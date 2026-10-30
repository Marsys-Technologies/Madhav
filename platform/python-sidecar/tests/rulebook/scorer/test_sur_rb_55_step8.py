"""SUR-RB-54 R1/R2 and SUR-RB-55: the step-8 invocation builds both episode lists exactly as count_blind builds its two
sets (checked against count_blind's own count_chart on synthetic rows that mix schedulable and non-schedulable
occurrences within one area and one merge window), and checks each family's pool before the claim."""

from __future__ import annotations

import importlib.util
import random
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.model import Episode
from services.rulebook.step8 import run_step8 as S8

PIPELINE = Path("/Users/Dev/Archives/madhav-research-library/10_engine/admission-v1_1/pipeline/count_blind.py")
COUNT_BLIND_V3 = "41ea7d8e4676b8f4b8e97be0c0abc1ced29c0fdd593f57f3af19e5ee1d56616a"


def _count_blind_module():
    import hashlib

    assert hashlib.sha256(PIPELINE.read_bytes()).hexdigest() == COUNT_BLIND_V3  # the logged count_blind V3
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("count_blind_v3_reference", PIPELINE)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(PIPELINE.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(PIPELINE.parent))
    return mod


def _mixed_rows(seed=7, n=3000):
    """Several charts; within one chart, area and direction, schedulable and non-schedulable occurrences alternate
    inside the same 31-day merge window and the same calendar month, plus G3 rows and mixed directions."""
    rng = random.Random(seed)
    codes = ["X%02d" % i for i in range(5)]
    hz = {c: (date(1990, 1, 10) + timedelta(days=rng.randint(0, 40)), date(2010, 6, 15) - timedelta(days=rng.randint(0, 40))) for c in codes}
    rows = []
    for _ in range(n):
        c = rng.choice(codes)
        g = rng.choice(["day", "day", "day", "month", "year"])
        base = date(1989, 6, 1) + timedelta(days=rng.randint(0, 365 * 22))
        area, direction = rng.choice(["career", "health"]), rng.choice(["favourable", "unfavourable", "mixed"])
        for k in range(rng.randint(1, 3)):  # a burst: same key, days apart, alternating categories
            d = base + timedelta(days=k * rng.randint(3, 20))
            if g == "month":
                d = date(d.year, d.month, 1)
            rows.append((c, g, None if g == "year" else d, area, direction, (k % 2 == 0) if rng.random() < 0.8 else rng.random() < 0.5))
    return codes, hz, rows


def _reference(cbm, codes, hz, rows):
    """count_blind's own count_chart, episode counts per (set, chart, area, direction, grade)."""
    ref = Counter()
    for c in codes:
        occs = [{"date": (d.isoformat() if g == "day" else (f"{d.year:04d}-{d.month:02d}" if g == "month" else "")), "grade": g, "area": a,
                 "direction": dr, "schedulable": s} for (cid, g, d, a, dr, s) in rows if cid == c]
        agg, *_ = cbm.count_chart(occs, {"dasha": hz[c]}, {}, {}, hz[c][0])
        for (fam, st, area, direction, grade), v in agg.items():
            if v.get("episodes"):
                ref[(st, c, area, direction, grade)] += v["episodes"]
    return ref


@pytest.mark.skipif(not PIPELINE.exists(), reason="count_blind V3 source not on this machine")
def test_r1_both_lists_equal_count_blinds_sets_on_rows_mixing_both_kinds():
    cbm = _count_blind_module()
    codes, hz, rows = _mixed_rows()
    ref = _reference(cbm, codes, hz, rows)
    mine = Counter()
    for st in ("all", "primary_nonschedulable"):
        eps, _g3 = S8.family_episodes(rows, codes, hz, "dasha", C, Episode, st)
        for e in eps:
            mine[(st, codes[e.chart], e.area, e.direction, {C.G1: "day", C.G2: "month"}[e.grade])] += 1
    assert mine == ref
    # the mixing is real: somewhere the separate list differs from any labelling of the 'all' episodes
    differs = sum(1 for k in ref if k[0] == "primary_nonschedulable" and ref[k] != ref.get(("all",) + k[1:], 0))
    assert differs > 0


def test_r1_drop_before_merge_on_a_hand_made_case():
    d0 = date(2000, 3, 10)
    hz = {"X": (date(1999, 1, 1), date(2005, 1, 1))}
    # schedulable on day 0, non-schedulable on days 20 and 45: 'all' merges 0+20 and starts again at 45 (2 episodes);
    # the non-schedulable set merges 20+45 (25 days apart): 1 episode starting on day 20
    rows = [("X", "day", d0, "career", "favourable", True), ("X", "day", d0 + timedelta(days=20), "career", "favourable", False),
            ("X", "day", d0 + timedelta(days=45), "career", "favourable", False)]
    a, _ = S8.family_episodes(rows, ["X"], hz, "dasha", C, Episode, "all")
    n, _ = S8.family_episodes(rows, ["X"], hz, "dasha", C, Episode, "primary_nonschedulable")
    assert [date.fromordinal(e.lo + 1) for e in a] == [d0, d0 + timedelta(days=45)]
    assert [date.fromordinal(e.lo + 1) for e in n] == [d0 + timedelta(days=20)]
    assert all(e.schedulable is False for e in a + n)  # no label is read by the scorer


def test_r1_unknown_set_refuses():
    with pytest.raises(S8.Stop):
        S8.family_episodes([], [], {}, "dasha", C, Episode, "something")


def test_r2_the_pool_must_be_inside_s6_and_free_of_horizon_exclusions():
    assert S8.check_pool("dasha", ["C2", "C1"], ["C1", "C2", "C3"], ["C1", "C2"]) == ["C1", "C2"]
    with pytest.raises(S8.Stop, match="s6_admit"):
        S8.check_pool("dasha", ["C1", "C9"], ["C1", "C2"], ["C1", "C2", "C9"])
    with pytest.raises(S8.Stop, match="horizon exclusions"):
        S8.check_pool("dasha", ["C1", "C3"], ["C1", "C2", "C3"], ["C1", "C2"])


def test_the_script_names_the_candidate_scorer_and_sends_the_list_in_the_lock():
    src = Path(S8.__file__).read_text()
    assert S8.FROZEN_SCORER_SHA256 == C.source_sha256()
    assert "nonschedulable_episodes=ns_episodes" in src and "nonschedulable_count_rows=ns_rows" in src
    assert "all_members_schedulable" not in src
