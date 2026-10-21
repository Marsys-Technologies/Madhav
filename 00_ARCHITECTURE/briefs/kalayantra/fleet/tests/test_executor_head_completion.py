"""M-W56-16: the executor publishes a head change's <op>.completion.json (schema ky.head_completion/1) from a COMMITTED publish_head / rollback_head
receipt (AWAITING_READBACK), an independent v-lane readback and a digest-bound ACCEPTED acceptance, without a fence.

One doctrine-grounded oracle per distinct production claim (owner decision D-OWNER-TESTS-20261016; root CLAUDE.md §N.8: each verdict comes from a
detector that can read false). The verdict is the reviewed policy's own `head_operation.complete` (and, for a rollback, its `request_problem`), read
here from the working copy exactly as the executor reads it from the reviewed commit; these tests never re-implement it. The fixtures are the real
ones of test_j6_head_bindings.py (request / stage / receipt / rollback_request) plus a real readback output built with head_operation.expected_readback.
Each oracle names the single planted reversion (an exact line of executor.py or head_operation.py, applied to a copy) that makes it FAIL.
  H1 completion only when commit receipt, readback bytes and acceptance bind each other  (J6_BINDINGS_PREBUILD; head_operation.complete)
       reversion: `complete` is skipped and the receipt is written as COMPLETED
  H2 each break is refused: dry-run kind, requester accepts own head, readback by the requester, wrong sql_sha256, output != expected_readback,
     acceptance bound to another receipt digest
       reversion: the requester != acceptor test of head_operation.complete is dropped
  H3 a rollback completes only against its original publish (`rollback_of`; head_operation.request_problem)
       reversion: the executor ignores the policy's request_problem for a rollback
  H4 publication is atomic, idempotent and fence-free (publish_teardown_completions pattern)
       reversion: the document is written straight to its final path (no stage + os.replace)
  H5 nothing else the executor admits or runs changes (test_executor_table's boundary pin: only exact reviewed additions)
       reversion: a kind is added to SIGNED_ONLY_KINDS
Each oracle is one function `oracle_hN(w)`; it passes on the real sources and `test_revert_proof` shows it FAILS on the reverted copy.
"""
import copy
import csv
import hashlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
EXECUTOR_PY = FLEET / "executor.py"
HEAD_PY = FLEET / "head_operation.py"
sys.path.insert(0, str(FLEET))
import head_operation as head  # noqa: E402

_spec = importlib.util.spec_from_file_location("j6_fixtures", FLEET / "tests" / "test_j6_head_bindings.py")
j6 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(j6)      # the real J-6 fixtures: request / stage / receipt / rollback_request

CALL = "        publish_head_completions()            # M-W56-16: a committed head change + its independent readback and accepted digest complete without a fence\n"
TEARDOWN_CALL = "        publish_teardown_completions()        # SR-TEARDOWN-COMPLETION: a committed teardown + its accepted absence complete without a fence\n"
COMPLETE_CALL = 'completion = dict(policy["complete"](req, commit_raw, rb_req, rb_raw, output_raw, accepted), schema='
ROLLBACK_GATE = '            if req.get("kind") == "rollback_head" and policy["request_problem"](req, OPS): continue\n'
STAGE_LINE = '            staged = target.with_suffix(".json.tmp")\n            with staged.open("w") as stream:\n                stream.write(json.dumps(completion, indent=1))'
REQUESTER_TEST = " or accepted.get('by') == req.get('requested_by')"


class Stop(Exception): pass


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


