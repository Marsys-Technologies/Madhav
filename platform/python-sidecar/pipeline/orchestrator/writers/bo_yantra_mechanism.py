"""
bo_yantra_mechanism — Mechanism object (L2 Bodha, D-2 Lane V-4)
=================================================================
यन्त्र = "instrument/mechanism"

CR-24/CR-25/CR-86 (BRIEF_D2.md Lane V-4): a Mechanism is a named, valenced CGM
subgraph — first-class table + serving face, no longer structurally
subordinate to MSR. This writer promotes two kinds of already-detected
structure into `bodha_mechanisms`:

  1. Motif-derived mechanisms — every bodha_cgm_motifs row (yoga_cluster,
     mutual_reception, parivartana_chain, stellium, mutual_aspect,
     mutual_aspect_triangle) is promoted 1:1, gaining a real valence (derived
     from its member edges' `valence` field — never re-guessed), a real
     edge-strength summary (DR-7 `edge_strength_v1` values already on
     bodha_cgm_edges — this writer never invents a new formula, it aggregates
     the one bo_karanajala already computed), and a centrality summary over its
     member nodes.

  2. Chain/circuit mechanisms (CR-24) — a general-purpose cycle detector runs
     over TWO real relational graphs bo_karanajala already writes: the
     graha-to-graha sign-dispositor graph (`dispositor` edges) and the
     house-to-house "lord sits in" graph (`lordship` + `occupancy` edges
     composed). Any real closed cycle in either graph is served as a
     `dispositor_cycle` / `house_lordship_cycle` mechanism.

     CR-24 names a "10→8→12→10" specimen. VERIFIED LIVE (2026-07-16, read-only
     postgres probe against chart 482012f1, ayanamsha lahiri_chitrapaksha,
     during this lane's implementation): NO such closed house-lordship cycle
     exists on this chart's real D1 topology — house 10's lord (Saturn) sits
     in house 7, not house 8; tracing every house's lord-occupied-house edge
     from this chart never returns to its start except at house 9 (Jupiter,
     self-ruling — a length-1 self-loop, not a multi-house circuit). The
     graha-to-graha sign-dispositor graph is likewise acyclic on this chart
     (every chain terminates at self-ruling Jupiter). Per §F1.7's anti-vacuous
     rule ("a specimen that 'must fire' is verified by firing it, not by
     asserting it") and this brief's own instruction ("if the live chart's
     real circuit differs from the literal description, report what you
     actually find rather than forcing a match"), this writer does NOT
     fabricate a 10→8→12→10 row. Instead it serves what the chart actually
     contains: the REAL dominant structure is a CONVERGENT dispositor chain —
     Sun, Moon, and Mercury (three independent D1 lords) all resolve through
     Saturn → Venus → Jupiter (self-ruling terminus) — emitted as
     `convergent_dispositor_chain` mechanisms. The cycle detector itself is
     fully general (works identically for a true cycle on any other chart or
     ayanamsha); this is a genuine chart-specific finding, not a detector gap.

Idempotency (§N.3): per-chart delete-then-insert, LIGHT writer, one run() call
iterating the 5 canonical ayanamshas.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from brahmagyan import valence_doctrine as _vd
from . import WriterBase, ContextSpec, WriterResult, register
from brahmagyan.graha_vocabulary import to_title
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_yantra_mechanism_v1.0"
SNAPSHOT_TYPE  = "static_natal"

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

MOTIF_MIN_STRENGTH_FOR_MECHANISM = 0.0  # every real motif is promoted (B.10 — no silent drop)

_MECHANISM_INSERT = """
INSERT INTO bodha_mechanisms (
  mechanism_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  mechanism_name, mechanism_class, valence,
  member_node_ids_array, member_edge_ids_array, domains_affected_array,
  edge_strength_avg, edge_strength_min, edge_strength_max,
  edge_strength_formula_version, constituent_ga_vichara_ids_array,
  centrality_summary_jsonb, source_motif_id, fingerprint_hash,
  verification_pass_status, citation_ref, citation_human, computed_at, engine_version
) VALUES (
  %(mechanism_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(mechanism_name)s, %(mechanism_class)s, %(valence)s,
  %(member_node_ids_array)s, %(member_edge_ids_array)s, %(domains_affected_array)s,
  %(edge_strength_avg)s, %(edge_strength_min)s, %(edge_strength_max)s,
  %(edge_strength_formula_version)s, %(constituent_ga_vichara_ids_array)s,
  %(centrality_summary_jsonb)s::jsonb, %(source_motif_id)s, %(fingerprint_hash)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s, %(engine_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, build_id, mechanism_class, fingerprint_hash) DO NOTHING
"""


def _fetch_dict(conn: Any, sql: str, params: list) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return [dict(r) for r in rows]
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]


def _fingerprint(node_ids: list[str], mechanism_class: str) -> str:
    payload = mechanism_class + ":" + ",".join(sorted(str(n) for n in node_ids))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _mechanism_valence(edge_valences: list[str]) -> str:
    """Real valence from member edges' `valence` field (bo_karanajala's
    _typed_edge_fields — now DR-9 graha-nature-aware:
    harmonious/antagonistic/mixed/neutral) — never re-guessed. Delegates to the
    shared valence doctrine's combiner: a 'mixed' member edge, or co-present
    harmonious AND antagonistic edges, → MIXED (the prior two-way logic
    collapsed a 'mixed' edge to neutral, losing it)."""
    return _vd.mechanism_valence_from_edges(edge_valences)


def _edge_strength_summary(edges: list[dict]) -> tuple[float | None, float | None, float | None]:
    strengths = [abs(float(e["computed_strength"])) for e in edges if e.get("computed_strength") is not None]
    if not strengths:
        return None, None, None
    return (round(sum(strengths) / len(strengths), 6), round(min(strengths), 6), round(max(strengths), 6))


def _centrality_summary(nodes: list[dict]) -> dict:
    def _avg(key: str) -> float | None:
        vals = [float(n[key]) for n in nodes if n.get(key) is not None]
        return round(sum(vals) / len(vals), 8) if vals else None
    return {
        "pagerank_avg": _avg("pagerank_score"),
        "eigenvector_avg": _avg("eigenvector_centrality"),
        "betweenness_avg": _avg("betweenness_centrality"),
        "harmonic_avg": _avg("harmonic_centrality"),
        "member_count": len(nodes),
    }


def _make_mechanism(
    chart_id: str, aya: str, build_id: str, now: str,
    mechanism_name: str, mechanism_class: str,
    member_node_ids: list[str], member_edges: list[dict],
    domains: list[str] | None, nodes_by_id: dict[str, dict],
    source_motif_id: str | None, citation_ref: str, citation_human: str,
    valence_override: str | None = None,
) -> dict:
    # valence_override: for a graha-to-house tenancy/affliction mechanism (DR-9),
    # valence is the OCCUPANT graha's own signed valence (natural × dignity ×
    # contact), computed by the caller — the occupancy edge itself is
    # structurally polarity-neutral, so the edge-derived combiner would wrongly
    # read neutral.
    valence = valence_override or _mechanism_valence([e.get("valence") for e in member_edges])
    avg_s, min_s, max_s = _edge_strength_summary(member_edges)
    formula_versions = {e.get("weight_formula_version") for e in member_edges if e.get("weight_formula_version")}
    formula_version = sorted(formula_versions)[0] if len(formula_versions) == 1 else (
        "mixed" if formula_versions else None)
    vichara_ids: list[str] = []
    for e in member_edges:
        for vid in (e.get("constituent_ga_vichara_ids_array") or []):
            if vid not in vichara_ids:
                vichara_ids.append(vid)
    member_nodes = [nodes_by_id[n] for n in member_node_ids if n in nodes_by_id]
    return {
        "mechanism_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "snapshot_type": SNAPSHOT_TYPE,
        "mechanism_name": mechanism_name,
        "mechanism_class": mechanism_class,
        "valence": valence,
        "member_node_ids_array": member_node_ids,
        "member_edge_ids_array": [str(e["edge_id"]) for e in member_edges],
        "domains_affected_array": domains or None,
        "edge_strength_avg": avg_s,
        "edge_strength_min": min_s,
        "edge_strength_max": max_s,
        "edge_strength_formula_version": formula_version,
        "constituent_ga_vichara_ids_array": vichara_ids,
        "centrality_summary_jsonb": json.dumps(_centrality_summary(member_nodes)),
        "source_motif_id": source_motif_id,
        "fingerprint_hash": _fingerprint(member_node_ids, mechanism_class),
        # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
        # "pass" — an unconditional stamp with no verification logic behind it, and a
        # live false-green the serve layer counted as verified. Audited: nothing here
        # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
        "verification_pass_status": UNVERIFIED_DEFAULT,
        "citation_ref": citation_ref,
        "citation_human": citation_human,
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
    }


# ── Motif promotion ───────────────────────────────────────────────────────────

def _promote_motifs(
    conn: Any, chart_id: str, aya: str, build_id: str, now: str,
    edges_by_id: dict[str, dict], nodes_by_id: dict[str, dict],
) -> list[dict]:
    motifs = _fetch_dict(
        conn,
        """SELECT motif_id, motif_name, motif_class, involved_node_ids_array,
                  involved_edge_ids_array, motif_strength
           FROM bodha_cgm_motifs
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    )
    rows: list[dict] = []
    for m in motifs:
        edge_ids = [str(e) for e in (m.get("involved_edge_ids_array") or [])]
        member_edges = [edges_by_id[e] for e in edge_ids if e in edges_by_id]
        node_ids = [str(n) for n in (m.get("involved_node_ids_array") or [])]
        rows.append(_make_mechanism(
            chart_id, aya, build_id, now,
            mechanism_name=m["motif_name"],
            mechanism_class=str(m["motif_class"]),
            member_node_ids=node_ids,
            member_edges=member_edges,
            domains=None,
            nodes_by_id=nodes_by_id,
            source_motif_id=str(m["motif_id"]),
            citation_ref=f"bo_cgm_motifs/{m['motif_id']}",
            citation_human=f"Mechanism promoted from CGM motif: {m['motif_name']}",
        ))
    return rows


