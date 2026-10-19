"""SR-J2A-N18 — migration 1394: the 1379 statement locks serve the charts a statement touches (real disposable database).

Production holds a non-canonical chart in kala_gochara_publication (1c826d5a-…/4.0/candidate) and kala_gochara_authority. Before 1394 the
1379 BEFORE STATEMENT triggers walked EVERY chart present (1153 ka_gochara_chart_statement_lock), so ANY UPDATE/DELETE on those tables --
including the J-2a teardown's zero-row DELETE -- raised the N18 one-chart-per-transaction refusal (P0001). The fixture seeds exactly that
production shape (a foreign chart's rows in both tables) before 1379 and applies 1379, 1382 and 1394 in order.

Claims and their sources (each measured by a statement that can fail, none golden-captured):
  C1  a statement touching only the governed chart succeeds with a foreign chart present and takes exactly that chart's family key
      -- 1153 ka_gochara_lock_chart (:430-455: N18 :441-444, D-SCOPE :446-449); SR-J2A-N18 ruling (i).
  C2  a statement touching two charts, or only a non-canonical chart, is still refused and leaves every row -- N18/D-SCOPE; ruling (ii)
      and "never delete or alter another chart's rows".
  C3  the J-2a teardown's own delete sequence passes, EMPTY and REAL (5.0 rows), with the foreign rows present, and the foreign rows
      are still there afterwards -- ruling (iii).
  C4  the catalog: 0_ BEFORE locks and the 9_ AFTER transition-table locks are ENABLE ALWAYS (they fire under replica role), the
      migration is re-runnable, and it joins the Kāla protected window (SR-J2A-N18: "joins the protected list").
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .test_a53_inventory import ADMIN_DSN, CHART_ID, apply_near_miss_storage, create_am5_database, drop_am5_database

ROOT = Path(__file__).resolve().parents[5]
MIGRATIONS = ROOT / 'platform/migrations'
FOREIGN = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'      # the production non-canonical chart (read back 2026-10-17)
LOCK_FIX = '1394_gochara_statement_lock_touched_charts.sql'
BEFORE_LOCKS = ('kala_gochara_publication_0_authority_statement_lock', 'kala_gochara_authority_0_statement_lock')
AFTER_LOCKS = tuple(f'kala_gochara_{t}_9_touched_charts_{e}_lock' for t in ('publication', 'authority') for e in ('update', 'delete'))
N18 = r'lock-order violation \(steward ruling B / N18\)'
DSCOPE = r'is not governed by the Gochara-5 contract'

sys.path.insert(0, str(ROOT / 'platform/scripts'))
import teardown_v5_small_test_job as td  # noqa: E402

STUB_ORCHESTRATOR_DDL = (
    'CREATE TABLE public.asset_provenance_receipts (asset_id text, chart_id uuid)',
    'CREATE TABLE public.asset_freshness (asset_id text, chart_id uuid)',
    'CREATE TABLE public.build_runs (id uuid PRIMARY KEY)',
    'CREATE TABLE public.build_run_assets (run_id uuid, asset_id text)',
    'CREATE TABLE public.asset_throughput (asset_id text, chart_id uuid)',
)


def _publish(conn, chart, generation, status, vector=None):
    conn.execute("INSERT INTO public.kala_gochara_publication"
                 " (manifest_id,chart_id,generation,writer_asset_id,convention_id,input_generation_vector,"
                 " ephemeris_backend,horizon,row_counts,content_digest,status)"
                 " VALUES (%s,%s,%s,'ka_gochara_v5','n18-metadata-only',%s,'{}',"
                 " tstzrange('2025-01-01 UTC','2025-02-01 UTC','[)'),'{}','fixture',%s)",
                 (uuid.uuid4(), chart, generation, Jsonb(vector or {}), status))


@pytest.fixture(scope='module')
def lock_db():
    admin, name, dsn = create_am5_database('n18')
    conn = None
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        for ddl in STUB_ORCHESTRATOR_DDL:
            conn.execute(ddl)
        apply_near_miss_storage(conn)       # the teardown's closed list covers the migration-1308 generation tables
        conn.execute('CREATE TABLE public.kala_gochara_windows (chart_id uuid)')
        conn.execute((ROOT / 'platform/supabase/migrations/527_kala_gochara_generation_authority.sql').read_text())
        conn.execute((MIGRATIONS / '1236_gochara_authority_refuses_governed_generation.sql').read_text())
        conn.execute("INSERT INTO public.kala_gochara_convention"
                     " (convention_id,zodiac,ayanamsha,sidereal_method,node_model,node_source,epoch_convention,"
                     " time_scale,house_system,ephemeris_mode,method_version)"
                     " VALUES ('n18-metadata-only','fixture','fixture','fixture','fixture','fixture','fixture',"
                     " 'fixture','fixture','fixture','fixture')")
        # production's shape (readback J-2a.teardown-diag3): the canonical chart has a rolled-back 4.0 manifest, the foreign chart an
        # unpublished 4.0 candidate; a '5.0' unsealed test-slice candidate is the teardown's real target.
        _publish(conn, CHART_ID, '4.0', 'rolled_back')
        _publish(conn, CHART_ID, '5.0', 'candidate', {'stored_scope': 'test_slice'})
        _publish(conn, FOREIGN, '4.0', 'candidate')
        for chart in (CHART_ID, FOREIGN):
            conn.execute("INSERT INTO public.kala_gochara_authority(chart_id,authoritative_generation,flipped_by,evidence_ref)"
                         " VALUES (%s,'3.0','fixture','previous-head')", (chart,))
        with conn.transaction():
            conn.execute((MIGRATIONS / '1379_gochara_sealed_authority.sql').read_text())
            conn.execute((MIGRATIONS / '1382_gochara_authority_no_truncate.sql').read_text())
            # Optional only so the same behavioural oracles run on a revert copy (1379 alone) and fail there for the
            # real reason; test_migration_joins_the_protected_window requires the file.
            if (MIGRATIONS / LOCK_FIX).exists():
                conn.execute((MIGRATIONS / LOCK_FIX).read_text())
        yield conn, dsn
    finally:
        if conn is not None:
            conn.close()
        drop_am5_database(admin, name)


@pytest.fixture
def db(lock_db):
    conn, _ = lock_db
    with conn.transaction(force_rollback=True):
        yield conn


def _advisory_keys(conn):
    return [r[0] for r in conn.execute(
        "SELECT ((classid::bigint << 32) + objid::bigint) FROM pg_locks"
        " WHERE locktype = 'advisory' AND granted AND pid = pg_backend_pid() ORDER BY 1").fetchall()]


def _family_key(chart):
    # the chart family key, pinned independently of the helper under test (1153 :453)
    return f'gochara5:chart:{chart}'


def _charts(conn, table):
    return sorted({r[0] for r in conn.execute(f'SELECT chart_id::text FROM public.{table}').fetchall()})


def _snapshot(conn):
    return (conn.execute('SELECT to_jsonb(t)::text FROM public.kala_gochara_publication t ORDER BY manifest_id').fetchall(),
            conn.execute('SELECT to_jsonb(t)::text FROM public.kala_gochara_authority t ORDER BY chart_id').fetchall())


# ── C1: touching only the governed chart succeeds, taking only that chart's key ───────────────────────────────────────────────────

@pytest.mark.parametrize('sql', [
    "UPDATE public.kala_gochara_publication SET status = status WHERE chart_id = '%s' AND generation = '4.0'" % CHART_ID,
    "DELETE FROM public.kala_gochara_publication WHERE chart_id = '%s' AND generation = '5.0'" % CHART_ID,
    "UPDATE public.kala_gochara_authority SET authoritative_generation = '3.0' WHERE chart_id = '%s'" % CHART_ID,
], ids=['publication-update', 'publication-delete', 'authority-update'])
def test_statement_on_the_governed_chart_succeeds_with_a_foreign_chart_present(db, sql):
    assert FOREIGN in _charts(db, 'kala_gochara_publication') and FOREIGN in _charts(db, 'kala_gochara_authority')   # production's shape
    foreign_before = db.execute("SELECT to_jsonb(t)::text FROM public.kala_gochara_publication t WHERE chart_id = %s", (FOREIGN,)).fetchall()
    db.execute(sql)
    assert _advisory_keys(db) == [db.execute('SELECT hashtext(%s)::bigint', (_family_key(CHART_ID),)).fetchone()[0]]   # exactly ONE key: X's
    assert db.execute("SELECT current_setting('gochara5.bound_chart')").fetchone() == (CHART_ID,)
    assert db.execute("SELECT to_jsonb(t)::text FROM public.kala_gochara_publication t WHERE chart_id = %s", (FOREIGN,)).fetchall() == foreign_before


def test_zero_row_statement_touches_no_chart_beyond_the_governed_one(db):
    db.execute("DELETE FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '9.9'", (CHART_ID,))
    db.execute("UPDATE public.kala_gochara_authority SET authoritative_generation = '3.0' WHERE false")
    assert db.execute("SELECT current_setting('gochara5.bound_chart', true)").fetchone()[0] in ('', CHART_ID)


# ── C2: two charts, or a non-canonical chart, are still refused ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('sql', [
    "UPDATE public.kala_gochara_publication SET status = status",
    "UPDATE public.kala_gochara_authority SET authoritative_generation = '3.0'",
    "DELETE FROM public.kala_gochara_publication WHERE generation = '4.0'",
], ids=['publication-update-both', 'authority-update-both', 'publication-delete-both'])
def test_statement_touching_two_charts_is_refused_and_changes_nothing(db, sql):
    before = _snapshot(db)
    with pytest.raises(psycopg.errors.RaiseException, match=N18):
        with db.transaction():
            db.execute(sql)
    assert _snapshot(db) == before


@pytest.mark.parametrize('sql', [
    "DELETE FROM public.kala_gochara_publication WHERE chart_id = '%s'" % FOREIGN,
    "UPDATE public.kala_gochara_publication SET status = 'rolled_back' WHERE chart_id = '%s'" % FOREIGN,
    "DELETE FROM public.kala_gochara_authority WHERE chart_id = '%s'" % FOREIGN,
], ids=['publication-delete-foreign', 'publication-update-foreign', 'authority-delete-foreign'])
def test_statement_touching_only_a_foreign_chart_is_refused_and_its_rows_stay(db, sql):
    before = _snapshot(db)
    with pytest.raises(psycopg.errors.RaiseException, match=f'{N18}|{DSCOPE}'):
        with db.transaction():
            db.execute(sql)
    assert _snapshot(db) == before


# ── C3: the J-2a teardown's own delete sequence, empty and real, with the foreign rows present ─────────────────────────────────────

def _teardown_connection(dsn):
    return psycopg.connect(make_conninfo(ADMIN_DSN, dbname=psycopg.conninfo.conninfo_to_dict(dsn)['dbname']),
                           row_factory=dict_row, autocommit=False, connect_timeout=3)


def _teardown_sequence(cur):
    """The script's own lock and delete steps, in its own order (teardown() :606-)."""
    td._take_locks(cur)
    td._lock_delete_tables(cur)
    td._delete_everything(cur, [])


