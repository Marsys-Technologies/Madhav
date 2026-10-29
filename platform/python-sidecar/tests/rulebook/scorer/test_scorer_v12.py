"""Yardstick v1.2 rules in the scorer: K4 direction floor, K5 Z25, K6 donors, K10 blocks, K11 donor floors."""

from __future__ import annotations

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import (
    FamilyContext,
    direction_counts,
    donor_eligibility_counts,
    make_blocks,
    run_donor_check,
    score_family,
)
from services.rulebook.scorer.footprint import family_testable
from services.rulebook.scorer.model import ChartTimeline, Episode
from services.rulebook.scorer.outcome import LABEL_DIR_UNTESTABLE, LABEL_NOT_DIRECTION, MIDDLE, STRONG, decide

from ._toy import BASE, make_units, month_window, random_episodes, runs_series, toy_world

AREAS = ["career_adv_change_entry", "illness_chronic_surgery"]


def test_k10_block_rules():
    assert C.MERGE_BELOW_5Y == 913 and C.MERGE_BELOW_15Y == 2740
    assert make_blocks(5479 + 2739, 5479, 2740) == [(0, 5479 + 2738)]  # 2,739 days left over: merged
    assert make_blocks(5479 + 2740, 5479, 2740) == [(0, 5478), (5479, 8218)]  # 2,740: stands alone
    assert make_blocks(3000, 5479, 2740) == [(0, 2999)]  # a horizon shorter than one block is one block
    assert make_blocks(1826 + 912, 1826, 913) == [(0, 2737)]


def test_k5_z25_needs_eight_units_and_uses_ceiling_of_a_quarter():
    tls, units = toy_world(1, n_charts=16, years=25, n_units=4)
    eps = random_episodes(np.random.default_rng(1), tls, 14, AREAS)
    r = score_family(FamilyContext(C.FAMILY_DASHA, tls, units), eps, C.ScoreConfig(draws=200, seed=1))
    assert r["z25_units"] < 8 and "Z25-5y" not in r["stats"] and "Z25-15y" not in r["stats"]
    assert set(r["stats"]) == {"T-5y", "T-15y"}  # min-p over T alone
    tls, units = toy_world(1, n_charts=16, years=25, n_units=12)
    eps = random_episodes(np.random.default_rng(1), tls, 14, AREAS)
    r = score_family(FamilyContext(C.FAMILY_DASHA, tls, units), eps, C.ScoreConfig(draws=200, seed=1))
    assert r["z25_units"] >= 8 and "Z25-5y" in r["stats"]


def test_k4_direction_floor_counts_and_label():
    tls, units = toy_world(2, n_charts=18, years=25, n_units=8)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(2), tls, 12, AREAS)
    d = direction_counts(ctx, eps)
    assert d["testable"] and d["episodes"] >= 100 and d["charts"] >= 15
    few = [e for e in eps if e.chart < 14]  # 14 charts: below the floor of 15 whatever the episodes
    assert direction_counts(ctx, few)["testable"] is False
    r = score_family(ctx, few, C.ScoreConfig(draws=200, seed=1))
    assert r["dir_testable"] is False and r["p_dir"] is None and r["T_dir"] is None
    few100 = [e for e in eps if e.chart < 18][:99]
    assert direction_counts(ctx, few100)["testable"] is False
    # an episode with no applicable opposite-polarity unit is not counted
    only_prom = make_units([("U0", "promotive", [[("M0", [C.GENERAL])]])])
    ctx2 = FamilyContext(C.FAMILY_DASHA, tls, only_prom)
    assert direction_counts(ctx2, [e for e in eps if e.direction == C.FAVOURABLE])["episodes"] == 0


def test_k4_family_meeting_strong_without_testable_direction_is_middle_with_its_label():
    r = {"p1": 0.001, "p2": 0.01, "p3": 0.01, "p_dir": None, "dir_testable": False}
    v = decide({"dasha": r}, {"dasha": True})
    assert v["outcome"] == MIDDLE and LABEL_DIR_UNTESTABLE in v["labels"] and LABEL_NOT_DIRECTION not in v["labels"]
    r2 = dict(r, p_dir=0.5, dir_testable=True)
    v2 = decide({"dasha": r2}, {"dasha": True})
    assert v2["outcome"] == MIDDLE and LABEL_NOT_DIRECTION in v2["labels"]
    assert decide({"dasha": dict(r, p_dir=0.01, dir_testable=True)}, {"dasha": True})["outcome"] == STRONG


