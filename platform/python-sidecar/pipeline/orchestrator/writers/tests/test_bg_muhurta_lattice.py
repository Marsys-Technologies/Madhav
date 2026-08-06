"""Tests for the bg_muhurta_lattice writer.

Two tiers, matching the project's test-writer convention (see
test_bg_sky_calendar.py):

1. Offline (always runs, no DB required; swisseph IS required and is a
   project dependency): proves the horizon/substep-planning functions are pure,
   deterministic transforms, and that compute_day_factors produces well-formed,
   internally consistent, citation-carrying rows for real calendar days.
2. Live (skipped unless DATABASE_URL is set): runs the writer against a real
   DB connection and asserts row counts, idempotency, and schema shape.
"""
from __future__ import annotations

import os
import uuid
from datetime import date

import pytest
import psycopg

from pipeline.orchestrator.writers.bg_muhurta_lattice import (
    BgMuhurtaLatticeWriter,
    FORWARD_HORIZON_YEARS,
    REFERENCE_LAT,
    REFERENCE_LON,
    REFERENCE_TZ_OFFSET_MINUTES,
    compute_agnivasa_convention_b,
    compute_day_factors,
    compute_horizon,
    plan_year_substeps,
    _year_range,
)
from pipeline.orchestrator.writers import ContextSpec, SubStep

swe = pytest.importorskip("swisseph", reason="swisseph is a project dependency; skip only if truly absent")


# ── Offline tests: compute_horizon (pure function) ────────────────────────────

def test_compute_horizon_is_deterministic():
    a = compute_horizon(today=date(2026, 7, 30))
    b = compute_horizon(today=date(2026, 7, 30))
    assert a == b


def test_compute_horizon_rolling_forward_no_fixed_history():
    """Unlike bg_sky_calendar's fixed HISTORY_START=1900, this asset's horizon
    starts at 'today' itself -- a rolling FORWARD-only election substrate."""
    start, end = compute_horizon(today=date(2026, 7, 30))
    assert start == date(2026, 7, 30)
    assert end.year == 2026 + FORWARD_HORIZON_YEARS


def test_compute_horizon_rolls_forward_with_today():
    _, end_2026 = compute_horizon(today=date(2026, 7, 30))
    _, end_2028 = compute_horizon(today=date(2028, 7, 30))
    assert end_2028 > end_2026


def test_compute_horizon_leap_day_edge_case():
    start, end = compute_horizon(today=date(2024, 2, 29))
    assert end.day in (28, 29)


def test_forward_horizon_is_five_years_per_brief():
    """Brief §2 explicitly specifies '~5y' for this asset, distinct from
    bg_sky_calendar's own deliberately-different 10y choice."""
    assert FORWARD_HORIZON_YEARS == 5


# ── Offline tests: plan_year_substeps (pure function) ─────────────────────────

def test_plan_year_substeps_single_year():
    steps = plan_year_substeps(date(2026, 3, 1), date(2026, 9, 1))
    assert [s.key for s in steps] == ["year:2026"]


def test_plan_year_substeps_spans_multiple_years():
    steps = plan_year_substeps(date(2026, 7, 30), date(2031, 7, 30))
    assert [s.key for s in steps] == [f"year:{y}" for y in range(2026, 2032)]


def test_year_range_clips_to_horizon():
    start, end = date(2026, 7, 30), date(2031, 7, 30)
    # First touched year is clipped to start, not Jan 1.
    r_start, r_end = _year_range(2026, start, end)
    assert r_start == start
    assert r_end == date(2027, 1, 1)
    # A fully-interior year covers the whole calendar year.
    r_start, r_end = _year_range(2028, start, end)
    assert r_start == date(2028, 1, 1)
    assert r_end == date(2029, 1, 1)
    # Last touched year is clipped to end, not Dec 31/Jan 1.
    r_start, r_end = _year_range(2031, start, end)
    assert r_start == date(2031, 1, 1)
    assert r_end == end


