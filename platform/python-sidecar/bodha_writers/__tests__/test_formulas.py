"""Unit tests for bodha_writers/formulas.py.

All tests use deterministic fixture inputs so they double as reproducibility
proofs: same inputs → same outputs, always (Trap-2 avoidance, Campaign §6.C).

Run: python -m pytest platform/python-sidecar/bodha_writers/__tests__/test_formulas.py -v
"""
from __future__ import annotations

import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from bodha_writers.formulas import (
    DIGNITY_SCORE,
    HOUSE_WEIGHT,
    SalienceInputs,
    salience_formula_v1,
    VERSION_SALIENCE_FORMULA,
    LinkageInputs,
    linkage_formula_v1,
    VERSION_LINKAGE_FORMULA,
    ResonanceInputs,
    resonance_score_v1,
    VERSION_RESONANCE_FORMULA,
    ResonanceMatchInputs,
    resonance_match_score_v1,
    ConvergenceInputs,
    convergence_formula_v1,
    VERSION_CONVERGENCE_FORMULA,
    CentralityInputs,
    centrality_formula_v1,
    VERSION_CENTRALITY_FORMULA,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def approx(a: float, b: float, tol: float = 1e-4) -> bool:
    return abs(a - b) < tol


# ──────────────────────────────────────────────────────────────────────────────
# salience_formula_v1
# ──────────────────────────────────────────────────────────────────────────────

class TestSalienceFormulaV1:
    def test_version_constant(self):
        assert VERSION_SALIENCE_FORMULA == "v1.0"

    def test_dignity_score_table(self):
        assert DIGNITY_SCORE["exalted"] == 1.00
        assert DIGNITY_SCORE["debilitated"] == 0.10
        assert DIGNITY_SCORE["own"] == 0.85

    def test_house_weight_table_kendra_trikona(self):
        assert HOUSE_WEIGHT[1] == 1.30
        assert HOUSE_WEIGHT[5] == 1.20
        assert HOUSE_WEIGHT[9] == 1.20
        # Dusthana
        assert HOUSE_WEIGHT[6] == 0.90
        assert HOUSE_WEIGHT[8] == 0.90

    def test_neutral_signal(self):
        """A neutral signal: orb=1, shadbala=1, dignity=neutral, 1 source, no modifiers."""
        s = SalienceInputs(
            orb_tightness=1.0,
            shadbala_norm=1.0,
            dignity_score=DIGNITY_SCORE["neutral"],
            source_corroboration_count_by_text=1,
            dasha_activation_proximity_score=0.0,
            house_number=2,    # "other" → 1.00
            ashtakavarga_bindus=4,  # 3-4 → 1.00
            aspect_modifier=0.0,
            vargottama_amplification=0.0,
            argala_modifier=0.0,
            neechabhanga_modifier=1.0,
            cancellation_modifier=1.0,
        )
        result = salience_formula_v1(s)
        # deterministic_strength = 1.0 × 1.0 × 0.50 = 0.5
        # verification_certainty = log(2)/log(10) ≈ 0.30103
        # computed = 0.5 × 0.30103 × 1.0 × 1.0 × 1.0 × 1.0 × 1.0 × 1.0 × 1.0 × 1.0
        expected_ds = 0.5
        expected_vc = math.log(2) / math.log(10)
        expected = expected_ds * expected_vc
        assert approx(result["deterministic_strength"], expected_ds)
        assert approx(result["verification_certainty"], expected_vc)
        assert approx(result["computed_salience"], expected)
        assert result["salience_formula_version"] == "v1.0"

    def test_strong_exalted_signal(self):
        """Exalted graha in 9th (trikona), vargottama, 3 sources."""
        s = SalienceInputs(
            orb_tightness=0.9,
            shadbala_norm=1.5,
            dignity_score=DIGNITY_SCORE["exalted"],
            source_corroboration_count_by_text=3,
            dasha_activation_proximity_score=0.8,
            house_number=9,
            ashtakavarga_bindus=7,
            vargottama_amplification=0.2,
            neechabhanga_modifier=1.0,
            cancellation_modifier=1.0,
        )
        result = salience_formula_v1(s)
        assert result["computed_salience"] > 1.0, "strong exalted signal should exceed 1.0"
        assert result["house_weight_multiplier"] == 1.20
        assert result["ashtakavarga_support_multiplier"] == 1.15

    def test_cancelled_signal_is_tanked(self):
        """Cancelled signal: cancellation_modifier=0.1 should tank salience."""
        s_normal = SalienceInputs(cancellation_modifier=1.0)
        s_cancelled = SalienceInputs(cancellation_modifier=0.1)
        r_normal = salience_formula_v1(s_normal)
        r_cancelled = salience_formula_v1(s_cancelled)
        assert r_cancelled["computed_salience"] < r_normal["computed_salience"] * 0.15

    def test_neechabhanga_boosts(self):
        """neechabhanga_modifier=1.3 should increase salience."""
        s_base = SalienceInputs(dignity_score=DIGNITY_SCORE["debilitated"])
        s_cancelled = SalienceInputs(dignity_score=DIGNITY_SCORE["debilitated"],
                                      neechabhanga_modifier=1.3)
        r_base = salience_formula_v1(s_base)
        r_boost = salience_formula_v1(s_cancelled)
        assert approx(r_boost["computed_salience"] / r_base["computed_salience"], 1.3, tol=1e-3)

    def test_reproducibility(self):
        """Same inputs → same output on repeated calls."""
        s = SalienceInputs(
            orb_tightness=0.7,
            shadbala_norm=1.2,
            dignity_score=0.85,
            source_corroboration_count_by_text=2,
            house_number=10,
            ashtakavarga_bindus=6,
        )
        r1 = salience_formula_v1(s)
        r2 = salience_formula_v1(s)
        assert r1 == r2

    def test_version_stamp_in_output(self):
        r = salience_formula_v1(SalienceInputs())
        assert "salience_formula_version" in r
        assert r["salience_formula_version"] == VERSION_SALIENCE_FORMULA


# ──────────────────────────────────────────────────────────────────────────────
# linkage_formula_v1
# ──────────────────────────────────────────────────────────────────────────────

class TestLinkageFormulaV1:
    def test_version_constant(self):
        assert VERSION_LINKAGE_FORMULA == "v1.0"

    def test_empty_cell(self):
        r = linkage_formula_v1(LinkageInputs())
        assert r["computed_linkage_strength"] == 0.0

    def test_pure_positive_signals(self):
        signals = [{"salience": 0.8, "in_contradiction": False}] * 5
        r = linkage_formula_v1(LinkageInputs(shared_signals=signals,
                                              high_convergence_count=3,
                                              shared_factor_count=4,
                                              cross_ayanamsha_stability_score=1.0))
        assert r["positive_contribution"] == approx_val(4.0)
        assert r["computed_linkage_strength"] > 4.0   # bonuses applied

    def test_contradiction_reduces_linkage(self):
        signals_no_contra = [{"salience": 0.8, "in_contradiction": False}] * 4
        signals_with_contra = [{"salience": 0.8, "in_contradiction": False}] * 3 + \
                               [{"salience": 0.8, "in_contradiction": True}]
        r_clean = linkage_formula_v1(LinkageInputs(shared_signals=signals_no_contra))
        r_dirty = linkage_formula_v1(LinkageInputs(shared_signals=signals_with_contra))
        assert r_dirty["computed_linkage_strength"] < r_clean["computed_linkage_strength"]

    def test_stability_zero_collapses_linkage(self):
        signals = [{"salience": 1.0, "in_contradiction": False}] * 3
        r = linkage_formula_v1(LinkageInputs(shared_signals=signals,
                                              cross_ayanamsha_stability_score=0.0))
        assert r["computed_linkage_strength"] == 0.0

    def test_reproducibility(self):
        inp = LinkageInputs(
            shared_signals=[{"salience": 0.5, "in_contradiction": False}] * 4,
            high_convergence_count=2,
            shared_factor_count=3,
            cross_ayanamsha_stability_score=0.9,
        )
        assert linkage_formula_v1(inp) == linkage_formula_v1(inp)

    def test_version_stamp(self):
        r = linkage_formula_v1(LinkageInputs())
        assert r["linkage_formula_version"] == VERSION_LINKAGE_FORMULA


def approx_val(v: float) -> float:
    return round(v, 6)


# ──────────────────────────────────────────────────────────────────────────────
# resonance_score_v1
# ──────────────────────────────────────────────────────────────────────────────

class TestResonanceScoreV1:
    def test_version_constant(self):
        assert VERSION_RESONANCE_FORMULA == "v1.0"

    def test_strong_graha_has_low_resonance(self):
        """A fully strong, unafflicted graha should have low resonance (not a remedy target)."""
        strong = ResonanceInputs(
            shadbala_normalized=1.0,
            bhava_bala_normalized=1.0,
            combustion_score=0.0,
            debility_score=0.0,
            affliction_count_normalized=0.0,
            cancellation_burden=0.0,
            dispositor_chain_weakness=0.0,
            vargottama_absence_score=0.0,
            dasha_proximity_activation_score=0.0,
        )
        r = resonance_score_v1(strong)
        assert r["resonance_score"] < 0.2

    def test_weak_graha_has_high_resonance(self):
        """A combust, debilitated, afflicted graha with active contradictions and
        domain burden should have resonance well above 1.0."""
        weak = ResonanceInputs(
            shadbala_normalized=0.0,
            bhava_bala_normalized=0.0,
            combustion_score=1.0,
            debility_score=1.0,
            affliction_count_normalized=1.0,
            cancellation_burden=1.0,
            dispositor_chain_weakness=1.0,
            vargottama_absence_score=1.0,
            dasha_proximity_activation_score=1.0,
            msr_signals_in_conflict=1.0,     # contradiction_factor = 1.0
            cdlm_weakest_constituent_count=1.0,
            cgm_motifs_weakest_node=1.0,
            is_yoga_karaka=True,
            chara_role="AK",
        )
        r = resonance_score_v1(weak)
        assert r["resonance_score"] > 1.0

    def test_yoga_karaka_amplification(self):
        base = ResonanceInputs(shadbala_normalized=0.3)
        yk = ResonanceInputs(shadbala_normalized=0.3, is_yoga_karaka=True)
        r_base = resonance_score_v1(base)
        r_yk = resonance_score_v1(yk)
        assert approx(r_yk["resonance_score"] / r_base["resonance_score"], 1.20, tol=1e-3)

    def test_atmakaraka_amplification(self):
        base = ResonanceInputs(shadbala_normalized=0.3)
        ak = ResonanceInputs(shadbala_normalized=0.3, chara_role="AK")
        r_base = resonance_score_v1(base)
        r_ak = resonance_score_v1(ak)
        assert approx(r_ak["resonance_score"] / r_base["resonance_score"], 1.30, tol=1e-3)

    def test_reproducibility(self):
        inp = ResonanceInputs(shadbala_normalized=0.4, combustion_score=0.6, chara_role="BK")
        assert resonance_score_v1(inp) == resonance_score_v1(inp)

    def test_version_stamp(self):
        r = resonance_score_v1(ResonanceInputs())
        assert r["resonance_score_formula_version"] == VERSION_RESONANCE_FORMULA


# ──────────────────────────────────────────────────────────────────────────────
# resonance_match_score_v1
# ──────────────────────────────────────────────────────────────────────────────

class TestResonanceMatchScoreV1:
    def test_counter_indication_halves_score(self):
        p_clean = ResonanceMatchInputs(classical_strength_for_graha=0.8)
        p_contra = ResonanceMatchInputs(classical_strength_for_graha=0.8,
                                         has_active_counter_indication=True)
        r_clean = resonance_match_score_v1(p_clean)
        r_contra = resonance_match_score_v1(p_contra)
        assert approx(r_contra["resonance_match_score"],
                      r_clean["resonance_match_score"] * 0.5, tol=0.01)

    def test_pattern_alignment_boosts(self):
        p_no_align = ResonanceMatchInputs(targets_motif_id="motif_abc",
                                           active_motif_ids=set())
        p_align = ResonanceMatchInputs(targets_motif_id="motif_abc",
                                        active_motif_ids={"motif_abc"})
        r_no = resonance_match_score_v1(p_no_align)
        r_yes = resonance_match_score_v1(p_align)
        assert r_yes["resonance_match_score"] > r_no["resonance_match_score"]

    def test_reproducibility(self):
        p = ResonanceMatchInputs(classical_strength_for_graha=0.7,
                                  chart_typology="career_dominant",
                                  remedy_category="gem",
                                  cross_tradition_corroboration_count=3)
        assert resonance_match_score_v1(p) == resonance_match_score_v1(p)


# ──────────────────────────────────────────────────────────────────────────────
# convergence_formula_v1
# ──────────────────────────────────────────────────────────────────────────────

class TestConvergenceFormulaV1:
    def test_version_constant(self):
        assert VERSION_CONVERGENCE_FORMULA == "v1.0"

    def test_empty_domain(self):
        r = convergence_formula_v1(ConvergenceInputs(domain="career"))
        assert r["convergence_count"] == 0
        assert r["convergence_score"] == 0.0

    def test_single_tradition_baseline(self):
        r = convergence_formula_v1(ConvergenceInputs(
            domain="career",
            signal_saliencies=[0.8, 0.7, 0.9],
            signal_traditions=["parashari", "parashari", "parashari"],
        ))
        assert r["convergence_count"] == 3
        assert r["cross_tradition_count"] == 1
        assert r["convergence_formula_version"] == "v1.0"

    def test_multi_tradition_boosts_score(self):
        mono = ConvergenceInputs(
            domain="career",
            signal_saliencies=[0.8] * 4,
            signal_traditions=["parashari"] * 4,
        )
        multi = ConvergenceInputs(
            domain="career",
            signal_saliencies=[0.8] * 4,
            signal_traditions=["parashari", "jaimini", "kp", "tajik"],
        )
        r_mono = convergence_formula_v1(mono)
        r_multi = convergence_formula_v1(multi)
        assert r_multi["convergence_score"] > r_mono["convergence_score"]
        assert r_multi["cross_tradition_count"] == 4

    def test_contradiction_reduces_score(self):
        base = ConvergenceInputs(
            domain="relationships",
            signal_saliencies=[0.7] * 5,
            signal_traditions=["parashari"] * 5,
            contradiction_count=0,
        )
        contra = ConvergenceInputs(
            domain="relationships",
            signal_saliencies=[0.7] * 5,
            signal_traditions=["parashari"] * 5,
            contradiction_count=3,
        )
        r_base = convergence_formula_v1(base)
        r_contra = convergence_formula_v1(contra)
        assert r_contra["convergence_score"] < r_base["convergence_score"]

    def test_floor_at_50pct_penalty(self):
        """Contradiction penalty is floored at 0.5 — signal never goes to zero."""
        r = convergence_formula_v1(ConvergenceInputs(
            domain="health",
            signal_saliencies=[0.5] * 10,
            signal_traditions=["parashari"] * 10,
            contradiction_count=100,   # extreme
        ))
        assert r["convergence_score"] > 0

    def test_reproducibility(self):
        inp = ConvergenceInputs(
            domain="wealth",
            signal_saliencies=[0.6, 0.8, 0.7, 0.9],
            signal_traditions=["parashari", "jaimini", "kp", "parashari"],
            contradiction_count=1,
        )
        assert convergence_formula_v1(inp) == convergence_formula_v1(inp)


# ──────────────────────────────────────────────────────────────────────────────
# centrality_formula_v1
# ──────────────────────────────────────────────────────────────────────────────

class TestCentralityFormulaV1:
    def test_version_constant(self):
        assert VERSION_CENTRALITY_FORMULA == "v1.0"

    def test_zero_inputs(self):
        r = centrality_formula_v1(CentralityInputs())
        assert r["composite_centrality"] >= 0.0

    def test_high_pagerank_high_centrality(self):
        low = CentralityInputs(pagerank_score=0.01, eigenvector_centrality=0.01,
                                betweenness_centrality=0.01, harmonic_centrality=0.01)
        high = CentralityInputs(pagerank_score=0.9, eigenvector_centrality=0.9,
                                 betweenness_centrality=0.8, harmonic_centrality=0.7,
                                 degree_total=15, max_degree_in_graph=20,
                                 strength_score=0.9, terminus_convergence_weight=1.5)
        r_low = centrality_formula_v1(low)
        r_high = centrality_formula_v1(high)
        assert r_high["composite_centrality"] > r_low["composite_centrality"] * 5

    def test_terminus_weight_amplifies(self):
        base = CentralityInputs(pagerank_score=0.5, eigenvector_centrality=0.5,
                                  betweenness_centrality=0.3, harmonic_centrality=0.4,
                                  terminus_convergence_weight=1.0)
        terminus = CentralityInputs(pagerank_score=0.5, eigenvector_centrality=0.5,
                                     betweenness_centrality=0.3, harmonic_centrality=0.4,
                                     terminus_convergence_weight=2.0)
        r_base = centrality_formula_v1(base)
        r_term = centrality_formula_v1(terminus)
        assert approx(r_term["composite_centrality"] / r_base["composite_centrality"], 2.0, tol=1e-3)

    def test_strength_amplifier_range(self):
        """strength_score=0 → amplifier=0.5; strength_score=1 → amplifier=1.0."""
        zero = CentralityInputs(pagerank_score=0.5, strength_score=0.0)
        full = CentralityInputs(pagerank_score=0.5, strength_score=1.0)
        r_zero = centrality_formula_v1(zero)
        r_full = centrality_formula_v1(full)
        assert approx(r_full["composite_centrality"] / r_zero["composite_centrality"], 2.0, tol=0.05)

    def test_reproducibility(self):
        inp = CentralityInputs(pagerank_score=0.4, eigenvector_centrality=0.3,
                                betweenness_centrality=0.2, harmonic_centrality=0.35,
                                degree_total=8, max_degree_in_graph=15,
                                strength_score=0.7, terminus_convergence_weight=1.2)
        assert centrality_formula_v1(inp) == centrality_formula_v1(inp)

    def test_version_stamp(self):
        r = centrality_formula_v1(CentralityInputs())
        assert r["centrality_formula_version"] == VERSION_CENTRALITY_FORMULA
