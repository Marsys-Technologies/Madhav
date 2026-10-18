"""Amendment A8 (§3.8–§3.11, §5) executor changes — one fail-on-revert oracle per change.

Each test fails with its change reverted and passes with it. Nothing here touches a real repository, a credential or the running
executor: the loop tests run the real main() on a temporary KY_ROOT with git, the table, validate and execute doubled; the admission
tests run the real validate against a throwaway repository (test_executor_table.World); the tree tests run the real execute /
execute_lane against test_executor_overlay's fixture repository.

  1. a refused refresh does not stop admissions: a queued read-only request still runs, the refusal is logged REFRESH_REFUSED;
  2. request_digest excludes acceptance_receipt, expires_at and any *_expires_at field — an extension voids no acceptance — and
     the signer's (kyd_kinds_ops) and the children's (v5_small_test_shared) mirrors agree byte for byte;
  3. no acceptance age cap: an acceptance is valid from its timestamp until the request's expires_at;
  4. preconditions: required_rows and restore_verified retired; backup_taken only for *_teardown; dry_run_passed for a mutating kind;
  5. *_dryrun kinds are production:false — admitted with no lease, acceptance, chart_id or fence; refused without a merged
     reviewed_commit; run in that reviewed tree with the generated overlay; the receipt still fails without the rollback proof;
  6. the fence is set only for a remote-asynchronous kind (the table's remote_async flag or a named kind); a synchronous kind takes none;
  7. the lane_receipts qualification is no longer an admission precondition — a request that still carries it is bound at execution
     (never by reading outside run/ops/receipts) and at the receipt.
"""
import datetime as dt
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_executor_overlay import DIGESTS, FRESH, load_executor as load_overlay_executor, make_repo, production_request, sha
from test_executor_table import ALL_CAPS, CANONICAL_CHART, OPS_FILE, World, _load_executor, _production_world

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
REPO = FLEET.parents[3]
REMOTE_ASYNC = {"smalltest_dispatch", "measuring_dispatch", "century_dispatch", "verification_job"}
MISSING = "required backup/restore/dry-run attestation missing"
EXPIRED = "approval expired or not yet valid"


def _utc(**delta):
    return (dt.datetime.now(dt.timezone.utc) + dt.timedelta(**delta)).isoformat(timespec="seconds")


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ───────────── the loop: the real main() on a temporary KY_ROOT; git, the table, validate and execute are the only doubles ─────────────

def _loop(tmp_path, monkeypatch, table, execute):
    mod = _load_executor(tmp_path)
    for d in (mod.REQ, mod.REC, mod.DONE, mod.ACC, mod.INFLIGHT, mod.TMP, mod.EXEC, mod.KY_ROOT / "logs"):
        d.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(mod, "sync", lambda: None)
    monkeypatch.setattr(mod, "main_executor_source", lambda: Path(mod.__file__).read_bytes())   # the real refresh path, proven current without git
    monkeypatch.setattr(mod, "main_revision", lambda: "a" * 40)
    monkeypatch.setattr(mod, "load_table", lambda: table)
    monkeypatch.setattr(mod, "capabilities", lambda table_on_main: {"none": True})
    monkeypatch.setattr(mod, "validate", lambda request, current_table, caps, reserved=False: None)
    monkeypatch.setattr(mod, "execute", execute)
    return mod


def _run_until_idle(mod, monkeypatch, pool):
    """Run main() until every operation submitted to `pool` has finished (or three idle ticks pass), then STOP; return the futures."""
    captured = []
    original = mod.cf.ThreadPoolExecutor

    class Capturing(original):
        def submit(self, fn, *args, **kwargs):
            future = super().submit(fn, *args, **kwargs)
            if getattr(self, "_thread_name_prefix", "") == pool:
                captured.append(future)
            return future

    ticks = []

    def tick(_seconds):
        ticks.append(1)
        for future in captured:
            future.result(timeout=20)
        if captured or len(ticks) > 3:
            (mod.RUN / "STOP_executor").touch()

    monkeypatch.setattr(mod.cf, "ThreadPoolExecutor", Capturing)
    monkeypatch.setattr(mod.time, "sleep", tick)
    assert mod.main() == 0
    (mod.RUN / "STOP_executor").unlink(missing_ok=True)
    return captured


def _queue(mod, operation_id, kind, **more):
    req = {"operation_id": operation_id, "kind": kind, "item_id": "A8", "idempotency_key": "key-" + operation_id,
           "requested_by": "adhikarin", "kyd": "fixture", **more}
    (mod.REQ / f"{operation_id}.json").write_text(json.dumps(req))
    return req


