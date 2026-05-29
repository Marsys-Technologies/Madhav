"""
varga_formulas.py — Divisional chart (varga) formula library for MARSYS-JIS.

Defines mathematical rules for computing which sign a planet falls in for each
divisional chart (D1 through D2700). Covers all Parashari standard vargas,
supplementary vargas, and Nadi subdivisions.

Classical source: Brihat Parashara Hora Shastra (BPHS), Chapters 6–7 (Hora to
Shashtiamsa descriptions); Saptarishis Astrology supplementary texts for
higher-order vargas.

Usage:
    from pipeline.varga_formulas import (
        VARGA_FORMULAS,
        get_varga_formula,
        list_all_vargas,
        compute_navamsa_sign,
        compute_dasamsa_sign,
    )
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Master formula dictionary
# key = divisor (int D-number)
# ---------------------------------------------------------------------------

VARGA_FORMULAS: dict[int, dict] = {

    # -----------------------------------------------------------------------
    # D1 — Rasi (Natal / Lagna chart)
    # -----------------------------------------------------------------------
    1: {
        "divisor": 1,
        "name": "Rasi",
        "alias": "Lagna / Natal chart",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Identity: planet stays in its natal rasi. No subdivision required. "
            "The full 30° of each sign belongs to that sign."
        ),
        "significance": "Physical body, personality, overall life frame.",
        "classical_source": "BPHS Ch. 6 v. 1",
    },

    # -----------------------------------------------------------------------
    # D2 — Hora (wealth, resources)
    # -----------------------------------------------------------------------
    2: {
        "divisor": 2,
        "name": "Hora",
        "alias": "Drekkana-2 / Half-sign",
        "formula_type": "special",
        "assignment_rule": (
            "Each sign is divided into two 15° halves. "
            "Odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius): "
            "first half (0–15°) → Sun's Hora (Leo); second half (15–30°) → Moon's Hora (Cancer). "
            "Even signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces): "
            "first half (0–15°) → Moon's Hora (Cancer); second half (15–30°) → Sun's Hora (Leo). "
            "Result is always Cancer or Leo."
        ),
        "significance": "Wealth, financial resources, family inheritance.",
        "classical_source": "BPHS Ch. 6 v. 2–4",
    },

    # -----------------------------------------------------------------------
    # D3 — Drekkana (siblings, co-born, courage)
    # -----------------------------------------------------------------------
    3: {
        "divisor": 3,
        "name": "Drekkana",
        "alias": "Decanate",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign is divided into three 10° parts. "
            "Part 1 (0–10°) → same sign as natal (1st sign of same triplicity). "
            "Part 2 (10–20°) → 5th sign from natal (2nd sign of same triplicity). "
            "Part 3 (20–30°) → 9th sign from natal (3rd sign of same triplicity). "
            "Formula: drekkana_sign = (rasi_index + part * 4) % 12, where part ∈ {0,1,2}."
        ),
        "significance": "Siblings, co-born, courage, short journeys.",
        "classical_source": "BPHS Ch. 6 v. 5–7",
    },

    # -----------------------------------------------------------------------
    # D4 — Chaturthamsa (fortune, property)
    # -----------------------------------------------------------------------
    4: {
        "divisor": 4,
        "name": "Chaturthamsa",
        "alias": "Turiya / Padamsa",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into four 7°30' parts. "
            "Movable signs (Aries, Cancer, Libra, Capricorn): parts map to "
            "Aries → Cancer → Libra → Capricorn (cardinal quartet). "
            "Fixed signs (Taurus, Leo, Scorpio, Aquarius): "
            "Taurus → Leo → Scorpio → Aquarius. "
            "Dual signs (Gemini, Virgo, Sagittarius, Pisces): "
            "Gemini → Virgo → Sagittarius → Pisces. "
            "Formula: start = first cardinal/fixed/dual sign of that modality; "
            "chaturthamsa_sign = (start + part * 3) % 12."
        ),
        "significance": "Property, fixed assets, general fortune, mother's wealth.",
        "classical_source": "BPHS Ch. 6 v. 8–10",
    },

    # -----------------------------------------------------------------------
    # D5 — Panchamsa (progeny, past-life credits)
    # -----------------------------------------------------------------------
    5: {
        "divisor": 5,
        "name": "Panchamsa",
        "alias": "Fifth division",
        "formula_type": "special",
        "assignment_rule": (
            "Each sign divided into five 6° parts. "
            "Odd signs: parts map to Aries, Aquarius, Sagittarius, Gemini, Libra (sequence per BPHS). "
            "Even signs: parts map to Taurus, Virgo, Pisces, Capricorn, Scorpio. "
            "The exact sign sequence is text-dependent; Parashara gives a fixed list per sign parity."
        ),
        "significance": "Children, past-life merits/demerits, spiritual credits.",
        "classical_source": "BPHS Ch. 6 v. 11–13",
    },

    # -----------------------------------------------------------------------
    # D6 — Shashtamsa (health, enemies)
    # -----------------------------------------------------------------------
    6: {
        "divisor": 6,
        "name": "Shashtamsa",
        "alias": "Sixth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into six 5° parts. "
            "Odd signs: counting starts from Aries (0). "
            "Even signs: counting starts from Libra (6). "
            "Formula: shashtamsa_sign = (start + part) % 12, part ∈ {0..5}."
        ),
        "significance": "Health, enemies, debts, diseases, maternal relatives.",
        "classical_source": "BPHS Ch. 6 v. 14–16",
    },

    # -----------------------------------------------------------------------
    # D7 — Saptamsa (children, progeny potential)
    # -----------------------------------------------------------------------
    7: {
        "divisor": 7,
        "name": "Saptamsa",
        "alias": "Seventh division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into seven parts of 4°17'8.57\" each. "
            "Odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius): "
            "parts counted from Aries (sign 0). "
            "Even signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces): "
            "parts counted from Libra (sign 6). "
            "Formula: start = 0 if odd else 6; saptamsa_sign = (start + part) % 12."
        ),
        "significance": "Children, progeny, fertility, grandchildren.",
        "classical_source": "BPHS Ch. 6 v. 17–19",
    },

    # -----------------------------------------------------------------------
    # D8 — Ashtamsa (longevity, obstacles, hidden dangers)
    # -----------------------------------------------------------------------
    8: {
        "divisor": 8,
        "name": "Ashtamsa",
        "alias": "Eighth division",
        "formula_type": "special",
        "assignment_rule": (
            "Each sign divided into eight 3°45' parts. "
            "Parts cycle through Aries to Scorpio (8 signs), then restart. "
            "The starting sign depends on the natal sign's position in its own "
            "triplicity element sequence. "
            "Formula: ashtamsa_sign = (element_start[rasi_element] + part) % 12."
        ),
        "significance": "Longevity, obstacles, 8th-house matters, hidden enemies.",
        "classical_source": "BPHS Ch. 6 v. 20–22",
    },

    # -----------------------------------------------------------------------
    # D9 — Navamsa (marriage, dharma, inner strength)
    # -----------------------------------------------------------------------
    9: {
        "divisor": 9,
        "name": "Navamsa",
        "alias": "Ninth division / Dharma chart",
        "formula_type": "navamsa_cycle",
        "assignment_rule": (
            "Each sign divided into nine parts of 3°20' each (pada = 3°20'). "
            "Starting sign for each natal sign is determined by its element triplicity: "
            "Fire signs (Aries=0, Leo=4, Sag=8) → start from Aries (0). "
            "Earth signs (Taurus=1, Virgo=5, Capricorn=9) → start from Capricorn (9). "
            "Air signs (Gemini=2, Libra=6, Aquarius=10) → start from Libra (6). "
            "Water signs (Cancer=3, Scorpio=7, Pisces=11) → start from Cancer (3). "
            "Formula: pada = floor(degree_in_sign / 3.3333); "
            "navamsa_sign = (navamsa_start[rasi] + pada) % 12."
        ),
        "significance": "Marriage, spouse, dharma, inner vitality, spiritual progress, vimshottari antardasha sub-periods.",
        "classical_source": "BPHS Ch. 6 v. 23–27",
    },

    # -----------------------------------------------------------------------
    # D10 — Dasamsa (career, profession, social standing)
    # -----------------------------------------------------------------------
    10: {
        "divisor": 10,
        "name": "Dasamsa",
        "alias": "Swargamsa / Karmamsa",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into ten 3° parts. "
            "Odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius, 0-indexed even): "
            "parts counted from Aries (0). "
            "Even signs (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces, 0-indexed odd): "
            "parts counted from Capricorn (9). "
            "Formula: start = 0 if rasi_index % 2 == 0 else 9; "
            "dasamsa_sign = (start + part) % 12."
        ),
        "significance": "Career, profession, authority, social standing, karma in the world.",
        "classical_source": "BPHS Ch. 6 v. 28–30",
    },

    # -----------------------------------------------------------------------
    # D11 — Rudramsa (accidents, death-like experiences)
    # -----------------------------------------------------------------------
    11: {
        "divisor": 11,
        "name": "Rudramsa",
        "alias": "Eleventh division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into eleven 2°43'38\" parts. "
            "Odd signs: parts counted from Aries (0). "
            "Even signs: parts counted from Libra (6). "
            "Formula: start = 0 if odd else 6; rudramsa_sign = (start + part) % 12."
        ),
        "significance": "Accidents, death-like experiences, Rudra (Shiva) energy, crises.",
        "classical_source": "BPHS Ch. 6 v. 31–33",
    },

    # -----------------------------------------------------------------------
    # D12 — Dvadasamsa (parents, ancestry)
    # -----------------------------------------------------------------------
    12: {
        "divisor": 12,
        "name": "Dvadasamsa",
        "alias": "Suryamsa / Twelfth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into twelve 2°30' parts. "
            "Counting starts from the natal sign itself (self-referential). "
            "Formula: dvadasamsa_sign = (rasi_index + part) % 12, part ∈ {0..11}."
        ),
        "significance": "Parents, ancestry, lineage, paternal/maternal inheritance.",
        "classical_source": "BPHS Ch. 6 v. 34–36",
    },

    # -----------------------------------------------------------------------
    # D14 — Chaturdamsa (luck, fortune, misfortune)
    # -----------------------------------------------------------------------
    14: {
        "divisor": 14,
        "name": "Chaturdamsa",
        "alias": "Fourteenth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into fourteen 2°8'34\" parts. "
            "Odd signs: counting from Aries (0). "
            "Even signs: counting from Libra (6). "
            "Formula: start = 0 if odd else 6; chaturdamsa_sign = (start + part) % 12."
        ),
        "significance": "Luck, fortune, misfortune, general auspiciousness.",
        "classical_source": "BPHS Ch. 6 v. 37–39",
    },

    # -----------------------------------------------------------------------
    # D15 — Vimsamsa (spiritual progress, worship)  [NOTE: also called D15]
    # -----------------------------------------------------------------------
    15: {
        "divisor": 15,
        "name": "Vimsamsa",
        "alias": "Fifteenth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into fifteen 2° parts. "
            "Movable signs (Aries, Cancer, Libra, Capricorn): counting starts from Aries (0). "
            "Fixed signs (Taurus, Leo, Scorpio, Aquarius): counting starts from Sagittarius (8). "
            "Dual signs (Gemini, Virgo, Sagittarius, Pisces): counting starts from Leo (4). "
            "Formula: vimsamsa_sign = (modality_start[modality] + part) % 12."
        ),
        "significance": "Upasana (worship), spiritual progress, devotional nature.",
        "classical_source": "BPHS Ch. 6 v. 40–42",
    },

    # -----------------------------------------------------------------------
    # D16 — Shodasamsa (vehicles, comforts, movable assets)
    # -----------------------------------------------------------------------
    16: {
        "divisor": 16,
        "name": "Shodasamsa",
        "alias": "Kalamsa / Sixteenth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into sixteen parts of 1°52'30\" each. "
            "All signs: parts cycle through Aries (0) → Taurus (1) → ... sequentially. "
            "Movable signs start from Aries (0); Fixed from Leo (4); Dual from Sagittarius (8). "
            "Formula: shodasamsa_sign = (modality_start[modality] + part) % 12."
        ),
        "significance": "Vehicles, conveyances, comfort, happiness from assets.",
        "classical_source": "BPHS Ch. 6 v. 43–45",
    },

    # -----------------------------------------------------------------------
    # D20 — Vimsamsa (religious merit, piety) [second use of name; D15 is also called Vimsamsa]
    # -----------------------------------------------------------------------
    20: {
        "divisor": 20,
        "name": "Vimsamsa",
        "alias": "Twentieth division / Upagrahamsa",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into twenty 1°30' parts. "
            "Movable signs: counting from Aries (0). "
            "Fixed signs: counting from Leo (4). "
            "Dual signs: counting from Sagittarius (8). "
            "Formula: vimsamsa20_sign = (modality_start[modality] + part) % 12."
        ),
        "significance": "Religious merit, piety, mode of worship, devotional inclinations.",
        "classical_source": "BPHS Ch. 7 v. 1–3",
    },

    # -----------------------------------------------------------------------
    # D21 — Chaturvimsamsa variant (some texts)
    # -----------------------------------------------------------------------
    21: {
        "divisor": 21,
        "name": "Ekavimshamsa",
        "alias": "Twenty-first division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into twenty-one parts of 1°25'42\" each. "
            "Odd signs: counting from Aries (0). "
            "Even signs: counting from Libra (6). "
            "Formula: ekavimshamsa_sign = (start + part) % 12."
        ),
        "significance": "Vitality, strength, inherent constitution.",
        "classical_source": "BPHS Ch. 7 v. 4–6",
    },

    # -----------------------------------------------------------------------
    # D24 — Chaturvimsamsa / Siddhamsa (education, learning)
    # -----------------------------------------------------------------------
    24: {
        "divisor": 24,
        "name": "Chaturvimsamsa",
        "alias": "Siddhamsa / Twenty-fourth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into twenty-four parts of 1°15' each. "
            "Odd signs: counting starts from Leo (4). "
            "Even signs: counting starts from Cancer (3). "
            "Formula: siddhamsa_sign = (start + part) % 12, "
            "where start = 4 for odd rasi, 3 for even rasi."
        ),
        "significance": "Education, learning, academic achievement, wisdom.",
        "classical_source": "BPHS Ch. 7 v. 7–9",
    },

    # -----------------------------------------------------------------------
    # D27 — Nakshatramsa / Bhamsa (physical strength, vitality)
    # -----------------------------------------------------------------------
    27: {
        "divisor": 27,
        "name": "Nakshatramsa",
        "alias": "Bhamsa / Twenty-seventh division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into twenty-seven parts of 1°6'40\" each (27 nakshatras). "
            "Fiery signs (Aries, Leo, Sagittarius): counting from Aries (0). "
            "Earthy signs (Taurus, Virgo, Capricorn): counting from Cancer (3). "
            "Airy signs (Gemini, Libra, Aquarius): counting from Libra (6). "
            "Watery signs (Cancer, Scorpio, Pisces): counting from Capricorn (9). "
            "Formula: bhamsa_sign = (element_start[element] + part) % 12."
        ),
        "significance": "Physical strength, innate vitality, constitutional health.",
        "classical_source": "BPHS Ch. 7 v. 10–12",
    },

    # -----------------------------------------------------------------------
    # D30 — Trimsamsa (evils, diseases, miseries)
    # -----------------------------------------------------------------------
    30: {
        "divisor": 30,
        "name": "Trimsamsa",
        "alias": "Thirtieth division",
        "formula_type": "special",
        "assignment_rule": (
            "Each sign divided into UNEQUAL parts assigned to five planets. "
            "Odd signs (Aries, Gemini, etc.): "
            "Mars 0–5° (Aries), Saturn 5–10° (Aquarius), Jupiter 10–18° (Sagittarius), "
            "Mercury 18–25° (Gemini), Venus 25–30° (Libra). "
            "Even signs (Taurus, Cancer, etc.): "
            "Venus 0–5° (Taurus), Mercury 5–12° (Virgo), Jupiter 12–20° (Pisces), "
            "Saturn 20–25° (Capricorn), Mars 25–30° (Scorpio). "
            "Sun and Moon have no trimsamsa. "
            "The sign assigned = the moolatrikona / exaltation sign of the ruling planet."
        ),
        "significance": "Miseries, evils, health afflictions, inauspicious results, past karma debts.",
        "classical_source": "BPHS Ch. 7 v. 13–17",
    },

    # -----------------------------------------------------------------------
    # D32 — Khavedamsa variant
    # -----------------------------------------------------------------------
    32: {
        "divisor": 32,
        "name": "Dvatrinshamsa",
        "alias": "Thirty-second division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into thirty-two parts of 0°56'15\" each. "
            "Odd signs: counting from Aries (0). "
            "Even signs: counting from Leo (4). "
            "Formula: dvatrinshamsa_sign = (start + part) % 12."
        ),
        "significance": "Auspiciousness, inherent good/evil nature of situations.",
        "classical_source": "BPHS Ch. 7 v. 18–20",
    },

    # -----------------------------------------------------------------------
    # D33 — Tritrimshamsa (miscellaneous classifications)
    # -----------------------------------------------------------------------
    33: {
        "divisor": 33,
        "name": "Tritrimshamsa",
        "alias": "Thirty-third division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into thirty-three parts of 0°54'33\" each. "
            "Odd signs: counting from Aries (0). "
            "Even signs: counting from Libra (6). "
            "Formula: tritrimshamsa_sign = (start + part) % 12."
        ),
        "significance": "Classification of planetary strength in miscellaneous contexts.",
        "classical_source": "BPHS Ch. 7 v. 21–22",
    },

    # -----------------------------------------------------------------------
    # D36 — Khavedamsa (auspicious/inauspicious results)
    # -----------------------------------------------------------------------
    36: {
        "divisor": 36,
        "name": "Khavedamsa",
        "alias": "Thirty-sixth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into thirty-six parts of 0°50' each. "
            "Movable signs: counting from Aries (0). "
            "Fixed signs: counting from Leo (4). "
            "Dual signs: counting from Sagittarius (8). "
            "Formula: khavedamsa36_sign = (modality_start[modality] + part) % 12."
        ),
        "significance": "Auspicious/inauspicious deeds in the native's life.",
        "classical_source": "BPHS Ch. 7 v. 23–25",
    },

    # -----------------------------------------------------------------------
    # D40 — Khavedamsa / Chatvarimsamsa (maternal legacy)
    # -----------------------------------------------------------------------
    40: {
        "divisor": 40,
        "name": "Chatvarimsamsa",
        "alias": "Khavedamsa / Fortieth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into forty parts of 0°45' each. "
            "Odd signs: counting from Aries (0). "
            "Even signs: counting from Libra (6). "
            "Formula: chatvarimsamsa_sign = (start + part) % 12."
        ),
        "significance": "Auspicious/inauspicious effects from maternal lineage.",
        "classical_source": "BPHS Ch. 7 v. 26–28",
    },

    # -----------------------------------------------------------------------
    # D45 — Akshavedamsa (paternal legacy)
    # -----------------------------------------------------------------------
    45: {
        "divisor": 45,
        "name": "Akshavedamsa",
        "alias": "Forty-fifth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into forty-five parts of 0°40' each. "
            "Movable signs: counting from Aries (0). "
            "Fixed signs: counting from Leo (4). "
            "Dual signs: counting from Sagittarius (8). "
            "Formula: akshavedamsa_sign = (modality_start[modality] + part) % 12."
        ),
        "significance": "Auspicious/inauspicious effects from paternal lineage.",
        "classical_source": "BPHS Ch. 7 v. 29–31",
    },

    # -----------------------------------------------------------------------
    # D50 — Panchasat (past life, spiritual evolution)
    # -----------------------------------------------------------------------
    50: {
        "divisor": 50,
        "name": "Panchasat",
        "alias": "Fiftieth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into fifty parts of 0°36' each. "
            "Odd signs: counting from Aries (0). "
            "Even signs: counting from Libra (6). "
            "Formula: panchasat_sign = (start + part) % 12."
        ),
        "significance": "Past-life deeds, spiritual evolution, deep karmic patterns.",
        "classical_source": "BPHS Ch. 7 v. 32–34",
    },

    # -----------------------------------------------------------------------
    # D54 — Trimshadamsa (Chaturasubhamsa variant)
    # -----------------------------------------------------------------------
    54: {
        "divisor": 54,
        "name": "Chaturasubhamsa",
        "alias": "Fifty-fourth division",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into fifty-four parts of 0°33'20\" each. "
            "Movable signs: counting from Aries (0). "
            "Fixed signs: counting from Leo (4). "
            "Dual signs: counting from Sagittarius (8). "
            "Formula: chaturasubhamsa_sign = (modality_start[modality] + part) % 12."
        ),
        "significance": "Manifold auspicious/inauspicious life outcomes.",
        "classical_source": "BPHS Ch. 7 v. 35–36",
    },

    # -----------------------------------------------------------------------
    # D60 — Shashtiamsa (all past karma, general results)
    # -----------------------------------------------------------------------
    60: {
        "divisor": 60,
        "name": "Shashtiamsa",
        "alias": "Sixtieth division / Shastyamsa",
        "formula_type": "equal_division",
        "assignment_rule": (
            "Each sign divided into sixty parts of 0°30' each. "
            "60 portions cycle through all 12 signs (5 per sign). "
            "Odd signs: counting from Aries (0). "
            "Even signs: counting from Libra (6). "
            "Formula: shashtiamsa_sign = (start + part) % 12. "
            "Each of the 60 parts has a named quality (Ghora, Rakshasa, Deva, etc.) "
            "per BPHS shashtiamsa-quality table."
        ),
        "significance": "All past karma, most comprehensive judgment, overall life quality.",
        "classical_source": "BPHS Ch. 7 v. 37–50",
    },

    # -----------------------------------------------------------------------
    # NADI VARGAS (higher-order subdivisions used in Nadi Jyotish)
    # -----------------------------------------------------------------------

    # D108 — Ashtottaramsa (Nadi subdivision)
    108: {
        "divisor": 108,
        "name": "Ashtottaramsa",
        "alias": "D108 / 108-division Nadi chart",
        "formula_type": "nadi",
        "assignment_rule": (
            "Each sign divided into 108 parts of 0°16'40\" each. "
            "Corresponds to 108 nakshatras × padas combined scheme. "
            "Formula: part = floor(degree_in_sign / (30/108)); "
            "nadi_sign = (rasi_index * 9 + part) % 12. "
            "In Nadi tradition, 12 signs × 9 navamsas × 1 level = 108 subdivisions."
        ),
        "significance": "Nadi-level karmic imprints, very precise life events, soul memory.",
        "classical_source": "Nadi Grantha tradition; Saptarishi Nadi texts",
    },

    # D150 — Rishi-level Nadi
    150: {
        "divisor": 150,
        "name": "Navamsa-Panchamsa",
        "alias": "D150 / Rishi Nadi division",
        "formula_type": "nadi",
        "assignment_rule": (
            "Each sign divided into 150 parts of 0°12' each. "
            "Compound of D9 × D5 sub-subdivision. "
            "Formula: part = floor(degree_in_sign / 0.2); "
            "nadi_sign = (navamsa_sign * 5 + panchamsa_offset) % 12. "
            "Used exclusively in Rishi Nadi readings for sub-event timing."
        ),
        "significance": "Rishi-level Nadi readings, sub-event timing, precise karmic moments.",
        "classical_source": "Agastya Nadi; Bhrigu Nadi supplementary texts",
    },

    # D2700 — Sub-Rishi Nadi (extremely fine subdivision)
    2700: {
        "divisor": 2700,
        "name": "Trilinga-Nadi",
        "alias": "D2700 / Sub-Rishi Nadi",
        "formula_type": "nadi",
        "assignment_rule": (
            "Each sign divided into 2700 parts of 0°0'40\" each. "
            "Product of D108 × D25 or D9 × D300 compound scheme. "
            "This is the finest subdivision used in classical Nadi tradition. "
            "Formula: part = floor(degree_in_sign / (30/2700)); "
            "nadi_sign = part % 12. "
            "Practical precision requires exact birth time to the second."
        ),
        "significance": "Sub-Rishi Nadi: atomic-level karma imprints, birth-second precision events.",
        "classical_source": "Agastya Nadi sub-commentary; Nadi Jyotish oral tradition",
    },
}


# ---------------------------------------------------------------------------
# Public API functions
# ---------------------------------------------------------------------------

def get_varga_formula(divisor: int) -> dict:
    """
    Return the formula dict for the given divisor (D-number).

    Args:
        divisor: The D-number (e.g., 9 for Navamsa, 10 for Dasamsa).

    Returns:
        dict with keys: divisor, name, alias, formula_type, assignment_rule,
        significance, classical_source.

    Raises:
        KeyError: if the divisor is not in VARGA_FORMULAS.
    """
    return VARGA_FORMULAS[divisor]


def list_all_vargas() -> list[int]:
    """
    Return a sorted list of all supported divisors.

    Returns:
        Sorted list of ints, e.g. [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ...]
    """
    return sorted(VARGA_FORMULAS.keys())


def compute_navamsa_sign(rasi_sign_index: int, degree_in_sign: float) -> int:
    """
    Compute the D9 navamsa sign (0-indexed from Aries) for a planet.

    Each natal sign is divided into 9 parts of 3°20' (= 30/9 degrees).
    The starting navamsa sign depends on the element of the natal sign:
      - Fire (Aries=0, Leo=4, Sag=8)    → start from Aries (0)
      - Earth (Taurus=1, Virgo=5, Cap=9) → start from Capricorn (9)
      - Air (Gemini=2, Libra=6, Aqu=10)  → start from Libra (6)
      - Water (Cancer=3, Sco=7, Pis=11)  → start from Cancer (3)

    Args:
        rasi_sign_index: 0-indexed natal sign (0=Aries, 1=Taurus, ..., 11=Pisces).
        degree_in_sign: Degrees within the natal sign (0.0 – 29.999...).

    Returns:
        0-indexed navamsa sign (0=Aries, ..., 11=Pisces).

    Examples:
        >>> compute_navamsa_sign(0, 0.0)   # Aries 0° → Aries navamsa
        0
        >>> compute_navamsa_sign(0, 3.5)   # Aries 3°30' → 2nd pada → Taurus navamsa
        1
        >>> compute_navamsa_sign(1, 0.0)   # Taurus 0° → Capricorn navamsa (earth start)
        9
    """
    # Starting navamsa sign indexed by natal sign index
    navamsa_start = {
        0: 0,   # Aries   → fire → Aries
        4: 0,   # Leo     → fire → Aries
        8: 0,   # Sag     → fire → Aries
        1: 9,   # Taurus  → earth → Capricorn
        5: 9,   # Virgo   → earth → Capricorn
        9: 9,   # Cap     → earth → Capricorn
        2: 6,   # Gemini  → air  → Libra
        6: 6,   # Libra   → air  → Libra
        10: 6,  # Aquarius→ air  → Libra
        3: 3,   # Cancer  → water → Cancer
        7: 3,   # Scorpio → water → Cancer
        11: 3,  # Pisces  → water → Cancer
    }
    part_size = 30.0 / 9  # 3.3333...°
    pada = int(degree_in_sign / part_size)  # 0–8
    # Clamp to 0–8 in case of floating point edge (e.g. exactly 30.0)
    pada = min(pada, 8)
    return (navamsa_start[rasi_sign_index] + pada) % 12


def compute_dasamsa_sign(rasi_sign_index: int, degree_in_sign: float) -> int:
    """
    Compute the D10 dasamsa sign (0-indexed from Aries) for a planet.

    Each natal sign is divided into 10 parts of 3° each.
    - Odd signs (0-indexed: Aries=0, Gemini=2, Leo=4, Libra=6, Sag=8, Aqu=10):
      counting starts from Aries (0).
    - Even signs (0-indexed: Taurus=1, Cancer=3, Virgo=5, Scorpio=7, Cap=9, Pis=11):
      counting starts from Capricorn (9).

    Note: "odd" here means rasi_sign_index % 2 == 0 (Aries is index 0, which
    is even numerically but the first/odd sign in the zodiac sequence).
    The classical rule is: signs 1,3,5,7,9,11 (Aries, Gemini, ...) start from
    Aries; signs 2,4,6,8,10,12 (Taurus, Cancer, ...) start from Capricorn.
    In 0-indexed terms: rasi_index 0,2,4,6,8,10 → Aries start;
    rasi_index 1,3,5,7,9,11 → Capricorn start.

    Args:
        rasi_sign_index: 0-indexed natal sign (0=Aries, ..., 11=Pisces).
        degree_in_sign: Degrees within the natal sign (0.0 – 29.999...).

    Returns:
        0-indexed dasamsa sign (0=Aries, ..., 11=Pisces).

    Examples:
        >>> compute_dasamsa_sign(0, 0.0)   # Aries 0° → Aries (odd sign, part 0)
        0
        >>> compute_dasamsa_sign(1, 0.0)   # Taurus 0° → Capricorn (even sign, part 0)
        9
        >>> compute_dasamsa_sign(0, 15.0)  # Aries 15° → part 5 → Gemini (0+5=5)
        5
    """
    part = int(degree_in_sign / 3.0)  # 0–9
    part = min(part, 9)  # clamp edge case
    # 0-indexed even = classical "odd" sign (Aries, Gemini, Leo, Libra, Sag, Aqu)
    start = 0 if rasi_sign_index % 2 == 0 else 9
    return (start + part) % 12


def compute_drekkana_sign(rasi_sign_index: int, degree_in_sign: float) -> int:
    """
    Compute the D3 drekkana sign (0-indexed from Aries) for a planet.

    Each natal sign is divided into 3 parts of 10° each.
    Part 0 (0–10°)  → same sign (1st of its triplicity).
    Part 1 (10–20°) → 5th sign from natal (2nd of its triplicity).
    Part 2 (20–30°) → 9th sign from natal (3rd of its triplicity).
    Formula: drekkana_sign = (rasi_index + part * 4) % 12.

    Args:
        rasi_sign_index: 0-indexed natal sign.
        degree_in_sign: Degrees within the natal sign.

    Returns:
        0-indexed drekkana sign.
    """
    part = int(degree_in_sign / 10.0)  # 0–2
    part = min(part, 2)
    return (rasi_sign_index + part * 4) % 12


def compute_dvadasamsa_sign(rasi_sign_index: int, degree_in_sign: float) -> int:
    """
    Compute the D12 dvadasamsa sign (0-indexed from Aries) for a planet.

    Each natal sign is divided into 12 parts of 2°30' each.
    Counting starts from the natal sign itself.
    Formula: dvadasamsa_sign = (rasi_index + part) % 12.

    Args:
        rasi_sign_index: 0-indexed natal sign.
        degree_in_sign: Degrees within the natal sign.

    Returns:
        0-indexed dvadasamsa sign.
    """
    part = int(degree_in_sign / 2.5)  # 0–11
    part = min(part, 11)
    return (rasi_sign_index + part) % 12
