"""K9-4b `k9_rebuild_stage` in the executor (ruling SR-PREP-LANES-1 (2)): the governed op kind that stages, in production, the frozen build_runs row and open candidate that
`orchestrator_rebuild` requires. The staging itself is proven against a real database in platform/python-sidecar/tests/l3/kala_db/manifest/test_k9_rebuild_stage.py; the
absence / exposure gates in test_executor_k9_stage_policy.py. THIS file proves how the executor admits and runs the kind. Root CLAUDE.md §N.8: each claim is measured by a detector that can
read false, so each oracle passes on the real executor and FAILS on a copy of executor.py with that ONE claim's line reverted.

  E1 the staging is a build: it is refused `owner_go_missing` without the owner's go bound to the request, and admitted with it; the dry run needs none
  E2 the absence / exposure gates run inside validate: a request without the readbacks is refused although the owner's go, lease, signer and dry run are all in order
  E3 the staging needs THIS executor's own completed dry run of the same identity (a signer's attestation alone never admits it)
  E4 the reviewed policy is loaded from the request's merged commit (git show), not from a working tree: an unreadable policy refuses
  E5 the child is `python -m services.kala_core.rebuild_stage stage --assets .. --run-id .. --natal-build .. --expected-head ..` in platform/python-sidecar and holds the builder's
     connection only
  E6 it is a production write that needs a signer (or a verified pack fill), a live lease and the canonical chart, and it is neither a deletion nor a serving change
"""
import json
from types import SimpleNamespace

import pytest

import k9_stage_cases as C
import test_executor_mechanical_production as M
from owner_go_cases import write_owner_go
from test_executor_table import ALL_CAPS, _git

POLICY_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/k9_stage_policy.py"
KIND = "k9_rebuild_stage"


def policy_text():
    from pathlib import Path
    return (Path(__file__).resolve().parents[1] / "k9_stage_policy.py").read_text()


def commit_policy(w, text):
    """The reviewed (merged) commit the executor loads the policy from: the temporary origin/main gains the policy file; `w.reviewed` becomes that commit."""
    path = w.repo / POLICY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    _git(w.repo, "add", "-A")
    _git(w.repo, "commit", "-q", "-m", "k9 stage policy")
    _git(w.repo, "push", "-q", "origin", "main")
    _git(w.repo, "fetch", "-q", "origin")
    w.reviewed = _git(w.repo, "rev-parse", "HEAD")


def archive_dry_run(w, req, oid="dry-stage", status="COMPLETED", exit_code=0):
    dreq = {"operation_id": oid, "kind": KIND + "_dryrun", "item_id": req["item_id"], "idempotency_key": "k-" + oid, "requested_by": "adhikarin", "kyd": "kyd-1",
            "args": dict(req["args"]), "chart_id": req["chart_id"], "reviewed_commit": req["reviewed_commit"]}
    (w.mod.DONE / f"{oid}.json").write_text(json.dumps(dreq))
    output = json.dumps({"status": "ROLLED_BACK", "rollback_confirmed": True}) + "\n"
    (w.mod.REC / f"{oid}.output.txt").write_text(output)
    record = {"operation_id": oid, "kind": dreq["kind"], "item_id": req["item_id"], "status": status, "reason": "", "exit_code": exit_code, "ts": M.iso(seconds=-30),
              "reviewed_commit": req["reviewed_commit"], "request_sha256": w.mod.request_digest(dreq), "output_sha256": M.sha(output)}
    body = json.dumps(record, indent=1).encode()
    (w.mod.REC / f"{oid}.json").write_bytes(body)
    return {"name": f"{oid}.json", "sha256": M.sha(body)}


def world(tmp_path, monkeypatch, mutation=None, policy=None):
    w, table = M.build(tmp_path, monkeypatch, mutation)
    commit_policy(w, policy_text() if policy is None else policy)
    return w, w.table()


