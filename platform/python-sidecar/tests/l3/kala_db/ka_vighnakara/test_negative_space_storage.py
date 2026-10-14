"""Real SQL candidate storage and mutation oracles on a guarded throwaway DB."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import psycopg
import pytest

from services.ka_vighnakara.model import Finding, NegativeSpace, interpret
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT
from tests.l3.ka_vighnakara.test_negative_space import finding, protection
from tests.l3.kala_db._schema import apply_schema_migration, apply_stage_verification_migration

ROOT=Path(__file__).parents[4]
MIGRATION=ROOT.parent/'migrations/1349_k3_1_negative_space_contract.sql'
EVIDENCE_MIGRATION=ROOT.parent/'migrations/1374_k3_defeating_evidence_guard.sql'
CHART='00000000-0000-0000-0000-000000000392'
BUILD='00000000-0000-0000-0000-000000000393'
GEN='candidate:fixture'


def storage():
    assert importlib.util.find_spec('services.ka_vighnakara.storage') is not None, 'K3 storage missing'
    from services.ka_vighnakara.storage import write_fixture_candidate
    return write_fixture_candidate


@pytest.fixture(scope='module')
def database(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn) as c:
        c.execute('''CREATE TABLE charts (id uuid PRIMARY KEY);
          CREATE TABLE kala_obstruction (
            id bigserial PRIMARY KEY, chart_id uuid NOT NULL REFERENCES charts(id),
            convergence_id bigint, signal_id uuid, obstruction_type text NOT NULL
              CHECK (obstruction_type IN ('malefic_transit','dasha_lord_afflicted','panchanga_obstruction','rashi_dristi_conflict','combustion','gandanta','papakartari')),
            severity text NOT NULL CHECK (severity IN ('mild','moderate','severe')),
            severity_score double precision NOT NULL CHECK (severity_score BETWEEN 0 AND 1),
            override_score double precision NOT NULL DEFAULT 0 CHECK (override_score BETWEEN 0 AND 1),
            obstruction_detail jsonb NOT NULL DEFAULT '{}', source_citation text NOT NULL,
            computed_at timestamptz DEFAULT now());
          CREATE TABLE kala_darshana (id bigserial PRIMARY KEY);
          CREATE TABLE kala_layer_candidate (chart_id uuid NOT NULL, generation text NOT NULL,
            build_id uuid UNIQUE NOT NULL, state text NOT NULL, conventions jsonb NOT NULL,
            PRIMARY KEY(chart_id,generation));
          CREATE TABLE kala_layer_head (chart_id uuid PRIMARY KEY, generation text NOT NULL);''')
        apply_schema_migration(c, ROOT.parent/'migrations/1338_kala_assertion_vertical_slice.sql')
        assert MIGRATION.exists(), 'K3 additive candidate schema missing'
        apply_schema_migration(c, MIGRATION)
        apply_schema_migration(c, EVIDENCE_MIGRATION)
        c.execute('INSERT INTO charts VALUES (%s)',(CHART,))
        c.execute("INSERT INTO kala_layer_candidate VALUES (%s,%s,%s,'building','{\"fixture\":true}')",(CHART,GEN,BUILD))
    yield isolated_kala_db_dsn


@pytest.fixture(params=[False, True], ids=['before-1376', 'after-1376'])
def conn(database, request):
    with psycopg.connect(database) as c:
        if request.param:
            apply_stage_verification_migration(c, 'kala_obstruction')
        yield c
        c.rollback()


def ctx(c,**changes):
    values=dict(db_conn=c,build_id=BUILD,dry_run=False,config={'chart_id':CHART})
    values.update(changes)
    return SimpleNamespace(**values)


def write(c,**changes):
    return storage()(ctx(c),[finding(**changes)])


def test_dry_run_without_database():
    assert storage()(SimpleNamespace(dry_run=True),[]) == 0


def test_repeat_candidate_write_has_zero_net_rows(conn):
    write(conn)
    write(conn)
    assert conn.execute('SELECT count(*) FROM kala_obstruction').fetchone()[0] == 1


def test_typed_axes_stored_separately(conn):
    write(conn)
    assert conn.execute('SELECT exposure,knowledge,rule_conclusion,defeat_state,measurement FROM kala_obstruction').fetchone() == ('in_risk_set','complete','obstructed','active','not_estimated_here')


def test_release_interval_stored(conn):
    write(conn)
    assert conn.execute("SELECT (release->>'instant')::timestamptz=interval_end FROM kala_obstruction").fetchone()[0]


def test_legacy_and_other_generation_byte_identical(conn):
    conn.execute("INSERT INTO kala_obstruction (chart_id,generation,obstruction_type,severity,severity_score,source_citation) VALUES (%s,NULL,'malefic_transit','mild',0.5,'fixture:legacy'),(%s,'retained','malefic_transit','mild',0.5,'fixture:retained')",(CHART,CHART))
    before=conn.execute("SELECT to_jsonb(o) FROM kala_obstruction o ORDER BY id").fetchall()
    write(conn)
    after=conn.execute("SELECT to_jsonb(o) FROM kala_obstruction o WHERE generation IS DISTINCT FROM %s ORDER BY id",(GEN,)).fetchall()
    assert after == before


@pytest.mark.parametrize('state',['published','verified','failed'])
def test_nonbuilding_candidate_refused(conn,state):
    conn.execute('UPDATE kala_layer_candidate SET state=%s',(state,))
    with pytest.raises(ValueError,match='building'): write(conn)


def test_published_head_cannot_be_replaced(conn):
    conn.execute('INSERT INTO kala_layer_head VALUES (%s,%s)',(CHART,GEN))
    with pytest.raises(ValueError,match='published'): write(conn)


def test_non_fixture_binding_refused(conn):
    conn.execute("UPDATE kala_layer_candidate SET conventions='{}'")
    with pytest.raises(ValueError,match='fixture'): write(conn)


def test_cross_chart_refused_before_delete(conn):
    with pytest.raises(ValueError,match='partition'): write(conn,chart_id=str(uuid4()))


def test_cross_generation_refused_before_delete(conn):
    with pytest.raises(ValueError,match='partition'): write(conn,generation='candidate:other')


def test_duplicate_assertion_identity_refused(conn):
    with pytest.raises(ValueError,match='duplicate'): storage()(ctx(conn),[finding(),finding()])


def test_unbound_candidate_preserves_named_reason(conn):
    write(conn,binding='unbound',null_reason='judge_vedha_source_mapping_unadmitted')
    assert conn.execute('SELECT effective_state,null_reason FROM kala_obstruction').fetchone() == ('information_unavailable','judge_vedha_source_mapping_unadmitted')


def test_numeric_compatibility_slots_are_inert(conn):
    write(conn)
    assert conn.execute('SELECT severity_score,override_score FROM kala_obstruction').fetchone() == (0,0)


def test_candidate_constraints_reject_cancelled_in_force(conn):
    write(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("UPDATE kala_obstruction SET defeat_state='cancelled'")


def test_candidate_constraints_reject_unknown_as_silent(conn):
    write(conn,binding='unbound',null_reason='source_unbound')
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("UPDATE kala_obstruction SET effective_state='evaluated_silent'")


def test_empty_replacement_deletes_only_candidate(conn):
    write(conn)
    storage()(ctx(conn),[])
    assert conn.execute('SELECT count(*) FROM kala_obstruction').fetchone()[0] == 0


def test_writer_explicit_fixture_dispatch_without_legacy_scan(conn):
    from pipeline.orchestrator.writers.ka_vighnakara import KaVighnakaraWriter
    context=ctx(conn,config={'chart_id':CHART,'negative_space_fixture_inputs':[finding().model_dump(mode='json')]})
    assert KaVighnakaraWriter().run(context).rows_inserted == 1


def test_fixture_contract_is_version_pinned():
    assert Finding.model_fields['contract_version'].annotation.__args__ == ('k3-negative-space/1.0.0',)


def test_additive_migration_reapplies(conn):
    apply_schema_migration(conn, MIGRATION)
    assert conn.execute("SELECT count(*) FROM pg_constraint WHERE conrelid='kala_obstruction'::regclass AND conname='kala_obstruction_k3_axes_check'").fetchone()[0] == 1


@pytest.mark.parametrize('release', ['{"kind":"instant","instant":""}',
    '{"kind":"instant","instant":"tomorrow"}', '{"kind":"conditional","predicate_ref":""}'])
def test_database_rejects_untyped_release(conn,release):
    write(conn)
    with pytest.raises((psycopg.errors.CheckViolation,psycopg.errors.InvalidDatetimeFormat)):
        conn.execute('UPDATE kala_obstruction SET release=%s::jsonb,release_reason=%s',(release,'release_conditional' if 'conditional' in release else None))


def test_candidate_unknown_release_with_null_reason_refused(conn):
    write(conn,release={'kind':'unknown'})
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute('UPDATE kala_obstruction SET release_reason=NULL')


def test_writer_dry_run_requires_no_inputs():
    from pipeline.orchestrator.writers.ka_vighnakara import KaVighnakaraWriter
    assert KaVighnakaraWriter().run(SimpleNamespace(dry_run=True)).rows_inserted == 0


@pytest.mark.parametrize('mutation', [
    "assertion=jsonb_set(assertion,'{protections}','[]')",
    "assertion=jsonb_set(assertion,'{protections,0,target_assertion_id}','\"unrelated\"')",
    "assertion=jsonb_set(assertion,'{protections,0,fact_ids}','[]')",
    "assertion=jsonb_set(assertion,'{protections,0,kind}','\"contests\"')",
    "assertion=jsonb_set(assertion,'{protections,0,interval}', '{\"t0\":\"2027-01-01T00:00:00+00:00\",\"t1\":\"2027-02-01T00:00:00+00:00\"}')",
    "assertion=jsonb_set(assertion,'{protections,0,interval}', '{\"t0\":\"2026-02-01T00:00:00+00:00\",\"t1\":\"2026-03-01T00:00:00+00:00\"}')",
    "assertion=jsonb_set(assertion,'{protections,0,interval}', '{\"t0\":\"2025-12-01T00:00:00+00:00\",\"t1\":\"2026-01-01T00:00:00+00:00\"}')",
    "roots=jsonb_set(roots,'{fact_ids}','[]')",
])
def test_database_cancellation_requires_targeted_retained_evidence(conn,mutation):
    write(conn,protections=[protection()])
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute('UPDATE kala_obstruction SET '+mutation)


@pytest.mark.parametrize('kind,state', [('defeats','obstruction_cancelled'),
    ('excepts','obstruction_cancelled'), ('partly_defeats','obstruction_partly_cancelled')])
@pytest.mark.parametrize('offset', ['Z', '+05:30'])
def test_protected_candidate_preserves_evidence_and_instants(conn,kind,state,offset):
    interval={'t0':f'2026-01-01T00:00:00.123456{offset}',
              't1':f'2026-02-01T00:00:00.654321{offset}'}
    value=finding(interval=interval,release={'kind':'unknown'},
                  protections=[protection(kind=kind,interval=interval)])
    assert storage()(ctx(conn),[value]) == 1
    payload,roots,release,start,end,stored_state=conn.execute(
        "SELECT assertion,roots,(release->>'instant')::timestamptz,"
        'interval_start,interval_end,effective_state FROM kala_obstruction').fetchone()
    expected=interpret(value)
    assert NegativeSpace.model_validate(payload) == expected
    assert (roots,release,start,end,stored_state) == (
        expected.roots.model_dump(mode='json'),None if kind == 'partly_defeats' else value.interval.t0,
        value.interval.t0,value.interval.t1,state)


def test_evidence_guard_reapplies_without_changing_rows(conn):
    write(conn,protections=[protection()])
    before=conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o').fetchall()
    apply_schema_migration(conn, EVIDENCE_MIGRATION)
    assert conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o').fetchall() == before


def test_alias_rejection_preserves_existing_candidate(conn):
    write(conn,protections=[protection()])
    before=conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o').fetchall()
    with pytest.raises(ValueError,match='duplicate physical'):
        storage()(ctx(conn),[finding(protections=[protection()]),
            finding(assertion_id='alias',protections=[protection()])])
    assert conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o').fetchall() == before


def test_candidate_stores_honest_single_tier_and_legacy_stays_null(conn, request):
    has_tier = request.node.callspec.params['conn']
    conn.execute("INSERT INTO kala_obstruction (chart_id,obstruction_type,severity,severity_score,source_citation) VALUES (%s,'malefic_transit','mild',0.5,'fixture:legacy')", (CHART,))
    write(conn)
    rows = conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o ORDER BY id').fetchall()
    assert all(('verification_pass_status' in row[0]) == has_tier for row in rows)
    assert rows[0][0].get('verification_pass_status') is None
    assert rows[1][0].get('verification_pass_status') == (UNVERIFIED_DEFAULT if has_tier else None)
    apply_stage_verification_migration(conn, 'kala_obstruction')
    assert conn.execute('SELECT verification_pass_status FROM kala_obstruction WHERE generation=%s', (GEN,)).fetchone() == (UNVERIFIED_DEFAULT if has_tier else None,)
    write(conn)
    assert conn.execute('SELECT verification_pass_status FROM kala_obstruction WHERE generation=%s', (GEN,)).fetchone() == (UNVERIFIED_DEFAULT,)
    assert conn.execute('SELECT verification_pass_status FROM kala_obstruction WHERE generation IS NULL').fetchone() == (None,)


def test_candidate_write_is_deploy_safe(conn, request):
    has_tier = request.node.callspec.params['conn']
    assert write(conn) == 1
    row = conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o WHERE generation=%s', (GEN,)).fetchone()[0]
    assert ('verification_pass_status' in row) == has_tier
    if has_tier:
        assert row['verification_pass_status'] == UNVERIFIED_DEFAULT
    assert row['effective_state'] == interpret(finding()).effective_state


def test_label_only_replacement_preserves_protected_candidate(conn):
    write(conn, protections=[protection()])
    before = conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o').fetchall()
    with pytest.raises(ValueError, match='protection target'):
        write(conn, assertion_id='alias:replacement', protections=[protection()])
    assert conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o').fetchall() == before


@pytest.mark.parametrize('retarget', [False, True])
def test_overlapping_alias_preserves_protected_candidate(conn, retarget):
    write(conn, protections=[protection()])
    before = conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o').fetchall()
    alias = finding(assertion_id='alias:segment',
        protections=[protection(target_assertion_id='alias:segment' if retarget else 'fixture:vedha')],
        interval={'t0':'2026-01-01T00:00:00Z','t1':'2026-01-15T00:00:00Z'},
        release={'kind':'instant','instant':'2026-01-15T00:00:00Z'})
    with pytest.raises(ValueError, match='duplicate physical'):
        storage()(ctx(conn), [finding(protections=[protection()]), alias])
    assert conn.execute('SELECT to_jsonb(o) FROM kala_obstruction o').fetchall() == before
