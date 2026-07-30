"""
services.ka_kshetra.stage3_clocks — Lane B, Stage 3: dasha-system clocks.

Per KALA_W2_FIELD_DESIGN_v1_0.md §4: Law-1 applicability evaluation per
dasha system (item 12, §4.1) + the boundary-uncertainty writers that
consume `uncertainty.py` (item 24-full, §4.2) + the published functions
Lane C calls (`applicable_systems`, `clock_activation`, `boundary_breakpoints`).

Legacy is untouched (design doc §1 rail 2): this module only reads
`chart_dashas` / `chart_facts` / `brahma_dasha_systems` / `ephemeris`
read-only, and only writes `kala_field_clocks` / `kala_field_boundaries`
(the two tables this lane owns, migration 477).

── Corpus-vs-design gaps this builder resolved, and how (all documented
   inline at point of use too) ──────────────────────────────────────────

1. `bg_dasha_systems` in the design doc is this repo's `brahma_dasha_systems`
   L0 catalog (19 rows, corpus-sourced, `brahmagyan/l0_dasha_systems.py`).
   That catalog does NOT carry `entry_condition` / `competence_class` /
   `seniority_rank` as literal machine-evaluable columns — its
   `conditions_for_use` column is free classical prose (e.g. "10th-lord-
   in-10th charts.", "hora/day-night rule."), not an evaluable predicate.
   Per B.10 (no fabricated computation) this builder does not invent a
   prose parser. `competence_class` / `seniority_rank` are static
   classification metadata about each SYSTEM (not a per-chart
   computation), so `SYSTEM_META` below hardcodes them directly — exactly
   the same technique the design doc itself uses for its quality-rule
   table (§4.1 step 4, a literal per-system_id lookup in code).

2. This product's L1 writer (`ga_dashas_writer.py` / `ka_dasha_kala`)
   computes 7 systems into `chart_dashas`: vimshottari, ashtottari, yogini,
   chara_karaka, naisargika, mudda, kalachakra. `brahma_dasha_systems`
   covers a different, only partially-overlapping vocabulary (19 rows,
   'chara_jaimini' not 'chara_karaka', no naisargika/mudda rows at all).
   `SYSTEM_META` is keyed to the 7 systems chart_dashas actually computes.

3. The design doc's step-4 quality-rule table gives an exact formula for
   vimshottari / yogini / kalachakra / chara / mudda / naisargika, plus a
   generic 'conditional' placeholder with no concrete system bound to it
   in this repo. `ashtottari` has a REAL classical entry condition
   (`brahma_dasha_systems.conditions_for_use`: "Rahu in a quadrant/trine
   from lagna-lord, day birth in Krishna paksha / night in Shukla") but no
   margin/tolerance formula is specified for it anywhere the design doc
   defines, so per its own explicit instruction ("Any system not in this
   table is not_computed... a builder MUST NOT invent one") ashtottari is
   evaluated as `not_computed` at the quality step, not excluded at
   jurisdiction (see `_evaluate_quality`).

4. Jurisdiction (§4.1 step 1) requires evaluating `entry_condition` against
   L1 facts. None of the 7 systems this builder covers has a real,
   machine-evaluable entry condition sourced anywhere in this corpus (see
   #1) -- all 7 pass jurisdiction unconditionally. A future system with a
   real, citable, machine-evaluable condition should extend
   `_evaluate_jurisdiction`, never bypass this module's honesty discipline.

5. `r_{s,e}(t)`'s lord_stack nodes are `'graha:<lord>'` (§5.1 C-3), but
   `chara_karaka`'s running "lord" is a RASHI (`chart_dashas.lord_sign`),
   not a graha. This builder maps a sign to its classical ruling graha
   (`SIGN_LORDS`, the same static Parashari rulership table used
   elsewhere in this codebase, e.g. `ga_ayurdaya_writer.SIGN_LORDS`) before
   looking up promise-graph reachability -- a citation-free, universally
   agreed classical mapping, not an invented heuristic.

6. The design doc's sigma_lambda chain (v_Moon-driven) is specified for
   Moon-nakshatra/pada-driven systems (vimshottari, yogini, ashtottari,
   kalachakra). `chara_karaka`'s birth-time sensitivity flows through the
   ascendant's much-faster rotation rate, a different physical channel the
   design doc gives no formula for; naisargika and mudda are explicitly
   exempted by the design doc itself. This builder therefore treats
   chara_karaka the SAME as naisargika/mudda (`sigma_t = sigma_T` alone) —
   the conservative, non-fabricating choice — rather than reusing v_Moon
   for a lagna-driven system, which would be a physics error dressed as a
   formula.

7. "T_MD^birth" ("the full ... mahadasha length of the birth-... lord") is
   sourced ENTIRELY from `chart_dashas` itself (`full_lord_period_days`),
   never a hardcoded classical period table -- per SS_N.5 (L1 is the
   authority; a derivation inherits, it does not recompute). This also
   sidesteps needing to parse three different `brahma_dasha_systems.
   sequence_jsonb` shapes (a flat lord/years list for vimshottari/
   ashtottari; free descriptive prose for kalachakra/chara_jaimini).

8. `v_Moon` at birth ("from the stage-0 spline", Lane A's owned code) is
   computed independently here via a direct `swisseph` call at the birth
   Julian day (tropical longitude speed -- ayanamsha is a constant offset,
   so speed is ayanamsha-invariant) rather than reading Lane A's
   `stage0_kinematics.py` (never read another lane's code) or depending on
   `kala_field_kinematics`'s event-grain rows (which are not a dense
   per-day grid and are not guaranteed to carry a sample AT the birth
   instant). Day-grade precision is this whole wave's explicit ceiling
   (design doc scope note), so an exact swisseph evaluation at the birth
   instant is at least as precise as required, never an approximation of
   a number the design asked for exactly.

9. `mudda`'s quality rule ("q = 1.0 if the evaluated t lies inside a
   computed varsha year, else 0.0") textually depends on t, but
   `kala_field_clocks.quality` is a single stored scalar per (chart,
   system). This builder evaluates mudda's rule once, at a representative
   reference instant (default: build time / "now"), documented on
   `evaluate_applicability`'s `reference_dt` parameter -- the same
   representative-instant reading this builder gives every other static
   per-system value on this table.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from . import uncertainty as U

# ── Epoch conversion: t_days = days since J2000, matching stage 0's
#    convention (KALA_W2_FIELD_DESIGN_v1_0.md §3.1). J2000 = 2000-01-01
#    12:00:00 UTC (JD 2451545.0). Day-grade precision throughout W2 makes
#    the ~64s TT/UTC offset immaterial. ─────────────────────────────────────

J2000_EPOCH = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def to_t_days(dt: datetime) -> float:
    """Convert an aware (or naive-UTC) datetime to days-since-J2000."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (dt - J2000_EPOCH).total_seconds() / 86400.0


