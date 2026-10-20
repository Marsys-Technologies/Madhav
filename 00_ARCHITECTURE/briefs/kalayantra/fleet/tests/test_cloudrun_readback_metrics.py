"""SR-BOLD-09: the optional `metrics` leg of `cloudrun_job_readback` — CPU / memory utilisation of ONE execution from Cloud Monitoring.

One oracle per distinct production claim. No gcloud, credential or network: the script's `runner` is a double that serves the existing
job / image / execution fixtures plus synthetic Cloud Monitoring TimeSeries. Expected numbers are worked out by hand from the Monitoring
API's own definitions (the oracle never calls the code under test to compute its expectation):
  · TimeSeries / Point / Distribution (mean, bucketOptions, bucketCounts):  https://cloud.google.com/monitoring/api/ref_v3/rest/v3/TimeSeries
    and https://cloud.google.com/monitoring/api/ref_v3/rest/v3/TypedValue#Distribution — bucket i of a linearBuckets layout is
    [offset+(i-1)*width, offset+i*width), bucket 0 is the underflow, the last is the overflow.
  · Cloud Run container/cpu/utilizations and container/memory/utilizations: distributions of the fraction of the container's limit
    (https://cloud.google.com/monitoring/api/metrics_gcp_p_z#gcp-run).

  M1  the metrics leg is two fixed monitoring reads, scoped to the job and the execution's own window; no flag = no call and no key
  M2  present series are summarised: sample-weighted mean, bucket-interpolated p95, highest non-empty bucket's upper bound
  M3  an absent series, a failed query, an unreadable point or an unreadable start time read NULL (never zero), each with its status
  M4  the shape: p95 at ~1 vCPU of several allocated = SINGLE_THREAD_BOUND; a flat all-vCPU load, a partly parallel and an idle build are told apart
  M5  memory: peak is the bucket upper bound and, against the allocated memory, bytes; an open overflow bucket = null
  M6  DB wait is reported as not exposed, not as zero
  M7  percentile across different bucket layouts is NULL (not a pooled guess); mean and max bound are still given
  M8  the CLI carries --metrics end to end and `--metrics` without --execution is refused before any cloud call
  M9  the executor's real `validate` admits {execution, metrics} against the real executor_ops.json table and still refuses any other argument
"""
import importlib.util
import json
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
FIX = HERE / "fixtures" / "cloudrun_readback"
SCRIPT = FLEET / "cloudrun_readback.py"
EXEC = "brahma-build-pipeline-job-abc12"
CPU, MEM = "run.googleapis.com/container/cpu/utilizations", "run.googleapis.com/container/memory/utilizations"

spec = importlib.util.spec_from_file_location("cloudrun_readback_metrics_under_test", SCRIPT)
CR = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CR)

LINEAR = {"linearBuckets": {"numFiniteBuckets": 20, "width": 0.05, "offset": 0}}      # [0,0.05) .. [0.95,1.0); index 0 underflow, 21 overflow


def dist(in_bucket, count, mean, options=LINEAR, total_buckets=22):
    counts = [0] * total_buckets
    counts[in_bucket] = count
    return {"count": str(count), "mean": mean, "bucketOptions": options, "bucketCounts": [str(c) for c in counts]}


def series(metric_type, *distributions):
    return {"metric": {"type": metric_type}, "resource": {"type": "cloud_run_job"},
            "points": [{"interval": {"endTime": "2026-10-17T10:05:00Z"}, "value": {"distributionValue": d}} for d in distributions]}


class Cloud:
    def __init__(self, cpu=(), memory=(), fail=(), job=None, drop_start=False):
        self.calls = []
        self.answers = {CPU: list(cpu), MEM: list(memory)}
        self.fail = set(fail)
        self.job = job
        self.drop_start = drop_start

    def __call__(self, argv):
        self.calls.append(list(argv))
        text = " ".join(argv)
        if "monitoring" in argv:
            metric = next(m for m in (CPU, MEM) if f'metric.type="{m}"' in text)
            if metric in self.fail:
                return SimpleNamespace(returncode=1, stdout="", stderr="secret ya29.LEAK")
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.answers[metric]), stderr="")
        name = "job" if "jobs describe" in text else "image" if "images describe" in text else "execution_succeeded"
        body = self.job if (name == "job" and self.job is not None) else json.loads((FIX / f"{name}.json").read_text())
        if name == "execution_succeeded" and self.drop_start:
            body["status"].pop("startTime")
        return SimpleNamespace(returncode=0, stdout=json.dumps(body), stderr="")


