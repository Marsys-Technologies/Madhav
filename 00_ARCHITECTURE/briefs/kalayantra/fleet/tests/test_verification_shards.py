"""SR-OD1 R8 (RECONCILIATION R-8; ruling SR-R8-SHARDED): the PINNED class shards of the Gochara verification job and the launcher that runs one shard per execution.

Why: one whole-generation verification of the 26 classes (PLAN.md 2.5: 1.8-3.8 ks/class + a <= 0.6 ks solver check) is 46.8-98.8 ks against the job's 28,800 s task timeout
(`gochara_seal_execution_check.JOB_TIMEOUT_SECONDS`); so the launch is split, and `fleet/VERIFY_SHARDS.json` is the ONE partition the rehearsal and the dispatch both read.

Distinct claims, each with one oracle and its single planted reversion (applied to a copy under the job folder; see result.json):
S1 the pinned partition is an exact cover of the 26 scored classes (hand-declared below, from ka_gochara_v5.SCORED_CLASSES), disjoint, with every shard inside the design bound
   4.4 ks/class x size <= 0.75 x 28,800 s                                                                                               — revert: drop one class from a shard
S2 a partition that is not exact (a class twice, a class missing from the declared total, a malformed id) is refused by the loader                — revert: skip the duplicate check
S3 a launch of shard V02 passes `--class <c>` once per class of THAT shard, taken from the pinned file, and records the file's sha256        — revert: launch without the --class arguments (the whole generation)
S4 the request and the command line must name the same shard; an unknown shard and a request-supplied class list refuse before any cloud call — revert: do not compare the two
S5 the executed resource of a shard launch is judged with the shard's exact arguments (a whole-generation execution is NONCONFORMING)           — revert: judge with the whole-generation arguments
S6 G-5 per shard is measured: a dry-run wall <= 0.75 x timeout is within budget, over it is not, an unread wall is null                          — revert: compare against the full timeout
S7 G-5 projection: the 26-class total <= shards x timeout AND no shard projects over its own budget; nothing measured is null, never green      — revert: drop the per-shard clause
S9 B4 (SR-A10-1): the SERIAL whole-generation execution is the primary path iff its measured effective wall <= 0.75 x timeout, else the shards are the fallback; a whole-generation
   dry run is measured over all 26 classes                                                                                              — revert: compare against the full timeout
S10 the two-shard overlap measurement: overlap, union wall and speedup from the executions' own times; shards that did not overlap conclude nothing — revert: report the longer wall as the union
S11 every real launch appends one line to the append-only execution history (operation, execution, shard, commit, image); a dry run writes none  — revert: do not append
S8 the executor table lets exactly `generation` and `shard` through for both kinds, and no class list                                          — revert: allow `classes`
Doctrine: owner ruling D-OWNER-TESTS-20261016 (planted reversion per claim), root CLAUDE.md §N.8 (a measured wall is the detector; an unread one is null) and §N.7.6.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_executor_verification_launch as base  # noqa: E402  the shared stateful gcloud stand-in and request builders

vl = base.vl
shards = vl.shards
FLEET = base.FLEET

# Hand-declared (NOT read from the file under test): ka_gochara_v5.SCORED_CLASSES at the pinned head, sorted — the 26 scored classes (birth_anchor is not scored).
SCORED = ["achievement_recognition", "bereavement", "business_launch", "career_advancement", "career_change", "career_entry", "career_setback", "childbirth", "chronic_onset",
          "education_milestone", "exam_outcome", "financial_deception", "foreign_settlement", "illness_acute", "major_gain", "major_loss", "marriage", "parental_event",
          "property_acquisition", "psychological_arc", "relocation", "romantic_start", "separation", "spiritual_turn", "surgery", "travel_event"]
V02 = ["career_change", "career_entry", "career_setback", "childbirth"]
TIMEOUT, FRACTION, PER_CLASS_UPPER_S = 28800, 0.75, 4400          # PLAN.md 2.5: <= 3.8 ks verification + <= 0.6 ks solver check per class


def shard_request(kind="verification_job", shard="V02"):
    return base.request(kind, args={"generation": "5.0", "shard": shard})


def go_shard(tmp_path, cloud=None, shard="V02", dry=False, req=None, argv_shard="V02"):
    argv = ("--generation", "5.0") + (("--shard", argv_shard) if argv_shard else ())
    return base.go(tmp_path, cloud, req if req is not None else shard_request("verification_job_dryrun" if dry else "verification_job", shard), argv=argv, dry=dry)


def test_s1_the_pinned_partition_is_an_exact_cover_of_the_26_scored_classes_inside_the_design_bound():
    doc, _ = shards.load()
    flat = [c for s in doc["shards"] for c in s["classes"]]
    assert sorted(flat) == SCORED and len(flat) == len(set(flat)) == 26
    assert [s["id"] for s in doc["shards"]] == [f"V{i:02d}" for i in range(1, len(doc["shards"]) + 1)]
    assert (doc["generation"], doc["classes_total"], doc["task_timeout_s"], doc["wall_fraction"]) == ("5.0", 26, TIMEOUT, FRACTION)
    assert all(len(s["classes"]) * PER_CLASS_UPPER_S <= FRACTION * TIMEOUT for s in doc["shards"]), [len(s["classes"]) for s in doc["shards"]]
    assert next(s for s in doc["shards"] if s["id"] == "V02")["classes"] == V02


@pytest.mark.parametrize("mutate,needle", [
    (lambda d: d["shards"][1]["classes"].append(d["shards"][0]["classes"][0]), "is in shards"),
    (lambda d: d["shards"][1]["classes"].pop(), "the shards hold 25 classes"),
    (lambda d: d["shards"][0].update(id="S1"), "is not V<two digits>"),
    (lambda d: d["shards"][1].update(id="V01"), "repeated"),
    (lambda d: d.update(schema="ky.verification_shards/2"), "schema"),
])
def test_s2_a_partition_that_is_not_exact_is_refused_by_the_loader(tmp_path, mutate, needle):
    doc = json.loads((FLEET / "VERIFY_SHARDS.json").read_text())
    mutate(doc)
    path = tmp_path / "VERIFY_SHARDS.json"
    path.write_text(json.dumps(doc))
    with pytest.raises(shards.Refused, match=needle):
        shards.load(path)


def test_s3_a_shard_launch_passes_one_class_flag_per_class_of_that_shard_and_records_the_pinned_files_digest(tmp_path):
    cloud, record, _ = go_shard(tmp_path)
    expected = ["--chart", base.CHART, "--generation", "5.0", "--final-rules"] + [f"--class={c}" for c in V02]
    assert cloud.writes() == [["gcloud", "run", "jobs", "execute", "gochara-verification-job", "--project=madhav-astrology", "--region=asia-south1",
                               "--args=" + ",".join(expected), "--async", "--format=value(metadata.name)"]]
    import hashlib
    assert record["args"] == expected
    assert record["shard"] == {"id": "V02", "classes": V02, "shards_sha256": hashlib.sha256((FLEET / "VERIFY_SHARDS.json").read_bytes()).hexdigest()}
    assert record["executed_check"]["status"] == "NONCONFORMING"        # the fake still answers the whole-generation execution: S5's detector, here only noted


def test_s3_the_shardless_launch_is_the_whole_generation_exactly_as_before(tmp_path):
    cloud, record, _ = base.go(tmp_path)
    assert record["args"] == list(vl.EXECUTE_ARGS) and record["shard"] is None and cloud.writes()[0][7] == "--args=" + ",".join(vl.EXECUTE_ARGS)


@pytest.mark.parametrize("req_shard,argv_shard,needle", [
    ("V02", "V03", "same shard"), ("V02", None, "same shard"), (None, "V02", "same shard"),
    ("V99", "V99", "unknown verification shard"),
])
def test_s4_the_request_and_the_command_line_must_name_the_same_known_shard_before_any_cloud_call(tmp_path, req_shard, argv_shard, needle):
    cloud = base.Cloud()
    req = base.request(args={"generation": "5.0", **({"shard": req_shard} if req_shard else {})})
    with pytest.raises(vl.Refused, match=needle):
        go_shard(tmp_path, cloud, req=req, argv_shard=argv_shard)
    assert cloud.calls == [] and not (tmp_path / "claims").exists()


def test_s4_a_request_cannot_supply_its_own_class_list(tmp_path):
    cloud = base.Cloud()
    req = base.request(args={"generation": "5.0", "shard": "V02", "classes": "marriage"})
    with pytest.raises(vl.Refused, match="only verified generation"):
        go_shard(tmp_path, cloud, req=req)
    assert cloud.calls == []


def test_s5_the_executed_resource_of_a_shard_launch_is_judged_with_the_shards_exact_arguments(tmp_path):
    shard_args = list(vl.build_job_args(V02))
    cloud = base.Cloud()
    cloud.execution = base.execution_v1(args=shard_args)
    record = go_shard(tmp_path / "ok", cloud)[1]
    assert record["executed_check"]["status"] == "CONFORMS", record["executed_check"]
    whole = base.Cloud()                                                # the job executed WITHOUT the --class arguments: the shard's work would be the whole generation
    assert go_shard(tmp_path / "bad", whole)[1]["executed_check"]["status"] == "NONCONFORMING"


def _dry_cloud(wall_s):
    from datetime import datetime, timedelta, timezone
    cloud = base.Cloud()
    cloud.dry_execution = base.execution_v1(args=vl.build_job_args(V02, report_only=True))
    start = datetime(2026, 10, 19, 10, 0, 0, tzinfo=timezone.utc)
    cloud.dry_execution["status"] = {"startTime": start.isoformat().replace("+00:00", "Z"), "completionTime": (start + timedelta(seconds=wall_s)).isoformat().replace("+00:00", "Z"),
                                    "succeededCount": 1, "conditions": [{"type": "Completed", "status": "True"}]}
    return cloud


@pytest.mark.parametrize("wall,within", [(2500.5, True), (21600.0, True), (21600.5, False)])
def test_s6_the_dry_run_measures_the_shard_wall_against_three_quarters_of_the_task_timeout(tmp_path, wall, within):
    cloud, record, _ = go_shard(tmp_path, _dry_cloud(wall), dry=True)
    ran = record["report_only_run"]
    assert ran["args"] == list(vl.build_job_args(V02, report_only=True)) and ran["executed_check"]["status"] == "CONFORMS", ran["executed_check"]
    assert ran["capacity"] == {"wall_s": wall, "classes": 4, "budget_s": 21600.0, "per_class_s": round(wall / 4, 3), "within_budget": within}
    assert record["shard"]["classes"] == V02


def test_s6_an_unread_wall_is_null_never_within_budget():
    doc, _ = shards.load()
    cap = shards.shard_capacity(None, 4, doc)
    assert cap["within_budget"] is None and cap["wall_s"] is None and cap["per_class_s"] is None


def test_s7_the_projection_needs_both_the_26_class_total_and_every_shard_inside_its_budget():
    doc, _ = shards.load()
    cap = lambda wall, n: shards.shard_capacity(wall, n, doc)  # noqa: E731
    ok = shards.projection([cap(12000, 4)], doc)                       # 3 ks/class: 78 ks total, 12 ks per 4-class shard
    assert ok["ok"] is True and ok["projected_total_s"] == 78000.0 and ok["ceiling_s"] == len(doc["shards"]) * TIMEOUT and ok["problems"] == []
    slow_shard = shards.projection([cap(30000, 4)], doc)                # 7.5 ks/class: total 195 ks <= 7 x 28.8 ks = 201.6 ks, but a 4-class shard projects to 30 ks > 21.6 ks
    assert slow_shard["projected_total_s"] <= slow_shard["ceiling_s"] and slow_shard["ok"] is False and any("over its budget" in p for p in slow_shard["problems"])
    projected = shards.projection([cap(18000, 3)], doc)                 # the measured 3-class shard is inside its budget (6 ks/class), but a 4-class shard projects to 24 ks > 21.6 ks
    assert projected["ok"] is False and projected["projected_total_s"] <= projected["ceiling_s"]
    assert not any("took" in p for p in projected["problems"]) and any("projects to" in p for p in projected["problems"])
    over_total = shards.projection([cap(25000, 3)], doc)               # 8.33 ks/class: 216.7 ks > 201.6 ks
    assert over_total["ok"] is False and any("exceeds shards x timeout" in p for p in over_total["problems"])
    assert shards.projection([cap(None, 4)], doc)["ok"] is None        # nothing measured: null


@pytest.mark.parametrize("kind", ["verification_job", "verification_job_dryrun"])
def test_s8_the_executor_table_passes_exactly_generation_and_shard(kind):
    ops = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
    assert ops[kind]["allowed_args"] == ["generation", "shard"]


def test_s9_the_serial_path_is_primary_only_when_its_measured_wall_fits_three_quarters_of_the_timeout(tmp_path):
    doc, _ = shards.load()
    whole = lambda wall: {"shard": None, "report_only_run": {"execution_wall_s": wall}}  # noqa: E731
    assert shards.serial_decision(whole(21600.0), doc)["path"] == "serial"
    assert shards.serial_decision(whole(25000.0), doc)["path"] == "sharded"        # inside the 28,800 s timeout, outside 0.75 of it
    assert shards.serial_decision(whole(None), doc)["path"] is None                # an unread wall is not 'serial'
    assert shards.serial_decision({"shard": {"id": "V02"}, "report_only_run": {"execution_wall_s": 100.0}}, doc)["path"] is None
    cloud, record, _ = base.go(tmp_path, dry=True)                                   # a whole-generation dry run is measured over the pinned 26 classes
    assert record["shard"] is None and record["report_only_run"]["capacity"]["classes"] == 26 and record["report_only_run"]["capacity"]["wall_s"] == 2500.5
    assert shards.serial_decision(record, doc)["path"] == "serial"


def test_s10_the_two_shard_overlap_is_measured_from_the_executions_own_times():
    rec = lambda a, b: {"report_only_run": {"start_time": a, "completion_time": b}}  # noqa: E731
    both = shards.overlap(rec("2026-10-22T10:00:00Z", "2026-10-22T12:00:00Z"), rec("2026-10-22T10:30:00Z", "2026-10-22T12:30:00Z"))
    assert both == {"overlapped": True, "overlap_s": 5400.0, "union_wall_s": 9000.0, "sum_wall_s": 14400.0, "speedup": 1.6}
    serial = shards.overlap(rec("2026-10-22T10:00:00Z", "2026-10-22T12:00:00Z"), rec("2026-10-22T12:00:00Z", "2026-10-22T14:00:00Z"))
    assert serial["overlapped"] is False and serial["speedup"] is None and serial["union_wall_s"] is None
    assert shards.overlap(rec("2026-10-22T10:00:00Z", None), rec("2026-10-22T10:00:00Z", "2026-10-22T11:00:00Z"))["overlapped"] is None


def test_s11_a_real_launch_appends_to_the_execution_history_and_a_dry_run_writes_none(tmp_path):
    cloud, record, claims = go_shard(tmp_path / "a")
    cloud2, record2, claims2 = go_shard(tmp_path / "b", shard="V03", req=base.request(operation_id="op-verify-2", args={"generation": "5.0", "shard": "V03"}), argv_shard="V03")
    lines = [json.loads(x) for x in (claims / "HISTORY.jsonl").read_text().splitlines()]
    assert len(lines) == 1 and lines[0]["execution_name"] == base.NAME and lines[0]["shard"]["id"] == "V02" and lines[0]["reviewed_commit"] == base.COMMIT
    assert lines[0]["image_digest"] == base.DIGEST and lines[0]["request_sha256"] == record["request_sha256"] and lines[0]["args"] == record["args"]
    again = base.Cloud()                                                           # a second launch into the SAME ledger appends; it never rewrites the first
    go_shard(tmp_path / "a", again, req=base.request(operation_id="op-verify-3", args={"generation": "5.0", "shard": "V02"}))
    assert len((claims / "HISTORY.jsonl").read_text().splitlines()) == 2 and (claims2 / "HISTORY.jsonl").exists()
    dry_claims = go_shard(tmp_path / "c", _dry_cloud(100.0), dry=True)[2]
    assert not dry_claims.exists()
