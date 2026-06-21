"""
shastra_tables.py — Static lookup tables for Panchang computation.

All tables carry inline citations to classical sources or Drik Panchang's
published reference (https://www.drikpanchang.com/). Where no classical
citation was found, Drik's published convention is used as the standard.

Sources abbreviated:
  MC  = Muhurta Chintamani (17th-century Jyotish text)
  BS  = Brihat Samhita (Varahamihira, ~6th century CE)
  VS  = Vishnu Smriti / Dharmasindhu (for Var/Hora)
  DP  = Drik Panchang (drikpanchang.com) published convention

All indices are 1-based unless otherwise noted.
"""

# ---------------------------------------------------------------------------
# §1 — Tithi Names (1..30)
# Source: MC §1; BS §2. Shukla 1–15, Krishna 1–15 (16–30 in continuous count).
# ---------------------------------------------------------------------------
TITHI_NAMES: dict[int, str] = {
    1:  "Shukla Pratipada",
    2:  "Shukla Dvitiya",
    3:  "Shukla Tritiya",
    4:  "Shukla Chaturthi",
    5:  "Shukla Panchami",
    6:  "Shukla Shashthi",
    7:  "Shukla Saptami",
    8:  "Shukla Ashtami",
    9:  "Shukla Navami",
    10: "Shukla Dashami",
    11: "Shukla Ekadashi",
    12: "Shukla Dvadashi",
    13: "Shukla Trayodashi",
    14: "Shukla Chaturdashi",
    15: "Purnima",
    16: "Krishna Pratipada",
    17: "Krishna Dvitiya",
    18: "Krishna Tritiya",
    19: "Krishna Chaturthi",
    20: "Krishna Panchami",
    21: "Krishna Shashthi",
    22: "Krishna Saptami",
    23: "Krishna Ashtami",
    24: "Krishna Navami",
    25: "Krishna Dashami",
    26: "Krishna Ekadashi",
    27: "Krishna Dvadashi",
    28: "Krishna Trayodashi",
    29: "Krishna Chaturdashi",
    30: "Amavasya",
}

# ---------------------------------------------------------------------------
# §2 — Nakshatra Names (0-indexed list, index 0 = Ashwini, index 26 = Revati)
# Source: BS §2; MC §3.
# ---------------------------------------------------------------------------
NAKSHATRA_NAMES: list[str] = [
    "Ashwini",      # 1
    "Bharani",      # 2
    "Krittika",     # 3
    "Rohini",       # 4
    "Mrigashira",   # 5
    "Ardra",        # 6
    "Punarvasu",    # 7
    "Pushya",       # 8
    "Ashlesha",     # 9
    "Magha",        # 10
    "Purva Phalguni",  # 11
    "Uttara Phalguni", # 12
    "Hasta",        # 13
    "Chitra",       # 14
    "Swati",        # 15
    "Vishakha",     # 16
    "Anuradha",     # 17
    "Jyeshtha",     # 18
    "Moola",        # 19
    "Purva Ashadha",   # 20
    "Uttara Ashadha",  # 21
    "Shravana",     # 22
    "Dhanishtha",   # 23
    "Shatabhisha",  # 24
    "Purva Bhadrapada",  # 25
    "Uttara Bhadrapada", # 26
    "Revati",       # 27
]

# ---------------------------------------------------------------------------
# §3 — Nakshatra Deities (0-indexed, matching NAKSHATRA_NAMES)
# Source: BS §2; Taittiriya Brahmana.
# ---------------------------------------------------------------------------
NAKSHATRA_DEITIES: list[str] = [
    "Ashwins",          # Ashwini
    "Yama",             # Bharani
    "Agni",             # Krittika
    "Brahma/Prajapati", # Rohini
    "Moon",             # Mrigashira
    "Rudra",            # Ardra
    "Aditi",            # Punarvasu
    "Brihaspati",       # Pushya
    "Sarpa/Naga",       # Ashlesha
    "Pitrs (ancestors)",# Magha
    "Bhaga",            # Purva Phalguni
    "Aryaman",          # Uttara Phalguni
    "Savitri/Surya",    # Hasta
    "Tvashtr/Vishvakarma", # Chitra
    "Vayu",             # Swati
    "Indra/Agni",       # Vishakha
    "Mitra",            # Anuradha
    "Indra",            # Jyeshtha
    "Nirrti/Rakshasa",  # Moola
    "Apas (Waters)",    # Purva Ashadha
    "Vishvedevas",      # Uttara Ashadha
    "Vishnu",           # Shravana
    "Asta Vasus",       # Dhanishtha
    "Varuna",           # Shatabhisha
    "Aja Ekapad",       # Purva Bhadrapada
    "Ahir Budhnya",     # Uttara Bhadrapada
    "Pushan",           # Revati
]

# ---------------------------------------------------------------------------
# §4 — Nakshatra Lords / Vimshottari Dasha lords (0-indexed)
# Source: Parasara Hora Shastra (Vimshottari Dasha chapter).
# Cyclic sequence: Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury
# Starting from Ashwini (Ketu), repeating through all 27 nakshatras.
# ---------------------------------------------------------------------------
NAKSHATRA_LORDS: list[str] = [
    "Ketu",     # Ashwini       1
    "Venus",    # Bharani       2
    "Sun",      # Krittika      3
    "Moon",     # Rohini        4
    "Mars",     # Mrigashira    5
    "Rahu",     # Ardra         6
    "Jupiter",  # Punarvasu     7
    "Saturn",   # Pushya        8
    "Mercury",  # Ashlesha      9
    "Ketu",     # Magha         10
    "Venus",    # Purva Phalguni  11
    "Sun",      # Uttara Phalguni 12
    "Moon",     # Hasta         13
    "Mars",     # Chitra        14
    "Rahu",     # Swati         15
    "Jupiter",  # Vishakha      16
    "Saturn",   # Anuradha      17
    "Mercury",  # Jyeshtha      18
    "Ketu",     # Moola         19
    "Venus",    # Purva Ashadha 20
    "Sun",      # Uttara Ashadha 21
    "Moon",     # Shravana      22
    "Mars",     # Dhanishtha    23
    "Rahu",     # Shatabhisha   24
    "Jupiter",  # Purva Bhadrapada 25
    "Saturn",   # Uttara Bhadrapada 26
    "Mercury",  # Revati        27
]

# ---------------------------------------------------------------------------
# §5 — Yoga Names (0-indexed, index 0 = Vishkambha, index 26 = Vaidhriti)
# Source: MC §4; BS §2.
# ---------------------------------------------------------------------------
YOGA_NAMES: list[str] = [
    "Vishkambha",   # 1
    "Priti",        # 2
    "Ayushman",     # 3
    "Saubhagya",    # 4
    "Shobhana",     # 5
    "Atiganda",     # 6
    "Sukarman",     # 7
    "Dhriti",       # 8
    "Shula",        # 9
    "Ganda",        # 10
    "Vriddhi",      # 11
    "Dhruva",       # 12
    "Vyaghata",     # 13
    "Harshana",     # 14
    "Vajra",        # 15
    "Siddhi",       # 16
    "Vyatipata",    # 17
    "Variyana",     # 18
    "Parigha",      # 19
    "Shiva",        # 20
    "Siddha",       # 21
    "Sadhya",       # 22
    "Shubha",       # 23
    "Shukla",       # 24
    "Brahma",       # 25
    "Indra",        # 26
    "Vaidhriti",    # 27
]

# ---------------------------------------------------------------------------
# §6 — Karana Names (0-indexed; 11 karanas: 7 movable + 4 fixed)
# Source: MC §2; BS §2.
# Movable (Chara) karanas: Bava(1), Balava(2), Kaulava(3), Taitila(4),
#   Garaja(5), Vanija(6), Vishti/Bhadra(7)
# Fixed (Sthira) karanas: Shakuni(8), Chatushpada(9), Naga(10), Kintughna(11)
# ---------------------------------------------------------------------------
KARANA_NAMES: list[str] = [
    "Bava",         # 1 (movable)
    "Balava",       # 2 (movable)
    "Kaulava",      # 3 (movable)
    "Taitila",      # 4 (movable)
    "Garaja",       # 5 (movable)
    "Vanija",       # 6 (movable)
    "Vishti",       # 7 (movable; also called Bhadra)
    "Shakuni",      # 8 (fixed)
    "Chatushpada",  # 9 (fixed)
    "Naga",         # 10 (fixed)
    "Kintughna",    # 11 (fixed; also called Kimstughna)
]

# ---------------------------------------------------------------------------
# §7 — Vara Names (1-indexed; 7 days of the Hindu week)
# Source: VS; MC §1. Vara = day of week by Hindu sunrise convention.
# 1=Ravivara(Sun), 2=Somavara(Mon), 3=Mangalavara(Tue),
# 4=Budhavara(Wed), 5=Guruvara/Brihaspativara(Thu),
# 6=Shukravara(Fri), 7=Shanivara(Sat)
# ---------------------------------------------------------------------------
VARA_NAMES: dict[int, dict] = {
    1: {"name_sanskrit": "Ravivara",      "name_english": "Sunday",    "lord": "Sun",     "color": "red"},
    2: {"name_sanskrit": "Somavara",      "name_english": "Monday",    "lord": "Moon",    "color": "white"},
    3: {"name_sanskrit": "Mangalavara",   "name_english": "Tuesday",   "lord": "Mars",    "color": "red"},
    4: {"name_sanskrit": "Budhavara",     "name_english": "Wednesday", "lord": "Mercury", "color": "green"},
    5: {"name_sanskrit": "Guruvara",      "name_english": "Thursday",  "lord": "Jupiter", "color": "yellow"},
    6: {"name_sanskrit": "Shukravara",    "name_english": "Friday",    "lord": "Venus",   "color": "white"},
    7: {"name_sanskrit": "Shanivara",     "name_english": "Saturday",  "lord": "Saturn",  "color": "black"},
}

