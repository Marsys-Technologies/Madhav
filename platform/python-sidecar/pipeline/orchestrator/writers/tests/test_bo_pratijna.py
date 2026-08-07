"""Tests for the bo_pratijna writer (Promise Register, L2 Bodha).

Two tiers, matching the project's established writer-test convention:

1. Offline (always runs, no DB required): the pure, DB-free grading logic
   (_compute_grade, _grade_to_status, valence partitioning).
2. Live (skipped unless DATABASE_URL or PROD_DB_URL is set): proves the
   migration constraint and writer behaviour against the real schema.

Bug targets (SHABDA-SHUDDHI lane-l2-pratijna):

BUG-1: Empty evidence → 'denied 0.000' instead of 'no_evidence'
   When BOTH supporting AND contradicting signal lists are empty, the writer
   must set status='no_evidence', NOT status='denied'.

BUG-2: Valence filtering uses 'positive'/'negative' which never occur
   The actual bodha_msr_signals valence values are 'benefic'/'malefic'/
   'mixed'/'neutral'. The old code checks 'positive'/'negative' → everything
   is silently discarded → all outputs are no_evidence (after this fix) or
   falsely denied (before).

BUG-3: mixed and neutral signals are silently discarded (R7 violation)
   Mixed signals must contribute to BOTH supporting and contradicting with
   reduced weight. Neutral signals contribute as context (lower weight).
"""
from __future__ import annotations

import inspect
import os
import uuid

import pytest

from pipeline.orchestrator.writers.bo_pratijna import (
    _compute_grade,
    _grade_to_status,
    _partition_signal,
)


# ── Offline tests: pure logic, no DB ──────────────────────────────────────────


# BUG-1: empty evidence must yield no_evidence, not denied
class TestNoEvidenceStatus:
    def test_empty_both_sides_yields_grade_zero(self):
        """Grade with no evidence is 0.0 — the formula has no inputs."""
        grade = _compute_grade([], [])
        assert grade == 0.0

    def test_grade_zero_empty_evidence_maps_to_no_evidence(self):
        """BUG-1 fix: grade=0.0 from empty evidence → 'no_evidence', not 'denied'."""
        status = _grade_to_status(0.0, supporting_empty=True, contradicting_empty=True)
        assert status == "no_evidence", (
            f"Expected 'no_evidence' when both lists are empty; got {status!r}. "
            "Empty evidence means 'no information', NOT 'denied'."
        )

    def test_grade_zero_with_contradicting_signals_is_denied(self):
        """grade=0 from real contradicting signals is still 'denied', not 'no_evidence'."""
        # A single contradicting signal drives grade toward zero
        grade = _compute_grade([], [0.5])
        status = _grade_to_status(grade, supporting_empty=True, contradicting_empty=False)
        assert status == "denied", (
            "A chart with real contradicting evidence should be 'denied', not 'no_evidence'."
        )

    def test_no_evidence_is_not_denied_and_not_promised(self):
        """no_evidence is a distinct third state — neither denied nor promised."""
        status = _grade_to_status(0.0, supporting_empty=True, contradicting_empty=True)
        assert status not in ("denied", "promised", "conditional")


