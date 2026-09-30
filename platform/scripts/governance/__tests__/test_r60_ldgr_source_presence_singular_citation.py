"""test_r60_ldgr_source_presence_singular_citation.py — R60 (NIKASHA_CHANGE_REGISTER_v2_0.md).

`Ldgr.source_presence`'s citation-column list (`source_citation`, `source_text_id`,
`classical_citations`, `citation_ref`) missed the singular `classical_citation` — measured
2026-09-28 via information_schema, at least a dozen L0 tables carry it (bg_nakshatra_medical,
bg_avastha_schemes, bg_combustion_orbs, bg_dignity_reference, bg_graha_dik,
bg_graha_naisargika_friendship, bg_medical_mappings, bg_motion_state_thresholds, five
bg_prashna_* tables, bg_shashtiamsha_deities, bg_sign_medical, bg_transit_av_gates,
bg_transit_moorti), and every one of them got NO Ldgr check at all despite a fully-populated
citation column.

Uses the same offline `measure()` harness as `test_a4_gate_corrections.py` (`_stub_layer` +
per-asset `psql` stub) so the REAL production code path runs end to end, offline. Fails without
the fix: `Ldgr.source_presence` is simply absent from the measurements dict for a table whose only
citation column is the singular `classical_citation`.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402


def _reg_row(aid, target_table=None, has_writer=False):
    return dict(asset_id=aid, has_writer=has_writer, target_table=target_table, count_sql="",
                has_integrity=False, depends_on=[], target_floor=None, catalog_status="", asset_kind="")


def _stub_layer(monkeypatch, ctrl, reg, tables=None):
    tables = tables or {}
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg),
                                                                    excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(tables),
                                                       cols={t: c for t, (c, _k) in tables.items()},
                                                       keys={t: k for t, (_c, k) in tables.items()}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: None for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=48, full=list(c), never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)


def _measured(census, aid, crit):
    asset = next(a for a in census["assets"] if a["asset_id"] == aid)
    return asset["measurements"].get(crit)


_TABLE = {"bg_nakshatra_medical": (["id", "nakshatra_id", "condition", "classical_citation"], [])}


def test_ldgr_source_presence_fires_on_singular_classical_citation(monkeypatch, tmp_path):
    _stub_layer(monkeypatch, tmp_path, {"bg_nakshatra_medical": _reg_row("bg_nakshatra_medical", "bg_nakshatra_medical")}, _TABLE)

    def fake_psql(sql, sep="\x1f", timeout=None):
        if "count(*)::text FROM bg_nakshatra_medical WHERE classical_citation IS NOT NULL" in sql:
            return [["48"]]
        raise AssertionError(f"unexpected query: {sql[:100]}")

    monkeypatch.setattr(ac, "psql", fake_psql)
    res = _measured(ac.measure("L0"), "bg_nakshatra_medical", "Ldgr.source_presence")
    assert res is not None, "Ldgr.source_presence must fire for a table whose only citation column is the singular 'classical_citation'"
    assert res == dict(v=ac.PASS, measured="classical_citation populated on 48/48 rows")


def test_other_citation_column_names_still_work(monkeypatch, tmp_path):
    """Regression guard: adding the singular form must not disturb the pre-existing column names."""
    table = {"bg_x": (["id", "source_citation"], [])}
    _stub_layer(monkeypatch, tmp_path, {"bg_x": _reg_row("bg_x", "bg_x")}, table)

    def fake_psql(sql, sep="\x1f", timeout=None):
        if "count(*)::text FROM bg_x WHERE source_citation IS NOT NULL" in sql:
            return [["10"]]
        raise AssertionError(f"unexpected query: {sql[:100]}")

    monkeypatch.setattr(ac, "psql", fake_psql)
    res = _measured(ac.measure("L0"), "bg_x", "Ldgr.source_presence")
    assert res == dict(v=ac.PARTIAL, measured="source_citation populated on 10/48 rows")
