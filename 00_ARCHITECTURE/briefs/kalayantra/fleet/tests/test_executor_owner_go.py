"""OWNER-BUILD-GO-REQUIRED-20261023: the executor starts the actual build only on the owner's explicit go.

Doctrine: the owner's decision (run/DECISIONS_SURROGATE.jsonl, OWNER-BUILD-GO-REQUIRED-20261023, verbatim) — "before you start the actual build, take my permission. Anything else, trial, all of that, you can
continue, but before you start the actual build, take my explicit approval" — held for the century dispatch and K9-4b's production rebuild; root CLAUDE.md §N.8 (each claim is measured by a detector that
can read false). One oracle per distinct production claim. Each passes on the real executor and FAILS on a copy of executor.py with that ONE claim's line reverted (the planted reversion; the
pattern of test_executor_rebuild_dryrun_detector.py).

  G1 a century dispatch / production rebuild with no go file is refused `owner_go_missing`; with a correctly bound file it is admitted
  G2 a go file bound to another request digest is refused `owner_go_mismatch: request_sha256`
  G3 a go file naming another kind is refused `owner_go_mismatch: kind`
  G4 a go file naming another dispatch head is refused `owner_go_mismatch: reviewed_commit`
  G5 a go file with an empty transcript citation is refused `owner_go_mismatch: transcript_citation`
  G6 a go file whose owner_yes is not true is refused `owner_go_mismatch: owner_yes`
  G7 the dry-run siblings are NOT gated
  G8 the rebuild is gated exactly as the century dispatch is (each kind's membership of the gated set)
  G9 nothing but the file substitutes: an environment flag and an earlier approval file admit nothing
"""
import json

import pytest

import test_executor_mechanical_production as M
import test_executor_rebuild_dryrun_detector as D7
from owner_go_cases import write_owner_go
from test_executor_table import ALL_CAPS

CHAIN_LINE = "        lambda: owner_go_problem(req),\n"
GATED = ("orchestrator_rebuild", "century_dispatch")


def request(w, kind, **over):
    """A production request of `kind` that every other admission check accepts (the owner go is the only missing piece), with its acceptance NOT yet attached."""
    if kind == "orchestrator_rebuild":
        req = w.production_request(kind, args=dict(D7.ARGS), **over)
        req["dryrun_receipt"] = D7.archive_dry_run(w, req)
    else:
        w.mod.century_contract_problem = lambda req: None        # the contract gate and the evidence policy have their own tests; this file judges the owner go
        w.mod.smalltest_policy_problem = lambda req: None
        req = w.production_request(kind, args={"classes": "all"}, item_id="J-4e", **over)
    return req


def judged(w, table, req):
    return w.mod.validate(w.accept(req), table, ALL_CAPS)


def oracle_g1_no_go_no_build(w, table):
    for kind in GATED:
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        assert judged(w, table, req) == "owner_go_missing", kind
        write_owner_go(w.mod, req)
        assert judged(w, table, req) is None, f"control failed — {kind} with a correctly bound go must be admitted"


def oracle_g2_a_go_for_another_request_digest(w, table):
    for kind in GATED:
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        write_owner_go(w.mod, req, request_sha256="0" * 64)
        assert judged(w, table, req) == "owner_go_mismatch: request_sha256", kind
        write_owner_go(w.mod, req)                              # the same request, bound correctly, is admitted (control)
        assert judged(w, table, req) is None, kind
        changed = {**req, "kyd": "another-kyd"}                 # a request changed after the owner said yes no longer matches the file
        assert judged(w, table, changed) == "owner_go_mismatch: request_sha256", kind


def oracle_g3_a_go_for_another_kind(w, table):
    for kind in GATED:
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        write_owner_go(w.mod, req, kind=next(k for k in GATED if k != kind))
        assert judged(w, table, req) == "owner_go_mismatch: kind", kind


def oracle_g4_a_go_for_another_dispatch_head(w, table):
    for kind in GATED:
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        write_owner_go(w.mod, req, reviewed_commit="a" * 40)
        assert judged(w, table, req) == "owner_go_mismatch: reviewed_commit", kind


def oracle_g5_no_transcript_citation(w, table):
    for kind in GATED:
        for citation in ("", "   ", None):
            req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
            write_owner_go(w.mod, req, transcript_citation=citation)
            assert judged(w, table, req) == "owner_go_mismatch: transcript_citation", (kind, citation)


def oracle_g6_the_owner_must_have_said_yes(w, table):
    for kind in GATED:
        for yes in (False, "true", 1, None):
            req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
            write_owner_go(w.mod, req, owner_yes=yes)
            assert judged(w, table, req) == "owner_go_mismatch: owner_yes", (kind, yes)


