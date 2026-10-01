"""AM-5 search-inventory PLANNER (GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT v0.5 §AM-5;
migration 1206). Pure: no database, no clock.

For one event class it plans exactly what 1206 stores:

  * OBLIGATIONS — the atomic unit of search: the 9-tuple
    `(event_class, path_id, rule_version, agent, relation, object_role, target, frame,
    person)`, lowercase, single `|`, arity 9; `ob_id` is the AM-2 UUIDv8 of those bytes
    (the DB recomputes it and refuses a mismatch). One obligation per enumerated edge of an
    included path.
  * PATH PINS — a TOTAL partition of the registry's sealed rule versions: every sealed
    (path, version) is `included` (its obligations are the committed set), `computed_empty`
    (the derivation PROVED the qualified set empty — never an absence), or `excluded` (a
    closed reason; the three degrading reasons need a `ruling_ref`).
  * the INTERVAL LEDGER — per obligation, the searched range and its state. An obligation
    whose search input is absent is `missing_inputs`, which a seal REFUSES by design
    (`missing_inputs_present`): nothing is silently scored.

What this module will NOT do is invent a disposition it has no warrant for:

  * A class whose signature houses are UNKNOWN cannot have a `computed_empty` P1/P3/P4 —
    unknown is not proven-empty (C3's false twin). It needs a degrading `excluded /
    inputs_unavailable` pin, which needs a ruling_ref this module does not own: without one
    the plan raises `InventoryBlocked`, naming the class and path.
  * P5's DB writes are held (steward M20261001T121451-1a8d; v1.5 batch item D7): its pin is
    `excluded / tier_withheld_by_ruling` and the ruling must be supplied by the caller.

The independent verifier (inventory_verifier.py) shares NO function with this module.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Mapping, Sequence

from .evaluator import RecordEdge, enumerate_edges
from .substrate import _uuid8_of
from services.gochara_rules.registry import signature_houses

#: paths whose qualified set is defined THROUGH the class's signature houses
H_DEPENDENT_PATHS = frozenset({"P1", "P3", "P4"})

# kgspp_reason_closed_ck / kgspp_ruling_iff_degrading_ck
EXCLUSION_REASONS = frozenset({"not_applicable_to_class", "on_demand_tier",
                               "disabled_form", "inputs_unavailable",
                               "tier_withheld_by_ruling"})
DEGRADING_REASONS = frozenset({"disabled_form", "inputs_unavailable",
                               "tier_withheld_by_ruling"})

STATE_COMPLETE = "searched_complete"
STATE_MISSING = "missing_inputs"


class InventoryBlocked(RuntimeError):
    """The inventory cannot be planned honestly without an input the planner does
    not own (a ruling, a search capability). Raised BY NAME — never defaulted."""


@dataclass(frozen=True)
class Exclusion:
    """A deliberate `excluded` disposition. `basis` follows 1206's grammar
    (`spec:<doc>@<ver>#<anchor>` | `ruling:<id>` | `oracle:<id>`)."""

    reason: str
    basis: str
    ruling_ref: str | None = None

    def __post_init__(self) -> None:
        if self.reason not in EXCLUSION_REASONS:
            raise ValueError(f"exclusion reason {self.reason!r} is not in the closed set")
        if (self.reason in DEGRADING_REASONS) != (self.ruling_ref is not None):
            raise ValueError(
                f"exclusion {self.reason!r}: ruling_ref is required iff the reason is "
                f"degrading {sorted(DEGRADING_REASONS)} (kgspp_ruling_iff_degrading_ck)")


@dataclass(frozen=True)
class Obligation:
    event_class: str
    path_id: str
    rule_version: str
    agent: str
    relation: str
    object_role: str
    target: str
    frame: str
    person: str
    transit: bool = field(default=True, compare=False)

    @property
    def canonical_bytes(self) -> str:
        return "|".join((self.event_class, self.path_id.lower(), self.rule_version.lower(),
                         self.agent, self.relation, self.object_role, self.target,
                         self.frame, self.person)).lower()

    @property
    def ob_id(self) -> uuid.UUID:
        return _uuid8_of(self.canonical_bytes.encode("utf-8"))


def obligation_of_edge(edge: RecordEdge) -> Obligation:
    frame = edge.frame_kind if edge.frame_arg is None else f"{edge.frame_kind}:{edge.frame_arg}"
    return Obligation(
        event_class=edge.event_class, path_id=edge.path_id, rule_version=edge.rule_version,
        agent=edge.agent, relation=edge.relation, object_role=edge.object_role,
        target=edge.obj.canonical_target, frame=frame, person=edge.affected_person,
        transit=edge.transit)


@dataclass(frozen=True)
class PinPlan:
    path_id: str
    rule_version: str
    disposition: str                       # included | computed_empty | excluded
    obligations: tuple[Obligation, ...] = ()
    exclusion_reason: str | None = None
    ruling_ref: str | None = None
    basis: str | None = None

    @property
    def committed_ob_ids(self) -> list[uuid.UUID]:
        return sorted({o.ob_id for o in self.obligations})


@dataclass(frozen=True)
class IntervalPlan:
    ob_id: uuid.UUID
    start: datetime
    end: datetime
    state: str


@dataclass(frozen=True)
class SearchCapability:
    """What the build can actually search. Never assumed: a capability that is
    absent turns the dependent obligations into `missing_inputs`."""

    position_probe: bool
    arc_index: bool


@dataclass(frozen=True)
class ClassInventory:
    event_class: str
    horizon: tuple[datetime, datetime]
    pins: tuple[PinPlan, ...]
    intervals: tuple[IntervalPlan, ...]

    @property
    def obligations(self) -> list[Obligation]:
        return [o for p in self.pins for o in p.obligations]

    @property
    def relations(self) -> list[str]:
        """The partition's relations_searched: exactly the distinct relations of the
        stored obligations (`partition_overclaims` compares them at seal)."""
        return sorted({o.relation for o in self.obligations})


def require_whole_second_utc(t: datetime, what: str) -> datetime:
    if t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError(f"{what} must be a UTC-aware datetime")
    if t.microsecond:
        raise ValueError(f"{what} must be whole-second (1206 kgsi_horizon_ck)")
    return t.astimezone(timezone.utc)


def _interval_state(o: Obligation, cap: SearchCapability) -> str:
    if not o.transit:
        return STATE_COMPLETE          # an atemporal natal fact: evaluated from L1
    if o.relation == "residence":
        return STATE_COMPLETE if cap.position_probe else STATE_MISSING
    if o.relation in ("conjunction", "aspect"):
        return STATE_COMPLETE if cap.arc_index else STATE_MISSING
    return STATE_MISSING               # a transit relation this build has no solver for


def plan_class_inventory(
    *,
    event_class: str,
    chart: dict,
    horizon: tuple[datetime, datetime],
    sealed_paths: Sequence[tuple[str, str]],
    capability: SearchCapability,
    path_exclusions: Mapping[str, Exclusion] | None = None,
    h_unknown_exclusion: Exclusion | None = None,
) -> ClassInventory:
    """Plan one class. `sealed_paths` is the registry's sealed (path_id, rule_version)
    set — every one is accounted for (`registry_unaccounted_path`)."""
    lo = require_whole_second_utc(horizon[0], "horizon start")
    hi = require_whole_second_utc(horizon[1], "horizon end")
    if not lo < hi:
        raise ValueError("horizon must be non-empty")
    path_exclusions = dict(path_exclusions or {})
    h_known = signature_houses(event_class, chart) is not None

    pins: list[PinPlan] = []
    intervals: list[IntervalPlan] = []
    for path_id, rule_version in sorted(sealed_paths):
        excl = path_exclusions.get(path_id)
        if excl is not None:
            pins.append(PinPlan(path_id, rule_version, "excluded",
                                exclusion_reason=excl.reason,
                                ruling_ref=excl.ruling_ref, basis=excl.basis))
            continue
        if path_id in H_DEPENDENT_PATHS and not h_known:
            if h_unknown_exclusion is None:
                raise InventoryBlocked(
                    f"{event_class}/{path_id}: the class's signature houses are UNKNOWN, so "
                    "its qualified set is unknown, not empty — it cannot be `computed_empty`. "
                    "A degrading `excluded/inputs_unavailable` pin needs a ruling_ref this "
                    "build was not given (config inventory_rulings.h_unknown).")
            pins.append(PinPlan(path_id, rule_version, "excluded",
                                exclusion_reason=h_unknown_exclusion.reason,
                                ruling_ref=h_unknown_exclusion.ruling_ref,
                                basis=h_unknown_exclusion.basis))
            continue
        edges = enumerate_edges(event_class, path_id, chart)
        seen: dict[str, Obligation] = {}
        for edge in edges:
            ob = obligation_of_edge(edge)
            seen.setdefault(ob.canonical_bytes, ob)
        obligations = tuple(seen[k] for k in sorted(seen))
        if obligations:
            pins.append(PinPlan(path_id, rule_version, "included", obligations))
            intervals.extend(
                IntervalPlan(o.ob_id, lo, hi, _interval_state(o, capability))
                for o in obligations)
        else:
            pins.append(PinPlan(
                path_id, rule_version, "computed_empty",
                basis=f"spec:GOCHARA_DESIGN_SPECS@1.4#2.2-{path_id.lower()}-empty-qualified-set"))
    return ClassInventory(event_class=event_class, horizon=(lo, hi),
                          pins=tuple(pins), intervals=tuple(intervals))


__all__ = ["ClassInventory", "DEGRADING_REASONS", "EXCLUSION_REASONS", "Exclusion",
           "H_DEPENDENT_PATHS", "IntervalPlan", "InventoryBlocked", "Obligation",
           "PinPlan", "STATE_COMPLETE", "STATE_MISSING", "SearchCapability",
           "obligation_of_edge", "plan_class_inventory", "require_whole_second_utc"]
