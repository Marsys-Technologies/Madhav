"""Tests for the bg_cohort writer.

Three tiers, matching the project's test-writer convention (see
test_bg_ontology.py):

1. Offline (always runs, no DB / no live swisseph ephemeris required): proves
   the sampling function is a pure, deterministic transform — same seed →
   same synthetic birth parameters, every time — and (KALA_W2_FIELD_DESIGN_v1_0
   §6.3, ANTARYĀMIN ADJUDICATION-1) that `compute_md_lord_chain()` is a pure,
   correct age-interval Vimśottarī chain over an already-stored Moon longitude.
2. Cross-check (skipped if the full PyJHora/swisseph stack is unavailable):
   reproduces the shipped dasha engine's own real output for the native's
   FORENSIC-anchored birth — a genuine worked example, not just internal
   self-consistency (§6.3 acceptance test 1).
3. Live (skipped unless DATABASE_URL is set): runs the writer against a real
   DB connection and asserts row counts, idempotency, and schema shape for
   both bg_synthetic_cohort and bg_synthetic_cohort_md.
"""
from __future__ import annotations

import os
import uuid

import pytest
import psycopg

from pipeline.orchestrator.writers.bg_cohort import (
    BgCohortWriter,
    CHAIN_VERSION,
    COHORT_LAT_MAX,
    COHORT_LAT_MIN,
    COHORT_LON_MAX,
    COHORT_LON_MIN,
    COHORT_RNG_SEED,
    COHORT_SIZE,
    COHORT_WINDOW_END,
    COHORT_WINDOW_START,
    MdChainAuthorityDivergence,
    NAK_LORD_CYCLE,
    VIMSHOTTARI_YEARS,
    compute_md_lord_chain,
    compute_synthetic_positions,
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


# ── Offline tests: compute_md_lord_chain() — pure, no DB/swisseph ────────────
# KALA_W2_FIELD_DESIGN_v1_0.md §6.3, ANTARYĀMIN ADJUDICATION-1.

def _positions_for(moon_lon: float) -> dict:
    """Build a minimal positions dict with a Moon at the given sidereal
    longitude, its nakshatra_id computed the SAME way _parse_sidereal does
    (so the guard never spuriously fires in these synthetic fixtures)."""
    one_star = 360.0 / 27.0
    nak_id = int(moon_lon / one_star) + 1
    return {"Moon": {"sidereal_longitude": moon_lon, "nakshatra_id": nak_id}}


class TestConstants:
    def test_vimshottari_years_sum_to_120(self):
        assert sum(VIMSHOTTARI_YEARS.values()) == 120

    def test_vimshottari_years_nine_classical_lords(self):
        assert set(VIMSHOTTARI_YEARS.keys()) == {
            'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu',
        }

    def test_vimshottari_years_classical_values(self):
        # Verified byte-identical to pyjhora_adapter/dashas.py::_VIMSHOTTARI_YEARS
        # (keyed there by PyJHora planet id via _names.py::PLANET_NAMES).
        assert VIMSHOTTARI_YEARS == {
            'Sun': 6, 'Moon': 10, 'Mars': 7, 'Mercury': 17, 'Jupiter': 16,
            'Venus': 20, 'Saturn': 19, 'Rahu': 18, 'Ketu': 7,
        }

    def test_nak_lord_cycle_matches_names_py(self):
        # Verified byte-identical to pyjhora_adapter/_names.py::_NAK_LORD_CYCLE.
        assert NAK_LORD_CYCLE == [
            'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
        ]


class TestComputeMdLordChainHonestEmpty:
    def test_positions_none(self):
        assert compute_md_lord_chain(None) == []

    def test_positions_empty_dict(self):
        assert compute_md_lord_chain({}) == []

    def test_moon_key_missing(self):
        assert compute_md_lord_chain({'Sun': {'sidereal_longitude': 10.0, 'nakshatra_id': 1}}) == []

    def test_moon_is_none(self):
        # Mirrors the honest-null Lagna case in compute_synthetic_positions —
        # Moon is never expected to be null in practice, but a single
        # malformed row must degrade to empty, never crash the batch.
        assert compute_md_lord_chain({'Moon': None}) == []


class TestComputeMdLordChainGuard:
    def test_divergence_raises(self):
        """A stored nakshatra_id that disagrees with the derived one is a
        halt-worthy §N.5 bug, never a silently-absorbed divergence."""
        positions = {'Moon': {'sidereal_longitude': 327.055230133129, 'nakshatra_id': 1}}
        with pytest.raises(MdChainAuthorityDivergence):
            compute_md_lord_chain(positions)

    def test_consistent_parse_never_raises(self):
        # _positions_for() computes nakshatra_id the same way _parse_sidereal
        # does, so the guard must never fire on internally-consistent input.
        for nak_id in range(1, 28):
            one_star = 360.0 / 27.0
            moon_lon = (nak_id - 1) * one_star + one_star / 2  # mid-nakshatra
            compute_md_lord_chain(_positions_for(moon_lon))  # must not raise


class TestComputeMdLordChainShape:
    def test_general_case_ten_rows(self):
        """A moon partway through its nakshatra (the overwhelmingly common
        case) produces exactly 10 rows."""
        chain = compute_md_lord_chain(_positions_for(327.055230133129))
        assert len(chain) == 10
        assert [r['md_index'] for r in chain] == list(range(1, 11))

    def test_measure_zero_case_nine_rows(self):
        """Moon sitting exactly on a nakshatra boundary (frac == 0.0) yields
        exactly 9 rows — no residual first-lord repeat needed."""
        one_star = 360.0 / 27.0
        moon_lon = 5 * one_star  # exactly on nakshatra 6's start (0-based idx 5)
        chain = compute_md_lord_chain(_positions_for(moon_lon))
        assert len(chain) == 9
        assert [r['md_index'] for r in chain] == list(range(1, 10))
        assert chain[0]['is_partial'] is False

    def test_gapless_half_open_cover(self):
        """start(1)=0, start(k+1)=end(k), max(end)=120 exactly — the
        contiguous cover the half-open age-join predicate depends on."""
        chain = compute_md_lord_chain(_positions_for(200.123456))
        assert chain[0]['start_age_years'] == 0.0
        for a, b in zip(chain, chain[1:]):
            assert a['end_age_years'] == b['start_age_years']
        assert chain[-1]['end_age_years'] == 120.0

    def test_is_partial_flags(self):
        chain = compute_md_lord_chain(_positions_for(327.055230133129))
        assert chain[0]['is_partial'] is True          # birth MD balance
        assert all(r['is_partial'] is False for r in chain[1:9])  # full lords 2..9
        assert chain[9]['is_partial'] is True          # the cycle-restart row

    def test_md_full_years_matches_classical_length(self):
        chain = compute_md_lord_chain(_positions_for(327.055230133129))
        for row in chain:
            assert row['md_full_years'] == VIMSHOTTARI_YEARS[row['md_lord']]

    def test_lord_sequence_is_the_classical_cycle_no_repeats_within_9(self):
        chain = compute_md_lord_chain(_positions_for(88.0))
        first_nine_lords = [r['md_lord'] for r in chain[:9]]
        assert len(set(first_nine_lords)) == 9, 'first 9 rows must be all distinct lords'
        assert set(first_nine_lords) == set(VIMSHOTTARI_YEARS.keys())

    def test_deterministic_property_across_many_longitudes(self):
        """Property test over a dense grid of longitudes (every 0.7°, avoiding
        exact boundary points): the chain is always gapless, always covers
        [0, 120], and every md_lord is one of the 9 classical names."""
        lon = 0.01
        while lon < 359.99:
            chain = compute_md_lord_chain(_positions_for(lon))
            assert len(chain) in (9, 10)
            assert chain[0]['start_age_years'] == 0.0
            assert abs(chain[-1]['end_age_years'] - 120.0) < 1e-9
            for a, b in zip(chain, chain[1:]):
                assert abs(a['end_age_years'] - b['start_age_years']) < 1e-9
            for row in chain:
                assert row['md_lord'] in VIMSHOTTARI_YEARS
            lon += 0.7


# ── Cross-check tier: real worked example against the shipped dasha engine ──
# KALA_W2_FIELD_DESIGN_v1_0.md §6.3 acceptance test 1. Requires the full
# PyJHora/swisseph stack; skipped gracefully if unavailable (this file's
# other tiers are deliberately dependency-free — see module docstring).

def test_md_chain_matches_pyjhora_worked_example_native():
    """The native's own FORENSIC-anchored birth (Abhisek Mohanty, 1984-02-05
    10:43 IST Bhubaneswar — CLAUDE.md §B: Moon in Purva Bhadrapada) is a real,
    independently-computed worked example — not merely internal
    self-consistency — that our pure age-chain must reproduce to within the
    §6.3-specified 0.05-year tolerance (the expected PyJHora-vs-`dashas.py`
    365.256364-vs-365.2425 year-length discrepancy)."""
    pytest.importorskip('swisseph')
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    try:
        from pyjhora_adapter import compute_chart
        from pyjhora_adapter.dashas import compute_dashas
        from pyjhora_adapter._jhora import drik, utils as jhora_utils
    except ImportError:
        pytest.skip('pyjhora_adapter / PyJHora stack not available')

    inputs = {
        'datetime_iso': '1984-02-05T10:43:00',
        'tz_offset_hours': 5.5,
        'latitude_deg': 20.2961,
        'longitude_deg': 85.8245,
        'place_name': 'Bhubaneswar',
        'subject_label': 'native_worked_example',
    }
    chart = compute_chart(inputs=inputs, ayanamsha_id='lahiri', computed_at_iso='2026-06-01T00:00:00+00:00')
    moon = next(p for p in chart['planets'] if p['name'] == 'Moon')

    # FORENSIC anchor (CLAUDE.md §B): Moon = Purva Bhadrapada, lord Jupiter.
    assert moon['nakshatra'] == 'Purva Bhadrapada'
    assert moon['nakshatra_lord'] == 'Jupiter'

    positions = {'Moon': {
        'sidereal_longitude': moon['longitude_deg'],
        'nakshatra_id': moon['nakshatra_id'],
    }}
    chain = compute_md_lord_chain(positions)
    assert len(chain) == 10
    assert chain[0]['md_lord'] == 'Jupiter'
    assert chain[0]['md_full_years'] == 16

    # Independent cross-check via the shipped dasha engine's own computation.
    # jd convention per pyjhora_adapter/compute.py's own module docstring:
    # PyJHora's dasha/chart stack consumes a LOCAL wall-clock JD (its Place's
    # tz drives the internal UT conversion) — NOT a pre-converted UTC jd.
    dob = drik.Date(1984, 2, 5)
    tob = (10, 43, 0)
    jd_local = jhora_utils.julian_day_number(dob, tob)
    dashas = compute_dashas(jd_local, 'lahiri', lat=20.2961, lon=85.8245, tz=5.5)
    seq = dashas['mahadasha_sequence']

    # Same lord order, same years per lord, for all 9 mahadashas.
    assert [row['lord'] for row in seq] == [chain[i]['md_lord'] for i in range(9)]
    assert [row['years'] for row in seq] == [chain[i]['md_full_years'] for i in range(9)]

    # Row 1's length (the birth MD balance) must match the engine's own
    # first-boundary jd, converted to years via its own sidereal_year
    # constant, within the design doc's 0.05-year tolerance.
    sidereal_year = 365.256364
    balance_years = (seq[1]['start_jd'] - jd_local) / sidereal_year
    assert abs(chain[0]['end_age_years'] - balance_years) <= 0.05, (
        f"chain balance {chain[0]['end_age_years']} vs engine balance {balance_years}"
    )


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


# ── Live tests: bg_synthetic_cohort_md (§6.3 second-pass table) ──────────────

def test_bg_synthetic_cohort_md_writer_runs(db_conn):
    writer = BgCohortWriter()
    ctx = ContextSpec(asset_id='bg_cohort', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()
    assert 'md_rows_inserted' in result.notes
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_synthetic_cohort_md")
    n = cur.fetchone()['n']
    assert n > 0, 'bg_synthetic_cohort_md must be populated after a full build'


def test_bg_synthetic_cohort_md_volume(db_conn):
    """~100,000 rows: 10 per synthetic chart, 9 in the measure-zero boundary
    case (§6.3). Overwhelmingly close to 10 * COHORT_SIZE."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_synthetic_cohort_md")
    n = cur.fetchone()['n']
    assert n >= 9 * COHORT_SIZE, f'bg_synthetic_cohort_md volume too low (got {n})'
    assert n <= 10 * COHORT_SIZE, f'bg_synthetic_cohort_md volume too high (got {n})'


def test_bg_synthetic_cohort_md_rows_per_chart(db_conn):
    """Every synthetic_id has either 9 or 10 chain rows — never anything else."""
    cur = db_conn.cursor()
    cur.execute(
        """
        SELECT n_rows, count(*) AS n_charts
        FROM (
            SELECT synthetic_id, count(*) AS n_rows
            FROM bg_synthetic_cohort_md
            GROUP BY synthetic_id
        ) t
        GROUP BY n_rows
        """
    )
    rows = cur.fetchall()
    assert rows, 'expected at least one synthetic_id with chain rows'
    for row in rows:
        assert row['n_rows'] in (9, 10), f"unexpected chain length {row['n_rows']}"


def test_bg_synthetic_cohort_md_gapless_half_open_cover(db_conn):
    """Per §6.3 acceptance test 3: start(1)=0, start(k+1)=end(k), max(end)=120,
    checked over a sample of synthetic_ids."""
    cur = db_conn.cursor()
    cur.execute(
        """
        SELECT synthetic_id, md_index, start_age_years, end_age_years
        FROM bg_synthetic_cohort_md
        WHERE synthetic_id IN (SELECT synthetic_id FROM bg_synthetic_cohort ORDER BY synthetic_id LIMIT 50)
        ORDER BY synthetic_id, md_index
        """
    )
    rows = cur.fetchall()
    by_chart: dict[int, list] = {}
    for row in rows:
        by_chart.setdefault(row['synthetic_id'], []).append(row)

    assert len(by_chart) > 0
    for synthetic_id, chain in by_chart.items():
        assert float(chain[0]['start_age_years']) == 0.0, synthetic_id
        for a, b in zip(chain, chain[1:]):
            assert float(a['end_age_years']) == float(b['start_age_years']), synthetic_id
        assert float(chain[-1]['end_age_years']) == 120.0, synthetic_id


def test_bg_synthetic_cohort_md_age_join_returns_exactly_one_row(db_conn):
    """§6.3 acceptance test 3's second half: for reference ages spread over
    [0, 120), the half-open age join returns exactly one chain row per chart."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_synthetic_cohort")
    n_total = cur.fetchone()['n']
    assert n_total > 0

    for ref_age in (0.0, 7.5, 25.0, 50.0, 75.0, 100.0, 119.999):
        cur.execute(
            """
            SELECT count(*) AS n
            FROM bg_synthetic_cohort_md
            WHERE %(age)s >= start_age_years AND %(age)s < end_age_years
            """,
            {'age': ref_age},
        )
        n = cur.fetchone()['n']
        assert n == n_total, f'age join at ref_age={ref_age}: expected {n_total} rows, got {n}'


def test_bg_synthetic_cohort_md_stored_parse_agreement(db_conn):
    """§6.3 acceptance test 2: the chain's row-1 lord must be derivable from
    the SAME Moon nakshatra_id already stored in bg_synthetic_cohort.positions
    — i.e. the L0-authority guard never fires across the live cohort."""
    cur = db_conn.cursor()
    cur.execute(
        """
        SELECT c.synthetic_id, c.positions->'Moon'->>'nakshatra_id' AS moon_nak_id,
               m.md_lord
        FROM bg_synthetic_cohort c
        JOIN bg_synthetic_cohort_md m
          ON m.synthetic_id = c.synthetic_id AND m.md_index = 1
        LIMIT 2000
        """
    )
    rows = cur.fetchall()
    assert rows, 'expected joinable rows'
    for row in rows:
        nak_id = int(row['moon_nak_id'])
        expected_lord = NAK_LORD_CYCLE[(nak_id - 1) % 9]
        assert row['md_lord'] == expected_lord, (
            f"synthetic_id={row['synthetic_id']}: nak_id={nak_id} expects {expected_lord}, "
            f"got {row['md_lord']}"
        )


def test_bg_synthetic_cohort_md_chain_version(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT DISTINCT chain_version FROM bg_synthetic_cohort_md")
    versions = {row['chain_version'] for row in cur.fetchall()}
    assert versions == {CHAIN_VERSION}, f'expected only {CHAIN_VERSION!r}, got {versions}'


def test_bg_synthetic_cohort_md_writer_idempotent(db_conn):
    """Re-running the writer must insert zero new bg_synthetic_cohort_md rows."""
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_synthetic_cohort_md")
    count_before = cur.fetchone()['n']

    writer = BgCohortWriter()
    ctx = ContextSpec(asset_id='bg_cohort', build_id=str(uuid.uuid4()), db_conn=db_conn)
    result = writer.run(ctx)
    db_conn.commit()

    cur.execute("SELECT count(*) AS n FROM bg_synthetic_cohort_md")
    count_after = cur.fetchone()['n']

    assert count_before == count_after, f'MD-chain idempotency broken: {count_before} → {count_after}'
    if count_before > 0:
        assert 'md_rows_inserted=0' in result.notes, result.notes
