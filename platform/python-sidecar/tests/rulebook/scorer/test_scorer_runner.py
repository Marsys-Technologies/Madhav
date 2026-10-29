"""Footprint gate, testability, the one-run ledger, the dry run, the scorer hash."""

from __future__ import annotations

import json
import os
import stat

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext
from services.rulebook.scorer.footprint import descriptive_hits, family_testable, gate_from_touch, pooled_touch, touch_rates
from services.rulebook.scorer.model import ChartTimeline, Episode
from services.rulebook.scorer.runner import RunLedger, RunRefused, mechanical_dry_run, sample_sha256, score_sample, write_result

from ._toy import BASE, make_units, month_window, random_episodes, runs_series, toy_world

AREAS = ["career_adv_change_entry", "illness_chronic_surgery"]


# ── footprint ───────────────────────────────────────────────────────────────────────────
def test_touch_rate_of_a_known_series():
    n = 400
    st = np.zeros(n, dtype=np.int8)
    st[100] = 1  # one TRUE day touches exactly three 3-day windows
    u = make_units([("U", "promotive", [[("M", [C.GENERAL])]])])
    t = ChartTimeline("c", BASE - 100, BASE, BASE + n - 1, {"M": st})
    tr = touch_rates([t], u)["U"]
    assert tr["3d"] == pytest.approx(3 / (n - 2))
    mths = [m for m in range(1, 14) if True]
    # the one TRUE day (BASE+100 = 2020-04-11) lies in one of the whole calendar months inside the horizon
    from datetime import date

    d = date.fromordinal(BASE + 100)
    assert tr["month"] == pytest.approx(1 / _count_months(BASE, BASE + n - 1))


def _count_months(lo, hi):
    from datetime import date

    k = 0
    d0 = date.fromordinal(lo)
    y, m = (d0.year, d0.month) if d0.day == 1 else ((d0.year + (d0.month == 12)), d0.month % 12 + 1)
    while True:
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        if date(ny, nm, 1).toordinal() - 1 > hi:
            return k
        k += 1
        y, m = ny, nm


def test_gate_drops_a_unit_above_sixty_percent_per_window_class_by_mean_over_charts():
    n = 900
    u = make_units([("BUSY", "promotive", [[("B", [C.GENERAL])]]), ("QUIET", "promotive", [[("Q", [C.GENERAL])]])])
    rng = np.random.default_rng(1)
    tls = []
    for c in range(4):
        t = ChartTimeline(f"c{c}", BASE - 100, BASE, BASE + n - 1)
        t.states["B"] = (rng.random(n) < 0.6).astype(np.int8)  # nearly every 3-day window touched, every month touched
        t.states["Q"] = np.zeros(n, dtype=np.int8)
        t.states["Q"][::90] = 1
        tls.append(t)
    touch = touch_rates(tls, u)
    drop = gate_from_touch(touch)
    assert drop == {"BUSY": frozenset({C.G1, C.G2})}
    assert touch["QUIET"]["3d"] < 0.1
    # a unit whose 3-day rate is under the gate but whose month rate is over it is dropped for G2 only
    drop2 = gate_from_touch({"X": {"3d": 0.5, "month": 0.9}, "Y": {"3d": 0.61, "month": None}})
    assert drop2 == {"X": frozenset({C.G2}), "Y": frozenset({C.G1})}
    p = pooled_touch(touch)  # reported, never gated
    assert 0 < p["3d"] < 1


def test_gated_unit_leaves_the_episode_class_for_that_grade_only():
    u = make_units([("A", "promotive", [[("MA", [C.GENERAL])]]), ("B", "promotive", [[("MB", [C.GENERAL])]])])
    t = ChartTimeline("c", BASE - 100, BASE, BASE + 1000, {"MA": np.zeros(1001, dtype=np.int8), "MB": np.zeros(1001, dtype=np.int8)})
    ctx = FamilyContext(C.FAMILY_DASHA, [t], u, gate_drop={"A": frozenset({C.G1})})
    assert [v.unit_id for v in ctx.klass_variants(("promotive", "x", C.G1))] == ["B"]
    assert [v.unit_id for v in ctx.klass_variants(("promotive", "x", C.G2))] == ["A", "B"]


