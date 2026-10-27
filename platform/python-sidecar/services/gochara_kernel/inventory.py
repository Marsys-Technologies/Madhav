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
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Mapping, Sequence

from .evaluator import RecordEdge, enumerate_edges, node_aspect_declined
from .substrate import _uuid8_of
from services.gochara_rules import registry as _rules
from services.gochara_rules.registry import signature_houses

#: paths whose qualified set is defined THROUGH the class's signature houses
H_DEPENDENT_PATHS = frozenset({"P1", "P3", "P4"})

# kgspp_reason_closed_ck / kgspp_ruling_iff_degrading_ck
EXCLUSION_REASONS = frozenset({"not_applicable_to_class", "on_demand_tier",
                               "disabled_form", "inputs_unavailable",
                               "tier_withheld_by_ruling", "superseded_by_version"})
DEGRADING_REASONS = frozenset({"disabled_form", "inputs_unavailable",
                               "tier_withheld_by_ruling"})

STATE_COMPLETE = "searched_complete"
STATE_MISSING = "missing_inputs"
#: AM-14 (Codex round 6 R2; migration 1232, not yet applied anywhere): the Moon-RESOLVED portion of a
#: period-role obligation, explicitly accounted as EXCLUDED from the stored tier — neither a missing
#: search interval nor a completed geometry search.
STATE_EXCLUDED_MOON = "excluded_moon_tier"

#: steward rulings (2026-10-02; Stream B records both under decisions/). The ids pass
#: 1206's ruling_ref grammar `^[A-Za-z0-9._-]+$` and its basis grammar `ruling:<id>`.
P5_HOLD_RULING = "ST-P5-HOLD-20261001"          # P5 DB writes hold (migration 1204 + AM-7)
H_UNKNOWN_RULING = "ST-H-UNKNOWN-20261002"      # H unknown (S:307-312) — P1/P3/P4 ONLY

#: AM-11 pin (e): P1's period-role agent is a ROLE token in the inventory (records keep
#: the concrete graha). level_n of the Vimśottarī rows each role is cut at (§4.0).
PERIOD_ROLE_LEVEL = {"md": 1, "ad": 2, "pd": 3}


