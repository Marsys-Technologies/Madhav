#!/usr/bin/env python3
"""operation_adapters.py — what every executor operation adapter shares (KV3-B-OPS-CONTRACT; relaunch plan v2.7 §6
REQUEST-PREP · PRE-ACCEPT · EXECUTE · POST-READBACK, §8, §14).

An adapter is the reviewed script a table entry of executor_ops.json names. The executor launches it (executor.py
`execute`: fixed_args, then the request's args as `--key value`) and writes the receipt. The fast lane prepares and accepts the request and independently judges the receipt digest. This module
changes none of that and enables nothing: it holds the parts each adapter would otherwise write again, and the reads
by which an item says whether its operation is complete. Importing it runs nothing; standard library only.

  the mode            add_mode_arguments / resolve_mode / parse_request_args — an explicit `--dry-run` and an explicit
                      `--execute`; omitting both defaults to a dry run
  the launch          launch_argv — the executor's argv for an entry and a request, as a statement to compare with
  the remote          remote_execute_argv / remote_launch — the one fixed build-job launch, its principal checked
                      first, planned identically in both modes and submitted in one
  the principal       run_identity / principal_refusal — a job definition's service account and secret NAMES against
                      the existing bindings; never a value, never a change to either
  no credential       remote_env / secret_refusal / emit — the allow-listed environment, and no credential value in
                      argv, a record or a job's output
  the dry run         dry_run_refusal / rehearse / scope_record — what a dry run must show before it counts
  completion          completion — receipt, the item's terminal observation and the verifier's verdict, together

A refusal is a `Refusal` (a code, and a reason that never repeats a credential); a function named `*_refusal` returns
the reason or None instead. Nothing here starts a process, opens a connection, reads a credential, writes under
run/ops, or touches the production fence (executor.py run/ops/PRODUCTION_PENDING.json: the owner surrogate's alone).

INTERPRETATIONS (what the packet leaves open, and what is done here):
  (I) INTERPRETATION A-1: The record an adapter prints (`ky.op_adapter/1`) is the adapter's OUTPUT — the body the executor stores as
       <operation_id>.output.txt and digests in its receipt. It is not a receipt and replaces no receipt field.
  (I) INTERPRETATION A-2: The build launch uses the fixed project/region, async flag and execution-name format of the current
       smalltest_launch.py cloud_launcher (Wave 4, #3527), independent of ambient gcloud defaults. The Gochara
       verifier has a principal binding here and no launch; whole-layer job bindings remain their items' prerequisites.
  (I) INTERPRETATION A-3: The principal check reads a job definition the adapter's transport fetched (`describe`): the metadata name, the
       one service account and the secret references by NAME, compared with data-plane-secret-isolation-preflight.ts's
       bindings (a test reads them from that file). A `run.googleapis.com/secrets` alias annotation, or a secret
       qualified by a project number, is not resolved here: it refuses.
  (I) INTERPRETATION A-4: The item's terminal observation is `ky.op_observation/1` {operation_id, request_sha256, receipt_sha256,
       terminal, outcome, source}: `terminal` true and `outcome` "succeeded" | "failed", read by the item from the
       remote or the database after the receipt, and bound to the ACTUAL receipt file's sha256. None is unknown.
  (I) INTERPRETATION A-5: A rehearsal's disposable lane database is one of local_db.sh's: host 127.0.0.1, database `ky_<name>`.
  (I) INTERPRETATION A-6: The executor appends `--key value` in the request's own key order, and the request digest (sorted keys) does
       not bind that order: an adapter reads its arguments by name, in any order, and nothing positional.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re

RECORD_SCHEMA = "ky.op_adapter/1"
OBSERVATION_SCHEMA = "ky.op_observation/1"
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
# executor.py, value for value (a test compares them)
CHILD_ENV_ALLOW = {"HOME", "PATH", "LANG", "LC_ALL", "TZ", "TMPDIR", "USER", "LOGNAME", "CLOUDSDK_CONFIG", "GOOGLE_APPLICATION_CREDENTIALS"}
SECRET_VALUE = [re.compile(r"postgres(?:ql)?://[^\s'\"]+", re.I), re.compile(r"(password|pgpassword|secret|token|apikey|api_key)\s*[=:]\s*\S+", re.I)]
# data-plane-secret-isolation-preflight.ts, name for name (a test reads that file): job → (service account, secret)
DEFAULT_PROJECT = "madhav-astrology"
BUILD_JOB = "brahma-build-pipeline-job"
VERIFIER_JOB = "gochara-verification-job"
JOB_BINDINGS = {BUILD_JOB: ("data-plane-builder-runtime", "data-plane-builder-db-url"),
                VERIFIER_JOB: ("gochara-verifier-runtime", "gochara-verifier-db-url")}
MODES = ("dry_run", "execute")
RUN_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")
HEX64 = re.compile(r"^[0-9a-f]{64}\Z")
LANE_HOST = "127.0.0.1"
LANE_DATABASE = re.compile(r"^ky_[a-z0-9_]+\Z")


class Refusal(Exception):
    """An adapter refuses: `code` is the class of refusal, the text the reason (never a credential value)."""

    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


# ───────────────────────────────────────── the mode and the arguments ─────────────────────────────────────────

def add_mode_arguments(parser):
    """`--dry-run` and `--execute`. They are not an argparse exclusive group: `resolve_mode` refuses the pair itself."""
    parser.add_argument("--dry-run", action="store_true", help="the DEFAULT: plan, measure and record; submit and write nothing")
    parser.add_argument("--execute", action="store_true", help="actually perform the operation; without it nothing is submitted")


def resolve_mode(dry_run=False, execute=False):
    """"dry_run" or "execute". Execution is only ever asked for explicitly; omitting both flags defaults to dry-run."""
    if not isinstance(dry_run, bool) or not isinstance(execute, bool):
        raise Refusal("mode", "the mode flags are not booleans")
    if dry_run and execute:
        raise Refusal("mode", "--dry-run and --execute were both given")
    return "execute" if execute else "dry_run"


def parse_request_args(argv, allowed, parser=None):
    """The executor's argv tail — the mode flags and `--key value` for the entry's allowed_args — read by name, in any
    order (A-6). A repeated, abbreviated, `=`-joined, unknown or positional token, or a missing value, refuses."""
    parser = parser or argparse.ArgumentParser()
    options = {"--" + name: name for name in allowed}
    seen, i, argv = set(), 0, list(argv)
    while i < len(argv):
        token = argv[i]
        if token in seen:
            raise Refusal("arguments", "%s is given twice" % token)
        if token in ("--dry-run", "--execute"):
            i += 1
        elif token in options:
            if i + 1 >= len(argv) or not isinstance(argv[i + 1], str) or argv[i + 1].startswith("-"):
                raise Refusal("arguments", "%s has no value" % token)
            i += 2
        else:
            raise Refusal("arguments", "an argument that is neither a mode flag nor one of %s" % sorted(options))
        seen.add(token)
    resolve_mode("--dry-run" in seen, "--execute" in seen)
    for option in sorted(options):
        try:
            parser.add_argument(option)
        except argparse.ArgumentError:
            pass                                             # the wrapper's parser already defines it
    try:
        return parser.parse_args(argv)
    except SystemExit:
        raise Refusal("arguments", "the wrapper's parser refused the arguments") from None


def launch_argv(entry, request, *, py, script_path):
    """executor.execute's argv for this entry and request: `py` is its interpreter, `script_path` where the script is
    when it runs (the operation worktree for a production kind, run/ops/tmp for a read-only one)."""
    args = list(entry.get("fixed_args", []))
    for key, value in (request.get("args") or {}).items():
        args += ["--" + key, str(value)]
    in_worktree = entry.get("production") or str(request.get("kind", "")).endswith("_dryrun")   # executor.execute: both run in the reviewed tree
    if in_worktree and entry.get("python_module"):
        return [py, "-m", entry["python_module"]] + args
    return ([py, script_path] if entry["script"].endswith(".py") else ["bash", script_path]) + args


# ───────────────────────────────────────── no credential value ─────────────────────────────────────────

def remote_env(environ=None):
    """The environment a remote CLI is started with: the executor's allow-list and nothing else — no connection."""
    environ = os.environ if environ is None else environ
    return {k: v for k, v in environ.items() if k in CHILD_ENV_ALLOW}


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for key, value in obj.items():
            yield from _strings(key)
            yield from _strings(value)
    elif isinstance(obj, (list, tuple, set)):
        for value in obj:
            yield from _strings(value)


