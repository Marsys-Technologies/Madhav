"""
tara_bala.py — Tara Bala (Star Strength) computation for Muhurat native overlay.

Tara Bala is a classical Vedic muhurat technique that assesses the Moon's
nakshatra on a given day relative to the native's birth nakshatra. The 27
nakshatras are cycled from the birth nakshatra, and each position (Tara) has
a quality — auspicious, inauspicious, or neutral.

The 9-Tara cycle (Nava Tara Chakra):
  Position 1 (Janma)      — birth star: neutral
  Position 2 (Sampat)     — wealth: auspicious
  Position 3 (Vipat)      — danger: inauspicious
  Position 4 (Kshema)     — comfort: auspicious
  Position 5 (Pratyari)   — enemy: inauspicious
  Position 6 (Sadhaka)    — achievement: auspicious
  Position 7 (Vadha)      — destruction: inauspicious
  Position 8 (Mitra)      — friend: auspicious
  Position 9 (Ati-Mitra)  — great friend: auspicious

The cycle repeats: positions 10–18 mirror 1–9 (called the secondary cycle),
positions 19–27 mirror again (tertiary cycle). The auspiciousness of each
position in the secondary and tertiary cycles is generally maintained, though
strength is modulated.

Source: Muhurta Chintamani §Tara Bala; Brihat Parashara Hora Shastra §Tara;
  Jataka Parijata §Tara Bala computation.

Python-side version of the TS tara_bala helper (parity for score_muhurat
native overlay in Phase 4C-6-S1). Same outputs confirmed against TS version
in test_muhurat_scoring.py.
"""

# ---------------------------------------------------------------------------
# Tara quality map: position (1-indexed within a 9-cycle) → quality + score
# Source: MC §Tara Bala (Nava Tara Chakra)
# ---------------------------------------------------------------------------
_TARA_QUALITY: dict[int, dict] = {
    1: {"name": "Janma",    "quality": "neutral",     "score": 0.50},
    2: {"name": "Sampat",   "quality": "auspicious",  "score": 0.90},
    3: {"name": "Vipat",    "quality": "inauspicious","score": 0.00},
    4: {"name": "Kshema",   "quality": "auspicious",  "score": 0.85},
    5: {"name": "Pratyari", "quality": "inauspicious","score": 0.10},
    6: {"name": "Sadhaka",  "quality": "auspicious",  "score": 0.95},
    7: {"name": "Vadha",    "quality": "inauspicious","score": 0.00},
    8: {"name": "Mitra",    "quality": "auspicious",  "score": 0.80},
    9: {"name": "Ati-Mitra","quality": "auspicious",  "score": 1.00},
}

# Attenuation factor for secondary (2nd cycle) and tertiary (3rd cycle) repetitions.
# Classical texts indicate the secondary cycle has ~80% strength; tertiary ~60%.
_CYCLE_ATTENUATION: dict[int, float] = {
    1: 1.00,   # primary cycle (positions 1-9)
    2: 0.80,   # secondary cycle (positions 10-18)
    3: 0.60,   # tertiary cycle (positions 19-27)
}


def compute_tara_position(birth_nakshatra_id: int, current_nakshatra_id: int) -> int:
    """
    Return the Tara position (1..27) of current_nakshatra relative to birth_nakshatra.
    Both IDs are 1-indexed (1=Ashwini, 27=Revati).

    The Tara position is computed as:
      position = ((current - birth) mod 27) + 1

    This gives position 1 (Janma) when current == birth.
    """
    if not (1 <= birth_nakshatra_id <= 27):
        raise ValueError(f"birth_nakshatra_id must be 1..27, got {birth_nakshatra_id}")
    if not (1 <= current_nakshatra_id <= 27):
        raise ValueError(f"current_nakshatra_id must be 1..27, got {current_nakshatra_id}")

    # Convert to 0-indexed, compute offset, convert back to 1-indexed
    offset = (current_nakshatra_id - birth_nakshatra_id) % 27
    return offset + 1  # 1-indexed Tara position (1=Janma, 9=Ati-Mitra, 10=Janma again, etc.)


