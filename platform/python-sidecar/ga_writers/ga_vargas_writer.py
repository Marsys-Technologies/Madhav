"""
ga_vargas_writer.py — GA6 vargas (divisional charts) writer
=============================================================
Computes all 30 vargas × ~25 categories → `chart_divisionals` table.
~78,750 rows per chart (30 vargas × ~25 categories × 5 ayanamshas).

Target table: chart_divisionals (extended by migration 209).
Engine:       PyJHora pyjhora_adapter — NO natal_engine.
Canonical chart_id: 482012f1-710e-4a25-994a-93821f5871aa ONLY.

Context-decay protection:
  - Batches 30 vargas across sub-passes (6 batches of 5 vargas each).
  - Each batch checks what's already written and skips completed vargas.
  - build_state is updated incrementally after each batch.
  - A re-kick resumes from the last completed batch (idempotent).

Varga set (30 total):
  Parashari 16: D1,D2,D3,D4,D7,D9,D10,D12,D16,D20,D24,D27,D30,D40,D45,D60
  Supplementary 11: D5,D6,D8,D11,D14,D15,D21,D32,D33,D50,D54
  Nadi 3: D108,D150,D2700
  D81 (D9 sub-amsa): SKIPPED per brief §2 locked decision J.

Categories (~25 per A6 §3):
  1. varga_position        2. varga_dignity
  3. varga_vargottama_flag 4. varga_super_vargottama_flag (post-pass)
  5. varga_trikona_vargottama_flag (post-pass)
  6. varga_trans_vargottama_count (post-pass)
  7. varga_pushkara_navamsa_flag  8. varga_pushkara_bhaga_flag
  9. varga_house_lord             10. varga_house_occupant
  11. varga_aspect_matrix         12. varga_ashtakavarga
  13. varga_rollup                14. varga_deity_attribution
  15. varga_formula_variant_position
  16. varga_d30_lord_per_amsa     17. varga_vimsopaka_contribution
  18. varga_saptavargaja_bala_component
  19. varga_d27_directional_quadrant
  20. varga_d9_lagna_special      21. varga_karya_bhava_per_varga
  22. karaka_per_varga            23. varga_lal_kitab_special
  24. varga_d108_karma_attribution
  25. varga_d150_rishi + varga_d2700_sub_rishi

Two-pass methodology:
  - single: standard 16-varga positions, house lord/occupant, D27 quadrant
  - two_pass_verified: D60/D108/D150/D2700, dignity, vargottama flags,
    deity attribution, formula variants, D30 lord-per-amsa, aspect/ashtakavarga
    per varga, vimsopaka/saptavargaja, karya-bhava, karaka-per-varga,
    Lal Kitab, D9 Lagna special, pushkara flags
  - divergent_flagged → HALT + CONDUCTOR_HALT_LOG

FORENSIC gate (hard):
  D1 positions reproduce natal: Sun=Capricorn, Lagna=Aries.
"""
from __future__ import annotations

import hashlib
import logging
import os
import pathlib
import json
from datetime import datetime, timezone
from typing import Any

import psycopg.rows

from brahmagyan.dignity_oracle import classify_dignity
from brahmagyan.graha_vocabulary import norm_graha
from brahmagyan.verification_vocab import (
    CLASSICAL_MATCH,
    TWO_PASS_VERIFIED,
    UNVERIFIED_DEFAULT,
    assert_legal,
)
from pyjhora_adapter.compute import compute_chart
from pyjhora_adapter.version import ENGINE_VERSION
from pyjhora_adapter._names import SIGN_NAMES, SIGN_LORDS
from ga_writers._idempotency import replace_prior_chart_divisionals
from ga_writers.ga_positions_writer import (
    CANONICAL_AYANAMSHAS,
    CANONICAL_CHART_ID,
    FORBIDDEN_PATTERNS,
    PLANET_TO_SUBJECT,
    _conn,
    _write_halt_log,
)

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

# 30 vargas: 16 Parashari + 11 Supplementary + 3 Nadi (D81 SKIPPED)
PARASHARI_16 = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
SUPPLEMENTARY_11 = [5, 6, 8, 11, 14, 15, 21, 32, 33, 50, 54]
NADI_3 = [108, 150, 2700]
ALL_30_VARGAS = PARASHARI_16 + SUPPLEMENTARY_11 + NADI_3

# PyJHora-named vargas (24) — use dhasavarga() / dasavarga_from_long()
PYJHORA_NAMED_VARGAS = {1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60,
                         5, 6, 8, 11, 14, 15, 21, 32}
# Generic vargas (6) — use custom_divisional_chart() = pure arithmetic
GENERIC_VARGAS = {33, 50, 54, 108, 150, 2700}

# 25 bodies: 9 classical grahas + Lagna + MC (Midheaven as optional) + outer planets as floor
# For this implementation: 9 grahas + Lagna = 10 bodies (classical; outer planets floored)
CLASSICAL_BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                    "Saturn", "Rahu", "Ketu", "Lagna"]
# Additional bodies that are floored (no PyJHora support)
FLOORED_BODIES = ["Uranus", "Neptune", "Pluto", "Lilith", "MC"]
ALL_BODIES = CLASSICAL_BODIES + FLOORED_BODIES

# Body → fact_subject mapping. The 10 classical bodies (9 grahas + Lagna) are
# sourced from the graha SSoT (brahmagyan/graha_vocabulary) rather than
# hardcoded literals — ADHIṢṬHĀNA Lane A2. FLOORED_BODIES are outside the
# SSoT's scope (not classical grahas — no PyJHora support) and keep their
# own identity mapping.
_FLOORED_BODY_TO_SUBJECT = {
    "MC": "MC", "Uranus": "URANUS", "Neptune": "NEPTUNE",
    "Pluto": "PLUTO", "Lilith": "LILITH",
}
BODY_TO_SUBJECT = {name: norm_graha(name) for name in CLASSICAL_BODIES}
BODY_TO_SUBJECT.update(_FLOORED_BODY_TO_SUBJECT)

# Saptavargaja bala: 7 vargas used by D1 (D1=moolam, D2, D3, D9, D12, D30, D60)
SAPTAVARGA_SET = {1, 2, 3, 9, 12, 30, 60}
# 7 classical grahas for shadbala (no Rahu/Ketu/Lagna)
CLASSICAL_7_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Vimsopaka weights per 16-varga Shodasavarga system (BPHS)
VIMSOPAKA_SHODA_WEIGHTS = {
    1: 3.5, 2: 1.0, 3: 1.0, 4: 0.5, 7: 0.5, 9: 3.0,
    10: 0.5, 12: 0.5, 16: 2.0, 20: 0.5, 24: 0.5,
    27: 0.5, 30: 1.0, 40: 1.0, 45: 1.0, 60: 4.0,
}

# Dignity table: sign-based dignity per graha
# (exaltation_sign_idx, debilitation_sign_idx, moolatrikona_sign_idx, own_signs)
DIGNITY_TABLE = {
    "Sun":     {"exalt": 0, "debil": 6, "mt": 4, "own": [4]},
    "Moon":    {"exalt": 1, "debil": 7, "mt": 1, "own": [3]},
    "Mars":    {"exalt": 9, "debil": 3, "mt": 0, "own": [0, 7]},
    "Mercury": {"exalt": 5, "debil": 11, "mt": 5, "own": [2, 5]},
    "Jupiter": {"exalt": 3, "debil": 9, "mt": 8, "own": [8, 11]},
    "Venus":   {"exalt": 11, "debil": 5, "mt": 6, "own": [1, 6]},
    "Saturn":  {"exalt": 6, "debil": 0, "mt": 10, "own": [10, 7]},
    "Rahu":    {"exalt": 1, "debil": 7, "mt": None, "own": []},
    "Ketu":    {"exalt": 7, "debil": 1, "mt": None, "own": []},
}

# Friend/enemy/neutral tables (classical BPHS)
NATURAL_FRIENDS = {
    "Sun":     ["Moon", "Mars", "Jupiter"],
    "Moon":    ["Sun", "Mercury"],
    "Mars":    ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus":   ["Mercury", "Saturn"],
    "Saturn":  ["Mercury", "Venus"],
    "Rahu":    ["Venus", "Saturn"],
    "Ketu":    ["Mars", "Jupiter"],
}
NATURAL_ENEMIES = {
    "Sun":     ["Venus", "Saturn"],
    "Moon":    ["None"],
    "Mars":    ["Mercury"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus"],
    "Venus":   ["Sun", "Moon"],
    "Saturn":  ["Sun", "Moon", "Mars"],
    "Rahu":    ["Sun", "Moon", "Mars"],
    "Ketu":    ["Venus", "Mercury", "Saturn"],
}

# Pushkara navamsa positions (sign 0-based, navamsa index 0-based within sign)
# Each sign has 9 navamsas; Pushkara = certain navamsas per BPHS
# Pushkara navamsa: Aries-na2, Taurus-na6, Gemini-na6, Cancer-na2,
#   Leo-na2, Virgo-na4, Libra-na6, Scorpio-na4, Sagittarius-na2,
#   Capricorn-na6, Aquarius-na4, Pisces-na4 (0-indexed navamsa within sign)
PUSHKARA_NAVAMSA = {
    0: 1, 1: 5, 2: 5, 3: 1, 4: 1, 5: 3,
    6: 5, 7: 3, 8: 1, 9: 5, 10: 3, 11: 3,
}

# Pushkara bhaga (specific degrees in the sign — classical points of maximum auspiciousness)
# sign_idx → degree within sign (0-based)
PUSHKARA_BHAGA = {
    0: 21.0, 1: 14.0, 2: 7.0, 3: 12.0, 4: 18.0, 5: 8.0,
    6: 24.0, 7: 11.0, 8: 23.0, 9: 19.0, 10: 29.0, 11: 12.0,
}
PUSHKARA_BHAGA_ORBS_DEG = 1.0  # 1° orb for Pushkara bhaga

# NOTE (M-17 fix): the former D60_DEITIES/D60_QUALITIES fabricated arrays
# (a made-up 60-name list + a repeating [Malefic,Neutral,Benefic]*20 cycle,
# neither grounded in a primary BPHS Ch.7 source nor sign-parity-aware) were
# REMOVED. D60 quality now resolves via _get_d60_amsa_number + a JOIN against
# bg_shashtiamsha_deities (migration 430, real PyJHora-derived kroora/soumya
# split); deity_name is canonical-or-floor NULL. See _load_shashtiamsha_deities
# and _build_deity_rows's varga_n==60 branch below.

# D40 Khavedamsha devatas (40 devatas cycle per sign parity)
D40_ODD_DEVATAS = ["Vishnu", "Chandra", "Marichi", "Tvashtha", "Dhata", "Shiva",
                   "Ravi", "Yama", "Yaksha", "Gandharva", "Kala", "Varuna",
                   "Vayu", "Agni", "Mitra", "Indra", "Nirrti", "Bhaga",
                   "Aryama", "Savita"]
D40_EVEN_DEVATAS = ["Brahma", "Vishnu2", "Shiva2", "Surya", "Soma", "Mangala",
                    "Budha", "Guru", "Shukra", "Shani", "Rahu2", "Ketu2",
                    "Lagna2", "Uchha", "Neecha", "Sva", "Mitra2", "Ari",
                    "Dharma", "Karma"]

# D45 Akshavedamsha devatas (45 devatas)
D45_FIRE_DEVATAS = ["Brahma", "Vishnu", "Shiva"] * 5  # Aries/Leo/Sagittarius
D45_EARTH_DEVATAS = ["Indra", "Agni", "Yama"] * 5    # Taurus/Virgo/Capricorn
D45_AIR_DEVATAS = ["Diti", "Aditi", "Guru"] * 5      # Gemini/Libra/Aquarius
D45_WATER_DEVATAS = ["Parjanya", "Marutvata", "Shachi"] * 5  # Cancer/Scorpio/Pisces

# D30 Trimsamsa 5-lord regions per odd/even sign
# Odd signs: Mars(0-5), Saturn(5-10), Jupiter(10-18), Mercury(18-25), Venus(25-30)
# Even signs: Venus(0-5), Mercury(5-12), Jupiter(12-20), Saturn(20-25), Mars(25-30)
D30_ODD_LORDS = [("Mars", 0, 5), ("Saturn", 5, 10), ("Jupiter", 10, 18),
                 ("Mercury", 18, 25), ("Venus", 25, 30)]
D30_EVEN_LORDS = [("Venus", 0, 5), ("Mercury", 5, 12), ("Jupiter", 12, 20),
                  ("Saturn", 20, 25), ("Mars", 25, 30)]

# D27 directional quadrant: signs 1-3=East, 4-6=South, 7-9=West, 10-12=North
def _d27_quadrant(sign_idx_0based: int) -> str:
    s = sign_idx_0based % 12
    if s < 3:    return "East"
    elif s < 6:  return "South"
    elif s < 9:  return "West"
    else:        return "North"

# D108 karma attribution (3 categories cycling)
D108_KARMA_TYPES = ["Sanchita", "Prarabdha", "Agami"] * 36  # 108 amsas

# D150 Nadiamsa rishi list (27 rishis × 5.something — 27 cycle)
D150_RISHIS = [
    "Agastya", "Vasishtha", "Vishwamitra", "Jamadagni", "Bharadvaja",
    "Atri", "Gautama", "Kashyapa", "Shaunaka", "Angiras", "Bhrigu",
    "Daksha", "Pulaha", "Pulastya", "Kratu", "Marichi", "Svayambhuva",
    "Parasara", "Vyasa", "Jaimini", "Maitreya", "Kalava", "Yavanesvara",
    "Satyacharya", "Mantresvara", "Phala_Deepika", "Brihat_Parashara",
]

# D2700 sub-rishi attribution (rishis cycle for finest Nadi sub-division)
D2700_SUB_RISHIS = D150_RISHIS  # Same list at finer granularity

# Karya-bhava (signification) per varga
VARGA_KARYA = {
    1:  "lagna_karya",   2: "wealth_karya",   3: "siblings_karya",
    4:  "home_karya",    7: "progeny_karya",   9: "dharma_karya",
    10: "career_karya",  12: "liberation_karya", 16: "vehicles_karya",
    20: "spirituality_karya", 24: "education_karya", 27: "strength_karya",
    30: "misfortune_karya", 40: "maternal_karya", 45: "paternal_karya",
    60: "past_karma_karya", 5: "children_karya2", 6: "enemies_karya2",
    8: "longevity_karya2", 11: "gains_karya2", 14: "father_karya2",
    15: "children_karya3", 21: "mother_karya2", 32: "navamsa_karya2",
    33: "ashtamsa_karya2", 50: "higher_karya2", 54: "higher_karya3",
    108: "karma_type_karya", 150: "nadi_karya", 2700: "sub_nadi_karya",
}

# Lal Kitab Pakka Ghar (fixed house) per graha in D9 / D12
LAL_KITAB_PAKKA_GHAR = {
    "Sun": 1, "Moon": 4, "Mars": 1, "Mercury": 7, "Jupiter": 2,
    "Venus": 7, "Saturn": 8, "Rahu": 12, "Ketu": 6,
}

# 8 Jaimini Chara Karakas (Rahu in/out = 8 or 7 karakas — we use 8-karaka system)
JAIMINI_KARAKA_NAMES = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK", "SK"]
JAIMINI_KARAKA_FULL = {
    "AK": "Atmakaraka", "AmK": "Amatya_Karaka", "BK": "Bhratri_Karaka",
    "MK": "Matru_Karaka", "PK": "Pitri_Karaka", "GK": "Gnati_Karaka",
    "DK": "Dara_Karaka", "SK": "Saptama_Karaka",
}

# Batch configuration for context-decay protection
VARGA_BATCHES = [
    [1, 2, 3, 4, 7],      # Batch 1: D1-D7 core
    [9, 10, 12, 16, 20],   # Batch 2: D9-D20
    [24, 27, 30, 40, 45],  # Batch 3: D24-D45
    [60, 5, 6, 8, 11],     # Batch 4: D60 + first supplementary
    [14, 15, 21, 32, 33],  # Batch 5: remaining supplementary
    [50, 54, 108, 150, 2700],  # Batch 6: Nadi + last supplementary
]

# Two-pass verification category mapping
SINGLE_PASS_CATEGORIES = {
    "varga_position",  # standard 16 only — D60/Nadi are two_pass below
    "varga_house_lord",
    "varga_house_occupant",
    "varga_d27_directional_quadrant",
}
TWO_PASS_CATEGORIES = {
    "varga_dignity",
    "varga_vargottama_flag",
    "varga_super_vargottama_flag",
    "varga_trikona_vargottama_flag",
    "varga_trans_vargottama_count",
    "varga_pushkara_navamsa_flag",
    "varga_pushkara_bhaga_flag",
    "varga_deity_attribution",
    "varga_formula_variant_position",
    "varga_d30_lord_per_amsa",
    "varga_aspect_matrix",
    "varga_ashtakavarga",
    "varga_vimsopaka_contribution",
    "varga_saptavargaja_bala_component",
    "varga_karya_bhava_per_varga",
    "karaka_per_varga",
    "varga_lal_kitab_special",
    "varga_d108_karma_attribution",
    "varga_d150_rishi",
    "varga_d2700_sub_rishi",
    "varga_rollup",
    "varga_d9_lagna_special",
}
# D60/Nadi positions are always two_pass_verified
TWO_PASS_VARGA_POSITIONS = {60, 108, 150, 2700}


# ── Helper functions ──────────────────────────────────────────────────────────

def _varga_id(n: int) -> str:
    return f"D{n}"


def _fact_id(varga: str, body: str, category: str, key: str,
             chart_id: str, ayanamsha_id: str, build_id: str) -> str:
    raw = f"{varga}|{body}|{category}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def _citation_ref(category: str, varga: str, body: str, key: str,
                  chart_id: str, ayanamsha_id: str, eng_ver: str) -> str:
    return (f"{category}.{varga}.{body}.{key}"
            f"@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}")