# ── Chain/circuit detection (CR-24) ───────────────────────────────────────────

def _find_cycles(adj: dict[str, str]) -> list[list[str]]:
    """adj: {node -> single successor} (each house/graha has at most one
    'lord'/'dispositor' successor in these graphs). Returns every distinct
    cycle (as an ordered list of nodes) reachable by following successors.
    A self-loop (node -> itself, e.g. a self-ruling graha/house) is NOT
    reported as a cycle here — it is the classical 'final dispositor' state,
    already served by bo_cgm_paths, not a circuit."""
    seen_in_cycle: set[str] = set()
    cycles: list[list[str]] = []
    for start in adj:
        if start in seen_in_cycle:
            continue
        path: list[str] = []
        visited: dict[str, int] = {}
        node = start
        while node in adj and node not in visited:
            visited[node] = len(path)
            path.append(node)
            node = adj[node]
        if node in visited and node in adj:
            cycle = path[visited[node]:]
            if len(cycle) >= 2:  # exclude self-loops
                cycles.append(cycle)
                seen_in_cycle.update(cycle)
    return cycles


def _find_convergent_chains(adj: dict[str, str], min_converging: int = 2) -> list[tuple[str, list[str]]]:
    """Finds the longest acyclic chain(s) ending at a terminal (self-ruling /
    no-successor) node, where >=min_converging distinct start nodes converge
    onto the SAME terminal via the SAME final 2+ hops. Returns
    [(terminal, [starts_that_converge])] for the most convergent terminal(s)."""
    terminals: dict[str, list[str]] = {}
    for start in adj:
        node = start
        seen: set[str] = set()
        while node in adj and adj[node] != node and node not in seen:
            seen.add(node)
            node = adj[node]
        terminals.setdefault(node, []).append(start)
    return [(t, starts) for t, starts in terminals.items() if len(starts) >= min_converging]


