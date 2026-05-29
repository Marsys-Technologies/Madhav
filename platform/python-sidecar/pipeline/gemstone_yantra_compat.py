"""
gemstone_yantra_compat.py — G34 Gemstone Reference, G35 Yantra Reference,
G36 Ashta Koota Compatibility tables.

Classical sources: Garuda Purana, Mani Mala, Brihat Parasara Hora Shastra,
Muhurta Chintamani, Vivaha Paddhati.

No DB interaction, no swisseph calls. Pure lookup tables + scoring functions.
"""

# ---------------------------------------------------------------------------
# G34 — GEMSTONE_REFERENCE
# 9 primary grahas with primary stone, substitutes, metal, finger, day,
# weight range (ratti), activation mantra, and classical citation.
# ---------------------------------------------------------------------------

GEMSTONE_REFERENCE = {
    "sun": {
        "primary_stone": "Ruby",
        "alternate_name": "Manikya",
        "substitute_stones": ["Red Spinel", "Red Zircon", "Red Garnet"],
        "metal": "gold",
        "finger": "ring",
        "day": "sunday",
        "weight_ratti_min": 3.0,
        "weight_ratti_max": 6.0,
        "activation_mantra": "Om Hraam Hreem Hraum Sah Suryaya Namah",
        "classical_citation": "Garuda Purana 68.14; Mani Mala §3",
    },
    "moon": {
        "primary_stone": "Pearl",
        "alternate_name": "Moti",
        "substitute_stones": ["Moonstone", "White Coral", "White Zircon"],
        "metal": "silver",
        "finger": "little",
        "day": "monday",
        "weight_ratti_min": 2.0,
        "weight_ratti_max": 5.0,
        "activation_mantra": "Om Shraam Shreem Shraum Sah Chandraya Namah",
        "classical_citation": "Garuda Purana 68.15; Mani Mala §4",
    },
    "mars": {
        "primary_stone": "Red Coral",
        "alternate_name": "Moonga",
        "substitute_stones": ["Red Agate", "Carnelian"],
        "metal": "gold/copper",
        "finger": "ring",
        "day": "tuesday",
        "weight_ratti_min": 3.0,
        "weight_ratti_max": 9.0,
        "activation_mantra": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
        "classical_citation": "Garuda Purana 68.16; Mani Mala §5",
    },
    "mercury": {
        "primary_stone": "Emerald",
        "alternate_name": "Panna",
        "substitute_stones": ["Green Tourmaline", "Peridot", "Green Jade"],
        "metal": "gold",
        "finger": "little",
        "day": "wednesday",
        "weight_ratti_min": 3.0,
        "weight_ratti_max": 5.0,
        "activation_mantra": "Om Braam Breem Braum Sah Budhaya Namah",
        "classical_citation": "Garuda Purana 68.17; Mani Mala §6",
    },
    "jupiter": {
        "primary_stone": "Yellow Sapphire",
        "alternate_name": "Pukhraj",
        "substitute_stones": ["Yellow Topaz", "Citrine", "Yellow Beryl"],
        "metal": "gold",
        "finger": "index",
        "day": "thursday",
        "weight_ratti_min": 3.0,
        "weight_ratti_max": 5.0,
        "activation_mantra": "Om Graam Greem Graum Sah Gurave Namah",
        "classical_citation": "Garuda Purana 68.18; Brihat Parasara Hora Shastra 83.6",
    },
    "venus": {
        "primary_stone": "Diamond",
        "alternate_name": "Heera",
        "substitute_stones": ["White Sapphire", "White Zircon", "White Topaz"],
        "metal": "silver/platinum",
        "finger": "middle",
        "day": "friday",
        "weight_ratti_min": 0.5,
        "weight_ratti_max": 1.0,
        "activation_mantra": "Om Draam Dreem Draum Sah Shukraya Namah",
        "classical_citation": "Garuda Purana 68.19; Mani Mala §7",
    },
    "saturn": {
        "primary_stone": "Blue Sapphire",
        "alternate_name": "Neelam",
        "substitute_stones": ["Amethyst", "Blue Spinel", "Lapis Lazuli"],
        "metal": "silver/iron",
        "finger": "middle",
        "day": "saturday",
        "weight_ratti_min": 3.0,
        "weight_ratti_max": 5.0,
        "activation_mantra": "Om Praam Preem Praum Sah Shanaischaraya Namah",
        "classical_citation": "Garuda Purana 68.20; Mani Mala §8",
    },
    "rahu": {
        "primary_stone": "Hessonite",
        "alternate_name": "Gomed",
        "substitute_stones": ["Zircon", "Smoky Quartz"],
        "metal": "silver/panchaloha",
        "finger": "middle",
        "day": "saturday",
        "weight_ratti_min": 5.0,
        "weight_ratti_max": 8.0,
        "activation_mantra": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
        "classical_citation": "Garuda Purana 68.21; Mani Mala §9",
    },
    "ketu": {
        "primary_stone": "Cat's Eye",
        "alternate_name": "Vaidurya",
        "substitute_stones": ["Tiger's Eye", "Apatite"],
        "metal": "silver/panchaloha",
        "finger": "little",
        "day": "tuesday",
        "weight_ratti_min": 3.0,
        "weight_ratti_max": 5.0,
        "activation_mantra": "Om Sraam Sreem Sraum Sah Ketave Namah",
        "classical_citation": "Garuda Purana 68.22; Mani Mala §10",
    },
}