def test_testability_needs_250_episodes_in_15_charts_and_half_the_units():
    tls, units = toy_world(5, n_charts=16, years=20, n_units=6)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    mk = lambda n: [Episode(c % 16, AREAS[0], C.FAVOURABLE, C.G2, *month_window(1995, 1 + k % 12)) for k, c in enumerate(range(n))]
    assert family_testable(ctx, mk(250))["testable"] is True
    assert family_testable(ctx, mk(249))["testable"] is False
    few_charts = [Episode(c % 14, AREAS[0], C.FAVOURABLE, C.G2, *month_window(1995, 1 + c % 12)) for c in range(300)]
    assert family_testable(ctx, few_charts)["testable"] is False  # only 14 charts
    gated = FamilyContext(C.FAMILY_DASHA, tls, units, gate_drop={u.unit_id: frozenset({C.G2}) for u in units[:4]})
    r = family_testable(gated, mk(300))  # 4 of 6 units dropped for the only used grade
    assert r["testable"] is False and r["units_surviving"] == 2
    gated2 = FamilyContext(C.FAMILY_DASHA, tls, units, gate_drop={u.unit_id: frozenset({C.G2}) for u in units[:3]})
    assert family_testable(gated2, mk(300))["testable"] is True  # exactly half survive


def test_descriptive_hits_report_O_E_without_testing():
    tls, units = toy_world(6, n_charts=6, years=15, n_units=4)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(1), tls, 6, AREAS)
    from services.rulebook.scorer.core import scorable_mask

    scored = [e for e, ok in zip(eps, scorable_mask(ctx, eps)) if ok]
    d = descriptive_hits(ctx, scored)
    assert d["member_episodes"] > 0 and 0 <= d["O"] <= d["member_episodes"] and d["E"] > 0
    assert 0.4 < d["O_over_E"] < 2.5  # random placement: observed close to expected


# ── ledger: no second run on the same sample ────────────────────────────────────────────
def _small_sample(seed=1, n_charts=22, per_chart=20):
    tls, units = toy_world(seed, n_charts=n_charts, years=25, n_units=6)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(seed), tls, per_chart, AREAS)
    return ctx, eps


def test_second_run_on_the_same_sample_is_refused(tmp_path):
    ctx, eps = _small_sample()
    ledger = RunLedger(str(tmp_path / "ledger"))
    cfg = C.ScoreConfig(draws=200, seed=1)
    res = score_sample({C.FAMILY_DASHA: ctx}, {C.FAMILY_DASHA: eps}, cfg, ledger)
    assert res["outcome"] in {"STRONG", "MIDDLE", "CHANCE-LEVEL", "NO_VERDICT"}
    assert res["scorer_source_sha256"] == C.source_sha256()
    with pytest.raises(RunRefused):
        score_sample({C.FAMILY_DASHA: ctx}, {C.FAMILY_DASHA: eps}, cfg, ledger)
    # a different seed or a different draw count is still the same sample
    with pytest.raises(RunRefused):
        score_sample({C.FAMILY_DASHA: ctx}, {C.FAMILY_DASHA: eps}, C.ScoreConfig(draws=500, seed=2), ledger)
    # the same episodes in another order are the same sample
    with pytest.raises(RunRefused):
        score_sample({C.FAMILY_DASHA: ctx}, {C.FAMILY_DASHA: list(reversed(eps))}, cfg, ledger)
    # one more episode is a different sample
    extra = eps + [Episode(0, AREAS[0], C.FAVOURABLE, C.G1, eps[0].lo + 40, eps[0].lo + 42)]
    assert RunLedger(str(tmp_path / "ledger")).has(sample_sha256({C.FAMILY_DASHA: ctx.tl}, {C.FAMILY_DASHA: eps}))
    assert sample_sha256({C.FAMILY_DASHA: ctx.tl}, {C.FAMILY_DASHA: extra}) != sample_sha256({C.FAMILY_DASHA: ctx.tl}, {C.FAMILY_DASHA: eps})


def test_a_run_that_crashes_after_the_claim_still_counts_as_run(tmp_path):
    ctx, eps = _small_sample(2)
    ledger = RunLedger(str(tmp_path / "ledger"))
    bad = [Episode(0, AREAS[0], "mixed", C.G1, 1, 3)] + eps  # mixed direction: refused inside the scorer
    with pytest.raises(Exception):
        score_sample({C.FAMILY_DASHA: ctx}, {C.FAMILY_DASHA: bad}, C.ScoreConfig(draws=100, seed=1), ledger)
    with pytest.raises(RunRefused):
        score_sample({C.FAMILY_DASHA: ctx}, {C.FAMILY_DASHA: bad}, C.ScoreConfig(draws=100, seed=1), ledger)


