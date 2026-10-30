"""Rule Book engine (E3) — the natal operands one chart supplies.

``NatalChart`` is plain data. Every field may be ``None`` (a fact that was
missing, non-unique or outside its vocabulary): a resolver turns a ``None`` into
NOT_ASSESSED, never into FALSE (Q1, M10). The DB loader (``dbload``) and the
JSON fixture reader here both produce it; nothing in this module touches a
database.

Houses are whole-sign. ``lagna_sign`` and the graha signs are 1..12 (Aries=1).
``aspected_houses`` are the absolute houses (counted from the lagna) the L1
``aspect_parashari_given`` rows list. ``house_lords`` is the D1 lord of each
house (L1 ``lord_in_house_per_varga``); the lord of a sign is read from it, so no
sign-lordship table is hard-coded here (§N.7.3).
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence

from . import constants as K


class ChartDataError(ValueError):
    """The chart data is structurally unusable (not merely missing a fact)."""


def utc_to_jd(dt: datetime) -> float:
    if dt.tzinfo is None:
        raise ChartDataError("naive datetime: UTC instants must carry tzinfo")
    return K.JD_UNIX_EPOCH + dt.astimezone(timezone.utc).timestamp() / K.SECONDS_PER_DAY


def parse_utc(text: str) -> datetime:
    t = text.strip()
    if t.endswith("Z"):
        t = t[:-1] + "+00:00"
    dt = datetime.fromisoformat(t)
    if dt.tzinfo is None:
        raise ChartDataError(f"timestamp without a zone: {text!r}")
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class Birth:
    birth_date: date
    birth_time_local: str  # HH:MM[:SS]
    lat: float
    lon: float
    zone: Optional[str]
    birth_utc: Optional[datetime] = None  # filled by the day-atom module once the zone is validated
    # Explicit-offset path (foreign births): the UT offset the SOURCE RECORD states, in minutes east of UT.
    # When set, ``birth_utc`` is local time minus this offset and no zone name is needed or consulted.
    utc_offset_minutes: Optional[int] = None
    utc_offset_seconds: Optional[int] = None  # mean-time (meridian-form) records only (v1.6 Q1)

    def to_json(self) -> dict:
        return {
            "birth_date": self.birth_date.isoformat(),
            "birth_time_local": self.birth_time_local,
            "lat": self.lat,
            "lon": self.lon,
            "zone": self.zone,
            "birth_utc": self.birth_utc.isoformat() if self.birth_utc else None,
            "utc_offset_minutes": self.utc_offset_minutes,
            "utc_offset_seconds": self.utc_offset_seconds,
        }


@dataclass
class GrahaFacts:
    sign: Optional[int] = None
    retrograde: Optional[bool] = None
    exalted: Optional[bool] = None
    debilitated: Optional[bool] = None
    dignity_state: Optional[str] = None  # L1 D1 dignity_state vocabulary; None if absent
    longitude: Optional[float] = None  # L1 sidereal longitude (degrees); used only by the birth-instant guards


@dataclass
class DashaRow:
    lord: str  # card graha name
    start_jd: float
    end_jd: float


class DashaLevel:
    """One daśā level as a half-open interval table [start, end) in UT.

    The table must be time-ordered and gap-free; a gap or overlap makes the
    instants around it unknown (NOT_ASSESSED) and is counted, never papered over.
    """

    def __init__(self, rows: Sequence[DashaRow], tolerance_days: float = 1.5 / K.SECONDS_PER_DAY):
        self.rows: List[DashaRow] = sorted(rows, key=lambda r: r.start_jd)
        self._starts = [r.start_jd for r in self.rows]
        self.tolerance_days = tolerance_days
        self.defects = 0
        for r in self.rows:
            if not r.end_jd > r.start_jd:
                raise ChartDataError("daśā row with end <= start")
        for a, b in zip(self.rows, self.rows[1:]):
            if b.start_jd < a.end_jd - tolerance_days:
                raise ChartDataError("overlapping daśā rows in one level")
            if b.start_jd > a.end_jd + tolerance_days:
                self.defects += 1  # a gap: instants inside it are unknown

    @property
    def first_jd(self) -> Optional[float]:
        return self.rows[0].start_jd if self.rows else None

    @property
    def last_jd(self) -> Optional[float]:
        return self.rows[-1].end_jd if self.rows else None

    def lord_at(self, jd: float) -> Optional[str]:
        if not self.rows:
            return None
        i = bisect_right(self._starts, jd) - 1
        if i < 0:
            return None
        row = self.rows[i]
        return row.lord if jd < row.end_jd else None


@dataclass
class NatalChart:
    chart_key: str
    birth: Birth
    lagna_sign: Optional[int]
    grahas: Dict[str, GrahaFacts]
    aspected_houses: Dict[str, Optional[FrozenSet[int]]]
    house_lords: Dict[int, Optional[str]]
    md: DashaLevel
    ad: DashaLevel
    ledger: Dict[str, List[str]] = field(default_factory=dict)  # kind -> fact ids / row ids consumed
    diagnostics: Dict[str, int] = field(default_factory=dict)

    # accessors ------------------------------------------------------------------
    def graha(self, g: str) -> GrahaFacts:
        return self.grahas.get(g) or GrahaFacts()

    def sign_of(self, g: str) -> Optional[int]:
        return self.graha(g).sign

    def sign_of_house(self, house: int) -> Optional[int]:
        if self.lagna_sign is None:
            return None
        return (self.lagna_sign + house - 2) % 12 + 1

    def sign_lord(self, sign: Optional[int]) -> Optional[str]:
        """Lord of a sign, read from this chart's own D1 house-lord rows."""
        if sign is None or self.lagna_sign is None:
            return None
        house = (sign - self.lagna_sign) % 12 + 1
        return self.house_lords.get(house)

    def aspected_signs(self, g: str) -> Optional[FrozenSet[int]]:
        hs = self.aspected_houses.get(g)
        if hs is None or self.lagna_sign is None:
            return None
        return frozenset((self.lagna_sign + h - 2) % 12 + 1 for h in hs)

    def own_sign(self, g: str) -> Optional[bool]:
        """TRUE iff the graha occupies a sign it rules (lordship read from the chart's own D1 rows).

        The L1 dignity state is a cross-check only: a state of 'own' where the
        lordship says otherwise, or a 'neutral'/'debilitated' state where it says own,
        is a disagreement between two L1 facts and reads NOT_ASSESSED.
        """
        gf = self.graha(g)
        lord = self.sign_lord(gf.sign)
        if lord is None:
            return None
        by_lord = lord == g
        st = gf.dignity_state
        if st is None:
            return by_lord
        if (st == "own" and not by_lord) or (st in ("neutral", "debilitated") and by_lord):
            self.diagnostics["own_sign_fact_disagreement"] = self.diagnostics.get("own_sign_fact_disagreement", 0) + 1
            return None
        return by_lord


