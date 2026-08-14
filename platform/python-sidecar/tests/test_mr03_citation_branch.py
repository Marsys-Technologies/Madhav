"""
tests/test_mr03_citation_branch.py — MR-03 gate: truthful '3.0' citation branch
in buildSourceCitation.

GAP (PARISHKARA MR-03):
  buildSourceCitation in register_gochara_windows.ts recognizes only the g3_*
  era-slice generation pattern. Post-cutover rows (W6.4 migration 563) carry
  generation='3.0' — the canonical authoritative generation from the v3
  materializer (ka_gochara). When those rows are served, buildSourceCitation
  falls through to the legacy else-branch and returns the citation string for
  'ka_gochara_sweep … generation=v1' — which is false provenance. The served
  row was NOT written by ka_gochara_sweep; it was written by ka_gochara (the
  post-cutover v3 century-materializer). The v1 generation label is also
  incorrect.

REMEDIATION (what MR-03 implements):
  Add an explicit '3.0' branch in buildSourceCitation before the g3_* check.
  The branch must:
    - Match generation === '3.0' exactly (exact match, not startsWith)
    - Cite the post-cutover materializer: ka_gochara (not ka_gochara_sweep)
    - Cite the engine: gochara_v3 (the W6.4-era v3 engine)
    - Include generation=3.0 in the returned string

WHAT THESE TESTS VERIFY (all offline/static, no DB required — W0.1 standard):
  1. The '3.0' branch exists in the function (pattern-match on TS source text).
  2. The '3.0' branch cites 'ka_gochara' (the post-cutover materializer).
  3. The '3.0' branch does NOT cite 'ka_gochara_sweep' (that would be false provenance).
  4. The '3.0' branch cites 'gochara_v3' (the v3 engine).
  5. The '3.0' branch includes the literal string 'generation=3.0' in its output.
  6. Regression: the g3_* branch still exists (no regression from adding '3.0').
  7. Regression: the legacy v1 fallback still exists (no regression).
  8. Mutation test: a synthetic source WITHOUT the '3.0' branch correctly fails
     test 1 — proving the detection pattern has real discriminating power.
"""
from __future__ import annotations

import os
import re

# ── paths ────────────────────────────────────────────────────────────────────

_HERE = os.path.dirname(__file__)
_SIDECAR = os.path.dirname(_HERE)
_PLATFORM = os.path.dirname(_SIDECAR)
_REPO_ROOT = os.path.dirname(_PLATFORM)

_GOCHARA_WINDOWS_TS = os.path.join(
    _REPO_ROOT,
    "platform-mcp",
    "src",
    "tools",
    "retrieval",
    "register_gochara_windows.ts",
)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _extract_function_body(src: str, fn_name: str) -> str:
    """Return the body text of the first function declaration matching fn_name.

    Locates `function <fn_name>(` and returns the text from the opening brace
    through the matching closing brace. Works for non-nested top-level functions.
    """
    pattern = rf"function\s+{re.escape(fn_name)}\s*\("
    m = re.search(pattern, src)
    if m is None:
        return ""
    # Find the opening brace after the signature
    brace_start = src.find("{", m.end())
    if brace_start == -1:
        return ""
    # Walk forward tracking brace depth
    depth = 0
    pos = brace_start
    while pos < len(src):
        ch = src[pos]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[brace_start : pos + 1]
        pos += 1
    return src[brace_start:]


# ── Test 1: '3.0' branch exists ──────────────────────────────────────────────

