"""SR-RESUME-NOW (OWNER-RESUMABLE-REQUIRED-20261025): the century RESUME staging binding, platform/scripts/dispatch_v5_century_resume_job.py, and the one hook it needs in
dispatch_v5_small_test_job._admit.

Doctrine: root CLAUDE.md §N.8 (each claim is measured by a detector that can read false) and §B.10 (no invented value). One oracle per distinct production claim; each passes on the
real module and FAILS on a copy of it with that ONE claim's line reverted (the planted reversion). The live gate runs against the local disposable cluster (127.0.0.1:55433,
KALA_REQUIRE_DB=1) on TEMP tables only: they shadow the real names for one session and nothing outlives the connection. The ledger is the writer lane's (migration 1410); the gate reads
the table and the `writer_digest` column through the RESUME_* constants of v5_small_test_shared.

  S1 the live gate admits a resume only over a ledger written by the request's writer program
  S2 nothing to resume refuses by name: no candidate manifest, no ledger table, an empty ledger
  S3 the run being resumed must be an unfinished century run of this chart
  S4 _admit's hook replaces ONLY the refusal of existing generation 5.0 output (the dispatch still refuses it) and judges the N-137 end state with the century trigger too
  S5 the staging mode and the executor kind agree, the dry run stages with --dry-run only (no launch, no cloud call, no commit) and its proof names the resume it was staged for
  S6 a request whose program identity is not the century contract's writer program refuses (pure check shared by the staging rollback and the launcher)
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
REPO = SCRIPTS.parents[1]
for folder in (SCRIPTS, SCRIPTS / "__tests__"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import century_resume_support as S  # noqa: E402
import dispatch_v5_century_resume_job as binding  # noqa: E402
import dispatch_v5_small_test_job as staging  # noqa: E402
import v5_small_test_shared as shared  # noqa: E402

CLUSTER = os.environ.get("KALA_ADMIN_DSN", "postgresql://postgres@127.0.0.1:55433/postgres")
CONTRACT = json.loads((REPO / "00_ARCHITECTURE/briefs/kalayantra/fleet/century_contract.json").read_text())
WRITER = CONTRACT["image"]["writer_source_digest"]
OTHER_RUN = "99999999-9999-4999-8999-999999999999"


def module_copy(tmp_path, source, mutation=None):
    """A module of this tree, or a copy with ONE line reverted (the planted reversion)."""
    text = Path(source).read_text()
    if mutation:
        old, new = mutation
        if text.count(old) != 1:
            raise RuntimeError(f"mutation anchor not unique: {old!r}")      # a bad anchor must never read as a failed oracle
        text = text.replace(old, new)
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / f"{Path(source).stem}_{abs(hash(mutation))}.py"
    path.write_text(text)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cluster():
    try:
        import psycopg
        import psycopg.rows
        return psycopg.connect(CLUSTER, autocommit=True, connect_timeout=3, row_factory=psycopg.rows.dict_row)
    except Exception:
        if os.environ.get("KALA_REQUIRE_DB") == "1":
            pytest.fail("KALA_REQUIRE_DB=1 and the local cluster is unreachable")
        pytest.skip("local cluster unreachable: deferred to CI")


def world(conn, *, ledger=("snapshot", "inventory:career"), writer=WRITER, run_state="failed", trigger=shared.CENTURY_TRIGGERED_BY, with_ledger_table=True):
    """TEMP tables shadowing the real names for this session: the run being resumed and the writer's ledger."""
    conn.execute("CREATE TEMP TABLE build_runs (id uuid, chart_id uuid, state text, triggered_by text)")
    conn.execute("INSERT INTO build_runs VALUES (%s, %s, %s, %s)", [S.RUN, shared.CHART_ID, run_state, trigger])
    if with_ledger_table:
        conn.execute(f"CREATE TEMP TABLE {shared.RESUME_LEDGER_TABLE} (chart_id uuid, generation text, substep_key text, writer_digest text)")
        for key in ledger:
            conn.execute(f"INSERT INTO {shared.RESUME_LEDGER_TABLE} VALUES (%s, '5.0', %s, %s)", [shared.CHART_ID, key, writer])


def gate_request(**over):
    return {"resume_run_id": S.RUN, "program_identity": dict(S.IDENTITY, writer_digest=WRITER), **over}


