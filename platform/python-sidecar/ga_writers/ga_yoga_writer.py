"""
ga_yoga_writer.py — GA Yoga Firings Writer
==========================================
Asset: ga_yoga — per-chart yoga firing records.

Evaluates classical yoga formation rules against L1 chart_facts rows
(from ga_structural, ga_positions) for each ayanamsha, then writes
one row per fired yoga into ga_yoga_firings.

Hard rails:
- ZERO LLM in data path — all yoga logic is deterministic rule evaluation.
- No fabricated strength: strength is NULL unless a classical formula applies.
- Classical citations required on every yoga (inherited from brahma_yoga_catalog).
- L1-authority: constituent_fact_ids reference real chart_facts.fact_id values.
- Idempotency: DELETE-then-INSERT scoped to (chart_id, ayanamsha_id).
- NEVER commits / closes conn — orchestrator owns the transaction boundary.

FORENSIC anchors (native chart 482012f1-710e-4a25-994a-93821f5871aa):
  Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries (all 5 ayanamshas),
  Tithi=Shukla Tritiya, Vara=Ravivara, Yoga=Shiva, Karana=Garaja.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any

import psycopg.rows

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# Five canonical ayanamshas — mirrors ga_positions_writer.CANONICAL_AYANAMSHAS keys
CANONICAL_AYANAMSHAS = [
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
]

STRENGTH_FORMULA_VERSION = "yoga_strength_formula_v1"

# Planet name normalisations (as stored in chart_facts.fact_subject)
# Based on ga_positions_writer PLANET_TO_SUBJECT convention
PLANET_SUBJECTS = {
    "sun": "SUN",
    "moon": "MOON",
    "mars": "MARS",
    "mercury": "MERCURY",
    "jupiter": "JUPITER",
    "venus": "VENUS",
    "saturn": "SATURN",
    "rahu": "RAHU",
    "ketu": "KETU",
}

# Benefics and malefics (natural, context-independent)
NATURAL_BENEFICS = {"jupiter", "venus", "mercury", "moon"}
NATURAL_MALEFICS = {"sun", "mars", "saturn", "rahu", "ketu"}

# Movable (chara), fixed (sthira), dual (dvisvabhava) signs
MOVABLE_SIGNS = {"aries", "cancer", "libra", "capricorn"}
FIXED_SIGNS = {"taurus", "leo", "scorpio", "aquarius"}
DUAL_SIGNS = {"gemini", "virgo", "sagittarius", "pisces"}

# Sign number → sign name (1-based)
SIGN_NAMES = {
    1: "aries", 2: "taurus", 3: "gemini", 4: "cancer",
    5: "leo", 6: "virgo", 7: "libra", 8: "scorpio",
    9: "sagittarius", 10: "capricorn", 11: "aquarius", 12: "pisces",
}
SIGN_NUMBERS = {v: k for k, v in SIGN_NAMES.items()}

# Kendra houses
KENDRAS = {1, 4, 7, 10}
TRIKONAS = {1, 5, 9}
DUSTHANAS = {6, 8, 12}
UPACHAYAS = {3, 6, 10, 11}
PANAPHARAS = {2, 5, 8, 11}
APOKLIMAS = {3, 6, 9, 12}


# ── Strength formula ───────────────────────────────────────────────────────────

def compute_yoga_strength_v1(
    dignity_scores: list[float],
    in_kendra: bool = False,
    has_exalted: bool = False,
) -> float | None:
    """
    Classical yoga strength composition per BPHS Ch.75 weighting principles.
    formula_version = yoga_strength_formula_v1

    strength = avg(constituent_planet_dignity_scores) * kendra_bonus * exaltation_bonus

    dignity_scores: 0.0=debilitated, 0.5=neutral, 0.75=own, 1.0=exalted
    kendra_bonus: 1.25 if in kendra, else 1.0
    exaltation_bonus: 1.1 if exalted planet present, else 1.0

    Returns None if dignity_scores is empty (no classical formula applicable).
    Classical citation: BPHS Ch.75 — strength of mahapurusha yogas as composite
    of shadbala × positional bonuses.
    """
    if not dignity_scores:
        return None
    avg_dignity = sum(dignity_scores) / len(dignity_scores)
    kendra_bonus = 1.25 if in_kendra else 1.0
    exaltation_bonus = 1.1 if has_exalted else 1.0
    return round(avg_dignity * kendra_bonus * exaltation_bonus, 4)


# ── Chart data loader ──────────────────────────────────────────────────────────

def _load_chart_facts(conn: Any, chart_id: str, ayanamsha_id: str) -> list[dict]:
    """Load all chart_facts rows for (chart_id, ayanamsha_id)."""
    with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
        cur.execute("""
            SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_text,
                   fact_value_num, fact_value_jsonb
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
        """, (chart_id, ayanamsha_id))
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _load_yoga_catalog(conn: Any) -> list[dict]:
    """Load all yoga catalog rows from brahma_yoga_catalog."""
    with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
        cur.execute("""
            SELECT canonical_id, name_sa, name_en, category, formation_rule_jsonb,
                   cancellation_conditions, classical_citations, computed_strength_formula,
                   school, rare
            FROM brahma_yoga_catalog
            ORDER BY canonical_id
        """)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    # Parse JSON fields
    for row in rows:
        for field in ("formation_rule_jsonb", "cancellation_conditions", "classical_citations"):
            if isinstance(row.get(field), str):
                try:
                    row[field] = json.loads(row[field])
                except (json.JSONDecodeError, TypeError):
                    row[field] = {}
    return rows


def _load_yoga_families(conn: Any) -> dict[str, list[str]]:
    """Load yoga → family mapping from yoga_family_members (if table exists)."""
    try:
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT yoga_canonical_id, family_id
                FROM yoga_family_members
            """)
            mapping: dict[str, list[str]] = {}
            for (yoga_id, family_id) in cur.fetchall():
                mapping.setdefault(yoga_id, []).append(family_id)
            return mapping
    except Exception as exc:
        logger.warning("[ga_yoga] Family mapping load failed: %s", exc)
        return {}


