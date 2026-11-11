"""Sangam previews may read but may not mutate a borrowed or owning transaction."""
import importlib
import sys
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from panchang_engine import swiss_backend
from pipeline.orchestrator import birth_params
from pipeline.orchestrator.writers import ContextSpec, SubStep, WriterResult
from pipeline.orchestrator.writers import ka_sangam as sangam
from services.ka_sangam.jury import candidate
from tests.l3.ka_sangam.test_jury_writer import CHART, GEN, fixture_input

BIRTH_PARAMS = {'datetime_iso': '1980-01-01T12:00:00+00:00'}


@pytest.fixture
def borrowed_writer(monkeypatch):
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value
    writer = sangam.KaSangamWriter()
    writer._chart_id = CHART
    writer._candidate = object()
    writer._birth_year = 1980
    writer._reset_pending = True
    writer._dks = writer._gs = writer._muhurta = None
    writer._enrichment_ctx = writer._native_ctx = None
    writer._pred_dicts = ({'signal_id': 'synthetic-signal'},)
    writer._lt_preds = writer._pred_dicts
    monkeypatch.setattr(swiss_backend, 'ensure_swiss_backend', lambda *jds: None)
    monkeypatch.setattr(swiss_backend, 'backend_note', lambda *jds: 'ephemeris_backend=synthetic')
    generation = MagicMock(return_value='candidate:synthetic')
    monkeypatch.setattr(sangam, 'convergence_generation', generation)

    def preview(*, pred_dicts, horizon_start, keepalive, **_kwargs):
        keepalive()
        return [{'mode': 'A', 'peak_date': horizon_start + timedelta(days=1),
                 'signal_id': row['signal_id'], 'convergence_score': 0.5} for row in pred_dicts]

    monkeypatch.setattr(writer, '_generate_windows', preview)
    ctx = ContextSpec('ka_sangam', 'fixture-build', conn,
                      {'chart_id': CHART, 'birth_params': BIRTH_PARAMS}, dry_run=True)
    return writer, ctx, cursor, generation


@pytest.mark.parametrize(('key', 'lifetime'), [('near', True), ('near', False), ('lifetime:0', True)])
def test_legacy_preview_reads_without_locking_output_or_acknowledging_rows(borrowed_writer, key, lifetime):
    writer, ctx, cursor, generation = borrowed_writer
    if not lifetime:
        writer._lt_preds = ()
    result = writer.run_substep(ctx, SubStep(key=key))
    assert [call.args[0] for call in cursor.execute.call_args_list] == ['SELECT 1']
    generation.assert_not_called()
    assert result.rows_inserted == result.rows_updated == 0
    assert writer._windows_written == 1
    assert writer._reset_pending
    ctx.db_conn.commit.assert_not_called()
    ctx.db_conn.rollback.assert_not_called()
    ctx.db_conn.close.assert_not_called()


def test_dry_replayed_grain_does_not_attest(borrowed_writer, monkeypatch):
    writer, ctx, cursor, _ = borrowed_writer
    attest = MagicMock()
    monkeypatch.setattr(writer, '_attest_candidate_grain', attest)
    result = writer.run_substep(ctx, SubStep(key='grain:inputs'))
    attest.assert_not_called()
    assert result.rows_inserted == result.rows_updated == 0
    assert 'dry_run' in result.notes
    cursor.execute.assert_not_called()


def test_jury_preview_uses_read_binding_only(borrowed_writer, monkeypatch):
    writer, ctx, cursor, _ = borrowed_writer
    ctx.config['jury_fixture_inputs'] = [fixture_input()]
    binding = MagicMock(return_value=GEN)
    monkeypatch.setattr(candidate, 'bind_candidate', binding)
    steps = writer.plan_substeps(ctx)
    assert [step.key for step in steps] == ['class:career']
    result = writer.run_substep(ctx, steps[0])
    binding.assert_called_once_with(ctx, lock=False)
    cursor.execute.assert_not_called()
    assert result.rows_inserted == result.rows_updated == 0
    ctx.db_conn.commit.assert_not_called()
    ctx.db_conn.rollback.assert_not_called()


