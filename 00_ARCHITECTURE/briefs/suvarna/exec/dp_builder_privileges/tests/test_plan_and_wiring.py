"""Pure tests (no database): the bound pre/post state, the plan hash, the gate wiring, the interpreter binding and the SQL history files."""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib

import pytest

from conftest import FOLDER

GATE = FOLDER.parent / "gate_v2"


def test_live_definition_and_patched_definition_are_the_bound_ones(ex):
    p = ex.BIND_PATCH
    live, new = p.live_def(), p.patched_def()
    assert hashlib.md5(live.encode()).hexdigest() == p.live_md5 and len(live) == p.live_len
    assert hashlib.sha256(live.encode()).hexdigest() == p.live_sha256     # equals production's l2_data_plane_function_attestations digest, read 2026-10-03
    assert hashlib.md5(new.encode()).hexdigest() == p.patched_md5 and hashlib.sha256(new.encode()).hexdigest() == p.patched_sha256
    assert len(ex.bp.unified_hunks(live, new)) == 2 == p.diff_hunks and ex.bp.diff_digest(live, new) == p.diff_sha256


def test_the_patched_body_differs_from_the_live_body_only_by_the_two_insertions(ex):
    import difflib
    live, new = ex.BIND_PATCH.live_def(), ex.BIND_PATCH.patched_def()
    live_lines, new_lines = live.splitlines(), new.splitlines()
    ops = [o for o in difflib.SequenceMatcher(None, live_lines, new_lines, autojunk=False).get_opcodes() if o[0] != "equal"]
    assert [o[0] for o in ops] == ["insert", "insert"], ops                      # nothing removed or changed: two pure insertions
    inserted = ["\n".join(new_lines[o[3]:o[4]]) for o in ops]
    assert [new_lines[:ops[0][3]] + new_lines[ops[0][4]:ops[1][3]] + new_lines[ops[1][4]:]] == [live_lines]
    for text in inserted:
        # the grant goes to exactly the builder, BY NAME (the loop variable that just created the shadow), never PUBLIC, never a pg_class scan (review LOW-4)
        assert text.count("GRANT SELECT") == 1 and "TO data_plane_builder', v_table" in text
        assert "pg_class" not in text and "relowner" not in text and "PUBLIC" not in text.replace("pg_catalog", "")
    # each grant sits directly after the END of a CREATE TEMP TABLE pass, inside the loop, and before the receipt
    assert new.index("TO data_plane_builder', v_table") < new.index("CREATE TEMP TABLE l2_data_plane_bind_receipt")
    assert new.count("GRANT SELECT ON pg_temp.%I TO data_plane_builder") == 2 and live.count("GRANT") == 0
    assert "l2_data_plane_bind_receipt" not in "".join(inserted), "the bind receipt is never granted"


def test_hunk_refuses_a_missing_anchor_and_a_second_application(ex):
    live = ex.BIND_PATCH.live_def()
    with pytest.raises(ValueError):
        ex.bp.apply_hunks(live.replace("SELECT DISTINCT source_table", "SELECT DISTINCT zz_source_table"), ex.BIND_PATCH.hunks)
    with pytest.raises(ValueError):
        ex.bp.apply_hunks(ex.BIND_PATCH.patched_def(), ex.BIND_PATCH.hunks)


def test_a_tampered_live_file_or_hunk_is_refused_before_any_work(ex, tmp_path, monkeypatch):
    p = ex.BIND_PATCH
    real = p.live_def()
    monkeypatch.setattr(ex, "LIVE_DEFS", tmp_path)
    (tmp_path / "bind_l2_exact_inputs.LIVE.sql").write_text(real + "-- tampered\n")
    with pytest.raises(ex.ExpectedDiffError):
        ex.forward_leg()
    monkeypatch.undo()
    bad = ex.dataclasses.replace(p, hunks=((p.hunks[0][0], p.hunks[0][1], p.hunks[0][2] + "-- x\n"),))
    with pytest.raises(ex.ExpectedDiffError):
        bad.patched_def()