# ---------------------------------------------------------------------------
# G35 — YANTRA_REFERENCE
# Navagraha yantras + Sri Yantra variants + Vastu Yantra
# ---------------------------------------------------------------------------

YANTRA_REFERENCE = [
    {
        "name": "Sun Yantra",
        "graha": "sun",
        "purpose": "Authority, health, vitality, government favour, father's wellbeing",
        "metal": "copper/gold",
        "activation_day": "sunday",
        "mantra_syllables": "Om Hraam Hreem Hraum Sah Suryaya Namah",
        "structure_description": "6-pointed star (Shatkona) within circle within square with 4 gates; central bindu encodes solar energy",
        "classical_citation": "Tantrasara; Mantra Mahodadhi §11",
    },
    {
        "name": "Moon Yantra",
        "graha": "moon",
        "purpose": "Mental peace, emotional balance, mother's wellbeing, fertility",
        "metal": "silver",
        "activation_day": "monday",
        "mantra_syllables": "Om Shraam Shreem Shraum Sah Chandraya Namah",
        "structure_description": "Hexagon within two interlaced triangles; 16-petalled lotus outer ring",
        "classical_citation": "Tantrasara; Mantra Mahodadhi §12",
    },
    {
        "name": "Mars Yantra",
        "graha": "mars",
        "purpose": "Courage, property, siblings, overcoming enemies, surgery",
        "metal": "copper",
        "activation_day": "tuesday",
        "mantra_syllables": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
        "structure_description": "Upward-pointing triangle within octagon; fiery red yantra with 8-petalled lotus",
        "classical_citation": "Tantrasara; Mantra Mahodadhi §13",
    },
    {
        "name": "Mercury Yantra",
        "graha": "mercury",
        "purpose": "Intelligence, speech, business success, education, trade",
        "metal": "gold/bronze",
        "activation_day": "wednesday",
        "mantra_syllables": "Om Braam Breem Braum Sah Budhaya Namah",
        "structure_description": "Interlaced triangles forming Star of David; surrounded by 8-petalled lotus",
        "classical_citation": "Tantrasara; Mantra Mahodadhi §14",
    },
    {
        "name": "Jupiter Yantra",
        "graha": "jupiter",
        "purpose": "Wisdom, wealth, children, dharma, teacher's blessings",
        "metal": "gold",
        "activation_day": "thursday",
        "mantra_syllables": "Om Graam Greem Graum Sah Gurave Namah",
        "structure_description": "Central bindu in upward triangle within hexagon; 8-petalled lotus with 3 circles",
        "classical_citation": "Tantrasara; Brihat Parasara Hora Shastra 83.8",
    },
    {
        "name": "Venus Yantra",
        "graha": "venus",
        "purpose": "Love, marriage, luxury, arts, conveyances, beauty",
        "metal": "silver/platinum",
        "activation_day": "friday",
        "mantra_syllables": "Om Draam Dreem Draum Sah Shukraya Namah",
        "structure_description": "Downward triangle within octagon; surrounded by 10-petalled lotus",
        "classical_citation": "Tantrasara; Mantra Mahodadhi §15",
    },
    {
        "name": "Saturn Yantra",
        "graha": "saturn",
        "purpose": "Longevity, discipline, service, karmic balance, sade-sati mitigation",
        "metal": "iron/silver",
        "activation_day": "saturday",
        "mantra_syllables": "Om Praam Preem Praum Sah Shanaischaraya Namah",
        "structure_description": "7 concentric squares; central triangle pointing downward; dark metallic finish",
        "classical_citation": "Tantrasara; Mantra Mahodadhi §16",
    },
    {
        "name": "Rahu Yantra",
        "graha": "rahu",
        "purpose": "Foreign travel, speculation, sudden gains, breaking obstacles, Rahu dasha remedy",
        "metal": "silver/panchaloha",
        "activation_day": "saturday",
        "mantra_syllables": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
        "structure_description": "Irregular octagram within square; shadowy geometric form representing the ascending node",
        "classical_citation": "Tantrasara; Mantra Mahodadhi §17",
    },
    {
        "name": "Ketu Yantra",
        "graha": "ketu",
        "purpose": "Moksha, spirituality, past-life karma resolution, Ketu dasha remedy",
        "metal": "silver/panchaloha",
        "activation_day": "tuesday",
        "mantra_syllables": "Om Sraam Sreem Sraum Sah Ketave Namah",
        "structure_description": "Tail-serpent form encoded in geometric matrix; 7-pointed star within circle",
        "classical_citation": "Tantrasara; Mantra Mahodadhi §18",
    },
    {
        "name": "Sri Yantra",
        "type": "shakti",
        "purpose": "Wealth, abundance, cosmic harmony, Lakshmi's blessings — the supreme yantra",
        "metal": "gold/copper/silver",
        "activation_day": "friday",
        "mantra_syllables": "Om Shreem Hreem Shreem Kamale Kamalalaye Praseed Praseed Om Shreem Hreem Shreem Mahalakshmiyai Namah",
        "structure_description": "9 interlocked triangles (5 downward Shakti + 4 upward Shiva) creating 43 smaller triangles; 8-petalled + 16-petalled lotus rings; outer bhupura (square earth-plane) with 4 gates",
        "classical_citation": "Devi Bhagavata Purana; Lalita Sahasranama tantric commentary",
    },
    {
        "name": "Shri Yantra Maha Meru",
        "type": "shakti_3d",
        "purpose": "Three-dimensional Sri Yantra representing Mount Meru; home prosperity, spiritual elevation",
        "metal": "sphatika (crystal)/gold/copper",
        "activation_day": "friday",
        "mantra_syllables": "Om Aim Hreem Shreem Sri Lalita Tripurasundaryai Namah",
        "structure_description": "Three-dimensional pyramidal form of Sri Yantra; nine-storied mountain with bindu at apex; base is bhupura, apex is the supreme bindu",
        "classical_citation": "Devi Bhagavata Purana §12; Soundaryalahari verse 11",
    },
    {
        "name": "Vastu Yantra",
        "type": "vastu",
        "purpose": "Home/office space harmony, removal of vastu doshas, directional balance",
        "metal": "copper",
        "activation_day": "sunday",
        "mantra_syllables": "Om Vastoshpate Pratarano Na Ehi Ayur Gayo Abhivardhan No Asminn Indravastu Asminn Indra Vastu",
        "structure_description": "Vastu Purusha mandala — 45-field grid; Brahmasthana at center; 8 directional deities at perimeter; placed at entrance or center of dwelling",
        "classical_citation": "Vastu Shastra; Manasara §4; Brihat Samhita §53",
    },
]


