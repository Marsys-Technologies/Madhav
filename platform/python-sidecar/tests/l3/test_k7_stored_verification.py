"""K7-3: actual producer binds, not scores or caller labels, determine stored tiers."""
from datetime import date, datetime, timezone
from types import SimpleNamespace
import re

import pytest
from tests._insert_capture import insert_bindings
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT

class Capture:
    db = None
    def __init__(self, select_rows=()):
        self.rows = select_rows
        self.writes = []
    def cursor(self, **kwargs): return self
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def execute(self, sql, params=()):
        if str(sql).lstrip().startswith('INSERT'): self.writes.append((sql, tuple(params)))
        return self
    def executemany(self, sql, rows):
        self.writes.extend((sql, tuple(row)) for row in rows)
    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows


def bound_rows(capture, table):
    result = []
    for sql, params in capture.writes:
        match = re.search(r'INSERT INTO ' + table + r'\s*\((.*?)\)\s*VALUES\s*\((.*)\)', sql, re.S)
        if match:
            result.append(insert_bindings(sql, params))
            if Capture.db is not None:
                adapted = tuple('11111111-1111-4111-8111-111111111111' if value in ('chart','convention','manifest','build') else value for value in params)
                Capture.db.execute(sql, adapted)
    assert result, f'producer did not write {table}'
    if Capture.db is not None:
        stored = Capture.db.execute(f'SELECT verification_pass_status FROM {table}').fetchall()
        assert [row[0] for row in stored] == [UNVERIFIED_DEFAULT] * len(result)
    return result


def test_darshana_persists_single_despite_high_scores_and_roots():
    from pipeline.orchestrator.writers.ka_kala_darshana import KaKalaDarshanaWriter
    c = Capture([dict(convergence_id=1, signal_id=None, mode='A', peak_date=date(2026,10,9),
        window_start=date(2026,10,9), window_end=date(2026,10,10), convergence_score=.99,
        confidence_label='high', orb_strength=.99, rarity_years=10)])
    KaKalaDarshanaWriter().run(SimpleNamespace(db_conn=c, build_id='build', config={'chart_id':'chart'}))
    assert bound_rows(c, 'kala_darshana')[0].get('verification_pass_status') == UNVERIFIED_DEFAULT


def test_sangam_persists_single_for_every_mode_without_promoting_confidence():
    from pipeline.orchestrator.writers.ka_sangam import KaSangamWriter
    c = Capture()
    KaSangamWriter()._insert_windows(c, 'chart', [dict(mode=m, window_start=date(2026,10,9),
        window_end=date(2026,10,10), peak_date=date(2026,10,9), convergence_score=.99,
        orb_strength=.99, constituent_factors={}) for m in ('A','B','C','D')], 'near')
    assert [r.get('verification_pass_status') for r in bound_rows(c, 'kala_convergence')] == [UNVERIFIED_DEFAULT]*4


def test_contact_storage_overrides_a_supplied_verified_label():
    from services.gochara_kernel import ledger
    now = datetime(2026,10,9,tzinfo=timezone.utc)
    ep = dict(ephemeris_backend={'fixture':True}, independence_group='fixture', target_resolution_state='resolved', bracket_seconds=1, tolerance_arcsec=1, branch='direct', orb_max_deg=1, orb_source='fixture', epistemic_class='computed', completeness_state='complete', operator_role='scored', precision_regime='fixture', time_basis='utc', comparable_with='fixture', body='Saturn', relation='conjunction', target_type='natal', target_ref='fixture',
        t_in=now,t_exact=now,t_out=now, verification_pass_status='two_pass_verified')
    row = ledger._normalize_episode(ep,'chart','4.1','convention','v1','manifest','build')
    c = Capture()
    ledger._insert_contact_rows(c,[row])
    assert bound_rows(c, 'kala_gochara_contacts')[0].get('verification_pass_status') == UNVERIFIED_DEFAULT