def run(cloud, **kw):
    return CR.measure(EXEC, cloud, **kw)


def job_with(**limits):
    job = json.loads((FIX / "job.json").read_text())
    job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"].update(limits)
    return job


# one thread's worth on 4 vCPUs: 100 samples in [0.20,0.25) -> p95 = 0.20 + 0.05*0.95 = 0.2475 -> 0.99 vCPU of 4
SINGLE_THREAD = (series(CPU, dist(5, 100, 0.24)),)


# ───────────── M1 ─────────────

def test_m1_two_fixed_reads_scoped_to_the_job_and_the_executions_own_window():
    cloud = Cloud(cpu=SINGLE_THREAD, memory=(series(MEM, dist(10, 10, 0.5)),))
    record = run(cloud, metrics=True)
    reads = [c for c in cloud.calls if "monitoring" in c]

    def flt(m):
        return (f'metric.type="{m}" AND resource.type="cloud_run_job" AND resource.labels.job_name="brahma-build-pipeline-job" '
                f'AND resource.labels.location="asia-south1"')
    assert reads == [["gcloud", "monitoring", "time-series", "list", f"--filter={flt(m)}", "--interval-start-time=2026-10-17T10:01:00Z",
                      "--interval-end-time=2026-10-17T10:41:30Z", "--project=madhav-astrology", "--format=json"] for m in (CPU, MEM)]
    assert record["metrics"]["window"] == {"start": "2026-10-17T10:01:00Z", "end": "2026-10-17T10:41:30Z", "end_is_now": False}
    assert record["metrics"]["metric_types"] == {"cpu": CPU, "memory": MEM}


def test_m1_without_the_flag_there_is_no_monitoring_call_and_no_metrics_key():
    cloud = Cloud()
    assert "metrics" not in run(cloud) and not [c for c in cloud.calls if "monitoring" in c]


# ───────────── M2 ─────────────

def test_m2_present_series_are_summarised_by_hand_checked_numbers():
    # 100 samples in [0.05,0.10) mean .07 and 100 in [0.20,0.25) mean .22: mean = .145; target 190 of 200 -> second bucket: .20+.05*(90/100) = .245
    cpu = run(Cloud(cpu=(series(CPU, dist(2, 100, 0.07), dist(5, 100, 0.22)),)), metrics=True)["metrics"]["cpu"]
    assert cpu["status"] == "OK" and cpu["samples"] == 200 and cpu["points"] == 2
    assert cpu["mean"] == pytest.approx(0.145) and cpu["p95"] == pytest.approx(0.245) and cpu["max_upper_bound"] == pytest.approx(0.25)


# ───────────── M3 ─────────────

@pytest.mark.parametrize("answers", [[], [{"metric": {"type": CPU}, "points": []}], [series(CPU, dist(5, 0, 0.0))]])
def test_m3_an_absent_series_reads_null_not_zero(answers):
    cpu = run(Cloud(cpu=answers), metrics=True)["metrics"]["cpu"]
    assert cpu["status"] == "ABSENT" and cpu["mean"] is None and cpu["p95"] is None and cpu["max_upper_bound"] is None and cpu["shape"] is None


def test_m3_a_failed_query_reads_null_with_its_status_and_no_stderr():
    record = run(Cloud(cpu=SINGLE_THREAD, fail={CPU}), metrics=True)
    cpu = record["metrics"]["cpu"]
    assert cpu["status"] == "QUERY_FAILED" and cpu["mean"] is None and cpu["shape"] is None
    assert "ya29" not in json.dumps(record) and record["metrics"]["memory"]["status"] == "ABSENT"


@pytest.mark.parametrize("point", [{"count": "5", "mean": 0.1, "bucketOptions": LINEAR, "bucketCounts": ["5"]},                # wrong bucket count
                                   {**dist(5, 100, 0.24), "count": "99"},                                                      # counts do not sum
                                   dist(5, 100, "x"), dist(5, 100, 0.24, options={"mystery": {}})])
def test_m3_an_unreadable_point_reads_null_for_the_whole_series(point):
    cpu = run(Cloud(cpu=(series(CPU, dist(5, 100, 0.24), point),)), metrics=True)["metrics"]["cpu"]
    assert cpu["status"] == "UNREADABLE" and cpu["mean"] is None and cpu["p95"] is None and cpu["shape"] is None


