#!/usr/bin/env python3
"""Century staging binding (item J-4e; SR-PREBUILD-ALL): stage the FINAL, ordinary candidate build of ka_gochara_v5.

The measuring build (dispatch_v5_measuring_job.py) is the same staged run with a test-slice marker, stamped `test_slice` and so unsealable by
construction. The century build is that run WITHOUT the marker: `plan_manifest` carries no `gochara_v5_test_slice`, the run's trigger is
'gochara-v5-century', and the writer builds the ordinary, sealable candidate it builds for any unmarked run. This binding chooses NO horizon,
class set or rule version itself: the production orchestrator hands the writer chart_id and birth_params only, so the request's `final_rules`,
`defer_in_build_verify` and `horizon` arguments (F-CHANNEL, SR-W34-PREP-RULINGS 1; the owner's D-G9 value, never a constant here) are STAGED as
plan_manifest['gochara_v5_century_config'], covered by plan_manifest_digest, and the writer reads them from there. The request digest covers `args`,
so each is bound by the acceptance and the pack fill. The writer refuses an unmarked run that arrives without an explicit profile or horizon.

It reuses the guarded small-test staging transaction (chart lock, frozen-generation refusal, one active run per chart, registry-row shape,
N-137 end state, no receipts and no generation '5.0' output: the measuring lifecycle must be torn down first) through explicit keyword
interfaces of `dispatch_v5_small_test_job._main`; no request flag changes the small-test policy.

Modes: `--dry-run` runs the real staging transaction and ROLLS BACK (zero cloud writes), printing the staged plan and the exact Cloud Run
launch it would make; `--execute` commits the staged run and prints exactly its UUID. The durable, no-retry launch is
fleet/century_launch.py, which stages once through this module and launches that staged run.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import hashlib
import io
import json
import sys

import dispatch_v5_small_test_job as staging
import v5_small_test_shared as shared

TRIGGERED_BY = shared.CENTURY_TRIGGERED_BY
_load_inactive_candidate = staging._load_inactive_candidate

# The one Cloud Run launch the real kind makes (fleet/smalltest_launch.py cloud_launcher; a test pins this plan to its argv). Fixed text, never
# request input.
LAUNCH_JOB = "brahma-build-pipeline-job"
LAUNCH_PROJECT = "madhav-astrology"
LAUNCH_REGION = "asia-south1"


def launch_plan(run_id: str) -> dict:
    return dict(argv=["gcloud", "run", "jobs", "execute", LAUNCH_JOB, f"--project={LAUNCH_PROJECT}", f"--region={LAUNCH_REGION}",
                      f"--update-env-vars={shared.CENTURY_EXECUTION_ENV}", f"--args=--run-id,{run_id}", "--async",
                      "--format=value(metadata.name)"],
                job=LAUNCH_JOB, project=LAUNCH_PROJECT, region=LAUNCH_REGION, update_env_vars=shared.CENTURY_EXECUTION_ENV, run_id=run_id,
                async_launch=True)


def century_shape(*, run=None, classes=None, horizon_start=None, horizon_end=None, final_rules=None, defer_in_build_verify=None, horizon=None, result_policy=None) -> dict:
    """The only request shape there is: all classes, no run name, no slice horizon (`horizon_start`/`horizon_end` are the small-test pair and stay refused),
    plus — F-CHANNEL, SR-W34-PREP-RULINGS 1 — the century config: the rule profile, the verify-deferral switch and the D-G9 horizon as the request's
    'true'/'false'/'start,end' strings. The three come together or not at all; given, they are validated by the WRITER's own validator and returned in its
    canonical form under 'century_config'. Anything else is refused before any connection."""
    if run is not None or horizon_start is not None or horizon_end is not None or classes not in (None, "all"):
        raise shared.Refused("century dispatch takes only --classes all: no run name and no slice horizon (the century horizon is the one 'horizon' argument)")
    shape = {"classes": "all"}
    given = (final_rules, defer_in_build_verify, horizon, result_policy)
    if any(value is not None for value in given):
        if any(value is None for value in given):
            raise shared.Refused("century dispatch takes final_rules, defer_in_build_verify, horizon and result_policy together")
        shape["century_config"] = shared.century_config_component(final_rules, defer_in_build_verify, horizon, result_policy)
    return shape


def build_century_manifest(*, candidate, slice_marker=None):
    """The frozen asset_set manifest, digested once, with NO slice marker. `slice_marker` is the century shape (see `century_shape`): when it carries a
    'century_config' the manifest also carries it under the writer's CENTURY_CONFIG_KEY and the digest is taken over the whole — so the profile, the
    deferral switch and the horizon are fixed at dispatch and the writer's every read verifies them (a shape without one is `build_manifest`'s own)."""
    manifest, digest = staging.build_manifest(chart_id=shared.CHART_ID, candidate=candidate,
                                              expected_code_digest=staging._load_writer_digest(shared.ASSET_ID))
    if staging.SLICE_MARKER_KEY in manifest:
        raise shared.Refused("a century manifest never carries a slice marker")
    config = (slice_marker or {}).get("century_config")
    if config is not None:
        manifest[shared.CENTURY_CONFIG_KEY] = config
        digest = hashlib.sha256(staging._canonical_json(manifest).encode("utf-8")).hexdigest()
    return manifest, digest


def parse_args(argv):
    p = argparse.ArgumentParser(allow_abbrev=False, prog="dispatch_v5_century_job.py", description=__doc__.splitlines()[0])
    p.add_argument("--i-am-steward", action="store_true", help="required: you are the steward, acting on native authority")
    p.add_argument("--after-settled-1", action="store_true", help="required: the protected window's settled-1 precondition has passed")
    p.add_argument("--classes", default="all", choices=("all",))
    p.add_argument("--final_rules", required=True, choices=("true", "false"), help="the rule profile: true = the final ND-H rules, false = the measuring rules")
    p.add_argument("--defer_in_build_verify", required=True, choices=("true", "false"), help="true = defer the in-build verify:<class> to the independent job (final rules only)")
    p.add_argument("--result_policy", required=True, choices=shared.CENTURY_RESULT_POLICIES, help="OD-1: the numeric-result policy the century build is bound under (window_qualification/1 = numbers on)")
    p.add_argument("--horizon", required=True, help="the D-G9 derived horizon as 'start,end', each a tz-aware ISO timestamp (half-open)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="the DEFAULT: stage, ROLL BACK, print the plan")
    mode.add_argument("--execute", action="store_true", help="commit the staged run (needs both steward flags)")
    a = p.parse_args(argv)
    # the attributes staging._main reads; a century run has no lookup mode, run name or horizon
    return argparse.Namespace(i_am_steward=a.i_am_steward, after_settled_1=a.after_settled_1, execute=a.execute, classes=a.classes,
                              final_rules=a.final_rules, defer_in_build_verify=a.defer_in_build_verify, horizon=a.horizon, result_policy=a.result_policy,
                              list_runs=False, lookup=None, run=None, horizon_start=None, horizon_end=None)


def prepare_report(*, dry_run, run_id, manifest, manifest_digest, existing, notes, created_at) -> dict:
    """Everything the run prints, built BEFORE the COMMIT (the staging transaction's rule)."""
    plan = {"run_id": run_id, "chart_id": shared.CHART_ID, "asset_id": shared.ASSET_ID, "triggered_by": TRIGGERED_BY,
            "plan_manifest_digest": manifest_digest, "plan_manifest": manifest, "existing_small_test_runs": existing,
            "admission_notes": notes, "launch_plan": launch_plan(run_id)}
    skew = staging.image_skew_notice(manifest)
    if dry_run:
        return {"stderr": [f"[dry-run] staged plan for the CENTURY build of {shared.ASSET_ID} on chart {shared.CHART_ID} — ROLLED BACK, "
                           "nothing written, no cloud call; launch_plan is the one Cloud Run launch the real kind would make", *skew],
                "stdout": [json.dumps(plan, indent=2, sort_keys=True)]}
    if created_at is None:
        raise RuntimeError("the INSERT returned no created_at, so no deadline can be derived from the database")
    execute_by = (created_at + datetime.timedelta(minutes=staging.EXECUTE_WITHIN_MINUTES)).isoformat(timespec="seconds")
    return {"stderr": [f"[dispatch] LAUNCH BEFORE {execute_by}: the cockpit watchdog fails a planned run never started after "
                       f"{staging.EXECUTE_WITHIN_MINUTES} minutes (stored creation time {created_at.isoformat(timespec='seconds')})",
                       *skew,
                       f"[dispatch] staged CENTURY build_run {run_id} for asset {shared.ASSET_ID} on chart {shared.CHART_ID} "
                       f"(manifest digest {manifest_digest}); asset_registry was not touched"],
            "stdout": [run_id]}


def _century_request_policy(req, root):
    """The century evidence policy with its fresh, read-only scoped-content measurement (SR-BACKUP-VALIDITY-A8): the named scoped backup
    admits this dispatch only while the database's scoped content still has the digest the backup recorded. The executor's admission has
    no database; this is the check that reads it, at --execute and before anything is staged."""
    import backup_v5_small_test_job as backup
    return shared.century_request_problem(req, root, measure=backup.measure_scope_now)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = parse_args(argv)
    # Both the real staging and its rollback consume the executor's request; the executor separately checks live lease, G8 and merged reviewed source.
    req = shared.operation_request()
    expected = "century_dispatch" if args.execute else "century_dispatch_dryrun"
    if req.get("kind") != expected:
        raise shared.Refused("executor operation kind and century mode differ")
    problem = _century_request_policy(req, shared.evidence_root())
    if problem:
        raise shared.Refused(problem)
    shape = century_shape(classes=args.classes, final_rules=args.final_rules, defer_in_build_verify=args.defer_in_build_verify, horizon=args.horizon,
                          result_policy=args.result_policy)
    bound = req.get("args") or {}
    if shape != century_shape(run=bound.get("run"), classes=bound.get("classes"), final_rules=bound.get("final_rules"),
                              defer_in_build_verify=bound.get("defer_in_build_verify"), horizon=bound.get("horizon"),
                              result_policy=bound.get("result_policy")):
        raise shared.Refused("century arguments differ from the accepted request")

    def marker_builder(*, run=None, classes=None, horizon_start=None, horizon_end=None):
        # staging._main passes only the small-test keywords; the century config is the request's, already compared with the bound request above
        return century_shape(run=run, classes=classes, horizon_start=horizon_start, horizon_end=horizon_end, final_rules=args.final_rules,
                             defer_in_build_verify=args.defer_in_build_verify, horizon=args.horizon, result_policy=args.result_policy)

    def check_manifest(manifest, digest):
        if args.execute:
            shared.century_dryrun_evidence(req, shared.evidence_root(), digest)

    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        staging._main(argv, parse_args=parse_args, marker_builder=marker_builder, operation_kind="century_dispatch",
                      request_policy=_century_request_policy, manifest_check=check_manifest,
                      manifest_builder=build_century_manifest, triggered_by=TRIGGERED_BY, report_builder=prepare_report)
    if args.execute:
        print(output.getvalue().strip(), flush=True)          # exactly one staging UUID; the durable bridge owns the remote launch
    else:
        plan = json.loads(output.getvalue())
        proof = dict(schema="ky.century_staging/1", status="ROLLED_BACK", rollback_confirmed=True, operation_id=req["operation_id"],
                     request_sha256=shared.request_hash(req), args=req["args"], **plan)
        print(json.dumps(proof, sort_keys=True, separators=(",", ":")), flush=True)


def cli(argv=None):
    try:
        main(argv)
        return 0
    except SystemExit as exc:
        return exc.code
    except BaseException as exc:
        print(staging._safe_failure(exc), file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 1


if __name__ == "__main__":
    raise SystemExit(cli())
