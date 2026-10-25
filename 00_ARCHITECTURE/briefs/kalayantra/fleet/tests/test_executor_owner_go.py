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

SR-OWNER-GATE-HARDEN (review of #3902, NB-1 / NB-4 / NB-2): the same ledger, one oracle per distinct claim, each with its ONE planted reversion.
  G10 a row that runs the century launcher (century_launch.py) is gated whatever its kind is called (a `*_dryrun` name included)
  G11 a row that runs the production rebuild entry with `rebuild` / `--force-execute` is gated whatever its kind is called; a row running `rebuild-dryrun` stays free
  G12 a symlink at the go directory or at any parent below the run root is refused `owner_go_mismatch: directory`
  G13 a symlink AT the go file is refused `owner_go_mismatch: file`
  G14 a go without a usable `expires_at` (absent, unparsable, naive, not a string) is refused `owner_go_mismatch: expires_at`
  G15 a go whose `expires_at` is in the past is refused `owner_go_mismatch: expires_at`
  G16 a go whose `expires_at` is more than 12 hours after `written_at` is refused `owner_go_mismatch: expires_at`
  G17 a longer span is accepted only with `owner_span_hours` AND the owner's `owner_span_words` (otherwise `owner_go_mismatch: owner_span_hours`)
  G18 a `written_at` in the future (which would stretch the window) is refused `owner_go_mismatch: written_at`
  G19 run_one judges the go again immediately before execution: a go that has lapsed since admission stops the queued build (REFUSED, nothing executed)
"""
import datetime as dt
import os
import json

import pytest

import test_executor_mechanical_production as M
import test_executor_rebuild_dryrun_detector as D7
from owner_go_cases import write_owner_go
from test_executor_table import ALL_CAPS

CHAIN_LINE = "        lambda: owner_go_problem(req, op),\n"
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
    assert set(w.mod.OWNER_GO_KINDS) == set(GATED) | {"century_resume"}      # SR-RESUME-NOW: a resume is a build too, with its own go (test_executor_century_resume.py judges it; its shipped row is disabled)
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


def renamed(w, table, base_kind, new_kind, **row):
    """A request for the `base_kind` build under another kind name, and a table that carries that name as a copy of base_kind's row (with `row` overrides)."""
    req = request(w, base_kind, operation_id=f"op-{new_kind}", idempotency_key=f"k-{new_kind}")
    req["kind"] = new_kind
    return req, {**table, new_kind: {**table[base_kind], **row}}


def oracle_g10_the_century_launcher_is_gated_by_script(w, table):
    for name in ("quarterly_launch", "century_launch_dryrun"):      # an innocent name, and a name that claims to be dry while running the very same launcher
        req, renamed_table = renamed(w, table, "century_dispatch", name)
        assert judged(w, renamed_table, req) == "owner_go_missing", name
        write_owner_go(w.mod, req)
        assert judged(w, renamed_table, req) is None, f"control failed — {name} with a correctly bound go must be admitted"


def oracle_g11_the_production_rebuild_entry_is_gated_by_script(w, table):
    req, renamed_table = renamed(w, table, "orchestrator_rebuild", "nightly_refresh")
    assert judged(w, renamed_table, req) == "owner_go_missing"
    write_owner_go(w.mod, req)
    assert judged(w, renamed_table, req) is None, "control failed — the renamed rebuild with a correctly bound go must be admitted"
    forced, forced_table = renamed(w, table, "orchestrator_rebuild", "nightly_forced", fixed_args=["--force-execute"])      # the force flag alone is enough
    assert judged(w, forced_table, forced) == "owner_go_missing"
    free = w.mod.validate(w.production_request("orchestrator_rebuild_dryrun", operation_id="op-free", idempotency_key="k-free", args=dict(D7.ARGS)),
                          {**table, "rebuild_rehearsal_dryrun": dict(table["orchestrator_rebuild_dryrun"])}, ALL_CAPS)
    assert free is None, f"control failed — a rebuild-dryrun row is admitted ({free})"
    dry = w.production_request("rebuild_rehearsal_dryrun", operation_id="op-free2", idempotency_key="k-free2", args=dict(D7.ARGS))
    assert w.mod.validate(dry, {**table, "rebuild_rehearsal_dryrun": dict(table["orchestrator_rebuild_dryrun"])}, ALL_CAPS) is None, "a genuinely dry row under another name stays free"


def oracle_g12_a_symlinked_directory_is_refused(w, table):
    mod = w.mod
    req = request(w, "orchestrator_rebuild", operation_id="op-rb", idempotency_key="k-rb")
    write_owner_go(mod, req)
    assert judged(w, table, req) is None, "control failed — the go in a real directory is admitted"
    real = mod.OPS.parent / "elsewhere"
    os.rename(mod.OPS / "owner_go", real)                          # the same bytes, reached through a symlinked owner_go directory
    (mod.OPS / "owner_go").symlink_to(real, target_is_directory=True)
    assert judged(w, table, req) == "owner_go_mismatch: directory"
    (mod.OPS / "owner_go").unlink()
    os.rename(real, mod.OPS / "owner_go")
    assert judged(w, table, req) is None
    parked = mod.OPS.parent / "ops_real"                           # ...and through a symlinked parent (run/ops) below the run root
    os.rename(mod.OPS, parked)
    mod.OPS.symlink_to(parked, target_is_directory=True)
    assert judged(w, table, req) == "owner_go_mismatch: directory"


def oracle_g13_a_symlinked_file_is_refused(w, table):
    req = request(w, "orchestrator_rebuild", operation_id="op-rb", idempotency_key="k-rb")
    write_owner_go(w.mod, req)
    target = w.mod.OPS / "owner_go" / "op-rb.json"
    real = w.mod.OPS / "real-go.json"
    os.rename(target, real)
    target.symlink_to(real)
    assert judged(w, table, req) == "owner_go_mismatch: file"


def at(hours):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=hours)).isoformat(timespec="seconds")


