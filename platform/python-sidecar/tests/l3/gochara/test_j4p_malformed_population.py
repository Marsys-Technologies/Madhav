"""J4P-B4 audit: independent verification validates before horizon/range cuts."""
from datetime import timedelta

import pytest

from services.gochara_kernel import inventory_verifier as verifier
from tests.l3.gochara.test_j4p_dasha_settlement import BUILD, CHART, LO, HI, row


@pytest.mark.parametrize("side", ["consumed", "pinned"])
@pytest.mark.parametrize("start,end", [
    (LO, LO), (HI, LO), (None, HI), (LO, None),
    # Entirely outside the horizon: still corrupt admitted input.
    (HI + timedelta(days=10), HI + timedelta(days=9)),
])
def test_malformed_period_is_a_violation_before_horizon_filtering(side, start, end):
    good = row(BUILD)
    bad = dict(good, dasha_row_id="bad", start_iso=start, end_iso=end)
    consumed = [good] + ([bad] if side == "consumed" else [])
    pinned = [good] + ([bad] if side == "pinned" else [])
    problems = verifier.check_dasha_population(
        consumed, pinned, chart_id=CHART, horizon=(LO, HI),
        consumed_ids=[r["dasha_row_id"] for r in consumed])
    assert any("invalid period" in problem for problem in problems), problems


def test_valid_population_unchanged():
    good = row(BUILD)
    assert verifier.check_dasha_population(
        [good], [good], chart_id=CHART, horizon=(LO, HI),
        consumed_ids=[good["dasha_row_id"]]) == []


@pytest.mark.parametrize("start,end,reason", [
    ("invalid", HI, "no datetime boundary"),
    (LO.replace(tzinfo=None), HI, "timezone-aware"),
])
def test_f2_boundary_normalization_has_a_typed_refusal(start, end, reason):
    from services.kala_core import clocks
    bad = dict(row(BUILD), start_iso=start, end_iso=end)
    with pytest.raises(clocks.ClockUnavailable, match=reason):
        clocks.validate_clock_rows([bad], build_id=BUILD, tier="two_pass_verified")
