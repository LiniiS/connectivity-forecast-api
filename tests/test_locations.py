from fastapi.testclient import TestClient


FORBIDDEN_FIELDS = {
    "src_addr",
    "from",
    "address_v4",
    "address_v6",
    "prefix_v4",
    "prefix_v6",
}


def test_locations_returns_valid_list(client: TestClient) -> None:
    response = client.get("/api/v1/locations")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 10
    assert len(payload["items"]) == payload["total"]

    first = payload["items"][0]
    assert "probeId" in first
    assert first["countryCode"] == "BR"
    assert -90 <= first["location"]["latitude"] <= 90
    assert -180 <= first["location"]["longitude"] <= 180
    serialized = str(payload)
    for field in FORBIDDEN_FIELDS:
        assert field not in serialized
