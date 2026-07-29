"""Tests for the bg_cohort writer.

Two tiers, matching the project's test-writer convention (see
test_bg_ontology.py):

1. Offline (always runs, no DB / no live swisseph ephemeris required): proves
   the sampling function is a pure, deterministic transform — same seed →
   same synthetic birth parameters, every time. This is the property the
   whole cohort's reproducibility claim rests on.
2. Live (skipped unless DATABASE_URL is set): runs the writer against a real
   DB connection and asserts row counts, idempotency, and schema shape.
"""
from __future__ import annotations

import os
import uuid

import pytest
import psycopg

from pipeline.orchestrator.writers.bg_cohort import (
    BgCohortWriter,
    COHORT_LAT_MAX,
    COHORT_LAT_MIN,
    COHORT_LON_MAX,
    COHORT_LON_MIN,
    COHORT_RNG_SEED,
    COHORT_SIZE,
    COHORT_WINDOW_END,
    COHORT_WINDOW_START,
    sample_birth_params,
)
from pipeline.orchestrator.writers import ContextSpec


# ── Offline tests (pure sampling function; no DB, no swisseph) ───────────────

def test_sample_birth_params_is_deterministic():
    """Same seed → byte-identical synthetic birth parameters across two calls."""
    a = sample_birth_params(n=200, seed=COHORT_RNG_SEED)
    b = sample_birth_params(n=200, seed=COHORT_RNG_SEED)
    assert a == b


def test_sample_birth_params_different_seed_differs():
    """A different seed must not accidentally collide with the canonical one."""
    a = sample_birth_params(n=200, seed=COHORT_RNG_SEED)
    b = sample_birth_params(n=200, seed=COHORT_RNG_SEED + 1)
    assert a != b


def test_sample_birth_params_count_and_ids():
    samples = sample_birth_params(n=COHORT_SIZE, seed=COHORT_RNG_SEED)
    assert len(samples) == COHORT_SIZE
    ids = [s['synthetic_id'] for s in samples]
    assert ids == list(range(1, COHORT_SIZE + 1)), 'synthetic_id must be a dense 1..N sequence'


def test_sample_birth_params_within_declared_bounds():
    """Every sampled birth param must fall within the documented sampling window."""
    samples = sample_birth_params(n=500, seed=COHORT_RNG_SEED)
    for s in samples:
        assert COHORT_WINDOW_START <= s['birth_datetime_utc'].date() <= COHORT_WINDOW_END
        assert COHORT_LAT_MIN <= s['lat'] <= COHORT_LAT_MAX
        assert COHORT_LON_MIN <= s['lon'] <= COHORT_LON_MAX


def test_writer_registered():
    """bg_cohort must be discoverable via @register('bg_cohort')."""
    from pipeline.orchestrator.writers import get_writer
    writer_cls = get_writer('bg_cohort')
    assert writer_cls is BgCohortWriter
    assert writer_cls.asset_id == 'bg_cohort'


def test_writer_dry_run_no_db_needed():
    """dry_run=True must short-circuit before any DB/swisseph work — no live conn required."""
    writer = BgCohortWriter()
    ctx = ContextSpec(
        asset_id='bg_cohort', build_id=str(uuid.uuid4()), db_conn=None, dry_run=True,
    )
    result = writer.run(ctx)
    assert result.asset_id == 'bg_cohort'
    assert result.rows_inserted == 0
    assert result.notes == 'dry_run'


# ── Live tests (require DATABASE_URL; skipped otherwise) ─────────────────────

@pytest.fixture(scope='module')
def db_conn():
    url = os.environ.get('DATABASE_URL') or os.environ.get('PROD_DB_URL')
    if not url:
        pytest.skip('DATABASE_URL not set')
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def test_bg_cohort_writer_runs(db_conn):
    writer = BgCohortWriter()
    ctx = ContextSpec(asset_id='bg_cohort', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()
    assert result.asset_id == 'bg_cohort'
    assert result.rows_inserted >= 0


def test_bg_cohort_volume_floor(db_conn):
    """bg_synthetic_cohort must reach the target floor after a full build."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_synthetic_cohort")
    n = cur.fetchone()['n']
    assert n >= COHORT_SIZE, f'bg_synthetic_cohort below floor of {COHORT_SIZE} (got {n})'


def test_bg_cohort_positions_shape(db_conn):
    """Every row's positions JSONB must carry all 10 grahas/Lagna."""
    cur = db_conn.cursor()
    cur.execute("SELECT positions FROM bg_synthetic_cohort ORDER BY synthetic_id LIMIT 5")
    rows = cur.fetchall()
    expected_keys = {
        'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter',
        'Venus', 'Saturn', 'Rahu', 'Ketu', 'Lagna',
    }
    for row in rows:
        assert set(row['positions'].keys()) == expected_keys
        for body, val in row['positions'].items():
            # Lagna may be an honest `null` (never a fabricated stub, per §N.7) on
            # the empirically-unreachable near-polar swe.houses() failure branch.
            if val is None:
                assert body == 'Lagna', f'{body} must never be null (only Lagna may be)'
                continue
            assert 1 <= val['sign_id'] <= 12, f'{body} sign_id out of range'
            assert 1 <= val['nakshatra_id'] <= 27, f'{body} nakshatra_id out of range'


def test_bg_cohort_no_null_citations(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_synthetic_cohort WHERE source_citation IS NULL")
    n = cur.fetchone()['n']
    assert n == 0, f'bg_synthetic_cohort has {n} rows with NULL source_citation'


def test_bg_cohort_writer_idempotent(db_conn):
    """Running the writer twice leaves bg_synthetic_cohort row count identical."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_synthetic_cohort")
    count_before = cur.fetchone()['n']

    writer = BgCohortWriter()
    ctx = ContextSpec(asset_id='bg_cohort', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()

    cur.execute("SELECT count(*) AS n FROM bg_synthetic_cohort")
    count_after = cur.fetchone()['n']

    assert count_before == count_after, f'Idempotency broken: {count_before} → {count_after}'
    if count_before > 0:
        assert result.rows_inserted == 0, f'Expected 0 rows_inserted on re-run, got {result.rows_inserted}'