def test_m3_a_series_of_another_metric_type_is_unreadable_not_used():
    assert run(Cloud(cpu=(series(MEM, dist(5, 100, 0.24)),)), metrics=True)["metrics"]["cpu"]["status"] == "UNREADABLE"


def test_m3_an_execution_without_a_start_time_is_not_queried_at_all():
    cloud = Cloud(cpu=SINGLE_THREAD, drop_start=True)
    metrics = run(cloud, metrics=True)["metrics"]
    assert metrics["cpu"]["status"] == "NOT_QUERIED" and metrics["window"] is None
    assert metrics["cpu"]["mean"] is None and metrics["memory"]["peak_bytes_upper_bound"] is None
    assert not [c for c in cloud.calls if "monitoring" in c]


# ───────────── M4 ─────────────

def test_m4_p95_at_one_vcpu_of_four_is_single_thread_bound():
    cpu = run(Cloud(cpu=SINGLE_THREAD), metrics=True)["metrics"]["cpu"]            # job fixture: cpu "4"
    assert cpu["allocated_vcpus"] == 4 and cpu["p95_vcpus"] == pytest.approx(0.99) and cpu["mean_vcpus"] == pytest.approx(0.96)
    assert cpu["shape"] == "SINGLE_THREAD_BOUND"


def test_m4_a_flat_load_across_all_vcpus_an_idle_and_a_partly_parallel_build_are_not_single_thread():
    # [0.95,1.0): p95 .9975 -> ~4 vCPU · [0.05,0.10): p95 .0975 -> .39 vCPU · [0.50,0.55): p95 .5475 -> 2.19 vCPU
    shapes = [run(Cloud(cpu=(series(CPU, dist(i, 100, m)),)), metrics=True)["metrics"]["cpu"]["shape"] for i, m in ((20, 0.98), (2, 0.07), (11, 0.52))]
    assert shapes == ["SATURATES_ALL_VCPUS", "BELOW_ONE_VCPU", "MULTI_THREAD_PARTIAL"]


def test_m4_a_burst_at_one_vcpu_with_a_low_mean_is_not_a_bound():
    # 6 of 100 samples in [0.20,0.25) (~1 vCPU of 4), 94 in [0.05,0.10)... idle: p95 lands in the busy bucket (target 95, 94 below), mean ~0.1 vCPU < 0.5
    cpu = run(Cloud(cpu=(series(CPU, dist(5, 6, 0.24), dist(1, 94, 0.01)),)), metrics=True)["metrics"]["cpu"]
    assert cpu["p95_vcpus"] == pytest.approx(0.2 * 4 + 0.05 * 4 * ((95 - 94) / 6)) and cpu["mean_vcpus"] < 0.5 and cpu["shape"] == "BURSTY_AT_ONE_VCPU"


def test_m4_with_one_allocated_vcpu_saturation_is_the_allocation_not_a_thread_verdict():
    cpu = run(Cloud(cpu=(series(CPU, dist(20, 100, 0.98)),), job=job_with(cpu="1")), metrics=True)["metrics"]["cpu"]
    assert cpu["allocated_vcpus"] == 1 and cpu["shape"] == "SATURATES_ALLOCATION_ONE_VCPU"


def test_m4_an_unreadable_allocation_gives_no_shape():
    cpu = run(Cloud(cpu=SINGLE_THREAD, job=job_with(cpu="lots")), metrics=True)["metrics"]["cpu"]
    assert cpu["allocated_vcpus"] is None and cpu["shape"] is None and cpu["mean"] == pytest.approx(0.24)


# ───────────── M5 ─────────────

def test_m5_memory_peak_is_the_highest_bucket_upper_bound_and_bytes_against_the_allocation():
    # peak sample in [0.40,0.45) -> upper bound .45 of 16Gi
    memory = run(Cloud(memory=(series(MEM, dist(5, 50, 0.1), dist(9, 1, 0.42)),)), metrics=True)["metrics"]["memory"]
    assert memory["max_upper_bound"] == pytest.approx(0.45) and memory["peak_bytes_upper_bound"] == pytest.approx(0.45 * 16 * 1024 ** 3)


def test_m5_a_sample_in_the_open_overflow_bucket_has_no_upper_bound():
    memory = run(Cloud(memory=(series(MEM, dist(21, 3, 1.2)),)), metrics=True)["metrics"]["memory"]
    assert memory["status"] == "OK" and memory["mean"] == pytest.approx(1.2) and memory["max_upper_bound"] is None
    assert memory["peak_bytes_upper_bound"] is None


