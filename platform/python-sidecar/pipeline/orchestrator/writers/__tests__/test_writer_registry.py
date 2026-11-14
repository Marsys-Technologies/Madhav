"""
Phase 2 AC tests: writer registry + state transitions + per-asset error recovery.
Runs without a real DB — uses mock connections/cursors.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call
import pytest


@pytest.fixture(autouse=True)
def _remove_synthetic_registrations():
    from pipeline.orchestrator.writers import WRITER_REGISTRY

    yield
    for asset_id in ("fixture.asset_a", "fixture.success", "fixture.crashing"):
        WRITER_REGISTRY.pop(asset_id, None)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_conn_cur():
    """Return (mock_conn, mock_cur) wired up like psycopg."""
    cur = MagicMock()
    cur.fetchone.return_value = None
    cur.fetchall.return_value = []
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: cur
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cur


# ── Writer registry ───────────────────────────────────────────────────────────

def test_register_and_get_writer():
    from pipeline.orchestrator.writers import WRITER_REGISTRY, register, get_writer, WriterBase, WriterResult

    @register("fixture.asset_a")
    class _Writer(WriterBase):
        asset_id = "fixture.asset_a"
        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=42)

    assert get_writer("fixture.asset_a") is _Writer
    assert WRITER_REGISTRY["fixture.asset_a"] is _Writer


def test_get_writer_missing_returns_none():
    from pipeline.orchestrator.writers import get_writer
    assert get_writer("does.not.exist.xyz") is None


# ── run_asset — success path ──────────────────────────────────────────────────

def test_run_asset_success_transitions():
    """Writer returning WriterResult(rows_inserted=7) → asset_throughput goes to 'lit'."""
    from pipeline.orchestrator.writers import register, WriterBase, WriterResult
    from pipeline.orchestrator import asset_runner

    @register("fixture.success")
    class _Writer(WriterBase):
        asset_id = "fixture.success"
        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=7)

    conn, cur = _mock_conn_cur()
    cur.fetchall.return_value = []  # no downstream assets

    with patch.object(asset_runner, "emit_event") as mock_emit, \
         patch.object(asset_runner, "compute_upstream_hash", return_value="aabbccdd"), \
         patch.object(asset_runner, "get_writer_source_hash", return_value="deaddead"), \
         patch.object(asset_runner, "fetch_birth_params", return_value=None):

        asset_runner.run_asset(conn, cur, "run-1", "chart-1", "fixture.success", 0)

    # Should have set state='lit' in asset_throughput
    update_calls = [str(c) for c in cur.execute.call_args_list]
    lit_call = any("'lit'" in c or "state = 'lit'" in c or "state = %s" in c for c in update_calls)
    assert lit_call or any("lit" in c for c in update_calls), \
        f"Expected 'lit' state update; got calls: {update_calls}"

    # emit_event should have fired asset.state_change to 'lit'
    emitted_types = [c.args[0]["type"] for c in mock_emit.call_args_list]
    assert "asset.state_change" in emitted_types
    assert "asset.progress" in emitted_types


# ── run_asset — error recovery ────────────────────────────────────────────────

def test_run_asset_writer_error_marks_error_state():
    """Writer raising → asset goes to 'error'; function returns (doesn't re-raise)."""
    from pipeline.orchestrator.writers import register, WriterBase, WriterResult
    from pipeline.orchestrator import asset_runner

    @register("fixture.crashing")
    class _BadWriter(WriterBase):
        asset_id = "fixture.crashing"
        def run(self, ctx):
            raise RuntimeError("intentional crash")

    conn, cur = _mock_conn_cur()

    with patch.object(asset_runner, "emit_event") as mock_emit, \
         patch.object(asset_runner, "compute_upstream_hash", return_value="x"), \
         patch.object(asset_runner, "get_writer_source_hash", return_value="x"), \
         patch.object(asset_runner, "fetch_birth_params", return_value=None):

        # Should NOT raise — per-asset error recovery
        asset_runner.run_asset(conn, cur, "run-2", "chart-2", "fixture.crashing", 0)

    emitted = [c.args[0] for c in mock_emit.call_args_list]
    error_events = [e for e in emitted if e.get("to_state") == "error"]
    assert error_events, "Expected error state_change event"
    assert "intentional crash" in error_events[0].get("error", "")


def test_run_asset_no_writer_marks_error():
    """Missing writer registration → marks error, doesn't crash."""
    from pipeline.orchestrator import asset_runner

    conn, cur = _mock_conn_cur()

    with patch.object(asset_runner, "emit_event") as mock_emit:
        asset_runner.run_asset(conn, cur, "run-3", "chart-3", "no.writer.here", 0)

    emitted = [c.args[0] for c in mock_emit.call_args_list]
    error_events = [e for e in emitted if e.get("to_state") == "error"]
    assert error_events
    assert "no writer registered" in error_events[0].get("error", "")


# ── downstream closure ────────────────────────────────────────────────────────

def test_compute_downstream_closure_empty():
    from pipeline.orchestrator.asset_runner import compute_downstream_closure

    cur = MagicMock()
    cur.fetchall.return_value = []
    result = compute_downstream_closure(cur, "leaf.asset")
    assert result == []
    cur.execute.assert_called_once()


@pytest.fixture
def isolated_discovery_registry(monkeypatch):
    """Load the real registry with a fresh state and an inert import frontier."""
    import importlib.util
    import sys
    from pathlib import Path
    import pipeline.orchestrator.writers as owner

    name = "_writer_discovery_fixture"
    path = Path(owner.__file__)
    spec = importlib.util.spec_from_file_location(
        name, path, submodule_search_locations=[str(path.parent)]
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    module.logger = MagicMock()
    return module


def _fail_after_partial_registration(registry, monkeypatch, failure):
    class PartialWriter(registry.WriterBase):
        asset_id = "fixture.partial"

        def run(self, ctx):
            return registry.WriterResult(asset_id=self.asset_id, rows_inserted=0)

    imported = []

    def import_writer(name):
        imported.append(name.rsplit(".", 1)[-1])
        if name.endswith(".partial"):
            registry.register("fixture.partial")(PartialWriter)
            return object()
        raise failure

    monkeypatch.setattr(
        registry.pkgutil,
        "iter_modules",
        lambda path: [(None, "partial", False), (None, "broken", False), (None, "later", False)],
    )
    monkeypatch.setattr(registry.importlib, "import_module", import_writer)
    return PartialWriter, imported


@pytest.mark.parametrize("error_type", [ImportError, KeyboardInterrupt, SystemExit])
@pytest.mark.parametrize("entrypoint", ["partial", "missing", "explicit"])
def test_discovery_failure_stays_failed_for_complete_lookup(
    isolated_discovery_registry, monkeypatch, error_type, entrypoint
):
    registry = isolated_discovery_registry
    failure = error_type("synthetic writer import failure")
    partial, imported = _fail_after_partial_registration(registry, monkeypatch, failure)

    with pytest.raises(error_type) as first:
        registry.get_writer("fixture.partial")
    assert first.value is failure

    for _ in range(2):
        with pytest.raises(RuntimeError, match="writer discovery previously failed") as repeated:
            if entrypoint == "explicit":
                registry.discover_all()
            else:
                asset_id = "fixture.partial" if entrypoint == "partial" else "fixture.missing"
                registry.get_writer(asset_id)
        assert repeated.value.__cause__ is failure

    assert imported == ["partial", "broken"]
    # These compatibility surfaces remain non-triggering registration diagnostics.
    assert registry.list_writers() == {"fixture.partial": partial}
    assert registry.WRITER_REGISTRY["fixture.partial"] is partial


def test_discovery_success_preserves_recursive_import_and_skips_private_modules(
    isolated_discovery_registry, monkeypatch
):
    registry = isolated_discovery_registry
    # Fail a non-reentrant-lock mutant before attempting recursion; never leave a hung thread.
    with registry._discover_lock:
        reentrant = registry._discover_lock.acquire(blocking=False)
        if reentrant:
            registry._discover_lock.release()
        assert reentrant

    class AlphaWriter(registry.WriterBase):
        asset_id = "fixture.alpha"

        def run(self, ctx):
            return registry.WriterResult(asset_id=self.asset_id, rows_inserted=0)

    class BetaWriter(AlphaWriter):
        asset_id = "fixture.beta"

    imported = []

    def import_writer(name):
        suffix = name.rsplit(".", 1)[-1]
        imported.append(suffix)
        if suffix == "alpha":
            registry.register("fixture.alpha")(AlphaWriter)
            assert registry.get_writer("fixture.alpha") is AlphaWriter
        else:
            registry.register("fixture.beta")(BetaWriter)
        return object()

    monkeypatch.setattr(
        registry.pkgutil,
        "iter_modules",
        lambda path: [
            (None, "_private", False),
            (None, "tests", True),
            (None, "alpha", False),
            (None, "beta", True),
        ],
    )
    monkeypatch.setattr(registry.importlib, "import_module", import_writer)
    assert registry.list_writers() == {}
    registry.discover_all()
    registry.discover_all()
    assert registry.get_writer("fixture.alpha") is AlphaWriter
    assert registry.get_writer("fixture.beta") is BetaWriter
    assert registry.get_writer("fixture.missing") is None
    assert imported == ["alpha", "beta"]
    assert registry.list_writers() == {
        "fixture.alpha": AlphaWriter,
        "fixture.beta": BetaWriter,
    }


def test_discovery_concurrent_waiter_cannot_obtain_partial_registry(
    isolated_discovery_registry, monkeypatch
):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    registry = isolated_discovery_registry
    failure = ImportError("synthetic blocked writer import failure")
    partial, imported = _fail_after_partial_registration(registry, monkeypatch, failure)
    import_writer = registry.importlib.import_module
    entered = Event()
    release = Event()
    waiter_started = Event()

    def blocked_import(name):
        if name.endswith(".broken"):
            entered.set()
            assert release.wait(timeout=2)
        return import_writer(name)

    def waiting_lookup():
        waiter_started.set()
        return registry.get_writer("fixture.partial")

    monkeypatch.setattr(registry.importlib, "import_module", blocked_import)
    with ThreadPoolExecutor(max_workers=2) as workers:
        first = workers.submit(registry.discover_all)
        try:
            assert entered.wait(timeout=2)
            second = workers.submit(waiting_lookup)
            assert waiter_started.wait(timeout=2)
            assert not second.done()
        finally:
            release.set()
        with pytest.raises(ImportError) as initial:
            first.result(timeout=2)
        assert initial.value is failure
        with pytest.raises(RuntimeError, match="writer discovery previously failed") as repeated:
            second.result(timeout=2)
        assert repeated.value.__cause__ is failure
    assert imported == ["partial", "broken"]
    assert registry.list_writers() == {"fixture.partial": partial}


def test_discovery_iterator_failure_stays_failed(isolated_discovery_registry, monkeypatch):
    registry = isolated_discovery_registry
    failure = RuntimeError("synthetic discovery iterator failure")
    partial, imported = _fail_after_partial_registration(registry, monkeypatch, failure)

    def interrupted_frontier(path):
        yield None, "partial", False
        raise failure

    monkeypatch.setattr(registry.pkgutil, "iter_modules", interrupted_frontier)
    with pytest.raises(RuntimeError) as first:
        registry.discover_all()
    assert first.value is failure
    with pytest.raises(RuntimeError, match="writer discovery previously failed") as repeated:
        registry.get_writer("fixture.partial")
    assert repeated.value.__cause__ is failure
    assert imported == ["partial"]
    assert registry.list_writers() == {"fixture.partial": partial}
