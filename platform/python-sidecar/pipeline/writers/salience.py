"""
salience.py — MARSYS-JIS G4-01
Salience formula v1: deterministic_strength, verification_certainty, computed_salience.
"""

SALIENCE_FORMULA_VERSION = "v1"


def deterministic_strength(
    orb_tightness: float,
    shadbala_rank: float,
    dignity_score: float,
) -> float:
    """
    orb_tightness: 0.0-1.0 (1.0 = exact, 0.0 = at max orb)
    shadbala_rank: 0.0-1.0 (normalized rank among 9 grahas; 1.0 = strongest)
    dignity_score: 0.0-1.0 (exaltation=1.0, debilitation=0.0, etc.)
    Returns 0.0-1.0
    """
    orb_tightness = max(0.0, min(1.0, float(orb_tightness)))
    shadbala_rank = max(0.0, min(1.0, float(shadbala_rank)))
    dignity_score = max(0.0, min(1.0, float(dignity_score)))
    return 0.4 * orb_tightness + 0.3 * shadbala_rank + 0.3 * dignity_score


def verification_certainty(source_corroboration_count: int) -> float:
    """
    source_corroboration_count: number of distinct classical texts mentioning this signal
    Returns 0.0-1.0 (asymptotic: 1 source=0.5, 2=0.75, 3=0.875, ...)
    """
    if source_corroboration_count <= 0:
        return 0.25
    return 1.0 - (0.5 ** source_corroboration_count)


def computed_salience(
    deterministic_str: float,
    verification_cert: float,
    dasha_proximity: float = 0.5,       # 0.0-1.0; 1.0 = currently in this period
    house_weight: float = 0.5,          # 0.0-1.0; angular houses=1.0, cadent=0.3
    ashtakavarga_support: float = 0.5,  # 0.0-1.0; normalized SAV score at graha
) -> float:
    """Final salience score 0.0-1.0"""
    deterministic_str = max(0.0, min(1.0, float(deterministic_str)))
    verification_cert = max(0.0, min(1.0, float(verification_cert)))
    dasha_proximity = max(0.0, min(1.0, float(dasha_proximity)))
    house_weight = max(0.0, min(1.0, float(house_weight)))
    ashtakavarga_support = max(0.0, min(1.0, float(ashtakavarga_support)))

    base = 0.5 * deterministic_str + 0.3 * verification_cert
    modifiers = (
        0.1 * dasha_proximity
        + 0.05 * house_weight
        + 0.05 * ashtakavarga_support
    )
    return min(1.0, base + modifiers)
