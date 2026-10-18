"""J-6r lane rehearsal across COMMITTED snapshots, on a guarded disposable database.

One oracle per production claim of ``j6r_rehearsal.rehearse_committed`` (PLAN
KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1 §4.4.6; SURROGATE G6 rollback rehearsal,
previous-head retention). Each test is built to fail under ONE planted reversion
named in its docstring. Synthetic admission metadata, as in test_j6r_rehearsal_db:
no sky stand-in, no production, no acceptance.
"""
import hashlib
import json
import uuid

import psycopg
import pytest

from scripts.kala_gochara_cutover import j6r_rehearsal as rehearsal
from ._disposable_db_guard import guarded_admin_connect
from .test_a53_inventory import CHART_ID, create_am5_database, drop_am5_database
from .test_a53_record_store import ADMIN_DSN
from .test_j6r_rehearsal_db import seed_rehearsal_lane, _legacy


@pytest.fixture
def lane():
    """A fresh database per test: committed rehearsals leave state behind."""
    admin, name, dsn = create_am5_database('j6r')
    conn = None
    try:
        conn = psycopg.connect(dsn, autocommit=True)
        manifests = seed_rehearsal_lane(conn)
        yield dsn, conn, manifests
    finally:
        if conn is not None:
            conn.close()
        drop_am5_database(admin, name)


def _head(conn):
    return conn.execute('SELECT * FROM public.kala_gochara_authority WHERE chart_id=%s', (CHART_ID,)).fetchall()


def _go(lane, **kw):
    dsn, _, mids = lane
    args = dict(chart_id=CHART_ID, expected_previous='3.0', generation='5.0', manifest_id=mids['5.0'],
                legacy_reader=_legacy, request={'event_classes': ['marriage']})
    args.update(kw)
    return rehearsal.rehearse_committed(dsn, **args)


def test_committed_flip_is_served_from_5_0_and_rollback_restores_the_exact_bytes(lane):
    """Claim: flip -> '5.0' served -> rollback -> bytes identical to before the flip (G6, §4.4.6).
    Planted reversion: the rollback swap leaves the head on 5.0 / the legacy bytes differ -> refused."""
    _, conn, mids = lane
    head_before = _head(conn)
    expected = _legacy(conn, CHART_ID, '3.0', event_classes=['marriage'])
    evidence = _go(lane)
    assert evidence['before']['sha256'] == evidence['after']['sha256'] == hashlib.sha256(expected).hexdigest()
    assert evidence['flipped']['generation'] == '5.0' and evidence['flipped']['manifest_id'] == mids['5.0']
    assert evidence['flipped']['sha256'] != evidence['before']['sha256']
    assert evidence['rollback_bytes_equal'] is True and evidence['previous_head_restored'] is True
    assert evidence['acceptance'] is None and evidence['production_activated'] is False
    assert _head(conn) == head_before          # complete row, audit columns included
    json.dumps(evidence, allow_nan=False)


def test_rollback_with_changed_bytes_is_refused_and_head_still_restored(lane):
    """Claim: a byte-different post-rollback response (even equal JSON) is never accepted.
    Planted reversion: compare parsed JSON instead of bytes."""
    _, conn, _ = lane
    head_before = _head(conn)
    calls = []

    def unstable(*args, **kwargs):
        calls.append(1)
        raw = _legacy(*args, **kwargs)
        return raw + b'\n' if len(calls) > 1 else raw
    with pytest.raises(rehearsal.RehearsalRefused, match='rollback_response_bytes_changed'):
        _go(lane, legacy_reader=unstable)
    assert _head(conn) == head_before


def test_previous_head_is_retained_never_deleted_by_the_flip(lane):
    """Claim: the previous head's rows survive the flip untouched (never deleted).
    Planted reversion: the flip also deletes the previous generation's rows."""
    _, conn, _ = lane
    original = rehearsal.compare_and_swap

    def flip_that_deletes(c, chart_id, expected, replacement):
        original(c, chart_id, expected, replacement)
        if replacement.generation == '5.0':
            c.execute('DELETE FROM public.kala_gochara_windows WHERE chart_id=%s', (chart_id,))
    rehearsal.compare_and_swap = flip_that_deletes
    try:
        with pytest.raises(rehearsal.RehearsalRefused, match='retained_rows_changed'):
            _go(lane)
    finally:
        rehearsal.compare_and_swap = original
    assert _head(conn)[0][1] == '3.0'          # head restored even though retention failed


def test_failure_after_the_committed_flip_restores_the_previous_head(lane, monkeypatch):
    """Claim: an error while the flip is committed cannot leave the lane on 5.0.
    Planted reversion: drop the finally-restore -> head stays on '5.0'."""
    _, conn, _ = lane
    head_before = _head(conn)
    original = rehearsal.serving_reader.read_authoritative
    calls = []

    def broken(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            assert conn.execute('SELECT authoritative_generation FROM public.kala_gochara_authority'
                                ' WHERE chart_id=%s', (CHART_ID,)).fetchone()[0] == '5.0'
            raise RuntimeError('reader failed after the committed flip')
        return original(*args, **kwargs)
    monkeypatch.setattr(rehearsal.serving_reader, 'read_authoritative', broken)
    with pytest.raises(RuntimeError, match='reader failed'):
        _go(lane)
    assert _head(conn) == head_before


@pytest.mark.parametrize('gen', ['5.1', '5.3'])
def test_candidate_and_test_slice_are_refused_before_any_flip(lane, gen):
    """Claim: only a sealed, published, non-test-slice 5.x manifest is rehearsed.
    Planted reversion: drop the seal join / the test_slice exclusion in _admissible_target."""
    _, conn, mids = lane
    head_before = _head(conn)
    with pytest.raises(rehearsal.RehearsalRefused, match='target_not_admissible'):
        _go(lane, generation=gen, manifest_id=mids[gen])
    assert _head(conn) == head_before


def test_reads_run_in_sessions_separate_from_the_writer(lane):
    """Claim: served responses are read from committed state by other sessions, not the writer's.
    Planted reversion: read through the writer connection -> refused."""
    evidence = _go(lane)
    assert evidence['separate_reader_sessions'] is True and evidence['reader_sessions'] >= 5


def test_maintenance_database_is_refused_before_any_authority_access(lane):
    """Claim: lane-only. Planted reversion: remove _require_lane from rehearse_committed."""
    from psycopg.conninfo import make_conninfo
    _, _, mids = lane
    with pytest.raises(rehearsal.RehearsalRefused, match='not_a_lane_database'):
        rehearsal.rehearse_committed(make_conninfo(ADMIN_DSN, dbname='postgres'), chart_id=CHART_ID,
                                     expected_previous='3.0', generation='5.0', manifest_id=mids['5.0'],
                                     legacy_reader=_legacy)