def standing_exclusions() -> tuple[dict, "Exclusion", ]:
    """The standing rulings as the planner's exclusion inputs:
    ({path_id: Exclusion} for P5 (held) and for every path the registry switches off
    (`registry.DISABLED_PATHS` — P4 under FOURQ-CLOSURE-20261027), the H-unknown Exclusion).
    An excluded path is pinned `excluded / tier_withheld_by_ruling / ruling:<id>` BEFORE any
    enumeration: no obligation, interval, record or window of it is planned or built."""
    paths = {"P5": Exclusion("tier_withheld_by_ruling", f"ruling:{P5_HOLD_RULING}", P5_HOLD_RULING)}
    for path_id, ruling in sorted(_rules.DISABLED_PATHS.items()):
        paths[path_id] = Exclusion(ruling["reason"], f"ruling:{ruling['ruling_ref']}", ruling["ruling_ref"])
    return (
        paths,
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
    #: the pinned daśā period it was cut at, as a NATURAL pointer (level, start) — never a row id, which an L1 rebuild re-issues (AM-11 pin e, G12). SQL does not check it — a named
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
    #: the schema can account a Moon-resolved period-role interval as `excluded_moon_tier` (1232). Off
    #: ⇒ such an interval stays an honest `missing_inputs` and the class cannot seal — the schema is
    #: never assumed to be ahead of what is applied.
    moon_scope_domain: bool = False


#: SR-D6-OBJECTIVE-UNKNOWN (a): a node as the ASPECTING agent is DECLARED not-applicable (N-14, O-CF-DRISHTI: nodes cast no dṛṣṭi) — excluded from
#: the product at the inventory, counted per class and path, and never a window-level blank. The reason is `gochara_rules.drishti`'s own name for it.
NODE_CASTS_NO_DRISHTI = "node_casts_no_drishti"


@dataclass(frozen=True)
class NotApplicable:
    """`count` enumerated candidate edges of `agent` under `path_id` that the rule declares not-applicable (`reason`)."""

    reason: str
    path_id: str
    agent: str
    count: int


@dataclass(frozen=True)
class ClassInventory:
    event_class: str
    horizon: tuple[datetime, datetime]
    pins: tuple[PinPlan, ...]
    intervals: tuple[IntervalPlan, ...]
    #: the declared not-applicable candidates of the SEARCHED versions (not obligations: nothing is searched for them). Not part of
    #: the stored ledger — an accounting beside it, so no digest moves.
    not_applicable: tuple[NotApplicable, ...] = ()

    @property
    def node_aspect_not_applicable(self) -> int:
        """The class's total of node-as-aspecting-agent edges declared not-applicable."""
        return sum(n.count for n in self.not_applicable if n.reason == NODE_CASTS_NO_DRISHTI)

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
             cap: SearchCapability, dasha_rows: Sequence[DashaRow] | None,
             rule_version: str):
    """P1 under the AM-11 role-token form: the obligation agent is
    `period_lord:md|ad|pd`; each searched interval is cut at the PINNED daśā rows'
    boundaries (half-open, §4.0) and names the agent it resolved to. The qualified
    geometry is P1's enumerated TRANSIT edges (its natal-fact rows are not
    admission-bearing records — pin b — so they are not obligations)."""
    edges = [e for e in enumerate_edges(event_class, "P1", chart, rule_version=rule_version)
             if e.transit]
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
                                                  {"resolved_agent": None, "dasha_period": None,
                                                   **({"limitation": "p1_pd_level_no_source"} if role == "pd" else {})}))
                else:
                    # a period whose lord is the MOON resolves to an agent the stored build never
                    # searches (AM-4: EPHEMERAL tier). AM-14: the exclusion follows the RESOLVED
                    # concrete agent, per role obligation — so a Moon bhukti excludes only the
                    # `period_lord:ad` interval (the MD lord's delivery is still searched), and the
                    # Moon as a natal TARGET or in another agent's Moon-frame evaluation is untouched.
                    # With the 1232 domain accounting that portion is `excluded_moon_tier`; without
                    # it, honest `missing_inputs` — never `searched_complete` on a search not run.
                    on_demand = r.lord == "moon"
                    if on_demand and cap.moon_scope_domain:
                        state, tier = STATE_EXCLUDED_MOON, "moon_resolved_domain (AM-14)"
                    elif on_demand:
                        state, tier = STATE_MISSING, "moon_on_demand (AM-4)"
                    else:
                        state, tier = _interval_state(o, cap), None
                    intervals.append(IntervalPlan(
                        o.ob_id, a, b, state,
                        {"resolved_agent": r.lord, "dasha_period": {"level": r.level, "start": r.start.isoformat()},
                         **({"tier": tier} if tier else {}),
                         # R9-5: the PD level has no verse — searched, but its readings are TESTIMONY only
                         **({"limitation": "p1_pd_level_no_source"} if role == "pd" else {})}))
    # AM-21 part 2 / XX.38 (steward M…053914): the DELIVERY searches. The Sun's or Jupiter's transit through ANOTHER
    # graha's exaltation sign (and the Sun's through another's debilitation sign) is read under that graha's AD, so it
    # is a CONCRETE-agent search — the agent is not the period lord, and the role-token obligations above resolve to
    # the running lord, never to the Sun/Jupiter. These obligations carry the geometry the records stand on: the whole
    # horizon, like every non-role transit search. The anchor (which bhukti lord's AD licenses a reading) is NOT part of
    # the obligation grammar (the 9-tuple has no anchor, the ledger digest no domain) — it is the RECORD's property,
    # derived independently by `record_verifier.verify_p1_anchors`; a search obligation is anchor-free.
    delivery = sorted({(e.agent, e.relation, e.object_role, e.obj.canonical_target,
                        (e.frame_kind if e.frame_arg is None else f"{e.frame_kind}:{e.frame_arg}"),
                        e.affected_person, e.rule_version, e.path_id)
                       for e in edges if e.period_anchor_lord is not None and e.agent != e.period_anchor_lord})
    for agent, relation, role_, target, frame, person, ver, pid in delivery:
        o = Obligation(event_class, pid, ver, agent, relation, role_, target, frame, person, transit=True)
        obligations.append(o)
        intervals.append(IntervalPlan(o.ob_id, lo, hi, _interval_state(o, cap)))
    return tuple(sorted(set(obligations), key=lambda o: o.canonical_bytes)), intervals


def supersession_basis(path_id: str, old: str, new: str) -> str:
    """The 1206-grammar basis of a `superseded_by_version` pin (non-degrading: no ruling_ref). The anchor names
    the amendment that approved the successor; the verifier carries its OWN copy of this table. A successor at the
    owner-confirmed doctrine version (1.3.0, SR-OD1 V1) names the owner ruling it stands on instead."""
    if new == _rules.DOCTRINE_VERSION:
        return f"ruling:{_rules.DOCTRINE_PATH_RULINGS[path_id]}"
    anchor = "AM-18" if path_id == "P2" else "AM-13"
    return f"spec:GOCHARA_SPECS_V1_5_AMENDMENTS@1.5#{anchor}-{path_id.lower()}-{old}-superseded-by-{new}"


