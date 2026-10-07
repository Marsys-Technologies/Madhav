"""Keep Kāla database tests in the CI-discovered, skip-failing DB directory."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest


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
                names[alias.asname or alias.name.split(".")[0]] = alias.name
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
    for path in (TESTS / "l3" / "kala").rglob("*.py"):
        yield path
    for path in (TESTS / "l3").rglob("test_kala_*.py"):
        if "kala_db" not in path.parts and "kala" not in path.parts:
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


@pytest.mark.parametrize("source", [
    "import psycopg as pg\npg.connect('dsn')",
    "from psycopg import connect as open_db\nopen_db('dsn')",
    "from sqlalchemy import create_engine\ncreate_engine('dsn')",
])
def test_planted_database_connection_is_rejected(source):
    assert _db_calls(source), "a direct database connection escaped the guard"


def test_ci_collects_canary_and_entire_db_directory():
    workflow = CI.read_text(encoding="utf-8")
    assert "pytest tests/ bodha_writers/__tests__" in workflow
    assert (TESTS / "l3" / "kala" / "test_ci_canary.py").is_file()
    assert "kala-db-tests:" in workflow
    assert "KALA_REQUIRE_DB: '1'" in workflow
    assert "python -m pytest tests/l3/kala_db -q -rs" in workflow
