"""
services.ka_kshetra.uncertainty — Lane B, item 24-full: the W2 uncertainty
budget and interval-propagation machinery.

Per KALA_W2_FIELD_DESIGN_v1_0.md §4.2. This module is pure math (no DB
access) plus the two data-access helpers that assemble its two raw inputs
(sigma_T, sigma_A) from the L1/L4 tables that hold them. Everything here
supersedes the W1-lite placeholder (`kala_uncertainty.ts` /
`sukshma_boundary_uncertainty`) for W2's internal field computation only;
the W1-lite serving field is untouched until a later wave upgrades it
(design doc scope note).

The two uncertainty sources (§4.2):
  sigma_T — birth-time uncertainty, in days. Read from the rectification
            posterior (`phala_rectification`) if present; else the
            documented default of 120 seconds, carried NEVER-silently via
            `sigma_t_source`.
  sigma_A — ayanamsha uncertainty, in degrees. The range across the five
            pinned ayanamshas' Moon longitude at the birth epoch, treated
            as uniform: sigma_A = range / sqrt(12).

Propagation (the exact derivation, §4.2): for a nakshatra/pada-fraction
-driven dasha system (Moon-longitude-driven: vimshottari, yogini,
ashtottari, kalachakra),

    sigma_lambda = sqrt((v_Moon * sigma_T)^2 + sigma_A^2)          [deg]
    sigma_f      = sigma_lambda / L_span                            [dimensionless]
    sigma_t      = sqrt((T_balance * sigma_f)^2 + sigma_T^2)        [days]

identical at every level of that system's ladder (design doc's "whole
ladder translates by a single delta t" property — sub-periods are exact
rational fractions of their parent and inherit the same translation).

For systems whose balance does NOT depend on a fractional arc (naisargika,
mudda per the design doc explicitly; chara_karaka by this builder's
documented extension — see `stage3_clocks.py`'s module docstring for why),
sigma_t = sigma_T alone.

The precision-support rule (§4.2) turns a (t_boundary, sigma_t, period)
triple into an honest serving posture: instant / interval /
precision_unsupported — never a claim at a precision the input
uncertainty cannot support.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

# ── Constants (§4.2, exact) ────────────────────────────────────────────────

Z_95 = 1.96

#: Default birth-time sigma when no rectification posterior exists: 120
#: seconds, expressed in days. Never applied silently — every caller must
#: carry `sigma_t_source = 'default_120s_assumption'` alongside it.
DEFAULT_SIGMA_T_DAYS = 120.0 / 86400.0  # 1.388...e-3 days

#: The five ayanamshas this product pins (matches
#: ga_dashas_writer.AYANAMSHAS / ga_ayurdaya_writer.CANONICAL_AYANAMSHAS —
#: the DB-facing canonical ids, not pyjhora's internal short ids).
AYANAMSHA_IDS = (
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
)

NAK_SPAN_DEG = 360.0 / 27.0          # 13.333... — one nakshatra
PADA_SPAN_DEG = NAK_SPAN_DEG / 4.0   # 3.333... — one pada
SIGN_SPAN_DEG = 30.0                 # one rashi


# ── sigma_A: ayanamsha spread ───────────────────────────────────────────────

def wrap180(x: float) -> float:
    """Wrap an angle (degrees) into (-180, 180], per stage 0's convention."""
    return ((x + 180.0) % 360.0) - 180.0


def unwrap_longitudes(values: dict[str, float]) -> dict[str, float]:
    """Fold a small cluster of longitudes (degrees) that are known to be
    close together (e.g. the same body's position under 5 ayanamshas that
    differ from each other by at most a few degrees) so a value just below
    360 and a value just above 0 are not treated as ~360 degrees apart.

    Anchors on the first item (dict insertion order) and folds every other
    value to within 180 degrees of that anchor — the same +-180 test stage
    0 uses for kinematics unwrapping (never based on any "is_retrograde"style
    flag, which does not apply here anyway).
    """
    items = list(values.items())
    if not items:
        return {}
    anchor_key, anchor_val = items[0]
    out: dict[str, float] = {anchor_key: anchor_val}
    for key, val in items[1:]:
        delta = wrap180(val - anchor_val)
        out[key] = anchor_val + delta
    return out


@dataclass(frozen=True)
class SigmaAResult:
    sigma_a_deg: float
    range_deg: float
    longitudes_unwrapped: dict[str, float]
    n_ayanamshas: int