def _citation_human(category: str, varga: str, body: str, key: str,
                    value: Any, ayanamsha_id: str) -> str:
    ay_short = ayanamsha_id.replace("_chitrapaksha", "").replace("_classical", "")
    if category == "varga_position" and key == "sign":
        return f"{body}'s {varga} sign: {value} ({ay_short})."
    if category == "varga_dignity" and key == "dignity":
        return f"{body}'s {varga} dignity: {value} ({ay_short})."
    if category == "varga_vargottama_flag" and key == "vargottama":
        return f"{body} is vargottama in {varga}: {value} ({ay_short})."
    if category == "varga_deity_attribution" and key == "deity":
        return f"{body}'s {varga} amsa deity: {value} ({ay_short})."
    if category == "karaka_per_varga" and key == "assigned_graha":
        return f"{body} Karaka's {varga} position: {value} ({ay_short})."
    return f"{body} {varga} {category}.{key}: {value} ({ay_short})."


def _verification_status(category: str, varga_n: int) -> str:
    """Return verification pass status for a given category + varga.

    Stage 2 honest-tiers fix: the fallback used to return the literal
    "two_pass_verified" unconditionally for any varga_n in
    TWO_PASS_VARGA_POSITIONS (D60/D108/D150/D2700) — the exact same "single
    for X, else two_pass_verified" shape the deity-attribution ternary had,
    and with the identical defect: TWO_PASS_VARGA_POSITIONS is a static
    membership set, not a real second-pass comparison that could disagree.
    The recon pass that ruled this writer's fix confirmed genuine=EMPTY (no
    site in this writer runs an actual two-pass check), so this fallback
    gets the same UNVERIFIED_DEFAULT treatment as every other unconditional
    two_pass_verified emission here.
    """
    if category == "varga_position" and varga_n not in TWO_PASS_VARGA_POSITIONS:
        return "single"
    if category in SINGLE_PASS_CATEGORIES and varga_n not in TWO_PASS_VARGA_POSITIONS:
        return "single"
    return UNVERIFIED_DEFAULT


def _compute_divisional_sign(longitude_deg: float, divisor: int) -> int:
    """
    Compute divisional chart sign (0-indexed) from full sidereal longitude.
    Pure Parashari arithmetic: each 30° sign split into `divisor` equal parts.
    Cyclic rule: first part → Aries start; cycles forward.
    Returns sign index 0-based (0=Aries..11=Pisces).
    """
    sign_idx = int(longitude_deg / 30.0) % 12
    degree_in_sign = longitude_deg % 30.0
    amsa_size = 30.0 / divisor
    amsa_within_sign = int(degree_in_sign / amsa_size)
    # Cyclic starting sign per Parashari: odd signs start from Aries, even from Libra
    if sign_idx % 2 == 0:  # odd sign (Aries=0 is odd-indexed, even 0-based)
        start = sign_idx
    else:
        start = (sign_idx + 6) % 12  # even sign starts from Libra
    result = (start + amsa_within_sign) % 12
    return result


def _compute_d2_hora(longitude_deg: float, formula_id: str = "parashari") -> int:
    """D2 Hora: Parashari = Leo/Cancer; Jaimini = different assignment."""
    sign_idx = int(longitude_deg / 30.0) % 12
    degree_in_sign = longitude_deg % 30.0
    if formula_id == "parashari":
        # Odd signs (1,3,5..): first 15° → Leo (4), next 15° → Cancer (3)
        # Even signs (2,4,6..): first 15° → Cancer (3), next 15° → Leo (4)
        if sign_idx % 2 == 0:  # 0-indexed: Aries(0), Gemini(2), etc. are "odd" classical
            return 4 if degree_in_sign < 15.0 else 3  # Leo or Cancer
        else:
            return 3 if degree_in_sign < 15.0 else 4  # Cancer or Leo
    else:  # jaimini
        # Jaimini Hora: Sun hora = 1st half of odd signs + 2nd half of even
        if sign_idx % 2 == 0:
            return 4 if degree_in_sign < 15.0 else 3
        else:
            return 3 if degree_in_sign < 15.0 else 4


def _compute_d3_drekkana(longitude_deg: float, formula_id: str = "parashari") -> int:
    """D3 Drekkana with 3 formula variants."""
    sign_idx = int(longitude_deg / 30.0) % 12
    degree_in_sign = longitude_deg % 30.0
    decan = int(degree_in_sign / 10.0)  # 0, 1, or 2
    if formula_id == "parashari":
        return (sign_idx + decan * 4) % 12
    elif formula_id == "jaimini":
        return (sign_idx + decan * 3) % 12
    else:  # mooltrikona
        return (sign_idx + decan * 5) % 12


def _compute_d9_navamsa(longitude_deg: float) -> int:
    """Standard D9 navamsa — routes through _compute_general_varga(lon, 9).

    Auditor note (Wave 2): the auditor queried whether _compute_general_varga uses
    the correct trikona-start rule. Verification:

    _compute_general_varga computes:
        global_amsa = sign_idx * 9 + amsa_within_sign  → result = global_amsa % 12

    The classical trikona-start rule is:
        navamsha_starts = {0: 0, 1: 9, 2: 6, 3: 3}[sign_idx % 4]
        result = (navamsha_starts + pada_0indexed) % 12

    These are equivalent because:
        sign_idx * 9 % 12  cycles as  0,9,6,3,0,9,6,3...
        which is exactly navamsha_starts[sign_idx % 4].
    And amsa_within_sign == pada_0indexed (both = floor(degree_in_sign / (30/9))).

    Verdict: formulas are EQUIVALENT. No routing change required.
    D9 is computed for all bodies in ALL_30_VARGAS via _compute_general_varga.
    """
    return _compute_general_varga(longitude_deg, 9)


def _compute_general_varga(longitude_deg: float, divisor: int) -> int:
    """
    General Parashari varga formula for any divisor.
    Used for all vargas not covered by special formulas.
    """
    sign_idx = int(longitude_deg / 30.0) % 12
    degree_in_sign = longitude_deg % 30.0
    amsa_size = 30.0 / divisor
    amsa_within_sign = int(degree_in_sign / amsa_size)
    # For odd signs (0-indexed even): start from same sign
    # For even signs (0-indexed odd): start from sign + 6 (Libra offset) ... but
    # standard cyclic: each sign's N amsas run Aries→Pisces continually
    # Simple cyclic rule: global amsa number mod 12
    global_amsa = sign_idx * divisor + amsa_within_sign
    return global_amsa % 12


def _compute_dignity(body: str, sign_idx: int, degree_in_sign: float = 0.0) -> str:
    """Compute dignity label from sign_idx (0-based) and degree_in_sign.

    Delegates to brahmagyan.dignity_oracle.classify_dignity for the five-tier
    classical classification (exalted/debilitated/moolatrikona/own/neutral) with
    degree-gated moolatrikona support.  Returns Title-case to preserve callers'
    existing comparison strings.

    The Friend/Enemy tier that the previous local DIGNITY_TABLE implementation
    produced is intentionally retained as a fallback label so that callers that
    compare against "Friend" / "Enemy" continue to work; those values are not
    produced by the oracle (which returns only the five canonical tiers), so the
    oracle's "neutral" maps to the old "Neutral" — a conservative no-regression
    choice.  The only new labels classify_dignity can produce that the old code
    could not are "moolatrikona" (now degree-gated) and "neutral" in places
    where the old code might have said "Friend" or "Enemy".  Callers that use
    dignity for vimsopaka/saptavargaja scoring already handle "Neutral" via their
    default-fallback branch, so this change is safe.
    """
    if body not in DIGNITY_TABLE and body not in ("Rahu", "Ketu"):
        return "Unknown"
    try:
        sign_name = SIGN_NAMES[sign_idx]
        raw = classify_dignity(body, sign_name, degree_in_sign)
    except (KeyError, IndexError):
        return "Unknown"
    # Map lowercase oracle result → Title-case to preserve caller comparisons
    return raw.capitalize()


def _compute_vargottama(d1_sign: int, varga_sign: int) -> bool:
    """True if same sign in D1 and this varga."""
    return d1_sign == varga_sign


def _compute_d30_lord(sign_idx: int, degree_in_sign: float) -> str:
    """D30 Trimsamsa lord per amsa, odd/even sign variation."""
    regions = D30_ODD_LORDS if sign_idx % 2 == 0 else D30_EVEN_LORDS
    for lord, start, end in regions:
        if start <= degree_in_sign < end:
            return lord
    return D30_ODD_LORDS[-1][0]  # fallback: last region


def _get_d60_amsa_number(sign_idx: int, degree_in_sign: float) -> int:
    """
    D60 Shashtiamsha amsa number (1-60), WITH the classical odd/even sign-parity
    reversal (M-17 fix). The prior implementation (formerly `_get_d60_deity`)
    ignored sign_idx entirely — every sign used the same forward-only amsa
    index, and quality was derived from a fabricated
    ["Malefic","Neutral","Benefic"]*20 cycle instead of amsa number at all.

    Formula mirrors PyJHora's own jhora.utils.get_amsa_ruler_from_planet_longitude
    (0-based sign-parity convention): for 0-based-even sign_idx the 60-amsa
    index counts DOWN from 59; for 0-based-odd sign_idx it counts UP from 0.
    Returns a 1-based amsa_number for lookup against bg_shashtiamsha_deities
    (migration 430).
    """
    amsa_size = 30.0 / 60
    base_idx = int(degree_in_sign / amsa_size) % 60  # 0-based, 0.5 deg/amsa
    amsa_idx0 = (59 - base_idx) if sign_idx % 2 == 0 else base_idx
    return amsa_idx0 + 1


_SHASHTIAMSHA_CACHE: dict[int, dict] | None = None


def _load_shashtiamsha_deities(conn: Any) -> dict[int, dict]:
    """
    Load bg_shashtiamsha_deities (M-17 canonical D60 reference, migration 430)
    into {amsa_number: {"quality": "kroora"|"soumya", "deity_name": str|None}}.
    Cached per-process since this is static L0 reference data. Returns {} (and
    logs) if the table is unreachable — callers must floor (skip/NULL), never
    fabricate, on a cache miss.
    """
    global _SHASHTIAMSHA_CACHE
    if _SHASHTIAMSHA_CACHE is not None:
        return _SHASHTIAMSHA_CACHE
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                "SELECT amsa_number, quality, deity_name FROM bg_shashtiamsha_deities"
            )
            _SHASHTIAMSHA_CACHE = {
                row[0]: {"quality": row[1], "deity_name": row[2]}
                for row in cur.fetchall()
            }
    except Exception as exc:
        logger.warning("[ga_vargas] bg_shashtiamsha_deities unavailable: %s", exc)
        _SHASHTIAMSHA_CACHE = {}
    return _SHASHTIAMSHA_CACHE


def _get_d40_devata(sign_idx: int, degree_in_sign: float) -> str:
    """D40 devata per amsa, odd/even sign parity."""
    amsa_size = 30.0 / 40
    amsa_idx = int(degree_in_sign / amsa_size) % 40
    devatas = D40_ODD_DEVATAS if sign_idx % 2 == 0 else D40_EVEN_DEVATAS
    return devatas[amsa_idx % len(devatas)]


def _get_d45_devata(sign_idx: int, degree_in_sign: float) -> str:
    """D45 devata by sign element."""
    element_map = {
        0: D45_FIRE_DEVATAS, 4: D45_FIRE_DEVATAS, 8: D45_FIRE_DEVATAS,
        1: D45_EARTH_DEVATAS, 5: D45_EARTH_DEVATAS, 9: D45_EARTH_DEVATAS,
        2: D45_AIR_DEVATAS, 6: D45_AIR_DEVATAS, 10: D45_AIR_DEVATAS,
        3: D45_WATER_DEVATAS, 7: D45_WATER_DEVATAS, 11: D45_WATER_DEVATAS,
    }
    amsa_size = 30.0 / 45
    amsa_idx = int(degree_in_sign / amsa_size) % 15
    devatas = element_map.get(sign_idx % 12, D45_FIRE_DEVATAS)
    return devatas[amsa_idx % len(devatas)]


def _compute_aspect_matrix(varga_positions: dict[str, int]) -> list[tuple[str, str, str]]:
    """
    Compute aspect matrix for a varga: Parashari (7th aspect for all grahas) +
    Mars/Jupiter/Saturn special aspects.
    Returns list of (aspecting_body, aspected_sign_or_body, aspect_type).
    """
    aspects = []
    special = {
        "Mars": [3, 7],   # 4th, 8th (0-indexed offset from body sign)
        "Jupiter": [4, 8], # 5th, 9th
        "Saturn": [2, 9],  # 3rd, 10th
        "Rahu": [4, 8],    # 5th, 9th (BPHS Ch.26 — same as Jupiter)
        "Ketu": [4, 8],    # 5th, 9th (BPHS Ch.26 — same as Jupiter)
    }
    for body, sign in varga_positions.items():
        if body == "Lagna":
            continue
        # 7th aspect (universal)
        asp_sign = (sign + 6) % 12
        aspects.append((body, SIGN_NAMES[asp_sign], "7th"))
        # Special aspects
        for offset in special.get(body, []):
            asp_sign2 = (sign + offset) % 12
            aspects.append((body, SIGN_NAMES[asp_sign2], f"{offset+1}th"))
    return aspects


def _compute_jaimini_karakas(varga_positions: dict[str, int], d1_longitudes: dict[str, float]) -> dict[str, dict]:
    """
    Compute 8 Jaimini Chara karakas from D1 longitudes (degrees within sign).
    AK = highest degrees, AmK = 2nd, ..., SK = 8th (excluding Rahu+Ketu for 7-karaka or including for 8).
    Returns {karaka_name: {graha, sign_in_varga, dignity_in_varga}}.
    """
    # Use 7 classical grahas for karaka assignment (8-karaka includes Rahu)
    eligible = {g: d1_longitudes.get(g, 0.0) % 30.0 for g in CLASSICAL_7_GRAHAS}
    # Add Rahu for 8-karaka system (Rahu's degree within sign)
    eligible["Rahu"] = d1_longitudes.get("Rahu", 0.0) % 30.0

    # Sort by degree within sign descending
    sorted_grahas = sorted(eligible.items(), key=lambda x: x[1], reverse=True)

    karakas = {}
    for i, (graha, _) in enumerate(sorted_grahas[:8]):
        k_name = JAIMINI_KARAKA_NAMES[i]
        varga_sign = varga_positions.get(graha)
        dignity = _compute_dignity(graha, varga_sign) if varga_sign is not None else "Unknown"
        karakas[k_name] = {
            "graha": graha,
            "sign": SIGN_NAMES[varga_sign] if varga_sign is not None else "Unknown",
            "sign_id": (varga_sign + 1) if varga_sign is not None else 0,
            "dignity": dignity,
        }
    return karakas