# ---------------------------------------------------------------------------
# G36 — ASHTA KOOTA compatibility system
# ---------------------------------------------------------------------------

ASHTA_KOOTA = {
    "varna": {
        "max_points": 1,
        "description": "Spiritual/social compatibility (Brahmin > Kshatriya > Vaishya > Shudra hierarchy)",
        "scoring_rule": (
            "1 point if boy's varna >= girl's varna; 0 if boy's varna < girl's varna. "
            "Brahmin=4, Kshatriya=3, Vaishya=2, Shudra=1. "
            "Nakshatra rulers: Sun/Jupiter=Brahmin; Moon/Venus=Vaishya; "
            "Mars/Ketu=Kshatriya; Mercury/Saturn=Shudra; Rahu=mixed."
        ),
    },
    "vashya": {
        "max_points": 2,
        "description": "Dominance/control/magnetic influence between partners",
        "scoring_rule": (
            "2 points if both same vashya class; 1 point if one vashya governs other; "
            "0.5 if neutral; 0 if hostile. "
            "Vashya classes by rashi: Manav/Dwipada (human) = Gemini/Virgo/Libra/Libra 1st half/Aquarius; "
            "Chatushpad (quadruped) = Aries/Taurus/Capricorn 2nd half/Sagittarius 2nd half; "
            "Jalachara (water) = Cancer/Pisces/Capricorn 1st half; "
            "Keet (insect) = Scorpio; Vanchar (wild) = Leo."
        ),
    },
    "tara": {
        "max_points": 3,
        "description": "Birth star (janma nakshatra) compatibility counted in groups of 9 from girl's to boy's nakshatra",
        "scoring_rule": (
            "Count from girl's nakshatra to boy's nakshatra; divide by 9 and take remainder. "
            "Tara groups (remainder 1-9): 1=Janma, 2=Sampat, 3=Vipat, 4=Kshema, "
            "5=Pratyak, 6=Sadhana, 7=Naidhana, 8=Mitra, 9=Parama Mitra. "
            "Odd taras (1,3,5,7) for girl are inauspicious; check both directions. "
            "3 points if average is >= 1.5; 1.5 if one direction auspicious; 0 if both inauspicious."
        ),
    },
    "yoni": {
        "max_points": 4,
        "description": "Sexual/animal compatibility — 14 yoni pairs mapped to 27 nakshatras",
        "scoring_rule": (
            "4 points = same yoni (max harmony); "
            "3 points = friendly yoni; "
            "2 points = neutral yoni; "
            "1 point = enemy yoni; "
            "0 points = bitter enemy yoni. "
            "14 animal yoni pairs: Ashwa(horse), Gaja(elephant), Mesha(ram), Sarpa(serpent), "
            "Shvan(dog), Marjara(cat), Mushaka(rat), Gau(cow), Mahisha(buffalo), "
            "Vyaghra(tiger), Mriga(deer), Vanara(monkey), Nakula(mongoose), Simha(lion)."
        ),
    },
    "graha_maitri": {
        "max_points": 5,
        "description": "Planetary friendship between Moon sign lords of boy and girl",
        "scoring_rule": (
            "5 points = both Moon lords are mutual friends; "
            "4 points = one friend + one neutral; "
            "3 points = both neutral; "
            "2 points = one friend + one enemy (or both neutral with one exception); "
            "1 point = one neutral + one enemy; "
            "0 points = both Moon lords are mutual enemies."
        ),
    },
    "gana": {
        "max_points": 6,
        "description": "Nature/temperament compatibility — Deva (divine), Manushya (human), Rakshasa (demonic)",
        "scoring_rule": (
            "6 points = same gana (best); "
            "5 points = Deva + Manushya (compatible); "
            "1 point = Manushya + Rakshasa (difficult); "
            "0 points = Deva + Rakshasa (incompatible — Gana Dosha). "
            "Exception: if Moon signs are friendly, some texts allow Gana Dosha cancellation."
        ),
    },
    "bhakoot": {
        "max_points": 7,
        "description": "Moon sign relationship — inter-rashi compatibility and financial/longevity implications",
        "scoring_rule": (
            "7 points = 1/1, 1/7, 1/4, 1/10 rashi relationships (same or trine/kendra); "
            "0 points = 2/12, 6/8 rashi relationships (Bhakoot Dosha — poverty/death patterns). "
            "Count girl's rashi from boy's and boy's from girl's. "
            "2/12 pattern: financial incompatibility. 6/8 pattern: health/longevity risk. "
            "Navamsha lords' friendship can cancel Bhakoot Dosha per some acharyas."
        ),
    },
    "nadi": {
        "max_points": 8,
        "description": "Nadi (Adi/Madhya/Antya) — most important koota; governs progeny and health",
        "scoring_rule": (
            "8 points = different nadis (excellent — Nadi Anukoolya); "
            "0 points = same nadi (Nadi Dosha — most severe dosha in Ashta Koota). "
            "Nadi Dosha effects: childlessness, progeny ill-health, marital disharmony. "
            "Cancellation: if both have same rashi but different nakshatras (Nadi Dosha Parihara), "
            "or if both have same nakshatra but different padas."
        ),
    },
}

