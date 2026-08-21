"""
_grounding_engine.py — WS-2 L2 Bodha Grounding Engine
=======================================================

Matches each of the 569 MSR signals against the WS-3 rule corpus (~1,370 rules).
Produces grounding assignments with:
  - rule_id: best matching rule
  - grounding_status: GROUNDED | PARTIAL_MATCH | UNGROUNDED_NO_MATCH
  - source_school: parashari | jaimini | kp | tajaka | multi-school | nadi
  - verse_citation: source_verse.verse_ref from matched rule
  - match_confidence: 0.0–1.0
  - match_rationale: why this rule was chosen
  - caveats: the matched rule's own `caveats` field (provenance/attribution note), or None

Grounding Algorithm:
  For each signal, extract key terms:
    - graha names (Saturn, Moon, Sun, etc.)
    - bhava/house numbers
    - yoga names
    - signal_type → scope mapping
    - school from classical_source
  Search rule corpus:
    - scope match (primary filter)
    - keyword overlap (secondary filter)
  Score = scope_match(0.5) + school_match(0.2) + keyword_overlap(0.3)
  If score >= 0.35: GROUNDED (or PARTIAL_MATCH if 0.20–0.34)
  If score < 0.20: UNGROUNDED_NO_MATCH
"""
from __future__ import annotations

import logging
import re
import yaml
import glob
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

WS3_DIR = os.path.join(
    os.path.dirname(__file__),
    "../../../../00_ARCHITECTURE/CONDUCTOR/ws3/"
)

# Mapping signal_type → rule scope (primary lookup key)
SIGNAL_TYPE_TO_SCOPE: dict[str, list[str]] = {
    "yoga":                    ["yoga", "bhava", "graha"],
    "divisional-pattern":      ["divisional", "yoga", "bhava"],
    "dignity":                 ["graha", "bhava", "nakshatra"],
    "jaimini-pattern":         ["dasha", "misc", "bhava"],
    "convergence":             ["yoga", "bhava", "misc"],
    "sensitive-point":         ["bhava", "graha", "misc"],
    "transit-activation":      ["transit", "dasha"],
    "nakshatra-signature":     ["nakshatra", "graha", "bhava"],
    "dasha-activation":        ["dasha", "transit"],
    "panchang":                ["muhurta", "misc", "nakshatra"],
    "yogini-period":           ["dasha", "misc"],
    "tajika-pattern":          ["varshaphal", "dasha"],
    "tajika-yoga":             ["varshaphal"],
    "tajika-foundation":       ["varshaphal"],
    "tajika-sahama":           ["varshaphal"],
    "aspect":                  ["bhava", "graha", "yoga"],
    "kp-signature":            ["sub_lord", "nakshatra", "bhava"],
    "contradiction":           ["misc", "shadbala", "graha"],
    "house-strength":          ["bhava", "yoga"],
    "house-from-planet":       ["bhava", "misc"],
    "sequential-transit":      ["transit", "dasha"],
    "conjunction-placement":   ["bhava", "yoga", "graha"],
    "conjunction-career":      ["bhava", "yoga"],
    "structural":              ["misc", "bhava"],
    "transit-trigger":         ["transit"],
    "planetary-aspect":        ["graha", "bhava"],
    "placement-career":        ["bhava", "yoga"],
    "placement-spirituality":  ["bhava", "misc"],
    "multi-planet-combination":["yoga", "bhava"],
    "planetary-proximity":     ["graha", "bhava"],
    "conjunction-pattern":     ["yoga", "bhava"],
    "conjunction-environmental":["bhava", "misc"],
    "multi-placement-spiritual":["bhava", "misc"],
    "conjunction-psychological":["graha", "bhava"],
    "placement-psychological": ["graha", "bhava"],
    "placement-timing":        ["dasha", "transit"],
    "exchange-combination":    ["yoga", "bhava"],
    "transit-timing":          ["transit", "dasha"],
    "placement-longevity":     ["bhava", "misc"],
    "shadbala":                ["shadbala", "graha"],
}

