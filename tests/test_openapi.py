from fastapi.testclient import TestClient


def test_docs_are_available(client: TestClient) -> None:
    response = client.get("/docs")
    assert response.status_code == 200


def test_root_redirects_to_docs(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)
    assert response.status_code in {307, 302}
    assert response.headers["location"] == "/docs"


def test_openapi_documents_field_origins(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    serialized = str(spec)
    assert "SOURCE" in serialized
    assert "DERIVED" in serialized
    assert "PREDICTED" in serialized
    assert "BUSINESS" in serialized
    assert "/api/v1/health" in spec["paths"]
    assert "/api/v1/locations" in spec["paths"]
    assert "/api/v1/forecasts/nearby" in spec["paths"]
    assert "/api/v1/activity/check" in spec["paths"]
    assert "/api/v1/models" in spec["paths"]
    nearby_params = spec["paths"]["/api/v1/forecasts/nearby"]["get"]["parameters"]
    assert any(param.get("name") == "model_id" for param in nearby_params)