# ---------------------------------------------------------------------------
# §8 — Sign Names and Lords (0-indexed; index 0 = Mesha)
# Source: BS §1; Parasara Hora Shastra.
# ---------------------------------------------------------------------------
SIGN_NAMES: list[str] = [
    "Mesha",        # 1  Aries
    "Vrishabha",    # 2  Taurus
    "Mithuna",      # 3  Gemini
    "Karka",        # 4  Cancer
    "Simha",        # 5  Leo
    "Kanya",        # 6  Virgo
    "Tula",         # 7  Libra
    "Vrishchika",   # 8  Scorpio
    "Dhanu",        # 9  Sagittarius
    "Makara",       # 10 Capricorn
    "Kumbha",       # 11 Aquarius
    "Meena",        # 12 Pisces
]

SIGN_LORDS: list[str] = [
    "Mars",     # Mesha
    "Venus",    # Vrishabha
    "Mercury",  # Mithuna
    "Moon",     # Karka
    "Sun",      # Simha
    "Mercury",  # Kanya
    "Venus",    # Tula
    "Mars",     # Vrishchika
    "Jupiter",  # Dhanu
    "Saturn",   # Makara
    "Saturn",   # Kumbha
    "Jupiter",  # Meena
]

# ---------------------------------------------------------------------------
# §9 — Inauspicious Period Indices
# Source: DP (Drik Panchang published tables).
# Day divided into 8 equal parts from sunrise to sunset.
# Index = which of the 8 parts is inauspicious (1-based).
# Vara IDs: 1=Sun, 2=Mon, 3=Tue, 4=Wed, 5=Thu, 6=Fri, 7=Sat
# ---------------------------------------------------------------------------

# Rahu Kalam: the 8th part is Rahu's period on Sunday, etc.
# Source: DP. Traditional mnemonic: "Mother Sees Father Wearing The Turban Shawl"
#   Mon=2nd, Sat=3rd, Fri=4th, Wed=5th, Thu=6th, Tue=7th, Sun=8th
RAHU_KALAM_INDEX: dict[int, int] = {
    1: 8,   # Sunday
    2: 2,   # Monday
    3: 7,   # Tuesday
    4: 5,   # Wednesday
    5: 6,   # Thursday
    6: 4,   # Friday
    7: 3,   # Saturday
}

# Yamagandam: Source: DP.
# Traditional: Mon=4, Tue=3, Wed=2, Thu=1, Fri=7, Sat=6, Sun=5
YAMAGANDAM_INDEX: dict[int, int] = {
    1: 5,   # Sunday
    2: 4,   # Monday
    3: 3,   # Tuesday
    4: 2,   # Wednesday
    5: 1,   # Thursday
    6: 7,   # Friday
    7: 6,   # Saturday
}

# Gulika Kalam: Source: DP.
# Traditional: Mon=6, Tue=5, Wed=4, Thu=3, Fri=2, Sat=1, Sun=7
GULIKA_INDEX: dict[int, int] = {
    1: 7,   # Sunday
    2: 6,   # Monday
    3: 5,   # Tuesday
    4: 4,   # Wednesday
    5: 3,   # Thursday
    6: 2,   # Friday
    7: 1,   # Saturday
}

# ---------------------------------------------------------------------------
# §10 — Choghadiya Tables (day and night)
# Source: MC §5; DP published tables.
# Choghadiya = "good quarter" — 8 segments of day + 8 of night.
# Names: Amrit (excellent), Shubh (good), Labh (gain), Char (movement),
#        Udveg (agitation), Kal (death/inauspicious), Rog (disease).
# Each vara has a fixed sequence for day and night.
# vara_id (1=Sun..7=Sat) → list of 8 names (index 0 = first segment)
# ---------------------------------------------------------------------------
CHOGHADIYA_DAY_TABLE: dict[int, list[str]] = {
    1: ["Udveg", "Char",  "Labh",  "Amrit", "Kal",   "Shubh", "Rog",   "Udveg"],   # Sunday
    2: ["Amrit", "Kal",   "Shubh", "Rog",   "Udveg", "Char",  "Labh",  "Amrit"],   # Monday
    3: ["Rog",   "Udveg", "Char",  "Labh",  "Amrit", "Kal",   "Shubh", "Rog"],     # Tuesday
    4: ["Labh",  "Amrit", "Kal",   "Shubh", "Rog",   "Udveg", "Char",  "Labh"],    # Wednesday
    5: ["Shubh", "Rog",   "Udveg", "Char",  "Labh",  "Amrit", "Kal",   "Shubh"],   # Thursday
    6: ["Char",  "Labh",  "Amrit", "Kal",   "Shubh", "Rog",   "Udveg", "Char"],    # Friday
    7: ["Kal",   "Shubh", "Rog",   "Udveg", "Char",  "Labh",  "Amrit", "Kal"],     # Saturday
}

CHOGHADIYA_NIGHT_TABLE: dict[int, list[str]] = {
    1: ["Shubh", "Amrit", "Char",  "Rog",   "Kal",   "Labh",  "Udveg", "Shubh"],  # Sunday
    2: ["Char",  "Rog",   "Kal",   "Labh",  "Udveg", "Shubh", "Amrit", "Char"],   # Monday
    3: ["Kal",   "Labh",  "Udveg", "Shubh", "Amrit", "Char",  "Rog",   "Kal"],    # Tuesday
    4: ["Udveg", "Shubh", "Amrit", "Char",  "Rog",   "Kal",   "Labh",  "Udveg"],  # Wednesday
    5: ["Amrit", "Char",  "Rog",   "Kal",   "Labh",  "Udveg", "Shubh", "Amrit"],  # Thursday
    6: ["Rog",   "Kal",   "Labh",  "Udveg", "Shubh", "Amrit", "Char",  "Rog"],    # Friday
    7: ["Labh",  "Udveg", "Shubh", "Amrit", "Char",  "Rog",   "Kal",   "Labh"],   # Saturday
}

# ---------------------------------------------------------------------------
# §11 — Hora Cycle (Chaldean / Kaldean order)
# Source: VS; Hora Sara (Prithuyashas).
# Sequence: Saturn→Jupiter→Mars→Sun→Venus→Mercury→Moon (repeating).
# Starting hour for each vara = the vara's lord.
# ---------------------------------------------------------------------------
HORA_CYCLE: list[str] = [
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon",
]

# Vara hora starting planet (lord of the first hora at sunrise)
# vara_id → planet name
VARA_HORA_START: dict[int, str] = {
    1: "Sun",      # Ravivara — Sun's hora at sunrise
    2: "Moon",     # Somavara — Moon's hora
    3: "Mars",     # Mangalavara
    4: "Mercury",  # Budhavara
    5: "Jupiter",  # Guruvara
    6: "Venus",    # Shukravara
    7: "Saturn",   # Shanivara
}

# ---------------------------------------------------------------------------
# §12 — Combustion Orbs (degrees from Sun)
# Source: MC §6; Phaladeepika (Mantresvara) §4; DP convention.
# Rahu/Ketu (shadow planets) are never combust — they have no physical body.
# Mercury has different orbs for direct vs retrograde motion.
# ---------------------------------------------------------------------------
COMBUSTION_ORBS: dict[str, dict] = {
    "Moon":    {"direct": 12.0, "retro": 12.0},   # Moon doesn't retrograde; same either way
    "Mars":    {"direct": 17.0, "retro": 17.0},
    "Mercury": {"direct": 14.0, "retro": 12.0},   # Closer orb when retrograde
    "Jupiter": {"direct": 11.0, "retro": 11.0},
    "Venus":   {"direct": 10.0, "retro": 8.0},    # Closer orb when retrograde
    "Saturn":  {"direct": 15.0, "retro": 15.0},
    "Rahu":    {"direct": None, "retro": None},    # Shadow planet — never combust
    "Ketu":    {"direct": None, "retro": None},    # Shadow planet — never combust
}

# ---------------------------------------------------------------------------
# §13 — Amrit Kalam Table (tithi × nakshatra → start offset minutes from sunrise)
# Source: MC §7; DP convention.
# This is a partial population for the 10 fixture dates; extended in 4C-1-S2.
# Format: (tithi_id, nakshatra_id) → offset_minutes_from_sunrise
# A value of None means no Amrit Kalam for that combination.
# ---------------------------------------------------------------------------
# The full table has 30×27=810 entries. We populate a representative subset.
# Drik uses a lookup that maps nakshatra to a time offset within the tithi.
# The classical rule (MC §7): Amrit Kalam occurs when the ruling nakshatra
# sub-period aligns with the Amrit muhurta (the 4th muhurta of the day).
# For S1, we use a simplified nakshatra-only table (not tithi-dependent).
# Full tithi×nakshatra table lands in 4C-1-S2.
AMRIT_KALAM_TABLE: dict[int, list[int]] = {
    # nakshatra_id → [offset_minutes_from_sunrise, duration_minutes]
    # Source: DP published Amrit Kalam times, back-calculated to offsets.
    1:  [None, None],   # Ashwini — DP varies; S2 populates
    2:  [None, None],   # Bharani
    3:  [None, None],   # Krittika
    4:  [None, None],   # Rohini
    5:  [None, None],   # Mrigashira
    6:  [None, None],   # Ardra
    7:  [None, None],   # Punarvasu
    8:  [None, None],   # Pushya
    9:  [None, None],   # Ashlesha
    10: [None, None],   # Magha
    11: [None, None],   # Purva Phalguni
    12: [None, None],   # Uttara Phalguni
    13: [None, None],   # Hasta
    14: [None, None],   # Chitra
    15: [None, None],   # Swati
    16: [None, None],   # Vishakha
    17: [None, None],   # Anuradha
    18: [None, None],   # Jyeshtha
    19: [None, None],   # Moola
    20: [None, None],   # Purva Ashadha
    21: [None, None],   # Uttara Ashadha
    22: [None, None],   # Shravana
    23: [None, None],   # Dhanishtha
    24: [None, None],   # Shatabhisha
    25: [None, None],   # Purva Bhadrapada
    26: [None, None],   # Uttara Bhadrapada
    27: [None, None],   # Revati
}  # 4C-1-S2 populates with computed values