# classical_source keywords → school
SOURCE_TO_SCHOOL: dict[str, str] = {
    "BPHS":         "parashari",
    "Parashar":     "parashari",
    "Phaladeepika": "parashari",
    "Saravali":     "parashari",
    "Brihat Jataka":"parashari",
    "Uttara Kalam": "parashari",
    "Jaimini":      "jaimini",
    "KP":           "kp",
    "Krishnamurti": "kp",
    "Tajak":        "tajaka",
    "Varsha":       "tajaka",
    "Solar Return": "tajaka",
    "Nadi":         "nadi",
    "BNN":          "nadi",
    "Chandra Kala": "nadi",
}

# Graha keywords for matching
GRAHA_KEYWORDS: dict[str, list[str]] = {
    "PLN.SUN":     ["sun", "surya", "ravi", "solarreturn"],
    "PLN.MOON":    ["moon", "chandra", "soma", "mind"],
    "PLN.MARS":    ["mars", "mangal", "kuja", "bhoomi"],
    "PLN.MERCURY": ["mercury", "budha", "budh"],
    "PLN.JUPITER": ["jupiter", "guru", "brihaspati"],
    "PLN.VENUS":   ["venus", "shukra", "sukra"],
    "PLN.SATURN":  ["saturn", "shani", "sani"],
    "PLN.RAHU":    ["rahu", "dragon", "north node", "shadow"],
    "PLN.KETU":    ["ketu", "south node", "moksha"],
}

# House keywords
HOUSE_KEYWORDS: dict[str, list[str]] = {
    f"HSE.{i}": [f"{i}h", f"house {i}", f"{i}st house", f"{i}nd house",
                 f"{i}rd house", f"{i}th house", f"bhava {i}", f"{i}bhava"]
    for i in range(1, 13)
}


# ── Rule Loading ────────────────────────────────────────────────────────────

def load_all_rules() -> list[dict[str, Any]]:
    """Load all rules from WS-3 corpus."""
    ws3_path = os.path.abspath(os.path.join(os.path.dirname(__file__), WS3_DIR))
    rule_files = sorted(glob.glob(os.path.join(ws3_path, "*.yaml")))
    rule_files = [f for f in rule_files
                  if "concordance" not in f
                  and "session_queue" not in f
                  and "bphs_batch_0" not in f]  # Skip old files, use canon batches

    all_rules: list[dict[str, Any]] = []

    for f in rule_files:
        if "bphs_pilot_rules" in f:
            # YAML parse error in this file — use regex extraction
            all_rules.extend(_load_pilot_rules_regex(f))
            continue
        try:
            with open(f) as fh:
                data = yaml.safe_load(fh)
            if data and "rules" in data:
                for r in data["rules"]:
                    if r:
                        all_rules.append(r)
        except Exception:
            # §N.8: a silent `pass` here drops the whole file's rules with no
            # trace — log loudly so a corpus YAML break is diagnosable instead
            # of surfacing only as a mysteriously-missing rule downstream.
            logger.error("load_all_rules: failed to parse rule file %s", f, exc_info=True)

    return all_rules


def _load_pilot_rules_regex(filepath: str) -> list[dict[str, Any]]:
    """Load bphs_pilot_rules.yaml via regex (has YAML parse error)."""
    with open(filepath) as f:
        content = f.read()

    rule_block_pattern = re.compile(
        r"  - rule_id:\s*(\S+)\n(.*?)(?=  - rule_id:|\Z)",
        re.DOTALL
    )

    def _get(text: str, key: str, default: str = "") -> str:
        m = re.search(r"^\s{4}" + re.escape(key) + r":\s*(.*)", text, re.MULTILINE)
        if not m:
            return default
        return m.group(1).strip().strip('"').strip("'")

    def _verse_ref(text: str) -> str:
        m = re.search(r"verse_ref:\s*[\"']?([^\"'\n]+)", text)
        return m.group(1).strip().strip('"').strip("'") if m else ""

    def _assertion(text: str) -> str:
        m = re.search(r"    assertion:\s*>\n((?:      .+\n?)+)", text)
        return m.group(1).strip() if m else ""

    def _condition(text: str) -> str:
        m = re.search(r"    condition:\s*>\n((?:      .+\n?)+)", text)
        return m.group(1).strip() if m else ""

    rules = []
    for match in rule_block_pattern.finditer(content):
        rule_id = match.group(1)
        body = match.group(2)
        scope = _get(body, "scope")
        school = _get(body, "school", "parashari")
        verse_ref = _verse_ref(body)
        assertion = _assertion(body)
        condition = _condition(body)
        try:
            conf_str = _get(body, "confidence")
            conf = float(conf_str) if conf_str else 0.7
        except ValueError:
            conf = 0.7

        rule = {
            "rule_id": rule_id,
            "scope": scope,
            "school": school,
            "source_verse": {"verse_ref": verse_ref},
            "assertion": assertion,
            "condition": condition,
            "confidence": conf,
        }
        rules.append(rule)

    return rules


