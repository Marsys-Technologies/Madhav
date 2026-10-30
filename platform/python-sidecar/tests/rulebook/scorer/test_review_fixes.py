"""One test per finding of the independent scorer review (SCORER_REVIEW.md 709b3f09...), as ruled by SUR-RB-37 and
yardstick v1.4. Each failed on the reviewed head (6917c91bf) or its successor 52808890.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer import core
from services.rulebook.scorer.core import (
    FamilyContext,
    assemble,
    d7_from_counts,
    direction_counts,
    donor_eligibility_counts,
    donor_recount,
    donor_sets,
    min_p_adjusted,
    pool_p,
    pool_p_all,
    run_donor_check,
    scorable_mask,
    score_family,
    simes_two,
)
from services.rulebook.scorer.footprint import touch_rates, unit_touch
from services.rulebook.scorer.model import ChartTimeline, Episode, MemberSpec, UnitSpec
from services.rulebook.scorer.outcome import CHANCE, NO_VERDICT, decide
import services.rulebook.scorer.runner as R
from services.rulebook.scorer.runner import (
    RunLedger,
    RunLock,
    RunRefused,
    claim_keys,
    prepare_episodes,
    recount_rows,
    score_sample_for_tests,
)


def score_sample(ctx, eps, cfg, lock, ledger=None):
    """Tests drive the test entry point (separate ledger path); the production entry point is exercised directly."""
    return score_sample_for_tests(ctx, eps, cfg, lock, str(ledger.dir) if ledger is not None else lock.ledger_dir)

from ._toy import BASE, make_units, month_window, random_episodes, runs_series, toy_world

AREAS = ["career_adv_change_entry", "illness_chronic_surgery"]
CAREER = AREAS[0]


# ── a complete, valid two-family sample and its lock ────────────────────────────────────────────────
def _two_families(n_charts=22, per_chart=22, seed=3):
    tls, units = toy_world(seed, n_charts=n_charts, years=25, n_units=10)
    t_units = [replace(u, plane=C.FAMILY_TRANSIT) for u in units]
    ctx = {C.FAMILY_DASHA: FamilyContext(C.FAMILY_DASHA, tls, units), C.FAMILY_TRANSIT: FamilyContext(C.FAMILY_TRANSIT, tls, t_units)}
    eps = random_episodes(np.random.default_rng(seed), tls, per_chart, AREAS)
    return ctx, {f: list(eps) for f in ctx}


def _manifest_and_table(units_by_family):
    """A UNIT_MANIFEST / cluster table pair that defines exactly the toy units (units_from_manifest reads it back)."""
    units, clusters = [], []
    for fam, units_ in units_by_family.items():
        for u in units_:
            members = [{"rulebook_id": m.rid, "status": "evaluable", "area_tags": sorted(m.area_tags), "transit_bodies": ["chandra"] if m.moon else []} for m in u.members()]
            units.append({"unit_id": u.unit_id, "plane": fam, "status": "evaluable", "kind": u.kind, "polarity": u.polarity, "members": members})
            if u.kind == "cluster":
                clusters.append({"cluster_id": u.unit_id, "scored_as": u.scored_as, "groups_scored": [[m.rid for m in g] for g in u.groups]})
    return {"units": units}, {"clusters": clusters}


@pytest.fixture
def lockfiles(tmp_path, monkeypatch):
    """Stand-in yardstick files, a manifest and cluster table defining the toy units, occurrence and birth-data files;
    the constants are pointed at their hashes."""
    files = {}
    ys = {}
    for name in C.YARDSTICK_SHA256:
        p = tmp_path / name
        p.write_text(f"stand-in {name}")
        ys[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        files["yardstick " + name] = str(p)
    ctx, _ = _two_families()
    man, tab = _manifest_and_table({f: c.units for f, c in ctx.items()})
    ct = tmp_path / "FINAL_CLUSTER_TABLE_v1_1.json"
    ct.write_text(json.dumps(tab))
    mf = tmp_path / "UNIT_MANIFEST_v1_0.json"
    mf.write_text(json.dumps(man))
    files["cluster_table"], files["unit_manifest"] = str(ct), str(mf)
    (tmp_path / "sample_events_v5_slim.csv").write_text("synthetic stand-in occurrences")
    (tmp_path / "BIRTH_DATA_v5.csv").write_text("synthetic stand-in birth data")
    monkeypatch.setattr(C, "YARDSTICK_SHA256", ys)
    monkeypatch.setattr(C, "CLUSTER_TABLE_SHA256", hashlib.sha256(ct.read_bytes()).hexdigest())
    monkeypatch.setattr(C, "DRAWS_PRODUCTION", 120)
    return files


def _lock(ctx, eps, files, tmp_path, **over):
    import platform

    from services.rulebook.scorer.footprint import family_testable

    d7, rows, donors = {}, {}, {}
    for f, c in ctx.items():
        kept, _ = prepare_episodes(c, eps[f])
        own = d7_from_counts(c, kept)
        don = donor_eligibility_counts(c, kept)
        d7[f] = {"testable": family_testable(c, kept)["testable"], "dir_testable": own["dir_testable"],
                 "z25_units": own["z25_units"] if len(own["z25_units"]) >= 8 else [], "donor_charts_b": don["b"], "donor_charts_c": don["c"]}
        rows[f] = [{"chart_id": k[0], "area": k[1], "direction": k[2], "grade": k[3], **v} for k, v in recount_rows(c, kept).items()]
        donors[f] = donor_recount(c, kept)  # stands in for count_blind v2's donor outputs
        diag = donors[f]["checks"]
        d7[f]["donor_rule_b"] = "m3" if diag["b"]["k11_floor_met_m3"] else "p2_90"
        d7[f]["donor_rule_c"] = "m3" if diag["c"]["k11_floor_met_m3"] else "p2_90"
    occ, birth = tmp_path / "sample_events_v5_slim.csv", tmp_path / "BIRTH_DATA_v5.csv"
    args = dict(
        occurrence_sha256=hashlib.sha256(occ.read_bytes()).hexdigest(), birth_data_sha256=hashlib.sha256(birth.read_bytes()).hexdigest(),
        scorer_sha256=C.source_sha256(), seed=7, fallback_primary_set=False, count_set="primary_nonschedulable",
        admitted={f: [t.code for t in c.tl] for f, c in ctx.items()}, d7=d7, count_rows=rows, files=files,
        ledger_dir=str(tmp_path / "ledger"), occurrence_path=str(occ), birth_data_path=str(birth),
        manifest_sha256=hashlib.sha256(Path(files["unit_manifest"]).read_bytes()).hexdigest(),
        numpy_version=np.__version__, python_version=platform.python_version(), donor_counts=donors,
    )
    args.update(over)
    return RunLock(**args)


def _cfg(**over):
    a = dict(draws=C.DRAWS_PRODUCTION, seed=7)
    a.update(over)
    return C.ScoreConfig(**a)


def _claims(tmp_path):
    d = tmp_path / "ledger"
    return sorted(p.name for p in d.glob("*.run")) if d.exists() else []


# ── B1: routine rows never crash, and nothing can fail after the claim ────────────────────────────────
def test_b1_month_straddling_the_horizon_mixed_and_g3_rows_are_dropped_before_the_claim(tmp_path, lockfiles):
    ctx, eps = _two_families()
    t = ctx[C.FAMILY_DASHA].tl[0]
    hs = date.fromordinal(t.h_start)
    straddle = Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(hs.year, hs.month))  # contains the horizon start
    assert straddle.lo < t.h_start <= straddle.hi
    edge_day = Episode(0, CAREER, C.FAVOURABLE, C.G1, t.h_end - 1, t.h_end + 1)  # day inside, window crosses the end
    mixed = Episode(1, CAREER, "mixed", C.G2, *month_window(2000, 5))
    g3 = Episode(1, CAREER, C.FAVOURABLE, "G3", date(2001, 1, 1).toordinal(), date(2001, 12, 31).toordinal())
    extra = [straddle, edge_day, mixed, g3]
    for f in eps:
        eps[f] = eps[f] + extra
    kept, drops = prepare_episodes(ctx[C.FAMILY_DASHA], eps[C.FAMILY_DASHA])
    assert drops == {"dropped_mixed": 1, "dropped_g3_or_range": 1, "dropped_horizon": 1, "clipped_day_windows": 1}
    assert any(e.lo == t.h_end - 1 and e.hi == t.h_end for e in kept)  # clipped to 2 days, kept (K2)
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    res = score_sample(ctx, eps, _cfg(), lock)
    assert res["outcome"] in ("STRONG", "MIDDLE", "CHANCE-LEVEL") and len(_claims(tmp_path)) == 1
    assert res["validation_drops"][C.FAMILY_DASHA]["dropped_horizon"] == 1


def test_b1_a_problem_found_by_validation_or_the_dry_pass_leaves_no_claim(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)

    def boom(*a, **k):
        raise ValueError("synthetic failure inside scoring")

    monkeypatch.setattr("services.rulebook.scorer.runner.score_family", boom)
    with pytest.raises(RunRefused, match="dry pass"):
        score_sample(ctx, eps, _cfg(), lock)
    assert _claims(tmp_path) == []  # refused before the claim: the sample is not spent


# ── S1 / v1.4 M1: Simes across the two schemes, each scheme's min-p in its own draws ─────────────────────
def test_s1_dasha_p1_is_simes_over_within_scheme_min_p():
    tls, units = toy_world(4, n_charts=16, years=30, n_units=10)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(4), tls, 14, AREAS)
    r = score_family(ctx, eps, C.ScoreConfig(draws=300, seed=1))
    p5, p15 = r["p_scheme"]["5y"], r["p_scheme"]["15y"]
    assert r["p1"] == pytest.approx(min(1.0, 2 * min(p5, p15), max(p5, p15)))
    assert r["scheme_combination"] == "simes"
    rb = score_family(ctx, eps, C.ScoreConfig(draws=300, seed=1, scheme_combination="bonferroni"))
    assert rb["p1"] == pytest.approx(min(1.0, 2 * min(p5, p15)))
    assert simes_two(0.01, 0.4) == 0.02 and simes_two(0.03, 0.04) == 0.04 and simes_two(0.6, 0.9) == 0.9
    rt = score_family(FamilyContext(C.FAMILY_TRANSIT, tls, [replace(u, plane=C.FAMILY_TRANSIT) for u in units]), eps, C.ScoreConfig(draws=300, seed=1))
    assert rt["scheme_combination"] == "single" and rt["p1"] == rt["p_scheme"]["5y"]


def test_s1_simes_is_not_conservative_like_the_independent_pairing():
    """On toy nulls the old 4-statistic min-p across independent streams had a mean p1 near 0.63 (review M-a: the
    band must exclude it)."""
    ps = []
    for s in range(100):
        if s % 20 == 0:
            tls, units = toy_world(800 + s, n_charts=16, years=40, n_units=8)
            ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
        r = score_family(ctx, random_episodes(np.random.default_rng(s), tls, 12, AREAS), C.ScoreConfig(draws=200, seed=s))
        ps.append(r["p1"])
    assert 0.42 < float(np.mean(ps)) < 0.58


# ── S2: the sealed D7 record decides, and the recount must agree, before the claim ───────────────────────
def test_s2_sealed_d7_is_read_and_a_disagreeing_recount_refuses_before_the_claim(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    bad = dict(lock.d7)
    bad[C.FAMILY_DASHA] = dict(bad[C.FAMILY_DASHA], dir_testable=not bad[C.FAMILY_DASHA]["dir_testable"])
    with pytest.raises(RunRefused, match="p_dir testability"):
        score_sample(ctx, eps, _cfg(), replace(lock, d7=bad))
    bad2 = dict(lock.d7)
    bad2[C.FAMILY_TRANSIT] = dict(bad2[C.FAMILY_TRANSIT], z25_units=["RB1-NOT-A-UNIT"] * 9)
    with pytest.raises(RunRefused, match="Z25"):
        score_sample(ctx, eps, _cfg(), replace(lock, d7=bad2))
    assert _claims(tmp_path) == []


def test_s2_score_family_uses_the_sealed_list_not_its_own():
    tls, units = toy_world(5, n_charts=18, years=25, n_units=12)
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    eps = random_episodes(np.random.default_rng(5), tls, 14, AREAS)
    r = score_family(ctx, eps, C.ScoreConfig(draws=100, seed=1), d7={"dir_testable": False, "z25_units": []})
    assert r["dir_testable"] is False and r["p_dir"] is None and r["z25_unit_list"] == [] and "Z25-5y" not in r["stats"]


# ── S3: A7 is counted on the daśā family only ─────────────────────────────────────────────────────────────
def test_s3_a7_counts_dasha_charts_only(tmp_path, lockfiles):
    ctx, eps = _two_families(n_charts=22)
    tls = ctx[C.FAMILY_DASHA].tl[:18]  # 18 daśā charts admitted, 22 transit charts
    ctx[C.FAMILY_DASHA] = FamilyContext(C.FAMILY_DASHA, tls, ctx[C.FAMILY_DASHA].units)
    eps[C.FAMILY_DASHA] = [e for e in eps[C.FAMILY_DASHA] if e.chart < 18] * 2
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    res = score_sample(ctx, eps, _cfg(), lock)
    assert res["outcome"] == NO_VERDICT and res["a7"]["dasha_charts"] == 18 and _claims(tmp_path) == []


# ── S4: footprint touch rate per SUR-RB-27 Q3 ─────────────────────────────────────────────────────────────
def _tl(states, n=900):
    return ChartTimeline("c", BASE - 100, BASE, BASE + n - 1, {k: v for k, v in states.items()})


def _unit(groups):
    gs = tuple(tuple(MemberSpec(r, frozenset([C.GENERAL])) for r in g) for g in groups)
    return UnitSpec("U", C.FAMILY_DASHA, "promotive", "cluster", gs)


def _every(k, n=900, start=0):
    a = np.zeros(n, dtype=np.int8)
    a[start::k] = 1
    return a


def test_s4_R_unit_is_the_mean_of_member_touch_rates_not_the_union():
    a, b = _every(10, start=0), _every(10, start=5)  # each touches 0.30 of 3-day windows; the union touches 0.60
    t = _tl({"A": a, "B": b})
    ra, rb = unit_touch(t, _unit([["A"]]), "3d"), unit_touch(t, _unit([["B"]]), "3d")
    r = unit_touch(t, _unit([["A", "B"]]), "3d")
    assert r == pytest.approx((ra + rb) / 2) and 0.25 < r < 0.35
    assert unit_touch(t, _unit([["A"], ["B"]]), "3d") > 0.55  # E unit: the OR of members


def test_s4_mixed_unit_is_the_mean_over_one_member_per_group_readings():
    a, b, c = _every(10, start=0), _every(10, start=5), _every(50, start=2)
    t = _tl({"A": a, "B": b, "C": c})
    want = np.mean([unit_touch(t, _unit([["A"], ["C"]]), "3d"), unit_touch(t, _unit([["B"], ["C"]]), "3d")])
    assert unit_touch(t, _unit([["A", "B"], ["C"]]), "3d") == pytest.approx(want)


def test_s4_not_assessed_is_never_false_and_under_half_assessed_windows_are_skipped():
    a = np.zeros(900, dtype=np.int8)
    a[:450] = -1  # first half not assessed
    a[600] = 1
    t = _tl({"A": a})
    r = unit_touch(t, _unit([["A"]]), "3d")
    assert r == pytest.approx(3 / (900 - 450 - 2 + 1))  # only fully/half-assessed windows count, all in the second half
    tr = touch_rates([t], [_unit([["A"]])])["U"]
    assert tr["3d"] == pytest.approx(r)


# ── S5: the claim key does not depend on list order, and is bound to the logged inputs ───────────────────
def test_s5_reordering_the_charts_cannot_buy_a_second_run(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    score_sample(ctx, eps, _cfg(), lock)
    rev = {}
    reps = {}
    for f, c in ctx.items():
        order = list(range(len(c.tl)))[::-1]
        pos = {old: new for new, old in enumerate(order)}
        rev[f] = FamilyContext(f, [c.tl[i] for i in order], c.units, c.gate_drop)
        reps[f] = [Episode(pos[e.chart], e.area, e.direction, e.grade, e.lo, e.hi, e.schedulable) for e in eps[f]]
    assert claim_keys(lock, rev) == claim_keys(lock, ctx)
    with pytest.raises(RunRefused, match="already been run"):
        score_sample(rev, reps, _cfg(), lock)
    # one episode fewer, same occurrence file: still the same opened sample, refused
    fewer = {f: v[:-1] for f, v in eps.items()}
    with pytest.raises(RunRefused, match="already been run"):
        score_sample(ctx, fewer, _cfg(), _lock(ctx, fewer, lockfiles, tmp_path))


def test_s5_the_ledger_has_one_fixed_logged_path(tmp_path, lockfiles):
    assert RunLedger().dir == Path(C.LEDGER_DIR) and C.LEDGER_DIR.endswith("10_engine/run-ledger")
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    with pytest.raises(RunRefused, match="fixed, logged ledger"):  # production: any other path is refused
        R.score_sample(ctx, eps, _cfg(), lock)
    assert _claims(tmp_path) == []


# ── SUR-RB-42 F2: no bypass on the canonical path; test mode only with a separate ledger ────────────────────────
def test_f2_the_production_entry_point_has_no_test_switch():
    import dataclasses
    import inspect

    assert "test_mode" not in {f.name for f in dataclasses.fields(RunLock)}
    assert not any("test" in p for p in inspect.signature(R.score_sample).parameters)


def test_f2_production_refuses_contexts_not_tied_to_step5_even_on_the_canonical_path(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path, ledger_dir=C.LEDGER_DIR)
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(_record(tmp_path, lock.occurrence_sha256, lock.birth_data_sha256)))
    with pytest.raises(RunRefused, match="not tied to the step-5"):
        R.score_sample(ctx, eps, _cfg(), lock)


def test_f2_test_mode_cannot_use_the_canonical_ledger(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    with pytest.raises(RunRefused, match="canonical ledger"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, C.LEDGER_DIR)
    with pytest.raises(RunRefused, match="canonical ledger"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, str(Path(C.LEDGER_DIR) / "sub"))
    with pytest.raises(RunRefused, match="canonical ledger"):
        R._run(ctx, eps, _cfg(), lock, RunLedger(C.LEDGER_DIR), _test=True)


def test_f2_test_mode_refuses_any_input_matching_a_logged_real_file_hash(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    real = tmp_path / "real_hashes.json"
    monkeypatch.setattr(C, "REAL_INPUT_HASHES_PATH", str(real))
    for logged in ({"occurrence": lock.occurrence_sha256}, {"birth": lock.birth_data_sha256}, {"count_blind": {"COUNT_BLIND_UNITS.csv": "c" * 64}}):
        real.write_text(json.dumps(logged))
        lk = replace(lock, count_blind_sha256={"COUNT_BLIND_UNITS.csv": "c" * 64})
        with pytest.raises(RunRefused, match="logged real-file hash"):
            score_sample_for_tests(ctx, eps, _cfg(), lk, lock.ledger_dir)
    # a file inside the sample store is refused too
    store = tmp_path / "store"
    store.mkdir()
    (store / "occ.csv").write_text("synthetic stand-in")
    monkeypatch.setattr(C, "SAMPLE_STORE", str(store))
    real.write_text("{}")
    with pytest.raises(RunRefused, match="sample store"):
        score_sample_for_tests(ctx, eps, _cfg(), replace(lock, occurrence_path=str(store / "occ.csv")), lock.ledger_dir)
    assert _claims(tmp_path) == []


def test_n5_occurrence_and_birth_files_are_rehashed_before_the_claim(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    (tmp_path / "sample_events_v5_slim.csv").write_text("a different occurrence file")
    with pytest.raises(RunRefused, match="occurrence file"):
        score_sample(ctx, eps, _cfg(), lock)
    with pytest.raises(RunRefused, match="birth-data"):
        score_sample(ctx, eps, _cfg(), replace(lock, birth_data_path=None))
    assert _claims(tmp_path) == []


def test_s8_units_must_be_those_of_the_hashed_manifest(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    d = ctx[C.FAMILY_DASHA]
    ctx2 = dict(ctx)
    ctx2[C.FAMILY_DASHA] = FamilyContext(C.FAMILY_DASHA, d.tl, d.units[:-1], d.gate_drop)  # one unit missing
    with pytest.raises(RunRefused, match="hashed manifest"):
        score_sample(ctx2, eps, _cfg(), lock)
    with pytest.raises(RunRefused, match="unit manifest does not match"):
        score_sample(ctx, eps, _cfg(), replace(lock, manifest_sha256="0" * 64))


def test_s8_timelines_must_be_the_step5_artefacts(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    with pytest.raises(RunRefused, match="step-5"):
        score_sample(ctx, eps, _cfg(), _lock(ctx, eps, lockfiles, tmp_path, admission_dir=str(tmp_path / "no-such-dir")))
    lk = _lock(ctx, eps, lockfiles, tmp_path)
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(_record(tmp_path, lk.occurrence_sha256, lk.birth_data_sha256)))
    with pytest.raises(RunRefused, match="not tied to the step-5"):
        R.score_sample(ctx, eps, _cfg(), _lock(ctx, eps, lockfiles, tmp_path, ledger_dir=C.LEDGER_DIR))
    assert _claims(tmp_path) == []


def test_m9_numpy_and_python_versions_are_pinned(tmp_path, lockfiles):
    ctx, eps = _two_families()
    with pytest.raises(RunRefused, match="pinned"):
        score_sample(ctx, eps, _cfg(), _lock(ctx, eps, lockfiles, tmp_path, numpy_version="0.0.0"))


def test_n3_the_sealed_testability_flag_is_recounted(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    bad = {f: dict(v) for f, v in lock.d7.items()}
    bad[C.FAMILY_TRANSIT]["testable"] = not bad[C.FAMILY_TRANSIT]["testable"]
    with pytest.raises(RunRefused, match="testability"):
        score_sample(ctx, eps, _cfg(), replace(lock, d7=bad))


def test_n4_a_crash_after_the_claim_still_spends_the_sample(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    real = R.descriptive_hits
    calls = {"n": 0}

    def flaky(*a, **k):  # passes in the dry pass, fails in the real run (after the claim)
        calls["n"] += 1
        if calls["n"] > len([f for f in ctx]):
            raise RuntimeError("post-claim failure")
        return real(*a, **k)

    monkeypatch.setattr(R, "descriptive_hits", flaky)
    with pytest.raises(RuntimeError):
        score_sample(ctx, eps, _cfg(), lock)
    assert len(_claims(tmp_path)) == 1  # the claim is never released
    monkeypatch.setattr(R, "descriptive_hits", real)
    with pytest.raises(RunRefused, match="already been run"):
        score_sample(ctx, eps, _cfg(), lock)


def test_n7_the_dry_pass_covers_part_e_and_writing_the_result(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    for target in ("decide", "write_result"):
        orig = getattr(R, target)

        def boom(*a, **k):
            raise ValueError(f"{target} broken")

        monkeypatch.setattr(R, target, boom)
        with pytest.raises(RunRefused, match="dry pass"):
            score_sample(ctx, eps, _cfg(), lock)
        monkeypatch.setattr(R, target, orig)
    assert _claims(tmp_path) == [] and not list((tmp_path).glob(".dry-pass-*"))


# ── S6 and S7 are in test_calib.py (gate under m = 1 and m = 2; NOT_GATE conditions; q = 30% sanity) ──────────


# ── S8: hashes of the files actually loaded ───────────────────────────────────────────────────────────────
def test_s8_the_inputs_actually_loaded_are_hashed_and_checked(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    Path(lockfiles["cluster_table"]).write_text('{"tampered": true}')
    with pytest.raises(RunRefused, match="cluster table"):
        score_sample(ctx, eps, _cfg(), lock)
    files = dict(lockfiles)
    files.pop(next(k for k in files if k.endswith("v1_4_LOCKED.md")))
    with pytest.raises(RunRefused, match="yardstick"):
        score_sample(ctx, eps, _cfg(), replace(lock, files=files))
    assert _claims(tmp_path) == []


def test_s8_result_header_carries_the_computed_hashes(tmp_path, lockfiles):
    ctx, eps = _two_families()
    res = score_sample(ctx, eps, _cfg(), _lock(ctx, eps, lockfiles, tmp_path))
    assert res["input_sha256"]["cluster_table"] == hashlib.sha256(Path(lockfiles["cluster_table"]).read_bytes()).hexdigest()
    assert len(res["yardstick_sha256"]) == 6 and res["numpy"] and res["python"]


# ── M1: the opposite-polarity mask narrows the shift set only for the direction statistic ────────────────────
def test_m1_opposite_mask_does_not_narrow_the_shifts_when_direction_is_not_computed():
    n = 365 * 8
    units = make_units([("P", "promotive", [[("MP", [C.GENERAL])]]), ("O", "obstructive", [[("MO", [C.GENERAL])]])])
    rng = np.random.default_rng(2)
    t = ChartTimeline("c0", BASE - 9000, BASE, BASE + n - 1, {"MP": runs_series(rng, n, 0.2, 10), "MO": runs_series(rng, n, 0.2, 10)})
    t.states["MO"][200:1000] = -1  # the opposite unit is not assessed over a long stretch
    ctx = FamilyContext(C.FAMILY_DASHA, [t], units)
    ep = [Episode(0, CAREER, C.FAVOURABLE, C.G2, *month_window(1993, 6))]
    with_dir = assemble(ctx, "5y", ep, True, False)
    no_dir = assemble(ctx, "5y", ep, False, False)
    assert no_dir.recs[0]["shifts"].size > with_dir.recs[0]["shifts"].size


# ── M2: the direction set is the K4/L1 applicability set ───────────────────────────────────────────────────
def test_m2_direction_set_requires_an_applicable_half_assessed_opposite_unit():
    n = 365 * 8
    units = make_units([("P", "promotive", [[("MP", [C.GENERAL])]]), ("O", "obstructive", [[("MO", [C.GENERAL])]])])
    t = ChartTimeline("c0", BASE - 9000, BASE, BASE + n - 1, {"MP": runs_series(np.random.default_rng(3), n, 0.2, 10), "MO": runs_series(np.random.default_rng(4), n, 0.2, 10)})
    lo, hi = month_window(1992, 3)
    t.states["MO"][lo - BASE : hi - BASE + 1 - 5] = -1  # opposite member less than half assessed in this window
    ctx = FamilyContext(C.FAMILY_DASHA, [t], units)
    ep = Episode(0, CAREER, C.FAVOURABLE, C.G2, lo, hi)
    assert core.opposite_applicable_mask(ctx, [ep]) == [False]
    assert direction_counts(ctx, [ep])["episodes"] == 0


# ── M3: ties within 1e-12 count against the observed ───────────────────────────────────────────────────────
def test_m3_ties_within_tolerance_count_against():
    pool = np.array([0.5, 0.5 + 1e-15, 0.2, 0.5 - 1e-15])
    # the two draws within 1e-15 of the observed tie with it and count against it: (1 + 2) / 4
    assert pool_p(pool) == 0.75
    assert pool_p_all(pool)[0] == 0.75
    adj, _ = min_p_adjusted({"T": pool})
    assert adj == 0.75


# ── M4 / v1.4 M3: a donor is eligible only with a defined coverage for every episode; never a zero deviation ──
def test_m4_donor_with_an_unassessed_window_is_not_eligible_and_never_imputed():
    tls, units = toy_world(6, n_charts=10, years=20, n_units=4)
    eps = [Episode(c, CAREER, C.FAVOURABLE, C.G2, *month_window(1995, 1 + c)) for c in range(10)]
    ctx = FamilyContext(C.FAMILY_DASHA, tls, units)
    before = donor_sets(ctx, eps, False)[0]["elig"]
    assert 3 in before
    lo, hi = month_window(1995, 1)
    for rid in list(tls[3].states):  # donor 3: chart 0's episode window is not assessed for any member
        tls[3].states[rid][lo - tls[3].h_start : hi - tls[3].h_start + 1] = -1
    ctx2 = FamilyContext(C.FAMILY_DASHA, tls, units)
    after = donor_sets(ctx2, eps, False)[0]["elig"]
    assert 3 not in after and set(after) == set(before) - {3}
    r = run_donor_check(ctx2, eps, 50, np.random.default_rng(1), False)
    assert r["T"] is not None  # computed from defined coverages only (no NaN, no zero fill)


# ── M5: no testable family is NO_VERDICT; m cannot change after the p-values start ─────────────────────────
def test_m5_no_testable_family_is_no_verdict_and_an_undefined_p1_is_an_error():
    assert decide({}, {})["outcome"] == NO_VERDICT
    assert decide({"dasha": {"p1": 0.5, "p2": 0.5, "p3": 0.5, "p_dir": 0.5}}, {"dasha": False})["outcome"] == NO_VERDICT
    with pytest.raises(ValueError):
        decide({"dasha": {"p1": None}}, {"dasha": True})
    assert decide({"dasha": {"p1": 0.5, "p2": 0.5, "p3": 0.5, "p_dir": 0.5}}, {"dasha": True})["outcome"] == CHANCE


# ── M6: draws, seed, A7 flag and the scheme combination must equal the logged ones ─────────────────────────
@pytest.mark.parametrize(
    "cfg_over,msg",
    [({"draws": 50}, "draws"), ({"seed": 8}, "seed"), ({"fallback_primary_set": True}, "A7"), ({"scheme_combination": "bonferroni"}, "scheme")],
)
def test_m6_run_configuration_must_match_the_lock(tmp_path, lockfiles, cfg_over, msg):
    ctx, eps = _two_families()
    with pytest.raises(RunRefused, match=msg):
        score_sample(ctx, eps, _cfg(**cfg_over), _lock(ctx, eps, lockfiles, tmp_path))
    assert _claims(tmp_path) == []


def test_m6_a_chart_outside_the_logged_admitted_set_is_refused(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    adm = dict(lock.admitted)
    adm[C.FAMILY_DASHA] = adm[C.FAMILY_DASHA][:-1]
    with pytest.raises(RunRefused, match="admitted"):
        score_sample(ctx, eps, _cfg(), replace(lock, admitted=adm))


def test_m6_count_blind_disagreement_is_refused_before_the_claim(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    rows = {f: [dict(r) for r in v] for f, v in lock.count_rows.items()}
    rows[C.FAMILY_DASHA][0]["scored_applicable"] += 1
    with pytest.raises(RunRefused, match="count_blind"):
        score_sample(ctx, eps, _cfg(), replace(lock, count_rows=rows))
    assert _claims(tmp_path) == []


# ── M8 / v1.4 M2: MIXED percentile = mean over readings ──────────────────────────────────────────────────────
def test_m8_mixed_unit_percentile_is_the_mean_of_its_readings_percentiles():
    n = 365 * 6
    rng = np.random.default_rng(9)
    st = {k: runs_series(rng, n, 0.2, 12) for k in ("A", "B", "C")}
    t = ChartTimeline("c0", BASE - 9000, BASE, BASE + n - 1, st)
    mixed = _unit([["A", "B"], ["C"]])
    ctx = FamilyContext(C.FAMILY_DASHA, [t], [mixed])
    v = mixed.variant(CAREER, True)
    got = ctx.unit_curve("5y", 0, 0, 31, v)
    r1 = ctx.comp_curve("5y", 0, 0, 31, ("or", ("A", "C")))
    r2 = ctx.comp_curve("5y", 0, 0, 31, ("or", ("B", "C")))
    assert np.allclose(got, (r1.astype(float) + r2) / 2, atol=1e-6, equal_nan=True)


# ── M9: study files are identical bytes whatever the worker order ───────────────────────────────────────────
def test_m9_study_lines_are_sorted_before_hashing(tmp_path, monkeypatch):
    from services.rulebook.scorer_calib import harness as H

    class Stub:
        def run_study(self, model, i, q=0.0, target="dasha", sparse=False, min_usable=0):
            return {"model": model, "i": i}

    out1, out2 = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    H.run_many(Stub(), [("N0", i, 0.0, "dasha", False) for i in (3, 1, 2)], 1, str(out1))
    H.run_many(Stub(), [("N0", i, 0.0, "dasha", False) for i in (2, 3, 1)], 1, str(out2))
    assert out1.read_bytes() == out2.read_bytes()


def test_n6_with_d7_known_every_study_uses_the_single_m_d7_fixed():
    from services.rulebook.scorer_calib import harness as H
    from services.rulebook.scorer_calib import occurrences as O

    tls, units = toy_world(21, n_charts=16, years=25, n_units=8)
    t_units = [replace(u, plane=C.FAMILY_TRANSIT) for u in units]
    prof = O.CountsProfile(tuple(tuple([(CAREER, C.FAVOURABLE, C.G2)] * 3) for _ in tls))  # too few to be testable
    cal = H.Calibration({C.FAMILY_DASHA: tls, C.FAMILY_TRANSIT: tls}, {C.FAMILY_DASHA: units, C.FAMILY_TRANSIT: t_units}, {}, prof, draws=50)
    r = cal.run_study("N0", 0)
    assert r["dasha"]["testable"] is False  # per-study counts say untestable
    cal.fixed_testable = {C.FAMILY_DASHA: True, C.FAMILY_TRANSIT: False}
    r2 = cal.run_study("N0", 0)
    assert r2["dasha"]["testable"] is True and r2["transit"]["testable"] is False
    if r2["dasha"]["p1"] is not None:
        assert r2["dasha"]["adj"] == r2["dasha"]["p1"]  # m = 1: Holm leaves p1 unchanged


# ── SUR-RB-42 F1: the one-run rule is per sample; a scorer edit cannot open a second claim ─────────────────────
def test_f1_an_edited_scorer_cannot_run_the_same_sample_again(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    score_sample(ctx, eps, _cfg(), lock)
    edited = "e" * 64  # the scorer source after an edit
    monkeypatch.setattr(C, "source_sha256", lambda: edited)
    with pytest.raises(RunRefused, match="already been run"):
        score_sample(ctx, eps, _cfg(), replace(lock, scorer_sha256=edited))
    assert len(_claims(tmp_path)) == 1


def test_f1_the_key_is_the_sample_and_the_claim_records_the_scorer_and_yardsticks(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    assert claim_keys(lock, ctx) == claim_keys(replace(lock, scorer_sha256="0" * 64), ctx)  # the scorer is not in the key
    assert claim_keys(lock, ctx) != claim_keys(replace(lock, birth_data_sha256="1" * 64), ctx)
    score_sample(ctx, eps, _cfg(), lock)
    rec = json.loads((tmp_path / "ledger" / _claims(tmp_path)[0]).read_text())
    assert rec["scorer_sha256"] == C.source_sha256() and len(rec["yardstick_sha256"]) == len(C.YARDSTICK_SHA256)
    assert rec["occurrence_sha256"] == lock.occurrence_sha256 and rec["birth_data_sha256"] == lock.birth_data_sha256
    # a different scorer hash in the lock refuses before anything else (validation)
    with pytest.raises(RunRefused):
        score_sample(ctx, eps, _cfg(), replace(lock, scorer_sha256="0" * 64))


# ── SUR-RB-43: the claim-key inputs come from the logged lock record (lock step 4) ─────────────────────────────
def _record(tmp_path, occ, birth, entry="CUTOFF-AND-FILE-HASHES-V5-20261030"):
    p = tmp_path / "DECISIONS_SURROGATE.jsonl"
    rows = [{"id": "SOMETHING-ELSE", "files_sha256": {}},
            {"id": entry, "files_sha256": {"sample_events_v5_slim.csv": occ, "BIRTH_DATA_v5.csv": birth, "sample_events_v5.csv": "f" * 64}}]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return p


def test_sur_rb_43_lock_record_reader():
    rec = R.read_lock_record
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        p = _record(Path(d), "a" * 64, "b" * 64)
        got = rec(str(p))
        assert got["occurrence"] == "a" * 64 and got["birth_data"] == "b" * 64 and got["all"]["sample_events_v5.csv"] == "f" * 64
        with pytest.raises(RunRefused, match="not found"):
            rec(str(p), "NO-SUCH-ENTRY")
        p.write_text(json.dumps({"id": "CUTOFF-AND-FILE-HASHES-V5-20261030", "files_sha256": {"BIRTH_DATA_v5.csv": "b" * 64}}) + "\n")
        with pytest.raises(RunRefused, match="claim-key"):
            rec(str(p))


@pytest.mark.skipif(not Path(C.LOCK_LEDGER_PATH).exists(), reason="the governance ledger is not on this machine")
def test_sur_rb_43_the_logged_record_names_the_slim_occurrence_file_and_birth_data():
    got = R.read_lock_record()
    assert got["occurrence"] == "4be3abadb6348860c9f6b47b9c8aedab8527bee75bd816d76d0b3f8055d0f37d"
    assert got["birth_data"] == "4288cca3cd277d54cfe5f0d24b57830b47f7b8a692373ee4b5fa7b52030214d5"


def test_sur_rb_43_production_accepts_only_the_logged_claim_key_hashes(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path, ledger_dir=C.LEDGER_DIR)
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(_record(tmp_path, "9" * 64, lock.birth_data_sha256)))
    with pytest.raises(RunRefused, match="logged lock record"):
        R.score_sample(ctx, eps, _cfg(), lock)
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(_record(tmp_path, lock.occurrence_sha256, lock.birth_data_sha256)))
    other = tmp_path / "sample_events_v5.csv"  # same bytes, but not the SLIM file the key names
    other.write_bytes(Path(lock.occurrence_path).read_bytes())
    with pytest.raises(RunRefused, match="sample_events_v5_slim.csv"):
        R.score_sample(ctx, eps, _cfg(), replace(lock, occurrence_path=str(other)))


def test_sur_rb_43_test_mode_refuses_any_hash_in_the_real_lock_record(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    monkeypatch.setattr(C, "REAL_INPUT_HASHES_PATH", str(tmp_path / "none.json"))
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(_record(tmp_path, lock.occurrence_sha256, "b" * 64)))
    with pytest.raises(RunRefused, match="logged real-file hash"):
        score_sample(ctx, eps, _cfg(), lock)


def test_sur_rb_43_result_reports_pre_1930_charts_with_death_source_none(monkeypatch):
    from datetime import date as _d

    tls, units = toy_world(31, n_charts=4, years=10, n_units=2)
    for t, y in zip(tls, (1925, 1928, 1931, 1920)):
        t.birth = _d(y, 6, 1).toordinal()
    ctx = {C.FAMILY_DASHA: FamilyContext(C.FAMILY_DASHA, tls, units)}

    class Adm:
        def __init__(self, d):
            self.horizons = {"charts": {tls[0].code: {"death_source": "none"}, tls[1].code: {"death_source": "wikidata"},
                                        tls[2].code: {"death_source": "none"}, tls[3].code: {"death_source": "none"}}}

    import services.rulebook.scorer.inputs as I

    monkeypatch.setattr(I, "AdmissionInputs", Adm)
    lock = type("L", (), {"admission_dir": "x"})()
    assert R._pre1930_alive_by_default(ctx, lock) == 2  # 1925 and 1920; 1928 has a death source, 1931 is after 1930
    assert R._pre1930_alive_by_default(ctx, type("L", (), {"admission_dir": None})()) is None