@pytest.fixture
def cli_fixture(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'synthetic-fixture-dsn')
    cli = importlib.import_module('run_ka_sangam_prod')
    conn = MagicMock(read_only=False)
    cursor = conn.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = ('30min', '30s', '5min')
    fetch = MagicMock(return_value=BIRTH_PARAMS)
    run = MagicMock(return_value=WriterResult('ka_sangam', 0))
    monkeypatch.setattr(cli, 'DB_URL', 'synthetic-fixture-dsn')
    monkeypatch.setattr(cli, 'CHART_ID', CHART)

    def connect(dsn, **_kwargs):
        assert dsn == 'synthetic-fixture-dsn'
        return conn

    monkeypatch.setattr(cli.psycopg, 'connect', connect)
    monkeypatch.setattr(birth_params, 'fetch_birth_params', fetch)
    monkeypatch.setitem(cli._REGISTRY, 'ka_sangam', lambda: SimpleNamespace(run=run))
    return cli, conn, cursor, fetch, run


def test_cli_dry_run_rolls_back_preview_without_predelete_or_completion(cli_fixture, monkeypatch, caplog):
    cli, conn, cursor, fetch, run = cli_fixture
    monkeypatch.setattr(sys, 'argv', ['run_ka_sangam_prod.py', '--dry-run'])
    with caplog.at_level('INFO'):
        cli.main()
    assert conn.read_only
    conn.commit.assert_not_called()
    conn.rollback.assert_called_once_with()
    conn.close.assert_called_once_with()
    fetch.assert_called_once_with(conn, CHART)
    assert run.call_args.args[0].dry_run
    assert not any('DELETE' in call.args[0] for call in cursor.execute.call_args_list)
    assert 'DRY-RUN PREVIEW' in caplog.text and 'COMPLETE:' not in caplog.text


@pytest.mark.parametrize('phase', ['setup', 'birth_lookup', 'writer'])
def test_cli_dry_run_failure_rolls_back_and_never_commits(cli_fixture, monkeypatch, caplog, phase):
    cli, conn, cursor, fetch, run = cli_fixture
    monkeypatch.setattr(sys, 'argv', ['run_ka_sangam_prod.py', '--dry-run'])
    failing_call = {'setup': cursor.execute, 'birth_lookup': fetch, 'writer': run}[phase]
    failing_call.side_effect = RuntimeError('synthetic preview refusal')
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1
    assert conn.read_only
    conn.commit.assert_not_called()
    conn.rollback.assert_called_once_with()
    conn.close.assert_called_once_with()
    assert not any('DELETE' in call.args[0] for call in cursor.execute.call_args_list)
    if phase != 'writer':
        run.assert_not_called()
    assert 'COMPLETE:' not in caplog.text


def test_cli_non_dry_run_preserves_setup_predelete_read_and_write_commits(cli_fixture, monkeypatch, caplog):
    cli, conn, cursor, fetch, run = cli_fixture
    monkeypatch.setattr(sys, 'argv', ['run_ka_sangam_prod.py'])
    sequence = MagicMock()
    sequence.attach_mock(conn.commit, 'commit')
    sequence.attach_mock(cursor.execute, 'execute')
    sequence.attach_mock(fetch, 'fetch')
    sequence.attach_mock(run, 'run')
    with caplog.at_level('INFO'):
        cli.main()
    assert not conn.read_only
    assert [call[0] for call in sequence.mock_calls] == [
        'execute', 'execute', 'execute', 'commit',
        'execute', 'commit', 'fetch', 'commit', 'run', 'commit',
    ]
    conn.rollback.assert_not_called()
    conn.close.assert_called_once_with()
    cursor.execute.assert_any_call('DELETE FROM phala_anchors WHERE chart_id = %s AND anchor_source = %s',
                                   (CHART, 'convergence'))
    fetch.assert_called_once_with(conn, CHART)
    assert not run.call_args.args[0].dry_run
    assert 'COMPLETE: rows_inserted=0' in caplog.text
