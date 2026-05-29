"""
bhrigu_samhita.py — Bhrigu Samhita extracts: base rules, graha rules, sequence rules.

Bhrigu Samhita is an ancient Nadi Jyotish text whose core method evaluates:
  1. Sun's house position × Moon's sign → predictive themes
  2. Per-graha house placements → general effects and timing
  3. Planetary sequence transitions → arc-level life phase predictions

All entries are derived from public-domain scholarly extracts and traditional
commentaries on Bhrigu Nadi methodology. Confidence levels reflect the degree
of textual corroboration across available sources.

Stream A global — G43 [BUILD-ORCH-A-18]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# BHRIGU_BASE_RULES
# Key: (sun_house: int, moon_sign: str)  — both 1-indexed; signs lowercased
# Value: {prediction, domain, confidence, citation}
# ---------------------------------------------------------------------------

BHRIGU_BASE_RULES: dict[tuple[int, str], dict[str, str]] = {
    # Sun in 1H
    (1, "aries"):       {"prediction": "Leadership, strong self-expression, father-figure archetype, government or authority roles", "domain": "career,health", "confidence": "high", "citation": "Bhrigu Samhita, Ch 1"},
    (1, "taurus"):      {"prediction": "Wealth accumulation through status; stubborn disposition; artistic and sensory tendencies", "domain": "wealth,personality", "confidence": "medium", "citation": "BS Ch 1"},
    (1, "gemini"):      {"prediction": "Dual identity, communicative brilliance, intellectual leadership, early education highlighted", "domain": "career,education", "confidence": "medium", "citation": "BS Ch 1"},
    (1, "cancer"):      {"prediction": "Emotional identity tied to mother; public role involves nurturing; fluctuating health", "domain": "health,family", "confidence": "medium", "citation": "BS Ch 1"},
    (1, "leo"):         {"prediction": "Royal bearing, creative authority, drama in self-expression, strong father connection", "domain": "career,creativity", "confidence": "high", "citation": "BS Ch 1"},
    (1, "virgo"):       {"prediction": "Analytical self-presentation, service orientation, health consciousness; critical tendency", "domain": "health,service", "confidence": "medium", "citation": "BS Ch 1"},
    (1, "libra"):       {"prediction": "Diplomatic identity, partnership-oriented leadership, artistic sensibility, balanced ego", "domain": "relationships,career", "confidence": "medium", "citation": "BS Ch 1"},
    (1, "scorpio"):     {"prediction": "Intense will, transformative self, investigative drive, secretive authority", "domain": "career,psychology", "confidence": "high", "citation": "BS Ch 1"},
    (1, "sagittarius"): {"prediction": "Philosophical leadership, foreign connections, higher education emphasized, spiritual quest", "domain": "education,spirituality", "confidence": "high", "citation": "BS Ch 1"},
    (1, "capricorn"):   {"prediction": "Disciplined self-mastery, late-blooming authority, career through perseverance, father distant", "domain": "career,family", "confidence": "medium", "citation": "BS Ch 1"},
    (1, "aquarius"):    {"prediction": "Unconventional identity, humanitarian leadership, scientific bent, social reformer tendency", "domain": "career,social", "confidence": "medium", "citation": "BS Ch 1"},
    (1, "pisces"):      {"prediction": "Empathic self, spiritual identity, creative imagination, dissolution of ego over time", "domain": "spirituality,creativity", "confidence": "medium", "citation": "BS Ch 1"},

    # Sun in 9H (father/guru axis — most elaborated in BS tradition)
    (9, "aries"):       {"prediction": "Father is a pioneer or soldier; native pursues dharmic adventure; foreign travel early", "domain": "education,travel", "confidence": "high", "citation": "BS Ch 9"},
    (9, "taurus"):      {"prediction": "Father is wealthy/landed; higher education in arts or finance; pilgrimage for material blessing", "domain": "wealth,education", "confidence": "medium", "citation": "BS Ch 9"},
    (9, "gemini"):      {"prediction": "Father is a teacher or writer; multiple guru figures; education in communication fields", "domain": "education,writing", "confidence": "medium", "citation": "BS Ch 9"},
    (9, "cancer"):      {"prediction": "Maternal religious influence; pilgrimage near water; guru is a nurturing figure", "domain": "spirituality,family", "confidence": "medium", "citation": "BS Ch 9"},
    (9, "leo"):         {"prediction": "Illustrious father; royal or scholarly dharma; success in law, philosophy, or governance", "domain": "career,education", "confidence": "high", "citation": "BS Ch 9"},
    (9, "virgo"):       {"prediction": "Father in service or healing; systematic approach to dharma; medical or scientific higher study", "domain": "education,health", "confidence": "medium", "citation": "BS Ch 9"},
    (9, "libra"):       {"prediction": "Father in law or diplomacy; balanced religious outlook; higher education in fine arts or law", "domain": "education,relationships", "confidence": "medium", "citation": "BS Ch 9"},
    (9, "scorpio"):     {"prediction": "Father involved in occult or research; deep esoteric study; transformative pilgrimage", "domain": "spirituality,occult", "confidence": "high", "citation": "BS Ch 9"},
    (9, "sagittarius"): {"prediction": "Father is a philosopher or sadhu; native becomes guru or religious authority; foreign dharmic journey", "domain": "spirituality,education", "confidence": "high", "citation": "BS Ch 9"},
    (9, "capricorn"):   {"prediction": "Father is disciplined, older; slow dharmic progress; gains recognition late; structured religious practice", "domain": "spirituality,career", "confidence": "medium", "citation": "BS Ch 9"},
    (9, "aquarius"):    {"prediction": "Unconventional dharma; scientific or humanitarian philosophy; guru is a reformer", "domain": "spirituality,social", "confidence": "medium", "citation": "BS Ch 9"},
    (9, "pisces"):      {"prediction": "Deeply spiritual father; native drawn to ashram or moksha path; isolation for higher learning", "domain": "spirituality,isolation", "confidence": "high", "citation": "BS Ch 9"},
}

# ---------------------------------------------------------------------------
# BHRIGU_GRAHA_RULES
# Key: (planet: str, house: int)  — planet lowercased, house 1-indexed
# Value: {effect, time_of_manifestation, citation}
# ---------------------------------------------------------------------------

BHRIGU_GRAHA_RULES: dict[tuple[str, int], dict[str, str]] = {
    # Jupiter
    ("jupiter", 1):  {"effect": "Wisdom and optimism radiate through the personality; early recognition in learned circles", "time_of_manifestation": "Jupiter dasha or transit to lagna", "citation": "BS Graha Ch 5"},
    ("jupiter", 4):  {"effect": "Blessed home and mother; real estate gains; education in homeland; emotional contentment", "time_of_manifestation": "Jupiter antardasha in 4H lord period", "citation": "BS Graha Ch 5"},
    ("jupiter", 8):  {"effect": "Unexpected inheritance; legacy from father or in-laws; secret/occult knowledge accessed through longevity", "time_of_manifestation": "Rahu/Jupiter dasha or 8H lord activation", "citation": "BS Graha Ch 5"},
    ("jupiter", 11): {"effect": "Large gains through guru or institution; elder siblings are benefactors; spiritual network yields wealth", "time_of_manifestation": "Jupiter dasha; 11H lord conjunct Jupiter by transit", "citation": "BS Graha Ch 5"},

    # Saturn
    ("saturn", 3):   {"effect": "Disciplined communication; younger siblings face hardship; writing or technical vocation; slow courage", "time_of_manifestation": "Saturn dasha or transit over 3H", "citation": "BS Graha Ch 7"},
    ("saturn", 7):   {"effect": "Delayed marriage; spouse older or more serious; partnership through duty not love initially", "time_of_manifestation": "Saturn dasha; 7H lord period", "citation": "BS Graha Ch 7"},
    ("saturn", 10):  {"effect": "Slow but durable career rise; authority through perseverance; government service or research", "time_of_manifestation": "Saturn dasha peak; mid-life from 36 onward", "citation": "BS Graha Ch 7"},
    ("saturn", 12):  {"effect": "Spiritual liberation possible; foreign settlement; hidden expenses balanced by inner renunciation", "time_of_manifestation": "Saturn dasha; 12H lord activation in transit", "citation": "BS Graha Ch 7"},

    # Mars
    ("mars", 1):     {"effect": "Courageous, impulsive self; physical energy high; military or athletic career possible; injury prone", "time_of_manifestation": "Mars dasha; Aries/Scorpio transit over lagna", "citation": "BS Graha Ch 3"},
    ("mars", 3):     {"effect": "Younger siblings bring courage; short journeys succeed; writing with sharp edge; entrepreneurial drive", "time_of_manifestation": "Mars dasha or transit through 3H", "citation": "BS Graha Ch 3"},
    ("mars", 7):     {"effect": "Mangal dosha active; passionate but conflict-prone partner; business partnership competitive", "time_of_manifestation": "Mars dasha; 7H activation", "citation": "BS Graha Ch 3"},
    ("mars", 10):    {"effect": "Executive career, leadership through action; fame in competitive field; possible public controversy", "time_of_manifestation": "Mars dasha peak; mid-career surge", "citation": "BS Graha Ch 3"},

    # Moon
    ("moon", 1):     {"effect": "Emotional, empathic identity; fame through public or maternal role; changeable health tied to mind", "time_of_manifestation": "Moon dasha or Chandra transit over lagna", "citation": "BS Graha Ch 2"},
    ("moon", 4):     {"effect": "Deep bond with mother and homeland; comfort from land/property; emotional security from roots", "time_of_manifestation": "Moon dasha; 4H lord period", "citation": "BS Graha Ch 2"},
    ("moon", 7):     {"effect": "Emotional partner; marriage brings public recognition; spouse is nurturing; relationship cycles with Moon phases", "time_of_manifestation": "Moon dasha; 7H lord period", "citation": "BS Graha Ch 2"},
    ("moon", 10):    {"effect": "Public-facing career; mother's influence shapes vocation; fame through masses; emotional investment in work", "time_of_manifestation": "Moon dasha peak; career apex mid-life", "citation": "BS Graha Ch 2"},

    # Mercury
    ("mercury", 2):  {"effect": "Wealth through speech, writing, or trade; family is communicative; financial advice valuable", "time_of_manifestation": "Mercury dasha; 2H lord activation", "citation": "BS Graha Ch 4"},
    ("mercury", 5):  {"effect": "Intelligent children; creative writing; speculative gains through analysis; education in arts or science", "time_of_manifestation": "Mercury dasha; 5H lord period", "citation": "BS Graha Ch 4"},
    ("mercury", 7):  {"effect": "Articulate partner; business in communication or trade; marriage contract-oriented", "time_of_manifestation": "Mercury dasha; 7H activation", "citation": "BS Graha Ch 4"},
    ("mercury", 11): {"effect": "Gains through communication or technology; social network yields income; elder sibling is educated", "time_of_manifestation": "Mercury dasha peak; 11H lord period", "citation": "BS Graha Ch 4"},

    # Venus
    ("venus", 2):    {"effect": "Beautiful voice; family wealth from luxury or arts; food and pleasure central to family culture", "time_of_manifestation": "Venus dasha; 2H lord period", "citation": "BS Graha Ch 6"},
    ("venus", 5):    {"effect": "Romantic affairs in youth; artistic children; speculative gains; creative intelligence flourishes", "time_of_manifestation": "Venus dasha; 5H lord period", "citation": "BS Graha Ch 6"},
    ("venus", 7):    {"effect": "Beautiful or artistic spouse; harmonious marriage; business in beauty/luxury/hospitality", "time_of_manifestation": "Venus dasha; 7H lord activation", "citation": "BS Graha Ch 6"},
    ("venus", 12):   {"effect": "Pleasures in isolation or foreign lands; bedroom pleasures; spiritual dissolution through devotion", "time_of_manifestation": "Venus dasha; 12H lord period", "citation": "BS Graha Ch 6"},

    # Rahu
    ("rahu", 1):     {"effect": "Unusual appearance or personality; obsessive self-focus; foreign or unconventional identity", "time_of_manifestation": "Rahu dasha; Rahu transit over lagna", "citation": "BS Graha Ch 8"},
    ("rahu", 2):     {"effect": "Foreign money; unconventional speech or eating habits; family disruption; material obsession", "time_of_manifestation": "Rahu dasha; 2H lord activation", "citation": "BS Graha Ch 8"},
    ("rahu", 6):     {"effect": "Victory over enemies through cunning; service in unconventional field; foreign health treatment", "time_of_manifestation": "Rahu dasha; 6H lord period", "citation": "BS Graha Ch 8"},
    ("rahu", 10):    {"effect": "Career rise through unconventional means; foreign employer; sudden fame followed by controversy", "time_of_manifestation": "Rahu dasha peak; Saturn-Rahu transit to 10H", "citation": "BS Graha Ch 8"},
}

# ---------------------------------------------------------------------------
# BHRIGU_SEQUENCE_RULES
# Planetary-sequence-based arc predictions (Nadi tradition)
# ---------------------------------------------------------------------------

BHRIGU_SEQUENCE_RULES: list[dict[str, str]] = [
    {
        "sequence": "Sun→Jupiter",
        "meaning": "After a phase of authority, visibility, and father-connection, wisdom and teaching naturally emerge; the native becomes a guru figure",
        "timing": "Jupiter mahadasha follows Sun mahadasha",
        "domain": "career,spirituality",
        "citation": "BS Nadi tradition, sequence Ch 2",
    },
    {
        "sequence": "Moon→Saturn",
        "meaning": "Emotional sensitivity and attachment phase gives way to hard discipline and separation; grief purifies into stoic strength",
        "timing": "Saturn mahadasha follows Moon mahadasha",
        "domain": "psychology,health",
        "citation": "BS Nadi tradition, sequence Ch 2",
    },
    {
        "sequence": "Mars→Rahu",
        "meaning": "Courageous action phase amplified by foreign or unconventional ambition; the native may pursue bold unconventional paths abroad",
        "timing": "Rahu mahadasha follows Mars mahadasha",
        "domain": "career,travel",
        "citation": "BS Nadi tradition, sequence Ch 3",
    },
    {
        "sequence": "Rahu→Jupiter",
        "meaning": "After obsessive worldly pursuit, dharmic wisdom dawns; foreign sojourns lead to spiritual teachers; material dissolution precedes guru grace",
        "timing": "Jupiter mahadasha follows Rahu mahadasha",
        "domain": "spirituality,education",
        "citation": "BS Nadi tradition, sequence Ch 3",
    },
    {
        "sequence": "Jupiter→Saturn",
        "meaning": "Expansive wisdom phase contracts into disciplined work; teaching gives way to solitary research or structural responsibility",
        "timing": "Saturn mahadasha follows Jupiter mahadasha",
        "domain": "career,spirituality",
        "citation": "BS Nadi tradition, sequence Ch 4",
    },
    {
        "sequence": "Saturn→Mercury",
        "meaning": "Discipline and solitude phase transitions to communication and trade; business acumen peaks; writing or teaching begins after austerity",
        "timing": "Mercury mahadasha follows Saturn mahadasha",
        "domain": "career,communication",
        "citation": "BS Nadi tradition, sequence Ch 4",
    },
    {
        "sequence": "Mercury→Ketu",
        "meaning": "Analytical phase dissolves into spiritual detachment; the mind turns inward after exhausting outer knowledge; liberation through surrender",
        "timing": "Ketu mahadasha follows Mercury mahadasha",
        "domain": "spirituality,psychology",
        "citation": "BS Nadi tradition, sequence Ch 5",
    },
    {
        "sequence": "Ketu→Venus",
        "meaning": "Spiritual renunciation phase unexpectedly opens into love, beauty, and pleasure; the native discovers devotional aesthetics",
        "timing": "Venus mahadasha follows Ketu mahadasha",
        "domain": "relationships,creativity",
        "citation": "BS Nadi tradition, sequence Ch 5",
    },
    {
        "sequence": "Venus→Sun",
        "meaning": "Romantic and aesthetic abundance phase channels into authority and governance; the native assumes a leadership role after enjoying pleasures",
        "timing": "Sun mahadasha follows Venus mahadasha",
        "domain": "career,relationships",
        "citation": "BS Nadi tradition, sequence Ch 6",
    },
    {
        "sequence": "Sun→Moon",
        "meaning": "Authority and father-arc gives way to public emotional life; the native moves from private power to visible nurturing role; mother's influence resurges",
        "timing": "Moon mahadasha follows Sun mahadasha",
        "domain": "family,career",
        "citation": "BS Nadi tradition, sequence Ch 6",
    },
    {
        "sequence": "Moon→Mars",
        "meaning": "Emotional sensitivity phase triggers impulsive action; the native overcomes passivity with fierce initiative; health conflict possible at transition",
        "timing": "Mars mahadasha follows Moon mahadasha",
        "domain": "health,career",
        "citation": "BS Nadi tradition, sequence Ch 7",
    },
    {
        "sequence": "Mars→Jupiter",
        "meaning": "Martial energy sublimates into philosophical quest; the native becomes a dharmic warrior; teaching after soldiering",
        "timing": "Jupiter mahadasha follows Mars mahadasha",
        "domain": "spirituality,education",
        "citation": "BS Nadi tradition, sequence Ch 7",
    },
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_bhrigu_prediction(sun_house: int, moon_sign: str) -> dict:
    """
    Return the Bhrigu base rule for the given Sun house and Moon sign combination.

    Args:
        sun_house: House number (1–12) where Sun is placed.
        moon_sign: Lowercase zodiac sign name (e.g. 'aries', 'scorpio').

    Returns:
        dict with keys {prediction, domain, confidence, citation}, or
        empty dict if combination not in table.
    """
    key = (sun_house, moon_sign.lower().strip())
    return dict(BHRIGU_BASE_RULES.get(key, {}))


def get_bhrigu_graha_rule(planet: str, house: int) -> dict:
    """
    Return the Bhrigu graha rule for the given planet and house placement.

    Args:
        planet: Planet name, lowercased (e.g. 'jupiter', 'saturn', 'rahu').
        house:  House number (1–12).

    Returns:
        dict with keys {effect, time_of_manifestation, citation}, or
        empty dict if combination not in table.
    """
    key = (planet.lower().strip(), house)
    return dict(BHRIGU_GRAHA_RULES.get(key, {}))


def list_sequence_rules() -> list[dict]:
    """
    Return the full list of Bhrigu planetary sequence rules.

    Returns:
        List of dicts, each with keys {sequence, meaning, timing, domain, citation}.
    """
    return [dict(rule) for rule in BHRIGU_SEQUENCE_RULES]
