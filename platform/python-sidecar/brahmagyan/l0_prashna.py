"""
brahmagyan/l0_prashna.py
L0 static seed for Prashna (Horary) reference tables.
Chart-agnostic — no per-chart computation at this layer.
All rules carry classical citations; uncited rules are not stored.
"""
from __future__ import annotations
from typing import Any

# ---------------------------------------------------------------------------
# §1 — Prashna Lagna methods
# ---------------------------------------------------------------------------

PRASHNA_LAGNA_METHODS: list[dict[str, Any]] = [
    {
        "method_id": "tajik_moment_lagna",
        "method_name": "Tajik Moment Lagna",
        "method_name_sa": "Tājika Prashna Lagna",
        "derivation_rule": (
            "The Ascendant computed for the exact moment and location at which the querent "
            "poses the question. The rising degree becomes the Prashna Lagna; the chart cast "
            "for this moment is the primary Tajika horary chart."
        ),
        "derivation_rule_jsonb": {
            "input": "datetime_utc + querent_lat_lon",
            "output": "prashna_lagna_sign + degree",
            "computation": "swiss_ephemeris_house_cusps",
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 1 (Prashna Lagna Nirūpaṇa); Prashna Mārga Ch. 1",
        "is_primary": False,
        "tradition": "tajika",
    },
    {
        "method_id": "kp_249",
        "method_name": "KP Number (1–249) Prashna Lagna",
        "method_name_sa": "KP Prashna Aṅka",
        "derivation_rule": (
            "The querent selects a number between 1 and 249. Each number maps to a "
            "specific sublord within the KP sub-lord table (divided across 12 × 9 × sub = 249 "
            "subdivisions of the zodiac). The cusp whose sublord is thus identified becomes the "
            "Prashna Lagna for KP judgment."
        ),
        "derivation_rule_jsonb": {
            "input": "querent_chosen_number_1_to_249",
            "output": "kp_sublord_and_corresponding_cusp_lagna",
            "table": "KP_249_sublord_table",
        },
        "classical_citation": (
            "Krishnamurti Paddhati — Prashna system; "
            "K.S. Krishnamurti, 'Krishnamurti Padhdhati' Vol. 2, Ch. on Prashna (Horary)"
        ),
        "is_primary": True,
        "tradition": "kp",
    },
    {
        "method_id": "aarudha_based",
        "method_name": "Āruḍha-based Prashna Lagna",
        "method_name_sa": "Āruḍha Prashna Lagna",
        "derivation_rule": (
            "The Prashna Lagna is derived from the Āruḍha of the question: the seat or "
            "position the querent occupies when asking, and the direction they face. "
            "The direction indicates a zodiac sign which becomes the Prashna Lagna. "
            "East = Aries/Leo/Sagittarius; North = Cancer/Scorpio/Pisces; "
            "West = Libra/Aquarius/Gemini; South = Capricorn/Taurus/Virgo."
        ),
        "derivation_rule_jsonb": {
            "input": "querent_direction_faced + querent_seat_position",
            "output": "prashna_lagna_sign",
            "direction_map": {
                "east": ["Aries", "Leo", "Sagittarius"],
                "north": ["Cancer", "Scorpio", "Pisces"],
                "west": ["Libra", "Aquarius", "Gemini"],
                "south": ["Capricorn", "Taurus", "Virgo"],
            },
        },
        "classical_citation": "Prashna Mārga, Ch. 1 (Āruḍha Prashna Lagna Vichāra)",
        "is_primary": False,
        "tradition": "prashna_marga",
    },
    {
        "method_id": "chandra_lagna",
        "method_name": "Chandra (Moon) Lagna as Prashna Lagna",
        "method_name_sa": "Chandra Prashna Lagna",
        "derivation_rule": (
            "The natal Moon sign of the querent is used as the Prashna Lagna. "
            "The Moon, as the significator of mind (manas) and the question arising from it, "
            "gives a chart rooted in the querent's mental state. "
            "Houses are counted from the natal Moon sign."
        ),
        "derivation_rule_jsonb": {
            "input": "querent_natal_moon_sign",
            "output": "prashna_lagna_sign_equals_natal_moon_sign",
        },
        "classical_citation": "Bṛhat Prashna tradition; Prashna Mārga Ch. 2 (Chandra Bala adhyāya)",
        "is_primary": False,
        "tradition": "parashari",
    },
    {
        "method_id": "swara_based",
        "method_name": "Swara-based Prashna Lagna",
        "method_name_sa": "Swara Prashna Lagna",
        "derivation_rule": (
            "The Prashna Lagna is determined by the querent's active nostril (Swara) at the "
            "moment of asking. Right nostril active (Surya Swara / Pingala) → odd signs "
            "(Aries, Gemini, Leo, Libra, Sagittarius, Aquarius); "
            "Left nostril active (Chandra Swara / Ida) → even signs "
            "(Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces). "
            "The specific sign within the group is determined by the time of day and Tithi."
        ),
        "derivation_rule_jsonb": {
            "input": "active_nostril + time_of_day + tithi",
            "output": "prashna_lagna_sign",
            "surya_swara_signs": ["Aries", "Gemini", "Leo", "Libra", "Sagittarius", "Aquarius"],
            "chandra_swara_signs": ["Taurus", "Cancer", "Virgo", "Scorpio", "Capricorn", "Pisces"],
        },
        "classical_citation": "Swara Śāstra (Śiva Swarodaya); Prashna Mārga Ch. 4 (Swara adhyāya)",
        "is_primary": False,
        "tradition": "swara",
    },
]

# ---------------------------------------------------------------------------
# §2 — Tajik horary yogas
# ---------------------------------------------------------------------------

TAJIK_YOGAS: list[dict[str, Any]] = [
    {
        "yoga_id": "ithasala",
        "yoga_name": "Ithasala",
        "yoga_name_sa": "Ithashāla",
        "judgment_meaning": "yes_will_happen",
        "formation_rule": (
            "An applying aspect exists between the lord of the 1st house (querent significator) "
            "and the lord of the house of the matter (quesited significator): the faster-moving "
            "planet is behind the slower and closing the gap. Both planets must be within their "
            "mutual orbs (half the sum of their individual orbs). "
            "This is the single strongest positive indicator in Tajika horary."
        ),
        "formation_rule_jsonb": {
            "condition": "applying_aspect",
            "planets": ["lord_1st", "lord_matter_house"],
            "faster_planet": "closing_gap_to_slower",
            "aspect_types": ["conjunction", "trine", "sextile", "square", "opposition"],
            "orb_check": "within_mutual_orb",
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Ithashāla adhyāya); Prashna Mārga Ch. 6",
        "is_fructification_indicator": True,
    },
    {
        "yoga_id": "eesarpha",
        "yoga_name": "Eesarpha (Isarpha)",
        "yoga_name_sa": "Īsharpha",
        "judgment_meaning": "no_matter_is_past_or_declined",
        "formation_rule": (
            "A separating aspect: the faster planet has already passed the exact aspect degree "
            "with the slower planet and is now moving away. The matter asked about has already "
            "been decided, has passed, or the opportunity has slipped."
        ),
        "formation_rule_jsonb": {
            "condition": "separating_aspect",
            "planets": ["lord_1st", "lord_matter_house"],
            "faster_planet": "moving_away_from_slower",
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Ithashāla adhyāya, Eesarpha section)",
        "is_fructification_indicator": False,
    },
    {
        "yoga_id": "nakta",
        "yoga_name": "Nakta",
        "yoga_name_sa": "Nakta",
        "judgment_meaning": "yes_via_intermediary_or_delay",
        "formation_rule": (
            "No direct applying aspect exists between the two significators, but a third planet "
            "receives an applying aspect from one significator and itself applies to the other, "
            "thus acting as a mediator (nakta = one who goes between). "
            "The matter will fructify through an intermediary person or event."
        ),
        "formation_rule_jsonb": {
            "condition": "mediated_aspect",
            "mediator_planet": "receives_aspect_from_sig1_and_applies_to_sig2",
            "result": "indirect_fructification",
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Nakta adhyāya)",
        "is_fructification_indicator": True,
    },
    {
        "yoga_id": "yamaya",
        "yoga_name": "Yamaya",
        "yoga_name_sa": "Yamaya",
        "judgment_meaning": "yes_but_mutual_dependency_or_exchange",
        "formation_rule": (
            "Both significators are in mutual exchange of signs (parivartana yoga): "
            "each planet occupies the sign owned by the other. "
            "This indicates the matter will occur but with mutual dependency, "
            "compromise, or an exchange between the querent and the quesited party."
        ),
        "formation_rule_jsonb": {
            "condition": "mutual_sign_exchange",
            "planet_A": "in_sign_owned_by_planet_B",
            "planet_B": "in_sign_owned_by_planet_A",
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Yamaya adhyāya)",
        "is_fructification_indicator": True,
    },
    {
        "yoga_id": "manaau",
        "yoga_name": "Manaau",
        "yoga_name_sa": "Manau",
        "judgment_meaning": "uncertain_obstacles",
        "formation_rule": (
            "The two significators are in square aspect (90°) — a tense, conflicted relationship "
            "that is neither cleanly applying nor separating. "
            "The matter is uncertain, fraught with obstacles, and the outcome is not clearly "
            "positive or negative."
        ),
        "formation_rule_jsonb": {
            "condition": "square_aspect_90_degrees",
            "planets": ["lord_1st", "lord_matter_house"],
            "aspect_degree": 90,
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4",
        "is_fructification_indicator": False,
    },
    {
        "yoga_id": "kambula",
        "yoga_name": "Kambula",
        "yoga_name_sa": "Kambūla",
        "judgment_meaning": "favorable_timing_indicated",
        "formation_rule": (
            "The Moon applies to either the querent significator (lord of 1st) or the quesited "
            "significator (lord of the matter house) within orb. "
            "The Moon's application brings timeliness and the matter moves toward resolution. "
            "Considered highly favorable in Tajika."
        ),
        "formation_rule_jsonb": {
            "condition": "moon_applying_to_significator",
            "moon_applies_to": "lord_1st_or_lord_matter_house",
            "within_orb": True,
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Kambūla adhyāya)",
        "is_fructification_indicator": True,
    },
    {
        "yoga_id": "gairi_kambula",
        "yoga_name": "Gairi Kambula",
        "yoga_name_sa": "Gairi Kambūla",
        "judgment_meaning": "matter_already_decided_or_declined",
        "formation_rule": (
            "The Moon has already separated from the significator — the Moon's aspect is past. "
            "This is the inverse of Kambula: the Moon's helpful timing has already been spent. "
            "The matter has already been set in motion or has already passed its opportunity."
        ),
        "formation_rule_jsonb": {
            "condition": "moon_separating_from_significator",
            "moon_has_passed": "lord_1st_or_lord_matter_house",
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Kambūla adhyāya, Gairi section)",
        "is_fructification_indicator": False,
    },
    {
        "yoga_id": "dutthottha",
        "yoga_name": "Dutthottha",
        "yoga_name_sa": "Duttoththa",
        "judgment_meaning": "difficulty_obstruction",
        "formation_rule": (
            "The querent or quesited significator is placed in the 8th house from the sign it "
            "owns (its own sign). Being in the 8th from own house is a position of weakness, "
            "indicating obstruction, difficulty, or a hidden impediment to the matter."
        ),
        "formation_rule_jsonb": {
            "condition": "significator_in_8th_from_own_sign",
            "house_count": 8,
            "counted_from": "planet_own_sign",
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Duttoththa adhyāya)",
        "is_fructification_indicator": False,
    },
    {
        "yoga_id": "rudda",
        "yoga_name": "Rudda",
        "yoga_name_sa": "Rudda",
        "judgment_meaning": "blocked_prevented",
        "formation_rule": (
            "A malefic planet (Saturn, Mars, Rahu, Ketu in affliction) is interposed between "
            "the two significators in longitude, blocking the applying aspect from completing "
            "before the faster planet reaches the exact aspect. "
            "The matter is actively blocked or prevented by an external agent or obstacle."
        ),
        "formation_rule_jsonb": {
            "condition": "malefic_interposed_between_significators",
            "malefic_planets": ["Saturn", "Mars", "Rahu", "Ketu"],
            "interposition": "between_faster_and_slower_significator_in_longitude",
            "effect": "applying_aspect_blocked",
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Rudda adhyāya = prevention)",
        "is_fructification_indicator": False,
    },
    {
        "yoga_id": "khallasara",
        "yoga_name": "Khallasara",
        "yoga_name_sa": "Khallāsara",
        "judgment_meaning": "delayed_fulfillment_via_transfer",
        "formation_rule": (
            "The faster significator transfers its light to an intermediate planet "
            "(by forming an applying aspect to it), and that intermediate planet then "
            "completes the connection to the slower significator. "
            "A chain of light transfer: A → B → C. The matter will fructify but with a "
            "delay and through an intermediate transfer of agency."
        ),
        "formation_rule_jsonb": {
            "condition": "light_transfer_chain",
            "chain": ["faster_significator", "intermediate_planet", "slower_significator"],
            "mechanism": "applying_aspects_in_sequence",
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Khallāsara adhyāya)",
        "is_fructification_indicator": True,
    },
    {
        "yoga_id": "duhphali_kuttha",
        "yoga_name": "Duhphali Kuttha",
        "yoga_name_sa": "Duḥphalī Kuṭṭha",
        "judgment_meaning": "opposition_or_conflict_in_the_matter",
        "formation_rule": (
            "The two significators are in opposition (180°) — a direct confrontation between "
            "the querent's interest and the quesited matter or party. "
            "The opposition indicates open conflict, opposition from others, or the matter "
            "being pulled in two opposing directions simultaneously."
        ),
        "formation_rule_jsonb": {
            "condition": "opposition_aspect_180_degrees",
            "planets": ["lord_1st", "lord_matter_house"],
            "aspect_degree": 180,
        },
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 4 (Duḥphalī Kuṭṭha adhyāya)",
        "is_fructification_indicator": False,
    },
]

# ---------------------------------------------------------------------------
# §3 — Significator map
# ---------------------------------------------------------------------------

SIGNIFICATORS: list[dict[str, Any]] = [
    {
        "question_class": "marriage",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 7,
        "quesited_planet": "Venus, Jupiter",
        "significator_rule": (
            "For marriage questions: querent is lord of 1st + Moon (significator of mind); "
            "quesited is lord of 7th house (spouse) + Venus (natural karaka of marriage) + "
            "Jupiter (natural karaka of husband for female querents). "
            "Ithasala between lord-1 and lord-7 or Venus is the primary positive indicator."
        ),
        "classical_citation": "Prashna Mārga, Ch. 14 (Vivāha Prashna)",
    },
    {
        "question_class": "career",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 10,
        "quesited_planet": "Saturn, Sun",
        "significator_rule": (
            "For career/profession questions: quesited is lord of 10th house (karma/action) + "
            "Saturn (natural karaka of profession and service) + Sun (authority and government). "
            "2nd (income) and 11th (gains) lords are supporting significators."
        ),
        "classical_citation": "Prashna Mārga, Ch. 19 (Karma Prashna)",
    },
    {
        "question_class": "litigation_legal",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 6,
        "quesited_planet": "Mars",
        "significator_rule": (
            "For litigation/legal dispute questions: quesited is lord of 6th house (enemies, "
            "disputes, litigation) + Mars (natural karaka of conflict and litigation). "
            "The 8th lord (obstacles, hidden matters) and 12th lord (loss) are adversarial "
            "indicators. If lord-1 overcomes lord-6, the querent prevails."
        ),
        "classical_citation": "Prashna Mārga, Ch. 17 (Śatru Prashna)",
    },
    {
        "question_class": "lost_object",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 2,
        "quesited_planet": None,
        "significator_rule": (
            "For lost object questions: 2nd house = movable objects (money, jewelry); "
            "4th house = fixed or hidden objects (buried, in a building); "
            "lord of 2nd or 4th depending on object type. "
            "The sign of the 4th house/lord indicates the direction and color of the hiding place. "
            "Ithasala of lord-1 and lord-2/4 indicates recovery."
        ),
        "classical_citation": "Prashna Mārga, Ch. 20 (Nashṭa Dravya Prashna)",
    },
    {
        "question_class": "health_illness",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 6,
        "quesited_planet": "Moon, Saturn",
        "significator_rule": (
            "For health/illness questions: 1st house = the querent's body and constitution; "
            "6th house = disease and illness (quesited for recovery); "
            "8th house lord = chronic illness, longevity, and critical conditions; "
            "Moon = mind and body fluid; Saturn = chronic disease karaka. "
            "If lord-1 and Moon are strong and unafflicted, recovery is indicated."
        ),
        "classical_citation": "Prashna Mārga, Ch. 13 (Ārogya Prashna)",
    },
    {
        "question_class": "finance_wealth",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 2,
        "quesited_planet": "Jupiter",
        "significator_rule": (
            "For finance/wealth questions: 2nd house = accumulated wealth and movable assets; "
            "11th house = gains, income, fulfillment of desires; "
            "Jupiter = natural karaka of wealth. "
            "Ithasala between lord-1 and lord-2 or Jupiter indicates financial gain. "
            "Lord-12 (loss) afflicting lord-2 or Jupiter indicates financial loss."
        ),
        "classical_citation": "Prashna Mārga, Ch. 15 (Dhana Prashna)",
    },
    {
        "question_class": "travel_journey",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 9,
        "quesited_planet": "Mercury",
        "significator_rule": (
            "For travel/journey questions: 9th house = long journeys, pilgrimage; "
            "12th house = foreign travel, journeys overseas; "
            "Mercury = natural karaka of short journeys and communication; "
            "Saturn = journeys by sea or long arduous travel. "
            "Lords of 9th and 12th are the primary quesited significators."
        ),
        "classical_citation": "Prashna Mārga, Ch. 21 (Yātrā Prashna)",
    },
    {
        "question_class": "property_land",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 4,
        "quesited_planet": "Mars, Moon",
        "significator_rule": (
            "For property/land questions: 4th house = immovable property, land, home; "
            "Mars = natural karaka of land and real estate; "
            "Moon = natural karaka of home and dwelling. "
            "Ithasala between lord-1 and lord-4 or Mars indicates acquisition of property."
        ),
        "classical_citation": "Prashna Mārga, Ch. 16 (Bhūmi Prashna)",
    },
    {
        "question_class": "children_progeny",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 5,
        "quesited_planet": "Jupiter, Moon",
        "significator_rule": (
            "For children/progeny questions: 5th house = children, conception, intelligence; "
            "Jupiter = natural karaka of children and wisdom; "
            "Moon = natural karaka for mother and nurturing. "
            "Ithasala between lord-1 and lord-5 or Jupiter indicates fulfillment of progeny desire."
        ),
        "classical_citation": "Prashna Mārga, Ch. 18 (Santāna Prashna)",
    },
    {
        "question_class": "death_longevity",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 8,
        "quesited_planet": "Saturn",
        "significator_rule": (
            "For death/longevity questions: 8th house = death, longevity, major transformation; "
            "Saturn = natural karaka of death, disease, and old age. "
            "Lord-8 afflicted by malefics and lord-1 weak = concern for life. "
            "The 8th house sign and lord indicate the nature and timing of critical events."
        ),
        "classical_citation": "Prashna Mārga, Ch. 22 (Āyu Prashna)",
    },
    {
        "question_class": "spiritual_religious",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 9,
        "quesited_planet": "Jupiter",
        "significator_rule": (
            "For spiritual/religious questions: 9th house = dharma, guru, religion, pilgrimage; "
            "Jupiter = natural karaka of wisdom, guru, and spiritual knowledge. "
            "Lord-5 (past-life merit, mantra) and lord-12 (liberation, moksha) are supporting "
            "significators for deep spiritual questions."
        ),
        "classical_citation": "Prashna Mārga, Ch. 23 (Dharma Prashna)",
    },
    {
        "question_class": "enemy_conflict",
        "querent_house": 1,
        "querent_planet": "Moon",
        "quesited_house": 6,
        "quesited_planet": "Mars, Sun",
        "significator_rule": (
            "For enemy/conflict questions: 6th house = enemies, opponents, and those who "
            "obstruct; Mars = natural karaka of aggression and conflict; "
            "Sun = authority and dominance. "
            "Lord-1 stronger than lord-6 indicates victory over the enemy. "
            "Malefics in 6th (for querent) = active enemies; malefics in 12th = hidden foes."
        ),
        "classical_citation": "Prashna Mārga, Ch. 17 (Śatru Prashna)",
    },
]

# ---------------------------------------------------------------------------
# §4 — Fructification timing rules
# ---------------------------------------------------------------------------

FRUCTIFICATION_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "degree_to_hours",
        "time_unit": "hours",
        "degree_conversion_rule": (
            "1 degree of orb remaining in the applying aspect = 1 hour of time. "
            "Used for questions about immediate or same-day events. "
            "Applicable when the question concerns something happening within hours."
        ),
        "applicable_when": (
            "Movable sign rising (Aries, Cancer, Libra, Capricorn) AND the quesited planet "
            "is fast-moving (Moon, Mercury, Venus). Question concerns immediate near-term outcome."
        ),
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya — fructification timing)",
    },
    {
        "rule_id": "degree_to_days",
        "time_unit": "days",
        "degree_conversion_rule": (
            "1 degree of orb remaining in the applying aspect = 1 day. "
            "The standard short-term conversion rule. "
            "The number of degrees to the exact aspect gives the number of days to fructification."
        ),
        "applicable_when": (
            "Dual/mutable sign rising (Gemini, Virgo, Sagittarius, Pisces) OR the question "
            "concerns short-to-medium term outcomes (days to a few weeks). "
            "Default timing rule for most ordinary horary questions."
        ),
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya); Prashna Mārga Ch. 7",
    },
    {
        "rule_id": "sign_to_months",
        "time_unit": "months",
        "degree_conversion_rule": (
            "Each complete zodiac sign traversed by the slower significator from its current "
            "position to the aspect point = 1 month. "
            "Alternatively: 1 degree of orb = 1 month for slower matters."
        ),
        "applicable_when": (
            "Fixed sign rising (Taurus, Leo, Scorpio, Aquarius) AND the quesited planet is "
            "a medium-speed planet (Sun, Mars). "
            "Or when the question involves medium-term outcomes (weeks to months), "
            "such as career changes or health recovery."
        ),
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya)",
    },
    {
        "rule_id": "sign_to_years",
        "time_unit": "years",
        "degree_conversion_rule": (
            "Each zodiac sign traversed by the significator = 1 year. "
            "Used for long-range questions where Saturn or Jupiter is the quesited significator. "
            "1 degree = 1 year for very slow matters."
        ),
        "applicable_when": (
            "Fixed or earth signs involved AND the quesited significator is Saturn or Jupiter "
            "(slow planets). The question concerns long-range outcomes such as longevity, "
            "long-term property, or multi-year career trajectories."
        ),
        "classical_citation": "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya)",
    },
    {
        "rule_id": "sign_quality_timing_matrix",
        "time_unit": "days",
        "degree_conversion_rule": (
            "Sign quality determines the time scale: "
            "Movable (Chara) signs = short time (hours to days); "
            "Fixed (Sthira) signs = long time (months to years); "
            "Dual (Dvisvabhava) signs = medium time (weeks to months). "
            "The quality of both the rising sign and the sign occupied by the significator "
            "are considered; the shorter of the two prevails."
        ),
        "applicable_when": (
            "General timing rule applicable to all horary questions as a cross-check. "
            "Movable Lagna = outcome in days; Fixed Lagna = outcome in months/years; "
            "Dual Lagna = weeks. This matrix is applied first, then refined by degree count."
        ),
        "classical_citation": (
            "Tājika Nīlakaṇṭhī, Ch. 5 (Phala adhyāya); Prashna Mārga Ch. 7 (Kāla Nirṇaya)"
        ),
    },
]

