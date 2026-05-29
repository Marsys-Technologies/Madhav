"""
tara_chandra_vimsh.py — G22/G23/G24 transit-strength reference tables
====================================================================
G22  TARA_BALA_MATRIX   27×27  natal_nak × transit_nak → tara class
G23  CHANDRA_BALA_MATRIX 12×12  natal_sign × transit_sign → favorability
G24  VIMSHOTTARI_START   27-entry  nakshatra → starting dasha lord + years

All indices are 1-based (nakshatras 1-27, signs 1-12).
Classical sources: BPHS Muhurta/Transit chapters; Phaladeepika ch.26.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# G22 — Tara Bala
# ---------------------------------------------------------------------------

# Nine tara names in order (index 0 = count 1)
TARA_CLASSES: list[str] = [
    "janma",    # 1
    "sampat",   # 2
    "vipat",    # 3
    "kshema",   # 4
    "pratyak",  # 5  (also called Pratyari)
    "sadhaka",  # 6
    "vadha",    # 7
    "mitra",    # 8
    "atimitra", # 9
]

TARA_BENEFIC: frozenset[str] = frozenset({
    "sampat", "kshema", "sadhaka", "mitra", "atimitra"
})

TARA_MALEFIC: frozenset[str] = frozenset({
    "janma", "vipat", "pratyak", "vadha"
})


def _build_tara_bala_matrix() -> dict[int, dict[int, str]]:
    """Build 27×27 tara bala lookup (1-based indices)."""
    matrix: dict[int, dict[int, str]] = {}
    for natal in range(1, 28):
        row: dict[int, str] = {}
        for transit in range(1, 28):
            # Count from natal to transit (1-based, wraps at 27)
            count = ((transit - natal) % 27) + 1
            tara_index = (count - 1) % 9
            row[transit] = TARA_CLASSES[tara_index]
        matrix[natal] = row
    return matrix


TARA_BALA_MATRIX: dict[int, dict[int, str]] = _build_tara_bala_matrix()


def get_tara_bala(natal_nakshatra: int, transit_nakshatra: int) -> str:
    """Return tara class string for the natal/transit nakshatra pair.

    Args:
        natal_nakshatra:   Natal Moon nakshatra (1-27).
        transit_nakshatra: Transit planet nakshatra (1-27).

    Returns:
        One of the nine tara class strings from TARA_CLASSES.
    """
    if not (1 <= natal_nakshatra <= 27):
        raise ValueError(f"natal_nakshatra must be 1-27, got {natal_nakshatra}")
    if not (1 <= transit_nakshatra <= 27):
        raise ValueError(f"transit_nakshatra must be 1-27, got {transit_nakshatra}")
    return TARA_BALA_MATRIX[natal_nakshatra][transit_nakshatra]


def is_tara_benefic(tara_class: str) -> bool:
    """Return True if *tara_class* is classically benefic."""
    return tara_class in TARA_BENEFIC


# ---------------------------------------------------------------------------
# G23 — Chandra Bala
# ---------------------------------------------------------------------------

# Classical position (1-12) → favorability mapping
CHANDRA_CLASS_MAP: dict[int, str] = {
    1:  "favorable",
    2:  "neutral",
    3:  "favorable",
    4:  "neutral",
    5:  "neutral",
    6:  "unfavorable",
    7:  "favorable",
    8:  "neutral",
    9:  "neutral",
    10: "neutral",
    11: "favorable",
    12: "unfavorable",
}


def _build_chandra_bala_matrix() -> dict[int, dict[int, str]]:
    """Build 12×12 chandra bala lookup (1-based sign indices)."""
    matrix: dict[int, dict[int, str]] = {}
    for natal in range(1, 13):
        row: dict[int, str] = {}
        for transit in range(1, 13):
            count = ((transit - natal) % 12) + 1
            row[transit] = CHANDRA_CLASS_MAP[count]
        matrix[natal] = row
    return matrix


CHANDRA_BALA_MATRIX: dict[int, dict[int, str]] = _build_chandra_bala_matrix()


def get_chandra_bala(natal_moon_sign: int, transit_moon_sign: int) -> str:
    """Return 'favorable', 'neutral', or 'unfavorable' chandra bala.

    Args:
        natal_moon_sign:   Natal Moon rashi (1-12, Aries=1).
        transit_moon_sign: Transit Moon rashi (1-12).

    Returns:
        'favorable' | 'neutral' | 'unfavorable'
    """
    if not (1 <= natal_moon_sign <= 12):
        raise ValueError(f"natal_moon_sign must be 1-12, got {natal_moon_sign}")
    if not (1 <= transit_moon_sign <= 12):
        raise ValueError(f"transit_moon_sign must be 1-12, got {transit_moon_sign}")
    return CHANDRA_BALA_MATRIX[natal_moon_sign][transit_moon_sign]


# ---------------------------------------------------------------------------
# G24 — Vimshottari Dasha Starting Table
# ---------------------------------------------------------------------------

# Dasha sequence with years (total = 120)
_DASHA_SEQUENCE: list[tuple[str, int]] = [
    ("ketu",    7),
    ("venus",  20),
    ("sun",     6),
    ("moon",   10),
    ("mars",    7),
    ("rahu",   18),
    ("jupiter",16),
    ("saturn", 19),
    ("mercury",17),
]

# nakshatra 1-27 mapped to dasha sequence index (repeating cycle of 9)
# Nakshatra 1 (Ashwini) → Ketu (index 0)
# Nakshatra 2 (Bharani) → Venus (index 1) …

def _build_vimshottari_start() -> dict[int, dict]:
    """Build 27-entry Vimshottari starting dasha table."""
    table: dict[int, dict] = {}
    for nak in range(1, 28):
        seq_index = (nak - 1) % 9  # cycles every 9 nakshatras
        lord, years = _DASHA_SEQUENCE[seq_index]
        table[nak] = {"lord": lord, "years": years}
    return table


VIMSHOTTARI_START: dict[int, dict] = _build_vimshottari_start()


def get_vimshottari_start(nakshatra: int) -> dict:
    """Return {'lord': str, 'years': int} for nakshatra 1-27.

    Args:
        nakshatra: Nakshatra number (1-27).

    Returns:
        dict with keys 'lord' (dasha lord name, lowercase) and
        'years' (full dasha duration in years).
    """
    if not (1 <= nakshatra <= 27):
        raise ValueError(f"nakshatra must be 1-27, got {nakshatra}")
    return VIMSHOTTARI_START[nakshatra]


def compute_vimshottari_elapsed_fraction(nakshatra: int, pada: int) -> float:
    """Return fraction of the starting dasha elapsed based on pada (1-4).

    Classical rule: each nakshatra spans 13°20'; each pada = 3°20' (25 %).
    Moon at pada=1 means 0% elapsed; pada=4 means 75% elapsed.
    The fraction represents the proportion of the starting dasha already
    consumed at birth.

    Args:
        nakshatra: Nakshatra number (1-27).
        pada:      Pada number (1-4).

    Returns:
        float in [0.0, 0.75]; 0.0 for pada 1 (just entered), 0.75 for pada 4.
    """
    if not (1 <= nakshatra <= 27):
        raise ValueError(f"nakshatra must be 1-27, got {nakshatra}")
    if not (1 <= pada <= 4):
        raise ValueError(f"pada must be 1-4, got {pada}")
    return (pada - 1) * 0.25


# ---------------------------------------------------------------------------
# Module-level integrity assertion (runs at import)
# ---------------------------------------------------------------------------
assert len(TARA_BALA_MATRIX) == 27, "TARA_BALA_MATRIX must have 27 natal keys"
assert all(len(v) == 27 for v in TARA_BALA_MATRIX.values()), \
    "Each natal key must have 27 transit entries"
assert len(CHANDRA_BALA_MATRIX) == 12, "CHANDRA_BALA_MATRIX must have 12 natal keys"
assert all(len(v) == 12 for v in CHANDRA_BALA_MATRIX.values()), \
    "Each natal key must have 12 transit entries"
assert len(VIMSHOTTARI_START) == 27, "VIMSHOTTARI_START must have 27 entries"
assert sum(v["years"] for v in VIMSHOTTARI_START.values()) == 120 * 3, \
    "Total years across 27 entries must equal 360 (120 × 3 cycles)"
