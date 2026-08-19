from datetime import datetime, timezone

from pydantic import Field, field_validator

from app.config.activity_rules import ActivityType, RecommendationCode
from app.config.quality_rules import Quality
from app.models.common import APIModel, UtcDateTime

SOURCE = "SOURCE"
DERIVED = "DERIVED"
PREDICTED = "PREDICTED"
BUSINESS = "BUSINESS"


def annotated(kind: str, text: str) -> str:
    return f"{kind} — {text}"


class HealthResponse(APIModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["internet-quality-api"])


class ErrorBody(APIModel):
    code: str = Field(examples=["PROBE_NOT_FOUND"])
    message: str = Field(
        examples=["No prediction data was found for the requested probe."]
    )
    details: list[dict] | None = None


class ErrorResponse(APIModel):
    error: ErrorBody


class GeoPoint(APIModel):
    latitude: float = Field(
        description=annotated(
            SOURCE,
            "Latitude derived from RIPE Atlas probe.geometry.coordinates "
            "(GeoJSON order is [longitude, latitude]; this API exposes named fields). "
            "Public probe coordinates are privacy-protected and are not the exact user location.",
        ),
        examples=[-23.55],
    )
    longitude: float = Field(
        description=annotated(
            SOURCE,
            "Longitude derived from RIPE Atlas probe.geometry.coordinates "
            "(GeoJSON order is [longitude, latitude]).",
        ),
        examples=[-46.63],
    )


class LocationItem(APIModel):
    probe_id: int = Field(
        description=annotated(SOURCE, "RIPE Atlas probe id (prb_id / probe.id)."),
        examples=[900001],
    )
    country_code: str = Field(
        description=annotated(SOURCE, "RIPE Atlas probe.country_code."),
        examples=["BR"],
    )
    asn_v4: int | None = Field(
        default=None,
        description=annotated(SOURCE, "RIPE Atlas probe.asn_v4. May be null."),
        examples=[28573],
    )
    asn_v6: int | None = Field(
        default=None,
        description=annotated(SOURCE, "RIPE Atlas probe.asn_v6. May be null."),
        examples=[None],
    )
    location: GeoPoint


class LocationsResponse(APIModel):
    items: list[LocationItem]
    total: int = Field(examples=[10])


class ModelListItem(APIModel):
    id: str = Field(
        description=annotated(
            PREDICTED,
            "Unique identifier of the prediction model selected by the user. "
            "Not a RIPE Atlas field. The API does not execute this model.",
        ),
        examples=["model-a"],
    )
    name: str = Field(examples=["Modelo A"])
    description: str = Field(examples=["Modelo desenvolvido pelo Grupo 1."])
    group_name: str = Field(examples=["Grupo 1"])
    algorithm: str = Field(
        description=annotated(
            PREDICTED,
            "Informational metadata about the group's algorithm. The API never runs it.",
        ),
        examples=["Linear Regression"],
    )
    version: str = Field(
        description=annotated(PREDICTED, "Active model version label for this catalog entry."),
        examples=["1.0"],
    )


class ModelsResponse(APIModel):
    items: list[ModelListItem]
    total: int = Field(examples=[4])


class ModelDetail(ModelListItem):
    active: bool = Field(
        description="Whether this catalog entry can be used by forecast endpoints.",
        examples=[True],
    )


class ModelRef(APIModel):
    id: str = Field(
        description="Unique identifier of the prediction model selected by the user.",
        examples=["model-a"],
    )
    name: str = Field(examples=["Modelo A"])
    version: str = Field(examples=["1.0"])


class LocationWithCountry(GeoPoint):
    country_code: str = Field(
        description=annotated(SOURCE, "RIPE Atlas probe.country_code."),
        examples=["BR"],
    )


