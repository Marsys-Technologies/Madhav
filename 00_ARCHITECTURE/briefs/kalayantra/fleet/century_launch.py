#!/usr/bin/env python3
"""Century bridge (item J-4e; SR-PREBUILD-ALL): stage the final ordinary candidate run once, then launch exactly that run.

The measuring launch with the test slice removed. The executor supplies the accepted J-4e request, source and capabilities. The staged run
carries NO slice marker and the trigger 'gochara-v5-century' (platform/scripts/dispatch_v5_century_job.py); the durable O_EXCL no-retry claim,
the database-clock budget and the row locks are the small-test bridge's own (smalltest_launch.launch_staged), unchanged. No horizon, class set
or rule version is chosen here: the request's final_rules, defer_in_build_verify, horizon and result_policy (F-CHANNEL, OD-1) are staged into the run's plan_manifest
by the dispatch binding and the launch expects exactly that manifest; the writer refuses an unmarked run without them.

`--resume` (SR-RESUME-NOW, OWNER-RESUMABLE-REQUIRED-20261025; the executor kind `century_resume`) continues a killed or failed century build instead of starting it again. It
starts the SAME Cloud Run job as the dispatch, over the SAME staged century config and horizon: the only differences are the staging binding (platform/scripts/
dispatch_v5_century_resume_job.py, which admits a ledger-attested partial chain where the dispatch demands none) and one launcher check first — the request's program
identity must be the writer program the century contract declares, else it refuses before anything is staged. The launcher passes the writer NO resume argument: the resume binding
(SR-RESUME-EXPLICIT-BINDING: `plan_manifest.gochara_v5_century_resume`, staged by dispatch_v5_century_resume_job.py from the accepted ledger readback) is the writer's only signal,
and the writer plans only the substeps its committed-substep ledger (migration 1410) has not recorded, after proving the program and the rows unchanged. The durable O_EXCL claim, the
database-clock budget, the row locks and the launch evidence (`ky.century_launch/1`) are the dispatch's, unchanged.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys

import smalltest_launch as bridge

# SR-J2D-TEARDOWN-EVIDENCE item 2 (as measuring_launch.py): with Pub/Sub on, events.emit_event publishes asset.substep to the topic and prints
# nothing, so the Cloud Logging read (cloudrun_readback --logs) would see no sub-step lines. PUBSUB_DISABLED makes every event print to stdout.
# Set for THIS execution only. A test ties this text to the shared constant the dry run's launch_plan shows.
CENTURY_EXECUTION_ENV = "PUBSUB_DISABLED=1"
CENTURY_TRIGGERED_BY = "gochara-v5-century"
LAUNCH_SCHEMA = "ky.century_launch/1"
RUN_UUID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")


def century_cloud_launcher(run_id, timeout_s):
    return bridge.cloud_launcher(run_id, timeout_s, update_env_vars=CENTURY_EXECUTION_ENV)


def staging_binding(resume):
    """The module that stages the run: the century dispatch binding, or — for `--resume` — the resume binding (same staged manifest, ledger-attested admission). Static imports, so the
    executor's marker scan (test_executor_mechanical_acceptance) follows both into their closure."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "platform/scripts"))
    if resume:
        import dispatch_v5_century_resume_job as binding
    else:
        import dispatch_v5_century_job as binding
    return binding


