"""The plan file and the contract document say what the executor does (no database)."""
from __future__ import annotations

import hashlib
import re

from conftest import EXEC_DIR

PLAN = EXEC_DIR / "D6_COMBINED_DATAPLANE_CAPTURE_FA2_PLAN_DRAFT.md"
CONTRACT = EXEC_DIR.parent / "DATAPLANE_CAPTURE_TYPED_VALUE_CONTRACT_v1_0.md"
AUTH = ("Authorization: run the D6 owner-path plan with hash `<PLAN_HASH>` on production (the L1 data-plane capture repair, option A / N-84, plus the "
        "F-A2 ga_vargas key widening), exactly as described in `<PLAN FILE PATH>` sha256 `<PLAN_FILE_SHA>`, after Strategic Suvarna has approved the dry run. "
        "No other change.")


def test_the_plain_language_summary_is_first_and_the_authorisation_sentence_is_exact():
    t = PLAN.read_text()
    body = t.split("\n---\n", 1)[1]
    assert body.index("## 0. One-page summary for the owner") < body.index("## 1. The owner's authorisation") < body.index("## 3. The numbered items")
    assert "> " + AUTH in t
    summary = body[body.index("## 0."):body.index("## 1.")]
    assert len(summary.split()) < 700                                                        # one page
    for must in ("Nothing is inserted into, changed in or deleted from any chart", "How it is undone", "What can go wrong", "option A", "B", "C"):
        assert must in summary, must


def test_b_and_c_are_named_separately_from_option_a_and_are_not_in_the_plan(mod):
    t = PLAN.read_text()
    assert "plus patch B" in t and "plus patch C" in t and "separate approval" in t
    sec2 = t[t.index("## 2. Status of the hunk set"):t.index("## 3.")]
    assert re.search(r"\| \*\*B\*\* \|.*\*\*NO, candidate\*\*", sec2) and re.search(r"\| \*\*C\*\* \|.*\*\*NO, candidate\*\*", sec2)
    assert "DRAFT_NOT_FROZEN" in t and "<PLAN_FILE_SHA>" in t


def test_the_plan_file_quotes_the_bound_constants_of_the_executor(mod):
    t = PLAN.read_text()
    for p in mod.FUNCTION_PATCHES:
        for v in (p.live_md5, p.patched_md5, p.live_sha256, p.patched_sha256, p.diff_sha256):
            assert v in t, v
    assert mod.LIVE_TRG_DIGEST in t and mod.PATCHED_TRG_DIGEST in t
    for v in mod.GATE_REV3_PROPOSED.values():
        assert v in t
    for n in ("d6_f_a2_key_widening_DRAFT.py", "d6_capture_patch_a.py"):
        assert hashlib.sha256((EXEC_DIR / n).read_bytes()).hexdigest() in t, n


def test_the_plan_hash_cannot_contain_the_plan_file_sha(mod):
    """No circularity: neither the executor nor the hashed plan text reads or names the plan file."""
    assert hashlib.sha256(PLAN.read_bytes()).hexdigest() not in mod.render_plan()
    assert "D6_COMBINED_DATAPLANE" not in mod.render_plan() and "PLAN_DRAFT" not in (EXEC_DIR / "d6_dataplane_capture_fa2_exec.py").read_text()


def test_the_contract_states_the_precedence_the_marker_and_the_complete_record(mod):
    t = CONTRACT.read_text()
    for must in ("fact_value_num", "fact_value_text", "fact_value_jsonb", "typed_value_column", "companion_value_columns", "source_row_jsonb",
                 "floored", "unavailable", "complete record"):
        assert must in t, must
    assert t.index("`fact_value_num`, when not NULL") < t.index("`fact_value_text`, when not NULL") < t.index("`fact_value_jsonb`, when not NULL")
    # the installed comments carry the same keywords (the contract lives in the database too)
    comments = " ".join(list(mod.COMMENT_NEW_TABLES.values()) + list(mod.COMMENT_NEW_COLUMNS.values()))
    for must in ("typed_value_column", "companion_value_columns", "source_row_jsonb", "num, then text, then jsonb"):
        assert must in comments, must