# 1 ── refresh refusal is decoupled from admission
def test_a_refused_refresh_keeps_serving_a_queued_read_only_request(tmp_path, monkeypatch):
    """Before A8, `table = load_table() if refresh_from_main_or_fail_closed() else None`: a merged executor change plus one queued request
    refused the refresh (the queue is not idle) and the refusal set table = None — every admission stopped until an operator intervened.
    Now the real refresh_from_main_or_fail_closed() refuses, logs REFRESH_REFUSED, records it, and the current snapshot serves the queue."""
    mod = _loop(tmp_path, monkeypatch, {"fixture_readback": {"production": False}}, lambda request, op: (0, "read back"))
    monkeypatch.setattr(mod, "handover_from_main", lambda: "pending operation request; executor refresh is refused")
    _queue(mod, "a8-read", "fixture_readback", requested_by="v1")
    futures = _run_until_idle(mod, monkeypatch, "read")
    assert futures, "the queued read-only request was never admitted while the refresh was refused"
    record = json.loads((mod.REC / "a8-read.json").read_text())
    assert record["status"] == "COMPLETED" and (mod.DONE / "a8-read.json").exists()
    assert mod.refresh_state() == "REFUSED"
    assert "REFRESH_REFUSED pending operation request; executor refresh is refused" in (mod.KY_ROOT / "logs/executor.log").read_text()
    assert not mod.FENCE.exists()


# 2 ── the digest an acceptance binds
def test_request_digest_excludes_the_clocks_so_an_extension_voids_no_acceptance(tmp_path, monkeypatch):
    w, table = _production_world(tmp_path, monkeypatch)
    base = w.production_request("backup_snapshot")
    accepted = w.accept(base)
    assert w.mod.validate(accepted, table, ALL_CAPS) is None
    extended = {**accepted, "expires_at": _utc(days=3), "lease_expires_at": _utc(days=3)}
    assert w.mod.request_digest(extended) == w.mod.request_digest(accepted) == w.mod.request_digest(base)
    assert w.mod.validate(extended, table, ALL_CAPS) is None, "an expiry extension voided the acceptance"
    for field, value in [("operation_id", "op-2"), ("kind", "backup_restore_verify"), ("item_id", "Y"), ("args", {"label": "other"}),
                         ("reviewed_commit", "a" * 40), ("chart_id", "0" * 36), ("lease_id", "lease-2"), ("kyd", "kyd-2"), ("timeout_s", 5)]:
        assert w.mod.request_digest({**base, field: value}) != w.mod.request_digest(base), field
        assert w.mod.validate({**accepted, field: value}, table, ALL_CAPS) is not None, field


def test_the_signer_and_the_children_mirror_the_executor_digest(tmp_path):
    ex = _load_executor(tmp_path)
    kyd = _load_module("a8_kyd_kinds_ops", FLEET / "kyd_kinds_ops.py")
    shared = _load_module("a8_v5_small_test_shared", REPO / "platform/scripts/v5_small_test_shared.py")
    req = {"operation_id": "op-1", "kind": "smalltest_teardown", "item_id": "J-1a", "idempotency_key": "k", "requested_by": "adhikarin",
           "kyd": "k", "args": {}, "chart_id": CANONICAL_CHART, "lease_id": "lease-1", "reviewed_commit": "a" * 40, "smalltest_scope": {"run_id": "r"}}
    timed = {**req, "expires_at": _utc(hours=1), "lease_expires_at": _utc(hours=2), "acceptance_receipt": "/run/ops/acceptance/op-1.json"}
    assert ex.request_digest(timed) == ex.request_digest(req) == kyd.request_digest(timed) == shared.request_hash(timed)
    changed = {**req, "args": {"x": "y"}}
    assert ex.request_digest(changed) == kyd.request_digest(changed) == shared.request_hash(changed) != ex.request_digest(req)


# 3 ── no age cap
def test_an_acceptance_lives_from_its_timestamp_until_the_request_expires(tmp_path, monkeypatch):
    w, table = _production_world(tmp_path, monkeypatch)
    aged = w.accept(w.production_request("backup_snapshot", expires_at=_utc(days=2)), ts=_utc(hours=-26))
    assert w.mod.validate(aged, table, ALL_CAPS) is None                                 # refused under the 3-hour cap; admitted now
    assert w.mod.validate(w.accept(w.production_request("backup_snapshot"), ts=_utc(minutes=5)), table, ALL_CAPS) == EXPIRED            # not yet valid
    assert w.mod.validate(w.accept(w.production_request("backup_snapshot", expires_at=_utc(seconds=-5))), table, ALL_CAPS) == EXPIRED   # the request lapsed


