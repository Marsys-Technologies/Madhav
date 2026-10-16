"""Synthetic FK oracles for the madhav-6d ruling (2026-10-16).

Authority: CANONICAL_L1_OFFLINE_FIXTURE_SPEC_v1_0.md v1.1, restore/FK audit;
CLAUDE.md §N.8 requires measured failure, §N.7.6 requires honest nulls.
No classical computation is changed or asserted by these transport tests.
"""
import importlib.util
from pathlib import Path

import psycopg
import pytest


REPO = Path(__file__).resolve().parents[5]
SPEC = importlib.util.spec_from_file_location(
    'canonical_l1_snapshot', REPO / 'platform/scripts/gochara/canonical_l1_snapshot.py')
snapshot = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(snapshot)


@pytest.fixture
def restored(isolated_kala_db_dsn):
    """Only the guarded fixture owns this synthetic database and its teardown."""
    with psycopg.connect(isolated_kala_db_dsn, autocommit=True) as conn:
        conn.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
        conn.execute('''
            CREATE TABLE public.profiles(id integer PRIMARY KEY);
            CREATE TABLE public.authority(id integer PRIMARY KEY);
            INSERT INTO public.authority VALUES (1);
            CREATE TABLE public.charts(
                id integer PRIMARY KEY, client_id integer,
                CONSTRAINT personal_parent FOREIGN KEY(client_id) REFERENCES public.profiles(id));
            CREATE TABLE public.chart_facts(
                fact_id integer PRIMARY KEY, chart_id integer REFERENCES public.charts(id),
                authority_id integer,
                CONSTRAINT authority_parent FOREIGN KEY(authority_id) REFERENCES public.authority(id));
            CREATE TABLE public.chart_dashas(
                dasha_row_id integer PRIMARY KEY, chart_id integer REFERENCES public.charts(id),
                parent_id integer REFERENCES public.chart_dashas(dasha_row_id));
            CREATE TABLE public.life_events(
                event_id integer PRIMARY KEY, chart_id integer REFERENCES public.charts(id));
        ''')
        # The four row tables are loaded together, without rewriting client_id
        # or inventing a parent. Replica applies only inside this transaction.
        with conn.transaction():
            conn.execute('SET LOCAL session_replication_role = replica')
            conn.execute('INSERT INTO public.charts VALUES (1, 42)')
            conn.execute('INSERT INTO public.chart_facts VALUES (10, 1, 1)')
            conn.execute('INSERT INTO public.chart_dashas VALUES (20, 1, NULL)')
            conn.execute('INSERT INTO public.life_events VALUES (30, 1)')
        assert conn.execute('SHOW session_replication_role').fetchone() == ('origin',)
        yield conn, isolated_kala_db_dsn
        conn.execute('DROP SCHEMA IF EXISTS incoming CASCADE')
        conn.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')


@pytest.mark.parametrize('resolved', [False, True], ids=['dangling', 'resolved'])
def test_only_ruled_personal_reference_passes_without_reading_profiles(restored, resolved):
    """Break caught: rejecting the ruled edge, inventing counts, or reading profiles."""
    conn, dsn = restored
    if resolved:
        # A synthetic resolved edge must pass too; never export real profiles.
        conn.execute('INSERT INTO public.profiles VALUES (42)')
    before = conn.execute('SELECT row_to_json(c)::text FROM public.charts c').fetchall()
    # Any SELECT of profiles by the audit would wait on this lock and fail its
    # statement timeout. Catalog enumeration of the FK remains possible.
    with conn.transaction():
        conn.execute('LOCK TABLE public.profiles IN ACCESS EXCLUSIVE MODE')
        verdict = snapshot.audit_foreign_keys(dsn)
    assert verdict['passed'] is True, verdict
    assert verdict['status'] == 'FK_AUDIT_PASSED'
    assert verdict['production_acceptance'] is False
    assert len(verdict['constraints']) == 6
    personal = next(c for c in verdict['constraints'] if c['name'] == 'personal_parent')
    assert personal['classification'] == 'intentional_exclusion'
    assert personal['unresolved_rows'] is None  # Resolution deliberately unmeasured.
    assert personal['reason'] == 'intentional: parent personal data excluded by ruling (madhav-6d 2026-10-16)'
    assert all(c['unresolved_rows'] == 0 for c in verdict['constraints'] if c is not personal)
    assert conn.execute('SELECT row_to_json(c)::text FROM public.charts c').fetchall() == before
    # Ordinary FK enforcement must be active after restoration.
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        conn.execute('INSERT INTO public.charts VALUES (2, 999)')


