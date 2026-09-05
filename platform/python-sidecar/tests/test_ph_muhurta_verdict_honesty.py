"""ph_muhurta: the verdict that could only ever read 'mediocre'.

Both tarabala and chandrabala default to the 0.5 JL-016 placeholder when no live
transit-Moon lookup is available, so the geometric mean is pinned at exactly 0.5 and caps
composite_quality at 0.5 -- below the 0.55 'adequate' threshold. Measured live before this
fix: 'mediocre' on 134/134 canonical rows and 49/49 Abhinandan rows. One of the four values
the CHECK constraint permits was reachable.
"""
from __future__ import annotations

import pytest

from services.ph_muhurta.engine import (
    _GENUINE_THRESHOLD,
    _STRONG_THRESHOLD,
    classify_verdict,
    compute_composite_quality,
)

PLACEHOLDER = 0.5


class TestPlaceholderYieldsNoGrade:
    def test_verdict_is_null_when_moon_strength_was_never_measured(self) -> None:
        verdict, reason = classify_verdict(0.26, tara_chandra_known=False)
        assert verdict is None, "an unmeasured Moon-strength factor must not produce a grade"
        assert reason is not None

    def test_the_reason_names_the_missing_input_not_an_astrological_story(self) -> None:
        """The old reason said 'Moon may be afflicted or no fixed nakshatra available' --
        attributing the low score to the chart when nothing had computed Moon strength at
        all. §N.7 item 6: not a missing value, but a plausible story told over one."""
        _, reason = classify_verdict(0.26, tara_chandra_known=False)
        assert reason is not None
        assert 'placeholder' in reason.lower()
        assert 'afflicted' not in reason.lower()

    def test_a_real_lookup_still_grades_normally(self) -> None:
        assert classify_verdict(0.90, tara_chandra_known=True)[0] == 'strong'
        assert classify_verdict(0.60, tara_chandra_known=True)[0] == 'adequate'
        assert classify_verdict(0.26, tara_chandra_known=True)[0] == 'mediocre'
        assert classify_verdict(0.0, tara_chandra_known=True)[0] == 'none_genuine'

    def test_grading_is_the_default_so_the_null_path_is_opt_in(self) -> None:
        # A caller that does not know about the placeholder still gets the old behaviour,
        # rather than silently losing every verdict.
        assert classify_verdict(0.90)[0] == 'strong'


class TestTheCeilingThisFixExistsFor:
    def test_the_placeholder_caps_composite_below_the_adequate_threshold(self) -> None:
        """With both factors at the placeholder, even a PERFECT score on every other term
        cannot reach 'adequate'. This is the arithmetic that made three of four verdicts
        unreachable."""
        best_possible = compute_composite_quality(
            panchanga_score=1.0,
            chart_personalization_score=1.0,
            personal_adversity_penalty=0.0,
            tarabala_score=PLACEHOLDER,
            chandrabala_score=PLACEHOLDER,
        )
        assert best_possible == pytest.approx(0.5)
        assert best_possible < _GENUINE_THRESHOLD
        assert best_possible < _STRONG_THRESHOLD
        # ...and under the OLD code that ceiling still produced a confident-looking grade.
        assert classify_verdict(best_possible, tara_chandra_known=True)[0] == 'mediocre'
        # Under the new code it produces none.
        assert classify_verdict(best_possible, tara_chandra_known=False)[0] is None

    def test_a_real_lookup_can_exceed_the_ceiling(self) -> None:
        """Proves the ceiling is the placeholder's doing, not the formula's."""
        real = compute_composite_quality(
            panchanga_score=1.0,
            chart_personalization_score=1.0,
            personal_adversity_penalty=0.0,
            tarabala_score=1.0,
            chandrabala_score=1.0,
        )
        assert real > _STRONG_THRESHOLD
        assert classify_verdict(real, tara_chandra_known=True)[0] == 'strong'
