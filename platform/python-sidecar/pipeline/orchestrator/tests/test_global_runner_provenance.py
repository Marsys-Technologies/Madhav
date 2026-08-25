"""Global/L0 builds must persist the same provenance receipts as chart builds."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from pipeline.orchestrator import global_runner
from pipeline.orchestrator.writers import WriterBase, WriterResult


class _Cursor:
    def __init__(self):
        self.executed: list[tuple[str, object]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))


class _Conn:
    def __init__(self):
        self.cursors: list[_Cursor] = []
        self.commits = 0

    def cursor(self):
        cursor = _Cursor()
        self.cursors.append(cursor)
        return cursor

    def commit(self):
        self.commits += 1


def test_global_build_stamps_global_provenance_receipts(monkeypatch):
    persisted: list[tuple[str, str, dict]] = []
    calls: list[tuple[str, str | None]] = []

    class _GlobalWriter(WriterBase):
        asset_id = 'bg_fixture'

        def run(self, ctx):
            assert ctx.config == {}
            return WriterResult(asset_id=self.asset_id, rows_inserted=3, rows_updated=0)

    monkeypatch.setattr(global_runner, 'get_writer', lambda asset_id: _GlobalWriter)
    monkeypatch.setattr(
        global_runner,
        'compute_upstream_hash',
        lambda cur, asset_id, chart_id: calls.append((asset_id, chart_id)) or 'upstream-receipt',
    )
    monkeypatch.setattr(global_runner, 'get_writer_source_hash', lambda asset_id: 'writer-receipt')
    monkeypatch.setattr(
        global_runner,
        '_upsert_asset_throughput_global',
        lambda conn, asset_id, state, **kwargs: persisted.append((asset_id, state, kwargs)),
    )

    assert global_runner._run_asset_writer(_Conn(), 'run-1', 'bg_fixture', {}) == 'ok'
    assert calls == [('bg_fixture', None)]
    assert persisted == [
        ('bg_fixture', 'building', {}),
        ('bg_fixture', 'lit', {'upstream_hash': 'upstream-receipt', 'writer_hash': 'writer-receipt'}),
    ]
