"""
brahmagyan.l0_sutravali_extractor — BRAHMA L0FR Stream D
=========================================================

Sūtravali Pattern Extraction: deterministic Python-regex extraction of Jyotish
rules from classical_text_chunks.

Approach: pure Python regex, ZERO LLM calls. Rules not matching known
templates are SKIPPED per the deterministic-first quality trade-off
(native-ratified 2026-06-07).

Volume target (deterministic): >= 800 rows in sutravali_rules.
Review queue target: >= 100 rows in sutravali_review.

Phase 1: Pattern library — regex extraction
Phase 2: Deterministic quality scoring (SQL + Python checks)
Phase 3: Deterministic deduplication (hash + Levenshtein when available)

Tables written:
  sutravali_rules  — accepted rules (confidence = 1.0 for all regex matches)
  sutravali_review — rejected candidates with rejection_reason

BRAHMA-L0FR-STREAM-D v3.0
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Volume floors ─────────────────────────────────────────────────────────────

RULES_FLOOR = 800
REVIEW_FLOOR = 100

# ── Planet synonym normalization ───────────────────────────────────────────────

PLANET_CANON = {
    "sun": "SUN", "ravi": "SUN", "surya": "SUN", "arka": "SUN",
    "moon": "MON", "chandra": "MON", "soma": "MON", "indu": "MON",
    "mars": "MAR", "mangal": "MAR", "kuja": "MAR", "angaraka": "MAR",
    "mercury": "MER", "budh": "MER", "budha": "MER",
    "jupiter": "JUP", "guru": "JUP", "brihaspati": "JUP",
    "venus": "VEN", "shukra": "VEN", "sukra": "VEN",
    "saturn": "SAT", "shani": "SAT", "sani": "SAT",
    "rahu": "RAH",
    "ketu": "KET",
}

SIGN_CANON = {
    "aries": "ARI", "mesha": "ARI",
    "taurus": "TAU", "vrishabha": "TAU",
    "gemini": "GEM", "mithuna": "GEM",
    "cancer": "CAN", "karka": "CAN", "karkata": "CAN",
    "leo": "LEO", "simha": "LEO",
    "virgo": "VIR", "kanya": "VIR",
    "libra": "LIB", "tula": "LIB",
    "scorpio": "SCO", "vrischika": "SCO", "vrishchika": "SCO",
    "sagittarius": "SAG", "dhanus": "SAG",
    "capricorn": "CAP", "makara": "CAP",
    "aquarius": "AQU", "kumbha": "AQU",
    "pisces": "PIS", "meena": "PIS", "mina": "PIS",
}

HOUSE_ORDINAL_MAP = {
    "first": "1st", "second": "2nd", "third": "3rd", "fourth": "4th",
    "fifth": "5th", "sixth": "6th", "seventh": "7th", "eighth": "8th",
    "ninth": "9th", "tenth": "10th", "eleventh": "11th", "twelfth": "12th",
}


def normalize_planet(raw: str) -> str:
    return PLANET_CANON.get(raw.lower(), raw.upper()[:3])


def normalize_sign(raw: str) -> str:
    return SIGN_CANON.get(raw.lower(), raw.upper()[:3])


def normalize_house(raw: str) -> str:
    return HOUSE_ORDINAL_MAP.get(raw.lower(), raw.lower())


# ── Noun heuristic word list ──────────────────────────────────────────────────

JYOTISH_OUTCOME_NOUNS = {
    "wealth", "riches", "money", "finance", "poverty", "gain", "gains",
    "health", "disease", "illness", "sickness", "longevity", "life",
    "career", "profession", "work", "employment", "occupation",
    "marriage", "spouse", "wife", "husband", "partner",
    "children", "progeny", "son", "daughter", "offspring",
    "father", "mother", "parents", "sibling", "brother", "sister",
    "enemy", "foe", "opponent", "enemies",
    "fame", "reputation", "honor", "renown", "name",
    "luck", "fortune", "success", "failure", "loss",
    "profit", "benefit", "benefits",
    "education", "learning", "knowledge", "wisdom",
    "travel", "journey", "foreign", "abroad",
    "spirituality", "religion", "dharma", "piety",
    "king", "kingdom", "government", "authority",
    "land", "property", "house", "home",
    "happiness", "sorrow", "grief", "joy", "pleasure",
    "death", "destruction", "trouble", "danger", "suffering",
    "character", "nature", "disposition", "temperament",
    "power", "strength", "weakness", "affliction",
    "intellect", "intelligence", "mind", "speech",
    "body", "limb", "eye", "vision",
    "native", "person", "individual", "born",
    "results", "effects", "outcome", "consequence",
    "period", "dasa", "antardasa", "bhukti", "transit",
    "aspect", "conjunction", "opposition",
    "exaltation", "debilitation",
    "malefic", "benefic", "neutral",
    "bhava", "rashi", "navamsa", "lagna", "ascendant",
    "yoga", "raja", "dhana",
    "graha", "planet", "sun", "moon", "mars", "mercury",
    "jupiter", "venus", "saturn", "rahu", "ketu",
    "longlived", "wealthy", "intelligent", "valiant", "brave",
    "wise", "rich", "poor", "prosperous", "unfortunate", "fortunate",
    "auspicious", "inauspicious", "good", "bad", "evil",
    "war", "victory", "defeat", "honor", "disgrace",
    "children", "wife", "lord", "king", "servant",
    "function", "deeds", "actions",
    "long", "short", "middle", "mean",
    "kendra", "trine", "trikona", "dusthana", "upachaya",
    "child", "age", "year", "years",
    "die", "dead", "mortal", "survive",
    "confer", "bestow", "endow", "grant",
    "happiness", "sorrow", "affliction",
    "misery", "comfort", "luxury",
    "pious", "sinful", "virtuous",
    "warrior", "soldier", "brave",
    "ascetic", "monk", "renunciate",
    "liberated", "bondage", "moksha",
    "friends", "foes", "relatives",
    # Outcome adjectives (Jataka Parijata style outcomes)
    "long-lived", "shortlived", "wealthy", "prosperous", "intelligent",
    "famous", "renowned", "fortunate", "unfortunate", "happy",
    "miserable", "virtuous", "wicked", "brave", "cowardly",
    "liberal", "generous", "miser", "stingy",
    "beautiful", "ugly", "learned", "illiterate",
    "healthy", "sickly", "strong", "weak",
    "cruel", "gentle", "passionate", "detached",
    "royal", "servile", "noble", "base",
    # Jyotish outcomes from actual text (supplemental)
    "valorous", "valour", "valor", "courageous", "heroic",
    "eloquent", "truthful", "charitable", "charitable",
    "libidinous", "lascivious", "carnal", "sensual", "amorous",
    "afflicted", "bereft", "devoid", "endowed",
    "rajayoga", "yoga", "combinations",
    "two", "three", "four", "many", "few", "several",
    "wives", "sons", "daughters",
    "finances", "financial", "expenditure", "expenses",
    "stomach", "stomachial", "disorders", "fire",
    "wandering", "garrulous", "iritable", "spiteful",
    "serving", "skilful", "skilled", "adept",
    "trading", "trade", "wood", "stones", "poison",
    "inimical", "co-born", "uncle", "aunt", "maternal",
    "author", "writer", "poet",
    "bliss", "felicity", "enjoyment", "pleasures", "comforts",
    "charitable", "chaste", "devoted", "pious", "righteous",
    "detached", "dejected", "troubled",
    "learned", "scholar", "scholarly",
    "honours", "honoured", "honourable",
    "conveyances", "vehicles", "horses", "elephants",
    "minister", "officer", "official", "army", "chief",
    "patron", "patronage", "king",
    "bold", "timid", "fearless",
    "generous", "miserly", "extravagant",
    "handsome", "beautiful", "attractive",
    "skinny", "fat", "tall", "short",
    "popular", "famous", "renowned",
    "sinful", "wicked", "dishonest", "thievish",
    "jealous", "angry", "wrathful",
    "clever", "dull", "sharp",
    "gains", "financial", "monetary",
    "brothers", "friends", "companions",
    "servants", "slaves",
    "enemies", "foes", "opponents",
}

# ── Regex building blocks ─────────────────────────────────────────────────────

# All planet names (with OCR variants)
PLANET_LIST = (
    "Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|"
    "Ravi|Surya|Chandra|Soma|Mangal|Kuja|Budh|Budha|"
    "Guru|Brihaspati|Shukra|Sukra|Shani|Sani"
)

PLANET_PAT = rf"(?P<planet>{PLANET_LIST})"
PLANET_ANY = rf"(?:{PLANET_LIST})"

HOUSE_NUMS = (
    "1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th|"
    "first|second|third|fourth|fifth|sixth|seventh|eighth|"
    "ninth|tenth|eleventh|twelfth"
)
HOUSE_PAT = rf"(?P<house>{HOUSE_NUMS})"
HOUSE_ANY = rf"(?:{HOUSE_NUMS})"

SIGN_LIST = (
    "Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|"
    "Sagittarius|Capricorn|Aquarius|Pisces|"
    "Mesha|Vrishabha|Mithuna|Karka|Karkata|Simha|Kanya|"
    "Tula|Vrischika|Vrishchika|Dhanus|Makara|Kumbha|Meena|Mina"
)
SIGN_PAT = rf"(?P<sign>{SIGN_LIST})"
SIGN_ANY = rf"(?:{SIGN_LIST})"

# Outcome verb
VERB_PAT = (
    r"(?P<verb>"
    r"gives?|cause[sd]?|leads?\s+to|brings?|results?\s+in|"
    r"produces?|makes?|denotes?|indicates?|signifies?|"
    r"confers?|bestows?|renders?|endows?"
    r")"
)

# Outcomes: short + bounded
OUTCOME_PAT = r"(?P<outcome>[^.;!?\n]{5,250})"

# Location phrases (where a planet can be)
LOC_HOUSE = rf"(?:the\s+)?(?P<house>{HOUSE_NUMS})\s+(?:bhava|house|from\s+the\s+ascendant|from\s+lagna)?"
LOC_SIGN = rf"(?P<sign>{SIGN_LIST})"

# ── Sutra patterns — comprehensive coverage ──────────────────────────────────
# Designed to match the actual BPHS, Jataka Parijata, Phaladeepika text structure.
# Key findings from text analysis:
# - BPHS: heavy use of "If X be in the Nth, the native will be..." and dasa bullet lists
# - Jataka Parijata: "When [multi-condition], the person born will [outcome]"
# - Most rules are multi-sentence with complex antecedents
# - v3.0: Added many broader capture patterns, especially for JP "person born" style

SUTRA_PATTERNS: list[tuple[str, str]] = [

    # ══════════════════════════════════════════════════════════════════════
    # GROUP A: Direct "planet in house gives outcome" patterns
    # ══════════════════════════════════════════════════════════════════════

    # A01: "Saturn in the 7th house gives X"
    (
        "A01_planet_in_house_gives",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # A02: "Saturn in the 7th house, [the native...] outcome"
    (
        "A02_planet_in_house_comma",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # A03: "Saturn in Aries gives X"
    (
        "A03_planet_in_sign_gives",
        rf"{PLANET_PAT}\s+in\s+{SIGN_PAT}\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # A04: "Saturn in Aries, [the native...] X"
    (
        "A04_planet_in_sign_comma",
        rf"{PLANET_PAT}\s+in\s+{SIGN_PAT}[,;]\s+(?:the\s+)?(?:native\s+)?{OUTCOME_PAT}",
    ),
    # A05: "Saturn placed/posited/situated in the 7th gives X"
    (
        "A05_planet_placed_in_house",
        rf"{PLANET_PAT}\s+(?:placed|posited|situated|posted|occupying|found)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # A06: "Saturn placed/posited in Aries gives X"
    (
        "A06_planet_placed_in_sign",
        rf"{PLANET_PAT}\s+(?:placed|posited|situated|posted|occupying|found)\s+in\s+{SIGN_PAT}\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # A07: "Saturn is in the 7th (house) — outcome" (dash separator)
    (
        "A07_planet_in_house_dash",
        rf"{PLANET_PAT}\s+is\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[—\-]{{1,2}}\s+{OUTCOME_PAT}",
    ),
    # A08: "Saturn occupies the 7th house — outcome"
    (
        "A08_planet_occupies_house",
        rf"{PLANET_PAT}\s+occupies?\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house|place|position)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # A09: "Saturn occupies the 7th — gives/brings"
    (
        "A09_planet_occupies_house_dash",
        rf"{PLANET_PAT}\s+occupies?\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house|place|position)?\s*[,;—\-]\s+{OUTCOME_PAT}",
    ),
    # A10: "Saturn in the 7th — X" (simple dash outcome, no verb needed)
    (
        "A10_planet_house_dash_outcome",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[—\-]+\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP B: Conditional "If/When planet is in house, outcome"
    # ══════════════════════════════════════════════════════════════════════

    # B01: "If Saturn is/be in the 7th house, X" (includes "If the Moon is in...")
    (
        "B01_if_planet_in_house",
        rf"[Ii]f\s+(?:the\s+)?{PLANET_PAT}\s+(?:is|be|be\s+in|is\s+in)\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # B02: "If Saturn be/is in Aries, X"
    (
        "B02_if_planet_in_sign",
        rf"[Ii]f\s+(?:the\s+)?{PLANET_PAT}\s+(?:is|be|be\s+in|is\s+in)\s+{SIGN_PAT}[,;]\s+{OUTCOME_PAT}",
    ),
    # B03: "When Saturn is in the 7th house, X"
    (
        "B03_when_planet_in_house",
        rf"[Ww]hen\s+(?:the\s+)?{PLANET_PAT}\s+(?:is\s+|goes\s+to\s+|be\s+)?(?:in|to)\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # B04: "When Saturn is in Aries, X" (includes "When the Moon is in Libra, ...")
    (
        "B04_when_planet_in_sign",
        rf"[Ww]hen\s+(?:the\s+)?{PLANET_PAT}\s+(?:is\s+|goes\s+|be\s+)?(?:in|to)\s+{SIGN_PAT}[,;]\s+{OUTCOME_PAT}",
    ),
    # B05: Inverted: "X will result, if Saturn be in the 7th"
    (
        "B05_outcome_if_planet_house",
        rf"(?P<outcome>[A-Z][a-zA-Z\s,().%&]{{10,200}}),\s+if\s+{PLANET_PAT}\s+be\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?",
    ),
    # B06: Inverted: "X will result, if Saturn be in Aries"
    (
        "B06_outcome_if_planet_sign",
        rf"(?P<outcome>[A-Z][a-zA-Z\s,().%&]{{10,200}}),\s+if\s+{PLANET_PAT}\s+be\s+in\s+{SIGN_PAT}",
    ),
    # B07: Inverted: "X, if Saturn is in the 7th"
    (
        "B07_outcome_if_planet_is_house",
        rf"(?P<outcome>[A-Z][a-zA-Z\s,().%&]{{10,200}}),\s+if\s+{PLANET_PAT}\s+is\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?",
    ),
    # B08: "If Saturn be in the 7th and/or [condition], X will result"
    (
        "B08_if_planet_house_condition",
        rf"[Ii]f\s+{PLANET_PAT}\s+be\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+(?:and\s+[^,;.]{{0,60}})?[,;]\s+{OUTCOME_PAT}",
    ),
    # B09: "If Saturn occupies the 7th house, X"
    (
        "B09_if_planet_occupies_house",
        rf"[Ii]f\s+{PLANET_PAT}\s+occupies?\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # B10: "When Saturn occupies the 7th house, X"
    (
        "B10_when_planet_occupies_house",
        rf"[Ww]hen\s+{PLANET_PAT}\s+occupies?\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP C: "native will be/have" predictions
    # ══════════════════════════════════════════════════════════════════════

    # C01: "If Saturn is in the 7th, the native will be X"
    (
        "C01_if_planet_house_native_will",
        rf"[Ii]f\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+(?:be\s+)?(?P<outcome>[^.;!?\n]{{5,200}})",
    ),
    # C02: "Saturn in the 7th, the native will be X"
    (
        "C02_planet_house_native_will",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+(?:be\s+)?(?P<outcome>[^.;!?\n]{{5,200}})",
    ),
    # C03: "the native will be X" — preceded within same sentence by planet/house
    (
        "C03_sentence_native_will_planet",
        rf"(?:(?:the\s+)?native|person\s+born)\s+will\s+be\s+(?P<outcome>[a-zA-Z][^.;!?\n]{{5,200}})\s+if\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?",
    ),
    # C04: "[planet] in [house/sign], the native will have X"
    (
        "C04_planet_house_native_have",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?(?:{HOUSE_ANY}|{SIGN_ANY})\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+have\s+(?P<outcome>[^.;!?\n]{{5,200}})",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP D: Lord-of-house patterns
    # ══════════════════════════════════════════════════════════════════════

    # D01: "lord of the 10th is in the 7th — X"
    (
        "D01_lord_in_house_gives",
        rf"[Ll]ord\s+of\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s+(?:is\s+|be\s+)?in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # D02: "If the lord of the 10th is in the 8th, the native will X"
    (
        "D02_if_lord_in_house_native",
        rf"[Ii]f\s+(?:the\s+)?[Ll]ord\s+of\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s+(?:is|be)\s+(?:relegated\s+to\s+|in\s+)(?:the\s+)?{HOUSE_PAT}\s*(?:[^,;.!?\n]{{0,50}})?[,;]\s+(?:the\s+)?native\s+will\s+(?P<outcome>[^.;!?\n]{{5,200}})",
    ),
    # D03: "If the lord of the 2nd is in the 11th, wealth will be acquired"
    (
        "D03_if_lord_in_house_outcome",
        rf"[Ii]f\s+(?:the\s+)?[Ll]ord\s+of\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:[^,;.!?\n]{{0,50}})?[,;]\s+{OUTCOME_PAT}",
    ),
    # D04: "the Nth lord in the Mth house gives X"
    (
        "D04_house_lord_in_house_gives",
        rf"(?:the\s+)?{HOUSE_PAT}\s+[Ll]ord\s+in\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP E: Sign-ascendant descriptions
    # ══════════════════════════════════════════════════════════════════════

    # E01: "Aries Ascendant — The natives are X"
    (
        "E01_sign_ascendant_description",
        rf"{SIGN_PAT}\s+[Aa]scendant\s*[—\-:]\s+(?:[Tt]he\s+)?(?:natives?|persons?)\s+(?:of\s+this\s+[Aa]scendant\s+)?(?:are\s+|is\s+|will\s+be\s+)?(?P<outcome>[^.;!?\n]{{10,300}})",
    ),
    # E02: "For Aries Lagna, X"
    (
        "E02_for_sign_lagna",
        rf"[Ff]or\s+{SIGN_PAT}\s+(?:Lagna|Ascendant|ascendant|lagna)\s*[,;]\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP F: Yoga / combination patterns
    # ══════════════════════════════════════════════════════════════════════

    # F01: "X Yoga: One born in X yoga will be Y"
    (
        "F01_yoga_native",
        rf"[A-Z][A-Z\s]{{2,25}}\s+[Yy]oga\s*[;:—\-]\s+[Oo]ne\s+born\s+in\s+(?:this\s+)?(?:yoga\s+)?will\s+be\s+(?P<outcome>[^.;!?\n]{{5,200}})",
    ),
    # F02: "Saturn aspects the Xth house — outcome"
    (
        "F02_planet_aspects_house",
        rf"{PLANET_PAT}\s+aspects?\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # F03: "Saturn conjunct Jupiter gives Y"
    (
        "F03_planet_conjunct_planet_gives",
        rf"{PLANET_PAT}\s+(?:conjunct(?:ion)?|conjoined|joined|associated)\s+(?:with\s+)?(?P<planet2>{PLANET_LIST})\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # F04: "Saturn aspected by Jupiter gives X"
    (
        "F04_planet_aspected_by_gives",
        rf"{PLANET_PAT}\s+aspected\s+by\s+(?P<planet2>{PLANET_LIST})\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP G: Dasa/Antardasa patterns (BPHS chapter-specific)
    # ══════════════════════════════════════════════════════════════════════

    # G01: "Saturn (Capricorn or Aquarius) — Loss of wealth, mental agony"
    (
        "G01_planet_sign_dasa_bullet",
        rf"{PLANET_PAT}\s+\((?:{SIGN_ANY})(?:\s+or\s+(?:{SIGN_ANY}))?\)\s*[—\-]{{1,2}}\s+(?P<outcome>[^.!?\n(]{{10,250}})",
    ),
    # G02: "Antardasa of Saturn in the Dasa of Jupiter — X"
    (
        "G02_antardasa_in_dasa",
        rf"[Aa]ntardasa\s+of\s+{PLANET_PAT}\s+in\s+(?:the\s+)?[Dd]asa\s+of\s+(?P<planet2>{PLANET_LIST})\s*[,;—\-:]\s+{OUTCOME_PAT}",
    ),
    # G03: "In the Dasa of Saturn, X"
    (
        "G03_in_dasa_of_planet",
        rf"[Ii]n\s+the\s+[Dd]asa\s+of\s+{PLANET_PAT}\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # G04: "Effects of Saturn Dasa: X"
    (
        "G04_effects_of_planet_dasa",
        rf"[Ee]ffects\s+of\s+(?:the\s+)?[Dd]asa\s+of\s+{PLANET_PAT}\s*[,:—\-]\s+{OUTCOME_PAT}",
    ),
    # G05: "Saturn Dasa gives X"
    (
        "G05_planet_dasa_gives",
        rf"{PLANET_PAT}\s+[Dd]asa\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # G06: "Moon's dasa will cause/lead to X" (Hora Sara style)
    (
        "G06_planets_dasa_will_cause",
        rf"(?:the\s+)?{PLANET_PAT}['s]*\s+dasa\s+will\s+(?:cause|lead\s+to|bring|result\s+in|make)\s+{OUTCOME_PAT}",
    ),
    # G07: "In Saturn's dasa, when she/he is in Sign, the native X" (Hora Sara)
    (
        "G07_in_planets_dasa_when_in_sign",
        rf"[Ii]n\s+(?:the\s+)?{PLANET_PAT}['s]*\s+dasa\s*,\s+when\s+(?:she|he|it)\s+is\s+in\s+{SIGN_PAT}\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # G08: "The Moon's dasa, when she is in Virgo, X" (variant)
    (
        "G08_planets_dasa_when_in_sign_alt",
        rf"(?:[Tt]he\s+)?{PLANET_PAT}['s]+\s+dasa\s*,\s+when\s+(?:she|he|it)\s+is\s+in\s+{SIGN_PAT}\s*[,;]\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP H: "person born" patterns (dominant in Jataka Parijata)
    # ══════════════════════════════════════════════════════════════════════

    # H01: "When [condition with planet], the person born will [outcome]"
    # The condition must contain a planet reference
    (
        "H01_person_born_will_planet",
        rf"[Ww]hen\s+(?=[^.!?]{{0,200}}{PLANET_ANY})([^.!?]{{10,200}})[,;]\s+(?:the\s+)?person\s+born\s+will\s+(?P<outcome>[^.!?]{{5,200}})",
    ),
    # H02: "the person born becomes/will be [outcome]" — short pattern for bullets
    (
        "H02_person_born_becomes",
        rf"(?:[Tt]he\s+)?person\s+born\s+(?:will\s+(?:be|have|become)|becomes?|is\s+declared\s+to\s+(?:possess|have|be))\s+(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # H03: "When [planet] in [position], the person born will/is X"
    (
        "H03_when_planet_pos_person",
        rf"[Ww]hen\s+{PLANET_PAT}\s+(?:is\s+|be\s+|goes\s+to\s+)?(?:in|to)\s+(?:the\s+)?(?:{HOUSE_ANY}|{SIGN_ANY})\s*(?:bhava|house)?\s*[^.!?]{{0,100}}[,;]\s+(?:the\s+)?person\s+born\s+(?:will\s+(?:be|have)|becomes?|is)\s+(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # H04: "the person born must be declared to possess X" (JP specific)
    (
        "H04_person_born_declared",
        rf"(?:[Tt]he\s+)?person\s+born\s+(?:must\s+be\s+declared|is\s+to\s+be\s+declared|is\s+declared)\s+(?:to\s+(?:be|possess|have)\s+)?(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # H05: "the person born in [sign/house] will be X"
    (
        "H05_person_born_in_sign",
        rf"(?:[Tt]he\s+)?person\s+born\s+(?:in|with|under)\s+(?:{SIGN_ANY}|{HOUSE_ANY})\s+will\s+(?:be\s+)?(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # H06: Broad JP pattern - "person born will die/live/have X"
    (
        "H06_person_born_will_verb",
        rf"(?:[Tt]he\s+)?person\s+born\s+will\s+(?:die|live|have|get|attain|obtain|enjoy|suffer|experience|possess|be|become)\s+(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # H07: "one born in [sign/position] will be X"
    (
        "H07_one_born_in",
        rf"[Oo]ne\s+born\s+(?:in|with|under)\s+(?:{SIGN_ANY}|{HOUSE_ANY}|(?:this\s+)?(?:yoga|combination|configuration))\s+will\s+(?:be\s+)?(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP I: Positional + "will result" patterns
    # ══════════════════════════════════════════════════════════════════════

    # I01: "if Saturn be in kendra/trikona, X"
    (
        "I01_if_planet_in_positional",
        rf"[Ii]f\s+{PLANET_PAT}\s+be\s+in\s+(?:the\s+)?(?P<position>kendra|trikona|trine|angle|upachaya|dusthana|ascendant|lagna)\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # I02: "One will be X if Saturn is in the Nth"
    (
        "I02_one_will_if_planet_house",
        rf"[Oo]ne\s+will\s+(?:be\s+)?(?P<outcome>[^,;.!?\n]{{5,100}})\s+if\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?",
    ),
    # I03: "will be acquired/result if Saturn is in the 7th"
    (
        "I03_will_result_if_planet_house",
        rf"will\s+(?:be\s+)?(?P<outcome>[a-zA-Z][a-zA-Z\s,()-]{{5,100}})\s+if\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?",
    ),
    # I04: "If Pranapada/Vyatipata/Mandi is in the Nth, the native will be X"
    # Covers sub-planet and special point placements (not just graha)
    (
        "I04_if_special_point_in_house",
        rf"[Ii]f\s+(?P<planet>Pranapada|Vyatipata|Mandi|Gulika|Pars\s+Fortunae|Arudha|Upapada|Dhumra|Artha|Kala|Mrityu|Trisphuta|Shatabhisha|Atmakaraka|Amatyakaraka|Darakaraka|Putrakaraka)\s+(?:is\s+)?in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+(?:be\s+|have\s+)?(?P<outcome>[^.;!?\n]{{5,200}})",
    ),
    # I05: "if [planet] be in [house], [outcome] will result/follow"
    (
        "I05_if_planet_house_result",
        rf"[Ii]f\s+{PLANET_PAT}\s+be\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}\s+will\s+(?:result|follow|come\s+to\s+pass|be\s+the\s+result)",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP J: Exaltation/debilitation rules
    # ══════════════════════════════════════════════════════════════════════

    # J01: "Saturn in exaltation gives X"
    (
        "J01_planet_in_exaltation",
        rf"{PLANET_PAT}\s+in\s+(?:his\s+)?(?:sign\s+of\s+)?(?P<state>exaltation|debilitation|own\s+sign|own\s+house|moolatrikona)\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # J02: "If Saturn be in his sign of exaltation, X"
    (
        "J02_if_planet_exaltation",
        rf"[Ii]f\s+{PLANET_PAT}\s+be\s+in\s+(?:his\s+)?(?:sign\s+of\s+)?(?P<state>exaltation|debilitation|own\s+sign|own\s+house|moolatrikona)\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # J03: "When Saturn is exalted, X"
    (
        "J03_when_planet_exalted",
        rf"[Ww]hen\s+{PLANET_PAT}\s+is\s+(?:exalted|debilitated|in\s+own\s+sign|in\s+its\s+own\s+sign)\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # J04: "Saturn exalted gives X"
    (
        "J04_planet_exalted_gives",
        rf"{PLANET_PAT}\s+(?:exalted|debilitated|in\s+own\s+sign|in\s+its\s+own\s+sign)\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP K: "native will be" sentences (complex BPHS patterns)
    # Extract based on sentence structure: "If [condition with planet], the native will be X"
    # Uses lookahead to verify planet presence in the condition part
    # ══════════════════════════════════════════════════════════════════════

    # K01: "If [anything containing planet], the native will be X"
    (
        "K01_if_anything_native_will",
        rf"[Ii]f\s+(?=[^.!?]{{0,200}}{PLANET_ANY})(?P<condition>[^.!?]{{5,200}}),\s+(?:the\s+)?native\s+will\s+be\s+(?P<outcome>[a-zA-Z][a-zA-Z\s,()-]{{5,200}})",
    ),
    # K02: "If [anything with planet], the native will have X"
    (
        "K02_if_anything_native_will_have",
        rf"[Ii]f\s+(?=[^.!?]{{0,200}}{PLANET_ANY})(?P<condition>[^.!?]{{5,200}}),\s+(?:the\s+)?native\s+will\s+have\s+(?P<outcome>[a-zA-Z][a-zA-Z\s,()-]{{5,200}})",
    ),
    # K03: "When [anything with planet], the native will be X"
    (
        "K03_when_anything_native_will",
        rf"[Ww]hen\s+(?=[^.!?]{{0,200}}{PLANET_ANY})(?P<condition>[^.!?]{{5,200}})[,;]\s+(?:the\s+)?native\s+will\s+be\s+(?P<outcome>[a-zA-Z][a-zA-Z\s,()-]{{5,200}})",
    ),
    # K04: "[planet] in [house/sign], the native will be X" — without if/when
    (
        "K04_planet_native_will_direct",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?(?:{HOUSE_ANY}|{SIGN_ANY})\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+be\s+(?P<outcome>[a-zA-Z][a-zA-Z\s,()-]{{5,200}})",
    ),
    # K05: "When [condition with planet], the person born will be X" — JP style
    (
        "K05_when_anything_person_born_will",
        rf"[Ww]hen\s+(?=[^.!?]{{0,200}}{PLANET_ANY})(?P<condition>[^.!?]{{10,250}})[,;]\s+(?:the\s+)?person\s+born\s+will\s+be\s+(?P<outcome>[a-zA-Z][a-zA-Z\s,()-]{{5,200}})",
    ),
    # K06: "When [condition], the person born must be declared to possess X"
    (
        "K06_when_condition_person_declared",
        rf"[Ww]hen\s+(?=[^.!?]{{0,200}}{PLANET_ANY})(?P<condition>[^.!?]{{10,250}})[,;]\s+(?:the\s+)?(?:person\s+born|native)\s+(?:must\s+be\s+declared|is\s+declared|is\s+to\s+be)\s+(?:to\s+(?:be|possess|have)\s+)?(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # K07: "If [condition with planet], the person born will X"
    (
        "K07_if_condition_person_will",
        rf"[Ii]f\s+(?=[^.!?]{{0,200}}{PLANET_ANY})(?P<condition>[^.!?]{{5,200}}),\s+(?:the\s+)?person\s+born\s+will\s+(?:be\s+)?(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP L: Broader outcome patterns — "X will be [outcome]"
    # ══════════════════════════════════════════════════════════════════════

    # L01: "X will be acquired by the native" style — inverted
    (
        "L01_outcome_acquired_native",
        rf"(?P<outcome>[A-Z][a-zA-Z\s,]+)\s+will\s+be\s+(?:acquired|obtained|gained|conferred|bestowed)\s+(?:by\s+the\s+native\s+)?if\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?",
    ),
    # L02: "Wealth will be acquired if Saturn is in 11th"
    (
        "L02_wealth_acquired_if",
        rf"(?P<outcome>[A-Z][a-zA-Z\s,]{{5,100}})\s+will\s+(?:result|follow|come)\s+if\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}",
    ),
    # L03: "One will be X if [planet] be in [house]"
    (
        "L03_one_will_be_if",
        rf"[Oo]ne\s+will\s+be\s+(?P<outcome>[a-zA-Z][a-zA-Z\s,()-]{{5,100}})\s+if\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?(?:{HOUSE_ANY}|{SIGN_ANY})",
    ),
    # L04: "will enjoy X if Saturn is in the 7th"
    (
        "L04_will_enjoy_if",
        rf"will\s+(?:enjoy|attain|obtain|get|gain|experience|suffer|have)\s+(?P<outcome>[a-zA-Z][^,;.!?\n]{{5,100}})\s+if\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP M: Uttara Kalamrita / special text patterns
    # ══════════════════════════════════════════════════════════════════════

    # M01: "If [planet] is strong in [house], X" (UK style)
    (
        "M01_if_planet_strong_in_house",
        rf"[Ii]f\s+{PLANET_PAT}\s+is\s+(?:strong|powerful|exalted|well-placed|well\s+placed)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # M02: "Saturn in the Nth produces X" (UK style)
    (
        "M02_planet_in_house_produces",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+(?:produces?|causes?|creates?|brings?\s+about)\s+{OUTCOME_PAT}",
    ),
    # M03: "The lord of Nth in Mth gives X"
    (
        "M03_lord_of_nth_in_mth",
        rf"[Tt]he\s+[Ll]ord\s+of\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # M04: "The Nth house lord in the Mth — X"
    (
        "M04_nth_lord_in_mth_dash",
        rf"(?:[Tt]he\s+)?{HOUSE_PAT}\s+(?:house\s+)?[Ll]ord\s+in\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s*[—\-:]\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP N: "the native will" without explicit if/when (direct statements)
    # ══════════════════════════════════════════════════════════════════════

    # N01: "Saturn in the 7th house. The native will be X" (next sentence)
    (
        "N01_planet_house_period_native",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\.\s+(?:[Tt]he\s+)?native\s+will\s+(?:be\s+)?(?P<outcome>[^.;!?\n]{{5,200}})",
    ),
    # N02: "Saturn in the Nth. [The person born] will be X"
    (
        "N02_planet_house_period_person",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\.\s+(?:[Tt]he\s+)?person\s+born\s+will\s+(?:be\s+)?(?P<outcome>[^.;!?\n]{{5,200}})",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP P: BPHS specific — "Saturn in the 4th house will deprive one of X"
    # ══════════════════════════════════════════════════════════════════════

    # P01: "Saturn in the Nth house will X"
    (
        "P01_planet_in_house_will",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+will\s+(?P<outcome>[^.;!?\n]{{5,200}})",
    ),
    # P02: "Saturn in the Nth will give/bring/confer X"
    (
        "P02_planet_in_house_will_verb",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+will\s+{VERB_PAT}\s+(?P<outcome>[^.;!?\n]{{5,200}})",
    ),
    # P03: "A planet in the Nth gives X"
    (
        "P03_a_planet_in_house_gives",
        rf"[Aa]\s+(?P<planet>benefic|malefic|planet|graha)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # P04: "Having Saturn in the 7th, the native will X"
    (
        "P04_having_planet_in_house",
        rf"[Hh]aving\s+{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+(?:be\s+)?(?P<outcome>[^.;!?\n]{{5,200}})",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP Q: JP life-span patterns (heavily "will die in Nth year")
    # ══════════════════════════════════════════════════════════════════════

    # Q01: "the person born will die in his Nth year"
    (
        "Q01_person_die_in_year",
        rf"(?:[Tt]he\s+)?person\s+born\s+will\s+(?:die|pay\s+the\s+debt\s+of\s+nature)\s+in\s+(?:his\s+)?(?P<outcome>\d+[a-z]*\s+year[^.!?]{{0,100}})",
    ),
    # Q02: "the child will not live beyond Nth year"
    (
        "Q02_child_not_live",
        rf"(?:[Tt]he\s+)?child\s+will\s+(?:not\s+live|die|expire|perish)\s+(?:beyond|before|in|after)\s+(?P<outcome>[^.!?]{{5,100}})",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP R: Yoga-name based patterns (JP: "person born in X yoga is Y")
    # These don't require planet/house reference - yoga name IS the antecedent
    # ══════════════════════════════════════════════════════════════════════

    # R01: "A person born under the X yoga has/is Y"
    (
        "R01_person_born_under_yoga",
        rf"[Aa]\s+person\s+born\s+under\s+(?:the\s+)?(?P<planet>[A-Z][a-zA-Z\s]+?)\s+yoga\s+(?:has|is|will\s+be|will\s+have|becomes?)\s+(?P<outcome>[a-zA-Z][^.!?]{{5,250}})",
    ),
    # R02: "The person born in the X yoga is Y"
    (
        "R02_person_born_in_yoga",
        rf"(?:[Tt]he\s+)?person\s+born\s+in\s+(?:the\s+)?(?P<planet>[A-Z][a-zA-Z\s()]+?)\s+(?:yoga|Yoga)\s+(?:is|has|will\s+be|may\s+be|becomes?)\s+(?P<outcome>[a-zA-Z][^.!?]{{5,250}})",
    ),
    # R03: "One born in X yoga will be Y"
    (
        "R03_one_born_in_yoga",
        rf"[Oo]ne\s+born\s+in\s+(?:the\s+)?(?P<planet>[A-Z][a-zA-Z\s()]+?)\s+(?:yoga|Yoga)\s+will\s+(?:be\s+|have\s+)?(?P<outcome>[a-zA-Z][^.!?]{{5,250}})",
    ),
    # R04: "person born in X yoga may be/is a king/minister/etc"
    (
        "R04_person_in_yoga_is",
        rf"(?:[Tt]he\s+)?person\s+born\s+in\s+(?:the\s+)?(?P<planet>[A-Z]\w+\s+(?:yoga|Yoga))\s+(?P<outcome>[a-zA-Z][^.!?]{{5,250}})",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP S: "astrologer declares" patterns (JP specific)
    # ══════════════════════════════════════════════════════════════════════

    # S01: "the astrologer is to declare the person born to be X"
    (
        "S01_astrologer_declare",
        rf"(?:astrologer|sage)\s+(?:is\s+to\s+declare|declares?|should\s+declare|must\s+declare)\s+(?:the\s+)?(?:person\s+born|native)\s+(?:to\s+be\s+|to\s+possess\s+|to\s+have\s+)?(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # S02: "one must be declared to possess X"
    (
        "S02_must_be_declared",
        rf"(?:one|native|person\s+born)\s+must\s+be\s+declared\s+(?:to\s+(?:be|possess|have)\s+)?(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP T: BPHS "one will be endowed with X if Y" patterns
    # ══════════════════════════════════════════════════════════════════════

    # T01: "One will be endowed with X if Saturn is in the 7th"
    (
        "T01_one_endowed_with",
        rf"[Oo]ne\s+will\s+be\s+endowed\s+with\s+(?P<outcome>[a-zA-Z][^.!?]{{5,100}})\s+if\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?(?:{HOUSE_ANY}|{SIGN_ANY})",
    ),
    # T02: "Fame/wealth/X will be acquired if Y" (inverted BPHS patterns)
    (
        "T02_fame_acquired_if_planet",
        rf"(?P<outcome>[A-Z][a-zA-Z,\s]+)\s+will\s+be\s+(?:acquired|obtained|gained|enjoyed|conferred)\s+(?:by\s+the\s+native\s+)?if\s+{PLANET_PAT}\s+(?:is|be)\s+in\s+(?:the\s+)?(?:{HOUSE_ANY}|{SIGN_ANY})",
    ),
    # T03: "Effects of Saturn in Aries: X" — header format
    (
        "T03_effects_of_planet_in_sign",
        rf"[Ee]ffects?\s+of\s+{PLANET_PAT}\s+in\s+{SIGN_PAT}\s*[;:—\-]\s+{OUTCOME_PAT}",
    ),
    # T04: "Effects of Saturn in the Nth house: X" — header format
    (
        "T04_effects_of_planet_in_house",
        rf"[Ee]ffects?\s+of\s+{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[;:—\-]\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP U: Simple declarative rules (no conditional structure needed)
    # ══════════════════════════════════════════════════════════════════════

    # U01: "Saturn in the ascendant makes one X" (simple declarative)
    (
        "U01_planet_in_lagna_makes",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?(?:ascendant|lagna)\s+(?:makes?|renders?|confers?|gives?)\s+(?:the\s+native\s+|one\s+)?(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # U02: "Saturn aspecting the Xth house gives X"
    (
        "U02_planet_aspecting_house",
        rf"{PLANET_PAT}\s+aspecting\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # U03: "Saturn in the 7th or 8th gives X" (compound house)
    (
        "U03_planet_in_compound_house",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s+or\s+(?:the\s+)?(?P<house2>{HOUSE_NUMS})\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # U04: "Saturn, lord of X, in the Nth house gives Y"
    (
        "U04_planet_lord_of_in_house",
        rf"{PLANET_PAT}(?:,\s+lord\s+of\s+[^,]+,)?\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # U05: "When Jupiter and Venus are in X, Y"
    (
        "U05_two_planets_in_house",
        rf"[Ww]hen\s+{PLANET_PAT}\s+and\s+(?P<planet2>{PLANET_LIST})\s+(?:are\s+)?in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP V: Uttara Kalamrita style
    # ══════════════════════════════════════════════════════════════════════

    # V01: "In [sign] Lagna, Saturn gives X"
    (
        "V01_in_sign_lagna_planet_gives",
        rf"[Ii]n\s+{SIGN_PAT}\s+(?:[Ll]agna|[Aa]scendant)\s*[,;]\s+{PLANET_PAT}\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # V02: "The native having [planet] in [house] will X"
    (
        "V02_native_having_planet_house",
        rf"(?:[Tt]he\s+)?native\s+having\s+{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+will\s+(?:be\s+)?(?P<outcome>[^.;!?\n]{{5,200}})",
    ),
    # V03: "[Planet] in [house], [Native/Person] [verb phrase]"
    (
        "V03_planet_house_then_effect",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*;\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP W: Broad antecedent patterns with explicit outcomes
    # Capture any sentence with "[planet] in [house/sign]" followed by clear outcome
    # ══════════════════════════════════════════════════════════════════════

    # W01: "The Sun/Moon/Mars in the 7th house makes the native X"
    (
        "W01_planet_house_makes_native",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s+makes?\s+(?:the\s+)?(?:native|person|one)\s+(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # W02: "With Saturn in the 7th, the native X"
    (
        "W02_with_planet_in_house_native",
        rf"[Ww]ith\s+{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+(?P<outcome>[a-zA-Z][^.!?]{{5,200}})",
    ),
    # W03: "If Saturn be in the 7th, [X will] happen" — simple conditional
    (
        "W03_if_planet_house_simple",
        rf"[Ii]f\s+{PLANET_PAT}\s+(?:is|be|occupies)\s+(?:in\s+)?(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # W04: "Saturn in [house] from lagna gives X"
    (
        "W04_planet_house_from_lagna",
        rf"{PLANET_PAT}\s+in\s+(?:the\s+)?{HOUSE_PAT}\s+(?:from\s+(?:the\s+)?(?:Lagna|Ascendant|ascendant|lagna))\s+{VERB_PAT}\s+{OUTCOME_PAT}",
    ),
    # W05: "period/dasa of planet in Nth house gives/makes X" (Hora Sara)
    (
        "W05_period_of_planet_in_house",
        rf"(?:period|dasa|bhukti)\s+of\s+(?:(?:the\s+)?(?:a\s+)?)?(?:planet\s+in\s+(?:the\s+)?{HOUSE_PAT}|{PLANET_PAT})\s+(?:gives?|makes?|causes?|results?\s+in)\s+{OUTCOME_PAT}",
    ),
    # W06: "Saturn gives X if he is in lagna / 7th house" (UK/Hora Sara inverted)
    (
        "W06_planet_gives_if_in_house",
        rf"{PLANET_PAT}\s+{VERB_PAT}\s+(?P<outcome>[a-zA-Z][^.!?]{{5,100}})\s+if\s+(?:he|she|it)\s+is\s+in\s+(?:the\s+)?(?:{HOUSE_ANY}|lagna|ascendant)",
    ),
    # W07: "Should the Nth lord be in the Mth, X" (BPHS "Should" variant)
    (
        "W07_should_lord_be_in_house",
        rf"[Ss]hould\s+(?:the\s+)?{HOUSE_PAT}\s+(?:house\s+)?lord\s+be\s+in\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # W08: "Should the ascendant lord be in X, Y" (BPHS/Hora Sara)
    (
        "W08_should_lagna_lord_be",
        rf"[Ss]hould\s+(?:the\s+)?(?P<planet>ascendant\s+lord|lagna\s+lord)\s+be\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # GROUP X: House-lord in house patterns (no specific planet — uses house lord)
    # These are major BPHS patterns: "If ascendant lord is in Nth, native will be X"
    # ══════════════════════════════════════════════════════════════════════

    # X01: "If the ascendant lord is in the Nth, the native will be X"
    (
        "X01_if_lagna_lord_in_house_native",
        rf"[Ii]f\s+(?:the\s+)?(?P<planet>ascendant\s+lord|lagna\s+lord|lagnesh)\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+(?:be\s+|have\s+|not\s+)?{OUTCOME_PAT}",
    ),
    # X02: "If the Nth house lord is in the Mth, native will be X"
    (
        "X02_if_house_lord_in_house_native",
        rf"[Ii]f\s+(?:the\s+)?{HOUSE_PAT}\s+(?:house\s+)?lord\s+(?:is|be)\s+in\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+(?:be\s+|have\s+)?{OUTCOME_PAT}",
    ),
    # X03: "If the ascendant lord is in the Nth, X" (without "native will")
    (
        "X03_if_lagna_lord_in_house_outcome",
        rf"[Ii]f\s+(?:the\s+)?(?P<planet>ascendant\s+lord|lagna\s+lord|lagnesh)\s+(?:is|be)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # X04: "If the Nth lord is in the Mth, X" (without "native will")
    (
        "X04_if_nth_lord_in_mth_outcome",
        rf"[Ii]f\s+(?:the\s+)?{HOUSE_PAT}\s+(?:house\s+)?lord\s+(?:is|be)\s+in\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s*[,;]\s+{OUTCOME_PAT}",
    ),
    # X05: "The Nth lord in the Mth house, the native will X"
    (
        "X05_nth_lord_in_mth_native_will",
        rf"(?:[Tt]he\s+)?{HOUSE_PAT}\s+(?:house\s+)?lord\s+in\s+(?:the\s+)?(?P<from_house>{HOUSE_NUMS})\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+(?:be\s+|have\s+)?{OUTCOME_PAT}",
    ),
    # X06: "The ascendant lord in the Nth — native will be X"
    (
        "X06_lagna_lord_in_house_outcome",
        rf"(?:[Tt]he\s+)?(?P<planet>ascendant\s+lord|lagna\s+lord)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;—\-]\s+(?:the\s+)?native\s+will\s+(?:be\s+|have\s+)?{OUTCOME_PAT}",
    ),
    # X07: "Ascendant lord in Nth house: native will X" (colon separator)
    (
        "X07_lagna_lord_house_colon",
        rf"(?:[Tt]he\s+)?(?P<planet>ascendant\s+lord|lagna\s+lord)\s+in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*:\s+(?:the\s+)?native\s+will\s+(?:be\s+|have\s+)?{OUTCOME_PAT}",
    ),
    # X08: "When the ascendant lord is in the Nth, the native will be X"
    (
        "X08_when_lagna_lord_in_house",
        rf"[Ww]hen\s+(?:the\s+)?(?P<planet>ascendant\s+lord|lagna\s+lord)\s+(?:is\s+|occupies\s+)?in\s+(?:the\s+)?{HOUSE_PAT}\s*(?:bhava|house)?\s*[,;]\s+(?:the\s+)?native\s+will\s+(?:be\s+|have\s+)?{OUTCOME_PAT}",
    ),
]

# ── Rule dataclass ─────────────────────────────────────────────────────────────

@dataclass
class ExtractedRule:
    rule_hash: str
    text_id: str
    verse_ref: str
    chunk_id: str
    pattern_name: str
    match_text: str
    planet_raw: str
    planet_canon: str
    house_raw: Optional[str]
    house_norm: Optional[str]
    sign_raw: Optional[str]
    sign_canon: Optional[str]
    verb_raw: Optional[str]
    outcome_raw: str
    antecedent_jsonb: dict
    predicate_jsonb: dict
    prediction_jsonb: dict
    confidence: float = 1.0
    extraction_pass_log: dict = field(default_factory=dict)


# ── Text cleaning ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Clean OCR artifacts and normalize whitespace."""
    text = unicodedata.normalize("NFKD", text)
    # Remove non-ASCII characters (OCR Sanskrit, Devanagari, control chars)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    # Collapse multiple spaces/newlines
    text = re.sub(r"[\r\n]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    # Fix common OCR artifacts: "IfVyatipata" → "If Vyatipata", "theNative" → "the Native"
    # Add space before capitalized word that directly follows lowercase
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    # Fix OCR number confusions for ordinals
    # "lOth" → "10th", "lIth" → "11th"
    text = re.sub(r'\bl([Oo])th\b', '10th', text)
    text = re.sub(r'\bl([Ii1])th\b', '11th', text)
    # "1 0th" → "10th", "1 1th" → "11th", "1 2th" → "12th"
    text = re.sub(r'\b1\s+0th\b', '10th', text)
    text = re.sub(r'\b1\s+1th\b', '11th', text)
    text = re.sub(r'\b1\s+2th\b', '12th', text)
    # "4lh" → "4th", "6tb" → "6th", "8tb" → "8th", "5tb" → "5th" etc.
    text = re.sub(r'\b(\d)lh\b', r'\g<1>th', text)
    text = re.sub(r'\b(\d)tb\b', r'\g<1>th', text)
    # "Ilth" / "llth" → "11th" (capital I misread as 1)
    text = re.sub(r'\b[Il][l1]th\b', '11th', text)
    # "I2th" → "12th", "I0th" → "10th"
    text = re.sub(r'\b[I](\d)th\b', r'1\1th', text)
    # "4 lh" → "4th" (space then lh)
    text = re.sub(r'\b(\d)\s+lh\b', r'\g<1>th', text)
    # "2od" → "2nd", "3id" → "3rd" OCR ordinal errors
    text = re.sub(r'\b2od\b', '2nd', text)
    text = re.sub(r'\b3id\b', '3rd', text)
    # "kx" → "in" (common OCR artifact in BPHS: "is kx the 6th" → "is in the 6th")
    text = re.sub(r'\bkx\b', 'in', text)
    # "7th/8th" → "7th or 8th" (slash separators in compounds)
    text = re.sub(r'(\d+(?:st|nd|rd|th))/(\d+(?:st|nd|rd|th))', r'\1 or \2', text)
    # "<he " → "the " (OCR '<' misread for 't')
    text = re.sub(r'<he\s', 'the ', text)
    # "{the" → "the" (curly brace OCR artifact)
    text = re.sub(r'\{the\b', 'the', text)
    # "will he " → "will be " (OCR 'h' for 'b' before vowels)
    text = re.sub(r'\bwill he\s+(?=[a-z])', 'will be ', text)
    # "wiJ 1 " / "wi J 1" / "wi j 1" → "will " (OCR artifact for "will")
    text = re.sub(r'\bwi\s*[Jj]\s*1\s+', 'will ', text)
    # "Will" → "will" (OCR capital)
    text = re.sub(r'\bWill\b', 'will', text)
    return text.strip()


STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "and", "or", "but", "not",
    "with", "by", "from", "as", "if", "that", "this", "it", "he", "she",
    "his", "her", "they", "their", "we", "our", "will", "would", "can",
    "could", "may", "might", "shall", "should", "do", "does", "did",
    "have", "has", "had", "there", "one", "so", "very", "also", "then",
    "than", "too", "no", "any", "all", "such", "thus", "get", "its",
    "who", "what", "when", "where", "while", "into", "out", "up", "down",
    "been", "through", "about", "after", "before", "between", "over",
    "under", "again", "further", "same", "other", "him", "them",
}


