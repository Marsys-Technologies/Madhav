"""Tests for check_public_schema_migration_privilege.py — the guard for the 2026-10-08 Kāla deploy outage
(a routine migration that CREATEs in schema public, which the routine migrator cannot do)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import check_public_schema_migration_privilege as guard

REPO = Path(__file__).resolve().parents[4]


def _repo(tmp_path: Path, files: dict[str, str], kala_list: str = "") -> Path:
    """A minimal repo tree: migrate.ts with the three protected sets, a Kāla list file and migration files."""
    (tmp_path / "platform/scripts").mkdir(parents=True)
    (tmp_path / "platform/migrations").mkdir(parents=True)
    (tmp_path / "platform/supabase/migrations").mkdir(parents=True)
    (tmp_path / guard.MIGRATE_TS).write_text(
        "export const PROTECTED_DATA_PLANE_MIGRATIONS = new Set([\n  '1035_dp.sql',\n])\n"
        "export const PROTECTED_PUBLIC_SCHEMA_MIGRATIONS = new Set([\n  '1153_gochara.sql',\n])\n"
        "const AI_METERING_PROTECTED_PUBLIC_SCHEMA_MIGRATION = '1202_ai_metering_ledger.sql'\n"
    )
    (tmp_path / guard.KALA_LIST).write_text(kala_list)
    for rel, sql in files.items():
        (tmp_path / rel).write_text(sql)
    return tmp_path


def _scan(root: Path, changed: set[str] | None = None) -> list[str]:
    return guard.scan(root, guard.load_protected(root), changed or set())


def test_planted_create_table_in_new_routine_file_fails(tmp_path):
    root = _repo(tmp_path, {"platform/migrations/9001_kala_new.sql": "CREATE TABLE IF NOT EXISTS public.kala_t (id int);\n"})
    findings = _scan(root)
    assert findings == ["platform/migrations/9001_kala_new.sql: line 1: CREATE TABLE in schema public"]


def test_same_file_on_the_kala_list_passes(tmp_path):
    root = _repo(
        tmp_path,
        {"platform/migrations/9001_kala_new.sql": "CREATE TABLE IF NOT EXISTS public.kala_t (id int);\n"},
        kala_list="# window\n9001_kala_new.sql  # same PR\n",
    )
    assert _scan(root) == []


def test_create_table_inside_comments_passes(tmp_path):
    root = _repo(tmp_path, {
        "platform/migrations/9002_comment.sql": "-- CREATE TABLE public.x (id int);\n/* CREATE TABLE y (id int); /* nested */ */\nSELECT 1;\n",
    })
    assert _scan(root) == []


def test_unqualified_names_count_as_public_and_every_kind_is_caught(tmp_path):
    sql = (
        "CREATE TABLE t (id int);\n"
        "CREATE UNIQUE INDEX i ON t (id);\n"
        "CREATE OR REPLACE FUNCTION f() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;\n"
        "CREATE TYPE e AS ENUM ('a');\n"
        "CREATE TRIGGER tr AFTER INSERT ON t FOR EACH ROW EXECUTE FUNCTION f();\n"
        "CREATE VIEW v AS SELECT 1;\n"
        "CREATE MATERIALIZED VIEW mv AS SELECT 1;\n"
        "CREATE SEQUENCE s;\n"
        "GRANT USAGE ON SCHEMA public TO verifier_principal;\n"
    )
    kinds = [v.split(": ", 1)[1] for v in guard.find_violations(sql)]
    assert kinds == [
        "CREATE TABLE in schema public", "CREATE INDEX in schema public", "CREATE FUNCTION in schema public",
        "CREATE TYPE in schema public", "CREATE TRIGGER in schema public", "CREATE VIEW in schema public",
        "CREATE MATERIALIZED VIEW in schema public", "CREATE SEQUENCE in schema public", "GRANT ... ON SCHEMA",
    ]


def test_other_schemas_temp_tables_and_alters_pass():
    sql = (
        "CREATE TEMP TABLE scratch (id int);\n"
        "CREATE TABLE IF NOT EXISTS nirmana.t (id int);\n"
        "CREATE INDEX i ON nirmana.t (id);\n"
        'CREATE FUNCTION "audit".f() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;\n'
        "ALTER TABLE bg_parihara_rules ADD COLUMN scope text;\n"
        "GRANT SELECT ON TABLE public.t TO role_x;\n"
    )
    assert guard.find_violations(sql) == []


def test_dynamic_ddl_inside_a_do_block_is_still_caught():
    """Literals are scanned on purpose: EXECUTE 'CREATE TABLE ...' is real DDL (documented known limit: a literal that
    merely mentions CREATE TABLE is a false positive, never a false negative)."""
    sql = "DO $$ BEGIN EXECUTE 'CREATE TABLE dyn (id int)'; END $$;\n"
    assert guard.find_violations(sql) == ["line 1: CREATE TABLE in schema public"]


def test_files_at_or_below_the_pinned_baseline_are_not_scanned_unless_changed(tmp_path):
    old = f"platform/supabase/migrations/{guard.BASELINE_MAX_APPLIED:04d}_historic.sql"
    root = _repo(tmp_path, {old: "CREATE TABLE historic (id int);\n"})
    assert _scan(root) == []
    assert _scan(root, changed={old}) == [f"{old}: line 1: CREATE TABLE in schema public"]


def test_protected_sets_from_migrate_ts_pass(tmp_path):
    root = _repo(tmp_path, {
        "platform/migrations/9153_x.sql": "CREATE TABLE a (id int);\n",
        "platform/migrations/1153_gochara.sql": "CREATE TABLE b (id int);\n",
        "platform/migrations/1202_ai_metering_ledger.sql": "CREATE TABLE c (id int);\n",
    })
    changed = {"platform/migrations/1153_gochara.sql", "platform/migrations/1202_ai_metering_ledger.sql"}
    assert _scan(root, changed) == ["platform/migrations/9153_x.sql: line 1: CREATE TABLE in schema public"]


def test_unparseable_migrate_ts_fails_closed(tmp_path):
    root = _repo(tmp_path, {})
    (root / guard.MIGRATE_TS).write_text("// sets renamed\n")
    with pytest.raises(ValueError):
        guard.load_protected(root)
    assert guard.main(["--repo-root", str(root)]) == 5


def test_the_real_repo_loads_every_protected_list_and_is_clean():
    protected = guard.load_protected(REPO)
    assert "1330_kala_layer_manifest_candidates.sql" in protected
    assert "1153_gochara_sky_event_substrate.sql" in protected
    assert "1202_ai_metering_ledger.sql" in protected
    assert "1035_data_plane_l1_producer_history.sql" in protected
    assert guard.scan(REPO, protected, set()) == []


def test_the_original_1330_would_have_failed_the_guard():
    """The file as merged on 2026-10-08 (before the GRANT USAGE line was removed), as a routine file."""
    sql = (REPO / "platform/migrations/1330_kala_layer_manifest_candidates.sql").read_text() + \
        "GRANT USAGE ON SCHEMA public TO verifier_principal;\n"
    found = guard.find_violations(sql)
    assert sum("CREATE TABLE" in f for f in found) == 4
    assert any("ON SCHEMA" in f for f in found)


def test_self_test_passes():
    r = subprocess.run([sys.executable, str(REPO / "platform/scripts/governance/check_public_schema_migration_privilege.py"), "--self-test"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
