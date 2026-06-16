"""
brahmagyan.l0_medical — Medical/Ayurvedic Subsystem Gate-1: L0 static reference data.
========================================================================================

Populates two classical reference tables with hardcoded, source-cited Ayurvedic
Jyotish mappings. ZERO LLM generation. ZERO live computation. Pure deterministic
Python data.

Tables written:
  bg_medical_mappings     — 9 graha → dosha/dhatu/organ/body-part/disease-tendency
  bg_nakshatra_medical    — 27 nakshatras → body-part correspondences

Volume floors:
  bg_medical_mappings:    >= 9 rows (Sun, Moon, Mars, Mercury, Jupiter, Venus,
                                      Saturn, Rahu, Ketu)
  bg_nakshatra_medical:   >= 27 rows (all 27 classical nakshatras)

Acceptance gates:
  - All rows have non-empty classical_citation (§N hard gate)
  - bg_medical_mappings has exactly 9 grahas (all 9 classical Jyotish planets)
  - bg_nakshatra_medical has exactly 27 nakshatras (IDs 1–27)

FORENSIC anchor:
  - Nakshatra #25 = Purva Bhadrapada → body_part = 'left_side'
    (native Moon nakshatra per FORENSIC anchor: Moon = Purva Bhadrapada)

MEDICAL DISCLAIMER (NON-NEGOTIABLE):
  This module seeds Jyotish reference data ONLY. No row in this module or any
  dependent ga_medical row constitutes a medical diagnosis. ga_medical rows
  MUST carry indication_tier='jyotish_indication' and not_diagnosis=TRUE.
  See ga_medical_writer.py for enforcement.

Sources:
  BPHS_CH18 = Brihat Parasara Hora Sastra, Chapter 18 (Nidana Adhyaya — disease
               indication per graha placement / lordship)
  AH        = Ashtanga Hridayam (Vagbhata) — graha–dosha correspondences
  CS        = Charaka Samhita — graha–constitution correspondences
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Source citations ───────────────────────────────────────────────────────────

BPHS_CH18_AH = "BPHS Ch.18 / Ashtanga Hridayam"
BPHS_CH18_CS = "BPHS Ch.18 / Charaka Samhita"
BPHS_CH18_RAHU = "BPHS Ch.18 (Rahu disease indications)"
BPHS_CH18_KETU = "BPHS Ch.18 (Ketu disease indications)"
AH_BPHS       = "Ashtanga Hridayam / BPHS"

# ── Medical graha mappings (9 classical Jyotish grahas) ───────────────────────

MEDICAL_MAPPINGS: list[dict] = [
    {
        "graha":            "Sun",
        "dosha":            ["pitta"],
        "dhatu":            ["asthi"],
        "organ_systems":    ["heart", "eyes"],
        "body_part":        ["right_eye", "spine", "heart"],
        "disease_tendency": ["heart_disease", "eye_problems", "bone_disorders"],
        "classical_citation": BPHS_CH18_AH,
    },
    {
        "graha":            "Moon",
        "dosha":            ["kapha", "vata"],
        "dhatu":            ["rasa"],
        "organ_systems":    ["mind", "lungs", "stomach"],
        "body_part":        ["left_eye", "breast", "uterus"],
        "disease_tendency": ["mental_disorders", "respiratory", "digestive"],
        "classical_citation": BPHS_CH18_CS,
    },
    {
        "graha":            "Mars",
        "dosha":            ["pitta"],
        "dhatu":            ["rakta", "mamsa"],
        "organ_systems":    ["marrow", "red_blood_cells"],
        "body_part":        ["right_ear", "bile", "genitals"],
        "disease_tendency": ["blood_disorders", "inflammation", "accidents"],
        "classical_citation": BPHS_CH18_AH,
    },
    {
        "graha":            "Mercury",
        "dosha":            ["tridosha"],
        "dhatu":            ["skin", "nervous_tissue"],
        "organ_systems":    ["nervous_system", "skin"],
        "body_part":        ["tongue", "hands", "arms"],
        "disease_tendency": ["nervous_disorders", "skin_diseases", "speech_disorders"],
        "classical_citation": BPHS_CH18_CS,
    },
    {
        "graha":            "Jupiter",
        "dosha":            ["kapha"],
        "dhatu":            ["meda", "majja"],
        "organ_systems":    ["liver", "pancreas"],
        "body_part":        ["thighs", "liver", "ears"],
        "disease_tendency": ["obesity", "liver_disorders", "diabetes"],
        "classical_citation": BPHS_CH18_AH,
    },
    {
        "graha":            "Venus",
        "dosha":            ["kapha", "vata"],
        "dhatu":            ["shukra", "rasa"],
        "organ_systems":    ["reproductive", "kidneys"],
        "body_part":        ["face", "neck", "genitals"],
        "disease_tendency": ["reproductive_disorders", "venereal", "kidney_stones"],
        "classical_citation": BPHS_CH18_CS,
    },
    {
        "graha":            "Saturn",
        "dosha":            ["vata"],
        "dhatu":            ["asthi", "nervous"],
        "organ_systems":    ["large_intestine", "spleen"],
        "body_part":        ["teeth", "bones", "joints", "legs"],
        "disease_tendency": ["chronic_diseases", "arthritis", "paralysis", "vayu_disorders"],
        "classical_citation": BPHS_CH18_AH,
    },
    {
        "graha":            "Rahu",
        "dosha":            ["vata"],
        "dhatu":            ["skin"],
        "organ_systems":    ["nervous_system"],
        "body_part":        ["skin", "limbs"],
        "disease_tendency": ["mysterious_diseases", "cancer_indications", "poisons", "skin"],
        "classical_citation": BPHS_CH18_RAHU,
    },
    {
        "graha":            "Ketu",
        "dosha":            ["pitta", "vata"],
        "dhatu":            ["marrow"],
        "organ_systems":    ["intestines"],
        "body_part":        ["abdomen", "anus"],
        "disease_tendency": ["intestinal_worms", "abdominal_disorders", "moksha_related"],
        "classical_citation": BPHS_CH18_KETU,
    },
]

# ── Nakshatra body-part mappings (27 classical nakshatras) ────────────────────
# FORENSIC: #25 Purva Bhadrapada = 'left_side' (native Moon nakshatra)

NAKSHATRA_MEDICAL: list[dict] = [
    {"nakshatra_name": "Ashwini",           "nakshatra_number": 1,  "body_part": "feet/knees",      "classical_citation": AH_BPHS},
    {"nakshatra_name": "Bharani",           "nakshatra_number": 2,  "body_part": "head",            "classical_citation": AH_BPHS},
    {"nakshatra_name": "Krittika",          "nakshatra_number": 3,  "body_part": "eyes/face",       "classical_citation": AH_BPHS},
    {"nakshatra_name": "Rohini",            "nakshatra_number": 4,  "body_part": "forehead/neck",   "classical_citation": AH_BPHS},
    {"nakshatra_name": "Mrigashira",        "nakshatra_number": 5,  "body_part": "eyes/eyebrows",   "classical_citation": AH_BPHS},
    {"nakshatra_name": "Ardra",             "nakshatra_number": 6,  "body_part": "eyes/mind",       "classical_citation": AH_BPHS},
    {"nakshatra_name": "Punarvasu",         "nakshatra_number": 7,  "body_part": "ears/chest",      "classical_citation": AH_BPHS},
    {"nakshatra_name": "Pushya",            "nakshatra_number": 8,  "body_part": "face/mouth",      "classical_citation": AH_BPHS},
    {"nakshatra_name": "Ashlesha",          "nakshatra_number": 9,  "body_part": "ears/skin",       "classical_citation": AH_BPHS},
    {"nakshatra_name": "Magha",             "nakshatra_number": 10, "body_part": "nose",            "classical_citation": AH_BPHS},
    {"nakshatra_name": "Purva Phalguni",    "nakshatra_number": 11, "body_part": "right_hand",      "classical_citation": AH_BPHS},
    {"nakshatra_name": "Uttara Phalguni",   "nakshatra_number": 12, "body_part": "right_side",      "classical_citation": AH_BPHS},
    {"nakshatra_name": "Hasta",             "nakshatra_number": 13, "body_part": "fingers/hands",   "classical_citation": AH_BPHS},
    {"nakshatra_name": "Chitra",            "nakshatra_number": 14, "body_part": "forehead",        "classical_citation": AH_BPHS},
    {"nakshatra_name": "Swati",             "nakshatra_number": 15, "body_part": "chest",           "classical_citation": AH_BPHS},
    {"nakshatra_name": "Vishakha",          "nakshatra_number": 16, "body_part": "arms",            "classical_citation": AH_BPHS},
    {"nakshatra_name": "Anuradha",          "nakshatra_number": 17, "body_part": "abdomen",         "classical_citation": AH_BPHS},
    {"nakshatra_name": "Jyeshtha",          "nakshatra_number": 18, "body_part": "right_side_body", "classical_citation": AH_BPHS},
    {"nakshatra_name": "Mula",              "nakshatra_number": 19, "body_part": "feet/hips",       "classical_citation": AH_BPHS},
    {"nakshatra_name": "Purva Ashadha",     "nakshatra_number": 20, "body_part": "thighs",          "classical_citation": AH_BPHS},
    {"nakshatra_name": "Uttara Ashadha",    "nakshatra_number": 21, "body_part": "thighs/knees",    "classical_citation": AH_BPHS},
    {"nakshatra_name": "Shravana",          "nakshatra_number": 22, "body_part": "ears",            "classical_citation": AH_BPHS},
    {"nakshatra_name": "Dhanishtha",        "nakshatra_number": 23, "body_part": "back/knees",      "classical_citation": AH_BPHS},
    {"nakshatra_name": "Shatabhisha",       "nakshatra_number": 24, "body_part": "right_thigh",     "classical_citation": AH_BPHS},
    {"nakshatra_name": "Purva Bhadrapada",  "nakshatra_number": 25, "body_part": "left_side",       "classical_citation": AH_BPHS},
    {"nakshatra_name": "Uttara Bhadrapada", "nakshatra_number": 26, "body_part": "feet",            "classical_citation": AH_BPHS},
    {"nakshatra_name": "Revati",            "nakshatra_number": 27, "body_part": "feet/abdomen",    "classical_citation": AH_BPHS},
]


# ── Seed functions ─────────────────────────────────────────────────────────────

def seed_medical_mappings(
    conn: Any,
    build_id: str,
    dry_run: bool = False,
    autocommit: bool = False,
) -> dict[str, int]:
    """
    Seed bg_medical_mappings and bg_nakshatra_medical from in-module constants.

    Returns a dict with keys:
      'bg_medical_mappings'  → number of rows upserted
      'bg_nakshatra_medical' → number of rows upserted

    L0 idempotency: ON CONFLICT DO UPDATE — safe to call multiple times.
    autocommit=False (default): caller (orchestrator) owns the transaction.
    """
    if dry_run:
        logger.info("[l0_medical] dry_run=True — skipping DB writes")
        return {"bg_medical_mappings": 0, "bg_nakshatra_medical": 0}

    counts: dict[str, int] = {}

    # ── bg_medical_mappings ────────────────────────────────────────────────────
    medical_sql = """
        INSERT INTO bg_medical_mappings
            (graha, dosha, dhatu, organ_systems, body_part, disease_tendency,
             classical_citation)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (graha) DO UPDATE SET
            dosha              = EXCLUDED.dosha,
            dhatu              = EXCLUDED.dhatu,
            organ_systems      = EXCLUDED.organ_systems,
            body_part          = EXCLUDED.body_part,
            disease_tendency   = EXCLUDED.disease_tendency,
            classical_citation = EXCLUDED.classical_citation
    """
    inserted_mappings = 0
    with conn.cursor() as cur:
        for row in MEDICAL_MAPPINGS:
            cur.execute(medical_sql, (
                row["graha"],
                row["dosha"],
                row["dhatu"],
                row["organ_systems"],
                row["body_part"],
                row["disease_tendency"],
                row["classical_citation"],
            ))
            inserted_mappings += cur.rowcount or 0
    counts["bg_medical_mappings"] = inserted_mappings
    logger.info("[l0_medical] bg_medical_mappings: %d rows upserted", inserted_mappings)

    # ── bg_nakshatra_medical ───────────────────────────────────────────────────
    nak_sql = """
        INSERT INTO bg_nakshatra_medical
            (nakshatra_name, nakshatra_number, body_part, classical_citation)
        VALUES
            (%s, %s, %s, %s)
        ON CONFLICT (nakshatra_name) DO UPDATE SET
            nakshatra_number   = EXCLUDED.nakshatra_number,
            body_part          = EXCLUDED.body_part,
            classical_citation = EXCLUDED.classical_citation
    """
    inserted_nakshatras = 0
    with conn.cursor() as cur:
        for row in NAKSHATRA_MEDICAL:
            cur.execute(nak_sql, (
                row["nakshatra_name"],
                row["nakshatra_number"],
                row["body_part"],
                row["classical_citation"],
            ))
            inserted_nakshatras += cur.rowcount or 0
    counts["bg_nakshatra_medical"] = inserted_nakshatras
    logger.info("[l0_medical] bg_nakshatra_medical: %d rows upserted", inserted_nakshatras)

    if autocommit:
        conn.commit()

    return counts


# ── Lookup helpers ─────────────────────────────────────────────────────────────

def lookup_graha_medical(graha: str) -> dict | None:
    """Return the MEDICAL_MAPPINGS entry for a graha name, or None."""
    for entry in MEDICAL_MAPPINGS:
        if entry["graha"] == graha:
            return entry
    return None


def lookup_nakshatra_body_part(nakshatra_name: str) -> str | None:
    """
    Return the body_part for a nakshatra name, or None if not found.

    FORENSIC: 'Purva Bhadrapada' → 'left_side' (native Moon nakshatra).
    """
    for entry in NAKSHATRA_MEDICAL:
        if entry["nakshatra_name"] == nakshatra_name:
            return entry["body_part"]
    return None
