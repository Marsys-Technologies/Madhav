"""Static tests (no database): 1274 is never run by migrate.ts; the steps; the gate pins; the Python 3.11 grammar; the plan binds what runs."""
from __future__ import annotations

import ast
import hashlib
import pathlib
import re
import sys

import pytest

import conftest as cf
from conftest import EXEC_DIR, REPO

PLATFORM = REPO / "platform"
GATE_V2 = EXEC_DIR.parent / "gate_v2"


@pytest.fixture(scope="module")
def mod():
    return cf.load_exec("mig_1274_static")


# ------------------------------------------------------------------------------- 1274 is NEVER run by migrate.ts
def migrate_dirs():
    """The folders platform/scripts/migrate.ts reads, parsed from its own source (main()'s `dirs = [...]`)."""
    src = (PLATFORM / "scripts/migrate.ts").read_text()
    block = re.search(r"const dirs = \[(.*?)\]", src, re.S).group(1)
    rels = re.findall(r"path\.resolve\(scriptDir, '([^']+)'\)", block)
    assert rels, "could not parse migrate.ts dirs"
    return [(PLATFORM / "scripts" / r).resolve() for r in rels]


def test_migrate_ts_reads_only_these_two_folders_non_recursively():
    dirs = migrate_dirs()
    assert dirs == [(PLATFORM / "migrations").resolve(), (PLATFORM / "supabase/migrations").resolve()]
    src = (PLATFORM / "scripts/migrate.ts").read_text()
    body = src[src.index("export function collectMigrationFiles"):]
    body = body[:body.index("files.sort")]
    assert "readdirSync(dir)" in body and "recursive" not in body and ".endsWith('.sql')" in body      # flat listing of each dir, *.sql only


def test_no_1274_file_is_in_a_folder_migrate_ts_reads():
    for d in migrate_dirs():
        assert not [f.name for f in d.iterdir() if f.name.endswith(".sql") and re.match(r"^1274\D", f.name)], d
        assert not [f.name for f in d.iterdir() if "life_events_chart_scoped" in f.name], d


def test_the_1274_sql_files_live_outside_every_discovery_folder_and_carry_the_number():
    dirs = migrate_dirs()
    for f in (EXEC_DIR / "1274_life_events_chart_scoped_view.sql", EXEC_DIR / "1274_life_events_chart_scoped_view_ROLLBACK.sql"):
        assert f.is_file() and f.name.startswith("1274_")
        assert f.parent.resolve() not in dirs and not any(d in f.resolve().parents for d in dirs)
    # a discovery pass over the real folders (what collectMigrationFiles does, in Python) finds neither file
    found = sorted(n for d in dirs for n in (p.name for p in d.iterdir()) if n.endswith(".sql"))
    assert not [n for n in found if n.startswith("1274_")]


def test_the_header_says_it_is_never_run_by_migrate_ts():
    head = (EXEC_DIR / "1274_life_events_chart_scoped_view.sql").read_text().split("-- @@STEP")[0]
    assert "NEVER RUN BY platform/scripts/migrate.ts" in head


# ------------------------------------------------------------------------------- the legs
def test_steps_parse_and_the_header_is_not_executed(mod):
    f = mod.forward_leg().steps
    assert [n for n, _ in f] == ["s1_assume_owner_roles", "s2_preconditions", "s3_transient_create_for_the_table_owner", "s4_create_view_as_table_owner",
                                 "s5_revoke_transient_create", "s6_behavioural_probe_as_owner", "s7_behavioural_probe_as_builder", "s8_post_assertions",
                                 "s9_restore_memberships"]
    r = mod.rollback_leg().steps
    assert [n for n, _ in r] == ["r1_assume_owner_roles", "r2_preconditions", "r3_drop_view_as_owner", "r4_post_assertions", "r5_restore_memberships"]
    assert not any("HISTORY + OWNER-PATH" in s for _, s in f)


