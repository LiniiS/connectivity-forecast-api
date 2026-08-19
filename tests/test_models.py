from fastapi.testclient import TestClient


def test_list_models_returns_only_active(client: TestClient) -> None:
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    payload = response.json()
    ids = [item["id"] for item in payload["items"]]
    assert payload["total"] == len(ids)
    assert "model-a" in ids
    assert "model-b" in ids
    assert "model-c" in ids
    assert "model-d" in ids
    assert "model-inactive" not in ids
    names = [item["name"] for item in payload["items"]]
    assert names == sorted(names, key=str.lower)


def test_get_existing_model_returns_200(client: TestClient) -> None:
    response = client.get("/api/v1/models/model-a")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "model-a"
    assert payload["groupName"] == "Grupo 1"
    assert payload["algorithm"] == "Linear Regression"
    assert payload["active"] is True


def test_get_unknown_model_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/models/model-z")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "MODEL_NOT_FOUND"