def staged_request(w, with_go=True, with_dry=True, with_readbacks=True, **over):
    """A K9-4b staging request that every OTHER admission check accepts; the keyword switches take one piece away."""
    ops = C.Ops(w.mod.OPS)
    req = w.production_request(KIND, item_id="K9-4b", operation_id="op-stage", idempotency_key="k-stage", args=dict(C.ARGS))
    if with_readbacks:
        req["absence_readback"] = ops.readback("rb-absence", C.absence_evidence(), C.policy.absence_sql(C.RUN))
        req["exposure_readback"] = ops.readback("rb-exposure", C.exposure_evidence(), C.policy.exposure_sql(C.RUN))
    if with_dry:
        req["dryrun_receipt"] = archive_dry_run(w, req)
    req.update(over)
    accepted = w.accept(req)
    if with_go:
        write_owner_go(w.mod, accepted)
    return accepted


def judged(w, table, req):
    return w.mod.validate(req, table, ALL_CAPS)


# ------------------------------------------------------------------ oracles


def oracle_e1_the_staging_is_a_build(w, table):
    req = staged_request(w, with_go=False)
    assert judged(w, table, req) == "owner_go_missing"
    write_owner_go(w.mod, req)
    assert judged(w, table, req) is None, "control failed — a fully gated staging with the owner's go is admitted"
    write_owner_go(w.mod, req, request_sha256="0" * 64)
    assert judged(w, table, req) == "owner_go_mismatch: request_sha256"
    dry = w.production_request(KIND + "_dryrun", item_id="K9-4b", operation_id="op-dry", idempotency_key="k-dry", args=dict(C.ARGS))
    assert judged(w, table, dry) is None, "the dry run persists nothing and needs no go"


def oracle_e2_the_gates_run_inside_validate(w, table):
    assert judged(w, table, staged_request(w)) is None, "control failed"
    why = judged(w, table, staged_request(w, with_readbacks=False, operation_id="op-stage-2", idempotency_key="k-stage-2"))
    assert why and "absence_readback" in why, why


def oracle_e3_the_staging_needs_its_own_dry_run(w, table):
    assert judged(w, table, staged_request(w)) is None, "control failed"
    req = staged_request(w, with_dry=False, operation_id="op-nodry", idempotency_key="k-nodry")
    assert "dryrun_receipt" in (judged(w, table, req) or "")
    failed = staged_request(w, with_dry=False, operation_id="op-faildry", idempotency_key="k-faildry")
    failed["dryrun_receipt"] = archive_dry_run(w, failed, oid="dry-failed", status="FAILED", exit_code=3)
    failed = w.accept(failed)
    write_owner_go(w.mod, failed)
    assert "did not COMPLETE OK" in (judged(w, table, failed) or "")


def oracle_e6_a_production_write_needs_a_signer_and_a_lease(w, table):
    req = staged_request(w)
    assert judged(w, table, req) is None, "control failed"
    unsigned = {k: v for k, v in req.items() if k != "acceptance_receipt"}
    assert "pre-acceptance receipt missing" in (judged(w, table, unsigned) or "")
    assert "lease" in (judged(w, table, {**req, "lease_id": "no-such-lease"}) or "")
    assert "canonical chart" in (judged(w, table, {**req, "chart_id": "362f9f17-0000-4000-8000-000000000000"}) or "")
    assert KIND not in w.mod.SIGNED_ONLY_KINDS and not w.mod.mechanical_exempt(KIND), "a staging is neither a serving change nor a deletion"


# claim -> (oracle, the ONE planted reversion of executor.py that must make it fail)
ORACLES = {
    "e1": (oracle_e1_the_staging_is_a_build, ('    "k9_rebuild_stage",\n    "orchestrator_rebuild",\n})\nOWNER_GO_DIR', '    "orchestrator_rebuild",\n})\nOWNER_GO_DIR')),
    "e2": (oracle_e2_the_gates_run_inside_validate, ("        lambda: k9_rebuild_stage_problem(req, table),\n", "")),
    "e3": (oracle_e3_the_staging_needs_its_own_dry_run, ('    if why or req["kind"] != "k9_rebuild_stage": return why\n    return dry_run_check(req, table)[0]\n', '    return why\n')),
}


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_executor(tmp_path, monkeypatch, claim):
    w, table = world(tmp_path, monkeypatch)
    ORACLES[claim][0](w, table)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, mutation = ORACLES[claim]
    w, table = world(tmp_path, monkeypatch, mutation)
    with pytest.raises(AssertionError):
        oracle(w, table)