# Total maximum points
ASHTA_KOOTA_MAX_TOTAL = sum(k["max_points"] for k in ASHTA_KOOTA.values())  # 36

# Compatibility thresholds (traditional)
COMPATIBILITY_THRESHOLDS = {
    "excellent": (31, 36),   # Uttama — marriage recommended
    "good": (25, 30),        # Madhyama — acceptable
    "average": (18, 24),     # Samanya — proceed with caution
    "poor": (0, 17),         # Adhama — not recommended
}

# ---------------------------------------------------------------------------
# NAKSHATRA_GANA — all 27 nakshatras classified
# Nakshatra numbers are 1-indexed (1=Ashwini … 27=Revati)
# ---------------------------------------------------------------------------

# deva = divine nature (sattvic)
# manushya = human nature (rajasic)
# rakshasa = demon nature (tamasic)

NAKSHATRA_GANA: dict[int, str] = {
    # Deva gana
    1: "deva",   # Ashwini
    5: "deva",   # Mrigashira
    7: "deva",   # Punarvasu
    8: "deva",   # Pushya
    12: "deva",  # Uttara Phalguni
    13: "deva",  # Hasta
    15: "deva",  # Swati
    16: "deva",  # Vishakha
    17: "deva",  # Anuradha
    21: "deva",  # Uttara Ashadha
    22: "deva",  # Shravana
    25: "deva",  # Purva Bhadrapada
    27: "deva",  # Revati
    # Manushya gana
    2: "manushya",   # Bharani
    6: "manushya",   # Ardra
    11: "manushya",  # Purva Phalguni
    14: "manushya",  # Chitra
    20: "manushya",  # Purva Ashadha
    24: "manushya",  # Shatabhisha
    26: "manushya",  # Uttara Bhadrapada
    # Rakshasa gana
    3: "rakshasa",   # Krittika
    4: "rakshasa",   # Rohini
    9: "rakshasa",   # Ashlesha
    10: "rakshasa",  # Magha
    18: "rakshasa",  # Jyeshtha
    19: "rakshasa",  # Mula
    23: "rakshasa",  # Dhanishtha
}

