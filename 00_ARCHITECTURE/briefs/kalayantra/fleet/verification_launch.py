#!/usr/bin/env python3
"""Launch ONE run of the Gochara verification job under the verifier principal (J-4b; SR-PREBUILD-ALL). Durable no-retry launch fence.

The executor runs this for the fixed kinds `verification_job` (launch) and `verification_job_dryrun` (`--dry-run`: the same validation, then the job's own
`--report-only` run, waited for, with its ONE report printed) of fleet/executor_ops.json. The job it starts is the already-defined Cloud Run job `gochara-verification-job` (gochara-verification-job-deploy.yml);
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
                belongs to the human-approved gochara-seal-approved.yml workflow, which this kind does not replace. `--report-only` is not passed by the launch (it can
                never reach VERIFIED); it is the dry run's one mode (step 6).
  5 readback    (execute only) the EXECUTED resource is read and judged by the same contract (image digest, exact args, no env override, no retries). A launch whose
                executed resource does not conform, or cannot be read, still printed LAUNCHED (it was) but exits 1: it is never a green.

  6 report-only (dry run only) ONE `gcloud run jobs execute gochara-verification-job --args=--chart,<canonical>,--generation,5.0,--report-only --async`, then the execution is
                polled until it completes (never past WAIT_BUDGET_S, which is under the executor's cap), judged by the same contract with the report-only arguments,
                and the job's ONE report line is read back from its stdout log and printed UNCHANGED after the record. The job in this mode persists nothing (verification_job.run
                `persist=not report_only`) and reports the combined candidate gate honestly; whether the report is clean is judged by the pack's dryrun_gate, not here.

SHARDS (SR-OD1 R8, RECONCILIATION R-8): one whole-generation execution of the 26 classes cannot fit the job's 28,800 s task timeout, so a launch may name ONE shard of the pinned
partition (`fleet/VERIFY_SHARDS.json`, `ky.verification_shards/1`): the request carries the second argument `shard` (V01..), equal to the command line's `--shard`, and the job is
launched with `--class=<c>` once per class of that shard (the Cloud Run `--args` list is comma-joined, so a comma-separated class list is not usable; the job's flag is repeated, in the
`--class=<c>` form because gcloud's --args (ArgList + UpdateAction) refuses any repeated identical item, so `--class,c1,--class,c2` never reaches the API). The
shard -> classes map is read from the pinned file, never from the request, and its sha256 is in the record. Each shard is its own execution, its own operation and its own claim; the
rehearsal (`verification_job_dryrun --shard V03`) and the dispatch (`verification_job --shard V03`) run the same classes. Every row a shard persists carries its generation, head, image
digest, execution and classes (the job stamps them); the seal brief and the seal read only the generation-wide AGGREGATE, which refuses unless every class is attested at one head.
A dry run's record carries `report_only_run.capacity` (G-5, per shard: measured wall <= 0.75 x the task timeout; `verification_shards.py capacity` projects the 26-class total).
SR-W4-SIBLING-DRYRUN-ADMISSION: a shard request the executor admitted on the window's V01 dry run carries `sibling_dryrun` {ruling, image_digest}; this launcher then refuses (definition_check) unless the job's image digest is that
digest, so a job or image redefined after the dry run never launches. Without the field nothing changes.
A request with no `shard` launches the whole generation exactly as before (a small generation, a rehearsal); it is not the way to verify 26 classes.

Prints a `ky.verification_launch/1` JSON record (status DRY_RUN | LAUNCHED). A launch prints that one line; a dry run prints it and then the job's report line (the
record carries no `classes`, so the report is the one report in the output). `executed_check.status` is CONFORMS | NONCONFORMING | UNREADABLE (null in a dry run; the dry run's own is under `report_only_run`).
A failure after step 3 leaves the claim in LAUNCH_PENDING and the exit non-zero: reconcile, never retry. Honest nulls (CLAUDE.md §N.7.6 / §N.8): nothing here says the
job SUCCEEDED; the launch is not the verification. Its outcome is the execution read back later and the persisted attestations.

(I) INTERPRETATION V-1 (mode): the kind starts the PERSISTING verification run, `--chart <C> --generation 5.0` — the same shape the seal workflow passes minus `--brief` — because
  the seal brief reads the attestations this run writes. Alternative: `--final-rules` (verify the explicitly configured final-rule candidate); not passed, since the
  workflow's own brief run does not pass it and the request cannot carry it.
(I) INTERPRETATION V-2 (same-commit rule): the request's `reviewed_commit` is the runner commit the job must have been defined at (the workflow's rule). Alternative:
  accept any commit the job runs; refused, it would let an older image verify a newer build.
(I) INTERPRETATION V-3 (claim key): one claim per operation_id, under $KY_ROOT/run/ops/verification_launch. Alternative: one per (chart, generation, commit); refused, a
  governed re-run after a REFUSED/exit-3 verification is legitimate and the executor's idempotency key already stops a replay of the same request.
(I) INTERPRETATION V-4 (dry run = the job in --report-only): the dry run does the cloud READS (digest, definition), then runs the job with `--report-only` and returns its report,
  so `dry_run_passed` means the classes were measured, not that a definition exists (PR #3747 verify finding B3: a definition check read NULL at the pack's dryrun_gate and its seconds-long wall
  time was a proxy for the cost gate). Alternative: reads only; refused, it attests nothing about the classes or their cost. It writes no durable claim (a repeated report-only run persists
  nothing); a run that outlives the wait budget keeps running to the job's own task timeout and the refusal names it.
(I) INTERPRETATION V-5 (measured time): `execution_wall_s` is the execution's own completionTime - startTime and `waited_s` this process's wait; either is null when unread, never a guess.
(I) INTERPRETATION V-6 (the report line): taken from the execution's stdout log, newest 1000 entries, split entries (Cloud Logging `split`) reassembled in index order and only when
  complete; exactly one report or a refusal. The line is printed byte for byte as the job wrote it. Alternative: a projection of the report; refused, the gate must judge the job's own words.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "platform/scripts"))

import cloudrun_readback as readback                      # noqa: E402  PROJECT / REGION / IMAGE_REPO / gcloud_json / registry_digest / default_runner
import gochara_seal_execution_check as execchk            # noqa: E402  the verifier identity and the job's resources, and the executed-resource task reader
import gochara_verification_job_contract as vjc           # noqa: E402  the pinned task contract (shared byte for byte with the deploy and seal workflows)
import gochara_verification_job_readback as jobrb         # noqa: E402  the deployed-definition check
import smalltest_launch as bridge                         # noqa: E402  the durable claim fence and canonical JSON, shared with the other launchers
import verification_shards as shards                      # noqa: E402  the pinned class shards (SR-OD1 R8) and the G-5 capacity arithmetic
from scheduler_reaper import request_digest               # noqa: E402  the executor's request digest, byte for byte

SCHEMA = "ky.verification_launch/1"
CHART = bridge.CHART
GENERATION = "5.0"
JOB = "gochara-verification-job"
SECRET = "gochara-verifier-db-url"
CLOUDSQL_INSTANCE = "madhav-astrology:asia-south1:amjis-postgres"
KIND_EXECUTE, KIND_DRYRUN = "verification_job", "verification_job_dryrun"
EXECUTE_ARGS = ("--chart", CHART, "--generation", GENERATION)
REPORT_ONLY_ARGS = EXECUTE_ARGS + ("--report-only",)


def build_job_args(shard_classes=None, report_only: bool = False) -> tuple:
    """The job's argument list: the constants, then `--class=<c>` for each class of the shard (shard_classes comes only from the pinned file), then `--report-only` for a dry run.
    One `--class=<c>` item per class: gcloud's --args parser (ArgList + UpdateAction) refuses a repeated identical item, so a repeated bare `--class` is refused client-side."""
    base = EXECUTE_ARGS + tuple(f"--class={c}" for c in (shard_classes or ()))
    return base + (("--report-only",) if report_only else ())
