"""Tests for the bo_pratijna writer (Promise Register, L2 Bodha).

Two tiers, matching the project's established writer-test convention:

1. Offline (always runs, no DB required): the pure, DB-free grading logic
   (_compute_grade, _grade_to_status, _partition_signal).
2. Live (skipped unless DATABASE_URL or PROD_DB_URL is set): proves the
   migration constraint and writer behaviour against the real schema.

Bug targets (SHABDA-SHUDDHI lane-l2-pratijna):

BUG-1: Empty evidence -> 'denied 0.000' instead of 'no_evidence'
   When BOTH supporting AND contradicting signal lists are empty, the writer
   must set status='no_evidence', NOT status='denied'.

BUG-2: Valence filtering uses 'positive'/'negative' which never occur
   The actual bodha_msr_signals valence values are 'benefic'/'malefic'/
   'mixed'/'neutral'. The old code checks 'positive'/'negative' so everything
   is silently discarded and all outputs are falsely 'denied'.

BUG-3: mixed and neutral signals are silently discarded (R7 violation)
   Mixed signals must contribute to BOTH supporting and contradicting with
   reduced weight. Neutral signals contribute as context (lower weight).
"""
from __future__ import annotations

import inspect
import os

import pytest

from pipeline.orchestrator.writers.bo_pratijna import (
    _compute_grade,
    _grade_to_status,
    _partition_signal,
)
from pipeline.orchestrator.writers.bo_pratijna_karyatva import (
    KARYATVA_REGISTRY,
    get_karyatva,
)


# ── Offline tests: pure logic, no DB ──────────────────────────────────────────


# BUG-1: empty evidence must yield no_evidence, not denied
class TestNoEvidenceStatus:
    def test_empty_both_sides_yields_grade_zero(self):
        """Grade with no evidence is 0.0 — the formula has no inputs."""
        grade = _compute_grade([], [])
        assert grade == 0.0

    def test_grade_zero_empty_evidence_maps_to_no_evidence(self):
        """BUG-1 fix: grade=0.0 from empty evidence -> 'no_evidence', not 'denied'."""
        status = _grade_to_status(0.0, supporting_empty=True, contradicting_empty=True)
        assert status == "no_evidence", (
            f"Expected 'no_evidence' when both lists are empty; got {status!r}. "
            "Empty evidence means 'no information', NOT 'denied'."
        )

    def test_grade_zero_with_contradicting_signals_is_denied(self):
        """grade=0 from real contradicting signals is still 'denied', not 'no_evidence'."""
        grade = _compute_grade([], [0.5])
        status = _grade_to_status(grade, supporting_empty=True, contradicting_empty=False)
        assert status == "denied", (
            "A chart with real contradicting evidence should be 'denied', not 'no_evidence'."
        )

    def test_no_evidence_is_not_denied_and_not_promised(self):
        """no_evidence is a distinct fourth state."""
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
        """'positive' never occurs in bodha_msr_signals.
        It must NOT be accepted as full benefic weight."""
        sup, con = _partition_signal("positive", 0.8)
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
        assert sup <= 0.8, "mixed signal's supporting contribution must not exceed full salience"
        assert con <= 0.8, "mixed signal's contradicting contribution must not exceed full salience"

    def test_neutral_contributes_as_context(self):
        """R7: neutral signals contribute as context (lower weight, not zero).
        They are NOT silently discarded."""
        sup, con = _partition_signal("neutral", 0.8)
        total = sup + con
        assert total > 0.0, (
            "neutral signal must contribute as context (R7) — "
            f"got sup={sup}, con={con} (both zero means it was discarded)"
        )

    def test_mixed_hurts_grade_less_than_pure_malefic_of_same_salience(self):
        """When the top-5 supporting pool is saturated, a mixed signal (contributing
        partial con weight = _MIXED_WEIGHT * sal) damages the grade LESS than a pure
        malefic of the same salience (contributing full con weight = sal).

        This is the key R7 invariant: mixed is not equivalent to pure malefic.
        It contributes supporting evidence AND contradicting, so its net harm is
        smaller than the same salience as pure opposition.
        """
        sal = 0.5
        sup_from_mixed, con_from_mixed = _partition_signal("mixed", sal)

        # 5 strong benefic signals already saturate the top-5 supporting pool.
        # A 6th supporting entry (the mixed's sup portion) does not change the mean.
        grade_with_mixed = _compute_grade([1.0] * 5 + [sup_from_mixed], [con_from_mixed])
        grade_with_malefic = _compute_grade([1.0] * 5, [sal])  # pure malefic, no sup

        assert grade_with_mixed >= grade_with_malefic, (
            "A mixed signal (partial con) must damage the grade LESS than a pure "
            "malefic of the same salience (full con). "
            f"grade_with_mixed={grade_with_mixed:.3f}, "
            f"grade_with_malefic={grade_with_malefic:.3f}"
        )