# ---------------------------------------------------------------------------
# NAKSHATRA_NADI — all 27 nakshatras classified as adi/madhya/antya
# Alternating in groups of 3: adi={1,4,7,10,13,16,19,22,25},
# madhya={2,5,8,11,14,17,20,23,26}, antya={3,6,9,12,15,18,21,24,27}
# ---------------------------------------------------------------------------

NAKSHATRA_NADI: dict[int, str] = {}
for _n in range(1, 28):
    _rem = (_n - 1) % 3   # 0=adi, 1=madhya, 2=antya
    NAKSHATRA_NADI[_n] = ("adi", "madhya", "antya")[_rem]

# Gana scoring matrix: gana_score[boy_gana][girl_gana] = points
_GANA_SCORE_MATRIX: dict[str, dict[str, int]] = {
    "deva":     {"deva": 6, "manushya": 5, "rakshasa": 0},
    "manushya": {"deva": 5, "manushya": 6, "rakshasa": 1},
    "rakshasa": {"deva": 0, "manushya": 1, "rakshasa": 6},
}


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def get_gemstone(graha: str) -> dict:
    """Return gemstone data for a graha.

    Args:
        graha: lowercase graha name ('sun', 'moon', 'mars', 'mercury',
               'jupiter', 'venus', 'saturn', 'rahu', 'ketu').

    Returns:
        dict with primary_stone, substitute_stones, metal, finger, day,
        weight_ratti_min/max, activation_mantra, classical_citation.

    Raises:
        KeyError if graha not found.
    """
    graha_key = graha.lower().strip()
    if graha_key not in GEMSTONE_REFERENCE:
        raise KeyError(
            f"Graha '{graha}' not found. Valid: {sorted(GEMSTONE_REFERENCE.keys())}"
        )
    return GEMSTONE_REFERENCE[graha_key]