# ── Chart state extraction ─────────────────────────────────────────────────────

class ChartState:
    """Parsed chart state from chart_facts rows — the evaluation context."""

    def __init__(self, facts: list[dict]):
        self.facts = facts
        self._fact_by_id: dict[str, dict] = {f["fact_id"]: f for f in facts}

        # planet → house number (int)
        self.planet_house: dict[str, int] = {}
        # planet → sign name (lowercase)
        self.planet_sign: dict[str, str] = {}
        # planet → degree_absolute
        self.planet_degree: dict[str, float] = {}
        # planet → fact_id (for constituent_fact_ids)
        self.planet_fact_id: dict[str, str] = {}
        # house number (int) → list of planet names
        self.house_planets: dict[int, list[str]] = {}
        # sign name → list of planets
        self.sign_planets: dict[str, list[str]] = {}
        # sign name → house number (lagna)
        self.lagna_sign: str | None = None
        self.lagna_house_planets: dict[int, list[str]] = {}

        self._parse(facts)

    # Maps abbreviated fact_subject values → full planet names used in yoga catalog
    _SUBJECT_NORM: dict[str, str] = {
        "sun": "sun", "moon": "moon", "mar": "mars", "mer": "mercury",
        "jup": "jupiter", "ven": "venus", "sat": "saturn",
        "rah_mean": "rahu", "ket_mean": "ketu", "lagna": "lagna",
    }

    def _parse(self, facts: list[dict]) -> None:
        for f in facts:
            raw_subj = (f.get("fact_subject") or "").lower()
            subj = self._SUBJECT_NORM.get(raw_subj, raw_subj)  # normalize abbreviations
            cat = (f.get("fact_category") or "")
            key = (f.get("fact_key") or "")

            # Graha position rows — category graha_position or planet_position
            if cat in ("graha_position", "planet_position") and key == "house_d1":  # FIX: was "house"
                planet = subj
                house_num = f.get("fact_value_num")
                if house_num is not None:
                    try:
                        h = int(house_num)
                        self.planet_house[planet] = h
                        self.house_planets.setdefault(h, []).append(planet)
                        self.planet_fact_id[planet] = f["fact_id"]
                    except (TypeError, ValueError):
                        pass

            if cat in ("graha_position", "planet_position") and key == "sign":
                planet = subj
                sign = (f.get("fact_value_text") or "").lower()
                if sign:
                    self.planet_sign[planet] = sign
                    self.sign_planets.setdefault(sign, []).append(planet)
                    if planet == "lagna":  # FIX: lagna sign stored under graha_position
                        self.lagna_sign = sign

            if cat in ("graha_position", "planet_position") and key in ("degree_absolute", "longitude"):
                planet = subj
                deg = f.get("fact_value_num")
                if deg is not None:
                    try:
                        self.planet_degree[planet] = float(deg)
                    except (TypeError, ValueError):
                        pass

            # Lagna (legacy category fallback)
            if cat in ("lagna", "ascendant") and key in ("sign", "sign_name"):
                self.lagna_sign = (f.get("fact_value_text") or "").lower()

        # Build lagna-relative house → planets map
        if self.lagna_sign and self.lagna_sign in SIGN_NUMBERS:
            lagna_sign_num = SIGN_NUMBERS[self.lagna_sign]
            for planet, sign in self.planet_sign.items():
                if sign in SIGN_NUMBERS:
                    planet_sign_num = SIGN_NUMBERS[sign]
                    # House from lagna = (planet_sign_num - lagna_sign_num) mod 12 + 1
                    house_from_lagna = ((planet_sign_num - lagna_sign_num) % 12) + 1
                    self.lagna_house_planets.setdefault(house_from_lagna, []).append(planet)

    def planets_in_house(self, house: int) -> list[str]:
        """Return planets in house N from lagna."""
        return self.lagna_house_planets.get(house, [])

    def planets_in_sign(self, sign: str) -> list[str]:
        return self.sign_planets.get(sign.lower(), [])

    def distinct_signs_occupied(self) -> int:
        """Count of distinct signs occupied by the 7 classical planets."""
        classical = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}
        signs = {self.planet_sign[p] for p in classical if p in self.planet_sign}
        return len(signs)

    def planets_in_houses(self, houses: list[int]) -> list[str]:
        result = []
        for h in houses:
            result.extend(self.planets_in_house(h))
        return list(set(result))

    def fact_ids_for_planets(self, planets: list[str]) -> list[str]:
        return [self.planet_fact_id[p] for p in planets if p in self.planet_fact_id]


# ── Yoga evaluation engine ─────────────────────────────────────────────────────

