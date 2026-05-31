"""
Canonical Jyotish name tables — fixed classical/astronomical constants.

These are NOT computed; they are the standard sidereal-zodiac sign names,
nakshatra names, sign-lords, and panchanga-anga names. Encoded directly here
(rather than read from PyJHora's i18n resource files) so the adapter has zero
dependency on PyJHora's language-pack layout and is fully deterministic.

All indices follow PyJHora's conventions:
  - sign index: 0 = Aries .. 11 = Pisces
  - planet id:  0=Sun 1=Moon 2=Mars 3=Mercury 4=Jupiter 5=Venus 6=Saturn
                7=Rahu 8=Ketu  ('L' = Lagna/Ascendant)
  - nakshatra index here is normalised to 1-based (1=Ashwini .. 27=Revati)
"""
from __future__ import annotations

# 0-indexed: Aries .. Pisces
SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Sign lord by sign index (0=Aries..11=Pisces) — classical rulerships.
SIGN_LORDS = [
    "Mars",     # Aries
    "Venus",    # Taurus
    "Mercury",  # Gemini
    "Moon",     # Cancer
    "Sun",      # Leo
    "Mercury",  # Virgo
    "Venus",    # Libra
    "Mars",     # Scorpio
    "Jupiter",  # Sagittarius
    "Saturn",   # Capricorn
    "Saturn",   # Aquarius
    "Jupiter",  # Pisces
]

# Planet id -> canonical name. Matches natal_engine graha order.
PLANET_NAMES = {
    0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter",
    5: "Venus", 6: "Saturn", 7: "Rahu", 8: "Ketu",
}

# The 9-graha emission order (matches natal_engine: Sun..Ketu).
GRAHA_ORDER = [0, 1, 2, 3, 4, 5, 6, 7, 8]

# 27 nakshatras, 1-based index (index 0 unused placeholder).
NAKSHATRA_NAMES = [
    "",  # 0 unused
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

# Nakshatra lord by 1-based nakshatra index (Vimshottari dasha lord cycle).
# Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury repeating.
_NAK_LORD_CYCLE = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
]
NAKSHATRA_LORDS = [""] + [_NAK_LORD_CYCLE[(i - 1) % 9] for i in range(1, 28)]

# Tithi names, 1-based (1=Shukla Pratipada .. 30=Amavasya). PyJHora tithi()
# returns a 1..30 index where 1..15 are Shukla paksha, 16..30 Krishna paksha.
_TITHI_BASE = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
]


def tithi_name(idx: int) -> str:
    """idx is PyJHora 1-based tithi index (1..30)."""
    if idx <= 0:
        return ""
    if idx == 15:
        return "Purnima"
    if idx == 30:
        return "Amavasya"
    if idx <= 15:
        return f"Shukla {_TITHI_BASE[idx - 1]}"
    # Krishna paksha 16..29 -> Pratipada..Chaturdashi
    return f"Krishna {_TITHI_BASE[(idx - 16) % 14]}"


# Vara (weekday) — PyJHora vaara() returns 0=Sunday .. 6=Saturday.
VARA_NAMES = [
    "Ravivara",     # 0 Sunday
    "Somavara",     # 1 Monday
    "Mangalavara",  # 2 Tuesday
    "Budhavara",    # 3 Wednesday
    "Guruvara",     # 4 Thursday
    "Shukravara",   # 5 Friday
    "Shanivara",    # 6 Saturday
]

# 27 Yoga names, 1-based (PyJHora yogam() returns 1..27).
YOGA_NAMES = [
    "",  # 0 unused
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi",
    "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
    "Variyana", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti",
]

# Karana. PyJHora karana() returns a karana index in [1..60] where
#   1 = Kimstughna, 2 = Bava, ..., 60 = Naga.
# There are 11 distinct karanas: 4 fixed (Kimstughna at the very start; Shakuni,
# Chatushpada, Naga at the very end) and 7 movable (Bava..Vishti) that cycle 8
# times in between. We resolve the 60-index to its name below.
_KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja",
                   "Vanija", "Vishti"]
# Full list for the 11 distinct names (used by tests/introspection).
KARANA_NAMES = [
    "",  # 0 unused
    "Kimstughna", "Bava", "Balava", "Kaulava", "Taitila",
    "Garaja", "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga",
]


def karana_name(idx_1_to_60: int) -> str:
    """Resolve PyJHora's 1..60 karana index to a karana name.

    Index 1 = Kimstughna (fixed). Indices 58/59/60 = Shakuni/Chatushpada/Naga
    (fixed). Indices 2..57 cycle the 7 movable karanas Bava..Vishti.
    """
    i = int(idx_1_to_60)
    if i <= 1:
        return "Kimstughna"
    if i == 58:
        return "Shakuni"
    if i == 59:
        return "Chatushpada"
    if i >= 60:
        return "Naga"
    # 2..57 -> movable cycle (offset so index 2 -> Bava)
    return _KARANA_MOVABLE[(i - 2) % 7]


def sign_name(sign_idx: int) -> str:
    return SIGN_NAMES[sign_idx % 12]


def sign_lord(sign_idx: int) -> str:
    return SIGN_LORDS[sign_idx % 12]


def nakshatra_name(nak_idx_1based: int) -> str:
    if 1 <= nak_idx_1based <= 27:
        return NAKSHATRA_NAMES[nak_idx_1based]
    return ""


def nakshatra_lord(nak_idx_1based: int) -> str:
    if 1 <= nak_idx_1based <= 27:
        return NAKSHATRA_LORDS[nak_idx_1based]
    return ""