class PredictionDetail(APIModel):
    prediction_for: UtcDateTime = Field(
        description=annotated(PREDICTED, "UTC instant the forecast refers to."),
        examples=["2026-08-20T19:00:00Z"],
    )
    predicted_avg_rtt_ms: float = Field(
        description=annotated(
            PREDICTED,
            "Forecast of future average RTT in milliseconds. Historical RIPE Atlas "
            "observation field is ping `avg`. Not a RIPE Atlas field.",
        ),
        examples=[71.4],
    )
    predicted_packet_loss_pct: float = Field(
        description=annotated(
            PREDICTED,
            "Forecast of future packet loss in percent. Historical value is DERIVED "
            "from RIPE Atlas ping `sent` and `rcvd` as ((sent - rcvd) / sent) * 100 "
            "when sent > 0. There is no original RIPE field named packet_loss.",
        ),
        examples=[1.5],
    )
    model_confidence: float | None = Field(
        default=None,
        description=annotated(
            PREDICTED,
            "Optional model-produced confidence in [0, 1]. Not a RIPE Atlas field. "
            "May be null when the model does not provide confidence.",
        ),
        examples=[0.82],
    )


class PredictionSummary(APIModel):
    prediction_for: UtcDateTime = Field(
        description=annotated(PREDICTED, "UTC instant the forecast refers to."),
        examples=["2026-08-20T19:00:00Z"],
    )
    predicted_avg_rtt_ms: float = Field(
        description=annotated(
            PREDICTED,
            "Forecast of future average RTT in milliseconds. Historical RIPE field: avg.",
        ),
        examples=[71.4],
    )
    predicted_packet_loss_pct: float = Field(
        description=annotated(
            PREDICTED,
            "Forecast of future packet loss percent. Historical value is derived from sent/rcvd.",
        ),
        examples=[1.5],
    )


class TimelineItem(APIModel):
    prediction_for: UtcDateTime
    predicted_avg_rtt_ms: float
    predicted_packet_loss_pct: float
    quality: Quality = Field(
        description=annotated(
            BUSINESS,
            "Experimental backend category (GOOD, MODERATE, UNSTABLE). "
            "Not produced by the model and not provided by RIPE Atlas.",
        ),
        examples=["MODERATE"],
    )
    quality_score: int = Field(
        description=annotated(
            BUSINESS,
            "Experimental backend score from 0 to 100. Not a RIPE Atlas field.",
        ),
        ge=0,
        le=100,
        examples=[68],
    )


class Assessment(APIModel):
    quality: Quality = Field(
        description=annotated(
            BUSINESS,
            "Experimental backend category. Not a RIPE Atlas classification.",
        ),
        examples=["MODERATE"],
    )
    quality_score: int = Field(
        description=annotated(BUSINESS, "Experimental backend score from 0 to 100."),
        ge=0,
        le=100,
        examples=[68],
    )


class Recommendation(APIModel):
    code: RecommendationCode = Field(
        description=annotated(
            BUSINESS,
            "Stable recommendation code for the mobile app. Prefer this over the message text. "
            "Not produced by the model and not provided by RIPE Atlas.",
        ),
        examples=["REDUCE_NETWORK_USAGE"],
    )
    message: str = Field(
        description=annotated(BUSINESS, "Human-readable hint. Do not key app logic on this text."),
        examples=["A conexão pode apresentar alguma instabilidade neste período."],
    )


class ProbeForecastResponse(APIModel):
    model: ModelRef
    probe_id: int = Field(
        description=annotated(SOURCE, "RIPE Atlas probe id (prb_id / probe.id)."),
        examples=[900001],
    )
    location: LocationWithCountry
    prediction: PredictionDetail
    assessment: Assessment
    recommendation: Recommendation


class TimelineResponse(APIModel):
    model: ModelRef
    probe_id: int
    items: list[TimelineItem]


class RequestedLocation(APIModel):
    latitude: float = Field(examples=[-23.551])
    longitude: float = Field(examples=[-46.634])


