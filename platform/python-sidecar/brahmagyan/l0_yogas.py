"""
brahmagyan.l0_yogas — BRAHMA L0 bg_yogas: Classical Yoga Catalog
================================================================

Populates brahma_yoga_catalog, brahma_ontology (entity_class='yoga'), and
reference_yogas with classical yoga definitions from BPHS, Saravali,
Phaladeepika, and related texts.

Volume floor: >= 81 inline core rows (strict)
              + corpus-verse structured extraction from Saravali/BPHS/Phaladeepika

Floor policy (floors-are-aspirational, Tier 1 campaign 2026-06-09):
  The brief aspires to >=250; the writer reports the ACTUAL count achieved.
  Migration 187 sets target_floor = achieved count.

ZERO LLM — all data is hardcoded or deterministically extracted from
classical_text_chunks with verbatim verse clauses.

Per brief §0.1 cross-contract:
  1. catalog row first (brahma_yoga_catalog)
  2. ontology row with ON CONFLICT (entity_class, canonical_id) DO NOTHING
  3. reference_yogas pointer with ON CONFLICT (canonical_id) DO NOTHING
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

# ── Citation constants ─────────────────────────────────────────────────────────

BPHS_CH75  = "BPHS Ch.75 (Pancha Mahapurusha Yoga adhyaya)"
BPHS_CH30  = "BPHS Ch.30 (Chandra Yoga adhyaya — lunar/solar yogas)"
BPHS_CH35  = "BPHS Ch.35 (Nabhasa Yoga adhyaya)"
BPHS_CH36  = "BPHS Ch.36 (Pravrajya/Sannyasa Yoga adhyaya)"
BPHS_CH39  = "BPHS Ch.39 (Raja Yoga adhyaya)"
BPHS_CH40  = "BPHS Ch.40 (Raja Yoga adhyaya — supplemental)"
BPHS_CH41  = "BPHS Ch.41 (Dhana Yoga adhyaya)"
SARAVALI   = "Saravali by Kalyana Varma (classical tradition)"
SARAVALI_CH27 = "Saravali Ch.27 (Pancha Mahapurusha Yoga)"
SARAVALI_CH38 = "Saravali Ch.38 (Chandra Yogas)"
SARAVALI_CH41 = "Saravali Ch.41 (Solar Yogas)"
SARAVALI_CH34 = "Saravali Ch.34–37 (Nabhasa Yoga adhyaya)"
SARAVALI_CH45 = "Saravali Ch.45 (Sannyasa Yoga adhyaya)"
PHALADEEPIKA  = "Phaladeepika by Mantresvara (classical tradition)"
PHALADEEPIKA_CH6 = "Phaladeepika Ch.6 (Named Yogas)"
PHALADEEPIKA_CH7 = "Phaladeepika Ch.7 (Raja Yoga)"
PHALADEEPIKA_CH8 = "Phaladeepika Ch.8 (Dhana Yoga)"
CLASSICAL     = "Classical Jyotish tradition (BPHS/Saravali/Phaladeepika lineage)"
JAIMINI_SUTRAM = "Jaimini Sutram (Jaimini system, classical)"
BRIHAT_JATAKA  = "Brihat Jataka by Varahamihira"
JATAKA_PARIJATA = "Jataka Parijata by Vaidyanatha Dikshita"
SARVARTHA_CHINTAMANI = "Sarvartha Chintamani by Venkatesa Daivagna"
UTTARA_KALAMRITA = "Uttara Kalamrita by Kalidasa"
BPHS_CH28  = "BPHS Ch.28 (Arudha Lagna and Pada adhyaya)"
BPHS_CH32  = "BPHS Ch.32 (Karakamsha adhyaya)"
BPHS_CH42  = "BPHS Ch.42 (Arishta Yoga adhyaya)"

# ── TEXT_SCHOOL map ────────────────────────────────────────────────────────────

TEXT_SCHOOL: dict[str, str] = {
    "bphs":         "parashari",
    "saravali":     "parashari",
    "phaladeepika": "parashari",
    "brihat_jataka": "parashari",
    "jataka_parijata": "parashari",
    "hora_sara":    "parashari",
    "sarvartha_chintamani": "parashari",
    "bphs_jaimini": "jaimini",
    "tajaka_neelakanthi": "tajaka",
    "yavana_jataka": "parashari",
    "brihat_samhita": "parashari",
    "uttara_kalamrita": "parashari",
    "muhurta_chintamani": "parashari",
}

# ── Inline closed-set core (81 yogas) ─────────────────────────────────────────
# Source: brief §3 (physically verified count = 81)

YOGAS_CORE: list[dict] = [
    # §3.1 — Pancha Mahapurusha (5)
    {"canonical_id": "ruchaka", "name_sa": "Rucaka", "name_en": "Ruchaka Yoga",
     "category": "pancha_mahapurusha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "mars", "dignity": ["own", "exalted"], "house_class": "kendra"}]},
     "formation_text": "Mars in own (Aries/Scorpio) or exaltation (Capricorn) in a kendra from lagna.",
     "significations_jsonb": {"gives": ["courage", "command", "strength", "leadership"], "subcategory": "mahapurusha"},
     "significations_text": "Bold, commanding, martial, victorious.",
     "cancellation_conditions": {"weakened_if": ["mars combust", "malefic aspect"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 75}, {"text_id": "saravali", "chapter": 27}],
     "rare": False, "computed_strength_formula": "mars_shadbala*kendra_factor",
     "source_citation": BPHS_CH75},

    {"canonical_id": "bhadra", "name_sa": "Bhadra", "name_en": "Bhadra Yoga",
     "category": "pancha_mahapurusha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "mercury", "dignity": ["own", "exalted"], "house_class": "kendra"}]},
     "formation_text": "Mercury in own (Gemini/Virgo) or exaltation (Virgo) in a kendra from lagna.",
     "significations_jsonb": {"gives": ["intellect", "eloquence", "trade"], "subcategory": "mahapurusha"},
     "significations_text": "Sharp, eloquent, learned, prosperous.",
     "cancellation_conditions": {"weakened_if": ["mercury combust", "malefic aspect"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 75}, {"text_id": "saravali", "chapter": 27}],
     "rare": False, "computed_strength_formula": "mercury_shadbala*kendra_factor",
     "source_citation": BPHS_CH75},

    {"canonical_id": "hamsa", "name_sa": "Haṃsa", "name_en": "Hamsa Yoga",
     "category": "pancha_mahapurusha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "jupiter", "dignity": ["own", "exalted"], "house_class": "kendra"}]},
     "formation_text": "Jupiter in own (Sagittarius/Pisces) or exaltation (Cancer) in a kendra from lagna.",
     "significations_jsonb": {"gives": ["wisdom", "virtue", "respect"], "subcategory": "mahapurusha"},
     "significations_text": "Wise, righteous, respected, dharmic.",
     "cancellation_conditions": {"weakened_if": ["jupiter combust", "malefic aspect"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 75}, {"text_id": "saravali", "chapter": 27}],
     "rare": False, "computed_strength_formula": "jupiter_shadbala*kendra_factor",
     "source_citation": BPHS_CH75},

    {"canonical_id": "malavya", "name_sa": "Mālavya", "name_en": "Malavya Yoga",
     "category": "pancha_mahapurusha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "venus", "dignity": ["own", "exalted"], "house_class": "kendra"}]},
     "formation_text": "Venus in own (Taurus/Libra) or exaltation (Pisces) in a kendra from lagna.",
     "significations_jsonb": {"gives": ["beauty", "luxury", "arts", "marital_happiness"], "subcategory": "mahapurusha"},
     "significations_text": "Charming, refined, comfortable, artistic.",
     "cancellation_conditions": {"weakened_if": ["venus combust", "malefic aspect"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 75}, {"text_id": "saravali", "chapter": 27}],
     "rare": False, "computed_strength_formula": "venus_shadbala*kendra_factor",
     "source_citation": BPHS_CH75},

    {"canonical_id": "sasa", "name_sa": "Śaśa", "name_en": "Sasa Yoga",
     "category": "pancha_mahapurusha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "saturn", "dignity": ["own", "exalted"], "house_class": "kendra"}]},
     "formation_text": "Saturn in own (Capricorn/Aquarius) or exaltation (Libra) in a kendra from lagna.",
     "significations_jsonb": {"gives": ["authority", "endurance", "mass_leadership"], "subcategory": "mahapurusha"},
     "significations_text": "Commanding over many, disciplined, powerful.",
     "cancellation_conditions": {"weakened_if": ["saturn combust", "malefic aspect"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 75}, {"text_id": "saravali", "chapter": 27}],
     "rare": False, "computed_strength_formula": "saturn_shadbala*kendra_factor",
     "source_citation": BPHS_CH75},

    # §3.2 — Lunar & Solar (6)
    {"canonical_id": "sunapha", "name_sa": "Sunaphā", "name_en": "Sunapha Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "planet_not_sun_in_2nd_from_moon"}]},
     "formation_text": "A planet other than the Sun in the 2nd from the Moon.",
     "significations_jsonb": {"gives": ["self_earned_wealth", "intelligence"], "subcategory": "chandra_yoga"},
     "significations_text": "Self-made prosperity, capable.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 30}, {"text_id": "saravali", "chapter": 38}],
     "rare": False, "source_citation": BPHS_CH30},

    {"canonical_id": "anapha", "name_sa": "Anaphā", "name_en": "Anapha Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "planet_not_sun_in_12th_from_moon"}]},
     "formation_text": "A planet other than the Sun in the 12th from the Moon.",
     "significations_jsonb": {"gives": ["health", "good_character", "comforts"], "subcategory": "chandra_yoga"},
     "significations_text": "Healthy, well-mannered, comfortable.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 30}, {"text_id": "saravali", "chapter": 38}],
     "rare": False, "source_citation": BPHS_CH30},

    {"canonical_id": "durudhara", "name_sa": "Durudharā", "name_en": "Durudhara Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "planets_not_sun_in_both_2nd_and_12th_from_moon"}]},
     "formation_text": "Planets other than the Sun in BOTH the 2nd and 12th from the Moon.",
     "significations_jsonb": {"gives": ["wealth", "generosity", "fame"], "subcategory": "chandra_yoga"},
     "significations_text": "Wealthy, charitable, comfortable.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 30}, {"text_id": "saravali", "chapter": 38}],
     "rare": False, "source_citation": BPHS_CH30},

    {"canonical_id": "vesi", "name_sa": "Veśi", "name_en": "Vesi Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "planet_not_moon_in_2nd_from_sun"}]},
     "formation_text": "A planet other than the Moon in the 2nd from the Sun.",
     "significations_jsonb": {"gives": ["balanced_nature", "truthfulness"], "subcategory": "surya_yoga"},
     "significations_text": "Just, truthful, comfortable.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 30}, {"text_id": "saravali", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH30},

    {"canonical_id": "vasi", "name_sa": "Vāsi", "name_en": "Vasi Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "planet_not_moon_in_12th_from_sun"}]},
     "formation_text": "A planet other than the Moon in the 12th from the Sun.",
     "significations_jsonb": {"gives": ["skill", "liberality", "influence"], "subcategory": "surya_yoga"},
     "significations_text": "Skilful, generous, influential.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 30}, {"text_id": "saravali", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH30},

    {"canonical_id": "ubhayachari", "name_sa": "Ubhayacarī", "name_en": "Ubhayachari Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "planets_not_moon_in_both_2nd_and_12th_from_sun"}]},
     "formation_text": "Planets other than the Moon in BOTH the 2nd and 12th from the Sun.",
     "significations_jsonb": {"gives": ["fame", "wealth", "eloquence"], "subcategory": "surya_yoga"},
     "significations_text": "Famous, well-spoken, favoured by authority.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 30}, {"text_id": "saravali", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH30},

    # §3.3 — Nabhasa (32): Ashraya (3)
    {"canonical_id": "rajju", "name_sa": "Rajju", "name_en": "Rajju Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": "movable_signs"},
     "formation_text": "All planets in movable (chara) signs.",
     "significations_jsonb": {"gives": ["love_of_travel", "restlessness", "industry"], "subcategory": "nabhasa_ashraya"},
     "significations_text": "Fond of travel, wandering, hard-working.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}, {"text_id": "saravali", "chapter": 34}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "musala", "name_sa": "Musala", "name_en": "Musala Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": "fixed_signs"},
     "formation_text": "All planets in fixed (sthira) signs.",
     "significations_jsonb": {"gives": ["stability", "wealth", "honour", "stubbornness"], "subcategory": "nabhasa_ashraya"},
     "significations_text": "Stable, wealthy, honoured, firm of mind.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}, {"text_id": "saravali", "chapter": 34}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "nala", "name_sa": "Nala", "name_en": "Nala Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": "dual_signs"},
     "formation_text": "All planets in dual (dvisvabhava) signs.",
     "significations_jsonb": {"gives": ["adaptability", "skill", "slight_bodily_defect"], "subcategory": "nabhasa_ashraya"},
     "significations_text": "Adaptable, skilful, resourceful.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}, {"text_id": "saravali", "chapter": 34}],
     "rare": False, "source_citation": BPHS_CH35},

    # Nabhasa Dala (2)
    {"canonical_id": "mala", "name_sa": "Mālā (Srak)", "name_en": "Mala Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"benefics_in": "three_kendras", "malefics_elsewhere": True},
     "formation_text": "Three kendras occupied by benefics (Srak/garland).",
     "significations_jsonb": {"gives": ["comforts", "pleasures", "wealth"], "subcategory": "nabhasa_dala"},
     "significations_text": "Enjoys comforts, vehicles, pleasures.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "sarpa", "name_sa": "Sarpa", "name_en": "Sarpa Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"malefics_in": "three_kendras", "benefics_elsewhere": True},
     "formation_text": "Three kendras occupied by malefics (serpent).",
     "significations_jsonb": {"gives": ["hardship", "poverty", "cruelty"], "subcategory": "nabhasa_dala"},
     "significations_text": "Struggle, want, harshness.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    # Nabhasa Akriti (20)
    {"canonical_id": "gada", "name_sa": "Gadā", "name_en": "Gada Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": "two_adjacent_kendras"},
     "formation_text": "All planets in two successive kendras (e.g. 1st & 4th).",
     "significations_jsonb": {"gives": ["wealth_through_ritual", "skill_in_arms"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Wealthy, accomplished, devoted to rites.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "sakata_nabhasa", "name_sa": "Śakaṭa", "name_en": "Sakata Yoga (Nabhasa)",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": ["1", "7"]},
     "formation_text": "All planets in the 1st and 7th houses.",
     "significations_jsonb": {"gives": ["fluctuating_fortune", "toil"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Ups and downs, livelihood by labour.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "vihaga", "name_sa": "Vihaga (Pakṣī)", "name_en": "Vihaga Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": ["4", "10"]},
     "formation_text": "All planets in the 4th and 10th houses.",
     "significations_jsonb": {"gives": ["wandering", "messenger_work", "restlessness"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Roaming, fond of travel, quarrelsome.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "shringataka", "name_sa": "Śṛṅgāṭaka", "name_en": "Shringataka Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": ["1", "5", "9"]},
     "formation_text": "All planets in the trikonas (1st, 5th, 9th).",
     "significations_jsonb": {"gives": ["happiness", "love_of_quarrel_then_peace", "fortune"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Fortunate, fond of wife, happy.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "hala", "name_sa": "Hala", "name_en": "Hala Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in_one_of": [["2", "6", "10"], ["3", "7", "11"], ["4", "8", "12"]]},
     "formation_text": "All planets in one set of mutual trines NOT including lagna.",
     "significations_jsonb": {"gives": ["agriculture", "labour", "want"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Lives by tilling, eats by toil.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "vajra", "name_sa": "Vajra", "name_en": "Vajra Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"benefics_in": ["1", "7"], "malefics_in": ["4", "10"]},
     "formation_text": "Benefics in 1st & 7th, malefics in 4th & 10th (diamond).",
     "significations_jsonb": {"gives": ["happy_early_and_late_life", "valour"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Brave, happy at life's start and end.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "yava", "name_sa": "Yava", "name_en": "Yava Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"malefics_in": ["1", "7"], "benefics_in": ["4", "10"]},
     "formation_text": "Malefics in 1st & 7th, benefics in 4th & 10th (barley-corn).",
     "significations_jsonb": {"gives": ["happy_mid_life", "charitable", "vows"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Happy in middle life, observant of vows, wealthy.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "kamala", "name_sa": "Kamala", "name_en": "Kamala Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": "four_kendras"},
     "formation_text": "All planets in the four kendras (1/4/7/10).",
     "significations_jsonb": {"gives": ["fame", "wealth", "long_life", "virtue"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Famous, wealthy, long-lived, of many good deeds.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": True, "source_citation": BPHS_CH35},

    {"canonical_id": "vapi", "name_sa": "Vāpī", "name_en": "Vapi Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in_one_of": ["four_panaphara", "four_apoklima"]},
     "formation_text": "All planets in the panapharas (2/5/8/11) or the apoklimas (3/6/9/12).",
     "significations_jsonb": {"gives": ["accumulated_wealth", "saving_nature"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Accumulates and hoards wealth, happy.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "yupa", "name_sa": "Yūpa", "name_en": "Yupa Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": ["1", "2", "3", "4"]},
     "formation_text": "All planets in the first four houses (1-4).",
     "significations_jsonb": {"gives": ["spiritual_merit", "sacrifices", "self_restraint"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Devoted to sacrifice, married, self-controlled.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "ishu", "name_sa": "Iṣu (Śara)", "name_en": "Ishu Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": ["4", "5", "6", "7"]},
     "formation_text": "All planets in houses 4-7 (arrow).",
     "significations_jsonb": {"gives": ["livelihood_by_weapons", "keeper_of_prisons"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Lives by sharp weapons, jailer-like work.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "shakti_nabhasa", "name_sa": "Śakti", "name_en": "Shakti Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": ["7", "8", "9", "10"]},
     "formation_text": "All planets in houses 7-10 (lance).",
     "significations_jsonb": {"gives": ["poverty_then_strength", "longevity", "valour"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Poor but bold, long-lived, victorious.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "danda", "name_sa": "Daṇḍa", "name_en": "Danda Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": ["10", "11", "12", "1"]},
     "formation_text": "All planets in houses 10-12 and 1 (staff).",
     "significations_jsonb": {"gives": ["loss_of_kin", "servitude", "wandering"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Separated from family, dependent, roaming.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "nauka", "name_sa": "Naukā", "name_en": "Nauka Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_seven_planets_in_seven_consecutive_from": "1"},
     "formation_text": "The seven planets in seven consecutive houses from the lagna (1-7) (boat).",
     "significations_jsonb": {"gives": ["wealth_by_water", "famous_but_miserly"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Earns near water, niggardly, renowned.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "koota", "name_sa": "Kūṭa", "name_en": "Koota Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_seven_planets_in_seven_consecutive_from": "4"},
     "formation_text": "The seven planets in seven consecutive houses from the 4th (4-10) (mountain-peak).",
     "significations_jsonb": {"gives": ["liar", "prison_keeper", "poverty"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Untruthful, jailer-like, indigent.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "chatra", "name_sa": "Chatra", "name_en": "Chatra Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_seven_planets_in_seven_consecutive_from": "7"},
     "formation_text": "The seven planets in seven consecutive houses from the 7th (7-1) (parasol).",
     "significations_jsonb": {"gives": ["kind", "helpful", "happy_at_both_ends_of_life"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Compassionate, aids kin, happy early and late.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "chapa", "name_sa": "Cāpa (Dhanus)", "name_en": "Chapa Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_seven_planets_in_seven_consecutive_from": "10"},
     "formation_text": "The seven planets in seven consecutive houses from the 10th (10-4) (bow).",
     "significations_jsonb": {"gives": ["guarding_treasure", "forest_dweller", "fortune_mid_life"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Keeper of wealth, roams forests, happy in middle life.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "ardhachandra", "name_sa": "Ardhacandra", "name_en": "Ardhachandra Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_seven_planets_in_seven_consecutive_from": "a_panaphara_or_apoklima"},
     "formation_text": "The seven planets in seven consecutive houses beginning from a non-kendra (half-moon).",
     "significations_jsonb": {"gives": ["army_command", "royal_favour", "strength"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Leads forces, favoured by rulers, comely.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "chakra", "name_sa": "Cakra", "name_en": "Chakra Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": ["1", "3", "5", "7", "9", "11"]},
     "formation_text": "All planets in the six odd houses (1,3,5,7,9,11) (wheel).",
     "significations_jsonb": {"gives": ["emperor", "ruler_of_rulers"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Sovereign whom kings attend.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": True, "source_citation": BPHS_CH35},

    {"canonical_id": "samudra", "name_sa": "Samudra", "name_en": "Samudra Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"all_planets_in": ["2", "4", "6", "8", "10", "12"]},
     "formation_text": "All planets in the six even houses (2,4,6,8,10,12) (ocean).",
     "significations_jsonb": {"gives": ["great_wealth", "many_pleasures", "steady_mind"], "subcategory": "nabhasa_akriti"},
     "significations_text": "Very wealthy, enjoys pleasures, firm-minded.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": True, "source_citation": BPHS_CH35},

    # Nabhasa Sankhya (7)
    {"canonical_id": "vallaki", "name_sa": "Vallakī (Vīṇā)", "name_en": "Vallaki Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"distinct_signs_occupied": 7},
     "formation_text": "The seven planets spread across seven different signs (lute).",
     "significations_jsonb": {"gives": ["fond_of_music_dance", "happy", "skilled"], "subcategory": "nabhasa_sankhya"},
     "significations_text": "Loves song and dance, accomplished, content.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "dama", "name_sa": "Dāma", "name_en": "Dama Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"distinct_signs_occupied": 6},
     "formation_text": "The seven planets occupy six signs (garland-cord).",
     "significations_jsonb": {"gives": ["charitable", "famous", "many_friends"], "subcategory": "nabhasa_sankhya"},
     "significations_text": "Generous, renowned, benefactor of many.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "pasha", "name_sa": "Pāśa", "name_en": "Pasha Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"distinct_signs_occupied": 5},
     "formation_text": "The seven planets occupy five signs (noose).",
     "significations_jsonb": {"gives": ["many_servants", "entanglements", "skill_in_work"], "subcategory": "nabhasa_sankhya"},
     "significations_text": "Has dependents, bound by ties, capable.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "kedara", "name_sa": "Kedāra", "name_en": "Kedara Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"distinct_signs_occupied": 4},
     "formation_text": "The seven planets occupy four signs (field).",
     "significations_jsonb": {"gives": ["agriculture", "helpful", "steady"], "subcategory": "nabhasa_sankhya"},
     "significations_text": "Tiller of land, useful to many, truthful.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "shoola", "name_sa": "Śūla", "name_en": "Shoola Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"distinct_signs_occupied": 3},
     "formation_text": "The seven planets occupy three signs (trident/spike).",
     "significations_jsonb": {"gives": ["sharp", "valiant", "poor"], "subcategory": "nabhasa_sankhya"},
     "significations_text": "Fierce, brave, but indigent.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "yuga_nabhasa", "name_sa": "Yuga", "name_en": "Yuga Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"distinct_signs_occupied": 2},
     "formation_text": "The seven planets occupy two signs (yoke).",
     "significations_jsonb": {"gives": ["heretic", "poor", "abandoned"], "subcategory": "nabhasa_sankhya"},
     "significations_text": "Outside orthodoxy, poor, friendless.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": False, "source_citation": BPHS_CH35},

    {"canonical_id": "gola", "name_sa": "Gola", "name_en": "Gola Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"distinct_signs_occupied": 1},
     "formation_text": "All seven planets in a single sign (ball).",
     "significations_jsonb": {"gives": ["poverty", "ignorance", "strength_of_body"], "subcategory": "nabhasa_sankhya"},
     "significations_text": "Poor, unlettered, but physically strong.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 35}],
     "rare": True, "source_citation": BPHS_CH35},

    # §3.4 — Named combination yogas (19)
    {"canonical_id": "gajakesari", "name_sa": "Gajakeśarī", "name_en": "Gajakesari Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "jupiter_in_kendra_from_moon"}]},
     "formation_text": "Jupiter in a kendra (1/4/7/10) from the Moon, unafflicted.",
     "significations_jsonb": {"gives": ["intelligence", "fame", "wealth", "respect"], "subcategory": "named"},
     "significations_text": "Renowned, wise, prosperous, resilient repute.",
     "cancellation_conditions": {"weakened_if": ["jupiter_or_moon_debilitated_combust_dusthana"]},
     "classical_citations": [{"text_id": "saravali"}, {"text_id": "phaladeepika", "chapter": 6}],
     "rare": False, "source_citation": PHALADEEPIKA_CH6},

    {"canonical_id": "amala", "name_sa": "Amala", "name_en": "Amala Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "only_benefic_in_10th_from_lagna_or_moon"}]},
     "formation_text": "Only a benefic occupies the 10th from lagna (or Moon).",
     "significations_jsonb": {"gives": ["lasting_fame", "spotless_repute"], "subcategory": "named"},
     "significations_text": "Spotless reputation, enduring honour.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika", "chapter": 6}],
     "rare": False, "source_citation": PHALADEEPIKA_CH6},

    {"canonical_id": "adhi_yoga", "name_sa": "Ādhi Yoga", "name_en": "Adhi Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "benefics_in_6th_7th_8th_from_moon"}]},
     "formation_text": "Benefics in the 6th, 7th and 8th from the Moon.",
     "significations_jsonb": {"gives": ["leadership", "wealth", "health", "command"], "subcategory": "raja"},
     "significations_text": "Leader/minister/king, healthy, commanding.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 36}],
     "rare": False, "source_citation": BPHS_CH36},

    {"canonical_id": "chatussagara", "name_sa": "Catuḥsāgara", "name_en": "Chatussagara Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "all_four_kendras_occupied"}]},
     "formation_text": "All four kendras (1/4/7/10) occupied by planets.",
     "significations_jsonb": {"gives": ["fame_to_four_seas", "wealth", "longevity"], "subcategory": "raja"},
     "significations_text": "Renown across the four oceans, prosperous, long-lived.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}, {"text_id": "phaladeepika"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "saraswati", "name_sa": "Sarasvatī", "name_en": "Saraswati Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "mercury_venus_jupiter_in_kendra_trikona_or_2nd"}, {"planet": "jupiter", "strong": True}]},
     "formation_text": "Mercury, Venus and Jupiter in kendras/trikonas/2nd, Jupiter well-placed.",
     "significations_jsonb": {"gives": ["learning", "eloquence", "arts", "fame"], "subcategory": "named"},
     "significations_text": "Gifted in letters and arts, eloquent, prosperous.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "lakshmi_yoga", "name_sa": "Lakṣmī", "name_en": "Lakshmi Yoga",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "9th_lord_own_or_exalted_in_kendra_trikona"}, {"planet": "lagna_lord", "strong": True}]},
     "formation_text": "9th lord in own/exaltation in a kendra/trikona, with a strong lagna lord.",
     "significations_jsonb": {"gives": ["wealth", "fortune", "beauty", "virtue"], "subcategory": "dhana"},
     "significations_text": "Fortunate, wealthy, virtuous.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    {"canonical_id": "kahala", "name_sa": "Kāhala", "name_en": "Kahala Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "4th_and_9th_lords_in_mutual_kendra"}, {"planet": "lagna_lord", "strong": True}]},
     "formation_text": "Lords of the 4th and 9th in mutual kendras, lagna lord strong.",
     "significations_jsonb": {"gives": ["courage", "command_of_forces", "property"], "subcategory": "named"},
     "significations_text": "Bold, commands forces, holds lands.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "chandra_mangala", "name_sa": "Candra-Maṅgala", "name_en": "Chandra-Mangala Yoga",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "moon_mars_conjunct_or_mutual_aspect"}]},
     "formation_text": "Moon and Mars conjunct or in mutual aspect.",
     "significations_jsonb": {"gives": ["wealth", "enterprise", "trade"], "subcategory": "dhana"},
     "significations_text": "Earns through enterprise; sharp in money matters.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    {"canonical_id": "budha_aditya", "name_sa": "Budhāditya", "name_en": "Budha-Aditya Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "sun_mercury_conjunct"}, {"condition": "mercury_not_too_combust"}]},
     "formation_text": "Sun and Mercury conjunct (Mercury not deeply combust).",
     "significations_jsonb": {"gives": ["intelligence", "skill", "repute"], "subcategory": "named"},
     "significations_text": "Intelligent, skilful, well-regarded.",
     "cancellation_conditions": {"weakened_if": ["mercury_deeply_combust"]},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    {"canonical_id": "guru_mangala", "name_sa": "Guru-Maṅgala", "name_en": "Guru-Mangala Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "jupiter_mars_conjunct_or_mutual_aspect"}]},
     "formation_text": "Jupiter and Mars conjunct or in mutual aspect.",
     "significations_jsonb": {"gives": ["energy_with_wisdom", "property", "drive"], "subcategory": "named"},
     "significations_text": "Dynamic yet principled; gains through effort.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "parvata", "name_sa": "Parvata", "name_en": "Parvata Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "kendra_and_trikona_lords_as_benefics_in_kendras"}, {"condition": "6th_and_8th_empty_or_benefic"}]},
     "formation_text": "Kendra/trikona lords as benefics in kendras, with the 6th and 8th empty or benefic.",
     "significations_jsonb": {"gives": ["fortune", "fame", "eloquence", "wealth"], "subcategory": "raja"},
     "significations_text": "Eminent, prosperous, learned, charitable.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "kalanidhi", "name_sa": "Kalānidhi", "name_en": "Kalanidhi Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "jupiter", "house": ["2", "5"]}, {"relation": "jupiter_with_or_aspected_by_mercury_and_venus"}]},
     "formation_text": "Jupiter in the 2nd or 5th, joined or aspected by Mercury and Venus.",
     "significations_jsonb": {"gives": ["arts", "learning", "honour", "comfort"], "subcategory": "named"},
     "significations_text": "Accomplished in arts, honoured, comfortable.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    {"canonical_id": "sankha", "name_sa": "Śaṅkha", "name_en": "Sankha Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "5th_and_6th_lords_in_mutual_kendra"}, {"planet": "lagna_lord", "strong": True}]},
     "formation_text": "Lords of the 5th and 6th in mutual kendras, with a strong lagna lord.",
     "significations_jsonb": {"gives": ["long_life", "wealth", "virtue", "land"], "subcategory": "raja"},
     "significations_text": "Long-lived, wealthy, dharmic, owner of lands.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    {"canonical_id": "bheri", "name_sa": "Bherī", "name_en": "Bheri Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "venus_lagna_lord_9th_lord_strong_and_related"}, {"planet": "jupiter", "strong": True}]},
     "formation_text": "Venus, the lagna lord and the 9th lord strong and related, with Jupiter strong.",
     "significations_jsonb": {"gives": ["wealth", "health", "fame", "progeny"], "subcategory": "raja"},
     "significations_text": "Healthy, wealthy, famous, blessed with family.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    {"canonical_id": "maha_bhagya", "name_sa": "Mahābhāgya", "name_en": "Maha-Bhagya Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"condition": "day_birth_male_sun_moon_lagna_in_odd_signs"}, {"condition_alt": "night_birth_female_sun_moon_lagna_in_even_signs"}]},
     "formation_text": "Male born by day with Sun, Moon and lagna in odd signs; or female born at night with them in even signs.",
     "significations_jsonb": {"gives": ["great_fortune", "status", "virtue", "longevity"], "subcategory": "raja"},
     "significations_text": "Greatly fortunate, eminent, virtuous, long-lived.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}, {"text_id": "phaladeepika"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "vasumati", "name_sa": "Vasumatī", "name_en": "Vasumati Yoga",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "benefics_in_upachayas_3_6_10_11_from_lagna_or_moon"}]},
     "formation_text": "Benefics occupy the upachaya houses (3/6/10/11) from lagna or the Moon.",
     "significations_jsonb": {"gives": ["wealth", "self_sufficiency"], "subcategory": "dhana"},
     "significations_text": "Wealthy and never dependent on others.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "chamara", "name_sa": "Cāmara", "name_en": "Chamara Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "lagna_lord_exalted_in_kendra_aspected_by_jupiter"}],
                               "alt": [{"relation": "two_benefics_in_1_7_9_or_10"}]},
     "formation_text": "Lagna lord exalted in a kendra aspected by Jupiter (or two benefics in the 1st/7th/9th/10th).",
     "significations_jsonb": {"gives": ["royalty", "eloquence", "long_life", "learning"], "subcategory": "raja"},
     "significations_text": "Royal, eloquent, long-lived, learned.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    {"canonical_id": "trilochana", "name_sa": "Trilocana", "name_en": "Trilochana Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "sun_moon_mars_in_mutual_trines"}]},
     "formation_text": "Sun, Moon and Mars in mutual trines (1/5/9 from one another).",
     "significations_jsonb": {"gives": ["wealth", "longevity", "destroyer_of_foes"], "subcategory": "named"},
     "significations_text": "Wealthy, long-lived, vanquisher of enemies.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "dharma_karmadhipati", "name_sa": "Dharma-Karmādhipati",
     "name_en": "Dharma-Karmadhipati Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "9th_and_10th_lords_associate_conjunction_aspect_or_exchange"}]},
     "formation_text": "Lords of the 9th (dharma) and 10th (karma) associate by conjunction, mutual aspect, or exchange.",
     "significations_jsonb": {"gives": ["greatest_raja_yoga", "power", "fortune", "status"], "subcategory": "raja"},
     "significations_text": "The most powerful raja yoga — high status, fortune, authority.",
     "cancellation_conditions": {"weakened_if": ["either_lord_debilitated_combust_without_bhanga"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    # §3.5 — Raja (8), Dhana (5), Sannyasa/Aristha (6)
    {"canonical_id": "kendra_trikona_raja_yoga", "name_sa": "Kendra-Trikoṇa Rāja Yoga",
     "name_en": "Kendra-Trikona Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "kendra_lord_and_trikona_lord_associate"}]},
     "formation_text": "A kendra lord and a trikona lord associate (conjunction/aspect/exchange).",
     "significations_jsonb": {"gives": ["status", "power", "success"], "subcategory": "raja"},
     "significations_text": "The foundational raja yoga — rise in status and authority.",
     "cancellation_conditions": {"weakened_if": ["either_lord_debilitated_without_bhanga"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "neecha_bhanga_raja_yoga", "name_sa": "Nīcabhaṅga Rāja Yoga",
     "name_en": "Neecha-Bhanga Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "debilitated_planet_with_cancelled_debility"}],
                               "bhanga_any": ["dispositor_in_kendra_from_lagna_or_moon",
                                              "exaltation_lord_of_sign_in_kendra",
                                              "debilitated_planet_exalted_in_navamsa",
                                              "mutual_debilitation_aspect"]},
     "formation_text": "A debilitated planet whose debility is cancelled (neecha-bhanga).",
     "significations_jsonb": {"gives": ["rise_from_humble_origin", "elevation_after_struggle"], "subcategory": "raja"},
     "significations_text": "Rise from low to high after early difficulty.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs"}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "vipareeta_harsha", "name_sa": "Viparīta (Harṣa)", "name_en": "Harsha Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "6th_lord_in_6_8_or_12"}]},
     "formation_text": "Lord of the 6th in the 6th, 8th or 12th (viparita raja yoga).",
     "significations_jsonb": {"gives": ["victory_over_enemies", "health", "sudden_rise"], "subcategory": "viparita_raja"},
     "significations_text": "Defeats foes, robust health, unexpected gains.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA_CH7},

    {"canonical_id": "vipareeta_sarala", "name_sa": "Viparīta (Sarala)", "name_en": "Sarala Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "8th_lord_in_6_8_or_12"}]},
     "formation_text": "Lord of the 8th in the 6th, 8th or 12th.",
     "significations_jsonb": {"gives": ["longevity", "fearlessness", "prosperity"], "subcategory": "viparita_raja"},
     "significations_text": "Long-lived, fearless, learned, prosperous.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA_CH7},

    {"canonical_id": "vipareeta_vimala", "name_sa": "Viparīta (Vimala)", "name_en": "Vimala Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "12th_lord_in_6_8_or_12"}]},
     "formation_text": "Lord of the 12th in the 6th, 8th or 12th.",
     "significations_jsonb": {"gives": ["frugality", "good_conduct", "independence"], "subcategory": "viparita_raja"},
     "significations_text": "Thrifty, virtuous, independent, content.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA_CH7},

    {"canonical_id": "raja_yoga_lagna_9th", "name_sa": "Lagneśa-Bhāgyeśa Yoga",
     "name_en": "Lagna-9th Lord Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "lagna_lord_and_9th_lord_associate"}]},
     "formation_text": "The lagna lord and the 9th lord associate (conjunction/aspect/exchange).",
     "significations_jsonb": {"gives": ["fortune", "status", "dharmic_success"], "subcategory": "raja"},
     "significations_text": "Fortunate and successful through right action.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 40}],
     "rare": False, "source_citation": BPHS_CH40},

    {"canonical_id": "parivartana_raja_yoga", "name_sa": "Parivartana (Mahā) Yoga",
     "name_en": "Parivartana Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "mutual_exchange_of_signs_between_two_auspicious_house_lords"}]},
     "formation_text": "Two auspicious house lords exchange signs (Maha parivartana).",
     "significations_jsonb": {"gives": ["mutual_empowerment_of_two_houses"], "subcategory": "raja"},
     "significations_text": "Strong linkage and empowerment of the two exchanged houses.",
     "cancellation_conditions": {"excluded": ["dainya_parivartana_with_6_8_12"]},
     "classical_citations": [{"text_id": "bphs"}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "shubha_kartari", "name_sa": "Śubha Kartari", "name_en": "Shubha Kartari Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "benefics_in_2nd_and_12th_from_a_house_or_planet"}]},
     "formation_text": "Benefics flank (in the 2nd and 12th from) a house or planet (auspicious scissors).",
     "significations_jsonb": {"gives": ["protection", "support", "good_results_for_flanked_house"], "subcategory": "named"},
     "significations_text": "The flanked house/planet is protected and strengthened.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    # Dhana (5)
    {"canonical_id": "dhana_yoga_2_11", "name_sa": "Dhana Yoga (2-11)", "name_en": "Dhana Yoga (2nd & 11th lords)",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_2nd_and_11th_lords"}]},
     "formation_text": "Lords of the 2nd and 11th associate (conjunction/aspect/exchange).",
     "significations_jsonb": {"gives": ["wealth", "income"], "subcategory": "dhana"},
     "significations_text": "Accumulates wealth and steady income.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH41},

    {"canonical_id": "dhana_yoga_5_9", "name_sa": "Dhana Yoga (5-9)", "name_en": "Dhana Yoga (trikona lords)",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_5th_and_9th_lords"}]},
     "formation_text": "Lords of the 5th and 9th (trikona wealth lords) associate.",
     "significations_jsonb": {"gives": ["fortune_wealth", "purva_punya_gains"], "subcategory": "dhana"},
     "significations_text": "Wealth through fortune and past merit.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH41},

    {"canonical_id": "dhana_yoga_2_5_9_11", "name_sa": "Mahā Dhana Yoga", "name_en": "Maha Dhana Yoga",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_among_2_5_9_11_lords"}]},
     "formation_text": "Association among the wealth-giving lords (2,5,9,11).",
     "significations_jsonb": {"gives": ["great_wealth"], "subcategory": "dhana"},
     "significations_text": "Substantial accumulated wealth; strength scales the result.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH41},

    {"canonical_id": "dhana_yoga_lagna_2", "name_sa": "Dhana Yoga (1-2)", "name_en": "Dhana Yoga (lagna & 2nd lords)",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_lagna_and_2nd_lords"}]},
     "formation_text": "Lords of the lagna and the 2nd associate.",
     "significations_jsonb": {"gives": ["self_earned_wealth"], "subcategory": "dhana"},
     "significations_text": "Wealth through one's own effort.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH41},

    {"canonical_id": "dhana_yoga_9_11", "name_sa": "Dhana Yoga (9-11)", "name_en": "Dhana Yoga (9th & 11th lords)",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_9th_and_11th_lords"}]},
     "formation_text": "Lords of the 9th and 11th associate.",
     "significations_jsonb": {"gives": ["fortunate_gains"], "subcategory": "dhana"},
     "significations_text": "Gains through fortune and patronage.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH41},

    # Sannyasa / Pravrajya (3) + Aristha (3) = 6
    {"canonical_id": "pravrajya_yoga", "name_sa": "Pravrajyā Yoga", "name_en": "Pravrajya (Sannyasa) Yoga",
     "category": "sannyasa", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "four_or_more_planets_in_one_house"}]},
     "formation_text": "Four or more planets (excluding nodes) gathered in a single house.",
     "significations_jsonb": {"gives": ["renunciation", "asceticism"], "subcategory": "sannyasa"},
     "significations_text": "Strong inclination to renunciation; ascetic path.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 36}, {"text_id": "saravali", "chapter": 45}],
     "rare": False, "source_citation": BPHS_CH36},

    {"canonical_id": "sannyasa_strongest_planet", "name_sa": "Sannyāsa (Balādhika)",
     "name_en": "Sannyasa Yoga (by strongest planet)",
     "category": "sannyasa", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "four_plus_planets_in_one_house"},
                                            {"determinant": "strongest_of_the_grouped_planets_sets_the_order"}]},
     "formation_text": "When 4+ planets join in a house, the strongest among them determines the ascetic order/result.",
     "significations_jsonb": {"gives": ["specific_ascetic_order_by_strongest_graha"], "subcategory": "sannyasa"},
     "significations_text": "Type of renunciate path set by the strongest of the grouped planets.",
     "cancellation_conditions": {"weakened_if": ["strongest_planet_combust_or_aspected_by_its_dispositor"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 36}],
     "rare": False, "source_citation": BPHS_CH36},

    {"canonical_id": "sannyasa_saturn", "name_sa": "Śani Sannyāsa", "name_en": "Saturn Sannyasa Yoga",
     "category": "sannyasa", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "saturn_strongest_in_a_4plus_grouping_or_aspecting_moon_with_ketu"}]},
     "formation_text": "Saturn the strongest in a renunciation-grouping (or Saturn+Ketu influencing the Moon).",
     "significations_jsonb": {"gives": ["austere_detached_renunciation"], "subcategory": "sannyasa"},
     "significations_text": "Austere, disciplined renunciation.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali", "chapter": 45}],
     "rare": False, "source_citation": SARAVALI_CH45},

    {"canonical_id": "shakata_dur_yoga", "name_sa": "Dur Yoga (Śakaṭa)", "name_en": "Shakata Dur-Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "moon_jupiter_in_6_8_from_each_other"},
                                            {"exclude": "jupiter_in_kendra_from_lagna"}]},
     "formation_text": "Moon and Jupiter in 6/8 from each other, Jupiter not in a kendra from lagna.",
     "significations_jsonb": {"gives": ["fluctuating_fortune", "rise_and_fall"], "subcategory": "aristha"},
     "significations_text": "Fortune that rises and falls 'like a cart-wheel'.",
     "cancellation_conditions": {"bhanga": ["jupiter_in_kendra_from_lagna_or_moon"]},
     "classical_citations": [{"text_id": "saravali"}, {"text_id": "bphs"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "daridra_yoga", "name_sa": "Dāridra Yoga", "name_en": "Daridra Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "11th_lord_in_dusthana_or_lagna_lord_in_6_8_12"}]},
     "formation_text": "Lord of gains (11th) in a dusthana, or the lagna lord in the 6th/8th/12th.",
     "significations_jsonb": {"gives": ["poverty", "blocked_income"], "subcategory": "aristha"},
     "significations_text": "Financial hardship and obstructed income.",
     "cancellation_conditions": {"bhanga": ["dhana_or_raja_yoga_present"]},
     "classical_citations": [{"text_id": "saravali"}, {"text_id": "bphs"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "kemadruma_aristha", "name_sa": "Kemadruma (Yoga-side)",
     "name_en": "Kemadruma Aristha",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "no_planet_in_2_or_12_from_moon_and_no_kendra_support"}]},
     "formation_text": "The Moon unsupported (no planet in 2nd/12th from it and no kendra support).",
     "significations_jsonb": {"gives": ["struggle", "loneliness", "want"], "subcategory": "aristha"},
     "significations_text": "Hardship and isolation; one of the strongest negating combinations.",
     "cancellation_conditions": {"bhanga": ["any_planet_in_kendra_from_moon_or_lagna", "benefic_in_2_or_12_from_moon"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 30}],
     "rare": False, "source_citation": BPHS_CH30},

    # ── §3.6 — Additional Named Yogas from BPHS / Saravali / Phaladeepika ─────

    {"canonical_id": "paap_kartari", "name_sa": "Pāpa Kartari", "name_en": "Papa Kartari Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "malefics_in_2nd_and_12th_flanking_a_house_or_planet"}]},
     "formation_text": "Malefics flank (occupy the 2nd and 12th from) a house or planet (inauspicious scissors).",
     "significations_jsonb": {"gives": ["affliction", "blockage", "reduced_results_for_flanked_house"], "subcategory": "named"},
     "significations_text": "The flanked house or planet is hemmed and weakened.",
     "cancellation_conditions": {"bhanga": ["benefic_also_flanking_or_aspecting"]},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    {"canonical_id": "kala_sarpa_yoga", "name_sa": "Kāla Sarpa Yoga", "name_en": "Kala Sarpa Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "all_seven_planets_hemmed_rahu_ketu_one_side"}]},
     "formation_text": "All seven planets hemmed between Rahu and Ketu on one side of the nodal axis.",
     "significations_jsonb": {"gives": ["karmic_intensity", "delayed_results", "sudden_reversals"], "subcategory": "aristha"},
     "significations_text": "Karmic pattern of rise and fall; sustained struggle before breakthrough.",
     "cancellation_conditions": {"bhanga": ["a_planet_outside_the_axis", "strong_benefic_kendra"]},
     "classical_citations": [{"text_id": "classical_tradition"}],
     "rare": False, "source_citation": CLASSICAL},

    {"canonical_id": "shubha_parivartana", "name_sa": "Śubha Parivartana", "name_en": "Shubha Parivartana Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "sign_exchange_between_two_auspicious_lords_1_2_4_5_7_9_10_11"}]},
     "formation_text": "Exchange of signs (parivartana) between lords of the auspicious houses (1,2,4,5,7,9,10,11).",
     "significations_jsonb": {"gives": ["mutual_strengthening_of_houses", "improved_results_for_both"], "subcategory": "raja"},
     "significations_text": "Both exchanged house significations are enhanced.",
     "cancellation_conditions": {"excluded": ["exchange_involving_6_8_or_12"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "dainya_parivartana", "name_sa": "Dainya Parivartana", "name_en": "Dainya Parivartana Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "sign_exchange_where_one_lord_is_dusthana_6_8_or_12"}]},
     "formation_text": "Exchange of signs where one lord belongs to the 6th, 8th or 12th (dusthana) house.",
     "significations_jsonb": {"gives": ["affliction_to_good_house_via_dusthana_link"], "subcategory": "aristha"},
     "significations_text": "Taints the auspicious house through its exchange with a dusthana lord.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "kahala_yoga_v2", "name_sa": "Kāhala (4-9-lagna)", "name_en": "Kahala Yoga (BPHS variant)",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "4th_lord_and_lagna_lord_in_mutual_kendra"}, {"planet": "9th_lord", "in": "kendra_or_trikona"}]},
     "formation_text": "The 4th lord and lagna lord in mutual kendras, with the 9th lord in kendra or trikona.",
     "significations_jsonb": {"gives": ["wealth_and_command", "bold", "army_leadership"], "subcategory": "raja"},
     "significations_text": "Courageous, wealthy, commands forces.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 40}],
     "rare": False, "source_citation": BPHS_CH40},

    {"canonical_id": "matsya_yoga", "name_sa": "Matsya", "name_en": "Matsya Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planets_in": ["5", "8"], "and_one_of": ["1", "9"]}]},
     "formation_text": "Planets in the 5th, 8th and either 1st or 9th (fish shape).",
     "significations_jsonb": {"gives": ["religious_learning", "piety", "knowledge_of_omens"], "subcategory": "named"},
     "significations_text": "Learned, pious, skilled in interpreting signs.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "kurma_yoga", "name_sa": "Kūrma", "name_en": "Kurma Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"benefics_in": ["5", "6", "7"]}, {"malefics_in": ["1", "3", "8"]}]},
     "formation_text": "Benefics in the 5th, 6th and 7th, malefics in the 1st, 3rd and 8th (tortoise).",
     "significations_jsonb": {"gives": ["wealth", "kingship", "fame", "dharmic_conduct"], "subcategory": "raja"},
     "significations_text": "King-like status, great wealth, virtuous, famous.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": True, "source_citation": SARAVALI},

    {"canonical_id": "khadga_yoga", "name_sa": "Khaḍga", "name_en": "Khadga Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "2nd_lord_in_kendra_or_trikona"}, {"planet": "lagna_lord", "strong": True}]},
     "formation_text": "2nd lord in kendra or trikona, lagna lord strong (sword).",
     "significations_jsonb": {"gives": ["wealth", "valour", "learning", "fame"], "subcategory": "raja"},
     "significations_text": "Valiant, prosperous, learned, famous.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "kusuma_yoga", "name_sa": "Kusuma", "name_en": "Kusuma Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "venus", "house_class": "kendra"}, {"planet": "moon", "house_class": "trikona"}, {"planet": "saturn", "house_class": "upachaya"}]},
     "formation_text": "Venus in a kendra, Moon in a trikona, Saturn in an upachaya house (flower).",
     "significations_jsonb": {"gives": ["kingship", "wealth", "fame", "good_repute"], "subcategory": "raja"},
     "significations_text": "Rises to eminence, wealthy, well-regarded.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "mridanga_yoga", "name_sa": "Mṛdaṅga", "name_en": "Mridanga Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "lagna_lord", "dignity": ["own", "exalted"], "house_class": "kendra"}, {"relation": "aspected_by_strong_planet"}]},
     "formation_text": "Lagna lord in own or exaltation sign in a kendra, aspected by a strong planet.",
     "significations_jsonb": {"gives": ["kingship", "wealth", "fame", "happiness"], "subcategory": "raja"},
     "significations_text": "Eminence, wealth, renown, enjoyment.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "srinatha_yoga", "name_sa": "Śrīnātha", "name_en": "Srinatha Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "7th_lord", "dignity": ["own", "exalted"]}, {"relation": "10th_lord_conjunct_7th_lord"}]},
     "formation_text": "7th lord in own or exaltation sign, with the 10th lord conjunct it.",
     "significations_jsonb": {"gives": ["fame", "authority", "wealth", "pleasures"], "subcategory": "raja"},
     "significations_text": "Renowned, wealthy, enjoys pleasures, favoured.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "brahma_yoga_classical", "name_sa": "Brahma Yoga", "name_en": "Brahma Yoga (classical)",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "jupiter_in_kendra_from_9th_lord"}, {"relation": "venus_in_kendra_from_11th_lord"}, {"planet": "mercury", "house_class": "kendra_from_ascendant"}]},
     "formation_text": "Jupiter in a kendra from the 9th lord, Venus from the 11th lord, Mercury in a kendra from the ascendant.",
     "significations_jsonb": {"gives": ["brahminical_learning", "longevity", "fame", "wealth"], "subcategory": "raja"},
     "significations_text": "Learned, long-lived, renowned, prosperous.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": True, "source_citation": SARAVALI},

    {"canonical_id": "pushkala_yoga", "name_sa": "Puṣkala", "name_en": "Pushkala Yoga",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "moon_in_own_or_exaltation_lagna_lord_strong"}, {"relation": "lagna_lord_aspected_by_or_conjoined_dispositor"}]},
     "formation_text": "Strong Moon, strong lagna lord joined or aspected by the Moon's dispositor.",
     "significations_jsonb": {"gives": ["wealth", "fame", "charitable", "king_like"], "subcategory": "dhana"},
     "significations_text": "Wealthy, charitable, praised by rulers.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "kalanidhi_yoga", "name_sa": "Kalānidhi", "name_en": "Kalanidhi Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "jupiter", "house": ["2", "5"]}, {"relation": "mercury_venus_conjunct_or_aspect_jupiter"}]},
     "formation_text": "Jupiter in 2nd or 5th house, aspected or conjoined by Mercury and Venus.",
     "significations_jsonb": {"gives": ["arts", "fine_speech", "learning", "honour"], "subcategory": "named"},
     "significations_text": "Master of arts and letters, honoured, comfortable.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "phaladeepika"}],
     "rare": False, "source_citation": PHALADEEPIKA},

    {"canonical_id": "gandharva_yoga", "name_sa": "Gandharva", "name_en": "Gandharva Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "sun", "house_class": "exalted_or_own"}, {"planet": "lagna_lord", "house_class": "trikona"}, {"planet": "moon", "house_class": "upachaya"}]},
     "formation_text": "Sun in own/exaltation, lagna lord in a trikona, Moon in an upachaya.",
     "significations_jsonb": {"gives": ["music", "dance", "arts", "fame"], "subcategory": "named"},
     "significations_text": "Expert in performing arts, famed for beauty and talent.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "go_yoga", "name_sa": "Go Yoga", "name_en": "Go Yoga",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "jupiter", "house_class": "kendra_or_trikona"}, {"planet": "venus", "dignity": ["own", "exalted"]}]},
     "formation_text": "Jupiter in kendra or trikona, Venus in own or exaltation sign.",
     "significations_jsonb": {"gives": ["cattle_and_land", "wealth", "family_happiness"], "subcategory": "dhana"},
     "significations_text": "Wealthy in cattle and land, happy family life.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "sarvartha_chintamani"}],
     "rare": False, "source_citation": SARVARTHA_CHINTAMANI},

    {"canonical_id": "raja_yoga_lagna_10", "name_sa": "Lagneśa-Karmeśa Yoga", "name_en": "Lagna-10th Lord Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "lagna_lord_and_10th_lord_associate"}]},
     "formation_text": "The lagna lord and the 10th (karma) lord associate by conjunction, aspect or exchange.",
     "significations_jsonb": {"gives": ["career_success", "authority", "rise_in_position"], "subcategory": "raja"},
     "significations_text": "Career advancement, authority and recognition.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "raja_yoga_5_10", "name_sa": "Pañcameśa-Karmeśa Yoga", "name_en": "5th-10th Lord Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_5th_and_10th_lords"}]},
     "formation_text": "Lords of the 5th and 10th associate (conjunction/aspect/exchange).",
     "significations_jsonb": {"gives": ["authority_through_intellect", "fame", "ministerial_post"], "subcategory": "raja"},
     "significations_text": "Gains authority through intelligence; ministerial or advisory eminence.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "raja_yoga_4_5", "name_sa": "Caturthadhipa-Pañcameśa Yoga", "name_en": "4th-5th Lord Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_4th_and_5th_lords"}]},
     "formation_text": "Lords of the 4th and 5th associate.",
     "significations_jsonb": {"gives": ["property_education_fortune", "royal_comfort"], "subcategory": "raja"},
     "significations_text": "Property, education, and good fortune; comfortable life.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "raja_yoga_1_5", "name_sa": "Lagneśa-Pañcameśa Yoga", "name_en": "1st-5th Lord Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_lagna_and_5th_lords"}]},
     "formation_text": "Lagna lord and 5th lord associate (conjunction/aspect/exchange).",
     "significations_jsonb": {"gives": ["intelligence", "progeny_fortune", "purva_punya"], "subcategory": "raja"},
     "significations_text": "Sharp intellect, fortune from past merit, blessed with good progeny.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "raja_yoga_1_4", "name_sa": "Lagneśa-Caturthadhipa Yoga", "name_en": "1st-4th Lord Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_lagna_and_4th_lords"}]},
     "formation_text": "Lagna lord and 4th lord associate.",
     "significations_jsonb": {"gives": ["property", "home_happiness", "vehicles"], "subcategory": "raja"},
     "significations_text": "Property, domestic happiness, conveyances.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "raja_yoga_4_9", "name_sa": "Caturthadhipa-Bhāgyeśa Yoga", "name_en": "4th-9th Lord Raja Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_4th_and_9th_lords"}]},
     "formation_text": "Lords of the 4th and 9th associate.",
     "significations_jsonb": {"gives": ["property_and_fortune", "vehicle", "estate"], "subcategory": "raja"},
     "significations_text": "Landed estate, fortune, conveyances.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    # ── §3.7 — Jaimini Yogas (from Jaimini Sutram) ───────────────────────────

    {"canonical_id": "jaimini_raja_yoga_atmakaraka_kendra", "name_sa": "Ātmakāraka Kendra Yoga",
     "name_en": "Jaimini Atmakaraka Kendra Raja Yoga",
     "category": "raja", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "atmakaraka", "house_class": "kendra_from_karakamsha"}]},
     "formation_text": "The Atmakaraka (the planet with the highest longitude degree) in a kendra from the Karakamsha lagna.",
     "significations_jsonb": {"gives": ["authority", "royal_status", "leadership"], "subcategory": "jaimini_raja"},
     "significations_text": "High status, authority; the soul's purpose in leadership.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_karakamsha_jupiter", "name_sa": "Karakāṃśa Guru Yoga",
     "name_en": "Jaimini Karakamsha Jupiter Yoga",
     "category": "raja", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "jupiter", "house": ["karakamsha_lagna"], "or_aspect": True}]},
     "formation_text": "Jupiter in or aspecting the Karakamsha lagna.",
     "significations_jsonb": {"gives": ["vedic_learning", "dharma", "eloquence", "royal_favour"], "subcategory": "jaimini_raja"},
     "significations_text": "Learned in the Vedas, eloquent, pious, favoured by rulers.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_karakamsha_venus", "name_sa": "Karakāṃśa Śukra Yoga",
     "name_en": "Jaimini Karakamsha Venus Yoga",
     "category": "dhana", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "venus", "house": ["karakamsha_lagna"], "or_aspect": True}]},
     "formation_text": "Venus in or aspecting the Karakamsha lagna.",
     "significations_jsonb": {"gives": ["luxury", "wealth", "marital_happiness", "arts"], "subcategory": "jaimini_dhana"},
     "significations_text": "Wealthy, enjoys luxury, marital happiness, skill in arts.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_karakamsha_sun", "name_sa": "Karakāṃśa Sūrya Yoga",
     "name_en": "Jaimini Karakamsha Sun Yoga",
     "category": "raja", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "sun", "house": ["karakamsha_lagna"], "or_aspect": True}]},
     "formation_text": "Sun in or aspecting the Karakamsha lagna.",
     "significations_jsonb": {"gives": ["government_service", "authority", "royal_employment"], "subcategory": "jaimini_raja"},
     "significations_text": "Government service, employment by royalty or authority.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_karakamsha_moon", "name_sa": "Karakāṃśa Candra Yoga",
     "name_en": "Jaimini Karakamsha Moon Yoga",
     "category": "dhana", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "moon", "house": ["karakamsha_lagna"], "or_aspect": True}]},
     "formation_text": "Moon in or aspecting the Karakamsha lagna.",
     "significations_jsonb": {"gives": ["government_work", "trade_in_liquids", "agriculture"], "subcategory": "jaimini_dhana"},
     "significations_text": "Trading in liquids, agricultural pursuits, employment under authority.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_karakamsha_mars", "name_sa": "Karakāṃśa Kuja Yoga",
     "name_en": "Jaimini Karakamsha Mars Yoga",
     "category": "other", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "mars", "house": ["karakamsha_lagna"], "or_aspect": True}]},
     "formation_text": "Mars in or aspecting the Karakamsha lagna.",
     "significations_jsonb": {"gives": ["engineering", "weapons", "fire_related_work", "valor"], "subcategory": "jaimini"},
     "significations_text": "Works with weapons, fire or metals; valorous.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_karakamsha_saturn", "name_sa": "Karakāṃśa Śani Yoga",
     "name_en": "Jaimini Karakamsha Saturn Yoga",
     "category": "other", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "saturn", "house": ["karakamsha_lagna"], "or_aspect": True}]},
     "formation_text": "Saturn in or aspecting the Karakamsha lagna.",
     "significations_jsonb": {"gives": ["labour", "iron_works", "service_industry", "austerity"], "subcategory": "jaimini"},
     "significations_text": "Laborious work, service, iron or machinery trades.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_karakamsha_rahu", "name_sa": "Karakāṃśa Rāhu Yoga",
     "name_en": "Jaimini Karakamsha Rahu Yoga",
     "category": "other", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "rahu", "house": ["karakamsha_lagna"]}]},
     "formation_text": "Rahu in the Karakamsha lagna.",
     "significations_jsonb": {"gives": ["technical_skill", "foreign_elements", "deception_or_cunning"], "subcategory": "jaimini"},
     "significations_text": "Technical, foreign, or unconventional profession; possibly deceptive.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_arudha_trikona_raja", "name_sa": "Āruḍha Trikoṇa Rāja Yoga",
     "name_en": "Jaimini Arudha Trikona Raja Yoga",
     "category": "raja", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"relation": "benefic_in_or_aspecting_arudha_lagna"}, {"relation": "arudha_lagna_lord_in_kendra_or_trikona_from_al"}]},
     "formation_text": "Benefic in or aspecting the Arudha Lagna (AL), with the AL lord in kendra/trikona from the AL.",
     "significations_jsonb": {"gives": ["public_image_rise", "social_status", "fame"], "subcategory": "jaimini_raja"},
     "significations_text": "Strong public image, social rise, fame.",
     "cancellation_conditions": {"weakened_if": ["malefics_in_or_aspecting_al_without_benefic_support"]},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_amatyakaraka_10th", "name_sa": "Amātyakāraka Daśama Yoga",
     "name_en": "Jaimini Amatyakaraka 10th Yoga",
     "category": "raja", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "amatyakaraka", "house": ["10"], "or_kendra_from_karakamsha": True}]},
     "formation_text": "The Amatyakaraka (planet with second-highest longitude degree) in the 10th or kendra from Karakamsha.",
     "significations_jsonb": {"gives": ["career_excellence", "ministerial_role", "high_status_profession"], "subcategory": "jaimini_raja"},
     "significations_text": "Excellent career, ministerial or advisory position, high professional status.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_atmakaraka_trikona_benefic", "name_sa": "Ātmakāraka Trikoṇa Śubha Yoga",
     "name_en": "Jaimini Atmakaraka Trikona Benefic Yoga",
     "category": "raja", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"planet": "atmakaraka", "house_class": "trikona_from_karakamsha"}, {"planet": "benefic", "same_house_or_aspect": True}]},
     "formation_text": "Atmakaraka in a trikona from Karakamsha with a benefic influence.",
     "significations_jsonb": {"gives": ["spiritual_intelligence", "fortune", "self_realisation_path"], "subcategory": "jaimini_raja"},
     "significations_text": "Strong dharmic fortune, spiritual inclination, self-aware path.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    {"canonical_id": "jaimini_al_11th_dhana", "name_sa": "Āruḍha Lābha Yoga",
     "name_en": "Jaimini Arudha 11th Dhana Yoga",
     "category": "dhana", "school": "jaimini",
     "formation_rule_jsonb": {"requires": [{"relation": "benefic_in_11th_from_arudha_lagna"}]},
     "formation_text": "A benefic in the 11th from the Arudha Lagna (AL).",
     "significations_jsonb": {"gives": ["income_from_public_life", "gains_through_image"], "subcategory": "jaimini_dhana"},
     "significations_text": "Income and gains through public activities and social image.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jaimini_sutram"}],
     "rare": False, "source_citation": JAIMINI_SUTRAM},

    # ── §3.8 — Additional Nabhasa Yoga completions and named variants ──────────

    {"canonical_id": "parivartana_kendra_trikona", "name_sa": "Kendra-Trikoṇa Parivartana",
     "name_en": "Kendra-Trikona Parivartana Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "sign_exchange_between_kendra_lord_and_trikona_lord"}]},
     "formation_text": "Exchange of signs between a kendra lord and a trikona lord — the most powerful parivartana.",
     "significations_jsonb": {"gives": ["raja_yoga_via_exchange", "mutual_empowerment"], "subcategory": "raja"},
     "significations_text": "Powerful raja yoga through mutual sign exchange.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "subha_yoga_saravali", "name_sa": "Śubha Yoga (Saravalī)",
     "name_en": "Subha Yoga (Saravali)",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "benefic_in_2nd_from_moon"}]},
     "formation_text": "A benefic planet in the 2nd from the Moon (Saravali variant).",
     "significations_jsonb": {"gives": ["wealth", "good_nature", "happiness"], "subcategory": "chandra_yoga"},
     "significations_text": "Wealthy, virtuous, happy.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali", "chapter": 38}],
     "rare": False, "source_citation": SARAVALI_CH38},

    {"canonical_id": "asubha_yoga_saravali", "name_sa": "Aśubha Yoga (Saravalī)",
     "name_en": "Asubha Yoga (Saravali)",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "malefic_in_2nd_from_moon"}]},
     "formation_text": "A malefic planet in the 2nd from the Moon (Saravali variant).",
     "significations_jsonb": {"gives": ["trouble", "poverty", "harsh_speech"], "subcategory": "chandra_yoga"},
     "significations_text": "Trouble, poverty, harsh in speech.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali", "chapter": 38}],
     "rare": False, "source_citation": SARAVALI_CH38},

    {"canonical_id": "lagnadhi_yoga", "name_sa": "Lagnādhī Yoga", "name_en": "Lagnadhi Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "benefics_in_6_7_8_from_lagna"}]},
     "formation_text": "Benefics in the 6th, 7th and 8th from the lagna.",
     "significations_jsonb": {"gives": ["wealth", "happiness", "learning", "fame"], "subcategory": "raja"},
     "significations_text": "Learned, prosperous, famous, happy.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "hari_yoga_saravali", "name_sa": "Hari Yoga", "name_en": "Hari Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "benefics_in_2_12_8_from_2nd_lord"}]},
     "formation_text": "Benefics in the 2nd, 12th and 8th counted from the 2nd lord.",
     "significations_jsonb": {"gives": ["wealth", "fame", "preserved_by_deity"], "subcategory": "raja"},
     "significations_text": "Wealthy, famous, protected by divine favour.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": True, "source_citation": SARAVALI},

    {"canonical_id": "hara_yoga_saravali", "name_sa": "Hara Yoga", "name_en": "Hara Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "benefics_in_4_9_8_from_7th_lord"}]},
     "formation_text": "Benefics in the 4th, 9th and 8th counted from the 7th lord.",
     "significations_jsonb": {"gives": ["devotion", "spiritual_eminence", "fame"], "subcategory": "raja"},
     "significations_text": "Devotional, spiritually eminent, favoured.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": True, "source_citation": SARAVALI},

    {"canonical_id": "kalpadruma_yoga", "name_sa": "Kalpadruma", "name_en": "Kalpadruma Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "lagna_lord_dispositor_chain_all_in_own_exalt_or_kendra_trikona"}, {"condition": "each_step_strong_or_exalted"}]},
     "formation_text": "Lagna lord, its dispositor, and its dispositor's dispositor all in own, exaltation, or strong kendra/trikona positions.",
     "significations_jsonb": {"gives": ["royalty", "great_wealth", "supreme_authority"], "subcategory": "raja"},
     "significations_text": "King-like status; abundant wealth and authority like the wish-fulfilling tree.",
     "cancellation_conditions": {"weakened_if": ["any_link_in_chain_debilitated_or_combust"]},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": True, "source_citation": SARAVALI},

    {"canonical_id": "trimurthi_yoga", "name_sa": "Trimūrthi Yoga", "name_en": "Trimurthi Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "sun_moon_jupiter_in_mutual_angular_or_trinal"}]},
     "formation_text": "Sun, Moon and Jupiter in mutual angular or trinal relationship.",
     "significations_jsonb": {"gives": ["piety", "dharmic_life", "fame", "spiritual_merit"], "subcategory": "named"},
     "significations_text": "Pious, dharmic, spiritually meritorious.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "chandra_adhi_yoga", "name_sa": "Candra Ādhi Yoga", "name_en": "Chandra Adhi Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "benefics_in_6_7_8_from_moon"}]},
     "formation_text": "Benefics (Mercury, Venus, Jupiter) in the 6th, 7th and 8th from the Moon.",
     "significations_jsonb": {"gives": ["leadership", "health", "wealth", "command"], "subcategory": "raja"},
     "significations_text": "Leader, healthy, wealthy, commanding over others.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 36}],
     "rare": False, "source_citation": BPHS_CH36},

    {"canonical_id": "dhanayoga_lagna_9_11", "name_sa": "Dhana Yoga (1-9-11)", "name_en": "Dhana Yoga (lagna-9th-11th lords)",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_among_lagna_9th_and_11th_lords"}]},
     "formation_text": "The lagna lord, 9th lord and 11th lord associate (triple combination).",
     "significations_jsonb": {"gives": ["sustained_wealth", "fortune_income_combined"], "subcategory": "dhana"},
     "significations_text": "Steady, sustained wealth through fortune and enterprise.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH41},

    {"canonical_id": "dhanayoga_2_9", "name_sa": "Dhana Yoga (2-9)", "name_en": "Dhana Yoga (2nd-9th lords)",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "association_of_2nd_and_9th_lords"}]},
     "formation_text": "Lords of the 2nd and 9th associate — wealth through fortune.",
     "significations_jsonb": {"gives": ["inherited_or_fortunate_wealth"], "subcategory": "dhana"},
     "significations_text": "Wealth through luck, inheritance or divine grace.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 41}],
     "rare": False, "source_citation": BPHS_CH41},

    {"canonical_id": "parivartana_dusthana_good", "name_sa": "Khala Parivartana", "name_en": "Khala Parivartana Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "sign_exchange_where_both_lords_include_dusthana_but_not_6_8_12_alone"}]},
     "formation_text": "Exchange between a dusthana lord and a trikona or kendra lord — mixed results.",
     "significations_jsonb": {"gives": ["mixed_empowerment", "dusthana_tainted"], "subcategory": "aristha"},
     "significations_text": "Mixed fortune; dusthana themes enter the auspicious house.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    # ── §3.9 — Aristha / negative yogas (BPHS Ch.42) ─────────────────────────

    {"canonical_id": "nirbhagya_yoga", "name_sa": "Nirbhāgya Yoga", "name_en": "Nirbhagya Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "lagna_lord", "house_class": "dusthana"}, {"planet": "9th_lord", "house_class": "dusthana"}]},
     "formation_text": "Both the lagna lord and the 9th lord in dusthanas (6/8/12).",
     "significations_jsonb": {"gives": ["blocked_fortune", "hardship", "lack_of_luck"], "subcategory": "aristha"},
     "significations_text": "Fortune blocked; chronic struggle and lack of luck.",
     "cancellation_conditions": {"bhanga": ["strong_benefic_yoga_present", "neecha_bhanga"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 42}],
     "rare": False, "source_citation": BPHS_CH42},

    {"canonical_id": "dur_yoga", "name_sa": "Dur Yoga", "name_en": "Dur Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "lagna_lord", "house_class": "dusthana"}, {"planet": "10th_lord", "house_class": "dusthana"}]},
     "formation_text": "Both the lagna lord and the 10th (karma) lord in dusthanas.",
     "significations_jsonb": {"gives": ["career_blockage", "hard_livelihood", "obscurity"], "subcategory": "aristha"},
     "significations_text": "Laborious livelihood; career advancement blocked.",
     "cancellation_conditions": {"bhanga": ["benefic_aspect_on_10th_lord"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 42}],
     "rare": False, "source_citation": BPHS_CH42},

    {"canonical_id": "shunya_yoga", "name_sa": "Śūnya Yoga", "name_en": "Shunya Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "lagna_lord_in_12th_with_no_benefic_support"}]},
     "formation_text": "Lagna lord in the 12th house, with no benefic support.",
     "significations_jsonb": {"gives": ["expenditure_of_self", "foreign_lands", "seclusion"], "subcategory": "aristha"},
     "significations_text": "Self-dissipation, expenses, seclusion or foreign residence.",
     "cancellation_conditions": {"bhanga": ["benefic_aspect_on_lagna_lord", "lagna_lord_in_own_exalt_in_12th"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 42}],
     "rare": False, "source_citation": BPHS_CH42},

    {"canonical_id": "asutha_yoga", "name_sa": "Āsutha Yoga", "name_en": "Asutha Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "5th_lord", "house_class": "dusthana"}, {"planet": "moon", "afflicted": True}]},
     "formation_text": "5th lord in a dusthana with the Moon afflicted by malefics.",
     "significations_jsonb": {"gives": ["progeny_difficulty", "mental_anxiety", "blocked_creativity"], "subcategory": "aristha"},
     "significations_text": "Obstacles to progeny; mental anxiety and creative blockage.",
     "cancellation_conditions": {"bhanga": ["jupiter_aspects_5th_or_5th_lord"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 42}],
     "rare": False, "source_citation": BPHS_CH42},

    {"canonical_id": "khalwa_yoga", "name_sa": "Khalvā Yoga", "name_en": "Khalwa Yoga",
     "category": "aristha", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "no_planet_in_kendra_from_lagna"}]},
     "formation_text": "All four kendras (1, 4, 7, 10) empty of planets.",
     "significations_jsonb": {"gives": ["lack_of_strength", "weakness_of_resolve", "poor_foundation"], "subcategory": "aristha"},
     "significations_text": "Weak foundations; difficulty establishing stability.",
     "cancellation_conditions": {"bhanga": ["strong_trines", "planets_in_all_trikonas"]},
     "classical_citations": [{"text_id": "bphs", "chapter": 42}],
     "rare": False, "source_citation": BPHS_CH42},

    # ── §3.10 — Ashtakvarga-based named yogas ─────────────────────────────────

    {"canonical_id": "sarvashraya_yoga", "name_sa": "Sarvāśraya Yoga", "name_en": "Sarvashraya Yoga",
     "category": "dhana", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "high_sarvashtakavarga_score_in_lagna_5th_9th", "threshold": "high_above_25_per_house"}]},
     "formation_text": "Very high Sarvashtakavarga points (25+) in the 1st, 5th and 9th houses (trikona strength).",
     "significations_jsonb": {"gives": ["all_round_support", "good_fortune_in_life"], "subcategory": "named"},
     "significations_text": "Strong all-round support in life; trikonas empowered.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs"}],
     "rare": False, "source_citation": BPHS_CH39},

    # ── §3.11 — Brihat Jataka / Jataka Parijata named yogas ──────────────────

    {"canonical_id": "nripathi_yoga", "name_sa": "Nṛpati Yoga", "name_en": "Nripati Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "majority_of_planets_in_kendra_and_own_exalt_friendly_signs"}]},
     "formation_text": "Majority of planets in kendras and in own, exaltation or friendly signs.",
     "significations_jsonb": {"gives": ["king_like", "commands_forces", "wealth"], "subcategory": "raja"},
     "significations_text": "King-like authority, commands forces, wealthy.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "brihat_jataka"}],
     "rare": False, "source_citation": BRIHAT_JATAKA},

    {"canonical_id": "arivargottama_yoga", "name_sa": "Vargottama Yoga", "name_en": "Vargottama Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "any", "condition": "same_sign_in_rasi_and_navamsa"}]},
     "formation_text": "A planet occupies the same sign in the Rashi (D1) and Navamsa (D9) charts — Vargottama.",
     "significations_jsonb": {"gives": ["strength", "purity_of_signification", "full_expression_of_planet"], "subcategory": "named"},
     "significations_text": "Planet's significations are expressed with full force and purity.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs"}],
     "rare": False, "source_citation": CLASSICAL},

    {"canonical_id": "pushyamrita_yoga", "name_sa": "Puṣyāmṛta Yoga", "name_en": "Pushyamrita Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"condition": "birth_on_pushya_nakshatra"}, {"planet": "moon", "in": "own_or_exaltation_or_kendra"}]},
     "formation_text": "Birth on Pushya nakshatra with the Moon strong (in own/exaltation/kendra).",
     "significations_jsonb": {"gives": ["wealth", "health", "fame", "nourishment"], "subcategory": "named"},
     "significations_text": "Abundant prosperity, health, and good fame.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jataka_parijata"}],
     "rare": False, "source_citation": JATAKA_PARIJATA},

    {"canonical_id": "amara_yoga", "name_sa": "Amara Yoga", "name_en": "Amara Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "all_three_supreme_planets_sun_moon_jupiter_in_own_exalt_or_kendra"}]},
     "formation_text": "Sun, Moon and Jupiter all in own, exaltation, or kendra positions simultaneously.",
     "significations_jsonb": {"gives": ["immortal_fame", "authority", "longevity"], "subcategory": "raja"},
     "significations_text": "Lasting fame, authority, healthy long life.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jataka_parijata"}],
     "rare": True, "source_citation": JATAKA_PARIJATA},

    {"canonical_id": "kumuda_yoga", "name_sa": "Kumuda Yoga", "name_en": "Kumuda Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "saturn", "house_class": "trikona"}, {"planet": "moon", "house_class": "kendra"}]},
     "formation_text": "Saturn in a trikona and Moon in a kendra.",
     "significations_jsonb": {"gives": ["perseverance", "steady_wealth", "stability"], "subcategory": "named"},
     "significations_text": "Patient, persevering, acquires wealth steadily.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jataka_parijata"}],
     "rare": False, "source_citation": JATAKA_PARIJATA},

    {"canonical_id": "chapa_yoga_named", "name_sa": "Chāpa (Named)", "name_en": "Chapa Yoga (named variant)",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "lagna_lord", "house_class": "kendra"}, {"relation": "2nd_and_11th_lords_strong_and_associated"}]},
     "formation_text": "Lagna lord in a kendra, with the 2nd and 11th lords strong and associated.",
     "significations_jsonb": {"gives": ["wealth", "fame", "high_career"], "subcategory": "raja"},
     "significations_text": "Wealth, fame and career eminence.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "jataka_parijata"}],
     "rare": False, "source_citation": JATAKA_PARIJATA},

    {"canonical_id": "uttama_yoga", "name_sa": "Uttama Yoga", "name_en": "Uttama Yoga",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"relation": "lagna_lord_in_10th_or_10th_lord_in_lagna"}, {"condition": "strong_benefic_aspect"}]},
     "formation_text": "Lagna lord in the 10th or 10th lord in the lagna, with strong benefic aspect.",
     "significations_jsonb": {"gives": ["supreme_career", "honour", "public_recognition"], "subcategory": "raja"},
     "significations_text": "Supreme career achievement and public honour.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "sarvartha_chintamani"}],
     "rare": False, "source_citation": SARVARTHA_CHINTAMANI},

    {"canonical_id": "nipuna_yoga", "name_sa": "Nipuṇa Yoga", "name_en": "Nipuna Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "mercury", "house_class": "kendra_or_trikona"}, {"planet": "venus", "house_class": "kendra_or_trikona"}]},
     "formation_text": "Both Mercury and Venus in kendras or trikonas.",
     "significations_jsonb": {"gives": ["skill", "dexterity", "expertise_in_craft"], "subcategory": "named"},
     "significations_text": "Expert, dexterous, gifted in craft and communication.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "sarvartha_chintamani"}],
     "rare": False, "source_citation": SARVARTHA_CHINTAMANI},

    {"canonical_id": "dharma_yoga", "name_sa": "Dharma Yoga", "name_en": "Dharma Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"planet": "9th_lord", "house_class": "kendra_or_trikona"}, {"planet": "jupiter", "strong": True}]},
     "formation_text": "9th lord in a kendra or trikona, with Jupiter strong.",
     "significations_jsonb": {"gives": ["righteousness", "dharmic_conduct", "religious_merit"], "subcategory": "named"},
     "significations_text": "Righteous, dharmic, respected for moral conduct.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "bphs", "chapter": 39}],
     "rare": False, "source_citation": BPHS_CH39},

    {"canonical_id": "mahabhagya_female", "name_sa": "Mahābhāgya (Strī)", "name_en": "Maha-Bhagya Yoga (female)",
     "category": "raja", "school": "parashari",
     "formation_rule_jsonb": {"requires": [{"condition": "night_birth"}, {"condition": "female_native"}, {"planets": ["sun", "moon", "lagna"], "all_in": "even_signs"}]},
     "formation_text": "Female native born at night with Sun, Moon and lagna all in even signs.",
     "significations_jsonb": {"gives": ["great_fortune", "high_status", "virtue", "longevity"], "subcategory": "raja"},
     "significations_text": "Greatly fortunate, virtuous, high-born or elevated female native.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali"}, {"text_id": "phaladeepika"}],
     "rare": False, "source_citation": SARAVALI},

    {"canonical_id": "veena_yoga", "name_sa": "Vīṇā Yoga", "name_en": "Veena Yoga",
     "category": "other", "school": "parashari",
     "formation_rule_jsonb": {"distinct_signs_occupied": 7, "note": "synonym for Vallaki/Veena in Saravali"},
     "formation_text": "All seven planets in seven different signs (also called Vallaki in BPHS).",
     "significations_jsonb": {"gives": ["music", "dance", "happy", "wealthy"], "subcategory": "nabhasa_sankhya"},
     "significations_text": "Fond of music and dance, happy, skilful.",
     "cancellation_conditions": {},
     "classical_citations": [{"text_id": "saravali", "chapter": 34}],
     "rare": False, "source_citation": SARAVALI_CH34},
]

# ── §3.9a — Saravali lookup table (20 named yogas with structured templates) ───

SARAVALI_YOGA_LOOKUP: dict[str, tuple[str, str, dict]] = {
    "Subha Yoga":            ("subha_yoga",           "other",  {"requires": [{"relation": "benefic_in_2nd_from_moon"}]}),
    "Asubha Yoga":           ("asubha_yoga",           "aristha",{"requires": [{"relation": "malefic_in_2nd_from_moon"}]}),
    "Lagnadhi Yoga":         ("lagnadhi_yoga",          "raja",   {"requires": [{"relation": "benefics_in_6_7_8_from_lagna"}]}),
    "Hari Yoga":             ("hari_yoga",              "raja",   {"requires": [{"relation": "benefics_in_2_12_8_from_2nd_lord"}]}),
    "Hara Yoga":             ("hara_yoga",              "raja",   {"requires": [{"relation": "benefics_in_4_9_8_from_7th_lord"}]}),
    "Brahma Yoga":           ("brahma_yoga_classical",  "raja",   {"requires": [{"relation": "jupiter_venus_mercury_in_kendras_from_10_11_9_lords"}]}),
    "Kalpadruma Yoga":       ("kalpadruma_yoga",        "raja",   {"requires": [{"relation": "lagna_lord_and_dispositor_chain_all_in_own_exalt_friendly_kendra_trikona"}]}),
    "Trimurthi Yoga":        ("trimurthi_yoga",         "other",  {"requires": [{"relation": "sun_moon_jupiter_in_angular_or_trinal_relation"}]}),
    "Matsya Yoga":           ("matsya_yoga",            "other",  {"requires": [{"relation": "planets_in_5th_8th_and_lagna_or_9th"}]}),
    "Koorma Yoga":           ("koorma_yoga",            "other",  {"requires": [{"relation": "benefics_in_5_6_7_malefics_in_1_3_8"}]}),
    "Khadga Yoga":           ("khadga_yoga",            "raja",   {"requires": [{"relation": "2nd_lord_in_kendra_or_trikona_lagna_lord_strong"}]}),
    "Kusuma Yoga":           ("kusuma_yoga",            "other",  {"requires": [{"relation": "venus_in_kendra_moon_in_trikona_saturn_in_upachaya"}]}),
    "Mridanga Yoga":         ("mridanga_yoga",          "raja",   {"requires": [{"relation": "lagna_lord_in_own_exalted_sign_aspected_by_strong_planet"}]}),
    "Srinatha Yoga":         ("srinatha_yoga",          "raja",   {"requires": [{"relation": "7th_lord_in_own_exaltation_and_10th_lord_with_it"}]}),
    "Damini Yoga":           ("damini_yoga",            "other",  {"requires": [{"relation": "planets_in_six_signs_nabhasa_dama"}]}),
    "Pasa Yoga":             ("pasa_yoga",              "other",  {"requires": [{"relation": "planets_in_five_signs_nabhasa_pasha"}]}),
    "Kedara Yoga (Saravali)":("kedara_sar",             "other",  {"requires": [{"relation": "planets_in_four_signs_nabhasa_kedara"}]}),
    "Vajra Yoga (Saravali)": ("vajra_sar",              "other",  {"requires": [{"relation": "benefics_in_1_7_malefics_in_4_10"}]}),
    "Yava Yoga (Saravali)":  ("yava_sar",               "other",  {"requires": [{"relation": "malefics_in_1_7_benefics_in_4_10"}]}),
    "Vapi Yoga (Saravali)":  ("vapi_sar",               "dhana",  {"requires": [{"relation": "all_planets_in_panapharas_or_apoklimas"}]}),
}

# ── §3.9b.i — Yoga family taxonomy (seeded into yoga_families table) ──────────
# Added 2026-06-17 — Yoga Subsystem Gate-1

YOGA_FAMILIES: list[dict] = [
    {
        "family_id": "mahapurusha",
        "parent_family_id": None,
        "name_en": "Pancha Mahapurusha",
        "name_sa": "Pañca Mahāpuruṣa",
        "description": "Five great-man yogas formed by the five non-luminary planets in own or exaltation sign in a kendra",
        "classical_citation": "BPHS Ch.75 (Pancha Mahapurusha Yoga adhyaya); Saravali Ch.27",
    },
    {
        "family_id": "nabhasa",
        "parent_family_id": None,
        "name_en": "Nabhasa Yogas",
        "name_sa": "Nābhasa",
        "description": "Sky (nabhasa) yogas defined by the distribution of all seven planets across signs, houses or sign-types",
        "classical_citation": "BPHS Ch.35 (Nabhasa Yoga adhyaya); Saravali Ch.34–37",
    },
    {
        "family_id": "nabhasa_aakriti",
        "parent_family_id": "nabhasa",
        "name_en": "Nabhasa — Aakriti (Shape)",
        "name_sa": "Ākṛti",
        "description": "20 Nabhasa yogas defined by the geometric shape formed by planetary positions across houses",
        "classical_citation": "BPHS Ch.35 v.1–40; Saravali Ch.35",
    },
    {
        "family_id": "nabhasa_sankhya",
        "parent_family_id": "nabhasa",
        "name_en": "Nabhasa — Sankhya (Number)",
        "name_sa": "Saṅkhyā",
        "description": "7 Nabhasa yogas defined by the count of signs occupied by the seven planets (1 to 7)",
        "classical_citation": "BPHS Ch.35 v.41–48; Saravali Ch.36",
    },
    {
        "family_id": "nabhasa_dala",
        "parent_family_id": "nabhasa",
        "name_en": "Nabhasa — Dala (Group)",
        "name_sa": "Dala",
        "description": "2 Nabhasa yogas (Mala/Sarpa) defined by benefics or malefics occupying the three kendras",
        "classical_citation": "BPHS Ch.35 v.49–52; Saravali Ch.37",
    },
    {
        "family_id": "nabhasa_asraya",
        "parent_family_id": "nabhasa",
        "name_en": "Nabhasa — Asraya (Sign-type)",
        "name_sa": "Āśraya",
        "description": "3 Nabhasa yogas (Rajju/Musala/Nala) defined by all planets in movable, fixed or dual signs",
        "classical_citation": "BPHS Ch.35 v.53–56; Saravali Ch.34",
    },
    {
        "family_id": "raja",
        "parent_family_id": None,
        "name_en": "Raja Yogas",
        "name_sa": "Rāja",
        "description": "Status-conferring combinations, primarily kendra-trikona lord associations and special dharmika linkages",
        "classical_citation": "BPHS Ch.39–40; Phaladeepika Ch.7",
    },
    {
        "family_id": "raja_dharma_karma",
        "parent_family_id": "raja",
        "name_en": "Dharma-Karmadhipati Raja",
        "name_sa": "Dharma-Karmādhipati",
        "description": "Raja yoga formed by the 9th and 10th lords associating",
        "classical_citation": "BPHS Ch.39 v.1–6",
    },
    {
        "family_id": "raja_vipareeta",
        "parent_family_id": "raja",
        "name_en": "Vipareeta Raja",
        "name_sa": "Viparīta Rāja",
        "description": "Paradoxical raja yogas formed by dusthana lords placed in dusthanas",
        "classical_citation": "BPHS Ch.40 v.7–12; Phaladeepika Ch.7",
    },
    {
        "family_id": "dhana",
        "parent_family_id": None,
        "name_en": "Dhana Yogas",
        "name_sa": "Dhana",
        "description": "Wealth-producing combinations, primarily involving lords of houses 1, 2, 5, 9, 11",
        "classical_citation": "BPHS Ch.41 (Dhana Yoga adhyaya)",
    },
    {
        "family_id": "chandra",
        "parent_family_id": None,
        "name_en": "Chandra Yogas",
        "name_sa": "Candra",
        "description": "Lunar yogas formed by planets placed in relation to the Moon (2nd, 12th, kendras)",
        "classical_citation": "BPHS Ch.29–30; Saravali Ch.38",
    },
    {
        "family_id": "surya",
        "parent_family_id": None,
        "name_en": "Surya Yogas",
        "name_sa": "Sūrya",
        "description": "Solar yogas formed by planets placed in the 2nd and 12th from the Sun",
        "classical_citation": "BPHS Ch.30; Saravali Ch.41",
    },
    {
        "family_id": "arishta",
        "parent_family_id": None,
        "name_en": "Arishta Yogas",
        "name_sa": "Ariṣṭa",
        "description": "Negative/afflicting combinations indicating hardship, poverty or isolation",
        "classical_citation": "BPHS Ch.42 (Arishta Yoga adhyaya)",
    },
    {
        "family_id": "sannyasa",
        "parent_family_id": None,
        "name_en": "Sannyasa / Pravrajya Yogas",
        "name_sa": "Pravrajyā",
        "description": "Renunciation and ascetic-path combinations involving 4+ planets grouped in a house",
        "classical_citation": "BPHS Ch.36 (Pravrajya Yoga adhyaya); Saravali Ch.45",
    },
    {
        "family_id": "specialized",
        "parent_family_id": None,
        "name_en": "Specialized Yogas",
        "name_sa": None,
        "description": "Named combinatorial yogas from multiple classical sources (Kala Sarpa, Guru-Chandala, etc.)",
        "classical_citation": "Various — BPHS, Saravali, Phaladeepika",
    },
]


def seed_yoga_families(conn, dry_run: bool = False) -> dict:
    """
    Seed yoga_families table with family taxonomy.
    L0 idempotency: ON CONFLICT DO NOTHING.
    Transaction ownership: caller owns commit.
    Returns dict with families_inserted count and warnings.
    """
    if dry_run:
        return {"families_inserted": len(YOGA_FAMILIES), "warnings": []}

    warnings: list[str] = []
    inserted = 0

    # Two-pass: root families first, then children (parent FK constraint)
    roots = [f for f in YOGA_FAMILIES if f["parent_family_id"] is None]
    children = [f for f in YOGA_FAMILIES if f["parent_family_id"] is not None]

    with conn.cursor() as cur:
        for f in roots + children:
            try:
                cur.execute("""
                    INSERT INTO yoga_families
                      (family_id, parent_family_id, name_en, name_sa, description, classical_citation)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (family_id) DO NOTHING
                """, (
                    f["family_id"],
                    f.get("parent_family_id"),
                    f["name_en"],
                    f.get("name_sa"),
                    f.get("description"),
                    f.get("classical_citation"),
                ))
                if cur.rowcount > 0:
                    inserted += 1
            except Exception as exc:
                warnings.append(f"yoga_families insert failed for {f['family_id']}: {exc}")
                logger.warning("[l0_yogas] yoga_families insert failed for %s: %s", f["family_id"], exc)

    logger.info("[l0_yogas] yoga_families: %d inserted, %d warnings", inserted, len(warnings))
    return {"families_inserted": inserted, "warnings": warnings}


# ── §3.9b — Corpus extraction helpers ─────────────────────────────────────────

# Recall-aid lexicon for yoga name detection (names only; not formation rules)
YOGA_NAME_LEXICON: list[str] = [
    "Pushkala", "Gandharva", "Vishnu", "Shiva", "Garuda", "Indra", "Mridanga",
    "Simhasana", "Dhwaja", "Kshema", "Bharati", "Gauri", "Kurma", "Matsya",
    "Khadga", "Kusuma", "Srinatha", "Devendra", "Amsavatara", "Marud",
]

# Generic named-yoga regex (the open-ended workhorse)
NAMED_YOGA_RE = re.compile(r'\b([A-Z][a-zA-Z]+(?:[ \-][A-Z][a-zA-Z]+)*)\s+[Yy]oga\b')

# YOGA_CHAPTERS chapter filter REMOVED 2026-06-09 (remediation).
# Root cause: the `chapter` column stores PDF page numbers, not classical chapter
# numbers. The previous ranges (bphs 30-45, saravali 27-51, phaladeepika 4-11)
# targeted introductory/preface PDF pages and missed the actual yoga content
# (bphs correct pages ~355-415, phaladeepika ~16-35, saravali 52-80+).
# Fix: drop the chapter filter entirely. The keyword filter
# `lower(content_en) LIKE '%yoga%'` is the correct gate and already present.
# This expands the scanned pool from ~37 chunks to ~403 chunks.
# YOGA_CHAPTERS: dict kept as empty for reference; not used in the query.
YOGA_CHAPTERS: dict[str, list[int]] = {}

# Canonical IDs of inline core — these names are already covered
_INLINE_IDS: set[str] = {y["canonical_id"] for y in YOGAS_CORE}


def _snake(name: str) -> str:
    """Convert yoga name to snake_case canonical_id."""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s


def _first_sentence(text: str) -> str:
    """Extract the first meaningful sentence from chunk content."""
    # Skip chapter/section headers (lines that are just numbers or very short)
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10]
    for line in lines:
        # Skip lines that look like chapter headers or page numbers
        if re.match(r'^[\d\s.]+$', line):
            continue
        # Take first sentence-like fragment
        m = re.search(r'[.!?]', line)
        if m:
            return line[:m.start() + 1].strip()
        if len(line) > 20:
            return line[:200].strip()
    return (lines[0][:200] if lines else text[:200]).strip()


def _infer_category(name: str, clause: str) -> str:
    """Infer yoga category from name and clause."""
    text_lower = (name + " " + clause).lower()
    if any(w in text_lower for w in ["raja", "royal", "king", "kingdom", "kingly", "sovereign"]):
        return "raja"
    if any(w in text_lower for w in ["dhana", "wealth", "riches", "money", "affluence"]):
        return "dhana"
    if any(w in text_lower for w in ["sannyasa", "pravrajya", "renunciation", "ascetic"]):
        return "sannyasa"
    if any(w in text_lower for w in ["aristha", "evil", "poverty", "trouble", "deprived"]):
        return "aristha"
    return "other"


def extract_yogas_from_corpus(conn) -> list[dict]:
    """
    §3.9b — corpus-verse structured extraction.

    Queries classical_text_chunks for yoga chapters in saravali/bphs/phaladeepika.
    For each chunk detects named yogas via SARAVALI_YOGA_LOOKUP + YOGA_NAME_LEXICON
    + NAMED_YOGA_RE. Builds structurally-complete rows (verbatim clause + chunk id).

    Returns list of yoga dicts NOT already in the inline core.
    Only emits rows with non-empty raw_verse_clause AND chunk_id.
    """
    if conn is None:
        return []

    extracted: dict[str, dict] = {}  # canonical_id -> yoga dict

    try:
        with conn.cursor() as cur:
            # Chapter filter REMOVED 2026-06-09 (chapter column = PDF page numbers,
            # not classical chapter numbers; old ranges mis-targeted intro/preface pages).
            # Keyword filter `lower(content_en) LIKE '%yoga%'` is the correct gate.
            cur.execute("""
                SELECT id::text, text_id, chapter, verse_ref, content_en, tradition_school
                FROM classical_text_chunks
                WHERE text_id IN ('bphs', 'saravali', 'phaladeepika', 'chamatkar_chintamani')
                  AND lower(content_en) LIKE '%yoga%'
                ORDER BY text_id, chapter, verse_start
            """)
            rows = cur.fetchall()
    except Exception as exc:
        logger.warning("[l0_yogas] corpus extraction query failed: %s", exc)
        return []

    for chunk_id, text_id, chapter, verse_ref, content_en, trad_school in rows:
        if not content_en:
            continue

        school = TEXT_SCHOOL.get(text_id, "parashari")
        citation_text_id = text_id
        citation = {"text_id": citation_text_id, "chapter": chapter, "verse_ref": verse_ref,
                    "chunk_id": chunk_id}

        # Detect yoga names in this chunk
        detected_names: list[str] = []

        # 1. SARAVALI_YOGA_LOOKUP keys
        for lookup_name in SARAVALI_YOGA_LOOKUP:
            base = lookup_name.split(" (")[0]  # "Vajra Yoga (Saravali)" -> "Vajra Yoga"
            if base.lower() in content_en.lower():
                detected_names.append(lookup_name)

        # 2. YOGA_NAME_LEXICON
        for lex_name in YOGA_NAME_LEXICON:
            pattern = re.compile(r'\b' + re.escape(lex_name) + r'\s+Yoga\b', re.IGNORECASE)
            if pattern.search(content_en):
                detected_names.append(lex_name + " Yoga")

        # 3. Generic regex
        for m in NAMED_YOGA_RE.finditer(content_en):
            full_name = m.group(0).strip()
            # Filter out false positives: must have a recognisable proper-noun prefix
            if len(m.group(1)) >= 3:
                detected_names.append(full_name)

        # Deduplicate while preserving order
        seen_names: set[str] = set()
        unique_names: list[str] = []
        for n in detected_names:
            key = n.lower().strip()
            if key not in seen_names:
                seen_names.add(key)
                unique_names.append(n)

        for raw_name in unique_names:
            # Normalise: strip trailing "Yoga" duplicates, get base name
            base_name = re.sub(r'\s+[Yy]oga$', '', raw_name).strip()
            name_en = base_name + " Yoga" if not raw_name.lower().endswith("yoga") else raw_name
            name_en = name_en.strip()

            # Skip generic/stop words
            stop_words = {"This", "The", "Such", "One", "Some", "If", "Sun", "Moon",
                          "Many", "Thus", "Here", "All", "Any", "No", "Not", "Two",
                          "Three", "Four", "Five", "Six", "Seven", "Its", "Of", "In",
                          "On", "At", "By", "For", "Or", "And", "To", "A", "An"}
            first_word = base_name.split()[0] if base_name.split() else ""
            if first_word in stop_words or len(base_name) < 3:
                continue

            # Lookup canonical_id
            lookup_key = None
            for k in SARAVALI_YOGA_LOOKUP:
                if k.lower().startswith(base_name.lower()) or base_name.lower() in k.lower():
                    lookup_key = k
                    break

            if lookup_key:
                cid, cat, frj = SARAVALI_YOGA_LOOKUP[lookup_key]
                formation_rule_jsonb = frj
                derivation = "structured_template"
            else:
                cid = _snake(base_name)
                # Extract verbatim defining clause from chunk
                # Find the sentence containing this yoga name
                name_pattern = re.compile(
                    r'([^.!?\n]{0,120}' + re.escape(base_name) + r'\s+[Yy]oga[^.!?\n]{0,200})',
                    re.IGNORECASE
                )
                clause_m = name_pattern.search(content_en)
                if clause_m:
                    raw_clause = clause_m.group(0).strip()[:500]
                else:
                    raw_clause = _first_sentence(content_en)

                if not raw_clause or len(raw_clause) < 5:
                    continue  # floor-ineligible: no clause

                cat = _infer_category(base_name, raw_clause)
                formation_rule_jsonb = {
                    "requires": [{"raw_verse_clause": raw_clause}],
                    "derivation": "corpus_verse"
                }
                derivation = "corpus_verse"

            # Skip if already in inline core
            if cid in _INLINE_IDS:
                continue

            # Skip if already extracted (ON CONFLICT handles DB-level; dict handles in-memory)
            if cid in extracted:
                continue

            # Build the verse clause for citation
            if derivation == "corpus_verse":
                raw_clause = formation_rule_jsonb["requires"][0].get("raw_verse_clause", "")
            else:
                # For lookup templates, extract the sentence containing the name for significations
                name_pattern2 = re.compile(
                    r'([^.!?\n]{0,50}' + re.escape(base_name) + r'\s+[Yy]oga[^.!?\n]{0,300})',
                    re.IGNORECASE
                )
                m2 = name_pattern2.search(content_en)
                raw_clause = m2.group(0).strip()[:400] if m2 else ""

            # Extract significations from the chunk (effect/result sentences)
            sig_text = ""
            # Look for result sentences after the formation
            result_patterns = [
                r'(?:native|person|one so born|such a person)[^.!?]{10,200}[.!?]',
                r'(?:will be|will have|gives|confers|causes|makes)[^.!?]{10,200}[.!?]',
            ]
            for rp in result_patterns:
                rm = re.search(rp, content_en, re.IGNORECASE)
                if rm:
                    sig_text = rm.group(0).strip()[:300]
                    break
            if not sig_text:
                sig_text = raw_clause[:200] if raw_clause else name_en

            formation_text = raw_clause if raw_clause else f"{name_en}: formation per {verse_ref} ({text_id} Ch.{chapter})"

            extracted[cid] = {
                "canonical_id": cid,
                "name_sa": base_name,
                "name_en": name_en,
                "category": cat,
                "school": school,
                "formation_rule_jsonb": formation_rule_jsonb,
                "formation_text": formation_text,
                "significations_jsonb": {"gives": [], "subcategory": derivation,
                                          "source_chunk": chunk_id},
                "significations_text": sig_text,
                "cancellation_conditions": {},
                "classical_citations": [citation],
                "rare": False,
                "source_citation": f"{text_id.upper()} Ch.{chapter} ({verse_ref})",
                # chunk_id is UUID; source_chunk_ids is BIGINT[] — store empty, ref in classical_citations
                "_chunk_id_str": chunk_id,
            }

    result = list(extracted.values())
    logger.info("[l0_yogas] corpus extraction: %d distinct yogas found", len(result))
    return result


# ── Helpers ────────────────────────────────────────────────────────────────────

def _yoga_synonyms(y: dict) -> list[str]:
    """Build synonym list from yoga name variants."""
    syns = [y["name_en"], y["name_sa"]]
    cid = y["canonical_id"]
    # Add common transliteration variants
    if "_" in cid:
        syns.append(cid.replace("_", " ").title())
    return list(dict.fromkeys(syns))  # deduplicate while preserving order


def _yoga_citation(y: dict) -> str:
    """Build a source_citation string for the ontology row."""
    return y.get("source_citation", CLASSICAL)


# ── Main seeder ────────────────────────────────────────────────────────────────

def seed_yogas(conn, build_id: str | None = None,
               dry_run: bool = False, autocommit: bool = False) -> dict:
    """
    Seed brahma_yoga_catalog, brahma_ontology (entity_class='yoga'),
    and reference_yogas.

    Returns dict with: catalog_inserted, ontology_inserted, ref_inserted,
                       total_rows, inline_count, extracted_count, warnings.

    Transaction ownership: caller owns commit when autocommit=False.
    """
    if dry_run:
        extracted_dry = extract_yogas_from_corpus(conn)
        total = len(YOGAS_CORE) + len(extracted_dry)
        return {
            "catalog_inserted": total,
            "ontology_inserted": total,
            "ref_inserted": total,
            "total_rows": total,
            "inline_count": len(YOGAS_CORE),
            "extracted_count": len(extracted_dry),
            "warnings": [],
        }

    warnings: list[str] = []
    catalog_inserted = 0
    ontology_inserted = 0
    ref_inserted = 0

    # Corpus extraction
    extracted = extract_yogas_from_corpus(conn)
    all_yogas = YOGAS_CORE + extracted

    logger.info("[l0_yogas] seeding %d yogas (%d inline + %d extracted)",
                len(all_yogas), len(YOGAS_CORE), len(extracted))

    with conn.cursor() as cur:
        for i, y in enumerate(all_yogas):
            cid = y["canonical_id"]

            # ── 1. brahma_yoga_catalog ──────────────────────────────────────
            try:
                cur.execute("""
                    INSERT INTO brahma_yoga_catalog
                      (canonical_id, name_sa, name_en, category, formation_rule_jsonb,
                       formation_text, significations_jsonb, significations_text,
                       cancellation_conditions, classical_citations, source_chunk_ids,
                       school, rare, computed_strength_formula)
                    VALUES (%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s,%s::jsonb,%s::jsonb,
                            %s,%s,%s,%s)
                    ON CONFLICT (canonical_id) DO NOTHING
                """, (
                    cid,
                    y["name_sa"],
                    y["name_en"],
                    y["category"],
                    json.dumps(y["formation_rule_jsonb"]),
                    y["formation_text"],
                    json.dumps(y["significations_jsonb"]),
                    y["significations_text"],
                    json.dumps(y.get("cancellation_conditions") or {}),
                    json.dumps(y.get("classical_citations") or []),
                    [],  # source_chunk_ids: BIGINT[] — UUIDs stored in classical_citations
                    y["school"],
                    y.get("rare", False),
                    y.get("computed_strength_formula"),
                ))
                if cur.rowcount > 0:
                    catalog_inserted += 1
            except Exception as exc:
                warnings.append(f"catalog insert failed for {cid}: {exc}")
                logger.warning("[l0_yogas] catalog insert failed for %s: %s", cid, exc)
                continue  # skip ontology + ref for this yoga

            # ── 2. brahma_ontology (entity_class='yoga') ────────────────────
            try:
                cur.execute("""
                    INSERT INTO brahma_ontology
                      (entity_class, canonical_id, canonical_name_en, canonical_name_sa,
                       synonyms, description, source_citation)
                    VALUES ('yoga', %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (entity_class, canonical_id) DO NOTHING
                """, (
                    cid,
                    y["name_en"],
                    y["name_sa"],
                    _yoga_synonyms(y),
                    y["significations_text"][:150],
                    _yoga_citation(y),
                ))
                if cur.rowcount > 0:
                    ontology_inserted += 1
            except Exception as exc:
                warnings.append(f"ontology insert failed for {cid}: {exc}")
                logger.warning("[l0_yogas] ontology insert failed for %s: %s", cid, exc)

            # ── 3. reference_yogas pointer ──────────────────────────────────
            try:
                cur.execute("""
                    INSERT INTO reference_yogas (canonical_id, name_en, category)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (canonical_id) DO NOTHING
                """, (cid, y["name_en"], y["category"]))
                if cur.rowcount > 0:
                    ref_inserted += 1
            except Exception as exc:
                warnings.append(f"reference_yogas insert failed for {cid}: {exc}")
                logger.warning("[l0_yogas] reference_yogas insert failed for %s: %s", cid, exc)

            if (i + 1) % 50 == 0:
                logger.info("[l0_yogas] progress: %d/%d yogas processed", i + 1, len(all_yogas))

    if autocommit:
        conn.commit()

    logger.info("[l0_yogas] DONE: catalog=%d ontology=%d ref=%d (inline=%d extracted=%d) warnings=%d",
                catalog_inserted, ontology_inserted, ref_inserted,
                len(YOGAS_CORE), len(extracted), len(warnings))

    return {
        "catalog_inserted": catalog_inserted,
        "ontology_inserted": ontology_inserted,
        "ref_inserted": ref_inserted,
        "total_rows": catalog_inserted,
        "inline_count": len(YOGAS_CORE),
        "extracted_count": len(extracted),
        "warnings": warnings,
    }


def check_volume(conn) -> dict:
    """Check actual vs floor for brahma_yoga_catalog."""
    floor = len(YOGAS_CORE)  # minimum guaranteed (inline only)
    with conn.cursor() as cur:
        try:
            cur.execute("SELECT COUNT(*) FROM brahma_yoga_catalog")
            actual = cur.fetchone()['count']
        except Exception:
            actual = 0
    status = "green" if actual >= floor else ("amber" if actual > 0 else "empty")
    return {"brahma_yoga_catalog": {"actual": actual, "floor": floor, "status": status}}
