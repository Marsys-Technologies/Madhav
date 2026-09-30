"""test_r99_empty_table_agreeing_build_record.py — R99 (NIKASHA_CHANGE_REGISTER_v2_0.md).

The third, previously-uncovered case D4/D6's discipline already applies to (P4 derivability L1;
depends on R52, whose comment is preserved and extended in place, not re-opened): an EMPTY data
table (live=0) whose build record AGREES (rows_written=0) under a registry `target_floor=0`
declaration used to read a blanket PASS via R52's fix — but `target_floor=0` alone is not "the
layer plan declares this asset empty by design" (T4 §4.2 check 6's own clause); it is frequently
just an unset floor. The uncovered case is a WRITER-BACKED data asset (`has_writer=true`) that has
actually run and still produced zero rows — ga_prashna: 51 runs, 0 rows, 0 modules — which is
indistinguishable from a writer that has never worked. `has_writer` is the one existing registry
signal (no new field invented) that separates it from a genuinely no-writer, empty-by-design asset
(bg_sarvatobhadra_grid: has_writer=false).

Uses the same offline `measure()` harness as test_a4_gate_corrections.py / test_r60. Fails without
the fix: a writer-backed, persistently-empty asset reads PASS (R52's blanket rule) instead of the
honest PARTIAL this row requires.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402


def _reg_row(aid, target_table, has_writer, count_sql):
    return dict(asset_id=aid, has_writer=has_writer, target_table=target_table, count_sql=count_sql,
                has_integrity=True, depends_on=[], target_floor="0", catalog_status="CURRENT",
                asset_kind="data")


def _stub_layer(monkeypatch, ctrl, reg, tables, thru_rec):
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg),
                                                                    excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(tables),
                                                       cols={t: c for t, (c, _k) in tables.items()},
                                                       keys={t: k for t, (_c, k) in tables.items()}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    # live=0 for every asset — the empty-table case under test.
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: 0 for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {aid: {"": dict(thru_rec)} for aid in reg})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=0, full=[], never=list(c), note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)


def _measured(census, aid, crit):
    return next(a for a in census["assets"] if a["asset_id"] == aid)["measurements"][crit]


_REC = dict(state="lit", rows_written="0", rps="", last_built="2026-09-01", n_rows=1, ambiguous=False,
            _key=(0.0, 0.0), built_epoch="0", duration=None)

_TABLE = {"ga_prashna_judgment": (["id", "verdict"], [])}


def test_writer_backed_persistently_empty_asset_reads_partial_not_pass(monkeypatch, tmp_path):
    """ga_prashna's own shape: has_writer=true, live=0, rows_written=0, target_floor=0."""
    reg = {"ga_prashna": _reg_row("ga_prashna", "ga_prashna_judgment", True,
                                  "SELECT count(*) FROM ga_prashna_judgment")}
    _stub_layer(monkeypatch, tmp_path, reg, _TABLE, _REC)
    res = _measured(ac.measure("L0"), "ga_prashna", "Build.completion")
    assert res["v"] == ac.PARTIAL, res
    assert "has_writer=true" in res["measured"] and "no layer-plan claim" in res["measured"]


def test_no_writer_empty_by_design_asset_still_reads_pass(monkeypatch, tmp_path):
    """bg_sarvatobhadra_grid's own shape: has_writer=false — R52's original PASS path must survive."""
    reg = {"bg_sarvatobhadra_grid": _reg_row("bg_sarvatobhadra_grid", "ga_prashna_judgment", False,
                                             "SELECT count(*) FROM ga_prashna_judgment")}
    _stub_layer(monkeypatch, tmp_path, reg, _TABLE, _REC)
    res = _measured(ac.measure("L0"), "bg_sarvatobhadra_grid", "Build.completion")
    assert res["v"] == ac.PASS, res
    assert "has_writer=false" in res["measured"]


def test_non_empty_consistent_asset_is_unaffected(monkeypatch, tmp_path):
    """Regression guard: a normal non-empty, consistent build record must still PASS (R99 must not
    touch the live>0 path at all)."""
    reg = {"bg_y": _reg_row("bg_y", "ga_prashna_judgment", True, "SELECT count(*) FROM ga_prashna_judgment")}
    _stub_layer(monkeypatch, tmp_path, reg, _TABLE, _REC)
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: 5 for x in r}, {}))
    rec = dict(_REC, rows_written="5")
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {aid: {"": dict(rec)} for aid in reg})
    res = _measured(ac.measure("L0"), "bg_y", "Build.completion")
    assert res["v"] == ac.PASS, res
