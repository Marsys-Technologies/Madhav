"""salience_formula_v2's verification_pass_status handling — Nirmāṇa #1729 / D-CND-05.

L1's finding: VERIFICATION_RESCALE named 3 of 13 settled vocabulary members and let
everything else fall through to a silent 0.60 default. Two consequences:
  1. `single` (80.7% of live chart_facts) fell through to 0.60 while its own
     DECLARED ALIAS `single_pass` (verification_vocab.deprecated_alias_of) was
     priced at 0.85 -- a 42% relative gap between two strings the vocabulary
     calls synonyms.
  2. Five statuses describe the ABSENCE of a value (an N/A, a skip, a floor)
     rather than a value's verification state; pricing an N/A at 0.60 is a
     category error, not a conservative choice.

Ruling (Conductor, full text on #1729): alias resolution through
verification_vocab.canonical(), an explicit weight or EXCLUDED_NO_VALUE_STATUSES
membership for all 12 canonical members, and a loud failure for anything outside
the settled vocabulary. These tests cover that contract at the formula level.
"""
from __future__ import annotations

import pytest

from bodha_writers.formulas import (
    EXCLUDED_NO_VALUE_STATUSES,
    VERIFICATION_RESCALE,
    SalienceInputsV2,
    salience_formula_v2,
)
from brahmagyan.verification_vocab import ALL_STATUSES, canonical


def _rescale_for(status: str) -> float:
    return salience_formula_v2(SalienceInputsV2(verification_pass_status=status))["verification_rescale"]


class TestAliasResolution:
    def test_single_and_single_pass_score_identically(self) -> None:
        """The defect itself: two strings the vocabulary calls synonyms must be
        priced the same, not coincidentally close."""
        assert _rescale_for("single") == _rescale_for("single_pass") == 0.85

    def test_single_pass_is_not_a_separate_key_in_the_table(self) -> None:
        """Ruling part 2: a second copy of the shadowing defect is not a fix."""
        assert "single_pass" not in VERIFICATION_RESCALE

    def test_single_pass_resolves_through_the_vocabulary_not_a_local_copy(self) -> None:
        """canonical('single_pass') must come from verification_vocab, proving the
        alias is resolved through the SSoT rather than restated locally."""
        assert canonical("single_pass") == "single"


class TestGroupAWeights:
    """The ruled weight table (L1 proposed, Conductor approved in full)."""

    @pytest.mark.parametrize(
        "status,expected",
        [
            ("two_pass_verified", 1.00),
            ("classical_match", 0.90),
            ("single", 0.85),
            ("pending_w3_verification", 0.85),
            ("computed_extension", 0.75),
            ("documented_approximation", 0.60),
            ("divergent_flagged", 0.40),
        ],
    )
    def test_ruled_weight(self, status: str, expected: float) -> None:
        assert _rescale_for(status) == expected

    def test_pending_w3_verification_matches_single_deliberately(self) -> None:
        """Ruled as deliberately identical: deferral is a project-management fact,
        not an evidential one."""
        assert _rescale_for("pending_w3_verification") == _rescale_for("single")

    def test_scale_is_strictly_ordered(self) -> None:
        """two_pass_verified > classical_match > single == pending_w3_verification
        > computed_extension > documented_approximation > divergent_flagged."""
        order = [
            "two_pass_verified", "classical_match", "single",
            "computed_extension", "documented_approximation", "divergent_flagged",
        ]
        weights = [_rescale_for(s) for s in order]
        assert weights == sorted(weights, reverse=True)
        assert len(set(weights)) == len(weights), "each rung must be distinct"


class TestExcludedNoValue:
    """Group B: statuses describing the absence of a value, not its verification."""

    @pytest.mark.parametrize("status", sorted(EXCLUDED_NO_VALUE_STATUSES))
    def test_excluded_status_has_zero_rescale_and_is_flagged(self, status: str) -> None:
        result = salience_formula_v2(SalienceInputsV2(verification_pass_status=status))
        assert result["verification_rescale"] == 0.0
        assert result["excluded_from_ranking"] is True

    def test_non_excluded_status_is_not_flagged(self) -> None:
        result = salience_formula_v2(SalienceInputsV2(verification_pass_status="single"))
        assert result["excluded_from_ranking"] is False

    def test_excluded_status_zeroes_computed_salience(self) -> None:
        """A row with no value to weight should not carry a misleadingly non-zero
        computed_salience that a naive reader mistakes for a real ranked score."""
        result = salience_formula_v2(SalienceInputsV2(
            verification_pass_status="not_defined_for_nodes",
            class_prior=1.5, specificity=1.5, shadbala_norm=2.0,
        ))
        assert result["computed_salience"] == 0.0

    def test_the_five_group_b_statuses_are_exactly_this_set(self) -> None:
        assert EXCLUDED_NO_VALUE_STATUSES == frozenset({
            "floored",
            "not_defined_for_nodes",
            "scope_cap_sentinel",
            "skipped_malformed_source",
            "external_computation_required",
        })


class TestUnknownStatusRaisesLoudly:
    """§N.8: an unrecognized status must fail loudly, not default to a plausible
    lowest weight (the exact defect this whole fix removes for the known ones)."""

    def test_illegal_status_raises(self) -> None:
        with pytest.raises(ValueError, match="not a member of the settled vocabulary"):
            salience_formula_v2(SalienceInputsV2(verification_pass_status="totally_made_up"))

    def test_prohibited_bare_pass_raises(self) -> None:
        with pytest.raises(ValueError):
            salience_formula_v2(SalienceInputsV2(verification_pass_status="pass"))

    def test_no_silent_fallback_to_documented_approximation(self) -> None:
        """The old behaviour: an unrecognized status quietly became 0.60. That
        must be gone -- it must raise, not return 0.60."""
        with pytest.raises(ValueError):
            salience_formula_v2(SalienceInputsV2(verification_pass_status="nonexistent_status"))


class TestVocabularyCoverage:
    """The CI-assertion half of the ruling (part 3): the table's coverage must
    equal the settled vocabulary's canonical members, or a future vocabulary
    addition silently reintroduces the fall-through defect."""

    def test_rescale_table_and_excluded_set_are_disjoint(self) -> None:
        assert set(VERIFICATION_RESCALE) & EXCLUDED_NO_VALUE_STATUSES == set()

    def test_rescale_table_plus_excluded_set_equals_canonical_vocabulary_members(self) -> None:
        covered = set(VERIFICATION_RESCALE) | EXCLUDED_NO_VALUE_STATUSES
        canonical_members = {canonical(s) for s in ALL_STATUSES}
        assert covered == canonical_members, (
            f"formulas.py's coverage has drifted from verification_vocab's canonical "
            f"members. Missing: {canonical_members - covered}; extra: {covered - canonical_members}"
        )

    def test_every_all_statuses_member_resolves_to_a_priced_or_excluded_canonical(self) -> None:
        """Exercise every single legal status (including the alias) through the
        real formula call, not just the canonical set -- this is what a live
        writer actually emits."""
        for status in ALL_STATUSES:
            result = salience_formula_v2(SalienceInputsV2(verification_pass_status=status))
            assert result["verification_rescale"] >= 0.0
