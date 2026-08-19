from app.core.exceptions import NoProbeInRangeError
from app.core.geo import haversine_km
from app.models.prediction import ProbeLocation
from app.models.responses import GeoPoint, LocationItem, LocationsResponse
from app.repositories.prediction_repository import PredictionRepository


class LocationService:
    def __init__(self, repository: PredictionRepository) -> None:
        self._repository = repository

    def list_locations(self) -> LocationsResponse:
        probes = sorted(self._repository.list_probe_locations(), key=lambda item: item.probe_id)
        items = [
            LocationItem(
                probe_id=probe.probe_id,
                country_code=probe.country_code,
                asn_v4=probe.asn_v4,
                asn_v6=probe.asn_v6,
                location=GeoPoint(latitude=probe.latitude, longitude=probe.longitude),
            )
            for probe in probes
        ]
        return LocationsResponse(items=items, total=len(items))

    def find_nearest(
        self,
        latitude: float,
        longitude: float,
        radius_km: float | None = None,
        model_id: str | None = None,
    ) -> tuple[ProbeLocation, float]:
        probes = self._repository.list_probe_locations(model_id)
        if not probes:
            raise NoProbeInRangeError()

        nearest = min(
            probes,
            key=lambda probe: haversine_km(latitude, longitude, probe.latitude, probe.longitude),
        )
        distance = haversine_km(latitude, longitude, nearest.latitude, nearest.longitude)
        if radius_km is not None and distance > radius_km:
            raise NoProbeInRangeError()
        return nearest, round(distance, 1)
