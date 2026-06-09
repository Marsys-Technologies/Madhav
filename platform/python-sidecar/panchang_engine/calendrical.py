"""
calendrical.py — Classical calendar context: masa, samvat, samvatsara, ritu, ayana.

All computations are deterministic from (date, sun_lon, tithi_id, paksha).

Ayana boundary (sidereal):
  Uttarayana — Sun in Makara through Mithuna (270°–90°, wrapping through 0°).
  Dakshinayana — Sun in Karkata through Dhanu (90°–270°).

Purnimanta masa mapping (direct, no shift):
  masa_index = int(sun_lon / 30) % 12
  Mesha Sun (0°) → Chaitra, Vrishabha (30°) → Vaishakha, …
  Makara (270°) → Pausha, Kumbha (300°) → Magha.

NOTE: is_adhika_masa and is_kshaya_masa are FLOORED as False — determination
requires multi-month sequential computation tracking whether the sun transits
two sign boundaries in one lunar month. Not available at single-call scope.
"""
from __future__ import annotations
from datetime import date
from .types import Calendrical
from .shastra_tables import JOVIAN_60_YEAR_NAMES, SIGN_NAMES


# ---------------------------------------------------------------------------
# Lookup tables (0-indexed by int(sun_lon / 30) % 12)
# ---------------------------------------------------------------------------

# Ritu by 0-based sign index (Mesha=0 … Meena=11)
_RITU_BY_SIGN_0: list[str] = [
    "Vasanta",  "Vasanta",   # Mesha, Vrishabha
    "Grishma",  "Grishma",   # Mithuna, Karkata
    "Varsha",   "Varsha",    # Simha, Kanya
    "Sharad",   "Sharad",    # Tula, Vrishchika
    "Hemanta",  "Hemanta",   # Dhanu, Makara
    "Shishira", "Shishira",  # Kumbha, Meena
]

# Purnimanta masa names — indexed 0..11 directly by sign_0 = int(sun_lon/30) % 12.
# No shift required: Mesha (sign_0=0) → Chaitra; Kumbha (sign_0=10) → Magha.
# Canonical purnimanta mapping: each masa is named after the full moon nakshatra
# that falls while the Sun is in that sign.
#   Mesha Sun → full moon near Chitra nak → Chaitra
#   Vrishabha → Vishakha nak → Vaishakha
#   …
#   Kumbha Sun → full moon near Magha nak → Magha
_MASA_PURNIMANTA: list[str] = [
    "Chaitra",      # index 0  — Sun in Mesha (0°–30°)
    "Vaishakha",    # index 1  — Sun in Vrishabha
    "Jyeshtha",     # index 2  — Sun in Mithuna
    "Ashadha",      # index 3  — Sun in Karkata
    "Shravana",     # index 4  — Sun in Simha
    "Bhadrapada",   # index 5  — Sun in Kanya
    "Ashwina",      # index 6  — Sun in Tula
    "Kartika",      # index 7  — Sun in Vrishchika
    "Margashirsha", # index 8  — Sun in Dhanu
    "Pausha",       # index 9  — Sun in Makara
    "Magha",        # index 10 — Sun in Kumbha
    "Phalguna",     # index 11 — Sun in Meena
]


def compute_calendrical(
    d: date,
    sun_lon: float,
    tithi_id: int,
    paksha: str,
) -> Calendrical:
    """
    Compute classical calendar context from date and Sun's sidereal longitude.

    Args:
        d:        local calendar date
        sun_lon:  Sun's sidereal longitude (0..360)
        tithi_id: 1..30 (current tithi, 1-based)
        paksha:   "shukla" | "krishna"

    Returns:
        Calendrical dataclass (frozen).
    """
    # 0-based sign index: 0=Mesha, 1=Vrishabha, … 11=Meena
    sign_0 = int(sun_lon / 30) % 12

    # Ayana — sidereal definition:
    #   Uttarayana: Sun from Makara (270°) to Mithuna (< 90°), wrapping through 0°.
    #   Dakshinayana: Sun from Karkata (90°) to Dhanu (< 270°).
    ayana = "Uttarayana" if (sun_lon >= 270.0 or sun_lon < 90.0) else "Dakshinayana"

    # Ritu — two signs per season
    ritu = _RITU_BY_SIGN_0[sign_0]

    # Purnimanta masa: direct sign_0 index (no shift).
    # Mesha (0) → Chaitra; Kumbha (10) → Magha.
    masa_idx = sign_0
    masa_purnimanta = _MASA_PURNIMANTA[masa_idx]

    # Amanta masa: in shukla paksha the amanta month runs one name behind purnimanta;
    # in krishna paksha the amanta month matches the purnimanta month's second half.
    if paksha == "shukla":
        amanta_idx = (masa_idx - 1) % 12
    else:
        amanta_idx = masa_idx
    masa_amanta = _MASA_PURNIMANTA[amanta_idx]

    year = d.year

    # Samvat formulas (civil Gregorian year as reference):
    #   Vikram Samvat new year falls around March/April; add 57 from April onwards,
    #   56 for Jan–Mar (before Vikram new year).
    vikram_samvat = year + 57 if d.month >= 4 else year + 56

    #   Shaka Samvat (Shalivahana): Gregorian year − 78.
    shaka_samvat = year - 78

    #   Kali Yuga elapsed years: starts 3102 BCE; year 2000 CE = Kali 5102,
    #   so kali = year + 3102.
    kali_samvat = year + 3102

    #   Saptarshi (Laukika) Samvat: year + 3076.
    saptarshi_samvat = year + 3076

    # Jovian (Brihaspati) 60-year cycle — 0-based index from Kali epoch.
    jovian_idx = (kali_samvat - 1) % 60
    jovian_year_name = JOVIAN_60_YEAR_NAMES[jovian_idx]
    jovian_year_number = jovian_idx + 1  # 1-based (1..60)

    # Sankranti detection: Sun within 0.5° of entering a sign boundary
    # (i.e. within 0.5° measured from the start of the current sign).
    within_sign_deg = sun_lon % 30
    sankranti_name: str | None = None
    if within_sign_deg < 0.5:
        sankranti_name = f"{SIGN_NAMES[sign_0]} Sankranti"

    return Calendrical(
        masa_purnimanta=masa_purnimanta,
        masa_amanta=masa_amanta,
        is_adhika_masa=False,   # floored — multi-month sequential detection required
        is_kshaya_masa=False,   # floored — multi-month sequential detection required
        ritu=ritu,
        ayana=ayana,
        vikram_samvat=vikram_samvat,
        shaka_samvat=shaka_samvat,
        kali_samvat=kali_samvat,
        saptarshi_samvat=saptarshi_samvat,
        jovian_year_name=jovian_year_name,
        jovian_year_number=jovian_year_number,
        sankranti_name=sankranti_name,
        solar_arc_deg=round(sun_lon % 360, 4),
    )
