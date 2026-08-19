from fastapi.testclient import TestClient


def test_nearby_with_valid_coordinates_returns_200(client: TestClient) -> None:
    response = client.get(
        "/api/v1/forecasts/nearby",
        params={"lat": -23.551, "lon": -46.634, "model_id": "model-b"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"]["id"] == "model-b"
    assert payload["matchedProbe"]["probeId"] == 900001
    assert payload["matchedProbe"]["distanceKm"] >= 0
    assert "disclaimer" in payload["metadata"]
    assert "não representa uma medição direta" in payload["metadata"]["disclaimer"]


def test_invalid_latitude_returns_422(client: TestClient) -> None:
    response = client.get(
        "/api/v1/forecasts/nearby",
        params={"lat": 100, "lon": -46.63, "model_id": "model-a"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_invalid_longitude_returns_422(client: TestClient) -> None:
    response = client.get(
        "/api/v1/forecasts/nearby",
        params={"lat": -23.55, "lon": 200, "model_id": "model-a"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_nearby_outside_small_radius_returns_404(client: TestClient) -> None:
    response = client.get(
        "/api/v1/forecasts/nearby",
        params={"lat": 0.0, "lon": 0.0, "radius_km": 1, "model_id": "model-a"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NO_PROBE_IN_RANGE"


def test_nearby_without_model_id_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/forecasts/nearby", params={"lat": -23.55, "lon": -46.63})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