def from_t_days(t_days: float) -> datetime:
    return J2000_EPOCH + timedelta(days=t_days)


# ── Static classical reference (see module docstring #1-#2) ────────────────

LEVEL_TEXT_BY_N: dict[int, str] = {1: "MD", 2: "AD", 3: "PD", 4: "SD", 5: "PrD"}
LEVEL_DEPTH_WEIGHT: dict[str, float] = {"MD": 1.0, "AD": 0.7, "PD": 0.5, "SD": 0.3, "PrD": 0.15}
LEVEL_ORDER: tuple[str, ...] = ("MD", "AD", "PD", "SD", "PrD")

#: Standard Parashari sign-lordship table (see module docstring #5).
SIGN_LORDS: dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

#: The classical seven-graha chara-karaka candidate set (Sapta Chara
#: Karaka scheme, Sun through Saturn, nodes excluded) — see module
#: docstring; used by the "chara" quality rule's d_sign computation
#: (§4.1 step 4: "min over the chara-karaka set of each graha's distance
#: to a sign boundary").
CHARA_KARAKA_CANDIDATE_GRAHAS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)

#: chart_facts.fact_subject abbreviations (PLANET_TO_SUBJECT, mirrored
#: from ga_writers/ga_nakshatra_emitters.py / ga_positions_writer.py) for
#: the seven chara-karaka candidates.
GRAHA_TO_FACT_SUBJECT: dict[str, str] = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
}

DEFAULT_AYANAMSHA_ID = "lahiri_chitrapaksha"

#: Systems whose sigma_t is driven purely by birth-time uncertainty
#: (§4.2's naisargika/mudda exception, extended to chara_karaka per module
#: docstring #6).
BIRTH_TIME_ONLY_SYSTEMS: frozenset[str] = frozenset({"naisargika", "mudda", "chara_karaka"})

#: Systems whose sigma_t is propagated through the Moon-nakshatra/pada
#: fractional-arc chain (§4.2), keyed to the fractional-arc span each uses.
FRACTIONAL_ARC_SPAN_DEG: dict[str, float] = {
    "vimshottari": U.NAK_SPAN_DEG,
    "yogini": U.NAK_SPAN_DEG,
    "ashtottari": U.NAK_SPAN_DEG,
    "kalachakra": U.PADA_SPAN_DEG,
}


