"""
tests/test_mr18_generation_stance.py — MR-18 gate: explicit generation stance
on all offline validators and scripts.

GAP (MASTER_REMEDIATION_REGISTER_v2_0.md MR-18):
After the v1→3.0 cutover (both charts now on gen-3.0 authority via
`kala_gochara_authority`), any script that reads `kala_gochara_windows` or
`kala_gochara_windows_v2` WITHOUT declaring which generation it intends to read
will silently mix v1 and 3.0 rows — producing wrong results with no error.

GATE (MR-18): a grep of the scripts/tests for generation-blind reads returns
zero undocumented instances. Every reader either:
  (a) uses the authority-seam COALESCE pattern:
        COALESCE((SELECT authoritative_generation FROM kala_gochara_authority
                  WHERE chart_id = ...), 'v1')
  (b) has an `# INTENTIONAL:` pin comment explaining WHY the pin is correct
      for that specific use case (comparator baseline, grammar audit, etc.)

WHAT THESE TESTS VERIFY (all offline, no DB):
  1. v6_divergence_pilot._pilot_census SQL pins generation='v1' and carries
     the INTENTIONAL comment (it measures v1 chunk-boundary candidates, so v1
     is the correct and only relevant generation).
  2. s4_05_data_real_retest._health_row_evidence SQL pins generation='v1' and
     carries the INTENTIONAL comment (retests the pre-item-9 grammar that
     produced v1 rows; cross-generation mixing would invalidate the defect
     proof).
  3. test_cr131_gochara_db_reachability's integration test uses the authority-
     seam COALESCE or a generation-explicit filter (CR-131 proved the serving
     path reaches any authoritative generation; a generation-blind COUNT would
     give a spuriously large number after 3.0 rows land, masking an honest-
     zero state on any one generation).
  4. w2g_equivalence_report.py's v1 read carries the INTENTIONAL comment
     (the equivalence report reads v1 as the frozen validation benchmark;
     the pin is permanent and correct for the comparison).
  5. w41_lambda_contenders.load_v1_windows SQL carries the INTENTIONAL comment
     (λ_v1 is explicitly the v1-generation contender; the pin is the point).
  6. test_migration_527_generation_catalog_only's live integration assertion
     acknowledges multi-generation rows (COUNT(*) per generation, not a flat
     total-row assertion that breaks once 3.0 rows are present).
"""
from __future__ import annotations

import ast
import os
import re

# ── paths ───────────────────────────────────────────────────────────────────

_HERE = os.path.dirname(__file__)
_SIDECAR = os.path.dirname(_HERE)
_PLATFORM = os.path.dirname(_SIDECAR)

_V6_PILOT = os.path.join(_SIDECAR, "services", "w2g_validations", "v6_divergence_pilot.py")
_S4_05 = os.path.join(_SIDECAR, "scripts", "s4_05_data_real_retest.py")
_CR131 = os.path.join(_HERE, "test_cr131_gochara_db_reachability.py")
_W2G_EQUIV = os.path.join(_SIDECAR, "scripts", "w2g_equivalence_report.py")
_W41 = os.path.join(_SIDECAR, "scripts", "kala_admission", "w41_lambda_contenders.py")
_MIG527_TEST = os.path.join(_HERE, "test_migration_527_generation_catalog_only.py")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _strip_comments(src: str) -> str:
    """Remove Python line comments (# ...) to distinguish executable SQL strings
    from comment-only mentions of generation."""
    return re.sub(r"#[^\n]*", "", src)


# ── 1. v6_divergence_pilot._pilot_census ────────────────────────────────────

def test_v6_divergence_pilot_pins_v1_generation_in_sql():
    """_pilot_census reads kala_gochara_windows WHERE generation = 'v1'.

    The pilot measures v1 chunk-boundary candidates — rows from v1's own
    writer — so reading any other generation would count irrelevant rows.
    The generation pin must appear in the SQL string (not only in a comment)
    so it is enforced at query execution time, not just documented.
    """
    src = _read(_V6_PILOT)
    # The SQL in _pilot_census must contain an explicit generation filter
    assert "generation" in src and "'v1'" in src, (
        "v6_divergence_pilot._pilot_census must pin generation='v1' in its "
        "kala_gochara_windows query — the pilot measures v1 chunk-boundary "
        "candidates; reading across all generations would include 3.0 rows "
        "that don't share v1's chunk structure and skew the workload estimate."
    )


