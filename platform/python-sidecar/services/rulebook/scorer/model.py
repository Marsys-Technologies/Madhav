"""Rule Book scorer - data model: episodes, unit structure, chart timelines.

Unit structure (SUR-RB-23, FINAL_CLUSTER_TABLE_v1_1):
* a unit is a list of GROUPS of members; members inside one group are rival readings of one
  claim (their percentiles are averaged), separate groups are disjoint claims (OR-ed into one
  unit state per day);
* only EVALUABLE members enter a group or an OR;
* for an episode, only members whose OWN manifest area tags include the episode's area (or
  GENERAL) enter that unit; if none does, the unit does not apply to that episode. This keeps
  one area's claim from being credited to another area's occurrence, and keeps an always-true
  defective member of another area from switching an OR on.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from . import config as C

# component keys: ("m", rid) is one member's own state; ("or", groups) is the combined state of a
# multi-group unit variant, groups being a tuple of tuples of rids
CompKey = Tuple[Any, ...]


class ScorerError(ValueError):
    """The input breaks a rule of the yardstick; nothing is scored."""


@dataclass(frozen=True)
class MemberSpec:
    rid: str
    area_tags: FrozenSet[str]
    moon: bool = False  # the transiting body is the Moon (scored on G1 episodes only, v1.1 C1)


@dataclass(frozen=True)
class Variant:
    """A unit as one episode sees it: the eligible members, still arranged in their groups."""

    unit_id: str
    groups: Tuple[Tuple[str, ...], ...]

    @property
    def key(self) -> Tuple[Any, ...]:
        return (self.unit_id, self.groups)

    def readings(self) -> Tuple[Tuple[str, ...], ...]:
        """v1.4 M2: a reading = one member chosen from each group. R unit: one reading per member; E unit: one
        reading (all its single-member groups); MIXED: every combination."""
        return tuple(itertools.product(*self.groups))

    def components(self) -> Tuple[CompKey, ...]:
        """Percentile components: one per reading, its day state the OR of the reading's members (v1.4 M2). The
        unit's percentile is the mean over its readings."""
        return tuple(("m", r[0]) if len(r) == 1 else ("or", tuple(r)) for r in self.readings())


@dataclass(frozen=True)
class UnitSpec:
    unit_id: str
    plane: str
    polarity: str  # "promotive" | "obstructive"
    kind: str  # "conflict_free" | "cluster"
    groups: Tuple[Tuple[MemberSpec, ...], ...]
    scored_as: str = "SINGLE"

    def members(self) -> List[MemberSpec]:
        return [m for g in self.groups for m in g]

    def variant(self, area: str, moon_ok: bool) -> Optional[Variant]:
        """The members this unit brings to an episode of ``area``; None when none qualifies."""
        out: List[Tuple[str, ...]] = []
        for g in self.groups:
            rids = tuple(
                m.rid
                for m in g
                if (area in m.area_tags or C.GENERAL in m.area_tags) and (moon_ok or not m.moon)
            )
            if rids:
                out.append(rids)
        return Variant(self.unit_id, tuple(out)) if out else None

    def all_members_variant(self) -> Variant:
        """Every evaluable member (footprint gate: the unit's own busyness, whatever the area)."""
        return Variant(self.unit_id, tuple(tuple(m.rid for m in g) for g in self.groups))


def units_from_manifest(
    manifest: Mapping[str, Any], cluster_table: Mapping[str, Any], plane: str
) -> List[UnitSpec]:
    """Unit structure for one family from the UNIT_MANIFEST and the final cluster table.

    Conflict-free unit: one group of its one evaluable member. Cluster: the table's
    ``groups_scored`` (evaluable members only); a NOT_EVALUABLE cluster is left out. The table's
    members must be exactly the manifest's evaluable members of that cluster, else the input is
    refused.
    """
    by_cluster = {c["cluster_id"]: c for c in cluster_table["clusters"]}
    units: List[UnitSpec] = []
    for u in manifest["units"]:
        if u["plane"] != plane or u["status"] != "evaluable":
            continue
        ev = {m["rulebook_id"]: m for m in u["members"] if m["status"] == "evaluable"}
        if not ev:
            continue
        if u["kind"] == "conflict_free":
            groups_ids: List[List[str]] = [sorted(ev)]
            scored_as = "SINGLE"
        else:
            row = by_cluster.get(u["unit_id"])
            if row is None:
                raise ScorerError(f"{u['unit_id']}: not in the final cluster table")
            if row["scored_as"] == "NOT_EVALUABLE":
                continue
            groups_ids = [list(g) for g in row["groups_scored"]]
            scored_as = row["scored_as"]
            flat = sorted(r for g in groups_ids for r in g)
            if flat != sorted(ev):
                raise ScorerError(f"{u['unit_id']}: cluster table members {flat} differ from the manifest's evaluable members {sorted(ev)}")
        groups = tuple(
            tuple(
                MemberSpec(
                    rid=r,
                    area_tags=frozenset(ev[r]["area_tags"]),
                    moon=C.MOON_BODY in (ev[r].get("transit_bodies") or []),
                )
                for r in g
            )
            for g in groups_ids
        )
        units.append(UnitSpec(u["unit_id"], plane, u["polarity"], u["kind"], groups, scored_as))
    units.sort(key=lambda x: x.unit_id)
    return units