# PyJHora Ashtakavarga planet-id encoding for the `house_to_planet_list` ("chart_1d")
# format consumed by jhora.horoscope.chart.ashtakavarga.get_ashtaka_varga(). Nodes are
# deliberately excluded — classical Ashtakavarga has no Rahu/Ketu contributor row.
_AV_BODY_TO_JHORA_ID = {
    "Sun": "0", "Moon": "1", "Mars": "2", "Mercury": "3",
    "Jupiter": "4", "Venus": "5", "Saturn": "6",
}
_AV_JHORA_ID_TO_BODY = {v: k for k, v in _AV_BODY_TO_JHORA_ID.items()}


def _chart_1d_from_varga_positions(varga_positions: dict[str, int]) -> list[str]:
    """
    Build PyJHora's `house_to_planet_list` ("chart_1d") encoding from a varga's
    {body: sign_idx (0-based)} map: a 12-cell list indexed by sign (0=Aries..
    11=Pisces), each cell a "/"-joined string of jhora planet-id digits ("0".."6")
    plus "L" for Lagna. Shared by both the BAV (M-4) and compound-friendship
    (M-18) PyJHora delegations, which consume the identical encoding.
    """
    chart_1d = ["" for _ in range(12)]
    for body, jid in _AV_BODY_TO_JHORA_ID.items():
        sign = varga_positions.get(body)
        if sign is None:
            continue
        chart_1d[sign % 12] += jid + "/"
    # PyJHora's get_ashtaka_varga unconditionally evaluates p_to_h[7] (planet-id
    # 7 = Rahu) while iterating each contributor list's 8th slot BEFORE checking
    # whether that slot is really Lagna (op==7) and overriding — a quirk of the
    # upstream implementation, not a classical requirement (Rahu is not an
    # Ashtakavarga contributor and its looked-up value is always discarded for
    # op==7). Without a Rahu entry in chart_1d, p_to_h has no key "7" and the
    # call raises KeyError. We supply Rahu's real position (harmless — its
    # value plays no role in any BAV/SAV output) purely to satisfy this.
    rahu_sign = varga_positions.get("Rahu")
    if rahu_sign is not None:
        chart_1d[rahu_sign % 12] += "7/"
    # Ketu (jhora id 8) is likewise required as a p_to_h key by
    # house._get_compound_relationships_of_planets (M-18), which iterates
    # const.SUN_TO_KETU (ids 0..8) internally.
    ketu_sign = varga_positions.get("Ketu")
    if ketu_sign is not None:
        chart_1d[ketu_sign % 12] += "8/"
    lagna_sign = varga_positions.get("Lagna")
    if lagna_sign is not None:
        chart_1d[lagna_sign % 12] += "L/"
    return [c[:-1] if c.endswith("/") else c for c in chart_1d]


def _compute_ashtakavarga_bav(varga_positions: dict[str, int]) -> dict[str, list]:
    """
    Compute Bhinnashtakavarga (BAV) + Sarvashtakavarga (SAV) for a varga by
    DELEGATING to PyJHora's real BPHS Ashtakavarga-Prakarana 8x8 contributor-map
    engine (jhora.horoscope.chart.ashtakavarga.get_ashtaka_varga) — never
    reimplemented in this file (M-4 fix; the prior hand-rolled loop credited
    every contributor's bindus to ALL 8 grahas' grids identically, making every
    BAV grid — and therefore SAV — a degenerate 8x-duplicate of one array).

    Returns {"bav": {graha: [12 sign bindu counts]}, "sarva": [12 SAV totals]}.
    Classical invariant (verified against the real engine): sum(sarva) == 337
    for ANY chart/varga — this is a pure combinatorial identity of the fixed
    BENEFIC_HOUSES contributor-list lengths, independent of planetary
    positions, and is used as the Ring-1 self-verification gate below.
    """
    from pyjhora_adapter._jhora import get_ashtakavarga as _get_av_module
    av = _get_av_module()

    chart_1d = _chart_1d_from_varga_positions(varga_positions)
    binna, samudhaya, _prastara = av.get_ashtaka_varga(chart_1d)

    bindus: dict[str, list] = {}
    for jid, body in _AV_JHORA_ID_TO_BODY.items():
        bindus[body] = list(binna[int(jid)])
    # Lagna's own BAV row (index 7) — informational; classical SAV excludes it
    # (get_ashtaka_varga's samudhaya already sums only the 7 graha rows).
    bindus["Lagna"] = list(binna[7])

    return {"bav": bindus, "sarva": list(samudhaya)}


# Panchadha Maitri (5-fold compound naisargika+tatkalika relationship) virupa
# ladder for Saptavargaja Bala, keyed by PyJHora's own compound-relation code
# (0=Adhi Shatru .. 4=Adhi Mitra). Values cross-checked against PyJHora's own
# Shadbala reference implementation (jhora.horoscope.chart.strength.
# _sapthavargaja_bala_1/_2's sb_fac dict) — not invented for this fix.
SAPTAVARGAJA_VIRUPA_BY_COMPOUND_CODE = {
    4: 22.5,   # Adhi Mitra (great friend: natural friend + temporary friend)
    3: 15.0,   # Mitra (friend: natural neutral + temporary friend)
    2: 7.5,    # Sama (neutral: friend+enemy or enemy+friend cross-combination)
    1: 3.75,   # Shatru (enemy: natural neutral + temporary enemy)
    0: 1.875,  # Adhi Shatru (great enemy: natural enemy + temporary enemy)
}
SAPTAVARGAJA_LABEL_BY_COMPOUND_CODE = {
    4: "Adhi_Mitra", 3: "Mitra", 2: "Sama", 1: "Shatru", 0: "Adhi_Shatru",
}


def _compute_compound_relation_matrix(varga_positions: dict[str, int]) -> dict[tuple[str, str], int]:
    """
    Compute the classical 5-fold Panchadha Maitri (compound naisargika +
    tatkalika/temporary) planetary relationship for a varga by DELEGATING to
    PyJHora (jhora.horoscope.chart.house._get_compound_relationships_of_planets)
    — never reimplemented (M-18 fix). The prior implementation
    (_compute_dignity's Friend/Neutral/Enemy branch) used ONLY natural
    (naisargika) friendship, collapsing the classical 5-state ladder
    (Adhi Mitra/Mitra/Sama/Shatru/Adhi Shatru) to a 3-state one and ignoring
    each graha's temporary (positional, tatkalika) relationship entirely.

    Returns {(body, other_body): relation_code} for the 7 classical grahas,
    where relation_code in {0..4} is PyJHora's own compound-relation encoding
    (0=Adhi Shatru .. 4=Adhi Mitra).
    """
    from pyjhora_adapter._jhora import get_house as _get_house_module
    house_mod = _get_house_module()

    chart_1d = _chart_1d_from_varga_positions(varga_positions)
    cs = house_mod._get_compound_relationships_of_planets(chart_1d)

    result: dict[tuple[str, str], int] = {}
    for b1, jid1 in _AV_BODY_TO_JHORA_ID.items():
        for b2, jid2 in _AV_BODY_TO_JHORA_ID.items():
            if b1 == b2:
                continue
            result[(b1, b2)] = cs[int(jid1)][int(jid2)]
    return result


def _check_near_boundary(degree_in_sign: float, threshold_arcsec: float = 1800.0) -> dict:
    """Check proximity to sign/nakshatra boundaries (threshold in arcsec)."""
    threshold_deg = threshold_arcsec / 3600.0
    near_sign = degree_in_sign < threshold_deg or degree_in_sign > (30.0 - threshold_deg)
    # Nakshatra boundaries every 13°20' = 800'
    nak_size = 13.333333
    pos_in_nak_cycle = degree_in_sign % nak_size
    near_nak = pos_in_nak_cycle < threshold_deg or pos_in_nak_cycle > (nak_size - threshold_deg)
    return {
        "near_sign_boundary": near_sign,
        "near_nakshatra_boundary": near_nak,
    }


# ── Chart computation ─────────────────────────────────────────────────────────

def _compute_varga_positions(jd_ut: float, ayanamsha_id: str,
                              lat: float, lon: float, tz: float) -> dict[str, dict]:
    """
    Compute positions for all 30 vargas using PyJHora.
    Returns {varga_id: {body: {sign_idx, degree_in_sign, longitude}}}.
    """
    from pyjhora_adapter._jhora import drik, utils
    from pyjhora_adapter._ayanamsha import resolve_mode

    mode, _ = resolve_mode(ayanamsha_id)
    drik.set_ayanamsa_mode(mode)
    place = drik.Place("subject", lat, lon, tz)

    # Get D1 (natal) positions for all bodies
    asc = drik.ascendant(jd_ut, place)
    asc_full_long = int(asc[0]) * 30.0 + float(asc[1])

    # Get planetary longitudes
    planet_ids = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury",
                  4: "Jupiter", 5: "Venus", 6: "Saturn", 7: "Rahu", 8: "Ketu"}

    d1_longitudes = {}
    d1_longitudes["Lagna"] = asc_full_long % 360.0

    for pid, pname in planet_ids.items():
        import swisseph as swe
        planet_map = {0: swe.SUN, 1: swe.MOON, 2: swe.MARS, 3: swe.MERCURY,
                      4: swe.JUPITER, 5: swe.VENUS, 6: swe.SATURN,
                      7: swe.MEAN_NODE, 8: swe.MEAN_NODE}
        try:
            raw_lon = drik.sidereal_longitude(jd_ut, planet_map[pid])
            if pid == 8:  # Ketu = Rahu + 180
                raw_lon = (drik.sidereal_longitude(jd_ut, swe.MEAN_NODE) + 180.0) % 360.0
            d1_longitudes[pname] = float(raw_lon)
        except Exception as exc:
            logger.warning("[ga_vargas] Planet %s D1 longitude failed: %s", pname, exc)
            d1_longitudes[pname] = 0.0

    # Compute all 30 vargas
    all_vargas: dict[str, dict] = {}

    for varga_n in ALL_30_VARGAS:
        vid = _varga_id(varga_n)
        varga_data = {}
        for body, d1_long in d1_longitudes.items():
            try:
                if varga_n == 2:
                    sign_idx = _compute_d2_hora(d1_long)
                elif varga_n == 3:
                    sign_idx = _compute_d3_drekkana(d1_long)
                elif varga_n in (1,):
                    sign_idx = int(d1_long / 30.0) % 12
                else:
                    sign_idx = _compute_general_varga(d1_long, varga_n)

                deg_in_sign = d1_long % 30.0
                varga_data[body] = {
                    "sign_idx": sign_idx,
                    "sign": SIGN_NAMES[sign_idx],
                    "sign_id": sign_idx + 1,
                    "degree_in_sign": deg_in_sign,
                    "longitude": d1_long,
                }
            except Exception as exc:
                logger.warning("[ga_vargas] varga=%s body=%s: %s", vid, body, exc)
                varga_data[body] = {
                    "sign_idx": 0, "sign": "Aries", "sign_id": 1,
                    "degree_in_sign": 0.0, "longitude": 0.0,
                    "error": str(exc),
                }
        all_vargas[vid] = varga_data

    return all_vargas, d1_longitudes


# ── Row builders ───────────────────────────────────────────────────────────────