def _detect_dispositor_cycles_and_chains(
    conn: Any, chart_id: str, aya: str, build_id: str, now: str,
    edges_by_id: dict[str, dict], nodes_by_id: dict[str, dict],
) -> list[dict]:
    """Graha-to-graha sign-dispositor graph (bo_karanajala 'dispositor' edges)."""
    disp_edges = _fetch_dict(
        conn,
        """SELECT e.edge_id, e.from_node_id, e.to_node_id, e.computed_strength,
                  e.weight_formula_version, e.valence, e.constituent_ga_vichara_ids_array,
                  n1.node_subject AS from_subject, n2.node_subject AS to_subject
           FROM bodha_cgm_edges e
           JOIN bodha_cgm_nodes n1 ON n1.node_id = e.from_node_id
           JOIN bodha_cgm_nodes n2 ON n2.node_id = e.to_node_id
           WHERE e.chart_id = %s AND e.ayanamsha_id = %s AND e.edge_type = 'dispositor'""",
        [chart_id, aya],
    )
    if not disp_edges:
        return []
    adj_subject: dict[str, str] = {e["from_subject"]: e["to_subject"] for e in disp_edges}
    edge_by_pair = {(e["from_subject"], e["to_subject"]): e for e in disp_edges}
    subject_to_node: dict[str, str] = {}
    for e in disp_edges:
        subject_to_node[e["from_subject"]] = str(e["from_node_id"])
        subject_to_node[e["to_subject"]] = str(e["to_node_id"])

    rows: list[dict] = []

    cycles = _find_cycles(adj_subject)
    for cycle in cycles:
        member_node_ids = [subject_to_node[s] for s in cycle]
        pairs = list(zip(cycle, cycle[1:] + cycle[:1]))
        member_edges = [edge_by_pair[p] for p in pairs if p in edge_by_pair]
        member_edges_full = [
            {"edge_id": e["edge_id"], "computed_strength": e["computed_strength"],
             "weight_formula_version": e["weight_formula_version"], "valence": e["valence"],
             "constituent_ga_vichara_ids_array": e.get("constituent_ga_vichara_ids_array") or []}
            for e in member_edges
        ]
        label = " → ".join(cycle + [cycle[0]])
        rows.append(_make_mechanism(
            chart_id, aya, build_id, now,
            mechanism_name=f"Dispositor cycle: {label}",
            mechanism_class="dispositor_cycle",
            member_node_ids=member_node_ids,
            member_edges=member_edges_full,
            domains=None,
            nodes_by_id=nodes_by_id,
            source_motif_id=None,
            citation_ref=f"bo_yantra_mechanism/dispositor_cycle/{'_'.join(cycle)}",
            citation_human=f"Closed sign-dispositor cycle (CR-24 circuit class): {label}",
        ))

    if not cycles:
        # CR-24 anti-vacuous disposition: no real cycle exists on this chart's
        # sign-dispositor graph. Serve the real dominant structure instead —
        # the convergent chain(s) onto a self-ruling terminus.
        convergent = _find_convergent_chains(adj_subject, min_converging=2)
        for terminal, starts in convergent:
            all_nodes: list[str] = []
            all_edges: list[dict] = []
            seen_pairs: set[tuple[str, str]] = set()
            for s in starts:
                node = s
                while node in adj_subject:
                    nxt = adj_subject[node]
                    if (node, nxt) not in seen_pairs:
                        seen_pairs.add((node, nxt))
                        e = edge_by_pair.get((node, nxt))
                        if e:
                            all_edges.append({
                                "edge_id": e["edge_id"], "computed_strength": e["computed_strength"],
                                "weight_formula_version": e["weight_formula_version"], "valence": e["valence"],
                                "constituent_ga_vichara_ids_array": e.get("constituent_ga_vichara_ids_array") or [],
                            })
                    if subject_to_node.get(node) not in all_nodes:
                        all_nodes.append(subject_to_node.get(node))
                    if nxt == node:
                        break
                    node = nxt
                if subject_to_node.get(node) not in all_nodes:
                    all_nodes.append(subject_to_node.get(node))
            all_nodes = [n for n in all_nodes if n]
            label = ", ".join(f"{s} → … → {terminal}" for s in starts)
            rows.append(_make_mechanism(
                chart_id, aya, build_id, now,
                mechanism_name=f"Convergent dispositor chain onto {terminal}: {label}",
                mechanism_class="convergent_dispositor_chain",
                member_node_ids=all_nodes,
                member_edges=all_edges,
                domains=None,
                nodes_by_id=nodes_by_id,
                source_motif_id=None,
                citation_ref=f"bo_yantra_mechanism/convergent_dispositor_chain/{terminal}",
                citation_human=(
                    f"CR-24 disposition (verified live, no closed circuit on this chart): "
                    f"{len(starts)} grahas ({', '.join(starts)}) converge onto self-ruling "
                    f"{terminal} — the real dominant chain/circuit-class structure this "
                    f"chart carries."
                ),
            ))
    return rows