def test_empty_teardown_passes_with_the_foreign_chart_rows_present(lock_db, monkeypatch):
    _, dsn = lock_db
    monkeypatch.setattr(td, 'GENERATION', '7.7')           # a generation nothing was built for: every delete matches zero rows
    with _teardown_connection(dsn) as conn:
        before = _snapshot(conn)
        _teardown_sequence(conn.cursor())
        assert _snapshot(conn) == before
        conn.rollback()


def test_real_teardown_of_the_5_0_rows_passes_and_only_the_governed_chart_rows_go(lock_db):
    _, dsn = lock_db
    with _teardown_connection(dsn) as conn:
        for t in ('asset_provenance_receipts', 'asset_freshness', 'asset_throughput'):
            conn.execute(f'INSERT INTO public.{t}(asset_id, chart_id) VALUES (%s, %s)', (td.ASSET_ID, CHART_ID))
        cur = conn.cursor()
        _teardown_sequence(cur)
        rows = conn.execute('SELECT chart_id::text AS c, generation AS g FROM public.kala_gochara_publication ORDER BY 1, 2').fetchall()
        assert rows == [{'c': FOREIGN, 'g': '4.0'}, {'c': CHART_ID, 'g': '4.0'}]    # 5.0 gone; 4.0 of both charts untouched
        for t in ('asset_provenance_receipts', 'asset_freshness', 'asset_throughput'):
            assert conn.execute(f'SELECT count(*) AS n FROM public.{t}').fetchone()['n'] == 0
        assert sorted(r['c'] for r in conn.execute('SELECT chart_id::text AS c FROM public.kala_gochara_authority').fetchall()) \
            == sorted([CHART_ID, FOREIGN])                                  # the authority rows of both charts are untouched
        conn.rollback()