def test_jivana_persists_single_for_chapters_without_source_verification():
    from pipeline.orchestrator.writers.ka_jivana_parva import KaJivanaParvaWriter
    c = Capture([dict(lord_graha='Saturn', start_date=date(2020,1,1), end_date=date(2030,1,1),level_n=1)])
    KaJivanaParvaWriter().run(SimpleNamespace(db_conn=c, build_id='build', config={'chart_id':'chart', 'birth_params':{'datetime_iso':'2000-01-01T00:00:00Z'}}))
    assert bound_rows(c, 'kala_jivana_parva')[0].get('verification_pass_status') == UNVERIFIED_DEFAULT


def test_bhavishya_persists_single_beside_probability_tier():
    from tests.l3.test_bhavishya_p0_safety import _StrictConnection, _darshana_row, _run
    from pipeline.orchestrator.writers.ka_bhavishya_lekha import KaBhavishyaLekhaWriter
    c = _StrictConnection(candidates=[_darshana_row(convergence_id=1)])
    _run(c)
    insert = next((sql,params) for sql,params in c.sql if sql.startswith('INSERT INTO kala_bhavishya'))
    cap = Capture()
    cap.writes = [(insert[0],insert[1][0])]
    assert bound_rows(cap, 'kala_bhavishya')[0].get('verification_pass_status') == UNVERIFIED_DEFAULT


def test_obstruction_fixture_storage_does_not_invent_a_verified_detector(monkeypatch):
    from services.ka_vighnakara import storage
    from tests.l3.ka_vighnakara.test_negative_space import finding
    class Binding(Capture):
        def execute(self, sql, params=()):
            self.head = 'head' in sql
            return self
        def fetchone(self):
            return None if self.head else ('00000000-0000-0000-0000-000000000392','candidate:fixture','building',{'fixture':True})
    written=[]
    monkeypatch.setattr(storage,'replace_candidate_partition', lambda c,t,ch,g,p,rows: written.extend(rows) or len(rows))
    storage.write_fixture_candidate(SimpleNamespace(dry_run=False,db_conn=Binding(),build_id='build',config={'chart_id':'00000000-0000-0000-0000-000000000392'}), [finding()])
    assert written[0].get('verification_pass_status') == UNVERIFIED_DEFAULT
    if Capture.db is not None:
        from psycopg import sql
        row = written[0]
        query = sql.SQL('INSERT INTO kala_obstruction ({}) VALUES ({})').format(
            sql.SQL(',').join(map(sql.Identifier,row)), sql.SQL(',').join(sql.Placeholder() for _ in row))
        Capture.db.execute(query,list(row.values()))
        assert Capture.db.execute('SELECT verification_pass_status FROM kala_obstruction').fetchone() == (UNVERIFIED_DEFAULT,)


def test_additive_migration_replays_keeps_old_rows_null_and_refuses_unknown_status():
    import os
    from pathlib import Path
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
    from brahmagyan.verification_vocab import ALL_STATUSES
    dsn = os.environ.get('KALA_ADMIN_DSN')
    if not dsn:
        pytest.skip('requires explicitly enabled disposable SQL job')
    info = conninfo_to_dict(dsn)
    assert (info['host'], info['port'], info['dbname']) == ('127.0.0.1','55433','ky_cx_k73')
    path = Path(__file__).parents[3]/'supabase/migrations/1376_k7_stage_verification_status.sql'
    assert path.exists(), 'additive stored-tier migration missing'
    body = path.read_text().replace('BEGIN;', '').replace('COMMIT;', '').replace('public.', 'pg_temp.')
    tables = ('kala_darshana','kala_obstruction','kala_gochara_contacts','kala_bhavishya','kala_convergence','kala_jivana_parva')
    with psycopg.connect(dsn) as conn:
        for table in tables:
            conn.execute(f'CREATE TEMP TABLE {table} (id text)')
            conn.execute(f"INSERT INTO {table} VALUES ('old')")
        conn.execute(body)
        conn.execute(body)
        for table in tables:
            assert conn.execute(f'SELECT verification_pass_status FROM {table}').fetchone() == (None,)
            for status in ALL_STATUSES:
                conn.execute(f'INSERT INTO {table} (id,verification_pass_status) VALUES (%s,%s)', ('new',status))
            with pytest.raises(psycopg.errors.CheckViolation), conn.transaction():
                conn.execute(f'INSERT INTO {table} (id,verification_pass_status) VALUES (%s,%s)', ('bad','confirmed'))
        conn.rollback()


