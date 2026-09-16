"""DP-SD-017 KSH-P0: mutation-safe Kshetra planning and recovery."""
from __future__ import annotations

import copy
import re
from types import SimpleNamespace

import pytest

from pipeline.orchestrator import asset_runner
from pipeline.orchestrator.writers import SubStep, WriterResult
from services.ka_kshetra import stage0_kinematics as S0
from services.ka_kshetra import writer as W
from tests.l3.ka_kshetra import fixtures as F
from tests.l3.ka_kshetra.fake_db import FakeConn, FakeCtx, FakeCursor


def _mutating_statements(conn: FakeConn) -> list[str]:
    return [
        sql for sql in conn.executed
        if re.match(r"\s*(?:DELETE|INSERT|UPDATE|TRUNCATE)\b", sql, re.IGNORECASE)
    ]


def _plan(conn: FakeConn, *, dry_run: bool = False):
    ctx = FakeCtx(conn, F.CHART_ID, dry_run=dry_run)
    writer = W.KaKshetraWriter()
    return writer, ctx, writer.plan_substeps(ctx)


def _without_owned_outputs(tables: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Keep source fixtures but remove every output owned by this writer."""
    for table, _predicate in W._OWNED_TABLES:
        if table == 'kala_insights':
            tables[table] = [
                row for row in tables.get(table, [])
                if row.get('lel_derived') is True
            ]
        else:
            tables[table] = []
    return tables


class _TransactionalCursor(FakeCursor):
    """Add the real driver's transaction statements to the strict Kshetra fake."""

    def execute(self, sql: str, params: tuple = ()) -> None:
        statement = ' '.join(sql.split())
        if statement == 'SAVEPOINT writer_exec':
            self._conn.executed.append(sql)
            self._conn.savepoint = (
                copy.deepcopy(self._conn.tables),
                copy.deepcopy(self._conn.inserts),
                list(self._conn.deletes),
            )
            return
        if statement == 'ROLLBACK TO SAVEPOINT writer_exec':
            self._conn.executed.append(sql)
            tables, inserts, deletes = self._conn.savepoint
            self._conn.tables = tables
            self._conn.inserts = inserts
            self._conn.deletes = deletes
            return
        if statement == 'RELEASE SAVEPOINT writer_exec':
            self._conn.executed.append(sql)
            self._conn.savepoint = None
            return
        if statement.startswith('UPDATE asset_throughput'):
            self._conn.executed.append(sql)
            return
        super().execute(sql, params)


class _TransactionalFakeConn(FakeConn):
    """In-memory SAVEPOINT/commit semantics for the actual substep driver."""

    def __init__(self, tables: dict[str, list[dict]]):
        super().__init__(tables)
        self.savepoint = None
        self.commits = 0

    def cursor(self, *args, **kwargs) -> _TransactionalCursor:
        return _TransactionalCursor(self)

    def commit(self) -> None:
        assert self.savepoint is None, 'driver must release before commit'
        self.commits += 1


def test_planning_is_zero_dml_and_prepare_is_first() -> None:
    conn = FakeConn(F.build_tables())

    _, _, steps = _plan(conn)

    assert steps[0].key == 'prepare:replace'
    assert _mutating_statements(conn) == []
    assert conn.deletes == []


def test_prepare_clears_every_owned_table_once_in_dependency_safe_order() -> None:
    conn = FakeConn(_without_owned_outputs(F.build_tables()))
    writer, ctx, steps = _plan(conn)

    writer.run_substep(ctx, steps[0])

    expected = [table for table, _ in W._OWNED_TABLES] + ['build_substep_progress']
    assert conn.deletes == expected
    assert len(expected) == len(set(expected))
    assert expected.index('kala_field_primitives') < expected.index('kala_field_kinematics')
    assert expected.index('kala_field_routes') < expected.index('kala_field_promise_edges')
    assert expected.index('kala_field_promise_edges') < expected.index('kala_field_promise_nodes')
    progress = conn.tables['build_substep_progress']
    assert len(progress) == 1
    assert progress[0]['substep_key'] == 'prepare:replace'
    assert progress[0]['build_fingerprint'] == writer._fingerprint()


@pytest.mark.parametrize('table,predicate', W._OWNED_TABLES)
def test_any_preexisting_writer_owned_output_holds_replacement_without_dml(
    table: str, predicate: str | None,
) -> None:
    tables = _without_owned_outputs(F.build_tables())
    row = {'chart_id': F.CHART_ID}
    if table == 'kala_insights':
        assert predicate == 'lel_derived = FALSE'
        row['lel_derived'] = False
    tables[table].append(row)
    conn = FakeConn(tables)
    prior_slice = copy.deepcopy(conn.tables)
    writer, ctx, steps = _plan(conn)

    with pytest.raises(W.KshetraReplacementHeld, match=table):
        writer.run_substep(ctx, steps[0])

    assert conn.advisory_locks == [(W.ASSET_ID, F.CHART_ID)]
    assert conn.tables == prior_slice
    assert _mutating_statements(conn) == []
    assert conn.deletes == []


def test_lane_e_only_insight_does_not_block_and_survives_empty_slice_prepare() -> None:
    tables = _without_owned_outputs(F.build_tables())
    lane_e_row = {
        'chart_id': F.CHART_ID, 'insight_id': 'kin_laneE_biographical',
        'insight_type': 'biographical_echo', 'lel_derived': True,
    }
    tables['kala_insights'].append(lane_e_row)
    conn = FakeConn(tables)
    writer, ctx, steps = _plan(conn)

    writer.run_substep(ctx, steps[0])

    assert conn.tables['kala_insights'] == [lane_e_row]
    assert conn.advisory_locks == [(W.ASSET_ID, F.CHART_ID)]


def test_matching_resume_is_zero_dml_and_does_not_prepare_twice() -> None:
    conn = FakeConn(_without_owned_outputs(F.build_tables()))
    writer, ctx, steps = _plan(conn)
    writer.run_substep(ctx, steps[0])
    deletes_after_prepare = list(conn.deletes)
    conn.executed.clear()

    _, _, resumed = _plan(conn)

    assert 'prepare:replace' not in {step.key for step in resumed}
    assert _mutating_statements(conn) == []
    assert conn.deletes == deletes_after_prepare


def test_dhara_semantic_version_changes_snapshot_and_resume_identity(monkeypatch) -> None:
    """The v1.1 -> v1.2 endpoint repair must invalidate both identities."""
    with monkeypatch.context() as patch_v11:
        patch_v11.setattr(W, '_dhara_sweep_semantic_version', lambda: '1.1')
        writer_v11, _, _ = _plan(FakeConn(F.build_tables()))
        snapshot_v11 = writer_v11._snapshot_id
        fingerprint_v11 = writer_v11._fingerprint()
        assert writer_v11._pins.config_pin['dhara_sweep_semantic_version'] == '1.1'

    with monkeypatch.context() as patch_v12:
        patch_v12.setattr(W, '_dhara_sweep_semantic_version', lambda: '1.2')
        writer_v12, _, _ = _plan(FakeConn(F.build_tables()))
        snapshot_v12 = writer_v12._snapshot_id
        fingerprint_v12 = writer_v12._fingerprint()
        assert writer_v12._pins.config_pin['dhara_sweep_semantic_version'] == '1.2'
        # Hold the snapshot constant to prove the semantic version is also a
        # direct resume-fingerprint input rather than moving only transitively.
        writer_v12._snapshot_id = snapshot_v11
        fingerprint_v12_same_snapshot = writer_v12._fingerprint()

    assert snapshot_v11 != snapshot_v12
    assert fingerprint_v11 != fingerprint_v12
    assert fingerprint_v11 != fingerprint_v12_same_snapshot


def test_later_stage_crash_replan_preserves_prior_slice_without_dml() -> None:
    tables = _without_owned_outputs(F.build_tables())
    tables['kala_field'].append({
        'chart_id': F.CHART_ID, 'event_class': F.EVENT_CLASS,
        'segment_index': 99, 't_start': 0.0,
    })
    tables['kala_field_snapshots'].append({
        'chart_id': F.CHART_ID, 'field_snapshot_id': 'prior-servable',
    })
    tables['kala_insights'].append({
        'chart_id': F.CHART_ID, 'insight_id': 'prior-field-insight',
        'lel_derived': False,
    })
    tables['build_substep_progress'] = [{
        'chart_id': F.CHART_ID,
        'asset_id': W.ASSET_ID,
        'substep_key': 'stage4:stale:0',
        'build_fingerprint': 'v7-stale-fingerprint',
        'rows_written': 1,
    }]
    conn = FakeConn(tables)
    prior_slice = copy.deepcopy(conn.tables)

    writer, ctx, steps = _plan(conn)

    assert steps[0].key == 'prepare:replace'
    assert _mutating_statements(conn) == []

    with pytest.raises(W.KshetraReplacementHeld, match='until W7'):
        writer.run_substep(ctx, steps[0])
    assert conn.tables == prior_slice
    assert _mutating_statements(conn) == []
    assert conn.deletes == []


def test_driver_rollback_removes_failed_plugin_output_and_receipt(monkeypatch) -> None:
    conn = _TransactionalFakeConn(_without_owned_outputs(F.build_tables()))
    writer, ctx, steps = _plan(conn)
    prepare = steps[0]
    stage0_sun = next(step for step in steps if step.key == 'stage0:Sun')
    stage0_moon = next(step for step in steps if step.key == 'stage0:Moon')
    attempted_outputs: list[str] = []
    attempted_receipts: list[str] = []

    def plugin_stage(_ctx, step):
        body = step.key.split(':', 1)[1]
        conn.tables['kala_field_kinematics'].append({
            'chart_id': F.CHART_ID, 'event_kind': 'sign_ingress',
            'body': body, 'target_ref': None, 't_days': 1.0,
        })
        attempted_outputs.append(body)
        return WriterResult(asset_id=W.ASSET_ID, rows_inserted=1)

    original_record = writer._record_substep

    def record_then_crash(record_conn, substep_key, rows):
        original_record(record_conn, substep_key, rows)
        attempted_receipts.append(substep_key)
        if substep_key == stage0_moon.key:
            raise RuntimeError('crash after plugin output and receipt')

    monkeypatch.setattr(S0, 'run_substep', plugin_stage)
    monkeypatch.setattr(writer, '_record_substep', record_then_crash)
    monkeypatch.setattr(writer, 'plan_substeps', lambda _ctx: [
        prepare, stage0_sun, stage0_moon,
    ])
    monkeypatch.setattr(asset_runner, 'emit_event', lambda *_args, **_kwargs: None)

    with pytest.raises(RuntimeError, match='crash after plugin output and receipt'):
        asset_runner._drive_substeps(
            conn, conn.cursor(), ctx.build_id, F.CHART_ID, W.ASSET_ID, writer, ctx,
        )

    assert conn.commits == 2, 'prepare and Sun committed before Moon crashed'
    assert attempted_outputs == ['Sun', 'Moon']
    assert attempted_receipts == ['prepare:replace', 'stage0:Sun', 'stage0:Moon']
    assert [row['body'] for row in conn.tables['kala_field_kinematics']] == ['Sun']
    receipts = {row['substep_key'] for row in conn.tables['build_substep_progress']}
    assert receipts == {'prepare:replace', 'stage0:Sun'}
    assert 'ROLLBACK TO SAVEPOINT writer_exec' in conn.executed

    conn.executed.clear()
    _, _, resumed = _plan(conn)
    resumed_keys = {step.key for step in resumed}
    assert 'prepare:replace' not in resumed_keys
    assert 'stage0:Sun' not in resumed_keys
    assert 'stage0:Moon' in resumed_keys
    assert _mutating_statements(conn) == []


def test_dry_run_complete_isolated_plan_is_zero_dml(monkeypatch) -> None:
    dry_conn = FakeConn(F.build_tables())
    before = copy.deepcopy(dry_conn.tables)

    def isolated_plugins(writer, _ctx):
        writer._plugin_stages = ['services.ka_kshetra.stage0_kinematics']
        return [SubStep(key='stage0:Sun')]

    monkeypatch.setattr(W.KaKshetraWriter, '_optional_stage_plugins', isolated_plugins)
    monkeypatch.setattr(W, 'DECADES', 1)
    monkeypatch.setattr(W, 'TIMELINE_VIEWS', ('now',))
    monkeypatch.setattr(
        W.DN, 'dhara_compute_null',
        lambda *_args, **_kwargs: SimpleNamespace(replicates=1, q_threshold=None),
    )
    monkeypatch.setattr(
        S0, 'run_substep',
        lambda *_args, **_kwargs: WriterResult(asset_id=W.ASSET_ID, rows_inserted=1),
    )
    writer, ctx, steps = _plan(dry_conn, dry_run=True)
    writer._class_cache[F.EVENT_CLASS] = SimpleNamespace(
        evaluator=object(), dhara_segments=[],
    )

    for step in steps:
        writer.run_substep(ctx, step)

    assert _mutating_statements(dry_conn) == []
    assert dry_conn.tables == before


def test_empty_discovery_preserves_preexisting_output_without_dml(monkeypatch) -> None:
    empty_tables = _without_owned_outputs(F.build_tables())
    empty_tables['bodha_pratijna'] = []
    empty_tables['kala_field'].append({
        'chart_id': F.CHART_ID, 'event_class': 'stale', 'segment_index': 1,
    })
    empty_tables['kala_field_snapshots'].append({
        'chart_id': F.CHART_ID, 'field_snapshot_id': 'prior-servable',
    })
    empty_tables['kala_insights'].append({
        'chart_id': F.CHART_ID, 'insight_id': 'prior-field-insight',
        'lel_derived': False,
    })
    empty_tables['build_substep_progress'].append({
        'chart_id': F.CHART_ID, 'asset_id': W.ASSET_ID,
        'substep_key': 'stage4:stale:0', 'build_fingerprint': 'old',
        'rows_written': 1,
    })
    empty_conn = _TransactionalFakeConn(empty_tables)
    prior_slice = copy.deepcopy(empty_conn.tables)

    writer, ctx, empty_steps = _plan(empty_conn)

    assert [step.key for step in empty_steps] == ['prepare:replace']
    assert _mutating_statements(empty_conn) == []
    monkeypatch.setattr(asset_runner, 'emit_event', lambda *_args, **_kwargs: None)
    with pytest.raises(W.KshetraReplacementHeld, match='until W7'):
        asset_runner._drive_substeps(
            empty_conn, empty_conn.cursor(), ctx.build_id, F.CHART_ID,
            W.ASSET_ID, writer, ctx,
        )
    assert empty_conn.commits == 0
    assert 'SAVEPOINT writer_exec' in empty_conn.executed
    assert 'ROLLBACK TO SAVEPOINT writer_exec' in empty_conn.executed
    assert empty_conn.tables == prior_slice
    assert _mutating_statements(empty_conn) == []


def test_actually_empty_discovery_noops_prepare_without_dml() -> None:
    tables = _without_owned_outputs(F.build_tables())
    tables['bodha_pratijna'] = []
    tables['build_substep_progress'] = []
    conn = FakeConn(tables)
    prior_slice = copy.deepcopy(conn.tables)

    writer, ctx, steps = _plan(conn)
    result = writer.run_substep(ctx, steps[0])

    assert result.rows_inserted == 0
    assert result.notes == 'honest_empty:no_event_classes; replacement not required'
    assert conn.tables == prior_slice
    assert _mutating_statements(conn) == []
    assert conn.deletes == []


def test_event_class_discovery_error_is_not_an_honest_empty() -> None:
    broken_tables = F.build_tables()
    broken_tables['bodha_pratijna'] = [{
        'chart_id': F.CHART_ID, 'status': 'promised',
    }]
    broken_conn = FakeConn(broken_tables)

    with pytest.raises(RuntimeError, match='event-class discovery failed'):
        _plan(broken_conn)
    assert _mutating_statements(broken_conn) == []


def test_prepare_does_not_own_transaction_lifecycle() -> None:
    # FakeConn raises if commit/rollback/close is called.
    conn = FakeConn(_without_owned_outputs(F.build_tables()))
    writer, ctx, steps = _plan(conn)
    writer.run_substep(ctx, steps[0])