@dataclass(frozen=True)
class SystemMeta:
    competence_class: str
    seniority_rank: int
    is_predictive: bool


#: Rule C-4: naisargika (competence_class='life_stage') is non-predictive
#: by construction, not by fitting -- its w_s == 0 always, and it must not
#: even be offered to the fitter (§5.1). Every other system here IS
#: predictive-eligible (the fitter may still learn w_s == 0 for one, but
#: that is a calibration outcome, not a structural exclusion).
SYSTEM_META: dict[str, SystemMeta] = {
    "vimshottari":  SystemMeta(competence_class="fruition", seniority_rank=1, is_predictive=True),
    "ashtottari":   SystemMeta(competence_class="fruition", seniority_rank=2, is_predictive=True),
    "yogini":       SystemMeta(competence_class="flavour", seniority_rank=3, is_predictive=True),
    "kalachakra":   SystemMeta(competence_class="arena", seniority_rank=4, is_predictive=True),
    "chara_karaka": SystemMeta(competence_class="arena", seniority_rank=5, is_predictive=True),
    "mudda":        SystemMeta(competence_class="annual", seniority_rank=6, is_predictive=True),
    "naisargika":   SystemMeta(competence_class="life_stage", seniority_rank=7, is_predictive=False),
}


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _distance_to_grid_boundary(value_deg: float, span_deg: float) -> float:
    """Distance (degrees) from value_deg to the nearest multiple-of-span_deg
    boundary (value_deg mod span_deg, folded to the nearer side)."""
    r = value_deg % span_deg
    return min(r, span_deg - r)


# ── Quality rules (§4.1 step 4, exact) ──────────────────────────────────────

def moon_quality_nakshatra(moon_longitude_deg: float) -> tuple[float, float]:
    """vimshottari / yogini: q = clamp01(d_nak / 0.50deg). Returns (d_nak, q)."""
    d_nak = _distance_to_grid_boundary(moon_longitude_deg, U.NAK_SPAN_DEG)
    return d_nak, _clamp01(d_nak / 0.50)


def moon_quality_pada(moon_longitude_deg: float) -> tuple[float, float]:
    """kalachakra: q = clamp01(d_pada / 0.25deg). Returns (d_pada, q)."""
    d_pada = _distance_to_grid_boundary(moon_longitude_deg, U.PADA_SPAN_DEG)
    return d_pada, _clamp01(d_pada / 0.25)


def chara_quality(degree_in_sign_by_graha: dict[str, float]) -> tuple[float, float]:
    """chara: q = clamp01(d_sign / 1.00deg), d_sign = min over the
    chara-karaka set of each graha's distance to a sign boundary.
    `degree_in_sign_by_graha` values are already in [0, 30) (degree within
    the graha's occupied sign), so distance-to-boundary is simply
    min(d, 30-d) with no further modulus needed."""
    candidates = [
        degree_in_sign_by_graha[g]
        for g in CHARA_KARAKA_CANDIDATE_GRAHAS
        if g in degree_in_sign_by_graha
    ]
    if not candidates:
        raise ValueError(
            "chara_quality requires at least one chara-karaka-set graha's "
            "degree_in_sign; got none"
        )
    d_sign = min(min(d, U.SIGN_SPAN_DEG - d) for d in candidates)
    return d_sign, _clamp01(d_sign / 1.00)


# ── DB-facing readers (chart_facts / chart_dashas) ──────────────────────────

def _rows_as_dicts(rows: Any, cols: list[str]) -> list[dict]:
    return [dict(zip(cols, r)) if not isinstance(r, dict) else r for r in rows]


def fetch_moon_longitude_deg(chart_id: str, conn: Any, ayanamsha_id: str = DEFAULT_AYANAMSHA_ID) -> float:
    row = conn.execute(
        """
        SELECT fact_value_num
        FROM chart_facts
        WHERE chart_id = %s AND ayanamsha_id = %s
          AND fact_category = 'graha_position' AND fact_subject = 'MOON'
          AND fact_key = 'longitude_sidereal'
        """,
        [chart_id, ayanamsha_id],
    ).fetchone()
    if row is None:
        raise RuntimeError(
            f"no MOON longitude_sidereal chart_facts row for chart {chart_id!r} "
            f"ayanamsha {ayanamsha_id!r}"
        )
    val = row["fact_value_num"] if isinstance(row, dict) else row[0]
    return float(val)


