"""
bo_cgm_motifs — CGM Structural Motif + Topology + Sub-graph layer (L2 Bodha)
=============================================================================
आकृति = "pattern/form"

Reads bodha_cgm_nodes + bodha_cgm_edges (written by bo_bimba + bo_karanajala)
and derives the CGM topology layer over the *real* node+edge set:

  1. MOTIFS      → bodha_cgm_motifs               (recurring structural patterns)
  2. SUB-GRAPHS  → bodha_cgm_sub_graphs           (connected components / neighborhoods)
  3. TOPOLOGY    → bodha_cgm_chart_topology_summary (graph-level structural facts)

All three are emitted per ayanamsha from a single deterministic pass over the
graph — no LLM, no invented values (B.10). Every structural claim carries edge
lineage (involved_edge_ids_array / edge_ids_array) that resolves through
bodha_cgm_edges.constituent_fact_ids_array back to chart_facts.fact_id (§N.5).

--------------------------------------------------------------------------------
LCA-6 fix (WP-2.2-CGM) — why the native produced ZERO motifs before this change
--------------------------------------------------------------------------------
Pre-WP-2.3 the CGM edge set was half-wired: bo_karanajala emitted NO dispositor
edges and bo_bimba left graha nodes with position_in_chart_jsonb=NULL. So all
three original detectors were structurally dead:
  • mutual_reception / parivartana_chain — needed dispositor edges (none existed)
  • stellium                             — needed graha house positions (all NULL)
Migration 376 then rationalised this as "0 rows is a valid completed state"
(target_floor=0). That excuse expired when WP-2.3 landed real dispositor edges,
graha↔bhava edges, yoga/dosha first-class nodes, yoga_member edges, AND graha
position hydration. This writer is now rewired to consume that real edge set,
and adds a yoga_cluster detector over yoga_member edges — a class that fires for
essentially any real chart carrying multi-constituent yogas. The aggregate motif
count for a real native is therefore > 0 from genuine structural patterns, not
from any lowered/meaningless threshold.

Motif classes (all structural, all edge-derived):
  1. yoga_cluster       — a yoga/dosha configuration node + its ≥2 constituent
                          graha/bhava members (yoga_member edges). PRIMARY guarantor.
  2. mutual_reception   — A disposits into B AND B disposits into A (dispositor
                          cycle length 2; simplest Parivartana).
  3. parivartana_chain  — dispositor cycle length 3–6 (longer lord-exchange cycles).
  4. stellium           — 3+ graha nodes sharing one bhava (occupancy/conjunction).
  5. mutual_aspect      — grahas that aspect each other (pairs) and mutual-aspect
                          triangles (3 grahas pairwise mutually aspecting).

LIGHT writer — one run() call, iterates 5 ayanamshas.
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_cgm_motifs_v2.0"
SNAPSHOT_TYPE  = "static_natal"

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

# Minimum grahas in a house to count as stellium
STELLIUM_THRESHOLD = 3
# Minimum constituents for a yoga configuration to count as a cluster motif
YOGA_CLUSTER_MIN_MEMBERS = 2

# Dispositor edge matchers (post-WP-2.3 bo_karanajala emits edge_type='dispositor')
_DISPOSITOR_BASES = ("dispositor", "lord_of_sign")
_DISPOSITOR_TYPES = ("disposited_by", "dispositor", "sign_lord")


def _is_dispositor_edge(e: dict) -> bool:
    return (
        str(e.get("relationship_basis", "")).lower() in _DISPOSITOR_BASES
        or str(e.get("edge_type", "")).lower() in _DISPOSITOR_TYPES
    )


_MOTIF_INSERT = """
INSERT INTO bodha_cgm_motifs (
  motif_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  motif_name, motif_class,
  involved_node_ids_array, involved_edge_ids_array,
  motif_strength, classical_citation_id,
  fingerprint_hash,
  verification_pass_status, citation_ref, citation_human,
  computed_at
) VALUES (
  %(motif_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(motif_name)s, %(motif_class)s,
  %(involved_node_ids_array)s, %(involved_edge_ids_array)s,
  %(motif_strength)s, %(classical_citation_id)s,
  %(fingerprint_hash)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s,
  %(computed_at)s
)
ON CONFLICT DO NOTHING
"""

_SUBGRAPH_INSERT = """
INSERT INTO bodha_cgm_sub_graphs (
  subgraph_id, chart_id, ayanamsha_id, build_id,
  subgraph_type, subgraph_label,
  node_ids_array, edge_ids_array,
  subgraph_density, subgraph_centroid_node_id,
  representative_path_jsonb, classical_archetype_match,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(subgraph_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(subgraph_type)s, %(subgraph_label)s,
  %(node_ids_array)s, %(edge_ids_array)s,
  %(subgraph_density)s, %(subgraph_centroid_node_id)s,
  %(representative_path_jsonb)s, %(classical_archetype_match)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
"""

_TOPOLOGY_INSERT = """
INSERT INTO bodha_cgm_chart_topology_summary (
  summary_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  total_nodes, total_edges,
  top_5_hub_nodes_jsonb, top_5_central_nodes_jsonb,
  triangle_count, strongly_connected_components_count,
  graph_diameter, graph_density, isolated_node_ids_array,
  dispositor_cycle_jsonb, hub_dominance_score, fragmentation_score,
  graph_fingerprint_hash,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(summary_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(total_nodes)s, %(total_edges)s,
  %(top_5_hub_nodes_jsonb)s, %(top_5_central_nodes_jsonb)s,
  %(triangle_count)s, %(strongly_connected_components_count)s,
  %(graph_diameter)s, %(graph_density)s, %(isolated_node_ids_array)s,
  %(dispositor_cycle_jsonb)s, %(hub_dominance_score)s, %(fragmentation_score)s,
  %(graph_fingerprint_hash)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
ON CONFLICT (chart_id, ayanamsha_id, build_id, snapshot_type) DO NOTHING
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


def _fingerprint(node_ids: list[str], motif_class: str) -> str:
    """Deterministic hash for a motif: sorted node_ids + motif_class."""
    payload = motif_class + ":" + ",".join(sorted(node_ids))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _label(node: dict, fallback: str = "?") -> str:
    return node.get("node_label_human") or str(node.get("node_subject", fallback))


# ── Motif detectors ──────────────────────────────────────────────────────────

def _detect_yoga_clusters(
    config_nodes: list[dict],
    edge_by_from: dict[str, list[dict]],
    node_by_id: dict[str, dict],
) -> list[dict]:
    """
    Detect yoga-cluster motifs: a yoga/dosha configuration node (node_type in
    ('yoga','dosha')) together with its ≥2 constituent members, wired by
    yoga_member edges (bo_karanajala, WP-2.3).

    Classical basis: a named yoga IS a structural cluster — the configuration and
    the grahas/bhavas that constitute it form a first-class sub-pattern of the
    chart (BPHS yoga chapters; Phaladeepika). This is the primary guarantor that a
    real chart yields motif_count > 0, since virtually every natal chart carries
    multi-constituent yogas.

    Lineage (§N.5): involved_edge_ids are the yoga_member edges, each of which
    carries constituent_fact_ids_array resolving to chart_facts.fact_id.
    """
    motifs: list[dict] = []
    for cfg_node in config_nodes:
        cfg_id = str(cfg_node["node_id"])
        member_edges = [
            e for e in edge_by_from.get(cfg_id, [])
            if str(e.get("edge_type", "")).lower() == "yoga_member"
        ]
        # Dedupe members (a config may edge to the same node twice across signals)
        members_seen: dict[str, str] = {}   # member_node_id → edge_id
        for e in member_edges:
            mid = str(e["to_node_id"])
            if mid in node_by_id and mid not in members_seen:
                members_seen[mid] = str(e["edge_id"])
        if len(members_seen) < YOGA_CLUSTER_MIN_MEMBERS:
            continue

        member_ids = list(members_seen.keys())
        edge_ids   = [members_seen[m] for m in member_ids]
        cfg_class  = str(cfg_node.get("node_type", "yoga")).lower()
        cfg_label  = _label(cfg_node, "yoga")
        member_labels = [_label(node_by_id[m]) for m in member_ids]

        # strength grows modestly with cluster size; capped
        strength = min(0.5 + 0.1 * (len(member_ids) - YOGA_CLUSTER_MIN_MEMBERS), 1.0)
        # config node's own strength (if present) informs but never fabricates
        node_strength = cfg_node.get("strength_score")
        if node_strength is not None:
            try:
                strength = max(strength, float(node_strength))
            except (TypeError, ValueError):
                pass

        motifs.append({
            "motif_class": "yoga_cluster",
            "motif_name": f"Yoga cluster: {cfg_label} [{', '.join(member_labels)}]",
            "node_ids": [cfg_id] + member_ids,
            "edge_ids": edge_ids,
            "strength": round(strength, 6),
            "classical_citation_id": f"yoga_cluster:{cfg_class}:configuration_membership:BPHS",
            "citation_human": (
                f"Yoga cluster: configuration '{cfg_label}' binds {len(member_ids)} "
                f"constituents ({', '.join(member_labels)}) into a single structural pattern"
            ),
        })
    return motifs


def _detect_mutual_reception(
    graha_nodes: list[dict],
    edge_by_from: dict[str, list[dict]],
) -> list[dict]:
    """
    Detect mutual reception: node A → dispositor edge → node B AND node B →
    dispositor edge → node A (dispositor cycle of length 2).

    Post-WP-2.3 bo_karanajala emits edge_type='dispositor' (graha → sign lord),
    so this detector fires whenever two grahas sit in each other's signs. If the
    chart happens to carry no such pair the detector correctly returns 0 (that is
    a real absence, not a wiring gap). A warning is logged only when the entire
    dispositor edge set is empty, which post-WP-2.3 would itself be a build fault.
    """
    motifs: list[dict] = []
    seen_pairs: set[frozenset] = set()

    disp_targets: dict[str, set[str]] = {}
    disp_edges: dict[tuple[str, str], str] = {}  # (from, to) → edge_id
    for node in graha_nodes:
        nid = str(node["node_id"])
        disp_targets[nid] = set()
        for e in edge_by_from.get(nid, []):
            if _is_dispositor_edge(e):
                tid = str(e["to_node_id"])
                disp_targets[nid].add(tid)
                disp_edges[(nid, tid)] = str(e["edge_id"])

    if sum(len(v) for v in disp_targets.values()) == 0:
        logger.warning(
            "[bo_cgm_motifs] mutual_reception: 0 dispositor edges in CGM edge set — "
            "post-WP-2.3 bo_karanajala should emit dispositor edges; verify the build"
        )

    graha_ids = [str(n["node_id"]) for n in graha_nodes]
    node_by_id = {str(n["node_id"]): n for n in graha_nodes}

    for i, a_id in enumerate(graha_ids):
        for b_id in graha_ids[i + 1:]:
            pair = frozenset({a_id, b_id})
            if pair in seen_pairs:
                continue
            if b_id in disp_targets.get(a_id, set()) and a_id in disp_targets.get(b_id, set()):
                seen_pairs.add(pair)
                edge_ids = [e for e in (disp_edges.get((a_id, b_id)), disp_edges.get((b_id, a_id))) if e]
                label_a = _label(node_by_id[a_id], a_id)
                label_b = _label(node_by_id[b_id], b_id)
                motifs.append({
                    "motif_class": "mutual_reception",
                    "motif_name": f"Mutual Reception: {label_a} ↔ {label_b}",
                    "node_ids": [a_id, b_id],
                    "edge_ids": edge_ids,
                    "strength": 0.8,
                    "classical_citation_id": "parivartana_yoga:HS:mutual_exchange",
                    "citation_human": (
                        "Mutual reception (Parivartana): two grahas ruling each other's "
                        "signs, exchanging strength and domain influence"
                    ),
                })
    return motifs


def _detect_stellia(
    graha_nodes: list[dict],
    edge_by_from: dict[str, list[dict]],
) -> list[dict]:
    """
    Detect stellia: 3+ graha nodes in the same house. House affiliation comes from
    position_in_chart_jsonb (populated by bo_bimba, WP-2.3). Lineage cites any
    conjunction/occupancy edges connecting the co-located grahas.
    """
    motifs: list[dict] = []
    by_house: dict[str, list[dict]] = {}
    for node in graha_nodes:
        pos = node.get("position_in_chart_jsonb")
        if pos is None:
            continue
        if isinstance(pos, str):
            try:
                pos = json.loads(pos)
            except (ValueError, TypeError):
                continue
        house = pos.get("house") or pos.get("house_number")
        if house is None:
            continue
        by_house.setdefault(str(house), []).append(node)

    for house_key, nodes in by_house.items():
        if len(nodes) < STELLIUM_THRESHOLD:
            continue
        node_ids = [str(n["node_id"]) for n in nodes]
        labels   = [_label(n) for n in nodes]
        node_id_set = set(node_ids)
        conj_edges: list[str] = []
        for node in nodes:
            nid = str(node["node_id"])
            for e in edge_by_from.get(nid, []):
                if str(e.get("edge_type", "")).lower() in ("conjunction", "conjunct") \
                   and str(e["to_node_id"]) in node_id_set:
                    conj_edges.append(str(e["edge_id"]))
        strength = min(0.5 + (len(nodes) - STELLIUM_THRESHOLD) * 0.1, 1.0)
        motifs.append({
            "motif_class": "stellium",
            "motif_name": f"Stellium in House {house_key}: {', '.join(labels)}",
            "node_ids": node_ids,
            "edge_ids": list(set(conj_edges)),
            "strength": strength,
            "classical_citation_id": "stellium:graha_yuddha_cluster:HS",
            "citation_human": (
                f"Stellium: {len(nodes)} grahas in house {house_key}, pooling their "
                f"energies in a single bhava"
            ),
        })
    return motifs


def _detect_parivartana_chains(
    graha_nodes: list[dict],
    edge_by_from: dict[str, list[dict]],
) -> list[dict]:
    """
    Detect Parivartana chains: dispositor cycles of length 3–6 (DFS over the
    dispositor adjacency). Length-2 cycles are handled by _detect_mutual_reception.

    Post-WP-2.3 the dispositor adjacency is populated from real 'dispositor' edges;
    a warning is logged only when it is entirely empty (a build fault post-WP-2.3).
    """
    motifs: list[dict] = []
    seen_cycles: set[frozenset] = set()

    disp_adj: dict[str, list[tuple[str, str]]] = {}  # node_id → [(to, edge_id)]
    for node in graha_nodes:
        nid = str(node["node_id"])
        disp_adj[nid] = [
            (str(e["to_node_id"]), str(e["edge_id"]))
            for e in edge_by_from.get(nid, [])
            if _is_dispositor_edge(e)
        ]

    if sum(len(v) for v in disp_adj.values()) == 0:
        logger.warning(
            "[bo_cgm_motifs] parivartana_chain: 0 dispositor edges in CGM edge set — "
            "post-WP-2.3 bo_karanajala should emit dispositor edges; verify the build"
        )

    node_by_id = {str(n["node_id"]): n for n in graha_nodes}
    graha_id_set = {str(n["node_id"]) for n in graha_nodes}

    def dfs(start: str, current: str, path: list[str], edges: list[str], depth: int) -> None:
        if depth > 6:
            return
        for next_id, edge_id in disp_adj.get(current, []):
            if next_id == start and depth >= 3:
                cycle_set = frozenset(path)
                if cycle_set not in seen_cycles:
                    seen_cycles.add(cycle_set)
                    labels = [_label(node_by_id[n], n) for n in path if n in node_by_id]
                    cycle_label = " → ".join(labels) + f" → {labels[0]} (cycle)"
                    strength = max(0.3, 0.7 - (depth - 3) * 0.1)
                    motifs.append({
                        "motif_class": "parivartana_chain",
                        "motif_name": f"Parivartana Chain (length {depth}): {cycle_label}",
                        "node_ids": list(path),
                        "edge_ids": list(edges) + [edge_id],
                        "strength": strength,
                        "classical_citation_id": f"parivartana_yoga:chain_{depth}:HS",
                        "citation_human": (
                            f"Parivartana chain of length {depth}: dispositor cycle linking "
                            f"{depth} grahas, each ruling the next's sign"
                        ),
                    })
            elif next_id not in path and next_id in graha_id_set and depth < 6:
                dfs(start, next_id, path + [next_id], edges + [edge_id], depth + 1)

    for node in graha_nodes:
        nid = str(node["node_id"])
        dfs(nid, nid, [nid], [], 1)
    return motifs


def _detect_mutual_aspects(
    graha_nodes: list[dict],
    edge_by_from: dict[str, list[dict]],
) -> list[dict]:
    """
    Detect mutual aspects: grahas that aspect each other (both A→B and B→A 'aspect'
    edges present) — emitted as mutual_aspect pairs — and mutual-aspect triangles
    (3 grahas pairwise in mutual aspect).

    Classical basis: paraspara drishti (mutual aspect) is a recognised strengthening
    relationship; three grahas in mutual aspect form a drishti trikona.
    Lineage cites the participating 'aspect' edges.
    """
    motifs: list[dict] = []
    graha_id_set = {str(n["node_id"]) for n in graha_nodes}
    node_by_id = {str(n["node_id"]): n for n in graha_nodes}

    # aspect adjacency: from → {to: edge_id}
    asp: dict[str, dict[str, str]] = {}
    for gid in graha_id_set:
        for e in edge_by_from.get(gid, []):
            if str(e.get("edge_type", "")).lower() == "aspect":
                tid = str(e["to_node_id"])
                if tid in graha_id_set:
                    asp.setdefault(gid, {})[tid] = str(e["edge_id"])

    # mutual pairs: A→B and B→A both present
    mutual_edge: dict[frozenset, list[str]] = {}
    for a, targets in asp.items():
        for b, eid_ab in targets.items():
            eid_ba = asp.get(b, {}).get(a)
            if eid_ba is not None:
                mutual_edge[frozenset({a, b})] = [eid_ab, eid_ba]

    # emit pairs
    for pair, edge_ids in mutual_edge.items():
        a, b = tuple(pair)
        motifs.append({
            "motif_class": "mutual_aspect",
            "motif_name": f"Mutual Aspect: {_label(node_by_id[a], a)} ↔ {_label(node_by_id[b], b)}",
            "node_ids": [a, b],
            "edge_ids": edge_ids,
            "strength": 0.6,
            "classical_citation_id": "paraspara_drishti:mutual_aspect:HS",
            "citation_human": (
                "Mutual aspect (paraspara drishti): two grahas casting drishti on one "
                "another, reinforcing their combined influence"
            ),
        })

    # triangles: three nodes pairwise in mutual aspect
    mutual_adj: dict[str, set[str]] = {}
    for pair in mutual_edge:
        a, b = tuple(pair)
        mutual_adj.setdefault(a, set()).add(b)
        mutual_adj.setdefault(b, set()).add(a)
    seen_tri: set[frozenset] = set()
    nodes = sorted(mutual_adj.keys())
    for a in nodes:
        for b in mutual_adj[a]:
            if b <= a:
                continue
            for c in mutual_adj[a] & mutual_adj[b]:
                if c <= b:
                    continue
                tri = frozenset({a, b, c})
                if tri in seen_tri:
                    continue
                seen_tri.add(tri)
                edge_ids = (
                    mutual_edge[frozenset({a, b})]
                    + mutual_edge[frozenset({a, c})]
                    + mutual_edge[frozenset({b, c})]
                )
                labels = [_label(node_by_id[n], n) for n in (a, b, c)]
                motifs.append({
                    "motif_class": "mutual_aspect_triangle",
                    "motif_name": f"Mutual-Aspect Triangle: {', '.join(labels)}",
                    "node_ids": [a, b, c],
                    "edge_ids": edge_ids,
                    "strength": 0.75,
                    "classical_citation_id": "paraspara_drishti:trikona:HS",
                    "citation_human": (
                        f"Mutual-aspect triangle: {', '.join(labels)} each cast drishti on the "
                        f"other two, forming a self-reinforcing drishti trikona"
                    ),
                })
    return motifs


# ── Sub-graph + topology derivation ──────────────────────────────────────────

def _undirected_adjacency(
    node_ids: list[str], edges: list[dict]
) -> tuple[dict[str, set[str]], dict[frozenset, list[str]]]:
    """Undirected projection: adjacency set + edge-id lists per unordered pair."""
    adj: dict[str, set[str]] = {n: set() for n in node_ids}
    pair_edges: dict[frozenset, list[str]] = {}
    node_set = set(node_ids)
    for e in edges:
        a = str(e["from_node_id"]); b = str(e["to_node_id"])
        if a == b or a not in node_set or b not in node_set:
            continue
        adj[a].add(b); adj[b].add(a)
        pair_edges.setdefault(frozenset({a, b}), []).append(str(e["edge_id"]))
    return adj, pair_edges


def _connected_components(node_ids: list[str], adj: dict[str, set[str]]) -> list[list[str]]:
    seen: set[str] = set()
    comps: list[list[str]] = []
    for start in node_ids:
        if start in seen:
            continue
        stack = [start]; comp: list[str] = []
        seen.add(start)
        while stack:
            n = stack.pop(); comp.append(n)
            for m in adj.get(n, ()):
                if m not in seen:
                    seen.add(m); stack.append(m)
        comps.append(comp)
    return comps


def _component_diameter(comp: list[str], adj: dict[str, set[str]]) -> int:
    """Longest shortest-path (BFS) within a single connected component."""
    if len(comp) <= 1:
        return 0
    comp_set = set(comp)
    diameter = 0
    for src in comp:
        dist = {src: 0}
        queue = [src]
        while queue:
            n = queue.pop(0)
            for m in adj.get(n, ()):
                if m in comp_set and m not in dist:
                    dist[m] = dist[n] + 1
                    queue.append(m)
        diameter = max(diameter, max(dist.values()))
    return diameter


def _triangle_count(node_ids: list[str], adj: dict[str, set[str]]) -> int:
    idx = {n: i for i, n in enumerate(node_ids)}
    count = 0
    for a in node_ids:
        for b in adj[a]:
            if idx[b] <= idx[a]:
                continue
            for c in adj[a] & adj[b]:
                if idx[c] > idx[b]:
                    count += 1
    return count


def _scc_count(node_ids: list[str], edges: list[dict]) -> int:
    """Tarjan strongly-connected-components count over the DIRECTED edge set."""
    node_set = set(node_ids)
    out_adj: dict[str, list[str]] = {n: [] for n in node_ids}
    for e in edges:
        a = str(e["from_node_id"]); b = str(e["to_node_id"])
        if a in node_set and b in node_set and a != b:
            out_adj[a].append(b)

    index_counter = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    index: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    scc_total = [0]

    def strongconnect(v: str) -> None:
        # iterative to avoid recursion limits on larger graphs
        work = [(v, iter(out_adj[v]))]
        index[v] = lowlink[v] = index_counter[0]; index_counter[0] += 1
        stack.append(v); on_stack.add(v)
        while work:
            node, it = work[-1]
            advanced = False
            for w in it:
                if w not in index:
                    index[w] = lowlink[w] = index_counter[0]; index_counter[0] += 1
                    stack.append(w); on_stack.add(w)
                    work.append((w, iter(out_adj[w])))
                    advanced = True
                    break
                elif w in on_stack:
                    lowlink[node] = min(lowlink[node], index[w])
            if advanced:
                continue
            work.pop()
            if lowlink[node] == index[node]:
                scc_total[0] += 1
                while True:
                    w = stack.pop(); on_stack.discard(w)
                    if w == node:
                        break
            if work:
                parent = work[-1][0]
                lowlink[parent] = min(lowlink[parent], lowlink[node])

    for n in node_ids:
        if n not in index:
            strongconnect(n)
    return scc_total[0]


def _compute_sub_graphs(
    chart_id: str, aya: str, build_id: str, now: str,
    all_nodes: list[dict], all_edges: list[dict],
) -> list[dict]:
    """Connected components (≥2 nodes) as sub-graph rows over the real edge set."""
    node_ids = [str(n["node_id"]) for n in all_nodes]
    node_by_id = {str(n["node_id"]): n for n in all_nodes}
    adj, pair_edges = _undirected_adjacency(node_ids, all_edges)
    comps = _connected_components(node_ids, adj)

    rows: list[dict] = []
    for comp in comps:
        if len(comp) < 2:
            continue
        comp_set = set(comp)
        edge_ids: list[str] = []
        for pair, eids in pair_edges.items():
            if pair <= comp_set:
                edge_ids.extend(eids)
        n = len(comp)
        max_edges = n * (n - 1) / 2
        density = round(len(set(edge_ids)) / max_edges, 6) if max_edges else 0.0
        # centroid = highest intra-component degree
        centroid = max(comp, key=lambda x: len(adj[x] & comp_set))
        labels = sorted(_label(node_by_id[c]) for c in comp)
        rows.append({
            "subgraph_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "subgraph_type": "connected_component",
            "subgraph_label": f"Component of {n} nodes centred on {_label(node_by_id[centroid])}",
            "node_ids_array": comp,
            "edge_ids_array": sorted(set(edge_ids)),
            "subgraph_density": density,
            "subgraph_centroid_node_id": centroid,
            "representative_path_jsonb": json.dumps({"members": labels}),
            "classical_archetype_match": None,
            # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
            # "pass" — an unconditional stamp with no verification logic behind it, and a
            # live false-green the serve layer counted as verified. Audited: nothing here
            # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "citation_ref": "bo_cgm_motifs:connected_component:v2",
            "citation_human": (
                f"Connected component: {n} CGM nodes joined through {len(set(edge_ids))} "
                f"edges into one structural neighbourhood"
            ),
            "computed_at": now,
        })
    return rows


def _compute_topology(
    chart_id: str, aya: str, build_id: str, now: str,
    all_nodes: list[dict], all_edges: list[dict], motifs: list[dict],
) -> dict:
    """Graph-level topology summary over the real node+edge set."""
    node_ids = [str(n["node_id"]) for n in all_nodes]
    node_by_id = {str(n["node_id"]): n for n in all_nodes}
    adj, _ = _undirected_adjacency(node_ids, all_edges)

    degree = {n: len(adj[n]) for n in node_ids}
    sum_degree = sum(degree.values()) or 1
    ranked = sorted(node_ids, key=lambda x: degree[x], reverse=True)
    top_hubs = [
        {"node_id": n, "label": _label(node_by_id[n]), "degree": degree[n]}
        for n in ranked[:5] if degree[n] > 0
    ]
    isolated = [n for n in node_ids if degree[n] == 0]

    comps = _connected_components(node_ids, adj)
    largest = max(comps, key=len) if comps else []
    diameter = _component_diameter(largest, adj) if largest else 0

    n_total = len(node_ids)
    max_edges = n_total * (n_total - 1) / 2
    # distinct undirected pairs actually connected
    connected_pairs = sum(len(adj[n]) for n in node_ids) / 2
    density = round(connected_pairs / max_edges, 6) if max_edges else 0.0

    hub_dominance = round((degree[ranked[0]] / sum_degree), 6) if ranked and degree[ranked[0]] else 0.0
    fragmentation = round(1 - (len(largest) / n_total), 6) if n_total else 0.0

    disp_cycles = [
        {"motif_class": m["motif_class"], "nodes": m["node_ids"]}
        for m in motifs
        if m["motif_class"] in ("mutual_reception", "parivartana_chain")
    ]

    fp_payload = f"{n_total}:{len(all_edges)}:{sorted(degree.values())}"
    fingerprint = hashlib.sha256(fp_payload.encode()).hexdigest()[:16]

    return {
        "summary_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "snapshot_type": SNAPSHOT_TYPE,
        "total_nodes": n_total,
        "total_edges": len(all_edges),
        "top_5_hub_nodes_jsonb": json.dumps(top_hubs),
        "top_5_central_nodes_jsonb": json.dumps(top_hubs),  # degree-centrality proxy (labelled)
        "triangle_count": _triangle_count(node_ids, adj),
        "strongly_connected_components_count": _scc_count(node_ids, all_edges),
        "graph_diameter": diameter,
        "graph_density": density,
        "isolated_node_ids_array": isolated,
        "dispositor_cycle_jsonb": json.dumps(disp_cycles),
        "hub_dominance_score": hub_dominance,
        "fragmentation_score": fragmentation,
        "graph_fingerprint_hash": fingerprint,
        # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
        # "pass" — an unconditional stamp with no verification logic behind it, and a
        # live false-green the serve layer counted as verified. Audited: nothing here
        # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
        "verification_pass_status": UNVERIFIED_DEFAULT,
        "citation_ref": "bo_cgm_motifs:chart_topology:v2",
        "citation_human": (
            f"CGM topology summary: {n_total} nodes / {len(all_edges)} edges, "
            f"{len(comps)} component(s), diameter {diameter}"
        ),
        "computed_at": now,
    }


def _write_aya(conn: Any, chart_id: str, aya: str, build_id: str, now: str) -> tuple[int, int, int]:
    """Detect + write motifs, sub_graphs, topology for one ayanamsha.
    Returns (motif_rows, subgraph_rows, topology_rows)."""

    all_nodes = _fetch_dict(
        conn,
        """SELECT node_id, node_type, node_subject, node_label_human,
                  position_in_chart_jsonb, strength_score
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )
    if not all_nodes:
        logger.info("[bo_cgm_motifs] %s — no CGM nodes; skipping", aya)
        return (0, 0, 0)

    all_edges = _fetch_dict(
        conn,
        """SELECT edge_id, from_node_id, to_node_id, edge_type, relationship_basis,
                  computed_strength
           FROM bodha_cgm_edges
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )

    graha_nodes  = [n for n in all_nodes if str(n.get("node_type")) == "graha"]
    config_nodes = [n for n in all_nodes if str(n.get("node_type")) in ("yoga", "dosha")]
    node_by_id   = {str(n["node_id"]): n for n in all_nodes}

    edge_by_from: dict[str, list[dict]] = {}
    for e in all_edges:
        edge_by_from.setdefault(str(e["from_node_id"]), []).append(e)

    all_motifs: list[dict] = []
    all_motifs.extend(_detect_yoga_clusters(config_nodes, edge_by_from, node_by_id))
    all_motifs.extend(_detect_mutual_reception(graha_nodes, edge_by_from))
    all_motifs.extend(_detect_stellia(graha_nodes, edge_by_from))
    all_motifs.extend(_detect_parivartana_chains(graha_nodes, edge_by_from))
    all_motifs.extend(_detect_mutual_aspects(graha_nodes, edge_by_from))

    motif_rows = 0
    with conn.cursor() as cur:
        for m in all_motifs:
            row = {
                "motif_id": str(uuid.uuid4()),
                "chart_id": chart_id,
                "ayanamsha_id": aya,
                "build_id": build_id,
                "snapshot_type": SNAPSHOT_TYPE,
                "motif_name": m["motif_name"],
                "motif_class": m["motif_class"],
                "involved_node_ids_array": m["node_ids"],
                "involved_edge_ids_array": m["edge_ids"] or [],
                "motif_strength": m["strength"],
                "classical_citation_id": m.get("classical_citation_id"),
                "fingerprint_hash": _fingerprint(m["node_ids"], m["motif_class"]),
                # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
                # "pass" — an unconditional stamp with no verification logic behind it, and a
                # live false-green the serve layer counted as verified. Audited: nothing here
                # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
                "verification_pass_status": UNVERIFIED_DEFAULT,
                "citation_ref": f"bo_cgm_motifs:{m['motif_class']}:v2",
                "citation_human": m.get("citation_human", f"CGM structural motif: {m['motif_class']}"),
                "computed_at": now,
            }
            cur.execute(_MOTIF_INSERT, row)
            motif_rows += 1

    # Sub-graphs (connected components)
    subgraph_rows = 0
    subgraphs = _compute_sub_graphs(chart_id, aya, build_id, now, all_nodes, all_edges)
    with conn.cursor() as cur:
        for sg in subgraphs:
            cur.execute(_SUBGRAPH_INSERT, sg)
            subgraph_rows += 1

    # Topology summary (one row per ayanamsha)
    topo = _compute_topology(chart_id, aya, build_id, now, all_nodes, all_edges, all_motifs)
    with conn.cursor() as cur:
        cur.execute(_TOPOLOGY_INSERT, topo)
    topology_rows = 1

    logger.info(
        "[bo_cgm_motifs] %s — %d motifs, %d sub_graphs, %d topology (nodes=%d edges=%d)",
        aya, motif_rows, subgraph_rows, topology_rows, len(all_nodes), len(all_edges),
    )
    return (motif_rows, subgraph_rows, topology_rows)


@register("bo_cgm_motifs")
class BoCgmMotifsWriter(WriterBase):
    """bo_cgm_motifs: CGM motif + sub-graph + topology layer over the CGM graph."""
    asset_id = "bo_cgm_motifs"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes=("dry_run — would derive motifs (yoga_cluster, mutual_reception, "
                       "stellium, parivartana_chain, mutual_aspect) + sub_graphs + topology"),
            )

        # Idempotency (§N.3): per-chart delete-then-insert for all three outputs
        # (all 5 ayanamshas are rewritten below, so a chart-wide delete is a valid
        # per-chart REPLACE). SET LOCAL statement_timeout=0 guards the heavy DELETE
        # on large charts and scopes to the orchestrator txn (writer never commits).
        # Ref: bo_laksana native-rebuild timeout; ka_* precedent (PR 422).
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")
            cur.execute("DELETE FROM bodha_cgm_motifs WHERE chart_id = %s", [chart_id])
            cur.execute("DELETE FROM bodha_cgm_sub_graphs WHERE chart_id = %s", [chart_id])
            cur.execute(
                "DELETE FROM bodha_cgm_chart_topology_summary WHERE chart_id = %s",
                [chart_id],
            )

        total_motifs = total_subgraphs = total_topology = 0
        for aya in CANONICAL_AYAS:
            m, s, t = _write_aya(conn, chart_id, aya, build_id, now)
            total_motifs += m
            total_subgraphs += s
            total_topology += t

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_motifs,
            notes=(f"motifs={total_motifs} sub_graphs={total_subgraphs} "
                   f"topology={total_topology} across {len(CANONICAL_AYAS)} ayanamshas"),
        )