WAIT_BUDGET_S = 21000          # under the executor's MAX_TIMEOUT (6 h = 21600): the refusal names the execution instead of the executor killing us silently
POLL_INTERVAL_S = 30
LOG_ATTEMPTS, LOG_RETRY_S = 8, 15                    # Cloud Logging lags a completed execution by seconds
LOG_PAGE_SIZE = 1000
EXECUTION = re.compile(JOB + r"-[a-z0-9]+(?:-[a-z0-9]+)*")
SAFE_ID = re.compile(r"[A-Za-z0-9_.-]{1,80}")
COMMIT = re.compile(r"[0-9a-f]{40}")
V2_JOB_URL = f"https://run.googleapis.com/v2/projects/{readback.PROJECT}/locations/{readback.REGION}/jobs/{JOB}"
HTTP_TIMEOUT_S = 60
UNREADABLE_POLLS = 5
Refused = bridge.Refused
REFUSALS = (bridge.Refused, readback.Refused, execchk.Refused, jobrb.Refused)      # each message is structural text (no stderr, no value)


def job_describe_argv() -> list[str]:
    return ["gcloud", "run", "jobs", "describe", JOB, f"--project={readback.PROJECT}", f"--region={readback.REGION}", "--format=json"]


def execute_argv(job_args=EXECUTE_ARGS) -> list[str]:
    """The one launch: fixed project, region, job and arguments (the dry run passes REPORT_ONLY_ARGS); asynchronous; prints only the execution name."""
    return ["gcloud", "run", "jobs", "execute", JOB, f"--project={readback.PROJECT}", f"--region={readback.REGION}",
            "--args=" + ",".join(job_args), "--async", "--format=value(metadata.name)"]


