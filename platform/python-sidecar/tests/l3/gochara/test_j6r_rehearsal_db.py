"""J-6r code preparation on guarded disposable Postgres, without a sky stand-in.

Seals below are synthetic admission metadata, installed before 1379. They do
not attest to computation or independent verification. The actual reader must
honestly report stale_binding (no search snapshot). This is deliberately
not the production/lane acceptance artifact required by J-6r and G6.
"""
import hashlib
import json
import uuid

import psycopg
from psycopg.types.json import Jsonb
import pytest

from scripts.kala_gochara_cutover import j6r_rehearsal as rehearsal
from ._disposable_db_guard import guarded_admin_connect
from .test_a53_inventory import CHART_ID, create_am5_database, drop_am5_database
from .test_a53_record_store import ADMIN_DSN
from .test_j6m_authority_admission_db import ROOT, MIGRATIONS

OTHER_CHART = str(uuid.UUID(int=900))


def seed_rehearsal_lane(conn):
    """Install the real 527/1236/1379/1382 chain over synthetic admission metadata; returns {generation: manifest_id}."""
    conn.execute('CREATE TABLE public.kala_gochara_windows (chart_id uuid)')
    conn.execute((ROOT / 'platform/supabase/migrations/527_kala_gochara_generation_authority.sql').read_text())
    conn.execute((MIGRATIONS / '1236_gochara_authority_refuses_governed_generation.sql').read_text())
    conn.execute("INSERT INTO public.kala_gochara_convention"
                 " (convention_id,zodiac,ayanamsha,sidereal_method,node_model,node_source,epoch_convention,"
                 " time_scale,house_system,ephemeris_mode,method_version)"
                 " VALUES ('j6r-metadata-only','fixture','fixture','fixture','fixture','fixture','fixture',"
                 " 'fixture','fixture','fixture','fixture')")
    manifests = {}
    with conn.transaction():
        conn.execute('ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER USER')
        for gen, status, vector, sealed in [
            ('3.0', 'published', {}, False),
            ('5.0', 'published', {'stored_scope': 'stored_non_moon', 'result_policy': 'all_null_candidate/1'}, True),
            ('5.1', 'candidate', {}, False),
            ('5.2', 'published', {}, False),
            ('5.3', 'published', {'stored_scope': 'test_slice'}, True),
        ]:
            mid = str(uuid.uuid4())
            manifests[gen] = mid
            conn.execute("INSERT INTO public.kala_gochara_publication"
                         " (manifest_id,chart_id,generation,writer_asset_id,convention_id,input_generation_vector,"
                         " ephemeris_backend,horizon,row_counts,content_digest,status)"
                         " VALUES (%s,%s,%s,'ka_gochara_v5','j6r-metadata-only',%s,'{}',"
                         " tstzrange('2025-01-01 UTC','2025-02-01 UTC','[)'),'{}','metadata-only',%s)",
                         (mid, CHART_ID, gen, Jsonb(vector), status))
            if sealed:
                conn.execute('INSERT INTO public.ka_gochara_generation_seal(chart_id,generation,manifest_id)'
                             ' VALUES (%s,%s,%s)', (CHART_ID, gen, mid))
        conn.execute('ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER USER')
    conn.execute("INSERT INTO public.kala_gochara_authority"
                 " (chart_id,authoritative_generation,flipped_at,flipped_by,evidence_ref)"
                 " VALUES (%s,'3.0','2025-01-01 UTC','fixture','retained-head')", (CHART_ID,))
    conn.execute("INSERT INTO public.kala_gochara_windows(chart_id,generation) VALUES (%s,'3.0'),(%s,'v1')",
                 (CHART_ID, OTHER_CHART))
    with conn.transaction():
        conn.execute((MIGRATIONS / '1379_gochara_sealed_authority.sql').read_text())
        conn.execute((MIGRATIONS / '1382_gochara_authority_no_truncate.sql').read_text())
    return manifests


@pytest.fixture(scope='module')
def rehearsal_database():
    admin, name, dsn = create_am5_database('j6r')
    conn = None
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        manifests = seed_rehearsal_lane(conn)
        yield conn, manifests
    finally:
        if conn is not None:
            conn.close()
        drop_am5_database(admin, name)


@pytest.fixture
def db(rehearsal_database):
    conn, manifests = rehearsal_database
    with conn.transaction(force_rollback=True):
        yield conn, manifests