def fetch_degree_in_sign_by_graha(
    chart_id: str, conn: Any, ayanamsha_id: str = DEFAULT_AYANAMSHA_ID,
) -> dict[str, float]:
    subject_to_graha = {v: k for k, v in GRAHA_TO_FACT_SUBJECT.items()}
    rows = conn.execute(
        """
        SELECT fact_subject, fact_value_num
        FROM chart_facts
        WHERE chart_id = %s AND ayanamsha_id = %s
          AND fact_category = 'graha_sign_attributes' AND fact_key = 'degree_in_sign'
          AND fact_subject = ANY(%s)
        """,
        [chart_id, ayanamsha_id, list(GRAHA_TO_FACT_SUBJECT.values())],
    ).fetchall()
    dict_rows = _rows_as_dicts(rows, ["fact_subject", "fact_value_num"])
    out: dict[str, float] = {}
    for r in dict_rows:
        graha = subject_to_graha.get(r["fact_subject"])
        if graha is not None and r["fact_value_num"] is not None:
            out[graha] = float(r["fact_value_num"])
    return out


def _chart_dashas_row_count(chart_id: str, system_id: str, conn: Any) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM chart_dashas WHERE chart_id = %s AND system_id = %s",
        [chart_id, system_id],
    ).fetchone()
    if row is None:
        return 0
    n = row["n"] if isinstance(row, dict) else row[0]
    return int(n)


