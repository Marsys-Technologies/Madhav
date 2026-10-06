"""test_sb4_zero_row_convention.py -- the DECLARED zero-row convention (SS N-149): a writer-backed asset that legitimately has no rows for a chart reads
Build.completion PASS (rows_written 0 = live 0) only where the census VERIFIED the declared condition against the live scope table; otherwise the
R99 PARTIAL stands. Count.floor on that chart reads N/A-by-design (cause zero-row-convention-holds). Offline: psql is faked, measure() on the harness.
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

CH = ac.CHART_ID
EVID = "platform/python-sidecar/ga_writers/ga_prashna_writer.py:134"
ZR = dict(scope_table="prashna_charts", scope_column="chart_id", applies_when="chart_absent",
          why="a natal chart has no row in prashna_charts, and the writer returns zero rows for it by design", evidence=EVID)


# ───────────── the declaration validator ─────────────

def _doc(zr):
    e = dict(kind="data", zero_row_convention=zr)
    return dict(version="x", kind_enum=list(ac.DECLARED_KINDS), assets={"ga_prashna": e})


def test_a_well_formed_declaration_validates():
    ac.validate_declarations(_doc(ZR))


@pytest.mark.parametrize("patch,match", [
    (dict(scope_table="prashna charts"), "scope_table"),
    (dict(scope_column="chart_id; drop"), "scope_column"),
    (dict(applies_when="always"), "applies_when"),
    (dict(why="short"), "why"),
    (dict(evidence="unverified:i believe so by the writer code"), "evidence"),
    (dict(evidence="platform/python-sidecar/ga_writers/nope.py:1"), "evidence"),
    (dict(extra="x"), "unknown field"),
])
def test_a_malformed_declaration_is_refused(patch, match):
    zr = dict(ZR, **patch)
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(zr))


def test_the_committed_declarations_file_loads_and_declares_the_ga_prashna_convention():
    d = ac.load_asset_declarations()
    zr = d["ga_prashna"]["zero_row_convention"]
    assert zr["scope_table"] == "prashna_charts" and zr["scope_column"] == "chart_id" and zr["applies_when"] == "chart_absent"
    assert [a for a, e in d.items() if "zero_row_convention" in e] == ["ga_prashna"]


# ───────────── the verification (fake psql) ─────────────

def _fake(monkeypatch, cols="1", absent="t", boom=None):
    sent = []

    def fake(sql, *a, **k):
        sent.append(sql)
        if boom:
            raise ac.Unknown(boom)
        return [[cols]] if "information_schema" in sql else [[absent]]
    monkeypatch.setattr(ac, "psql", fake)
    return sent


def test_outcome_holds_when_the_chart_is_absent_from_the_scope_table(monkeypatch):
    sent = _fake(monkeypatch)
    o = ac.zero_row_convention_outcome(ZR, CH)
    assert o["state"] == "holds" and "has no row in prashna_charts.chart_id" in o["detail"], o
    assert any('"prashna_charts"' in s and CH in s for s in sent)          # the census wrote the SQL itself, over validated identifiers


def test_outcome_does_not_hold_when_the_chart_is_in_the_scope_table(monkeypatch):
    _fake(monkeypatch, absent="f")
    assert ac.zero_row_convention_outcome(ZR, CH)["state"] == "does_not_hold"


def test_outcome_is_unverified_on_a_missing_column_a_failed_read_or_a_ragged_answer(monkeypatch):
    _fake(monkeypatch, cols="0")
    assert ac.zero_row_convention_outcome(ZR, CH)["state"] == "unverified"
    _fake(monkeypatch, boom="connection refused")
    o = ac.zero_row_convention_outcome(ZR, CH)
    assert o["state"] == "unverified" and "connection refused" in o["detail"]
    _fake(monkeypatch, absent="maybe")
    assert ac.zero_row_convention_outcome(ZR, CH)["state"] == "unverified"


# ───────────── measure() wiring ─────────────

def _reg(floor="5", integrity_sql=None):
    return dict(asset_id="ga_prashna", has_writer=True, target_table="ga_prashna_judgment", count_sql="SELECT count(*) FROM ga_prashna_judgment",
                has_integrity=integrity_sql is not None, integrity_sql=integrity_sql, depends_on=[], target_floor=floor, catalog_status="CURRENT",
                asset_kind="data")


def _stub(monkeypatch, tmp_path, reg, decls):
    rec = dict(state="lit", rows_written="0", rps="", last_built="2026-09-01", n_rows=1, ambiguous=False, _key=(0.0, 0.0), built_epoch="0", duration=None)
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    monkeypatch.setattr(ac, "registry", lambda k: ({"ga_prashna": reg}, dict(registry_total=1, active=1, excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={"ga_prashna_judgment"}, cols={"ga_prashna_judgment": ["id"]}, keys={"ga_prashna_judgment": []}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: 0 for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {"ga_prashna": {"": dict(rec)}})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {"ga_prashna": []}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=0, full=[], never=list(c), note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decls)


def _cells(census):
    return next(a for a in census["assets"] if a["asset_id"] == "ga_prashna")["measurements"]


DECL = {"ga_prashna": {"kind": "data", "zero_row_convention": ZR}}


def test_verified_convention_reads_pass_with_zero_rows_and_count_floor_is_na_by_design(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, _reg(), DECL)
    _fake(monkeypatch)
    m = _cells(ac.measure("L1"))
    assert m["Build.completion"]["v"] == ac.PASS and "rows_written=0 = live=0" in m["Build.completion"]["measured"], m["Build.completion"]
    assert "zero_row_convention" in m["Build.completion"]["measured"] and "has no row in prashna_charts.chart_id" in m["Build.completion"]["measured"]
    cf = m["Count.floor"]
    assert cf["v"] == ac.NA and cf["cause"] == "zero-row-convention-holds" and "floor does not apply" in cf["measured"], cf


def test_convention_that_does_not_hold_keeps_the_partial_under_floor_zero(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, _reg(floor="0"), DECL)
    _fake(monkeypatch, absent="f")
    m = _cells(ac.measure("L1"))
    assert m["Build.completion"]["v"] == ac.PARTIAL and "does not hold here" in m["Build.completion"]["measured"], m["Build.completion"]
    assert m["Count.floor"]["cause"] == "target-floor-zero"


def test_convention_that_does_not_hold_keeps_the_fail_and_the_floor_breach_under_a_real_floor(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, _reg(floor="5"), DECL)
    _fake(monkeypatch, absent="f")
    m = _cells(ac.measure("L1"))
    assert m["Build.completion"]["v"] == ac.FAIL and "empty: live=0" in m["Build.completion"]["measured"], m["Build.completion"]
    assert m["Count.floor"]["v"] == ac.FAIL


def test_unverifiable_convention_keeps_the_partial_naming_why(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, _reg(floor="0"), DECL)
    _fake(monkeypatch, boom="connection refused")
    m = _cells(ac.measure("L1"))
    assert m["Build.completion"]["v"] == ac.PARTIAL and "could not be verified" in m["Build.completion"]["measured"] and "connection refused" in m["Build.completion"]["measured"]
    _stub(monkeypatch, tmp_path, _reg(floor="5"), DECL)                    # under a real floor an unverified convention changes nothing: FAIL as before
    assert _cells(ac.measure("L1"))["Build.completion"]["v"] == ac.FAIL


def test_no_declaration_reads_exactly_as_before(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, _reg(floor="0"), {"ga_prashna": {"kind": "data"}})
    sent = _fake(monkeypatch)
    m = _cells(ac.measure("L1"))
    assert m["Build.completion"]["v"] == ac.PARTIAL and "no layer-plan claim" in m["Build.completion"]["measured"]
    assert "zero_row_convention" not in m["Build.completion"]["measured"] and not sent, sent
    _stub(monkeypatch, tmp_path, _reg(floor="5"), {"ga_prashna": {"kind": "data"}})
    m = _cells(ac.measure("L1"))
    assert m["Build.completion"]["v"] == ac.FAIL and m["Count.floor"]["v"] == ac.FAIL


def test_the_record_must_still_agree_for_the_convention_to_pass(monkeypatch, tmp_path):
    """The convention releases the EMPTINESS, not the build record: a record that is not a completed build, or says rows_written>0 against live 0,
    keeps its FAIL."""
    for patch in (dict(state="error"), dict(rows_written="7"), dict(rows_written="")):
        _stub(monkeypatch, tmp_path, _reg(floor="0"), DECL)
        base = ac.throughput
        monkeypatch.setattr(ac, "throughput", lambda prefix, *a, _p=patch, **k: {"ga_prashna": {"": dict(next(iter(base(prefix).values()))[""], **_p)}})
        _fake(monkeypatch)
        assert _cells(ac.measure("L1"))["Build.completion"]["v"] != ac.PASS, patch


def test_a_declared_integrity_sql_must_still_hold_under_the_convention(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, _reg(integrity_sql="SELECT false"), DECL)
    _fake(monkeypatch)
    monkeypatch.setattr(ac, "_integrity_outcome", lambda sql: dict(state="fails", sha="s", secs=0, detail="first column of the first row = f"))
    m = _cells(ac.measure("L1"))
    assert m["Build.completion"]["v"] == ac.PARTIAL and "does NOT hold" in m["Build.completion"]["measured"], m["Build.completion"]


def test_count_floor_zero_still_reads_its_own_na(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, _reg(floor="0"), DECL)
    _fake(monkeypatch)
    cf = _cells(ac.measure("L1"))["Count.floor"]
    assert cf["v"] == ac.NA and cf["cause"] == "target-floor-zero", cf


def test_the_na_cause_is_registered_for_count_floor():
    assert "zero-row-convention-holds" in ac.NA_CAUSES["Count.floor"]
    ac.validate_na_rule_decisions()
