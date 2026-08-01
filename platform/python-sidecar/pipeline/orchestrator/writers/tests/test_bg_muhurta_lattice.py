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
    FACTOR_FAMILIES,
    compute_day_factors,
    compute_horizon,
    compute_lagna_spans,
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


# ── Offline tests: compute_day_factors over real days (no DB) ────────────────

@pytest.fixture(scope="module", autouse=True)
def _set_lahiri():
    swe.set_sid_mode(swe.SIDM_LAHIRI)


def test_compute_day_factors_is_deterministic():
    a = compute_day_factors(date(2026, 8, 15))
    b = compute_day_factors(date(2026, 8, 15))
    assert [(r.factor_family, r.factor_key, r.start_utc, r.end_utc) for r in a] == \
           [(r.factor_family, r.factor_key, r.start_utc, r.end_utc) for r in b]


def test_compute_day_factors_covers_all_nine_families():
    """A real day must yield at least the always-present families and, over a
    sampled week, every one of the NINE documented families must appear at
    least once. Widened from four to nine by ṢAḌ-DARŚANA W4 ruling R-1
    (migration 530): hora/vara/nakshatra/tithi/lagna. Asserted as set EQUALITY,
    not containment, so an accidental tenth family (which the migration's CHECK
    would reject at insert time) fails here first."""
    families_seen: set[str] = set()
    for offset in range(7):
        rows = compute_day_factors(date(2026, 8, 1 + offset))
        families_seen.update(r.factor_family for r in rows)
    assert families_seen == {
        "agnivasa", "combination_yoga", "kalam", "ghati_muhurta",
        "hora", "vara", "nakshatra", "tithi", "lagna",
    }


def test_every_emitted_family_is_declared_in_factor_families():
    """The module constant, the migration CHECK, and what the writer actually
    emits must never disagree — a family emitted but not declared would be
    rejected by the DB at insert time, i.e. a silent partial build."""
    rows = compute_day_factors(date(2026, 8, 15))
    for r in rows:
        assert r.factor_family in FACTOR_FAMILIES, f"undeclared family {r.factor_family!r}"


def test_compute_day_factors_agnivasa_exactly_one_row_per_day():
    rows = compute_day_factors(date(2026, 8, 15))
    agni_rows = [r for r in rows if r.factor_family == "agnivasa"]
    assert len(agni_rows) == 1
    assert agni_rows[0].factor_key == "agni_vasa"
    assert agni_rows[0].detail["element"] in ("Prithvi", "Jala", "Vayu", "Akasha")


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


# ══════════════════════════════════════════════════════════════════════════════
# W4 ruling R-1: the five new families (hora / vara / nakshatra / tithi / lagna)
# ══════════════════════════════════════════════════════════════════════════════


def test_hora_family_twentyfour_rows_covering_the_whole_cycle():
    """24 horā per sunrise→next-sunrise cycle, contiguous, no gap, no overlap.
    Contiguity is the Elevation §9 Stage-1 property that makes 'no sampling
    interval exists' true for this family."""
    rows = compute_day_factors(date(2026, 8, 15))
    horas = sorted((r for r in rows if r.factor_family == "hora"), key=lambda r: r.start_utc)
    assert len(horas) == 24
    for a, b in zip(horas, horas[1:]):
        assert a.end_utc == b.start_utc, "horā spans must be exactly contiguous"
    assert [h.detail["hora_index"] for h in horas] == list(range(1, 25))


def test_hora_first_lord_is_the_vara_lord_from_panchang_engine_table():
    """The first horā at sunrise is the vāra lord (shastra_tables.VARA_HORA_START).
    Asserted against panchang_engine's OWN table, not a literal repeated here —
    a literal would pass even if the table changed underneath us."""
    from panchang_engine.angas import compute_vara
    from panchang_engine.shastra_tables import VARA_HORA_START

    day = date(2026, 8, 6)
    rows = compute_day_factors(day)
    horas = sorted((r for r in rows if r.factor_family == "hora"), key=lambda r: r.start_utc)
    expected_lord = VARA_HORA_START[compute_vara(day).id]
    assert horas[0].detail["lord"] == expected_lord
    assert horas[0].factor_key == f"hora_{expected_lord.lower()}"


def test_hora_cycle_follows_chaldean_order_from_panchang_engine():
    """Successive horā lords follow shastra_tables.HORA_CYCLE, read from the
    table rather than restated — this is the atom the W4 fixture's
    `planet_state {body: Guru, in: {hora_lord}}` constraint searches over."""
    from panchang_engine.shastra_tables import HORA_CYCLE

    rows = compute_day_factors(date(2026, 8, 6))
    horas = sorted((r for r in rows if r.factor_family == "hora"), key=lambda r: r.start_utc)
    lords = [h.detail["lord"] for h in horas]
    start_idx = HORA_CYCLE.index(lords[0])
    expected = [HORA_CYCLE[(start_idx + i) % len(HORA_CYCLE)] for i in range(24)]
    assert lords == expected