# 4 ── preconditions
def _attestation_world(tmp_path, monkeypatch):
    ops = json.loads(OPS_FILE.read_text())
    for kind in ("fixture_teardown", "fixture_publish"):
        ops["ops"][kind] = {"enabled": True, "needs": "owner", "script": "platform/scripts/fixture.py", "fixed_args": [], "allowed_args": [],
                            "production": True, "enabled_by": "J-1a", "required_rows": ["2", "3"]}      # rows a pre-A8 executor would demand
    w = World(tmp_path, monkeypatch, json.dumps(ops))
    return w, w.table()


def test_preconditions_are_dry_run_passed_and_backup_taken_for_a_teardown_only(tmp_path, monkeypatch):
    w, table = _attestation_world(tmp_path, monkeypatch)
    publish = w.production_request("fixture_publish")
    assert w.mod.validate(w.accept(publish, rows={}, checks={"dry_run_passed": True}), table, ALL_CAPS) is None               # no rows, backup_taken or restore_verified
    assert w.mod.validate(w.accept(publish, rows={"2": False, "3": False}, checks={"dry_run_passed": True}), table, ALL_CAPS) is None   # required_rows ignored
    assert w.mod.validate(w.accept(publish, checks={"backup_taken": True, "restore_verified": True}), table, ALL_CAPS) == MISSING    # dry_run_passed still earned
    teardown = w.production_request("fixture_teardown")
    assert w.mod.validate(w.accept(teardown, checks={"dry_run_passed": True}), table, ALL_CAPS) == MISSING                           # a teardown needs backup_taken
    assert w.mod.validate(w.accept(teardown, checks={"dry_run_passed": True, "backup_taken": True}), table, ALL_CAPS) is None
    assert w.mod.validate(w.accept(teardown, checks={"dry_run_passed": True, "backup_taken": "true"}), table, ALL_CAPS) == MISSING   # the boolean, never prose


def test_the_signers_required_checks_are_exactly_what_the_executor_demands(tmp_path, monkeypatch):
    """kyd_kinds_ops.required_checks is the signer's mirror of executor.validate's attestation rule (A8 §5). For every production kind of the
    real table: the executor admits an acceptance whose checks are exactly required_checks(kind), and refuses one missing any of them."""
    kyd = _load_module("a8_kyd_required_checks", FLEET / "kyd_kinds_ops.py")
    ops = json.loads(OPS_FILE.read_text())
    ops["ops"]["fixture_teardown"] = {"enabled": True, "needs": "owner", "script": "platform/scripts/fixture.py", "fixed_args": [],
                                      "allowed_args": [], "production": True, "enabled_by": "J-1a"}
    kinds = []
    for kind, entry in ops["ops"].items():
        if entry.get("production") and "TO_BE_SET" not in entry.get("script", ""):
            entry["enabled"] = True
            kinds.append(kind)
    assert {"backup_snapshot", "backup_restore_verify", "smalltest_dispatch", "smalltest_teardown", "fixture_teardown"} <= set(kinds)
    w = World(tmp_path, monkeypatch, json.dumps(ops))
    table = w.table()
    for kind in kinds:
        required = kyd.required_checks(kind)
        req = w.production_request(kind)
        assert w.mod.validate(w.accept(req, checks={k: True for k in required}), table, ALL_CAPS) != MISSING, kind        # nothing more is demanded
        for dropped in required:
            partial = {k: True for k in required if k != dropped}
            assert w.mod.validate(w.accept(req, checks=partial), table, ALL_CAPS) == MISSING, (kind, dropped)              # nothing less
    assert kyd.required_checks("smalltest_teardown") == ["backup_taken", "dry_run_passed"]
    assert kyd.required_checks("smalltest_dispatch") == ["dry_run_passed"]
    assert kyd.required_checks("backup_snapshot") == [] and kyd.required_checks("smalltest_teardown_dryrun") == []


# 5 ── *_dryrun kinds
def test_every_dry_run_kind_is_read_only_with_a_credential_in_the_table():
    ops = json.loads(OPS_FILE.read_text())["ops"]
    dry = {k for k in ops if k.endswith("_dryrun")}
    assert dry == {"smalltest_dispatch_dryrun", "smalltest_teardown_dryrun", "measuring_dispatch_dryrun", "measuring_teardown_dryrun",
                   "orchestrator_rebuild_dryrun"}
    for kind in dry:
        assert ops[kind]["production"] is False, kind
        assert ops[kind]["needs"] in ("builder", "owner"), kind                       # the credential stays
        assert "required_rows" not in ops[kind] and "remote_async" not in ops[kind], kind