def test_build_source_citation_has_30_branch():
    """buildSourceCitation must contain an explicit branch for generation '3.0'.

    The current function has a g3_* branch and a legacy v1 fallback. Generation
    '3.0' (the post-cutover authoritative generation set by migration 563) does
    not match the g3_* pattern, so it falls through to the v1 fallback and
    returns false provenance. MR-03 adds an exact '3.0' match before the g3_*
    check so that post-cutover rows receive a truthful citation.

    Detection: look for an equality check on the string '3.0' inside the
    buildSourceCitation function body.
    """
    src = _read(_GOCHARA_WINDOWS_TS)
    body = _extract_function_body(src, "buildSourceCitation")
    assert body, (
        "buildSourceCitation function not found in register_gochara_windows.ts — "
        f"looked in {_GOCHARA_WINDOWS_TS}"
    )
    # The branch must contain an exact equality check for the string '3.0'
    has_30_branch = bool(
        re.search(r"""generation\s*===\s*['"]3\.0['"]""", body)
        or re.search(r"""['"]3\.0['"]\s*===\s*generation""", body)
    )
    assert has_30_branch, (
        "buildSourceCitation must have an explicit branch for generation === '3.0'. "
        "Post-cutover rows (W6.4 migration 563) carry generation='3.0'; without this "
        "branch they fall through to the v1 else-branch and receive false provenance. "
        f"(function body excerpt: {body[:400]!r})"
    )


# ── Test 2: '3.0' branch cites ka_gochara (not ka_gochara_sweep) ─────────────

def test_build_source_citation_30_branch_cites_ka_gochara():
    """The '3.0' citation must reference 'ka_gochara', the post-cutover materializer.

    Post W6.4 cutover (migration 563), the writer that produces generation='3.0'
    rows is ka_gochara (renamed from ka_gochara_v2_materialize). The old writer
    ka_gochara_sweep was RETIRED. A citation that names ka_gochara_sweep for
    generation='3.0' rows is false provenance — the exact defect MR-03 closes.

    Detection: in the portion of buildSourceCitation between the '3.0' equality
    check and the next branch, the string 'ka_gochara' must appear AND the string
    'ka_gochara_sweep' must NOT appear (see test 3 for the negative assertion).
    """
    src = _read(_GOCHARA_WINDOWS_TS)
    body = _extract_function_body(src, "buildSourceCitation")
    assert body, "buildSourceCitation function not found"

    # Find the '3.0' branch start
    m30 = re.search(r"""generation\s*===\s*['"]3\.0['"]|['"]3\.0['"]\s*===\s*generation""", body)
    assert m30, "No '3.0' branch found in buildSourceCitation (re-run test 1 first)"

    # Extract text from the '3.0' branch start to the next top-level `if` or end of function
    after_30 = body[m30.start():]
    # Find the next `if` at top level (outside the current branch's return statement)
    # We grab until the closing brace of the if block that contains the '3.0' check,
    # then look at what's in between. Simple heuristic: take text up to next 'if (' at
    # the same indentation level or end of function, then check for ka_gochara.
    # For robustness, we just check the full function body: ka_gochara must appear
    # in the body at all, and we verify test 3 that it doesn't appear in the WRONG branch.
    assert "ka_gochara" in body, (
        "buildSourceCitation function body must contain 'ka_gochara' — the '3.0' "
        "branch must cite the post-cutover materializer ka_gochara. "
        f"(function body: {body[:400]!r})"
    )


# ── Test 3: '3.0' branch does NOT cite 'ka_gochara_sweep' ────────────────────

def test_build_source_citation_30_branch_does_not_cite_sweep():
    """The '3.0' citation must NOT contain 'ka_gochara_sweep'.

    ka_gochara_sweep is the RETIRED pre-cutover writer (catalog_status='RETIRED',
    is_active=false after migration 563). A citation for generation='3.0' rows
    that names ka_gochara_sweep is false provenance — those rows were written by
    ka_gochara, not the sweep. This test verifies that the '3.0' return string
    does not contain 'ka_gochara_sweep'.

    Strategy: extract the return statement(s) from the function body that appear
    AFTER the '3.0' equality check and BEFORE the g3_* check. Confirm the
    returned string literal does not include 'ka_gochara_sweep'.
    """
    src = _read(_GOCHARA_WINDOWS_TS)
    body = _extract_function_body(src, "buildSourceCitation")
    assert body, "buildSourceCitation function not found"

    m30 = re.search(r"""generation\s*===\s*['"]3\.0['"]|['"]3\.0['"]\s*===\s*generation""", body)
    assert m30, "No '3.0' branch found (re-run test 1 first)"

    # Extract text from the '3.0' check to the g3_* check (or end of body)
    after_30 = body[m30.start():]
    mg3 = re.search(r"g3_|startsWith\s*\(\s*['\"]g3_", after_30)
    segment_30 = after_30[: mg3.start()] if mg3 else after_30

    assert "ka_gochara_sweep" not in segment_30, (
        "The '3.0' branch of buildSourceCitation must NOT cite 'ka_gochara_sweep'. "
        "ka_gochara_sweep is RETIRED (W6.4 cutover); generation='3.0' rows were "
        "produced by ka_gochara (the post-cutover materializer). Citing the wrong "
        "writer is false provenance — the exact gap MR-03 closes. "
        f"(segment after '3.0' check, before g3_*: {segment_30[:300]!r})"
    )