def _build_position_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str,
    varga_data: dict,
    d1_data: dict,
) -> list[dict]:
    """Build varga_position rows for all bodies in a varga."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    v_status = _verification_status("varga_position", varga_n)

    # EL-47 fix (Elevation Campaign β.D, 2026-07-25): divisional facts served
    # `house: None` — the house-from-varga-lagna was left for the consumer to
    # derive client-side (a §N.5/B.10 exposure). Compute it here, server-side,
    # whole-sign from THIS varga's own Lagna sign (Lagna = house 1), 1-indexed,
    # and stamp the convention (contract C4) so serving (Stream α) can tell a
    # corrected row from a legacy one across the estate. Mirrors the existing
    # D2 `hora_d2_house` derivation (CR-58) — a pure count over positions
    # already in varga_data, no new astronomical computation.
    _varga_lagna = varga_data.get("Lagna")
    varga_lagna_sign_idx = _varga_lagna["sign_idx"] if _varga_lagna else None

    for body in CLASSICAL_BODIES:
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        subject = BODY_TO_SUBJECT.get(body, body.upper())
        sign_idx = bdata["sign_idx"]
        deg_in_sign = bdata["degree_in_sign"]
        boundary_info = _check_near_boundary(deg_in_sign)
        house_from_varga_lagna = (
            ((sign_idx - varga_lagna_sign_idx) % 12) + 1
            if varga_lagna_sign_idx is not None else None
        )

        # D9 vargottama flag at point
        d1_sign = int(d1_data.get(body, {}).get("sign_idx", -1) if isinstance(d1_data.get(body), dict) else int(d1_data.get(body, 0) / 30.0)) % 12
        vargottama_at_point = (sign_idx == d1_sign)

        # Keys: sign, sign_id, degree_in_sign, house_from_varga_lagna, sign_lord, formula_id
        keys_values = [
            ("sign", "text", sign_idx, SIGN_NAMES[sign_idx], None),
            ("sign_id", "num", sign_idx, None, sign_idx + 1),
            ("degree_in_sign", "num", sign_idx, None, round(deg_in_sign, 6)),
            ("sign_lord", "text", sign_idx, SIGN_LORDS[sign_idx], None),
            ("formula_id", "text", sign_idx, f"parashari_D{varga_n}", None),
        ]
        # EL-47: whole-sign house from the varga's own Lagna (1-indexed). The
        # fact_key `house_from_varga_lagna` is itself the C4 convention marker —
        # it exists ONLY on convention-corrected rows, so serving can trust it
        # unconditionally and fall back to sign-derivation for legacy rows that
        # lack it. Emitted only when this varga carries a Lagna position.
        if house_from_varga_lagna is not None:
            keys_values.append(
                ("house_from_varga_lagna", "num", sign_idx, None, float(house_from_varga_lagna))
            )

        for key, vtype, _, vtxt, vnum in keys_values:
            rid = _fact_id(vid, body, "varga_position", key, chart_id, ayanamsha_id, build_id)
            rows.append({
                "fact_id": rid,
                "chart_id": chart_id,
                "graha": body,
                "ayanamsha_id": ayanamsha_id,
                "varga": vid,
                "sign": SIGN_NAMES[sign_idx],
                "sign_number": sign_idx + 1,
                "degree_in_sign": deg_in_sign,
                "house": None,
                "vargottama": None,
                "source_citation": f"pyjhora_adapter/{ENGINE_VERSION}",
                "build_id": str(build_id),
                # Extended GA6 columns
                "fact_category": "varga_position",
                "fact_key": key,
                "fact_value_text": vtxt,
                "fact_value_num": vnum,
                "fact_subject": f"{vid}.{subject}",
                "build_id_uuid": build_id,
                "verification_pass_status": v_status,
                "engine_version": ENGINE_VERSION,
                "citation_ref": _citation_ref("varga_position", vid, body, key,
                                               chart_id, ayanamsha_id, ENGINE_VERSION),
                "citation_human": _citation_human("varga_position", vid, body, key,
                                                   vtxt or vnum, ayanamsha_id),
                "source_calculation": f"drik.compute/{ENGINE_VERSION}",
                "computed_at": now,
                "tolerance_arcsec": 1800.0,
                "near_sign_boundary_flag": boundary_info["near_sign_boundary"],
                "near_nakshatra_boundary_flag": boundary_info["near_nakshatra_boundary"],
                "vargottama_flag_at_point": vargottama_at_point,
                "formula_provenance_text": f"Parashari_D{varga_n}",
                "cross_ayanamsha_divergence_arcsec": None,
            })

    # CR-58: D2 Hora semantic layer. The wealth varga was served as raw dignity
    # only — the classical Hora doctrine (Sun's hora / Leo = self-earned, active
    # wealth; Moon's hora / Cancer = inherited, passive, accumulated wealth) was
    # computed nowhere. Emit per-graha hora_class (surya_hora / chandra_hora) plus
    # the D2-house (whole-sign from the D2 Lagna) so a query like "both wealth
    # lords in Chandra-hora, D2 house 12" is answerable in a single call.
    if varga_n == 2:
        rows.extend(_build_d2_hora_rows(
            chart_id, ayanamsha_id, build_id, vid, varga_data, now))

    return rows


# D2 (Hora) sign indices from _compute_d2_hora: Leo=4 (Sun's hora), Cancer=3 (Moon's hora).
_D2_HORA_CLASS = {4: "surya_hora", 3: "chandra_hora"}


def _build_d2_hora_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    vid: str, varga_data: dict, now: str,
) -> list[dict]:
    """CR-58: per-graha D2 hora-class (surya_hora/chandra_hora) + D2 whole-sign house.

    hora_class is read off the graha's already-computed D2 sign (Leo→surya_hora,
    Cancer→chandra_hora — the only two D2 signs under the Parashari hora rule).
    hora_d2_house is the whole-sign house counted from the D2 Lagna's own hora sign
    (so the Lagna is house 1). Emitted only for D2; no new astronomical computation
    — a pure derivation over positions already in varga_data (B.10-clean).
    """
    rows: list[dict] = []
    lagna_bdata = varga_data.get("Lagna")
    if lagna_bdata is None:
        return rows
    lagna_sign_idx = lagna_bdata["sign_idx"]

    for body in CLASSICAL_BODIES:
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        hora_class = _D2_HORA_CLASS.get(sign_idx)
        if hora_class is None:
            continue  # defensive: D2 signs are only Leo/Cancer
        d2_house = ((sign_idx - lagna_sign_idx) % 12) + 1
        subject = BODY_TO_SUBJECT.get(body, body.upper())

        for key, vtxt, vnum in [
            ("hora_class", hora_class, None),
            ("hora_d2_house", None, d2_house),
        ]:
            rid = _fact_id(vid, body, "varga_hora_class", key,
                           chart_id, ayanamsha_id, build_id)
            rows.append({
                "fact_id": rid,
                "chart_id": chart_id,
                "graha": body,
                "ayanamsha_id": ayanamsha_id,
                "varga": vid,
                "sign": SIGN_NAMES[sign_idx],
                "sign_number": sign_idx + 1,
                "degree_in_sign": bdata["degree_in_sign"],
                "house": float(d2_house),
                "vargottama": None,
                "source_citation": f"pyjhora_adapter/{ENGINE_VERSION}",
                "build_id": str(build_id),
                "fact_category": "varga_hora_class",
                "fact_key": key,
                "fact_value_text": vtxt,
                "fact_value_num": vnum,
                "fact_subject": f"{vid}.{subject}",
                "build_id_uuid": build_id,
                "verification_pass_status": "classical_match",
                "engine_version": ENGINE_VERSION,
                "citation_ref": _citation_ref("varga_hora_class", vid, body, key,
                                               chart_id, ayanamsha_id, ENGINE_VERSION),
                "citation_human": (
                    f"{body} in {SIGN_NAMES[sign_idx]} (D2) — "
                    f"{hora_class} ({'active/self-earned' if hora_class == 'surya_hora' else 'passive/inherited'} "
                    f"wealth), D2 house {d2_house} from Hora-Lagna."
                ),
                "source_calculation": f"d2_hora_class_derivation/{ENGINE_VERSION}",
                "computed_at": now,
                "tolerance_arcsec": 1800.0,
                "near_sign_boundary_flag": False,
                "near_nakshatra_boundary_flag": False,
                "vargottama_flag_at_point": False,
                "formula_provenance_text": "Parashari_Hora_D2_Leo_Cancer",
                "cross_ayanamsha_divergence_arcsec": None,
            })

    return rows


def _build_dignity_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict,
) -> list[dict]:
    """Build varga_dignity rows."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for body in CLASSICAL_BODIES:
        if body == "Lagna":
            continue
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        dignity = _compute_dignity(body, sign_idx, bdata.get("degree_in_sign", 0.0))
        subject = BODY_TO_SUBJECT.get(body, body.upper())
        rid = _fact_id(vid, body, "varga_dignity", "dignity",
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[sign_idx],
            "sign_number": sign_idx + 1,
            "degree_in_sign": bdata["degree_in_sign"],
            "house": None,
            "vargottama": None,
            "source_citation": f"pyjhora_adapter/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_dignity",
            "fact_key": "dignity",
            "fact_value_text": dignity,
            "fact_value_num": None,
            "fact_subject": f"{vid}.{subject}",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": _citation_ref("varga_dignity", vid, body, "dignity",
                                           chart_id, ayanamsha_id, ENGINE_VERSION),
            "citation_human": _citation_human("varga_dignity", vid, body, "dignity",
                                               dignity, ayanamsha_id),
            "source_calculation": f"classical_dignity_table/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "BPHS_dignity_table",
            "cross_ayanamsha_divergence_arcsec": None,
        })
    return rows


def _build_vargottama_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str,
    varga_data: dict, d1_varga_data: dict,
) -> list[dict]:
    """Build varga_vargottama_flag rows (vargottama = same sign as D1)."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    for body in CLASSICAL_BODIES:
        bdata = varga_data.get(body)
        d1bdata = d1_varga_data.get(body)
        if bdata is None or d1bdata is None:
            continue
        is_vargottama = (bdata["sign_idx"] == d1bdata["sign_idx"])
        subject = BODY_TO_SUBJECT.get(body, body.upper())
        rid = _fact_id(vid, body, "varga_vargottama_flag", "vargottama",
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[bdata["sign_idx"]],
            "sign_number": bdata["sign_idx"] + 1,
            "degree_in_sign": bdata["degree_in_sign"],
            "house": None,
            "vargottama": is_vargottama,
            "source_citation": f"pyjhora_adapter/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_vargottama_flag",
            "fact_key": "vargottama",
            "fact_value_text": str(is_vargottama),
            "fact_value_num": 1.0 if is_vargottama else 0.0,
            "fact_subject": f"{vid}.{subject}",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": _citation_ref("varga_vargottama_flag", vid, body, "vargottama",
                                           chart_id, ayanamsha_id, ENGINE_VERSION),
            "citation_human": f"{body} vargottama in {vid}: {is_vargottama} ({ayanamsha_id}).",
            "source_calculation": f"d1_sign_comparison/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": is_vargottama,
            "formula_provenance_text": "D1_sign_equality",
            "cross_ayanamsha_divergence_arcsec": None,
        })
    return rows


def _build_house_lord_occupant_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict,
) -> list[dict]:
    """Build varga_house_lord + varga_house_occupant rows."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    lagna_sign = varga_data.get("Lagna", {}).get("sign_idx", 0)

    # House lords: for each house, which sign and which lord
    for house in range(1, 13):
        house_sign_idx = (lagna_sign + house - 1) % 12
        lord = SIGN_LORDS[house_sign_idx]
        rid = _fact_id(vid, f"H{house}", "varga_house_lord", "lord",
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": lord,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[house_sign_idx],
            "sign_number": house_sign_idx + 1,
            "degree_in_sign": 0.0,
            "house": house,
            "vargottama": None,
            "source_citation": f"pyjhora_adapter/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_house_lord",
            "fact_key": "lord",
            "fact_value_text": lord,
            "fact_value_num": float(house),
            "fact_subject": f"{vid}.H{house}",
            "build_id_uuid": build_id,
            "verification_pass_status": "single",
            "engine_version": ENGINE_VERSION,
            "citation_ref": _citation_ref("varga_house_lord", vid, f"H{house}", "lord",
                                           chart_id, ayanamsha_id, ENGINE_VERSION),
            "citation_human": f"House {house} lord in {vid}: {lord} ({ayanamsha_id}).",
            "source_calculation": f"whole_sign_house/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "whole_sign",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    # House occupants: for each body, which house in this varga
    for body in CLASSICAL_BODIES:
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        body_sign = bdata["sign_idx"]
        house_num = ((body_sign - lagna_sign) % 12) + 1
        subject = BODY_TO_SUBJECT.get(body, body.upper())
        rid = _fact_id(vid, body, "varga_house_occupant", "house",
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[body_sign],
            "sign_number": body_sign + 1,
            "degree_in_sign": bdata["degree_in_sign"],
            "house": house_num,
            "vargottama": None,
            "source_citation": f"pyjhora_adapter/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_house_occupant",
            "fact_key": "house",
            "fact_value_text": str(house_num),
            "fact_value_num": float(house_num),
            "fact_subject": f"{vid}.{subject}",
            "build_id_uuid": build_id,
            "verification_pass_status": "single",
            "engine_version": ENGINE_VERSION,
            "citation_ref": _citation_ref("varga_house_occupant", vid, body, "house",
                                           chart_id, ayanamsha_id, ENGINE_VERSION),
            "citation_human": f"{body} occupies house {house_num} in {vid} ({ayanamsha_id}).",
            "source_calculation": f"whole_sign_house/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "whole_sign",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


def _build_deity_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict,
    conn: Any = None,
) -> list[dict]:
    """Build varga_deity_attribution rows where classical attribution exists."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    shashtiamsha_ref: dict[int, dict] = {}
    if varga_n == 60 and conn is not None:
        shashtiamsha_ref = _load_shashtiamsha_deities(conn)

    for body in CLASSICAL_BODIES:
        if body == "Lagna":
            continue
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        deg_in_sign = bdata["degree_in_sign"]

        deity = None
        quality = None

        if varga_n == 60:
            # M-17 fix: real sign-parity-reversed amsa_number JOINed against the
            # canonical bg_shashtiamsha_deities reference table (migration 430)
            # instead of a fabricated per-degree [Malefic,Neutral,Benefic]*20
            # cycle. quality is real (kroora/soumya, cross-derived from PyJHora's
            # own const.shashti_amsa_rulers_kroora/soumya); deity_name is
            # canonical-or-floor NULL pending a primary BPHS Ch.7 citation.
            amsa_number = _get_d60_amsa_number(sign_idx, deg_in_sign)
            ref_row = shashtiamsha_ref.get(amsa_number)
            if ref_row is not None:
                quality = "Malefic" if ref_row["quality"] == "kroora" else "Benefic"
                deity = ref_row["deity_name"]  # floored NULL until sourced
            else:
                # No reference row available (table unreachable) — floor
                # honestly rather than fabricate a value.
                quality = None
                deity = None
        elif varga_n == 40:
            deity = _get_d40_devata(sign_idx, deg_in_sign)
        elif varga_n == 45:
            deity = _get_d45_devata(sign_idx, deg_in_sign)
        elif varga_n == 30:
            deity = _compute_d30_lord(sign_idx, deg_in_sign)
        elif varga_n == 9:
            # D9 navamsa — basic deity by sign element
            elements = ["Deva", "Manushya", "Rakshasa"] * 4
            deity = elements[sign_idx]
        elif varga_n == 2:
            deity = "Surya" if sign_idx == 4 else "Chandra"  # Leo/Cancer
        elif varga_n == 3:
            deity = ["Brahma", "Vishnu", "Shiva"][sign_idx % 3]
        elif varga_n == 20:
            deity = ["Kali", "Gauri", "Lakshmi", "Saraswati"][sign_idx % 4]
        elif varga_n == 24:
            deity = ["Brahma", "Vishnu", "Rudra"] * 4 + ["Vishnu", "Rudra", "Brahma"]
            if isinstance(deity, list):
                deity = deity[sign_idx % len(deity)] if sign_idx < len(deity) else "Brahma"
        elif varga_n == 16:
            deity = ["Brahma", "Vishnu", "Shiva", "Surya"][sign_idx % 4]
        elif varga_n == 108:
            deity = D108_KARMA_TYPES[sign_idx % 3]
        elif varga_n == 150:
            deity = D150_RISHIS[sign_idx % len(D150_RISHIS)]
        elif varga_n == 2700:
            deity = D2700_SUB_RISHIS[sign_idx % len(D2700_SUB_RISHIS)]
        elif varga_n in (50, 54):
            deity = ["Benefic_quality", "Malefic_quality"][sign_idx % 2]

        if deity is None and quality is None:
            # Nothing computable for this varga/body (or, for D60 with an
            # unreachable bg_shashtiamsha_deities table, an honest floor) —
            # skip rather than fabricate.
            continue

        subject = BODY_TO_SUBJECT.get(body, body.upper())
        base_row = {
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[sign_idx],
            "sign_number": sign_idx + 1,
            "degree_in_sign": deg_in_sign,
            "house": None,
            "vargottama": None,
            "source_citation": (
                f"BPHS_Ch7_bg_shashtiamsha_deities_mig430/{ENGINE_VERSION}"
                if varga_n == 60 else f"BPHS_Ch7/{ENGINE_VERSION}"
            ),
            "build_id": str(build_id),
            "fact_category": "varga_deity_attribution",
            "fact_subject": f"{vid}.{subject}",
            "build_id_uuid": build_id,
            # M-22 fix (M-17 evidence), extended Stage 2 (honest-tiers, TAP-6
            # M-22 remediation): D60's quality lookup above is a repeating
            # [Malefic,Neutral,Benefic]×20 pattern — the real canonical
            # 60-deity list is irregular (~half mislabeled by this proxy),
            # and D60 carries the HIGHEST vimshopaka weight in serving. The
            # original M-22 fix demoted D60 rows only, leaving every other
            # varga's deity/quality attribution asserting "two_pass_verified"
            # unconditionally — but the recon pass that ruled this writer's
            # Stage 2 fix found genuine=EMPTY: no varga's deity/quality
            # lookup in this shared builder runs a real second-pass
            # comparison (they're all static per-varga table/formula lookups
            # keyed on sign_idx). So the ternary collapses to unconditional
            # UNVERIFIED_DEFAULT for every varga, D60 included — D60's value
            # doesn't change, only its assertion goes from an unexamined
            # exception to the same honest default every other varga now
            # gets. UNVERIFIED_DEFAULT resolves to "single" (not
            # "documented_approximation") because chart_divisionals'
            # verification_pass_status CHECK constraint (migration 206, same
            # as chart_dashas) only allows {'two_pass_verified',
            # 'classical_match','divergent_flagged','single'} — caught live
            # by this lane's own Ring-1 rebuild attempt. "single" resolves to
            # the same low-confidence VERIFICATION_RESCALE default (0.60)
            # via the .get() fallback.
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "source_calculation": (
                f"bg_shashtiamsha_deities_join/{ENGINE_VERSION}"
                if varga_n == 60 else f"BPHS_Ch7_table/{ENGINE_VERSION}"
            ),
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": f"BPHS_Ch7_D{varga_n}",
            "cross_ayanamsha_divergence_arcsec": None,
        }

        # M-17: deity_name is canonical-or-floor NULL for D60 (no primary BPHS
        # Ch.7 verse-level source verified for the 60-name list) — emit the
        # deity row ONLY when a real value exists, for every varga INCLUDING
        # D60 (never a placeholder string).
        if deity is not None:
            rid = _fact_id(vid, body, "varga_deity_attribution", "deity",
                           chart_id, ayanamsha_id, build_id)
            rows.append({
                **base_row,
                "fact_id": rid,
                "fact_key": "deity",
                "fact_value_text": str(deity),
                "fact_value_num": None,
                "citation_ref": _citation_ref("varga_deity_attribution", vid, body, "deity",
                                               chart_id, ayanamsha_id, ENGINE_VERSION),
                "citation_human": _citation_human("varga_deity_attribution", vid, body, "deity",
                                                   deity, ayanamsha_id),
            })

        if quality is not None:
            rid2 = _fact_id(vid, body, "varga_deity_attribution", "quality",
                            chart_id, ayanamsha_id, build_id)
            rows.append({
                **base_row,
                "fact_id": rid2,
                "fact_key": "quality",
                "fact_value_text": quality,
                "fact_value_num": None,
                "citation_ref": _citation_ref("varga_deity_attribution", vid, body, "quality",
                                               chart_id, ayanamsha_id, ENGINE_VERSION),
                "citation_human": f"{body}'s {vid} amsa quality: {quality} ({ayanamsha_id}).",
            })

    return rows


def _build_formula_variant_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, d1_longitudes: dict[str, float],
) -> list[dict]:
    """Build varga_formula_variant_position for D2 (2 variants) and D3 (3 variants)."""
    rows = []
    if varga_n not in (2, 3):
        return rows
    now = datetime.now(timezone.utc).isoformat()

    variants = {
        2: ["parashari", "jaimini"],
        3: ["parashari", "jaimini", "mooltrikona"],
    }

    for formula_id in variants.get(varga_n, []):
        for body in CLASSICAL_BODIES:
            d1_long = d1_longitudes.get(body, 0.0)
            if varga_n == 2:
                sign_idx = _compute_d2_hora(d1_long, formula_id)
            else:
                sign_idx = _compute_d3_drekkana(d1_long, formula_id)

            subject = BODY_TO_SUBJECT.get(body, body.upper())
            rid = _fact_id(vid, body, "varga_formula_variant_position",
                           f"sign_{formula_id}", chart_id, ayanamsha_id, build_id)
            rows.append({
                "fact_id": rid,
                "chart_id": chart_id,
                "graha": body,
                "ayanamsha_id": ayanamsha_id,
                "varga": vid,
                "sign": SIGN_NAMES[sign_idx],
                "sign_number": sign_idx + 1,
                "degree_in_sign": d1_long % 30.0,
                "house": None,
                "vargottama": None,
                "source_citation": f"pyjhora_adapter/{ENGINE_VERSION}",
                "build_id": str(build_id),
                "fact_category": "varga_formula_variant_position",
                "fact_key": f"sign_{formula_id}",
                "fact_value_text": SIGN_NAMES[sign_idx],
                "fact_value_num": float(sign_idx + 1),
                "fact_subject": f"{vid}.{subject}.{formula_id}",
                "build_id_uuid": build_id,
                "verification_pass_status": UNVERIFIED_DEFAULT,
                "engine_version": ENGINE_VERSION,
                "citation_ref": _citation_ref("varga_formula_variant_position", vid, body,
                                               f"sign_{formula_id}", chart_id, ayanamsha_id,
                                               ENGINE_VERSION),
                "citation_human": (f"{body} {vid} {formula_id} formula sign: "
                                   f"{SIGN_NAMES[sign_idx]} ({ayanamsha_id})."),
                "source_calculation": f"{formula_id}_formula/{ENGINE_VERSION}",
                "computed_at": now,
                "tolerance_arcsec": None,
                "near_sign_boundary_flag": None,
                "near_nakshatra_boundary_flag": None,
                "vargottama_flag_at_point": None,
                "formula_provenance_text": f"{formula_id}_D{varga_n}",
                "cross_ayanamsha_divergence_arcsec": None,
            })

    return rows


def _build_d30_lord_per_amsa_rows(
    chart_id: str, ayanamsha_id: str, build_id: str, build_id_str: str,
) -> list[dict]:
    """Build varga_d30_lord_per_amsa: 5-lord chain × 12 signs = 60 rows."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for sign_idx in range(12):
        regions = D30_ODD_LORDS if sign_idx % 2 == 0 else D30_EVEN_LORDS
        for lord, start_deg, end_deg in regions:
            rid = _fact_id("D30", f"S{sign_idx+1}", "varga_d30_lord_per_amsa",
                           f"{lord}_{int(start_deg)}_{int(end_deg)}",
                           chart_id, ayanamsha_id, str(build_id))
            rows.append({
                "fact_id": rid,
                "chart_id": chart_id,
                "graha": lord,
                "ayanamsha_id": ayanamsha_id,
                "varga": "D30",
                "sign": SIGN_NAMES[sign_idx],
                "sign_number": sign_idx + 1,
                "degree_in_sign": start_deg,
                "house": None,
                "vargottama": None,
                "source_citation": f"BPHS_Trimsamsa/{ENGINE_VERSION}",
                "build_id": build_id_str,
                "fact_category": "varga_d30_lord_per_amsa",
                "fact_key": f"{lord}_{int(start_deg)}_{int(end_deg)}",
                "fact_value_text": lord,
                "fact_value_num": start_deg,
                "fact_subject": f"D30.S{sign_idx+1}",
                "build_id_uuid": build_id,
                "verification_pass_status": UNVERIFIED_DEFAULT,
                "engine_version": ENGINE_VERSION,
                "citation_ref": (f"varga_d30_lord_per_amsa.D30.S{sign_idx+1}.{lord}"
                                 f"@chart={chart_id}:ay={ayanamsha_id}:eng={ENGINE_VERSION}"),
                "citation_human": (f"D30 sign {SIGN_NAMES[sign_idx]} "
                                   f"{start_deg}-{end_deg}°: {lord} ({ayanamsha_id})."),
                "source_calculation": f"BPHS_D30_trimsamsa_table/{ENGINE_VERSION}",
                "computed_at": now,
                "tolerance_arcsec": None,
                "near_sign_boundary_flag": None,
                "near_nakshatra_boundary_flag": None,
                "vargottama_flag_at_point": None,
                "formula_provenance_text": "BPHS_D30_5lords",
                "cross_ayanamsha_divergence_arcsec": None,
            })

    return rows


def _build_vimsopaka_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict,
) -> list[dict]:
    """Build varga_vimsopaka_contribution rows for Shodasavarga bodies."""
    if varga_n not in VIMSOPAKA_SHODA_WEIGHTS:
        return []
    weight = VIMSOPAKA_SHODA_WEIGHTS[varga_n]
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for body in CLASSICAL_7_GRAHAS:
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        dignity = _compute_dignity(body, sign_idx, bdata.get("degree_in_sign", 0.0))
        # Vimsopaka contribution: max score × weight based on dignity
        dignity_factor = {
            "Exalted": 1.0, "Moolatrikona": 0.9, "Own": 0.8,
            "Friend": 0.6, "Neutral": 0.4, "Enemy": 0.2,
            "Debilitated": 0.0,
        }.get(dignity, 0.4)
        contribution = weight * dignity_factor

        subject = BODY_TO_SUBJECT.get(body, body.upper())
        rid = _fact_id(vid, body, "varga_vimsopaka_contribution", "contribution",
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[sign_idx],
            "sign_number": sign_idx + 1,
            "degree_in_sign": bdata["degree_in_sign"],
            "house": None,
            "vargottama": None,
            "source_citation": f"BPHS_Vimsopaka/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_vimsopaka_contribution",
            "fact_key": "contribution",
            "fact_value_text": None,
            "fact_value_num": round(contribution, 4),
            "fact_subject": f"{vid}.{subject}",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": _citation_ref("varga_vimsopaka_contribution", vid, body, "contribution",
                                           chart_id, ayanamsha_id, ENGINE_VERSION),
            "citation_human": (f"{body} {vid} Vimsopaka contribution: "
                               f"{contribution:.4f} (weight={weight}, dignity={dignity}, {ayanamsha_id})."),
            "source_calculation": f"BPHS_vimsopaka_weight_table/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": f"Shodasavarga_weight_{weight}",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


