"""P09 offline acceptance: admission, archived review counterexamples and rollback.

The SQL suites retain the real migration/seal/grants oracles. These stubs test the
serving decisions without opening any database or replacing stored chart facts.
"""
from datetime import datetime, timezone
from types import SimpleNamespace
import json

import pytest

from services.gochara_kernel import serving_reader as rd
from routers import gochara_v5 as route

UTC = timezone.utc
LO = datetime(2025, 1, 1, tzinfo=UTC)
HI = datetime(2025, 3, 1, tzinfo=UTC)
CHART = '00000000-0000-0000-0000-000000000001'
MANIFEST = '00000000-0000-0000-0000-000000000002'


@pytest.fixture
def reader(monkeypatch):
    state = SimpleNamespace(status='published', vector={'stored_scope': 'stored_non_moon',
                            'result_policy': 'all_null_candidate/1'}, seal=MANIFEST,
                            classes=['marriage'], coverage='complete_within_scope', bounds_bad=False)
    monkeypatch.setattr(rd, '_require_schema', lambda conn: None)
    monkeypatch.setattr(rd, '_load_manifest', lambda *args: (MANIFEST, state.status, LO, HI, True, False, state.vector))
    monkeypatch.setattr(rd, '_load_seal', lambda *args: None if state.seal is None else
                        {'manifest_id': state.seal, 'sealed_at': LO.isoformat()})
    monkeypatch.setattr(rd, '_stored_bounds_problem', lambda *args: state.bounds_bad)
    def rows(conn, sql, params=()):
        if 'GROUP BY w.event_class' in sql:
            return []
        if 'SELECT event_class' in sql:
            return [(c,) for c in state.classes]
        if 'SELECT w.window_id' in sql:
            return []
        raise AssertionError(sql)
    monkeypatch.setattr(rd, '_all', rows)
    monkeypatch.setattr(rd, '_near_miss', lambda *args: {'near_miss_layer': 'absent'})
    def coverage(conn, **kwargs):
        result = {'completeness': state.coverage, 'windows': []}
        if state.coverage == 'refused':
            result['refusal'] = 'stored_scope_missing'
            result['refusal_detail'] = 'manifest scope missing'
        return result
    monkeypatch.setattr(rd.sr, 'coverage_response', coverage)
    return state


@pytest.mark.parametrize('change,code', [
    ({'status': 'candidate'}, 'not_published'),
    ({'status': 'rolled_back'}, 'not_published'),
    ({'seal': None}, 'not_sealed'),
    ({'seal': 'another-manifest'}, 'not_sealed'),
    ({'vector': {'stored_scope': 'test_slice'}}, 'test_slice_candidate'),
    ({'vector': {'stored_scope': 'stored_non_moon', 'test_slice': False}}, 'test_slice_candidate'),
])
def test_admission_refuses_unpublished_unsealed_mismatched_and_test_slice(reader, change, code):
    for key, value in change.items():
        setattr(reader, key, value)
    env = rd.read_v5(object(), CHART, '5.0')
    assert env['refusal']['code'] == code
    assert env['windows'] is None and env['classes'] is None and env['counts'] is None


def test_review_closed_window_bounds_are_refused_before_matching(reader):
    reader.bounds_bad = True
    result = rd.read_v5(object(), CHART, '5.0', at_instant=HI)
    # Check bounds on an in-horizon request; out-of-horizon admission takes priority.
    result = rd.read_v5(object(), CHART, '5.0', at_instant=LO)
    assert result['refusal']['code'] == 'stored_window_bounds_incompatible'
    assert result['windows'] is None


def test_review_no_class_evidence_is_named_refusal(reader):
    reader.classes = []
    result = rd.read_v5(object(), CHART, '5.0')
    assert result['refusal']['code'] == 'class_evidence_unavailable'
    assert result['windows'] is None


def test_review_constructor_refusal_reaches_top_level(reader):
    reader.coverage = 'refused'
    result = rd.read_v5(object(), CHART, '5.0')
    assert result['refusal']['code'] == 'stored_scope_missing'
    assert result['classes'] is None and result['windows'] is None
    assert result['refusal']['class_details'][0]['event_class'] == 'marriage'


def test_review_disclosure_does_not_claim_unverified_contacts(reader):
    reader.coverage = 'unverified'
    result = rd.read_v5(object(), CHART, '5.0')
    assert result['classes'][0]['completeness'] == 'unverified'
    assert 'verified contact intervals' not in result['numbers_disclosure']


