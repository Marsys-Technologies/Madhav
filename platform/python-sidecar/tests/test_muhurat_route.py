from __future__ import annotations

import os
from datetime import date, datetime, time

from fastapi.testclient import TestClient

import main
from main import app
from panchang_engine.types import MuhuratWindow
from routers import muhurat as muhurat_router


def _headers() -> dict[str, str]:
    key = os.environ.get("PYTHON_SIDECAR_API_KEY", "")
    return {"x-api-key": key} if key else {}


def _request(**overrides):
    payload = {
        "event": "vivah",
        "date_from": "2027-01-01",
        "date_to": "2027-01-02",
        "lat": 20.27,
        "lon": 85.84,
        "tz_offset_minutes": 330,
        "chart_id": None,
        "top_n": 10,
    }
    payload.update(overrides)
    return payload


def _window() -> MuhuratWindow:
    return MuhuratWindow(
        event="vivah",
        start_utc=datetime(2027, 1, 1, 0, 30),
        end_utc=datetime(2027, 1, 1, 12, 30),
        star_rating=4,
        score=71.234,
        breakdown={
            "tithi": 0.19,
            "nakshatra": 0.38,
            "vara": 0.0475,
            "yoga": 0.0,
            "planet": 0.1,
        },
    )


def test_muhurat_route_is_mounted():
    assert "/api/compute/muhurat" in app.openapi()["paths"]


def test_muhurat_route_serializes_compact_numeric_breakdown(monkeypatch):
    window = _window()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(muhurat_router, "find_muhurat", lambda *args, **kwargs: [window])

    response = TestClient(app).post(
        "/api/compute/muhurat", json=_request(), headers=_headers()
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["windows"][0]["score"] == 71.23
    assert body["windows"][0]["breakdown"] == window.breakdown


def test_muhurat_route_preserves_requested_timezone(monkeypatch):
    window = _window()
    received = {}

    def fake_find(*args, **kwargs):
        received.update(kwargs)
        return [window]

    monkeypatch.setattr(muhurat_router, "find_muhurat", fake_find)

    response = TestClient(app).post(
        "/api/compute/muhurat",
        json=_request(tz_offset_minutes=0),
        headers=_headers(),
    )

    assert response.status_code == 200
    assert received["tz_offset_minutes"] == 0


def test_native_chart_uses_birth_instant_not_sunrise(monkeypatch):
    from panchang_engine import compute_panchang

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, *args):
            return self

        def fetchone(self):
            return (
                date(2027, 1, 1),
                time(23, 59),
                20.27,
                85.84,
                "Asia/Kolkata",
            )

    monkeypatch.setenv("DATABASE_URL", "postgresql://chart")
    monkeypatch.setattr(muhurat_router.psycopg, "connect", lambda *args: FakeConnection())

    native = muhurat_router._fetch_native_chart("chart-transition-day")

    assert compute_panchang(date(2027, 1, 1), 20.27, 85.84, 330).nakshatra.id == 14
    assert native.birth_nakshatra_id == 15


def test_muhurat_route_rejects_unsupported_event():
    response = TestClient(app).post(
        "/api/compute/muhurat",
        json=_request(event="unsupported"),
        headers=_headers(),
    )
    assert response.status_code == 422


def test_muhurat_route_rejects_more_than_90_inclusive_days():
    response = TestClient(app).post(
        "/api/compute/muhurat",
        json=_request(date_to="2027-04-02"),
        headers=_headers(),
    )
    assert response.status_code == 422


def test_muhurat_route_inherits_sidecar_api_key_guard(monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "route-secret")
    monkeypatch.setattr(
        muhurat_router,
        "find_muhurat",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("engine called")),
    )

    response = TestClient(app).post("/api/compute/muhurat", json=_request())

    assert response.status_code == 401