# ── C4: catalog, replica role, re-run, protected window ────────────────────────────────────────────────────────────────────────────

def test_locks_are_always_triggers_with_the_expected_shape(lock_db):
    conn, _ = lock_db
    rows = dict(conn.execute("SELECT tgname, tgenabled::text || ':' || tgtype::text || ':' || (tgoldtable IS NOT NULL)::text || ':' || (tgnewtable IS NOT NULL)::text"
                             " FROM pg_trigger WHERE NOT tgisinternal AND tgname = ANY(%s)", (list(BEFORE_LOCKS + AFTER_LOCKS),)).fetchall())
    assert set(rows) == set(BEFORE_LOCKS + AFTER_LOCKS)
    for name in BEFORE_LOCKS:
        assert rows[name] == 'A:26:false:false', name              # ALWAYS, STATEMENT|BEFORE|DELETE|UPDATE, no transition table
    for name in AFTER_LOCKS:
        assert rows[name] == ('A:8:true:false' if name.endswith('delete_lock') else 'A:16:true:true'), name


def test_the_always_locks_also_fire_under_replica_role(db):
    db.execute("SET LOCAL session_replication_role = 'replica'")
    with pytest.raises(psycopg.errors.RaiseException, match=N18):
        with db.transaction():
            db.execute('UPDATE public.kala_gochara_publication SET status = status')


def test_migration_is_rerunnable(lock_db):
    conn, _ = lock_db
    with conn.transaction():
        conn.execute((MIGRATIONS / LOCK_FIX).read_text())
        conn.execute((MIGRATIONS / LOCK_FIX).read_text())
    test_locks_are_always_triggers_with_the_expected_shape(lock_db)


def test_migration_joins_the_protected_window():
    sys.path.insert(0, str(ROOT / 'platform/scripts/governance'))
    sys.path.insert(0, str(ROOT / 'platform/scripts'))
    import kala_protected_migrations as kpm
    assert (MIGRATIONS / LOCK_FIX).exists()
    assert LOCK_FIX in kpm.derive(ROOT)