def get_tara_detail(tara_position: int) -> dict:
    """
    Return the Tara quality dict for a given position (1..27).
    Handles the three-cycle repeat with attenuation.
    Returns: {"name": str, "quality": str, "score": float, "cycle": int, "position_in_cycle": int}
    """
    if not (1 <= tara_position <= 27):
        raise ValueError(f"tara_position must be 1..27, got {tara_position}")

    cycle = (tara_position - 1) // 9 + 1           # 1, 2, or 3
    pos_in_cycle = (tara_position - 1) % 9 + 1     # 1..9

    base = _TARA_QUALITY[pos_in_cycle]
    attenuation = _CYCLE_ATTENUATION.get(cycle, 0.60)
    attenuated_score = base["score"] * attenuation

    return {
        "name": base["name"],
        "quality": base["quality"],
        "score": attenuated_score,
        "cycle": cycle,
        "position_in_cycle": pos_in_cycle,
        "tara_position": tara_position,
    }


def compute_tara_bala_score(birth_nakshatra_id: int, current_nakshatra_id: int) -> float:
    """
    Return a Tara Bala score in 0.0..1.0 for use in score_muhurat's native overlay.

    This is the primary entry point called by score_muhurat() when a NatalChart
    is provided. The score is then multiplied by the "native" weight.

    Args:
        birth_nakshatra_id: Native's birth Moon nakshatra (1=Ashwini, 27=Revati).
        current_nakshatra_id: Moon's current nakshatra on the day being scored.

    Returns:
        float: 0.0 (Vipat/Vadha) to 1.0 (Ati-Mitra primary cycle), attenuated by cycle.

    Source: MC §Tara Bala; JBHS §Tara; DP "Tara Bala" reference.
    """
    tara_pos = compute_tara_position(birth_nakshatra_id, current_nakshatra_id)
    detail = get_tara_detail(tara_pos)
    return detail["score"]


def compute_chandra_bala_score(birth_moon_sign_id: int, current_moon_sign_id: int) -> float:
    """
    Chandra Bala: Moon's strength relative to native's birth Moon sign.
    Classical rule (MC §Chandra Bala): Moon in positions 1,3,6,7,10,11 from
    birth Moon sign is auspicious; other positions are weak.

    Both IDs are 1-indexed (1=Mesha, 12=Meena).
    Returns: 0.0..1.0

    Source: MC §Chandra Bala; DP "Chandra Bala" reference.
    """
    if not (1 <= birth_moon_sign_id <= 12):
        raise ValueError(f"birth_moon_sign_id must be 1..12, got {birth_moon_sign_id}")
    if not (1 <= current_moon_sign_id <= 12):
        raise ValueError(f"current_moon_sign_id must be 1..12, got {current_moon_sign_id}")

    # Position of current Moon from birth Moon sign (1-indexed, 1=same sign)
    position = (current_moon_sign_id - birth_moon_sign_id) % 12 + 1

    # Auspicious positions per classical Chandra Bala rules
    # Source: MC §Chandra Bala
    _CHANDRA_BALA_SCORES: dict[int, float] = {
        1:  0.80,   # same sign — mixed (strong but too close)
        2:  0.30,   # 2nd — weak
        3:  0.90,   # 3rd — auspicious (Kshema; comfort)
        4:  0.20,   # 4th — weak (Pratyari)
        5:  0.30,   # 5th — weak
        6:  0.90,   # 6th — auspicious (Sadhaka; achievement)
        7:  0.85,   # 7th — auspicious (Mitra; partnership)
        8:  0.10,   # 8th — inauspicious (Vadha; obstacles)
        9:  0.40,   # 9th — neutral
        10: 0.90,   # 10th — auspicious (Karma; action succeeds)
        11: 0.95,   # 11th — most auspicious (Labha; gain)
        12: 0.30,   # 12th — weak (loss)
    }
    return _CHANDRA_BALA_SCORES.get(position, 0.50)


def compute_combined_native_score(
    birth_nakshatra_id: int,
    current_nakshatra_id: int,
    birth_moon_sign_id: int,
    current_moon_sign_id: int,
) -> float:
    """
    Combined Tara Bala + Chandra Bala score, weighted 60/40.
    Returns 0.0..1.0 for use in the native overlay weight in score_muhurat.

    Both are needed for a complete native overlay; Tara Bala is primary (60%)
    and Chandra Bala is secondary (40%) per classical weighting.
    Source: MC §Tara Bala + §Chandra Bala combined muhurta assessment.
    """
    tara_score = compute_tara_bala_score(birth_nakshatra_id, current_nakshatra_id)
    chandra_score = compute_chandra_bala_score(birth_moon_sign_id, current_moon_sign_id)
    return 0.60 * tara_score + 0.40 * chandra_score
