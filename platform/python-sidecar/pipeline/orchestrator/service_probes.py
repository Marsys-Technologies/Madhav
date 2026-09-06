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
    elif probe_type == "graha_sancara_forensic":
        return _probe_graha_sancara(probe_spec)
    elif probe_type == "tulana_ranking_forensic":
        return _probe_tulana(probe_spec)
    else:
        return {"status": "down", "message": f"unknown probe_type: {probe_type}", "checks": []}


# ── bg_panchanga probe ────────────────────────────────────────────────────────

_PANCHANGA_EXPECTED_FIELDS = ("tithi", "nakshatra", "yoga", "karana", "vara")
_PANCHANGA_EXPECTED_FIELD_SET = frozenset(_PANCHANGA_EXPECTED_FIELDS)


def _validated_panchanga_probe_config(probe_spec: dict) -> dict[str, Any]:
    """Return normalized registry inputs or fail closed on an incomplete probe."""
    from datetime import datetime

    required = {
        "forensic_instant",
        "forensic_lat",
        "forensic_lon",
        "forensic_tz_offset",
        "forensic_expected",
    }
    missing = sorted(required - probe_spec.keys())
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    raw_instant = probe_spec["forensic_instant"]
    if not isinstance(raw_instant, str):
        raise ValueError("forensic_instant must be an ISO-8601 string")
    try:
        instant = datetime.fromisoformat(raw_instant)
    except ValueError as exc:
        raise ValueError("forensic_instant must be valid ISO-8601") from exc
    if instant.tzinfo is not None:
        raise ValueError("forensic_instant must be local wall time without an embedded offset")

    lat = probe_spec["forensic_lat"]
    lon = probe_spec["forensic_lon"]
    tz_offset = probe_spec["forensic_tz_offset"]
    if isinstance(lat, bool) or not isinstance(lat, (int, float)) or not -90 <= lat <= 90:
        raise ValueError("forensic_lat must be a number in [-90, 90]")
    if isinstance(lon, bool) or not isinstance(lon, (int, float)) or not -180 <= lon <= 180:
        raise ValueError("forensic_lon must be a number in [-180, 180]")
    if isinstance(tz_offset, bool) or not isinstance(tz_offset, int) or not -840 <= tz_offset <= 840:
        raise ValueError("forensic_tz_offset must be integer minutes in [-840, 840]")

    expected = probe_spec["forensic_expected"]
    if not isinstance(expected, dict):
        raise ValueError("forensic_expected must be an object")
    missing_expected = sorted(_PANCHANGA_EXPECTED_FIELD_SET - expected.keys())
    if missing_expected:
        raise ValueError(f"forensic_expected is missing: {', '.join(missing_expected)}")
    invalid_expected = sorted(
        field for field in _PANCHANGA_EXPECTED_FIELDS
        if not isinstance(expected[field], str) or not expected[field].strip()
    )
    if invalid_expected:
        raise ValueError(
            "forensic_expected values must be non-empty strings: "
            + ", ".join(invalid_expected)
        )

    return {
        "instant": instant,
        "lat": float(lat),
        "lon": float(lon),
        "tz_offset": tz_offset,
        "expected": {field: expected[field] for field in _PANCHANGA_EXPECTED_FIELDS},
    }


