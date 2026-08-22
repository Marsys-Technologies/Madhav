"""tests/l2/test_b08_ranker.py — EKV B-08 golden tests.

B-08 lane: domain-affinity weighting + servable=False for abstention markers
+ plateau test (F-114/F-131).

These tests are written FIRST (TDD) and must FAIL before the implementation
lands in bodha_writers/formulas.py and bo_laksana.py.
"""
from __future__ import annotations


def test_abstention_marker_signal_gets_zero_salience():
    """Signals whose summary text matches an abstention marker must have computed_salience=0.0."""
    from bodha_writers.formulas import SalienceInputsV2, salience_formula_v2

    # Standard inputs that would normally produce non-zero salience
    inp = SalienceInputsV2(
        orb_tightness=1.0,
        shadbala_norm=1.5,
        dignity_score=0.7,
        house_number=7,
        ashtakavarga_bindus=5,
        verification_pass_status="single",
        class_prior=1.0,
        varga_id="D1",
        is_abstention_marker=True,  # THE KEY FLAG
    )
    result = salience_formula_v2(inp)
    assert result["computed_salience"] == 0.0


def test_domain_count_penalty_reduces_salience_for_broad_signals():
    """A 7-domain signal gets lower salience than a 1-domain signal with identical other inputs."""
    from bodha_writers.formulas import SalienceInputsV2, salience_formula_v2

    base = dict(
        orb_tightness=1.0,
        shadbala_norm=1.5,
        dignity_score=0.7,
        house_number=7,
        ashtakavarga_bindus=5,
        verification_pass_status="single",
        class_prior=1.0,
        varga_id="D1",
    )
    specific = salience_formula_v2(SalienceInputsV2(**base, domain_count=1))
    broad = salience_formula_v2(SalienceInputsV2(**base, domain_count=7))
    assert specific["computed_salience"] > broad["computed_salience"]


def test_ten_signals_with_varied_domain_counts_have_distinct_salience():
    """Build 10 signals with the same formula inputs but varying domain_count 1..10.
    All must have distinct computed_salience."""
    from bodha_writers.formulas import SalienceInputsV2, salience_formula_v2

    base = dict(
        orb_tightness=1.0,
        shadbala_norm=1.5,
        dignity_score=0.7,
        house_number=7,
        ashtakavarga_bindus=5,
        verification_pass_status="single",
        class_prior=1.0,
        varga_id="D1",
    )
    saliences = [
        salience_formula_v2(SalienceInputsV2(**base, domain_count=n))["computed_salience"]
        for n in range(1, 11)
    ]
    assert len(set(saliences)) == 10, f"Expected 10 distinct values, got: {saliences}"


def test_marriage_and_progeny_top10_share_at_most_3():
    """Signals with both 'relationship' and 'progeny' domains should not dominate both top-10s.
    A signal in the RELATIONSHIP domain top-10 and also in the PROGENY domain top-10
    should be <=3 (they can appear in both, but broad cross-domain signals are deprioritized)."""
    from bodha_writers.formulas import SalienceInputsV2, salience_formula_v2

    # Generate 20 signals: 10 relationship-only (domain_count=1), 10 both (domain_count=2)
    rel_only = [
        salience_formula_v2(
            SalienceInputsV2(
                orb_tightness=0.8 + 0.02 * i,
                shadbala_norm=1.5,
                dignity_score=0.7,
                house_number=7,
                ashtakavarga_bindus=5,
                verification_pass_status="single",
                class_prior=1.0,
                varga_id="D1",
                domain_count=1,  # relationship only
            )
        )["computed_salience"]
        for i in range(10)
    ]
    both = [
        salience_formula_v2(
            SalienceInputsV2(
                orb_tightness=0.8 + 0.02 * i,
                shadbala_norm=1.5,
                dignity_score=0.7,
                house_number=7,
                ashtakavarga_bindus=5,
                verification_pass_status="single",
                class_prior=1.0,
                varga_id="D1",
                domain_count=2,  # relationship + progeny
            )
        )["computed_salience"]
        for i in range(10)
    ]
    # Relationship top-10 = top 10 from rel_only (they should outrank 'both')
    # Progeny top-10 = top 10 from 'both' signals (they appear in progeny too)
    # Intersection: at most 3 of 'both' should beat all rel_only
    above_min_rel = sum(1 for b in both if b >= min(rel_only))
    assert above_min_rel <= 3, (
        f"{above_min_rel} cross-domain signals dominated relationship top-10"
    )


def test_normal_signal_not_zeroed():
    """A normal (non-abstention) signal must not be zeroed."""
    from bodha_writers.formulas import SalienceInputsV2, salience_formula_v2

    result = salience_formula_v2(
        SalienceInputsV2(
            orb_tightness=1.0,
            shadbala_norm=1.5,
            dignity_score=0.7,
            house_number=7,
            ashtakavarga_bindus=5,
            verification_pass_status="single",
            class_prior=1.0,
            varga_id="D1",
            is_abstention_marker=False,
            domain_count=3,
        )
    )
    assert result["computed_salience"] > 0.0
