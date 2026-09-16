"""Standalone heavy-writer lifecycle must fence destructive ga_dashas replacement."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "run_heavy_writer_standalone.py"
SPEC = importlib.util.spec_from_file_location("run_heavy_writer_standalone", SCRIPT)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class Cursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        self.executed.append((sql, params))


class Connection:
    def __init__(self) -> None:
        self.commits = 0

    def commit(self) -> None:
        self.commits += 1


def test_lifecycle_is_committed_before_ga_dashas_preclean_delete() -> None:
    source = SCRIPT.read_text()
    main_source = source[source.index("def main() -> None:"):]

    assert main_source.index("_create_standalone_run_lifecycle(conn, cur, run_id, asset_id)") < main_source.index('DELETE FROM chart_dashas')
    assert "A synthetic run_id (uuid4) is sufficient" not in source
    assert main_source.index("_has_eligible_ga_dashas_receipt(cur, run_id)") < main_source.index("_complete_standalone_run_lifecycle(conn, cur, run_id, asset_id)")
    assert main_source.index("_complete_standalone_run_lifecycle(conn, cur, run_id, asset_id)") < main_source.index('logger.info("SUCCESS')
    assert main_source.count("_fail_standalone_run_lifecycle(") == 3


def test_lifecycle_creation_and_terminal_transitions_are_durable() -> None:
    conn = Connection()
    cur = Cursor()

    runner._create_standalone_run_lifecycle(conn, cur, "run-1", "ga_dashas")
    assert conn.commits == 1
    assert len(cur.executed) == 2
    runner._complete_standalone_run_lifecycle(conn, cur, "run-1", "ga_dashas")
    runner._fail_standalone_run_lifecycle(conn, cur, "run-1", "ga_dashas", "writer failed")

    sql = " ".join("\n".join(statement for statement, _ in cur.executed).split())
    assert "INSERT INTO build_runs" in sql
    assert "'running'" in sql
    assert "INSERT INTO build_run_assets" in sql
    assert "'building'" in sql
    assert "UPDATE build_run_assets SET state = 'complete'" in sql
    assert "UPDATE build_runs SET state = 'completed'" in sql
    assert "UPDATE build_run_assets SET state = 'error'" in sql
    assert "UPDATE build_runs SET state = 'failed'" in sql
    assert conn.commits == 3


def test_data_writer_already_terminalizes_the_durable_asset_row() -> None:
    asset_runner = SCRIPT.parent / "pipeline/orchestrator/asset_runner.py"
    source = " ".join(asset_runner.read_text().split())

    assert "UPDATE build_run_assets SET state = 'complete', disposition = 'build', ended_at = NOW()" in source
    assert "UPDATE build_run_assets SET state = 'error', ended_at = NOW(), error = %s" in source


class MainCursor(Cursor):
    def fetchone(self):
        sql = self.executed[-1][0]
        if "COUNT(*) AS n FROM chart_dashas" in sql:
            return {"n": 2}
        if "FROM asset_registry" in sql:
            return {
                "depends_on": ["ga_chart_service"],
                "natural_key_partition": "chart_id,system_id,ayanamsha_id",
                "has_cowriters": False,
            }
        if "asset_provenance_receipts" in sql:
            return {"receipt_exists": self.receipt_exists}
        raise AssertionError(f"unexpected fetchone query: {sql}")

    def __init__(self, receipt_exists: bool = True) -> None:
        super().__init__()
        self.receipt_exists = receipt_exists


class MainConnection(Connection):
    def __init__(self, cursor: MainCursor) -> None:
        super().__init__()
        self._cursor = cursor
        self.autocommit = True
        self.closed = False
        self.rollbacks = 0

    def cursor(self) -> MainCursor:
        return self._cursor

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closed = True


def _install_main_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    conn: MainConnection,
    calls: list[object],
    *,
    writer_result: bool = True,
    writer_error: Exception | None = None,
) -> None:
    db = ModuleType("pipeline.orchestrator.db")
    db.connect = lambda: conn  # type: ignore[attr-defined]
    writers = ModuleType("pipeline.orchestrator.writers")
    writers.discover_all = lambda: calls.append("discover")  # type: ignore[attr-defined]
    asset_runner = ModuleType("pipeline.orchestrator.asset_runner")

    def write(*args: object, **kwargs: object) -> bool:
        calls.append(("write", args, kwargs))
        if writer_error:
            raise writer_error
        return writer_result

    asset_runner._run_data_writer = write  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "pipeline.orchestrator.db", db)
    monkeypatch.setitem(sys.modules, "pipeline.orchestrator.writers", writers)
    monkeypatch.setitem(sys.modules, "pipeline.orchestrator.asset_runner", asset_runner)


def test_main_commits_fence_before_delete_and_captures_a_proven_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    cur = MainCursor(receipt_exists=True)
    conn = MainConnection(cur)
    calls: list[object] = []
    _install_main_dependencies(monkeypatch, conn, calls)
    completed: list[object] = []
    monkeypatch.setattr(runner, "_complete_standalone_run_lifecycle", lambda *args: completed.append(args))
    monkeypatch.setattr(runner, "_fail_standalone_run_lifecycle", lambda *args: pytest.fail("successful run must not fail"))
    monkeypatch.setattr(sys, "argv", ["runner", "ga_dashas"])
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    runner.main()

    delete_index = next(i for i, (sql, _) in enumerate(cur.executed) if "DELETE FROM chart_dashas" in sql)
    lifecycle_insert_index = next(i for i, (sql, _) in enumerate(cur.executed) if "INSERT INTO build_runs" in sql)
    assert lifecycle_insert_index < delete_index
    assert conn.commits >= 2  # lifecycle commit, then destructive pre-clean commit
    write_call = next(call for call in calls if isinstance(call, tuple) and call[0] == "write")
    assert write_call[2] == {
        "declared_deps": ["ga_chart_service"],
        "natural_key_partition": "chart_id,system_id,ayanamsha_id",
        "has_cowriters": False,
        "force": True,
    }
    receipt_check_index = next(i for i, (sql, _) in enumerate(cur.executed) if "asset_provenance_receipts" in sql)
    assert receipt_check_index > delete_index
    assert completed


def test_main_fails_the_lifecycle_when_writer_cannot_prove_its_new_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    cur = MainCursor(receipt_exists=False)
    conn = MainConnection(cur)
    calls: list[object] = []
    _install_main_dependencies(monkeypatch, conn, calls)
    completed: list[object] = []
    failed: list[object] = []
    monkeypatch.setattr(runner, "_complete_standalone_run_lifecycle", lambda *args: completed.append(args))
    monkeypatch.setattr(runner, "_fail_standalone_run_lifecycle", lambda *args: failed.append(args))
    monkeypatch.setattr(sys, "argv", ["runner", "ga_dashas"])
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    with pytest.raises(SystemExit) as exit_info:
        runner.main()

    assert exit_info.value.code == 1
    assert not completed
    assert failed


def test_main_marks_the_committed_fence_non_successful_when_the_writer_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    cur = MainCursor(receipt_exists=True)
    conn = MainConnection(cur)
    calls: list[object] = []
    _install_main_dependencies(monkeypatch, conn, calls, writer_error=RuntimeError("writer exploded"))
    failed: list[object] = []
    monkeypatch.setattr(runner, "_complete_standalone_run_lifecycle", lambda *args: pytest.fail("exception must not complete"))
    monkeypatch.setattr(runner, "_fail_standalone_run_lifecycle", lambda *args: failed.append(args))
    monkeypatch.setattr(sys, "argv", ["runner", "ga_dashas"])
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")

    with pytest.raises(SystemExit) as exit_info:
        runner.main()

    assert exit_info.value.code == 1
    assert failed
    assert "RuntimeError: writer exploded" in failed[0][-1]
