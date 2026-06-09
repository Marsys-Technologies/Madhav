"""
brahmagyan.l0_rules — L0 Brahmagyan: Classical Rule Extraction (bg_rules)
==========================================================================

Populates `sutravali_rules` with classical astrological rules extracted
deterministically from `classical_text_chunks` via regex pattern matching.

Design:
  - ZERO LLM — pure Python regex pattern library (v1.1 directive)
  - ~14 pattern families covering the principal rule types in classical texts
  - Deterministic rule_id: UUID5(NAMESPACE_URL, "text_id|verse_ref|sha256[:16]")
  - Quality score: 0.0–1.0 from 5 deterministic criteria (≥0.6 → live)
  - ON CONFLICT (rule_id) DO NOTHING → idempotent

Volume:  ~1,900–2,500 rules from 8,193 chunks (1,908 chunks have result-
         clauses; average ~1.2 matches per qualifying chunk).

BRAHMA-BG-0-8
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generator

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

EXTRACTED_BY = "python_regex_v2"
QUALITY_THRESHOLD_LIVE = 0.6     # ≥0.6 → sutravali_rules
QUALITY_THRESHOLD_REVIEW = 0.4   # 0.4–0.6 → log-and-skip; <0.4 → reject

# ── Ontology macros (hardcoded — sourced from bg_ontology canonical_ids) ─────

PLANETS_EN = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
    "Rahu", "Ketu",
]
PLANETS_ALT = [
    "Surya", "Chandra", "Mangal", "Budha", "Guru", "Shukra", "Shani",
    "Rahu", "Ketu", "Sol", "Luna",
]

PLANET_CANONICAL = {
    # English
    "sun": "sun", "moon": "moon", "mars": "mars", "mercury": "mercury",
    "jupiter": "jupiter", "venus": "venus", "saturn": "saturn",
    "rahu": "rahu", "ketu": "ketu",
    # Sanskrit aliases
    "surya": "sun", "chandra": "moon", "mangal": "mars", "mangala": "mars",
    "budha": "mercury", "guru": "jupiter", "shukra": "venus",
    "shani": "saturn", "sol": "sun", "luna": "moon",
    "sukra": "venus", "budh": "mercury",
}

SIGNS_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_NUMBER = {s.lower(): i + 1 for i, s in enumerate(SIGNS_EN)}

ORDINALS = [
    "first", "second", "third", "fourth", "fifth", "sixth",
    "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth",
]
ORDINAL_TO_NUM = {w: i + 1 for i, w in enumerate(ORDINALS)}

ORDINALS_ABBR = [
    r"1st", r"2nd", r"3rd", r"4th", r"5th", r"6th",
    r"7th", r"8th", r"9th", r"10th", r"11th", r"12th",
]
ABBR_TO_NUM = {a: i + 1 for i, a in enumerate(ORDINALS_ABBR)}

KARAKA_NAMES = [
    "Atmakaraka", "Amatyakaraka", "Bhratrukaraka", "Matrukaraka",
    "Putrakaraka", "Gnatikaraka", "Darakaraka", "Pitrukaraka",
]

RESULT_WORDS = (
    r"gives?|bestows?|causes?|produces?|confers?|grants?|"
    r"makes?\s+the\s+native|native\s+will\s+be|native\s+will\s+have|"
    r"will\s+be\s+blessed|will\s+become|will\s+suffer|will\s+enjoy|"
    r"results?\s+in|leads?\s+to|brings?\s+(?:about\s+)?(?:\w+\s+)?(?:wealth|fame|disease|happiness|trouble)|"
    r"ushers?|indicating|indicates?|signifies?"
)

# ── Compiled regex helpers ─────────────────────────────────────────────────────

_PLANET_PAT = r"(?:" + "|".join(re.escape(p) for p in PLANETS_EN + PLANETS_ALT) + r")"
_SIGN_PAT = r"(?:" + "|".join(re.escape(s) for s in SIGNS_EN) + r")"
_ORDINAL_PAT = r"(?:" + "|".join(ORDINALS) + r")"
_ABBR_PAT = r"(?:1[0-2]th|[1-9](?:st|nd|rd|th))"
_HOUSE_NUM_PAT = rf"(?:{_ORDINAL_PAT}|{_ABBR_PAT})"
_RESULT_PAT = RESULT_WORDS


# ── Rule dataclass ─────────────────────────────────────────────────────────────

@dataclass
class ExtractedRule:
    text_id: str
    verse_ref: str
    chunk_uuid: str               # classical_text_chunks.id
    antecedent: list[dict]        # [{planet, house, sign, relation}, ...]
    predicate: dict               # {type: str, description: str}
    prediction: dict              # {result: str, domain: str}
    pattern_name: str
    match_text: str               # the matched substring (for logging)
    quality_score: float = 0.0
    yoga_canonical_id: str | None = None
    dasha_system_id: str | None = None
    transit_marker: bool = False


# ── Deterministic rule_id ─────────────────────────────────────────────────────

def _make_rule_id(text_id: str, verse_ref: str, antecedent: list, prediction: dict) -> uuid.UUID:
    """
    Deterministic UUID5 from (text_id, verse_ref, sha256[:16] of antecedent+prediction).
    Guarantees same content → same UUID; different content → different UUID.
    """
    payload = f"{text_id}|{verse_ref}|{json.dumps(antecedent, sort_keys=True)}|{json.dumps(prediction, sort_keys=True)}"
    sha = hashlib.sha256(payload.encode()).hexdigest()[:24]
    key = f"{text_id}|{verse_ref}|{sha}"
    return uuid.uuid5(uuid.NAMESPACE_URL, key)


# ── Quality scoring (deterministic, 5 criteria, 0.2 each) ─────────────────────

def _score(
    antecedent: list[dict],
    prediction: dict,
    verse_ref: str,
    text_id_valid: bool,
) -> float:
    """
    Returns quality score 0.0–1.0 (each criterion = 0.2):
      1. antecedent has a recognised planet or house
      2. antecedent house is 1–12 (if present)
      3. prediction result is non-empty and has ≥3 words
      4. verse_ref is non-empty (chunk resolved in bg_texts)
      5. text_id is valid (in the known corpus)
    """
    score = 0.0
    # Criterion 1: antecedent has planet or house
    has_planet = any(a.get("planet") for a in antecedent)
    has_house = any(a.get("house") for a in antecedent)
    has_sign = any(a.get("sign") for a in antecedent)
    if has_planet or has_house or has_sign:
        score += 0.2
    # Criterion 2: house number in range 1-12 (if any)
    house_nums = [a.get("house") for a in antecedent if a.get("house")]
    if house_nums:
        if all(isinstance(h, int) and 1 <= h <= 12 for h in house_nums):
            score += 0.2
    else:
        # No house is OK — give credit for sign-based rules
        if has_sign or has_planet:
            score += 0.2
    # Criterion 3: prediction non-empty ≥ 3 words
    result_text = prediction.get("result", "")
    if result_text and len(result_text.split()) >= 3:
        score += 0.2
    # Criterion 4: verse_ref non-empty
    if verse_ref and len(verse_ref) > 0:
        score += 0.2
    # Criterion 5: text_id valid
    if text_id_valid:
        score += 0.2
    return round(score, 3)


# ── Pattern families ──────────────────────────────────────────────────────────

# Each pattern: (name, regex_flags, pattern_str, extract_fn)
# extract_fn(m: re.Match, chunk_content: str) -> ExtractedRule | None

FLAGS = re.IGNORECASE | re.DOTALL


def _canon_planet(name: str) -> str | None:
    return PLANET_CANONICAL.get(name.lower().strip())


def _canon_house(token: str) -> int | None:
    t = token.lower().strip()
    if t in ORDINAL_TO_NUM:
        return ORDINAL_TO_NUM[t]
    if t in ABBR_TO_NUM:
        return ABBR_TO_NUM[t]
    # Numeric digit
    try:
        n = int(re.sub(r'[^0-9]', '', t))
        if 1 <= n <= 12:
            return n
    except (ValueError, TypeError):
        pass
    return None


def _canon_sign(name: str) -> int | None:
    return SIGN_NUMBER.get(name.lower().strip())


def _extract_result_clause(text: str, match_end: int, window: int = 120) -> str:
    """Extract the result clause after a result-word trigger."""
    tail = text[match_end:match_end + window]
    # Clean up OCR noise: collapse multiple spaces/newlines
    tail = re.sub(r'\s+', ' ', tail).strip()
    # Truncate at sentence boundary
    for sep in ['. ', '! ', '? ', '\n']:
        idx = tail.find(sep)
        if 0 < idx < 100:
            tail = tail[:idx].strip()
            break
    return tail[:150]


# ─── Pattern 1: <planet> in the <ordinal> house … gives/bestows <result> ─────

_P1 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,4}}\s+in\s+(?:the\s+)?({_HOUSE_NUM_PAT})\s+(?:house|bhava|Bhava|House)\b'
    rf'(?P<tail>.{{0,120}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p1_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    house = _canon_house(m.group(2))
    if not planet or not house:
        return None
    result_start = m.end()
    result = _extract_result_clause(full_text, result_start)
    return {
        "antecedent": [{"planet": planet, "house": house, "relation": "occupies"}],
        "predicate": {"type": "planet_in_house", "description": f"{planet} in house {house}"},
        "prediction": {"result": result, "domain": "house_signification"},
        "pattern": "planet_in_house",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 2: <planet> in <sign> … gives/causes <result> ───────────────────

_P2 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,4}}\s+in\s+(?:the\s+sign\s+of\s+|the\s+sign\s+)?({_SIGN_PAT})\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p2_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    sign_num = _canon_sign(m.group(2))
    if not planet or not sign_num:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "sign": sign_num, "relation": "in_sign"}],
        "predicate": {"type": "planet_in_sign", "description": f"{planet} in sign {m.group(2)}"},
        "prediction": {"result": result, "domain": "sign_placement"},
        "pattern": "planet_in_sign",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 3: lord of the <ordinal> … in the <ordinal> … <result> ─────────

_P3 = re.compile(
    rf'\blord\s+of\s+(?:the\s+)?({_HOUSE_NUM_PAT})\b'
    rf'.{{0,40}}'
    rf'\bin\s+(?:the\s+)?({_HOUSE_NUM_PAT})\s+(?:house|bhava|Bhava|House)?\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p3_extract(m: re.Match, full_text: str) -> dict | None:
    from_house = _canon_house(m.group(1))
    to_house = _canon_house(m.group(2))
    if not from_house or not to_house:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"role": "lord", "from_house": from_house, "to_house": to_house, "relation": "lord_placement"}],
        "predicate": {"type": "lord_placement", "description": f"lord of {from_house} in house {to_house}"},
        "prediction": {"result": result, "domain": "lord_placement"},
        "pattern": "lord_placement",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 4: <planet> conjunct/with <planet> … <result> ───────────────────

_P4 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'\s+(?:conjunct(?:s|ed)?|and|with|associated\s+with|join(?:s|ed|ing)?|in\s+conjunction\s+with)\s+'
    rf'({_PLANET_PAT})\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p4_extract(m: re.Match, full_text: str) -> dict | None:
    p1 = _canon_planet(m.group(1))
    p2 = _canon_planet(m.group(2))
    if not p1 or not p2 or p1 == p2:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": p1, "relation": "conjunction"}, {"planet": p2, "relation": "conjunction"}],
        "predicate": {"type": "conjunction", "description": f"{p1} conjunct {p2}"},
        "prediction": {"result": result, "domain": "conjunction"},
        "pattern": "conjunction",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 5: <planet> aspect(s/ing/ed by) … <result> ─────────────────────

_P5 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'\s+(?:aspect(?:s|ing|ed\s+by)|aspected\s+by|lends?\s+(?:its\s+)?aspect\s+(?:to|on))\s+'
    rf'(?:the\s+)?(?:({_PLANET_PAT})|({_HOUSE_NUM_PAT})\s+(?:house|bhava)?)\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p5_extract(m: re.Match, full_text: str) -> dict | None:
    p1 = _canon_planet(m.group(1))
    if not p1:
        return None
    aspected_planet = _canon_planet(m.group(2)) if m.group(2) else None
    aspected_house = _canon_house(m.group(3)) if m.group(3) else None
    target_desc = aspected_planet or (f"house {aspected_house}" if aspected_house else "subject")
    result = _extract_result_clause(full_text, m.end())
    ant: list[dict] = [{"planet": p1, "relation": "aspects"}]
    if aspected_planet:
        ant.append({"planet": aspected_planet, "relation": "aspected"})
    if aspected_house:
        ant.append({"house": aspected_house, "relation": "aspected"})
    return {
        "antecedent": ant,
        "predicate": {"type": "aspect", "description": f"{p1} aspects {target_desc}"},
        "prediction": {"result": result, "domain": "aspect"},
        "pattern": "aspect",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 6: <planet> in exaltation/own sign/debilitation … <result> ──────

_P6 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,3}}\s+(?:in\s+)?'
    rf'(exaltation|own\s+(?:house|sign)|debilitation|debilitated|exalted|Moolatrikona|Swakshetra|neecha)\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p6_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    dignity = m.group(2).lower().strip()
    if not planet:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "dignity": dignity, "relation": "dignity_state"}],
        "predicate": {"type": "dignity_placement", "description": f"{planet} in {dignity}"},
        "prediction": {"result": result, "domain": "dignity"},
        "pattern": "dignity_placement",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 7: during <planet>'s (maha)?dasha … <result> ────────────────────

_P7 = re.compile(
    rf'(?:during|in|at\s+the\s+commencement\s+of)\s+'
    rf'(?:the\s+)?({_PLANET_PAT})\b(?:\'s|s)?\s+'
    rf'(?:maha)?dasha(?:\s+period)?\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p7_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    if not planet:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "relation": "dasha_lord"}],
        "predicate": {"type": "dasha_rule", "description": f"{planet} mahadasha period"},
        "prediction": {"result": result, "domain": "dasha_timing"},
        "pattern": "dasha_rule",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
        "dasha_system_id": "vimshottari",
    }


# ─── Pattern 8: when <planet> transits … <result> ────────────────────────────

_P8 = re.compile(
    rf'(?:when|if)\s+(?:the\s+)?({_PLANET_PAT})\b'
    rf'\s+(?:transit(?:s|ing|ed)?|passes?\s+through|moves?\s+through)\s+'
    rf'(?:the\s+)?(?:({_SIGN_PAT})|({_HOUSE_NUM_PAT})\s+(?:house|bhava)?)\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p8_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    if not planet:
        return None
    sign_num = _canon_sign(m.group(2)) if m.group(2) else None
    house_num = _canon_house(m.group(3)) if m.group(3) else None
    result = _extract_result_clause(full_text, m.end())
    ant: list[dict] = [{"planet": planet, "relation": "transits"}]
    if sign_num:
        ant.append({"sign": sign_num, "relation": "transit_target"})
    if house_num:
        ant.append({"house": house_num, "relation": "transit_target"})
    return {
        "antecedent": ant,
        "predicate": {"type": "transit_rule", "description": f"{planet} transits"},
        "prediction": {"result": result, "domain": "transit"},
        "pattern": "transit_rule",
        "match_text": m.group(0)[:120],
        "transit_marker": True,
    }


# ─── Pattern 9: <planet> in the <ordinal> from <planet/lagna> … <result> ─────

_P9 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'\s+in\s+(?:the\s+)?({_HOUSE_NUM_PAT})\s+'
    rf'from\s+(?:the\s+)?({_PLANET_PAT}|[Ll]agna|[Aa]scendant)\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p9_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    house = _canon_house(m.group(2))
    ref = m.group(3).lower().strip()
    if not planet or not house:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "house": house, "reference": ref, "relation": "house_from"}],
        "predicate": {"type": "house_from_reference", "description": f"{planet} in {house}th from {ref}"},
        "prediction": {"result": result, "domain": "house_from_reference"},
        "pattern": "house_from_reference",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 10: benefic/malefic aspect on <planet/house> … <result> ─────────

_P10 = re.compile(
    rf'\b(benefic|malefic)s?\s+(?:aspect(?:s|ing|ed)?|glance)\s+'
    rf'(?:on\s+|to\s+)?(?:the\s+)?(?:({_PLANET_PAT})|({_HOUSE_NUM_PAT})\s+(?:house|bhava)?)\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p10_extract(m: re.Match, full_text: str) -> dict | None:
    beneficence = m.group(1).lower()  # "benefic" or "malefic"
    target_planet = _canon_planet(m.group(2)) if m.group(2) else None
    target_house = _canon_house(m.group(3)) if m.group(3) else None
    if not target_planet and not target_house:
        return None
    result = _extract_result_clause(full_text, m.end())
    ant: list[dict] = [{"type": beneficence, "relation": "aspects"}]
    if target_planet:
        ant.append({"planet": target_planet, "relation": "aspected_by_" + beneficence})
    if target_house:
        ant.append({"house": target_house, "relation": "aspected_by_" + beneficence})
    return {
        "antecedent": ant,
        "predicate": {"type": "generic_aspect", "description": f"{beneficence} aspects"},
        "prediction": {"result": result, "domain": "aspect_effect"},
        "pattern": "benefic_malefic_aspect",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 11: <planet> hemmed between / kartari … <result> ────────────────

_P11 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,4}}\s+'
    rf'(?:hemmed\s+between|kartari|papa.kartari|shubha.kartari)'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p11_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    if not planet:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "relation": "kartari"}],
        "predicate": {"type": "kartari", "description": f"{planet} in kartari"},
        "prediction": {"result": result, "domain": "kartari_affliction"},
        "pattern": "kartari",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 12: <planet> retrograde … <result> ───────────────────────────────

_P12 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,4}}\s+'
    rf'(?:retrograde|vakra|in\s+retrograde\s+motion|is\s+retrograde)\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p12_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    if not planet:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "motion": "retrograde", "relation": "retrograde"}],
        "predicate": {"type": "retrograde", "description": f"{planet} retrograde"},
        "prediction": {"result": result, "domain": "planetary_motion"},
        "pattern": "retrograde",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 13: <planet> combust / in combustion … <result> ─────────────────

_P13 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,4}}\s+'
    rf'(?:combust(?:ion)?|astangata|asta|in\s+combustion|eclipsed\s+by\s+the\s+sun)\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p13_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    if not planet:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "state": "combust", "relation": "combustion"}],
        "predicate": {"type": "combustion", "description": f"{planet} combust"},
        "prediction": {"result": result, "domain": "combustion_effect"},
        "pattern": "combustion",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 14: <planet> in the <ordinal> house gives/causes (no intermediate clause) ──

_P14 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'\s+(?:posited|placed|situated|occupying|occupies|being)?\s*'
    rf'in\s+(?:the\s+)?({_HOUSE_NUM_PAT})\s+'
    rf'(?:house|bhava|Bhava|House|Bhav)\b'
    rf'\s*(?:,\s*|\s+)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p14_extract(m: re.Match, full_text: str) -> dict | None:
    # Alternative planet-in-house pattern (direct result word after house)
    planet = _canon_planet(m.group(1))
    house = _canon_house(m.group(2))
    if not planet or not house:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "house": house, "relation": "occupies"}],
        "predicate": {"type": "planet_in_house", "description": f"{planet} in house {house} (direct)"},
        "prediction": {"result": result, "domain": "house_signification"},
        "pattern": "planet_in_house_direct",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 15: If <planet> is in <sign/house> … one will/native will ────────
# Handles conditional form: "If the Moon is in Aries aspected by Mars, one will..."

_P15 = re.compile(
    rf'[Ii]f\s+(?:the\s+)?({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,6}}\s+'
    rf'(?:is\s+in\s+(?:the\s+)?)?(?:(?:the\s+)?({_HOUSE_NUM_PAT})\s+(?:house|bhava|House|Bhava)?|({_SIGN_PAT})\b)'
    rf'(?P<tail>.{{0,120}}?)'
    rf'(?:one\s+will|native\s+will|the\s+native\s+will|he\s+will|she\s+will|they\s+will)',
    FLAGS,
)


def _p15_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    house = _canon_house(m.group(2)) if m.group(2) else None
    sign_num = _canon_sign(m.group(3)) if m.group(3) else None
    if not planet:
        return None
    if not house and not sign_num:
        return None
    result = _extract_result_clause(full_text, m.end())
    ant: list[dict] = [{"planet": planet, "relation": "occupies"}]
    if house:
        ant[0]["house"] = house
    if sign_num:
        ant[0]["sign"] = sign_num
    loc_desc = f"house {house}" if house else f"sign {m.group(3)}"
    return {
        "antecedent": ant,
        "predicate": {"type": "conditional_placement", "description": f"if {planet} in {loc_desc}"},
        "prediction": {"result": result, "domain": "natal_effect"},
        "pattern": "conditional_if",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 16: <planet> aspected by <planet> … gives/results ───────────────
# "Moon in Navamsa of Mars aspected by Mars, one will win over enemies"

_P16 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,8}}\s+'
    rf'aspected\s+by\s+(?:the\s+)?({_PLANET_PAT})\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT}|one\s+will|native\s+will)',
    FLAGS,
)


def _p16_extract(m: re.Match, full_text: str) -> dict | None:
    subject = _canon_planet(m.group(1))
    aspector = _canon_planet(m.group(2))
    if not subject or not aspector or subject == aspector:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [
            {"planet": subject, "relation": "aspected"},
            {"planet": aspector, "relation": "aspecting"},
        ],
        "predicate": {"type": "aspected_by", "description": f"{subject} aspected by {aspector}"},
        "prediction": {"result": result, "domain": "aspect_effect"},
        "pattern": "aspected_by",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 17: Should <planet> be in <house/sign> … <result> ───────────────

_P17 = re.compile(
    rf'[Ss]hould\s+(?:the\s+)?({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,6}}\s+'
    rf'(?:be\s+in\s+|occupy\s+|be\s+posited\s+in\s+)?'
    rf'(?:(?:the\s+)?({_HOUSE_NUM_PAT})\s+(?:house|bhava|House|Bhava)?|({_SIGN_PAT})\b)'
    rf'(?P<tail>.{{0,120}}?)'
    rf'(?:{_RESULT_PAT}|one\s+will|native\s+will)',
    FLAGS,
)


def _p17_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    house = _canon_house(m.group(2)) if m.group(2) else None
    sign_num = _canon_sign(m.group(3)) if m.group(3) else None
    if not planet:
        return None
    if not house and not sign_num:
        return None
    result = _extract_result_clause(full_text, m.end())
    ant: list[dict] = [{"planet": planet, "relation": "occupies"}]
    if house:
        ant[0]["house"] = house
    if sign_num:
        ant[0]["sign"] = sign_num
    loc_desc = f"house {house}" if house else f"sign {m.group(3)}"
    return {
        "antecedent": ant,
        "predicate": {"type": "conditional_should", "description": f"should {planet} be in {loc_desc}"},
        "prediction": {"result": result, "domain": "natal_effect"},
        "pattern": "conditional_should",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 18: <planet> and <planet> in <house> … <result> ─────────────────

_P18 = re.compile(
    rf'\b({_PLANET_PAT})\b\s+and\s+({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,6}}\s+'
    rf'in\s+(?:the\s+)?({_HOUSE_NUM_PAT})\s+(?:house|bhava|House|Bhava)?\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p18_extract(m: re.Match, full_text: str) -> dict | None:
    p1 = _canon_planet(m.group(1))
    p2 = _canon_planet(m.group(2))
    house = _canon_house(m.group(3))
    if not p1 or not p2 or not house or p1 == p2:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [
            {"planet": p1, "house": house, "relation": "occupies"},
            {"planet": p2, "house": house, "relation": "occupies"},
        ],
        "predicate": {"type": "dual_planet_in_house", "description": f"{p1} and {p2} in house {house}"},
        "prediction": {"result": result, "domain": "combination_effect"},
        "pattern": "dual_planet_in_house",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 19: <planet> in <sign> in aspect to … <result> ──────────────────
# "Moon in Aries in aspect to Mars gives courage"

_P19 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,4}}\s+in\s+({_SIGN_PAT})\b'
    rf'(?:\s+\w+){{0,8}}\s+'
    rf'(?:in\s+aspect\s+(?:to|with)|aspected\s+by|aspecting)\s+'
    rf'(?:the\s+)?({_PLANET_PAT})\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT}|one\s+will|native\s+will)',
    FLAGS,
)


def _p19_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    sign_num = _canon_sign(m.group(2))
    aspector = _canon_planet(m.group(3))
    if not planet or not sign_num or not aspector:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [
            {"planet": planet, "sign": sign_num, "relation": "in_sign"},
            {"planet": aspector, "relation": "aspecting"},
        ],
        "predicate": {"type": "planet_in_sign_aspected", "description": f"{planet} in {m.group(2)} aspected by {aspector}"},
        "prediction": {"result": result, "domain": "sign_aspect_effect"},
        "pattern": "planet_in_sign_aspected",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 20: <planet> strong/weak … gives/bestows <result> ───────────────

_P20 = re.compile(
    rf'\b(?:strong|weak|powerful|strengthened|debilitated|exalted)\s+({_PLANET_PAT})\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT})',
    FLAGS,
)


def _p20_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    if not planet:
        return None
    # strength adjective is just before group 1 — extract it
    strength_word = m.group(0).split()[0].lower()
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "strength": strength_word, "relation": "strength_state"}],
        "predicate": {"type": "strength_state", "description": f"{strength_word} {planet}"},
        "prediction": {"result": result, "domain": "strength_effect"},
        "pattern": "strength_state",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 21: when/if <planet> is in <sign/house> … he/she/person will ────
# "When the Moon is in Dhanusat... he will have a very long face"
# "when Mars is in that bhava, the effect ... he will become odious"

_P21 = re.compile(
    rf'(?:[Ww]hen|[Ii]f)\s+(?:the\s+)?({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,8}}\s+'
    rf'(?:is\s+in\s+|be\s+in\s+|occupies?\s+|is\s+posited\s+in\s+)?'
    rf'(?:(?:the\s+)?({_HOUSE_NUM_PAT})\s+(?:house|bhava|bha[uv]a|bhav|Bhava|House)?|({_SIGN_PAT})\b|(?:that|the\s+said|the\s+same)\s+(?:house|bhava|sign|rasi|rashi)?\b)'
    rf'(?P<tail>.{{0,120}}?)'
    rf'(?:he\s+will|she\s+will|one\s+will|the\s+person\s+born\s+will|the\s+native\s+will|person\s+will|they\s+will)',
    FLAGS,
)


def _p21_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    house = _canon_house(m.group(2)) if m.group(2) else None
    sign_num = _canon_sign(m.group(3)) if m.group(3) else None
    if not planet:
        return None
    # Accept even if house/sign is vague (e.g. "that bhava") — predicate carries context
    result = _extract_result_clause(full_text, m.end())
    ant: list[dict] = [{"planet": planet, "relation": "occupies"}]
    if house:
        ant[0]["house"] = house
    if sign_num:
        ant[0]["sign"] = sign_num
    loc_desc = f"house {house}" if house else (f"sign {m.group(3)}" if sign_num else "bhava")
    return {
        "antecedent": ant,
        "predicate": {"type": "when_conditional", "description": f"when {planet} in {loc_desc}"},
        "prediction": {"result": result, "domain": "natal_effect"},
        "pattern": "conditional_when",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 22: <planet> in the <house/sign> … the person born will ──────────
# "if Jupiter be in the last bhava, the person born will be sceptical"

_P22 = re.compile(
    rf'({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,8}}\s+'
    rf'(?:(?:be\s+in|in|occupy|occupies?|be\s+posited\s+in)\s+)?'
    rf'(?:(?:the\s+)?({_HOUSE_NUM_PAT})\s+(?:house|bhava|bhav|bh\w*)?|({_SIGN_PAT})\b)'
    rf'(?P<tail>.{{0,120}}?)'
    rf'the\s+person\s+(?:born\s+)?will\b',
    FLAGS,
)


def _p22_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    house = _canon_house(m.group(2)) if m.group(2) else None
    sign_num = _canon_sign(m.group(3)) if m.group(3) else None
    if not planet:
        return None
    if not house and not sign_num:
        return None
    result = _extract_result_clause(full_text, m.end())
    ant: list[dict] = [{"planet": planet, "relation": "occupies"}]
    if house:
        ant[0]["house"] = house
    if sign_num:
        ant[0]["sign"] = sign_num
    loc_desc = f"house {house}" if house else f"sign {m.group(3)}"
    return {
        "antecedent": ant,
        "predicate": {"type": "person_born_will", "description": f"{planet} in {loc_desc} — person born will"},
        "prediction": {"result": result, "domain": "natal_effect"},
        "pattern": "person_born_will",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 23: <planet> in the <N>th bhava … gives/causes ─────────────────
# Variant: "bhava" spelling without "house"

_P23 = re.compile(
    rf'\b({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,6}}\s+'
    rf'(?:in\s+|occupying\s+|be\s+in\s+)?(?:the\s+)?({_HOUSE_NUM_PAT})\s+bhava\b'
    rf'(?P<tail>.{{0,100}}?)'
    rf'(?:{_RESULT_PAT}|one\s+will|native\s+will|he\s+will|she\s+will|the\s+person)',
    FLAGS,
)


def _p23_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    house = _canon_house(m.group(2))
    if not planet or not house:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "house": house, "relation": "occupies"}],
        "predicate": {"type": "planet_in_bhava", "description": f"{planet} in {house}th bhava"},
        "prediction": {"result": result, "domain": "house_signification"},
        "pattern": "planet_in_bhava",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ─── Pattern 24: when <planet> occupies <sign> … <result> ───────────────────
# "when the Moon occupies Dhanusat the person born will..."

_P24 = re.compile(
    rf'(?:[Ww]hen|[Ii]f)\s+(?:the\s+)?({_PLANET_PAT})\b'
    rf'(?:\s+\w+){{0,4}}\s+'
    rf'(?:occupy|occupies|occupying|is\s+in|be\s+in)\s+'
    rf'(?:the\s+)?(?:({_SIGN_PAT})\b|(?:a\s+)?({_SIGN_PAT})\s+(?:rasi|rashi|sign)?)',
    FLAGS,
)


def _p24_extract(m: re.Match, full_text: str) -> dict | None:
    planet = _canon_planet(m.group(1))
    sign_name = m.group(2) or m.group(3)
    sign_num = _canon_sign(sign_name) if sign_name else None
    if not planet or not sign_num:
        return None
    result = _extract_result_clause(full_text, m.end())
    return {
        "antecedent": [{"planet": planet, "sign": sign_num, "relation": "occupies"}],
        "predicate": {"type": "when_planet_in_sign", "description": f"when {planet} occupies {sign_name}"},
        "prediction": {"result": result, "domain": "sign_placement"},
        "pattern": "when_planet_in_sign",
        "match_text": m.group(0)[:120],
        "transit_marker": False,
    }


# ── Registered pattern list ────────────────────────────────────────────────────

PATTERNS: list[tuple[str, re.Pattern, Any]] = [
    ("planet_in_house",       _P1,  _p1_extract),
    ("planet_in_sign",        _P2,  _p2_extract),
    ("lord_placement",        _P3,  _p3_extract),
    ("conjunction",           _P4,  _p4_extract),
    ("aspect",                _P5,  _p5_extract),
    ("dignity_placement",     _P6,  _p6_extract),
    ("dasha_rule",            _P7,  _p7_extract),
    ("transit_rule",          _P8,  _p8_extract),
    ("house_from_reference",  _P9,  _p9_extract),
    ("benefic_malefic_aspect", _P10, _p10_extract),
    ("kartari",               _P11, _p11_extract),
    ("retrograde",            _P12, _p12_extract),
    ("combustion",            _P13, _p13_extract),
    ("planet_in_house_direct", _P14, _p14_extract),
    ("conditional_if",        _P15, _p15_extract),
    ("aspected_by",           _P16, _p16_extract),
    ("conditional_should",    _P17, _p17_extract),
    ("dual_planet_in_house",  _P18, _p18_extract),
    ("planet_in_sign_aspected", _P19, _p19_extract),
    ("strength_state",        _P20, _p20_extract),
    ("conditional_when",      _P21, _p21_extract),
    ("person_born_will",      _P22, _p22_extract),
    ("planet_in_bhava",       _P23, _p23_extract),
    ("when_planet_in_sign",   _P24, _p24_extract),
]


# ── Chunk extraction engine ────────────────────────────────────────────────────

def _normalize_ocr(text: str) -> str:
    """
    Normalize OCR-noisy text so that patterns can match across line breaks.

    Strategy:
    1. Split into lines; discard lines that are purely OCR garbage (Sanskrit
       glyphs, lone punctuation, or very short fragments < 4 chars).
    2. Join remaining lines with a single space — produces a flat paragraph
       that regex can scan linearly.
    3. Collapse runs of whitespace.

    This preserves all meaningful English sentences while stripping the
    Sanskrit transliteration noise that breaks multi-word regex patterns.
    """
    lines = text.split('\n')
    kept = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        # Discard very short lines (OCR artifacts, lone digits, lone glyphs)
        if len(s) < 4:
            continue
        # Discard lines that are >50% non-ASCII (Sanskrit/garbled OCR)
        non_ascii = sum(1 for c in s if ord(c) > 127)
        if non_ascii > len(s) * 0.5:
            continue
        # Discard lines that look like page numbers (short all-digit or mixed)
        if re.match(r'^\d[\d\s]*$', s) and len(s) < 6:
            continue
        kept.append(s)
    normalized = ' '.join(kept)
    # Collapse multiple spaces
    normalized = re.sub(r'\s{2,}', ' ', normalized)
    return normalized


def extract_rules_from_chunk(
    chunk: dict,
    valid_text_ids: set[str],
) -> Generator[dict, None, None]:
    """
    Run all patterns against a single chunk.
    Yields dicts ready for DB insertion (all columns of sutravali_rules).
    Each dict has a deterministic rule_id.
    """
    text_id = chunk["text_id"]
    verse_ref = chunk["verse_ref"]
    chunk_uuid = str(chunk["id"])
    raw_content = chunk["content_en"] or ""
    # Normalize OCR noise: collapse newlines, discard garbage lines
    content = _normalize_ocr(raw_content)
    text_id_valid = text_id in valid_text_ids

    # Deduplicate within a chunk: track (pattern, antecedent_key, prediction_key)
    seen_within_chunk: set[str] = set()

    for pat_name, pat_re, extract_fn in PATTERNS:
        for m in pat_re.finditer(content):
            try:
                result = extract_fn(m, content)
            except Exception as e:
                logger.debug("[rules] pattern %s match error: %s", pat_name, e)
                continue

            if result is None:
                continue

            antecedent = result["antecedent"]
            prediction = result["prediction"]

            # Within-chunk dedup key: use antecedent+prediction only (not pattern name)
            # so that two patterns producing the same antecedent+prediction → 1 rule
            dedup_key = f"{json.dumps(antecedent, sort_keys=True)}|{json.dumps(prediction, sort_keys=True)}"
            if dedup_key in seen_within_chunk:
                continue
            seen_within_chunk.add(dedup_key)

            quality = _score(antecedent, prediction, verse_ref, text_id_valid)

            if quality < QUALITY_THRESHOLD_REVIEW:
                continue  # reject entirely

            rule_id = _make_rule_id(text_id, verse_ref, antecedent, prediction)

            yield {
                "rule_id": str(rule_id),
                "text_id": text_id,
                "verse_ref": verse_ref,
                "antecedent_jsonb": json.dumps(antecedent),
                "predicate_jsonb": json.dumps(result["predicate"]),
                "prediction_jsonb": json.dumps(prediction),
                "confidence": quality,
                "extracted_by": EXTRACTED_BY,
                "extraction_pass_log": json.dumps([{
                    "pattern": result["pattern"],
                    "match_text": result["match_text"],
                    "chunk_id": chunk_uuid,
                }]),
                "quality_score": quality,
                "yoga_canonical_id": result.get("yoga_canonical_id"),
                "dasha_system_id": result.get("dasha_system_id"),
                "transit_marker": result.get("transit_marker", False),
                "_quality": quality,  # ephemeral — used by caller for routing
            }


# ── Main seed function ─────────────────────────────────────────────────────────

def seed_rules(
    conn: Any,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = True,
) -> dict[str, int]:
    """
    Extract rules from classical_text_chunks and insert into sutravali_rules.

    Returns:
        rows_inserted: rows inserted into sutravali_rules (quality ≥ 0.6)
        rows_skipped_conflict: ON CONFLICT DO NOTHING skips
        rows_below_threshold: quality 0.4–0.6 (logged, not inserted)
        rows_rejected: quality < 0.4 (rejected entirely)
        chunks_processed: total chunks iterated
        chunks_with_zero_extractions: coverage gap count
        upstream_chunks: total rows in classical_text_chunks
    """
    with conn.cursor() as cur:
        # Validate table exists
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='sutravali_rules'"
        )
        if cur.fetchone()[0] == 0:
            raise RuntimeError(
                "sutravali_rules table does not exist — apply migration 081 first."
            )

        # Validate upstream table exists
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='classical_text_chunks'"
        )
        if cur.fetchone()[0] == 0:
            raise RuntimeError(
                "classical_text_chunks table does not exist — bg_texts must run first."
            )

        # Load upstream chunks count
        cur.execute("SELECT COUNT(*) FROM classical_text_chunks")
        upstream_chunks = cur.fetchone()[0]

        if upstream_chunks == 0:
            logger.warning("[rules] classical_text_chunks is empty — 0 rules extracted")
            return {
                "rows_inserted": 0,
                "rows_skipped_conflict": 0,
                "rows_below_threshold": 0,
                "rows_rejected": 0,
                "chunks_processed": 0,
                "chunks_with_zero_extractions": 0,
                "upstream_chunks": 0,
            }

        # Load valid text_ids
        cur.execute("SELECT DISTINCT text_id FROM classical_text_chunks")
        valid_text_ids = {r[0] for r in cur.fetchall()}

        # Load valid dasha_system_ids for FK validation
        cur.execute("SELECT canonical_id FROM brahma_dasha_systems")
        valid_dasha_ids = {r[0] for r in cur.fetchall()}

        # Load valid yoga_canonical_ids for FK validation
        cur.execute("SELECT canonical_id FROM brahma_yoga_catalog")
        valid_yoga_ids = {r[0] for r in cur.fetchall()}

    if dry_run:
        logger.info(
            "[rules] dry_run — would process %d chunks from %d texts",
            upstream_chunks, len(valid_text_ids),
        )
        return {
            "rows_inserted": 0,
            "rows_skipped_conflict": 0,
            "rows_below_threshold": 0,
            "rows_rejected": 0,
            "chunks_processed": upstream_chunks,
            "chunks_with_zero_extractions": 0,
            "upstream_chunks": upstream_chunks,
        }

    now = datetime.now(timezone.utc)
    rows_inserted = 0
    rows_skipped_conflict = 0
    rows_below_threshold = 0
    rows_rejected = 0
    chunks_processed = 0
    chunks_with_zero_extractions = 0

    # Stream chunks in batches to avoid loading all 8k into memory at once
    BATCH_SIZE = 200

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, text_id, verse_ref, content_en "
            "FROM classical_text_chunks "
            "ORDER BY text_id, chapter, verse_start"
        )

        batch: list[dict] = []
        while True:
            rows = cur.fetchmany(BATCH_SIZE)
            if not rows:
                break
            batch = [
                {"id": r[0], "text_id": r[1], "verse_ref": r[2], "content_en": r[3]}
                for r in rows
            ]

            with conn.cursor() as insert_cur:
                for chunk in batch:
                    chunk_rule_count = 0
                    for rule_row in extract_rules_from_chunk(chunk, valid_text_ids):
                        quality = rule_row.pop("_quality")

                        # FK validation: dasha_system_id
                        dsi = rule_row.get("dasha_system_id")
                        if dsi and dsi not in valid_dasha_ids:
                            rule_row["dasha_system_id"] = None  # null; don't reject

                        # FK validation: yoga_canonical_id
                        yci = rule_row.get("yoga_canonical_id")
                        if yci and yci not in valid_yoga_ids:
                            rule_row["yoga_canonical_id"] = None

                        if quality < QUALITY_THRESHOLD_LIVE:
                            rows_below_threshold += 1
                            continue

                        # Insert into sutravali_rules
                        try:
                            insert_cur.execute(
                                """
                                INSERT INTO sutravali_rules (
                                    rule_id, text_id, verse_ref,
                                    antecedent_jsonb, predicate_jsonb, prediction_jsonb,
                                    confidence, extracted_by, extraction_pass_log,
                                    quality_score, yoga_canonical_id, dasha_system_id,
                                    transit_marker, created_at
                                ) VALUES (
                                    %s::uuid, %s, %s,
                                    %s::jsonb, %s::jsonb, %s::jsonb,
                                    %s, %s, %s::jsonb,
                                    %s, %s, %s,
                                    %s, %s
                                )
                                ON CONFLICT (rule_id) DO NOTHING
                                """,
                                (
                                    rule_row["rule_id"],
                                    rule_row["text_id"],
                                    rule_row["verse_ref"],
                                    rule_row["antecedent_jsonb"],
                                    rule_row["predicate_jsonb"],
                                    rule_row["prediction_jsonb"],
                                    rule_row["confidence"],
                                    rule_row["extracted_by"],
                                    rule_row["extraction_pass_log"],
                                    rule_row["quality_score"],
                                    rule_row["yoga_canonical_id"],
                                    rule_row["dasha_system_id"],
                                    rule_row["transit_marker"],
                                    now,
                                ),
                            )
                            if insert_cur.rowcount > 0:
                                rows_inserted += 1
                                chunk_rule_count += 1
                            else:
                                rows_skipped_conflict += 1
                        except Exception as e:
                            logger.warning("[rules] insert error chunk %s: %s", chunk["verse_ref"], e)
                            conn.rollback()
                            continue

                    chunks_processed += 1
                    if chunk_rule_count == 0:
                        chunks_with_zero_extractions += 1

                    if chunks_processed % 500 == 0:
                        logger.info(
                            "[rules] processed %d chunks → %d rules inserted so far",
                            chunks_processed, rows_inserted,
                        )

    logger.info(
        "[rules] DONE: inserted=%d skipped_conflict=%d below_threshold=%d "
        "chunks=%d zero_extraction=%d upstream=%d",
        rows_inserted, rows_skipped_conflict, rows_below_threshold,
        chunks_processed, chunks_with_zero_extractions, upstream_chunks,
    )

    # Coverage report
    coverage_pct = (chunks_processed - chunks_with_zero_extractions) / max(chunks_processed, 1) * 100
    logger.info(
        "[rules] Coverage: %.1f%% of chunks yielded ≥1 rule (%d / %d)",
        coverage_pct,
        chunks_processed - chunks_with_zero_extractions,
        chunks_processed,
    )

    if autocommit:
        conn.commit()

    return {
        "rows_inserted": rows_inserted,
        "rows_skipped_conflict": rows_skipped_conflict,
        "rows_below_threshold": rows_below_threshold,
        "rows_rejected": rows_rejected,
        "chunks_processed": chunks_processed,
        "chunks_with_zero_extractions": chunks_with_zero_extractions,
        "upstream_chunks": upstream_chunks,
    }
