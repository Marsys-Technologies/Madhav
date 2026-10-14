#!/usr/bin/env python3
"""Read-only validation of the P08 verifier definition, before and after execution.

Both workflows use the pinned verification-job task contract. Deployment never
executes the job or enables a fleet operation. A failed readback leaves the
remote definition for the controller to inspect; it never claims rollback.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import gochara_verification_job_contract as vjc

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
_SHA = re.compile(r"[0-9a-f]{40}")
_SQL_ANNOTATION = "run.googleapis.com/cloudsql-instances"


class Refused(Exception):
    pass


def _dig(document, *path):
    for key in path:
        if not isinstance(document, dict):
            return None
        document = document.get(key)
    return document


def strict_v2_retries(document, kind):
    """Preserve the pinned parser; refuse explicit null at the serving boundary.

    Missing fields are absent. Present null templates or retry values are
    malformed input, and cannot be rescued by a valid zero in another read.
    """
    current = document
    path = ("template", "template", "maxRetries") if kind == "job" else ("template", "maxRetries")
    if current is None:
        return None
    for key in path:
        if not isinstance(current, dict):
            return vjc.INVALID
        if key not in current:
            return None
        current = current[key]
        if current is None:
            return vjc.INVALID
    return vjc.retries_from_v2(document, kind)


def _annotations(job):
    return [_dig(job, "spec", "template", "metadata", "annotations"),
            _dig(job, "spec", "template", "spec", "template", "metadata", "annotations"),
            _dig(job, "metadata", "annotations")]


def _shape(job):
    execution = _dig(job, "spec", "template", "spec")
    task = _dig(execution, "template", "spec")
    if not isinstance(task, dict) or "containers" not in task:
        raise Refused("unexpected Job resource shape: no spec.template.spec.template.spec.containers")
    annotations = {}
    for source in _annotations(job):
        if isinstance(source, dict):
            annotations.update(source)
    return execution, task, annotations


def check(job, *, image_repo, image_digest, service_account, runner_commit, secret_name,
          cloudsql_instance, timeout_seconds, memory, cpu, v2_job=None):
    if not isinstance(job, dict):
        raise Refused("the job description is not a JSON object")
    if not _DIGEST.fullmatch(image_digest or "") or not _SHA.fullmatch(runner_commit or ""):
        raise Refused("the expected image digest / runner commit are malformed")
    execution, task, annotations = _shape(job)
    retries = vjc.UNSET if v2_job is None else strict_v2_retries(v2_job, "job")
    bad = vjc.forbidden_annotations(job, v2_job)
    bad += vjc.validate_task(task, image_repo=image_repo, image_digest=image_digest,
                             service_account=service_account, runner_commit=runner_commit,
                             secret_name=secret_name, expected_args=[], timeout_seconds=timeout_seconds,
                             memory=memory, cpu=cpu, v2_retries=retries)
    sql_values = [source[_SQL_ANNOTATION] for source in _annotations(job)
                  if isinstance(source, dict) and _SQL_ANNOTATION in source]
    if not sql_values or any(value != cloudsql_instance for value in sql_values):
        bad.append(f"Cloud SQL instances annotation must name exactly {cloudsql_instance!r} at every present level")
    count = vjc.parse_int64(execution["taskCount"]) if "taskCount" in execution else 1
    if count != 1:
        bad.append("taskCount is not 1")
    return bad


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("job-file", "image-repo", "image-digest", "service-account", "runner-commit",
                 "secret-name", "cloudsql-instance", "memory", "cpu"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--timeout-seconds", required=True, type=int)
    parser.add_argument("--v2-job-file")
    args = parser.parse_args(argv)
    try:
        with open(args.job_file, encoding="utf-8") as stream:
            job = json.load(stream)
        v2_job = None
        if args.v2_job_file:
            with open(args.v2_job_file, encoding="utf-8") as stream:
                v2_job = json.load(stream)
            if not isinstance(v2_job, dict):
                raise Refused("the supplied v2 job file is not a JSON object (not an absent read)")
        bad = check(job, v2_job=v2_job, image_repo=args.image_repo, image_digest=args.image_digest,
                    service_account=args.service_account, runner_commit=args.runner_commit,
                    secret_name=args.secret_name, cloudsql_instance=args.cloudsql_instance,
                    timeout_seconds=args.timeout_seconds, memory=args.memory, cpu=args.cpu)
    except (Refused, OSError, ValueError, TypeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    for problem in bad:
        print(f"REFUSED: {problem}", file=sys.stderr)
    if bad:
        return 2
    print(f"verification job definition verified: image {args.image_repo}@{args.image_digest}; "
          f"identity {args.service_account}; one secret; one Cloud SQL instance; one task, no retries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