# ── Offline tests: compute_agnivasa_convention_b (pure function, ADJUDICATION-16) ──
#
# Formula: remainder = (tithi_id + 1 + vara_id) mod 4
#   {0, 3} → Prithvi (auspicious)
#   1       → Akasha (inauspicious)
#   2       → Patala (inauspicious)
#
# Encoding: tithi_id 1-30 (MC §1 continuous count);
#           vara_id 1=Sunday … 7=Saturday (platform-wide VARA_NAMES convention).

def test_convention_b_remainder_0_yields_prithvi():
    # Example: tithi=1 vara=1 → (1+1+1)%4=3 → Prithvi
    # Need remainder=0: (tithi_id+1+vara_id)%4==0 → try tithi=1 vara=6: (1+1+6)%4=0
    element, valence = compute_agnivasa_convention_b(tithi_id=1, vara_id=6)
    assert element == "Prithvi"
    assert valence == "auspicious"


def test_convention_b_remainder_3_yields_prithvi():
    # tithi=1, vara=1: (1+1+1)%4=3 → Prithvi
    element, valence = compute_agnivasa_convention_b(tithi_id=1, vara_id=1)
    assert element == "Prithvi"
    assert valence == "auspicious"


def test_convention_b_remainder_1_yields_akasha():
    # tithi=1, vara=7: (1+1+7)%4=1 → Akasha (prana-nasha inauspicious)
    element, valence = compute_agnivasa_convention_b(tithi_id=1, vara_id=7)
    assert element == "Akasha"
    assert valence == "inauspicious"


def test_convention_b_remainder_2_yields_patala():
    # tithi=1, vara=4: (1+1+4)%4=2 → Patala (artha-nasha inauspicious)
    element, valence = compute_agnivasa_convention_b(tithi_id=1, vara_id=4)
    assert element == "Patala"
    assert valence == "inauspicious"


def test_convention_b_all_four_remainders_exhausted():
    """Enumerate all 28 (tithi 1-7 × vara 1-7) combinations and confirm
    every result is one of the three valid elements with the correct valence."""
    seen_remainders: set[int] = set()
    for tithi_id in range(1, 31):
        for vara_id in range(1, 8):
            element, valence = compute_agnivasa_convention_b(tithi_id, vara_id)
            assert element in ("Prithvi", "Akasha", "Patala"), f"unexpected element {element!r}"
            if element == "Prithvi":
                assert valence == "auspicious"
            else:
                assert valence == "inauspicious"
            seen_remainders.add((tithi_id + 1 + vara_id) % 4)
    assert seen_remainders == {0, 1, 2, 3}, "all four remainders must be reachable"


def test_convention_b_is_deterministic():
    a = compute_agnivasa_convention_b(8, 3)
    b = compute_agnivasa_convention_b(8, 3)
    assert a == b


def test_convention_b_distinguishable_from_convention_a():
    """Convention B (tithi+vara-keyed, 3-location) and Convention A
    (tithi-only, 4-element) must disagree on at least ONE tithi×vara pair —
    proving they are genuinely distinct reckoning systems, not duplicates."""
    from panchang_engine.shastra_tables import AGNI_VASA_TABLE
    disagreements = 0
    for tithi_id in range(1, 31):
        b_element, _ = compute_agnivasa_convention_b(tithi_id, vara_id=3)  # Budhavara
        a_element = AGNI_VASA_TABLE.get(tithi_id)
        if b_element != a_element:
            disagreements += 1
    assert disagreements > 0, (
        "Convention A and Convention B must produce different results on at least "
        "one tithi×vara pair — otherwise they are duplicates, not distinct conventions"
    )


# ── Offline tests: compute_day_factors over real days (no DB) ────────────────

@pytest.fixture(scope="module", autouse=True)
def _set_lahiri():
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def test_compute_day_factors_is_deterministic():
    a = compute_day_factors(date(2026, 8, 15))
    b = compute_day_factors(date(2026, 8, 15))
    assert [(r.factor_family, r.factor_key, r.start_utc, r.end_utc) for r in a] == \
           [(r.factor_family, r.factor_key, r.start_utc, r.end_utc) for r in b]