def _chart_dashas_covers_instant(
    chart_id: str, system_id: str, level_n: int, at_dt: datetime, conn: Any,
) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND level_n = %s
          AND start_iso <= %s AND end_iso > %s
        LIMIT 1
        """,
        [chart_id, system_id, level_n, at_dt, at_dt],
    ).fetchone()
    return row is not None


def _chart_dashas_level1_rows(chart_id: str, system_id: str, conn: Any) -> list[dict]:
    rows = conn.execute(
        """
        SELECT dasha_row_id, lord_graha, lord_sign, start_iso, end_iso, duration_days
        FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND level_n = 1
        ORDER BY start_iso ASC
        """,
        [chart_id, system_id],
    ).fetchall()
    return _rows_as_dicts(
        rows, ["dasha_row_id", "lord_graha", "lord_sign", "start_iso", "end_iso", "duration_days"]
    )


# ── Law-1 applicability evaluation (§4.1) ───────────────────────────────────

@dataclass(frozen=True)
class ClockApplicability:
    system_id: str
    applicability_state: str  # 'applicable' | 'excluded_by_condition' | 'not_computed'
    exclusion_reason: str | None
    competence_class: str
    seniority_rank: int
    quality: float | None
    quality_basis: str | None
    is_predictive: bool


def _evaluate_jurisdiction(system_id: str) -> tuple[bool, str | None]:
    """Step 1 (§4.1). See module docstring #4: no system this builder
    covers has a real, machine-evaluable entry_condition sourced anywhere
    in this corpus, so jurisdiction passes unconditionally for all of
    them. Returns (passes, exclusion_reason_if_not)."""
    del system_id  # unused today; kept for signature stability
    return True, None


def _evaluate_quality(
    chart_id: str,
    system_id: str,
    conn: Any,
    *,
    ayanamsha_id: str,
    reference_dt: datetime,
) -> tuple[float | None, str | None]:
    """Step 4 (§4.1), exact per-system rules. Returns (quality, basis);
    (None, None) means 'no quality rule defined' -- caller must render
    that as not_computed, never invent a value (design doc's own words)."""
    if system_id == "naisargika":
        return 1.0, "naisargika_deterministic_age_based"

    if system_id in ("vimshottari", "yogini"):
        moon_lon = fetch_moon_longitude_deg(chart_id, conn, ayanamsha_id)
        d_nak, q = moon_quality_nakshatra(moon_lon)
        return q, f"moon_nakshatra_margin={d_nak:.4f}deg"

    if system_id == "kalachakra":
        moon_lon = fetch_moon_longitude_deg(chart_id, conn, ayanamsha_id)
        d_pada, q = moon_quality_pada(moon_lon)
        return q, f"moon_pada_margin={d_pada:.4f}deg"

    if system_id == "chara_karaka":
        degrees = fetch_degree_in_sign_by_graha(chart_id, conn, ayanamsha_id)
        d_sign, q = chara_quality(degrees)
        return q, f"chara_karaka_sign_margin={d_sign:.4f}deg"

    if system_id == "mudda":
        covers = _chart_dashas_covers_instant(chart_id, "mudda", 1, reference_dt, conn)
        basis = f"mudda_varsha_coverage_at={reference_dt.isoformat()}"
        return (1.0 if covers else 0.0), basis

    # ashtottari, and any future/unknown system: no quality rule defined
    # (module docstring #3) -- honest not_computed, never invented.
    return None, None


def evaluate_applicability(
    chart_id: str,
    system_id: str,
    conn: Any,
    *,
    ayanamsha_id: str = DEFAULT_AYANAMSHA_ID,
    reference_dt: datetime | None = None,
) -> ClockApplicability:
    """The full §4.1 algorithm for one (chart, system). `reference_dt`
    defaults to now (UTC) -- see module docstring #9 for why mudda's
    "evaluated t" is read as a representative build-time instant."""
    meta = SYSTEM_META.get(system_id)
    if meta is None:
        raise ValueError(f"unknown system_id for Law-1 applicability: {system_id!r}")

    ref_dt = reference_dt or datetime.now(timezone.utc)

    passes, exclusion_reason = _evaluate_jurisdiction(system_id)
    if not passes:
        return ClockApplicability(
            system_id=system_id,
            applicability_state="excluded_by_condition",
            exclusion_reason=exclusion_reason,
            competence_class=meta.competence_class,
            seniority_rank=meta.seniority_rank,
            quality=None,
            quality_basis=None,
            is_predictive=meta.is_predictive,
        )

    count = _chart_dashas_row_count(chart_id, system_id, conn)
    if count == 0:
        return ClockApplicability(
            system_id=system_id,
            applicability_state="not_computed",
            exclusion_reason="no chart_dashas rows for system",
            competence_class=meta.competence_class,
            seniority_rank=meta.seniority_rank,
            quality=None,
            quality_basis=None,
            is_predictive=meta.is_predictive,
        )

    quality, basis = _evaluate_quality(
        chart_id, system_id, conn, ayanamsha_id=ayanamsha_id, reference_dt=ref_dt
    )
    if quality is None:
        return ClockApplicability(
            system_id=system_id,
            applicability_state="not_computed",
            exclusion_reason="no quality rule defined",
            competence_class=meta.competence_class,
            seniority_rank=meta.seniority_rank,
            quality=None,
            quality_basis=None,
            is_predictive=meta.is_predictive,
        )

    return ClockApplicability(
        system_id=system_id,
        applicability_state="applicable",
        exclusion_reason=None,
        competence_class=meta.competence_class,
        seniority_rank=meta.seniority_rank,
        quality=quality,
        quality_basis=basis,
        is_predictive=meta.is_predictive,
    )


def applicable_systems(
    chart_id: str,
    conn: Any,
    *,
    ayanamsha_id: str = DEFAULT_AYANAMSHA_ID,
    reference_dt: datetime | None = None,
) -> list[ClockApplicability]:
    """PUBLISHED FUNCTION (Lane B -> Lane C). Evaluates Law-1 applicability
    for every daśā system this product computes into `chart_dashas`, in a
    stable (sorted by system_id) order."""
    ref_dt = reference_dt or datetime.now(timezone.utc)
    return [
        evaluate_applicability(chart_id, sid, conn, ayanamsha_id=ayanamsha_id, reference_dt=ref_dt)
        for sid in sorted(SYSTEM_META.keys())
    ]


def write_clock_rows(chart_id: str, applicabilities: list[ClockApplicability], conn: Any) -> int:
    """Idempotent per-chart write to `kala_field_clocks`: delete-then-insert
    scoped to (chart_id x system_id) — §N.3 / the ga_writers/_idempotency.py
    pattern. Deletion is scoped to exactly the system_ids being (re)written,
    so a partial re-run never wipes a sibling system's row."""
    if not applicabilities:
        return 0
    system_ids = [a.system_id for a in applicabilities]
    conn.execute(
        "DELETE FROM kala_field_clocks WHERE chart_id = %s AND system_id = ANY(%s)",
        [chart_id, system_ids],
    )
    for a in applicabilities:
        conn.execute(
            """
            INSERT INTO kala_field_clocks
                (chart_id, system_id, applicability_state, exclusion_reason,
                 competence_class, seniority_rank, quality, quality_basis,
                 is_predictive, source_table)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'chart_dashas')
            """,
            [
                chart_id, a.system_id, a.applicability_state, a.exclusion_reason,
                a.competence_class, a.seniority_rank, a.quality, a.quality_basis,
                a.is_predictive,
            ],
        )
    return len(applicabilities)


# ── v_Moon at birth (module docstring #8) ───────────────────────────────────

def moon_velocity_dps_at_jd(jd_ut: float) -> float:
    """Moon's tropical longitude speed (deg/day) at a Julian day (UT), via
    a direct swisseph evaluation. Ayanamsha-invariant (a constant angular
    offset does not change the time-derivative), so no sidereal mode is
    needed for this value specifically."""
    import swisseph as swe

    result, _ = swe.calc_ut(jd_ut, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SPEED)
    return float(result[3])


def moon_velocity_dps_at_birth(birth_params: dict) -> float:
    """`birth_params` per `pipeline.orchestrator.birth_params.fetch_birth_params`
    shape: {'datetime_iso': <local, naive>, 'tz_offset_hours': <float>, ...}."""
    import swisseph as swe

    local_dt = datetime.fromisoformat(birth_params["datetime_iso"])
    utc_dt = local_dt - timedelta(hours=float(birth_params["tz_offset_hours"]))
    jd_ut = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )
    return moon_velocity_dps_at_jd(jd_ut)