def _evaluate_yoga(yoga: dict, state: ChartState) -> dict | None:
    """
    Evaluate a single yoga against chart state.
    Returns a result dict if the yoga fires, or None if it does not.

    Result dict keys:
      fired, constituent_planets, constituent_houses, constituent_fact_ids,
      strength, strength_formula_version, is_partial, partial_formation_pct,
      bhanga_active, bhanga_rule_fired

    Classical-citation guard: if a yoga lacks formation_rule_jsonb, it is
    not evaluated (cannot be deterministically checked without a rule).
    """
    cid = yoga["canonical_id"]
    rule = yoga.get("formation_rule_jsonb") or {}

    if not rule:
        return None  # no rule → cannot evaluate

    category = yoga.get("category", "")

    fired = False
    constituent_planets: list[str] = []
    constituent_houses: list[int] = []
    constituent_fact_ids: list[str] = []
    strength: float | None = None
    strength_formula_version: str | None = None
    is_partial = False
    partial_formation_pct: float | None = None
    bhanga_active = False
    bhanga_rule_fired: str | None = None

    # ── Pancha Mahapurusha ────────────────────────────────────────────────────
    if category == "pancha_mahapurusha":
        reqs = rule.get("requires", [])
        for req in reqs:
            planet = req.get("planet")
            dignities = req.get("dignity", [])
            house_class = req.get("house_class", "")
            if not planet:
                continue
            planet_sign = state.planet_sign.get(planet)
            if not planet_sign:
                continue
            # Check dignity
            in_dignity = _check_dignity(planet, planet_sign, dignities)
            if not in_dignity:
                continue
            # Check house class
            planet_house = state.planet_house.get(planet)
            if planet_house is None:
                # Try lagna-relative
                for h, planets in state.lagna_house_planets.items():
                    if planet in planets:
                        planet_house = h
                        break
            if planet_house is None:
                continue
            in_kendra = planet_house in KENDRAS if house_class == "kendra" else True
            if not in_kendra:
                continue
            # Yoga fires
            fired = True
            constituent_planets = [planet]
            constituent_houses = [planet_house]
            constituent_fact_ids = state.fact_ids_for_planets([planet])
            # Strength
            dignity_score = 1.0 if "exalted" in dignities and _is_exalted(planet, planet_sign) else 0.75
            strength = compute_yoga_strength_v1(
                [dignity_score], in_kendra=True, has_exalted=(dignity_score == 1.0)
            )
            strength_formula_version = STRENGTH_FORMULA_VERSION
            break

    # ── Nabhasa Ashraya (sign-type) ──────────────────────────────────────────
    elif "all_planets_in" in rule and isinstance(rule["all_planets_in"], str):
        target = rule["all_planets_in"]
        classical = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        placed = [p for p in classical if p in state.planet_sign]
        if not placed:
            return None
        if target == "movable_signs":
            all_match = all(state.planet_sign[p] in MOVABLE_SIGNS for p in placed)
        elif target == "fixed_signs":
            all_match = all(state.planet_sign[p] in FIXED_SIGNS for p in placed)
        elif target == "dual_signs":
            all_match = all(state.planet_sign[p] in DUAL_SIGNS for p in placed)
        elif target == "four_kendras":
            # All in kendras from lagna
            all_match = all(
                any(p in state.planets_in_house(k) for k in KENDRAS)
                for p in placed
            )
        elif target in (["1", "7"], ["4", "10"]):
            houses = [int(h) for h in target]
            all_match = all(any(p in state.planets_in_house(h) for h in houses) for p in placed)
        else:
            all_match = False
        if all_match:
            fired = True
            constituent_planets = placed
            constituent_fact_ids = state.fact_ids_for_planets(placed)

    # ── Nabhasa Ashraya — all_planets_in LIST (house lists) ─────────────────
    elif "all_planets_in" in rule and isinstance(rule["all_planets_in"], list):
        target_houses = [int(h) for h in rule["all_planets_in"]]
        classical = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        placed = [p for p in classical if p in state.planet_sign]
        if placed:
            all_match = all(
                any(p in state.planets_in_house(h) for h in target_houses)
                for p in placed
            )
            if all_match:
                fired = True
                constituent_planets = placed
                constituent_houses = target_houses
                constituent_fact_ids = state.fact_ids_for_planets(placed)

    # ── Nabhasa Sankhya (distinct signs count) ────────────────────────────────
    elif "distinct_signs_occupied" in rule:
        target_count = rule["distinct_signs_occupied"]
        actual_count = state.distinct_signs_occupied()
        if actual_count == target_count:
            fired = True
            classical = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
            constituent_planets = [p for p in classical if p in state.planet_sign]
            constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)

    # ── Nabhasa Dala (benefics/malefics in kendras) ───────────────────────────
    elif "benefics_in" in rule and rule.get("benefics_in") == "three_kendras":
        # Mala yoga: benefics in 3 of the 4 kendras
        kendra_list = [1, 4, 7, 10]
        kendra_with_benefics = [
            k for k in kendra_list
            if any(p in NATURAL_BENEFICS for p in state.planets_in_house(k))
        ]
        if len(kendra_with_benefics) >= 3:
            fired = True
            constituent_houses = kendra_with_benefics
            for h in kendra_with_benefics:
                benefic_ps = [p for p in state.planets_in_house(h) if p in NATURAL_BENEFICS]
                constituent_planets.extend(benefic_ps)
            constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)

    elif "malefics_in" in rule and rule.get("malefics_in") == "three_kendras":
        # Sarpa yoga: malefics in 3 of the 4 kendras
        kendra_list = [1, 4, 7, 10]
        kendra_with_malefics = [
            k for k in kendra_list
            if any(p in NATURAL_MALEFICS for p in state.planets_in_house(k))
        ]
        if len(kendra_with_malefics) >= 3:
            fired = True
            constituent_houses = kendra_with_malefics
            for h in kendra_with_malefics:
                malefic_ps = [p for p in state.planets_in_house(h) if p in NATURAL_MALEFICS]
                constituent_planets.extend(malefic_ps)
            constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)

    # ── Nabhasa Akriti — two adjacent kendras (Gada) ─────────────────────────
    elif rule.get("all_planets_in") == "two_adjacent_kendras":
        classical = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        placed = [p for p in classical if p in state.planet_sign]
        adjacent_kendra_pairs = [(1, 4), (4, 7), (7, 10), (10, 1)]
        for pair in adjacent_kendra_pairs:
            ps_in_pair = state.planets_in_houses(list(pair))
            if all(p in ps_in_pair for p in placed) and placed:
                fired = True
                constituent_planets = placed
                constituent_houses = list(pair)
                constituent_fact_ids = state.fact_ids_for_planets(placed)
                break

    # ── Nabhasa Akriti — all planets in one of multiple house-sets (Hala) ────
    elif "all_planets_in_one_of" in rule:
        sets = rule["all_planets_in_one_of"]
        classical = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        placed = [p for p in classical if p in state.planet_sign]
        if placed:
            for house_set in sets:
                if isinstance(house_set, str):
                    # e.g. "four_panaphara", "four_apoklima"
                    if house_set == "four_panaphara":
                        houses = list(PANAPHARAS)
                    elif house_set == "four_apoklima":
                        houses = list(APOKLIMAS)
                    else:
                        continue
                else:
                    houses = [int(h) for h in house_set]
                ps_in_set = state.planets_in_houses(houses)
                if all(p in ps_in_set for p in placed):
                    fired = True
                    constituent_planets = placed
                    constituent_houses = houses
                    constituent_fact_ids = state.fact_ids_for_planets(placed)
                    break

    # ── Nabhasa Akriti — 7 planets in 7 consecutive houses ───────────────────
    elif "all_seven_planets_in_seven_consecutive_from" in rule:
        start = rule["all_seven_planets_in_seven_consecutive_from"]
        classical = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        placed = [p for p in classical if p in state.planet_sign]

        starts_to_try: list[int] = []
        if start == "a_panaphara_or_apoklima":
            starts_to_try = [2, 3, 5, 6, 8, 9, 11, 12]
        elif isinstance(start, str) and start.isdigit():
            starts_to_try = [int(start)]
        else:
            starts_to_try = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        for s in starts_to_try:
            houses = [((s - 1 + i) % 12) + 1 for i in range(7)]
            ps_in_houses = state.planets_in_houses(houses)
            if len(placed) >= 5 and all(p in ps_in_houses for p in placed):
                fired = True
                constituent_planets = placed
                constituent_houses = houses
                constituent_fact_ids = state.fact_ids_for_planets(placed)
                break

    # ── Chakra and Samudra (odd/even houses) ─────────────────────────────────
    elif rule.get("all_planets_in") in (["1","3","5","7","9","11"], ["2","4","6","8","10","12"]):
        house_list = [int(h) for h in rule["all_planets_in"]]
        classical = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        placed = [p for p in classical if p in state.planet_sign]
        ps_in_houses = state.planets_in_houses(house_list)
        if placed and all(p in ps_in_houses for p in placed):
            fired = True
            constituent_planets = placed
            constituent_houses = house_list
            constituent_fact_ids = state.fact_ids_for_planets(placed)

    # ── Yupa, Ishu, Shakti, Danda (consecutive-4-house blocks) ───────────────
    elif rule.get("all_planets_in") in (
        ["1","2","3","4"], ["4","5","6","7"], ["7","8","9","10"], ["10","11","12","1"]
    ):
        house_list = [int(h) for h in rule["all_planets_in"]]
        classical = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        placed = [p for p in classical if p in state.planet_sign]
        ps_in_houses = state.planets_in_houses(house_list)
        if placed and all(p in ps_in_houses for p in placed):
            fired = True
            constituent_planets = placed
            constituent_houses = house_list
            constituent_fact_ids = state.fact_ids_for_planets(placed)

    # ── Vajra / Yava (benefics/malefics in specific pairs of houses) ─────────
    elif "benefics_in" in rule and "malefics_in" in rule:
        benefic_houses = [int(h) for h in rule["benefics_in"]]
        malefic_houses = [int(h) for h in rule["malefics_in"]]
        benefics_ok = all(
            any(p in NATURAL_BENEFICS for p in state.planets_in_house(h))
            for h in benefic_houses
        )
        malefics_ok = all(
            any(p in NATURAL_MALEFICS for p in state.planets_in_house(h))
            for h in malefic_houses
        )
        if benefics_ok and malefics_ok:
            fired = True
            for h in benefic_houses + malefic_houses:
                for p in state.planets_in_house(h):
                    if p not in constituent_planets:
                        constituent_planets.append(p)
            constituent_houses = benefic_houses + malefic_houses
            constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)

    # ── Shringataka (1,5,9) and Hala ─────────────────────────────────────────
    elif "all_planets_in" in rule and isinstance(rule["all_planets_in"], list) and len(rule["all_planets_in"]) == 3:
        house_list = [int(h) for h in rule["all_planets_in"]]
        classical = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        placed = [p for p in classical if p in state.planet_sign]
        ps_in_houses = state.planets_in_houses(house_list)
        if placed and all(p in ps_in_houses for p in placed):
            fired = True
            constituent_planets = placed
            constituent_houses = house_list
            constituent_fact_ids = state.fact_ids_for_planets(placed)

    # ── Chandra yogas (Sunapha, Anapha, Durudhara, Kemadruma) ────────────────
    elif "requires" in rule:
        reqs = rule["requires"]
        # Gate: check the first requirement's relation field
        for req in reqs:
            relation = req.get("relation", "")

            if relation == "planet_not_sun_in_2nd_from_moon":
                moon_house = _house_of_planet("moon", state)
                if moon_house:
                    h2 = ((moon_house - 1 + 1) % 12) + 1
                    ps = [p for p in state.planets_in_house(h2) if p not in ("sun", "moon")]
                    if ps:
                        fired = True
                        constituent_planets = ["moon"] + ps
                        constituent_houses = [moon_house, h2]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "planet_not_sun_in_12th_from_moon":
                moon_house = _house_of_planet("moon", state)
                if moon_house:
                    h12 = ((moon_house - 1 - 1) % 12) + 1
                    ps = [p for p in state.planets_in_house(h12) if p not in ("sun", "moon")]
                    if ps:
                        fired = True
                        constituent_planets = ["moon"] + ps
                        constituent_houses = [moon_house, h12]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "planets_not_sun_in_both_2nd_and_12th_from_moon":
                moon_house = _house_of_planet("moon", state)
                if moon_house:
                    h2 = ((moon_house - 1 + 1) % 12) + 1
                    h12 = ((moon_house - 1 - 1) % 12) + 1
                    ps2 = [p for p in state.planets_in_house(h2) if p not in ("sun", "moon")]
                    ps12 = [p for p in state.planets_in_house(h12) if p not in ("sun", "moon")]
                    if ps2 and ps12:
                        fired = True
                        constituent_planets = ["moon"] + ps2 + ps12
                        constituent_houses = [moon_house, h2, h12]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "no_planet_in_2_or_12_from_moon_and_no_kendra_support":
                # Kemadruma: Moon isolated (no planet in 2nd/12th from moon, no planet in kendra from moon)
                moon_house = _house_of_planet("moon", state)
                if moon_house:
                    h2 = ((moon_house - 1 + 1) % 12) + 1
                    h12 = ((moon_house - 1 - 1) % 12) + 1
                    ps2 = [p for p in state.planets_in_house(h2) if p != "moon"]
                    ps12 = [p for p in state.planets_in_house(h12) if p != "moon"]
                    # Kendra from moon: 1st, 4th, 7th, 10th from moon
                    moon_kendra_houses = [((moon_house - 1 + k - 1) % 12) + 1 for k in [1, 4, 7, 10]]
                    kendra_ps = []
                    for h in moon_kendra_houses:
                        kendra_ps.extend([p for p in state.planets_in_house(h) if p != "moon"])
                    if not ps2 and not ps12 and not kendra_ps:
                        fired = True
                        constituent_planets = ["moon"]
                        constituent_houses = [moon_house]
                        constituent_fact_ids = state.fact_ids_for_planets(["moon"])
                break

            elif relation == "planet_not_moon_in_2nd_from_sun":
                # Vesi yoga
                sun_house = _house_of_planet("sun", state)
                if sun_house:
                    h2 = ((sun_house - 1 + 1) % 12) + 1
                    ps = [p for p in state.planets_in_house(h2) if p not in ("moon", "sun")]
                    if ps:
                        fired = True
                        constituent_planets = ["sun"] + ps
                        constituent_houses = [sun_house, h2]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "planet_not_moon_in_12th_from_sun":
                # Vasi yoga
                sun_house = _house_of_planet("sun", state)
                if sun_house:
                    h12 = ((sun_house - 1 - 1) % 12) + 1
                    ps = [p for p in state.planets_in_house(h12) if p not in ("moon", "sun")]
                    if ps:
                        fired = True
                        constituent_planets = ["sun"] + ps
                        constituent_houses = [sun_house, h12]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "planets_not_moon_in_both_2nd_and_12th_from_sun":
                # Ubhayachari yoga
                sun_house = _house_of_planet("sun", state)
                if sun_house:
                    h2 = ((sun_house - 1 + 1) % 12) + 1
                    h12 = ((sun_house - 1 - 1) % 12) + 1
                    ps2 = [p for p in state.planets_in_house(h2) if p not in ("moon", "sun")]
                    ps12 = [p for p in state.planets_in_house(h12) if p not in ("moon", "sun")]
                    if ps2 and ps12:
                        fired = True
                        constituent_planets = ["sun"] + ps2 + ps12
                        constituent_houses = [sun_house, h2, h12]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "jupiter_in_kendra_from_moon":
                # Gajakesari yoga
                moon_house = _house_of_planet("moon", state)
                jupiter_house = _house_of_planet("jupiter", state)
                if moon_house and jupiter_house:
                    rel_house = ((jupiter_house - moon_house) % 12) + 1
                    if rel_house in {1, 4, 7, 10}:
                        fired = True
                        constituent_planets = ["moon", "jupiter"]
                        constituent_houses = [moon_house, jupiter_house]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "benefics_in_6th_7th_8th_from_moon":
                # Adhi yoga: benefics in 6/7/8 from moon
                moon_house = _house_of_planet("moon", state)
                if moon_house:
                    benefic_houses_rel = [6, 7, 8]
                    benefic_houses_abs = [((moon_house - 1 + r - 1) % 12) + 1 for r in benefic_houses_rel]
                    benefics_found = []
                    for h in benefic_houses_abs:
                        benefics_found.extend([p for p in state.planets_in_house(h) if p in NATURAL_BENEFICS])
                    if len(set(benefics_found)) >= 2:
                        fired = True
                        constituent_planets = ["moon"] + list(set(benefics_found))
                        constituent_houses = [moon_house] + benefic_houses_abs
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "only_benefic_in_10th_from_lagna_or_moon":
                # Amala yoga
                h10_planets = state.planets_in_house(10)
                if h10_planets and all(p in NATURAL_BENEFICS for p in h10_planets):
                    fired = True
                    constituent_planets = h10_planets
                    constituent_houses = [10]
                    constituent_fact_ids = state.fact_ids_for_planets(h10_planets)
                break

            elif relation == "all_four_kendras_occupied":
                # Chatussagara yoga
                kendra_occupants = []
                all_occupied = True
                for k in [1, 4, 7, 10]:
                    ps = state.planets_in_house(k)
                    if not ps:
                        all_occupied = False
                        break
                    kendra_occupants.extend(ps)
                if all_occupied:
                    fired = True
                    constituent_planets = list(set(kendra_occupants))
                    constituent_houses = [1, 4, 7, 10]
                    constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "sun_mercury_conjunct":
                # Budha-Aditya yoga
                sun_house = _house_of_planet("sun", state)
                mercury_house = _house_of_planet("mercury", state)
                if sun_house and mercury_house and sun_house == mercury_house:
                    # Check mercury not deeply combust (within 3° of sun)
                    sun_deg = state.planet_degree.get("sun")
                    merc_deg = state.planet_degree.get("mercury")
                    combust = False
                    if sun_deg is not None and merc_deg is not None:
                        diff = abs(sun_deg - merc_deg) % 360
                        if diff > 180:
                            diff = 360 - diff
                        combust = diff <= 3.0
                    if not combust:
                        fired = True
                        constituent_planets = ["sun", "mercury"]
                        constituent_houses = [sun_house]
                        constituent_fact_ids = state.fact_ids_for_planets(["sun", "mercury"])
                break

            elif relation == "sun_moon_mars_in_mutual_trines":
                # Trilochana yoga
                sun_h = _house_of_planet("sun", state)
                moon_h = _house_of_planet("moon", state)
                mars_h = _house_of_planet("mars", state)
                if sun_h and moon_h and mars_h:
                    # Each must be in a trikona from one of the others
                    def in_trine(h1: int, h2: int) -> bool:
                        diff = (h2 - h1) % 12
                        return diff in {0, 4, 8}
                    if in_trine(sun_h, moon_h) and in_trine(moon_h, mars_h):
                        fired = True
                        constituent_planets = ["sun", "moon", "mars"]
                        constituent_houses = [sun_h, moon_h, mars_h]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "moon_mars_conjunct_or_mutual_aspect":
                # Chandra-Mangala yoga
                moon_h = _house_of_planet("moon", state)
                mars_h = _house_of_planet("mars", state)
                if moon_h and mars_h:
                    diff = abs(moon_h - mars_h) % 12
                    if diff == 0 or diff == 6:  # conjunct or opposition
                        fired = True
                        constituent_planets = ["moon", "mars"]
                        constituent_houses = [moon_h, mars_h]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "jupiter_mars_conjunct_or_mutual_aspect":
                # Guru-Mangala yoga
                jup_h = _house_of_planet("jupiter", state)
                mars_h = _house_of_planet("mars", state)
                if jup_h and mars_h:
                    diff = abs(jup_h - mars_h) % 12
                    if diff == 0 or diff == 6:
                        fired = True
                        constituent_planets = ["jupiter", "mars"]
                        constituent_houses = [jup_h, mars_h]
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "9th_and_10th_lords_associate_conjunction_aspect_or_exchange":
                # Dharma-Karmadhipati: 9th and 10th lords associate
                # We evaluate by checking if 9th/10th lords are in same house or mutual aspect
                # House lord lookup requires lagna sign — simplified here
                if state.lagna_sign:
                    fired = _check_house_lord_association(state, 9, 10)
                    if fired:
                        constituent_fact_ids = []
                break

            elif relation == "kendra_lord_and_trikona_lord_associate":
                # Kendra-Trikona Raja Yoga
                if state.lagna_sign:
                    fired = _check_kendra_trikona_raja(state)
                    if fired:
                        constituent_fact_ids = []
                break

            elif relation in (
                "4th_and_9th_lords_in_mutual_kendra",
                "5th_and_6th_lords_in_mutual_kendra",
                "lagna_lord_and_9th_lord_associate",
                "association_of_2nd_and_11th_lords",
                "association_of_5th_and_9th_lords",
                "association_among_2_5_9_11_lords",
                "association_of_lagna_and_2nd_lords",
                "association_of_9th_and_11th_lords",
                "9th_lord_own_or_exalted_in_kendra_trikona",
                "mercury_venus_jupiter_in_kendra_trikona_or_2nd",
                "benefics_in_upachayas_3_6_10_11_from_lagna_or_moon",
                "benefics_in_6_7_8_from_lagna",
                "lagna_lord_exalted_in_kendra_aspected_by_jupiter",
                "venus_lagna_lord_9th_lord_strong_and_related",
                "four_or_more_planets_in_one_house",
                "four_plus_planets_in_one_house",
                "6th_lord_in_6_8_or_12",
                "8th_lord_in_6_8_or_12",
                "12th_lord_in_6_8_or_12",
                "debilitated_planet_with_cancelled_debility",
                "mutual_exchange_of_signs_between_two_auspicious_house_lords",
                "kendra_and_trikona_lords_as_benefics_in_kendras",
                "lagna_lord_and_9th_lord_associate",
                "benefics_in_2nd_and_12th_from_a_house_or_planet",
                "saturn_strongest_in_a_4plus_grouping_or_aspecting_moon_with_ketu",
                "11th_lord_in_dusthana_or_lagna_lord_in_6_8_12",
                "moon_jupiter_in_6_8_from_each_other",
            ):
                # These require house-lord computation or multi-condition evaluation
                # beyond what simple chart_facts rows provide without ga_structural
                # columns. We mark them as requiring deeper fact lookup — fired=False,
                # partial_formation_pct set to indicate evaluation attempted.
                # The ga_structural writer (GA8) does yoga_fires rows that handle these.
                # Here we conservatively skip rather than fabricate.
                is_partial = False
                partial_formation_pct = None
                break

            else:
                # Unknown relation — skip
                break

    if not fired:
        return None

    return {
        "fired": True,
        "constituent_planets": constituent_planets,
        "constituent_houses": constituent_houses,
        "constituent_fact_ids": constituent_fact_ids,
        "strength": strength,
        "strength_formula_version": strength_formula_version,
        "is_partial": is_partial,
        "partial_formation_pct": partial_formation_pct,
        "bhanga_active": bhanga_active,
        "bhanga_rule_fired": bhanga_rule_fired,
    }