def readiness(chart: NatalChart) -> List[str]:
    """Problems that will turn into NOT_ASSESSED for this chart (empty list = every operand the engine reads is present)."""
    out: List[str] = []
    if chart.lagna_sign is None:
        out.append("lagna sign missing")
    for g in K.GRAHAS:
        if chart.graha(g).sign is None:
            out.append(f"{g}: natal sign missing")
        if g not in K.NODES:
            gf = chart.graha(g)
            for fld in ("retrograde", "exalted", "debilitated"):
                if getattr(gf, fld) is None:
                    out.append(f"{g}: {fld} flag missing")
    for g in K.GRAHAS:
        if chart.aspected_houses.get(g) is None:
            out.append(f"{g}: aspect rows missing")
    for h in range(1, 13):
        if chart.house_lords.get(h) is None:
            out.append(f"house {h}: D1 lord missing")
    if not chart.md.rows:
        out.append("no Vimshottari level-1 rows")
    if not chart.ad.rows:
        out.append("no Vimshottari level-2 rows")
    if chart.md.defects or chart.ad.defects:
        out.append(f"daśā gaps: level1={chart.md.defects} level2={chart.ad.defects}")
    for k, v in sorted(chart.diagnostics.items()):
        out.append(f"diagnostic {k}={v}")
    return out