def has_outcome_noun(outcome_text: str) -> bool:
    """Check: outcome contains meaningful content (not just stopwords/OCR fragments).

    Two-tier check:
    1. If any word is in JYOTISH_OUTCOME_NOUNS, accept immediately.
    2. Otherwise, accept if outcome has ≥3 non-stopword content words AND ≥10 chars.
    This prevents accepting pure OCR garbage like 'i o e' while accepting
    domain-valid but vocabulary-novel outcomes.
    """
    words = re.findall(r"\b[a-zA-Z-]+\b", outcome_text.lower())
    # Tier 1: exact noun match
    if any(w in JYOTISH_OUTCOME_NOUNS for w in words):
        return True
    # Tier 2: structural check — enough non-stopword content
    content_words = [w for w in words if w not in STOPWORDS and len(w) >= 4]
    return len(content_words) >= 3 and len(outcome_text) >= 10


# ── Core extraction ────────────────────────────────────────────────────────────

def extract_from_chunk(
    chunk_id: str,
    text_id: str,
    verse_ref: str,
    content_en: str,
) -> tuple[list[ExtractedRule], list[dict]]:
    """Extract rules from one chunk."""
    accepted: list[ExtractedRule] = []
    rejected: list[dict] = []
    seen_hashes: set[str] = set()

    cleaned = clean_text(content_en)

    for pattern_name, pattern_str in SUTRA_PATTERNS:
        try:
            compiled = re.compile(pattern_str, re.IGNORECASE)
        except re.error as e:
            logger.debug("Pattern compile error %s: %s", pattern_name, e)
            continue

        for match in compiled.finditer(cleaned):
            match_text = match.group(0).strip()
            if len(match_text) < 20:
                continue

            rule_hash = hashlib.sha256(
                f"{chunk_id}:{match_text}".encode()
            ).hexdigest()[:16]

            if rule_hash in seen_hashes:
                continue
            seen_hashes.add(rule_hash)

            # Extract named groups safely
            gd = match.groupdict()
            planet_raw = gd.get("planet") or ""
            house_raw = gd.get("house")
            sign_raw = gd.get("sign")
            verb_raw = gd.get("verb")
            outcome_raw = (gd.get("outcome") or "").strip().rstrip(".,;:—-")

            # ── Deterministic quality checks ──────────────────────────────────
            rejection_reasons = []

            # Check 1: verse_ref is non-empty
            if not verse_ref or verse_ref.strip() == "":
                rejection_reasons.append("verse_ref_empty")

            # Check 2: planet token validation
            # Some patterns don't require a standard graha
            flexible_planet_patterns = {
                "F01_yoga_native", "G01_planet_sign_dasa_bullet",
                "H01_person_born_will_planet", "H02_person_born_becomes",
                "H03_when_planet_pos_person", "H04_person_born_declared",
                "H05_person_born_in_sign", "H06_person_born_will_verb",
                "H07_one_born_in",
                "I04_if_special_point_in_house",
                "K01_if_anything_native_will", "K02_if_anything_native_will_have",
                "K03_when_anything_native_will", "K05_when_anything_person_born_will",
                "K06_when_condition_person_declared", "K07_if_condition_person_will",
                "P03_a_planet_in_house_gives",
                "Q01_person_die_in_year", "Q02_child_not_live",
                # Yoga patterns - planet group is yoga name, not a graha
                "R01_person_born_under_yoga", "R02_person_born_in_yoga",
                "R03_one_born_in_yoga", "R04_person_in_yoga_is",
                # Astrologer-declares patterns
                "S01_astrologer_declare", "S02_must_be_declared",
                # House-lord patterns (planet group = lord description, not graha name)
                "X01_if_lagna_lord_in_house_native", "X02_if_house_lord_in_house_native",
                "X03_if_lagna_lord_in_house_outcome", "X04_if_nth_lord_in_mth_outcome",
                "X05_nth_lord_in_mth_native_will", "X06_lagna_lord_in_house_outcome",
                "X07_lagna_lord_house_colon", "X08_when_lagna_lord_in_house",
                "W07_should_lord_be_in_house", "W08_should_lagna_lord_be",
            }

            # For house-lord patterns — planet group is lord description
            if pattern_name in {
                "X01_if_lagna_lord_in_house_native", "X02_if_house_lord_in_house_native",
                "X03_if_lagna_lord_in_house_outcome", "X04_if_nth_lord_in_mth_outcome",
                "X05_nth_lord_in_mth_native_will", "X06_lagna_lord_in_house_outcome",
                "X07_lagna_lord_house_colon", "X08_when_lagna_lord_in_house",
                "W07_should_lord_be_in_house", "W08_should_lagna_lord_be",
            }:
                lord_desc = planet_raw.strip() if planet_raw else "house_lord"
                planet_raw = lord_desc
                planet_canon = "LORD"

            # For yoga patterns — the "planet" group is a yoga name, not a graha
            elif pattern_name in {
                "R01_person_born_under_yoga", "R02_person_born_in_yoga",
                "R03_one_born_in_yoga", "R04_person_in_yoga_is",
            }:
                yoga_name = planet_raw.strip()
                planet_raw = yoga_name
                planet_canon = "YOGA"
            # For astrologer-declares patterns — extract planet from match text
            elif pattern_name in {"S01_astrologer_declare", "S02_must_be_declared"}:
                planet_match = re.search(
                    r'\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|'
                    r'Ravi|Surya|Chandra|Mangal|Budha|Guru|Shukra|Shani)\b',
                    match_text, re.IGNORECASE
                )
                if planet_match:
                    planet_raw = planet_match.group(1)
                    planet_canon = normalize_planet(planet_raw)
                else:
                    planet_raw = "multi"
                    planet_canon = "MISC"
            # For K/H patterns without explicit planet group, extract from condition text
            elif pattern_name in {
                "K01_if_anything_native_will", "K02_if_anything_native_will_have",
                "K03_when_anything_native_will", "K05_when_anything_person_born_will",
                "K06_when_condition_person_declared", "K07_if_condition_person_will",
            }:
                condition_text = gd.get("condition") or match_text
                # Find the first planet mentioned in the condition
                planet_match = re.search(
                    r'\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|'
                    r'Ravi|Surya|Chandra|Mangal|Budha|Guru|Shukra|Shani)\b',
                    condition_text, re.IGNORECASE
                )
                if planet_match:
                    planet_raw = planet_match.group(1)
                    planet_canon = normalize_planet(planet_raw)
                else:
                    planet_raw = "multi_planet"
                    planet_canon = "MISC"
            elif pattern_name in {
                "H01_person_born_will_planet", "H02_person_born_becomes",
                "H03_when_planet_pos_person", "H04_person_born_declared",
                "H05_person_born_in_sign", "H06_person_born_will_verb",
                "H07_one_born_in", "Q01_person_die_in_year", "Q02_child_not_live",
            }:
                # For person-born patterns, extract planet from the entire match_text
                planet_match = re.search(
                    r'\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu|'
                    r'Ravi|Surya|Chandra|Mangal|Budha|Guru|Shukra|Shani)\b',
                    match_text, re.IGNORECASE
                )
                if planet_match:
                    planet_raw = planet_match.group(1)
                    planet_canon = normalize_planet(planet_raw)
                else:
                    planet_raw = "multi"
                    planet_canon = "MISC"

                # Also try to extract house from match_text
                if not house_raw:
                    house_match = re.search(
                        r'\b(' + HOUSE_NUMS + r')\s*(?:bhava|house)?',
                        match_text, re.IGNORECASE
                    )
                    if house_match:
                        house_raw = house_match.group(1)
            elif pattern_name in flexible_planet_patterns:
                planet_canon = normalize_planet(planet_raw) if planet_raw else "MISC"
                if planet_canon not in {
                    "SUN", "MON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH", "KET",
                }:
                    planet_canon = planet_raw.upper()[:6] if planet_raw else "MISC"
            else:
                planet_canon = normalize_planet(planet_raw) if planet_raw else ""
                if planet_canon not in {
                    "SUN", "MON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH", "KET",
                }:
                    rejection_reasons.append(f"planet_unrecognized:{planet_raw}")

            # Check 3: outcome contains noun
            if not has_outcome_noun(outcome_raw):
                rejection_reasons.append("outcome_no_noun")

            # Check 4: outcome minimum length (2 words, 5+ chars each counts)
            # Short outcomes like "a king", "insane", "a dwarf" are valid Jyotish results
            outcome_meaningful_words = [w for w in outcome_raw.split() if len(w) >= 3]
            if len(outcome_meaningful_words) < 2:
                rejection_reasons.append("outcome_too_short")

            # Check 5: outcome shouldn't start with OCR garbage symbol
            if outcome_raw and outcome_raw[0] in "!@#$%^&*_+=[]{}|;':\"<>?,/\\":
                rejection_reasons.append("outcome_starts_with_symbol")

            # Build JSONBs
            house_norm = normalize_house(house_raw) if house_raw else None
            sign_canon = normalize_sign(sign_raw) if sign_raw else None

            antecedent: dict = {}
            if planet_canon == "YOGA":
                antecedent["yoga"] = planet_raw.strip()[:50]
            elif planet_canon == "LORD":
                antecedent["lord"] = planet_raw.strip()[:80]
            elif planet_canon and planet_canon not in {"MISC"}:
                antecedent["planet"] = planet_canon
            elif planet_raw and planet_raw not in {"multi_planet", "multi"}:
                antecedent["special_point"] = planet_raw
            if house_norm:
                antecedent["house"] = house_norm
            if sign_canon:
                antecedent["sign"] = sign_canon
            # For positional patterns
            if "position" in gd and gd.get("position"):
                antecedent["position"] = (gd["position"] or "").strip()
            # For from_house in lord patterns
            if "from_house" in gd and gd.get("from_house"):
                antecedent["from_house"] = normalize_house(gd["from_house"])
            # For exaltation/debilitation state
            if "state" in gd and gd.get("state"):
                antecedent["state"] = (gd["state"] or "").strip()

            # For person-born patterns, use match_text as context even if no planet/house
            if not antecedent and pattern_name in {
                "H02_person_born_becomes", "H06_person_born_will_verb",
                "H01_person_born_will_planet", "H03_when_planet_pos_person",
                "H04_person_born_declared", "H05_person_born_in_sign",
                "H07_one_born_in",
                "S01_astrologer_declare", "S02_must_be_declared",
            }:
                antecedent["context"] = "person_born"

            if not antecedent:
                rejection_reasons.append("no_antecedent")

            predicate: dict = {
                "pattern": pattern_name,
                "verb": verb_raw or "gives",
                "match_text": match_text[:200],
            }

            prediction: dict = {
                "outcome_text": outcome_raw[:300],
                "confidence": 1.0,
                "method": "python_regex",
            }

            pass_log = {
                "pattern": pattern_name,
                "match_text": match_text[:150],
                "checks": {
                    "verse_ref_present": not any("verse_ref" in r for r in rejection_reasons),
                    "planet_recognized": not any("planet_unrecognized" in r for r in rejection_reasons),
                    "outcome_has_noun": not any("outcome_no_noun" in r for r in rejection_reasons),
                    "outcome_min_length": not any("outcome_too_short" in r for r in rejection_reasons),
                },
            }

            rule = ExtractedRule(
                rule_hash=rule_hash,
                text_id=text_id,
                verse_ref=verse_ref,
                chunk_id=chunk_id,
                pattern_name=pattern_name,
                match_text=match_text,
                planet_raw=planet_raw,
                planet_canon=planet_canon,
                house_raw=house_raw,
                house_norm=house_norm,
                sign_raw=sign_raw,
                sign_canon=sign_canon,
                verb_raw=verb_raw,
                outcome_raw=outcome_raw,
                antecedent_jsonb=antecedent,
                predicate_jsonb=predicate,
                prediction_jsonb=prediction,
                confidence=1.0,
                extraction_pass_log=pass_log,
            )

            if rejection_reasons:
                rejected.append({
                    "rule_hash": rule_hash,
                    "text_id": text_id,
                    "verse_ref": verse_ref,
                    "antecedent_jsonb": antecedent,
                    "predicate_jsonb": predicate,
                    "prediction_jsonb": prediction,
                    "extraction_pass_log": pass_log,
                    "rejection_reason": "; ".join(rejection_reasons),
                })
            else:
                accepted.append(rule)

    return accepted, rejected