class World:
    """An executor module (optionally with one planted reversion) on a sandbox KY_ROOT, with the head policy from the working copy."""

    def __init__(self, tmp, mutations=(), head_mutations=()):
        text = EXECUTOR_PY.read_text()
        for old, new in mutations:
            if text.count(old) != 1: raise RuntimeError(f"mutation anchor not unique: {old!r}")      # a bad anchor is never a failed oracle
            text = text.replace(old, new)
        source = HEAD_PY.read_text()
        for old, new in head_mutations:
            if source.count(old) != 1: raise RuntimeError(f"head mutation anchor not unique: {old!r}")
            source = source.replace(old, new)
        path = tmp / "executor_under_test.py"
        path.write_text(text)
        saved = os.environ.get("KY_ROOT")
        os.environ["KY_ROOT"] = str(tmp / "ky")
        try:
            spec = importlib.util.spec_from_file_location(f"ky_exec_head_{abs(hash((str(tmp), tuple(mutations), tuple(head_mutations))))}", path)
            self.mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(self.mod)
        finally:
            os.environ.pop("KY_ROOT", None) if saved is None else os.environ.__setitem__("KY_ROOT", saved)
        m = self.mod
        for d in (m.REQ, m.REC, m.DONE, m.ACC, m.INFLIGHT, m.TMP, m.KY_ROOT / "logs"): d.mkdir(parents=True, exist_ok=True)
        (m.OPS.parent / "EVENTS.jsonl").write_text(json.dumps(j6.decision()) + "\n")
        namespace = {"__name__": "reviewed_head_policy", "__file__": "reviewed_head_policy.py"}
        exec(compile(source, "reviewed head evidence policy", "exec"), namespace)
        m.head_policy = lambda req: namespace       # the reviewed policy, from the working copy instead of `git show <reviewed_commit>`
        self.op = None

    # -- the flow a head change leaves behind: archived request, committed receipt, readback request/receipt/output, acceptance ------------------

    def file_head(self, kind="publish_head", *, requested_by="adhikarin", rollback_of_other=False):
        """A genuine committed head change (real stage/receipt fixtures) and its archived request. Returns the request."""
        m = self.mod
        if kind == "publish_head":
            req = j6.request("publish_head")
            req["requested_by"] = requested_by
            dry = j6.request()
            req["dry_run_receipt"] = j6.store(m.OPS, "dry.json", j6.receipt(dry, j6.stage(dry)))
            proof = j6.stage(req)
        else:
            dry = j6.rollback_request(m.OPS)                            # a rollback_head_dryrun request whose rollback_of binds the original publish
            dry["operation_id"] = "J-6r-dry"; dry["requested_by"] = requested_by
            if rollback_of_other:                                       # rollback_of names a DIFFERENT committed publish (another manifest)
                other = j6.request("publish_head"); other["operation_id"] = "J-6-other"
                other["head_change"]["target"]["manifest_id"] = str(__import__("uuid").UUID(int=77))
                other["args"]["manifest-id"] = other["head_change"]["target"]["manifest_id"]
                other_proof = j6.stage(other); other_proof.update(status="COMMITTED_AWAITING_READBACK", rollback_confirmed=False)
                committed = j6.receipt(other, other_proof); committed["status"] = "AWAITING_READBACK"
                dry["rollback_of"] = j6.store(m.OPS, "other-publish.json", committed)
            req = copy.deepcopy(dry); req["kind"] = "rollback_head"; req["operation_id"] = "J-6r-attempt-1"
            req["dry_run_receipt"] = j6.store(m.OPS, "rb-dry.json", j6.receipt(dry, j6.stage(dry)))
            proof = j6.stage(req)
        proof.update(status="COMMITTED_AWAITING_READBACK", rollback_confirmed=False)
        committed = j6.receipt(req, proof); committed["status"] = "AWAITING_READBACK"
        (m.REC / f"{req['operation_id']}.json").write_text(json.dumps(committed))
        (m.DONE / f"{req['operation_id']}.json").write_text(json.dumps(req))
        self.req = req
        return req

    def file_readback(self, *, readback_by="v1", accepted_by="v2", sql_sha=None, output_over=None, accepted_over=None, opid="J-6-readback-1"):
        """The independent readback of the head change in self.req, and its acceptance by a v-lane (the signer post-acceptance)."""
        m, req = self.mod, self.req
        rows = head.expected_readback(req) if output_over is None else output_over
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
        writer.writerow(["head_readback"]); writer.writerow([json.dumps(rows)])
        output = m.REC / f"{opid}.output.txt"
        output.write_text(buffer.getvalue())
        rb_req = dict(operation_id=opid, item_id=req["item_id"], kind="readback_sql", requested_by=readback_by, chart_id=req["chart_id"],
                      reviewed_commit=req["reviewed_commit"], args={"sql_sha256": sql_sha or sha(head.readback_sql(req))})
        rb = dict(status="COMPLETED", operation_id=opid, kind="readback_sql", item_id=req["item_id"], requested_by=readback_by,
                  request_sha256=head.request_digest(rb_req), output_sha256=sha(output.read_bytes()), exit_code=0)
        (m.DONE / f"{opid}.json").write_text(json.dumps(rb_req))
        (m.REC / f"{opid}.json").write_text(json.dumps(rb))
        commit_raw = (m.REC / f"{req['operation_id']}.json").read_bytes()
        accepted = dict(result="ACCEPTED", by=accepted_by, operation_id=req["operation_id"], request_sha256=head.request_digest(req),
                        receipt_sha256=sha(commit_raw), readback_receipt_sha256=sha((m.REC / f"{opid}.json").read_bytes()),
                        readback_operation_id=opid)
        accepted.update(accepted_over or {})
        (m.ACC / f"{req['operation_id']}.readback.json").write_text(json.dumps(accepted))
        return accepted

    @property
    def completion(self):
        return self.mod.REC / f"{self.req['operation_id']}.completion.json"

    def expected(self):
        """What the reviewed policy's complete() returns for the filed flow, plus the document's own three source digests."""
        m, req = self.mod, self.req
        commit_raw = (m.REC / f"{req['operation_id']}.json").read_bytes()
        acc_raw = (m.ACC / f"{req['operation_id']}.readback.json").read_bytes()
        acc = json.loads(acc_raw)
        rb_raw = (m.REC / f"{acc['readback_operation_id']}.json").read_bytes()
        out = head.complete(req, commit_raw, json.loads((m.DONE / f"{acc['readback_operation_id']}.json").read_bytes()), rb_raw,
                            (m.REC / f"{acc['readback_operation_id']}.output.txt").read_bytes(), acc)
        return dict(out, schema="ky.head_completion/1", readback_operation_id=acc["readback_operation_id"],
                    source_digests=dict(commit_receipt=sha(commit_raw), readback_receipt=sha(rb_raw), acceptance=sha(acc_raw)))