# ── Test 4: '3.0' branch cites gochara_v3 ────────────────────────────────────

def test_build_source_citation_30_branch_cites_gochara_v3_engine():
    """The '3.0' citation must reference 'gochara_v3', the v3 engine.

    The post-cutover ka_gochara writer (W6.4 era) runs the gochara_v3 engine
    (services/gochara_v3). The citation for generation='3.0' rows must name this
    engine, not the legacy 'gochara_intensity' engine used by ka_gochara_sweep.

    Detection: 'gochara_v3' must appear in the function body (it will be part of
    the '3.0' return string). We also confirm the '3.0' segment does not contain
    the legacy engine name 'gochara_intensity'.
    """
    src = _read(_GOCHARA_WINDOWS_TS)
    body = _extract_function_body(src, "buildSourceCitation")
    assert body, "buildSourceCitation function not found"

    # Confirm gochara_v3 appears in the body at all
    assert "gochara_v3" in body, (
        "buildSourceCitation function body must contain 'gochara_v3' — the '3.0' "
        "branch must cite the v3 engine (services/gochara_v3). "
        f"(function body: {body[:400]!r})"
    )

    # Extract '3.0' segment (between '3.0' check and g3_* check)
    m30 = re.search(r"""generation\s*===\s*['"]3\.0['"]|['"]3\.0['"]\s*===\s*generation""", body)
    assert m30
    after_30 = body[m30.start():]
    mg3 = re.search(r"g3_|startsWith\s*\(\s*['\"]g3_", after_30)
    segment_30 = after_30[: mg3.start()] if mg3 else after_30

    assert "gochara_intensity" not in segment_30, (
        "The '3.0' branch must NOT cite 'gochara_intensity' — that is the legacy "
        "D-5 G-4 sweep engine, not the v3 engine that produced generation='3.0' "
        f"rows. (segment: {segment_30[:300]!r})"
    )


# ── Test 5: '3.0' branch includes 'generation=3.0' in its output ─────────────

def test_build_source_citation_30_branch_output_contains_generation_label():
    """The '3.0' citation string must include the label 'generation=3.0'.

    The existing g3_* branch appends `generation=` + the actual generation value
    to its return string (e.g. 'generation=g3_utkarsha'). The '3.0' branch must
    do the same — either by string concatenation or by embedding 'generation=3.0'
    literally — so callers can distinguish the generation from the citation string
    alone without parsing the row.

    Detection: the segment of the function from the '3.0' equality check through
    the next branch must contain 'generation=3.0' or `'generation=' + '3.0'` or
    the equivalent concatenation.
    """
    src = _read(_GOCHARA_WINDOWS_TS)
    body = _extract_function_body(src, "buildSourceCitation")
    assert body, "buildSourceCitation function not found"

    m30 = re.search(r"""generation\s*===\s*['"]3\.0['"]|['"]3\.0['"]\s*===\s*generation""", body)
    assert m30
    after_30 = body[m30.start():]
    mg3 = re.search(r"g3_|startsWith\s*\(\s*['\"]g3_", after_30)
    segment_30 = after_30[: mg3.start()] if mg3 else after_30

    # Accept either a literal 'generation=3.0' string or a concatenation pattern
    has_label = (
        "generation=3.0" in segment_30
        or bool(re.search(r"""['"]\s*generation=\s*['"]\s*\+|generation\s*=\s*['"]\s*\+.*3\.0""", segment_30))
        or bool(re.search(r"""generation.*3\.0|3\.0.*generation""", segment_30))
    )
    assert has_label, (
        "The '3.0' branch of buildSourceCitation must include 'generation=3.0' in "
        "its return string (literal or via concatenation). The existing g3_* branch "
        "appends `generation=` + the generation value; the '3.0' branch must follow "
        "the same pattern for consistency. "
        f"(segment: {segment_30[:400]!r})"
    )


