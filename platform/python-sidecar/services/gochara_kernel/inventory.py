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

#: steward rulings (2026-10-02; Stream B records both under decisions/). The ids pass
#: 1206's ruling_ref grammar `^[A-Za-z0-9._-]+$` and its basis grammar `ruling:<id>`.
P5_HOLD_RULING = "ST-P5-HOLD-20261001"          # P5 DB writes hold (migration 1204 + AM-7)
H_UNKNOWN_RULING = "ST-H-UNKNOWN-20261002"      # H unknown (S:307-312) — P1/P3/P4 ONLY

#: AM-11 pin (e): P1's period-role agent is a ROLE token in the inventory (records keep
#: the concrete graha). level_n of the Vimśottarī rows each role is cut at (§4.0).
PERIOD_ROLE_LEVEL = {"md": 1, "ad": 2, "pd": 3}


def standing_exclusions() -> tuple[dict, "Exclusion", ]:
    """The two standing rulings as the planner's exclusion inputs:
    ({path_id: Exclusion} for P5, the H-unknown Exclusion)."""
    return (
        {"P5": Exclusion("tier_withheld_by_ruling", f"ruling:{P5_HOLD_RULING}",
                         P5_HOLD_RULING)},
        Exclusion("inputs_unavailable", f"ruling:{H_UNKNOWN_RULING}", H_UNKNOWN_RULING),
    )


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
    #: a role-token obligation's interval names the concrete agent it was resolved to and
    #: the pinned daśā row it was cut at (AM-11 pin e). SQL does not check it — a named
    #: residual; the independent verifier re-derives it.
    detail: dict | None = None


@dataclass(frozen=True)
class DashaRow:
    """One pinned Vimśottarī row (§4.0), half-open [start, end)."""

    row_id: str
    level: int              # 1 MD, 2 AD, 3 PD
    lord: str               # lowercase graha
    start: datetime
    end: datetime


@dataclass(frozen=True)
class SearchCapability:
    """What the build can actually search. Never assumed: a capability that is
    absent turns the dependent obligations into `missing_inputs`."""

    position_probe: bool
    arc_index: bool
    #: aspect-to-span (the aspect point's ingress into a house span): derived from the body's
    #: residence spans (materialise.aspect_spans), so it is searched only with the position probe
    #: AND this flag — flipped on only once the independent oracle derives the same spans.
    aspect_span_solver: bool = False


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
    if o.relation == "aspect" and o.target.startswith("span:"):
        # aspect-to-span is not a point root: the arc index alone does not search it
        return STATE_COMPLETE if (cap.aspect_span_solver and cap.position_probe) else STATE_MISSING
    if o.relation in ("conjunction", "aspect"):
        return STATE_COMPLETE if cap.arc_index else STATE_MISSING
    return STATE_MISSING               # a transit relation this build has no solver for


def _plan_p1(event_class: str, chart: dict, lo: datetime, hi: datetime,
             cap: SearchCapability, dasha_rows: Sequence[DashaRow] | None):
    """P1 under the AM-11 role-token form: the obligation agent is
    `period_lord:md|ad|pd`; each searched interval is cut at the PINNED daśā rows'
    boundaries (half-open, §4.0) and names the agent it resolved to. The qualified
    geometry is P1's enumerated TRANSIT edges (its natal-fact rows are not
    admission-bearing records — pin b — so they are not obligations)."""
    edges = [e for e in enumerate_edges(event_class, "P1", chart) if e.transit]
    shapes = sorted({(e.relation, e.object_role, e.obj.canonical_target,
                      (e.frame_kind if e.frame_arg is None
                       else f"{e.frame_kind}:{e.frame_arg}"), e.affected_person,
                      e.rule_version, e.path_id) for e in edges})
    if not shapes:
        return (), []
    if dasha_rows is None:
        raise InventoryBlocked(
            f"{event_class}/P1: the role-token obligations are cut at the pinned daśā rows "
            "(AM-11 pin e) and none were supplied")
    obligations: list[Obligation] = []
    intervals: list[IntervalPlan] = []
    for role, level in PERIOD_ROLE_LEVEL.items():
        rows = sorted((r for r in dasha_rows if r.level == level), key=lambda r: r.start)
        pieces: list[tuple[datetime, datetime, DashaRow | None]] = []
        cursor = lo
        for r in rows:
            a, b = max(r.start, lo), min(r.end, hi)
            if not a < b:
                continue
            for what, t in (("start", a), ("end", b)):
                if t.microsecond:
                    raise InventoryBlocked(
                        f"daśā row {r.row_id} {what} {t.isoformat()} is not whole-second; "
                        "1206's interval CHECK refuses it and rounding would be a silent edit")
            if a > cursor:
                pieces.append((cursor, a, None))         # a gap: no pinned row covers it
            pieces.append((a, b, r))
            cursor = max(cursor, b)
        if cursor < hi:
            pieces.append((cursor, hi, None))
        for relation, role_, target, frame, person, ver, pid in shapes:
            o = Obligation(event_class, pid, ver, f"period_lord:{role}", relation, role_,
                           target, frame, person, transit=True)
            obligations.append(o)
            for a, b, r in pieces:
                if r is None:
                    intervals.append(IntervalPlan(o.ob_id, a, b, STATE_MISSING,
                                                  {"resolved_agent": None, "dasha_row_id": None}))
                else:
                    # a period whose lord is the MOON resolves to an agent the stored build never
                    # searches (AM-4: EPHEMERAL tier, excluded from the stored enumeration by rule):
                    # honest `missing_inputs`, named — never `searched_complete` on a search not run
                    on_demand = r.lord == "moon"
                    intervals.append(IntervalPlan(
                        o.ob_id, a, b, STATE_MISSING if on_demand else _interval_state(o, cap),
                        {"resolved_agent": r.lord, "dasha_row_id": str(r.row_id),
                         **({"tier": "moon_on_demand (AM-4)"} if on_demand else {})}))
    return tuple(sorted(set(obligations), key=lambda o: o.canonical_bytes)), intervals


def plan_class_inventory(
    *,
    event_class: str,
    chart: dict,
    horizon: tuple[datetime, datetime],
    sealed_paths: Sequence[tuple[str, str]],
    capability: SearchCapability,
    path_exclusions: Mapping[str, Exclusion] | None = None,
    h_unknown_exclusion: Exclusion | None = None,
    dasha_rows: Sequence[DashaRow] | None = None,
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
        if path_id == "P1":
            ob_plan, iv_plan = _plan_p1(event_class, chart, lo, hi, capability, dasha_rows)
            if ob_plan:
                pins.append(PinPlan(path_id, rule_version, "included", ob_plan))
                intervals.extend(iv_plan)
            else:
                pins.append(PinPlan(
                    path_id, rule_version, "computed_empty",
                    basis="spec:GOCHARA_DESIGN_SPECS@1.4#2.2-p1-empty-qualified-set"))
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


__all__ = ["ClassInventory", "DEGRADING_REASONS", "DashaRow", "H_UNKNOWN_RULING",
           "P5_HOLD_RULING", "PERIOD_ROLE_LEVEL", "standing_exclusions", "EXCLUSION_REASONS", "Exclusion",
           "H_DEPENDENT_PATHS", "IntervalPlan", "InventoryBlocked", "Obligation",
           "PinPlan", "STATE_COMPLETE", "STATE_MISSING", "SearchCapability",
           "obligation_of_edge", "plan_class_inventory", "require_whole_second_utc"]
