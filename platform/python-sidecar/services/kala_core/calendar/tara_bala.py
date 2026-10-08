"""PG67 v.13 Tāra-bala classification without a weighted score or attenuation."""
from __future__ import annotations

from dataclasses import dataclass

_NAMES = ("janma", "sampat", "vipat", "kshema", "pratyari", "sadhaka", "vadha", "mitra", "ati_mitra")
_INAUSPICIOUS = {3, 5, 7}

# PG67 v.13 preserves a dāna alongside the adverse tārā.  It is returned as
# evidence for a consumer to present, never converted into a score or an
# automatic cancellation.
_REMEDIES = {
    "vipat": "dāna prescribed for Vipat tārā (PG67 v.13)",
    "pratyari": "dāna prescribed for Pratyari tārā (PG67 v.13)",
    "vadha": "dāna prescribed for Vadha tārā (PG67 v.13)",
}

# This is deliberately a classification table, not a weight table.  The
# previous panchang_engine / finder path applies numerical attenuation and is
# retained only for legacy callers until the election view moves to this core.
TARA_BALA_TABLE_V1 = {
    "locator": "PG67:C1 v.13",
    "retired_models": (
        "panchang_engine.tara_bala score plus cycle attenuation",
        "muhurat.finder weighted native overlay",
        "gochara_v3 w23 transit-intensity modifier",
    ),
    "rule": "first-cycle adverse stars; specified thirds in cycle two; cycle three auspicious",
}

# The previous implementations share the nine-name cycle, but disagree with
# PG67 about how that cycle affects a muhurta: they produce scores, modifiers,
# or testimony and do not encode the second-cycle thirds / third-cycle release.
# Keep that disagreement explicit so no legacy table can silently regain
# authority while consumers move to this location-required calendar core.
TARA_BALA_RECONCILIATION_V1 = {
    "selected_rule": "PG67:C1 v.13",
    "retired_sources": (
        "ka_sangam._TARA_SCORES",
        "gochara_v3.w23_tara_bala",
        "gochara_rules.p6",
        "gochara_grammar.panchang_engine_adapter",
    ),
    "disagreements": {
        "ka_sangam._TARA_SCORES": "numeric score repeats each nine-star cycle",
        "gochara_v3.w23_tara_bala": "transit modifier repeats each nine-star cycle",
        "gochara_rules.p6": "testimony class repeats each nine-star cycle",
        "gochara_grammar.panchang_engine_adapter": "attenuated score repeats each nine-star cycle",
    },
}


@dataclass(frozen=True)
class TaraAssessment:
    tara_position: int
    cycle: int
    tara_name: str
    third: int | None
    status: str
    remedy: str | None
    locator: str = "PG67 v.13"


def assess_tara_bala(birth_nakshatra_id: int, current_nakshatra_id: int, *, elapsed_fraction: float = 0.0) -> TaraAssessment:
    """Classify Tāra-bala using the three-cycle rule stated in PG67 v.13.

    The second cycle only condemns the first/middle/last third of vipat,
    pratyari and vadha respectively; no numeric attenuation is produced.
    """
    if not 1 <= birth_nakshatra_id <= 27 or not 1 <= current_nakshatra_id <= 27:
        raise ValueError("nakshatra ids must be in 1..27")
    if not 0.0 <= elapsed_fraction < 1.0:
        raise ValueError("elapsed_fraction must be in [0, 1)")
    position = (current_nakshatra_id - birth_nakshatra_id) % 27 + 1
    cycle = (position - 1) // 9 + 1
    within_cycle = (position - 1) % 9 + 1
    third = int(elapsed_fraction * 3) + 1
    status = "auspicious"
    if cycle == 1 and within_cycle in _INAUSPICIOUS:
        status = "inauspicious"
    elif cycle == 2 and ((within_cycle == 3 and third == 1) or (within_cycle == 5 and third == 2) or (within_cycle == 7 and third == 3)):
        status = "inauspicious"
    tara_name = _NAMES[within_cycle - 1]
    remedy = _REMEDIES.get(tara_name) if status == "inauspicious" else None
    return TaraAssessment(position, cycle, tara_name, third, status, remedy)
