"""The protected-function DB fixture must refuse missing/unsafe CI targets before connecting."""
import importlib.util
from pathlib import Path

import pytest


@pytest.mark.parametrize("dsn", [None, "postgresql://u:p@remote.invalid:5432/postgres",
                                  "postgresql://u:p@localhost:5432/postgres?hostaddr=203.0.113.1"])
def test_required_database_refuses_missing_or_unsafe_target_before_connect(monkeypatch, dsn):
    import psycopg
    from tests.l3.gochara._disposable_db_guard import UnsafeAdminDSN

    monkeypatch.setenv("GOCHARA_REQUIRE_DB", "1")
    if dsn is None:
        monkeypatch.delenv("GOCHARA_A51_TEST_DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("GOCHARA_A51_TEST_DATABASE_URL", dsn)
    def forbidden(*args, **kwargs):
        raise AssertionError("unsafe or missing target reached psycopg.connect")
    monkeypatch.setattr(psycopg, "connect", forbidden)
    spec = importlib.util.spec_from_file_location("migration_1235_boundary_subject", Path(__file__).with_name("test_migration_1235_evidence_function.py"))
    subject = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subject)
    with pytest.raises((pytest.fail.Exception, UnsafeAdminDSN), match="requires|loopback"):
        next(subject.dsn.__wrapped__())


def test_required_ci_invocation_errors_all_five_cases_when_url_is_missing(tmp_path):
    import os
    import subprocess
    import sys

    env = os.environ.copy()
    env.pop("GOCHARA_A51_TEST_DATABASE_URL", None)
    env["GOCHARA_REQUIRE_DB"] = "1"
    result = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", str(Path(__file__).with_name("test_migration_1235_evidence_function.py")),
         "-q", "-p", "no:cacheprovider", f"--basetemp={tmp_path / 'required-db'}"],
        cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "5 errors" in result.stdout and "skipped" not in result.stdout
    assert "GOCHARA_REQUIRE_DB=1 requires GOCHARA_A51_TEST_DATABASE_URL" in result.stdout