# ── Deduplication ─────────────────────────────────────────────────────────────

def dedup_rules(rules: list[ExtractedRule]) -> tuple[list[ExtractedRule], int, list[dict]]:
    """
    Phase 3 dedup:
    1. Exact dedup by (planet_canon, house_norm, first_8_outcome_words)
    2. Fuzzy dedup using Levenshtein ratio >= 0.85 on outcome text
    Returns (accepted, dropped_count, review_overflow) where review_overflow
    are the duplicate rules routed to sutravali_review for audit.
    """
    # Step 1: exact dedup
    # Key includes text_id + verse_ref to preserve cross-text duplicates as valid
    # (same rule may appear in multiple texts = valid multiple sources)
    # Within same text+verse, deduplicate on planet+house+sign+outcome
    seen_exact: set[str] = set()
    after_exact: list[ExtractedRule] = []
    review_overflow: list[dict] = []
    for rule in rules:
        # Use first 8 words of outcome for dedup (more discriminating than 5)
        first8 = " ".join(rule.outcome_raw.lower().split()[:8])
        # Include text_id and verse_ref in key so cross-text matches are preserved
        key = f"{rule.text_id}|{rule.verse_ref}|{rule.planet_canon}|{rule.house_norm}|{rule.sign_canon}|{first8}"
        if key not in seen_exact:
            seen_exact.add(key)
            after_exact.append(rule)
        else:
            # Route to review as duplicate candidate
            review_overflow.append({
                "rule_hash": rule.rule_hash,
                "text_id": rule.text_id,
                "verse_ref": rule.verse_ref,
                "antecedent_jsonb": rule.antecedent_jsonb,
                "predicate_jsonb": rule.predicate_jsonb,
                "prediction_jsonb": rule.prediction_jsonb,
                "extraction_pass_log": rule.extraction_pass_log,
                "rejection_reason": "dedup_duplicate",
            })

    dropped_exact = len(review_overflow)

    # Step 2: Levenshtein fuzzy dedup
    have_levenshtein = False
    lev_module = None
    for mod_name in ("Levenshtein", "rapidfuzz.distance"):
        try:
            if mod_name == "Levenshtein":
                import Levenshtein as _lev  # type: ignore[import]
                lev_module = _lev
            else:
                from rapidfuzz.distance import Levenshtein as _lev  # type: ignore[import]
                lev_module = _lev
            have_levenshtein = True
            break
        except ImportError:
            continue

    if not have_levenshtein:
        logger.info("Levenshtein not available — exact dedup only")
        return after_exact, dropped_exact, review_overflow

    # Group by planet for efficiency
    from collections import defaultdict
    by_planet: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(after_exact):
        by_planet[r.planet_canon].append(i)

    drop_indices: set[int] = set()
    for planet, indices in by_planet.items():
        for i_pos, i in enumerate(indices):
            if i in drop_indices:
                continue
            ri = after_exact[i]
            for j in indices[i_pos + 1:]:
                if j in drop_indices:
                    continue
                rj = after_exact[j]
                if ri.outcome_raw and rj.outcome_raw:
                    try:
                        ratio = lev_module.ratio(
                            ri.outcome_raw[:150], rj.outcome_raw[:150]
                        )
                    except Exception:
                        continue
                    if ratio >= 0.85:
                        if len(ri.outcome_raw) >= len(rj.outcome_raw):
                            drop_indices.add(j)
                        else:
                            drop_indices.add(i)
                            break

    after_fuzzy = [r for i, r in enumerate(after_exact) if i not in drop_indices]
    dropped_fuzzy = len(after_exact) - len(after_fuzzy)

    logger.info(
        "Dedup: exact dropped %d, fuzzy dropped %d, final %d rules",
        dropped_exact, dropped_fuzzy, len(after_fuzzy),
    )
    return after_fuzzy, dropped_exact + dropped_fuzzy, review_overflow


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_conn():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    import psycopg2  # type: ignore[import]
    return psycopg2.connect(url)


