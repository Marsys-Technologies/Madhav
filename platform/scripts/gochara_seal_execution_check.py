#!/usr/bin/env python3
"""Verify the EXECUTED Cloud Run resource — not a job name (R13-3) — and build the retained envelope the approval and the seal are bound to.

Input: `gcloud run jobs executions describe <execution> --format=json` (the execution that produced the brief), plus what this workflow run EXPECTS: the immutable image digest the verification
job was deployed with for THIS commit (resolved from the registry by the workflow), the sealing commit, the runtime service account, the exact arguments the workflow passed, and the one secret
binding. It refuses unless the execution (a) is the named execution, (b) ran image `…@sha256:<that digest>` (a tag is mutable and is refused), (c) ran as the verifier service account,
(d) carried `GOCHARA_RUNNER_COMMIT == the sealing commit` as a plain value, (e) received exactly the expected arguments, (f) bound exactly one secret, `GOCHARA_VERIFIER_DB_URL` from the verifier secret
(a different or extra secret means another identity ran it), (g) had one task, no retries (a retried task could have produced a stale brief), and (h) completed successfully with one succeeded task.
It does NOT treat log labels or resource fields as producer attestation (Cloud Logging does not authenticate who wrote an entry; a principal with `logging.logEntries.create` can set them): the
producer is established by the EXECUTION RESOURCE read here, the persisted `brief_id` (database-attested `produced_by`) and the digest, never by what a log line claims about itself.

`build-envelope` then writes `seal_execution_envelope/1`: execution, image digest, service account, runner commit, args, run id, attempt, sealing commit, brief digest and persisted brief id.
It is retained under a name carrying run id + attempt and re-checked by the gated job against ITS OWN run/attempt/commit and the brief it is about to approve. The execution's JSON shape is
the documented Execution resource (`spec.template.spec` = the task template; a Job-style nesting is also accepted); the FIRST real execution is the proof of that shape.
Exit 0 ok / 2 refused (reason on stderr). `state` prints RUNNING / SUCCEEDED / FAILED for the wait loop."""
from __future__ import annotations

import argparse
import json
import re
import sys

from gochara_verification_job_readback import Refused as DefinitionRefused, strict_v2_retries

SCHEMA = "seal_execution_envelope/1"
ENV_COMMIT = "GOCHARA_RUNNER_COMMIT"
ENV_IMAGE = "GOCHARA_RUNNER_IMAGE_DIGEST"
ENV_SECRET = "GOCHARA_VERIFIER_DB_URL"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_SHA = re.compile(r"[0-9a-f]{40}")


class Refused(Exception):
    pass


# The deployed job's resources (#2976 deploys exactly these); the executed resource and the pre-execution definition read are judged against them by VALUE through the shared contract
# (int64 `timeoutSeconds` arrives as a decimal string; quantities in any equivalent spelling).
JOB_TIMEOUT_SECONDS, JOB_MEMORY, JOB_CPU = 28800, "4Gi", "1"      # SR-RIGHT-SIZE amend-1: was "8Gi", "2"; the timeout is unchanged
VERIFIER_SERVICE_ACCOUNT = "gochara-verifier-runtime@madhav-astrology.iam.gserviceaccount.com"


def _task_spec(ex: dict) -> dict:
    spec = (ex.get("spec") or {})
    t = (spec.get("template") or {}).get("spec") or {}
    if "containers" not in t:
        t = (t.get("template") or {}).get("spec") or {}                    # a Job-style nesting
    if "containers" not in t:
        raise Refused("the execution carries no container specification (unexpected resource shape)")
    return t


def _conds(ex: dict) -> dict | None:
    conditions = (ex.get("status") or {}).get("conditions", [])
    if not isinstance(conditions, list):
        return None
    result = {}
    for condition in conditions:
        if not isinstance(condition, dict):
            return None
        name = condition.get("type")
        if not isinstance(name, str) or not name or name in result:
            return None                   # duplicates cannot be resolved by API array order
        result[name] = condition.get("status")
    return result


