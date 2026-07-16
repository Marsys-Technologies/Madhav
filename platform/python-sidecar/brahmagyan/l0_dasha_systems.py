"""
brahmagyan.l0_dasha_systems — L0 Brahmagyan: Classical Dasha System Definitions
================================================================================

Populates three tables per §0.1 contract (Doc 12 brief):
  1. brahma_dasha_systems  — the catalog row (FK target); INSERT FIRST
  2. brahma_ontology       — entity_class='dasha_system' pointer row
  3. reference_dasha_systems — thin pointer row (FK → brahma_dasha_systems)

19 classical dasha systems embedded as hardcoded source-cited data (18
original + narayana, CR-104 / D-2 Lane V-6 addition, 2026-07-16).
ZERO LLM. All period lengths / sequences are attested classical values.

Sources:
  - BPHS Ch.46-50 (Vimshottari, Yogini, conditional nakshatra dashas, Kalachakra)
  - Jaimini Sutram Ch.1 (Chara, Sthira, Niryana Shoola, Brahma, Narayana)

Volume floor: >= 15 rows in brahma_dasha_systems (design aspiration 15-18).
Achieved: 19 rows (all embedded inline).

BRAHMA-BG-0-12
"""
from __future__ import annotations

import json as _json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Source citations ───────────────────────────────────────────────────────────

BPHS_CH46 = "BPHS Ch.46 (Vimshottari Dasha)"
BPHS_CH47 = "BPHS Ch.47 (Tara Chakra & Nakshatra Dashas)"
BPHS_CH48 = "BPHS Ch.48 (Conditional Nakshatra Dashas)"
BPHS_CH49 = "BPHS Ch.49 (Kalachakra & Conditional Dashas)"
BPHS_CH50 = "BPHS Ch.50 (Yogini Dasha)"
JAIMINI_CH1 = "Jaimini Sutram Ch.1 (Upadesa Sutra — Rashi Dasha systems)"

# ── Vimshottari sequence (reused for Yogardha average) ─────────────────────────

VIMSHOTTARI_SEQ = [
    {"ruler": "ketu",    "years": 7},
    {"ruler": "venus",   "years": 20},
    {"ruler": "sun",     "years": 6},
    {"ruler": "moon",    "years": 10},
    {"ruler": "mars",    "years": 7},
    {"ruler": "rahu",    "years": 18},
    {"ruler": "jupiter", "years": 16},
    {"ruler": "saturn",  "years": 19},
    {"ruler": "mercury", "years": 17},
]

ASHTOTTARI_SEQ = [
    {"ruler": "sun",     "years": 6},
    {"ruler": "moon",    "years": 15},
    {"ruler": "mars",    "years": 8},
    {"ruler": "mercury", "years": 17},
    {"ruler": "saturn",  "years": 10},
    {"ruler": "jupiter", "years": 19},
    {"ruler": "rahu",    "years": 12},
    {"ruler": "venus",   "years": 21},
]

# ── Per-system synonyms (for brahma_ontology.synonyms[]) ──────────────────────

_SYNONYMS: dict[str, list[str]] = {
    "vimshottari":        ["vimsottari", "udu dasha", "nakshatra dasha", "vimshottari dasha", "120-year dasha"],
    "ashtottari":         ["ashtottari dasha", "108-year dasha", "conditional nakshatra dasha"],
    "yogini":             ["yogini dasha", "36-year dasha", "mangala dasha cycle"],
    "kalachakra":         ["kalachakra dasha", "100-year dasha", "pada dasha"],
    "chara_jaimini":      ["chara dasha", "movable sign dasha", "jaimini chara"],
    "sthira_dasha":       ["sthira dasha", "fixed sign dasha", "jaimini sthira"],
    "niryana_shoola":     ["shoola dasha", "niryana shoola", "maraka dasha", "trikona shoola"],
    "shodashottari":      ["shodashottari dasha", "116-year dasha"],
    "dwadashottari":      ["dwadashottari dasha", "112-year dasha"],
    "panchottari":        ["panchottari dasha", "105-year dasha"],
    "shatabdika":         ["shatabdika dasha", "100-year conditional dasha"],
    "chaturashiti_sama":  ["chaturashiti sama", "84-year dasha", "chaturashiti"],
    "dwisaptati_sama":    ["dwisaptati sama", "72-year dasha", "dwisaptati"],
    "shashtihayani":      ["shashtihayani dasha", "60-year dasha"],
    "shattrimsha_sama":   ["shattrimsha sama", "36-year conditional dasha"],
    "tara_dasha":         ["tara dasha", "tara chakra dasha", "nakshatra tara"],
    "brahma_dasha":       ["brahma dasha", "jaimini brahma", "brahma graha dasha"],
    "yogardha_dasha":     ["yogardha dasha", "108-year average dasha", "vimshottari ashtottari mean"],
    "narayana":           ["narayana dasha", "narayan dasha", "jaimini narayana", "rashi dasha (narayana)"],
}