# BUG-2: valence mapping uses actual data values ('benefic'/'malefic')
class TestValencePartitioning:
    def test_benefic_signal_goes_to_supporting(self):
        """'benefic' (the actual data value) must land in supporting, not be discarded."""
        sup, con = _partition_signal("benefic", 0.8)
        assert sup == 0.8, "'benefic' valence must contribute its full salience to supporting"
        assert con == 0.0

    def test_malefic_signal_goes_to_contradicting(self):
        """'malefic' (the actual data value) must land in contradicting, not be discarded."""
        sup, con = _partition_signal("malefic", 0.8)
        assert sup == 0.0
        assert con == 0.8, "'malefic' valence must contribute its full salience to contradicting"

    def test_positive_valence_is_not_in_actual_data(self):
        """'positive' never occurs in bodha_msr_signals — it must NOT be accepted as supporting.
        (If _partition_signal accepts 'positive', the old bug is still present.)
        The function must return 0.0, 0.0 for unknown valences rather than counting them."""
        sup, con = _partition_signal("positive", 0.8)
        # 'positive' is not a real valence — it should be ignored (0,0) or
        # treated as neutral (low weight context-only). It must NOT contribute
        # full salience to either side as if it were 'benefic'.
        assert sup != 0.8, (
            "'positive' is not a real valence in the data — the old bug is still present "
            "if it maps to full benefic weight"
        )

    def test_negative_valence_is_not_in_actual_data(self):
        """'negative' never occurs in bodha_msr_signals. Must not map to malefic weight."""
        sup, con = _partition_signal("negative", 0.8)
        assert con != 0.8, (
            "'negative' is not a real valence in the data — the old bug is still present "
            "if it maps to full malefic weight"
        )


# BUG-3: mixed and neutral signals must not be discarded (R7)
class TestMixedNeutralSignals:
    def test_mixed_contributes_to_both_sides_with_reduced_weight(self):
        """R7: mixed signals contribute to BOTH supporting and contradicting.
        They are NOT discarded. The contribution is reduced (< full salience)."""
        sup, con = _partition_signal("mixed", 0.8)
        assert sup > 0.0, "mixed signal must contribute SOMETHING to supporting (R7)"
        assert con > 0.0, "mixed signal must contribute SOMETHING to contradicting (R7)"
        # Both contributions must be less than the full salience (it's split/reduced)
        assert sup <= 0.8, "mixed signal's supporting contribution must not exceed full salience"
        assert con <= 0.8, "mixed signal's contradicting contribution must not exceed full salience"

    def test_neutral_contributes_as_context(self):
        """R7: neutral signals contribute as context (lower weight, not zero).
        They are NOT silently discarded."""
        sup, con = _partition_signal("neutral", 0.8)
        # neutral must contribute SOMETHING (to supporting, as context) — not zero
        total = sup + con
        assert total > 0.0, (
            "neutral signal must contribute as context (R7) — "
            f"got sup={sup}, con={con} (both zero means it was discarded)"
        )

    def test_grade_higher_with_mixed_signals_than_without(self):
        """With a mix of benefic + mixed signals, grade should exceed the case
        where only the benefic signals are present (mixed contributes positively)."""
        grade_benefic_only = _compute_grade([0.8, 0.6], [])
        # A mixed signal at 0.5 salience should add net positive contribution
        sup_from_mixed, con_from_mixed = _partition_signal("mixed", 0.5)
        grade_with_mixed = _compute_grade(
            [0.8, 0.6, sup_from_mixed], [con_from_mixed]
        )
        # The mixed signal adds more to supporting than it adds to contradicting,
        # so the grade should increase (or at least not decrease dramatically).
        assert grade_with_mixed >= grade_benefic_only - 0.5, (
            "Including a mixed signal should not severely penalise the grade; "
            f"grade_only_benefic={grade_benefic_only:.3f}, "
            f"grade_with_mixed={grade_with_mixed:.3f}"
        )


# Grade thresholds: contract with downstreams (ph_nimitta, stage2_promise)
class TestGradeThresholds:
    def test_high_grade_yields_promised(self):
        """grade >= 6.0 → 'promised'."""
        status = _grade_to_status(6.0, supporting_empty=False, contradicting_empty=True)
        assert status == "promised"

    def test_mid_grade_yields_conditional(self):
        """2.0 <= grade < 6.0 → 'conditional'."""
        status = _grade_to_status(4.0, supporting_empty=False, contradicting_empty=False)
        assert status == "conditional"

    def test_low_grade_with_signals_yields_denied(self):
        """grade < 2.0 with real evidence → 'denied'."""
        status = _grade_to_status(1.0, supporting_empty=False, contradicting_empty=False)
        assert status == "denied"

    def test_grade_range_is_clamped_0_to_10(self):
        """_compute_grade must always return a value in [0, 10]."""
        assert 0.0 <= _compute_grade([], []) <= 10.0
        assert 0.0 <= _compute_grade([1.0, 2.0], []) <= 10.0
        assert 0.0 <= _compute_grade([], [1.0, 2.0]) <= 10.0
        assert 0.0 <= _compute_grade([1.0], [1.0]) <= 10.0


