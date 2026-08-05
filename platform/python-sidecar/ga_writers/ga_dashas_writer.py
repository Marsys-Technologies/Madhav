"""
ga_dashas_writer.py — GA7 dasha writer
========================================
Computes 7 dasha systems × 5 ayanamshas for the canonical native chart
and persists rows into `chart_dashas` (GA3 migration 206).

CAMPAIGN RAILS (BINDING — never deviate):
  - Engine: PyJHora via pyjhora_adapter. No natal_engine. No JH-parity oracle.
  - Two-pass = classical-rule reconstruction, NEVER "match JH".
  - Canonical chart_id: 482012f1-710e-4a25-994a-93821f5871aa ONLY.
  - CRITICAL OVERRIDE 1: DEPTH = 4-level Sukshma (level_n 1-4). ZERO level_n=5.
  - CRITICAL OVERRIDE 2: KP = kp_sublevel dimension (NOT level_n=6/7).
  - Calculation window: start_iso >= 1950-01-01, end_iso <= 2100-12-31.
  - Per-system incremental + idempotent (context-decay-safe).
  - Only 1 sanctioned JSONB column: concurrent_system_lords_jsonb.
    (R6 0e-dashameta / register V-11: triggered_yogas_jsonb_atomic and
    lord_transit_at_period_start_jsonb — formerly "sanctioned JSONB #2/#3" —
    were dropped via migration 428: both were permanently dead placeholders,
    no yoga-trigger or transit engine exists in GA7 to populate them.)

FORENSIC anchors (hard gate):
  Sun=Capricorn, Moon nak=Purva Bhadrapada, Lagna=Aries,
  Tithi=Shukla Tritiya, Vara=Ravivara, Yoga=Shiva, Karana=Garaja.
  Birth: 1984-02-05 10:43 IST, lat 20.27, lon 85.84, tz_offset +5.5.

FORENSIC Vimshottari assertion:
  Moon in Purva Bhadrapada (nak index 25, 0-based 24) → lord = Jupiter.
  Starting Mahadasha MUST be Jupiter.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Generator

from brahmagyan.verification_vocab import (
    CLASSICAL_MATCH,
    DIVERGENT_FLAGGED,
    TWO_PASS_VERIFIED,
    UNVERIFIED_DEFAULT,
)
from ga_writers._idempotency import replace_prior_chart_dashas
from ga_writers._telemetry import update_asset_throughput
from ga_writers._vimshottari_independent_verifier import (
    compare_row as _iv_compare_row,
    compute_independent_vimshottari_tree as _iv_compute_independent_tree,
)
from ga_writers.ga_condition_writer import _DIVISIONAL_DIGNITY_NORMALIZE
from pipeline.orchestrator.birth_params import CANONICAL_CHART_ID as _BP_CANONICAL_CHART_ID, resolve_birth_params

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# 5 canonical ayanamshas
AYANAMSHAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]

# Calculation window
WINDOW_START = date(1950, 1, 1)
WINDOW_END = date(2100, 12, 31)

# BIRTH_TZ_OFFSET used as .get() fallback for tz in _birth_jd_utc / _get_moon_position
# when the birth_params dict was built without an explicit tz_offset_hours field.
BIRTH_TZ_OFFSET = 5.5  # IST = UTC+5:30
# NOTE: BIRTH_IST / BIRTH_LAT / BIRTH_LON deleted (B1 elimination — every chart,
# including the native, now sources birth params from public.charts via fetch_birth_params).

# Vimshottari constants
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_SEQUENCE = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]
VIMSHOTTARI_TOTAL_YEARS = 120

# V-12 fix: KP sub-period rows get their OWN system_id, distinct from
# "vimshottari" classical Antardasha/Pratyantardasha rows. Before this fix,
# compute_kp_subperiods() wrote KP sub/sub-sub rows under system_id=
# "vimshottari" (same as classical), differentiated only by the kp_sublevel
# column — any consumer querying system_id='vimshottari' AND level_n=2
# without ALSO filtering kp_sublevel IS NULL got both the classical
# Antardasha row and the KP sub-period row for the same start date, with
# divergent end dates (register V-12; get_dashas.ts's default facets are
# exactly system=vimshottari + level<=3, so this collision was live in the
# default retrieval path, not just a theoretical query shape).
KP_SYSTEM_ID = "vimshottari_kp"

# Populated from L0 before build; _load_nakshatra_lords_l0() overwrites from reference_nakshatras.
# Fallback = correct Parashari vimshottari cycle (28-element, index 0 unused) so unit tests
# without a DB still work. L0 is the authority; this matches what reference_nakshatras holds.
_CLASSICAL_CYCLE = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
_NAKSHATRA_LORDS_1BASED: list[str] = [""] + [_CLASSICAL_CYCLE[(i - 1) % 9] for i in range(1, 28)]

def _load_nakshatra_lords_l0(conn: Any) -> None:
    """Populate _NAKSHATRA_LORDS_1BASED (28-element, index 0='') from reference_nakshatras."""
    global _NAKSHATRA_LORDS_1BASED
    import psycopg.rows as _pr
    with conn.cursor(row_factory=_pr.tuple_row) as cur:
        cur.execute("SELECT lord FROM reference_nakshatras ORDER BY nakshatra_id")
        lords = [row[0].capitalize() for row in cur.fetchall()]
    _NAKSHATRA_LORDS_1BASED = [""] + lords  # 1-based; index 0 unused


# FORENSIC: Purva Bhadrapada is nak 25 (1-based), lord = Jupiter
FORENSIC_MOON_NAK_NAME = "Purva Bhadrapada"
FORENSIC_MOON_NAK_IDX_1BASED = 25
FORENSIC_VIMSHOTTARI_STARTING_LORD = "Jupiter"  # MUST match engine output

# Yogini constants
YOGINI_SEQUENCE = [
    ("Mangala",  "Moon",    1),
    ("Pingala",  "Sun",     2),
    ("Dhanya",   "Jupiter", 3),
    ("Bhramari", "Mars",    4),
    ("Bhadrika", "Mercury", 5),
    ("Ulka",     "Saturn",  6),
    ("Siddha",   "Venus",   7),
    ("Sankata",  "Rahu",    8),
]
YOGINI_TOTAL_YEARS = 36

# Ashtottari constants
ASHTOTTARI_SEQUENCE = [
    ("Sun",     6),
    ("Moon",    15),
    ("Mars",    8),
    ("Mercury", 17),
    ("Saturn",  10),
    ("Jupiter", 19),
    ("Rahu",    12),
    ("Venus",   21),
]
ASHTOTTARI_TOTAL_YEARS = 108
ASHTOTTARI_LORDS_ORDER = [lord for lord, _ in ASHTOTTARI_SEQUENCE]

# Naisargika dasha — age-based brackets (120y total)
NAISARGIKA_SEQUENCE = [
    ("Moon",    4),    # 0-4
    ("Mars",    12),   # 4-16
    ("Mercury", 16),   # 16-32
    ("Venus",   20),   # 32-52
    ("Jupiter", 20),   # 52-72
    ("Sun",     20),   # 72-92
    ("Saturn",  20),   # 92-112
    ("Rahu",    8),    # 112-120
]
NAISARGIKA_TOTAL_YEARS = 120

# Kalachakra — BPHS Ch.53 simplified (proper sign-based deha/jeeva)
# 12 signs × 9 years base, paramayush = 100y; navamsha-anchored
KALACHAKRA_SIGN_YEARS = [
    # (sign_name, years) — savya signs (forward-running)
    ("Aries",       7),
    ("Taurus",     16),
    ("Gemini",      9),
    ("Cancer",     21),
    ("Leo",         5),
    ("Virgo",       9),
    ("Libra",      14),
    ("Scorpio",     7),
    ("Sagittarius", 12),
    ("Capricorn",  16),
    ("Aquarius",    9),
    ("Pisces",     21),
]
KALACHAKRA_TOTAL_YEARS = sum(y for _, y in KALACHAKRA_SIGN_YEARS)  # 146y (uses ~100y window)

# Planet relationship table (friend/enemy/neutral) — classical Parashari
_FRIEND = {
    "Sun":     {"Moon", "Mars", "Jupiter"},
    "Moon":    {"Sun", "Mercury"},
    "Mars":    {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus":   {"Mercury", "Saturn"},
    "Saturn":  {"Mercury", "Venus"},
    "Rahu":    {"Venus", "Saturn"},
    "Ketu":    {"Venus", "Saturn"},
}
_ENEMY = {
    "Sun":     {"Venus", "Saturn"},
    "Moon":    {"None"},
    "Mars":    {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus":   {"Sun", "Moon"},
    "Saturn":  {"Sun", "Moon", "Mars"},
    "Rahu":    {"Sun", "Moon"},
    "Ketu":    {"Sun", "Moon"},
}


def _planet_relationship(lord: str, parent: str | None) -> str | None:
    """Classical Parashari lord-to-parent relationship."""
    if parent is None:
        return None
    friends = _FRIEND.get(lord, set())
    enemies = _ENEMY.get(lord, set())
    if parent in friends:
        return "friend"
    if parent in enemies:
        return "enemy"
    return "neutral"


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[ga_dashas] DATABASE_URL not set")


@contextmanager
def _conn() -> Generator:
    import psycopg
    with psycopg.connect(_db_url()) as conn:
        yield conn


# ── JD / date helpers ─────────────────────────────────────────────────────────

def _birth_jd_utc(birth: dict) -> float:
    """Birth Julian Day (UT). Requires a non-None birth_params dict sourced from
    public.charts via fetch_birth_params() — B1 elimination: no BIRTH_* fallback."""
    import swisseph as swe
    if not birth:
        raise ValueError("[_birth_jd_utc] birth_params is falsy; every chart must supply DB-sourced birth params")
    iso = birth["datetime_iso"]
    tz = float(birth.get("tz_offset_hours", BIRTH_TZ_OFFSET))
    dt_local = datetime.fromisoformat(iso)
    dt_utc = dt_local - timedelta(hours=tz)
    return swe.julday(
        dt_utc.year, dt_utc.month, dt_utc.day,
        dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0,
    )


def _datetime_to_jd(dt: datetime) -> float:
    """UTC datetime -> Julian Day (UT). Inverse of _jd_to_iso_utc (V-9)."""
    import swisseph as swe
    return swe.julday(
        dt.year, dt.month, dt.day,
        dt.hour + dt.minute / 60.0 + dt.second / 3600.0,
    )


def _jd_to_date(jd: float) -> date:
    import swisseph as swe
    y, m, d, _ = swe.revjul(jd)
    return date(int(y), int(m), int(d))


def _date_to_iso(d: date) -> str:
    return d.isoformat() + "T00:00:00+00:00"


def _jd_to_iso_utc(jd: float) -> str:
    """Full-precision UTC ISO-8601 timestamp from a Julian Day (UT).

    V-9 fix: chart_dashas.start_iso/end_iso are TIMESTAMPTZ columns (migration
    206), but every boundary was previously built via _jd_to_date() -> date ->
    _date_to_iso() (hardcoded "T00:00:00"), truncating the real ephemeris
    time-of-day and — because the engine works in JD (fractional days), not
    midnight-aligned dates — silently shifting the true boundary by up to a
    day. This helper preserves swe.revjul()'s fractional-hour return so the
    stored timestamp matches what the engine actually computed.
    """
    import swisseph as swe
    y, m, d, ut_hours = swe.revjul(jd)
    # ut_hours is a float in [0, 24); build the date at midnight then add the
    # fractional day as a timedelta so a rounding-induced day rollover (e.g.
    # 23:59:59.6 -> 24:00:00) is handled correctly across month/year boundaries
    # by datetime arithmetic instead of hand-rolled calendar math.
    total_seconds = int(round(ut_hours * 3600.0))
    dt = datetime(int(y), int(m), int(d), tzinfo=timezone.utc) + timedelta(seconds=total_seconds)
    return dt.isoformat()


def _years_to_days(years: float) -> float:
    return years * 365.25


def _days_between(d1: date, d2: date) -> float:
    return (d2 - d1).days


# ── Ayanamsha + Moon position ─────────────────────────────────────────────────

def _get_moon_position(ayanamsha_id: str, birth: dict) -> tuple[float, float]:
    """
    Returns (moon_sidereal_lon, birth_jd_utc).
    Requires a non-None birth_params dict sourced from public.charts —
    B1 elimination: no BIRTH_* fallback for native or any other chart.
    Uses pyjhora_adapter engine.
    """
    from pyjhora_adapter.compute import compute_chart
    from pyjhora_adapter._ayanamsha import resolve_mode
    from pyjhora_adapter._jhora import drik

    if not birth:
        raise ValueError("[_get_moon_position] birth_params is falsy; every chart must supply DB-sourced birth params")
    lat = float(birth["latitude_deg"])
    lon = float(birth["longitude_deg"])
    tz = float(birth.get("tz_offset_hours", BIRTH_TZ_OFFSET))

    jd = _birth_jd_utc(birth)
    mode, _ = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = drik.Place("native", lat, lon, tz)

    # Use pyjhora_adapter.compute for Moon sidereal longitude
    chart = compute_chart(jd, lat, lon, tz, ayanamsha_id)
    for body in chart.get("bodies", []):
        if body.get("name") == "Moon":
            return body.get("sidereal_longitude", 0.0), jd
    # Fallback: direct calculation
    from pyjhora_adapter._jhora import drik as _drik
    moon_lon = _drik.sidereal_longitude(jd, 1)  # 1 = Moon in swisseph
    return float(moon_lon), jd


def _get_moon_nakshatra_lord(moon_sid_lon: float) -> tuple[int, str, str]:
    """
    Returns (nak_idx_1based, nak_name, lord).
    Nak 25 = Purva Bhadrapada → lord = Jupiter (FORENSIC anchor).
    """
    from pyjhora_adapter._names import NAKSHATRA_NAMES
    nak_span = 360.0 / 27
    nak_idx_0 = int(moon_sid_lon / nak_span)
    nak_idx_1 = nak_idx_0 + 1  # 1-based
    if nak_idx_1 > 27:
        nak_idx_1 = 27
    nak_name = NAKSHATRA_NAMES[nak_idx_1] if nak_idx_1 < len(NAKSHATRA_NAMES) else f"Nak{nak_idx_1}"
    lord = _NAKSHATRA_LORDS_1BASED[nak_idx_1] if nak_idx_1 < len(_NAKSHATRA_LORDS_1BASED) else "Unknown"
    return nak_idx_1, nak_name, lord


# ── Window filtering ──────────────────────────────────────────────────────────

def _clip_to_window(start_d: date, end_d: date) -> tuple[date | None, date | None, bool, bool]:
    """
    Clip period to [WINDOW_START, WINDOW_END].
    Returns (clipped_start, clipped_end, truncated_start, truncated_end)
    or (None, None, _, _) if period is entirely outside window.
    """
    if end_d <= WINDOW_START or start_d >= WINDOW_END:
        return None, None, False, False
    trunc_start = start_d < WINDOW_START
    trunc_end = end_d > WINDOW_END
    clipped_start = max(start_d, WINDOW_START)
    clipped_end = min(end_d, WINDOW_END)
    return clipped_start, clipped_end, trunc_start, trunc_end


# ── Backdating: find window-aligned start for 1950 ───────────────────────────

def _find_cycle_start_for_window(
    birth_jd: float,
    moon_sid: float,
    sequence: list[str],
    years_map: dict[str, float],
    total_years: float,
) -> tuple[float, str, int]:
    """
    Walk Vimshottari cycles backward from birth to cover 1950-01-01.
    Returns (effective_start_jd, starting_lord, lord_seq_start_idx).

    For natives born 1950-2100 (native born 1984): backdate to cover 1950.
    Strategy: walk MD cycles backward from birth until we're before 1950-01-01.
    """
    window_start_jd = sum(
        [1721425.5 + (WINDOW_START - date(1, 1, 1)).days]  # approximate JD for 1950-01-01
    )
    # More precise: 1950-01-01 JD
    import swisseph as swe
    window_start_jd = swe.julday(1950, 1, 1, 0.0)

    # Compute balance at birth
    nak_span = 360.0 / 27
    nak_idx_0 = int(moon_sid / nak_span)
    nak_lord = _NAKSHATRA_LORDS_1BASED[nak_idx_0 + 1]
    nak_progress = (moon_sid - nak_idx_0 * nak_span) / nak_span
    balance_years = years_map[nak_lord] * (1.0 - nak_progress)

    # Sequence from birth
    seq_start_at_birth = sequence.index(nak_lord)

    # Walk forward from birth to find all MD periods, then find what covers 1950
    # The entire cycle covers 120 years. Native born 1984, so 1984 - 120 = 1864 (prior cycle).
    # We need to backtrack full cycles until before 1950.
    # A full 120y cycle covers ~43,800 days.
    cycle_days = _years_to_days(total_years)

    # Start from birth and trace backward full cycles
    # Period starting at birth: balance_years of nak_lord
    # Period starting birth - (120y - balance_of_prior_lord_chain) etc.
    # Simpler: go back N full cycles from birth such that start covers 1950
    # 1984 birth - 1950 = 34 years = less than one cycle (120y), so we just
    # need to go back partial in the same cycle.

    # Find the jd at cycle boundary BEFORE birth
    # The cycle before birth started at birth - (balance of prior period chain)
    # Actually: balance_years = portion of nak_lord remaining at birth
    # So the full nak_lord period would have started at birth - (years_map[nak_lord] - balance_years)*days

    # We'll do a simple approach: compute the start of the cycle that covers 1950
    # by walking backward from birth
    effective_start_jd = birth_jd - _years_to_days(years_map[nak_lord] - balance_years)

    # Now walk backward adding full periods in reverse sequence until we're before window_start_jd
    # The sequence going backward from nak_lord is: prev of nak_lord (reverse of SEQUENCE)
    idx = seq_start_at_birth
    while effective_start_jd > window_start_jd:
        # Go back one period (previous lord in cycle)
        idx = (idx - 1) % len(sequence)
        prev_lord = sequence[idx]
        effective_start_jd -= _years_to_days(years_map[prev_lord])

    # Now effective_start_jd is before 1950; idx is the starting lord
    return effective_start_jd, sequence[idx], idx


# ── Natal lord context (Addition A) — register V-1 / G-7 / D-1 fix ──────────
#
# CLAUDE.md §N.5 (L1-is-authority): an L2+ (here: a denormalized column on an
# L1 table itself) NEVER restates an L1 computed value as its own truth — it
# JOINS to chart_facts and inherits the value. The prior version of this file
# hardcoded a module-level `_NATAL_CONTEXT` dict of "FORENSIC-grounded"
# natal values that were, on live audit against chart_facts + chart_divisionals
# for chart 482012f1 (lahiri_chitrapaksha), wrong for 6 of 9 grahas:
#   Mars:    dict said Capricorn/h10/exalted   ; chart_facts = Libra/h7/neutral_sign
#   Rahu:    dict said Leo/h5                  ; chart_facts = Taurus/h2
#   Ketu:    dict said Aquarius/PurvaBhadrapada/h11 (= a copy of MOON's values)
#                                               ; chart_facts = Scorpio/Jyeshtha/h8
#   Sun:     dict said dignity "exalted_friend" (not even a real dignity value)
#                                               ; chart_facts = Enemy -> enemy_sign
#   Venus:   dict said nakshatra "Mula" (= a copy of JUPITER's nakshatra)
#                                               ; chart_facts = Purva Ashadha
#   Saturn:  dict said house_d1=11 (G-7's cited contradiction)
#                                               ; chart_facts = house_d1=7
# Moon's own house_d1 was also wrong (dict said 12; chart_facts = 11).
# Only Jupiter and Mercury's *sign* happened to match by coincidence.
#
# Fix: re-derive ALL lord_natal_* columns from chart_facts (sign/nakshatra/
# house_d1 via fact_category='graha_position') + chart_divisionals (dignity_d1
# via fact_category='varga_dignity', varga='D1') + chart_facts
# (shadbala_total via fact_category='graha_shadbala_total', fact_key='rupa')
# at BUILD time, per (chart_id, ayanamsha_id) — never hand-copied again.

# Yogini system uses deity names, not graha names, as its `lord` — this maps
# each deity back to the graha whose natal condition it inherits (unchanged
# mapping from before; only the VALUES were wrong, not this alias table).
_YOGINI_DEITY_TO_GRAHA: dict[str, str] = {
    name: graha for name, graha, _ in YOGINI_SEQUENCE
}

# Cache: (chart_id, ayanamsha_id) -> {graha_or_deity_name: {house_d1, sign,
# nakshatra, dignity_d1, shadbala_total}}. Populated by _load_natal_context();
# _get_natal_context() reads the "active" entry set by build_system() for the
# (chart_id, ayanamsha_id) currently being built.
_NATAL_CONTEXT_CACHE: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
_CURRENT_NATAL_CONTEXT: dict[str, dict[str, Any]] = {}
_CURRENT_NATAL_CONTEXT_KEY: tuple[str, str] | None = None


def _load_natal_context(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, dict[str, Any]]:
    """Load real lord_natal_* values from chart_facts + chart_divisionals for
    (chart_id, ayanamsha_id), cached per key. Canonical-or-floor: a graha with
    no chart_facts row (or any query failure — e.g. a caller-injected fake conn
    in a unit test that doesn't implement full cursor semantics) yields
    all-None fields (never a fabricated substitute), matching this codebase's
    established graceful-degradation pattern for non-critical enrichment reads
    (see _load_special_points in ga_structural_writer.py).
    """
    key = (chart_id, ayanamsha_id)
    cached = _NATAL_CONTEXT_CACHE.get(key)
    if cached is not None:
        return cached

    from ga_writers.ga_positions_writer import PLANET_TO_SUBJECT
    subject_to_graha = {v: k for k, v in PLANET_TO_SUBJECT.items() if k != "Lagna"}

    ctx: dict[str, dict[str, Any]] = {}
    try:
        _load_natal_context_inner(conn, chart_id, ayanamsha_id, subject_to_graha, ctx)
    except Exception as exc:
        logger.warning(
            "[ga_dashas] _load_natal_context query failed for chart_id=%s ayanamsha_id=%s "
            "(lord_natal_* columns will be NULL for this build, not fabricated): %s",
            chart_id, ayanamsha_id, exc,
        )
    _NATAL_CONTEXT_CACHE[key] = ctx
    return ctx


def _load_natal_context_inner(
    conn: Any, chart_id: str, ayanamsha_id: str,
    subject_to_graha: dict[str, str], ctx: dict[str, dict[str, Any]],
) -> None:
    # tuple_row forced explicitly: the orchestrator's shared worker connection
    # (pipeline.orchestrator.db.connect()) defaults to row_factory=dict_row, and every
    # loop below unpacks fetchall() rows positionally (`for subj, key_, vtxt, vnum in
    # ...`). Under a dict-row cursor that silently unpacks each dict's KEYS instead of
    # its values, so every row is dropped by `subject_to_graha.get(subj)` returning
    # None — no exception, just all-NULL lord_natal_* columns. Same bug class as
    # _compute_dynamic_chara_params (see its comment above); fixed alongside it,
    # 2026-07-10.
    import psycopg.rows as _pr
    with conn.cursor(row_factory=_pr.tuple_row) as cur:
        cur.execute(
            """
            SELECT fact_subject, fact_key, fact_value_text, fact_value_num
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND fact_category = 'graha_position'
              AND fact_key IN ('sign', 'nakshatra', 'house_d1')
              AND fact_subject = ANY(%s)
            """,
            (chart_id, ayanamsha_id, list(subject_to_graha.keys())),
        )
        for subj, key_, vtxt, vnum in cur.fetchall():
            graha = subject_to_graha.get(subj)
            if not graha:
                continue
            entry = ctx.setdefault(graha, {"house_d1": None, "sign": None, "nakshatra": None,
                                            "dignity_d1": None, "shadbala_total": None})
            if key_ == "sign":
                entry["sign"] = vtxt
            elif key_ == "nakshatra":
                entry["nakshatra"] = vtxt
            elif key_ == "house_d1":
                entry["house_d1"] = int(vnum) if vnum is not None else None

        cur.execute(
            """
            SELECT graha, fact_value_text
            FROM chart_divisionals
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND varga = 'D1' AND fact_category = 'varga_dignity' AND fact_key = 'dignity'
            """,
            (chart_id, ayanamsha_id),
        )
        for graha, dignity_text in cur.fetchall():
            entry = ctx.setdefault(graha, {"house_d1": None, "sign": None, "nakshatra": None,
                                            "dignity_d1": None, "shadbala_total": None})
            entry["dignity_d1"] = _DIVISIONAL_DIGNITY_NORMALIZE.get(dignity_text, dignity_text.lower() if dignity_text else None)

        cur.execute(
            """
            SELECT fact_subject, fact_value_num
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND fact_category = 'graha_shadbala_total' AND fact_key = 'rupa'
              AND fact_subject = ANY(%s)
            """,
            (chart_id, ayanamsha_id, list(subject_to_graha.keys())),
        )
        for subj, vnum in cur.fetchall():
            graha = subject_to_graha.get(subj)
            if not graha:
                continue
            entry = ctx.setdefault(graha, {"house_d1": None, "sign": None, "nakshatra": None,
                                            "dignity_d1": None, "shadbala_total": None})
            entry["shadbala_total"] = float(vnum) if vnum is not None else None


def set_natal_context(chart_id: str, ayanamsha_id: str, ctx: dict[str, dict[str, Any]]) -> None:
    """Explicitly seed the active natal-context view. Production code should
    never call this (build_system() loads from the DB) — it exists so unit
    tests that compute a system directly (no DB, no build_system()) can supply
    a deliberate, correctly-labeled fixture instead of silently getting
    all-None natal fields."""
    global _CURRENT_NATAL_CONTEXT, _CURRENT_NATAL_CONTEXT_KEY
    key = (chart_id, ayanamsha_id)
    _NATAL_CONTEXT_CACHE[key] = ctx
    _CURRENT_NATAL_CONTEXT = ctx
    _CURRENT_NATAL_CONTEXT_KEY = key


def _activate_natal_context(chart_id: str, ayanamsha_id: str, conn: Any) -> None:
    """Load (if needed) and activate the natal context for (chart_id, ayanamsha_id)
    as the view _get_natal_context() reads from."""
    global _CURRENT_NATAL_CONTEXT, _CURRENT_NATAL_CONTEXT_KEY
    key = (chart_id, ayanamsha_id)
    if _CURRENT_NATAL_CONTEXT_KEY == key:
        return
    _CURRENT_NATAL_CONTEXT = _load_natal_context(conn, chart_id, ayanamsha_id)
    _CURRENT_NATAL_CONTEXT_KEY = key


# Karakas mapping (7 Jaimini karakas based on degree-ordering — FORENSIC chart)
# AK=Sun(highest deg), AmK=Mars, BK=Mercury, MK=Saturn, PK=Jupiter, GK=Venus, DK=Moon
_JAIMINI_KARAKAS = {
    "Sun":     "AK",    # Atmakaraka
    "Mars":    "AmK",   # Amatyakaraka
    "Mercury": "BK",    # Bhratrukaraka
    "Saturn":  "MK",    # Matrukaraka
    "Jupiter": "PK",    # Pitrukaraka
    "Venus":   "GK",    # Gnatikaraka
    "Moon":    "DK",    # Darakaraka
}


def _get_natal_context(lord: str) -> dict[str, Any]:
    graha = _YOGINI_DEITY_TO_GRAHA.get(lord, lord)
    ctx = _CURRENT_NATAL_CONTEXT.get(graha, {})
    return {
        "lord_natal_house_d1": ctx.get("house_d1"),
        "lord_natal_sign": ctx.get("sign"),
        "lord_natal_nakshatra": ctx.get("nakshatra"),
        "lord_natal_dignity_d1": ctx.get("dignity_d1"),
        "lord_natal_shadbala_total": ctx.get("shadbala_total"),
    }


def _get_karakas_active(lord: str, parent_lord: str | None) -> list[str]:
    """Karakas active at this branch (Addition Q)."""
    active = []
    for graha, karaka in _JAIMINI_KARAKAS.items():
        if graha == lord or graha == parent_lord:
            active.append(f"{graha}:{karaka}")
    return active


# ── Two-pass verification ─────────────────────────────────────────────────────

def _verify_vimshottari(rows: list[dict], moon_sid: float,
                        chart_id: str = CANONICAL_CHART_ID) -> str:
    """
    Two-pass verification for Vimshottari:
    Pass 1: algebraic — sum of all L1 years ≈ N × 120y (within 1 day) [structural,
            any chart].
    Pass 2: FORENSIC — the period containing the NATIVE birth date (1984-02-05)
            must have lord = Jupiter. Native-anchored; run only for the native
            chart (Phase 3B). A non-native chart has its own birth date + lord.
    Returns 'two_pass_verified' or raises ValueError.
    """
    l1_rows = [r for r in rows if r["level_n"] == 1]
    if not l1_rows:
        raise ValueError("Vimshottari: no L1 rows")

    # Pass 2 (FORENSIC) — native-only regression guard.
    if chart_id == CANONICAL_CHART_ID:
        birth_date = date(1984, 2, 5)
        birth_period_lord: str | None = None
        for row in l1_rows:
            if row["start_date"] <= birth_date <= row["end_date"]:
                birth_period_lord = row["lord_graha"]
                break
        if birth_period_lord is None:
            raise ValueError("Vimshottari: no L1 row covers birth date 1984-02-05")
        if birth_period_lord != FORENSIC_VIMSHOTTARI_STARTING_LORD:
            raise ValueError(
                f"FORENSIC HALT: Vimshottari starting lord={birth_period_lord!r}, "
                f"expected={FORENSIC_VIMSHOTTARI_STARTING_LORD!r}. "
                f"Moon nakshatra must be Purva Bhadrapada (lord=Jupiter)."
            )

    # §6.18 EARNEDNESS RULING (2026-08-02): Pass 2 above is the ONLY check here that can fail
    # for a reason other than a bug in itself, and it runs for the native chart only. Pass 1
    # below cannot fail at all — its tolerance comparison ends in a bare `pass`. So a non-native
    # chart reaching this point has had NOTHING contradicted, and must not claim otherwise.
    verdict = TWO_PASS_VERIFIED if chart_id == CANONICAL_CHART_ID else UNVERIFIED_DEFAULT

    # Pass 1: algebraic — each L1 period should have correct duration
    for row in l1_rows:
        lord = row["lord_graha"]
        expected_years = VIMSHOTTARI_YEARS.get(lord, 0)
        if expected_years == 0:
            continue
        actual_days = row["duration_days"]
        expected_days = _years_to_days(expected_years)
        # Allow 5% tolerance for balance-period (first/last periods may be partial)
        tol_days = max(expected_days * 0.05, 30)
        if abs(actual_days - expected_days) > tol_days + 1:
            # Only fail on interior (non-partial) periods
            pass  # Partial periods are expected at boundaries

    return verdict


def _apply_vimshottari_independent_verification(
    rows: list[dict],
    moon_sid: float,
    birth_jd: float,
) -> int:
    """A3 fix (M-22 Stage 3 wiring gap): stamp EVERY level_n 1-4, non-KP
    Vimshottari row with ITS OWN `verification_pass_status`, earned by
    genuinely comparing it against an independently-computed dasha tree —
    replacing the old broadcast pattern where `_verify_vimshottari()`
    examined only the L1 rows and produced ONE string, which the caller then
    (a) applied to every L1 row regardless of which one it actually checked
    and (b) defaulted every L2-4 row to `UNVERIFIED_DEFAULT` without ever
    trying to check them. `_vimshottari_independent_verifier.py` (PR #1047)
    was built and discrimination-tested for exactly this job but was never
    actually called from this write path until now — it was importable by
    nothing but its own test file.

    Uses `_vimshottari_independent_verifier.compute_independent_vimshottari_tree`
    (an independently re-implemented, from-first-principles re-derivation of
    the same classical M/A/P/Sukshma recursion — see that module's docstring
    for the full independence audit) and `.compare_row` (the sanctioned
    per-row verdict producer, already discrimination-tested against
    wrong-lord and out-of-tolerance-boundary inputs in
    `test_vimshottari_independent_verifier.py`) — this function does not
    reimplement any comparison logic of its own; it only pairs rows and
    calls the real functions.

    INDEPENDENCE SCOPE (read before assuming this is identical to the
    standalone diagnostic): this call site feeds the independent tree
    builder the SAME `moon_sid`/`birth_jd` values `compute_vimshottari()`
    itself was called with (computed once, by `build_system()`, above) —
    NOT a separately-DB-fetched Moon longitude the way the standalone
    diagnostic `verify_chart_vimshottari()` does (which reads the
    `chart_facts` MOON longitude_sidereal fact written by a *different* L1
    writer, `ga_positions_writer`, via `fetch_moon_sidereal_longitude`).
    That fuller input-source independence remains a property of the
    standalone diagnostic entry point only. Requiring a live DB read for
    inputs at THIS call site would make per-row verification silently
    unavailable whenever `build_system()` runs with `skip_db=True` (a real,
    exercised unit-test path — see `test_ga7_writer.py`) or without an open
    connection at this point in the call. What this DOES independently
    verify, on every real build: whether the two SEPARATELY-CODED
    implementations of the classical Vimshottari recursion (this file's
    `compute_vimshottari` vs. the Stage 3 module's
    `compute_independent_vimshottari_tree`) agree lord-by-lord and
    boundary-by-boundary — exactly the class of defect (wrong lord
    sequence, wrong proportion formula, wrong day conversion, off-by-one
    cycle, boundary/window-clipping bug) a second, independently written
    implementation is positioned to catch.

    PERFORMANCE: `compute_independent_vimshottari_tree()` — a full
    first-principles re-derivation of the whole 150-year window — is the
    expensive part of this check. It is called EXACTLY ONCE here, regardless
    of how many rows `rows` contains. Per-row cost after that is a single
    O(1) `compare_row()` call; grouping engine rows by level and sorting
    each level is O(n log n). This function is O(n log n) overall, not
    O(n^2) — it does not recompute the independent tree inside the per-row
    loop.

    Mutates `rows` in place (sets `verification_pass_status` on every
    level_n 1-4, `kp_sublevel is None` row). KP sub-periods and any row
    outside level_n 1-4 are untouched here — the caller's existing
    broadcast-fallback loop still stamps those `UNVERIFIED_DEFAULT`,
    matching this module's own documented scope (it never examines KP
    sub-periods — a different derivation, see register V-12).

    Returns the count of rows stamped (diagnostic/logging only).
    """
    tree_result = _iv_compute_independent_tree(moon_sid, birth_jd)
    derived_by_level: dict[int, list] = {1: [], 2: [], 3: [], 4: []}
    for r in tree_result.rows:
        derived_by_level[r.level_n].append(r)
    for lvl in derived_by_level:
        derived_by_level[lvl].sort(key=lambda r: r.start_dt)

    engine_by_level: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: []}
    for row in rows:
        lvl = row["level_n"]
        if lvl in engine_by_level and row.get("kp_sublevel") is None:
            engine_by_level[lvl].append(row)
    for lvl in engine_by_level:
        engine_by_level[lvl].sort(key=lambda r: r["start_iso"])

    stamped = 0
    for level_n in (1, 2, 3, 4):
        engine_rows = engine_by_level[level_n]
        derived_rows = derived_by_level[level_n]
        n = max(len(engine_rows), len(derived_rows))
        for i in range(n):
            eng = engine_rows[i] if i < len(engine_rows) else None
            der = derived_rows[i] if i < len(derived_rows) else None
            if eng is None:
                # A derived-only period (no engine counterpart at this
                # index) has no engine row here to carry a verdict — this
                # signals a real derivation gap, but there is nothing on the
                # engine side to stamp.
                continue
            if der is None:
                # An engine row with no independent counterpart at all — a
                # genuine row-count mismatch (the H1 case, in the standalone
                # module's terms). Never left silently unstamped.
                eng["verification_pass_status"] = DIVERGENT_FLAGGED
                stamped += 1
                continue
            eng_start = datetime.fromisoformat(eng["start_iso"])
            eng_end = datetime.fromisoformat(eng["end_iso"])
            cmp_ = _iv_compare_row(
                eng["lord_graha"], eng_start, eng_end,
                der.lord, der.start_dt, der.end_dt,
            )
            eng["verification_pass_status"] = cmp_.verdict
            stamped += 1
    return stamped


def _verify_yogini(rows: list[dict]) -> str:
    """
    Two-pass verification: yogini 8-cycle, sum=36y, lords in known sequence.
    """
    l1_rows = [r for r in rows if r["level_n"] == 1]
    if not l1_rows:
        raise ValueError("Yogini: no L1 rows")

    known_lords = {name for name, _, _ in YOGINI_SEQUENCE}
    for row in l1_rows:
        if row["lord_graha"] not in known_lords:
            raise ValueError(f"Yogini: unknown lord {row['lord_graha']!r}")

    return CLASSICAL_MATCH  # membership check only — relay fidelity, not re-derivation (§6.18 ruling)


def _verify_ashtottari(rows: list[dict]) -> str:
    """
    Two-pass: sum=108y, lords in known order.
    """
    l1_rows = [r for r in rows if r["level_n"] == 1]
    if not l1_rows:
        return "classical_match"  # Non-applicable → empty is OK

    known = set(ASHTOTTARI_LORDS_ORDER)
    for row in l1_rows:
        if row["lord_graha"] not in known:
            raise ValueError(f"Ashtottari: unknown lord {row['lord_graha']!r}")

    return CLASSICAL_MATCH  # membership check only — relay fidelity, not re-derivation (§6.18 ruling)


def _verify_chara(rows: list[dict]) -> str:
    """
    Jaimini Chara verification: signs in zodiac order, correct L1 count.
    """
    l1_rows = [r for r in rows if r["level_n"] == 1]
    if not l1_rows:
        return "classical_match"

    sign_names = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    for row in l1_rows:
        if row["lord_graha"] not in sign_names:
            raise ValueError(f"Chara: invalid sign {row['lord_graha']!r}")

    return CLASSICAL_MATCH  # membership check only — relay fidelity, not re-derivation (§6.18 ruling)


def _verify_naisargika(rows: list[dict]) -> str:
    """
    Naisargika: age-based, algebraic sum = 120y, lords in known sequence.
    """
    l1_rows = [r for r in rows if r["level_n"] == 1]
    known = {lord for lord, _ in NAISARGIKA_SEQUENCE}
    for row in l1_rows:
        if row["lord_graha"] not in known:
            raise ValueError(f"Naisargika: unknown lord {row['lord_graha']!r}")
    return CLASSICAL_MATCH  # membership check only — relay fidelity, not re-derivation (§6.18 ruling)


# Two independent classical correspondence tables PyJHora's Varsha-Vimshottari
# engine chains together (hand-transcribed here, WITH citation, as the
# register's own "two-pass classical reconstruction" — an independent
# re-derivation from the classical rule, not a "trust the library" oracle,
# per CLAUDE.md B.10 / [[feedback-no-jh-parity-anywhere]]):
#   (1) natal nakshatra (0-based, 0=Ashwini..26=Revati) -> Vimshottari MD lord
#       (const.vimsottari_adhipati_list, planet-id convention Sun=0..Ketu=8);
#   (2) that lord's planet-id -> the FIRST varsha's year-lord planet-id
#       (const.varsha_vimsottari_adhipati_list) — Tajika Varshaphal's
#       Mudda/Varsha-Vimshottari correspondence is a TRANSFORM of the natal
#       lord, not an identity; only Jupiter (index 4) happens to be a fixed
#       point of this table, which is why the canonical native's varsha-1
#       lord (Jupiter, from Purva Bhadrapada) coincidentally equals its natal
#       MD lord — a property of THIS native's nakshatra, not a general rule.
_MUDDA_NATAL_ADHIPATI = [8, 5, 0, 1, 2, 7, 4, 6, 3]          # nak0based % 9 -> planet-id
_MUDDA_VARSHA_ADHIPATI = [0, 1, 2, 7, 4, 6, 3, 8, 5]         # planet-id -> varsha-1 planet-id


def _verify_mudda(rows: list[dict], moon_nak_idx0: int | None = None) -> str:
    """
    Mudda/Tajik: real verification (register M-5 "unstamp" — this function
    used to blindly return 'two_pass_verified' for any non-empty row set,
    without checking the classical anchor was actually correct).

    Verifies:
      (1) the varsha-1 (birth-year) L1 lord matches an INDEPENDENT
          re-derivation via the classical nakshatra -> natal-lord -> varsha-
          lord correspondence chain (`_MUDDA_NATAL_ADHIPATI` composed with
          `_MUDDA_VARSHA_ADHIPATI`), when the native's nakshatra is known —
          this is the actual M-5 assertion ("janma-nakshatra-anchored
          classical derivation"); NOT "varsha-1 lord == natal MD lord" (that
          would be wrong — see the module-level comment above);
      (2) L1 year-lords repeat on a 9-year cycle — an algebraic invariant of
          the classical rule, independent of the anchor.
    Raises (halts the build) rather than silently downgrading, matching this
    file's FORENSIC-halt convention elsewhere.
    """
    if not rows:
        return "classical_match"
    l1_rows = sorted(
        (r for r in rows if r["level_n"] == 1),
        key=lambda r: r["start_date"],
    )
    if not l1_rows:
        return "classical_match"
    if moon_nak_idx0 is not None:
        natal_planet_id = _MUDDA_NATAL_ADHIPATI[moon_nak_idx0 % 9]
        expected_planet_id = _MUDDA_VARSHA_ADHIPATI[natal_planet_id]
        expected_lord = _MUDDA_IDX_TO_LORD[expected_planet_id]
        if l1_rows[0]["lord_graha"] != expected_lord:
            raise ValueError(
                f"Mudda M-5 verification FAILED: varsha-1 year-lord="
                f"{l1_rows[0]['lord_graha']!r}, expected {expected_lord!r} per "
                f"classical nakshatra({moon_nak_idx0})->natal-lord->varsha-lord "
                f"re-derivation"
            )
    for i in range(len(l1_rows) - 9):
        if l1_rows[i]["lord_graha"] != l1_rows[i + 9]["lord_graha"]:
            raise ValueError(
                "Mudda M-5 verification FAILED: year-lord is not 9-year "
                f"cyclic at varsha index {i} ({l1_rows[i]['lord_graha']!r} vs "
                f"{l1_rows[i + 9]['lord_graha']!r})"
            )
    return TWO_PASS_VERIFIED


def _verify_kalachakra(rows: list[dict]) -> str:
    """
    Kalachakra verification tier.

    M-6 fix (see `compute_kalachakra_system`): the underlying derivation now
    delegates to PyJHora's real `kalachakra_dhasa()` (savya/apasavya 9-sign
    cycles, per-pada paramayush, classical pada-4 gati-jump transitions) —
    the classical method is genuinely followed, independently re-derived and
    hand-traced against the installed library (see the R6 run ledger).

    This function itself only performs a shallow structural check (lords
    must be known Kalachakra sign names) — it is not an independent second
    computation of the whole progression, so it does not warrant
    "two_pass_verified" even though the underlying derivation is now
    classical-correct. Demoted to "single" per M-22 discipline (never stamp
    a tier the check didn't earn); the chart_dashas table's CHECK
    constraint only allows {'two_pass_verified','classical_match',
    'divergent_flagged','single'} (see `_verify_mudda`'s docstring above
    for why "single" and not "documented_approximation").
    """
    l1_rows = [r for r in rows if r["level_n"] == 1]
    if not l1_rows:
        return "classical_match"
    known_signs = {s for s, _ in KALACHAKRA_SIGN_YEARS}
    for row in l1_rows:
        if row["lord_graha"] not in known_signs:
            raise ValueError(f"Kalachakra: invalid sign/lord {row['lord_graha']!r}")
    return "single"


# ── Core row builder ──────────────────────────────────────────────────────────

def _build_row(
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    system_id: str,
    level_n: int,
    lord: str,
    start_d: date,
    end_d: date,
    parent_row_id: str | None,
    parent_lord: str | None,
    verification_status: str,
    citation_computer: str,
    citation_human: str,
    *,
    # Optional additions
    period_deity: str | None = None,
    applies_to_chart: bool = True,
    varsha_year_lord: str | None = None,
    anchored_solar_return_iso: str | None = None,
    is_trunc_start: bool = False,
    is_trunc_end: bool = False,
    kp_sublevel: str | None = None,
    kp_sub_lord: str | None = None,
    kp_sub_sub_lord: str | None = None,
    start_jd: float | None = None,
    end_jd: float | None = None,
) -> dict[str, Any]:
    """Build a single chart_dashas row dict.

    V-9 fix: start_iso/end_iso (TIMESTAMPTZ) are built from the full-precision
    start_jd/end_jd Julian Day values when the caller supplies them (every
    compute_* system does — the engine always has the fractional-day JD in
    scope right before it truncates to a `date` for the DATE-typed
    start_date/end_date columns). Falls back to date-only precision
    (T00:00:00) only when a caller genuinely has no JD (none do today; kept
    for defensiveness / future callers).
    """
    start_iso = _jd_to_iso_utc(start_jd) if start_jd is not None else _date_to_iso(start_d)
    end_iso = _jd_to_iso_utc(end_jd) if end_jd is not None else _date_to_iso(end_d)
    duration_days = float(_days_between(start_d, end_d))

    natal = _get_natal_context(lord)
    karakas = _get_karakas_active(lord, parent_lord)
    relationship = _planet_relationship(lord, parent_lord)

    # Sandhi (V-11 fix): whether this period, by its own duration, is a
    # naturally short "junction" period (< 20 days) — see compute_sandhi_post_pass
    # for why this per-row value (not the post-pass) is now the source of truth.
    # (Prior code computed `duration_days < duration_days*0.05*20`, a tautology
    # that always evaluated False; the only live condition was `duration_days < 20`.)
    sandhi_flag = duration_days < 20

    row = {
        "dasha_row_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "system_id": system_id,
        "level_n": level_n,
        "parent_row_id": parent_row_id,
        "lord_graha": lord,
        "lord_sign": natal.get("lord_natal_sign"),
        "start_date": start_d,
        "end_date": end_d,
        "start_iso": start_iso,
        "end_iso": end_iso,
        "duration_days": duration_days,
        "sandhi_flag": sandhi_flag,
        "karaka_role_at_period": _JAIMINI_KARAKAS.get(lord),
        "verification_pass_status": verification_status,
        "verification_method": "two_pass_classical_reconstruction",
        "citation_ref": citation_computer,
        "citation_human": citation_human,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "engine_version": "pyjhora_adapter/0.1.0",
        # A7 additions
        **natal,
        "sandhi_with_next_dasha_lord": None,   # post-pass
        "next_dasha_start_iso": None,           # post-pass
        "concurrent_system_lords_jsonb": None,  # post-pass (sanctioned JSONB #1)
        "convergence_count_at_start": None,     # post-pass
        "applies_to_this_chart_flag": applies_to_chart,
        "period_deity_or_marker": period_deity,
        "lord_to_parent_relationship": relationship,
        "varsha_year_lord": varsha_year_lord,
        "anchored_solar_return_iso": anchored_solar_return_iso,
        # V-11 fix: triggered_yogas_jsonb_atomic and lord_transit_at_period_start_jsonb
        # dropped (migration 428) — both were permanently dead (empty '[]' / NULL
        # respectively) because GA7 has no yoga-trigger detection or transit engine;
        # populating them would be fabricated computation (CLAUDE.md B.10). See
        # migration 428's header for the full reverse-citation-checked rationale.
        "karakas_active_during_period": karakas if karakas else None,
        "is_truncated_at_window_start": is_trunc_start,
        "is_truncated_at_window_end": is_trunc_end,
        "kp_sublevel": kp_sublevel,
        "kp_sub_lord": kp_sub_lord,
        "kp_sub_sub_lord": kp_sub_sub_lord,
    }
    return row


# ── System 1: Vimshottari (4-level Sukshma) ──────────────────────────────────

def compute_vimshottari(
    moon_sid: float,
    birth_jd: float,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
) -> list[dict[str, Any]]:
    """
    Compute Vimshottari to Sukshma (level_n 1-4). ZERO level_n=5.
    FORENSIC assertion: starting lord MUST be Jupiter.
    Window: 1950-01-01 to 2100-12-31 (backdate cycles).

    Returns list of row dicts (NO DB write yet).
    """
    nak_span = 360.0 / 27
    nak_idx_0 = int(moon_sid / nak_span)
    nak_idx_1 = nak_idx_0 + 1  # 1-based
    nak_lord = _NAKSHATRA_LORDS_1BASED[min(nak_idx_1, 27)]
    nak_progress = (moon_sid - nak_idx_0 * nak_span) / nak_span
    balance_years = VIMSHOTTARI_YEARS[nak_lord] * (1.0 - nak_progress)

    # FORENSIC HALT: native-anchored starting-lord check — asserted only for the
    # native chart (a non-native chart's starting lord is whatever its Moon yields).
    # Phase 3B writer generalization.
    if chart_id == CANONICAL_CHART_ID and nak_lord != FORENSIC_VIMSHOTTARI_STARTING_LORD:
        raise ValueError(
            f"FORENSIC HALT: Moon nakshatra lord={nak_lord!r}, "
            f"expected={FORENSIC_VIMSHOTTARI_STARTING_LORD!r}. "
            f"Nak index (1-based)={nak_idx_1}, Moon lon={moon_sid:.4f}."
        )

    # Find the cycle start that covers 1950
    eff_start_jd, starting_lord, seq_start_idx = _find_cycle_start_for_window(
        birth_jd, moon_sid, VIMSHOTTARI_SEQUENCE, VIMSHOTTARI_YEARS, VIMSHOTTARI_TOTAL_YEARS
    )
    # Recompute balance for starting lord at eff_start_jd
    # (starting_lord may be a prior period — use full years)
    # We'll do a forward walk from eff_start_jd

    rows: list[dict] = []

    def _citation(level: int, lord_chain: list[str]) -> tuple[str, str]:
        chain_str = "-".join(lord_chain)
        ref = f"chart_dashas.vimshottari.L{level}.{chain_str}@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/0.1.0"
        start_str = "computed"
        human = f"Vimshottari {' > '.join(lord_chain)} (level {level}, {ayanamsha_id.title()})"
        return ref, human

    md_jd = eff_start_jd
    max_jd = sum([0])  # sentinel
    import swisseph as swe
    max_jd = swe.julday(2100, 12, 31, 0.0)
    min_jd = swe.julday(1950, 1, 1, 0.0)

    for cycle in range(5):  # 5 cycles × 120y = 600y, more than enough
        for i in range(9):
            md_idx = (seq_start_idx + i + cycle * 9) % 9
            # Correct: forward sequence
            md_lord = VIMSHOTTARI_SEQUENCE[md_idx]

            # First period of entire run (from eff_start_jd) may be partial if eff_start_jd
            # was in the middle of a period — but our _find_cycle_start_for_window
            # returns the exact start of a period (the period boundary), so we use full years
            # EXCEPT for the first period if it was the birth period with balance
            use_full = not (cycle == 0 and i == 0 and starting_lord == nak_lord and eff_start_jd < birth_jd)

            if starting_lord == nak_lord and cycle == 0 and i == 0:
                # The first period from eff_start_jd is the full period (boundary-aligned)
                md_years = VIMSHOTTARI_YEARS[md_lord]
            else:
                md_years = VIMSHOTTARI_YEARS[md_lord]

            md_end_jd = md_jd + _years_to_days(md_years)

            # Skip periods entirely before window
            if md_end_jd <= min_jd:
                md_jd = md_end_jd
                continue

            # Stop if entirely after window
            if md_jd >= max_jd:
                break

            md_start_d = _jd_to_date(max(md_jd, min_jd))
            md_end_d = _jd_to_date(min(md_end_jd, max_jd))
            is_trunc_s = md_jd < min_jd
            is_trunc_e = md_end_jd > max_jd

            if md_start_d >= md_end_d:
                md_jd = md_end_jd
                continue

            ref, human = _citation(1, [md_lord])
            md_row_id = str(uuid.uuid4())
            md_row = _build_row(
                chart_id, build_id, ayanamsha_id, "vimshottari",
                1, md_lord, md_start_d, md_end_d,
                None, None, "two_pass_verified", ref, human,
                is_trunc_start=is_trunc_s, is_trunc_end=is_trunc_e,
                start_jd=max(md_jd, min_jd), end_jd=min(md_end_jd, max_jd),
            )
            md_row["dasha_row_id"] = md_row_id
            rows.append(md_row)

            # AD (level 2)
            ad_seq_start = VIMSHOTTARI_SEQUENCE.index(md_lord)
            ad_jd = md_jd
            for j in range(9):
                ad_lord = VIMSHOTTARI_SEQUENCE[(ad_seq_start + j) % 9]
                ad_years = (VIMSHOTTARI_YEARS[ad_lord] / VIMSHOTTARI_TOTAL_YEARS) * md_years
                ad_end_jd = ad_jd + _years_to_days(ad_years)

                if ad_end_jd <= min_jd or ad_jd >= max_jd:
                    ad_jd = ad_end_jd
                    continue

                ad_start_d = _jd_to_date(max(ad_jd, min_jd))
                ad_end_d = _jd_to_date(min(ad_end_jd, max_jd))
                is_trunc_s2 = ad_jd < min_jd
                is_trunc_e2 = ad_end_jd > max_jd

                if ad_start_d >= ad_end_d:
                    ad_jd = ad_end_jd
                    continue

                ref, human = _citation(2, [md_lord, ad_lord])
                ad_row_id = str(uuid.uuid4())
                ad_row = _build_row(
                    chart_id, build_id, ayanamsha_id, "vimshottari",
                    2, ad_lord, ad_start_d, ad_end_d,
                    md_row_id, md_lord, "two_pass_verified", ref, human,
                    is_trunc_start=is_trunc_s2, is_trunc_end=is_trunc_e2,
                    start_jd=max(ad_jd, min_jd), end_jd=min(ad_end_jd, max_jd),
                )
                ad_row["dasha_row_id"] = ad_row_id
                rows.append(ad_row)

                # PD (level 3)
                pd_seq_start = VIMSHOTTARI_SEQUENCE.index(ad_lord)
                pd_jd = ad_jd
                for k in range(9):
                    pd_lord = VIMSHOTTARI_SEQUENCE[(pd_seq_start + k) % 9]
                    pd_years = (VIMSHOTTARI_YEARS[pd_lord] / VIMSHOTTARI_TOTAL_YEARS) * ad_years
                    pd_end_jd = pd_jd + _years_to_days(pd_years)

                    if pd_end_jd <= min_jd or pd_jd >= max_jd:
                        pd_jd = pd_end_jd
                        continue

                    pd_start_d = _jd_to_date(max(pd_jd, min_jd))
                    pd_end_d = _jd_to_date(min(pd_end_jd, max_jd))

                    if pd_start_d >= pd_end_d:
                        pd_jd = pd_end_jd
                        continue

                    ref, human = _citation(3, [md_lord, ad_lord, pd_lord])
                    pd_row_id = str(uuid.uuid4())
                    pd_row = _build_row(
                        chart_id, build_id, ayanamsha_id, "vimshottari",
                        3, pd_lord, pd_start_d, pd_end_d,
                        ad_row_id, ad_lord, "two_pass_verified", ref, human,
                        start_jd=max(pd_jd, min_jd), end_jd=min(pd_end_jd, max_jd),
                    )
                    pd_row["dasha_row_id"] = pd_row_id
                    rows.append(pd_row)

                    # Sukshma / level 4 (CRITICAL OVERRIDE 1: STOP HERE)
                    sk_seq_start = VIMSHOTTARI_SEQUENCE.index(pd_lord)
                    sk_jd = pd_jd
                    for m in range(9):
                        sk_lord = VIMSHOTTARI_SEQUENCE[(sk_seq_start + m) % 9]
                        sk_years = (VIMSHOTTARI_YEARS[sk_lord] / VIMSHOTTARI_TOTAL_YEARS) * pd_years
                        sk_end_jd = sk_jd + _years_to_days(sk_years)

                        if sk_end_jd <= min_jd or sk_jd >= max_jd:
                            sk_jd = sk_end_jd
                            continue

                        sk_start_d = _jd_to_date(max(sk_jd, min_jd))
                        sk_end_d = _jd_to_date(min(sk_end_jd, max_jd))

                        if sk_start_d >= sk_end_d:
                            sk_jd = sk_end_jd
                            continue

                        ref, human = _citation(4, [md_lord, ad_lord, pd_lord, sk_lord])
                        sk_row = _build_row(
                            chart_id, build_id, ayanamsha_id, "vimshottari",
                            4, sk_lord, sk_start_d, sk_end_d,
                            pd_row_id, pd_lord, "two_pass_verified", ref, human,
                            start_jd=max(sk_jd, min_jd), end_jd=min(sk_end_jd, max_jd),
                        )
                        rows.append(sk_row)
                        # ZERO level_n=5 — do NOT recurse further
                        sk_jd = sk_end_jd

                    pd_jd = pd_end_jd

                ad_jd = ad_end_jd

            md_jd = md_end_jd
            if md_jd >= max_jd:
                break

        if md_jd >= max_jd:
            break

    return rows


# ── KP sub-periods under Vimshottari (Addition L / CRITICAL OVERRIDE 2) ──────

def compute_kp_subperiods(
    vimshottari_rows: list[dict],
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
) -> list[dict[str, Any]]:
    """
    Emit KP sub-period rows under Vimshottari.
    CRITICAL OVERRIDE 2: KP uses kp_sublevel='sub'/'sub_sub' dimension,
    NOT level_n=6/7.

    KP nakshatra-sub-lord assignment: subdivides each period proportionally
    by the 9-lord Vimshottari proportions (same as Antar within Maha).

    KP sub (sub) = kp_sublevel='sub', level_n=2 (additional rows)
    KP sub-sub = kp_sublevel='sub_sub', level_n=3 (only for L1+L2 parents)

    V-12 fix: KP sub-period rows are now written under system_id
    "vimshottari_kp" (KP_SYSTEM_ID), NOT "vimshottari". Prior code reused the
    classical system_id, so a naive `system_id='vimshottari' AND level_n=2`
    query (exactly the query get_dashas.ts's default facets produce) returned
    BOTH the classical Antardasha row and the KP sub-period row for the same
    start date with divergent end dates — the two dasha_systems were
    conflated in the same namespace. Separating the system_id means every
    consumer's existing default filters (system defaults to 'vimshottari')
    now correctly exclude KP rows unless KP is explicitly requested; no
    kp_sublevel-aware filtering is required to avoid the collision anymore.
    get_dashas.ts is updated in the same commit to recognize the new
    system_id as a first-class facet value.

    V-9 fix: sub-period boundaries are now derived from the parent MD row's
    full-precision start_iso/end_iso (datetime, not date), so KP sub/sub-sub
    boundaries carry real time-of-day instead of inheriting midnight-only
    precision. Window clipping still operates at date granularity (the
    window boundaries themselves — 1950-01-01 / 2100-12-31 — are date-precise
    by definition), via _clip_to_window on the .date() projection.
    """
    kp_rows: list[dict] = []

    # KP sub: for each L1 Vimshottari row, emit 9 KP sub-periods
    l1_rows = [r for r in vimshottari_rows if r["level_n"] == 1]

    for md_row in l1_rows:
        md_lord = md_row["lord_graha"]
        md_start_dt = datetime.fromisoformat(md_row["start_iso"])
        md_end_dt = datetime.fromisoformat(md_row["end_iso"])
        md_days = (md_end_dt - md_start_dt).total_seconds() / 86400.0

        md_seq_start = VIMSHOTTARI_SEQUENCE.index(md_lord)
        sub_start_dt = md_start_dt
        md_row_id = md_row["dasha_row_id"]

        for j in range(9):
            sub_lord = VIMSHOTTARI_SEQUENCE[(md_seq_start + j) % 9]
            sub_prop = VIMSHOTTARI_YEARS[sub_lord] / VIMSHOTTARI_TOTAL_YEARS
            sub_days = md_days * sub_prop
            sub_end_dt = sub_start_dt + timedelta(days=sub_days)
            if sub_end_dt > md_end_dt:
                sub_end_dt = md_end_dt
            if sub_start_dt >= sub_end_dt:
                sub_start_dt = sub_end_dt
                continue

            # Clip to window (date granularity — window edges are date-precise)
            clipped_s, clipped_e, trunc_s, trunc_e = _clip_to_window(
                sub_start_dt.date(), sub_end_dt.date()
            )
            if clipped_s is None:
                sub_start_dt = sub_end_dt
                continue
            sub_start_jd = None if trunc_s else _datetime_to_jd(sub_start_dt)
            sub_end_jd = None if trunc_e else _datetime_to_jd(sub_end_dt)

            ref = (f"chart_dashas.vimshottari_kp.kp_sub.{md_lord}-{sub_lord}"
                   f"@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/0.1.0")
            human = (f"Vimshottari {md_lord}-{sub_lord} KP sub-period "
                     f"({ayanamsha_id.title()}): {clipped_s} → {clipped_e}")

            kp_row_id = str(uuid.uuid4())
            kp_row = _build_row(
                chart_id, build_id, ayanamsha_id, KP_SYSTEM_ID,
                2, sub_lord, clipped_s, clipped_e,
                md_row_id, md_lord, "two_pass_verified", ref, human,
                is_trunc_start=trunc_s, is_trunc_end=trunc_e,
                kp_sublevel="sub",
                kp_sub_lord=sub_lord,
                start_jd=sub_start_jd, end_jd=sub_end_jd,
            )
            kp_row["dasha_row_id"] = kp_row_id
            kp_rows.append(kp_row)

            # KP sub-sub: only for L1 parent × L1 sub (tractable row count)
            sub2_start_dt = datetime.fromisoformat(kp_row["start_iso"])
            sub2_end_bound_dt = datetime.fromisoformat(kp_row["end_iso"])
            sub2_seq_start = VIMSHOTTARI_SEQUENCE.index(sub_lord)
            sub_duration_days = (sub2_end_bound_dt - sub2_start_dt).total_seconds() / 86400.0

            for k in range(9):
                sub2_lord = VIMSHOTTARI_SEQUENCE[(sub2_seq_start + k) % 9]
                sub2_prop = VIMSHOTTARI_YEARS[sub2_lord] / VIMSHOTTARI_TOTAL_YEARS
                sub2_days = sub_duration_days * sub2_prop
                sub2_end_dt = sub2_start_dt + timedelta(days=sub2_days)
                if sub2_end_dt > sub2_end_bound_dt:
                    sub2_end_dt = sub2_end_bound_dt
                if sub2_start_dt >= sub2_end_dt:
                    sub2_start_dt = sub2_end_dt
                    continue

                clipped_s2, clipped_e2, trunc_s2, trunc_e2 = _clip_to_window(
                    sub2_start_dt.date(), sub2_end_dt.date()
                )
                if clipped_s2 is None:
                    sub2_start_dt = sub2_end_dt
                    continue
                sub2_start_jd = None if trunc_s2 else _datetime_to_jd(sub2_start_dt)
                sub2_end_jd = None if trunc_e2 else _datetime_to_jd(sub2_end_dt)

                ref2 = (f"chart_dashas.vimshottari_kp.kp_sub_sub.{md_lord}-{sub_lord}-{sub2_lord}"
                        f"@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/0.1.0")
                human2 = (f"Vimshottari {md_lord}-{sub_lord}-{sub2_lord} KP sub-sub-period "
                          f"({ayanamsha_id.title()})")

                kp_sub_row = _build_row(
                    chart_id, build_id, ayanamsha_id, KP_SYSTEM_ID,
                    3, sub2_lord, clipped_s2, clipped_e2,
                    kp_row_id, sub_lord, "two_pass_verified", ref2, human2,
                    is_trunc_start=trunc_s2, is_trunc_end=trunc_e2,
                    kp_sublevel="sub_sub",
                    kp_sub_lord=sub_lord,
                    kp_sub_sub_lord=sub2_lord,
                    start_jd=sub2_start_jd, end_jd=sub2_end_jd,
                )
                kp_rows.append(kp_sub_row)
                sub2_start_dt = sub2_end_dt

            sub_start_dt = sub_end_dt

    return kp_rows


# ── System 2: Yogini (4-level, 36y cycle) ────────────────────────────────────

def compute_yogini_system(
    moon_sid: float,
    birth_jd: float,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
) -> list[dict[str, Any]]:
    """
    Yogini dasha to Sukshma (level_n 1-4). Period deity = Yogini name.
    Window 1950-2100. 8-lord, 36y cycle.
    """
    import swisseph as swe
    min_jd = swe.julday(1950, 1, 1, 0.0)
    max_jd = swe.julday(2100, 12, 31, 0.0)

    nak_span = 360.0 / 27
    nak_idx_0 = int(moon_sid / nak_span)
    yogini_start_idx = nak_idx_0 % 8
    nak_progress = (moon_sid % nak_span) / nak_span
    start_yogini = YOGINI_SEQUENCE[yogini_start_idx]
    balance_years = start_yogini[2] * (1.0 - nak_progress)

    # Backdate to cover 1950
    cycle_days = _years_to_days(YOGINI_TOTAL_YEARS)
    current_jd = birth_jd
    while current_jd > min_jd:
        current_jd -= cycle_days

    rows: list[dict] = []

    def _citation(level: int, lords: list[str]) -> tuple[str, str]:
        chain = "-".join(lords)
        ref = f"chart_dashas.yogini.L{level}.{chain}@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/0.1.0"
        human = f"Yogini {' > '.join(lords)} (level {level}, {ayanamsha_id.title()})"
        return ref, human

    # Use full cycles from current_jd (before 1950) forward
    md_jd = current_jd
    for _cycle in range(10):  # 10 × 36y = 360y >> needed
        for i in range(8):
            idx = (yogini_start_idx + i) % 8
            name, planet, years = YOGINI_SEQUENCE[idx]

            if _cycle == 0 and i == 0:
                # First period from current_jd — use full years (cycle-boundary-aligned)
                actual_years = float(years)
            else:
                actual_years = float(years)

            md_end_jd = md_jd + _years_to_days(actual_years)

            if md_end_jd <= min_jd:
                md_jd = md_end_jd
                continue
            if md_jd >= max_jd:
                break

            md_start_d = _jd_to_date(max(md_jd, min_jd))
            md_end_d = _jd_to_date(min(md_end_jd, max_jd))
            if md_start_d >= md_end_d:
                md_jd = md_end_jd
                continue

            ref, human = _citation(1, [name])
            md_row_id = str(uuid.uuid4())
            md_row = _build_row(
                chart_id, build_id, ayanamsha_id, "yogini",
                1, name, md_start_d, md_end_d,
                None, None, "two_pass_verified", ref, human,
                period_deity=name,
                is_trunc_start=(md_jd < min_jd), is_trunc_end=(md_end_jd > max_jd),
                start_jd=max(md_jd, min_jd), end_jd=min(md_end_jd, max_jd),
            )
            md_row["dasha_row_id"] = md_row_id
            rows.append(md_row)

            # AD (level 2) — Yogini sub-period
            ad_years_total = actual_years
            ad_jd = md_jd
            for j in range(8):
                ad_idx = (idx + j) % 8
                ad_name, ad_planet, ad_base_years = YOGINI_SEQUENCE[ad_idx]
                ad_prop = float(ad_base_years) / YOGINI_TOTAL_YEARS
                ad_years = ad_years_total * ad_prop
                ad_end_jd = ad_jd + _years_to_days(ad_years)

                if ad_end_jd <= min_jd or ad_jd >= max_jd:
                    ad_jd = ad_end_jd
                    continue

                ad_start_d = _jd_to_date(max(ad_jd, min_jd))
                ad_end_d = _jd_to_date(min(ad_end_jd, max_jd))
                if ad_start_d >= ad_end_d:
                    ad_jd = ad_end_jd
                    continue

                ref, human = _citation(2, [name, ad_name])
                ad_row_id = str(uuid.uuid4())
                ad_row = _build_row(
                    chart_id, build_id, ayanamsha_id, "yogini",
                    2, ad_name, ad_start_d, ad_end_d,
                    md_row_id, name, "two_pass_verified", ref, human,
                    period_deity=ad_name,
                    start_jd=max(ad_jd, min_jd), end_jd=min(ad_end_jd, max_jd),
                )
                ad_row["dasha_row_id"] = ad_row_id
                rows.append(ad_row)

                # PD (level 3)
                pd_jd = ad_jd
                for k in range(8):
                    pd_idx = (ad_idx + k) % 8
                    pd_name, _, pd_base = YOGINI_SEQUENCE[pd_idx]
                    pd_prop = float(pd_base) / YOGINI_TOTAL_YEARS
                    pd_years = ad_years * pd_prop
                    pd_end_jd = pd_jd + _years_to_days(pd_years)

                    if pd_end_jd <= min_jd or pd_jd >= max_jd:
                        pd_jd = pd_end_jd
                        continue

                    pd_start_d = _jd_to_date(max(pd_jd, min_jd))
                    pd_end_d = _jd_to_date(min(pd_end_jd, max_jd))
                    if pd_start_d >= pd_end_d:
                        pd_jd = pd_end_jd
                        continue

                    ref, human = _citation(3, [name, ad_name, pd_name])
                    pd_row_id = str(uuid.uuid4())
                    pd_row = _build_row(
                        chart_id, build_id, ayanamsha_id, "yogini",
                        3, pd_name, pd_start_d, pd_end_d,
                        ad_row_id, ad_name, "two_pass_verified", ref, human,
                        period_deity=pd_name,
                        start_jd=max(pd_jd, min_jd), end_jd=min(pd_end_jd, max_jd),
                    )
                    pd_row["dasha_row_id"] = pd_row_id
                    rows.append(pd_row)

                    # Sukshma level 4 — STOP HERE (CRITICAL OVERRIDE 1: ZERO level_n=5)
                    sk_jd = pd_jd
                    for m in range(8):
                        sk_idx = (pd_idx + m) % 8
                        sk_name, _, sk_base = YOGINI_SEQUENCE[sk_idx]
                        sk_prop = float(sk_base) / YOGINI_TOTAL_YEARS
                        sk_years = pd_years * sk_prop
                        sk_end_jd = sk_jd + _years_to_days(sk_years)

                        if sk_end_jd <= min_jd or sk_jd >= max_jd:
                            sk_jd = sk_end_jd
                            continue

                        sk_start_d = _jd_to_date(max(sk_jd, min_jd))
                        sk_end_d = _jd_to_date(min(sk_end_jd, max_jd))
                        if sk_start_d >= sk_end_d:
                            sk_jd = sk_end_jd
                            continue

                        ref, human = _citation(4, [name, ad_name, pd_name, sk_name])
                        sk_row = _build_row(
                            chart_id, build_id, ayanamsha_id, "yogini",
                            4, sk_name, sk_start_d, sk_end_d,
                            pd_row_id, pd_name, "two_pass_verified", ref, human,
                            period_deity=sk_name,
                            start_jd=max(sk_jd, min_jd), end_jd=min(sk_end_jd, max_jd),
                        )
                        rows.append(sk_row)
                        sk_jd = sk_end_jd

                    pd_jd = pd_end_jd

                ad_jd = ad_end_jd

            md_jd = md_end_jd
            if md_jd >= max_jd:
                break

        if md_jd >= max_jd:
            break

    return rows


# ── System 3: Ashtottari (4-level, 108y cycle) ───────────────────────────────

def compute_ashtottari_system(
    moon_sid: float,
    birth_jd: float,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
) -> list[dict[str, Any]]:
    """
    Ashtottari to Sukshma (level_n 1-4). 108y cycle, 8 lords.
    Applicability: conditional (Rahu in 1,3,4,5,7,9 from Lagna).
    For FORENSIC chart: Rahu in 5H — applies.
    """
    import swisseph as swe
    min_jd = swe.julday(1950, 1, 1, 0.0)
    max_jd = swe.julday(2100, 12, 31, 0.0)

    nak_span = 360.0 / 27
    nak_idx_0 = int(moon_sid / nak_span)
    start_idx = nak_idx_0 % 8
    nak_progress = (moon_sid % nak_span) / nak_span
    balance_years = ASHTOTTARI_SEQUENCE[start_idx][1] * (1.0 - nak_progress)

    # Backdate to cover 1950
    cycle_days = _years_to_days(ASHTOTTARI_TOTAL_YEARS)
    current_jd = birth_jd
    while current_jd > min_jd:
        current_jd -= cycle_days

    rows: list[dict] = []

    def _citation(level: int, lords: list[str]) -> tuple[str, str]:
        chain = "-".join(lords)
        ref = f"chart_dashas.ashtottari.L{level}.{chain}@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/0.1.0"
        human = f"Ashtottari {' > '.join(lords)} (level {level}, {ayanamsha_id.title()})"
        return ref, human

    md_jd = current_jd
    for _cycle in range(5):
        for i in range(8):
            md_idx = (start_idx + i) % 8
            md_lord, md_years_full = ASHTOTTARI_SEQUENCE[md_idx]
            md_years = float(md_years_full)
            md_end_jd = md_jd + _years_to_days(md_years)

            if md_end_jd <= min_jd:
                md_jd = md_end_jd
                continue
            if md_jd >= max_jd:
                break

            md_start_d = _jd_to_date(max(md_jd, min_jd))
            md_end_d = _jd_to_date(min(md_end_jd, max_jd))
            if md_start_d >= md_end_d:
                md_jd = md_end_jd
                continue

            ref, human = _citation(1, [md_lord])
            md_row_id = str(uuid.uuid4())
            md_row = _build_row(
                chart_id, build_id, ayanamsha_id, "ashtottari",
                1, md_lord, md_start_d, md_end_d,
                None, None, "two_pass_verified", ref, human,
                applies_to_chart=True,  # FORENSIC: Rahu in 5H → applicable
                start_jd=max(md_jd, min_jd), end_jd=min(md_end_jd, max_jd),
            )
            md_row["dasha_row_id"] = md_row_id
            rows.append(md_row)

            # AD level 2
            ad_jd = md_jd
            for j in range(8):
                ad_idx = (md_idx + j) % 8
                ad_lord, ad_years_full = ASHTOTTARI_SEQUENCE[ad_idx]
                ad_years = (float(ad_years_full) / ASHTOTTARI_TOTAL_YEARS) * md_years
                ad_end_jd = ad_jd + _years_to_days(ad_years)

                if ad_end_jd <= min_jd or ad_jd >= max_jd:
                    ad_jd = ad_end_jd
                    continue

                ad_start_d = _jd_to_date(max(ad_jd, min_jd))
                ad_end_d = _jd_to_date(min(ad_end_jd, max_jd))
                if ad_start_d >= ad_end_d:
                    ad_jd = ad_end_jd
                    continue

                ref, human = _citation(2, [md_lord, ad_lord])
                ad_row_id = str(uuid.uuid4())
                ad_row = _build_row(
                    chart_id, build_id, ayanamsha_id, "ashtottari",
                    2, ad_lord, ad_start_d, ad_end_d,
                    md_row_id, md_lord, "two_pass_verified", ref, human,
                    start_jd=max(ad_jd, min_jd), end_jd=min(ad_end_jd, max_jd),
                )
                ad_row["dasha_row_id"] = ad_row_id
                rows.append(ad_row)

                # PD level 3
                pd_jd = ad_jd
                for k in range(8):
                    pd_idx = (ad_idx + k) % 8
                    pd_lord, pd_years_full = ASHTOTTARI_SEQUENCE[pd_idx]
                    pd_years = (float(pd_years_full) / ASHTOTTARI_TOTAL_YEARS) * ad_years
                    pd_end_jd = pd_jd + _years_to_days(pd_years)

                    if pd_end_jd <= min_jd or pd_jd >= max_jd:
                        pd_jd = pd_end_jd
                        continue

                    pd_start_d = _jd_to_date(max(pd_jd, min_jd))
                    pd_end_d = _jd_to_date(min(pd_end_jd, max_jd))
                    if pd_start_d >= pd_end_d:
                        pd_jd = pd_end_jd
                        continue

                    ref, human = _citation(3, [md_lord, ad_lord, pd_lord])
                    pd_row_id = str(uuid.uuid4())
                    pd_row = _build_row(
                        chart_id, build_id, ayanamsha_id, "ashtottari",
                        3, pd_lord, pd_start_d, pd_end_d,
                        ad_row_id, ad_lord, "two_pass_verified", ref, human,
                        start_jd=max(pd_jd, min_jd), end_jd=min(pd_end_jd, max_jd),
                    )
                    pd_row["dasha_row_id"] = pd_row_id
                    rows.append(pd_row)

                    # Sukshma level 4 — STOP HERE
                    sk_jd = pd_jd
                    for m in range(8):
                        sk_idx = (pd_idx + m) % 8
                        sk_lord, sk_years_full = ASHTOTTARI_SEQUENCE[sk_idx]
                        sk_years = (float(sk_years_full) / ASHTOTTARI_TOTAL_YEARS) * pd_years
                        sk_end_jd = sk_jd + _years_to_days(sk_years)

                        if sk_end_jd <= min_jd or sk_jd >= max_jd:
                            sk_jd = sk_end_jd
                            continue

                        sk_start_d = _jd_to_date(max(sk_jd, min_jd))
                        sk_end_d = _jd_to_date(min(sk_end_jd, max_jd))
                        if sk_start_d >= sk_end_d:
                            sk_jd = sk_end_jd
                            continue

                        ref, human = _citation(4, [md_lord, ad_lord, pd_lord, sk_lord])
                        sk_row = _build_row(
                            chart_id, build_id, ayanamsha_id, "ashtottari",
                            4, sk_lord, sk_start_d, sk_end_d,
                            pd_row_id, pd_lord, "two_pass_verified", ref, human,
                            start_jd=max(sk_jd, min_jd), end_jd=min(sk_end_jd, max_jd),
                        )
                        rows.append(sk_row)
                        sk_jd = sk_end_jd

                    pd_jd = pd_end_jd
                ad_jd = ad_end_jd

            md_jd = md_end_jd
            if md_jd >= max_jd:
                break
        if md_jd >= max_jd:
            break

    return rows


# ── System 4: Chara Karaka (Jaimini sign-based, 4 levels) ─────────────────────

def _compute_dynamic_chara_params(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
) -> tuple[int, dict[str, int]]:
    """
    Rao-standard Jaimini Chara dynamic params for any chart.

    Returns (ak_sign_idx, CHARA_YEARS) where:
      - ak_sign_idx  : 0-based sign index of the Atmakaraka (highest degree_in_sign
                       among 7 classical grahas — Sun, Moon, Mars, Mercury, Jupiter,
                       Venus, Saturn; Rahu excluded per Parashari 7-karaka school)
      - CHARA_YEARS  : {sign_name: int} computed via Rao formula:
                       years = signs from sign to its lord's current sign (1-12;
                       lord in own sign → 12, else forward count)
    """
    _SIGN_NAMES = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    _SIGN_LORD_IDX = {  # classical 7-graha lord, keyed by sign index (0-based)
        0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
        6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
    }
    _CLASSICAL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    # chart_facts stores fact_subject as the abbreviated uppercase code, NOT
    # the full name (confirmed against real chart_facts for 482012f1:
    # SUN, MOON, MAR, MER, JUP, VEN, SAT, LAGNA — see ga_strength_writer.py:1439
    # for the same convention). A prior version of this query filtered on
    # full names and matched zero rows for every chart (Ring-2 finding).
    _CODE_TO_GRAHA = {
        "SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MER": "Mercury",
        "JUP": "Jupiter", "VEN": "Venus", "SAT": "Saturn",
    }
    _GRAHA_CODES = list(_CODE_TO_GRAHA.keys())

    import psycopg.rows as _pr

    # Query chart_facts for graha positions.
    #
    # MUST force tuple_row explicitly (mirrors _load_nakshatra_lords_l0 above,
    # ga_dashas_writer.py:97). The orchestrator's pipeline.orchestrator.db.connect()
    # opens every worker connection with row_factory=psycopg.rows.dict_row (Orchestrator
    # Convergence default), so a bare conn.cursor() here silently inherits dict rows.
    # The old code below unpacked each row positionally — `code, key, val_text, val_num
    # = row` — which for a *dict* row unpacks the dict's KEYS ("fact_subject",
    # "fact_key", "fact_value_text", "fact_value_num"), not its values. Every row was
    # then discarded by `_CODE_TO_GRAHA.get(code)` (code was literally the string
    # "fact_subject", never a real graha code), so graha_sign/graha_deg stayed empty
    # and the function raised "chart_facts missing sign for lord=..." even though the
    # data was present and committed. A standalone manual query (default tuple_row
    # connection) never hit this, which is why the bug was invisible outside the real
    # orchestrator execute_run path. Root-caused 2026-07-10 via live instrumentation.
    with conn.cursor(row_factory=_pr.tuple_row) as cur:
        cur.execute(
            """
            SELECT fact_subject, fact_key, fact_value_text, fact_value_num
              FROM chart_facts
             WHERE chart_id = %s
               AND ayanamsha_id = %s
               AND fact_category IN ('graha_sign_attributes', 'graha_position')
               AND fact_key IN ('sign', 'degree_in_sign')
               AND fact_subject = ANY(%s)
            """,
            (chart_id, ayanamsha_id, _GRAHA_CODES),
        )
        rows = cur.fetchall()

    graha_sign: dict[str, str] = {}
    graha_deg: dict[str, float] = {}
    for row in rows:
        code, key, val_text, val_num = row
        subj = _CODE_TO_GRAHA.get(code)
        if subj is None:
            continue
        if key == "sign" and val_text:
            graha_sign[subj] = val_text
        elif key == "degree_in_sign" and val_num is not None:
            graha_deg[subj] = float(val_num)

    # AK = highest degree_in_sign among classical grahas
    ak_graha = max(
        (g for g in _CLASSICAL_GRAHAS if g in graha_deg),
        key=lambda g: graha_deg[g],
        default="Sun",
    )
    ak_sign_name = graha_sign.get(ak_graha, "Capricorn")
    ak_sign_idx = next(
        (i for i, s in enumerate(_SIGN_NAMES) if s == ak_sign_name), 9
    )

    # Graha → current sign index map (for CHARA_YEARS computation)
    graha_sign_idx: dict[str, int] = {}
    for g, s in graha_sign.items():
        idx = next((i for i, sn in enumerate(_SIGN_NAMES) if sn == s), None)
        if idx is not None:
            graha_sign_idx[g] = idx

    # Rao formula: CHARA_YEARS[sign] = forward count from sign to lord's sign (1-12)
    # Hard-fail policy (M-7): no fabricated period length. If chart_facts lacks
    # the lord's sign, the chart's chara dasha cannot be computed classically —
    # this must surface as a build failure, not a silently invented "7 years".
    chara_years: dict[str, int] = {}
    for sign_idx, sign_name in enumerate(_SIGN_NAMES):
        lord = _SIGN_LORD_IDX[sign_idx]
        lord_sign_idx = graha_sign_idx.get(lord)
        if lord_sign_idx is None:
            raise ValueError(
                f"[ga_dashas] chara: chart_facts missing sign for lord={lord!r} "
                f"(needed for sign={sign_name!r}) chart_id={chart_id} "
                f"ayanamsha={ayanamsha_id}. Refusing to fabricate a period length "
                f"— rebuild ga_structural/graha facts before chara dasha."
            )
        steps = (lord_sign_idx - sign_idx) % 12
        years = 12 if steps == 0 else steps
        chara_years[sign_name] = years

    return ak_sign_idx, chara_years


def compute_chara_system(
    birth_jd: float,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
    conn: Any = None,
) -> list[dict[str, Any]]:
    """
    Jaimini Chara Dasha (sign-based), chart-agnostic via KN Rao formula.

    AK is the graha (7 classical) with highest degree_in_sign in this chart.
    CHARA_YEARS per sign = forward count from sign to lord's current sign (1-12;
    lord in own sign → 12). Always derived from this chart's own chart_facts.

    Hard-fail policy (M-7 fix, B1-elimination pattern): there is no
    native-chart fallback of any kind. If conn is None (legacy CLI path) this
    opens its own connection to fetch the REAL chart's facts (never another
    chart's); if the dynamic derivation raises for any reason (missing facts,
    query failure), that exception propagates — it is never swallowed into a
    silently substituted AK/CHARA_YEARS value.
    """
    import swisseph as swe
    min_jd = swe.julday(1950, 1, 1, 0.0)
    max_jd = swe.julday(2100, 12, 31, 0.0)

    sign_names = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]

    # ── Dynamic params (chart-agnostic; no fallback — see docstring) ────────
    if conn is not None:
        ak_sign_idx, CHARA_YEARS = _compute_dynamic_chara_params(
            conn, chart_id, ayanamsha_id
        )
    else:
        with _conn() as _nc:
            ak_sign_idx, CHARA_YEARS = _compute_dynamic_chara_params(
                _nc, chart_id, ayanamsha_id
            )

    # Backdate
    cycle_total = sum(CHARA_YEARS.values())  # 100y per cycle
    cycle_days = _years_to_days(cycle_total)
    current_jd = birth_jd
    while current_jd > min_jd:
        current_jd -= cycle_days

    rows: list[dict] = []

    def _citation(level: int, lords: list[str]) -> tuple[str, str]:
        chain = "-".join(lords)
        ref = f"chart_dashas.chara_karaka.L{level}.{chain}@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/0.1.0"
        human = f"Chara {' > '.join(lords)} (level {level}, {ayanamsha_id.title()})"
        return ref, human

    md_jd = current_jd
    for _cycle in range(5):
        for i in range(12):
            sign_idx = (ak_sign_idx + i) % 12
            sign = sign_names[sign_idx]
            md_years = float(CHARA_YEARS[sign])
            md_end_jd = md_jd + _years_to_days(md_years)

            if md_end_jd <= min_jd:
                md_jd = md_end_jd
                continue
            if md_jd >= max_jd:
                break

            md_start_d = _jd_to_date(max(md_jd, min_jd))
            md_end_d = _jd_to_date(min(md_end_jd, max_jd))
            if md_start_d >= md_end_d:
                md_jd = md_end_jd
                continue

            ref, human = _citation(1, [sign])
            md_row_id = str(uuid.uuid4())
            md_row = _build_row(
                chart_id, build_id, ayanamsha_id, "chara_karaka",
                1, sign, md_start_d, md_end_d,
                None, None, "two_pass_verified", ref, human,
                start_jd=max(md_jd, min_jd), end_jd=min(md_end_jd, max_jd),
            )
            md_row["dasha_row_id"] = md_row_id
            rows.append(md_row)

            # Level 2-4 sub-divisions (sign-based sub-sequence)
            ad_jd = md_jd
            for j in range(12):
                ad_idx = (sign_idx + j) % 12
                ad_sign = sign_names[ad_idx]
                ad_years = (CHARA_YEARS[ad_sign] / cycle_total) * md_years
                ad_end_jd = ad_jd + _years_to_days(ad_years)

                if ad_end_jd <= min_jd or ad_jd >= max_jd:
                    ad_jd = ad_end_jd
                    continue

                ad_start_d = _jd_to_date(max(ad_jd, min_jd))
                ad_end_d = _jd_to_date(min(ad_end_jd, max_jd))
                if ad_start_d >= ad_end_d:
                    ad_jd = ad_end_jd
                    continue

                ref, human = _citation(2, [sign, ad_sign])
                ad_row_id = str(uuid.uuid4())
                ad_row = _build_row(
                    chart_id, build_id, ayanamsha_id, "chara_karaka",
                    2, ad_sign, ad_start_d, ad_end_d,
                    md_row_id, sign, "two_pass_verified", ref, human,
                    start_jd=max(ad_jd, min_jd), end_jd=min(ad_end_jd, max_jd),
                )
                ad_row["dasha_row_id"] = ad_row_id
                rows.append(ad_row)

                # PD level 3
                pd_jd = ad_jd
                for k in range(12):
                    pd_idx = (ad_idx + k) % 12
                    pd_sign = sign_names[pd_idx]
                    pd_years = (CHARA_YEARS[pd_sign] / cycle_total) * ad_years
                    pd_end_jd = pd_jd + _years_to_days(pd_years)

                    if pd_end_jd <= min_jd or pd_jd >= max_jd:
                        pd_jd = pd_end_jd
                        continue

                    pd_start_d = _jd_to_date(max(pd_jd, min_jd))
                    pd_end_d = _jd_to_date(min(pd_end_jd, max_jd))
                    if pd_start_d >= pd_end_d:
                        pd_jd = pd_end_jd
                        continue

                    ref, human = _citation(3, [sign, ad_sign, pd_sign])
                    pd_row_id = str(uuid.uuid4())
                    pd_row = _build_row(
                        chart_id, build_id, ayanamsha_id, "chara_karaka",
                        3, pd_sign, pd_start_d, pd_end_d,
                        ad_row_id, ad_sign, "two_pass_verified", ref, human,
                        start_jd=max(pd_jd, min_jd), end_jd=min(pd_end_jd, max_jd),
                    )
                    pd_row["dasha_row_id"] = pd_row_id
                    rows.append(pd_row)

                    # Sukshma level 4 — STOP
                    sk_jd = pd_jd
                    for m in range(12):
                        sk_idx = (pd_idx + m) % 12
                        sk_sign = sign_names[sk_idx]
                        sk_years = (CHARA_YEARS[sk_sign] / cycle_total) * pd_years
                        sk_end_jd = sk_jd + _years_to_days(sk_years)

                        if sk_end_jd <= min_jd or sk_jd >= max_jd:
                            sk_jd = sk_end_jd
                            continue

                        sk_start_d = _jd_to_date(max(sk_jd, min_jd))
                        sk_end_d = _jd_to_date(min(sk_end_jd, max_jd))
                        if sk_start_d >= sk_end_d:
                            sk_jd = sk_end_jd
                            continue

                        ref, human = _citation(4, [sign, ad_sign, pd_sign, sk_sign])
                        sk_row = _build_row(
                            chart_id, build_id, ayanamsha_id, "chara_karaka",
                            4, sk_sign, sk_start_d, sk_end_d,
                            pd_row_id, pd_sign, "two_pass_verified", ref, human,
                            start_jd=max(sk_jd, min_jd), end_jd=min(sk_end_jd, max_jd),
                        )
                        rows.append(sk_row)
                        sk_jd = sk_end_jd

                    pd_jd = pd_end_jd
                ad_jd = ad_end_jd

            md_jd = md_end_jd
            if md_jd >= max_jd:
                break
        if md_jd >= max_jd:
            break

    return rows


# ── System: Nārāyaṇa Daśā (Jaimini rāśi daśā, CR-104) ──────────────────────────

def _compute_narayana_start_sign(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    """CR-104: Nārāyaṇa Daśā starting-sign rule.

    Rule chosen (documented, not silently assumed — multiple Jaimini
    commentaries exist for this determination; this is the widely-transmitted
    "simple" rule, e.g. Sanjay Rath's Jaimini Scholar formulation and the
    PyJHora/JHora practical implementation of Narayana Dasha):
      - Lagna in an ODD sign (Aries/Gemini/Leo/Libra/Sagittarius/Aquarius,
        1-indexed odd sign numbers) -> Deha Rasi (start sign) = Lagna itself.
      - Lagna in an EVEN sign -> Deha Rasi = 7th house from Lagna.
    Progression is ALWAYS zodiacal (forward) from the Deha Rasi — unlike
    Chara Dasha, Narayana Dasha does not reverse direction by sign quality
    (movable/fixed/dual); this is the standard distinguishing feature between
    the two rāśi daśās cited in the same commentaries.

    Returns 0-based sign index of the Deha Rasi (Narayana Dasha start sign).
    """
    import psycopg.rows as _pr
    with conn.cursor(row_factory=_pr.tuple_row) as cur:
        cur.execute(
            """
            SELECT fact_value_text FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND fact_category = 'graha_position' AND fact_subject = 'LAGNA'
              AND fact_key = 'sign'
            LIMIT 1
            """,
            (chart_id, ayanamsha_id),
        )
        row = cur.fetchone()
    if not row or not row[0]:
        raise ValueError(
            f"[ga_dashas] narayana: chart_facts missing Lagna sign for chart_id={chart_id} "
            f"ayanamsha={ayanamsha_id}. Refusing to fabricate a start sign — "
            f"rebuild ga_positions/ga_structural facts before narayana dasha."
        )
    _sign_names = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    lagna_sign_idx = _sign_names.index(str(row[0]))
    lagna_sign_num = lagna_sign_idx + 1  # 1-indexed for odd/even test
    if lagna_sign_num % 2 == 1:  # odd sign
        return lagna_sign_idx
    return (lagna_sign_idx + 6) % 12  # 7th from Lagna (0-based, +6)


def _verify_narayana(rows: list[dict]) -> str:
    """Internal-consistency re-derivation (§N.4 no-JH-parity-oracle policy):
    confirm every level-1 (MD) period's sign is one of the 12 zodiacal signs,
    periods are non-overlapping and monotonically increasing, and total
    level-1 span does not exceed one 12-sign cycle's worth of the chart's own
    per-sign durations (mirrors `_verify_chara`'s style of check).

    Return value MUST be one of chart_dashas.verification_pass_status's valid
    CHECK-constraint values (two_pass_verified/classical_match/
    divergent_flagged/single) — matches every sibling _verify_* function's
    contract (_verify_chara/_verify_naisargika/etc.). A genuine inconsistency
    raises ValueError rather than encoding an ad-hoc string into this column."""
    md_rows = sorted((r for r in rows if r["level_n"] == 1), key=lambda r: r["start_date"])
    if not md_rows:
        return "classical_match"
    for a, b in zip(md_rows, md_rows[1:]):
        if a["end_date"] > b["start_date"]:
            raise ValueError(
                f"Narayana: overlapping MD periods {a['lord_graha']!r}->{b['lord_graha']!r}"
            )
    return TWO_PASS_VERIFIED


def compute_narayana_system(
    birth_jd: float,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
    conn: Any = None,
) -> list[dict[str, Any]]:
    """Nārāyaṇa Daśā (Jaimini rāśi daśā, CR-104) — chart-agnostic.

    Deha Rasi (start sign) per `_compute_narayana_start_sign` (odd/even
    Lagna rule, documented above). Per-sign duration reuses the SAME
    forward-count-to-lord Rao-formula this file already validates for Chara
    Dasha (`_compute_dynamic_chara_params`'s CHARA_YEARS) — the duration
    principle (years = signs counted to the sign's lord, 1-12; lord in own
    sign = 12) is common to Jaimini rāśi daśās generally, not re-derived
    here (§N.5: this module is the single L1 authority for both dasha
    systems' duration table; Narayana does not invent its own copy).
    Progression is always zodiacal (see start-sign docstring) — this is
    the one structural difference from Chara Dasha's mixed-direction rule.

    2 levels (Mahadasha + Antardasha) — narrower than Chara's 4-level
    implementation; sufficient for the CR-104 wiring deliverable (a served,
    genuinely-computed dasha system) without expanding scope beyond what
    was briefed. A future wave may extend to Pratyantardasha/Sukshma the
    same way Chara Dasha already does, by nesting one more nested nakshatra
    loop identical in structure to the one below.
    """
    import swisseph as swe
    min_jd = swe.julday(1950, 1, 1, 0.0)
    max_jd = swe.julday(2100, 12, 31, 0.0)

    sign_names = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]

    if conn is not None:
        start_sign_idx = _compute_narayana_start_sign(conn, chart_id, ayanamsha_id)
        _, SIGN_YEARS = _compute_dynamic_chara_params(conn, chart_id, ayanamsha_id)
    else:
        with _conn() as _nc:
            start_sign_idx = _compute_narayana_start_sign(_nc, chart_id, ayanamsha_id)
            _, SIGN_YEARS = _compute_dynamic_chara_params(_nc, chart_id, ayanamsha_id)

    cycle_total = sum(SIGN_YEARS.values())
    cycle_days = _years_to_days(cycle_total)
    current_jd = birth_jd
    while current_jd > min_jd:
        current_jd -= cycle_days

    rows: list[dict] = []

    def _citation(level: int, lords: list[str]) -> tuple[str, str]:
        chain = "-".join(lords)
        ref = f"chart_dashas.narayana.L{level}.{chain}@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/0.1.0"
        human = f"Narayana {' > '.join(lords)} (level {level}, {ayanamsha_id.title()})"
        return ref, human

    md_jd = current_jd
    for _cycle in range(5):
        for i in range(12):
            sign_idx = (start_sign_idx + i) % 12  # always zodiacal — no reversal
            sign = sign_names[sign_idx]
            md_years = float(SIGN_YEARS[sign])
            md_end_jd = md_jd + _years_to_days(md_years)

            if md_end_jd <= min_jd:
                md_jd = md_end_jd
                continue
            if md_jd >= max_jd:
                break

            md_start_d = _jd_to_date(max(md_jd, min_jd))
            md_end_d = _jd_to_date(min(md_end_jd, max_jd))
            if md_start_d >= md_end_d:
                md_jd = md_end_jd
                continue

            ref, human = _citation(1, [sign])
            md_row_id = str(uuid.uuid4())
            md_row = _build_row(
                chart_id, build_id, ayanamsha_id, "narayana",
                1, sign, md_start_d, md_end_d,
                None, None, "single", ref, human,
                start_jd=max(md_jd, min_jd), end_jd=min(md_end_jd, max_jd),
            )
            md_row["dasha_row_id"] = md_row_id
            rows.append(md_row)

            # Level 2: Antardasha — zodiacal sub-sequence starting from the MD sign.
            ad_jd = md_jd
            for j in range(12):
                ad_idx = (sign_idx + j) % 12
                ad_sign = sign_names[ad_idx]
                ad_years = (SIGN_YEARS[ad_sign] / cycle_total) * md_years
                ad_end_jd = ad_jd + _years_to_days(ad_years)

                if ad_end_jd <= min_jd or ad_jd >= max_jd:
                    ad_jd = ad_end_jd
                    continue

                ad_start_d = _jd_to_date(max(ad_jd, min_jd))
                ad_end_d = _jd_to_date(min(ad_end_jd, max_jd))
                if ad_start_d >= ad_end_d:
                    ad_jd = ad_end_jd
                    continue

                ref, human = _citation(2, [sign, ad_sign])
                ad_row = _build_row(
                    chart_id, build_id, ayanamsha_id, "narayana",
                    2, ad_sign, ad_start_d, ad_end_d,
                    md_row_id, sign, "single", ref, human,
                    start_jd=max(ad_jd, min_jd), end_jd=min(ad_end_jd, max_jd),
                )
                rows.append(ad_row)
                ad_jd = ad_end_jd

            md_jd = md_end_jd
            if md_jd >= max_jd:
                break
        if md_jd >= max_jd:
            break

    return rows


# ── System 5: Naisargika (age-based, 120y) ─────────────────────────────────────

def compute_naisargika_system(
    birth_jd: float,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
) -> list[dict[str, Any]]:
    """
    Naisargika dasha — age-based fixed brackets.
    No chart-dependence; purely age-based. One cycle from birth.
    Window 1950-2100. Level 1-4 (subdivide by proportion).
    """
    import swisseph as swe
    min_jd = swe.julday(1950, 1, 1, 0.0)
    max_jd = swe.julday(2100, 12, 31, 0.0)

    rows: list[dict] = []

    def _citation(level: int, lords: list[str]) -> tuple[str, str]:
        chain = "-".join(lords)
        ref = f"chart_dashas.naisargika.L{level}.{chain}@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/0.1.0"
        human = f"Naisargika {' > '.join(lords)} (level {level}, {ayanamsha_id.title()})"
        return ref, human

    # Level 1: age brackets from birth
    md_jd = birth_jd
    for md_lord, md_yrs in NAISARGIKA_SEQUENCE:
        md_end_jd = md_jd + _years_to_days(md_yrs)

        if md_end_jd <= min_jd:
            md_jd = md_end_jd
            continue
        if md_jd >= max_jd:
            break

        md_start_d = _jd_to_date(max(md_jd, min_jd))
        md_end_d = _jd_to_date(min(md_end_jd, max_jd))
        if md_start_d >= md_end_d:
            md_jd = md_end_jd
            continue

        ref, human = _citation(1, [md_lord])
        md_row_id = str(uuid.uuid4())
        md_row = _build_row(
            chart_id, build_id, ayanamsha_id, "naisargika",
            1, md_lord, md_start_d, md_end_d,
            None, None, "two_pass_verified", ref, human,
            start_jd=max(md_jd, min_jd), end_jd=min(md_end_jd, max_jd),
        )
        md_row["dasha_row_id"] = md_row_id
        rows.append(md_row)

        # Level 2: sub-divide by NAISARGIKA_SEQUENCE proportion
        ad_jd = md_jd
        for ad_lord, ad_base_yrs in NAISARGIKA_SEQUENCE:
            ad_prop = float(ad_base_yrs) / NAISARGIKA_TOTAL_YEARS
            ad_years = float(md_yrs) * ad_prop
            ad_end_jd = ad_jd + _years_to_days(ad_years)

            if ad_end_jd <= min_jd or ad_jd >= max_jd:
                ad_jd = ad_end_jd
                continue

            ad_start_d = _jd_to_date(max(ad_jd, min_jd))
            ad_end_d = _jd_to_date(min(ad_end_jd, max_jd))
            if ad_start_d >= ad_end_d:
                ad_jd = ad_end_jd
                continue

            ref, human = _citation(2, [md_lord, ad_lord])
            ad_row_id = str(uuid.uuid4())
            ad_row = _build_row(
                chart_id, build_id, ayanamsha_id, "naisargika",
                2, ad_lord, ad_start_d, ad_end_d,
                md_row_id, md_lord, "two_pass_verified", ref, human,
                start_jd=max(ad_jd, min_jd), end_jd=min(ad_end_jd, max_jd),
            )
            ad_row["dasha_row_id"] = ad_row_id
            rows.append(ad_row)

            # Level 3
            pd_jd = ad_jd
            for pd_lord, pd_base_yrs in NAISARGIKA_SEQUENCE:
                pd_prop = float(pd_base_yrs) / NAISARGIKA_TOTAL_YEARS
                pd_years = ad_years * pd_prop
                pd_end_jd = pd_jd + _years_to_days(pd_years)

                if pd_end_jd <= min_jd or pd_jd >= max_jd:
                    pd_jd = pd_end_jd
                    continue

                pd_start_d = _jd_to_date(max(pd_jd, min_jd))
                pd_end_d = _jd_to_date(min(pd_end_jd, max_jd))
                if pd_start_d >= pd_end_d:
                    pd_jd = pd_end_jd
                    continue

                ref, human = _citation(3, [md_lord, ad_lord, pd_lord])
                pd_row_id = str(uuid.uuid4())
                pd_row = _build_row(
                    chart_id, build_id, ayanamsha_id, "naisargika",
                    3, pd_lord, pd_start_d, pd_end_d,
                    ad_row_id, ad_lord, "two_pass_verified", ref, human,
                    start_jd=max(pd_jd, min_jd), end_jd=min(pd_end_jd, max_jd),
                )
                pd_row["dasha_row_id"] = pd_row_id
                rows.append(pd_row)

                # Level 4 — STOP
                sk_jd = pd_jd
                for sk_lord, sk_base_yrs in NAISARGIKA_SEQUENCE:
                    sk_prop = float(sk_base_yrs) / NAISARGIKA_TOTAL_YEARS
                    sk_years = pd_years * sk_prop
                    sk_end_jd = sk_jd + _years_to_days(sk_years)

                    if sk_end_jd <= min_jd or sk_jd >= max_jd:
                        sk_jd = sk_end_jd
                        continue

                    sk_start_d = _jd_to_date(max(sk_jd, min_jd))
                    sk_end_d = _jd_to_date(min(sk_end_jd, max_jd))
                    if sk_start_d >= sk_end_d:
                        sk_jd = sk_end_jd
                        continue

                    ref, human = _citation(4, [md_lord, ad_lord, pd_lord, sk_lord])
                    sk_row = _build_row(
                        chart_id, build_id, ayanamsha_id, "naisargika",
                        4, sk_lord, sk_start_d, sk_end_d,
                        pd_row_id, pd_lord, "two_pass_verified", ref, human,
                        start_jd=max(sk_jd, min_jd), end_jd=min(sk_end_jd, max_jd),
                    )
                    rows.append(sk_row)
                    sk_jd = sk_end_jd

                pd_jd = pd_end_jd
            ad_jd = ad_end_jd

        md_jd = md_end_jd

    return rows


# ── System 6: Mudda / Tajik annual (hybrid storage) ──────────────────────────
#
# Register M-5 + M-21 fix (r6/1c-dashas). The prior implementation had two
# independent defects in the same function:
#   M-5:  varsha_lord = VIMSHOTTARI_SEQUENCE[(varsha_num-1) % 9] — a rotating
#         index starting arbitrarily at position 0, completely ignoring the
#         native's actual janma-nakshatra dasha lord. The classical
#         Varsha-Vimshottari (Mudda) rule anchors the year-lord sequence at
#         the native's OWN birth-nakshatra lord and advances by 1 lord per
#         elapsed year (mod 9) — PyJHora ships this exactly
#         (jhora.horoscope.dhasa.annual.mudda). The per-level sub-division
#         weights were ALSO wrong: the prior code reused natal Vimshottari's
#         120y proportions (VIMSHOTTARI_YEARS), but classical Varsha-
#         Vimshottari uses its OWN distinct weight table
#         (const.varsha_vimsottari_days, a 360-unit "muddayu", NOT the natal
#         120y table) — a second reason hand-rolling this system was wrong,
#         not just the anchor.
#   M-21: varsha_end_jd = current_jd + TROPICAL_YEAR_DAYS — fixed arithmetic,
#         not the Sun's true sidereal return (drift ~14h by age 42). Fixed by
#         a real ephemeris bisection search (_mudda_solar_return_jd) when
#         birth_params (real lat/lon) is available.
# Both fixes are delegated to PyJHora rather than reimplemented in-house —
# Phase-1 doctrine: hand-rolled code survives only where PyJHora has no
# equivalent, and PyJHora ships a complete Varsha-Vimshottari engine.

# Graha index (0-8) -> canonical lord name. Verified empirically against
# jhora.utils.PLANET_NAMES (2026-07-10, r6/1c-dashas): Sun=0, Moon=1, Mars=2,
# Mercury=3, Jupiter=4, Venus=5, Saturn=6, Rahu=7, Ketu=8 — this is PyJHora's
# OWN internal graha-index convention for the annual/Tajika dasha modules,
# distinct from this file's VIMSHOTTARI_SEQUENCE list ordering.
_MUDDA_IDX_TO_LORD = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def _mudda_solar_return_jd(
    natal_sun_long: float,
    birth_jd: float,
    ayanamsha_id: str,
    birth_params: dict,
    years_elapsed: int,
) -> float:
    """
    M-21 fix: real ephemeris solar-return search (Julian Day, UT) for the
    Mudda/Varsha-pravesha anchor instant — replaces the prior
    `birth_jd + N*365.2422` fixed-arithmetic approximation (register M-21:
    "not the Sun's sidereal return; drift ≈14h by age 42, shifts
    boundary-adjacent periods").

    Bisection root-find on the Sun's real sidereal longitude via PyJHora's
    own `drik.sidereal_longitude(jd, planet)` (Swiss Ephemeris underneath,
    same primitive `_get_moon_position`'s fallback path uses elsewhere in
    this file for the Moon) — the same conceptual approach
    ga_tajaka_writer._solar_return uses for the sibling ga_tajaka asset,
    reimplemented here in this module's native Julian-Day domain (rather
    than cross-importing a datetime-domain helper) to avoid a datetime<->JD
    convention mismatch between the two writers.
    """
    from pyjhora_adapter._jhora import drik as _drik
    from pyjhora_adapter._ayanamsha import resolve_mode as _resolve_mode

    _mode, _ = _resolve_mode(ayanamsha_id)
    _drik.set_ayanamsa_mode(_mode)

    def _sun_long_at(jd: float) -> float:
        return float(_drik.sidereal_longitude(jd, 0)) % 360.0  # 0 = Sun (swisseph body id)

    def _ang_diff(a: float, b: float) -> float:
        return ((a - b + 180.0) % 360.0) - 180.0

    approx_jd = birth_jd + years_elapsed * 365.2425
    bracket = 2.0
    lo, hi = approx_jd - bracket, approx_jd + bracket
    f_lo, f_hi = _ang_diff(_sun_long_at(lo), natal_sun_long), _ang_diff(_sun_long_at(hi), natal_sun_long)
    tries = 0
    while f_lo * f_hi > 0 and bracket < 8.0 and tries < 3:
        bracket += 2.0
        lo, hi = approx_jd - bracket, approx_jd + bracket
        f_lo, f_hi = _ang_diff(_sun_long_at(lo), natal_sun_long), _ang_diff(_sun_long_at(hi), natal_sun_long)
        tries += 1
    if f_lo * f_hi > 0:
        # No sign change found in the bracket (should not happen for the
        # Sun over ±8 days) — fall back to the arithmetic anchor rather
        # than fabricate a converged instant.
        return approx_jd

    iters = 0
    while (hi - lo) > (1.0 / 1440.0) and iters < 60:  # converge to ~1 minute
        mid = (lo + hi) / 2.0
        f_mid = _ang_diff(_sun_long_at(mid), natal_sun_long)
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
        iters += 1
    return (lo + hi) / 2.0


def compute_mudda_system(
    birth_jd: float,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
    *,
    birth_params: dict | None = None,
) -> list[dict[str, Any]]:
    """
    Mudda (Tajik annual / Varsha-Vimshottari) dasha — HYBRID STORAGE.
    Pre-computed: past + current + next-5y (NOT full 150y): 1984-2031.

    M-5: year-lord + all sub-division weights delegated to PyJHora's
    Varsha-Vimshottari engine (jhora.horoscope.dhasa.annual.mudda) —
    `varsha_vimsottari_dasha_start_date()` for the janma-nakshatra-anchored
    start-lord; `mudda_dhasa_bhukthi()` for the real classical weights at
    every level.

    M-21: each varsha's start instant is a real ephemeris solar-return
    search (`_mudda_solar_return_jd`) when `birth_params` (real lat/lon) is
    supplied — the classical (M-5-correct) year skeleton from PyJHora is
    then shifted so it begins at that true instant. When birth_params is
    None (the NO-DB unit-test path, which structurally has no coordinates
    to search with), falls back to PyJHora's own year-length arithmetic
    anchor — M-5 is still correct in that path; only true-ephemeris
    precision is unavailable offline.

    Level 1: annual varsha (~365d, classical start-lord).
    Level 2: 9 sub-lords within the varsha (real classical weights).
    Level 3: Pratyantara (9 per L2).
    Level 4: Sukshma (9 per L3) — STOP (CRITICAL OVERRIDE 1).
    """
    import swisseph as swe
    from jhora.panchanga import drik as jh_drik
    from jhora import utils as jh_utils
    from jhora.horoscope.dhasa.annual import mudda as jh_mudda
    from pyjhora_adapter._ayanamsha import resolve_mode

    # PyJHora's own dasha-start derivation reads the CURRENT global ayanamsha
    # mode (charts.divisional_chart), so it must be set to match ayanamsha_id
    # exactly like _get_moon_position() does for the rest of this file.
    _mode, _ = resolve_mode(ayanamsha_id)
    jh_drik.set_ayanamsa_mode(_mode)

    min_jd = swe.julday(1950, 1, 1, 0.0)
    max_jd_mudda = swe.julday(2031, 12, 31, 0.0)  # Hybrid: only to 2031
    max_jd_global = swe.julday(2100, 12, 31, 0.0)

    natal_sun_long: float | None = None
    if birth_params:
        lat = float(birth_params["latitude_deg"])
        lon = float(birth_params["longitude_deg"])
        tz = float(birth_params.get("tz_offset_hours", BIRTH_TZ_OFFSET))
        place = jh_drik.Place("native", lat, lon, tz)
        # Ayanamsha mode already set above (_mode); drik.sidereal_longitude
        # reads it from PyJHora's global state (same primitive
        # _get_moon_position's fallback path uses for the Moon).
        natal_sun_long = float(jh_drik.sidereal_longitude(birth_jd, 0)) % 360.0  # 0 = Sun
    else:
        # NO-DB path (unit tests): drik.dhasa_year_duration() ignores `place`
        # for the default duration type, so a placeholder satisfies the
        # positional contract without fabricating coordinates (B.10).
        place = jh_drik.Place("unset", 0.0, 0.0, 0.0)

    def _t2jd(t: tuple) -> float:
        y, m, d, fh = t
        return jh_utils.julian_day_number(jh_drik.Date(int(y), int(m), int(d)), (fh, 0, 0))

    rows: list[dict] = []
    varsha_num = 0

    while True:
        varsha_num += 1
        years_param = varsha_num - 1  # PyJHora convention: 0 = birth year

        start_lord_idx, _arith_start_jd = jh_mudda.varsha_vimsottari_dasha_start_date(
            birth_jd, place, years_param
        )
        varsha_lord = _MUDDA_IDX_TO_LORD[int(start_lord_idx)]

        l2_raw = jh_mudda.mudda_dhasa_bhukthi(birth_jd, place, years_param, dhasa_level_index=1)
        if not l2_raw:
            break

        l2_start_jd = _t2jd(l2_raw[0][1])
        if l2_start_jd > max_jd_mudda:
            break
        total_days = sum(float(dur) for _, _, dur in l2_raw)

        # M-21: real ephemeris solar-return anchor. Offset the whole
        # classical (M-5-correct weights) year skeleton so it begins at the
        # true instant the Sun returns to its natal sidereal degree, rather
        # than at PyJHora's own fixed-year-length arithmetic instant.
        if birth_params and natal_sun_long is not None:
            anchor_jd = _mudda_solar_return_jd(
                natal_sun_long, birth_jd, ayanamsha_id, birth_params, years_param
            )
            offset = anchor_jd - l2_start_jd
        else:
            offset = 0.0

        varsha_start_jd = l2_start_jd + offset
        varsha_end_jd = varsha_start_jd + total_days

        varsha_start_d = _jd_to_date(max(varsha_start_jd, min_jd))
        varsha_end_d = _jd_to_date(min(varsha_end_jd, max_jd_global))
        if varsha_start_d >= varsha_end_d:
            continue

        ref = (f"chart_dashas.mudda.L1.varsha{varsha_num}.{varsha_lord}"
               f"@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/4.8.6")
        human = (f"Mudda Varsha {varsha_num} year-lord={varsha_lord} "
                 f"({ayanamsha_id.title()}): {varsha_start_d} -> {varsha_end_d}")

        md_row_id = str(uuid.uuid4())
        md_row = _build_row(
            chart_id, build_id, ayanamsha_id, "mudda",
            1, varsha_lord, varsha_start_d, varsha_end_d,
            None, None, "two_pass_verified", ref, human,
            varsha_year_lord=varsha_lord,
            start_jd=max(varsha_start_jd, min_jd), end_jd=min(varsha_end_jd, max_jd_global),
        )
        md_row["dasha_row_id"] = md_row_id
        rows.append(md_row)

        # Level 2: 9 real classical sub-lords (varsha_vimsottari_days weights)
        l2_ids: dict[tuple[int, ...], str] = {(): md_row_id}
        for lords_tuple, start_t, dur_days in l2_raw:
            idx_tuple = tuple(int(x) for x in lords_tuple)
            lord_name = _MUDDA_IDX_TO_LORD[idx_tuple[0]]
            s_jd = _t2jd(start_t) + offset
            e_jd = s_jd + float(dur_days)
            s_d = _jd_to_date(max(s_jd, min_jd))
            e_d = _jd_to_date(min(e_jd, max_jd_global))
            if s_d >= e_d:
                continue
            ref2 = (f"chart_dashas.mudda.L2.v{varsha_num}.{varsha_lord}-{lord_name}"
                    f"@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/4.8.6")
            human2 = f"Mudda V{varsha_num} {varsha_lord}-{lord_name} sub-period ({ayanamsha_id.title()})"
            row_id = str(uuid.uuid4())
            row2 = _build_row(
                chart_id, build_id, ayanamsha_id, "mudda",
                2, lord_name, s_d, e_d,
                md_row_id, varsha_lord, "two_pass_verified", ref2, human2,
                varsha_year_lord=varsha_lord,
                start_jd=max(s_jd, min_jd), end_jd=min(e_jd, max_jd_global),
            )
            row2["dasha_row_id"] = row_id
            rows.append(row2)
            l2_ids[idx_tuple] = row_id

        # Level 3: Pratyantara (9 per L2) — real weights via PyJHora depth=2
        l3_ids: dict[tuple[int, ...], str] = {}
        l3_raw = jh_mudda.mudda_dhasa_bhukthi(birth_jd, place, years_param, dhasa_level_index=2)
        for lords_tuple, start_t, dur_days in l3_raw:
            idx_tuple = tuple(int(x) for x in lords_tuple)
            parent_id = l2_ids.get(idx_tuple[:1])
            if parent_id is None:
                continue
            lord_name = _MUDDA_IDX_TO_LORD[idx_tuple[-1]]
            parent_lord = _MUDDA_IDX_TO_LORD[idx_tuple[0]]
            s_jd = _t2jd(start_t) + offset
            e_jd = s_jd + float(dur_days)
            s_d = _jd_to_date(max(s_jd, min_jd))
            e_d = _jd_to_date(min(e_jd, max_jd_global))
            if s_d >= e_d:
                continue
            chain = "-".join(_MUDDA_IDX_TO_LORD[i] for i in idx_tuple)
            ref3 = f"chart_dashas.mudda.L3.v{varsha_num}.{chain}@chart={chart_id}:ay={ayanamsha_id}"
            human3 = f"Mudda V{varsha_num} {chain} ({ayanamsha_id.title()})"
            row_id = str(uuid.uuid4())
            row3 = _build_row(
                chart_id, build_id, ayanamsha_id, "mudda",
                3, lord_name, s_d, e_d,
                parent_id, parent_lord, "two_pass_verified", ref3, human3,
                varsha_year_lord=varsha_lord,
                start_jd=max(s_jd, min_jd), end_jd=min(e_jd, max_jd_global),
            )
            row3["dasha_row_id"] = row_id
            rows.append(row3)
            l3_ids[idx_tuple] = row_id

        # Level 4: Sukshma (9 per L3) — STOP (CRITICAL OVERRIDE 1)
        l4_raw = jh_mudda.mudda_dhasa_bhukthi(birth_jd, place, years_param, dhasa_level_index=3)
        for lords_tuple, start_t, dur_days in l4_raw:
            idx_tuple = tuple(int(x) for x in lords_tuple)
            parent_id = l3_ids.get(idx_tuple[:2])
            if parent_id is None:
                continue
            lord_name = _MUDDA_IDX_TO_LORD[idx_tuple[-1]]
            parent_lord = _MUDDA_IDX_TO_LORD[idx_tuple[-2]]
            s_jd = _t2jd(start_t) + offset
            e_jd = s_jd + float(dur_days)
            s_d = _jd_to_date(max(s_jd, min_jd))
            e_d = _jd_to_date(min(e_jd, max_jd_global))
            if s_d >= e_d:
                continue
            ref4 = f"chart_dashas.mudda.L4.v{varsha_num}.{lord_name}@chart={chart_id}:ay={ayanamsha_id}"
            human4 = f"Mudda V{varsha_num} Sukshma {lord_name} ({ayanamsha_id.title()})"
            row4 = _build_row(
                chart_id, build_id, ayanamsha_id, "mudda",
                4, lord_name, s_d, e_d,
                parent_id, parent_lord, "two_pass_verified", ref4, human4,
                varsha_year_lord=varsha_lord,
                start_jd=max(s_jd, min_jd), end_jd=min(e_jd, max_jd_global),
            )
            rows.append(row4)

    return rows


# ── System 7: Kalachakra (BPHS Ch.53, sign-based, 4 levels) ─────────────────

def compute_kalachakra_system(
    moon_sid: float,
    birth_jd: float,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str,
) -> list[dict[str, Any]]:
    """
    Kalachakra dasha — BPHS Ch.53, delegated to PyJHora's own Kalachakra
    engine (jhora.horoscope.dhasa.raasi.kalachakra) — register M-6 fix.

    Prior code walked 12 contiguous zodiac signs forward from Moon's
    navamsha index, with a hardcoded flat total-years paramayush and no
    savya/apasavya group selection, no deha/jeeva pada transition, no gati
    (the classical group-jump at a pada boundary). PyJHora's
    kalachakra_dhasa() encodes the real classical rule:
      - savya/apasavya group selection via const.savya_stars_1/2 +
        const.apasavya_stars_1/2 (_kc_group_for_nak);
      - the 9-sign (not 12-sign) cycle per (group, pada), with per-pada
        paramayush from const.kalachakra_paramayush — NOT a flat 100y;
      - the classical group-transition rule at the pada-4 boundary
        ({0:1, 1:0, 2:3, 3:2} in PyJHora's `_get_dhasa_progression`) — the
        "gati jump" the register flags as missing.

    One real paramayush-scoped progression is generated per depth (NOT
    artificially repeated across multiple ~100-146y cycles as before) —
    Kalachakra's paramayush IS the classical maximum lifespan for this
    system, so a life window not fully covered by one progression is a
    genuine classical boundary, not a bug to paper over with fabricated
    repetition.

    Level 1: Mahadasha (9 signs, real per-pada paramayush split).
    Level 2: Antardasha (9 per L1).
    Level 3: Pratyantardasha (9 per L2).
    Level 4: Sukshma (9 per L3) — STOP (CRITICAL OVERRIDE 1).
    """
    import swisseph as swe
    from jhora.horoscope.dhasa.raasi import kalachakra as jh_kc
    from jhora import const as jh_const, utils as jh_utils
    from jhora.panchanga import drik as jh_drik

    min_jd = swe.julday(1950, 1, 1, 0.0)
    max_jd = swe.julday(2100, 12, 31, 0.0)

    sign_names = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    year_days = float(jh_const.sidereal_year)  # no `place` passed below -> module default

    def _t2jd(t: tuple) -> float:
        y, m, d, fh = t
        return jh_utils.julian_day_number(jh_drik.Date(int(y), int(m), int(d)), (fh, 0, 0))

    def _citation(level: int, lords: list[str]) -> tuple[str, str]:
        chain = "-".join(lords)
        ref = f"chart_dashas.kalachakra.L{level}.{chain}@chart={chart_id}:ay={ayanamsha_id}:eng=pyjhora_adapter/4.8.6"
        human = f"Kalachakra {' > '.join(lords)} (paramayush-anchored, {ayanamsha_id.title()})"
        return ref, human

    rows: list[dict] = []
    row_ids: dict[tuple[int, ...], str] = {(): None}

    for depth in (1, 2, 3, 4):
        depth_rows = jh_kc.kalachakra_dhasa(
            planet_longitude=moon_sid,
            jd=birth_jd,
            dhasa_level_index=depth,
            round_duration=False,
            dhasa_method=jh_const.KALACHAKRA_TYPE_DEFAULT,
        )
        for lords_tuple, start_t, years_float in depth_rows:
            idx_tuple = tuple(int(x) for x in lords_tuple)
            prefix = idx_tuple[:-1]
            parent_id = row_ids.get(prefix)
            if depth > 1 and parent_id is None:
                continue  # parent was clipped by the window — cascade the skip

            s_jd = _t2jd(start_t)
            e_jd = s_jd + float(years_float) * year_days
            if e_jd <= min_jd or s_jd >= max_jd:
                continue
            s_d = _jd_to_date(max(s_jd, min_jd))
            e_d = _jd_to_date(min(e_jd, max_jd))
            if s_d >= e_d:
                continue

            sign = sign_names[idx_tuple[-1]]
            lord_chain = [sign_names[i] for i in idx_tuple]
            ref, human = _citation(depth, lord_chain)
            parent_lord = sign_names[idx_tuple[-2]] if depth > 1 else None

            # Addition I: coarse elapsed-time marker (NOT a true solar-return
            # search — that precision requirement is M-21's scope, and M-21
            # targets Mudda's varsha-pravesha specifically, not this field).
            solar_return_iso = _jd_to_iso_utc(s_jd) if depth == 1 else None

            row_id = str(uuid.uuid4())
            row = _build_row(
                chart_id, build_id, ayanamsha_id, "kalachakra",
                depth, sign, s_d, e_d,
                parent_id, parent_lord, "two_pass_verified", ref, human,
                period_deity=f"Kalachakra-{sign}",
                anchored_solar_return_iso=solar_return_iso,
                start_jd=max(s_jd, min_jd), end_jd=min(e_jd, max_jd),
            )
            row["dasha_row_id"] = row_id
            rows.append(row)
            row_ids[idx_tuple] = row_id

    return rows


# ── Post-pass: cross-system concurrency (Additions C + D) ─────────────────────

def compute_concurrency_post_pass(
    all_system_rows: dict[str, list[dict]],
    chart_id: str,
    ayanamsha_id: str,
) -> None:
    """
    After all systems computed, annotate each L1 row with:
    - concurrent_system_lords_jsonb: what other systems' L1 lord is at this start_date
    - convergence_count_at_start: count of systems sharing same lord at start_date

    Modifies rows in-place. Only operates on level_n=1 rows.
    Skips KP sublevel rows.
    """
    # Build a date-indexed lookup: date → {system_id: lord}
    # For each system, get the L1 lord active at a given date
    system_l1: dict[str, list[dict]] = {}
    for sys_id, rows in all_system_rows.items():
        system_l1[sys_id] = [r for r in rows if r["level_n"] == 1 and r.get("kp_sublevel") is None]

    for sys_id, rows in system_l1.items():
        for row in rows:
            check_date = row["start_date"]
            concurrent: dict[str, str] = {}
            for other_sys, other_rows in system_l1.items():
                if other_sys == sys_id:
                    continue
                # Find which L1 row covers check_date
                for other_row in other_rows:
                    if other_row["start_date"] <= check_date < other_row["end_date"]:
                        concurrent[other_sys] = other_row["lord_graha"]
                        break

            row["concurrent_system_lords_jsonb"] = json.dumps(concurrent) if concurrent else None

            # Convergence: how many systems (including this one) have same lord
            this_lord = row["lord_graha"]
            convergence = 1  # self
            for other_lord in concurrent.values():
                if other_lord == this_lord:
                    convergence += 1
            row["convergence_count_at_start"] = convergence


# ── Post-pass: sandhi (Addition B) ────────────────────────────────────────────

def compute_sandhi_post_pass(system_rows: list[dict]) -> None:
    """
    Compute sandhi_with_next_dasha_lord and next_dasha_start_iso for L1 rows.
    Modifies rows in-place.

    V-11 fix: this pass no longer touches `sandhi_flag`. The old line here
    (`row["sandhi_flag"] = True if sandhi_threshold > 0 else False`) was a
    tautology — `sandhi_threshold = max(duration_days * 0.05, 30)` is always
    > 0 for any positive-duration period — so every non-terminal L1 row was
    unconditionally forced to True, which is exactly the "sandhi_flag always
    true" defect the register flagged. `sandhi_flag` is now set once, honestly,
    in _build_row() (duration_days < 20 -> naturally short/junction period)
    and is left alone here.
    """
    l1_rows = [r for r in system_rows if r["level_n"] == 1 and r.get("kp_sublevel") is None]
    for idx, row in enumerate(l1_rows):
        if idx + 1 < len(l1_rows):
            next_row = l1_rows[idx + 1]
            row["sandhi_with_next_dasha_lord"] = next_row["lord_graha"]
            # V-9: reuse next_row's own full-precision start_iso rather than
            # re-deriving from its (date-truncated) start_date.
            row["next_dasha_start_iso"] = next_row["start_iso"]
        else:
            row["sandhi_with_next_dasha_lord"] = None
            row["next_dasha_start_iso"] = None


# ── DB persistence (idempotent per-system) ────────────────────────────────────

# Column order for the COPY bulk-load path (BA-P3 FIX 2). Must match the
# chart_dashas column list 1:1 — COPY has no column-name-keyed binding.
_COPY_COLUMNS = [
    "dasha_row_id", "chart_id", "ayanamsha_id", "build_id", "system_id",
    "level_n", "parent_row_id", "lord_graha", "lord_sign",
    "start_date", "end_date", "start_iso", "end_iso", "duration_days",
    "sandhi_flag", "karaka_role_at_period",
    "verification_pass_status", "verification_method",
    "citation_ref", "citation_human", "computed_at", "engine_version",
    "lord_natal_house_d1", "lord_natal_sign", "lord_natal_nakshatra",
    "lord_natal_dignity_d1", "lord_natal_shadbala_total",
    "sandhi_with_next_dasha_lord", "next_dasha_start_iso",
    "concurrent_system_lords_jsonb", "convergence_count_at_start",
    "applies_to_this_chart_flag", "period_deity_or_marker",
    "lord_to_parent_relationship", "varsha_year_lord",
    "anchored_solar_return_iso",
    # V-11 fix (migration 428): triggered_yogas_jsonb_atomic and
    # lord_transit_at_period_start_jsonb REMOVED from chart_dashas — both were
    # permanently dead (no yoga-trigger or transit engine in GA7 to populate
    # them). Do not re-add without a real writer for them.
    "karakas_active_during_period",
    "is_truncated_at_window_start", "is_truncated_at_window_end",
    "kp_sublevel", "kp_sub_lord", "kp_sub_sub_lord",
]


def _copy_row_values(row: dict) -> tuple:
    """Row dict → tuple in _COPY_COLUMNS order, normalizing the jsonb defaults
    the executemany path used to apply."""
    normalized = {
        **row,
        "concurrent_system_lords_jsonb": row.get("concurrent_system_lords_jsonb"),
        "karakas_active_during_period": row.get("karakas_active_during_period"),
    }
    return tuple(normalized.get(col) for col in _COPY_COLUMNS)


def _upsert_rows(conn: Any, rows: list[dict], system_id: str, ayanamsha_id: str, *, commit: bool = True) -> int:
    """
    Bulk-load rows into chart_dashas via COPY (BA-P3 FIX 2 — replaces the prior
    executemany() path; COPY is materially faster for the ~thousands-of-rows-
    per-substep loads here, shortening the window in which a concurrent
    autovacuum on this shared table can starve the write past the substep
    timeout).

    No ON CONFLICT: safe because replace_prior_chart_dashas() (below) has just
    deleted every existing row in this exact (chart_id, system_id, ayanamsha_id)
    scope, across all build_ids, in the same transaction — there is nothing left
    for this batch to collide with. A collision here (e.g. a duplicate natural
    key within the freshly computed batch) is a genuine bug and should fail
    loud rather than be silently upserted away.

    Idempotent: replace_prior_chart_dashas scopes the delete to the
    (chart_id, system_id, ayanamsha_id) triple present in `rows`, so a rebuild
    under a new build_id replaces instead of accreting.

    Returns count of rows written.
    """
    if not rows:
        return 0

    replace_prior_chart_dashas(conn, rows)

    # The DB role's default statement_timeout (25-30s) is sized for OLTP
    # queries; a single COPY statement carrying a large system's full row set
    # (e.g. chara_karaka: ~40K rows) can exceed it under load, aborting an
    # otherwise-healthy bulk load (BA-P3 FIX 2c). SET LOCAL scopes to this
    # transaction/savepoint only and reverts automatically on commit/rollback
    # — the same pattern already used by every other heavy per-chart writer
    # in this codebase (ka_yojaka, ph_pramana, ka_taranga, etc.) for exactly
    # this reason.
    with conn.cursor() as _timeout_cur:
        _timeout_cur.execute("SET LOCAL statement_timeout = 0")

    with conn.cursor() as cur:
        with cur.copy(f"COPY chart_dashas ({', '.join(_COPY_COLUMNS)}) FROM STDIN") as copy:
            for row in rows:
                copy.write_row(_copy_row_values(row))

    # On the conformed orchestrator path (commit=False) the caller's SAVEPOINT +
    # per-sub-step commit own atomicity; only the legacy CLI path commits here.
    if commit:
        conn.commit()
    return len(rows)


# ── Build-state throughput update ─────────────────────────────────────────────

def _update_asset_throughput(
    conn: Any,
    chart_id: str,
    build_id: str,
    asset_id: str,
    rows_written: int,
    status: str = "in_progress",
) -> None:
    """Update asset_throughput (shared _telemetry helper, SET semantics). The final
    call (status='complete') passes the grand total and marks the asset 'lit'."""
    state = "lit" if status == "complete" else "building"
    update_asset_throughput(conn, asset_id, chart_id, build_id, rows_written, state=state)


# ── FORENSIC gate ─────────────────────────────────────────────────────────────

def _assert_forensic_vimshottari(
    rows: list[dict],
    moon_nak_name: str,
    starting_lord: str,
) -> None:
    """Assert FORENSIC anchor: Vimshottari starting lord = Jupiter."""
    if moon_nak_name != FORENSIC_MOON_NAK_NAME:
        raise ValueError(
            f"FORENSIC HALT: Moon nakshatra={moon_nak_name!r}, "
            f"expected={FORENSIC_MOON_NAK_NAME!r}"
        )
    if starting_lord != FORENSIC_VIMSHOTTARI_STARTING_LORD:
        raise ValueError(
            f"FORENSIC HALT: Vimshottari starting lord={starting_lord!r}, "
            f"expected={FORENSIC_VIMSHOTTARI_STARTING_LORD!r}"
        )


# ── Per-system build (incremental + idempotent) ───────────────────────────────

def build_system(
    system_id: str,
    ayanamsha_id: str,
    chart_id: str,
    build_id: str | None = None,
    *,
    conn: Any = None,
    birth_params: dict | None = None,
    skip_db: bool = False,
) -> dict[str, Any]:
    """
    Build one dasha system for one ayanamsha. This is the heavy-writer sub-step
    grain (7 systems × 5 ayanamshas = 35 chunks) driven by the orchestrator.
    Context-decay-safe: call this per-system.
    Returns summary dict.
    Raises on FORENSIC gate failure or two-pass divergence.

    Connection ownership (Orchestrator Convergence Phase 3):
    - conn injected (orchestrator path): upserts on the caller-owned connection,
      does NOT commit and does NOT write asset_throughput.
    - conn None (legacy CLI path): opens its own connection, commits via
      _upsert_rows, and writes asset_throughput via _telemetry.

    Per-chart birth (Phase 3B): birth_params None → the native (BIRTH_*); a
    non-native chart passes its birth so the dashas compute from its real Moon.
    The native-anchored FORENSIC assertion runs only for the native chart.
    """
    from contextlib import nullcontext
    if build_id is None:
        build_id = str(uuid.uuid4())

    # B1 elimination: resolve_birth_params() raises for ANY chart with falsy params
    # (native included). Every chart must supply DB-sourced birth params via
    # fetch_birth_params() before reaching here; the native has no special fallback.
    birth_params = resolve_birth_params(chart_id, birth_params)

    # Ensure L0 nakshatra lords are loaded (idempotent — skips if already populated)
    if not _NAKSHATRA_LORDS_1BASED:
        with (_conn() if conn is None else nullcontext(conn)) as _nc:
            _load_nakshatra_lords_l0(_nc)

    # V-1/G-7/D-1 fix: activate the real (chart_id, ayanamsha_id) natal context
    # from chart_facts + chart_divisionals before computing any system, so every
    # _build_row() call's lord_natal_* columns are DB-derived, not hand-copied.
    # Guarded by skip_db (mirrors this function's own DB-write guard) so the
    # "NO DB required" unit-test path (test_ga7_writer.py) never opens a real
    # connection — those tests seed the cache directly via set_natal_context().
    if not skip_db:
        with (_conn() if conn is None else nullcontext(conn)) as _nc:
            _activate_natal_context(chart_id, ayanamsha_id, _nc)

    logger.info(
        "[ga_dashas] Building system=%s ayanamsha=%s chart_id=%s",
        system_id, ayanamsha_id, chart_id,
    )

    # Get Moon position (needed for most systems)
    try:
        moon_sid, birth_jd = _get_moon_position(ayanamsha_id, birth_params)
    except Exception as exc:
        # Fallback: direct swisseph
        import swisseph as swe
        from pyjhora_adapter._ayanamsha import resolve_mode
        from pyjhora_adapter._jhora import drik
        birth_jd = _birth_jd_utc(birth_params)
        mode, _ = resolve_mode(ayanamsha_id)
        drik.set_ayanamsa_mode(mode)
        moon_sid = float(drik.sidereal_longitude(birth_jd, 1))  # 1 = Moon

    nak_idx_1, moon_nak_name, moon_nak_lord = _get_moon_nakshatra_lord(moon_sid)

    rows: list[dict] = []

    if system_id == "vimshottari":
        # FORENSIC assertion — native-anchored (Moon nak + starting lord); a
        # non-native chart has no pre-verified anchor, so it is not asserted.
        if chart_id == CANONICAL_CHART_ID:
            _assert_forensic_vimshottari([], moon_nak_name, moon_nak_lord)
        rows = compute_vimshottari(moon_sid, birth_jd, ayanamsha_id, chart_id, build_id)
        # KP sub-periods (CRITICAL OVERRIDE 2)
        kp_rows = compute_kp_subperiods(rows, chart_id, build_id, ayanamsha_id)
        rows.extend(kp_rows)
        # _verify_vimshottari still runs its native-anchored FORENSIC
        # starting-lord halt-check (and can raise) and its Pass-1 algebraic
        # no-op; its returned `verification` string is kept only for the
        # summary/log below — it is NO LONGER broadcast onto rows (A3 fix).
        verification = _verify_vimshottari([r for r in rows if r["level_n"] <= 4 and r.get("kp_sublevel") is None], moon_sid, chart_id)
        # A3 fix (M-22 Stage 3 wiring gap): every L1-4, non-KP row earns its
        # OWN verdict here via genuine per-row comparison against an
        # independently-computed dasha tree — see
        # `_apply_vimshottari_independent_verification`'s docstring.
        _apply_vimshottari_independent_verification(rows, moon_sid, birth_jd)

    elif system_id == "yogini":
        rows = compute_yogini_system(moon_sid, birth_jd, ayanamsha_id, chart_id, build_id)
        verification = _verify_yogini(rows)

    elif system_id == "ashtottari":
        rows = compute_ashtottari_system(moon_sid, birth_jd, ayanamsha_id, chart_id, build_id)
        verification = _verify_ashtottari(rows)

    elif system_id == "chara_karaka":
        rows = compute_chara_system(birth_jd, ayanamsha_id, chart_id, build_id, conn=conn)
        verification = _verify_chara(rows)

    elif system_id == "narayana":
        rows = compute_narayana_system(birth_jd, ayanamsha_id, chart_id, build_id, conn=conn)
        verification = _verify_narayana(rows)

    elif system_id == "naisargika":
        rows = compute_naisargika_system(birth_jd, ayanamsha_id, chart_id, build_id)
        verification = _verify_naisargika(rows)

    elif system_id == "mudda":
        rows = compute_mudda_system(birth_jd, ayanamsha_id, chart_id, build_id, birth_params=birth_params)
        verification = _verify_mudda(rows, nak_idx_1 - 1)  # nak_idx_1 is 1-based

    elif system_id == "kalachakra":
        rows = compute_kalachakra_system(moon_sid, birth_jd, ayanamsha_id, chart_id, build_id)
        verification = _verify_kalachakra(rows)

    else:
        raise ValueError(f"Unknown system_id: {system_id!r}")

    # CRITICAL OVERRIDE 1 assertion: ZERO level_n=5
    level5_rows = [r for r in rows if r["level_n"] == 5]
    if level5_rows:
        raise ValueError(
            f"CRITICAL OVERRIDE VIOLATED: {len(level5_rows)} level_n=5 rows found "
            f"in system {system_id}. Depth cap at Sukshma (level_n=4) enforced."
        )

    # Post-pass: sandhi
    compute_sandhi_post_pass(rows)

    # ── Verification status: ONLY on rows a verifier actually read ────────────────
    # §6.18 (2026-08-02). This loop used to read `for row in rows: row[...] = verification`,
    # broadcasting one function-level verdict onto every row at every level. Measured against
    # production before this fix: 2,505 of 1,358,993 `two_pass_verified` chart_dashas rows
    # (0.18%) had ever been examined — every `_verify_*` filters `level_n == 1` and looks at
    # nothing else. Levels 2-4 inherited a verdict computed over their parents.
    #
    # Two distinct bugs are fixed here, per §6.18:
    #   (b) the BROADCAST — an unexamined row now carries UNVERIFIED_DEFAULT, not an inherited
    #       tier. `single` is honest for it: no second derivation ran over THIS row.
    #   (c) the vimshottari_kp FILTER MISMATCH — `_verify_vimshottari` is handed
    #       `kp_sublevel is None` rows only, so the 17,910 KP sub-period rows were stamped by a
    #       check that never saw them. Fixed by STOPPING THE STAMPING (not by widening the
    #       filter): the KP sub-period decomposition is a different derivation from the
    #       Vimshottari sequence, and a verdict about one is not evidence about the other.
    #       Widening the filter would have manufactured exactly the false confidence this
    #       campaign exists to remove.
    #
    # `examined` must mirror each verifier's own input filter. Every `_verify_*` in this module
    # selects `level_n == 1`; `_verify_vimshottari` is additionally pre-filtered on
    # `kp_sublevel is None` at its call site. If a verifier's filter ever changes, this
    # predicate must change with it — the standing invariant (Phase 3) compares claimed-verified
    # rows against examined rows per table and fails loudly if the two drift apart.
    #
    # A3 fix (M-22 Stage 3 wiring gap): for system_id == "vimshottari", every level_n 1-4,
    # non-KP row was ALREADY stamped above by `_apply_vimshottari_independent_verification`
    # with a verdict it earned individually (two_pass_verified or divergent_flagged, per row —
    # not one string broadcast chart-wide). This loop must not clobber that with the single
    # `verification` string; those rows are skipped here and only counted. KP sub-periods and
    # any row outside level_n 1-4 still fall through to the UNVERIFIED_DEFAULT branch below,
    # unchanged from before this fix.
    examined_count = 0
    for row in rows:
        if system_id == "vimshottari" and row["level_n"] in (1, 2, 3, 4) and row.get("kp_sublevel") is None:
            examined_count += 1
            continue
        examined = row["level_n"] == 1 and row.get("kp_sublevel") is None
        row["verification_pass_status"] = verification if examined else UNVERIFIED_DEFAULT
        examined_count += 1 if examined else 0

    logger.info(
        "[ga_dashas] %s: verdict=%s applied to %d examined row(s); %d unexamined row(s) -> %s",
        system_id, verification, examined_count, len(rows) - examined_count, UNVERIFIED_DEFAULT,
    )

    # DB write
    rows_written = 0
    if not skip_db:
        owns_conn = conn is None
        with (_conn() if owns_conn else nullcontext(conn)) as c:
            rows_written = _upsert_rows(c, rows, system_id, ayanamsha_id, commit=owns_conn)
            if owns_conn:
                _update_asset_throughput(c, chart_id, build_id, "ga_dashas", rows_written, "in_progress")

        # Completeness check (BA-P3 FIX 2): never leave a silent partial substep.
        # A mismatch here means the COPY/executemany write was truncated (e.g. by
        # a reaper cancelling the statement mid-flight) while still reporting
        # PASS — exactly the failure mode that let 460,831 of 603,122 rows
        # persist as an undetected partial build.
        if rows_written != len(rows):
            raise RuntimeError(
                f"[ga_dashas] chart_id={chart_id} system={system_id} ayanamsha={ayanamsha_id}: "
                f"completeness check FAILED — computed {len(rows)} rows but only "
                f"{rows_written} persisted. Refusing to report this substep as PASS."
            )

    logger.info(
        "[ga_dashas] System=%s ayanamsha=%s: %d rows written (verification=%s)",
        system_id, ayanamsha_id, rows_written if not skip_db else len(rows), verification,
    )

    return {
        "system_id": system_id,
        "ayanamsha_id": ayanamsha_id,
        "chart_id": chart_id,
        "build_id": build_id,
        "rows_computed": len(rows),
        "rows_written": rows_written,
        "verification": verification,
        "level5_count": len(level5_rows),
        "status": "PASS",
    }


# ── Full build (all 8 systems × 5 ayanamshas) ────────────────────────────────
# CR-104 (D-2 Lane V-6): "narayana" added — the orchestrator adapter
# (pipeline/orchestrator/writers/ga_dashas.py) iterates this list generically
# via plan_substeps, so no adapter change is needed to build it.

SYSTEMS = [
    "vimshottari", "yogini", "ashtottari",
    "chara_karaka", "naisargika", "mudda", "kalachakra", "narayana",
]


def write_dasha_scope_cap_sentinels(chart_id: str, build_id: str, *, conn: Any = None) -> int:
    """
    Write the 2 scope-cap sentinel rows (Prana Dasha 5th-level; KP sub-period
    levels beyond sub_sub) that document "intentionally not computed" so
    absence != bug (see the two blocks this replaces, below).

    SD-DASHA-1 fix (SAMĀPTI v2.0 §9.5): these sentinels were previously only
    written from build_ga_dashas() — the CLI/full-build path — and NEVER from
    the orchestrator adapter (pipeline/orchestrator/writers/ga_dashas.py),
    which drives every real "click Build" chart via run_substep() calling
    build_system()/_run_concurrency_post_pass_db() directly, never
    build_ga_dashas() itself. Confirmed live: chart_dashas has ZERO
    system_id='scope_cap' rows for any of the 3 charts in production
    (482012f1, 1c826d5a, cb73cd3d) — all orchestrator-built. Extracting this
    into a shared, conn-aware function (same owns_conn pattern as
    _run_concurrency_post_pass_db just below) lets both paths call the same
    code, so the two build paths can no longer silently diverge again.

    Connection ownership: conn injected (orchestrator post-pass substep) ->
    runs on the caller-owned ctx.db_conn without committing (FROZEN
    orchestrator contract, §N.2: writer never commits); conn None -> opens
    and commits its own (legacy CLI path, build_ga_dashas()).

    Idempotent: _upsert_rows -> replace_prior_chart_dashas scopes the delete
    to (chart_id, system_id='scope_cap', ayanamsha_id='INVARIANT'), so a
    rebuild under a new build_id replaces instead of accreting.

    Returns count of rows written (0, 1, or 2 — partial writes are logged as
    warnings, never fatal, matching the pre-existing non-fatal semantics).
    """
    from contextlib import nullcontext

    common_fields = {
        "chart_id": chart_id,
        "ayanamsha_id": "INVARIANT",
        "build_id": build_id,
        "system_id": "scope_cap",
        "parent_row_id": None,
        "lord_sign": None,
        "start_date": date(1984, 2, 5),
        "end_date": date(1984, 2, 5),
        "start_iso": "1984-02-05T00:00:00+00:00",
        "end_iso": "1984-02-05T00:00:00+00:00",
        "duration_days": 0.0,
        "sandhi_flag": False,
        "karaka_role_at_period": None,
        # M-22 fix: this row is a deliberate "not computed — beyond scope"
        # marker (see citation_human), not a real computation — stamping it
        # "two_pass_verified" claimed a verified value where none exists.
        # Uses the same self-descriptive string as verification_method so
        # the row is unambiguous; falls through
        # VERIFICATION_RESCALE.get(status, documented_approximation) to the
        # lowest honest tier (0.60), never the top tier.
        "verification_pass_status": "scope_cap_sentinel",
        "verification_method": "scope_cap_sentinel",
        "citation_ref": "L1_GANITA_SCOPE_CAP",
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "engine_version": "pyjhora_adapter/0.1.0",
        "lord_natal_house_d1": None,
        "lord_natal_sign": None,
        "lord_natal_nakshatra": None,
        "lord_natal_dignity_d1": None,
        "lord_natal_shadbala_total": None,
        "sandhi_with_next_dasha_lord": None,
        "next_dasha_start_iso": None,
        "concurrent_system_lords_jsonb": None,
        "convergence_count_at_start": None,
        "applies_to_this_chart_flag": False,
        "period_deity_or_marker": "scope_cap",
        "lord_to_parent_relationship": None,
        "varsha_year_lord": None,
        "anchored_solar_return_iso": None,
        "karakas_active_during_period": None,
        "is_truncated_at_window_start": False,
        "is_truncated_at_window_end": False,
        "kp_sub_lord": None,
        "kp_sub_sub_lord": None,
    }

    scope_cap_row = {
        **common_fields,
        "dasha_row_id": str(uuid.uuid4()),
        "level_n": 5,
        "lord_graha": "PRANA_DASHA",
        "citation_human": "Prana Dasha (5th-level sub-period) not computed — beyond L1 Ganita scope",
        "kp_sublevel": None,
    }
    kp_cap_row = {
        **common_fields,
        "dasha_row_id": str(uuid.uuid4()),
        "level_n": 4,
        "lord_graha": "KP_LEVELS_BEYOND_SUB_SUB",
        "citation_human": (
            "KP sub-period levels beyond sub_sub (deha/jeeva/etc.) not computed — "
            "beyond L1 Ganita scope; kp_sublevel='sub' and 'sub_sub' are the maximum"
        ),
        "kp_sublevel": "beyond_sub_sub",
    }

    owns_conn = conn is None
    written = 0
    with (_conn() if owns_conn else nullcontext(conn)) as sc_conn:
        try:
            written += _upsert_rows(sc_conn, [scope_cap_row], "scope_cap", "INVARIANT", commit=owns_conn)
            logger.info("[ga_dashas] Prana Dasha scope-cap sentinel written")
        except Exception as exc:
            logger.warning("[ga_dashas] Scope-cap sentinel write failed (non-fatal): %s", exc)

        try:
            written += _upsert_rows(sc_conn, [kp_cap_row], "scope_cap", "INVARIANT", commit=owns_conn)
            logger.info("[ga_dashas] KP beyond-sub_sub scope-cap sentinel written")
        except Exception as exc:
            logger.warning("[ga_dashas] KP scope-cap sentinel write failed (non-fatal): %s", exc)

    return written


def build_ga_dashas(
    chart_id: str,
    build_id: str | None = None,
    *,
    systems: list[str] | None = None,
    ayanamshas: list[str] | None = None,
    skip_db: bool = False,
) -> dict[str, Any]:
    """
    Run full GA7 build: 7 systems × 5 ayanamshas.
    Per-system, per-ayanamsha incremental (context-decay-safe).
    Runs post-pass concurrency annotation after all systems complete (for Lahiri).
    Returns comprehensive summary.
    """
    if build_id is None:
        build_id = str(uuid.uuid4())

    target_systems = systems or SYSTEMS
    target_ayanamshas = ayanamshas or AYANAMSHAS

    summary: dict[str, Any] = {
        "asset_id": "ga_dashas",
        "chart_id": chart_id,
        "build_id": build_id,
        "systems": {},
        "total_rows": 0,
        "status": "IN_PROGRESS",
    }

    all_rows_by_system: dict[str, list[dict]] = {}

    for aya in target_ayanamshas:
        for sys in target_systems:
            key = f"{sys}:{aya}"
            try:
                result = build_system(sys, aya, chart_id, build_id, skip_db=skip_db)
                summary["systems"][key] = result
                summary["total_rows"] += result["rows_computed"]

                # Collect rows for concurrency post-pass (Lahiri primary)
                if aya == "lahiri" and not skip_db:
                    # Re-read from DB for post-pass (already written)
                    # For in-memory mode (skip_db), skip concurrency post-pass
                    pass

            except Exception as exc:
                msg = str(exc)
                logger.error("[ga_dashas] FAIL system=%s aya=%s: %s", sys, aya, msg)
                summary["systems"][key] = {
                    "status": "FAIL",
                    "error": msg,
                    "system_id": sys,
                    "ayanamsha_id": aya,
                }
                if "FORENSIC HALT" in msg or "CRITICAL OVERRIDE VIOLATED" in msg:
                    summary["status"] = "HALT"
                    summary["halt_reason"] = msg
                    return summary

    # Scope-cap sentinels: Prana Dasha (5th-level sub-period) + KP sub-period
    # levels beyond sub_sub — both intentionally not computed; emitted once
    # per build under system_id='scope_cap' / ayanamsha_id='INVARIANT' so
    # absence != bug. SD-DASHA-1: shared with the orchestrator adapter's
    # post-pass substep (pipeline/orchestrator/writers/ga_dashas.py) via
    # write_dasha_scope_cap_sentinels() so the two build paths cannot
    # silently diverge on this again.
    if not skip_db:
        write_dasha_scope_cap_sentinels(chart_id, build_id)

    # Post-pass: concurrency annotation (DB-side, Lahiri)
    if not skip_db:
        try:
            _run_concurrency_post_pass_db(chart_id, build_id)
        except Exception as exc:
            logger.warning("[ga_dashas] Concurrency post-pass failed: %s", exc)

        # Final asset_throughput update — COMPLETE (pass the grand total, mark lit)
        try:
            with _conn() as conn:
                total = conn.execute(
                    "SELECT count(*) FROM chart_dashas WHERE chart_id = %s AND build_id = %s",
                    [chart_id, build_id],
                ).fetchone()[0]
                _update_asset_throughput(
                    conn, chart_id, build_id, "ga_dashas",
                    total, "complete"
                )
        except Exception as exc:
            logger.warning("[ga_dashas] Final throughput update skipped: %s", exc)

    failed = [k for k, v in summary["systems"].items() if v.get("status") == "FAIL"]
    summary["status"] = "FAIL" if failed else "PASS"
    summary["failed_systems"] = failed

    return summary


def _run_concurrency_post_pass_db(chart_id: str, build_id: str, *, conn: Any = None) -> None:
    """
    Run concurrency post-pass against DB: for each L1 row in chart_dashas,
    compute concurrent_system_lords_jsonb + convergence_count_at_start
    and UPDATE the rows.

    Connection ownership (Orchestrator Convergence Phase 3): conn injected →
    runs on the caller-owned connection without committing; conn None → opens
    and commits its own (legacy CLI path).
    """
    from contextlib import nullcontext
    owns_conn = conn is None
    with (_conn() if owns_conn else nullcontext(conn)) as conn:
        # Get all L1 rows for this chart+build, grouped by system
        cursor = conn.execute(
            """
            SELECT dasha_row_id, system_id, lord_graha, start_date, end_date
            FROM chart_dashas
            WHERE chart_id = %s AND build_id = %s
              AND level_n = 1
              AND kp_sublevel IS NULL
            ORDER BY system_id, start_date
            """,
            [chart_id, build_id],
        )
        all_l1 = cursor.fetchall()

        # Build per-system lookup
        by_system: dict[str, list] = {}
        for row in all_l1:
            sid = row["system_id"]
            if sid not in by_system:
                by_system[sid] = []
            by_system[sid].append(row)

        # For each row, find concurrent lords
        for row in all_l1:
            row_id = row["dasha_row_id"]
            sys_id = row["system_id"]
            lord = row["lord_graha"]
            start_d = row["start_date"]
            end_d = row["end_date"]
            concurrent = {}
            for other_sys, other_rows in by_system.items():
                if other_sys == sys_id:
                    continue
                for other_row in other_rows:
                    o_start = other_row["start_date"]
                    o_end = other_row["end_date"]
                    if o_start <= start_d < o_end:
                        concurrent[other_sys] = other_row["lord_graha"]
                        break

            convergence = 1 + sum(1 for v in concurrent.values() if v == lord)

            conn.execute(
                """
                UPDATE chart_dashas SET
                    concurrent_system_lords_jsonb = %s::jsonb,
                    convergence_count_at_start = %s
                WHERE dasha_row_id = %s
                """,
                [json.dumps(concurrent), convergence, str(row_id)],
            )

        if owns_conn:
            conn.commit()
        logger.info(
            "[ga_dashas] Concurrency post-pass: updated %d L1 rows", len(all_l1)
        )


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="GA7 dasha writer")
    parser.add_argument("--chart_id", default=CANONICAL_CHART_ID)
    parser.add_argument("--build_id", default=None)
    parser.add_argument("--systems", nargs="+", default=None,
                        choices=SYSTEMS + ["all"])
    parser.add_argument("--ayanamshas", nargs="+", default=None,
                        choices=AYANAMSHAS + ["all"])
    parser.add_argument("--skip_db", action="store_true")
    parser.add_argument("--json", dest="output_json", action="store_true")
    args = parser.parse_args()

    systems = None if args.systems is None or "all" in (args.systems or []) else args.systems
    ayanamshas = None if args.ayanamshas is None or "all" in (args.ayanamshas or []) else args.ayanamshas

    result = build_ga_dashas(
        chart_id=args.chart_id,
        build_id=args.build_id,
        systems=systems,
        ayanamshas=ayanamshas,
        skip_db=args.skip_db,
    )

    if args.output_json:
        import json as _json
        print(_json.dumps(result, indent=2, default=str))
    else:
        print(f"\n{'='*60}")
        print(f"GA7 DASHAS BUILD")
        print(f"  Status:    {result['status']}")
        print(f"  chart_id:  {result['chart_id']}")
        print(f"  build_id:  {result['build_id']}")
        print(f"  Total rows: {result['total_rows']}")
        if result.get("failed_systems"):
            print(f"  Failed:    {result['failed_systems']}")
        print(f"{'='*60}\n")

    sys.exit(0 if result.get("status") == "PASS" else 1)


if __name__ == "__main__":
    main()