# ───────────── M6 / M7 ─────────────

def test_m6_db_wait_is_stated_as_not_exposed_with_no_number():
    wait = run(Cloud(cpu=SINGLE_THREAD), metrics=True)["metrics"]["wait"]
    assert wait["status"] == "NOT_EXPOSED" and set(wait) == {"status", "reason"}


def test_m7_different_bucket_layouts_give_no_pooled_percentile_but_mean_and_bound_stay():
    other = {"explicitBuckets": {"bounds": [0.1, 0.5]}}
    cpu = run(Cloud(cpu=(series(CPU, dist(5, 100, 0.24), dist(1, 100, 0.3, options=other, total_buckets=3)),)), metrics=True)["metrics"]["cpu"]
    assert cpu["p95"] is None and cpu["shape"] is None and cpu["mean"] == pytest.approx(0.27) and cpu["max_upper_bound"] == pytest.approx(0.5)


# ───────────── M8 ─────────────

def test_m8_metrics_needs_an_execution_and_stops_before_any_cloud_call():
    cloud = Cloud()
    with pytest.raises(CR.Refused, match="--metrics requires --execution"):
        CR.measure(None, cloud, metrics=True)
    assert cloud.calls == []


def test_m8_the_cli_carries_metrics_end_to_end(tmp_path):
    (tmp_path / "answers").mkdir()
    for name in ("job", "image", "execution_succeeded"):
        (tmp_path / "answers" / f"{name}.json").write_text((FIX / f"{name}.json").read_text())
    (tmp_path / "answers" / "cpu.json").write_text(json.dumps(list(SINGLE_THREAD)))
    (tmp_path / "answers" / "mem.json").write_text("[]")
    stub = tmp_path / "gcloud"
    stub.write_text("#!/bin/sh\n"
                    f'D="{tmp_path}/answers"\n'
                    'echo "$@" >> "$D/../calls.log"\n'
                    'case "$*" in\n'
                    '  *"container/cpu/utilizations"*) cat "$D/cpu.json" ;;\n'
                    '  *"container/memory/utilizations"*) cat "$D/mem.json" ;;\n'
                    '  *"jobs executions describe"*) cat "$D/execution_succeeded.json" ;;\n'
                    '  *"images describe"*) cat "$D/image.json" ;;\n'
                    '  *"jobs describe"*) cat "$D/job.json" ;;\n'
                    '  *) exit 9 ;;\nesac\n')
    stub.chmod(stub.stat().st_mode | stat.S_IXUSR)
    env = {"PATH": f"{tmp_path}:/usr/bin:/bin", "HOME": str(tmp_path)}

    def go(*args):
        return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, env=env, cwd=tmp_path)
    done = go("--execution", EXEC, "--metrics", "true")
    assert done.returncode == 0, done.stdout + done.stderr
    record = json.loads(done.stdout)
    assert record["metrics"]["cpu"]["shape"] == "SINGLE_THREAD_BOUND" and record["metrics"]["memory"]["status"] == "ABSENT"
    before = len((tmp_path / "calls.log").read_text().splitlines())
    assert before == 5
    assert go("--metrics", "true").returncode == 1 and go("--execution", EXEC, "--metrics", "false").returncode == 2
    assert len((tmp_path / "calls.log").read_text().splitlines()) == before


# ───────────── M9 ─────────────

def test_m9_the_executor_admits_the_metrics_argument_and_refuses_an_unknown_one(tmp_path, monkeypatch):
    monkeypatch.setenv("KY_ROOT", str(tmp_path / "ky"))
    spec = importlib.util.spec_from_file_location("ky_exec_cr_metrics", FLEET / "executor.py")
    ex = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ex)
    table = json.loads((FLEET / "executor_ops.json").read_text())["ops"]

    def req(args):
        return {"operation_id": "op-cr-m", "kind": "cloudrun_job_readback", "item_id": "BOLD-09", "idempotency_key": "key-cr-m",
                "requested_by": "v1", "kyd": "kyd-1", "args": args}
    assert ex.validate(req({"execution": EXEC, "metrics": "true"}), table, {"gcloud": True}) is None
    assert "disallowed args" in ex.validate(req({"execution": EXEC, "metrics": "true", "limit": "9"}), table, {"gcloud": True})
