"""
W2G V3 — spline accuracy audit near stations and Moon perigee.

Design §6 V3: "spline accuracy audit near stations + Moon perigee (max
interpolation error vs one-off swe spot-checks; sets the root-find
tolerance)." Design §2.1 states the target: "Spline interpolation recovers
any timestamp's position to arc-minute accuracy incl. the Moon (validate
near stations, §6.V3)."

This module is the real thing, not a description of one: it fits cubic
splines over ACTUAL `ephemeris_daily` rows and compares off-grid evaluations
against direct `swisseph` calls at the same instants, in the three regimes
the design names.

TWO GRID FACTS THAT ARE LOAD-BEARING, both read out of the builder rather
than assumed (CLAUDE.md §N.7 item 1 — restate a referenced fact, never
re-derive it):

  1. KNOTS SIT AT NOON UT, not midnight. `brahmagyan.l0_ephemeris` computes
     every row at `swe.julday(y, m, d, 12.0)`. A spline that places date D's
     knot at midnight is wrong by half a day — an error of ~6.6° for the
     Moon, which would dwarf everything this validation measures. The knot
     abscissa here is therefore noon-UT Julian day, taken from the same
     `swe.julday(..., 12.0)` call the builder used.

  2. STORED LONGITUDE IS TROPICAL and ROUNDED TO 6 DECIMALS (~0.013
     arcsec). That quantization is a floor on any achievable accuracy and is
     reported so the measured error is never mistaken for pure spline error.

WRAP HANDLING: longitude is an angle on [0, 360). A naive spline across the
360→0 wrap produces a ~360° excursion. Longitudes are unwrapped to a
monotone real sequence before fitting and re-wrapped after evaluation.

ANGULAR DIFFERENCE is computed on the circle (shortest arc), so a comparison
straddling the wrap reports the true small error, not ~360°.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Sequence

from ._db import QueryFn, table_exists
from .types import FAIL, INDETERMINATE, PASS, ValidationResult

TABLE = "ephemeris_daily"
AYANAMSHA_ID = "tropical"

ARCSEC_PER_DEG = 3600.0
ARCMIN_ARCSEC = 60.0

# Design §2.1's stated target: arc-minute accuracy, including the Moon.
ACCURACY_TARGET_ARCSEC = ARCMIN_ARCSEC

# Half-width of the fitting window around each probe date, in days. Wide
# enough that the probe sits far from the spline's own end effects.
DEFAULT_FIT_HALF_WINDOW_DAYS = 15

# Off-grid instants probed within each central day, as fractions of a day
# from the knot. Deliberately includes the worst case (half-way between two
# knots), where cubic interpolation error is maximal.
DEFAULT_PROBE_OFFSETS = (-0.5, -0.25, -0.1, 0.1, 0.25, 0.5)


def _unwrap_degrees(values: Sequence[float]) -> list[float]:
    """Turn a wrapped [0,360) angle sequence into a continuous one."""
    out = [float(values[0])]
    for v in values[1:]:
        prev = out[-1]
        candidate = float(v)
        # Move `candidate` into the branch nearest `prev`.
        while candidate - prev > 180.0:
            candidate -= 360.0
        while prev - candidate > 180.0:
            candidate += 360.0
        out.append(candidate)
    return out


def angular_delta_deg(a: float, b: float) -> float:
    """Signed shortest-arc difference a - b, in degrees, on (-180, 180]."""
    d = (float(a) - float(b)) % 360.0
    if d > 180.0:
        d -= 360.0
    return d


def fit_longitude_spline(knot_jds: Sequence[float], longitudes_deg: Sequence[float]):
    """Cubic spline over (noon-UT Julian day -> unwrapped tropical longitude).

    Returns a callable jd -> wrapped longitude in [0, 360)."""
    from scipy.interpolate import CubicSpline  # imported lazily; see validate()

    if len(knot_jds) < 4:
        raise ValueError("a cubic spline needs at least 4 knots")
    unwrapped = _unwrap_degrees(longitudes_deg)
    spline = CubicSpline(list(knot_jds), unwrapped)

    def _evaluate(jd: float) -> float:
        return float(spline(jd)) % 360.0

    return _evaluate


def _noon_ut_jd(swe, d: date) -> float:
    """The SAME abscissa the builder used for this date's row."""
    return swe.julday(d.year, d.month, d.day, 12.0)


def _swe_longitude(swe, body_name: str, jd: float) -> float:
    """Direct Swiss-Ephemeris tropical longitude, computed with the SAME
    flags and the SAME Ketu convention the builder used."""
    from brahmagyan.l0_ephemeris import DAILY_BODIES

    swe_id = next(b["swe_id"] for b in DAILY_BODIES if b["name"] == body_name)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    if swe_id == -1:  # Ketu = mean node + 180°, exactly as the builder does it
        rahu = swe.calc_ut(jd, 11, flags)
        return (rahu[0][0] + 180.0) % 360.0
    return swe.calc_ut(jd, swe_id, flags)[0][0]


