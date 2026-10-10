"""Lahiri-primary PR-5 (N-339): sidecar boundaries pin or validate the ayanamsha id.

DB-free: fake connections / monkeypatched cast, no psycopg connection is opened.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from services.ayanamsha_ids import (
    CROSS_CHECK_AYANAMSHA_IDS,
    PRIMARY_AYANAMSHA_ID,
    STORED_AYANAMSHA_IDS,
    normalize_ayanamsha_id,
)
from services.gochara_grammar import primitives as P
from services.gochara_grammar.models import ResonanceTarget

client = TestClient(app)
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
STORED = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]


# ── vocabulary module ────────────────────────────────────────────────────

def test_stored_ids_are_the_five_in_serve_order():
    assert list(STORED_AYANAMSHA_IDS) == STORED
    assert PRIMARY_AYANAMSHA_ID == "lahiri_chitrapaksha"
    assert list(CROSS_CHECK_AYANAMSHA_IDS) == STORED[1:]


@pytest.mark.parametrize("raw,expected", [
    (None, "lahiri_chitrapaksha"), ("", "lahiri_chitrapaksha"), ("lahiri", "lahiri_chitrapaksha"),
    ("LAHIRI", "lahiri_chitrapaksha"), ("kp", "krishnamurti"), ("true_citra", "true_chitra"),
    ("true_chitra", "true_chitra"), ("surya_siddhanta", "surya_siddhanta_classical"),
])
def test_normalize_maps_aliases_to_stored_ids(raw, expected):
    assert normalize_ayanamsha_id(raw) == expected


def test_normalize_unknown_lists_stored_ids():
    with pytest.raises(ValueError) as ei:
        normalize_ayanamsha_id("fagan_bradley")
    assert "lahiri_chitrapaksha" in str(ei.value)


# ── sade-sati: id pinned in SQL, cache keyed by (chart_id, ayanamsha_id) ──

class _Cur:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _SadeSatiConn:
    """Records every chart_facts query with its params; returns per-ayanamsha rows."""

    def __init__(self):
        self.queries: list[tuple[str, list]] = []
        self.autocommit = False

    def execute(self, sql, params=None):
        s = sql if isinstance(sql, str) else str(sql)
        if s.strip().startswith(("SAVEPOINT ", "RELEASE SAVEPOINT ", "ROLLBACK TO SAVEPOINT ")):
            return _Cur([])
        self.queries.append((s, list(params or [])))
        ay = (params or [None, None])[1]
        return _Cur([
            {"fact_subject": "cycle_1", "fact_key": "phase_start_iso",
             "fact_value_text": f"start-{ay}", "fact_value_num": None, "citation_human": None},
        ])

    def rollback(self):
        pass


def _target():
    return ResonanceTarget(chart_id=CHART_ID, event_class="marriage", target_type="bhava",
                           target_ref="7", weight=0.5,
                           classical_citation="BPHS Ch.71")


def test_sade_sati_sql_pins_ayanamsha_id():
    P.clear_primitive_read_caches()
    conn = _SadeSatiConn()
    out = P.sade_sati_phase(CHART_ID, _target(), conn=conn)
    sql, params = conn.queries[0]
    assert "ayanamsha_id = %s" in sql
    assert "ORDER BY" in sql
    assert params == [CHART_ID, "lahiri_chitrapaksha"]  # default = Lahiri primary
    assert out and out[0].detail["phase_start_iso"] == "start-lahiri_chitrapaksha"


def test_sade_sati_cache_is_keyed_by_chart_and_ayanamsha():
    P.clear_primitive_read_caches()
    conn = _SadeSatiConn()
    a = P.sade_sati_phase(CHART_ID, _target(), conn=conn, ayanamsha_id="lahiri_chitrapaksha")
    P.sade_sati_phase(CHART_ID, _target(), conn=conn, ayanamsha_id="lahiri_chitrapaksha")
    assert len(conn.queries) == 1, "same (chart, ayanamsha) is a cache hit"
    b = P.sade_sati_phase(CHART_ID, _target(), conn=conn, ayanamsha_id="krishnamurti")
    assert len(conn.queries) == 2, "a different ayanamsha must not reuse Lahiri's cached rows"
    assert a[0].detail["phase_start_iso"] != b[0].detail["phase_start_iso"]
    assert (CHART_ID, "krishnamurti") in P._SADE_SATI_ROWS_CACHE
    P.clear_primitive_read_caches()


# ── permission_curve / taranga: Literal of the five stored ids, 422 otherwise ──

_PC = {"chart_id": CHART_ID, "event_class": "marriage",
       "t_start": "2013-12-11T00:00:00Z", "t_end": "2013-12-01T00:00:00Z"}  # t_end<t_start -> 400 before any DB


@pytest.mark.parametrize("bad", ["lahiri", "kp", "true_citra", "yukteshwar", "kp_newcomb", ""])
def test_permission_curve_422_on_unknown_ayanamsha(bad):
    r = client.post("/api/compute/permission_curve", json={**_PC, "ayanamsha_id": bad})
    assert r.status_code == 422


@pytest.mark.parametrize("ok", STORED)
def test_permission_curve_accepts_each_stored_id(ok):
    r = client.post("/api/compute/permission_curve", json={**_PC, "ayanamsha_id": ok})
    assert r.status_code == 400  # passed id validation; rejected by the t_end check, before any DB
    assert "t_end must be >= t_start" in r.json()["detail"]


def test_permission_curve_default_is_lahiri():
    from routers.permission_curve import PermissionCurveRequest
    req = PermissionCurveRequest(chart_id=CHART_ID, event_class="marriage",
                                 t_start="2013-12-01T00:00:00Z", t_end="2013-12-02T00:00:00Z")
    assert req.ayanamsha_id == "lahiri_chitrapaksha"


def test_taranga_models_validate_and_default():
    from pydantic import ValidationError
    from routers import taranga as T
    for model, extra in ((T.ActivationRequest, {"t": "2026-01-01T00:00:00Z"}),
                         (T.CurveRequest, {"t_start": "2026-01-01T00:00:00Z", "t_end": "2026-02-01T00:00:00Z"}),
                         (T.RecordEvidenceRequest, {"t": "2026-01-01T00:00:00Z", "cited_by": "x"})):
        base = {"chart_id": CHART_ID, "target": "wealth", **extra}
        assert model(**base).ayanamsha_id == "lahiri_chitrapaksha"
        for ok in STORED:
            assert model(**base, ayanamsha_id=ok).ayanamsha_id == ok
        for bad in ("lahiri", "kp", "true_citra", "nonsense"):
            with pytest.raises(ValidationError):
                model(**base, ayanamsha_id=bad)


def test_taranga_route_422_on_unknown_ayanamsha():
    r = client.post("/api/compute/taranga/activation", json={
        "chart_id": CHART_ID, "target": "wealth", "t": "2026-01-01T00:00:00Z", "ayanamsha_id": "kp"})
    assert r.status_code == 422


# ── pyhora: stored id accepted, aliases mapped, unknown 422 (not 500) ──

def test_pyhora_boundary_normalises_and_rejects():
    from pydantic import ValidationError
    from routers.pyhora import BirthData
    base = dict(datetime_iso="1984-02-05T10:43:00", latitude_deg=20.27, longitude_deg=85.83, tz_offset_hours=5.5)
    assert BirthData(**base).ayanamsha_id == "lahiri_chitrapaksha"
    assert BirthData(**base, ayanamsha_id="lahiri").ayanamsha_id == "lahiri_chitrapaksha"
    assert BirthData(**base, ayanamsha_id="true_chitra").ayanamsha_id == "true_chitra"
    assert BirthData(**base, ayanamsha_id="true_citra").ayanamsha_id == "true_chitra"
    with pytest.raises(ValidationError):
        BirthData(**base, ayanamsha_id="nonsense")
    r = client.post("/api/pyhora/compute", json={**base, "ayanamsha_id": "nonsense"})
    assert r.status_code == 422


def test_pyhora_stored_ids_all_resolve_in_adapter():
    from pyjhora_adapter._ayanamsha import resolve_mode
    for a in STORED:
        resolve_mode(a)  # must not raise


# ── prashna: Lahiri judgment is THE answer; the four others labelled ──

def test_prashna_split_primary_and_four_labelled():
    from routers.prashna import split_primary_and_cross_check
    j = {a: {"verdict": a} for a in STORED}
    primary, cross = split_primary_and_cross_check(j)
    assert primary == {"verdict": "lahiri_chitrapaksha"}
    assert list(cross) == STORED[1:]
    assert all(cross[a] == {"verdict": a} for a in cross)
    assert "lahiri_chitrapaksha" not in cross


def test_prashna_missing_ayanamsha_is_named_null():
    from routers.prashna import split_primary_and_cross_check
    _, cross = split_primary_and_cross_check({"lahiri_chitrapaksha": {"v": 1}, "raman": {"v": 2}})
    assert list(cross) == STORED[1:]
    assert cross["krishnamurti"] is None and cross["raman"] == {"v": 2}


def test_prashna_route_response_keys(monkeypatch):
    import ga_writers.ga_prashna_cast as G
    import routers.prashna as R

    j = {a: {"verdict": f"v-{a}"} for a in STORED}
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake/none")
    monkeypatch.setattr(G, "validate_prashna_question", lambda q: {"valid": True, "reason": ""})
    monkeypatch.setattr(G, "cast_prashna_chart", lambda **kw: {
        "chart_id": "pc-1", "rows_inserted": 5, "primary_judgment": j["lahiri_chitrapaksha"],
        "judgment_by_ayanamsha": j})

    class _Conn:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def commit(self): pass

    monkeypatch.setattr(R.psycopg, "connect", lambda *a, **k: _Conn())
    r = client.post("/api/compute/prashna/cast", json={
        "question_text": "Will the move to the new city work out well?", "question_class": "career",
        "question_instant": "2026-06-18T22:00:00+05:30", "question_lat": 20.27, "question_lon": 85.83})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["primary_judgment"] == {"verdict": "v-lahiri_chitrapaksha"}
    assert body["primary_ayanamsha_id"] == "lahiri_chitrapaksha"
    assert list(body["judgment_by_ayanamsha"]) == STORED[1:]
    assert body["judgment_by_ayanamsha"]["krishnamurti"] == {"verdict": "v-krishnamurti"}
    assert "Cross-check, not the reading" in body["cross_check_label"]