def compute_sigma_a_degrees(longitudes_by_ayanamsha: dict[str, float]) -> SigmaAResult:
    """sigma_A = range / sqrt(12), the uniform-distribution treatment of the
    ayanamsha spread (§4.2). `longitudes_by_ayanamsha` is the same body's
    (Moon's) sidereal longitude in degrees under each of the pinned
    ayanamshas at the birth epoch.

    Raises ValueError on fewer than 2 ayanamshas (a range needs at least 2
    points) — this is a hard precondition failure, not an honest-empty
    state, since the five ayanamshas are a fixed, always-available L1
    computation for any built chart.
    """
    if len(longitudes_by_ayanamsha) < 2:
        raise ValueError(
            "compute_sigma_a_degrees requires >= 2 ayanamsha longitudes, "
            f"got {len(longitudes_by_ayanamsha)}"
        )
    unwrapped = unwrap_longitudes(longitudes_by_ayanamsha)
    values = list(unwrapped.values())
    range_deg = max(values) - min(values)
    sigma_a = range_deg / math.sqrt(12.0)
    return SigmaAResult(
        sigma_a_deg=sigma_a,
        range_deg=range_deg,
        longitudes_unwrapped=unwrapped,
        n_ayanamshas=len(unwrapped),
    )


# ── sigma_T: birth-time uncertainty ─────────────────────────────────────────

@dataclass(frozen=True)
class RectificationCandidate:
    offset_minutes: int
    lel_fit_score: float | None
    lagna_stable: bool


def compute_sigma_t_days(
    candidates: Iterable[RectificationCandidate],
) -> tuple[float, str]:
    """Derive sigma_T (days) from a `phala_rectification` posterior if one
    usable exists, else the documented default.

    Builder's documented aggregation (the design doc says only "read from
    the rectification posterior if present" without giving an exact
    aggregation formula, so this is this builder's choice, stated plainly):
    the LEL-fit-score-weighted standard deviation of `offset_minutes`
    (converted to days) across candidates that are lagna-stable and carry a
    positive fit score. Fewer than 2 such candidates cannot support a
    spread estimate, so the default applies. A degenerate zero-spread
    posterior (e.g. exactly one distinct offset value, or all candidates
    landing on the same minute) is floored at the instrumental default
    rather than claiming zero birth-time uncertainty.

    Returns (sigma_t_days, sigma_t_source).
    """
    usable = [
        c for c in candidates
        if c.lagna_stable and c.lel_fit_score is not None and c.lel_fit_score > 0
    ]
    if len(usable) < 2:
        return DEFAULT_SIGMA_T_DAYS, "default_120s_assumption"

    weights = [c.lel_fit_score for c in usable]
    values_days = [c.offset_minutes / 1440.0 for c in usable]
    total_w = sum(weights)
    mean = sum(w * v for w, v in zip(weights, values_days)) / total_w
    var = sum(w * (v - mean) ** 2 for w, v in zip(weights, values_days)) / total_w
    sigma = math.sqrt(var)
    sigma = max(sigma, DEFAULT_SIGMA_T_DAYS)
    return sigma, "rectification_posterior_weighted_std"


def fetch_sigma_t_days(chart_id: str, conn: Any) -> tuple[float, str]:
    """DB-facing wrapper: read `phala_rectification` rows for this chart and
    derive sigma_T. See `compute_sigma_t_days` for the aggregation."""
    rows = conn.execute(
        """
        SELECT offset_minutes, lel_fit_score, lagna_stable
        FROM phala_rectification
        WHERE chart_id = %s
        """,
        [chart_id],
    ).fetchall()
    cols = ["offset_minutes", "lel_fit_score", "lagna_stable"]
    dict_rows = [dict(zip(cols, r)) if not isinstance(r, dict) else r for r in rows]
    candidates = [
        RectificationCandidate(
            offset_minutes=int(r["offset_minutes"]),
            lel_fit_score=(float(r["lel_fit_score"]) if r["lel_fit_score"] is not None else None),
            lagna_stable=bool(r["lagna_stable"]),
        )
        for r in dict_rows
    ]
    return compute_sigma_t_days(candidates)


def fetch_sigma_a_degrees(chart_id: str, conn: Any, fact_subject: str = "MOON") -> SigmaAResult:
    """DB-facing wrapper: read the Moon's `longitude_sidereal` chart_facts
    row for each of the five pinned ayanamshas and derive sigma_A."""
    rows = conn.execute(
        """
        SELECT ayanamsha_id, fact_value_num
        FROM chart_facts
        WHERE chart_id = %s
          AND fact_category = 'graha_position'
          AND fact_subject = %s
          AND fact_key = 'longitude_sidereal'
          AND ayanamsha_id = ANY(%s)
        """,
        [chart_id, fact_subject, list(AYANAMSHA_IDS)],
    ).fetchall()
    cols = ["ayanamsha_id", "fact_value_num"]
    dict_rows = [dict(zip(cols, r)) if not isinstance(r, dict) else r for r in rows]
    longitudes = {
        r["ayanamsha_id"]: float(r["fact_value_num"])
        for r in dict_rows
        if r["fact_value_num"] is not None
    }
    return compute_sigma_a_degrees(longitudes)