def oracle_g14_an_unusable_expiry_is_refused(w, table):
    for kind in GATED:
        for expiry in (None, "", "tomorrow", (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).replace(tzinfo=None).isoformat(timespec="seconds"), 1893456000):
            req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
            write_owner_go(w.mod, req, expires_at=expiry)
            assert judged(w, table, req) == "owner_go_mismatch: expires_at", (kind, expiry)
        write_owner_go(w.mod, req, expires_at=at(2))
        assert judged(w, table, req) is None, f"control failed — {kind} with a future timezone-qualified expiry is admitted"


def oracle_g15_an_expired_go_is_refused(w, table):
    for kind in GATED:
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        write_owner_go(w.mod, req, written_at=at(-3), expires_at=at(-1))
        assert judged(w, table, req) == "owner_go_mismatch: expires_at", kind
        write_owner_go(w.mod, req, written_at=at(-3), expires_at=at(1))      # control: the same window, still running, is admitted
        assert judged(w, table, req) is None, kind


def oracle_g16_the_default_span_is_twelve_hours(w, table):
    for kind in GATED:
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        write_owner_go(w.mod, req, written_at=at(0), expires_at=at(12.5))
        assert judged(w, table, req) == "owner_go_mismatch: expires_at", kind
        write_owner_go(w.mod, req, written_at=at(0), expires_at=at(11.9))
        assert judged(w, table, req) is None, kind


def oracle_g17_a_longer_span_needs_the_owners_words(w, table):
    for kind in GATED:
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        write_owner_go(w.mod, req, written_at=at(0), expires_at=at(30), owner_span_hours=48, owner_span_words="keep it open for two days")
        assert judged(w, table, req) is None, f"control failed — {kind} with an owner-given 48 h window is admitted"
        write_owner_go(w.mod, req, written_at=at(0), expires_at=at(60), owner_span_hours=48, owner_span_words="keep it open for two days")
        assert judged(w, table, req) == "owner_go_mismatch: expires_at", "past the owner's own span"
        for hours, words in ((48, None), (48, "  "), (0, "x"), (-5, "x"), (True, "x"), ("48", "x"), (float("nan"), "x"), (10 ** 9, "x")):
            write_owner_go(w.mod, req, written_at=at(0), expires_at=at(30), owner_span_hours=hours, owner_span_words=words)
            assert judged(w, table, req) == "owner_go_mismatch: owner_span_hours", (kind, hours, words)


def oracle_g18_a_future_written_at_is_refused(w, table):
    for kind in GATED:
        req = request(w, kind, operation_id=f"op-{kind}", idempotency_key=f"k-{kind}")
        write_owner_go(w.mod, req, written_at=at(30), expires_at=at(35))      # within 12 h of a written_at that has not happened yet: still not a window that started
        assert judged(w, table, req) == "owner_go_mismatch: written_at", kind


def drive_run_one(w, table, req):
    """Run the real run_one on `req` with the transport doubled: returns (receipts written, whether the child was executed)."""
    mod = w.mod
    seen = {"receipts": [], "executed": False}
    mod.sync = lambda: None
    mod.load_table = lambda: table
    mod.capabilities = lambda *a, **k: ALL_CAPS
    mod.mechanical_acceptance = lambda *a, **k: None
    mod.receipt = lambda req, status, reason="", *a, **k: seen["receipts"].append((status, reason))
    mod.execute = lambda req, op: seen.__setitem__("executed", True) or (0, "")
    queued = mod.REQ / f"{req['operation_id']}.json"
    mod.REQ.mkdir(parents=True, exist_ok=True); mod.DONE.mkdir(parents=True, exist_ok=True)
    queued.write_text(json.dumps(req))
    mod.run_one(queued, req, table[req["kind"]])
    return seen["receipts"], seen["executed"]


