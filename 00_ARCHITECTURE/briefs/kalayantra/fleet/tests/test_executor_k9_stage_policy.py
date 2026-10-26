"""K9-4b `k9_rebuild_stage`: the absence and exposure gates (ruling SR-PREP-LANES-1 (2): "admitted only under owner_go + absence/exposure gates").

Doctrine: root CLAUDE.md §N.8 (every gate is computed by a detector that can read false; a readback that was never run, or ran another query, proves nothing) and §B.10 (nothing here
invents a value). One oracle per distinct production claim; each passes on the real policy and FAILS on a copy of fleet/k9_stage_policy.py with that ONE claim's line reverted.

  A1 a run, a candidate, an open rebuild run or a building candidate already present is refused by the absence gate (each of the four counts)
  A2 the absence readback must be THIS run's (another run id / chart / schema is refused)
  X1 rows already under the candidate generation (grain table or any layer partition) are refused by the exposure gate
  X2 the served head must equal the request's expected-head (NONE = no head)
  R1 a cited readback must be an ACCEPTED, completed readback_sql (an unaccepted one is refused)
  R2 the cited receipt must be the bytes the request names (sha256)
  R3 the readback must have run the policy's fixed query (a different query that reads zeros proves nothing)
  R4 a stale readback is refused
  S1 the request is item K9-4b with exactly the four staging arguments, each well formed
  S2 the dry run needs no readbacks (it persists nothing) but has the same argument shape
"""
import importlib.util
import sys
from pathlib import Path

import pytest

import k9_stage_cases as C
import k9_stage_policy as real

FLEET = Path(__file__).resolve().parents[1]
POLICY = FLEET / "k9_stage_policy.py"


def load(path, name="mutated_k9_stage_policy"):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def mutated(tmp_path, old, new):
    text = POLICY.read_text()
    assert text.count(old) == 1, f"reversion anchor is not unique: {old!r}"
    path = tmp_path / "k9_stage_policy_mutated.py"
    path.write_text(text.replace(old, new))
    return load(path)


def judge(module, ops, req):
    try:
        return module.request_problem(req, ops.root, ops.accepted_readback)
    except Exception as exc:      # a reverted policy may crash instead of refusing: that is a failed oracle, not a harness error
        return f"CRASH {type(exc).__name__}"


@pytest.fixture
def ops(tmp_path):
    return C.Ops(tmp_path / "ops")


# ------------------------------------------------------------------ oracles (each takes the policy module under test and the ops folder)


def a1(module, ops):
    assert judge(module, ops, ops.request()) is None, "control failed — a clean absence and exposure admits the staging"
    for field in C.ABSENT:
        req = ops.request(absence=C.absence_evidence(**{field: 1}))
        why = judge(module, ops, req)
        assert why and why.startswith("absence gate"), (field, why)


def a2(module, ops):
    other = "0a0a0a0a-0000-4000-8000-0000000000ff"
    for evidence in (C.absence_evidence(run_id=other), C.absence_evidence(chart_id="362f9f17-0000-4000-8000-000000000000"), C.absence_evidence(schema="ky.other/1")):
        why = judge(module, ops, ops.request(absence=evidence))
        assert why and why.startswith("absence gate"), (evidence, why)


def x1(module, ops):
    assert judge(module, ops, ops.request()) is None, "control failed"
    assert (judge(module, ops, ops.request(exposure=C.exposure_evidence(grain_rows=3))) or "").startswith("exposure gate")
    for table in real.PARTITIONED_TABLES:
        partitions = {t: 0 for t in real.PARTITIONED_TABLES} | {table: 2}
        why = judge(module, ops, ops.request(exposure=C.exposure_evidence(partition_rows=partitions)))
        assert why and why.startswith("exposure gate"), (table, why)
    why = judge(module, ops, ops.request(exposure=C.exposure_evidence(partition_rows={"kala_convergence": 0})))
    assert why and why.startswith("exposure gate"), "a partition set that omits a table is not a measurement of every table"


def x2(module, ops):
    assert judge(module, ops, ops.request(exposure=C.exposure_evidence(head="g-0"))) is None, "control failed"
    assert "served head" in (judge(module, ops, ops.request(exposure=C.exposure_evidence(head="g-9"))) or "")
    assert "served head" in (judge(module, ops, ops.request(exposure=C.exposure_evidence(head=None))) or ""), "a head appeared where the request expects g-0"
    none_req = ops.request(exposure=C.exposure_evidence(head=None))
    none_req["args"] = {**none_req["args"], "expected-head": "NONE"}
    assert judge(module, ops, none_req) is None, "NONE matches a chart with no head"
    none_req = ops.request(exposure=C.exposure_evidence(head="g-0"))
    none_req["args"] = {**none_req["args"], "expected-head": "NONE"}
    assert "served head" in (judge(module, ops, none_req) or "")


def r1(module, ops):
    req = ops.request()
    assert judge(module, ops, req) is None, "control failed"
    post = ops.root / "acceptance" / "rb-absence.post.json"
    post.write_text(post.read_text().replace("ACCEPTED", "REJECTED"))
    assert "not an accepted" in (judge(module, ops, req) or "")
    post.unlink()
    assert "accepted readback" in (judge(module, ops, req) or ""), "no acceptance record at all"


