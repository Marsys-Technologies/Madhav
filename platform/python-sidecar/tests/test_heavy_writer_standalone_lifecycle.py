"""Standalone heavy-writer lifecycle must fence destructive ga_dashas replacement."""
from __future__ import annotations

import importlib.util
from pathlib import Path


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
    assert main_source.index("_complete_standalone_run_lifecycle(conn, cur, run_id, asset_id)") < main_source.index('logger.info("SUCCESS')
    assert main_source.count("_fail_standalone_run_lifecycle(") == 2


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
