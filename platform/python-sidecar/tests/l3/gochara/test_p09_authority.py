"""P09 authority operation units; DB constraint and real-seal tests live alongside."""
from pathlib import Path
import pytest
from services.gochara_kernel import authority_head as ah


class Result:
    def __init__(self, row):
        self.row = row
    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, head='3.0', sealed=True, status='published', test_slice=False):
        self.head, self.sealed, self.status, self.test_slice = head, sealed, status, test_slice
        self.statements = []
    def execute(self, sql, params=()):
        self.statements.append(sql)
        if 'ka_gochara_lock_chart' in sql:
            return Result((None,))
        if 'SELECT authoritative_generation' in sql:
            return Result((self.head,))
        if 'kala_gochara_publication' in sql:
            return Result((self.status, self.test_slice, self.sealed))
        if 'UPDATE public.kala_gochara_authority' in sql:
            self.head = params[0]
            return Result((self.head,))
        raise AssertionError(sql)


def test_flip_and_rollback_compare_head_and_retain_previous_generation():
    conn = Connection()
    flip = ah.publish_head(conn, 'chart', generation='5.0', expected_head='3.0',
                           evidence_ref='receipt-1', operator='operator')
    assert flip == {'chart_id': 'chart', 'previous_head': '3.0', 'head': '5.0', 'evidence_ref': 'receipt-1'}
    back = ah.rollback_head(conn, 'chart', generation=flip['previous_head'], expected_head='5.0',
                            evidence_ref='receipt-2', operator='operator')
    assert back['head'] == '3.0'
    assert all('DELETE' not in s and 'TRUNCATE' not in s for s in conn.statements)
    assert conn.statements[0].startswith('SELECT public.ka_gochara_lock_chart')


@pytest.mark.parametrize('kwargs', [dict(sealed=False), dict(status='candidate'), dict(test_slice=True)])
def test_publish_refuses_unsealed_unpublished_and_test_slice(kwargs):
    conn = Connection(**kwargs)
    with pytest.raises(ah.AuthorityRefused):
        ah.publish_head(conn, 'chart', generation='5.0', expected_head='3.0', evidence_ref='receipt', operator='op')
    assert conn.head == '3.0' and not any(s.startswith('UPDATE ') for s in conn.statements)


def test_stale_expected_head_never_overwrites_another_flip():
    conn = Connection(head='4.1')
    with pytest.raises(ah.AuthorityRefused, match='head_changed'):
        ah.publish_head(conn, 'chart', generation='5.0', expected_head='3.0', evidence_ref='receipt', operator='op')
    assert not any(s.startswith('UPDATE ') for s in conn.statements)


def test_operation_requires_evidence_and_does_not_own_transaction():
    conn = Connection()
    with pytest.raises(ah.AuthorityRefused):
        ah.publish_head(conn, 'chart', generation='5.0', expected_head='3.0', evidence_ref='', operator='op')
    assert conn.statements == []
    text = Path(ah.__file__).read_text()
    assert '.commit(' not in text and '.close(' not in text


def test_authority_migration_is_new_protected_and_not_a_row_flip():
    root = Path(__file__).resolve().parents[5]
    migration = next(root.glob('platform/migrations/*_gochara_sealed_authority.sql'))
    sql = migration.read_text()
    assert int(migration.name.split('_')[0]) > 1236
    assert migration.name in (root / 'platform/scripts/kala_protected_migrations.txt').read_text()
    assert 'DROP CONSTRAINT kga_governed_generation_refused_ck' in sql
    assert 'CREATE TRIGGER' in sql and 'ENABLE ALWAYS TRIGGER' in sql
    assert 's.manifest_id = p.manifest_id' in sql and "p.status = 'published'" in sql
    assert "'test_slice'" in sql
    assert 'UPDATE public.kala_gochara_authority SET' not in sql


def test_rollback_restores_manifestless_legacy_head_from_recorded_previous_generation():
    class PreLedger(Connection):
        def execute(self, sql, params=()):
            if 'kala_gochara_publication' in sql:
                return Result(None)
            return super().execute(sql, params)
    conn = PreLedger(head='5.0')
    receipt = ah.rollback_head(conn, 'chart', generation='3.0', expected_head='5.0', evidence_ref='original-flip-receipt', operator='op')
    assert receipt['head'] == '3.0'
    assert not any('DELETE' in s for s in conn.statements)
