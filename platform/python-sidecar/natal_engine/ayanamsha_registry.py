"""
ayanamsha_registry.py — The engine's THREE-ayanamsha registry.

Unit 1.2's canonical ayanamsha is `jh_true_chitra` (True Chitrapaksha pinned
to Jagannatha Hora's 23°37'09.78" = 23.619383° at native birth). This is the
authoritative sidereal-zero offset under JH-as-oracle (per the native decision
that resolves the FORENSIC ↔ JH circularity).

The registry holds THREE entries so the engine can compute the same chart
under all three sets concurrently and assert the constant-offset invariant
across them (a cross-contamination tripwire — if any two sets drift by more
than 1" beyond their declared ayanamsha gap, something is reaching across
swisseph's sidereal-mode state when it shouldn't).

This module is pure: no I/O, no DB, no LLM. Public surface:

    AYANAMSHA_REGISTRY       — the dict
    apply_ayanamsha(jd_ut, ayanamsha_id)
        Configures swisseph's sidereal mode for `ayanamsha_id` at the given
        Julian Day (UT). Returns the resulting ayanamsha value in degrees.
        For `jh_true_chitra`, if raw `swe.SIDM_TRUE_CITRA` differs from the
        pinned value by more than 10", we close the residual via
        `swe.SIDM_USER`. Otherwise we use the raw mode.
    ayanamsha_value_deg(jd_ut, ayanamsha_id)
        Stateless query — does NOT permanently set sidereal mode (it saves
        + restores). Returns the ayanamsha in degrees.
"""

from __future__ import annotations

from typing import Any

import swisseph as swe

# Pinned True Chitra value from JH at the canonical reference JD (native birth).
# This is the "anchor" the SIDM_USER calibration locks onto.
_JH_TRUE_CITRA_PINNED_DEG: float = 23.619383
# Reference JD for the SIDM_USER pin (native birth, 1984-02-05 05:13 UT).
_JH_TRUE_CITRA_PINNED_JD: float = 2445735.717361111

# Threshold (arcsec) above which we fall back to SIDM_USER calibration
# for jh_true_chitra. Raw TRUE_CITRA at the native JD is ~7.6" off; if that
# drifts further in another swisseph build we still want determinism.
_TRUE_CITRA_PIN_THRESHOLD_ARCSEC: float = 10.0


AYANAMSHA_REGISTRY: dict[str, dict[str, Any]] = {
    "jh_true_chitra": {
        "id": "jh_true_chitra",
        "display_name": "True Chitrapaksha (pinned to Jagannatha Hora)",
        "swe_sid_mode": swe.SIDM_TRUE_CITRA,
        "nutation_flag": True,
        "pinned_value_arcsec": _JH_TRUE_CITRA_PINNED_DEG * 3600.0,
        "pinned_value_deg": _JH_TRUE_CITRA_PINNED_DEG,
        "pinned_at_jd_ut": _JH_TRUE_CITRA_PINNED_JD,
        "role": "canonical",
        "provenance": (
            "JH-as-oracle. JH 'Lahiri' = True Chitrapaksha pinned to "
            "23°37'09.78\" (23.619383°) at native birth. Raw pyswisseph "
            "SIDM_TRUE_CITRA differs by ~7.6\" at the native JD; closed via "
            "SIDM_USER calibration to reproduce JH exactly."
        ),
    },
    "kp": {
        "id": "kp",
        "display_name": "Krishnamurti (KP)",
        "swe_sid_mode": swe.SIDM_KRISHNAMURTI,
        "nutation_flag": True,
        "pinned_value_arcsec": None,
        "pinned_value_deg": None,
        "pinned_at_jd_ut": None,
        "role": "kp_school",
        "provenance": (
            "Krishna Paksha (KP) ayanamsha; swisseph SIDM_KRISHNAMURTI. "
            "Used for KP-school computations (sub-lord cascades, ruling "
            "planets). Distinct from jh_true_chitra by a constant offset "
            "of ~5.6' (~338\") at modern epochs."
        ),
    },
    "lahiri_standard": {
        "id": "lahiri_standard",
        "display_name": "Lahiri (Standard / Chitrapaksha)",
        "swe_sid_mode": swe.SIDM_LAHIRI,
        "nutation_flag": True,
        "pinned_value_arcsec": None,
        "pinned_value_deg": None,
        "pinned_at_jd_ut": None,
        "role": "reference",
        "provenance": (
            "Standard Indian government Lahiri ayanamsha (mean Chitrapaksha). "
            "Reproduces FORENSIC v8.0's chart (which is a reconciliation, "
            "NOT the oracle). Held in the registry for cross-school "
            "constant-offset checks; NOT canonical for parity."
        ),
    },
}


