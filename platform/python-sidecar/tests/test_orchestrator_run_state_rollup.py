"""Orchestrator run-level state rollup (BA-P3 FIX 3).

Regression for the "green over-report" (NF-1): a run whose plan included any
failed/blocked asset must terminate with state='failed', never 'completed' —
an operator reading 'completed' must be able to trust the build actually
succeeded. Reuses the FakeConn/FakeCursor harness from test_orchestrator_gate.py.
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import runner  # noqa: E402
from tests.test_orchestrator_gate import REGISTRY, PLAN, FakeConn, FakeCursor  # noqa: E402


def _install(monkeypatch, state, fail_assets, mark_calls):
    monkeypatch.setattr(runner, "connect", lambda: FakeConn(state))
    monkeypatch.setattr(runner, "acquire_chart_lock", lambda *a, **k: True)
    monkeypatch.setattr(runner, "release_chart_lock", lambda *a, **k: None)
    monkeypatch.setattr(runner, "check_signals", lambda *a, **k: None)
    monkeypatch.setattr(runner, "is_asset_complete", lambda *a, **k: False)

    def fake_mark_run_state(conn, cur, run_id, new_state, **kwargs):
        mark_calls.append(new_state)

    monkeypatch.setattr(runner, "mark_run_state", fake_mark_run_state)
    monkeypatch.setattr(runner, "emit_event", lambda *a, **k: None)
    import pipeline.orchestrator.writers as writers_mod
    monkeypatch.setattr(writers_mod, "discover_all", lambda: None, raising=False)
    monkeypatch.setattr(runner, "_check_writer_registry_gaps", lambda cur: [], raising=False)

    def fake_run_asset(conn, cur, run_id, chart_id, asset_id, position):
        cur.execute(
            "UPDATE build_run_assets SET state=%s WHERE run_id=%s AND asset_id=%s",
            ("error" if asset_id in fail_assets else "complete", run_id, asset_id),
        )
        state[asset_id] = "error" if asset_id in fail_assets else "complete"

    import pipeline.orchestrator.asset_runner as ar
    monkeypatch.setattr(ar, "run_asset", fake_run_asset)


def test_run_with_failed_asset_is_marked_failed_not_completed(monkeypatch):
    state: dict[str, str] = {}
    mark_calls: list[str] = []
    _install(monkeypatch, state, fail_assets={"A"}, mark_calls=mark_calls)

    runner.execute_run("run-1")

    assert "running" in mark_calls
    assert "completed" not in mark_calls
    assert mark_calls[-1] == "failed", (
        f"run had failed/blocked assets — must terminate 'failed', got {mark_calls!r}"
    )


def test_clean_run_is_still_marked_completed(monkeypatch):
    state: dict[str, str] = {}
    mark_calls: list[str] = []
    _install(monkeypatch, state, fail_assets=set(), mark_calls=mark_calls)

    runner.execute_run("run-1")

    assert mark_calls[-1] == "completed", (
        f"a run with zero failed assets must still report 'completed', got {mark_calls!r}"
    )
