"""J-3-SUBSTEP-LOG (SR-J2D-TEARDOWN-EVIDENCE item 2): the measuring launch makes asset.substep reach Cloud Logging.

Why: events.emit_event publishes to Pub/Sub and prints NOTHING when PUBSUB_TOPIC is set and PUBSUB_DISABLED is not
(platform/python-sidecar/pipeline/orchestrator/events.py, emit_event). The J-3 gate reads sub-step progress from the
execution's job log (cloudrun_readback --logs), so the measuring execution must run with PUBSUB_DISABLED=1.

One oracle per distinct claim; the chain under test is launch argv -> job environment -> the REAL emit_event -> stdout lines
shaped as Cloud Logging textPayload entries (timestamps invented) -> the REAL cloudrun_readback logs parser -> the gate.

  S1  the measuring launch (measuring_launch's default launcher) passes `--update-env-vars=PUBSUB_DISABLED=1` on the one
      fixed `gcloud run jobs execute` call, and the small-test launch's argv is left exactly as it was
  S2  with that override, a job whose own environment has Pub/Sub on prints every asset.substep as "[event] <json>", the
      reader reports last index == total, and the J-3 gate reads PASS
  S3  planted reversion: no override -> no stdout sub-step lines -> the reader has nothing -> the gate reads NULL, never PASS
"""
import importlib.util
import io
import contextlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

FLEET = Path(__file__).resolve().parents[1]
REPO = FLEET.parents[3]
RUN = "11111111-2222-4333-8444-555555555555"
EXEC = "brahma-build-pipeline-job-abc12"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(FLEET))                      # measuring_launch does `import smalltest_launch as bridge`
ML = _load("measuring_launch_under_test", FLEET / "measuring_launch.py")
BRIDGE = ML.bridge
CR = _load("cloudrun_readback_under_test_sub", FLEET / "cloudrun_readback.py")
EVENTS = _load("events_under_test", REPO / "platform/python-sidecar/pipeline/orchestrator/events.py")

# The deployed job's own environment has Pub/Sub on (CURRENT_STATE_v1_0.md: PUBSUB_TOPIC=cockpit-events, PUBSUB_DISABLED absent).
JOB_ENV = {"PUBSUB_TOPIC": "cockpit-events"}


def launch_argv(launcher, monkeypatch):
    seen = []
    monkeypatch.setattr(BRIDGE.subprocess, "run", lambda argv, **kw: seen.append(list(argv)) or SimpleNamespace(
        returncode=0, stdout=EXEC + "\n", stderr=""))
    assert launcher(RUN, 20) == EXEC
    return seen[0]


def execution_env(argv):
    """The job's environment as `gcloud run jobs execute --update-env-vars` leaves it for this one execution."""
    env = dict(JOB_ENV)
    for arg in argv:
        if arg.startswith("--update-env-vars="):
            for pair in arg.split("=", 1)[1].split(","):
                key, value = pair.split("=", 1)
                env[key] = value
    return env


def job_log_after(env, monkeypatch):
    """Run the real emit_event for a 3-step asset under `env`; return what Cloud Logging would hold (stdout lines -> entries)."""
    for key in ("PUBSUB_DISABLED", "PUBSUB_TOPIC"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    published = []
    monkeypatch.setattr(EVENTS, "_pubsub_publish", published.append)      # no google client; Pub/Sub is a sink that is not the job log
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        for index, key in enumerate(("chunk_a", "chunk_b", "chunk_c"), start=1):
            EVENTS.emit_event({"type": "asset.substep", "chart_id": CHART, "asset_id": "ka_gochara_v5", "substep_key": key,
                               "substep_label": key, "index": index, "total": 3, "skipped": False})
    entries = [{"insertId": f"i{n}", "textPayload": line, "timestamp": f"2026-10-17T10:00:{n:02d}.123456789Z",
                "labels": {"run.googleapis.com/execution_name": EXEC},
                "resource": {"type": "cloud_run_job", "labels": {"job_name": "brahma-build-pipeline-job", "location": "asia-south1"}}}
               for n, line in enumerate(out.getvalue().splitlines(), start=1)]
    return entries, published


def read_logs(entries):
    def runner(argv):
        return SimpleNamespace(returncode=0, stdout=json.dumps(entries), stderr="")
    return CR.measure_logs(EXEC, runner)


def j3_gate(logs):
    """The J-3 gate's sub-step claim: PASS only when a measured asset reached its last planned sub-step (last index == total).
    Anything the reader could not measure is None (N.8: a signal without a detector that can read false is null, not green)."""
    assets = logs["substeps"]["assets"]
    if not assets:
        return None
    return "PASS" if all(a["total"] is not None and a["last_index"] == a["total"] for a in assets) else None


def test_s1_measuring_launch_sets_pubsub_disabled_for_this_execution_only(monkeypatch):
    assert ML.run.__kwdefaults__["launcher"] is ML.measuring_cloud_launcher
    argv = launch_argv(ML.measuring_cloud_launcher, monkeypatch)
    assert argv == ["gcloud", "run", "jobs", "execute", "brahma-build-pipeline-job", "--project=madhav-astrology",
                    "--region=asia-south1", "--update-env-vars=PUBSUB_DISABLED=1", "--args=--run-id," + RUN, "--async",
                    "--format=value(metadata.name)"]
    plain = launch_argv(BRIDGE.cloud_launcher, monkeypatch)                  # the small-test launch is untouched
    assert not any("env-vars" in arg for arg in plain)


def test_s2_with_the_override_every_substep_reaches_the_job_log_and_the_gate_passes(monkeypatch):
    argv = launch_argv(ML.measuring_cloud_launcher, monkeypatch)
    entries, published = job_log_after(execution_env(argv), monkeypatch)
    assert len(entries) == 3 and published == []
    assert all(e["textPayload"].startswith("[event] {") for e in entries)
    logs = read_logs(entries)
    asset, = logs["substeps"]["assets"]
    assert (asset["asset_id"], asset["substeps_seen"], asset["total"], asset["last_index"]) == ("ka_gochara_v5", 3, 3, 3)
    assert logs["substeps"]["last_substep"]["index"] == logs["substeps"]["last_substep"]["total"] == 3
    assert j3_gate(logs) == "PASS"


def test_s3_planted_reversion_without_the_override_the_log_is_empty_and_the_gate_reads_null(monkeypatch):
    argv = launch_argv(BRIDGE.cloud_launcher, monkeypatch)                    # reversion: the launch before this change
    entries, published = job_log_after(execution_env(argv), monkeypatch)
    assert entries == [] and len(published) == 3                              # events went to Pub/Sub, not to the job log
    logs = read_logs(entries)
    assert logs["substeps"] == {"last_substep": None, "assets": []}
    assert j3_gate(logs) is None
