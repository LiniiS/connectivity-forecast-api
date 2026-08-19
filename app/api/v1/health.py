from fastapi import APIRouter

from app.config.settings import settings
from app.models.responses import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Confirms that the API process is running. Does not query RIPE Atlas.",
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.service_name)
