"""Review VERIFY6 section 4: the five tests whose mutations survived, strengthened."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, nonschedulable_statistic, scorable_mask, score_family
import services.rulebook.scorer.runner as R
from services.rulebook.scorer_calib import cli
from services.rulebook.scorer_calib import harness as H
from services.rulebook.scorer_calib import occurrences as O

from ._toy import planted_episodes, random_episodes, toy_world
from .test_review_fixes import AREAS, _cfg, _lock, _two_families, lockfiles, score_sample  # noqa: F401  (fixture re-used)
from .test_sur_rb_55_nonschedulable import _ns_world
from .test_sur_rb_56_step8_e2e import build_world, sha


# (1) the scorable filter on the separate list
def test_an_unscorable_episode_in_the_separate_list_is_dropped_not_scored():
    tls, units = toy_world(90, n_charts=12, years=25, n_units=8)
    blind = replace(tls[0], states={k: np.full_like(v, -1) for k, v in tls[0].states.items()})  # chart 0: nothing assessed
    ctx = FamilyContext(C.FAMILY_DASHA, [blind] + tls[1:], units)
    ns = random_episodes(np.random.default_rng(3), ctx.tl, 8, AREAS)
    on0 = [e for e in ns if e.chart == 0]
    assert on0 and not any(scorable_mask(ctx, on0))
    cfg = C.ScoreConfig(draws=50, seed=1, fallback_primary_set=True)
    r = nonschedulable_statistic(ctx, ns, cfg)
    rest = nonschedulable_statistic(ctx, [e for e in ns if e.chart != 0], cfg)
    assert r == rest and r["nonschedulable_episodes_scored"] == sum(scorable_mask(ctx, ns))
    only = nonschedulable_statistic(ctx, on0, cfg)
    assert only == {"T_nonschedulable": None, "nonschedulable_episodes_scored": 0, "nonschedulable_above_null_mean": False}


# (2) the dry pass is run WITH the separate list (before the claim)
def test_the_dry_pass_receives_the_separate_list(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _ns_world(_lock(ctx, eps, lockfiles, tmp_path), ctx, eps)
    calls = []
    real = R.score_family

    def rec(c, e, cfg, *a, **k):
        calls.append({"draws": cfg.draws, "fallback": cfg.fallback_primary_set, "ns": k.get("ns_episodes"), "claimed": bool(list((tmp_path / "ledger").glob("*.run"))) if (tmp_path / "ledger").exists() else False})
        return real(c, e, cfg, *a, **k)

    monkeypatch.setattr(R, "score_family", rec)
    score_sample(ctx, eps, _cfg(fallback_primary_set=True), lock)
    dry = [c for c in calls if not c["claimed"]]
    assert dry and all(c["draws"] == 20 and c["fallback"] for c in dry)
    assert all(c["ns"] is not None and len(c["ns"]) > 0 for c in dry)


# (3) only_ns: exactly the marked occurrences inside the family horizon
def test_only_ns_returns_exactly_the_marked_occurrences():
    tls, units = toy_world(21, n_charts=10, years=25, n_units=8)
    rows = tuple(tuple([(AREAS[0], C.FAVOURABLE, C.G2)] * 8 + [(AREAS[1], C.UNFAVOURABLE, C.G1)] * 6) for _ in tls)
    ns = tuple(tuple([(AREAS[0], C.FAVOURABLE, C.G2)] * 3 + [(AREAS[1], C.UNFAVOURABLE, C.G1)] * 2) for _ in tls)
    prof = O.CountsProfile(rows, ns)
    occ = O.place_study(np.random.default_rng(5), prof, tls, [O._DayPmf(t) for t in tls], "N0")
    got = O.to_episodes(occ, tls, None, only_ns=True)
    want = [(o.chart, o.area, o.direction, o.grade, o.lo, o.hi) for o in occ if o.ns and o.lo >= tls[o.chart].h_start and o.hi <= tls[o.chart].h_end]
    assert [(e.chart, e.area, e.direction, e.grade, e.lo, e.hi) for e in got] == want
    assert 0 < len(got) < len(O.to_episodes(occ, tls))


# (4) and (5): the CLI loader sets the fallback from --count-set and applies the per-family horizon exclusions
def _args(w, tmp_path, count_set, with_cb=True):
    return SimpleNamespace(manifest=str(w["man"]), clusters=str(w["tab"]), admission=str(w["adm"]), count_blind=str(w["cb"]) if with_cb else None,
                           timelines=None, mean_per_chart=O.DECLARED_MEAN_PER_CHART, draws=30, seed=1, warm=0, count_set=count_set)


@pytest.fixture
def lworld(tmp_path, lockfiles):
    return build_world(tmp_path / "w", tmp_path)


def test_load_sets_the_fallback_from_the_count_set(lworld, tmp_path):
    cal = cli._load(_args(lworld, tmp_path, "all"))
    assert cal.fallback is True and cal.profile.ns_per_chart is not None and cal.fallback_note is None
    cal2 = cli._load(_args(lworld, tmp_path, "primary_nonschedulable"))
    assert cal2.fallback is False and cal2.profile.ns_per_chart is None
    assert cal.profile.total() > cal2.profile.total()  # the 'all' set's counts were read, not the non-schedulable ones
    cal3 = cli._load(_args(lworld, tmp_path, "all", with_cb=False))  # VERIFY6 H3: stand-in profile, no subset
    assert cal3.fallback is False and cal3.fallback_note.startswith("PROVISIONAL")


def test_load_applies_the_per_family_horizon_exclusions(lworld, tmp_path):
    adm = lworld["adm"]
    hz = json.loads((adm / "out" / "s5_horizons.json").read_text())
    codes = sorted(hz["charts"])
    hz["charts"][codes[1]]["families"]["dasha"]["under_12_years"] = True  # daśā only
    for f in ("dasha", "transit"):
        hz["charts"][codes[2]]["families"][f]["under_12_years"] = True  # both families
    (adm / "out" / "s5_horizons.json").write_text(json.dumps(hz, sort_keys=True))
    man = json.loads((adm / "out" / "TIMELINES_MANIFEST.json").read_text())
    man["files"]["out/s5_horizons.json"] = sha(adm / "out" / "s5_horizons.json")
    (adm / "out" / "TIMELINES_MANIFEST.json").write_text(json.dumps(man, sort_keys=True))
    cal = cli._load(_args(lworld, tmp_path, "primary_nonschedulable"))
    d = [t.code for t in cal.tls[C.FAMILY_DASHA]]
    t = [t.code for t in cal.tls[C.FAMILY_TRANSIT]]
    assert codes[1] not in d and codes[2] not in d and codes[2] not in t and codes[1] in t
    assert len(t) == len(codes) - 1 and len(d) == len(codes) - 2