def test_a_dry_run_needs_a_merged_reviewed_commit_and_nothing_a_production_kind_needs(tmp_path, monkeypatch):
    ops = json.loads(OPS_FILE.read_text())
    ops["ops"]["fixture_dryrun"] = {"enabled": True, "needs": "owner", "script": "platform/scripts/fixture.py", "fixed_args": ["--dry-run"],
                                    "allowed_args": [], "production": False, "enabled_by": "J-1a"}
    w = World(tmp_path, monkeypatch, json.dumps(ops))
    table = w.table()
    bare = {"operation_id": "op-dry", "kind": "fixture_dryrun", "item_id": "X", "idempotency_key": "key-dry", "requested_by": "adhikarin",
            "kyd": "kyd-1", "args": {}}
    assert w.mod.validate(bare, table, ALL_CAPS) == "reviewed_commit required for a dry-run operation"
    assert w.mod.validate({**bare, "reviewed_commit": "f" * 40}, table, ALL_CAPS) == "reviewed_commit is not merged to main"
    assert w.mod.validate({**bare, "reviewed_commit": w.reviewed}, table, ALL_CAPS) is None          # no lease, acceptance, chart_id or expires_at
    assert w.mod.validate({**bare, "reviewed_commit": w.reviewed}, table, {**ALL_CAPS, "owner": False}) == "capability_missing: owner"


def test_a_dry_run_runs_in_its_reviewed_tree_with_the_generated_overlay(tmp_path):
    src, commit = make_repo(tmp_path)
    mod = load_overlay_executor(tmp_path, src)
    req = dict(production_request(commit, "op-dry"), kind="fixture_dryrun")
    rc, out = mod.execute(req, {"script": "platform/scripts/read_digest.py", "needs": "none", "production": False})
    assert rc == 0, out
    assert (mod.KY_ROOT / "script_ran.marker").read_text() == FRESH               # the worktree at reviewed_commit with the overlay, not an extracted file
    assert mod.overlay_proofs().pop("op-dry")["files"] == {DIGESTS: sha(FRESH)}
    assert not list(mod.EXEC.iterdir()) and not list(mod.TMP.iterdir())


def test_a_dry_run_receipt_still_fails_without_its_rollback_proof(tmp_path):
    mod = _load_executor(tmp_path)
    for d in (mod.REC, mod.KY_ROOT / "logs"):
        d.mkdir(parents=True, exist_ok=True)
    scope = {"empty": True}
    req = {"operation_id": "dry-tear", "kind": "smalltest_teardown_dryrun", "item_id": "J-1a", "smalltest_scope": scope, "reviewed_commit": "a" * 40}
    proof = {"schema": "ky.smalltest_teardown/1", "status": "ROLLED_BACK", "rollback_confirmed": True, "operation_id": "dry-tear",
             "request_sha256": mod.request_digest(req), "scope": scope, "rowset_sha256": "c" * 64,
             "scope_sha256": mod.digest_bytes(json.dumps(scope, sort_keys=True, separators=(",", ":")).encode())}
    mod.receipt(req, "COMPLETED", rc=0, out="teardown_proof\t" + json.dumps(proof))
    assert json.loads((mod.REC / "dry-tear.json").read_text())["status"] == "COMPLETED"
    for broken in ("", "teardown_proof\t" + json.dumps({**proof, "rollback_confirmed": False}),
                   "teardown_proof\t" + json.dumps({**proof, "status": "COMMITTED_AWAITING_ABSENCE"})):
        mod.receipt(req, "COMPLETED", rc=0, out=broken)
        record = json.loads((mod.REC / "dry-tear.json").read_text())
        assert (record["status"], record["reason"]) == ("FAILED", "bound teardown proof missing; reconcile transaction outcome"), broken


# 6 ── the fence
@pytest.mark.parametrize("entry,fenced", [
    ({"production": True}, False),                              # a synchronous production kind: no fence
    ({"production": True, "remote_async": True}, True),         # the table flag
])
def test_only_a_remote_asynchronous_kind_takes_the_fence(tmp_path, monkeypatch, entry, fenced):
    mod = _loop(tmp_path, monkeypatch, {"fixture_production": entry}, lambda request, op: (0, "child returned"))
    req = _queue(mod, "a8-prod", "fixture_production")
    futures = _run_until_idle(mod, monkeypatch, "prod")
    assert futures and json.loads((mod.REC / "a8-prod.json").read_text())["status"] == "COMPLETED"
    assert mod.FENCE.exists() is fenced
    if fenced:
        fence = json.loads(mod.FENCE.read_text())
        assert fence["operation_id"] == "a8-prod" and fence["request_sha256"] == mod.request_digest(req)
    # a second production request is admitted at once after a synchronous kind and held behind the retained fence after a remote one
    _queue(mod, "a8-prod-2", "fixture_production")
    assert bool(_run_until_idle(mod, monkeypatch, "prod")) is (not fenced)
    assert (mod.REQ / "a8-prod-2.json").exists() is fenced