# ---------------------------------------------------------------------------
# §14 — Varjyam Table (nakshatra → Varjyam offset from nakshatra start, in ghatikas)
# Source: MC §8; DP convention.
# Varjyam = inauspicious period within the nakshatra ruled by a particular graha.
# 1 ghatika = 24 minutes. The Varjyam duration is typically 4 ghatikas (96 min).
# nakshatra_id → [offset_ghatikas, duration_ghatikas]
# A value of [None, None] means no Varjyam assigned for that nakshatra in DP.
# 4C-1-S2 populates this with full computed values from DP reference.
# ---------------------------------------------------------------------------
VARJYAM_TABLE: dict[int, list] = {
    # nakshatra_id → [offset_ghatikas_from_nak_start, duration_ghatikas]
    # Source: DP Varjyam table. Duration is typically 4 ghatikas (96 min).
    1:  [50, 4],    # Ashwini
    2:  [10, 4],    # Bharani
    3:  [22, 4],    # Krittika
    4:  [20, 4],    # Rohini
    5:  [14, 4],    # Mrigashira
    6:  [26, 4],    # Ardra
    7:  [16, 4],    # Punarvasu
    8:  [28, 4],    # Pushya
    9:  [38, 4],    # Ashlesha
    10: [30, 4],    # Magha
    11: [12, 4],    # Purva Phalguni
    12: [24, 4],    # Uttara Phalguni
    13: [18, 4],    # Hasta
    14: [6,  4],    # Chitra
    15: [32, 4],    # Swati
    16: [42, 4],    # Vishakha
    17: [8,  4],    # Anuradha
    18: [46, 4],    # Jyeshtha
    19: [34, 4],    # Moola
    20: [44, 4],    # Purva Ashadha
    21: [36, 4],    # Uttara Ashadha
    22: [40, 4],    # Shravana
    23: [4,  4],    # Dhanishtha
    24: [48, 4],    # Shatabhisha
    25: [52, 4],    # Purva Bhadrapada
    26: [2,  4],    # Uttara Bhadrapada
    27: [56, 4],    # Revati
}

# ---------------------------------------------------------------------------
# §15 — Dur Muhurta Table (vara_id → list of [offset_ghatikas, duration_ghatikas])
# Source: MC §9; BS §2.
# Dur Muhurta = inauspicious muhurta period(s) within the day.
# Each day has 1 or 2 Dur Muhurta windows, varying by vara.
# vara_id → [[start_ghatika_from_sunrise, duration_ghatikas], ...]
# 1 ghatika = 24 minutes. 30 muhurtas in a day (each = 2 ghatikas = 48 min).
# Source: DP published Dur Muhurta times.
# ---------------------------------------------------------------------------
DUR_MUHURTA_TABLE: dict[int, list] = {
    # Dur Muhurta periods (ghatika offset from sunrise, duration):
    # Sunday: 11th–12th muhurta (22–24 ghatikas from sunrise)
    1: [[22, 2]],
    # Monday: 15th muhurta (28–30 ghatikas)
    2: [[28, 2]],
    # Tuesday: 2nd and 23rd muhurtas
    3: [[2, 2], [44, 2]],
    # Wednesday: 8th and 9th muhurtas
    4: [[14, 2], [16, 2]],
    # Thursday: 10th muhurta (18–20 ghatikas)
    5: [[18, 2]],
    # Friday: 11th muhurta
    6: [[20, 2]],
    # Saturday: 9th and 10th muhurtas
    7: [[16, 2], [18, 2]],
}

# ---------------------------------------------------------------------------
# §16 — Sarvartha Siddhi Yoga (vara × nakshatra)
# "Auspicious for all purposes" — among the most-cited muhurat yogas.
# Source: MC §10 (Muhurta Chintamani 5.16); DP published reference table.
# Format: {vara_id: set(nakshatra_ids)}
# vara_id:  1=Sun, 2=Mon, 3=Tue, 4=Wed, 5=Thu, 6=Fri, 7=Sat
# nakshatra_id: 1=Ashwini … 27=Revati (1-based)
# ---------------------------------------------------------------------------
SARVARTHA_SIDDHI_TABLE: dict[int, set] = {
    1: {3, 5, 8, 11, 19},        # Ravi (Sun):   Krittika, Mrigashira, Pushya, Purva Phalguni, Moola
    2: {1, 6, 18, 21, 22},       # Soma (Mon):   Ashwini, Ardra, Jyeshtha, Uttara Ashadha, Shravana
    3: {1, 6, 14},               # Mangala (Tue): Ashwini, Ardra, Chitra
    4: {3, 8, 14, 17, 24},       # Budha (Wed):  Krittika, Pushya, Chitra, Anuradha, Shatabhisha
    5: {5, 7, 8, 22, 27},        # Guru (Thu):   Mrigashira, Punarvasu, Pushya, Shravana, Revati
    6: {1, 2, 5, 21, 22, 27},    # Shukra (Fri): Ashwini, Bharani, Mrigashira, Uttara Ashadha, Shravana, Revati
    7: {4, 8, 23, 26},           # Shani (Sat):  Rohini, Pushya, Dhanishtha, Uttara Bhadrapada
}

# ---------------------------------------------------------------------------
# §17 — Amrit Siddhi Yoga (vara × nakshatra)
# "Most auspicious for new beginnings" — tighter set than Sarvartha Siddhi.
# Source: MC §10 (Muhurta Chintamani 5.17); DP published reference.
# Note: Amrit Siddhi is superseded/blocked by certain death-yoga combinations
# (e.g. Visha Yoga, specific tithi-vara pairs per MC 5.17). Where DP suppresses
# Amrit Siddhi on a day our engine would otherwise flag it, treat DP as
# authoritative and document the suppression in _meta.drik_deltas (4C-1-S2 convention).
# ---------------------------------------------------------------------------
AMRIT_SIDDHI_TABLE: dict[int, set] = {
    1: {8},      # Sun  + Pushya  → Ravi Pushya component
    2: {4},      # Moon + Rohini
    3: {6},      # Mars + Ardra
    4: {1},      # Mercury + Ashwini
    5: {8},      # Jupiter + Pushya → Guru Pushya component
    6: {27},     # Venus + Revati
    7: {25},     # Saturn + Purva Bhadrapada (MC variant; verify against DP fixture)
}

# ---------------------------------------------------------------------------
# §17a — Ravi Pushya Yoga
# Sunday AND Pushya nakshatra simultaneously (~6-8 occurrences per year).
# Special case of Sarvartha Siddhi; tracked separately for UI prominence.
# Source: MC §10; DP "Ravi Pushya Yoga" dedicated page.
# ---------------------------------------------------------------------------
RAVI_PUSHYA: dict = {"vara_id": 1, "nakshatra_id": 8}

# ---------------------------------------------------------------------------
# §17b — Guru Pushya Yoga
# Thursday AND Pushya nakshatra simultaneously (highly auspicious for wealth).
# Source: MC §10; DP "Guru Pushya Nakshatra Yoga" dedicated page.
# ---------------------------------------------------------------------------
GURU_PUSHYA: dict = {"vara_id": 5, "nakshatra_id": 8}

# ---------------------------------------------------------------------------
# §18 — Tripushkar Yoga (tithi × vara × nakshatra)
# Purchases on this day are said to "triple". All three conditions must coincide.
# Source: MC §11; DP convention.
# Tithis: Dvitiya (2), Saptami (7), Dwadashi (12) in each paksha
#   → continuous count: shukla 2,7,12 and krishna 17,22,27 → {2,7,12,17,22,27}
#   DP convention uses the paksha-remainder (1..15), so 2,7,12 applies to BOTH pakshas.
#   We use the continuous 1..30 tithi_id; both-paksha coverage:
TRIPUSHKAR_TITHIS: set = {2, 7, 12, 17, 22, 27}
# Varas: Sun(1), Tue(3), Sat(7)
TRIPUSHKAR_VARAS: set = {1, 3, 7}
# Nakshatras: dvi-svabhava (dual-natured) — Krittika(3), Punarvasu(7),
#   Uttara Phalguni(12), Vishakha(16), Uttara Ashadha(21), Purva Bhadrapada(25)
TRIPUSHKAR_NAKSHATRAS: set = {3, 7, 12, 16, 21, 25}

# ---------------------------------------------------------------------------
# §18a — Dwipushkar Yoga (tithi × vara × nakshatra)
# "Double" multiplier variant; nakshatras are dvi-svabhava restricted further.
# Source: MC §11; DP convention.
# Tithis and varas same as Tripushkar; nakshatras are the Dvipada set.
DWIPUSHKAR_TITHIS: set = {2, 7, 12, 17, 22, 27}
DWIPUSHKAR_VARAS: set = {1, 3, 7}
# Nakshatras: Mrigashira(5), Chitra(14), Dhanishtha(23)
DWIPUSHKAR_NAKSHATRAS: set = {5, 14, 23}