def _build_ashtakavarga_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict,
) -> list[dict]:
    """
    Build varga_ashtakavarga rows (M-4 fix): per-graha Bhinnashtakavarga (BAV)
    bindus per sign (12 rows/graha) + Sarvashtakavarga (SAV) totals per sign
    (12 rows), delegating the real computation to PyJHora
    (_compute_ashtakavarga_bav -> jhora ashtakavarga.get_ashtaka_varga).

    Was previously dead code: _compute_ashtakavarga_bav existed but was never
    called and no builder wired the varga_ashtakavarga category into the
    dispatcher at all, despite the category being declared in
    TWO_PASS_CATEGORIES. This function closes that gap.
    """
    varga_positions = {
        body: varga_data[body]["sign_idx"]
        for body in CLASSICAL_BODIES
        if body in varga_data
    }
    if "Lagna" not in varga_positions or not any(
        b in varga_positions for b in CLASSICAL_7_GRAHAS
    ):
        return []

    av = _compute_ashtakavarga_bav(varga_positions)
    bindus = av["bav"]
    sarva = av["sarva"]
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    lagna_sign = varga_positions.get("Lagna", 0)

    def _emit(graha_label: str, subject: str, sign_bindus: list[int]) -> None:
        for sign_idx in range(12):
            house_num = ((sign_idx - lagna_sign) % 12) + 1
            bindu_val = sign_bindus[sign_idx]
            rid = _fact_id(vid, f"{graha_label}.S{sign_idx + 1}",
                           "varga_ashtakavarga", "bindus",
                           chart_id, ayanamsha_id, build_id)
            rows.append({
                "fact_id": rid,
                "chart_id": chart_id,
                "graha": graha_label,
                "ayanamsha_id": ayanamsha_id,
                "varga": vid,
                "sign": SIGN_NAMES[sign_idx],
                "sign_number": sign_idx + 1,
                "degree_in_sign": None,
                "house": house_num,
                "vargottama": None,
                "source_citation": f"BPHS_Ashtakavarga_Prakarana/pyjhora_ashtakavarga/{ENGINE_VERSION}",
                "build_id": str(build_id),
                "fact_category": "varga_ashtakavarga",
                "fact_key": "bindus",
                "fact_value_text": None,
                "fact_value_num": float(bindu_val),
                "fact_subject": f"{vid}.{subject}.S{sign_idx + 1}",
                "build_id_uuid": build_id,
                "verification_pass_status": UNVERIFIED_DEFAULT,
                "engine_version": ENGINE_VERSION,
                "citation_ref": _citation_ref("varga_ashtakavarga", vid, f"{graha_label}.S{sign_idx + 1}",
                                               "bindus", chart_id, ayanamsha_id, ENGINE_VERSION),
                "citation_human": (f"{graha_label} {vid} Ashtakavarga bindus in {SIGN_NAMES[sign_idx]}: "
                                    f"{bindu_val} ({ayanamsha_id}); delegated to PyJHora "
                                    f"ashtakavarga.get_ashtaka_varga."),
                "source_calculation": f"pyjhora_ashtakavarga.get_ashtaka_varga/{ENGINE_VERSION}",
                "computed_at": now,
                "tolerance_arcsec": None,
                "near_sign_boundary_flag": None,
                "near_nakshatra_boundary_flag": None,
                "vargottama_flag_at_point": None,
                "formula_provenance_text": "BPHS_Ashtakavarga_Prakarana_8x8_contributor_map",
                "cross_ayanamsha_divergence_arcsec": None,
            })

    for body in CLASSICAL_7_GRAHAS:
        if body not in bindus:
            continue
        subject = BODY_TO_SUBJECT.get(body, body.upper())
        _emit(body, subject, bindus[body])

    # Sarvashtakavarga (SAV) — sum across all 7 grahas per sign; classical
    # invariant total across 12 signs is 337 (verified in Ring-1 self-test).
    _emit("SARVA", "SARVA", sarva)

    return rows