def test_review_connection_configuration_failure_closes_handle(monkeypatch):
    calls = []
    class Broken:
        @property
        def read_only(self):
            return False
        @read_only.setter
        def read_only(self, value):
            raise RuntimeError('configuration failed')
        def rollback(self):
            calls.append('rollback')
        def close(self):
            calls.append('close')
    monkeypatch.setattr(route, '_db_url', lambda: 'stub')
    monkeypatch.setattr(route.psycopg, 'connect', lambda *args, **kwargs: Broken())
    with pytest.raises(RuntimeError, match='configuration failed'):
        route._connect()
    assert calls == ['rollback', 'close']


def test_default_reader_flip_rollback_restores_exact_legacy_bytes(reader, monkeypatch):
    state = {'head': '3.0'}
    legacy_bytes = b'{"generation":"3.0","score":null,"windows":[]}'
    legacy_calls = []
    monkeypatch.setattr(rd, '_first', lambda *args: (state['head'],))
    def legacy(conn, chart_id, generation, **kwargs):
        legacy_calls.append((chart_id, generation))
        return legacy_bytes
    conn = object()
    before = rd.read_authoritative(conn, CHART, legacy_reader=legacy)
    state['head'] = '5.0'
    served = rd.read_authoritative(conn, CHART, legacy_reader=legacy)
    assert served['generation'] == '5.0' and served['refusal'] is None
    assert json.dumps(served)
    state['head'] = '3.0'
    after = rd.read_authoritative(conn, CHART, legacy_reader=legacy)
    assert before == after == legacy_bytes
    assert legacy_calls == [(CHART, '3.0'), (CHART, '3.0')]


def test_default_reader_never_falls_back_from_unsealed_governed_head(reader, monkeypatch):
    reader.seal = None
    monkeypatch.setattr(rd, '_first', lambda *args: ('5.0',))
    def forbidden(*args, **kwargs):
        pytest.fail('governed refusal fell back to legacy')
    result = rd.read_authoritative(object(), CHART, legacy_reader=forbidden)
    assert result['refusal']['code'] == 'not_sealed'


def test_absent_authority_is_unknown_without_a_legacy_default(monkeypatch):
    monkeypatch.setattr(rd, '_first', lambda *args: None)
    def forbidden(*args, **kwargs):
        pytest.fail('absent authority invented a generation')
    result = rd.read_authoritative(object(), CHART, legacy_reader=forbidden)
    assert result['refusal']['code'] == 'authority_not_published'


@pytest.mark.parametrize('broken,detail', [
    ('type', 'column_types'), ('key', 'keys'), ('orphan', 'rows'), ('score', 'rows'), ('standing', 'rows')])
def test_review_near_miss_mismatches_are_named_and_do_not_emit_an_array(monkeypatch, broken, detail):
    schema = rd.NEAR_MISS_SCHEMA
    occ, obj = schema['occurrence_table'], schema['object_table']
    def all_rows(conn, sql, params=()):
        if 'data_type' in sql:
            return [(table, column, 'text' if broken == 'type' and column == 'proximity' else typ)
                    for table, cols in rd.NEAR_MISS_COLUMN_TYPES.items() for column, typ in cols.items()]
        return [(table, col) for table, cols in [(occ, schema['occurrence_columns']), (obj, schema['object_columns'])]
                for col in cols.values()]
    def first(conn, sql, params=()):
        if 'pg_index' in sql:
            return (broken != 'key',)
        if 'to_regclass' in sql:
            return (True, True)
        if 'IS DISTINCT FROM' in sql:
            return (broken in ('orphan', 'score', 'standing'),)
        raise AssertionError(sql)
    monkeypatch.setattr(rd, '_all', all_rows)
    monkeypatch.setattr(rd, '_first', first)
    block = rd._near_miss(object(), CHART, '5.0', {'near_miss_layer_version': '1'}, None, LO, HI, 5)
    assert block['near_miss_layer'] == 'schema_mismatch'
    assert 'near_miss_intervals' not in block
    assert detail in block['near_miss_layer_detail']


def test_absent_authority_refusal_keeps_request_instants_json_serializable(monkeypatch):
    monkeypatch.setattr(rd, '_first', lambda *args: None)
    result = rd.read_authoritative(object(), CHART, legacy_reader=lambda *args: pytest.fail('invented legacy head'),
                                   date_from=LO, date_to=HI, event_classes=['marriage'])
    assert json.dumps(result)
    assert result['requested']['date_from'] == LO.isoformat()
    assert result['requested']['date_to'] == HI.isoformat()
    assert result['refusal']['code'] == 'authority_not_published'