def test_the_named_remote_kinds_are_fenced_without_the_flag_and_the_table_flags_exactly_them(tmp_path):
    mod = _load_executor(tmp_path)
    for kind in REMOTE_ASYNC:
        assert mod.remote_async(kind, {"production": True}) is True, kind
    for kind in ("backup_snapshot", "backup_restore_verify", "smalltest_teardown", "measuring_teardown", "publish_head", "rollback_head", "layer_publish"):
        assert mod.remote_async(kind, {"production": True}) is False, kind
    assert mod.remote_async("some_future_kind", {"production": True, "remote_async": True}) is True
    assert mod.remote_async("some_future_kind", {"production": True, "remote_async": "true"}) is False       # the boolean, never prose
    ops = json.loads(OPS_FILE.read_text())["ops"]
    assert {k for k, e in ops.items() if e.get("remote_async") is True} == REMOTE_ASYNC
    assert all(ops[k]["production"] is True for k in REMOTE_ASYNC)


# 7 ── lane_receipts
def _lane_executor(tmp_path, monkeypatch):
    """test_lane_smalltest's `ex`: the table and the small-test policy from this tree; every other git answer empty and successful."""
    mod = _load_executor(tmp_path)
    monkeypatch.setattr(mod, "seen", lambda _: False)

    def git(*args, **kw):
        if args[0] == "show" and args[1].endswith("executor_ops.json"):
            return SimpleNamespace(returncode=0, stdout=OPS_FILE.read_text())
        if args[0] == "show" and args[1].endswith("v5_small_test_shared.py"):
            return SimpleNamespace(returncode=0, stdout=(REPO / "platform/scripts/v5_small_test_shared.py").read_text())
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(mod, "git", git)
    monkeypatch.setattr(mod, "REC", tmp_path / "receipts")
    mod.REC.mkdir()
    monkeypatch.setattr(mod, "log", lambda *a: None)
    return mod


def _lane_readback(**more):
    return dict(operation_id="lane-final", request_id="request-final", kind="readback_sql", item_id="J-1a", idempotency_key="j1a-final",
                requested_by="v1", kyd="J-1a", chart_id=CANONICAL_CHART, reviewed_commit="a" * 40, expires_at="2099-01-01T00:00:00+00:00",
                dry_run=True, lane_target=dict(host="127.0.0.1", port=55433, database="ky_j1a"), args={}, **more)


def test_lane_receipts_are_no_longer_an_admission_precondition(tmp_path, monkeypatch):
    mod = _lane_executor(tmp_path, monkeypatch)
    table = json.loads(OPS_FILE.read_text())["ops"]
    unqualified = _lane_readback(lane_receipts=[{"name": "nowhere.json", "sha256": "0" * 64}])
    assert mod.validate(unqualified, table, {"none": True}) is None     # before A8: "lane qualification receipts missing, mismatched or incomplete"
    with pytest.raises(ValueError):                                     # the binding itself still refuses where it is applied (execute_lane, receipt_lane)
        mod.lane_qualification(unqualified)
    assert mod.validate(_lane_readback(), table, {"none": True}) is None


def test_unqualified_lane_receipts_fail_at_execution_without_reading_outside_the_receipts_directory(tmp_path, monkeypatch):
    src, commit = make_repo(tmp_path)
    mod = load_overlay_executor(tmp_path, src)
    monkeypatch.setattr(mod, "validate_lane", lambda req, op, reserved=False: None)
    (tmp_path / "secret.json").write_text("{}")                          # what a traversal in the old per-ref staging would have copied for the child
    req = dict(production_request(commit, "op-lane"), lane_target={"fixture": True},
               lane_receipts=[{"name": "../secret.json", "sha256": mod.digest_bytes(b"{}")}])
    rc, out = mod.execute_lane(req, {"lane_dry_run": {"script": "00_ARCHITECTURE/briefs/kalayantra/fleet/lane_adapter.py"}})
    assert (rc, out) == (2, "lane qualification receipts missing, mismatched or incomplete")
    assert "op-lane" not in mod.overlay_proofs()                         # refused before the overlay and the adapter ran
    assert not list(mod.TMP.iterdir())