def _fetch_window(query: QueryFn, body: str, start: date, end: date) -> list[dict]:
    return query(
        f"SELECT date, tropical_longitude, speed_dps FROM {TABLE} "
        f"WHERE body = %s AND ayanamsha_id = %s AND date BETWEEN %s AND %s "
        f"ORDER BY date",
        [body, AYANAMSHA_ID, start, end],
    )


def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def find_station_dates(query: QueryFn, body: str, limit: int = 3) -> list[date]:
    """Dates where `speed_dps` changes sign — real retrograde stations, read
    from the substrate rather than assumed from a period table."""
    rows = query(
        f"""
        SELECT date FROM (
            SELECT date, speed_dps,
                   LAG(speed_dps) OVER (ORDER BY date) AS prev_speed
            FROM {TABLE} WHERE body = %s AND ayanamsha_id = %s
        ) s
        WHERE prev_speed IS NOT NULL AND SIGN(speed_dps) <> SIGN(prev_speed)
        ORDER BY date
        LIMIT %s
        """,
        [body, AYANAMSHA_ID, limit],
    )
    return [_as_date(r["date"]) for r in rows]


def find_moon_perigee_dates(query: QueryFn, limit: int = 3) -> list[date]:
    """Dates of the Moon's fastest apparent motion — the perigee proxy the
    design names, taken from measured `speed_dps` maxima, not from a
    computed anomalistic-month phase."""
    rows = query(
        f"SELECT date, speed_dps FROM {TABLE} "
        f"WHERE body = 'Moon' AND ayanamsha_id = %s "
        f"ORDER BY speed_dps DESC LIMIT %s",
        [AYANAMSHA_ID, limit],
    )
    return [_as_date(r["date"]) for r in rows]


def audit_probe(
    query: QueryFn,
    swe,
    body: str,
    probe_date: date,
    half_window_days: int = DEFAULT_FIT_HALF_WINDOW_DAYS,
    probe_offsets: Sequence[float] = DEFAULT_PROBE_OFFSETS,
) -> dict[str, Any]:
    """Fit a spline around `probe_date` and measure |spline - swe| at
    off-grid instants. Errors are returned in ARCSECONDS."""
    window = _fetch_window(
        query,
        body,
        probe_date - timedelta(days=half_window_days),
        probe_date + timedelta(days=half_window_days),
    )
    if len(window) < 4:
        return {
            "body": body,
            "probe_date": probe_date.isoformat(),
            "measured": False,
            "reason": f"only {len(window)} ephemeris rows in the fitting window",
        }

    dates = [_as_date(r["date"]) for r in window]
    jds = [_noon_ut_jd(swe, d) for d in dates]
    lons = [float(r["tropical_longitude"]) for r in window]
    evaluate = fit_longitude_spline(jds, lons)

    centre_jd = _noon_ut_jd(swe, probe_date)
    errors: list[dict[str, Any]] = []
    for offset in probe_offsets:
        jd = centre_jd + float(offset)
        spline_lon = evaluate(jd)
        truth_lon = _swe_longitude(swe, body, jd)
        err_arcsec = abs(angular_delta_deg(spline_lon, truth_lon)) * ARCSEC_PER_DEG
        errors.append(
            {
                "offset_days": offset,
                "spline_deg": round(spline_lon, 8),
                "swe_deg": round(truth_lon, 8),
                "abs_error_arcsec": round(err_arcsec, 4),
            }
        )

    abs_errors = [e["abs_error_arcsec"] for e in errors]
    return {
        "body": body,
        "probe_date": probe_date.isoformat(),
        "measured": True,
        "n_knots": len(window),
        "max_abs_error_arcsec": round(max(abs_errors), 4),
        "mean_abs_error_arcsec": round(sum(abs_errors) / len(abs_errors), 4),
        "samples": errors,
    }