def _approved_successors(path_id: str, version: str) -> frozenset[str]:
    """EVERY version the registry approves as a successor of `path@version`: the AM-13 / AM-18 table
    (`SUPERSEDED_PATHS`, one step) and the owner-confirmed doctrine chain (`DOCTRINE_SUPERSEDED_PATHS`, SR-OD1 V1:
    1.0.0 → 1.3.0, and 1.1.0 → 1.3.0 for P3/P4). A 1.0.0 row has both, so the selected version decides which applies."""
    from services.gochara_rules import registry as rules_registry
    ref = rules_registry.composite_ref(path_id, version)
    out = set()
    for table in (rules_registry.SUPERSEDED_PATHS, rules_registry.DOCTRINE_SUPERSEDED_PATHS):
        row = table.get(ref)
        if row is not None:
            pid, ver = tuple(row["superseded_by"])
            if pid == path_id:
                out.add(ver)
    return frozenset(out)


def _exclusion_for(path_id: str, version: str,
                   path_exclusions: Mapping) -> Exclusion | None:
    """A path-level exclusion (`"P5"`) applies to EVERY version of the path; a version-specific ruling is keyed
    by the COMPOSITE `(path_id, version)` and applies to that version only."""
    return path_exclusions.get((path_id, version)) or path_exclusions.get(path_id)