@pytest.fixture(autouse=True)
def persisted_producer_sql(monkeypatch):
    """Run captured producer INSERTs on actual schema types and rolled-back TEMP tables."""
    import os
    from pathlib import Path
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
    dsn = os.environ.get('KALA_ADMIN_DSN')
    if not dsn:
        yield
        return
    info = conninfo_to_dict(dsn)
    assert (info['host'],info['port'],info['dbname']) == ('127.0.0.1','55433','ky_cx_k73')
    tables=('kala_darshana','kala_obstruction','kala_gochara_contacts','kala_bhavishya','kala_convergence','kala_jivana_parva')
    path=Path(__file__).parents[3]/'supabase/migrations/1376_k7_stage_verification_status.sql'
    with psycopg.connect(dsn) as conn:
        for table in tables:
            conn.execute(f'CREATE TEMP TABLE {table} (LIKE public.{table} INCLUDING DEFAULTS)')
            id_column = 'convergence_id' if table == 'kala_convergence' else 'id'
            if table != 'kala_gochara_contacts':
                conn.execute(f'ALTER TABLE {table} ALTER COLUMN {id_column} SET DEFAULT 1')
        # Apply the actual migration to the cloned schemas. It has no data backfill.
        if path.exists():
            conn.execute(path.read_text().replace('BEGIN;','').replace('COMMIT;','').replace('public.','pg_temp.'))
        monkeypatch.setattr(Capture,'db',conn)
        yield
        conn.rollback()


def test_legacy_obstructions_store_single_for_window_and_dasha_anchor(monkeypatch):
    from pipeline.orchestrator.writers import ka_vighnakara as mod
    writer = mod._LegacyKaVighnakaraWriter()
    for method in ('_fetch_natal_lagna_lon','_fetch_natal_moon_lon'):
        monkeypatch.setattr(writer, method, lambda *args: None)
    monkeypatch.setattr(writer,'_fetch_combustion_orbs',lambda *args: {})
    monkeypatch.setattr(writer,'_resolve_native_location',lambda *args: {})
    monkeypatch.setattr(writer,'_dasha_anchor_peaks',lambda *args: [(date(2026,10,9),None)])
    monkeypatch.setattr(mod,'_detect_all',lambda **kwargs: [dict(obstruction_type='malefic_transit',severity='severe',severity_score=.99,override_score=.99,detail={})])
    c = Capture([(1,None,'A',date(2026,10,9),.99,.99,date(2026,10,9),date(2026,10,10))])
    # Storage assembly only: the real ephemeris guard is exercised in its own suite.
    mod._LegacyKaVighnakaraWriter.run.__wrapped__(writer,SimpleNamespace(db_conn=c,config={'chart_id':'chart'}))
    assert [r['verification_pass_status'] for r in bound_rows(c,'kala_obstruction')] == [UNVERIFIED_DEFAULT]*2


def test_bhavishya_changed_match_keeps_id_and_outcome_and_stores_single():
    from tests.l3.test_bhavishya_p0_safety import _StrictConnection, _darshana_row, _existing_row, _run
    existing = _existing_row()
    candidate = _darshana_row()
    candidate['effective_score'] = .55
    c = _StrictConnection(rows=[existing],candidates=[candidate])
    _run(c)
    assert c.rows[0]['id'] == existing['id']
    assert c.rows[0]['outcome_recorded'] == existing['outcome_recorded']
    assert c.rows[0]['outcome_notes'] == existing['outcome_notes']
    assert c.rows[0]['verification_pass_status'] == UNVERIFIED_DEFAULT