CANDIDATE = {"manifest_id": "m", "status": "candidate"}


# ───────────────────────────── S1 / S2 / S3 the live gate ─────────────────────────────
def oracle_s1_a_resume_continues_only_the_same_program(module, tmp_path):
    conn = cluster()
    with conn:
        world(conn)
        notes = module.resume_gate(gate_request())(conn.cursor(), 4, CANDIDATE)
        assert len(notes) == 1 and "2 committed substep(s)" in notes[0] and S.RUN in notes[0], "control failed — the ledger of the request's program is admitted"
        conn.execute(f"INSERT INTO {shared.RESUME_LEDGER_TABLE} VALUES (%s, '5.0', 'window:career:p1', %s)", [shared.CHART_ID, "1" * 64])      # one substep by another program
        with pytest.raises(shared.Refused, match=r"1 ledger substep\(s\) were committed by a writer program other than the request's"):
            module.resume_gate(gate_request())(conn.cursor(), 4, CANDIDATE)


def oracle_s2_nothing_to_resume_refuses_by_name(module, tmp_path):
    conn = cluster()
    with conn:
        world(conn, ledger=())
        with pytest.raises(shared.Refused, match="holds no committed substep"):
            module.resume_gate(gate_request())(conn.cursor(), 4, CANDIDATE)
        for manifest, text in ((None, "no candidate manifest"), ({"manifest_id": "m", "status": "published"}, "status published")):
            with pytest.raises(shared.Refused, match=text):
                module.resume_gate(gate_request())(conn.cursor(), 4, manifest)
    conn = cluster()
    with conn:
        world(conn, with_ledger_table=False)
        with pytest.raises(shared.Refused, match="ledger ka_gochara_build_ledger does not exist"):
            module.resume_gate(gate_request())(conn.cursor(), 4, CANDIDATE)


def oracle_s3_the_run_to_resume_is_an_unfinished_century_run_of_this_chart(module, tmp_path):
    for label, kwargs, run_id in (("a completed run", dict(run_state="completed"), S.RUN), ("a small-test run", dict(trigger=shared.TRIGGERED_BY), S.RUN),
                                  ("an unknown run", {}, OTHER_RUN)):
        conn = cluster()
        with conn:
            world(conn, **kwargs)
            with pytest.raises(shared.Refused, match="is not an unfinished century run of chart"):
                module.resume_gate(gate_request(resume_run_id=run_id))(conn.cursor(), 4, CANDIDATE)
    conn = cluster()
    with conn:
        world(conn, run_state="failed")
        module.resume_gate(gate_request())(conn.cursor(), 4, CANDIDATE)          # control: a failed century run resumes


# ───────────────────────────── S4 the admission hook ─────────────────────────────
class Cursor:
    def execute(self, sql, params=None):
        self.sql = " ".join(sql.split())

    def fetchall(self):
        return []                                  # no active build run


def hooked(module, monkeypatch, *, output_rows=7):
    """`_admit` with every other read replaced by a recorder, so only the hook's behaviour is under test."""
    seen = {"end_state": []}
    monkeypatch.setattr(module, "_take_chart_lock", lambda cur: None)
    monkeypatch.setattr(module.shared, "refuse_if_frozen", lambda cur: None)
    monkeypatch.setattr(module, "_validate_registry_row", lambda cur: [])
    monkeypatch.setattr(module, "_check_dependencies_ready", lambda cur, depends_on: None)
    monkeypatch.setattr(module.shared, "end_state_problems", lambda cur, *triggers: seen["end_state"].append(triggers) or [])
    monkeypatch.setattr(module.shared, "count", lambda cur, sql, params=(): 0)
    monkeypatch.setattr(module, "_existing_small_test_runs", lambda cur: [])
    monkeypatch.setattr(module.shared, "generation_exists", lambda cur: (output_rows, CANDIDATE if output_rows else None))
    return seen