def test_compute_day_factors_covers_all_four_families():
    """A real day must yield at least the two always-present families
    (agnivasa: exactly 1/day; kalam: several/day) and, over a sampled week,
    every one of the four documented families must appear at least once."""
    families_seen: set[str] = set()
    for offset in range(7):
        rows = compute_day_factors(date(2026, 8, 1 + offset))
        families_seen.update(r.factor_family for r in rows)
    assert families_seen == {"agnivasa", "combination_yoga", "kalam", "ghati_muhurta"}


def test_compute_day_factors_agnivasa_two_rows_per_day():
    """Two Agnivāsa rows per day since ADJUDICATION-16:
    Convention A (agni_vasa, AGNI_VASA_TABLE, tithi-only, 4-element,
    computed_uncited_convention) and Convention B (agni_vasa_mc_arithmetic,
    MC 1.36 formula, computed_cited). Both always present — A is the
    native-confirmed lineage practice; B is corpus-grounded (translated +
    independently verified 2026-08-03, chunk muhurta_chintamani_pg0048_c01)."""
    rows = compute_day_factors(date(2026, 8, 15))
    agni_rows = [r for r in rows if r.factor_family == "agnivasa"]
    agni_keys = {r.factor_key for r in agni_rows}
    assert len(agni_rows) == 2, f"expected 2 agnivasa rows (A+B), got {len(agni_rows)}: {agni_keys}"
    assert "agni_vasa" in agni_keys
    assert "agni_vasa_mc_arithmetic" in agni_keys


def test_compute_day_factors_agnivasa_convention_a_properties():
    """Convention A: AGNI_VASA_TABLE (tithi-only, 4-element), computed_uncited_convention."""
    rows = compute_day_factors(date(2026, 8, 15))
    conv_a = next(r for r in rows if r.factor_family == "agnivasa" and r.factor_key == "agni_vasa")
    assert conv_a.detail["element"] in ("Prithvi", "Jala", "Vayu", "Akasha")
    assert conv_a.corpus_status == "computed_uncited_convention"
    assert conv_a.detail.get("convention") == "A_agni_vasa_table"


def test_compute_day_factors_agnivasa_convention_b_properties():
    """Convention B: MC 1.36 arithmetic (tithi_id + 1 + vara_id) mod 4,
    computed_cited (corpus-grounded per ADJUDICATION-16). 3-location banding."""
    rows = compute_day_factors(date(2026, 8, 15))
    conv_b = next(r for r in rows if r.factor_family == "agnivasa" and r.factor_key == "agni_vasa_mc_arithmetic")
    assert conv_b.detail["element"] in ("Prithvi", "Akasha", "Patala")
    assert conv_b.corpus_status == "computed_cited"
    assert conv_b.detail.get("convention") == "B_mc_arithmetic"
    assert "muhurta_chintamani_pg0048_c01" in conv_b.source_citation


def test_compute_day_factors_ghati_muhurta_thirty_rows_per_day():
    rows = compute_day_factors(date(2026, 8, 15))
    ghati_rows = [r for r in rows if r.factor_family == "ghati_muhurta"]
    assert len(ghati_rows) == 30
    numbers = sorted(r.detail["number"] for r in ghati_rows)
    assert numbers == list(range(1, 31))


def test_compute_day_factors_kalam_includes_core_periods():
    rows = compute_day_factors(date(2026, 8, 15))
    kalam_keys = {r.factor_key for r in rows if r.factor_family == "kalam"}
    for expected in ("rahu_kalam", "yamaganda", "gulika_kalam", "durmuhurta", "abhijit", "brahma_muhurta"):
        assert expected in kalam_keys, f"expected kalam factor {expected!r} present"


