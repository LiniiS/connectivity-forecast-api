from fastapi.testclient import TestClient


def test_compare_returns_all_active_models(client: TestClient) -> None:
    response = client.get(
        "/api/v1/forecasts/probes/900001/compare",
        params={"prediction_for": "2026-08-20T19:00:00Z"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["probeId"] == 900001
    assert payload["predictionFor"] == "2026-08-20T19:00:00Z"
    ids = [item["modelId"] for item in payload["models"]]
    assert ids == ["model-a", "model-b", "model-c", "model-d"]
    rtts = [item["predictedAvgRttMs"] for item in payload["models"]]
    assert len(set(rtts)) == 4
    for item in payload["models"]:
        assert item["quality"] in {"GOOD", "MODERATE", "UNSTABLE"}


def test_compare_unknown_probe_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/forecasts/probes/1/compare")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROBE_NOT_FOUND"
