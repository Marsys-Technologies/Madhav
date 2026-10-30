"""SUR-RB-56: no scoring path reads an episode's ``schedulable`` label. Every Episode the scorer, the runner and the
harness see is an instrumented subclass whose ``schedulable`` read fails the test."""

from __future__ import annotations

from dataclasses import fields, replace

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, score_family
from services.rulebook.scorer.model import Episode
import services.rulebook.scorer.runner as R

from ._toy import planted_episodes, random_episodes, toy_world
from .test_review_fixes import AREAS, _cfg, _lock, _two_families, lockfiles, score_sample  # noqa: F401  (fixture re-used)
from .test_sur_rb_55_nonschedulable import _ns_world


class LabelRead(AssertionError):
    pass


class SpyEpisode(Episode):
    """An Episode whose ``schedulable`` attribute cannot be read."""

    def __getattribute__(self, name):
        if name == "schedulable":
            raise LabelRead("a scoring path read an episode's schedulable label")
        return object.__getattribute__(self, name)


def spy(eps):
    return [SpyEpisode(e.chart, e.area, e.direction, e.grade, e.lo, e.hi, bool(i % 2)) for i, e in enumerate(eps)]


def test_the_spy_fires_on_a_read():
    e = spy([Episode(0, AREAS[0], C.FAVOURABLE, C.G1, 10, 12)])[0]
    with pytest.raises(LabelRead):
        e.schedulable  # noqa: B018
    assert "schedulable" in {f.name for f in fields(Episode)}  # the field still exists; nothing reads it


def test_score_family_with_the_fallback_never_reads_the_label():
    tls, units = toy_world(90, n_charts=12, years=25, n_units=8)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    main = spy(planted_episodes(np.random.default_rng(4), tls, units, 8, 0.4, AREAS))
    ns = spy(random_episodes(np.random.default_rng(5), tls, 6, AREAS))
    for rule in ("m3", "p2_90"):
        r = score_family(ctx, main, C.ScoreConfig(draws=60, seed=1, fallback_primary_set=True), d7={"donor_rule_b": rule, "donor_rule_c": rule}, ns_episodes=ns)
        assert r["status"] == "scored" and r["nonschedulable_episodes_scored"] > 0


def test_the_runner_never_reads_the_label(tmp_path, lockfiles, monkeypatch):
    monkeypatch.setattr(R, "Episode", SpyEpisode)  # episodes the runner rebuilds (edge rules) are instrumented too
    ctx, eps = _two_families()
    lock = _ns_world(_lock(ctx, eps, lockfiles, tmp_path), ctx, eps)
    eps_s = {f: spy(v) for f, v in eps.items()}
    lock = replace(lock, nonschedulable_episodes={f: spy(v) for f, v in lock.nonschedulable_episodes.items()})
    res = score_sample(ctx, eps_s, _cfg(fallback_primary_set=True), lock)
    assert res["outcome"] in ("STRONG", "MIDDLE", "CHANCE-LEVEL", "NO_VERDICT")
    R.mechanical_dry_run(ctx, eps_s)


def test_the_harness_never_reads_the_label(monkeypatch):
    from services.rulebook.scorer_calib import harness as H
    from services.rulebook.scorer_calib import occurrences as O

    monkeypatch.setattr(O, "Episode", SpyEpisode)
    tls, units = toy_world(21, n_charts=16, years=25, n_units=8)
    t_units = [replace(u, plane=C.FAMILY_TRANSIT) for u in units]
    rows = tuple(tuple([(AREAS[0], C.FAVOURABLE, C.G2)] * 10 + [(AREAS[0], C.FAVOURABLE, C.G1)] * 4) for _ in tls)
    ns = tuple(tuple([(AREAS[0], C.FAVOURABLE, C.G2)] * 4) for _ in tls)
    cal = H.Calibration({C.FAMILY_DASHA: tls, C.FAMILY_TRANSIT: tls}, {C.FAMILY_DASHA: units, C.FAMILY_TRANSIT: t_units}, {}, O.CountsProfile(rows, ns), draws=40)
    cal.fallback = True
    for q in (0.0, 0.3):
        r = cal.run_study("N4", 0, q, C.FAMILY_DASHA, False, 3)
        assert all(r[f]["n_ns"] >= 0 for f in C.FAMILIES)
