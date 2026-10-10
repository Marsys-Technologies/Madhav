"""Read-only L1 formation adapter; event bindings are separate reviewable rows.

The canonical ids below are from brahmagyan.l0_yogas, not the Y-* rule ids.
Only the four unambiguous natal definitions in the served registry are bound.
Other formations (including NBRY) are retained with an unresolved event class.
No rule is inferred from a name, an L2 selection, or a bare bhanga_active flag.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from collections.abc import Iterable, Mapping

from services.gochara_rules.registry import YOGA_EVENT_MAP
from services.kala_core.promise import (
    Conclusion, Defeat, EdgePolarity, FactState, Mechanism, MechanismRoute,
    PromiseEdge, PromiseGraph, PromiseNode,
)


@dataclass(frozen=True)
class EventBinding:
    canonical_id: str
    event_class_id: str
    rule_id: str
    rule_version: str
    source: str
    frame: str = "moon"
    relation: str = "supports"
    source_status: str = "verse_cited"
    ocr_degradation: str | None = None


EVENT_BINDINGS = tuple(
    EventBinding(canonical, event_class, rule_id, "PROMISE_NATURE_YOGA_MAP_v1_1",
                 f"{row['source']}; {row['citation']['text']}:{row['citation']['locator']}:"
                 f"{row['citation']['sloka']}", source_status=row['provenance'],
                 ocr_degradation=row['ocr_degradation'])
    for canonical, rule_id in (
        ("adhi_yoga", "Y-ADHI"), ("sunapha", "Y-SUNAPHA"),
        ("anapha", "Y-ANAPHA"), ("durudhara", "Y-DURADHARA"),
    )
    for row in (YOGA_EVENT_MAP[rule_id],)
    for event_class in row["event_classes"]
)


def _ids(value) -> tuple[str, ...]:
    return tuple(sorted({str(v) for v in value})) if isinstance(value, (list, tuple)) else ()


def _version(row: Mapping) -> str | None:
    """Content-address the L0 rule and citations: the catalog has no version column."""
    if not row.get("formation_rule_jsonb"):
        return None
    return hashlib.sha256(json.dumps(
        [row.get("formation_rule_jsonb"), row.get("classical_citations")],
        sort_keys=True, separators=(",", ":"), default=str,
    ).encode()).hexdigest()


def _target(fact_ids, facts):
    # A single, explicitly referenced longitude is usable; no first-root guess.
    candidates = []
    for fact_id in fact_ids:
        row = facts.get(fact_id)
        if not row or row.get("fact_category") != "graha_position":
            continue
        if row.get("fact_key") != "longitude_sidereal":
            continue
        if row.get("unit") not in {"degrees", "deg"} or row.get("fact_value_num") is None:
            continue
        longitude = float(row["fact_value_num"])
        if not math.isfinite(longitude) or not 0 <= longitude < 360:
            continue
        candidates.append(dict(fact_id=fact_id, identity=f"graha:{row['fact_subject']}",
                               longitude_deg=longitude))
    return candidates[0] if len(candidates) == 1 else None


def build_bundle(facts: Iterable[Mapping], firings: Iterable[Mapping], signals: Iterable[Mapping],
                 *, bindings=EVENT_BINDINGS) -> list[dict]:
    """Retain formations; compute only sourced, convention-local conclusions.

    Cancellation adapter contract: L0 bhanga_rules_jsonb must name kind, rule_id,
    version, locator, target canonical yoga and event class. L1 grounds_jsonb
    must separately name cancellation_evidence[{rule_id,fact_ids}]. Older
    producers without that information are unqualified, never guessed. NBRY's
    flag describes its own formation; only a separately identified target can
    be defeated. These contracts do not write or alter either source layer.
    """
    facts = list(facts)
    firings = sorted((r for r in firings if r.get("fired") is True),
                     key=lambda r: (str(r["ayanamsha_id"]), str(r["yoga_canonical_id"])))
    signals = list(signals)
    graphs: dict[str, PromiseGraph] = {}
    available: dict[str, dict] = {}
    for fact in facts:
        available.setdefault(str(fact["ayanamsha_id"]), {})[str(fact["fact_id"])] = fact
    output = []
    for firing in firings:
        ayan, canonical = str(firing["ayanamsha_id"]), str(firing["yoga_canonical_id"])
        fact_ids = _ids(firing.get("constituent_fact_ids"))
        graph = graphs.setdefault(ayan, PromiseGraph())
        local_facts = available.get(ayan, {})
        state = "present" if fact_ids and set(fact_ids) <= local_facts.keys() else "missing_fact"
        source = json.dumps({"l1": f"ga_yoga_firings:{firing['id']}", "l0": canonical,
                             "citations": firing.get("classical_citations") or []}, sort_keys=True)
        matches = [b for b in bindings if b.canonical_id == canonical]
        ambiguous = len({b.event_class_id for b in matches}) != len(matches)
        qualified = bool(matches) and not ambiguous and bool(firing.get("formation_rule_jsonb")) and bool(firing.get("classical_citations"))
        for binding in matches if qualified else (None,):
            event_class = binding.event_class_id if binding else None
            mechanism_id = f"{ayan}:{canonical}:{event_class or 'unqualified'}"
            conclusion_id = f"{mechanism_id}:conclusion"
            formation_node = f"{ayan}:yoga:{canonical}"
            graph_nodes, graph_edges = [], []
            if qualified and fact_ids:
                if formation_node not in graph.nodes:
                    graph.add_node(PromiseNode(formation_node, "yoga", fact_ids))
                participants = []
                for fact_id in fact_ids:
                    node_id = f"{ayan}:fact:{fact_id}"
                    if node_id not in graph.nodes:
                        graph.add_node(PromiseNode(node_id, "L1_fact", (fact_id,)))
                    edge = PromiseEdge(node_id, formation_node, "yoga_constituency",
                        EdgePolarity.SUPPORTS, binding.frame, canonical, _version(firing), source)
                    graph.add_edge(edge)
                    participants.append(node_id)
                    graph_edges.append(asdict(edge))
                graph.add_mechanism(Mechanism(mechanism_id, MechanismRoute.ADMITTED,
                    event_class, (formation_node, *participants), fact_ids, binding.source))
                graph.add_conclusion(Conclusion(conclusion_id, mechanism_id,
                    FactState(state), fact_ids))
                graph_nodes = [asdict(graph.nodes[n]) for n in (formation_node, *participants)]
            output.append(dict(
                mechanism_id=mechanism_id, conclusion_id=conclusion_id,
                canonical_id=canonical, ayanamsha_id=ayan, event_class_id=event_class,
                route="admitted", formation_state="present",
                fact_state=state, fact_ids=list(fact_ids), rule_version=_version(firing),
                source=source, binding=asdict(binding) if binding else None,
                graph_nodes=graph_nodes, graph_edges=graph_edges,
                qualification=("sourced" if qualified else "ambiguous_event_binding" if ambiguous else
                    "missing_l0_rule" if not firing.get("formation_rule_jsonb") or not firing.get("classical_citations") else "unbound_event_class"),
                effective_state="unresolved", scored=False, defeats=[], excepts=[],
                cancellation_unqualified=[], target=_target(fact_ids, local_facts),
                constituent_planets=list(firing.get("constituent_planets") or []),
                attachments=sorted({str(s["signal_id"]) for s in signals
                    if str(s["ayanamsha_id"]) == ayan and fact_ids
                    and set(fact_ids) <= set(_ids(s.get("constituent_facts_array")))}),
            ))
    by_conclusion = {r["conclusion_id"]: r for r in output}
    for firing in firings:
        if firing.get("bhanga_active") is not True:
            continue
        ayan, canonical = str(firing["ayanamsha_id"]), str(firing["yoga_canonical_id"])
        specs = firing.get("bhanga_rules_jsonb") or []
        grounds = firing.get("grounds_jsonb") or {}
        evidence = grounds.get("cancellation_evidence", []) if isinstance(grounds, dict) else []
        applied = False
        for spec in specs if isinstance(specs, list) else []:
            if not isinstance(spec, dict) or not all(spec.get(k) for k in (
                "rule_id", "rule_version", "source_locator", "target_yoga_canonical_id", "target_event_class_id")):
                continue
            # A matching L1 evaluation is mandatory; no substring matching.
            records = [e for e in evidence if e.get("rule_id") == spec["rule_id"]]
            if len(records) != 1 or firing.get("bhanga_rule_fired") != spec["rule_id"] or spec.get("kind") not in {"defeats", "excepts"}:
                continue
            if canonical == "neecha_bhanga_raja_yoga" and spec["target_yoga_canonical_id"] == canonical:
                continue
            cid = f"{ayan}:{spec['target_yoga_canonical_id']}:{spec['target_event_class_id']}:conclusion"
            target = by_conclusion.get(cid)
            refs = _ids(records[0].get("fact_ids"))
            if not target or target["conclusion_id"] not in graphs[ayan].conclusions or not refs or not set(refs) <= available.get(ayan, {}).keys():
                continue
            defeat = Defeat(cid, refs, spec["rule_id"], spec["kind"])
            graphs[ayan].add_defeat(defeat)
            target[spec["kind"]].append({**asdict(defeat), "fact_ids": list(refs),
                "rule_version": spec["rule_version"], "source_locator": spec["source_locator"]})
            applied = True
        if not applied and canonical != "neecha_bhanga_raja_yoga":
            for row in output:
                if row["ayanamsha_id"] == ayan and row["canonical_id"] == canonical:
                    row["cancellation_unqualified"].append("missing_sourced_target_or_evidence")
    for row in output:
        graph = graphs[row["ayanamsha_id"]]
        if row["conclusion_id"] in graph.conclusions and row["fact_state"] == "present" and not row["cancellation_unqualified"]:
            row["effective_state"] = graph.effective_state(row["conclusion_id"], available.get(row["ayanamsha_id"], {})).value
            row["scored"] = row["effective_state"] == "in_force"
    attached = {signal_id for row in output for signal_id in row["attachments"]}
    for signal in sorted(signals, key=lambda s: str(s["signal_id"])):
        signal_id, ayan = str(signal["signal_id"]), str(signal["ayanamsha_id"])
        if signal_id in attached:
            continue
        refs = _ids(signal.get("constituent_facts_array"))
        config = signal.get("configuration_jsonb") or {}
        # Explicit L2 proposals survive but cannot enlarge scored promise.
        from services.kala_core.ontology import CLASS_ROSTER
        event_class = config.get("event_class_id")
        if event_class not in CLASS_ROSTER:
            event_class = None
        mid = f"{ayan}:testimony:{signal_id}"
        output.append(dict(mechanism_id=mid, conclusion_id=f"{mid}:conclusion",
            canonical_id=None, ayanamsha_id=ayan, event_class_id=event_class,
            route="testimony", formation_state="proposed", fact_state=("present" if refs and set(refs) <= available.get(ayan, {}).keys() else "missing_fact"),
            fact_ids=list(refs), rule_version="L2-proposal-v1", source=f"bodha_msr_signals:{signal_id}",
            binding=None, qualification="unreviewed_testimony", effective_state="unresolved",
            scored=False, defeats=[], excepts=[], cancellation_unqualified=[],
            target=_target(refs, available.get(ayan, {})), constituent_planets=[], attachments=[signal_id],
            assumptions=config.get("assumptions"),
        ))
    return output
