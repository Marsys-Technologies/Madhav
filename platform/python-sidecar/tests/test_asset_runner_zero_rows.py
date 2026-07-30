"""Task 15 (B2) — asset_runner: 0-row writers get 'dormant', not 'lit'.

Tests the final_state logic added to _run_data_writer:
  - chart-scoped writer returning 0 rows → state='dormant' written to asset_throughput.
  - chart-scoped writer returning >0 rows → state='lit' as before.
  - global-scoped writer (chart_id=None) returning 0 rows → state='lit' (service singleton).

All three use FakeCursor / FakeConn — no live DB required.
Writers are NOT decorated with @register to avoid polluting the global writer registry
(which would break test_has_writer_completeness). Instead they are injected via monkeypatch.
"""
from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator import asset_runner as ar
from pipeline.orchestrator.writers import WriterBase, WriterResult


# ── Fakes ─────────────────────────────────────────────────────────────────────

class FakeCursor:
    def __init__(self):
        self.executed: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return []

    def fetchone(self):
        return None

    def params_for(self, keyword: str) -> list[tuple]:
        """Return params tuples from all executed statements containing keyword."""
        return [p for s, p in self.executed if keyword in s]


class FakeConn:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


# ── Writers (not @register-decorated to avoid polluting global registry) ───────

class _ZeroRowWriter(WriterBase):
    asset_id = '_test_zero_rows'

    def run(self, ctx):
        return WriterResult(asset_id=self.asset_id, rows_inserted=0, rows_updated=0)


class _NonZeroRowWriter(WriterBase):
    asset_id = '_test_nonzero_rows'

    def run(self, ctx):
        return WriterResult(asset_id=self.asset_id, rows_inserted=5, rows_updated=2)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _run_with_writer(monkeypatch, writer_cls, chart_id) -> FakeCursor:
    """Run _run_data_writer with the given writer class injected via get_writer stub."""
    monkeypatch.setattr(ar, 'emit_event', lambda e, cur=None: None)
    monkeypatch.setattr(ar, 'discover_all', lambda: None)
    monkeypatch.setattr(ar, 'get_writer', lambda aid: writer_cls)
    monkeypatch.setattr(ar, 'fetch_birth_params', lambda conn, cid: {'chart_id': cid})
    monkeypatch.setattr(ar, 'compute_upstream_hash', lambda cur, aid, cid: 'hash-upstream')
    monkeypatch.setattr(ar, 'get_writer_git_hash', lambda aid: 'hash-writer')
    monkeypatch.setattr(ar, 'compute_downstream_closure', lambda cur, aid: [])

    conn = FakeConn()
    cur = FakeCursor()
    ar._run_data_writer(conn, cur, 'run-1', chart_id, writer_cls.asset_id)
    return cur


def _state_written(cur: FakeCursor) -> str | None:
    """Extract the final_state value from the UPDATE asset_throughput SET state = %s."""
    # params tuple is (final_state, rows_written, upstream_hash, writer_hash, chart_id, asset_id)
    params_list = cur.params_for('SET state = %s')
    return params_list[-1][0] if params_list else None


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_zero_rows_chart_scoped_writes_dormant(monkeypatch):
    """Chart-scoped writer producing 0 rows must record state='dormant'."""
    cur = _run_with_writer(monkeypatch, _ZeroRowWriter, 'chart-abc')
    assert _state_written(cur) == 'dormant', (
        "Expected state='dormant' for chart-scoped 0-row writer, got: %r" % _state_written(cur)
    )


def test_nonzero_rows_chart_scoped_writes_lit(monkeypatch):
    """Chart-scoped writer producing >0 rows must record state='lit' as before."""
    cur = _run_with_writer(monkeypatch, _NonZeroRowWriter, 'chart-abc')
    assert _state_written(cur) == 'lit', (
        "Expected state='lit' for chart-scoped writer with rows, got: %r" % _state_written(cur)
    )


def test_zero_rows_global_scope_writes_lit(monkeypatch):
    """Global-scoped writer (chart_id=None) producing 0 rows must still get state='lit'."""
    cur = _run_with_writer(monkeypatch, _ZeroRowWriter, None)
    assert _state_written(cur) == 'lit', (
        "Expected state='lit' for global (chart_id=None) 0-row writer, got: %r" % _state_written(cur)
    )
