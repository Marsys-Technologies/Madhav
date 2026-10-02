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

SCHEMA = "seal_execution_envelope/1"
ENV_COMMIT = "GOCHARA_RUNNER_COMMIT"
ENV_IMAGE = "GOCHARA_RUNNER_IMAGE_DIGEST"
ENV_SECRET = "GOCHARA_VERIFIER_DB_URL"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_SHA = re.compile(r"[0-9a-f]{40}")


class Refused(Exception):
    pass


def _task_spec(ex: dict) -> dict:
    spec = (ex.get("spec") or {})
    t = (spec.get("template") or {}).get("spec") or {}
    if "containers" not in t:
        t = (t.get("template") or {}).get("spec") or {}                    # a Job-style nesting
    if "containers" not in t:
        raise Refused("the execution carries no container specification (unexpected resource shape)")
    return t


def _conds(ex: dict) -> dict:
    return {c.get("type"): c.get("status") for c in ((ex.get("status") or {}).get("conditions") or []) if isinstance(c, dict)}


def state(ex: dict) -> str:
    st = ex.get("status") or {}
    c = _conds(ex)
    if c.get("Completed") == "True" and int(st.get("succeededCount") or 0) >= 1 and int(st.get("failedCount") or 0) == 0:
        return "SUCCEEDED"
    if c.get("Completed") == "False" or int(st.get("failedCount") or 0) > 0 or int(st.get("cancelledCount") or 0) > 0:
        return "FAILED"
    return "RUNNING"


def check(ex, *, execution_name: str, image_digest: str, service_account: str, runner_commit: str, args: list, secret_name: str) -> dict:
    if not isinstance(ex, dict):
        raise Refused("the execution description is not a JSON object")
    if not _DIGEST.fullmatch(image_digest or ""):
        raise Refused("the expected image digest is not sha256:<64-hex>")
    if not _SHA.fullmatch(runner_commit or ""):
        raise Refused("the expected runner commit is not a 40-hex revision")
    if (ex.get("metadata") or {}).get("name") != execution_name:
        raise Refused(f"this is execution {(ex.get('metadata') or {}).get('name')!r}, not {execution_name!r}")
    t = _task_spec(ex)
    cs = t.get("containers") or []
    if len(cs) != 1:
        raise Refused(f"the execution has {len(cs)} containers, not exactly one")
    c = cs[0]
    image = c.get("image") or ""
    if not image.endswith("@" + image_digest) or "@" not in image:
        raise Refused(f"the execution ran image {image!r}, not an image pinned to the digest {image_digest} deployed for this commit (a tag is mutable and is refused)")
    if t.get("serviceAccountName") != service_account:
        raise Refused(f"the execution ran as {t.get('serviceAccountName')!r}, not {service_account!r}")
    env = c.get("env") or []
    secrets = [e for e in env if isinstance(e, dict) and "secretKeyRef" in ((e.get("valueFrom") or {}))]
    if [e.get("name") for e in secrets] != [ENV_SECRET] or ((secrets[0].get("valueFrom") or {}).get("secretKeyRef") or {}).get("name") != secret_name:
        raise Refused(f"the execution's secret bindings are not exactly {ENV_SECRET} <- {secret_name}")
    commits = [e for e in env if isinstance(e, dict) and e.get("name") == ENV_COMMIT]
    if len(commits) != 1 or commits[0].get("value") != runner_commit:
        raise Refused(f"the execution's {ENV_COMMIT} is not exactly the sealing commit {runner_commit}")
    images = [e for e in env if isinstance(e, dict) and e.get("name") == ENV_IMAGE]
    if len(images) != 1 or images[0].get("value") != image_digest:
        raise Refused(f"the execution's {ENV_IMAGE} is not exactly the immutable digest {image_digest} (the verifier records it as its producer identity)")
    if list(c.get("args") or []) != list(args):
        raise Refused("the execution's arguments are not exactly the ones this workflow passed")
    if int(t.get("maxRetries") if t.get("maxRetries") is not None else 0) != 0:
        raise Refused("the execution allowed task retries (a retried task could have produced a stale brief)")
    if int((ex.get("spec") or {}).get("taskCount") or 1) != 1:
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


def check_envelope(env, *, run_id: str, attempt: str, sealing_commit: str, brief_digest: str, brief_id: str) -> dict:
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
    return env


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("state")
    st.add_argument("--execution-file", required=True)
    ji = sub.add_parser("job-image")
    ji.add_argument("--job-file", required=True)
    ji.add_argument("--image-digest", required=True)
    ji.add_argument("--service-account", required=True)
    ce = sub.add_parser("check-envelope")
    ce.add_argument("--envelope-file", required=True)
    ce.add_argument("--compact-file", required=True)
    ce.add_argument("--run-id", required=True)
    ce.add_argument("--attempt", required=True)
    ce.add_argument("--sealing-commit", required=True)
    ce.add_argument("--brief-digest", required=True)
    bv = sub.add_parser("build-envelope")
    bv.add_argument("--execution-file", required=True)
    bv.add_argument("--compact-file", required=True)
    bv.add_argument("--execution-name", required=True)
    bv.add_argument("--image-digest", required=True)
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
            with open(a.job_file, encoding="utf-8") as f:
                job = json.load(f)
            t = _task_spec(job)
            image = ((t.get("containers") or [{}])[0].get("image")) or ""
            if not _DIGEST.fullmatch(a.image_digest) or not image.endswith("@" + a.image_digest):
                raise Refused(f"the verification job is defined with image {image!r}, not the digest {a.image_digest} deployed for this commit: re-dispatch the job-definition workflow at this commit (same-commit rule)")
            if t.get("serviceAccountName") != a.service_account:
                raise Refused(f"the verification job runs as {t.get('serviceAccountName')!r}, not {a.service_account!r}")
            envs = [e for e in ((t.get("containers") or [{}])[0].get("env") or []) if isinstance(e, dict) and e.get("name") == ENV_IMAGE]
            if len(envs) != 1 or envs[0].get("value") != a.image_digest:
                raise Refused(f"the verification job does not carry {ENV_IMAGE} = {a.image_digest}: it would refuse to brief (producer_identity_absent); re-dispatch #2976 at this commit")
            print("OK")
            return 0
        if a.cmd == "check-envelope":
            with open(a.envelope_file, encoding="utf-8") as f:
                envelope = json.load(f)
            with open(a.compact_file, encoding="utf-8") as f:
                brief_id = ((json.load(f) or {}).get("persisted") or {}).get("brief_id")
            check_envelope(envelope, run_id=a.run_id, attempt=a.attempt, sealing_commit=a.sealing_commit, brief_digest=a.brief_digest, brief_id=str(brief_id))
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
        verified = check(ex, execution_name=a.execution_name, image_digest=a.image_digest, service_account=a.service_account, runner_commit=a.sealing_commit,
                         args=json.loads(a.args_json), secret_name=a.secret_name)
        if compact.get("sha256") != a.brief_digest:
            raise Refused("the compact result's digest is not the checked brief's digest")
        producer = (compact or {}).get("producer") or {}
        bind_producer(verified, producer, execution_name=a.execution_name, sealing_commit=a.sealing_commit)
        env = build_envelope(verified, run_id=a.run_id, attempt=a.attempt, sealing_commit=a.sealing_commit, brief_digest=a.brief_digest, brief_id=per.get("brief_id"),
                             producer_execution_id=producer["execution_id"])
    except (Refused, OSError, ValueError, TypeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(env, f, sort_keys=True)
    print(f"execution {env['execution']} image {env['image_digest']} brief {env['brief_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