def test_a_step_may_not_control_the_transaction(mod):
    with pytest.raises(ValueError):
        mod.parse_steps("-- @@STEP a\nSELECT 1;\nCOMMIT;\n")
    with pytest.raises(ValueError):
        mod.parse_steps("-- @@STEP a\nSELECT 1;\n-- @@STEP a\nSELECT 2;\n")
    with pytest.raises(ValueError):
        mod.parse_steps("no steps at all")


def test_the_forward_sql_never_touches_data_and_only_reads_the_table_for_counts():
    sql = (EXEC_DIR / "1274_life_events_chart_scoped_view.sql").read_text()
    code = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))
    # N-46: no statement may change or delete a life_events row; the only DML words are the probe's denied-write attempts on the VIEW
    assert not re.search(r"(?i)\b(INSERT\s+INTO|UPDATE|DELETE\s+FROM|TRUNCATE)\s+public\.life_events\b(?!_chart_scoped)", code)
    assert not re.search(r"(?i)\bDROP\b|\bALTER\s+TABLE\b", code)
    assert "GRANT SELECT ON public.life_events_chart_scoped TO data_plane_builder;" in code
    # REVOKE nothing existing: the only REVOKEs are on the NEW view and the transient CREATE this file granted
    revokes = re.findall(r"(?im)^\s*REVOKE\b[^;]*;", code)
    assert sorted(revokes) == sorted(["REVOKE ALL ON public.life_events_chart_scoped FROM PUBLIC, retrieval_census_ro;", "REVOKE CREATE ON SCHEMA public FROM amjis_app;",
                                      "REVOKE SELECT (id, event_date, category, description, outcome_observed) ON public.life_events FROM data_plane_builder;"])


# ------------------------------------------------------------------------------- gate + plan
def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def test_the_gate_pins_equal_the_shipped_gate_v2_files(mod):
    assert mod.GATE_PINS == {n: sha(GATE_V2 / n) for n in ("prerun_gate.py", "run_gated.sh", "executor_standards.py")}


def test_the_plan_hash_binds_the_sql_the_gate_and_the_executor(mod, monkeypatch, tmp_path):
    base = mod.plan_hash()
    assert len(base) == 64 and base == mod.plan_hash()
    text = mod.render_plan()
    assert mod.forward_leg().sql_sha256 in text and mod.rollback_leg().sql_sha256 in text and mod.exec_sha() in text
    for pin in mod.GATE_PINS.values():
        assert pin in text
    p = tmp_path / "f.sql"
    p.write_text(mod.SQL_FORWARD.read_text().replace("security_barrier = true", "security_barrier = false", 1))
    monkeypatch.setattr(mod, "SQL_FORWARD", p)
    assert mod.plan_hash() != base                                         # any SQL edit changes the plan hash
    monkeypatch.undo()
    assert mod.plan_hash(pins={**mod.GATE_PINS, "run_gated.sh": "0" * 64}) != base      # and so does a gate pin


def test_main_refuses_without_a_launch_marker(mod, monkeypatch, capsys):
    monkeypatch.delenv("GATE_V2_LAUNCH", raising=False)
    with pytest.raises(SystemExit) as e:
        mod.main(["--count", "--expect-plan", "0" * 64])
    assert e.value.code == 93 and "run_gated.sh" in capsys.readouterr().err


def test_launch_gate_accepts_a_genuine_marker_and_refuses_a_forged_or_missing_one(mod):
    es = mod.standards()
    marker = es.make_marker(str(GATE_V2 / "prerun_gate.py"), str(GATE_V2 / "run_gated.sh"))
    fp = mod.launch_gate({"GATE_V2_LAUNCH": marker})
    assert fp["gate_sha256"] == mod.GATE_PINS["prerun_gate.py"] and fp["run_gated_sha256"] == mod.GATE_PINS["run_gated.sh"] and fp["under_test"] is False
    forged = marker[:-1] + ("0" if marker[-1] != "0" else "1")
    for env in ({"GATE_V2_LAUNCH": forged}, {}):
        with pytest.raises(SystemExit) as e:
            mod.launch_gate(env)
        assert e.value.code == 93