# ── T_MD^birth / birth-balance scale factor (module docstring #7) ──────────

def full_lord_period_days(
    chart_id: str, system_id: str, lord_identity: str, conn: Any,
) -> tuple[float, str]:
    """The full (untruncated) period length, in days, of `lord_identity`'s
    level-1 (MD) period in this system -- sourced entirely from
    `chart_dashas`, never a hardcoded classical table (SS_N.5).

    Method: among all level_n=1 rows for (chart_id, system_id) whose
    lord identity (lord_graha, or lord_sign for sign-based systems) equals
    `lord_identity`, take the MAXIMUM `duration_days`. The very first
    occurrence in the whole ladder is birth-balance-truncated (shorter than
    the lord's true full length); any LATER occurrence of the same lord is
    a full, untruncated cycle, so max() recovers the true full length
    whenever at least one later occurrence exists in the computed horizon.
    If the lord never recurs within the horizon, the single occurrence's
    own (truncated) duration is returned as the best available estimate,
    flagged via the returned source string.
    """
    rows = _chart_dashas_level1_rows(chart_id, system_id, conn)
    matching = [
        r for r in rows
        if (r.get("lord_graha") == lord_identity) or (r.get("lord_sign") == lord_identity)
    ]
    if not matching:
        raise RuntimeError(
            f"no level-1 chart_dashas rows for chart {chart_id!r} system "
            f"{system_id!r} lord {lord_identity!r}"
        )
    durations = [float(r["duration_days"]) for r in matching]
    full_days = max(durations)
    source = (
        "full_cycle_recurrence" if len(matching) > 1 else "single_occurrence_approx"
    )
    return full_days, source


# ── Boundary computation + write (§4.2) ─────────────────────────────────────

@dataclass(frozen=True)
class BoundaryRow:
    system_id: str
    level: str
    lord: str
    parent_lords: list[str]
    t_boundary: float
    period_days: float
    sigma_t_days: float
    interval_lo: float
    interval_hi: float
    precision_state: str
    dominant_uncertainty_source: str
    sigma_t_source: str
    source_pk: str


def _system_sigma_t(
    chart_id: str,
    system_id: str,
    conn: Any,
    *,
    birth_params: dict,
    ayanamsha_id: str,
    sigma_t_birth_days: float,
    sigma_t_source: str,
) -> tuple[float, str]:
    """sigma_t (days), IDENTICAL at every level of this system's ladder
    (§4.2's rigid-grid-translation property). Returns (sigma_t_days,
    dominant_uncertainty_source)."""
    if system_id in BIRTH_TIME_ONLY_SYSTEMS:
        sigma_t, dominant = U.sigma_t_birth_time_only(sigma_t_birth_days)
        return sigma_t, dominant

    l_span = FRACTIONAL_ARC_SPAN_DEG[system_id]
    v_moon = moon_velocity_dps_at_birth(birth_params)
    sigma_a = U.fetch_sigma_a_degrees(chart_id, conn).sigma_a_deg

    rows = _chart_dashas_level1_rows(chart_id, system_id, conn)
    if not rows:
        raise RuntimeError(
            f"no level-1 chart_dashas rows for chart {chart_id!r} system {system_id!r}"
        )
    birth_lord = rows[0].get("lord_graha") or rows[0].get("lord_sign")
    t_balance_days, _ = full_lord_period_days(chart_id, system_id, birth_lord, conn)

    result = U.propagate_fractional_arc_sigma_t(
        v_moon_dps=v_moon,
        sigma_t_birth_days=sigma_t_birth_days,
        sigma_a_deg=sigma_a,
        t_balance_days=t_balance_days,
        l_span_deg=l_span,
    )
    return result.sigma_t_days, result.dominant_uncertainty_source


