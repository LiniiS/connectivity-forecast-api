from app.models.responses import (
    ActivityCheckRequest,
    ActivityCheckResponse,
    ActivityForecast,
    ModelRef,
)
from app.services.forecast_service import ForecastService
from app.services.location_service import LocationService
from app.services.quality_classifier import QualityClassifier
from app.services.recommendation_service import RecommendationService


class ActivityService:
    def __init__(
        self,
        location_service: LocationService,
        forecast_service: ForecastService,
        classifier: QualityClassifier,
        recommendations: RecommendationService,
    ) -> None:
        self._location_service = location_service
        self._forecast_service = forecast_service
        self._classifier = classifier
        self._recommendations = recommendations

    def check(self, payload: ActivityCheckRequest) -> ActivityCheckResponse:
        model = self._forecast_service.require_active_model(payload.model_id)
        probe, _distance = self._location_service.find_nearest(
            payload.latitude,
            payload.longitude,
            model_id=model.id,
        )
        record = self._forecast_service.select_closest_record(
            model.id,
            probe.probe_id,
            payload.date_time,
        )
        assessment = self._classifier.classify(
            record.predicted_avg_rtt_ms,
            record.predicted_packet_loss_pct,
        )
        suitable, recommendation = self._recommendations.for_activity(
            payload.activity,
            assessment.quality,
        )
        return ActivityCheckResponse(
            model=ModelRef(id=model.id, name=model.name, version=model.version),
            activity=payload.activity,
            suitable=suitable,
            forecast=ActivityForecast(
                quality=assessment.quality,
                predicted_avg_rtt_ms=record.predicted_avg_rtt_ms,
                predicted_packet_loss_pct=record.predicted_packet_loss_pct,
            ),
            recommendation=recommendation,
            metadata=self._forecast_service.reference_metadata(),
        )