def _legacy(conn, chart_id, generation, **request):
    # A deterministic transport fixture over stored rows, not fabricated chart
    # values, a production legacy adapter, or an ephemeris replacement.
    rows = conn.execute('SELECT generation FROM public.kala_gochara_windows'
                        ' WHERE chart_id=%s AND generation=%s ORDER BY generation', (chart_id, generation)).fetchall()
    return json.dumps({'generation': generation, 'stored_rows': rows}, separators=(',', ':')).encode()


def _run(db, **kw):
    conn, mids = db
    args = dict(chart_id=CHART_ID, expected_previous='3.0', generation='5.0',
                manifest_id=mids['5.0'], legacy_reader=_legacy, request={'event_classes': ['marriage']})
    args.update(kw)
    return rehearsal.rehearse(conn, **args)


def _heads(conn):
    return conn.execute('SELECT * FROM public.kala_gochara_authority ORDER BY chart_id').fetchall()


def test_flip_serves_exact_manifest_rollback_restores_bytes_and_retains_both_heads(db):
    conn, mids = db
    before_heads = _heads(conn)
    before = _legacy(conn, CHART_ID, '3.0')
    evidence = _run(db)
    assert evidence['schema'] == 'ky.j6r_prebuild_rehearsal/1'
    assert evidence['acceptance'] is None and evidence['production_activated'] is False
    assert evidence['target'] == {'generation': '5.0', 'manifest_id': mids['5.0']}
    assert evidence['before']['generation'] == evidence['after']['generation'] == '3.0'
    assert evidence['before']['sha256'] == evidence['after']['sha256'] == hashlib.sha256(before).hexdigest()
    assert evidence['flipped']['generation'] == '5.0'
    assert evidence['flipped']['manifest_id'] == mids['5.0']
    assert evidence['flipped']['class_completeness'] == {'marriage': 'stale_binding'}
    assert evidence['rollback_bytes_equal'] is True
    assert evidence['retained_rows_equal'] is True
    assert evidence['outside_horizon_refusal'] == 'outside_served_horizon'
    assert evidence['retained_before'] == evidence['retained_after_flip'] == evidence['retained_after_rollback']
    assert evidence['retained_before']['kala_gochara_publication']['rows'] == 5
    assert evidence['retained_before']['kala_gochara_windows']['rows'] == 1
    assert _heads(conn) == before_heads  # includes all audit columns
    assert conn.execute('SELECT generation FROM public.kala_gochara_windows WHERE chart_id=%s',
                        (OTHER_CHART,)).fetchall() == [('v1',)]
    json.dumps(evidence, allow_nan=False)


@pytest.mark.parametrize('gen', ['5.1', '5.2', '5.3', '9.9'])
def test_candidate_unsealed_slice_and_missing_target_refused_without_mutation(db, gen):
    conn, mids = db
    before = _heads(conn)
    with pytest.raises(rehearsal.RehearsalRefused, match='target_not_admissible'):
        _run(db, generation=gen, manifest_id=mids.get(gen, str(uuid.uuid4())))
    assert _heads(conn) == before


def test_exact_manifest_and_expected_previous_are_mandatory(db):
    conn, _ = db
    before = _heads(conn)
    with pytest.raises(rehearsal.RehearsalRefused, match='target_not_admissible'):
        _run(db, manifest_id=str(uuid.uuid4()))
    with pytest.raises(rehearsal.RehearsalRefused, match='previous_head_changed'):
        _run(db, expected_previous='v1')
    assert _heads(conn) == before


