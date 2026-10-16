#!/usr/bin/env python3
"""Dedicated measuring staging binding. DISABLED in executor_ops until phase review.

Uses the existing guarded transaction; never relaxes the small-test CLI gate.
Only the exact measuring shape is accepted. The full-horizon writer and its
sink-all policy remain the authoritative computation, unchanged by this binding.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys

import dispatch_v5_small_test_job as staging
import v5_small_test_shared as shared

_load_inactive_candidate = staging._load_inactive_candidate
build_small_test_manifest = staging.build_small_test_manifest


def build_slice_marker(*, run, classes=None, horizon_start=None, horizon_end=None):
    if run != 'all_classes_full' or classes not in (None, 'all') or horizon_start is not None or horizon_end is not None:
        raise shared.Refused('measuring dispatch requires all_classes_full, all classes and the ruled full horizon')
    writer = staging._writer()
    marker = dict(schema=writer.TEST_SLICE_SCHEMA, run='all_classes_full',
        horizon=[x.isoformat() for x in writer.MEASURING_HORIZON], classes=list(writer.SCORED_CLASSES))
    validated = writer._validate_test_slice(marker)
    if validated.marker != marker:
        raise shared.Refused('measuring marker is not the canonical writer shape')
    return marker


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = staging._parse_args(argv)
    if args.lookup or args.list_runs:
        raise shared.Refused('use the existing read-only run lookup; measuring binding stages only')
    # Both real rollback and staging consume independent request acceptance.
    # The executor separately checks live lease, G8 and merged reviewed source.
    req = shared.operation_request()
    expected = 'measuring_dispatch' if args.execute else 'measuring_dispatch_dryrun'
    if req.get('kind') != expected:
        raise shared.Refused('executor operation kind and measuring mode differ')
    problem = shared.measuring_request_problem(req, shared.evidence_root())
    if problem:
        raise shared.Refused(problem)
    marker = build_slice_marker(run=args.run, classes=args.classes,
        horizon_start=args.horizon_start, horizon_end=args.horizon_end)
    bound = req.get('args') or {}
    if marker != build_slice_marker(run=bound.get('run'), classes=bound.get('classes')):
        raise shared.Refused('measuring arguments differ from the accepted request')
    def check_manifest(manifest, digest):
        if args.execute:
            shared.measuring_dryrun_evidence(req, shared.evidence_root(), digest)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        staging._main(argv, marker_builder=build_slice_marker, operation_kind='measuring_dispatch',
                      request_policy=shared.measuring_request_problem, manifest_check=check_manifest)
    if args.execute:
        # Exactly one staging UUID; the durable bridge owns remote launch.
        print(output.getvalue().strip(), flush=True)
    else:
        plan = json.loads(output.getvalue())
        proof = dict(schema='ky.measuring_staging/1', status='ROLLED_BACK', rollback_confirmed=True,
            operation_id=req['operation_id'], request_sha256=shared.request_hash(req), args=req['args'], **plan)
        print(json.dumps(proof, sort_keys=True, separators=(',', ':')), flush=True)


def cli(argv=None):
    try:
        main(argv)
        return 0
    except SystemExit as exc:
        return exc.code
    except BaseException as exc:
        print(staging._safe_failure(exc), file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 1


if __name__ == '__main__':
    raise SystemExit(cli())