# ── Grounding Logic ─────────────────────────────────────────────────────────

def _detect_school_from_source(classical_source: str) -> str:
    """Detect primary school from classical_source text."""
    src_lower = classical_source.lower()
    for keyword, school in SOURCE_TO_SCHOOL.items():
        if keyword.lower() in src_lower:
            return school
    return "parashari"


def _extract_keywords(signal: dict[str, Any]) -> set[str]:
    """Extract matching keywords from a signal."""
    keywords: set[str] = set()
    name = signal.get("signal_name", "").lower()
    sig_type = signal.get("signal_type", "").lower()
    classical = signal.get("classical_source", "").lower()
    entities = signal.get("entities_involved", [])
    domains = signal.get("domains_affected", [])

    # Add signal type terms
    for term in sig_type.replace("-", " ").split():
        keywords.add(term)

    # Add graha keywords from entities
    for entity in entities:
        if entity in GRAHA_KEYWORDS:
            keywords.update(GRAHA_KEYWORDS[entity])
        elif entity.startswith("HSE."):
            num = entity.replace("HSE.", "")
            keywords.add(f"{num}h")
            keywords.add(f"house{num}")
            keywords.add(f"bhava{num}")

    # Add domain terms
    for domain in domains:
        keywords.update(domain.lower().replace("_", " ").split())

    # Extract house numbers from name
    for m in re.finditer(r'\b(\d+)H\b', signal.get("signal_name", "")):
        h = m.group(1)
        keywords.add(f"{h}h")
        keywords.add(f"house{h}")

    # Add yoga/special terms from name
    name_words = re.sub(r'[^\w\s]', ' ', name).split()
    for w in name_words:
        if len(w) > 3:
            keywords.add(w)

    return keywords


def _rule_keywords(rule: dict[str, Any]) -> set[str]:
    """Extract keywords from a rule."""
    keywords: set[str] = set()
    scope = rule.get("scope", "").lower()
    school = rule.get("school", "").lower()
    rule_id = rule.get("rule_id", "").lower()
    assertion = str(rule.get("assertion", "")).lower()
    condition = str(rule.get("condition", "")).lower()
    verse_ref = ""
    sv = rule.get("source_verse")
    if isinstance(sv, dict):
        verse_ref = str(sv.get("verse_ref", "")).lower()

    keywords.add(scope)
    keywords.add(school)
    for w in re.sub(r'[^\w\s]', ' ', assertion).split():
        if len(w) > 3:
            keywords.add(w)
    for w in re.sub(r'[^\w\s]', ' ', condition).split():
        if len(w) > 3:
            keywords.add(w)

    # Graha keywords from rule_id
    for graha, graha_kw in GRAHA_KEYWORDS.items():
        for kw in graha_kw:
            if kw in rule_id:
                keywords.update(graha_kw)

    # House numbers from rule_id and text
    for m in re.finditer(r'[._](\d+)[hH]', rule_id + " " + verse_ref):
        h = m.group(1)
        keywords.add(f"{h}h")
        keywords.add(f"house{h}")

    return keywords


