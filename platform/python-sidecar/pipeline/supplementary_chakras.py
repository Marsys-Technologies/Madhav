"""
supplementary_chakras.py — Supplementary Jyotish chakra reference data.
Covers: Sapta-Shalaka, Kalanala, Kota, and Chandra Kala Nadi chakras.

Sapta-Shalaka: 7-spoked Tara-based wheel for transit muhurta assessment (27 nakshatras).
Kalanala:      Timing chakra grouping nakshatras by fire intensity (27 nakshatras).
Kota:          Fortification chakra for transit protection in 3 rings (28 nakshatras incl. Abhijit).
CKN:           Chandra Kala Nadi nakshatra attributes — rishi, domain, soul theme (27 nakshatras).

Stream C global — A17 [BUILD-ORCH-STREAM-C-A17-S2]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# SAPTA_SHALAKA_DATA — 27 nakshatras across 7 shalas (Tara-based cycling)
# ---------------------------------------------------------------------------
# Tara-9 positions applied across 27 nakshatras cycling through 7 shalaka types:
#   1=Janma, 2=Sampat, 3=Vipat, 4=Ksheema, 5=Pratyak, 6=Sadhana, 7=Naidhana
#   (Positions 8=Mitra and 9=Ati-mitra of Tara-9 are folded into the 7-spoke pattern)
# Source: Muhurta Chintamani, Tara Bala chapter

SAPTA_SHALAKA_DATA: list[dict] = [
    {"nakshatra_id": 1,  "nakshatra_name": "ashwini",           "shalaka_number": 1, "shalaka_type": "Janma — birth/self",        "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 2,  "nakshatra_name": "bharani",           "shalaka_number": 2, "shalaka_type": "Sampat — prosperity",        "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 3,  "nakshatra_name": "krittika",          "shalaka_number": 3, "shalaka_type": "Vipat — danger",             "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 4,  "nakshatra_name": "rohini",            "shalaka_number": 4, "shalaka_type": "Ksheema — wellbeing",        "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 5,  "nakshatra_name": "mrigashira",        "shalaka_number": 5, "shalaka_type": "Pratyak — obstacle",         "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 6,  "nakshatra_name": "ardra",             "shalaka_number": 6, "shalaka_type": "Sadhana — achievement",      "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 7,  "nakshatra_name": "punarvasu",         "shalaka_number": 7, "shalaka_type": "Naidhana — death/end",       "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 8,  "nakshatra_name": "pushya",            "shalaka_number": 1, "shalaka_type": "Janma — birth/self",         "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 9,  "nakshatra_name": "aslesha",           "shalaka_number": 2, "shalaka_type": "Sampat — prosperity",        "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 10, "nakshatra_name": "magha",             "shalaka_number": 3, "shalaka_type": "Vipat — danger",             "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 11, "nakshatra_name": "purva_phalguni",    "shalaka_number": 4, "shalaka_type": "Ksheema — wellbeing",        "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 12, "nakshatra_name": "uttara_phalguni",   "shalaka_number": 5, "shalaka_type": "Pratyak — obstacle",         "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 13, "nakshatra_name": "hasta",             "shalaka_number": 6, "shalaka_type": "Sadhana — achievement",      "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 14, "nakshatra_name": "chitra",            "shalaka_number": 7, "shalaka_type": "Naidhana — death/end",       "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 15, "nakshatra_name": "swati",             "shalaka_number": 1, "shalaka_type": "Janma — birth/self",         "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 16, "nakshatra_name": "vishakha",          "shalaka_number": 2, "shalaka_type": "Sampat — prosperity",        "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 17, "nakshatra_name": "anuradha",          "shalaka_number": 3, "shalaka_type": "Vipat — danger",             "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 18, "nakshatra_name": "jyeshtha",          "shalaka_number": 4, "shalaka_type": "Ksheema — wellbeing",        "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 19, "nakshatra_name": "mula",              "shalaka_number": 5, "shalaka_type": "Pratyak — obstacle",         "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 20, "nakshatra_name": "purva_ashadha",     "shalaka_number": 6, "shalaka_type": "Sadhana — achievement",      "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 21, "nakshatra_name": "uttara_ashadha",    "shalaka_number": 7, "shalaka_type": "Naidhana — death/end",       "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 22, "nakshatra_name": "shravana",          "shalaka_number": 1, "shalaka_type": "Janma — birth/self",         "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 23, "nakshatra_name": "dhanishtha",        "shalaka_number": 2, "shalaka_type": "Sampat — prosperity",        "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 24, "nakshatra_name": "shatabhisha",       "shalaka_number": 3, "shalaka_type": "Vipat — danger",             "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 25, "nakshatra_name": "purva_bhadrapada",  "shalaka_number": 4, "shalaka_type": "Ksheema — wellbeing",        "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 26, "nakshatra_name": "uttara_bhadrapada", "shalaka_number": 5, "shalaka_type": "Pratyak — obstacle",         "classical_citation": "Muhurta Chintamani, Tara Bala"},
    {"nakshatra_id": 27, "nakshatra_name": "revati",            "shalaka_number": 6, "shalaka_type": "Sadhana — achievement",      "classical_citation": "Muhurta Chintamani, Tara Bala"},
]

# ---------------------------------------------------------------------------
# KALANALA_DATA — 27 nakshatras in 3 kalanala groups by fire intensity
# ---------------------------------------------------------------------------
# Group 1: auspicious (mild fire) — safe for activities
# Group 2: inauspicious (intense fire) — avoid for muhurta
# Group 3: mixed (moderate fire) — context-dependent
# Source: Jyotish Sara Sangraha, Muhurta Kalanala chapter

KALANALA_DATA: list[dict] = [
    {"nakshatra_id": 1,  "nakshatra_name": "ashwini",           "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 2,  "nakshatra_name": "bharani",           "kalanala_group": 2, "group_effect": "inauspicious", "fire_intensity": "intense",  "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 3,  "nakshatra_name": "krittika",          "kalanala_group": 2, "group_effect": "inauspicious", "fire_intensity": "intense",  "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 4,  "nakshatra_name": "rohini",            "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 5,  "nakshatra_name": "mrigashira",        "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 6,  "nakshatra_name": "ardra",             "kalanala_group": 2, "group_effect": "inauspicious", "fire_intensity": "intense",  "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 7,  "nakshatra_name": "punarvasu",         "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 8,  "nakshatra_name": "pushya",            "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 9,  "nakshatra_name": "aslesha",           "kalanala_group": 2, "group_effect": "inauspicious", "fire_intensity": "moderate", "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 10, "nakshatra_name": "magha",             "kalanala_group": 2, "group_effect": "inauspicious", "fire_intensity": "moderate", "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 11, "nakshatra_name": "purva_phalguni",    "kalanala_group": 3, "group_effect": "mixed",        "fire_intensity": "moderate", "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 12, "nakshatra_name": "uttara_phalguni",   "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 13, "nakshatra_name": "hasta",             "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 14, "nakshatra_name": "chitra",            "kalanala_group": 3, "group_effect": "mixed",        "fire_intensity": "moderate", "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 15, "nakshatra_name": "swati",             "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 16, "nakshatra_name": "vishakha",          "kalanala_group": 3, "group_effect": "mixed",        "fire_intensity": "moderate", "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 17, "nakshatra_name": "anuradha",          "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 18, "nakshatra_name": "jyeshtha",          "kalanala_group": 2, "group_effect": "inauspicious", "fire_intensity": "intense",  "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 19, "nakshatra_name": "mula",              "kalanala_group": 2, "group_effect": "inauspicious", "fire_intensity": "intense",  "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 20, "nakshatra_name": "purva_ashadha",     "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 21, "nakshatra_name": "uttara_ashadha",    "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 22, "nakshatra_name": "shravana",          "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 23, "nakshatra_name": "dhanishtha",        "kalanala_group": 3, "group_effect": "mixed",        "fire_intensity": "moderate", "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 24, "nakshatra_name": "shatabhisha",       "kalanala_group": 2, "group_effect": "inauspicious", "fire_intensity": "moderate", "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 25, "nakshatra_name": "purva_bhadrapada",  "kalanala_group": 2, "group_effect": "inauspicious", "fire_intensity": "moderate", "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 26, "nakshatra_name": "uttara_bhadrapada", "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
    {"nakshatra_id": 27, "nakshatra_name": "revati",            "kalanala_group": 1, "group_effect": "auspicious",   "fire_intensity": "mild",     "classical_citation": "Jyotish Sara Sangraha, Muhurta Kalanala chapter"},
]

# ---------------------------------------------------------------------------
# KOTA_DATA — 28 nakshatras (27 + Abhijit id=28) in 3 rings, 4 quadrants
# ---------------------------------------------------------------------------
# Ring definitions:
#   swami  = inner ring — fortress lord's zone, most protected (protection_level=3)
#   madhya = middle ring — moderately protected (protection_level=2)
#   bahya  = outer ring — exposed/vulnerable (protection_level=1)
# Abhijit (28th nakshatra) placed in inner ring per classical Kota tradition.
# Source: Brihat Samhita, Kota Chakra

KOTA_DATA: list[dict] = [
    # Inner ring (swami — protection_level=3): 4 nakshatras + Abhijit
    {"nakshatra_id": 4,  "nakshatra_name": "rohini",            "ring": "swami",  "quadrant": "north", "protection_level": 3, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 8,  "nakshatra_name": "pushya",            "ring": "swami",  "quadrant": "east",  "protection_level": 3, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 13, "nakshatra_name": "hasta",             "ring": "swami",  "quadrant": "south", "protection_level": 3, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 15, "nakshatra_name": "swati",             "ring": "swami",  "quadrant": "west",  "protection_level": 3, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 28, "nakshatra_name": "abhijit",           "ring": "swami",  "quadrant": "south", "protection_level": 3, "classical_citation": "Brihat Samhita, Kota Chakra"},
    # Middle ring (madhya — protection_level=2): 8 nakshatras
    {"nakshatra_id": 3,  "nakshatra_name": "krittika",          "ring": "madhya", "quadrant": "north", "protection_level": 2, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 5,  "nakshatra_name": "mrigashira",        "ring": "madhya", "quadrant": "north", "protection_level": 2, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 7,  "nakshatra_name": "punarvasu",         "ring": "madhya", "quadrant": "east",  "protection_level": 2, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 9,  "nakshatra_name": "aslesha",           "ring": "madhya", "quadrant": "east",  "protection_level": 2, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 11, "nakshatra_name": "purva_phalguni",    "ring": "madhya", "quadrant": "south", "protection_level": 2, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 12, "nakshatra_name": "uttara_phalguni",   "ring": "madhya", "quadrant": "south", "protection_level": 2, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 14, "nakshatra_name": "chitra",            "ring": "madhya", "quadrant": "west",  "protection_level": 2, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 16, "nakshatra_name": "vishakha",          "ring": "madhya", "quadrant": "west",  "protection_level": 2, "classical_citation": "Brihat Samhita, Kota Chakra"},
    # Outer ring (bahya — protection_level=1): 15 nakshatras
    {"nakshatra_id": 1,  "nakshatra_name": "ashwini",           "ring": "bahya",  "quadrant": "north", "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 2,  "nakshatra_name": "bharani",           "ring": "bahya",  "quadrant": "north", "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 6,  "nakshatra_name": "ardra",             "ring": "bahya",  "quadrant": "east",  "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 10, "nakshatra_name": "magha",             "ring": "bahya",  "quadrant": "east",  "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 17, "nakshatra_name": "anuradha",          "ring": "bahya",  "quadrant": "south", "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 18, "nakshatra_name": "jyeshtha",          "ring": "bahya",  "quadrant": "south", "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 19, "nakshatra_name": "mula",              "ring": "bahya",  "quadrant": "south", "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 20, "nakshatra_name": "purva_ashadha",     "ring": "bahya",  "quadrant": "west",  "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 21, "nakshatra_name": "uttara_ashadha",    "ring": "bahya",  "quadrant": "west",  "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 22, "nakshatra_name": "shravana",          "ring": "bahya",  "quadrant": "north", "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 23, "nakshatra_name": "dhanishtha",        "ring": "bahya",  "quadrant": "north", "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 24, "nakshatra_name": "shatabhisha",       "ring": "bahya",  "quadrant": "west",  "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 25, "nakshatra_name": "purva_bhadrapada",  "ring": "bahya",  "quadrant": "east",  "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 26, "nakshatra_name": "uttara_bhadrapada", "ring": "bahya",  "quadrant": "east",  "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
    {"nakshatra_id": 27, "nakshatra_name": "revati",            "ring": "bahya",  "quadrant": "north", "protection_level": 1, "classical_citation": "Brihat Samhita, Kota Chakra"},
]

# ---------------------------------------------------------------------------
# CKN_DATA — 27 nakshatras with Chandra Kala Nadi attributes (no Abhijit)
# ---------------------------------------------------------------------------
# d150_amsa_group: D150 Saptarishi group cycling through 7 rishis:
#   1=Marichi, 2=Atri, 3=Angiras, 4=Pulastya, 5=Pulaha, 6=Kratu, 7=Vasishtha
# Source: Chandra Kala Nadi, Saptarishi Nadi tradition

CKN_DATA: list[dict] = [
    {"nakshatra_id": 1,  "nakshatra_name": "ashwini",           "rishi_lord": "Marichi",  "primary_domain": "healing",        "soul_theme": "initiation of healing gift",              "d150_amsa_group": 1, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 2,  "nakshatra_name": "bharani",           "rishi_lord": "Atri",     "primary_domain": "transformation", "soul_theme": "karmic debt of birth-death",               "d150_amsa_group": 2, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 3,  "nakshatra_name": "krittika",          "rishi_lord": "Angiras",  "primary_domain": "purification",   "soul_theme": "fire of divine initiation",                "d150_amsa_group": 3, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 4,  "nakshatra_name": "rohini",            "rishi_lord": "Pulastya", "primary_domain": "creation",       "soul_theme": "abundance and creative overflow",           "d150_amsa_group": 4, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 5,  "nakshatra_name": "mrigashira",        "rishi_lord": "Pulaha",   "primary_domain": "seeking",        "soul_theme": "eternal quest for beauty",                  "d150_amsa_group": 5, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 6,  "nakshatra_name": "ardra",             "rishi_lord": "Kratu",    "primary_domain": "dissolution",    "soul_theme": "destruction for renewal",                   "d150_amsa_group": 6, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 7,  "nakshatra_name": "punarvasu",         "rishi_lord": "Vasishtha","primary_domain": "renewal",        "soul_theme": "return from exile to wisdom",               "d150_amsa_group": 7, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 8,  "nakshatra_name": "pushya",            "rishi_lord": "Marichi",  "primary_domain": "nourishment",    "soul_theme": "divine sustenance and dharma",              "d150_amsa_group": 1, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 9,  "nakshatra_name": "aslesha",           "rishi_lord": "Atri",     "primary_domain": "wisdom",         "soul_theme": "serpent wisdom and hidden power",           "d150_amsa_group": 2, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 10, "nakshatra_name": "magha",             "rishi_lord": "Angiras",  "primary_domain": "ancestry",       "soul_theme": "royal lineage and ancestral duty",          "d150_amsa_group": 3, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 11, "nakshatra_name": "purva_phalguni",    "rishi_lord": "Pulastya", "primary_domain": "pleasure",       "soul_theme": "creative joy and romantic dharma",          "d150_amsa_group": 4, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 12, "nakshatra_name": "uttara_phalguni",   "rishi_lord": "Pulaha",   "primary_domain": "partnership",    "soul_theme": "covenant of mutual support",                "d150_amsa_group": 5, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 13, "nakshatra_name": "hasta",             "rishi_lord": "Kratu",    "primary_domain": "skill",          "soul_theme": "craft of the divine artisan",               "d150_amsa_group": 6, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 14, "nakshatra_name": "chitra",            "rishi_lord": "Vasishtha","primary_domain": "beauty",         "soul_theme": "architecture of the cosmos",                "d150_amsa_group": 7, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 15, "nakshatra_name": "swati",             "rishi_lord": "Marichi",  "primary_domain": "independence",   "soul_theme": "freedom of the self-born wind",             "d150_amsa_group": 1, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 16, "nakshatra_name": "vishakha",          "rishi_lord": "Atri",     "primary_domain": "ambition",       "soul_theme": "dual purpose — dharma and wealth",          "d150_amsa_group": 2, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 17, "nakshatra_name": "anuradha",          "rishi_lord": "Angiras",  "primary_domain": "devotion",       "soul_theme": "fraternal love and discipline",             "d150_amsa_group": 3, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 18, "nakshatra_name": "jyeshtha",          "rishi_lord": "Pulastya", "primary_domain": "protection",     "soul_theme": "elder authority and guardianship",          "d150_amsa_group": 4, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 19, "nakshatra_name": "mula",              "rishi_lord": "Pulaha",   "primary_domain": "roots",          "soul_theme": "destruction of false foundations",          "d150_amsa_group": 5, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 20, "nakshatra_name": "purva_ashadha",     "rishi_lord": "Kratu",    "primary_domain": "invincibility",  "soul_theme": "early victory before the zenith",           "d150_amsa_group": 6, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 21, "nakshatra_name": "uttara_ashadha",    "rishi_lord": "Vasishtha","primary_domain": "victory",        "soul_theme": "final triumph through dharma",              "d150_amsa_group": 7, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 22, "nakshatra_name": "shravana",          "rishi_lord": "Marichi",  "primary_domain": "learning",       "soul_theme": "listening to divine wisdom",                "d150_amsa_group": 1, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 23, "nakshatra_name": "dhanishtha",        "rishi_lord": "Atri",     "primary_domain": "wealth",         "soul_theme": "abundance through righteous action",        "d150_amsa_group": 2, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 24, "nakshatra_name": "shatabhisha",       "rishi_lord": "Angiras",  "primary_domain": "healing",        "soul_theme": "100 physicians — cosmic remedy",            "d150_amsa_group": 3, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 25, "nakshatra_name": "purva_bhadrapada",  "rishi_lord": "Pulastya", "primary_domain": "asceticism",     "soul_theme": "burning of the two-faced one",              "d150_amsa_group": 4, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 26, "nakshatra_name": "uttara_bhadrapada", "rishi_lord": "Pulaha",   "primary_domain": "depth",          "soul_theme": "serpentine wisdom of the depths",           "d150_amsa_group": 5, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
    {"nakshatra_id": 27, "nakshatra_name": "revati",            "rishi_lord": "Kratu",    "primary_domain": "completion",     "soul_theme": "shepherd of the cosmic journey",            "d150_amsa_group": 6, "classical_citation": "Chandra Kala Nadi, Saptarishi Nadi tradition"},
]


# ---------------------------------------------------------------------------
# seed_supplementary_chakras — idempotent DB seeder for all 4 chakra tables
# ---------------------------------------------------------------------------

def seed_supplementary_chakras(conn) -> dict:
    """
    Seed all four supplementary chakra tables:
      - l1_sapta_shalaka    (27 rows)
      - l1_kalanala_chakra  (27 rows)
      - l1_kota_chakra      (28 rows, including Abhijit id=28)
      - l1_ckn_chakra       (27 rows)

    Idempotent: uses INSERT ... ON CONFLICT (nakshatra_id) DO NOTHING.
    Returns dict with keys: sapta_shalaka, kalanala, kota, ckn
    (each = count of rows actually inserted).
    """
    counts = {"sapta_shalaka": 0, "kalanala": 0, "kota": 0, "ckn": 0}

    with conn.cursor() as cur:

        # ---- Sapta-Shalaka ----
        for row in SAPTA_SHALAKA_DATA:
            cur.execute(
                """
                INSERT INTO l1_sapta_shalaka
                    (nakshatra_id, nakshatra_name, shalaka_number, shalaka_type, classical_citation)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (nakshatra_id) DO NOTHING
                """,
                (
                    row["nakshatra_id"],
                    row["nakshatra_name"],
                    row["shalaka_number"],
                    row["shalaka_type"],
                    row.get("classical_citation"),
                ),
            )
            counts["sapta_shalaka"] += cur.rowcount

        # ---- Kalanala ----
        for row in KALANALA_DATA:
            cur.execute(
                """
                INSERT INTO l1_kalanala_chakra
                    (nakshatra_id, nakshatra_name, kalanala_group, group_effect,
                     fire_intensity, classical_citation)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (nakshatra_id) DO NOTHING
                """,
                (
                    row["nakshatra_id"],
                    row["nakshatra_name"],
                    row["kalanala_group"],
                    row["group_effect"],
                    row["fire_intensity"],
                    row.get("classical_citation"),
                ),
            )
            counts["kalanala"] += cur.rowcount

        # ---- Kota Chakra ----
        for row in KOTA_DATA:
            cur.execute(
                """
                INSERT INTO l1_kota_chakra
                    (nakshatra_id, nakshatra_name, ring, quadrant,
                     protection_level, classical_citation)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (nakshatra_id) DO NOTHING
                """,
                (
                    row["nakshatra_id"],
                    row["nakshatra_name"],
                    row["ring"],
                    row["quadrant"],
                    row["protection_level"],
                    row.get("classical_citation"),
                ),
            )
            counts["kota"] += cur.rowcount

        # ---- CKN Chakra ----
        for row in CKN_DATA:
            cur.execute(
                """
                INSERT INTO l1_ckn_chakra
                    (nakshatra_id, nakshatra_name, rishi_lord, primary_domain,
                     soul_theme, d150_amsa_group, classical_citation)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (nakshatra_id) DO NOTHING
                """,
                (
                    row["nakshatra_id"],
                    row["nakshatra_name"],
                    row["rishi_lord"],
                    row["primary_domain"],
                    row["soul_theme"],
                    row.get("d150_amsa_group"),
                    row.get("classical_citation"),
                ),
            )
            counts["ckn"] += cur.rowcount

        conn.commit()

    return counts