def validate_v3_spline_accuracy(
    query: QueryFn,
    accuracy_target_arcsec: float = ACCURACY_TARGET_ARCSEC,
    half_window_days: int = DEFAULT_FIT_HALF_WINDOW_DAYS,
) -> ValidationResult:
    title = (
        "V3 — cubic-spline interpolation error vs direct Swiss Ephemeris, "
        "near stations and Moon perigee (sets the root-find tolerance)"
    )

    try:
        import swisseph as swe  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return ValidationResult(
            validation_id="V3",
            title=title,
            status=INDETERMINATE,
            summary="swisseph is unavailable in this environment.",
            reason=(
                f"cannot compute the ground-truth side of the comparison: {exc}. "
                "There is no honest way to report an interpolation error without the "
                "reference it is measured against."
            ),
        )
    try:
        import scipy.interpolate  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return ValidationResult(
            validation_id="V3",
            title=title,
            status=INDETERMINATE,
            summary="scipy is unavailable in this environment.",
            reason=f"cannot fit the cubic spline under test: {exc}",
        )

    if not table_exists(query, TABLE):
        return ValidationResult(
            validation_id="V3",
            title=title,
            status=INDETERMINATE,
            summary=f"`{TABLE}` is not present in this database.",
            reason=f"no position substrate to fit a spline over (`{TABLE}` missing)",
        )

    probes: list[dict[str, Any]] = []

    # Regime 1 — stations. Mercury and Mars are the sharpest station
    # curvature among the bodies with real retrogradation in the substrate.
    for body in ("Mercury", "Mars", "Venus", "Saturn"):
        for d in find_station_dates(query, body, limit=2):
            probes.append({"regime": "station", "body": body, "date": d})

    # Regime 2 — Moon perigee (fastest apparent motion; the design's named
    # worst case for a daily grid).
    for d in find_moon_perigee_dates(query, limit=3):
        probes.append({"regime": "moon_perigee", "body": "Moon", "date": d})

    # Regime 3 — baseline Moon, away from perigee, so the perigee number has
    # something to be compared against rather than standing alone.
    baseline = query(
        f"SELECT date FROM {TABLE} WHERE body = 'Moon' AND ayanamsha_id = %s "
        f"ORDER BY speed_dps ASC LIMIT 2",
        [AYANAMSHA_ID],
    )
    for r in baseline:
        probes.append({"regime": "moon_apogee_baseline", "body": "Moon", "date": _as_date(r["date"])})

    if not probes:
        return ValidationResult(
            validation_id="V3",
            title=title,
            status=INDETERMINATE,
            summary="No probe dates could be located in the substrate.",
            reason=(
                "neither a sign change in `speed_dps` (station) nor a Moon speed extremum "
                "was found — the substrate cannot supply the regimes design §6 V3 names"
            ),
        )

    results: list[dict[str, Any]] = []
    for probe in probes:
        audit = audit_probe(
            query, swe, probe["body"], probe["date"], half_window_days=half_window_days
        )
        audit["regime"] = probe["regime"]
        results.append(audit)

    measured = [r for r in results if r.get("measured")]
    if not measured:
        return ValidationResult(
            validation_id="V3",
            title=title,
            status=INDETERMINATE,
            summary="No probe had enough surrounding ephemeris rows to fit a spline.",
            reason="every fitting window held fewer than 4 knots",
            data={"probes": results},
        )

    by_regime: dict[str, dict[str, Any]] = {}
    for r in measured:
        slot = by_regime.setdefault(
            r["regime"], {"n_probes": 0, "max_abs_error_arcsec": 0.0, "worst_probe": None}
        )
        slot["n_probes"] += 1
        if r["max_abs_error_arcsec"] > slot["max_abs_error_arcsec"]:
            slot["max_abs_error_arcsec"] = r["max_abs_error_arcsec"]
            slot["worst_probe"] = {"body": r["body"], "date": r["probe_date"]}

    overall_max = max(r["max_abs_error_arcsec"] for r in measured)
    worst = max(measured, key=lambda r: r["max_abs_error_arcsec"])

    findings: list[str] = [
        "Spline knots are placed at NOON UT — the abscissa "
        "`brahmagyan.l0_ephemeris` actually built each row at. A 2.0 spline that "
        "assumes midnight knots is wrong by half a day (~6.6 deg for the Moon).",
        "Stored `tropical_longitude` is rounded to 6 decimals (~0.013 arcsec). That "
        "quantization is a hard floor under every number here.",
    ]

    ok = overall_max <= accuracy_target_arcsec
    if not ok:
        findings.append(
            f"Worst-case interpolation error {overall_max:.2f} arcsec EXCEEDS the design "
            f"§2.1 arc-minute target ({accuracy_target_arcsec:.0f} arcsec), at "
            f"{worst['body']} {worst['probe_date']} (regime {worst['regime']}). "
            "The daily-knot spline is not by itself sufficient for this body/regime; the "
            "E-1 lane must either densify knots there or root-find against direct swe "
            "calls in that neighbourhood."
        )

    # The root-find tolerance the design says this validation sets. Stated as
    # the measured worst case with a safety factor, never as a round guess.
    recommended_tolerance_arcsec = round(max(overall_max * 2.0, 1.0), 3)

    return ValidationResult(
        validation_id="V3",
        title=title,
        status=PASS if ok else FAIL,
        summary=(
            f"Worst-case spline-vs-swe error {overall_max:.3f} arcsec across "
            f"{len(measured)} probe(s) in {len(by_regime)} regime(s); "
            f"target {accuracy_target_arcsec:.0f} arcsec."
        ),
        data={
            "accuracy_target_arcsec": accuracy_target_arcsec,
            "overall_max_abs_error_arcsec": overall_max,
            "worst_probe": {
                "body": worst["body"],
                "date": worst["probe_date"],
                "regime": worst["regime"],
                "max_abs_error_arcsec": worst["max_abs_error_arcsec"],
            },
            "by_regime": by_regime,
            "recommended_root_find_tolerance_arcsec": recommended_tolerance_arcsec,
            "knot_epoch_convention": "noon_ut",
            "stored_longitude_quantization_arcsec": round(1e-6 * ARCSEC_PER_DEG, 6),
            "fit_half_window_days": half_window_days,
            "probes": results,
        },
        findings=findings,
    )


__all__ = [
    "validate_v3_spline_accuracy",
    "fit_longitude_spline",
    "angular_delta_deg",
    "audit_probe",
    "find_station_dates",
    "find_moon_perigee_dates",
    "ACCURACY_TARGET_ARCSEC",
]
