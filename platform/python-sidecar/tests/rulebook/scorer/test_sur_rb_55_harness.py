"""SUR-RB-54 (i)/(ii) and SUR-RB-55 (e)/(f), Part F harness: per-family charts (the daśā list a subset of the transit
list, matched by chart code), the occurrence-set option, and a separately formed non-schedulable subset in every
synthetic study with the F2 gate simulating the full rule."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import replace
from datetime import date, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.inputs import read_count_blind
from services.rulebook.scorer_calib import cli
from services.rulebook.scorer_calib import harness as H
from services.rulebook.scorer_calib import occurrences as O

from ._toy import toy_world
from .test_inputs import _admission, _count_blind, _sha, _write_json

CAREER = "career_adv_change_entry"


def _families(drop_dasha=(2, 5), late_dasha=(1,)):
    tls, units = toy_world(21, n_charts=16, years=25, n_units=8)
    t_units = [replace(u, plane=C.FAMILY_TRANSIT) for u in units]
    dasha = []
    for i, t in enumerate(tls):
        if i in drop_dasha:
            continue
        if i in late_dasha:  # the daśā horizon may start later than the transit one (same end)
            t = replace(t, h_start=t.h_start + 400, states={k: v[400:] for k, v in t.states.items()})
        dasha.append(t)
    return {C.FAMILY_DASHA: dasha, C.FAMILY_TRANSIT: list(tls)}, {C.FAMILY_DASHA: units, C.FAMILY_TRANSIT: t_units}


def _profile(n, ns=None, per=10):
    rows = tuple(tuple([(CAREER, C.FAVOURABLE, C.G2)] * per + [(CAREER, C.FAVOURABLE, C.G1)] * 4) for _ in range(n))
    nsr = None if ns is None else tuple(tuple([(CAREER, C.FAVOURABLE, C.G2)] * ns + [(CAREER, C.FAVOURABLE, C.G1)] * 9) for _ in range(n))
    return O.CountsProfile(rows, nsr)


def test_i_the_dasha_list_is_a_subset_of_the_transit_list_matched_by_code():
    tl, units = _families()
    cal = H.Calibration(tl, units, {}, _profile(16), draws=30)
    r = cal.run_study("N0", 0)
    assert r["dasha"]["charts"] <= 14 and r["transit"]["charts"] <= 16
    # episodes are mapped to each family's own chart index by code
    occ = O.place_study(np.random.default_rng(1), cal.profile, cal.tls[C.FAMILY_TRANSIT], cal.pmfs, "N0")
    eps_d = O.to_episodes(occ, cal.tls[C.FAMILY_DASHA], cal.maps[C.FAMILY_DASHA])
    codes_d = [t.code for t in cal.tls[C.FAMILY_DASHA]]
    dropped = {tl[C.FAMILY_TRANSIT][i].code for i in (2, 5)}
    assert all(0 <= e.chart < len(codes_d) for e in eps_d)
    assert not dropped & {codes_d[e.chart] for e in eps_d}
    by_t = Counter(cal.tls[C.FAMILY_TRANSIT][o.chart].code for o in occ)
    by_d = Counter(codes_d[e.chart] for e in eps_d)
    late = tl[C.FAMILY_TRANSIT][1].code
    for c, n in by_d.items():
        assert n <= by_t[c] and (n == by_t[c] or c == late)  # only the late-starting daśā horizon loses occurrences


def test_i_a_dasha_chart_missing_from_transit_or_a_different_end_refuses():
    tl, units = _families()
    bad = dict(tl)
    bad[C.FAMILY_DASHA] = tl[C.FAMILY_DASHA] + [replace(tl[C.FAMILY_TRANSIT][0], code="ZZZ")]
    with pytest.raises(AssertionError, match="transit"):
        H.Calibration(bad, units, {}, _profile(16), draws=30)
    bad2 = dict(tl)
    t0 = tl[C.FAMILY_DASHA][0]
    bad2[C.FAMILY_DASHA] = [replace(t0, h_end=t0.h_end - 1, states={k: v[:-1] for k, v in t0.states.items()})] + tl[C.FAMILY_DASHA][1:]
    with pytest.raises(AssertionError, match="end"):
        H.Calibration(bad2, units, {}, _profile(16), draws=30)


def test_i_the_loader_applies_the_per_family_horizon_exclusions(tmp_path):
    d = _admission(tmp_path, charts=("C001", "C002", "C003"))
    hz = json.loads((d / "out" / "s5_horizons.json").read_text())
    hz["charts"]["C002"]["families"]["dasha"].update(under_12_years=True, start="2000-03-01", end="2000-02-29", days=0)  # daśā only
    for f in ("dasha", "transit"):
        hz["charts"]["C003"]["families"][f]["under_12_years"] = True  # both families
    _write_json(d / "out" / "s5_horizons.json", hz)
    man = json.loads((d / "out" / "TIMELINES_MANIFEST.json").read_text())
    man["files"]["out/s5_horizons.json"] = _sha(d / "out" / "s5_horizons.json")
    _write_json(d / "out" / "TIMELINES_MANIFEST.json", man)
    from services.rulebook.scorer.inputs import AdmissionInputs

    ids = cli.family_chart_ids(AdmissionInputs(str(d)))
    assert ids == {C.FAMILY_DASHA: ["C001"], C.FAMILY_TRANSIT: ["C001", "C002"]}


def test_ii_the_occurrence_set_option_selects_the_profile_and_a6s_a7_set(tmp_path):
    cb = read_count_blind(str(_count_blind(tmp_path)))
    cb.donor_diagnostic += [dict(r, set="all") for r in cb.donor_diagnostic]  # count_blind V3 writes both sets
    cb.donors += [dict(r, set="all") for r in cb.donors]
    codes = ["C%03d" % i for i in range(1, 21)]
    p_all = O.profile_from_count_blind(cb, codes, set_name="all")
    p_ns = O.profile_from_count_blind(cb, codes, set_name="primary_nonschedulable")
    assert p_all.total() > p_ns.total() and p_all.ns_per_chart is not None and p_ns.ns_per_chart is None
    assert p_all.ns_per_chart == p_ns.per_chart  # the subset's counts come from count_blind's primary_nonschedulable rows
    # threshold 5: 18 charts in the pool, below A7's 20 charts in either set; threshold 3: 20 charts and enough episodes
    assert cli.a7_meets(cb, 5, "all") is False and cli.a7_meets(cb, 3, "all") is True
    # the set decides: with fewer non-schedulable episodes per chart the primary set misses A7's 400 episodes
    cb.aggregates = [dict(r, scored_applicable=(1 if r["set"] == "primary_nonschedulable" else r["scored_applicable"])) for r in cb.aggregates]
    assert cli.a7_meets(cb, 3, "primary_nonschedulable") is False and cli.a7_meets(cb, 3, "all") is True
    assert "count_set" in cli.build_parser().parse_args(["a6", "--manifest", "m", "--clusters", "c", "--out", "o"]).__dict__
    assert cli.build_parser().parse_args(["a6", "--manifest", "m", "--clusters", "c", "--out", "o"]).count_set == "all"


def test_e_each_study_carries_a_separately_formed_non_schedulable_subset():
    tl, units = _families(drop_dasha=(), late_dasha=())
    cal = H.Calibration(tl, units, {}, _profile(16, ns=4), draws=30)
    occ = O.place_study(np.random.default_rng(3), cal.profile, cal.tls[C.FAMILY_TRANSIT], cal.pmfs, "N0")
    for ci in range(16):
        mine = [o for o in occ if o.chart == ci]
        ns = Counter((o.area, o.direction, o.grade) for o in mine if o.ns)
        allc = Counter((o.area, o.direction, o.grade) for o in mine)
        assert ns[(CAREER, C.FAVOURABLE, C.G2)] == min(4, allc[(CAREER, C.FAVOURABLE, C.G2)])
        assert ns[(CAREER, C.FAVOURABLE, C.G1)] == min(9, allc[(CAREER, C.FAVOURABLE, C.G1)])  # capped by what was placed
    moved = O.apply_effect(np.random.default_rng(4), occ, 0.9, cal.eff[C.FAMILY_DASHA], index_map=cal.maps[C.FAMILY_DASHA])
    assert sum(o.ns for o in moved) == sum(o.ns for o in occ)  # the label travels with a moved occurrence
    cal.fallback = True
    r = cal.run_study("N0", 0)
    for f in C.FAMILIES:
        assert "ns_ok" in r[f] and "T_ns" in r[f] and r[f]["n_ns"] > 0


def test_e_the_full_rule_needs_the_consistency_condition_with_the_fallback():
    r = {"p2": 0.01, "p3": 0.01, "p_dir": 0.01, "nonschedulable_above_null_mean": False}
    assert H.flags(0.01, r)["full"] is True  # no fallback: unchanged
    assert H.flags(0.01, r, fallback=True)["full"] is False and H.flags(0.01, r, fallback=True)["a+b+c"] is True
    assert H.flags(0.01, dict(r, nonschedulable_above_null_mean=True), fallback=True)["full"] is True


def test_e_without_an_ns_profile_the_studies_are_unchanged():
    tl, units = _families(drop_dasha=(), late_dasha=())
    a = O.place_study(np.random.default_rng(3), _profile(16), tl[C.FAMILY_TRANSIT], [O._DayPmf(t) for t in tl[C.FAMILY_TRANSIT]], "N4")
    assert not any(o.ns for o in a)