def score_match(signal: dict[str, Any], rule: dict[str, Any]) -> float:
    """Score how well a rule matches a signal. Returns 0.0–1.0."""
    sig_type = signal.get("signal_type", "")
    classical_source = signal.get("classical_source", "")
    signal_school = _detect_school_from_source(classical_source)

    rule_scope = rule.get("scope", "")
    rule_school = rule.get("school", "")

    # 1. Scope match (0–0.50)
    expected_scopes = SIGNAL_TYPE_TO_SCOPE.get(sig_type, ["misc"])
    scope_score = 0.0
    if rule_scope == expected_scopes[0]:
        scope_score = 0.50
    elif rule_scope in expected_scopes[1:]:
        scope_score = 0.30
    elif rule_scope in ["misc", "graha", "bhava"]:
        scope_score = 0.10

    # 2. School match (0–0.20)
    school_score = 0.0
    if signal_school == "nadi":
        # Nadi signals: BPHS is acceptable fallback
        if rule_school in ("parashari", "jaimini"):
            school_score = 0.10
    elif signal_school == rule_school:
        school_score = 0.20
    elif rule_school == "parashari" and signal_school in ("parashari", ""):
        school_score = 0.15

    # 3. Keyword overlap (0–0.30)
    sig_kw = _extract_keywords(signal)
    rule_kw = _rule_keywords(rule)
    if sig_kw and rule_kw:
        overlap = len(sig_kw & rule_kw)
        max_possible = min(len(sig_kw), 10)
        kw_score = min(0.30, (overlap / max(max_possible, 1)) * 0.30)
    else:
        kw_score = 0.0

    return scope_score + school_score + kw_score


def find_best_rule(
    signal: dict[str, Any],
    rules: list[dict[str, Any]],
    school_filter: Optional[str] = None,
) -> tuple[Optional[dict[str, Any]], float]:
    """Find best matching rule for a signal."""
    best_rule = None
    best_score = 0.0

    signal_school = _detect_school_from_source(signal.get("classical_source", ""))
    sig_type = signal.get("signal_type", "")

    # Pre-filter: prefer rules from detected school + correct scope
    preferred_scopes = SIGNAL_TYPE_TO_SCOPE.get(sig_type, ["misc"])

    # Score all rules
    for rule in rules:
        score = score_match(signal, rule)
        if score > best_score:
            best_score = score
            best_rule = rule

    return best_rule, best_score


def ground_signal(signal: dict[str, Any], rules: list[dict[str, Any]]) -> dict[str, Any]:
    """Ground a single signal against the rule corpus."""
    best_rule, score = find_best_rule(signal, rules)

    # Determine grounding status
    if score >= 0.35:
        grounding_status = "GROUNDED"
    elif score >= 0.20:
        grounding_status = "PARTIAL_MATCH"
    else:
        grounding_status = "UNGROUNDED_NO_MATCH"

    if best_rule is None or score < 0.20:
        return {
            "signal_id": signal["signal_id"],
            "rule_id": None,
            "grounding_status": "UNGROUNDED_NO_MATCH",
            "source_school": _detect_school_from_source(signal.get("classical_source", "")),
            "verse_citation": None,
            "match_confidence": 0.0,
            "match_rationale": "No rule in WS-3 corpus reached minimum score threshold (0.20)",
            "caveats": None,
        }

    # Extract verse reference
    sv = best_rule.get("source_verse")
    verse_citation = None
    if isinstance(sv, dict):
        verse_citation = sv.get("verse_ref")

    # Determine source school
    source_school = best_rule.get("school", "parashari")
    signal_school = _detect_school_from_source(signal.get("classical_source", ""))
    if signal_school != source_school and signal_school not in ("", "nadi"):
        source_school = f"{signal_school}+{source_school}"
        if "+" in source_school:
            # If multiple schools, note as multi-school
            parts = set(source_school.split("+"))
            if len(parts) > 1:
                source_school = "multi-school"

    return {
        "signal_id": signal["signal_id"],
        "rule_id": best_rule["rule_id"],
        "grounding_status": grounding_status,
        "source_school": source_school,
        "verse_citation": verse_citation,
        "match_confidence": round(score, 3),
        "match_rationale": (
            f"scope={best_rule.get('scope')} / school={best_rule.get('school')} / "
            f"score={score:.3f}"
        ),
        "caveats": best_rule.get("caveats"),
    }


# ── Public API ───────────────────────────────────────────────────────────────

_RULES_CACHE: Optional[list[dict[str, Any]]] = None


def get_rules() -> list[dict[str, Any]]:
    """Return cached rule corpus."""
    global _RULES_CACHE
    if _RULES_CACHE is None:
        _RULES_CACHE = load_all_rules()
    return _RULES_CACHE


def ground_signals(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ground a list of signals. Returns list of grounding assignments."""
    rules = get_rules()
    return [ground_signal(s, rules) for s in signals]
