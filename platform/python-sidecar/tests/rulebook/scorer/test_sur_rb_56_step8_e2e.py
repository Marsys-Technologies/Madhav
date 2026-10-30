"""Review VERIFY6 H1: the step-8 invocation end to end on FULLY SYNTHETIC inputs:
run_step8.main -> the production runner -> the claim -> the result, with the canonical ledger redirected to a temporary
directory (conftest; never 10_engine/run-ledger). Every artefact the script reads is written here in its logged format
(step-5 admission directory, count_blind V3 outputs, unit manifest and cluster table, the locked yardstick files, the
slim occurrence file and the decisions-ledger entries), so the test exercises the real plumbing, including the
RunLock.files the runner hashes."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
from dataclasses import replace
from datetime import date
from pathlib import Path

import numpy as np
import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, d7_from_counts, donor_recount
from services.rulebook.scorer.footprint import family_testable
from services.rulebook.scorer.inputs import AGG_INTS, AGG_TEXT, DONOR_COLUMNS, DONOR_DIAG_COLUMNS, DONOR_ELIG_COLUMNS, TIMELINE_SCHEMA, UNIT_COLUMNS
from services.rulebook.scorer.model import Episode, MemberSpec, UnitSpec
import services.rulebook.scorer.runner as R
from services.rulebook.step8 import run_step8 as S8

from ._toy import FAKE_COUNT_BLIND_SHA, FAKE_COUNT_BLIND_TESTS_SHA, ledger_lines, random_episodes, toy_world
from .test_inputs import _s1_resolve
from .test_review_fixes import AREAS, _manifest_and_table, lockfiles  # noqa: F401  (fixture re-used)

THRESHOLD = 3


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _wjson(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, sort_keys=True))


def _wcsv(p, header, rows):
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def _runs(a):
    out, prev = [], None
    for i, v in enumerate(a.tolist()):
        s = {1: "T", 0: "F", -1: "N"}[v]
        if s != prev:
            out.append([i, s])
            prev = s
    return out


def _transit(units):
    """Transit units with their own member ids (one plane per member in a step-5 timeline)."""
    out = []
    for u in units:
        groups = tuple(tuple(MemberSpec("T" + m.rid, m.area_tags, m.moon) for m in g) for g in u.groups)
        out.append(UnitSpec(u.unit_id.replace("U", "TU"), C.FAMILY_TRANSIT, u.polarity, u.kind, groups))
    return out


def build_world(root: Path, ys_dir: Path):
    tls, units = toy_world(3, n_charts=22, years=25, n_units=10)
    t_units = _transit(units)
    adm, cbd = root / "admission-v1_1", root / "admission-v1_1" / "out" / "count_blind"
    codes = [t.code for t in tls]
    # step-5 admission directory
    hz = {"charts": {}, "provenance": {}, "step": "s5", "under_12_years": {}}
    for t in tls:
        first = date.fromordinal(t.h_start)
        b = date.fromordinal(t.birth)
        members = {}
        for u, pl in [(u, C.FAMILY_DASHA) for u in units] + [(u, C.FAMILY_TRANSIT) for u in t_units]:
            for m in u.members():
                src = m.rid[1:] if pl == C.FAMILY_TRANSIT else m.rid
                members[m.rid] = {"unit": u.unit_id, "plane": pl, "polarity": u.polarity, "chart_level": False, "runs": _runs(t.states[src])}
        _wjson(adm / "timelines" / f"{t.code}.json", {
            "timeline_schema": TIMELINE_SCHEMA, "chart_id": t.code, "confirmatory": True,
            "range": {"first": first.isoformat(), "last": date.fromordinal(t.h_end).isoformat(), "days": t.n_days},
            "horizon_inputs": {"horizon_start_12y": date(b.year + 12, b.month, b.day).isoformat()}, "members": members})
        fam = {"start": first.isoformat(), "end": date.fromordinal(t.h_end).isoformat(), "days": t.n_days, "years": t.n_days / 365.25, "under_12_years": False}
        hz["charts"][t.code] = {"confirmatory": "Y", "death_source": "alive", "range_first": first.isoformat(), "families": {C.FAMILY_DASHA: dict(fam), C.FAMILY_TRANSIT: dict(fam)}}
    _wjson(adm / "out" / "s5_horizons.json", hz)
    _wjson(adm / "out" / "s6_admit.json", {"admitted": codes, "dry_run_set": [], "donor_pool_candidates": codes, "ledger": {c: {"admitted": True, "reason": None} for c in codes}})
    _wjson(adm / "out" / "s1_resolve.json", _s1_resolve(codes, set()))
    _wjson(adm / "out" / "s7_footprint.json", {"summary": {f: {"3day": {"dropped_units": []}, "month": {"dropped_units": []}} for f in C.FAMILIES}})
    files = {f"{sub}/{p.name}": sha(p) for sub in ("timelines", "out") for p in sorted((adm / sub).glob("*.json"))}
    _wjson(adm / "out" / "TIMELINES_MANIFEST.json", {"manifest": "synthetic", "files": files})
    # unit manifest and cluster table
    man, tab = _manifest_and_table({C.FAMILY_DASHA: units, C.FAMILY_TRANSIT: t_units})
    _wjson(root / "UNIT_MANIFEST_v1_0.json", man)
    _wjson(root / "FINAL_CLUSTER_TABLE_v1_1.json", tab)
    # the slim occurrence file: schedulable and non-schedulable occurrences mixed in every chart
    rng = np.random.default_rng(11)
    occ_rows = []
    for e in random_episodes(rng, tls, 34, AREAS):
        d = date.fromordinal(e.lo + 1 if e.grade == C.G1 else e.lo)
        occ_rows.append([codes[e.chart], d.year, d.month, d.day if e.grade == C.G1 else "", "day" if e.grade == C.G1 else "month",
                         "True" if rng.random() < 0.35 else "False", e.area, e.direction, "Y", "Y"])
    (root / "sample").mkdir()
    occ = root / "sample" / "sample_events_v5_slim.csv"
    _wcsv(occ, S8.SLIM_COLUMNS, occ_rows)
    birth = root / "sample" / "BIRTH_DATA_v5.csv"
    birth.write_text("synthetic birth data\n")
    # count_blind V3 outputs from the same construction (the plumbing under test, not count_blind's equivalence)
    rows = S8.read_slim(occ)
    from services.rulebook.scorer.inputs import AdmissionInputs
    from services.rulebook.scorer.model import units_from_manifest

    A = AdmissionInputs(str(adm))
    agg, don, uni, dele, ddg, testable = [], [], [], [], [], []
    for f in C.FAMILIES:
        ctx = FamilyContext(f, A.timelines(f, codes), units_from_manifest(man, tab, f), {})
        hzf = {t.code: (date.fromordinal(t.h_start), date.fromordinal(t.h_end)) for t in ctx.tl}
        for st in ("all", "primary_nonschedulable"):
            eps, _g3 = S8.family_episodes(rows, codes, hzf, f, C, Episode, st)
            kept, _ = R.prepare_episodes(ctx, eps)
            for (cid, area, direction, grade), v in sorted(R.recount_rows(ctx, kept).items()):
                agg.append([cid, f, st, area, direction, grade] + [v.get(k, 0) for k in AGG_INTS])
            for cid in codes:
                don.append([THRESHOLD, f, st, cid, 1, 20, 20])
            if st == "all":
                own = d7_from_counts(ctx, kept)
                for u in ctx.units:
                    uni.append([THRESHOLD, f, st, u.unit_id, 10 if u.unit_id in own["z25_units"] else 0])
                rec = donor_recount(ctx, kept)
                for cid, r in sorted(rec["charts"].items()):
                    dele.append([THRESHOLD, f, st, cid] + [r[k] for k in DONOR_ELIG_COLUMNS[4:]])
                for chk in ("b", "c"):
                    ddg.append([THRESHOLD, f, st, chk] + [rec["checks"][chk][k] for k in DONOR_DIAG_COLUMNS[4:]])
                rules = {k: ("m3" if rec["checks"][k]["k11_floor_met_m3"] else "p2_90") for k in ("b", "c")}
                if family_testable(ctx, kept, donor_rules=rules)["testable"]:
                    testable.append(f)
    cbd.mkdir(parents=True)
    _wcsv(cbd / "COUNT_BLIND_AGGREGATES.csv", list(AGG_TEXT + AGG_INTS), agg)
    _wcsv(cbd / "COUNT_BLIND_DONORS.csv", list(DONOR_COLUMNS), don)
    _wcsv(cbd / "COUNT_BLIND_UNITS.csv", list(UNIT_COLUMNS), uni)
    _wcsv(cbd / "COUNT_BLIND_DONOR_ELIGIBILITY.csv", list(DONOR_ELIG_COLUMNS), dele)
    _wcsv(cbd / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv", list(DONOR_DIAG_COLUMNS), ddg)
    outs = {p.name: sha(p) for p in sorted(cbd.glob("*.csv"))}
    _wjson(cbd / "COUNT_BLIND_RUN.json", {"script": "count_blind.py", "script_sha256": FAKE_COUNT_BLIND_SHA, "tests_sha256": FAKE_COUNT_BLIND_TESTS_SHA, "outputs_sha256": outs})
    return {"adm": adm, "cb": cbd, "man": root / "UNIT_MANIFEST_v1_0.json", "tab": root / "FINAL_CLUSTER_TABLE_v1_1.json",
            "occ": occ, "birth": birth, "testable": testable, "outs": {**outs, "COUNT_BLIND_RUN.json": sha(cbd / "COUNT_BLIND_RUN.json")}}


def yardstick_entries(ys_dir):
    """YARDSTICK-V1_x-LOCKED entries in the logged format for every yardstick file in ys_dir."""
    out = []
    for p in sorted(Path(ys_dir).glob("YARDSTICK_v1_*_LOCKED.md")):
        n = p.name.split("_")[2]
        out.append({"id": f"YARDSTICK-V1_{n}-LOCKED", "file": f"02_plans/rule-book-programme/{p.name} (library, 0400)", "sha256": sha(p)})
    return out


@pytest.fixture
def world(tmp_path, lockfiles, monkeypatch):
    w = build_world(tmp_path / "w", tmp_path)
    led = tmp_path / "DECISIONS_SURROGATE.jsonl"
    v16 = tmp_path / "YARDSTICK_v1_6_LOCKED.md"  # a later locked version the scorer itself does not list (SUR-RB-44)
    v16.write_text("stand-in YARDSTICK_v1_6_LOCKED.md")
    lines = ledger_lines(sha(w["occ"]), sha(w["birth"])) + [{"id": "COUNT-BLIND-V3-RUN-20261030", "outputs_sha256": w["outs"]}]
    lines += yardstick_entries(tmp_path)
    w["ledger_lines"], w["ledger"] = lines, led
    led.write_text("\n".join(json.dumps(r) for r in lines) + "\n")
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(led))
    monkeypatch.setattr(C, "CLUSTER_TABLE_SHA256", sha(w["tab"]))
    for k, v in (("ADM", w["adm"]), ("CB", w["cb"]), ("UNIT_MANIFEST", w["man"]), ("CLUSTER_TABLE", w["tab"]), ("YARDSTICK_DIR", tmp_path)):
        monkeypatch.setattr(S8, k, Path(v), raising=False)
    monkeypatch.setattr(S8, "LOGGED", {"TIMELINES_MANIFEST.json": sha(w["adm"] / "out" / "TIMELINES_MANIFEST.json"), "UNIT_MANIFEST_v1_0.json (rev4)": sha(w["man"]),
                                       "FINAL_CLUSTER_TABLE_v1_1.json": sha(w["tab"]), "s7_footprint.json": sha(w["adm"] / "out" / "s7_footprint.json")})
    assert Path(C.LEDGER_DIR).resolve() != Path(S8.LIB / "10_engine/run-ledger").resolve()  # the conftest redirect is in force
    assert w["testable"], "the synthetic world must make at least one family testable"
    return w


def _args(w, out):
    return ["--threshold", str(THRESHOLD), "--testable", ",".join(w["testable"]), "--seed", "7", "--numpy", np.__version__,
            "--python", platform.python_version(), "--occurrences", str(w["occ"]), "--birth-data", str(w["birth"]), "--out", str(out)]


def test_step8_end_to_end_reaches_one_claim_and_writes_the_result(world, tmp_path):
    out = tmp_path / "step8-out"
    rc = S8.main(_args(world, out))
    log = json.loads((out / "STEP8_RUN_LOG.json").read_text())
    assert rc == 0, log
    assert log["stage"] == "complete"
    empty = hashlib.sha256(json.dumps([]).encode()).hexdigest()
    assert log["ledger_before"] == {"names_count": 0, "names_are_one_claim": False, "sha256": empty}
    names = sorted(os.listdir(C.LEDGER_DIR))
    assert len(names) == 1 and names[0].endswith(".run")
    assert log["ledger_after"] == {"names_count": 1, "names_are_one_claim": True, "sha256": hashlib.sha256(json.dumps(names).encode()).hexdigest()}
    res = json.loads((out / "STEP8_RESULT.json").read_text())
    assert log["result_sha256"] == sha(out / "STEP8_RESULT.json")
    # the result header
    assert res["scorer_source_sha256"] == C.source_sha256() and res["canonical_ledger"] is True and res["test_mode"] is False
    assert res["occurrence_sha256"] == sha(world["occ"]) and res["birth_data_sha256"] == sha(world["birth"])
    assert res["admitted_charts_offset_normalised"] == 0 and res["config"]["fallback_primary_set"] is True
    assert res["ledger_listing_before"]["names"] == [] and res["ledger_listing_after"] == {"names": names, "sha256": log["ledger_after"]["sha256"], "claims": 1}
    assert res["outcome"] in ("STRONG", "MIDDLE", "CHANCE-LEVEL")
    for f in world["testable"]:
        assert res["families"][f]["nonschedulable_episodes_scored"] > 0  # the separate list reached the statistic
    logged = {e["file"].split(" (")[0].split("/")[-1]: e["sha256"] for e in world["ledger_lines"] if str(e.get("id", "")).startswith("YARDSTICK-V1_")}
    assert len(logged) == len(C.YARDSTICK_SHA256) + 1 and "YARDSTICK_v1_6_LOCKED.md" in logged
    assert res["yardstick_sha256"] == logged and log["yardstick_sha256"] == logged  # every logged locked version, v1.6 included
    assert set(res["input_sha256"]) >= {f"yardstick {n}" for n in logged} | {"unit_manifest", "cluster_table"}
    prov_p = out / "STEP8_YARDSTICK_PROVENANCE.json"  # SUR-RB-58: provenance record next to the result, hashed and logged
    prov = json.loads(prov_p.read_text())
    assert prov["yardstick_sha256"] == logged and prov["result_sha256"] == log["result_sha256"]
    assert log["yardstick_provenance_sha256"] == sha(prov_p) and oct(prov_p.stat().st_mode & 0o777) == "0o600"
    # a second invocation on the same sample is refused before anything is claimed again
    rc2 = S8.main(_args(world, tmp_path / "again"))
    log2 = json.loads((tmp_path / "again" / "STEP8_RUN_LOG.json").read_text())
    assert rc2 != 0 and log2["stage"] == "stopped_before_claim" and sorted(os.listdir(C.LEDGER_DIR)) == names


def test_step8_refuses_a_non_empty_ledger_before_the_call(world, tmp_path):
    Path(C.LEDGER_DIR).mkdir(parents=True)
    (Path(C.LEDGER_DIR) / ".DS_Store").write_text("")
    rc = S8.main(_args(world, tmp_path / "o"))
    log = json.loads((tmp_path / "o" / "STEP8_RUN_LOG.json").read_text())
    assert rc == 1 and log["stage"] == "stopped_before_claim" and "not empty" in log["stop"]
    assert sorted(os.listdir(C.LEDGER_DIR)) == [".DS_Store"]


def test_step8_files_are_files_only_and_include_every_yardstick(world, tmp_path, monkeypatch):
    seen = {}
    real = R.score_sample

    def spy(contexts, episodes, cfg, lock, **kw):
        seen["files"] = dict(lock.files)
        return real(contexts, episodes, cfg, lock, **kw)

    monkeypatch.setattr(R, "score_sample", spy)
    assert S8.main(_args(world, tmp_path / "o")) == 0
    assert all(Path(p).is_file() for p in seen["files"].values())
    assert {Path(p).name for p in seen["files"].values()} >= set(C.YARDSTICK_SHA256)


def test_step8_a_stray_file_after_the_run_voids_the_sample_and_discards_the_result(world, tmp_path, monkeypatch):
    real = R.score_sample

    def then_stray(*a, **k):
        res = real(*a, **k)
        (Path(C.LEDGER_DIR) / ".DS_Store").write_text("")  # e.g. a Finder preview between the run and the listing
        return res

    monkeypatch.setattr(R, "score_sample", then_stray)
    out = tmp_path / "o"
    rc = S8.main(_args(world, out))
    log = json.loads((out / "STEP8_RUN_LOG.json").read_text())
    assert rc == 4 and log["stage"] == "VOID" and log["ledger_after"]["names_count"] == 2
    assert not (out / "STEP8_RESULT.json").exists()


def _rewrite_ledger(world, lines):
    world["ledger"].write_text("\n".join(json.dumps(r) for r in lines) + "\n")


@pytest.mark.parametrize("break_it", ["v16_file_missing", "v16_hash_differs", "gap_v1_3", "no_entries", "entry_without_file"])
def test_step8_stops_unless_every_logged_locked_yardstick_is_present(world, tmp_path, break_it):
    lines = [dict(r) for r in world["ledger_lines"]]
    if break_it == "v16_file_missing":
        (tmp_path / "YARDSTICK_v1_6_LOCKED.md").unlink()
    elif break_it == "v16_hash_differs":
        (tmp_path / "YARDSTICK_v1_6_LOCKED.md").write_text("edited after the lock")
    elif break_it == "gap_v1_3":
        lines = [r for r in lines if r.get("id") != "YARDSTICK-V1_3-LOCKED"]
    elif break_it == "no_entries":
        lines = [r for r in lines if not str(r.get("id", "")).startswith("YARDSTICK-V1_")]
    elif break_it == "entry_without_file":
        lines = [dict(r, file="") if r.get("id") == "YARDSTICK-V1_6-LOCKED" else r for r in lines]
    _rewrite_ledger(world, lines)
    rc = S8.main(_args(world, tmp_path / "o"))
    log = json.loads((tmp_path / "o" / "STEP8_RUN_LOG.json").read_text())
    assert rc == 1 and log["stage"] == "stopped_before_claim" and "yardstick" in log["stop"]
    assert not Path(C.LEDGER_DIR).exists() or os.listdir(C.LEDGER_DIR) == []