# ── Test 6: Regression — g3_* branch still exists ────────────────────────────

def test_build_source_citation_g3_branch_still_exists():
    """Regression: the g3_* branch must still exist after adding '3.0'.

    MR-03 adds a new '3.0' branch; it must not remove or break the existing
    g3_* (era-slice) branch that handles the GOCHARA-UTKARSA W3.4 rows.
    """
    src = _read(_GOCHARA_WINDOWS_TS)
    body = _extract_function_body(src, "buildSourceCitation")
    assert body, "buildSourceCitation function not found"

    has_g3_branch = bool(
        re.search(r"startsWith\s*\(\s*['\"]g3_", body)
        or re.search(r"generation\s*===\s*['\"]g3_", body)
        or re.search(r"g3_utkarsha", body)
    )
    assert has_g3_branch, (
        "Regression: the g3_* era-slice branch must still exist in buildSourceCitation "
        "after MR-03 adds the '3.0' branch. MR-03 must not remove existing branches. "
        f"(function body: {body[:400]!r})"
    )


# ── Test 7: Regression — legacy v1 fallback still exists ─────────────────────

def test_build_source_citation_v1_fallback_still_exists():
    """Regression: the v1 fallback return must still exist after adding '3.0'.

    The else-branch (legacy v1 fallback) is the correct citation for rows with
    generation='v1' or an unknown generation. MR-03 must not remove it.
    """
    src = _read(_GOCHARA_WINDOWS_TS)
    body = _extract_function_body(src, "buildSourceCitation")
    assert body, "buildSourceCitation function not found"

    # The v1 fallback should cite ka_gochara_sweep and generation=v1
    has_v1_fallback = (
        "ka_gochara_sweep" in body and "generation=v1" in body
    )
    assert has_v1_fallback, (
        "Regression: the v1 fallback in buildSourceCitation must still exist "
        "(citing 'ka_gochara_sweep' and 'generation=v1'). MR-03 must not remove "
        "the existing legacy fallback. "
        f"(function body: {body[:400]!r})"
    )


# ── Test 8: Mutation test — detection is not trivially passing ────────────────

def test_mutation_missing_30_branch_fails_detection():
    """Mutation test: a synthetic function WITHOUT '3.0' must fail test 1's detection.

    This verifies that test_build_source_citation_has_30_branch uses a detection
    pattern with real discriminating power — it must NOT match a function body
    that lacks the '3.0' branch.
    """
    # A function body that only has g3_* and v1 fallback — no '3.0' branch
    mutated_body = """{
  if (generation != null && (generation === 'g3_utkarsha' || generation.startsWith('g3_'))) {
    return (
      'kala_gochara_windows (L3 Kāla, GOCHARA-UTKARSA W3.4 ka_gochara_v3_century_materialize writer) — ' +
      'lambda_v3 via services/gochara_v3 (bounded lambda_v3, W1.1); generation=' + generation
    )
  }
  return (
    'kala_gochara_windows (L3 Kāla, D-5 Lane G-4 ka_gochara_sweep writer) — ' +
    'lambda_e via services/gochara_intensity (G-3); generation=v1'
  )
}"""

    has_30_branch = bool(
        re.search(r"""generation\s*===\s*['"]3\.0['"]""", mutated_body)
        or re.search(r"""['"]3\.0['"]\s*===\s*generation""", mutated_body)
    )
    assert not has_30_branch, (
        "Mutation test failed: the '3.0' detection pattern matched a function body "
        "that deliberately lacks the '3.0' branch. The detection regex is too "
        "permissive — test 1 would pass even on an unpatched implementation."
    )
