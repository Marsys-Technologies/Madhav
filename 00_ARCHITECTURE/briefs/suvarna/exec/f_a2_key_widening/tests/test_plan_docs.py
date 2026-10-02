"""The plan file and the contract document say what the executor does (no database)."""
from __future__ import annotations

import hashlib
import re

from conftest import EXEC_DIR

PLAN = EXEC_DIR / "D6_COMBINED_DATAPLANE_CAPTURE_FA2_PLAN_DRAFT.md"
CONTRACT = EXEC_DIR.parent / "DATAPLANE_CAPTURE_TYPED_VALUE_CONTRACT_v1_0.md"
AUTH = ("Authorization: run the D6 owner-path plan with hash `<PLAN_HASH>` on production (the L1 data-plane capture repair, option A / N-84; patch B and "
        "patch C, approved as design in N-85; plus the F-A2 ga_vargas key widening), exactly as described in `<PLAN FILE PATH>` sha256 `<PLAN_FILE_SHA>`, "
        "after Strategic Suvarna has approved the dry run. No other change.")


def test_the_plain_language_summary_is_first_and_the_authorisation_sentence_is_exact():
    t = PLAN.read_text()
    body = t.split("\n---\n", 1)[1]
    assert body.index("## 0. One-page summary for the owner") < body.index("## 1. The owner's authorisation") < body.index("## 3. The numbered items")
    assert "> " + AUTH in t
    summary = body[body.index("## 0."):body.index("## 1.")]
    assert len(summary.split()) < 1100                                                       # one dense page
    for must in ("nothing is inserted into, changed in or deleted from any chart's data", "How it is undone", "What can go wrong", "What changes in the production database"):
        assert must in summary, must


def test_the_summary_lists_a_b_c_and_fa2_as_four_numbered_items_each_with_a_serving_effect_and_item_5_is_a_marked_empty_slot():
    t = PLAN.read_text()
    summary = t[t.index("**The four items**"):t.index("**What changes in the production database.**")]
    items = [ln for ln in summary.splitlines() if ln[:3] in ("1. ", "2. ", "3. ", "4. ")]
    assert len(items) == 4
    for ln, key in zip(items, ("Option A (N-84)", "Patch B (N-85)", "Patch C (N-85)", "F-A2")):
        assert key in ln and "*What it changes:*" in ln and "*Serving effect:*" in ln, key
    assert "RESERVED, NOT WRITTEN, NOT PART OF THIS PLAN" in summary and "item 5" in summary
    sec2 = t[t.index("## 2. Status of the hunk set"):t.index("## 3.")]
    assert "RESERVED SLOT, NOT WRITTEN" in sec2 and sec2.count("**YES**") == 4
    assert "DRAFT_NOT_FROZEN" in t and "<PLAN_FILE_SHA>" in t and "NOT COMPUTED FINAL" in t


def test_item_5_is_absent_from_the_executor_and_the_plan_but_its_slot_is_marked(mod):
    assert [p.signature for p in mod.FUNCTION_PATCHES] == ["l1_data_plane_capture_row()", "capture_l1_data_plane_dasha_partition(uuid,text,text,integer)",
                                                           "complete_l1_data_plane_partition(uuid,text,text,text,integer)"]
    src = (EXEC_DIR / "d6_dataplane_capture_fa2_exec.py").read_text()
    assert "ITEM 5, RESERVED SLOT, NOT WRITTEN" in src and "chart_vichara" not in mod.render_plan().replace("ITEM 5 (chart_vichara capture identity", "")
    assert "chart_vichara" not in " ".join(h[1] + h[2] for p in mod.FUNCTION_PATCHES for h in p.hunks)


def test_the_plan_file_quotes_the_bound_constants_of_the_executor(mod):
    t = PLAN.read_text()
    for p in mod.FUNCTION_PATCHES:
        for v in (p.live_md5, p.patched_md5, p.live_sha256, p.patched_sha256, p.diff_sha256):
            assert v in t, v
    assert mod.LIVE_TRG_DIGEST in t and mod.PATCHED_TRG_DIGEST in t
    for v in mod.GATE_PINS.values():
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
