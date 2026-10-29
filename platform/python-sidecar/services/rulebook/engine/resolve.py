"""Rule Book engine (E3) — resolve planned predicates to Kleene series, one day per sunrise.

Every resolver returns a ``Series`` of ``Tri`` over the run's days. A fact that is
missing, a coverage edge, or a node-lord day is NOT_ASSESSED, never FALSE (Q1, §N.7.6).
No resolver reads a Rāhu/Ketu position: ``body_sign`` and the natal readers refuse a
node outright, and daśā-lord readers return NOT_ASSESSED on node-lord days.

The reference semantics (Kleene tables, exceptions, the N tally) are ``..ast``'s; this
module only supplies the leaf truth values.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Optional

from ..ast import NOT_ASSESSED, Tri, k_and
from . import constants as K
from .chart import NatalChart, house_from, utc_to_jd
from .dayatom import DayGrid
from .plan import (
    BHAVA_LORD_HOUSE,
    DASHA_FLAG,
    DASHA_HOUSE,
    DASHA_IDENTITY,
    LORD_OF,
    NATAL_ASPECT,
    NATAL_CONJOIN,
    NATAL_FLAG,
    NATAL_HOUSE,
    TRANSIT_HOUSE,
    FrameSpec,
    PredPlan,
)
from .series import Series
from .sky import SkyTable


class NodeReadRefused(RuntimeError):
    """A resolver was asked for a Rāhu/Ketu position or state (DF-03 undecided)."""


def _tri(value: Optional[bool]) -> Tri:
    return NOT_ASSESSED if value is None else Tri.of(value)


class EvalContext:
    def __init__(self, chart: NatalChart, sky: SkyTable, grid: DayGrid):
        self.chart, self.sky, self.grid = chart, sky, grid
        self.n = grid.n
        self._body: Dict[str, Series] = {}
        self._lord: Dict[int, Series] = {}
        self._lord_sign: Dict[int, Series] = {}
        self._frame: Dict[str, Series] = {}
        self._pred: Dict[str, Series] = {}
        self.birth_jd: Optional[float] = utc_to_jd(chart.birth.birth_utc) if chart.birth.birth_utc else None

    # ── time-varying inputs ─────────────────────────────────────────────────
    def body_sign(self, graha: str) -> Series:
        if graha in K.NODES:
            raise NodeReadRefused(graha)
        s = self._body.get(graha)
        if s is None:
            body = K.L0_BODY[graha]
            s = Series.from_values([None if jd is None else self.sky.sign_at(body, jd) for jd in self.grid.sunrise_jd])
            self._body[graha] = s
        return s

    def lord(self, level: int) -> Series:
        s = self._lord.get(level)
        if s is None:
            table = self.chart.md if level == K.DASHA_LEVEL_MD else self.chart.ad
            vals: List[Optional[str]] = []
            for jd in self.grid.sunrise_jd:
                if jd is None:
                    vals.append(None)  # no sunrise that date: the day has no state
                elif self.birth_jd is not None and jd < self.birth_jd:
                    vals.append(None)  # before the birth instant: no daśā
                else:
                    vals.append(table.lord_at(jd))
            s = Series.from_values(vals)
            self._lord[level] = s
        return s

    def lord_sign(self, level: int) -> Series:
        """Natal sign of the daśā/antardaśā lord; None for a node lord (no node position is read) or unknown."""
        s = self._lord_sign.get(level)
        if s is None:
            s = self.lord(level).map(lambda g: None if g is None or g in K.NODES else self.chart.sign_of(g))
            self._lord_sign[level] = s
        return s

    def frame_sign(self, frame: FrameSpec) -> Series:
        k = frame.key()
        s = self._frame.get(k)
        if s is None:
            if frame.kind == "lagna":
                s = Series.const(self.n, self.chart.lagna_sign)
            elif frame.kind == "moon":
                s = Series.const(self.n, self.chart.sign_of("chandra"))
            elif frame.kind == "graha":
                if frame.graha in K.NODES:
                    raise NodeReadRefused(str(frame.graha))
                s = Series.const(self.n, self.chart.sign_of(str(frame.graha)))
            elif frame.kind == "md_lord":
                s = self.lord_sign(K.DASHA_LEVEL_MD)
            else:  # pragma: no cover - planner never emits another kind
                raise ValueError(frame.kind)
            self._frame[k] = s
        return s

    # ── predicate series ────────────────────────────────────────────────────
    def pred(self, plan: PredPlan, frame: FrameSpec) -> Series:
        sig = plan.signature(frame)
        s = self._pred.get(sig)
        if s is None:
            s = self._resolve(plan, frame)
            self._pred[sig] = s
        return s

    def _in_houses(self, targets: FrozenSet[int]):
        def fn(ref: Optional[int], sign: Optional[int]) -> Tri:
            h = house_from(ref, sign)
            return NOT_ASSESSED if h is None else Tri.of(h in targets)

        return fn

    def _resolve(self, p: PredPlan, frame: FrameSpec) -> Series:
        c, n = self.chart, self.n
        kind = p.kind
        g = p.p("graha")
        if g in K.NODES and kind not in (DASHA_IDENTITY,):
            raise NodeReadRefused(f"{p.operand_id}: {g}")
        if kind == TRANSIT_HOUSE:
            tg = frozenset(p.p("targets"))
            if 0 in tg:
                raise NodeReadRefused(f"{p.operand_id}: vedha obstructor set names a node")
            return Series.zip(self._in_houses(tg), self.frame_sign(frame), self.body_sign(g))
        if kind == NATAL_HOUSE:
            tg = frozenset(p.p("targets"))
            return Series.zip(self._in_houses(tg), self.frame_sign(frame), Series.const(n, c.sign_of(g)))
        if kind == NATAL_ASPECT:
            asp = c.aspected_signs(g)
            partner = p.p("partner")
            if partner is not None:
                if partner in K.NODES:
                    raise NodeReadRefused(f"{p.operand_id}: {partner}")
                ps = c.sign_of(partner)
                v = NOT_ASSESSED if asp is None or ps is None else Tri.of(ps in asp)
                return Series.const(n, v)
            tg = tuple(p.p("targets"))

            def fn(ref: Optional[int]) -> Tri:
                if ref is None or asp is None:
                    return NOT_ASSESSED
                signs = {(ref + h - 2) % 12 + 1 for h in tg}
                return Tri.of(bool(signs & asp))

            return self.frame_sign(frame).map(fn)
        if kind == NATAL_CONJOIN:
            partner = p.p("partner")
            if partner in K.NODES:
                raise NodeReadRefused(f"{p.operand_id}: {partner}")
            a, b = c.sign_of(g), c.sign_of(partner)
            return Series.const(n, NOT_ASSESSED if a is None or b is None else Tri.of(a == b))
        if kind == NATAL_FLAG:
            flag = p.p("flag")
            val = c.own_sign(g) if flag == "own_sign" else getattr(c.graha(g), {"retrograde": "retrograde", "exalted": "exalted", "debilitated": "debilitated"}[flag])
            return Series.const(n, _tri(val))
        if kind == LORD_OF:
            b = int(p.p("bhava"))

            def lo(ref: Optional[int]) -> Tri:
                if ref is None:
                    return NOT_ASSESSED
                lord = c.sign_lord((ref + b - 2) % 12 + 1)
                return NOT_ASSESSED if lord is None else Tri.of(lord == g)

            return self.frame_sign(frame).map(lo)
        if kind == BHAVA_LORD_HOUSE:
            b = int(p.p("bhava"))
            tg = frozenset(p.p("targets"))

            def bl(ref: Optional[int]) -> Tri:
                if ref is None:
                    return NOT_ASSESSED
                lord = c.sign_lord((ref + b - 2) % 12 + 1)
                if lord is None:
                    return NOT_ASSESSED
                if g is not None and lord != g:
                    return Tri.FALSE  # the verse names a different lord: identity fails, no position needed
                if lord in K.NODES:
                    return NOT_ASSESSED
                h = house_from(ref, c.sign_of(lord))
                return NOT_ASSESSED if h is None else Tri.of(h in tg)

            return self.frame_sign(frame).map(bl)
        if kind == DASHA_IDENTITY:
            level = int(p.p("level"))
            if g is None:
                return self.lord(level).map(lambda x: NOT_ASSESSED if x is None else Tri.TRUE)
            return self.lord(level).map(lambda x: NOT_ASSESSED if x is None else Tri.of(x == g))
        if kind == DASHA_HOUSE:
            level = int(p.p("level"))
            tg = frozenset(p.p("targets"))
            pos = Series.zip(self._in_houses(tg), self.frame_sign(frame), self.lord_sign(level))
            if g is None:
                return pos
            ident = self._resolve(PredPlan(p.operand_id, DASHA_IDENTITY, (("graha", g), ("level", level)), False), frame)
            return Series.zip(k_and, ident, pos)
        if kind == DASHA_FLAG:
            level = int(p.p("level"))
            flag = p.p("flag")

            def fl(x: Optional[str]) -> Tri:
                if x is None or x in K.NODES:
                    return NOT_ASSESSED  # node-lord day: no node state is read
                if flag == "own_sign":
                    return _tri(c.own_sign(x))
                return _tri(getattr(c.graha(x), flag))

            flags = self.lord(level).map(fl)
            if g is None:
                return flags
            ident = self._resolve(PredPlan(p.operand_id, DASHA_IDENTITY, (("graha", g), ("level", level)), False), frame)
            return Series.zip(k_and, ident, flags)
        raise ValueError(f"unknown predicate kind {kind!r}")  # pragma: no cover
