"""Ephemeris at an instant: two read paths, one convention, one memo cache.

Path `swiss_instant` computes sidereal positions at the requested JD through
the kernel's Swiss seam (`calc_sidereal_lon_speed`: FLG_SWIEPH|FLG_SIDEREAL,
mean node, Moon file probe). Path `daily_row` reads one stored daily row
(the `ephemeris_daily` shape: tropical longitude and speed per body) at its
own abscissa, noon UT, and converts with the per-instant ayanāṃśa. A daily row
answers only its own instant; it is never shifted or interpolated.

Every answer names its JD and time scale, backend, flags, node model,
ayanāṃśa id and value, convention id and coverage. Missing backend data is
`information_unavailable`; a Moshier number is never substituted.
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date, timedelta
from math import isfinite
from typing import Callable, Mapping

import swisseph as swe

from brahmagyan.l0_ephemeris import AYANAMSHA_MAP
from panchang_engine.lagna import compute_lagna
from services.gochara_kernel import knots as _knots
from services.gochara_kernel.convention import canonical_convention_id
from services.gochara_kernel.substrate import jd_to_utc
from services.kala_core.ayanamsha import CANONICAL_AYANAMSHA, sidereal_offset
from services.kala_core.vocab import NullReason

from .coverage import SkyCoverage, SkyResult, coverage_of, unavailable
from .identity import kernel_body

TIME_SCALE = "UT"
SWISS_INSTANT = "swiss_instant"
DAILY_ROW = "daily_row"
BACKEND_SWIEPH = "swieph"
EPHE_FLAGS = _knots.EPHE_FLAGS | swe.FLG_SPEED
EPHE_FLAG_NAMES = "FLG_SWIEPH|FLG_SIDEREAL|FLG_SPEED"
NODE_MODELS = ("mean", "true")
NINE_GRAHAS = _knots.NINE_GRAHAS

# The pinned .se1 corpus (sepl_18, semo_18, seas_18) spans 1800-01-01 to
# 2400-01-01 UT; outside it Swiss would fall back to Moshier.
SWISS_FILE_INTERVAL_JD = (2378496.5, 2597641.5)

# ephemeris_daily rows sit at noon UT (the kernel's F-15 knot abscissa).
DAILY_ROW_EPOCH_HOURS_UT = 12.0
# JD of a calendar date at 00:00 UT = proleptic ordinal + this offset.
_ORDINAL_TO_JD_MIDNIGHT = 1721424.5
# A request "at" a row's abscissa: one millisecond of JD slack for float input.
ROW_INSTANT_TOLERANCE_DAYS = 1e-3 / 86400.0
# The two paths' frames differ by nutation in longitude (|Δψ| ≤ 17.3″: the
# Swiss sidereal flag versus tropical minus the mean ayanāṃśa); stored
# rounding adds well under a second.
PATH_AGREEMENT_ARCSEC = 20.0


@dataclass(frozen=True)
class SkyConvention:
    ayanamsha_id: str = CANONICAL_AYANAMSHA
    node_model: str = "mean"

    def __post_init__(self) -> None:
        if self.ayanamsha_id not in AYANAMSHA_MAP:
            raise ValueError(f"unknown L1 ayanamsha id: {self.ayanamsha_id!r}")
        if self.node_model not in NODE_MODELS:
            raise ValueError(f"unknown node model: {self.node_model!r}")

    @property
    def convention_id(self) -> str:
        vector = {"ayanamsha": self.ayanamsha_id, "node_model": self.node_model,
                  "time_scale": TIME_SCALE, "flags": EPHE_FLAG_NAMES,
                  "kernel": canonical_convention_id()}
        text = json.dumps(vector, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()

    @property
    def computable(self) -> bool:
        """The kernel seam computes Lahiri sidereal positions with the mean node."""
        return (AYANAMSHA_MAP[self.ayanamsha_id] == swe.SIDM_LAHIRI
                and self.node_model == "mean")


@dataclass(frozen=True)
class BodyPosition:
    body: str
    longitude_deg: float        # sidereal, [0, 360)
    speed_deg_per_day: float


@dataclass(frozen=True)
class EphemerisAnswer:
    jd: float
    time_scale: str
    path: str
    backend: str
    flags: int
    flag_names: str
    node_model: str
    ayanamsha_id: str
    ayanamsha_deg: float
    convention_id: str
    positions: tuple[BodyPosition, ...]

    def position(self, body: str) -> BodyPosition:
        name = kernel_body(body)
        return next(p for p in self.positions if p.body == name)


@dataclass(frozen=True)
class DailyRow:
    """One stored day of tropical positions, as `ephemeris_daily` holds them."""

    day: date
    tropical: Mapping[str, tuple[float, float]]    # body -> (longitude, speed)
    backend: str                                   # the backend that computed the row
    node_model: str


def row_jd(day: date) -> float:
    return day.toordinal() + _ORDINAL_TO_JD_MIDNIGHT + DAILY_ROW_EPOCH_HOURS_UT / 24.0


class EphemerisCache:
    """LRU memo keyed by (path, JD, convention id, bodies)."""

    def __init__(self, maxsize: int = 4096) -> None:
        self.maxsize = maxsize
        self.computes = 0
        self._store: OrderedDict[tuple, SkyResult] = OrderedDict()

    @staticmethod
    def key(path: str, jd: float, convention: SkyConvention, bodies: tuple[str, ...]) -> tuple:
        return (path, float(jd), convention.convention_id, bodies)

    def get_or_compute(self, key: tuple, compute: Callable[[], SkyResult]) -> SkyResult:
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key]
        self.computes += 1
        result = compute()
        if result.available:
            self._store[key] = result
            if len(self._store) > self.maxsize:
                self._store.popitem(last=False)
        return result


def _instant_coverage(jd: float, source, backend: str, convention: SkyConvention) -> SkyCoverage:
    return coverage_of((jd, jd), source, backend=backend, convention_id=convention.convention_id)


def _answer(jd: float, path: str, backend: str, convention: SkyConvention,
            offset: float, positions: list[BodyPosition], source) -> SkyResult[EphemerisAnswer]:
    answer = EphemerisAnswer(
        jd=jd, time_scale=TIME_SCALE, path=path, backend=backend, flags=EPHE_FLAGS,
        flag_names=EPHE_FLAG_NAMES, node_model=convention.node_model,
        ayanamsha_id=convention.ayanamsha_id, ayanamsha_deg=offset,
        convention_id=convention.convention_id, positions=tuple(positions))
    return SkyResult((answer,), _instant_coverage(jd, source, backend, convention))


def _bodies(bodies) -> tuple[str, ...]:
    return tuple(kernel_body(b) for b in bodies)


def ephemeris_at(jd: float, convention: SkyConvention = SkyConvention(), *,
                 bodies=NINE_GRAHAS, ephe_path: str | None = None,
                 cache: EphemerisCache | None = None) -> SkyResult[EphemerisAnswer]:
    """Sidereal positions at a UT Julian day through the Swiss seam."""
    jd = float(jd)
    if not isfinite(jd):
        raise ValueError("jd must be finite")
    names = _bodies(bodies)

    def compute() -> SkyResult[EphemerisAnswer]:
        if not convention.computable:
            return unavailable(_instant_coverage(jd, SWISS_FILE_INTERVAL_JD, BACKEND_SWIEPH,
                                                 convention), NullReason.METHOD_INAPPLICABLE)
        coverage = _instant_coverage(jd, SWISS_FILE_INTERVAL_JD, BACKEND_SWIEPH, convention)
        if coverage.covered is None:
            return unavailable(coverage)
        try:
            positions = []
            for name in names:
                lon, speed, retflag = _knots.calc_sidereal_lon_speed(name, jd, ephe_path)
                _knots._check_retflag(name, retflag)
                positions.append(BodyPosition(name, lon % 360.0, speed))
            offset = sidereal_offset(jd, convention.ayanamsha_id)
        except (_knots.EphemerisBackendError, RuntimeError):
            return unavailable(_instant_coverage(jd, None, BACKEND_SWIEPH, convention))
        return _answer(jd, SWISS_INSTANT, BACKEND_SWIEPH, convention, offset, positions,
                       SWISS_FILE_INTERVAL_JD)

    if cache is None:
        return compute()
    return cache.get_or_compute(EphemerisCache.key(SWISS_INSTANT, jd, convention, names), compute)


def ephemeris_from_row(row: DailyRow, jd: float, convention: SkyConvention = SkyConvention(),
                       *, bodies=NINE_GRAHAS,
                       cache: EphemerisCache | None = None) -> SkyResult[EphemerisAnswer]:
    """Sidereal positions from one stored daily row, at the row's own instant only."""
    jd = float(jd)
    names = _bodies(bodies)
    at = row_jd(row.day)
    source = (at, at + 1.0 / 86400.0)    # the row's single instant

    def compute() -> SkyResult[EphemerisAnswer]:
        backend = row.backend or "undeclared"
        if abs(jd - at) > ROW_INSTANT_TOLERANCE_DAYS or not row.backend \
                or any(name not in row.tropical for name in names):
            return unavailable(_instant_coverage(jd, None, backend, convention))
        if row.node_model != convention.node_model:
            return unavailable(_instant_coverage(at, source, backend, convention),
                               NullReason.METHOD_INAPPLICABLE)
        try:
            offset = sidereal_offset(at, convention.ayanamsha_id)
        except RuntimeError:
            return unavailable(_instant_coverage(jd, None, backend, convention))
        positions = [BodyPosition(name, (row.tropical[name][0] - offset) % 360.0,
                                  float(row.tropical[name][1])) for name in names]
        return _answer(at, DAILY_ROW, backend, convention, offset, positions, source)

    if cache is None:
        return compute()
    return cache.get_or_compute(EphemerisCache.key(DAILY_ROW, jd, convention, names), compute)