# ---------------------------------------------------------------------------
# §5 — Special techniques
# ---------------------------------------------------------------------------

SPECIAL_TECHNIQUES: list[dict[str, Any]] = [
    {
        "technique_id": "nashta_jataka",
        "technique_name": "Nashta Jataka (Lost Horoscope Reconstruction)",
        "technique_name_sa": "Naṣṭa Jātaka",
        "application_rule": (
            "When the native's birth chart (Rashi + Lagna) is unknown, the Prashna chart "
            "cast for the moment of asking is used as a proxy birth chart. "
            "The Prashna Lagna becomes the proxy birth Lagna; the planetary positions at "
            "the moment of the question are read as the natal positions. "
            "The technique allows astrological judgment even without the birth time."
        ),
        "classical_citation": "Prashna Mārga, Ch. 28 (Naṣṭa Jātaka adhyāya)",
    },
    {
        "technique_id": "tithi_nakshatra_yoga",
        "technique_name": "Tithi-Nakshatra-Yoga at Question Moment",
        "technique_name_sa": "Tithi Nakṣatra Yoga Vicāra",
        "application_rule": (
            "The Panchanga elements at the moment of the question carry inherent significance "
            "for the outcome: "
            "Tithi (lunar day) indicates the emotional/motivational quality of the matter; "
            "Nakshatra (Moon's asterism at question time) indicates the nature of outcome — "
            "Nakshatra of the Moon at question time classified as benefic/malefic/mixed per "
            "traditional Tajika Nakshatra table; "
            "Yoga (Sun+Moon degree sum combination) indicates auspiciousness of the timing. "
            "All three are checked before passing judgment on the Prashna chart."
        ),
        "classical_citation": "Prashna Mārga, Ch. 3 (Pañcāṅga Vicāra in Prashna)",
    },
    {
        "technique_id": "omen_nimitta",
        "technique_name": "Omen Reading (Nimitta)",
        "technique_name_sa": "Nimitta Vicāra",
        "application_rule": (
            "Observable omens at the precise moment the querent poses the question are "
            "interpreted using classical Nimitta rules where deterministic textual rules exist: "
            "Direction of animal call (bird from east = auspicious for sunrise questions; "
            "bird from north = inauspicious); "
            "Objects in the querent's visual field (iron objects = Saturn/obstacles; "
            "flowers = Venus/auspiciousness); "
            "Sounds heard at the moment of question (conch = Vishnu/auspicious; drum = war/conflict). "
            "Only rules with explicit classical textual support are applied."
        ),
        "classical_citation": "Prashna Mārga, Ch. 2 (Nimitta adhyāya); Bṛhat Saṃhitā (Nimitta sections)",
    },
]


