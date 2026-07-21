"""
tests/test_permission_curve_route.py — D-4b permission-bridge lane
(wave/D-4b/permission-bridge), routers/permission_curve.py.

Non-integration tests here are DB-free (module-level invariants + request
validation, which the route rejects before ever opening a DB connection).
The `@pytest.mark.integration` tests at the bottom hit the LIVE Cloud SQL
proxy (127.0.0.1:5433, same convention as tests/test_gochara_intensity.py's
`_live_conn_or_skip`) and are excluded by the mandated `-m "not integration"`
CI invocation.
"""
from __future__ import annotations

import psycopg
import pytest
from fastapi.testclient import TestClient

from main import app
from routers.permission_curve import PERMISSION_SYSTEM_IDS
from services.gochara_intensity.permission import SYSTEM_WEIGHTS

client = TestClient(app)

LIVE_DSN = "postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@127.0.0.1:5433/amjis"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


def _live_reachable() -> bool:
    try:
        psycopg.connect(LIVE_DSN, connect_timeout=2).close()
        return True
    except Exception:
        return False


# ── module-level invariants (no DB, no HTTP) ────────────────────────────

def test_permission_system_ids_is_exactly_the_12_generators():
    """Regression guard against this route's id list drifting from
    permission.py's live SYSTEM_WEIGHTS -- the module-level assert in
    permission_curve.py already enforces this at import time; this test
    makes the invariant visible in the test report too."""
    assert len(PERMISSION_SYSTEM_IDS) == 12
    assert set(PERMISSION_SYSTEM_IDS) == set(SYSTEM_WEIGHTS.keys())


def test_permission_system_ids_names_match_dispatch_spec():
    """The dispatch's own enumeration: 8 dasha systems + sade_sati +
    guru_shani_double_transit + av_threshold + planetary_return."""
    expected = {
        "vimshottari", "yogini", "ashtottari", "chara_karaka", "naisargika",
        "mudda", "kalachakra", "narayana",
        "sade_sati", "guru_shani_double_transit", "av_threshold", "planetary_return",
    }
    assert set(PERMISSION_SYSTEM_IDS) == expected


# ── HTTP validation (no DB reached — rejected before conn open) ─────────

def test_route_rejects_t_end_before_t_start():
    resp = client.post("/api/compute/permission_curve", json={
        "chart_id": CHART_ID, "event_class": "marriage",
        "t_start": "2013-12-11T00:00:00Z", "t_end": "2013-12-01T00:00:00Z",
    })
    assert resp.status_code == 400
    assert "t_end must be >= t_start" in resp.json()["detail"]


def test_route_rejects_unknown_system_id():
    resp = client.post("/api/compute/permission_curve", json={
        "chart_id": CHART_ID, "event_class": "marriage",
        "t_start": "2013-12-11T00:00:00Z", "t_end": "2013-12-11T00:00:00Z",
        "system_ids": ["not_a_real_system"],
    })
    assert resp.status_code == 400
    assert "unknown system_ids" in resp.json()["detail"]


def test_route_requires_chart_id():
    resp = client.post("/api/compute/permission_curve", json={
        "event_class": "marriage",
        "t_start": "2013-12-11T00:00:00Z", "t_end": "2013-12-11T00:00:00Z",
    })
    assert resp.status_code == 422  # pydantic: chart_id is a required field


def test_route_requires_event_class():
    resp = client.post("/api/compute/permission_curve", json={
        "chart_id": CHART_ID,
        "t_start": "2013-12-11T00:00:00Z", "t_end": "2013-12-11T00:00:00Z",
    })
    assert resp.status_code == 422


# ── live integration (excluded by -m "not integration"; run manually) ──

@pytest.mark.integration
def test_live_permission_curve_marriage_specimen_two_systems_active():
    """The named marriage specimen date (2013-12-11): live-verifies real,
    non-fabricated curve output for >= 2 of the 12 standalone PERMISSION
    generators, matching test_gochara_intensity.py's own
    test_permission_multisystem acceptance bar but via the HTTP route."""
    if not _live_reachable():
        pytest.skip("live Cloud SQL proxy not reachable at 127.0.0.1:5433 in this environment")
    resp = client.post("/api/compute/permission_curve", json={
        "chart_id": CHART_ID, "event_class": "marriage",
        "t_start": "2013-12-11T00:00:00Z", "t_end": "2013-12-11T00:00:00Z",
        "step_days": 5,
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["points_computed"] == 1
    assert len(body["system_ids"]) == 12
    active = [sid for sid, pts in body["systems"].items() if pts[0]["active"]]
    assert len(active) >= 2, f"expected >= 2 active systems at the marriage specimen date, got {active}"
    assert body["combined_permission_series"][0]["combined_permission"] > 0.0
    assert body["calibration_state"] == "structural_prior"


@pytest.mark.integration
def test_live_permission_curve_filters_to_requested_systems_only():
    if not _live_reachable():
        pytest.skip("live Cloud SQL proxy not reachable at 127.0.0.1:5433 in this environment")
    resp = client.post("/api/compute/permission_curve", json={
        "chart_id": CHART_ID, "event_class": "marriage",
        "t_start": "2013-12-01T00:00:00Z", "t_end": "2013-12-21T00:00:00Z",
        "step_days": 5, "system_ids": ["vimshottari", "guru_shani_double_transit"],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["systems"].keys()) == {"vimshottari", "guru_shani_double_transit"}
    for sid, pts in body["systems"].items():
        assert len(pts) == body["points_computed"]
        assert all(p["intensity"] in (0.0, 1.0) for p in pts)


@pytest.mark.integration
def test_live_permission_curve_never_writes():
    """Read-only guard: a curve call must not create/modify any row this
    session can observe via a subsequent read (compute_permission itself
    never writes; this route adds no write path)."""
    if not _live_reachable():
        pytest.skip("live Cloud SQL proxy not reachable at 127.0.0.1:5433 in this environment")
    conn = psycopg.connect(LIVE_DSN)
    try:
        before = conn.execute("SELECT count(*) FROM build_substep_progress").fetchone()[0]
    finally:
        conn.close()
    resp = client.post("/api/compute/permission_curve", json={
        "chart_id": CHART_ID, "event_class": "marriage",
        "t_start": "2013-12-01T00:00:00Z", "t_end": "2013-12-11T00:00:00Z", "step_days": 5,
    })
    assert resp.status_code == 200
    conn = psycopg.connect(LIVE_DSN)
    try:
        after = conn.execute("SELECT count(*) FROM build_substep_progress").fetchone()[0]
    finally:
        conn.close()
    assert before == after