def persist_rules(rules: list[ExtractedRule], conn=None) -> int:
    """Insert accepted rules into sutravali_rules. Returns rows inserted."""
    if not rules:
        return 0
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    inserted = 0
    try:
        with conn.cursor() as cur:
            for r in rules:
                cur.execute(
                    """
                    INSERT INTO sutravali_rules
                      (text_id, verse_ref, antecedent_jsonb, predicate_jsonb,
                       prediction_jsonb, confidence, extracted_by, extraction_pass_log)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        r.text_id,
                        r.verse_ref,
                        json.dumps(r.antecedent_jsonb),
                        json.dumps(r.predicate_jsonb),
                        json.dumps(r.prediction_jsonb),
                        r.confidence,
                        "python_regex",
                        json.dumps(r.extraction_pass_log),
                    ),
                )
                if cur.rowcount > 0:
                    inserted += 1
        conn.commit()
    finally:
        if close_conn:
            conn.close()
    return inserted


def persist_rejected(rejected: list[dict], conn=None) -> int:
    """Insert rejected candidates into sutravali_review. Returns rows inserted."""
    if not rejected:
        return 0
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    inserted = 0
    try:
        with conn.cursor() as cur:
            for r in rejected:
                cur.execute(
                    """
                    INSERT INTO sutravali_review
                      (text_id, verse_ref, antecedent_jsonb, predicate_jsonb,
                       prediction_jsonb, confidence, extracted_by, extraction_pass_log,
                       rejection_reason, review_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        r["text_id"],
                        r["verse_ref"],
                        json.dumps(r["antecedent_jsonb"]),
                        json.dumps(r["predicate_jsonb"]),
                        json.dumps(r["prediction_jsonb"]),
                        0.5,
                        "python_regex",
                        json.dumps(r["extraction_pass_log"]),
                        r["rejection_reason"],
                        "pending",
                    ),
                )
                if cur.rowcount > 0:
                    inserted += 1
        conn.commit()
    finally:
        if close_conn:
            conn.close()
    return inserted


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_extraction(conn=None) -> dict[str, Any]:
    """
    Full extraction pipeline.
    Returns summary dict.
    """
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    try:
        # Fetch all chunks
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_id, text_id, verse_ref, content_en
                FROM classical_text_chunks
                ORDER BY text_id, chunk_id
                """
            )
            chunks = cur.fetchall()

        logger.info("Loaded %d classical text chunks", len(chunks))

        all_accepted: list[ExtractedRule] = []
        all_rejected: list[dict] = []
        chunks_with_matches = 0

        pattern_hits: dict[str, int] = {}

        for chunk_id, text_id, verse_ref, content_en in chunks:
            if not content_en:
                continue
            accepted, rejected = extract_from_chunk(chunk_id, text_id, verse_ref, content_en)
            if accepted or rejected:
                chunks_with_matches += 1
            for r in accepted:
                pattern_hits[r.pattern_name] = pattern_hits.get(r.pattern_name, 0) + 1
            all_accepted.extend(accepted)
            all_rejected.extend(rejected)

        logger.info(
            "Raw extraction: %d accepted, %d rejected from %d chunks (matched %d)",
            len(all_accepted),
            len(all_rejected),
            len(chunks),
            chunks_with_matches,
        )
        logger.info("Pattern hits: %s", sorted(pattern_hits.items(), key=lambda x: -x[1]))

        # Phase 3: Dedup
        deduped, n_dropped, review_overflow = dedup_rules(all_accepted)
        logger.info("After dedup: %d rules (%d dropped to review)", len(deduped), n_dropped)

        # Persist
        rules_inserted = persist_rules(deduped, conn=conn)
        # Combine rejected + dedup overflow into review table
        review_inserted = persist_rejected(all_rejected + review_overflow, conn=conn)

        coverage_pct = (
            round(100.0 * chunks_with_matches / len(chunks), 1) if chunks else 0.0
        )

        return {
            "ok": True,
            "chunks_processed": len(chunks),
            "chunks_with_matches": chunks_with_matches,
            "coverage_pct": coverage_pct,
            "raw_accepted": len(all_accepted),
            "raw_rejected": len(all_rejected),
            "dedup_dropped": n_dropped,
            "rules_inserted": rules_inserted,
            "review_inserted": review_inserted,
            "patterns_tried": len(SUTRA_PATTERNS),
            "pattern_hits": pattern_hits,
        }

    finally:
        if close_conn:
            conn.close()


# ── Volume check ──────────────────────────────────────────────────────────────

def check_volume(conn=None) -> dict[str, Any]:
    """Check volume floors for sutravali tables."""
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM sutravali_rules")
            rules_count = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM sutravali_review")
            review_count = cur.fetchone()[0]

        return {
            "asset": "brahmagyan.sutravali",
            "sutravali_rules": {
                "actual": rules_count,
                "floor": RULES_FLOOR,
                "status": "GREEN" if rules_count >= RULES_FLOOR else "RED",
            },
            "sutravali_review": {
                "actual": review_count,
                "floor": REVIEW_FLOOR,
                "status": "GREEN" if review_count >= REVIEW_FLOOR else "AMBER",
            },
            "overall_status": "GREEN" if rules_count >= RULES_FLOOR else "RED",
        }
    finally:
        if close_conn:
            conn.close()


# ── Query functions (capabilities) ────────────────────────────────────────────

def query_rules(
    antecedent_pattern: Optional[dict] = None,
    limit: int = 20,
    conn=None,
) -> dict[str, Any]:
    """Query sutravali_rules by antecedent JSONB pattern."""
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    try:
        with conn.cursor() as cur:
            if antecedent_pattern:
                cur.execute(
                    """
                    SELECT text_id, verse_ref, antecedent_jsonb, predicate_jsonb,
                           prediction_jsonb, confidence
                    FROM sutravali_rules
                    WHERE antecedent_jsonb @> %s::jsonb
                    ORDER BY confidence DESC
                    LIMIT %s
                    """,
                    (json.dumps(antecedent_pattern), limit),
                )
            else:
                cur.execute(
                    """
                    SELECT text_id, verse_ref, antecedent_jsonb, predicate_jsonb,
                           prediction_jsonb, confidence
                    FROM sutravali_rules
                    ORDER BY confidence DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
            rows = cur.fetchall()

        return {
            "ok": True,
            "count": len(rows),
            "rules": [
                {
                    "text_id": r[0],
                    "verse_ref": r[1],
                    "antecedent": r[2],
                    "predicate": r[3],
                    "prediction": r[4],
                    "confidence": float(r[5]),
                }
                for r in rows
            ],
        }
    finally:
        if close_conn:
            conn.close()