def secret_refusal(obj):
    """A reason when a string anywhere in `obj` (an argv, a record, a request, a job's output) carries what the
    executor would redact; None otherwise. The reason counts; it never repeats."""
    found = sum(1 for text in _strings(obj) if any(rx.search(text) for rx in SECRET_VALUE))
    return "a credential value is present in %d string(s)" % found if found else None


def emit(record):
    """The record as the text an adapter prints, refused when a credential value is in it."""
    why = secret_refusal(record)
    if why:
        raise Refusal("secret_value", why)
    return json.dumps(record, indent=1, sort_keys=True)


# ───────────────────────────────────────── the runtime principal ─────────────────────────────────────────

def _secret_name(reference, project):
    full = re.match(r"^projects/([A-Za-z0-9-]+)/secrets/([^/:]+)(?::|/versions/.*)?$", reference)
    if full:                                                 # this project's secret is its bare name; another's stays qualified
        return full.group(2) if full.group(1) == project else "projects/%s/secrets/%s" % (full.group(1), full.group(2))
    resource = re.search(r"(?:^|/)secrets/([^/:]+)(?::|/versions/|$)", reference)
    if resource:
        return resource.group(1)
    short = re.match(r"^([A-Za-z0-9_-]+)(?::[^:]*)?$", reference)
    if short:
        return short.group(1)
    raise Refusal("principal", "a secret reference of the job definition is not a secret name")


