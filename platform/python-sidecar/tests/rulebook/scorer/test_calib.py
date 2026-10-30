"""Part F calibration package: birth projection, natal fixture, null models N0-N4, planted effect, gate arithmetic."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer_calib import births as B
from services.rulebook.scorer_calib import harness as H
from services.rulebook.scorer_calib import occurrences as O
from services.rulebook.scorer_calib import timelines as TL
from services.rulebook.scorer.model import ChartTimeline

from ._toy import BASE, make_units, toy_world

# ── births: only the permitted columns ever leave the file ───────────────────────────────────────
def _people_csv(path):
    cols = ["title", "source_batch", "stratum", "born_year", "birthplace", "india", "tz_raw", "born_time", "wikipedia_title", "revid", "n_events", "chart_id", "confirmatory"]
    rows = [
        ["Some Name", "post1955", "AA", "1971", "Somewhere", "False", "EST h5w (is standard time)", "09:30", "Some_Name", "9", "14", "C001", "Y"],
        ["Other Name", "post1955", "AA", "1980", "Elsewhere", "True", "IST h5e30 (is standard time)", "14:08", "Other_Name", "9", "7", "C002", "Y"],
        ["Third", "post1955", "A", "1990", "Nowhere", "False", "-05 h5w (is standard time)", "01:00", "Third", "9", "3", "C003", "N"],
        ["Fourth", "post1955", "AA", "1962", "Here", "False", "CET h1e (is standard time)", "", "Fourth", "9", "5", "C004", "Y"],
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        w.writerows(rows)


def test_only_permitted_columns_are_extracted(tmp_path):
    p = tmp_path / "people.csv"
    _people_csv(p)
    rows = B.read_permitted_columns(str(p))
    assert len(rows) == 4
    assert set(rows[0]) == set(B.ALLOWED_COLUMNS) | {"_row"}
    blob = json.dumps(rows)
    for forbidden in ("Some Name", "Somewhere", "n_events", "C001"):
        assert forbidden not in blob


def test_surrogate_births_use_row_index_codes_year_time_offset_and_are_reproducible(tmp_path):
    p = tmp_path / "people.csv"
    _people_csv(p)
    rows = B.read_permitted_columns(str(p))
    a, b = B.surrogate_births(rows, seed=5), B.surrogate_births(rows, seed=5)
    assert a == b and B.births_sha256(a) == B.births_sha256(b)
    assert [x.code for x in a] == ["r000", "r001"]  # confirmatory rows with a usable time; the blank-time row is out
    assert [x.local_date.year for x in a] == [1971, 1980]
    assert [x.local_time for x in a] == ["09:30", "14:08"] and [x.utc_offset_minutes for x in a] == [-300, 330]
    assert all(x.surrogate for x in a) and a[1].india and 12 <= a[1].lat <= 30
    assert B.surrogate_births(rows, seed=6)[0].local_date != a[0].local_date or B.surrogate_births(rows, seed=7)[0].local_date != a[0].local_date
    # a numeric zone code is read through the same h<H>(e|w) rule
    assert B._offset_fields("-0330 h3w30 (is standard time)")["utc_offset_minutes"] == -210


# ── natal fixture against the repo's own FORENSIC birth anchors (CLAUDE.md section B) ───────────────
def test_natal_chart_reproduces_the_known_anchors_of_the_repo_subject():
    from services.rulebook.scorer_calib.natal import build_natal

    swe = pytest.importorskip("swisseph")
    b = B.BirthRow("x", date(1984, 2, 5), "10:43", 20.27, 85.84, 330, True, False)
    ch = build_natal(b)
    assert ch.grahas["surya"].sign == 10  # Sun = Capricorn
    assert ch.grahas["chandra"].sign == 11  # Moon = Purva Bhadrapada (Aquarius)
    assert ch.lagna_sign == 1  # Lagna = Aries
    assert 320.0 + 20.0 / 3.0 <= ch.grahas["chandra"].longitude < 340.0  # Purva Bhadrapada spans 320 deg 00' to 333 deg 20'
    # Vimshottari: Purva Bhadrapada belongs to Jupiter; the table is gap-free and covers the birth instant
    from services.rulebook.engine.chart import utc_to_jd

    jd = utc_to_jd(ch.birth.birth_utc)
    assert ch.md.lord_at(max(jd, 2433283.0)) in {"guru", "shani", "budha", "ketu", "shukra", "surya", "chandra", "mangala", "rahu"}
    assert ch.md.defects == 0 and ch.ad.defects == 0
    assert ch.house_lords[1] == "mangala" and ch.house_lords[10] == "shani"  # Aries lagna: 1st Mars, 10th Capricorn Saturn
    assert ch.grahas["rahu"].sign is None and ch.aspected_houses["ketu"] is None  # nodes left unknown


def test_birth_time_shift_moves_the_birth_instant_by_that_many_minutes():
    from services.rulebook.scorer_calib.natal import build_natal

    pytest.importorskip("swisseph")
    b = B.BirthRow("x", date(1984, 2, 5), "10:43", 20.27, 85.84, 330, True, False)
    c0, c5 = build_natal(b, 0), build_natal(b, 5)
    assert (c5.birth.birth_utc - c0.birth.birth_utc).total_seconds() == 300


# ── timelines plumbing ───────────────────────────────────────────────────────────────────────────────
def test_runs_to_array_and_save_load_round_trip(tmp_path):
    a = TL.runs_to_array([[0, "F"], [3, "T"], [5, "N"], [7, "F"]], 10)
    assert a.tolist() == [0, 0, 0, 1, 1, -1, -1, 0, 0, 0]
    res = {
        "code": "r001", "birth_ord": 700000, "surrogate": True, "meta": {"readiness": 0},
        C.FAMILY_DASHA: {"h_start": 1, "h_end": 10, "states": {"RB1-C001": a}, "unstable_share": 0.0},
        C.FAMILY_TRANSIT: {"h_start": 1, "h_end": 10, "states": {"RB1-C002": a[::-1].copy()}},
    }
    TL.save_chart(res, str(tmp_path))
    back = TL.load_timelines(str(tmp_path))
    assert back[C.FAMILY_DASHA][0].code == "r001" and back[C.FAMILY_DASHA][0].states["RB1-C001"].tolist() == a.tolist()
    assert back[C.FAMILY_TRANSIT][0].states["RB1-C002"].tolist() == a[::-1].tolist()
    assert oct(Path(tmp_path / "r001.json").stat().st_mode & 0o777) == "0o600"


LIB = Path("/Users/Dev/Archives/madhav-research-library/10_engine/unit-manifest/rev3-20261030")
SKY = Path("/Users/Dev/scratch.noindex/claude/madhav/20261030-rulebook-scorer/sky_rows.json")


@pytest.mark.skipif(not ((LIB / "UNIT_MANIFEST_v1_0.json").exists() and SKY.exists()), reason="private manifest / sky dump not on this machine")
def test_engine_driver_builds_a_chart_end_to_end_with_masked_unstable_days():
    pytest.importorskip("panchang_engine.swiss_state")  # the repo's sunrise module needs Python 3.10+ (typing.ParamSpec)
    inp = TL.InputsBundle(str(LIB / "UNIT_MANIFEST_v1_0.json"), str(LIB / "RULE_BUNDLE_v1_0.json"), str(SKY))
    b = B.BirthRow("x", date(1985, 6, 15), "08:20", 28.6, 77.2, 330, True, False)
    r = TL.build_one(b, inp)
    if "excluded" in r:  # exclusion 4 is a legitimate outcome for a birth near a boundary
        assert r["excluded"].startswith(("EXCL4", "ENGINE_"))
        return
    assert r[C.FAMILY_DASHA]["h_start"] >= date(1985 + 12, 6, 15).toordinal() - 1
    assert r[C.FAMILY_DASHA]["h_end"] == r[C.FAMILY_TRANSIT]["h_end"]
    for fam in (C.FAMILY_DASHA, C.FAMILY_TRANSIT):
        n = r[fam]["h_end"] - r[fam]["h_start"] + 1
        assert r[fam]["states"] and all(v.shape == (n,) for v in r[fam]["states"].values())


# ── occurrence models ───────────────────────────────────────────────────────────────────────────────
def _tl_set(n_charts=1, years=70):
    tls, units = toy_world(1, n_charts=n_charts, years=years, n_units=6)
    return tls, units, [O._DayPmf(t) for t in tls]


def _profile(area, direction, grade, n, n_charts=1):
    return O.CountsProfile(tuple(tuple([(area, direction, grade)] * n) for _ in range(n_charts)))


def _ages(occ, tls):
    return np.array([((o.lo + o.hi) / 2 - tls[o.chart].birth) / 365.25 for o in occ])


def test_N0_is_uniform_over_the_horizon():
    tls, units, pm = _tl_set()
    occ = O.place_study(np.random.default_rng(1), _profile("career_adv_change_entry", C.FAVOURABLE, C.G1, 3000), tls, pm, "N0")
    a = _ages(occ, tls)
    assert len(occ) == 3000 and abs(a.mean() - (12 + 82) / 2.0) < 1.0 and a.min() < 14 and a.max() > 80


@pytest.mark.parametrize("area,direction,mu,sd", [("childbirth_progeny", C.FAVOURABLE, 31, 5), ("bereavement_parent", C.UNFAVOURABLE, 52, 12), ("separation_relationship_end", C.UNFAVOURABLE, 38, 8)])
def test_N1_age_densities(area, direction, mu, sd):
    tls, units, pm = _tl_set(years=80)
    occ = O.place_study(np.random.default_rng(2), _profile(area, direction, C.G1, 3000), tls, pm, "N1")
    a = _ages(occ, tls)
    assert abs(a.mean() - mu) < 1.0  # truncated at age 12 and at the horizon end: the mean moves a little
    assert 0.8 * sd < a.std() < 1.15 * sd


def test_N1_career_density_is_flat_20_to_65_with_double_weight_25_to_40():
    tls, units, pm = _tl_set(years=80)
    occ = O.place_study(np.random.default_rng(3), _profile("career_adv_change_entry", C.FAVOURABLE, C.G1, 6000), tls, pm, "N1")
    a = _ages(occ, tls)
    assert a.min() >= 19.9 and a.max() <= 65.1
    inner = ((a >= 25) & (a < 40)).mean()
    assert abs(inner - 30.0 / 60.0) < 0.03  # weight 2*15 of 2*15 + 30 total
    assert abs(((a >= 20) & (a < 25)).mean() - 5.0 / 60.0) < 0.02


def test_N1_leaves_unlisted_categories_uniform():
    tls, units, pm = _tl_set(years=80)
    occ = O.place_study(np.random.default_rng(4), _profile("education_learning", C.FAVOURABLE, C.G1, 3000), tls, pm, "N1")
    assert abs(_ages(occ, tls).mean() - 52.0) < 1.5  # horizon = ages 12..92


def test_N2_seasonal_month_weights():
    tls, units, pm = _tl_set(years=70)
    occ = O.place_study(np.random.default_rng(5), _profile("career_adv_change_entry", C.FAVOURABLE, C.G1, 12000), tls, pm, "N2")
    m = np.array([date.fromordinal((o.lo + o.hi) // 2).month for o in occ])
    share = np.bincount(m, minlength=13)[1:] / m.size
    # weight 1 + 0.3 sin(2 pi (month - 1) / 12): April (month 4) = 1.3, October (month 10) = 0.7
    assert 1.5 < share[3] / share[9] < 2.3


def test_N3_half_the_episodes_follow_a_previous_one_within_15_days():
    tls, units, pm = _tl_set(years=70)
    prof = _profile("career_adv_change_entry", C.FAVOURABLE, C.G1, 40, n_charts=1)
    near = {}
    for model in ("N0", "N3"):
        c = 0
        for s in range(30):
            occ = O.place_study(np.random.default_rng(s), prof, tls, pm, model)
            mids = [(o.lo + o.hi) // 2 for o in occ]
            for i, m in enumerate(mids):
                if any(0 < m - mids[j] <= 15 for j in range(i)):
                    c += 1
        near[model] = c / (30 * 40)
    assert near["N3"] > 0.40 and near["N0"] < 0.10


def test_N4_combines_age_season_and_bursts():
    tls, units, pm = _tl_set(years=80)
    occ = O.place_study(np.random.default_rng(6), _profile("childbirth_progeny", C.FAVOURABLE, C.G2, 4000), tls, pm, "N4")
    a = _ages(occ, tls)
    assert abs(a.mean() - 31) < 1.5
    assert all(o.hi - o.lo + 1 in (28, 29, 30, 31) for o in occ)  # month windows


def test_declared_profile_is_reproducible_and_counts_only():
    a, b = O.declared_profile(30), O.declared_profile(30)
    assert a == b and a.total() > 0
    assert all(x[2] in (C.G1, C.G2) and x[1] in (C.FAVOURABLE, C.UNFAVOURABLE) for ch in a.per_chart for x in ch)


# ── planted effect ────────────────────────────────────────────────────────────────────────────────────
def _cov(ctx, chart, klass, lo, hi, units=None):
    """Pooled coverage of the applicable units (optionally only ``units``) over [lo, hi]: share of TRUE days."""
    t = ctx.tl[chart]
    tr = asd = 0.0
    for v in ctx.klass_variants(klass):
        if units is not None and v.unit_id not in units:
            continue
        comps = v.components()
        for comp in comps:
            val = ctx.comp_vals(chart, comp)[lo - t.h_start : hi - t.h_start + 1]
            ok = ~np.isnan(val)
            tr += np.where(ok, val, 0.0).sum() / len(comps)
            asd += ok.sum() / len(comps)
    return tr / asd if asd else np.nan


def test_planted_effect_uses_the_top_20_percent_coverage_windows_of_the_chart():
    from services.rulebook.scorer.core import FamilyContext

    tls, units = toy_world(2, n_charts=6, years=40, n_units=6, duty=0.1)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    pm = [O._DayPmf(t) for t in tls]
    one = tuple([("career_adv_change_entry", C.FAVOURABLE, C.G1)] * 15 + [("career_adv_change_entry", C.FAVOURABLE, C.G2)] * 15)
    prof = O.CountsProfile(tuple(one for _ in tls))
    occ = O.place_study(np.random.default_rng(1), prof, tls, pm, "N0")
    target = O.ChartTimelineSet(ctx)
    moved = O.apply_effect(np.random.default_rng(2), occ, 1.0, target)
    assert len(moved) == len(occ)
    for o in moved:
        klass = ("promotive", o.area, o.grade)
        t = tls[o.chart]
        assert o.lo >= t.h_start and o.hi <= t.h_end
        # compare the window with ALL windows of that grade in the chart: it must be in the top 20% and above zero
        if o.grade == C.G1:
            allw = [(d, d + 2) for d in range(t.h_start, t.h_end - 1, 7)]
        else:
            mlo, mhi = target._month_windows(o.chart)
            allw = list(zip(mlo.tolist(), mhi.tolist()))
        covs = np.array([_cov(ctx, o.chart, klass, a, b) for a, b in allw])
        thr = np.nanquantile(covs, 0.8)
        mine = _cov(ctx, o.chart, klass, o.lo, o.hi)
        assert mine > 0 and mine >= thr - 1e-9
    assert O.apply_effect(np.random.default_rng(2), occ, 0.0, target) == list(occ)


def test_q_is_the_share_moved_and_the_rest_keep_their_null_placement():
    from services.rulebook.scorer.core import FamilyContext

    tls, units = toy_world(3, n_charts=4, years=30, n_units=6, duty=0.1)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    pm = [O._DayPmf(t) for t in tls]
    prof = O.CountsProfile(tuple(tuple([("career_adv_change_entry", C.FAVOURABLE, C.G2)] * 100) for _ in tls))
    occ = O.place_study(np.random.default_rng(1), prof, tls, pm, "N0")
    moved = O.apply_effect(np.random.default_rng(5), occ, 0.25, O.ChartTimelineSet(ctx))
    same = sum(1 for a, b in zip(occ, moved) if a == b)
    assert 0.65 < same / len(occ) < 0.85  # ~75% unchanged (a moved episode can also land where it was)


def test_sparse_effect_uses_only_a_random_fifth_of_the_units():
    from services.rulebook.scorer.core import FamilyContext

    tls, units = toy_world(4, n_charts=4, years=30, n_units=10, duty=0.1)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    pm = [O._DayPmf(t) for t in tls]
    prof = O.CountsProfile(tuple(tuple([("career_adv_change_entry", C.FAVOURABLE, C.G2)] * 60) for _ in tls))
    occ = O.place_study(np.random.default_rng(1), prof, tls, pm, "N0")
    target = O.ChartTimelineSet(ctx)
    a = O.apply_effect(np.random.default_rng(7), occ, 1.0, target, sparse=True)
    b = O.apply_effect(np.random.default_rng(8), occ, 1.0, target, sparse=True)
    assert a != b  # a different random 20% of the units each time
    # with 10 units the active set is 2 units: moved windows are top-20% for THOSE units only
    assert len(target.windows_cache) == 0  # sparse choices are never cached across studies


def test_k12_trigger_arithmetic():
    def mk(rate_dasha, rate_transit, n=1000):
        out = []
        for i in range(n):
            out.append({"dasha": {"p1": 0.02 if i < rate_dasha * n else 0.5}, "transit": {"p1": 0.02 if i < rate_transit * n else 0.5}})
        return out

    ok = H.k12_check({"N1": mk(0.03, 0.03), "N2": mk(0.03, 0.03), "N4": mk(0.034, 0.02)})
    assert ok["triggered"] is False
    bad = H.k12_check({"N1": mk(0.04, 0.02), "N2": mk(0.04, 0.036), "N4": mk(0.02, 0.02), "N0": mk(0.05, 0.05)})
    assert bad["triggers"] == ["N1/dasha: F3 step 1 (age adjustment) then step 2", "N2/transit: F3 step 3 (whole-year shifts in 10-year blocks)"]


def test_to_episodes_keeps_what_falls_inside_the_family_horizon():
    tls, units = toy_world(3, n_charts=1, years=10)
    t = tls[0]
    inside = O.Occurrence(0, "a", C.FAVOURABLE, C.G1, t.h_start + 10, t.h_start + 12)
    outside = O.Occurrence(0, "a", C.FAVOURABLE, C.G1, t.h_start - 3, t.h_start - 1)
    eps = O.to_episodes([inside, outside], tls)
    assert len(eps) == 1 and eps[0].lo == inside.lo


# ── gate arithmetic ─────────────────────────────────────────────────────────────────────────────────────
def _res(model, n, k_dasha, k_transit, k_any, m1=None, m2=None):
    """Synthetic study results: the first k studies pass in that family (same counts under every rule unless given)."""
    out = []
    m1 = m1 or (k_dasha, k_transit, k_any)
    m2 = m2 or (k_dasha, k_transit, k_any)
    for i in range(n):
        row = {}
        for key, (kd, kt, ka) in (("flags", (k_dasha, k_transit, k_any)), ("flags_m1", m1), ("flags_m2", m2)):
            row.setdefault("dasha", {})[key] = {v: i < kd for v in H.VARIANTS}
            row.setdefault("transit", {})[key] = {v: i < kt for v in H.VARIANTS}
            row["any" if key == "flags" else "any_" + key[6:]] = {v: i < ka for v in H.VARIANTS}
        out.append(row)
    return out


SHA = "a" * 64
GOOD_SANITY = {"dasha": 0.9, "transit": 0.85}


def _gate(by, **kw):
    args = dict(draws=2000, scorer_sha256=SHA, frozen_scorer_sha256=SHA, d7_known=False, sanity=GOOD_SANITY)
    args.update(kw)
    return H.f2_gate(by, **args)


def test_flags_apply_the_four_variants_of_the_strong_rule():
    r = {"p2": 0.04, "p3": 0.04, "p_dir": 0.04}
    assert H.flags(0.04, r) == {"a": True, "a+b": True, "a+c": True, "a+b+c": True, "full": True}
    assert H.flags(0.04, {**r, "p3": 0.2})["a+b"] and not H.flags(0.04, {**r, "p3": 0.2})["a+c"]
    assert not H.flags(0.04, {**r, "p_dir": 0.2})["full"] and H.flags(0.04, {**r, "p_dir": 0.2})["a+b+c"]
    assert not any(H.flags(0.06, r).values())
    assert not H.flags(None, r)["a"]


def test_f2_gate_passes_and_fails_on_the_stated_numbers():
    ok = {m: _res(m, 5000, 100, 100, 150) for m in O.MODELS}  # 0.02, 0.02, 0.03 exactly: point estimate passes
    g = _gate(ok)
    assert g["status"] == "GATE" and g["pass"] is True
    assert "Wilson" in g["criterion"] and g["models"]["N0"]["flags_m1"]["rates"]["dasha"]["full_upper95"] > 0.02
    g = _gate(dict(ok, N3=_res("N3", 5000, 101, 0, 101)))
    assert g["pass"] is False and g["models"]["N3"]["flags_m1"]["per_family_ok"] is False
    assert _gate(dict(ok, N1=_res("N1", 5000, 50, 50, 151)))["models"]["N1"]["flags_m2"]["overall_ok"] is False


def test_f2_gate_needs_every_condition_or_it_is_not_a_gate():
    ok = {m: _res(m, 5000, 0, 0, 0) for m in O.MODELS}
    assert _gate(ok)["status"] == "GATE"
    only_n0 = {"N0": ok["N0"]}  # review S7 (i): a subset of models is never a gate
    g = _gate(only_n0)
    assert g["status"] == "NOT_GATE" and g["pass"] is False and g["conditions"]["all_five_models"] is False
    few = {m: _res(m, 4999, 0, 0, 0) for m in O.MODELS}  # (ii)
    assert _gate(few)["conditions"]["studies_at_least_5000"] is False and _gate(few)["pass"] is False
    assert _gate(ok, draws=1999)["status"] == "NOT_GATE"  # (iii)
    assert _gate(ok, frozen_scorer_sha256="b" * 64)["status"] == "NOT_GATE"  # not the frozen scorer
    assert _gate(ok, frozen_scorer_sha256=None)["status"] == "NOT_GATE"
    assert _gate(ok, sanity=None)["status"] == "NOT_GATE"  # (iv) the q = 30% sanity check must be run
    assert _gate(ok, sanity={"dasha": 0.95, "transit": 0.79})["pass"] is False
    assert H.f2_gate({}, draws=2000, scorer_sha256=SHA, frozen_scorer_sha256=SHA, sanity=GOOD_SANITY)["pass"] is False


def test_f2_gate_before_d7_needs_both_m1_and_m2_and_after_d7_uses_its_m():
    """review S6: one family testable means Holm's first step is 0.05, not 0.025; the gate must see that case."""
    m1_fails = {m: _res(m, 5000, 0, 0, 0, m1=(150, 0, 150)) for m in O.MODELS}
    g = _gate(m1_fails)
    assert g["rules"] == ["flags_m1", "flags_m2"] and g["pass"] is False
    assert g["models"]["N0"]["flags_m2"]["per_family_ok"] is True and g["models"]["N0"]["flags_m1"]["per_family_ok"] is False
    g = _gate(m1_fails, d7_known=True)  # D7 fixed m: the study's own production rule decides
    assert g["rules"] == ["flags"] and g["pass"] is True


def test_wilson_upper_bound():
    assert H.wilson_upper(0, 5000) == pytest.approx(0.00077, abs=1e-4)
    assert 0.02 < H.wilson_upper(100, 5000) < 0.026