def oracle_s4_the_hook_replaces_only_the_existing_output_refusal(module, tmp_path, monkeypatch):
    seen = hooked(module, monkeypatch)
    with pytest.raises(module.shared.Refused, match="already has output"):
        module._admit(Cursor())                                                        # the dispatch: unchanged
    assert seen["end_state"] == [()], "the dispatch judges the N-137 end state exactly as before (the default trigger)"
    seen["end_state"].clear()
    calls = []
    existing, notes = module._admit(Cursor(), resume=lambda cur, rows, manifest: calls.append((rows, manifest)) or ["resuming"])
    assert (existing, notes, calls) == ([], ["resuming"], [(7, CANDIDATE)])
    assert seen["end_state"] == [((module.TRIGGERED_BY, module.shared.CENTURY_TRIGGERED_BY),)], "a resume judges the end state with the century trigger too: the resumed run is itself a century run"
    # nothing else is relaxed: a refusing hook refuses the admission
    with pytest.raises(module.shared.Refused, match="nope"):
        module._admit(Cursor(), resume=lambda cur, rows, manifest: (_ for _ in ()).throw(module.shared.Refused("nope")))


# ───────────────────────────── S5 the modes and the dry run ─────────────────────────────
DRY = ["--i-am-steward", "--after-settled-1", "--dry-run", "--classes", "all", "--final_rules", "true", "--defer_in_build_verify", "true",
       "--horizon", S.ARGS["horizon"], "--result_policy", "window_qualification/1"]


def staged_request(tmp_path, kind):
    root = tmp_path / "ops"
    root.mkdir(parents=True, exist_ok=True)
    req = S.scenario(root, request_identity=dict(S.IDENTITY, writer_digest=WRITER), identity=dict(S.IDENTITY, writer_digest=WRITER), kind=kind, operation_id="op-dry")
    return root, req


def run_main(module, tmp_path, monkeypatch, argv, kind):
    """The resume binding's main() against a staged request, with the transaction replaced by a recorder and every process / network call forbidden."""
    root, req = staged_request(tmp_path, kind)
    monkeypatch.setenv("KY_ROOT", str(root.parent))
    monkeypatch.setattr(module.shared, "evidence_root", lambda: root)
    monkeypatch.setattr(module.shared, "operation_request", lambda: req)
    monkeypatch.setattr(module.shared, "century_request_problem", lambda r, root_: None)       # the evidence gate has its own oracles (test_century_resume_gate)
    monkeypatch.setattr(module, "century_shape", lambda **kw: {"classes": "all"})
    forbidden = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: forbidden.append(a))
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: forbidden.append(a))
    staged = []
    monkeypatch.setattr(module.staging, "_main", lambda argv_, **kw: staged.append((list(argv_), kw)) or print(json.dumps({"run_id": S.NEW_RUN, "launch_plan": {"async_launch": True}})))
    out = io.StringIO()
    real = sys.stdout
    sys.stdout = out
    try:
        module.main(argv)
    finally:
        sys.stdout = real
    return req, staged, forbidden, out.getvalue()


def oracle_s5_the_dry_run_stages_with_dry_run_only_and_names_its_resume(module, tmp_path, monkeypatch):
    req, staged, forbidden, out = run_main(module, tmp_path / "dry", monkeypatch, DRY, "century_resume_dryrun")
    assert len(staged) == 1 and "--dry-run" in staged[0][0] and "--execute" not in staged[0][0], "the dry run stages in a rolled-back transaction"
    assert staged[0][1]["operation_kind"] == "century_resume" and staged[0][1]["triggered_by"] == "gochara-v5-century" and callable(staged[0][1]["admit"])
    assert forbidden == [], "the dry run called a process"
    proof = json.loads(out)
    assert (proof["schema"], proof["status"], proof["rollback_confirmed"]) == ("ky.century_staging/1", "ROLLED_BACK", True)
    assert proof["resume"] == {"resumes": req["resumes"]["name"], "resume_run_id": req["resume_run_id"], "program_identity": req["program_identity"]}
    assert proof["request_sha256"] == module.shared.request_hash(req) and proof["args"] == req["args"] and proof["run_id"] == S.NEW_RUN
    # the mode and the executor kind agree, both ways
    with pytest.raises(module.shared.Refused, match="executor operation kind and century resume mode differ"):
        run_main(module, tmp_path / "wrong-kind-dry", monkeypatch, DRY, "century_resume")
    with pytest.raises(module.shared.Refused, match="executor operation kind and century resume mode differ"):
        run_main(module, tmp_path / "wrong-kind-exec", monkeypatch, [a if a != "--dry-run" else "--execute" for a in DRY], "century_resume_dryrun")
    assert "launch_staged" not in Path(module.__file__).read_text(), "the staging binding never launches: that is century_launch.py's"