def run_identity(definition, project=DEFAULT_PROJECT):
    """(service account, sorted secret names) of a Cloud Run job definition, as the secret-isolation preflight reads
    them. More than one service account, a reference without a name, or an alias annotation (A-3) refuses."""
    accounts, secrets = set(), set()

    def walk(value):
        if isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, dict):
            for key, child in value.items():
                if key in ("serviceAccountName", "serviceAccount") and isinstance(child, str) and "@" in child:
                    accounts.add(child)
                if key == "secretKeyRef" and isinstance(child, dict):
                    name = child.get("name") if isinstance(child.get("name"), str) else child.get("secret")
                    if not isinstance(name, str) or not name:
                        raise Refusal("principal", "a secretKeyRef of the job definition has no secret name")
                    secrets.add(_secret_name(name, project))
                elif key in ("secretName", "secret") and isinstance(child, str):
                    secrets.add(_secret_name(child, project))
                if key == "run.googleapis.com/secrets":
                    raise Refusal("principal", "the job definition maps secrets by alias; the alias is not resolved here")
                walk(child)

    walk(definition)
    if len(accounts) != 1:
        raise Refusal("principal", "the job definition names %d service accounts, not one" % len(accounts))
    return accounts.pop(), sorted(secrets)


def principal_refusal(job, definition, project=DEFAULT_PROJECT):
    """Why `definition` is not `job` under its existing binding (None when it is): the name, the one service account
    at `project`, and the one secret, each exactly. A job with no binding here has none to check against: it refuses."""
    if job not in JOB_BINDINGS:
        return "%r has no existing principal binding to compare with" % (job,)
    if not isinstance(definition, dict):
        return "the job definition could not be read"
    if secret_refusal(definition):
        return "the job definition carries a literal credential value"
    metadata = definition.get("metadata")
    if not isinstance(metadata, dict) or metadata.get("name") != job:
        return "the job definition is not %s's" % job
    try:
        account, secrets = run_identity(definition, project)
    except Refusal as refusal:
        return str(refusal)
    wanted_account, wanted_secret = JOB_BINDINGS[job]
    if account != "%s@%s.iam.gserviceaccount.com" % (wanted_account, project):
        return "%s runs as another principal than %s at %s" % (job, wanted_account, project)
    if secrets != [wanted_secret]:
        return "%s references %s, not the one secret %s" % (job, secrets or "no secret", wanted_secret)
    return None


