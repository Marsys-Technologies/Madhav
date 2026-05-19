"""
types.py — Core dataclasses for panchang_engine.
All objects are frozen (immutable) to encourage functional-style usage.
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass(frozen=True)
class Anga:
    """
    A single Panchang element (tithi, nakshatra, yoga, karana, vara).
    id is the element-specific ordinal (e.g. tithi 1..30, nakshatra 1..27).
    end_utc is when this anga transitions to the next one (UTC).
    """
    id: int               # tithi 1..30; nakshatra 1..27; yoga 1..27; karana 1..11; vara 1..7
    name: str             # e.g. "Shukla Dvitiya", "Bharani"
    end_utc: datetime     # transition moment to the next anga; UTC


@dataclass(frozen=True)
class Timing:
    """A named time window (inauspicious period, auspicious muhurat, choghadiya, hora, etc.)."""
    label: str            # "rahu_kalam", "abhijit", "hora_sun", etc.
    start_utc: datetime
    end_utc: datetime


@dataclass(frozen=True)
class PlanetState:
    """
    Sidereal state of one graha (planet / shadow planet) at a given moment.
    Longitudes are Lahiri-ayanamsha-corrected unless another ayanamsha was set.
    """
    name: str                       # "Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                    # "Venus", "Saturn", "Rahu", "Ketu"
    longitude_sidereal: float       # 0..360 (degrees, ayanamsha-corrected)
    sign_id: int                    # 1..12 (Mesha=1, Vrishabha=2, ..., Meena=12)
    sign_name: str                  # e.g. "Mesha"
    nakshatra_id: int               # 1..27 (Ashwini=1, ..., Revati=27)
    nakshatra_name: str             # e.g. "Ashwini"
    nakshatra_pada: int             # 1..4
    retrograde: bool                # True if planet is in retrograde motion
    combust: bool                   # True if within combustion orb of Sun


@dataclass(frozen=True)
class Panchang:
    """
    Full Panchang for a single local calendar day at a given location.
    special_yogas is [] in 4C-1-S1; populated in 4C-1-S2.
    """
    date: date
    lat: float
    lon: float
    tz_offset_minutes: int
    sunrise_utc: datetime
    sunset_utc: datetime
    moonrise_utc: Optional[datetime]
    moonset_utc: Optional[datetime]
    tithi: Anga
    nakshatra: Anga
    yoga: Anga
    karana_first: Anga
    karana_second: Anga
    vara: Anga
    paksha: str                     # "shukla" (tithis 1–15) or "krishna" (tithis 16–30)
    inauspicious: list              # list[Timing] — rahu_kalam, yamagandam, gulika_kalam, dur_muhurta
    auspicious: list                # list[Timing] — abhijit, brahma_muhurta, amrit_kalam, varjyam
    choghadiya: dict                # {"day": [Timing...], "night": [Timing...]}
    hora: list                      # list[Timing] — 24 planetary hours
    special_yogas: list             # list[dict] — populated in 4C-1-S2; [] this session
    planets: list                   # list[PlanetState] — 9 grahas
    computation_version: str        # panchang_engine.__version__
    ephemeris_version: str          # swisseph version string


@dataclass(frozen=True)
class NatalChart:
    """
    Minimal natal chart reference for dasha-aware muhurat scoring (used in 4C.6).
    Only the fields needed for Muhurat Finder scoring are captured here.
    """
    birth_nakshatra_id: int         # 1..27
    birth_lagna_sign_id: int        # 1..12 (Mesha=1)
    moon_sign_id: int               # 1..12
    active_dasha_lord: str          # e.g. "Saturn" — current Vimshottari dasha lord


@dataclass(frozen=True)
class MuhuratWindow:
    """
    A scored auspicious window for a specific event type.
    Populated by find_muhurat() in 4C.6.
    """
    event: str
    start_utc: datetime
    end_utc: datetime
    star_rating: int                # 1..5 (5 = best)
    score: float                    # aggregate weighted score
    breakdown: dict                 # per-factor score contributions