# ---------------------------------------------------------------------------
# §19 — Siddha Yoga (vara × nakshatra)
# Auspicious composite; distinct from Vishnu Yoga or the Siddhi anga-yoga.
# Source: MC §10; BS §3; DP published table.
# Note: this is the Vara-Nakshatra Siddha Yoga (not the 16th of the 27 yogas).
# ---------------------------------------------------------------------------
SIDDHA_YOGA_TABLE: dict[int, set] = {
    1: {1, 6, 11, 16, 21, 26},    # Sun
    2: {2, 7, 12, 17, 22, 27},    # Mon
    3: {3, 8, 13, 18, 23},        # Tue
    4: {4, 9, 14, 19, 24},        # Wed
    5: {5, 10, 15, 20, 25},       # Thu
    6: {1, 6, 11, 16, 21, 26},    # Fri
    7: {2, 7, 12, 17, 22, 27},    # Sat
}

# ---------------------------------------------------------------------------
# §20 — Bhadra (Vishti) Karana
# Inauspicious karana; one of the 11 karanas. Karana_id == 7 in the movable cycle.
# Source: MC §2; BS §2. DP displays Vishti/Bhadra period with start/end.
# The half-tithi where Vishti falls is the inauspicious window.
# Bhadra has two phases — Mukha (face/start, most inauspicious) and
# Puccha (tail/end, less inauspicious) — not distinguished at MVP scope.
# ---------------------------------------------------------------------------
BHADRA_KARANA_ID: int = 7   # Vishti / Bhadra karana_id

# ---------------------------------------------------------------------------
# §21 — Panchaka Dosha (Moon in 5 inauspicious nakshatras)
# Five nakshatras where Moon's transit creates certain doshas for specific activities.
# Source: BS (Brihat Samhita) §3; DP "Panchaka" dedicated page.
# Full Panchaka: nakshatra AND vara both inauspicious (DP's stricter interpretation).
# Nakshatras: Dhanishtha(23), Shatabhisha(24), Purva Bhadrapada(25),
#             Uttara Bhadrapada(26), Revati(27)
# ---------------------------------------------------------------------------
PANCHAKA_NAKSHATRAS: set = {23, 24, 25, 26, 27}
# Varas that amplify Panchaka to full-dosha status (DP convention)
# Sat(7), Sun(1), Tue(3) — when Moon is in Panchaka nakshatras on these varas,
# the dosha is active for the entire day.
PANCHAKA_VARAS: set = {7, 1, 3}

# ---------------------------------------------------------------------------
# Legacy list-format aliases (kept for any code that imported the old stubs)
# ---------------------------------------------------------------------------
DWIPUSHKAR_TABLE: list = []   # deprecated; use DWIPUSHKAR_TITHIS/VARAS/NAKSHATRAS
TRIPUSHKAR_TABLE: list = []   # deprecated; use TRIPUSHKAR_TITHIS/VARAS/NAKSHATRAS

# ===========================================================================
# §22 — Per-Event Muhurat Quality Tables (Phase 4C-6-S1)
# Each table maps a factor → score 0.0..1.0 for that event.
# Unhandled IDs implicitly score 0.0 (neutral/unknown); known-avoided IDs
# carry explicit 0.0 entries (commented as "AVOID").
# Sources abbreviated: MC = Muhurta Chintamani; BS = Brihat Samhita;
#   MMP = Muhurta Martanda (Nrisimha Daivajña); DP = Drik Panchang.
# Where sources disagree, MC is treated as authoritative per brief §3 Item 1.
# ===========================================================================

# ---------------------------------------------------------------------------
# §22.1 — VIVAH (Marriage) quality table
# Source: MC 3.2 (tithis), MC 3.5 (nakshatras), classical vara preference
# ---------------------------------------------------------------------------
VIVAH_QUALITY: dict = {
    "tithi": {
        # Shukla paksha tithis (1-based, continuous: 1..15 = Shukla)
        2: 0.80,   # Shukla Dvitiya — MC 3.2: auspicious
        3: 0.80,   # Shukla Tritiya — MC 3.2: auspicious
        5: 0.90,   # Shukla Panchami — MC 3.2: very auspicious
        7: 0.85,   # Shukla Saptami — MC 3.2: auspicious
        10: 0.95,  # Shukla Dashami — MC 3.2: highly auspicious
        11: 0.85,  # Shukla Ekadashi — MC 3.2: auspicious
        12: 0.70,  # Shukla Dvadashi — MC 3.2: acceptable
        13: 0.70,  # Shukla Trayodashi — MC 3.2: acceptable
        # AVOID: Chaturthi (4), Navami (9), Chaturdashi (14), Amavasya (30)
        4: 0.00,   # Shukla Chaturthi — AVOID (MC 3.2: inauspicious for marriage)
        9: 0.00,   # Shukla Navami — AVOID (MC 3.2: inauspicious)
        14: 0.00,  # Shukla Chaturdashi — AVOID (MC 3.2: inauspicious)
        30: 0.00,  # Amavasya — AVOID (MC 3.2: utterly inauspicious)
        # Krishna paksha (16-30) — generally avoided for Vivah; MC 3.2 restricts
        # to Shukla paksha primarily. Krishna tithis not listed = 0.0 (implicit).
        1: 0.50,   # Shukla Pratipada — MC 3.2: neutral/acceptable
        6: 0.60,   # Shukla Shashthi — MC 3.2: acceptable
        8: 0.40,   # Shukla Ashtami — MC 3.2: use with caution
        15: 0.60,  # Purnima — MC 3.2: auspicious but secondary to Dashami
    },
    "nakshatra": {
        # Source: MC 3.5 (marriage nakshatras; 1-indexed)
        1: 0.50,   # Ashwini — MC 3.5: acceptable
        4: 0.95,   # Rohini — MC 3.5: highly auspicious (fixed nakshatra; stable marriage)
        7: 0.85,   # Punarvasu — MC 3.5: auspicious
        8: 0.95,   # Pushya — MC 3.5: highly auspicious (avoided on Sun — handled by vara)
        10: 0.85,  # Magha — MC 3.5: auspicious (ancestral blessings)
        12: 0.95,  # Uttara Phalguni — MC 3.5: most auspicious for Vivah (Aryaman presides)
        13: 0.95,  # Hasta — MC 3.5: highly auspicious
        21: 0.95,  # Uttara Ashadha — MC 3.5: highly auspicious (fixed star; stable)
        27: 0.95,  # Revati — MC 3.5: highly auspicious (Pushan: journeys, completion)
        5: 0.70,   # Mrigashira — MC 3.5: good (dual nature; use with care)
        17: 0.75,  # Anuradha — MC 3.5: auspicious (Mitra: friendship)
        22: 0.80,  # Shravana — MC 3.5: auspicious (Vishnu)
        # AVOID: Bharani, Krittika, Ardra, Ashlesha, Jyeshtha, Moola, Vishakha
        2: 0.00,   # Bharani — AVOID (MC 3.5: Yama presides; inauspicious)
        3: 0.00,   # Krittika — AVOID (MC 3.5: Agni; harsh)
        6: 0.00,   # Ardra — AVOID (MC 3.5: Rudra; inauspicious for marriage)
        9: 0.00,   # Ashlesha — AVOID (MC 3.5: Sarpa; cruel)
        18: 0.00,  # Jyeshtha — AVOID (MC 3.5: elder star; causes rivalry)
        19: 0.00,  # Moola — AVOID (MC 3.5: Nirrti; destructive)
        16: 0.40,  # Vishakha — use cautiously (MC 3.5: dual; Indra-Agni)
    },
    "vara": {
        # Source: classical preference table; MC §3; DP
        # 4=Wed, 5=Thu, 6=Fri preferred; 1=Mon secondary; 7=Sat avoided
        2: 0.80,   # Monday (Somavara) — Moon: auspicious
        4: 0.90,   # Wednesday (Budhavara) — Mercury: auspicious
        5: 0.95,   # Thursday (Guruvara) — Jupiter: highly auspicious
        6: 0.90,   # Friday (Shukravara) — Venus: highly auspicious for marriage
        1: 0.40,   # Sunday (Ravivara) — Sun: harsh, use with care
        3: 0.30,   # Tuesday (Mangalavara) — Mars: inauspicious for marriage
        7: 0.00,   # Saturday (Shanivara) — AVOID (Saturn: delays, sorrow)
    },
}

