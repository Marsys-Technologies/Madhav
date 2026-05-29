"""
era_fixed_stars.py — G31 Era Conversion + G32 Fixed Star Catalog
MARSYS-JIS Global Reference Data
BUILD-ORCH-A-12

G31: Calendrical era conversion (Kali Yuga, Vikram Samvat, Shaka Samvat, Saptarshi,
     Julian Day Number).
G32: Fixed star catalog (~50 stars) with J2000 tropical longitudes, ecliptic latitudes,
     Jyotish names, nature, and classical significance.
"""

from __future__ import annotations
import math
from typing import Optional

# ---------------------------------------------------------------------------
# G31 — CALENDRICAL ERA EPOCHS
# ---------------------------------------------------------------------------

ERA_EPOCHS = {
    "kali_yuga": {
        "description": "Kali Yuga epoch",
        "jd_start": 588465.5,           # JD at midnight Feb 18 3102 BCE (Julian calendar)
        "gregorian_equivalent": "3102-02-18 BCE Julian",
        "ce_offset": 3101,              # KY year = CE year + 3101 (approx)
    },
    "vikram_samvat": {
        "description": "Vikram Samvat (Bikram Sambat)",
        "jd_start": 1612826.5,          # Approximate JD for 57 BCE epoch
        "gregorian_equivalent": "57 BCE",
        "ce_offset_pre_april": 57,      # Jan–Mar: VS = CE + 57
        "ce_offset_post_march": 56,     # Apr–Dec: VS = CE + 56
    },
    "shaka_samvat": {
        "description": "Shaka Samvat",
        "jd_start": 1749994.5,          # Approximate JD for 78 CE epoch
        "gregorian_equivalent": "78 CE",
        "ce_offset_pre_april": -79,     # Jan–Mar: SS = CE - 79
        "ce_offset_post_march": -78,    # Apr–Dec: SS = CE - 78
    },
    "saptarshi_samvat": {
        "description": "Saptarshi Samvat (Era of the Seven Sages)",
        "jd_start": 493130.5,           # Approximate JD for 3076 BCE
        "gregorian_equivalent": "3076 BCE",
        "ce_offset": 3076,              # SRS year = CE year + 3076
    },
}


# ---------------------------------------------------------------------------
# G31 — JD ↔ GREGORIAN CONVERSION (proleptic Gregorian)
# ---------------------------------------------------------------------------

def gregorian_to_jd(year: int, month: int, day: int) -> float:
    """
    Convert a proleptic Gregorian calendar date to Julian Day Number.

    Uses the standard algorithm valid for all dates (including BCE dates when
    year is given as an astronomical year, i.e. 1 BCE = year 0).

    Returns:
        Julian Day Number as float (noon = .0, midnight = .5 offset not applied —
        this returns the JD for noon on the given date, which is the canonical
        definition of a Julian Day Number boundary).

    Reference: Jean Meeus, "Astronomical Algorithms", Ch. 7.
    """
    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12

    a = math.floor(y / 100)
    b = 2 - a + math.floor(a / 4)

    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day + b - 1524.5
    return jd


def jd_to_gregorian(jd: float) -> tuple[int, int, int]:
    """
    Convert Julian Day Number to proleptic Gregorian calendar date (year, month, day).

    Reference: Jean Meeus, "Astronomical Algorithms", Ch. 7.

    Returns:
        Tuple of (year, month, day) as integers.
    """
    jd_int = jd + 0.5
    z = math.floor(jd_int)
    f = jd_int - z

    if z < 2299161:
        a = z
    else:
        alpha = math.floor((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - math.floor(alpha / 4)

    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d) / 30.6001)

    day = int(b - d - math.floor(30.6001 * e) + f)

    if e < 14:
        month = int(e - 1)
    else:
        month = int(e - 13)

    if month > 2:
        year = int(c - 4716)
    else:
        year = int(c - 4715)

    return (year, month, day)


# ---------------------------------------------------------------------------
# G31 — ERA CONVERSION FUNCTIONS
# ---------------------------------------------------------------------------

def gregorian_to_kali(year: int, month: int, day: int) -> int:
    """
    Return approximate Kali Yuga year for a given Gregorian CE date.

    The Kali Yuga epoch is traditionally Feb 18, 3102 BCE (Julian calendar).
    In astronomical (CE) notation, this is year -3101.
    Therefore KY year ≈ CE year + 3101 for any date CE.

    Note: This is a calendar-year approximation. The precise Kali Yuga year
    depends on the exact tithi at the epoch and the regional calendar variant
    in use; for astrological purposes this integer approximation is standard.

    Args:
        year: Gregorian CE year (positive int)
        month: Month (1–12)
        day: Day of month

    Returns:
        Kali Yuga year (integer)
    """
    return year + 3101


def gregorian_to_vikram(year: int, month: int, day: int) -> int:
    """
    Return approximate Vikram Samvat year for a given Gregorian CE date.

    Vikram Samvat begins in Chaitra (approximately late March / early April).
    Convention used here:
      - January through March (months 1–3): VS = CE + 57
        (the VS year has not yet turned over for the calendar year)
      - April through December (months 4–12): VS = CE + 56
        (the VS year turned over in Chaitra)

    This matches the most common North Indian (Purnimanta) reckoning used in
    astrology software. South Indian (Amanta) and Nepalese variants may differ
    by ±1 year.

    Args:
        year: Gregorian CE year
        month: Month (1–12)
        day: Day of month

    Returns:
        Vikram Samvat year (integer)
    """
    if month <= 3:
        return year + 57
    return year + 56


