from fastapi.testclient import TestClient


def test_existing_probe_forecast_returns_200(client: TestClient) -> None:
    response = client.get("/api/v1/forecasts/probes/900001", params={"model_id": "model-a"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["probeId"] == 900001
    assert payload["model"]["id"] == "model-a"
    assert "prediction" in payload
    assert "predictedAvgRttMs" in payload["prediction"]
    assert "predictedPacketLossPct" in payload["prediction"]
    assert payload["assessment"]["quality"] in {"GOOD", "MODERATE", "UNSTABLE"}
    assert 0 <= payload["assessment"]["qualityScore"] <= 100
    assert payload["recommendation"]["code"] in {
        "NORMAL_USE",
        "REDUCE_NETWORK_USAGE",
        "PREPARE_OFFLINE",
    }


def test_missing_probe_forecast_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/forecasts/probes/1", params={"model_id": "model-a"})
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "PROBE_NOT_FOUND"
    assert "traceback" not in str(payload).lower()
    assert "stack" not in str(payload).lower()


def test_forecast_model_a_is_isolated_from_model_b(client: TestClient) -> None:
    response_a = client.get("/api/v1/forecasts/probes/900001", params={"model_id": "model-a"})
    response_b = client.get("/api/v1/forecasts/probes/900001", params={"model_id": "model-b"})
    assert response_a.status_code == 200
    assert response_b.status_code == 200
    payload_a = response_a.json()
    payload_b = response_b.json()
    assert payload_a["model"]["id"] == "model-a"
    assert payload_b["model"]["id"] == "model-b"
    assert payload_a["prediction"]["predictionFor"] == payload_b["prediction"]["predictionFor"]
    assert payload_a["prediction"]["predictedAvgRttMs"] != payload_b["prediction"]["predictedAvgRttMs"]


def test_forecast_without_model_id_returns_422(client: TestClient) -> None:
    response = client.get("/api/v1/forecasts/probes/900001")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_forecast_unknown_model_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/forecasts/probes/900001", params={"model_id": "model-z"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODEL_NOT_FOUND"


def test_forecast_inactive_model_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/forecasts/probes/900001", params={"model_id": "model-inactive"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODEL_INACTIVE"
