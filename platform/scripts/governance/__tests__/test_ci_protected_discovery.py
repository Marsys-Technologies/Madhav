"""Automatic protected-window membership uses the existing privilege detector."""
import importlib.util
from pathlib import Path
import sys
import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import check_public_schema_migration_privilege as guard


def test_a_new_public_ddl_file_is_protected_without_editing_the_legacy_list(tmp_path):
    from kala_protected_migrations import derive
    scripts = tmp_path / 'platform/scripts'
    scripts.mkdir(parents=True)
    (scripts / 'kala_protected_migrations.txt').write_text('1330_legacy.sql\n')
    migrations = tmp_path / 'platform/migrations'
    migrations.mkdir()
    (migrations / '9001_new.sql').write_text('CREATE TABLE public.new_table (id int);\n')
    (migrations / '9002_routine.sql').write_text('UPDATE things SET value=1;\n')
    assert derive(tmp_path) == ['1330_legacy.sql', '9001_new.sql']
    assert guard.scan(tmp_path, set(derive(tmp_path)), set()) == []
    # A genuine bypass still fails: excluding DDL does not silence the privilege guard.
    (scripts / 'kala_protected_migrations_exclusions.json').write_text('{"9001_new.sql":"test deliberate mismatch"}')
    assert guard.scan(tmp_path, set(derive(tmp_path)), set())


def test_missing_or_malformed_seed_and_exclusions_fail_closed(tmp_path):
    from kala_protected_migrations import derive
    with pytest.raises((OSError, ValueError)):
        derive(tmp_path)
    scripts = tmp_path / 'platform/scripts'
    scripts.mkdir(parents=True)
    (scripts / 'kala_protected_migrations.txt').write_text('not-a-migration\n')
    with pytest.raises(ValueError):
        derive(tmp_path)


def test_empty_legacy_seed_cannot_be_hidden_by_new_automatic_members(tmp_path):
    from kala_protected_migrations import derive
    scripts = tmp_path / 'platform/scripts'
    scripts.mkdir(parents=True)
    (scripts / 'kala_protected_migrations.txt').write_text('# no membership\n')
    migrations = tmp_path / 'platform/migrations'
    migrations.mkdir()
    (migrations / '9001_new.sql').write_text('CREATE TABLE public.new_table (id int);\n')
    assert derive(tmp_path) == []
    assert guard.scan(tmp_path, set(derive(tmp_path)), set()) == [
        'platform/migrations/9001_new.sql: line 1: CREATE TABLE in schema public'
    ]


def test_deployment_selector_cli_still_refuses_an_empty_window(tmp_path):
    import subprocess
    scripts = tmp_path / 'platform/scripts'
    scripts.mkdir(parents=True)
    (scripts / 'kala_protected_migrations.txt').write_text('# intentionally empty fixture\n')
    proc = subprocess.run([sys.executable, str(HERE / 'kala_protected_migrations.py'),
                           '--repo-root', str(tmp_path)], text=True, capture_output=True, timeout=30)
    assert proc.returncode == 5
    assert 'empty' in proc.stderr