@pytest.fixture
def world(tmp_path):
    w = World(tmp_path); w.file_head(); w.file_readback()
    return w


def publish(w):
    w.mod.publish_head_completions()


# ---------------------------------------------------------------------------------------------------- oracles

def oracle_h1(w):
    w.file_head("publish_head"); w.file_readback()
    publish(w)
    assert w.completion.exists(), "a COMMITTED head change with an independent readback and a digest-bound acceptance published no completion"
    doc = json.loads(w.completion.read_text())
    assert doc == w.expected(), "the completion must be exactly what the reviewed policy's complete() returned, plus the three source digests"
    assert doc["status"] == "COMPLETED" and doc["schema"] == "ky.head_completion/1" and doc["head_change"]["status"] == "COMMITTED_AWAITING_READBACK"
    # the same readback with its output altered by one byte is NOT bound by the readback receipt: nothing is published for the tampered flow
    w.completion.unlink()
    out = w.mod.REC / "J-6-readback-1.output.txt"
    out.write_text(out.read_text() + " ")
    publish(w)
    assert not w.completion.exists(), "a readback output that its receipt does not bind completed the head change"
    out.write_text(out.read_text().rstrip(" "))
    # a commit receipt changed after the acceptance bound its digest
    commit = w.mod.REC / "J-6-attempt-1.json"
    commit.write_text(json.dumps(dict(json.loads(commit.read_text()), ts="2026-10-16T09:09:09+00:00")))
    publish(w)
    assert not w.completion.exists(), "a commit receipt the acceptance does not bind completed the head change"


H2_CASES = ("dryrun_kind", "requester_accepts_own_head", "readback_by_requester", "wrong_sql_sha256", "output_not_expected_readback", "acceptance_other_receipt_digest")


def oracle_h2(w, case):
    if case == "dryrun_kind":                       # a dry-run request/receipt can never be completed (committed-status forged on a dry-run kind)
        req = w.file_head("publish_head"); w.file_readback()
        forged = dict(json.loads((w.mod.REC / "J-6-attempt-1.json").read_text()), kind="publish_head_dryrun")
        (w.mod.REC / "J-6-attempt-1.json").write_text(json.dumps(forged))
        publish(w)
        assert not w.completion.exists(), "a dry-run receipt (publisher gate) was completed"
        (w.mod.DONE / "J-6-attempt-1.json").write_text(json.dumps(dict(req, kind="publish_head_dryrun")))
        (w.mod.REC / "J-6-attempt-1.json").write_text(json.dumps(dict(forged, kind="publish_head")))
        publish(w)
        assert not w.completion.exists(), "a dry-run request (policy gate) was completed"
    elif case == "requester_accepts_own_head":
        w.file_head("publish_head", requested_by="v1"); w.file_readback(readback_by="v2", accepted_by="v1")
        publish(w)
        assert not w.completion.exists(), "the head requester's own acceptance completed its head change"
    elif case == "readback_by_requester":
        w.file_head("publish_head", requested_by="v1"); w.file_readback(readback_by="v1", accepted_by="v2")
        publish(w)
        assert not w.completion.exists(), "a readback requested by the head requester completed its head change"
    elif case == "wrong_sql_sha256":
        w.file_head("publish_head"); w.file_readback(sql_sha="0" * 64)
        publish(w)
        assert not w.completion.exists(), "a readback of other SQL than readback_sql(req) completed the head change"
    elif case == "output_not_expected_readback":
        w.file_head("publish_head")
        w.file_readback(output_over=dict(head.expected_readback(w.req), head=dict(head.expected_readback(w.req)["head"], generation="3.0")))
        publish(w)
        assert not w.completion.exists(), "a readback that disagrees with expected_readback(req) completed the head change"
    else:
        w.file_head("publish_head"); w.file_readback(accepted_over={"receipt_sha256": "1" * 64})
        publish(w)
        assert not w.completion.exists(), "an acceptance bound to another receipt digest completed the head change"