def _probe_panchanga_engine(probe_spec: dict) -> dict[str, Any]:
    checks: list[dict] = []
    failures: list[str] = []

    try:
        config = _validated_panchanga_probe_config(probe_spec)
        _add_check(checks, failures, "probe_config_valid", True)
    except (TypeError, ValueError) as exc:
        _add_check(
            checks,
            failures,
            "probe_config_valid",
            False,
            f"invalid panchanga health_probe contract: {exc}",
            error=str(exc),
        )
        return _aggregate(checks, failures)

    # Check 1: single canonical implementation importable
    try:
        from panchang_engine import panchanga_instant, panchanga_day  # noqa: F401
        _add_check(checks, failures, "single_engine_importable", True)
    except ImportError as exc:
        _add_check(checks, failures, "single_engine_importable", False,
                   f"import failed: {exc}", error=str(exc))

    # Check 2: deterministic FORENSIC smoke — panchanga_instant at birth
    try:
        from panchang_engine import panchanga_instant
        result = panchanga_instant(
            config["instant"], config["lat"], config["lon"], config["tz_offset"]
        )
        expected = config["expected"]
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
    _DAY_EXPECTED_FIELDS = ("vara", "tithi", "nakshatra", "yoga")
    try:
        from panchang_engine import panchanga_day
        birth_date = config["instant"].date()
        result = panchanga_day(
            birth_date, config["lat"], config["lon"], config["tz_offset"]
        )
        day_mismatches: list[str] = []
        if getattr(result, "date", None) != birth_date:
            day_mismatches.append(
                f"date: got {getattr(result, 'date', None)!r}, expected {birth_date!r}"
            )
        day_expected = {field: config["expected"][field] for field in _DAY_EXPECTED_FIELDS}
        for field, exp_val in day_expected.items():
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
# Swiss Ephemeris return-flag bits (swe.FLG_*), pinned here so the backend attribution
# below does not depend on the caller having imported swisseph.
_EPHE_BACKENDS = ((1, "jpl_file"), (2, "swiss_ephemeris_file"), (4, "moshier_analytic_fallback"))
_EPHE_BACKEND_NAMES = frozenset(name for _bit, name in _EPHE_BACKENDS)
_EPHEMERIS_CORPUS_FILES = frozenset({"sepl_18.se1", "semo_18.se1", "seas_18.se1"})


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


def _validated_ephemeris_probe_config(probe_spec: dict) -> dict[str, Any]:
    """Normalize the registry-owned ephemeris contract or fail closed."""
    import re

    required = {
        "forensic_jd",
        "expected_sun_sign",
        "expected_mean_node_rahu_sign",
        "ayanamsha",
        "node_mode",
        "allowed_ephemeris_backends",
        "ephemeris_file_sha256",
    }
    missing = sorted(required - probe_spec.keys())
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    jd = probe_spec["forensic_jd"]
    if isinstance(jd, bool) or not isinstance(jd, (int, float)) or not 1_000_000 < jd < 4_000_000:
        raise ValueError("forensic_jd must be a plausible numeric Julian Day")

    def _sign(field: str) -> int:
        value = probe_spec[field]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 12:
            raise ValueError(f"{field} must be an integer sign number in [1, 12]")
        return value

    if probe_spec["ayanamsha"] != "lahiri":
        raise ValueError("ayanamsha must be 'lahiri'")
    if probe_spec["node_mode"] != "mean":
        raise ValueError("node_mode must be 'mean'")

    allowed = probe_spec["allowed_ephemeris_backends"]
    if not isinstance(allowed, list) or not allowed or any(not isinstance(x, str) for x in allowed):
        raise ValueError("allowed_ephemeris_backends must be a non-empty string array")
    unknown = sorted(set(allowed) - _EPHE_BACKEND_NAMES)
    if unknown:
        raise ValueError(f"unknown allowed_ephemeris_backends: {', '.join(unknown)}")

    file_sha256 = probe_spec["ephemeris_file_sha256"]
    if not isinstance(file_sha256, dict) or set(file_sha256) != _EPHEMERIS_CORPUS_FILES:
        raise ValueError(
            "ephemeris_file_sha256 must pin exactly sepl_18.se1, semo_18.se1, seas_18.se1"
        )
    invalid_digests = sorted(
        name for name, digest in file_sha256.items()
        if not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None
    )
    if invalid_digests:
        raise ValueError(
            "ephemeris_file_sha256 contains invalid SHA-256 values: "
            + ", ".join(invalid_digests)
        )

    return {
        "jd": float(jd),
        "expected_sun_sign": _sign("expected_sun_sign"),
        "expected_mean_node_rahu_sign": _sign("expected_mean_node_rahu_sign"),
        "allowed_ephemeris_backends": frozenset(allowed),
        "ephemeris_file_sha256": file_sha256,
    }


