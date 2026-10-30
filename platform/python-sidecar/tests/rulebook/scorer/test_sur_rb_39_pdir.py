"""SUR-RB-39 (3). Full ruling: (1) masks-only reading rule for coverage, percentiles and D8; (2) the own chart's applicable unit set
defines the (b)/(c) coverage and donor eligibility; (3) p_dir averages only episodes with defined own and opposite
scores; (4) the q = 30% sanity check per testable family, with the q-curve on a shortfall."""

from __future__ import annotations

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, assemble, donor_sets, reading_coverage, run_donor_check, scorable_mask
from services.rulebook.scorer.footprint import unit_touch
from services.rulebook.scorer.model import ChartTimeline, Episode, MemberSpec, UnitSpec

from ._toy import BASE, month_window, runs_series

CAREER = "career_adv_change_entry"


def _unit(uid, groups, pol="promotive", tags=None):
    gs = tuple(tuple(MemberSpec(r, frozenset(tags or [C.GENERAL])) for r in g) for g in groups)
    return UnitSpec(uid, C.FAMILY_DASHA, pol, "cluster", gs)


# ── (3) p_dir averages episodes with defined own AND opposite scores only ───────────────────────────────────
def test_3_p_dir_drops_an_episode_whose_opposite_score_is_undefined_by_carve_out_3():
    n = 365 * 8
    rng = np.random.default_rng(5)
    units = [_unit("P", [["MP"]]), _unit("O", [["MO"]], pol="obstructive")]
    t = ChartTimeline("c", BASE - 9000, BASE, BASE + n - 1, {"MP": runs_series(rng, n, 0.25, 10), "MO": np.zeros(n, dtype=np.int8)})
    t.states["MO"][1900:] = runs_series(rng, n - 1900, 0.25, 10)  # opposite member constant (never TRUE) in block 0
    ctx = FamilyContext(C.FAMILY_DASHA, [t], units)
    e0 = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1991, 6))  # block 0: opposite applicable but constant
    e1 = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1996, 6))  # block 1: opposite informative
    asm = assemble(ctx, "5y", [e0, e1], True, False, dir_eligible=[True, True])
    rec0 = next(r for r in asm.recs if r["blk"] == 0)
    rec1 = next(r for r in asm.recs if r["blk"] == 1)
    assert np.all(rec0["BD"] == 0.0)  # e0 contributes nothing to the direction statistic (dropped, not zero-filled)
    assert np.any(rec1["BD"] != 0.0)
    # and the drop is draw-invariant: e0's shift set is not narrowed by the opposite mask
    no_dir = assemble(ctx, "5y", [e0, e1], False, False)
    assert next(r for r in no_dir.recs if r["blk"] == 0)["shifts"].size == rec0["shifts"].size


