"""
services.ka_kshetra.stage3_clocks — Lane B, Stage 3: dasha-system clocks.

Per KALA_W2_FIELD_DESIGN_v1_0.md §4: Law-1 applicability evaluation per
dasha system (item 12, §4.1) + the boundary-uncertainty writers that
consume `uncertainty.py` (item 24-full, §4.2) + the published functions
Lane C calls (`applicable_systems`, `clock_activation`, `boundary_breakpoints`).

Legacy is untouched (design doc §1 rail 2): this module only reads
`chart_dashas` / `chart_facts` / `brahma_dasha_systems` / `ephemeris`
read-only, and only writes `kala_field_clocks` / `kala_field_boundaries`
(the two tables this lane owns, migration 490).

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

10. `vimshottari_kp` (SHAD-DARSANA W3K Lane 2, gap G-4 of
   `W3K_SUBSTRATE_INVENTORY_v1_0.md` §2; the extension seam
   `KALA_W2_FIELD_DESIGN_v1_0.md` §11.4 designates: "W3K's KP clock joins
   by adding a bg_dasha_systems row and a `q_s` rule (§4.1 step 4), with no
   change to §5.1"). Two things had to be true for KP to join honestly, and
   only one of them is:

   (a) The `q_s` rule EXISTS and is KP-specific -- `_kp_sub_quality` below,
       the Moon's margin to the nearest boundary of the 249-fold KP sub
       division, measured against the chart's OWN ayanamsha spread. The
       boundaries are REFERENCED from the L0 authority table
       `bg_kp_sublord_division` (W3K Lane 1, PR #1039), never re-derived
       here -- §N.5. No L0 table => `not_computed`, never a silent
       re-derivation and never an invented quality.

   (b) KP must be a genuinely DIFFERENT voice in `S_pred(e)`, not the same
       clock counted twice. `hazard.relevance` consumes ONLY the (level,
       lord) pairs `lord_stack_at` reads out of `chart_dashas.lord_graha`.
       So if `vimshottari_kp`'s per-level lord sequence is identical to
       `vimshottari`'s over the field horizon, then r_kp(t) == r_vim(t) for
       every t, and admitting KP to S_pred(e) would raise the SAME clock's
       exponent from w_vim to w_vim + w_kp -- the exact double-count
       `gochara_intensity/permission.py` already refuses one layer down for
       DR-14's plurality sum, and which `W3K_SUBSTRATE_INVENTORY_v1_0.md`
       §4 rules on directly ("KP's sub/sub-sub periods subdivide the SAME
       Vimsottari windows... it is not an independent generator").

   (b) is therefore MEASURED, not assumed: `kp_window_redundancy` below is a
   real detector over this chart's own `chart_dashas` rows, and its verdict
   can genuinely come back either way (§N.8). On the two canonical charts it
   currently comes back REDUNDANT -- verified read-only 2026-08-03 against
   production for chart 482012f1 (lahiri_chitrapaksha): inside the field
   horizon [birth, birth+36525d], 69/69 level-2 and 630/630 level-3
   `vimshottari_kp` rows have an exact `vimshottari` twin (same level, same
   `lord_graha`, both boundaries within 2s; the sub-2s spread is the two
   writers' independent rounding, not a different window). Every untwinned
   row lies OUTSIDE that horizon (pre-birth back-extrapolation to the 1950
   build floor, and the post-2084 tail) and so is outside the field entirely
   (design §5.2's H = 36525 days FROM BIRTH). KP is consequently reported
   `excluded_by_condition` with that measurement as its verbatim reason, and
   `hazard.predictive_systems` drops it from S_pred(e) through its ALREADY
   EXISTING `applicability_state != 'applicable'` clause -- literally "no
   change to §5.1", as §11.4 requires.

   What KP's exclusion here does NOT say: it does not say KP has nothing to
   contribute. It says KP has no independent CLOCK to contribute. KP's
   independence is a judgment-method independence (does the running lord
   signify this house, by the KP significator ladder?), and that voice is
   served at the serving layer from `kp_house_significators` /
   `kp_planet_significations`, not multiplied into lambda as a fourth
   proportional-hazards factor. See `platform-mcp/src/lib/kp_school_voice.ts`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from brahmagyan.graha_vocabulary import norm_graha
from . import uncertainty as U
from .contracts import ClockApplicability

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

#: chart_facts.fact_subject abbreviations for the seven chara-karaka
#: candidates. Values sourced from the graha SSoT
#: (brahmagyan/graha_vocabulary) rather than hardcoded literals —
#: ADHIṢṬHĀNA Lane A2 (found via the full-tree census; not one of the
#: originally-enumerated retirement targets, but the same shape).
GRAHA_TO_FACT_SUBJECT: dict[str, str] = {
    name: norm_graha(name)
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
}

DEFAULT_AYANAMSHA_ID = "lahiri_chitrapaksha"

#: W3K G-4. The KP-variant Vimsottari sub-period system_id already live in
#: `chart_dashas` (`ga_dashas_writer.KP_SYSTEM_ID`), and the classical system
#: whose windows it subdivides.
KP_SYSTEM_ID = "vimshottari_kp"
KP_PARENT_SYSTEM_ID = "vimshottari"

#: The field's own horizon (design §5.2: "H = 36525 days from birth"). The KP
#: window-redundancy detector is scoped to exactly this interval because that is
#: the only interval the field evaluates -- a pre-birth or post-horizon row
#: cannot double-count anything, so counting it either way would be measuring
#: something the question does not ask about.
FIELD_HORIZON_DAYS = 36525.0

#: Boundary tolerance for the KP/Vimsottari window-twin comparison. The two
#: ladders are written by two independent code paths (`ga_dashas_writer`'s
#: classical branch and its KP branch) whose datetime rounding differs by up to
#: one second on the same computed instant; 2s is that rounding band and nothing
#: more. It is NOT a similarity threshold: a genuinely different KP window
#: differs by days-to-years, never by a second.
KP_TWIN_TOLERANCE_SECONDS = 2.0

#: z for the 95% band, matching §4.2's own `z = 1.96`.
Z_95 = 1.96

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
    # vimshottari_kp rides the SAME rigid grid as vimshottari — same Moon-nakṣatra
    # determination, same birth balance, sub-periods that are exact rational
    # fractions of the same parents (§4.2's rigid-grid-translation property). Its
    # σ_t is therefore Vimśottarī's, inherited rather than recomputed.
    KP_SYSTEM_ID: U.NAK_SPAN_DEG,
}

#: Systems with no level-1 (MD) rows of their own, whose birth-balance scale
#: factor is inherited from the parent system whose ladder they subdivide.
#: `vimshottari_kp` is written from level 2 down (`ga_dashas_writer`), so its
#: T_MD^birth is Vimśottarī's own — read from the parent, never re-derived.
PARENT_LADDER_SYSTEM: dict[str, str] = {KP_SYSTEM_ID: KP_PARENT_SYSTEM_ID}


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
    # W3K G-4. competence_class='fruition' is not a filler pick: KP's sub-periods
    # ARE Vimsottari's, so KP shares Vimsottari's class by construction -- and
    # `writer.py`'s §6.4-type-1 insight counts DISTINCT competence_classes
    # precisely so that "two systems sharing a class are one voice". Declaring KP
    # a NEW class would have manufactured a second voice out of one clock in that
    # counter too. is_predictive stays True here because C-4's structural
    # exclusion is about `life_stage` context bands and KP is not one; KP's
    # actual non-participation is decided by the MEASURED redundancy verdict at
    # jurisdiction (module docstring #10), not by a hardcoded flag.
    KP_SYSTEM_ID:   SystemMeta(competence_class="fruition", seniority_rank=8, is_predictive=True),
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
#
# ClockApplicability is defined in contracts.py (the shared cross-lane surface,
# owned by nobody) and imported above — NOT redefined here. Merge-train note
# (2026-07-30): this module originally carried its own copy of the same shape;
# consolidated to one definition so `isinstance`/type-identity checks agree
# regardless of which module a caller imports it from. Field usage below is
# 100% keyword-argument construction, so the consolidation changes nothing at
# any call site.


# ── W3K G-4: the KP window-redundancy detector (module docstring #10) ───────

@dataclass(frozen=True)
class KpWindowRedundancy:
    """The measured answer to "is `vimshottari_kp` a second clock, or the same
    clock relabelled?" — for ONE chart, inside the field's own horizon.

    `is_redundant` is True iff EVERY in-horizon KP row has a `vimshottari` twin
    at the same level with the same `lord_graha` and both boundaries within
    `tolerance_seconds`. One untwinned row is enough to make it False: that row
    is an instant at which the two systems' lord stacks genuinely differ, which
    is all it takes for KP to carry information Vimsottari does not.
    """
    rows_in_horizon: int
    twinned_rows: int
    is_redundant: bool
    tolerance_seconds: float
    horizon_start: datetime
    horizon_end: datetime
    levels_compared: tuple[int, ...]

    @property
    def untwinned_rows(self) -> int:
        return self.rows_in_horizon - self.twinned_rows

    def basis(self) -> str:
        levels = "/".join(f"L{n}" for n in self.levels_compared) or "none"
        return (
            f"kp_window_twin_check[{levels}] "
            f"twinned={self.twinned_rows}/{self.rows_in_horizon} "
            f"tol={self.tolerance_seconds:g}s "
            f"horizon={self.horizon_start.date().isoformat()}..{self.horizon_end.date().isoformat()}"
        )


def kp_window_redundancy(
    chart_id: str,
    conn: Any,
    *,
    birth_dt: datetime,
    ayanamsha_id: str = DEFAULT_AYANAMSHA_ID,
    tolerance_seconds: float = KP_TWIN_TOLERANCE_SECONDS,
) -> KpWindowRedundancy:
    """Measure whether `vimshottari_kp` adds a distinct lord stack over
    `vimshottari` for this chart, inside the field horizon.

    Read-only over `chart_dashas` alone. Compares exactly the quantity
    `hazard.relevance` consumes — (level, `lord_graha`) at an instant — so a
    "redundant" verdict here means, precisely and only, that r_kp(t) can never
    differ from r_vim(t) inside the horizon.
    """
    if birth_dt.tzinfo is None:
        birth_dt = birth_dt.replace(tzinfo=timezone.utc)
    horizon_end = birth_dt + timedelta(days=FIELD_HORIZON_DAYS)

    rows = conn.execute(
        """
        SELECT kp.level_n AS level_n,
               (EXISTS (
                   SELECT 1 FROM chart_dashas v
                    WHERE v.chart_id = kp.chart_id
                      AND v.ayanamsha_id = kp.ayanamsha_id
                      AND v.system_id = %s
                      AND v.level_n = kp.level_n
                      AND v.lord_graha IS NOT DISTINCT FROM kp.lord_graha
                      AND abs(extract(epoch FROM (v.start_iso - kp.start_iso))) <= %s
                      AND abs(extract(epoch FROM (v.end_iso   - kp.end_iso)))   <= %s
               )) AS has_twin
          FROM chart_dashas kp
         WHERE kp.chart_id = %s
           AND kp.ayanamsha_id = %s
           AND kp.system_id = %s
           AND kp.start_iso >= %s
           AND kp.end_iso   <= %s
        """,
        [
            KP_PARENT_SYSTEM_ID, tolerance_seconds, tolerance_seconds,
            chart_id, ayanamsha_id, KP_SYSTEM_ID, birth_dt, horizon_end,
        ],
    ).fetchall()
    dict_rows = _rows_as_dicts(rows, ["level_n", "has_twin"])

    total = len(dict_rows)
    twinned = sum(1 for r in dict_rows if bool(r["has_twin"]))
    levels = tuple(sorted({int(r["level_n"]) for r in dict_rows}))

    return KpWindowRedundancy(
        rows_in_horizon=total,
        twinned_rows=twinned,
        # Zero in-horizon rows is NOT redundancy — it is absence, and §4.1 step 2
        # is explicit that absent is never treated as excluded. The presence check
        # in `evaluate_applicability` handles that case on its own terms.
        is_redundant=total > 0 and twinned == total,
        tolerance_seconds=tolerance_seconds,
        horizon_start=birth_dt,
        horizon_end=horizon_end,
        levels_compared=levels,
    )


def _evaluate_jurisdiction(
    system_id: str,
    chart_id: str | None = None,
    conn: Any = None,
    *,
    birth_dt: datetime | None = None,
    ayanamsha_id: str = DEFAULT_AYANAMSHA_ID,
) -> tuple[str, str | None]:
    """Step 1 (§4.1), returning `(applicability_state, reason)`.

    For the seven systems this builder originally covered: see module docstring
    #4 — none has a real, machine-evaluable `entry_condition` sourced anywhere in
    this corpus, so all seven pass jurisdiction unconditionally, exactly as
    before (`('applicable', None)`).

    `vimshottari_kp` is the first system with a real, machine-evaluable
    condition, and it is evaluated here rather than bypassing this step (module
    docstring #4's own instruction: "A future system with a real, citable,
    machine-evaluable condition should extend `_evaluate_jurisdiction`, never
    bypass this module's honesty discipline"). The condition is the
    window-redundancy measurement of docstring #10.
    """
    if system_id != KP_SYSTEM_ID:
        return "applicable", None

    if birth_dt is None or conn is None or chart_id is None:
        # §N.8: no detector ran, so there is no verdict. Reporting `applicable`
        # here would admit KP to S_pred(e) on an unmeasured assumption — the
        # precise failure mode this module refuses. `not_computed` is the honest
        # state, and it is NOT 'excluded_by_condition' either: nothing was
        # decided against KP, the question was simply never put.
        return "not_computed", (
            "KP window-redundancy vs Vimsottari is undecidable without the chart's "
            "birth instant (the field horizon's own anchor, design §5.2) — reported "
            "not_computed rather than admitted to S_pred(e) unmeasured"
        )

    verdict = kp_window_redundancy(chart_id, conn, birth_dt=birth_dt, ayanamsha_id=ayanamsha_id)
    if verdict.rows_in_horizon == 0:
        # Fall through to the presence check, which owns the absence vocabulary.
        return "applicable", None
    if not verdict.is_redundant:
        return "applicable", None

    return "excluded_by_condition", (
        "vimshottari_kp's period ladder is boundary-identical to vimshottari's inside "
        f"the field horizon ({verdict.basis()}): every in-horizon KP row has a "
        "vimshottari twin at the same level with the same lord, so its running lord "
        "stack — the only input hazard.relevance reads — can never differ. Admitting it "
        "to S_pred(e) would multiply one clock's factor twice (w_vim + w_kp on the same "
        "exponent), the same double-count gochara_intensity/permission.py refuses for "
        "DR-14's plurality sum. KP's independence is a JUDGMENT-method independence "
        "(W3K_SUBSTRATE_INVENTORY_v1_0.md §4) and is served as a school voice, not as a "
        "hazard factor."
    )


# ── W3K G-4: the KP q_s rule (§4.1 step 4, per design §11.4's seam) ─────────

def _fetch_kp_sub_boundaries(conn: Any) -> list[float]:
    """The 249-fold KP sub-division boundaries, REFERENCED from the L0 authority
    `bg_kp_sublord_division` (§N.5) — never re-derived here.

    Deliberately reads the table through this module's own `conn.execute` idiom
    rather than calling `brahmagyan.l0_kp_sublord_division.load_divisions`, which
    speaks the psycopg `conn.cursor(row_factory=...)` protocol this module does
    not use anywhere else. Same table, same authority, same values — only the
    cursor idiom differs. Returns [] when the table is absent or unbuilt; the
    caller renders that as `not_computed`, never as a fallback re-derivation.
    """
    try:
        rows = conn.execute(
            """
            SELECT start_longitude_deg
              FROM bg_kp_sublord_division
             ORDER BY division_index
            """,
        ).fetchall()
    except Exception:  # noqa: BLE001 — table absent (pre-Lane-1 chart/db) is a data
        # state, not a crash: reported honestly as "no boundaries" by the caller.
        return []
    dict_rows = _rows_as_dicts(rows, ["start_longitude_deg"])
    return [float(r["start_longitude_deg"]) % 360.0 for r in dict_rows
            if r["start_longitude_deg"] is not None]


def kp_sub_quality(
    moon_longitude_deg: float, boundaries: list[float], sigma_a_deg: float,
) -> tuple[float, float]:
    """`vimshottari_kp`'s q_s: the KP sub-lord determination's robustness.

    Returns `(d_sub, q)` where `d_sub` is the Moon's angular distance to the
    nearest KP sub boundary and `q = clamp01(d_sub / (z · σ_A))`.

    Why this shape, and why it is not an invented constant. §4.1 step 4 defines
    q_s as "the system's own determination-robustness"; vimshottari's rule is the
    Moon's margin to its determining grid (nakṣatra), kalachakra's is the same
    against a finer grid (pāda). KP's determining grid is finer again — the 249
    sub division — so the same rule against KP's own grid is the direct
    continuation, and §11.4 explicitly authorises adding it ("W3K's KP clock
    joins by adding ... a `q_s` rule (§4.1 step 4)").

    The tolerance is the one place a builder could have invented a number, so it
    is not invented: it is `z · σ_A`, both terms already defined by §4.2 (`z =
    1.96`; σ_A the ayanāṃśa spread across the five pinned ayanāṃśas at this
    chart's own epoch). That is also the empirically right band for THIS grid —
    `05_TEMPORAL_ENGINES/kp/CROSSCHECK_v1_0.md` §2 records that the KP sub-lord
    engine's only non-exact comparisons against the FORENSIC fixture were
    boundary flips attributed to exactly the standing ayanāṃśa-precision band
    (GAP.09). A KP sub whose margin exceeds that band is determinable; one inside
    it is the case the crosscheck actually observed flipping.
    """
    if not boundaries:
        raise ValueError("kp_sub_quality requires the L0 KP sub-division boundaries; got none")
    if not (sigma_a_deg > 0.0):
        raise ValueError(f"kp_sub_quality requires sigma_a_deg > 0; got {sigma_a_deg!r}")

    lon = moon_longitude_deg % 360.0
    d_sub = min(
        min(abs(lon - b), 360.0 - abs(lon - b))
        for b in boundaries
    )
    return d_sub, _clamp01(d_sub / (Z_95 * sigma_a_deg))


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

    if system_id == KP_SYSTEM_ID:
        # Only reachable when the redundancy detector found KP to be a genuinely
        # distinct clock for this chart (jurisdiction passed) — see docstring #10.
        boundaries = _fetch_kp_sub_boundaries(conn)
        if not boundaries:
            return None, None  # rendered as not_computed by the caller
        sigma_a = U.fetch_sigma_a_degrees(chart_id, conn).sigma_a_deg
        if not (sigma_a > 0.0):
            return None, None
        moon_lon = fetch_moon_longitude_deg(chart_id, conn, ayanamsha_id)
        d_sub, q = kp_sub_quality(moon_lon, boundaries, sigma_a)
        return q, (
            f"kp_sub_margin={d_sub:.4f}deg;sigma_a={sigma_a:.4f}deg;z={Z_95};"
            f"n_divisions={len(boundaries)}"
        )

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
    birth_dt: datetime | None = None,
) -> ClockApplicability:
    """The full §4.1 algorithm for one (chart, system). `reference_dt`
    defaults to now (UTC) -- see module docstring #9 for why mudda's
    "evaluated t" is read as a representative build-time instant.

    `birth_dt` anchors the field horizon (design §5.2's H = 36525 days FROM
    BIRTH) and is read by exactly one system's jurisdiction step today,
    `vimshottari_kp`'s (module docstring #10). Omitting it leaves that system
    `not_computed` — never silently `applicable` — and changes nothing for the
    other seven."""
    meta = SYSTEM_META.get(system_id)
    if meta is None:
        raise ValueError(f"unknown system_id for Law-1 applicability: {system_id!r}")

    ref_dt = reference_dt or datetime.now(timezone.utc)

    jurisdiction_state, exclusion_reason = _evaluate_jurisdiction(
        system_id, chart_id, conn, birth_dt=birth_dt, ayanamsha_id=ayanamsha_id,
    )
    if jurisdiction_state != "applicable":
        return ClockApplicability(
            system_id=system_id,
            applicability_state=jurisdiction_state,
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
    birth_dt: datetime | None = None,
) -> list[ClockApplicability]:
    """PUBLISHED FUNCTION (Lane B -> Lane C). Evaluates Law-1 applicability
    for every daśā system this product computes into `chart_dashas`, in a
    stable (sorted by system_id) order.

    `birth_dt` (optional) anchors the field horizon for `vimshottari_kp`'s
    jurisdiction step — see `evaluate_applicability`."""
    ref_dt = reference_dt or datetime.now(timezone.utc)
    return [
        evaluate_applicability(
            chart_id, sid, conn,
            ayanamsha_id=ayanamsha_id, reference_dt=ref_dt, birth_dt=birth_dt,
        )
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

    # A subdividing system (vimshottari_kp) has no level-1 rows of its own; its
    # birth-balance scale factor is the parent ladder's, inherited not recomputed.
    ladder_system = PARENT_LADDER_SYSTEM.get(system_id, system_id)
    rows = _chart_dashas_level1_rows(chart_id, ladder_system, conn)
    if not rows:
        raise RuntimeError(
            f"no level-1 chart_dashas rows for chart {chart_id!r} system {ladder_system!r}"
            + (f" (the parent ladder of {system_id!r})" if ladder_system != system_id else "")
        )
    birth_lord = rows[0].get("lord_graha") or rows[0].get("lord_sign")
    t_balance_days, _ = full_lord_period_days(chart_id, ladder_system, birth_lord, conn)

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
