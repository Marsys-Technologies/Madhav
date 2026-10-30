"""Yardstick v1.5 (SUR-RB-40): P1 donor diagnostic and trigger, P2 relaxed donor rule with imputation, P3 extra gate,
P4 horizon edges (count_blind's rules, conductor 2026-10-30)."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, donor_diagnostic, donor_eligibility_counts, donor_sets, run_donor_check, score_family
from services.rulebook.scorer.model import ChartTimeline, Episode
from services.rulebook.scorer.runner import RunRefused, prepare_episodes
from services.rulebook.scorer_calib import harness as H
from services.rulebook.scorer_calib import occurrences as O

from ._toy import BASE, make_units, month_window, random_episodes, runs_series, toy_world
from .test_review_fixes import _cfg, _claims, _lock, _two_families, lockfiles, score_sample  # noqa: F401  (fixture re-used)

CAREER = "career_adv_change_entry"


def _na_world(na_share, seed=1, n_charts=20):
    """Members with scattered NOT_ASSESSED stretches covering about ``na_share`` of the days."""
    rng = np.random.default_rng(seed)
    units = make_units([(f"U{k}", "promotive", [[(f"M{k}", [C.GENERAL])]]) for k in range(6)])
    tls = []
    n = 365 * 15
    for c in range(n_charts):
        t = ChartTimeline(f"c{c:02d}", BASE - 9000 + c, BASE, BASE + n - 1)
        for u in units:
            st = runs_series(rng, n, 0.2, 12)
            k = int(na_share * n / 30)
            for s in rng.integers(0, n - 30, k):
                st[s : s + 30] = -1
            t.states[u.members()[0].rid] = st
        tls.append(t)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(seed), tls, 18, [CAREER])
    return ctx, eps


# ── P1 ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_p1_diagnostic_counts_and_triggers_only_below_the_floor():
    ctx, eps = _na_world(0.0)
    d = donor_diagnostic(ctx, eps)
    assert d["b"]["charts_with_5_donors"] >= 15 and d["b"]["floor_ok"] and not d["b"]["p2_trigger"]
    assert d["donor_rules"] == {"b": "m3", "c": "m3"}
    ctx2, eps2 = _na_world(0.08)
    d2 = donor_diagnostic(ctx2, eps2)
    assert d2["b"]["charts_with_5_donors"] < 15 and d2["b"]["p2_trigger"] and d2["donor_rules"]["b"] == "p2_90"


def test_p1_the_sealed_rule_must_follow_the_trigger(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)  # no NOT_ASSESSED: M3 meets the floor, the rule must stay M3
    bad = {f: dict(v) for f, v in lock.d7.items()}
    bad[C.FAMILY_DASHA]["donor_rule_b"] = "p2_90"
    with pytest.raises(RunRefused, match="v1.5 P1"):
        score_sample(ctx, eps, _cfg(), replace(lock, d7=bad))
    assert _claims(tmp_path) == []


# ── P2 ───────────────────────────────────────────────────────────────────────────────────────────────────
def test_p2_relaxed_rule_keeps_donors_with_at_least_90_percent_of_cells_and_imputes_the_rest():
    ctx, eps = _na_world(0.06)
    m3 = donor_eligibility_counts(ctx, eps)
    p2 = donor_eligibility_counts(ctx, eps, rules={"b": "p2_90", "c": "p2_90"})
    p95 = donor_eligibility_counts(ctx, eps, rules={"b": "p2_95", "c": "p2_95"})
    assert p2["b"] >= p95["b"] >= m3["b"] and p2["b"] > m3["b"]
    sets = donor_sets(ctx, eps, False, rule="p2_90")
    for c, d in sets.items():
        for donor in d["elig"]:
            share = sum(int(dm[:, donor].sum()) for dm in d["defined"]) / d["cells"]
            assert share >= 0.9 - 1e-12
    r = run_donor_check(ctx, eps, 100, np.random.default_rng(1), False, rule="p2_90")
    assert r["T"] is not None and 0 < r["imputed_share"] < 0.1


def test_p2_an_undefined_cell_takes_the_donors_own_block_base_rate():
    n = 365 * 8
    rng = np.random.default_rng(3)
    units = make_units([("U0", "promotive", [[("M0", [C.GENERAL])]])])
    tls = [ChartTimeline(f"c{c}", BASE - 9000 + c, BASE, BASE + n - 1, {"M0": runs_series(rng, n, 0.2, 12)}) for c in range(7)]
    lo, hi = month_window(1992, 6)
    tls[3].states["M0"][lo - BASE : hi - BASE + 1] = -1  # donor 3: chart 0's only cell is undefined on it
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = [Episode(0, CAREER, C.FAVOURABLE, C.G2, lo, hi)] + [Episode(c, CAREER, C.FAVOURABLE, C.G2, *month_window(1994, c)) for c in range(1, 7)]
    assert 3 not in donor_sets(ctx, eps, False, rule="m3")[0]["elig"]
    # with one cell per chart, 90% means every cell: donor 3 is still not eligible for chart 0
    assert 3 not in donor_sets(ctx, eps, False, rule="p2_90")[0]["elig"]
    base = ctx.block_base_rate(3, units[0].variant(CAREER, True), hi - lo + 1, (lo + hi) // 2)
    st = tls[3].states["M0"][: C.BLOCK_DAYS_5Y]
    L = hi - lo + 1
    covs = []
    for s in range(0, C.BLOCK_DAYS_5Y - L + 1):
        w = st[s : s + L]
        k = (w >= 0).sum()
        if k * 2 >= L:
            covs.append((w == 1).sum() / k)
    assert base == pytest.approx(float(np.mean(covs)))  # the donor's own block, windows at least half assessed


def test_p2_score_family_reads_the_sealed_rule_and_reports_the_imputed_share():
    ctx, eps = _na_world(0.06)
    r = score_family(ctx, eps, C.ScoreConfig(draws=50, seed=1), d7={"donor_rule_b": "p2_90", "donor_rule_c": "m3"})
    assert r["donor_rules"] == {"b": "p2_90", "c": "m3"} and r["imputed_share_b"] > 0 and r["imputed_share_c"] == 0.0


# ── P3 ───────────────────────────────────────────────────────────────────────────────────────────────────
def _rows(n, k2):
    return [{"dasha": {"p2": 0.01 if i < k2 else 0.5, "p3": 0.5}, "transit": {"p2": 0.5, "p3": 0.5}} for i in range(n)]


def test_p3_marginal_rate_of_a_p2_check_must_stay_under_six_percent_under_every_model():
    rules = {"dasha": {"b": "p2_90", "c": "m3"}, "transit": {"b": "m3", "c": "m3"}}
    ok = H.p3_check({m: _rows(1000, 60) for m in O.MODELS}, rules)
    assert ok["ok"] and list(ok["rows"]) == ["dasha/b"]
    assert all(0.06 < u < 0.08 for u in ok["rows"]["dasha/b"]["wilson_upper95"].values())  # Wilson bound printed (VERIFY2 F5)
    bad = H.p3_check(dict({m: _rows(1000, 60) for m in O.MODELS}, N2=_rows(1000, 61)), rules)
    assert not bad["ok"] and bad["failing"] == [("dasha", "b")]
    assert H.p3_check({m: _rows(1000, 99) for m in O.MODELS}, {"dasha": {"b": "m3", "c": "m3"}, "transit": {"b": "m3", "c": "m3"}})["ok"]  # no P2: no P3


def test_p3_an_untestable_family_is_dropped_and_the_other_judged_at_m1():
    from .test_calib import _res, GOOD_SANITY, SHA

    by = {m: _res(m, 5000, 0, 900, 900, m1=(50, 900, 900)) for m in O.MODELS}  # transit fails, dasha 1% at m = 1
    g = H.f2_gate(by, draws=2000, scorer_sha256=SHA, frozen_scorer_sha256=SHA, sanity={"dasha": 0.9}, testable=["dasha"], untestable=["transit"])
    assert g["families_judged"] == ["dasha"] and g["rules"] == ["flags_m1"] and g["pass"] is True


# ── P4: horizon edges exactly as count_blind ───────────────────────────────────────────────────────────────
def _one_chart():
    n = 365 * 4
    units = make_units([("U0", "promotive", [[("M0", [C.GENERAL])]])])
    start = date(1990, 1, 10).toordinal()
    t = ChartTimeline("c0", start - 9000, start, start + n - 1, {"M0": runs_series(np.random.default_rng(1), n, 0.2, 10)})
    return FamilyContext(C.FAMILY_DASHA, [t], units), t


def test_p4_a_day_just_outside_the_horizon_is_dropped_even_though_its_window_overlaps():
    ctx, t = _one_chart()
    before = Episode(0, CAREER, C.FAVOURABLE, C.G1, t.h_start - 2, t.h_start)  # day = h_start - 1
    after = Episode(0, CAREER, C.FAVOURABLE, C.G1, t.h_end, t.h_end + 2)  # day = h_end + 1
    kept, drops = prepare_episodes(ctx, [before, after])
    assert kept == [] and drops["dropped_horizon"] == 2


def test_p4_a_day_on_the_horizon_edge_is_clipped_and_kept():
    ctx, t = _one_chart()
    edge = Episode(0, CAREER, C.FAVOURABLE, C.G1, t.h_start - 1, t.h_start + 1)  # day = h_start
    kept, drops = prepare_episodes(ctx, [edge])
    assert len(kept) == 1 and (kept[0].lo, kept[0].hi) == (t.h_start, t.h_start + 1) and drops["clipped_day_windows"] == 1


def test_p4_a_month_straddling_the_horizon_is_dropped_not_clipped():
    ctx, t = _one_chart()  # the horizon starts on 10 January 1990
    straddle = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1990, 1))
    inside = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1990, 2))
    kept, drops = prepare_episodes(ctx, [straddle, inside])
    assert kept == [inside] and drops["dropped_horizon"] == 1


# ── count_blind v2 donor outputs: equality before the claim (SUR-RB-41) ─────────────────────────────────────
def test_v2_donor_outputs_must_equal_the_recount_before_the_claim(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    bad = {f: {"charts": {k: dict(v) for k, v in d["charts"].items()}, "checks": {k: dict(v) for k, v in d["checks"].items()}} for f, d in lock.donor_counts.items()}
    first = sorted(bad[C.FAMILY_DASHA]["charts"])[0]
    bad[C.FAMILY_DASHA]["charts"][first]["donors_b_p2"] += 1
    with pytest.raises(RunRefused, match="COUNT_BLIND_DONOR_ELIGIBILITY"):
        score_sample(ctx, eps, _cfg(), replace(lock, donor_counts=bad))
    bad2 = {f: {"charts": d["charts"], "checks": {k: dict(v) for k, v in d["checks"].items()}} for f, d in lock.donor_counts.items()}
    bad2[C.FAMILY_TRANSIT]["checks"]["c"]["imputed_cell_share_p2"] = "0.999999"
    with pytest.raises(RunRefused, match="COUNT_BLIND_DONOR_DIAGNOSTIC"):
        score_sample(ctx, eps, _cfg(), replace(lock, donor_counts=bad2))
    missing = dict(lock.donor_counts)
    missing.pop(C.FAMILY_DASHA)
    with pytest.raises(RunRefused, match="count_blind v2"):
        score_sample(ctx, eps, _cfg(), replace(lock, donor_counts=missing))
    assert _claims(tmp_path) == []


def test_v2_the_trigger_comes_from_the_sealed_diagnostic(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    forged = {f: {"charts": d["charts"], "checks": {k: dict(v) for k, v in d["checks"].items()}} for f, d in lock.donor_counts.items()}
    forged[C.FAMILY_DASHA]["checks"]["b"]["k11_floor_met_m3"] = 0  # the diagnostic now says P2 for dasha (b)
    with pytest.raises(RunRefused, match="v1.5 P1"):
        score_sample(ctx, eps, _cfg(), replace(lock, donor_counts=forged))


def test_v2_recount_round_trips_through_files_in_the_exact_format(tmp_path):
    """Write the recount as count_blind v2 would (exact columns), read it back, and compare: equal."""
    import csv as _csv_mod
    import hashlib
    import json

    from services.rulebook.scorer.core import donor_recount
    from services.rulebook.scorer.inputs import DONOR_DIAG_COLUMNS, DONOR_ELIG_COLUMNS, donor_rows, read_count_blind

    from .test_inputs import _count_blind

    ctx, eps = _na_world(0.05, n_charts=18)
    rec = donor_recount(ctx, eps)
    d = _count_blind(tmp_path)
    with open(d / "COUNT_BLIND_DONOR_ELIGIBILITY.csv", "w", newline="", encoding="utf-8") as fh:
        w = _csv_mod.writer(fh, lineterminator="\n")
        w.writerow(DONOR_ELIG_COLUMNS)
        for code, row in sorted(rec["charts"].items()):
            w.writerow([5, "dasha", "primary_nonschedulable", code] + [row[k] for k in DONOR_ELIG_COLUMNS[4:]])
    with open(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv", "w", newline="", encoding="utf-8") as fh:
        w = _csv_mod.writer(fh, lineterminator="\n")
        w.writerow(DONOR_DIAG_COLUMNS)
        for chk in ("b", "c"):
            w.writerow([5, "dasha", "primary_nonschedulable", chk] + [rec["checks"][chk][k] for k in DONOR_DIAG_COLUMNS[4:]])
    run = json.loads((d / "COUNT_BLIND_RUN.json").read_text())
    for nm in ("COUNT_BLIND_DONOR_ELIGIBILITY.csv", "COUNT_BLIND_DONOR_DIAGNOSTIC.csv"):
        run["outputs_sha256"][nm] = hashlib.sha256((d / nm).read_bytes()).hexdigest()
    (d / "COUNT_BLIND_RUN.json").write_text(json.dumps(run))
    back = donor_rows(read_count_blind(str(d)), 5, "dasha")
    assert back == rec
    assert rec["checks"]["b"]["k11_floor_met_m3"] in (0, 1) and rec["checks"]["b"]["imputed_cell_share_p2"] != ""