def gregorian_to_shaka(year: int, month: int, day: int) -> int:
    """
    Return approximate Shaka Samvat year for a given Gregorian CE date.

    Shaka Samvat begins around the vernal equinox (Chaitra Shukla Pratipada),
    which falls in late March. Convention used here:
      - January through March (months 1–3): SS = CE - 79
        (the SS year has not yet turned over)
      - April through December (months 4–12): SS = CE - 78
        (the SS year turned over at the vernal equinox)

    The Indian National Calendar (Saka Calendar) adopted by Government of India
    uses this epoch (78 CE).

    Args:
        year: Gregorian CE year
        month: Month (1–12)
        day: Day of month

    Returns:
        Shaka Samvat year (integer)
    """
    if month <= 3:
        return year - 79
    return year - 78


def gregorian_to_saptarshi(year: int, month: int, day: int) -> int:
    """
    Return approximate Saptarshi Samvat year for a given Gregorian CE date.

    The Saptarshi (Seven Sages) era is reckoned from ~3076 BCE in the
    Kashmiri/Himalayan tradition. Cycle of 2700 years in some reckoning
    but here we return the raw elapsed years since the epoch.

    Args:
        year: Gregorian CE year
        month: Month (1–12)
        day: Day of month

    Returns:
        Saptarshi Samvat year (integer)
    """
    return year + 3076


def jd_to_kali(jd: float) -> int:
    """
    Return Kali Yuga year for a given Julian Day Number.

    Uses the standard epoch JD 588465.5.
    1 tropical year ≈ 365.25 days (approximate for this use).

    Args:
        jd: Julian Day Number

    Returns:
        Kali Yuga year (integer, 1-indexed from epoch year 1)
    """
    days_since_epoch = jd - ERA_EPOCHS["kali_yuga"]["jd_start"]
    return int(days_since_epoch / 365.25) + 1


def julian_to_gregorian(year: int, month: int, day: int) -> tuple[int, int, int]:
    """
    Convert a Julian calendar date to proleptic Gregorian calendar date.

    Uses the Julian Day Number as intermediary.

    Args:
        year: Julian calendar year (astronomical, 1 BCE = 0)
        month: Month (1–12)
        day: Day of month

    Returns:
        Tuple (year, month, day) in Gregorian calendar
    """
    # Julian calendar to JD (no Gregorian correction — use pre-reform formula)
    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12

    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + day - 1524.5
    return jd_to_gregorian(jd)


# ---------------------------------------------------------------------------
# G32 — FIXED STAR CATALOG
# ---------------------------------------------------------------------------
# Longitudes are J2000.0 tropical ecliptic longitudes (degrees).
# Latitudes are ecliptic latitudes (degrees, positive = north of ecliptic).
# Sources: Bernadette Brady "Fixed Stars & Constellations in Astrology";
#          Vivian Robson "Fixed Stars and Constellations in Astrology";
#          Cyril Fagan ayanamsha reference data; standard star catalogues.

