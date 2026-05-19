"""
ayanamsha.py — Ayanamsha management for panchang_engine.

Lahiri is the Indian government's official ayanamsha (1955 Calendar Reform Committee)
and is what Drik Panchang uses by default. PROJECT DEFAULT — overridable per call
only via explicit set_ayanamsha().

Supported modes: lahiri, raman, krishnamurti, true_chitra_paksha.
"""
import swisseph as swe
from .exceptions import AyanamshaError

# Project default ayanamsha. All computations use this unless overridden.
DEFAULT_AYANAMSHA = "lahiri"

# Mapping of supported ayanamsha names to swisseph constants
_AYANAMSHA_MAP = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
    "true_chitra_paksha": swe.SIDM_TRUE_CITRA,  # swisseph spells it CITRA
}


def set_ayanamsha(mode: str = DEFAULT_AYANAMSHA) -> None:
    """
    Set the sidereal mode (ayanamsha) for all subsequent swisseph computations.

    Args:
        mode: One of "lahiri" (default), "raman", "krishnamurti",
              "true_chitra_paksha". Case-sensitive.

    Raises:
        AyanamshaError: If mode is not one of the supported values.

    Note:
        swisseph maintains global state. This must be called before any
        sidereal longitude computation. panchang_engine always calls this
        at the start of compute_panchang() so callers do not need to manage it.
    """
    if mode not in _AYANAMSHA_MAP:
        supported = ", ".join(sorted(_AYANAMSHA_MAP.keys()))
        raise AyanamshaError(
            f"Unsupported ayanamsha mode '{mode}'. "
            f"Supported: {supported}. "
            f"Project default is '{DEFAULT_AYANAMSHA}' (Lahiri, Indian Govt 1955)."
        )
    swe.set_sid_mode(_AYANAMSHA_MAP[mode])


def get_ayanamsha_value(jd_ut: float) -> float:
    """
    Return the ayanamsha value (degrees) for the currently-set mode at the
    given Julian Day (UT).

    Args:
        jd_ut: Julian Day, Universal Time.

    Returns:
        Ayanamsha in decimal degrees. For Lahiri at J2000 (jd_ut=2451545.0)
        this is approximately 23.85°.

    Raises:
        AyanamshaError: If swisseph returns an error.
    """
    try:
        val = swe.get_ayanamsa_ut(jd_ut)
        return float(val)
    except Exception as exc:
        raise AyanamshaError(
            f"Failed to compute ayanamsha at JD={jd_ut}: {exc}"
        ) from exc
