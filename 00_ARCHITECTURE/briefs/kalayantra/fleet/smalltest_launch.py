#!/usr/bin/env python3
"""Stage once and launch exactly that small-test run; never evaluate child prose.

Only the credential-bearing executor invokes this entry point after pre-acceptance.
A durable per-run claim precedes the remote call and survives every outcome. It is
never cleared automatically: a timeout/interrupt may mean the job was launched.
The explicit --dry-run rehearses staging and rolls it back, without a claim or
remote launch; it uses the dispatcher's normal admission checks and report.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
ASSET = "ka_gochara_v5"
JOB = "brahma-build-pipeline-job"
EXECUTION = re.compile(r"brahma-build-pipeline-job-[a-z0-9]+(?:-[a-z0-9]+)*")


class Refused(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def cloud_launcher(run_id, timeout_s, *, update_env_vars=None):
    """Fixed target, one async request; neither credentials nor commands in output.

    `update_env_vars` is a fixed, caller-coded per-execution override (never request input), e.g.
    "PUBSUB_DISABLED=1"; None leaves the job's own environment untouched (the small-test launch).
    """
    env_flag = [f"--update-env-vars={update_env_vars}"] if update_env_vars else []
    result = subprocess.run(
        ["gcloud", "run", "jobs", "execute", JOB, "--project=madhav-astrology", "--region=asia-south1",
         *env_flag, f"--args=--run-id,{run_id}", "--async", "--format=value(metadata.name)"],
        capture_output=True, text=True, timeout=timeout_s, check=False)
    if result.returncode:
        raise Refused("remote launch failed or outcome unknown; reconcile the retained claim, never retry")
    return result.stdout.strip()


def _remaining(connection, created_at):
    now = connection.execute("SELECT clock_timestamp() AS db_now").fetchone()["db_now"]
    if not isinstance(created_at, dt.datetime) or created_at.tzinfo is None or not isinstance(now, dt.datetime) or now.tzinfo is None:
        raise Refused("timezone-qualified database creation time and clock required")
    age = (now - created_at).total_seconds()
    if not 0 <= age < 600:
        raise Refused("staged run is stale or has a future creation time; re-stage through the governed path")
    # A sub-second budget is unsafe for a subprocess timeout; refuse it.
    remaining = math.floor(600 - age)
    if remaining < 1:
        raise Refused("staged run has no launch budget left")
    return remaining


def _write_claim(path, value, *, exclusive=False):
    # The initial O_EXCL is the cross-process no-retry fence. A partial claim also
    # refuses replay. fsync before any remote effect; no unlink on error.
    flags = os.O_WRONLY | os.O_CREAT | (os.O_EXCL if exclusive else os.O_TRUNC)
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        raise Refused("run already claimed/launched or launch outcome unknown; reconcile, never retry") from None
    with os.fdopen(fd, "w") as stream:
        stream.write(canonical(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def launch_staged(*, run_id, expected_manifest, connection, claim_dir, launcher=cloud_launcher, launch_schema="ky.smalltest_launch/1"):
    """Caller owns transaction; hold run/asset row locks until launch returns.

    `launcher(run_id, timeout_s)` is injectable. All identity and age checks run
    against the locked DB row, not stdout or the client clock.
    """
    try:
        if str(uuid.UUID(run_id)) != run_id:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise Refused("canonical run UUID required") from None
    row = connection.execute(
        "SELECT id, chart_id, state, scope, scope_target, action, plan, triggered_by, "
        "plan_manifest, plan_manifest_digest, created_at, started_at FROM build_runs WHERE id = %s FOR UPDATE",
        (run_id,)).fetchone()
    expected = dict(id=run_id, chart_id=CHART, state="planned", scope="asset_set", scope_target=ASSET,
                    action="rebuild", plan=[ASSET], triggered_by="gochara-v5-small-test", started_at=None)
    if not row or any((str(row.get(k)) if k in ("id", "chart_id") else row.get(k)) != v for k, v in expected.items()):
        raise Refused("staged run identity/state mismatch or already started")
    digest = hashlib.sha256(canonical(expected_manifest).encode()).hexdigest()
    if (row["plan_manifest"] != expected_manifest or row["plan_manifest_digest"] != digest
            or expected_manifest.get("chart_id") != CHART or expected_manifest.get("scope_target") != ASSET
            or not expected_manifest.get("gochara_v5_test_slice")):
        raise Refused("staged manifest differs from the reviewed checkout/request")
    assets = connection.execute("SELECT asset_id, state, position FROM build_run_assets WHERE run_id = %s FOR UPDATE", (run_id,)).fetchall()
    if [dict(a) for a in assets] != [dict(asset_id=ASSET, state="queued", position=0)]:
        raise Refused("staged asset queue mismatch or already started")
    _remaining(connection, row["created_at"])
    claim_dir = Path(claim_dir)
    claim_dir.mkdir(parents=True, exist_ok=True)
    path = claim_dir / f"{run_id}.json"
    record = dict(schema=launch_schema, status="LAUNCH_PENDING", run_id=run_id, chart_id=CHART,
                  asset_id=ASSET, plan_manifest_digest=digest, created_at=row["created_at"].isoformat(),
                  execute_by=(row["created_at"] + dt.timedelta(minutes=10)).isoformat(), execution_name=None)
    _write_claim(path, record, exclusive=True)
    # Re-read the DB clock after local persistence, immediately before the call.
    remaining = _remaining(connection, row["created_at"])
    execution = launcher(run_id, remaining)
    if not isinstance(execution, str) or not EXECUTION.fullmatch(execution):
        raise Refused("remote execution identity absent or wrong job; retained claim requires reconciliation")
    record.update(status="LAUNCHED", execution_name=execution)
    _write_claim(path, record)
    return record


def run(argv=None, *, dispatcher=None, connect=None, launcher=cloud_launcher, claim_dir=None, launch_schema="ky.smalltest_launch/1"):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, choices=("all_classes_1y", "one_class_full", "all_classes_full"))
    parser.add_argument("--classes", default="all")
    parser.add_argument("--horizon-start")
    parser.add_argument("--horizon-end")
    parser.add_argument("--dry-run", action="store_true", help="rehearse staging and roll back; never launch")
    args = parser.parse_args(argv)
    if dispatcher is None:
        scripts = Path(__file__).resolve().parents[4] / "platform/scripts"
        sys.path.insert(0, str(scripts))
        import dispatch_v5_small_test_job as dispatcher
    marker = dispatcher.build_slice_marker(run=args.run, classes=args.classes,
                                            horizon_start=args.horizon_start, horizon_end=args.horizon_end)
    staging = ["--i-am-steward", "--after-settled-1", "--dry-run" if args.dry_run else "--execute",
               "--run", args.run, "--classes", args.classes]
    for key in ("horizon_start", "horizon_end"):
        if getattr(args, key) is not None:
            staging += ["--" + key.replace("_", "-"), getattr(args, key)]
    if args.dry_run:
        return dispatcher.main(staging)
    if connect is None:
        import psycopg
        import psycopg.rows
        connect = lambda: psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
    output = io.StringIO()
    # Preserve the dispatcher's safe error/commit-unknown behavior. Never stage
    # again if it throws, even when a run id was printed or COMMIT was sent.
    with contextlib.redirect_stdout(output):
        dispatcher.main(staging)
    run_id = output.getvalue().strip()
    if not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", run_id):
        raise Refused("staging output is not exactly one run UUID; lookup required, never retry")
    conn = connect()
    try:
        conn.execute("SELECT set_config('lock_timeout', '5s', true)")
        candidate = dispatcher._load_inactive_candidate(conn.cursor())
        manifest, _ = dispatcher.build_small_test_manifest(candidate=candidate, slice_marker=marker)
        result = launch_staged(run_id=run_id, expected_manifest=manifest, connection=conn,
                               claim_dir=claim_dir or Path(os.environ["KY_ROOT"]) / "run/ops/smalltest_launch",
                               launcher=launcher, launch_schema=launch_schema)
        print(canonical(result), flush=True)
        return result
    finally:
        # No run mutation here. The independently committed staging transaction
        # is left intact, including on an unknown remote outcome.
        conn.rollback()
        conn.close()


def cli(argv=None):
    try:
        run(argv)
        return 0
    except BaseException as exc:
        if isinstance(exc, SystemExit):
            return exc.code
        # Neither DB exceptions nor remote output may expose credentials.
        print(f"launch bridge failed ({type(exc).__name__}); staged/remote outcome may be unknown; reconcile retained evidence, never retry", file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 1


if __name__ == "__main__":
    raise SystemExit(cli())