# ───────────────────────────────────────── the one remote launch ─────────────────────────────────────────

def remote_execute_argv(job, run_id):
    """The launch of one staged run on the build job (A-2), and of nothing else."""
    if job != BUILD_JOB:
        raise Refusal("remote_target", "no launch of %r is stated; the only remote launch is %s's" % (job, BUILD_JOB))
    if not isinstance(run_id, str) or not RUN_ID.match(run_id):
        raise Refusal("run_id", "the run id is not one staged run's id")
    return ["gcloud", "run", "jobs", "execute", job, "--project=madhav-astrology", "--region=asia-south1",
            "--args=--run-id," + run_id, "--async", "--format=value(metadata.name)"]


def remote_launch(mode, run_id, transport, *, job=BUILD_JOB, project=DEFAULT_PROJECT, environ=None):
    """Plan the launch, check the job's principal, and — in "execute" only — hand the planned argv to the transport.

    `transport.describe(job)` returns the job's definition (a read); `transport.execute(argv, env)` submits and returns
    (exit code, output). The record states the same plan in both modes. `submit_exit` is the local command's exit and
    `remote_terminal` is always None: that a submission was taken says nothing of how the run ends (see `completion`)."""
    if mode not in MODES:
        raise Refusal("mode", "the mode is neither dry_run nor execute")
    if project != DEFAULT_PROJECT:
        raise Refusal("remote_target", "the launch project is fixed to the reviewed build job project")
    argv = remote_execute_argv(job, run_id)
    definition = transport.describe(job)
    why = principal_refusal(job, definition, project)
    if why:
        raise Refusal("principal", why)
    env = remote_env(environ)
    if secret_refusal(argv):
        raise Refusal("secret_value", "the planned argv carries a credential value")
    account, secrets = run_identity(definition, project)
    record = {"schema": RECORD_SCHEMA, "mode": mode, "job": job, "project": project, "principal": account, "secrets": secrets,
              "run_id": run_id, "planned_argv": argv, "env_names": sorted(env), "submitted": False, "submit_exit": None,
              "remote_terminal": None}
    if mode == "execute":
        code, _ = transport.execute(list(argv), dict(env))
        record["submitted"], record["submit_exit"] = True, code
    return record


# ───────────────────────────────────────── the dry run ─────────────────────────────────────────

def dry_run_refusal(record, *, submissions, before, after):
    """Why a dry run does not count (None when it does). The record says what the adapter claims; `submissions` is
    the transport's own count and `before` / `after` are fingerprints of the state the operation would change, taken
    by the caller around the run. A count or a fingerprint that was not taken is a refusal, not a zero."""
    if not isinstance(record, dict) or record.get("schema") != RECORD_SCHEMA or record.get("mode") != "dry_run":
        return "the record is not a dry run's"
    if record.get("submitted") is not False:
        return "the record does not say that nothing was submitted"
    if "planned_argv" in record and not (isinstance(record["planned_argv"], list) and record["planned_argv"]):
        return "the record plans no argv"
    if isinstance(submissions, bool) or not isinstance(submissions, int):
        return "what the transport submitted was not counted"
    if submissions != 0:
        return "the dry run submitted %d time(s)" % submissions
    if not isinstance(before, str) or not before or not isinstance(after, str) or not after:
        return "the state around the dry run was not measured"
    if before != after:
        return "the state changed across the dry run"
    return None


