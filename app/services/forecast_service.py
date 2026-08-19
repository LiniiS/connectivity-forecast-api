from datetime import datetime

from app.core.exceptions import (
    InvalidTimeRangeError,
    NoCommonPredictionError,
    ProbeNotFoundError,
)
from app.core.time import ensure_utc, utc_now
from app.models.prediction import PredictionRecord
from app.models.prediction_model import PredictionModel
from app.models.responses import (
    Assessment,
    CompareModelItem,
    CompareResponse,
    LocationWithCountry,
    NearbyForecastResponse,
    NearbyMetadata,
    MatchedProbe,
    ModelRef,
    PredictionDetail,
    PredictionSummary,
    ProbeForecastResponse,
    RequestedLocation,
    TimelineItem,
    TimelineResponse,
)
from app.repositories.prediction_repository import PredictionRepository
from app.services.location_service import LocationService
from app.services.model_service import ModelService
from app.services.quality_classifier import QualityClassifier
from app.services.recommendation_service import RecommendationService

NEARBY_DISCLAIMER = (
    "A previsão está associada à probe RIPE Atlas selecionada como referência "
    "geográfica e não representa uma medição direta do dispositivo do usuário."
)
LOCATION_PRIVACY = (
    "As coordenadas públicas das probes recebem proteção de privacidade do RIPE Atlas "
    "e não devem ser tratadas como a localização exata do usuário."
)