def report_logs_argv(name: str) -> list[str]:
    """The one fixed read of the execution's STDOUT log, newest first. `name` has matched EXECUTION, so nothing else varies."""
    flt = (f'resource.type="cloud_run_job" AND resource.labels.job_name="{JOB}" AND resource.labels.location="{readback.REGION}" '
           f'AND labels."run.googleapis.com/execution_name"="{name}" AND logName="projects/{readback.PROJECT}/logs/run.googleapis.com%2Fstdout"')
    return ["gcloud", "logging", "read", flt, f"--project={readback.PROJECT}", f"--limit={LOG_PAGE_SIZE}", "--order=desc", "--format=json"]


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


def bind_request(environ, argv_generation: str, dry_run: bool, argv_shard=None) -> tuple[dict, str]:
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
    if not isinstance(args, dict) or set(args) not in ({"generation"}, {"generation", "shard"}) or args["generation"] != GENERATION or argv_generation != GENERATION:
        raise Refused(f"the only verified generation is {GENERATION}, and the request and the command line must both name it")
    if args.get("shard") != argv_shard:
        raise Refused("the request and the command line must name the same shard (or both none)")
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
    sibling = request.get("sibling_dryrun")      # SR-W4-SIBLING-DRYRUN-ADMISSION: this request was admitted on the window's V01 dry run at that image; a job redefined since refuses
    if "sibling_dryrun" in request and not (isinstance(sibling, dict) and sibling.get("image_digest") == digest):
        raise Refused("the verification job's image digest is not the one sibling_dryrun names: the job was redefined after the V01 dry run")
    return {"image_digest": digest, "status": "CONFORMS"}


def executed_check(name: str, image_digest: str, commit: str, runner, fetch, job_args=EXECUTE_ARGS) -> dict:
    """The EXECUTED resource, judged by the same contract as the definition and with the exact arguments this launcher passed. Never raises: UNREADABLE says so."""
    try:
        execution = readback.gcloud_json(execution_describe_argv(name), runner, "execution")
        v2 = read_v2(f"{V2_JOB_URL}/executions/{name}", runner, fetch)
        if (execution.get("metadata") or {}).get("name") != name:
            return {"status": "NONCONFORMING", "problems": [f"the described resource is not execution {name}"]}
        retries = jobrb.strict_v2_retries(v2, "execution")
        problems = vjc.forbidden_annotations(execution, v2) + vjc.validate_task(
            execchk._task_spec(execution), image_repo=readback.IMAGE_REPO, image_digest=image_digest, service_account=execchk.VERIFIER_SERVICE_ACCOUNT,
            runner_commit=commit, secret_name=SECRET, expected_args=list(job_args), timeout_seconds=execchk.JOB_TIMEOUT_SECONDS,
            memory=execchk.JOB_MEMORY, cpu=execchk.JOB_CPU, v2_retries=retries)
    except REFUSALS as exc:
        return {"status": "UNREADABLE", "problems": [str(exc)]}
    return {"status": "NONCONFORMING", "problems": problems} if problems else {"status": "CONFORMS", "problems": []}


