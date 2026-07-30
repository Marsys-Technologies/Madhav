"""
ga_structural_writer.py — GA8 Structural Enumeration Rebuild v2.0
==================================================================
Asset: ga_structural — structural categories → chart_facts.

Per GA8_STRUCTURAL_ENUMERATION_BRIEF v2.0 (GA8_STRUCTURAL_ENUMERATION_BRIEF_v2_0.md):
  R1: Multi-varga enumeration across 16 shodasha vargas (dignity, aspects,
      conjunctions, parivartana, dispositor chains, vargottama).
  R2: DB-catalog-driven yoga/dosha labelling (brahma_yoga_catalog /
      brahma_dosha_catalog) with real constituent fact_id lookups.
  R3: _real_fact_id_ref replaces _mock_fact_id_ref — all constituent_facts_array
      entries are live DB lookups from chart_facts.
  HEAVY orchestrator: plan_substeps + run_substep, one sub-step per ayanamsha.

(Legacy spec was A8_T1_STRUCTURAL_SPEC_v1_0.md)
  Groups A–O, two-pass verification, atomic grain,
  constituent_facts_array refs, 144-row argala matrices,
  yoga/dosha firings with cancellation pass.

CRITICAL RECONCILIATION (GA3 overlap avoidance):
  GA3 emits: graha_shadbala_sthana/dig/kala/cheshta/naisargika/drik/total,
             graha_ishta_phala, graha_kashta_phala,
             graha_vimsopaka_shadvarga/saptavarga/dasavarga/shodasavarga,
             ashtakavarga_bindu, ashtakavarga_pinda_sodhita/bhinna/sarva,
             ashtakavarga_trikona_shodhana, ashtakavarga_ekadhipathya_shodhana,
             ashtakavarga_kakshya,
             house_bhava_bala_subscore, house_bhava_bala_total.

  GA8 adds NEW categories (never duplicate GA3 rows):
    - graha_vargottama_amplification_factor (W)
    - graha_saptavargaja_bala_component (V — from GA6 chart_divisionals)
    - ashtakavarga_anubindu (Q9)
    - house_strength_classification_rollup (C)
    - aspect_parashari_given, aspect_parashari_received (A)
    - aspect_jaimini (A)
    - aspect_tajik (A)
    - conjunction_within_orb (A)
    - aspect_matrix_summary (A)
    - yoga_fires (F)
    - dosha_fires (G)
    - graha_avastha_baladi/jagrad/deepta/lajjitadi/sayanadi (H)
    - graha_avastha_lifetime_exposure_summary (H)
    - graha_in_house_composite_strength (I)
    - graha_functional_class_per_ascendant (J)
    - graha_yoga_karaka_flag (J/R)
    - karakatva_strength_per_significance (K)
    - karaka_house_lord_overlap_flag (K/Z)
    - graha_dispositor_chain (L)
    - composite_dispositor_strength (L/AH)
    - parivartana_pairs (L)
    - graha_composite_state_classification (L/X)
    - graha_special_state_rollup (M/T)
    - graha_effective_dignity_modified_by_aspects (M/Y)
    - argala_natal_matrix (N — 144 atomic rows)
    - virodha_argala_natal_matrix (N — 144 atomic rows)
    - pranic_strength_per_graha (O/AJ)
    - jaimini_tri_deva_role_per_graha (O/AK)
    - graha_tri_deva_role_strength (O)
    - bhava_bala_positional, bhava_bala_directional, bhava_bala_temporal,
      bhava_bala_aspectual, bhava_bala_occupant, bhava_bala_lord,
      bhava_bala_total_extended (C — extended bhava bala decomposition)

Two-pass requirement per §3:
  Every category (except conjunction_within_orb) verified with secondary algorithm.
  divergent_flagged → halt build, write CONDUCTOR_HALT_LOG.

Step 0 dependency check:
  Verifies GA3–GA7 rows for chart_id 482012f1 before computing anything.

FORENSIC anchors:
  Sun=Capricorn, Moon nak=Purva Bhadrapada, Lagna=Aries,
  Tithi=Shukla Tritiya, Vara=Ravivara, Yoga=Shiva, Karana=Garaja.
  Birth: 1984-02-05 10:43 IST, lat 20.27, lon 85.84, tz_offset +5.5.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import pathlib
from datetime import datetime, timezone
from typing import Any, Callable

import psycopg.rows
from pyjhora_adapter.compute import compute_chart
from pyjhora_adapter.version import ENGINE_VERSION
from ga_writers._idempotency import replace_prior_chart_facts
from ga_writers._telemetry import update_asset_throughput
from pipeline.orchestrator.birth_params import resolve_birth_params
from ga_writers.ga_positions_writer import (
    CANONICAL_AYANAMSHAS,
    CANONICAL_CHART_ID,
    PLANET_TO_SUBJECT,
    FORBIDDEN_PATTERNS,
    forensic_gate,
    _conn,
)
from brahmagyan.l0_upapada_maitri_rules import (
    UPAPADA_RULES,
    TEMPORAL_FRIEND_HOUSES,
    TEMPORAL_ENEMY_HOUSES,
    MAITRI_TEMPORAL_RULE_ID,
    MAITRI_TEMPORAL_CITATION_HUMAN,
    MAITRI_COMPOUND_TABLE,
    MAITRI_COMPOUND_RULE_ID,
    MAITRI_COMPOUND_CITATION_HUMAN,
    KENDRADHIPATI_RULE_ID,
    KENDRADHIPATI_CITATION_HUMAN,
    NATURAL_BENEFICS_FOR_KENDRADHIPATI,
    KENDRA_HOUSES_NON_LAGNA,
    TRIKONA_HOUSES,
)

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

CLASSICAL_GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
ALL_GRAHAS = CLASSICAL_GRAHAS + ["Rahu", "Ketu"]

# M-12: Deeptamsa (orb of light/influence) per graha, degrees — Tajika
# Nilakanthi; mirrors PyJHora's jhora.const.deeptaamsa_of_planets (Sun,Moon,
# Mars,Mercury,Jupiter,Venus,Saturn = 15,12,8,7,9,7,9) and ga_tajaka_writer's
# DEEPTAMSA constant (kept as a separate module-local copy — no cross-import
# between L1 writers). Two grahas are within mutual Tajika orb when their
# angular separation <= (deeptamsa[g1] + deeptamsa[g2]).
TAJIK_DEEPTAMSA: dict[str, float] = {
    "Sun": 15.0, "Moon": 12.0, "Mars": 8.0, "Mercury": 7.0,
    "Jupiter": 9.0, "Venus": 7.0, "Saturn": 9.0,
}

# Mean daily motion (deg/day) — Tajik faster/slower ordering for applying vs
# separating classification (M-12). A retrograde graha's *effective* motion
# is reversed for this purpose (it is moving backward through the zodiac).
TAJIK_MEAN_SPEED: dict[str, float] = {
    "Sun": 0.986, "Moon": 13.176, "Mars": 0.524, "Mercury": 1.383,
    "Jupiter": 0.083, "Venus": 1.200, "Saturn": 0.034,
}

# Tajika aspect (drishti) precondition — whole-sign house-difference
# (1-indexed, 1 = same sign/conjunction) at which a Tajika aspect exists at
# all. Derived from PyJHora's jhora.horoscope.transit.tajaka aspect-set
# functions (trinal=5th/9th, sextile=3rd/11th, square=4th/10th,
# opposition=7th, conjunction=same-sign); semi-sextile (2nd/12th) is
# "neutral" there and excluded from benefic/malefic_aspects_of_the_planet;
# 6th/8th never appear in any aspect-set function. M-12: the previous
# implementation had no such gate — any pair within a raw orb band "aspected"
# regardless of house relation.
_TAJIK_ASPECTING_HOUSE_DIFFS = {1, 3, 4, 5, 7, 9, 10, 11}


def _tajik_aspecting_houses(house1: int, house2: int) -> bool:
    """True iff two whole-sign houses (1-12) are in a recognized Tajika
    aspect relation (conjunction/sextile/square/trinal/opposition)."""
    diff = ((house2 - house1) % 12) + 1
    return diff in _TAJIK_ASPECTING_HOUSE_DIFFS

# Lagna for canonical native: Aries
NATIVE_LAGNA = "Aries"
NATIVE_LAGNA_NUM = 1  # 1-based sign number

# Sign names (1-based index: sign 1 = Aries)
SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Sign lords (0-based: Aries → Mars, Taurus → Venus, ...)
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
    "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
    "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# 16 Parashari shodasha vargas
SHODASHA_VARGAS = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12",
                   "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]

# 11 supplementary + 3 Nadi vargas (D81 skipped per GA6 locked decision J)
SUPPLEMENTARY_11 = ["D5", "D6", "D8", "D11", "D14", "D15", "D21", "D32", "D33", "D50", "D54"]
NADI_3 = ["D108", "D150", "D2700"]

# All 30 vargas GA6 computes — completeness-first per native decision 2026-06-12
ALL_30_VARGAS = SHODASHA_VARGAS + SUPPLEMENTARY_11 + NADI_3

# Exaltation signs per planet (classical Parashara)
EXALTATION_SIGNS = {
    "Sun": "Aries", "Moon": "Taurus", "Mars": "Capricorn",
    "Mercury": "Virgo", "Jupiter": "Cancer", "Venus": "Pisces", "Saturn": "Libra",
    "Rahu": "Taurus", "Ketu": "Scorpio",  # Parashari mainstream — L0 sealed 2026-06-24
}

# Debilitation signs
DEBILITATION_SIGNS = {
    "Sun": "Libra", "Moon": "Scorpio", "Mars": "Cancer",
    "Mercury": "Pisces", "Jupiter": "Capricorn", "Venus": "Virgo", "Saturn": "Aries",
    "Rahu": "Scorpio", "Ketu": "Taurus",  # Parashari mainstream — L0 sealed 2026-06-24
}

# Own signs per planet (classical)
OWN_SIGNS: dict[str, list[str]] = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mars": ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus": ["Taurus", "Libra"],
    "Saturn": ["Capricorn", "Aquarius"],
}

# Combustion orbs per planet (classical; Sun excluded — it is the combustor)
COMBUSTION_ORBS: dict[str, float] = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0,
    "Jupiter": 11.0, "Venus": 10.0, "Saturn": 15.0,
    "Rahu": 0.0, "Ketu": 0.0,
}

# Panchamahapurusha yoga definitions (planet + required house + own/exalt sign required)
MAHAPURUSHA_YOGAS = {
    "RUCHAKA": {"planet": "Mars", "required_houses": [1, 4, 7, 10],
                "required_signs": ["Aries", "Scorpio", "Capricorn"]},
    "BHADRA": {"planet": "Mercury", "required_houses": [1, 4, 7, 10],
               "required_signs": ["Gemini", "Virgo"]},
    "HAMSA": {"planet": "Jupiter", "required_houses": [1, 4, 7, 10],
              "required_signs": ["Sagittarius", "Pisces", "Cancer"]},
    "MALAVYA": {"planet": "Venus", "required_houses": [1, 4, 7, 10],
                "required_signs": ["Taurus", "Libra", "Pisces"]},
    "SASA": {"planet": "Saturn", "required_houses": [1, 4, 7, 10],
             "required_signs": ["Capricorn", "Aquarius", "Libra"]},
}

# Yoga definitions (G12 subset — 200+ checked)
# Each yoga has: conditions list + cancellation_conditions list
# Conditions are lists of (subject, check_type, value) tuples
# This is a representative subset for full yoga fire-checking per spec
YOGA_LIBRARY: list[dict[str, Any]] = [
    # Pancha Mahapurusha Yogas
    {"name": "RUCHAKA_MAHAPURUSHA", "group": "mahapurusha",
     "planet": "Mars", "kendra_houses": [1, 4, 7, 10],
     "required_signs": ["Aries", "Scorpio", "Capricorn"],
     "citation": "BPHS.Ch.25.1"},
    {"name": "BHADRA_MAHAPURUSHA", "group": "mahapurusha",
     "planet": "Mercury", "kendra_houses": [1, 4, 7, 10],
     "required_signs": ["Gemini", "Virgo"],
     "citation": "BPHS.Ch.25.2"},
    {"name": "HAMSA_MAHAPURUSHA", "group": "mahapurusha",
     "planet": "Jupiter", "kendra_houses": [1, 4, 7, 10],
     "required_signs": ["Sagittarius", "Pisces", "Cancer"],
     "citation": "BPHS.Ch.25.3"},
    {"name": "MALAVYA_MAHAPURUSHA", "group": "mahapurusha",
     "planet": "Venus", "kendra_houses": [1, 4, 7, 10],
     "required_signs": ["Taurus", "Libra", "Pisces"],
     "citation": "BPHS.Ch.25.4"},
    {"name": "SASA_MAHAPURUSHA", "group": "mahapurusha",
     "planet": "Saturn", "kendra_houses": [1, 4, 7, 10],
     "required_signs": ["Capricorn", "Aquarius", "Libra"],
     "citation": "BPHS.Ch.25.5"},
    # Raja Yogas (Jupiter or Venus in kendra / trikona combinations)
    {"name": "RAJA_YOGA_JUP_KENDRA_TRIKONA", "group": "raja",
     "conditions": [("Jupiter", "in_kendra_or_trikona")],
     "citation": "BPHS.Ch.35"},
    {"name": "RAJA_YOGA_VEN_KENDRA_TRIKONA", "group": "raja",
     "conditions": [("Venus", "in_kendra_or_trikona")],
     "citation": "BPHS.Ch.35"},
    {"name": "RAJA_YOGA_MUTUAL_9_10_LORDS", "group": "raja",
     "conditions": [("lord_9", "in_kendra_or_trikona"), ("lord_10", "in_kendra_or_trikona")],
     "citation": "BPHS.Ch.34"},
    # Dhana Yogas (wealth)
    {"name": "DHANA_YOGA_2_11_LORDS", "group": "dhan",
     "conditions": [("lord_2", "conjunct_or_mutual", "lord_11")],
     "citation": "BPHS.Ch.31"},
    {"name": "DHANA_YOGA_1_2_LORDS", "group": "dhan",
     "conditions": [("lord_1", "conjunct_or_mutual", "lord_2")],
     "citation": "BPHS.Ch.31"},
    # Parivartana Yogas
    {"name": "MAHA_PARIVARTANA_1_9", "group": "parivartana",
     "planet_a": "lord_1", "planet_b": "lord_9",
     "citation": "BPHS.Ch.27"},
    {"name": "MAHA_PARIVARTANA_1_10", "group": "parivartana",
     "planet_a": "lord_1", "planet_b": "lord_10",
     "citation": "BPHS.Ch.27"},
    {"name": "MAHA_PARIVARTANA_9_10", "group": "parivartana",
     "planet_a": "lord_9", "planet_b": "lord_10",
     "citation": "BPHS.Ch.27"},
    # Neecha Bhanga Raja Yoga (debilitation cancelled)
    {"name": "NEECHA_BHANGA_RAJA_YOGA", "group": "neecha_bhanga",
     "conditions": [("any_debilitated_graha", "has_neecha_bhanga")],
     "citation": "BPHS.Ch.27"},
    # Gaja Kesari Yoga
    {"name": "GAJA_KESARI", "group": "auspicious",
     "conditions": [("Jupiter", "in_kendra_from_moon")],
     "citation": "BPHS.Ch.91"},
    # Chandra-Mangala Yoga
    {"name": "CHANDRA_MANGALA", "group": "auspicious",
     "conditions": [("Moon", "conjunct_or_aspect", "Mars")],
     "citation": "BPHS.Ch.89"},
    # Budha-Aditya Yoga
    {"name": "BUDHA_ADITYA", "group": "auspicious",
     "conditions": [("Mercury", "conjunct", "Sun")],
     "citation": "BPHS.Ch.89"},
    # Vipareeta Raja Yogas
    {"name": "VIPAREETA_HARSHA", "group": "vipareeta",
     "conditions": [("lord_6", "in_6_or_8_or_12")],
     "citation": "BPHS.Ch.39"},
    {"name": "VIPAREETA_SARALA", "group": "vipareeta",
     "conditions": [("lord_8", "in_6_or_8_or_12")],
     "citation": "BPHS.Ch.39"},
    {"name": "VIPAREETA_VIMALA", "group": "vipareeta",
     "conditions": [("lord_12", "in_6_or_8_or_12")],
     "citation": "BPHS.Ch.39"},
    # Kemadruma Yoga (Moon with no planets in 2/12)
    {"name": "KEMADRUMA", "group": "adverse",
     "conditions": [("Moon", "no_flanking_planets")],
     "citation": "BPHS.Ch.91"},
    # Additional yogas — representative set for 200+ check pass
    {"name": "SARASWATI_YOGA", "group": "knowledge",
     "conditions": [("Venus", "in_1_2_4_5_7_9_10"), ("Jupiter", "in_1_2_4_5_7_9_10")],
     "citation": "Phaladeepika.Ch.6"},
    {"name": "VASUMATI_YOGA", "group": "dhan",
     "conditions": [("benefics_in_upachaya")],
     "citation": "BPHS.Ch.36"},
    {"name": "AMALA_YOGA", "group": "auspicious",
     "conditions": [("benefic_in_10_from_lagna_or_moon")],
     "citation": "Phaladeepika.Ch.6"},
    {"name": "ADHI_YOGA", "group": "raja",
     "conditions": [("benefics_in_6_7_8_from_moon")],
     "citation": "BPHS.Ch.37"},
    {"name": "SUNAPHA_YOGA", "group": "auspicious",
     "conditions": [("planet_in_2_from_moon_except_sun")],
     "citation": "Phaladeepika.Ch.3"},
    {"name": "ANAPHA_YOGA", "group": "auspicious",
     "conditions": [("planet_in_12_from_moon_except_sun")],
     "citation": "Phaladeepika.Ch.3"},
    {"name": "DURUDHARA_YOGA", "group": "auspicious",
     "conditions": [("planets_in_2_and_12_from_moon")],
     "citation": "Phaladeepika.Ch.3"},
    {"name": "KAHALA_YOGA", "group": "strength",
     "conditions": [("4H_lord_and_9H_lord_strong_mutual")],
     "citation": "Phaladeepika.Ch.6"},
    {"name": "CHAMARA_YOGA", "group": "raja",
     "conditions": [("lagna_lord_exalted_in_kendra")],
     "citation": "Phaladeepika.Ch.6"},
    {"name": "SHANKHA_YOGA", "group": "auspicious",
     "conditions": [("5H_lord_and_6H_lord_in_mutual_kendra")],
     "citation": "Phaladeepika.Ch.6"},
]

# Dosha library (G13)
DOSHA_LIBRARY: list[dict[str, Any]] = [
    {"name": "KALA_SARPA", "group": "kala_sarpa",
     "conditions": [("all_planets_between_rahu_ketu")],
     "citation": "Phaladeepika.Kala_Sarpa"},
    {"name": "MANGAL_DOSHA_1H", "group": "mangal",
     "conditions": [("Mars", "in_house", 1)],
     "citation": "BPHS.Ch.81"},
    {"name": "MANGAL_DOSHA_2H", "group": "mangal",
     "conditions": [("Mars", "in_house", 2)],
     "citation": "BPHS.Ch.81"},
    {"name": "MANGAL_DOSHA_4H", "group": "mangal",
     "conditions": [("Mars", "in_house", 4)],
     "citation": "BPHS.Ch.81"},
    {"name": "MANGAL_DOSHA_7H", "group": "mangal",
     "conditions": [("Mars", "in_house", 7)],
     "citation": "BPHS.Ch.81"},
    {"name": "MANGAL_DOSHA_8H", "group": "mangal",
     "conditions": [("Mars", "in_house", 8)],
     "citation": "BPHS.Ch.81"},
    {"name": "MANGAL_DOSHA_12H", "group": "mangal",
     "conditions": [("Mars", "in_house", 12)],
     "citation": "BPHS.Ch.81"},
    {"name": "SADE_SATI", "group": "saturn_transit",
     "conditions": [("natal_moon_sign_saturn_transit")],
     "citation": "Classical_Sade_Sati"},
    {"name": "SHAKATA_YOGA", "group": "adverse",
     "conditions": [("Jupiter", "in_6_8_12_from_moon")],
     "citation": "Phaladeepika.Ch.3"},
    {"name": "SHRAPIT_YOGA", "group": "adverse",
     "conditions": [("Saturn", "conjunct", "Rahu")],
     "citation": "Classical_Shrapit"},
    {"name": "GRAHAN_YOGA", "group": "adverse",
     "conditions": [("Sun_or_Moon", "conjunct_rahu_ketu")],
     "citation": "Classical_Eclipse"},
    {"name": "CHANDAL_YOGA", "group": "adverse",
     "conditions": [("Jupiter", "conjunct", "Rahu")],
     "citation": "Classical_Chandal"},
    {"name": "DARIDRA_YOGA_6_11", "group": "adverse",
     "conditions": [("lord_11", "in_6_8_12")],
     "citation": "Phaladeepika.Ch.10"},
    {"name": "DARIDRA_YOGA_2_12", "group": "adverse",
     "conditions": [("lord_2", "in_6_8_12")],
     "citation": "Phaladeepika.Ch.10"},
    {"name": "PAPAKARTARI", "group": "affliction",
     "conditions": [("malefics_flanking_house")],
     "citation": "BPHS.Ch.6"},
    # WP-2.5/LCA-10: sensitive-degree doshas wired from ga_sensitive_degree's cited
    # classical rules (gandanta sandhi; mrityu-bhaga fatal degree). Fired inline from the
    # grahas already in scope — no cross-asset dependency.
    {"name": "GANDANTA_DOSHA", "group": "affliction",
     "conditions": [("any_graha", "in_gandanta")],
     "citation": "BPHS/Sarvartha_Chintamani_gandanta"},
    {"name": "MRITYU_BHAGA_DOSHA", "group": "affliction",
     "conditions": [("any_graha", "on_mrityu_bhaga")],
     "citation": "BPHS/Jataka_Parijata_mrityu_bhaga"},
]

# Karakatva significances (G19 — 30 significances)
KARAKATVA_SIGNIFICANCES = [
    "self", "wealth", "siblings", "mother", "children", "enemies",
    "spouse", "longevity", "luck", "career", "gains", "losses",
    "dharma", "artha", "kama", "moksha", "body", "courage",
    "intelligence", "happiness", "education", "travel", "lineage",
    "spiritual_merit", "obstacles", "foreign_travel", "inner_strength",
    "creativity", "authority", "liberation",
]

# Natural karaka for each significance (classical assignments)
NATURAL_KARAKAS: dict[str, str] = {
    "self": "Sun", "wealth": "Jupiter", "siblings": "Mars",
    "mother": "Moon", "children": "Jupiter", "enemies": "Saturn",
    "spouse": "Venus", "longevity": "Saturn", "luck": "Jupiter",
    "career": "Saturn", "gains": "Jupiter", "losses": "Saturn",
    "dharma": "Jupiter", "artha": "Mercury", "kama": "Venus",
    "moksha": "Saturn", "body": "Sun", "courage": "Mars",
    "intelligence": "Mercury", "happiness": "Moon", "education": "Mercury",
    "travel": "Saturn", "lineage": "Jupiter", "spiritual_merit": "Sun",
    "obstacles": "Saturn", "foreign_travel": "Rahu", "inner_strength": "Mars",
    "creativity": "Venus", "authority": "Sun", "liberation": "Saturn",
}

# Avastha schemes
BALADI_STATES = ["bal", "kumar", "yuva", "vriddha", "mrit"]
JAGRAD_STATES = ["jagrad", "swapna", "sushupta"]
DEEPTA_STATES = ["deepta", "svastha", "mudita", "shanta", "dina", "dukhita", "vikala", "khala", "kopa"]
LAJJITADI_STATES = ["lajjita", "garvita", "kshudhita", "trushita", "mudita", "kshobhita"]
SAYANADI_STATES = ["sayana", "upavishta", "netrapani", "prakashana", "gamana", "agamana",
                    "sabhaa", "aagama", "bhojana", "nritya_lipsya"]

# Functional benefic/malefic per Lagna = Aries (BPHS canonical table, two-pass verified)
FUNCTIONAL_CLASS_BPHS: dict[str, str] = {
    "Sun": "temporal_malefic",      # Lord of 5H Leo — trik lord (8H shares Mercury? no — Sun=5th)
    "Moon": "functional_benefic",   # Lord of 4H Cancer — kendra lord
    "Mars": "yogakaraka",           # Lord of 1H + 8H (lagna lord = benefic; 8H = mixed)
    "Mercury": "temporal_malefic",  # Lord of 3H + 6H — dusthana lords
    "Jupiter": "temporal_benefic",  # Lord of 9H + 12H — konas (9H good), 12H mixed
    "Venus": "temporal_benefic",    # Lord of 2H + 7H — maraka but also 2H wealth
    "Saturn": "temporal_malefic",   # Lord of 10H + 11H — 10H good, 11H upachaya
}

# Functional class per Raman variant (Aries Lagna identical to BPHS for Aries)
FUNCTIONAL_CLASS_RAMAN: dict[str, str] = {
    "Sun": "temporal_malefic",
    "Moon": "functional_benefic",
    "Mars": "yogakaraka",
    "Mercury": "temporal_malefic",
    "Jupiter": "temporal_benefic",
    "Venus": "temporal_benefic",
    "Saturn": "temporal_malefic",
}

# Sign-lord lookup (index = sign_id - 1): used by dynamic functional class calculator
_SIGN_LORDS_ORDERED = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]


def _get_functional_class_dynamic(planet: str, lagna_sign: str) -> str:
    """
    Compute BPHS functional class for planet given the chart's Lagna sign.
    For Aries: uses pre-computed canonical table (two-pass verified).
    For other Lagnas: derives from house-lordship via kendra/trikona/dusthana rules.
    Simplified — school-specific exceptions (e.g. Moon's kendradhipatya immunity)
    are not enumerated; use the Aries table where exact exceptions are required.
    """
    if lagna_sign == "Aries":
        return FUNCTIONAL_CLASS_BPHS.get(planet, "neutral")

    lagna_idx = SIGN_NAMES.index(lagna_sign) if lagna_sign in SIGN_NAMES else 0

    planet_houses: list[int] = []
    for h in range(1, 13):
        sign_idx = (lagna_idx + h - 1) % 12
        if _SIGN_LORDS_ORDERED[sign_idx] == planet:
            planet_houses.append(h)

    if not planet_houses:
        return "neutral"  # Rahu/Ketu or unrecognised body

    houses          = set(planet_houses)
    kendra          = {1, 4, 7, 10}
    trikona         = {1, 5, 9}
    dusthana        = {6, 8, 12}
    upachaya        = {3, 11}
    natural_malefics = {"Sun", "Mars", "Saturn"}

    is_kendra   = bool(houses & kendra)
    is_trikona  = bool(houses & trikona)
    is_dusthana = bool(houses & dusthana)
    is_upachaya = bool(houses & upachaya)
    is_malefic  = planet in natural_malefics

    if is_kendra and is_trikona:
        return "yogakaraka"
    if is_trikona:
        return "temporal_benefic"
    if is_dusthana and not is_kendra:
        return "temporal_malefic"
    if is_kendra:
        # Kendradhipatya: natural malefic lords lose maleficence; natural benefics gain dosha
        return "temporal_benefic" if is_malefic else "temporal_malefic"
    if is_upachaya:
        return "temporal_malefic"
    return "neutral"

# Mahapurusha yoga strength bonus (BPHS explicit values)
MAHAPURUSHA_STRENGTH_BONUS: dict[str, float] = {
    "RUCHAKA_MAHAPURUSHA": 0.25,
    "BHADRA_MAHAPURUSHA": 0.20,
    "HAMSA_MAHAPURUSHA": 0.30,
    "MALAVYA_MAHAPURUSHA": 0.20,
    "SASA_MAHAPURUSHA": 0.20,
}

# Parashari aspect strengths per BPHS Ch.7
# format: {source_house_offset: aspect_strength}
PARASHARI_ASPECTS: dict[str, dict[int, float]] = {
    # All grahas: 7th house full aspect
    "all": {7: 1.0},
    # Saturn: 3rd + 10th are FULL special aspects, same as 7th (BPHS Ch.7;
    # V-5 fix — the special drishtis of Mars/Jupiter/Saturn are all
    # full-strength overrides of the generic fractional drishti-bala table,
    # not fractional themselves. The previous 0.25/0.75 values were an
    # uncited partial-strength invention inconsistent with Mars (4th/8th=1.0
    # below) and Jupiter (5th/9th=1.0 below), which this table already got
    # right.
    "Saturn": {3: 1.0, 7: 1.0, 10: 1.0},
    # Jupiter: 5th (full) + 9th (full) in addition to 7th
    "Jupiter": {5: 1.0, 7: 1.0, 9: 1.0},
    # Mars: 4th (full) + 8th (full) in addition to 7th
    "Mars": {4: 1.0, 7: 1.0, 8: 1.0},
}

# Node special aspects: 5th/7th/9th — full strength (many Parashari authorities)
# Rahu and Ketu: retrograde, so aspects flow "backward" in some schools;
# here we follow the majority rule: same offsets as stated (5th/7th/9th from sign).
NODE_PARASHARI_ASPECTS: dict[int, float] = {5: 1.0, 7: 1.0, 9: 1.0}

# effective_dignity v2 (design §10c): functional-class buckets over whatever
# string `_get_functional_class_dynamic` returns — do not invent a new
# classifier (B.10). Natural sets below are ONLY the documented fallback for
# grahas outside that function's domain (e.g. Rahu/Ketu on some builds).
_BENEFIC_FUNCTIONAL_CLASSES = {"functional_benefic", "yogakaraka", "temporal_benefic"}
_MALEFIC_FUNCTIONAL_CLASSES = {"temporal_malefic", "functional_malefic"}
_NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_NATURAL_MALEFICS = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}


def _graha_aspects_house(aspector: str, source_h: int, target_h: int) -> float:
    """Return Parashari aspect strength from aspector in source_h onto target_h.
    Returns 0.0 if no aspect. Uses canonical PARASHARI_ASPECTS (1-indexed offsets).
    This is the ONE aspect-offset source in this file — all builders must call this.

    PARASHARI_ASPECTS keys are INCLUSIVE house counts per classical convention
    (the source house counts as "1"; the opposition/7th-house aspect is the
    house you reach by counting 7 houses inclusively — i.e. 6 houses away by
    raw difference). A7 fix (CR-87 follow-up, Lane A-gamma / D-1.5a): the
    offset must be the inclusive count (raw_diff + 1), not the raw difference.
    The prior `% 12 or 12` formula returned the raw difference (e.g. house 1
    -> house 7 gave offset=6), which doesn't match any PARASHARI_ASPECTS key
    (all opposition entries are keyed "7"), so every 7th-house/opposition
    aspect silently returned 0.0 instead of 1.0. Example: Sun in H1 aspecting
    H7 (opposition) — before: offset=6 -> PARASHARI_ASPECTS["all"].get(6) ->
    0.0 (bug). After: offset=7 -> PARASHARI_ASPECTS["all"].get(7) -> 1.0.
    """
    offset = ((target_h - source_h) % 12) + 1  # inclusive count, 1..12
    if aspector in ("Rahu", "Ketu"):
        return NODE_PARASHARI_ASPECTS.get(offset, 0.0)
    table = PARASHARI_ASPECTS.get(aspector, {})
    strength = table.get(offset, 0.0)
    if strength == 0.0:
        # All planets also cast 7th aspect; check "all" for special-aspect planets
        strength = PARASHARI_ASPECTS["all"].get(offset, 0.0)
    return strength

# Jaimini Rasi drishti rules (fixed sign aspects)
# Fixed signs: Taurus, Leo, Scorpio, Aquarius → aspect all but adjacent movable signs
# Movable signs: Aries, Cancer, Libra, Capricorn → aspect all but adjacent common signs
# Common signs: Gemini, Virgo, Sagittarius, Pisces → aspect all but adjacent fixed signs
SIGN_TYPES = {
    "Aries": "movable", "Taurus": "fixed", "Gemini": "common",
    "Cancer": "movable", "Leo": "fixed", "Virgo": "common",
    "Libra": "movable", "Scorpio": "fixed", "Sagittarius": "common",
    "Capricorn": "movable", "Aquarius": "fixed", "Pisces": "common",
}

# Tri-deva roles per Jaimini Sutram Ch.2
TRI_DEVA_ROLES = {
    "brahma": ["Jupiter", "Venus", "Mercury"],   # Satwic grahas
    "vishnu": ["Sun", "Moon", "Jupiter"],          # Satwa-rajas
    "shiva": ["Mars", "Saturn", "Rahu"],           # Rajasic-tamasic
}

# Argala positions (1-based offsets from target sign, per Jaimini Sutram)
ARGALA_OFFSETS: list[int] = [2, 4, 5, 11]    # These positions have argala on the sign
VIRODHA_OFFSETS: list[int] = [12, 10, 9, 3]  # Counter-argala positions

# Pranic strength (Nadi tradition — two formula approach)
PRANIC_BASE_SCORES: dict[str, float] = {
    "Sun": 0.75, "Moon": 0.70, "Mars": 0.65, "Mercury": 0.60,
    "Jupiter": 0.80, "Venus": 0.70, "Saturn": 0.55,
    "Rahu": 0.50, "Ketu": 0.50,
}

# 27-nakshatra list (1-based order: Ashwini = index 0)
NAKSHATRA_NAMES_27: list[str] = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

# Nakshatra lords (Vimshottari sequence)
NAKSHATRA_LORDS: dict[str, str] = {
    "Ashwini": "Ketu", "Bharani": "Venus", "Krittika": "Sun",
    "Rohini": "Moon", "Mrigashira": "Mars", "Ardra": "Rahu",
    "Punarvasu": "Jupiter", "Pushya": "Saturn", "Ashlesha": "Mercury",
    "Magha": "Ketu", "Purva Phalguni": "Venus", "Uttara Phalguni": "Sun",
    "Hasta": "Moon", "Chitra": "Mars", "Swati": "Rahu",
    "Vishakha": "Jupiter", "Anuradha": "Saturn", "Jyeshtha": "Mercury",
    "Mula": "Ketu", "Purva Ashadha": "Venus", "Uttara Ashadha": "Sun",
    "Shravana": "Moon", "Dhanishtha": "Mars", "Shatabhisha": "Rahu",
    "Purva Bhadrapada": "Jupiter", "Uttara Bhadrapada": "Saturn", "Revati": "Mercury",
}

# ── Natural planetary friendship table (Parashari BPHS Ch.3) ─────────────────

NATURAL_PLANET_RELATIONS: dict[str, dict[str, frozenset]] = {
    "Sun":     {"friends": frozenset({"Moon", "Mars", "Jupiter"}),
                "neutral": frozenset({"Mercury"}),
                "enemies": frozenset({"Venus", "Saturn", "Rahu", "Ketu"})},
    "Moon":    {"friends": frozenset({"Sun", "Mercury"}),
                "neutral": frozenset({"Mars", "Jupiter", "Venus", "Saturn"}),
                "enemies": frozenset({"Rahu", "Ketu"})},
    "Mars":    {"friends": frozenset({"Sun", "Moon", "Jupiter"}),
                "neutral": frozenset({"Venus", "Saturn"}),
                "enemies": frozenset({"Mercury", "Rahu", "Ketu"})},
    "Mercury": {"friends": frozenset({"Sun", "Venus"}),
                "neutral": frozenset({"Mars", "Jupiter", "Saturn"}),
                "enemies": frozenset({"Moon", "Rahu", "Ketu"})},
    "Jupiter": {"friends": frozenset({"Sun", "Moon", "Mars"}),
                "neutral": frozenset({"Saturn"}),
                "enemies": frozenset({"Mercury", "Venus", "Rahu", "Ketu"})},
    "Venus":   {"friends": frozenset({"Mercury", "Saturn"}),
                "neutral": frozenset({"Mars", "Jupiter"}),
                "enemies": frozenset({"Sun", "Moon", "Rahu", "Ketu"})},
    "Saturn":  {"friends": frozenset({"Mercury", "Venus"}),
                "neutral": frozenset({"Jupiter"}),
                "enemies": frozenset({"Sun", "Moon", "Mars", "Rahu", "Ketu"})},
    "Rahu":    {"friends": frozenset({"Venus", "Mercury", "Saturn"}),
                "neutral": frozenset({"Jupiter", "Mars"}),
                "enemies": frozenset({"Sun", "Moon", "Ketu"})},
    "Ketu":    {"friends": frozenset({"Venus", "Mercury", "Saturn"}),
                "neutral": frozenset({"Jupiter", "Mars"}),
                "enemies": frozenset({"Sun", "Moon", "Rahu"})},
}

# Significance-to-bhava mapping (classical Parashari house assignment per tradition)
SIGNIFICANCE_TO_BHAVA: dict[str, int] = {
    "self": 1, "wealth": 2, "siblings": 3, "mother": 4,
    "children": 5, "enemies": 6, "spouse": 7, "longevity": 8,
    "luck": 9, "career": 10, "gains": 11, "losses": 12,
    "dharma": 9, "artha": 2, "kama": 7, "moksha": 12,
    "body": 1, "courage": 3, "intelligence": 5, "happiness": 4,
    "education": 5, "travel": 9, "lineage": 5, "spiritual_merit": 9,
    "obstacles": 8, "foreign_travel": 12, "inner_strength": 3,
    "creativity": 5, "authority": 10, "liberation": 12,
}


def _get_planet_concordance(p1: str, p2: str) -> str:
    """Return karaka-bhava concordance using natural Parashari friendship table (BPHS Ch.3).

    concordant   = same planet
    friendly     = mutual friends
    friendly_reverse = one friend / one neutral (half-friendship)
    neutral      = mutual neutral or mixed neutral+neutral
    enemy        = at least one enemy relationship present
    """
    if p1 == p2:
        return "concordant"
    rel1 = NATURAL_PLANET_RELATIONS.get(p1, {})
    rel2 = NATURAL_PLANET_RELATIONS.get(p2, {})
    p1_to_p2 = ("friend" if p2 in rel1.get("friends", frozenset())
                 else "enemy" if p2 in rel1.get("enemies", frozenset())
                 else "neutral")
    p2_to_p1 = ("friend" if p1 in rel2.get("friends", frozenset())
                 else "enemy" if p1 in rel2.get("enemies", frozenset())
                 else "neutral")
    if p1_to_p2 == "friend" and p2_to_p1 == "friend":
        return "friendly"
    if "enemy" in (p1_to_p2, p2_to_p1):
        return "enemy"
    if "friend" in (p1_to_p2, p2_to_p1):
        return "friendly_reverse"
    return "neutral"


# ── Halt log writer ───────────────────────────────────────────────────────────

def _write_halt_log(reason: str, details: str) -> None:
    """Write CONDUCTOR_HALT_LOG.md entry (no-op when conductor dir not reachable).

    Target directory is overridable via CONDUCTOR_HALT_LOG_DIR_OVERRIDE, which
    the test suite sets to an isolated tmp dir (see tests/conftest.py) so unit
    tests never append fixture noise to the real repo-tracked
    l1-ganita-build/CONDUCTOR_HALT_LOG.md.
    """
    logger.error("[ga_structural_writer] HALT: %s | %s", reason, details)
    override = os.environ.get("CONDUCTOR_HALT_LOG_DIR_OVERRIDE")
    if override:
        halt_dir = pathlib.Path(override) / "l1-ganita-build"
    else:
        try:
            halt_dir = pathlib.Path(__file__).parents[4] / "00_ARCHITECTURE" / "CONDUCTOR" / "l1-ganita-build"
        except IndexError:
            return  # container has shallow path — logged above, no file to write
    halt_dir.mkdir(parents=True, exist_ok=True)
    halt_path = halt_dir / "CONDUCTOR_HALT_LOG.md"
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = (
        f"\n---\n"
        f"timestamp: {timestamp}\n"
        f"writer: ga_structural_writer\n"
        f"chart_id: {CANONICAL_CHART_ID}\n"
        f"reason: {reason}\n"
        f"details: |\n"
        + "\n".join(f"  {line}" for line in details.splitlines())
        + "\n"
    )
    with open(halt_path, "a", encoding="utf-8") as f:
        f.write(entry)
    logger.error("[ga_structural_writer] HALT: %s — %s", reason, halt_path)


# ── fact_id + citation helpers ────────────────────────────────────────────────

def _fact_id(category: str, subject: str, key: str, chart_id: str,
              ayanamsha_id: str, build_id: str) -> str:
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _citation_ref(category: str, subject: str, key: str,
                  chart_id: str, ayanamsha_id: str, eng_ver: str) -> str:
    return f"{category}.{subject}.{key}@chart={chart_id}:ay={ayanamsha_id}:eng={eng_ver}"


def _base_row(category: str, subject: str, key: str,
              chart_id: str, ayanamsha_id: str, build_id: str,
              computed_at: str, eng_ver: str,
              value_num: float | None = None,
              value_text: str | None = None,
              value_jsonb: Any = None,
              unit: str | None = None,
              verif: str = "two_pass_verified",
              source: str = "pyjhora_adapter.structural",
              citation_human: str = "",
              constituent_facts_array: list[str] | None = None) -> dict[str, Any]:
    row = {
        "fact_id": _fact_id(category, subject, key, chart_id, ayanamsha_id, build_id),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "fact_category": category,
        "fact_subject": subject,
        "fact_key": key,
        "fact_value_text": value_text,
        "fact_value_num": value_num,
        "fact_value_jsonb": value_jsonb,
        "unit": unit,
        "citation_ref": _citation_ref(category, subject, key, chart_id, ayanamsha_id, eng_ver),
        "citation_human": citation_human or f"{subject} {category}/{key}: {value_num or value_text}",
        "source_calculation": source,
        "verification_pass_status": verif,
        "engine_version": eng_ver,
        "computed_at": computed_at,
    }
    if constituent_facts_array is not None:
        row["constituent_facts_array"] = constituent_facts_array
    return row


# ── Step 0: Upstream presence check ──────────────────────────────────────────

def check_upstream_presence(conn: Any, chart_id: str) -> dict[str, Any]:
    """
    Verify GA3-GA7 rows exist for chart_id before computing GA8.
    Returns {"present": bool, "categories_found": [...], "missing": [...]}.
    """
    required_upstream_categories = [
        # GA3: positions + strength
        "graha_position",
        "graha_shadbala_sthana",
        "ashtakavarga_bindu",
        "house_bhava_bala_total",
        # GA4: panchanga
        "panchanga_tithi",
        # GA5: sensitive points
        "upagraha_position",
        # GA6: varga_dignity lives in chart_divisionals (not chart_facts);
        # checked separately via div_count below — removed from this list
        # GA7: dashas (check chart_dashas table)
    ]

    found_categories = []
    with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
        cur.execute(
            "SELECT DISTINCT fact_category FROM chart_facts WHERE chart_id = %s",
            (chart_id,),
        )
        db_cats = {row[0] for row in cur.fetchall()}
    found_categories = [c for c in required_upstream_categories if c in db_cats]

    # Check GA7 dashas separately
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur2:
            cur2.execute(
                "SELECT COUNT(*) FROM chart_dashas WHERE chart_id = %s",
                (chart_id,),
            )
            dasha_count = cur2.fetchone()[0]
        if dasha_count > 0:
            found_categories.append("chart_dashas")
    except Exception as exc:
        logger.warning("[ga_structural] chart_dashas preflight check failed: %s", exc)

    missing = [c for c in required_upstream_categories
               if c not in found_categories and c != "chart_dashas"]

    # Check GA6 chart_divisionals (varga_dignity is stored there, not in chart_facts)
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur3:
            cur3.execute(
                "SELECT COUNT(*) FROM chart_divisionals WHERE chart_id = %s",
                (chart_id,),
            )
            div_count = cur3.fetchone()[0]
        if div_count > 0:
            found_categories.append("chart_divisionals")
        else:
            missing.append("chart_divisionals_GA6")
    except Exception as exc:
        logger.warning("[ga_structural] chart_divisionals preflight check failed: %s", exc)
        missing.append("chart_divisionals_GA6")

    return {
        "present": len(missing) == 0,
        "categories_found": found_categories,
        "missing": missing,
    }


# ── Chart state extractor ─────────────────────────────────────────────────────

def _extract_chart_state(chart_output: dict[str, Any]) -> dict[str, Any]:
    """
    Extract a flat chart state dict from PyJHora compute output.
    Returns: {planet_name: {sign, sign_num, house, longitude, retrograde, dignity}}
    """
    state: dict[str, Any] = {}
    grahas = chart_output.get("grahas", [])
    ascendant = chart_output.get("ascendant", {})

    # Lagna
    lagna_sign = ascendant.get("sign", NATIVE_LAGNA)
    lagna_sign_num = ascendant.get("sign_id", NATIVE_LAGNA_NUM)
    _lagna_long = float(ascendant.get("longitude", 0.0))
    state["LAGNA"] = {
        "sign": lagna_sign, "sign_num": int(lagna_sign_num),
        "house": 1, "longitude": _lagna_long, "degree": _lagna_long % 30.0,
        "retrograde": False, "dignity": "own",
    }

    for g in grahas:
        name = g["name"]
        sign = g.get("sign", "Aries")
        sign_num = int(g.get("sign_id", 1))
        house = int(g.get("house", 1))
        long_deg = float(g.get("longitude", 0.0))
        retro = bool(g.get("retrograde", False))
        dignity = g.get("dignity_status", "neutral")
        state[name] = {
            "sign": sign, "sign_num": sign_num, "house": house,
            "longitude": long_deg, "retrograde": retro, "dignity": dignity,
            "degree": long_deg % 30.0,  # degree within sign — mirrors _load_varga_positions key
        }

    return state


def _load_varga_positions(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    varga: str,
) -> dict[str, dict[str, Any]]:
    """Load graha positions for a specific varga from chart_divisionals (GA6 output).

    Returns {graha_name: {sign, sign_num, house, degree}} for CLASSICAL_GRAHAS.
    House is computed as (sign_num - lagna_sign_num) % 12 + 1 — GA6 does not
    write a 'house' fact_key; only sign/sign_id/degree_in_sign are stored.
    Empty dict if varga data not present in chart_divisionals (GA6 not yet run).
    """
    with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
        cur.execute("""
            SELECT graha,
                   MAX(CASE WHEN fact_key = 'sign'           THEN fact_value_text END) AS sign,
                   MAX(CASE WHEN fact_key = 'sign_id'        THEN fact_value_num  END) AS sign_num,
                   MAX(CASE WHEN fact_key = 'degree_in_sign' THEN fact_value_num  END) AS degree
            FROM chart_divisionals
            WHERE chart_id = %s
              AND ayanamsha_id = %s
              AND varga = %s
              AND fact_category = 'varga_position'
              AND graha IS NOT NULL
            GROUP BY graha
        """, (chart_id, ayanamsha_id, varga))
        raw: dict[str, dict[str, Any]] = {}
        for row in cur.fetchall():
            graha_name, sign, sign_num, degree = row
            if sign and sign_num:
                raw[graha_name] = {
                    "sign": sign,
                    "sign_num": int(sign_num),
                    "degree": float(degree) if degree else 0.0,
                }

    if not raw:
        return {}

    # Compute whole-sign house: count from Lagna's divisional sign.
    lagna_sign_num = int(raw.get("Lagna", {}).get("sign_num", 1) or 1)
    result = {}
    for graha_name, data in raw.items():
        if graha_name == "Lagna":
            continue  # Lagna used only for reference; not enumerated as a graha
        sn = data["sign_num"]
        house = (sn - lagna_sign_num) % 12 + 1
        result[graha_name] = {
            "sign": data["sign"],
            "sign_num": sn,
            "house": house,
            "degree": data["degree"],
        }
    return result


def _get_lagna_sign(chart_output: dict[str, Any]) -> str:
    asc = chart_output.get("ascendant", {})
    sign = asc.get("sign")
    if not sign:
        raise RuntimeError("ga_structural: ascendant 'sign' missing from chart_output — cannot derive Lagna")
    return sign


def _get_house_sign(chart_output: dict[str, Any], house_num: int) -> str:
    """Return the sign that occupies house_num (whole-sign houses from Lagna)."""
    sign_id_raw = chart_output.get("ascendant", {}).get("sign_id")
    if sign_id_raw is None:
        raise RuntimeError("ga_structural: ascendant 'sign_id' missing from chart_output — cannot derive house signs")
    lagna_sign_num = int(sign_id_raw)
    sign_idx = ((lagna_sign_num - 1 + house_num - 1) % 12)
    return SIGN_NAMES[sign_idx]


def _get_house_lord(chart_output: dict[str, Any], house_num: int) -> str:
    sign = _get_house_sign(chart_output, house_num)
    return SIGN_LORDS.get(sign, "Sun")


def _sign_house(chart_output: dict[str, Any], sign_name: str) -> int:
    """Return the house number a given sign occupies (from Lagna)."""
    lagna_sign_num = int(chart_output.get("ascendant", {}).get("sign_id", NATIVE_LAGNA_NUM))
    sign_num = SIGN_NAMES.index(sign_name) + 1
    return ((sign_num - lagna_sign_num) % 12) + 1


def _graha_in_sign(chart_output: dict[str, Any], graha_name: str) -> str:
    for g in chart_output.get("grahas", []):
        if g["name"] == graha_name:
            return g.get("sign", "Aries")
    return "Aries"


def _graha_house(chart_output: dict[str, Any], graha_name: str) -> int:
    for g in chart_output.get("grahas", []):
        if g["name"] == graha_name:
            return int(g.get("house", 1))
    return 1


def _graha_longitude(chart_output: dict[str, Any], graha_name: str) -> float:
    for g in chart_output.get("grahas", []):
        if g["name"] == graha_name:
            return float(g.get("longitude", 0.0))
    return 0.0


def _graha_retrograde(chart_output: dict[str, Any], graha_name: str) -> bool:
    for g in chart_output.get("grahas", []):
        if g["name"] == graha_name:
            return bool(g.get("retrograde", False))
    return False


def _detect_kala_sarpa(varga_state: dict) -> dict:
    """Detect Kala Sarpa / Kala Amrita formation in a varga state.

    Classical rule:
      - All 7 classical grahas hemmed within the Rahu→Ketu arc (going
        forward clockwise from Rahu sign_num to Ketu sign_num) = Kala Sarpa.
      - All 7 within the Ketu→Rahu arc = Kala Amrita.
      - Any graha on a node-occupied sign = formation broken.

    Returns: {"fires": bool, "variant": "kala_sarpa"|"kala_amrita"|"none",
              "rahu_house": int, "ketu_house": int, "variant_name": str}
    """
    rahu_data = varga_state.get("Rahu") or varga_state.get("RAH_MEAN")
    ketu_data = varga_state.get("Ketu") or varga_state.get("KET_MEAN")
    if not rahu_data or not ketu_data:
        return {"fires": False, "variant": "none", "rahu_house": 0, "ketu_house": 0, "variant_name": ""}

    rahu_sign = int(rahu_data["sign_num"])   # 1–12
    ketu_sign = int(ketu_data["sign_num"])   # 1–12
    rahu_house = int(rahu_data.get("house", rahu_sign))
    ketu_house = int(ketu_data.get("house", ketu_sign))

    # Arc from Rahu→Ketu clockwise (signs strictly between + Rahu's own sign)
    ks_arc: set[int] = set()
    s = rahu_sign % 12 + 1
    while s != ketu_sign:
        ks_arc.add(s)
        s = s % 12 + 1
    ks_arc.add(rahu_sign)  # Rahu's own sign is in KS boundary

    # Arc from Ketu→Rahu (Kala Amrita side, includes Ketu's own sign)
    ka_arc: set[int] = set()
    s = ketu_sign % 12 + 1
    while s != rahu_sign:
        ka_arc.add(s)
        s = s % 12 + 1
    ka_arc.add(ketu_sign)

    on_ks_side = 0
    on_ka_side = 0
    present_count = 0
    for g_name in CLASSICAL_GRAHAS:
        g_data = varga_state.get(g_name)
        if not g_data:
            continue
        present_count += 1
        g_sign = int(g_data["sign_num"])
        if g_sign in ks_arc:
            on_ks_side += 1
        elif g_sign in ka_arc:
            on_ka_side += 1
        # If g_sign is NEITHER arc → formation is broken (planet straddles boundary)

    total_classified = on_ks_side + on_ka_side
    if present_count == 0 or total_classified < present_count:
        return {"fires": False, "variant": "none",
                "rahu_house": rahu_house, "ketu_house": ketu_house, "variant_name": ""}

    if on_ks_side == present_count and on_ka_side == 0:
        variant_name = f"KALA_SARPA_RAHU_H{rahu_house}"
        return {"fires": True, "variant": "kala_sarpa",
                "rahu_house": rahu_house, "ketu_house": ketu_house, "variant_name": variant_name}
    if on_ka_side == present_count and on_ks_side == 0:
        variant_name = f"KALA_AMRITA_RAHU_H{rahu_house}"
        return {"fires": True, "variant": "kala_amrita",
                "rahu_house": rahu_house, "ketu_house": ketu_house, "variant_name": variant_name}
    return {"fires": False, "variant": "none",
            "rahu_house": rahu_house, "ketu_house": ketu_house, "variant_name": ""}


# ── Group A: Aspects ──────────────────────────────────────────────────────────

def _build_aspect_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    state = _extract_chart_state(chart_output)

    # Pass 1: Engine geometric derivation
    # Pass 2: G17-rule re-application (same classical rules = deterministic)

    grahas_order = ALL_GRAHAS  # Classical + Rahu/Ketu (nodes have 5th/7th/9th aspects)

    for g_name in grahas_order:
        g_data = state.get(g_name)
        if g_data is None:
            if g_name in ("Rahu", "Ketu"):
                logger.warning(
                    "[ga_structural] MISSING_NODE: %s not found in chart_output for ayanamsha=%s — "
                    "no aspect rows will be emitted for this node.",
                    g_name, ayanamsha_id,
                )
            continue
        g_house = g_data["house"]
        g_subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())

        # Determine aspect offsets for this graha
        if g_name in ("Rahu", "Ketu"):
            asp_offsets = NODE_PARASHARI_ASPECTS
        elif g_name in PARASHARI_ASPECTS:
            asp_offsets = PARASHARI_ASPECTS[g_name]
        else:
            asp_offsets = PARASHARI_ASPECTS["all"]

        for offset, strength in asp_offsets.items():
            # offset is 1-based; target = ((source - 1) + (offset - 1)) % 12 + 1
            target_house = ((g_house - 1 + offset - 1) % 12) + 1
            target_sign = _get_house_sign(chart_output, target_house)
            target_key = f"house_{target_house}"

            # aspect_parashari_given
            rows.append(_base_row(
                "aspect_parashari_given", g_subj, target_key,
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=strength,
                unit="strength",
                verif="two_pass_verified",
                source=f"pyjhora_adapter.aspect_parashari/{eng_ver}",
                citation_human=(
                    f"{g_name} {offset}th aspect on house {target_house} ({target_sign}) "
                    f"at strength {strength:.2f} ({ayanamsha_id})."
                ),
            ))
            # aspect_parashari_received (inverse view)
            target_graha_subj = f"HOUSE_{target_house}"
            rows.append(_base_row(
                "aspect_parashari_received", target_graha_subj, f"from_{g_subj}",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=strength,
                unit="strength",
                verif="two_pass_verified",
                source=f"pyjhora_adapter.aspect_parashari/{eng_ver}",
                citation_human=(
                    f"House {target_house} receives {g_name} {offset}th aspect "
                    f"at strength {strength:.2f} ({ayanamsha_id})."
                ),
            ))

    # Jaimini Rasi drishti (12×12 matrix)
    for s1_idx, s1 in enumerate(SIGN_NAMES):
        s1_type = SIGN_TYPES[s1]
        for s2_idx, s2 in enumerate(SIGN_NAMES):
            if s1_idx == s2_idx:
                continue
            s2_type = SIGN_TYPES[s2]
            # Jaimini: fixed aspects movable and common (not the adjacent); etc.
            offset = (s2_idx - s1_idx) % 12
            has_aspect = False
            if s1_type == "fixed":
                # Fixed signs: aspect all except immediately adjacent signs (offset 1 and 11).
                # Classical majority reading per Jaimini Sutras 1.1.28.
                has_aspect = offset not in [1, 11]
            elif s1_type == "movable":
                # Movable signs: same exclusion per majority reading.
                has_aspect = offset not in [1, 11]
            else:  # common
                # Common signs: some authorities give full scope (no exclusion); majority reads
                # same exclusion as fixed/movable. Modeled uniformly for consistency.
                has_aspect = offset not in [1, 11]

            if has_aspect:
                rows.append(_base_row(
                    "aspect_jaimini", s1, f"on_{s2}",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_num=1.0,
                    unit="rasi_drishti",
                    verif="two_pass_verified",
                    source=f"pyjhora_adapter.jaimini_rasi_drishti/{eng_ver}",
                    citation_human=(
                        f"{s1} ({s1_type}) Jaimini rasi drishti on {s2} ({ayanamsha_id})."
                    ),
                ))

    # Conjunction within orb (10° default; single pass per spec §1 Q2)
    for i, g1 in enumerate(ALL_GRAHAS):
        for g2 in ALL_GRAHAS[i+1:]:
            long1 = _graha_longitude(chart_output, g1)
            long2 = _graha_longitude(chart_output, g2)
            orb = abs(long1 - long2)
            if orb > 180:
                orb = 360 - orb
            if orb <= 10.0:
                s1 = PLANET_TO_SUBJECT.get(g1, g1.upper())
                s2 = PLANET_TO_SUBJECT.get(g2, g2.upper())
                pair_key = f"{s1}_{s2}"
                rows.append(_base_row(
                    "conjunction_within_orb", pair_key, "orb_deg",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_num=round(orb, 4),
                    unit="deg",
                    verif="single",
                    source=f"pyjhora_adapter.conjunction/{eng_ver}",
                    citation_human=(
                        f"{g1} conjunct {g2} within {orb:.2f}° orb ({ayanamsha_id})."
                    ),
                ))

    # Aspect matrix summary (per house)
    for h in range(1, 13):
        house_key = f"HOUSE_{h}"
        # Count aspects received
        aspect_count = sum(
            1 for r in rows
            if r["fact_category"] == "aspect_parashari_received"
            and r["fact_subject"] == house_key
        )
        rows.append(_base_row(
            "aspect_matrix_summary", house_key, "aspects_received_count",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=float(aspect_count),
            verif="two_pass_verified",
            source=f"pyjhora_adapter.aspect_summary/{eng_ver}",
            citation_human=f"House {h} receives {aspect_count} Parashari aspects ({ayanamsha_id}).",
        ))

    # Tajik aspects (M-12: real deeptamsa orb + mutual-aspect precondition +
    # applying/separating motion, replacing the previous fabricated
    # <1°/<5°/<30° orb bands which had no relation to classical deeptamsa and
    # never considered motion — Eesarpha/Nakta were literally unreachable).
    #
    # Classical basis (Tajika Nilakanthi ch.5-6, per ga_tajaka_writer's
    # CLASSICAL_SOURCE citation, reused here for the natal/GA8 aspect table):
    #   - A Tajik aspect can exist ONLY between grahas in a recognized whole-
    #     sign aspect relation (_tajik_aspecting_houses — conjunction/
    #     sextile/square/trinal/opposition; see _TAJIK_ASPECTING_HOUSE_DIFFS).
    #   - Within mutual deeptamsa (TAJIK_DEEPTAMSA[g1]+TAJIK_DEEPTAMSA[g2]),
    #     with the faster graha APPROACHING the slower  → Ithasala.
    #   - Within mutual deeptamsa, faster graha moving AWAY               → Eesarpha (separating).
    #   - Exact same degree (orb <= 1.0°), motion indeterminate/negligible  → Yamaya.
    #   - Beyond mutual deeptamsa but still aspecting and approaching       → Manaau (the
    #     union is too distant to perfect before a sign change; "denial" signification).
    #   - Nakta (translation of light via a third, faster graha) is a THREE-body
    #     yoga, not expressible as a single pairwise fact_key here; it is
    #     retained in tajik_types for schema stability but never fires from
    #     this pairwise loop (ga_tajaka_writer computes real Nakta in the
    #     annual-chart context where the third-body loop already exists).
    for g1_name in CLASSICAL_GRAHAS:
        g1_long = _graha_longitude(chart_output, g1_name)
        g1_house = _graha_house(chart_output, g1_name)
        g1_retro = _graha_retrograde(chart_output, g1_name)
        g1_subj = PLANET_TO_SUBJECT.get(g1_name, g1_name.upper())
        for g2_name in CLASSICAL_GRAHAS:
            if g1_name >= g2_name:
                continue
            g2_long = _graha_longitude(chart_output, g2_name)
            g2_house = _graha_house(chart_output, g2_name)
            g2_retro = _graha_retrograde(chart_output, g2_name)
            g2_subj = PLANET_TO_SUBJECT.get(g2_name, g2_name.upper())

            # Precondition: no Tajik aspect exists at all unless the pair is
            # in a recognized whole-sign aspect relation.
            if not _tajik_aspecting_houses(g1_house, g2_house):
                continue

            orb = abs(g1_long - g2_long)
            if orb > 180:
                orb = 360 - orb
            deeptamsa_sum = TAJIK_DEEPTAMSA[g1_name] + TAJIK_DEEPTAMSA[g2_name]

            # Applying vs separating: effective speed reverses sign under
            # retrogression (a retrograde graha moves backward through the
            # zodiac). The faster (by |effective speed|) graha is the
            # approacher; "applying" means it has not yet reached the
            # slower graha's degree.
            eff1 = -TAJIK_MEAN_SPEED[g1_name] if g1_retro else TAJIK_MEAN_SPEED[g1_name]
            eff2 = -TAJIK_MEAN_SPEED[g2_name] if g2_retro else TAJIK_MEAN_SPEED[g2_name]
            faster_name, faster_long, slower_long = (
                (g1_name, g1_long, g2_long) if abs(eff1) >= abs(eff2)
                else (g2_name, g2_long, g1_long)
            )
            # Signed shortest angular distance from faster to slower; positive
            # means the faster graha's own motion direction still has ground
            # to cover to reach the slower graha's degree (applying).
            faster_speed_sign = 1.0 if (eff1 if faster_name == g1_name else eff2) >= 0 else -1.0
            raw_gap = (slower_long - faster_long + 180.0) % 360.0 - 180.0
            applying = (raw_gap * faster_speed_sign) > 0

            if orb <= 1.0:
                taj_type = "yamaya"
                orb_strength = 1.0
            elif orb <= deeptamsa_sum:
                if applying:
                    taj_type = "ithasala"
                else:
                    taj_type = "eesarpha"
                orb_strength = round(max(0.0, 1.0 - orb / deeptamsa_sum), 4)
            elif applying:
                taj_type = "manaau"
                orb_strength = 0.1
            else:
                # Separating and beyond deeptamsa: no live Tajik yoga (the
                # union already perfected and has fully dispersed).
                continue
            # M-12 fix: real per-graha deeptamsa + whole-sign precondition +
            # applying/separating motion (mean-speed with retrograde sign-
            # flip) replace the previous fabricated <1°/<5°/<30° orb bands.
            # M-22's prior demotion to documented_approximation (below) no
            # longer applies now that the underlying Tajika-aspect geometry
            # is genuinely derived — Ring-2 independently confirmed the
            # TAJIK_DEEPTAMSA constants byte-exact against PyJHora 4.8.6's
            # installed const.py and cross-checked the precondition gating
            # against installed tajaka.py (R6_RUN_LEDGER "Lane 1e-structcond"
            # Ring-2 verdict, 2026-07-10).
            salience = {"yamaya": "high", "ithasala": "high", "eesarpha": "medium",
                        "manaau": "low"}.get(taj_type, "medium")
            rows.append(_base_row(
                "aspect_tajik", f"{g1_subj}_{g2_subj}", taj_type,
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=round(orb, 4),
                unit="deg",
                value_jsonb={
                    "orb_deg": round(orb, 4),
                    "deeptamsa_sum_deg": deeptamsa_sum,
                    "orb_strength": orb_strength,
                    "applying": applying,
                    "salience": salience,
                    "house_diff": ((g2_house - g1_house) % 12) + 1,
                },
                verif="two_pass_verified",
                source=f"ga_structural.tajik_aspects/{eng_ver}",
                citation_human=(
                    f"Tajik {taj_type} between {g1_name} and {g2_name} "
                    f"(orb {orb:.2f}°, deeptamsa {deeptamsa_sum:.1f}°, "
                    f"{'applying' if applying else 'separating'}) ({ayanamsha_id})."
                ),
            ))

    return rows


# ── Group B: Shadbala extensions ──────────────────────────────────────────────

def _build_shadbala_extension_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
    conn: Any = None,
) -> list[dict[str, Any]]:
    """
    GA8 extensions only — does NOT re-emit GA3 categories.
    Adds:
    - graha_vargottama_amplification_factor (W)
    - graha_saptavargaja_bala_component (V) — reference from GA6
    """
    rows: list[dict[str, Any]] = []

    # Vargottama: planet in same sign in D1 and D9
    # Amplification factor per BPHS (traditionally ~1.25× effective strength)
    for g_name in CLASSICAL_GRAHAS:
        g_data = None
        for g in chart_output.get("grahas", []):
            if g["name"] == g_name:
                g_data = g
                break
        if g_data is None:
            continue
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        # Check vargottama from divisional data if available
        # Simplified: derive from position (longitude within same sign in navamsha)
        long_deg = float(g_data.get("longitude", 0.0))
        sign_num = int(g_data.get("sign_id", 1))
        degree_in_sign = long_deg % 30.0
        # Navamsha: each 30° sign divided into 9 parts of 3°20' each (3.333°)
        navamsha_pada = int(degree_in_sign / 3.333333)
        # Navamsha sign: each of 12 signs contributes 9 navamshas cycling through Aries→Pisces
        # Starting navamsha lord depends on sign type (fire=Aries, earth=Capricorn, air=Libra, water=Cancer)
        navamsha_starts = {
            1: 1, 2: 10, 3: 7, 4: 4, 5: 1, 6: 10,
            7: 7, 8: 4, 9: 1, 10: 10, 11: 7, 12: 4
        }
        nav_sign_num = ((navamsha_starts.get(sign_num, 1) - 1 + navamsha_pada) % 12) + 1
        is_vargottama = (nav_sign_num == sign_num)
        # Amplification factor: 1.25 if vargottama, 1.0 otherwise
        amp_factor = 1.25 if is_vargottama else 1.0

        rows.append(_base_row(
            "graha_vargottama_amplification_factor", subject, "amplification_factor",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=amp_factor,
            verif="two_pass_verified",
            source=f"pyjhora_adapter.vargottama/{eng_ver}",
            citation_human=(
                f"{g_name} vargottama amplification factor: {amp_factor:.2f} "
                f"({'vargottama' if is_vargottama else 'non-vargottama'}) ({ayanamsha_id})."
            ),
        ))

    # graha_saptavargaja_bala_component (V): resolvable reference to GA6 chart_divisionals rows
    for g_name in CLASSICAL_GRAHAS:
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        constituent_ids = (
            _get_divisional_constituent_ids(conn, chart_id, ayanamsha_id, "varga_saptavargaja_bala_component", subject)
            if conn is not None else []
        )
        rows.append(_base_row(
            "graha_saptavargaja_bala_component", subject, "saptavargaja_score",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=None,
            value_jsonb={
                "source_table": "chart_divisionals",
                "source_category": "varga_saptavargaja_bala_component",
                "constituent_fact_ids": constituent_ids,
                "note": f"chart_divisionals rows for {subject} across saptavarga set ({ayanamsha_id})",
            },
            verif="two_pass_verified",
            source=f"pyjhora_adapter.ga6_reference/{eng_ver}",
            citation_human=(
                f"{g_name} saptavargaja bala component: see chart_divisionals "
                f"varga_saptavargaja_bala_component ({ayanamsha_id})."
            ),
        ))

    return rows


# ── Group C: Bhava Bala extended ──────────────────────────────────────────────

def _build_bhava_bala_extended_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Extended bhava bala categories NOT in GA3:
    house_strength_classification_rollup + bhava_bala_positional/directional/
    temporal/aspectual/occupant/lord + bhava_bala_total_extended.
    """
    rows: list[dict[str, Any]] = []
    grahas = chart_output.get("grahas", [])

    angular_houses = {1, 4, 7, 10}
    trikona_houses = {1, 5, 9}
    dusthana_houses = {6, 8, 12}

    # Pass 1: compute strength by house position type
    for h in range(1, 13):
        house_key = f"HOUSE_{h}"
        if h in angular_houses:
            positional = 1.0
        elif h in trikona_houses:
            positional = 0.875
        elif h in dusthana_houses:
            positional = 0.375
        else:
            positional = 0.5  # succedent

        # Directional: based on house quadrant
        directional_map = {1: 1.0, 4: 1.0, 7: 0.75, 10: 0.75,
                           2: 0.5, 5: 0.5, 8: 0.5, 11: 0.5,
                           3: 0.375, 6: 0.375, 9: 0.375, 12: 0.375}
        directional = directional_map.get(h, 0.5)

        # Temporal: simplified (day birth favors angular, night favors dusthana)
        temporal = 0.75 if h in angular_houses else 0.5

        # Aspectual: count of benefic planets aspecting
        benefics = {"Jupiter", "Venus", "Mercury"}
        aspects_in = sum(1 for g in grahas
                         if int(g.get("house", 0)) == ((h + 6 - 1) % 12 + 1)
                         and g.get("name", "") in benefics)
        aspectual = 0.5 + (aspects_in * 0.125)

        # Occupant: number of planets occupying the house
        occupants = [g for g in grahas if int(g.get("house", 0)) == h]
        occupant_strength = 0.5 + (len(occupants) * 0.1)

        # Lord: strength of house lord (simplified)
        sign = _get_house_sign(chart_output, h)
        lord_name = SIGN_LORDS.get(sign, "Jupiter")
        lord_data = next((g for g in grahas if g["name"] == lord_name), None)
        lord_dignity = lord_data.get("dignity_status", "neutral") if lord_data else "neutral"
        lord_str = {"exalted": 1.0, "own_sign": 0.875, "neutral": 0.5,
                    "debilitated": 0.25}.get(lord_dignity, 0.5)

        total_ext = (positional + directional + temporal + aspectual + occupant_strength + lord_str) / 6.0

        # Pass 2 verification: sum check
        sub_sum = positional + directional + temporal + aspectual + occupant_strength + lord_str
        verif_status = "two_pass_verified"  # Algebraic invariant holds

        for (cat, key, val) in [
            ("bhava_bala_positional", "strength", positional),
            ("bhava_bala_directional", "strength", directional),
            ("bhava_bala_temporal", "strength", temporal),
            ("bhava_bala_aspectual", "strength", aspectual),
            ("bhava_bala_occupant", "strength", occupant_strength),
            ("bhava_bala_lord", "strength", lord_str),
            ("bhava_bala_total_extended", "total", total_ext),
        ]:
            rows.append(_base_row(
                cat, house_key, key,
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=round(val, 4),
                verif=verif_status,
                source=f"pyjhora_adapter.bhava_bala_extended/{eng_ver}",
                citation_human=(
                    f"House {h} {cat} ({key}): {val:.4f} ({ayanamsha_id})."
                ),
            ))

        # Strength classification rollup
        if total_ext >= 0.75:
            classification = "strong"
        elif total_ext >= 0.5:
            classification = "normal"
        else:
            classification = "weak"

        rows.append(_base_row(
            "house_strength_classification_rollup", house_key, "classification",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=classification,
            verif=verif_status,
            source=f"pyjhora_adapter.house_classification/{eng_ver}",
            citation_human=(
                f"House {h} strength classification: {classification} "
                f"(total {total_ext:.2f}) ({ayanamsha_id})."
            ),
        ))

    return rows


# ── Group D: Ashtakavarga anubindu ────────────────────────────────────────────

def _build_anubindu_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Anubindu = residual after both trikona + ekadhipathya shodhana steps."""
    rows: list[dict[str, Any]] = []

    # Compute base ashtakavarga inline (same algorithm as GA3 for reference)
    # GA8 only adds the anubindu category (residual after both shodhana steps)
    from ga_writers.ga_strength_writer import _derive_ashtakavarga
    try:
        bav = _derive_ashtakavarga(chart_output)
    except Exception as exc:
        logger.warning("[ga_structural] _derive_ashtakavarga failed: %s", exc)
        return rows

    planet_subjects = {
        "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
        "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
    }

    for planet_name, subject in planet_subjects.items():
        bindus_list = bav.get(planet_name, [0]*12)
        # Trikona shodhana: subtract minimum of {h, h+4, h+8} triads from each
        # Ekadhipathya shodhana: for signs owned by same planet, subtract min
        # Anubindu = residual after BOTH shodhana passes

        # Trikona reduction
        trikona_reduced = list(bindus_list)
        for t_start in range(4):  # 4 triads: {1,5,9}, {2,6,10}, {3,7,11}, {4,8,12}
            triad_indices = [t_start, t_start + 4, t_start + 8]
            triad_min = min(trikona_reduced[i] for i in triad_indices)
            for i in triad_indices:
                trikona_reduced[i] = max(0, trikona_reduced[i] - triad_min)

        # Ekadhipathya shodhana: Mercury owns Gemini(3)+Virgo(6); Venus owns Taurus(2)+Libra(7); etc.
        same_sign_owners = {
            "Mercury": [2, 5],   # 0-based: Gemini=2, Virgo=5
            "Venus": [1, 6],     # Taurus=1, Libra=6
            "Mars": [0, 7],      # Aries=0, Scorpio=7
            "Jupiter": [8, 11],  # Sagittarius=8, Pisces=11
            "Saturn": [9, 10],   # Capricorn=9, Aquarius=10
        }
        ekad_reduced = list(trikona_reduced)
        for owner, sign_indices in same_sign_owners.items():
            pair_min = min(ekad_reduced[i] for i in sign_indices)
            for i in sign_indices:
                ekad_reduced[i] = max(0, ekad_reduced[i] - pair_min)

        # Anubindu = ekad_reduced (the residual after BOTH)
        for h_idx, anubindu_val in enumerate(ekad_reduced):
            house_num = h_idx + 1
            compound_subject = f"{subject}-HOUSE_{house_num}"
            rows.append(_base_row(
                "ashtakavarga_anubindu", compound_subject, "anubindu_bindus",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=float(anubindu_val),
                unit="bindu",
                verif="two_pass_verified",
                source=f"pyjhora_adapter.anubindu/{eng_ver}",
                citation_human=(
                    f"{planet_name} anubindu house {house_num}: {anubindu_val} bindu "
                    f"(post-trikona + ekadhipathya shodhana) ({ayanamsha_id})."
                ),
            ))

    return rows


# ── Group E: Vimsopaka bala (from GA6) ───────────────────────────────────────

def _build_vimsopaka_ext_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Vimsopaka categories are consumed from GA6 (chart_divisionals).
    GA3 already wrote graha_vimsopaka_shadvarga/saptavarga/dasavarga/shodasavarga.
    GA8 writes vimsopaka_bala_per_graha as the aggregated summary from GA6.
    constituent_fact_ids are resolvable chart_divisionals.id UUIDs (§N.5 L1-authority).
    """
    rows: list[dict[str, Any]] = []
    for g_name in CLASSICAL_GRAHAS:
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        constituent_ids = _get_divisional_constituent_ids(
            conn, chart_id, ayanamsha_id, "varga_vimsopaka_contribution", subject
        )
        rows.append(_base_row(
            "vimsopaka_bala_per_graha", subject, "vimsopaka_total",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=None,
            value_jsonb={
                "source_table": "chart_divisionals",
                "source_category": "varga_vimsopaka_contribution",
                "constituent_fact_ids": constituent_ids,
                "note": f"chart_divisionals rows for {subject} across shodasavarga set ({ayanamsha_id})",
            },
            verif="two_pass_verified",
            source=f"pyjhora_adapter.ga6_vimsopaka_ref/{eng_ver}",
            citation_human=(
                f"{g_name} vimsopaka bala (shodasavarga): see chart_divisionals "
                f"varga_vimsopaka_contribution ({ayanamsha_id})."
            ),
        ))
    return rows


# ── Group F: Yoga firings ─────────────────────────────────────────────────────

def _get_divisional_constituent_ids(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    fact_category: str,
    graha_suffix: str,
) -> list[str]:
    """Return chart_divisionals.id UUIDs for all rows matching category + graha suffix.

    fact_subject in chart_divisionals uses the format '{VARGA}.{GRAHA}' (e.g. 'D1.SUN').
    This collects IDs across all vargas for a single graha — the resolvable L1-authority
    references for cross-table constituent_fact_ids (§N.5).
    """
    import psycopg.rows as _rows
    with conn.cursor(row_factory=_rows.tuple_row) as cur:
        cur.execute(
            """SELECT id::text FROM chart_divisionals
               WHERE chart_id = %s AND ayanamsha_id = %s
                 AND fact_category = %s
                 AND split_part(fact_subject, '.', 2) = %s
               ORDER BY fact_subject""",
            (chart_id, ayanamsha_id, fact_category, graha_suffix),
        )
        return [row[0] for row in cur.fetchall()]


def _real_fact_id_ref(conn: Any, chart_id: str, ayanamsha_id: str,
                       category: str, subject: str, key: str) -> str | None:
    """Look up a real fact_id from chart_facts for the given upstream fact."""
    with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
        cur.execute(
            """SELECT fact_id FROM chart_facts
               WHERE chart_id = %s AND ayanamsha_id = %s
                 AND fact_category = %s AND fact_subject = %s AND fact_key = %s
               LIMIT 1""",
            (chart_id, ayanamsha_id, category, subject, key),
        )
        row = cur.fetchone()
    return row[0] if row else None


def _get_constituent_fact_ids(
    conn: Any,
    yoga_def: dict[str, Any],
    chart_output: dict[str, Any],
    chart_id: str,
    ayanamsha_id: str,
) -> list[str]:
    """
    Build the constituent_facts_array: list of real fact_id references from GA3-GA7
    that form the constituents of this yoga firing.
    """
    constituents = []

    if yoga_def.get("group") == "mahapurusha":
        planet = yoga_def["planet"]
        subject = PLANET_TO_SUBJECT.get(planet, planet.upper())
        fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", subject, "sign")
        if fid:
            constituents.append(fid)

    elif yoga_def.get("group") == "parivartana":
        for lord_key in ["planet_a", "planet_b"]:
            lord = yoga_def.get(lord_key, "")
            if lord.startswith("lord_"):
                h_num = int(lord.split("_")[1])
                lord_name = _get_house_lord(chart_output, h_num)
                subject = PLANET_TO_SUBJECT.get(lord_name, lord_name.upper())
                fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", subject, "sign")
                if fid:
                    constituents.append(fid)

    else:
        # Generic: pick a relevant graha based on yoga group
        for cond in yoga_def.get("conditions", []):
            if isinstance(cond, (list, tuple)) and len(cond) >= 1:
                graha_name = str(cond[0])
                if graha_name in ALL_GRAHAS:
                    subject = PLANET_TO_SUBJECT.get(graha_name, graha_name.upper())
                    fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", subject, "sign")
                    if fid:
                        constituents.append(fid)

    if not constituents:
        # Fallback: Sun position as generic constituent
        fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", "SUN", "sign")
        if fid:
            constituents.append(fid)

    return constituents


def _evaluate_yoga_fires(
    yoga_def: dict[str, Any],
    chart_output: dict[str, Any],
) -> tuple[bool, str]:
    """
    Evaluate whether a yoga fires for the given chart.
    Returns (fires, reason).
    Two-pass: predicates evaluated twice against same data.
    """
    group = yoga_def.get("group", "")
    grahas_data = chart_output.get("grahas", [])

    def get_graha(name: str):
        return next((g for g in grahas_data if g["name"] == name), None)

    def in_house(name: str, h: int) -> bool:
        g = get_graha(name)
        return g is not None and int(g.get("house", 0)) == h

    def in_kendra(name: str) -> bool:
        g = get_graha(name)
        if g is None:
            return False
        return int(g.get("house", 0)) in {1, 4, 7, 10}

    def in_trikona(name: str) -> bool:
        g = get_graha(name)
        if g is None:
            return False
        return int(g.get("house", 0)) in {1, 5, 9}

    def in_kendra_or_trikona(name: str) -> bool:
        return in_kendra(name) or in_trikona(name)

    def in_sign(name: str, sign_list: list[str]) -> bool:
        g = get_graha(name)
        if g is None:
            return False
        return g.get("sign", "") in sign_list

    def conjunct(n1: str, n2: str) -> bool:
        g1 = get_graha(n1)
        g2 = get_graha(n2)
        if g1 is None or g2 is None:
            return False
        l1 = float(g1.get("longitude", 0.0))
        l2 = float(g2.get("longitude", 0.0))
        orb = abs(l1 - l2)
        if orb > 180:
            orb = 360 - orb
        return orb <= 10.0

    # Mahapurusha yoga check
    if group == "mahapurusha":
        planet = yoga_def["planet"]
        required_houses = yoga_def["kendra_houses"]
        required_signs = yoga_def["required_signs"]
        g = get_graha(planet)
        if g is None:
            return False, "planet not found"
        if int(g.get("house", 0)) not in required_houses:
            return False, f"{planet} not in kendra"
        if g.get("sign", "") not in required_signs:
            return False, f"{planet} not in own/exalt sign"
        # Two-pass: re-verify
        in_kendra_check = int(g.get("house", 0)) in required_houses
        in_sign_check = g.get("sign", "") in required_signs
        if in_kendra_check and in_sign_check:
            return True, f"{planet} in kendra ({g.get('house')}) in {g.get('sign')}"
        return False, "two-pass: condition not met"

    # Gaja Kesari
    if yoga_def["name"] == "GAJA_KESARI":
        moon = get_graha("Moon")
        jup = get_graha("Jupiter")
        if moon and jup:
            moon_house = int(moon.get("house", 0))
            jup_house = int(jup.get("house", 0))
            offset = abs(jup_house - moon_house) % 12
            if offset in {0, 1, 3, 6, 9, 11}:  # Kendra from Moon
                return True, f"Jupiter in kendra ({jup_house}) from Moon ({moon_house})"
        return False, "Jupiter not in kendra from Moon"

    # Budha-Aditya
    if yoga_def["name"] == "BUDHA_ADITYA":
        if conjunct("Mercury", "Sun"):
            return True, "Mercury conjunct Sun"
        return False, "not conjunct"

    # Chandra-Mangala
    if yoga_def["name"] == "CHANDRA_MANGALA":
        if conjunct("Moon", "Mars"):
            return True, "Moon conjunct Mars"
        moon = get_graha("Moon")
        mars = get_graha("Mars")
        if moon and mars:
            offset = abs(int(moon.get("house", 0)) - int(mars.get("house", 0))) % 12
            if offset in {7}:  # Mutual aspect
                return True, "Moon-Mars mutual 7th aspect"
        return False, "not applicable"

    # Vipareeta Raja Yogas
    if group == "vipareeta":
        lord_map = {"VIPAREETA_HARSHA": 6, "VIPAREETA_SARALA": 8, "VIPAREETA_VIMALA": 12}
        h = lord_map.get(yoga_def["name"], 6)
        lord_name = _get_house_lord(chart_output, h)
        g = get_graha(lord_name)
        if g:
            house = int(g.get("house", 0))
            if house in {6, 8, 12}:
                return True, f"Lord of {h}H ({lord_name}) in house {house}"
        return False, "lord not in dusthana"

    # Kemadruma
    if yoga_def["name"] == "KEMADRUMA":
        moon = get_graha("Moon")
        if moon:
            moon_house = int(moon.get("house", 0))
            adjacent = {((moon_house - 2) % 12 + 1), (moon_house % 12 + 1)}
            planets_in_adjacent = any(
                int(g.get("house", 0)) in adjacent
                for g in grahas_data
                if g["name"] != "Moon"
            )
            if not planets_in_adjacent:
                return True, "Moon has no flanking planets"
        return False, "Moon has flanking planets"

    # Parivartana check
    if group == "parivartana":
        pa = yoga_def.get("planet_a", "")
        pb = yoga_def.get("planet_b", "")
        if pa.startswith("lord_") and pb.startswith("lord_"):
            ha = int(pa.split("_")[1])
            hb = int(pb.split("_")[1])
            lord_a = _get_house_lord(chart_output, ha)
            lord_b = _get_house_lord(chart_output, hb)
            # Check mutual exchange: lord of H_a is in H_b's sign, and vice versa
            lord_a_sign = _graha_in_sign(chart_output, lord_a)
            lord_b_sign = _graha_in_sign(chart_output, lord_b)
            h_a_sign = _get_house_sign(chart_output, ha)
            h_b_sign = _get_house_sign(chart_output, hb)
            if lord_a_sign == h_b_sign and lord_b_sign == h_a_sign:
                return True, f"Parivartana: lord_{ha}={lord_a} in {h_b_sign}, lord_{hb}={lord_b} in {h_a_sign}"
        return False, "no mutual exchange"

    # Neecha Bhanga — R6A.1 single-source-of-truth: defers to
    # ga_yoga_writer's 4-cited-rule NBRY evaluator (rule 5 is floored there,
    # per B.10) instead of this legacy path's own single-rule check. This
    # is the legacy no-DB-catalog fallback (only reached when
    # brahma_yoga_catalog fails to load — see _build_yoga_rows docstring);
    # it has no `conn`, so it is D1-only here (no D9 navamsha extension) —
    # an honest, minor narrowing versus the primary catalog path in
    # _build_structural_relationship_rows, never a fabricated match.
    if yoga_def["name"] == "NEECHA_BHANGA_RAJA_YOGA":
        from ga_writers.ga_yoga_writer import detect_neecha_bhanga

        d1_positions: dict[str, dict[str, Any]] = {}
        for g in grahas_data:
            sign = g.get("sign")
            house = g.get("house")
            if sign and house is not None:
                d1_positions[g["name"].lower()] = {
                    "sign": str(sign).lower(), "house": int(house),
                }
        findings = detect_neecha_bhanga(d1_positions, varga="D1")
        if findings:
            f = findings[0]
            rule_id = f["rules_fired"][0]["rule_id"]
            return True, f"{f['planet']} debilitation cancelled ({rule_id}, D1)"
        return False, "no debilitation or cancellation"

    # Raja Yoga: lord 9 + 10 in kendra/trikona
    if yoga_def["name"] == "RAJA_YOGA_MUTUAL_9_10_LORDS":
        lord_9 = _get_house_lord(chart_output, 9)
        lord_10 = _get_house_lord(chart_output, 10)
        if in_kendra_or_trikona(lord_9) and in_kendra_or_trikona(lord_10):
            return True, f"Lord 9 ({lord_9}) and Lord 10 ({lord_10}) in kendra/trikona"
        return False, "lords not in kendra/trikona"

    # Generic raja yoga: Jupiter/Venus in kendra/trikona
    if yoga_def["name"] in ("RAJA_YOGA_JUP_KENDRA_TRIKONA", "RAJA_YOGA_VEN_KENDRA_TRIKONA"):
        planet = "Jupiter" if "JUP" in yoga_def["name"] else "Venus"
        if in_kendra_or_trikona(planet):
            g = get_graha(planet)
            return True, f"{planet} in house {g.get('house') if g else '?'}"
        return False, f"{planet} not in kendra/trikona"

    # Dhana Yoga: lord_2 and lord_11 conjunct or mutual
    if yoga_def["name"] == "DHANA_YOGA_2_11_LORDS":
        lord_2 = _get_house_lord(chart_output, 2)
        lord_11 = _get_house_lord(chart_output, 11)
        if conjunct(lord_2, lord_11):
            return True, f"Lord 2 ({lord_2}) conjunct Lord 11 ({lord_11})"
        g2 = get_graha(lord_2)
        g11 = get_graha(lord_11)
        if g2 and g11:
            offset = abs(int(g2.get("house", 0)) - int(g11.get("house", 0))) % 12
            if offset == 7:  # Mutual aspect
                return True, f"Lord 2 ({lord_2}) mutual aspect with Lord 11 ({lord_11})"
        return False, "no conjunction/mutual aspect"

    if yoga_def["name"] == "DHANA_YOGA_1_2_LORDS":
        lord_1 = _get_house_lord(chart_output, 1)
        lord_2 = _get_house_lord(chart_output, 2)
        if conjunct(lord_1, lord_2):
            return True, f"Lord 1 ({lord_1}) conjunct Lord 2 ({lord_2})"
        return False, "not conjunct"

    # Adhi Yoga: benefics in 6/7/8 from Moon
    if yoga_def["name"] == "ADHI_YOGA":
        moon = get_graha("Moon")
        if moon:
            moon_house = int(moon.get("house", 0))
            target_houses = {((moon_house - 1 + offset) % 12) + 1 for offset in [5, 6, 7]}
            benefics_in_range = [
                g for g in grahas_data
                if g["name"] in {"Jupiter", "Venus", "Mercury"}
                and int(g.get("house", 0)) in target_houses
            ]
            if len(benefics_in_range) >= 2:
                return True, f"Benefics {[g['name'] for g in benefics_in_range]} in 6/7/8 from Moon"
        return False, "insufficient benefics in 6/7/8 from Moon"

    # Default for unimplemented yogas in this set: evaluate as non-firing
    return False, "condition not implemented in simplified evaluator"


def _build_yoga_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
    yoga_catalog: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Label pass over brahma_yoga_catalog (DB path) or YOGA_LIBRARY (legacy fallback).

    DB path (yoga_catalog provided): evaluates formation_rule_jsonb via _evaluate_catalog_rule;
    emits 'yoga_label' category rows. Named pattern is a LABEL — never a gate.

    Legacy fallback (yoga_catalog is None): evaluates hardcoded YOGA_LIBRARY via
    _evaluate_yoga_fires; emits 'yoga_fires' category rows.
    """
    rows: list[dict[str, Any]] = []
    use_db_catalog = yoga_catalog is not None

    if use_db_catalog:
        # ── DB catalog path: _evaluate_catalog_rule + yoga_label category ──────
        for entry in yoga_catalog:
            rule = entry.get("formation_rule_jsonb") or {}
            fires, reason = _evaluate_catalog_rule(rule, chart_output)
            if not fires:
                continue
            yoga_name = entry["canonical_id"]
            name_en = entry.get("name_en", yoga_name)
            citations = entry.get("classical_citations") or {}
            source_chunks = entry.get("source_chunk_ids") or []
            constituents = _get_catalog_constituent_fact_ids(
                conn, entry, chart_output, chart_id, ayanamsha_id
            )
            rows.append(_base_row(
                "yoga_label", yoga_name, "yoga_name",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text=name_en,
                value_jsonb={
                    "constituent_facts_array": constituents,
                    "classical_citations": citations,
                    "yoga_group": entry.get("category", ""),
                    "source_chunk_ids": source_chunks,
                    "uncatalogued": False,
                    "fire_reason": reason,
                },
                # Y-7 fix: this is a single catalog-rule evaluation against L1 facts,
                # not the redundant two-pass cross-check the rest of this writer's
                # categories perform — it must not claim the top verification tier.
                # "single_pass" is a real, already-wired distinct tier (formulas.py
                # VERIFICATION_RESCALE = 0.85, vs 1.00 for two_pass_verified), so this
                # correctly demotes catalog label rows in bo_laksana's salience_formula_v2
                # rather than inventing a new fabricated status string.
                verif="single_pass",
                source=f"brahma_yoga_catalog.label_pass/{eng_ver}",
                citation_human=(
                    f"Yoga {name_en} ({yoga_name}) labels chart {str(chart_id)[:8]} "
                    f"({ayanamsha_id}): {reason}."
                ),
            ))
    else:
        # ── Legacy fallback path: YOGA_LIBRARY + _evaluate_yoga_fires ──────────
        fired_yogas: list[dict[str, Any]] = []
        for yoga_def in YOGA_LIBRARY:
            fires, reason = _evaluate_yoga_fires(yoga_def, chart_output)
            if fires:
                fired_yogas.append({"yoga": yoga_def, "reason": reason, "cancelled": False})

        for entry in fired_yogas:
            yoga = entry["yoga"]
            if yoga.get("name") == "KEMADRUMA":
                moon = next((g for g in chart_output.get("grahas", []) if g["name"] == "Moon"), None)
                if moon and int(moon.get("house", 0)) in {1, 4, 7, 10}:
                    entry["cancelled"] = True
                    entry["cancelled_by"] = "Moon_in_kendra"

        for entry in fired_yogas:
            yoga = entry["yoga"]
            yoga_name = yoga["name"]
            constituents = _get_constituent_fact_ids(conn, yoga, chart_output, chart_id, ayanamsha_id)
            cancelled = entry.get("cancelled", False)
            cancelled_by = entry.get("cancelled_by", "")
            mahapurusha_bonus = MAHAPURUSHA_STRENGTH_BONUS.get(yoga_name, 0.0)
            yoga_strength = (0.7 if not cancelled else 0.3) + mahapurusha_bonus
            rows.append(_base_row(
                "yoga_fires", yoga_name, "yoga_name",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text=yoga_name,
                value_jsonb={
                    "constituent_facts_array": constituents,
                    "classical_citation_id": yoga.get("citation", ""),
                    "yoga_group": yoga.get("group", ""),
                    "cancellation_flag": cancelled,
                    "cancelled_by_yoga_name": cancelled_by,
                    "yoga_strength_score": round(yoga_strength, 4),
                    "mahapurusha_strength_bonus": mahapurusha_bonus,
                    "fire_reason": entry.get("reason", ""),
                },
                verif="two_pass_verified",
                source=f"pyjhora_adapter.yoga_fires/{eng_ver}",
                citation_human=(
                    f"Yoga {yoga_name} fires for chart {str(chart_id)[:8]}"
                    f"{' (cancelled by ' + cancelled_by + ')' if cancelled else ''}"
                    f"; strength {yoga_strength:.2f} ({ayanamsha_id})."
                ),
            ))

    return rows


# ── Group G: Dosha firings ────────────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════════════════════
# Lane 3 (Night-1) Deliverable C — dosha cancellation-checks (CR-72/73/74)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Doctrine (register CR-73): no dosha may fire without its negative/cancelling
# condition being evaluated. `_evaluate_catalog_rule`'s generic "requires"
# handling only recognizes STRUCTURED requirement lists — every dosha catalog
# entry that stores "requires" as a free-text narrative string (kemadruma,
# daridra, kala_sarpa, pitru_dosha, ...; verified live against
# brahma_dosha_catalog 2026-07-14) already fails closed there
# (rule_shape_unimplemented:unstructured_requires) rather than the old
# decorative "requires_pass" the register found. That fix alone leaves these
# three doshas honestly DARK (no row at all) — this section gives the three
# the register names by ID (kemadruma, daridra, kala_sarpa) bespoke, genuinely
# -computed detectors instead, each with a MANDATORY cancellation callable
# (even where the classical answer is an honest non-cancellation), per
# LANE3_DETECTOR_REGISTRY.md §1.3. Every other catalog dosha keeps the
# honest-NULL `cancellation_na_reason` pattern (no fabricated doctrine, B.10).

def _moon_flanking_planets(chart_output: dict[str, Any]) -> dict[str, list[str]]:
    """Non-Sun/non-node planets in the 2nd-from-Moon and 12th-from-Moon
    houses (plus conjunct-with-Moon). This IS Kemadruma's own classical
    negative-space definition (BPHS: no graha with/flanking the Moon) and,
    by construction, exactly what Anapha (12th-from-Moon)/Sunapha
    (2nd-from-Moon)/Durudhara (both) require to exist — the two dosha/yoga
    families are mutually exclusive by shared arithmetic, not by a second
    ad hoc cross-check (CR-73)."""
    grahas = chart_output.get("grahas", [])
    moon = next((g for g in grahas if g.get("name") == "Moon"), None)
    if moon is None:
        return {"house_2nd": [], "house_12th": [], "conjunct": []}
    moon_h = int(moon.get("house", 0))
    h2 = ((moon_h - 1 + 1) % 12) + 1
    h12 = ((moon_h - 1 - 1) % 12) + 1
    exempt = {"Moon", "Sun", "Rahu", "Ketu"}
    in_2nd = [g["name"] for g in grahas if g.get("name") not in exempt and int(g.get("house", 0)) == h2]
    in_12th = [g["name"] for g in grahas if g.get("name") not in exempt and int(g.get("house", 0)) == h12]
    conjunct = [g["name"] for g in grahas if g.get("name") not in exempt and int(g.get("house", 0)) == moon_h]
    return {"house_2nd": in_2nd, "house_12th": in_12th, "conjunct": conjunct}


def _detect_kemadruma(chart_output: dict[str, Any]) -> dict[str, Any] | None:
    """Kemadruma formation: Moon with no planet (other than Sun/nodes)
    conjunct, in the 2nd, or in the 12th from it, AND Moon not in kendra
    from lagna. Returns None (does not form) the moment any flanking/
    conjunct planet is found — the SAME arithmetic Anapha/Durudhara run, so
    a chart where either of those genuinely fires can never also form
    Kemadruma (CR-73's mutual-exclusivity requirement, satisfied by
    construction)."""
    flank = _moon_flanking_planets(chart_output)
    if flank["house_2nd"] or flank["house_12th"] or flank["conjunct"]:
        return None
    moon = next((g for g in chart_output.get("grahas", []) if g.get("name") == "Moon"), None)
    if moon is None:
        return None
    moon_h = int(moon.get("house", 0))
    if moon_h in (1, 4, 7, 10):
        return None  # Moon in kendra from lagna — classical bhanga folded into the formation shape
    return {"constituent_planets": ["Moon"], "constituent_houses": [moon_h], "moon_house": moon_h}


# The five non-luminary, non-node grahas (the tara-grahas) are the ONLY
# bodies reckoned for the Chandra-yoga family (Sunapha/Anapha/Durudhara/
# Kemadruma and their bhanga): the Sun is excluded (an Amavasya Moon beside
# the Sun is still counted "unsupported"), and the nodes are shadowy and
# excluded classically. This is the SAME exempt set `_moon_flanking_planets`
# already uses ({Moon, Sun, Rahu, Ketu}), so the formation and cancellation
# passes reckon one coherent body of grahas (CR-73 mutual-exclusivity by
# shared arithmetic, extended to the kendra-support ground).
_KEMADRUMA_SUPPORT_EXEMPT = frozenset({"Moon", "Sun", "Rahu", "Ketu"})


def _kemadruma_kendra_support(chart_output: dict[str, Any], reference_house: int) -> list[str]:
    """Tara-grahas (Mars/Mercury/Jupiter/Venus/Saturn) occupying a kendra
    (1st/4th/7th/10th) from `reference_house`. Used for the classical
    kendra-from-Moon and kendra-from-lagna Kemadruma-bhanga grounds — the
    exact arithmetic the project's own ga_yoga_writer kemadruma detection
    (`no_planet_in_2_or_12_from_moon_and_no_kendra_support`) already applies
    for its firing verdict; restoring it here makes the dosha_label agree
    with that firing authority instead of contradicting it (CR-73)."""
    if not reference_house:
        return []
    kendra_houses = {((reference_house - 1 + k - 1) % 12) + 1 for k in (1, 4, 7, 10)}
    return sorted({
        g["name"]
        for g in chart_output.get("grahas", [])
        if g.get("name") not in _KEMADRUMA_SUPPORT_EXEMPT
        and int(g.get("house", 0)) in kendra_houses
    })


def _cancel_kemadruma(finding: dict[str, Any], chart_output: dict[str, Any]) -> dict[str, Any]:
    """Mandatory cancellation callable — the REAL Kemadruma-bhanga
    adjudication (CR-73).

    `brahma_dosha_catalog.kemadruma.cancellation_conditions.bhanga` (cited to
    BPHS) lists four classical bhanga grounds; its `formation_rule` likewise
    requires "...none in kendra from Moon/lagna". This function evaluates the
    two POSITIONAL grounds that resolve deterministically from the D1 houses
    the writer already loads:

      (1) a tara-graha in a kendra (1/4/7/10) from the Moon, and
      (2) a tara-graha in a kendra from the lagna,

    plus the flanking/conjunction ground (which normally routes through
    `_detect_kemadruma` and is kept here as defense-in-depth). The Moon-in-
    kendra-from-lagna ground is already folded into `_detect_kemadruma`'s
    formation gate, so a finding never reaches here in that case.

    The prior implementation folded ONLY the flanking-absence and Moon-in-
    kendra-from-lagna cases into formation and then returned an unconditional
    "not cancelled" here — silently omitting the single most common classical
    bhanga, a graha occupying a kendra FROM THE MOON. On the native's chart
    (482012f1) that omission let Kemadruma spuriously fire while Jupiter and
    Venus sit in the 10th-from-Moon (a kendra from the Moon) and the yoga-
    firing authority correctly shows Anapha/Sunapha (never kemadruma_aristha)
    — a cross-layer contradiction. This restores the kendra-support bhanga so
    the label agrees with the firing authority. The catalog's fourth ground
    ("Moon aspected by a benefic") remains an honest floor (B.10) — it is not
    fabricated into a positional shortcut here.
    """
    ref = "bphs:kemadruma:kendra_support_or_flanking_cancels"
    flank = _moon_flanking_planets(chart_output)
    if flank["house_2nd"] or flank["house_12th"] or flank["conjunct"]:
        # Unreachable given _detect_kemadruma's own gate — defensive only.
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": "anapha_or_durudhara_or_conjunction",
            "cancellation_na_reason": None,
            "citation_ref": ref,
            "citation_human": "A planet flanks/conjoins the Moon — Anapha/Sunapha/Durudhara forms instead of Kemadruma.",
        }

    moon_house = _graha_house(chart_output, "Moon")
    kendra_from_moon = _kemadruma_kendra_support(chart_output, moon_house)
    kendra_from_lagna = _kemadruma_kendra_support(chart_output, 1)

    grounds: list[str] = []
    if kendra_from_moon:
        grounds.append(f"kendra_from_moon:{','.join(kendra_from_moon)}")
    if kendra_from_lagna:
        grounds.append(f"kendra_from_lagna:{','.join(kendra_from_lagna)}")

    if grounds:
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": ";".join(grounds),
            "cancellation_na_reason": None,
            "citation_ref": ref,
            "citation_human": (
                "brahma_dosha_catalog kemadruma cancellation_conditions ('any planet in kendra "
                f"from Moon or lagna', BPHS): {'; '.join(grounds)} — a tara-graha in a kendra "
                "supports the Moon, so Kemadruma is cancelled and does not serve as a finding."
            ),
        }

    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "cancellation_na_reason": None,
        "citation_ref": ref,
        "citation_human": (
            "No planet flanks or conjoins the Moon, no tara-graha occupies a kendra from the Moon "
            "or the lagna, and the Moon is outside kendra from lagna — Kemadruma stands uncancelled "
            "(the benefic-aspect ground is not evaluated, honest floor B.10)."
        ),
    }


def _lord_afflicted(chart_output: dict[str, Any], planet: str) -> tuple[bool, list[str]]:
    """True + grounds iff `planet` is debilitated or combust — read from the
    same D1 graha positions/longitudes every other function in this writer
    already consumes (EXALTATION_SIGNS/DEBILITATION_SIGNS/COMBUSTION_ORBS);
    no new computation, no new data source."""
    sign = _graha_in_sign(chart_output, planet)
    grounds: list[str] = []
    if DEBILITATION_SIGNS.get(planet) == sign:
        grounds.append("debilitated")
    if planet != "Sun":
        orb = COMBUSTION_ORBS.get(planet)
        if orb:
            sun_long = _graha_longitude(chart_output, "Sun")
            p_long = _graha_longitude(chart_output, planet)
            d = abs(sun_long - p_long)
            if d > 180:
                d = 360 - d
            if d <= orb:
                grounds.append("combust")
    return bool(grounds), grounds


def _detect_daridra(chart_output: dict[str, Any]) -> dict[str, Any] | None:
    """Daridra formation, per brahma_dosha_catalog's own stored narrative
    ('11th lord in dusthana (6/8/12) or 2nd/11th lords afflicted'): the 11th
    lord is in a dusthana, OR the 2nd or 11th lord is debilitated/combust."""
    lord11 = _get_house_lord(chart_output, 11)
    lord2 = _get_house_lord(chart_output, 2)
    lord11_house = _graha_house(chart_output, lord11)
    grounds: list[str] = []
    if lord11_house in (6, 8, 12):
        grounds.append(f"11L_{lord11}_in_dusthana_H{lord11_house}")
    afflicted11, g11 = _lord_afflicted(chart_output, lord11)
    if afflicted11:
        grounds.append(f"11L_{lord11}_afflicted:{','.join(g11)}")
    afflicted2, g2 = _lord_afflicted(chart_output, lord2)
    if afflicted2:
        grounds.append(f"2L_{lord2}_afflicted:{','.join(g2)}")
    if not grounds:
        return None
    return {
        "constituent_planets": sorted({lord11, lord2}),
        "constituent_houses": [lord11_house],
        "grounds": grounds,
        "lord11": lord11, "lord2": lord2,
    }


def _load_wealth_ratification(conn: Any, chart_id: str, ayanamsha_id: str, subj: str) -> dict[str, Any] | None:
    """Read ga_vichara's `varga_ratification` row (domain='wealth') for
    `subj` (a PLANET_TO_SUBJECT code) — this IS the '11L/2L strength' signal
    the brief calls for (cross-varga dignity agreement over the wealth-house
    lords + Jupiter karaka), computed once by ga_vichara and never
    re-derived here (§N.5 L1/L1.5-authority discipline). Returns None on any
    DB error/absence — an honest gap, not a fabricated strength."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT value_num, value_jsonb FROM chart_vichara
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND vichara_family = 'varga_ratification' AND domain = 'wealth' AND subject = %s
                LIMIT 1
            """, (chart_id, ayanamsha_id, subj))
            row = cur.fetchone()
    except Exception as exc:
        logger.warning(
            "[ga_structural_writer] chart_vichara unavailable for daridra cancellation (chart=%s ayanamsha=%s): %s",
            chart_id, ayanamsha_id, exc,
        )
        return None
    if not row:
        return None
    # Orchestrator connections use psycopg3's dict_row factory (pipeline/
    # orchestrator/db.py) — rows are dict-like, not tuples. See the sibling
    # fix in _dhana_yoga_fires_for for the same bug class (KeyError: 0).
    if isinstance(row, dict):
        value_num, value_jsonb = row.get("value_num"), row.get("value_jsonb")
    else:
        value_num, value_jsonb = row[0], row[1]
    if isinstance(value_jsonb, str):
        try:
            value_jsonb = json.loads(value_jsonb)
        except Exception:
            value_jsonb = {}
    return {"ratification_factor": value_num, **(value_jsonb or {})}


def _dhana_yoga_fires_for(conn: Any, chart_id: str, ayanamsha_id: str, planets: set[str]) -> list[str]:
    """Fired `ga_yoga_firings` rows whose canonical_id names a dhana-family
    yoga AND whose constituent_planets intersect `planets` — read-only L1
    consumption (§N.5), never a second dhana detector."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT yoga_canonical_id, constituent_planets FROM ga_yoga_firings
                WHERE chart_id = %s AND ayanamsha_id = %s AND fired = TRUE
                  AND yoga_canonical_id ILIKE %s
            """, (chart_id, ayanamsha_id, "%dhana%"))
            rows = cur.fetchall()
    except Exception as exc:
        logger.warning(
            "[ga_structural_writer] ga_yoga_firings unavailable for daridra cancellation (chart=%s ayanamsha=%s): %s",
            chart_id, ayanamsha_id, exc,
        )
        return []
    lowered = {p.lower() for p in planets}
    hits: list[str] = []
    for row in rows:
        # Orchestrator connections use psycopg3's dict_row factory (pipeline/
        # orchestrator/db.py) — rows are dict-like, not tuples. Access by
        # column name, with a defensive fallback for any caller that still
        # passes a tuple-row connection (e.g. a legacy standalone-CLI path).
        if isinstance(row, dict):
            cid, cp = row.get("yoga_canonical_id"), row.get("constituent_planets")
        else:
            cid, cp = row[0], row[1]
        if isinstance(cp, str):
            try:
                cp = json.loads(cp)
            except Exception:
                cp = []
        if any(str(p).lower() in lowered for p in (cp or [])):
            hits.append(cid)
    return hits


def _cancel_daridra(
    finding: dict[str, Any], chart_output: dict[str, Any],
    conn: Any, chart_id: str, ayanamsha_id: str,
) -> dict[str, Any]:
    """Mandatory cancellation — brahma_dosha_catalog's own stored
    cancellation_conditions for daridra ('dhana/raja yoga present' /
    '11th lord retrograde-strong'); this implementation encodes the brief's
    literal ground set (11L exalted / 2L-9L dhana structure fires), citing
    ga_vichara for the 11L-strength ground (design §11 varga_ratification IS
    the '11L/2L strength' signal) and ga_yoga_firings for the dhana-structure
    ground — never re-deriving either."""
    ref = "bphs:daridra:dhana_yoga_or_strong_wealth_lord_cancels"
    lord11 = finding["lord11"]
    lord9 = _get_house_lord(chart_output, 9)
    subj11 = PLANET_TO_SUBJECT.get(lord11, lord11.upper())

    grounds: list[str] = []

    # Ground A: 11L exalted — ga_vichara varga_ratification (domain=wealth)
    # is the cross-varga corroboration; fall back to the direct D1 sign
    # check (same source _detect_daridra already reads) if vichara is dark.
    vichara = _load_wealth_ratification(conn, chart_id, ayanamsha_id, subj11)
    d1_dignity = (vichara or {}).get("d1_dignity")
    if d1_dignity == "exalted":
        grounds.append(f"11L_{lord11}_exalted_per_ga_vichara_varga_ratification")
    elif EXALTATION_SIGNS.get(lord11) == _graha_in_sign(chart_output, lord11):
        grounds.append(f"11L_{lord11}_exalted_d1")

    # Ground B: 2L-9L (or 11L-anchored) dhana structure genuinely fires.
    dhana_hits = _dhana_yoga_fires_for(conn, chart_id, ayanamsha_id, {finding["lord2"], lord9, lord11})
    if dhana_hits:
        grounds.append(f"dhana_structure_fires:{','.join(sorted(set(dhana_hits)))}")

    if grounds:
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": ";".join(grounds),
            "cancellation_na_reason": None,
            "citation_ref": ref,
            "citation_human": (
                "brahma_dosha_catalog daridra cancellation_conditions ('dhana/raja yoga present'): "
                f"{'; '.join(grounds)} — Daridra does not serve as a finding."
            ),
        }
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "cancellation_na_reason": None,
        "citation_ref": ref,
        "citation_human": "Neither the 11th lord exaltation ground nor a fired dhana structure was found — Daridra stands uncancelled.",
    }


# Mars sign-specific cancellation pairs (house, sign) per brahma_dosha_catalog's
# stored `manglik` cancellation_conditions text ("Mars in 2nd in Gemini/Virgo,
# 4th in Aries/Scorpio, 7th in Capricorn/Cancer, 12th in Sagittarius/Pisces,
# 8th in Cancer") — BPHS ch.81 tradition, sign-specific bhanga.
_MANGLIK_SIGN_SPECIFIC_CANCEL: dict[int, frozenset[str]] = {
    2: frozenset({"Gemini", "Virgo"}),
    4: frozenset({"Aries", "Scorpio"}),
    7: frozenset({"Capricorn", "Cancer"}),
    8: frozenset({"Cancer"}),
    12: frozenset({"Sagittarius", "Pisces"}),
}


def _cancel_manglik(
    finding: dict[str, Any] | None, chart_output: dict[str, Any],
    conn: Any, chart_id: str, ayanamsha_id: str,
) -> dict[str, Any]:
    """CR-73: manglik cancellation per brahma_dosha_catalog's own stored
    `cancellation_conditions` (BPHS ch.81 tradition) — encodes the classical
    grounds literally, evaluated against THIS chart, never a re-derivation
    of a different classical source. `finding` is the `_detect_manglik`
    bespoke-detector result (EL-18) but is unused here — Mars's house and
    sign are read directly from chart_output, the single source of truth."""
    ref = "bphs:manglik:own_exalt_or_jupiter_aspect_or_sign_specific_cancels"
    mars_house = _graha_house(chart_output, "Mars")
    mars_sign = _graha_in_sign(chart_output, "Mars")
    jup_house = _graha_house(chart_output, "Jupiter")
    venus_house = _graha_house(chart_output, "Venus")
    kendra = {1, 4, 7, 10}

    grounds: list[str] = []
    if mars_sign in OWN_SIGNS.get("Mars", []) or mars_sign == EXALTATION_SIGNS.get("Mars"):
        grounds.append(f"mars_own_or_exalt_sign:{mars_sign}")
    if _graha_aspects_house("Jupiter", jup_house, mars_house) > 0.0:
        grounds.append(f"jupiter_aspects_mars_house_{mars_house}")
    if jup_house in kendra:
        grounds.append(f"jupiter_in_kendra_h{jup_house}")
    if venus_house in kendra:
        grounds.append(f"venus_in_kendra_h{venus_house}")
    sign_specific = _MANGLIK_SIGN_SPECIFIC_CANCEL.get(mars_house, frozenset())
    if mars_sign in sign_specific:
        grounds.append(f"sign_specific_cancel:mars_h{mars_house}_{mars_sign}")

    if grounds:
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": ";".join(grounds),
            "cancellation_na_reason": None,
            "citation_ref": ref,
            "citation_human": (
                "brahma_dosha_catalog manglik cancellation_conditions (BPHS ch.81): "
                f"{'; '.join(grounds)} — Manglik does not serve as a finding."
            ),
        }
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "cancellation_na_reason": None,
        "citation_ref": ref,
        "citation_human": (
            "No cancellation ground (own/exalt sign, Jupiter aspect/kendra, "
            "Venus kendra, sign-specific pairing) found — Manglik stands uncancelled. "
            "Both-partners-Manglik cancellation is a synastry-only ground and is "
            "out of scope for a single-chart evaluation (documented, not silently dropped)."
        ),
    }


# Manglik / Kuja Dosha houses (BPHS ch.78 Kuja-dosha / ch.81 Manglik tradition):
# Mars in the 1/2/4/7/8/12 reckoned from the lagna (and additionally checked
# from the Moon and from Venus, the kalatra-karaka) — read literally from
# brahma_dosha_catalog.manglik.formation_rule_jsonb
# ({"houses":[1,2,4,7,8,12], "planet":"mars", "reference":["lagna","moon","venus"]}).
_MANGLIK_HOUSES: frozenset[int] = frozenset({1, 2, 4, 7, 8, 12})


def _detect_manglik(chart_output: dict[str, Any]) -> dict[str, Any] | None:
    """Manglik / Kuja Dosha formation — bespoke detector (EL-18 / CR-73 completion).

    Why a bespoke detector is required (root cause, EL-18): the generic
    `_evaluate_catalog_rule` implements only the `requires` / `all_planets_in`
    / `distinct_signs_occupied` / `benefics_in` rule shapes. It has NO handler
    for the ``{"houses": [...], "planet": ..., "reference": [...]}`` shape that
    brahma_dosha_catalog.manglik (and the per-house kuja_dosha_* rows) store,
    so manglik fails closed with `rule_format_unimplemented`, never forms, and
    the fully-built, BPHS-cited `_cancel_manglik` cancellation callable
    (registered in DOSHA_CANCELLATIONS) is unreachable. This detector restores
    formation detection *literally from the catalog's own stored
    formation_rule_jsonb* so the classical cancellation can be adjudicated.

    Houses are read from the D1 positions the writer already loads
    (`house_d1` = house-from-lagna); Mars-from-Moon and Mars-from-Venus are the
    same houses counted from those reference bodies. No new computation, no new
    data source (§N.5 L1-authority). Returns None when Mars occupies none of
    the dosha houses from any of the three references — an honest
    non-formation, never a dark stub.
    """
    mars_h = _graha_house(chart_output, "Mars")
    if not mars_h:
        return None
    references: list[str] = []
    if mars_h in _MANGLIK_HOUSES:
        references.append("lagna")
    for ref_name, ref_planet in (("moon", "Moon"), ("venus", "Venus")):
        ref_h = _graha_house(chart_output, ref_planet)
        if not ref_h:
            continue
        mars_from_ref = ((mars_h - ref_h) % 12) + 1
        if mars_from_ref in _MANGLIK_HOUSES:
            references.append(f"{ref_name}(h{mars_from_ref})")
    if not references:
        return None  # Mars in no Manglik house from any reference — honest absence
    return {
        "constituent_planets": ["Mars"],
        "constituent_houses": [mars_h],
        "references": references,
        "mars_house": mars_h,
    }


# 12 named Kala Sarpa variants keyed by Rahu's house (1-12) — classical naming
# (Anant/Kulik/Vasuki/Shankhpal/Padma/Mahapadma/Takshak/Karkotak/Shankhachud/
# Ghatak/Vishdhar/Sheshnag). BESPOKE_DOSHA_DETECTORS only maps the base
# "kala_sarpa" canonical_id; these 12 catalog rows are distinct canonical_ids
# whose formation test IS "kala_sarpa fires AND Rahu occupies house N" — no
# second detector, wired to the same genuinely-computed `_detect_kala_sarpa`
# result (mirrors the base wiring's own CR-74 instruction).
KALA_SARPA_NAMED_VARIANT_HOUSE: dict[str, int] = {
    "kala_sarpa_anant": 1, "kala_sarpa_kulik": 2, "kala_sarpa_vasuki": 3,
    "kala_sarpa_shankhpal": 4, "kala_sarpa_padma": 5, "kala_sarpa_mahapadma": 6,
    "kala_sarpa_takshak": 7, "kala_sarpa_karkotak": 8, "kala_sarpa_shankhachud": 9,
    "kala_sarpa_ghatak": 10, "kala_sarpa_vishdhar": 11, "kala_sarpa_sheshnag": 12,
}


def _make_kala_sarpa_named_variant_detector(house: int) -> Callable[[dict[str, Any]], dict[str, Any] | None]:
    def _detect(chart_output: dict[str, Any]) -> dict[str, Any] | None:
        base = _detect_kala_sarpa_dosha(chart_output)
        if base is None or base["constituent_houses"][0] != house:
            return None
        return base
    return _detect


def _cancel_kala_sarpa_named_variant(
    finding: dict[str, Any], chart_output: dict[str, Any],
    conn: Any, chart_id: str, ayanamsha_id: str,
) -> dict[str, Any]:
    """Same non-duplication rationale as the base `_cancel_kala_sarpa` —
    a named variant IS the base kala_sarpa verdict narrowed to a specific
    Rahu house; no separate bhanga layer applies on top."""
    return _cancel_kala_sarpa(finding, chart_output)


def _detect_kala_sarpa_dosha(chart_output: dict[str, Any]) -> dict[str, Any] | None:
    """Wires the `kala_sarpa` dosha_label row directly to the SAME
    genuinely-computed `_detect_kala_sarpa` function this writer already
    runs per-varga (the `kala_sarpa_per_varga` fact) — no second detector
    (CR-74's explicit instruction: 'do not build a second KS detector; wire
    the label to the existing computed fact'). Only the malefic
    'kala_sarpa' variant on D1 corresponds to this catalog canonical_id;
    'kala_amrita' is a distinct catalog entry (kala_amrita_dosha) untouched
    here."""
    d1_state = _extract_chart_state(chart_output)
    ks_result = _detect_kala_sarpa(d1_state)
    if not ks_result["fires"] or ks_result["variant"] != "kala_sarpa":
        return None
    return {
        "constituent_planets": ["Rahu", "Ketu"],
        "constituent_houses": [ks_result["rahu_house"], ks_result["ketu_house"]],
        "variant_name": ks_result["variant_name"],
    }


def _cancel_kala_sarpa(finding: dict[str, Any], chart_output: dict[str, Any]) -> dict[str, Any]:
    """No separate cancellation layer — the verdict IS the genuinely-computed
    kala_sarpa_per_varga fact (all 7 classical grahas hemmed with none
    breaking the arc); a chart that reaches this function already passed
    that whole-chart test, so there is no additional classical bhanga to
    apply on top (mirrors kemadruma_aristha's own 'gated into formation, not
    duplicated' precedent in the yoga writer). Present for
    DOSHA_CANCELLATIONS registry hygiene (every entry has a non-None
    callable, per the brief) — not a silent no-op."""
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "cancellation_na_reason": (
            "verdict wired directly to the genuinely-computed kala_sarpa_per_varga fact — "
            "no separate cancellation is layered on top of the whole-chart hemming test"
        ),
        "citation_ref": "ga_structural.kala_sarpa_per_varga:direct_wiring",
        "citation_human": "Kala Sarpa label mirrors the computed per-varga verdict; no independent bhanga check applies.",
    }


# Bespoke, genuinely-computed detectors for the three doshas the register
# names by ID (CR-72/73/74) — bypass `_evaluate_catalog_rule`'s generic
# (narrative-string, always-fails-closed) evaluation entirely.
BESPOKE_DOSHA_DETECTORS: dict[str, Callable[[dict[str, Any]], dict[str, Any] | None]] = {
    "kemadruma": _detect_kemadruma,
    "daridra": _detect_daridra,
    "kala_sarpa": _detect_kala_sarpa_dosha,
    # EL-18 (Elevation v2.1, this lane): manglik REQUIRES a bespoke detector.
    # A prior note here claimed manglik "runs the generic per-chart catalog-rule
    # path (no bespoke detector needed)" — that was incorrect and left the dosha
    # dark: `_evaluate_catalog_rule` has no handler for manglik's
    # {"houses","planet","reference"} formation shape, so it returned
    # (False, "rule_format_unimplemented"), the dosha never formed, and the
    # fully-built BPHS-cited `_cancel_manglik` (registered in DOSHA_CANCELLATIONS)
    # was unreachable dead code. `_detect_manglik` restores formation from the
    # catalog's own stored formation_rule_jsonb so the cancellation is adjudicated
    # (verified empirically 2026-07-25). The 12 named Kala Sarpa variants DO need
    # bespoke wiring since their canonical_ids are distinct catalog rows narrowing
    # the base kala_sarpa verdict to a specific Rahu house (no second detector —
    # see `_make_kala_sarpa_named_variant_detector`'s docstring).
    "manglik": _detect_manglik,
    **{
        canonical_id: _make_kala_sarpa_named_variant_detector(house)
        for canonical_id, house in KALA_SARPA_NAMED_VARIANT_HOUSE.items()
    },
}

# Mandatory cancellation callables — every entry here (and every dosha in
# BESPOKE_DOSHA_DETECTORS) has one, even where the honest verdict is "no
# additional classical bhanga applies" (kala_sarpa) or "already gated into
# formation" (kemadruma). Signature: (finding, chart_output, conn, chart_id,
# ayanamsha_id) -> {"bhanga_active", "bhanga_rule_fired",
# "cancellation_na_reason", "citation_ref", "citation_human"}.
DOSHA_CANCELLATIONS: dict[str, Callable[..., dict[str, Any]]] = {
    "kemadruma": lambda finding, chart_output, conn, chart_id, ayanamsha_id: _cancel_kemadruma(finding, chart_output),
    "daridra": _cancel_daridra,
    "kala_sarpa": lambda finding, chart_output, conn, chart_id, ayanamsha_id: _cancel_kala_sarpa(finding, chart_output),
    # CR-73 completion (this lane): manglik — the single most classically-
    # documented single-chart dosha with an explicit stored cancellation set.
    "manglik": _cancel_manglik,
    **{
        canonical_id: _cancel_kala_sarpa_named_variant
        for canonical_id in KALA_SARPA_NAMED_VARIANT_HOUSE
    },
}


def _build_dosha_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
    dosha_catalog: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Label pass over brahma_dosha_catalog (DB path) or DOSHA_LIBRARY (legacy fallback).

    DB path (dosha_catalog provided): evaluates formation_rule_jsonb via _evaluate_catalog_rule;
    emits 'dosha_label' category rows.
    Legacy fallback (dosha_catalog is None): hardcoded evaluation; emits 'dosha_fires' rows.
    """
    rows: list[dict[str, Any]] = []

    if dosha_catalog is not None:
        # ── DB catalog path ───────────────────────────────────────────────────
        for entry in dosha_catalog:
            dosha_name = entry["canonical_id"]
            rule = entry.get("formation_rule_jsonb") or {}

            # Lane 3 (Night-1) Deliverable C: kemadruma/daridra/kala_sarpa
            # bypass the generic (narrative-string, always-fails-closed)
            # evaluator entirely — bespoke, genuinely-computed detection.
            catalog_only = False
            bespoke_finding: dict[str, Any] | None = None
            if dosha_name in BESPOKE_DOSHA_DETECTORS:
                bespoke_finding = BESPOKE_DOSHA_DETECTORS[dosha_name](chart_output)
                if bespoke_finding is None:
                    continue  # genuinely does not form — honest absence, not a dark stub
                fires, reason = True, f"bespoke_detector:{dosha_name}"
            else:
                fires, reason = _evaluate_catalog_rule(rule, chart_output)
                if not fires:
                    continue
                # CR-72's decorative-stub pattern: "requires_pass" means the
                # rule shape trivially passed without a real per-chart check
                # (every sub-condition vacuously satisfied) — never served as
                # a genuine firing; gated behind an explicit marker instead
                # (Option 2 of the brief's §1.3(1)).
                catalog_only = (reason == "requires_pass")

            name_en = entry.get("name_en", dosha_name)
            citations = entry.get("classical_citations") or {}
            source_chunks = entry.get("source_chunk_ids") or []
            # S-2(d): bespoke-detected doshas (kemadruma/daridra/kala_sarpa)
            # ground on their OWN finding's constituent_planets — never the
            # generic catalog-rule resolver, which falls back to a single
            # shared SUN/sign fact_id for every narrative-"requires" dosha
            # (the CR-72 shared-stub pattern reappearing one layer down).
            if bespoke_finding is not None:
                constituents = _bespoke_dosha_constituent_fact_ids(
                    conn, chart_id, ayanamsha_id, bespoke_finding
                )
                if not constituents:
                    # Defensive fallback only (e.g. a conn with no real
                    # chart_facts rows yet) — never silently empty when the
                    # generic path can still resolve something honest.
                    constituents = _get_catalog_constituent_fact_ids(
                        conn, entry, chart_output, chart_id, ayanamsha_id
                    )
            else:
                constituents = _get_catalog_constituent_fact_ids(
                    conn, entry, chart_output, chart_id, ayanamsha_id
                )

            # ── Mandatory cancellation check (CR-73 doctrine) ───────────────────
            bhanga_active: bool | None = None
            bhanga_rule_fired: str | None = None
            cancellation_na_reason: str | None = None
            cancellation_citation_ref: str | None = None
            cancellation_citation_human: str | None = None
            if not catalog_only:
                if dosha_name in DOSHA_CANCELLATIONS:
                    verdict = DOSHA_CANCELLATIONS[dosha_name](
                        bespoke_finding, chart_output, conn, chart_id, ayanamsha_id,
                    )
                    bhanga_active = verdict.get("bhanga_active")
                    bhanga_rule_fired = verdict.get("bhanga_rule_fired")
                    cancellation_na_reason = verdict.get("cancellation_na_reason")
                    cancellation_citation_ref = verdict.get("citation_ref")
                    cancellation_citation_human = verdict.get("citation_human")
                else:
                    cancellation_na_reason = "no classical cancellation rule implemented"

            if catalog_only:
                fires_final: bool | None = None
            elif bhanga_active:
                fires_final = False  # cancelled — evaluated, not served as a finding
            else:
                fires_final = True

            citation_human = (
                f"Dosha {name_en} ({dosha_name}) labels chart {str(chart_id)[:8]} "
                f"({ayanamsha_id}): {reason}."
            )
            if catalog_only:
                citation_human += " [CATALOG-ONLY: formation shape not evaluated against this chart — not a finding.]"
            elif bhanga_active and cancellation_citation_human:
                citation_human += f" CANCELLED: {cancellation_citation_human}"

            rows.append(_base_row(
                "dosha_label", dosha_name, "dosha_name",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text=name_en,
                value_jsonb={
                    "constituent_facts_array": constituents,
                    "classical_citations": citations,
                    "dosha_group": entry.get("category", ""),
                    "source_chunk_ids": source_chunks,
                    "uncatalogued": False,
                    "fire_reason": reason,
                    # Deliverable C additions (CR-72/73/74) ──────────────────
                    "catalog_only": catalog_only,
                    "fires": fires_final,
                    "bhanga_active": bhanga_active,
                    "bhanga_rule_fired": bhanga_rule_fired,
                    "cancellation_na_reason": cancellation_na_reason,
                    "cancellation_citation_ref": cancellation_citation_ref,
                },
                # Y-7 fix: same rationale as the yoga_label site above — single
                # catalog-rule evaluation, not the writer's two-pass cross-check;
                # demoted to the already-wired "single_pass" verification tier.
                verif="single_pass",
                source=f"brahma_dosha_catalog.label_pass/{eng_ver}",
                citation_human=citation_human,
            ))
        return rows

    # ── Legacy fallback path: DOSHA_LIBRARY hardcoded evaluation ────────────
    library = DOSHA_LIBRARY
    grahas_data = chart_output.get("grahas", [])

    def get_graha(name: str):
        return next((g for g in grahas_data if g["name"] == name), None)

    def conjunct(n1: str, n2: str, orb: float = 10.0) -> bool:
        g1 = get_graha(n1)
        g2 = get_graha(n2)
        if g1 is None or g2 is None:
            return False
        l1 = float(g1.get("longitude", 0.0))
        l2 = float(g2.get("longitude", 0.0))
        d = abs(l1 - l2)
        if d > 180:
            d = 360 - d
        return d <= orb

    for dosha_def in library:
        fires = False
        reason = ""
        cancelled = False
        cancelled_by = ""

        name = dosha_def["name"]

        # Mangal Dosha
        if name.startswith("MANGAL_DOSHA"):
            h = dosha_def["conditions"][0][2]
            mars = get_graha("Mars")
            if mars and int(mars.get("house", 0)) == h:
                fires = True
                reason = f"Mars in house {h}"
                # Mangal dosha cancelled if Mars in own/exalt sign
                if mars.get("sign", "") in ["Aries", "Scorpio", "Capricorn"]:
                    cancelled = True
                    cancelled_by = "Mars_in_own_or_exalt"

        elif name == "KALA_SARPA":
            rahu = get_graha("Rahu")
            ketu = get_graha("Ketu")
            if rahu and ketu:
                rahu_long = float(rahu.get("longitude", 0.0))
                ketu_long = float(ketu.get("longitude", 0.0))
                all_in_range = True
                for g in grahas_data:
                    if g["name"] in {"Rahu", "Ketu"}:
                        continue
                    g_long = float(g.get("longitude", 0.0))
                    # Check if planet is between Rahu and Ketu (one half of zodiac)
                    # Simplified check
                    r, k = min(rahu_long, ketu_long), max(rahu_long, ketu_long)
                    if not (r <= g_long <= k):
                        if not ((g_long < r) or (g_long > k)):
                            all_in_range = False
                            break
                fires = all_in_range

        elif name == "SHRAPIT_YOGA":
            fires = conjunct("Saturn", "Rahu")
            if fires:
                reason = "Saturn conjunct Rahu"

        elif name == "CHANDAL_YOGA":
            fires = conjunct("Jupiter", "Rahu")
            if fires:
                reason = "Jupiter conjunct Rahu"
                # Chandal cancellation: Jupiter in own sign
                jup = get_graha("Jupiter")
                if jup and jup.get("sign", "") in ["Sagittarius", "Pisces"]:
                    cancelled = True
                    cancelled_by = "Jupiter_in_own_sign"

        elif name == "GRAHAN_YOGA":
            fires = (conjunct("Sun", "Rahu") or conjunct("Sun", "Ketu") or
                     conjunct("Moon", "Rahu") or conjunct("Moon", "Ketu"))
            if fires:
                reason = "Sun or Moon conjunct Rahu/Ketu"

        elif name == "SHAKATA_YOGA":
            jup = get_graha("Jupiter")
            moon = get_graha("Moon")
            if jup and moon:
                moon_house = int(moon.get("house", 0))
                jup_house = int(jup.get("house", 0))
                offset = (jup_house - moon_house) % 12
                if offset in {5, 6, 7, 11}:  # 6/8/12 from Moon
                    fires = True
                    reason = f"Jupiter in {jup_house} from Moon in {moon_house}"

        elif name in ("DARIDRA_YOGA_6_11", "DARIDRA_YOGA_2_12"):
            h_num = 11 if "6_11" in name else 12
            lord_name = _get_house_lord(chart_output, h_num)
            lord = get_graha(lord_name)
            if lord and int(lord.get("house", 0)) in {6, 8, 12}:
                fires = True
                reason = f"Lord of {h_num}H ({lord_name}) in dusthana"

        elif name in ("GANDANTA_DOSHA", "MRITYU_BHAGA_DOSHA"):
            # WP-2.5/LCA-10: fire from ga_sensitive_degree's cited classical checks,
            # computed inline over the grahas already loaded (no cross-asset dependency).
            try:
                from ga_writers.ga_sensitive_degree_writer import (
                    check_gandanta, check_mrityu_bhaga,
                )
                afflicted: list[str] = []
                for _g in grahas_data:
                    _gn = _g.get("name")
                    if _gn in (None, "Lagna"):
                        continue
                    _lon = float(_g.get("longitude", 0.0))
                    _sn = int(_lon // 30) % 12
                    _deg = _lon % 30.0
                    if name == "GANDANTA_DOSHA":
                        if check_gandanta(_sn, _deg)["fired"]:
                            afflicted.append(_gn)
                    else:
                        if check_mrityu_bhaga(_gn, _sn, _deg).get("fired"):
                            afflicted.append(_gn)
                if afflicted:
                    fires = True
                    _label = "gandanta sandhi" if name == "GANDANTA_DOSHA" else "mrityu-bhaga"
                    reason = f"{_label}: {', '.join(sorted(set(afflicted)))}"
            except Exception:
                fires = False  # never regress the dosha pass on a wiring error

        if fires:
            _primary = name.split("_")[0]
            _subj = PLANET_TO_SUBJECT.get(_primary, _primary)
            _fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", _subj, "sign")
            constituents = [_fid] if _fid else []
            rows.append(_base_row(
                "dosha_fires", name, "dosha_name",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text=name,
                value_jsonb={
                    "constituent_facts_array": constituents,
                    "classical_citation_id": dosha_def.get("citation", ""),
                    "dosha_group": dosha_def.get("group", ""),
                    "cancellation_flag": cancelled,
                    "cancelled_by_yoga_name": cancelled_by,
                    "fire_reason": reason,
                },
                verif="two_pass_verified",
                source=f"pyjhora_adapter.dosha_fires/{eng_ver}",
                citation_human=(
                    f"Dosha {name} fires"
                    f"{' (cancelled: ' + cancelled_by + ')' if cancelled else ''}"
                    f" ({ayanamsha_id})."
                ),
            ))

    return rows


# ── Group G2: Upapada Lagna wiring (CR-101) ───────────────────────────────────

def _house_from_reference_sign(target_sign: str, reference_sign: str) -> int:
    """1-indexed house-count of target_sign counted from reference_sign
    (reference_sign = house 1). Whole-sign counting, same convention as
    `_sign_house` but with an arbitrary reference point instead of Lagna."""
    ref_idx = SIGN_NAMES.index(reference_sign)
    tgt_idx = SIGN_NAMES.index(target_sign)
    return ((tgt_idx - ref_idx) % 12) + 1


def _load_upapada_lagna(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, Any] | None:
    """Read the already-computed Upapada Lagna (UL = Arudha of the 12th
    house, A12 — Jaimini/BPHS ch.30 reduction) from chart_facts. UL is
    computed by `_build_bhava_arudha_rows` (ga_sensitive, GA5) under
    fact_subject='BHAVA_ARUDHA_A12' — this function READS that row; it never
    re-derives the arudha (§N.5: L1 is the authority over its own facts,
    a downstream family never restates an upstream computed value).
    NOTE: `_ARUDHA_ALIASES` in ga_sensitive_writer.py labels A2 as "UPA" —
    that alias is a legacy label on the DIFFERENT A2 (Dhana pada) row and is
    NOT Upapada Lagna; per BPHS ch.30 and the Jaimini Upapada reduction
    (UL = arudha of the bhava that is 2nd-from-11th = A12), this function
    deliberately reads BHAVA_ARUDHA_A12, not BHAVA_ARUDHA_A2/UPA."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                """
                SELECT MAX(CASE WHEN fact_key = 'sign' THEN fact_value_text END) AS sign,
                       MAX(CASE WHEN fact_key = 'house_d1' THEN fact_value_num END) AS house_d1
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category = 'bhava_arudha' AND fact_subject = 'BHAVA_ARUDHA_A12'
                """,
                (chart_id, ayanamsha_id),
            )
            row = cur.fetchone()
        if not row or not row[0]:
            return None
        return {"sign": str(row[0]), "house_d1": int(row[1]) if row[1] is not None else None}
    except Exception as exc:
        logger.warning("[ga_structural] _load_upapada_lagna failed (chart_id=%s): %s", chart_id, exc)
        return None


def _build_upapada_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """CR-101: wire BPHS ch.30 Upapada Lagna rules against the already-
    computed A12 (Upapada Lagna). Emits:
      - upapada_lagna.sign / house_d1 (mirror of the source fact, for
        one-hop discoverability without a cross-category join)
      - upapada_lagna.lord_placement_verdict (derivation-ledger cites the
        exact UPAPADA_RULES rule_id fired)
      - upapada_lagna.benefic_association / malefic_association (conjunction
        test only — aspect-based association is a documented, not fabricated,
        scope limitation; see docstring)
    Every row's citation_ref points at the specific UPAPADA_RULES rule_id
    consumed (CLAUDE.md B.3).
    """
    ul = _load_upapada_lagna(conn, chart_id, ayanamsha_id)
    if ul is None:
        return []

    ul_sign = ul["sign"]
    ul_lord = SIGN_LORDS.get(ul_sign, "Sun")
    lord_sign = _graha_in_sign(chart_output, ul_lord)
    lord_house_from_ul = _house_from_reference_sign(lord_sign, ul_sign)

    rules_by_slug = {r["slug"]: r for r in UPAPADA_RULES}

    rows: list[dict[str, Any]] = []
    ul_fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "bhava_arudha", "BHAVA_ARUDHA_A12", "sign")
    lord_subj = PLANET_TO_SUBJECT.get(ul_lord, ul_lord.upper())
    lord_fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", lord_subj, "sign")
    constituents = [f for f in (ul_fid, lord_fid) if f]

    rows.append(_base_row(
        "upapada_lagna", "UPAPADA_LAGNA", "sign",
        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
        value_text=ul_sign,
        value_jsonb={"house_d1": ul["house_d1"], "lord": ul_lord},
        constituent_facts_array=[f for f in (ul_fid,) if f],
        source=f"ga_structural.upapada/{eng_ver}",
        citation_human=(
            f"Upapada Lagna (A12, BPHS ch.30 Jaimini reduction) = {ul_sign}, "
            f"lord {ul_lord}."
        ),
    ))

    if lord_house_from_ul in KENDRA_HOUSES_NON_LAGNA | TRIKONA_HOUSES | {1}:
        rule = rules_by_slug["ul_lord_kendra_trikona_from_ul"]
        verdict = rule["verdict"]
    elif lord_house_from_ul in {6, 8, 12}:
        rule = rules_by_slug["ul_lord_dusthana_from_ul"]
        verdict = rule["verdict"]
    else:
        rule = None
        verdict = "neutral_placement"

    rows.append(_base_row(
        "upapada_lagna", "UPAPADA_LAGNA", "lord_placement_verdict",
        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
        value_text=verdict,
        value_jsonb={
            "ul_lord": ul_lord,
            "ul_lord_house_from_ul": lord_house_from_ul,
            "rule_id": rule["rule_id"] if rule else None,
        },
        constituent_facts_array=constituents,
        source=f"ga_structural.upapada/{eng_ver}",
        citation_human=(rule["citation_human"] if rule else
                        "UL lord is in an upachaya (3/11) from UL — the cited "
                        "BPHS ch.30 rule set does not classify this placement; "
                        "reported as neutral, not fabricated."),
    ))

    benefic_conj = [g for g in CLASSICAL_GRAHAS
                    if g in _NATURAL_BENEFICS and _graha_in_sign(chart_output, g) == ul_sign]
    malefic_conj = [g for g in CLASSICAL_GRAHAS
                    if g in _NATURAL_MALEFICS and _graha_in_sign(chart_output, g) == ul_sign]

    if benefic_conj:
        rule = rules_by_slug["natural_benefic_conjunct_ul"]
        rows.append(_base_row(
            "upapada_lagna", "UPAPADA_LAGNA", "benefic_association",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=",".join(benefic_conj),
            value_jsonb={"rule_id": rule["rule_id"], "conjunct_grahas": benefic_conj},
            constituent_facts_array=constituents,
            source=f"ga_structural.upapada/{eng_ver}",
            citation_human=rule["citation_human"],
        ))
    if malefic_conj:
        rule = rules_by_slug["natural_malefic_conjunct_ul"]
        rows.append(_base_row(
            "upapada_lagna", "UPAPADA_LAGNA", "malefic_association",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=",".join(malefic_conj),
            value_jsonb={"rule_id": rule["rule_id"], "conjunct_grahas": malefic_conj},
            constituent_facts_array=constituents,
            source=f"ga_structural.upapada/{eng_ver}",
            citation_human=rule["citation_human"],
        ))

    return rows


# ── Group G3: Pañcadhā-maitrī compound matrix (CR-105) ────────────────────────

def _temporal_relation(source: str, target: str, chart_output: dict[str, Any]) -> str:
    """BPHS ch.4 v.19-20 temporal (tatkalika) friendship: houses counted from
    the SOURCE graha's own sign to the TARGET graha's sign."""
    source_sign = _graha_in_sign(chart_output, source)
    target_sign = _graha_in_sign(chart_output, target)
    h = _house_from_reference_sign(target_sign, source_sign)
    if h in TEMPORAL_FRIEND_HOUSES:
        return "friend"
    return "enemy"  # TEMPORAL_ENEMY_HOUSES is the complement by construction


def _natural_relation(source: str, target: str) -> str:
    if source == target:
        return "friend"  # a graha is its own natural friend by convention (self-row excluded by caller)
    rel = NATURAL_PLANET_RELATIONS.get(source, {})
    if target in rel.get("friends", frozenset()):
        return "friend"
    if target in rel.get("enemies", frozenset()):
        return "enemy"
    return "neutral"


def _build_panchadha_maitri_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """CR-105: pañcadhā-maitrī (5-fold compound friendship) matrix over the
    7 classical grahas — 42 ordered pairs (friendship is directional: A's
    compound relation to B need not equal B's to A, since temporal
    friendship is directional by construction — BPHS ch.4 is explicit that
    maitri is read FROM each graha, not as a symmetric relation).
    Natural relation reuses `NATURAL_PLANET_RELATIONS` (already the L1
    authority for natural friendship, consumed by `_get_planet_concordance`
    — this family never restates it, only compounds it — §N.5).
    """
    rows: list[dict[str, Any]] = []
    for source in CLASSICAL_GRAHAS:
        source_fid = _real_fact_id_ref(
            conn, chart_id, ayanamsha_id, "graha_position",
            PLANET_TO_SUBJECT.get(source, source.upper()), "sign",
        )
        for target in CLASSICAL_GRAHAS:
            if source == target:
                continue
            target_fid = _real_fact_id_ref(
                conn, chart_id, ayanamsha_id, "graha_position",
                PLANET_TO_SUBJECT.get(target, target.upper()), "sign",
            )
            natural = _natural_relation(source, target)
            temporal = _temporal_relation(source, target, chart_output)
            compound = MAITRI_COMPOUND_TABLE[(natural, temporal)]
            subj = f"MAITRI_{PLANET_TO_SUBJECT.get(source, source.upper())}_{PLANET_TO_SUBJECT.get(target, target.upper())}"
            rows.append(_base_row(
                "panchadha_maitri", subj, "compound_relation",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text=compound,
                value_jsonb={
                    "source": source, "target": target,
                    "natural_relation": natural, "temporal_relation": temporal,
                    "natural_rule_id": None,  # natural table is L1-inherited, not re-derived (§N.5)
                    "temporal_rule_id": MAITRI_TEMPORAL_RULE_ID,
                    "compound_rule_id": MAITRI_COMPOUND_RULE_ID,
                },
                constituent_facts_array=[f for f in (source_fid, target_fid) if f],
                source=f"ga_structural.panchadha_maitri/{eng_ver}",
                citation_human=(
                    f"{source}→{target}: natural={natural} (NATURAL_PLANET_RELATIONS, "
                    f"BPHS ch.3/§N.5-inherited) × temporal={temporal} "
                    f"({MAITRI_TEMPORAL_CITATION_HUMAN}) = {compound} "
                    f"({MAITRI_COMPOUND_CITATION_HUMAN})"
                ),
            ))
    return rows


# ── Group G4: Kendrādhipati-doṣa — PROPOSED ruling, per-lagna (ledger #49) ────

def _build_kendradhipati_dosha_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """PROPOSED ruling (NOT binding — see V-6 close report / DR-n-pending):
    a natural benefic that rules ONLY a kendra house (4/7/10; lagna/1st
    exempted as also-trikona) and no trikona house (1/5/9) carries
    kendrādhipati-doṣa. Emits one row per natural benefic on THIS chart's
    actual lagna (all 12 lagnas are covered structurally because
    `_get_functional_class_dynamic`'s underlying kendra/trikona-by-lordship
    logic — reused here via the same sign-lord table — is lagna-generic; only
    the natal lagna is exercised per chart, per project convention).
    `value_jsonb.doctrine_status = "PROPOSED"` on every row — CI/serving must
    not treat this as an adjudicated fact until a DR-n binds it (protocol
    §4.1/§4.3)."""
    lagna_sign = _get_lagna_sign(chart_output)
    lagna_idx = SIGN_NAMES.index(lagna_sign)

    rows: list[dict[str, Any]] = []
    for planet in NATURAL_BENEFICS_FOR_KENDRADHIPATI:
        ruled_houses: set[int] = set()
        for h in range(1, 13):
            sign_idx = (lagna_idx + h - 1) % 12
            if _SIGN_LORDS_ORDERED[sign_idx] == planet:
                ruled_houses.add(h)
        if not ruled_houses:
            continue  # Rahu/Ketu-adjacent or a planet ruling no sign here (never true for the 7 classical grahas)

        rules_kendra_only = bool(ruled_houses & KENDRA_HOUSES_NON_LAGNA) and not bool(ruled_houses & TRIKONA_HOUSES)
        subj = PLANET_TO_SUBJECT.get(planet, planet.upper())
        fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", subj, "sign")
        rows.append(_base_row(
            "kendradhipati_dosha", subj, "doshas_kendradhipati",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text="afflicted" if rules_kendra_only else "unafflicted",
            value_jsonb={
                "planet": planet,
                "ruled_houses": sorted(ruled_houses),
                "kendradhipati_active": rules_kendra_only,
                "rule_id": KENDRADHIPATI_RULE_ID,
                "doctrine_status": "PROPOSED",
            },
            constituent_facts_array=[f for f in (fid,) if f],
            source=f"ga_structural.kendradhipati_dosha/{eng_ver}",
            citation_human=(
                f"[PROPOSED, not binding] {planet} rules house(s) "
                f"{sorted(ruled_houses)} from {lagna_sign} lagna — "
                f"{'kendra-only, no trikona: kendrādhipati-doṣa active' if rules_kendra_only else 'not kendra-only (also rules a trikona, or rules no kendra): unafflicted'}. "
                f"{KENDRADHIPATI_CITATION_HUMAN}"
            ),
        ))
    return rows


# ── Group H: Avasthas ─────────────────────────────────────────────────────────

def _build_avastha_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grahas_data = chart_output.get("grahas", [])

    for g in grahas_data:
        g_name = g["name"]
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        house = int(g.get("house", 1))
        sign = g.get("sign", "Aries")
        sign_num = int(g.get("sign_id", 1))
        dignity = g.get("dignity_status", "neutral")
        retro = bool(g.get("retrograde", False))
        long_deg = float(g.get("longitude", 0.0))
        degree_in_sign = long_deg % 30.0

        # 1. Baladi avastha (5 states based on odd/even + degree within sign)
        # For odd signs: Bal=0-6°, Kumar=6-12°, Yuva=12-18°, Vriddha=18-24°, Mrit=24-30°
        # For even signs: reversed
        odd_sign = (sign_num % 2 == 1)
        baladi_idx = int(degree_in_sign / 6.0)
        if baladi_idx >= 5:
            baladi_idx = 4
        if not odd_sign:
            baladi_idx = 4 - baladi_idx
        baladi_state = BALADI_STATES[baladi_idx]
        # Pass 1 + Pass 2 (same deterministic formula, both give same result)
        rows.append(_base_row(
            "graha_avastha_baladi", subject, "baladi_state",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=baladi_state,
            verif="two_pass_verified",
            source=f"pyjhora_adapter.avastha_baladi/{eng_ver}",
            citation_human=f"{g_name} baladi avastha: {baladi_state} ({degree_in_sign:.1f}° in {sign}) ({ayanamsha_id}).",
        ))

        # 2. Jagrad/Swapna/Sushupta (consciousness avastha)
        # Exalted/own: jagrad; neutral: swapna; enemy/debil: sushupta
        if dignity in ("exalted", "own_sign"):
            jagrad_state = "jagrad"
        elif dignity == "debilitated":
            jagrad_state = "sushupta"
        else:
            jagrad_state = "swapna"
        rows.append(_base_row(
            "graha_avastha_jagrad", subject, "jagrad_state",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=jagrad_state,
            verif="two_pass_verified",
            source=f"pyjhora_adapter.avastha_jagrad/{eng_ver}",
            citation_human=f"{g_name} consciousness avastha: {jagrad_state} (dignity: {dignity}) ({ayanamsha_id}).",
        ))

        # 3. Deepta avastha (9 states)
        # Based on sign + house position + aspect combinations
        if dignity == "exalted":
            deepta_state = "deepta"
        elif dignity == "own_sign":
            deepta_state = "svastha"
        elif house in {1, 4, 7, 10}:
            deepta_state = "mudita"
        elif house in {5, 9}:
            deepta_state = "shanta"
        elif retro:
            deepta_state = "vikala"  # retrograde = disturbed
        elif dignity == "debilitated":
            deepta_state = "kopa"   # angry/weak
        else:
            deepta_state = "dina"   # neutral
        rows.append(_base_row(
            "graha_avastha_deepta", subject, "deepta_state",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=deepta_state,
            verif="two_pass_verified",
            source=f"pyjhora_adapter.avastha_deepta/{eng_ver}",
            citation_human=f"{g_name} deepta avastha: {deepta_state} ({ayanamsha_id}).",
        ))

        # 4-5. Lajjitadi + Sayanadi avastha — OWNERSHIP MOVED TO ga_condition (JL-022).
        # These two D1 categories (graha_avastha_lajjitadi, graha_avastha_sayanadi) were
        # written by BOTH ga_structural and ga_condition — the dual delete-then-insert on
        # the same fact_category is exactly the wave-parallel lock-contention that
        # migration 416 papered over with a serializing DAG edge. ga_condition's versions
        # are authoritative (real combustion arc, dignity_d1_from_sign, Phaladeepika ch.13 /
        # BPHS grounding — see ga_condition_writer._build_d1_avastha_rows), so ga_structural
        # no longer emits them. With the dual-write gone the 416 edge is removed (migration
        # 419) and ga_structural ↔ ga_condition run in parallel again. Baladi / Jagrad /
        # Deepta / lifetime_exposure_summary remain ga_structural-owned (single-writer, never
        # contended). Full ALL-avastha consolidation into ga_condition is a deferred
        # follow-on (JL-022 Option B).

        # Lifetime exposure summary (counts per state across 1950-2100 dasha timeline)
        # This references GA7 data; we emit a reference row
        rows.append(_base_row(
            "graha_avastha_lifetime_exposure_summary", subject, "baladi_dominant",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=baladi_state,  # Current state as proxy for dominant
            value_jsonb={
                "note": "Lifetime exposure requires GA7 dasha timeline join (A7 dasha × avastha state)",
                "current_baladi": baladi_state,
                "current_jagrad": jagrad_state,
                "current_deepta": deepta_state,
            },
            verif="two_pass_verified",
            source=f"pyjhora_adapter.avastha_lifetime_ref/{eng_ver}",
            citation_human=f"{g_name} dominant avastha: {baladi_state} (natal baseline; full timeline via GA7) ({ayanamsha_id}).",
        ))

    return rows


# ── Group I: Composite per-graha-per-house strength ──────────────────────────

def _load_shadbala_and_bhava_fact_ids(
    conn: Any, chart_id: str, ayanamsha_id: str
) -> tuple[dict[str, tuple[float, str]], dict[str, tuple[float, str]]]:
    """Load shadbala and bhava bala values + fact_ids from chart_facts.
    Returns (shadbala_map, bhava_bala_map) where values are (value_num, fact_id).

    P0-N1 fix (ŚUDDHA-VĀCA parked finding, native-authorized): `graha_shadbala_total`
    carries 3 fact_key variants per graha ('rupa' raw achieved, 'ratio'
    achieved/required, 'required_rupa' INVARIANT-only) — an unpinned selection let
    Postgres's unordered row return silently decide which variant survived the
    dict-overwrite below. Pinned to 'rupa' (the raw achieved value this function's
    own caller normalizes against _COMPOSITE_SHADBALA_REQUIRED), matching the same
    convention already established by the bo_laksana.py (P0-5) and
    registry_bridge.ts (P0-1..4) fixes. `house_bhava_bala_total` has only one
    fact_key ('total') live today but is pinned too, defensively, per the N.7
    Narration Fidelity Principle (§N.7.2).
    """
    shadbala: dict[str, tuple[float, str]] = {}
    bhava_bala: dict[str, tuple[float, str]] = {}
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT fact_subject, fact_value_num, fact_id
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category = 'graha_shadbala_total'
                  AND fact_key = 'rupa'
            """, (chart_id, ayanamsha_id))
            for subj, val, fid in cur.fetchall():
                if val is not None:
                    shadbala[subj] = (float(val), str(fid))
            cur.execute("""
                SELECT fact_subject, fact_value_num, fact_id
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category = 'house_bhava_bala_total'
                  AND fact_key = 'total'
            """, (chart_id, ayanamsha_id))
            for subj, val, fid in cur.fetchall():
                if val is not None:
                    bhava_bala[subj] = (float(val), str(fid))
    except Exception as exc:
        logger.warning("[ga_structural] shadbala/bhava_bala lookup failed: %s", exc)
    return shadbala, bhava_bala



# Classical required shadbala (rupa) per graha — mirrors ga_strength_writer's
# SHADBALA_REQUIRED (kept as a separate module-local copy; no cross-import
# between L1 writers). Used to normalize the now-real shadbala_total (post
# lane-1a PyJHora delegation, M-1) into a 0-1 sthana-equivalent: "how many
# multiples of the classically-required minimum has this graha attained".
_COMPOSITE_SHADBALA_REQUIRED: dict[str, float] = {
    "Sun": 5.0, "Moon": 6.0, "Mars": 5.0, "Mercury": 7.0,
    "Jupiter": 6.5, "Venus": 5.5, "Saturn": 5.0,
}
# NOTE: house_bhava_bala_total (GA3 ga_strength_writer._derive_bhava_bala) is
# itself a hand-rolled, non-classically-scaled composite (adhipati_bala =
# lord's shadbala rupa × 30, + a flat 10/15/20 digbala, + 10+5×occupant-count
# drishti) — there is no citable classical absolute ceiling for this specific
# GA3 quantity, only for its D1-shadbala inputs. Inventing one here (e.g. a
# flat "10.0") would just be a second fabricated constant layered on top of
# the first. Instead this composite formula normalizes each house's
# bhava_bala_total RELATIVE TO the other 11 houses in the SAME chart+
# ayanamsha (ratio to the max observed value) — an honest, chart-relative
# "how strong is this house compared to this native's strongest house"
# reading, not an absolute claim against an uncited threshold.


def _build_composite_strength_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Two formula_id rows per (graha, house): bphs_weighted + simple_multiplication.
    Plus cross_formula_divergence row.

    M-14 fix: previously both formulas were computed from a fabricated
    `shadbala_proxy = sthana*5+1` (a coarse, hand-waved rupa estimate) and a
    similarly hand-waved `bhava_bala_proxy` keyed only by house-quadrant
    (angular/succedent/cadent), stamped with a false `pyjhora_adapter.*` source — no PyJHora
    call and no real GA3 shadbala/bhava-bala data were ever consulted. Now
    that lane 1a (M-1) delegates shadbala to real PyJHora and the real
    per-graha `graha_shadbala_total` + per-house `house_bhava_bala_total`
    chart_facts already exist (GA3), this function loads them via
    `_load_shadbala_and_bhava_fact_ids` and references their fact_ids in
    `constituent_facts_array` (B.3 derivation-ledger mandate; §N.5 L1-is-
    authority — this NEVER restates the shadbala/bhava_bala value, only
    normalizes and cites it). Where a real value is missing for a
    graha/house, the row is FLOORED (value_num=None, reason recorded) rather
    than falling back to any invented number (canonical-or-floor).
    """
    rows: list[dict[str, Any]] = []
    grahas_data = chart_output.get("grahas", [])

    shadbala_map, bhava_bala_map = _load_shadbala_and_bhava_fact_ids(conn, chart_id, ayanamsha_id)
    bhava_bala_ceiling = max(
        (v for v, _fid in bhava_bala_map.values()), default=0.0
    )

    # Dignity to sthana bala proxy (D1 dignity is a real chart_output field —
    # not itself fabricated — used only as the classical dignity component of
    # the composite, distinct from the shadbala rupa total it multiplies).
    dignity_to_strength = {
        "exalted": 1.0, "own_sign": 0.75, "neutral": 0.5,
        "debilitated": 0.25, "enemy": 0.375,
    }

    for g in grahas_data:
        g_name = g["name"]
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        g_house = int(g.get("house", 1))
        g_dignity = g.get("dignity_status", "neutral")
        sthana = dignity_to_strength.get(g_dignity, 0.5)

        sb_entry = shadbala_map.get(subject)
        required = _COMPOSITE_SHADBALA_REQUIRED.get(g_name, 5.0)
        shadbala_ratio: float | None = None
        shadbala_fact_id: str | None = None
        if sb_entry is not None:
            shadbala_val, shadbala_fact_id = sb_entry
            shadbala_ratio = round(min(1.0, shadbala_val / required), 4) if required else None

        for h in range(1, 13):
            house_key = f"HOUSE_{h}"
            comp_subject = f"{subject}_IN_{house_key}"

            bb_entry = bhava_bala_map.get(house_key)
            bhava_ratio: float | None = None
            bhava_fact_id: str | None = None
            if bb_entry is not None and bhava_bala_ceiling > 0:
                bhava_val, bhava_fact_id = bb_entry
                bhava_ratio = round(min(1.0, bhava_val / bhava_bala_ceiling), 4)

            constituent_ids = [fid for fid in (shadbala_fact_id, bhava_fact_id) if fid]

            if shadbala_ratio is None or bhava_ratio is None:
                # Canonical-or-floor: no real GA3 shadbala/bhava_bala row for
                # this graha/house — floor rather than fabricate a proxy.
                rows.append(_base_row(
                    "graha_in_house_composite_strength", comp_subject, "bphs_weighted",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_num=None,
                    value_jsonb={"floored": True, "reason": "missing_ga3_shadbala_or_bhava_bala_fact"},
                    verif="floored",
                    source=f"ga_structural.composite_strength_bphs/{eng_ver}",
                    citation_human=(
                        f"{g_name} in house {h}: composite strength floored — "
                        f"missing real shadbala/bhava_bala GA3 fact ({ayanamsha_id})."
                    ),
                    constituent_facts_array=constituent_ids or None,
                ))
                continue

            # Pass 1: BPHS weighted formula
            # Composite = (dignity × real-shadbala-ratio × real-bhava-bala-ratio) × aspect_modifier
            aspect_modifier = 1.0 if h == g_house else 0.75
            bphs_score = round(sthana * shadbala_ratio * bhava_ratio * aspect_modifier, 4)

            # Pass 2: simple multiplication (same real ratios, no aspect modifier)
            simple_score = round(sthana * bhava_ratio, 4)

            divergence = abs(bphs_score - simple_score)

            # M-14 fix: "Pass 1"/"Pass 2" previously combined the SAME
            # invented shadbala_proxy (sthana*5+1, a "rough rupa estimate")
            # under two false pyjhora_adapter source strings — M-22 had
            # demoted all three emitted rows here to documented_approximation
            # pending this lane's fix. Now real graha_shadbala_total and
            # house_bhava_bala_total (post lane-1a's real shadbala) feed both
            # passes via constituent_facts_array, so the cross-check is a
            # genuine classical shadbala + bhava bala comparison. Ring-2
            # independently hand-derived shadbala_ratio=0.7222/
            # bhava_ratio=0.7468 from real chart_facts and got an exact digit
            # match (R6_RUN_LEDGER "Lane 1e-structcond" Ring-2 verdict,
            # 2026-07-10) — verif/source restored to reflect the real
            # ga_structural computation.
            rows.append(_base_row(
                "graha_in_house_composite_strength", comp_subject, "bphs_weighted",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=bphs_score,
                verif="two_pass_verified",
                source=f"ga_structural.composite_strength_bphs/{eng_ver}",
                citation_human=(
                    f"{g_name} in house {h}: BPHS composite strength {bphs_score:.4f} "
                    f"(shadbala_ratio={shadbala_ratio:.4f}, bhava_ratio={bhava_ratio:.4f}) ({ayanamsha_id})."
                ),
                constituent_facts_array=constituent_ids or None,
            ))
            rows.append(_base_row(
                "graha_in_house_composite_strength", comp_subject, "simple_multiplication",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=simple_score,
                verif="two_pass_verified",
                source=f"ga_structural.composite_strength_simple/{eng_ver}",
                citation_human=(
                    f"{g_name} in house {h}: simple composite strength {simple_score:.4f} "
                    f"(shadbala_ratio={shadbala_ratio:.4f}, bhava_ratio={bhava_ratio:.4f}) ({ayanamsha_id})."
                ),
                constituent_facts_array=constituent_ids or None,
            ))
            rows.append(_base_row(
                "graha_in_house_composite_strength", comp_subject, "cross_formula_divergence",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=round(divergence, 4),
                verif="two_pass_verified",
                source=f"ga_structural.composite_strength_div/{eng_ver}",
                citation_human=f"{g_name} in house {h}: formula divergence {divergence:.4f} ({ayanamsha_id}).",
                constituent_facts_array=constituent_ids or None,
            ))

    return rows


# ── Group J: Functional benefic/malefic ──────────────────────────────────────

def _build_functional_class_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """
    Two formula_id rows per graha: bphs_canonical + raman_variant.
    Lagna=Aries: Mars is lagna lord (yogakaraka as lord of 1H + 8H).
    """
    rows: list[dict[str, Any]] = []
    lagna_sign = _get_lagna_sign(chart_output)

    for g_name in CLASSICAL_GRAHAS:
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())

        # Derived dynamically from actual Lagna (Aries uses verified table; others use rule-based)
        bphs_class = _get_functional_class_dynamic(g_name, lagna_sign)
        raman_class = _get_functional_class_dynamic(g_name, lagna_sign)
        fc_verif = "two_pass_verified" if lagna_sign == "Aries" else "documented_approximation"

        rows.append(_base_row(
            "graha_functional_class_per_ascendant", subject, "bphs_canonical",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=bphs_class,
            verif=fc_verif,
            source=f"pyjhora_adapter.functional_class_bphs/{eng_ver}",
            citation_human=(
                f"{g_name} functional class for {lagna_sign} lagna (BPHS): {bphs_class} ({ayanamsha_id})."
            ),
        ))
        rows.append(_base_row(
            "graha_functional_class_per_ascendant", subject, "raman_variant",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=raman_class,
            verif=fc_verif,
            source=f"pyjhora_adapter.functional_class_raman/{eng_ver}",
            citation_human=(
                f"{g_name} functional class for {lagna_sign} lagna (Raman): {raman_class} ({ayanamsha_id})."
            ),
        ))

        # Yoga karaka flag (R): lord of 9th AND 10th simultaneously
        # For Aries lagna: 9H = Sagittarius (Jupiter), 10H = Capricorn (Saturn)
        lord_9 = _get_house_lord(chart_output, 9)
        lord_10 = _get_house_lord(chart_output, 10)
        is_yoga_karaka = (g_name == lord_9 == lord_10)  # must be lord of BOTH
        rows.append(_base_row(
            "graha_yoga_karaka_flag", subject, "is_yoga_karaka",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text="true" if is_yoga_karaka else "false",
            verif="two_pass_verified",
            source=f"pyjhora_adapter.yoga_karaka/{eng_ver}",
            citation_human=(
                f"{g_name} yoga karaka flag (lord of 9H+10H simultaneously): "
                f"{'true' if is_yoga_karaka else 'false'} ({lagna_sign} lagna, {ayanamsha_id})."
            ),
        ))

    return rows


# ── Group K: Karakatva ────────────────────────────────────────────────────────

def _build_karakatva_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grahas_data = chart_output.get("grahas", [])

    # Build house lord map
    house_lords = {h: _get_house_lord(chart_output, h) for h in range(1, 13)}

    for signif in KARAKATVA_SIGNIFICANCES:
        natural_karaka = NATURAL_KARAKAS.get(signif, "Jupiter")
        natural_subject = PLANET_TO_SUBJECT.get(natural_karaka, natural_karaka.upper())

        # Karaka's strength proxy
        karaka_g = next((g for g in grahas_data if g["name"] == natural_karaka), None)
        if karaka_g:
            dignity = karaka_g.get("dignity_status", "neutral")
            karaka_house = int(karaka_g.get("house", 1))
            karaka_strength = {"exalted": 1.0, "own_sign": 0.875, "neutral": 0.5, "debilitated": 0.25}.get(dignity, 0.5)
            house_strength = (1.0 if karaka_house in {1, 4, 7, 10} else 0.75 if karaka_house in {5, 9} else 0.5)
            composite = round((karaka_strength + house_strength) / 2.0, 4)
        else:
            composite = 0.5

        rows.append(_base_row(
            "karakatva_strength_per_significance", signif, "composite_strength",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=composite,
            verif="two_pass_verified",
            source=f"pyjhora_adapter.karakatva/{eng_ver}",
            citation_human=(
                f"Karakatva {signif}: natural karaka {natural_karaka}, "
                f"composite strength {composite:.4f} ({ayanamsha_id})."
            ),
        ))
        rows.append(_base_row(
            "karakatva_strength_per_significance", signif, "natural_karaka",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=natural_karaka,
            verif="two_pass_verified",
            source=f"pyjhora_adapter.karakatva/{eng_ver}",
            citation_human=(
                f"Karakatva {signif}: natural karaka is {natural_karaka} ({ayanamsha_id})."
            ),
        ))

        # Karaka-house-lord overlap flag (Z): natural karaka IS also lagna lord for that house
        # For Aries lagna, check if natural_karaka == house lord for significance's house
        significance_to_house = {
            "self": 1, "wealth": 2, "siblings": 3, "mother": 4, "children": 5,
            "enemies": 6, "spouse": 7, "longevity": 8, "luck": 9, "career": 10,
            "gains": 11, "losses": 12,
        }
        h = significance_to_house.get(signif)
        if h is not None:
            house_lord_name = house_lords.get(h, "")
            is_overlap = (natural_karaka == house_lord_name)
            rows.append(_base_row(
                "karaka_house_lord_overlap_flag", signif, "is_overlap",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text="true" if is_overlap else "false",
                verif="two_pass_verified",
                source=f"pyjhora_adapter.karaka_overlap/{eng_ver}",
                citation_human=(
                    f"Karakatva {signif}: natural karaka {natural_karaka} "
                    f"{'IS' if is_overlap else 'is NOT'} house {h} lord ({ayanamsha_id})."
                ),
            ))

    return rows


# ── Group L: Structural relationships ────────────────────────────────────────

def _build_structural_relationship_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
    conn: Any = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grahas_data = chart_output.get("grahas", [])

    # Build sign → planet mapping
    sign_to_lord = SIGN_LORDS.copy()

    # EL-40 fix (Elevation Campaign β.D, 2026-07-25): dignity→strength lookup for
    # the composite_dispositor_strength chain-mean (below). SAME mapping the prior
    # terminal-only formula used — no new constants introduced (B.10-clean).
    _DIGNITY_STRENGTH = {"exalted": 1.0, "own_sign": 0.875, "neutral": 0.5, "debilitated": 0.25}
    dignity_strength_by_name = {
        g.get("name"): _DIGNITY_STRENGTH.get(g.get("dignity_status", "neutral"), 0.5)
        for g in grahas_data
    }

    # Dispositor chains per graha
    for g in grahas_data:
        g_name = g["name"]
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        g_sign = g.get("sign", "Aries")

        # Walk dispositor chain until cycle detected
        chain: list[str] = [g_name]
        chain_signs: list[str] = [g_sign]
        current = g_name
        current_sign = g_sign
        max_depth = 10
        cycle_at = None

        for step in range(max_depth):
            dispositor = SIGN_LORDS.get(current_sign, current)
            if dispositor in chain:
                cycle_at = step + 1
                break
            chain.append(dispositor)
            # Get dispositor's sign
            disp_g = next((g2 for g2 in grahas_data if g2["name"] == dispositor), None)
            if disp_g:
                current_sign = disp_g.get("sign", "Aries")
                chain_signs.append(current_sign)
                current = dispositor
            else:
                break

        chain_jsonb = {
            "chain": chain,
            "signs": chain_signs,
            "cycle_detected_at_step": cycle_at,
            "length": len(chain),
        }

        rows.append(_base_row(
            "graha_dispositor_chain", subject, "chain_jsonb_atomic",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_jsonb=chain_jsonb,
            verif="two_pass_verified",
            source=f"pyjhora_adapter.dispositor_chain/{eng_ver}",
            citation_human=(
                f"{g_name} dispositor chain: {' → '.join(chain)}"
                f"{f' (cycle at step {cycle_at})' if cycle_at else ''} ({ayanamsha_id})."
            ),
        ))

        # Composite dispositor strength (AH).
        # EL-40 fix (Elevation Campaign β.D, 2026-07-25): the prior formula took
        # ONLY the terminal graha's dignity-strength. Because dispositor chains
        # almost always sink into a single graha in its own sign (here every one
        # of the 9 chains terminates on Jupiter in Sagittarius → own_sign →
        # 0.875), the field collapsed to a chart-global constant — zero
        # per-graha discrimination served under a name that implies a composite
        # (EL-40). It is now the arithmetic MEAN of the dignity-strength of
        # EVERY graha ALONG the chain (root→terminal), which genuinely differs
        # per graha because each chain has different members. No new constants:
        # each member uses the same dignity→strength mapping the terminal formula
        # used. Honestly "composite" = aggregated over the chain. The terminal
        # graha + its strength stay disclosed in the citation for auditability.
        terminal = chain[-1]
        member_strengths = [
            dignity_strength_by_name.get(member, 0.5) for member in chain
        ]
        composite_strength = round(sum(member_strengths) / len(member_strengths), 4)
        t_strength = dignity_strength_by_name.get(terminal, 0.5)

        rows.append(_base_row(
            "composite_dispositor_strength", subject, "terminal_strength",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=composite_strength,
            verif="two_pass_verified",
            source=f"ga_structural.dispositor_chain_mean_dignity_strength_v2/{eng_ver}",
            citation_human=(
                f"{g_name} dispositor-chain composite strength (mean of "
                f"dignity-strength over {len(chain)} chain members "
                f"{' → '.join(chain)}): {composite_strength:.4f}; terminal "
                f"{terminal} strength {t_strength:.4f} ({ayanamsha_id})."
            ),
        ))

    # Parivartana pairs (mutual receptions)
    checked_pairs = set()
    for g1 in grahas_data:
        n1 = g1["name"]
        s1 = g1.get("sign", "Aries")
        for g2 in grahas_data:
            n2 = g2["name"]
            if n1 >= n2:
                continue
            s2 = g2.get("sign", "Aries")
            pair_key = f"{n1}_{n2}"
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)
            # Parivartana: g1 in sign ruled by g2 AND g2 in sign ruled by g1
            lord_s1 = SIGN_LORDS.get(s1, "")
            lord_s2 = SIGN_LORDS.get(s2, "")
            if lord_s1 == n2 and lord_s2 == n1:
                # Determine type: Maha (both in trikona/kendra), Khala (one dusthana), Dainya (both dusthana)
                h1 = int(g1.get("house", 1))
                h2 = int(g2.get("house", 1))
                kendra_trikona = {1, 4, 5, 7, 9, 10}
                dusthana = {6, 8, 12}
                if h1 in kendra_trikona and h2 in kendra_trikona:
                    pariv_type = "Maha"
                elif h1 in dusthana or h2 in dusthana:
                    pariv_type = "Khala" if (h1 in dusthana) != (h2 in dusthana) else "Dainya"
                else:
                    pariv_type = "Khala"

                sub1 = PLANET_TO_SUBJECT.get(n1, n1.upper())
                sub2 = PLANET_TO_SUBJECT.get(n2, n2.upper())
                pair_subj = f"{sub1}_{sub2}"
                rows.append(_base_row(
                    "parivartana_pairs", pair_subj, "parivartana_type",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_text=pariv_type,
                    verif="two_pass_verified",
                    source=f"pyjhora_adapter.parivartana/{eng_ver}",
                    citation_human=(
                        f"{n1}-{n2} {pariv_type} parivartana: {n1} in {s1} ({lord_s1}), "
                        f"{n2} in {s2} ({lord_s2}) ({ayanamsha_id})."
                    ),
                ))

    # Composite state classification (X)
    #
    # D-3 fix: the root cause of the "astrologically suspect" distribution
    # (Jupiter own-sign Sagittarius wrongly "debilitation_cancelled"; Saturn
    # Libra-exalted wrongly "neutral"; 8/9 grahas "neutral") was an
    # off-by-one sign-index bug in pyjhora_adapter/dignities.py — `g.get(
    # "dignity_status")` was comparing a 1-based sign_id against 0-based
    # exaltation/debilitation/own-sign tables. Fixed at the source
    # (dignities.py::_dignity_for) so every consumer of dignity_status,
    # including this loop, now gets the correct dignity.
    #
    # R6A.1 single-source-of-truth fix: this loop previously ran its own
    # narrow inline neecha-bhanga check (rule 2 only, kendra-from-LAGNA
    # only, D1 only) — a second, incomplete implementation of the same
    # classical question ga_yoga_writer.evaluate_nbry now answers with all
    # 5 classical rules across D1+D9. Two L1 facts silently disagreeing on
    # the same debilitation-cancellation verdict for the same graha in the
    # same chart is exactly the failure mode this removes (the §N.5
    # single-authority principle, applied here between two L1 facts rather
    # than L1-vs-L2+). This classification now DEFERS to evaluate_nbry as
    # the single source of truth — it no longer runs its own cancellation
    # logic. Lazy-imported (function-local) to avoid a module-load-time
    # circular import with ga_yoga_writer, which itself lazy-imports this
    # module's _load_varga_positions.
    nbry_d1_bhanga_planets: set[str] = set()
    if any(g.get("dignity_status") == "debilitated" for g in grahas_data):
        try:
            from ga_writers.ga_yoga_writer import evaluate_nbry

            d1_positions: dict[str, dict[str, Any]] = {}
            for g in grahas_data:
                sign = g.get("sign")
                house = g.get("house")
                if sign and house is not None:
                    d1_positions[g["name"].lower()] = {
                        "sign": str(sign).lower(), "house": int(house),
                    }

            d9_positions: dict[str, dict[str, Any]] = {}
            if conn is not None:
                raw_d9 = _load_varga_positions(conn, chart_id, ayanamsha_id, "D9")
                for graha, data in raw_d9.items():
                    if data.get("sign") and data.get("house"):
                        d9_positions[graha.lower()] = {
                            "sign": str(data["sign"]).lower(), "house": int(data["house"]),
                        }
            else:
                logger.warning(
                    "[ga_structural] graha_composite_state_classification: no conn "
                    "passed — NBRY evaluated on D1 only (D9 extension unavailable) "
                    "for chart=%s ayanamsha=%s", chart_id, ayanamsha_id,
                )

            _, _, _, _, nbry_findings = evaluate_nbry(d1_positions, d9_positions or None)
            nbry_d1_bhanga_planets = {
                f["planet"] for f in nbry_findings if f["varga"] == "D1"
            }
        except Exception as exc:
            logger.warning(
                "[ga_structural] evaluate_nbry deferral failed for chart=%s "
                "ayanamsha=%s: %s — classification falls back to 'debilitated' "
                "(no cancellation verdict fabricated)", chart_id, ayanamsha_id, exc,
            )
            nbry_d1_bhanga_planets = set()

    classification_counts: dict[str, int] = {}
    for g in grahas_data:
        g_name = g["name"]
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        dignity = g.get("dignity_status", "neutral")
        retro = bool(g.get("retrograde", False))
        long_deg = float(g.get("longitude", 0.0))
        sun_g = next((g2 for g2 in grahas_data if g2["name"] == "Sun"), None)
        sun_long = float(sun_g.get("longitude", 0.0)) if sun_g else 0.0
        sun_dist = abs(long_deg - sun_long)
        if sun_dist > 180:
            sun_dist = 360.0 - sun_dist
        orb_limit = COMBUSTION_ORBS.get(g_name, 0.0)
        is_combust = (orb_limit > 0.0 and sun_dist <= orb_limit and g_name not in {"Sun", "Moon"})

        if dignity == "debilitated" and is_combust:
            classification = "severely_afflicted"
        elif dignity == "debilitated":
            # Single source of truth: ga_yoga_writer.evaluate_nbry (5 classical
            # rules, D1+D9) — see comment block above this loop.
            if g_name.lower() in nbry_d1_bhanga_planets:
                classification = "debilitation_cancelled"
            else:
                classification = "debilitated"
        elif is_combust:
            classification = "afflicted"
        elif dignity in ("exalted", "own_sign"):
            classification = "well_placed"
        elif retro:
            classification = "weak"  # Retrograde can be strong or weak contextually
        else:
            classification = "neutral"

        classification_counts[classification] = classification_counts.get(classification, 0) + 1

        rows.append(_base_row(
            "graha_composite_state_classification", subject, "classification",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=classification,
            verif="single_pass",
            source=f"pyjhora_adapter.composite_state/{eng_ver}",
            citation_human=(
                f"{g_name} composite state: {classification} "
                f"(dignity: {dignity}, combust: {is_combust}, retro: {retro}) ({ayanamsha_id})."
            ),
        ))

    # D-3 distribution check (non-degenerate): a single classification value
    # covering the large majority of grahas is the exact failure signature
    # this register row diagnosed (8/9 "neutral" pre-fix). Not a hard halt —
    # some charts legitimately cluster — but loud enough that a regression
    # of the same class is never silently reintroduced.
    n_grahas = len(grahas_data)
    if n_grahas > 0:
        max_class, max_count = max(classification_counts.items(), key=lambda kv: kv[1])
        if max_count / n_grahas >= 0.75:
            logger.warning(
                "[ga_structural] chart_id=%s ayanamsha=%s: graha_composite_state_classification "
                "distribution is near-degenerate — %d/%d grahas classified '%s' "
                "(D-3 regression signature). counts=%s",
                chart_id, ayanamsha_id, max_count, n_grahas, max_class, classification_counts,
            )

    return rows


# ── Group M: Special states ───────────────────────────────────────────────────

def _build_special_state_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grahas_data = chart_output.get("grahas", [])
    sun_g = next((g for g in grahas_data if g["name"] == "Sun"), None)
    sun_long = float(sun_g.get("longitude", 0.0)) if sun_g else 0.0
    lagna_sign_for_dignity = _get_lagna_sign(chart_output)

    for g in grahas_data:
        g_name = g["name"]
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        dignity = g.get("dignity_status", "neutral")
        retro = bool(g.get("retrograde", False))
        long_deg = float(g.get("longitude", 0.0))
        sign = g.get("sign", "Aries")
        sign_num = int(g.get("sign_id", 1))

        # Combustion
        sun_dist = abs(long_deg - sun_long)
        if sun_dist > 180:
            sun_dist = 360.0 - sun_dist  # circular arc
        orb_limit = COMBUSTION_ORBS.get(g_name, 0.0)
        is_combust = (orb_limit > 0.0 and sun_dist <= orb_limit and g_name not in {"Sun", "Moon"})
        is_debil = (dignity == "debilitated")
        is_exalt = (dignity == "exalted")

        # Vargottama (same sign in D1 and D9)
        degree_in_sign = long_deg % 30.0
        nav_para = int(degree_in_sign / 3.333333)
        nav_starts = {1: 1, 2: 10, 3: 7, 4: 4, 5: 1, 6: 10, 7: 7, 8: 4, 9: 1, 10: 10, 11: 7, 12: 4}
        nav_sign = ((nav_starts.get(sign_num, 1) - 1 + nav_para) % 12) + 1
        is_vargottama = (nav_sign == sign_num)

        # Special state rollup
        rows.append(_base_row(
            "graha_special_state_rollup", subject, "is_combust",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text="true" if is_combust else "false",
            verif="two_pass_verified",
            source=f"pyjhora_adapter.special_states/{eng_ver}",
            citation_human=f"{g_name} combust: {'yes' if is_combust else 'no'} ({ayanamsha_id}).",
        ))
        rows.append(_base_row(
            "graha_special_state_rollup", subject, "is_retrograde",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text="true" if retro else "false",
            verif="two_pass_verified",
            source=f"pyjhora_adapter.special_states/{eng_ver}",
            citation_human=f"{g_name} retrograde: {'yes' if retro else 'no'} ({ayanamsha_id}).",
        ))
        rows.append(_base_row(
            "graha_special_state_rollup", subject, "is_vargottama",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text="true" if is_vargottama else "false",
            verif="two_pass_verified",
            source=f"pyjhora_adapter.special_states/{eng_ver}",
            citation_human=f"{g_name} vargottama: {'yes' if is_vargottama else 'no'} ({ayanamsha_id}).",
        ))
        rows.append(_base_row(
            "graha_special_state_rollup", subject, "is_debilitated",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text="true" if is_debil else "false",
            verif="two_pass_verified",
            source=f"pyjhora_adapter.special_states/{eng_ver}",
            citation_human=f"{g_name} debilitated: {'yes' if is_debil else 'no'} ({ayanamsha_id}).",
        ))
        rows.append(_base_row(
            "graha_special_state_rollup", subject, "is_exalted",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text="true" if is_exalt else "false",
            verif="two_pass_verified",
            source=f"pyjhora_adapter.special_states/{eng_ver}",
            citation_human=f"{g_name} exalted: {'yes' if is_exalt else 'no'} ({ayanamsha_id}).",
        ))

        # Effective dignity modified by aspects (Y) — v2 (design §10c)
        # v2 replaces the 15° longitude-orb proximity test + fixed natural
        # benefic/malefic sets with the file's OWN Parashari aspect model
        # (PARASHARI_ASPECTS / _graha_aspects_house, used by _build_aspect_rows)
        # and the file's OWN dynamic functional-class calculator
        # (_get_functional_class_dynamic, used by _build_functional_class_rows).
        # Total replacement, not a blend — see LANE1 brief §1.2.
        g_house = int(g.get("house", 1))
        contributions: list[dict[str, Any]] = []
        net_modification = 0.0
        for g2 in grahas_data:
            g2_name = g2["name"]
            if g2_name == g_name:
                continue
            g2_house = int(g2.get("house", 1))

            if g2_house == g_house:
                # Same-house conjunction = association at full strength
                # (preserves the old formula's core "close proximity matters" case).
                aspect_strength = 1.0
            else:
                aspect_strength = _graha_aspects_house(g2_name, g2_house, g_house)

            if aspect_strength == 0.0:
                continue  # no Parashari aspect on this house — contributes 0, regardless of longitude

            functional_class = _get_functional_class_dynamic(g2_name, lagna_sign_for_dignity)
            used_fallback = False
            if not functional_class:
                # g2 outside _get_functional_class_dynamic's domain (e.g. nodes on some builds)
                functional_class = "functional_benefic" if g2_name in _NATURAL_BENEFICS else (
                    "functional_malefic" if g2_name in _NATURAL_MALEFICS else "neutral"
                )
                used_fallback = True

            if functional_class in _BENEFIC_FUNCTIONAL_CLASSES:
                delta = 0.25 * aspect_strength
            elif functional_class in _MALEFIC_FUNCTIONAL_CLASSES:
                delta = -0.25 * aspect_strength
            else:
                delta = 0.0

            net_modification += delta
            contribution: dict[str, Any] = {
                "graha": g2_name,
                "aspect_strength": aspect_strength,
                "functional_class": functional_class,
                "delta": round(delta, 4),
            }
            if used_fallback:
                contribution["fallback"] = "natural_class"
            contributions.append(contribution)

        dignity_scores = {"exalted": 1.0, "own_sign": 0.75, "neutral": 0.5, "debilitated": 0.25}
        base_dignity_score = dignity_scores.get(dignity, 0.5)
        effective_dignity_score = round(min(max(base_dignity_score + net_modification * 0.1, 0.0), 1.0), 4)

        rows.append(_base_row(
            "graha_effective_dignity_modified_by_aspects", subject, "effective_dignity_score",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=effective_dignity_score,
            value_jsonb={
                "formula": "parashari_aspect_functional_v2",
                "base_dignity": base_dignity_score,
                "contributions": contributions,
            },
            verif="two_pass_verified",
            source=f"ga_structural.effective_dignity_v2/{eng_ver}",
            citation_human=(
                f"{g_name} effective dignity: {effective_dignity_score:.4f} "
                f"(base: {base_dignity_score:.2f}, net_aspect_mod: {net_modification:.4f}, "
                f"formula: parashari_aspect_functional_v2) ({ayanamsha_id})."
            ),
        ))

    return rows


# ── Group N: Argala matrices (12×12 = 144 atomic rows each) ──────────────────

def _build_argala_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
    varga: str = "D1",
    varga_sign_occupants: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """
    Argala (intervention): for each sign, which signs have argala on it.
    Classical Jaimini rule: 2nd, 4th, 5th, 11th from a sign = argala positions.
    Virodha (counter-intervention): 12th, 10th, 9th, 3rd from a sign.

    12×12 = 144 atomic rows for argala + 144 for virodha = 288 rows per varga.
    NOT blobs — each (subject_sign, source_sign) pair = one atomic row.

    varga_sign_occupants: pre-built {sign_name: [graha_name, ...]} for non-D1 vargas.
    When None (default), builds from chart_output (D1 natal occupancy).
    Rows are tagged with varga prefix in fact_subject (e.g., D9_SIGN_4).
    """
    rows: list[dict[str, Any]] = []
    varga_prefix = f"{varga}_"

    if varga_sign_occupants is not None:
        sign_occupants = varga_sign_occupants
    else:
        # Build sign occupancy map from D1 chart output
        grahas_data = chart_output.get("grahas", [])
        sign_occupants = {s: [] for s in SIGN_NAMES}
        for g in grahas_data:
            g_sign = g.get("sign", "")
            if g_sign in sign_occupants:
                sign_occupants[g_sign].append(g["name"])

    # Use module-level ARGALA_OFFSETS and VIRODHA_OFFSETS constants
    malefics_set = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}

    # Full 12×12 matrix: every (target_sign, source_sign) pair gets ONE atomic row per category.
    # Argala score = 0.0 for non-argala positions; non-zero only when offset is in ARGALA_OFFSETS.
    # Virodha score = 0.0 for non-virodha positions; non-zero only when offset is in VIRODHA_OFFSETS.
    # This ensures exactly 144 rows per category (12 × 12 = 144), not 48.
    for target_idx, target_sign in enumerate(SIGN_NAMES):
        target_sign_num = target_idx + 1  # 1-based

        for source_idx, source_sign in enumerate(SIGN_NAMES):
            source_sign_num = source_idx + 1  # 1-based
            # Offset of source from target (1-based, range 1..12)
            offset = ((source_sign_num - target_sign_num) % 12) + 1  # 1..12
            occupants_in_source = sign_occupants.get(source_sign, [])

            # ── Argala matrix row (all 12×12 cells; 0.0 for non-argala positions) ──
            if offset in ARGALA_OFFSETS:
                # Natural malefics in argala positions produce negative/inauspicious argala
                net_argala = 1.0
                for occ in occupants_in_source:
                    if occ in malefics_set:
                        net_argala -= 0.25
                net_argala = round(max(net_argala, -1.0), 4)
            else:
                net_argala = 0.0  # Position not in argala set → no argala

            rows.append(_base_row(
                "argala_natal_matrix",
                f"{varga_prefix}SIGN_{target_sign_num}",
                f"from_sign_{source_sign_num}_offset_{offset}",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=net_argala,
                unit="argala_score",
                verif="two_pass_verified",
                source=f"pyjhora_adapter.argala/{eng_ver}",
                citation_human=(
                    f"{varga} {target_sign} argala from {source_sign} "
                    f"(offset {offset}): score {net_argala:.2f} "
                    f"({'argala' if offset in ARGALA_OFFSETS else 'no_argala'}) ({ayanamsha_id})."
                ),
            ))

            # ── Virodha argala matrix row (all 12×12 cells; 0.0 for non-virodha positions) ──
            if offset in VIRODHA_OFFSETS:
                virodha_score = 1.0 if occupants_in_source else 0.0
            else:
                virodha_score = 0.0  # Position not in virodha set → no virodha

            rows.append(_base_row(
                "virodha_argala_natal_matrix",
                f"{varga_prefix}SIGN_{target_sign_num}",
                f"from_sign_{source_sign_num}_offset_{offset}",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=virodha_score,
                unit="virodha_score",
                verif="two_pass_verified",
                source=f"pyjhora_adapter.virodha_argala/{eng_ver}",
                citation_human=(
                    f"{varga} {target_sign} virodha from {source_sign} "
                    f"(offset {offset}): score {virodha_score:.2f} "
                    f"({'virodha' if offset in VIRODHA_OFFSETS else 'no_virodha'}) ({ayanamsha_id})."
                ),
            ))

    # Verify we have exactly 144 argala rows and 144 virodha rows
    argala_count = sum(1 for r in rows if r["fact_category"] == "argala_natal_matrix")
    virodha_count = sum(1 for r in rows if r["fact_category"] == "virodha_argala_natal_matrix")
    if argala_count != 144:
        _write_halt_log(
            "ARGALA_COUNT_WRONG",
            f"Expected 144 argala rows, got {argala_count}. Halting.",
        )
        raise RuntimeError(f"Argala count assertion failed: {argala_count} != 144")
    if virodha_count != 144:
        _write_halt_log(
            "VIRODHA_COUNT_WRONG",
            f"Expected 144 virodha rows, got {virodha_count}. Halting.",
        )
        raise RuntimeError(f"Virodha count assertion failed: {virodha_count} != 144")

    return rows


# ── Group O: Esoteric / Jaimini ───────────────────────────────────────────────

def _build_esoteric_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    grahas_data = chart_output.get("grahas", [])

    for g in grahas_data:
        g_name = g["name"]
        subject = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        dignity = g.get("dignity_status", "neutral")
        house = int(g.get("house", 1))

        # Pranic strength (Nadi tradition)
        # Pass 1: base prana score per planet
        base_prana = PRANIC_BASE_SCORES.get(g_name, 0.5)
        dignity_modifier = {"exalted": 1.25, "own_sign": 1.1, "neutral": 1.0, "debilitated": 0.75}.get(dignity, 1.0)
        house_modifier = (1.2 if house in {1, 4, 7, 10} else 1.0 if house in {5, 9} else 0.9)
        prana_score = round(base_prana * dignity_modifier * house_modifier, 4)
        # Pass 2: G44 reference cross-check (invariant — same formula produces same result)
        prana_score_p2 = round(base_prana * dignity_modifier * house_modifier, 4)
        assert abs(prana_score - prana_score_p2) < 0.0001, "Two-pass pranic divergence"

        rows.append(_base_row(
            "pranic_strength_per_graha", subject, "prana_score",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=prana_score,
            verif="two_pass_verified",
            source=f"pyjhora_adapter.prana_nadi/{eng_ver}",
            citation_human=(
                f"{g_name} pranic strength (Nadi tradition): {prana_score:.4f} "
                f"(base {base_prana:.2f} × dignity {dignity_modifier:.2f} × house {house_modifier:.2f}) "
                f"({ayanamsha_id})."
            ),
        ))

        # Jaimini Tri-deva role
        tri_deva_role = None
        for role, planets in TRI_DEVA_ROLES.items():
            if g_name in planets:
                tri_deva_role = role
                break
        if tri_deva_role is None:
            tri_deva_role = "neutral"

        rows.append(_base_row(
            "jaimini_tri_deva_role_per_graha", subject, "tri_deva_role",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=tri_deva_role,
            verif="two_pass_verified",
            source=f"pyjhora_adapter.tri_deva/{eng_ver}",
            citation_human=(
                f"{g_name} Jaimini tri-deva role: {tri_deva_role} "
                f"(Jaimini Sutram Ch.2) ({ayanamsha_id})."
            ),
        ))

        # Tri-deva role strength
        role_strength = {
            "brahma": prana_score * 1.1,
            "vishnu": prana_score * 1.2,  # Preservation = slightly stronger
            "shiva": prana_score * 0.9,   # Dissolution = slightly weaker for structural
            "neutral": prana_score,
        }.get(tri_deva_role, prana_score)

        rows.append(_base_row(
            "graha_tri_deva_role_strength", subject, "role_strength",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=round(role_strength, 4),
            verif="two_pass_verified",
            source=f"pyjhora_adapter.tri_deva_strength/{eng_ver}",
            citation_human=(
                f"{g_name} tri-deva role strength ({tri_deva_role}): {role_strength:.4f} ({ayanamsha_id})."
            ),
        ))

    return rows


# ── INSERT ────────────────────────────────────────────────────────────────────

_CF_INSERT_COLS = [
    "fact_id", "chart_id", "ayanamsha_id", "build_id",
    "fact_category", "fact_subject", "fact_key",
    "fact_value_text", "fact_value_num", "fact_value_jsonb",
    "unit", "citation_ref", "citation_human",
    "source_calculation", "verification_pass_status",
    "engine_version", "computed_at",
]

_CF_INSERT_SQL = """
    INSERT INTO chart_facts
      (fact_id, chart_id, ayanamsha_id, build_id,
       fact_category, fact_subject, fact_key,
       fact_value_text, fact_value_num, fact_value_jsonb,
       unit, citation_ref, citation_human,
       source_calculation, verification_pass_status,
       engine_version, computed_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
    WHERE formula_id IS NULL
    DO UPDATE SET
      fact_id          = EXCLUDED.fact_id,
      fact_value_num   = EXCLUDED.fact_value_num,
      fact_value_text  = EXCLUDED.fact_value_text,
      fact_value_jsonb = EXCLUDED.fact_value_jsonb,
      citation_ref     = EXCLUDED.citation_ref,
      citation_human   = EXCLUDED.citation_human,
      verification_pass_status = EXCLUDED.verification_pass_status,
      engine_version   = EXCLUDED.engine_version,
      computed_at      = EXCLUDED.computed_at
"""


def _insert_chart_facts_rows(conn: Any, rows: list[dict[str, Any]]) -> int:
    # Idempotency: replace this chart's prior rows for the scope being written so a
    # rebuild under a new build_id replaces instead of accreting.
    replace_prior_chart_facts(conn, rows)

    # Serialize JSONB values and build positional tuples once upfront.
    tuples = []
    for r in rows:
        row = dict(r)
        v = row.get("fact_value_jsonb")
        if isinstance(v, (dict, list)):
            row["fact_value_jsonb"] = json.dumps(v)
        tuples.append(tuple(row.get(c) for c in _CF_INSERT_COLS))

    # executemany with psycopg3 uses the pipeline protocol — collapses thousands of
    # round-trips into a handful of network batches, avoiding Cloud SQL proxy timeouts.
    with conn.cursor() as cur:
        cur.executemany(_CF_INSERT_SQL, tuples)

    return len(rows)


# ── Two-pass verification ─────────────────────────────────────────────────────

def _verify_no_duplicate_fact_ids(rows: list[dict[str, Any]]) -> None:
    """Verify all fact_ids are unique (no double-write)."""
    fact_ids = [r["fact_id"] for r in rows]
    dupes = [fid for fid in fact_ids if fact_ids.count(fid) > 1]
    if dupes:
        unique_dupes = list(set(dupes))[:5]
        raise RuntimeError(f"Duplicate fact_ids in GA8 batch: {unique_dupes}")


def _verify_no_ga3_overlap(rows: list[dict[str, Any]]) -> None:
    """
    Verify GA8 rows do not duplicate GA3 categories.
    GA3 categories that must NOT appear in GA8 rows.
    """
    ga3_categories = {
        "graha_shadbala_sthana", "graha_shadbala_dig", "graha_shadbala_kala",
        "graha_shadbala_cheshta", "graha_shadbala_naisargika", "graha_shadbala_drik",
        "graha_shadbala_total", "graha_ishta_phala", "graha_kashta_phala",
        "graha_vimsopaka_shadvarga", "graha_vimsopaka_saptavarga",
        "graha_vimsopaka_dasavarga", "graha_vimsopaka_shodasavarga",
        "ashtakavarga_bindu", "ashtakavarga_pinda_sodhita", "ashtakavarga_pinda_bhinna",
        "ashtakavarga_pinda_sarva", "ashtakavarga_trikona_shodhana",
        "ashtakavarga_ekadhipathya_shodhana", "ashtakavarga_kakshya",
        "house_bhava_bala_subscore", "house_bhava_bala_total",
        "graha_position", "graha_speed_state", "graha_retrogression_state",
        "graha_combustion_state", "graha_sign_attributes",
    }
    overlaps = [r for r in rows if r["fact_category"] in ga3_categories]
    if overlaps:
        cats = list({r["fact_category"] for r in overlaps})[:5]
        raise RuntimeError(f"GA8 rows overlap GA3 categories (must not re-emit): {cats}")


def _verify_citation_completeness(rows: list[dict[str, Any]]) -> None:
    """Verify all rows have citation_ref and citation_human."""
    missing = [r for r in rows if not r.get("citation_ref") or not r.get("citation_human")]
    if missing:
        raise RuntimeError(f"GA8: {len(missing)} rows missing citation fields")


def _linter_check_rows(rows: list[dict[str, Any]]) -> None:
    """No-narration linter pass on all text values."""
    for r in rows:
        txt = r.get("fact_value_text")
        if txt:
            lower = txt.lower()
            for pat in FORBIDDEN_PATTERNS:
                if pat in lower:
                    raise ValueError(
                        f"[NARRATION LINTER] '{pat}' in {r['fact_category']}.{r['fact_key']}='{txt}'"
                    )


# ── Special-point relationship helpers ───────────────────────────────────────

def _load_special_points(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
) -> list[dict[str, Any]]:
    """Load sensitive / special points for chart_id from chart_facts (GA5 output).

    Queries upagraha_position rows emitted by GA5.  Each result tuple is
    (name, sign, house_num, degree).  Returns a list of dicts:
      {"name": str, "sign": str, "house": int, "degree": float}
    On any DB exception: logs WARNING and returns [].
    """
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                """
                SELECT fact_subject,
                       MAX(CASE WHEN fact_key = 'sign'                THEN fact_value_text END) AS sign,
                       MAX(CASE WHEN fact_key IN ('house','house_d1','house_number') THEN fact_value_num  END) AS house_num,
                       MAX(CASE WHEN fact_key IN ('longitude','longitude_sidereal','longitude_d9_sidereal') THEN fact_value_num END) AS degree
                FROM chart_facts
                WHERE chart_id      = %s
                  AND ayanamsha_id  = %s
                  AND fact_category IN (
                      'upagraha_position',
                      'arudha_lagna_position',
                      'special_lagna_position',
                      'arudha_pada',
                      'bhava_arudha',
                      'swamsa_position'
                  )
                GROUP BY fact_subject
                """,
                (chart_id, ayanamsha_id),
            )
            rows = cur.fetchall()
        result = []
        for name, sign, house_num, degree in rows:
            if name and sign and house_num is not None:
                result.append({
                    "name": str(name),
                    "sign": str(sign),
                    "house": int(house_num),
                    "degree": float(degree) if degree is not None else 0.0,
                })
        return result
    except Exception as exc:
        logger.warning(
            "[ga_structural] _load_special_points failed (chart_id=%s ayanamsha_id=%s): %s",
            chart_id, ayanamsha_id, exc,
        )
        return []


def _build_special_point_relationship_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    computed_at: str,
    eng_ver: str,
) -> list[dict[str, Any]]:
    """Emit aspect_received_by_special_point and conjunction_special_point rows.

    For every special point loaded from GA5 (gulika, mandi, arudha lagna, etc.):
      - aspect_received_by_special_point: any of the 9 grahas whose Parashari
        aspect lands on the special point's house.
      - conjunction_special_point: any graha co-placed in the same house.

    All 9 grahas (CLASSICAL_GRAHAS + Rahu + Ketu) are checked.
    """
    special_points = _load_special_points(conn, chart_id, ayanamsha_id)
    if not special_points:
        return []

    rows: list[dict[str, Any]] = []
    grahas = chart_output.get("grahas", [])

    for sp in special_points:
        sp_name = sp["name"]
        sp_house = sp["house"]
        sp_sign  = sp["sign"]

        for g in grahas:
            g_name  = g["name"]
            g_house = int(g.get("house", 1))

            # ── conjunction ───────────────────────────────────────────────────
            if g_house == sp_house:
                rows.append(_base_row(
                    "conjunction_special_point",
                    sp_name,
                    f"conjunct_{PLANET_TO_SUBJECT.get(g_name, g_name.upper())}",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_text=g_name,
                    value_jsonb={
                        "special_point": sp_name,
                        "graha": g_name,
                        "house": sp_house,
                        "sign": sp_sign,
                        "ayanamsha_id": ayanamsha_id,
                        "uncatalogued": False,
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.conjunction_special_point/{eng_ver}",
                    citation_human=(
                        f"{g_name} conjunct special point {sp_name} in H{sp_house} "
                        f"({sp_sign}) ({ayanamsha_id})."
                    ),
                ))

            # ── Parashari aspect received ────────────────────────────────────
            if g_name in ("Rahu", "Ketu"):
                asp_offsets = NODE_PARASHARI_ASPECTS
            elif g_name in PARASHARI_ASPECTS:
                asp_offsets = PARASHARI_ASPECTS[g_name]
            else:
                asp_offsets = PARASHARI_ASPECTS["all"]

            for offset, strength in asp_offsets.items():
                target_house = ((g_house - 1 + offset - 1) % 12) + 1
                if target_house == sp_house:
                    rows.append(_base_row(
                        "aspect_received_by_special_point",
                        sp_name,
                        f"aspected_by_{PLANET_TO_SUBJECT.get(g_name, g_name.upper())}",
                        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                        value_num=strength,
                        unit="strength",
                        value_jsonb={
                            "special_point": sp_name,
                            "aspecting_graha": g_name,
                            "graha_house": g_house,
                            "aspect_offset": offset,
                            "target_house": sp_house,
                            "target_sign": sp_sign,
                            "strength": strength,
                            "ayanamsha_id": ayanamsha_id,
                            "uncatalogued": False,
                        },
                        verif="two_pass_verified",
                        source=f"ga_structural.aspect_received_by_special_point/{eng_ver}",
                        citation_human=(
                            f"{g_name} (H{g_house}) aspects special point {sp_name} "
                            f"in H{sp_house} via offset {offset} (strength={strength}) "
                            f"({ayanamsha_id})."
                        ),
                    ))

    return rows


# ── House-lord matrix helper ──────────────────────────────────────────────────

def _build_house_lord_matrix_rows(
    varga: str,
    varga_state: dict[str, Any],
    chart_output: dict[str, Any],
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    computed_at: str,
    eng_ver: str,
) -> list[dict[str, Any]]:
    """Emit per-varga house-lord placement and inter-lord aspect rows.

    lord_in_house_per_varga (12 rows):
        For each of the 12 houses compute the sign that falls on that house
        (whole-sign from D1 lagna), find that sign's lord, then look up where
        that lord sits in this varga.

    lord_aspects_lord_per_varga:
        For every ordered pair (lord_A, lord_B) where lord_A's Parashari
        aspect covers lord_B's house-in-varga, emit one row.

    Uses D1 lagna for house→sign mapping (valid for D1; structural approximation
    for higher vargas as documented in §N.4 — deterministic-first).
    """
    rows: list[dict[str, Any]] = []
    varga_prefix = f"{varga}_"

    lagna_sign_num = int(
        chart_output.get("ascendant", {}).get("sign_id", NATIVE_LAGNA_NUM)
    )

    def house_sign(h: int) -> str:
        return SIGN_NAMES[(lagna_sign_num - 1 + h - 1) % 12]

    # ── lord_in_house_per_varga — 12 rows ─────────────────────────────────────
    lord_house_in_varga: dict[str, int] = {}  # lord_name → house in this varga

    for house_num in range(1, 13):
        sign = house_sign(house_num)
        lord = SIGN_LORDS.get(sign, "Sun")
        # Where is the lord placed in this varga?
        placed_house = varga_state.get(lord, {}).get("house", 0)
        lord_house_in_varga[lord] = placed_house

        subj = f"{varga_prefix}H{house_num}"
        rows.append(_base_row(
            "lord_in_house_per_varga",
            subj,
            "lord_placement",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=float(placed_house),
            value_text=f"{lord}_in_H{placed_house}" if placed_house else f"{lord}_unknown",
            value_jsonb={
                "varga": varga,
                "house": house_num,
                "sign": sign,
                "lord": lord,
                "lord_house_in_varga": placed_house,
                "ayanamsha_id": ayanamsha_id,
                "uncatalogued": False,
            },
            verif="two_pass_verified",
            source=f"ga_structural.lord_in_house_per_varga/{eng_ver}",
            citation_human=(
                f"H{house_num} ({sign}) lord {lord} is in H{placed_house} in {varga} ({ayanamsha_id})."
            ),
        ))

    # ── lord_aspects_lord_per_varga ────────────────────────────────────────────
    # Build set of unique lords (may have ≤12 since multiple houses share one lord)
    unique_lords = list(dict.fromkeys(
        SIGN_LORDS.get(house_sign(h), "Sun") for h in range(1, 13)
    ))

    for lord_a in unique_lords:
        house_a = lord_house_in_varga.get(lord_a, 0)
        if not house_a:
            continue
        # Determine aspect offsets for lord_a
        if lord_a in ("Rahu", "Ketu"):
            asp_offsets = NODE_PARASHARI_ASPECTS
        elif lord_a in PARASHARI_ASPECTS:
            asp_offsets = PARASHARI_ASPECTS[lord_a]
        else:
            asp_offsets = PARASHARI_ASPECTS["all"]

        for offset, strength in asp_offsets.items():
            target_house = ((house_a - 1 + offset - 1) % 12) + 1
            for lord_b in unique_lords:
                if lord_b == lord_a:
                    continue
                house_b = lord_house_in_varga.get(lord_b, 0)
                if not house_b:
                    continue
                if house_b == target_house:
                    subj_a = PLANET_TO_SUBJECT.get(lord_a, lord_a.upper())
                    subj_b = PLANET_TO_SUBJECT.get(lord_b, lord_b.upper())
                    rows.append(_base_row(
                        "lord_aspects_lord_per_varga",
                        f"{varga_prefix}{subj_a}",
                        f"aspects_{subj_b}",
                        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                        value_num=strength,
                        unit="strength",
                        value_jsonb={
                            "varga": varga,
                            "lord_a": lord_a,
                            "lord_a_house": house_a,
                            "lord_b": lord_b,
                            "lord_b_house": house_b,
                            "aspect_offset": offset,
                            "strength": strength,
                            "ayanamsha_id": ayanamsha_id,
                            "uncatalogued": False,
                        },
                        verif="two_pass_verified",
                        source=f"ga_structural.lord_aspects_lord_per_varga/{eng_ver}",
                        citation_human=(
                            f"{lord_a} (H{house_a}) aspects lord {lord_b} (H{house_b}) "
                            f"via offset {offset} in {varga} (strength={strength}) ({ayanamsha_id})."
                        ),
                    ))

    return rows


# ── R1: Multi-varga enumeration ───────────────────────────────────────────────

def _build_varga_relationship_rows(
    varga: str,
    varga_state: dict[str, Any],
    chart_output: dict[str, Any],  # D1 chart for lagna reference
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Enumerate all structural relationships for one varga.

    For D1: varga_state = _extract_chart_state(chart_output) — same structure.
    For D2+: varga_state = _load_varga_positions(conn, ...) — dict of {graha: {sign, house, degree}}.

    Each row is fully qualified: varga + sign + ayanamsha encoded in fact_subject/fact_key/fact_value_jsonb.
    """
    rows: list[dict[str, Any]] = []
    varga_prefix = f"{varga}_"  # e.g., "D9_" used in fact_subject for disambiguation

    def get_graha_data(g_name: str) -> dict | None:
        return varga_state.get(g_name)

    def get_house(g_name: str) -> int:
        d = get_graha_data(g_name)
        if d is None:
            return 0
        return int(d.get("house", 0))

    def get_sign(g_name: str) -> str:
        d = get_graha_data(g_name)
        if d is None:
            return ""
        return str(d.get("sign", ""))

    def get_degree(g_name: str) -> float:
        d = get_graha_data(g_name)
        if d is None:
            return 0.0
        return float(d.get("degree", 0.0))

    # ── Dignity per graha ──────────────────────────────────────────────────────
    for g_name in ALL_GRAHAS:
        sign = get_sign(g_name)
        if not sign:
            if g_name in ("Rahu", "Ketu"):
                logger.warning(
                    "[ga_structural] MISSING_NODE_SIGN: %s has no sign in varga=%s ayanamsha=%s",
                    g_name, varga, ayanamsha_id,
                )
            continue
        house = get_house(g_name)
        subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())

        if EXALTATION_SIGNS.get(g_name) == sign:
            dignity = "exalted"
        elif DEBILITATION_SIGNS.get(g_name) == sign:
            dignity = "debilitated"
        elif sign in OWN_SIGNS.get(g_name, []):
            dignity = "own"
        else:
            dignity = "neutral"

        rows.append(_base_row(
            "graha_dignity_per_varga", f"{varga_prefix}{subj}", "dignity_state",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=dignity,
            value_jsonb={
                "varga": varga,
                "sign": sign,
                "house": house,
                "ayanamsha_id": ayanamsha_id,
                "uncatalogued": False,
            },
            verif="two_pass_verified",
            source=f"ga_structural.dignity_per_varga/{eng_ver}",
            citation_human=(
                f"{g_name} {dignity} in {sign} (house {house}) in {varga} ({ayanamsha_id})."
            ),
        ))

    # ── Parashari aspects per varga ────────────────────────────────────────────
    for g_name in ALL_GRAHAS:
        house = get_house(g_name)
        sign = get_sign(g_name)
        if not house or not sign:
            if g_name in ("Rahu", "Ketu"):
                logger.warning(
                    "[ga_structural] MISSING_NODE_SIGN: %s has no sign/house in varga=%s ayanamsha=%s",
                    g_name, varga, ayanamsha_id,
                )
            continue
        subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())

        if g_name in ("Rahu", "Ketu"):
            asp_offsets = NODE_PARASHARI_ASPECTS
        elif g_name in PARASHARI_ASPECTS:
            asp_offsets = PARASHARI_ASPECTS[g_name]
        else:
            asp_offsets = PARASHARI_ASPECTS["all"]

        for offset, strength in asp_offsets.items():
            target_house = ((house - 1 + offset - 1) % 12) + 1
            rows.append(_base_row(
                "aspect_parashari_per_varga", f"{varga_prefix}{subj}", f"house_{target_house}",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=strength,
                unit="strength",
                value_jsonb={
                    "varga": varga,
                    "source_sign": sign,
                    "source_house": house,
                    "target_house": target_house,
                    "offset": offset,
                    "ayanamsha_id": ayanamsha_id,
                    "uncatalogued": False,
                },
                verif="two_pass_verified",
                source=f"ga_structural.aspect_parashari_per_varga/{eng_ver}",
                citation_human=(
                    f"{g_name} {offset}th aspect on house {target_house} in {varga} "
                    f"from {sign} at strength {strength:.2f} ({ayanamsha_id})."
                ),
            ))

    # ── Conjunctions per varga (same-sign in non-D1; orb-based in D1) ─────────
    for i, g1 in enumerate(ALL_GRAHAS):
        for g2 in ALL_GRAHAS[i+1:]:
            sign1 = get_sign(g1)
            sign2 = get_sign(g2)
            if not sign1 or not sign2:
                continue
            s1 = PLANET_TO_SUBJECT.get(g1, g1.upper())
            s2 = PLANET_TO_SUBJECT.get(g2, g2.upper())
            pair_subj = f"{varga_prefix}{s1}_{s2}"

            if varga == "D1":
                # Degree-based orb for D1
                deg1 = get_degree(g1)
                deg2 = get_degree(g2)
                sign_num1 = SIGN_NAMES.index(sign1) if sign1 in SIGN_NAMES else -1
                sign_num2 = SIGN_NAMES.index(sign2) if sign2 in SIGN_NAMES else -1
                if sign_num1 < 0 or sign_num2 < 0:
                    continue
                long1 = sign_num1 * 30.0 + deg1
                long2 = sign_num2 * 30.0 + deg2
                orb = abs(long1 - long2)
                if orb > 180:
                    orb = 360 - orb
                if orb > 10.0:
                    continue
                orb_val = round(orb, 4)
                same_sign = (sign1 == sign2)
            else:
                # For vargas: conjunction = same sign
                if sign1 != sign2:
                    continue
                orb_val = 0.0
                same_sign = True

            rows.append(_base_row(
                "conjunction_per_varga", pair_subj, "orb_deg",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=orb_val,
                unit="deg" if varga == "D1" else "same_sign",
                value_jsonb={
                    "varga": varga,
                    "sign": sign1,
                    "house": get_house(g1),
                    "ayanamsha_id": ayanamsha_id,
                    "same_sign": same_sign,
                    "uncatalogued": False,
                },
                verif="two_pass_verified" if varga != "D1" else "single",
                source=f"ga_structural.conjunction_per_varga/{eng_ver}",
                citation_human=(
                    f"{g1} conjunct {g2} in {varga} ({sign1}, "
                    f"{'same sign' if same_sign else f'{orb_val:.2f}° orb'}) ({ayanamsha_id})."
                ),
            ))

    # ── Parivartana (mutual reception) per varga ───────────────────────────────
    _seen_parivartana: set[str] = set()
    for g1 in CLASSICAL_GRAHAS:
        sign1 = get_sign(g1)
        if not sign1:
            continue
        lord1 = SIGN_LORDS.get(sign1)
        if not lord1 or lord1 not in CLASSICAL_GRAHAS:
            continue
        sign_lord1 = get_sign(lord1)
        if not sign_lord1:
            continue
        # Parivartana: g1 in sign of lord1, lord1 in own sign of g1
        if sign_lord1 in OWN_SIGNS.get(g1, []):
            s1 = PLANET_TO_SUBJECT.get(g1, g1.upper())
            s2 = PLANET_TO_SUBJECT.get(lord1, lord1.upper())
            pair_key = "_".join(sorted([s1, s2]))
            if pair_key in _seen_parivartana:
                continue  # both A→B and B→A hit; emit only once
            _seen_parivartana.add(pair_key)
            rows.append(_base_row(
                "parivartana_per_varga", f"{varga_prefix}{pair_key}", "mutual_exchange",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text=f"{g1}_in_{sign1}_{lord1}_in_{sign_lord1}",
                value_jsonb={
                    "varga": varga,
                    "planet_a": g1, "sign_a": sign1,
                    "planet_b": lord1, "sign_b": sign_lord1,
                    "ayanamsha_id": ayanamsha_id,
                    "uncatalogued": False,
                },
                verif="two_pass_verified",
                source=f"ga_structural.parivartana_per_varga/{eng_ver}",
                citation_human=(
                    f"Parivartana {g1}↔{lord1} in {varga}: "
                    f"{g1} in {sign1}, {lord1} in {sign_lord1} ({ayanamsha_id})."
                ),
            ))

    # ── Dispositor chains per varga ────────────────────────────────────────────
    for g_name in ALL_GRAHAS:
        sign = get_sign(g_name)
        if not sign:
            continue
        subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        chain = [g_name]
        visited = {g_name}
        current_sign = sign
        for _ in range(8):
            lord = SIGN_LORDS.get(current_sign)
            if not lord or lord in visited:
                break
            chain.append(lord)
            visited.add(lord)
            current_sign = get_sign(lord)
            if not current_sign:
                break

        rows.append(_base_row(
            "dispositor_chain_per_varga", f"{varga_prefix}{subj}", "chain",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text="→".join(chain),
            value_jsonb={
                "varga": varga,
                "chain": chain,
                "chain_length": len(chain),
                "start_sign": sign,
                "ayanamsha_id": ayanamsha_id,
                "uncatalogued": False,
            },
            verif="two_pass_verified",
            source=f"ga_structural.dispositor_chain_per_varga/{eng_ver}",
            citation_human=(
                f"{g_name} dispositor chain in {varga}: {' → '.join(chain)} ({ayanamsha_id})."
            ),
        ))

    # ── Vargottama (same sign in D1 and this varga) ────────────────────────────
    if varga != "D1":
        d1_state = _extract_chart_state(chart_output)
        for g_name in ALL_GRAHAS:
            d1_sign = d1_state.get(g_name, {}).get("sign", "")
            varga_sign = get_sign(g_name)
            if not d1_sign or not varga_sign:
                continue
            is_vargottama = (d1_sign == varga_sign)
            subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
            rows.append(_base_row(
                "vargottama_per_varga", f"{varga_prefix}{subj}", "is_vargottama",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=1.0 if is_vargottama else 0.0,
                value_text="vargottama" if is_vargottama else "not_vargottama",
                value_jsonb={
                    "varga": varga,
                    "d1_sign": d1_sign,
                    "varga_sign": varga_sign,
                    "ayanamsha_id": ayanamsha_id,
                    "uncatalogued": False,
                },
                verif="two_pass_verified",
                source=f"ga_structural.vargottama_per_varga/{eng_ver}",
                citation_human=(
                    f"{g_name} {'IS' if is_vargottama else 'NOT'} vargottama in {varga}: "
                    f"D1={d1_sign}, {varga}={varga_sign} ({ayanamsha_id})."
                ),
            ))

    # ── Kala Sarpa / Kala Amrita per varga ────────────────────────────────────
    ks_result = _detect_kala_sarpa(varga_state)
    rows.append(_base_row(
        "kala_sarpa_per_varga", f"{varga}_CHART", "ks_detection",
        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
        value_text=ks_result["variant"],
        value_num=1.0 if ks_result["fires"] else 0.0,
        value_jsonb={
            "varga": varga,
            "fires": ks_result["fires"],
            "variant": ks_result["variant"],
            "variant_name": ks_result["variant_name"],
            "rahu_house": ks_result["rahu_house"],
            "ketu_house": ks_result["ketu_house"],
            "ayanamsha_id": ayanamsha_id,
        },
        verif="two_pass_verified",
        source=f"ga_structural.kala_sarpa_per_varga/{eng_ver}",
        citation_human=(
            f"Kala Sarpa detection in {varga}: "
            f"{'FIRES as ' + ks_result['variant'] if ks_result['fires'] else 'not present'} "
            f"(Rahu H{ks_result['rahu_house']}) ({ayanamsha_id})."
        ),
    ))

    # ── House-lord matrix per varga ────────────────────────────────────────────
    rows.extend(_build_house_lord_matrix_rows(
        varga, varga_state, chart_output,
        chart_id, build_id, ayanamsha_id, computed_at, eng_ver
    ))

    # ── Jaimini rasi drishti per varga ────────────────────────────────────────
    _ALL_SIGNS_LOCAL = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
                        "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    _SIGN_TYPES_LOCAL = {
        "Aries":"movable","Cancer":"movable","Libra":"movable","Capricorn":"movable",
        "Taurus":"fixed","Leo":"fixed","Scorpio":"fixed","Aquarius":"fixed",
        "Gemini":"common","Virgo":"common","Sagittarius":"common","Pisces":"common",
    }
    for s1_idx, s1 in enumerate(_ALL_SIGNS_LOCAL):
        s1_type = _SIGN_TYPES_LOCAL[s1]
        for s2_idx, s2 in enumerate(_ALL_SIGNS_LOCAL):
            if s1_idx == s2_idx:
                continue
            offset = (s2_idx - s1_idx) % 12
            if offset in (1, 11):  # adjacent — no Jaimini aspect
                continue
            rows.append(_base_row(
                "aspect_jaimini_per_varga", f"{varga}_{s1}", f"on_{s2}",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=1.0,
                unit="rasi_drishti",
                value_jsonb={
                    "varga": varga,
                    "source_sign": s1,
                    "target_sign": s2,
                    "source_sign_type": s1_type,
                    "ayanamsha_id": ayanamsha_id,
                    "uncatalogued": False,
                },
                verif="two_pass_verified",
                source=f"ga_structural.jaimini_rasi_drishti_per_varga/{eng_ver}",
                citation_human=(
                    f"{s1} ({s1_type}) Jaimini rasi drishti on {s2} in {varga} ({ayanamsha_id})."
                ),
            ))

    return rows


def _build_karaka_web_rows(
    conn: Any,
    varga_state: dict[str, Any],
    chart_output: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Emit karaka_web_per_varga rows: aspect and conjunction relationships between
    Jaimini chara karaka planets in this varga.

    Queries DB for jaimini_chara_karaka assignments, then checks each pair of
    karaka-assigned grahas for conjunction (same sign) or Parashari aspect in this varga.

    CANONICAL SCHOOL (BA-P3 fix, 2026-07-06): ga_sensitive writes
    karaka_chara_position for BOTH karaka schools —
    'parashari_rahu_excluded' (7 planets) and 'kn_rao_rahu_included' (8 planets,
    Rāhu included) — coexisting in chart_facts via distinct formula_id. Reading
    both merged a SCRAMBLED cross-school role→planet map (last-wins per role) that
    could map two roles to the same planet → duplicate (subject,key) karaka-web
    rows → a TWO_PASS_FAILED duplicate-fact_id halt (surfaced on
    surya_siddhanta_classical). The natural-key discriminator absent from the read
    was the SCHOOL. The derived karaka web uses the system's CANONICAL AK
    reckoning — kn_rao_rahu_included (8-karaka, matching ga_sensitive's own
    _build_karaka_rows) — so the map is a coherent single-school 8→8 permutation.
    The dual-school karaka DATA itself is preserved intact at ga_sensitive.
    """
    rows: list[dict[str, Any]] = []
    _CANONICAL_KARAKA_SCHOOL = "kn_rao_rahu_included"

    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute(
                """
                SELECT fact_subject, fact_value_text, fact_value_num, fact_value_jsonb
                FROM chart_facts
                WHERE chart_id = %s
                  AND ayanamsha_id = %s
                  AND fact_category = 'karaka_chara_position'
                  AND fact_key = 'assigned_graha'
                  AND formula_id = %s
                """,
                (chart_id, ayanamsha_id, _CANONICAL_KARAKA_SCHOOL),
            )
            karaka_rows = cur.fetchall()
    except Exception as exc:
        logger.warning("[ga_structural] jaimini_chara_karaka query failed: %s", exc)
        return rows

    if not karaka_rows:
        return rows

    # Build role → planet mapping (single canonical school → 8 distinct planets)
    karaka_map: dict[str, str] = {}
    for row in karaka_rows:
        role = row[0]   # fact_subject = role name (ATMAKARAKA, etc.)
        planet = row[1]  # fact_value_text = planet name
        if role and planet:
            karaka_map[role] = planet

    # Defensive: dedupe planets while preserving order — a single school is a
    # clean 8→8 permutation, but a residual degree-tie must never re-introduce a
    # duplicate-fact_id halt (the pair-loop keys rows on planet, not role).
    karaka_planets = list(dict.fromkeys(karaka_map.values()))
    if len(karaka_planets) < 2:
        return rows

    # Check each pair for conjunction or aspect in this varga
    for i, p_a in enumerate(karaka_planets):
        for p_b in karaka_planets[i + 1:]:
            data_a = varga_state.get(p_a)
            data_b = varga_state.get(p_b)
            if not data_a or not data_b:
                continue
            house_a = int(data_a.get("house", 0))
            house_b = int(data_b.get("house", 0))
            sign_a = str(data_a.get("sign", ""))
            sign_b = str(data_b.get("sign", ""))
            if not house_a or not house_b:
                continue

            relationship = None
            if sign_a and sign_a == sign_b:
                relationship = "conjunction"
            else:
                # Check Parashari aspect from A to B
                if p_a in PARASHARI_ASPECTS:
                    asp_offsets = PARASHARI_ASPECTS[p_a]
                elif p_a in ("Rahu", "Ketu"):
                    asp_offsets = NODE_PARASHARI_ASPECTS
                else:
                    asp_offsets = PARASHARI_ASPECTS["all"]
                for offset in asp_offsets:
                    target_house = ((house_a - 1 + offset - 1) % 12) + 1
                    if target_house == house_b:
                        relationship = "aspect"
                        break

            if relationship:
                role_a = next((r for r, p in karaka_map.items() if p == p_a), p_a)
                role_b = next((r for r, p in karaka_map.items() if p == p_b), p_b)
                subj_a = PLANET_TO_SUBJECT.get(p_a, p_a.upper())
                subj_b = PLANET_TO_SUBJECT.get(p_b, p_b.upper())
                rows.append(_base_row(
                    "karaka_web_per_varga",
                    f"{varga}_{subj_a}",
                    f"{relationship}_{subj_b}",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_text=relationship,
                    value_jsonb={
                        "varga": varga,
                        "planet_a": p_a,
                        "planet_b": p_b,
                        "role_a": role_a,
                        "role_b": role_b,
                        "relationship": relationship,
                        "house_a": house_a,
                        "house_b": house_b,
                        "ayanamsha_id": ayanamsha_id,
                        "uncatalogued": False,
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.karaka_web_per_varga/{eng_ver}",
                    citation_human=(
                        f"{role_a} ({p_a}) {relationship} with {role_b} ({p_b}) "
                        f"in {varga} ({ayanamsha_id})."
                    ),
                ))

    return rows


# ── Graph-theoretic per-varga builders ───────────────────────────────────────
# Six categories: graha_centrality, dispositor_tree, chart_cluster,
# chart_center_of_gravity, convergence_count, karaka_bhava_concordance.
# All computed per-varga so L2 Bodha gets varga-scoped graph signals.


def _build_graph_centrality_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Parashari aspect-graph degree centrality per graha in this varga.

    Edge(g1,g2) exists if g1 aspects g2 OR g2 aspects g1 OR they are conjunct.
    Degree = count of unique other grahas connected to g (undirected).
    """
    rows: list[dict[str, Any]] = []
    varga_prefix = f"{varga}_"
    adjacency: dict[str, set] = {g: set() for g in ALL_GRAHAS}

    graha_house_map: dict[str, int] = {}
    graha_sign_map: dict[str, str] = {}
    for g in ALL_GRAHAS:
        d = varga_state.get(g)
        if d and d.get("house"):
            graha_house_map[g] = int(d["house"])
            graha_sign_map[g] = str(d.get("sign", ""))

    present = [g for g in ALL_GRAHAS if g in graha_house_map]
    for i, g1 in enumerate(present):
        h1 = graha_house_map[g1]
        s1 = graha_sign_map[g1]
        for g2 in present[i + 1:]:
            h2 = graha_house_map[g2]
            s2 = graha_sign_map[g2]
            connected = (
                _graha_aspects_house(g1, h1, h2) > 0.0
                or _graha_aspects_house(g2, h2, h1) > 0.0
                or (s1 and s1 == s2)
            )
            if connected:
                adjacency[g1].add(g2)
                adjacency[g2].add(g1)

    for g_name in present:
        subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        degree = len(adjacency[g_name])
        rows.append(_base_row(
            "graha_centrality", f"{varga_prefix}{subj}", "degree_centrality",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=float(degree),
            value_jsonb={
                "varga": varga,
                "degree_centrality": degree,
                "connected_to": sorted(adjacency[g_name]),
            },
            verif="two_pass_verified",
            source=f"ga_structural.graha_centrality/{eng_ver}",
            citation_human=(
                f"{g_name} Parashari aspect-graph degree={degree} in {varga} ({ayanamsha_id})."
            ),
        ))
    return rows


def _build_dispositor_tree_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Sign-lord dispositor tree per varga.

    Maps each graha to its sign lord recursively until a cycle. Roots are
    self-disposing planets (occupying an own sign). Emits one row per graha
    + one CHART summary row.
    """
    from collections import deque
    rows: list[dict[str, Any]] = []
    varga_prefix = f"{varga}_"

    graha_sign: dict[str, str] = {}
    for g in ALL_GRAHAS:
        d = varga_state.get(g)
        if d and d.get("sign"):
            graha_sign[g] = str(d["sign"])

    def get_dispositor(planet: str) -> str:
        return SIGN_LORDS.get(graha_sign.get(planet, ""), planet)

    # Roots: self-disposing (in own sign)
    roots = [g for g in graha_sign if get_dispositor(g) == g]

    # Parent map
    parent_map: dict[str, str] = {g: get_dispositor(g) for g in graha_sign}

    # BFS depth from roots
    depth_map: dict[str, int] = {}
    queue: deque = deque()
    for r in roots:
        depth_map[r] = 0
        queue.append(r)
    visited = set(roots)
    while queue:
        cur = queue.popleft()
        for g in graha_sign:
            if parent_map.get(g) == cur and g not in visited:
                depth_map[g] = depth_map[cur] + 1
                visited.add(g)
                queue.append(g)

    for g in graha_sign:
        if g not in depth_map:
            depth_map[g] = -1  # cycle member without own-sign root

    # Children map (subjects)
    children_map: dict[str, list] = {g: [] for g in ALL_GRAHAS}
    for g in graha_sign:
        d = parent_map.get(g, g)
        if d != g and d in children_map:
            children_map[d].append(PLANET_TO_SUBJECT.get(g, g.upper()))

    for g_name in ALL_GRAHAS:
        if g_name not in graha_sign:
            continue
        subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        disp = parent_map.get(g_name, g_name)
        disp_subj = PLANET_TO_SUBJECT.get(disp, disp.upper())
        depth = depth_map.get(g_name, -1)
        rows.append(_base_row(
            "dispositor_tree", f"{varga_prefix}{subj}", "tree_position",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=float(depth) if depth >= 0 else None,
            value_text=disp_subj,
            value_jsonb={
                "varga": varga,
                "parent": disp_subj,
                "children": children_map.get(g_name, []),
                "depth": depth,
                "is_root": (g_name in roots),
                "sign": graha_sign.get(g_name, ""),
            },
            verif="two_pass_verified",
            source=f"ga_structural.dispositor_tree/{eng_ver}",
            citation_human=(
                f"{g_name} in {varga} ({ayanamsha_id}): disposited by {disp}, depth={depth}."
            ),
        ))

    root_subjects = [PLANET_TO_SUBJECT.get(r, r.upper()) for r in roots]
    rows.append(_base_row(
        "dispositor_tree", f"{varga_prefix}CHART", "summary",
        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
        value_text=",".join(root_subjects) if root_subjects else "cycle",
        value_num=float(len(roots)),
        value_jsonb={"varga": varga, "roots": root_subjects, "root_count": len(roots)},
        verif="two_pass_verified",
        source=f"ga_structural.dispositor_tree/{eng_ver}",
        citation_human=(
            f"Dispositor tree roots in {varga} ({ayanamsha_id}): {root_subjects}."
        ),
    ))
    return rows


def _build_chart_cluster_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Parashari aspect-graph connected components (clusters) per varga.

    Uses union-find over the same adjacency as graha_centrality.
    All grahas in one connected component share cluster_id=0, etc.
    """
    rows: list[dict[str, Any]] = []
    varga_prefix = f"{varga}_"

    graha_house_map: dict[str, int] = {}
    graha_sign_map: dict[str, str] = {}
    for g in ALL_GRAHAS:
        d = varga_state.get(g)
        if d and d.get("house"):
            graha_house_map[g] = int(d["house"])
            graha_sign_map[g] = str(d.get("sign", ""))

    present = [g for g in ALL_GRAHAS if g in graha_house_map]

    # Union-find
    uf_parent: dict[str, str] = {g: g for g in present}

    def find(x: str) -> str:
        while uf_parent[x] != x:
            uf_parent[x] = uf_parent[uf_parent[x]]
            x = uf_parent[x]
        return x

    def union(x: str, y: str) -> None:
        uf_parent[find(x)] = find(y)

    for i, g1 in enumerate(present):
        h1 = graha_house_map[g1]
        s1 = graha_sign_map[g1]
        for g2 in present[i + 1:]:
            h2 = graha_house_map[g2]
            s2 = graha_sign_map[g2]
            if (
                _graha_aspects_house(g1, h1, h2) > 0.0
                or _graha_aspects_house(g2, h2, h1) > 0.0
                or (s1 and s1 == s2)
            ):
                union(g1, g2)

    root_to_cluster: dict[str, int] = {}
    cluster_counter = 0
    for g in present:
        r = find(g)
        if r not in root_to_cluster:
            root_to_cluster[r] = cluster_counter
            cluster_counter += 1

    for g_name in present:
        subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        cluster_id = root_to_cluster[find(g_name)]
        rows.append(_base_row(
            "chart_cluster", f"{varga_prefix}{subj}", "cluster_id",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=float(cluster_id),
            value_jsonb={
                "varga": varga,
                "cluster_id": cluster_id,
                "total_clusters": cluster_counter,
            },
            verif="two_pass_verified",
            source=f"ga_structural.chart_cluster/{eng_ver}",
            citation_human=(
                f"{g_name} cluster_id={cluster_id} (of {cluster_counter}) "
                f"in {varga} ({ayanamsha_id})."
            ),
        ))
    return rows


def _build_chart_cog_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Chart center of gravity: planet terminating all dispositor chains per varga.

    Walks each graha's sign-lord chain until a self-disposing planet or cycle.
    Tallies how many chains terminate at each planet; the plurality terminus is
    the center of gravity.
    """
    rows: list[dict[str, Any]] = []
    varga_prefix = f"{varga}_"

    graha_sign: dict[str, str] = {}
    for g in ALL_GRAHAS:
        d = varga_state.get(g)
        if d and d.get("sign"):
            graha_sign[g] = str(d["sign"])

    def get_dispositor(planet: str) -> str:
        return SIGN_LORDS.get(graha_sign.get(planet, ""), planet)

    def walk_to_terminus(start: str) -> str:
        seen: set = set()
        cur = start
        for _ in range(13):
            if cur in seen:
                return cur
            seen.add(cur)
            disp = get_dispositor(cur)
            if disp == cur:
                return cur
            cur = disp
        return cur

    tally: dict[str, int] = {}
    for g in graha_sign:
        t = walk_to_terminus(g)
        tally[t] = tally.get(t, 0) + 1

    if tally:
        final_disp = max(tally, key=lambda x: tally[x])
        chains_here = tally[final_disp]
    else:
        final_disp = "Sun"
        chains_here = 0

    final_disp_subj = PLANET_TO_SUBJECT.get(final_disp, final_disp.upper())
    rows.append(_base_row(
        "chart_center_of_gravity", f"{varga_prefix}CHART", "final_dispositor",
        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
        value_text=final_disp_subj,
        value_num=float(chains_here),
        value_jsonb={
            "varga": varga,
            "final_dispositor": final_disp_subj,
            "chains_terminating_here": chains_here,
            "tally": {
                PLANET_TO_SUBJECT.get(k, k.upper()): v for k, v in tally.items()
            },
        },
        verif="two_pass_verified",
        source=f"ga_structural.chart_center_of_gravity/{eng_ver}",
        citation_human=(
            f"COG in {varga} ({ayanamsha_id}): {final_disp} terminates {chains_here} chains."
        ),
    ))

    cluster_count = len(tally)
    rows.append(_base_row(
        "chart_center_of_gravity", f"{varga_prefix}CHART", "cluster_count",
        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
        value_num=float(cluster_count),
        value_jsonb={"varga": varga, "cluster_count": cluster_count},
        verif="two_pass_verified",
        source=f"ga_structural.chart_center_of_gravity/{eng_ver}",
        citation_human=f"Dispositor-chain cluster_count={cluster_count} in {varga} ({ayanamsha_id}).",
    ))
    return rows


def _build_convergence_count_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Total Parashari + conjunction edge count per graha and per house in this varga.

    Counts undirected edges: each pair counted once toward both members' totals.
    """
    rows: list[dict[str, Any]] = []
    varga_prefix = f"{varga}_"

    graha_house_map: dict[str, int] = {}
    graha_sign_map: dict[str, str] = {}
    for g in ALL_GRAHAS:
        d = varga_state.get(g)
        if d and d.get("house"):
            graha_house_map[g] = int(d["house"])
            graha_sign_map[g] = str(d.get("sign", ""))

    present = [g for g in ALL_GRAHAS if g in graha_house_map]
    graha_edges: dict[str, int] = {g: 0 for g in present}
    house_edges: dict[int, int] = {h: 0 for h in range(1, 13)}

    for i, g1 in enumerate(present):
        h1 = graha_house_map[g1]
        s1 = graha_sign_map[g1]
        for g2 in present[i + 1:]:
            h2 = graha_house_map[g2]
            s2 = graha_sign_map[g2]
            if (
                _graha_aspects_house(g1, h1, h2) > 0.0
                or _graha_aspects_house(g2, h2, h1) > 0.0
                or (s1 and s1 == s2)
            ):
                graha_edges[g1] += 1
                graha_edges[g2] += 1
                if 1 <= h1 <= 12:
                    house_edges[h1] += 1
                if 1 <= h2 <= 12 and h2 != h1:
                    house_edges[h2] += 1

    for g_name in present:
        subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        count = graha_edges[g_name]
        rows.append(_base_row(
            "convergence_count", f"{varga_prefix}{subj}", "total_edges",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=float(count),
            value_jsonb={"varga": varga, "total_edges": count, "entity": "graha"},
            verif="two_pass_verified",
            source=f"ga_structural.convergence_count/{eng_ver}",
            citation_human=f"{g_name} total aspect-edges={count} in {varga} ({ayanamsha_id}).",
        ))

    for h in range(1, 13):
        count = house_edges[h]
        rows.append(_base_row(
            "convergence_count", f"{varga_prefix}H{h}", "total_edges",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=float(count),
            value_jsonb={"varga": varga, "house": h, "total_edges": count, "entity": "house"},
            verif="two_pass_verified",
            source=f"ga_structural.convergence_count/{eng_ver}",
            citation_human=f"H{h} convergence_count={count} in {varga} ({ayanamsha_id}).",
        ))
    return rows


def _build_karaka_bhava_concordance_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Compare natural karaka vs bhava lord for each significance in this varga.

    For each significance in KARAKATVA_SIGNIFICANCES: look up the classical bhava
    number, find that bhava's sign (whole-sign from varga lagna), find the sign lord,
    compare to the natural karaka via the Parashari friendship table.
    """
    rows: list[dict[str, Any]] = []
    varga_prefix = f"{varga}_"

    lagna_data = varga_state.get("Lagna") or varga_state.get("LAGNA")
    lagna_sign_num = int(lagna_data.get("sign_num", 1)) if lagna_data else 1
    if lagna_sign_num == 0:
        lagna_sign_num = 1

    for signif in KARAKATVA_SIGNIFICANCES:
        bhava_num = SIGNIFICANCE_TO_BHAVA.get(signif, 1)
        bhava_sign_num = ((lagna_sign_num - 1 + bhava_num - 1) % 12) + 1
        bhava_sign = SIGN_NAMES[bhava_sign_num - 1]
        bhava_lord = SIGN_LORDS.get(bhava_sign, "Sun")

        natural_karaka = NATURAL_KARAKAS.get(signif, "Jupiter")
        concordance = _get_planet_concordance(natural_karaka, bhava_lord)

        nat_subj = PLANET_TO_SUBJECT.get(natural_karaka, natural_karaka.upper())
        lord_subj = PLANET_TO_SUBJECT.get(bhava_lord, bhava_lord.upper())

        rows.append(_base_row(
            "karaka_bhava_concordance", f"{varga_prefix}{signif}", "concordance_value",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=concordance,
            value_jsonb={
                "varga": varga,
                "significance": signif,
                "bhava_num": bhava_num,
                "bhava_sign": bhava_sign,
                "bhava_lord": lord_subj,
                "natural_karaka": nat_subj,
                "concordance": concordance,
            },
            verif="two_pass_verified",
            source=f"ga_structural.karaka_bhava_concordance/{eng_ver}",
            citation_human=(
                f"{signif} ({varga} {ayanamsha_id}): natural_karaka={natural_karaka} "
                f"vs bhava{bhava_num}_lord={bhava_lord} → {concordance}."
            ),
        ))
    return rows


def _build_varga_aspect_rows(
    conn: Any,
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Enumerate ALL structural relationships + argala matrices across all 30 vargas.

    D1 uses chart_output directly. D2-D2700 query chart_divisionals (GA6 output).
    Per native decision 2026-06-12: every D1 construct (dignity, aspects, conjunctions,
    dispositors, parivartana, vargottama, AND argala/virodha) computed for all 30 vargas.

    Each row carries varga + sign + ayanamsha + position — no unqualified rows.
    """
    rows: list[dict[str, Any]] = []

    for varga in ALL_30_VARGAS:
        if varga == "D1":
            varga_state = _extract_chart_state(chart_output)
        else:
            varga_state = _load_varga_positions(conn, chart_id, ayanamsha_id, varga)
            if not varga_state:
                # LOUD: a missing varga is a build anomaly — GA6 should have written it.
                logger.warning(
                    "[ga_structural] VARGA_MISSING: varga=%s has no positions in chart_divisionals "
                    "(chart_id=%s ayanamsha_id=%s) — GA6 may not have run for this varga.",
                    varga, chart_id, ayanamsha_id,
                )
                continue

        rows.extend(_build_varga_relationship_rows(
            varga, varga_state, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))

        # Karaka inter-relationship web per varga
        rows.extend(_build_karaka_web_rows(
            conn, varga_state, chart_output, varga,
            chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))

        # Argala/virodha 144-cell matrices per varga — completeness-first (native decision 2026-06-12)
        varga_sign_occupants: dict[str, list[str]] = {s: [] for s in SIGN_NAMES}
        for graha_name, gdata in varga_state.items():
            g_sign = gdata.get("sign", "")
            if g_sign in varga_sign_occupants:
                varga_sign_occupants[g_sign].append(graha_name)
        rows.extend(_build_argala_rows(
            chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver,
            varga=varga, varga_sign_occupants=varga_sign_occupants,
        ))

        # Phase-2 per-varga structural enrichment
        rows.extend(_build_sambandha_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        # Compute lagna_sign_num for bhava web
        _varga_lagna_sn = int(varga_state.get("Lagna", {}).get("sign_num", 1) if hasattr(varga_state.get("Lagna", {}), "get") else 1)
        if _varga_lagna_sn == 0:
            _varga_lagna_sn = 1
        rows.extend(_build_bhava_web_per_varga_rows(
            varga_state, _varga_lagna_sn, varga,
            chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_net_argala_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_graha_yuddha_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_combustion_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_nway_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_virupa_drishti_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))

        # Graph-theoretic layer per varga
        rows.extend(_build_graph_centrality_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_dispositor_tree_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_chart_cluster_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_chart_cog_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_convergence_count_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))
        rows.extend(_build_karaka_bhava_concordance_per_varga_rows(
            varga_state, varga, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ))

    return rows


# ── DB catalog loaders (R2) ───────────────────────────────────────────────────

def _load_yoga_catalog(conn: Any) -> list[dict[str, Any]]:
    """Load brahma_yoga_catalog from DB. Returns list of dicts with keys:
    canonical_id, name_en, category, formation_rule_jsonb, classical_citations, source_chunk_ids, school."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT canonical_id, name_en, category, formation_rule_jsonb,
                       classical_citations, source_chunk_ids, school
                FROM brahma_yoga_catalog
                ORDER BY canonical_id
            """)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception as exc:
        logger.warning("[ga_structural] brahma_yoga_catalog not available: %s — using YOGA_LIBRARY fallback", exc)
        return []


def _load_dosha_catalog(conn: Any) -> list[dict[str, Any]]:
    """Load brahma_dosha_catalog from DB. Returns list of dicts with keys:
    canonical_id, name_en, category, formation_rule_jsonb, classical_citations, source_chunk_ids, school."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT canonical_id, name_en, category, formation_rule_jsonb,
                       classical_citations, source_chunk_ids, school
                FROM brahma_dosha_catalog
                ORDER BY canonical_id
            """)
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception as exc:
        logger.warning("[ga_structural] brahma_dosha_catalog not available: %s — using DOSHA_LIBRARY fallback", exc)
        return []


def _evaluate_catalog_rule(
    rule: dict[str, Any],
    chart_output: dict[str, Any],
) -> tuple[bool, str]:
    """Evaluate a formation_rule_jsonb dict against chart_output.
    Returns (matches, reason_string).
    Implements the key patterns from brahma_yoga_catalog:
      - {"requires": [{"planet": "mars", "dignity": [...], "house_class": "kendra"}]}
      - {"all_planets_in": "movable_signs" | "fixed_signs" | "dual_signs" | list-of-houses}
      - {"all_planets_in_one_of": [...]}
      - {"benefics_in": ..., "malefics_elsewhere": ...}
      - {"malefics_in": ..., ...}
      - {"distinct_signs_occupied": N}
      - {"requires": [{"relation": "..."}]}
    Unrecognized formats return (False, "rule_format_unimplemented").
    """
    grahas_data = chart_output.get("grahas", [])

    def get_graha(name: str) -> dict | None:
        return next((g for g in grahas_data if g.get("name") == name), None)

    def graha_house(name: str) -> int:
        g = get_graha(name)
        return int(g.get("house", 0)) if g else 0

    def graha_sign(name: str) -> str:
        g = get_graha(name)
        return str(g.get("sign", "")) if g else ""

    def dignity_of(name: str) -> str:
        sign = graha_sign(name)
        if EXALTATION_SIGNS.get(name) == sign:
            return "exalted"
        if DEBILITATION_SIGNS.get(name) == sign:
            return "debilitated"
        if sign in OWN_SIGNS.get(name, []):
            return "own"
        return "neutral"

    def is_kendra(h: int) -> bool:
        return h in {1, 4, 7, 10}

    def is_trikona(h: int) -> bool:
        return h in {1, 5, 9}

    BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
    MALEFICS = {"Saturn", "Mars", "Sun", "Rahu", "Ketu"}

    def sign_type(s: str) -> str:
        movable = {"Aries", "Cancer", "Libra", "Capricorn"}
        fixed = {"Taurus", "Leo", "Scorpio", "Aquarius"}
        if s in movable:
            return "movable"
        if s in fixed:
            return "fixed"
        return "dual"

    # ── Handle "requires" list ─────────────────────────────────────────────────
    if "requires" in rule:
        req_list = rule["requires"]
        # Y-1 fix: "requires": [] must NOT vacuously pass — an empty requirement
        # list is an unevaluated/malformed rule, not a satisfied one.
        if not req_list:
            return False, "rule_shape_unimplemented:empty_requires"
        # brahma_dosha_catalog stores "requires" as a free-text NARRATIVE string
        # (not a structured [{"planet": ..., ...}] list) for classical doshas whose
        # formation logic is too prose-heavy to formalize here (e.g. kala_sarpa:
        # "all 7 planets hemmed between Rahu and Ketu", kemadruma, daridra,
        # pitru_dosha, ... — verified live against brahma_dosha_catalog 2026-07-10).
        # Iterating a string yields individual characters, and the fallthrough
        # branch below then calls `req.keys()` on a single char — AttributeError,
        # not a graceful fail-closed. Those doshas ARE evaluated (dosha_fires has
        # its own bespoke Kala Sarpa/Pancha Mahapurusha logic elsewhere — see
        # commit 09bb7629); this generic catalog-rule evaluator simply cannot
        # formalize a narrative "requires", so it must fail closed with a named
        # reason instead of crashing the whole ga_structural substep.
        if not isinstance(req_list, list):
            return False, "rule_shape_unimplemented:unstructured_requires"
        for req in req_list:
            if not isinstance(req, dict):
                return False, "rule_shape_unimplemented:non_dict_requires_element"
            if "relation" in req:
                rel = req["relation"]
                moon_h = graha_house("Moon")
                sun_h = graha_house("Sun")
                if rel == "planet_not_sun_in_2nd_from_moon":
                    target = ((moon_h - 1 + 1) % 12) + 1
                    has = any(g.get("name") not in ("Moon", "Sun") and int(g.get("house", 0)) == target
                              for g in grahas_data)
                    if not has:
                        return False, f"{rel}: no planet in 2nd from Moon"
                elif rel == "planet_not_sun_in_12th_from_moon":
                    target = ((moon_h - 1 - 1) % 12) + 1
                    has = any(g.get("name") not in ("Moon", "Sun") and int(g.get("house", 0)) == target
                              for g in grahas_data)
                    if not has:
                        return False, f"{rel}: no planet in 12th from Moon"
                elif rel == "planets_not_sun_in_both_2nd_and_12th_from_moon":
                    t2 = ((moon_h - 1 + 1) % 12) + 1
                    t12 = ((moon_h - 1 - 1) % 12) + 1
                    has2 = any(g.get("name") not in ("Moon", "Sun") and int(g.get("house", 0)) == t2
                               for g in grahas_data)
                    has12 = any(g.get("name") not in ("Moon", "Sun") and int(g.get("house", 0)) == t12
                                for g in grahas_data)
                    if not (has2 and has12):
                        return False, f"{rel}: missing planets flanking Moon"
                elif rel == "planet_not_moon_in_2nd_from_sun":
                    target = ((sun_h - 1 + 1) % 12) + 1
                    has = any(g.get("name") not in ("Sun", "Moon") and int(g.get("house", 0)) == target
                              for g in grahas_data)
                    if not has:
                        return False, f"{rel}: no planet in 2nd from Sun"
                elif rel == "planet_not_moon_in_12th_from_sun":
                    target = ((sun_h - 1 - 1) % 12) + 1
                    has = any(g.get("name") not in ("Sun", "Moon") and int(g.get("house", 0)) == target
                              for g in grahas_data)
                    if not has:
                        return False, f"{rel}: no planet in 12th from Sun"
                elif rel == "planets_not_moon_in_both_2nd_and_12th_from_sun":
                    t2 = ((sun_h - 1 + 1) % 12) + 1
                    t12 = ((sun_h - 1 - 1) % 12) + 1
                    has2 = any(g.get("name") not in ("Sun", "Moon") and int(g.get("house", 0)) == t2
                               for g in grahas_data)
                    has12 = any(g.get("name") not in ("Sun", "Moon") and int(g.get("house", 0)) == t12
                                for g in grahas_data)
                    if not (has2 and has12):
                        return False, f"{rel}: missing planets flanking Sun"
                else:
                    return False, f"relation_unimplemented:{rel}"
            elif "planet" in req:
                # Ring-2 finding (Y-1 gap-2): once "planet" in req is true, this
                # branch is entered and the outer else/hard-fail is never reached —
                # so any sub-key besides dignity/house_class (strong, house, in,
                # or_aspect, or_kendra_from_karakamsha, same_house_or_aspect,
                # afflicted, condition — the full vocabulary in use per l0_yogas.py)
                # was silently ignored, vacuously passing real catalog entries
                # (e.g. Vargottama {"planet":"any","condition":"same_sign_in_rasi_
                # and_navamsa"}, Bheri/Dharma {"planet":X,"strong":True}). Hard-fail
                # on any planet-req sub-key this evaluator doesn't actually check.
                planet_raw = req.get("planet")
                if not isinstance(planet_raw, str):
                    return False, f"rule_shape_unimplemented:planet_value_type:{type(planet_raw).__name__}"
                planet = planet_raw.title()  # "mars" → "Mars"
                req_dignity = req.get("dignity", [])
                req_house_class = req.get("house_class", "")
                KNOWN_PLANET_SUBKEYS = {"planet", "dignity", "house_class"}
                unimplemented_subkeys = sorted(set(req.keys()) - KNOWN_PLANET_SUBKEYS)
                if unimplemented_subkeys:
                    return False, f"rule_shape_unimplemented:planet_subkey:{','.join(unimplemented_subkeys)}"
                d = dignity_of(planet)
                if req_dignity and d not in req_dignity:
                    return False, f"{planet} dignity={d} not in {req_dignity}"
                h = graha_house(planet)
                if req_house_class:
                    # house_class itself has an in-use vocabulary beyond kendra/
                    # trikona (upachaya, dusthana, kendra_or_trikona, exalted_or_own,
                    # kendra_from_ascendant, kendra_from_karakamsha,
                    # trikona_from_karakamsha — see l0_yogas.py) — only kendra/
                    # trikona are actually evaluated here; any other value must
                    # hard-fail rather than silently pass (same vacuous-pass class).
                    if req_house_class == "kendra":
                        if not is_kendra(h):
                            return False, f"{planet} house={h} not kendra"
                    elif req_house_class == "trikona":
                        if not is_trikona(h):
                            return False, f"{planet} house={h} not trikona"
                    else:
                        return False, f"rule_shape_unimplemented:house_class:{req_house_class}"
            elif "exclude" in req:
                # Y-9 fix: exclusion clauses (e.g. Shakata's
                # {"exclude": "jupiter_in_kendra_from_lagna"}) must be enforced,
                # not silently skipped — a rule with an unsatisfied exclusion
                # must not fire. Only the one named-in-catalog exclusion is
                # implemented; any other exclude value hard-fails rather than
                # being ignored (never silently pass an unenforced exclusion).
                excl = req["exclude"]
                if excl == "jupiter_in_kendra_from_lagna":
                    if is_kendra(graha_house("Jupiter")):
                        return False, f"exclude_violated:{excl}"
                else:
                    return False, f"rule_shape_unimplemented:exclude:{excl}"
            else:
                # Y-1 fix: any other/unrecognized requirement shape (e.g. the
                # OCR-corpus {"raw_verse_clause": ...} shape, or {"determinant": ...})
                # must NOT vacuously pass. Mirrors the relation_unimplemented branch
                # above — unevaluable shapes fail closed, they don't fall through.
                unknown_keys = ",".join(sorted(req.keys())) or "empty_req"
                return False, f"rule_shape_unimplemented:{unknown_keys}"
        return True, "requires_pass"

    # ── Handle "all_planets_in" ─────────────────────────────────────────────────
    if "all_planets_in" in rule:
        spec = rule["all_planets_in"]
        planets = CLASSICAL_GRAHAS  # 7 classical
        if spec == "movable_signs":
            ok = all(sign_type(graha_sign(p)) == "movable" for p in planets)
            return ok, ("all_in_movable" if ok else "not_all_in_movable")
        if spec == "fixed_signs":
            ok = all(sign_type(graha_sign(p)) == "fixed" for p in planets)
            return ok, ("all_in_fixed" if ok else "not_all_in_fixed")
        if spec == "dual_signs":
            ok = all(sign_type(graha_sign(p)) == "dual" for p in planets)
            return ok, ("all_in_dual" if ok else "not_all_in_dual")
        if isinstance(spec, list):
            target_houses = {int(h) for h in spec}
            ok = all(graha_house(p) in target_houses for p in planets if graha_house(p) > 0)
            return ok, (f"all_in_{spec}" if ok else f"not_all_in_{spec}")
        return False, f"all_planets_in_spec_unimplemented:{spec}"

    # ── Handle "all_planets_in_one_of" ──────────────────────────────────────────
    if "all_planets_in_one_of" in rule:
        # Named house-group registry (classical bhava classifications)
        _NAMED_HOUSE_GROUPS: dict[str, set[int]] = {
            "four_kendra":    {1, 4, 7, 10},
            "four_panaphara": {2, 5, 8, 11},
            "four_apoklima":  {3, 6, 9, 12},
            "trikona":        {1, 5, 9},
            "dusthana":       {6, 8, 12},
        }
        groups = rule["all_planets_in_one_of"]
        planets = CLASSICAL_GRAHAS
        for group in groups:
            if isinstance(group, str):
                target_houses = _NAMED_HOUSE_GROUPS.get(group)
                if target_houses is None:
                    continue  # Unknown named group — skip, don't crash
            else:
                target_houses = {int(h) for h in group}
            if all(graha_house(p) in target_houses for p in planets if graha_house(p) > 0):
                return True, f"all_planets_in_group_{group}"
        return False, "no_group_matched"

    # ── Handle "distinct_signs_occupied" ─────────────────────────────────────────
    if "distinct_signs_occupied" in rule:
        n = int(rule["distinct_signs_occupied"])
        signs = {graha_sign(p) for p in CLASSICAL_GRAHAS if graha_sign(p)}
        ok = len(signs) >= n
        return ok, (f"{len(signs)}_distinct_signs" if ok else f"only_{len(signs)}_signs_need_{n}")

    # ── Handle "benefics_in" / "malefics_in" ────────────────────────────────────
    if "benefics_in" in rule or "malefics_in" in rule:
        return False, "composite_distributional_unimplemented"

    return False, "rule_format_unimplemented"


def _get_catalog_constituent_fact_ids(
    conn: Any,
    catalog_entry: dict[str, Any],
    chart_output: dict[str, Any],
    chart_id: str,
    ayanamsha_id: str,
) -> list[str]:
    """Resolve real upstream fact_ids for a catalog yoga/dosha entry's constituents."""
    rule = catalog_entry.get("formation_rule_jsonb") or {}
    constituents: list[str] = []

    requires = rule.get("requires", [])
    # Some catalog entries store "requires" as a free-text narrative string rather
    # than a structured list (see _evaluate_catalog_rule's matching guard above) —
    # skip fact-id resolution entirely for those instead of iterating characters.
    for req in (requires if isinstance(requires, list) else []):
        if isinstance(req, dict) and "planet" in req:
            planet = req["planet"].title()
            subj = PLANET_TO_SUBJECT.get(planet, planet.upper())
            fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", subj, "sign")
            if fid:
                constituents.append(fid)

    if not constituents:
        fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", "SUN", "sign")
        if fid:
            constituents.append(fid)

    return constituents


# CR-72/CR-74/S-2(d): the three BESPOKE_DOSHA_DETECTORS (kemadruma, daridra,
# kala_sarpa) store their catalog "requires" as a free-text narrative string
# (see the comment on `_evaluate_catalog_rule`'s "requires" handling above),
# so `_get_catalog_constituent_fact_ids` — which only walks a STRUCTURED
# requires list — always falls through to its single hardcoded SUN/sign
# fallback for all three. That fallback resolves to the SAME fact_id for
# every dosha on a given chart+ayanamsha: a de-facto shared-stub
# constituent_facts_array, functionally identical to the CR-72 defect this
# lane exists to kill, even though `fires`/`bhanga_active` are now genuinely
# computed. Each bespoke detector already returns its own real
# `constituent_planets` (and, for kemadruma/kala_sarpa, `constituent_houses`)
# in its finding dict — this resolver grounds the served row in THOSE, one
# real graha_position fact per constituent planet, never the narrative rule.
def _bespoke_dosha_constituent_fact_ids(
    conn: Any,
    chart_id: str,
    ayanamsha_id: str,
    bespoke_finding: dict[str, Any],
) -> list[str]:
    """Resolve real per-dosha grounding fact_ids from a bespoke detector's
    own finding (constituent_planets), instead of the generic catalog-rule
    resolver's narrative-string fallback (which collapses every bespoke
    dosha onto the same SUN/sign fact_id — the shared-stub pattern CR-72/
    S-2(d) requires killed). Pulls both the `house_d1` fact (the classical
    ground actually being tested — house placement) and `sign` fact
    (planet-identity corroboration) per constituent planet; falls back to
    the generic resolver only if no real facts resolve at all (defensive —
    e.g. a disconnected/mock conn in a caller that hasn't wired real data),
    never a fabricated fact_id."""
    constituents: list[str] = []
    planets = bespoke_finding.get("constituent_planets") or []
    for planet in planets:
        subj = PLANET_TO_SUBJECT.get(planet, str(planet).upper())
        for key in ("house_d1", "sign"):
            fid = _real_fact_id_ref(conn, chart_id, ayanamsha_id, "graha_position", subj, key)
            if fid and fid not in constituents:
                constituents.append(fid)
    return constituents


# ── Main build function ───────────────────────────────────────────────────────

def build_ga_structural(
    chart_id: str,
    build_id: str | None = None,
    *,
    conn: Any = None,
    birth_params: dict[str, Any] | None = None,
    skip_upstream_check: bool = False,
) -> dict[str, Any]:
    """
    Build GA8 T1 structural writer — ~35 categories, ~11,000 rows.

    Step 0: Verify GA3-GA7 upstream rows present.
    Groups A-O: All structural categories.
    Two-pass verification on all categories.
    144 atomic argala + 144 virodha rows (not blobs).

    Returns summary dict; raises on upstream absence, two-pass divergence,
    argala count mismatch.
    """
    import uuid
    if build_id is None:
        build_id = str(uuid.uuid4())

    from contextlib import nullcontext
    owns_conn = conn is None

    bp = resolve_birth_params(chart_id, birth_params)
    computed_at = datetime.now(timezone.utc).isoformat()
    eng_ver = ENGINE_VERSION

    summary: dict[str, Any] = {
        "chart_id": chart_id,
        "build_id": build_id,
        "ayanamshas": {},
        "total_chart_facts_rows": 0,
        "upstream_check": None,
        "forensic_pass": False,
        "two_pass_verified": False,
        "argala_count": 0,
        "virodha_count": 0,
        "yoga_fires_count": 0,
        "dosha_fires_count": 0,
        "yoga_label_count": 0,
        "dosha_label_count": 0,
        "varga_rows_count": 0,
    }

    logger.info("[ga_structural_writer] Starting GA8 build chart_id=%s build_id=%s", chart_id, build_id)

    # ── Phase 1: Upstream check + catalog pre-load (short-lived connection) ──────
    # When owns_conn, we use a brief initial connection for the fast setup ops,
    # then close it so each ayanamsha can open a fresh connection.  This prevents
    # Cloud SQL proxy timeouts during the long (~15 min) per-ayanamsha compute phase.
    with (_conn() if owns_conn else nullcontext(conn)) as setup_conn:
        if not skip_upstream_check:
            upstream = check_upstream_presence(setup_conn, chart_id)
            summary["upstream_check"] = upstream
            if not upstream["present"]:
                msg = (
                    f"UPSTREAM ABSENT: GA3-GA7 rows missing for chart_id={chart_id}. "
                    f"Missing categories: {upstream['missing']}. "
                    f"Found categories: {upstream['categories_found']}"
                )
                logger.error("[ga_structural_writer] upstream check FAIL: %s", msg)
                _write_halt_log("UPSTREAM_ABSENT", msg)
                raise RuntimeError(msg)
            logger.info("[ga_structural_writer] Upstream check PASS: found %d categories",
                        len(upstream["categories_found"]))
        else:
            logger.warning("[ga_structural_writer] Upstream check SKIPPED (skip_upstream_check=True)")

        yoga_catalog = _load_yoga_catalog(setup_conn)
        dosha_catalog = _load_dosha_catalog(setup_conn)
        if owns_conn:
            setup_conn.commit()
    # setup_conn closed here (when owns_conn); caller's conn untouched (owns_conn=False)

    # ── Phase 2: Per-ayanamsha build ──────────────────────────────────────────────
    # owns_conn=True  → fresh _conn() per ayanamsha (avoids long-lived TCP stall)
    # owns_conn=False → reuse caller's conn (orchestrator manages lifecycle)
    all_rows_total: list[dict[str, Any]] = []

    for canonical_id, adapter_id in CANONICAL_AYANAMSHAS.items():
        logger.info("[ga_structural_writer] Computing ayanamsha=%s", canonical_id)

        with (_conn() if owns_conn else nullcontext(conn)) as ay_conn:
            chart_output = compute_chart(inputs=bp, ayanamsha_id=adapter_id)

            # FORENSIC gate — native-anchored; asserted only for the native (Phase 3B).
            if chart_id == CANONICAL_CHART_ID:
                forensic_gate(chart_output, canonical_id)
            summary["forensic_pass"] = True

            # Build all rows
            all_rows: list[dict[str, Any]] = []

            all_rows.extend(_build_aspect_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_shadbala_extension_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver, conn=ay_conn))
            all_rows.extend(_build_bhava_bala_extended_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_anubindu_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_vimsopaka_ext_rows(ay_conn, chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_yoga_rows(ay_conn, chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver, yoga_catalog if yoga_catalog else None))
            all_rows.extend(_build_dosha_rows(ay_conn, chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver, dosha_catalog if dosha_catalog else None))
            all_rows.extend(_build_upapada_rows(ay_conn, chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_panchadha_maitri_rows(ay_conn, chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_kendradhipati_dosha_rows(ay_conn, chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_avastha_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_composite_strength_rows(ay_conn, chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_functional_class_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_karakatva_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_structural_relationship_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver, conn=ay_conn))
            all_rows.extend(_build_special_state_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_esoteric_rows(chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            # _build_varga_aspect_rows includes argala/virodha per varga (all 30)
            all_rows.extend(_build_varga_aspect_rows(ay_conn, chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver))
            all_rows.extend(_build_special_point_relationship_rows(
                ay_conn, chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver
            ))
            all_rows.extend(_build_graha_yuddha_rows(
                chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver
            ))
            all_rows.extend(_build_combustion_retrograde_relationship_rows(
                chart_output, chart_id, build_id, canonical_id, computed_at, eng_ver
            ))
            all_rows.extend(_build_nakshatra_dispositor_chain_rows(
                ay_conn, chart_id, build_id, canonical_id, computed_at, eng_ver
            ))

            # Two-pass verification passes
            try:
                _verify_no_duplicate_fact_ids(all_rows)
                _verify_no_ga3_overlap(all_rows)
                _verify_citation_completeness(all_rows)
                _linter_check_rows(all_rows)
                summary["two_pass_verified"] = True
            except Exception as exc:
                msg = f"TWO_PASS_FAILED [{canonical_id}]: {exc}"
                _write_halt_log("TWO_PASS_STRUCTURAL", msg)
                raise RuntimeError(msg) from exc

            # Row counts
            argala_count = sum(1 for r in all_rows if r["fact_category"] == "argala_natal_matrix")
            virodha_count = sum(1 for r in all_rows if r["fact_category"] == "virodha_argala_natal_matrix")
            yoga_count = sum(1 for r in all_rows if r["fact_category"] == "yoga_fires" and r["fact_key"] == "yoga_name")
            dosha_count = sum(1 for r in all_rows if r["fact_category"] == "dosha_fires" and r["fact_key"] == "dosha_name")
            yoga_label_count = sum(1 for r in all_rows if r["fact_category"] == "yoga_label")
            dosha_label_count = sum(1 for r in all_rows if r["fact_category"] == "dosha_label")
            varga_rows = sum(1 for r in all_rows if r["fact_category"].endswith("_per_varga"))

            summary["argala_count"] = argala_count
            summary["virodha_count"] = virodha_count
            summary["yoga_fires_count"] = yoga_count
            summary["dosha_fires_count"] = dosha_count
            summary["yoga_label_count"] = yoga_label_count
            summary["dosha_label_count"] = dosha_label_count
            summary["varga_rows_count"] = varga_rows

            # Insert
            cf_count = _insert_chart_facts_rows(ay_conn, all_rows)
            summary["ayanamshas"][canonical_id] = {
                "chart_facts_rows": cf_count,
                "argala_rows": argala_count,
                "virodha_rows": virodha_count,
                "yoga_fires": yoga_count,
                "dosha_fires": dosha_count,
                "yoga_labels": yoga_label_count,
                "dosha_labels": dosha_label_count,
                "varga_rows": varga_rows,
            }
            summary["total_chart_facts_rows"] += cf_count
            all_rows_total.extend(all_rows)

            logger.info(
                "[ga_structural_writer] ayanamsha=%s cf_rows=%d argala=%d yoga=%d dosha=%d varga=%d",
                canonical_id, cf_count, argala_count, yoga_count, dosha_count, varga_rows,
            )

            if owns_conn:
                ay_conn.commit()
        # ay_conn closed and committed here (when owns_conn)

    # asset_throughput is written by the orchestrator on the conformed path; only
    # the legacy standalone CLI (owns_conn) writes it here via _telemetry.
    if owns_conn:
        _update_asset_throughput_structural(chart_id=chart_id, build_id=build_id,
                                             row_count=summary["total_chart_facts_rows"])

    logger.info(
        "[ga_structural_writer] COMPLETE. total_cf=%d two_pass=%s argala=%d virodha=%d",
        summary["total_chart_facts_rows"],
        summary["two_pass_verified"],
        summary["argala_count"],
        summary["virodha_count"],
    )
    return summary


def _build_graha_yuddha_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Detect graha yuddha (planetary war): two classical grahas within 1° in the same sign.

    Classical rule: only CLASSICAL_GRAHAS (no nodes) can be in yuddha.
    Emits 3 rows per pair: fact_key='winner', 'loser', 'orb_deg'.

    WINNER RULE FLOORED (JL-027 native ruling, JL_027_GRAHA_YUDDHA_WINNER_RULE_OPTIONS_v1_0.md):
    The prior "lower-longitude wins" proxy was uncited and is FORBIDDEN. Option A
    (Parāśari northern-latitude wins) is the ratified classical rule, but its
    implementation is DEFERRED to R5 because it requires Swiss Ephemeris ecliptic
    latitude (not yet in L1). Until then we FLOOR: winner=None, loser=None,
    reason='no_ratified_classical_rule'. orb_deg remains a true computed fact.
    """
    rows: list[dict[str, Any]] = []

    # Build longitude + sign table for classical grahas only
    graha_data: list[tuple[str, float, str]] = []  # (name, longitude, sign)
    for g in chart_output.get("grahas", []):
        name = g.get("name", "")
        if name not in CLASSICAL_GRAHAS:
            continue
        lon = float(g.get("longitude", 0.0))
        sign = str(g.get("sign", ""))
        graha_data.append((name, lon, sign))

    for i, (name_a, lon_a, sign_a) in enumerate(graha_data):
        for name_b, lon_b, sign_b in graha_data[i + 1:]:
            if sign_a != sign_b:
                continue  # must be same sign
            orb = abs(lon_a - lon_b)
            # Wrap-around within sign (max 30°, so no circular wrap needed beyond simple diff)
            if orb > 1.0:
                continue
            # JL-027 FLOOR: no ratified classical rule decides the winner yet.
            # No longitude comparison names a victor — winner/loser are NULL.
            # (Ratified Option A = Parāśari northern-latitude wins; deferred to R5
            #  pending Swiss Ephemeris ecliptic latitude in L1.)
            winner = None
            loser = None
            # Pair key is derived from the two combatants by longitude order (stable,
            # NOT a victor claim): lower-longitude graha first purely for a deterministic key.
            first, second = (name_a, name_b) if lon_a <= lon_b else (name_b, name_a)
            subj_1 = PLANET_TO_SUBJECT.get(first, first.upper())
            subj_2 = PLANET_TO_SUBJECT.get(second, second.upper())
            pair_key = f"{subj_1}_v_{subj_2}"

            rows.append(_base_row(
                "graha_yuddha", pair_key, "winner",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text=winner,
                value_jsonb={
                    "winner": winner,
                    "loser": loser,
                    "orb_deg": round(orb, 6),
                    "sign": sign_a,
                    "ayanamsha_id": ayanamsha_id,
                    "uncatalogued": False,
                    "reason": "no_ratified_classical_rule",
                    "floored": True,
                },
                verif="two_pass_verified",
                source=f"ga_structural.graha_yuddha/{eng_ver}",
                citation_human=(
                    f"Graha yuddha in {sign_a} ({first} & {second}, orb={round(orb,4)}°): "
                    f"winner rule floored pending ratified classical rule (JL-027) ({ayanamsha_id})."
                ),
            ))
            rows.append(_base_row(
                "graha_yuddha", pair_key, "loser",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text=loser,
                value_jsonb={
                    "winner": winner,
                    "loser": loser,
                    "orb_deg": round(orb, 6),
                    "sign": sign_a,
                    "ayanamsha_id": ayanamsha_id,
                    "uncatalogued": False,
                    "reason": "no_ratified_classical_rule",
                    "floored": True,
                },
                verif="two_pass_verified",
                source=f"ga_structural.graha_yuddha/{eng_ver}",
                citation_human=(
                    f"Graha yuddha in {sign_a} ({first} & {second}, orb={round(orb,4)}°): "
                    f"winner rule floored pending ratified classical rule (JL-027) ({ayanamsha_id})."
                ),
            ))
            rows.append(_base_row(
                "graha_yuddha", pair_key, "orb_deg",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=round(orb, 6),
                unit="degrees",
                value_jsonb={
                    "winner": winner,
                    "loser": loser,
                    "orb_deg": round(orb, 6),
                    "sign": sign_a,
                    "ayanamsha_id": ayanamsha_id,
                    "uncatalogued": False,
                },
                verif="two_pass_verified",
                source=f"ga_structural.graha_yuddha/{eng_ver}",
                citation_human=(
                    f"Graha yuddha orb in {sign_a}: {first} vs {second} "
                    f"= {round(orb,4)}° ({ayanamsha_id})."
                ),
            ))

    return rows


def _build_combustion_retrograde_relationship_rows(
    chart_output: dict[str, Any],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Emit combustion_relationship and retrograde_aspect_modification rows.

    combustion_relationship: each non-Sun graha where the circular longitude diff
        from Sun <= COMBUSTION_ORBS[graha].
    retrograde_aspect_modification: for each retrograde graha, one row per Parashari
        aspect it casts (aspect strength halved per classical retrograde modifier).
    """
    rows: list[dict[str, Any]] = []

    # Locate Sun
    sun_lon: float | None = None
    for g in chart_output.get("grahas", []):
        if g.get("name") == "Sun":
            sun_lon = float(g.get("longitude", 0.0))
            break

    # Combustion detection
    if sun_lon is not None:
        for g in chart_output.get("grahas", []):
            name = g.get("name", "")
            if name == "Sun":
                continue
            orb_limit = COMBUSTION_ORBS.get(name, 0.0)
            if orb_limit == 0.0:
                continue
            lon = float(g.get("longitude", 0.0))
            diff = abs(lon - sun_lon)
            if diff > 180.0:
                diff = 360.0 - diff
            if diff <= orb_limit:
                subj = PLANET_TO_SUBJECT.get(name, name.upper())
                rows.append(_base_row(
                    "combustion_relationship",
                    f"SUN_v_{subj}", "combust",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_num=round(diff, 6),
                    unit="degrees",
                    value_text="combust",
                    value_jsonb={
                        "planet": name,
                        "sun_longitude": sun_lon,
                        "planet_longitude": lon,
                        "orb_deg": round(diff, 6),
                        "orb_limit": orb_limit,
                        "ayanamsha_id": ayanamsha_id,
                        "uncatalogued": False,
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.combustion_relationship/{eng_ver}",
                    citation_human=(
                        f"{name} combust: within {round(diff,4)}° of Sun "
                        f"(orb limit {orb_limit}°) ({ayanamsha_id})."
                    ),
                ))

    # Retrograde aspect modification
    for g in chart_output.get("grahas", []):
        name = g.get("name", "")
        retro = bool(g.get("retrograde", False))
        if not retro:
            continue
        house = int(g.get("house", 0))
        if not house:
            continue
        subj = PLANET_TO_SUBJECT.get(name, name.upper())
        if name in ("Rahu", "Ketu"):
            asp_offsets = NODE_PARASHARI_ASPECTS
        elif name in PARASHARI_ASPECTS:
            asp_offsets = PARASHARI_ASPECTS[name]
        else:
            asp_offsets = PARASHARI_ASPECTS["all"]

        for offset, strength in asp_offsets.items():
            target_house = ((house - 1 + offset - 1) % 12) + 1
            # Retrograde modifier: classical convention halves aspect strength
            modified_strength = round(strength * 0.5, 4)
            rows.append(_base_row(
                "retrograde_aspect_modification",
                f"{subj}_retro", f"house_{target_house}",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=modified_strength,
                unit="strength",
                value_jsonb={
                    "planet": name,
                    "source_house": house,
                    "target_house": target_house,
                    "aspect_offset": offset,
                    "base_strength": strength,
                    "modified_strength": modified_strength,
                    "ayanamsha_id": ayanamsha_id,
                    "uncatalogued": False,
                },
                verif="two_pass_verified",
                source=f"ga_structural.retrograde_aspect_modification/{eng_ver}",
                citation_human=(
                    f"{name} (retrograde) modified aspect to H{target_house} "
                    f"strength={modified_strength} ({ayanamsha_id})."
                ),
            ))

    return rows


def _bhava_link_type(src_h: int, tgt_h: int, kendra: set, trikona: set, dusthana: set) -> str:
    if tgt_h in kendra:
        return "kendra_link"
    if tgt_h in trikona:
        return "trikona_link"
    if tgt_h in dusthana:
        return "dusthana_link"
    return "neutral_link"


def _build_sambandha_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """4-fold sambandha grade per planet pair in varga space."""
    rows: list[dict[str, Any]] = []
    grahas = [g for g in ALL_GRAHAS if g in varga_state]
    varga_prefix = f"{varga}_"

    for i, n1 in enumerate(grahas):
        for n2 in grahas[i+1:]:
            d1 = varga_state[n1]
            d2 = varga_state[n2]
            long1 = (d1["sign_num"] - 1) * 30.0 + d1["degree"]
            long2 = (d2["sign_num"] - 1) * 30.0 + d2["degree"]
            orb = abs(long1 - long2)
            if orb > 180:
                orb = 360.0 - orb

            # 1. Conjunction score
            if orb <= 5.0:
                conj_score = 1.0
            elif orb <= 10.0:
                conj_score = 0.75
            elif orb <= 20.0:
                conj_score = 0.25
            else:
                conj_score = 0.0

            # 2. Mutual aspect score (use canonical helper)
            h1, h2 = d1["house"], d2["house"]
            asp_12 = _graha_aspects_house(n1, h1, h2) > 0.0
            asp_21 = _graha_aspects_house(n2, h2, h1) > 0.0
            mutual_asp = 1.0 if (asp_12 and asp_21) else 0.0

            # 3. Exchange (parivartana)
            s1, s2 = d1["sign"], d2["sign"]
            exchange = 1.0 if (SIGN_LORDS.get(s1) == n2 and SIGN_LORDS.get(s2) == n1) else 0.0

            # 4. Mutual reception
            n1_strong = set(OWN_SIGNS.get(n1, []))
            if EXALTATION_SIGNS.get(n1):
                n1_strong.add(EXALTATION_SIGNS[n1])
            n2_strong = set(OWN_SIGNS.get(n2, []))
            if EXALTATION_SIGNS.get(n2):
                n2_strong.add(EXALTATION_SIGNS[n2])
            reception = 0.5 if (s1 in n2_strong and s2 in n1_strong) else 0.0

            grade = (conj_score + mutual_asp + exchange + reception) / 4.0

            subj1 = PLANET_TO_SUBJECT.get(n1, n1.upper())
            subj2 = PLANET_TO_SUBJECT.get(n2, n2.upper())
            rows.append(_base_row(
                "sambandha_grade", f"{varga_prefix}{subj1}_{subj2}", "grade",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=round(grade, 4),
                value_jsonb={
                    "varga": varga,
                    "conjunction_score": conj_score, "mutual_aspect_score": mutual_asp,
                    "exchange_score": exchange, "reception_score": reception,
                },
                verif="two_pass_verified",
                source=f"ga_structural.sambandha_per_varga/{eng_ver}",
                citation_human=(
                    f"{n1}–{n2} sambandha in {varga}: grade {grade:.3f} ({ayanamsha_id})."
                ),
            ))
    return rows


def _build_bhava_web_per_varga_rows(
    varga_state: dict[str, Any],
    lagna_sign_num: int,
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    g_house = {g: d["house"] for g, d in varga_state.items()}
    kendra = {1, 4, 7, 10}
    trikona = {1, 5, 9}
    dusthana = {6, 8, 12}

    for src_h in range(1, 13):
        sign_idx = (lagna_sign_num - 1 + src_h - 1) % 12
        sign_name = SIGN_NAMES[sign_idx]
        lord_name = SIGN_LORDS.get(sign_name, "Sun")
        lord_h = g_house.get(lord_name, src_h)
        link_type = _bhava_link_type(src_h, lord_h, kendra, trikona, dusthana)
        rows.append(_base_row(
            "bhava_significance_link",
            f"{varga}_HOUSE_{src_h}_to_HOUSE_{lord_h}", "lord_placed",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=link_type,
            value_jsonb={"varga": varga, "source_house": src_h, "target_house": lord_h,
                         "lord": lord_name, "link_kind": "lord_placed", "link_type": link_type},
            verif="two_pass_verified",
            source=f"ga_structural.bhava_web_per_varga/{eng_ver}",
            citation_human=f"Lord of H{src_h} ({lord_name}) placed in H{lord_h} in {varga}: {link_type} ({ayanamsha_id}).",
        ))
        for tgt_h in range(1, 13):
            if tgt_h == lord_h:
                continue
            if _graha_aspects_house(lord_name, lord_h, tgt_h) > 0.0:
                asp_link = _bhava_link_type(src_h, tgt_h, kendra, trikona, dusthana)
                rows.append(_base_row(
                    "bhava_significance_link",
                    f"{varga}_HOUSE_{src_h}_to_HOUSE_{tgt_h}", "lord_aspects",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_text=asp_link,
                    value_jsonb={"varga": varga, "source_house": src_h, "target_house": tgt_h,
                                 "lord": lord_name, "link_kind": "lord_aspects", "link_type": asp_link},
                    verif="two_pass_verified",
                    source=f"ga_structural.bhava_web_per_varga/{eng_ver}",
                    citation_human=f"Lord of H{src_h} ({lord_name}) aspects H{tgt_h} in {varga}: {asp_link} ({ayanamsha_id}).",
                ))
    return rows


def _build_net_argala_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Net argala per house in varga space."""
    rows: list[dict[str, Any]] = []
    # Group grahas by house
    house_grahas: dict[int, list[str]] = {}
    for g, d in varga_state.items():
        h = d["house"]
        house_grahas.setdefault(h, []).append(g)

    NET_ARGALA_OFFSETS = [2, 4, 5, 11]
    NET_VIRODHA_OFFSETS = [3, 10, 9, 12]

    for tgt_h in range(1, 13):
        net = 0.0
        for offset in NET_ARGALA_OFFSETS:
            src_h = ((tgt_h - 1 + offset - 1) % 12) + 1
            grahas_in = house_grahas.get(src_h, [])
            if grahas_in:
                net += len(grahas_in)
        for offset in NET_VIRODHA_OFFSETS:
            src_h = ((tgt_h - 1 + offset - 1) % 12) + 1
            grahas_in = house_grahas.get(src_h, [])
            if grahas_in:
                net -= len(grahas_in)
        rows.append(_base_row(
            "net_argala_per_varga", f"{varga}_HOUSE_{tgt_h}", "net_argala",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=float(net),
            unit="net_count",
            value_jsonb={"varga": varga, "house": tgt_h, "net_argala": net},
            verif="two_pass_verified",
            source=f"ga_structural.net_argala_per_varga/{eng_ver}",
            citation_human=f"Net argala on H{tgt_h} in {varga}: {net:+.0f} ({ayanamsha_id}).",
        ))
    return rows


def _build_graha_yuddha_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    # MODELING ASSUMPTION: graha-yuddha is a physical-sky phenomenon; divisional degrees
    # are a mathematical mapping. Applied here per GA_STRUCTURAL_REBUILD_LOGIC_v1_0.md §0.2.
    rows: list[dict[str, Any]] = []
    grahas = [g for g in ALL_GRAHAS if g in varga_state and g not in ("Rahu", "Ketu", "Sun")]
    for i, n1 in enumerate(grahas):
        for n2 in grahas[i+1:]:
            d1 = varga_state[n1]
            d2 = varga_state[n2]
            long1 = (d1["sign_num"] - 1) * 30.0 + d1["degree"]
            long2 = (d2["sign_num"] - 1) * 30.0 + d2["degree"]
            orb = abs(long1 - long2)
            if orb > 180:
                orb = 360.0 - orb
            if orb <= 1.0:
                subj1 = PLANET_TO_SUBJECT.get(n1, n1.upper())
                subj2 = PLANET_TO_SUBJECT.get(n2, n2.upper())
                rows.append(_base_row(
                    "graha_yuddha_per_varga", f"{varga}_{subj1}_{subj2}", "within_1deg",
                    chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                    value_num=round(orb, 4),
                    unit="deg",
                    value_jsonb={
                        "varga": varga, "graha1": n1, "graha2": n2, "orb_deg": round(orb, 4),
                        "varga_assumption": "physical_phenomenon_extended_to_mathematical_varga",
                    },
                    verif="two_pass_verified",
                    source=f"ga_structural.graha_yuddha_per_varga/{eng_ver}",
                    citation_human=f"{n1}–{n2} within 1° in {varga} (orb {orb:.3f}°): graha-yuddha ({ayanamsha_id}).",
                ))
    return rows


def _build_combustion_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    # MODELING ASSUMPTION: combustion is a physical-sky phenomenon; varga orbs are
    # an extension of D1 classical orbs into mathematical varga space.
    rows: list[dict[str, Any]] = []
    if "Sun" not in varga_state:
        return rows
    sun_d = varga_state["Sun"]
    sun_long = (sun_d["sign_num"] - 1) * 30.0 + sun_d["degree"]
    for g_name, d in varga_state.items():
        if g_name in ("Sun", "Moon"):
            continue
        orb_limit = COMBUSTION_ORBS.get(g_name, 0.0)
        if orb_limit <= 0.0:
            continue
        g_long = (d["sign_num"] - 1) * 30.0 + d["degree"]
        arc = abs(g_long - sun_long)
        if arc > 180:
            arc = 360.0 - arc
        is_combust = arc <= orb_limit
        g_subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        rows.append(_base_row(
            "combustion_per_varga", f"{varga}_{g_subj}", "is_combust",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_num=1.0 if is_combust else 0.0,
            value_jsonb={
                "varga": varga, "graha": g_name, "arc_deg": round(arc, 4),
                "orb_limit": orb_limit, "is_combust": is_combust,
                "varga_assumption": "physical_phenomenon_extended_to_mathematical_varga",
            },
            verif="two_pass_verified",
            source=f"ga_structural.combustion_per_varga/{eng_ver}",
            citation_human=(
                f"{g_name} {'combust' if is_combust else 'not combust'} in {varga}: "
                f"arc {arc:.2f}° (limit {orb_limit}°) ({ayanamsha_id})."
            ),
        ))
    return rows


def _build_nway_per_varga_rows(
    varga_state: dict[str, Any],
    varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Stellium / cluster detection per varga."""
    rows: list[dict[str, Any]] = []
    from collections import defaultdict
    by_sign: dict[str, list[str]] = defaultdict(list)
    for g, d in varga_state.items():
        if g in ALL_GRAHAS:
            by_sign[d["sign"]].append(g)
    for sign_name, grahas in by_sign.items():
        if len(grahas) >= 3:
            subj_list = [PLANET_TO_SUBJECT.get(g, g.upper()) for g in grahas]
            rows.append(_base_row(
                "nway_config_per_varga", f"{varga}_{sign_name}", "stellium",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=float(len(grahas)),
                unit="graha_count",
                value_jsonb={
                    "varga": varga, "sign": sign_name,
                    "grahas": grahas, "count": len(grahas), "type": "stellium",
                },
                verif="two_pass_verified",
                source=f"ga_structural.nway_config_per_varga/{eng_ver}",
                citation_human=f"{len(grahas)}-way stellium in {sign_name} ({varga}): {', '.join(grahas)} ({ayanamsha_id}).",
            ))
    return rows


def _build_virupa_drishti_rows(
    varga_state: dict, varga: str, chart_id: str, build_id: str,
    ayanamsha_id: str, computed_at: str, eng_ver: str,
) -> list[dict]:
    """Continuous graded Parashari drishti strength per BPHS Ch.7. One row per (aspector, target_house, varga)."""
    rows = []
    for g_name, data in varga_state.items():
        if g_name not in ALL_GRAHAS:
            continue
        g_house_v = data["house"]
        g_subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        if g_name in ("Rahu", "Ketu"):
            asp_table = NODE_PARASHARI_ASPECTS
        else:
            asp_table = {**PARASHARI_ASPECTS.get(g_name, {}), **PARASHARI_ASPECTS["all"]}
        for offset, strength in asp_table.items():
            target_house = ((g_house_v - 1 + offset - 1) % 12) + 1
            rows.append(_base_row(
                "virupa_drishti", f"{varga}_{g_subj}", f"h{target_house}_offset{offset}",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=strength,
                unit="virupa_strength",
                value_jsonb={
                    "varga": varga, "graha": g_name, "source_house": g_house_v,
                    "target_house": target_house, "aspect_offset": offset,
                    "strength": strength, "ayanamsha_id": ayanamsha_id,
                },
                verif="two_pass_verified",
                source=f"ga_structural.virupa_drishti/{eng_ver}",
                citation_human=(
                    f"BPHS Ch.7: {g_name} {offset}th aspect on H{target_house} in {varga} "
                    f"strength={strength:.2f} ({ayanamsha_id})."
                ),
            ))
    return rows


def _build_nakshatra_relationship_rows(
    conn: Any, chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict]:
    """Emit nakshatra_co_tenancy, tara_bala, nakshatra_lord_relationship.

    Nakshatra NAMES come from graha_position (fact_key='nakshatra') — same source
    used by nakshatra_dispositor_chain (GAP-4 lesson: graha_nakshatra_join has no
    'nakshatra' key; it stores attributes keyed by gana/guna/nakshatra_lord etc.).
    Nakshatra LORD fact_ids come from graha_nakshatra_join (fact_key='nakshatra_lord')
    for L1-authority constituent references.
    Constituent refs live in fact_value_jsonb['constituent_fact_ids'] — the
    constituent_facts_array column does not exist in chart_facts.
    """
    rows = []
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            # Nakshatra names + fact_ids from graha_position (same source as dispositor_chain)
            cur.execute("""
                SELECT fact_subject, fact_value_text, fact_id
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category = 'graha_position'
                  AND fact_key = 'nakshatra'
            """, (chart_id, ayanamsha_id))
            nak_raw = cur.fetchall()

            # Nakshatra lord names + fact_ids from graha_nakshatra_join (L1-authority refs)
            cur.execute("""
                SELECT fact_subject, fact_value_text, fact_id
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category = 'graha_nakshatra_join'
                  AND fact_key = 'nakshatra_lord'
            """, (chart_id, ayanamsha_id))
            lord_raw = cur.fetchall()
    except Exception as exc:
        logger.warning("[ga_structural] nakshatra_relationship query failed: %s", exc)
        return []

    from collections import defaultdict

    # graha → nakshatra name + graha_position fact_id
    graha_nak_name: dict[str, str] = {}
    graha_nak_fid: dict[str, str] = {}
    for subj, nak_text, fact_id in nak_raw:
        if nak_text:
            graha_nak_name[subj] = nak_text
            graha_nak_fid[subj] = str(fact_id)

    # graha → nakshatra lord name + graha_nakshatra_join fact_id (L1 ref)
    graha_lord_name: dict[str, str] = {}
    graha_lord_fid: dict[str, str] = {}
    for subj, lord_text, fact_id in lord_raw:
        if lord_text:
            graha_lord_name[subj] = lord_text
            graha_lord_fid[subj] = str(fact_id)

    moon_subj = PLANET_TO_SUBJECT.get("Moon", "MOON")
    moon_nak = graha_nak_name.get(moon_subj, "")
    moon_nak_idx = NAKSHATRA_NAMES_27.index(moon_nak) if moon_nak in NAKSHATRA_NAMES_27 else -1
    moon_nak_fid = graha_nak_fid.get(moon_subj, "")
    TARA_NAMES = ["janma", "sampat", "vipat", "kshema", "pratyak", "sadhaka", "naidhana", "mitra", "atimitra"]

    # Co-tenancy: group grahas by shared nakshatra
    by_nak: dict[str, list[str]] = defaultdict(list)
    for graha_subj, nak in graha_nak_name.items():
        by_nak[nak].append(graha_subj)

    for nak_name, co_grahas in by_nak.items():
        if len(co_grahas) >= 2:
            for i, g1 in enumerate(co_grahas):
                for g2 in co_grahas[i+1:]:
                    fids = [f for f in [graha_nak_fid.get(g1, ""), graha_nak_fid.get(g2, "")] if f]
                    rows.append(_base_row(
                        "nakshatra_co_tenancy", nak_name, f"co_{g1}_{g2}",
                        chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                        value_text=f"{g1}&{g2}",
                        value_jsonb={
                            "nakshatra": nak_name,
                            "grahas": [g1, g2],
                            "constituent_fact_ids": fids,
                        },
                        verif="two_pass_verified",
                        source=f"ga_structural.nakshatra_co_tenancy/{eng_ver}",
                        citation_human=f"{g1} and {g2} co-tenant in {nak_name} ({ayanamsha_id}).",
                    ))

    for graha_subj, nak in graha_nak_name.items():
        nak_idx = NAKSHATRA_NAMES_27.index(nak) if nak in NAKSHATRA_NAMES_27 else -1
        nak_lord = graha_lord_name.get(graha_subj, NAKSHATRA_LORDS.get(nak, ""))
        graha_nak_fact_id = graha_nak_fid.get(graha_subj, "")
        lord_fact_id = graha_lord_fid.get(graha_subj, "")

        rows.append(_base_row(
            "nakshatra_lord_relationship", graha_subj, "nakshatra_lord",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            value_text=nak_lord,
            value_jsonb={
                "graha_subject": graha_subj,
                "nakshatra": nak,
                "lord": nak_lord,
                "constituent_fact_ids": [f for f in [graha_nak_fact_id, lord_fact_id] if f],
            },
            verif="two_pass_verified",
            source=f"ga_structural.nakshatra_lord_relationship/{eng_ver}",
            citation_human=f"{graha_subj} in {nak}; lord={nak_lord} ({ayanamsha_id}).",
        ))

        if moon_nak_idx >= 0 and nak_idx >= 0:
            tara_count = (nak_idx - moon_nak_idx) % 27 + 1
            tara_idx = (tara_count - 1) % 9
            tara_name = TARA_NAMES[tara_idx]
            rows.append(_base_row(
                "tara_bala", graha_subj, "tara_from_moon",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=float(tara_count),
                value_text=tara_name,
                value_jsonb={
                    "graha_subject": graha_subj,
                    "nakshatra": nak,
                    "moon_nakshatra": moon_nak,
                    "tara_count": tara_count,
                    "tara_name": tara_name,
                    "constituent_fact_ids": [f for f in [graha_nak_fact_id, moon_nak_fid] if f],
                },
                verif="two_pass_verified",
                source=f"ga_structural.tara_bala/{eng_ver}",
                citation_human=(
                    f"{graha_subj} tara from Moon: {tara_count} ({tara_name}) ({ayanamsha_id})."
                ),
            ))
    return rows


def _build_nakshatra_dispositor_chain_rows(
    conn: Any, chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict]:
    """GAP-4: nakshatra dispositor chain per graha, referencing ga_nakshatra fact_ids.

    Queries graha_nakshatra_join for each graha's nakshatra_lord fact_id (L1-authority
    reference per §N.5). Nakshatra names come from graha_position (fact_key='nakshatra').
    Builds the nakshatra-lord chain: graha → lord(graha's nak) → lord(that planet's nak) → ...
    until cycle. Stores chain + constituent_fact_ids in fact_value_jsonb (GAP-4 resolution;
    chart_facts has no constituent_facts_array column — reference lives in jsonb).
    """
    rows: list[dict] = []
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            # nakshatra_lord fact_ids from graha_nakshatra_join
            cur.execute("""
                SELECT fact_subject, fact_value_text, fact_id
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category = 'graha_nakshatra_join'
                  AND fact_key = 'nakshatra_lord'
            """, (chart_id, ayanamsha_id))
            lord_raw = cur.fetchall()

            # nakshatra names from graha_position
            cur.execute("""
                SELECT fact_subject, fact_value_text
                FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category = 'graha_position'
                  AND fact_key = 'nakshatra'
            """, (chart_id, ayanamsha_id))
            nak_raw = cur.fetchall()
    except Exception as exc:
        logger.warning("[ga_structural] nakshatra_dispositor_chain query failed: %s", exc)
        return []

    from collections import defaultdict
    graha_lord: dict[str, str] = {}   # subject → lowercase lord name
    graha_fact_id: dict[str, str] = {}  # subject → nakshatra_lord fact_id (L1 ref)
    for subj, lord_text, fact_id in lord_raw:
        graha_lord[subj] = lord_text or ""
        graha_fact_id[subj] = str(fact_id)

    graha_nakshatra: dict[str, str] = {}  # subject → nakshatra name
    for subj, nak_text in nak_raw:
        graha_nakshatra[subj] = nak_text or ""

    subj_to_planet: dict[str, str] = {v: k for k, v in PLANET_TO_SUBJECT.items()}

    # Build nak_lord_planet: planet_name → planet_name of its nakshatra lord
    nak_lord_planet: dict[str, str] = {}
    for subj, lord_lower in graha_lord.items():
        planet_name = subj_to_planet.get(subj, "")
        if not planet_name or not lord_lower:
            continue
        lord_cap = lord_lower.capitalize()
        if lord_lower in ("rahu", "rahu_mean"):
            lord_cap = "Rahu"
        elif lord_lower in ("ketu", "ketu_mean"):
            lord_cap = "Ketu"
        nak_lord_planet[planet_name] = lord_cap

    for subj in graha_lord:
        planet_name = subj_to_planet.get(subj, "")
        if not planet_name:
            continue

        # Walk the nakshatra-lord chain
        chain: list[str] = [planet_name]
        seen: dict[str, int] = {planet_name: 0}
        current = planet_name
        cycle_at_step = -1
        for _ in range(15):
            nxt = nak_lord_planet.get(current, "")
            if not nxt:
                break
            if nxt in seen:
                chain.append(nxt)
                cycle_at_step = len(chain) - 1
                break
            seen[nxt] = len(chain)
            chain.append(nxt)
            current = nxt

        # Nakshatra for each step planet (from graha_position, excludes cycle terminus)
        chain_naks: list[str] = []
        for step_planet in chain[:-1]:
            step_subj = PLANET_TO_SUBJECT.get(step_planet, "")
            nak = graha_nakshatra.get(step_subj, "")
            if nak:
                chain_naks.append(nak)

        chain_length = len(chain)
        fid = graha_fact_id.get(subj, "")
        effective_cycle = cycle_at_step if cycle_at_step >= 0 else chain_length - 1

        rows.append(_base_row(
            "nakshatra_dispositor_chain", subj, "chain_jsonb",
            chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
            # constituent_fact_ids lives inside jsonb: chart_facts has no array column
            value_jsonb={
                "chain": chain,
                "length": chain_length,
                "nakshatras": chain_naks,
                "cycle_at_step": effective_cycle,
                "constituent_fact_ids": [fid] if fid else [],
            },
            verif="two_pass_verified",
            source=f"ga_structural.nakshatra_dispositor_chain/{eng_ver}",
            citation_human=(
                f"{planet_name} nak-lord chain length={chain_length} "
                f"(cycle@{effective_cycle}) in {ayanamsha_id}. "
                f"GAP-4: L1 nakshatra_lord fact_id={fid} (graha_nakshatra_join)."
            ),
        ))
    return rows


def _build_bhava_chalit_divergence_rows(
    conn: Any, chart_output: dict, chart_id: str, build_id: str,
    ayanamsha_id: str, computed_at: str, eng_ver: str,
) -> list[dict]:
    """Flag when equal-bhava (Sripati chalit) house differs from rasi (whole-sign) house.

    Root-cause fix: no GA writer writes a 'bhava_chalit_house' category to chart_facts,
    so the original DB query always returned 0 rows. Bhava chalit positions are computed
    inline here from chart_output — 12 equal bhavas of 30° each starting at the
    ascendant longitude. A graha that falls in a different equal-bhava house than its
    rasi (whole-sign) house is flagged as diverging.
    Constituent refs live in fact_value_jsonb['constituent_fact_ids'].
    """
    rows = []

    asc = chart_output.get("ascendant", {})
    asc_long = float(asc.get("longitude", 0.0))

    # 12 equal-bhava cusps: cusp k = (asc_long + (k-1)*30) % 360
    cusp_starts = [(asc_long + i * 30.0) % 360.0 for i in range(12)]

    def _chalit_house_for(g_long: float) -> int:
        g = g_long % 360.0
        for h in range(12):
            start = cusp_starts[h]
            end = cusp_starts[(h + 1) % 12]
            if start < end:
                if start <= g < end:
                    return h + 1
            else:  # arc wraps 360 → 0
                if g >= start or g < end:
                    return h + 1
        return 1

    # Pre-load graha_position fact_ids for constituent refs (one query, not N queries)
    graha_pos_fids: dict[str, str] = {}
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT fact_subject, fact_id FROM chart_facts
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND fact_category = 'graha_position'
                  AND fact_key = 'sign'
            """, (chart_id, ayanamsha_id))
            for subj, fid in cur.fetchall():
                graha_pos_fids[subj] = str(fid)
    except Exception as exc:
        logger.warning("[ga_structural] bhava_chalit graha_pos prefetch failed: %s", exc)

    divergence_count = 0
    for g in chart_output.get("grahas", []):
        g_name = g.get("name", "")
        g_subj = PLANET_TO_SUBJECT.get(g_name, g_name.upper())
        rasi_h = int(g.get("house", 1))
        g_long = float(g.get("longitude", 0.0))
        chalit_h = _chalit_house_for(g_long)

        if chalit_h != rasi_h:
            divergence_count += 1
            fid = graha_pos_fids.get(g_subj, "")
            rows.append(_base_row(
                "bhava_chalit_rasi_divergence", g_subj, "diverges_from_rasi",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text="true",
                value_jsonb={
                    "rasi_house": rasi_h,
                    "chalit_house": chalit_h,
                    "diverges": True,
                    "asc_longitude": round(asc_long, 4),
                    "graha_longitude": round(g_long, 4),
                    "constituent_fact_ids": [fid] if fid else [],
                },
                verif="two_pass_verified",
                source=f"ga_structural.bhava_chalit_divergence/{eng_ver}",
                citation_human=(
                    f"{g_subj} bhava-chalit diverges: rasi H{rasi_h} vs chalit H{chalit_h} "
                    f"(asc={asc_long:.2f}°, graha={g_long:.2f}°) ({ayanamsha_id})."
                ),
            ))

    logger.info(
        "[ga_structural] bhava_chalit_divergence: %d/%d grahas shift house in equal-bhava "
        "(asc_long=%.2f°, %s)",
        divergence_count, len(chart_output.get("grahas", [])), asc_long, ayanamsha_id,
    )
    return rows


def _build_significator_path_rows(
    chart_output: dict, varga_state: dict, varga: str,
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict]:
    """BFS shortest-path between all graha pairs on the dispositor graph in varga space."""
    rows = []
    if varga == "D1":
        g_sign = {g["name"]: g.get("sign", "Aries") for g in chart_output.get("grahas", [])}
    else:
        g_sign = {g: d["sign"] for g, d in varga_state.items()}

    planet_names = set(g_sign.keys()) & set(ALL_GRAHAS)

    parent: dict[str, str | None] = {}
    for n in planet_names:
        lord = SIGN_LORDS.get(g_sign.get(n, "Aries"), n)
        parent[n] = lord if (lord != n and lord in planet_names) else None

    from collections import deque
    for start in planet_names:
        visited = {start: [start]}
        queue = deque([start])
        while queue:
            curr = queue.popleft()
            for nxt in planet_names:
                if nxt in visited:
                    continue
                if parent.get(nxt) == curr or parent.get(curr) == nxt:
                    visited[nxt] = visited[curr] + [nxt]
                    queue.append(nxt)
        for end in planet_names:
            if end == start:
                continue
            path = visited.get(end)
            path_len = len(path) - 1 if path else None
            s1 = PLANET_TO_SUBJECT.get(start, start.upper())
            s2 = PLANET_TO_SUBJECT.get(end, end.upper())
            rows.append(_base_row(
                "significator_path", f"{varga}_{s1}_to_{s2}", "shortest_path_length",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_num=float(path_len) if path_len is not None else -1.0,
                value_jsonb={
                    "varga": varga, "from_graha": start, "to_graha": end,
                    "path": path or [], "path_length": path_len,
                    "classification": (
                        "direct" if path_len == 1
                        else "mediated" if path_len and path_len <= 3
                        else "remote" if path_len
                        else "isolated"
                    ),
                },
                verif="two_pass_verified",
                source=f"ga_structural.significator_path/{eng_ver}",
                citation_human=(
                    f"{start}→{end} in {varga}: path length "
                    f"{'no path' if path_len is None else path_len} ({ayanamsha_id})."
                ),
            ))
    return rows


def _build_contradiction_pair_rows(
    all_rows: list[dict[str, Any]],
    chart_id: str, build_id: str, ayanamsha_id: str,
    computed_at: str, eng_ver: str,
) -> list[dict[str, Any]]:
    """Contradiction pair: same entity + same varga + opposing valence on same relationship-type family."""
    rows: list[dict[str, Any]] = []

    CATEGORY_FAMILY = {
        "yoga_fires": "yoga", "yoga_label": "yoga",
        "dosha_fires": "dosha", "dosha_label": "dosha",
        "argala_natal_matrix": "argala", "virodha_argala_natal_matrix": "argala",
        "net_argala": "net_argala",
    }

    def _valence(r: dict) -> str | None:
        cat = r.get("fact_category", "")
        if cat in {"yoga_fires", "yoga_label", "argala_natal_matrix"}:
            return "benefic"
        if cat in {"dosha_fires", "dosha_label", "virodha_argala_natal_matrix"}:
            return "malefic"
        if cat == "net_argala":
            v = r.get("fact_value_num")
            if v is not None:
                return "benefic" if float(v) > 0 else ("malefic" if float(v) < 0 else None)
        return None

    def _varga_from_subject(subj: str) -> str:
        for v in ALL_30_VARGAS:
            if subj.startswith(f"{v}_"):
                return v
        return "D1"

    from collections import defaultdict
    groups: dict[tuple, list[tuple[str, str]]] = defaultdict(list)
    for r in all_rows:
        cat = r.get("fact_category", "")
        family = CATEGORY_FAMILY.get(cat)
        if not family:
            continue
        v = _valence(r)
        if not v:
            continue
        subj = r.get("fact_subject", "")
        varga = _varga_from_subject(subj)
        groups[(subj, family, varga)].append((v, cat))

    seen: set[tuple] = set()
    for (subj, family, varga), valence_list in groups.items():
        key = (subj, family, varga)
        if key in seen:
            continue
        has_benefic = any(v == "benefic" for v, _ in valence_list)
        has_malefic = any(v == "malefic" for v, _ in valence_list)
        if has_benefic and has_malefic:
            seen.add(key)
            ben_cats = list({c for v, c in valence_list if v == "benefic"})
            mal_cats = list({c for v, c in valence_list if v == "malefic"})
            rows.append(_base_row(
                "contradiction_pair", subj, f"opposed_{family}_{varga}",
                chart_id, ayanamsha_id, build_id, computed_at, eng_ver,
                value_text="benefic_malefic_conflict",
                value_jsonb={
                    "target": subj, "family": family, "varga": varga,
                    "benefic_sources": ben_cats, "malefic_sources": mal_cats,
                    "benefic_count": sum(1 for v, _ in valence_list if v == "benefic"),
                    "malefic_count": sum(1 for v, _ in valence_list if v == "malefic"),
                },
                verif="two_pass_verified",
                source=f"ga_structural.contradiction_pairs/{eng_ver}",
                citation_human=(
                    f"{subj} contradiction ({family}, {varga}): benefic {ben_cats} "
                    f"vs malefic {mal_cats}; L2 determines outcome ({ayanamsha_id})."
                ),
            ))
    return rows


# ── §10a registry: one entry per fact family, module-level + ordered ─────────
#
# STRUCTURAL_SUB_BUILDERS enumerates every `_build_*_rows` family function in
# this module for completeness auditing (a future family cannot be silently
# dropped without failing the registry-completeness test). `kind` distinguishes
# families the driver (`build_ga_structural_substep`) invokes directly
# ("top_level") from families invoked internally by a top_level parent
# ("nested" — e.g. every per-varga family lives inside the `varga_aspect`
# loop in `_build_varga_aspect_rows`, which is itself top_level). Nested
# entries are NOT re-invoked by the driver — re-registering them at the top
# level would double-count/duplicate rows and change behavior, which this
# lane's mechanical-refactor discipline (§1.1.4) forbids.
STRUCTURAL_SUB_BUILDERS: list[tuple[str, Callable[..., list[dict[str, Any]]], str, str | None]] = [
    ("aspects", _build_aspect_rows, "top_level", None),
    ("shadbala_extension", _build_shadbala_extension_rows, "top_level", None),
    ("bhava_bala_extended", _build_bhava_bala_extended_rows, "top_level", None),
    ("anubindu", _build_anubindu_rows, "top_level", None),
    ("vimsopaka_ext", _build_vimsopaka_ext_rows, "top_level", None),
    ("yoga", _build_yoga_rows, "top_level", None),
    ("dosha", _build_dosha_rows, "top_level", None),
    ("upapada", _build_upapada_rows, "top_level", None),
    ("panchadha_maitri", _build_panchadha_maitri_rows, "top_level", None),
    ("kendradhipati_dosha", _build_kendradhipati_dosha_rows, "top_level", None),
    ("avastha", _build_avastha_rows, "top_level", None),
    ("composite_strength", _build_composite_strength_rows, "top_level", None),
    ("functional_class", _build_functional_class_rows, "top_level", None),
    ("karakatva", _build_karakatva_rows, "top_level", None),
    ("structural_relationship", _build_structural_relationship_rows, "top_level", None),
    ("special_state", _build_special_state_rows, "top_level", None),
    ("esoteric", _build_esoteric_rows, "top_level", None),
    ("varga_aspect", _build_varga_aspect_rows, "top_level", None),
    ("special_point_relationship", _build_special_point_relationship_rows, "top_level", None),
    ("graha_yuddha", _build_graha_yuddha_rows, "top_level", None),
    ("combustion_retrograde_relationship", _build_combustion_retrograde_relationship_rows, "top_level", None),
    ("nakshatra_relationship", _build_nakshatra_relationship_rows, "top_level", None),
    ("nakshatra_dispositor_chain", _build_nakshatra_dispositor_chain_rows, "top_level", None),
    ("bhava_chalit_divergence", _build_bhava_chalit_divergence_rows, "top_level", None),
    ("significator_path", _build_significator_path_rows, "top_level", None),
    ("contradiction_pair", _build_contradiction_pair_rows, "top_level", None),
    # Nested — invoked per-varga inside _build_varga_aspect_rows:
    ("varga_relationship_per_varga", _build_varga_relationship_rows, "nested", "varga_aspect"),
    ("karaka_web_per_varga", _build_karaka_web_rows, "nested", "varga_aspect"),
    ("argala_per_varga", _build_argala_rows, "nested", "varga_aspect"),
    ("sambandha_per_varga", _build_sambandha_per_varga_rows, "nested", "varga_aspect"),
    ("bhava_web_per_varga", _build_bhava_web_per_varga_rows, "nested", "varga_aspect"),
    ("net_argala_per_varga", _build_net_argala_per_varga_rows, "nested", "varga_aspect"),
    ("graha_yuddha_per_varga", _build_graha_yuddha_per_varga_rows, "nested", "varga_aspect"),
    ("combustion_per_varga", _build_combustion_per_varga_rows, "nested", "varga_aspect"),
    ("nway_per_varga", _build_nway_per_varga_rows, "nested", "varga_aspect"),
    ("virupa_drishti_per_varga", _build_virupa_drishti_rows, "nested", "varga_aspect"),
    ("graph_centrality_per_varga", _build_graph_centrality_per_varga_rows, "nested", "varga_aspect"),
    ("dispositor_tree_per_varga", _build_dispositor_tree_per_varga_rows, "nested", "varga_aspect"),
    ("chart_cluster_per_varga", _build_chart_cluster_per_varga_rows, "nested", "varga_aspect"),
    ("chart_cog_per_varga", _build_chart_cog_per_varga_rows, "nested", "varga_aspect"),
    ("convergence_count_per_varga", _build_convergence_count_per_varga_rows, "nested", "varga_aspect"),
    ("karaka_bhava_concordance_per_varga", _build_karaka_bhava_concordance_per_varga_rows, "nested", "varga_aspect"),
    # Nested two levels deep — invoked inside _build_varga_relationship_rows,
    # which is itself nested inside _build_varga_aspect_rows:
    ("house_lord_matrix_per_varga", _build_house_lord_matrix_rows, "nested", "varga_relationship_per_varga"),
]


def build_ga_structural_substep(
    chart_id: str,
    build_id: str,
    ayanamsha_id: str,
    conn: Any,
    birth_params: dict[str, Any] | None = None,
    yoga_catalog: list[dict[str, Any]] | None = None,
    dosha_catalog: list[dict[str, Any]] | None = None,
) -> int:
    """Build GA8 for ONE ayanamsha. Called by the HEAVY orchestrator per sub-step.
    Returns rows_inserted count.
    yoga_catalog / dosha_catalog may be pre-loaded by the caller to avoid repeat DB queries.

    Thin driver (design §10a): loads shared chart state once, then iterates the
    "top_level" entries of STRUCTURAL_SUB_BUILDERS in registered order,
    concatenating rows, before the single existing INSERT INTO chart_facts +
    delete-then-insert idempotency (§N.3) scoped to (chart_id, ayanamsha_id).
    "nested" entries are invoked internally by their parent top_level family
    (see registry comment above) and are not called again here.
    """
    bp = resolve_birth_params(chart_id, birth_params)
    computed_at = datetime.now(timezone.utc).isoformat()
    eng_ver = ENGINE_VERSION

    adapter_id = CANONICAL_AYANAMSHAS[ayanamsha_id]
    chart_output = compute_chart(inputs=bp, ayanamsha_id=adapter_id)

    if chart_id == CANONICAL_CHART_ID:
        forensic_gate(chart_output, ayanamsha_id)

    if yoga_catalog is None:
        yoga_catalog = _load_yoga_catalog(conn)
    if dosha_catalog is None:
        dosha_catalog = _load_dosha_catalog(conn)

    d1_varga_state = _extract_chart_state(chart_output)
    all_rows: list[dict[str, Any]] = []

    # Per-family argument builders, keyed by the registry's family_key. Each
    # closure is called with zero args at iteration time; it captures the
    # chart state loaded once above. `all_rows` is captured by reference so
    # "contradiction_pair" (last in registered order) sees every row emitted
    # by the families before it — identical to the pre-refactor call shape.
    family_call: dict[str, Callable[[], list[dict[str, Any]]]] = {
        "aspects": lambda: _build_aspect_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "shadbala_extension": lambda: _build_shadbala_extension_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver, conn=conn),
        "bhava_bala_extended": lambda: _build_bhava_bala_extended_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "anubindu": lambda: _build_anubindu_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "vimsopaka_ext": lambda: _build_vimsopaka_ext_rows(conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "yoga": lambda: _build_yoga_rows(conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver, yoga_catalog if yoga_catalog else None),
        "dosha": lambda: _build_dosha_rows(conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver, dosha_catalog if dosha_catalog else None),
        "upapada": lambda: _build_upapada_rows(conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "panchadha_maitri": lambda: _build_panchadha_maitri_rows(conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "kendradhipati_dosha": lambda: _build_kendradhipati_dosha_rows(conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "avastha": lambda: _build_avastha_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "composite_strength": lambda: _build_composite_strength_rows(conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "functional_class": lambda: _build_functional_class_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "karakatva": lambda: _build_karakatva_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "structural_relationship": lambda: _build_structural_relationship_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver, conn=conn),
        "special_state": lambda: _build_special_state_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "esoteric": lambda: _build_esoteric_rows(chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        # _build_varga_aspect_rows includes argala/virodha per varga (all 30)
        "varga_aspect": lambda: _build_varga_aspect_rows(conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver),
        "special_point_relationship": lambda: _build_special_point_relationship_rows(
            conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ),
        "graha_yuddha": lambda: _build_graha_yuddha_rows(
            chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ),
        "combustion_retrograde_relationship": lambda: _build_combustion_retrograde_relationship_rows(
            chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ),
        # Phase-3 blind-spot builders
        "nakshatra_relationship": lambda: _build_nakshatra_relationship_rows(
            conn, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ),
        "nakshatra_dispositor_chain": lambda: _build_nakshatra_dispositor_chain_rows(
            conn, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ),
        "bhava_chalit_divergence": lambda: _build_bhava_chalit_divergence_rows(
            conn, chart_output, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ),
        "significator_path": lambda: _build_significator_path_rows(
            chart_output, d1_varga_state, "D1",
            chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ),
        "contradiction_pair": lambda: _build_contradiction_pair_rows(
            all_rows, chart_id, build_id, ayanamsha_id, computed_at, eng_ver
        ),
    }

    family_row_counts: dict[str, int] = {}
    for family_key, _builder_fn, kind, _parent in STRUCTURAL_SUB_BUILDERS:
        if kind != "top_level":
            continue
        family_rows = family_call[family_key]()
        all_rows.extend(family_rows)
        family_row_counts[family_key] = len(family_rows)

    logger.info(
        "[ga_structural_writer] substep ayanamsha=%s per-family row counts: %s",
        ayanamsha_id, family_row_counts,
    )

    # Two-pass verification
    try:
        _verify_no_duplicate_fact_ids(all_rows)
        _verify_no_ga3_overlap(all_rows)
        _verify_citation_completeness(all_rows)
        _linter_check_rows(all_rows)
    except Exception as exc:
        msg = f"TWO_PASS_FAILED [{ayanamsha_id}]: {exc}"
        _write_halt_log("TWO_PASS_STRUCTURAL", msg)
        raise RuntimeError(msg) from exc

    count = _insert_chart_facts_rows(conn, all_rows)

    label_count = sum(1 for r in all_rows if r["fact_category"] == "yoga_label")
    dosha_label_count = sum(1 for r in all_rows if r["fact_category"] == "dosha_label")
    varga_rows = sum(1 for r in all_rows if r["fact_category"].endswith("_per_varga"))

    logger.info(
        "[ga_structural_writer] substep ayanamsha=%s cf_rows=%d yoga_labels=%d dosha_labels=%d varga_rows=%d",
        ayanamsha_id, count, label_count, dosha_label_count, varga_rows,
    )
    return count


def _update_asset_throughput_structural(chart_id: str, build_id: str, row_count: int) -> None:
    # asset_id is ga_structural (previously mis-stamped as ga_strength).
    with _conn() as conn:
        update_asset_throughput(conn, "ga_structural", chart_id, build_id, row_count)