def _probe_ephemeris_engine(probe_spec: dict) -> dict[str, Any]:
    checks: list[dict] = []
    failures: list[str] = []

    try:
        config = _validated_ephemeris_probe_config(probe_spec)
        _add_check(checks, failures, "probe_config_valid", True)
    except (TypeError, ValueError) as exc:
        _add_check(
            checks,
            failures,
            "probe_config_valid",
            False,
            f"invalid ephemeris health_probe contract: {exc}",
            error=str(exc),
        )
        return _aggregate(checks, failures)

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
        import hashlib
        import os
        from pathlib import Path

        ephe_path = (
            os.environ.get("SWE_EPHE_PATH")
            or os.environ.get("SWISSEPH_PATH")
            or "/app/ephe"
        )
        expected_files = config["ephemeris_file_sha256"]
        actual_files: dict[str, str] = {}
        file_errors: list[str] = []
        for filename, expected_digest in sorted(expected_files.items()):
            source = Path(ephe_path) / filename
            if not source.is_file():
                file_errors.append(f"{filename}: missing")
                continue
            digest = hashlib.sha256()
            with source.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            actual_digest = digest.hexdigest()
            actual_files[filename] = actual_digest
            if actual_digest != expected_digest:
                file_errors.append(
                    f"{filename}: SHA-256 {actual_digest}, expected {expected_digest}"
                )
        _add_check(
            checks,
            failures,
            "ephemeris_corpus_sha256",
            not file_errors,
            "; ".join(file_errors),
            files=actual_files,
            ephe_path=ephe_path,
        )

        swe.set_ephe_path(ephe_path)
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        _SID = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        jd = config["jd"]
        xx, retflag = swe.calc_ut(jd, swe.SUN, _SID)
        sun_lon = xx[0]
        sun_sign = int(sun_lon / 30) + 1
        expected_sun_sign = config["expected_sun_sign"]
        backend = _ephemeris_backend(retflag)
        backend_ok = backend in config["allowed_ephemeris_backends"]
        sun_ok = sun_sign == expected_sun_sign
        sun_failures = []
        if not sun_ok:
            sun_failures.append(
                f"sidereal-Lahiri Sun sign={sun_sign} (lon={sun_lon:.4f}°), "
                f"expected sign {expected_sun_sign} at JD {jd}"
            )
        if not backend_ok:
            sun_failures.append(
                f"ephemeris backend={backend}, allowed="
                f"{sorted(config['allowed_ephemeris_backends'])}"
            )
        _add_check(
            checks, failures, "sidereal_sun_forensic_sign",
            sun_ok and backend_ok,
            "; ".join(sun_failures),
            sun_lon=round(sun_lon, 4),
            sun_sign=sun_sign,
            expected_sun_sign=expected_sun_sign,
            ayanamsha="Lahiri",
            ephemeris_backend=backend,
            allowed_ephemeris_backends=sorted(config["allowed_ephemeris_backends"]),
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
        jd = config["jd"]
        xx, _retflag = swe.calc_ut(jd, swe.MEAN_NODE, _SID)
        node_lon = xx[0]
        rahu_sign = int(node_lon / 30) + 1
        expected_rahu_sign = config["expected_mean_node_rahu_sign"]
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
                f"expected sign {expected_rahu_sign} at JD {jd}"
            )
        if not ketu_ok:
            node_failures.append(
                f"Ketu sign={ketu_sign} (lon={ketu_lon:.4f}°), "
                f"expected sign {expected_ketu_sign} at JD {jd}"
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


# ── ka_graha_sancara probe ────────────────────────────────────────────────────

# NIRMĀṆA L3-W4 — an INDEPENDENT probe, not a reuse of
# pipeline/orchestrator/writers/ka_graha_sancara.py's own self-test (implementer
# != certifier, same discipline as the two probes above). Both call the same
# single canonical `services.ka_graha_sancara.engine.get_ephemeris` surface,
# but this one is invoked fresh from the Nirmana probe route, independent of
# whatever the writer already self-reported into `selftest_detail`.
#
# `force_live=True` is load-bearing: it is the ONLY path that answers a
# birth-INSTANT question (PATH-A/`ephemeris_daily` is day-grade, computed at
# 12:00 UT, and yields the wrong sign for this exact anchor — see L3-W3 M3 /
# `ka_graha_sancara.py`'s own `forensic_moon_sign` check comment). It is also
# what keeps this probe DB-free (skips PATH-A's `db_conn` read entirely), same
# class of guarantee as the two probes above ("in-process Python library, no
# network endpoint" — module docstring).
_GRAHA_SANCARA_EXPECTED_GRAHAS = frozenset(
    {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
)


def _validated_graha_sancara_probe_config(probe_spec: dict) -> dict[str, Any]:
    """Return normalized registry inputs or fail closed on an incomplete probe."""
    from datetime import datetime

    required = {"forensic_birth_instant", "forensic_ayanamsha", "forensic_expected_moon_sign"}
    missing = sorted(required - probe_spec.keys())
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    raw_instant = probe_spec["forensic_birth_instant"]
    if not isinstance(raw_instant, str):
        raise ValueError("forensic_birth_instant must be an ISO-8601 string")
    try:
        instant = datetime.fromisoformat(raw_instant)
    except ValueError as exc:
        raise ValueError("forensic_birth_instant must be valid ISO-8601") from exc
    if instant.tzinfo is not None:
        raise ValueError("forensic_birth_instant must be local wall time without an embedded offset")

    ayanamsha = probe_spec["forensic_ayanamsha"]
    if ayanamsha != "lahiri":
        raise ValueError("forensic_ayanamsha must be 'lahiri' (engine's live-compute path supports only lahiri)")

    expected_moon_sign = probe_spec["forensic_expected_moon_sign"]
    if not isinstance(expected_moon_sign, str) or not expected_moon_sign.strip():
        raise ValueError("forensic_expected_moon_sign must be a non-empty string")

    return {"instant": instant, "ayanamsha": ayanamsha, "expected_moon_sign": expected_moon_sign}


def _probe_graha_sancara(probe_spec: dict) -> dict[str, Any]:
    checks: list[dict] = []
    failures: list[str] = []

    try:
        config = _validated_graha_sancara_probe_config(probe_spec)
        _add_check(checks, failures, "probe_config_valid", True)
    except (TypeError, ValueError) as exc:
        _add_check(
            checks,
            failures,
            "probe_config_valid",
            False,
            f"invalid graha_sancara health_probe contract: {exc}",
            error=str(exc),
        )
        return _aggregate(checks, failures)

    # Check 1: single canonical implementation importable
    try:
        from services.ka_graha_sancara.engine import get_ephemeris  # noqa: F401
        _add_check(checks, failures, "single_engine_importable", True)
    except ImportError as exc:
        _add_check(checks, failures, "single_engine_importable", False,
                   f"import failed: {exc}", error=str(exc))
        return _aggregate(checks, failures)

    # Check 2 + 3: birth-instant FORENSIC compute, independent of PATH-A/db_conn.
    try:
        from services.ka_graha_sancara.engine import get_ephemeris
        result = get_ephemeris(
            dt=config["instant"], ayanamsha=config["ayanamsha"], db_conn=None, force_live=True,
        )
    except Exception as exc:
        _add_check(checks, failures, "forensic_moon_sign", False,
                   f"ephemeris computation failed: {exc}", error=str(exc))
        _add_check(checks, failures, "nine_grahas_present", False,
                   "ephemeris computation failed, no grahas to check")
        return _aggregate(checks, failures)

    moon = result.grahas.get("Moon")
    moon_sign = moon.sign if moon is not None else None
    moon_ok = moon_sign == config["expected_moon_sign"]
    _add_check(
        checks, failures, "forensic_moon_sign", moon_ok,
        f"Moon sign={moon_sign!r}, expected {config['expected_moon_sign']!r} "
        f"at {config['instant'].isoformat()} ({config['ayanamsha']}, force_live)",
        moon_sign=moon_sign, expected_moon_sign=config["expected_moon_sign"],
        source=result.source,
    )

    # Check 3: same 9-graha/non-null-speed completeness the writer's own
    # selftest asserts (L3-W3 M3 context) — free from the same result object,
    # independently re-derived here rather than trusted from the writer.
    graha_names = set(result.grahas.keys())
    missing_grahas = sorted(_GRAHA_SANCARA_EXPECTED_GRAHAS - graha_names)
    null_speeds = sorted(name for name, gs in result.grahas.items() if gs.speed_dps is None)
    nine_ok = not missing_grahas and not null_speeds
    _add_check(
        checks, failures, "nine_grahas_present", nine_ok,
        f"missing={missing_grahas}, null_speeds={null_speeds}" if not nine_ok else "",
        missing_grahas=missing_grahas, null_speeds=null_speeds, graha_count=len(graha_names),
    )

    return _aggregate(checks, failures)


# ── ka_tulana probe ───────────────────────────────────────────────────────────

# NIRMĀṆA L3-W3 (F-L3-15, third slice; correction of an earlier PR description
# that mis-scoped this asset as DB-dependent — see #2065's own follow-up note).
# `KaTulanaService.rank_windows()`/`.compare()` are PURE ranking logic over
# already-computed `WindowInput` records the caller supplies — "No DB writes,
# No commit/rollback" per the module's own docstring, no `db_conn` anywhere in
# the class. This is DB-free by construction, the same class the other three
# probes are built for — no architecture question, unlike `ka_dasha_kala`
# (which genuinely does read `chart_dashas` via `db_conn` inside its own
# `tree_walk.walk_eligible_intervals`, still out of scope).
#
# The check constructs two FIXED, synthetic WindowInput records (not fetched
# from any chart) and asserts the I-11 composite formula (native-ratified
# weights: 0.40 convergence / 0.25 rarity / 0.20 confidence / 0.15 proximity)
# produces the exact pinned composite scores AND the exact rank order AND the
# exact compare() decisive_factor/recommendation — a genuine re-derivation of
# the deterministic math, not a bare "did it return something" check.
_TULANA_REQUIRED_FIELDS = frozenset(
    {
        "forensic_reference_date",
        "forensic_window_a",
        "forensic_window_b",
        "forensic_expected_composite_a",
        "forensic_expected_composite_b",
        "forensic_expected_winner_window_id",
        "forensic_expected_decisive_factor",
    }
)
_TULANA_WINDOW_FIELDS = frozenset(
    {"window_id", "mode", "peak_date", "convergence_score", "confidence_label", "rarity_years"}
)


def _validated_tulana_window(spec: dict, field_name: str):
    from datetime import date as date_cls
    from services.ka_tulana.ranker import WindowInput

    if not isinstance(spec, dict):
        raise ValueError(f"{field_name} must be an object")
    missing = sorted(_TULANA_WINDOW_FIELDS - spec.keys())
    if missing:
        raise ValueError(f"{field_name} missing fields: {', '.join(missing)}")
    try:
        peak_date = date_cls.fromisoformat(spec["peak_date"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name}.peak_date must be a valid ISO-8601 date") from exc
    return WindowInput(
        window_id=spec["window_id"],
        mode=spec["mode"],
        peak_date=peak_date,
        convergence_score=float(spec["convergence_score"]),
        confidence_label=spec["confidence_label"],
        rarity_years=float(spec["rarity_years"]),
    )


def _validated_tulana_probe_config(probe_spec: dict) -> dict[str, Any]:
    """Return normalized registry inputs or fail closed on an incomplete probe."""
    from datetime import date as date_cls

    missing = sorted(_TULANA_REQUIRED_FIELDS - probe_spec.keys())
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    try:
        reference_date = date_cls.fromisoformat(probe_spec["forensic_reference_date"])
    except (TypeError, ValueError) as exc:
        raise ValueError("forensic_reference_date must be a valid ISO-8601 date") from exc

    window_a = _validated_tulana_window(probe_spec["forensic_window_a"], "forensic_window_a")
    window_b = _validated_tulana_window(probe_spec["forensic_window_b"], "forensic_window_b")

    def _score(field: str) -> float:
        value = probe_spec[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be a number")
        return float(value)

    winner_id = probe_spec["forensic_expected_winner_window_id"]
    if not isinstance(winner_id, str) or not winner_id.strip():
        raise ValueError("forensic_expected_winner_window_id must be a non-empty string")
    if winner_id not in (window_a.window_id, window_b.window_id):
        raise ValueError(
            "forensic_expected_winner_window_id must match forensic_window_a or forensic_window_b's window_id"
        )

    decisive_factor = probe_spec["forensic_expected_decisive_factor"]
    if not isinstance(decisive_factor, str) or not decisive_factor.strip():
        raise ValueError("forensic_expected_decisive_factor must be a non-empty string")

    return {
        "reference_date": reference_date,
        "window_a": window_a,
        "window_b": window_b,
        "expected_composite_a": _score("forensic_expected_composite_a"),
        "expected_composite_b": _score("forensic_expected_composite_b"),
        "expected_winner_window_id": winner_id,
        "expected_decisive_factor": decisive_factor,
    }


# Float-tolerance for composite-score comparisons — the I-11 formula's own
# rounding is to 4 decimal places (ranker.py's `_composite()`), so anything
# tighter than that would be fragile against the module's own precision.
_TULANA_SCORE_EPSILON = 1e-4


def _probe_tulana(probe_spec: dict) -> dict[str, Any]:
    checks: list[dict] = []
    failures: list[str] = []

    try:
        config = _validated_tulana_probe_config(probe_spec)
        _add_check(checks, failures, "probe_config_valid", True)
    except (TypeError, ValueError) as exc:
        _add_check(
            checks,
            failures,
            "probe_config_valid",
            False,
            f"invalid tulana health_probe contract: {exc}",
            error=str(exc),
        )
        return _aggregate(checks, failures)

    # Check 1: single canonical implementation importable
    try:
        from services.ka_tulana.ranker import KaTulanaService  # noqa: F401
        _add_check(checks, failures, "single_engine_importable", True)
    except ImportError as exc:
        _add_check(checks, failures, "single_engine_importable", False,
                    f"import failed: {exc}", error=str(exc))
        return _aggregate(checks, failures)

    # Check 2: rank_windows() produces the exact pinned composite scores AND
    # rank order for two fixed, synthetic windows — a genuine re-derivation of
    # the I-11 weighted-sum formula, not a bare "returned a list" check.
    try:
        from services.ka_tulana.ranker import KaTulanaService

        svc = KaTulanaService()
        ranked = svc.rank_windows(
            [config["window_a"], config["window_b"]], reference_date=config["reference_date"]
        )
        by_id = {r.window.window_id: r for r in ranked}
        composite_a = by_id[config["window_a"].window_id].factors.composite
        composite_b = by_id[config["window_b"].window_id].factors.composite

        composite_a_ok = abs(composite_a - config["expected_composite_a"]) < _TULANA_SCORE_EPSILON
        composite_b_ok = abs(composite_b - config["expected_composite_b"]) < _TULANA_SCORE_EPSILON
        expected_first = (
            config["window_a"].window_id
            if config["expected_composite_a"] >= config["expected_composite_b"]
            else config["window_b"].window_id
        )
        rank_order_ok = ranked[0].window.window_id == expected_first
        rank_failures = []
        if not composite_a_ok:
            rank_failures.append(
                f"composite_a={composite_a!r}, expected {config['expected_composite_a']!r}"
            )
        if not composite_b_ok:
            rank_failures.append(
                f"composite_b={composite_b!r}, expected {config['expected_composite_b']!r}"
            )
        if not rank_order_ok:
            rank_failures.append(
                f"rank #1 was {ranked[0].window.window_id!r}, expected {expected_first!r}"
            )
        _add_check(
            checks, failures, "forensic_composite_and_rank_order",
            composite_a_ok and composite_b_ok and rank_order_ok,
            "; ".join(rank_failures),
            composite_a=composite_a, composite_b=composite_b,
        )
    except Exception as exc:
        _add_check(checks, failures, "forensic_composite_and_rank_order", False,
                    f"rank_windows failed: {exc}", error=str(exc))
        return _aggregate(checks, failures)

    # Check 3: compare() picks the same winner via the same decisive factor —
    # a second, independent code path over the identical two windows, proving
    # the two entry points (rank_windows vs compare) agree with each other and
    # with the pinned FORENSIC expectation, not just internally self-consistent.
    try:
        from services.ka_tulana.ranker import KaTulanaService

        svc = KaTulanaService()
        verdict = svc.compare(
            config["window_a"], config["window_b"], reference_date=config["reference_date"]
        )
        winner_ok = verdict.winner.window_id == config["expected_winner_window_id"]
        decisive_ok = verdict.decisive_factor == config["expected_decisive_factor"]
        compare_failures = []
        if not winner_ok:
            compare_failures.append(
                f"winner={verdict.winner.window_id!r}, expected {config['expected_winner_window_id']!r}"
            )
        if not decisive_ok:
            compare_failures.append(
                f"decisive_factor={verdict.decisive_factor!r}, expected {config['expected_decisive_factor']!r}"
            )
        _add_check(
            checks, failures, "forensic_compare_verdict",
            winner_ok and decisive_ok,
            "; ".join(compare_failures),
            winner=verdict.winner.window_id, decisive_factor=verdict.decisive_factor,
        )
    except Exception as exc:
        _add_check(checks, failures, "forensic_compare_verdict", False,
                    f"compare failed: {exc}", error=str(exc))

    return _aggregate(checks, failures)
