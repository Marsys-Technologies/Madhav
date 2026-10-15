"""J-6m admission/retention SQL oracles; no sky computation or production action.

Uses the A5.3 guarded, disposable database with the real migration chain. The
publication/seal rows below are synthetic *admission metadata*, including corrupt
pairs. Their setup bypasses seal insertion guards deliberately: this suite tests
which existing seals authority admission accepts, not whether sealing is earned.
"""
from pathlib import Path
import uuid

import psycopg
from psycopg.types.json import Jsonb
import pytest

from .test_a53_inventory import CHART_ID, create_am5_database, drop_am5_database

ROOT = Path(__file__).resolve().parents[5]
MIGRATIONS = ROOT / 'platform/migrations'
FOLLOWUP = '1382_gochara_authority_no_truncate.sql'


@pytest.fixture(scope='module')
def authority_db():
    admin, name, dsn = create_am5_database('j6m')
    conn = None
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        # Real 527 DDL, including its legacy window discriminator; no handwritten
        # authority-table replacement. 527 owns its own legacy transaction.
        conn.execute('CREATE TABLE public.kala_gochara_windows (chart_id uuid)')
        conn.execute((ROOT / 'platform/supabase/migrations/527_kala_gochara_generation_authority.sql').read_text())
        conn.execute((MIGRATIONS / '1236_gochara_authority_refuses_governed_generation.sql').read_text())
        conn.execute("INSERT INTO public.kala_gochara_convention"
                     " (convention_id,zodiac,ayanamsha,sidereal_method,node_model,node_source,epoch_convention,"
                     " time_scale,house_system,ephemeris_mode,method_version)"
                     " VALUES ('j6m-metadata-only','fixture','fixture','fixture','fixture','fixture','fixture',"
                     " 'fixture','fixture','fixture','fixture')")
        # Seed adversarial metadata before the migration; this is not a seal-flow
        # acceptance test and makes no claim of computed or verified chart data.
        with conn.transaction():
            conn.execute('ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER USER')
            cases = [
                (CHART_ID, '5.0', 'published', {}, 'match'),
                (CHART_ID, '5.1', 'published', {}, None),
                (CHART_ID, '5.2', 'candidate', {}, 'match'),
                (CHART_ID, '5.3', 'published', {}, 'mismatch'),
                (CHART_ID, '5.4', 'published', {'stored_scope': 'test_slice'}, 'match'),
                (CHART_ID, '5.5', 'published', {'test_slice': False}, 'match'),
                (CHART_ID, '10.0', 'published', {}, 'match'),
            ]
            for chart, gen, status, vector, seal in cases:
                manifest = uuid.uuid4()
                conn.execute("INSERT INTO public.kala_gochara_publication"
                             " (manifest_id,chart_id,generation,writer_asset_id,convention_id,input_generation_vector,"
                             " ephemeris_backend,horizon,row_counts,content_digest,status)"
                             " VALUES (%s,%s,%s,'ka_gochara_v5','j6m-metadata-only',%s,'{}',"
                             " tstzrange('2025-01-01 UTC','2025-02-01 UTC','[)'),'{}','fixture',%s)",
                             (manifest, chart, gen, Jsonb(vector), status))
                if seal:
                    conn.execute('INSERT INTO public.ka_gochara_generation_seal(chart_id,generation,manifest_id)'
                                 ' VALUES (%s,%s,%s)', (chart, gen, manifest if seal == 'match' else uuid.uuid4()))
            conn.execute('ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER USER')
        conn.execute("INSERT INTO public.kala_gochara_authority(chart_id,authoritative_generation,flipped_by,evidence_ref)"
                     " VALUES (%s,'3.0','fixture','previous-head')", (CHART_ID,))
        before = conn.execute('TABLE public.kala_gochara_authority').fetchall()
        with conn.transaction():
            conn.execute((MIGRATIONS / '1379_gochara_sealed_authority.sql').read_text())
            # Optional only so the same behavioral oracle runs on the revert
            # copy (1379 alone), exposing TRUNCATE's actual effect rather than
            # failing on a missing file. The static suite requires the file.
            if (MIGRATIONS / FOLLOWUP).exists():
                conn.execute((MIGRATIONS / FOLLOWUP).read_text())
        assert conn.execute('TABLE public.kala_gochara_authority').fetchall() == before
        yield conn
    finally:
        if conn is not None:
            conn.close()
        drop_am5_database(admin, name)


@pytest.fixture
def db(authority_db):
    with authority_db.transaction(force_rollback=True):
        yield authority_db


def _head(conn):
    return conn.execute('SELECT authoritative_generation FROM public.kala_gochara_authority WHERE chart_id=%s',
                        (CHART_ID,)).fetchone()[0]


def _set(conn, generation):
    conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation=%s WHERE chart_id=%s',
                 (generation, CHART_ID))