def oracle_h3(w):
    w.file_head("rollback_head")
    w.file_readback(opid="J-6r-readback-1")
    publish(w)
    assert w.completion.exists(), "premise: a rollback bound to its original publish completes"
    assert json.loads(w.completion.read_text())["kind"] == "rollback_head"
    w.completion.unlink()
    for name in ("J-6r-attempt-1.json", "J-6r-readback-1.json", "J-6r-readback-1.output.txt"): (w.mod.REC / name).unlink()
    w.file_head("rollback_head", rollback_of_other=True)          # rollback_of binds ANOTHER committed publish; every other file is honestly consistent
    w.file_readback(opid="J-6r-readback-1")
    publish(w)
    assert not w.completion.exists(), "a rollback whose rollback_of is not its original publish completed"


def oracle_h4(w, monkeypatch):
    w.file_head(); w.file_readback()
    publish(w)
    first = w.completion.read_bytes()
    publish(w)
    assert w.completion.read_bytes() == first and sorted(p.name for p in w.mod.REC.glob("*.completion.json")) == ["J-6-attempt-1.completion.json"]
    assert not list(w.mod.REC.glob("*.tmp")), "a staged file was left behind"
    w.completion.unlink()
    def killed(src, dst): raise OSError("killed between stage and replace")
    monkeypatch.setattr(os, "replace", killed)
    with pytest.raises(OSError, match="killed"):
        publish(w)
    monkeypatch.undo()
    assert not w.completion.exists(), "a partial completion document is visible after a kill between stage and replace"
    publish(w)                                                      # the staged remnant is overwritten, then replaced atomically
    assert w.completion.read_bytes() == first


def oracle_h4_fence(w):
    w.file_head(); w.file_readback()
    assert not w.mod.FENCE.exists()
    publish(w)
    assert w.completion.exists() and not w.mod.FENCE.exists(), "publishing created a production fence"
    w.completion.unlink()
    w.mod.FENCE.write_text(json.dumps({"operation_id": "J-3c.dispatch", "request_sha256": "9" * 64, "ts": "2026-10-19T00:00:00+00:00"}))
    before = w.mod.FENCE.read_bytes()
    publish(w)
    assert w.completion.exists() and w.mod.FENCE.read_bytes() == before, "the publisher did not run beside a fence, or touched it"


def oracle_h4_loop(w):
    w.file_head(); w.file_readback()
    m = w.mod
    m.sync = lambda: None; m.refresh_from_main_or_fail_closed = lambda: True; m.load_table = lambda: {}
    m.capabilities = lambda on_main: {}; m.scheduler_backstop_tick = lambda: None; m.scheduler_backstop_records = lambda: []
    def stop(_seconds): raise Stop()
    m.time = type("T", (), {"time": staticmethod(__import__("time").time), "sleep": staticmethod(stop)})
    with pytest.raises(Stop):
        m.main()
    assert w.completion.exists(), "one turn of main() with no fence held did not publish the head completion"
    assert not m.FENCE.exists()


ORACLES = {"h1": oracle_h1, "h3": oracle_h3, "h4_fence": oracle_h4_fence, "h4_loop": oracle_h4_loop}


@pytest.mark.parametrize("key", sorted(ORACLES))
def test_oracle_passes_on_the_real_sources(tmp_path, key):
    ORACLES[key](World(tmp_path))


@pytest.mark.parametrize("case", H2_CASES)
def test_h2_each_break_is_refused_and_publishes_nothing(tmp_path, case):
    oracle_h2(World(tmp_path), case)