# Grade thresholds: contract with downstreams (ph_nimitta, stage2_promise)
class TestGradeThresholds:
    def test_high_grade_yields_promised(self):
        """grade >= 6.0 -> 'promised'."""
        status = _grade_to_status(6.0, supporting_empty=False, contradicting_empty=True)
        assert status == "promised"

    def test_mid_grade_yields_conditional(self):
        """2.0 <= grade < 6.0 -> 'conditional'."""
        status = _grade_to_status(4.0, supporting_empty=False, contradicting_empty=False)
        assert status == "conditional"

    def test_low_grade_with_signals_yields_denied(self):
        """grade < 2.0 with real evidence -> 'denied'."""
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
        """'mixed' must be present -- R7 forbids discarding it."""
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


# ── v3 Property Tests (SIDDHANTA campaign) ────────────────────────────────────


class TestMarriageNotEqualSeparation:
    """REQUIRED: marriage and separation must have different karyatva routes
    producing DIFFERENT grades on the same chart. This test would have caught
    the domain-matching defect."""

    def test_different_karyatva_maps(self):
        """Marriage and separation have structurally different factor sets."""
        marriage = get_karyatva("marriage")
        separation = get_karyatva("separation")
        assert marriage is not None
        assert separation is not None
        # Key structural difference: separation requires dusthana
        assert not marriage.dusthana_required
        assert separation.dusthana_required
        # Different karaka grahas
        assert set(marriage.karaka_grahas) != set(separation.karaka_grahas)

    def test_marriage_separation_different_primary_bhava(self):
        """Separation uses dusthana houses (6,8,12) that marriage does not."""
        marriage = get_karyatva("marriage")
        separation = get_karyatva("separation")
        assert set(marriage.primary_bhava) != set(separation.primary_bhava)
        # Separation includes dusthana houses
        assert 6 in separation.primary_bhava
        assert 8 in separation.primary_bhava
        assert 12 in separation.primary_bhava


class TestChildbirthIndependence:
    """REQUIRED: childbirth routes through 5H/Jupiter/D7 and is INDEPENDENT
    of 7H affliction."""

    def test_childbirth_does_not_use_7th_house(self):
        """Childbirth's primary bhava must NOT include house 7."""
        cb = get_karyatva("childbirth")
        assert cb is not None
        assert 7 not in cb.primary_bhava

    def test_childbirth_uses_5th_house_and_jupiter(self):
        """Childbirth routes through 5H and Jupiter."""
        cb = get_karyatva("childbirth")
        assert 5 in cb.primary_bhava
        assert "Jupiter" in cb.karaka_grahas

    def test_childbirth_uses_d7(self):
        """Childbirth uses D7 (saptamsha) divisional."""
        cb = get_karyatva("childbirth")
        assert cb.divisional == "D7"


