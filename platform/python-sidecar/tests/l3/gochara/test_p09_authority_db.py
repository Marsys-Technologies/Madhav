"""P09 SQL/real-seal acceptance. Requires the disposable A5.3 CI database only."""
from pathlib import Path
import json
import pytest

from services.gochara_kernel import authority_head as ah
from services.gochara_kernel import serving_reader as rd
from services.gochara_kernel import scope_response as sr
from services.gochara_kernel import seal_flow
from routers import gochara_v5 as route
from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_window_verification_gate import world, CLS, _consistent_sky  # noqa: F401
from .test_w1_serving_reader import _sealed, _read, _unguarded

ROOT = Path(__file__).resolve().parents[5]


def _authority_schema(w):
    # 527's complete table definition; the A5.3 fixture does not load the serving table.
    w.conn.execute('CREATE TABLE IF NOT EXISTS public.kala_gochara_authority ('
                   "chart_id UUID PRIMARY KEY, authoritative_generation TEXT NOT NULL DEFAULT 'v1',"
                   'flipped_at TIMESTAMPTZ, flipped_by TEXT, evidence_ref TEXT)')
    exists = w.conn.execute("SELECT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid ="
                            " 'public.kala_gochara_authority'::regclass AND conname = 'kga_governed_generation_refused_ck')").fetchone()[0]
    if not exists:
        w.conn.execute((ROOT / 'platform/migrations/1236_gochara_authority_refuses_governed_generation.sql').read_text())
    migration = next(ROOT.glob('platform/migrations/*_gochara_sealed_authority.sql'))
    w.conn.execute(migration.read_text())


def test_new_constraint_refuses_unsealed_governed_head_and_admits_matching_published_seal(world):
    import psycopg
    w = world
    _authority_schema(w)
    w.conn.execute('INSERT INTO public.kala_gochara_authority(chart_id, authoritative_generation) VALUES (%s, %s)',
                   (CHART_ID, '3.0'))
    for mode in ('origin', 'replica'):
        with pytest.raises(psycopg.errors.CheckViolation):
            with w.conn.transaction():
                w.conn.execute(f"SET LOCAL session_replication_role = '{mode}'")
                w.conn.execute("UPDATE public.kala_gochara_authority SET authoritative_generation = '5.0'")
    _sealed(w)
    w.conn.execute('UPDATE public.kala_gochara_authority SET authoritative_generation = %s WHERE chart_id = %s',
                   (GEN, CHART_ID))
    assert w.conn.execute('SELECT authoritative_generation FROM public.kala_gochara_authority WHERE chart_id = %s',
                          (CHART_ID,)).fetchone()[0] == GEN
    definition = w.conn.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid ="
                                " 'public.kala_gochara_authority'::regclass AND conname = 'kga_sealed_authority_ck'").fetchone()[0]
    assert 'ka_gochara_authority_admissible' in definition
    with pytest.raises(psycopg.errors.CheckViolation):
        w.conn.execute("UPDATE public.kala_gochara_publication SET status = 'rolled_back' WHERE generation = %s", (GEN,))
    with pytest.raises(psycopg.errors.CheckViolation):
        w.conn.execute('DELETE FROM public.kala_gochara_authority WHERE chart_id = %s', (CHART_ID,))


def test_new_constraint_refuses_a_sealed_test_slice(world):
    import psycopg
    w = _sealed(world)
    _authority_schema(w)
    _unguarded(w, 'kala_gochara_publication',
               "UPDATE public.kala_gochara_publication SET input_generation_vector ="
               " input_generation_vector || '{\"test_slice\": false}'::jsonb WHERE generation = %s", (GEN,))
    with pytest.raises(psycopg.errors.CheckViolation):
        w.conn.execute('INSERT INTO public.kala_gochara_authority(chart_id, authoritative_generation) VALUES (%s, %s)',
                       (CHART_ID, GEN))