def cloud_launcher(runner=readback.default_runner, job_args=EXECUTE_ARGS, failure="remote launch failed or outcome unknown; reconcile the retained claim, never retry") -> str:
    try:
        result = runner(execute_argv(job_args))
    except (OSError, subprocess.SubprocessError):
        raise Refused(failure) from None
    if result.returncode:
        raise Refused(failure)
    return (result.stdout or "").strip()


def _entry_text(entry: dict):
    text = entry.get("textPayload")
    if not isinstance(text, str):
        payload = entry.get("jsonPayload")
        text = payload.get("message") if isinstance(payload, dict) else None
    return text if isinstance(text, str) else None


def _split_part(entry: dict):
    """(uid, index, total) of a Cloud Logging split entry; None when the entry is not split. A malformed `split` is a refusal, never a guess."""
    split = entry.get("split")
    if split is None:
        return None
    index, total = (split.get("index", 0), split.get("totalSplits")) if isinstance(split, dict) else (None, None)
    index = int(index) if isinstance(index, str) and index.isdigit() else index
    total = int(total) if isinstance(total, str) and total.isdigit() else total
    uid = split.get("uid") if isinstance(split, dict) else None
    if not (isinstance(uid, str) and uid and isinstance(index, int) and isinstance(total, int) and not isinstance(index, bool) and not isinstance(total, bool) and 0 <= index < total):
        raise Refused("report log: a split entry is malformed")
    return uid, index, total


def report_from_entries(entries: list) -> tuple[str, dict]:
    """The job's ONE report line (verbatim) and its parsed form. A report is a stdout line that is a JSON object carrying `classes` (an object) and `generation`
    - the same shape the pack's dryrun_gate selects. Split entries are joined in index order and only when every part is present. Exactly one report or a refusal."""
    texts, parts, seen = [], {}, set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise Refused("report log: an entry is not a JSON object")
        key = entry.get("insertId")
        if isinstance(key, str) and key:
            if key in seen:
                continue
            seen.add(key)
        text = _entry_text(entry)
        part = _split_part(entry)
        if text is None:
            continue
        if part is None:
            texts.append(text)
        else:
            uid, index, total = part
            if parts.setdefault(uid, {"total": total, "texts": {}})["total"] != total:
                raise Refused("report log: split entries disagree on their count")
            parts[uid]["texts"][index] = text
    incomplete = 0
    for group in parts.values():
        if sorted(group["texts"]) == list(range(group["total"])):
            texts.append("".join(group["texts"][i] for i in range(group["total"])))
        else:
            incomplete += 1
    found = []
    for text in texts:
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict) and isinstance(value.get("classes"), dict) and "generation" in value:
                found.append((line, value))
    if len(found) != 1:
        raise Refused(f"report log: {len(found)} verification reports in the newest {len(entries)} stdout entries, not exactly one"
                      + (f" ({incomplete} split report(s) incomplete)" if incomplete else ""))
    return found[0]


def read_report(name: str, runner, sleep) -> tuple[str, dict]:
    """The execution's report, read back from its stdout log. Cloud Logging lags a finished execution by seconds, so an absent report is re-read a bounded number of times."""
    last = None
    for attempt in range(LOG_ATTEMPTS):
        if attempt:
            sleep(LOG_RETRY_S)
        entries = readback.gcloud_json(report_logs_argv(name), runner, "report log", shape=list)
        try:
            return report_from_entries(entries)
        except Refused as exc:
            last = exc
    raise last


def wait_for_execution(name: str, job_reference: str, runner, sleep, monotonic) -> tuple[dict, float]:
    """Poll the execution until it is no longer RUNNING. A poll that cannot be read is retried (a multi-hour wait is not lost to one flaky call) up to UNREADABLE_POLLS in a row."""
    started, unreadable = monotonic(), 0
    while True:
        try:
            measured = readback.measure_execution(name, job_reference, runner, JOB)      # the execution's owner label is judged against THIS job (the reader defaults to the pipeline job)
            unreadable = 0
        except REFUSALS as exc:
            unreadable += 1
            if unreadable >= UNREADABLE_POLLS:
                raise Refused(f"execution {name} could not be read {UNREADABLE_POLLS} times in a row ({exc}); it may still be running: it persists nothing and ends at its task timeout") from None
            measured = None
        if measured is not None and measured["outcome"] != "RUNNING":
            return measured, monotonic() - started
        if monotonic() - started >= WAIT_BUDGET_S:
            raise Refused(f"execution {name} is still running after {WAIT_BUDGET_S} s; it persists nothing and ends at its task timeout; read it back with cloudrun_job_readback")
        sleep(POLL_INTERVAL_S)