def oracle_g19_run_one_judges_the_go_again_before_execution(w, table):
    req = request(w, "orchestrator_rebuild", operation_id="op-rb", idempotency_key="k-rb")
    write_owner_go(w.mod, req)
    receipts, executed = drive_run_one(w, table, w.accept(req))
    assert executed and receipts == [("COMPLETED", "")], f"control failed — a bound, unexpired go runs ({receipts})"
    again = request(w, "orchestrator_rebuild", operation_id="op-rb2", idempotency_key="k-rb2")
    write_owner_go(w.mod, again)
    accepted = w.accept(again)
    assert w.mod.validate(accepted, table, ALL_CAPS) is None                    # admitted ...
    write_owner_go(w.mod, again, written_at=at(-3), expires_at=at(-1))        # ... then the window lapses before the worker starts it
    receipts, executed = drive_run_one(w, table, accepted)
    assert not executed and receipts == [("REFUSED", "owner_go_mismatch: expires_at")], (receipts, executed)


# claim -> (oracle, the ONE planted reversion of executor.py that must make it fail)
ORACLES = {
    "g1": (oracle_g1_no_go_no_build, (CHAIN_LINE, "")),
    "g2": (oracle_g2_a_go_for_another_request_digest, ('("request_sha256", request_digest(req)), ', "")),
    "g3": (oracle_g3_a_go_for_another_kind, ('("kind", req.get("kind")), ', "")),
    "g4": (oracle_g4_a_go_for_another_dispatch_head, ('("reviewed_commit", req.get("reviewed_commit")), ', "")),
    "g5": (oracle_g5_no_transcript_citation, ('for field in ("owner_words", "transcript_citation"):', 'for field in ("owner_words",):')),
    "g6": (oracle_g6_the_owner_must_have_said_yes, ('if go.get("owner_yes") is not True:', "if False:")),
    "g7": (oracle_g7_dry_runs_are_not_gated, ('if req.get("kind") in OWNER_GO_KINDS: return True', 'if str(req.get("kind")).startswith(("century_dispatch", "orchestrator_rebuild")): return True')),
    "g8": (oracle_g8_the_gated_set_is_the_two_build_kinds, ('    "orchestrator_rebuild",\n})\nOWNER_GO_DIR', '})\nOWNER_GO_DIR')),
    "g10": (oracle_g10_the_century_launcher_is_gated_by_script, ("    if names & OWNER_GO_SCRIPT_NAMES: return True\n", "")),
    "g11": (oracle_g11_the_production_rebuild_entry_is_gated_by_script, ("        return any(t in OWNER_GO_REBUILD_TOKENS for t in tokens)\n", "        return False\n")),
    "g12": (oracle_g12_a_symlinked_directory_is_refused, ('        if directory.is_symlink(): return "owner_go_mismatch: directory"\n', "")),
    "g13": (oracle_g13_a_symlinked_file_is_refused, ("if path.is_symlink() or not path.is_file():", "if not path.is_file():")),
    "g14": (oracle_g14_an_unusable_expiry_is_refused, ('if expires is None: return "owner_go_mismatch: expires_at"', "if expires is None: expires = now + dt.timedelta(hours=1)")),
    "g15": (oracle_g15_an_expired_go_is_refused, (" or expires <= now: return", ": return")),
    "g16": (oracle_g16_the_default_span_is_twelve_hours, (" or expires - written > dt.timedelta(hours=span)", "")),
    "g17": (oracle_g17_a_longer_span_needs_the_owners_words, ("        span = max(span, hours)\n", "")),
    "g18": (oracle_g18_a_future_written_at_is_refused, ('    if written > now + dt.timedelta(minutes=5): return "owner_go_mismatch: written_at"\n', "")),
    "g19": (oracle_g19_run_one_judges_the_go_again_before_execution, ("        why = validate(req, current_table, capabilities(True), reserved=True)\n        if why:\n            receipt(req, \"REFUSED\", why); return\n", "")),
    "g9": (oracle_g9_nothing_but_the_file_substitutes, ('if not owner_go_gated(req, op): return None', 'if not owner_go_gated(req, op) or os.environ.get("KY_OWNER_GO"): return None')),
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

