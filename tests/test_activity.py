from fastapi.testclient import TestClient


def test_activity_check_with_valid_payload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/activity/check",
        json={
            "modelId": "model-a",
            "latitude": -3.119,
            "longitude": -60.0217,
            "dateTime": "2026-08-20T19:00:00Z",
            "activity": "VIDEO_CALL",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"]["id"] == "model-a"
    assert payload["activity"] == "VIDEO_CALL"
    assert payload["suitable"] is False
    assert payload["forecast"]["quality"] == "UNSTABLE"
    assert payload["recommendation"]["code"] == "PREPARE_OFFLINE"


def test_activity_check_messaging_can_be_suitable(client: TestClient) -> None:
    response = client.post(
        "/api/v1/activity/check",
        json={
            "modelId": "model-a",
            "latitude": -23.55,
            "longitude": -46.63,
            "dateTime": "2026-08-20T03:00:00Z",
            "activity": "MESSAGING",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["suitable"] is True
    assert payload["forecast"]["quality"] == "GOOD"


def test_activity_check_without_model_id_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/activity/check",
        json={
            "latitude": -23.55,
            "longitude": -46.63,
            "dateTime": "2026-08-20T19:00:00Z",
            "activity": "VIDEO_CALL",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
