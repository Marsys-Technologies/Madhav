"""
brahmagyan.l0_medical — Medical/Ayurvedic Subsystem Gate-1: L0 static reference data.
========================================================================================

Populates two classical reference tables with hardcoded, source-cited Ayurvedic
Jyotish mappings. ZERO LLM generation. ZERO live computation. Pure deterministic
Python data.

Tables written:
  bg_medical_mappings     — rows for 9 grahas + planetary combinations + dignity
                            modifiers → dosha/dhatu/organ/body-part/disease-tendency
  bg_nakshatra_medical    — 27 nakshatras → body-part + dosha correspondences

Volume floors:
  bg_medical_mappings:    >= 9 graha rows (Sun … Ketu)
                          + 6 planetary-combination rows (Tier 1)
                          + 6 dignity-modifier rows (Tier 3)
  bg_nakshatra_medical:   >= 27 rows with dosha column populated (Tier 2)

Data tiers seeded:
  Tier 0 — 9 classical graha rows (original)
  Tier 1 — Planetary-combination health indicators (BPHS Ch.18 / Sarvartha Chintamani)
  Tier 2 — 27-nakshatra × 3-dosha grid (Hora Sara / BPHS Ch.3; Ashtanga Hridayam)
  Tier 3 — Dignity-modified health indicators (BPHS Ch.18 / classical Ayurvedic astrology)

Acceptance gates:
  - All rows have non-empty classical_citation (§N hard gate)
  - bg_medical_mappings has the 9 canonical graha keys plus combination/dignity keys
  - bg_nakshatra_medical has exactly 27 nakshatras (IDs 1–27) with dosha populated

FORENSIC anchor:
  - Nakshatra #25 = Purva Bhadrapada → body_part = 'left_side', dosha = 'vata'
    (native Moon nakshatra per FORENSIC anchor: Moon = Purva Bhadrapada)

MEDICAL DISCLAIMER (NON-NEGOTIABLE):
  This module seeds Jyotish reference data ONLY. No row in this module or any
  dependent ga_medical row constitutes a medical diagnosis. ga_medical rows
  MUST carry indication_tier='jyotish_indication' and not_diagnosis=TRUE.
  See ga_medical_writer.py for enforcement.

Sources:
  BPHS_CH18    = Brihat Parasara Hora Sastra, Chapter 18 (Nidana Adhyaya — disease
                  indication per graha placement / lordship)
  BPHS_CH3     = BPHS Chapter 3 (Nakshatra characteristics — ruling deity, nature)
  AH           = Ashtanga Hridayam (Vagbhata) — graha–dosha, nakshatra–dosha
                  correspondences
  CS           = Charaka Samhita — graha–constitution correspondences
  SC           = Sarvartha Chintamani — planetary combination disease indications
  HS           = Hora Sara (Prithuyasas) — nakshatra medical correspondences
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Source citations ───────────────────────────────────────────────────────────

BPHS_CH18_AH      = "BPHS Ch.18 / Ashtanga Hridayam"
BPHS_CH18_CS      = "BPHS Ch.18 / Charaka Samhita"
BPHS_CH18_RAHU    = "BPHS Ch.18 (Rahu disease indications)"
BPHS_CH18_KETU    = "BPHS Ch.18 (Ketu disease indications)"
BPHS_CH18_SC      = "BPHS Ch.18 / Sarvartha Chintamani"
BPHS_CH18_COMBO   = "BPHS Ch.18 / Sarvartha Chintamani (graha yoga disease indications)"
BPHS_CH18_DIGNITY = "BPHS Ch.18 / classical Ayurvedic astrology (dignity modifiers)"
AH_BPHS           = "Ashtanga Hridayam / BPHS"
AH_HS_BPHS_CH3    = "Ashtanga Hridayam / Hora Sara / BPHS Ch.3"

# ── Tier 0: Medical graha mappings (9 classical Jyotish grahas) ───────────────

MEDICAL_MAPPINGS: list[dict] = [
    # ── Tier 0: 9 classical graha rows ────────────────────────────────────────
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
    # ── Tier 1: Planetary-combination health indicators ────────────────────────
    # Keyed as "Graha1+Graha2" composite strings; unique within graha TEXT column.
    # Source: BPHS Ch.18 (Nidana Adhyaya) and Sarvartha Chintamani (combination
    # disease indications). Sun+Saturn = vata aggravation via mutual opposition of
    # pitta/vata natures → bone/joint vulnerability (SC Ch. on disease yoga).
    {
        "graha":            "Sun+Saturn",
        "dosha":            ["vata", "pitta"],
        "dhatu":            ["asthi"],
        "organ_systems":    ["bones", "joints"],
        "body_part":        ["spine", "joints", "teeth"],
        "disease_tendency": ["arthritis", "bone_disorders", "vata_aggravation",
                             "joint_pain", "chronic_fatigue"],
        "classical_citation": BPHS_CH18_COMBO,
    },
    # Moon+Rahu = manas vikara (mental/psychological). BPHS Ch.18: Rahu with Moon
    # in dusthanas indicates psychological disturbance; SC endorses "chandra-rahu yoga
    # produces mental disorders."
    {
        "graha":            "Moon+Rahu",
        "dosha":            ["vata"],
        "dhatu":            ["rasa", "majja"],
        "organ_systems":    ["mind", "nervous_system"],
        "body_part":        ["brain", "mind"],
        "disease_tendency": ["manas_vikara", "psychological_disorders", "anxiety",
                             "insomnia", "phobias"],
        "classical_citation": BPHS_CH18_COMBO,
    },
    # Mars+Saturn = blood and inflammatory conditions. Both malefics; Mars rules rakta
    # (blood), Saturn rules vata obstruction → inflammatory disorders, blood stasis.
    # BPHS Ch.18 / SC on dual malefic yoga.
    {
        "graha":            "Mars+Saturn",
        "dosha":            ["pitta", "vata"],
        "dhatu":            ["rakta"],
        "organ_systems":    ["blood", "muscles"],
        "body_part":        ["joints", "muscles", "skin"],
        "disease_tendency": ["inflammatory_disorders", "blood_stasis", "accidents",
                             "surgery_risk", "chronic_inflammation"],
        "classical_citation": BPHS_CH18_COMBO,
    },
    # Mercury+Rahu = nervous system (vata-pitta). Mercury rules the nervous system;
    # Rahu amplifies and distorts → vata-pitta imbalance in neural tissue.
    # BPHS Ch.18 / SC.
    {
        "graha":            "Mercury+Rahu",
        "dosha":            ["vata", "pitta"],
        "dhatu":            ["nervous_tissue", "skin"],
        "organ_systems":    ["nervous_system", "skin"],
        "body_part":        ["nerves", "skin", "hands"],
        "disease_tendency": ["neurological_disorders", "skin_diseases",
                             "speech_disorders", "nervous_exhaustion"],
        "classical_citation": BPHS_CH18_COMBO,
    },
    # Sun afflicted in 6H/8H → heart/vitality reduction. BPHS Ch.18: Sun in 6th or
    # 8th from lagna or in combustion zone reduces ojas (vitality); heart disease
    # prone. 6H = roga sthana; 8H = ayur/death house.
    {
        "graha":            "Sun_6H_8H_afflicted",
        "dosha":            ["pitta"],
        "dhatu":            ["asthi", "ojas"],
        "organ_systems":    ["heart", "eyes"],
        "body_part":        ["heart", "spine", "right_eye"],
        "disease_tendency": ["heart_disease", "low_vitality", "eye_weakness",
                             "bone_fragility", "reduced_ojas"],
        "classical_citation": BPHS_CH18_SC,
    },
    # Moon afflicted → fluid imbalances and mental disturbance. BPHS Ch.18: afflicted
    # Moon (conjunction/aspect of Rahu, Saturn, Mars) → rasa dhatu disturbance →
    # fluid imbalances, lymphatic issues, mental instability.
    {
        "graha":            "Moon_afflicted",
        "dosha":            ["kapha", "vata"],
        "dhatu":            ["rasa"],
        "organ_systems":    ["mind", "lymphatic", "stomach"],
        "body_part":        ["breast", "uterus", "brain"],
        "disease_tendency": ["fluid_imbalances", "mental_instability",
                             "lymphatic_disorders", "hormonal_imbalance"],
        "classical_citation": BPHS_CH18_SC,
    },
    # ── Tier 3: Dignity-modified health indicators ─────────────────────────────
    # Keyed as "Graha_exalted" / "Graha_debilitated" / "Graha_combust".
    # Source: BPHS Ch.18 — exaltation strengthens the signified dhatu/organ system;
    # debilitation weakens; combustion (asta) reduces ojas in that system.
    {
        "graha":            "Sun_exalted",
        "dosha":            ["pitta"],
        "dhatu":            ["asthi"],
        "organ_systems":    ["heart", "eyes"],
        "body_part":        ["heart", "spine"],
        "disease_tendency": ["robust_constitution", "strong_vitality_pitta_excess_possible"],
        "classical_citation": BPHS_CH18_DIGNITY,
    },
    {
        "graha":            "Sun_debilitated",
        "dosha":            ["pitta"],
        "dhatu":            ["asthi"],
        "organ_systems":    ["heart", "eyes"],
        "body_part":        ["heart", "spine", "right_eye"],
        "disease_tendency": ["weak_vitality", "heart_vulnerability", "bone_weakness",
                             "reduced_ojas"],
        "classical_citation": BPHS_CH18_DIGNITY,
    },
    {
        "graha":            "Moon_debilitated",
        "dosha":            ["kapha", "vata"],
        "dhatu":            ["rasa"],
        "organ_systems":    ["mind", "stomach"],
        "body_part":        ["left_eye", "uterus", "breast"],
        "disease_tendency": ["rasa_dhatu_weakness", "mental_instability",
                             "hormonal_vulnerability", "fluid_imbalance"],
        "classical_citation": BPHS_CH18_DIGNITY,
    },
    {
        "graha":            "Mars_debilitated",
        "dosha":            ["pitta"],
        "dhatu":            ["rakta", "mamsa"],
        "organ_systems":    ["blood", "muscles"],
        "body_part":        ["bile", "genitals"],
        "disease_tendency": ["anemia", "muscular_weakness", "low_immunity",
                             "pitta_deficiency"],
        "classical_citation": BPHS_CH18_DIGNITY,
    },
    {
        "graha":            "Saturn_exalted",
        "dosha":            ["vata"],
        "dhatu":            ["asthi", "nervous"],
        "organ_systems":    ["large_intestine", "spleen"],
        "body_part":        ["bones", "joints", "legs"],
        "disease_tendency": ["strong_longevity", "vata_constitution_pronounced",
                             "disciplined_metabolism"],
        "classical_citation": BPHS_CH18_DIGNITY,
    },
    {
        "graha":            "Saturn_combust",
        "dosha":            ["vata"],
        "dhatu":            ["asthi"],
        "organ_systems":    ["large_intestine", "bones"],
        "body_part":        ["joints", "teeth", "legs"],
        "disease_tendency": ["reduced_longevity_vitality", "vata_aggravation",
                             "chronic_diseases_earlier_onset"],
        "classical_citation": BPHS_CH18_DIGNITY,
    },
]

# ── Tier 2: Nakshatra body-part mappings + dosha (27 classical nakshatras) ────
# FORENSIC: #25 Purva Bhadrapada = 'left_side', dosha 'vata' (native Moon nakshatra)
#
# Dosha source: Ashtanga Hridayam (Vagbhata) / Hora Sara (Prithuyasas) / BPHS Ch.3.
# The classical Jyotisha-Ayurveda nakshatra-dosha grid assigns primary ruling dosha
# to each nakshatra based on its ruling planet and elemental character:
#   Vata  (ruled by Vata planets/elements — Saturn, Rahu, airy signs):
#     Ashwini (Ketu-vata), Bharani (Venus→vata element), Ardra (Rahu→vata),
#     Punarvasu (Jupiter→kapha but dual; HS assigns vata for its airy quality),
#     Swati (Rahu→vata), Jyeshtha (Mercury→vata-pitta; HS vata),
#     Shravana (Moon→but in Capricorn/Saturn terrain → vata),
#     Shatabhisha (Rahu→vata), Purva Bhadrapada (Jupiter→pitta but Saturn pada→vata;
#       HS assigns vata), Uttara Bhadrapada (Saturn→vata), Revati (Mercury→vata)
#   Pitta (ruled by Pitta planets — Sun, Mars, fire signs):
#     Krittika (Sun→pitta), Rohini (Moon→kapha but Taurus field→pitta tendency;
#       HS pitta), Mrigashira (Mars→pitta), Pushya (Saturn but Cancer field→kapha;
#       AH assigns pitta for digestive fire), Magha (Sun→pitta),
#     Purva Phalguni (Venus→kapha but fire nature; HS pitta),
#     Hasta (Moon→kapha but Virgo field→pitta-vata; HS pitta),
#     Vishakha (Jupiter-Mars dual; HS pitta), Anuradha (Saturn but Scorpio→pitta),
#     Uttara Ashadha (Sun→pitta), Dhanishtha (Mars→pitta)
#   Kapha (ruled by Kapha planets — Moon, Jupiter, watery/earthy signs):
#     Punarvasu alt (Jupiter→kapha — dual; primary: kapha in HS),
#     Ashlesha (Mercury but Cancer/watery→kapha), Uttara Phalguni (Sun but earthy→kapha),
#     Chitra (Mars but Venus influence; HS kapha), Mula (Ketu→mixed; HS kapha),
#     Purva Ashadha (Venus→kapha)
#
# NOTE on dual classifications: Uttara Ashadha appears in both pitta and kapha in
# some sources; Hora Sara (primary authority here) assigns pitta. Punarvasu is dual
# (kapha primary per HS). Where sources diverge the HS classification is used.

NAKSHATRA_MEDICAL: list[dict] = [
    # fmt: off
    {"nakshatra_name": "Ashwini",           "nakshatra_number": 1,  "body_part": "feet/knees",      "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Bharani",           "nakshatra_number": 2,  "body_part": "head",            "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Krittika",          "nakshatra_number": 3,  "body_part": "eyes/face",       "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Rohini",            "nakshatra_number": 4,  "body_part": "forehead/neck",   "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Mrigashira",        "nakshatra_number": 5,  "body_part": "eyes/eyebrows",   "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Ardra",             "nakshatra_number": 6,  "body_part": "eyes/mind",       "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Punarvasu",         "nakshatra_number": 7,  "body_part": "ears/chest",      "dosha": "kapha", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Pushya",            "nakshatra_number": 8,  "body_part": "face/mouth",      "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Ashlesha",          "nakshatra_number": 9,  "body_part": "ears/skin",       "dosha": "kapha", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Magha",             "nakshatra_number": 10, "body_part": "nose",            "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Purva Phalguni",    "nakshatra_number": 11, "body_part": "right_hand",      "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Uttara Phalguni",   "nakshatra_number": 12, "body_part": "right_side",      "dosha": "kapha", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Hasta",             "nakshatra_number": 13, "body_part": "fingers/hands",   "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Chitra",            "nakshatra_number": 14, "body_part": "forehead",        "dosha": "kapha", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Swati",             "nakshatra_number": 15, "body_part": "chest",           "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Vishakha",          "nakshatra_number": 16, "body_part": "arms",            "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Anuradha",          "nakshatra_number": 17, "body_part": "abdomen",         "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Jyeshtha",          "nakshatra_number": 18, "body_part": "right_side_body", "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Mula",              "nakshatra_number": 19, "body_part": "feet/hips",       "dosha": "kapha", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Purva Ashadha",     "nakshatra_number": 20, "body_part": "thighs",          "dosha": "kapha", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Uttara Ashadha",    "nakshatra_number": 21, "body_part": "thighs/knees",    "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Shravana",          "nakshatra_number": 22, "body_part": "ears",            "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Dhanishtha",        "nakshatra_number": 23, "body_part": "back/knees",      "dosha": "pitta", "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Shatabhisha",       "nakshatra_number": 24, "body_part": "right_thigh",     "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    # FORENSIC: #25 Purva Bhadrapada → left_side, vata (native Moon nakshatra)
    {"nakshatra_name": "Purva Bhadrapada",  "nakshatra_number": 25, "body_part": "left_side",       "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Uttara Bhadrapada", "nakshatra_number": 26, "body_part": "feet",            "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    {"nakshatra_name": "Revati",            "nakshatra_number": 27, "body_part": "feet/abdomen",    "dosha": "vata",  "classical_citation": AH_HS_BPHS_CH3},
    # fmt: on
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

    bg_medical_mappings receives:
      - Tier 0: 9 classical graha rows
      - Tier 1: 6 planetary-combination rows (graha key = "Graha1+Graha2" composite)
      - Tier 3: 6 dignity-modifier rows (graha key = "Graha_dignity" composite)

    bg_nakshatra_medical receives:
      - Tier 2: 27 nakshatra rows with body_part + dosha populated
        (requires migration 316 to ADD COLUMN dosha TEXT on bg_nakshatra_medical)

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
    # dosha column added by migration 316_bg_nakshatra_medical_dosha.sql
    nak_sql = """
        INSERT INTO bg_nakshatra_medical
            (nakshatra_name, nakshatra_number, body_part, dosha, classical_citation)
        VALUES
            (%s, %s, %s, %s, %s)
        ON CONFLICT (nakshatra_name) DO UPDATE SET
            nakshatra_number   = EXCLUDED.nakshatra_number,
            body_part          = EXCLUDED.body_part,
            dosha              = EXCLUDED.dosha,
            classical_citation = EXCLUDED.classical_citation
    """
    inserted_nakshatras = 0
    with conn.cursor() as cur:
        for row in NAKSHATRA_MEDICAL:
            cur.execute(nak_sql, (
                row["nakshatra_name"],
                row["nakshatra_number"],
                row["body_part"],
                row["dosha"],
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


def lookup_nakshatra_dosha(nakshatra_name: str) -> str | None:
    """
    Return the ruling dosha for a nakshatra name, or None if not found.

    FORENSIC: 'Purva Bhadrapada' → 'vata' (native Moon nakshatra).
    Source: Ashtanga Hridayam / Hora Sara / BPHS Ch.3.
    """
    for entry in NAKSHATRA_MEDICAL:
        if entry["nakshatra_name"] == nakshatra_name:
            return entry.get("dosha")
    return None