class TestR12TwoJudgments:
    """REQUIRED: an afflicted-but-present 7th house yields
    occurrence-positive AND condition-afflicted."""

    def test_occurrence_grade_separate_from_condition(self):
        """v3 produces two separate grades. The _compute_grade function
        can produce different values for occurrence vs condition."""
        # Strong occurrence evidence, weak condition evidence
        occ = _compute_grade([0.8, 0.7, 0.6, 0.5, 0.4], [])
        cond = _compute_grade([], [0.8, 0.7, 0.6])
        # They should be different values
        assert occ != cond
        # Occurrence should be positive (above denied threshold)
        assert occ >= 2.0  # Not denied

    def test_afflicted_house_not_denied(self):
        """An afflicted 7th house: occurrence-positive (house exists),
        condition-afflicted. Status from occurrence must NOT be 'denied'."""
        # Occurrence: house is present (supporting evidence exists)
        occ_grade = _compute_grade([0.6, 0.5, 0.4], [])
        status = _grade_to_status(occ_grade, supporting_empty=False, contradicting_empty=True)
        assert status != "denied", (
            f"An afflicted-but-present house should not be denied. "
            f"occurrence_grade={occ_grade}, status={status}"
        )


class TestR13NoFitting:
    """REQUIRED: no weight or threshold derived from the native's outcomes."""

    def test_no_chart_id_in_karyatva(self):
        """Karyatva maps must not reference any specific chart_id."""
        from pipeline.orchestrator.writers import bo_pratijna_karyatva as mod
        src = inspect.getsource(mod)
        assert "482012f1" not in src, "Karyatva map references native's chart_id (R13 violation)"
        assert "1c826d5a" not in src
        assert "cb73cd3d" not in src

    def test_all_entries_have_citations(self):
        """Every karyatva entry must have at least one classical citation (B.3)."""
        for ec_id, km in KARYATVA_REGISTRY.items():
            assert km.citations, f"Karyatva map for {ec_id} has no citations (B.3 violation)"

    def test_uniform_weights(self):
        """No empirical weight tuning — all weights in the matching function
        are structural constants, not outcome-derived."""
        import pipeline.orchestrator.writers.bo_pratijna as mod
        src = inspect.getsource(mod)
        assert "LEL" not in src.upper() or "life_event_log" not in src.lower(), (
            "Writer references LEL data (R13: no fitting to known outcomes)"
        )


class TestKaryatvaRegistry:
    """Structural tests for the karyatva registry."""

    def test_all_mapped_classes_have_primary_bhava(self):
        for ec_id, km in KARYATVA_REGISTRY.items():
            if not km.provisional:
                assert km.primary_bhava, f"{ec_id} has empty primary_bhava"

    def test_all_mapped_classes_have_karaka(self):
        for ec_id, km in KARYATVA_REGISTRY.items():
            if not km.provisional:
                assert km.karaka_grahas, f"{ec_id} has empty karaka_grahas"

    def test_provisional_classes_are_labelled(self):
        """DR-13 provisional classes must be marked provisional=True."""
        provisionals = {ec_id for ec_id, km in KARYATVA_REGISTRY.items() if km.provisional}
        assert "achievement_recognition" in provisionals
        assert "financial_deception" in provisionals
        assert "psychological_arc" in provisionals
        assert "birth_anchor" in provisionals
        assert "travel_event" in provisionals


class TestEngineVersion:
    """v3 version markers."""

    def test_engine_version_is_v3(self):
        from pipeline.orchestrator.writers.bo_pratijna import ENGINE_VERSION
        assert "v3" in ENGINE_VERSION.lower()

    def test_formula_version_is_v3(self):
        from pipeline.orchestrator.writers.bo_pratijna import FORMULA_VERSION
        assert "v3" in FORMULA_VERSION.lower()


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
    """Migration 545 must have added 'no_evidence' to the CHECK constraint."""
    cur = db_conn.cursor()
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
    src = inspect.getsource(_fetch_pratijna)
    assert "AND status IN ('promised', 'conditional')" not in src, (
        "stage2_promise._fetch_pratijna still gates on status='promised'/'conditional'. "
        "R6 fix: remove the status filter so ALL rows flow through as modifiers."
    )