def query_rules_for_planet(
    body: str,
    house: Optional[int] = None,
    limit: int = 20,
    conn=None,
) -> dict[str, Any]:
    """Query rules for a given planet."""
    canon = normalize_planet(body)
    if canon not in {"SUN", "MON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH", "KET"}:
        canon = body.upper()[:3]

    pattern: dict = {"planet": canon}
    if house is not None:
        ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
        pattern["house"] = ordinals.get(house, f"{house}th")

    return query_rules(antecedent_pattern=pattern, limit=limit, conn=conn)


def query_sutras_by_planet(
    planet: str,
    limit: int = 20,
    conn=None,
) -> dict[str, Any]:
    """Capability: query_sutras_by_planet"""
    return query_rules_for_planet(planet, limit=limit, conn=conn)


def query_sutras_by_sign(
    sign: str,
    limit: int = 20,
    conn=None,
) -> dict[str, Any]:
    """Capability: query_sutras_by_sign"""
    canon = normalize_sign(sign)
    return query_rules(antecedent_pattern={"sign": canon}, limit=limit, conn=conn)


def query_sutras_by_house(
    house: int,
    planet: Optional[str] = None,
    limit: int = 20,
    conn=None,
) -> dict[str, Any]:
    """Capability: query_sutras_by_house"""
    ordinals = {1: "1st", 2: "2nd", 3: "3rd"}
    house_str = ordinals.get(house, f"{house}th")
    pattern: dict = {"house": house_str}
    if planet:
        pattern["planet"] = normalize_planet(planet)
    return query_rules(antecedent_pattern=pattern, limit=limit, conn=conn)


