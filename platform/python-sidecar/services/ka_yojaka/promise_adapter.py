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
from brahmagyan.verification_vocab import TWO_PASS_VERIFIED

from services.gochara_rules.registry import YOGA_EVENT_MAP
from services.kala_core.promise import (
    Conclusion, Defeat, EdgePolarity, EventRelation, FactState, Mechanism, MechanismRoute,
    PromiseEdge, PromiseGraph, PromiseNode,
    UnassessedReason,
)
from services.ka_yojaka.structural_adapter import structural_bundle
from services.ka_yojaka.attachment_adapter import attach_sources


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
                 *, bindings=EVENT_BINDINGS, cgm=(), pratijna=(), served_locators=()) -> list[dict]:
    """Retain formations; compute only sourced, convention-local conclusions.

    Cancellation adapter contract: L0 bhanga_rules_jsonb must name kind, rule_id,
    version, locator, target canonical yoga and event class. L1 grounds_jsonb
    must separately name cancellation_evidence[{rule_id,fact_ids}]. Older
    producers without a sourced target are unqualified, never guessed. A named
    fired target with absent/ambiguous evidence stays unresolved. NBRY's
    flag describes its own formation; only a separately identified target can
    be defeated. These contracts do not write or alter either source layer.
    """
    facts = list(facts)
    firings = sorted((r for r in firings if r.get("fired") is True),
                     key=lambda r: (str(r["ayanamsha_id"]), str(r["yoga_canonical_id"])))
    signals = list(signals)
    cgm, pratijna = list(cgm), list(pratijna)
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
        target = _target(fact_ids, local_facts)
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
                    FactState(state), fact_ids,
                    # (I) INTERPRETATION: use only the existing explicit target
                    # identity and sourced binding relation; no target fallback.
                    target_id=target['identity'] if target else None,
                    valence=(None if binding.relation == EventRelation.CONDITIONS else
                             EdgePolarity(binding.relation)),
                    event_relation=EventRelation(binding.relation)))
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
                cancellation_unqualified=[], target=target,
                constituent_planets=list(firing.get("constituent_planets") or []),
                yoga_tier=firing.get('verification_pass_status'),
                null_reason=(None if firing.get('verification_pass_status') is not None else
                             'ga_yoga_firings_carries_no_verification_tier'),
                judgment_flags=[] if firing.get('verification_pass_status') is not None else ['yoga_tier_unavailable'],
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
        retained = False
        for spec in specs if isinstance(specs, list) else []:
            if not isinstance(spec, dict) or not all(spec.get(k) for k in (
                "rule_id", "rule_version", "source_locator", "target_yoga_canonical_id", "target_event_class_id")):
                continue
            # The fired rule must match exactly; evidence cardinality cannot
            # erase its separately named target.
            if firing.get("bhanga_rule_fired") != spec["rule_id"] or spec.get("kind") not in {"defeats", "excepts"}:
                continue
            if canonical == "neecha_bhanga_raja_yoga" and spec["target_yoga_canonical_id"] == canonical:
                continue
            cid = f"{ayan}:{spec['target_yoga_canonical_id']}:{spec['target_event_class_id']}:conclusion"
            target = by_conclusion.get(cid)
            if not target or target["conclusion_id"] not in graphs[ayan].conclusions:
                continue
            records = [e for e in evidence if isinstance(e, dict) and e.get("rule_id") == spec["rule_id"]] if isinstance(evidence, list) else []
            evidence_reason = (UnassessedReason.DEFEAT_EVIDENCE_MISSING if not records else
                               UnassessedReason.DEFEAT_EVIDENCE_AMBIGUOUS if len(records) > 1 else None)
            # (I) INTERPRETATION: duplicate records, even identical ones, remain
            # ambiguous. Their union of ids is audit data, never earned grounding.
            refs = _ids([fact_id for record in records for fact_id in _ids(record.get("fact_ids"))])
            # Retain named evidence even when its roots are missing: the graph
            # earns defeat only after grounding, otherwise it reports unresolved.
            # (I) INTERPRETATION: identify each evidence row by its L1 firing id,
            # target conclusion, kind and sourced rule id.
            defeat = Defeat(cid, refs, spec["rule_id"], spec["kind"],
                defeat_id=f"ga_yoga_firings:{firing['id']}:{cid}:{spec['kind']}:{spec['rule_id']}",
                evidence_reason=evidence_reason)
            graphs[ayan].add_defeat(defeat)
            target[spec["kind"]].append({**asdict(defeat), "fact_ids": list(refs),
                "rule_version": spec["rule_version"], "source_locator": spec["source_locator"],
                "evidence_records": [dict(record) for record in records]})
            retained = True
        if not retained and canonical != "neecha_bhanga_raja_yoga":
            for row in output:
                if row["ayanamsha_id"] == ayan and row["canonical_id"] == canonical:
                    row["cancellation_unqualified"].append("missing_sourced_target_or_evidence")
    for row in output:
        graph = graphs[row["ayanamsha_id"]]
        if row["conclusion_id"] in graph.conclusions and row["fact_state"] == "present":
            result = graph.effective_result(row["conclusion_id"], available.get(row["ayanamsha_id"], {}))
            if not row['cancellation_unqualified'] or result.null_reason is not None:
                row["effective_state"] = result.state.value
            if result.null_reason is not None:
                row['effective_reason'] = dict(null_reason=result.null_reason.value,
                    conclusion_ids=list(result.conclusion_ids), defeat_ids=list(result.defeat_ids))
                if result.null_reason is UnassessedReason.MISSING_DEFEAT_FACTS:
                    row['effective_reason']['missing_fact_ids'] = list(result.missing_fact_ids)
                if result.null_reason in {UnassessedReason.DEFEAT_EVIDENCE_MISSING,
                                          UnassessedReason.DEFEAT_EVIDENCE_AMBIGUOUS}:
                    row['effective_reason']['evidence_fact_ids'] = list(result.evidence_fact_ids)
                row['null_reason'] = result.null_reason.value
                row['judgment_flags'].append(result.null_reason.value)
            row["scored"] = row["effective_state"] == "in_force"
    output.extend(structural_bundle(facts, served_locators=served_locators))
    attached = {signal_id for row in output for signal_id in row["attachments"]}
    for signal in sorted(signals, key=lambda s: str(s["signal_id"])):
        signal_id, ayan = str(signal["signal_id"]), str(signal["ayanamsha_id"])
        config = signal.get('configuration_jsonb') or {}
        equivalent = any(signal_id in row['attachments']
                         and config.get('event_class_id') == row['event_class_id']
                         and not config.get('assumptions') for row in output)
        # (I) INTERPRETATION: a signal without an event proposal or assumptions
        # is only an attachment; explicit distinct proposals remain testimony.
        if signal_id in attached and (equivalent or not config):
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
    attach_sources(output, available, signals, cgm, pratijna)
    return sorted(output, key=mechanism_density_key)


