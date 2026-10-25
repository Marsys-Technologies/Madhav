"""SR-RESUME-NOW (ruling madhav-f9 lane 2; standing owner requirement OWNER-RESUMABLE-REQUIRED-20261025, "resumable substeps for heavy assets"): the executor's `century_resume`
op kind — a killed or failed century build continued over the substeps its ledger committed, not torn down and rebuilt.

Doctrine: root CLAUDE.md §N.8 (each claim is measured by a detector that can read false) and §B.10 (no invented value); the owner's go rule (OWNER-BUILD-GO-REQUIRED-20261023,
test_executor_owner_go.py) — a resume is a new paid Cloud Run execution of the century job and takes its OWN go. One oracle per distinct production claim; each passes on the real
executor and FAILS on a copy of executor.py with that ONE claim's line reverted (the planted reversion; the pattern of test_executor_owner_go.py). The ledger-attested absence gate
itself (v5_small_test_shared.py) has its own oracles in platform/scripts/__tests__/test_century_resume_gate.py; here the executor is shown to apply it, end to end.

  X1 a century_resume is refused without the owner's go (the kind alone gates it, whatever script its row runs) and admitted with a correctly bound one
  X2 the two gos never cross: a dispatch go does not open a resume, a resume go does not open a dispatch (each otherwise correctly bound)
  X3 a resume takes the production fence a dispatch takes (remote-async), and is modelled on the dispatch row: same principal, capabilities and arguments
  X4 century_cancel covers the execution a century_resume launched (and still not another family's, nor another execution)
  X5 a resume is bound to the committed century contract (its sha at the reviewed commit, its launch_args)
  X6 the request's program identity is the century contract's writer program: a resume of any other program refuses by name
  X7 the executor judges a resume by the ledger-attested absence gate, and a dispatch by the unchanged one
  X10 the resume dry run (staging rollback twin) needs no go, no lease and no acceptance, is judged on the same evidence and the same program as the resume, and its rollback
      proof is only recorded when it names the resume (receipt, run, program) the request names
  X8 the kind is ENABLED (the launcher mode `century_launch.py --resume` exists, tests/test_century_launch_resume.py) and so is its staging-rollback twin
     `century_resume_dryrun`, which is read-only and needs no owner go; reverting the shipped flag refuses the request as not enabled
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import test_executor_table as TT
from owner_go_cases import write_owner_go
from test_executor_table import ALL_CAPS, OPS_FILE, World

REPO = TT.FLEET.parents[3]
sys.path[:0] = [str(REPO / "platform/scripts"), str(REPO / "platform/scripts/__tests__")]
import century_resume_support as S      # noqa: E402  (the evidence fixtures the gate's own tests use)

EXECUTOR_SRC = TT.EXECUTOR_PY
CONTRACT_PATH = "00_ARCHITECTURE/briefs/kalayantra/fleet/century_contract.json"
SHARED_SRC = REPO / "platform/scripts/v5_small_test_shared.py"
DISPATCH_OP = "op-prior-dispatch"


def contract(writer_digest=None):
    doc = {"schema": "ky.century_contract/1", "launch_args": dict(S.ARGS), "image": {"writer_source_digest": writer_digest or S.IDENTITY["writer_digest"]}}
    return (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode()


def build(tmp_path, monkeypatch, mutation=None, contract_blob=None, shipped=False, ops_text=None):
    """The real executor on a temporary origin. `century_resume` is ENABLED in the fixture table (as the shipped row is, X8); the century contract is served at the
    reviewed commit by a git double; the evidence policy is the working tree's v5_small_test_shared.py, exec'd the way the executor execs the reviewed one."""
    if mutation:
        old, new = mutation
        text = EXECUTOR_SRC.read_text()
        if text.count(old) != 1:
            raise RuntimeError(f"mutation anchor not unique: {old!r}")      # a bad anchor must never read as a failed oracle
        mutated = tmp_path / "executor_mutated.py"
        mutated.write_text(text.replace(old, new))
        monkeypatch.setattr(TT, "EXECUTOR_PY", mutated)
    w = World(tmp_path, monkeypatch, ops_text if ops_text is not None else OPS_FILE.read_text() if shipped else TT.copy_with(OPS_FILE.read_text(), "century_resume"))
    for d in (w.mod.REC, w.mod.DONE, w.mod.ACC):
        d.mkdir(parents=True, exist_ok=True)
    blob = contract() if contract_blob is None else contract_blob
    real_git = w.mod.git

    def git(*args, **kwargs):
        if len(args) == 2 and args[0] == "show" and args[1].endswith(":" + CONTRACT_PATH):
            return SimpleNamespace(returncode=0, stdout=blob.decode(), stderr="")
        return real_git(*args, **kwargs)
    monkeypatch.setattr(w.mod, "git", git)
    namespace = {"__name__": "reviewed_smalltest_policy", "__file__": "reviewed_smalltest_policy.py"}
    exec(compile(SHARED_SRC.read_text(), "reviewed small-test evidence policy", "exec"), namespace)
    monkeypatch.setattr(w.mod, "smalltest_policy", lambda req: namespace)
    return w, w.table(), blob


def resume_request(w, blob, **scenario):
    """A century_resume request every admission check accepts, with its evidence written under the executor's own evidence directories; no go and no acceptance yet."""
    sc = S.scenario(w.mod.OPS, **scenario)
    req = w.production_request("century_resume", item_id="J-4e", idempotency_key="key-resume", century_contract_sha256=hashlib.sha256(blob).hexdigest())
    req.update({k: v for k, v in sc.items() if k not in ("kind", "item_id")})
    return req


