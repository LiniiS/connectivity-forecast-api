from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import get_forecast_service
from app.config.settings import settings
from app.models.responses import (
    CompareResponse,
    NearbyForecastResponse,
    ProbeForecastResponse,
    TimelineResponse,
)
from app.services.forecast_service import ForecastService

router = APIRouter()

ModelIdQuery = Annotated[
    str,
    Query(
        min_length=1,
        description="Unique identifier of the prediction model selected by the user.",
        examples=["model-a", "model-b"],
    ),
]
ProbeIdPath = Annotated[
    int,
    Path(ge=1, description="Probe identifier (RIPE Atlas prb_id / probe.id)."),
]


@router.get(
    "/forecasts/probes/{probe_id}",
    response_model=ProbeForecastResponse,
    summary="Nearest forecast for a probe and model",
    description=(
        "Returns the nearest upcoming prediction for the given probe **and** `model_id`. "
        "Predictions from other models are never mixed. "
        "If every stored prediction is in the past, the latest available row is returned. "
        "`quality` and `recommendation` come from the shared backend classifiers, "
        "not from the selected algorithm."
    ),
    responses={
        404: {
            "description": "Unknown/inactive model or no prediction data for this probe.",
        }
    },
)
def get_probe_forecast(
    probe_id: ProbeIdPath,
    model_id: ModelIdQuery,
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> ProbeForecastResponse:
    return forecast_service.get_probe_forecast(probe_id, model_id)


@router.get(
    "/forecasts/probes/{probe_id}/timeline",
    response_model=TimelineResponse,
    summary="Forecast timeline for a probe and model",
    description=(
        "Returns predictions for one probe and one `model_id`, ordered by `predictionFor`. "
        "Optional `from` and `to` are inclusive UTC instants. `limit` is capped."
    ),
    responses={
        400: {"description": "from is later than to."},
        404: {"description": "Unknown/inactive model or no prediction data for this probe."},
    },
)
def get_probe_timeline(
    probe_id: ProbeIdPath,
    model_id: ModelIdQuery,
    from_time: datetime | None = Query(
        default=None,
        alias="from",
        description="Inclusive UTC start instant (ISO-8601).",
    ),
    to_time: datetime | None = Query(
        default=None,
        alias="to",
        description="Inclusive UTC end instant (ISO-8601).",
    ),
    limit: int = Query(
        default=settings.timeline_default_limit,
        ge=1,
        le=settings.timeline_max_limit,
        description="Maximum number of timeline items to return.",
    ),
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> TimelineResponse:
    return forecast_service.get_timeline(probe_id, model_id, from_time, to_time, limit)


@router.get(
    "/forecasts/probes/{probe_id}/compare",
    response_model=CompareResponse,
    summary="Compare active models for a probe",
    description=(
        "Returns the same instant across all active models that have data for this probe. "
        "If `prediction_for` is omitted, the nearest upcoming common instant is used. "
        "This endpoint does **not** rank models or declare a winner. "
        "Quality labels use the same QualityClassifier for every model."
    ),
    responses={
        404: {"description": "Probe without data or no shared prediction instant."},
    },
)
def compare_probe_forecasts(
    probe_id: ProbeIdPath,
    prediction_for: datetime | None = Query(
        default=None,
        description="UTC instant to compare. Must exist for every active model included.",
        examples=["2026-08-20T19:00:00Z"],
    ),
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> CompareResponse:
    return forecast_service.compare(probe_id, prediction_for)


@router.get(
    "/forecasts/nearby",
    response_model=NearbyForecastResponse,
    summary="Forecast for the nearest available probe of a model",
    description=(
        "Validates `model_id`, selects the geographically nearest probe that has "
        "predictions for that model (Haversine), and returns its nearest upcoming forecast. "
        "This is a geographic reference to a RIPE Atlas probe, not a measurement "
        "of the user device."
    ),
    responses={
        404: {"description": "Unknown/inactive model or no probe inside the optional radius."},
        422: {"description": "Invalid latitude, longitude, or missing model_id."},
    },
)
def get_nearby_forecast(
    lat: Annotated[float, Query(ge=-90, le=90, description="Requested latitude in decimal degrees.")],
    lon: Annotated[float, Query(ge=-180, le=180, description="Requested longitude in decimal degrees.")],
    model_id: ModelIdQuery,
    radius_km: Annotated[
        float | None,
        Query(
            gt=0,
            description="Optional maximum distance in kilometers. If omitted, the globally nearest probe is used.",
        ),
    ] = None,
    forecast_service: ForecastService = Depends(get_forecast_service),
) -> NearbyForecastResponse:
    return forecast_service.get_nearby_forecast(lat, lon, model_id, radius_km)
