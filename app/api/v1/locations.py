from fastapi import APIRouter, Depends

from app.api.deps import get_location_service
from app.models.responses import LocationsResponse
from app.services.location_service import LocationService

router = APIRouter()


@router.get(
    "/locations",
    response_model=LocationsResponse,
    summary="List available probe locations",
    description=(
        "Returns probes that currently have prediction data. "
        "Coordinates come from RIPE Atlas probe geometry semantics "
        "(GeoJSON `[longitude, latitude]`), exposed here as named fields. "
        "Public probe coordinates are privacy-protected and must not be treated "
        "as the exact user location. Probe IP addresses are never returned."
    ),
)
def list_locations(
    location_service: LocationService = Depends(get_location_service),
) -> LocationsResponse:
    return location_service.list_locations()
