"""Static tests (no database): the package is never run by migrate.ts; the steps; the single DELETE; the bound values; the gate pins; the Python 3.11 grammar; the
plan binds what runs."""
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
SQL_FILE = EXEC_DIR / "sd8_delete_life_event_miss_phala_pramana.sql"


@pytest.fixture(scope="module")
def mod():
    return cf.load_exec("sd8_static")


# ------------------------------------------------------------------------------- this package is NEVER run by migrate.ts
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


def test_no_file_of_this_package_is_in_a_folder_migrate_ts_reads():
    for d in migrate_dirs():
        assert not [f.name for f in d.iterdir() if "sd8" in f.name or "scoped_delete" in f.name or "phala_pramana" in f.name and "delete" in f.name], d
    for f in (SQL_FILE, EXEC_DIR / "scoped_delete_8_exec.py"):
        assert f.is_file() and not re.match(r"^\d+", f.name)                    # no migration number
        assert f.parent.resolve() not in migrate_dirs() and not any(d in f.resolve().parents for d in migrate_dirs())
    found = sorted(p.name for d in migrate_dirs() for p in d.iterdir() if p.name.endswith(".sql"))
    assert SQL_FILE.name not in found


def test_the_header_says_it_is_never_run_by_migrate_ts_and_irreversible():
    head = SQL_FILE.read_text().split("-- @@STEP")[0]
    assert "NEVER RUN BY platform/scripts/migrate.ts" in head and "IRREVERSIBLE" in head and "PR #3047" in head


# ------------------------------------------------------------------------------- the steps
def test_steps_parse_and_the_header_is_not_executed(mod):
    s = mod.forward_leg().steps
    assert [n for n, _ in s] == ["s1_assume_roles", "s2_preconditions_as_reader", "s3_delete_as_builder", "s4_delete_shadow_as_table_owner",
                                 "s5_delete_phaladesa_snapshot_as_table_owner", "s6_post_assertions_as_reader", "s7_restore_memberships"]
    assert not any("IRREVERSIBLE" in sql for _, sql in s)
    assert mod.STEP_FIRST == s[0][0] and mod.STEP_DELETE == s[2][0] and mod.STEP_DELETE_SHADOW == s[3][0] and mod.STEP_DELETE_PHD == s[4][0] and mod.STEP_LAST == s[-1][0] and mod.COUNT_STEPS == (s[0][0], s[1][0])


def test_a_step_may_not_control_the_transaction(mod):
    with pytest.raises(ValueError):
        mod.parse_steps("-- @@STEP a\nSELECT 1;\nCOMMIT;\n")
    with pytest.raises(ValueError):
        mod.parse_steps("-- @@STEP a\nSELECT 1;\n-- @@STEP a\nSELECT 2;\n")
    with pytest.raises(ValueError):
        mod.parse_steps("no steps at all")


def code_lines(sql: str) -> str:
    return "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))