def house_from(ref_sign: Optional[int], sign: Optional[int]) -> Optional[int]:
    """Whole-sign house of ``sign`` counted inclusively from ``ref_sign`` (1..12)."""
    if ref_sign is None or sign is None:
        return None
    return (sign - ref_sign) % 12 + 1


# ── JSON fixture (synthetic charts, oracle inputs, offline runs) ───────────────
def chart_from_fixture(doc: Mapping[str, Any]) -> NatalChart:
    """Build a NatalChart from the neutral fixture format (FIXTURE_SCHEMA).

    {"fixture_schema": "rulebook-engine-fixture-v1", "chart_key": str,
     "birth": {"date","time_local","lat","lon","zone","birth_utc"},
     "lagna_sign": 1..12,
     "graha": {<card graha>: {"sign","retrograde","exalted","debilitated","dignity_state"}, ... },
     "aspected_houses": {<card graha>: [absolute houses from lagna]},
     "house_lord": {"1": <card graha>, ... "12": ...},
     "dasha": {"mahadasha": [{"lord","start_utc","end_utc"}], "antardasha": [...]}}
    Any key may be omitted or null: the fact is then missing (NOT_ASSESSED).
    """
    if doc.get("fixture_schema") != K.FIXTURE_SCHEMA:
        raise ChartDataError(f"fixture_schema must be {K.FIXTURE_SCHEMA!r}")
    b = doc.get("birth") or {}
    birth = Birth(
        birth_date=date.fromisoformat(b["date"]),
        birth_time_local=str(b.get("time_local") or ""),
        lat=float(b["lat"]),
        lon=float(b["lon"]),
        zone=b.get("zone"),
        birth_utc=parse_utc(b["birth_utc"]) if b.get("birth_utc") else None,
        utc_offset_minutes=b.get("utc_offset_minutes"),
    )
    grahas: Dict[str, GrahaFacts] = {}
    for g, f in (doc.get("graha") or {}).items():
        if g not in K.GRAHAS:
            raise ChartDataError(f"unknown graha {g!r}")
        f = f or {}
        grahas[g] = GrahaFacts(
            sign=_sign(f.get("sign")),
            retrograde=_opt_bool(f.get("retrograde")),
            exalted=_opt_bool(f.get("exalted")),
            debilitated=_opt_bool(f.get("debilitated")),
            dignity_state=f.get("dignity_state"),
            longitude=f.get("longitude"),
        )
    asp: Dict[str, Optional[FrozenSet[int]]] = {}
    for g, hs in (doc.get("aspected_houses") or {}).items():
        asp[g] = None if hs is None else frozenset(int(h) for h in hs)
    lords: Dict[int, Optional[str]] = {}
    for k, v in (doc.get("house_lord") or {}).items():
        lords[int(k)] = v
    das = doc.get("dasha") or {}
    return NatalChart(
        chart_key=str(doc.get("chart_key") or "fixture"),
        birth=birth,
        lagna_sign=_sign(doc.get("lagna_sign")),
        grahas=grahas,
        aspected_houses=asp,
        house_lords=lords,
        md=_dasha_level(das.get("mahadasha") or []),
        ad=_dasha_level(das.get("antardasha") or []),
    )


def _sign(v: Any) -> Optional[int]:
    if v is None:
        return None
    if not isinstance(v, int) or isinstance(v, bool) or not 1 <= v <= 12:
        raise ChartDataError(f"sign must be an int 1..12, got {v!r}")
    return v


def _opt_bool(v: Any) -> Optional[bool]:
    if v is None:
        return None
    if not isinstance(v, bool):
        raise ChartDataError(f"expected bool or null, got {v!r}")
    return v


def _dasha_level(rows: Sequence[Mapping[str, Any]]) -> DashaLevel:
    out = []
    for r in rows:
        if r["lord"] not in K.GRAHAS:
            raise ChartDataError(f"daśā lord {r['lord']!r} is not a card graha name")
        out.append(DashaRow(r["lord"], utc_to_jd(parse_utc(r["start_utc"])), utc_to_jd(parse_utc(r["end_utc"]))))
    return DashaLevel(out)
