"""
Canonical ayanamsha id -> PyJHora ayanamsa-mode string.

PyJHora drives sidereal mode via `drik.set_ayanamsa_mode(<MODE_STRING>)` rather
than raw Swiss-Ephemeris integer constants. The map below resolves the five
canonical pipeline ids to PyJHora's mode keys (see
const.available_ayanamsa_modes in PyJHora 4.8.6).

For provenance / cross-reference the underlying Swiss-Ephemeris SIDM integer is
also recorded.
"""
from __future__ import annotations

# canonical_id -> (pyjhora_mode_string, swisseph_sidm_int)
AYANAMSHA_MAP = {
    "lahiri": ("LAHIRI", 1),               # SE_SIDM_LAHIRI
    "true_chitra": ("TRUE_CITRA", 27),     # SE_SIDM_TRUE_CITRA
    "kp": ("KP", 5),                       # SE_SIDM_KRISHNAMURTI
    "raman": ("RAMAN", 3),                 # SE_SIDM_RAMAN
    "surya_siddhanta": ("SURYASIDDHANTA", 21),  # SE_SIDM_SURYASIDDHANTA
}

DEFAULT_AYANAMSHA = "lahiri"


def resolve_mode(ayanamsha_id: str | None) -> tuple[str, int]:
    """Return (pyjhora_mode_string, swisseph_sidm_int) for a canonical id.

    Unknown / None falls back to lahiri (the pipeline default).
    """
    key = (ayanamsha_id or DEFAULT_AYANAMSHA).lower()
    return AYANAMSHA_MAP.get(key, AYANAMSHA_MAP[DEFAULT_AYANAMSHA])