def bind_signal_ids(rows: Iterable[Mapping]) -> dict[tuple[str, str | None], str]:
    """The MSR signal each candidate row belongs to, keyed (mechanism_id, event_class_id).

    (I) INTERPRETATION: the table's identity is one row per (chart, signal,
    ayanamsha, generation) (idx_kap_chart_signal_ayan_generation) while the F1
    graph is many rows per signal. A row therefore *belongs to* a signal only
    when that is unambiguous: a testimony row is its own signal's row; an
    admitted row belongs to its sole attached signal when no other row of the
    same convention lists that signal. Rows with no, several or a shared
    signal are absent from the result and keep an honest NULL (§N.7.6); no
    signal is chosen, defaulted or invented for them.
    """
    rows = list(rows)
    listed: dict[tuple[str, str], int] = {}
    for row in rows:
        for signal_id in row["attachments"]:
            key = (str(row["ayanamsha_id"]), str(signal_id))
            listed[key] = listed.get(key, 0) + 1
    bound = {}
    for row in rows:
        attachments = list(row["attachments"])
        if len(attachments) != 1:
            continue
        key = (str(row["ayanamsha_id"]), str(attachments[0]))
        if row["route"] == "testimony" or listed[key] == 1:
            bound[(row["mechanism_id"], row["event_class_id"])] = str(attachments[0])
    return bound


def mechanism_density_key(row):
    """Earned fact verification precedes an unavailable yoga verification tier."""
    if row.get('null_reason') in {reason.value for reason in UnassessedReason}:
        return (2, str(row['mechanism_id']))
    tiers = row.get('constituent_fact_tiers') or {}
    fact_verified = bool(row.get('fact_ids')) and set(tiers) == set(row['fact_ids']) and all(
        tier == TWO_PASS_VERIFIED for tier in tiers.values())
    unverified_yoga = bool(row.get('canonical_id')) and row.get('yoga_tier') != TWO_PASS_VERIFIED
    rank = 0 if fact_verified and not unverified_yoga else 1 if unverified_yoga else 2
    return (rank, str(row['mechanism_id']))