def test_missing_explicit_previous_head_is_not_invented(db):
    conn, _ = db
    conn.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,))
    with pytest.raises(rehearsal.RehearsalRefused, match='previous_head_missing'):
        _run(db)
    assert conn.execute('SELECT count(*) FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,)).fetchone()[0] == 0


def test_compare_and_swap_refuses_stale_audit_metadata_as_well_as_generation(db):
    conn, _ = db
    previous = rehearsal.read_head(conn, CHART_ID)
    conn.execute("UPDATE public.kala_gochara_authority SET evidence_ref='different' WHERE chart_id=%s", (CHART_ID,))
    with pytest.raises(rehearsal.RehearsalRefused, match='head_compare_and_swap_conflict'):
        rehearsal.compare_and_swap(conn, CHART_ID, previous, previous)
    assert rehearsal.read_head(conn, CHART_ID).evidence_ref == 'different'


def test_byte_difference_is_detected_even_for_semantically_equal_json_and_scope_rolls_back(db):
    conn, _ = db
    before = _heads(conn)
    calls = []
    def unstable(*args, **kwargs):
        calls.append(1)
        raw = _legacy(*args, **kwargs)
        return raw if len(calls) == 1 else raw + b'\n'
    with pytest.raises(rehearsal.RehearsalRefused, match='rollback_response_bytes_changed'):
        _run(db, legacy_reader=unstable)
    assert len(calls) == 2 and _heads(conn) == before


def test_failure_during_reader_probe_rolls_back_and_preserves_callers_work(db, monkeypatch):
    conn, _ = db
    conn.execute("UPDATE public.kala_gochara_authority SET evidence_ref='caller-work' WHERE chart_id=%s", (CHART_ID,))
    before = _heads(conn)
    original = rehearsal.serving_reader.read_authoritative
    calls = []
    def broken(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            assert rehearsal.read_head(conn, CHART_ID).generation == '5.0'
            raise RuntimeError('reader failed after flip')
        return original(*args, **kwargs)
    monkeypatch.setattr(rehearsal.serving_reader, 'read_authoritative', broken)
    with pytest.raises(RuntimeError, match='reader failed'):
        _run(db)
    assert len(calls) == 2
    assert _heads(conn) == before


def test_retention_detector_rejects_mutated_rows_and_rolls_them_back(db):
    conn, _ = db
    before = _heads(conn)
    calls = []
    def destructive(c, chart_id, generation, **request):
        calls.append(1)
        if len(calls) == 1:
            c.execute('DELETE FROM public.kala_gochara_windows WHERE chart_id=%s', (chart_id,))
        return _legacy(c, chart_id, generation, **request)
    with pytest.raises(rehearsal.RehearsalRefused, match='retained_rows_changed'):
        _run(db, legacy_reader=destructive)
    assert _heads(conn) == before
    assert conn.execute('SELECT count(*) FROM public.kala_gochara_windows WHERE chart_id=%s', (CHART_ID,)).fetchone()[0] == 1


def test_rehearsal_never_commits_an_autocommit_connection(rehearsal_database):
    conn, mids = rehearsal_database
    assert conn.autocommit
    before = _heads(conn)
    _run((conn, mids))
    assert _heads(conn) == before


def test_even_successful_probe_side_effects_are_discarded(rehearsal_database):
    conn, mids = rehearsal_database
    assert conn.autocommit
    def side_effect(*args, **kwargs):
        conn.execute('CREATE TABLE IF NOT EXISTS public.j6r_probe_side_effect (n integer)')
        conn.execute('INSERT INTO public.j6r_probe_side_effect VALUES (1)')
        return _legacy(*args, **kwargs)
    _run((conn, mids), legacy_reader=side_effect)
    assert conn.execute("SELECT to_regclass('public.j6r_probe_side_effect')").fetchone()[0] is None


@pytest.mark.parametrize('corruption', ['manifest', 'generation', 'refusal', 'horizon'])
def test_served_identity_admission_and_horizon_are_measured_not_assumed(db, monkeypatch, corruption):
    conn, _ = db
    before = _heads(conn)
    original = rehearsal.serving_reader.read_authoritative
    def corrupt(*args, **kwargs):
        result = original(*args, **kwargs)
        if isinstance(result, dict):
            if corruption == 'manifest':
                result['manifest_id'] = str(uuid.uuid4())
            elif corruption == 'generation':
                result['generation'] = '9.9'
            elif corruption == 'refusal':
                result['refusal'] = {'code': 'not_sealed'}
            elif 'at_instant' in kwargs:
                result['refusal'] = None
        return result
    monkeypatch.setattr(rehearsal.serving_reader, 'read_authoritative', corrupt)
    reason = 'outside_horizon_probe_failed' if corruption == 'horizon' else 'flipped_reader_identity_or_admission_failed'
    with pytest.raises(rehearsal.RehearsalRefused, match=reason):
        _run(db)
    assert _heads(conn) == before


def test_maintenance_database_is_refused_before_authority_access(rehearsal_database):
    # conn.info.dsn omits the password required by CI's disposable Postgres.
    with guarded_admin_connect(ADMIN_DSN) as maintenance:
        with pytest.raises(rehearsal.RehearsalRefused, match='not_a_lane_database'):
            _run((maintenance, rehearsal_database[1]))
