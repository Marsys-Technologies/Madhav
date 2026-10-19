"""madhav-6d (2)(b)/(4), job A/B; CLAUDE §N.8 and §N.7.6.

Only synthetic rows in the suite-owned DB. No classical calculation is claimed.
Each oracle measures a distinct preparation claim, not captured current output.
"""
import json

import psycopg
from psycopg import sql
import pytest

from services.gochara_kernel import dasha_read as reader
from services.gochara_kernel import inventory_verifier as verifier

CHART = '482012f1-710e-4a25-994a-93821f5871aa'
BUILD = '22222222-2222-4222-8222-222222222222'  # synthetic, never canonical data
MANIFEST = 'a' * 64


def adapter():
    from services.gochara_kernel import rehearsal_settlement
    return rehearsal_settlement


@pytest.fixture(autouse=True)
def job_scratch(tmp_path, monkeypatch):
    """Hermetic rehearsal ownership: JOB_SCRATCH exists only for the harness, so
    every test supplies its own absolute scratch rather than inheriting one."""
    scratch = tmp_path / 'synthetic-settlement-job'
    scratch.mkdir()
    monkeypatch.setenv('JOB_SCRATCH', str(scratch))
    return scratch


@pytest.fixture
def restored(isolated_kala_db_dsn, job_scratch):
    """Existing guarded fixture alone creates/drops the DB; tag its job custody."""
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as conn:
        name = conn.info.dbname
        conn.execute(sql.SQL('COMMENT ON DATABASE {} IS {}').format(
            sql.Identifier(name), sql.Literal('ky.job=' + job_scratch.name)))
        conn.execute('''
            DROP SCHEMA public CASCADE; CREATE SCHEMA public;
            CREATE TABLE chart_dashas (
                dasha_row_id uuid, chart_id uuid, system_id text, ayanamsha_id text,
                level_n integer, parent_row_id uuid, lord_graha text,
                start_iso timestamptz, end_iso timestamptz, build_id uuid,
                verification_pass_status text, kp_sublevel text);
            CREATE TABLE profiles(id integer PRIMARY KEY);
            CREATE TABLE charts(id integer PRIMARY KEY, client_id integer);
        ''')
        conn.execute('''INSERT INTO chart_dashas VALUES
            ('11111111-1111-4111-8111-111111111111',%s,'vimshottari','lahiri_chitrapaksha',
             1,NULL,'Saturn','2026-01-01Z','2026-01-09Z',%s,'two_pass_verified')''', (CHART, BUILD))
        yield conn
        conn.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')


def wrap(conn, **kw):
    return adapter().synthetic_settlement_connection(
        conn, chart_id=CHART, manifest_sha256=MANIFEST, receipt=kw.pop('receipt', {}), **kw)


