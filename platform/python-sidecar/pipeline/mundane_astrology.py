"""
mundane_astrology.py — G48 Mundane Astrology Reference Module
=============================================================
Classical sources: Mundane astrology tradition; Jupiter-Saturn conjunction
cycles (Vishnu/Brahma cycles); Saptarishi cycle.

Jupiter-Saturn conjunctions occur approximately every 20 years and mark
major world-historical transition points. The "Great Mutation" (shift from
one triplicity to another) occurs roughly every 200 years.

canonical_id: G48
stream: A
session: G48-G49-G50-S1 [BUILD-ORCH-A-15]
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. JUPITER-SATURN CONJUNCTIONS 1950-2100
# ---------------------------------------------------------------------------
# Approximately every 19.86 years. Each conjunction marks a new Vishnu cycle.
# The "Great Mutation" (change of triplicity/element) occurs every ~200 years.
# 2020 marked the "Great Air Mutation" after ~800 years of earth conjunctions.

JUPITER_SATURN_CONJUNCTIONS: list[dict] = [
    {
        "date_approx": "1940-08-08",
        "sign": "aries",
        "element": "fire",
        "longitude_approx": 14.0,
        "era_name": "Mesha Yuga junction — fire triplicity",
        "notes": "Last fire-element conjunction before the long earth series; WWII pivot era",
    },
    {
        "date_approx": "1961-02-18",
        "sign": "capricorn",
        "element": "earth",
        "longitude_approx": 25.0,
        "era_name": "Makara Yuga junction — earth triplicity",
        "notes": "Cold War peak, space race era, post-colonial realignment; earth-element series mid-cycle",
    },
    {
        "date_approx": "1980-12-31",
        "sign": "libra",
        "element": "air",
        "longitude_approx": 9.0,
        "era_name": "Tula Yuga junction — air preview",
        "notes": (
            "Near-mutation: first conjunction in an air sign since 1186 CE; "
            "reverted to earth in the next cycle; Reaganomics / Thatcher era"
        ),
    },
    {
        "date_approx": "2000-05-28",
        "sign": "taurus",
        "element": "earth",
        "longitude_approx": 22.0,
        "era_name": "Vrishabha Yuga junction — earth triplicity",
        "notes": (
            "Great Conjunction in Taurus; dot-com peak; final earth-element "
            "conjunction before the 2020 Great Air Mutation"
        ),
    },
    {
        "date_approx": "2020-12-21",
        "sign": "aquarius",
        "element": "air",
        "longitude_approx": 0.5,
        "era_name": "Kumbha Yuga junction — The Great Air Mutation",
        "notes": (
            "Great Mutation: shift from earth to air triplicity after ~800 years. "
            "Winter solstice alignment. COVID-19 pivot year, digital acceleration era. "
            "First true air-element conjunction since 1226 CE."
        ),
    },
    {
        "date_approx": "2040-10-31",
        "sign": "libra",
        "element": "air",
        "longitude_approx": 17.5,
        "era_name": "Tula Yuga junction — air triplicity continuation",
        "notes": (
            "Second consecutive air conjunction; confirms Great Air Mutation series. "
            "Libra is Venus-ruled — arts, diplomacy, balance emphasis."
        ),
    },
    {
        "date_approx": "2060-04-07",
        "sign": "gemini",
        "element": "air",
        "longitude_approx": 19.5,
        "era_name": "Mithuna Yuga junction — air triplicity",
        "notes": (
            "Third air conjunction; Mercury-ruled Gemini emphasis on communication, "
            "technology, trade networks."
        ),
    },
    {
        "date_approx": "2080-03-15",
        "sign": "aquarius",
        "element": "air",
        "longitude_approx": 12.0,
        "era_name": "Kumbha Yuga junction — air triplicity",
        "notes": (
            "Return to Aquarius after 60 years; Saturn-ruled Aquarius; "
            "fourth consecutive air conjunction deepens the mutation."
        ),
    },
    {
        "date_approx": "2100-09-18",
        "sign": "libra",
        "element": "air",
        "longitude_approx": 25.0,
        "era_name": "Tula Yuga junction — air triplicity",
        "notes": "Fifth consecutive air conjunction; Venus-ruled; late 22nd century social order.",
    },
]

# ---------------------------------------------------------------------------
# 2. SLOW-PLANET ALIGNMENTS 1950-2100
# ---------------------------------------------------------------------------
# Outer-planet alignments with mundane significance.
# Saturn-Neptune: idealism vs structure; Saturn-Uranus: reform vs tradition;
# Saturn-Pluto: power restructuring; Uranus-Neptune: generational vision shift;
# Uranus-Pluto: revolutionary upheaval.

SLOW_PLANET_ALIGNMENTS: list[dict] = [
    # --- Saturn-Pluto ---
    {
        "planets": ["saturn", "pluto"],
        "date_approx": "1947-08-11",
        "sign": "leo",
        "type": "conjunction",
        "notes": "Cold War beginning, partition of India, post-WWII world order",
    },
    {
        "planets": ["saturn", "pluto"],
        "date_approx": "1965-06-22",
        "sign": "pisces",
        "type": "opposition",
        "notes": "Vietnam escalation, cultural revolution era",
    },
    {
        "planets": ["saturn", "pluto"],
        "date_approx": "1982-11-08",
        "sign": "libra-aries",
        "type": "square",
        "notes": "Falklands War, Cold War tension peak, global recession",
    },
    {
        "planets": ["saturn", "pluto"],
        "date_approx": "2001-11-02",
        "sign": "sagittarius-gemini",
        "type": "opposition",
        "notes": "9/11 aftermath, War on Terror launch, world order restructuring",
    },
    {
        "planets": ["saturn", "pluto"],
        "date_approx": "2020-01-12",
        "sign": "capricorn",
        "type": "conjunction",
        "notes": "COVID-19 onset, global power restructuring, institutional dismantling",
    },
    {
        "planets": ["saturn", "pluto"],
        "date_approx": "2053-05-10",
        "sign": "pisces",
        "type": "conjunction",
        "notes": "Projected next Saturn-Pluto conjunction; generational power reset",
    },
    # --- Saturn-Uranus ---
    {
        "planets": ["saturn", "uranus"],
        "date_approx": "1988-03-01",
        "sign": "sagittarius",
        "type": "conjunction",
        "notes": "Glasnost/perestroika era, Wall coming down imminently, reform vs structure tension",
    },
    {
        "planets": ["saturn", "uranus"],
        "date_approx": "2021-02-17",
        "sign": "aquarius-taurus",
        "type": "square",
        "notes": "Post-COVID institutional reform vs tradition clash; crypto surge; political polarization",
    },
    {
        "planets": ["saturn", "uranus"],
        "date_approx": "2032-07-14",
        "sign": "gemini",
        "type": "conjunction",
        "notes": "Next Saturn-Uranus conjunction; technology-governance nexus",
    },
    # --- Saturn-Neptune ---
    {
        "planets": ["saturn", "neptune"],
        "date_approx": "1952-11-21",
        "sign": "libra",
        "type": "conjunction",
        "notes": "McCarthyism, ideological battle between East and West solidified",
    },
    {
        "planets": ["saturn", "neptune"],
        "date_approx": "1989-03-03",
        "sign": "capricorn",
        "type": "conjunction",
        "notes": "Fall of Berlin Wall, dissolution of Soviet ideals; illusion-reality confrontation",
    },
    {
        "planets": ["saturn", "neptune"],
        "date_approx": "2025-02-20",
        "sign": "aries",
        "type": "conjunction",
        "notes": "Next Saturn-Neptune conjunction; spiritual-material reconciliation; AI ethics crossroads",
    },
    # --- Uranus-Pluto ---
    {
        "planets": ["uranus", "pluto"],
        "date_approx": "1966-10-09",
        "sign": "virgo",
        "type": "conjunction",
        "notes": "1960s revolution: civil rights, counterculture, Vietnam protests, sexual revolution",
    },
    {
        "planets": ["uranus", "pluto"],
        "date_approx": "2012-06-24",
        "sign": "aries-capricorn",
        "type": "square",
        "notes": "Arab Spring, Occupy movement, digital surveillance state, global unrest",
    },
    # --- Uranus-Neptune ---
    {
        "planets": ["uranus", "neptune"],
        "date_approx": "1993-02-02",
        "sign": "capricorn",
        "type": "conjunction",
        "notes": "End of Cold War era, internet age birth, globalization wave, new world order",
    },
    {
        "planets": ["uranus", "neptune"],
        "date_approx": "2165-04-01",
        "sign": "aquarius",
        "type": "conjunction",
        "notes": "Next projected Uranus-Neptune conjunction; deep generational vision shift (22nd century)",
    },
    # --- Jupiter-Uranus ---
    {
        "planets": ["jupiter", "uranus"],
        "date_approx": "1969-03-11",
        "sign": "libra",
        "type": "conjunction",
        "notes": "Moon landing year; sudden expansion of human horizon; liberation movements",
    },
    {
        "planets": ["jupiter", "uranus"],
        "date_approx": "2010-06-08",
        "sign": "aries",
        "type": "conjunction",
        "notes": "Arab Spring precursor; social media revolution trigger; innovative breakthroughs",
    },
    {
        "planets": ["jupiter", "uranus"],
        "date_approx": "2024-04-20",
        "sign": "taurus",
        "type": "conjunction",
        "notes": "AI breakthrough era, global financial restructuring signals, earth-sign innovation",
    },
    {
        "planets": ["jupiter", "uranus"],
        "date_approx": "2037-07-03",
        "sign": "scorpio",
        "type": "conjunction",
        "notes": "Projected next Jupiter-Uranus conjunction; transformation and hidden knowledge themes",
    },
    # --- Jupiter-Neptune ---
    {
        "planets": ["jupiter", "neptune"],
        "date_approx": "2022-04-12",
        "sign": "pisces",
        "type": "conjunction",
        "notes": "Spiritual peak in its own domain; idealism surge; crypto/NFT boom and bust; Ukraine war",
    },
]

# ---------------------------------------------------------------------------
# 3. HISTORICAL CORRELATIONS
# ---------------------------------------------------------------------------

HISTORICAL_CORRELATIONS: list[dict] = [
    {
        "event_type": "Empire formation",
        "date_range": "1226 CE",
        "planetary_trigger": "Jupiter-Saturn conjunction in Aquarius",
        "description": (
            "Mongol Empire under Genghis Khan at its height; last air-element "
            "Great Mutation before 2020; shift in world power and trade routes. "
            "Air mutations historically correlate with dissolution of established order."
        ),
    },
    {
        "event_type": "Religious reformation",
        "date_range": "1484-1504 CE",
        "planetary_trigger": "Jupiter-Saturn conjunction in Scorpio (1484) then fire signs",
        "description": (
            "Martin Luther's reformation era; Mughal Empire founding (1526); "
            "European Age of Exploration. Jupiter-Saturn in Scorpio preceded "
            "upheaval of religious authority."
        ),
    },
    {
        "event_type": "Scientific revolution",
        "date_range": "1603-1623 CE",
        "planetary_trigger": "Jupiter-Saturn conjunctions, Kepler nova year (1603)",
        "description": (
            "Fire-element mutation of 1603 (Sagittarius); Galileo's telescope; "
            "Kepler's laws; scientific method birth. Fire mutations correlate with "
            "intellectual and ideological revolutions."
        ),
    },
    {
        "event_type": "Industrial revolution onset",
        "date_range": "1762-1802 CE",
        "planetary_trigger": "Jupiter-Saturn conjunction in Capricorn (1782), earth series",
        "description": (
            "Watt's steam engine (1769), industrial capital formation, enclosure "
            "movements, French Revolution (1789). Earth-element Jupiter-Saturn "
            "series correlated with material-economic transformation."
        ),
    },
    {
        "event_type": "World War inflection",
        "date_range": "1940-1941",
        "planetary_trigger": "Jupiter-Saturn conjunction in Aries (1940), fire element",
        "description": (
            "WWII global conflagration at peak; Battle of Britain; Operation Barbarossa; "
            "Pearl Harbor. Fire element conjunctions correlate with armed conflict "
            "and assertion of power through force."
        ),
    },
    {
        "event_type": "Cold War restructuring",
        "date_range": "1961",
        "planetary_trigger": "Jupiter-Saturn conjunction in Capricorn (1961)",
        "description": (
            "Bay of Pigs invasion, Berlin Wall construction, Space Race acceleration, "
            "Non-Aligned Movement formation. Capricorn conjunction reinforced "
            "geopolitical structures and institutional authority."
        ),
    },
    {
        "event_type": "Reaganomics and neoliberal shift",
        "date_range": "1980-1981",
        "planetary_trigger": "Jupiter-Saturn conjunction in Libra (1980), air preview",
        "description": (
            "Reagan election, Thatcher economic policies, early personal computing, "
            "MTV culture, rise of financial markets. Air-sign preview conjunction "
            "preceded massive shift in economic ideology."
        ),
    },
    {
        "event_type": "Dot-com era and globalization peak",
        "date_range": "2000-2001",
        "planetary_trigger": "Jupiter-Saturn conjunction in Taurus (2000), earth element",
        "description": (
            "Y2K transition, dot-com peak and crash, 9/11 event one year later. "
            "Taurus-Capricorn earth energy: material excess followed by structural "
            "collapse and security reorientation."
        ),
    },
    {
        "event_type": "Great Air Mutation — digital civilization pivot",
        "date_range": "2020-2021",
        "planetary_trigger": "Jupiter-Saturn conjunction in Aquarius (2020-12-21) — Great Mutation",
        "description": (
            "COVID-19 pandemic reshapes civilization; mass digitization; remote work "
            "normalization; vaccine technology breakthrough; global power realignment. "
            "First air Great Mutation since 1226 CE marks end of material-industrial age "
            "and onset of information-network age per mundane tradition."
        ),
    },
    {
        "event_type": "Ancient: Maurya Empire consolidation",
        "date_range": "~305 BCE",
        "planetary_trigger": "Jupiter-Saturn conjunction, fire element series",
        "description": (
            "Chandragupta Maurya's empire consolidation post-Alexander's death. "
            "Fire-element conjunction series historically correlated with "
            "rise of new sovereign orders in South Asia."
        ),
    },
    {
        "event_type": "Gupta Empire golden age onset",
        "date_range": "~320 CE",
        "planetary_trigger": "Jupiter-Saturn in fire/earth signs",
        "description": (
            "Chandragupta I founded Gupta dynasty; classical Indian golden age in "
            "sciences, arts, mathematics. Conjunction energy in supportive element "
            "favored cultural flourishing."
        ),
    },
    {
        "event_type": "AI acceleration era",
        "date_range": "2040-2060",
        "planetary_trigger": "Jupiter-Saturn conjunctions in Libra (2040) and Gemini (2060)",
        "description": (
            "Projected: continued air-element conjunction series; Mercury-ruled "
            "Gemini (2060) especially favors algorithmic intelligence, "
            "communication technologies, and network-based governance."
        ),
    },
]

# ---------------------------------------------------------------------------
# 4. HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_conjunctions_by_sign(sign: str) -> list[dict]:
    """Return Jupiter-Saturn conjunctions in the given sign (case-insensitive)."""
    sign_lower = sign.lower()
    return [c for c in JUPITER_SATURN_CONJUNCTIONS if c["sign"].lower() == sign_lower]


def get_conjunctions_by_element(element: str) -> list[dict]:
    """Return Jupiter-Saturn conjunctions of the given element (fire/earth/air/water)."""
    element_lower = element.lower()
    return [c for c in JUPITER_SATURN_CONJUNCTIONS if c["element"].lower() == element_lower]


def get_next_conjunction_after(year: int) -> dict | None:
    """Return first Jupiter-Saturn conjunction with year > given year, or None."""
    for c in JUPITER_SATURN_CONJUNCTIONS:
        conj_year = int(c["date_approx"][:4])
        if conj_year > year:
            return c
    return None


# ---------------------------------------------------------------------------
# 5. MODULE ASSERTIONS
# ---------------------------------------------------------------------------

assert len(JUPITER_SATURN_CONJUNCTIONS) >= 8
assert all("date_approx" in c for c in JUPITER_SATURN_CONJUNCTIONS)
assert all("element" in c for c in JUPITER_SATURN_CONJUNCTIONS)
assert len(SLOW_PLANET_ALIGNMENTS) >= 20
assert len(HISTORICAL_CORRELATIONS) >= 10