def plan_class_inventory(
    *,
    event_class: str,
    chart: dict,
    horizon: tuple[datetime, datetime],
    sealed_paths: Sequence[tuple[str, str]],
    capability: SearchCapability,
    selected_versions: Mapping[str, str] | None = None,
    path_exclusions: Mapping | None = None,
    h_unknown_exclusion: Exclusion | None = None,
    dasha_rows: Sequence[DashaRow] | None = None,
) -> ClassInventory:
    """Plan one class. `sealed_paths` is the registry's sealed (path_id, rule_version) CATALOGUE — every
    one is accounted for (`registry_unaccounted_path`). `selected_versions` ({path_id: version}) is the ONE
    version of each path this class's search runs under (R8-2): at most one version of a path is `included`
    (1206 `multiple_included_versions`); an older sealed version is `excluded/superseded_by_version` ONLY when
    its approved successor is the selected version AND is included for this class (a supersession with no
    included superseder is a coverage hole — `superseded_without_included_version`); every other non-selected
    version is accounted by the same dispositions the selected one would get (excluded, computed_empty) and a
    non-selected version that would otherwise be `included` needs an explicit composite-keyed ruling
    (a WITHHELD successor) or the plan is refused. A catalogue with several versions of a path and no
    selection for it is refused — never resolved by taking them all."""
    lo = require_whole_second_utc(horizon[0], "horizon start")
    hi = require_whole_second_utc(horizon[1], "horizon end")
    if not lo < hi:
        raise ValueError("horizon must be non-empty")
    path_exclusions = dict(path_exclusions or {})
    by_path: dict[str, list[str]] = {}
    for path_id, rule_version in sealed_paths:
        by_path.setdefault(path_id, []).append(rule_version)
    selected = dict(selected_versions or {})
    for path_id, versions in by_path.items():
        if path_id in selected:
            if selected[path_id] not in versions:
                raise InventoryBlocked(
                    f"{event_class}/{path_id}: the selected version {selected[path_id]!r} is not sealed "
                    f"(sealed: {sorted(versions)})")
        elif len(versions) == 1:
            selected[path_id] = versions[0]
        else:
            raise InventoryBlocked(
                f"{event_class}/{path_id}: {len(versions)} sealed versions {sorted(versions)} and no "
                "selected version — the planner never searches (or double-counts) them all")

    na_by_version: dict = {(p, v): [] for p, vs in by_path.items() for v in vs}

    def disposition(path_id: str, rule_version: str):
        """(PinPlan, [IntervalPlan]) of `path@version` as if it were the searched version."""
        excl = _exclusion_for(path_id, rule_version, path_exclusions)
        if excl is not None:
            return PinPlan(path_id, rule_version, "excluded", exclusion_reason=excl.reason,
                           ruling_ref=excl.ruling_ref, basis=excl.basis), []
        # ND-H-20261005: a 1.2.0 row is the eight classes' row. For any other class it does not apply (its H is
        # the unchanged cited table, searched under the default selection) — non-degrading, basis the ruling.
        if (rule_version == _rules.ND_H_VERSION and path_id in H_DEPENDENT_PATHS
                and event_class not in _rules.ND_H_CLASSES and selected.get(path_id) != rule_version):
            return PinPlan(path_id, rule_version, "excluded", exclusion_reason="not_applicable_to_class",
                           basis=f"ruling:{_rules.ND_H_RULING}"), []
        # SR-OD1 V1: the 1.3.0 doctrine row is every OTHER class's row. A class that runs the path at its ND-H /
        # ND-P2 row (1.2.0, re-derived in place from the 1.3.0 soft factors) does not search 1.3.0 — non-degrading,
        # basis the ruling that put the class on 1.2.0 (the scoped supersession's own ruling, one source).
        if (rule_version == _rules.DOCTRINE_VERSION and path_id in H_DEPENDENT_PATHS
                and selected.get(path_id) == _rules.ND_H_VERSION):
            scoped_row = _rules.CLASS_SUPERSEDED_PATHS.get((event_class, path_id, _rules.RULE_VERSION))
            if scoped_row is None:
                raise InventoryBlocked(
                    f"{event_class}/{path_id}: runs at {_rules.ND_H_VERSION} but names no class-scoped ruling for it")
            return PinPlan(path_id, rule_version, "excluded", exclusion_reason="not_applicable_to_class",
                           basis=f"ruling:{scoped_row['ruling_ref']}"), []
        # ND-H item 5: P2 emits no row for a parent class once the class runs under its ND-H rows (the
        # native's Moon never evidences the parent, §1.2 inv 6).
        if (path_id == "P2" and event_class in _rules.P2_NO_ROW_CLASSES
                and selected.get("P3") == _rules.ND_H_VERSION):
            return PinPlan(path_id, rule_version, "excluded", exclusion_reason="not_applicable_to_class",
                           basis=f"ruling:{_rules.ND_H_RULING}"), []
        # FB-44: H is read under the version being planned — never another version's H
        if path_id in H_DEPENDENT_PATHS and signature_houses(event_class, chart, rule_version) is None:
            if h_unknown_exclusion is None:
                raise InventoryBlocked(
                    f"{event_class}/{path_id}: the class's signature houses are UNKNOWN, so "
                    "its qualified set is unknown, not empty — it cannot be `computed_empty`. "
                    "A degrading `excluded/inputs_unavailable` pin needs a ruling_ref this "
                    "build was not given (config inventory_rulings.h_unknown).")
            return PinPlan(path_id, rule_version, "excluded",
                           exclusion_reason=h_unknown_exclusion.reason,
                           ruling_ref=h_unknown_exclusion.ruling_ref,
                           basis=h_unknown_exclusion.basis), []
        if path_id == "P1":
            ob_plan, iv_plan = _plan_p1(event_class, chart, lo, hi, capability, dasha_rows, rule_version)
            if ob_plan:
                return PinPlan(path_id, rule_version, "included", ob_plan), list(iv_plan)
            return PinPlan(path_id, rule_version, "computed_empty",
                           basis="spec:GOCHARA_DESIGN_SPECS@1.4#2.2-p1-empty-qualified-set"), []
        with node_aspect_declined() as declined:
            edges = enumerate_edges(event_class, path_id, chart, rule_version=rule_version)
        for agent in sorted(set(declined)):
            na_by_version[(path_id, rule_version)].append(
                NotApplicable(NODE_CASTS_NO_DRISHTI, path_id, agent, declined.count(agent)))
        seen: dict[str, Obligation] = {}
        for edge in edges:
            ob = obligation_of_edge(edge)
            seen.setdefault(ob.canonical_bytes, ob)
        obligations = tuple(seen[k] for k in sorted(seen))
        if obligations:
            return (PinPlan(path_id, rule_version, "included", obligations),
                    [IntervalPlan(o.ob_id, lo, hi, _interval_state(o, capability)) for o in obligations])
        return PinPlan(path_id, rule_version, "computed_empty",
                       basis=f"spec:GOCHARA_DESIGN_SPECS@1.4#2.2-{path_id.lower()}-empty-qualified-set"), []

    pins: list[PinPlan] = []
    intervals: list[IntervalPlan] = []
    for path_id in sorted(by_path):
        chosen = selected[path_id]
        chosen_pin, chosen_iv = disposition(path_id, chosen)
        for rule_version in sorted(by_path[path_id]):
            if rule_version == chosen:
                pins.append(chosen_pin)
                intervals.extend(chosen_iv)
                continue
            # FB-32: for a class selected at its ND-H row the older row is searched no more — superseded FOR
            # THAT CLASS (class-scoped: the registry's global SUPERSEDED_PATHS is not touched)
            scoped = _rules.CLASS_SUPERSEDED_PATHS.get((event_class, path_id, rule_version))
            if (scoped is not None and chosen_pin.disposition == "included"
                    and tuple(scoped["superseded_by"]) == (path_id, chosen)):
                pins.append(PinPlan(path_id, rule_version, "excluded",
                                    exclusion_reason="superseded_by_version",
                                    basis=f"ruling:{scoped['ruling_ref']}"))
                continue
            pin, _iv = disposition(path_id, rule_version)
            if pin.disposition != "included":
                pins.append(pin)                 # excluded / computed_empty exactly as the version would be
                continue
            # a non-selected version that WOULD be searched: superseded by the included selection, or refused
            if chosen_pin.disposition == "included" and chosen in _approved_successors(path_id, rule_version):
                pins.append(PinPlan(path_id, rule_version, "excluded",
                                    exclusion_reason="superseded_by_version",
                                    basis=supersession_basis(path_id, rule_version, chosen)))
                continue
            raise InventoryBlocked(
                f"{event_class}/{path_id}: sealed version {rule_version!r} is neither the selected "
                f"{chosen!r}, superseded by an INCLUDED approved successor, nor excluded by a composite-keyed "
                "ruling (a withheld version needs its own ruling_ref) — it cannot be accounted honestly")
    # FB-34/35/36: normalized record annotations live in the inventory's free
    # detail JSON, referenced by (grain, physical edge key). No record key or
    # coverage-facts value changes; 1155 requires exact coverage-facts equality.
    from .evaluator import final_rule_context, edge_identity_key, record_final_rules
    by_ob = {o.ob_id: (pin, o) for pin in pins if pin.disposition == 'included'
             and pin.rule_version == '1.2.0' for o in pin.obligations}
    prototypes = {pin.path_id: enumerate_edges(event_class, pin.path_id, chart, rule_version=pin.rule_version)
                  for pin in pins if pin.disposition == 'included' and pin.rule_version == '1.2.0'}
    annotated = []
    for iv in intervals:
        if iv.ob_id not in by_ob:
            annotated.append(iv)
            continue
        pin, ob = by_ob[iv.ob_id]
        detail = dict(iv.detail or {})
        factors = {}
        for edge in prototypes[pin.path_id]:
            if (edge.relation, edge.object_role, edge.obj.canonical_target) != (ob.relation, ob.object_role, ob.target):
                continue
            if ob.agent.startswith('period_lord:'):
                level = ob.agent.split(':')[1]
                if (edge.period_anchor_level != level or edge.agent != detail.get('resolved_agent')
                        or edge.period_anchor_lord != detail.get('resolved_agent')):
                    continue
            elif edge.agent != ob.agent:
                continue
            factors[edge_identity_key(edge)] = record_final_rules(edge)
        detail['record_factors'] = factors
        context = final_rule_context(event_class, pin.path_id, chart, pin.rule_version)
        if context is not None:
            detail['final_rule_context'] = context
        annotated.append(replace(iv, detail=detail))
    intervals = annotated
    # the declared not-applicable account follows the SEARCHED version of each path (a non-selected version is accounted by its pin only)
    not_applicable = tuple(n for path_id in sorted(by_path) for n in na_by_version[(path_id, selected[path_id])])
    return ClassInventory(event_class=event_class, horizon=(lo, hi),
                          pins=tuple(pins), intervals=tuple(intervals), not_applicable=not_applicable)


__all__ = ["supersession_basis", "ClassInventory", "NODE_CASTS_NO_DRISHTI", "NotApplicable", "DEGRADING_REASONS", "DashaRow", "H_UNKNOWN_RULING",
           "P5_HOLD_RULING", "PERIOD_ROLE_LEVEL", "standing_exclusions", "EXCLUSION_REASONS", "Exclusion",
           "H_DEPENDENT_PATHS", "IntervalPlan", "InventoryBlocked", "Obligation",
           "PinPlan", "STATE_COMPLETE", "STATE_EXCLUDED_MOON", "STATE_MISSING", "SearchCapability",
           "obligation_of_edge", "plan_class_inventory", "require_whole_second_utc"]
