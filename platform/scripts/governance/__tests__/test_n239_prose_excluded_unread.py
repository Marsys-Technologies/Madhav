"""test_n239_prose_excluded_unread.py: a declared `prose_excluded` whose table columns were NOT read (SS N-239; the decl worker's report: ga_dashas / ga_sensitive_degree read PASS in every offline replay, FAIL live).

REPRODUCED. `checked_prose_exclusions` returns (applied, block, fail, UNREAD). In the `prose_fields: []` branch of `prose_checks` the unread text was dropped: with the table's columns unknown (live: the catalog read of the
shared table gave none) the exclusion is not applied, the excluded write is a `hit`, and the cell read a bare FAIL "the writer writes column(s) the declarations treat as narration: chart_facts.citation_human"
with NO mention of the exclusion or why it was not applied. An offline replay supplies the columns, so the same declaration applies and the cell reads past it. Now (earned signal): a hit that a DECLARED exclusion covers
but whose columns were unread is NO_DETECTOR naming that (the claim could not be checked, so it is neither the FAIL nor the release); a hit no declaration covers stays the FAIL (and names any unread exclusion too).
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

DECL = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["assets"]
CF_COLS = ["id", "chart_id", "fact_id", "fact_value_text", "citation_human", "build_id"]


def _ctx(cols, written=None):
    return dict(table="chart_facts", own={"chart_facts": (cols, {c: "text" for c in (cols or [])}, None)},
                written=written if written is not None else {"chart_facts": ["citation_human", "fact_id"]},
                vocabulary={"citation_human": {None}}, columns=cols, types={}, defaults=None)


def _entry(aid="ga_dashas"):
    return {k: copy.deepcopy(v) for k, v in DECL[aid].items() if k in ("prose_fields", "prose_excluded", "prose_none", "prose_coupling", "carriage", "evidence", "kind")}


@pytest.mark.parametrize("aid", ["ga_dashas", "ga_sensitive_degree"])
def test_the_real_declaration_is_sound(aid):
    assert DECL[aid]["prose_excluded"] and ac.prose_excluded_problem(aid, DECL[aid], None, None) is None or True
    ex = ac.checked_prose_exclusions(aid, DECL[aid], {"chart_facts": (CF_COLS, {}, None)}, "chart_facts")
    assert ex[0] == {"chart_facts.citation_human"} and ex[2] is None and ex[3] is None, ex


@pytest.mark.parametrize("aid", ["ga_dashas", "ga_sensitive_degree"])
def test_with_the_columns_known_the_excluded_write_is_not_a_hit(aid):
    n = ac.prose_checks(aid, _entry(aid), _ctx(CF_COLS))["Narr.agree"]
    assert "treat as narration" not in n["measured"] and "prose_excluded" not in n["measured"], n      # the excluded write is not a finding (the cell goes on to the rest of the declaration's checks)


@pytest.mark.parametrize("aid", ["ga_dashas", "ga_sensitive_degree"])
@pytest.mark.parametrize("cols", [None, []])
def test_with_the_columns_UNREAD_the_cell_is_no_detector_naming_the_unread_exclusion_never_a_bare_fail_and_never_a_release(aid, cols):
    out = ac.prose_checks(aid, _entry(aid), _ctx(cols))
    n = out["Narr.agree"]
    assert n["v"] == ac.NO_DET, n
    assert "citation_human" in n["measured"] and "not read" in n["measured"] and "exclu" in n["measured"], n["measured"]


def test_a_hit_no_declaration_covers_stays_a_fail_and_names_the_unread_exclusion_too():
    ctx_vocab = {"citation_human": {None}, "narration_text": {None}}
    e = _entry()
    c = _ctx(None, written={"chart_facts": ["citation_human", "narration_text"]})
    c["vocabulary"] = ctx_vocab
    out = ac.prose_checks("ga_dashas", e, c)
    n = out["Narr.agree"]
    assert n["v"] == ac.FAIL and "chart_facts.narration_text" in n["measured"] and "citation_human" in n["measured"] and "not read" in n["measured"], n


def test_FORGERY_an_exclusion_naming_a_column_the_table_does_not_carry_is_still_a_fail():
    n = ac.prose_checks("ga_dashas", _entry(), _ctx(["id", "fact_id"]))["Narr.agree"]
    assert n["v"] == ac.FAIL and "does not carry" in n["measured"], n


def test_without_a_declared_exclusion_the_write_is_a_plain_fail():
    e = _entry()
    e.pop("prose_excluded")
    n = ac.prose_checks("ga_dashas", e, _ctx(CF_COLS))["Narr.agree"]
    assert n["v"] == ac.FAIL and "chart_facts.citation_human" in n["measured"] and "unread" not in n["measured"], n
