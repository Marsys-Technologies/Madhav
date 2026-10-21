"""P1 nature operands and the per-instant side/valence of a period lord (SR-OD1 P1B; plan §3.3, N-3, N-9).

What this module supplies to the window sweep (through W0's `OperandSource`, never through a sweep edit):

  * `NatureOperands` — the lord's natural nature AT t from the sky, by the L2 rule authority `gochara_rules.nature.agent_nature`
    (BPHS 3.11, bphs:PG26:C1 [V]): the Sun, Saturn, Mars, Rāhu and Ketu are malefic, Jupiter and Venus benefic; the Moon is
    malefic while waning (Sun-Moon elongation past 180 degrees) and benefic while waxing; Mercury is malefic iff it shares a SIGN
    with a malefic ("joined" = same sign, ND Q4 x; the waning Moon counts as a malefic at that instant) and benefic otherwise.
    Its CHANGE INSTANTS are found from the ephemeris alone: the Moon's elongation crossings of 0/180 degrees; for Mercury every
    instant at which Mercury, the Sun, Mars, Saturn, Rāhu, Ketu change sign, the Moon enters or leaves Mercury's sign, or the
    Moon's pakṣa flips. The search is `contact_reconstruct._core` (speed-bounded, named limit `contact_reconstruct.NAMED_LIMIT`);
    its answers are memoised per aligned chunk when the position source declares a `cache_key`.
  * `P1LordValence` — the lord's side and value at t: `p1_valence.LordRungRules` gives the effective rung (COMB > EX > MT > OWN >
    DEB > FR/NEU/INI) and the validated `SideValueMapping` (Form B, the registry's `category_mapping`) gives (side, value) for
    (nature, rung). Exactly ONE factor decides the side (W0 refuses two): the side — default by nature, overridden at the extremes
    the rung names — is the `agent_nature` source's `channel_at`; the VALUE is the table value, carried by the dignity factor's
    source; `agent_nature` itself has magnitude 1 and the combustion factor the declared neutral 1.0, so the within-path product
    equals the table (ANSWERS §B.2).

NOT here: the values (they are the row's `category_mapping`, D2), the dignity / combustion operand sources and their boundaries
(P1a — they arrive as the injected `combust_at`, `rung_boundaries`), the verifier-side derivation (P1c: independent, from the spec).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable

from services.gochara_rules import nature as _nature
from services.gochara_rules import p1_valence as _pv
from services.gochara_rules.p1_inputs import GRAHAS, NEVER_COMBUST, SIGNS
from services.gochara_rules.score import channel_for

from . import contact_reconstruct as _cr
from .window_sweep import OperandSource

#: the bodies whose sign-sharing with Mercury makes Mercury malefic, besides the waning Moon (BPHS 3.11)
_MALEFIC_COMPANIONS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
STATIC_NATURE = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu", "Jupiter", "Venus"})
REASON_POSITION_UNAVAILABLE = "p1_lord_position_unavailable"
REASON_COMBUSTION_UNAVAILABLE = "p1_combustion_state_undeterminable"

# Aligned chunking for the memo: a multiple of `contact_reconstruct.STEP_SECONDS` so the step lattice never straddles a chunk.
_CHUNK = timedelta(days=96)
_EPOCH = datetime(1900, 1, 1, tzinfo=timezone.utc)
_MEMO: dict = {}


def _sign(lon: float) -> int:
    return int((lon % 360.0) // 30.0)


def _edge_to_sign_edges(lon: float, sign: int) -> float:
    """Angular distance from `lon` to the nearest of the two edges of zodiac sign `sign`."""
    return min(_cr._angdiff(lon, sign * 30.0), _cr._angdiff(lon, (sign + 1) * 30.0))


class NatureOperands:
    """The natural nature of `graha` at t, and the instants it changes, from `position_at(body, t)` (sidereal longitude)."""

    def __init__(self, graha: str, position_at: Callable[[str, datetime], float | None]):
        if graha not in GRAHAS:
            raise ValueError(f"unknown graha {graha!r}")
        self.graha = graha
        self.position_at = position_at
        self.static = graha in STATIC_NATURE

    # ── the value at t ──
    def _lon(self, body: str, t: datetime) -> float | None:
        v = self.position_at(body, t)
        return None if v is None else float(v)

    def nature_at(self, t: datetime) -> str | None:
        """'benefic' | 'malefic', or None when an operand it needs is undeterminable at t (never a default side)."""
        g = self.graha
        if self.static:
            return _nature.agent_nature(g)
        if g == "Moon":
            sun, moon = self._lon("Sun", t), self._lon("Moon", t)
            if sun is None or moon is None:
                return None
            return _nature.agent_nature("Moon", sun_lon=sun, moon_lon=moon)
        if g == "Mercury":
            joined = self.mercury_joined_at(t)
            return None if joined is None else _nature.agent_nature("Mercury", joined_to_malefic=joined)
        raise ValueError(f"no nature rule for {g!r}")

    def mercury_joined_at(self, t: datetime) -> bool | None:
        """True iff Mercury shares a sign with the Sun, Mars, Saturn, Rāhu, Ketu or the WANING Moon at t (None = undeterminable)."""
        merc = self._lon("Mercury", t)
        sun = self._lon("Sun", t)
        moon = self._lon("Moon", t)
        if merc is None or sun is None or moon is None:
            return None
        ms = _sign(merc)
        for body in _MALEFIC_COMPANIONS:
            lon = sun if body == "Sun" else self._lon(body, t)
            if lon is None:
                return None
            if _sign(lon) == ms:
                return True
        return _nature.moon_paksa(sun, moon) == "waning" and _sign(moon) == ms

    # ── the change instants ──
    def boundaries(self, lo: datetime, hi: datetime) -> list[datetime]:
        """The instants in (lo, hi) at which this lord's natural nature may change (a SUPERSET is allowed — an extra cut is
        harmless; a missing one is not). Empty for a graha whose nature is fixed."""
        if self.static or not lo < hi:
            return []
        out: list[datetime] = []
        k = int((lo - _EPOCH) / _CHUNK)
        while _EPOCH + k * _CHUNK < hi:
            out.extend(self._chunk(k))
            k += 1
        return sorted(c for c in set(out) if lo < c < hi)

    def _chunk(self, k: int) -> list[datetime]:
        c0, c1 = _EPOCH + k * _CHUNK, _EPOCH + (k + 1) * _CHUNK
        key = getattr(self.position_at, "cache_key", None)
        memo_key = None if key is None else (key, self.graha, k)
        if memo_key is not None and memo_key in _MEMO:
            return _MEMO[memo_key]
        found = self._changes(c0, c1)
        if memo_key is not None:
            _MEMO[memo_key] = found
        return found

    def _changes(self, lo: datetime, hi: datetime) -> list[datetime]:
        src = {b: _cr._lon_source(self.position_at, b) for b in ("Sun", "Moon", "Mercury") + _MALEFIC_COMPANIONS}
        sun, moon = src["Sun"], src["Moon"]
        vmoon, vsun = _cr.VMAX_DPS["moon"], _cr.VMAX_DPS["sun"]

        def paksa(t):
            return _nature.moon_paksa(sun(t), moon(t))

        def paksa_edge_deg(t):
            e = (moon(t) - sun(t)) % 360.0
            return min(e % 180.0, 180.0 - e % 180.0)

        if self.graha == "Moon":
            return _cr._core(paksa, paksa_edge_deg, vmoon + vsun, lo, hi)

        merc = src["Mercury"]

        def joined(t):
            ms = _sign(merc(t))
            if any(_sign(src[b](t)) == ms for b in _MALEFIC_COMPANIONS):
                return True
            return paksa(t) == "waning" and _sign(moon(t)) == ms

        def days_to_event(t):
            """A lower bound, in days, on the time until ANY operand of `joined` can change state: each body's distance to
            its sign edges over its speed bound; the Moon's distance to the edges of MERCURY's sign (it matters only where
            it enters or leaves that sign) over its speed bound; the pakṣa edge over the Sun-Moon relative speed bound."""
            ms = _sign(merc(t))
            d = [_edge_to_sign_edges(merc(t), ms) / _cr.VMAX_DPS["mercury"], paksa_edge_deg(t) / (vmoon + vsun),
                 _edge_to_sign_edges(moon(t), ms) / vmoon]
            for b in _MALEFIC_COMPANIONS:
                lon = src[b](t)
                d.append(_edge_to_sign_edges(lon, _sign(lon)) / _cr.VMAX_DPS[b.lower()])
            return min(d)

        # `_core` compares edge_distance with vmax*dt; vmax = 1 deg/day and a distance expressed in DAYS make that "time to
        # the nearest possible change > dt"
        return _cr._core(joined, days_to_event, 1.0, lo, hi)


@dataclass(frozen=True)
class LordValence:
    """The determinable state of the lord at one instant."""
    nature: str
    rung: str
    side: str
    value: float
    disclosures: tuple = ()


class P1LordValence:
    """The period lord's side and value at t, and the `OperandSource`s that carry them to the sweep.

    graha / event_class   the lord (Title case) and the class whose polarity turns a side into a channel (`score.channel_for`)
    mapping               the validated `SideValueMapping` (the registry row's `category_mapping`)
    rules                 `p1_valence.LordRungRules` for this lord (validated L0 rows)
    nature                `NatureOperands` for this lord
    position_at           the sidereal-longitude source (the lord's sign and degree)
    combust_at            t -> bool | None: the L1 combustion state (P1a's source). Required for a combustible lord; the Sun and
                          the nodes are a declared non-applicability
    rung_boundaries       (lo, hi) -> instants at which the rung (sign ingress, mūlatrikoṇa degree edges, combustion edges) may
                          change (P1a's provider). None ⇒ the sources assert NO completeness and the record is blank
                          (`state_boundaries_incomplete`) rather than numbered on a guess
    """

    def __init__(self, *, graha: str, event_class: str, mapping: _pv.SideValueMapping, rules: _pv.LordRungRules,
                 nature: NatureOperands, position_at, combust_at: Callable[[datetime], bool | None] | None = None,
                 rung_boundaries: Callable[[datetime, datetime], list[datetime]] | None = None):
        if rules.graha != graha or nature.graha != graha:
            raise ValueError("rules / nature operands belong to a different lord")
        if graha not in NEVER_COMBUST and combust_at is None:
            raise ValueError(f"{graha} is combustible: a combustion operand (combust_at) is required, none is defaulted")
        self.graha, self.event_class, self.mapping, self.rules = graha, event_class, mapping, rules
        self.nature, self.position_at, self.combust_at, self.rung_boundaries = nature, position_at, combust_at, rung_boundaries

    # ── the state at t ──
    def state_at(self, t: datetime) -> LordValence | str:
        """The lord's `LordValence` at t, or the NAMED reason it cannot be determined (a string)."""
        lon = self.position_at(self.graha, t)
        if lon is None:
            return REASON_POSITION_UNAVAILABLE
        if self.graha in NEVER_COMBUST:
            combust = False
        else:
            combust = self.combust_at(t)
            if combust is None:
                return REASON_COMBUSTION_UNAVAILABLE
        lon = float(lon) % 360.0
        res = self.rules.rung(SIGNS[_sign(lon)], lon % 30.0, combust)
        if res.rung is None:
            return res.reason
        nat = self.nature.nature_at(t)
        if nat is None:
            return REASON_POSITION_UNAVAILABLE
        side, value = self.mapping.side_and_value(nat, res.rung)
        return LordValence(nat, res.rung, side, value, res.disclosures)

    def channel_at(self, t: datetime) -> str | None:
        s = self.state_at(t)
        return None if isinstance(s, str) else channel_for(s.side, self.event_class)

    def value_at(self, t: datetime) -> float | None:
        s = self.state_at(t)
        return None if isinstance(s, str) else s.value

    def unknown_reason(self, t: datetime) -> str | None:
        s = self.state_at(t)
        return s if isinstance(s, str) else None

    # ── the change instants ──
    def boundaries(self, lo: datetime, hi: datetime) -> list[datetime]:
        cuts = set(self.nature.boundaries(lo, hi))
        if self.rung_boundaries is not None:
            cuts.update(c for c in self.rung_boundaries(lo, hi) if lo < c < hi)
        return sorted(cuts)

    @property
    def complete(self) -> bool:
        """Whether the combined list is complete: the nature list is (under `contact_reconstruct.NAMED_LIMIT`); the rung's
        only if a rung provider was supplied."""
        return self.rung_boundaries is not None

    # ── the sources the sweep reads ──
    def agent_nature_source(self) -> OperandSource:
        """`agent_nature`: DECIDES THE SIDE per instant (default by nature, overridden at the extremes the rung names); its own
        magnitude is the declared 1.0 (ANSWERS §B.2). Undeterminable ⇒ both hooks say None, with the named reason."""
        return OperandSource(
            boundaries=self.boundaries, complete=self.complete,
            value_at=lambda t: None if isinstance(self.state_at(t), str) else 1.0,
            channel_at=self.channel_at, unknown_reason=self.unknown_reason)

    def dignity_value_source(self) -> OperandSource:
        """`dignity_of_transit_sign`: the table VALUE for (nature, effective rung). It assigns no side."""
        return OperandSource(boundaries=self.boundaries, complete=self.complete, value_at=self.value_at,
                             unknown_reason=self.unknown_reason)


def declared_neutral_source() -> OperandSource:
    """`combustion` under the consolidated rule: combustion is a RUNG of the table (COMB, adverse, from the L1 state), so the
    combustion factor contributes the declared neutral element 1.0 and the product equals the table (ANSWERS §B.2). Its change
    list is empty and complete by construction: a constant has none."""
    return OperandSource(boundaries=lambda lo, hi: [], complete=True, value_at=lambda t: 1.0)


__all__ = ["LordValence", "NatureOperands", "P1LordValence", "REASON_COMBUSTION_UNAVAILABLE", "REASON_POSITION_UNAVAILABLE",
           "STATIC_NATURE", "declared_neutral_source"]