class ForecastService:
    def __init__(
        self,
        repository: PredictionRepository,
        location_service: LocationService,
        model_service: ModelService,
        classifier: QualityClassifier,
        recommendations: RecommendationService,
    ) -> None:
        self._repository = repository
        self._location_service = location_service
        self._model_service = model_service
        self._classifier = classifier
        self._recommendations = recommendations

    def get_probe_forecast(self, probe_id: int, model_id: str) -> ProbeForecastResponse:
        model = self._model_service.require_active(model_id)
        record = self._select_current(self._require_probe_records(model.id, probe_id))
        location = self._repository.get_probe_location(probe_id)
        assert location is not None
        assessment = self._assess(record)
        return ProbeForecastResponse(
            model=_model_ref(model),
            probe_id=probe_id,
            location=LocationWithCountry(
                latitude=location.latitude,
                longitude=location.longitude,
                country_code=location.country_code,
            ),
            prediction=PredictionDetail(
                prediction_for=record.prediction_for,
                predicted_avg_rtt_ms=record.predicted_avg_rtt_ms,
                predicted_packet_loss_pct=record.predicted_packet_loss_pct,
                model_confidence=record.model_confidence,
            ),
            assessment=Assessment(
                quality=assessment.quality,
                quality_score=assessment.quality_score,
            ),
            recommendation=self._recommendations.for_quality(assessment.quality),
        )

    def get_timeline(
        self,
        probe_id: int,
        model_id: str,
        from_time: datetime | None,
        to_time: datetime | None,
        limit: int,
    ) -> TimelineResponse:
        model = self._model_service.require_active(model_id)
        if from_time is not None and to_time is not None:
            if ensure_utc(from_time) > ensure_utc(to_time):
                raise InvalidTimeRangeError()

        records = self._require_probe_records(model.id, probe_id)
        if from_time is not None:
            start = ensure_utc(from_time)
            records = [item for item in records if item.prediction_for >= start]
        if to_time is not None:
            end = ensure_utc(to_time)
            records = [item for item in records if item.prediction_for <= end]

        records = records[:limit]
        items = []
        for record in records:
            assessment = self._assess(record)
            items.append(
                TimelineItem(
                    prediction_for=record.prediction_for,
                    predicted_avg_rtt_ms=record.predicted_avg_rtt_ms,
                    predicted_packet_loss_pct=record.predicted_packet_loss_pct,
                    quality=assessment.quality,
                    quality_score=assessment.quality_score,
                )
            )
        return TimelineResponse(model=_model_ref(model), probe_id=probe_id, items=items)

    def get_nearby_forecast(
        self,
        latitude: float,
        longitude: float,
        model_id: str,
        radius_km: float | None,
    ) -> NearbyForecastResponse:
        model = self._model_service.require_active(model_id)
        probe, distance_km = self._location_service.find_nearest(
            latitude,
            longitude,
            radius_km,
            model_id=model.id,
        )
        record = self._select_current(self._require_probe_records(model.id, probe.probe_id))
        assessment = self._assess(record)
        return NearbyForecastResponse(
            model=_model_ref(model),
            requested_location=RequestedLocation(latitude=latitude, longitude=longitude),
            matched_probe=MatchedProbe(probe_id=probe.probe_id, distance_km=distance_km),
            prediction=PredictionSummary(
                prediction_for=record.prediction_for,
                predicted_avg_rtt_ms=record.predicted_avg_rtt_ms,
                predicted_packet_loss_pct=record.predicted_packet_loss_pct,
            ),
            assessment=Assessment(
                quality=assessment.quality,
                quality_score=assessment.quality_score,
            ),
            recommendation=self._recommendations.for_quality(assessment.quality),
            metadata=self.reference_metadata(),
        )

    def compare(self, probe_id: int, prediction_for: datetime | None) -> CompareResponse:
        active_models = self._model_service.list_active_models()
        timelines: dict[str, list[PredictionRecord]] = {}
        for model in active_models:
            records = self._repository.get_timeline(model.id, probe_id)
            if records:
                timelines[model.id] = records
        if not timelines:
            raise ProbeNotFoundError(probe_id)

        common = set.intersection(
            *[{record.prediction_for for record in records} for records in timelines.values()]
        )
        if not common:
            raise NoCommonPredictionError()

        if prediction_for is not None:
            target = ensure_utc(prediction_for)
            if target not in common:
                raise NoCommonPredictionError()
            chosen = target
        else:
            chosen = self._select_current_time(common)

        catalog = {model.id: model for model in active_models}
        items: list[CompareModelItem] = []
        for model_id, records in timelines.items():
            record = next(item for item in records if item.prediction_for == chosen)
            assessment = self._assess(record)
            model = catalog[model_id]
            items.append(
                CompareModelItem(
                    model_id=model.id,
                    model_name=model.name,
                    predicted_avg_rtt_ms=record.predicted_avg_rtt_ms,
                    predicted_packet_loss_pct=record.predicted_packet_loss_pct,
                    quality=assessment.quality,
                )
            )
        items.sort(key=lambda item: item.model_name.lower())
        return CompareResponse(probe_id=probe_id, prediction_for=chosen, models=items)

    def select_closest_record(
        self,
        model_id: str,
        probe_id: int,
        target: datetime,
    ) -> PredictionRecord:
        records = self._require_probe_records(model_id, probe_id)
        moment = ensure_utc(target)
        return min(
            records,
            key=lambda item: abs((item.prediction_for - moment).total_seconds()),
        )

    def require_active_model(self, model_id: str) -> PredictionModel:
        return self._model_service.require_active(model_id)

    @staticmethod
    def reference_metadata() -> NearbyMetadata:
        return NearbyMetadata(disclaimer=NEARBY_DISCLAIMER, location_privacy=LOCATION_PRIVACY)

    def _assess(self, record: PredictionRecord):
        return self._classifier.classify(
            record.predicted_avg_rtt_ms,
            record.predicted_packet_loss_pct,
        )

    def _require_probe_records(self, model_id: str, probe_id: int) -> list[PredictionRecord]:
        records = self._repository.get_timeline(model_id, probe_id)
        if not records:
            raise ProbeNotFoundError(probe_id)
        return records

    @staticmethod
    def _select_current(records: list[PredictionRecord]) -> PredictionRecord:
        now = utc_now()
        future = [item for item in records if item.prediction_for >= now]
        if future:
            return min(future, key=lambda item: item.prediction_for)
        return max(records, key=lambda item: item.prediction_for)

    @staticmethod
    def _select_current_time(times: set[datetime]) -> datetime:
        now = utc_now()
        future = [item for item in times if item >= now]
        if future:
            return min(future)
        return max(times)


def _model_ref(model: PredictionModel) -> ModelRef:
    return ModelRef(id=model.id, name=model.name, version=model.version)