def _detect_house_lordship_cycles_and_chains(
    conn: Any, chart_id: str, aya: str, build_id: str, now: str,
    nodes_by_id: dict[str, dict],
) -> list[dict]:
    """House-to-house 'lord sits in' graph: house H -> house(lord-of-H's D1
    occupied house), composed from bo_karanajala's 'lordship' (house -> lord
    graha) + 'occupancy' (graha -> occupied house) edges. This is the
    house-level analogue CR-24's '10→8→12→10' specimen describes."""
    lordship = _fetch_dict(
        conn,
        """SELECT edge_properties_jsonb->>'graha' AS lord, (edge_properties_jsonb->>'house')::int AS house
           FROM bodha_cgm_edges
           WHERE chart_id = %s AND ayanamsha_id = %s AND edge_type = 'lordship'""",
        [chart_id, aya],
    )
    occupancy = _fetch_dict(
        conn,
        """SELECT edge_properties_jsonb->>'graha' AS graha, (edge_properties_jsonb->>'house')::int AS house,
                  edge_id, computed_strength, weight_formula_version, valence, constituent_ga_vichara_ids_array
           FROM bodha_cgm_edges
           WHERE chart_id = %s AND ayanamsha_id = %s AND edge_type = 'occupancy'""",
        [chart_id, aya],
    )
    if not lordship or not occupancy:
        return []
    occ_house_by_graha = {r["graha"]: r["house"] for r in occupancy}
    occ_edge_by_graha = {r["graha"]: r for r in occupancy}
    house_node = {}
    for r in _fetch_dict(
        conn,
        """SELECT node_id, node_subject FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s AND node_type = 'bhava'""",
        [chart_id, aya],
    ):
        house_node[str(r["node_subject"])] = str(r["node_id"])

    adj_house: dict[int, int] = {}
    edge_by_house_pair: dict[tuple[int, int], dict] = {}
    for r in lordship:
        h, lord = r["house"], r["lord"]
        sits_in = occ_house_by_graha.get(lord)
        if sits_in is None:
            continue
        adj_house[h] = sits_in
        occ_e = occ_edge_by_graha.get(lord)
        if occ_e:
            edge_by_house_pair[(h, sits_in)] = occ_e

    adj_str = {str(k): str(v) for k, v in adj_house.items()}
    cycles = _find_cycles(adj_str)
    rows: list[dict] = []
    for cycle in cycles:
        member_node_ids = [house_node[h] for h in cycle if h in house_node]
        pairs = list(zip([int(c) for c in cycle], [int(c) for c in cycle[1:]] + [int(cycle[0])]))
        member_edges = []
        for p in pairs:
            e = edge_by_house_pair.get(p)
            if e:
                member_edges.append({
                    "edge_id": e["edge_id"], "computed_strength": e["computed_strength"],
                    "weight_formula_version": e["weight_formula_version"], "valence": e["valence"],
                    "constituent_ga_vichara_ids_array": e.get("constituent_ga_vichara_ids_array") or [],
                })
        label = " → ".join(cycle + [cycle[0]])
        rows.append(_make_mechanism(
            chart_id, aya, build_id, now,
            mechanism_name=f"House-lordship cycle: {label}",
            mechanism_class="house_lordship_cycle",
            member_node_ids=member_node_ids,
            member_edges=member_edges,
            domains=None,
            nodes_by_id=nodes_by_id,
            source_motif_id=None,
            citation_ref=f"bo_yantra_mechanism/house_lordship_cycle/{'_'.join(cycle)}",
            citation_human=f"Closed house-lordship circuit (CR-24's named specimen class): {label}",
        ))
    if not cycles:
        logger.info(
            "[bo_yantra_mechanism] %s — CR-24: no closed house-lordship cycle found "
            "(verified: %s); the '10→8→12→10' specimen does not exist on this chart's "
            "real D1 topology — reported honestly, not fabricated.",
            aya, {h: adj_house.get(h) for h in sorted(adj_house)},
        )
    return rows