def test_the_eight_identity_functions_are_exactly_the_four_families_and_their_namespaces(ex):
    sigs = [s for s, _ in ex.IDENTITY_FUNCTIONS]
    assert len(sigs) == 8 == len(set(sigs))
    assert {s.split("(")[0] for s in sigs} == {
        "bodha_signal_identity", "bodha_signal_identity_namespace", "bodha_cgm_node_identity", "bodha_cgm_node_identity_namespace",
        "bodha_cgm_edge_identity", "bodha_cgm_edge_identity_namespace", "bodha_contradiction_identity", "bodha_contradiction_identity_namespace"}
    stmts = ex.forward_leg().grant_sql
    assert len(stmts) == 8 and all(s.startswith("GRANT EXECUTE ON FUNCTION public.") and s.endswith(" TO data_plane_builder") for s in stmts)
    assert all(s.startswith("REVOKE EXECUTE ON FUNCTION public.") and s.endswith(" FROM data_plane_builder") for s in ex.rollback_leg().grant_sql)
    assert not any("PUBLIC" in s.upper().replace("PUBLIC.", "") for s in stmts)


def test_gate_pins_equal_the_gate_files_on_main(ex):
    for name, pin in ex.GATE_PINS.items():
        assert hashlib.sha256((GATE / name).read_bytes()).hexdigest() == pin, name


def test_plan_hash_changes_with_every_input(ex):
    base = ex.plan_hash_unbound()
    assert ex.plan_hash_unbound() == base
    assert ex.plan_hash_unbound(sha="0" * 64) != base                                         # the executor source
    pins = dict(ex.GATE_PINS, **{"run_gated.sh": "0" * 64})
    assert ex.plan_hash_unbound(pins=pins) != base                                            # a gate pin
    assert ex.plan_hash() != base                                                             # the gate binding
    text = ex.render_plan()
    for needle in (ex.BIND_PATCH.live_sha256, ex.BIND_PATCH.patched_sha256, ex.BIND_PATCH.diff_sha256, "GRANT EXECUTE ON FUNCTION public.bodha_signal_identity(",
                   "ASSERTING post-checks", "data_plane_l2_owner", "amjis_app", "(exit 92 otherwise)", "never run by migrate.ts"):
        assert needle in text or needle == "never run by migrate.ts" and "migrate.ts" in text, needle
    for n in ex.SQL_FILES:
        assert hashlib.sha256((FOLDER / n).read_bytes()).hexdigest() in text


def test_sql_history_files_are_generated_from_the_executor_data(ex):
    leg = ex.forward_leg()
    s1 = (FOLDER / ex.SQL_FILES[0]).read_text()
    s2 = (FOLDER / ex.SQL_FILES[1]).read_text()
    assert leg.to_def.rstrip("\n") + ";\n" in s1 and leg.to_sha in s1 and leg.from_md5 in s1
    for stmt in leg.grant_sql:
        assert stmt + ";" in s2
    for text in (s1, s2):
        assert "NEVER RUN BY migrate.ts" in text


def test_executor_source_is_python_311_compatible():
    for path in sorted(FOLDER.glob("*.py")):
        ast.parse(path.read_text(), feature_version=(3, 11))
        compile(path.read_text(), str(path), "exec")


def test_launch_is_refused_without_a_verifying_marker(ex, monkeypatch):
    monkeypatch.delenv("GATE_V2_LAUNCH", raising=False)
    with pytest.raises(SystemExit) as e:
        ex.launch_gate()
    assert e.value.code == ex.EXIT_NO_LAUNCH == 93


def test_an_unbound_pin_or_a_wrong_pin_is_refused(ex, monkeypatch, capsys):
    monkeypatch.setitem(ex.GATE_PINS, "run_gated.sh", ex.GATE_TBD)
    with pytest.raises(SystemExit) as e:
        ex.launch_gate()
    assert e.value.code == 93 and "TBD" in capsys.readouterr().err
    monkeypatch.setitem(ex.GATE_PINS, "run_gated.sh", "305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076")
    monkeypatch.setitem(ex.GATE_PINS, "executor_standards.py", "0" * 64)
    with pytest.raises(SystemExit) as e:
        ex.launch_gate()
    assert e.value.code == 93 and "differs from the version pinned" in capsys.readouterr().err      # refused for THIS reason, not merely for the missing marker


