"""Archived review 1: serving uses immutable seal-bound indexed attestations."""
from services.gochara_kernel import scope_response as sr


class Rows:
    def __init__(self, data):
        self.data = data
    def fetchone(self):
        return self.data[0] if self.data else None
    def fetchall(self):
        return self.data


class Conn:
    def __init__(self, sealed=True, bad=False):
        self.sealed, self.bad, self.queries = sealed, bad, []
    def execute(self, sql, params=()):
        self.queries.append((sql, params))
        if 'ka_gochara_seal_approval' in sql:
            return Rows([(True,)] if self.sealed else [])
        if 'ka_gochara_search_path_pin' in sql:
            return Rows([(self.bad,)])
        if 'window_id::text' in sql:
            return Rows([('w1', 'objective', None, {'why': 'null'}, 'P3'),
                         ('w2', 'objective', 0.5, {'why': None}, 'P2')])
        raise AssertionError(sql)


def test_sealed_attestation_is_bound_to_manifest_seal_and_approval_without_replay():
    conn = Conn()
    assert sr._sealed_window_attestation(conn, 'chart', '5.0', 'marriage') is True
    assert len(conn.queries) == 2
    sql = '\n'.join(q for q, _ in conn.queries)
    assert 'ka_gochara_window_verification_violations' not in sql
    assert 's.manifest_id = p.manifest_id' in sql and 'a.manifest_id = p.manifest_id' in sql
    assert 'windows_stored' in sql and 'windows_unverified' in sql


def test_sealed_attestation_does_not_turn_missing_or_bad_evidence_green():
    assert sr._sealed_window_attestation(Conn(sealed=False), 'chart', '5.0', 'marriage') is None
    assert sr._sealed_window_attestation(Conn(bad=True), 'chart', '5.0', 'marriage') is False


def test_qualification_read_is_batched_and_preserves_null_and_vedha_scope():
    conn = Conn()
    out = sr._window_qualification(conn, 'chart', '5.0', [{'window_id': 'w1'}, {'window_id': 'w2'}], batch=True)
    assert len(conn.queries) == 1
    assert out[0]['objective_value'] is None and out[0]['qualification'] == {'why': 'null'}
    assert out[1]['objective_value'] == 0.5 and out[1]['vedha_moon_obstruction_scope'] == sr.VEDHA_MOON_SCOPE


def test_completeness_uses_sealed_attestation_without_replaying_contacts(monkeypatch):
    from datetime import datetime, timezone
    from types import SimpleNamespace
    lo = datetime(2025, 1, 1, tzinfo=timezone.utc)
    hi = datetime(2025, 2, 1, tzinfo=timezone.utc)
    vector = {'stored_scope': 'stored_non_moon'}
    horizon = SimpleNamespace(lower=lo, upper=hi)
    class Evidence:
        def execute(self, sql, params=()):
            if 'ka_gochara_window_verification_violations(%s' in sql:
                raise AssertionError('request replayed the generation')
            if 'ka_gochara_search_input_snapshot' in sql:
                return Rows([(vector, 'input')])
            if 'SELECT horizon, input_digest' in sql:
                return Rows([(horizon, 'input', 'inventory')])
            if 'completed_horizon' in sql:
                return Rows([(horizon,)])
            if 'ka_gochara_search_interval' in sql:
                return Rows([(0,)])
            if 'ka_gochara_search_inventory_verification' in sql:
                return Rows([(1,)])
            if 'to_regprocedure' in sql:
                return Rows([(True,)])
            raise AssertionError(sql)
    monkeypatch.setattr(sr, '_sealed_window_attestation', lambda *args: True)
    state, reasons, basis = sr._completeness(Evidence(), 'chart', '5.0', 'marriage',
                                            (lo, hi), (vector, 'published', None), sealed_read=True)
    assert state == sr.COMPLETE and reasons == []
    assert basis['verification_source'] == 'seal_bound_immutable_attestation'