# ── Propagation into a fractional-arc-driven dasha ladder ──────────────────

@dataclass(frozen=True)
class FractionalArcPropagation:
    sigma_lambda_deg: float
    sigma_f: float
    sigma_t_days: float
    dominant_uncertainty_source: str  # 'birth_time' | 'ayanamsha'


def propagate_fractional_arc_sigma_t(
    v_moon_dps: float,
    sigma_t_birth_days: float,
    sigma_a_deg: float,
    t_balance_days: float,
    l_span_deg: float = NAK_SPAN_DEG,
) -> FractionalArcPropagation:
    """The exact §4.2 derivation for a Moon-position-driven dasha ladder
    (vimshottari, yogini, ashtottari at nakshatra grain; kalachakra at pada
    grain via `l_span_deg=PADA_SPAN_DEG`). `t_balance_days` is
    "T_MD^birth" — the full (untruncated) period length of the birth
    epoch's ruling lord; see `stage3_clocks.py::full_lord_period_days` for
    how this builder sources it (data-driven from chart_dashas, never a
    hardcoded classical table, per SS_N.5).

    sigma_t_days is IDENTICAL at every level of the ladder (the design
    doc's rigid-grid-translation property) — callers compute this once per
    (chart, system) and reuse it for every boundary of that system.
    """
    if v_moon_dps == 0:
        raise ValueError("v_moon_dps must be nonzero (a stationary Moon is not physical)")
    if l_span_deg <= 0:
        raise ValueError("l_span_deg must be positive")

    sigma_lambda = math.sqrt((v_moon_dps * sigma_t_birth_days) ** 2 + sigma_a_deg ** 2)
    sigma_f = sigma_lambda / l_span_deg
    sigma_t = math.sqrt((t_balance_days * sigma_f) ** 2 + sigma_t_birth_days ** 2)

    birth_time_term_sq = (
        (t_balance_days * (v_moon_dps * sigma_t_birth_days / l_span_deg)) ** 2
        + sigma_t_birth_days ** 2
    )
    ayanamsha_term_sq = (t_balance_days * (sigma_a_deg / l_span_deg)) ** 2
    dominant = "birth_time" if birth_time_term_sq > ayanamsha_term_sq else "ayanamsha"

    return FractionalArcPropagation(
        sigma_lambda_deg=sigma_lambda,
        sigma_f=sigma_f,
        sigma_t_days=sigma_t,
        dominant_uncertainty_source=dominant,
    )


def sigma_t_birth_time_only(sigma_t_birth_days: float) -> tuple[float, str]:
    """The degenerate case (§4.2): "where a system's balance does not depend
    on a fractional arc (e.g. naisargika, mudda), sigma_t = sigma_T alone."
    dominant_uncertainty_source is trivially 'birth_time' — there is no
    ayanamsha term in this branch at all."""
    return sigma_t_birth_days, "birth_time"


# ── The precision-support rule (§4.2) ───────────────────────────────────────

@dataclass(frozen=True)
class PrecisionSupport:
    interval_lo: float
    interval_hi: float
    width_days: float
    precision_state: str  # 'instant' | 'interval' | 'precision_unsupported'


def evaluate_precision_support(
    t_boundary_days: float,
    sigma_t_days: float,
    period_days: float,
    z: float = Z_95,
) -> PrecisionSupport:
    """The exact §4.2 precision-support rule:

        interval = [t_b - z*sigma_t, t_b + z*sigma_t], width = 2*z*sigma_t
        serve_as_instant           iff width <= 0.10 * P
        serve_as_interval          iff 0.10*P < width <= 1.00 * P
        precision_unsupported      iff width > P
    """
    if sigma_t_days < 0:
        raise ValueError("sigma_t_days must be >= 0")
    if period_days <= 0:
        raise ValueError("period_days must be positive")

    half_width = z * sigma_t_days
    width = 2.0 * half_width
    lo = t_boundary_days - half_width
    hi = t_boundary_days + half_width

    if width <= 0.10 * period_days:
        state = "instant"
    elif width <= 1.00 * period_days:
        state = "interval"
    else:
        state = "precision_unsupported"

    return PrecisionSupport(interval_lo=lo, interval_hi=hi, width_days=width, precision_state=state)
