"""test_n189_bo_laksana_declared.py: the REAL bo_laksana `forwarded_leaves` declaration, end to end (SS ruling N-189).

The real declaration (asset_declarations.json), the real writer scan of bo_laksana.py, rows built by the REAL writer (`_build_signal_row`, `_load_vichara_divergence_signals`) in a DISPOSABLE
PostgreSQL, through `_measure_prose` and the rollup: faithful data lifts both Null cells; one flipped forwarded value turns the cell red; a timeout or an unmeasured form never reads PASS.

Run: python -m pytest platform/scripts/governance/__tests__/test_n189_bo_laksana_declared.py -q
"""
from __future__ import annotations

import json

import pytest

from test_n189_forwarded_leaves import (  # noqa: F401  (fixtures and builders shared with the detector tests)
    COLS, CHART, FACTS, FAIL, HERE, NO_DET, NULL, PARTIAL, PASS, PRODUCER, PROSE, T, TIMEOUT, VROWS, _fault, ac, disposable_pg, fact, mutate, project, vichara_world, world, writer,
)


def test_the_real_bo_laksana_declaration_validates_and_only_bo_laksana_declares():
    doc = json.loads((HERE.parent / "asset_declarations.json").read_text())
    entry = doc["assets"]["bo_laksana"]
    assert entry.get("forwarded_leaves") is not None and ac.forwarded_leaves_problem(entry) is None
    ac.validate_declarations(doc)
    declared = sorted(a for a, e in doc["assets"].items() if isinstance(e, dict) and e.get("forwarded_leaves") is not None)
    assert declared == ["bo_laksana"], declared                     # the sibling emitters (bo_arudha, bo_special_lagna, bo_sudarshana, bo_vargottama_dhana, bo_nakshatra_semantic, bo_laksana_rerank) do not forward fact_value_jsonb leaves


def _bo_laksana_entry():
    return json.loads((HERE.parent / "asset_declarations.json").read_text())["assets"]["bo_laksana"]


def _cat():
    types = {c: ("uuid" if c in ("signal_id", "chart_id") else "jsonb" if c == "configuration_jsonb" else "ARRAY" if c == "constituent_facts_array" else "text") for c in COLS}
    return dict(exists={T}, cols={T: list(COLS)}, types={T: types}, defaults={T: {}}, udts=None, keys=None)


def _measure_bo_laksana(shared=(T,)):
    decl = _bo_laksana_entry()
    r = dict(target_table=T, count_sql=f"SELECT count(*) FROM {T} WHERE chart_id = $1 AND producer_asset_id = '{PRODUCER}'")
    sc = ac.read_scopes([T], r, {T: COLS}, set(shared), decl, CHART)
    ac.set_read_scope(sc)
    return ac._measure_prose("bo_laksana", decl, r, ["bo_laksana.py"], _cat(), [T], set(shared), (), set()), decl


def test_REAL_SQL_end_to_end_the_real_declaration_and_writer_scan_lift_both_null_cells_on_faithful_data(world, writer):
    vichara_world(world, writer, VROWS, facts=FACTS + [fact("v1", key="vk1"), fact("v2", key="vk2")], with_projections=True)
    got, decl = _measure_bo_laksana()
    for c in NULL:
        assert got[c]["v"] == PASS and got[c]["forwarded_leaves"]["verified"] is True, (c, got[c]["measured"])
        assert got[c]["forwarded_leaves"]["forms"]["chart_facts_row"]["count"] >= 4 and got[c]["forwarded_leaves"]["forms"]["chart_vichara_row"]["count"] == 2
        assert got[c]["forwarded_leaves"]["scan_waived"]["empty_fallbacks"] >= 1 and "writer_scan" not in got[c]
    cells = ac.rollup_asset("L2", {c: got[c] for c in NULL}, dict(declared_prose_fields=decl["prose_fields"]))
    assert cells["Null"]["v"] == PASS and all(ch.get("null_forwarded_leaves_verified") is True for ch in cells["Null"]["checks"])


def test_REAL_SQL_end_to_end_one_flipped_forwarded_value_turns_the_null_cell_red(world, writer):
    vichara_world(world, writer, VROWS, facts=FACTS + [fact("v1", key="vk1"), fact("v2", key="vk2")], with_projections=True)
    mutate(project(writer, FACTS[0])["signal_id"], "configuration_jsonb = jsonb_set(configuration_jsonb, '{fact_value_text}', '\"forged\"')")
    got, decl = _measure_bo_laksana()
    assert got["Null.blank_rows"]["v"] == FAIL and "forwarded \"forged\" vs L1 \"exalted\"" in got["Null.blank_rows"]["measured"]
    assert ac.rollup_asset("L2", {c: got[c] for c in NULL}, dict(declared_prose_fields=decl["prose_fields"]))["Null"]["v"] == FAIL


def test_REAL_SQL_end_to_end_a_timeout_leaves_the_cells_at_the_static_scans_partial_never_pass(world, writer, monkeypatch):
    vichara_world(world, writer, VROWS, facts=FACTS + [fact("v1", key="vk1"), fact("v2", key="vk2")], with_projections=True)
    _fault(monkeypatch, "CROSS JOIN LATERAL unnest", ac.Unknown(TIMEOUT))
    got, decl = _measure_bo_laksana()
    assert all(got[c]["v"] == PARTIAL and got[c]["forwarded_leaves"]["v"] == NO_DET and "statement timeout" in got[c]["measured"] for c in NULL)


def test_REAL_SQL_end_to_end_a_chart_without_vichara_rows_stays_partial_naming_the_unmeasured_form(world, writer):
    world(FACTS)
    got, decl = _measure_bo_laksana()
    assert all(got[c]["v"] == PARTIAL and "chart_vichara_row have no row in the measured chart" in got[c]["measured"] for c in NULL)