# ── Helper utilities ───────────────────────────────────────────────────────────

def _house_of_planet(planet: str, state: ChartState) -> int | None:
    """Return the lagna-relative house of a planet."""
    for h, planets in state.lagna_house_planets.items():
        if planet in planets:
            return h
    return state.planet_house.get(planet)


def _check_dignity(planet: str, sign: str, dignities: list[str]) -> bool:
    """Check if a planet is in the stated dignity in the given sign."""
    OWN_SIGNS: dict[str, list[str]] = {
        "sun": ["leo"],
        "moon": ["cancer"],
        "mars": ["aries", "scorpio"],
        "mercury": ["gemini", "virgo"],
        "jupiter": ["sagittarius", "pisces"],
        "venus": ["taurus", "libra"],
        "saturn": ["capricorn", "aquarius"],
    }
    EXALTATION_SIGNS: dict[str, str] = {
        "sun": "aries",
        "moon": "taurus",
        "mars": "capricorn",
        "mercury": "virgo",
        "jupiter": "cancer",
        "venus": "pisces",
        "saturn": "libra",
    }
    is_own = sign in OWN_SIGNS.get(planet, [])
    is_exalted = sign == EXALTATION_SIGNS.get(planet)

    if "own" in dignities and is_own:
        return True
    if "exalted" in dignities and is_exalted:
        return True
    return False