@dataclass(frozen=True)
class Episode:
    """One scored episode: chart index, area, direction, grade and its window (inclusive date ordinals).

    G1 window = the day +- 1 (3 days); G2 window = the whole calendar month. ``schedulable`` is NOT read by any scoring
    path (SUR-RB-55/56): the fallback check reads its own, separately formed non-schedulable list instead.
    """

    chart: int
    area: str
    direction: str
    grade: str
    lo: int
    hi: int
    schedulable: bool = False

    def validate(self) -> None:
        if self.direction not in C.POLARITY_OF_DIRECTION:
            raise ScorerError(f"direction {self.direction!r}: only favourable/unfavourable episodes are scored")
        if self.grade == C.G1:
            # the day +- 1, possibly clipped to the family horizon (v1.2 K2): 3 days, or 2 at a horizon edge
            if self.hi - self.lo not in (C.G1_WINDOW_DAYS - 1, C.G1_WINDOW_DAYS - 2):
                raise ScorerError("a G1 window is 3 days (2 when clipped at the horizon edge)")
        elif self.grade == C.G2:
            a, b = date.fromordinal(self.lo), date.fromordinal(self.hi)
            first = date(a.year, a.month, 1)
            nxt = date(a.year + (a.month == 12), a.month % 12 + 1, 1)
            if a != first or b.toordinal() != nxt.toordinal() - 1:
                raise ScorerError("a G2 window is one whole calendar month")
        else:
            raise ScorerError(f"grade {self.grade!r}: this sample has G1 and G2 only")

    @property
    def mid(self) -> int:
        return (self.lo + self.hi) // 2

    @property
    def moon_ok(self) -> bool:
        return self.grade == C.G1


@dataclass
class ChartTimeline:
    """One chart's states over its family horizon [h_start, h_end] (date ordinals, inclusive).

    ``states[rid]`` is an int8 array of length h_end - h_start + 1: 1 TRUE, 0 FALSE, -1 NOT_ASSESSED.
    ``birth`` is the birth date ordinal (age matching for check (c)).
    """

    code: str
    birth: int
    h_start: int
    h_end: int
    states: Dict[str, np.ndarray] = field(default_factory=dict)

    @property
    def n_days(self) -> int:
        return self.h_end - self.h_start + 1

    # The ONLY two ways scorer code reads a member's states (SUR-RB-36): ``assessed`` exposes which days are
    # assessed and nothing else; ``values`` exposes TRUE/FALSE and is permitted only in the three carve-outs
    # (the statistics, the D8 touch rates, the constant-member rule of v1.0 3.2 step 3).
    def assessed(self, rid: str) -> Optional[np.ndarray]:
        a = self.states.get(rid)
        return None if a is None else (a >= 0)

    def assessed_count(self, rid: str, lo: int, hi: int) -> Optional[int]:
        """Number of assessed days of member ``rid`` in [lo, hi] (indices from h_start). Assessed-mask only."""
        a = self.states.get(rid)
        return None if a is None else int((a[lo : hi + 1] >= 0).sum())

    def values(self, rid: str) -> Optional[np.ndarray]:
        return self.states.get(rid)

    def validate(self) -> None:
        if self.h_end < self.h_start:
            raise ScorerError(f"{self.code}: empty horizon")
        for rid, a in self.states.items():
            if a.dtype != np.int8 or a.shape != (self.n_days,):
                raise ScorerError(f"{self.code}/{rid}: states must be int8 of length {self.n_days}")
            if a.size and (a.min() < -1 or a.max() > 1):
                raise ScorerError(f"{self.code}/{rid}: state codes must be 1, 0 or -1")


def mask_unstable(builds: Sequence[np.ndarray]) -> np.ndarray:
    """v1.1 C2: a day on which a member's state differs between the -5, 0, +5 minute builds is NOT_ASSESSED.

    ``builds`` are int8 arrays over the same days (the three builds of one member, any order).
    """
    if len(builds) < 2:
        raise ScorerError("birth-time stability needs at least two builds")
    base = np.array(builds[0], dtype=np.int8, copy=True)
    for other in builds[1:]:
        if other.shape != base.shape:
            raise ScorerError("builds cover different days")
        base[base != other] = -1
    return base
