"""Default dispatch must use the K6-5a immutable issue contract, without L4.

The strict in-memory SQL boundary exercises the real registrar and immutable
helper. PostgreSQL triggers/FKs remain the separate lifecycle CI oracles.
"""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from psycopg.sql import Composable
from psycopg.types.json import Jsonb
from psycopg.types.multirange import Multirange
from psycopg.types.range import Range

from pipeline.orchestrator.writers import ka_bhavishya_lekha as registrar
from services.kala_core.idempotency import ImmutableIssueConflict
from tests.l3.test_bhavishya_p0_safety import (
    CHART_ID, _StrictConnection, _StrictCursor, _darshana_row, _existing_row,
)

CHART = UUID(CHART_ID)
BUILD = UUID('22222222-2222-4222-8222-222222222222')
ISSUE = UUID('33333333-3333-4333-8333-333333333333')
AT = datetime(2026, 10, 10, 10, tzinfo=timezone.utc)
PINS = {
    'producer_ref': 'fixture:producer:1', 'coverage_ref': 'fixture:coverage:1',
    'qualification_ref': 'fixture:qualification:1',
    'classes': {'career_change': {
        'result_policy': 'structural', 'calibration_status': 'uncalibrated',
        'ontology_locator': 'fixture:ontology:1', 'domain': 'career',
        'observation_predicate': 'No recorded career change in the disclosed interval',
    }},
}


def _input():
    return registrar.RegistrarInput(
        issue_id=ISSUE, version=1, generation='fixture:v1', event_class='career_change',
        phase='fruition', affected_person='native', episode='career:1', issued_at=AT,
        information_cutoff=AT, statement='  Delivered statement.\n',
        intervals=Multirange([Range(AT, AT + timedelta(days=1), '[)')]),
        disclosed_grain='day', point_functional='none', probability_target=None,
        model_digest='fixture:model:1', producer_ref=PINS['producer_ref'],
        coverage_ref=PINS['coverage_ref'], qualification_ref=PINS['qualification_ref'],
        result_policy='structural', calibration_status='uncalibrated',
        delivery=registrar.DeliveryConfirmation(ISSUE, 1, '  Delivered statement.\n', 'fixture:inbox', AT, True),
        ontology=registrar.ObservationPredicate('fixture:ontology:1', 'career_change', 'career',
                                               PINS['classes']['career_change']['observation_predicate']),
    )


class _Cursor:
    def __init__(self, conn):
        self.conn = conn
        self.one = None
        self.legacy = _StrictCursor(conn.legacy)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=()):
        query = query.as_string() if isinstance(query, Composable) else query
        statement = ' '.join(query.split())
        self.conn.sql.append(statement)
        self.one = None
        if 'phala_anchors' in statement:
            if self.conn.l4_unavailable:
                raise RuntimeError('L4 protective read unavailable')
            self.legacy.execute(statement, params)
            self.one = self.legacy.fetchone()
            return self
        if statement.startswith('SELECT state, model_digest, conventions FROM kala_layer_candidate'):
            assert tuple(params) == (str(CHART), 'fixture:v1', str(BUILD))
            self.one = ('complete', 'fixture:model:1', {'fixture': True, 'registrar': PINS})
        elif statement.startswith('SELECT generation FROM kala_layer_head'):
            assert tuple(params) == (str(CHART),)
        elif statement.startswith('INSERT INTO issued_forecast ('):
            assert 'ON CONFLICT (issue_id, version) DO NOTHING RETURNING 1' in statement
            columns = [column.strip().strip('"') for column in query.split('(', 1)[1].split(')', 1)[0].split(',')]
            row = {column: value.obj if isinstance(value, Jsonb) else value
                   for column, value in zip(columns, params, strict=True)}
            key = (row['issue_id'], row['version'])
            self.conn.attempt = row
            if key not in self.conn.issues:
                self.conn.issues[key] = deepcopy(row)
                self.one = (1,)
        elif statement.startswith('SELECT to_jsonb(issued_forecast)'):
            row = self.conn.issues.get(tuple(params))
            self.one = (deepcopy(row),) if row is not None else None
        elif statement.startswith('SELECT 1 FROM issued_forecast'):
            row = self.conn.issues.get(tuple(params[:2]))
            if row == self.conn.attempt:
                self.one = (1,)
        else:
            self.legacy.execute(statement, params)
            self.one = self.legacy.fetchone()
        return self

    def executemany(self, query, params):
        self.conn.sql.append(" ".join(query.split()))
        return self.legacy.executemany(query, params)

    def fetchall(self):
        return self.legacy.fetchall()

    def fetchone(self):
        return self.one


