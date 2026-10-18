#!/usr/bin/env python3
"""Launch ONE run of the Gochara verification job under the verifier principal (J-4b; SR-PREBUILD-ALL). Durable no-retry launch fence.

The executor runs this for the fixed kinds `verification_job` (launch) and `verification_job_dryrun` (`--dry-run`: the same validation, no claim and
no launch) of fleet/executor_ops.json. The job it starts is the already-defined Cloud Run job `gochara-verification-job` (gochara-verification-job-deploy.yml);
this module never defines or changes a job, holds no database connection and no credential: the job's own task holds GOCHARA_VERIFIER_DB_URL
(operation_adapters INTERPRETATION I3), so the executor needs `gcloud` and nothing else.

What one run does, in order (every refusal happens before the next step):
  1 request     KY_OPERATION_REQUEST must be this mode's kind, name the canonical chart, a merged-commit-shaped `reviewed_commit` and the one argument
                `generation` = 5.0, equal to this command line's `--generation`. The request digest (the executor's own, scheduler_reaper.request_digest) is recorded.
  2 definition  READ the registry digest of `brahma-pipeline:<reviewed_commit>` and the deployed job (v1 describe + the presence-bearing v2 `jobs.get`), and judge
                the job by the SAME contract the seal workflow uses (gochara_verification_job_readback.check): that exact image digest, the verifier service
                account, the one verifier secret, entry point, no args, maxRetries present and 0, runner commit == reviewed_commit. Anything else REFUSES.
  3 claim       (execute only) an O_EXCL claim file per operation, fsynced before the remote call and never cleared: a timeout may mean the job started.
  4 launch      (execute only) ONE `gcloud run jobs execute gochara-verification-job --args=--chart,<canonical>,--generation,5.0 --async`. The arguments are a
                constant of this file; the request supplies only the generation, which must be 5.0. `--brief` and `--sealing-commit` are NEVER passed: the seal brief
                belongs to the human-approved gochara-seal-approved.yml workflow, which this kind does not replace. `--report-only` is not passed either (it can
                never reach VERIFIED).
  5 readback    (execute only) the EXECUTED resource is read and judged by the same contract (image digest, exact args, no env override, no retries). A launch whose
                executed resource does not conform, or cannot be read, still printed LAUNCHED (it was) but exits 1: it is never a green.

Prints ONE line, a `ky.verification_launch/1` JSON record (status DRY_RUN | LAUNCHED). `executed_check.status` is CONFORMS | NONCONFORMING | UNREADABLE (null in a dry run).
A failure after step 3 leaves the claim in LAUNCH_PENDING and the exit non-zero: reconcile, never retry. Honest nulls (CLAUDE.md §N.7.6 / §N.8): nothing here says the
job SUCCEEDED; the launch is not the verification. Its outcome is the execution read back later and the persisted attestations.

(I) INTERPRETATION V-1 (mode): the kind starts the PERSISTING verification run, `--chart <C> --generation 5.0` — the same shape the seal workflow passes minus `--brief` — because
  the seal brief reads the attestations this run writes. Alternative: `--final-rules` (verify the explicitly configured final-rule candidate); not passed, since the
  workflow's own brief run does not pass it and the request cannot carry it.
(I) INTERPRETATION V-2 (same-commit rule): the request's `reviewed_commit` is the runner commit the job must have been defined at (the workflow's rule). Alternative:
  accept any commit the job runs; refused, it would let an older image verify a newer build.
(I) INTERPRETATION V-3 (claim key): one claim per operation_id, under $KY_ROOT/run/ops/verification_launch. Alternative: one per (chart, generation, commit); refused, a
  governed re-run after a REFUSED/exit-3 verification is legitimate and the executor's idempotency key already stops a replay of the same request.
(I) INTERPRETATION V-4 (dry run reads): the dry run does the cloud READS (digest, definition) and no write, so `dry_run_passed` means the definition is launchable now.
  Alternative: plan only, no read; refused, a dry run that cannot fail on the definition attests nothing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "platform/scripts"))

import cloudrun_readback as readback                      # noqa: E402  PROJECT / REGION / IMAGE_REPO / gcloud_json / registry_digest / default_runner
import gochara_seal_execution_check as execchk            # noqa: E402  the verifier identity and the job's resources, and the executed-resource task reader
import gochara_verification_job_contract as vjc           # noqa: E402  the pinned task contract (shared byte for byte with the deploy and seal workflows)
import gochara_verification_job_readback as jobrb         # noqa: E402  the deployed-definition check
import smalltest_launch as bridge                         # noqa: E402  the durable claim fence and canonical JSON, shared with the other launchers
from scheduler_reaper import request_digest               # noqa: E402  the executor's request digest, byte for byte

SCHEMA = "ky.verification_launch/1"
CHART = bridge.CHART
GENERATION = "5.0"
JOB = "gochara-verification-job"
SECRET = "gochara-verifier-db-url"
CLOUDSQL_INSTANCE = "madhav-astrology:asia-south1:amjis-postgres"
KIND_EXECUTE, KIND_DRYRUN = "verification_job", "verification_job_dryrun"
EXECUTE_ARGS = ("--chart", CHART, "--generation", GENERATION)
EXECUTION = re.compile(JOB + r"-[a-z0-9]+(?:-[a-z0-9]+)*")
SAFE_ID = re.compile(r"[A-Za-z0-9_.-]{1,80}")
COMMIT = re.compile(r"[0-9a-f]{40}")
V2_JOB_URL = f"https://run.googleapis.com/v2/projects/{readback.PROJECT}/locations/{readback.REGION}/jobs/{JOB}"
HTTP_TIMEOUT_S = 60
Refused = bridge.Refused
REFUSALS = (bridge.Refused, readback.Refused, execchk.Refused, jobrb.Refused)      # each message is structural text (no stderr, no value)


def job_describe_argv() -> list[str]:
    return ["gcloud", "run", "jobs", "describe", JOB, f"--project={readback.PROJECT}", f"--region={readback.REGION}", "--format=json"]


def execute_argv() -> list[str]:
    """The one launch: fixed project, region, job and arguments; asynchronous; prints only the execution name."""
    return ["gcloud", "run", "jobs", "execute", JOB, f"--project={readback.PROJECT}", f"--region={readback.REGION}",
            "--args=" + ",".join(EXECUTE_ARGS), "--async", "--format=value(metadata.name)"]


def execution_describe_argv(name: str) -> list[str]:
    return ["gcloud", "run", "jobs", "executions", "describe", name, f"--project={readback.PROJECT}", f"--region={readback.REGION}", "--format=json"]


def http_get(url: str, token: str) -> dict:
    """The presence-bearing v2 REST read (the seal workflow's curl). The token is in a header, never in an argv, a record or an error."""
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_S) as response:
            value = json.load(response)
    except Exception:
        raise Refused("v2 read: the request failed or the answer is not JSON") from None
    if not isinstance(value, dict):
        raise Refused("v2 read: the answer is not a JSON object")
    return value


