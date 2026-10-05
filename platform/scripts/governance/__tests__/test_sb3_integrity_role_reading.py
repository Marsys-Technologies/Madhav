"""test_sb3_integrity_role_reading.py -- an integrity check the census role may not run reads NO_DETECTOR naming the denied object and the
declared way to measure it (never PASS, never a verdict on the data); a view target with a constant count_sql says so in Build.count_integrity.
No database: `_integrity_outcome` is faked, measure() runs on the offline harness.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402


@pytest.mark.parametrize("msg,want", [
    ("ERROR:  42501: permission denied for function chart_identity", "function chart_identity"),
    ("ERROR:  42501: permission denied for table charts", "table charts"),
    ("ERROR:  42501: permission denied for view vw_chart_digest", "view vw_chart_digest"),
    ("ERROR:  42501: permission denied for schema private", "schema private"),
    ('ERROR:  42501: permission denied for function "Weird.Name"', 'function "Weird.Name"'),
    ("ERROR:  42501: permission denied", None),
    ("ERROR:  42P01: relation does not exist", None),
    ("", None),
])
def test_denied_object_is_parsed_from_the_server_message(msg, want):
    assert ac.denied_object(msg) == want


def test_not_measurable_cell_names_object_and_the_declared_way_and_stays_no_detector(monkeypatch):
    monkeypatch.setattr(ac, "_integrity_outcome", lambda sql: dict(state="not_measurable", sha="abc123abc123", secs=0.01,
                                                                    detail="ERROR: 42501: permission denied for function chart_identity"))
    r = ac._completion_integrity(dict(v=ac.PASS, measured="rows_written=5 = live=5"), dict(integrity_sql="SELECT chart_identity()"))
    assert r["v"] == ac.NO_DET, r
    for needle in ("integrity not measurable under the census role", "denied object: function chart_identity", "Declared way to measure it",
                   "asset_runner._probe_asset", "do NOT widen the census role", "NOT widened", "not a verdict on the data", "sha256:abc123abc123", "counts: rows_written=5 = live=5"):
        assert needle in r["measured"], (needle, r["measured"])


def test_not_measurable_with_an_unnamed_object_says_so(monkeypatch):
    monkeypatch.setattr(ac, "_integrity_outcome", lambda sql: dict(state="not_measurable", sha="s", secs=0, detail="ERROR: 42501: permission denied"))
    r = ac._completion_integrity(dict(v=ac.PASS, measured="m"), dict(integrity_sql="SELECT 1"))
    assert r["v"] == ac.NO_DET and "not named by the server message" in r["measured"]


def test_other_outcomes_are_unchanged(monkeypatch):
    for state, v in (("fails", ac.PARTIAL), ("refused", ac.PARTIAL), ("unrunnable", ac.PARTIAL), ("holds", ac.PASS)):
        monkeypatch.setattr(ac, "_integrity_outcome", lambda sql, s=state: dict(state=s, sha="s", secs=0, detail="d"))
        assert ac._completion_integrity(dict(v=ac.PASS, measured="m"), dict(integrity_sql="SELECT 1"))["v"] == v


def test_the_check_is_never_run_for_a_cell_that_is_not_pass(monkeypatch):
    monkeypatch.setattr(ac, "_integrity_outcome", lambda sql: pytest.fail("must not run"))
    rec = dict(v=ac.FAIL, measured="x")
    assert ac._completion_integrity(rec, dict(integrity_sql="SELECT 1")) is rec


# ───────────── Build.count_integrity on a view target with a constant count_sql (bo_samvada's shape) ─────────────

def _reg(aid, count_sql):
    return dict(asset_id=aid, has_writer=True, target_table="vw_x", count_sql=count_sql, has_integrity=True, integrity_sql=None, depends_on=[],
                target_floor="1", catalog_status="CURRENT", asset_kind="data")


def _stub(monkeypatch, tmp_path, reg):
    rec = dict(state="lit", rows_written="3", rps="", last_built="2026-09-01", n_rows=1, ambiguous=False, _key=(0.0, 0.0), built_epoch="0", duration=None)
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg), excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={"vw_x"}, cols={"vw_x": ["chart_id", "v"]}, keys={"vw_x": []}, views={"vw_x"}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: 3 for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {aid: {"": dict(rec)} for aid in reg})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=0, full=[], never=list(c), note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)


def _ci(census, aid):
    return next(a for a in census["assets"] if a["asset_id"] == aid)["measurements"]["Build.count_integrity"]


def test_view_with_constant_count_sql_says_the_registered_count_cannot_fail_and_verdict_is_unchanged(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {"bo_v": _reg("bo_v", "SELECT 0"), "bo_t": dict(_reg("bo_t", "SELECT count(*) FROM vw_x"))})
    c = _ci(ac.measure("L2"), "bo_v")
    assert c["v"] == ac.PASS and "count_sql reads no table (a constant)" in c["measured"] and "view vw_x" in c["measured"], c
    t = _ci(ac.measure("L2"), "bo_t")
    assert t["v"] == ac.PASS and "constant" not in t["measured"], t
