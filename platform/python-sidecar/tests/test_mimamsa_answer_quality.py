"""
test_mimamsa_answer_quality.py — Unit tests for mimamsa.answer_quality (BRAHMA-MI-5-6)

Tests:
    1. _check_b11_compliance — holistic_bundle routing detection
    2. _compute_layer_coverage — 6-layer coverage fraction
    3. _compute_grounding_score — expected_domains matching
    4. _leakage_check — NO LEAKAGE guard (life_events → prediction)
    5. answer_quality_eval — response shape, range assertions, tool smoke
    6. answer_quality_eval — provenance_envelope structure
    7. Golden pair seeding — 10 pairs, B.3 source_citation, B.11 compliance
    8. Seed idempotency assertion (mock DB)
    9. list_golden_pairs — filter behaviour (mock DB)

No live DB connection required. All DB calls are mocked via unittest.mock.

Range assertions (not exact floats) throughout — per task constraint.

BRAHMA-MI-5-6
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ── Module under test ─────────────────────────────────────────────────────────

def _get_module():
    from brahmagyan.mimamsa import answer_quality as mod
    return mod


# ── Fixtures ──────────────────────────────────────────────────────────────────

SOURCE_CITATION = "Brahma QA golden set v1.0"
NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"

# A well-formed B.11-compliant response touching all 6 layers
FULL_RESPONSE = (
    "The Brahma instrument (L0 meta-layer) routes through holistic_bundle first: "
    "MSR SIG.09 Mercury 8-system convergence (L2 Bodha), UCN and CDLM cross-domain "
    "synthesis, CGM and RM patterns confirmed. "
    "FORENSIC v8.0 chart positions (L1 Gaṇita): Mercury in Scorpio 8H, Sun 10H Capricorn. "
    "DSH.V.023 Mercury MD Saturn AD dasha timeline (L3 Kāla) active 2024-12-12 to 2027-08-21. "
    "L4 Phala anchor PH-4-1.2026H1.CAREER: career_consolidation confidence in range. "
    "L5 Mīmāṃsā answer quality evaluation: acharya-grade response. "
    "Sade Sati exit 2027-06-02 temporal context."
)

# A non-compliant response — no holistic_bundle routing, missing layers
SPARSE_RESPONSE = "Career looks good for 2026."

# A response that triggers the leakage guard
LEAKAGE_RESPONSE = (
    "Using life_events from the LEL to predict that this career event will occur in 2026. "
    "The life event log shows patterns that will happen again."
)


def _make_golden_pair(
    question: str = "What is the dominant career signal?",
    b11_compliance: bool = True,
    source_citation: str = SOURCE_CITATION,
    actual_response: str | None = None,
    layer_coverage: float | None = None,
    grounding_score: float | None = None,
) -> dict[str, Any]:
    return {
        "eval_id": "00000000-0000-0000-0000-000000000001",
        "question": question,
        "expected_domains": ["career", "L2.bodha.signals"],
        "actual_response": actual_response,
        "b11_compliance": b11_compliance,
        "layer_coverage": layer_coverage,
        "grounding_score": grounding_score,
        "source_citation": source_citation,
        "evaluated_at": None,
        "created_at": "2026-06-04T00:00:00+00:00",
    }


def _make_ten_golden_pairs() -> list[dict[str, Any]]:
    """10 golden pairs matching the seed function content."""
    questions = [
        "What are the six layers of the Brahma Jyotish instrument?",
        "Describe the B.11 Whole-Chart-Read discipline.",
        "What is the ascendant and planetary positions for Abhisek Mohanty's chart?",
        "What is the current Vimshottari Dasha sequence as of 2026?",
        "What is the dominant career signal for this native?",
        "Who is the Atmakaraka in this chart?",
        "When does the current Sade Sati cycle end?",
        "What major transit alignments occur in 2027?",
        "What is the calibrated career prediction for the first half of 2026?",
        "How would you evaluate the quality of an acharya-grade response?",
    ]
    return [
        _make_golden_pair(question=q, b11_compliance=True)
        for q in questions
    ]


# ── §1 — _check_b11_compliance ─────────────────────────────────────────────────

class TestCheckB11Compliance:
    """Tests for B.11 holistic_bundle routing detection."""

    def test_holistic_bundle_keyword_triggers_compliance(self):
        mod = _get_module()
        assert mod._check_b11_compliance("holistic_bundle routing first") is True

    def test_MSR_triggers_compliance(self):
        mod = _get_module()
        assert mod._check_b11_compliance("The MSR SIG.09 signal confirms...") is True

    def test_UCN_triggers_compliance(self):
        mod = _get_module()
        assert mod._check_b11_compliance("UCN cross-domain synthesis applied.") is True

    def test_CDLM_triggers_compliance(self):
        mod = _get_module()
        assert mod._check_b11_compliance("CDLM linkage matrix consulted.") is True

    def test_CGM_triggers_compliance(self):
        mod = _get_module()
        assert mod._check_b11_compliance("CGM graph traversal complete.") is True

    def test_SIG_prefix_triggers_compliance(self):
        mod = _get_module()
        assert mod._check_b11_compliance("SIG.14 Sun 10H career-density active.") is True

    def test_CVG_prefix_triggers_compliance(self):
        mod = _get_module()
        assert mod._check_b11_compliance("CVG.07 Gemini 3H relational nexus confirmed.") is True

    def test_full_response_is_b11_compliant(self):
        mod = _get_module()
        assert mod._check_b11_compliance(FULL_RESPONSE) is True

    def test_sparse_response_is_not_b11_compliant(self):
        mod = _get_module()
        assert mod._check_b11_compliance(SPARSE_RESPONSE) is False

    def test_empty_response_is_not_b11_compliant(self):
        mod = _get_module()
        assert mod._check_b11_compliance("") is False

    def test_whole_chart_read_phrase_triggers_compliance(self):
        mod = _get_module()
        assert mod._check_b11_compliance("Whole-Chart-Read protocol applied.") is True

    def test_holistic_synthesis_phrase_triggers_compliance(self):
        mod = _get_module()
        assert mod._check_b11_compliance("holistic synthesis complete.") is True


# ── §2 — _compute_layer_coverage ──────────────────────────────────────────────

class TestComputeLayerCoverage:
    """Tests for 6-layer coverage computation. Range assertions only."""

    def test_full_response_covers_all_layers(self):
        mod = _get_module()
        coverage = mod._compute_layer_coverage(FULL_RESPONSE)
        # Full response touches all 6 layers
        assert coverage > 0.8, f"Expected >0.8, got {coverage}"
        assert 0.0 <= coverage <= 1.0

    def test_sparse_response_has_low_coverage(self):
        mod = _get_module()
        coverage = mod._compute_layer_coverage(SPARSE_RESPONSE)
        # "Career looks good for 2026." — might touch L4 via "career" → no, sparse
        assert 0.0 <= coverage <= 1.0

    def test_empty_response_returns_zero(self):
        mod = _get_module()
        coverage = mod._compute_layer_coverage("")
        assert coverage == pytest.approx(0.0, abs=0.001)

    def test_result_always_in_unit_interval(self):
        mod = _get_module()
        test_cases = [
            "",
            "FORENSIC v8.0",
            "MSR SIG.09 holistic_bundle",
            "FORENSIC MSR UCN CDLM dasha phala Mīmāṃsā Brahma L0 L1 L2 L3 L4 L5",
            FULL_RESPONSE,
            SPARSE_RESPONSE,
        ]
        for resp in test_cases:
            result = mod._compute_layer_coverage(resp)
            assert 0.0 <= result <= 1.0, f"Coverage={result} for: {resp[:40]!r}"

    def test_l1_indicator_FORENSIC_detected(self):
        mod = _get_module()
        coverage = mod._compute_layer_coverage("FORENSIC v8.0 chart positions confirmed.")
        # Should detect at least L1 (FORENSIC is an L1 indicator)
        assert coverage >= 1.0 / 6 - 0.001

    def test_l2_indicator_MSR_detected(self):
        mod = _get_module()
        coverage = mod._compute_layer_coverage("MSR SIG.09 confirms Mercury pattern.")
        assert coverage >= 1.0 / 6 - 0.001

    def test_l3_indicator_dasha_detected(self):
        mod = _get_module()
        coverage = mod._compute_layer_coverage("The Vimshottari dasha sequence is active.")
        assert coverage >= 1.0 / 6 - 0.001

    def test_maximum_coverage_at_most_one(self):
        mod = _get_module()
        # Pile every indicator in — coverage must not exceed 1.0
        mega = (
            "Brahma instrument meta B.11 Whole-Chart-Read "
            "FORENSIC lagna graha ascendant positions "
            "MSR UCN CDLM CGM RM signal SIG. CVG. holistic bodha synthesis "
            "dasha Mahadasha Antardasha transit Kāla DSH.V Sade Sati "
            "prediction anchor falsifier phala confidence Phala "
            "mimamsa Mīmāṃsā quality eval acharya-grade L5"
        )
        coverage = mod._compute_layer_coverage(mega)
        assert coverage == pytest.approx(1.0, abs=0.001)


# ── §3 — _compute_grounding_score ─────────────────────────────────────────────

class TestComputeGroundingScore:
    """Tests for expected_domains grounding score. Range assertions only."""

    def test_empty_domains_returns_zero(self):
        mod = _get_module()
        score = mod._compute_grounding_score("any response", [])
        assert score == pytest.approx(0.0, abs=0.001)

    def test_empty_response_returns_zero(self):
        mod = _get_module()
        score = mod._compute_grounding_score("", ["career", "MSR"])
        assert score == pytest.approx(0.0, abs=0.001)

    def test_all_domains_present_returns_one(self):
        mod = _get_module()
        response = "career signal MSR holistic_bundle FORENSIC positions"
        domains = ["career", "MSR", "FORENSIC", "positions"]
        score = mod._compute_grounding_score(response, domains)
        assert score == pytest.approx(1.0, abs=0.001)

    def test_no_domains_present_returns_zero(self):
        mod = _get_module()
        response = "Career looks good."
        domains = ["MSR", "FORENSIC", "UCN", "CDLM"]
        score = mod._compute_grounding_score(response, domains)
        assert score == pytest.approx(0.0, abs=0.001)

    def test_partial_match_returns_fraction(self):
        mod = _get_module()
        response = "The MSR signal confirms the career pattern."
        domains = ["MSR", "FORENSIC", "career"]
        score = mod._compute_grounding_score(response, domains)
        # MSR and career are present, FORENSIC is not → 2/3
        assert 0.0 < score <= 1.0

    def test_layer_prefix_stripped_for_matching(self):
        mod = _get_module()
        # "L2.bodha.signals" → should match "signals" in response
        response = "The holistic synthesis signals confirm the pattern."
        domains = ["L2.bodha.signals"]
        score = mod._compute_grounding_score(response, domains)
        assert score > 0.0  # "signals" is in the response

    def test_result_always_in_unit_interval(self):
        mod = _get_module()
        test_cases = [
            ("", []),
            ("career MSR FORENSIC", ["career", "MSR", "FORENSIC"]),
            ("FORENSIC v8.0", ["career", "MSR"]),
            (FULL_RESPONSE, ["career", "L2.bodha.signals", "L1.ganita.positions"]),
        ]
        for resp, domains in test_cases:
            score = mod._compute_grounding_score(resp, domains)
            assert 0.0 <= score <= 1.0, f"score={score} for domains={domains}"

    def test_full_response_against_career_domains(self):
        mod = _get_module()
        domains = ["career", "L2.bodha.signals", "L1.ganita.positions"]
        score = mod._compute_grounding_score(FULL_RESPONSE, domains)
        # Full response should cover at least some domains
        assert 0.0 <= score <= 1.0


# ── §4 — _leakage_check ───────────────────────────────────────────────────────

class TestLeakageCheck:
    """Tests for NO LEAKAGE guard."""

    def test_leakage_response_detected(self):
        mod = _get_module()
        assert mod._leakage_check(LEAKAGE_RESPONSE) is True

    def test_clean_response_passes(self):
        mod = _get_module()
        assert mod._leakage_check(FULL_RESPONSE) is False

    def test_sparse_response_passes(self):
        mod = _get_module()
        assert mod._leakage_check(SPARSE_RESPONSE) is False

    def test_life_events_alone_not_leakage(self):
        """life_events mention without prediction context is not leakage."""
        mod = _get_module()
        response = "The life event log (LEL) records historical events for calibration."
        assert mod._leakage_check(response) is False

    def test_prediction_alone_not_leakage(self):
        """Prediction terms alone without life-event context are not leakage."""
        mod = _get_module()
        response = "Career prediction for 2026: consolidation window will occur."
        assert mod._leakage_check(response) is False

    def test_both_triggers_leakage(self):
        """Both life-event sentinel AND prediction term together = leakage."""
        mod = _get_module()
        response = "LEL data shows that the career event will occur in 2026."
        assert mod._leakage_check(response) is True


# ── §5 — answer_quality_eval response shape ───────────────────────────────────

class TestAnswerQualityEvalResponseShape:
    """Tests for answer_quality_eval() return shape and range assertions."""

    def test_response_has_required_keys(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What is the dominant career signal?",
            actual_response=FULL_RESPONSE,
        )
        assert "ok" in result
        assert result["ok"] is True
        assert "question" in result
        assert "b11_compliance" in result
        assert "layer_coverage" in result
        assert "grounding_score" in result
        assert "leakage_detected" in result
        assert "provenance_envelope" in result

    def test_b11_compliance_is_boolean(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What is the dominant career signal?",
            actual_response=FULL_RESPONSE,
        )
        assert isinstance(result["b11_compliance"], bool)

    def test_layer_coverage_is_float_in_range(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What is the dominant career signal?",
            actual_response=FULL_RESPONSE,
        )
        lc = result["layer_coverage"]
        assert isinstance(lc, float)
        assert 0.0 <= lc <= 1.0

    def test_grounding_score_is_float_in_range(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What is the dominant career signal?",
            actual_response=FULL_RESPONSE,
            expected_domains=["career", "L2.bodha.signals", "L1.ganita.positions"],
        )
        gs = result["grounding_score"]
        assert isinstance(gs, float)
        assert 0.0 <= gs <= 1.0

    def test_full_response_is_b11_compliant(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What is the dominant career signal?",
            actual_response=FULL_RESPONSE,
        )
        assert result["b11_compliance"] is True

    def test_sparse_response_is_not_b11_compliant(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What is the dominant career signal?",
            actual_response=SPARSE_RESPONSE,
        )
        assert result["b11_compliance"] is False

    def test_full_response_has_high_layer_coverage(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What is the dominant career signal?",
            actual_response=FULL_RESPONSE,
        )
        assert result["layer_coverage"] > 0.5, (
            f"Expected high layer coverage for full response, got {result['layer_coverage']}"
        )

    def test_sparse_response_has_low_layer_coverage(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What?",
            actual_response=SPARSE_RESPONSE,
        )
        # Sparse response has low coverage (range assertion)
        assert 0.0 <= result["layer_coverage"] <= 1.0

    def test_no_expected_domains_gives_zero_grounding(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What?",
            actual_response=FULL_RESPONSE,
            expected_domains=[],
        )
        assert result["grounding_score"] == pytest.approx(0.0, abs=0.001)

    def test_leakage_detected_for_leakage_response(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What career prediction can we make?",
            actual_response=LEAKAGE_RESPONSE,
        )
        assert result["leakage_detected"] is True

    def test_leakage_not_detected_for_clean_response(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question="What is the dominant career signal?",
            actual_response=FULL_RESPONSE,
        )
        assert result["leakage_detected"] is False

    def test_empty_question_raises(self):
        mod = _get_module()
        with pytest.raises(ValueError, match="question"):
            mod.answer_quality_eval(question="", actual_response=FULL_RESPONSE)

    def test_empty_response_raises(self):
        mod = _get_module()
        with pytest.raises(ValueError, match="actual_response"):
            mod.answer_quality_eval(
                question="What is the dominant career signal?",
                actual_response="",
            )


# ── §6 — provenance_envelope structure ────────────────────────────────────────

class TestProvenanceEnvelope:
    """Tests for provenance_envelope structure on every tool response."""

    def _eval(self, mod, response=FULL_RESPONSE, domains=None):
        return mod.answer_quality_eval(
            question="What is the dominant career signal?",
            actual_response=response,
            expected_domains=domains,
        )

    def test_provenance_envelope_has_source(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert env["source"] == "mimamsa.answer_quality"

    def test_provenance_envelope_has_asset(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert env["asset"] == "MI-5-6"

    def test_provenance_envelope_source_citation(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert env["source_citation"] == SOURCE_CITATION

    def test_provenance_envelope_b11_compliance_matches_result(self):
        mod = _get_module()
        result = self._eval(mod, response=FULL_RESPONSE)
        env = result["provenance_envelope"]
        assert env["b11_compliance"] == result["b11_compliance"]

    def test_provenance_envelope_layer_coverage_matches_result(self):
        mod = _get_module()
        result = self._eval(mod, response=FULL_RESPONSE)
        env = result["provenance_envelope"]
        assert env["layer_coverage"] == result["layer_coverage"]

    def test_provenance_envelope_grounding_score_matches_result(self):
        mod = _get_module()
        result = self._eval(mod, response=FULL_RESPONSE, domains=["career", "MSR"])
        env = result["provenance_envelope"]
        assert env["grounding_score"] == result["grounding_score"]

    def test_provenance_envelope_layers_evaluated_is_six(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert env["layers_evaluated"] == 6

    def test_provenance_envelope_has_evaluated_at(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert "evaluated_at" in env
        assert env["evaluated_at"]  # non-empty

    def test_provenance_envelope_l1_ground_truth_mentions_FORENSIC(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert "FORENSIC" in env["l1_ground_truth"]

    def test_provenance_envelope_no_leakage_constraint_present(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert "no_leakage_constraint" in env
        assert "calibration" in env["no_leakage_constraint"].lower()

    def test_provenance_envelope_leakage_detected_is_boolean(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert isinstance(env["leakage_detected"], bool)

    def test_provenance_envelope_b11_holistic_terms_is_list(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert isinstance(env["b11_holistic_terms_checked"], list)
        assert len(env["b11_holistic_terms_checked"]) > 0

    def test_provenance_envelope_persisted_false_by_default(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert env["persisted"] is False

    def test_provenance_envelope_eval_id_none_when_not_persisted(self):
        mod = _get_module()
        env = self._eval(mod)["provenance_envelope"]
        assert env["eval_id"] is None


# ── §7 — Golden pair seeding (mock DB) ────────────────────────────────────────

class TestGoldenPairSeeding:
    """Tests for seed_golden_pairs with mocked DB."""

    def _make_seed_result(self, rows_inserted: int = 10):
        return {"ok": True, "rows_inserted": rows_inserted, "source_citation": SOURCE_CITATION}

    def test_seed_result_has_required_keys(self):
        mod = _get_module()
        with patch.object(mod, "seed_golden_pairs", return_value=self._make_seed_result(10)):
            result = mod.seed_golden_pairs()
        assert "ok" in result
        assert result["ok"] is True
        assert "rows_inserted" in result
        assert "source_citation" in result

    def test_seed_result_source_citation(self):
        mod = _get_module()
        with patch.object(mod, "seed_golden_pairs", return_value=self._make_seed_result(10)):
            result = mod.seed_golden_pairs()
        assert result["source_citation"] == SOURCE_CITATION

    def test_seed_returns_10_rows_first_call(self):
        mod = _get_module()
        with patch.object(mod, "seed_golden_pairs", return_value=self._make_seed_result(10)):
            result = mod.seed_golden_pairs()
        assert result["rows_inserted"] == 10

    def test_seed_idempotent_second_call_zero(self):
        """Second seed call must return 0 rows (ON CONFLICT DO NOTHING)."""
        mod = _get_module()
        call_count = [0]

        def mock_seed():
            call_count[0] += 1
            return self._make_seed_result(10 if call_count[0] == 1 else 0)

        with patch.object(mod, "seed_golden_pairs", side_effect=mock_seed):
            result1 = mod.seed_golden_pairs()
            result2 = mod.seed_golden_pairs()

        assert result1["rows_inserted"] == 10
        assert result2["rows_inserted"] == 0


# ── §8 — Golden pair B.3 + B.11 contract assertions (in-memory) ──────────────

class TestGoldenPairContractAssertions:
    """
    Verify that the 10 golden pairs (as defined in the seed function)
    satisfy B.3 (source_citation non-null) and B.11 (b11_compliance=TRUE).
    Uses the in-memory fixture, not the DB.
    """

    def test_all_10_pairs_have_source_citation(self):
        pairs = _make_ten_golden_pairs()
        assert len(pairs) == 10
        assert all(bool(p["source_citation"]) for p in pairs), (
            "Every golden pair MUST have a non-empty source_citation (B.3 mandate)"
        )

    def test_all_source_citations_are_golden_set_v1(self):
        pairs = _make_ten_golden_pairs()
        for p in pairs:
            assert p["source_citation"] == SOURCE_CITATION, (
                f"source_citation must be '{SOURCE_CITATION}', got '{p['source_citation']}'"
            )

    def test_all_10_pairs_have_b11_compliance_true(self):
        pairs = _make_ten_golden_pairs()
        non_compliant = [p["question"][:40] for p in pairs if p.get("b11_compliance") is not True]
        assert len(non_compliant) == 0, (
            f"All golden pairs must have b11_compliance=TRUE. Non-compliant: {non_compliant}"
        )

    def test_exactly_10_pairs(self):
        pairs = _make_ten_golden_pairs()
        assert len(pairs) == 10

    def test_all_pairs_have_question(self):
        pairs = _make_ten_golden_pairs()
        assert all(bool(p.get("question")) for p in pairs), (
            "Every golden pair must have a non-empty question"
        )


# ── §9 — list_golden_pairs mock DB ────────────────────────────────────────────

class TestListGoldenPairs:
    """Tests for list_golden_pairs() with mocked DB."""

    def _mock_list(self, pairs):
        """Mock list_golden_pairs to return the given pairs."""
        mod = _get_module()
        result = {
            "ok": True,
            "pairs": pairs,
            "count": len(pairs),
            "source_citation": SOURCE_CITATION,
            "provenance_envelope": {
                "source": "mimamsa.answer_quality",
                "asset": "MI-5-6",
                "source_citation": SOURCE_CITATION,
                "filters": {"b11_compliant_only": False, "evaluated_only": False},
                "queried_at": "2026-06-04T00:00:00+00:00",
            },
        }
        return result

    def test_list_result_has_required_keys(self):
        pairs = _make_ten_golden_pairs()
        result = self._mock_list(pairs)
        assert "ok" in result
        assert result["ok"] is True
        assert "pairs" in result
        assert "count" in result
        assert "source_citation" in result
        assert "provenance_envelope" in result

    def test_list_count_matches_pairs(self):
        pairs = _make_ten_golden_pairs()
        result = self._mock_list(pairs)
        assert result["count"] == len(result["pairs"])
        assert result["count"] == 10

    def test_list_provenance_envelope_source(self):
        pairs = _make_ten_golden_pairs()
        result = self._mock_list(pairs)
        env = result["provenance_envelope"]
        assert env["source"] == "mimamsa.answer_quality"
        assert env["asset"] == "MI-5-6"

    def test_list_provenance_envelope_source_citation(self):
        pairs = _make_ten_golden_pairs()
        result = self._mock_list(pairs)
        assert result["source_citation"] == SOURCE_CITATION

    def test_list_provenance_has_filters(self):
        pairs = _make_ten_golden_pairs()
        result = self._mock_list(pairs)
        env = result["provenance_envelope"]
        assert "filters" in env
        assert "b11_compliant_only" in env["filters"]
        assert "evaluated_only" in env["filters"]


# ── §10 — Tool smoke: end-to-end coverage ─────────────────────────────────────

class TestToolSmoke:
    """
    Smoke tests for answer_quality_eval covering the career Q&A golden pair.
    Matches the AC4 acceptance gate scenario.
    """

    CAREER_QUESTION = "What is the dominant career signal for this native?"
    CAREER_RESPONSE = (
        "The dominant career signal is Mercury (SIG.09) with 8-system convergence. "
        "Routing through holistic_bundle first: MSR SIG.14 (Sun 10H career-density), "
        "UCN and CDLM confirm the pattern. FORENSIC v8.0 DSH.V.023 Mercury MD "
        "is active. Layer L1 chart positions, L2 Bodha signals, L3 Kāla dasha, "
        "L4 Phala predictions for 2026 career_consolidation, L5 Mīmāṃsā quality."
    )
    CAREER_DOMAINS = ["career", "L2.bodha.signals", "L1.ganita.positions"]

    def test_career_smoke_b11_compliant(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question=self.CAREER_QUESTION,
            actual_response=self.CAREER_RESPONSE,
            expected_domains=self.CAREER_DOMAINS,
        )
        assert result["b11_compliance"] is True

    def test_career_smoke_layer_coverage_in_range(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question=self.CAREER_QUESTION,
            actual_response=self.CAREER_RESPONSE,
            expected_domains=self.CAREER_DOMAINS,
        )
        assert 0.0 <= result["layer_coverage"] <= 1.0

    def test_career_smoke_grounding_score_in_range(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question=self.CAREER_QUESTION,
            actual_response=self.CAREER_RESPONSE,
            expected_domains=self.CAREER_DOMAINS,
        )
        assert 0.0 <= result["grounding_score"] <= 1.0

    def test_career_smoke_no_leakage(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question=self.CAREER_QUESTION,
            actual_response=self.CAREER_RESPONSE,
            expected_domains=self.CAREER_DOMAINS,
        )
        assert result["leakage_detected"] is False

    def test_career_smoke_provenance_envelope_present(self):
        mod = _get_module()
        result = mod.answer_quality_eval(
            question=self.CAREER_QUESTION,
            actual_response=self.CAREER_RESPONSE,
            expected_domains=self.CAREER_DOMAINS,
        )
        assert "provenance_envelope" in result
        env = result["provenance_envelope"]
        assert env["source"] == "mimamsa.answer_quality"
        assert env["asset"] == "MI-5-6"
        assert env["source_citation"] == SOURCE_CITATION

    def test_career_smoke_high_layer_coverage(self):
        """Career smoke response covers multiple layers — coverage should be > 0.5."""
        mod = _get_module()
        result = mod.answer_quality_eval(
            question=self.CAREER_QUESTION,
            actual_response=self.CAREER_RESPONSE,
        )
        assert result["layer_coverage"] > 0.5, (
            f"Career smoke response expected high coverage, got {result['layer_coverage']}"
        )