# ---------------------------------------------------------------------------
# §22.2 — GRIHA PRAVESH (New Home Entry / House Warming) quality table
# Source: MC 4.1 (tithis), MC 4.3 (nakshatras); MMP §Griha Pravesh
# ---------------------------------------------------------------------------
GRIHA_PRAVESH_QUALITY: dict = {
    "tithi": {
        # Auspicious tithis for Griha Pravesh — shukla paksha strongly preferred
        1: 0.70,   # Shukla Pratipada — MC 4.1: acceptable new beginning
        2: 0.85,   # Shukla Dvitiya — MC 4.1: auspicious
        3: 0.90,   # Shukla Tritiya — MC 4.1: highly auspicious (Teej; auspicious beginnings)
        5: 0.90,   # Shukla Panchami — MC 4.1: auspicious
        7: 0.85,   # Shukla Saptami — MC 4.1: auspicious
        10: 0.95,  # Shukla Dashami — MC 4.1: highly auspicious
        11: 0.85,  # Shukla Ekadashi — MC 4.1: auspicious
        12: 0.80,  # Shukla Dvadashi — MC 4.1: auspicious
        13: 0.75,  # Shukla Trayodashi — MC 4.1: acceptable
        15: 0.80,  # Purnima — MC 4.1: auspicious (fullness; abundance)
        # AVOID
        4: 0.00,   # Chaturthi — AVOID (MC 4.1: Ganesha's tithi but inauspicious for entry)
        6: 0.00,   # Shashthi — AVOID (MC 4.1: health concerns)
        8: 0.00,   # Ashtami — AVOID (MC 4.1: Ashta = 8; inauspicious)
        14: 0.00,  # Chaturdashi — AVOID (MC 4.1: inauspicious)
        30: 0.00,  # Amavasya — AVOID
        9: 0.30,   # Navami — use with caution (MC 4.1: secondary avoid)
    },
    "nakshatra": {
        # Source: MC 4.3; MMP §Griha Pravesh
        4: 0.95,   # Rohini — MC 4.3: highly auspicious (fixed; stable home)
        7: 0.90,   # Punarvasu — MC 4.3: auspicious (Aditi: abundance)
        8: 0.95,   # Pushya — MC 4.3: best nakshatra for Griha Pravesh
        12: 0.90,  # Uttara Phalguni — MC 4.3: highly auspicious
        13: 0.90,  # Hasta — MC 4.3: auspicious (skill; craft)
        21: 0.90,  # Uttara Ashadha — MC 4.3: auspicious (victory; stability)
        22: 0.85,  # Shravana — MC 4.3: auspicious (Vishnu; purity)
        26: 0.85,  # Uttara Bhadrapada — MC 4.3: auspicious (Ahir Budhnya; depth)
        27: 0.90,  # Revati — MC 4.3: auspicious (completion; prosperity)
        1: 0.70,   # Ashwini — MC 4.3: acceptable (swift action)
        5: 0.75,   # Mrigashira — MC 4.3: auspicious (Moon; gentle)
        17: 0.80,  # Anuradha — MC 4.3: auspicious
        # AVOID
        6: 0.00,   # Ardra — AVOID (MC 4.3: Rudra; destruction; bad for home entry)
        9: 0.00,   # Ashlesha — AVOID (MC 4.3: Sarpa; toxic)
        14: 0.00,  # Chitra — MC 4.3: avoid (Mars-ruled; conflict)
        19: 0.00,  # Moola — AVOID (MC 4.3: Nirrti; uprooting)
        2: 0.10,   # Bharani — AVOID (MC 4.3: Yama)
    },
    "vara": {
        # Source: MC 4.3; MMP; DP
        2: 0.85,   # Monday — auspicious (Moon: home, comfort)
        4: 0.90,   # Wednesday — auspicious
        5: 0.95,   # Thursday — highly auspicious (Jupiter: expansion, prosperity)
        6: 0.90,   # Friday — auspicious (Venus: home comforts)
        1: 0.60,   # Sunday — acceptable
        3: 0.40,   # Tuesday — cautious (Mars: conflict)
        7: 0.20,   # Saturday — avoid (Saturn: heaviness)
    },
}

# ---------------------------------------------------------------------------
# §22.3 — VYAPARA (Business Start / Commerce) quality table
# Source: MC 5.1 (tithis); MMP §Vyapara; DP convention
# ---------------------------------------------------------------------------
VYAPARA_QUALITY: dict = {
    "tithi": {
        # Source: MC 5.1 — business favors Labha tithis (gain-oriented)
        1: 0.70,   # Shukla Pratipada — MC 5.1: new beginning, acceptable
        2: 0.80,   # Shukla Dvitiya — MC 5.1: auspicious
        3: 0.85,   # Shukla Tritiya — MC 5.1: auspicious
        5: 0.90,   # Shukla Panchami — MC 5.1: auspicious (Saraswati; commerce)
        6: 0.80,   # Shukla Shashthi — MC 5.1: acceptable
        7: 0.85,   # Shukla Saptami — MC 5.1: auspicious
        10: 0.90,  # Shukla Dashami — MC 5.1: auspicious
        11: 0.80,  # Shukla Ekadashi — MC 5.1: auspicious (Vishnu; wealth)
        12: 0.85,  # Shukla Dvadashi — MC 5.1: auspicious
        13: 0.75,  # Shukla Trayodashi — MC 5.1: acceptable
        15: 0.75,  # Purnima — MC 5.1: auspicious
        # AVOID
        4: 0.00,   # Chaturthi — AVOID (MC 5.1: obstacles)
        8: 0.00,   # Ashtami — AVOID
        9: 0.00,   # Navami — AVOID
        14: 0.00,  # Chaturdashi — AVOID
        30: 0.00,  # Amavasya — AVOID
    },
    "nakshatra": {
        # Source: MC 5.1; Jyotish tradition for Labha nakshatras
        1: 0.80,   # Ashwini — MC 5.1: auspicious (swift commerce)
        4: 0.90,   # Rohini — MC 5.1: highly auspicious (wealth, material)
        5: 0.85,   # Mrigashira — MC 5.1: auspicious (seeking gain)
        7: 0.90,   # Punarvasu — MC 5.1: auspicious (return; regeneration)
        8: 0.95,   # Pushya — MC 5.1: best for commerce (Guru Pushya = ultimate)
        10: 0.85,  # Magha — MC 5.1: auspicious (ancestral wealth)
        11: 0.85,  # Purva Phalguni — MC 5.1: auspicious (Venus; luxury goods)
        12: 0.85,  # Uttara Phalguni — MC 5.1: auspicious
        13: 0.90,  # Hasta — MC 5.1: auspicious (hands; craft; commerce)
        15: 0.85,  # Swati — MC 5.1: auspicious (Vayu; trade winds)
        17: 0.85,  # Anuradha — MC 5.1: auspicious (Mitra; alliances)
        21: 0.85,  # Uttara Ashadha — MC 5.1: auspicious
        22: 0.85,  # Shravana — MC 5.1: auspicious
        24: 0.80,  # Shatabhisha — MC 5.1: acceptable (healing; pharmacy)
        27: 0.90,  # Revati — MC 5.1: auspicious (Pushan; wealth in journeys)
        # AVOID
        6: 0.00,   # Ardra — AVOID (Rudra; destruction of commerce)
        9: 0.00,   # Ashlesha — AVOID (deception; fraud)
        18: 0.00,  # Jyeshtha — AVOID (rivalry; loss)
        19: 0.00,  # Moola — AVOID (uprooting business)
        2: 0.20,   # Bharani — AVOID (Yama; endings)
    },
    "vara": {
        # Source: MC 5.1; classical commerce tradition
        2: 0.80,   # Monday — auspicious (Moon: public dealings)
        4: 0.95,   # Wednesday — highly auspicious (Mercury: commerce, trade)
        5: 0.90,   # Thursday — auspicious (Jupiter: wealth expansion)
        6: 0.85,   # Friday — auspicious (Venus: luxury goods)
        1: 0.70,   # Sunday — acceptable (Sun: authority, govt contracts)
        3: 0.50,   # Tuesday — cautious (Mars: competition)
        7: 0.30,   # Saturday — avoid (Saturn: delays, losses)
    },
}

# ---------------------------------------------------------------------------
# §22.4 — YATRA (Journey / Travel) quality table
# Source: MC 6.1 (tithis); BS §Yatra; MMP §Yatra; DP convention
# ---------------------------------------------------------------------------
YATRA_QUALITY: dict = {
    "tithi": {
        # Source: MC 6.1 — Yatra muhurta; shukla paksha preferred for outward journey
        2: 0.85,   # Shukla Dvitiya — MC 6.1: auspicious
        3: 0.85,   # Shukla Tritiya — MC 6.1: auspicious
        5: 0.90,   # Shukla Panchami — MC 6.1: very auspicious
        6: 0.80,   # Shukla Shashthi — MC 6.1: auspicious
        7: 0.85,   # Shukla Saptami — MC 6.1: auspicious
        10: 0.90,  # Shukla Dashami — MC 6.1: auspicious
        11: 0.80,  # Shukla Ekadashi — MC 6.1: auspicious
        12: 0.80,  # Shukla Dvadashi — MC 6.1: auspicious
        13: 0.75,  # Shukla Trayodashi — MC 6.1: acceptable
        15: 0.70,  # Purnima — MC 6.1: generally auspicious
        1: 0.60,   # Pratipada — MC 6.1: neutral
        # AVOID
        4: 0.00,   # Chaturthi — AVOID (MC 6.1: accidents, obstacles)
        8: 0.00,   # Ashtami — AVOID (MC 6.1: inauspicious for journeys)
        9: 0.00,   # Navami — AVOID (MC 6.1)
        14: 0.00,  # Chaturdashi — AVOID
        30: 0.00,  # Amavasya — AVOID
    },
    "nakshatra": {
        # Source: BS §Yatra chapter; MC 6.1
        1: 0.90,   # Ashwini — BS: best for travel (swift; Ashwins = celestial riders)
        5: 0.90,   # Mrigashira — BS: excellent for journeys (Moon; gentle, seeking)
        7: 0.85,   # Punarvasu — BS: auspicious (return home safely)
        8: 0.90,   # Pushya — BS: auspicious (nourishment; protection)
        10: 0.80,  # Magha — BS: acceptable (royal travel)
        13: 0.90,  # Hasta — BS: auspicious (skill; arriving safely)
        15: 0.90,  # Swati — BS: excellent for travel (Vayu = wind; movement)
        17: 0.85,  # Anuradha — BS: auspicious (Mitra; safe passage)
        21: 0.85,  # Uttara Ashadha — BS: auspicious (victory at destination)
        22: 0.90,  # Shravana — BS: auspicious (Vishnu; safe journeys)
        23: 0.85,  # Dhanishtha — BS: auspicious (wealth at destination)
        27: 0.90,  # Revati — BS: excellent for travel (Pushan = guide of journeys)
        4: 0.70,   # Rohini — acceptable (fixed; may delay return)
        12: 0.80,  # Uttara Phalguni — BS: acceptable
        # AVOID
        6: 0.00,   # Ardra — AVOID (BS: storms, danger)
        9: 0.00,   # Ashlesha — AVOID (BS: serpent dangers on road)
        18: 0.00,  # Jyeshtha — AVOID (BS: conflict at destination)
        19: 0.00,  # Moola — AVOID (BS: no return / loss)
        2: 0.10,   # Bharani — AVOID (Yama; death on journey)
        14: 0.20,  # Chitra — caution (MC: accidents)
    },
    "vara": {
        # Source: MC 6.1; BS §Yatra; DP
        # Direction rules apply (BS) but for day-scoring we use general auspiciousness
        1: 0.80,   # Sunday — acceptable (Sun: authority, bold travel)
        2: 0.85,   # Monday — auspicious (Moon: waters, North direction)
        4: 0.90,   # Wednesday — auspicious (Mercury: commerce, travel)
        5: 0.95,   # Thursday — highly auspicious (Jupiter: safe, prosperous journey)
        6: 0.90,   # Friday — auspicious (Venus: comfortable travel)
        3: 0.40,   # Tuesday — cautious (Mars: accidents, conflict)
        7: 0.20,   # Saturday — avoid (Saturn: delays, hardship)
    },
}

