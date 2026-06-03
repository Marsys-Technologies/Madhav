"""
brahmagyan.almanac.types — Type definitions for the Almanac asset.

All dataclasses are frozen (immutable) for functional-style usage,
consistent with panchang_engine.types conventions.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class AlmanacLocation:
    """
    A normalized (lat/lon rounded to 0.1°) + IANA-tz location descriptor.

    Normalization: lat/lon are rounded to the nearest 0.1° before caching so
    locations within ~11km share a cache entry. Callers should not rely on the
    exact stored values for precision work; they are for cache keying only.

    Fields
    ------
    lat       : decimal degrees, +N, rounded to 0.1°
    lon       : decimal degrees, +E, rounded to 0.1°
    tz_name   : IANA timezone string (e.g. "Asia/Kolkata", "America/New_York")
                Required. The engine resolves UTC offset per-date to handle DST.
    label     : Human-readable label (optional, e.g. "Bhubaneswar")

    Cache key = f"{lat:.1f}_{lon:.1f}_{tz_name}"
    """
    lat: float       # rounded to 0.1°
    lon: float       # rounded to 0.1°
    tz_name: str     # IANA timezone name
    label: str = ""  # optional human label

    @property
    def cache_key(self) -> str:
        return f"{self.lat:.1f}_{self.lon:.1f}_{self.tz_name}"


@dataclass(frozen=True)
class AlmanacDateRange:
    """
    Inclusive date range for almanac.query().

    Validation: date_from <= date_to; maximum 366 days per call.
    """
    date_from: date
    date_to: date

    def __post_init__(self):
        if self.date_from > self.date_to:
            raise ValueError(
                f"date_from ({self.date_from}) must be <= date_to ({self.date_to})"
            )
        delta = (self.date_to - self.date_from).days
        if delta > 365:
            raise ValueError(
                f"Date range spans {delta} days; maximum is 366. Split the request."
            )


@dataclass(frozen=True)
class AlmanacDay:
    """
    Full almanac for a single local calendar day at a given location.

    Wraps panchang_engine.Panchang and adds provenance metadata required
    by the Brahmagyan contract.

    Five angas (panchanga limbs)
    ----------------------------
    tithi       : tithi name + ordinal (1..30) + end_utc
    vara        : weekday (Hindu sunrise-to-sunrise convention) + end_utc
    nakshatra   : moon nakshatra + ordinal (1..27) + end_utc
    yoga        : yoga name + ordinal (1..27) + end_utc
    karana      : first karana at sunrise + end_utc

    Day-quality windows
    -------------------
    choghadiya  : {"day": [8 × Timing], "night": [8 × Timing]}
    hora        : list of 24 planetary hours (Timing objects)
    rahu_kalam  : Timing — inauspicious period (Rahu Kalam)
    gulika_kalam: Timing — inauspicious period (Gulika Kalam)
    yamagandam  : Timing — inauspicious period (Yamagandam)
    special_yogas: list of yoga dicts (Sarvartha Siddhi, Ravi Pushya, etc.)

    Provenance
    ----------
    location            : AlmanacLocation used (with normalized coordinates)
    tz_offset_minutes   : UTC offset in minutes used for THIS date's computation
                          (changes across DST transitions)
    computation_version : panchang_engine version string
    ephemeris_version   : swisseph version string
    source              : "engine" (computed on-demand)
    """
    # Date + location
    date: date
    location: AlmanacLocation
    tz_offset_minutes: int      # resolved for this specific date (handles DST)

    # Sunrise / sunset (UTC-aware)
    sunrise_utc: datetime
    sunset_utc: datetime
    moonrise_utc: Optional[datetime]
    moonset_utc: Optional[datetime]

    # Five angas
    tithi: dict          # {id, name, end_utc_iso, paksha}
    vara: dict           # {id, name, end_utc_iso}
    nakshatra: dict      # {id, name, end_utc_iso, pada}
    yoga: dict           # {id, name, end_utc_iso}
    karana: dict         # {id, name, end_utc_iso}  ← first karana at sunrise

    # Day-quality windows
    choghadiya: dict              # {"day": [...], "night": [...]}
    hora: list                    # [24 × {label, start_utc_iso, end_utc_iso}]
    rahu_kalam: Optional[dict]    # {label, start_utc_iso, end_utc_iso}
    gulika_kalam: Optional[dict]  # {label, start_utc_iso, end_utc_iso}
    yamagandam: Optional[dict]    # {label, start_utc_iso, end_utc_iso}
    special_yogas: list           # [yoga_dict, ...]

    # Provenance
    computation_version: str
    ephemeris_version: str
    source: str = "engine"        # "engine" | "cache" (set by cache layer)