@pytest.mark.parametrize('mode', ['origin', 'replica'])
@pytest.mark.parametrize('generation', ['5.0', '10.0'])
def test_matching_published_non_slice_seal_admitted_and_explicit_previous_head_restored(db, mode, generation):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    _set(db, generation)
    assert _head(db) == generation
    _set(db, '3.0')
    assert _head(db) == '3.0'


@pytest.mark.parametrize('mode', ['origin', 'replica'])
@pytest.mark.parametrize('generation', ['5.1', '5.2', '5.3', '5.4', '5.5', '5.9'])
def test_unsealed_unpublished_mismatched_slice_and_missing_seals_refused(db, mode, generation):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    with pytest.raises(psycopg.errors.CheckViolation, match='governed head requires'):
        with db.transaction():
            _set(db, generation)
    assert _head(db) == '3.0'


@pytest.mark.parametrize('mode', ['origin', 'replica'])
def test_insert_also_requires_matching_seal(db, mode):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    db.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    with pytest.raises(psycopg.errors.CheckViolation):
        with db.transaction():
            db.execute("INSERT INTO public.kala_gochara_authority(chart_id,authoritative_generation) VALUES (%s,'5.1')",
                       (CHART_ID,))
    db.execute("INSERT INTO public.kala_gochara_authority(chart_id,authoritative_generation) VALUES (%s,'5.0')",
               (CHART_ID,))
    assert _head(db) == '5.0'


@pytest.mark.parametrize('mode', ['origin', 'replica'])
def test_delete_cannot_silently_restore_implicit_legacy_default(db, mode):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    _set(db, '5.0')
    with pytest.raises(psycopg.errors.CheckViolation, match='explicit retained previous head'):
        with db.transaction():
            db.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    assert _head(db) == '5.0'


@pytest.mark.parametrize('mode', ['origin', 'replica'])
@pytest.mark.parametrize('generation', ['5.0', '3.0', None])
def test_truncate_cannot_silently_restore_implicit_legacy_default(db, mode, generation):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    if generation is None:
        db.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    else:
        _set(db, generation)
    before = db.execute('TABLE public.kala_gochara_authority').fetchall()
    with pytest.raises(psycopg.errors.RaiseException, match='TRUNCATE refused on kala_gochara_authority'):
        with db.transaction():
            db.execute('TRUNCATE public.kala_gochara_authority')
    assert db.execute('TABLE public.kala_gochara_authority').fetchall() == before


@pytest.mark.parametrize('mode', ['origin', 'replica'])
@pytest.mark.parametrize('sql', [
    "UPDATE public.kala_gochara_publication SET status='rolled_back' WHERE generation='5.0'",
    "UPDATE public.kala_gochara_publication SET input_generation_vector='{}'::jsonb || '{\"test_slice\":true}'::jsonb WHERE generation='5.0'",
    "DELETE FROM public.kala_gochara_publication WHERE generation='5.0'",
])
def test_authoritative_manifest_cannot_be_withdrawn_or_replaced(db, mode, sql):
    db.execute(f"SET LOCAL session_replication_role = '{mode}'")
    _set(db, '5.0')
    with pytest.raises(psycopg.errors.CheckViolation, match='authoritative manifest is immutable|sealed boundary'):
        with db.transaction():
            db.execute(sql)
    assert _head(db) == '5.0'


def test_catalog_readback_names_validated_constraint_and_always_trigger(db):
    name, validated, definition = db.execute(
        "SELECT conname,convalidated,pg_get_constraintdef(oid) FROM pg_constraint"
        " WHERE conrelid='public.kala_gochara_authority'::regclass AND conname='kga_sealed_authority_ck'").fetchone()
    assert name == 'kga_sealed_authority_ck' and validated
    assert 'ka_gochara_authority_admissible(chart_id, authoritative_generation)' in definition
    assert db.execute("SELECT tgenabled FROM pg_trigger WHERE tgrelid='public.kala_gochara_authority'::regclass"
                      " AND tgname='kala_gochara_authority_no_truncate'").fetchone() == ('A',)


def test_followup_refuses_missing_sealed_constraint_before_creating_trigger(db):
    with pytest.raises(psycopg.errors.RaiseException, match='1382 preflight'):
        with db.transaction():
            db.execute('DROP TRIGGER kala_gochara_authority_no_truncate ON public.kala_gochara_authority')
            db.execute('ALTER TABLE public.kala_gochara_authority DROP CONSTRAINT kga_sealed_authority_ck')
            db.execute((MIGRATIONS / FOLLOWUP).read_text())
    # Savepoint rollback preserves the previously validated deployment.
    assert db.execute("SELECT tgenabled FROM pg_trigger WHERE tgrelid='public.kala_gochara_authority'::regclass"
                      " AND tgname='kala_gochara_authority_no_truncate'").fetchone() == ('A',)