def test_compute_day_factors_abhijit_excluded_on_wednesday():
    """Regression test for the Opus corpus-citation review defect (2026-07-30):
    `compute_extended_auspicious` (panchang_engine/timings.py) ignores vara_id
    and always emits 'abhijit', but the KALAM_CITATIONS entry for abhijit
    cites 'Muhurta Chintamani §5 (excluded on Wednesday)' -- the same rule the
    BASE compute_auspicious_timings correctly implements. Serving abhijit as
    present on a Wednesday while citing its own exclusion is a self-
    contradicting row. 2026-08-05 is a real Wednesday (vara.id=4,
    Budhavara) -- confirmed via compute_vara before this test was written."""
    from panchang_engine.angas import compute_vara
    wednesday = date(2026, 8, 5)
    assert compute_vara(wednesday).id == 4, "test fixture date must be a real Wednesday"

    rows = compute_day_factors(wednesday)
    kalam_keys = {r.factor_key for r in rows if r.factor_family == "kalam"}
    assert "abhijit" not in kalam_keys, "abhijit must be excluded on Wednesday (Muhurta Chintamani §5)"


def test_compute_day_factors_abhijit_present_on_non_wednesday():
    """Positive control: abhijit MUST still appear on a non-Wednesday (guards
    against the fix over-correcting into an always-absent stub)."""
    from panchang_engine.angas import compute_vara
    thursday = date(2026, 8, 6)
    assert compute_vara(thursday).id != 4, "test fixture date must NOT be a Wednesday"

    rows = compute_day_factors(thursday)
    kalam_keys = {r.factor_key for r in rows if r.factor_family == "kalam"}
    assert "abhijit" in kalam_keys, "abhijit must be present on a non-Wednesday"


def test_compute_day_factors_every_row_has_start_before_end():
    rows = compute_day_factors(date(2026, 8, 15))
    for r in rows:
        assert r.start_utc < r.end_utc, f"{r.factor_family}/{r.factor_key}: start must precede end"


def test_lattice_tiling_invariant_no_overlap_within_factor_key():
    """ACCURACY STANDARDS invariant (W3-ENG spec): rows from bg_muhurta_lattice
    must not overlap within the same (factor_family, factor_key) for a given
    calendar day.  Different factor families may share the same timestamp range
    (rahu_kalam and abhijit can coexist), but the SAME factor should appear at
    most once per day — any overlap within a key would double-count a doṣa or
    auspicious span in the adjudication engine.
    """
    import itertools

    rows = compute_day_factors(date(2026, 8, 15))
    # Group by (family, key)
    key_to_rows: dict[tuple[str, str], list] = {}
    for r in rows:
        k = (r.factor_family, r.factor_key)
        key_to_rows.setdefault(k, []).append(r)

    for (family, key), group in key_to_rows.items():
        # Sort by start to make pairwise overlap check O(n log n) instead of O(n²)
        sorted_rows = sorted(group, key=lambda r: r.start_utc)
        for earlier, later in itertools.pairwise(sorted_rows):
            # Half-open intervals [start, end): overlap iff earlier.end > later.start
            assert earlier.end_utc <= later.start_utc, (
                f"Tiling violation: {family}/{key} has overlapping spans "
                f"[{earlier.start_utc}, {earlier.end_utc}) ∩ "
                f"[{later.start_utc}, {later.end_utc})"
            )


def test_compute_day_factors_every_row_has_a_citation_and_valid_corpus_status():
    rows = compute_day_factors(date(2026, 8, 15))
    for r in rows:
        assert r.source_citation, f"{r.factor_family}/{r.factor_key}: missing source_citation"
        assert r.corpus_status in ("computed_cited", "computed_uncited_convention")


def test_compute_day_factors_bhadra_only_when_karana_vishti():
    """Bhadra is a real conditional yoga -- over a 30-day window it must
    appear on SOME but not ALL days (a positive AND negative control in one
    assertion, guarding against both a silent no-op and a fabricated
    always-fire stub)."""
    days_with_bhadra = 0
    days_total = 30
    for offset in range(days_total):
        rows = compute_day_factors(date(2026, 8, 1 + offset))
        if any(r.factor_family == "combination_yoga" and r.factor_key == "bhadra" for r in rows):
            days_with_bhadra += 1
    assert 0 < days_with_bhadra < days_total, (
        f"expected Bhadra to fire on SOME but not ALL of {days_total} days, "
        f"got {days_with_bhadra}"
    )


# ── Offline: writer registration + dry_run ────────────────────────────────────

