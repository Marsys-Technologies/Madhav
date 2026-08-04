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
#
# Two vocabularies reach this map and BOTH must resolve:
#   1. pyjhora_adapter-native short ids ("lahiri", "kp", "surya_siddhanta", ...)
#      — used once ga_positions_writer.CANONICAL_AYANAMSHAS has already
#      translated the A3 canonical id to the adapter id.
#   2. A3 §4 canonical ids ("lahiri_chitrapaksha", "krishnamurti",
#      "surya_siddhanta_classical", ...) — passed straight through by callers
#      that never went through that translation step, e.g.
#      ga_dashas_writer.AYANAMSHAS. Prior to this fix "krishnamurti" and
#      "surya_siddhanta_classical" were absent from the map entirely and
#      silently resolved to the lahiri default via the .get() fallback below
#      — corrupting every KP / Surya Siddhanta dasha build with Lahiri
#      positions. See DEFECT_NIGHT_LEDGER (Track A1, 2026-08-04).
AYANAMSHA_MAP = {
    # pyjhora_adapter-native keys
    "lahiri": ("LAHIRI", 1),               # SE_SIDM_LAHIRI
    "true_chitra": ("TRUE_CITRA", 27),     # SE_SIDM_TRUE_CITRA
    "kp": ("KP", 5),                       # SE_SIDM_KRISHNAMURTI
    "raman": ("RAMAN", 3),                 # SE_SIDM_RAMAN
    "surya_siddhanta": ("SURYASIDDHANTA", 21),  # SE_SIDM_SURYASIDDHANTA
    # A3 §4 canonical ids (must resolve identically to their adapter-id
    # counterparts above)
    "lahiri_chitrapaksha": ("LAHIRI", 1),
    "krishnamurti": ("KP", 5),
    "surya_siddhanta_classical": ("SURYASIDDHANTA", 21),
}

DEFAULT_AYANAMSHA = "lahiri"


def resolve_mode(ayanamsha_id: str | None) -> tuple[str, int]:
    """Return (pyjhora_mode_string, swisseph_sidm_int) for a canonical id.

    `None` resolves to lahiri (the pipeline default) — this is the only
    silent fallback. Any other, non-empty id that isn't a recognized key
    RAISES: silently substituting a different ayanamsha here would corrupt
    the sidereal computation with no signal that anything went wrong (the
    exact failure mode this map previously had for 'krishnamurti' and
    'surya_siddhanta_classical').
    """
    if ayanamsha_id is None:
        return AYANAMSHA_MAP[DEFAULT_AYANAMSHA]
    key = ayanamsha_id.lower()
    try:
        return AYANAMSHA_MAP[key]
    except KeyError:
        raise ValueError(
            f"Unknown ayanamsha_id {ayanamsha_id!r}; expected one of "
            f"{sorted(AYANAMSHA_MAP)}"
        ) from None