# ── local answers: location and civil time are part of the answer ────────────

@dataclass(frozen=True)
class GeoLocation:
    latitude_deg: float
    longitude_deg: float

    def __post_init__(self) -> None:
        if not (isfinite(self.latitude_deg) and -90.0 <= self.latitude_deg <= 90.0):
            raise ValueError("latitude_deg must lie in [-90, 90]")
        if not (isfinite(self.longitude_deg) and -180.0 <= self.longitude_deg <= 180.0):
            raise ValueError("longitude_deg must lie in [-180, 180]")


@dataclass(frozen=True)
class CivilTime:
    zone: str                   # IANA zone name the caller's clock follows
    utc_offset_minutes: int     # the offset in force at the instant

    def __post_init__(self) -> None:
        if not self.zone:
            raise ValueError("civil time must name its zone")


@dataclass(frozen=True)
class LocalAnswer:
    kind: str
    jd: float
    time_scale: str
    local_time: str
    location: GeoLocation
    civil_time: CivilTime
    longitude_deg: float
    backend: str
    flags: int
    flag_names: str
    node_model: str
    ayanamsha_id: str
    ayanamsha_deg: float
    convention_id: str
    extra: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.location, GeoLocation):
            raise TypeError("a local answer names its location")
        if not isinstance(self.civil_time, CivilTime):
            raise TypeError("a local answer names its civil-time convention")