class MatchedProbe(APIModel):
    probe_id: int = Field(
        description=annotated(SOURCE, "RIPE Atlas probe id selected as geographic reference."),
        examples=[900001],
    )
    distance_km: float = Field(
        description=annotated(
            BUSINESS,
            "Great-circle distance in kilometers between the requested point and the probe coordinates.",
        ),
        examples=[2.7],
    )


class NearbyMetadata(APIModel):
    disclaimer: str = Field(
        description=annotated(
            BUSINESS,
            "Mandatory interpretation note: the forecast is bound to a RIPE Atlas probe, "
            "not to a measurement of the user device.",
        ),
        examples=[
            "A previsão está associada à probe RIPE Atlas selecionada como referência "
            "geográfica e não representa uma medição direta do dispositivo do usuário."
        ],
    )
    location_privacy: str = Field(
        description=annotated(
            BUSINESS,
            "RIPE Atlas applies privacy protection to public probe coordinates.",
        ),
        examples=[
            "As coordenadas públicas das probes recebem proteção de privacidade do RIPE Atlas "
            "e não devem ser tratadas como a localização exata do usuário."
        ],
    )


class NearbyForecastResponse(APIModel):
    model: ModelRef
    requested_location: RequestedLocation
    matched_probe: MatchedProbe
    prediction: PredictionSummary
    assessment: Assessment
    recommendation: Recommendation
    metadata: NearbyMetadata


class ActivityForecast(APIModel):
    quality: Quality = Field(
        description=annotated(BUSINESS, "Experimental backend quality category."),
        examples=["UNSTABLE"],
    )
    predicted_avg_rtt_ms: float = Field(
        description=annotated(PREDICTED, "Forecast of future average RTT (historical RIPE field: avg)."),
        examples=[185.2],
    )
    predicted_packet_loss_pct: float = Field(
        description=annotated(
            PREDICTED,
            "Forecast of future packet loss percent (historical value derived from sent/rcvd).",
        ),
        examples=[8.1],
    )


class ActivityCheckRequest(APIModel):
    model_id: str = Field(
        min_length=1,
        description="Unique identifier of the prediction model selected by the user.",
        examples=["model-a"],
        alias="modelId",
    )
    latitude: float = Field(
        ge=-90,
        le=90,
        description="User latitude in decimal degrees. Not a RIPE Atlas field.",
        examples=[-23.55],
    )
    longitude: float = Field(
        ge=-180,
        le=180,
        description="User longitude in decimal degrees. Not a RIPE Atlas field.",
        examples=[-46.63],
    )
    date_time: datetime = Field(
        description="UTC instant to evaluate, ISO-8601.",
        examples=["2026-08-20T19:00:00Z"],
        alias="dateTime",
    )
    activity: ActivityType = Field(examples=["VIDEO_CALL"])

    @field_validator("date_time")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class ActivityCheckResponse(APIModel):
    model: ModelRef
    activity: ActivityType
    suitable: bool = Field(
        description=annotated(
            BUSINESS,
            "Whether the experimental activity rules consider the forecast suitable. "
            "Not a universal network requirement.",
        ),
        examples=[False],
    )
    forecast: ActivityForecast
    recommendation: Recommendation
    metadata: NearbyMetadata


class CompareModelItem(APIModel):
    model_id: str = Field(examples=["model-a"])
    model_name: str = Field(examples=["Modelo A"])
    predicted_avg_rtt_ms: float = Field(
        description=annotated(PREDICTED, "Forecast of future average RTT for this model."),
        examples=[71.4],
    )
    predicted_packet_loss_pct: float = Field(
        description=annotated(PREDICTED, "Forecast of future packet loss percent for this model."),
        examples=[1.5],
    )
    quality: Quality = Field(
        description=annotated(
            BUSINESS,
            "Same QualityClassifier applied to every model. Differences come from predictions, not from per-model rules.",
        ),
        examples=["MODERATE"],
    )


class CompareResponse(APIModel):
    probe_id: int = Field(examples=[900001])
    prediction_for: UtcDateTime = Field(examples=["2026-08-20T19:00:00Z"])
    models: list[CompareModelItem]