# ───────────────────────────── S6 the program identity ─────────────────────────────
def oracle_s6_the_program_identity_is_the_contracts_writer_program(module, tmp_path):
    module.resume_program_problem({"program_identity": {"writer_digest": WRITER}}, CONTRACT)          # control: admitted
    for label, req, contract in (("another program", {"program_identity": {"writer_digest": "1" * 64}}, CONTRACT), ("no identity", {}, CONTRACT),
                                 ("identity not a mapping", {"program_identity": WRITER}, CONTRACT), ("no contract digest", {"program_identity": {"writer_digest": WRITER}}, {"image": {}}),
                                 ("no contract", {"program_identity": {"writer_digest": WRITER}}, None)):
        with pytest.raises(module.Refused, match="differs from the century contract writer_source_digest"):
            module.resume_program_problem(req, contract)


def test_the_resume_staging_reads_the_contract_of_its_own_tree():
    assert binding.load_contract() == CONTRACT and binding.CONTRACT == REPO / "00_ARCHITECTURE/briefs/kalayantra/fleet/century_contract.json"


# claim -> (module under test, the ONE planted reversion that must make its oracle fail)
RESUME_JOB = SCRIPTS / "dispatch_v5_century_resume_job.py"
ORACLES = {
    "s1": (oracle_s1_a_resume_continues_only_the_same_program, RESUME_JOB, ('        if other:\n', '        if False:\n')),
    "s2": (oracle_s2_nothing_to_resume_refuses_by_name, RESUME_JOB, ('        if not committed:\n', '        if False:\n')),
    "s3": (oracle_s3_the_run_to_resume_is_an_unfinished_century_run_of_this_chart, RESUME_JOB,
           ('if run is None or run["triggered_by"] != shared.CENTURY_TRIGGERED_BY or run["state"] == "completed":', 'if False:')),
    "s4": (oracle_s4_the_hook_replaces_only_the_existing_output_refusal, SCRIPTS / "dispatch_v5_small_test_job.py",
           ("    if resume is not None:\n        notes.extend(resume(cur, rows, manifest))\n    elif rows or manifest is not None:", "    if False:\n        pass\n    elif rows or manifest is not None:")),
    "s5": (oracle_s5_the_dry_run_stages_with_dry_run_only_and_names_its_resume, RESUME_JOB,
           ('    expected = "century_resume" if args.execute else "century_resume_dryrun"', '    expected = req.get("kind")')),
    "s6": (oracle_s6_the_program_identity_is_the_contracts_writer_program, SCRIPTS / "v5_small_test_shared.py",
           ("identity.get('writer_digest') == declared)", "True)")),
}


def call(oracle, module, tmp_path, monkeypatch):
    names = oracle.__code__.co_varnames[:oracle.__code__.co_argcount]
    return oracle(module, tmp_path, monkeypatch) if "monkeypatch" in names else oracle(module, tmp_path)


def real_module(source):
    return {"dispatch_v5_century_resume_job.py": binding, "dispatch_v5_small_test_job.py": staging, "v5_small_test_shared.py": shared}[Path(source).name]


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_passes_on_the_real_module(tmp_path, monkeypatch, claim):
    oracle, source, _ = ORACLES[claim]
    call(oracle, real_module(source), tmp_path, monkeypatch)


@pytest.mark.parametrize("claim", sorted(ORACLES))
def test_oracle_fails_on_its_planted_reversion(tmp_path, monkeypatch, claim):
    oracle, source, mutation = ORACLES[claim]
    copy = module_copy(tmp_path / "copy", source, mutation)
    if Path(source).name == "dispatch_v5_century_resume_job.py":
        copy.century_shape = lambda **kw: {"classes": "all"}       # as run_main does for the real one
        copy.CONTRACT = binding.CONTRACT                           # the copy sits outside the tree: point it at the tree's contract
    with pytest.raises((AssertionError, pytest.fail.Exception, shared.Refused)) as caught:
        call(oracle, copy, tmp_path / "run", monkeypatch)
    assert "mutation anchor" not in str(caught.value)
