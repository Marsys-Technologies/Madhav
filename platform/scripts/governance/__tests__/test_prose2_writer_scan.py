"""test_prose2_writer_scan.py: TI-prose-batch2-writers. The Null writer scan (writer_literal_scan.py, the census's own
`writer_scan_scope` + `scan`) reads the edited L1 / L0 writers with NO literal fallback and NO constant write on the
prose columns it is declared for.

Every writer below was PARTIAL on the base because of named literal fallbacks / constant writes (the prose-batch-2
"Writer edits needed" list: ga_panchanga 171/338/341/653-662/703/754/1025/1121/1139, ga_positions 482/522, ga_sade_sati 909/1125/1388,
ga_sensitive 269/3043, ga_vargas 3323, ga_yoga 2708, the remedy loader's blank defaults); this file fails on that base and passes
with the writer edits. It asserts `problems == []` (the scan's findings a human must act on), NOT `v == PASS`: an asset can still
read PARTIAL for an UNRESOLVED path the scan cannot follow (a dict built by a comprehension, a hop-limit cut), which is a
limit of the scan and not a literal in the writer. bg_remedies is NOT in the first test: its 167 curated corpus sentences
(l0_remedy_corpus.py) are constant writes by design and are left for the declaration ruling (see the PR body); only the loader's
blank-string defaults are pinned (last test).

Source only: nothing here touches a database.

Run: python -m pytest platform/scripts/governance/__tests__/test_prose2_writer_scan.py -q
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402

WS = ac._lint_module("writer_literal_scan")
REG = ac.registered_ids("")

# asset -> (prose entries the committed declaration scans, the tables that hold them)
CASES = {
    "ga_panchanga": (["citation_human"], ["chart_facts"]),
    "ga_positions": (["citation_human"], ["chart_facts"]),
    "ga_sade_sati": (["citation_human"], ["chart_facts"]),
    "ga_sensitive": (["citation_human"], ["chart_facts"]),
    "ga_yoga": (["citation_human"], ["ga_yoga_firings", "chart_facts"]),
    "ga_vargas": (["citation_human"], ["chart_divisionals"]),
    "bg_remedies": (["prescription_text", "charity_action"], ["brahma_remedy_corpus"]),
}


def _scan(aid: str) -> dict:
    entries, tables = CASES[aid]
    units, beyond = ac.writer_scan_scope(aid, REG[aid])
    # one known column per table is enough for the holder lookup: the entries' own columns
    own = {t: (list({ac.parse_prose_field(e)[0] for e in entries}), None, None) for t in tables}
    holders = {ac.parse_prose_field(e)[0]: ac._holders(ac.parse_prose_field(e)[0], own) for e in entries}
    return WS.scan(units, list(entries), holders, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts,
                   parse_entry=ac.parse_prose_field, beyond=beyond)


@pytest.mark.parametrize("aid", sorted(a for a in CASES if a != "bg_remedies"))
def test_no_literal_fallback_or_constant_write_on_the_prose_column(aid):
    res = _scan(aid)
    assert res["problems"] == [], f"{aid}: {res['problems']}"


@pytest.mark.parametrize("aid", ["ga_panchanga", "ga_positions", "ga_sade_sati", "ga_sensitive", "ga_yoga"])
def test_these_five_assets_read_pass_on_the_writer_scan(aid):
    res = _scan(aid)
    assert res["v"] == "PASS", f"{aid}: {res['v']} {res['problems']} {res['unresolved']}"


def test_the_ga_vargas_d81_sentinel_is_no_longer_a_constant_write():
    res = _scan("ga_vargas")
    assert not [p for p in res["problems"] if p["kind"] == "constant_write"]
    # FORM-GAP (SS N-191, detector limits): the 33 sites that build the row through a non-literal subscript store used to stay opaque because the key name appeared once as a READ (`row.get("citation_human", "")`)
    # in the narration linter; a read cannot make a key appear in a row, so the scan no longer treats it as a supplier and finds nothing unresolved (test_formgap_scan_limits.py pins the mutation)
    assert not res["unresolved"]


def test_the_remedy_loader_has_no_blank_string_default_left_on_a_nullable_text_column():
    res = _scan("bg_remedies")
    assert not [p for p in res["problems"] if "l0_remedy_loader" in p["where"]]
