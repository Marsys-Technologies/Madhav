"""ph_sankrama: the stale domain map, the invented trajectory, and the honest row count.

Three defects found in W1 and fixed together because they share one shape: a value that
looked settled was actually asserting something nothing had measured.
"""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers.ph_sankrama import (
    _ANCHOR_TO_CDLM_DOMAIN,
    _KNOWN_UNMAPPED_ANCHOR_DOMAINS,
    _LINKAGE_THRESHOLD,
)
from services.ph_sankrama.engine import _trajectory

# Verified live against production 2026-09-05, both built charts.
ANCHOR_DOMAINS = frozenset({
    'career', 'character', 'health', 'relationship', 'spirituality', 'transition', 'wealth',
})
CDLM_DOMAIN_ROWS = frozenset({
    'career', 'character', 'education', 'family', 'health', 'progeny',
    'relationship', 'residence', 'spirituality', 'transition', 'travel',
})


class TestDomainMapping:
    def test_the_map_is_identity_because_the_vocabularies_converged(self) -> None:
        assert _ANCHOR_TO_CDLM_DOMAIN == {}

    @pytest.mark.parametrize("domain", sorted(ANCHOR_DOMAINS - {'wealth'}))
    def test_every_anchor_domain_but_wealth_resolves_to_a_real_cdlm_domain(self, domain: str) -> None:
        resolved = _ANCHOR_TO_CDLM_DOMAIN.get(domain, domain)
        assert resolved in CDLM_DOMAIN_ROWS, (
            f"anchor domain {domain!r} resolves to {resolved!r}, which CDLM does not have -- "
            "every such miss silently destroys that domain's spillover rows"
        )

    def test_transition_is_the_regression_this_fix_exists_for(self) -> None:
        """The old map sent 'transition' to 'general', a domain CDLM does not have.

        'transition' is the anchor domain with the MOST anchors (71 across both charts) and
        CDLM does have a 'transition' domain_row with 5 material cells -- so the entry turned
        a working match into a guaranteed miss, costing 355 rows (250 on the canonical chart,
        10% of the asset).
        """
        assert 'general' not in CDLM_DOMAIN_ROWS
        assert 'transition' in CDLM_DOMAIN_ROWS
        assert _ANCHOR_TO_CDLM_DOMAIN.get('transition', 'transition') == 'transition'

    def test_wealth_is_declared_a_known_divergence_not_left_to_look_like_a_bug(self) -> None:
        # CDLM genuinely has no 'wealth' domain_row, so those 26 anchors legitimately
        # produce nothing. B.10: that must be disclosed, not silently zero.
        assert 'wealth' not in CDLM_DOMAIN_ROWS
        assert _KNOWN_UNMAPPED_ANCHOR_DOMAINS == frozenset({'wealth'})

    def test_known_unmapped_set_contains_only_genuinely_unmappable_domains(self) -> None:
        """Guards the escape hatch: a domain must not be parked here to silence a real miss."""
        for domain in _KNOWN_UNMAPPED_ANCHOR_DOMAINS:
            assert domain not in CDLM_DOMAIN_ROWS, (
                f"{domain!r} IS a CDLM domain -- declaring it 'known unmapped' would suppress "
                "a disclosure for rows that should exist"
            )


class TestTrajectoryHonesty:
    def test_unknown_gradient_yields_none_not_stable(self) -> None:
        """§N.7 item 6. The upstream L2 column is 100% NULL, so `or 0.0` made 'stable' --
        a favourable-sounding verdict -- the only reachable branch for all 2,985 rows."""
        assert _trajectory(None) is None

    @pytest.mark.parametrize("gradient,expected", [
        (0.5, 'strengthening'),
        (0.11, 'strengthening'),
        (-0.5, 'weakening'),
        (-0.11, 'weakening'),
        (0.0, 'stable'),
        (0.05, 'stable'),
    ])
    def test_the_real_branches_are_unchanged_and_reachable(self, gradient: float, expected: str) -> None:
        assert _trajectory(gradient) == expected

    def test_zero_is_a_measurement_and_none_is_not(self) -> None:
        """The distinction the `or 0.0` coercion destroyed: a measured 0.0 gradient really is
        flat, and an absent one is unknown. They must not collapse to the same answer."""
        assert _trajectory(0.0) == 'stable'
        assert _trajectory(None) is None


def test_linkage_threshold_is_unchanged() -> None:
    """The volume formula in migration 681 cites this constant; a silent change to it would
    invalidate the expected_volume_inputs without touching the migration."""
    assert _LINKAGE_THRESHOLD == 0.25
