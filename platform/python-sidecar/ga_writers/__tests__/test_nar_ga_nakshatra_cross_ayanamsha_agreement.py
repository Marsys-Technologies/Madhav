"""
test_nar_ga_nakshatra_cross_ayanamsha_agreement.py — B-NAR-GA regression test
for the SAMĀPTI_NARRATION_TRIAGE_AND_PARTITION §4.2 P2 finding at
ga_nakshatra.py:289.

Prior defect: `agree_cnt = total_ay if len(unique) == 1 else 0` collapsed to a
literal 0 the instant ANY of the (usually 5) sidereal ayanamsha computations
for a graha disagreed on nakshatra id — even when e.g. 4 of 5 shared the same
id. That value is served verbatim as `chart_facts.nak_5ay_consistency`'s
`fact_value_text` (e.g. "0/5") and narrated by
platform-mcp/src/tools/registry_bridge.ts's readCrossAyanamshaFamily as
"holds the SAME nakshatra in 0 of the 5 sidereal ayanamshas" — a false report
of zero agreement when substantial (4/5) agreement existed.

The fix moves the computation into a pure, testable helper,
`compute_cross_ayanamsha_agreement` (ga_nakshatra_compute.py), which reports
the size of the largest agreeing subset (Counter mode count) instead of
flattening any disagreement to 0.

DB-free: this test exercises only the pure compute helper, not the writer's
`run_substep` (which requires a live DB cursor) — matching this repo's
convention of factoring DB-free pure algorithms into ga_nakshatra_compute.py
and testing them directly (see the sibling KP-lord/gandanta/tara/dispositor
tests already exercised via this module's own `_self_check()`).
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from ga_writers.ga_nakshatra_compute import compute_cross_ayanamsha_agreement  # noqa: E402


class TestComputeCrossAyanamshaAgreement:
    def test_unanimous_agreement_all_five(self):
        agree_cnt, total_ay = compute_cross_ayanamsha_agreement([25.0] * 5)
        assert (agree_cnt, total_ay) == (5, 5)

    def test_four_of_five_agree_reports_four_not_zero(self):
        # THE regression this test exists to lock: pre-fix code returned 0
        # here because len(unique) == 2 (not 1), even though 4 of 5 genuinely
        # agree. A caller narrating "0 of 5" for a chart with 4/5 real
        # agreement is the exact defect §4.2/§2 of the partition document
        # confirmed.
        agree_cnt, total_ay = compute_cross_ayanamsha_agreement(
            [25.0, 25.0, 25.0, 25.0, 26.0]
        )
        assert agree_cnt == 4, (
            f"Expected majority agree_cnt=4 for 4-of-5 partial agreement, got {agree_cnt} "
            "(the pre-fix defect returned 0 for any non-unanimous set)"
        )
        assert total_ay == 5

    def test_total_disagreement_reports_one_not_zero(self):
        # Every ayanamsha disagrees (all distinct) — the largest agreeing
        # subset has exactly 1 member. Still not 0: nothing agrees with
        # nothing, but each value trivially "agrees with itself" as the mode.
        agree_cnt, total_ay = compute_cross_ayanamsha_agreement(
            [21.0, 22.0, 23.0, 24.0, 25.0]
        )
        assert agree_cnt == 1
        assert total_ay == 5

    def test_majority_not_unanimous_three_of_five(self):
        agree_cnt, total_ay = compute_cross_ayanamsha_agreement(
            [10.0, 10.0, 10.0, 11.0, 12.0]
        )
        assert agree_cnt == 3
        assert total_ay == 5

    def test_empty_input(self):
        assert compute_cross_ayanamsha_agreement([]) == (0, 0)

    def test_never_returns_zero_agree_cnt_for_nonempty_input(self):
        # A structural invariant: agree_cnt must be >= 1 whenever there is at
        # least one value, since every value agrees with at least itself.
        # This is the property the pre-fix `else 0` branch violated.
        for nak_ids in (
            [1.0],
            [1.0, 2.0],
            [1.0, 1.0, 2.0, 3.0],
            [5.0, 5.0, 5.0, 5.0, 5.0],
        ):
            agree_cnt, _total = compute_cross_ayanamsha_agreement(nak_ids)
            assert agree_cnt >= 1, f"agree_cnt must never be 0 for nonempty input {nak_ids}"
