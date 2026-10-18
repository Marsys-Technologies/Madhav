"""The supplied K4 endpoint exception must not admit another DB or server."""
from types import SimpleNamespace

import pytest

from tests.l3._disposable_db_guard import RefusedError
from tests.l3.kala_db.ka_sangam import conftest as fixture

DSN = 'postgresql://fixture@127.0.0.1:55433/ky_cx_k4'


@pytest.fixture(params=[None, 'false', 'true'], ids=['local-unset', 'local-false', 'github-actions'])
def github_actions(monkeypatch, request):
    if request.param is None:
        monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
    else:
        monkeypatch.setenv('GITHUB_ACTIONS', request.param)


class Probe:
    def __init__(self, identity):
        self.identity = identity

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql):
        return SimpleNamespace(fetchone=lambda: self.identity)


@pytest.mark.parametrize('identity', [
    ('ky_cx_k4', '172.17.0.3/32'),
    ('ky_cx_k4', '127.0.0.1/32'),
])
def test_exact_provided_database_is_admitted(monkeypatch, github_actions, identity):
    monkeypatch.setenv('KALA_ADMIN_DSN', DSN)
    monkeypatch.setattr(fixture.psycopg, 'connect', lambda *args, **kwargs: Probe(identity))
    connection = fixture.kala_db_dsn.__wrapped__(None)
    assert next(connection) == DSN
    connection.close()


@pytest.mark.parametrize('dsn,identity', [
    (DSN.replace('127.0.0.1', 'remote.invalid'), ('ky_cx_k4', '172.17.0.3/32')),
    (DSN.replace('55433', '55434'), ('ky_cx_k4', '172.17.0.3/32')),
    (DSN + '?dbname=other', ('ky_cx_k4', '172.17.0.3/32')),
    (DSN, ('other_database', '172.17.0.3/32')),
    (DSN, ('ky_cx_k4', '172.17.0.4/32')),
    (DSN, ('ky_cx_k4', '8.8.8.8/32')),
])
def test_wrong_provided_identity_is_refused(monkeypatch, github_actions, dsn, identity):
    monkeypatch.setenv('KALA_ADMIN_DSN', dsn)
    monkeypatch.setattr(fixture.psycopg, 'connect', lambda *args, **kwargs: Probe(identity))
    request = SimpleNamespace(getfixturevalue=lambda name: next(fixture.created_database.__wrapped__()))
    with pytest.raises((RefusedError, RuntimeError)):
        next(fixture.kala_db_dsn.__wrapped__(request))