def state(ex: dict) -> str:
    st = ex.get("status") or {}
    c = _conds(ex)
    if c is None:
        return "FAILED"                   # malformed/ambiguous evidence never authorizes an envelope
    import gochara_verification_job_contract as vjc
    n = lambda k: vjc.parse_int64(st.get(k)) if st.get(k) is not None else 0               # noqa: E731 — int32/int64 counts: number or canonical decimal string
    if None in (n("succeededCount"), n("failedCount"), n("cancelledCount")):
        return "FAILED"                                                                  # an unparseable count is never read as zero
    if n("failedCount") > 0 or n("cancelledCount") > 0 or n("succeededCount") > 1:
        return "FAILED"
    if c.get("Completed") == "True" and n("succeededCount") == 1 and n("failedCount") == 0:
        return "SUCCEEDED"
    if c.get("Completed") == "False" or n("failedCount") > 0 or n("cancelledCount") > 0:
        return "FAILED"
    return "RUNNING"


def check(ex, *, execution_name: str, image_repo: str, image_digest: str, service_account: str, runner_commit: str, args: list, secret_name: str, v2_execution=None) -> dict:
    """The EXECUTED resource is judged by the SAME strict contract as the deployed definition (R14-3: `gochara_verification_job_contract.validate_task`, shared byte for byte with
    #2976's readback): exact image@digest, exact command (the builder entry point may not be swapped back), exact args, `maxRetries` PRESENT and 0, exact environment, no volumes /
    volumeMounts / envFrom / unexpected fields, exact service account."""
    import gochara_verification_job_contract as vjc
    if not isinstance(ex, dict):
        raise Refused("the execution description is not a JSON object")
    if not _DIGEST.fullmatch(image_digest or ""):
        raise Refused("the expected image digest is not sha256:<64-hex>")
    if not _SHA.fullmatch(runner_commit or ""):
        raise Refused("the expected runner commit is not a 40-hex revision")
    if (ex.get("metadata") or {}).get("name") != execution_name:
        raise Refused(f"this is execution {(ex.get('metadata') or {}).get('name')!r}, not {execution_name!r}")
    t = _task_spec(ex)
    v2 = vjc.UNSET if v2_execution is None else strict_v2_retries(v2_execution, 'execution')       # the presence-bearing v2 read of maxRetries (F-R15-3); absent in BOTH ⇒ refusal
    bad = vjc.forbidden_annotations(ex, v2_execution) + vjc.validate_task(t, image_repo=image_repo, image_digest=image_digest, service_account=service_account, runner_commit=runner_commit, secret_name=secret_name, expected_args=list(args), timeout_seconds=JOB_TIMEOUT_SECONDS, memory=JOB_MEMORY, cpu=JOB_CPU, v2_retries=v2)
    if bad:
        raise Refused("the executed resource does not conform to the verification-job contract: " + "; ".join(bad))
    tc = (ex.get("spec") or {}).get("taskCount")
    if (vjc.parse_int64(tc) if tc is not None else 1) != 1:
        raise Refused("the execution has more than one task")
    if state(ex) != "SUCCEEDED":
        raise Refused(f"the execution is {state(ex)}, not SUCCEEDED")
    return {"execution": execution_name, "image_digest": image_digest, "service_account": service_account, "runner_commit": runner_commit, "args": list(args)}


def _execution_matches(producer_id: str, execution_name: str) -> bool:
    """`CLOUD_RUN_EXECUTION` is the execution's NAME; the long resource-path form `…/executions/<name>` is accepted as the same execution. (The golden fixture's long form is documentation-built;
    the first real execution settles which form Cloud Run prints.)"""
    return producer_id == execution_name or producer_id.endswith("/executions/" + execution_name)


def bind_producer(verified: dict, producer: dict, *, execution_name: str, sealing_commit: str) -> None:
    """The brief's PRODUCER (from the compact line the verifier printed) must be the very resource this workflow read: the executed image digest, the execution id and the commit (ST-WIRE-2)."""
    if producer.get("image_digest") != verified["image_digest"]:
        raise Refused("the compact line's producer image digest is not the executed resource's image digest")
    if not _execution_matches(str(producer.get("execution_id")), execution_name):
        raise Refused("the compact line's producer execution id is not the execution this workflow started and read")
    if producer.get("commit") != sealing_commit or verified["runner_commit"] != sealing_commit:
        raise Refused("the compact line's producer commit is not the sealing commit")


def build_envelope(verified: dict, *, run_id: str, attempt: str, sealing_commit: str, brief_digest: str, brief_id: int, producer_execution_id: str) -> dict:
    return {"schema": SCHEMA, **verified, "run_id": int(run_id), "run_attempt": int(attempt), "sealing_commit": sealing_commit, "brief_digest": brief_digest, "brief_id": int(brief_id),
            "producer_execution_id": producer_execution_id}


