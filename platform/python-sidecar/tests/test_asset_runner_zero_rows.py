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
from pipeline.orchestrator.writers import SubStep, WriterBase, WriterResult


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
    monkeypatch.setattr(ar, 'get_writer_source_hash', lambda aid: 'hash-writer')
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


def test_unavailable_provenance_blocks_writer_before_output_mutation(monkeypatch):
    """A source-hash failure is an execution error before a writer can write output."""
    called: list[bool] = []
    errors: list[str] = []

    class _Writer(WriterBase):
        asset_id = '_test_provenance'

        def run(self, ctx):
            called.append(True)
            return WriterResult(asset_id=self.asset_id, rows_inserted=1, rows_updated=0)

    monkeypatch.setattr(ar, 'discover_all', lambda: None)
    monkeypatch.setattr(ar, 'get_writer', lambda aid: _Writer)
    monkeypatch.setattr(ar, 'fetch_birth_params', lambda conn, cid: {'chart_id': cid})
    monkeypatch.setattr(ar, 'compute_upstream_hash', lambda cur, aid, cid: 'hash-upstream')
    monkeypatch.setattr(ar, 'get_writer_source_hash', lambda aid: (_ for _ in ()).throw(RuntimeError('source unavailable')))
    monkeypatch.setattr(ar, 'mark_asset_error', lambda conn, cur, run, chart, asset, error: errors.append(error))

    assert ar._run_data_writer(FakeConn(), FakeCursor(), 'run-1', 'chart-abc', _Writer.asset_id) is False
    assert called == []
    assert errors == ['provenance: source unavailable']


def test_failed_post_write_integrity_rolls_back_output_before_recording_error(monkeypatch):
    """A writer result is not success until its configured integrity SQL passes."""
    events: list[str] = []

    class _Writer(WriterBase):
        asset_id = '_test_post_write_integrity'

        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=1, rows_updated=0)

    class _Cursor(FakeCursor):
        def fetchone(self):
            sql = self.executed[-1][0] if self.executed else ''
            if 'integrity_check_sql' in sql:
                return {
                    'asset_kind': 'data', 'asset_type': 'data',
                    'integrity_check_sql': 'SELECT true',
                }
            if 'target_floor' in sql:
                return {'target_floor': 1}
            return None

    class _Conn(FakeConn):
        def rollback(self):
            events.append('rollback')

    monkeypatch.setattr(ar, 'emit_event', lambda event, cur=None: None)
    monkeypatch.setattr(ar, 'discover_all', lambda: None)
    monkeypatch.setattr(ar, 'get_writer', lambda asset_id: _Writer)
    monkeypatch.setattr(ar, 'load_upstream_receipts', lambda cur, deps, chart_id: [])
    monkeypatch.setattr(ar, 'compute_upstream_hash', lambda cur, asset_id, chart_id: 'upstream')
    monkeypatch.setattr(ar, 'get_writer_source_hash', lambda asset_id: 'writer')
    monkeypatch.setattr(ar, '_drive_substeps', lambda *args, **kwargs: (1, 0))
    monkeypatch.setattr(ar, '_probe_asset', lambda *args, **kwargs: (False, 'detector returned false'))
    monkeypatch.setattr(
        ar,
        'mark_asset_error',
        lambda conn, cur, run_id, chart_id, asset_id, error: events.append(f'error:{error}'),
    )

    conn = _Conn()
    result = ar._run_data_writer(conn, _Cursor(), 'run-1', None, _Writer.asset_id)

    assert result is False
    assert conn.commits == 0
    assert events == ['rollback', 'error:post-write integrity check failed: detector returned false']


def test_light_writer_output_is_not_committed_before_post_write_integrity(monkeypatch):
    """The default one-step writer remains rollbackable until its detector passes."""
    events: list[str] = []

    class _Writer(WriterBase):
        asset_id = '_test_atomic_post_write_integrity'

        def run(self, ctx):
            return WriterResult(asset_id=self.asset_id, rows_inserted=1, rows_updated=0)

    class _Cursor(FakeCursor):
        def fetchone(self):
            sql = self.executed[-1][0] if self.executed else ''
            if 'integrity_check_sql' in sql:
                return {'integrity_check_sql': 'SELECT true'}
            return None

    class _Conn(FakeConn):
        def commit(self):
            super().commit()
            events.append('commit')

        def rollback(self):
            events.append('rollback')

    monkeypatch.setattr(ar, 'emit_event', lambda event, cur=None: None)
    monkeypatch.setattr(ar, 'discover_all', lambda: None)
    monkeypatch.setattr(ar, 'get_writer', lambda asset_id: _Writer)
    monkeypatch.setattr(ar, 'load_upstream_receipts', lambda cur, deps, chart_id: [])
    monkeypatch.setattr(ar, 'compute_upstream_hash', lambda cur, asset_id, chart_id: 'upstream')
    monkeypatch.setattr(ar, 'get_writer_source_hash', lambda asset_id: 'writer')
    monkeypatch.setattr(ar, '_probe_asset', lambda *args, **kwargs: (False, 'detector returned false'))
    monkeypatch.setattr(
        ar,
        'mark_asset_error',
        lambda conn, cur, run_id, chart_id, asset_id, error: events.append(f'error:{error}'),
    )

    result = ar._run_data_writer(_Conn(), _Cursor(), 'run-1', None, _Writer.asset_id)

    assert result is False
    assert events == ['rollback', 'error:post-write integrity check failed: detector returned false']


def test_integrity_gated_writer_exception_rolls_back_before_recording_error(monkeypatch):
    """An error record must never commit an open writer transaction."""
    events: list[str] = []

    class _Writer(WriterBase):
        asset_id = '_test_integrity_exception'
        has_substeps = True

        def plan_substeps(self, ctx):
            return [SubStep(key='one'), SubStep(key='two')]

        def run_substep(self, ctx, step):
            if step.key == 'two':
                raise RuntimeError('step two failed')
            return WriterResult(asset_id=self.asset_id, rows_inserted=1)

    class _Cursor(FakeCursor):
        def fetchone(self):
            sql = self.executed[-1][0] if self.executed else ''
            if 'integrity_check_sql' in sql:
                return {'integrity_check_sql': 'SELECT true'}
            return None

    class _Conn(FakeConn):
        def commit(self):
            super().commit()
            events.append('commit')

        def rollback(self):
            events.append('rollback')

    monkeypatch.setattr(ar, 'emit_event', lambda event, cur=None: None)
    monkeypatch.setattr(ar, 'discover_all', lambda: None)
    monkeypatch.setattr(ar, 'get_writer', lambda asset_id: _Writer)
    monkeypatch.setattr(ar, 'load_upstream_receipts', lambda cur, deps, chart_id: [])
    monkeypatch.setattr(ar, 'compute_upstream_hash', lambda cur, asset_id, chart_id: 'upstream')
    monkeypatch.setattr(ar, 'get_writer_source_hash', lambda asset_id: 'writer')
    monkeypatch.setattr(
        ar,
        'mark_asset_error',
        lambda conn, cur, run_id, chart_id, asset_id, error: events.append(f'error:{error.splitlines()[0]}'),
    )

    result = ar._run_data_writer(_Conn(), _Cursor(), 'run-1', None, _Writer.asset_id)

    assert result is False
    assert events[-2:] == ['rollback', 'error:RuntimeError: step two failed']