def _synonyms(canonical_id: str) -> list[str]:
    return _SYNONYMS.get(canonical_id, [])


# ── The 18 dasha systems ───────────────────────────────────────────────────────

DASHA_SYSTEMS: list[dict[str, Any]] = [
    # ── 1. Vimshottari — universal default; BPHS Ch.46 ────────────────────────
    {
        "canonical_id": "vimshottari",
        "name_sa": "Viṃśottarī",
        "name_en": "Vimshottari Dasha",
        "total_cycle_years": 120,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": VIMSHOTTARI_SEQ,
        "computation_method": "nakshatra_remainder",
        "computation_pseudocode": (
            "1. Find Moon's nakshatra (1-27) and its lord. "
            "2. Balance of starting dasha = (1 - moon_longitude_within_nakshatra / 13°20') × lord_years. "
            "3. Proceed in the fixed Ketu→Venus→Sun→Moon→Mars→Rahu→Jupiter→Saturn→Mercury order; "
            "antardashas subdivide each mahadasha proportionally "
            "(antar_years = maha_years × antar_lord_years / 120)."
        ),
        "conditions_for_use": "Universal default dasha; applicable to all charts. Reckoned from Moon's nakshatra.",
        "classical_citations": [{"text_id": "bphs", "chapter": 46}],
        "source_citation": BPHS_CH46,
        "python_impl_module": "pyjhora.vimsottari",
    },

    # ── 2. Ashtottari — conditional 108-year; BPHS Ch.48 ─────────────────────
    {
        "canonical_id": "ashtottari",
        "name_sa": "Aṣṭottarī",
        "name_en": "Ashtottari Dasha",
        "total_cycle_years": 108,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": ASHTOTTARI_SEQ,
        "computation_method": "nakshatra_remainder_conditional",
        "computation_pseudocode": (
            "8-planet 108-year cycle (Ketu omitted). Starting lord from Moon's nakshatra via the "
            "Ashtottari nakshatra-group mapping; balance computed like Vimshottari. "
            "Conditional applicability per classical rules (e.g. Rahu in a quadrant/trine from "
            "lagna-lord, day birth in Krishna paksha / night in Shukla)."
        ),
        "conditions_for_use": (
            "Conditional (Krishna/Shukla paksha + Rahu placement rules). "
            "Used where applicability conditions are met."
        ),
        "classical_citations": [{"text_id": "bphs", "chapter": 48}],
        "source_citation": BPHS_CH48,
        "python_impl_module": "pyjhora.ashtottari",
    },

    # ── 3. Yogini — 36-year; BPHS Ch.50 ──────────────────────────────────────
    {
        "canonical_id": "yogini",
        "name_sa": "Yoginī",
        "name_en": "Yogini Dasha",
        "total_cycle_years": 36,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": [
            {"ruler": "moon",    "yogini": "Mangala",  "years": 1},
            {"ruler": "sun",     "yogini": "Pingala",  "years": 2},
            {"ruler": "jupiter", "yogini": "Dhanya",   "years": 3},
            {"ruler": "mars",    "yogini": "Bhramari", "years": 4},
            {"ruler": "mercury", "yogini": "Bhadrika", "years": 5},
            {"ruler": "saturn",  "yogini": "Ulka",     "years": 6},
            {"ruler": "venus",   "yogini": "Siddha",   "years": 7},
            {"ruler": "rahu",    "yogini": "Sankata",  "years": 8},
        ],
        "computation_method": "nakshatra_remainder",
        "computation_pseudocode": (
            "8 yoginis, total 1+2+...+8 = 36 years. "
            "Starting yogini = ((nakshatra_number + 3) mod 8), mapping 0→Sankata. "
            "Balance from Moon's position in nakshatra. "
            "Order: Mangala→Pingala→Dhanya→Bhramari→Bhadrika→Ulka→Siddha→Sankata."
        ),
        "conditions_for_use": "Widely used short-cycle dasha, especially for timing and muhurta.",
        "classical_citations": [{"text_id": "bphs", "chapter": 50}],
        "source_citation": BPHS_CH50,
        "python_impl_module": "pyjhora.yogini",
    },

    # ── 4. Kalachakra — 100-year pada-driven; BPHS Ch.49 ─────────────────────
    {
        "canonical_id": "kalachakra",
        "name_sa": "Kālacakra",
        "name_en": "Kalachakra Dasha",
        "total_cycle_years": 100,
        "base_unit": "special",
        "school": "parashari",
        "sequence_jsonb": {
            "type": "nakshatra_pada_driven",
            "note": (
                "Sign sequence (savya/apasavya) determined by Moon's nakshatra-pada; "
                "years per sign from the Kalachakra sign-year table "
                "(Aries/Scorpio 7, Taurus/Libra 16, Gemini/Virgo 9, Cancer/Leo 21, "
                "Capricorn/Aquarius 4, Sagittarius/Pisces 10, other signs as per classical table)."
            ),
        },
        "computation_method": "nakshatra_pada_savya_apasavya",
        "computation_pseudocode": (
            "1. Moon's nakshatra-pada selects the deha/jeeva sign sequence and "
            "savya (direct) vs apasavya (reverse) progression. "
            "2. Each sign's dasha length from the Kalachakra year table. "
            "3. Antardashas follow the same sign progression within each mahadasha."
        ),
        "conditions_for_use": "Powerful but computation-sensitive; used for spiritual/longevity timing.",
        "classical_citations": [{"text_id": "bphs", "chapter": 49}],
        "source_citation": BPHS_CH49,
        "python_impl_module": "pyjhora.kalachakra",
    },

    # ── 5. Chara Dasha (Jaimini) — rashi dasha; Jaimini Sutram Ch.1 ──────────
    {
        "canonical_id": "chara_jaimini",
        "name_sa": "Cara Daśā",
        "name_en": "Chara Dasha (Jaimini)",
        "total_cycle_years": 144,
        "base_unit": "sign_lord",
        "school": "jaimini",
        "sequence_jsonb": {
            "type": "rashi_sequence",
            "note": (
                "Starts from lagna sign; direction by odd/even "
                "(movable→direct, fixed→reverse exceptions); "
                "years per sign = count to the sign's lord minus 1 (1-12)."
            ),
        },
        "computation_method": "jaimini_chara",
        "computation_pseudocode": (
            "1. Start sign = lagna. "
            "2. Direction: if lagna is odd-footed move zodiacally, else anti-zodiacally "
            "(with movable/fixed/dual refinements). "
            "3. Years for a sign = number of signs from the sign to its lord "
            "(counted per direction), minus 1; if lord is in the sign itself = 12. "
            "4. Progress sign-by-sign."
        ),
        "conditions_for_use": "Primary Jaimini rashi dasha; read with arudha & karakas.",
        "classical_citations": [{"text_id": "jaimini_sutram", "chapter": 1}],
        "source_citation": JAIMINI_CH1,
        "python_impl_module": "pyjhora.chara",
    },

    # ── 6. Sthira Dasha (Jaimini) — fixed-period rashi; Jaimini Sutram Ch.1 ──
    {
        "canonical_id": "sthira_dasha",
        "name_sa": "Sthira Daśā",
        "name_en": "Sthira Dasha (Jaimini)",
        "total_cycle_years": 86,
        "base_unit": "sign_lord",
        "school": "jaimini",
        "sequence_jsonb": {
            "type": "rashi_sequence",
            "fixed_years": {"movable": 7, "fixed": 8, "dual": 9},
        },
        "computation_method": "jaimini_sthira",
        "computation_pseudocode": (
            "Fixed sign-year scheme: movable signs 7y, fixed 8y, dual 9y; "
            "sequence from lagna by Jaimini direction rules."
        ),
        "conditions_for_use": "Jaimini rashi dasha with fixed period lengths.",
        "classical_citations": [{"text_id": "jaimini_sutram", "chapter": 1}],
        "source_citation": JAIMINI_CH1,
        "python_impl_module": "pyjhora.sthira",
    },

    # ── 7. Niryana Shoola — longevity/maraka; Jaimini Sutram Ch.1 ─────────────
    {
        "canonical_id": "niryana_shoola",
        "name_sa": "Niryāṇa Śūla",
        "name_en": "Niryana Shoola Dasha",
        "total_cycle_years": 108,
        "base_unit": "sign_lord",
        "school": "jaimini",
        "sequence_jsonb": {
            "type": "rashi_sequence",
            "fixed_years": {"movable": 7, "fixed": 8, "dual": 9},
            "note": "trikona-based; used for longevity/maraka timing",
        },
        "computation_method": "jaimini_shoola",
        "computation_pseudocode": (
            "Trikona-grouped rashi dasha (Shoola = trident); "
            "period lengths by sign modality; "
            "reckoned from the 7th/8th for maraka analysis."
        ),
        "conditions_for_use": "Longevity and death-timing (maraka) analysis.",
        "classical_citations": [{"text_id": "jaimini_sutram", "chapter": 1}],
        "source_citation": JAIMINI_CH1,
        "python_impl_module": "pyjhora.shoola",
    },

    # ── 8. Shodashottari — conditional 116-year; BPHS Ch.48 ──────────────────
    {
        "canonical_id": "shodashottari",
        "name_sa": "Ṣoḍaśottarī",
        "name_en": "Shodashottari Dasha",
        "total_cycle_years": 116,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": [
            {"ruler": "sun",     "years": 11},
            {"ruler": "mars",    "years": 12},
            {"ruler": "jupiter", "years": 13},
            {"ruler": "saturn",  "years": 14},
            {"ruler": "ketu",    "years": 15},
            {"ruler": "moon",    "years": 16},
            {"ruler": "mercury", "years": 17},
            {"ruler": "venus",   "years": 18},
        ],
        "computation_method": "nakshatra_remainder_conditional",
        "computation_pseudocode": (
            "8-lord 116-year conditional cycle; "
            "applicability per birth in Krishna paksha day / Shukla paksha night and lagna conditions; "
            "balance from Moon's nakshatra."
        ),
        "conditions_for_use": "Conditional nakshatra dasha (paksha + lagna rules).",
        "classical_citations": [{"text_id": "bphs", "chapter": 48}],
        "source_citation": BPHS_CH48,
        "python_impl_module": "pyjhora.shodasottari",
    },

    # ── 9. Dwadashottari — conditional 112-year; BPHS Ch.48 ──────────────────
    {
        "canonical_id": "dwadashottari",
        "name_sa": "Dvādaśottarī",
        "name_en": "Dwadashottari Dasha",
        "total_cycle_years": 112,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": [
            {"ruler": "sun",     "years": 7},
            {"ruler": "jupiter", "years": 9},
            {"ruler": "ketu",    "years": 11},
            {"ruler": "mercury", "years": 13},
            {"ruler": "rahu",    "years": 15},
            {"ruler": "mars",    "years": 17},
            {"ruler": "saturn",  "years": 19},
            {"ruler": "moon",    "years": 21},
        ],
        "computation_method": "nakshatra_remainder_conditional",
        "computation_pseudocode": (
            "8-lord 112-year conditional cycle; "
            "applicability per classical lagna/paksha rule (e.g. lagna in Venus-decanate)."
        ),
        "conditions_for_use": "Conditional nakshatra dasha.",
        "classical_citations": [{"text_id": "bphs", "chapter": 48}],
        "source_citation": BPHS_CH48,
        "python_impl_module": "pyjhora.dwadasottari",
    },

    # ── 10. Panchottari — conditional 105-year; BPHS Ch.48 ───────────────────
    {
        "canonical_id": "panchottari",
        "name_sa": "Pañcottarī",
        "name_en": "Panchottari Dasha",
        "total_cycle_years": 105,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": [
            {"ruler": "sun",     "years": 12},
            {"ruler": "mercury", "years": 13},
            {"ruler": "saturn",  "years": 14},
            {"ruler": "mars",    "years": 15},
            {"ruler": "venus",   "years": 16},
            {"ruler": "moon",    "years": 17},
            {"ruler": "jupiter", "years": 18},
        ],
        "computation_method": "nakshatra_remainder_conditional",
        "computation_pseudocode": (
            "7-lord 105-year conditional cycle; "
            "applicability per classical lagna rule (Cancer lagna / specific decanate)."
        ),
        "conditions_for_use": "Conditional nakshatra dasha.",
        "classical_citations": [{"text_id": "bphs", "chapter": 48}],
        "source_citation": BPHS_CH48,
        "python_impl_module": "pyjhora.panchottari",
    },

    # ── 11. Shatabdika — conditional 100-year; BPHS Ch.48 ────────────────────
    {
        "canonical_id": "shatabdika",
        "name_sa": "Śatābdikā",
        "name_en": "Shatabdika Dasha",
        "total_cycle_years": 100,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": [
            {"ruler": "venus",   "years": 5},
            {"ruler": "sun",     "years": 5},
            {"ruler": "moon",    "years": 10},
            {"ruler": "mars",    "years": 10},
            {"ruler": "mercury", "years": 10},
            {"ruler": "jupiter", "years": 20},
            {"ruler": "saturn",  "years": 20},
            {"ruler": "rahu",    "years": 20},
        ],
        "computation_method": "nakshatra_remainder_conditional",
        "computation_pseudocode": (
            "8-lord 100-year conditional cycle (Saptarishi nadi-linked); "
            "applicability per classical condition."
        ),
        "conditions_for_use": "Conditional nakshatra dasha; nadi tradition.",
        "classical_citations": [{"text_id": "bphs", "chapter": 48}],
        "source_citation": BPHS_CH48,
        "python_impl_module": "pyjhora.shatabdika",
    },

    # ── 12. Chaturashiti-sama — conditional 84-year; BPHS Ch.49 ──────────────
    {
        "canonical_id": "chaturashiti_sama",
        "name_sa": "Caturaśīti-sama",
        "name_en": "Chaturashiti-sama Dasha",
        "total_cycle_years": 84,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": {
            "type": "equal_period",
            "per_lord_years": 12,
            "lords": ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"],
            "note": "7 lords × 12 years = 84",
        },
        "computation_method": "nakshatra_remainder_conditional",
        "computation_pseudocode": (
            "Equal 12-year periods, 7 lords; "
            "applicability when the 10th lord is in the 10th house (classical condition)."
        ),
        "conditions_for_use": "Conditional: 10th-lord-in-10th charts.",
        "classical_citations": [{"text_id": "bphs", "chapter": 49}],
        "source_citation": BPHS_CH49,
        "python_impl_module": "pyjhora.chaturashiti",
    },

    # ── 13. Dwisaptati-sama — conditional 72-year; BPHS Ch.49 ────────────────
    {
        "canonical_id": "dwisaptati_sama",
        "name_sa": "Dvisaptati-sama",
        "name_en": "Dwisaptati-sama Dasha",
        "total_cycle_years": 72,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": {
            "type": "equal_period",
            "per_lord_years": 9,
            "lords": ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu"],
            "note": "8 lords × 9 years = 72",
        },
        "computation_method": "nakshatra_remainder_conditional",
        "computation_pseudocode": (
            "Equal 9-year periods, 8 lords; "
            "applicability when lagna lord is in the 7th or 7th lord in lagna (classical condition)."
        ),
        "conditions_for_use": "Conditional: lagna-lord/7th-lord exchange charts.",
        "classical_citations": [{"text_id": "bphs", "chapter": 49}],
        "source_citation": BPHS_CH49,
        "python_impl_module": "pyjhora.dwisaptati",
    },

    # ── 14. Shashtihayani — conditional 60-year; BPHS Ch.49 ──────────────────
    {
        "canonical_id": "shashtihayani",
        "name_sa": "Ṣaṣṭihāyaṇī",
        "name_en": "Shashtihayani Dasha",
        "total_cycle_years": 60,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": {
            "type": "shashtihayani",
            "note": "Sun-centric 60-year scheme; period lengths per classical Shashtihayani table",
            "lords": ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"],
        },
        "computation_method": "nakshatra_remainder_conditional",
        "computation_pseudocode": (
            "60-year cycle; "
            "applicability when Sun is the lagna lord or strongly placed (classical condition)."
        ),
        "conditions_for_use": "Conditional: Sun-dominant charts.",
        "classical_citations": [{"text_id": "bphs", "chapter": 49}],
        "source_citation": BPHS_CH49,
        "python_impl_module": "pyjhora.shashtihayani",
    },

    # ── 15. Shattrimsha-sama — conditional 36-year; BPHS Ch.49 ───────────────
    {
        "canonical_id": "shattrimsha_sama",
        "name_sa": "Ṣaṭtriṃśat-sama",
        "name_en": "Shattrimsha-sama Dasha",
        "total_cycle_years": 36,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": {
            "type": "day_night_dependent",
            "note": "36-year cycle; lord order depends on day vs night birth (Sun-first by day, Moon-first by night)",
        },
        "computation_method": "nakshatra_remainder_conditional",
        "computation_pseudocode": (
            "36-year cycle; "
            "applicability when lagna is in a Sun/Moon hora consistent with day/night birth."
        ),
        "conditions_for_use": "Conditional: hora/day-night rule.",
        "classical_citations": [{"text_id": "bphs", "chapter": 49}],
        "source_citation": BPHS_CH49,
        "python_impl_module": "pyjhora.shattrimsha",
    },

    # ── 16. Tara Dasha — tara chakra; BPHS Ch.47 ─────────────────────────────
    {
        "canonical_id": "tara_dasha",
        "name_sa": "Tārā Daśā",
        "name_en": "Tara Dasha",
        "total_cycle_years": 120,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": {
            "type": "tara_chakra",
            "note": (
                "Reckoned via the 9-tara (Janma, Sampat, Vipat, Kshema, Pratyak, "
                "Sadhana, Naidhana, Mitra, Parama-mitra) cycle from Moon's nakshatra."
            ),
        },
        "computation_method": "tara_chakra",
        "computation_pseudocode": (
            "9-fold tara cycle from janma nakshatra; "
            "period weighting per the tara scheme."
        ),
        "conditions_for_use": "Used in nakshatra/tarabala timing.",
        "classical_citations": [{"text_id": "bphs", "chapter": 47}],
        "source_citation": BPHS_CH47,
        "python_impl_module": "pyjhora.tara",
    },

    # ── 17. Brahma Dasha (Jaimini) — longevity karaka; Jaimini Sutram Ch.1 ───
    {
        "canonical_id": "brahma_dasha",
        "name_sa": "Brahma Daśā",
        "name_en": "Brahma Dasha (Jaimini)",
        "total_cycle_years": 120,
        "base_unit": "sign_lord",
        "school": "jaimini",
        "sequence_jsonb": {
            "type": "rashi_sequence",
            "note": (
                "Rashi dasha reckoned from the Brahma graha "
                "(Jaimini longevity karaka determination)."
            ),
        },
        "computation_method": "jaimini_brahma",
        "computation_pseudocode": (
            "Identify Brahma (one of the strong planets in odd/even signs by Jaimini rules); "
            "reckon a rashi dasha from its sign."
        ),
        "conditions_for_use": "Jaimini longevity/maraka analysis.",
        "classical_citations": [{"text_id": "jaimini_sutram", "chapter": 1}],
        "source_citation": JAIMINI_CH1,
        "python_impl_module": "pyjhora.brahma",
    },

    # ── 18. Yogardha Dasha — Vimshottari/Ashtottari average; BPHS Ch.48 ─────
    {
        "canonical_id": "yogardha_dasha",
        "name_sa": "Yogārdha Daśā",
        "name_en": "Yogardha Dasha",
        "total_cycle_years": 108,
        "base_unit": "nakshatra_lord",
        "school": "parashari",
        "sequence_jsonb": {
            "type": "average",
            "note": (
                "Average of Vimshottari and Ashtottari period-lengths per lord "
                "(yoga-ardha = half-sum). Ketu not in Ashtottari — carry Vimshottari value."
            ),
        },
        "computation_method": "vimshottari_ashtottari_average",
        "computation_pseudocode": (
            "For each lord, period = (Vimshottari years + Ashtottari years) / 2; "
            "sequence and balance as Vimshottari."
        ),
        "conditions_for_use": (
            "Used where both Vimshottari and Ashtottari are indicated; "
            "harmonizes the two."
        ),
        "classical_citations": [{"text_id": "bphs", "chapter": 48}],
        "source_citation": BPHS_CH48,
        "python_impl_module": "pyjhora.yogardha",
    },

    # ── 19. Nārāyaṇa Daśā (Jaimini rāśi daśā) — CR-104, D-2 Lane V-6 ─────────
    {
        "canonical_id": "narayana",
        "name_sa": "Nārāyaṇa Daśā",
        "name_en": "Narayana Dasha",
        "total_cycle_years": 144,
        "base_unit": "sign_lord",
        "school": "jaimini",
        "sequence_jsonb": {
            "type": "rashi_sequence",
            "note": (
                "Start sign (Deha Rasi): Lagna itself if Lagna is an odd sign, "
                "else the 7th sign from Lagna. Progression is ALWAYS zodiacal "
                "(forward) — unlike Chara Dasha, no direction reversal by "
                "movable/fixed/dual sign quality. Years per sign = count of "
                "signs from the sign to its lord's current sign (1-12; lord in "
                "own sign = 12) — the same Rao-formula duration principle "
                "already used for chara_jaimini in this catalog."
            ),
        },
        "computation_method": "narayana_rashi_dasha",
        "computation_pseudocode": (
            "1. Deha Rasi = Lagna if Lagna sign number (1-indexed) is odd, "
            "else the 7th sign from Lagna. "
            "2. Direction: always zodiacal (forward), sign-by-sign. "
            "3. Years for a sign = number of signs from the sign to its lord "
            "(counted zodiacally), minus 1 (i.e. inclusive count 1-12; lord "
            "in own sign = 12)."
        ),
        "conditions_for_use": (
            "Marriage/general-life rāśi daśā in the Jaimini tradition, read "
            "alongside Chara Dasha; CR-104 wiring — see V-6 close report for "
            "the exact rule-choice documentation (multiple commentarial "
            "variants exist for the start-sign determination)."
        ),
        "classical_citations": [{"text_id": "jaimini_sutram", "chapter": 1}],
        "source_citation": JAIMINI_CH1,
        "python_impl_module": "ga_writers.ga_dashas_writer.compute_narayana_system",
    },
]