FIXED_STARS: list[dict] = [
    # -----------------------------------------------------------------------
    # ARIES SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Hamal",
        "name_sanskrit": "Aswini / Bharani region",
        "bayer": "Alpha Arietis",
        "constellation": "Aries",
        "magnitude": 2.00,
        "j2000_longitude_tropical": 7.67,
        "j2000_latitude": 9.93,
        "nature": "malefic",
        "classical_significance": (
            "Head of Aries; associated with violence and accidents; "
            "linked to the nakshatra Aswini transition into Bharani."
        ),
    },
    {
        "name_latin": "Sheratan",
        "name_sanskrit": "Aswini nakshatra region",
        "bayer": "Beta Arietis",
        "constellation": "Aries",
        "magnitude": 2.64,
        "j2000_longitude_tropical": 3.51,
        "j2000_latitude": 8.47,
        "nature": "malefic",
        "classical_significance": (
            "Second star of Aries; combative nature per Robson; Jyotish: "
            "associated with hasty or impulsive action."
        ),
    },
    {
        "name_latin": "Algol",
        "name_sanskrit": "Kapala / Medusa Shira",
        "bayer": "Beta Persei",
        "constellation": "Perseus",
        "magnitude": 2.12,
        "j2000_longitude_tropical": 26.10,
        "j2000_latitude": 22.40,
        "nature": "malefic",
        "classical_significance": (
            "Most malefic star in Western tradition; the Demon's Head (Medusa). "
            "Eclipsing binary (period 2.87 days) — ancient observations of its "
            "variability reinforced its malefic reputation. Conjunctions indicate "
            "violence, beheadings, accidents. Called Rahu-like in Jyotish."
        ),
    },
    {
        "name_latin": "Achernar",
        "name_sanskrit": "Agni Nadi",
        "bayer": "Alpha Eridani",
        "constellation": "Eridanus",
        "magnitude": 0.46,
        "j2000_longitude_tropical": 15.30,
        "j2000_latitude": -59.50,
        "nature": "benefic",
        "classical_significance": (
            "Mouth of the River Eridanus; southern star, high ecliptic latitude. "
            "Jupiter-like nature; associated with royalty and religious eminence. "
            "Important in southern Indian/Sri Lankan Jyotish traditions."
        ),
    },
    # -----------------------------------------------------------------------
    # TAURUS SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Alcyone",
        "name_sanskrit": "Krittika nakshatra",
        "bayer": "Eta Tauri (Pleiades)",
        "constellation": "Taurus",
        "magnitude": 2.87,
        "j2000_longitude_tropical": 60.00,
        "j2000_latitude": 4.03,
        "nature": "malefic",
        "classical_significance": (
            "Central star of the Pleiades cluster; associated with Krittika nakshatra. "
            "Moon in Krittika on this star can give ambition, authority, and passion. "
            "Mars-Moon nature per Robson; sharp or cutting energy."
        ),
    },
    {
        "name_latin": "Aldebaran",
        "name_sanskrit": "Rohini",
        "bayer": "Alpha Tauri",
        "constellation": "Taurus",
        "magnitude": 0.87,
        "j2000_longitude_tropical": 69.90,
        "j2000_latitude": -5.47,
        "nature": "benefic",
        "classical_significance": (
            "Royal star of the East; one of the four Royal Stars of Persia. "
            "Nakshatra Rohini star; beloved of the Moon (Chandra). Mars-Jupiter "
            "nature; military honor, integrity. Conjunctions bring success but "
            "warn against violence."
        ),
    },
    # -----------------------------------------------------------------------
    # GEMINI SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Rigel",
        "name_sanskrit": "Rajanya / Agastya region",
        "bayer": "Beta Orionis",
        "constellation": "Orion",
        "magnitude": 0.13,
        "j2000_longitude_tropical": 81.30,
        "j2000_latitude": -31.11,
        "nature": "benefic",
        "classical_significance": (
            "Left foot of Orion; one of the brightest stars. Jupiter-Saturn nature. "
            "Associated with mechanical skills, architecture, wealth from labor. "
            "Jyotish: favorable for mathematics, engineering, precision work."
        ),
    },
    {
        "name_latin": "Capella",
        "name_sanskrit": "Brahma Hridaya",
        "bayer": "Alpha Aurigae",
        "constellation": "Auriga",
        "magnitude": 0.08,
        "j2000_longitude_tropical": 81.93,
        "j2000_latitude": 22.86,
        "nature": "benefic",
        "classical_significance": (
            "The She-Goat star; Mercury-Jupiter nature. High ecliptic latitude "
            "(north). Associated with curiosity, learning, and inquisitive mind. "
            "Honors in science and intellectual pursuits."
        ),
    },
    {
        "name_latin": "Bellatrix",
        "name_sanskrit": "Mrigashira border",
        "bayer": "Gamma Orionis",
        "constellation": "Orion",
        "magnitude": 1.64,
        "j2000_longitude_tropical": 80.81,
        "j2000_latitude": -16.75,
        "nature": "malefic",
        "classical_significance": (
            "The Amazon Star / Female Warrior; Mars-Mercury nature. Can give "
            "executive ability but also rash action. Associated with the beginning "
            "of Mrigashira nakshatra."
        ),
    },
    {
        "name_latin": "Betelgeuse",
        "name_sanskrit": "Ardra / Mrigashira junction",
        "bayer": "Alpha Orionis",
        "constellation": "Orion",
        "magnitude": 0.42,
        "j2000_longitude_tropical": 88.79,
        "j2000_latitude": -16.03,
        "nature": "malefic",
        "classical_significance": (
            "Red supergiant; right shoulder of Orion. Mars-Mercury nature per "
            "Robson; fortune, fame, preferment — but swift reversal. Jyotish: "
            "near Ardra nakshatra; Rudra energy. Variable star, eventually a supernova."
        ),
    },
    {
        "name_latin": "Sirius",
        "name_sanskrit": "Mrigavyadha / Lubdhaka",
        "bayer": "Alpha Canis Majoris",
        "constellation": "Canis Major",
        "magnitude": -1.46,
        "j2000_longitude_tropical": 104.08,
        "j2000_latitude": -39.60,
        "nature": "benefic",
        "classical_significance": (
            "Brightest star in the night sky. Jupiter-Mars nature. Called "
            "Mrigavyadha (Deer Hunter / Orion's Dog). Heliacal rising marked "
            "the Nile flood in Egypt. In Jyotish: wealth, renown, public honor, "
            "connection with the masses. Very powerful conjunctions."
        ),
    },
    {
        "name_latin": "Castor",
        "name_sanskrit": "Punarvasu / Dioscuri",
        "bayer": "Alpha Geminorum",
        "constellation": "Gemini",
        "magnitude": 1.58,
        "j2000_longitude_tropical": 113.66,
        "j2000_latitude": 10.05,
        "nature": "neutral",
        "classical_significance": (
            "The mortal twin of the Dioscuri. Saturn-Mercury nature; intellect, "
            "writing, travel. Jyotish: in Punarvasu nakshatra; associated with "
            "return (punar = again), renewal, and Aditi (goddess of infinity)."
        ),
    },
    {
        "name_latin": "Pollux",
        "name_sanskrit": "Punarvasu",
        "bayer": "Beta Geminorum",
        "constellation": "Gemini",
        "magnitude": 1.14,
        "j2000_longitude_tropical": 123.58,
        "j2000_latitude": 6.68,
        "nature": "benefic",
        "classical_significance": (
            "The immortal twin; brightest star in Gemini. Mars nature; courage, "
            "craftiness, and sudden fame. Jyotish: Punarvasu nakshatra endpoint; "
            "associated with blessings, recovery, renewal of fortune."
        ),
    },
    # -----------------------------------------------------------------------
    # CANCER SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Procyon",
        "name_sanskrit": "Gomedhaka region",
        "bayer": "Alpha Canis Minoris",
        "constellation": "Canis Minor",
        "magnitude": 0.34,
        "j2000_longitude_tropical": 115.78,
        "j2000_latitude": -16.02,
        "nature": "benefic",
        "classical_significance": (
            "The Little Dog Star; Mercury-Mars nature. Sudden fame and preferment "
            "with risk of reversal. Jyotish: high ecliptic latitude south; "
            "associated with quick achievement and rashness."
        ),
    },
    {
        "name_latin": "Canopus",
        "name_sanskrit": "Agastya",
        "bayer": "Alpha Carinae",
        "constellation": "Carina",
        "magnitude": -0.74,
        "j2000_longitude_tropical": 114.96,
        "j2000_latitude": -75.84,
        "nature": "benefic",
        "classical_significance": (
            "Second brightest star; extremely southern (lat -76°). Called Agastya "
            "in Jyotish — the great sage who controlled the Vindhya mountains. "
            "Important in South Indian and Sri Lankan traditions. Jupiter-Saturn "
            "nature; navigation, wisdom, spiritual authority. Heliacal rising "
            "marks auspicious muhurtas in southern India."
        ),
    },
    {
        "name_latin": "Asellus Australis",
        "name_sanskrit": "Pushya / Sidhya",
        "bayer": "Delta Cancri",
        "constellation": "Cancer",
        "magnitude": 3.94,
        "j2000_longitude_tropical": 118.29,
        "j2000_latitude": 0.07,
        "nature": "neutral",
        "classical_significance": (
            "Southern Donkey; in the Beehive Cluster (Praesepe) region. "
            "Saturn-Mercury nature. Jyotish: Pushya nakshatra — the most "
            "auspicious nakshatra for beginnings, nourishment, expansion."
        ),
    },
    # -----------------------------------------------------------------------
    # LEO SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Regulus",
        "name_sanskrit": "Magha / Jyestha",
        "bayer": "Alpha Leonis",
        "constellation": "Leo",
        "magnitude": 1.36,
        "j2000_longitude_tropical": 149.83,
        "j2000_latitude": 0.46,
        "nature": "benefic",
        "classical_significance": (
            "The King Star; Royal Star of the North; one of the four Royal Stars "
            "of Persia. Lies almost exactly on the ecliptic (lat 0.5°). Jupiter-Mars "
            "nature. Jyotish: Magha nakshatra — ancestors, royalty, honor, power. "
            "Conjunctions with Regulus are among the most powerful in predictive "
            "astrology; success and fame, but with pride as the pitfall."
        ),
    },
    {
        "name_latin": "Alphard",
        "name_sanskrit": "Ashlesha region",
        "bayer": "Alpha Hydrae",
        "constellation": "Hydra",
        "magnitude": 1.98,
        "j2000_longitude_tropical": 147.14,
        "j2000_latitude": -22.36,
        "nature": "malefic",
        "classical_significance": (
            "Heart of the Water Serpent; Saturn-Venus nature. Dissolute or "
            "addictive tendencies when prominent. Jyotish: associated with "
            "Ashlesha (the clinging, serpentine nakshatra)."
        ),
    },
    # -----------------------------------------------------------------------
    # VIRGO SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Denebola",
        "name_sanskrit": "Uttara Phalguni",
        "bayer": "Beta Leonis",
        "constellation": "Leo",
        "magnitude": 2.14,
        "j2000_longitude_tropical": 182.53,
        "j2000_latitude": 14.33,
        "nature": "malefic",
        "classical_significance": (
            "Tail of the Lion; Saturn-Venus nature. Associated with disgrace, "
            "criticism, and sudden loss of position. Jyotish: Uttara Phalguni "
            "nakshatra; contracts, partnerships, service."
        ),
    },
    {
        "name_latin": "Spica",
        "name_sanskrit": "Chitra",
        "bayer": "Alpha Virginis",
        "constellation": "Virgo",
        "magnitude": 0.97,
        "j2000_longitude_tropical": 203.91,
        "j2000_latitude": -2.05,
        "nature": "benefic",
        "classical_significance": (
            "THE most important reference star in Jyotish ayanamsha calibration. "
            "Chitra nakshatra is named for this star (Chitra = brilliant, shining "
            "gem). Venus-Mars nature. Fomalhaut-like: pure benefic when well placed. "
            "The Lahiri ayanamsha is defined such that Spica = 0° Chitra (180° sidereal "
            "from 0° Aries). Conjunctions bring artistry, fame, and wealth."
        ),
    },
    {
        "name_latin": "Acrux",
        "name_sanskrit": "Chitra / Vishakha region",
        "bayer": "Alpha Crucis",
        "constellation": "Crux (Southern Cross)",
        "magnitude": 0.77,
        "j2000_longitude_tropical": 201.78,
        "j2000_latitude": -59.71,
        "nature": "benefic",
        "classical_significance": (
            "Top star of the Southern Cross; extremely southern. Jupiter-Uranus "
            "nature; justice, mysticism. Important in southern-hemisphere traditions "
            "and Dravidian astrology. High ecliptic latitude means few planets conjoin it."
        ),
    },
    {
        "name_latin": "Mimosa",
        "name_sanskrit": "Chitra region",
        "bayer": "Beta Crucis",
        "constellation": "Crux (Southern Cross)",
        "magnitude": 1.25,
        "j2000_longitude_tropical": 202.65,
        "j2000_latitude": -55.26,
        "nature": "benefic",
        "classical_significance": (
            "Second star of Southern Cross; very southern latitude. Near Spica/Chitra "
            "in longitude. Jupiter nature; good fortune and spiritual aspiration."
        ),
    },
    # -----------------------------------------------------------------------
    # LIBRA / SCORPIO SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Arcturus",
        "name_sanskrit": "Swati / Nishtya",
        "bayer": "Alpha Bootis",
        "constellation": "Bootes",
        "magnitude": -0.05,
        "j2000_longitude_tropical": 213.97,
        "j2000_latitude": 30.72,
        "nature": "benefic",
        "classical_significance": (
            "Fourth brightest star; very high ecliptic latitude (+31°). Jupiter-Mars "
            "nature. Jyotish: Swati nakshatra — independence, moving freely like the "
            "wind, commerce, trade. High latitude means it appears far from the ecliptic; "
            "conjunctions are rare but powerful for planet at same longitude."
        ),
    },
    {
        "name_latin": "Toliman",
        "name_sanskrit": "Vishakha / Agastya neighbor",
        "bayer": "Alpha Centauri (Rigil Kentaurus)",
        "constellation": "Centaurus",
        "magnitude": -0.27,
        "j2000_longitude_tropical": 210.23,
        "j2000_latitude": -42.56,
        "nature": "benefic",
        "classical_significance": (
            "Closest star system to the Sun (4.37 ly); third brightest star. Very "
            "southern. Venus-Jupiter nature; good fortune, philosophical wisdom. "
            "Important in South Indian and Tamil Jyotish. Associated with teaching "
            "and the guru-shishya relationship."
        ),
    },
    {
        "name_latin": "Zubenelgenubi",
        "name_sanskrit": "Vishakha (southern claw)",
        "bayer": "Alpha Librae",
        "constellation": "Libra",
        "magnitude": 2.75,
        "j2000_longitude_tropical": 224.69,
        "j2000_latitude": 0.67,
        "nature": "malefic",
        "classical_significance": (
            "Southern Claw (originally Scorpion's claw before Libra was defined). "
            "Saturn-Mars nature; misfortune, criminal tendencies when afflicted. "
            "Jyotish: Vishakha nakshatra (tri-spoke / radha); ambition, branching paths."
        ),
    },
    {
        "name_latin": "Graffias",
        "name_sanskrit": "Anuradha",
        "bayer": "Beta Scorpii",
        "constellation": "Scorpius",
        "magnitude": 2.62,
        "j2000_longitude_tropical": 222.29,
        "j2000_latitude": 1.59,
        "nature": "malefic",
        "classical_significance": (
            "Head of the Scorpion. Mars-Saturn nature; Jyotish: associated with "
            "Anuradha nakshatra — devotion, friendship, organizational ability."
        ),
    },
    {
        "name_latin": "Antares",
        "name_sanskrit": "Jyeshtha",
        "bayer": "Alpha Scorpii",
        "constellation": "Scorpius",
        "magnitude": 1.06,
        "j2000_longitude_tropical": 249.56,
        "j2000_latitude": -4.57,
        "nature": "malefic",
        "classical_significance": (
            "Heart of the Scorpion; Royal Star of the West; one of the four Royal "
            "Stars of Persia. Rival of Mars (Anti-Ares). Mars-Jupiter nature. "
            "Jyotish: Jyeshtha nakshatra — the eldest, most powerful; authority, "
            "occult power, chieftainship. Conjunctions: extreme success OR extreme "
            "downfall depending on integrity."
        ),
    },
    # -----------------------------------------------------------------------
    # SAGITTARIUS SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Lesath",
        "name_sanskrit": "Mula (tip of stinger)",
        "bayer": "Upsilon Scorpii",
        "constellation": "Scorpius",
        "magnitude": 2.69,
        "j2000_longitude_tropical": 258.07,
        "j2000_latitude": -15.35,
        "nature": "malefic",
        "classical_significance": (
            "Tip of the Scorpion's stinger; Mars-Mercury nature. Dangerous and "
            "violent energy. Jyotish: Mula nakshatra — root-shaking events, "
            "destruction for regeneration, Nirriti (goddess of dissolution)."
        ),
    },
    {
        "name_latin": "Shaula",
        "name_sanskrit": "Mula nakshatra",
        "bayer": "Lambda Scorpii",
        "constellation": "Scorpius",
        "magnitude": 1.63,
        "j2000_longitude_tropical": 249.07,
        "j2000_latitude": -13.79,
        "nature": "malefic",
        "classical_significance": (
            "Raised tail / sting of Scorpion; near Antares. Mars nature. "
            "One of the most southern principal stars of the Scorpion. "
            "Jyotish: often grouped with Mula due to proximity."
        ),
    },
    {
        "name_latin": "Nunki",
        "name_sanskrit": "Purva Ashadha region",
        "bayer": "Sigma Sagittarii",
        "constellation": "Sagittarius",
        "magnitude": 2.05,
        "j2000_longitude_tropical": 282.34,
        "j2000_latitude": -6.84,
        "nature": "benefic",
        "classical_significance": (
            "Vow of the Sea (Babylonian); Jupiter-Mercury nature. Honesty, "
            "directness. Jyotish: Purva Ashadha nakshatra — invincible victory, "
            "purification, Apas (goddess of waters)."
        ),
    },
    # -----------------------------------------------------------------------
    # CAPRICORN SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Vega",
        "name_sanskrit": "Abhijit",
        "bayer": "Alpha Lyrae",
        "constellation": "Lyra",
        "magnitude": 0.03,
        "j2000_longitude_tropical": 284.52,
        "j2000_latitude": 61.72,
        "nature": "benefic",
        "classical_significance": (
            "Vega corresponds to the nakshatra Abhijit — the 28th (sometimes "
            "omitted) nakshatra; highly auspicious, the victorious one. "
            "Mercury-Venus nature. Future pole star (~13,000 years from now). "
            "Abhijit muhurta (midday) is named after this star. Conjunctions "
            "bring fame and powerful victories."
        ),
    },
    {
        "name_latin": "Altair",
        "name_sanskrit": "Shravana",
        "bayer": "Alpha Aquilae",
        "constellation": "Aquila",
        "magnitude": 0.77,
        "j2000_longitude_tropical": 301.49,
        "j2000_latitude": 29.30,
        "nature": "benefic",
        "classical_significance": (
            "The Flying Eagle; Jupiter-Mars nature. Jyotish: Shravana nakshatra "
            "— listening, learning, Vishnu's nakshatra. Three bright stars form "
            "Vishnu's three strides (trivikrama). Conjunctions favor education, "
            "travel, and spiritual receptivity."
        ),
    },
    # -----------------------------------------------------------------------
    # AQUARIUS SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Deneb",
        "name_sanskrit": "Dhanishtha region",
        "bayer": "Alpha Cygni",
        "constellation": "Cygnus",
        "magnitude": 1.25,
        "j2000_longitude_tropical": 324.93,
        "j2000_latitude": 59.89,
        "nature": "benefic",
        "classical_significance": (
            "Tail of the Swan / top of the Northern Cross. Very high ecliptic "
            "latitude (+60°). Jupiter-Venus nature; creative and artistic nature. "
            "Jyotish: near Dhanishtha nakshatra — abundance, music, Vasus."
        ),
    },
    {
        "name_latin": "Sualocin",
        "name_sanskrit": "Dhanishtha",
        "bayer": "Alpha Delphini",
        "constellation": "Delphinus",
        "magnitude": 3.77,
        "j2000_longitude_tropical": 323.56,
        "j2000_latitude": 29.93,
        "nature": "benefic",
        "classical_significance": (
            "The Dolphin star; Saturn-Mars nature, but benefic in spiritual "
            "traditions. Jyotish: Dhanishtha nakshatra — drum of the Vasus, "
            "abundance, musical talent, charitable disposition."
        ),
    },
    {
        "name_latin": "Sadalsuud",
        "name_sanskrit": "Shatabhisha / Varuna",
        "bayer": "Beta Aquarii",
        "constellation": "Aquarius",
        "magnitude": 2.87,
        "j2000_longitude_tropical": 343.44,
        "j2000_latitude": -9.24,
        "nature": "neutral",
        "classical_significance": (
            "Luckiest of the Lucky; Saturn-Mercury nature. Heliacal rising in "
            "spring marked beneficial seasonal rains in ancient Babylon. "
            "Jyotish: Shatabhisha nakshatra — hundred healers, Varuna's star, "
            "healing and occult knowledge."
        ),
    },
    {
        "name_latin": "Sadalmelik",
        "name_sanskrit": "Purva Bhadrapada",
        "bayer": "Alpha Aquarii",
        "constellation": "Aquarius",
        "magnitude": 2.95,
        "j2000_longitude_tropical": 333.38,
        "j2000_latitude": -11.20,
        "nature": "neutral",
        "classical_significance": (
            "Lucky Stars of the King; Saturn-Mercury nature. Jyotish: "
            "Purva Bhadrapada nakshatra — the front blessed feet, Ajaikapat "
            "(one-footed goat), fire of purification."
        ),
    },
    # -----------------------------------------------------------------------
    # PISCES SECTOR
    # -----------------------------------------------------------------------
    {
        "name_latin": "Fomalhaut",
        "name_sanskrit": "Revati / Matsya Mukha",
        "bayer": "Alpha Piscis Austrini",
        "constellation": "Piscis Austrinus",
        "magnitude": 1.16,
        "j2000_longitude_tropical": 333.90,
        "j2000_latitude": -21.14,
        "nature": "benefic",
        "classical_significance": (
            "Royal Star of the South; one of the four Royal Stars of Persia. "
            "Mouth of the Southern Fish. Venus-Mercury nature. Associated with "
            "idealism, spirituality, and magic — but dissolution if corrupted. "
            "Jyotish: near Revati nakshatra; associated with journeys, the final "
            "steps of the zodiac, and liberation (moksha)."
        ),
    },
    {
        "name_latin": "Scheat",
        "name_sanskrit": "Purva Bhadrapada / Uttara Bhadrapada junction",
        "bayer": "Beta Pegasi",
        "constellation": "Pegasus",
        "magnitude": 2.44,
        "j2000_longitude_tropical": 349.10,
        "j2000_latitude": 31.00,
        "nature": "malefic",
        "classical_significance": (
            "The Leg of Pegasus; Saturn-Mercury nature. Associated with "
            "drowning, imprisonment, extreme misfortune. Jyotish: near "
            "Uttara Bhadrapada nakshatra — Ahir Budhnya (serpent of the deep)."
        ),
    },
    {
        "name_latin": "Zeta Piscium",
        "name_sanskrit": "Revati ayanamsha reference",
        "bayer": "Zeta Piscium",
        "constellation": "Pisces",
        "magnitude": 5.21,
        "j2000_longitude_tropical": 359.50,
        "j2000_latitude": -0.14,
        "nature": "neutral",
        "classical_significance": (
            "THE defining reference star for the Revati ayanamsha. The Revati "
            "ayanamsha places Zeta Piscium exactly at 0° Aries sidereal. "
            "Jyotish: Revati nakshatra — the wealthy one, Pushan (nourisher), "
            "end of the zodiac and gateway to liberation."
        ),
    },
    # -----------------------------------------------------------------------
    # ADDITIONAL IMPORTANT STARS
    # -----------------------------------------------------------------------
    {
        "name_latin": "Pleiades (Alcyone group)",
        "name_sanskrit": "Krittika",
        "bayer": "Eta Tauri (central)",
        "constellation": "Taurus",
        "magnitude": 2.87,
        "j2000_longitude_tropical": 60.00,
        "j2000_latitude": 4.03,
        "nature": "malefic",
        "classical_significance": (
            "The Weeping Sisters; Krittika nakshatra stars. Moon's exaltation "
            "nakshatra. The six visible stars represent the six Krittikas who "
            "raised Skanda (Kartikeya). Sharp, fiery, cutting in nature."
        ),
    },
    {
        "name_latin": "Alhena",
        "name_sanskrit": "Mrigashira / Ardra region",
        "bayer": "Gamma Geminorum",
        "constellation": "Gemini",
        "magnitude": 1.93,
        "j2000_longitude_tropical": 90.09,
        "j2000_latitude": -6.68,
        "nature": "benefic",
        "classical_significance": (
            "The Brand on the Neck of the Camel; Mercury-Venus nature. "
            "Artistry, eloquence, and grace. Jyotish: transition region between "
            "Mrigashira and Ardra nakshatras."
        ),
    },
    {
        "name_latin": "Wezen",
        "name_sanskrit": "Punarvasu region",
        "bayer": "Delta Canis Majoris",
        "constellation": "Canis Major",
        "magnitude": 1.83,
        "j2000_longitude_tropical": 107.11,
        "j2000_latitude": -27.38,
        "nature": "neutral",
        "classical_significance": (
            "The Weight; in Canis Major. Mars-Saturn nature. "
            "Endurance and perseverance under burden."
        ),
    },
    {
        "name_latin": "Dubhe",
        "name_sanskrit": "Pushya region (high north)",
        "bayer": "Alpha Ursae Majoris",
        "constellation": "Ursa Major",
        "magnitude": 1.79,
        "j2000_longitude_tropical": 194.91,
        "j2000_latitude": 50.12,
        "nature": "malefic",
        "classical_significance": (
            "Back of the Great Bear; Mars-Saturn nature. Extremes of character, "
            "destructiveness. One of the pointer stars to Polaris. Very high "
            "ecliptic latitude."
        ),
    },
    {
        "name_latin": "Acubens",
        "name_sanskrit": "Ashlesha",
        "bayer": "Alpha Cancri",
        "constellation": "Cancer",
        "magnitude": 4.26,
        "j2000_longitude_tropical": 133.32,
        "j2000_latitude": 5.35,
        "nature": "malefic",
        "classical_significance": (
            "The Claw of the Crab; Saturn-Mercury nature. Deception, "
            "poison. Jyotish: Ashlesha nakshatra — the embracing/clinging, "
            "serpent energy, Naga deities."
        ),
    },
    {
        "name_latin": "Zosma",
        "name_sanskrit": "Purva Phalguni",
        "bayer": "Delta Leonis",
        "constellation": "Leo",
        "magnitude": 2.56,
        "j2000_longitude_tropical": 173.26,
        "j2000_latitude": 13.96,
        "nature": "malefic",
        "classical_significance": (
            "The Girdle / Hip of the Lion; Saturn-Venus nature. Introspection, "
            "victimhood, suffering. Jyotish: Purva Phalguni nakshatra — "
            "relaxation, pleasure, Bhaga (god of delight)."
        ),
    },
    {
        "name_latin": "Labrum",
        "name_sanskrit": "Hasta",
        "bayer": "Delta Crateris",
        "constellation": "Crater",
        "magnitude": 3.56,
        "j2000_longitude_tropical": 191.68,
        "j2000_latitude": -18.19,
        "nature": "benefic",
        "classical_significance": (
            "The Cup; Venus-Mercury nature. Psychic sensitivity, the Holy Grail. "
            "Jyotish: Hasta nakshatra region — the hand, craftsmanship, Savitar."
        ),
    },
    {
        "name_latin": "Vindemiatrix",
        "name_sanskrit": "Hasta / Chitra junction",
        "bayer": "Epsilon Virginis",
        "constellation": "Virgo",
        "magnitude": 2.83,
        "j2000_longitude_tropical": 196.20,
        "j2000_latitude": 15.94,
        "nature": "malefic",
        "classical_significance": (
            "The Grape Gatherer / Widow Maker; Saturn nature. Loss of spouse, "
            "or separations. Jyotish: transition from Hasta to Chitra."
        ),
    },
    {
        "name_latin": "Zubeneschamali",
        "name_sanskrit": "Vishakha (northern claw)",
        "bayer": "Beta Librae",
        "constellation": "Libra",
        "magnitude": 2.61,
        "j2000_longitude_tropical": 231.76,
        "j2000_latitude": 8.87,
        "nature": "benefic",
        "classical_significance": (
            "Northern Scale / Northern Claw; Jupiter-Mercury nature. The only "
            "star described as green. Intelligence, idealism, ambition that "
            "brings honor. Jyotish: Vishakha nakshatra."
        ),
    },
    {
        "name_latin": "Han",
        "name_sanskrit": "Anuradha / Jyeshtha junction",
        "bayer": "Zeta Ophiuchi",
        "constellation": "Ophiuchus",
        "magnitude": 2.54,
        "j2000_longitude_tropical": 237.79,
        "j2000_latitude": 23.56,
        "nature": "malefic",
        "classical_significance": (
            "Knee of the Serpent Bearer; Saturn-Venus nature. Occult interests, "
            "danger from medicine or poison. Jyotish: junction of Anuradha "
            "and Jyeshtha nakshatras."
        ),
    },
    {
        "name_latin": "Rasalhague",
        "name_sanskrit": "Jyeshtha / Mula region",
        "bayer": "Alpha Ophiuchi",
        "constellation": "Ophiuchus",
        "magnitude": 2.08,
        "j2000_longitude_tropical": 261.85,
        "j2000_latitude": 35.89,
        "nature": "malefic",
        "classical_significance": (
            "Head of the Serpent Bearer; Saturn-Venus nature. Healing ability "
            "but also addiction risks. Jyotish: near the Galactic Center region; "
            "deep knowledge, healing or toxicity themes."
        ),
    },
    {
        "name_latin": "Galactic Center",
        "name_sanskrit": "Vishnunabhi",
        "bayer": "Sagittarius A* direction",
        "constellation": "Sagittarius",
        "magnitude": -26.0,  # not a visible star per se; direction marker
        "j2000_longitude_tropical": 266.86,
        "j2000_latitude": -5.60,
        "nature": "neutral",
        "classical_significance": (
            "The center of the Milky Way galaxy; called Vishnunabhi (navel of "
            "Vishnu) in Jyotish. Some traditions place the origin of the sidereal "
            "zodiac here. Planets conjunct the Galactic Center (≈27° Sagittarius "
            "sidereal in Lahiri) are said to receive extraordinary cosmic imprints."
        ),
    },
    {
        "name_latin": "Kaus Australis",
        "name_sanskrit": "Purva Ashadha",
        "bayer": "Epsilon Sagittarii",
        "constellation": "Sagittarius",
        "magnitude": 1.79,
        "j2000_longitude_tropical": 275.15,
        "j2000_latitude": -6.44,
        "nature": "benefic",
        "classical_significance": (
            "Southern part of the Archer's bow; Jupiter-Mars nature. Optimism, "
            "generosity, cheerfulness. Jyotish: Purva Ashadha nakshatra — "
            "undefeated, invincible, Apas."
        ),
    },
    {
        "name_latin": "Peacock",
        "name_sanskrit": "Purva Ashadha / Uttara Ashadha border",
        "bayer": "Alpha Pavonis",
        "constellation": "Pavo",
        "magnitude": 1.94,
        "j2000_longitude_tropical": 283.86,
        "j2000_latitude": -20.40,
        "nature": "benefic",
        "classical_significance": (
            "The Peacock star (named officially 'Peacock'). Saturn-Venus nature "
            "— but associated with pride, beauty, and display. Jyotish: The "
            "peacock is Kartikeya's vehicle; associated with divine grace."
        ),
    },
    {
        "name_latin": "Nashira",
        "name_sanskrit": "Shravana / Dhanishtha region",
        "bayer": "Gamma Capricorni",
        "constellation": "Capricornus",
        "magnitude": 3.68,
        "j2000_longitude_tropical": 321.84,
        "j2000_latitude": -2.67,
        "nature": "benefic",
        "classical_significance": (
            "The Fortunate One / Bringing Good Tidings; Saturn-Jupiter nature. "
            "Associated with overcoming enemies through higher principle. "
            "Jyotish: transition region between Shravana and Dhanishtha."
        ),
    },
    {
        "name_latin": "Enif",
        "name_sanskrit": "Purva Bhadrapada",
        "bayer": "Epsilon Pegasi",
        "constellation": "Pegasus",
        "magnitude": 2.38,
        "j2000_longitude_tropical": 341.98,
        "j2000_latitude": 19.54,
        "nature": "malefic",
        "classical_significance": (
            "Nose of Pegasus; Saturn-Mars nature. Impulsive and rash when "
            "planets conjoin. Jyotish: Purva Bhadrapada nakshatra, the fiery "
            "front feet."
        ),
    },
]

