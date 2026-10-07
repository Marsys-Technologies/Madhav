"""test_formgap_decl_sibling.py: the two committed `writer_sibling` declarations are TRUE on the real writers (SS N-203).

bg_nakshatra_medical rides bg_medical_mappings (which declares the table in its produced_tables), bg_transit_engine rides bg_transit_rules (which declares none, so the writer scan is the evidence).
The registry rows stay has_writer=false; the real writer scan sees each primary write the sibling's table. Mutations: a primary without a writer, a table outside the produced set, a writer-built
claimant each FAIL.
"""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

DECLS = ac.load_asset_declarations()
REG = ac.registered_ids("")
PAIRS = [("bg_nakshatra_medical", "bg_medical_mappings", "bg_nakshatra_medical"), ("bg_transit_engine", "bg_transit_rules", "bg_transit_engine")]


@pytest.mark.parametrize("sib,pri,table", PAIRS)
def test_the_committed_declaration_is_sound_and_names_the_shared_writer_line(sib, pri, table):
    e = DECLS[sib]
    ws = e["writer_sibling"]
    assert ac.writer_sibling_problem(sib, e) is None and e["kind"] == "rider" and ws["primary"] == pri and ws["tables"] == [table]
    path, line = ws["evidence"].rsplit(":", 1)
    txt = (ac.ROOT / path).read_text(encoding="utf-8").splitlines()[int(line) - 1]
    assert "@register" in txt and sib in txt                                                 # the evidence line IS the sibling's @register
    assert REG[sib] == REG[pri] and len(REG[sib]) == 1                                         # one shared writer file
    assert "writer_sibling" not in DECLS[pri] and "has_writer" not in e                         # the primary is no sibling; the sibling does not declare has_writer (the registry row is not flipped)


@pytest.mark.parametrize("sib,pri,table", PAIRS)
def test_REAL_SCAN_build_registered_reads_pass_for_the_sibling(sib, pri, table):
    r = dict(has_writer=False, target_table=table)                                              # the registry row: has_writer false, as it is
    pr = dict(has_writer=True, target_table=pri)
    got = ac.writer_sibling_record(sib, r, REG[sib], DECLS[sib]["writer_sibling"], pr, REG[pri], DECLS[pri])
    assert got["v"] == ac.PASS and got["writer_sibling"]["verified"] is True and r["has_writer"] is False, got
    assert (got["writer_sibling"]["declared_produced"] is not None) == (pri == "bg_medical_mappings")


@pytest.mark.parametrize("sib,pri,table", PAIRS)
def test_REAL_SCAN_MUTATIONS_each_condition_turns_the_reading_red(sib, pri, table):
    r = dict(has_writer=False, target_table=table)
    pr = dict(has_writer=True, target_table=pri)
    ws = DECLS[sib]["writer_sibling"]
    base = (sib, r, REG[sib], ws, pr, REG[pri], DECLS[pri])
    assert ac.writer_sibling_record(*base)["v"] == ac.PASS
    assert ac.writer_sibling_record(sib, r, REG[sib], ws, dict(pr, has_writer=False), REG[pri], DECLS[pri])["v"] == ac.FAIL          # a primary without a writer
    assert ac.writer_sibling_record(sib, dict(r, has_writer=True), REG[sib], ws, pr, REG[pri], DECLS[pri])["v"] == ac.FAIL          # a writer-built claimant
    other = copy.deepcopy(ws)
    other["tables"] = [table, "bg_not_written_by_this_writer"]
    got = ac.writer_sibling_record(sib, r, REG[sib], other, pr, REG[pri], DECLS[pri])
    assert got["v"] == ac.FAIL and "bg_not_written_by_this_writer" in got["measured"]                                               # a table outside the primary's produced set
    assert ac.writer_sibling_record(sib, r, REG[sib], ws, pr, ["bg_other.py"], DECLS[pri])["v"] == ac.FAIL                          # not one writer class
    assert ac.writer_sibling_record(sib, r, REG[sib], ws, pr, REG[pri], dict(DECLS[pri], writer_sibling=ws))["v"] == ac.FAIL        # the primary is itself a sibling


def test_the_declared_produced_set_of_the_medical_primary_names_the_sibling_table_and_the_other_primary_does_not_declare_one():
    names = {d["table"] for d in ac.declared_produced_tables(DECLS["bg_medical_mappings"])}
    assert "bg_nakshatra_medical" in names and ac.declared_produced_tables(DECLS["bg_transit_rules"]) is None
    bad = ac.writer_sibling_record("bg_nakshatra_medical", dict(has_writer=False, target_table="bg_nakshatra_medical"), REG["bg_nakshatra_medical"], DECLS["bg_nakshatra_medical"]["writer_sibling"],
                                   dict(has_writer=True), REG["bg_medical_mappings"], dict(DECLS["bg_medical_mappings"], produced_tables=[{"table": "bg_medical_mappings"}]))
    assert bad["v"] == ac.FAIL and "outside the declared produced_tables" in bad["measured"]