def test_synthetic_binding_reaches_real_reader_and_independent_verifier(restored, isolated_kala_db_dsn):
    """A: one restored build, explicit synthetic provenance and retained receipt."""
    receipt = {}
    conn = wrap(restored, enabled=True, receipt=receipt)
    from types import SimpleNamespace
    # Exercise the harness adapter with the real snapshot operand reader; no
    # upstream writer or astronomical output is fabricated by this transport test.
    ctx, step = SimpleNamespace(db_conn=conn), SimpleNamespace(key='snapshot')
    assert receipt['snapshot_settlement_qualification'] is None
    idle = SimpleNamespace(run_substep=lambda ctx, step: None)
    conn.run_substep(idle, ctx, step)
    assert receipt['snapshot_settlement_qualification'] is None  # no-op cannot earn it
    snapshot = SimpleNamespace(run_substep=lambda ctx, step: reader.load_pinned_vimshottari(ctx.db_conn, CHART))
    rows, contract = conn.run_substep(snapshot, ctx, step)
    assert receipt['snapshot_stage_outcome'] == 'completed'
    assert [str(r['build_id']) for r in rows] == [BUILD]
    assert contract['build_id'] == BUILD
    assert contract['synthetic'] is True
    assert 'SYNTHETIC-REHEARSAL-ONLY' in contract['basis']
    record = receipt['dasha_settlement']
    assert record['synthetic'] is True
    assert record['provenance']['source'] == 'SYNTHETIC-REHEARSAL-ONLY'
    assert record['provenance']['manifest_sha256'] == MANIFEST
    assert record['run_id'] == BUILD and record['chart_id'] == CHART
    assert receipt['snapshot_settlement_qualification'] == 'snapshot stage rehearsed on synthetic settlement'
    assert receipt['production_acceptance'] is False
    # A later failed attempt keeps the synthetic qualification and honest failure.
    def fails_after_read(ctx, step):
        reader.load_pinned_vimshottari(ctx.db_conn, CHART)
        raise RuntimeError('synthetic fixture stage failure')
    with pytest.raises(RuntimeError, match='fixture stage failure'):
        conn.run_substep(SimpleNamespace(run_substep=fails_after_read), ctx, step)
    assert receipt['snapshot_stage_outcome'] == 'failed'
    # Exercise the verifier's own SQL, not the reader's population check.
    restored.execute('''CREATE TABLE ka_gochara_search_input_snapshot
        (chart_id uuid,generation text,consumed_fact_ids text[],consumed_dasha_row_ids uuid[]);
        CREATE TABLE ka_gochara_search_inventory(chart_id uuid,generation text,horizon tstzrange)''')
    restored.execute('INSERT INTO ka_gochara_search_input_snapshot VALUES (%s,\'5.0\',ARRAY[]::text[],ARRAY[%s::uuid])',
                     (CHART, rows[0]['dasha_row_id']))
    restored.execute("INSERT INTO ka_gochara_search_inventory VALUES (%s,'5.0',tstzrange('2026-01-01Z','2026-01-09Z'))", (CHART,))
    verified = verifier.validate_consumed_dasha_population(conn, chart_id=CHART, generation='5.0')
    assert verified == dict(consumed=1, pinned_overlapping=1, synthetic_settlement=True, production_acceptance=False)
    # A second connection to the SAME throwaway DB has no synthetic authority.
    # The fixture's own DSN: Connection.info.dsn omits the password, which CI's password-authenticated server requires.
    with psycopg.connect(isolated_kala_db_dsn) as other:
        with pytest.raises(reader.DashaBuildRefused, match='settled_build_absent'):
            reader.load_pinned_vimshottari(other, CHART)


def test_gate_is_required_even_on_a_guarded_throwaway(restored):
    """A: neither ownership nor row presence implies explicit authorization."""
    with pytest.raises(ValueError, match='explicit.*gate'):
        wrap(restored)


def test_non_rehearsal_identity_and_changed_custody_refuse(restored, job_scratch):
    """A: database name is insufficient; ownership is rechecked at consumption."""
    name = restored.info.dbname
    restored.execute(sql.SQL('COMMENT ON DATABASE {} IS NULL').format(sql.Identifier(name)))
    with pytest.raises(ValueError, match='ownership'):
        wrap(restored, enabled=True)
    restored.execute(sql.SQL('COMMENT ON DATABASE {} IS {}').format(
        sql.Identifier(name), sql.Literal('ky.job=' + job_scratch.name)))
    conn = wrap(restored, enabled=True)
    restored.execute(sql.SQL('COMMENT ON DATABASE {} IS {}').format(sql.Identifier(name), sql.Literal('ky.job=another-job')))
    with pytest.raises(ValueError, match='ownership'):
        reader.load_pinned_vimshottari(conn, CHART)


def test_missing_or_relative_job_scratch_refuses_before_sql(monkeypatch):
    """A: without an absolute JOB_SCRATCH no ownership can be proven; refuse unchanged."""
    class Target:
        info = None
        def execute(self, *args):
            pytest.fail('ownerless rehearsal reached SQL')
    monkeypatch.delenv('JOB_SCRATCH')
    with pytest.raises(ValueError, match='absolute JOB_SCRATCH required'):
        wrap(Target(), enabled=True)
    monkeypatch.setenv('JOB_SCRATCH', 'relative/job')
    with pytest.raises(ValueError, match='absolute JOB_SCRATCH required'):
        wrap(Target(), enabled=True)