def says(problem, fragment):
    """A refusal that names `fragment` (a missing refusal is None, which must read as a failed assertion, never a TypeError)."""
    assert isinstance(problem, str) and fragment in problem, problem


def judged(w, table, req, go=True):
    if go:
        write_owner_go(w.mod, req)
    return w.mod.validate(w.accept(req), table, ALL_CAPS)


# ───────────────────────────── X1 / X2 the owner's go ─────────────────────────────
def oracle_x1_a_resume_needs_the_owners_go(w, table, blob):
    ungated = {**table, "century_resume": {**table["century_resume"], "script": "platform/scripts/some_other_launcher.py"}}      # the KIND alone must gate it, not the script it runs
    req = resume_request(w, blob)
    assert judged(w, ungated, req, go=False) == "owner_go_missing"
    assert judged(w, ungated, req) is None, "control failed — a resume with a correctly bound go must be admitted"


def oracle_x2_the_two_gos_do_not_cross(w, table, blob):
    resume = resume_request(w, blob)
    write_owner_go(w.mod, resume, kind="century_dispatch")                # a go the owner gave for a DISPATCH, otherwise bound to this very request
    assert w.mod.validate(w.accept(resume), table, ALL_CAPS) == "owner_go_mismatch: kind"
    write_owner_go(w.mod, resume)
    assert w.mod.validate(w.accept(resume), table, ALL_CAPS) is None, "control failed — its own go opens it"
    dispatch = w.production_request("century_dispatch", operation_id="op-dispatch", idempotency_key="key-dispatch", item_id="J-4e", args={"classes": "all"})
    w.mod.century_contract_problem = lambda req: None                     # the dispatch's own gates have their own tests; this oracle judges the go
    w.mod.smalltest_policy_problem = lambda req: None
    write_owner_go(w.mod, dispatch, kind="century_resume")                # a go the owner gave for a RESUME, otherwise bound to this dispatch
    assert w.mod.validate(w.accept(dispatch), table, ALL_CAPS) == "owner_go_mismatch: kind"
    write_owner_go(w.mod, dispatch)
    assert w.mod.validate(w.accept(dispatch), table, ALL_CAPS) is None, "control failed — its own go opens it"


# ───────────────────────────── X3 the fence and the model row ─────────────────────────────
def oracle_x3_a_resume_is_fenced_like_a_dispatch(w, table, blob):
    assert w.mod.remote_async("century_resume", {}) is True            # even if a table drops its `remote_async` flag
    assert w.mod.remote_async("century_dispatch_dryrun", {}) is False
    assert "century_resume" in w.mod.REMOTE_ASYNC_KINDS
    resume, dispatch = table["century_resume"], table["century_dispatch"]
    for field in ("needs", "also_needs", "allowed_args", "production", "remote_async", "timeout_s"):
        assert resume.get(field) == dispatch.get(field), field
    assert w.mod.LAUNCH_SCHEMAS["century_resume"] == w.mod.LAUNCH_SCHEMAS["century_dispatch"] == "ky.century_launch/1"      # its launch evidence is the dispatch's, so a cancel reads it alike