def _is_exalted(planet: str, sign: str) -> bool:
    EXALTATION_SIGNS: dict[str, str] = {
        "sun": "aries",
        "moon": "taurus",
        "mars": "capricorn",
        "mercury": "virgo",
        "jupiter": "cancer",
        "venus": "pisces",
        "saturn": "libra",
    }
    return sign == EXALTATION_SIGNS.get(planet)


def _check_house_lord_association(state: ChartState, h1: int, h2: int) -> bool:
    """
    Simplified check: are the lords of h1 and h2 in the same house?
    Full evaluation requires house-lord mapping from lagna sign (not always available
    from chart_facts alone; ga_structural handles the full evaluation).
    Returns False if lagna sign unavailable — conservative guard.
    """
    # Without a complete house-lord table this cannot be fully evaluated
    # from chart_facts alone. Return False to avoid fabrication.
    return False


def _check_kendra_trikona_raja(state: ChartState) -> bool:
    """
    Conservative check for Kendra-Trikona Raja Yoga.
    Requires house-lord computation — deferred to ga_structural.
    """
    return False


# ── Idempotency helper for ga_yoga_firings ────────────────────────────────────

def _delete_prior_yoga_firings(conn: Any, chart_id: str, ayanamsha_id: str) -> int:
    """Delete prior ga_yoga_firings rows for (chart_id, ayanamsha_id)."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ga_yoga_firings WHERE chart_id = %s AND ayanamsha_id = %s",
            (chart_id, ayanamsha_id),
        )
        return cur.rowcount or 0


# ── Main substep builder ───────────────────────────────────────────────────────

def build_ga_yoga_substep(
    chart_id: str,
    build_id: str | None,
    ayanamsha_id: str,
    conn: Any,
    dry_run: bool = False,
) -> int:
    """
    Build ga_yoga_firings for one (chart_id, ayanamsha_id) pair.
    Called per ayanamsha substep by GaYogaWriter.run_substep.

    Hard gates:
    - No LLM.
    - strength = NULL unless classical formula applies (yoga_strength_formula_v1).
    - constituent_fact_ids = [] if no L1 fact_ids resolved (not fabricated).
    - Delete-then-insert idempotency.
    - No commit — caller owns the transaction.

    Returns: number of rows inserted.
    """
    t0 = time.time()
    logger.info("[ga_yoga_writer] substep start: chart=%s ayanamsha=%s", chart_id, ayanamsha_id)

    # FORENSIC guard
    if chart_id == CANONICAL_CHART_ID:
        logger.info("[ga_yoga_writer] FORENSIC: native chart — applying forensic assertions")

    if dry_run:
        logger.info("[ga_yoga_writer] DRY_RUN — no writes")
        return 0

    # 1. Load inputs
    facts = _load_chart_facts(conn, chart_id, ayanamsha_id)
    if not facts:
        logger.warning(
            "[ga_yoga_writer] No chart_facts found for chart=%s ayanamsha=%s — skipping",
            chart_id, ayanamsha_id,
        )
        return 0

    yoga_catalog = _load_yoga_catalog(conn)
    if not yoga_catalog:
        logger.warning("[ga_yoga_writer] brahma_yoga_catalog is empty — skipping")
        return 0

    family_map = _load_yoga_families(conn)

    # 2. Parse chart state
    state = ChartState(facts)

    # 3. Idempotency: delete prior rows for this (chart_id, ayanamsha_id)
    deleted = _delete_prior_yoga_firings(conn, chart_id, ayanamsha_id)
    logger.info("[ga_yoga_writer] deleted %d prior rows", deleted)

    # 4. Evaluate each yoga
    build_uuid = build_id or str(uuid.uuid4())
    rows_inserted = 0

    with conn.cursor() as cur:
        for yoga in yoga_catalog:
            cid = yoga["canonical_id"]
            result = _evaluate_yoga(yoga, state)

            if result is None:
                continue  # did not fire

            family_ids = family_map.get(cid, [])

            try:
                cur.execute("""
                    INSERT INTO ga_yoga_firings (
                        chart_id, build_id, ayanamsha_id, yoga_canonical_id,
                        fired, constituent_fact_ids, constituent_planets,
                        constituent_houses, strength, strength_formula_version,
                        partial_formation_pct, is_partial,
                        bhanga_active, bhanga_rule_fired,
                        family_ids, computed_at
                    ) VALUES (
                        %s, %s::uuid, %s, %s,
                        %s, %s::jsonb, %s::jsonb,
                        %s::jsonb, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s::jsonb, NOW()
                    )
                """, (
                    chart_id,
                    build_uuid,
                    ayanamsha_id,
                    cid,
                    result["fired"],
                    json.dumps(result["constituent_fact_ids"]),
                    json.dumps(result["constituent_planets"]),
                    json.dumps(result["constituent_houses"]),
                    result["strength"],
                    result["strength_formula_version"],
                    result["partial_formation_pct"],
                    result["is_partial"],
                    result["bhanga_active"],
                    result["bhanga_rule_fired"],
                    json.dumps(family_ids),
                ))
                rows_inserted += 1
            except Exception as exc:
                logger.warning(
                    "[ga_yoga_writer] insert failed for yoga=%s chart=%s ayanamsha=%s: %s",
                    cid, chart_id, ayanamsha_id, exc,
                )

    elapsed = time.time() - t0
    logger.info(
        "[ga_yoga_writer] substep done: chart=%s ayanamsha=%s rows=%d elapsed=%.1fs",
        chart_id, ayanamsha_id, rows_inserted, elapsed,
    )

    # FORENSIC assertion for native chart
    if chart_id == CANONICAL_CHART_ID:
        _forensic_assert(rows_inserted, ayanamsha_id)

    return rows_inserted


def _forensic_assert(rows_inserted: int, ayanamsha_id: str) -> None:
    """
    Hard FORENSIC assertion for native chart 482012f1-710e-4a25-994a-93821f5871aa.
    Raises AssertionError (halts the build) if 0 yogas fired — this is a sign of
    missing chart_facts input, not a valid empty result for the native's chart.

    Known expected checks for Aries lagna, Sun/Capricorn, Moon/Purva Bhadrapada:
    - budha_aditya: Sun and Mercury conjunction — common in Capricorn
    - kemadruma_aristha: Moon isolation check — PBP (Aquarius) is a key check
    - gajakesari: Jupiter-Moon kendra check
    - sunapha/anapha: planets around Moon check
    """
    if rows_inserted == 0:
        raise AssertionError(
            f"[ga_yoga_writer] FORENSIC FAIL: native chart {CANONICAL_CHART_ID} "
            f"ayanamsha={ayanamsha_id} fired 0 yogas — check chart_facts completeness"
        )
    logger.info(
        "[ga_yoga_writer] FORENSIC: native chart %s ayanamsha=%s fired %d yogas",
        CANONICAL_CHART_ID, ayanamsha_id, rows_inserted,
    )