def read_v2(url: str, runner, fetch) -> dict:
    try:
        result = runner(["gcloud", "auth", "print-access-token"])
    except (OSError, subprocess.SubprocessError):
        raise Refused("v2 read: gcloud could not be run or timed out") from None
    token = (result.stdout or "").strip() if not result.returncode else ""
    if not token:
        raise Refused("v2 read: no access token")
    return fetch(url, token)


def bind_request(environ, argv_generation: str, dry_run: bool) -> tuple[dict, str]:
    """The request this process was started for. (request, request_sha256); a refusal names the field, never a value that could be a credential."""
    try:
        request = json.loads(environ.get("KY_OPERATION_REQUEST") or "null")
    except ValueError:
        request = None
    if not isinstance(request, dict):
        raise Refused("KY_OPERATION_REQUEST is missing or not a JSON object")
    want = KIND_DRYRUN if dry_run else KIND_EXECUTE
    if request.get("kind") != want:
        raise Refused(f"the request is not a {want} request")
    if not isinstance(request.get("operation_id"), str) or not SAFE_ID.fullmatch(request["operation_id"]) or request["operation_id"].startswith("."):
        raise Refused("operation_id is missing or unsafe")
    if request.get("chart_id", CHART if dry_run else None) != CHART:
        raise Refused("chart_id is not the canonical chart")      # a production request must carry it; a dry run may omit it (executor admission, A8 §3.8)
    if not isinstance(request.get("reviewed_commit"), str) or not COMMIT.fullmatch(request["reviewed_commit"]):
        raise Refused("reviewed_commit is not a 40-hex commit")
    args = request.get("args")
    if not isinstance(args, dict) or set(args) != {"generation"} or args["generation"] != GENERATION or argv_generation != GENERATION:
        raise Refused(f"the only verified generation is {GENERATION}, and the request and the command line must both name it")
    return request, request_digest(request)


def definition_check(request: dict, runner, fetch) -> dict:
    """READ the registry digest and the deployed job and judge it. Reads only; raises Refused with every reason when the job is not launchable as defined."""
    commit = request["reviewed_commit"]
    digest = readback.registry_digest(commit, runner)
    job = readback.gcloud_json(job_describe_argv(), runner, "job")
    v2_job = read_v2(V2_JOB_URL, runner, fetch)
    try:
        problems = jobrb.check(job, v2_job=v2_job, image_repo=readback.IMAGE_REPO, image_digest=digest, service_account=execchk.VERIFIER_SERVICE_ACCOUNT,
                               runner_commit=commit, secret_name=SECRET, cloudsql_instance=CLOUDSQL_INSTANCE, timeout_seconds=execchk.JOB_TIMEOUT_SECONDS,
                               memory=execchk.JOB_MEMORY, cpu=execchk.JOB_CPU)
    except jobrb.Refused as exc:
        raise Refused(f"the verification job definition could not be judged: {exc}") from None
    if problems:
        raise Refused("the verification job is not defined as launched here: " + "; ".join(problems))
    return {"image_digest": digest, "status": "CONFORMS"}