def compute_boundaries_for_system(
    chart_id: str,
    system_id: str,
    conn: Any,
    *,
    birth_params: dict,
    ayanamsha_id: str = DEFAULT_AYANAMSHA_ID,
) -> list[BoundaryRow]:
    """Compute every boundary row for one system: one row per level-1..4
    chart_dashas row present (PrD/level-5 is never computed by this
    product's L1 writer -- honest absence, never fabricated), with the
    exact §4.2 sigma_t + precision-support evaluation. sigma_t is
    identical across all levels of the system (computed once, reused)."""
    sigma_t_birth_days, sigma_t_source = U.fetch_sigma_t_days(chart_id, conn)
    sigma_t_days, dominant_source = _system_sigma_t(
        chart_id, system_id, conn,
        birth_params=birth_params, ayanamsha_id=ayanamsha_id,
        sigma_t_birth_days=sigma_t_birth_days, sigma_t_source=sigma_t_source,
    )

    all_rows = conn.execute(
        """
        SELECT dasha_row_id, level_n, lord_graha, lord_sign, parent_row_id,
               start_iso, duration_days
        FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND level_n BETWEEN 1 AND 4
        ORDER BY level_n ASC, start_iso ASC
        """,
        [chart_id, system_id],
    ).fetchall()
    dict_rows = _rows_as_dicts(
        all_rows,
        ["dasha_row_id", "level_n", "lord_graha", "lord_sign", "parent_row_id", "start_iso", "duration_days"],
    )
    by_id = {r["dasha_row_id"]: r for r in dict_rows}

    def _ancestor_lords(row: dict) -> list[str]:
        chain: list[str] = []
        parent_id = row.get("parent_row_id")
        while parent_id is not None and parent_id in by_id:
            parent = by_id[parent_id]
            lord = parent.get("lord_graha") or parent.get("lord_sign")
            chain.append(lord)
            parent_id = parent.get("parent_row_id")
        chain.reverse()  # outermost first
        return chain

    out: list[BoundaryRow] = []
    for r in dict_rows:
        level = LEVEL_TEXT_BY_N[int(r["level_n"])]
        lord = r.get("lord_graha") or r.get("lord_sign")
        t_boundary = to_t_days(r["start_iso"])
        period_days = float(r["duration_days"])
        support = U.evaluate_precision_support(t_boundary, sigma_t_days, period_days)
        out.append(
            BoundaryRow(
                system_id=system_id,
                level=level,
                lord=lord,
                parent_lords=_ancestor_lords(r),
                t_boundary=t_boundary,
                period_days=period_days,
                sigma_t_days=sigma_t_days,
                interval_lo=support.interval_lo,
                interval_hi=support.interval_hi,
                precision_state=support.precision_state,
                dominant_uncertainty_source=dominant_source,
                sigma_t_source=sigma_t_source,
                source_pk=r["dasha_row_id"],
            )
        )
    return out


def write_boundary_rows(chart_id: str, system_id: str, rows: list[BoundaryRow], conn: Any) -> int:
    """Idempotent per-chart write to `kala_field_boundaries`: delete-then-
    insert scoped to (chart_id x system_id) — §N.3."""
    conn.execute(
        "DELETE FROM kala_field_boundaries WHERE chart_id = %s AND system_id = %s",
        [chart_id, system_id],
    )
    for r in rows:
        conn.execute(
            """
            INSERT INTO kala_field_boundaries
                (chart_id, system_id, level, lord, parent_lords, t_boundary,
                 period_days, sigma_t_days, interval_lo, interval_hi,
                 precision_state, dominant_uncertainty_source, sigma_t_source,
                 source_table, source_pk)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'chart_dashas', %s)
            """,
            [
                chart_id, r.system_id, r.level, r.lord, r.parent_lords, r.t_boundary,
                r.period_days, r.sigma_t_days, r.interval_lo, r.interval_hi,
                r.precision_state, r.dominant_uncertainty_source, r.sigma_t_source,
                r.source_pk,
            ],
        )
    return len(rows)


def boundary_breakpoints(chart_id: str, conn: Any) -> list[float]:
    """PUBLISHED FUNCTION (Lane B -> Lane C). Every t_boundary whose
    precision_state != 'precision_unsupported', ascending (§4.2)."""
    rows = conn.execute(
        """
        SELECT t_boundary FROM kala_field_boundaries
        WHERE chart_id = %s AND precision_state != 'precision_unsupported'
        ORDER BY t_boundary ASC
        """,
        [chart_id],
    ).fetchall()
    dict_rows = _rows_as_dicts(rows, ["t_boundary"])
    return [float(r["t_boundary"]) for r in dict_rows]