def _identity(identity):
    if (not isinstance(identity, dict) or not all(isinstance(identity.get(k), str) and HEX64.match(identity[k])
                                                  for k in ("script_sha256", "input_sha256"))):
        raise Refusal("identity", "the script and input sha256 the comparison is bound to are required")
    return {"script_sha256": identity["script_sha256"], "input_sha256": identity["input_sha256"]}


def _snapshot(conn, probes):
    out = {}
    for name in sorted(probes):
        cursor = conn.cursor()
        cursor.execute(probes[name])
        rows = [list(row) for row in cursor.fetchall()]
        out[name] = {"rows": len(rows), "sha256": _sha(rows)}
    return out


def rehearse(conn, statements, probes, head_probe, *, target, identity):
    """Run the operation's ACTUAL statements on a disposable lane database (A-5), roll back, and compare.

    `conn` is a DB-API connection the caller opened on `target` {host, database[, port]}; `statements` are the
    (sql, params) the execution would run; `probes` {name: SELECT} read the rows the operation touches and
    `head_probe` the published head. Each probe is read before, inside the open transaction and after the rollback, as
    a row count and a digest of the row values. The rehearsal counts only when the statements changed what a probe
    reads (otherwise nothing was rehearsed) and the rollback restored every probe; else it refuses. It never commits."""
    if (not isinstance(target, dict) or target.get("host") != LANE_HOST
            or not isinstance(target.get("database"), str) or not LANE_DATABASE.match(target["database"])):
        raise Refusal("lane_target", "the rehearsal target is not a disposable lane database (127.0.0.1, ky_<name>)")
    bound = _identity(identity)
    if (not isinstance(statements, (list, tuple)) or not statements or not isinstance(probes, dict) or not probes
            or "head" in probes or not all(isinstance(sql, str) and sql for sql in probes.values())
            or not isinstance(head_probe, str) or not head_probe):
        raise Refusal("rehearsal_scope", "statements, row probes and a separate head probe are all required")
    reads = dict(probes, head=head_probe)
    before = _snapshot(conn, reads)
    try:
        for sql, params in statements:
            conn.cursor().execute(sql, params)
    except Exception as exc:                                 # the class only: a driver's text can carry the connection
        raise Refusal("statement_failed", "a rehearsed statement failed (%s); rolled back" % type(exc).__name__) from None
    else:
        during = _snapshot(conn, reads)
    finally:
        conn.rollback()
    after = _snapshot(conn, reads)
    if after != before:
        raise Refusal("rollback_left_changes", "the probes differ after the rollback: %s"
                      % sorted(name for name in reads if after[name] != before[name]))
    if during == before:
        raise Refusal("no_observable_effect", "the statements changed nothing a probe reads; no rollback was rehearsed")
    return dict(bound, schema=RECORD_SCHEMA, mode="dry_run", submitted=False, rolled_back=True, target=dict(target),
                statements_sha256=_sha([[sql, list(params)] for sql, params in statements]), probes_sha256=_sha(reads),
                before=before, during=during, after=after)


def scope_record(mode, kind, *, scope, preflight, identity):
    """A dry run that can only measure its preflight and its scope (a backup, a restore): the record says so, and
    `restore_verified` is null — restore correctness is the item's restored scratch target, compared by content and
    count, never this."""
    if mode != "dry_run":
        raise Refusal("mode", "a scope record is a dry run's")
    if not isinstance(scope, dict) or not scope or not isinstance(preflight, dict) or not preflight:
        raise Refusal("rehearsal_scope", "the measured scope and preflight are both required")
    return dict(_identity(identity), schema=RECORD_SCHEMA, mode="dry_run", kind=kind, submitted=False, scope=scope,
                preflight=preflight, proves=["preflight", "scope"], restore_verified=None)


# ───────────────────────────────────────── completion ─────────────────────────────────────────

EVENT_KINDS = {"item", "decision", "heartbeat", "note", "metric", "message", "ack", "claim", "verdict"}