def executed_check(name: str, image_digest: str, commit: str, runner, fetch) -> dict:
    """The EXECUTED resource, judged by the same contract as the definition and with the exact arguments this launcher passed. Never raises: UNREADABLE says so."""
    try:
        execution = readback.gcloud_json(execution_describe_argv(name), runner, "execution")
        v2 = read_v2(f"{V2_JOB_URL}/executions/{name}", runner, fetch)
        if (execution.get("metadata") or {}).get("name") != name:
            return {"status": "NONCONFORMING", "problems": [f"the described resource is not execution {name}"]}
        retries = jobrb.strict_v2_retries(v2, "execution")
        problems = vjc.forbidden_annotations(execution, v2) + vjc.validate_task(
            execchk._task_spec(execution), image_repo=readback.IMAGE_REPO, image_digest=image_digest, service_account=execchk.VERIFIER_SERVICE_ACCOUNT,
            runner_commit=commit, secret_name=SECRET, expected_args=list(EXECUTE_ARGS), timeout_seconds=execchk.JOB_TIMEOUT_SECONDS,
            memory=execchk.JOB_MEMORY, cpu=execchk.JOB_CPU, v2_retries=retries)
    except REFUSALS as exc:
        return {"status": "UNREADABLE", "problems": [str(exc)]}
    return {"status": "NONCONFORMING", "problems": problems} if problems else {"status": "CONFORMS", "problems": []}


def cloud_launcher(runner=readback.default_runner) -> str:
    try:
        result = runner(execute_argv())
    except (OSError, subprocess.SubprocessError):
        raise Refused("remote launch failed or outcome unknown; reconcile the retained claim, never retry") from None
    if result.returncode:
        raise Refused("remote launch failed or outcome unknown; reconcile the retained claim, never retry")
    return (result.stdout or "").strip()


def run(argv=None, *, environ=None, runner=readback.default_runner, fetch=http_get, launcher=None, claim_dir=None, now=None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--generation", required=True)
    parser.add_argument("--dry-run", action="store_true", help="validate and print the plan; no claim, no launch")
    args = parser.parse_args(argv)
    environ = os.environ if environ is None else environ
    now = now or dt.datetime.now(dt.timezone.utc)
    request, digest = bind_request(environ, args.generation, args.dry_run)
    definition = definition_check(request, runner, fetch)
    record = {"schema": SCHEMA, "status": "DRY_RUN" if args.dry_run else "LAUNCH_PENDING", "mode": "dry_run" if args.dry_run else "execute",
              "operation_id": request["operation_id"], "item_id": request.get("item_id"), "request_sha256": digest, "reviewed_commit": request["reviewed_commit"],
              "chart_id": CHART, "generation": GENERATION, "project": readback.PROJECT, "region": readback.REGION, "job": JOB,
              "service_account": execchk.VERIFIER_SERVICE_ACCOUNT, "image_digest": definition["image_digest"], "definition_check": definition["status"],
              "args": list(EXECUTE_ARGS), "execution_name": None, "executed_check": None, "measured_at": now.isoformat(timespec="seconds"),
              "plan": {"execute": execute_argv()}}
    if args.dry_run:
        return record
    root = environ.get("KY_ROOT")
    if not root and claim_dir is None:
        raise Refused("KY_ROOT is not set")
    claim_dir = Path(claim_dir or Path(root) / "run/ops/verification_launch")
    claim_dir.mkdir(parents=True, exist_ok=True)
    path = claim_dir / f"{request['operation_id']}.json"
    claim = {k: v for k, v in record.items() if k != "plan"}
    bridge._write_claim(path, claim, exclusive=True)                 # the cross-process no-retry fence; before any remote effect
    execution = (launcher or (lambda: cloud_launcher(runner)))()
    if not isinstance(execution, str) or not EXECUTION.fullmatch(execution):
        raise Refused("remote execution identity absent or wrong job; retained claim requires reconciliation")
    claim.update(status="LAUNCHED", execution_name=execution)
    bridge._write_claim(path, claim)
    record.update(status="LAUNCHED", execution_name=execution, executed_check=executed_check(execution, definition["image_digest"], request["reviewed_commit"], runner, fetch))
    claim["executed_check"] = record["executed_check"]
    bridge._write_claim(path, claim)
    return record


def cli(argv=None, **injected):
    try:
        record = run(argv, **injected)
    except SystemExit as exc:
        return exc.code
    except BaseException as exc:
        reason = f": {exc}" if isinstance(exc, REFUSALS) else ""      # a refusal's message never repeats a credential; any other exception is named by class only
        print(f"verification launch failed ({type(exc).__name__}{reason}); reconcile retained evidence, never retry", file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 1
    print(bridge.canonical(record), flush=True)
    return 0 if record["status"] == "DRY_RUN" or record["executed_check"]["status"] == "CONFORMS" else 1


if __name__ == "__main__":
    raise SystemExit(cli())