LAGNA_BACKEND = "swiss_houses"
# compute_lagna calls swe.houses_ex(jd, lat, lon, b"P") with no iflag (tropical
# Placidus) and subtracts swe.get_ayanamsa_ut under SIDM_LAHIRI.
LAGNA_FLAGS = 0
LAGNA_FLAG_NAMES = "houses_ex:tropical|hsys=P|minus_ayanamsa_ut:SIDM_LAHIRI"


def lagna_at(jd: float, location: GeoLocation, civil_time: CivilTime,
             convention: SkyConvention = SkyConvention()) -> SkyResult[LocalAnswer]:
    """The sidereal ascendant at a UT Julian day for a place."""
    jd = float(jd)
    coverage = _instant_coverage(jd, SWISS_FILE_INTERVAL_JD, LAGNA_BACKEND, convention)
    if not convention.computable:
        return unavailable(coverage, NullReason.METHOD_INAPPLICABLE)
    if coverage.covered is None:
        return unavailable(coverage)
    local = jd_to_utc(jd).replace(tzinfo=None) + timedelta(minutes=civil_time.utc_offset_minutes)
    state = compute_lagna(local, location.latitude_deg, location.longitude_deg,
                          civil_time.utc_offset_minutes)
    answer = LocalAnswer(
        kind="lagna", jd=jd, time_scale=TIME_SCALE, local_time=local.isoformat(),
        location=location, civil_time=civil_time, longitude_deg=state.ascendant_deg,
        backend=LAGNA_BACKEND, flags=LAGNA_FLAGS, flag_names=LAGNA_FLAG_NAMES,
        node_model=convention.node_model, ayanamsha_id=convention.ayanamsha_id,
        ayanamsha_deg=sidereal_offset(jd, convention.ayanamsha_id),
        convention_id=convention.convention_id, extra={"mc_deg": state.mc_deg})
    return SkyResult((answer,), coverage)


__all__ = [
    "BodyPosition", "CivilTime", "DAILY_ROW", "DailyRow", "EphemerisAnswer",
    "EphemerisCache", "GeoLocation", "LocalAnswer", "NINE_GRAHAS",
    "PATH_AGREEMENT_ARCSEC", "SWISS_FILE_INTERVAL_JD", "SWISS_INSTANT", "SkyConvention",
    "ephemeris_at", "ephemeris_from_row", "lagna_at", "row_jd",
]