def _receipt(run, prepared):
    """Read the executor's wire receipt and measure its complete output without importing a retired job engine."""
    path = run / "ops" / "receipts" / (prepared["request"]["operation_id"] + ".json")
    try:
        body = path.read_bytes()
        doc = json.loads(body)
    except FileNotFoundError:
        return None, None, "incomplete", "no executor receipt"
    except (OSError, ValueError):
        return None, None, "unknown", "the executor receipt could not be read"
    if not isinstance(doc, dict):
        return None, None, "unknown", "the executor receipt could not be read"
    if doc.get("status") == "RUNNING":
        return None, None, "incomplete", "the executor receipt is RUNNING"
    valid = (doc.get("status") == "COMPLETED" and type(doc.get("exit_code")) is int and doc["exit_code"] == 0
             and doc.get("operation_id") == prepared["request"]["operation_id"]
             and doc.get("item_id") == prepared["item"] and doc.get("request_sha256") == prepared["request_sha256"])
    output, digest = doc.get("output_file"), doc.get("output_sha256")
    if valid and isinstance(output, str) and output and isinstance(digest, str) and HEX64.fullmatch(digest):
        out_path = pathlib.Path(output)
        if not out_path.is_absolute():
            out_path = path.parent / out_path
        try:
            measured = out_path.read_bytes()
            if measured and hashlib.sha256(measured).hexdigest() == digest:
                return doc, hashlib.sha256(body).hexdigest(), None, None
        except OSError:
            pass
    return None, None, "refused", "the executor receipt is not a COMPLETED, measured receipt of this request (status %r)" % doc.get("status")


def completion(run, prepared, events, observation):
    """(state, reason) of one prepared operation: "complete" only when all three hold —

      · the executor's receipt is COMPLETED and measured, for this request, item and operation (read directly from the executor wire format);
      · the item's terminal observation (A-4) is bound to the request and to that receipt file's sha256, is terminal
        and succeeded;
      · the latest artifact verdict at that same receipt sha256 is ACCEPTED (`events`: the item's tracker events).

    "incomplete": not there yet (no receipt, RUNNING, staged or still running, no verdict). "unknown": something that
    must be read was not (no observation, unreadable events or receipt). "failed": the observation is terminal and
    failed. "refused": evidence that is there and is not this operation's, or a verdict that is not ACCEPTED."""
    run = pathlib.Path(str(run))
    request = prepared["request"]
    _, receipt_sha, state, reason = _receipt(run, prepared)
    if state:
        return state, reason
    if observation is None:
        return "unknown", "no terminal semantic observation of this operation"
    if not isinstance(observation, dict) or observation.get("schema") != OBSERVATION_SCHEMA:
        return "refused", "the observation is not a %s record" % OBSERVATION_SCHEMA
    if (observation.get("operation_id") != request["operation_id"] or observation.get("request_sha256") != prepared["request_sha256"]
            or observation.get("receipt_sha256") != receipt_sha):
        return "refused", "the observation is of another operation, request or receipt"
    if observation.get("terminal") is False:
        return "incomplete", "the operation is observed and not terminal"
    if observation.get("terminal") is not True or observation.get("outcome") not in ("succeeded", "failed"):
        return "refused", "the observation states no terminal outcome"
    if observation["outcome"] == "failed":
        return "failed", "the operation is observed terminal and failed"
    if not isinstance(events, list) or not all(isinstance(e, dict) and e.get("kind") in EVENT_KINDS for e in events):
        return "unknown", "the item's events could not be read"
    verdicts = [e for e in events if e.get("kind") == "verdict" and e.get("item") == prepared["item"]
                and e.get("phase") == "artifact" and e.get("artifact_digest") == receipt_sha]
    if not verdicts:
        return "incomplete", "no artifact verdict at the receipt's sha256"
    if verdicts[-1].get("result") != "ACCEPTED":
        return "refused", "the latest artifact verdict at the receipt's sha256 is %r" % (verdicts[-1].get("result"),)
    return "complete", None