# ── Graha-to-house tenancy / affliction mechanisms (DR-9 / VAL-ROOT) ─────────

# Wealth/loss-relevant houses whose adverse tenancy D-3's retrodiction needs as
# first-class valenced Mechanism objects (the 2025-05 loss/financial_deception
# LEL event retrodicts to Rahu-occupies-dhana). dhana(2)/labha(11) + the three
# dusthānas(6/8/12).
_TENANCY_HOUSES = {
    2: "dhana (2nd)", 6: "ari (6th)", 8: "randhra (8th)",
    11: "labha (11th)", 12: "vyaya (12th)",
}


def _detect_tenancy_afflictions(
    conn: Any, chart_id: str, aya: str, build_id: str, now: str,
    nodes_by_id: dict[str, dict],
) -> list[dict]:
    """DR-9 / VAL-ROOT scope addition: a graha-to-house tenancy is a
    representable, valenced Mechanism object. Emits one 'graha_bhava_affliction'
    mechanism per graha whose OWN valence (natural × dignity incl. node
    exaltation × occupancy contact) is adverse (malefic/mixed) in a
    wealth/loss-relevant house — 'Rahu occupies dhana bhāva' becomes a served,
    valenced mechanism (the D-3 retrodiction target), no longer invisible."""
    positions = _fetch_dict(
        conn,
        """SELECT fact_subject, fact_key, fact_value_text, fact_value_num
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_position'
             AND fact_key IN ('house_d1', 'sign')""",
        [chart_id, aya],
    )
    by_graha: dict[str, dict] = {}
    for p in positions:
        subj = str(p["fact_subject"]).upper()
        by_graha.setdefault(subj, {})[p["fact_key"]] = (
            p["fact_value_text"] if p["fact_key"] == "sign" else p["fact_value_num"])

    # Node-id lookups: graha nodes (title-case subject → id), bhava nodes (num → id).
    graha_node_by_code: dict[str, str] = {}
    bhava_node_by_num: dict[int, str] = {}
    for nid, n in nodes_by_id.items():
        if n.get("node_type") == "graha":
            graha_node_by_code[_vd.norm_graha(n.get("node_subject"))] = nid
        elif n.get("node_type") == "bhava":
            try:
                bhava_node_by_num[int(n.get("node_subject"))] = nid
            except (TypeError, ValueError):
                pass

    rows: list[dict] = []
    for subj, rec in by_graha.items():
        code = _vd.norm_graha(subj)
        house = rec.get("house_d1")
        sign = rec.get("sign")
        if house is None:
            continue
        house = int(house)
        if house not in _TENANCY_HOUSES:
            continue
        verdict = _vd.graha_valence(
            code, contact_type="occupancy", target_house=house, graha_sign=sign)
        # Only adverse tenancies are "afflictions" — a benefic in the house is
        # not an affliction mechanism (B.10: never fabricate an adverse claim).
        if verdict.valence not in (_vd.MALEFIC, _vd.MIXED):
            continue
        g_node = graha_node_by_code.get(code)
        b_node = bhava_node_by_num.get(house)
        member_ids = [x for x in (g_node, b_node) if x]
        if not member_ids:
            continue
        display = SUBJECT_DISPLAY.get(code, subj.title())
        label = _TENANCY_HOUSES[house]
        rows.append(_make_mechanism(
            chart_id=chart_id, aya=aya, build_id=build_id, now=now,
            mechanism_name=f"{display} occupies {label} bhāva ({verdict.valence})",
            mechanism_class="graha_bhava_affliction",
            member_node_ids=member_ids, member_edges=[],
            domains=["wealth"] if house in (2, 11) else None,
            nodes_by_id=nodes_by_id, source_motif_id=None,
            citation_ref=f"graha_position/{code}/H{house}",
            citation_human=(f"{display} ({sign}) tenants the {label} bhāva — "
                            f"valence {verdict.valence} (net {verdict.value_num:+.2f}); "
                            f"natural {verdict.natural_score:+.1f}, "
                            f"dignity {verdict.dignity_mod:+.2f}"),
            valence_override=verdict.valence,
        ))
    return rows


# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2 (found via the full-tree census; not one of the originally-
# enumerated retirement targets).
SUBJECT_DISPLAY = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
}


@register("bo_yantra_mechanism")
class BoYantraMechanismWriter(WriterBase):
    """bo_yantra_mechanism: Mechanism object — named, valenced CGM subgraphs."""
    asset_id = "bo_yantra_mechanism"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes="dry_run — would promote motifs + detect dispositor/house-lordship chains+cycles")

        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")
            cur.execute("DELETE FROM bodha_mechanisms WHERE chart_id = %s", [chart_id])

        total = 0
        for aya in CANONICAL_AYAS:
            all_nodes = _fetch_dict(
                conn,
                """SELECT node_id, node_type, node_subject, pagerank_score,
                          eigenvector_centrality, betweenness_centrality, harmonic_centrality
                   FROM bodha_cgm_nodes
                   WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
                [chart_id, aya, SNAPSHOT_TYPE],
            )
            if not all_nodes:
                logger.info("[bo_yantra_mechanism] %s — no CGM nodes; skipping", aya)
                continue
            nodes_by_id = {str(n["node_id"]): n for n in all_nodes}

            all_edges = _fetch_dict(
                conn,
                """SELECT edge_id, from_node_id, to_node_id, edge_type, computed_strength,
                          weight_formula_version, valence, constituent_ga_vichara_ids_array
                   FROM bodha_cgm_edges
                   WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
                [chart_id, aya, SNAPSHOT_TYPE],
            )
            edges_by_id = {str(e["edge_id"]): e for e in all_edges}

            rows: list[dict] = []
            rows.extend(_promote_motifs(conn, chart_id, aya, build_id, now, edges_by_id, nodes_by_id))
            rows.extend(_detect_dispositor_cycles_and_chains(
                conn, chart_id, aya, build_id, now, edges_by_id, nodes_by_id))
            rows.extend(_detect_house_lordship_cycles_and_chains(
                conn, chart_id, aya, build_id, now, nodes_by_id))
            rows.extend(_detect_tenancy_afflictions(
                conn, chart_id, aya, build_id, now, nodes_by_id))

            inserted = 0
            with conn.cursor() as cur:
                for row in rows:
                    cur.execute(_MECHANISM_INSERT, row)
                    inserted += 1
            total += inserted
            logger.info("[bo_yantra_mechanism] %s — %d mechanisms written", aya, inserted)

        return WriterResult(
            asset_id=self.asset_id, rows_inserted=total,
            notes=f"mechanisms={total} across {len(CANONICAL_AYAS)} ayanamshas",
        )