# ---------------------------------------------------------------------------
# §22.5 — PROPERTY PURCHASE (Property / Vehicle Purchase) quality table
# Source: MC 7.1; MMP §Property; DP convention
# ---------------------------------------------------------------------------
PROPERTY_PURCHASE_QUALITY: dict = {
    "tithi": {
        # Source: MC 7.1 — fixed / stable tithis preferred
        2: 0.80,   # Shukla Dvitiya — MC 7.1: auspicious
        3: 0.85,   # Shukla Tritiya — MC 7.1: auspicious
        5: 0.90,   # Shukla Panchami — MC 7.1: very auspicious
        7: 0.85,   # Shukla Saptami — MC 7.1: auspicious
        10: 0.95,  # Shukla Dashami — MC 7.1: highly auspicious
        11: 0.85,  # Shukla Ekadashi — MC 7.1: auspicious
        12: 0.90,  # Shukla Dvadashi — MC 7.1: auspicious (Tripushkar amplifier)
        13: 0.80,  # Shukla Trayodashi — MC 7.1: acceptable
        15: 0.85,  # Purnima — MC 7.1: auspicious (fullness; abundance)
        1: 0.65,   # Pratipada — MC 7.1: acceptable new beginning
        6: 0.70,   # Shashthi — MC 7.1: acceptable
        # AVOID
        4: 0.00,   # Chaturthi — AVOID (MC 7.1: obstacles, disputed ownership)
        8: 0.00,   # Ashtami — AVOID
        9: 0.00,   # Navami — AVOID
        14: 0.00,  # Chaturdashi — AVOID
        30: 0.00,  # Amavasya — AVOID
    },
    "nakshatra": {
        # Source: MC 7.1; fixed nakshatras best for stable property
        4: 0.95,   # Rohini — MC 7.1: best (fixed; stable property)
        8: 0.95,   # Pushya — MC 7.1: best (nourishment; prosperity)
        12: 0.90,  # Uttara Phalguni — MC 7.1: highly auspicious (Aryaman: contracts)
        13: 0.90,  # Hasta — MC 7.1: auspicious (handshake deals)
        21: 0.90,  # Uttara Ashadha — MC 7.1: auspicious (stability; fixed)
        22: 0.85,  # Shravana — MC 7.1: auspicious
        26: 0.85,  # Uttara Bhadrapada — MC 7.1: auspicious (depth; permanence)
        27: 0.90,  # Revati — MC 7.1: auspicious (Pushan: wealth)
        1: 0.80,   # Ashwini — MC 7.1: auspicious (vehicles especially)
        5: 0.80,   # Mrigashira — MC 7.1: auspicious
        7: 0.85,   # Punarvasu — MC 7.1: auspicious
        17: 0.80,  # Anuradha — MC 7.1: auspicious
        # AVOID
        2: 0.00,   # Bharani — AVOID (Yama; possession ends)
        6: 0.00,   # Ardra — AVOID (Rudra; destruction)
        9: 0.00,   # Ashlesha — AVOID (hidden defects; fraud)
        19: 0.00,  # Moola — AVOID (uprooting; no stability)
        14: 0.20,  # Chitra — caution (dispute over aesthetics)
    },
    "vara": {
        # Source: MC 7.1; DP
        2: 0.85,   # Monday — auspicious (Moon: land, real estate)
        4: 0.90,   # Wednesday — auspicious (Mercury: documents, deals)
        5: 0.95,   # Thursday — highly auspicious (Jupiter: expansion, wealth)
        6: 0.90,   # Friday — auspicious (Venus: property comforts)
        1: 0.70,   # Sunday — acceptable
        3: 0.40,   # Tuesday — cautious (Mars: disputes)
        7: 0.20,   # Saturday — avoid (Saturn: encumbrances, old burdens)
    },
}

# ---------------------------------------------------------------------------
# §22.6 — MANTRA INITIATION (Mantra Diksha / Spiritual Initiation) quality table
# Source: MC 8.1 (diksha muhurta); BS §Diksha; DP convention
# ---------------------------------------------------------------------------
MANTRA_INITIATION_QUALITY: dict = {
    "tithi": {
        # Source: MC 8.1 — spiritual tithis; Ekadashi and Purnima especially auspicious
        1: 0.70,   # Shukla Pratipada — MC 8.1: acceptable for new initiations
        2: 0.75,   # Shukla Dvitiya — MC 8.1: auspicious
        3: 0.80,   # Shukla Tritiya — MC 8.1: auspicious
        5: 0.85,   # Shukla Panchami — MC 8.1: auspicious (Saraswati; mantra power)
        7: 0.85,   # Shukla Saptami — MC 8.1: auspicious (Sun; divine light)
        10: 0.85,  # Shukla Dashami — MC 8.1: auspicious
        11: 0.95,  # Shukla Ekadashi — MC 8.1: highly auspicious (Vishnu day; tapas)
        12: 0.90,  # Shukla Dvadashi — MC 8.1: auspicious (post-Ekadashi; pure)
        13: 0.80,  # Shukla Trayodashi — MC 8.1: auspicious (Shiva; mantra)
        15: 0.95,  # Purnima — MC 8.1: best for diksha (fullness; Guru Purnima)
        # Krishna Navami in some traditions: Durga Navami auspicious for Shakti diksha
        24: 0.80,  # Krishna Navami (24 in continuous count) — Shakti traditions
        # AVOID
        4: 0.00,   # Chaturthi — AVOID (MC 8.1: obstacles to mantra siddhi)
        14: 0.00,  # Chaturdashi — AVOID (unless Shivaratri; handled by special_yogas)
        30: 0.00,  # Amavasya — AVOID (pitru tithi; not for diksha initiation)
        8: 0.20,   # Ashtami — caution (Kali tithis; Shakti schools only)
        9: 0.30,   # Navami — caution (Durga; Shakti schools only)
    },
    "nakshatra": {
        # Source: BS §Diksha; MC 8.1; Tantra traditions
        1: 0.80,   # Ashwini — MC 8.1: auspicious (Ashwins: healing mantras)
        4: 0.90,   # Rohini — MC 8.1: auspicious (Brahma/Prajapati: creation mantras)
        7: 0.90,   # Punarvasu — MC 8.1: highly auspicious (Aditi: renewal)
        8: 0.95,   # Pushya — MC 8.1: best for diksha (Brihaspati: guru of gods)
        10: 0.85,  # Magha — MC 8.1: auspicious (Pitrs: ancestral lineage diksha)
        12: 0.90,  # Uttara Phalguni — MC 8.1: auspicious (Aryaman: contracts with divine)
        13: 0.85,  # Hasta — MC 8.1: auspicious (Savitri: solar mantras)
        17: 0.85,  # Anuradha — MC 8.1: auspicious (Mitra: friendship with deity)
        20: 0.80,  # Purva Ashadha — MC 8.1: auspicious (Apas: purification mantras)
        21: 0.85,  # Uttara Ashadha — MC 8.1: auspicious (Vishvedevas: universal)
        22: 0.90,  # Shravana — MC 8.1: auspicious (Vishnu: Vaishnava mantras)
        25: 0.85,  # Purva Bhadrapada — MC 8.1: auspicious (Aja Ekapad: depth)
        27: 0.90,  # Revati — MC 8.1: highly auspicious (Pushan: completion, journey's end)
        5: 0.75,   # Mrigashira — MC 8.1: acceptable (Moon: chandra mantras)
        26: 0.85,  # Uttara Bhadrapada — MC 8.1: auspicious (Ahir Budhnya: tantric)
        # AVOID
        6: 0.00,   # Ardra — AVOID (Rudra: intense; not for standard diksha)
        9: 0.00,   # Ashlesha — AVOID (Sarpa: deceptive energies)
        18: 0.00,  # Jyeshtha — AVOID (Indra: pride; ego obstacles)
        19: 0.00,  # Moola — AVOID (Nirrti: dissolution; not for initiation)
        2: 0.10,   # Bharani — AVOID (Yama: death energy)
    },
    "vara": {
        # Source: MC 8.1; BS §Diksha
        2: 0.85,   # Monday — auspicious (Moon: mantra, mind, Shiva-related)
        4: 0.90,   # Wednesday — auspicious (Mercury: mantra science)
        5: 0.95,   # Thursday — best (Jupiter: Guru; all spiritual initiation)
        6: 0.85,   # Friday — auspicious (Venus: Shakti, tantric initiation)
        7: 0.80,   # Saturday — acceptable for Saturn mantras/Hanuman (MC 8.1)
        1: 0.80,   # Sunday — auspicious (Sun: Surya/Gayatri mantras)
        3: 0.40,   # Tuesday — avoid for most (Mars: tamasic energy for diksha)
    },
}

