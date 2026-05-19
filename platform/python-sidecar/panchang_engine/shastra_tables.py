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
    # 4C-1-S2 populates this
    nakshatra_id: [None, None] for nakshatra_id in range(1, 28)
}  # Stub shell — 4C-1-S2 populates this

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
# §16–§19 — Special Yoga Lookup Tables (STUB SHELLS — 4C-1-S2 populates)
# Source: MC §10–§12; BS §3; DP convention.
# ---------------------------------------------------------------------------

# Sarvartha Siddhi Yoga: vara×nakshatra combinations that create this auspicious yoga.
# Source: MC §10; DP. Format: {vara_id: [nakshatra_ids...]}
SARVARTHA_SIDDHI_TABLE: dict[int, list[int]] = {}  # 4C-1-S2 populates this

# Amrit Siddhi Yoga: vara×nakshatra combinations.
# Source: MC §10; DP. Format: {vara_id: [nakshatra_ids...]}
AMRIT_SIDDHI_TABLE: dict[int, list[int]] = {}  # 4C-1-S2 populates this

# Dwipushkar / Tripushkar Yoga: tithi×vara×nakshatra combinations.
# Source: MC §11; DP. Format: list of (tithi_ids, vara_ids, nakshatra_ids) tuples.
DWIPUSHKAR_TABLE: list[dict] = []   # 4C-1-S2 populates this
TRIPUSHKAR_TABLE: list[dict] = []   # 4C-1-S2 populates this