# ---------------------------------------------------------------------------
# G32 — LOOKUP FUNCTIONS
# ---------------------------------------------------------------------------

_REQUIRED_STAR_KEYS = {
    "name_latin",
    "name_sanskrit",
    "constellation",
    "magnitude",
    "j2000_longitude_tropical",
    "j2000_latitude",
    "nature",
    "classical_significance",
}


def get_star_longitude(star_name: str, ayanamsha_deg: float) -> float:
    """
    Return the sidereal longitude of a fixed star for a given ayanamsha value.

    Sidereal longitude = (tropical_longitude - ayanamsha_deg) mod 360.

    Args:
        star_name: Case-insensitive partial match against name_latin or name_sanskrit.
        ayanamsha_deg: Ayanamsha in decimal degrees (e.g. 23.86 for Lahiri ~2000 CE).

    Returns:
        Sidereal longitude in degrees [0, 360).

    Raises:
        KeyError: If no star matching star_name is found.
    """
    name_lower = star_name.lower()
    for star in FIXED_STARS:
        if name_lower in star["name_latin"].lower() or name_lower in star["name_sanskrit"].lower():
            return (star["j2000_longitude_tropical"] - ayanamsha_deg) % 360
    raise KeyError(f"Star not found in catalog: {star_name!r}")


