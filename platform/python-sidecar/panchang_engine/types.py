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
class AngaAttributes:
    lord: str
    deity: str
    anga_type: str
    pct_elapsed: Optional[float] = None


@dataclass(frozen=True)
class LagnaState:
    ascendant_deg: float
    ascendant_sign_id: int
    ascendant_sign_name: str
    ascendant_nak_id: int
    ascendant_nak_name: str
    ascendant_pada: int
    mc_deg: float
    mc_sign_id: int
    mc_sign_name: str
    house_cusps: list
    house_system: str


@dataclass(frozen=True)
class WindowMembership:
    inauspicious_active: list
    auspicious_active: list
    choghadiya_slot: Optional[str] = None
    hora_planet: Optional[str] = None
    seconds_to_next_inauspicious: Optional[float] = None
    seconds_to_next_auspicious: Optional[float] = None
    seconds_to_next_choghadiya: Optional[float] = None
    seconds_to_next_hora: Optional[float] = None


@dataclass(frozen=True)
class MicroTiming:
    ghati_from_sunrise: float
    vighati_from_sunrise: float
    muhurta_of_day: int
    pranapada_sign_id: int
    pranapada_sign_name: str


@dataclass(frozen=True)
class SunMoonDynamics:
    sun_moon_separation_deg: float
    moon_illumination_pct: float
    moon_phase_angle_deg: float


@dataclass(frozen=True)
class VasaFamily:
    agni_vasa: str
    chandra_vasa: str
    rahu_vasa: str
    disha_vasa: str
    nakshatra_vasa: str
    bhadra_vasa: str


@dataclass(frozen=True)
class PanchakaState:
    active: bool
    panchaka_type: Optional[str] = None


@dataclass(frozen=True)
class AnandadiYoga:
    yoga_name: str
    yoga_number: int
    auspicious: bool


@dataclass(frozen=True)
class Calendrical:
    masa_purnimanta: str
    masa_amanta: str
    is_adhika_masa: bool
    is_kshaya_masa: bool
    ritu: str
    ayana: str
    vikram_samvat: int
    shaka_samvat: int
    kali_samvat: int
    saptarshi_samvat: int
    jovian_year_name: str
    jovian_year_number: int
    sankranti_name: Optional[str] = None
    solar_arc_deg: float = 0.0


@dataclass(frozen=True)
class ShoonyaState:
    tithi_shoonya_sign_id: Optional[int] = None
    tithi_shoonya_sign_name: Optional[str] = None
    nakshatra_shoonya_sign_id: Optional[int] = None
    nakshatra_shoonya_sign_name: Optional[str] = None


@dataclass(frozen=True)
class TaraBala:
    tara_count: int
    tara_name: str
    tara_quality: str
    chandra_bala: int
    chandra_bala_quality: str


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
    topics_computed: list = None
    upagrahas: Optional[list] = None
    outer_planets: Optional[list] = None
    sun_moon: Optional[SunMoonDynamics] = None
    inauspicious_full: Optional[list] = None
    auspicious_full: Optional[list] = None
    anandadi_yoga: Optional[AnandadiYoga] = None
    vasa: Optional[VasaFamily] = None
    panchaka: Optional[PanchakaState] = None
    homa_windows: Optional[list] = None
    calendrical: Optional[Calendrical] = None
    shoonya: Optional[ShoonyaState] = None
    tara_bala: Optional[TaraBala] = None
    festivals: Optional[list] = None
    day_events: Optional[list] = None
    day_muhurtas: Optional[list] = None


@dataclass(frozen=True)
class PanchangaInstant:
    """
    Panchang state at an exact datetime (birth moment or event instant query).
    Unlike Panchang (sunrise-based day record), all angas are computed at the
    given instant — correct for birth charts and moment-specific queries.

    Per-topic floor contract: only topics listed in `topics_computed` are present.
    Absent topics are omitted (never fabricated). Current release computes:
      "angas" — tithi/nakshatra/yoga/karana/vara/paksha
      "planets" — 9 grahas sidereal state
    """
    instant_utc: datetime
    lat: float
    lon: float
    tz_offset_minutes: int
    # The 5 angas — computed at the exact instant (not sunrise-based)
    tithi: Anga
    nakshatra: Anga
    yoga: Anga
    karana: Anga          # ruling karana at the instant (primary)
    karana_next: Optional[Anga]   # second karana of the tithi (may differ by day-end)
    vara: Anga
    paksha: str           # "shukla" (tithis 1–15) or "krishna" (tithis 16–30)
    planets: list         # list[PlanetState] — 9 grahas sidereal at instant
    # Metadata
    computation_version: str
    ephemeris_version: str
    topics_computed: list  # list[str] — floor-to-absent contract
    # Rich output fields
    tithi_attrs: Optional[AngaAttributes] = None
    nakshatra_attrs: Optional[AngaAttributes] = None
    yoga_attrs: Optional[AngaAttributes] = None
    karana_attrs: Optional[AngaAttributes] = None
    vara_attrs: Optional[AngaAttributes] = None
    upagrahas: Optional[list] = None
    outer_planets: Optional[list] = None
    sun_moon: Optional[SunMoonDynamics] = None
    inauspicious_full: Optional[list] = None
    auspicious_full: Optional[list] = None
    special_yogas_instant: Optional[list] = None
    anandadi_yoga: Optional[AnandadiYoga] = None
    vasa: Optional[VasaFamily] = None
    panchaka: Optional[PanchakaState] = None
    homa_windows: Optional[list] = None
    calendrical: Optional[Calendrical] = None
    shoonya: Optional[ShoonyaState] = None
    tara_bala: Optional[TaraBala] = None
    lagna: Optional[LagnaState] = None
    window_membership: Optional[WindowMembership] = None
    micro_timing: Optional[MicroTiming] = None


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