def test_rollback_rehearsal_restores_legacy_response_bytes_and_retains_both_generations(world):
    w = _sealed(world)
    _authority_schema(w)
    # Match the established pre-ledger 3.0 compatibility oracle. The A5.3
    # disposable legacy relation's shape is test_a53_inventory.py:297-298.
    w.conn.execute("CREATE TABLE public.kala_gochara_windows (id bigserial PRIMARY KEY, chart_id uuid NOT NULL,"
                   " event_class text, generation text NOT NULL, intensity numeric)")
    w.conn.execute("INSERT INTO public.kala_gochara_windows(chart_id, event_class, generation, intensity)"
                   " VALUES (%s, 'marriage', '3.0', NULL)", (CHART_ID,))
    w.conn.execute('INSERT INTO public.kala_gochara_authority(chart_id, authoritative_generation) VALUES (%s,%s)',
                   (CHART_ID, '3.0'))
    def legacy(conn, chart_id, generation, **kwargs):
        rows = conn.execute('SELECT generation, intensity FROM public.kala_gochara_windows'
                            ' WHERE chart_id = %s AND generation = %s ORDER BY id', (chart_id, generation)).fetchall()
        return json.dumps(rows, separators=(',', ':')).encode()
    before = rd.read_authoritative(w.conn, CHART_ID, legacy_reader=legacy)
    with w.conn.transaction():
        flip = ah.publish_head(w.conn, CHART_ID, generation=GEN, expected_head='3.0', evidence_ref='ci-flip', operator='test')
    assert rd.read_authoritative(w.conn, CHART_ID, legacy_reader=legacy)['generation'] == GEN
    with w.conn.transaction():
        ah.rollback_head(w.conn, CHART_ID, generation=flip['previous_head'], expected_head=GEN,
                         evidence_ref='ci-rollback', operator='test')
    assert rd.read_authoritative(w.conn, CHART_ID, legacy_reader=legacy) == before == b'[["3.0",null]]'
    assert w.conn.execute('SELECT generation, status FROM public.kala_gochara_publication ORDER BY generation').fetchall() == [
        (GEN, 'published')]


def test_reader_refuses_closed_stored_window_bounds(world):
    w = _sealed(world)
    _unguarded(w, 'ka_gochara_eval_window',
               "UPDATE public.ka_gochara_eval_window SET interval = tstzrange(lower(interval), upper(interval), '[]')")
    env = _read(w, event_classes=[CLS])
    assert env['refusal']['code'] == 'stored_window_bounds_incompatible'
    assert env['windows'] is None and env['classes'] is None


def test_half_open_window_check_rejects_new_incompatible_bounds(world):
    import psycopg
    w = _sealed(world)
    _authority_schema(w)
    with pytest.raises(psycopg.errors.CheckViolation):
        _unguarded(w, 'ka_gochara_eval_window',
                   "UPDATE public.ka_gochara_eval_window SET interval = tstzrange(lower(interval), upper(interval), '[]')")


@pytest.mark.parametrize('fault', ['orphan', 'score', 'standing'])
def test_near_miss_corruption_is_unavailable_instead_of_silently_served(world, fault):
    from psycopg import sql
    from .test_w1_serving_reader import _near_miss_tables, _near_miss_rows, _t
    w = _sealed(world)
    occ, obj = _near_miss_tables(w)
    _near_miss_rows(w, occ, obj, [(_t(1, 3), _t(1, 6))])
    if fault == 'orphan':
        w.conn.execute(sql.SQL('DELETE FROM public.{}').format(sql.Identifier(obj)))
    else:
        constraints = w.conn.execute('SELECT conname FROM pg_constraint WHERE conrelid = %s::regclass'
                                     " AND contype = 'c' AND pg_get_constraintdef(oid) LIKE %s ORDER BY conname",
                                     ('public.' + occ, '%' + fault + '%')).fetchall()
        for (name,) in constraints:
            w.conn.execute(sql.SQL('ALTER TABLE public.{} DROP CONSTRAINT {}').format(sql.Identifier(occ), sql.Identifier(name)))
        if fault == 'score':
            w.conn.execute(sql.SQL('UPDATE public.{} SET score = 0.75').format(sql.Identifier(occ)))
        else:
            w.conn.execute(sql.SQL("UPDATE public.{} SET standing = 'confirmed'").format(sql.Identifier(occ)))
    env = _read(w, event_classes=[CLS])
    assert env['near_miss_layer'] == 'schema_mismatch' and 'near_miss_intervals' not in env
    assert len(env['windows']) == 1


def test_new_constraint_refuses_a_seal_naming_a_different_manifest(world):
    import psycopg
    w = _sealed(world)
    _authority_schema(w)
    _unguarded(w, 'ka_gochara_generation_seal',
               "UPDATE public.ka_gochara_generation_seal SET manifest_id = '00000000-0000-0000-0000-000000000099'::uuid")
    with pytest.raises(psycopg.errors.CheckViolation):
        w.conn.execute('INSERT INTO public.kala_gochara_authority(chart_id, authoritative_generation) VALUES (%s,%s)',
                       (CHART_ID, GEN))