def test_an_under_test_marker_is_refused_outside_pytest(ex):
    with pytest.raises(SystemExit) as e:
        ex.refuse_under_test_outside_pytest({"under_test": True}, environ={})
    assert e.value.code == 93
    ex.refuse_under_test_outside_pytest({"under_test": True}, environ={"PYTEST_CURRENT_TEST": "x"})
    ex.refuse_under_test_outside_pytest({"under_test": False}, environ={})


def test_test_env_overrides_are_refused_outside_pytest(ex):
    with pytest.raises(SystemExit) as e:
        ex.gate_dir({"DPBP_TEST_GATE_DIR": "/x"})
    assert e.value.code == 95
    with pytest.raises(SystemExit) as e:
        ex.resolve_evidence_root(None, {"DPBP_TEST_EVIDENCE_ROOT": "/x"})
    assert e.value.code == 95
    with pytest.raises(SystemExit) as e:
        ex.resolve_evidence_root(None, {"DPBP_TEST_EVIDENCE_ROOT": "", "PYTEST_CURRENT_TEST": "x"})
    assert e.value.code == 95
    assert ex.resolve_evidence_root(None, {}) == ex.EVIDENCE_ROOT


def _record(root, name, digest, runtime):
    d = pathlib.Path(root) / name
    d.mkdir(parents=True)
    body = {"status": "dry_run", "evidence_digest": digest}
    body.update(runtime)
    (d / "outcome.json").write_text(json.dumps(body))


def _args(**kw):
    d = dict(evidence_root=None, expect_evidence=None)
    d.update(kw)
    return type("A", (), d)()


def test_apply_under_a_different_interpreter_exits_92_before_any_connection(ex, evidence):
    _record(evidence, "dry-run_20260101T000000000000Z", "d" * 64, dict(ex.runtime_record(), python_executable="/some/other/python3"))
    called = []
    with pytest.raises(SystemExit) as e:
        ex.execute(_args(mode="apply", expect_plan=ex.plan_hash(), expect_evidence="d" * 64), lambda: called.append(1))
    assert e.value.code == ex.EXIT_INTERPRETER == 92 and called == []
    outs = [json.loads(p.read_text()) for p in evidence.glob("apply_*/outcome.json")]
    assert outs and outs[0]["status"] == "failed" and "interpreter_differs_from_dry_run" in json.dumps(outs[0])


def test_apply_with_an_incomplete_dry_run_record_exits_92(ex, evidence):
    rt = dict(ex.runtime_record())
    rt.pop("libpq_version")
    _record(evidence, "dry-run_20260101T000000000000Z", "e" * 64, rt)
    with pytest.raises(SystemExit) as e:
        ex.execute(_args(mode="apply", expect_plan=ex.plan_hash(), expect_evidence="e" * 64), lambda: pytest.fail("connected"))
    assert e.value.code == 92


def test_a_wrong_plan_hash_never_connects(ex, evidence):
    with pytest.raises(SystemExit) as e:
        ex.execute(_args(mode="dry-run", expect_plan="0" * 64), lambda: pytest.fail("connected"))
    assert "REFUSED" in str(e.value)


def test_apply_without_expect_evidence_never_connects(ex, evidence):
    with pytest.raises(SystemExit):
        ex.execute(_args(mode="apply", expect_plan=ex.plan_hash()), lambda: pytest.fail("connected"))


def test_cli_parser_requires_expect_plan_and_evidence(ex):
    with pytest.raises(SystemExit):
        ex.parse_args(["--dry-run"])
    with pytest.raises(SystemExit):
        ex.parse_args(["--apply", "--expect-plan", "x"])
    assert ex.parse_args(["--apply", "--expect-plan", "x", "--expect-evidence", "y"]).mode == "apply"


def test_acl_set_parsing(ex):
    assert ex.acl_set("{a=X/b,c=X/d}") == {"a=X/b", "c=X/d"} and ex.acl_set("") == frozenset() and ex.acl_set(None) == frozenset()