def get_compatible_yantras(purpose: str) -> list:
    """Return yantras whose purpose field contains the given keyword (case-insensitive).

    Args:
        purpose: keyword string to search (e.g. 'wealth', 'marriage', 'health').

    Returns:
        list of yantra dicts matching the keyword.
    """
    keyword = purpose.lower().strip()
    return [y for y in YANTRA_REFERENCE if keyword in y["purpose"].lower()]


def get_nakshatra_gana(nakshatra: int) -> str:
    """Return gana classification for a nakshatra (1-indexed, 1=Ashwini).

    Returns:
        'deva', 'manushya', or 'rakshasa'.

    Raises:
        KeyError if nakshatra out of 1-27 range.
    """
    if nakshatra not in NAKSHATRA_GANA:
        raise KeyError(f"Nakshatra {nakshatra} out of range 1-27")
    return NAKSHATRA_GANA[nakshatra]


def get_nakshatra_nadi(nakshatra: int) -> str:
    """Return nadi classification for a nakshatra (1-indexed, 1=Ashwini).

    Returns:
        'adi', 'madhya', or 'antya'.

    Raises:
        KeyError if nakshatra out of 1-27 range.
    """
    if nakshatra not in NAKSHATRA_NADI:
        raise KeyError(f"Nakshatra {nakshatra} out of range 1-27")
    return NAKSHATRA_NADI[nakshatra]


def compute_gana_score(boy_nak: int, girl_nak: int) -> int:
    """Compute Gana Koota score (max 6) from boy's and girl's nakshatra numbers.

    Uses traditional scoring matrix:
      deva+deva = 6, deva+manushya = 5, deva+rakshasa = 0,
      manushya+manushya = 6, manushya+rakshasa = 1,
      rakshasa+rakshasa = 6.

    Args:
        boy_nak: boy's janma nakshatra (1-27).
        girl_nak: girl's janma nakshatra (1-27).

    Returns:
        int score 0-6.
    """
    boy_gana = get_nakshatra_gana(boy_nak)
    girl_gana = get_nakshatra_gana(girl_nak)
    return _GANA_SCORE_MATRIX[boy_gana][girl_gana]


def compute_nadi_score(boy_nak: int, girl_nak: int) -> int:
    """Compute Nadi Koota score (max 8) from boy's and girl's nakshatra numbers.

    Nadi Dosha: if both have same nadi → 0 points (most severe dosha).
    Different nadis → 8 points (full score).

    Args:
        boy_nak: boy's janma nakshatra (1-27).
        girl_nak: girl's janma nakshatra (1-27).

    Returns:
        8 if nadis differ, 0 if same nadi (Nadi Dosha).
    """
    boy_nadi = get_nakshatra_nadi(boy_nak)
    girl_nadi = get_nakshatra_nadi(girl_nak)
    return 0 if boy_nadi == girl_nadi else 8


def compute_ashta_koota_total_max() -> int:
    """Return the theoretical maximum Ashta Koota score (36)."""
    return ASHTA_KOOTA_MAX_TOTAL


def get_compatibility_grade(total_score: int) -> str:
    """Return compatibility grade label for a given total Ashta Koota score.

    Args:
        total_score: int 0-36.

    Returns:
        'excellent', 'good', 'average', or 'poor'.
    """
    for grade, (low, high) in COMPATIBILITY_THRESHOLDS.items():
        if low <= total_score <= high:
            return grade
    return "poor"