def resume_preflight(request=None, contract=None):
    """The launcher's own check of a `--resume`, before anything is staged: the executor's kind is `century_resume` and the request's program identity is the writer program the
    century contract of this tree declares (shared.resume_program_problem raises its named refusal). Both inputs are injectable for a test; by default the request is the
    executor's (`KY_OPERATION_REQUEST`) and the contract is fleet/century_contract.json beside this file (the executor runs this script from a tree at the reviewed commit)."""
    scripts = str(Path(__file__).resolve().parents[4] / "platform/scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import v5_small_test_shared as shared
    req = shared.operation_request() if request is None else request
    if req.get("kind") != "century_resume":
        raise bridge.Refused("executor operation kind does not authorize a century resume")
    shared.resume_program_problem(req, json.loads((Path(__file__).resolve().parent / "century_contract.json").read_text(encoding="utf-8")) if contract is None else contract)
    return req


def run(argv=None, *, dispatcher=None, connect=None, launcher=century_cloud_launcher, claim_dir=None, request=None, contract=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--resume", action="store_true", help="continue the killed or failed century build over the substeps its ledger committed (executor kind century_resume)")
    parser.add_argument("--classes", default="all", choices=("all",))
    parser.add_argument("--final_rules", required=True, choices=("true", "false"))
    parser.add_argument("--defer_in_build_verify", required=True, choices=("true", "false"))
    parser.add_argument("--horizon", required=True)
    parser.add_argument("--result_policy", required=True, choices=("all_null_candidate/1", "window_qualification/1"))
    args = parser.parse_args(argv)
    if args.resume:
        resume_preflight(request, contract)          # a program identity other than the contract's refuses here, before any staging
    if dispatcher is None:
        dispatcher = staging_binding(args.resume)
    staging = ["--i-am-steward", "--after-settled-1", "--execute", "--classes", args.classes, "--final_rules", args.final_rules,
               "--defer_in_build_verify", args.defer_in_build_verify, "--horizon", args.horizon, "--result_policy", args.result_policy]
    if connect is None:
        import psycopg
        import psycopg.rows
        connect = lambda: psycopg.connect(os.environ["DATABASE_URL"], row_factory=psycopg.rows.dict_row)
    output = io.StringIO()
    # Preserve the dispatcher's safe error/commit-unknown behaviour. Never stage again if it throws, even when a run id was printed or COMMIT was sent.
    with contextlib.redirect_stdout(output):
        dispatcher.main(staging)
    run_id = output.getvalue().strip()
    if not RUN_UUID.fullmatch(run_id):
        raise bridge.Refused("staging output is not exactly one run UUID; lookup required, never retry")
    conn = connect()
    try:
        conn.execute("SELECT set_config('lock_timeout', '5s', true)")
        candidate = dispatcher._load_inactive_candidate(conn.cursor())
        shape = dispatcher.century_shape(classes=args.classes, final_rules=args.final_rules, defer_in_build_verify=args.defer_in_build_verify,
                                         horizon=args.horizon, result_policy=args.result_policy)
        manifest, _ = dispatcher.build_century_manifest(candidate=candidate, slice_marker=shape)
        result = bridge.launch_staged(run_id=run_id, expected_manifest=manifest, connection=conn,
                                      claim_dir=claim_dir or Path(os.environ["KY_ROOT"]) / "run/ops/century_launch",
                                      launcher=launcher, launch_schema=LAUNCH_SCHEMA, triggered_by=CENTURY_TRIGGERED_BY, test_slice=False)
        print(bridge.canonical(result), flush=True)
        return result
    finally:
        # No run mutation here. The independently committed staging transaction is left intact, including on an unknown remote outcome.
        conn.rollback()
        conn.close()


def _is_named_refusal(exc):
    """bridge.Refused or v5_small_test_shared.Refused, nothing else. The shared module is looked up, never imported: run() puts platform/scripts on the
    path only when it imports the dispatcher, and a shared.Refused cannot exist unless that module was loaded."""
    shared_refused = getattr(sys.modules.get("v5_small_test_shared"), "Refused", None)
    return isinstance(exc, (bridge.Refused,) + ((shared_refused,) if shared_refused else ()))


def cli(argv=None):
    try:
        run(argv)
        return 0
    except SystemExit as exc:
        return exc.code
    except BaseException as exc:
        if _is_named_refusal(exc):
            # SR-J4E-FIX: a Refused's text is ids/counts/relation names only (never connection text), so it is shown; every other exception stays type-only
            print(f"century launch refused: {exc}; reconcile retained evidence, never retry", file=sys.stderr)
        else:
            print(f"century launch failed ({type(exc).__name__}); reconcile retained evidence, never retry", file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 1


if __name__ == "__main__":
    raise SystemExit(cli())