# ------------------------------------------------------------------------------------------------ review of PR #3045: pure tests of the re-bound executor
def test_identity_body_guards_cover_exactly_the_eight_functions(ex):
    assert set(ex.IDENTITY_BODY_MD5) == {s for s, _ in ex.IDENTITY_FUNCTIONS} and len(ex.IDENTITY_BODY_MD5) == 8
    assert all(len(m) == 32 for m in ex.IDENTITY_BODY_MD5.values())


def test_plan_hash_binds_the_gate_table_lists_by_content(ex, monkeypatch):
    """LOW-3: a changed list in the gate's own source changes the plan hash (it used to be read at run time without being bound)."""
    base = ex.plan_hash_unbound()
    real = ex.load_gate_lists
    monkeypatch.setattr(ex, "load_gate_lists", lambda root=None: {k: (v[:-1] + ["zz_extra_table"] if k == "L2_ACTIVE_TABLES" else v) for k, v in real().items()})
    assert ex.plan_hash_unbound() != base
    text = ex.render_plan()
    assert "L2_ACTIVE_TABLES (29) sha256" in text and "L1_ACTIVE_TABLES (12) sha256" in text


def test_the_plan_text_states_the_new_checks(ex):
    text = ex.render_plan()
    for needle in ("pg_read_all_stats", f"exit {ex.EXIT_WRONG_TARGET}", "md5(pg_get_functiondef) as bound", "two"[:0] + "GRANT SELECT ON pg_temp.%I TO data_plane_builder"):
        assert needle in text, needle


class _FakeCur:
    def __init__(self, row): self.row = row
    def execute(self, *a, **k): pass
    def fetchone(self): return self.row


class _FakeConn:
    def __init__(self, row): self.row = row; self.rolled_back = 0
    def cursor(self): return _FakeCur(self.row)
    def rollback(self): self.rolled_back += 1


@pytest.mark.parametrize("row,ok", [
    (("postgres", "postgres", "amjis", 15, False, True, True, True), True),
    (("postgres", "postgres", "amjis", 15, True, True, True, True), False),          # superuser
    (("postgres", "postgres", "amjis", 15, False, False, True, True), False),        # no CREATEROLE
    (("postgres", "postgres", "other", 15, False, True, True, True), False),         # wrong database
    (("somebody", "somebody", "amjis", 15, False, True, True, True), False),         # wrong administrator
    (("postgres", "other_session_user", "amjis", 15, False, True, True, True), False),  # SET ROLE'd connection
    (("postgres", "postgres", "amjis", 16, False, True, True, True), False),         # wrong major version
])
def test_check_target_accepts_only_the_production_administrator(ex, row, ok):
    conn = _FakeConn(row)
    got, facts = ex.check_target(conn, ex.PRODUCTION_TARGET)
    assert got is ok and facts[0].startswith("target: current_user=") and conn.rolled_back == 1


def test_main_maps_a_commit_state_unknown_to_its_own_exit_code(ex, monkeypatch, capsys):
    monkeypatch.setattr(ex, "launch_gate", lambda environ=None: {"under_test": False})
    monkeypatch.setattr(ex, "install_signal_handlers", lambda: None)

    def boom(*a, **k):
        raise ex.CommitStateUnknown("OperationalError")
    monkeypatch.setattr(ex, "execute", boom)
    assert ex.main(["--count", "--expect-plan", "x"]) == ex.EXIT_COMMIT_UNKNOWN == 96
    assert "COMMIT STATE UNKNOWN" in capsys.readouterr().out
    monkeypatch.setattr(ex, "execute", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    assert ex.main(["--count", "--expect-plan", "x"]) == 1                       # an ordinary failure keeps exit 1


def test_the_distinct_exit_codes_do_not_collide(ex):
    codes = [ex.EXIT_INTERPRETER, ex.EXIT_NO_LAUNCH, ex.EXIT_WRONG_TARGET, ex.EXIT_TEST_ENV, ex.EXIT_COMMIT_UNKNOWN]
    assert len(set(codes)) == 5 and sorted(codes) == [92, 93, 94, 95, 96]