def read_rule(rule_id: str, conn=None) -> dict[str, Any]:
    """Capability: read_rule — fetch a specific rule by UUID."""
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rule_id::text, text_id, verse_ref, antecedent_jsonb,
                       predicate_jsonb, prediction_jsonb, confidence, extracted_by,
                       extraction_pass_log, created_at
                FROM sutravali_rules
                WHERE rule_id = %s::uuid
                """,
                (rule_id,),
            )
            row = cur.fetchone()

        if not row:
            return {"ok": False, "error": "rule_not_found", "rule_id": rule_id}

        return {
            "ok": True,
            "rule": {
                "rule_id": row[0],
                "text_id": row[1],
                "verse_ref": row[2],
                "antecedent": row[3],
                "predicate": row[4],
                "prediction": row[5],
                "confidence": float(row[6]),
                "extracted_by": row[7],
                "extraction_pass_log": row[8],
                "created_at": str(row[9]),
            },
        }
    finally:
        if close_conn:
            conn.close()


def list_rules_by_text(text_id: str, limit: int = 50, conn=None) -> dict[str, Any]:
    """Capability: list_rules_by_text"""
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT rule_id::text, verse_ref, antecedent_jsonb,
                       prediction_jsonb, confidence
                FROM sutravali_rules
                WHERE text_id = %s
                ORDER BY verse_ref
                LIMIT %s
                """,
                (text_id, limit),
            )
            rows = cur.fetchall()
            cur.execute(
                "SELECT count(*) FROM sutravali_rules WHERE text_id = %s",
                (text_id,),
            )
            total = cur.fetchone()[0]

        return {
            "ok": True,
            "text_id": text_id,
            "total": total,
            "shown": len(rows),
            "rules": [
                {
                    "rule_id": r[0],
                    "verse_ref": r[1],
                    "antecedent": r[2],
                    "prediction": r[3],
                    "confidence": float(r[4]),
                }
                for r in rows
            ],
        }
    finally:
        if close_conn:
            conn.close()


