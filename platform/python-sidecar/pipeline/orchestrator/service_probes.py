"""
service_probes.py — Health probe runners for service assets (asset_type='service').

A service asset's "build" = running its health probe. No rows written.
GREEN = all checks pass; degraded = partial; down = critical failure.

Each probe spec is stored in asset_registry.health_probe (JSONB) and references
a named probe type via the `probe_type` key. The dispatcher routes to the
appropriate implementation here.

Per UNIFIED_ASSET_REGISTRY_ARCHITECTURE_v1_0.md §D:
  GREEN when: (1) single canonical impl; (2) deterministic smoke; (3) FORENSIC-
  consistent where applicable; (4) endpoints reachable; (5) supported domain declared.
  Honest scope note (SAMĀPTI B-N8-SWEEPFIX, F-06): conditions (4) and (5) are NOT
  measured by the probes in this module. Both current probes cover in-process Python
  libraries with no network endpoint, so (4) is genuinely N/A; (5) is a registry-
  declaration check that no probe here performs. This module's GREEN therefore means
  "conditions (1)-(3) hold", not "all five hold" — stated so a reader of a GREEN
  result does not infer coverage that does not exist (CLAUDE.md §N.8).

Aggregation contract (F-06): `status` is computed from the `checks` list itself —
every check with `passed: False` contributes a failure. Use `_add_check()` to append;
it makes a false check that does not count toward the verdict structurally impossible.
A probe whose verdict and whose reported checks can disagree is an §N.8 violation.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _add_check(
    checks: list[dict],
    failures: list[str],
    name: str,
    passed: bool,
    failure_message: str = "",
    **detail: Any,
) -> bool:
    """Append one check result AND, when it did not pass, its failure message.

    Single append point so `status` can never read GREEN while a check in the same
    payload reads `passed: False` (F-06 part 2 — the verdict was computed from
    `failures` while check 3 set `passed: False` without appending to it).
    Returns `passed` so callers can branch.
    """
    checks.append({"check": name, "passed": passed, **detail})
    if not passed:
        failures.append(failure_message or f"{name} failed")
    return passed


def _aggregate(checks: list[dict], failures: list[str]) -> dict[str, Any]:
    """Verdict from the checks actually reported. Defence-in-depth: recount the
    failed checks rather than trusting `failures` alone, so a future caller that
    appends to `checks` directly still cannot produce a GREEN-with-a-false-check."""
    failed_checks = [c for c in checks if not c.get("passed")]
    n_failed = max(len(failures), len(failed_checks))
    if n_failed == 0:
        status = "GREEN"
    elif checks and n_failed < len(checks):
        status = "degraded"
    else:
        status = "down"
    if failures:
        message = "; ".join(failures)
    elif failed_checks:
        message = "; ".join(f"{c['check']} reported passed=false" for c in failed_checks)
    else:
        message = "All checks passed"
    return {"status": status, "message": message, "checks": checks}


def run_health_probe(asset_id: str, probe_spec: dict | None) -> dict[str, Any]:
    """
    Dispatch to the named probe type for asset_id.
    Returns: {"status": "GREEN"|"degraded"|"down", "message": str, "checks": list}
    """
    if not probe_spec:
        return {"status": "down", "message": "no health_probe defined in asset_registry", "checks": []}

    probe_type = probe_spec.get("probe_type")
    if probe_type == "panchanga_engine":
        return _probe_panchanga_engine(probe_spec)
    elif probe_type == "ephemeris_engine":
        return _probe_ephemeris_engine(probe_spec)
    else:
        return {"status": "down", "message": f"unknown probe_type: {probe_type}", "checks": []}


# ── bg_panchanga probe ────────────────────────────────────────────────────────

_FORENSIC_BIRTH = {
    "instant": "1984-02-05T10:43:00",
    "lat": 20.27,
    "lon": 85.84,
    "tz_offset": 330,
    "expected": {
        "tithi": "Shukla Tritiya",
        "nakshatra": "Purva Bhadrapada",
        "yoga": "Shiva",
        "karana": "Garaja",
        "vara": "Ravivara",
    },
}


def _probe_panchanga_engine(probe_spec: dict) -> dict[str, Any]:
    checks: list[dict] = []
    failures: list[str] = []

    # Check 1: single canonical implementation importable
    try:
        from panchang_engine import panchanga_instant, panchanga_day  # noqa: F401
        _add_check(checks, failures, "single_engine_importable", True)
    except ImportError as exc:
        _add_check(checks, failures, "single_engine_importable", False,
                   f"import failed: {exc}", error=str(exc))

    # Check 2: deterministic FORENSIC smoke — panchanga_instant at birth
    try:
        from datetime import datetime
        from panchang_engine import panchanga_instant
        instant = datetime.fromisoformat(_FORENSIC_BIRTH["instant"])
        result = panchanga_instant(instant, _FORENSIC_BIRTH["lat"], _FORENSIC_BIRTH["lon"],
                                   _FORENSIC_BIRTH["tz_offset"])
        expected = _FORENSIC_BIRTH["expected"]
        mismatches = []
        for field, exp_val in expected.items():
            actual = getattr(result, field, None)
            actual_name = getattr(actual, "name", actual) if actual is not None else None
            if actual_name != exp_val:
                mismatches.append(f"{field}: got {actual_name!r}, expected {exp_val!r}")
        if mismatches:
            _add_check(checks, failures, "forensic_birth_smoke", False,
                       f"FORENSIC mismatch: {mismatches}", mismatches=mismatches)
        else:
            _add_check(checks, failures, "forensic_birth_smoke", True)
    except Exception as exc:
        _add_check(checks, failures, "forensic_birth_smoke", False,
                   f"forensic smoke exception: {exc}", error=str(exc))

    # Check 3: panchanga_day returns the SUNRISE-BASED FORENSIC angas for the birth date.
    #
    # F-06 fix. The prior form was `passed: result is not None` — `panchanga_day` is
    # annotated `-> "Panchang"` and has no `return None` path, so that expression could
    # not evaluate False; the only real detector was the surrounding try/except, and the
    # field itself measured nothing (CLAUDE.md §N.8).
    #
    # This is NOT a duplicate of check 2. Check 2 calls panchanga_instant() and asserts
    # the angas at the birth MOMENT (10:43 IST). This calls panchanga_day() and asserts
    # the angas ruling at SUNRISE on the same date — a different code path through the
    # engine with a different reference instant. Karana is instant-only and is therefore
    # not asserted here.
    _DAY_EXPECTED = {"vara": "Ravivara", "tithi": "Shukla Tritiya",
                     "nakshatra": "Purva Bhadrapada", "yoga": "Shiva"}
    try:
        from datetime import date
        from panchang_engine import panchanga_day
        birth_date = date(1984, 2, 5)
        result = panchanga_day(birth_date, _FORENSIC_BIRTH["lat"],
                               _FORENSIC_BIRTH["lon"], _FORENSIC_BIRTH["tz_offset"])
        day_mismatches: list[str] = []
        if getattr(result, "date", None) != birth_date:
            day_mismatches.append(
                f"date: got {getattr(result, 'date', None)!r}, expected {birth_date!r}"
            )
        for field, exp_val in _DAY_EXPECTED.items():
            actual = getattr(result, field, None)
            actual_name = getattr(actual, "name", actual) if actual is not None else None
            if actual_name != exp_val:
                day_mismatches.append(f"{field}: got {actual_name!r}, expected {exp_val!r}")
        _add_check(checks, failures, "panchanga_day_forensic_sunrise_angas",
                   not day_mismatches,
                   f"panchanga_day FORENSIC mismatch: {day_mismatches}",
                   mismatches=day_mismatches)
    except Exception as exc:
        _add_check(checks, failures, "panchanga_day_forensic_sunrise_angas", False,
                   f"panchanga_day exception: {exc}", error=str(exc))

    return _aggregate(checks, failures)


# ── bg_ephemeris_engine probe ─────────────────────────────────────────────────

# F-04 fix (SAMĀPTI B-N8-SWEEPFIX). Two defects made this probe unable to return
# GREEN in ANY environment, i.e. the ephemeris service asset's health signal was
# unearned in both branches (CLAUDE.md §N.8):
#
#   1. `jd` was 2445701.948264, commented "1984-02-05 10:43 IST → UTC Julian Day".
#      swe.revjul() decodes that value to 1984-01-02 10:45 UT — wrong by 33.77 days.
#      Recomputed with swe.julday(1984, 2, 5, 5 + 13/60) — 10:43 IST = 05:13 UT —
#      the correct JD is 2445735.717361111 (swe.revjul round-trips it to
#      1984-02-05 05:13 UT).
#
#   2. Both expected values below are SIDEREAL LAHIRI signs (as their comments have
#      always said, and as CLAUDE.md §B's FORENSIC anchors are stated), but the
#      checks called swe.calc_ut() with no FLG_SIDEREAL and no sid_mode set — i.e.
#      they compared a sidereal expectation against a tropical measurement. The
#      expected VALUES were right; the ayanamsha handling was wrong. Verified by
#      execution at the corrected JD with SIDM_LAHIRI + FLG_SIDEREAL:
#         Sun  lon = 291.9568° → sign 10 (Makara)     == expected_sun_sign
#         Rahu lon =  49.0330° → sign  2 (Vrishabha)  == expected_mean_node_rahu_sign
#         Ketu       229.0330° → sign  8 (Vrischika)  == derived Ketu expectation
#      (tropical at the same JD: Sun 315.5877° sign 11, node 72.6639° sign 3 — which
#      is what the old code measured and why check 3 failed unconditionally.)
#
# Sign-level assertions carry ≥8° of margin to the nearest sign boundary, so they are
# insensitive to the sub-arcsecond Swiss-file-vs-Moshier difference but WILL fail on a
# wrong body, a wrong Julian Day, or a missing/incorrect ayanamsha — which is the point.
_FORENSIC_POSITION = {
    "jd": 2445735.717361111,  # 1984-02-05 10:43 IST = 05:13 UT → Julian Day (swe.julday)
    "expected_sun_sign": 10,  # Makara (Capricorn) sidereal Lahiri
    "expected_mean_node_rahu_sign": 2,  # Vrishabha — Rahu mean node, sidereal Lahiri
}

# Swiss Ephemeris return-flag bits (swe.FLG_*), pinned here so the backend attribution
# below does not depend on the caller having imported swisseph.
_EPHE_BACKENDS = ((1, "jpl_file"), (2, "swiss_ephemeris_file"), (4, "moshier_analytic_fallback"))


def _ephemeris_backend(retflag: int) -> str:
    """Which ephemeris actually served the position, per the returned flag.

    `swe.calc_ut` silently falls back to the built-in Moshier analytic theory when the
    configured ephemeris files are absent. The retflag is the only datum that
    distinguishes them, and the previous code discarded it (`xx, _ = swe.calc_ut(...)`).

    Honest bound: this distinguishes JPL-file / Swiss-file / Moshier-fallback. It does
    NOT identify WHICH JPL ephemeris (DE441 vs DE431) backs the Swiss files — Swiss
    Ephemeris does not report that through this flag. The check built on this is named
    for what it can measure, not for DE441.
    """
    for bit, name in _EPHE_BACKENDS:
        if retflag & bit:
            return name
    return f"unknown (retflag={retflag})"


def _probe_ephemeris_engine(probe_spec: dict) -> dict[str, Any]:
    checks: list[dict] = []
    failures: list[str] = []

    # Check 1: swisseph importable
    try:
        import swisseph as swe  # noqa: F401
        _add_check(checks, failures, "swisseph_importable", True)
    except ImportError as exc:
        _add_check(checks, failures, "swisseph_importable", False,
                   f"swisseph import failed: {exc}", error=str(exc))
        return {"status": "down", "message": str(exc), "checks": checks}

    # Check 2: position query runs AND the sidereal-Lahiri Sun is in the FORENSIC sign.
    # CLAUDE.md §B anchor: Sun = Capricorn (Makara, sign 10) — a SIDEREAL statement.
    # Asserted as an exact sign equality, not a ±15° window: a window wide enough to
    # "absorb ayanamsha differences" is wide enough to pass on the wrong ayanamsha,
    # which is exactly how the pre-fix check passed on a Julian Day 33.77 days off.
    ephe_path = None
    try:
        import swisseph as swe
        import os
        ephe_path = os.environ.get("SWISSEPH_PATH", "/app/ephe")
        swe.set_ephe_path(ephe_path)
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        _SID = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        jd = _FORENSIC_POSITION["jd"]
        xx, retflag = swe.calc_ut(jd, swe.SUN, _SID)
        sun_lon = xx[0]
        sun_sign = int(sun_lon / 30) + 1
        expected_sun_sign = _FORENSIC_POSITION["expected_sun_sign"]
        _add_check(
            checks, failures, "sidereal_sun_forensic_sign",
            sun_sign == expected_sun_sign,
            f"sidereal-Lahiri Sun sign={sun_sign} (lon={sun_lon:.4f}°), expected sign "
            f"{expected_sun_sign} (Makara) for 1984-02-05 10:43 IST",
            sun_lon=round(sun_lon, 4),
            sun_sign=sun_sign,
            expected_sun_sign=expected_sun_sign,
            ayanamsha="Lahiri",
            ephemeris_backend=_ephemeris_backend(retflag),
            ephe_path=ephe_path,
        )
    except Exception as exc:
        _add_check(checks, failures, "sidereal_sun_forensic_sign", False,
                   f"ephemeris position query failed: {exc}",
                   error=str(exc), ephe_path=ephe_path)

    # Check 3: MEAN_NODE-for-Rahu invariant, sidereal Lahiri.
    # Asserts Rahu is in Vrishabha (sign 2) and Ketu — its exact opposite — in
    # Vrischika (sign 8). A real FORENSIC assertion, not the tautological
    # "1 <= sign <= 12" which is always True for any valid ephemeris output.
    try:
        import swisseph as swe
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        _SID = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        jd = _FORENSIC_POSITION["jd"]
        xx, _retflag = swe.calc_ut(jd, swe.MEAN_NODE, _SID)
        node_lon = xx[0]
        rahu_sign = int(node_lon / 30) + 1
        expected_rahu_sign = _FORENSIC_POSITION["expected_mean_node_rahu_sign"]  # 2
        # Ketu is exactly opposite; swe.MEAN_NODE gives Rahu, Ketu = (Rahu + 180) % 360
        ketu_lon = (node_lon + 180.0) % 360.0
        ketu_sign = int(ketu_lon / 30) + 1
        expected_ketu_sign = ((expected_rahu_sign - 1 + 6) % 12) + 1  # 8 = Vrischika
        rahu_ok = rahu_sign == expected_rahu_sign
        ketu_ok = ketu_sign == expected_ketu_sign
        node_failures = []
        if not rahu_ok:
            node_failures.append(
                f"Rahu sign={rahu_sign} (lon={node_lon:.4f}°), "
                f"expected sign {expected_rahu_sign} (Vrishabha) for 1984-02-05"
            )
        if not ketu_ok:
            node_failures.append(
                f"Ketu sign={ketu_sign} (lon={ketu_lon:.4f}°), "
                f"expected sign {expected_ketu_sign} (Vrischika) for 1984-02-05"
            )
        _add_check(
            checks, failures, "sidereal_mean_node_rahu_invariant",
            rahu_ok and ketu_ok,
            "; ".join(node_failures),
            rahu_sign=rahu_sign,
            rahu_lon=round(node_lon, 4),
            ketu_sign=ketu_sign,
            expected_rahu_sign=expected_rahu_sign,
            expected_ketu_sign=expected_ketu_sign,
            ayanamsha="Lahiri",
            # No ephemeris_backend here on purpose: MEAN_NODE is computed analytically
            # and swisseph returns FLG_SWIEPH for it even when the ephemeris files are
            # absent, so the flag would report a file-backed source that isn't one.
            # The Sun check above is where backend attribution is meaningful.
        )
    except Exception as exc:
        _add_check(checks, failures, "sidereal_mean_node_rahu_invariant", False,
                   f"MEAN_NODE check failed: {exc}", error=str(exc))

    return _aggregate(checks, failures)
