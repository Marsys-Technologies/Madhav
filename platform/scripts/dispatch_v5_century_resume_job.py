#!/usr/bin/env python3
"""Century RESUME staging binding (item J-4e; SR-RESUME-NOW, OWNER-RESUMABLE-REQUIRED-20261025): stage the run that CONTINUES a killed or failed century build.

A resume is a new build_run over the SAME generation '5.0' chain. It is staged exactly as the century build is (dispatch_v5_century_job.py: the same plan manifest,
the same `gochara_v5_century_config`, the same horizon, the same trigger 'gochara-v5-century', the same Cloud Run job) and launched by the same bridge
(fleet/century_launch.py --resume). What it does NOT do is decide what to skip: the WRITER does, from its committed-substep ledger (migration 1410). It does it ONLY
on the explicit binding this module stages (SR-RESUME-EXPLICIT-BINDING): the staged plan_manifest carries ONE extra key, `shared.RESUME_BINDING_KEY`
(`gochara_v5_century_resume`, see shared.resume_binding: the run being resumed, the program the ledger was built by, the ordered substep keys the accepted readback
measured). A run staged WITHOUT it (a century_dispatch) that finds ledger rows refuses by name in the writer (fresh_run_found_ledger) and, before that, in the dispatch's
absence census (ledger rows must be absent). So a resume and a dispatch differ in exactly that key (and therefore in the manifest digest).

What changes is the ADMISSION, in one place, `resume_gate` (a `dispatch_v5_small_test_job._admit(cur, resume=...)`): where a dispatch refuses any existing generation
'5.0' output, a resume requires that the output be the ledger's. All of `_admit`'s other checks stand (frozen generation, active run, registry row, N-137 end state,
dependencies, no provenance receipt); the N-137 check is judged with the century trigger too, because the run being resumed is itself a century run.
  1. the request names the program it continues (`program_identity`) and its writer digest equals the century contract's writer_source_digest (shared.resume_program_problem);
  2. the request's accepted evidence holds (shared.century_request_problem -> resume_evidence: the accepted ledger readback bound to the launch it resumes);
  3. LIVE, inside the chart lock: the generation's manifest is a candidate, the ledger table exists and holds substeps for (chart, generation), every one of them carries the
     request's writer, implementation and plan digests (migration 1410 columns), and the run being resumed is a century run of this chart that did not complete.
`--dry-run` stages inside the same transaction and ROLLS BACK: no commit, no claim, no Cloud Run call.

Modes: `--dry-run` (the default) prints the staging proof (`ky.century_staging/1`, with the `resume` it was staged for); `--execute` commits the staged run and prints
exactly its UUID. The durable, no-retry launch is fleet/century_launch.py --resume.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

import dispatch_v5_century_job as century
import dispatch_v5_small_test_job as staging
import v5_small_test_shared as shared

# the reused century staging helpers, under this module's name so the launcher drives either binding through one interface
century_shape = century.century_shape
_load_inactive_candidate = century._load_inactive_candidate
CONTRACT = Path(__file__).resolve().parents[2] / "00_ARCHITECTURE/briefs/kalayantra/fleet/century_contract.json"


def build_century_manifest(*, candidate, slice_marker=None):
    """The century manifest (dispatch_v5_century_job.build_century_manifest, unchanged) PLUS the explicit resume binding, digested over the whole. The binding is built from the
    executor's request and its accepted readback (shared.resume_binding), so the staging, its dry run and the launcher's expected manifest all compute the same manifest."""
    manifest, _ = century.build_century_manifest(candidate=candidate, slice_marker=slice_marker)
    if shared.RESUME_BINDING_KEY in manifest:
        raise shared.Refused("a century manifest never carries a resume binding before the resume stages it")
    manifest[shared.RESUME_BINDING_KEY] = shared.resume_binding(shared.operation_request(), shared.evidence_root())
    return manifest, hashlib.sha256(staging._canonical_json(manifest).encode("utf-8")).hexdigest()


def load_contract(path=None):
    """fleet/century_contract.json of the tree this script runs from (the executor runs it from a tree at the reviewed commit)."""
    return json.loads(Path(path or CONTRACT).read_text(encoding="utf-8"))


def resume_gate(req):
    """The live admission of a resume (see the module docstring, 3): `resume(cur, rows, manifest) -> notes`, raising shared.Refused by name."""
    identity = req["program_identity"]

    def gate(cur, rows, manifest):
        if manifest is None or manifest["status"] != "candidate":
            raise shared.Refused(f"generation '{shared.GENERATION}' of chart {shared.CHART_ID} has no candidate manifest "
                                 f"({'absent' if manifest is None else 'status ' + str(manifest['status'])}): nothing to resume")
        ledger = shared.RESUME_LEDGER_TABLE
        cur.execute("SELECT to_regclass(%s) AS found", (ledger,))       # the name the readback and the writer use, resolved on the role's own search path
        if cur.fetchone()["found"] is None:
            raise shared.Refused(f"the committed-substep ledger {ledger} does not exist: nothing to resume")
        where = "FROM " + ledger + " WHERE chart_id = %s::uuid AND generation = %s"
        committed = shared.count(cur, "SELECT count(*) AS n " + where, (shared.CHART_ID, shared.GENERATION))
        if not committed:
            raise shared.Refused(f"the ledger {ledger} holds no committed substep for chart {shared.CHART_ID} generation '{shared.GENERATION}': "
                                 "nothing to resume (a clean start is a century_dispatch)")
        for column in ("writer_digest", "implementation_digest", "plan_digest"):
            other = shared.count(cur, "SELECT count(*) AS n " + where + " AND " + column + " IS DISTINCT FROM %s",
                                 (shared.CHART_ID, shared.GENERATION, identity[column]))
            if other:
                raise shared.Refused(f"{other} ledger substep(s) were committed by a program other than the request's ({column}): a resume continues only the same program")
        cur.execute("SELECT state, triggered_by FROM build_runs WHERE id = %s::uuid AND chart_id = %s::uuid", (req["resume_run_id"], shared.CHART_ID))
        run = cur.fetchone()
        if run is None or run["triggered_by"] != shared.CENTURY_TRIGGERED_BY or run["state"] == "completed":
            raise shared.Refused(f"the run to resume ({req['resume_run_id']}) is not an unfinished century run of chart {shared.CHART_ID}")
        return [f"RESUME of century run {req['resume_run_id']}: {committed} committed substep(s) in {ledger}; the writer plans only the substeps not yet committed"]
    return gate


def _resume_request_policy(req, root):
    return shared.century_request_problem(req, root)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = century.parse_args(argv)
    req = shared.operation_request()
    expected = "century_resume" if args.execute else "century_resume_dryrun"
    if req.get("kind") != expected:
        raise shared.Refused("executor operation kind and century resume mode differ")
    shared.resume_program_problem(req, load_contract())
    problem = _resume_request_policy(req, shared.evidence_root())
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
        return century_shape(run=run, classes=classes, horizon_start=horizon_start, horizon_end=horizon_end, final_rules=args.final_rules,
                             defer_in_build_verify=args.defer_in_build_verify, horizon=args.horizon, result_policy=args.result_policy)

    gate = resume_gate(req)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        staging._main(argv, parse_args=century.parse_args, marker_builder=marker_builder, operation_kind="century_resume",
                      request_policy=_resume_request_policy, manifest_check=None, manifest_builder=build_century_manifest,
                      triggered_by=century.TRIGGERED_BY, report_builder=century.prepare_report,
                      admit=lambda cur: staging._admit(cur, resume=gate))
    if args.execute:
        print(output.getvalue().strip(), flush=True)          # exactly one staging UUID; the durable bridge owns the remote launch
    else:
        plan = json.loads(output.getvalue())
        resume = dict(resumes=req["resumes"]["name"], resume_run_id=req["resume_run_id"], program_identity=req["program_identity"])
        proof = dict(schema="ky.century_staging/1", status="ROLLED_BACK", rollback_confirmed=True, operation_id=req["operation_id"],
                     request_sha256=shared.request_hash(req), args=req["args"], resume=resume, **plan)
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