# ── Smoke tests ───────────────────────────────────────────────────────────────

def run_smoke_tests(conn=None) -> dict[str, Any]:
    """
    Run acceptance criteria smoke tests.
    AC1: query_sutras_by_planet('Saturn', house=7) returns >= 3 rules
    AC2: each rule has source_text + verse_ref NOT NULL
    """
    results = {}

    # AC1: Saturn in 7th house
    saturn_7 = query_rules_for_planet("Saturn", house=7, conn=conn)
    results["AC1_saturn_7th"] = {
        "pass": saturn_7["count"] >= 3,
        "count": saturn_7["count"],
        "threshold": 3,
    }

    # AC2: All rules have verse_ref NOT NULL
    close_conn = False
    if conn is None:
        conn = _get_conn()
        close_conn = True
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM sutravali_rules WHERE verse_ref IS NULL OR verse_ref = ''"
            )
            null_verse_ref = cur.fetchone()[0]
            cur.execute(
                "SELECT count(*) FROM sutravali_rules WHERE text_id IS NULL OR text_id = ''"
            )
            null_text_id = cur.fetchone()[0]
            cur.execute(
                "SELECT count(*) FROM sutravali_rules WHERE extraction_pass_log IS NULL"
            )
            null_log = cur.fetchone()[0]
        results["AC2_verse_ref_not_null"] = {
            "pass": null_verse_ref == 0,
            "null_count": null_verse_ref,
        }
        results["AC2_text_id_not_null"] = {
            "pass": null_text_id == 0,
            "null_count": null_text_id,
        }
        results["AC2_pass_log_not_null"] = {
            "pass": null_log == 0,
            "null_count": null_log,
        }
    finally:
        if close_conn:
            conn.close()

    all_pass = all(v.get("pass", False) for v in results.values())
    return {"ok": all_pass, "tests": results}
