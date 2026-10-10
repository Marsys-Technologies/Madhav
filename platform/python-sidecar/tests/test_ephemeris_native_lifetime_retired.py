"""
tests/test_ephemeris_native_lifetime_retired.py — SS N-373 (PR-S2).

The sidecar route GET /brahmagyan/ephemeris/native_lifetime_meta returned a
HARD-CODED block of the native's birth data (name, birth date/time, place,
lat/lon) to any holder of the shared service credential, with no per-chart
entitlement. It was retired together with the registry capability
`ephemeris_cache_native_lifetime`. These tests pin its ABSENCE.

DB-free: a missing route answers 404 before any dependency or handler runs.
"""
from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

RETIRED_PATH = "/brahmagyan/ephemeris/native_lifetime_meta"


def test_retired_route_returns_404():
    response = client.get(RETIRED_PATH)
    assert response.status_code == 404


def test_retired_route_returns_404_with_credential_and_params():
    response = client.get(
        RETIRED_PATH,
        params={"start_date": "1984-01-01", "end_date": "2070-12-31", "count_only": "true"},
        headers={"x-api-key": "any-key"},
    )
    assert response.status_code == 404
    assert "Abhisek" not in response.text
    assert "Bhubaneswar" not in response.text


def test_no_registered_route_mentions_native_lifetime():
    paths = [getattr(route, "path", "") for route in app.routes]
    assert not [p for p in paths if "native_lifetime" in p or "native-lifetime" in p]
    assert RETIRED_PATH not in app.openapi()["paths"]


def test_sibling_ephemeris_routes_still_registered():
    paths = {getattr(route, "path", "") for route in app.routes}
    for sibling in ("planet_position", "planet_transit", "aspects", "retrograde_periods", "all_bodies_range"):
        assert f"/brahmagyan/ephemeris/{sibling}" in paths


def test_ephemeris_routes_module_holds_no_native_birth_data():
    import brahmagyan.ephemeris_routes as mod

    assert not hasattr(mod, "get_native_lifetime_meta")
    assert not hasattr(mod, "NATIVE_LIFETIME_START")
    source = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
    for needle in ("Abhisek", "Bhubaneswar", "1984-02-05", "10:43", "native-lifetime"):
        assert needle not in source, needle
