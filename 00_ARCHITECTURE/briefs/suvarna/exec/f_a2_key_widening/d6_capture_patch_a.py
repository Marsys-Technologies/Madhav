"""Patch A for public.l1_data_plane_capture_row() (migration 1035 lineage): pure text transformation, no database, no credential.

DRAFT, NEVER APPLIED. The combined D6 executor (d6_dataplane_capture_fa2_exec.py) imports this module; it is also what the tests
use to prove that the patched function differs from the live one ONLY by the hunks listed here (plus F-A2's one hunk).

WHAT PATCH A FIXES (found by a disposable-database rehearsal that drove the real writers through the real capture path as
data_plane_builder; see D6_DATAPLANE_CAPTURE_FA2_PLAN_v2_0.md): the typed fact projection of the L1 capture function cannot store
a chart_facts row that carries (a) no typed value at all, or (b) more than one of fact_value_num / fact_value_text /
fact_value_jsonb. Both are legitimate producer shapes, and both abort the capture (the fact snapshot table has a CHECK that a
'present' fact carries exactly one typed value), so the whole partition aborts.

THE THREE HUNKS (H3 has two edit sites; the F-A2 hunk is a fourth, owned by the F-A2 draft and composed in the executor):

  H1  declare `v_typed_col TEXT; v_companions TEXT[];` after `v_yoga_rule JSONB;`.
  H2  an all-null chart_facts row (fact_value_num, fact_value_text and fact_value_jsonb all NULL, a JSON null counts as NULL) whose
      missingness would be 'present' or 'zero' becomes 'floored' when verification_pass_status = 'floored', else 'unavailable'.
  H3  typed-value choice. Precedence num, then text, then jsonb: if more than one typed value is non-null keep exactly ONE column
      and NULL the others; when something was dropped, grain_jsonb of the fact snapshot gains
      {typed_value_column, companion_value_columns}. Nothing dropped: grain_jsonb is exactly what it was. The FULL row stays,
      unchanged, in l1_data_plane_row_snapshots.source_row_jsonb.

Each hunk is applied only if its old text occurs EXACTLY ONCE in the function being patched, and its new text is not already present.
"""
from __future__ import annotations

import difflib
import hashlib

# ---------------------------------------------------------------------------------------------------------------- H1
H1_OLD = "  v_yoga_rule JSONB;\nBEGIN"
H1_NEW = "  v_yoga_rule JSONB;\n  v_typed_col TEXT;\n  v_companions TEXT[];\nBEGIN"

# ---------------------------------------------------------------------------------------------------------------- H2
H2_OLD = """  v_epistemic := CASE
    WHEN v_asset = 'ga_ayurdaya' THEN 'restricted_scholarly'"""
H2_NEW = """  IF TG_TABLE_NAME = 'chart_facts' AND v_missingness IN ('present', 'zero')
     AND v_row->>'fact_value_num' IS NULL
     AND v_row->>'fact_value_text' IS NULL
     AND NULLIF(v_row->'fact_value_jsonb', 'null'::jsonb) IS NULL THEN
    v_missingness := CASE WHEN v_row->>'verification_pass_status' = 'floored'
                          THEN 'floored' ELSE 'unavailable' END;
  END IF;
  v_epistemic := CASE
    WHEN v_asset = 'ga_ayurdaya' THEN 'restricted_scholarly'"""

# ---------------------------------------------------------------------------------------------------------------- H3 (site a)
H3A_OLD = """      v_value_num := NULL; v_value_text := NULL; v_value_jsonb := NULL;
    END IF;
    INSERT INTO public.l1_data_plane_fact_snapshots ("""
H3A_NEW = """      v_value_num := NULL; v_value_text := NULL; v_value_jsonb := NULL;
    END IF;
    IF num_nonnulls(v_value_num, v_value_text, v_value_jsonb) > 1 THEN
      IF v_value_num IS NOT NULL THEN
        v_typed_col := 'fact_value_num';
        v_companions := ARRAY[]::TEXT[]
          || CASE WHEN v_value_text IS NOT NULL THEN ARRAY['fact_value_text'] ELSE ARRAY[]::TEXT[] END
          || CASE WHEN v_value_jsonb IS NOT NULL THEN ARRAY['fact_value_jsonb'] ELSE ARRAY[]::TEXT[] END;
        v_value_text := NULL; v_value_jsonb := NULL;
      ELSE
        v_typed_col := 'fact_value_text';
        v_companions := ARRAY['fact_value_jsonb'];
        v_value_jsonb := NULL;
      END IF;
    END IF;
    INSERT INTO public.l1_data_plane_fact_snapshots ("""

# ---------------------------------------------------------------------------------------------------------------- H3 (site b)
H3B_OLD = """      jsonb_build_object(
        'source_table', TG_TABLE_NAME,
        'row_identity', v_identity,
        'fact_category', COALESCE(v_row->>'fact_category', v_asset),
        'fact_subject', COALESCE(v_row->>'fact_subject', v_identity),
        'fact_key', COALESCE(v_row->>'fact_key', 'value')
      ),"""
H3B_NEW = """      jsonb_build_object(
        'source_table', TG_TABLE_NAME,
        'row_identity', v_identity,
        'fact_category', COALESCE(v_row->>'fact_category', v_asset),
        'fact_subject', COALESCE(v_row->>'fact_subject', v_identity),
        'fact_key', COALESCE(v_row->>'fact_key', 'value')
      ) || CASE WHEN v_companions IS NULL THEN '{}'::jsonb
                ELSE jsonb_build_object('typed_value_column', v_typed_col,
                                        'companion_value_columns', to_jsonb(v_companions)) END,"""

PATCH_A_HUNKS = (
    ("H1_declare_v_typed_col_v_companions", H1_OLD, H1_NEW),
    ("H2_all_null_row_is_floored_or_unavailable", H2_OLD, H2_NEW),
    ("H3a_typed_value_precedence_num_text_jsonb", H3A_OLD, H3A_NEW),
    ("H3b_grain_jsonb_records_kept_and_dropped_columns", H3B_OLD, H3B_NEW),
)


def apply_hunks(definition: str, hunks) -> str:
    """Replace each hunk's old text by its new text. Each old text must occur exactly once and its new text not at all."""
    out = definition
    for name, old, new in hunks:
        n = out.count(old)
        if n != 1:
            raise ValueError(f"hunk {name}: old text occurs {n} times (expected exactly 1)")
        if new in out:
            raise ValueError(f"hunk {name}: new text is already present (already patched?)")
        out = out.replace(old, new)
    return out


def patch_a(definition: str) -> str:
    return apply_hunks(definition, PATCH_A_HUNKS)


def unified_hunks(before: str, after: str) -> list[str]:
    """Zero-context unified diff of two function definitions, split into one string per hunk (header lines dropped)."""
    lines = list(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile="live", tofile="patched", n=0))
    hunks: list[list[str]] = []
    for ln in lines[2:]:
        if ln.startswith("@@"):
            hunks.append([])
        hunks[-1].append(ln if ln.endswith("\n") else ln + "\n")
    return ["".join(h) for h in hunks]


def diff_digest(before: str, after: str) -> str:
    """sha256 of the zero-context diff: the compact, plan-bound statement 'the patched function differs from the live one by exactly
    these hunks and nothing else'."""
    return hashlib.sha256("".join(unified_hunks(before, after)).encode("utf-8")).hexdigest()