class _Connection:
    def __init__(self, *, l4_unavailable=False):
        self.legacy = _StrictConnection(rows=[_existing_row()], candidates=[_darshana_row()], phala_refs={41})
        self.sql = []
        self.issues = {}
        self.attempt = None
        self.l4_unavailable = l4_unavailable

    def cursor(self, **_kwargs):
        return _Cursor(self)

    def commit(self):
        pytest.fail('writer committed caller transaction')

    def rollback(self):
        pytest.fail('writer rolled back caller transaction')

    def close(self):
        pytest.fail('writer closed caller connection')


def _ctx(conn, values=None):
    config = {'chart_id': str(CHART)}
    if values is not None:
        config['registrar_inputs'] = values
    return SimpleNamespace(db_conn=conn, build_id=str(BUILD), config=config, dry_run=False)


def _protection_oracle(*, l4_unavailable=False):
    conn = _Connection(l4_unavailable=l4_unavailable)
    value = _input()
    ctx = _ctx(conn, (value,))  # no registrar_fixture_inputs dispatch flag
    writer = registrar.KaBhavishyaLekhaWriter()
    first = writer.run(ctx)
    before = deepcopy(conn.issues)
    retry = writer.run(ctx)
    assert (first.rows_inserted, retry.rows_inserted, retry.rows_skipped) == (1, 0, 1)
    ctx.config['registrar_inputs'] = (replace(value, point_functional='midpoint'),)
    with pytest.raises(ImmutableIssueConflict):
        writer.run(ctx)
    assert conn.issues == before
    assert conn.legacy.rows == conn.legacy.original_rows
    assert conn.legacy.phala_refs == {41}
    assert before[(ISSUE, 1)]['delivered_statement'] == value.statement
    assert not any('phala_anchors' in query or 'kala_bhavishya' in query for query in conn.sql)
    return conn


def test_default_path_protects_issued_forecast_via_k6_5a_contract():
    _protection_oracle()


def test_default_protection_survives_unavailable_l4_read():
    _protection_oracle(l4_unavailable=True)


def test_restoring_l4_guard_is_killed_by_default_protection_oracle(monkeypatch):
    original = registrar.KaBhavishyaLekhaWriter.run

    def restored_l4_guard(self, ctx):
        with ctx.db_conn.cursor() as cur:
            cur.execute("SELECT to_regclass('phala_anchors') IS NOT NULL AS present")
        return original(self, ctx)

    monkeypatch.setattr(registrar.KaBhavishyaLekhaWriter, 'run', restored_l4_guard)
    with pytest.raises(RuntimeError, match='L4 protective read unavailable'):
        _protection_oracle(l4_unavailable=True)


def test_default_without_delivery_leaves_served_and_issued_history_untouched():
    conn = _Connection(l4_unavailable=True)
    sentinel = {'delivered_statement': 'previously issued'}
    conn.issues[(ISSUE, 1)] = sentinel.copy()
    result = registrar.KaBhavishyaLekhaWriter().run(_ctx(conn))
    assert (result.rows_inserted, result.rows_updated) == (0, 0)
    assert result.notes == 'no_delivery_inputs'
    assert conn.issues == {(ISSUE, 1): sentinel}
    assert conn.legacy.rows == conn.legacy.original_rows
    assert conn.legacy.phala_refs == {41}
    assert conn.sql == []


def test_default_undelivered_candidate_does_not_create_issue():
    conn = _Connection(l4_unavailable=True)
    result = registrar.KaBhavishyaLekhaWriter().run(_ctx(conn, (replace(_input(), delivery=None),)))
    assert result.rows_inserted == 0
    assert result.notes == 'not_delivered'
    assert conn.issues == {}
    assert conn.sql == []


def test_default_dry_run_never_inserts_issue():
    conn = _Connection()
    ctx = _ctx(conn, (_input(),))
    ctx.dry_run = True
    result = registrar.KaBhavishyaLekhaWriter().run(ctx)
    assert result.rows_inserted == 0
    assert conn.issues == {}