# ───────────────────────────── X4 the cancel ─────────────────────────────
def cite(w, folder, name, doc):
    path = w.mod.OPS / folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(doc, sort_keys=True).encode()
    path.write_bytes(body)
    return {"name": name, "sha256": hashlib.sha256(body).hexdigest()}


def cancel_request(w, kind, receipt_kind="century_resume", execution="brahma-build-pipeline-job-abc12", target=None):
    receipt = {"operation_id": DISPATCH_OP, "kind": receipt_kind, "item_id": "J-4e", "status": "COMPLETED", "exit_code": 0,
               "launch": {"schema": "ky.century_launch/1", "status": "LAUNCHED", "execution_name": execution}}
    return {"operation_id": "op-cancel", "kind": kind, "item_id": "J-4e", "args": {"execution": target or execution},
            "dispatch_receipt": cite(w, "receipts", f"{DISPATCH_OP}.json", receipt),
            "verdict": cite(w, "verdicts", "abort.json", {"schema": "ky.reproject_verdict/1", "verdict": "ABORT"})}


def oracle_x4_a_century_cancel_covers_a_resume(w, table, blob):
    assert "century_cancel" in w.mod.CANCEL_LANE_KINDS                  # it runs on the cancel lane, never behind the fence the resume holds
    for kind in ("century_cancel", "century_cancel_dryrun"):
        assert w.mod.measuring_cancel_problem(cancel_request(w, kind)) is None, kind
        problem = w.mod.measuring_cancel_problem(cancel_request(w, kind, target="brahma-build-pipeline-job-zzz99"))
        assert problem and "not the execution named in the cited" in problem, (kind, problem)
    foreign = w.mod.measuring_cancel_problem(cancel_request(w, "century_cancel", receipt_kind="measuring_dispatch"))
    assert foreign and "COMPLETED launch" in foreign                    # another family's launch receipt still cancels nothing of the century's
    unrelated = w.mod.measuring_cancel_problem(cancel_request(w, "century_cancel", receipt_kind="century_teardown"))
    assert unrelated and "COMPLETED launch" in unrelated


# ───────────────────────────── X5 / X6 the contract ─────────────────────────────
def oracle_x5_a_resume_is_bound_to_the_century_contract(w, table, blob):
    req = resume_request(w, blob)
    assert w.mod.century_contract_problem(req) is None, "control failed — the sha of the blob at the reviewed commit"
    says(w.mod.century_contract_problem({**req, "century_contract_sha256": "0" * 64}), "does not equal the sha256 of fleet/century_contract.json")
    says(w.mod.century_contract_problem({**req, "century_contract_sha256": None}), "century_contract_sha256 (64 lowercase hex) is required")
    says(w.mod.century_contract_problem({**req, "args": dict(S.ARGS, final_rules="false")}), "differ from the century contract's launch_args")


def oracle_x6_the_program_identity_is_the_contracts_writer_program(w, table, blob):
    req = resume_request(w, blob)
    assert w.mod.century_contract_problem(req) is None, "control failed — the request's writer_digest is the contract's writer_source_digest"
    other = dict(req, program_identity=dict(req["program_identity"], writer_digest="1" * 64))
    says(w.mod.century_contract_problem(other), "program_identity.writer_digest differs from the century contract's writer_source_digest")
    says(w.mod.century_contract_problem({k: v for k, v in req.items() if k != "program_identity"}), "program_identity.writer_digest differs")      # no program identity at all


# ───────────────────────────── X7 the absence gate, applied by the executor ─────────────────────────────
def oracle_x7_the_executor_judges_a_resume_by_the_ledger_gate(w, table, blob):
    assert judged(w, table, resume_request(w, blob)) is None, "control failed — a ledger-attested partial chain, the contract's program, the owner's go: admitted"
    census = S.census_of(S.ledger_rows())
    census["ka_gochara_contact"] += 1                                   # one row no committed substep accounts for
    extra = resume_request(w, blob, census=census, operation_id="resume-extra")
    says(judged(w, table, extra), "unattested rows in ka_gochara_contact")
    mismatch = resume_request(w, blob, identity=dict(S.IDENTITY, writer_digest="1" * 64), operation_id="resume-other-program")      # the ledger was written by another program than the request (= the contract) names
    problem = judged(w, table, mismatch)
    says(problem, "writer_digest"); says(problem, "differs from the ledger")
    none = resume_request(w, blob, rows=[], operation_id="resume-no-ledger")
    says(judged(w, table, none), "nothing to resume")
    # a century_dispatch is judged by the UNCHANGED absence gate: a partly present chain refuses
    partial = S.absence(w.mod.OPS, counts_over={"ka_gochara_contact": 3}, name="absence-partial")
    dispatch = w.production_request("century_dispatch", operation_id="op-dispatch-partial", idempotency_key="key-dispatch-partial", item_id="J-4e", args=dict(S.ARGS),
                                    century_contract_sha256=hashlib.sha256(blob).hexdigest(), **partial)
    says(judged(w, table, dispatch), "independent absence")


