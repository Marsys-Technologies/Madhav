"""
ga_yoga_writer.py — GA Yoga Firings Writer
==========================================
Asset: ga_yoga — per-chart yoga firing records.

Evaluates classical yoga formation rules against L1 chart_facts rows
(from ga_structural, ga_positions) for each ayanamsha, then writes
one row per fired yoga into ga_yoga_firings.

Hard rails:
- ZERO LLM in data path — all yoga logic is deterministic rule evaluation.
- No fabricated strength: strength is NULL unless resolvable via the single
  ratified constituent_bala_v1 derivation (JL-012/J3 — normalized shadbala of
  constituent grahas; never a per-yoga invented formula, B.10).
- bhanga_active is NULL-with-a-documented-reason (bhanga_na_reason) wherever
  this writer implements no classical cancellation rule for that yoga type
  (JL-012/J3); Kemadruma's own bhanga logic is left untouched, not duplicated.
  R6A.1 (Y-5): a generic registry-driven bhanga evaluator (evaluate_bhanga)
  now supplies REAL cancellation verdicts where a cited classical rule is
  implemented — currently Neecha Bhanga Raja Yoga (5 classical rules, D1+D9;
  rule 5 floored per B.10). All other yogas keep the honest NULL floor.
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
from dataclasses import dataclass
from typing import Any, Callable

import psycopg.rows

from brahmagyan.graha_vocabulary import norm_graha, to_title

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

# Benefics and malefics (natural, context-independent)
NATURAL_BENEFICS = {"jupiter", "venus", "mercury", "moon"}
NATURAL_MALEFICS = {"sun", "mars", "saturn", "rahu", "ketu"}

# ── JL-012 / J3 — constituent_bala_v1 strength derivation ──────────────────────
# No yoga-specific strength formula exists in the classical corpus (B.10). Per
# ratified ruling JL-012, strength = normalized shadbala of the yoga's
# constituent grahas, applied uniformly across every yoga type this writer
# detects (never a per-yoga invented weighting). Source: graha_shadbala_total
# (chart_facts), written by ga_strength_writer — fact_key='rupa' (actual,
# ayanamsha-scoped) and fact_key='required_rupa' (classical Parashara minimum,
# ayanamsha_id='INVARIANT'). Only classical for the 7 grahas Sun..Saturn —
# Rahu/Ketu/Lagna and house-lord constituents have no shadbala in this schema
# and are simply excluded from the mean (not fabricated).
CONSTITUENT_BALA_DERIVATION = "constituent_bala_v1"
CONSTITUENT_BALA_LABEL = "computed_extension"

# planet (lowercase, as used in constituent_planets) → graha_shadbala_total
# fact_subject code. Values sourced from the graha SSoT
# (brahmagyan/graha_vocabulary) rather than hardcoded literals —
# ADHIṢṬHĀNA Lane A2.
GRAHA_SHADBALA_SUBJECTS: dict[str, str] = {
    planet: norm_graha(planet)
    for planet in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")
}

# Kemadruma's cancellation (bhanga) is already gated into its own firing
# condition above (relation="no_planet_in_2_or_12_from_moon_and_no_kendra_support")
# and, at the ga_structural layer, in ga_structural_writer.py's KEMADRUMA branch
# (Moon-in-kendra cancellation). Do not duplicate/override its bhanga_active here.
KEMADRUMA_CANONICAL_ID = "kemadruma_aristha"

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
    with conn.cursor() as cur:
        cur.execute("""
            SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_text,
                   fact_value_num, fact_value_jsonb
            FROM chart_facts
            WHERE chart_id = %s AND ayanamsha_id = %s
        """, (chart_id, ayanamsha_id))
        return [dict(r) for r in cur.fetchall()]


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


def _load_shadbala_map(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, dict[str, float]]:
    """
    Load composite shadbala (actual rupa) and classical required rupa per
    classical graha, keyed by lowercase planet name (sun..saturn) to match
    ChartState / _evaluate_yoga's constituent_planets convention.

    Source: chart_facts fact_category='graha_shadbala_total' — written by
    ga_strength_writer. fact_key='rupa' is ayanamsha-scoped (actual composite
    shadbala); fact_key='required_rupa' is ayanamsha_id='INVARIANT' (classical
    Parashara minimum). Used only by the constituent_bala_v1 strength
    derivation (JL-012 / J3) — never treated as this writer's own truth
    (L1-authority discipline, §N.5): the value is read, not recomputed.
    """
    subject_to_planet = {v: k for k, v in GRAHA_SHADBALA_SUBJECTS.items()}
    result: dict[str, dict[str, float]] = {}
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT fact_subject, fact_key, fact_value_num
                FROM chart_facts
                WHERE chart_id = %s
                  AND fact_category = 'graha_shadbala_total'
                  AND fact_key IN ('rupa', 'required_rupa')
                  AND (ayanamsha_id = %s OR ayanamsha_id = 'INVARIANT')
            """, (chart_id, ayanamsha_id))
            rows = [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        logger.warning(
            "[ga_yoga_writer] shadbala load failed for constituent_bala_v1 (chart=%s ayanamsha=%s): %s",
            chart_id, ayanamsha_id, exc,
        )
        return {}

    for row in rows:
        subject = (row.get("fact_subject") or "").upper()
        planet = subject_to_planet.get(subject)
        if not planet:
            continue
        key = row.get("fact_key")
        value = row.get("fact_value_num")
        if value is None or key not in ("rupa", "required_rupa"):
            continue
        result.setdefault(planet, {})[key] = float(value)
    return result


def _compute_constituent_bala_strength(
    constituent_planets: list[str],
    shadbala_map: dict[str, dict[str, float]],
    yoga_canonical_id: str,
    chart_id: str,
    ayanamsha_id: str,
) -> tuple[float | None, str | None, str | None, str | None, str | None]:
    """
    JL-012 / J3 ruling: strength = normalized shadbala of the yoga's constituent
    grahas. Normalization = actual_rupa / required_rupa (both already-computed
    classical values from graha_shadbala_total — no new ceiling invented);
    combination across constituents = plain mean (no per-yoga weighting, B.10).

    Returns (strength, derivation, strength_label, citation_ref, citation_human).
    All five are None when no constituent graha has resolvable shadbala (e.g.
    Rahu/Ketu-only constituents, or house-lord-only yogas with an empty
    constituent_planets list) — strength stays honestly NULL rather than
    fabricated.
    """
    ratios: list[float] = []
    resolved_planets: list[str] = []
    for planet in constituent_planets:
        bala = shadbala_map.get(planet)
        if not bala:
            continue
        required = bala.get("required_rupa")
        actual = bala.get("rupa")
        if not required or actual is None:
            continue
        ratios.append(actual / required)
        resolved_planets.append(planet)

    if not ratios:
        return None, None, None, None, None

    strength = round(sum(ratios) / len(ratios), 4)
    citation_ref = (
        f"ga_yoga.strength:{yoga_canonical_id}:{CONSTITUENT_BALA_DERIVATION}"
        f"@chart={chart_id}:ay={ayanamsha_id}:bala_gate=graha_shadbala_total"
    )
    citation_human = (
        f"{yoga_canonical_id} strength = mean of normalized shadbala (actual/required "
        f"rupa, graha_shadbala_total bala_gate) across constituent grahas "
        f"{sorted(set(resolved_planets))}; derivation={CONSTITUENT_BALA_DERIVATION} "
        f"({CONSTITUENT_BALA_LABEL} — not a classical per-yoga formula, B.10)."
    )
    return strength, CONSTITUENT_BALA_DERIVATION, CONSTITUENT_BALA_LABEL, citation_ref, citation_human


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
        # Jaimini Karakāṃśa (CR-130): the navāṃśa (D9) sign occupied by the
        # Ātmakāraka, treated as the karakāṃśa lagna. READ from chart_facts
        # (fact_category='karakamsa_position', KARAKAMSA/sign — written by
        # ga_sensitive_writer); never recomputed here (§N.5 L1-authority).
        self.karakamsha_sign: str | None = None
        self.karakamsha_fact_id: str | None = None
        self.atmakaraka_graha: str | None = None

        self._parse(facts)

    # Maps abbreviated fact_subject values → full planet names used in yoga
    # catalog (lowercase). Derived from the graha SSoT's to_title() helper
    # (brahmagyan/graha_vocabulary) rather than hardcoded literals —
    # ADHIṢṬHĀNA Lane A2 (found via the full-tree census; not one of the
    # originally-enumerated retirement targets — this file's own
    # established output convention happens to be all-lowercase).
    _SUBJECT_NORM: dict[str, str] = {
        code.lower(): to_title(code).lower()
        for code in (
            "sun", "moon", "mar", "mer", "jup", "ven", "sat",
            "rah_mean", "ket_mean", "lagna",
        )
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

            if cat in ("graha_position", "planet_position") and key in ("longitude_sidereal",):
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

            # Karakāṃśa lagna (CR-130) — D9 sign of the Ātmakāraka, from
            # ga_sensitive_writer's karakamsa_position rows. Consumed read-only.
            if cat == "karakamsa_position" and subj == "karakamsa":
                if key == "sign":
                    self.karakamsha_sign = (f.get("fact_value_text") or "").lower()
                    self.karakamsha_fact_id = f["fact_id"]
                elif key == "atmakaraka_graha":
                    self.atmakaraka_graha = (f.get("fact_value_text") or "").lower()

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
                # R6A.2 (Y-10): Dharma-Karmadhipati Yoga — lords of the 9th
                # (dharma) and 10th (karma) associate by conjunction, mutual
                # aspect, or sign exchange. Formation citation: catalog row
                # dharma_karmadhipati, source_citation BPHS Ch.39 (Raja Yoga
                # adhyaya) — reused, not re-derived (R6A.1 §C discipline).
                hit = _check_house_lord_association(state, 9, 10)
                if hit:
                    fired = True
                    constituent_planets = hit["lords"]
                    constituent_houses = hit["placement_houses"]
                    constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            # NOTE (Y-10, D-1.6/S-3): "kendra_lord_and_trikona_lord_associate" (catalog row
            # kendra_trikona_raja_yoga) is INTENTIONALLY absent from this dispatch — it is a
            # confirmed byte-identical duplicate of the Lane-3 detector raja_yoga_kendra_trikona
            # (both call the exact same _check_kendra_trikona_raja(state) helper; live-observed
            # on 482012f1: two ga_yoga_firings rows with identical constituent_planets/houses/
            # strength under two different canonical_ids). Superseded by raja_yoga_kendra_trikona
            # (DETECTOR_INSERT_IDS), which carries a proper mandatory-cancellation callable —
            # same supersession pattern already applied to budha_aditya/lakshmi_yoga (module
            # header, R6A.2). Floored here via R6A2_FLOOR_REASONS (falls through to the generic
            # floor branch below) so the catalog loop never double-inserts this finding.

            elif relation in R6A2_LORD_ASSOCIATION_RELATIONS:
                # R6A.2 (Y-10): two-house lord-association yogas.
                # Formation citations (reused from the catalog rows):
                #   lagna_lord_and_9th_lord_associate → raja_yoga_lagna_9th,
                #     BPHS Ch.40 (Raja Yoga adhyaya — supplemental);
                #   association_of_{2,11 / 5,9 / lagna,2 / 9,11} lords →
                #     dhana_yoga_* rows, BPHS Ch.41 (Dhana Yoga adhyaya).
                h1, h2 = R6A2_LORD_ASSOCIATION_RELATIONS[relation]
                hit = _check_house_lord_association(state, h1, h2)
                if hit:
                    fired = True
                    constituent_planets = hit["lords"]
                    constituent_houses = hit["placement_houses"]
                    constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "association_among_2_5_9_11_lords":
                # R6A.2 (Y-10): Maha Dhana Yoga — association among the
                # wealth-house lords (2/5/9/11); fires on any associating
                # pair among the four lords (the catalog formation_text's
                # plain reading). Citation: dhana_yoga_2_5_9_11, BPHS Ch.41.
                hit = _check_any_lord_pair_association(state, (2, 5, 9, 11))
                if hit:
                    fired = True
                    constituent_planets = hit["lords"]
                    constituent_houses = hit["placement_houses"]
                    constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation in R6A2_VIPARITA_RELATIONS:
                # R6A.2 (Y-10): Viparita Raja Yoga family — Harsha (6th lord),
                # Sarala (8th lord), Vimala (12th lord) placed in a dusthana
                # (6/8/12, own house included) — "poison cures poison".
                # Citation: catalog rows vipareeta_harsha/sarala/vimala,
                # source_citation Phaladeepika Ch.7 (Raja Yoga).
                own_house = R6A2_VIPARITA_RELATIONS[relation]
                hit = _check_lord_in_houses(state, own_house, DUSTHANAS)
                if hit:
                    fired = True
                    constituent_planets = hit["lords"]
                    constituent_houses = hit["placement_houses"]
                    constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "11th_lord_in_dusthana_or_lagna_lord_in_6_8_12":
                # R6A.2 (Y-10): Daridra Yoga — the 11th lord (gains) in a
                # dusthana, OR the lagna lord in 6/8/12 (catalog disjunction).
                # Citation: catalog row daridra_yoga, source_citation Saravali
                # (classical_citations also list BPHS).
                hit = (_check_lord_in_houses(state, 11, DUSTHANAS)
                       or _check_lord_in_houses(state, 1, DUSTHANAS))
                if hit:
                    fired = True
                    constituent_planets = hit["lords"]
                    constituent_houses = hit["placement_houses"]
                    constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "moon_jupiter_in_6_8_from_each_other":
                # R6A.2 (Y-10): Shakata Dur-Yoga — Moon and Jupiter in 6/8
                # (shadashtaka) from each other. The catalog's exclusion
                # clause {"exclude": "jupiter_in_kendra_from_lagna"} is
                # enforced HERE at formation time, exactly mirroring the
                # Y-9 fix in ga_structural_writer._evaluate_catalog_rule —
                # the two evaluators must not disagree on Shakata's
                # qualifier. (Jupiter in kendra from the MOON is
                # geometrically impossible when the two are 6/8 apart, so
                # the catalog's bhanga clause has no residual reach beyond
                # this exclusion.) Citation: catalog row shakata_dur_yoga,
                # source_citation Saravali (classical_citations also BPHS).
                moon_h = _house_of_planet("moon", state)
                jup_h = _house_of_planet("jupiter", state)
                if moon_h and jup_h:
                    rel_h = ((jup_h - moon_h) % 12) + 1
                    if rel_h in (6, 8) and jup_h not in KENDRAS:
                        fired = True
                        constituent_planets = ["moon", "jupiter"]
                        constituent_houses = sorted({moon_h, jup_h})
                        constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "mutual_exchange_of_signs_between_two_auspicious_house_lords":
                # R6A.2 (Y-10): Parivartana (Maha) Raja Yoga — lords of two
                # auspicious houses in mutual sign exchange, with the dainya
                # guard (see _check_auspicious_parivartana). Citation:
                # catalog row parivartana_raja_yoga, BPHS Ch.39.
                hit = _check_auspicious_parivartana(state)
                if hit:
                    fired = True
                    constituent_planets = hit["lords"]
                    constituent_houses = hit["placement_houses"]
                    constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)
                break

            elif relation == "four_or_more_planets_in_one_house":
                # R6A.2 (Y-10): Pravrajya (Sannyasa) Yoga — four or more of
                # the SEVEN classical grahas (nodes excluded, per the catalog
                # formation_text) gathered in one whole-sign house. Citation:
                # catalog row pravrajya_yoga, BPHS Ch.36 (Pravrajya adhyaya).
                for h in sorted(state.lagna_house_planets):
                    grouped = sorted(
                        p for p in state.lagna_house_planets[h]
                        if p in NBRY_CLASSICAL_GRAHAS
                    )
                    if len(grouped) >= 4:
                        fired = True
                        constituent_planets = grouped
                        constituent_houses = [h]
                        constituent_fact_ids = state.fact_ids_for_planets(grouped)
                        break
                break

            elif relation in R6A2_FLOOR_REASONS:
                # R6A.2 (Y-10) honest floor. The pre-R6A.2 comment here
                # claimed "the ga_structural writer (GA8) does yoga_fires
                # rows that handle these" — that claim was FALSE (defect
                # register Y-10) and is retired. Every relation still
                # floored has a SPECIFIC documented reason in
                # R6A2_FLOOR_REASONS (per-relation, not generic); firing
                # any of them without resolving that reason would be
                # fabrication (B.10). fired stays False → no row.
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


# ═══════════════════════════════════════════════════════════════════════════════
# R6A.2 — House-lord yoga detection (defect register Y-10)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Before R6A.2, ~27 house-lord relations were silently skipped behind a FALSE
# comment claiming ga_structural (GA8) handled them (it does not — Y-10), and
# _check_house_lord_association / _check_kendra_trikona_raja were hardcoded
# `return False` stubs. This section implements the real evaluators:
#
#   * Lord-of-house resolution: lagna sign + the Parashari sign-lord table
#     (NB_SIGN_LORDS, sealed in R6A.1, mirroring ga_structural_writer's
#     SIGN_LORDS). Rahu/Ketu never lord a sign in this table, so house lords
#     are always among the 7 classical grahas.
#   * "Association" (sambandha) = conjunction (same whole-sign house), MUTUAL
#     Parashari graha-drishti (each aspects the other's house; special aspects
#     of Mars/Jupiter/Saturn included via NB_GRAHA_DRISHTI), or parivartana
#     (mutual sign exchange) — the classical three-fold sambandha of the BPHS
#     Raja/Dhana yoga adhyayas.
#   * All placements whole-sign, lagna-relative (same basis as this writer's
#     other branches).
#
# LESS-scope decisions (deliberate, documented — flag for conductor review):
#   * If one planet lords BOTH houses of a pair (e.g. Taurus lagna: Saturn
#     lords both 9 and 10), the association does NOT fire — classical
#     treatments of self-association diverge; we do not pick one silently.
#   * Association requires MUTUAL aspect, never one-way drishti (the
#     conservative classical reading of sambandha).
#
# ZERO LLM — plain deterministic Python.
#
# Formation citations are REUSED from the catalog rows these relations belong
# to (brahma_yoga_catalog.source_citation, seeded in brahmagyan/l0_yogas.py) —
# same discipline as R6A.1's reuse of the BPHS Ch.39 NBRY anchor: BPHS Ch.39
# (Raja Yoga adhyaya) for Dharma-Karmadhipati / Kendra-Trikona / Parivartana
# Raja; BPHS Ch.40 for the Lagna-9th-lord raja; BPHS Ch.41 (Dhana Yoga
# adhyaya) for the dhana family; Phaladeepika Ch.7 for the Viparita family
# (Harsha/Sarala/Vimala); Saravali (+BPHS) for Daridra and Shakata; BPHS
# Ch.36 (Pravrajya adhyaya) for the 4+-graha sannyasa grouping. Firing rows'
# citation_ref/citation_human continue to carry the JL-012 strength-derivation
# citation (set uniformly in the main loop); the formation citation is
# authoritative on the catalog row itself.
#
# Cancellation wiring (R6A.2 §B outcome): NO new _BHANGA_EVALUATORS entries —
# none of these families has a classical cancellation rule this author can
# confidently cite as bhanga-of-the-formed-yoga:
#   * Shakata: the classical qualifier (Jupiter in a kendra from the lagna)
#     is enforced as a FORMATION exclusion (catalog "exclude" clause; parity
#     with ga_structural's Y-9 fix), and Jupiter in a kendra from the Moon is
#     geometrically impossible when the two are 6/8 apart — nothing remains
#     to register.
#   * Daridra's catalog bhanga ("dhana_or_raja_yoga_present") is a cross-yoga
#     interaction with no confidently citable classical chapter → it keeps
#     the honest NULL + has_catalog_cancellation reason via evaluate_bhanga.
#   * Dharma-Karmadhipati / Kendra-Trikona carry only "weakened_if" clauses
#     (strength modulation, not cancellation) → honest NULL floor likewise.

# Auspicious houses for parivartana classification (1,2,4,5,7,9,10,11 —
# catalog formation_text of parivartana_raja_yoga / shubha_parivartana).
R6A2_AUSPICIOUS_HOUSES: tuple[int, ...] = (1, 2, 4, 5, 7, 9, 10, 11)

# relation → (h1, h2) for plain two-house lord-association yogas.
R6A2_LORD_ASSOCIATION_RELATIONS: dict[str, tuple[int, int]] = {
    "lagna_lord_and_9th_lord_associate": (1, 9),    # raja_yoga_lagna_9th (BPHS Ch.40)
    "association_of_2nd_and_11th_lords": (2, 11),   # dhana_yoga_2_11 (BPHS Ch.41)
    "association_of_5th_and_9th_lords": (5, 9),     # dhana_yoga_5_9 (BPHS Ch.41)
    "association_of_lagna_and_2nd_lords": (1, 2),   # dhana_yoga_lagna_2 (BPHS Ch.41)
    "association_of_9th_and_11th_lords": (9, 11),   # dhana_yoga_9_11 (BPHS Ch.41)
}

# relation → the dusthana whose lord is examined (Viparita family,
# Phaladeepika Ch.7).
R6A2_VIPARITA_RELATIONS: dict[str, int] = {
    "6th_lord_in_6_8_or_12": 6,     # vipareeta_harsha
    "8th_lord_in_6_8_or_12": 8,     # vipareeta_sarala
    "12th_lord_in_6_8_or_12": 12,   # vipareeta_vimala
}

# Relations that remain HONESTLY floored after R6A.2, each with its specific
# reason (replaces the false "GA8 handles these" comment — Y-10). A floored
# relation returns no row; firing it without resolving the stated blocker
# would be fabrication (B.10). "Scope questions default to LESS scope."
R6A2_FLOOR_REASONS: dict[str, str] = {
    "kendra_lord_and_trikona_lord_associate": (
        "kendra_trikona_raja_yoga (catalog row): confirmed duplicate of the Lane-3 detector "
        "raja_yoga_kendra_trikona (Y-10, D-1.6/S-3) — both evaluate _check_kendra_trikona_raja "
        "identically; the catalog row is floored here so it never double-fires alongside the "
        "detector row, which is the authoritative one (it carries a mandatory cancellation "
        "callable this catalog relation lacks)"
    ),
    "4th_and_9th_lords_in_mutual_kendra": (
        "kahala: the mutual-kendra clause is computable, but the catalog "
        "co-requirement {lagna_lord strong} has no ratified deterministic "
        "'strong' predicate in this writer — firing on the relation alone "
        "would over-fire"
    ),
    "5th_and_6th_lords_in_mutual_kendra": (
        "sankha: same {lagna_lord strong} co-requirement blocker as kahala"
    ),
    "9th_lord_own_or_exalted_in_kendra_trikona": (
        "lakshmi_yoga: same {lagna_lord strong} co-requirement blocker"
    ),
    "mercury_venus_jupiter_in_kendra_trikona_or_2nd": (
        "saraswati: positional clause computable, but the {jupiter strong} "
        "co-requirement has no ratified deterministic predicate here"
    ),
    "venus_lagna_lord_9th_lord_strong_and_related": (
        "bheri: 'strong and related' compound has no ratified deterministic "
        "definition in this writer"
    ),
    "lagna_lord_exalted_in_kendra_aspected_by_jupiter": (
        "chamara: compound rule with an 'alt' disjunct "
        "(two_benefics_in_1_7_9_or_10); deferred rather than partially "
        "implemented — not in the R6A.2 family scope"
    ),
    "benefics_in_upachayas_3_6_10_11_from_lagna_or_moon": (
        "vasumati: quantifier ambiguous in catalog rule (ALL vs ANY benefics; "
        "lagna vs moon basis) — classical variants differ; not resolved here"
    ),
    "benefics_in_6_7_8_from_lagna": (
        "lagnadhi variant: required benefic count ambiguous in catalog rule"
    ),
    "four_plus_planets_in_one_house": (
        "sannyasa_strongest_planet: formation duplicates pravrajya_yoga "
        "(implemented above); its determinant (strongest grouped graha sets "
        "the ascetic order) requires a strength ranking not ratified in this "
        "writer"
    ),
    "debilitated_planet_with_cancelled_debility": (
        "neecha_bhanga_raja_yoga: evaluated by _build_nbry_firing (R6A.1) "
        "with real per-varga D1/D9 bhanga rules — must not double-fire via "
        "this catalog loop"
    ),
    "kendra_and_trikona_lords_as_benefics_in_kendras": (
        "parvata: multiple classical variants of Parvata exist and the "
        "catalog reading ('lords as benefics') is ambiguous — not implemented "
        "to avoid picking the wrong variant"
    ),
    "benefics_in_2nd_and_12th_from_a_house_or_planet": (
        "shubha_kartari: the flanking target ('a house or planet') is "
        "unspecified in the catalog rule — no deterministic target to check"
    ),
    "saturn_strongest_in_a_4plus_grouping_or_aspecting_moon_with_ketu": (
        "sannyasa_saturn: 'strongest' requires a strength ranking not "
        "ratified in this writer"
    ),
    "all_seven_planets_hemmed_rahu_ketu_one_side": (
        "kala_sarpa_yoga (relation form): legacy DUPLICATE of the dosha-form "
        "Kala Sarpa, which is fully implemented per-varga in "
        "ga_structural_writer._detect_kala_sarpa (kala_sarpa_per_varga rows) "
        "— re-firing it here would create two authorities for one dosha "
        "(R6A.2 finding; conductor may retire the catalog relation instead)"
    ),
}


def _sign_of_house(state: ChartState, house: int) -> str | None:
    """Sign occupying whole-sign house `house` (1-12) counted from the lagna."""
    if not state.lagna_sign or state.lagna_sign not in SIGN_NUMBERS:
        return None
    num = ((SIGN_NUMBERS[state.lagna_sign] - 1 + house - 1) % 12) + 1
    return SIGN_NAMES[num]


def _lord_of_house(state: ChartState, house: int) -> str | None:
    """Parashari lord of the sign in whole-sign house `house` from the lagna
    (NB_SIGN_LORDS — the R6A.1-sealed table)."""
    sign = _sign_of_house(state, house)
    return NB_SIGN_LORDS.get(sign) if sign else None


def _planets_associated(state: ChartState, p1: str, p2: str) -> str | None:
    """Classical sambandha between two DISTINCT planets: 'conjunction' (same
    whole-sign house), 'exchange' (each occupies a sign the other lords), or
    'mutual_aspect' (each casts Parashari drishti on the other's house).
    Returns the mode string, or None if not associated."""
    if p1 == p2:
        return None
    h1 = _house_of_planet(p1, state)
    h2 = _house_of_planet(p2, state)
    if not h1 or not h2:
        return None
    if h1 == h2:
        return "conjunction"
    s1 = state.planet_sign.get(p1)
    s2 = state.planet_sign.get(p2)
    if s1 and s2 and NB_SIGN_LORDS.get(s1) == p2 and NB_SIGN_LORDS.get(s2) == p1:
        return "exchange"
    if _nb_aspects_house(p1, h1, h2) and _nb_aspects_house(p2, h2, h1):
        return "mutual_aspect"
    return None


def _check_house_lord_association(state: ChartState, h1: int, h2: int) -> dict | None:
    """R6A.2 (Y-10): REAL generic house-lord association check (was a
    hardcoded `return False` stub). Do the lords of houses h1 and h2 (from
    the lagna) associate by conjunction / mutual aspect / sign exchange?

    Returns a detail dict {lords, houses_ruled, placement_houses,
    association_mode} when the association holds, else None (truthiness-
    compatible with the old bool contract). Same-lord pairs never fire
    (LESS scope — see section header)."""
    l1 = _lord_of_house(state, h1)
    l2 = _lord_of_house(state, h2)
    if not l1 or not l2 or l1 == l2:
        return None
    mode = _planets_associated(state, l1, l2)
    if not mode:
        return None
    placement = [h for h in (_house_of_planet(l1, state), _house_of_planet(l2, state)) if h]
    return {
        "lords": [l1, l2],
        "houses_ruled": [h1, h2],
        "placement_houses": sorted(set(placement)),
        "association_mode": mode,
    }


def _check_kendra_trikona_raja(state: ChartState) -> dict | None:
    """R6A.2 (Y-10): REAL Kendra-Trikona Raja Yoga check (was a hardcoded
    `return False` stub) — any kendra lord (1/4/7/10) associated with any
    trikona lord (1/5/9), per BPHS Ch.39. House 1 is both kendra and trikona;
    the degenerate (1,1) pair is skipped, and same-lord pairs never fire
    (LESS scope). Returns the first firing pair's detail dict, else None."""
    for hk in sorted(KENDRAS):
        for ht in sorted(TRIKONAS):
            if hk == ht:
                continue
            hit = _check_house_lord_association(state, hk, ht)
            if hit:
                return hit
    return None


def _check_any_lord_pair_association(state: ChartState, houses: tuple[int, ...]) -> dict | None:
    """Any associating lord pair among `houses` (Maha Dhana reading:
    'association among the lords of 2/5/9/11'). First firing pair returned."""
    for i, h1 in enumerate(houses):
        for h2 in houses[i + 1:]:
            hit = _check_house_lord_association(state, h1, h2)
            if hit:
                return hit
    return None


def _check_lord_in_houses(state: ChartState, lord_house: int, target_houses: set[int]) -> dict | None:
    """Is the lord of `lord_house` placed (whole-sign, from lagna) in one of
    `target_houses`? (Viparita family; Daridra.)"""
    lord = _lord_of_house(state, lord_house)
    if not lord:
        return None
    ph = _house_of_planet(lord, state)
    if ph is None or ph not in target_houses:
        return None
    return {"lords": [lord], "houses_ruled": [lord_house], "placement_houses": [ph]}


def _check_auspicious_parivartana(state: ChartState) -> dict | None:
    """Parivartana (Maha) Raja Yoga: the lords of two AUSPICIOUS houses
    (1/2/4/5/7/9/10/11) in mutual sign exchange — lord of h1 occupies h2 and
    lord of h2 occupies h1. Dainya guard (the catalog row's cancellation
    'excluded' clause, dainya_parivartana_with_6_8_12): neither participating
    lord may ALSO lord a dusthana (6/8/12) — conservative reading so a
    dual-lordship exchange is never mislabeled raja when its dusthana side
    would make it dainya (LESS scope — flag for conductor review)."""
    dusthana_lords = {_lord_of_house(state, h) for h in sorted(DUSTHANAS)}
    for i, h1 in enumerate(R6A2_AUSPICIOUS_HOUSES):
        for h2 in R6A2_AUSPICIOUS_HOUSES[i + 1:]:
            l1 = _lord_of_house(state, h1)
            l2 = _lord_of_house(state, h2)
            if not l1 or not l2 or l1 == l2:
                continue
            if l1 in dusthana_lords or l2 in dusthana_lords:
                continue
            if _house_of_planet(l1, state) == h2 and _house_of_planet(l2, state) == h1:
                return {
                    "lords": [l1, l2],
                    "houses_ruled": [h1, h2],
                    "placement_houses": sorted((h1, h2)),
                    "association_mode": "exchange",
                }
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# R6A.1 — Generic yoga-cancellation (bhanga) evaluator + Neecha Bhanga Raja Yoga
# ═══════════════════════════════════════════════════════════════════════════════
#
# Defect register Y-5: bhanga was only implemented for Kemadruma; every other
# yoga's bhanga_active was NULL-with-reason (correct floor behavior, B.10).
# This section adds:
#   (a) evaluate_bhanga(...) — a generic, registry-driven cancellation evaluator.
#       Yogas without a registered real classical rule keep today's honest
#       NULL + bhanga_na_reason floor. R6A.2 (house-lord family) plugs in later
#       by adding entries to _BHANGA_EVALUATORS.
#   (b) The 5 classical Neecha Bhanga Raja Yoga (NBRY) rules, each a distinct
#       separately-testable function with its own classical citation or an
#       explicit floor (rule 5 is floored — see NBRY_RULE_5_FLOOR_REASON).
#   (c) Per-varga evaluation: D1 (rasi) and D9 (navamsha) debilitations are
#       checked independently; rule 2 additionally carries the classical
#       navamsha extension (exaltation-graha in kendra from the navamsha
#       lagna redeems a D1 debilitation) — the golden-gate case.
#
# ZERO LLM — plain deterministic Python. Dignity tables mirror the L0-sealed
# Parashari tables in ga_writers/ga_structural_writer.py (EXALTATION_SIGNS /
# DEBILITATION_SIGNS / SIGN_LORDS), lowercased to this writer's naming
# convention. NBRY is evaluated for the 7 classical grahas only — classical
# neecha-bhanga doctrine is stated for Sun..Saturn; nodes are excluded
# (LESS-scope decision, not an oversight).

NBRY_CANONICAL_ID = "neecha_bhanga_raja_yoga"

NBRY_CLASSICAL_GRAHAS = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")

# Sign → lord (Parashari; mirror of ga_structural_writer.SIGN_LORDS, lowercase)
NB_SIGN_LORDS: dict[str, str] = {
    "aries": "mars", "taurus": "venus", "gemini": "mercury",
    "cancer": "moon", "leo": "sun", "virgo": "mercury",
    "libra": "venus", "scorpio": "mars", "sagittarius": "jupiter",
    "capricorn": "saturn", "aquarius": "saturn", "pisces": "jupiter",
}

# Planet → exaltation sign (Parashari; mirror of ga_structural_writer.EXALTATION_SIGNS)
NB_EXALTATION_SIGNS: dict[str, str] = {
    "sun": "aries", "moon": "taurus", "mars": "capricorn",
    "mercury": "virgo", "jupiter": "cancer", "venus": "pisces", "saturn": "libra",
}

# Planet → debilitation sign (Parashari; mirror of ga_structural_writer.DEBILITATION_SIGNS)
NB_DEBILITATION_SIGNS: dict[str, str] = {
    "sun": "libra", "moon": "scorpio", "mars": "cancer",
    "mercury": "pisces", "jupiter": "capricorn", "venus": "virgo", "saturn": "aries",
}

# Sign → the graha that gets EXALTED in that sign (inverse of NB_EXALTATION_SIGNS).
# e.g. Saturn debilitated in Aries → the graha exalted in Aries is the Sun.
NB_EXALTED_IN_SIGN: dict[str, str] = {sign: planet for planet, sign in NB_EXALTATION_SIGNS.items()}

# Parashari whole-sign graha drishti (special aspects; all grahas aspect the 7th).
# BPHS graha-drishti adhyaya — Mars 4/8, Jupiter 5/9, Saturn 3/10, all 7th.
NB_GRAHA_DRISHTI: dict[str, frozenset[int]] = {
    "mars": frozenset({4, 7, 8}),
    "jupiter": frozenset({5, 7, 9}),
    "saturn": frozenset({3, 7, 10}),
}
NB_DEFAULT_DRISHTI = frozenset({7})

# ── NBRY citations (citation discipline — section C of R6A.1) ──────────────────
# Grain: source text + chapter/adhyaya, no fabricated verse numbers. BPHS Ch.39
# is this project's ratified NBRY anchor (brahma_yoga_catalog.neecha_bhanga_raja_yoga
# cites {"text_id": "bphs"} with source_citation BPHS Ch.39 Raja Yoga adhyaya —
# see brahmagyan/l0_yogas.py). Phaladeepika's raja-yoga treatment is Ch.7
# (mirrors the catalog's PHALADEEPIKA_CH7 constant).
NBRY_CITATIONS: dict[str, tuple[str, str]] = {
    "nbry_rule_1_dispositor_kendra": (
        "bphs:ch39_raja_yoga_adhyaya:neecha_bhanga:dispositor_kendra",
        "BPHS Ch.39 (Raja Yoga adhyaya), neecha-bhanga verses; also Phaladeepika "
        "Ch.7 (Raja Yoga): the lord of the sign of debilitation placed in a kendra "
        "from the Lagna or from the Moon cancels the debility.",
    ),
    "nbry_rule_2_exaltation_lord_kendra": (
        "bphs:ch39_raja_yoga_adhyaya:neecha_bhanga:exaltation_graha_kendra",
        "BPHS Ch.39 (Raja Yoga adhyaya), neecha-bhanga verses; also Phaladeepika "
        "Ch.7 (Raja Yoga): the graha that is exalted in the debilitated planet's "
        "sign of debilitation, placed in a kendra from the Lagna or from the Moon, "
        "cancels the debility.",
    ),
    # Navamsha extension of rule 2 — kendra reckoned from the navamsha lagna.
    "nbry_rule_2_exaltation_lord_kendra_d9": (
        "bphs:ch39_raja_yoga_adhyaya:neecha_bhanga:exaltation_graha_kendra_navamsha",
        "BPHS Ch.39 (Raja Yoga adhyaya), neecha-bhanga verses — navamsha extension "
        "(classical Parashari transmission): the graha exalted in the debilitated "
        "planet's sign of debilitation, placed in a kendra reckoned from the "
        "navamsha (D9) lagna, cancels the debility.",
    ),
    "nbry_rule_3_lord_aspect": (
        "bphs:ch39_raja_yoga_adhyaya:neecha_bhanga:lord_aspect",
        "BPHS Ch.39 (Raja Yoga adhyaya), neecha-bhanga verses (classical "
        "enumeration): the debilitated planet aspected by the lord of its sign of "
        "debilitation, or by the lord of its own sign of exaltation, has its "
        "debility cancelled.",
    ),
    "nbry_rule_4_conjunct_exaltation_graha": (
        "bphs:ch39_raja_yoga_adhyaya:neecha_bhanga:conjunct_exaltation_graha",
        "BPHS Ch.39 (Raja Yoga adhyaya), neecha-bhanga verses (classical "
        "enumeration): the debilitated planet conjoined with the graha that is "
        "exalted in that same sign has its debility cancelled.",
    ),
}

# Rule 5 (dispositor of the debilitation sign and the exaltation-graha in mutual
# kendra from each other) is FLOORED: the condition circulates in the transmitted
# neecha-bhanga enumeration, but this author cannot pin it to a primary classical
# text + chapter with genuine confidence (its most familiar attributions are
# modern compilations quoting the tradition). Per project rule B.10 / R6A.1 §C,
# it ships as NULL + reason, never as an uncited firing rule.
NBRY_RULE_5_FLOOR_REASON = (
    "no confidently-verifiable classical citation for this cancellation pattern "
    "(mutual-kendra of the debilitation-sign dispositor and the exaltation-graha "
    "is transmitted in modern compilations; a primary classical text+chapter "
    "could not be verified with confidence) — floored per B.10, not fired"
)

NBRY_STRENGTH_FORMULA_VERSION = "nbry_rule_count_v1"
NBRY_TOTAL_RULES = 5  # denominator includes the floored rule 5 — honest grading


def _nb_rel_house(from_house: int, to_house: int) -> int:
    """1-based whole-sign house of `to_house` counted from `from_house`."""
    return ((to_house - from_house) % 12) + 1


def _nb_in_kendra_from_lagna_or_moon(
    positions: dict[str, dict[str, Any]], planet: str
) -> tuple[bool, list[str]]:
    """True if `planet` sits in a kendra (1/4/7/10) from the lagna OR from the
    Moon, within the given varga's positions. Returns (hit, basis-list)."""
    p = positions.get(planet)
    if not p:
        return False, []
    basis: list[str] = []
    if p["house"] in KENDRAS:
        basis.append("lagna")
    moon = positions.get("moon")
    if moon and _nb_rel_house(moon["house"], p["house"]) in KENDRAS:
        basis.append("moon")
    return bool(basis), basis


def _nb_aspects_house(aspecting_planet: str, from_house: int, target_house: int) -> bool:
    """Parashari whole-sign drishti: does `aspecting_planet` at `from_house`
    aspect `target_house`?"""
    drishti = NB_GRAHA_DRISHTI.get(aspecting_planet, NB_DEFAULT_DRISHTI)
    return _nb_rel_house(from_house, target_house) in drishti


# ── The 5 NBRY rules — each a distinct, separately-testable function ────────────
# Each takes the debilitated planet + the varga's positions
# ({planet: {"sign": str, "house": int}} — houses lagna-relative, lowercase)
# and returns a finding dict if the rule fires, a floor dict if the rule is
# floored, or None if it does not fire.

def nbry_rule_1_dispositor_kendra(
    planet: str, positions: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Rule 1: dispositor (lord) of the debilitation sign is in a kendra from
    the lagna or from the Moon."""
    debil_sign = NB_DEBILITATION_SIGNS[planet]
    dispositor = NB_SIGN_LORDS[debil_sign]
    hit, basis = _nb_in_kendra_from_lagna_or_moon(positions, dispositor)
    if not hit:
        return None
    ref, human = NBRY_CITATIONS["nbry_rule_1_dispositor_kendra"]
    return {
        "rule_id": "nbry_rule_1_dispositor_kendra",
        "supporting_planets": [dispositor],
        "supporting_houses": [positions[dispositor]["house"]],
        "kendra_basis": basis,
        "citation_ref": ref,
        "citation_human": human,
    }


def nbry_rule_2_exaltation_lord_kendra(
    planet: str,
    positions: dict[str, dict[str, Any]],
    navamsa_positions: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Rule 2 (golden gate): the graha that gets EXALTED in the debilitated
    planet's debilitation sign is in a kendra from the lagna or from the Moon.
    Navamsha extension: when `navamsa_positions` is supplied (D1 evaluation
    context), the same graha in a kendra from the D9 lagna also fires
    (distinct rule id `..._d9`)."""
    debil_sign = NB_DEBILITATION_SIGNS[planet]
    exalt_graha = NB_EXALTED_IN_SIGN.get(debil_sign)
    if not exalt_graha:
        return None

    hit, basis = _nb_in_kendra_from_lagna_or_moon(positions, exalt_graha)
    if hit:
        ref, human = NBRY_CITATIONS["nbry_rule_2_exaltation_lord_kendra"]
        return {
            "rule_id": "nbry_rule_2_exaltation_lord_kendra",
            "supporting_planets": [exalt_graha],
            "supporting_houses": [positions[exalt_graha]["house"]],
            "kendra_basis": basis,
            "citation_ref": ref,
            "citation_human": human,
        }

    # Navamsha extension — kendra reckoned from the D9 lagna.
    if navamsa_positions:
        d9 = navamsa_positions.get(exalt_graha)
        if d9 and d9["house"] in KENDRAS:
            ref, human = NBRY_CITATIONS["nbry_rule_2_exaltation_lord_kendra_d9"]
            return {
                "rule_id": "nbry_rule_2_exaltation_lord_kendra",
                "varga_context": "D9",
                "supporting_planets": [exalt_graha],
                "supporting_houses": [d9["house"]],
                "kendra_basis": ["d9_lagna"],
                "citation_ref": ref,
                "citation_human": human,
            }
    return None


def nbry_rule_3_lord_aspect(
    planet: str, positions: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Rule 3: the debilitated planet is aspected by the lord of its
    debilitation sign OR by the lord of its own exaltation sign
    (Parashari whole-sign drishti)."""
    debil_sign = NB_DEBILITATION_SIGNS[planet]
    target_house = positions[planet]["house"]
    candidates = {
        NB_SIGN_LORDS[debil_sign],                       # debilitation-sign lord
        NB_SIGN_LORDS[NB_EXALTATION_SIGNS[planet]],      # exaltation-sign lord
    }
    candidates.discard(planet)
    aspectors: list[str] = []
    for cand in sorted(candidates):
        c = positions.get(cand)
        if c and c["house"] != target_house and _nb_aspects_house(cand, c["house"], target_house):
            aspectors.append(cand)
    if not aspectors:
        return None
    ref, human = NBRY_CITATIONS["nbry_rule_3_lord_aspect"]
    return {
        "rule_id": "nbry_rule_3_lord_aspect",
        "supporting_planets": aspectors,
        "supporting_houses": [positions[a]["house"] for a in aspectors],
        "citation_ref": ref,
        "citation_human": human,
    }


def nbry_rule_4_conjunct_exaltation_graha(
    planet: str, positions: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Rule 4: the debilitated planet is conjunct (same whole-sign house) with
    the graha that is exalted in that sign."""
    debil_sign = NB_DEBILITATION_SIGNS[planet]
    exalt_graha = NB_EXALTED_IN_SIGN.get(debil_sign)
    if not exalt_graha or exalt_graha == planet:
        return None
    e = positions.get(exalt_graha)
    if not e or e["house"] != positions[planet]["house"]:
        return None
    ref, human = NBRY_CITATIONS["nbry_rule_4_conjunct_exaltation_graha"]
    return {
        "rule_id": "nbry_rule_4_conjunct_exaltation_graha",
        "supporting_planets": [exalt_graha],
        "supporting_houses": [e["house"]],
        "citation_ref": ref,
        "citation_human": human,
    }


def nbry_rule_5_mutual_kendra_floored(
    planet: str, positions: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Rule 5 — FLOORED (B.10). The classical pattern (dispositor of the
    debilitation sign and the exaltation-graha in mutual kendra from each
    other) is implemented here only as an explicit floor: it never fires,
    because no confidently-verifiable primary classical citation could be
    supplied. Returns the floor marker unconditionally."""
    return {
        "rule_id": "nbry_rule_5_mutual_kendra",
        "floored": True,
        "floor_reason": NBRY_RULE_5_FLOOR_REASON,
    }


# ── Per-varga NBRY detection ────────────────────────────────────────────────────

def detect_neecha_bhanga(
    positions: dict[str, dict[str, Any]],
    varga: str = "D1",
    navamsa_positions: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Detect Neecha Bhanga for every debilitated classical graha in one varga.

    positions: {planet_lowercase: {"sign": sign_lowercase, "house": int 1-12
    counted from that varga's lagna}}. navamsa_positions (same shape, D9) is
    only consulted for the rule-2 navamsha extension and should be passed only
    when evaluating the D1 (rasi) context.

    Returns a list of findings:
      {"planet", "varga", "debilitation_sign",
       "rules_fired": [rule finding dicts], "rules_floored": [floor dicts]}
    A finding is emitted only when at least one CITED rule fires — a floored
    rule alone never produces a bhanga (B.10).
    """
    findings: list[dict[str, Any]] = []
    for planet in NBRY_CLASSICAL_GRAHAS:
        p = positions.get(planet)
        if not p or p.get("sign") != NB_DEBILITATION_SIGNS.get(planet):
            continue  # not debilitated in this varga

        rules_fired: list[dict[str, Any]] = []
        for rule_fn, kwargs in (
            (nbry_rule_1_dispositor_kendra, {}),
            (nbry_rule_2_exaltation_lord_kendra, {"navamsa_positions": navamsa_positions}),
            (nbry_rule_3_lord_aspect, {}),
            (nbry_rule_4_conjunct_exaltation_graha, {}),
        ):
            hit = rule_fn(planet, positions, **kwargs)
            if hit:
                rules_fired.append(hit)
        rules_floored = [nbry_rule_5_mutual_kendra_floored(planet, positions)]

        if rules_fired:
            findings.append({
                "planet": planet,
                "varga": varga,
                "debilitation_sign": NB_DEBILITATION_SIGNS[planet],
                "rules_fired": rules_fired,
                "rules_floored": rules_floored,
            })
    return findings


def evaluate_nbry(
    d1_positions: dict[str, dict[str, Any]],
    d9_positions: dict[str, dict[str, Any]] | None = None,
) -> tuple[bool | None, str | None, str | None, str | None, list[dict[str, Any]]]:
    """
    Evaluate Neecha Bhanga Raja Yoga across D1 and D9.

    Returns (bhanga_active, bhanga_rule_fired, citation_ref, citation_human,
    findings). bhanga_active=True iff at least one cited NBRY rule fired for
    at least one debilitated graha in either varga; None (not False) when no
    debilitation-with-cancellation configuration exists — the yoga simply does
    not form, and no row should be written.
    """
    findings = detect_neecha_bhanga(d1_positions, varga="D1", navamsa_positions=d9_positions)
    if d9_positions:
        findings.extend(detect_neecha_bhanga(d9_positions, varga="D9"))

    if not findings:
        return None, None, None, None, []

    rule_parts: list[str] = []
    refs: list[str] = []
    humans: list[str] = []
    for f in findings:
        for r in f["rules_fired"]:
            ctx = f["varga"]
            if r.get("varga_context") and r["varga_context"] != ctx:
                ctx = f"{ctx}->{r['varga_context']}"
            rule_parts.append(f"{f['planet']}@{ctx}:{r['rule_id']}")
            if r["citation_ref"] not in refs:
                refs.append(r["citation_ref"])
                humans.append(r["citation_human"])
    return True, ";".join(rule_parts), "; ".join(refs), " | ".join(humans), findings


# ── CR-59 / CR-23 grounds-checked-per-verdict ledger ────────────────────────────
# Lane 3 (Night-1) Deliverable B: detect_neecha_bhanga/evaluate_nbry above only
# surface FIRED rules (correct for the bhanga_active/bhanga_rule_fired verdict
# columns — unchanged, additive-only here). CR-59's storage direction ("store
# grounds-checked per verdict") additionally requires every rule this writer
# CHECKED for a debilitated graha — fired or not — to be visible downstream,
# so a native/serving-layer ruling (CR-23's deferred Jupiter disagreement) has
# something concrete to inspect. This ledger changes no firing/bhanga logic;
# it is a parallel, read-only record of what was evaluated.

def _nbry_grounds_ledger(
    positions: dict[str, dict[str, Any]],
    varga: str,
    navamsa_positions: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """For every debilitated classical graha in `positions`, record EVERY NBRY
    rule checked (1-4, plus the floored rule 5), each with checked=True and
    fired=bool(hit). Unlike detect_neecha_bhanga, this runs (and records)
    regardless of whether any rule ultimately fires — the CR-59 visibility
    ledger. Returns one entry per debilitated graha; empty list if none."""
    ledger: list[dict[str, Any]] = []
    for planet in NBRY_CLASSICAL_GRAHAS:
        p = positions.get(planet)
        if not p or p.get("sign") != NB_DEBILITATION_SIGNS.get(planet):
            continue  # not debilitated in this varga — nothing to check

        grounds: list[dict[str, Any]] = []
        for rule_fn, kwargs in (
            (nbry_rule_1_dispositor_kendra, {}),
            (nbry_rule_2_exaltation_lord_kendra, {"navamsa_positions": navamsa_positions}),
            (nbry_rule_3_lord_aspect, {}),
            (nbry_rule_4_conjunct_exaltation_graha, {}),
        ):
            hit = rule_fn(planet, positions, **kwargs)
            grounds.append({
                "rule_id": rule_fn.__name__,
                "checked": True,
                "fired": bool(hit),
                "detail": hit,
            })
        floor = nbry_rule_5_mutual_kendra_floored(planet, positions)
        grounds.append({
            "rule_id": floor["rule_id"],
            "checked": True,
            "fired": False,
            "detail": {"floored": True, "floor_reason": floor["floor_reason"]},
        })
        ledger.append({
            "planet": planet,
            "varga": varga,
            "debilitation_sign": p["sign"],
            "grounds": grounds,
        })
    return ledger


# ── Generic bhanga evaluator (Y-5 scaffold) ─────────────────────────────────────

def _bhanga_neecha_handler(
    *,
    d1_positions: dict[str, dict[str, Any]],
    d9_positions: dict[str, dict[str, Any]] | None = None,
    **_ignored: Any,
) -> dict[str, Any]:
    """Registered handler for neecha_bhanga_raja_yoga → generic-evaluator shape."""
    active, rule_fired, ref, human, findings = evaluate_nbry(d1_positions, d9_positions)
    return {
        "bhanga_active": active,
        "bhanga_rule_fired": rule_fired,
        "bhanga_na_reason": None if active is not None else (
            "no debilitated graha with a firing classical neecha-bhanga rule in D1/D9"
        ),
        "citation_ref": ref,
        "citation_human": human,
        "findings": findings,
    }


# Extension point for R6A.2: register per-yoga cancellation handlers here.
# A handler receives keyword context (d1_positions, d9_positions,
# constituent_planets, ...) and returns the dict shape of _bhanga_neecha_handler.
_BHANGA_EVALUATORS: dict[str, Any] = {
    NBRY_CANONICAL_ID: _bhanga_neecha_handler,
}


def evaluate_bhanga(
    yoga_canonical_id: str,
    *,
    d1_positions: dict[str, dict[str, Any]] | None = None,
    d9_positions: dict[str, dict[str, Any]] | None = None,
    constituent_planets: list[str] | None = None,
    has_catalog_cancellation: bool = False,
    special_states: dict[str, dict[str, bool]] | None = None,
) -> dict[str, Any]:
    """
    Generic yoga-cancellation evaluator (defect register Y-5).

    Returns {"bhanga_active": bool|None, "bhanga_rule_fired": str|None,
             "bhanga_na_reason": str|None, "citation_ref": str|None,
             "citation_human": str|None, "findings": list}.

    Where no real classical cancellation rule is implemented for the yoga
    type, bhanga_active stays honestly NULL with the same documented reason
    this writer has always emitted (B.10 floor discipline) — a yoga is never
    forced to a bhanga verdict.

    `special_states` (Lane 3 / Night-1 addition): planet(lower) ->
    {"is_combust", "is_debilitated", "is_exalted"} from
    graha_special_state_rollup, only consulted by handlers that declare a
    **_ignored catch-all (existing handlers ignore it harmlessly).
    """
    handler = _BHANGA_EVALUATORS.get(yoga_canonical_id)
    if handler is not None:
        return handler(
            d1_positions=d1_positions or {},
            d9_positions=d9_positions,
            constituent_planets=constituent_planets or [],
            special_states=special_states or {},
        )
    # Floor — identical wording to the pre-R6A.1 behavior.
    return {
        "bhanga_active": None,
        "bhanga_rule_fired": None,
        "bhanga_na_reason": (
            "classical bhanga (cancellation) rule exists in "
            "brahma_yoga_catalog.cancellation_conditions for this yoga but is "
            "not evaluated by ga_yoga_writer (no per-yoga bhanga formula "
            "implemented here to avoid fabrication — B.10)"
            if has_catalog_cancellation else
            "no classical bhanga (cancellation) rule exists for this yoga type"
        ),
        "citation_ref": None,
        "citation_human": None,
        "findings": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Lane 3 (Night-1) — house-lord/positional detector registry (CR-56, CR-72/73)
# ═══════════════════════════════════════════════════════════════════════════════
#
# DetectorSpec: a module-level, pure, unit-testable detector with a MANDATORY
# cancellation callable (even when the verdict is an honest NULL). Mirrors the
# R6A.1 bhanga-evaluator precedent (_BHANGA_EVALUATORS) but for FORMATION,
# not just cancellation — six detectors ship here: dhana_yoga_house_lords,
# raja_yoga_kendra_trikona, budha_aditya, sarasvati_yoga, lakshmi_yoga,
# vipareeta_raja_yoga.
#
# Deviation from the brief's literal "detector key in formation_rule_jsonb"
# routing (documented in migration 434's header comment): budha_aditya and
# lakshmi_yoga already exist in brahma_yoga_catalog under those exact
# canonical_ids with NON-detector formation rules (seeded pre-Night-1). The
# migration is additive-only (ON CONFLICT DO NOTHING) and does not rewrite
# those rows, so:
#   - budha_aditya: already fires via the existing catalog "sun_mercury_
#     conjunct" relation in _evaluate_yoga. This registry does NOT re-insert
#     a second ga_yoga_firings row for it (would violate the table's UNIQUE
#     (chart_id, ayanamsha_id, yoga_canonical_id)) — instead its mandatory
#     cancellation is wired through the existing _BHANGA_EVALUATORS extension
#     point (see _budha_aditya_bhanga_handler below), which the main catalog
#     loop already calls for every non-kemadruma firing.
#   - lakshmi_yoga: the existing catalog relation is FLOORED
#     (R6A2_FLOOR_REASONS) and therefore never inserts a row — this
#     registry's own lakshmi_yoga detector runs independently and inserts its
#     row when it fires. No collision, because the floored path never writes.
#   - dhana_yoga_house_lords, raja_yoga_kendra_trikona, sarasvati_yoga,
#     vipareeta_raja_yoga are new canonical_ids (distinct from the pre-
#     existing narrower R6A.2 rows) and insert normally through this registry.
#
# ZERO LLM — plain deterministic Python, same helper functions R6A.2 uses.

@dataclass(frozen=True)
class DetectorSpec:
    yoga_id: str
    detect: Callable[..., dict[str, Any] | None]
    cancellation: Callable[..., dict[str, Any]]
    citation_ref: str
    citation_human: str


def _load_special_states(facts: list[dict]) -> dict[str, dict[str, bool]]:
    """planet(lower) -> {"is_combust", "is_debilitated", "is_exalted"} from
    already-loaded chart_facts rows (fact_category='graha_special_state_
    rollup', written by ga_structural_writer). Read-only consumption of an
    L1 fact — never recomputed here (§N.5 L1-authority discipline)."""
    subject_to_planet = {v: k for k, v in GRAHA_SHADBALA_SUBJECTS.items()}
    result: dict[str, dict[str, bool]] = {}
    for f in facts:
        if f.get("fact_category") != "graha_special_state_rollup":
            continue
        subj = (f.get("fact_subject") or "").upper()
        planet = subject_to_planet.get(subj)
        if not planet:
            continue
        key = f.get("fact_key")
        if key not in ("is_combust", "is_debilitated", "is_exalted"):
            continue
        result.setdefault(planet, {})[key] = (f.get("fact_value_text") or "").lower() == "true"
    return result


def _debilitated_without_nbry(
    planet: str, special_states: dict[str, dict[str, bool]], nbry_findings: list[dict[str, Any]],
) -> bool:
    """True iff `planet` is debilitated per L1 facts AND has no firing
    classical neecha-bhanga rule recorded in this build's NBRY findings."""
    if not special_states.get(planet, {}).get("is_debilitated"):
        return False
    cancelled = {f["planet"] for f in nbry_findings if f.get("rules_fired")}
    return planet not in cancelled


# ── Detector 1: dhana_yoga_house_lords (CR-56) ─────────────────────────────────

DHANA_HOUSE_LORD_HOUSES: tuple[int, ...] = (1, 2, 5, 9, 11)


def _detect_dhana_yoga_house_lords(
    state: ChartState, special_states: dict[str, dict[str, bool]],
) -> dict[str, Any] | None:
    for h1 in (2, 11):
        for h2 in DHANA_HOUSE_LORD_HOUSES:
            if h2 == h1:
                continue
            hit = _check_house_lord_association(state, h1, h2)
            if not hit:
                continue
            if any(h in DUSTHANAS for h in hit["placement_houses"]):
                continue  # meeting house is a dusthana — formation gate fails
            return {
                "constituent_planets": hit["lords"],
                "constituent_houses": hit["placement_houses"],
                "houses_ruled": sorted({h1, h2}),
                "association_mode": hit["association_mode"],
            }
    return None


def _cancel_dhana_yoga_house_lords(
    finding: dict[str, Any], state: ChartState,
    special_states: dict[str, dict[str, bool]], nbry_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    affected = [
        p for p in finding["constituent_planets"]
        if special_states.get(p, {}).get("is_combust")
        or _debilitated_without_nbry(p, special_states, nbry_findings)
    ]
    ref = "bphs:ch41_dhana_yoga_adhyaya:lord_affliction"
    if affected:
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": f"lord_combust_or_uncancelled_debility:{','.join(affected)}",
            "bhanga_na_reason": None,
            "citation_ref": ref,
            "citation_human": (
                "BPHS Ch.41 (Dhana Yoga adhyaya): a yoga-forming house lord that is "
                f"combust or debilitated without classical neecha-bhanga ({', '.join(affected)}) "
                "demotes the yoga — never silently served at full strength."
            ),
        }
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "bhanga_na_reason": None,
        "citation_ref": ref,
        "citation_human": "Neither constituent lord is combust or uncancelled-debilitated.",
    }


# ── Detector 2: raja_yoga_kendra_trikona (CR-56) ───────────────────────────────

def _detect_raja_yoga_kendra_trikona(
    state: ChartState, special_states: dict[str, dict[str, bool]],
) -> dict[str, Any] | None:
    hit = _check_kendra_trikona_raja(state)
    if not hit:
        return None
    if any(h in DUSTHANAS for h in hit["placement_houses"]):
        return None
    return {
        "constituent_planets": hit["lords"],
        "constituent_houses": hit["placement_houses"],
        "association_mode": hit["association_mode"],
    }


def _cancel_raja_yoga_kendra_trikona(
    finding: dict[str, Any], state: ChartState,
    special_states: dict[str, dict[str, bool]], nbry_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    affected = [
        p for p in finding["constituent_planets"]
        if special_states.get(p, {}).get("is_combust")
        or _debilitated_without_nbry(p, special_states, nbry_findings)
    ]
    ref = "bphs:ch39_raja_yoga_adhyaya:lord_affliction"
    if affected:
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": f"lord_combust_or_uncancelled_debility:{','.join(affected)}",
            "bhanga_na_reason": None,
            "citation_ref": ref,
            "citation_human": (
                "BPHS Ch.39 (Raja Yoga adhyaya): a kendra/trikona lord that is combust "
                f"or debilitated without classical neecha-bhanga ({', '.join(affected)}) "
                "demotes the yoga."
            ),
        }
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "bhanga_na_reason": None,
        "citation_ref": ref,
        "citation_human": "Neither constituent lord is combust or uncancelled-debilitated.",
    }


# ── Detector 3: budha_aditya (cancellation-only integration — see header) ─────

def _detect_budha_aditya(
    state: ChartState, special_states: dict[str, dict[str, bool]],
) -> dict[str, Any] | None:
    sun_h = _house_of_planet("sun", state)
    mer_h = _house_of_planet("mercury", state)
    if sun_h and mer_h and sun_h == mer_h:
        return {"constituent_planets": ["sun", "mercury"], "constituent_houses": [sun_h]}
    return None


BUDHA_ADITYA_COMBUSTION_CITATION_REF = "bphs:budha_aditya:combustion_cancels"


def _cancel_budha_aditya(
    finding: dict[str, Any] | None, state: ChartState | None,
    special_states: dict[str, dict[str, bool]], nbry_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    mercury_combust = special_states.get("mercury", {}).get("is_combust", False)
    if mercury_combust:
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": "mercury_combust",
            "bhanga_na_reason": None,
            "citation_ref": BUDHA_ADITYA_COMBUSTION_CITATION_REF,
            "citation_human": (
                "Mercury within its classical combustion orb of the Sun cancels "
                "Budha-Aditya — the union becomes plain combustion, not the yoga."
            ),
        }
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "bhanga_na_reason": None,
        "citation_ref": BUDHA_ADITYA_COMBUSTION_CITATION_REF,
        "citation_human": "Mercury is outside its combustion orb — Budha-Aditya stands uncancelled.",
    }


def _budha_aditya_bhanga_handler(
    *, special_states: dict[str, dict[str, bool]] | None = None, **_ignored: Any,
) -> dict[str, Any]:
    """_BHANGA_EVALUATORS entry for budha_aditya (registered below) — real
    combustion-based cancellation for the ALREADY-FIRING catalog relation
    (see module header for why this doesn't go through the detector-insert
    loop)."""
    verdict = _cancel_budha_aditya(None, None, special_states or {}, [])
    return {**verdict, "findings": []}


# ── Detector 4: sarasvati_yoga (CR-56) ─────────────────────────────────────────

SARASVATI_HOUSES: frozenset[int] = frozenset(KENDRAS | TRIKONAS | {2})


def _detect_sarasvati_yoga(
    state: ChartState, special_states: dict[str, dict[str, bool]],
) -> dict[str, Any] | None:
    planets = ("jupiter", "venus", "mercury")
    houses: dict[str, int] = {}
    for p in planets:
        h = _house_of_planet(p, state)
        if h is None or h not in SARASVATI_HOUSES:
            return None
        houses[p] = h
    jup_sign = state.planet_sign.get("jupiter")
    if not jup_sign or not _check_dignity("jupiter", jup_sign, ["own", "exalted"]):
        # The classical "or friendly sign" disjunct is not evaluated — no
        # ratified planetary-friendship table exists in this writer (honest
        # floor, B.10 — not a fabricated approximation).
        return None
    return {
        "constituent_planets": list(planets),
        "constituent_houses": sorted(set(houses.values())),
    }


def _cancel_sarasvati_yoga(
    finding: dict[str, Any], state: ChartState,
    special_states: dict[str, dict[str, bool]], nbry_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    afflicted = [
        p for p in finding["constituent_planets"]
        if special_states.get(p, {}).get("is_debilitated") or special_states.get(p, {}).get("is_combust")
    ]
    ref = "bphs:sarasvati_yoga:constituent_affliction_cancels"
    if afflicted:
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": f"constituent_debilitated_or_combust:{','.join(afflicted)}",
            "bhanga_na_reason": None,
            "citation_ref": ref,
            "citation_human": f"A constituent graha ({', '.join(afflicted)}) is debilitated or combust — Sarasvati Yoga is cancelled.",
        }
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "bhanga_na_reason": None,
        "citation_ref": ref,
        "citation_human": "No constituent graha is debilitated or combust.",
    }


# ── Detector 5: lakshmi_yoga (CR-56; existing catalog id, floored path never fires) ──

def _detect_lakshmi_yoga(
    state: ChartState, special_states: dict[str, dict[str, bool]],
) -> dict[str, Any] | None:
    lord9 = _lord_of_house(state, 9)
    if not lord9:
        return None
    h9lord = _house_of_planet(lord9, state)
    if h9lord is None or h9lord not in (KENDRAS | TRIKONAS):
        return None
    sign9lord = state.planet_sign.get(lord9)
    if not sign9lord or not _check_dignity(lord9, sign9lord, ["own", "exalted"]):
        return None
    venus_sign = state.planet_sign.get("venus")
    if not venus_sign or not _check_dignity("venus", venus_sign, ["own", "exalted"]):
        return None
    if special_states.get("venus", {}).get("is_combust"):
        return None
    venus_h = _house_of_planet("venus", state)
    houses = sorted({h for h in (h9lord, venus_h) if h is not None})
    return {"constituent_planets": sorted({lord9, "venus"}), "constituent_houses": houses}


def _cancel_lakshmi_yoga(
    finding: dict[str, Any], state: ChartState,
    special_states: dict[str, dict[str, bool]], nbry_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    ref = "bphs:lakshmi_yoga:venus_affliction_cancels"
    if special_states.get("venus", {}).get("is_debilitated") or special_states.get("venus", {}).get("is_combust"):
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": "venus_debilitated_or_combust",
            "bhanga_na_reason": None,
            "citation_ref": ref,
            "citation_human": "Venus is debilitated or combust — Lakshmi Yoga is cancelled.",
        }
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "bhanga_na_reason": None,
        "citation_ref": ref,
        "citation_human": "Venus is neither debilitated nor combust (formation already requires own/exalted, non-combust).",
    }


# ── Detector 6: vipareeta_raja_yoga (CR-56) ────────────────────────────────────

def _detect_vipareeta_raja_yoga(
    state: ChartState, special_states: dict[str, dict[str, bool]],
) -> dict[str, Any] | None:
    for h in sorted(DUSTHANAS):
        hit = _check_lord_in_houses(state, h, DUSTHANAS)
        if hit:
            return {
                "constituent_planets": hit["lords"],
                "constituent_houses": hit["placement_houses"],
                "source_house": h,
            }
    return None


def _cancel_vipareeta_raja_yoga(
    finding: dict[str, Any], state: ChartState,
    special_states: dict[str, dict[str, bool]], nbry_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    ref = "phaladeepika:ch7:vipareeta_dilution"
    lords = finding.get("constituent_planets") or []
    lord = lords[0] if lords else None
    if not lord:
        return {
            "bhanga_active": None, "bhanga_rule_fired": None,
            "bhanga_na_reason": "no resolvable dusthana lord to check dilution against",
            "citation_ref": ref, "citation_human": None,
        }
    lord_house = _house_of_planet(lord, state)
    dusthana_lord_set = {_lord_of_house(state, h) for h in DUSTHANAS}
    diluted_by: list[str] = []
    if lord_house is not None:
        for other in state.planets_in_house(lord_house):
            if other != lord and other not in dusthana_lord_set and other not in diluted_by:
                diluted_by.append(other)
        for other, oh in state.planet_house.items():
            if other == lord or other in dusthana_lord_set or other in diluted_by:
                continue
            if _nb_aspects_house(other, oh, lord_house):
                diluted_by.append(other)
    exalted_in_dusthana = bool(special_states.get(lord, {}).get("is_exalted"))
    grounds: list[str] = []
    if diluted_by:
        grounds.append(f"conjunct_or_aspected_by_non_dusthana_lord:{','.join(sorted(diluted_by))}")
    if exalted_in_dusthana:
        grounds.append("exalted_in_dusthana_nuance")
    if grounds:
        return {
            "bhanga_active": True,
            "bhanga_rule_fired": ";".join(grounds),
            "bhanga_na_reason": None,
            "citation_ref": ref,
            "citation_human": (
                "Phaladeepika Ch.7: the dusthana lord's Vipareeta effect is diluted "
                f"({'; '.join(grounds)}) — recorded, not silently voided."
            ),
        }
    return {
        "bhanga_active": False,
        "bhanga_rule_fired": None,
        "bhanga_na_reason": None,
        "citation_ref": ref,
        "citation_human": "No classical dilution ground found — Vipareeta Raja Yoga stands undiluted.",
    }


# Detector registry — every entry has a non-None cancellation callable
# (mandatory per the Lane 3 brief, even where the practical verdict is
# usually False/None; see individual cancellation functions above).
YOGA_DETECTORS: dict[str, DetectorSpec] = {
    "dhana_yoga_house_lords": DetectorSpec(
        yoga_id="dhana_yoga_house_lords",
        detect=_detect_dhana_yoga_house_lords,
        cancellation=_cancel_dhana_yoga_house_lords,
        citation_ref="bphs:ch41_dhana_yoga_adhyaya:house_lord_family",
        citation_human="BPHS Ch.41 (Dhana Yoga adhyaya): association among the lords of 1/2/5/9/11 including the 2nd or 11th lord.",
    ),
    "raja_yoga_kendra_trikona": DetectorSpec(
        yoga_id="raja_yoga_kendra_trikona",
        detect=_detect_raja_yoga_kendra_trikona,
        cancellation=_cancel_raja_yoga_kendra_trikona,
        citation_ref="bphs:ch39_raja_yoga_adhyaya:kendra_trikona",
        citation_human="BPHS Ch.39 (Raja Yoga adhyaya): any kendra lord associated with any trikona lord.",
    ),
    "budha_aditya": DetectorSpec(
        yoga_id="budha_aditya",
        detect=_detect_budha_aditya,
        cancellation=_cancel_budha_aditya,
        citation_ref=BUDHA_ADITYA_COMBUSTION_CITATION_REF,
        citation_human="Sun and Mercury conjunct in one house; cancelled if Mercury is combust.",
    ),
    "sarasvati_yoga": DetectorSpec(
        yoga_id="sarasvati_yoga",
        detect=_detect_sarasvati_yoga,
        cancellation=_cancel_sarasvati_yoga,
        citation_ref="bphs:sarasvati_yoga:formation",
        citation_human="Jupiter, Venus, Mercury each in kendra/trikona/2nd; Jupiter own/exalted.",
    ),
    "lakshmi_yoga": DetectorSpec(
        yoga_id="lakshmi_yoga",
        detect=_detect_lakshmi_yoga,
        cancellation=_cancel_lakshmi_yoga,
        citation_ref="bphs:lakshmi_yoga:formation",
        citation_human="9th lord own/exalted in kendra/trikona, with Venus own/exalted and non-combust.",
    ),
    "vipareeta_raja_yoga": DetectorSpec(
        yoga_id="vipareeta_raja_yoga",
        detect=_detect_vipareeta_raja_yoga,
        cancellation=_cancel_vipareeta_raja_yoga,
        citation_ref="phaladeepika:ch7:vipareeta_formation",
        citation_human="Phaladeepika Ch.7: a dusthana lord (6th/8th/12th) placed in a dusthana.",
    ),
}

# Registry hygiene: register budha_aditya's mandatory cancellation through the
# existing R6A.1 _BHANGA_EVALUATORS extension point (see module header for
# why — its formation already fires via the pre-existing catalog relation).
_BHANGA_EVALUATORS["budha_aditya"] = _budha_aditya_bhanga_handler

# Canonical_ids the detector loop (build_ga_yoga_substep) inserts its OWN
# ga_yoga_firings row for. budha_aditya is deliberately excluded — see header.
DETECTOR_INSERT_IDS: tuple[str, ...] = (
    "dhana_yoga_house_lords",
    "raja_yoga_kendra_trikona",
    "sarasvati_yoga",
    "lakshmi_yoga",
    "vipareeta_raja_yoga",
)


# ── Build-time wiring: positions extraction + NBRY firing row ──────────────────

def _d1_positions_from_state(state: ChartState) -> dict[str, dict[str, Any]]:
    """Project ChartState into the {planet: {sign, house}} shape the NBRY
    rules consume (7 classical grahas; houses lagna-relative)."""
    positions: dict[str, dict[str, Any]] = {}
    for planet in NBRY_CLASSICAL_GRAHAS:
        sign = state.planet_sign.get(planet)
        house = _house_of_planet(planet, state)
        if sign and house:
            positions[planet] = {"sign": sign, "house": int(house)}
    return positions


def _load_d9_positions(conn: Any, chart_id: str, ayanamsha_id: str) -> dict[str, dict[str, Any]]:
    """Load D9 (navamsha) positions from chart_divisionals via the existing
    ga_structural_writer._load_varga_positions helper (lazy import — that
    module pulls in the pyjhora adapter, which this writer does not otherwise
    need at import time). Returns {} if D9 data is unavailable — NBRY then
    evaluates on D1 alone (honest degradation, logged)."""
    try:
        from ga_writers.ga_structural_writer import _load_varga_positions
        raw = _load_varga_positions(conn, chart_id, ayanamsha_id, "D9")
    except Exception as exc:
        logger.warning(
            "[ga_yoga_writer] D9 varga positions unavailable for chart=%s ayanamsha=%s: %s "
            "— NBRY evaluated on D1 only", chart_id, ayanamsha_id, exc,
        )
        return {}
    positions: dict[str, dict[str, Any]] = {}
    for graha, data in raw.items():
        name = graha.lower()
        if name in NBRY_CLASSICAL_GRAHAS and data.get("sign") and data.get("house"):
            positions[name] = {"sign": str(data["sign"]).lower(), "house": int(data["house"])}
    return positions


def _build_nbry_firing(
    cur: Any,
    chart_id: str,
    build_uuid: str,
    ayanamsha_id: str,
    state: ChartState,
    d1_positions: dict[str, dict[str, Any]],
    d9_positions: dict[str, dict[str, Any]],
    family_map: dict[str, list[str]],
) -> int:
    """Evaluate NBRY for this (chart, ayanamsha) and insert at most ONE
    ga_yoga_firings row (table is UNIQUE on chart/ayanamsha/yoga_canonical_id
    — multiple planet/varga findings merge into that row). Returns rows
    inserted (0 or 1). Never commits — caller owns the transaction."""
    bhanga_active, rule_fired, citation_ref, citation_human, findings = evaluate_nbry(
        d1_positions, d9_positions or None,
    )

    # CR-59 grounds ledger — every rule checked for every debilitated graha in
    # D1 (+ D9 when available), fired or not. Computed regardless of whether
    # NBRY ultimately fires; only persisted (below) when a row is written,
    # per the brief's "minimum bar: any NBRY verdict served downstream must
    # be traceable to its checked grounds" (grounds live on the fired row).
    grounds_ledger = _nbry_grounds_ledger(d1_positions, "D1", navamsa_positions=d9_positions or None)
    if d9_positions:
        grounds_ledger += _nbry_grounds_ledger(d9_positions, "D9")

    if not bhanga_active:
        if grounds_ledger:
            logger.info(
                "[ga_yoga_writer] NBRY grounds-checked, not fired: chart=%s ayanamsha=%s "
                "debilitated_grahas=%s (no cited rule fired for any — no row written)",
                chart_id, ayanamsha_id, [g["planet"] + "@" + g["varga"] for g in grounds_ledger],
            )
        return 0  # yoga does not form — no row (uncancelled debilitations stay uncancelled)

    constituent_planets: list[str] = []
    constituent_houses: list[int] = []
    max_rules_fired = 0
    for f in findings:
        max_rules_fired = max(max_rules_fired, len(f["rules_fired"]))
        for p in [f["planet"]] + [
            sp for r in f["rules_fired"] for sp in r.get("supporting_planets", [])
        ]:
            if p not in constituent_planets:
                constituent_planets.append(p)
        if f["varga"] == "D1":
            h = d1_positions.get(f["planet"], {}).get("house")
            if h and h not in constituent_houses:
                constituent_houses.append(h)

    # Grade: fraction of the 5 classical rules fired for the strongest finding.
    # Rule 5 is floored (can never fire) so the ceiling is honestly 4/5.
    strength = round(max_rules_fired / NBRY_TOTAL_RULES, 4)

    # constituent_fact_ids resolve to chart_facts (L1 authority). D9 findings
    # anchor to the same grahas' D1 chart_facts rows — the D9 numbers live in
    # chart_divisionals, which has no fact_id to cite (documented in
    # citation_human via the @D9 rule tags).
    constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)

    try:
        cur.execute("""
            INSERT INTO ga_yoga_firings (
                chart_id, build_id, ayanamsha_id, yoga_canonical_id,
                fired, constituent_fact_ids, constituent_planets,
                constituent_houses, strength, strength_formula_version,
                partial_formation_pct, is_partial,
                bhanga_active, bhanga_rule_fired, bhanga_na_reason,
                derivation, strength_label, citation_ref, citation_human,
                family_ids, grounds_jsonb, computed_at
            ) VALUES (
                %s, %s::uuid, %s, %s,
                %s, %s::jsonb, %s::jsonb,
                %s::jsonb, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s::jsonb, %s::jsonb, NOW()
            )
        """, (
            chart_id, build_uuid, ayanamsha_id, NBRY_CANONICAL_ID,
            True,
            json.dumps(constituent_fact_ids),
            json.dumps(constituent_planets),
            json.dumps(constituent_houses),
            strength,
            NBRY_STRENGTH_FORMULA_VERSION,
            None, False,
            bhanga_active, rule_fired, None,
            NBRY_STRENGTH_FORMULA_VERSION,
            "computed_extension",
            citation_ref, citation_human,
            json.dumps(family_map.get(NBRY_CANONICAL_ID, [])),
            json.dumps(grounds_ledger),
        ))
        return 1
    except Exception as exc:
        logger.warning(
            "[ga_yoga_writer] NBRY insert failed for chart=%s ayanamsha=%s: %s",
            chart_id, ayanamsha_id, exc,
        )
        return 0


# ── CR-130: Jaimini Karakāṃśa yoga firings ─────────────────────────────────────
#
# Classical basis (Jaimini Sutram, Adhyāya 1 Pāda 2 karakāṃśa-phala; BPHS
# Ch.34 Karakāṃśa-phala adhyāya): the Ātmakāraka (graha with the highest
# degree-in-sign) occupies a navāṃśa (D9) sign — the KARAKĀṂŚA, read as a
# lagna. The soul-purpose reading is taken from the grahas that (a) OCCUPY
# that sign in the rāśi (D1) chart, or (b) cast a Jaimini chara-rāśi-dṛṣṭi
# (sign aspect) upon it. Each such graha stamps its karaka significations on
# the native's dharma/vocation.
#
# L1-authority (§N.5): the karakāṃśa sign and the Ātmakāraka identity are READ
# from chart_facts (fact_category='karakamsa_position', written by
# ga_sensitive_writer via the 7-graha Parāśari reckoning) — this detector never
# recomputes them. The graha's D1 sign is the same ChartState.planet_sign the
# rest of this writer consumes. No fabricated placements (B.10).
#
# Aspect model: Jaimini chara-rāśi-dṛṣṭi (sign aspects), NOT graha (Parāśari
# house) aspects — because these are Jaimini-school yogas. The three rules
# (Jaimini Sutram 1.1.9–11): a movable (chara) sign aspects the fixed (sthira)
# signs except the one adjacent to it (2nd from it); a fixed sign aspects the
# movable signs except the one adjacent to it (12th from it); a dual
# (dvisvabhāva) sign aspects the other three dual signs. Movable⇄adjacent-fixed
# is a mutual NON-aspect (symmetric), so the rule is self-consistent.

# canonical_id → (planet, allow_aspect). Rahu's catalog row carries no
# `or_aspect` clause (its rāśi-dṛṣṭi is not classically settled) — occupation
# only. Mercury is intentionally ABSENT: l0_yogas.py §3.7 defines no
# jaimini_karakamsha_mercury row, so firing one would be fabrication (B.10).
KARAKAMSHA_YOGAS: dict[str, tuple[str, bool]] = {
    "jaimini_karakamsha_sun": ("sun", True),
    "jaimini_karakamsha_moon": ("moon", True),
    "jaimini_karakamsha_mars": ("mars", True),
    "jaimini_karakamsha_jupiter": ("jupiter", True),
    "jaimini_karakamsha_venus": ("venus", True),
    "jaimini_karakamsha_saturn": ("saturn", True),
    "jaimini_karakamsha_rahu": ("rahu", False),
}

# Per-graha classical effect phrase (verbatim significations_text from
# l0_yogas.py §3.7) — folded into citation_human so every firing row carries
# its own cited karaka reading, not a generic label.
KARAKAMSHA_EFFECT: dict[str, str] = {
    "sun": "government service, employment by royalty or authority",
    "moon": "trade in liquids, agriculture, employment under authority",
    "mars": "work with weapons, fire or metals; valour (engineering, surgery)",
    "jupiter": "learning in the Vedas, eloquence, piety, favour of rulers",
    "venus": "wealth, luxury, marital happiness, skill in the arts",
    "saturn": "laborious work, service, iron/machinery trades, austerity",
    "rahu": "technical, foreign, or unconventional profession",
}

# Jaimini classical citation shared by the family (the per-planet effect and
# occupation/aspect mode are appended per firing).
KARAKAMSHA_CITATION_REF = "jaimini_sutram:1.2_karakamsa_phala;bphs:ch34_karakamsa_phala_adhyaya"


def _jaimini_rasi_aspects(from_sign: str) -> set[str]:
    """Signs that `from_sign` aspects by Jaimini chara-rāśi-dṛṣṭi (sign
    aspects). Jaimini Sutram 1.1.9–11. Empty set for an unknown sign."""
    s = from_sign.lower()
    idx = SIGN_NUMBERS.get(s)
    if idx is None:
        return set()
    if s in MOVABLE_SIGNS:
        # aspects the fixed signs except the adjacent one (2nd from it)
        adjacent_fixed = SIGN_NAMES[(idx % 12) + 1]
        return FIXED_SIGNS - {adjacent_fixed}
    if s in FIXED_SIGNS:
        # aspects the movable signs except the adjacent one (12th from it)
        adjacent_movable = SIGN_NAMES[((idx - 2) % 12) + 1]
        return MOVABLE_SIGNS - {adjacent_movable}
    # dual sign — aspects the other dual signs
    return DUAL_SIGNS - {s}


def _karakamsha_reaches(planet_sign: str, karakamsha_sign: str, allow_aspect: bool) -> str | None:
    """Return 'occupation', 'aspect', or None describing how a graha in
    `planet_sign` relates to the `karakamsha_sign`."""
    if planet_sign == karakamsha_sign:
        return "occupation"
    if allow_aspect and karakamsha_sign in _jaimini_rasi_aspects(planet_sign):
        return "aspect"
    return None


def _build_karakamsha_firings(
    cur: Any,
    chart_id: str,
    build_uuid: str,
    ayanamsha_id: str,
    state: ChartState,
    shadbala_map: dict[str, dict[str, float]],
    family_map: dict[str, list[str]],
) -> int:
    """Evaluate the 7 Jaimini karakāṃśa planet yogas for this (chart,
    ayanamsha) and insert one ga_yoga_firings row per graha that occupies or
    (chara-rāśi-dṛṣṭi) aspects the karakāṃśa sign. Returns rows inserted.
    Never commits — caller owns the transaction.

    Honest degradation: if chart_facts carries no karakāṃśa sign for this
    ayanamsha (ga_sensitive not built), no karakāṃśa firing is written and the
    condition is logged — never fabricated."""
    kshign = state.karakamsha_sign
    if not kshign or kshign not in SIGN_NUMBERS:
        logger.info(
            "[ga_yoga_writer] karakāṃśa sign unavailable for chart=%s ayanamsha=%s "
            "(karakamsa_position not in chart_facts) — no karakāṃśa firings",
            chart_id, ayanamsha_id,
        )
        return 0

    rows_inserted = 0
    for cid, (planet, allow_aspect) in KARAKAMSHA_YOGAS.items():
        planet_sign = state.planet_sign.get(planet)
        if not planet_sign:
            continue
        mode = _karakamsha_reaches(planet_sign, kshign, allow_aspect)
        if mode is None:
            continue

        house = _house_of_planet(planet, state)
        constituent_houses = [house] if house else []

        # constituent_fact_ids resolve to chart_facts (L1 authority, B.3):
        # the graha's own D1 position row + the karakāṃśa_position row that
        # supplies the karakāṃśa sign. Both MUST resolve.
        constituent_fact_ids = state.fact_ids_for_planets([planet])
        if state.karakamsha_fact_id:
            constituent_fact_ids = constituent_fact_ids + [state.karakamsha_fact_id]

        # Strength: constituent_bala_v1 (JL-012/J3), the single ratified
        # non-fabricated derivation. NULL for Rahu (no classical shadbala).
        strength, derivation, strength_label, _bala_ref, _bala_human = (
            _compute_constituent_bala_strength(
                [planet], shadbala_map, cid, chart_id, ayanamsha_id,
            )
        )

        mode_text = (
            f"placed in the karakāṃśa ({kshign.title()})"
            if mode == "occupation"
            else f"casting Jaimini chara-rāśi-dṛṣṭi on the karakāṃśa ({kshign.title()}) from {planet_sign.title()}"
        )
        citation_human = (
            f"Jaimini Sutram 1.2 (karakāṃśa-phala) / BPHS Ch.34: {planet.title()} "
            f"{mode_text} gives {KARAKAMSHA_EFFECT.get(planet, 'its karaka significations')}. "
            f"Ātmakāraka={(state.atmakaraka_graha or 'n/a').title()}; karakāṃśa reckoned "
            f"as the D9 sign of the Ātmakāraka (ga_sensitive karakamsa_position, §N.5). "
            f"Aspect model: Jaimini chara-rāśi-dṛṣṭi (sign aspects), not Parāśari graha aspects."
        )
        citation_ref = f"{KARAKAMSHA_CITATION_REF}:{planet}_{mode}"

        # No classical cancellation (bhanga) rule is defined for karakāṃśa
        # occupation/aspect yogas — honest NULL-with-reason floor (B.10),
        # matching this writer's bhanga discipline elsewhere.
        bhanga_na_reason = (
            "No classical bhanga rule for Jaimini karakāṃśa occupation/aspect yogas "
            "in the Jaimini Sutram; honest NULL floor (B.10)."
        )

        try:
            cur.execute("""
                INSERT INTO ga_yoga_firings (
                    chart_id, build_id, ayanamsha_id, yoga_canonical_id,
                    fired, constituent_fact_ids, constituent_planets,
                    constituent_houses, strength, strength_formula_version,
                    partial_formation_pct, is_partial,
                    bhanga_active, bhanga_rule_fired, bhanga_na_reason,
                    derivation, strength_label, citation_ref, citation_human,
                    family_ids, computed_at
                ) VALUES (
                    %s, %s::uuid, %s, %s,
                    %s, %s::jsonb, %s::jsonb,
                    %s::jsonb, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, NOW()
                )
            """, (
                chart_id, build_uuid, ayanamsha_id, cid,
                True,
                json.dumps(constituent_fact_ids),
                json.dumps([planet]),
                json.dumps(constituent_houses),
                strength,
                derivation or STRENGTH_FORMULA_VERSION,
                None, False,
                None, None, bhanga_na_reason,
                derivation, strength_label, citation_ref, citation_human,
                json.dumps(family_map.get(cid, [])),
            ))
            rows_inserted += 1
        except Exception as exc:
            logger.warning(
                "[ga_yoga_writer] karakāṃśa insert failed for yoga=%s chart=%s ayanamsha=%s: %s",
                cid, chart_id, ayanamsha_id, exc,
            )
    logger.info(
        "[ga_yoga_writer] karakāṃśa firings: chart=%s ayanamsha=%s karakāṃśa=%s rows=%d",
        chart_id, ayanamsha_id, kshign, rows_inserted,
    )
    return rows_inserted


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
    - strength = mean normalized shadbala of constituent grahas (constituent_bala_v1,
      JL-012/J3), or NULL if no constituent has resolvable shadbala (not fabricated).
    - bhanga_active = NULL + bhanga_na_reason unless the yoga is kemadruma_aristha
      (whose bhanga is already gated into its firing condition, not duplicated
      here) or has a registered real classical rule in _BHANGA_EVALUATORS
      (R6A.1: neecha_bhanga_raja_yoga — evaluated per-varga D1+D9).
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

    # JL-012 / J3: shadbala source for the constituent_bala_v1 strength
    # derivation — loaded once per substep, applied per fired yoga below.
    shadbala_map = _load_shadbala_map(conn, chart_id, ayanamsha_id)

    # 2. Parse chart state
    state = ChartState(facts)

    # R6A.1: positions for the generic bhanga evaluator + NBRY (D1 from the
    # parsed state; D9 from chart_divisionals via ga_structural's loader).
    d1_positions = _d1_positions_from_state(state)
    d9_positions = _load_d9_positions(conn, chart_id, ayanamsha_id)

    # Lane 3 (Night-1): special-state facts (combust/debilitated/exalted) for
    # the detector-registry cancellation checks — read-only L1 consumption.
    special_states = _load_special_states(facts)

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

            # ── JL-012 / J3: constituent_bala_v1 strength ──────────────────────
            # Supersedes whatever _evaluate_yoga computed internally (e.g. the
            # pancha_mahapurusha branch's ad hoc kendra/exaltation bonus) with
            # the single ratified, non-fabricated formula applied uniformly
            # across every yoga type: mean normalized shadbala of constituent
            # grahas. This is what fixes strength being NULL for all
            # solar/positional (non-mahapurusha) yogas.
            (
                strength, derivation, strength_label, citation_ref, citation_human,
            ) = _compute_constituent_bala_strength(
                result["constituent_planets"], shadbala_map, cid, chart_id, ayanamsha_id,
            )
            strength_formula_version = derivation or result["strength_formula_version"]

            # ── JL-012 / J3 + R6A.1: bhanga_active ─────────────────────────────
            # Kemadruma's cancellation is already gated into its own firing
            # condition (and, upstream, ga_structural_writer's KEMADRUMA branch)
            # — leave its bhanga_active exactly as _evaluate_yoga set it. Every
            # other yoga routes through the generic bhanga evaluator (Y-5):
            # yogas with a registered REAL classical cancellation rule get a
            # verdict; everything else keeps the honest NULL + reason floor
            # (B.10 — identical wording to pre-R6A.1 behavior).
            bhanga_rule_fired = result["bhanga_rule_fired"]
            if cid == KEMADRUMA_CANONICAL_ID:
                bhanga_active = result["bhanga_active"]
                bhanga_na_reason = None
            else:
                bhanga = evaluate_bhanga(
                    cid,
                    d1_positions=d1_positions,
                    d9_positions=d9_positions or None,
                    constituent_planets=result["constituent_planets"],
                    has_catalog_cancellation=bool(yoga.get("cancellation_conditions")),
                    special_states=special_states,
                )
                bhanga_active = bhanga["bhanga_active"]
                bhanga_na_reason = bhanga["bhanga_na_reason"]
                if bhanga["bhanga_rule_fired"]:
                    bhanga_rule_fired = bhanga["bhanga_rule_fired"]

            try:
                cur.execute("""
                    INSERT INTO ga_yoga_firings (
                        chart_id, build_id, ayanamsha_id, yoga_canonical_id,
                        fired, constituent_fact_ids, constituent_planets,
                        constituent_houses, strength, strength_formula_version,
                        partial_formation_pct, is_partial,
                        bhanga_active, bhanga_rule_fired, bhanga_na_reason,
                        derivation, strength_label, citation_ref, citation_human,
                        family_ids, computed_at
                    ) VALUES (
                        %s, %s::uuid, %s, %s,
                        %s, %s::jsonb, %s::jsonb,
                        %s::jsonb, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
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
                    strength,
                    strength_formula_version,
                    result["partial_formation_pct"],
                    result["is_partial"],
                    bhanga_active,
                    bhanga_rule_fired,
                    bhanga_na_reason,
                    derivation,
                    strength_label,
                    citation_ref,
                    citation_human,
                    json.dumps(family_ids),
                ))
                rows_inserted += 1
            except Exception as exc:
                logger.warning(
                    "[ga_yoga_writer] insert failed for yoga=%s chart=%s ayanamsha=%s: %s",
                    cid, chart_id, ayanamsha_id, exc,
                )

        # ── R6A.1: Neecha Bhanga Raja Yoga firing (D1 + D9) ────────────────────
        # NBRY's catalog formation relation
        # ("debilitated_planet_with_cancelled_debility") is in _evaluate_yoga's
        # conservative skip-list, so it never fires via the catalog loop above —
        # it is evaluated here with real per-varga bhanga rules instead.
        rows_inserted += _build_nbry_firing(
            cur, chart_id, build_uuid, ayanamsha_id, state,
            d1_positions, d9_positions, family_map,
        )

        # ── Lane 3 (Night-1): detector-registry firings (CR-56) ────────────────
        # Runs AFTER the catalog pass + NBRY, exactly like NBRY's own insert.
        # Only the ids in DETECTOR_INSERT_IDS write a row here — budha_aditya
        # is intentionally excluded (module header: it already fires via the
        # catalog loop above; only its cancellation is new, wired through
        # _BHANGA_EVALUATORS and already applied in that loop).
        _, _, _, _, nbry_findings_for_detectors = evaluate_nbry(d1_positions, d9_positions or None)
        for det_id in DETECTOR_INSERT_IDS:
            spec = YOGA_DETECTORS[det_id]
            catalog_row = next((y for y in yoga_catalog if y["canonical_id"] == det_id), None)
            if catalog_row is None:
                logger.warning(
                    "[ga_yoga_writer] detector %s has no brahma_yoga_catalog row "
                    "(migration not applied?) — skipping", det_id,
                )
                continue

            finding = spec.detect(state, special_states)
            if finding is None:
                continue

            verdict = spec.cancellation(finding, state, special_states, nbry_findings_for_detectors)
            constituent_planets = finding["constituent_planets"]
            constituent_houses = finding.get("constituent_houses", [])
            constituent_fact_ids = state.fact_ids_for_planets(constituent_planets)

            (
                strength, derivation, strength_label, bala_citation_ref, bala_citation_human,
            ) = _compute_constituent_bala_strength(
                constituent_planets, shadbala_map, det_id, chart_id, ayanamsha_id,
            )
            # Prefer the constituent_bala_v1 strength citation when resolvable;
            # otherwise fall back to the detector's own formation citation so
            # the row is never citation-less (writer rail: "Classical citations
            # required on every yoga").
            citation_ref = bala_citation_ref or spec.citation_ref
            citation_human = bala_citation_human or spec.citation_human

            try:
                cur.execute("""
                    INSERT INTO ga_yoga_firings (
                        chart_id, build_id, ayanamsha_id, yoga_canonical_id,
                        fired, constituent_fact_ids, constituent_planets,
                        constituent_houses, strength, strength_formula_version,
                        partial_formation_pct, is_partial,
                        bhanga_active, bhanga_rule_fired, bhanga_na_reason,
                        derivation, strength_label, citation_ref, citation_human,
                        family_ids, computed_at
                    ) VALUES (
                        %s, %s::uuid, %s, %s,
                        %s, %s::jsonb, %s::jsonb,
                        %s::jsonb, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s,
                        %s::jsonb, NOW()
                    )
                """, (
                    chart_id, build_uuid, ayanamsha_id, det_id,
                    True,
                    json.dumps(constituent_fact_ids),
                    json.dumps(constituent_planets),
                    json.dumps(constituent_houses),
                    strength,
                    derivation or STRENGTH_FORMULA_VERSION,
                    None, False,
                    verdict["bhanga_active"], verdict["bhanga_rule_fired"], verdict["bhanga_na_reason"],
                    derivation, strength_label, citation_ref, citation_human,
                    json.dumps(family_map.get(det_id, [])),
                ))
                rows_inserted += 1
            except Exception as exc:
                logger.warning(
                    "[ga_yoga_writer] detector insert failed for yoga=%s chart=%s ayanamsha=%s: %s",
                    det_id, chart_id, ayanamsha_id, exc,
                )

        # ── CR-130: Jaimini karakāṃśa planet yogas ─────────────────────────────
        # Runs AFTER the catalog pass + NBRY + detector registry, exactly like
        # those own inserts. Reads the karakāṃśa sign from chart_facts (L1
        # authority) and writes one firing per graha occupying/aspecting it.
        rows_inserted += _build_karakamsha_firings(
            cur, chart_id, build_uuid, ayanamsha_id, state, shadbala_map, family_map,
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