# ---------------------------------------------------------------------------
# §6 — Seed function
# ---------------------------------------------------------------------------

def seed_prashna_rules(db_conn, *, dry_run: bool = False) -> dict[str, int]:
    """
    Seed all bg_prashna_* reference tables.

    Uses ON CONFLICT DO NOTHING (L0 idempotency standard).
    Never commits — caller owns the transaction.
    Returns counts by category and a 'total_rules' sum.
    """
    if dry_run:
        return {
            "lagna_methods": len(PRASHNA_LAGNA_METHODS),
            "tajik_yogas": len(TAJIK_YOGAS),
            "significators": len(SIGNIFICATORS),
            "fructification": len(FRUCTIFICATION_RULES),
            "special_techniques": len(SPECIAL_TECHNIQUES),
            "total_rules": (
                len(PRASHNA_LAGNA_METHODS)
                + len(TAJIK_YOGAS)
                + len(SIGNIFICATORS)
                + len(FRUCTIFICATION_RULES)
                + len(SPECIAL_TECHNIQUES)
            ),
        }

    import json

    cur = db_conn.cursor()

    # --- Lagna methods ---
    for row in PRASHNA_LAGNA_METHODS:
        cur.execute(
            """
            INSERT INTO bg_prashna_lagna_methods
                (method_id, method_name, method_name_sa, derivation_rule,
                 derivation_rule_jsonb, classical_citation, is_primary, tradition)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (method_id) DO NOTHING
            """,
            (
                row["method_id"],
                row["method_name"],
                row.get("method_name_sa"),
                row["derivation_rule"],
                json.dumps(row.get("derivation_rule_jsonb")) if row.get("derivation_rule_jsonb") else None,
                row["classical_citation"],
                row["is_primary"],
                row["tradition"],
            ),
        )

    # --- Tajik yogas ---
    for row in TAJIK_YOGAS:
        cur.execute(
            """
            INSERT INTO bg_prashna_tajik_yogas
                (yoga_id, yoga_name, yoga_name_sa, judgment_meaning, formation_rule,
                 formation_rule_jsonb, classical_citation, is_fructification_indicator)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (yoga_id) DO NOTHING
            """,
            (
                row["yoga_id"],
                row["yoga_name"],
                row.get("yoga_name_sa"),
                row["judgment_meaning"],
                row["formation_rule"],
                json.dumps(row.get("formation_rule_jsonb")) if row.get("formation_rule_jsonb") else None,
                row["classical_citation"],
                row["is_fructification_indicator"],
            ),
        )

    # --- Significators ---
    for row in SIGNIFICATORS:
        cur.execute(
            """
            INSERT INTO bg_prashna_significators
                (question_class, querent_house, querent_planet, quesited_house,
                 quesited_planet, significator_rule, classical_citation)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (question_class) DO NOTHING
            """,
            (
                row["question_class"],
                row.get("querent_house"),
                row.get("querent_planet"),
                row["quesited_house"],
                row.get("quesited_planet"),
                row["significator_rule"],
                row["classical_citation"],
            ),
        )

    # --- Fructification rules ---
    for row in FRUCTIFICATION_RULES:
        cur.execute(
            """
            INSERT INTO bg_prashna_fructification_rules
                (rule_id, time_unit, degree_conversion_rule, applicable_when, classical_citation)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (rule_id) DO NOTHING
            """,
            (
                row["rule_id"],
                row["time_unit"],
                row["degree_conversion_rule"],
                row["applicable_when"],
                row["classical_citation"],
            ),
        )

    # --- Special techniques ---
    for row in SPECIAL_TECHNIQUES:
        cur.execute(
            """
            INSERT INTO bg_prashna_special_techniques
                (technique_id, technique_name, technique_name_sa, application_rule, classical_citation)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (technique_id) DO NOTHING
            """,
            (
                row["technique_id"],
                row["technique_name"],
                row.get("technique_name_sa"),
                row["application_rule"],
                row["classical_citation"],
            ),
        )

    cur.close()

    return {
        "lagna_methods": len(PRASHNA_LAGNA_METHODS),
        "tajik_yogas": len(TAJIK_YOGAS),
        "significators": len(SIGNIFICATORS),
        "fructification": len(FRUCTIFICATION_RULES),
        "special_techniques": len(SPECIAL_TECHNIQUES),
        "total_rules": (
            len(PRASHNA_LAGNA_METHODS)
            + len(TAJIK_YOGAS)
            + len(SIGNIFICATORS)
            + len(FRUCTIFICATION_RULES)
            + len(SPECIAL_TECHNIQUES)
        ),
    }