def _wall_seconds(measured: dict):
    """completionTime - startTime of the execution itself (null when either is unread)."""
    try:
        start, end = (dt.datetime.fromisoformat(measured[k].replace("Z", "+00:00")) for k in ("start_time", "completion_time"))
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    return round((end - start).total_seconds(), 3) if end >= start else None


def report_only_run(definition: dict, request: dict, runner, fetch, launcher, sleep, monotonic, shard=None) -> dict:
    """The dry run's body: ONE `--report-only` execution of the job (of the shard's classes, when `shard` = {id, classes} is given), waited for, judged and its report read back.
    -> the `report_only_run` record (with `report_line`)."""
    run_args = build_job_args((shard or {}).get("classes"), report_only=True)
    execution = (launcher or (lambda: cloud_launcher(runner, run_args, "report-only launch failed or outcome unknown; list the job's executions before running again")))()
    if not isinstance(execution, str) or not EXECUTION.fullmatch(execution):
        raise Refused("report-only execution identity absent or wrong job; list the job's executions before running again")
    measured, waited = wait_for_execution(execution, f"{readback.IMAGE_REPO}@{definition['image_digest']}", runner, sleep, monotonic)
    run_record = {"execution_name": execution, "args": list(run_args), "outcome": measured["outcome"], "start_time": measured["start_time"],
                  "completion_time": measured["completion_time"], "execution_wall_s": _wall_seconds(measured), "waited_s": round(waited, 3),
                  "executed_check": executed_check(execution, definition["image_digest"], request["reviewed_commit"], runner, fetch, run_args),
                  "report_status": None, "report_line": None}
    # G-5: the MEASURED effective wall (completionTime - startTime of this execution, certificate verifier included) against 0.75 x the task timeout; null when the wall was not read.
    # A whole-generation run is measured over the pinned class total: it is the SERIAL path's test (`verification_shards.py serial`); a shard's is the FALLBACK's.
    doc = (shard or {}).get("doc") or shards.load()[0]
    run_record["capacity"] = shards.shard_capacity(run_record["execution_wall_s"], len(shard["classes"]) if shard else doc["classes_total"], doc)
    try:
        line, report = read_report(execution, runner, sleep)
    except REFUSALS as exc:
        run_record["report_problem"] = str(exc)
    else:
        run_record.update(report_line=line, report_status=report.get("status") if isinstance(report.get("status"), str) else None,
                          report_sha256=hashlib.sha256(line.encode()).hexdigest())
        run_record["report_only"] = report.get("report_only") is True and report.get("status") == "REPORT_ONLY"
    # ok = the job ran to completion in report-only mode, as defined, and said so; whether its classes and gate are clean is the pack's dryrun_gate to judge
    run_record["ok"] = (run_record["outcome"] == "SUCCEEDED" and run_record["executed_check"]["status"] == "CONFORMS" and run_record.get("report_only") is True)
    return run_record


