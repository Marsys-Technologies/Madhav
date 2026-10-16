"""Keep Kāla database tests in the CI-discovered, skip-failing DB directory."""
from __future__ import annotations

import ast
from pathlib import Path
import shlex

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[5]
TESTS = Path(__file__).resolve().parents[2]
CI = ROOT / ".github/workflows/ci.yml"
DB_CALLS = {
    "psycopg.connect",
    "psycopg.Connection.connect",
    "psycopg2.connect",
    "asyncpg.connect",
    "asyncpg.create_pool",
    "sqlalchemy.create_engine",
    "sqlalchemy.create_async_engine",
    "sqlalchemy.ext.asyncio.create_async_engine",
}


def _db_calls(source: str) -> set[str]:
    """Resolve direct imports and module aliases before checking connection calls."""
    tree = ast.parse(source)
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    names[alias.asname] = alias.name
                else:
                    # `import sqlalchemy.ext.asyncio` binds `sqlalchemy`, not
                    # the full dotted name. Preserve the root for attribute
                    # traversal so the module path is not repeated.
                    root = alias.name.split(".")[0]
                    names[root] = root
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                names[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    def qualified(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return names.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            base = qualified(node.value)
            return f"{base}.{node.attr}" if base else None
        return None

    return {
        name for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        if (name := qualified(node.func)) in DB_CALLS
    }


def _campaign_db_free_tests():
    # Fixtures and helpers can open the connection before a test body runs.
    for path in TESTS.rglob("*.py"):
        parts = path.relative_to(TESTS).parts
        if "kala_db" in parts:
            continue
        if (any(part in {"kala", "kala_core"} or part.startswith("ka_") for part in parts[:-1])
                or path.name.startswith(("test_kala_", "test_ka_"))):
            yield path


def test_kala_database_connections_stay_in_kala_db():
    offenders = {
        str(path.relative_to(ROOT)): sorted(calls)
        for path in _campaign_db_free_tests()
        if (calls := _db_calls(path.read_text(encoding="utf-8")))
    }
    assert not offenders, f"Kāla tests opening a database outside tests/l3/kala_db: {offenders}"


def test_guard_discovers_database_free_fixtures(monkeypatch, tmp_path):
    kala = tmp_path / "l3" / "kala"
    kala.mkdir(parents=True)
    fixture = kala / "conftest.py"
    fixture.write_text("import psycopg\npsycopg.connect('dsn')\n", encoding="utf-8")
    monkeypatch.setitem(globals(), "TESTS", tmp_path)
    assert fixture in set(_campaign_db_free_tests())
    assert _db_calls(fixture.read_text(encoding="utf-8")) == {"psycopg.connect"}


def test_guard_rejects_connections_in_kala_core_subdirectories(monkeypatch, tmp_path):
    tests = tmp_path / "tests"
    vocab = tests / "l3" / "kala_core" / "vocab"
    vocab.mkdir(parents=True)
    (vocab / "conftest.py").write_text("# connection-free fixture\n", encoding="utf-8")
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    monkeypatch.setitem(globals(), "TESTS", tests)
    test_kala_database_connections_stay_in_kala_db()

    (vocab / "test_vocab_db.py").write_text(
        "import psycopg\npsycopg.connect('dsn')\n", encoding="utf-8"
    )

    with pytest.raises(AssertionError, match="test_vocab_db.py"):
        test_kala_database_connections_stay_in_kala_db()


@pytest.mark.parametrize("relative", [
    "l3/ka_kshetra/test_hazard.py", "l3/ka_avadhi/conftest.py",
    "test_ka_kshetra_stage3_clocks.py", "l3/other/test_kala_reader.py",
])
def test_guard_rejects_connections_across_campaign_test_areas(monkeypatch, tmp_path, relative):
    tests = tmp_path / "tests"
    planted = tests / relative
    planted.parent.mkdir(parents=True)
    planted.write_text("import psycopg2\npsycopg2.connect('dsn')\n", encoding="utf-8")
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    monkeypatch.setitem(globals(), "TESTS", tests)
    with pytest.raises(AssertionError, match=planted.name):
        test_kala_database_connections_stay_in_kala_db()


@pytest.mark.parametrize("source", [
    "import psycopg as pg\npg.connect('dsn')",
    "from psycopg import connect as open_db\nopen_db('dsn')",
    "from sqlalchemy import create_engine\ncreate_engine('dsn')",
    "import sqlalchemy.ext.asyncio\nsqlalchemy.ext.asyncio.create_async_engine('dsn')",
    "import sqlalchemy.ext.asyncio as sa_async\nsa_async.create_async_engine('dsn')",
])
def test_planted_database_connection_is_rejected(source):
    assert _db_calls(source), "a direct database connection escaped the guard"


def test_ci_collects_canary_and_entire_db_directory():
    workflow = CI.read_text(encoding="utf-8")
    assert "pytest tests/ bodha_writers/__tests__" in workflow
    assert (TESTS / "l3" / "kala" / "test_ci_canary.py").is_file()
    assert "kala-db-tests:" in workflow
    assert "KALA_REQUIRE_DB: '1'" in workflow
    # Additional explicit test targets must not invalidate directory discovery.
    steps = yaml.safe_load(workflow)["jobs"]["kala-db-tests"]["steps"]
    commands = [shlex.split(step["run"]) for step in steps if "run" in step]
    # -B is an interpreter flag and does not change pytest directory discovery.
    assert any(
        [token for token in command[:4] if token != "-B"][:3] == ["python", "-m", "pytest"]
        and {"tests/l3/kala_db", "-q", "-rs"} <= set(command)
        for command in commands
    )


@pytest.mark.parametrize("fixture_name", ["kala_db_dsn", "isolated_kala_db_dsn"])
def test_required_database_fixture_refuses_missing_access(monkeypatch, fixture_name):
    from tests.l3.kala_db import conftest as db
    monkeypatch.setenv("KALA_REQUIRE_DB", "1")
    monkeypatch.delenv("KALA_ADMIN_DSN", raising=False)
    with pytest.raises(pytest.fail.Exception, match="KALA_ADMIN_DSN is absent"):
        next(getattr(db, fixture_name).__wrapped__())


@pytest.mark.parametrize("fixture_name", ["kala_db_dsn", "isolated_kala_db_dsn"])
def test_required_database_fixture_refuses_unreachable_access(monkeypatch, fixture_name):
    from tests.l3.kala_db import conftest as db
    monkeypatch.setenv("KALA_REQUIRE_DB", "1")
    monkeypatch.setenv("KALA_ADMIN_DSN", "host=localhost port=5432 dbname=postgres user=postgres")

    def unavailable(*args, **kwargs):
        raise db.psycopg.OperationalError("test disposable server unavailable")

    monkeypatch.setattr(db.psycopg, "connect", unavailable)
    with pytest.raises(pytest.fail.Exception, match="disposable Postgres is unreachable"):
        next(getattr(db, fixture_name).__wrapped__())


def test_required_database_job_rejects_skips(monkeypatch):
    from types import SimpleNamespace
    from tests.l3.kala_db.conftest import pytest_sessionfinish
    monkeypatch.setenv("KALA_REQUIRE_DB", "1")
    reporter = SimpleNamespace(stats={"skipped": [object()]})
    session = SimpleNamespace(exitstatus=0, config=SimpleNamespace(
        pluginmanager=SimpleNamespace(get_plugin=lambda name: reporter)))
    pytest_sessionfinish(session, 0)
    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