def test_e6_a_production_write_needs_a_signer_a_lease_and_the_canonical_chart(tmp_path, monkeypatch):
    w, table = world(tmp_path, monkeypatch)
    oracle_e6_a_production_write_needs_a_signer_and_a_lease(w, table)


def test_e4_an_unreadable_reviewed_policy_refuses(tmp_path, monkeypatch):
    w, table = world(tmp_path, monkeypatch)
    req = staged_request(w)
    assert judged(w, table, req) is None, "control failed"
    broken = dict(req, reviewed_commit="0" * 40)          # a commit the repository does not hold: the policy cannot be loaded from it
    assert judged(w, table, broken) is not None
    (tmp_path / "b").mkdir()
    w2, table2 = world(tmp_path / "b", monkeypatch, policy="raise RuntimeError('broken policy')\n")
    assert judged(w2, table2, staged_request(w2)) == "reviewed K9 staging policy unavailable or invalid"


def test_e4_the_policy_is_read_from_the_reviewed_commit_not_from_a_working_tree(tmp_path, monkeypatch):
    """A permissive policy in the working tree never counts: only the merged commit's bytes do."""
    w, table = world(tmp_path, monkeypatch, policy=policy_text().replace("def request_problem(req: dict, ops, accepted_readback, now: dt.datetime | None = None) -> str | None:",
                                                                      "def request_problem(req: dict, ops, accepted_readback, now: dt.datetime | None = None) -> str | None:\n    return 'reviewed policy says no'"))
    assert judged(w, table, staged_request(w)) == "reviewed policy says no"


@pytest.mark.parametrize("kind", [KIND, KIND + "_dryrun"])
def test_e5_the_child_runs_the_staging_module_with_the_builder_connection_only(tmp_path, monkeypatch, kind):
    w, table = world(tmp_path, monkeypatch)
    for name, value in {"KY_BUILDER_DATABASE_URL": "builder-fixture", "KY_LAYER_VERIFIER_DATABASE_URL": "verifier-fixture", "KY_OWNER_DATABASE_URL": "owner-fixture"}.items():
        monkeypatch.setenv(name, value)
    seen = {}
    monkeypatch.setattr(w.mod, "git", lambda *a, **k: SimpleNamespace(returncode=0, stderr="", stdout=""))
    monkeypatch.setattr(w.mod, "run_group", lambda argv, cwd, env, timeout: seen.update(argv=argv, cwd=cwd, env=env) or SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(w.mod, "apply_generated_overlay", lambda root, commit, env, timeout=600: ({"schema": "ky.generated_overlay/1", "files": {}}, ""))
    request = {"operation_id": "fixture", "kind": kind, "reviewed_commit": "a" * 40, "args": dict(C.ARGS)}
    assert w.mod.execute(request, table[kind])[0] == 0
    tail = [part for name, value in C.ARGS.items() for part in ("--" + name, value)]
    assert seen["argv"] == [w.mod.PY, "-m", "services.kala_core.rebuild_stage", table[kind]["fixed_args"][0]] + tail
    assert table[kind]["fixed_args"] == (["stage"] if kind == KIND else ["stage-dryrun"])
    assert seen["cwd"].name == "python-sidecar" and seen["cwd"].parent.name == "platform"
    assert seen["env"]["DATABASE_URL"] == "builder-fixture" and not {"KY_BUILDER_DATABASE_URL", "KY_LAYER_VERIFIER_DATABASE_URL", "KY_OWNER_DATABASE_URL"} & set(seen["env"])
    assert "NIRMANA_FORCE_EXECUTE" not in seen["env"]
