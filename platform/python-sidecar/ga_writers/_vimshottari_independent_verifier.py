"""
_vimshottari_independent_verifier.py — M-22 Stage 3 independent second pass
=============================================================================

Builds a genuinely independent (levels 1-4) Vimshottari tree from first
principles and compares it against the rows `ga_dashas_writer.compute_vimshottari`
persisted into `chart_dashas`, so a row can honestly re-earn
`two_pass_verified` (or be caught as `divergent_flagged`) instead of carrying
a broadcast tier it never earned.

BACKGROUND (read `ga_dashas_writer.py` before touching this file)
-------------------------------------------------------------------
Per the §6.18 earnedness ruling (2026-08-02) already landed in
`ga_dashas_writer.py`, that writer's own `_verify_vimshottari()` only ever
examines `level_n == 1` rows, and even then only checks (a) a no-op float
tolerance comparison that ends in a bare `pass` (cannot fail), and (b) that
the ONE L1 period covering the native's birth date has lord=Jupiter. Levels
2-4 were never examined by anything and are correctly stamped `single`
(honest — Stage 1 of this campaign fixed the broadcast bug that used to
stamp them `two_pass_verified` too). This module is the real second pass
those L1-4 rows still need: an independently-implemented re-derivation of
the FULL M/A/P/Sukshma tree, compared boundary-by-boundary and lord-by-lord.

INDEPENDENCE AUDIT — every import in this file, and why it does not
compromise the second pass:
  - `math`, `dataclasses`, `datetime`, `zoneinfo` (stdlib): no dasha logic.
  - `psycopg` / `psycopg.rows`: DB driver only: issues raw SQL, no dasha
    logic. Used to (a) read `chart_facts.longitude_sidereal` for MOON
    (a stored L1 FACT, not a re-invocation of any position-computation
    function) and (b) read `public.charts` birth fields directly (raw SQL,
    not `pipeline.orchestrator.birth_params.fetch_birth_params` — that
    function is itself genuinely neutral, but this module re-implements the
    handful of lines it would have called, so there is *zero* import surface
    shared with anything `ga_dashas_writer.py` imports for its own
    computation).
  - `brahmagyan.verification_vocab.two_pass_verdict` / `TWO_PASS_VERIFIED` /
    `DIVERGENT_FLAGGED`: the SANCTIONED, ONLY-LEGAL producer of the
    `two_pass_verified` string (see that module's docstring). It performs an
    identity comparison of two values the CALLER supplies; it contains zero
    Vimshottari logic itself. Every comparison in this module supplies it
    with a boolean already computed independently (lord equality, boundary
    delta within tolerance) — using the sanctioned producer does not import
    any dasha computation.
  - Explicitly NOT imported, anywhere, by this module: `ga_dashas_writer`
    (any name from it), `pyjhora_adapter`, `swisseph`/`pyswisseph`,
    `pipeline.orchestrator.birth_params`. This module computes its own
    Julian Day <-> Gregorian-calendar conversion from the standard
    (Fliegel & Van Flandern / Meeus, "Astronomical Algorithms" ch. 7)
    closed-form formulas — see `_gregorian_to_jd` / `_jd_to_gregorian` below
    — rather than reusing swisseph's `swe.julday` / `swe.revjul`, which is
    what `ga_dashas_writer.py` uses. This was a deliberate choice: JD
    conversion is a "neutral" calendrical utility in principle, but sharing
    the exact same C-extension call as the code under test would have made
    the Skeptic's job of ruling on independence harder for no benefit, so
    this module carries its own (self-tested — see `_self_test_jd_roundtrip`)
    implementation instead.

THE MOON SIDEREAL LONGITUDE INPUT
----------------------------------
Per the task brief, the Moon's natal sidereal longitude is READ from the live
DB, not recomputed: `chart_facts` rows with
`fact_subject='MOON', fact_category='graha_position', fact_key='longitude_sidereal'`,
scoped to `(chart_id, ayanamsha_id)`. That fact was written by `ga_positions_writer`
(a *different* L1 writer than `ga_dashas_writer`), so this module's Moon input and
`ga_dashas_writer`'s Moon input are two independently-computed values that happen
to both trace to the same underlying Swiss-Ephemeris Moon position call; reading
the stored fact rather than recomputing it is exactly what the task specifies,
and keeps this module free of any ephemeris dependency.

ALGORITHM PARAMETERS CONFIRMED AGAINST THIS CODEBASE (not assumed):
  - 9-lord cyclic order and years, from `ga_dashas_writer.VIMSHOTTARI_SEQUENCE` /
    `VIMSHOTTARI_YEARS` (read, not imported): Ketu 7, Venus 20, Sun 6, Moon 10,
    Mars 7, Rahu 18, Jupiter 16, Saturn 19, Mercury 17 = 120y total. Standard
    Parashari Vimshottari; matches the classical table.
  - Nakshatra span: 360/27 degrees (equal-nakshatra convention); nakshatra-lord
    assignment matches `reference_nakshatras` (L0 reference table) exactly —
    cross-checked live, see `cross_check_nakshatra_lord_table()`.
  - Year-to-day convention: `DAYS_PER_YEAR = 365.25` (Julian year) — this is
    `ga_dashas_writer._years_to_days()`'s literal convention (`years * 365.25`),
    confirmed by reading the source; NOT a sidereal or tropical year, and NOT
    assumed from a generic Vimshottari reference (some traditions use 365.2425
    or a sidereal year ~365.2564 days — this codebase uses neither).
  - levels 1-4 = Mahadasha / Antardasha / Pratyantardasha / Sukshma, confirmed
    by `ga_dashas_writer.py`'s own "CRITICAL OVERRIDE 1: DEPTH = 4-level Sukshma
    (level_n 1-4). ZERO level_n=5" header comment and the `cd_level_n_max4` CHECK
    constraint on `chart_dashas` (`level_n >= 1 AND level_n <= 4`).
  - Balance of dasha at birth: standard classical rule — fraction of the natal
    nakshatra ALREADY ELAPSED at birth (Moon's degree within its 13°20' nakshatra
    span) determines how much of the birth-nakshatra-lord's full period remains;
    `balance_years = lord_total_years * (1 - fraction_elapsed)`. Confirmed against
    `ga_dashas_writer.compute_vimshottari`'s inline `balance_years = ...` line.
  - WINDOW MODEL — the one non-obvious convention, confirmed by reading the
    engine rather than assumed: `chart_dashas` does NOT store a birth-truncated
    first Mahadasha. It stores the calculation window [1950-01-01, 2100-12-31]
    (`ga_dashas_writer.WINDOW_START` / `WINDOW_END`), backdated from birth to a
    TRUE, un-truncated period boundary that covers 1950-01-01, then walks FORWARD
    through whole (never birth-truncated) MD/AD/PD/Sukshma periods, clipping only
    at the two window edges for the *stored* start/end (the underlying recursive
    math always uses the true, unclipped boundaries). This module replicates that
    same window model — see `compute_independent_vimshottari_tree()` — because a
    verifier using the textbook "first dasha truncated at birth" model would
    diverge from every single row in the table for a reason that has nothing to
    do with an engine defect.

TOLERANCE — see `_TOLERANCE_JUSTIFICATION` docstring below.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable

from brahmagyan.verification_vocab import DIVERGENT_FLAGGED, TWO_PASS_VERIFIED, two_pass_verdict

# ─────────────────────────────────────────────────────────────────────────────
# Classical Vimshottari constants — independently transcribed from BPHS /
# standard Parashari convention, cross-confirmed (not copy-imported) against
# `ga_dashas_writer.VIMSHOTTARI_SEQUENCE` / `VIMSHOTTARI_YEARS` by reading the
# source. Any two correct implementations of a fixed classical table are
# expected to look the same; independence here is about the CODE PATH
# (this module never calls into `ga_dashas_writer`), not about obfuscating a
# well-known 9-row constant table.
# ─────────────────────────────────────────────────────────────────────────────

CLASSICAL_9_LORDS: tuple[str, ...] = (
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
)
LORD_YEARS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
TOTAL_CYCLE_YEARS: int = 120
assert sum(LORD_YEARS.values()) == TOTAL_CYCLE_YEARS  # 7+20+6+10+7+18+16+19+17 = 120

# Confirmed convention (see module docstring): Julian year, NOT sidereal/tropical.
DAYS_PER_YEAR: float = 365.25

NAKSHATRA_SPAN_DEG: float = 360.0 / 27.0

# 27-nakshatra -> lord, 0-based (0=Ashwini .. 26=Revati). The classical
# assignment is exactly 3 repetitions of the 9-lord cycle starting at Ashwini.
NAKSHATRA_LORDS_27: tuple[str, ...] = tuple(CLASSICAL_9_LORDS[i % 9] for i in range(27))

# The calculation window this codebase's dasha table is built over — read
# (not imported) from `ga_dashas_writer.WINDOW_START` / `WINDOW_END` and its
# module docstring ("Calculation window: start_iso >= 1950-01-01, end_iso <=
# 2100-12-31"). This is a documented POLICY constant, not implementation
# detail; a verifier that used a different window would compare apples to
# oranges regardless of how correct its dasha math was.
WINDOW_START_DATE = date(1950, 1, 1)
WINDOW_END_DATE = date(2100, 12, 31)


# ─────────────────────────────────────────────────────────────────────────────
# Julian Day <-> Gregorian calendar — self-contained (Meeus, "Astronomical
# Algorithms" ch. 7 / Fliegel & Van Flandern). No swisseph, no ga_dashas_writer.
# ─────────────────────────────────────────────────────────────────────────────

def _gregorian_to_jd(year: int, month: int, day: int, hour: float = 0.0,
                     minute: float = 0.0, second: float = 0.0) -> float:
    """Proleptic-Gregorian calendar date (UT) -> Julian Day. Meeus ch. 7."""
    day_frac = day + (hour + minute / 60.0 + second / 3600.0) / 24.0
    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12
    a = math.floor(y / 100.0)
    b = 2 - a + math.floor(a / 4.0)
    jd = (
        math.floor(365.25 * (y + 4716))
        + math.floor(30.6001 * (m + 1))
        + day_frac + b - 1524.5
    )
    return jd


def _jd_to_gregorian(jd: float) -> tuple[int, int, int, float]:
    """Julian Day (UT) -> (year, month, day, seconds_into_day). Meeus ch. 7,
    proleptic-Gregorian branch only (valid for any JD in this module's
    1950-2100 operating range, far from the Julian/Gregorian cutover)."""
    jd_shift = jd + 0.5
    z = math.floor(jd_shift)
    f = jd_shift - z
    alpha = math.floor((z - 1867216.25) / 36524.25)
    a = z + 1 + alpha - math.floor(alpha / 4.0)
    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d) / 30.6001)
    day_frac = b - d - math.floor(30.6001 * e) + f
    day = math.floor(day_frac)
    seconds_into_day = (day_frac - day) * 86400.0
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715
    return int(year), int(month), int(day), seconds_into_day


def jd_to_datetime_utc(jd: float) -> datetime:
    """JD (UT) -> tz-aware UTC datetime, rounded to the nearest second.

    Matches `ga_dashas_writer._jd_to_iso_utc`'s documented rounding
    convention (chart_dashas.start_iso/end_iso are TIMESTAMPTZ, populated by
    rounding swe.revjul()'s fractional-day return to the nearest second) —
    replicated here independently so the comparison in this module is
    apples-to-apples with what is actually stored, not a spurious ~half-day
    of "noise" from comparing against a different rounding rule.
    """
    year, month, day, seconds_into_day = _jd_to_gregorian(jd)
    total_seconds = int(round(seconds_into_day))
    return datetime(year, month, day, tzinfo=timezone.utc) + timedelta(seconds=total_seconds)


def _self_test_jd_roundtrip() -> None:
    """Sanity-check the hand-rolled JD conversion against two well-known
    reference epochs before this module is trusted for anything. Raises
    AssertionError (loud failure, not a silent wrong answer) if either
    known constant doesn't round-trip.
    """
    # J2000.0 epoch: 2000-01-01 12:00:00 UT = JD 2451545.0 (IAU standard).
    jd_j2000 = _gregorian_to_jd(2000, 1, 1, 12, 0, 0)
    assert abs(jd_j2000 - 2451545.0) < 1e-9, f"J2000 epoch mismatch: {jd_j2000}"
    # Unix epoch: 1970-01-01 00:00:00 UT = JD 2440587.5 (widely tabulated).
    jd_unix = _gregorian_to_jd(1970, 1, 1, 0, 0, 0)
    assert abs(jd_unix - 2440587.5) < 1e-9, f"Unix epoch mismatch: {jd_unix}"
    # Round-trip: JD -> calendar -> JD for a handful of points across the
    # window this module actually operates over.
    for probe_jd in (2433282.5, 2451545.0, 2488069.5, 2460000.123456):
        y, mo, d, s = _jd_to_gregorian(probe_jd)
        back = _gregorian_to_jd(y, mo, d, 0, 0, s)
        assert abs(back - probe_jd) < 1e-6, f"round-trip mismatch at {probe_jd}: {back}"


_self_test_jd_roundtrip()  # run at import time — fail loudly, immediately, if the JD math is wrong.

WINDOW_START_JD: float = _gregorian_to_jd(WINDOW_START_DATE.year, WINDOW_START_DATE.month, WINDOW_START_DATE.day)
WINDOW_END_JD: float = _gregorian_to_jd(WINDOW_END_DATE.year, WINDOW_END_DATE.month, WINDOW_END_DATE.day)


# ─────────────────────────────────────────────────────────────────────────────
# DB reads — raw SQL only, no dasha logic, no shared imports with ga_dashas_writer.
# ─────────────────────────────────────────────────────────────────────────────

def fetch_moon_sidereal_longitude(conn: Any, chart_id: str, ayanamsha_id: str) -> float:
    """Read the natal Moon sidereal longitude FACT (degrees, 0-360) from
    `chart_facts`. This is a stored L1 fact written by `ga_positions_writer`
    (a different writer than `ga_dashas_writer`) — reading it is not a call
    into any dasha-computation code."""
    import psycopg.rows as _pr
    with conn.cursor(row_factory=_pr.tuple_row) as cur:
        cur.execute(
            """
            SELECT fact_value_num
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND fact_subject = 'MOON' AND fact_category = 'graha_position'
              AND fact_key = 'longitude_sidereal'
            LIMIT 1
            """,
            (chart_id, ayanamsha_id),
        )
        row = cur.fetchone()
    if row is None or row[0] is None:
        raise ValueError(
            f"[vimshottari_verifier] no chart_facts MOON longitude_sidereal fact for "
            f"chart_id={chart_id} ayanamsha_id={ayanamsha_id}"
        )
    return float(row[0]) % 360.0


def fetch_birth_jd_utc(conn: Any, chart_id: str) -> float:
    """Independently derive birth JD (UT) from `public.charts`, without going
    through `pipeline.orchestrator.birth_params`. Mirrors that module's
    documented technique (combine local birth_date/birth_time, subtract the
    IANA-zone UTC offset via `zoneinfo`) but is written fresh here so this
    module shares zero import surface with the birth-param path
    `ga_dashas_writer` itself uses."""
    from zoneinfo import ZoneInfo

    import psycopg.rows as _pr
    with conn.cursor(row_factory=_pr.dict_row) as cur:
        cur.execute(
            """
            SELECT birth_date, birth_time, timezone_id
            FROM public.charts
            WHERE id = %s OR chart_id = %s
            LIMIT 1
            """,
            (chart_id, chart_id),
        )
        row = cur.fetchone()
    if not row:
        raise ValueError(f"[vimshottari_verifier] no charts row for chart_id={chart_id}")
    if not row.get("timezone_id") or row.get("birth_date") is None or row.get("birth_time") is None:
        raise ValueError(f"[vimshottari_verifier] chart {chart_id} missing birth_date/birth_time/timezone_id")

    birth_dt_local = datetime.combine(row["birth_date"], row["birth_time"])
    offset = ZoneInfo(row["timezone_id"]).utcoffset(birth_dt_local)
    if offset is None:
        raise ValueError(f"[vimshottari_verifier] could not resolve UTC offset for {row['timezone_id']!r}")
    birth_dt_utc = birth_dt_local - offset
    return _gregorian_to_jd(
        birth_dt_utc.year, birth_dt_utc.month, birth_dt_utc.day,
        birth_dt_utc.hour, birth_dt_utc.minute,
        birth_dt_utc.second + birth_dt_utc.microsecond / 1e6,
    )


def cross_check_nakshatra_lord_table(conn: Any) -> list[str]:
    """Compares this module's hardcoded NAKSHATRA_LORDS_27 against the live
    `reference_nakshatras` L0 table. Returns a list of mismatch descriptions
    (empty = full agreement). Not required for a single verification run,
    but strengthens the independence story: rather than trusting a
    transcribed constant blind, cross-validate it against the DB's own
    reference data (which is itself independent of `ga_dashas_writer.py` —
    it's an L0 table, loaded by `_load_nakshatra_lords_l0`, but that loader
    is not being invoked or imported here; this function issues its own SQL).
    """
    import psycopg.rows as _pr
    mismatches: list[str] = []
    with conn.cursor(row_factory=_pr.tuple_row) as cur:
        cur.execute("SELECT nakshatra_id, lord FROM reference_nakshatras ORDER BY nakshatra_id")
        for nak_id_1based, lord_lower in cur.fetchall():
            idx0 = nak_id_1based - 1
            expected = NAKSHATRA_LORDS_27[idx0].lower()
            if lord_lower.lower() != expected:
                mismatches.append(
                    f"nakshatra_id={nak_id_1based}: reference_nakshatras.lord={lord_lower!r}, "
                    f"module table={expected!r}"
                )
    return mismatches


# ─────────────────────────────────────────────────────────────────────────────
# Balance-of-dasha-at-birth + full independent M/A/P/Sukshma tree.
# ─────────────────────────────────────────────────────────────────────────────

def derive_birth_nakshatra_period(moon_sid_deg: float) -> tuple[str, int, float, float]:
    """Returns (lord, nakshatra_idx0, elapsed_years_in_period, balance_years_in_period)."""
    nak_idx0 = int(moon_sid_deg // NAKSHATRA_SPAN_DEG)
    nak_idx0 = min(nak_idx0, 26)  # guard the moon_sid_deg == 360.0 edge
    lord = NAKSHATRA_LORDS_27[nak_idx0]
    pos_in_nak = moon_sid_deg - nak_idx0 * NAKSHATRA_SPAN_DEG
    fraction_elapsed = pos_in_nak / NAKSHATRA_SPAN_DEG
    total_years = float(LORD_YEARS[lord])
    elapsed_years = total_years * fraction_elapsed
    balance_years = total_years * (1.0 - fraction_elapsed)
    return lord, nak_idx0, elapsed_years, balance_years


@dataclass(frozen=True)
class IndependentDashaRow:
    level_n: int
    lord: str
    parent_chain: tuple[str, ...]
    start_jd: float          # true, unclipped boundary
    end_jd: float             # true, unclipped boundary
    start_dt: datetime        # window-clipped, second-precision (matches start_iso)
    end_dt: datetime          # window-clipped, second-precision (matches end_iso)
    is_trunc_start: bool
    is_trunc_end: bool


def _civil_date(jd: float) -> date:
    """The calendar DATE component of a JD (UT), floor semantics — matches
    `ga_dashas_writer._jd_to_date()` (which floors via `swe.revjul()`'s
    (y, m, d) return, discarding the fractional-day remainder)."""
    y, m, d, _secs = _jd_to_gregorian(jd)
    return date(y, m, d)


def _collapses_to_same_civil_date(start_jd: float, end_jd: float,
                                   window_start_jd: float, window_end_jd: float) -> bool:
    """Replicates a confirmed, non-obvious engine behavior found by reading
    `ga_dashas_writer.compute_vimshottari` (and every sibling `compute_*`
    system in that file — the pattern recurs at all 4 levels, e.g. lines
    1042/1075/1106/1136): after clipping a period's boundaries to the
    calculation window, the engine compares the CLIPPED boundaries at
    DATE (day) granularity — `_jd_to_date(max(jd, min_jd))` vs
    `_jd_to_date(min(end_jd, max_jd))` — and DROPS the row entirely
    (`if start_d >= end_d: continue`) whenever the clipped span collapses
    onto the same calendar date, or inverts. Critically, this `continue`
    skips the ENTIRE remainder of that loop iteration, which for MD/AD/PD
    includes the recursive descent into the next level down — so a
    collapsed period's children are never computed or emitted either, not
    just its own row.

    This is a genuine, confirmed engine trait (not a JD-arithmetic or
    lord-sequence defect): the shortest possible level-4 (Sukshma) period is
    ~6.6 hours (see `_TOLERANCE_JUSTIFICATION`), well under 24 hours, so a
    material fraction of Sukshma periods that do not happen to straddle a
    UTC midnight are silently un-persisted. Without replicating this here,
    this module would flag every such gap as a false "divergent_flagged"
    disagreement (a phantom missing-row cascade), rather than correctly
    recognizing it as the SAME row-existence policy the engine itself
    applies. First discovered empirically (row-count mismatch at level 4
    against the canonical chart), then confirmed by reading the source —
    per the task brief's "stop and report rather than guess" instruction,
    this was verified against the actual `if ..._d >= ..._d: continue`
    code before being encoded here, not assumed.
    """
    clipped_start_jd = max(start_jd, window_start_jd)
    clipped_end_jd = min(end_jd, window_end_jd)
    return _civil_date(clipped_start_jd) >= _civil_date(clipped_end_jd)


def _mk_row(level_n: int, lord: str, start_jd: float, end_jd: float,
            window_start_jd: float, window_end_jd: float,
            parent_chain: tuple[str, ...]) -> IndependentDashaRow:
    clipped_start_jd = max(start_jd, window_start_jd)
    clipped_end_jd = min(end_jd, window_end_jd)
    return IndependentDashaRow(
        level_n=level_n,
        lord=lord,
        parent_chain=parent_chain,
        start_jd=start_jd,
        end_jd=end_jd,
        start_dt=jd_to_datetime_utc(clipped_start_jd),
        end_dt=jd_to_datetime_utc(clipped_end_jd),
        is_trunc_start=start_jd < window_start_jd,
        is_trunc_end=end_jd > window_end_jd,
    )


def compute_independent_vimshottari_tree(
    moon_sid_deg: float,
    birth_jd_ut: float,
    *,
    window_start_jd: float = WINDOW_START_JD,
    window_end_jd: float = WINDOW_END_JD,
    max_md_iterations: int = 200,
) -> list[IndependentDashaRow]:
    """Independently compute the FULL levels 1-4 Vimshottari tree over
    [window_start_jd, window_end_jd], replicating the WINDOW MODEL confirmed
    from `ga_dashas_writer.py` (see module docstring): backdate to a TRUE
    (never birth-truncated) period boundary covering window_start, then walk
    forward through whole MD/AD/PD/Sukshma periods, clipping only the stored
    boundaries at the two window edges. No call into `ga_dashas_writer`
    anywhere in this function.
    """
    lord0, _nak_idx0, elapsed_years0, _balance_years0 = derive_birth_nakshatra_period(moon_sid_deg)

    # True (unclipped) start of the birth-nakshatra-lord's FULL period.
    true_period_start_jd = birth_jd_ut - elapsed_years0 * DAYS_PER_YEAR

    # A full 120y cycle is exactly TOTAL_CYCLE_YEARS * DAYS_PER_YEAR days and
    # returns to the SAME lord (9 sub-periods later) — so we can jump whole
    # cycles backward in closed form instead of an iterative walk.
    cycle_days = TOTAL_CYCLE_YEARS * DAYS_PER_YEAR  # 43830.0 exactly
    anchor_jd = true_period_start_jd
    if anchor_jd > window_start_jd:
        n_cycles = math.ceil((anchor_jd - window_start_jd) / cycle_days)
        anchor_jd -= n_cycles * cycle_days

    lord_idx = CLASSICAL_9_LORDS.index(lord0)

    rows: list[IndependentDashaRow] = []
    md_jd = anchor_jd
    iterations = 0
    while md_jd < window_end_jd and iterations < max_md_iterations:
        iterations += 1
        md_lord = CLASSICAL_9_LORDS[lord_idx % 9]
        md_years = float(LORD_YEARS[md_lord])
        md_days = md_years * DAYS_PER_YEAR
        md_end_jd = md_jd + md_days

        if md_end_jd <= window_start_jd:
            md_jd = md_end_jd
            lord_idx += 1
            continue
        if md_jd >= window_end_jd:
            break

        if _collapses_to_same_civil_date(md_jd, md_end_jd, window_start_jd, window_end_jd):
            # Matches engine's `if md_start_d >= md_end_d: continue` — row
            # dropped, AD/PD/Sukshma children never computed for this MD.
            md_jd = md_end_jd
            lord_idx += 1
            continue

        rows.append(_mk_row(1, md_lord, md_jd, md_end_jd, window_start_jd, window_end_jd, ()))

        ad_start_idx = CLASSICAL_9_LORDS.index(md_lord)
        ad_jd = md_jd
        for j in range(9):
            ad_lord = CLASSICAL_9_LORDS[(ad_start_idx + j) % 9]
            ad_years = LORD_YEARS[ad_lord] / TOTAL_CYCLE_YEARS * md_years
            ad_days = ad_years * DAYS_PER_YEAR
            ad_end_jd = ad_jd + ad_days

            if ad_end_jd <= window_start_jd or ad_jd >= window_end_jd:
                ad_jd = ad_end_jd
                continue
            if _collapses_to_same_civil_date(ad_jd, ad_end_jd, window_start_jd, window_end_jd):
                ad_jd = ad_end_jd
                continue

            rows.append(_mk_row(2, ad_lord, ad_jd, ad_end_jd, window_start_jd, window_end_jd, (md_lord,)))

            pd_start_idx = CLASSICAL_9_LORDS.index(ad_lord)
            pd_jd = ad_jd
            for k in range(9):
                pd_lord = CLASSICAL_9_LORDS[(pd_start_idx + k) % 9]
                pd_years = LORD_YEARS[pd_lord] / TOTAL_CYCLE_YEARS * ad_years
                pd_days = pd_years * DAYS_PER_YEAR
                pd_end_jd = pd_jd + pd_days

                if pd_end_jd <= window_start_jd or pd_jd >= window_end_jd:
                    pd_jd = pd_end_jd
                    continue
                if _collapses_to_same_civil_date(pd_jd, pd_end_jd, window_start_jd, window_end_jd):
                    pd_jd = pd_end_jd
                    continue

                rows.append(_mk_row(3, pd_lord, pd_jd, pd_end_jd, window_start_jd, window_end_jd, (md_lord, ad_lord)))

                sk_start_idx = CLASSICAL_9_LORDS.index(pd_lord)
                sk_jd = pd_jd
                for m in range(9):
                    sk_lord = CLASSICAL_9_LORDS[(sk_start_idx + m) % 9]
                    sk_years = LORD_YEARS[sk_lord] / TOTAL_CYCLE_YEARS * pd_years
                    sk_days = sk_years * DAYS_PER_YEAR
                    sk_end_jd = sk_jd + sk_days

                    if sk_end_jd <= window_start_jd or sk_jd >= window_end_jd:
                        sk_jd = sk_end_jd
                        continue
                    if _collapses_to_same_civil_date(sk_jd, sk_end_jd, window_start_jd, window_end_jd):
                        sk_jd = sk_end_jd
                        continue

                    rows.append(_mk_row(4, sk_lord, sk_jd, sk_end_jd, window_start_jd, window_end_jd,
                                         (md_lord, ad_lord, pd_lord)))
                    # ZERO level_n=5 — do not recurse further.
                    sk_jd = sk_end_jd

                pd_jd = pd_end_jd
            ad_jd = ad_end_jd

        md_jd = md_end_jd
        lord_idx += 1

    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Tolerance — see the long-form written justification below.
# ─────────────────────────────────────────────────────────────────────────────
#
# _TOLERANCE_JUSTIFICATION
# -------------------------
# chart_dashas.start_iso/end_iso are TIMESTAMPTZ, populated by
# `ga_dashas_writer._jd_to_iso_utc()`, which converts a JD (UT) float to a
# calendar timestamp and ROUNDS TO THE NEAREST SECOND
# (`total_seconds = int(round(ut_hours * 3600.0))`). This module's
# `jd_to_datetime_utc()` replicates that same "round to nearest second"
# convention independently. Two arithmetically-correct implementations of the
# same classical recursive-proportional-subdivision algorithm, computed in
# IEEE-754 double precision throughout, can still disagree at the stored
# (rounded) boundary for two structurally different reasons:
#
#   (1) ROUNDING-BOUNDARY NOISE (dominant, bounded, ~1 second worst case).
#       If the TRUE underlying JD values agree to double-precision accuracy
#       (see (2) below — they do, by a wide margin) but the true fractional-
#       second value sits within double-precision noise of a .5-second
#       rounding boundary, the engine's rounding and this module's rounding
#       can land on adjacent integer seconds. This is a real, expected,
#       bounded artifact of ROUNDING alone, not of the dasha math: it can
#       never exceed 1 second, because both sides are rounding the *same*
#       true instant (to within double-precision noise) to the nearest
#       integer second.
#
#   (2) FLOATING-POINT ACCUMULATION (negligible at this magnitude/depth).
#       JD values in this module's operating window are ~2.43-2.49e6.
#       IEEE-754 double precision carries ~15-17 significant decimal digits
#       (machine epsilon ~2.22e-16 relative). At magnitude 2.5e6, one
#       floating-point ADD or MULTIPLY carries absolute error on the order
#       of 2.5e6 * 2.22e-16 ~= 5.6e-10 days ~= 4.8e-5 seconds. Each row's
#       boundary is reached via at most a few dozen chained additions/
#       multiplications (anchor -> MD boundary: ~1-45 chained MD-length
#       additions across at most ~5 wrapped cycles; MD -> AD -> PD -> Sukshma:
#       3 further multiply+add steps per level). Even a maximally pessimistic
#       (non-cancelling, purely additive) worst case of ~200 chained
#       operations bounds accumulated error at roughly 200 * 4.8e-5 s ~= 9.6
#       milliseconds — over 500x smaller than 1 second, and this module's
#       actual iteration count for a 150-year window is far lower (~15-20 MD
#       steps, not 200). In practice IEEE-754 rounding error is
#       direction-mixed, not monotonically additive, so real accumulated
#       error is smaller still. This source cannot plausibly explain a
#       multi-second, let alone multi-day, discrepancy.
#
#   (3) DAYS_PER_YEAR / algorithm-parameter mismatches are NOT a legitimate
#       source of tolerance-sized noise — if this module used a different
#       year convention (365.2425, sidereal ~365.2564, etc.) than the
#       engine's confirmed 365.25, boundaries would drift by MINUTES to
#       HOURS per year of elapsed time (e.g. a 0.0064-day/year mismatch
#       compounded over a ~20-year Venus Mahadasha is ~2.25 HOURS) — many
#       orders of magnitude past any reasonable tolerance. This module uses
#       the SAME confirmed 365.25 convention specifically so that a real
#       parameter mismatch would show up as a large, obvious divergence
#       rather than being masked by an overly generous tolerance.
#
# CHOSEN TOLERANCE: 5 SECONDS (both start and end boundary, independently).
#   - Comfortably covers (1)'s bounded <=1-second rounding noise with 5x
#     margin for any additional rounding-order variation between the two
#     independently-chosen (but individually correct) implementations.
#   - Two orders of magnitude above (2)'s realistic microsecond-to-low-
#     millisecond accumulation, and still ~20x below even the pessimistic
#     9.6ms worst-case bound in (2).
#   - Utterly dwarfed by the shortest period this table can ever hold: the
#     minimum possible level-4 (Sukshma) period is
#     Sun-MD(6y) x Sun-AD(6/120) x Sun-PD(6/120) x Sun-Sukshma(6/120)
#     = 6 * 0.05^3 years = 0.00075 years = 0.99e-1... = ~23,652 seconds
#     (~6.57 hours). A 5-second tolerance is ~0.02% of even that shortest
#     possible period — nowhere near loose enough to mask a genuine engine
#     defect (wrong lord order, wrong proportion formula, wrong DAYS_PER_YEAR,
#     dropped/duplicated period, off-by-one cycle) — all of which produce
#     discrepancies of hours-to-years, not seconds.
TOLERANCE_SECONDS_DEFAULT: float = 5.0


# ─────────────────────────────────────────────────────────────────────────────
# Row-level verdict — the ONLY place `two_pass_verdict` is called from.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class RowComparison:
    verdict: str
    lord_agree: bool
    start_diff_seconds: float
    end_diff_seconds: float
    engine_lord: str
    derived_lord: str
    engine_start: datetime
    derived_start: datetime
    engine_end: datetime
    derived_end: datetime


def compare_row(engine_lord: str, engine_start: datetime, engine_end: datetime,
                 derived_lord: str, derived_start: datetime, derived_end: datetime,
                 *, tolerance_seconds: float = TOLERANCE_SECONDS_DEFAULT) -> RowComparison:
    """Compare ONE engine row against ONE independently-derived row.

    Requires ALL of: exact lord match, start within tolerance, end within
    tolerance -> two_pass_verified. Any single failure -> divergent_flagged.
    This is the real second pass: `two_pass_verdict` (the sanctioned,
    ONLY-legal producer of the 'two_pass_verified' string) is fed a boolean
    this function computed from an independent derivation, not a literal.
    """
    lord_agree = engine_lord == derived_lord
    start_diff = abs((engine_start - derived_start).total_seconds())
    end_diff = abs((engine_end - derived_end).total_seconds())
    start_agree = start_diff <= tolerance_seconds
    end_agree = end_diff <= tolerance_seconds
    all_agree = lord_agree and start_agree and end_agree

    verdict = two_pass_verdict(all_agree, True)

    return RowComparison(
        verdict=verdict,
        lord_agree=lord_agree,
        start_diff_seconds=start_diff,
        end_diff_seconds=end_diff,
        engine_lord=engine_lord,
        derived_lord=derived_lord,
        engine_start=engine_start,
        derived_start=derived_start,
        engine_end=engine_end,
        derived_end=derived_end,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Full-chart verification driver (read-only — no DB writes).
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LevelSummary:
    level_n: int
    engine_row_count: int
    derived_row_count: int
    count_mismatch: bool
    two_pass_verified: int = 0
    divergent_flagged: int = 0
    divergences: list[dict] = field(default_factory=list)


@dataclass
class ChartVerificationResult:
    chart_id: str
    ayanamsha_id: str
    moon_sid_deg: float
    birth_jd_ut: float
    tolerance_seconds: float
    per_level: list[LevelSummary]

    @property
    def total_examined(self) -> int:
        return sum(l.two_pass_verified + l.divergent_flagged for l in self.per_level)

    @property
    def total_two_pass_verified(self) -> int:
        return sum(l.two_pass_verified for l in self.per_level)

    @property
    def total_divergent(self) -> int:
        return sum(l.divergent_flagged for l in self.per_level)


def fetch_engine_rows(conn: Any, chart_id: str, ayanamsha_id: str, level_n: int) -> list[tuple]:
    """Read the actual persisted chart_dashas rows for one level, classical
    Vimshottari only (system_id='vimshottari', kp_sublevel IS NULL — KP
    sub-periods are a DIFFERENT derivation, see module docstring in
    ga_dashas_writer.py re: register V-12; not this module's concern)."""
    import psycopg.rows as _pr
    with conn.cursor(row_factory=_pr.tuple_row) as cur:
        cur.execute(
            """
            SELECT lord_graha, start_iso, end_iso
            FROM chart_dashas
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND system_id = 'vimshottari' AND level_n = %s
              AND kp_sublevel IS NULL
            ORDER BY start_iso
            """,
            (chart_id, ayanamsha_id, level_n),
        )
        return cur.fetchall()


def verify_chart_vimshottari(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    *,
    tolerance_seconds: float = TOLERANCE_SECONDS_DEFAULT,
    max_divergences_recorded_per_level: int = 25,
) -> ChartVerificationResult:
    """Read-only. Independently re-derives the full levels 1-4 Vimshottari
    tree for (chart_id, ayanamsha_id) and compares it, level by level and row
    by row (in start-time order — both sides are monotonically increasing in
    time within a level, and counts are expected to match when the engine is
    correct), against what is actually persisted in chart_dashas. Does not
    write anything to the DB.
    """
    moon_sid_deg = fetch_moon_sidereal_longitude(conn, chart_id, ayanamsha_id)
    birth_jd_ut = fetch_birth_jd_utc(conn, chart_id)

    derived_rows = compute_independent_vimshottari_tree(moon_sid_deg, birth_jd_ut)
    derived_by_level: dict[int, list[IndependentDashaRow]] = {1: [], 2: [], 3: [], 4: []}
    for r in derived_rows:
        derived_by_level[r.level_n].append(r)
    for lvl in derived_by_level:
        derived_by_level[lvl].sort(key=lambda r: r.start_dt)

    per_level: list[LevelSummary] = []
    for level_n in (1, 2, 3, 4):
        engine_rows = fetch_engine_rows(conn, chart_id, ayanamsha_id, level_n)
        derived = derived_by_level[level_n]
        summary = LevelSummary(
            level_n=level_n,
            engine_row_count=len(engine_rows),
            derived_row_count=len(derived),
            count_mismatch=len(engine_rows) != len(derived),
        )
        for i, (eng_lord, eng_start, eng_end) in enumerate(engine_rows):
            if i >= len(derived):
                summary.divergent_flagged += 1
                if len(summary.divergences) < max_divergences_recorded_per_level:
                    summary.divergences.append({
                        "index": i, "reason": "no corresponding derived row (count mismatch)",
                        "engine_lord": eng_lord, "engine_start": eng_start.isoformat(),
                    })
                continue
            d = derived[i]
            cmp_ = compare_row(
                eng_lord, eng_start, eng_end,
                d.lord, d.start_dt, d.end_dt,
                tolerance_seconds=tolerance_seconds,
            )
            if cmp_.verdict == TWO_PASS_VERIFIED:
                summary.two_pass_verified += 1
            else:
                summary.divergent_flagged += 1
                if len(summary.divergences) < max_divergences_recorded_per_level:
                    summary.divergences.append({
                        "index": i,
                        "engine_lord": cmp_.engine_lord, "derived_lord": cmp_.derived_lord,
                        "lord_agree": cmp_.lord_agree,
                        "start_diff_seconds": cmp_.start_diff_seconds,
                        "end_diff_seconds": cmp_.end_diff_seconds,
                        "engine_start": cmp_.engine_start.isoformat(),
                        "derived_start": cmp_.derived_start.isoformat(),
                        "engine_end": cmp_.engine_end.isoformat(),
                        "derived_end": cmp_.derived_end.isoformat(),
                    })
        per_level.append(summary)

    return ChartVerificationResult(
        chart_id=chart_id,
        ayanamsha_id=ayanamsha_id,
        moon_sid_deg=moon_sid_deg,
        birth_jd_ut=birth_jd_ut,
        tolerance_seconds=tolerance_seconds,
        per_level=per_level,
    )