# ───────────────────────────── X8 shipped enabled ─────────────────────────────
def oracle_x8_the_shipped_rows_are_enabled(w, table, blob):
    """The shipped table (executor_ops.json as merged), not a fixture: the resume row is enabled and a correctly evidenced, owner-approved resume is ADMITTED by it; its
    staging-rollback twin is enabled, read-only (`production: false`) and runs the resume staging binding in dry-run mode, never the launcher."""
    assert table["century_resume"]["enabled"] is True
    twin = table["century_resume_dryrun"]
    assert (twin["enabled"], twin["production"], twin["needs"]) == (True, False, "builder")
    assert twin["script"] == "platform/scripts/dispatch_v5_century_resume_job.py" and twin["fixed_args"] == ["--i-am-steward", "--after-settled-1", "--dry-run"]
    assert table["century_resume"]["script"].endswith("fleet/century_launch.py") and table["century_resume"]["fixed_args"] == ["--resume"]
    assert judged(w, table, resume_request(w, blob)) is None, "the shipped row must admit a correctly evidenced resume with the owner's go"


# ───────────────────────────── X9 the launch evidence ─────────────────────────────
def oracle_x9_the_resume_launch_is_recorded_like_a_dispatch_launch(w, table, blob):
    """receipt(): a COMPLETED century_resume child whose output carries the launcher's ky.century_launch/1 record is recorded with that `launch` (a cancel and a further resume
    cite it); one without it is FAILED, exactly as for a dispatch (exit zero is not launch evidence)."""
    launch = {"schema": "ky.century_launch/1", "status": "LAUNCHED", "chart_id": TT.CANONICAL_CHART, "asset_id": "ka_gochara_v5", "run_id": S.NEW_RUN,
              "execution_name": "brahma-build-pipeline-job-abc12", "plan_manifest_digest": "f" * 64}
    (w.mod.KY_ROOT / "logs").mkdir(parents=True, exist_ok=True)
    for output, expected in ((json.dumps(launch) + "\n", "COMPLETED"), ("no launch record\n", "FAILED")):
        req = w.production_request("century_resume", operation_id=f"op-{expected}", idempotency_key=f"k-{expected}", item_id="J-4e", args=dict(S.ARGS))
        w.mod.receipt(req, "COMPLETED", "", 0, output)
        record = json.loads((w.mod.REC / f"op-{expected}.json").read_text())
        assert record["status"] == expected, record
        assert (record.get("launch") == launch) is (expected == "COMPLETED"), record


# ───────────────────────────── X10 the resume dry run ─────────────────────────────
def oracle_x10_the_resume_dry_run_is_free_and_its_proof_is_bound(w, table, blob):
    live = resume_request(w, blob)
    dry = {k: v for k, v in live.items() if k not in ("lease_id", "expires_at")}
    dry.update(kind="century_resume_dryrun", operation_id="op-dry", idempotency_key="key-dry")
    assert w.mod.validate(dry, table, ALL_CAPS) is None, "control failed — no go, no lease, no acceptance: a read-only staging rollback"
    assert w.mod.owner_go_problem(dry, table["century_resume_dryrun"]) is None
    assert w.mod.remote_async("century_resume_dryrun", table["century_resume_dryrun"]) is False
    other = dict(dry, program_identity=dict(dry["program_identity"], writer_digest="1" * 64), operation_id="op-dry-other", idempotency_key="key-dry-other")
    says(w.mod.validate(other, table, ALL_CAPS), "program_identity.writer_digest differs from the century contract's writer_source_digest")
    (w.mod.KY_ROOT / "logs").mkdir(parents=True, exist_ok=True)
    manifest = {"chart_id": TT.CANONICAL_CHART, "scope_target": "ka_gochara_v5"}
    bound = {"resumes": dry["resumes"]["name"], "resume_run_id": dry["resume_run_id"], "program_identity": dry["program_identity"]}

    def proof(resume):
        doc = {"schema": "ky.century_staging/1", "status": "ROLLED_BACK", "rollback_confirmed": True, "operation_id": dry["operation_id"], "request_sha256": w.mod.request_digest(dry),
               "args": dry["args"], "triggered_by": "gochara-v5-century", "plan_manifest": manifest, "plan_manifest_digest": w.mod.digest_bytes(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode())}
        if resume is not None:
            doc["resume"] = resume
        return json.dumps(doc) + "\n"
    for resume, expected in ((bound, "COMPLETED"), (None, "FAILED"), (dict(bound, resume_run_id=S.NEW_RUN), "FAILED")):
        w.mod.receipt(dry, "COMPLETED", "", 0, proof(resume))
        record = json.loads((w.mod.REC / "op-dry.json").read_text())
        assert record["status"] == expected, (resume, record)


