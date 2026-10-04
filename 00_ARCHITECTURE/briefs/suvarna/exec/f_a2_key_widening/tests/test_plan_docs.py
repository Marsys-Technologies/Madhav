"""The plan file and the contract document say what the executor does (no database)."""
from __future__ import annotations

import hashlib
import re

from conftest import EXEC_DIR

PLAN = EXEC_DIR / "D6_COMBINED_DATAPLANE_CAPTURE_FA2_PLAN_DRAFT.md"
CONTRACT = EXEC_DIR.parent / "DATAPLANE_CAPTURE_TYPED_VALUE_CONTRACT_v1_0.md"
AUTH = ("Authorization: run the D6 owner-path plan with hash `<PLAN_HASH>` on production (the L1 data-plane capture repair, option A / N-84; patch B and "
        "patch C, approved as design in N-85; the chart_vichara capture identity, K1; plus the F-A2 ga_vargas key widening; including the transient role grants `GRANT data_plane_l1_owner, amjis_app TO CURRENT_USER`, "
        "revoked in the same transaction, net membership unchanged), exactly as described in `<PLAN FILE PATH>` "
        "sha256 `<PLAN_FILE_SHA>`, "
        "after Strategic Suvarna has approved the dry run. No other change.")


def test_the_plain_language_summary_is_first_and_the_authorisation_sentence_is_exact():
    t = PLAN.read_text()
    body = t.split("\n---\n", 1)[1]
    assert body.index("## 0. One-page summary for the owner") < body.index("## 1. The owner's authorisation") < body.index("## 3. The numbered items")
    assert "> " + AUTH in t
    summary = body[body.index("## 0."):body.index("## 1.")]
    assert len(summary.split()) < 1500                                                       # one dense page
    for must in ("nothing is inserted into, changed in or deleted from any chart's data", "How it is undone", "What can go wrong", "What changes in the production database"):
        assert must in summary, must


def test_the_summary_lists_a_b_c_fa2_and_k1_as_five_numbered_items_each_with_a_serving_effect():
    t = PLAN.read_text()
    summary = t[t.index("**The five items**"):t.index("**What changes in the production database.**")]
    items = [ln for ln in summary.splitlines() if ln[:3] in ("1. ", "2. ", "3. ", "4. ", "5. ")]
    assert len(items) == 5
    for ln, key in zip(items, ("Option A (N-84)", "Patch B (N-85)", "Patch C (N-85)", "F-A2", "K1 (chart_vichara capture identity)")):
        assert key in ln and "*What it changes:*" in ln and "*Serving effect:*" in ln, key
    assert "**not** a natural key" in summary and "RESERVED" not in summary
    sec2 = t[t.index("## 2. Status of the hunk set"):t.index("## 3.")]
    assert "RESERVED" not in sec2 and sec2.count("**YES**") == 5
    assert "DRAFT_NOT_FROZEN" in t and "<PLAN_FILE_SHA>" in t and "NOT COMPUTED FINAL" in t


def test_item_5_is_the_chart_vichara_trigger_arguments_entry_and_not_a_function_hunk(mod):
    assert [p.signature for p in mod.FUNCTION_PATCHES] == ["l1_data_plane_capture_row()", "capture_l1_data_plane_dasha_partition(uuid,text,text,integer)",
                                                           "complete_l1_data_plane_partition(uuid,text,text,text,integer)"]
    assert [c.table for c in mod.TRIGGER_CHANGES] == ["chart_divisionals", "chart_vichara"]
    assert "ITEM 5 (K1, chart_vichara capture identity)" in mod.render_plan() and "RESERVED" not in mod.render_plan()
    assert "constituent_fact_ids" not in " ".join(h[1] + h[2] for p in mod.FUNCTION_PATCHES for h in p.hunks)


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


def test_the_contract_states_that_the_nine_arguments_are_not_a_natural_key():
    t = CONTRACT.read_text()
    sec = t[t.index("## 7. chart_vichara capture identity"):]
    assert "grain plus L1 source-fact provenance set" in sec and "NOT a natural key" in sec and "constituent_fact_ids" in sec
    assert "arguments only" in sec and "separate lane" in sec
    assert "NOT a natural key" in PLAN.read_text() or "NOT** a natural key" in PLAN.read_text()


def test_the_review_edits_are_in_the_plan_file():
    t = PLAN.read_text()
    body = t.split("\n---\n", 1)[1]
    summary = body[body.index("## 0."):body.index("## 1.")]
    # M1 / section 0 honesty: the capture path, not the whole rebuild; 1255 and 1219 named
    assert "does not by itself make the canonical chart's rebuild succeed" in summary and "migration 1255" in summary and "1219" in summary
    # L1: the transient grants named in section 0 and in the sentence
    assert "GRANT data_plane_l1_owner, amjis_app TO CURRENT_USER" in summary and "SAME transaction" in summary
    # L2: both tables take the exclusive lock; statement bound and measured values
    assert "`chart_divisionals` (index swap and trigger) and `chart_vichara` (trigger)" in summary and "capped at 100" in summary and "63 to 65" in summary
    # L3: production figures labelled production, rehearsal figures labelled rehearsal
    for fig in ("1,170 / 1,170 / 1,080 / 1,080 / 1,170", "9,194 / 9,205 / 9,063 / 8,998 / 9,204"):
        assert fig in summary and fig in body[body.index("### Items 2 and 3"):body.index("## 4.")]
    assert "in the rehearsal they failed" in summary and "rehearsal numbers, not production's" in body
    # step 0, 1219, freeze sequence, commit_state_unknown procedure, what the hash covers
    sec6 = body[body.index("## 6."):body.index("## 7.")]
    assert "Step 0" in sec6 and "1255" in sec6 and "FAIL" in sec6 and "rows 60 and 61" in sec6
    assert "## 8a. Operator procedure: `commit_state_unknown`" in body and "Partial" in body and "STOP, change nothing" in body
    assert "1255 merged and verified live \u2192 #2965/#2969/#2971 etc. into the integration \u2192 integration merged and deployed" in body
    assert "SS says freeze \u2192 plan hash + plan-file sha \u2192 SS dry-run approval \u2192 dry run through the gate \u2192 owner's D6 line \u2192 SS apply approval \u2192 apply \u2192 W1." in body
    assert "dasha_scope_cap" in body[body.index("## 10."):] and "panchanga_amrit_kaal" in body and "172 seeds plus 2" in body
    assert "What the plan hash covers, and what it does not" in body and "verify_before_apply.sql" in body


def test_the_executor_names_step_0_the_transient_grants_and_the_verification_files_in_the_hashed_plan_text(mod):
    plan = mod.render_plan()
    assert "STEP 0 prerequisite" in plan and "migration 1255" in plan and "brahma_yoga_catalog" in plan
    for tbl in mod.PREREQ_1255_BUILDER_TABLES:
        assert tbl in plan
    assert "GRANT data_plane_l1_owner TO CURRENT_USER and GRANT amjis_app TO CURRENT_USER" in plan and "SAME transaction" in plan
    import hashlib
    for n in mod.VERIFY_FILES:
        assert f"{n} sha256 {hashlib.sha256((EXEC_DIR / n).read_bytes()).hexdigest()}" in plan, n
