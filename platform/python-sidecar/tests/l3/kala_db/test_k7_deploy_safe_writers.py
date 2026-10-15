"""Execute emitted producer SQL on real legacy and 1376-migrated TEMP tables.

Input SELECTs remain fixture-controlled; capability probes and output DML use
PostgreSQL. Reuse the production column/CHECK DDL, removing external FKs only.
The dedicated Kāla DB CI job collects this module in both schema states.
"""
from pathlib import Path
import re

import psycopg
import pytest

from tests.l3 import test_k7_stored_verification as producers

PLATFORM = Path(__file__).resolve().parents[4]
TABLES = ('kala_darshana', 'kala_obstruction', 'kala_gochara_contacts',
          'kala_bhavishya', 'kala_convergence', 'kala_jivana_parva')
ORACLES = (
    producers.test_darshana_persists_single_despite_high_scores_and_roots,
    producers.test_sangam_persists_single_for_every_mode_without_promoting_confidence,
    producers.test_contact_storage_overrides_a_supplied_verified_label,
    producers.test_jivana_persists_single_for_chapters_without_source_verification,
    producers.test_bhavishya_persists_single_beside_probability_tier,
    producers.test_legacy_obstructions_store_single_for_window_and_dasha_anchor,
)


def without_external_fks(statement):
    return re.sub(r'REFERENCES \w+\(\w+\)(?: ON DELETE (?:CASCADE|SET NULL))?', '', statement)


def create_table(conn, table, path):
    statement = re.search(
        rf'CREATE (?:TEMP )?TABLE(?: IF NOT EXISTS)? (?:public\.)?{table} \([\s\S]*?\n\);',
        path.read_text(),
    )
    assert statement, f'missing production table definition: {path}:{table}'
    ddl = re.sub(r'CREATE (?:TEMP )?TABLE(?: IF NOT EXISTS)? (?:public\.)?',
                 'CREATE TEMP TABLE ', statement[0], count=1)
    conn.execute(without_external_fks(ddl))


def apply_table_alters(conn, table, path, columns_only=False):
    statements = re.findall(rf'^ALTER TABLE (?:public\.)?{table}\b[^;]*;', path.read_text(), re.M)
    assert statements, f'missing table alterations: {path}:{table}'
    for statement in statements:
        if not columns_only or 'ADD COLUMN' in statement:
            conn.execute(without_external_fks(statement))


def apply_temp_verification(conn):
    # current_schema() remains public when pg_temp is an implicit lookup
    # namespace. Bind 1376 explicitly to these session-local fixture tables.
    body = (PLATFORM / 'supabase/migrations/1376_k7_stage_verification_status.sql').read_text()
    conn.execute(body.replace('BEGIN;', '').replace('COMMIT;', '').replace('public.', 'pg_temp.'))


def legacy_schema(conn):
    migrations = PLATFORM / 'supabase/migrations'
    create_table(conn, 'kala_convergence', migrations / '0001_brahma_baseline.sql')
    conn.execute('ALTER TABLE kala_convergence ALTER COLUMN convergence_id SET DEFAULT 1')
    for name in ('244_l3_ka_sangam.sql', '340_kala_convergence_horizon_tier.sql',
                 '361_kala_convergence_domain.sql', '409_kala_convergence_relative_tier.sql'):
        apply_table_alters(conn, 'kala_convergence', migrations / name)
    for table, name in (
        ('kala_darshana', '247_l3_ka_kala_darshana.sql'),
        ('kala_bhavishya', '249_l3_ka_bhavishya_lekha.sql'),
        ('kala_jivana_parva', '248_l3_ka_jivana_parva.sql'),
    ):
        create_table(conn, table, migrations / name)
    apply_table_alters(conn, 'kala_jivana_parva', PLATFORM / 'migrations/679_nirmana_l3_f_parva_1_level_column.sql', columns_only=True)
    create_table(conn, 'kala_obstruction', Path(__file__).with_name('e2e') / 'legacy_schema.sql')
    create_table(conn, 'kala_gochara_contacts', PLATFORM / 'migrations/1081_nirmana_l3_gochara_ledger_coverage_publication.sql')
    apply_table_alters(conn, 'kala_gochara_contacts', PLATFORM / 'migrations/1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis.sql', columns_only=True)


@pytest.mark.parametrize('has_tier', [False, True], ids=['before-1376', 'after-1376'])
@pytest.mark.parametrize('oracle', ORACLES, ids=lambda oracle: oracle.__name__)
def test_producer_sql_is_deploy_safe(kala_db_dsn, monkeypatch, has_tier, oracle):
    from tests.l3.test_bhavishya_p0_safety import _StrictConnection
    with psycopg.connect(kala_db_dsn) as conn:
        legacy_schema(conn)
        if has_tier:
            apply_temp_verification(conn)
        monkeypatch.setattr(producers.Capture, 'db', conn)
        monkeypatch.setattr(producers.Capture, 'has_tier', has_tier)
        monkeypatch.setattr(_StrictConnection, 'has_tier', has_tier)
        monkeypatch.setattr(_StrictConnection, 'db', conn)
        if 'monkeypatch' in oracle.__code__.co_varnames[:oracle.__code__.co_argcount]:
            oracle(monkeypatch)
        else:
            oracle()
        conn.rollback()


@pytest.mark.parametrize('has_tier', [False, True], ids=['before-1376', 'after-1376'])
def test_bhavishya_update_is_deploy_safe(kala_db_dsn, monkeypatch, has_tier):
    from tests.l3.test_bhavishya_p0_safety import _StrictConnection, _existing_row, _darshana_row, _run
    from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT
    with psycopg.connect(kala_db_dsn) as conn:
        legacy_schema(conn)
        if has_tier:
            apply_temp_verification(conn)
        monkeypatch.setattr(_StrictConnection, 'has_tier', has_tier)
        monkeypatch.setattr(_StrictConnection, 'db', conn)
        baseline = _StrictConnection(candidates=[_darshana_row(convergence_id=1)])
        _run(baseline)
        sql, params = next((sql, params) for sql, params in baseline.sql if sql.startswith('INSERT INTO kala_bhavishya'))
        conn.execute(sql, params[0])
        row_id = conn.execute('SELECT id FROM kala_bhavishya').fetchone()[0]
        existing = _existing_row(row_id=row_id)
        existing['convergence_id'] = 1
        candidate = _darshana_row(convergence_id=1)
        candidate['effective_score'] = .55
        changed = _StrictConnection(rows=[existing], candidates=[candidate])
        _run(changed)
        sql, params = next((sql, params) for sql, params in changed.sql if sql.startswith('UPDATE kala_bhavishya'))
        conn.execute(sql, params[0])
        stored = conn.execute('SELECT to_jsonb(b) FROM kala_bhavishya b').fetchone()[0]
        assert stored['id'] == row_id
        assert stored['effective_score'] == .55
        assert stored['outcome_recorded'] is False
        assert stored['outcome_notes'] is None
        assert ('verification_pass_status' in stored) == has_tier
        if has_tier:
            assert stored['verification_pass_status'] == UNVERIFIED_DEFAULT
        conn.rollback()