def test_h2_a_flow_with_no_acceptance_or_readback_files_publishes_nothing_and_raises_nothing(world):
    (world.mod.ACC / "J-6-attempt-1.readback.json").unlink()
    publish(world)
    assert not world.completion.exists()
    world.file_readback()
    (world.mod.REC / "J-6-readback-1.output.txt").unlink()
    publish(world)
    assert not world.completion.exists()


def test_h4_atomic_publication_survives_a_kill_and_is_idempotent(tmp_path, monkeypatch):
    oracle_h4(World(tmp_path), monkeypatch)


# ---------------------------------------------------------------------------------------------------- H5: nothing else the executor admits or runs changes

def table_test_module():
    spec = importlib.util.spec_from_file_location("ky_executor_table_pins", FLEET / "tests" / "test_executor_table.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def oracle_h5(mutations=()):
    t = table_test_module()
    work = EXECUTOR_PY.read_text()
    for old, new in mutations:
        assert work.count(old) == 1, f"mutation anchor not unique: {old!r}"
        work = work.replace(old, new)
    problems = t.boundary_violations(t.base_text(t.PY_REL), work)
    assert problems == [], f"executor.py changed beyond the pinned reviewed additions: {problems}"


def test_oracle_h5_passes_on_the_real_executor():
    oracle_h5()


def test_h5_the_signed_only_kinds_and_the_new_function_are_pinned():
    t = table_test_module()
    from executor_pin_shards import load_shards, hashes_after
    hashes = hashes_after({"W4": t.BASE_W4_FUNCTION_HASHES, "K9": t.BASE_K9_FUNCTION_HASHES}, load_shards())["W4"]
    assert "publish_head_completions" in hashes and "main" in hashes                  # new function + its one call in main: reviewed shard J-6 (M-W56-16)
    seg = t._segments(EXECUTOR_PY.read_text())
    assert hashlib.sha256(seg["publish_head_completions"].encode()).hexdigest() == hashes["publish_head_completions"]


# ---------------------------------------------------------------------------------------------------- revert proofs (ONE planted reversion per claim)

SIGNED_ONLY = '    "verification_cancel",\n})\nCANCEL_LANE_KINDS'
REVERSIONS = {
    "h1": dict(mutations=[(COMPLETE_CALL, 'completion = dict(json.loads(commit_raw), status="COMPLETED", commit_receipt_sha256=digest_bytes(commit_raw), readback_receipt_sha256=digest_bytes(rb_raw), schema=')]),
    "h3": dict(mutations=[(ROLLBACK_GATE, "")]),
    "h4_fence": dict(mutations=[('        log(f"{path.stem} head completion published (readback {readback_op})")\n',
                                 '        FENCE.write_text(json.dumps({"operation_id": path.stem, "ts": now()}))\n')]),
    "h4_loop": dict(mutations=[(CALL, "")]),
}
H2_REVERSION = dict(head_mutations=[(REQUESTER_TEST, "")])
H2_REQUESTER_PUBLISHER_REVERSION = dict(mutations=[('            if rb_req.get("requested_by") == req.get("requested_by"): continue      # S-5: the readback is a v-lane\'s, never the head requester\'s\n', "")])
H4_REVERSION = dict(mutations=[(STAGE_LINE, '            staged = target\n            with staged.open("w") as stream:\n                stream.write(json.dumps(completion, indent=1))')])


@pytest.mark.parametrize("key", sorted(REVERSIONS))
def test_revert_proof_the_oracle_fails_on_its_single_planted_reversion(tmp_path, key):
    with pytest.raises(AssertionError):
        ORACLES[key](World(tmp_path, **REVERSIONS[key]))


def test_revert_proof_h2_requester_accepts_own_head(tmp_path):
    with pytest.raises(AssertionError):
        oracle_h2(World(tmp_path, **H2_REVERSION), "requester_accepts_own_head")


def test_revert_proof_h2_readback_by_the_head_requester(tmp_path):
    with pytest.raises(AssertionError):
        oracle_h2(World(tmp_path, **H2_REQUESTER_PUBLISHER_REVERSION), "readback_by_requester")


def test_revert_proof_h4_a_direct_write_shows_a_partial_file(tmp_path, monkeypatch):
    with pytest.raises(AssertionError):
        oracle_h4(World(tmp_path, **H4_REVERSION), monkeypatch)


def test_revert_proof_h5_a_kind_added_to_signed_only_kinds_fails_the_pin():
    with pytest.raises(AssertionError):
        oracle_h5([(SIGNED_ONLY, '    "verification_cancel",\n    "layer_unpublish",\n})\nCANCEL_LANE_KINDS')])
