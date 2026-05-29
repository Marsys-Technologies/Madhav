"""
dasha_systems.py — G15 Dasha System Reference Library
======================================================
Comprehensive reference for all major Vedic dasha systems used in Jyotish.
Covers 32 classical systems across four classes: nakshatra-based, Jaimini,
Tajik (Varshaphala), and special systems.

canonical_id: G15
stream: A
session: G15-S1 [BUILD-ORCH-A-25]

Classical sources:
  - Brihat Parashara Hora Shastra (BPHS), Dasha chapters
  - Jaimini Sutras, Adhyaya 1–4
  - Tajika Neelakanthi, Varshaphala dasha chapters
  - KP (Krishnamurti Paddhati) system references
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# DASHA_SYSTEMS — primary reference table
# ---------------------------------------------------------------------------
# Key   : canonical system name (snake_case)
# Value : dict with the following required keys:
#   name                  : str  — display name
#   system_class          : str  — nakshatra_based | jaimini | tajik | special
#   total_years           : int|float — total dasha cycle duration in years
#   starting_point        : str  — how the starting point is determined
#   period_sequence       : list[str] — grahas/signs in dasha sequence order
#   period_lengths        : dict[str, int|float] — period duration per graha/sign
#                           (present on nakshatra_based systems; {} otherwise)
#   sub_period_divisor    : str  — how antardashas are derived
#   applicability_condition : str — when this system is preferred/applicable
#   activation_condition  : str  — specific chart conditions for validity
#   classical_source      : str  — citation
#   acharya_selected      : bool — True for 7 MARSYS instrument systems

DASHA_SYSTEMS: dict[str, dict] = {

    # -----------------------------------------------------------------------
    # 1. NAKSHATRA-BASED (nakshatra_based) — 12 systems
    # -----------------------------------------------------------------------

    "vimshottari": {
        "name": "Vimshottari Dasha",
        "system_class": "nakshatra_based",
        "total_years": 120,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "ketu", "venus", "sun", "moon", "mars",
            "rahu", "jupiter", "saturn", "mercury",
        ],
        "period_lengths": {
            "ketu": 7, "venus": 20, "sun": 6, "moon": 10, "mars": 7,
            "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17,
        },
        "sub_period_divisor": (
            "Proportional: antardasha = (dasha_years × antardasha_years) / 120 years"
        ),
        "applicability_condition": (
            "Universal — most widely used in Parashari Jyotish for all charts"
        ),
        "activation_condition": "No conditional restriction; applicable to all charts",
        "classical_source": "BPHS, Dasha Adhyaya (Ch. 46–48)",
        "acharya_selected": True,
    },

    "ashtottari": {
        "name": "Ashtottari Dasha",
        "system_class": "nakshatra_based",
        "total_years": 108,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "sun", "moon", "mars", "mercury",
            "saturn", "jupiter", "rahu", "venus",
        ],
        "period_lengths": {
            "sun": 6, "moon": 15, "mars": 8, "mercury": 17,
            "saturn": 10, "jupiter": 19, "rahu": 12, "venus": 21,
        },
        "sub_period_divisor": (
            "Proportional: antardasha = (dasha_years × antardasha_years) / 108 years"
        ),
        "applicability_condition": (
            "Used when Rahu is in an angle or trine from Lagna and is not in "
            "own sign or exaltation, and not conjunct or aspected by the 7th lord"
        ),
        "activation_condition": (
            "Rahu in kendra/trikona, not in own/exalted sign, not associated "
            "with 7th lord"
        ),
        "classical_source": "BPHS, Ashtottari Dasha Adhyaya (Ch. 49)",
        "acharya_selected": True,
    },

    "yogini": {
        "name": "Yogini Dasha",
        "system_class": "nakshatra_based",
        "total_years": 36,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "mangala", "pingala", "dhanya", "bhramari",
            "bhadrika", "ulka", "siddha", "sankata",
        ],
        "period_lengths": {
            "mangala": 1, "pingala": 2, "dhanya": 3, "bhramari": 4,
            "bhadrika": 5, "ulka": 6, "siddha": 7, "sankata": 8,
        },
        "sub_period_divisor": (
            "Proportional within each yogini period by nakshatra lord sequence"
        ),
        "applicability_condition": (
            "Widely used in North Indian tradition; especially for short-term timing "
            "and muhurta analysis; effective supplementary dasha"
        ),
        "activation_condition": "No conditional restriction; applicable to all charts",
        "classical_source": "Devi Bhagavata Purana; Yogini Dasha tradition in BPHS supplements",
        "acharya_selected": True,
    },

    "shodashottari": {
        "name": "Shodashottari Dasha",
        "system_class": "nakshatra_based",
        "total_years": 116,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "sun", "mars", "jupiter", "saturn",
            "ketu", "moon", "venus", "rahu",
        ],
        "period_lengths": {
            "sun": 11, "mars": 12, "jupiter": 13, "saturn": 14,
            "ketu": 15, "moon": 16, "venus": 17, "rahu": 18,
        },
        "sub_period_divisor": (
            "Proportional: antardasha = (dasha_years × antardasha_years) / 116 years"
        ),
        "applicability_condition": (
            "Used when Lagna lord is in an angle from Moon in navamsa"
        ),
        "activation_condition": (
            "Lagna lord occupies a kendra (1,4,7,10) from Moon in navamsa chart"
        ),
        "classical_source": "BPHS, Shodashottari Dasha Adhyaya",
        "acharya_selected": False,
    },

    "dvadashottari": {
        "name": "Dvadashottari Dasha",
        "system_class": "nakshatra_based",
        "total_years": 112,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "sun", "mars", "jupiter", "mercury",
            "venus", "moon", "saturn", "rahu",
        ],
        "period_lengths": {
            "sun": 7, "mars": 8, "jupiter": 9, "mercury": 10,
            "venus": 11, "moon": 12, "saturn": 13, "rahu": 14,
        },
        "sub_period_divisor": (
            "Proportional: antardasha = (dasha_years × antardasha_years) / 112 years"
        ),
        "applicability_condition": (
            "Used when Venus is in an angle or trine from Lagna in navamsa"
        ),
        "activation_condition": (
            "Venus occupies kendra or trikona (1,4,5,7,9,10) from Lagna in navamsa"
        ),
        "classical_source": "BPHS, Dvadashottari Dasha Adhyaya",
        "acharya_selected": False,
    },

    "panchottari": {
        "name": "Panchottari Dasha",
        "system_class": "nakshatra_based",
        "total_years": 100,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "sun", "moon", "mars", "mercury",
            "venus", "jupiter", "saturn",
        ],
        "period_lengths": {
            "sun": 12, "moon": 13, "mars": 14, "mercury": 15,
            "venus": 16, "jupiter": 17, "saturn": 13,
        },
        "sub_period_divisor": (
            "Proportional: antardasha = (dasha_years × antardasha_years) / 100 years"
        ),
        "applicability_condition": (
            "Used when Lagna is Cancer and Moon or Cancer lord is in a kendra"
        ),
        "activation_condition": (
            "Lagna is Cancer (Karkata); Moon or sign lord in angle from Lagna"
        ),
        "classical_source": "BPHS, Panchottari Dasha Adhyaya",
        "acharya_selected": False,
    },

    "shatabdika": {
        "name": "Shatabdika Dasha",
        "system_class": "nakshatra_based",
        "total_years": 100,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "sun", "moon", "mars", "mercury", "jupiter",
            "venus", "saturn", "rahu", "ketu", "lagna_lord",
        ],
        "period_lengths": {
            "sun": 10, "moon": 10, "mars": 10, "mercury": 10, "jupiter": 10,
            "venus": 10, "saturn": 10, "rahu": 10, "ketu": 10, "lagna_lord": 10,
        },
        "sub_period_divisor": "Equal: each antardasha = dasha_years / 10",
        "applicability_condition": (
            "Century-based equal-period system; used for longer lifespan analysis"
        ),
        "activation_condition": "No conditional restriction; applicable to all charts",
        "classical_source": "BPHS, Shatabdika Dasha Adhyaya",
        "acharya_selected": False,
    },

    "chatturashitika": {
        "name": "Chatturashitika Dasha",
        "system_class": "nakshatra_based",
        "total_years": 84,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "sun", "moon", "mars", "mercury", "venus",
            "jupiter", "saturn", "rahu", "ketu", "lagna",
        ],
        "period_lengths": {
            "sun": 12, "moon": 11, "mars": 10, "mercury": 9, "venus": 8,
            "jupiter": 7, "saturn": 5, "rahu": 6, "ketu": 7, "lagna": 9,
        },
        "sub_period_divisor": (
            "Proportional: antardasha = (dasha_years × antardasha_years) / 84 years"
        ),
        "applicability_condition": (
            "Used when Sun is in an angle from Lagna in navamsa chart"
        ),
        "activation_condition": (
            "Sun occupies kendra (1,4,7,10) from Lagna in navamsa chart"
        ),
        "classical_source": "BPHS, Chatturashitika Dasha Adhyaya",
        "acharya_selected": False,
    },

    "dvisaptati": {
        "name": "Dvisaptati Sama Dasha",
        "system_class": "nakshatra_based",
        "total_years": 72,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "sun", "moon", "mars", "mercury",
            "jupiter", "venus", "saturn", "rahu", "ketu",
        ],
        "period_lengths": {
            "sun": 8, "moon": 8, "mars": 8, "mercury": 8,
            "jupiter": 8, "venus": 8, "saturn": 8, "rahu": 8, "ketu": 8,
        },
        "sub_period_divisor": "Equal: each antardasha = 8 / 9 years per graha",
        "applicability_condition": (
            "Used when Lagna lord is in 7H or 7L is in Lagna (mutual exchange)"
        ),
        "activation_condition": (
            "Lagna lord occupies 7th house OR 7th lord occupies Lagna"
        ),
        "classical_source": "BPHS, Dvisaptati Sama Dasha Adhyaya",
        "acharya_selected": False,
    },

    "shashtihayani": {
        "name": "Shashtihayani Dasha",
        "system_class": "nakshatra_based",
        "total_years": 60,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "sun", "moon", "mars", "mercury",
            "jupiter", "venus", "saturn",
        ],
        "period_lengths": {
            "sun": 8, "moon": 8, "mars": 9, "mercury": 9,
            "jupiter": 9, "venus": 8, "saturn": 9,
        },
        "sub_period_divisor": (
            "Proportional: antardasha = (dasha_years × antardasha_years) / 60 years"
        ),
        "applicability_condition": (
            "Used when Sun is in Lagna in navamsa chart; suited to shorter lifespans"
        ),
        "activation_condition": "Sun occupies Lagna (1st house) in navamsa chart",
        "classical_source": "BPHS, Shashtihayani Dasha Adhyaya",
        "acharya_selected": False,
    },

    "shatatrimshat": {
        "name": "Shatatrimshat Sama Dasha",
        "system_class": "nakshatra_based",
        "total_years": 36,
        "starting_point": "birth nakshatra of Moon",
        "period_sequence": [
            "sun", "moon", "mars", "mercury",
            "jupiter", "venus", "saturn",
        ],
        "period_lengths": {
            "sun": 4, "moon": 4, "mars": 5, "mercury": 5,
            "jupiter": 6, "venus": 6, "saturn": 6,
        },
        "sub_period_divisor": "Equal: each antardasha = dasha_years / 7",
        "applicability_condition": (
            "Used when Saturn is in Lagna; associated with saturnine/late-blooming charts"
        ),
        "activation_condition": "Saturn occupies Lagna (1st house) in natal chart",
        "classical_source": "BPHS, Shatatrimshat Sama Dasha Adhyaya",
        "acharya_selected": False,
    },

    "tara": {
        "name": "Tara Dasha",
        "system_class": "nakshatra_based",
        "total_years": 36,
        "starting_point": "birth nakshatra of Moon — grouped into 9 tara groups",
        "period_sequence": [
            "janma", "sampat", "vipat", "kshema", "pratyak",
            "sadhaka", "vadha", "mitra", "atimitra",
        ],
        "period_lengths": {
            "janma": 4, "sampat": 4, "vipat": 4, "kshema": 4, "pratyak": 4,
            "sadhaka": 4, "vadha": 4, "mitra": 4, "atimitra": 4,
        },
        "sub_period_divisor": "Equal: each tara period = 4 years (36 / 9)",
        "applicability_condition": (
            "Transit and muhurta verification system; used alongside Vimshottari "
            "for event timing confirmation"
        ),
        "activation_condition": "No conditional restriction; supplementary to other dasha systems",
        "classical_source": "Phaladeepika, Transit (Gochara) chapter; BPHS Tara chapter",
        "acharya_selected": False,
    },

    # -----------------------------------------------------------------------
    # 2. JAIMINI SYSTEMS (jaimini) — 12 systems
    # -----------------------------------------------------------------------

    "jaimini_chara": {
        "name": "Jaimini Chara Dasha",
        "system_class": "jaimini",
        "total_years": 144,  # 12 signs × up to 12 years each; max cycle ~144yr
        "starting_point": (
            "Strongest sign, typically Lagna sign or sign containing Atmakaraka; "
            "direction (forward/backward) determined by sign type and lord position"
        ),
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},  # Variable: based on planet count and sign lord position
        "sub_period_divisor": (
            "Each sign's antardasha sequence runs through all 12 signs proportionally"
        ),
        "applicability_condition": (
            "Primary Jaimini dasha; universally applicable for Jaimini chart reading; "
            "especially suited to career, marriage, and general life events"
        ),
        "activation_condition": (
            "No conditional restriction; applicable to all charts under Jaimini system"
        ),
        "classical_source": "Jaimini Sutras, Adhyaya 2, Pada 3 (Chara Dasha sutras)",
        "acharya_selected": True,
    },

    "jaimini_sthira": {
        "name": "Jaimini Sthira Dasha",
        "system_class": "jaimini",
        "total_years": 96,  # 12 signs × average ~8 years
        "starting_point": "Lagna sign; progression by sign type with fixed durations",
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},  # Fixed by modality: movable=9yr, fixed=8yr, dual=7yr
        "sub_period_divisor": (
            "Fixed sub-periods by sign modality: movable=9yr, fixed=8yr, dual=7yr"
        ),
        "applicability_condition": (
            "Used for longevity analysis and determining time of death; "
            "effective for Jaimini Ayurda analysis"
        ),
        "activation_condition": "Applied in Jaimini Ayurda (longevity) computations",
        "classical_source": "Jaimini Sutras, Adhyaya 2, Pada 4 (Sthira Dasha sutras)",
        "acharya_selected": False,
    },

    "jaimini_niryaana_shoola": {
        "name": "Jaimini Niryaana Shoola Dasha",
        "system_class": "jaimini",
        "total_years": 108,
        "starting_point": (
            "8th house lord sign; tri-rashi variant using sign of 8th lord "
            "and its trines for longevity analysis"
        ),
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Tri-rashi: each main sign dasha subdivides into its trine signs",
        "applicability_condition": (
            "Specialised for determining time and nature of death; "
            "Shoola (trident) dasha used for mortality timing"
        ),
        "activation_condition": (
            "Applied specifically for Niryaana (death/exit) timing in Jaimini analysis"
        ),
        "classical_source": "Jaimini Sutras; Sanjay Rath commentary on Shoola Dasha",
        "acharya_selected": False,
    },

    "jaimini_trikona": {
        "name": "Jaimini Trikona Dasha",
        "system_class": "jaimini",
        "total_years": 108,
        "starting_point": (
            "Sign containing Atmakaraka in navamsa (Karakamsa); "
            "proceeds through trine signs from Karakamsa"
        ),
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Trine-based: proceeds through trikona signs from starting sign",
        "applicability_condition": (
            "Used for soul-level and spiritual life events; "
            "especially relevant when Atmakaraka is strong"
        ),
        "activation_condition": (
            "Requires strong Atmakaraka; Karakamsa sign clearly determinable in navamsa"
        ),
        "classical_source": "Jaimini Sutras, Adhyaya 1, Pada 2; Karakamsa chapter",
        "acharya_selected": False,
    },

    "jaimini_brahma": {
        "name": "Jaimini Brahma Dasha",
        "system_class": "jaimini",
        "total_years": 108,
        "starting_point": (
            "Brahma planet sign; Brahma is determined by strongest between "
            "6th lord from Lagna and 6th lord from Arudha Lagna"
        ),
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Standard Jaimini sign-based proportional sub-periods",
        "applicability_condition": (
            "Used for matters of sustenance (prana), livelihood, and social dharma"
        ),
        "activation_condition": (
            "Brahma planet clearly identifiable; used in Brahma-Vishnu-Rudra triad analysis"
        ),
        "classical_source": "Jaimini Sutras; Narasimha Rao commentary on special Jaimini dashas",
        "acharya_selected": False,
    },

    "jaimini_vimsa": {
        "name": "Jaimini Vimsa Dasha",
        "system_class": "jaimini",
        "total_years": 20,
        "starting_point": "Sign containing Moon; 20-year Jaimini sign cycle",
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Equal: each sign period = 20/12 years approximately",
        "applicability_condition": (
            "Compressed Jaimini cycle; used for medium-term analysis within a 20-year window"
        ),
        "activation_condition": "No conditional restriction within Jaimini system",
        "classical_source": "Jaimini Sutras supplementary traditions",
        "acharya_selected": False,
    },

    "jaimini_sudasa": {
        "name": "Jaimini Sudasa Dasha",
        "system_class": "jaimini",
        "total_years": 120,
        "starting_point": (
            "Sign containing Arudha Lagna (AL); "
            "proceeds through signs for financial and sukha (happiness) analysis"
        ),
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Jaimini sign-based proportional antardasha",
        "applicability_condition": (
            "Preferred for predictions about wealth, image, and social happiness; "
            "Su-dasa means 'good/auspicious dasha'"
        ),
        "activation_condition": (
            "Strong Arudha Lagna required; Arudha Lagna clearly distinguishable from Lagna"
        ),
        "classical_source": "Jaimini Sutras; Sanjay Rath Jaimini tradition",
        "acharya_selected": False,
    },

    "jaimini_drig": {
        "name": "Jaimini Drig Dasha",
        "system_class": "jaimini",
        "total_years": 120,
        "starting_point": (
            "Sign that is most strongly aspected (drig = seen/aspected); "
            "uses Jaimini rasi-drishti to determine starting sign"
        ),
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Jaimini sign-based with drishti-weighted sub-periods",
        "applicability_condition": (
            "Used for events related to recognition, visibility, and public life; "
            "drig = that which is seen"
        ),
        "activation_condition": (
            "Requires clear Jaimini rasi-drishti analysis; "
            "most aspected sign determinable without conflict"
        ),
        "classical_source": "Jaimini Sutras, Adhyaya 1–2; Drig Dasha sutras",
        "acharya_selected": False,
    },

    "naisargika": {
        "name": "Naisargika Dasha",
        "system_class": "jaimini",
        "total_years": 120,
        "starting_point": (
            "Natural order of planetary maturation; "
            "Moon governs infancy, then planets in order of natural rulership"
        ),
        "period_sequence": [
            "moon", "mars", "mercury", "venus",
            "jupiter", "sun", "saturn",
        ],
        "period_lengths": {
            "moon": 1, "mars": 2, "mercury": 9, "venus": 20,
            "jupiter": 18, "sun": 20, "saturn": 50,
        },
        "sub_period_divisor": (
            "Proportional: antardasha = (dasha_years × antardasha_years) / 120 years"
        ),
        "applicability_condition": (
            "Universal natural dasha representing stages of human life from birth to old age; "
            "reflects natural karaka (significator) energies at each life stage"
        ),
        "activation_condition": "No conditional restriction; applicable to all charts",
        "classical_source": "BPHS, Naisargika Dasha Adhyaya; Jaimini Sutras supplementary",
        "acharya_selected": True,
    },

    "mandukya": {
        "name": "Mandukya Dasha",
        "system_class": "jaimini",
        "total_years": 108,
        "starting_point": (
            "Lagna sign; alternates between trines in a 'frog-jump' pattern, "
            "skipping 4 signs at a time within trine groups"
        ),
        "period_sequence": [
            "aries", "leo", "sagittarius",
            "taurus", "virgo", "capricorn",
            "gemini", "libra", "aquarius",
            "cancer", "scorpio", "pisces",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Trine jump: proceeds through each trine group consecutively",
        "applicability_condition": (
            "Used for spiritual and dharmic evolution analysis; "
            "Manduka (frog) symbolises leaping spiritual progress"
        ),
        "activation_condition": (
            "Applied in charts with strong trine emphasis; "
            "Lagna lord in trine strengthens this dasha's validity"
        ),
        "classical_source": "Jaimini Sutras supplementary; Mandukya Dasha tradition",
        "acharya_selected": False,
    },

    "padakrama": {
        "name": "Padakrama Dasha",
        "system_class": "jaimini",
        "total_years": 108,
        "starting_point": (
            "Lagna sign; step-by-step progression sign by sign "
            "in natural zodiac order from Lagna"
        ),
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Sequential: each sign proceeds one step forward",
        "applicability_condition": (
            "Step-progression dasha for systematic life-stage analysis; "
            "Pada = step/pada, Krama = sequence"
        ),
        "activation_condition": "No conditional restriction; applicable in Jaimini analysis",
        "classical_source": "Jaimini Sutras; Padakrama Dasha sub-tradition",
        "acharya_selected": False,
    },

    "jaimini_karaka": {
        "name": "Jaimini Karaka Dasha",
        "system_class": "jaimini",
        "total_years": 108,
        "starting_point": (
            "Atmakaraka planet's sign; sequences through signs held by Chara Karakas "
            "in descending karaka order (AK→AmK→BK→MK→PK→GK→DK)"
        ),
        "period_sequence": [
            "atmakaraka_sign", "amatyakaraka_sign", "bhratrukaraka_sign",
            "matrukaraka_sign", "putrakaraka_sign", "gnatikaraka_sign",
            "darakaraka_sign",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Chara Karaka order: sub-periods by next karaka sign",
        "applicability_condition": (
            "Used for soul-purpose and karaka-specific predictions; "
            "Chara Karakas reflect temporary significators based on degree"
        ),
        "activation_condition": (
            "All 7 Chara Karakas clearly determinable; "
            "Atmakaraka not in same degree as Darakaraka"
        ),
        "classical_source": "Jaimini Sutras, Adhyaya 1, Pada 1 (Chara Karaka chapter)",
        "acharya_selected": False,
    },

    # -----------------------------------------------------------------------
    # 3. TAJIK SYSTEMS (tajik) — 4 systems
    # -----------------------------------------------------------------------

    "mudda": {
        "name": "Mudda Dasha (Varshaphala)",
        "system_class": "tajik",
        "total_years": 1,
        "starting_point": (
            "Solar Return Lagna (Varsha Lagna); same graha sequence as Vimshottari "
            "but compressed to 365 days from the annual Solar Return"
        ),
        "period_sequence": [
            "ketu", "venus", "sun", "moon", "mars",
            "rahu", "jupiter", "saturn", "mercury",
        ],
        "period_lengths": {},  # Proportional within 365 days
        "sub_period_divisor": (
            "Proportional: Mudda dasha period = (Vimshottari years / 120) × 365 days"
        ),
        "applicability_condition": (
            "Primary Varshaphala (annual chart) dasha; mandatory in Tajik analysis; "
            "governs events within a specific solar year"
        ),
        "activation_condition": (
            "Applied in Varshaphala (Solar Return) chart from moment Sun returns "
            "to natal longitude each year"
        ),
        "classical_source": "Tajika Neelakanthi, Varshaphala Dasha chapter; Tajik tradition",
        "acharya_selected": True,
    },

    "patyayini": {
        "name": "Patyayini Dasha",
        "system_class": "tajik",
        "total_years": 120,
        "starting_point": (
            "Varsha (annual) Lagna; Tajik dasha variant for longer-term "
            "predictions spanning multiple years from the Solar Return"
        ),
        "period_sequence": [
            "ketu", "venus", "sun", "moon", "mars",
            "rahu", "jupiter", "saturn", "mercury",
        ],
        "period_lengths": {},
        "sub_period_divisor": (
            "Proportional within Patyayini cycle; sub-periods by Vimshottari ratios"
        ),
        "applicability_condition": (
            "Used in advanced Tajik analysis for multi-year Varshaphala predictions; "
            "complements Mudda for longer trends"
        ),
        "activation_condition": "Applied in Varshaphala analysis for multi-year event windows",
        "classical_source": "Tajika Neelakanthi, Patyayini Dasha chapter",
        "acharya_selected": False,
    },

    "sahema": {
        "name": "Sahema Dasha",
        "system_class": "tajik",
        "total_years": 120,
        "starting_point": (
            "Lot/Saham position in Varsha chart; "
            "uses the specific Saham (Arabic Part) as the dasha starting point"
        ),
        "period_sequence": [],
        "period_lengths": {},
        "sub_period_divisor": "Based on sign lord of the Saham position; standard Tajik ratios",
        "applicability_condition": (
            "Saham-based prediction for specific life domains (wealth Saham for finance, "
            "vivah Saham for marriage, etc.)"
        ),
        "activation_condition": (
            "Specific Saham position clearly calculable in Varsha chart; "
            "requires precise birth time for Saham accuracy"
        ),
        "classical_source": "Tajika Neelakanthi, Saham (Lot) chapters",
        "acharya_selected": False,
    },

    "varsha_vimshottari": {
        "name": "Varsha Vimshottari Dasha",
        "system_class": "tajik",
        "total_years": 1,
        "starting_point": (
            "Birth nakshatra of Moon applied to Varsha (Solar Return) chart; "
            "Vimshottari sequence applied within the annual chart's year"
        ),
        "period_sequence": [
            "ketu", "venus", "sun", "moon", "mars",
            "rahu", "jupiter", "saturn", "mercury",
        ],
        "period_lengths": {},
        "sub_period_divisor": (
            "Proportional: same as Vimshottari ratios but compressed to 365 days"
        ),
        "applicability_condition": (
            "Supplementary annual dasha using natal Moon nakshatra applied to "
            "Varsha chart; used alongside Mudda for annual predictions"
        ),
        "activation_condition": "Applied in Varshaphala when Mudda and Patyayini are also computed",
        "classical_source": "Tajika Neelakanthi, Varshaphala chapter; KP tradition annual methods",
        "acharya_selected": False,
    },

    # -----------------------------------------------------------------------
    # 4. SPECIAL SYSTEMS (special) — 4 systems
    # -----------------------------------------------------------------------

    "kalachakra": {
        "name": "Kalachakra Dasha",
        "system_class": "special",
        "total_years": 100,
        "starting_point": (
            "Navamsa pada of birth Moon nakshatra; direction (Deha/Jeeva) and "
            "sequence determined by specific navamsa table with forward/backward movement"
        ),
        "period_sequence": [
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        ],
        "period_lengths": {},  # Complex table-based, varies by navamsa direction
        "sub_period_divisor": (
            "Navamsa table: each sign's period subdivides by the same Kalachakra table "
            "in the opposite direction (Deha→Jeeva or Jeeva→Deha)"
        ),
        "applicability_condition": (
            "Advanced navamsa-based dasha for deep karmic and spiritual timing; "
            "extremely sensitive to birth time accuracy; used by specialists only"
        ),
        "activation_condition": (
            "Requires precise birth time to 1-minute accuracy; "
            "navamsa pada of Moon nakshatra must be unambiguous"
        ),
        "classical_source": "BPHS, Kalachakra Dasha Adhyaya (Ch. 67); Neelakanthi commentary",
        "acharya_selected": True,
    },

    "sphuta": {
        "name": "Sphuta Dasha",
        "system_class": "special",
        "total_years": 120,
        "starting_point": (
            "Sphuta (true/precise) point calculated from Sun's position; "
            "uses a specific degree-based calculation for dasha initiation point"
        ),
        "period_sequence": [
            "sun", "moon", "mars", "mercury",
            "jupiter", "venus", "saturn", "rahu", "ketu",
        ],
        "period_lengths": {},
        "sub_period_divisor": "Proportional by Sphuta degree and graha period weights",
        "applicability_condition": (
            "Used in advanced predictive work; sensitive to precise Sun position; "
            "Sphuta = 'clear/precise' indicating exactitude of calculation"
        ),
        "activation_condition": (
            "Requires precise birth time; Sun's exact degree-minute determinable; "
            "used as verification layer alongside Vimshottari"
        ),
        "classical_source": "BPHS, Sphuta computation chapters; advanced Parashari tradition",
        "acharya_selected": False,
    },

    "vidhanottari": {
        "name": "Vidhanottari Dasha",
        "system_class": "special",
        "total_years": 120,
        "starting_point": "Birth nakshatra of Moon; variant sequence and period weights",
        "period_sequence": [
            "ketu", "venus", "sun", "moon", "mars",
            "rahu", "jupiter", "saturn", "mercury",
        ],
        "period_lengths": {
            "ketu": 7, "venus": 20, "sun": 6, "moon": 10, "mars": 7,
            "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17,
        },
        "sub_period_divisor": "Proportional variant of Vimshottari with modified sub-period rules",
        "applicability_condition": (
            "Variant of Vimshottari used in specific regional traditions; "
            "applies modified period weighting for certain grahas"
        ),
        "activation_condition": (
            "Used in specific regional (especially some South Indian) traditions "
            "as a cross-check with standard Vimshottari"
        ),
        "classical_source": "BPHS variant traditions; regional Jyotish commentaries",
        "acharya_selected": False,
    },

    "hadda": {
        "name": "Hadda (Egyptian Terms) Dasha",
        "system_class": "special",
        "total_years": 120,
        "starting_point": (
            "Hadda term (Egyptian term) sub-division of the sign containing the Lagna "
            "or Moon; each sign is divided into 5 unequal Hadda sections assigned to "
            "5 grahas (excluding Sun and Moon)"
        ),
        "period_sequence": [
            "jupiter", "venus", "mercury", "mars", "saturn",
        ],
        "period_lengths": {},  # Variable by sign; degrees-based within each sign
        "sub_period_divisor": (
            "Degree-based: antardasha proportional to Hadda degree widths within sign"
        ),
        "applicability_condition": (
            "Hellenistic-derived term dasha; used in Tajik and syncretic Jyotish traditions; "
            "Hadda = Egyptian term boundary sub-divisions"
        ),
        "activation_condition": (
            "Applied in charts using Hellenistic/Tajik synthesis; "
            "birth degree within sign must fall in a determinable Hadda section"
        ),
        "classical_source": "Tajika Neelakanthi; Hellenistic astrological tradition (Ptolemy, Tetrabiblos)",
        "acharya_selected": False,
    },
}


# ---------------------------------------------------------------------------
# MODULE-LEVEL INTEGRITY ASSERTIONS
# ---------------------------------------------------------------------------
assert len(DASHA_SYSTEMS) >= 32, \
    f"Expected at least 32 dasha systems, found {len(DASHA_SYSTEMS)}"
assert all("system_class" in v for v in DASHA_SYSTEMS.values()), \
    "Every dasha system entry must have a 'system_class' key"
assert all("total_years" in v for v in DASHA_SYSTEMS.values()), \
    "Every dasha system entry must have a 'total_years' key"
assert all("classical_source" in v for v in DASHA_SYSTEMS.values()), \
    "Every dasha system entry must have a 'classical_source' key"

_acharya = [k for k, v in DASHA_SYSTEMS.items() if v.get("acharya_selected")]
assert len(_acharya) == 7, \
    f"Expected 7 acharya-selected systems, got {len(_acharya)}: {_acharya}"

assert "vimshottari" in DASHA_SYSTEMS, "vimshottari must be present"
assert DASHA_SYSTEMS["vimshottari"]["total_years"] == 120, \
    "Vimshottari total_years must be 120"
assert sum(DASHA_SYSTEMS["vimshottari"]["period_lengths"].values()) == 120, \
    "Vimshottari period_lengths must sum to 120"


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_dasha_system(name: str) -> dict:
    """Return the dasha system dict for the given name.

    Args:
        name: Canonical system name (case-insensitive), e.g. 'vimshottari',
              'JAIMINI_CHARA', 'Mudda'.

    Returns:
        The dasha system dict with all fields.

    Raises:
        KeyError: if the named system is not found in DASHA_SYSTEMS.
    """
    key = name.lower()
    if key not in DASHA_SYSTEMS:
        raise KeyError(
            f"Dasha system '{name}' not found. "
            f"Available systems: {sorted(DASHA_SYSTEMS.keys())}"
        )
    return DASHA_SYSTEMS[key]


def list_systems_by_class(system_class: str) -> list[str]:
    """Return list of system names belonging to the given system class.

    Args:
        system_class: One of 'nakshatra_based', 'jaimini', 'tajik', 'special'.

    Returns:
        Sorted list of canonical system name strings for that class.
    """
    return sorted(
        k for k, v in DASHA_SYSTEMS.items()
        if v["system_class"] == system_class
    )


def get_acharya_selected_systems() -> list[str]:
    """Return list of the 7 acharya-selected system names.

    These are the systems selected for the MARSYS Jyotish instrument:
    Vimshottari, Yogini, Ashtottari, Jaimini Chara, Naisargika, Mudda,
    Kalachakra.

    Returns:
        Sorted list of 7 canonical system name strings.
    """
    return sorted(k for k, v in DASHA_SYSTEMS.items() if v.get("acharya_selected"))


def get_total_years(name: str) -> float:
    """Return the total_years value for the named dasha system.

    Args:
        name: Canonical system name (case-insensitive).

    Returns:
        Total cycle duration in years (int or float).

    Raises:
        KeyError: if the named system is not found.
    """
    return float(get_dasha_system(name)["total_years"])


def get_period_sequence(name: str) -> list[str]:
    """Return the period_sequence for the named dasha system.

    Args:
        name: Canonical system name (case-insensitive).

    Returns:
        List of graha/sign names in dasha sequence order.
        Returns an empty list if the system has no fixed sequence.

    Raises:
        KeyError: if the named system is not found.
    """
    return get_dasha_system(name).get("period_sequence", [])