# claim -> (oracle, the ONE planted reversion of executor.py that must make it fail)
ORACLES = {
    "x1": (oracle_x1_a_resume_needs_the_owners_go, ('    "century_resume",\n    "orchestrator_rebuild",\n', '    "orchestrator_rebuild",\n')),
    "x2": (oracle_x2_the_two_gos_do_not_cross, ('("kind", req.get("kind")), ', "")),
    "x3": (oracle_x3_a_resume_is_fenced_like_a_dispatch, ('    "century_resume",\n    "measuring_dispatch",\n', '    "measuring_dispatch",\n')),
    "x4": (oracle_x4_a_century_cancel_covers_a_resume, ('"also_dispatch": ("century_resume",), ', "")),
    "x5": (oracle_x5_a_resume_is_bound_to_the_century_contract, ('"century_dispatch_dryrun", "century_resume", "century_resume_dryrun"): return None', '"century_dispatch_dryrun"): return None')),
    "x6": (oracle_x6_the_program_identity_is_the_contracts_writer_program, ('if req.get("kind") in ("century_resume", "century_resume_dryrun"):      # SR-RESUME-NOW', 'if False:      # SR-RESUME-NOW')),
    "x7": (oracle_x7_the_executor_judges_a_resume_by_the_ledger_gate,
           ('"century_dispatch", "century_dispatch_dryrun", "century_resume", "century_resume_dryrun", "century_teardown", "century_teardown_dryrun"):\n        return None',
            '"century_dispatch", "century_dispatch_dryrun", "century_teardown", "century_teardown_dryrun"):\n        return None')),
    "x10": (oracle_x10_the_resume_dry_run_is_free_and_its_proof_is_bound, ('and (req["kind"] != "century_resume_dryrun"', 'and (True or req["kind"] != "century_resume_dryrun"')),
    "x9": (oracle_x9_the_resume_launch_is_recorded_like_a_dispatch_launch, ('"measuring_dispatch", "century_dispatch", "century_resume") and status == "COMPLETED":', '"measuring_dispatch", "century_dispatch") and status == "COMPLETED":')),
}


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_executor(tmp_path, monkeypatch, claim):
    w, table, blob = build(tmp_path, monkeypatch)
    ORACLES[claim][0](w, table, blob)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, mutation = ORACLES[claim]
    w, table, blob = build(tmp_path, monkeypatch, mutation)
    with pytest.raises(AssertionError):
        oracle(w, table, blob)


def test_x8_the_shipped_rows_are_enabled(tmp_path, monkeypatch):
    w, table, blob = build(tmp_path, monkeypatch, shipped=True)
    oracle_x8_the_shipped_rows_are_enabled(w, table, blob)


def test_x8_fails_on_its_planted_reversion_the_flag_flipped_back(tmp_path, monkeypatch):
    shipped = OPS_FILE.read_text()
    row = '"century_resume":               {"enabled": true,'
    assert shipped.count(row) == 1
    w, table, blob = build(tmp_path, monkeypatch, ops_text=shipped.replace(row, row.replace("true", "false")))
    with pytest.raises(AssertionError):
        oracle_x8_the_shipped_rows_are_enabled(w, table, blob)
    says(judged(w, table, resume_request(w, blob)), "kind century_resume is not enabled (enabled_by J-4d)")