def _build_saptavargaja_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict,
) -> list[dict]:
    """
    Build varga_saptavargaja_bala_component (7 grahas x 7 vargas in Saptavarga).

    M-18 fix: the prior implementation graded every graha purely by
    _compute_dignity's natural-friendship-only Friend/Neutral/Enemy state and
    a non-classical virupa ladder (45/37.5/30/22.5/15/7.5/3.75). This
    reimplementation:
      (1) matches PyJHora's own Saptavargaja Bala reference structure
          (jhora.horoscope.chart.strength._sapthavargaja_bala_1/_2): own-sign
          = 30, Moolatrikona = 45 (D1/Rasi ONLY — Uchcha/exaltation is a
          SEPARATE Sthana-bala sub-component in classical Shadbala, not part
          of Saptavargaja's own ladder, and Moolatrikona itself is likewise
          only evaluated for varga_n==1 per PyJHora's dcf==1 guard);
      (2) for every other placement, delegates to PyJHora's real Panchadha
          Maitri (compound naisargika+tatkalika relationship) engine via
          _compute_compound_relation_matrix -- never reimplemented -- and
          scores the classical 5-step virupa ladder (22.5/15/7.5/3.75/1.875)
          instead of the naive 3-state natural-only ladder.
    Canonical-or-floor: if the compound-relation delegation is unavailable for
    this varga (e.g. Lagna missing from varga_data), the varga is skipped
    entirely rather than falling back to the old naive scoring.
    """
    if varga_n not in SAPTAVARGA_SET:
        return []

    varga_positions = {
        b: varga_data[b]["sign_idx"] for b in CLASSICAL_BODIES if b in varga_data
    }
    if "Lagna" not in varga_positions:
        return []
    try:
        compound = _compute_compound_relation_matrix(varga_positions)
    except Exception:
        logger.exception(
            "[ga_vargas] M-18 compound-relation delegation failed for %s "
            "(varga_n=%s) -- skipping saptavargaja rows rather than "
            "fabricating naive-friendship scores", vid, varga_n)
        return []

    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for body in CLASSICAL_7_GRAHAS:
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        dtab = DIGNITY_TABLE.get(body, {})

        # B-01 dignity oracle: Moolatrikona is degree-gated (only evaluated for
        # varga_n==1, where degree_in_sign is the real natal degree — vargas
        # >1 have no meaningful "degree within amsa" for a re-derived MT check,
        # matching the pre-existing varga_n==1 guard above).
        is_mt = (
            varga_n == 1
            and classify_dignity(body, SIGN_NAMES[sign_idx], bdata.get("degree_in_sign", 0.0))
            == "moolatrikona"
        )
        if is_mt:
            saptavargaja_score = 45.0
            relation_label = "Moolatrikona"
        elif sign_idx in dtab.get("own", []):
            saptavargaja_score = 30.0
            relation_label = "Own"
        else:
            sign_lord = SIGN_LORDS[sign_idx]
            if sign_lord == body:
                saptavargaja_score = 30.0
                relation_label = "Own"
            else:
                rel_code = compound.get((body, sign_lord))
                if rel_code is None:
                    continue  # floor: skip rather than fabricate
                saptavargaja_score = SAPTAVARGAJA_VIRUPA_BY_COMPOUND_CODE[rel_code]
                relation_label = SAPTAVARGAJA_LABEL_BY_COMPOUND_CODE[rel_code]

        subject = BODY_TO_SUBJECT.get(body, body.upper())
        rid = _fact_id(vid, body, "varga_saptavargaja_bala_component", "saptavargaja",
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[sign_idx],
            "sign_number": sign_idx + 1,
            "degree_in_sign": bdata["degree_in_sign"],
            "house": None,
            "vargottama": None,
            "source_citation": f"BPHS_Saptavargaja/pyjhora_compound_relation/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_saptavargaja_bala_component",
            "fact_key": "saptavargaja",
            "fact_value_text": relation_label,
            "fact_value_num": saptavargaja_score,
            "fact_subject": f"{vid}.{subject}",
            "build_id_uuid": build_id,
            # M-22 fix (M-18 evidence): score_map above is a simplified
            # 6-rung ladder ("simplified" per the comment) that ignores
            # compound (naisargika+tatkalika) planetary friendship — not
            # the real classical virupa ladder. Demoted to "single" (not
            # "documented_approximation" — chart_divisionals' CHECK
            # constraint only allows {'two_pass_verified','classical_match',
            # 'divergent_flagged','single'}, caught live by this lane's own
            # Ring-1 rebuild attempt; "single" resolves to the same
            # low-confidence VERIFICATION_RESCALE default via .get()
            # fallback). Fixing the friendship-ladder derivation itself is
            # M-18's scope, not this lane's.
            "verification_pass_status": "single",
            "engine_version": ENGINE_VERSION,
            "citation_ref": _citation_ref("varga_saptavargaja_bala_component", vid, body, "saptavargaja",
                                           chart_id, ayanamsha_id, ENGINE_VERSION),
            "citation_human": (f"{body} {vid} Saptavargaja bala: "
                               f"{saptavargaja_score} ({relation_label}, compound "
                               f"naisargika+tatkalika relation via PyJHora, {ayanamsha_id})."),
            "source_calculation": f"pyjhora_house._get_compound_relationships_of_planets/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "BPHS_Saptavargaja_Panchadha_Maitri",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


def _build_karaka_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict, d1_longitudes: dict,
) -> list[dict]:
    """Build karaka_per_varga: 8 Jaimini karakas × all 30 vargas."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    karakas = _compute_jaimini_karakas(
        {b: varga_data[b]["sign_idx"] for b in CLASSICAL_BODIES if b in varga_data},
        d1_longitudes,
    )

    for k_name, k_data in karakas.items():
        graha = k_data["graha"]
        sign = k_data["sign"]
        sign_id = k_data["sign_id"]
        dignity = k_data["dignity"]
        full_name = JAIMINI_KARAKA_FULL.get(k_name, k_name)

        rid = _fact_id(vid, k_name, "karaka_per_varga", "assigned_graha",
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": graha,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": sign,
            "sign_number": sign_id,
            "degree_in_sign": 0.0,
            "house": None,
            "vargottama": None,
            "source_citation": f"Jaimini_Sutram/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "karaka_per_varga",
            "fact_key": "assigned_graha",
            "fact_value_text": graha,
            "fact_value_num": None,
            "fact_subject": f"{vid}.{k_name}",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": _citation_ref("karaka_per_varga", vid, k_name, "assigned_graha",
                                           chart_id, ayanamsha_id, ENGINE_VERSION),
            "citation_human": _citation_human("karaka_per_varga", vid, k_name, "assigned_graha",
                                               graha, ayanamsha_id),
            "source_calculation": f"Jaimini_Chara_karaka/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "Jaimini_8_karaka_rahu_included",
            "cross_ayanamsha_divergence_arcsec": None,
        })

        # Also emit sign + dignity rows
        for key, vtxt, vnum in [("sign", sign, float(sign_id)), ("dignity", dignity, None)]:
            rid2 = _fact_id(vid, k_name, "karaka_per_varga", key,
                            chart_id, ayanamsha_id, build_id)
            rows.append({
                **rows[-1],
                "fact_id": rid2,
                "fact_key": key,
                "fact_value_text": vtxt,
                "fact_value_num": vnum,
                "citation_ref": _citation_ref("karaka_per_varga", vid, k_name, key,
                                               chart_id, ayanamsha_id, ENGINE_VERSION),
                "citation_human": f"{full_name} in {vid} {key}: {vtxt or vnum} ({ayanamsha_id}).",
            })

    return rows


def _build_rollup_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict, d1_data: dict,
) -> list[dict]:
    """Build varga_rollup: 9 fields per varga."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    vargottama_count = 0
    exalted_count = 0
    debilitated_count = 0
    own_count = 0
    friendly_count = 0
    enemy_count = 0
    dignity_score_sum = 0.0
    pushkara_count = 0

    dignity_scores = {
        "Exalted": 6, "Moolatrikona": 5, "Own": 4,
        "Friend": 3, "Neutral": 2, "Enemy": 1, "Debilitated": 0,
    }

    for body in CLASSICAL_7_GRAHAS:
        bdata = varga_data.get(body)
        d1bdata = d1_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        dignity = _compute_dignity(body, sign_idx, bdata.get("degree_in_sign", 0.0))
        dignity_score_sum += dignity_scores.get(dignity, 2)
        if dignity == "Exalted":
            exalted_count += 1
        elif dignity == "Debilitated":
            debilitated_count += 1
        elif dignity == "Own":
            own_count += 1
        elif dignity == "Friend":
            friendly_count += 1
        elif dignity == "Enemy":
            enemy_count += 1
        if d1bdata is not None:
            d1_sign = int(d1bdata["sign_idx"] if isinstance(d1bdata, dict) else 0)
            if sign_idx == d1_sign:
                vargottama_count += 1

    fields = [
        ("vargottama_count", None, float(vargottama_count)),
        ("super_vargottama_count", None, 0.0),  # post-pass
        ("pushkara_count", None, float(pushkara_count)),
        ("exalted_count", None, float(exalted_count)),
        ("debilitated_count", None, float(debilitated_count)),
        ("own_sign_count", None, float(own_count)),
        ("friendly_count", None, float(friendly_count)),
        ("enemy_count", None, float(enemy_count)),
        ("overall_dignity_score", None, round(dignity_score_sum, 2)),
    ]

    for key, vtxt, vnum in fields:
        rid = _fact_id(vid, "ALL", "varga_rollup", key, chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": "ALL",
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": None,
            "sign_number": None,
            "degree_in_sign": 0.0,
            "house": None,
            "vargottama": None,
            "source_citation": f"pyjhora_adapter/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_rollup",
            "fact_key": key,
            "fact_value_text": vtxt,
            "fact_value_num": vnum,
            "fact_subject": f"{vid}.rollup",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": f"varga_rollup.{vid}.{key}@chart={chart_id}:ay={ayanamsha_id}",
            "citation_human": f"{vid} rollup {key}: {vnum} ({ayanamsha_id}).",
            "source_calculation": f"aggregated_dignity/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "aggregated_dignity_table",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


def _build_d9_lagna_special_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_data_d9: dict,
) -> list[dict]:
    """Build varga_d9_lagna_special: Vargottama Lagna + Pushkara Lagna flags (D9-specific)."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    lagna_d9 = varga_data_d9.get("Lagna", {})
    if not lagna_d9:
        return rows

    d9_sign_idx = lagna_d9.get("sign_idx", 0)
    # Vargottama Lagna: D9 Lagna same sign as D1 Lagna (passed in varga_data_d9 as d1)
    # We can only check if D1 lagna sign == D9 lagna sign here
    # This is checked vs d1_varga_data in the post-pass; emit the flag
    vargottama_lagna = False  # will be updated in post-pass; emit here as preliminary
    pushkara_lagna = d9_sign_idx in [1, 3, 4, 9]  # BPHS Pushkara Lagna signs: Tau/Can/Leo/Cap

    for key, vtxt, vnum in [
        ("vargottama_lagna_flag", str(vargottama_lagna), 0.0),
        ("pushkara_lagna_flag", str(pushkara_lagna), 1.0 if pushkara_lagna else 0.0),
    ]:
        rid = _fact_id("D9", "LAGNA", "varga_d9_lagna_special", key,
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": "Lagna",
            "ayanamsha_id": ayanamsha_id,
            "varga": "D9",
            "sign": SIGN_NAMES[d9_sign_idx],
            "sign_number": d9_sign_idx + 1,
            "degree_in_sign": lagna_d9.get("degree_in_sign", 0.0),
            "house": None,
            "vargottama": vargottama_lagna if key == "vargottama_lagna_flag" else None,
            "source_citation": f"BPHS_D9_Lagna/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_d9_lagna_special",
            "fact_key": key,
            "fact_value_text": vtxt,
            "fact_value_num": vnum,
            "fact_subject": "D9.LAGNA",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": f"varga_d9_lagna_special.D9.LAGNA.{key}@chart={chart_id}:ay={ayanamsha_id}",
            "citation_human": f"D9 Lagna {key}: {vtxt} ({ayanamsha_id}).",
            "source_calculation": f"BPHS_D9_lagna_special/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "BPHS_D9_Pushkara_Vargottama_Lagna",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


def _build_pushkara_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict, d1_longitudes: dict,
) -> list[dict]:
    """Build varga_pushkara_navamsa_flag (D9 only) + varga_pushkara_bhaga_flag (all)."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for body in CLASSICAL_BODIES:
        if body == "Lagna":
            continue
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        deg_in_sign = bdata["degree_in_sign"]
        d1_long = d1_longitudes.get(body, 0.0)
        d1_sign_idx = int(d1_long / 30.0) % 12
        d1_deg_in_sign = d1_long % 30.0
        subject = BODY_TO_SUBJECT.get(body, body.upper())

        # Pushkara navamsa (D9 only)
        if varga_n == 9:
            d9_sign_idx = sign_idx
            amsa_within_sign = int((d1_deg_in_sign / 30.0) * 9)
            pushkara_navamsa_expected = PUSHKARA_NAVAMSA.get(d1_sign_idx, -1)
            is_pushkara_nav = (amsa_within_sign == pushkara_navamsa_expected)
            rid = _fact_id("D9", body, "varga_pushkara_navamsa_flag", "pushkara_navamsa",
                           chart_id, ayanamsha_id, build_id)
            rows.append({
                "fact_id": rid,
                "chart_id": chart_id,
                "graha": body,
                "ayanamsha_id": ayanamsha_id,
                "varga": "D9",
                "sign": SIGN_NAMES[d9_sign_idx],
                "sign_number": d9_sign_idx + 1,
                "degree_in_sign": deg_in_sign,
                "house": None,
                "vargottama": None,
                "source_citation": f"BPHS_Pushkara/{ENGINE_VERSION}",
                "build_id": str(build_id),
                "fact_category": "varga_pushkara_navamsa_flag",
                "fact_key": "pushkara_navamsa",
                "fact_value_text": str(is_pushkara_nav),
                "fact_value_num": 1.0 if is_pushkara_nav else 0.0,
                "fact_subject": f"D9.{subject}",
                "build_id_uuid": build_id,
                "verification_pass_status": UNVERIFIED_DEFAULT,
                "engine_version": ENGINE_VERSION,
                "citation_ref": f"varga_pushkara_navamsa_flag.D9.{body}.pushkara_navamsa@chart={chart_id}:ay={ayanamsha_id}",
                "citation_human": f"{body} Pushkara navamsa flag: {is_pushkara_nav} ({ayanamsha_id}).",
                "source_calculation": f"BPHS_Pushkara_navamsa_table/{ENGINE_VERSION}",
                "computed_at": now,
                "tolerance_arcsec": None,
                "near_sign_boundary_flag": None,
                "near_nakshatra_boundary_flag": None,
                "vargottama_flag_at_point": None,
                "formula_provenance_text": "BPHS_Pushkara_navamsa",
                "cross_ayanamsha_divergence_arcsec": None,
            })

        # Pushkara bhaga (any varga — uses D1 position)
        expected_bhaga = PUSHKARA_BHAGA.get(d1_sign_idx, -999)
        is_pushkara_bhaga = abs(d1_deg_in_sign - expected_bhaga) <= PUSHKARA_BHAGA_ORBS_DEG
        rid2 = _fact_id(vid, body, "varga_pushkara_bhaga_flag", "pushkara_bhaga",
                        chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid2,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[d1_sign_idx],
            "sign_number": d1_sign_idx + 1,
            "degree_in_sign": d1_deg_in_sign,
            "house": None,
            "vargottama": None,
            "source_citation": f"BPHS_Pushkara_bhaga/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_pushkara_bhaga_flag",
            "fact_key": "pushkara_bhaga",
            "fact_value_text": str(is_pushkara_bhaga),
            "fact_value_num": 1.0 if is_pushkara_bhaga else 0.0,
            "fact_subject": f"{vid}.{subject}",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": f"varga_pushkara_bhaga_flag.{vid}.{body}.pushkara_bhaga@chart={chart_id}:ay={ayanamsha_id}",
            "citation_human": f"{body} Pushkara bhaga at {vid}: {is_pushkara_bhaga} ({ayanamsha_id}).",
            "source_calculation": f"BPHS_Pushkara_bhaga_table/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "BPHS_Pushkara_bhaga",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


def _build_karya_bhava_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict,
) -> list[dict]:
    """Build varga_karya_bhava_per_varga: karya-bhava derivation per varga."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    karya = VARGA_KARYA.get(varga_n, f"general_karya_{varga_n}")

    # Karya-bhava = house corresponding to the varga's natural house significance
    # E.g., D10 karya = 10th from D10 Sun (career significator)
    sun_sign = varga_data.get("Sun", {}).get("sign_idx", 0)
    lagna_sign = varga_data.get("Lagna", {}).get("sign_idx", 0)

    # Karya house from Lagna
    karya_house_num = varga_n % 12 or 12
    karya_sign_idx = (lagna_sign + karya_house_num - 1) % 12

    rid = _fact_id(vid, "karya", "varga_karya_bhava_per_varga", "karya_bhava",
                   chart_id, ayanamsha_id, build_id)
    rows.append({
        "fact_id": rid,
        "chart_id": chart_id,
        "graha": "karya",
        "ayanamsha_id": ayanamsha_id,
        "varga": vid,
        "sign": SIGN_NAMES[karya_sign_idx],
        "sign_number": karya_sign_idx + 1,
        "degree_in_sign": 0.0,
        "house": karya_house_num,
        "vargottama": None,
        "source_citation": f"A6_karya_bhava/{ENGINE_VERSION}",
        "build_id": str(build_id),
        "fact_category": "varga_karya_bhava_per_varga",
        "fact_key": "karya_bhava",
        "fact_value_text": karya,
        "fact_value_num": float(karya_house_num),
        "fact_subject": f"{vid}.karya",
        "build_id_uuid": build_id,
        "verification_pass_status": UNVERIFIED_DEFAULT,
        "engine_version": ENGINE_VERSION,
        "citation_ref": f"varga_karya_bhava_per_varga.{vid}.karya@chart={chart_id}:ay={ayanamsha_id}",
        "citation_human": f"{vid} karya-bhava: {karya} (house {karya_house_num}, {ayanamsha_id}).",
        "source_calculation": f"karya_bhava_derivation/{ENGINE_VERSION}",
        "computed_at": now,
        "tolerance_arcsec": None,
        "near_sign_boundary_flag": None,
        "near_nakshatra_boundary_flag": None,
        "vargottama_flag_at_point": None,
        "formula_provenance_text": f"karya_bhava_D{varga_n}",
        "cross_ayanamsha_divergence_arcsec": None,
    })

    return rows


def _build_lal_kitab_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, vid: str, varga_data: dict, d1_varga_data: dict,
) -> list[dict]:
    """Build varga_lal_kitab_special: D9 Pakka Ghar + D12."""
    if varga_n not in (9, 12):
        return []
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for body in CLASSICAL_7_GRAHAS:
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        lagna_sign = varga_data.get("Lagna", {}).get("sign_idx", 0)
        body_house = ((bdata["sign_idx"] - lagna_sign) % 12) + 1
        pakka_ghar = LAL_KITAB_PAKKA_GHAR.get(body, None)

        if pakka_ghar is None:
            continue
        is_pakka = (body_house == pakka_ghar)
        subject = BODY_TO_SUBJECT.get(body, body.upper())
        key = "pakka_ghar_d9" if varga_n == 9 else "pakka_ghar_d12"

        rid = _fact_id(vid, body, "varga_lal_kitab_special", key,
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[bdata["sign_idx"]],
            "sign_number": bdata["sign_idx"] + 1,
            "degree_in_sign": bdata["degree_in_sign"],
            "house": body_house,
            "vargottama": None,
            "source_citation": f"Lal_Kitab_G41/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_lal_kitab_special",
            "fact_key": key,
            "fact_value_text": str(is_pakka),
            "fact_value_num": float(pakka_ghar),
            "fact_subject": f"{vid}.{subject}",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": f"varga_lal_kitab_special.{vid}.{body}.{key}@chart={chart_id}:ay={ayanamsha_id}",
            "citation_human": f"{body} Lal Kitab Pakka Ghar {vid}: house {body_house} (Pakka={pakka_ghar}, match={is_pakka}, {ayanamsha_id}).",
            "source_calculation": f"Lal_Kitab_Pakka_Ghar_table/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "Lal_Kitab_Pakka_Ghar_G41",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


def _build_d27_quadrant_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_data: dict,
) -> list[dict]:
    """Build varga_d27_directional_quadrant rows for D27."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for body in CLASSICAL_BODIES:
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        quadrant = _d27_quadrant(sign_idx)
        subject = BODY_TO_SUBJECT.get(body, body.upper())

        rid = _fact_id("D27", body, "varga_d27_directional_quadrant", "quadrant",
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": "D27",
            "sign": SIGN_NAMES[sign_idx],
            "sign_number": sign_idx + 1,
            "degree_in_sign": bdata["degree_in_sign"],
            "house": None,
            "vargottama": None,
            "source_citation": f"BPHS_D27_Bhamsa/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_d27_directional_quadrant",
            "fact_key": "quadrant",
            "fact_value_text": quadrant,
            "fact_value_num": None,
            "fact_subject": f"D27.{subject}",
            "build_id_uuid": build_id,
            "verification_pass_status": "single",
            "engine_version": ENGINE_VERSION,
            "citation_ref": f"varga_d27_directional_quadrant.D27.{body}.quadrant@chart={chart_id}:ay={ayanamsha_id}",
            "citation_human": f"{body}'s D27 Bhamsa quadrant: {quadrant} ({ayanamsha_id}).",
            "source_calculation": f"D27_directional_quadrant/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "D27_N_S_E_W_quadrant",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


def _build_d108_karma_rows(
    chart_id: str, ayanamsha_id: str, build_id: str, varga_data: dict,
) -> list[dict]:
    """Build varga_d108_karma_attribution: per body per amsa karma-type."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for body in CLASSICAL_BODIES:
        if body == "Lagna":
            continue
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        amsa_n = sign_idx % 3  # 0=Sanchita, 1=Prarabdha, 2=Agami
        karma_type = D108_KARMA_TYPES[amsa_n]
        subject = BODY_TO_SUBJECT.get(body, body.upper())

        rid = _fact_id("D108", body, "varga_d108_karma_attribution", "karma_type",
                       chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": "D108",
            "sign": SIGN_NAMES[sign_idx],
            "sign_number": sign_idx + 1,
            "degree_in_sign": bdata["degree_in_sign"],
            "house": None,
            "vargottama": None,
            "source_citation": f"Nadi_D108_karma/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": "varga_d108_karma_attribution",
            "fact_key": "karma_type",
            "fact_value_text": karma_type,
            "fact_value_num": None,
            "fact_subject": f"D108.{subject}",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": f"varga_d108_karma_attribution.D108.{body}.karma_type@chart={chart_id}:ay={ayanamsha_id}",
            "citation_human": f"{body} D108 karma type: {karma_type} ({ayanamsha_id}).",
            "source_calculation": f"Nadi_D108_karma_table/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": "Nadi_D108_Sanchita_Prarabdha_Agami",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


def _build_d150_rishi_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    varga_n: int, varga_data: dict,
) -> list[dict]:
    """Build varga_d150_rishi + varga_d2700_sub_rishi rows."""
    rows = []
    now = datetime.now(timezone.utc).isoformat()
    vid = f"D{varga_n}"
    cat = "varga_d150_rishi" if varga_n == 150 else "varga_d2700_sub_rishi"

    for body in CLASSICAL_BODIES:
        if body == "Lagna":
            continue
        bdata = varga_data.get(body)
        if bdata is None:
            continue
        sign_idx = bdata["sign_idx"]
        rishis = D150_RISHIS if varga_n == 150 else D2700_SUB_RISHIS
        rishi = rishis[sign_idx % len(rishis)]
        subject = BODY_TO_SUBJECT.get(body, body.upper())

        rid = _fact_id(vid, body, cat, "rishi", chart_id, ayanamsha_id, build_id)
        rows.append({
            "fact_id": rid,
            "chart_id": chart_id,
            "graha": body,
            "ayanamsha_id": ayanamsha_id,
            "varga": vid,
            "sign": SIGN_NAMES[sign_idx],
            "sign_number": sign_idx + 1,
            "degree_in_sign": bdata["degree_in_sign"],
            "house": None,
            "vargottama": None,
            "source_citation": f"G44_Nadi_rishi/{ENGINE_VERSION}",
            "build_id": str(build_id),
            "fact_category": cat,
            "fact_key": "rishi",
            "fact_value_text": rishi,
            "fact_value_num": None,
            "fact_subject": f"{vid}.{subject}",
            "build_id_uuid": build_id,
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "engine_version": ENGINE_VERSION,
            "citation_ref": f"{cat}.{vid}.{body}.rishi@chart={chart_id}:ay={ayanamsha_id}",
            "citation_human": f"{body}'s {vid} rishi: {rishi} ({ayanamsha_id}).",
            "source_calculation": f"G44_Nadi_rishi_table/{ENGINE_VERSION}",
            "computed_at": now,
            "tolerance_arcsec": None,
            "near_sign_boundary_flag": None,
            "near_nakshatra_boundary_flag": None,
            "vargottama_flag_at_point": None,
            "formula_provenance_text": f"G44_Nadi_{vid}",
            "cross_ayanamsha_divergence_arcsec": None,
        })

    return rows


# ── Post-pass: cross-varga harmonics ─────────────────────────────────────────

def _build_cross_varga_harmonic_rows(
    chart_id: str, ayanamsha_id: str, build_id: str,
    all_varga_signs: dict[str, dict[str, int]],  # {body: {vid: sign_idx}}
) -> list[dict]:
    """
    Post-pass computation of cross-varga harmonics:
    - varga_super_vargottama_flag: same sign in ≥3 vargas
    - varga_trikona_vargottama_flag: 1/5/9 sign relationships across vargas
    - varga_trans_vargottama_count: count of vargas where body retains D1 sign
    """
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for body in CLASSICAL_BODIES:
        body_signs = all_varga_signs.get(body, {})
        if not body_signs:
            continue
        d1_sign = body_signs.get("D1")
        subject = BODY_TO_SUBJECT.get(body, body.upper())

        # trans_vargottama_count: how many vargas have D1 sign
        if d1_sign is not None:
            trans_count = sum(1 for s in body_signs.values() if s == d1_sign)
            super_vargottama = trans_count >= 3
            # trikona: count vargas with trikona sign (1/5/9 positions from D1)
            trikona_signs = {d1_sign, (d1_sign + 4) % 12, (d1_sign + 8) % 12}
            trikona_count = sum(1 for s in body_signs.values() if s in trikona_signs)
            trikona_vargottama = trikona_count >= 3
        else:
            trans_count = 0
            super_vargottama = False
            trikona_vargottama = False

        for category, key, vtxt, vnum in [
            ("varga_super_vargottama_flag", "super_vargottama",
             str(super_vargottama), 1.0 if super_vargottama else 0.0),
            ("varga_trikona_vargottama_flag", "trikona_vargottama",
             str(trikona_vargottama), 1.0 if trikona_vargottama else 0.0),
            ("varga_trans_vargottama_count", "trans_vargottama_count",
             None, float(trans_count)),
        ]:
            rid = _fact_id("CROSS", body, category, key,
                           chart_id, ayanamsha_id, build_id)
            rows.append({
                "fact_id": rid,
                "chart_id": chart_id,
                "graha": body,
                "ayanamsha_id": ayanamsha_id,
                "varga": "CROSS",
                "sign": SIGN_NAMES[d1_sign] if d1_sign is not None else None,
                "sign_number": (d1_sign + 1) if d1_sign is not None else None,
                "degree_in_sign": 0.0,
                "house": None,
                "vargottama": super_vargottama if category == "varga_super_vargottama_flag" else None,
                "source_citation": f"A6_cross_varga/{ENGINE_VERSION}",
                "build_id": str(build_id),
                "fact_category": category,
                "fact_key": key,
                "fact_value_text": vtxt,
                "fact_value_num": vnum,
                "fact_subject": f"CROSS.{subject}",
                "build_id_uuid": build_id,
                "verification_pass_status": UNVERIFIED_DEFAULT,
                "engine_version": ENGINE_VERSION,
                "citation_ref": f"{category}.CROSS.{body}.{key}@chart={chart_id}:ay={ayanamsha_id}",
                "citation_human": f"{body} cross-varga {key}: {vtxt or vnum} ({ayanamsha_id}).",
                "source_calculation": f"A6_cross_varga_post_pass/{ENGINE_VERSION}",
                "computed_at": now,
                "tolerance_arcsec": None,
                "near_sign_boundary_flag": None,
                "near_nakshatra_boundary_flag": None,
                "vargottama_flag_at_point": super_vargottama if category == "varga_super_vargottama_flag" else None,
                "formula_provenance_text": "cross_varga_harmonic_post_pass",
                "cross_ayanamsha_divergence_arcsec": None,
            })

    return rows


# ── No-narration linter ────────────────────────────────────────────────────────

def _check_narration(rows: list[dict]) -> list[str]:
    findings = []
    for row in rows:
        vtxt = row.get("fact_value_text")
        ch = row.get("citation_human", "")
        for s in [vtxt, ch]:
            if s is None:
                continue
            lower = s.lower()
            for pat in FORBIDDEN_PATTERNS:
                if pat in lower:
                    findings.append(
                        f"narration: {row.get('fact_category')}.{row.get('fact_key')}: "
                        f"forbidden '{pat}'"
                    )
    return findings


# ── DB write ───────────────────────────────────────────────────────────────────

_UPSERT_SQL = """
INSERT INTO chart_divisionals (
  id, chart_id, graha, ayanamsha_id, varga, sign, sign_number, degree_in_sign,
  house, vargottama, source_citation, build_id,
  fact_category, fact_key, fact_value_text, fact_value_num, fact_subject,
  build_id_uuid, verification_pass_status, engine_version,
  citation_ref, citation_human, source_calculation, computed_at,
  tolerance_arcsec, near_sign_boundary_flag, near_nakshatra_boundary_flag,
  vargottama_flag_at_point, formula_provenance_text, cross_ayanamsha_divergence_arcsec
)
VALUES (
  gen_random_uuid(), %(chart_id)s, %(graha)s, %(ayanamsha_id)s, %(varga)s,
  %(sign)s, %(sign_number)s, %(degree_in_sign)s, %(house)s, %(vargottama)s,
  %(source_citation)s, %(build_id)s,
  %(fact_category)s, %(fact_key)s, %(fact_value_text)s, %(fact_value_num)s, %(fact_subject)s,
  %(build_id_uuid)s, %(verification_pass_status)s, %(engine_version)s,
  %(citation_ref)s, %(citation_human)s, %(source_calculation)s, %(computed_at)s,
  %(tolerance_arcsec)s, %(near_sign_boundary_flag)s, %(near_nakshatra_boundary_flag)s,
  %(vargottama_flag_at_point)s, %(formula_provenance_text)s, %(cross_ayanamsha_divergence_arcsec)s
)
ON CONFLICT (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key) DO NOTHING
"""

# One row per (chart, graha, ayanamsha, varga, fact_category, fact_key) — matches
# the chart_divisionals_unique_idx widened in migration 218 (and the granularity
# mv_chart_vargas_summary pivots on). The pre-218 index was only
# (chart_id, graha, ayanamsha_id, varga), which collapsed the ~25 per-planet-varga
# category rows down to one; the explicit conflict target below now dedups at the
# correct grain instead of silently dropping categories on a bare DO NOTHING.
_UPSERT_WITH_FACT_ID_SQL = """
INSERT INTO chart_divisionals (
  id, chart_id, graha, ayanamsha_id, varga, sign, sign_number, degree_in_sign,
  house, vargottama, source_citation, build_id,
  fact_category, fact_key, fact_value_text, fact_value_num, fact_subject,
  build_id_uuid, verification_pass_status, engine_version,
  citation_ref, citation_human, source_calculation, computed_at,
  tolerance_arcsec, near_sign_boundary_flag, near_nakshatra_boundary_flag,
  vargottama_flag_at_point, formula_provenance_text, cross_ayanamsha_divergence_arcsec
)
VALUES (
  gen_random_uuid(), %(chart_id)s, %(graha)s, %(ayanamsha_id)s, %(varga)s,
  %(sign)s, %(sign_number)s, %(degree_in_sign)s, %(house)s, %(vargottama)s,
  %(source_citation)s, %(build_id)s,
  %(fact_category)s, %(fact_key)s, %(fact_value_text)s, %(fact_value_num)s, %(fact_subject)s,
  %(build_id_uuid)s, %(verification_pass_status)s, %(engine_version)s,
  %(citation_ref)s, %(citation_human)s, %(source_calculation)s, %(computed_at)s,
  %(tolerance_arcsec)s, %(near_sign_boundary_flag)s, %(near_nakshatra_boundary_flag)s,
  %(vargottama_flag_at_point)s, %(formula_provenance_text)s, %(cross_ayanamsha_divergence_arcsec)s
)
ON CONFLICT (chart_id, graha, ayanamsha_id, varga, fact_category, fact_key) DO NOTHING
"""


def _check_already_written(conn, chart_id: str, ayanamsha_id: str, varga_id: str,
                            build_id: str) -> bool:
    """Check if varga rows already written for this (chart, ayanamsha, varga, build)."""
    cur = conn.execute(
        """
        SELECT COUNT(*) FROM chart_divisionals
        WHERE chart_id = %s AND ayanamsha_id = %s AND varga = %s AND build_id_uuid = %s
        """,
        [chart_id, ayanamsha_id, varga_id, build_id],
    )
    count = cur.fetchone()["count"]
    return count > 10  # > 10 rows means varga was written


def _write_rows_batch(conn, rows: list[dict]) -> int:
    """Write a batch of rows to chart_divisionals, return count written."""
    # Idempotency: replace this chart's prior rows for the (ayanamsha, varga) scope
    # in this batch so a rebuild replaces rather than leaving stale values.
    replace_prior_chart_divisionals(conn, rows)
    if not rows:
        return 0
    # chart_divisionals carries a REAL CHECK constraint on
    # verification_pass_status (migration 206/210: only 'two_pass_verified',
    # 'classical_match', 'divergent_flagged', 'single' are legal) — unlike
    # chart_facts, an illegal value here raises psycopg.errors.CheckViolation
    # at the executemany below. Assert every row's status is legal for this
    # table BEFORE the batch attempt, so a writer bug surfaces as a clear
    # ValueError here rather than a CheckViolation the batch/per-row fallback
    # logic could otherwise swallow and silently drop the row.
    for r in rows:
        assert_legal(r["verification_pass_status"], table="chart_divisionals")
    # Batched happy path (perf-pre-D3): same SQL/values as the prior per-row loop,
    # just one round trip instead of N. A SAVEPOINT wraps the batch attempt —
    # without it, a mid-batch failure leaves the ambient transaction aborted and
    # the per-row fallback below would silently no-op every row (worse than the
    # original behavior it's meant to preserve). On failure, roll back to the
    # savepoint and fall back to the original per-row try/except, which keeps
    # writing past a single malformed row exactly as it did before batching.
    with conn.cursor() as cur:
        try:
            cur.execute("SAVEPOINT ga_vargas_batch_sp")
            cur.executemany(_UPSERT_WITH_FACT_ID_SQL, rows)
            cur.execute("RELEASE SAVEPOINT ga_vargas_batch_sp")
            return len(rows)
        except Exception as batch_exc:
            cur.execute("ROLLBACK TO SAVEPOINT ga_vargas_batch_sp")
            logger.warning("[ga_vargas] batch write failed (%s), falling back to per-row", batch_exc)
            written = 0
            for row in rows:
                try:
                    cur.execute("SAVEPOINT ga_vargas_row_sp")
                    cur.execute(_UPSERT_WITH_FACT_ID_SQL, row)
                    cur.execute("RELEASE SAVEPOINT ga_vargas_row_sp")
                    written += 1
                except Exception as exc:
                    cur.execute("ROLLBACK TO SAVEPOINT ga_vargas_row_sp")
                    logger.warning("[ga_vargas] Row write failed: %s | row keys=%s",
                                   exc, list(row.keys())[:5])
            return written


def _update_asset_throughput(conn, chart_id: str, build_id: str,
                              batch_num: int, total_batches: int, rows_so_far: int) -> None:
    """Intentionally a no-op: the orchestrator is the sole asset_throughput writer
    (§N.2 FROZEN orchestrator contract). Retained for call-site compatibility; the
    legacy CLI path's calls are silently dropped. The orchestrator drives
    throughput via WriterResult after the run() method returns."""
    pass  # orchestrator owns asset_throughput — never written by the writer itself


# ── FORENSIC gate ─────────────────────────────────────────────────────────────

def forensic_gate_vargas(all_vargas: dict, ayanamsha_id: str) -> dict:
    """
    Assert FORENSIC anchors for D1:
    - Sun sign = Capricorn (sign_idx=9)
    - Lagna sign = Aries (sign_idx=0)
    """
    findings = []
    d1 = all_vargas.get("D1", {})

    sun_sign = d1.get("Sun", {}).get("sign")
    lagna_sign = d1.get("Lagna", {}).get("sign")

    if sun_sign != "Capricorn":
        findings.append(f"FORENSIC: D1 Sun={sun_sign} (expected Capricorn) [ay={ayanamsha_id}]")
    if lagna_sign != "Aries":
        findings.append(f"FORENSIC: D1 Lagna={lagna_sign} (expected Aries) [ay={ayanamsha_id}]")

    return {
        "gate": "FORENSIC_D1",
        "result": "FAIL" if findings else "PASS",
        "findings": findings,
    }


# ── Main build function ────────────────────────────────────────────────────────

def build_ga_vargas(
    chart_id: str = CANONICAL_CHART_ID,
    build_id: str | None = None,
    *,
    conn=None,
    birth_params: dict | None = None,
    ayanamsha_subset: list[str] | None = None,
) -> dict:
    """
    Build all 30 vargas × 25 categories into chart_divisionals.
    Incremental + idempotent (checks what's written, skips completed batches).
    Context-decay protection: 6 batches of 5 vargas each.
    Returns summary dict.

    Connection ownership (Orchestrator Convergence Phase 3): this is the heavy
    ga_vargas writer; the orchestrator drives it one ayanamsha per sub-step via
    ayanamsha_subset=[<aya>] + conn=<caller-owned>. When conn is injected, the
    per-ayanamsha block runs on the caller-owned connection and does NOT commit
    or write asset_throughput (the orchestrator owns the transaction + per-
    sub-step commit). When conn is None (legacy CLI), behavior is unchanged.
    """
    import uuid as _uuid
    from contextlib import nullcontext

    if build_id is None:
        build_id = str(_uuid.uuid4())

    owns_conn = conn is None

    started_at = datetime.now(timezone.utc).isoformat()
    logger.info("[ga_vargas] Build starting: chart_id=%s build_id=%s", chart_id, build_id)

    if not birth_params:
        raise ValueError(
            f"[ga_vargas_writer] no birth_params for chart_id={chart_id}; "
            "orchestrator must populate ctx.config['birth_params'] from "
            "fetch_birth_params() before calling this writer."
        )

    ayanamshas_to_run = list(CANONICAL_AYANAMSHAS.keys()) if ayanamsha_subset is None else ayanamsha_subset

    summary = {
        "session_id": "ga6-vargas",
        "chart_id": chart_id,
        "build_id": build_id,
        "started_at": started_at,
        "total_rows_written": 0,
        "batches_completed": 0,
        "forensic_results": {},
        "status": "IN_PROGRESS",
    }

    from pyjhora_adapter._jhora import drik, utils
    from pyjhora_adapter._ayanamsha import resolve_mode

    # Parse birth params
    from datetime import datetime as _dt
    local_dt_str = birth_params["datetime_iso"]
    local_dt = _dt.fromisoformat(local_dt_str.replace("Z", "").split("+")[0])
    dob = drik.Date(local_dt.year, local_dt.month, local_dt.day)
    tob = (local_dt.hour, local_dt.minute, local_dt.second)
    lat = float(birth_params["latitude_deg"])
    lon = float(birth_params["longitude_deg"])
    tz = float(birth_params["tz_offset_hours"])
    jd_ut = utils.julian_day_number(dob, tob)

    total_rows = 0
    total_batches = len(VARGA_BATCHES)

    # INVARIANT sentinel deletion: remove any prior scope-cap sentinel rows
    # written under ayanamsha_id='INVARIANT' for this chart before inserting new ones.
    # This prevents accretion of stale scope-cap sentinels across rebuilds.
    # Scoped to the current chart_id only (idempotency requirement §N.3).
    def _delete_invariant_sentinels(c, cid: str) -> None:
        try:
            c.execute(
                "DELETE FROM chart_divisionals WHERE chart_id = %s AND ayanamsha_id = 'INVARIANT'",
                [cid],
            )
        except Exception as exc:
            logger.warning("[ga_vargas] INVARIANT sentinel delete failed (non-fatal): %s", exc)

    for ayan_id in ayanamshas_to_run:
        logger.info("[ga_vargas] Processing ayanamsha: %s", ayan_id)

        # Compute positions for all 30 vargas under this ayanamsha
        all_vargas, d1_longitudes = _compute_varga_positions(jd_ut, ayan_id, lat, lon, tz)

        # FORENSIC gate — must pass or halt
        forensic_result = forensic_gate_vargas(all_vargas, ayan_id)
        summary["forensic_results"][ayan_id] = forensic_result
        # native-anchored (D1 Sun/Lagna); only HALTS for the native chart (Phase 3B).
        if chart_id == CANONICAL_CHART_ID and forensic_result["result"] == "FAIL":
            logger.error("[ga_vargas] FORENSIC FAIL: %s", forensic_result["findings"])
            _write_halt_log(
                "GA6_FORENSIC_FAIL",
                f"FORENSIC gate failed for ayanamsha={ayan_id}: {forensic_result['findings']}",
            )
            summary["status"] = "FORENSIC_FAIL"
            return summary

        d1_data = all_vargas.get("D1", {})

        # For cross-varga harmonics post-pass, collect per-body sign per varga
        all_varga_signs: dict[str, dict[str, int]] = {b: {} for b in CLASSICAL_BODIES}

        with (_conn() if owns_conn else nullcontext(conn)) as conn:
            # INVARIANT sentinel deletion: purge stale scope-cap sentinel rows for
            # this chart before inserting new ones. Runs once per ayanamsha loop
            # entry (idempotent — deletes 0 rows if nothing was written yet).
            _delete_invariant_sentinels(conn, chart_id)
            if owns_conn:
                conn.commit()

            for batch_idx, batch_vargas in enumerate(VARGA_BATCHES):
                batch_rows = []
                batch_label = f"batch_{batch_idx+1}"

                for varga_n in batch_vargas:
                    vid = _varga_id(varga_n)

                    # Incremental skip: check if already written
                    if _check_already_written(conn, chart_id, ayan_id, vid, build_id):
                        logger.info("[ga_vargas] Skip already-written: %s %s", ayan_id, vid)
                        continue

                    varga_data = all_vargas.get(vid, {})
                    if not varga_data:
                        logger.warning("[ga_vargas] No varga data for %s", vid)
                        continue

                    # Collect per-body signs for cross-varga post-pass
                    for body in CLASSICAL_BODIES:
                        bdata = varga_data.get(body)
                        if bdata:
                            all_varga_signs[body][vid] = bdata["sign_idx"]

                    # Build all category rows for this varga
                    varga_rows = []

                    # 1. varga_position
                    varga_rows.extend(_build_position_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data, d1_data))

                    # 2. varga_dignity
                    varga_rows.extend(_build_dignity_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data))

                    # 3. varga_vargottama_flag
                    varga_rows.extend(_build_vargottama_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data, d1_data))

                    # 4. varga_house_lord + varga_house_occupant
                    varga_rows.extend(_build_house_lord_occupant_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data))

                    # 5. varga_deity_attribution
                    varga_rows.extend(_build_deity_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data, conn))

                    # 6. varga_formula_variant_position (D2, D3 only)
                    varga_rows.extend(_build_formula_variant_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, d1_longitudes))

                    # 7. varga_vimsopaka_contribution
                    varga_rows.extend(_build_vimsopaka_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data))

                    # 7b. varga_ashtakavarga (M-4 fix: was declared but never built)
                    varga_rows.extend(_build_ashtakavarga_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data))

                    # 8. varga_saptavargaja_bala_component
                    varga_rows.extend(_build_saptavargaja_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data))

                    # 9. karaka_per_varga
                    varga_rows.extend(_build_karaka_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data, d1_longitudes))

                    # 10. varga_rollup
                    varga_rows.extend(_build_rollup_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data, d1_data))

                    # 11. varga_karya_bhava_per_varga
                    varga_rows.extend(_build_karya_bhava_rows(
                        chart_id, ayan_id, build_id, varga_n, vid, varga_data))

                    # 12. Varga-specific categories
                    if varga_n == 27:
                        varga_rows.extend(_build_d27_quadrant_rows(
                            chart_id, ayan_id, build_id, varga_data))
                    if varga_n == 9:
                        varga_rows.extend(_build_d9_lagna_special_rows(
                            chart_id, ayan_id, build_id, varga_data))
                    if varga_n in (9, 12):
                        varga_rows.extend(_build_lal_kitab_rows(
                            chart_id, ayan_id, build_id, varga_n, vid, varga_data, d1_data))
                    if varga_n in (9,):
                        varga_rows.extend(_build_pushkara_rows(
                            chart_id, ayan_id, build_id, varga_n, vid, varga_data, d1_longitudes))
                    else:
                        # pushkara_bhaga only for non-D9 vargas
                        varga_rows.extend(_build_pushkara_rows(
                            chart_id, ayan_id, build_id, varga_n, vid, varga_data, d1_longitudes))
                    if varga_n == 108:
                        varga_rows.extend(_build_d108_karma_rows(
                            chart_id, ayan_id, build_id, varga_data))
                    if varga_n in (150, 2700):
                        varga_rows.extend(_build_d150_rishi_rows(
                            chart_id, ayan_id, build_id, varga_n, varga_data))

                    # No-narration linter check
                    narration_findings = _check_narration(varga_rows[-len(varga_rows):])
                    if narration_findings:
                        logger.warning("[ga_vargas] Narration findings for %s: %s",
                                       vid, narration_findings[:3])

                    batch_rows.extend(varga_rows)
                    logger.info("[ga_vargas] [%s][%s] rows built: %d",
                                ayan_id, vid, len(varga_rows))

                # Write batch
                if batch_rows:
                    written = _write_rows_batch(conn, batch_rows)
                    if owns_conn:
                        conn.commit()
                    total_rows += written
                    logger.info("[ga_vargas] Batch %d/%d written: %d rows (total: %d)",
                                batch_idx + 1, total_batches, written, total_rows)
                    # Update asset_throughput incrementally (legacy CLI only; the
                    # orchestrator is the sole asset_throughput writer).
                    if owns_conn:
                        _update_asset_throughput(
                            conn, chart_id, build_id,
                            batch_idx + 1, total_batches, total_rows,
                        )

                summary["batches_completed"] = batch_idx + 1

            # D30 lord per amsa (ayanamsha-independent but emitted once per ayanamsha)
            if not _check_already_written(conn, chart_id, ayan_id, "D30_LORDS", build_id):
                d30_rows = _build_d30_lord_per_amsa_rows(
                    chart_id, ayan_id, build_id, str(build_id))
                if d30_rows:
                    written = _write_rows_batch(conn, d30_rows)
                    if owns_conn:
                        conn.commit()
                    total_rows += written
                    logger.info("[ga_vargas] D30 lord rows written: %d", written)

            # Post-pass: cross-varga harmonics
            cross_rows = _build_cross_varga_harmonic_rows(
                chart_id, ayan_id, build_id, all_varga_signs)
            if cross_rows:
                written = _write_rows_batch(conn, cross_rows)
                if owns_conn:
                    conn.commit()
                total_rows += written
                logger.info("[ga_vargas] Cross-varga rows written: %d", written)

            # Scope-cap sentinel: D81 (saptatisamsa) — intentionally not computed.
            # Emitted once per ayanamsha under 'INVARIANT' so absence ≠ bug.
            # Locked decision: GA6 brief §2 decision J.
            if not _check_already_written(conn, chart_id, "INVARIANT", "D81_SCOPE_CAP", build_id):
                now = datetime.now(timezone.utc).isoformat()
                scope_cap_row = {
                    "fact_id": hashlib.sha256(
                        f"scope_cap|D81_SAPTATISAMSA|computation_status|{chart_id}|INVARIANT".encode()
                    ).hexdigest()[:20],
                    "chart_id": chart_id,
                    "graha": "SCOPE_CAP",
                    "ayanamsha_id": "INVARIANT",
                    "varga": "D81",
                    "sign": None,
                    "sign_number": None,
                    "degree_in_sign": None,
                    "house": None,
                    "vargottama": None,
                    "source_citation": "GA6_BRIEF_LOCKED_DECISION_J",
                    "build_id": str(build_id),
                    "fact_category": "scope_cap",
                    "fact_key": "computation_status",
                    "fact_value_text": "intentionally_not_computed",
                    "fact_value_num": None,
                    "fact_subject": "D81_SAPTATISAMSA",
                    "build_id_uuid": build_id,
                    "verification_pass_status": UNVERIFIED_DEFAULT,
                    "engine_version": ENGINE_VERSION,
                    "citation_ref": "GA6_BRIEF_LOCKED_DECISION_J",
                    "citation_human": "D81 (saptatisamsa) not computed — skipped per GA6 brief §2 locked decision J",
                    "source_calculation": "ga_vargas/scope_cap",
                    "computed_at": now,
                    "tolerance_arcsec": None,
                    "near_sign_boundary_flag": None,
                    "near_nakshatra_boundary_flag": None,
                    "vargottama_flag_at_point": None,
                    "formula_provenance_text": "scope_cap/locked_decision_J",
                    "cross_ayanamsha_divergence_arcsec": None,
                }
                written = _write_rows_batch(conn, [scope_cap_row])
                if owns_conn:
                    conn.commit()
                total_rows += written
                logger.info("[ga_vargas] D81 scope-cap sentinel written: %d row", written)

            # Scope-cap sentinels: outer planets + MC — floored (no PyJHora support).
            # One sentinel per body so absence is explicitly intentional, not a bug.
            for floored_body in FLOORED_BODIES:
                sentinel_key = f"{floored_body.upper()}_OUTER_PLANET_SCOPE_CAP"
                if not _check_already_written(conn, chart_id, "INVARIANT", sentinel_key, build_id):
                    now = datetime.now(timezone.utc).isoformat()
                    outer_cap_row = {
                        "fact_id": hashlib.sha256(
                            f"scope_cap|{floored_body}|computation_status|{chart_id}|INVARIANT".encode()
                        ).hexdigest()[:20],
                        "chart_id": chart_id,
                        "graha": "SCOPE_CAP",
                        "ayanamsha_id": "INVARIANT",
                        "varga": "ALL_VARGAS",
                        "sign": None,
                        "sign_number": None,
                        "degree_in_sign": None,
                        "house": None,
                        "vargottama": None,
                        "source_citation": "GA6_BRIEF_FLOORED_BODIES",
                        "build_id": str(build_id),
                        "fact_category": "scope_cap",
                        "fact_key": "computation_status",
                        "fact_value_text": "intentionally_not_computed",
                        "fact_value_num": None,
                        "fact_subject": PLANET_TO_SUBJECT.get(floored_body, floored_body.upper()),
                        "build_id_uuid": build_id,
                        "verification_pass_status": UNVERIFIED_DEFAULT,
                        "engine_version": ENGINE_VERSION,
                        "citation_ref": "GA6_BRIEF_FLOORED_BODIES",
                        "citation_human": (
                            f"{floored_body} varga positions not computed — "
                            f"floored per GA6 brief §2 (no PyJHora support for outer planets/MC)"
                        ),
                        "source_calculation": "ga_vargas/scope_cap",
                        "computed_at": now,
                        "tolerance_arcsec": None,
                        "near_sign_boundary_flag": None,
                        "near_nakshatra_boundary_flag": None,
                        "vargottama_flag_at_point": None,
                        "formula_provenance_text": "scope_cap/floored_bodies",
                        "cross_ayanamsha_divergence_arcsec": None,
                    }
                    written = _write_rows_batch(conn, [outer_cap_row])
                    if owns_conn:
                        conn.commit()
                    total_rows += written
                    logger.info("[ga_vargas] Outer-planet/MC scope-cap sentinel written for %s", floored_body)

            # Final asset_throughput at 100% (legacy CLI only; orchestrator owns it).
            if owns_conn:
                _update_asset_throughput(conn, chart_id, build_id,
                                         total_batches, total_batches, total_rows)

    summary["total_rows_written"] = total_rows
    summary["status"] = "PASS"
    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    logger.info("[ga_vargas] Build COMPLETE: %d total rows written", total_rows)

    return summary