def test_remote_and_admin_targets_refuse_before_sql(job_scratch):
    """A: a rehearsal-like name on another endpoint never authorizes access.

    A valid scratch is present (autouse fixture), so the refusal measured here
    is the target check, not the missing-scratch check."""
    from types import SimpleNamespace
    for host, port, name in [('192.0.2.1',55433,'ky_rehearse_test'),
                             ('127.0.0.1',5432,'ky_rehearse_test'),
                             ('127.0.0.1',55433,'postgres')]:
        class Target:
            info = SimpleNamespace(host=host, port=port, dbname=name)
            def execute(self, *args):
                pytest.fail('unsafe endpoint reached SQL')
        with pytest.raises(ValueError, match='guarded rehearsal target'):
            wrap(Target(), enabled=True)


def test_production_loader_still_requires_the_governed_line(restored, tmp_path, monkeypatch):
    """A: synthetic authority cannot replace/mask the production receipt."""
    conn = wrap(restored, enabled=True)
    rows, _ = reader.load_pinned_vimshottari(conn, CHART)
    record = conn.synthetic_record
    path = tmp_path / 'synthetic.json'
    path.write_text(json.dumps(record))
    monkeypatch.setattr(reader, 'SETTLEMENT_PATH', path)
    monkeypatch.setattr(verifier, '_SETTLEMENT_PATH', path)
    with pytest.raises(reader.DashaBuildRefused, match='settlement_malformed'):
        reader.load_dasha_settlement(CHART)
    with pytest.raises(verifier.Unverifiable, match='settlement_malformed'):
        verifier._load_dasha_settlement(CHART)
    path.unlink()
    with pytest.raises(reader.DashaBuildRefused, match='settlement_missing'):
        reader.load_dasha_settlement(CHART)
    # Even during rehearsal, a connection-free selection must use governance.
    with pytest.raises(reader.DashaBuildRefused, match='settlement_missing'):
        reader.select_dasha_read_contract(CHART, rows)


def test_profiles_scope_measures_rows_and_queries_not_empty_ddl_scans(restored):
    """B/ruling(4): empty FK validation allowed; even empty row queries forbidden."""
    conn = wrap(restored, enabled=True)
    restored.execute('ALTER TABLE charts ADD FOREIGN KEY(client_id) REFERENCES profiles(id)')
    # PostgreSQL counts empty DDL validation as a scan. Force local stats out;
    # detector uses tuple reads and the harness's explicit SQL/load census.
    restored.execute('SELECT pg_stat_force_next_flush()')
    scope = adapter().profiles_scope(conn, profile_rows_loaded=0, profile_row_queries=0)
    assert scope['passed'] is True, scope
    assert scope['profile_tuple_reads'] == 0
    assert scope['profile_table_scans'] > 0  # empty schema FK validation really occurred
    assert scope['production_acceptance'] is False
    restored.execute('SELECT id FROM profiles WHERE false')  # zero rows is still a forbidden query
    assert adapter().profiles_scope(conn, profile_rows_loaded=0, profile_row_queries=1)['passed'] is False
    assert adapter().profiles_scope(conn, profile_rows_loaded=1, profile_row_queries=0)['passed'] is False
    assert adapter().profiles_scope(conn)['passed'] is None  # no invented zero census
    # Synthetic-only row proves actual tuple reads independently defeat green.
    restored.execute('INSERT INTO profiles VALUES (42)')
    restored.execute('SELECT * FROM profiles').fetchall()
    restored.execute('SELECT pg_stat_force_next_flush()')
    assert adapter().profiles_scope(conn, profile_rows_loaded=0, profile_row_queries=0)['passed'] is False