def test_below_the_minimum_there_is_no_verdict_and_no_statistic(tmp_path):
    tls, units = toy_world(3, n_charts=12, years=20, n_units=4)  # 12 charts < 20
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(1), tls, 40, AREAS)
    res = score_sample({C.FAMILY_DASHA: ctx}, {C.FAMILY_DASHA: eps}, C.ScoreConfig(draws=100, seed=1), RunLedger(str(tmp_path / "l")))
    assert res["outcome"] == "NO_VERDICT" and "families" not in res and "minimum not met" in res["reason"]


def test_ledger_files_are_private_and_result_file_is_written_once(tmp_path):
    ledger = RunLedger(str(tmp_path / "ledger"))
    p = ledger.claim("a" * 64, C.source_sha256(), "x")
    assert stat.S_IMODE(os.stat(p).st_mode) == 0o600
    out = str(tmp_path / "result.json")
    sha = write_result({"k": 1}, out)
    assert len(sha) == 64 and stat.S_IMODE(os.stat(out).st_mode) == 0o600
    with pytest.raises(FileExistsError):
        write_result({"k": 2}, out)  # never overwritten


# ── mechanical dry run ───────────────────────────────────────────────────────────────────
def _keys(obj, acc):
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.add(k)
            _keys(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _keys(v, acc)
    return acc


def test_dry_run_checks_invariants_and_returns_no_statistics():
    ctx, eps = _small_sample(4, n_charts=10, per_chart=8)
    out = mechanical_dry_run({C.FAMILY_DASHA: ctx}, {C.FAMILY_DASHA: eps})
    assert out["dry_run"] and out["statistics_kept"] is False
    assert out["families"][C.FAMILY_DASHA]["invariants_hold"] is True
    banned = {"p1", "p2", "p3", "p_dir", "T", "T2", "T3", "stats", "null_mean", "p_stat"}
    assert not (_keys(out, set()) & banned)
    assert json.dumps(out)  # serialisable


# ── the scorer's own hash ───────────────────────────────────────────────────────────────────
def test_source_hash_covers_every_scorer_module():
    import pathlib

    here = pathlib.Path(C.__file__).parent
    on_disk = {p.name for p in here.glob("*.py")}
    assert on_disk == set(C.SOURCE_FILES)  # a new module cannot hide from the hash
    assert len(C.source_sha256()) == 64


def test_draws_spanning_several_chunks_are_handled():
    from services.rulebook.scorer.core import score_family

    tls, units = toy_world(12, n_charts=8, years=20, n_units=4)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(3), tls, 6, AREAS)
    n = 2 * C.DRAW_CHUNK + 1  # three chunks, the last of one draw
    r = score_family(ctx, eps, C.ScoreConfig(draws=n, seed=3))
    assert r["draws"] == n and 0 < r["p1"] <= 1
    # min p cannot go below 1 / (draws + 1)
    assert min(r["p_stat"].values()) >= 1.0 / (n + 1) - 1e-12
    assert abs(r["null_mean"]["T-5y"] - 0.5) < 0.05


def test_build_family_context_applies_the_gate_and_reports_it():
    from services.rulebook.scorer.footprint import build_family_context

    n = 900
    u = make_units([("BUSY", "promotive", [[("B", [C.GENERAL])]]), ("QUIET", "promotive", [[("Q", [C.GENERAL])]])])
    rng = np.random.default_rng(2)
    tls = []
    for c in range(3):
        t = ChartTimeline(f"c{c}", BASE - 100, BASE, BASE + n - 1)
        t.states["B"] = (rng.random(n) < 0.6).astype(np.int8)
        t.states["Q"] = np.zeros(n, dtype=np.int8)
        t.states["Q"][::90] = 1
        tls.append(t)
    ctx, rep = build_family_context(C.FAMILY_DASHA, tls, u)
    assert rep["dropped"] == {"BUSY": [C.G1, C.G2]} and ctx.gate_drop["BUSY"] == frozenset({C.G1, C.G2})
    assert [v.unit_id for v in ctx.klass_variants(("promotive", "x", C.G2))] == ["QUIET"]
    assert rep["units"] == 2 and rep["pooled_touch_rate"]["3d"] is not None
