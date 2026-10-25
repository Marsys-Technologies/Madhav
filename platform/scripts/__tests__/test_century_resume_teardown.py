"""SR-RESUME-NOW (OWNER-RESUMABLE-REQUIRED-20261025): the century TEARDOWN covers what a RESUMED century build adds.

A resume is a new build_runs row over the same generation '5.0' chain, so a resumed build leaves one more run (and the partitions it wrote) than the single run the teardown scope
used to name; before this change the teardown refused it (`only the identified staged run may be deleted; additional or pruned runs refuse`), which would have left the chart
uncleared for the next fresh dispatch. The scope now names the resumed runs (`century_scope.resumed_runs`), each bound to the accepted `century_resume` launch that started it.

Doctrine: root CLAUDE.md §N.8 and §B.10. One oracle per distinct production claim; each passes on the real module and FAILS on a copy of it with that ONE claim's line reverted.

  T1 a resumed run in the teardown scope is bound to the accepted `century_resume` launch that started it (run, plan manifest, execution), and only a century scope carries any
  T3 the foreign-coverage statement a resumed scope uses runs against the real column types and counts exactly the event_class partitions of runs outside the set
  T2 the teardown deletes exactly the identified run plus the resumed runs the scope names: an unnamed extra run, a named run that no longer exists, and a surviving run whose manifest
     digest differs all refuse; a partition written by a run outside the set refuses; a scope with no resumed runs is judged exactly as before
"""
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
for folder in (SCRIPTS, SCRIPTS / "__tests__"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import century_resume_support as S  # noqa: E402
import teardown_v5_small_test_job as teardown  # noqa: E402
import v5_small_test_shared as shared  # noqa: E402

R0, R1, R2 = S.RUN, S.NEW_RUN, "55555555-5555-4555-8555-555555555555"
FOREIGN = "77777777-7777-4777-8777-777777777777"
MANIFEST_ID = "88888888-8888-4888-8888-888888888888"
VECTOR = {"stored_scope": "default", "input": "vector"}
MANIFESTS = {r: {"chart_id": shared.CHART_ID, "scope_target": shared.ASSET_ID, "run": r} for r in (R0, R1, R2)}       # each run's staged plan_manifest
DIGESTS = {r: shared.evidence_digest(m) for r, m in MANIFESTS.items()}
EXEC = {R0: "brahma-build-pipeline-job-first", R1: "brahma-build-pipeline-job-second", R2: "brahma-build-pipeline-job-third"}


def module_copy(tmp_path, source, mutation=None):
    text = Path(source).read_text()
    old, new = mutation
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor not unique: {old!r}")      # a bad anchor must never read as a failed oracle
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / f"{Path(source).stem}_{abs(hash(mutation))}.py"
    path.write_text(text.replace(old, new))
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def accepted(root, name, kind, run_id, *, by="v1", result="ACCEPTED", status="COMPLETED", digest=None, execution=None):
    """The executor's launch receipt of `kind` and the verifier's acceptance of its request, as the teardown scope cites them."""
    request_sha = "b" * 64
    receipt = S.put(root, "receipts", name, {"operation_id": name, "kind": kind, "item_id": shared.CENTURY_ITEM, "status": status, "exit_code": 0, "ts": S.LAUNCHED_AT,
                                              "request_sha256": request_sha, "reviewed_commit": S.COMMIT,
                                              "launch": {"schema": "ky.century_launch/1", "status": "LAUNCHED", "run_id": run_id, "chart_id": shared.CHART_ID,
                                                         "asset_id": shared.ASSET_ID, "execution_name": execution or EXEC[run_id], "plan_manifest_digest": digest or DIGESTS[run_id]}})
    acceptance = S.put(root, "acceptance", name, {"operation_id": name, "result": result, "by": by, "request_sha256": request_sha, "reviewed_commit": S.COMMIT})
    return receipt, acceptance


def scope_of(root, resumed=(), **over):
    """A century teardown scope over the first run (a century_dispatch launch) and the named resumed runs (century_resume launches)."""
    dispatch_receipt, dispatch_acceptance = accepted(root, "dispatch-1", "century_dispatch", R0)
    entries = []
    for run_id in resumed:
        receipt, acceptance = accepted(root, "resume-" + run_id[:4], "century_resume", run_id)
        entries.append({"run_id": run_id, "plan_manifest_digest": DIGESTS[run_id], "resume_receipt": receipt, "resume_acceptance": acceptance})
    scope = {"chart_id": shared.CHART_ID, "generation": "5.0", "asset_id": shared.ASSET_ID, "run_id": R0, "plan_manifest_digest": DIGESTS[R0], "manifest_id": MANIFEST_ID,
             "input_vector_sha256": shared.evidence_digest(VECTOR), "dispatch_receipt": dispatch_receipt, "dispatch_acceptance": dispatch_acceptance}
    if entries:
        scope["resumed_runs"] = entries
    scope.update(over)
    return scope


def request(scope, kind="century_teardown_dryrun"):
    return {"kind": kind, "item_id": shared.CENTURY_ITEM, "century_scope" if kind.startswith("century") else "smalltest_scope": scope}


# ───────────────────────────── T1 the scope ─────────────────────────────
def oracle_t1_a_resumed_run_is_bound_to_its_accepted_resume_launch(module, tmp_path):
    root = tmp_path / "ok"
    scope = scope_of(root, (R1, R2))
    assert module.staged_scope(request(scope), root) == scope, "control failed — two resumed runs bound to their accepted century_resume launches"
    assert module.staged_scope(request(scope_of(tmp_path / "plain")), tmp_path / "plain")["run_id"] == R0, "a scope with no resumed runs is judged as before"

    def refused(label, text, scope, root_):
        with pytest.raises(module.Refused, match=text):
            module.staged_scope(request(scope), root_)

    root = tmp_path / "wrong-run"
    bad = scope_of(root, (R1,))
    bad["resumed_runs"][0]["run_id"] = R2                                          # names a run the cited launch did not start
    refused("another run than the launch's", "differs from the accepted century_resume launch", bad, root)
    root = tmp_path / "wrong-digest"
    bad = scope_of(root, (R1,))
    bad["resumed_runs"][0]["plan_manifest_digest"] = "9" * 64
    refused("another plan manifest than the launch's", "differs from the accepted century_resume launch", bad, root)
    root = tmp_path / "dispatch-as-resume"
    bad = scope_of(root, (R1,))
    bad["resumed_runs"][0]["resume_receipt"], bad["resumed_runs"][0]["resume_acceptance"] = accepted(root, "other-dispatch", "century_dispatch", R1)
    refused("a dispatch launch cited as a resume", "not independently accepted", bad, root)
    root = tmp_path / "unaccepted"
    bad = scope_of(root, (R1,))
    bad["resumed_runs"][0]["resume_receipt"], bad["resumed_runs"][0]["resume_acceptance"] = accepted(root, "unaccepted", "century_resume", R1, by="nobody")
    refused("a launch nobody accepted", "not independently accepted", bad, root)
    root = tmp_path / "duplicate"
    bad = scope_of(root, (R1,))
    bad["resumed_runs"].append(dict(bad["resumed_runs"][0]))
    refused("the same run twice", "distinct from every other run", bad, root)
    root = tmp_path / "primary-as-resumed"
    bad = scope_of(root, (R1,))
    bad["resumed_runs"][0]["run_id"] = R0
    refused("the identified run named as resumed", "distinct from every other run", bad, root)
    root = tmp_path / "empty"
    refused("an empty list", "non-empty list", scope_of(root, resumed=(), resumed_runs=[]), root)
    root = tmp_path / "extra-key"
    bad = scope_of(root, (R1,))
    bad["resumed_runs"][0]["note"] = "x"
    refused("an unknown key", "names exactly", bad, root)


def oracle_t1b_only_a_century_scope_carries_resumed_runs(module, tmp_path):
    root = tmp_path / "root"
    scope = scope_of(root, (R1,))
    with pytest.raises(module.Refused, match="century teardown scope only"):
        module.resumed_runs_problem(scope, root, False)
    assert module.resumed_runs_problem(scope, root, True) is None


# ───────────────────────────── T2 the deletion set ─────────────────────────────
class Cursor:
    """The rows `_bound_scope` reads: the surviving runs, the one candidate manifest and the coverage partitions (each the run that wrote it)."""

    def __init__(self, runs, coverage=()):
        self.runs, self.coverage, self.sql = runs, list(coverage), ""

    def execute(self, sql, params=None):
        self.sql, self.params = " ".join(sql.split()), params

    def fetchall(self):
        assert "FROM build_runs" in self.sql, self.sql
        return [{"id": r, "plan_manifest": MANIFESTS[r], "plan_manifest_digest": d} for r, d in self.runs]

    def fetchone(self):
        if "kala_gochara_publication" in self.sql:
            return {"manifest_id": MANIFEST_ID, "status": "candidate", "input_generation_vector": VECTOR, "horizon": None}
        assert "kala_gochara_coverage" in self.sql, self.sql
        allowed = self.params[2] if "ALL(" in self.sql else [self.params[2]]
        return {"n": sum(1 for built_by in self.coverage if built_by is None or built_by not in allowed)}


def bound(module, tmp_path, monkeypatch, *, resumed, owned, runs=None, coverage=(), name="root"):
    root = tmp_path / name
    scope = scope_of(root, resumed)
    monkeypatch.setattr(module.shared, "evidence_root", lambda: root)
    monkeypatch.setattr(module, "_writer", lambda: types.SimpleNamespace(TEST_SLICE_KEY="gochara_v5_test_slice"))
    surviving = [(r, DIGESTS[r]) for r in owned] if runs is None else runs
    return module._bound_scope(Cursor(surviving, coverage), owned, request(scope))


def oracle_t2_the_teardown_deletes_exactly_the_named_runs(module, tmp_path, monkeypatch):
    single = bound(module, tmp_path, monkeypatch, resumed=(), owned=[R0], coverage=[R0, R0], name="single")
    assert single["run_id"] == R0, "control failed — a scope with no resumed runs is judged as before"
    both = bound(module, tmp_path, monkeypatch, resumed=(R1,), owned=[R1, R0], coverage=[R0, R1, R1], name="both")
    assert [e["run_id"] for e in both["resumed_runs"]] == [R1], "control failed — the identified run and the named resumed run, in any order"
    three = bound(module, tmp_path, monkeypatch, resumed=(R1, R2), owned=[R0, R1, R2], coverage=[R2], name="three")
    assert len(three["resumed_runs"]) == 2

    def refused(text, **kw):
        with pytest.raises(module.TeardownRefused, match=text):
            bound(module, tmp_path, monkeypatch, name=str(abs(hash(str(kw)))), **kw)
    refused("only the identified staged run may be deleted", resumed=(), owned=[R0, R1])                                     # an unnamed extra run
    refused("only the identified staged run and its named resumed runs may be deleted", resumed=(R1,), owned=[R0])           # a named run that no longer exists
    refused("only the identified staged run and its named resumed runs may be deleted", resumed=(R1,), owned=[R0, R1, R2])   # a further run the scope does not name
    refused("does not match the surviving run", resumed=(R1,), owned=[R0, R1], runs=[(R0, DIGESTS[R0]), (R1, "9" * 64)])      # a surviving run with another manifest digest
    refused("generation coverage was not created by the identified staged run", resumed=(R1,), owned=[R0, R1], coverage=[R0, FOREIGN])
    refused("generation coverage was not created by the identified staged run", resumed=(R1,), owned=[R0, R1], coverage=[None])
    refused("generation coverage was not created by the identified staged run", resumed=(), owned=[R0], coverage=[R1])         # without resumed runs the single-run rule is unchanged


def oracle_t3_the_foreign_coverage_query_runs_and_counts_runs_outside_the_set(module, tmp_path, monkeypatch):
    """The statement itself, against the local disposable cluster on a TEMP table shaped as migration 1081 (build_id TEXT): the fake cursor above cannot tell a type error."""
    import os
    try:
        import psycopg
        import psycopg.rows
        conn = psycopg.connect(os.environ.get("KALA_ADMIN_DSN", "postgresql://postgres@127.0.0.1:55433/postgres"), autocommit=True, connect_timeout=3, row_factory=psycopg.rows.dict_row)
    except Exception:
        if os.environ.get("KALA_REQUIRE_DB") == "1":
            pytest.fail("KALA_REQUIRE_DB=1 and the local cluster is unreachable")
        pytest.skip("local cluster unreachable: deferred to CI")
    with conn:
        conn.execute("CREATE TEMP TABLE kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, build_id text)")
        for chart, generation, kind, built_by in ((shared.CHART_ID, "5.0", "event_class", R0), (shared.CHART_ID, "5.0", "event_class", R1), (shared.CHART_ID, "5.0", "event_class", FOREIGN),
                                                  (shared.CHART_ID, "5.0", "chart", FOREIGN), (shared.CHART_ID, "4.0", "event_class", FOREIGN)):
            conn.execute("INSERT INTO kala_gochara_coverage VALUES (%s, %s, %s, %s)", [chart, generation, kind, built_by])
        count = lambda owned: module.shared.count(conn.cursor(), module.RESUMED_FOREIGN_COVERAGE_SQL, (shared.CHART_ID, "5.0", owned))
        assert count([R0, R1]) == 1, "only the event_class partition of another run, of this generation, is foreign"
        assert count([R0, R1, FOREIGN]) == 0 and count([R0]) == 2


SHARED = SCRIPTS / "v5_small_test_shared.py"
TEARDOWN = SCRIPTS / "teardown_v5_small_test_job.py"
ORACLES = {
    "t1": (oracle_t1_a_resumed_run_is_bound_to_its_accepted_resume_launch, SHARED, ("launch.get('run_id') != entry['run_id']", "False")),
    "t1b": (oracle_t1b_only_a_century_scope_carries_resumed_runs, SHARED, ("    if not century:\n        raise Refused('resumed_runs belong to the century teardown scope only')\n", "")),
    "t3": (oracle_t3_the_foreign_coverage_query_runs_and_counts_runs_outside_the_set, TEARDOWN, ("AND build_id <> ALL(%s::text[])", "AND build_id = ANY(%s::text[])")),
    "t2": (oracle_t2_the_teardown_deletes_exactly_the_named_runs, TEARDOWN,
           ('    if sorted(owned) != sorted([scope["run_id"], *resumed]):', '    if False:')),
}


def call(oracle, module, tmp_path, monkeypatch):
    names = oracle.__code__.co_varnames[:oracle.__code__.co_argcount]
    return oracle(module, tmp_path, monkeypatch) if "monkeypatch" in names else oracle(module, tmp_path)


def real_module(source):
    return {"v5_small_test_shared.py": shared, "teardown_v5_small_test_job.py": teardown}[Path(source).name]


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_module(tmp_path, monkeypatch, claim):
    oracle, source, _ = ORACLES[claim]
    call(oracle, real_module(source), tmp_path, monkeypatch)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, source, mutation = ORACLES[claim]
    copy = module_copy(tmp_path / "copy", source, mutation)
    with pytest.raises((AssertionError, pytest.fail.Exception, shared.Refused, copy.Refused, getattr(copy, "TeardownRefused", shared.Refused))) as caught:
        call(oracle, copy, tmp_path / "run", monkeypatch)
    assert "mutation anchor" not in str(caught.value)
