"""HTTP smoke: health/ready + correlation header."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_ready_when_db_up(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.presentation.http.routers.ready.check_database",
        lambda: True,
    )
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_when_db_down(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.presentation.http.routers.ready.check_database",
        lambda: False,
    )
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_health_ok_even_if_db_down(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.presentation.http.routers.ready.check_database",
        lambda: False,
    )
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_correlation_id_echo_and_generate() -> None:
    custom = "client-corr-abc"
    response = client.get("/health", headers={"X-Request-ID": custom})
    assert response.headers["X-Request-ID"] == custom

    generated = client.get("/health")
    assert generated.headers["X-Request-ID"]
    assert generated.headers["X-Request-ID"] != custom