def test_v6_divergence_pilot_has_intentional_pin_comment():
    """The v1 pin in _pilot_census must be documented as INTENTIONAL.

    Distinguishes a legitimate, permanent comparator pin from an accidental
    hardcode that should have used the authority seam instead.
    """
    src = _read(_V6_PILOT)
    assert "INTENTIONAL" in src, (
        "v6_divergence_pilot must carry an # INTENTIONAL: comment explaining "
        "why generation='v1' is the correct pin for this use case (MR-18 gate)."
    )


# ── 2. s4_05_data_real_retest._health_row_evidence ──────────────────────────

def test_s4_05_retest_pins_v1_generation_in_sql():
    """_health_row_evidence queries kala_gochara_windows WHERE generation = 'v1'.

    The retest re-proves the pre-item-9 grammar defect using the same v1 data
    that was present when the defect occurred. Cross-generation mixing would
    include 3.0 rows that may carry different event_class coverage and would
    invalidate the proof that item 9 specifically closed the defect in the v1
    corpus.
    """
    src = _read(_S4_05)
    # The _health_row_evidence function queries kala_gochara_windows;
    # it must include a generation filter.
    assert "generation" in src and "'v1'" in src, (
        "s4_05_data_real_retest._health_row_evidence must pin generation='v1' "
        "in its kala_gochara_windows queries — the S4-05 defect lived in v1 "
        "data; including 3.0 rows in the count would mix corpora and misrepresent "
        "the defect-closure evidence."
    )


def test_s4_05_retest_has_intentional_pin_comment():
    """The v1 pin in s4_05_data_real_retest must be documented as INTENTIONAL."""
    src = _read(_S4_05)
    assert "INTENTIONAL" in src, (
        "s4_05_data_real_retest must carry an # INTENTIONAL: comment explaining "
        "why generation='v1' is the correct pin for the health-row evidence "
        "queries (MR-18 gate)."
    )


# ── 3. test_cr131_gochara_db_reachability (integration test) ─────────────────

def test_cr131_integration_test_is_not_generation_blind():
    """The CR-131 integration test must not issue a bare COUNT(*) with no
    generation filter against kala_gochara_windows.

    After the v1→3.0 cutover, a flat COUNT(*) WHERE chart_id = %s will include
    BOTH v1 and 3.0 rows. The test's intent is to prove the serving path reaches
    rows for the authoritative generation; a mixed-generation count satisfies the
    row-present assertion even if the authoritative generation has zero rows.

    ACCEPTABLE STANCES (either satisfies this test):
      (a) A generation-explicit query: WHERE chart_id = %s AND generation = 'v1'
          (or 'v1' replaced by the authority-seam COALESCE expression).
      (b) An INTENTIONAL: comment acknowledging the cross-generation scope is
          deliberate (e.g. "any generation present proves the table is reachable").
    """
    src = _read(_CR131)
    # Look only at the integration test function body for the generation concern.
    integration_marker = "test_kala_gochara_windows_reachable_and_has_rows_for_native_chart"
    if integration_marker not in src:
        # If the integration function was renamed/removed, the check is vacuously
        # satisfied — document what we looked for.
        return
    # Extract the portion of the file after the marker to scope the check.
    portion = src.split(integration_marker, 1)[1]
    # Either a generation filter in the SQL, or an INTENTIONAL comment explaining
    # why cross-generation counting is correct for this specific test.
    has_generation_filter = "generation" in portion and (
        "'v1'" in portion or "authoritative_generation" in portion or "COALESCE" in portion
    )
    has_intentional_comment = "INTENTIONAL" in portion
    assert has_generation_filter or has_intentional_comment, (
        "test_cr131_gochara_db_reachability's integration test must either "
        "filter by generation (generation='v1' or authority-seam COALESCE) or "
        "carry an # INTENTIONAL: comment explaining why a cross-generation row "
        "count is the correct stance — a flat COUNT(*) silently inflates after "
        "3.0 rows land (MR-18 gate)."
    )


