"""DP-SD-017 KSH-P0: mutation-safe Kshetra planning and recovery."""
from __future__ import annotations

import copy
import re

from pipeline.orchestrator.writers import WriterResult
from services.ka_kshetra import stage0_kinematics as S0
from services.ka_kshetra import writer as W
from tests.l3.ka_kshetra import fixtures as F
from tests.l3.ka_kshetra.fake_db import FakeConn, FakeCtx


def _mutating_statements(conn: FakeConn) -> list[str]:
    return [
        sql for sql in conn.executed
        if re.match(r"\s*(?:DELETE|INSERT|UPDATE|TRUNCATE)\b", sql, re.IGNORECASE)
    ]


def _plan(conn: FakeConn, *, dry_run: bool = False):
    ctx = FakeCtx(conn, F.CHART_ID, dry_run=dry_run)
    writer = W.KaKshetraWriter()
    return writer, ctx, writer.plan_substeps(ctx)


def test_planning_is_zero_dml_and_prepare_is_first() -> None:
    conn = FakeConn(F.build_tables())

    _, _, steps = _plan(conn)

    assert steps[0].key == 'prepare:replace'
    assert _mutating_statements(conn) == []
    assert conn.deletes == []


def test_prepare_clears_every_owned_table_once_in_dependency_safe_order() -> None:
    conn = FakeConn(F.build_tables())
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


def test_matching_resume_is_zero_dml_and_does_not_prepare_twice() -> None:
    conn = FakeConn(F.build_tables())
    writer, ctx, steps = _plan(conn)
    writer.run_substep(ctx, steps[0])
    deletes_after_prepare = list(conn.deletes)
    conn.executed.clear()

    _, _, resumed = _plan(conn)

    assert 'prepare:replace' not in {step.key for step in resumed}
    assert _mutating_statements(conn) == []
    assert conn.deletes == deletes_after_prepare


def test_stale_resume_defers_replacement_until_prepare_execution() -> None:
    tables = F.build_tables()
    tables['kala_field'].append({
        'chart_id': F.CHART_ID, 'event_class': F.EVENT_CLASS,
        'segment_index': 99, 't_start': 0.0,
    })
    tables['build_substep_progress'] = [{
        'chart_id': F.CHART_ID,
        'asset_id': W.ASSET_ID,
        'substep_key': 'stage4:stale:0',
        'build_fingerprint': 'v7-stale-fingerprint',
        'rows_written': 1,
    }]
    conn = FakeConn(tables)

    writer, ctx, steps = _plan(conn)

    assert steps[0].key == 'prepare:replace'
    assert conn.tables['kala_field'], 'stale output must survive read-only validation'
    assert _mutating_statements(conn) == []

    writer.run_substep(ctx, steps[0])
    assert conn.tables['kala_field'] == []
    assert [row['substep_key'] for row in conn.tables['build_substep_progress']] == [
        'prepare:replace'
    ]


def test_crash_resume_preserves_committed_plugin_output_and_skips_its_receipt(monkeypatch) -> None:
    conn = FakeConn(F.build_tables())
    writer, ctx, steps = _plan(conn)
    writer.run_substep(ctx, steps[0])
    stage0_sun = next(step for step in steps if step.key == 'stage0:Sun')

    def committed_stage(_ctx, _step):
        conn.tables['kala_field_kinematics'].append({
            'chart_id': F.CHART_ID, 'event_kind': 'sign_ingress',
            'body': 'Sun', 'target_ref': None, 't_days': 1.0,
        })
        return WriterResult(asset_id=W.ASSET_ID, rows_inserted=1)

    monkeypatch.setattr(S0, 'run_substep', committed_stage)
    writer.run_substep(ctx, stage0_sun)
    committed_rows = copy.deepcopy(conn.tables['kala_field_kinematics'])
    conn.executed.clear()

    _, _, resumed = _plan(conn)
    resumed_keys = {step.key for step in resumed}

    assert 'prepare:replace' not in resumed_keys
    assert 'stage0:Sun' not in resumed_keys
    assert 'stage0:Moon' in resumed_keys
    assert conn.tables['kala_field_kinematics'] == committed_rows
    assert _mutating_statements(conn) == []


def test_dry_run_and_honest_empty_probe_are_zero_dml() -> None:
    dry_conn = FakeConn(F.build_tables())
    before = copy.deepcopy(dry_conn.tables)
    writer, ctx, steps = _plan(dry_conn, dry_run=True)

    for step in steps:
        writer.run_substep(ctx, step)

    assert _mutating_statements(dry_conn) == []
    assert dry_conn.tables == before

    empty_tables = F.build_tables()
    empty_tables['bodha_pratijna'] = []
    empty_conn = FakeConn(empty_tables)
    _, _, empty_steps = _plan(empty_conn)
    assert empty_steps == []
    assert _mutating_statements(empty_conn) == []


def test_prepare_does_not_own_transaction_lifecycle() -> None:
    # FakeConn raises if commit/rollback/close is called.
    conn = FakeConn(F.build_tables())
    writer, ctx, steps = _plan(conn)
    writer.run_substep(ctx, steps[0])
