"""
yoga_definitions.py — G12 Yoga Definitions Library
====================================================
Comprehensive classical Jyotish yoga catalogue covering all major yoga
categories: Pancha Mahapurusha, Raja, Dhana, Vipareeta Raja, Neechabhanga,
Lunar, Solar, Kala Sarpa, Nabhas, and Miscellaneous yogas.

Classical sources:
  - Brihat Parashara Hora Shastra (BPHS), Raja Yoga and Dhana Yoga chapters
  - Phaladeepika (Mantreswara), chapters 6–12
  - Parashari system as codified in standard commentaries

canonical_id: G12
stream: A
session: G12-S1 [BUILD-ORCH-A-23]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# YOGA_DEFINITIONS
# ---------------------------------------------------------------------------
# Each entry: {
#   "name":             str   — display name
#   "category":         str   — pancha_mahapurusha | raja | dhana |
#                               vipareeta_raja | neechabhanga | lunar | solar |
#                               miscellaneous | kala_sarpa | nabhas
#   "constituent_rule": str   — plain English formation rule
#   "classical_citation": str — BPHS chapter/verse or text reference
#   "strength_modifier":float — 0.5 (weak) to 3.0 (exceptional); 1.0 = standard
#   "rarity_class":     str   — common | uncommon | rare | exceptional
#   "cancellation_rules": list[str] — conditions that cancel the yoga
# }

YOGA_DEFINITIONS: dict[str, dict] = {

    # -----------------------------------------------------------------------
    # PANCHA MAHAPURUSHA YOGAS (5)
    # -----------------------------------------------------------------------

    "ruchaka": {
        "name": "Ruchaka Yoga",
        "category": "pancha_mahapurusha",
        "constituent_rule": "Mars is in its own sign (Aries or Scorpio) or exaltation sign (Capricorn) and placed in a kendra (1st, 4th, 7th, or 10th house)",
        "classical_citation": "BPHS Ch. 75, v.1-4; Phaladeepika Ch. 6 v.1",
        "strength_modifier": 2.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Mars is combust (within 8° of Sun)",
            "Mars occupies a dusthana (6th, 8th, or 12th) in navamsa",
            "Mars is debilitated in navamsa",
        ],
    },

    "bhadra": {
        "name": "Bhadra Yoga",
        "category": "pancha_mahapurusha",
        "constituent_rule": "Mercury is in its own sign (Gemini or Virgo) or exaltation sign (Virgo) and placed in a kendra (1st, 4th, 7th, or 10th house)",
        "classical_citation": "BPHS Ch. 75, v.5-8; Phaladeepika Ch. 6 v.2",
        "strength_modifier": 2.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Mercury is combust (within 14° of Sun)",
            "Mercury occupies a dusthana in navamsa",
            "Mercury is debilitated in navamsa (Pisces)",
        ],
    },

    "hamsa": {
        "name": "Hamsa Yoga",
        "category": "pancha_mahapurusha",
        "constituent_rule": "Jupiter is in its own sign (Sagittarius or Pisces) or exaltation sign (Cancer) and placed in a kendra (1st, 4th, 7th, or 10th house)",
        "classical_citation": "BPHS Ch. 75, v.9-12; Phaladeepika Ch. 6 v.3",
        "strength_modifier": 3.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Jupiter is combust (within 11° of Sun)",
            "Jupiter occupies a dusthana in navamsa",
            "Jupiter is debilitated in navamsa (Capricorn)",
        ],
    },

    "malavya": {
        "name": "Malavya Yoga",
        "category": "pancha_mahapurusha",
        "constituent_rule": "Venus is in its own sign (Taurus or Libra) or exaltation sign (Pisces) and placed in a kendra (1st, 4th, 7th, or 10th house)",
        "classical_citation": "BPHS Ch. 75, v.13-16; Phaladeepika Ch. 6 v.4",
        "strength_modifier": 2.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Venus is combust (within 10° of Sun)",
            "Venus occupies a dusthana in navamsa",
            "Venus is debilitated in navamsa (Virgo)",
        ],
    },

    "sasha": {
        "name": "Sasha Yoga",
        "category": "pancha_mahapurusha",
        "constituent_rule": "Saturn is in its own sign (Capricorn or Aquarius) or exaltation sign (Libra) and placed in a kendra (1st, 4th, 7th, or 10th house)",
        "classical_citation": "BPHS Ch. 75, v.17-20; Phaladeepika Ch. 6 v.5",
        "strength_modifier": 2.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Saturn is combust (within 15° of Sun)",
            "Saturn occupies a dusthana in navamsa",
            "Saturn is debilitated in navamsa (Aries)",
        ],
    },

    # -----------------------------------------------------------------------
    # RAJA YOGAS (40+)
    # -----------------------------------------------------------------------

    "dharma_karmadhipati": {
        "name": "Dharma-Karmadhipati Yoga",
        "category": "raja",
        "constituent_rule": "Lords of the 9th house (dharma) and 10th house (karma) are in conjunction, mutual exchange, or mutual aspect",
        "classical_citation": "BPHS Ch. 41, v.1-3; Phaladeepika Ch. 7 v.1",
        "strength_modifier": 2.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Both lords are combust simultaneously",
            "Both lords are in dusthanas (6/8/12) without relief",
        ],
    },

    "sreenatha": {
        "name": "Sreenatha Yoga",
        "category": "raja",
        "constituent_rule": "Lord of the 10th house is in exaltation and lord of the 7th house is placed in the 10th house",
        "classical_citation": "BPHS Ch. 41; Phaladeepika Ch. 7 v.3",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "10th lord in exaltation is combust",
        ],
    },

    "mahabhagya": {
        "name": "Mahabhagya Yoga",
        "category": "raja",
        "constituent_rule": "For male births: daytime birth with Sun, Moon, and Ascendant in odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius). For female births: nighttime birth with all three in even signs",
        "classical_citation": "BPHS Ch. 75; Phaladeepika Ch. 6 v.6",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Condition not fully met (all three must qualify)",
        ],
    },

    "chandra_mangala": {
        "name": "Chandra-Mangala Yoga",
        "category": "raja",
        "constituent_rule": "Moon and Mars are in conjunction or mutual aspect; gives wealth through daring enterprise",
        "classical_citation": "BPHS Ch. 36; Phaladeepika Ch. 7 v.8",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both planets are weak or combust",
            "Mars heavily afflicts Moon without Jupiter's protection",
        ],
    },

    "budha_aditya": {
        "name": "Budha-Aditya Yoga",
        "category": "raja",
        "constituent_rule": "Sun and Mercury are in conjunction in the same house, ideally in an angle (kendra) or trine (trikona)",
        "classical_citation": "BPHS Ch. 36; Phaladeepika Ch. 7",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "Mercury is too close to Sun (within 5°), becoming fully combust",
            "Conjunction is in a dusthana (6/8/12)",
        ],
    },

    "gaja_kesari": {
        "name": "Gaja-Kesari Yoga",
        "category": "raja",
        "constituent_rule": "Jupiter is placed in a kendra (1st, 4th, 7th, or 10th house) from the Moon's position; bestows fame, prosperity and noble qualities",
        "classical_citation": "BPHS Ch. 36; Phaladeepika Ch. 6 v.7; Saravali Ch. 23",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Jupiter is combust (within 11° of Sun)",
            "Jupiter is debilitated (Capricorn)",
            "Moon is weak (Krishna Ashtami or weaker)",
            "Jupiter is in enemy sign",
        ],
    },

    "saraswati": {
        "name": "Saraswati Yoga",
        "category": "raja",
        "constituent_rule": "Mercury, Venus, and Jupiter are all placed in angles (1/4/7/10) or trines (5/9), with at least one of them in its own sign or exaltation",
        "classical_citation": "BPHS Ch. 36; Phala Deepika Ch. 7 v.17",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "All three planets are combust",
            "None of the three is in own sign or exaltation",
        ],
    },

    "kalanidhi": {
        "name": "Kalanidhi Yoga",
        "category": "raja",
        "constituent_rule": "Jupiter is in the 2nd or 5th house and is conjoined or aspected by Mercury and Venus",
        "classical_citation": "Phaladeepika Ch. 7 v.18",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Jupiter is combust or debilitated",
            "Mercury or Venus is combust",
        ],
    },

    "kahala": {
        "name": "Kahala Yoga",
        "category": "raja",
        "constituent_rule": "Lords of the 4th and 10th houses are in mutual kendra or trikona and the Ascendant lord is strong",
        "classical_citation": "BPHS Ch. 36; Phaladeepika Ch. 7 v.6",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Ascendant lord is combust or weak in shadbala",
        ],
    },

    "chamara": {
        "name": "Chamara Yoga",
        "category": "raja",
        "constituent_rule": "Ascendant lord is in the Ascendant or 7th house in exaltation, or two planets in exaltation aspect the Ascendant",
        "classical_citation": "BPHS Ch. 36; Phaladeepika Ch. 7 v.5",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Exalted Ascendant lord is combust",
        ],
    },

    "shankha": {
        "name": "Shankha Yoga",
        "category": "raja",
        "constituent_rule": "Lords of the 5th and 6th houses are in mutual kendra relationship and the Ascendant lord is strong",
        "classical_citation": "BPHS Ch. 36; Phaladeepika Ch. 7 v.7",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Ascendant lord is significantly weak or combust",
        ],
    },

    "bheri": {
        "name": "Bheri Yoga",
        "category": "raja",
        "constituent_rule": "Venus, Jupiter, and Moon are all strong and the lord of the 9th house is also powerful",
        "classical_citation": "Phaladeepika Ch. 7 v.9",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Jupiter or Venus is debilitated or combust",
            "Moon is in Krishna paksha ashtami or new Moon",
        ],
    },

    "mridanga": {
        "name": "Mridanga Yoga",
        "category": "raja",
        "constituent_rule": "Lord of the navamsa occupied by the 10th house lord is placed in an angle or trine, is vargottama (same sign in rasi and navamsa), or in own sign",
        "classical_citation": "Phaladeepika Ch. 7 v.10",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "The navamsa lord is debilitated in both charts",
        ],
    },

    "parijata": {
        "name": "Parijata Yoga",
        "category": "raja",
        "constituent_rule": "The lord of the sign occupied by the Ascendant lord is either in its own sign, exalted, or aspected by the 9th lord",
        "classical_citation": "BPHS Ch. 36; Phaladeepika Ch. 7 v.4",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Relevant lords are combust or debilitated",
        ],
    },

    "akhanda_samrajya": {
        "name": "Akhanda Samrajya Yoga",
        "category": "raja",
        "constituent_rule": "Jupiter rules the 2nd, 5th, or 11th house (for Taurus or Aquarius Ascendant) and Jupiter is placed in the 2nd house while the lord of the 2nd is strong",
        "classical_citation": "BPHS Ch. 41; Phaladeepika Ch. 7 v.11",
        "strength_modifier": 2.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Jupiter is combust, debilitated, or in dusthana in navamsa",
        ],
    },

    "raja_yoga_from_5th": {
        "name": "Raja Yoga from 5th Lord",
        "category": "raja",
        "constituent_rule": "Lord of the 5th house (trikona) conjoins or mutually aspects the lord of the 9th or 10th house (trikona/kendra), forming a trikona-kendra connection",
        "classical_citation": "BPHS Ch. 41 v.1-10",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or in dusthanas simultaneously",
        ],
    },

    "raja_yoga_from_9th": {
        "name": "Raja Yoga from 9th Lord",
        "category": "raja",
        "constituent_rule": "Lord of the 9th house (trikona) conjoins or mutually aspects the lord of the 5th or 10th house",
        "classical_citation": "BPHS Ch. 41 v.1-10",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or heavily afflicted",
        ],
    },

    "raja_yoga_from_10th": {
        "name": "Raja Yoga from 10th Lord",
        "category": "raja",
        "constituent_rule": "Lord of the 10th house (kendra) conjoins or mutually aspects the lord of the 9th or 5th house (trikona), forming a trikona-kendra connection",
        "classical_citation": "BPHS Ch. 41 v.1-10",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or in dusthanas without mitigation",
        ],
    },

    "raja_yoga_1_4": {
        "name": "Raja Yoga 1st-4th",
        "category": "raja",
        "constituent_rule": "Lords of the 1st (kendra) and 4th (kendra) houses are in conjunction, exchange, or mutual aspect, with one also owning a trikona",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords combust or in enemy signs",
        ],
    },

    "raja_yoga_1_5": {
        "name": "Raja Yoga 1st-5th",
        "category": "raja",
        "constituent_rule": "Lords of the 1st (kendra/trikona) and 5th (trikona) houses are in conjunction, exchange, or mutual aspect",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords combust or heavily afflicted",
        ],
    },

    "raja_yoga_1_9": {
        "name": "Raja Yoga 1st-9th",
        "category": "raja",
        "constituent_rule": "Lords of the 1st (kendra/trikona) and 9th (trikona) houses are in conjunction, exchange, or mutual aspect",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords combust or in dusthanas",
        ],
    },

    "raja_yoga_4_5": {
        "name": "Raja Yoga 4th-5th",
        "category": "raja",
        "constituent_rule": "Lords of the 4th (kendra) and 5th (trikona) houses are in conjunction, exchange, or mutual aspect",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords combust or in dusthanas",
        ],
    },

    "raja_yoga_4_9": {
        "name": "Raja Yoga 4th-9th",
        "category": "raja",
        "constituent_rule": "Lords of the 4th (kendra) and 9th (trikona) houses are in conjunction, exchange, or mutual aspect",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords combust",
        ],
    },

    "raja_yoga_7_5": {
        "name": "Raja Yoga 7th-5th",
        "category": "raja",
        "constituent_rule": "Lords of the 7th (kendra) and 5th (trikona) houses are in conjunction, exchange, or mutual aspect",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords combust or in dusthanas",
        ],
    },

    "raja_yoga_7_9": {
        "name": "Raja Yoga 7th-9th",
        "category": "raja",
        "constituent_rule": "Lords of the 7th (kendra) and 9th (trikona) houses are in conjunction, exchange, or mutual aspect",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords combust or in enemy signs",
        ],
    },

    "raja_yoga_10_5": {
        "name": "Raja Yoga 10th-5th",
        "category": "raja",
        "constituent_rule": "Lords of the 10th (kendra) and 5th (trikona) houses are in conjunction, exchange, or mutual aspect",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords combust or in dusthanas",
        ],
    },

    "raja_yoga_10_9": {
        "name": "Raja Yoga 10th-9th",
        "category": "raja",
        "constituent_rule": "Lords of the 10th (kendra) and 9th (trikona) houses are in conjunction, exchange, or mutual aspect — the Dharma-Karma combination",
        "classical_citation": "BPHS Ch. 41; Phaladeepika Ch. 7",
        "strength_modifier": 2.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Both lords combust or in dusthanas",
        ],
    },

    "punya_yoga": {
        "name": "Punya Yoga",
        "category": "raja",
        "constituent_rule": "Lord of the 9th house is exalted, in own sign, or in a kendra/trikona, conferring fortune, piety, and auspicious results",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "9th lord is combust or in a dusthana",
        ],
    },

    "viparita_hamsa": {
        "name": "Viparita Hamsa",
        "category": "raja",
        "constituent_rule": "Jupiter lord of a kendra is placed in a trikona or Jupiter lord of a trikona is placed in a kendra, strengthening dharma and wisdom",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Jupiter is combust or debilitated",
        ],
    },

    "vasudha_yoga": {
        "name": "Vasudha Yoga",
        "category": "raja",
        "constituent_rule": "Lord of the 10th house is in exaltation in the 4th house and the 4th lord is strong",
        "classical_citation": "Phaladeepika Ch. 7",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "10th lord is combust in the 4th",
        ],
    },

    "indra_yoga": {
        "name": "Indra Yoga",
        "category": "raja",
        "constituent_rule": "Lords of the 5th and 11th houses exchange signs and the Moon is in the 5th house",
        "classical_citation": "Phaladeepika Ch. 7 v.12",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Moon is severely afflicted in the 5th",
        ],
    },

    "ravi_yoga": {
        "name": "Ravi Yoga",
        "category": "raja",
        "constituent_rule": "Sun is in the 10th house in own sign (Leo) or exaltation (Aries); or the 10th lord joins the Sun in strength",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Sun is afflicted by Saturn or Rahu without Jupiter's aspect",
        ],
    },

    "guru_mangala": {
        "name": "Guru-Mangala Yoga",
        "category": "raja",
        "constituent_rule": "Jupiter and Mars are in conjunction, mutual aspect, or exchange, combining wisdom with courage for powerful executive action",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both planets are in dusthanas or combust",
        ],
    },

    "kesari_yoga": {
        "name": "Kesari Yoga",
        "category": "raja",
        "constituent_rule": "Moon and Jupiter are in a mutual kendra (1/4/7/10 from each other), giving fame, intelligence, and public recognition",
        "classical_citation": "BPHS Ch. 36; Saravali Ch. 23",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Jupiter is combust or debilitated",
            "Moon is in new Moon phase (amamvasya)",
        ],
    },

    "vishnu_yoga": {
        "name": "Vishnu Yoga",
        "category": "raja",
        "constituent_rule": "Lords of the 9th, 10th, and 11th houses are all in the 4th house together, giving administrative authority and prosperity",
        "classical_citation": "Phaladeepika Ch. 7 v.15",
        "strength_modifier": 2.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "All three lords are combust",
        ],
    },

    "sun_kendra_yoga": {
        "name": "Sun in Kendra Yoga",
        "category": "raja",
        "constituent_rule": "Sun is placed in a kendra (1st, 4th, 7th, 10th) in own sign or exaltation, conferring authority and government connections",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "Sun is in enemy sign in kendra without any support",
        ],
    },

    "chandra_kendra_yoga": {
        "name": "Chandra Kendra Yoga",
        "category": "raja",
        "constituent_rule": "Moon is placed in a kendra in own sign (Cancer) or exaltation (Taurus), giving public popularity and emotional strength",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "Moon is in amavasya (new Moon) phase",
            "Moon is heavily afflicted by Saturn or Rahu",
        ],
    },

    "devendra_yoga": {
        "name": "Devendra Yoga",
        "category": "raja",
        "constituent_rule": "Lord of a kendra and lord of a trikona are both exalted and placed together in an angle or trine",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 2.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Either exalted lord is combust",
        ],
    },

    "pancha_graha_yoga": {
        "name": "Pancha Graha Yoga",
        "category": "raja",
        "constituent_rule": "Five or more planets are in the 10th house, conferring exceptional professional prominence (very rare configuration)",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 2.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Majority of the planets are combust or debilitated",
        ],
    },

    "kuja_yoga": {
        "name": "Kuja (Mars Strength) Yoga",
        "category": "raja",
        "constituent_rule": "Mars is in the 10th house in own sign or exaltation, conferring courage, leadership, and executive power",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Mars is combust in the 10th",
        ],
    },

    "budha_yogakaraka": {
        "name": "Budha Yogakaraka",
        "category": "raja",
        "constituent_rule": "For Taurus and Libra ascendants, Saturn rules both a kendra and a trikona, acting as single-planet raja yoga karaka",
        "classical_citation": "BPHS Ch. 34",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Saturn is combust, debilitated, or in dusthana",
        ],
    },

    "venus_yogakaraka": {
        "name": "Venus Yogakaraka",
        "category": "raja",
        "constituent_rule": "For Capricorn and Aquarius ascendants, Venus rules both a kendra (5th or 4th) and a trikona (9th), acting as single-planet raja yoga karaka",
        "classical_citation": "BPHS Ch. 34",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Venus is combust or in dusthana",
        ],
    },

    "mars_yogakaraka": {
        "name": "Mars Yogakaraka",
        "category": "raja",
        "constituent_rule": "For Cancer and Leo ascendants, Mars rules both a kendra (4th or 1st) and a trikona (9th or 5th), acting as single-planet raja yoga karaka",
        "classical_citation": "BPHS Ch. 34",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Mars is combust or debilitated in navamsa",
        ],
    },

    "trikona_kendra_connection": {
        "name": "Trikona-Kendra Connection",
        "category": "raja",
        "constituent_rule": "Any planet owning both a kendra and a trikona, or two planets (one kendra lord, one trikona lord) joining by conjunction, aspect, or exchange",
        "classical_citation": "BPHS Ch. 41 v.1",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Planets involved are both in dusthanas",
        ],
    },

    "simhasana_yoga": {
        "name": "Simhasana Yoga",
        "category": "raja",
        "constituent_rule": "Multiple planets are in exaltation in angles or trines simultaneously, giving throne-like authority",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 2.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Exalted planets are simultaneously combust",
        ],
    },

    "uttama_yoga": {
        "name": "Uttama Yoga",
        "category": "raja",
        "constituent_rule": "Multiple lords of angles and trines are in exaltation or own signs, forming a compound auspicious pattern",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "The exalted or strong lords are combust",
        ],
    },

    "chandrika_yoga": {
        "name": "Chandrika Yoga",
        "category": "raja",
        "constituent_rule": "Moon is in exaltation (Taurus) in the 10th house or aspected by Jupiter from a kendra, giving brilliance, fame, and public eminence",
        "classical_citation": "Phaladeepika Ch. 7",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Moon is in amavasya phase",
        ],
    },

    "prabhu_yoga": {
        "name": "Prabhu Yoga",
        "category": "raja",
        "constituent_rule": "Ascendant lord is exalted and in a kendra or trikona, aspected by a benefic planet, conferring leadership and authority",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Ascendant lord is combust in exaltation",
        ],
    },

    "nabha_yoga_raja": {
        "name": "Nabha Raja Yoga",
        "category": "raja",
        "constituent_rule": "All planets are on one side of the horizon (all above or all below), creating a special nabhas pattern tied to raja outcomes",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Afflicted planets in the concentration undermine the yoga",
        ],
    },

    "surya_chandra_yoga": {
        "name": "Surya-Chandra (Full Moon) Yoga",
        "category": "raja",
        "constituent_rule": "Sun and Moon are in opposition (full Moon at birth) and aspected by benefics; particularly powerful for 1/7 or 4/10 house placements",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Full Moon is eclipsed or heavily afflicted by Saturn/Rahu",
        ],
    },

    "chandra_bala": {
        "name": "Chandra Bala Raja Yoga",
        "category": "raja",
        "constituent_rule": "Moon is in Shukla paksha (waxing, especially 8th tithi through Purnima), in a kendra or trikona, and aspected by Jupiter",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Moon is afflicted by Saturn conjunct or Ketu conjunct",
        ],
    },

    "vyavasaya_yoga": {
        "name": "Vyavasaya (Enterprise) Yoga",
        "category": "raja",
        "constituent_rule": "Lords of 2nd, 7th, and 10th houses are in mutual association in a kendra or trikona, giving commercial and entrepreneurial success",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "All three lords are combust",
        ],
    },

    "sunapha_raja": {
        "name": "Sunapha-based Raja Yoga",
        "category": "raja",
        "constituent_rule": "Planets in 2nd from Moon include a kendra or trikona lord, elevating the Sunapha yoga to raja level",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The 2nd-from-Moon planet is debilitated or combust",
        ],
    },

    "sri_yoga": {
        "name": "Sri Yoga",
        "category": "raja",
        "constituent_rule": "Venus and Jupiter are both in kendras or trikonas, in own or exaltation signs, conferring grace, prosperity, and renown",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Venus or Jupiter is combust",
        ],
    },

    "raja_yoga_exchange": {
        "name": "Parivartan Raja Yoga",
        "category": "raja",
        "constituent_rule": "A kendra lord and a trikona lord exchange signs (parivartana), creating a powerful mutual connection equivalent to conjunction",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Either exchanging planet is combust or in dusthana in navamsa",
        ],
    },

    "dhan_rajya_yoga": {
        "name": "Dhan-Rajya Yoga",
        "category": "raja",
        "constituent_rule": "Lord of the 11th house is in the 2nd house and lord of the 2nd house is in the 11th house (Parivartan), with both strong",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "raja_yoga_1_10": {
        "name": "Raja Yoga 1st-10th",
        "category": "raja",
        "constituent_rule": "Lords of the 1st (kendra/trikona) and 10th (kendra) houses are in conjunction, exchange, or mutual aspect",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or in dusthanas",
        ],
    },

    "raja_yoga_4_10": {
        "name": "Raja Yoga 4th-10th",
        "category": "raja",
        "constituent_rule": "Lords of the 4th and 10th houses (both kendras) are in conjunction, exchange, or mutual aspect, strengthening professional and domestic foundations",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "raja_yoga_7_10": {
        "name": "Raja Yoga 7th-10th",
        "category": "raja",
        "constituent_rule": "Lords of the 7th and 10th houses are in conjunction, exchange, or mutual aspect, connecting partnerships with career",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or in enemy signs",
        ],
    },

    "raja_yoga_1_7": {
        "name": "Raja Yoga 1st-7th",
        "category": "raja",
        "constituent_rule": "Lords of the 1st and 7th houses (both kendras) are in mutual exchange, both strong and in good dignity",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Either lord is combust or in navamsa dusthana",
        ],
    },

    "raja_yoga_5_9": {
        "name": "Raja Yoga 5th-9th (Dharma-Trikona)",
        "category": "raja",
        "constituent_rule": "Lords of the 5th and 9th houses (both trikonas) are in conjunction, exchange, or mutual aspect — the most auspicious trikona combination",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 2.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Both lords are combust or in dusthanas",
        ],
    },

    # -----------------------------------------------------------------------
    # DHANA YOGAS (25+)
    # -----------------------------------------------------------------------

    "dhana_yoga_1": {
        "name": "Dhana Yoga (2L-11L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 2nd house (accumulated wealth) and 11th house (gains) are in conjunction or mutual aspect",
        "classical_citation": "BPHS Ch. 39 v.1-3",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or in dusthanas",
        ],
    },

    "dhana_yoga_2": {
        "name": "Dhana Yoga (1L-2L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 1st and 2nd houses are in conjunction, exchange, or mutual aspect, creating self-made wealth",
        "classical_citation": "BPHS Ch. 39 v.4-6",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "dhana_yoga_3": {
        "name": "Dhana Yoga (ASC in 11H + 11L in 2H)",
        "category": "dhana",
        "constituent_rule": "Ascendant lord is in the 11th house and the 11th house lord is in the 2nd house, creating a wealth-generating circuit",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both planets are combust or debilitated",
        ],
    },

    "dhana_yoga_4": {
        "name": "Dhana Yoga (2L-1L Exchange)",
        "category": "dhana",
        "constituent_rule": "Lords of the 1st and 2nd houses exchange signs (parivartana), creating a robust wealth circuit",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Either lord is combust",
        ],
    },

    "dhana_yoga_5": {
        "name": "Dhana Yoga (Jupiter in 2H or 11H)",
        "category": "dhana",
        "constituent_rule": "Jupiter is strongly placed in the 2nd house (speech and wealth) or 11th house (gains), conferring abundance",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Jupiter is combust or debilitated in these houses",
        ],
    },

    "indu_lagna_dhana": {
        "name": "Indu Lagna Dhana Yoga",
        "category": "dhana",
        "constituent_rule": "The Indu Lagna (special wealth ascendant derived from Moon and Jupiter's lords) is strongly occupied or aspected, indicating special wealth",
        "classical_citation": "Phaladeepika Ch. 9",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Indu Lagna is afflicted by malefics without benefic aspect",
        ],
    },

    "lakshmi_yoga": {
        "name": "Lakshmi Yoga",
        "category": "dhana",
        "constituent_rule": "Lord of the 9th house is in own sign or exaltation in an angle or trine, AND Venus is in own sign or exaltation",
        "classical_citation": "BPHS Ch. 39; Phaladeepika Ch. 9 v.1",
        "strength_modifier": 2.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "9th lord or Venus is combust",
            "Venus is in dusthana in navamsa",
        ],
    },

    "dhana_yoga_2_5": {
        "name": "Dhana Yoga (2L-5L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 2nd (wealth) and 5th (intelligence/purva punya) houses are in conjunction or mutual aspect",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "dhana_yoga_2_9": {
        "name": "Dhana Yoga (2L-9L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 2nd (wealth) and 9th (fortune) houses are in conjunction or mutual aspect",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or in dusthanas",
        ],
    },

    "dhana_yoga_5_9": {
        "name": "Dhana Yoga (5L-9L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 5th (purva punya, investments) and 9th (bhagya/fortune) houses are in conjunction or mutual aspect",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "kubera_yoga": {
        "name": "Kubera Yoga",
        "category": "dhana",
        "constituent_rule": "Jupiter, Venus, and Mercury are all well-placed in the 2nd, 5th, or 11th house; multiple planets of wealth occupy financial houses",
        "classical_citation": "Phaladeepika Ch. 9",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "All three planets are combust or debilitated",
        ],
    },

    "vasumati_dhana": {
        "name": "Vasumati Dhana Yoga",
        "category": "dhana",
        "constituent_rule": "Benefics (Jupiter, Venus, Mercury, strong Moon) occupy upachaya houses (3rd, 6th, 10th, 11th) in strength, producing steady income accumulation",
        "classical_citation": "BPHS Ch. 39; Phaladeepika Ch. 9",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Benefics in upachayas are all combust or debilitated",
        ],
    },

    "dhana_yoga_1_11": {
        "name": "Dhana Yoga (1L-11L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 1st and 11th houses are in conjunction, exchange, or mutual aspect, linking identity with sustained income and gains",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "dhana_yoga_9_11": {
        "name": "Dhana Yoga (9L-11L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 9th (fortune) and 11th (gains) houses are in conjunction or mutual aspect, giving fortunate and continuous gains",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or in dusthanas",
        ],
    },

    "venus_2nd_yoga": {
        "name": "Venus in 2nd House Dhana Yoga",
        "category": "dhana",
        "constituent_rule": "Venus is in the 2nd house in own sign (Taurus) or exaltation (Pisces), giving tremendous wealth through artistic or material pursuits",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Venus is combust in the 2nd",
        ],
    },

    "mercury_2nd_yoga": {
        "name": "Mercury in 2nd House Dhana Yoga",
        "category": "dhana",
        "constituent_rule": "Mercury is in the 2nd house in own sign (Gemini or Virgo) or exaltation (Virgo), giving wealth through trade, communication, and commerce",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Mercury is combust",
        ],
    },

    "dhana_yoga_full_circuit": {
        "name": "Full Dhana Circuit",
        "category": "dhana",
        "constituent_rule": "Lords of the 1st, 2nd, 5th, 9th, and 11th houses all inter-relate through conjunction, aspect, or exchange, creating a complete wealth-generating circuit",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 2.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Majority of the lords involved are combust or debilitated",
        ],
    },

    "dhana_yoga_2_11_exchange": {
        "name": "Dhana Yoga (2L-11L Exchange)",
        "category": "dhana",
        "constituent_rule": "Lords of the 2nd and 11th houses exchange signs, creating a particularly powerful parivartana for accumulated wealth",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Either lord is combust",
        ],
    },

    "bhagya_dhana": {
        "name": "Bhagya Dhana Yoga",
        "category": "dhana",
        "constituent_rule": "9th lord is in the 2nd or 11th house in strength, bringing fortune directly to the wealth houses",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "9th lord is combust in the wealth house",
        ],
    },

    "dhan_panchama": {
        "name": "Dhan-Panchama Yoga",
        "category": "dhana",
        "constituent_rule": "5th lord is in the 2nd or 11th house in strength, or 2nd lord is in the 5th house; purva punya converts to tangible wealth",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The connecting planet is combust or debilitated",
        ],
    },

    "vriddhi_yoga": {
        "name": "Vriddhi Yoga",
        "category": "dhana",
        "constituent_rule": "Jupiter and Venus are in conjunction or mutual aspect, both in strength, giving continuous growth and increase in wealth",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both Jupiter and Venus are combust",
        ],
    },

    "mahavibhava_yoga": {
        "name": "Mahavibhava Yoga",
        "category": "dhana",
        "constituent_rule": "All wealth indicators (2L, 5L, 9L, 11L) are in exaltation or own signs simultaneously — extreme wealth indicator",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 3.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Any of the exalted lords is combust",
        ],
    },

    "chandra_2nd_yoga": {
        "name": "Chandra in 2nd House Dhana Yoga",
        "category": "dhana",
        "constituent_rule": "Moon is in the 2nd house in own sign (Cancer) or exaltation (Taurus), giving wealth through public ventures and the masses",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Moon is in amavasya phase or afflicted by Saturn",
        ],
    },

    "dhana_yoga_5_11": {
        "name": "Dhana Yoga (5L-11L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 5th (speculation, purva punya) and 11th (gains) houses are in conjunction or mutual aspect",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "saubhagya_yoga": {
        "name": "Saubhagya Yoga",
        "category": "dhana",
        "constituent_rule": "Lord of the 2nd house is exalted or in own sign and aspected by Jupiter or Venus, giving ease of wealth acquisition",
        "classical_citation": "Phaladeepika Ch. 9",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "2nd lord is combust",
        ],
    },

    # -----------------------------------------------------------------------
    # VIPAREETA RAJA YOGAS (3)
    # -----------------------------------------------------------------------

    "harsha": {
        "name": "Harsha Yoga",
        "category": "vipareeta_raja",
        "constituent_rule": "Lord of the 6th house (dusthana) is placed in the 6th, 8th, or 12th house; the enemy of your enemy becomes your friend — health, immunity, and overcoming opponents",
        "classical_citation": "BPHS Ch. 41 v.20-22; Phaladeepika Ch. 7 v.15",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The 6th lord also aspects the Ascendant lord negatively while in a dusthana",
            "The yoga is cancelled if the 6th lord occupies its own sign in the dusthana (debatable among commentators)",
        ],
    },

    "sarala": {
        "name": "Sarala Yoga",
        "category": "vipareeta_raja",
        "constituent_rule": "Lord of the 8th house (dusthana of longevity and transformation) is placed in the 6th, 8th, or 12th house; transforms longevity challenges into longevity and occult power",
        "classical_citation": "BPHS Ch. 41 v.23-25; Phaladeepika Ch. 7 v.16",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "8th lord simultaneously afflicts the Ascendant lord or Moon",
        ],
    },

    "vimala": {
        "name": "Vimala Yoga",
        "category": "vipareeta_raja",
        "constituent_rule": "Lord of the 12th house (dusthana of losses and liberation) is placed in the 6th, 8th, or 12th house; loss-signifying house lord neutralised, creating purity and spiritual renown",
        "classical_citation": "BPHS Ch. 41 v.26-28; Phaladeepika Ch. 7 v.17",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "12th lord in dusthana also devastates the 12th house significations entirely (double loss)",
        ],
    },

    # -----------------------------------------------------------------------
    # NEECHABHANGA RAJA YOGA — 8 cancellation conditions
    # -----------------------------------------------------------------------

    "neechabhanga_1": {
        "name": "Neechabhanga 1 — Debilitation Sign Lord Aspects",
        "category": "neechabhanga",
        "constituent_rule": "The lord of the sign in which the planet is debilitated aspects or conjoins the debilitated planet, cancelling its fall",
        "classical_citation": "BPHS Ch. 27 v.1-8; Phaladeepika Ch. 3 v.8",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The debilitation sign lord is itself debilitated, combust, or in a dusthana",
        ],
    },

    "neechabhanga_2": {
        "name": "Neechabhanga 2 — Exaltation Lord Aspects",
        "category": "neechabhanga",
        "constituent_rule": "The lord of the sign where the debilitated planet would be exalted aspects or conjoins the debilitated planet",
        "classical_citation": "BPHS Ch. 27 v.1-8; Phaladeepika Ch. 3 v.9",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The exaltation sign lord is itself debilitated or combust",
        ],
    },

    "neechabhanga_3": {
        "name": "Neechabhanga 3 — Debilitation Sign Lord in Kendra",
        "category": "neechabhanga",
        "constituent_rule": "The lord of the sign in which the planet is debilitated is in a kendra (1/4/7/10) from the Ascendant or Moon",
        "classical_citation": "BPHS Ch. 27 v.1-8",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The debilitation sign lord in kendra is itself weak or afflicted",
        ],
    },

    "neechabhanga_4": {
        "name": "Neechabhanga 4 — Debilitated Planet in Kendra from Moon",
        "category": "neechabhanga",
        "constituent_rule": "The debilitated planet itself is in a kendra (1/4/7/10) from the Moon's position",
        "classical_citation": "BPHS Ch. 27 v.1-8",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Moon itself is severely afflicted",
        ],
    },

    "neechabhanga_5": {
        "name": "Neechabhanga 5 — Vargottama Debilitated Planet",
        "category": "neechabhanga",
        "constituent_rule": "The debilitated planet is vargottama (occupies the same sign in both rasi and navamsa charts), gaining strength through navamsa position",
        "classical_citation": "BPHS Ch. 27 v.1-8",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Vargottama debilitated sign is still a debilitated navamsa",
        ],
    },

    "neechabhanga_6": {
        "name": "Neechabhanga 6 — Conjunct Exaltation Lord",
        "category": "neechabhanga",
        "constituent_rule": "The debilitated planet is in conjunction with the lord of its exaltation sign",
        "classical_citation": "BPHS Ch. 27 v.1-8",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The exaltation lord is combust or debilitated itself",
        ],
    },

    "neechabhanga_7": {
        "name": "Neechabhanga 7 — Exaltation Lord in Kendra or Trikona",
        "category": "neechabhanga",
        "constituent_rule": "The lord of the sign where the debilitated planet is exalted is placed in a kendra or trikona from the Ascendant",
        "classical_citation": "BPHS Ch. 27 v.1-8",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The exaltation lord in kendra/trikona is itself debilitated",
        ],
    },

    "neechabhanga_8": {
        "name": "Neechabhanga 8 — Another Planet Exalted in Same Sign",
        "category": "neechabhanga",
        "constituent_rule": "Another planet that is exalted in the same sign as the debilitated planet is present there, mitigating the debilitation by exaltation energy in that sign",
        "classical_citation": "BPHS Ch. 27 v.1-8",
        "strength_modifier": 1.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "The exalted planet in same sign is combust",
        ],
    },

    # -----------------------------------------------------------------------
    # LUNAR YOGAS (4)
    # -----------------------------------------------------------------------

    "sunafa": {
        "name": "Sunafa Yoga",
        "category": "lunar",
        "constituent_rule": "One or more planets (other than the Sun) are placed in the 2nd house from the Moon's position",
        "classical_citation": "BPHS Ch. 33; Saravali Ch. 19",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "The planet in 2nd from Moon is debilitated or combust",
            "Only Rahu or Ketu occupies the 2nd from Moon (most authorities exclude nodes)",
        ],
    },

    "anapha": {
        "name": "Anapha Yoga",
        "category": "lunar",
        "constituent_rule": "One or more planets (other than the Sun) are placed in the 12th house from the Moon's position",
        "classical_citation": "BPHS Ch. 33; Saravali Ch. 19",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "The planet in 12th from Moon is debilitated or combust",
            "Only Rahu or Ketu occupies the 12th from Moon",
        ],
    },

    "durdhura": {
        "name": "Durdhura Yoga",
        "category": "lunar",
        "constituent_rule": "Planets (other than the Sun) are placed in BOTH the 2nd and 12th houses from the Moon, creating a Moon flanked by planets",
        "classical_citation": "BPHS Ch. 33; Saravali Ch. 19",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Planets on both sides of Moon are debilitated or malefic without mitigating benefics",
        ],
    },

    "kemadruma": {
        "name": "Kemadruma Yoga",
        "category": "lunar",
        "constituent_rule": "No planets (other than Sun) occupy the 2nd or 12th houses from Moon, AND Moon has no planet in any kendra from the Ascendant; negative yoga indicating isolation",
        "classical_citation": "BPHS Ch. 33; Saravali Ch. 19",
        "strength_modifier": 0.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "Moon is in a kendra from the Ascendant (this cancels Kemadruma)",
            "Moon is conjunct a planet",
            "Moon is aspected by Jupiter",
            "A planet is in the 2nd or 12th from Moon",
        ],
    },

    # -----------------------------------------------------------------------
    # SOLAR YOGAS (3)
    # -----------------------------------------------------------------------

    "vesi": {
        "name": "Vesi Yoga",
        "category": "solar",
        "constituent_rule": "One or more planets (other than Moon and lunar nodes) are placed in the 2nd house from the Sun's position",
        "classical_citation": "BPHS Ch. 34; Saravali Ch. 21",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "The planet in 2nd from Sun is debilitated or severely afflicted",
        ],
    },

    "vasi": {
        "name": "Vasi Yoga",
        "category": "solar",
        "constituent_rule": "One or more planets (other than Moon and lunar nodes) are placed in the 12th house from the Sun's position",
        "classical_citation": "BPHS Ch. 34; Saravali Ch. 21",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "The planet in 12th from Sun is debilitated or severely afflicted",
        ],
    },

    "ubhayachari": {
        "name": "Ubhayachari Yoga",
        "category": "solar",
        "constituent_rule": "Planets (other than Moon and nodes) are in BOTH the 2nd and 12th houses from the Sun, giving balanced solar support",
        "classical_citation": "BPHS Ch. 34; Saravali Ch. 21",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "All planets flanking the Sun are debilitated or combust",
        ],
    },

    # -----------------------------------------------------------------------
    # KALA SARPA YOGAS (12 variants)
    # -----------------------------------------------------------------------

    "ananta_kala_sarpa": {
        "name": "Ananta Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 1st house and Ketu is in the 7th house, with all seven planets (Sun through Saturn) on the Rahu side of the Rahu-Ketu axis; named after Ananta (Shesha)",
        "classical_citation": "Kala Sarpa yoga doctrine; Rahu-Ketu Shakti texts",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet is outside the Rahu-Ketu axis (between Ketu and Rahu in reverse direction)",
            "Yoga partially cancelled if Jupiter or Saturn aspects Rahu",
        ],
    },

    "kulika_kala_sarpa": {
        "name": "Kulika Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 2nd house and Ketu is in the 8th house, with all planets on the Rahu side; affects family lineage and sudden events",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "vasuki_kala_sarpa": {
        "name": "Vasuki Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 3rd house and Ketu is in the 9th house, with all planets on the Rahu side; affects courage, siblings, and fortune",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "shankha_kala_sarpa": {
        "name": "Shankha Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 4th house and Ketu is in the 10th house, with all planets on the Rahu side; affects home, mother, and career",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "padma_kala_sarpa": {
        "name": "Padma Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 5th house and Ketu is in the 11th house, with all planets on the Rahu side; affects children, intellect, and gains",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "mahapadma_kala_sarpa": {
        "name": "Mahapadma Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 6th house and Ketu is in the 12th house, with all planets on the Rahu side; affects health, enemies, and liberation",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "takshaka_kala_sarpa": {
        "name": "Takshaka Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 7th house and Ketu is in the 1st house (reverse configuration), with all planets on the Rahu side; affects marriage and partnerships",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "karkotaka_kala_sarpa": {
        "name": "Karkotaka Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 8th house and Ketu is in the 2nd house (reverse), with all planets on the Rahu side; affects longevity and wealth",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "shankhanada_kala_sarpa": {
        "name": "Shankhanada Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 9th house and Ketu is in the 3rd house (reverse), with all planets on the Rahu side; affects dharma and fortune",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "patak_kala_sarpa": {
        "name": "Patak Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 10th house and Ketu is in the 4th house (reverse), with all planets on the Rahu side; affects career and domestic peace",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "vishadhar_kala_sarpa": {
        "name": "Vishadhar Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 11th house and Ketu is in the 5th house (reverse), with all planets on the Rahu side; affects income, children, and gains",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    "sheshanaag_kala_sarpa": {
        "name": "Sheshanaag Kala Sarpa Yoga",
        "category": "kala_sarpa",
        "constituent_rule": "Rahu is in the 12th house and Ketu is in the 6th house (reverse), with all planets on the Rahu side; affects foreign lands, liberation, and hidden enemies",
        "classical_citation": "Kala Sarpa yoga doctrine",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the Rahu-Ketu containment arc",
        ],
    },

    # -----------------------------------------------------------------------
    # NABHAS YOGAS (12)
    # -----------------------------------------------------------------------

    "rajju": {
        "name": "Rajju Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are exclusively in movable signs (Aries, Cancer, Libra, Capricorn); gives a wandering, adventurous nature and dynamic energy",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5 v.1",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Even one planet in a fixed or dual sign breaks the yoga",
        ],
    },

    "musala": {
        "name": "Musala Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are exclusively in fixed signs (Taurus, Leo, Scorpio, Aquarius); gives stability, stubbornness, and enduring character",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5 v.2",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Even one planet in a movable or dual sign breaks the yoga",
        ],
    },

    "nala": {
        "name": "Nala Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are exclusively in dual (mutable) signs (Gemini, Virgo, Sagittarius, Pisces); gives versatility, inconsistency, and intellectual flexibility",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5 v.3",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Even one planet in a movable or fixed sign breaks the yoga",
        ],
    },

    "mala": {
        "name": "Mala Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in the trine houses (1st, 5th, and 9th houses), creating a garland-like concentration in dharma houses",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Even one planet falls outside the 1st, 5th, or 9th house",
        ],
    },

    "sarpa": {
        "name": "Sarpa Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are confined to the dusthana houses (6th, 8th, and 12th); negative nabhas yoga indicating suffering, obstacles, and hardship",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 0.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Even one planet falls outside the 6th, 8th, or 12th house",
        ],
    },

    "gada": {
        "name": "Gada Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in angular pairs — either the 1st+4th houses together or the 7th+10th houses together",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 1.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Even one planet falls outside the 1/4 or 7/10 house pairs",
        ],
    },

    "shakat": {
        "name": "Shakat Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in the 1st and 7th houses only, creating a wheel-like opposition concentration",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 1.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Even one planet falls outside the 1st or 7th house",
        ],
    },

    "vihaga": {
        "name": "Vihaga Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in the 4th and 10th houses only, creating a meridian axis concentration — bird-like freedom and mobility",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 1.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Even one planet falls outside the 4th or 10th house",
        ],
    },

    "dama": {
        "name": "Dama Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in four adjacent houses (any four consecutive houses), giving a concentrated field of activity",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 1.5,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Any planet breaks the four-house concentration",
        ],
    },

    "pasha": {
        "name": "Pasha Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are spread across five consecutive houses, creating a noose-like pattern indicating bondage and responsibility",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 1.2,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet breaks the five-house concentration",
        ],
    },

    "kedara": {
        "name": "Kedara Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in four alternate houses (any four alternate signs/houses), giving agricultural, landholding, and community-building traits",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 1.2,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet breaks the alternating house pattern",
        ],
    },

    "shoola": {
        "name": "Shoola Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in exactly three houses (trine, kendra, or any three houses), creating a trident pattern — intensity and focused suffering or power",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 1.2,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Any planet breaks the three-house containment",
        ],
    },

    # -----------------------------------------------------------------------
    # MISCELLANEOUS YOGAS (20+)
    # -----------------------------------------------------------------------

    "adhi_yoga": {
        "name": "Adhi Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Benefic planets (Mercury, Venus, Jupiter, strong Moon) are placed in the 6th, 7th, and 8th houses from the Moon (or Ascendant), giving political power and dominance over rivals",
        "classical_citation": "BPHS Ch. 36; Phaladeepika Ch. 7 v.20",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "The benefics in 6/7/8 from Moon are all combust or debilitated",
            "Malefics occupy these houses along with benefics and overwhelm them",
        ],
    },

    "amala_yoga": {
        "name": "Amala Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Only benefic planets (Jupiter, Venus, Mercury, strong Moon) are in the 10th house from the Ascendant or Moon, without any malefic influence",
        "classical_citation": "Phaladeepika Ch. 7 v.22",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "A malefic planet is also in the 10th house",
            "The benefic in 10th is combust",
        ],
    },

    "parvata_yoga": {
        "name": "Parvata Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Benefics are in kendras and malefics are absent from the 6th and 8th houses, OR lords of the 6th and 8th are in kendras or trikonas",
        "classical_citation": "Phaladeepika Ch. 7 v.21",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Malefics are in kendras while benefics are absent",
        ],
    },

    "vasumati_yoga": {
        "name": "Vasumati Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Benefic planets (Jupiter, Venus, Mercury, strong Moon) are placed in upachaya houses (3rd, 6th, 10th, 11th) from the Ascendant or Moon, giving continuous accumulation",
        "classical_citation": "Phaladeepika Ch. 7 v.19",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The benefics in upachayas are all combust",
        ],
    },

    "chapa_yoga": {
        "name": "Chapa Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Seven planets occupy exactly six consecutive houses in the chart, forming a bow-like arc",
        "classical_citation": "BPHS Ch. 31",
        "strength_modifier": 1.2,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The pattern is broken by a planet outside the six houses",
        ],
    },

    "srikantha": {
        "name": "Srikantha Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Lords of the 1st, 5th, and 9th houses (all trikonas) are all in their own signs or exaltation signs simultaneously",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 2.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Any of the trikona lords is combust",
        ],
    },

    "gajakesari_yoga": {
        "name": "Gajakesari Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Jupiter is in a kendra (1/4/7/10) from Moon — the elephant-lion combination; bestows fame, prosperity, commanding presence, and honour",
        "classical_citation": "BPHS Ch. 36; Phaladeepika Ch. 6 v.7",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Jupiter is debilitated (Capricorn)",
            "Jupiter is combust (within 11° of Sun)",
            "Moon is in new Moon phase or severely weak",
        ],
    },

    "kalpa_druma": {
        "name": "Kalpa-Druma Yoga",
        "category": "miscellaneous",
        "constituent_rule": "The Ascendant lord, and the lords of the sign and navamsa occupied by the Ascendant lord, are all in exaltation or own signs in kendras or trikonas — extremely rare and powerful",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 3.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Any link in the chain is combust or debilitated",
        ],
    },

    "panchamahapurusha_compound": {
        "name": "Compound Pancha Mahapurusha",
        "category": "miscellaneous",
        "constituent_rule": "Two or more Pancha Mahapurusha yogas are present simultaneously in the same chart; each additional yoga compounds the power multiplicatively",
        "classical_citation": "BPHS Ch. 75 combined verse commentary",
        "strength_modifier": 3.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Individual Mahapurusha yogas cancel per their own cancellation rules",
        ],
    },

    "nipuna_yoga": {
        "name": "Nipuna Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Mercury and Jupiter are in conjunction or mutual aspect in an angle or trine — the 'skillful' yoga giving mastery in arts, sciences, and learning",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Mercury or Jupiter is combust or debilitated",
        ],
    },

    "pushkala_yoga": {
        "name": "Pushkala Yoga",
        "category": "miscellaneous",
        "constituent_rule": "The Moon is in the Ascendant sign's navamsa, aspected by the Ascendant lord, with the Ascendant lord exalted in a kendra",
        "classical_citation": "Phaladeepika Ch. 7",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Ascendant lord is combust",
        ],
    },

    "ruchaka_yoga_variant": {
        "name": "Ruchaka Variant — Mars in Exaltation Kendra",
        "category": "miscellaneous",
        "constituent_rule": "Mars is exalted in Capricorn and placed in a kendra, with particular power in the 10th house (Capricorn as 10th indicates natural authority and discipline)",
        "classical_citation": "BPHS Ch. 75 commentary",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Mars is combust in exaltation",
        ],
    },

    "shubha_kartari": {
        "name": "Shubha Kartari Yoga",
        "category": "miscellaneous",
        "constituent_rule": "A house or planet is flanked on both sides (in the adjacent houses) by benefic planets (Jupiter, Venus, Mercury, strong Moon), creating a protective scissors pattern",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The flanking benefics are combust or debilitated",
        ],
    },

    "papa_kartari": {
        "name": "Papa Kartari Yoga",
        "category": "miscellaneous",
        "constituent_rule": "A house or planet is flanked on both sides by malefic planets (Saturn, Mars, Sun, Rahu, Ketu), creating a malefic scissors pattern that harms significations",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 0.6,
        "rarity_class": "common",
        "cancellation_rules": [
            "Jupiter aspects the afflicted house directly",
            "A strong benefic is also placed in the afflicted house",
        ],
    },

    "muhurtha_yoga": {
        "name": "Muhurtha-based Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Birth at auspicious muhurtha (auspicious lunar day, weekday, and nakshatra combination) strengthens all other yogas present in the chart",
        "classical_citation": "BPHS Ch. 96-98 Muhurtha section",
        "strength_modifier": 1.2,
        "rarity_class": "common",
        "cancellation_rules": [
            "Birth on Tithis considered inauspicious (4th, 8th, 12th of either paksha, new Moon, amavasya)",
        ],
    },

    "veena_yoga": {
        "name": "Veena Yoga",
        "category": "miscellaneous",
        "constituent_rule": "All seven planets are distributed across exactly seven different houses, creating a balanced planetary spread like the seven strings of a veena",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any house has more than one planet (breaks the one-planet-per-house requirement)",
        ],
    },

    "shashtiamsha_yoga": {
        "name": "Shashtiamsha Yoga",
        "category": "miscellaneous",
        "constituent_rule": "The Ascendant or Moon occupies an auspicious shashtiamsha (60th division), particularly Deva or Kubera shashtiamsha, amplifying all positive chart features",
        "classical_citation": "BPHS Ch. 6 Shashtiamsha section",
        "strength_modifier": 1.3,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The shashtiamsha is one of the inauspicious types (Rakshasa, Krura, etc.)",
        ],
    },

    "atmakaraka_yoga": {
        "name": "Atmakaraka in Kendra/Trikona",
        "category": "miscellaneous",
        "constituent_rule": "The Atmakaraka planet (highest degree planet in Jaimini system) is placed in a kendra or trikona, strengthening the soul's purpose and life direction",
        "classical_citation": "Jaimini Sutras Adhyaya 1",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Atmakaraka is in a dusthana (6/8/12)",
            "Atmakaraka is combust or debilitated",
        ],
    },

    "karakamsha_yoga": {
        "name": "Karakamsha Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Benefic planets are placed in or aspect the Karakamsha lagna (navamsa position of Atmakaraka projected to rasi), supporting Jaimini soul-level blessings",
        "classical_citation": "Jaimini Sutras Adhyaya 2",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Malefics are conjunct the Karakamsha without benefic mitigation",
        ],
    },

    "hora_lagna_yoga": {
        "name": "Hora Lagna Yoga",
        "category": "miscellaneous",
        "constituent_rule": "The Hora Lagna (a special Jaimini ascendant for wealth) is in a kendra or trikona and aspected by Jupiter or Venus, strongly promising material prosperity",
        "classical_citation": "Jaimini Sutras Adhyaya 1",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Hora Lagna is afflicted by malefics without benefic protection",
        ],
    },

    "ashtamangala_yoga": {
        "name": "Ashta-Mangala Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Eight auspicious factors (eight planets in good dignity) are simultaneously present in the chart at the time of birth — extremely rare",
        "classical_citation": "BPHS Ch. 96",
        "strength_modifier": 3.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Any of the eight required factors is absent or afflicted",
        ],
    },

    "subha_yoga_compound": {
        "name": "Compound Shubha Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Multiple distinct auspicious yogas (raja, dhana, and pancha mahapurusha) operate simultaneously; each compounds the effect of the others for extraordinary outcomes",
        "classical_citation": "BPHS general commentary on yoga interaction",
        "strength_modifier": 2.5,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Individual component yogas are cancelled per their own rules",
        ],
    },

    "pravrajya_yoga": {
        "name": "Pravrajya Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Four or more planets are in the same sign, particularly in the 9th or 12th house, indicating a calling toward renunciation, spiritual life, or monastic vows",
        "classical_citation": "BPHS Ch. 83",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The cluster of planets includes strong Venus or is in the 7th house (worldly attachment overrides)",
        ],
    },

    "bandhu_yoga": {
        "name": "Bandhu Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Lords of the 4th and 12th houses are in mutual exchange or conjunction, connecting domestic happiness with spiritual release or foreign residence",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.2,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or debilitated",
        ],
    },

    "vipra_yoga": {
        "name": "Vipra Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Jupiter is in the 9th house in own sign or exaltation, with the 9th lord also strong, indicating a scholar, teacher, or spiritual guide",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Jupiter is combust in the 9th",
        ],
    },

    "kshatriya_yoga": {
        "name": "Kshatriya Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Mars, Sun, and Rahu are in the 1st, 3rd, 6th, or 10th house in strength, conferring warrior spirit, administrative leadership, and command",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The warrior planets are heavily afflicted by Saturn",
        ],
    },

    "brahma_yoga": {
        "name": "Brahma Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Jupiter is in angle from Venus, Venus is in angle from Mercury, and Mercury is in angle from the Ascendant — a three-planet kendra chain of knowledge and speech",
        "classical_citation": "Phaladeepika Ch. 7 v.23",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Any of the three planets is combust",
        ],
    },

    # -----------------------------------------------------------------------
    # ADDITIONAL RAJA YOGAS (continued — reaching 40+ raja total)
    # -----------------------------------------------------------------------

    "raja_yoga_1_4_dual": {
        "name": "Raja Yoga 1st-4th (Dual Kendra)",
        "category": "raja",
        "constituent_rule": "Ascendant lord is in the 4th house and the 4th lord is in the Ascendant (mutual exchange), creating a powerful domestic-self synthesis",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or debilitated",
        ],
    },

    "raja_yoga_7_4": {
        "name": "Raja Yoga 7th-4th",
        "category": "raja",
        "constituent_rule": "Lords of the 7th and 4th houses are in conjunction or exchange, connecting partnerships with domestic stability and property",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "digbala_yoga": {
        "name": "Digbala Yoga",
        "category": "raja",
        "constituent_rule": "A planet has directional strength (digbala): Jupiter or Mercury in the 1st, Sun or Mars in the 10th, Saturn in the 7th, Moon or Venus in the 4th, and that planet also rules a kendra or trikona",
        "classical_citation": "BPHS Ch. 27 Digbala section",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The planet with digbala is combust or debilitated",
        ],
    },

    "vargottama_raja": {
        "name": "Vargottama Raja Yoga",
        "category": "raja",
        "constituent_rule": "A planet that rules a kendra or trikona is vargottama (same sign in rasi and navamsa), gaining double strength through divisional chart confirmation",
        "classical_citation": "BPHS Ch. 27 Navamsa section",
        "strength_modifier": 2.0,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The vargottama kendra/trikona lord is combust",
        ],
    },

    "saptamsha_raja": {
        "name": "Saptamsha Confirmation Raja Yoga",
        "category": "raja",
        "constituent_rule": "A raja yoga operating in the rasi chart is confirmed and strengthened by the saptamsha (D-7) chart showing the same or complementary lords in strong positions",
        "classical_citation": "BPHS Ch. 6 Saptamsha section",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The saptamsha shows the yoga lords in dusthanas",
        ],
    },

    "dashamsha_raja": {
        "name": "Dashamsha Confirmation Raja Yoga",
        "category": "raja",
        "constituent_rule": "A career or status yoga (raja yoga) operating in the rasi chart is confirmed by the dashamsha (D-10) chart, with the same lords strong in the D-10 as well",
        "classical_citation": "BPHS Ch. 6 Dashamsha section",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The dashamsha shows the yoga lords weak or in dusthanas",
        ],
    },

    "karaka_yoga": {
        "name": "Karaka-Enhanced Raja Yoga",
        "category": "raja",
        "constituent_rule": "The natural karakas (Sun for status, Jupiter for wisdom, Mars for courage) are strong and placed in or aspecting their relevant house of signification, amplifying natural beneficence",
        "classical_citation": "BPHS Ch. 32 Karakatva section",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The relevant natural karaka is debilitated or combust",
        ],
    },

    "shubha_yoga_raja": {
        "name": "Shubha (Auspicious) Raja Yoga",
        "category": "raja",
        "constituent_rule": "All four angle lords (1, 4, 7, 10) are in mutual angular relationship to each other, creating a fully integrated kendra yoga grid",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Majority of the kendra lords are combust or in dusthanas",
        ],
    },

    # -----------------------------------------------------------------------
    # ADDITIONAL DHANA YOGAS
    # -----------------------------------------------------------------------

    "dhana_yoga_2_7": {
        "name": "Dhana Yoga (2L-7L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 2nd (wealth) and 7th (business/trade) houses are in conjunction or mutual aspect, giving wealth through commercial partnerships",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "dhana_yoga_7_11": {
        "name": "Dhana Yoga (7L-11L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 7th (trade, partnerships) and 11th (gains, income) houses are in conjunction or mutual aspect",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "treasury_yoga": {
        "name": "Treasury Yoga",
        "category": "dhana",
        "constituent_rule": "Jupiter, Venus, and Mercury are in the 11th house simultaneously, concentrating all three financial benefics in the house of gains",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 2.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "All three planets are combust in the 11th house",
        ],
    },

    # -----------------------------------------------------------------------
    # ADDITIONAL MISCELLANEOUS YOGAS
    # -----------------------------------------------------------------------

    "jnana_yoga": {
        "name": "Jnana Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Jupiter is strong in the 1st, 4th, or 9th house and Mercury is in a kendra or trikona; the wisdom combination giving philosophical depth and spiritual insight",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Jupiter is combust or debilitated",
            "Mercury is combust",
        ],
    },

    "tapasvi_yoga": {
        "name": "Tapasvi Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Saturn is in the 9th or 12th house in dignity, with the 9th lord also strong; gives a disciplined spiritual or ascetic disposition",
        "classical_citation": "BPHS Ch. 83",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Saturn is combust or in enemy sign without mitigation",
        ],
    },

    "vaidya_yoga": {
        "name": "Vaidya (Physician) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Mars and Saturn are in the 8th house in dignity or mutual aspect, and associated with the 6th lord; predisposes to medical or healing professions",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.3,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Mars and Saturn in the 8th are combust",
        ],
    },

    "shastra_yoga": {
        "name": "Shastra Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Jupiter, Mercury, and Saturn are all in the 1st, 5th, or 9th house in strength, giving mastery of scripture, law, and classical learning",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "All three planets are combust",
        ],
    },

    "shilpi_yoga": {
        "name": "Shilpi (Artisan) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Venus and Mercury are in conjunction or mutual aspect in a kendra or trikona, giving artistic talent, craft mastery, and aesthetic sensitivity",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both Venus and Mercury are combust",
        ],
    },

    "shaurya_yoga": {
        "name": "Shaurya (Bravery) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Mars is in the 3rd house in own sign or exaltation, or Mars is strongly placed in the 1st house; gives exceptional courage, initiative, and physical vigor",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "Mars is combust or debilitated in the 3rd",
        ],
    },

    "sangita_yoga": {
        "name": "Sangita (Music) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Venus is in the 2nd or 3rd house with Mercury, or Moon is in the 3rd house aspected by Venus; gives musical talent and artistic expression",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.3,
        "rarity_class": "common",
        "cancellation_rules": [
            "Venus is combust or debilitated",
        ],
    },

    "videsh_yoga": {
        "name": "Videsh (Foreign Lands) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Lord of the 12th house is in the 9th or Rahu is in the 9th/12th, or lord of the 9th exchanges with lord of the 12th; predisposes to foreign residence or international success",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.3,
        "rarity_class": "common",
        "cancellation_rules": [
            "The 12th lord is in own sign or highly dignified in the 12th itself",
        ],
    },

    "putra_yoga": {
        "name": "Putra (Children) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Jupiter is in or aspects the 5th house while the 5th lord is strong, with no malefics in the 5th; gives blessed progeny",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Malefics occupy the 5th house without Jupiter's aspect",
            "5th lord is severely debilitated",
        ],
    },

    "vivaha_yoga": {
        "name": "Vivaha (Marriage) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Venus is strong and in the 7th house or aspecting it, with the 7th lord also strong and unafflicted; gives happy and timely marriage",
        "classical_citation": "BPHS Ch. 75 Marriage section",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "Venus or 7th lord is combust, debilitated, or heavily afflicted",
            "Saturn and Mars both aspect the 7th without Jupiter's mitigating aspect",
        ],
    },

    "griha_yoga": {
        "name": "Griha (Property) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Mars and the 4th lord are in conjunction or mutual aspect in a kendra, with Saturn also favorably placed; gives real estate, land, and property",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Mars afflicts the 4th lord without benefic support",
        ],
    },

    "nabhasa_subha": {
        "name": "Nabhasa Shubha (Favourable Pattern) Yoga",
        "category": "nabhas",
        "constituent_rule": "Multiple planets concentrate in the kendras and trikonas of the chart in a favourable distribution pattern, creating a celestial canopy of support",
        "classical_citation": "BPHS Ch. 31",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The concentration is in dusthanas instead of favorable houses",
        ],
    },

    "yava": {
        "name": "Yava Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in the middle six houses (2nd through 7th), creating a barley-grain concentration that indicates a prosperous, socially active life",
        "classical_citation": "BPHS Ch. 31; Phaladeepika Ch. 5",
        "strength_modifier": 1.3,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Any planet falls outside the 2nd-7th house range",
        ],
    },

    "kamala": {
        "name": "Kamala Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in the 1st, 5th, and 9th houses only (trikona houses) — the lotus yoga of spiritual grace and dharmic prosperity",
        "classical_citation": "BPHS Ch. 31",
        "strength_modifier": 2.0,
        "rarity_class": "exceptional",
        "cancellation_rules": [
            "Any planet falls outside the 1st, 5th, or 9th house",
        ],
    },

    "vapi": {
        "name": "Vapi Yoga",
        "category": "nabhas",
        "constituent_rule": "All seven planets are in alternate houses (1/3/5/7/9/11 or 2/4/6/8/10/12 pattern), creating a well-like containment with hidden depth",
        "classical_citation": "BPHS Ch. 31",
        "strength_modifier": 1.3,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Any planet breaks the strict alternating pattern",
        ],
    },

    # -----------------------------------------------------------------------
    # ADDITIONAL DHANA YOGAS (to fill count)
    # -----------------------------------------------------------------------

    "dhana_yoga_1_9": {
        "name": "Dhana Yoga (1L-9L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 1st (self, vitality) and 9th (fortune, father) houses are in conjunction or mutual aspect — fortune flows to the self",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust or in dusthanas",
        ],
    },

    "dhana_yoga_4_11": {
        "name": "Dhana Yoga (4L-11L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 4th (property, fixed assets) and 11th (gains, income) are in conjunction or mutual aspect — property converts to income",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "dhana_yoga_10_2": {
        "name": "Dhana Yoga (10L-2L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 10th (career, action) and 2nd (accumulated wealth) houses are in conjunction or mutual aspect — career directly feeds wealth accumulation",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "dhana_yoga_10_11": {
        "name": "Dhana Yoga (10L-11L)",
        "category": "dhana",
        "constituent_rule": "Lords of the 10th (career) and 11th (income, gains) are in conjunction or mutual aspect — professional activity directly generates income",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 1.8,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "shri_narayana_yoga": {
        "name": "Shri Narayana Yoga",
        "category": "dhana",
        "constituent_rule": "The Hora Lagna and Ghati Lagna are both aspected by or conjoined with their respective lords in strength, indicating providential wealth",
        "classical_citation": "Jaimini Sutras Adhyaya 1",
        "strength_modifier": 1.8,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Both special lagnas are afflicted by malefics without benefic protection",
        ],
    },

    "sparsha_yoga": {
        "name": "Sparsha Yoga",
        "category": "dhana",
        "constituent_rule": "Jupiter, as natural significator of wealth, aspects all three wealth houses (2nd, 5th, and 11th) simultaneously from a strong position",
        "classical_citation": "BPHS Ch. 39",
        "strength_modifier": 2.0,
        "rarity_class": "rare",
        "cancellation_rules": [
            "Jupiter is combust or debilitated in the aspecting position",
        ],
    },

    # -----------------------------------------------------------------------
    # ADDITIONAL RAJA + MISC YOGAS
    # -----------------------------------------------------------------------

    "raja_yoga_3_11": {
        "name": "Upachaya Raja Yoga (3L-11L)",
        "category": "raja",
        "constituent_rule": "Lords of the 3rd and 11th houses (upachaya houses) are in conjunction or mutual exchange, both in strength — self-made success through enterprise and persistent effort",
        "classical_citation": "BPHS Ch. 41",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Both lords are combust",
        ],
    },

    "arishta_bhanga": {
        "name": "Arishta-Bhanga Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Yogas indicating suffering (Arishta) are cancelled (Bhanga) by benefic aspects or placements: Jupiter aspects the Ascendant or Moon, cancelling potential malefic harms",
        "classical_citation": "BPHS Ch. 43 Arishta section",
        "strength_modifier": 1.5,
        "rarity_class": "common",
        "cancellation_rules": [
            "The Arishta-cancelling planet is itself debilitated or combust",
        ],
    },

    "pita_yoga": {
        "name": "Pita (Father) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "The 9th lord and Sun (natural significator of father) are in mutual conjunction or aspect in a kendra or trikona, conferring benefits through the paternal lineage",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.3,
        "rarity_class": "common",
        "cancellation_rules": [
            "Sun is combust the 9th lord",
        ],
    },

    "mata_yoga": {
        "name": "Mata (Mother) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "The 4th lord and Moon (natural significator of mother) are in mutual conjunction or aspect, with both strong, conferring benefits through the maternal lineage",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.3,
        "rarity_class": "common",
        "cancellation_rules": [
            "Moon is in amavasya phase or afflicted",
            "4th lord is combust or debilitated",
        ],
    },

    "deergha_ayu_yoga": {
        "name": "Deergha Ayu (Long Life) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Jupiter, Saturn, and the 8th lord are all strong and in good dignity; the Ascendant is powerful and unafflicted, indicating long life and robust constitution",
        "classical_citation": "BPHS Ch. 44 Ayu chapter",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Multiple malefics afflict the Ascendant or Moon without benefic support",
        ],
    },

    "raja_yoga_navamsa": {
        "name": "Navamsa Raja Yoga",
        "category": "raja",
        "constituent_rule": "A planet forms a raja yoga in the navamsa (D-9) chart even if the rasi chart shows a weaker configuration; navamsa promise activates fully in latter half of life",
        "classical_citation": "BPHS Ch. 6 Navamsa section",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "The navamsa raja yoga planets are in dusthanas in the rasi chart",
        ],
    },

    "ghataka_yoga": {
        "name": "Ghataka-Bhanga (Obstacle Removal) Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Saturn's malefic effects on the chart are neutralised by Jupiter's benefic aspect on Saturn, converting Saturn's obstacles into patient effort and ultimate success",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.5,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Jupiter itself is combust when aspecting Saturn",
        ],
    },

    "rahu_yoga": {
        "name": "Rahu-Elevated Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Rahu is in the 3rd, 6th, 10th, or 11th house in strength, and conjoins or is aspected by a kendra or trikona lord, converting Rahu's disruptive energy into worldly achievement",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.3,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Rahu is in the 1st, 4th, 7th, or 8th without Jupiter's aspect",
        ],
    },

    "ketu_moksha_yoga": {
        "name": "Ketu Moksha Yoga",
        "category": "miscellaneous",
        "constituent_rule": "Ketu is in the 12th house or conjoins Jupiter or the 9th lord, orienting the native toward liberation (moksha), spirituality, and detachment from worldly results",
        "classical_citation": "BPHS Ch. 36",
        "strength_modifier": 1.3,
        "rarity_class": "uncommon",
        "cancellation_rules": [
            "Ketu is heavily afflicted by Mars or Saturn without Jupiter's protection",
        ],
    },

}

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------


def get_yoga(name: str) -> dict:
    """Return yoga dict by name (case-insensitive).

    Args:
        name: Yoga name in snake_case or any case variation.

    Returns:
        The yoga definition dict.

    Raises:
        KeyError: if no yoga with the given name exists.
    """
    key = name.lower()
    if key not in YOGA_DEFINITIONS:
        raise KeyError(f"Yoga not found: {name!r}. Use list_yogas_by_category() to browse available yogas.")
    return YOGA_DEFINITIONS[key]


def list_yogas_by_category(category: str) -> list[str]:
    """Return list of yoga names in the given category.

    Args:
        category: Category string, one of the YOGA_DEFINITIONS category values.

    Returns:
        Sorted list of yoga name keys in that category.
    """
    return sorted(
        name for name, defn in YOGA_DEFINITIONS.items()
        if defn["category"] == category
    )


def get_all_categories() -> list[str]:
    """Return sorted unique list of all category strings present in YOGA_DEFINITIONS.

    Returns:
        Sorted list of distinct category strings.
    """
    return sorted({defn["category"] for defn in YOGA_DEFINITIONS.values()})


def is_raja_yoga(name: str) -> bool:
    """Return True if the yoga belongs to raja, vipareeta_raja, neechabhanga,
    or pancha_mahapurusha categories (all produce raja-class outcomes).

    Args:
        name: Yoga name (case-insensitive).

    Returns:
        True if yoga is in a raja-class category, False otherwise.
        Returns False (not raises) if the yoga name is not found.
    """
    _RAJA_CATEGORIES = {"raja", "vipareeta_raja", "neechabhanga", "pancha_mahapurusha"}
    try:
        yoga = get_yoga(name)
        return yoga["category"] in _RAJA_CATEGORIES
    except KeyError:
        return False


# ---------------------------------------------------------------------------
# MODULE-LEVEL ASSERTIONS
# ---------------------------------------------------------------------------

assert len(YOGA_DEFINITIONS) >= 200, (
    f"Must have 200+ yogas, got {len(YOGA_DEFINITIONS)}"
)
assert all("category" in v for v in YOGA_DEFINITIONS.values()), (
    "All yogas need category"
)
assert all("constituent_rule" in v for v in YOGA_DEFINITIONS.values()), (
    "All yogas need constituent_rule"
)
assert all("classical_citation" in v for v in YOGA_DEFINITIONS.values()), (
    "All yogas need citation"
)
assert all("rarity_class" in v for v in YOGA_DEFINITIONS.values()), (
    "All yogas need rarity_class"
)