@pytest.mark.parametrize(
    "family,compute_name,id_range",
    [
        ("vara", "compute_vara", range(1, 8)),
        ("nakshatra", "compute_nakshatra", range(1, 28)),
        ("tithi", "compute_tithi", range(1, 31)),
    ],
)
def test_daily_anga_families_emit_exactly_one_row_with_a_canonical_factor_id(
    family, compute_name, id_range,
):
    """THE ID PROVENANCE RAIL (ADJUDICATION-10, design §3.3) — the assertion
    registry item 6 rests on. Each daily-aṅga family emits exactly one row per
    day whose detail.factor_id is inside panchang_engine's canonical id range.
    A row without factor_id, or with an out-of-range one, breaks the
    bg_muhurta_activity_rules join and MUST fail here."""
    rows = compute_day_factors(date(2026, 8, 15))
    matches = [r for r in rows if r.factor_family == family]
    assert len(matches) == 1, f"{family} must emit exactly one row per day"
    fid = matches[0].detail.get("factor_id")
    assert isinstance(fid, int), f"{family}.detail.factor_id must be an int, got {fid!r}"
    assert fid in id_range, f"{family}.detail.factor_id={fid} outside panchang_engine's canonical range"
    assert matches[0].detail["span_convention"].startswith("hindu_day_sunrise_to_next_sunrise")


def test_activity_rule_join_resolves_against_real_activity_rule_rows():
    """Registry item 6, end to end and WITHOUT any hand-written map: take the
    lattice's own emitted detail.factor_id values and look them up directly in
    bg_muhurta_activity_rules' materialized rows. At least one activity class
    must grade at least one of the day's three aṅgas — proving the two tables
    genuinely share an id space rather than merely both having an integer
    column. This is the test whose failure would mean the axis must stay
    excluded (a B.10 gate failure), so it asserts the join, not the shape."""
    from pipeline.orchestrator.writers.bg_parihara_rules import build_activity_rule_rows

    rows = compute_day_factors(date(2026, 8, 15))
    lattice_ids = {
        r.factor_family: r.detail["factor_id"]
        for r in rows
        if r.factor_family in ("tithi", "nakshatra", "vara")
    }
    assert set(lattice_ids) == {"tithi", "nakshatra", "vara"}

    activity_rows = build_activity_rule_rows("test-build")
    hits = [
        a for a in activity_rows
        if a["factor_type"] in lattice_ids and a["factor_id"] == lattice_ids[a["factor_type"]]
    ]
    assert hits, (
        "no bg_muhurta_activity_rules row matched the lattice's own factor_ids — "
        "the item-6 join is NOT resolvable and rite_specific_resonance must stay excluded"
    )
    # Every hit must carry the real per-activity citation the rule table ships.
    for h in hits:
        assert h["source_citation"] and "citation not mapped" not in h["source_citation"]


def test_lagna_spans_tile_the_whole_day_contiguously():
    """Item 7: rising-sign spans must partition [sunrise, next_sunrise) exactly —
    contiguous, in ascending-sign order (mod 12), covering the full cycle. A gap
    would be a moment with no muhūrta-lagna atom, i.e. a sampling hole."""
    from panchang_engine.timings import compute_sunrise_sunset

    day = date(2026, 8, 15)
    sunrise, _ = compute_sunrise_sunset(day, REFERENCE_LAT, REFERENCE_LON, REFERENCE_TZ_OFFSET_MINUTES)
    next_sunrise, _ = compute_sunrise_sunset(
        date(2026, 8, 16), REFERENCE_LAT, REFERENCE_LON, REFERENCE_TZ_OFFSET_MINUTES
    )
    rows = sorted(
        (r for r in compute_day_factors(day) if r.factor_family == "lagna"),
        key=lambda r: r.start_utc,
    )
    # A sidereal day is slightly shorter than a solar day, so a full cycle plus a
    # partial repeat is expected: 12 or 13 spans, never fewer than 12.
    assert 12 <= len(rows) <= 14, f"expected 12-14 lagna spans, got {len(rows)}"
    assert rows[0].start_utc == sunrise
    assert rows[-1].end_utc == next_sunrise
    for a, b in zip(rows, rows[1:]):
        assert a.end_utc == b.start_utc, "lagna spans must be exactly contiguous"
        assert b.detail["sign_id"] == a.detail["sign_id"] % 12 + 1, "signs must rise in order"