def test_test_only_redirects_are_refused_outside_pytest(mod):
    with pytest.raises(SystemExit) as e:
        mod.gate_dir({"M1274_TEST_GATE_DIR": "/tmp/x"})
    assert e.value.code == 95
    with pytest.raises(SystemExit) as e:
        mod.resolve_evidence_root(None, {"M1274_TEST_EVIDENCE_ROOT": "/tmp/x"})
    assert e.value.code == 95


# ------------------------------------------------------------------------------- Python 3.11 floor
def _py_files():
    return sorted(p for p in EXEC_DIR.rglob("*.py") if "__pycache__" not in p.parts)


@pytest.mark.parametrize("path", _py_files(), ids=lambda p: p.relative_to(EXEC_DIR).as_posix())
def test_every_file_parses_under_the_python_311_grammar(path):
    ast.parse(path.read_text(), filename=str(path), feature_version=(3, 11))


def test_no_reused_quote_inside_an_fstring_replacement_field():
    import io
    import tokenize
    if sys.version_info < (3, 12):
        pytest.skip("on < 3.12 the parser itself rejects the construct")
    bad = []
    for p in _py_files():
        stack = []
        for tok in tokenize.generate_tokens(io.StringIO(p.read_text()).readline):
            if tok.type == tokenize.FSTRING_START:
                stack.append(tok.string[-1])
            elif tok.type == tokenize.FSTRING_END:
                stack.pop()
            elif tok.type == tokenize.STRING and stack and tok.string.lstrip("rbuRBU")[:1] == stack[-1]:
                bad.append(f"{p.name}:{tok.start[0]}")
    assert bad == []


def test_plan_txt_is_the_rendered_plan(mod):
    """plan.txt is what the operator reads and approves; it must be exactly what the plan hash covers (regenerate with make_plan.py --write)."""
    assert (EXEC_DIR / "plan.txt").read_text() == mod.render_plan() + "\n"


def test_the_accepted_limit_is_stated_in_the_sql_and_in_the_plan(mod):
    """SS N-109 accepted limit: the GUC scoping stops accidental cross-chart reads, not a hostile builder session. It must stay written down."""
    head = (EXEC_DIR / "1274_life_events_chart_scoped_view.sql").read_text().split("-- @@STEP")[0]
    assert "ACCEPTED LIMIT" in head and "HOSTILE builder session" in head
    assert "accepted limit" in mod.render_plan() and "HOSTILE builder session" in mod.render_plan()


def test_the_view_has_seven_columns_and_no_free_text(mod):
    assert mod.VIEW_COLUMNS == ("id", "event_id", "event_date", "category", "domain", "chart_id")
    s4 = (EXEC_DIR / "1274_life_events_chart_scoped_view.sql").read_text().split("-- @@STEP s4")[1].split("-- @@STEP s5")[0]
    create_view = s4[s4.index("CREATE VIEW"):s4.index(";", s4.index("CREATE VIEW"))]
    assert "description" not in create_view and "outcome_observed" not in create_view


def test_the_landing_sequence_and_the_column_revoke_are_stated_in_the_sql_and_the_plan(mod):
    head = (EXEC_DIR / "1274_life_events_chart_scoped_view.sql").read_text().split("-- @@STEP")[0]
    assert "LANDING SEQUENCE" in head and "ONE slot" in head and "NO build in between" in head
    plan = mod.render_plan()
    assert "landing sequence" in plan and "NO build in between" in plan and "builder column grants" in plan
    assert mod.EXPECTED_BUILDER_COLUMN_ACL == ["category:SELECT:false:amjis_app", "description:SELECT:false:amjis_app", "event_date:SELECT:false:amjis_app",
                                               "id:SELECT:false:amjis_app", "outcome_observed:SELECT:false:amjis_app"]