def test_writer_registered():
    from pipeline.orchestrator.writers import get_writer
    writer_cls = get_writer("bg_muhurta_lattice")
    assert writer_cls is BgMuhurtaLatticeWriter
    assert writer_cls.asset_id == "bg_muhurta_lattice"
    assert writer_cls.has_substeps is True


def test_writer_plan_substeps_matches_horizon():
    writer = BgMuhurtaLatticeWriter()
    ctx = ContextSpec(asset_id="bg_muhurta_lattice", build_id=str(uuid.uuid4()), db_conn=None)
    steps = writer.plan_substeps(ctx)
    start, end = compute_horizon()
    assert [s.key for s in steps] == [s.key for s in plan_year_substeps(start, end)]


def test_writer_dry_run_no_db_needed():
    """dry_run=True must short-circuit before any DB/swisseph work — no live
    conn required, for any sub-step."""
    writer = BgMuhurtaLatticeWriter()
    ctx = ContextSpec(
        asset_id="bg_muhurta_lattice", build_id=str(uuid.uuid4()), db_conn=None, dry_run=True,
    )
    result = writer.run_substep(ctx, SubStep(key="year:2026"))
    assert result.asset_id == "bg_muhurta_lattice"
    assert result.rows_inserted == 0
    assert result.notes == "dry_run"


def test_reference_location_matches_bhubaneswar_panchang_convention():
    """The reference (lat, lon, tz_offset) must match panchang.py's own
    FORENSIC-matching 'bhubaneswar' fallback triple, not a different value."""
    assert REFERENCE_LAT == 20.27
    assert REFERENCE_LON == 85.84
    assert REFERENCE_TZ_OFFSET_MINUTES == 330


# ── Live tests (require DATABASE_URL; skipped otherwise) ─────────────────────

@pytest.fixture(scope="module")
def db_conn():
    url = os.environ.get("DATABASE_URL") or os.environ.get("PROD_DB_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    conn = psycopg.connect(url, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def test_bg_muhurta_lattice_writer_runs_one_year(db_conn):
    writer = BgMuhurtaLatticeWriter()
    ctx = ContextSpec(asset_id="bg_muhurta_lattice", build_id=str(uuid.uuid4()), db_conn=db_conn)
    steps = writer.plan_substeps(ctx)
    result = writer.run_substep(ctx, steps[0])
    db_conn.commit()
    assert result.asset_id == "bg_muhurta_lattice"
    assert result.rows_inserted >= 0


def test_bg_muhurta_lattice_no_null_citations(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_muhurta_lattice WHERE source_citation IS NULL")
    n = cur.fetchone()["n"]
    assert n == 0, f"bg_muhurta_lattice has {n} rows with NULL source_citation"


def test_bg_muhurta_lattice_all_four_families_present_after_full_build(db_conn):
    cur = db_conn.cursor()
    cur.execute("SELECT DISTINCT factor_family FROM bg_muhurta_lattice")
    families = {r["factor_family"] for r in cur.fetchall()}
    assert families == {"agnivasa", "combination_yoga", "kalam", "ghati_muhurta"}


def test_bg_muhurta_lattice_writer_idempotent(db_conn):
    """Re-running the SAME sub-step twice leaves the row count identical."""
    writer = BgMuhurtaLatticeWriter()
    ctx = ContextSpec(asset_id="bg_muhurta_lattice", build_id=str(uuid.uuid4()), db_conn=db_conn)
    steps = writer.plan_substeps(ctx)
    step = steps[0]

    writer.run_substep(ctx, step)
    db_conn.commit()

    cur = db_conn.cursor()
    cur.execute("SELECT count(*) AS n FROM bg_muhurta_lattice")
    count_before = cur.fetchone()["n"]

    result = writer.run_substep(ctx, step)
    db_conn.commit()

    cur.execute("SELECT count(*) AS n FROM bg_muhurta_lattice")
    count_after = cur.fetchone()["n"]

    assert count_before == count_after, f"Idempotency broken: {count_before} -> {count_after}"
    if count_before > 0:
        assert result.rows_inserted == 0, f"Expected 0 rows_inserted on re-run, got {result.rows_inserted}"