def r2(module, ops):
    req = ops.request()
    assert judge(module, ops, req) is None, "control failed"
    (ops.root / "receipts" / "rb-absence.json").write_bytes((ops.root / "receipts" / "rb-absence.json").read_bytes() + b" ")
    assert "differs from its cited sha256" in (judge(module, ops, req) or "")


def r3(module, ops):
    assert judge(module, ops, ops.request()) is None, "control failed"
    req = ops.request()
    req["absence_readback"] = ops.readback("rb-absence", C.absence_evidence(), real.absence_sql(C.RUN), sql_sha="0" * 64)
    assert "fixed query" in (judge(module, ops, req) or "")
    req = ops.request()
    req["exposure_readback"] = ops.readback("rb-exposure", C.exposure_evidence(), real.absence_sql(C.RUN))      # the absence query cited as the exposure readback
    assert "fixed query" in (judge(module, ops, req) or "")


def r4(module, ops):
    assert judge(module, ops, ops.request()) is None, "control failed"
    why = judge(module, ops, ops.request(absence=C.absence_evidence(measured_at=C.iso(-3 * real.FRESH_S))))
    assert why and "stale" in why, why
    why = judge(module, ops, ops.request(exposure=C.exposure_evidence(measured_at=C.iso(3600))))
    assert why and "stale" in why, why


def s1(module, ops):
    req = ops.request()
    assert judge(module, ops, req) is None, "control failed"
    assert "K9-4b" in (judge(module, ops, {**req, "item_id": "K9-4a"}) or "")
    for bad in ({"run-id": "NOT-A-UUID"}, {"natal-build": "x"}, {"assets": "ka_yojaka,ka_yojaka"}, {"assets": "ga_positions"}, {"expected-head": "bad head"}):
        assert judge(module, ops, {**req, "args": {**req["args"], **bad}}), bad
    assert judge(module, ops, {**req, "args": {k: v for k, v in req["args"].items() if k != "natal-build"}}), "a missing argument"
    assert judge(module, ops, {**req, "args": {**req["args"], "extra": "1"}}), "an extra argument"


def s2(module, ops):
    dry = {"operation_id": "d", "kind": "k9_rebuild_stage_dryrun", "item_id": "K9-4b", "args": dict(C.ARGS)}
    assert judge(module, ops, dry) is None, "the dry run needs no readbacks"
    assert judge(module, ops, {**dry, "item_id": "K9-4a"}), "the dry run has the same item rule"
    assert judge(module, ops, {**dry, "args": {**dry["args"], "run-id": "x"}}), "the dry run has the same argument shape"
    assert judge(module, ops, {"kind": "k9_rebuild_stage"} | {k: v for k, v in dry.items() if k != "kind"}), "the real kind without readbacks is refused"


# claim -> (oracle, the ONE planted reversion of k9_stage_policy.py that must make it fail)
ORACLES = {
    "a1": (a1, ('any(_count(absence.get(k)) != 0 for k in ("build_runs_for_run_id", "candidates_for_run_id", "open_rebuild_runs", "building_candidates"))', "False")),
    "a2": (a2, ('absence.get("run_id") != run_id or absence.get("chart_id") != CANONICAL_CHART', "False")),
    "x1": (x1, ('or any(_count(v) != 0 for v in partitions.values()):', "or False:")),
    "x2": (x2, ('if (head if head is not None else "NONE") != args["expected-head"]:', "if False:")),
    "r1": (r1, ("    if got is None:\n", "    if False:\n")),
    "r2": (r2, ('if hashlib.sha256(path.read_bytes()).hexdigest() != ref["sha256"]:', "if False:")),
    "r3": (r3, ('if (args.get("sql-sha256") or args.get("sql_sha256")) != sql_sha256(query):', "if False:")),
    "r4": (r4, ("if not (now - dt.timedelta(seconds=FRESH_S) <= measured <= now + dt.timedelta(seconds=FUTURE_S)):", "if False:")),
    "s1": (s1, ('if req.get("item_id") != ITEM:', "if False:")),
    "s2": (s2, ('if problem or req["kind"] != "k9_rebuild_stage":', "if problem:")),
}


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_policy(ops, claim):
    ORACLES[claim][0](real, ops)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, ops, claim):
    oracle, (old, new) = ORACLES[claim]
    with pytest.raises(AssertionError):
        oracle(mutated(tmp_path, old, new), ops)


def test_the_fixed_queries_satisfy_the_readback_preparer_rules():
    """fleet/k9_readback.prepare_readback accepts one un-commented SELECT without a terminator or backslash: both fixed queries must pass it unchanged, and the digest it
    binds is the one the policy computes (the executor compares it)."""
    import k9_readback
    for build in (real.absence_sql, real.exposure_sql):
        query = build(C.RUN)
        request = {"item_id": "K9-4b", "kind": "readback_sql", "operation_id": "rb-1", "reviewed_commit": "a" * 40, "args": {"sql_file": "run/ops/sql/rb-1.sql"}}
        prepared = k9_readback.prepare_readback(request, readback_sql=query)
        assert prepared["request"]["args"]["sql-sha256"] == real.sql_sha256(query)
        assert prepared["sql"] == real.wrapped_sql(query)