# ---------------------------------------------------------------------------
# §22.7 — UPĀYA RITUAL (Remedial action: homa, dana, japa, puja, vrata) quality table
# L3 Kāla K1 addition (ka_muhurta_seva, 2026-06-21)
# Source: MC §Upāya; Brihat Parashara Hora Shastra §Upāya Shastra; DP convention
# ---------------------------------------------------------------------------
UPAYA_RITUAL_QUALITY: dict = {
    "tithi": {
        # Source: MC §Upāya; BPHS §Upāya Shastra
        # Shukla paksha strongly preferred (building energy for remediation)
        1: 0.80,   # Shukla Pratipada — auspicious (new beginning; ideal for starting vrata)
        3: 0.90,   # Shukla Tritiya — highly auspicious (Akshaya Tritiya energy; Goddess)
        5: 0.90,   # Shukla Panchami — auspicious (Saraswati; mantra-related upāya)
        7: 0.85,   # Shukla Saptami — auspicious (Surya upāya; Aditya homa)
        10: 0.85,  # Shukla Dashami — auspicious (Dharma tithi; navagraha homa)
        11: 0.95,  # Shukla Ekadashi — best (Vishnu; fasting + Vishnu-related upāya)
        12: 0.90,  # Shukla Dvadashi — auspicious (Vishnu energy continues)
        13: 0.85,  # Shukla Trayodashi — auspicious (Shiva; Rudrabhisheka)
        14: 0.70,  # Shukla Chaturdashi — acceptable (Shiva Chaturdashi; Shivaratri-adjacent)
        15: 0.90,  # Purnima — highly auspicious (full Moon; homas maximally effective)
        # Krishna paksha acceptable for Saturn/Ketu/Rahu upāya (karmic dissolution)
        24: 0.75,  # Krishna Navami — acceptable for Durga/Kali upāya
        26: 0.80,  # Krishna Ekadashi — acceptable (Vishnu still relevant)
        # AVOID for upāya (these tithis resist remediation)
        4: 0.10,   # Chaturthi — avoid (Vighna; obstacles block remediation)
        8: 0.20,   # Ashtami — caution (Kali/Mars energy; use only for Mars upāya)
        9: 0.30,   # Navami — caution (Durga; Shakti upāya acceptable)
        30: 0.20,  # Amavasya — avoid for most (pitru; use ONLY for pitru tarpana/upāya)
    },
    "nakshatra": {
        # Source: MC §Upāya; BPHS §Upāya Shastra
        # Pushya reigns supreme for any upāya (Brihaspati/Guru energy amplifies all remediation)
        8: 0.99,   # Pushya — supreme for upāya (Guru Pushya = best upāya muhurta)
        4: 0.90,   # Rohini — auspicious (Brahma; wealth/prosperity upāya)
        7: 0.90,   # Punarvasu — auspicious (Aditi; renewal; removing afflictions)
        12: 0.90,  # Uttara Phalguni — auspicious (Aryaman; contractual karmas)
        13: 0.85,  # Hasta — auspicious (Savitri; skill-related upāya)
        17: 0.85,  # Anuradha — auspicious (Mitra; relationship upāya)
        22: 0.85,  # Shravana — auspicious (Vishnu; Vishnu-related upāya)
        25: 0.80,  # Purva Bhadrapada — auspicious (Aja Ekapad; depth of remediation)
        26: 0.85,  # Uttara Bhadrapada — auspicious (Ahir Budhnya; Saturn upāya)
        27: 0.90,  # Revati — auspicious (Pushan; journey upāya; completion)
        21: 0.85,  # Uttara Ashadha — auspicious (Vishvedevas; universal upāya)
        # AVOID for upāya
        6: 0.00,   # Ardra — AVOID (Rudra; intensifies affliction instead of remediating)
        9: 0.00,   # Ashlesha — AVOID (Sarpa; deception impedes remediation)
        19: 0.00,  # Moola — AVOID (dissolution; upāya can backfire)
        2: 0.10,   # Bharani — AVOID (Yama; mortality energy)
    },
    "vara": {
        # Source: MC §Upāya; DP convention
        # Planetary days align with the upāya's planetary target
        5: 0.95,   # Thursday — best universal upāya day (Jupiter: amplification)
        2: 0.90,   # Monday — auspicious (Moon/Shiva upāya; Rudrabhisheka)
        6: 0.90,   # Friday — auspicious (Venus/Lakshmi upāya; wealth remediation)
        4: 0.85,   # Wednesday — auspicious (Mercury; business/education upāya)
        1: 0.80,   # Sunday — auspicious (Surya upāya; Aditya Hridayam)
        7: 0.80,   # Saturday — auspicious FOR Saturn upāya specifically (Shani)
        3: 0.60,   # Tuesday — acceptable for Mars/Hanuman upāya (Mangala)
    },
}

# ---------------------------------------------------------------------------
# §22.8 — SĀDHANA INITIATION (beginning a sustained spiritual practice) quality table
# L3 Kāla K1 addition (ka_muhurta_seva, 2026-06-21)
# Source: MC §Diksha + §Upāya; Yoga Shastra tradition; DP convention
# Note: Distinct from mantra_initiation (one-time diksha) — this is for beginning
# an ongoing practice (daily japa, yoga abhyasa, meditation course, etc.)
# ---------------------------------------------------------------------------
SADHANA_INITIATION_QUALITY: dict = {
    "tithi": {
        # Source: MC §Diksha; Yoga tradition; DP convention
        # Shukla paksha strongly preferred (growing phase builds the sādhana)
        1: 0.80,   # Shukla Pratipada — excellent (new cycle; beginning amplified)
        2: 0.80,   # Shukla Dvitiya — auspicious
        3: 0.85,   # Shukla Tritiya — auspicious (Akshaya Tritiya quality)
        5: 0.90,   # Shukla Panchami — auspicious (Saraswati; knowledge-based sādhana)
        7: 0.85,   # Shukla Saptami — auspicious (Sun; solar practices)
        10: 0.85,  # Shukla Dashami — auspicious (Dharma tithi)
        11: 0.95,  # Shukla Ekadashi — premier (fasting + tapas initiation)
        12: 0.90,  # Shukla Dvadashi — auspicious (post-Ekadashi discipline)
        13: 0.85,  # Shukla Trayodashi — auspicious (Shiva; Shaiva sādhana)
        15: 0.95,  # Purnima — premier (Guru Purnima; completeness; sādhana peaks)
        # AVOID
        4: 0.00,   # Chaturthi — AVOID (Vighna; obstacles to sustained practice)
        8: 0.20,   # Ashtami — caution
        9: 0.30,   # Navami — caution
        14: 0.30,  # Chaturdashi — caution (Shivaratri exception via special_yogas)
        30: 0.10,  # Amavasya — AVOID for beginnings
    },
    "nakshatra": {
        # Source: MC §Diksha; BS §Diksha; Yoga tradition
        # Fixed (sthira) nakshatras are especially prized for sustained practice
        # because the Moon's stability supports long-term discipline
        4: 0.95,   # Rohini — premier (Brahma/Prajapati: steady creation; sthira)
        12: 0.90,  # Uttara Phalguni — auspicious (Aryaman: steady; sthira)
        21: 0.90,  # Uttara Ashadha — auspicious (Vishvedevas: universal practice; sthira)
        26: 0.90,  # Uttara Bhadrapada — auspicious (Ahir Budhnya: depth; sthira)
        8: 0.95,   # Pushya — premier for sādhana (Brihaspati: all spiritual practices)
        7: 0.90,   # Punarvasu — highly auspicious (Aditi: renewal and growth)
        22: 0.90,  # Shravana — auspicious (Vishnu: Vaishnava/bhakti practices)
        17: 0.85,  # Anuradha — auspicious (Mitra: devotion, consistent relationship)
        27: 0.90,  # Revati — auspicious (Pushan: nurturing; gentle practices)
        5: 0.80,   # Mrigashira — auspicious (Moon: lunar practices, soma)
        13: 0.85,  # Hasta — auspicious (Savitri: yoga asana especially)
        25: 0.85,  # Purva Bhadrapada — auspicious (Aja Ekapad: depth of practice)
        10: 0.85,  # Magha — auspicious (Pitrs: ancestral lineage practices)
        # AVOID for sādhana initiation
        6: 0.00,   # Ardra — AVOID (Rudra: instability; destroys sustained effort)
        9: 0.00,   # Ashlesha — AVOID (Sarpa: subtle toxicity in long-term practice)
        19: 0.00,  # Moola — AVOID (dissolution of roots; prevents stability)
        18: 0.10,  # Jyeshtha — AVOID (Indra's pride interrupts humility of sādhana)
        2: 0.10,   # Bharani — AVOID (Yama: completion rather than beginning)
    },
    "vara": {
        # Source: MC §Diksha; Yoga tradition; DP convention
        # Thursday (Guru) is universally the best day to begin any sādhana
        5: 0.99,   # Thursday — supreme for sādhana initiation (Guru/Jupiter)
        2: 0.85,   # Monday — auspicious (Moon/Shiva; Shaiva/lunar practices)
        6: 0.85,   # Friday — auspicious (Venus/Shakti; bhakti, arts-based sādhana)
        4: 0.85,   # Wednesday — auspicious (Mercury; mantra, study-based sādhana)
        1: 0.80,   # Sunday — auspicious (Sun; solar practices, Surya Namaskara)
        7: 0.75,   # Saturday — acceptable for Saturn-aligned sādhana (Shani; tapas)
        3: 0.50,   # Tuesday — acceptable for Hanuman/Mars practices only (MC 8.1)
    },
}