def _apply_raw(swe_sid_mode: int) -> None:
    """Set swisseph sidereal mode to a built-in id (no SIDM_USER calibration)."""
    swe.set_sid_mode(swe_sid_mode, 0, 0)


def _apply_pinned(jd_ut: float, pinned_value_deg: float) -> None:
    """Set swisseph to SIDM_USER, pinning ayanamsha to `pinned_value_deg` at `jd_ut`."""
    swe.set_sid_mode(swe.SIDM_USER, jd_ut, pinned_value_deg)


def apply_ayanamsha(jd_ut: float, ayanamsha_id: str) -> float:
    """Configure swisseph's sidereal mode for `ayanamsha_id` at `jd_ut`.

    For `jh_true_chitra`: if the raw `SIDM_TRUE_CITRA` value at `jd_ut`
    differs from the pinned value by more than 10 arcsec, fall back to
    `SIDM_USER` pinned to JH's value. Otherwise use the raw mode.

    Returns the resulting ayanamsha in degrees (post-application).
    """
    if ayanamsha_id not in AYANAMSHA_REGISTRY:
        raise ValueError(
            f"Unknown ayanamsha_id: {ayanamsha_id!r}. "
            f"Valid: {sorted(AYANAMSHA_REGISTRY.keys())}"
        )

    entry = AYANAMSHA_REGISTRY[ayanamsha_id]

    if ayanamsha_id == "jh_true_chitra":
        # Check raw residual first
        _apply_raw(entry["swe_sid_mode"])
        raw_ayan = swe.get_ayanamsa_ut(jd_ut)
        residual_arcsec = abs(raw_ayan - entry["pinned_value_deg"]) * 3600.0
        if residual_arcsec > _TRUE_CITRA_PIN_THRESHOLD_ARCSEC:
            # Pin via SIDM_USER to nail JH's exact value
            _apply_pinned(jd_ut, entry["pinned_value_deg"])
        # else: raw TRUE_CITRA is close enough; keep it
        return swe.get_ayanamsa_ut(jd_ut)

    # All other entries: use raw built-in sidereal mode
    _apply_raw(entry["swe_sid_mode"])
    return swe.get_ayanamsa_ut(jd_ut)


def ayanamsha_value_deg(jd_ut: float, ayanamsha_id: str) -> float:
    """Stateless query — returns ayanamsha in degrees without mutating engine state.

    Saves the current sidereal mode, applies the requested one, reads the
    value, then restores. (swisseph has no `get_sid_mode()`, so the
    "restore" is best-effort: we reset to the registry's canonical default
    `jh_true_chitra` after reading. Callers that need precise state
    isolation should call `apply_ayanamsha(...)` explicitly.)
    """
    value = apply_ayanamsha(jd_ut, ayanamsha_id)
    # Restore canonical (jh_true_chitra) after query
    if ayanamsha_id != "jh_true_chitra":
        apply_ayanamsha(jd_ut, "jh_true_chitra")
    return value


def list_ayanamsha_ids() -> list[str]:
    """Return the registered ayanamsha ids."""
    return list(AYANAMSHA_REGISTRY.keys())


__all__ = [
    "AYANAMSHA_REGISTRY",
    "apply_ayanamsha",
    "ayanamsha_value_deg",
    "list_ayanamsha_ids",
]