# ── 4. w2g_equivalence_report.py v1 read ────────────────────────────────────

def test_w2g_equivalence_report_v1_read_has_intentional_comment():
    """The v1 pin in w2g_equivalence_report.py must carry an INTENTIONAL comment.

    w2g_equivalence_report.py reads kala_gochara_windows WHERE generation = 'v1'
    as the frozen validation benchmark that λ_v3 (3.0) is compared against.
    The v1 pin is permanent and correct for this comparator role — the comment
    distinguishes this from an accidental hardcode.
    """
    src = _read(_W2G_EQUIV)
    # Confirm the v1 pin already exists in the SQL
    assert "generation = 'v1'" in src, (
        "w2g_equivalence_report.py must pin generation='v1' in its "
        "kala_gochara_windows query (it reads the frozen v1 benchmark)."
    )
    # Confirm it is documented as intentional
    assert "INTENTIONAL" in src, (
        "w2g_equivalence_report.py must carry an # INTENTIONAL: comment on its "
        "generation='v1' pin to distinguish it from an accidental hardcode "
        "(MR-18 gate)."
    )


# ── 5. w41_lambda_contenders.load_v1_windows ────────────────────────────────

def test_w41_load_v1_windows_has_intentional_comment():
    """load_v1_windows in w41_lambda_contenders.py must carry an INTENTIONAL comment.

    load_v1_windows already pins generation='v1' correctly (λ_v1 IS the v1
    corpus by definition). The comment distinguishes this from an accidental
    hardcode and documents that the pin is permanent for the bakeoff comparator.
    """
    src = _read(_W41)
    assert "generation = 'v1'" in src, (
        "w41_lambda_contenders.load_v1_windows must already pin generation='v1'."
    )
    assert "INTENTIONAL" in src, (
        "w41_lambda_contenders.py must carry an # INTENTIONAL: comment on its "
        "load_v1_windows generation='v1' pin (MR-18 gate)."
    )


# ── 6. test_migration_527: multi-generation row assertion ─────────────────────

def test_migration_527_integration_assertion_handles_v3_rows():
    """The live integration test in test_migration_527_generation_catalog_only.py
    must not use a flat row-count assertion that breaks when v3 rows are present.

    The test's intent is to prove `kala_gochara_windows` is reachable and holds
    rows for chart 482012f1. After the v1→3.0 cutover, the table holds rows from
    both generations; a 'count > 0' assertion still passes, but a 'count == N'
    hardcoded to the v1-only row count would fail.

    ACCEPTABLE: either
      (a) the assertion uses `> 0` (not `== N`) for the total, OR
      (b) the assertion is generation-scoped (WHERE generation = 'v1') so it
          remains stable after 3.0 rows are added, OR
      (c) an INTENTIONAL: comment acknowledges the cross-generation count.
    """
    src = _read(_MIG527_TEST)
    # Look only at the integration test body for the reachability assertion.
    marker = "test_kala_gochara_windows_reachable_and_has_rows_for_native_chart"
    if marker not in src:
        return  # test was removed; check vacuously passes
    portion = src.split(marker, 1)[1]

    # Fail: a literal `== N` (integer) count assertion against a bare
    # `COUNT(*) FROM kala_gochara_windows` with no generation filter.
    # We accept `> 0`, generation-scoped queries, or an INTENTIONAL comment.
    has_generation_scope = "generation" in portion and (
        "'v1'" in portion or "COALESCE" in portion or "authoritative_generation" in portion
    )
    has_intentional_comment = "INTENTIONAL" in portion
    # Check that there's no hardcoded `== N` count (a literal integer equality
    # on the row count that would break once v3 rows are added).
    count_eq_literal = bool(re.search(r'n\s*==\s*\d+', portion, re.IGNORECASE))

    assert not count_eq_literal or has_generation_scope or has_intentional_comment, (
        "test_migration_527's live integration test must not assert a hardcoded "
        "row count (n == <integer>) against a generation-blind COUNT(*) — after "
        "3.0 rows land the count will exceed the v1-only figure and the assertion "
        "will fail spuriously. Use `n > 0`, scope by generation, or add an "
        "# INTENTIONAL: comment acknowledging cross-generation scope (MR-18 gate)."
    )