def check_envelope(env, *, run_id: str, attempt: str, sealing_commit: str, brief_digest: str, brief_id: str, expected_args: list | None = None) -> dict:
    """The gated job's re-check: the retained envelope is for THIS run, THIS attempt, THIS commit and THIS brief (digest and persisted id)."""
    keys = {"schema", "execution", "image_digest", "service_account", "runner_commit", "args", "run_id", "run_attempt", "sealing_commit", "brief_digest", "brief_id", "producer_execution_id"}
    if not isinstance(env, dict) or set(env) != keys or env["schema"] != SCHEMA:
        raise Refused("the retained envelope is not a seal_execution_envelope/1")
    for k, want in (("run_id", int(run_id)), ("run_attempt", int(attempt))):
        if env[k] != want or isinstance(env[k], bool):
            raise Refused(f"the envelope is for {k} {env[k]!r}, this is {want}: a brief of another run or attempt is never reused")
    if env["sealing_commit"] != sealing_commit or env["runner_commit"] != sealing_commit:
        raise Refused("the envelope's sealing/runner commit is not this workflow's reviewed revision")
    if env["brief_digest"] != brief_digest:
        raise Refused("the envelope's brief digest is not the digest of the retained brief")
    if isinstance(env["brief_id"], bool) or env["brief_id"] != int(brief_id):
        raise Refused("the envelope's persisted brief id is not the retained brief's")
    if not _DIGEST.fullmatch(env["image_digest"] or "") or not env["execution"]:
        raise Refused("the envelope carries no image digest / execution id")
    if not isinstance(env["producer_execution_id"], str) or not _execution_matches(env["producer_execution_id"], env["execution"]):
        raise Refused("the envelope's producer execution id is not the execution it records")
    if env["service_account"] != VERIFIER_SERVICE_ACCOUNT:
        raise Refused("the envelope's service account is not the verifier runtime")
    if expected_args is not None and env["args"] != expected_args:
        raise Refused("the envelope's args are not this full candidate's brief invocation")
    return env


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("state")
    st.add_argument("--execution-file", required=True)
    ji = sub.add_parser("job-image")
    ji.add_argument("--job-file", required=True)
    ji.add_argument("--image-digest", required=True)
    ji.add_argument("--image-repo", required=True)
    ji.add_argument("--runner-commit", required=True)
    ji.add_argument("--secret-name", required=True)
    ji.add_argument("--v2-job-file", default=None, help="the v2 REST `jobs.get` JSON — the presence-bearing source of maxRetries")
    ji.add_argument("--service-account", required=True)
    ji.add_argument("--cloudsql-instance", default=None)
    ce = sub.add_parser("check-envelope")
    ce.add_argument("--envelope-file", required=True)
    ce.add_argument("--compact-file", required=True)
    ce.add_argument("--run-id", required=True)
    ce.add_argument("--attempt", required=True)
    ce.add_argument("--sealing-commit", required=True)
    ce.add_argument("--brief-digest", required=True)
    ce.add_argument("--chart-id", default=None)
    ce.add_argument("--generation", default=None)
    bv = sub.add_parser("build-envelope")
    bv.add_argument("--execution-file", required=True)
    bv.add_argument("--compact-file", required=True)
    bv.add_argument("--execution-name", required=True)
    bv.add_argument("--image-digest", required=True)
    bv.add_argument("--image-repo", required=True)
    bv.add_argument("--v2-execution-file", default=None, help="the v2 REST `executions.get` JSON — the presence-bearing source of maxRetries")
    bv.add_argument("--service-account", required=True)
    bv.add_argument("--secret-name", required=True)
    bv.add_argument("--args-json", required=True, help="the JSON array of the exact arguments the workflow passed")
    bv.add_argument("--run-id", required=True)
    bv.add_argument("--attempt", required=True)
    bv.add_argument("--sealing-commit", required=True)
    bv.add_argument("--brief-digest", required=True)
    bv.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "job-image":
            import gochara_verification_job_contract as vjc
            with open(a.job_file, encoding="utf-8") as f:
                job = json.load(f)
            if not isinstance(job, dict) or (job.get("metadata") or {}).get("name") != "gochara-verification-job":
                raise Refused("the definition is not the named verification job")
            from gochara_verification_job_readback import _shape, check as definition_check
            ets, _, _ = _shape(job)
            if (vjc.parse_int64(ets.get("taskCount")) if ets.get("taskCount") is not None else 1) != 1:
                raise Refused("the verification definition taskCount is not 1")
            v2 = vjc.UNSET
            v2_doc = None
            if a.v2_job_file:
                with open(a.v2_job_file, encoding="utf-8") as f:
                    v2_doc = json.load(f)
                if not isinstance(v2_doc, dict):
                    raise Refused("the supplied v2 job file is not a JSON object (not an absent read)")
                v2 = strict_v2_retries(v2_doc, "job")
            if a.cloudsql_instance is not None:
                bad = definition_check(job, v2_job=v2_doc, image_repo=a.image_repo, image_digest=a.image_digest,
                                       service_account=a.service_account, runner_commit=a.runner_commit, secret_name=a.secret_name,
                                       cloudsql_instance=a.cloudsql_instance, timeout_seconds=JOB_TIMEOUT_SECONDS, memory=JOB_MEMORY, cpu=JOB_CPU)
                if bad:
                    raise Refused("the verification definition does not conform: " + "; ".join(bad))
            bad = vjc.forbidden_annotations(job, v2_doc) + vjc.validate_task(_task_spec(job), image_repo=a.image_repo, image_digest=a.image_digest, service_account=a.service_account, runner_commit=a.runner_commit,
                                    secret_name=a.secret_name, expected_args=[], timeout_seconds=JOB_TIMEOUT_SECONDS, memory=JOB_MEMORY, cpu=JOB_CPU, v2_retries=v2)
            if bad:
                raise Refused("the verification job's DEFINITION does not conform to the contract (re-dispatch #2976 at this commit — same-commit rule): " + "; ".join(bad))
            print("OK")
            return 0
        if a.cmd == "check-envelope":
            with open(a.envelope_file, encoding="utf-8") as f:
                envelope = json.load(f)
            with open(a.compact_file, encoding="utf-8") as f:
                brief_id = ((json.load(f) or {}).get("persisted") or {}).get("brief_id")
            if (a.chart_id is None) != (a.generation is None):
                raise Refused("chart-id and generation must be supplied together")
            expected_args = (["--chart", a.chart_id, "--generation", a.generation, "--brief", "--sealing-commit", a.sealing_commit]
                             if a.chart_id is not None else None)
            check_envelope(envelope, run_id=a.run_id, attempt=a.attempt, sealing_commit=a.sealing_commit, brief_digest=a.brief_digest, brief_id=str(brief_id), expected_args=expected_args)
            print(brief_id, envelope["producer_execution_id"])
            return 0
        with open(a.execution_file, encoding="utf-8") as f:
            ex = json.load(f)
        if a.cmd == "state":
            print(state(ex))
            return 0
        with open(a.compact_file, encoding="utf-8") as f:
            compact = json.load(f)
        per = (compact or {}).get("persisted") or {}
        v2_execution = None
        if a.v2_execution_file:
            with open(a.v2_execution_file, encoding="utf-8") as f:
                v2_execution = json.load(f)
            if not isinstance(v2_execution, dict):
                raise Refused("the supplied v2 execution file is not a JSON object (not an absent read)")
        verified = check(ex, execution_name=a.execution_name, image_repo=a.image_repo, image_digest=a.image_digest, service_account=a.service_account, runner_commit=a.sealing_commit,
                         args=json.loads(a.args_json), secret_name=a.secret_name, v2_execution=v2_execution)
        if compact.get("sha256") != a.brief_digest:
            raise Refused("the compact result's digest is not the checked brief's digest")
        producer = (compact or {}).get("producer") or {}
        bind_producer(verified, producer, execution_name=a.execution_name, sealing_commit=a.sealing_commit)
        env = build_envelope(verified, run_id=a.run_id, attempt=a.attempt, sealing_commit=a.sealing_commit, brief_digest=a.brief_digest, brief_id=per.get("brief_id"),
                             producer_execution_id=producer["execution_id"])
    except (Refused, DefinitionRefused, OSError, ValueError, TypeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(env, f, sort_keys=True)
    print(f"execution {env['execution']} image {env['image_digest']} brief {env['brief_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