def get_star_by_name(star_name: str) -> dict:
    """
    Return the full catalog entry for a star by name (case-insensitive partial match).

    Args:
        star_name: Partial case-insensitive match against name_latin or name_sanskrit.

    Returns:
        The matching star dict.

    Raises:
        KeyError: If no match is found.
    """
    name_lower = star_name.lower()
    for star in FIXED_STARS:
        if name_lower in star["name_latin"].lower() or name_lower in star["name_sanskrit"].lower():
            return star
    raise KeyError(f"Star not found: {star_name!r}")


def get_stars_near_longitude(longitude: float, orb_degrees: float = 1.0) -> list[dict]:
    """
    Return all stars whose tropical longitude is within orb_degrees of the given longitude.

    Handles wrap-around at 0°/360°.

    Args:
        longitude: Reference tropical longitude in degrees [0, 360).
        orb_degrees: Search radius in degrees (default 1.0).

    Returns:
        List of matching star dicts (may be empty).
    """
    results = []
    for star in FIXED_STARS:
        diff = abs(star["j2000_longitude_tropical"] - longitude)
        # Handle wrap-around
        diff = min(diff, 360.0 - diff)
        if diff <= orb_degrees:
            results.append(star)
    return results


def get_stars_by_nature(nature: str) -> list[dict]:
    """
    Return all stars of a given nature ('benefic', 'malefic', 'neutral').

    Args:
        nature: One of 'benefic', 'malefic', 'neutral'.

    Returns:
        List of matching star dicts.
    """
    return [s for s in FIXED_STARS if s["nature"].lower() == nature.lower()]


def get_stars_in_sign(sign_index: int) -> list[dict]:
    """
    Return all stars whose tropical longitude falls in the given sign (0=Aries … 11=Pisces).

    Args:
        sign_index: Integer 0–11.

    Returns:
        List of star dicts whose j2000_longitude_tropical is in [sign_index*30, (sign_index+1)*30).
    """
    lo = sign_index * 30.0
    hi = lo + 30.0
    return [s for s in FIXED_STARS if lo <= s["j2000_longitude_tropical"] < hi]