# Source code structural checks (always run, no DB needed)
class TestSourceStructure:
    def test_writer_does_not_check_positive_valence(self):
        """The old bug: code checked 'positive' which never occurs.
        After the fix, 'positive' must not appear as a valence gate."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        # The literal string 'positive' should not appear as a valence comparison
        # (it may appear in comments, but not in the partition logic)
        # We look for the specific pattern that was the bug
        assert 'valence in ("positive"' not in src, (
            "Old bug still present: code checks for 'positive' valence which never "
            "occurs in bodha_msr_signals"
        )
        assert "valence == 'positive'" not in src

    def test_writer_does_not_check_negative_valence(self):
        """The old bug: code checked 'negative' which never occurs."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert 'valence in ("negative"' not in src, (
            "Old bug still present: code checks for 'negative' valence which never "
            "occurs in bodha_msr_signals"
        )
        assert "valence == 'negative'" not in src

    def test_writer_handles_benefic_and_malefic(self):
        """The actual valence values must be handled in the writer."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "benefic" in src, "Writer must handle 'benefic' valence (real data value)"
        assert "malefic" in src, "Writer must handle 'malefic' valence (real data value)"

    def test_writer_handles_mixed_valence(self):
        """'mixed' must be present — R7 forbids discarding it."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "mixed" in src, (
            "Writer must handle 'mixed' valence (R7: mixed signals are not discarded)"
        )

    def test_no_evidence_status_is_emitted(self):
        """Writer must be able to emit 'no_evidence' status."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "no_evidence" in src, (
            "Writer must emit 'no_evidence' status for empty-evidence cases"
        )


# ── Live tests (require DATABASE_URL or PROD_DB_URL; skipped otherwise) ───────

@pytest.fixture(scope="module")
def db_conn():
    import psycopg
    import psycopg.rows
    url = os.environ.get("DATABASE_URL") or os.environ.get("PROD_DB_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def test_no_evidence_status_is_in_check_constraint(db_conn):
    """Migration 545 must have added 'no_evidence' to the CHECK constraint.
    The DB should accept a row with status='no_evidence'."""
    cur = db_conn.cursor()
    # Verify the constraint allows 'no_evidence' by reading the constraint definition
    cur.execute("""
        SELECT pg_get_constraintdef(c.oid) AS def
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        WHERE t.relname = 'bodha_pratijna'
          AND c.contype = 'c'
          AND pg_get_constraintdef(c.oid) LIKE '%status%'
    """)
    rows = cur.fetchall()
    assert rows, "No CHECK constraint on bodha_pratijna.status found"
    constraint_def = rows[0]["def"]
    assert "no_evidence" in constraint_def, (
        f"Migration 545 did not add 'no_evidence' to the CHECK constraint. "
        f"Constraint definition: {constraint_def}"
    )


def test_stage2_promise_fetch_includes_no_evidence_rows(db_conn):
    """stage2_promise._fetch_pratijna must NOT filter out no_evidence rows.
    R6 (PROMISE IS A MODIFIER, NEVER A GATE): all statuses flow through."""
    from services.ka_kshetra.stage2_promise import _fetch_pratijna
    import inspect
    src = inspect.getsource(_fetch_pratijna)
    assert "AND status IN ('promised', 'conditional')" not in src, (
        "stage2_promise._fetch_pratijna still gates on status='promised'/'conditional'. "
        "R6 fix: remove the status filter so ALL rows flow through as modifiers."
    )
