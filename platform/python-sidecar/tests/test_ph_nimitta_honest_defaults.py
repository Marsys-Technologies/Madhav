"""ph_nimitta: two favourable-sounding values asserted on no evidence (§N.7 item 6).

Both are the same defect in different clothes -- a default chosen for how it READS rather
than for being the codebase's own neutral convention.
"""
from __future__ import annotations

import pytest

from services.ph_nimitta.engine import _promise_lift


class TestPromiseLiftNeutrality:
    def test_no_evidence_is_exactly_neutral(self) -> None:
        assert _promise_lift(0.0, 'no_evidence') == 1.0

    def test_the_substituted_default_was_a_75_percent_amplification(self) -> None:
        """The writer used to substitute grade=5.0 / status='conditional' whenever no
        bodha_pratijna row existed -- which is a 1.75x posterior lift derived from nothing,
        on 54 of 139 anchors. This test pins WHY that substitution was wrong, so the value
        cannot quietly come back."""
        assert _promise_lift(5.0, 'conditional') == 1.75
        assert _promise_lift(5.0, 'conditional') > _promise_lift(0.0, 'no_evidence')

    @pytest.mark.parametrize("grade,status,expected", [
        (0.0, 'no_evidence', 1.0),
        (10.0, 'no_evidence', 1.0),      # no_evidence ignores grade entirely
        (0.0, 'conditional', 1.0),
        (10.0, 'promised', 2.5),
    ])
    def test_the_real_branches_are_unchanged(self, grade: float, status: str, expected: float) -> None:
        assert _promise_lift(grade, status) == expected

    def test_a_real_pratijna_row_still_lifts(self) -> None:
        """The fix must not flatten genuine evidence -- only absent evidence."""
        assert _promise_lift(8.0, 'promised') > 1.0


class TestDiscoveryDirectionIsNotInvented:
    """bodha_discoveries carries NO direction, valence or probability column (verified against
    the live catalogue), so a discovery-sourced anchor has nothing to derive a direction from.
    It used to assert 'elevated' -- the favourable one -- for every such anchor."""

    def test_the_writer_no_longer_hardcodes_a_favourable_direction(self) -> None:
        import inspect
        from services.ph_nimitta import engine
        src = inspect.getsource(engine.derive_anchor_from_discovery)
        assert "direction='elevated'" not in src
        assert "direction='mixed'" in src

    def test_the_contradiction_fallback_is_neutral_too(self) -> None:
        import inspect
        from services.ph_nimitta import engine
        src = inspect.getsource(engine.derive_anchor_from_discovery)
        assert "ctx.contradiction_net or 'elevated'" not in src
        assert "ctx.contradiction_net or 'mixed'" in src

    def test_mixed_is_the_codebases_own_neutral_convention(self) -> None:
        """Not an invented third option -- the convergence path already fixed this same
        defect (P0-11) and settled on 'mixed'. The discovery path was simply left behind."""
        import inspect
        from services.ph_nimitta import engine
        src = inspect.getsource(engine)
        assert "'elevated', 'suppressed', 'mixed'" in src or '"elevated", "suppressed", "mixed"' in src
