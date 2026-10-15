"""K7-4: Pareto comparison of forecaster windows; no scalar or fixed weights.

Authority: OWNER_RULINGS_K7-4_TABLE.md Part B (lines 26–60), ALGO §3.10.
(I) INTERPRETATION: explicit identity bindings are fixture preparation only;
production callers supply no jury/negative-space bridge until admitted.
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from datetime import date, timedelta
from itertools import combinations
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS

KNOWN_DOMAINS = CANONICAL_DOMAINS
TIERS = {"structural_prior": 0, "concurrent": 1, "calibrated_provisional": 2, "calibrated": 3}
VERSION = "k7-4:pareto:v1"


class WindowInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chart_id: str = Field(min_length=1)
    window_id: str = Field(min_length=1)
    field_snapshot_id: str = Field(min_length=1)
    window_start: date | None = None
    window_end: date | None = None
    precision_regime: str = "day_grade"
    event_class: str | None = None
    event_domain: str | None = None
    confidence_tier: str | None = None
    weakest_link: str | None = None
    robustness: dict | None = None
    jury: dict | None = None
    jury_binding: dict | None = None
    obstruction: dict | None = None
    contest_rows: int | None = Field(default=None, ge=0, strict=True)
    lambda_peak: float | None = Field(default=None, allow_inf_nan=False)
    null_p: float | None = Field(default=None, allow_inf_nan=False)
    factor_informativeness: float | None = Field(default=None, allow_inf_nan=False)
    factor_consequence: float | None = Field(default=None, allow_inf_nan=False)


def _available(value):
    return {"state": "evaluated", "value": value, "reason": None}


def _unavailable(reason):
    return {"state": "information_unavailable", "value": None, "reason": reason}


def _binding(w: WindowInput) -> bool:
    if not w.jury_binding:
        return False
    if not w.jury:
        raise ValueError("jury binding without jury evidence")
    expected = {"chart_id": w.chart_id, "window_id": w.window_id,
                "field_snapshot_id": w.field_snapshot_id,
                "assertion_id": w.jury.get("assertion_id"), "generation": w.jury.get("generation")}
    if any(not value or w.jury_binding.get(key) != value for key, value in expected.items()):
        raise ValueError("jury outside chart/window/snapshot/generation binding")
    # No live mapping exists in the K4-2b reader contract.
    if not str(expected["generation"]).startswith("candidate:"):
        raise ValueError("live jury mapping unadmitted")
    return True


def _evidence(w, ref, end, frame):
    bound = _binding(w)
    axes = {"nearest": _available(max(0, (w.window_start - ref).days))
            if w.window_start and w.precision_regime == "day_grade" else _unavailable("start_not_day_grade")}
    anchor = None
    if bound:
        dw, anchor = w.jury.get("dw"), w.jury.get("anchor_days")
        if type(anchor) not in (float, int) or not math.isfinite(anchor) or anchor <= 0:
            raise ValueError("positive finite jury anchor_days required")
        if dw is not None and (type(dw) not in (int, float) or not math.isfinite(dw)):
            raise ValueError("finite signed D(W) required")
        if dw is None and not w.jury.get("null_reason"):
            raise ValueError("null D(W) requires null_reason")
        axes["strongest"] = _available(dw) if dw is not None else _unavailable(w.jury["null_reason"])
    else:
        axes["strongest"] = _unavailable("stage_to_reader_mapping_unadmitted")
    axes["most_robust"] = (_available(TIERS[w.confidence_tier]) if w.confidence_tier in TIERS
                           else _unavailable("robustness_not_computed"))
    if w.confidence_tier is not None and w.confidence_tier not in TIERS:
        raise ValueError("unknown confidence_tier")
    if frame is not None:
        if frame.get("domain") is not None and frame["domain"] not in KNOWN_DOMAINS:
            axes["best_suited"] = _unavailable("frame_domain_unknown")
        elif w.event_domain not in KNOWN_DOMAINS:
            axes["best_suited"] = _unavailable("event_class_not_in_ontology")
        elif not w.window_start or not w.window_end or w.precision_regime != "day_grade":
            axes["best_suited"] = _unavailable("start_not_day_grade")
        else:
            from services.ka_kshetra.stage6_salience import compute_relevance, QuestionFrame
            # (I) INTERPRETATION I2: stored DATE end is inclusive; producer
            # relevance consumes half-open intervals. Entity is echoed only.
            relevance = compute_relevance(w.event_domain, w.window_start.toordinal(),
                (w.window_end + timedelta(days=1)).toordinal(), frozenset(),
                QuestionFrame(domain=frame.get("domain"), horizon_start=ref.toordinal(), horizon_end=end.toordinal()))
            axes["best_suited"] = _available(relevance)
    annotations = {key: getattr(w, key) for key in ("confidence_tier", "weakest_link", "robustness",
        "lambda_peak", "null_p", "factor_informativeness", "factor_consequence")}
    annotations.update(strongest_qualification=w.jury.get("conditional_null") if bound else None,
        strongest_coverage=w.jury.get("coverage") if bound else None,
        strongest_provenance=w.jury.get("provenance") if bound else None,
        witness_signature=w.jury.get("witness_signature") if bound else None,
        obstruction=w.obstruction or _unavailable("negative_space_bridge_unadmitted"),
        contest_rows=w.contest_rows if bound else None,
        dissonance=(w.contest_rows > 0) if bound and w.contest_rows is not None else None)
    return {"axes": axes, "anchor_days": anchor, "annotations": annotations}


def _pair(a_id, b_id, a, b, horizon):
    axes = {}
    for name in a["axes"]:
        av, bv = a["axes"][name], b["axes"][name]
        tol = (1 if name == "nearest" else 0 if name == "most_robust" else 0.3/horizon
               if name == "best_suited" else 1/min(a["anchor_days"], b["anchor_days"])
               if a["anchor_days"] and b["anchor_days"] else None)
        if av["value"] is None or bv["value"] is None:
            relation = "unavailable"
        else:
            delta = av["value"] - bv["value"]
            # Stable <= at one-day relevance boundary; no additional tie band.
            if abs(delta) <= tol:
                relation = "tie"
            elif (delta < 0) == (name == "nearest"):
                relation = "A_better"
            else:
                relation = "B_better"
        axes[name] = {"A": av, "B": bv, "relation": relation, "tolerance": tol}
    relations = {axis["relation"] for axis in axes.values()}
    reason = None
    if "unavailable" in relations:
        relation, reason = "incomparable", "unavailable"
    elif {"A_better", "B_better"} <= relations:
        relation, reason = "incomparable", "tradeoff"
    elif "A_better" in relations:
        relation = "A_dominates"
    elif "B_better" in relations:
        relation = "B_dominates"
    else:
        relation = "tie"
    return {"A": a_id, "B": b_id, "axes": axes, "relation": relation, "reason": reason}


def _dominance_cycles(identities, comparisons):
    """Return nontrivial strongly connected components, without recursion.

    Pairwise tolerance ties need not be transitive. Preserve the actual pair
    verdicts, and disclose every cyclic group rather than choosing a winner.
    Two graph walks take O(V + E) beyond the existing pair comparisons.
    """
    edges = {identity: [] for identity in sorted(identities)}
    reverse = {identity: [] for identity in edges}
    for pair in comparisons:
        if pair["relation"] == "A_dominates":
            winner, loser = pair["A"], pair["B"]
        elif pair["relation"] == "B_dominates":
            winner, loser = pair["B"], pair["A"]
        else:
            continue
        edges[winner].append(loser)
        reverse[loser].append(winner)
    visited, finished = set(), []
    for root in edges:
        if root in visited:
            continue
        visited.add(root)
        stack = [(root, iter(edges[root]))]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                finished.append(node)
                stack.pop()
            elif child not in visited:
                visited.add(child)
                stack.append((child, iter(edges[child])))
    visited, cycles = set(), []
    for root in reversed(finished):
        if root in visited:
            continue
        component, pending = [], [root]
        visited.add(root)
        while pending:
            node = pending.pop()
            component.append(node)
            for parent in reverse[node]:
                if parent not in visited:
                    visited.add(parent)
                    pending.append(parent)
        if len(component) > 1:
            cycles.append(sorted(component))
    return sorted(cycles)


class KaTulanaService:
    def compare_windows(self, windows, *, date_from=None, date_to=None, question_frame=None, preference=None):
        ref = date.fromisoformat(date_from) if isinstance(date_from, str) else date_from or date.today()
        end = date.fromisoformat(date_to) if isinstance(date_to, str) else date_to or ref + timedelta(days=90)
        horizon = (end-ref).days
        if horizon < 1:
            raise ValueError("date_to must exceed date_from by at least one day")
        if question_frame is not None and (not isinstance(question_frame, dict) or
            any(key not in {"domain", "entity", "horizon", "intent_verb", "stakes", "comparison_target"}
                or not isinstance(value, str) for key, value in question_frame.items())):
            raise ValueError("invalid question_frame")
        default = (["best_suited"] if question_frame is not None else []) + ["most_robust", "strongest", "nearest"]
        preference = [] if preference is None else preference
        if not isinstance(preference, list) or any(p not in default for p in preference) or len(set(preference)) != len(preference):
            raise ValueError("preference must name unique active axes")
        policy = preference + [axis for axis in default if axis not in preference]
        parsed = [WindowInput.model_validate(w) if not isinstance(w, WindowInput) else w for w in windows]
        if len({w.window_id for w in parsed}) != len(parsed):
            raise ValueError("duplicate window_id")
        if len({(w.chart_id, w.field_snapshot_id) for w in parsed}) > 1:
            raise ValueError("mixed chart/field snapshot")
        evidence, rejected = {}, []
        for w in parsed:
            if w.window_start and w.window_end and w.window_end < w.window_start:
                raise ValueError("invalid window span")
            if w.window_end and w.window_end < ref:
                rejected.append({"window_id": w.window_id, "reason": "window_elapsed"})
            else:
                evidence[w.window_id] = _evidence(w, ref, end, question_frame)
        generations = {w.jury["generation"] for w in parsed if _binding(w)}
        if len(generations) > 1:
            raise ValueError("mixed jury generation")
        comparisons = [_pair(a,b,evidence[a],evidence[b],horizon) for a,b in combinations(sorted(evidence),2)]
        dominated = {p["B"] if p["relation"] == "A_dominates" else p["A"]
                     for p in comparisons if p["relation"] in {"A_dominates","B_dominates"}}
        cycles = _dominance_cycles(evidence, comparisons)
        # (I) INTERPRETATION K7-B1: front = undominated OR cycle member.
        # Even an externally dominated cycle retains all of its alternatives;
        # pairwise evidence and caller presentation preferences remain intact.
        cycle_members = {identity for cycle in cycles for identity in cycle}
        front = sorted((set(evidence) - dominated) | cycle_members)
        def order_key(identity):
            key = []
            for axis in policy:
                value = evidence[identity]["axes"][axis]["value"]
                key.extend([value is None, 0 if value is None else value if axis == "nearest" else -value])
            return (*key, identity)
        return copy.deepcopy({"contract_version": VERSION, "evidence": evidence, "comparisons": comparisons,
            "front": front, "dominance_cycles": cycles, "front_rule": "undominated_or_cycle_member",
            "ordered": sorted(evidence, key=order_key),
            "rejected": sorted(rejected, key=lambda r: r["window_id"]), "order_policy": policy,
            "question_frame": question_frame, "entity_not_evaluated": bool(question_frame and "entity" in question_frame),
            "tolerances": {"nearest_days":1, "most_robust":0, "best_suited":0.3/horizon,
                           "strongest":"per_pair_anchor_days"},
            "empty_reason": None if front else "no_candidate_windows" if not evidence else "dominance_front_unresolved"})

    def compare(self, window_a, window_b, reference_date=None, **kwargs):
        """Compatibility entry name: now returns a dominance table, never a fabricated winner."""
        result = self.compare_windows([window_a, window_b], date_from=reference_date, **kwargs)
        a = WindowInput.model_validate(window_a) if not isinstance(window_a, WindowInput) else window_a
        b = WindowInput.model_validate(window_b) if not isinstance(window_b, WindowInput) else window_b
        if a.window_id not in result["evidence"] or b.window_id not in result["evidence"]:
            raise ValueError("elapsed window has no comparison")
        pair = result["comparisons"][0]
        if pair["A"] == a.window_id:
            return pair
        mirror = {"A_better": "B_better", "B_better": "A_better", "A_dominates": "B_dominates",
                  "B_dominates": "A_dominates", "tie": "tie", "unavailable": "unavailable", "incomparable": "incomparable"}
        return {**pair, "A": a.window_id, "B": b.window_id, "relation": mirror[pair["relation"]],
            "axes": {name: {**axis, "A": axis["B"], "B": axis["A"], "relation": mirror[axis["relation"]]}
                     for name, axis in pair["axes"].items()}}

    def read_jury(self, ctx, *, generation=None):
        from services.ka_sangam.jury.reader import read_jury
        return read_jury(ctx, generation=generation)

    def rank_jury_candidates(self, ctx, *, generation):
        from services.ka_sangam.jury.reader import JuryView
        result = self.read_jury(ctx, generation=generation)
        if result.source != "candidate" or any(not isinstance(row, JuryView) for row in result.rows):
            raise ValueError("candidate ranking cannot pool legacy values")
        rows = sorted(result.rows, key=lambda row: (row.dw is None, -row.dw if row.dw is not None else 0,
                                                   row.event_class, row.assertion_id))
        return tuple(RankedJuryWindow(i,row) for i,row in enumerate(rows,1))


@dataclass(frozen=True)
class RankedJuryWindow:
    rank: int
    window: Any


class CompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    windows: list[WindowInput]
    date_from: date | None = None
    date_to: date | None = None
    question_frame: dict[str,str] | None = None
    preference: list[str] | None = None


router = APIRouter()


@router.post("/tulana_compare")
def tulana_compare(request: CompareRequest):
    try:
        return KaTulanaService().compare_windows(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