# ── Sanity check at import time ────────────────────────────────────────────────

assert len(DASHA_SYSTEMS) == 19, f"Expected 19 systems, got {len(DASHA_SYSTEMS)}"


# ── Main seed function ─────────────────────────────────────────────────────────

def seed_dasha_systems(
    conn,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = True,
) -> dict[str, int]:
    """
    Seed brahma_dasha_systems, brahma_ontology (dasha_system class), and
    reference_dasha_systems pointer rows from the embedded DASHA_SYSTEMS list.

    Per §0.1 contract: catalog row first (FK target), then ontology, then pointer.
    All three use ON CONFLICT DO NOTHING for idempotency.

    Returns dict with keys:
      brahma_dasha_systems, brahma_ontology, reference_dasha_systems

    autocommit=False: caller (asset_runner) owns the transaction.
    """
    if dry_run:
        logger.info(
            "[L0/dasha_systems] dry-run: would insert up to %d rows in "
            "brahma_dasha_systems + %d ontology + %d pointer rows",
            len(DASHA_SYSTEMS), len(DASHA_SYSTEMS), len(DASHA_SYSTEMS),
        )
        return {
            "brahma_dasha_systems": len(DASHA_SYSTEMS),
            "brahma_ontology": len(DASHA_SYSTEMS),
            "reference_dasha_systems": len(DASHA_SYSTEMS),
        }

    counts: dict[str, int] = {
        "brahma_dasha_systems": 0,
        "brahma_ontology": 0,
        "reference_dasha_systems": 0,
    }

    with conn.cursor() as cur:
        for d in DASHA_SYSTEMS:
            cid = d["canonical_id"]

            # ── Step 1: catalog row (FK *target* — must be inserted first) ────
            cur.execute(
                """
                INSERT INTO brahma_dasha_systems
                  (canonical_id, name_sa, name_en, total_cycle_years, base_unit,
                   sequence_jsonb, computation_method, computation_pseudocode,
                   conditions_for_use, school, classical_citations,
                   python_impl_module)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s::jsonb, %s)
                ON CONFLICT (canonical_id) DO NOTHING
                """,
                (
                    cid,
                    d["name_sa"],
                    d["name_en"],
                    d["total_cycle_years"],
                    d["base_unit"],
                    _json.dumps(d["sequence_jsonb"]),
                    d["computation_method"],
                    d["computation_pseudocode"],
                    d.get("conditions_for_use"),
                    d["school"],
                    _json.dumps(d.get("classical_citations")),
                    d.get("python_impl_module"),
                ),
            )
            counts["brahma_dasha_systems"] += cur.rowcount
            logger.debug("[L0/dasha_systems] catalog: %s rowcount=%d", cid, cur.rowcount)

            # ── Step 2: ontology row (entity_class='dasha_system') ────────────
            description = (
                f"{d['name_en']} — {d['total_cycle_years']}-year "
                f"{d['school']} dasha system"
            )
            cur.execute(
                """
                INSERT INTO brahma_ontology
                  (entity_class, canonical_id, canonical_name_en, canonical_name_sa,
                   synonyms, description, source_citation)
                VALUES ('dasha_system', %s, %s, %s, %s, %s, %s)
                ON CONFLICT (entity_class, canonical_id) DO NOTHING
                """,
                (
                    cid,
                    d["name_en"],
                    d["name_sa"],
                    _synonyms(cid),
                    description,
                    d["source_citation"],
                ),
            )
            counts["brahma_ontology"] += cur.rowcount

            # ── Step 3: pointer row (FK → brahma_dasha_systems.canonical_id) ──
            cur.execute(
                """
                INSERT INTO reference_dasha_systems (canonical_id, name_en, school)
                VALUES (%s, %s, %s)
                ON CONFLICT (canonical_id) DO NOTHING
                """,
                (cid, d["name_en"], d["school"]),
            )
            counts["reference_dasha_systems"] += cur.rowcount

    if autocommit:
        conn.commit()

    logger.info(
        "[L0/dasha_systems] seeded: catalog=%d, ontology=%d, pointer=%d",
        counts["brahma_dasha_systems"],
        counts["brahma_ontology"],
        counts["reference_dasha_systems"],
    )
    return counts