def test_lagna_span_carries_the_facts_a_strength_check_needs_and_no_verdict():
    """Item 7's strength half. The row must carry the FACTS (lord, lord's own
    sign, every graha's sign) and must NOT carry a dignity/dṛṣṭi verdict — §N.5:
    bg_dignity_reference and BPHS Ch.26 are the authorities, and a verdict stored
    here would be a second copy that can drift from both. The null is asserted
    positively so a future 'helpful' addition fails loudly."""
    from panchang_engine.shastra_tables import SIGN_LORDS

    rows = [r for r in compute_day_factors(date(2026, 8, 15)) if r.factor_family == "lagna"]
    assert rows
    for r in rows:
        d = r.detail
        assert d["lord"] == SIGN_LORDS[d["sign_id"] - 1], "lord must come from shastra_tables.SIGN_LORDS"
        assert isinstance(d["lord_sign_id"], int) and 1 <= d["lord_sign_id"] <= 12
        assert isinstance(d["lord_retrograde"], bool)
        assert set(d["graha_sign_ids"]) >= {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
        }
        assert all(1 <= v <= 12 for v in d["graha_sign_ids"].values())
        assert d["strength_verdict"] is None, "no dignity/dṛṣṭi verdict may be stored on the lattice row (§N.5)"
        assert d["strength_verdict_note"], "the null must carry its reason (§N.7 item 6)"


def test_lagna_lord_sign_agrees_with_the_graha_sign_map_it_was_read_from():
    """Internal consistency: `lord_sign_id` must be exactly the `graha_sign_ids`
    entry for `lord`. A divergence would mean one of the two was re-derived
    rather than read — the §N.5 authority-inversion defect class."""
    for r in compute_day_factors(date(2026, 8, 15)):
        if r.factor_family != "lagna":
            continue
        assert r.detail["lord_sign_id"] == r.detail["graha_sign_ids"][r.detail["lord"]]


def test_compute_lagna_spans_is_deterministic():
    """The bisection must reproduce byte-identical boundaries across runs — the
    natural key is (family, key, start_utc), so a wobbling boundary would break
    ON CONFLICT DO NOTHING idempotency and accrete duplicate rows."""
    from panchang_engine.planets import compute_all_grahas
    from panchang_engine.timings import compute_sunrise_sunset

    day = date(2026, 8, 15)
    sunrise, _ = compute_sunrise_sunset(day, REFERENCE_LAT, REFERENCE_LON, REFERENCE_TZ_OFFSET_MINUTES)
    next_sunrise, _ = compute_sunrise_sunset(
        date(2026, 8, 16), REFERENCE_LAT, REFERENCE_LON, REFERENCE_TZ_OFFSET_MINUTES
    )
    jd = swe.julday(
        sunrise.year, sunrise.month, sunrise.day,
        sunrise.hour + sunrise.minute / 60.0 + sunrise.second / 3600.0,
    )
    planets = compute_all_grahas(jd)
    a = compute_lagna_spans(sunrise, next_sunrise, planets)
    b = compute_lagna_spans(sunrise, next_sunrise, planets)
    assert [(s["start_utc"], s["end_utc"], s["detail"]["sign_id"]) for s in a] == \
           [(s["start_utc"], s["end_utc"], s["detail"]["sign_id"]) for s in b]
    # Whole-second boundaries: the interior boundaries are truncated so the
    # natural key cannot wobble at sub-second precision.
    for s in a[1:]:
        assert s["start_utc"].microsecond == 0


def test_new_families_carry_non_blank_citations_and_a_valid_corpus_status():
    """Every W4 family must ship a real citation string and a corpus_status from
    the migration's closed set — never a blank, never an invented upgrade."""
    rows = [
        r for r in compute_day_factors(date(2026, 8, 15))
        if r.factor_family in ("hora", "vara", "nakshatra", "tithi", "lagna")
    ]
    assert rows
    for r in rows:
        assert r.source_citation and len(r.source_citation) > 40
        assert r.corpus_status in ("computed_cited", "computed_uncited_convention")
    # The lagna family in particular must NOT claim `computed_cited`: this
    # codebase holds no muhūrta-lagna verse at grain (census row
    # muhurta_lagna/lagna_shuddhi_rules), and claiming one would be the exact
    # over-citation the 2026-07-30 Opus review caught elsewhere in this writer.
    for r in rows:
        if r.factor_family == "lagna":
            assert r.corpus_status == "computed_uncited_convention"


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


def test_bg_muhurta_lattice_all_nine_families_present_after_full_build(db_conn):
    """Widened four -> nine by W4 ruling R-1 (migration 530). This is the LIVE
    counterpart of the offline family-coverage test: it proves the migration's
    widened CHECK actually admits the five new families, which an offline test
    structurally cannot."""
    cur = db_conn.cursor()
    cur.execute("SELECT DISTINCT factor_family FROM bg_muhurta_lattice")
    families = {r["factor_family"] for r in cur.fetchall()}
    assert families == set(FACTOR_FAMILIES)


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
