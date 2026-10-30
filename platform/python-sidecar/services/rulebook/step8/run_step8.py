"""Step-8 invocation (v1.1 Part G step 8; reviewer VERIFY3 G4; SUR-RB-53 (3) and (4)). PREPARED, NOT RUN.

Builds the RunLock and the per-family episodes from the hash-fixed inputs and calls the pinned runner's production entry
point ONCE. It reads the slim occurrence file (only the OCCURRENCE_COLUMNS_SLIM_v1 columns) and nothing else from the
sample store. Outputs: the result file and a run log of counts and hashes only (0600, in a 0700 directory).

Order (any failed assertion before the claim stops with nothing claimed):
  1. the scorer source sha256 is the frozen one; every input file hash equals its logged value;
  2. the step-6 decisions (A6 threshold, exclusion 5, D7, the P1/P3 donor rules) are read from the sealed count_blind
     V3 outputs at the decided threshold for the PRIMARY set ("all", A7 fallback, SUR-RB-51) and must equal the values
     given on the command line (the surrogate's decisions);
  3. episodes: count_blind's rules per family (horizon trim, merge within chart/area/direction/grade, day +- 1 or the
     calendar month); the runner re-applies its own edge rules and refuses unless its recount equals count_blind's;
  4. SUR-RB-46 (c) / SUR-RB-53 (4): IMMEDIATELY before the call, 10_engine/run-ledger/ must list EMPTY; the listing
     and its sha256 are logged. Nobody opens, lists or previews that folder until step 6 below.
  5. R.score_sample(...) (the runner asserts emptiness again, claims, scores, asserts exactly one claim);
  6. after the run the listing must be exactly ONE '<key>.run' file; its sha256 is logged. Anything else (a stray
     .DS_Store, a second file, a runner error after the claim) = the sample is VOID: logged as such, result discarded.

Rulings applied (SUR-RB-54 R1/R2, SUR-RB-55):
  * R1: two episode lists per family, each built EXACTLY as count_blind builds its set: 'all' = every occurrence,
    trimmed to the family horizon and merged; 'primary_nonschedulable' = schedulable occurrences DROPPED FIRST, then
    the rest trimmed and merged on their own. The second list is NOT a label on the first; it travels in the lock and
    is used only for the fallback's direction-consistency statistic; its per-chart aggregates must equal count_blind's
    primary_nonschedulable rows before the claim.
  * R2: each family's charts = count_blind's exclusion-5 pool at the decided threshold (primary set 'all'), asserted
    inside s6_admit's admitted set and free of that family's horizon exclusions (under 12 years); any difference stops
    the run before the claim.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
from datetime import date, timedelta
from pathlib import Path

LIB = Path("/Users/Dev/Archives/madhav-research-library")
ADM = LIB / "10_engine/admission-v1_1"
CB = ADM / "out/count_blind"
UNIT_MANIFEST = LIB / "10_engine/unit-manifest/rev4-candidate-20261030/UNIT_MANIFEST_v1_0.json"
CLUSTER_TABLE = LIB / "02_plans/rule-book-programme/cluster-classification/FINAL_CLUSTER_TABLE_v1_1.json"
SAMPLE = Path("/Users/Dev/Archives/madhav-chart-sample")

FROZEN_SCORER_SHA256 = "836aabcd2b1a23b7f537cdb69c0f831e722557d2fc2baa6a494494e0f91823b4"  # SUR-RB-55 candidate (0c37855bc); the freeze confirms it
LOGGED = {
    "TIMELINES_MANIFEST.json": "d3d3948f56890336ac21388326eb3028e1038f8a58bf9221ca9c90b305f4dce0",
    "UNIT_MANIFEST_v1_0.json (rev4)": "7e8d69f29d11677b6ce430a2f3a6d21c2fcb45211117f28493c00dc659f71b79",
    "FINAL_CLUSTER_TABLE_v1_1.json": "b3e0a6b9f31e41dbd974f667c3507af6d2681b180ba78b694d6aeccddf79499f",
    "s7_footprint.json": "8d9d29935557ceac282fc88d025698fa10dd0fb7918d1bcb77849bce4a4c53ed",
}
COUNT_BLIND_RUN_ENTRY = "COUNT-BLIND-V3-RUN-20261030"
PRIMARY_SET = "all"  # SUR-RB-51: the A7 fallback applies; the all-occurrence set is PRIMARY
FALLBACK_PRIMARY_SET = True
NONSCHEDULABLE_SET = "primary_nonschedulable"
SLIM_COLUMNS = ("chart_id", "year", "month", "day", "date_grade", "schedulable", "area", "direction", "in_horizon_dasha", "in_horizon_transit")
FORBIDDEN_COLUMNS = ("title", "event", "evidence")
MERGE_DAYS = 31


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Stop(SystemExit):
    pass


def listing(d: Path) -> dict:
    names = sorted(os.listdir(d)) if d.exists() else []
    return {"names_count": len(names), "names_are_one_claim": len(names) == 1 and names[0].endswith(".run"),
            "sha256": hashlib.sha256(json.dumps(names).encode()).hexdigest(), "_names": names}


# ── occurrences -> per-family episodes (count_blind's rules) ───────────────────────────────────────────────────
def read_slim(path: Path):
    """Only the slim columns; errors name a row index and a field, never content."""
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        hdr = [h.strip().lower() for h in (rd.fieldnames or [])]
        if any(c in hdr for c in FORBIDDEN_COLUMNS):
            raise Stop("refused: the occurrence file carries a forbidden column; use the slim file")
        if [c for c in SLIM_COLUMNS if c not in (rd.fieldnames or [])]:
            raise Stop("refused: the occurrence file lacks a slim column")
        for i, r in enumerate(rd, start=1):
            try:
                grade = r["date_grade"].strip().lower()
                y, m, dd = int(r["year"]), int(r["month"]), r["day"].strip()
                if grade == "day":
                    d = date(y, m, int(dd))
                elif grade == "month":
                    if dd:
                        raise ValueError
                    d = date(y, m, 1)
                else:
                    d = None
                sv = r["schedulable"].strip()
                dr = r["direction"].strip().lower()
                ar = r["area"].strip()
                cid = r["chart_id"].strip()
                if sv not in ("True", "False") or dr not in ("favourable", "unfavourable", "mixed") or not ar or not cid:
                    raise ValueError
            except (ValueError, KeyError, TypeError):
                raise Stop(f"occurrence row {i} is malformed") from None
            rows.append((cid, grade, d, ar, dr, sv == "True"))
    return rows


def month_bounds(d: date):
    first = date(d.year, d.month, 1)
    nxt = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    return first, nxt - timedelta(days=1)


def family_episodes(rows, codes, horizons, family, C, Episode, set_name=PRIMARY_SET):
    """count_blind's count_chart, per set (R1): for 'primary_nonschedulable' schedulable occurrences are dropped FIRST;
    then the family horizon trim (a day inside; a month wholly inside) and the merge within chart, area, direction,
    grade (day: a new episode when more than 31 days after the current start; month: same calendar month). G3/R rows
    are counted and skipped; mixed episodes are passed on (the runner drops and counts them)."""
    if set_name not in (PRIMARY_SET, NONSCHEDULABLE_SET):
        raise Stop(f"unknown occurrence set {set_name!r}")
    idx = {c: i for i, c in enumerate(codes)}
    groups, g3 = {}, 0
    for cid, grade, d, area, direction, sched in rows:
        if cid not in idx:
            continue
        if set_name == NONSCHEDULABLE_SET and sched:  # drop before the trim and the merge (count_blind)
            continue
        if grade not in ("day", "month"):
            g3 += 1
            continue
        h0, h1 = horizons[cid]
        inside = (h0 <= d <= h1) if grade == "day" else (h0 <= month_bounds(d)[0] and month_bounds(d)[1] <= h1)
        if not inside:
            continue
        groups.setdefault((cid, area, direction, grade), []).append(d)
    out = []
    for (cid, area, direction, grade), ds in sorted(groups.items()):
        starts = []
        for d in sorted(ds):
            if not starts or (grade == "day" and (d - starts[-1]).days > MERGE_DAYS) or (grade == "month" and (d.year, d.month) != (starts[-1].year, starts[-1].month)):
                starts.append(d)
        for d in starts:
            if grade == "day":
                lo, hi, g = (d - timedelta(days=1)).toordinal(), (d + timedelta(days=1)).toordinal(), C.G1
            else:
                a, b = month_bounds(d)
                lo, hi, g = a.toordinal(), b.toordinal(), C.G2
            out.append(Episode(idx[cid], area, direction, g, lo, hi, False))  # the scorer reads no schedulable label
    return out, g3


def check_pool(family, pool, admitted, family_ids):
    """R2: the count_blind exclusion-5 pool of the family must lie inside s6_admit's admitted set and contain no chart
    the family's horizon exclusions removed; any difference stops before the claim."""
    out_s6 = sorted(set(pool) - set(admitted))
    if out_s6:
        raise Stop(f"{family}: {len(out_s6)} chart(s) of the count_blind pool are not in s6_admit's admitted set")
    excl = sorted(set(pool) - set(family_ids))
    if excl:
        raise Stop(f"{family}: {len(excl)} chart(s) of the count_blind pool fall under the family's horizon exclusions")
    return sorted(pool)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=int, required=True, choices=(3, 5, 8), help="the A6 threshold the surrogate decided")
    ap.add_argument("--testable", required=True, help="D7 testable families as decided, e.g. dasha,transit")
    ap.add_argument("--escalated", default="", help='v1.5 P3 95%% checks as decided at the gate, e.g. "dasha:b,c"')
    ap.add_argument("--seed", type=int, required=True, help="the seed logged at the lock")
    ap.add_argument("--numpy", required=True, help="the numpy version pinned at the freeze")
    ap.add_argument("--python", required=True, help="the Python version pinned at the freeze")
    ap.add_argument("--occurrences", default=str(SAMPLE / "astro-databank/extracted-wave2/sample_events_v5_slim.csv"))
    ap.add_argument("--birth-data", required=True, help="BIRTH_DATA_v5.csv (only hashed here; the runner re-hashes it)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rehearsal-ledger", default=None, help="step 7 only: a separate ledger; the test entry point is used")
    a = ap.parse_args(argv)

    from services.rulebook.scorer import config as C
    from services.rulebook.scorer import runner as R
    from services.rulebook.scorer.core import FamilyContext
    from services.rulebook.scorer.footprint import sealed_gate_from_s7
    from services.rulebook.scorer.inputs import AdmissionInputs, d7_decisions, donor_rows, ledger_entries, read_count_blind, single_entry
    from services.rulebook.scorer.model import Episode, units_from_manifest
    from services.rulebook.scorer_calib.cli import family_chart_ids

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    log = {"script_sha256": sha(__file__), "stage": "start"}

    def save(name, obj):
        p = out / name
        fd = os.open(str(p), os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(obj, sort_keys=True, indent=1, default=str) + "\n")

    try:
        # 1. hashes
        if C.source_sha256() != FROZEN_SCORER_SHA256:
            raise Stop("the scorer source is not the frozen one")
        got = {"TIMELINES_MANIFEST.json": sha(ADM / "out/TIMELINES_MANIFEST.json"), "UNIT_MANIFEST_v1_0.json (rev4)": sha(UNIT_MANIFEST),
               "FINAL_CLUSTER_TABLE_v1_1.json": sha(CLUSTER_TABLE), "s7_footprint.json": sha(ADM / "out/s7_footprint.json")}
        if got != LOGGED:
            raise Stop("an input hash differs from its logged value: " + ", ".join(k for k in LOGGED if got[k] != LOGGED[k]))
        run_entry = single_entry(ledger_entries(C.LOCK_LEDGER_PATH), COUNT_BLIND_RUN_ENTRY)
        if not run_entry or not run_entry.get("outputs_sha256"):
            raise Stop(f"{COUNT_BLIND_RUN_ENTRY} not in the decisions ledger")
        for name, h in (run_entry or {}).get("outputs_sha256", {}).items():
            if name.endswith(".csv") or name == "COUNT_BLIND_RUN.json":
                if sha(CB / name) != h:
                    raise Stop(f"count_blind output {name} differs from {COUNT_BLIND_RUN_ENTRY}")
        record = R.read_lock_record()  # the claim-key hashes logged at lock step 4 (SUR-RB-43/45)
        if sha(a.occurrences) != record["occurrence"] or sha(a.birth_data) != record["birth_data"]:
            raise Stop("the occurrence or birth-data file is not the one logged at lock step 4")
        log["inputs_sha256"] = {**got, "occurrences": record["occurrence"], "birth_data": record["birth_data"], "count_blind": run_entry["outputs_sha256"]}

        # 2. step-6 decisions from the sealed count_blind outputs, compared with the surrogate's
        cb = read_count_blind(str(CB))
        adm = AdmissionInputs(str(ADM))
        s7 = json.loads((ADM / "out/s7_footprint.json").read_text())
        man, tab = json.loads(UNIT_MANIFEST.read_text()), json.loads(CLUSTER_TABLE.read_text())
        esc = {}
        for spec in filter(None, a.escalated.split(";")):
            fam, chks = spec.split(":")
            esc[fam] = [c for c in chks.split(",") if c]
        testable_given = sorted(f for f in a.testable.split(",") if f)
        contexts, episodes, d7, admitted, rows_by_fam, donors, drops_g3 = {}, {}, {}, {}, {}, {}, {}
        ns_episodes, ns_rows = {}, {}
        fam_ids = family_chart_ids(adm)
        rows = read_slim(Path(a.occurrences))
        for fam in C.FAMILIES:
            dec = d7_decisions(cb, a.threshold, fam, PRIMARY_SET, escalated=esc.get(fam, ()))
            pool = check_pool(fam, dec["admitted"], adm.admitted(), fam_ids[fam])  # R2
            tls = adm.timelines(fam, pool)
            units = units_from_manifest(man, tab, fam)
            contexts[fam] = FamilyContext(fam, tls, [u for u in units if u.plane == fam], sealed_gate_from_s7(s7, fam))
            hz = {t.code: (date.fromordinal(t.h_start), date.fromordinal(t.h_end)) for t in tls}
            episodes[fam], drops_g3[fam] = family_episodes(rows, pool, hz, fam, C, Episode, PRIMARY_SET)
            ns_episodes[fam], _g3 = family_episodes(rows, pool, hz, fam, C, Episode, NONSCHEDULABLE_SET)  # R1: formed on its own
            ns_rows[fam] = [r for r in cb.aggregates if r["family"] == fam and r["set"] == NONSCHEDULABLE_SET and r["chart_id"] in set(pool)]
            admitted[fam] = pool
            d7[fam] = {"testable": fam in testable_given, "dir_testable": dec["dir_testable"], "z25_units": dec["z25_units"],
                       "donor_charts_b": dec["donor_charts_b"], "donor_charts_c": dec["donor_charts_c"],
                       "donor_rule_b": dec["donor_rule_b"], "donor_rule_c": dec["donor_rule_c"]}
            rows_by_fam[fam] = [r for r in cb.aggregates if r["family"] == fam and r["set"] == PRIMARY_SET and r["chart_id"] in set(pool)]
            donors[fam] = donor_rows(cb, a.threshold, fam, PRIMARY_SET)
        log["decisions"] = {f: {"charts": len(admitted[f]), **{k: v for k, v in d7[f].items() if k != "z25_units"}, "z25_units": len(d7[f]["z25_units"])} for f in C.FAMILIES}
        log["episodes_built"] = {f: len(episodes[f]) for f in C.FAMILIES}
        log["nonschedulable_episodes_built"] = {f: len(ns_episodes[f]) for f in C.FAMILIES}
        log["g3_or_range_rows_skipped"] = drops_g3
        lock = R.RunLock(
            occurrence_sha256=record["occurrence"], birth_data_sha256=record["birth_data"], scorer_sha256=FROZEN_SCORER_SHA256,
            seed=a.seed, fallback_primary_set=FALLBACK_PRIMARY_SET, count_set=PRIMARY_SET, admitted=admitted, d7=d7, count_rows=rows_by_fam,
            files={"unit_manifest": str(UNIT_MANIFEST), "cluster_table": str(CLUSTER_TABLE), "admission": str(ADM), "count_blind": str(CB)},
            ledger_dir=C.LEDGER_DIR, occurrence_path=a.occurrences, birth_data_path=a.birth_data, manifest_sha256=LOGGED["UNIT_MANIFEST_v1_0.json (rev4)"],
            numpy_version=a.numpy, python_version=a.python, admission_dir=str(ADM), count_blind_sha256=dict(cb.outputs_sha256), donor_counts=donors,
            nonschedulable_episodes=ns_episodes, nonschedulable_count_rows=ns_rows,
        )
        cfg = C.ScoreConfig(draws=C.DRAWS_PRODUCTION, seed=a.seed, fallback_primary_set=FALLBACK_PRIMARY_SET)
        if platform.python_version() != a.python:
            raise Stop("the Python version is not the pinned one")

        # 4. the canonical ledger must be EMPTY immediately before the call (SUR-RB-46 c, SUR-RB-53 (4))
        led = Path(a.rehearsal_ledger) if a.rehearsal_ledger else Path(C.LEDGER_DIR)
        before = listing(led)
        log["ledger_before"] = {k: v for k, v in before.items() if k != "_names"}
        if before["names_count"]:
            raise Stop("the ledger is not empty before the run: nothing claimed, run not started")
        log["stage"] = "calling_runner"
        save("STEP8_RUN_LOG.json", log)
        # 5. the one call
        try:
            if a.rehearsal_ledger:
                result = R.score_sample_for_tests(contexts, episodes, cfg, lock, str(led))
            else:
                result = R.score_sample(contexts, episodes, cfg, lock)
        except R.RunRefused as exc:
            after = listing(led)
            log["ledger_after"] = {k: v for k, v in after.items() if k != "_names"}
            log["stage"] = "refused_before_claim" if after["names_count"] == 0 else "VOID"
            log["refusal"] = str(exc)[:2000]
            save("STEP8_RUN_LOG.json", log)
            return 2
        except Exception as exc:  # noqa: BLE001 - after the claim any error voids the sample
            after = listing(led)
            log["ledger_after"] = {k: v for k, v in after.items() if k != "_names"}
            log["stage"] = "VOID" if after["names_count"] else "error_before_claim"
            log["error"] = f"{type(exc).__name__}: {str(exc)[:2000]}"
            save("STEP8_RUN_LOG.json", log)
            return 3
        # 6. exactly one claim after the run
        after = listing(led)
        log["ledger_after"] = {k: v for k, v in after.items() if k != "_names"}
        keys = sorted(k + ".run" for k in (result.get("claim_keys") or {}).values())
        if after["_names"] != keys or len(keys) != 1:
            log["stage"] = "VOID"
            log["void_reason"] = "the ledger does not hold exactly this run's one claim"
            save("STEP8_RUN_LOG.json", log)
            return 4
        res_path = out / "STEP8_RESULT.json"
        log["result_sha256"] = R.write_result(result, str(res_path))
        log["outcome"] = result.get("outcome")
        log["stage"] = "complete"
        save("STEP8_RUN_LOG.json", log)
        return 0
    except Stop as exc:
        log["stage"] = "stopped_before_claim"
        log["stop"] = str(exc)
        save("STEP8_RUN_LOG.json", log)
        return 1


if __name__ == "__main__":
    sys.exit(main())
