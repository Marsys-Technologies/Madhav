"""SR-K9-PUBLISHABLE D7 (root CLAUDE.md §N.8): `orchestrator_rebuild`'s required `dry_run_passed` attestation has a real detector.

The kind's dry run reports `dry_run_passed: null` by design (publication.inspect_rebuild: a plan inspection runs no detector, N.7.6), so a signer's
`dry_run_passed: true` for it measured nothing. The production request is now admitted only when THIS executor's own receipt shows a COMPLETED
`orchestrator_rebuild_dryrun` for the same identity (`dry_run_check`, DRYRUN_IDENTITY_FIELDS = item_id, chart_id, reviewed_commit, args): the
executor reads its receipt, never the signer's word. One oracle per distinct production claim; each passes on the real executor and FAILS on a copy of
executor.py with that ONE claim's line reverted (the planted reversion), as in test_executor_mechanical_production.py.

  Y1 a signed orchestrator_rebuild with the attestation but without a COMPLETED dry-run receipt for its own identity is refused (no receipt cited; a FAILED
     dry run; a dry run of another run-id), and one with the receipt is admitted
  Y2 the gate is this kind's alone: a signed request of another kind is admitted exactly as before (the attestation route is unchanged for it)
"""
import json

import pytest

import test_executor_mechanical_production as M
from test_executor_table import ALL_CAPS, CANONICAL_CHART, World  # noqa: F401  (World is used through M.build)

RUN = "6f1d3c1e-0000-4000-8000-000000000001"
OTHER_RUN = "6f1d3c1e-0000-4000-8000-000000000002"
ARGS = {"run-id": RUN, "assets": "ka_yojaka,ka_sangam"}


def archive_dry_run(w, req, oid="dry-rb", status="COMPLETED", exit_code=0):
    """The `orchestrator_rebuild_dryrun` request for `req`'s identity archived in done/, with the receipt and output the executor would have written."""
    dreq = {"operation_id": oid, "kind": "orchestrator_rebuild_dryrun", "item_id": req["item_id"], "idempotency_key": "k-" + oid,
            "requested_by": "adhikarin", "kyd": "kyd-1", "args": dict(req["args"]), "chart_id": req["chart_id"], "reviewed_commit": req["reviewed_commit"]}
    (w.mod.DONE / f"{oid}.json").write_text(json.dumps(dreq))
    output = json.dumps({"status": "PLAN_ONLY", "dry_run_passed": None}) + "\n"
    (w.mod.REC / f"{oid}.output.txt").write_text(output)
    record = {"operation_id": oid, "kind": dreq["kind"], "item_id": req["item_id"], "status": status, "reason": "", "exit_code": exit_code,
              "ts": M.iso(seconds=-30), "reviewed_commit": req["reviewed_commit"], "request_sha256": w.mod.request_digest(dreq),
              "output_sha256": M.sha(output)}
    body = json.dumps(record, indent=1).encode()
    (w.mod.REC / f"{oid}.json").write_bytes(body)
    return {"name": f"{oid}.json", "sha256": M.sha(body)}


def signed(w, args=ARGS, dry=None, oid="op-rb"):
    """A V1-signed production request (attestation dry_run_passed: true, as a signer would give) carrying the dry-run citation when `dry` is given."""
    req = w.production_request("orchestrator_rebuild", operation_id=oid, idempotency_key="k-" + oid, args=dict(args))
    if dry is not None:
        req["dryrun_receipt"] = dry
    return w.accept(req)


def oracle_y1_attestation_alone_never_admits_a_rebuild(w, table):
    base = w.production_request("orchestrator_rebuild", args=dict(ARGS))
    good = signed(w, dry=archive_dry_run(w, base))
    assert w.mod.validate(good, table, ALL_CAPS) is None, "control failed — the refusals below would be vacuous"
    attestation_only = signed(w, oid="op-rb-bare")
    assert json.loads(open(attestation_only["acceptance_receipt"]).read())["checks"]["dry_run_passed"] is True, "premise: the signer attested"
    assert w.mod.validate(attestation_only, table, ALL_CAPS) == "dryrun_receipt {name, sha256} citing this kind's completed dry run is required"
    failed = signed(w, dry=archive_dry_run(w, base, oid="dry-failed", status="FAILED", exit_code=1), oid="op-rb-failed")
    assert w.mod.validate(failed, table, ALL_CAPS) == "the dry run did not COMPLETE OK (exit 0, complete output, bound archived request) for this request's identity"
    other = w.production_request("orchestrator_rebuild", args={**ARGS, "run-id": OTHER_RUN})
    elsewhere = signed(w, args=ARGS, dry=archive_dry_run(w, other, oid="dry-other"), oid="op-rb-other")
    assert w.mod.validate(elsewhere, table, ALL_CAPS) == "the dry run did not COMPLETE OK (exit 0, complete output, bound archived request) for this request's identity"


def oracle_y2_other_kinds_keep_the_attestation_route(w, table):
    control = w.accept(w.production_request("scheduler_resume", operation_id="op-sr", idempotency_key="k-sr"))
    assert "dryrun_receipt" not in control
    assert w.mod.validate(control, table, ALL_CAPS) is None, "a signed request of another kind is admitted without a dry-run citation, as before"


ORACLES = {
    "y1": (oracle_y1_attestation_alone_never_admits_a_rebuild,
           ("or orchestrator_rebuild_dryrun_problem(req, table) or head_policy_problem(req)", "or head_policy_problem(req)")),
    "y2": (oracle_y2_other_kinds_keep_the_attestation_route,
           ('    if req.get("kind") != "orchestrator_rebuild": return None\n    return dry_run_check(req, table)[0]',
            '    return dry_run_check(req, table)[0]')),
}


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_executor(tmp_path, monkeypatch, claim):
    w, table = M.build(tmp_path, monkeypatch)
    ORACLES[claim][0](w, table)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, mutation = ORACLES[claim]
    w, table = M.build(tmp_path, monkeypatch, mutation)
    with pytest.raises(AssertionError):
        oracle(w, table)