def test_any_other_dangling_reference_fails_closed(restored):
    """Break caught: broadening the personal-data exception to other parents."""
    conn, dsn = restored
    with conn.transaction():
        conn.execute('SET LOCAL session_replication_role = replica')
        conn.execute('UPDATE public.chart_facts SET authority_id = 999')
    verdict = snapshot.audit_foreign_keys(dsn)
    assert verdict['passed'] is False
    assert verdict['status'] == 'FK_AUDIT_FAILED'
    broken = [c for c in verdict['constraints'] if c['classification'] == 'violation']
    assert [(c['name'], c['unresolved_rows']) for c in broken] == [('authority_parent', 1)]


def test_inventory_checks_both_endpoints_self_keys_and_composite_null_semantics(restored):
    """Break caught: auditing only outgoing or validated/non-composite FKs."""
    conn, dsn = restored
    conn.execute('''
        CREATE SCHEMA incoming;
        CREATE TABLE incoming."odd child"("Fact Ref" integer,
            CONSTRAINT inbound_parent FOREIGN KEY("Fact Ref") REFERENCES public.chart_facts(fact_id));
        CREATE TABLE public.pairs(a integer, b integer, UNIQUE(a,b));
        INSERT INTO public.pairs VALUES(1,2);
        ALTER TABLE public.life_events ADD COLUMN a integer, ADD COLUMN b integer;
        ALTER TABLE public.life_events ADD CONSTRAINT pair_parent
            FOREIGN KEY(a,b) REFERENCES public.pairs(a,b) MATCH FULL NOT VALID;
        CREATE TABLE public.unrelated(id integer REFERENCES public.authority(id));
    ''')
    with conn.transaction():
        conn.execute('SET LOCAL session_replication_role = replica')
        conn.execute('INSERT INTO incoming."odd child" VALUES (999)')
        conn.execute('UPDATE public.chart_dashas SET parent_id = 999')
        # MATCH FULL: one valid pair, one all-NULL pair, one partial-NULL
        # violation and one absent pair. Only the last two are unresolved.
        conn.execute('UPDATE public.life_events SET a=1,b=2')
        conn.execute('INSERT INTO public.life_events VALUES (31,1,NULL,NULL),(32,1,1,NULL),(33,1,9,9)')
        conn.execute('INSERT INTO public.unrelated VALUES (999)')
    verdict = snapshot.audit_foreign_keys(dsn)
    assert verdict['passed'] is False
    counts = {c['name']: c['unresolved_rows'] for c in verdict['constraints']}
    assert counts == {
        'personal_parent': None, 'chart_facts_chart_id_fkey': 0, 'authority_parent': 0,
        'chart_dashas_chart_id_fkey': 0, 'chart_dashas_parent_id_fkey': 1,
        'life_events_chart_id_fkey': 0, 'inbound_parent': 1, 'pair_parent': 2,
    }


def test_a_different_profiles_reference_is_a_scope_defect(restored):
    """Break caught: allowing every reference to profiles by table name alone."""
    conn, dsn = restored
    conn.execute('ALTER TABLE public.life_events ADD COLUMN person integer REFERENCES public.profiles(id)')
    verdict = snapshot.audit_foreign_keys(dsn)
    assert verdict['passed'] is False
    assert 'profiles_scope_defect' in verdict['errors']


def test_incomplete_restore_cannot_earn_a_vacuous_pass(restored):
    """Break caught: green audit over a missing restored table."""
    conn, dsn = restored
    conn.execute('DROP TABLE public.chart_dashas')
    verdict = snapshot.audit_foreign_keys(dsn)
    assert verdict['passed'] is False
    assert 'missing_restored_tables' in verdict['errors']


def test_audit_refuses_replica_session(restored):
    """Break caught: auditing before session_replication_role returns to origin."""
    _, dsn = restored
    replica = psycopg.conninfo.make_conninfo(dsn, options='-c session_replication_role=replica')
    verdict = snapshot.audit_foreign_keys(replica)
    assert verdict['passed'] is False
    assert 'replication_role_not_origin' in verdict['errors']


def test_interrupted_inspection_fails_closed(restored):
    """Break caught: turning a query error into a passing/partial audit."""
    conn, dsn = restored
    with conn.transaction():
        conn.execute('LOCK TABLE public.chart_facts IN ACCESS EXCLUSIVE MODE')
        verdict = snapshot.audit_foreign_keys(dsn)
    assert verdict['passed'] is False
    assert verdict['status'] == 'FK_AUDIT_FAILED'
    assert verdict['errors'] == ['database_audit_error']


def test_remote_dsn_is_refused_before_connecting(monkeypatch):
    """Break caught: accepting a target outside the throwaway local cluster."""
    # Safety boundary even when testing a planted reversion: never actually
    # attempt a remote connection. Local DB oracles above use real psycopg.
    monkeypatch.setattr(psycopg, 'connect', lambda *a, **kw: pytest.fail('remote connection attempted'))
    verdict = snapshot.audit_foreign_keys('postgresql://postgres@192.0.2.1:55433/fixture')
    assert verdict['passed'] is False
    assert verdict['errors'] == ['unsafe_audit_target']