def test_the_sql_has_exactly_three_deletes_one_per_target_and_writes_nothing_else():
    code = code_lines(SQL_FILE.read_text())
    deletes = re.findall(r"(?is)\bDELETE\s+FROM\b[^;]*?RETURNING", code)
    assert len(deletes) == 3
    assert "DELETE FROM ONLY public.phala_pramana\n" in deletes[0]
    assert "chart_id = v_chart AND pramana_id = ANY (v_ids) AND evidence_type = 'life_event_miss'" in deletes[0]
    assert "DELETE FROM ONLY public.phala_pramana__ssv_20260728b\n" in deletes[1]
    assert "chart_id = v_chart AND pramana_id = ANY (v_sids) AND evidence_type = 'life_event_miss'" in deletes[1]
    assert "DELETE FROM ONLY public.phala_phaladesa__ssv_20260728b\n" in deletes[2]
    assert "chart_id = v_chart AND phaladesa_id = ANY (v_pids) AND evidence_type = 'life_event_miss'" in deletes[2]
    assert len(re.findall(r"(?i)\bDELETE\s+FROM\b", code)) == 3 and code.count("FROM ONLY") == 3
    bare = re.sub(r"'[^']*'", "''", code)                                    # string literals (privilege names, messages) are not statements
    assert not re.search(r"(?i)\b(INSERT\s+INTO|UPDATE\s+\w|TRUNCATE|DROP|ALTER|CREATE|COPY|VACUUM|ANALYZE)\b", bare)
    # the only GRANT / REVOKE are the transient role memberships, by format(); no privilege on any object is granted
    assert re.findall(r"(?i)\b(?:GRANT|REVOKE)\b[^;']*", code) == ["GRANT %I TO %I", "REVOKE %I FROM %I"]
    # each delete runs as the least-privileged role that can actually perform it, every read as the SELECT-only role
    roles = re.findall(r"SET LOCAL ROLE (\w+);", code)
    assert roles == ["suvarna_reader", "data_plane_builder", "amjis_app", "amjis_app", "suvarna_reader"]
    # the LIVE phala_phaladesa is only ever READ (SELECT ... FROM); no statement writes it
    assert not re.search(r"(?i)(DELETE\s+FROM|INSERT\s+INTO|UPDATE)\s+(ONLY\s+)?public\.phala_phaladesa\b(?!_)", bare)
    # the bound values live in ONE place in the SQL
    for g in ("ids", "chart", "fp", "shadow_ids", "shadow_fp", "phd_ids", "phd_fp"):
        assert code.count(f"set_config('madhav.sd8_{g}',") == 1, g


def test_the_bound_values_are_the_ones_ss_approved(mod):
    assert len(mod.IDS) == 8 and len(set(mod.IDS)) == 8 and list(mod.IDS) == sorted(mod.IDS)
    for i in mod.IDS:
        assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", i)
    assert mod.CHART == "1c826d5a-41cb-4450-b4dc-59d440e5f75a" and re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", mod.CHART)
    assert mod.MARKER == "life_event_miss" and mod.SERVER_MAJOR == 15 and mod.EXPECTED_DATABASE == "amjis" and mod.EXPECTED_ADMIN == "postgres"
    assert mod.BUILDER == "data_plane_builder" and mod.READER == "suvarna_reader" and re.fullmatch(r"[0-9a-f]{64}", mod.ROWS_FINGERPRINT)
    assert len(mod.SHADOW_IDS) == 16 and len(set(mod.SHADOW_IDS)) == 16 and list(mod.SHADOW_IDS) == sorted(mod.SHADOW_IDS) and not set(mod.SHADOW_IDS) & set(mod.IDS)
    for i in mod.SHADOW_IDS:
        assert re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", i)
    assert mod.PHD_IDS == ("908e3c82-bb53-4457-8642-bf0d5e71460c",) and re.fullmatch(r"[0-9a-f]{64}", mod.PHD_FINGERPRINT) and len({mod.ROWS_FINGERPRINT, mod.SHADOW_FINGERPRINT, mod.PHD_FINGERPRINT}) == 3
    assert not set(mod.PHD_IDS) & (set(mod.IDS) | set(mod.SHADOW_IDS))
    assert re.fullmatch(r"[0-9a-f]{64}", mod.SHADOW_FINGERPRINT) and mod.SHADOW_FINGERPRINT != mod.ROWS_FINGERPRINT and mod.SHADOW_TABLE == "phala_pramana__ssv_20260728b"
    assert mod.sql_bound_values(SQL_FILE.read_text()) == {"chart": mod.CHART, "ids": ",".join(mod.IDS), "fp": mod.ROWS_FINGERPRINT,
                                                           "shadow_ids": ",".join(mod.SHADOW_IDS), "shadow_fp": mod.SHADOW_FINGERPRINT,
                                                           "phd_ids": ",".join(mod.PHD_IDS), "phd_fp": mod.PHD_FINGERPRINT}
    assert [(t["key"], t["table"], t["n"], t["role"]) for t in mod.TARGETS] == [("main", "phala_pramana", 8, "data_plane_builder"), ("shadow", "phala_pramana__ssv_20260728b", 16, "amjis_app"),
                                                                                                                          ("phd", "phala_phaladesa__ssv_20260728b", 1, "amjis_app")]
    assert "362f9f17" not in SQL_FILE.read_text() + (EXEC_DIR / "scoped_delete_8_exec.py").read_text()          # the dead phantom chart id (CLAUDE.md §B)


