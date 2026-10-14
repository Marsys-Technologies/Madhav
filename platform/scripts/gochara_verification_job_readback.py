#!/usr/bin/env python3
"""Complete READBACK of the deployed `gochara-verification-job` definition (Codex R13-3; #2976).

Input: `gcloud run jobs describe gochara-verification-job --format=json`. It refuses unless the DEFINITION is exactly what act 6 specifies — not merely "the image tag looks right":
  image            == <repository>@<the immutable sha256 digest the registry holds for this commit> (a tag is mutable and is refused)
  service account  == the verifier's runtime account
  command / args   == `python -m pipeline.orchestrator.verification_job` / none (an operator supplies the flags at execute time)
  environment      == exactly GOCHARA_RUNNER_COMMIT (the deployed commit, as a plain value), GOCHARA_RUNNER_IMAGE_DIGEST (the immutable digest, as a plain value — ST-WIRE-2) and
                      GOCHARA_VERIFIER_DB_URL (a secret reference to the verifier secret) — nothing else
  Cloud SQL        == exactly the one instance, in the job's `run.googleapis.com/cloudsql-instances` annotation
  tasks / retries  == one task, no retries (a retried task could produce a stale brief); timeout, memory and CPU as deployed
A failed check leaves the deployed definition in place to INSPECT or REMOVE (`gcloud run jobs delete`); this script never rolls anything back. The JSON shape is the documented Job resource
(`spec.template` = the execution template, whose `spec` carries the task count and whose `spec.template.spec` the task): the first real deployment is the proof of that shape, and an
unexpected shape is a refusal, never a pass.
Exit 0 ok / 2 refused (every reason on stderr)."""
from __future__ import annotations

import argparse
import json
import re
import sys

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_SHA = re.compile(r"[0-9a-f]{40}")


class Refused(Exception):
    pass


def _dig(d, *path):
    for k in path:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _shape(job: dict):
    """(execution-template spec, task spec, annotations) — the documented nesting; a missing level is a refusal."""
    et = _dig(job, "spec", "template")
    ets = (et or {}).get("spec") if isinstance(et, dict) else None
    task = _dig(ets, "template", "spec") if isinstance(ets, dict) else None
    if not isinstance(task, dict) or "containers" not in task:
        raise Refused("unexpected Job resource shape: no spec.template.spec.template.spec.containers")
    ann = {}
    for src in (_dig(et, "metadata", "annotations"), _dig(ets, "template", "metadata", "annotations"), _dig(job, "metadata", "annotations")):
        if isinstance(src, dict):
            ann.update(src)
    return ets, task, ann


def check(job, *, image_repo: str, image_digest: str, service_account: str, runner_commit: str, secret_name: str, cloudsql_instance: str,
          timeout_seconds: int, memory: str, cpu: str, v2_job=None) -> list[str]:
    """The task template is judged by the SAME strict contract as the executed resource (`gochara_verification_job_contract.validate_task`, shared byte for byte with #2975's executed-resource
    check — R14-3); only the JOB-LEVEL facts (Cloud SQL instance, task count) are checked here."""
    import gochara_verification_job_contract as vjc
    if not isinstance(job, dict):
        raise Refused("the job description is not a JSON object")
    if not _DIGEST.fullmatch(image_digest or "") or not _SHA.fullmatch(runner_commit or ""):
        raise Refused("the expected image digest / runner commit are malformed")
    ets, task, ann = _shape(job)
    v2 = vjc.UNSET if v2_job is None else vjc.retries_from_v2(v2_job, "job")          # maxRetries from the presence-bearing v2 REST representation (F-R15-3); absent in BOTH ⇒ refusal
    bad = vjc.forbidden_annotations(job, v2_job) + vjc.validate_task(task, image_repo=image_repo, image_digest=image_digest, service_account=service_account, runner_commit=runner_commit, secret_name=secret_name,
                            expected_args=[], timeout_seconds=timeout_seconds, memory=memory, cpu=cpu, v2_retries=v2)
    if ann.get("run.googleapis.com/cloudsql-instances") != cloudsql_instance:
        bad.append(f"Cloud SQL instances annotation is {ann.get('run.googleapis.com/cloudsql-instances')!r}, expected exactly {cloudsql_instance!r}")
    if (vjc.parse_int64(ets.get("taskCount")) if ets.get("taskCount") is not None else 1) != 1:           # int32/int64: number or canonical decimal string
        bad.append("taskCount is not 1")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job-file", required=True)
    ap.add_argument("--image-repo", required=True)
    ap.add_argument("--image-digest", required=True)
    ap.add_argument("--service-account", required=True)
    ap.add_argument("--runner-commit", required=True)
    ap.add_argument("--secret-name", required=True)
    ap.add_argument("--cloudsql-instance", required=True)
    ap.add_argument("--timeout-seconds", type=int, required=True)
    ap.add_argument("--memory", required=True)
    ap.add_argument("--cpu", required=True)
    ap.add_argument("--v2-job-file", default=None, help="the v2 REST jobs.get JSON — the presence-bearing source of maxRetries")
    a = ap.parse_args(argv)
    try:
        with open(a.job_file, encoding="utf-8") as f:
            job = json.load(f)
        v2_job = None
        if a.v2_job_file:
            with open(a.v2_job_file, encoding="utf-8") as f:
                v2_job = json.load(f)
        bad = check(job, v2_job=v2_job, image_repo=a.image_repo, image_digest=a.image_digest, service_account=a.service_account, runner_commit=a.runner_commit, secret_name=a.secret_name,
                    cloudsql_instance=a.cloudsql_instance, timeout_seconds=a.timeout_seconds, memory=a.memory, cpu=a.cpu)
    except (Refused, OSError, ValueError, TypeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    if bad:
        for b in bad:
            print(f"REFUSED: {b}", file=sys.stderr)
        return 2
    print(f"verification job definition verified: image {a.image_repo}@{a.image_digest}; identity {a.service_account}; one secret; one Cloud SQL instance; one task, no retries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