def run(argv=None, *, environ=None, runner=readback.default_runner, fetch=http_get, launcher=None, claim_dir=None, now=None, sleep=time.sleep, monotonic=time.monotonic) -> dict:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--generation", required=True)
    parser.add_argument("--dry-run", action="store_true", help="validate and print the plan; no claim, no launch")
    parser.add_argument("--shard", default=None, help="one shard id (V01..) of fleet/VERIFY_SHARDS.json; absent = the whole generation")
    args = parser.parse_args(argv)
    environ = os.environ if environ is None else environ
    now = now or dt.datetime.now(dt.timezone.utc)
    request, digest = bind_request(environ, args.generation, args.dry_run, args.shard)
    shard = None
    if args.shard is not None:
        try:
            doc, doc_sha = shards.load()      # the partition is the pinned file's, never the request's; an unknown or malformed one REFUSES before any cloud read
            shard = {"id": args.shard, "classes": shards.classes_for(args.shard, doc), "shards_sha256": doc_sha, "doc": doc}
        except shards.Refused as exc:
            raise Refused(str(exc)) from None
    definition = definition_check(request, runner, fetch)
    execute_args = build_job_args(shard and shard["classes"])
    record = {"schema": SCHEMA, "status": "DRY_RUN" if args.dry_run else "LAUNCH_PENDING", "mode": "dry_run" if args.dry_run else "execute",
              "operation_id": request["operation_id"], "item_id": request.get("item_id"), "request_sha256": digest, "reviewed_commit": request["reviewed_commit"],
              "chart_id": CHART, "generation": GENERATION, "project": readback.PROJECT, "region": readback.REGION, "job": JOB,
              "service_account": execchk.VERIFIER_SERVICE_ACCOUNT, "image_digest": definition["image_digest"], "definition_check": definition["status"],
              "args": list(execute_args), "shard": shard and {k: v for k, v in shard.items() if k != "doc"},
              "execution_name": None, "executed_check": None, "measured_at": now.isoformat(timespec="seconds"),
              "plan": {"execute": execute_argv(build_job_args(shard and shard["classes"], report_only=True) if args.dry_run else execute_args)}}
    if args.dry_run:
        record.update(args=list(build_job_args(shard and shard["classes"], report_only=True)),
                      report_only_run=report_only_run(definition, request, runner, fetch, launcher, sleep, monotonic, shard))
        return record
    root = environ.get("KY_ROOT")
    if not root and claim_dir is None:
        raise Refused("KY_ROOT is not set")
    claim_dir = Path(claim_dir or Path(root) / "run/ops/verification_launch")
    claim_dir.mkdir(parents=True, exist_ok=True)
    path = claim_dir / f"{request['operation_id']}.json"
    claim = {k: v for k, v in record.items() if k != "plan"}
    bridge._write_claim(path, claim, exclusive=True)                 # the cross-process no-retry fence; before any remote effect
    execution = (launcher or (lambda: cloud_launcher(runner, execute_args)))()
    if not isinstance(execution, str) or not EXECUTION.fullmatch(execution):
        raise Refused("remote execution identity absent or wrong job; retained claim requires reconciliation")
    claim.update(status="LAUNCHED", execution_name=execution)
    bridge._write_claim(path, claim)
    append_history(claim_dir, {**record, "execution_name": execution})
    record.update(status="LAUNCHED", execution_name=execution, executed_check=executed_check(execution, definition["image_digest"], request["reviewed_commit"], runner, fetch, execute_args))
    claim["executed_check"] = record["executed_check"]
    bridge._write_claim(path, claim)
    return record


def append_history(claim_dir: Path, record: dict) -> None:
    """The execution HISTORY (SR-A10-1 B3): one append-only line per launch in `<claim_dir>/HISTORY.jsonl` — operation, execution, shard (id, classes, pinned-file digest), reviewed
    commit (the head the job was defined at), image digest, request digest and time — fsynced. It is never rewritten: a re-run of a shard is a new line, so which execution attested
    which class at which head stays readable after the database rows are replaced. It records launches, not outcomes (the outcome is the execution read back and the attestations)."""
    line = bridge.canonical({"operation_id": record["operation_id"], "execution_name": record["execution_name"], "shard": record["shard"], "generation": record["generation"],
                             "reviewed_commit": record["reviewed_commit"], "image_digest": record["image_digest"], "request_sha256": record["request_sha256"],
                             "args": record["args"], "launched_at": record["measured_at"]})
    fd = os.open(claim_dir / "HISTORY.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o640)
    try:
        os.write(fd, (line + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def cli(argv=None, **injected):
    try:
        record = run(argv, **injected)
    except SystemExit as exc:
        return exc.code
    except BaseException as exc:
        reason = f": {exc}" if isinstance(exc, REFUSALS) else ""      # a refusal's message never repeats a credential; any other exception is named by class only
        print(f"verification launch failed ({type(exc).__name__}{reason}); reconcile retained evidence, never retry", file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 1
    ran = record.get("report_only_run")
    report_line = ran.pop("report_line", None) if ran else None
    print(bridge.canonical(record), flush=True)
    if report_line:
        print(report_line, flush=True)                  # the job's report, byte for byte, as the ONE report line of this output
    if ran is not None:
        return 0 if ran["ok"] else 1
    return 0 if record["executed_check"]["status"] == "CONFORMS" else 1


if __name__ == "__main__":
    raise SystemExit(cli())
