from datetime import datetime

from fastapi.testclient import TestClient


def test_timeline_is_sorted_by_prediction_for(client: TestClient) -> None:
    response = client.get(
        "/api/v1/forecasts/probes/900001/timeline",
        params={"model_id": "model-a"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"]["id"] == "model-a"
    items = payload["items"]
    assert len(items) >= 2
    timestamps = [datetime.fromisoformat(item["predictionFor"].replace("Z", "+00:00")) for item in items]
    assert timestamps == sorted(timestamps)


def test_timeline_respects_limit(client: TestClient) -> None:
    response = client.get(
        "/api/v1/forecasts/probes/900001/timeline",
        params={"model_id": "model-a", "limit": 3},
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3


def test_timeline_rejects_inverted_range(client: TestClient) -> None:
    response = client.get(
        "/api/v1/forecasts/probes/900001/timeline",
        params={
            "model_id": "model-a",
            "from": "2026-08-20T20:00:00Z",
            "to": "2026-08-20T10:00:00Z",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_TIME_RANGE"


def test_timeline_differs_between_models(client: TestClient) -> None:
    response_a = client.get(
        "/api/v1/forecasts/probes/900001/timeline",
        params={"model_id": "model-a", "limit": 5},
    )
    response_c = client.get(
        "/api/v1/forecasts/probes/900001/timeline",
        params={"model_id": "model-c", "limit": 5},
    )
    assert response_a.status_code == 200
    assert response_c.status_code == 200
    items_a = response_a.json()["items"]
    items_c = response_c.json()["items"]
    assert [item["predictionFor"] for item in items_a] == [item["predictionFor"] for item in items_c]
    assert [item["predictedAvgRttMs"] for item in items_a] != [
        item["predictedAvgRttMs"] for item in items_c
    ]