def test_no_private_column_is_ever_selected_into_a_result(mod):
    """The executor reads counts, ids and a hash of NON-private columns. falsifier_text / observable_criteria_jsonb / derivation_ledger_jsonb / source_citation /
    lel_entry_jsonb are only ever tested for NULL-ness (lel_entry_jsonb) and never selected, copied or printed."""
    src = (EXEC_DIR / "scoped_delete_8_exec.py").read_text() + "\n" + code_lines(SQL_FILE.read_text())
    for col in ("falsifier_text", "observable_criteria_jsonb", "derivation_ledger_jsonb", "source_citation"):
        assert col not in src, col
    for stmt in re.findall(r"[^\n]*lel_entry_jsonb[^\n]*", code_lines(SQL_FILE.read_text())):
        if "RAISE EXCEPTION" in stmt:
            continue                                                                 # a message that names the column, not a read of it
        assert re.search(r"lel_entry_jsonb IS (NOT )?NULL", stmt), stmt                  # in the SQL it is only ever tested for NULL-ness
    assert not re.search(r"(?i)\bSELECT\s+\*|INTO\s+(TEMP|TABLE)|CREATE\s+TABLE\s+\w+\s+AS|COPY\b", src)


# ------------------------------------------------------------------------------- gate + plan
def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def test_the_gate_pins_equal_the_shipped_gate_v2_files(mod):
    assert mod.GATE_PINS == {n: sha(GATE_V2 / n) for n in ("prerun_gate.py", "run_gated.sh", "executor_standards.py")}


def test_the_plan_hash_binds_the_sql_the_gate_the_ids_and_the_executor(mod, monkeypatch, tmp_path):
    base = mod.plan_hash()
    assert len(base) == 64 and base == mod.plan_hash() and mod.plan_hash_unbound() != base         # BOUND (gate shas folded in) vs UNBOUND
    text = mod.render_plan()
    assert mod.forward_leg().sql_sha256 in text and mod.exec_sha() in text and mod.ROWS_FINGERPRINT in text and mod.SHADOW_FINGERPRINT in text and mod.CHART in text
    for i in mod.IDS + mod.SHADOW_IDS:
        assert i in text
    for pin in mod.GATE_PINS.values():
        assert pin in text
    assert "irreversible" in text.lower() and "PR #3047" in text and "phala_pramana__ssv_20260728b" in text and "role_orchestrator" in text and "AMENDED ON PURPOSE" in text and "138 -> 122" in text and "7 -> 6" in text
    assert "migration 1288" in text and "BEFORE any ph_pramana build for another chart" in text and "rolsuper" in text and "phala_phaladesa__ssv_20260728b" in text and mod.PHD_IDS[0] in text
    p = tmp_path / "f.sql"
    p.write_text(mod.SQL_FORWARD.read_text().replace("FROM ONLY", "FROM", 1))
    monkeypatch.setattr(mod, "SQL_FORWARD", p)
    assert mod.plan_hash() != base                                         # any SQL edit changes the plan hash
    monkeypatch.undo()
    assert mod.plan_hash(pins={**mod.GATE_PINS, "run_gated.sh": "0" * 64}) != base      # and so does a gate pin
    assert mod.plan_hash(sha="0" * 64) != base                              # and the executor sha


def test_every_check_a_green_run_can_emit_is_named_in_the_plan(mod):
    text = mod.render_plan()
    for c in mod.CHECKS:
        assert c in text


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
        mod.gate_dir({"SD8_TEST_GATE_DIR": "/tmp/x"})
    assert e.value.code == 95
    with pytest.raises(SystemExit) as e:
        mod.resolve_evidence_root(None, {"SD8_TEST_EVIDENCE_ROOT": "/tmp/x"})
    assert e.value.code == 95
    assert mod.resolve_evidence_root(None, {}) == "/Users/Dev/suvarna-evidence/ScopedDelete8"


def test_there_is_no_rollback_mode_and_only_the_three_modes(mod):
    assert mod.MODES == ("count", "dry-run", "apply")
    with pytest.raises(SystemExit):
        mod.parse_args(["--rollback", "--expect-plan", "0" * 64])


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
