"""test_n430_pratijna_phrases.py: SS N-425/N-429 item 3a. bo_pratijna's five constant absence statements are declared through the existing `writer_constant_phrases` form (SS N-279).

The Null writer scan flags five findings in bo_pratijna's writers (3 distinct literals: the yoga-factor honest gap, 'no KaryatvaMap registered for this event_class_id', 'no D1 house data', each written
to the entries derivation.$.denials[*].reason / derivation.$.factor_ledger[*].connections[*].reason / derivation.$.factor_ledger[*].detail). Each is an honest absence statement the writer is MEANT to write.
The declaration is CHECKED per literal against the writer source AST and matched to a scan finding; every finding must be covered. Source only: no database. The data-level Null reading is a census
matter (the existing Null cells already read clean on the rows themselves); this file proves the declaration lifts exactly the writer-scan findings and nothing else.
"""
from __future__ import annotations

import copy
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

WS = ac._lint_module("writer_literal_scan")
AID = "bo_pratijna"


def _real():
    decl = ac.load_asset_declarations()[AID]
    units, _ = ac.writer_scan_scope(AID, ac.registered_ids("")[AID])
    pf = list(decl["prose_fields"])
    ws = WS.scan(units, pf, {ac.parse_prose_field(e)[0]: ["bodha_pratijna"] for e in pf}, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)
    return decl, units, ws


def test_the_scan_finds_exactly_the_five_constant_writes_these_declarations_name():
    decl, units, ws = _real()
    found = sorted((p["entry"], p["where"], p["kind"]) for p in ws["problems"])
    assert len(found) == 5 and {k for _, _, k in found} == {"constant_write"} and not ws["unresolved"]
    declared = sorted((d["entry"], f"{d['file']}:{d['evidence'].rsplit(':', 1)[1]}", "constant_write") for d in decl["writer_constant_phrases"])
    assert found == declared


def test_the_declaration_validates_and_covers_every_finding():
    decl, units, ws = _real()
    assert ac.writer_constant_phrases_problem(decl) is None
    chk = ac.constant_phrases_check(decl["writer_constant_phrases"], decl["prose_fields"], ws, units)
    assert chk["problems"] == [] and len(chk["covered"]) == 5 and chk["left"] == []


def test_a_missing_declaration_leaves_a_finding_uncovered():
    decl, units, ws = _real()
    items = copy.deepcopy(decl["writer_constant_phrases"])
    del items[0]
    chk = ac.constant_phrases_check(items, decl["prose_fields"], ws, units)
    assert chk["left"], "a finding with no declaration must stay uncovered (it keeps the cap)"


def test_a_changed_literal_is_refused():
    decl, units, ws = _real()
    items = copy.deepcopy(decl["writer_constant_phrases"])
    items[2]["literal"] = items[2]["literal"] + " (edited)"
    chk = ac.constant_phrases_check(items, decl["prose_fields"], ws, units)
    assert chk["problems"], "a literal that is not verbatim in the writer must be refused"


def test_every_entry_is_a_declared_prose_field_and_every_file_is_a_pratijna_writer():
    decl, _, _ = _real()
    for d in decl["writer_constant_phrases"]:
        assert d["entry"] in decl["prose_fields"] and d["file"] in ("bo_pratijna.py", "bo_pratijna_v4_engine.py") and len(d["literal"]) <= 160
