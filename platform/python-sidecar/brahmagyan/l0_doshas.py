"""
brahmagyan.l0_doshas — BRAHMA WS-2 L0 Brahmagyan: Classical Dosha / Affliction Catalog
========================================================================================

Populates brahma_dosha_catalog with 50 classical dosha definitions.
Each row has:
  - source_citation referencing a classical text (BPHS, classical tradition, etc.)
  - structured formation_rule_jsonb + prose formation_text
  - effects_text, severity_grades, cancellation_conditions
  - ZERO LLM generation

Also inserts:
  - brahma_ontology row (entity_class='dosha') per §0.1 cross-brief contract
  - reference_doshas pointer row per §0.1

Volume floor: >= 50 rows in brahma_dosha_catalog.

Citation policy (native decision per brief §3a): ~40 entries cite
'classical_tradition' (honest provenance for tradition-rooted doshas where no
single BPHS verse names them, e.g. Kala Sarpa variants, Ashtakoota kootas).
~10 cite BPHS Ch.9 directly. These are NOT fabricated citations.

BRAHMA-BG-0-13
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Source citations ───────────────────────────────────────────────────────────

BPHS_CITATION = "BPHS (Brihat Parasara Hora Sastra), classical tradition"
BPHS_CH9 = "BPHS Ch.9 (Arishta-adhyaya)"
BPHS_CH78 = "BPHS Ch.78 (Kuja Dosha / Vivaha Dosha adhyaya)"
CLASSICAL_TRADITION = "classical tradition (Jyotish)"

# ── Dosha corpus (50 entries, all inline) ─────────────────────────────────────

DOSHAS: list[dict] = [
    # ── Core graha-placement doshas ─────────────────────────────────────────
    {
        "canonical_id": "manglik",
        "name_sa": "Maṅgala Doṣa (Kuja Doṣa)",
        "name_en": "Manglik Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "houses": [1, 2, 4, 7, 8, 12],
            "reference": ["lagna", "moon", "venus"],
        },
        "formation_text": (
            "Mars in the 1st, 2nd, 4th, 7th, 8th or 12th house from lagna "
            "(and additionally checked from Moon and Venus)."
        ),
        "effects_text": (
            "Affliction to marriage — discord, delay, or harm to spouse; "
            "intensity varies by exact house and Mars's dignity."
        ),
        "severity_grades": {
            "mild": "from Venus only",
            "moderate": "from lagna or Moon",
            "severe": "from lagna AND Moon AND Venus; 7th/8th placement",
        },
        "cancellation_conditions": {
            "bhanga": [
                "Mars in own/exaltation sign",
                "both partners Manglik",
                "Mars aspected by Jupiter",
                "Mars in 2nd in Gemini/Virgo, 4th in Aries/Scorpio, 7th in Capricorn/Cancer, "
                "12th in Sagittarius/Pisces, 8th in Cancer (sign-specific cancellations)",
                "Jupiter/Venus in kendra",
            ]
        },
        "classical_citations": [{"text_id": "bphs"}],
        "source_citation": BPHS_CITATION,
    },
    {
        "canonical_id": "kala_sarpa",
        "name_sa": "Kāla Sarpa Doṣa",
        "name_en": "Kala Sarpa Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "all 7 planets hemmed between Rahu and Ketu (one side of the nodal axis)"
        },
        "formation_text": (
            "All seven planets fall on one side of the Rahu-Ketu axis "
            "(no planet outside the Rahu→Ketu arc)."
        ),
        "effects_text": (
            "Sustained struggle, delays, sudden reversals; karmic intensity. "
            "Partial when one planet is just outside the axis."
        ),
        "severity_grades": {
            "mild": "one planet conjunct a node (loose)",
            "moderate": "complete with benefic support",
            "severe": "complete with malefic emphasis",
        },
        "cancellation_conditions": {
            "bhanga": [
                "a planet outside the axis (then not full KSD)",
                "strong benefics in kendra/trikona",
                "Rahu/Ketu well-placed",
            ]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    # ── The 12 named Kala Sarpa variants (by Rahu→Ketu house placement) ─────
    {
        "canonical_id": "kala_sarpa_anant",
        "name_sa": "Ananta Kāla Sarpa",
        "name_en": "Anant Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 1, "ketu_house": 7},
        "formation_text": "Rahu in 1st, Ketu in 7th, all planets within the arc.",
        "effects_text": "Self vs partnership tension; identity and marriage karma.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_kulik",
        "name_sa": "Kulika Kāla Sarpa",
        "name_en": "Kulik Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 2, "ketu_house": 8},
        "formation_text": "Rahu in 2nd, Ketu in 8th, all planets within the arc.",
        "effects_text": "Wealth & longevity karma; speech and family obstacles.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_vasuki",
        "name_sa": "Vāsuki Kāla Sarpa",
        "name_en": "Vasuki Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 3, "ketu_house": 9},
        "formation_text": "Rahu in 3rd, Ketu in 9th, all planets within the arc.",
        "effects_text": "Courage & fortune karma; effort vs luck tension.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_shankhpal",
        "name_sa": "Śaṅkhapāla Kāla Sarpa",
        "name_en": "Shankhpal Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 4, "ketu_house": 10},
        "formation_text": "Rahu in 4th, Ketu in 10th, all planets within the arc.",
        "effects_text": "Home & career karma; instability in foundations and profession.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_padma",
        "name_sa": "Padma Kāla Sarpa",
        "name_en": "Padma Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 5, "ketu_house": 11},
        "formation_text": "Rahu in 5th, Ketu in 11th, all planets within the arc.",
        "effects_text": "Progeny & gains karma; children and aspiration obstacles.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_mahapadma",
        "name_sa": "Mahāpadma Kāla Sarpa",
        "name_en": "Mahapadma Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 6, "ketu_house": 12},
        "formation_text": "Rahu in 6th, Ketu in 12th, all planets within the arc.",
        "effects_text": "Enemies & loss karma; health and expenditure themes.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_takshak",
        "name_sa": "Takṣaka Kāla Sarpa",
        "name_en": "Takshak Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 7, "ketu_house": 1},
        "formation_text": "Rahu in 7th, Ketu in 1st, all planets within the arc.",
        "effects_text": "Marriage & self karma; partnership and identity friction.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_karkotak",
        "name_sa": "Karkoṭaka Kāla Sarpa",
        "name_en": "Karkotak Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 8, "ketu_house": 2},
        "formation_text": "Rahu in 8th, Ketu in 2nd, all planets within the arc.",
        "effects_text": "Longevity & family karma; sudden events, inheritance themes.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_shankhachud",
        "name_sa": "Śaṅkhacūḍa Kāla Sarpa",
        "name_en": "Shankhachud Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 9, "ketu_house": 3},
        "formation_text": "Rahu in 9th, Ketu in 3rd, all planets within the arc.",
        "effects_text": "Fortune & effort karma; dharma and sibling themes.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_ghatak",
        "name_sa": "Ghātaka Kāla Sarpa",
        "name_en": "Ghatak Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 10, "ketu_house": 4},
        "formation_text": "Rahu in 10th, Ketu in 4th, all planets within the arc.",
        "effects_text": "Career & home karma; profession and emotional-base themes.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_vishdhar",
        "name_sa": "Viṣadhara Kāla Sarpa",
        "name_en": "Vishdhar Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 11, "ketu_house": 5},
        "formation_text": "Rahu in 11th, Ketu in 5th, all planets within the arc.",
        "effects_text": "Gains & progeny karma; income and children themes.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kala_sarpa_sheshnag",
        "name_sa": "Śeṣanāga Kāla Sarpa",
        "name_en": "Sheshnag Kala Sarpa",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"rahu_house": 12, "ketu_house": 6},
        "formation_text": "Rahu in 12th, Ketu in 6th, all planets within the arc.",
        "effects_text": "Loss & enemies karma; expenditure, foreign, and conflict themes.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    # ── Other graha-placement doshas ────────────────────────────────────────
    {
        "canonical_id": "kemadruma",
        "name_sa": "Kemadruma Doṣa",
        "name_en": "Kemadruma Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "no planet (except Sun/nodes) in 2nd or 12th from Moon, "
                        "none with Moon, none in kendra from Moon/lagna"
        },
        "formation_text": (
            "The Moon has no planet in the 2nd or 12th from it "
            "(and no kendra support), leaving it unsupported."
        ),
        "effects_text": (
            "Poverty, struggle, loneliness, mental restlessness; "
            "one of the strongest negating yogas."
        ),
        "severity_grades": {
            "mild": "kendra benefic from lagna",
            "severe": "no support at all",
        },
        "cancellation_conditions": {
            "bhanga": [
                "any planet in kendra from Moon or lagna",
                "Moon in kendra from lagna",
                "benefic in 2nd/12th from Moon",
                "Moon aspected by a benefic",
            ]
        },
        "classical_citations": [{"text_id": "bphs"}],
        "source_citation": BPHS_CITATION,
    },
    {
        "canonical_id": "daridra",
        "name_sa": "Dāridra Doṣa",
        "name_en": "Daridra Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "11th lord in dusthana (6/8/12) or 2nd/11th lords afflicted"
        },
        "formation_text": "Lord of gains (11th) in a dusthana, or wealth-house lords debilitated/combust.",
        "effects_text": "Chronic financial difficulty, blocked income.",
        "severity_grades": {"moderate": "one condition", "severe": "multiple"},
        "cancellation_conditions": {
            "bhanga": ["dhana/raja yoga present", "11th lord retrograde-strong"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "shakata",
        "name_sa": "Śakaṭa Yoga (Doṣa)",
        "name_en": "Shakata Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "moon_jupiter_relation": "6/8 from each other",
            "exclude": "Jupiter in kendra from lagna",
        },
        "formation_text": (
            "Moon and Jupiter in 6/8 (or 12/2) mutual position, "
            "Jupiter not in a kendra from lagna."
        ),
        "effects_text": "Fluctuating fortune — rise and fall 'like a cart wheel'.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {
            "bhanga": ["Jupiter in kendra from lagna or Moon"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "vish_dosha",
        "name_sa": "Viṣa Doṣa",
        "name_en": "Vish Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"conjunction": ["moon", "saturn"]},
        "formation_text": "Moon conjunct Saturn (poison combination).",
        "effects_text": "Emotional heaviness, depression, chronic worry.",
        "severity_grades": {
            "mild": "wide orb",
            "severe": "close conjunction in dusthana",
        },
        "cancellation_conditions": {
            "bhanga": ["benefic aspect", "Moon strong in own/exalt"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "punarphoo",
        "name_sa": "Punarphū Doṣa",
        "name_en": "Punarphoo Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"relation": "Saturn aspects or conjoins Moon"},
        "formation_text": "Saturn conjunct/aspecting Moon (repetition/delay combination).",
        "effects_text": (
            "Repeated efforts, delays in settling matters (esp. marriage), "
            "maturity through obstruction."
        ),
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspect", "strong lagna lord"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "guru_chandal",
        "name_sa": "Guru Cāṇḍāla Doṣa",
        "name_en": "Guru Chandal Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"conjunction": ["jupiter", "rahu"]},
        "formation_text": "Jupiter conjunct Rahu (wisdom-corruption combination).",
        "effects_text": (
            "Distorted judgment, unorthodox beliefs, guru-related issues; "
            "can also give unconventional genius."
        ),
        "severity_grades": {
            "mild": "benefic support",
            "severe": "in dharma houses 5/9",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter exalted/own", "benefic aspect"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "angarak",
        "name_sa": "Aṅgāraka Doṣa",
        "name_en": "Angarak Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"conjunction": ["mars", "rahu"]},
        "formation_text": "Mars conjunct Rahu (fire-poison combination).",
        "effects_text": "Anger, accidents, impulsive conflict, blood/inflammation issues.",
        "severity_grades": {
            "moderate": "default",
            "severe": "in 1/4/7/8",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspect", "Mars in own sign"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "grahan",
        "name_sa": "Grahaṇa Doṣa",
        "name_en": "Grahan (Eclipse) Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "conjunction": [
                ["sun", "rahu"],
                ["sun", "ketu"],
                ["moon", "rahu"],
                ["moon", "ketu"],
            ]
        },
        "formation_text": "Sun or Moon conjunct Rahu or Ketu (natal eclipse combination).",
        "effects_text": "Affliction to vitality (Sun) or mind (Moon); ancestral/karmic themes.",
        "severity_grades": {
            "mild": "wide, in good house",
            "severe": "close, in dusthana",
        },
        "cancellation_conditions": {
            "bhanga": ["benefic aspect", "luminary strong"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "pitru_dosha",
        "name_sa": "Pitṛ Doṣa",
        "name_en": "Pitru Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "Sun/9th-house/9th-lord afflicted by Rahu/Ketu/Saturn"
        },
        "formation_text": (
            "Affliction to the Sun, the 9th house or its lord by Rahu/Ketu/Saturn "
            "(ancestral karmic debt)."
        ),
        "effects_text": (
            "Obstacles tied to ancestral karma; father-related difficulty; "
            "blocked fortune until remediated."
        ),
        "severity_grades": {
            "moderate": "one factor",
            "severe": "multiple",
        },
        "cancellation_conditions": {
            "bhanga": ["strong benefic on 9th", "Jupiter on Sun/9th"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    # ── Transit (gochara) doshas ─────────────────────────────────────────────
    {
        "canonical_id": "sade_sati",
        "name_sa": "Sāḍe-sātī",
        "name_en": "Sade Sati",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "transit": "Saturn over 12th, 1st, 2nd from natal Moon (7.5 years)"
        },
        "formation_text": (
            "Saturn transiting the 12th, 1st and 2nd from the natal Moon "
            "— a 7.5-year period in three phases."
        ),
        "effects_text": "Pressure, responsibility, restructuring; phase-dependent (rising/peak/setting).",
        "severity_grades": {
            "mild": "Saturn dig-bali/benefic",
            "moderate": "peak phase",
            "severe": "Saturn debilitated/afflicted",
        },
        "cancellation_conditions": {
            "mitigation": [
                "Saturn exalted/own in transit",
                "strong natal Saturn",
                "supportive dasha",
            ]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "dhaiya",
        "name_sa": "Dhaiyā (Aṣṭama/Kaṇṭaka Śani)",
        "name_en": "Dhaiya / Small Panoti",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "transit": "Saturn over 4th or 8th from natal Moon (2.5 years)"
        },
        "formation_text": (
            "Saturn transiting the 4th (Kantaka) or 8th (Ashtama) from the natal Moon "
            "— a 2.5-year sub-affliction."
        ),
        "effects_text": "Domestic (4th) or health/longevity (8th) pressure for 2.5 years.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {
            "mitigation": ["Saturn well-placed in transit"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    # ── Compatibility (Ashtakoota) doshas ────────────────────────────────────
    {
        "canonical_id": "nadi_dosha",
        "name_sa": "Nāḍī Doṣa",
        "name_en": "Nadi Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "same Nadi (Aadi/Madhya/Antya) for both partners' Moon nakshatras"
        },
        "formation_text": (
            "Bride and groom share the same Nadi (of the three: Aadi, Madhya, Antya) "
            "— 8 of 8 koota points lost."
        ),
        "effects_text": "Considered the gravest compatibility dosha — health/progeny concerns.",
        "severity_grades": {"severe": "same Nadi and same nakshatra-pada"},
        "cancellation_conditions": {
            "bhanga": [
                "same nakshatra but different pada",
                "same rashi different nakshatra",
                "specific Nadi-bhanga rules",
            ]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "bhakoot_dosha",
        "name_sa": "Bhakūṭa Doṣa",
        "name_en": "Bhakoot Dosha",
        "category": "rashi_combination",
        "school": "parashari",
        "formation_rule_jsonb": {"rashi_distance": ["6-8", "2-12", "5-9"]},
        "formation_text": (
            "Moon-sign distance between partners is 6/8, 2/12 (Dwirdwadasha) "
            "or 5/9 (Navapancham)."
        ),
        "effects_text": (
            "Discord, financial/health/progeny friction depending on the koota."
        ),
        "severity_grades": {
            "moderate": "2/12 or 5/9",
            "severe": "6/8",
        },
        "cancellation_conditions": {
            "bhanga": [
                "same rashi lord",
                "lords are friends",
                "Nadi-koota satisfied",
            ]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "gana_dosha",
        "name_sa": "Gaṇa Doṣa",
        "name_en": "Gana Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "mismatch": "Deva vs Rakshasa gana of the two Moon-nakshatras"
        },
        "formation_text": (
            "Nakshatra-gana mismatch (Deva/Manushya/Rakshasa) "
            "— worst when Deva-bride & Rakshasa-groom."
        ),
        "effects_text": "Temperamental incompatibility.",
        "severity_grades": {
            "mild": "Manushya-Deva",
            "severe": "Deva-Rakshasa",
        },
        "cancellation_conditions": {
            "bhanga": ["same rashi/nakshatra lord", "Bhakoot satisfied"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "yoni_dosha",
        "name_sa": "Yoni Doṣa",
        "name_en": "Yoni Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "mismatch": "enemy yoni (animal) of the two Moon-nakshatras"
        },
        "formation_text": (
            "The nakshatra-yoni (animal symbols) of the partners are natural enemies "
            "(e.g. cat–rat, cow–tiger)."
        ),
        "effects_text": "Sexual/instinctual incompatibility (Yoni koota, max 4 points).",
        "severity_grades": {
            "moderate": "enemy yoni",
            "severe": "mortal-enemy yoni",
        },
        "cancellation_conditions": {
            "bhanga": ["same yoni", "friendly/neutral yoni"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "vashya_dosha",
        "name_sa": "Vaśya Doṣa",
        "name_en": "Vashya Dosha",
        "category": "rashi_combination",
        "school": "parashari",
        "formation_rule_jsonb": {
            "mismatch": "vashya-group incompatibility of the two Moon-signs"
        },
        "formation_text": (
            "The vashya (control/magnetism) groups of the partners' Moon-signs are incompatible."
        ),
        "effects_text": "Imbalance of mutual control/attraction (Vashya koota, max 2 points).",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {"bhanga": ["same vashya group"]},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "tara_dosha_compat",
        "name_sa": "Tārā Doṣa",
        "name_en": "Tara (Dina) Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "mismatch": "inauspicious tara (3/5/7 count) between the two janma-nakshatras"
        },
        "formation_text": (
            "The mutual tara-count (birth-star compatibility) falls in an inauspicious "
            "tara (Vipat/Pratyak/Naidhana)."
        ),
        "effects_text": "Health/longevity-of-relationship concern (Tara koota, max 3 points).",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {"bhanga": ["auspicious mutual tara"]},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "varna_dosha",
        "name_sa": "Varṇa Doṣa",
        "name_en": "Varna Dosha",
        "category": "rashi_combination",
        "school": "parashari",
        "formation_rule_jsonb": {
            "mismatch": "groom's varna lower than bride's (by Moon-sign varna: Brahmin/Kshatriya/Vaishya/Shudra)"
        },
        "formation_text": (
            "The varna (by Moon-sign: water=Brahmin, fire=Kshatriya, earth=Vaishya, air=Shudra) "
            "of the groom is lower than the bride's."
        ),
        "effects_text": "Spiritual/ego-compatibility concern (Varna koota, max 1 point).",
        "severity_grades": {"mild": "default"},
        "cancellation_conditions": {"bhanga": ["groom varna >= bride varna"]},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "graha_maitri_dosha",
        "name_sa": "Graha-Maitrī Doṣa",
        "name_en": "Graha-Maitri Dosha",
        "category": "rashi_combination",
        "school": "parashari",
        "formation_rule_jsonb": {
            "mismatch": "Moon-sign lords of the partners are mutual enemies"
        },
        "formation_text": (
            "The lords of the partners' Moon-signs are natural enemies "
            "(Graha-Maitri / Rashi-adhipati koota)."
        ),
        "effects_text": "Mental/affectional incompatibility (Graha-Maitri koota, max 5 points).",
        "severity_grades": {
            "moderate": "one-way enmity",
            "severe": "mutual enmity",
        },
        "cancellation_conditions": {"bhanga": ["lords friends or same lord"]},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    # ── Arishta / balarishta (BPHS Ch.9) ─────────────────────────────────────
    {
        "canonical_id": "balarishta",
        "name_sa": "Bālāriṣṭa",
        "name_en": "Balarishta",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "afflicted Moon (with malefics, no benefic aspect) in early life indications"
        },
        "formation_text": (
            "Malefic affliction to the Moon/lagna indicating affliction in infancy "
            "(per BPHS Arishta-adhyaya)."
        ),
        "effects_text": "Classical infant-affliction yoga; read with longevity factors.",
        "severity_grades": {"varies": "by benefic cancellation"},
        "cancellation_conditions": {
            "bhanga": [
                "benefic in kendra",
                "strong lagna lord",
                "Jupiter aspect on Moon",
            ]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 9}],
        "source_citation": BPHS_CH9,
    },
    {
        "canonical_id": "gandanta_dosha",
        "name_sa": "Gaṇḍānta Doṣa",
        "name_en": "Gandanta Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": (
                "Moon at a water-fire sign junction (last 3deg20' of Cancer/Scorpio/Pisces "
                "or first 3deg20' of Leo/Sagittarius/Aries) "
                "OR nakshatra junction (Revati-Ashwini, Ashlesha-Magha, Jyeshtha-Mula)"
            )
        },
        "formation_text": (
            "The Moon (or lagna) falls at a gandanta — the vulnerable junction "
            "of a water and fire sign/nakshatra."
        ),
        "effects_text": "Early-life vulnerability; karmic knot at the sign/nakshatra seam.",
        "severity_grades": {
            "moderate": "sign gandanta",
            "severe": "nakshatra-pada gandanta (esp. Jyeshtha-Mula)",
        },
        "cancellation_conditions": {
            "bhanga": ["benefic aspect on the Moon", "strong lagna lord"]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 9}],
        "source_citation": BPHS_CH9,
    },
    {
        "canonical_id": "shrapit_dosha",
        "name_sa": "Śrāpita Doṣa",
        "name_en": "Shrapit Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"conjunction": ["saturn", "rahu"]},
        "formation_text": "Saturn conjunct Rahu (the 'cursed' combination).",
        "effects_text": "Accumulated karmic burden, chronic obstruction, ancestral curse themes.",
        "severity_grades": {
            "moderate": "default",
            "severe": "in dusthana or on a luminary",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspect", "both well-placed in own/exalt"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "mrityu_bhaga_dosha",
        "name_sa": "Mṛtyu-Bhāga Doṣa",
        "name_en": "Mrityu-Bhaga Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": (
                "a planet (or lagna) at its mrityu-bhaga (fatal degree) "
                "per the classical mrityu-bhaga table"
            )
        },
        "formation_text": (
            "A planet or the lagna occupies its specific 'death-degree' (mrityu-bhaga) "
            "per the classical per-sign degree table."
        ),
        "effects_text": "Marked vulnerability of the significations of that planet/house.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {
            "bhanga": ["strong benefic influence on the planet"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kemadruma_compat_kuja",
        "name_sa": "Kuja from Venus",
        "name_en": "Kuja-from-Venus Manglik",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "houses": [1, 2, 4, 7, 8, 12],
            "reference": ["venus"],
        },
        "formation_text": (
            "Mars in the 1/2/4/7/8/12 reckoned FROM Venus (the kalatra-karaka) "
            "— a Venus-referenced Manglik affliction."
        ),
        "effects_text": (
            "Affliction to married/relationship happiness reckoned from the marriage significator."
        ),
        "severity_grades": {
            "mild": "from Venus only",
            "moderate": "reinforced from lagna/Moon",
        },
        "cancellation_conditions": {
            "bhanga": ["Mars in own/exalt", "Jupiter aspect on Mars or Venus"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    # ── Additional attested doshas (classical enumeration) ───────────────────
    {
        "canonical_id": "kala_amrita_dosha",
        "name_sa": "Kāla Amṛta Doṣa",
        "name_en": "Kala Amrita Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "all 7 planets hemmed between Ketu and Rahu (the reverse arc of Kala Sarpa)"
        },
        "formation_text": (
            "All seven planets fall on the Ketu→Rahu side of the nodal axis "
            "(the reverse-direction counterpart of Kala Sarpa)."
        ),
        "effects_text": "Karmic intensity with a more inward/spiritual coloration than Kala Sarpa.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {"bhanga": ["a planet outside the arc"]},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "kuja_dosha_from_moon",
        "name_sa": "Candra Kuja Doṣa",
        "name_en": "Kuja Dosha (from Moon)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "houses": [1, 2, 4, 7, 8, 12],
            "reference": ["moon"],
        },
        "formation_text": "Mars in the 1/2/4/7/8/12 reckoned FROM the Moon — the Moon-referenced Manglik check.",
        "effects_text": (
            "Reinforces marital affliction when present alongside the lagna-referenced Manglik."
        ),
        "severity_grades": {
            "mild": "from Moon only",
            "severe": "from lagna AND Moon AND Venus",
        },
        "cancellation_conditions": {
            "bhanga": ["Mars in own/exalt", "Jupiter aspect"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "mool_dosha",
        "name_sa": "Mūla Doṣa",
        "name_en": "Mool (Gandmool) Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "birth Moon in a gandmool nakshatra (Ashwini, Ashlesha, Magha, Jyeshtha, Mula, Revati)"
        },
        "formation_text": "The natal Moon falls in one of the six gandmool nakshatras (ruled by Ketu/Mercury).",
        "effects_text": "Early-childhood vulnerability; tradition prescribes a 27th-day shanti.",
        "severity_grades": {
            "mild": "middle padas",
            "severe": "junction padas (Jyeshtha-4 / Mula-1, Revati-4 / Ashwini-1, Ashlesha-4 / Magha-1)",
        },
        "cancellation_conditions": {
            "mitigation": [
                "gandmool shanti performed",
                "benefic aspect on the Moon",
            ]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "abhukta_mula_dosha",
        "name_sa": "Abhukta Mūla Doṣa",
        "name_en": "Abhukta-Mula Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "birth in the specific junction ghatis of Jyeshtha-end / Mula-start"
        },
        "formation_text": "Birth in the abhukta-mula window — the last ghatis of Jyeshtha into the first of Mula.",
        "effects_text": (
            "Considered especially inauspicious for the child/family per tradition; "
            "specific shanti prescribed."
        ),
        "severity_grades": {"severe": "default"},
        "cancellation_conditions": {"mitigation": ["prescribed shanti"]},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "vish_kanya_dosha",
        "name_sa": "Viṣa-Kanyā Doṣa",
        "name_en": "Vish-Kanya Dosha",
        "category": "tithi",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "specific inauspicious tithi + vara + nakshatra combination at birth (per the classical vish-kanya table)"
        },
        "formation_text": (
            "Birth on a tithi/weekday/nakshatra combination listed in the classical vish-kanya yoga table."
        ),
        "effects_text": (
            "Tradition associates it with marital misfortune; read with the whole chart, not in isolation."
        ),
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {
            "bhanga": [
                "strong benefic on 7th/8th",
                "prescribed remedial measures",
            ]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "rajju_dosha",
        "name_sa": "Rajju Doṣa",
        "name_en": "Rajju Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "mismatch": "both partners' nakshatras fall in the same rajju (body-part: pada/kati/nabhi/kantha/siro)"
        },
        "formation_text": (
            "The partners' janma-nakshatras occupy the same rajju (one of the five "
            "body-segments of the rajju-chakra)."
        ),
        "effects_text": "South-Indian matching: same rajju is inauspicious (esp. siro=head, pada=feet).",
        "severity_grades": {
            "moderate": "same rajju",
            "severe": "same siro/pada rajju",
        },
        "cancellation_conditions": {"bhanga": ["ascending vs descending rajju differ"]},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "vedha_dosha",
        "name_sa": "Vedha Doṣa",
        "name_en": "Vedha Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "mismatch": "partners' nakshatras form a classical vedha (obstruction) pair"
        },
        "formation_text": (
            "The two janma-nakshatras form a vedha (mutually-obstructing) pair "
            "per the classical vedha table."
        ),
        "effects_text": "Mutual obstruction of well-being in the match.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {
            "bhanga": ["same nakshatra lord", "other kootas strongly satisfied"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "stree_deergha_dosha",
        "name_sa": "Strī-Dīrgha Doṣa",
        "name_en": "Stree-Deergha Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "count from bride's janma-nakshatra to groom's < 9 (stree-deergha not satisfied)"
        },
        "formation_text": (
            "The count from the bride's to the groom's nakshatra is less than nine "
            "— stree-deergha (longevity-of-union) unmet."
        ),
        "effects_text": "Tradition holds the union less enduring when stree-deergha is absent.",
        "severity_grades": {"mild": "default"},
        "cancellation_conditions": {"bhanga": ["count >= 9", "Mahendra also satisfied"]},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "mahendra_dosha",
        "name_sa": "Mahendra Doṣa",
        "name_en": "Mahendra Dosha",
        "category": "nakshatra_compatibility",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "count from bride's to groom's nakshatra NOT one of 4,7,10,13,16,19,22,25 (mahendra unmet)"
        },
        "formation_text": (
            "The bride->groom nakshatra count is not a mahendra number "
            "— the mahendra (progeny/well-being) factor is absent."
        ),
        "effects_text": "Tradition links mahendra to progeny and welfare of the couple.",
        "severity_grades": {"mild": "default"},
        "cancellation_conditions": {"bhanga": ["count is a mahendra number"]},
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "balarishta_moon_dusthana",
        "name_sa": "Bālāriṣṭa (Candra Dusthāna)",
        "name_en": "Balarishta (Moon in Dusthana)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "waning Moon in 6/8/12 conjunct/aspected by malefics without benefic relief"
        },
        "formation_text": (
            "A weak (waning) Moon in the 6th, 8th or 12th, afflicted by malefics "
            "and without benefic aspect (a BPHS Ch.9 arishta)."
        ),
        "effects_text": "Classical infant-affliction configuration; weigh with longevity factors.",
        "severity_grades": {"severe": "no benefic relief"},
        "cancellation_conditions": {
            "bhanga": ["benefic in kendra", "Jupiter aspect on Moon"]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 9}],
        "source_citation": BPHS_CH9,
    },
    {
        "canonical_id": "balarishta_sandhi",
        "name_sa": "Bālāriṣṭa (Sandhi)",
        "name_en": "Balarishta (Junction Birth)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "birth at rashi/bhava sandhi (sign or house junction) with malefic influence on lagna/Moon"
        },
        "formation_text": (
            "Birth at a sign or house junction (sandhi) with the lagna/Moon under malefic influence (BPHS Ch.9)."
        ),
        "effects_text": "Junction-birth arishta; vulnerability in early life.",
        "severity_grades": {"moderate": "default"},
        "cancellation_conditions": {
            "bhanga": ["strong benefic on lagna/Moon"]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 9}],
        "source_citation": BPHS_CH9,
    },
    {
        "canonical_id": "balarishta_paap_kartari",
        "name_sa": "Bālāriṣṭa (Pāpa Kartari)",
        "name_en": "Balarishta (Papa Kartari)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": (
                "lagna or Moon hemmed by malefics in the 2nd and 12th from it "
                "(papa-kartari) without benefic aspect"
            )
        },
        "formation_text": (
            "The lagna or the Moon is hemmed between malefics (papa-kartari) "
            "with no benefic relief (BPHS Ch.9)."
        ),
        "effects_text": "Hemming arishta; squeezes the vitality of the hemmed point.",
        "severity_grades": {"severe": "both lagna and Moon hemmed"},
        "cancellation_conditions": {
            "bhanga": [
                "benefic aspect on the hemmed point",
                "shubha-kartari instead",
            ]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 9}],
        "source_citation": BPHS_CH9,
    },

    # ── §2 — Kuja (Mangal) Dosha specific-house variants (BPHS Ch.78) ─────────
    {
        "canonical_id": "kuja_dosha_lagna_1st",
        "name_sa": "Kuja Doṣa — Lagna-prathama",
        "name_en": "Kuja Dosha (Mars in 1st from Lagna)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "house": 1,
            "reference": "lagna",
        },
        "formation_text": "Mars in the 1st house from lagna — the mildest Kuja Dosha house placement.",
        "effects_text": (
            "Physical aggression, impulsive temperament; mild marriage affliction "
            "compared to the 7th/8th placement."
        ),
        "severity_grades": {"mild": "1st house is the least severe Kuja position"},
        "cancellation_conditions": {
            "bhanga": [
                "Mars in Aries or Scorpio (own sign) in 1st",
                "Jupiter aspects Mars",
                "Benefic conjunction with Mars",
            ]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 78}],
        "source_citation": BPHS_CH78,
    },
    {
        "canonical_id": "kuja_dosha_lagna_4th",
        "name_sa": "Kuja Doṣa — Lagna-caturtha",
        "name_en": "Kuja Dosha (Mars in 4th from Lagna)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "house": 4,
            "reference": "lagna",
        },
        "formation_text": "Mars in the 4th house from lagna — disrupts domestic happiness and property.",
        "effects_text": (
            "Domestic friction, property disputes, marital tension through home environment."
        ),
        "severity_grades": {"moderate": "4th house Mars — domestic and marital strain"},
        "cancellation_conditions": {
            "bhanga": [
                "Mars in Aries/Scorpio/Capricorn in 4th",
                "Jupiter aspects Mars",
                "Moon strong from 4th",
            ]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 78}],
        "source_citation": BPHS_CH78,
    },
    {
        "canonical_id": "kuja_dosha_lagna_7th",
        "name_sa": "Kuja Doṣa — Lagna-saptama",
        "name_en": "Kuja Dosha (Mars in 7th from Lagna)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "house": 7,
            "reference": "lagna",
        },
        "formation_text": (
            "Mars in the 7th from lagna — the classic kalatra-house placement; "
            "severe marital affliction."
        ),
        "effects_text": (
            "Severe marital strain; harm to spouse; divorce or conflict in partnership."
        ),
        "severity_grades": {
            "severe": "7th house is the most direct marital-house Mars placement",
        },
        "cancellation_conditions": {
            "bhanga": [
                "Mars in Capricorn (exaltation) in 7th",
                "Both partners Manglik",
                "Jupiter aspects 7th or 7th lord",
            ]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 78}],
        "source_citation": BPHS_CH78,
    },
    {
        "canonical_id": "kuja_dosha_lagna_8th",
        "name_sa": "Kuja Doṣa — Lagna-ashtama",
        "name_en": "Kuja Dosha (Mars in 8th from Lagna)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "house": 8,
            "reference": "lagna",
        },
        "formation_text": "Mars in the 8th from lagna — longevity house; severe affliction.",
        "effects_text": (
            "Longevity of marriage threatened; potential widowhood/widowerhood in classical texts; "
            "deep marital and health affliction."
        ),
        "severity_grades": {"severe": "8th is the most severe Kuja Dosha position"},
        "cancellation_conditions": {
            "bhanga": [
                "Mars in own/exaltation in 8th (Scorpio, Capricorn)",
                "Jupiter aspects 8th lord",
                "Benefic Jupiter in 8th",
            ]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 78}],
        "source_citation": BPHS_CH78,
    },
    {
        "canonical_id": "kuja_dosha_lagna_12th",
        "name_sa": "Kuja Doṣa — Lagna-dvādaśa",
        "name_en": "Kuja Dosha (Mars in 12th from Lagna)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "house": 12,
            "reference": "lagna",
        },
        "formation_text": "Mars in the 12th from lagna — loss house; bedroom/expense affliction.",
        "effects_text": (
            "Loss of marital happiness through bedroom discord; health of spouse affected; "
            "expenditure through conflict."
        ),
        "severity_grades": {"moderate": "12th house Kuja Dosha — bedroom and loss themes"},
        "cancellation_conditions": {
            "bhanga": [
                "Mars in Sagittarius/Pisces in 12th (friendly/own sign by some accounts)",
                "Jupiter aspect on Mars",
            ]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 78}],
        "source_citation": BPHS_CH78,
    },
    {
        "canonical_id": "kuja_dosha_lagna_2nd",
        "name_sa": "Kuja Doṣa — Lagna-dvitīya",
        "name_en": "Kuja Dosha (Mars in 2nd from Lagna)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "house": 2,
            "reference": "lagna",
        },
        "formation_text": (
            "Mars in the 2nd from lagna — family/speech house; "
            "admitted by some classical authorities as a Kuja Dosha house."
        ),
        "effects_text": (
            "Harsh speech, family quarrels; financial disputes in marriage; "
            "considered Kuja Dosha by Parashara (BPHS Ch.78) though debated."
        ),
        "severity_grades": {"mild": "2nd house — speech and family affliction"},
        "cancellation_conditions": {
            "bhanga": [
                "Mars in own/exaltation in 2nd (Aries, Capricorn)",
                "Jupiter aspects 2nd house",
            ]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 78}],
        "source_citation": BPHS_CH78,
    },

    # ── §3 — Kuja Dosha cancellation-condition variants ──────────────────────
    {
        "canonical_id": "kuja_dosha_bhanga_own_sign",
        "name_sa": "Kuja Doṣa Bhaṅga (Svakṣetra)",
        "name_en": "Kuja Dosha Bhanga (Mars in Own Sign)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "houses": [1, 2, 4, 7, 8, 12],
            "reference": "lagna",
            "cancellation_condition": "mars_in_own_sign_aries_or_scorpio",
        },
        "formation_text": (
            "Mars in a Kuja Dosha house but in its own sign "
            "(Aries or Scorpio) — Kuja Dosha is cancelled."
        ),
        "effects_text": (
            "The dosha is neutralised; Mars in own sign in a Kuja house gives strength "
            "without marital affliction."
        ),
        "severity_grades": {"none": "Bhanga — dosha negated"},
        "cancellation_conditions": {"applies": "This entry is itself a cancellation record"},
        "classical_citations": [{"text_id": "bphs", "chapter": 78}],
        "source_citation": BPHS_CH78,
    },
    {
        "canonical_id": "kuja_dosha_bhanga_exaltation",
        "name_sa": "Kuja Doṣa Bhaṅga (Uccha)",
        "name_en": "Kuja Dosha Bhanga (Mars Exalted)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "mars",
            "houses": [1, 2, 4, 7, 8, 12],
            "reference": "lagna",
            "cancellation_condition": "mars_in_exaltation_capricorn",
        },
        "formation_text": "Mars in a Kuja Dosha house in Capricorn (exaltation) — Kuja Dosha cancelled.",
        "effects_text": "Exalted Mars in a Kuja house gives power without the dosha.",
        "severity_grades": {"none": "Bhanga — dosha negated"},
        "cancellation_conditions": {"applies": "This entry records the exaltation bhanga rule"},
        "classical_citations": [{"text_id": "bphs", "chapter": 78}],
        "source_citation": BPHS_CH78,
    },

    # ── §4 — Grahan Dosha sub-types ──────────────────────────────────────────
    {
        "canonical_id": "surya_grahan_dosha",
        "name_sa": "Sūrya Grahaṇa Doṣa",
        "name_en": "Surya Grahan Dosha (Solar Eclipse Dosha)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "conjunction": ["sun", "rahu"],
            "or": {"conjunction": ["sun", "ketu"]},
        },
        "formation_text": "Sun conjunct Rahu or Ketu — natal solar eclipse combination.",
        "effects_text": (
            "Affliction to vitality, father, authority; ego and identity themes; "
            "ancestral karmic debt related to the father."
        ),
        "severity_grades": {
            "mild": "wide orb (> 10°), benefic aspect",
            "moderate": "moderate orb",
            "severe": "close (< 5°) in dusthana or lagna",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects Sun", "Sun in own/exaltation"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "chandra_grahan_dosha",
        "name_sa": "Candra Grahaṇa Doṣa",
        "name_en": "Chandra Grahan Dosha (Lunar Eclipse Dosha)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "conjunction": ["moon", "rahu"],
            "or": {"conjunction": ["moon", "ketu"]},
        },
        "formation_text": "Moon conjunct Rahu or Ketu — natal lunar eclipse combination.",
        "effects_text": (
            "Mental affliction, emotional instability, distorted perceptions; "
            "mother-related karma; Rahu conjunct Moon is also called Chandal combination."
        ),
        "severity_grades": {
            "mild": "wide orb, strong Moon",
            "moderate": "Moon waning",
            "severe": "close conjunction in 4th/12th with weak Moon",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects Moon", "benefic in kendra from Moon"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "lagna_lord_grahan_dosha",
        "name_sa": "Lagneśa Grahaṇa Doṣa",
        "name_en": "Lagna Lord Grahan Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "lagna_lord",
            "conjunct_node": True,
        },
        "formation_text": "The lagna lord conjunct Rahu or Ketu — eclipse affliction to self and body.",
        "effects_text": (
            "Physical or identity affliction channelled through the eclipse of the self-significator; "
            "health concerns, identity distortion."
        ),
        "severity_grades": {
            "moderate": "default",
            "severe": "in dusthana or lagna lord debilitated",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects lagna lord", "lagna lord in own/exaltation"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },

    # ── §5 — Pitra Dosha sub-types ───────────────────────────────────────────
    {
        "canonical_id": "pitra_dosha_sun_rahu",
        "name_sa": "Pitṛ Doṣa — Sūrya-Rāhu",
        "name_en": "Pitra Dosha (Sun-Rahu conjunction)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"conjunction": ["sun", "rahu"]},
        "formation_text": "Sun conjunct Rahu — the primary Pitra Dosha indicator.",
        "effects_text": (
            "Ancestral karmic debt; father-related affliction; obstacles in dharmic path "
            "until ancestral patterns are resolved."
        ),
        "severity_grades": {
            "moderate": "wide conjunction",
            "severe": "close conjunction (< 8°) in 1/5/9",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects Sun", "Sun strong in own/exalt"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "pitra_dosha_9th_lord_afflicted",
        "name_sa": "Pitṛ Doṣa — Bhāgyeśa Pīḍita",
        "name_en": "Pitra Dosha (9th Lord Afflicted)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "9th_lord",
            "affliction": ["rahu", "ketu", "saturn"],
            "mode": "conjunction_or_aspect",
        },
        "formation_text": "The 9th lord afflicted by Rahu, Ketu or Saturn through conjunction or aspect.",
        "effects_text": (
            "Ancestral karma affecting fortune; obstacles to dharma and father's blessings."
        ),
        "severity_grades": {
            "moderate": "aspect affliction",
            "severe": "conjunction with 9th lord debilitated",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects 9th house or its lord"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "pitra_dosha_sun_12th_malefic",
        "name_sa": "Pitṛ Doṣa — Sūrya Dvādaśa",
        "name_en": "Pitra Dosha (Sun in 12th with Malefic Aspect)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "sun",
            "house": 12,
            "malefic_aspect": True,
        },
        "formation_text": "Sun in the 12th house with malefic aspect — loss of paternal blessings.",
        "effects_text": (
            "Loss of father early or estrangement; ancestral debt; expenditure through paternal karma."
        ),
        "severity_grades": {
            "moderate": "12th Sun with mild malefic",
            "severe": "Sun debilitated in 12th with Saturn/Rahu aspect",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects 12th", "Sun exalted/own in 12th (Sagittarius for some lagnas)"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "pitra_dosha_sun_saturn_conjunction",
        "name_sa": "Pitṛ Doṣa — Sūrya-Śani Yoga",
        "name_en": "Pitra Dosha (Sun-Saturn Conjunction)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"conjunction": ["sun", "saturn"]},
        "formation_text": "Sun conjunct Saturn — father-enemy combination; ancestral karmic debt.",
        "effects_text": (
            "Father-related karma; separation from or conflict with father; "
            "delayed or obstructed paternal blessings."
        ),
        "severity_grades": {
            "moderate": "wide conjunction",
            "severe": "close conjunction in 9th/12th",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects the conjunction", "one planet exalted"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },

    # ── §6 — Naga Dosha / Sarpa Dosha variants ───────────────────────────────
    {
        "canonical_id": "naga_dosha_nodes_kendra",
        "name_sa": "Nāga Doṣa (Kendra)",
        "name_en": "Naga Dosha (Rahu/Ketu in Kendra)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "rahu_or_ketu",
            "houses": [1, 4, 7, 10],
        },
        "formation_text": "Rahu or Ketu placed in the kendras (1st, 4th, 7th, 10th).",
        "effects_text": (
            "Serpent energy in foundational houses; karmic themes in self, home, "
            "partnership or career. Specific effects depend on the house and the node."
        ),
        "severity_grades": {
            "mild": "benefic association or aspect",
            "moderate": "kendra nodes unafflicted",
            "severe": "kendra nodes with malefic conjunction",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects the nodal house", "strong kendra lord"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "naga_dosha_rahu_lagna",
        "name_sa": "Nāga Doṣa — Rāhu Lagna",
        "name_en": "Naga Dosha (Rahu in Lagna)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"planet": "rahu", "house": 1},
        "formation_text": "Rahu in the 1st house (lagna) — serpent in self.",
        "effects_text": (
            "Identity and body affliction; obsessive personality; karmic patterns "
            "playing out through the self; also can give worldly ambition and charisma."
        ),
        "severity_grades": {
            "moderate": "Rahu in neutral sign in lagna",
            "severe": "Rahu in enemy sign or with malefic",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects lagna", "Rahu in exaltation (Gemini/Taurus)"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "sarpa_yoga_dosha",
        "name_sa": "Sarpa Yoga (Doṣa)",
        "name_en": "Sarpa Yoga Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "malefics_in": "three_kendras",
            "benefics_elsewhere": True,
        },
        "formation_text": (
            "Three kendras occupied by malefics with benefics not in kendras "
            "— the Nabhasa Sarpa yoga as a dosha."
        ),
        "effects_text": (
            "Hardship, poverty, cruelty of disposition; weakened foundations of life."
        ),
        "severity_grades": {
            "moderate": "two malefic kendras",
            "severe": "three or four malefic kendras",
        },
        "cancellation_conditions": {
            "bhanga": ["strong benefic trines", "benefic aspect on all kendra malefics"]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 35}],
        "source_citation": BPHS_CITATION,
    },

    # ── §7 — Additional classical doshas from BPHS / tradition ───────────────
    {
        "canonical_id": "chandal_yoga_dosha",
        "name_sa": "Cāṇḍāla Yoga Doṣa (Candra)",
        "name_en": "Chandal Yoga Dosha (Moon-Rahu)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {"conjunction": ["moon", "rahu"]},
        "formation_text": "Moon conjunct Rahu — Chandal yoga; the intellect and emotions corrupted.",
        "effects_text": (
            "Mental distortions, deceptive tendencies, unconventional behaviour; "
            "can also give extraordinary perceptive ability if strong."
        ),
        "severity_grades": {
            "mild": "wide orb, strong Moon",
            "severe": "close conjunction in 5th/9th/12th",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects Moon", "Moon in own/exaltation"]
        },
        "classical_citations": [{"text_id": "classical_tradition"}],
        "source_citation": CLASSICAL_TRADITION,
    },
    {
        "canonical_id": "graha_yuddha_dosha",
        "name_sa": "Graha Yuddha Doṣa",
        "name_en": "Graha Yuddha Dosha (Planetary War)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "two non-luminary planets within 1 degree of each other (excluding Sun/Moon/nodes)",
        },
        "formation_text": (
            "Two planets (excluding Sun, Moon, and nodes) within 1° of each other — "
            "planetary war (graha yuddha). The losing planet (lower declination) is weakened."
        ),
        "effects_text": (
            "The losing planet's significations are damaged for the life; "
            "both planets' significations are disturbed."
        ),
        "severity_grades": {
            "mild": "within 1° but loser not debilitated",
            "severe": "loser also combust or debilitated",
        },
        "cancellation_conditions": {
            "bhanga": ["loser planet in own or exaltation sign (then it may win)"]
        },
        "classical_citations": [{"text_id": "bphs"}],
        "source_citation": BPHS_CITATION,
    },
    {
        "canonical_id": "papa_kartari_lagna",
        "name_sa": "Pāpa Kartari (Lagna)",
        "name_en": "Papa Kartari Dosha (Lagna hemmed by malefics)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "malefics_in": ["2nd_from_lagna", "12th_from_lagna"],
        },
        "formation_text": (
            "Malefics in both the 2nd and 12th from the lagna, hemming the ascendant "
            "— papa-kartari on the lagna."
        ),
        "effects_text": (
            "Body and vitality hemmed; obstacles to self-expression and health; "
            "physical vulnerability."
        ),
        "severity_grades": {
            "moderate": "one classical malefic each side",
            "severe": "Sun/Saturn or Mars/Rahu hemming lagna",
        },
        "cancellation_conditions": {
            "bhanga": ["shubha kartari also present (benefics also flanking)", "lagna lord very strong"]
        },
        "classical_citations": [{"text_id": "phaladeepika"}],
        "source_citation": "Phaladeepika by Mantresvara (classical tradition)",
    },
    {
        "canonical_id": "papa_kartari_moon",
        "name_sa": "Pāpa Kartari (Candra)",
        "name_en": "Papa Kartari Dosha (Moon hemmed by malefics)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "malefics_in": ["2nd_from_moon", "12th_from_moon"],
        },
        "formation_text": "Malefics in the 2nd and 12th from the Moon, hemming the mind.",
        "effects_text": (
            "Mental hemming; anxiety, emotional suppression, psychological vulnerability; "
            "reinforces kemadruma effects."
        ),
        "severity_grades": {
            "moderate": "malefics flanking Moon",
            "severe": "Moon also waning with no benefic aspect",
        },
        "cancellation_conditions": {
            "bhanga": ["benefic aspect on Moon", "Moon in own/exaltation"]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 9}],
        "source_citation": BPHS_CH9,
    },
    {
        "canonical_id": "badhaka_dosha",
        "name_sa": "Bādhaka Doṣa",
        "name_en": "Badhaka Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "badhaka_lord": "lord_of_badhaka_house_afflicting_lagna_or_lagna_lord",
            "badhaka_house_by_lagna_type": {
                "movable_lagna": "11th_house",
                "fixed_lagna": "9th_house",
                "dual_lagna": "7th_house",
            },
        },
        "formation_text": (
            "The Badhaka lord (11th for movable lagnas, 9th for fixed, 7th for dual) "
            "afflicts the lagna or its lord."
        ),
        "effects_text": (
            "Hidden obstacles, unexplained chronic difficulties, enemies from unexpected quarters; "
            "effects are obstructive rather than directly harmful."
        ),
        "severity_grades": {
            "mild": "badhaka lord weak or in friendly sign",
            "severe": "badhaka lord strong in kendra/dusthana aspecting lagna",
        },
        "cancellation_conditions": {
            "bhanga": ["badhaka lord debilitated", "strong benefic on badhaka house"]
        },
        "classical_citations": [{"text_id": "bphs"}],
        "source_citation": BPHS_CITATION,
    },
    {
        "canonical_id": "karaka_dosha",
        "name_sa": "Kāraka Doṣa",
        "name_en": "Karaka Dosha (Karaka in its own house)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "natural significator (karaka) of a house placed in that house itself",
            "example": "Jupiter in 5th (putrakaraka in putra-bhava)",
        },
        "formation_text": (
            "A planet placed in the house it naturally signifies (e.g. Jupiter in 5th, "
            "Venus in 7th) — Karaka Dosha."
        ),
        "effects_text": (
            "Classical rule: karaka in its own bhava can damage the bhava's results "
            "(karako bhava nashaya). The house's external manifestations (spouse, child) "
            "may be hindered despite the significations being strong internally."
        ),
        "severity_grades": {
            "mild": "karaka well-aspected or in own/exaltation",
            "moderate": "default",
        },
        "cancellation_conditions": {
            "bhanga": ["strong bhava lord elsewhere", "additional benefic influence on house"]
        },
        "classical_citations": [{"text_id": "bphs"}],
        "source_citation": BPHS_CITATION,
    },
    {
        "canonical_id": "combust_dosha",
        "name_sa": "Maudhya Doṣa (Āsta)",
        "name_en": "Combust Dosha (Maudhya)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "planet within combustion orb of Sun (varies by planet)",
            "orbs_degrees": {
                "moon": 12,
                "mars": 17,
                "mercury": 14,
                "mercury_retrograde": 12,
                "jupiter": 11,
                "venus": 10,
                "venus_retrograde": 8,
                "saturn": 15,
            },
        },
        "formation_text": (
            "A planet within its classical combustion orb of the Sun — Maudhya (burnt) state."
        ),
        "effects_text": (
            "Planet's significations burnt out or suppressed; the ego (Sun) overwhelms the planet's "
            "natural expression. House lordships of the combust planet are weakened."
        ),
        "severity_grades": {
            "mild": "near combustion boundary",
            "severe": "deep combustion (< 2°) in enemy sign",
        },
        "cancellation_conditions": {
            "bhanga": [
                "planet retrograde (especially Mercury/Venus — reduces combustion effect)",
                "planet in own or exaltation sign despite combustion",
            ]
        },
        "classical_citations": [{"text_id": "bphs"}],
        "source_citation": BPHS_CITATION,
    },
    {
        "canonical_id": "dusthana_trikona_dosha",
        "name_sa": "Dusthāna Tṛtīya Doṣa",
        "name_en": "Dusthana Trikona Dosha (Malefic in trikona)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "malefic_in": "trikona_1_5_9",
            "condition": "malefic_not_a_trikona_lord_itself",
        },
        "formation_text": (
            "A natural malefic in a trikona (1/5/9) without being a trikona lord — "
            "damages fortune, progeny or dharma."
        ),
        "effects_text": (
            "Fortune and dharma afflicted; progeny issues if 5th afflicted; "
            "paternal/guru karma if 9th affected."
        ),
        "severity_grades": {
            "moderate": "one malefic in trikona",
            "severe": "multiple malefics in trikonas",
        },
        "cancellation_conditions": {
            "bhanga": ["malefic is trikona lord (then yogakaraka)", "benefic aspect on trikona"]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 9}],
        "source_citation": BPHS_CH9,
    },
    {
        "canonical_id": "neecha_dosha",
        "name_sa": "Nīca Doṣa (Debilitation)",
        "name_en": "Neecha Dosha (Planet in Debilitation)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "planet": "any",
            "dignity": "debilitated",
            "condition": "no_neecha_bhanga",
        },
        "formation_text": "A planet in its debilitation sign without neecha-bhanga cancellation.",
        "effects_text": (
            "Planet functions at minimum strength; significations degraded; "
            "house lordships weakened. Severity depends on which planet and house."
        ),
        "severity_grades": {
            "mild": "debilitation in upachaya (3/6/10/11)",
            "severe": "debilitation in kendra or trikona without bhanga",
        },
        "cancellation_conditions": {
            "bhanga": [
                "dispositor in kendra from lagna or Moon (neecha-bhanga)",
                "exaltation lord of the debilitated sign in kendra",
                "planet exalted in navamsa",
                "mutual debilitation aspect",
            ]
        },
        "classical_citations": [{"text_id": "bphs"}],
        "source_citation": BPHS_CITATION,
    },
    {
        "canonical_id": "gulika_dosha",
        "name_sa": "Gulika Doṣa (Māndī)",
        "name_en": "Gulika Dosha (Mandi)",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "Gulika (Mandi) — son of Saturn — in kendra or trikona or conjunct a planet",
            "note": "Gulika calculated from Saturn's weekday portion of the day",
        },
        "formation_text": (
            "Gulika (Mandi), a sub-planet / shadow point, in a kendra, trikona "
            "or conjunct a major planet."
        ),
        "effects_text": (
            "Poisoning influence on the house/planet it touches; chronic hidden affliction; "
            "malefic contamination of the significations."
        ),
        "severity_grades": {
            "moderate": "Gulika in neutral position",
            "severe": "Gulika conjunct Moon or lagna lord",
        },
        "cancellation_conditions": {
            "bhanga": ["Jupiter aspects Gulika", "Gulika in its own sign or exaltation by some accounts"]
        },
        "classical_citations": [{"text_id": "bphs"}],
        "source_citation": BPHS_CITATION,
    },
    {
        "canonical_id": "trikona_dusthana_parivartana_dosha",
        "name_sa": "Tṛkoṇa-Dusthāna Parivartana Doṣa",
        "name_en": "Trikona-Dusthana Parivartana Dosha",
        "category": "graha_placement",
        "school": "parashari",
        "formation_rule_jsonb": {
            "requires": "sign_exchange_between_a_trikona_lord_and_a_dusthana_lord_6_8_12",
        },
        "formation_text": (
            "The lord of a trikona (1/5/9) and the lord of a dusthana (6/8/12) exchange signs — "
            "Dainya parivartana tainting fortune."
        ),
        "effects_text": (
            "Fortune or dharma house contaminated by dusthana themes; "
            "obstructed luck, health/debt/loss themes entering the trikona."
        ),
        "severity_grades": {
            "moderate": "one trikona and one dusthana",
            "severe": "involving the 9th and 8th lords",
        },
        "cancellation_conditions": {
            "bhanga": ["strong benefic in the trikona house", "both lords strong despite exchange"]
        },
        "classical_citations": [{"text_id": "bphs", "chapter": 39}],
        "source_citation": BPHS_CITATION,
    },
]

assert len(DOSHAS) == 79, f"Expected 79 doshas, got {len(DOSHAS)}"


# ── Seed function ──────────────────────────────────────────────────────────────

def seed_doshas(
    conn: Any,
    build_id: str | None = None,
    dry_run: bool = False,
    autocommit: bool = True,
) -> dict[str, int]:
    """
    Insert DOSHAS into brahma_dosha_catalog, brahma_ontology (entity_class='dosha'),
    and reference_doshas.

    Returns dict with:
        catalog_inserted, ontology_inserted, ref_inserted, catalog_skipped

    autocommit: if False, caller owns the transaction (pass False from asset_runner).
    """
    if dry_run:
        logger.info("[L0/doshas] dry_run — would insert %d doshas", len(DOSHAS))
        return {
            "catalog_inserted": len(DOSHAS),
            "ontology_inserted": len(DOSHAS),
            "ref_inserted": len(DOSHAS),
            "catalog_skipped": 0,
        }

    now = datetime.now(timezone.utc)
    catalog_inserted = 0
    ontology_inserted = 0
    ref_inserted = 0
    catalog_skipped = 0

    with conn.cursor() as cur:
        # Validate table exists
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name='brahma_dosha_catalog'"
        )
        if cur.fetchone()['count'] == 0:
            raise RuntimeError(
                "brahma_dosha_catalog table does not exist — cannot write bg_doshas. "
                "Apply migration 176 first."
            )

        for d in DOSHAS:
            cid = d["canonical_id"]

            # ── 1. brahma_dosha_catalog (catalog-first; FK anchor) ────────────
            cur.execute(
                """
                INSERT INTO brahma_dosha_catalog (
                    canonical_id, name_sa, name_en, category,
                    formation_rule_jsonb, formation_text, effects_text,
                    severity_grades, cancellation_conditions,
                    classical_citations, source_chunk_ids,
                    associated_remedies, school, created_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s::jsonb, %s, %s,
                    %s::jsonb, %s::jsonb,
                    %s::jsonb, %s,
                    %s, %s, %s
                )
                ON CONFLICT (canonical_id) DO NOTHING
                """,
                (
                    cid,
                    d["name_sa"],
                    d["name_en"],
                    d["category"],
                    json.dumps(d["formation_rule_jsonb"]),
                    d["formation_text"],
                    d["effects_text"],
                    json.dumps(d.get("severity_grades") or {}),
                    json.dumps(d.get("cancellation_conditions") or {}),
                    json.dumps(d.get("classical_citations") or []),
                    [],   # source_chunk_ids — BIGINT[] default
                    [],   # associated_remedies — UUID[] seeded empty (Tier 3 fills)
                    d["school"],
                    now,
                ),
            )
            if cur.rowcount > 0:
                catalog_inserted += 1
            else:
                catalog_skipped += 1
                logger.debug("[L0/doshas] skipped (conflict) catalog: %s", cid)

            # ── 2. brahma_ontology (entity_class='dosha') ─────────────────────
            cur.execute(
                """
                INSERT INTO brahma_ontology (
                    entity_class, canonical_id, canonical_name_en, canonical_name_sa,
                    synonyms, description, source_citation, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (entity_class, canonical_id) DO NOTHING
                """,
                (
                    "dosha",
                    cid,
                    d["name_en"],
                    d["name_sa"],
                    [],   # synonyms — empty for doshas
                    d["effects_text"][:200] if d.get("effects_text") else None,
                    d.get("source_citation", CLASSICAL_TRADITION),
                    now,
                ),
            )
            if cur.rowcount > 0:
                ontology_inserted += 1

            # ── 3. reference_doshas pointer (catalog_id FK already satisfied) ─
            cur.execute(
                """
                INSERT INTO reference_doshas (canonical_id, name_en, category)
                VALUES (%s, %s, %s)
                ON CONFLICT (canonical_id) DO NOTHING
                """,
                (cid, d["name_en"], d["category"]),
            )
            if cur.rowcount > 0:
                ref_inserted += 1

        logger.info(
            "[L0/doshas] catalog: +%d inserted / %d skipped; ontology: +%d; ref: +%d",
            catalog_inserted, catalog_skipped, ontology_inserted, ref_inserted,
        )

    if autocommit:
        conn.commit()

    return {
        "catalog_inserted": catalog_inserted,
        "ontology_inserted": ontology_inserted,
        "ref_inserted": ref_inserted,
        "catalog_skipped": catalog_skipped,
    }
