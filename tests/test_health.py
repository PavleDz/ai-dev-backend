from __future__ import annotations

from fastapi.testclient import TestClient


def test_live(client: TestClient) -> None:
    assert client.get("/live").json() == {"status": "ok"}


def test_unknown_route_has_the_error_shape(client: TestClient) -> None:
    response = client.get("/api/nothing")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found", "code": "http_error"}