# ── clock_activation: a_{s,e}(t) (§5.1 rule C-3) ────────────────────────────

def lord_stack_at(chart_id: str, system_id: str, t_days: float, conn: Any) -> dict[str, str]:
    """The running lord at each PRECISION-SUPPORTED level of `system_id` at
    `t_days` (Rule C-5: a precision_unsupported level is simply absent).
    Returns {level_text: lord_identity}."""
    at_dt = from_t_days(t_days)

    supported_rows = conn.execute(
        """
        SELECT DISTINCT level FROM kala_field_boundaries
        WHERE chart_id = %s AND system_id = %s AND precision_state != 'precision_unsupported'
        """,
        [chart_id, system_id],
    ).fetchall()
    supported_levels = {r["level"] if isinstance(r, dict) else r[0] for r in supported_rows}

    out: dict[str, str] = {}
    for level, level_n in ((lv, n) for n, lv in LEVEL_TEXT_BY_N.items() if lv in supported_levels):
        row = conn.execute(
            """
            SELECT lord_graha, lord_sign FROM chart_dashas
            WHERE chart_id = %s AND system_id = %s AND level_n = %s
              AND start_iso <= %s AND end_iso > %s
            ORDER BY start_iso DESC LIMIT 1
            """,
            [chart_id, system_id, level_n, at_dt, at_dt],
        ).fetchone()
        if row is None:
            continue
        row_d = row if isinstance(row, dict) else {"lord_graha": row[0], "lord_sign": row[1]}
        lord = row_d.get("lord_graha") or row_d.get("lord_sign")
        if lord is not None:
            out[level] = lord
    return out


def _lord_to_graha(lord_identity: str) -> str:
    """Translate a running-lord identity to a graha id for the promise
    graph's `'graha:<...>'` node convention (module docstring #5): a sign
    name maps through its classical ruler; a graha name passes through."""
    return SIGN_LORDS.get(lord_identity, lord_identity)


def _route_gain_and_sign_for_lord(
    chart_id: str, event_class: str, graha: str, conn: Any,
) -> tuple[float, int]:
    """g_ell and sign_ell for one lord (§5.1 C-3): g = max route_gain over
    routes containing node 'graha:<lord>' for this event_class (0 if
    none); sign = -1 if THAT selected route carries a non-empty
    suppressed_by (the route's delivery is currently obstructed), else +1.
    This builder's literal reading of "sign_ell = +1 if the lord's role in
    that route is supportive, -1 if the route row lists it in
    suppressed_by" -- see module docstring for the exact citation."""
    node_id = f"graha:{graha}"
    rows = conn.execute(
        """
        SELECT route_gain, suppressed_by FROM kala_field_promise_routes
        WHERE chart_id = %s AND event_class = %s AND %s = ANY(path_node_ids)
        """,
        [chart_id, event_class, node_id],
    ).fetchall()
    dict_rows = _rows_as_dicts(rows, ["route_gain", "suppressed_by"])
    if not dict_rows:
        return 0.0, 1
    best = max(dict_rows, key=lambda r: float(r["route_gain"]))
    g = float(best["route_gain"])
    suppressed = best.get("suppressed_by") or []
    sign = -1 if len(suppressed) > 0 else 1
    return g, sign


def clock_activation(chart_id: str, system_id: str, event_class: str, t: float, conn: Any) -> float:
    """PUBLISHED FUNCTION (Lane B -> Lane C). a_{s,e}(t) = exp(A_s * r_{s,e}(t))
    per §5.1 rule C-3. Always > 0 (a stationless neutral value of 1.0 when
    A_s is unavailable or the lord stack is empty at t, e.g. outside any
    computed period -- this is exactly how a system like mudda "outside a
    computed varsha year" naturally reduces to no contribution, without
    needing quality itself to vary with t; see module docstring #9)."""
    clock_row = conn.execute(
        "SELECT quality FROM kala_field_clocks WHERE chart_id = %s AND system_id = %s",
        [chart_id, system_id],
    ).fetchone()
    if clock_row is None:
        return 1.0
    a_s = clock_row["quality"] if isinstance(clock_row, dict) else clock_row[0]
    if a_s is None:
        return 1.0

    stack = lord_stack_at(chart_id, system_id, t, conn)
    total = 0.0
    for level, lord in stack.items():
        depth_weight = LEVEL_DEPTH_WEIGHT[level]
        graha = _lord_to_graha(lord)
        g, sign = _route_gain_and_sign_for_lord(chart_id, event_class, graha, conn)
        total += depth_weight * sign * g

    r = math.tanh(total)
    return math.exp(float(a_s) * r)