# ---------------------------------------------------------------------------
# §23 — EVENT → TABLE mapping (central dispatch for score_muhurat)
# ---------------------------------------------------------------------------
EVENT_TABLES: dict = {
    "vivah":               VIVAH_QUALITY,
    "griha_pravesh":       GRIHA_PRAVESH_QUALITY,
    "vyapara":             VYAPARA_QUALITY,
    "yatra":               YATRA_QUALITY,
    "property_purchase":   PROPERTY_PURCHASE_QUALITY,
    "mantra_initiation":   MANTRA_INITIATION_QUALITY,
    # L3 Kāla K1 additions (ka_muhurta_seva, 2026-06-21)
    "upaya_ritual":        UPAYA_RITUAL_QUALITY,
    "sadhana_initiation":  SADHANA_INITIATION_QUALITY,
}

# ---------------------------------------------------------------------------
# §24 — Muhurat Scoring Weights
# Weights are now canonical in config/muhurat_weights.yaml (Phase 4C-6-S2).
# Load via panchang_engine.config_loader.get_weights_for_event(event).
# DEFAULT_MUHURAT_WEIGHTS was removed in S2; do not re-add it here.
# ---------------------------------------------------------------------------
# (constant removed — see config/muhurat_weights.yaml)

# ===========================================================================
# Rich output contract additions
# ===========================================================================

# Yamakantaka: vara_id → index of 8th day-part (1-based)
YAMAKANTAKA_INDEX: dict = {
    1: 4,   # Sunday
    2: 3,   # Monday
    3: 2,   # Tuesday
    4: 7,   # Wednesday
    5: 1,   # Thursday
    6: 6,   # Friday
    7: 5,   # Saturday
}

# Krakaca: vara_id → index of 8th night-part (1-based)
KRAKACA_INDEX: dict = {
    1: 6,   # Sunday
    2: 5,   # Monday
    3: 4,   # Tuesday
    4: 3,   # Wednesday
    5: 2,   # Thursday
    6: 1,   # Friday
    7: 7,   # Saturday
}

# Visha Ghati: nakshatra_id → list of ghatika numbers that are inauspicious
VISHA_GHATI_TABLE: dict = {
    1: [4],   2: [2],   3: [7],   4: [9],   5: [5],
    6: [3],   7: [8],   8: [6],   9: [10],  10: [1],
    11: [4],  12: [2],  13: [7],  14: [9],  15: [5],
    16: [3],  17: [8],  18: [6],  19: [10], 20: [1],
    21: [4],  22: [2],  23: [7],  24: [9],  25: [5],
    26: [3],  27: [8],
}

# Sashtighati: 6th and 8th ghatika of the day are inauspicious
SASHTIGHATI_GHATIKAS: list = [6, 8]

# Anandadi Yoga: 28-yoga series. Index = (vara_id + nakshatra_id - 2) % 28
ANANDADI_YOGA_NAMES: list = [
    "Ananda",       "Kaladanda",    "Dhumra",       "Dhumketu",
    "Dhwanksha",    "Dhwaja",       "Srivatsa",     "Vajra",
    "Mudgara",      "Chhatra",      "Mitra",        "Manasa",
    "Padma",        "Lumba",        "Utpata",       "Mrityu",
    "Kana",         "Siddhi",       "Subha",        "Amrita",
    "Musala",       "Gada",         "Matanga",      "Raksha",
    "Chara",        "Sthira",       "Pravardhamana","Prajapati",
]
ANANDADI_AUSPICIOUS: set = {1, 6, 7, 8, 10, 11, 13, 18, 19, 20, 26, 27, 28}

# Agni Vasa: tithi_id → element
AGNI_VASA_TABLE: dict = {
    **{t: "Prithvi" for t in range(1, 8)},
    **{t: "Jala"    for t in range(8, 16)},
    **{t: "Vayu"    for t in range(16, 23)},
    **{t: "Akasha"  for t in range(23, 31)},
}

# Chandra Vasa: tithi_id → direction
CHANDRA_VASA_TABLE: dict = {
    1: "East", 2: "East", 3: "South", 4: "South",
    5: "West",  6: "West",  7: "North", 8: "North",
    9: "East", 10: "East", 11: "South", 12: "South",
    13: "West", 14: "West", 15: "North", 16: "North",
    17: "East", 18: "East", 19: "South", 20: "South",
    21: "West", 22: "West", 23: "North", 24: "North",
    25: "East", 26: "East", 27: "South", 28: "South",
    29: "West", 30: "West",
}

# Rahu Vasa: vara_id → direction
RAHU_VASA_TABLE: dict = {
    1: "West", 2: "North", 3: "South", 4: "North",
    5: "West", 6: "South", 7: "East",
}

# Disha Shul (Disha Vasa): vara_id → direction to avoid
DISHA_SHUL_TABLE: dict = {
    1: "West", 2: "East", 3: "North", 4: "North",
    5: "South", 6: "West", 7: "East",
}

# Nakshatra Vasa: nakshatra_id → direction
NAKSHATRA_VASA_TABLE: dict = {
    **{n: "East"  for n in [1, 2, 3, 4, 5, 6, 7]},
    **{n: "South" for n in [8, 9, 10, 11, 12, 13, 14]},
    **{n: "West"  for n in [15, 16, 17, 18, 19, 20, 21]},
    **{n: "North" for n in [22, 23, 24, 25, 26, 27]},
}

# Bhadra Vasa: tithi_id → residence
BHADRA_VASA_TABLE: dict = {
    **{t: "Svarga"   for t in [1, 6, 11, 16, 21, 26]},
    **{t: "Prishtha" for t in [2, 7, 12, 17, 22, 27]},
    **{t: "Madhya"   for t in [3, 8, 13, 18, 23, 28]},
    **{t: "Jala"     for t in [4, 9, 14, 19, 24, 29]},
    **{t: "Simha"    for t in [5, 10, 15, 20, 25, 30]},
}

# 5-Panchaka: nakshatra_id → type (nakshatras 23-27 only)
PANCHAKA_TYPE_TABLE: dict = {
    23: "Roga",
    24: "Raja",
    25: "Agni",
    26: "Chora",
    27: "Mrityu",
}

# Tithi Shoonya: tithi_id → sign_id that is void
TITHI_SHOONYA_TABLE: dict = {
    1: 6,  2: 1,  3: 8,  4: 4,  5: 10,
    6: 5,  7: 2,  8: 11, 9: 7,  10: 12,
    11: 3, 12: 9, 13: 6, 14: 1, 15: 8,
    16: 6, 17: 1, 18: 8, 19: 4, 20: 10,
    21: 5, 22: 2, 23: 11, 24: 7, 25: 12,
    26: 3, 27: 9, 28: 6, 29: 1, 30: 8,
}

# Nakshatra Shoonya: nakshatra_id → sign_id that is void
NAKSHATRA_SHOONYA_TABLE: dict = {
    1: 5,  2: 6,  3: 7,  4: 8,  5: 9,
    6: 10, 7: 11, 8: 12, 9: 1,  10: 2,
    11: 3, 12: 4, 13: 5, 14: 6, 15: 7,
    16: 8, 17: 9, 18: 10,19: 11,20: 12,
    21: 1, 22: 2, 23: 3, 24: 4, 25: 5,
    26: 6, 27: 7,
}

# Jovian 60-year cycle (Samvatsara)
JOVIAN_60_YEAR_NAMES: list = [
    "Prabhava", "Vibhava", "Shukla", "Pramoda", "Prajapati",
    "Angirasa", "Shrimukha", "Bhava", "Yuva", "Dhatri",
    "Ishvara", "Bahudhanya", "Pramadi", "Vikrama", "Vrisha",
    "Chitrabhanu", "Subhanu", "Tarana", "Parthiva", "Vyaya",
    "Sarvajit", "Sarvadharin", "Virodhin", "Vikruti", "Khara",
    "Nandana", "Vijaya", "Jaya", "Manmatha", "Durmukhi",
    "Hevilambi", "Vilambi", "Vikari", "Sharvari", "Plava",
    "Shubhakruti", "Sobhakruti", "Krodhi", "Vishvavasu", "Parabhava",
    "Plavanga", "Kilaka", "Saumya", "Sadharana", "Virodhakrut",
    "Paridhavin", "Pramadi", "Ananda", "Rakshasa", "Anala",
    "Pingala", "Kalayukti", "Siddharthi", "Raudra", "Durmati",
    "Dundubhi", "Rudhirodgari", "Raktakshi", "Krodhana", "Akshaya",
]

# Festival rules: {name, tithi_ids, masa_ids, paksha}
FESTIVAL_RULES: list = [
    {"name": "Ekadashi",            "tithi_ids": {11},  "masa_ids": None, "paksha": "any"},
    {"name": "Pradosh",             "tithi_ids": {13},  "masa_ids": None, "paksha": "any"},
    {"name": "Purnima",             "tithi_ids": {15},  "masa_ids": None, "paksha": "shukla"},
    {"name": "Amavasya",            "tithi_ids": {30},  "masa_ids": None, "paksha": "krishna"},
    {"name": "Sankashti Chaturthi", "tithi_ids": {19},  "masa_ids": None, "paksha": "krishna"},
    {"name": "Shivaratri",          "tithi_ids": {29},  "masa_ids": None, "paksha": "krishna"},
    {"name": "Chaturthi",           "tithi_ids": {4},   "masa_ids": None, "paksha": "shukla"},
    {"name": "Navami",              "tithi_ids": {9},   "masa_ids": None, "paksha": "shukla"},
]