def _donor_world(n_charts, years=12):
    rng = np.random.default_rng(3)
    units = make_units([("U0", "promotive", [[("M0", [C.GENERAL])]]), ("U1", "obstructive", [[("M1", [C.GENERAL])]])])
    tls = []
    for c in range(n_charts):
        n = 365 * years
        t = ChartTimeline(f"c{c}", BASE - 9000 + c, BASE + c, BASE + c + n - 1)
        t.states["M0"] = runs_series(rng, n, 0.2, 15)
        t.states["M1"] = runs_series(rng, n, 0.2, 15)
        tls.append(t)
    return tls, units


def test_k11_donor_floors_make_a_family_untestable():
    tls, units = _donor_world(16)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = [Episode(c, AREAS[0], C.FAVOURABLE, C.G2, *month_window(1991, 1 + (c + k) % 12)) for c in range(16) for k in range(20)]
    cnt = donor_eligibility_counts(ctx, eps)
    assert cnt == {"b": 16, "c": 16}
    assert family_testable(ctx, eps)["testable"] is True
    # K6: donors are the ADMITTED charts only; with 6 admitted charts each has 5 donors, with 5 admitted each has 4
    assert donor_eligibility_counts(ctx, [e for e in eps if e.chart < 6], range(6)) == {"b": 6, "c": 6}
    assert donor_eligibility_counts(ctx, [e for e in eps if e.chart < 5], range(5)) == {"b": 0, "c": 0}
    # 14 charts: below the 15-chart floor even though each has plenty of donors
    ctx14 = FamilyContext(C.FAMILY_DASHA, tls[:14], units)
    eps14 = [e for e in eps if e.chart < 14]
    ft = family_testable(ctx14, eps14, min_episodes=1)
    assert ft["testable"] is False and ft["donor_charts_b"] == 14 and any("eligible donors" in x for x in ft["reasons"])
    # the floor applies to (b) AND (c) separately: shift one side out of reach
    for t in tls[:2]:
        t.birth -= 20000  # age matching would need ages far outside every donor's horizon
    ctx2 = FamilyContext(C.FAMILY_DASHA, tls, units)
    cnt2 = donor_eligibility_counts(ctx2, eps)
    assert cnt2["b"] == 16 and cnt2["c"] < 16


def test_k6_a_non_admitted_chart_is_never_a_donor():
    tls, units = _donor_world(12)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = [Episode(c, AREAS[0], C.FAVOURABLE, C.G2, *month_window(1991, 1 + (c + k) % 12)) for c in range(12) for k in range(5)]
    adm = [c for c in range(12) if c != 3]
    full = run_donor_check(ctx, eps, 200, np.random.default_rng(1), False)
    part = run_donor_check(ctx, [e for e in eps if e.chart != 3], 200, np.random.default_rng(1), False, admitted=adm)
    assert 3 in full["included_charts"] and 3 not in part["included_charts"]
    assert part["T"] != full["T"]
    # making chart 3's timeline wildly different must not move T when it is not admitted
    tls[3].states["M0"] = np.ones_like(tls[3].states["M0"])
    ctx_b = FamilyContext(C.FAMILY_DASHA, tls, units)
    part_b = run_donor_check(ctx_b, [e for e in eps if e.chart != 3], 200, np.random.default_rng(1), False, admitted=adm)
    assert part_b["T"] == pytest.approx(part["T"], abs=1e-12)


def test_v13_d7_decisions_from_the_sealed_counts_override_the_recount():
    tls, units = toy_world(5, n_charts=18, years=25, n_units=12)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(5), tls, 14, AREAS)
    base = score_family(ctx, eps, C.ScoreConfig(draws=200, seed=1))
    assert base["dir_testable"] and base["p_dir"] is not None and "Z25-5y" in base["stats"]
    # D7 says direction is not testable and lists only 7 units for Z25: p_dir is None and Z25 is dropped (n < 8)
    ids = sorted(u.unit_id for u in ctx.units)
    r = score_family(ctx, eps, C.ScoreConfig(draws=200, seed=1), d7={"dir_testable": False, "z25_units": ids[:7]})
    assert r["dir_testable"] is False and r["p_dir"] is None and "Z25-5y" not in r["stats"]
    r8 = score_family(ctx, eps, C.ScoreConfig(draws=200, seed=1), d7={"z25_units": ids[:8]})
    assert "Z25-5y" in r8["stats"] and r8["p_dir"] is not None
    # T does not depend on the D7 lists
    assert r["stats"]["T-5y"] == base["stats"]["T-5y"]