def oracle_g7_dry_runs_are_not_gated(w, table):
    rebuild = request(w, "orchestrator_rebuild", operation_id="op-rb", idempotency_key="k-rb")
    dry = w.mod.validate(w.production_request("orchestrator_rebuild_dryrun", operation_id="op-dry", idempotency_key="k-dry", args=dict(D7.ARGS)), table, ALL_CAPS)
    assert dry is None, f"control failed — a rebuild dry run is admitted ({dry})"
    assert judged(w, table, rebuild) == "owner_go_missing", "premise: the production rebuild beside it is gated"
    w.mod.century_contract_problem = lambda req: None
    w.mod.smalltest_policy_problem = lambda req: None
    century_dry = w.production_request("century_dispatch_dryrun", operation_id="op-cdry", idempotency_key="k-cdry", args={"classes": "all"}, item_id="J-4e")
    assert w.mod.validate(century_dry, table, ALL_CAPS) is None


def oracle_g8_the_gated_set_is_the_two_build_kinds(w, table):
    assert set(w.mod.OWNER_GO_KINDS) == set(GATED)
    for kind in GATED:                                          # each member is gated on its own: the other's go file does not open it
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        assert judged(w, table, req) == "owner_go_missing", kind


def oracle_g9_nothing_but_the_file_substitutes(w, table, monkeypatch):
    monkeypatch.setenv("KY_OWNER_GO", "1")
    monkeypatch.setenv("OWNER_GO", "1")
    (w.mod.OPS / "OWNER-CLOUD-RUNS-APPROVED.json").write_text(json.dumps({"owner_yes": True}))
    (w.mod.OPS / "owner_go").mkdir(parents=True, exist_ok=True)
    (w.mod.OPS / "owner_go" / "unrelated-operation.json").write_text("{}")
    for kind in GATED:
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        assert judged(w, table, req) == "owner_go_missing", kind


# claim -> (oracle, the ONE planted reversion of executor.py that must make it fail)
ORACLES = {
    "g1": (oracle_g1_no_go_no_build, (CHAIN_LINE, "")),
    "g2": (oracle_g2_a_go_for_another_request_digest, ('("request_sha256", request_digest(req)), ', "")),
    "g3": (oracle_g3_a_go_for_another_kind, ('("kind", req.get("kind")), ', "")),
    "g4": (oracle_g4_a_go_for_another_dispatch_head, ('("reviewed_commit", req.get("reviewed_commit")), ', "")),
    "g5": (oracle_g5_no_transcript_citation, ('for field in ("owner_words", "transcript_citation"):', 'for field in ("owner_words",):')),
    "g6": (oracle_g6_the_owner_must_have_said_yes, ('if go.get("owner_yes") is not True:', "if False:")),
    "g7": (oracle_g7_dry_runs_are_not_gated, ('if req.get("kind") not in OWNER_GO_KINDS: return None', 'if not str(req.get("kind")).startswith(("century_dispatch", "orchestrator_rebuild")): return None')),
    "g8": (oracle_g8_the_gated_set_is_the_two_build_kinds, ('    "orchestrator_rebuild",\n})\nOWNER_GO_DIR', '})\nOWNER_GO_DIR')),
    "g9": (oracle_g9_nothing_but_the_file_substitutes, ('if req.get("kind") not in OWNER_GO_KINDS: return None', 'if req.get("kind") not in OWNER_GO_KINDS or os.environ.get("KY_OWNER_GO"): return None')),
}


def run(oracle, w, table, monkeypatch):
    if oracle is oracle_g9_nothing_but_the_file_substitutes:
        oracle(w, table, monkeypatch)
    else:
        oracle(w, table)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_executor(tmp_path, monkeypatch, claim):
    w, table = M.build(tmp_path, monkeypatch)
    run(ORACLES[claim][0], w, table, monkeypatch)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, mutation = ORACLES[claim]
    w, table = M.build(tmp_path, monkeypatch, mutation)
    with pytest.raises(AssertionError):
        run(oracle, w, table, monkeypatch)


def test_the_go_is_judged_again_immediately_before_execution(tmp_path, monkeypatch):
    """run_one re-validates with reserved=True: deleting the file after admission stops the queued build (the owner can withdraw the go)."""
    w, table = M.build(tmp_path, monkeypatch)
    req = request(w, "orchestrator_rebuild", operation_id="op-rb", idempotency_key="k-rb")
    write_owner_go(w.mod, req)
    accepted = w.accept(req)
    assert w.mod.validate(accepted, table, ALL_CAPS, reserved=True) is None
    (w.mod.OPS / "owner_go" / "op-rb.json").unlink()
    assert w.mod.validate(accepted, table, ALL_CAPS, reserved=True) == "owner_go_missing"
