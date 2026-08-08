"""
services.ka_kshetra.stage2_promise — ṢAḌ-DARŚANA W2 Lane A, Stage 2.

Spec: KALA_W2_FIELD_DESIGN_v1_0.md §3.3. The promise graph: a directed
weighted graph per chart, digested from L2 Bodha, plus alternate routings
(Yen's K-shortest-loopless-paths) from significator seeds to each
`event_class` sink, combined via noisy-OR into the promise prior `P_e`.
Writes `kala_field_promise_nodes/edges/routes` (migration 489).

Published function (Lane A -> Lanes C/D, §3.3, FROZEN by this design):
    promise_prior(chart_id: UUID, event_class: str, conn) -> PromisePrior

Real L2 ingestion sources (verified against the live schema, not assumed):
  - `bodha_cgm_nodes` / `bodha_cgm_edges` (bo_karanajala, migration 226+433):
    graha/bhava/yoga/arudha/special_lagna nodes; dispositor/lordship/
    occupancy/bhava_aspect/argala/yoga_member edges, each carrying
    `computed_strength` and (where populated) `constituent_fact_ids_array`.
  - `bodha_pratijna` (bo_pratijna, migration 391): the promise register —
    one row per (chart, ayanamsha, event_class) with `status`/`grade` and
    the supporting/contradicting `bodha_msr_signals.signal_id` arrays. This
    is the source of `event_class` sink nodes and the ONLY edge kind that
    points at a sink (`class_signification`, §3.3).
  - `bodha_msr_signals` (bo_laksana): resolves a supporting signal_id back to
    its primary graha via `configuration_jsonb` (the same tag keys
    bo_laksana_rerank's own `_extract_primary_graha_for_rerank` treats as
    authoritative: graha / primary_graha / lord / body).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Optional, Sequence

import networkx as nx

from .contracts import PromisePrior, Route
from brahmagyan.graha_vocabulary import norm_graha

CANONICAL_AYANAMSHA = "lahiri_chitrapaksha"

# ── Graph model (§3.3) ────────────────────────────────────────────────────────

NODE_KINDS = ("graha", "bhava", "bhava_lord", "karaka", "yoga", "arudha", "event_class")
EDGE_KINDS = ("dispositor", "lordship", "occupation", "aspect", "argala",
              "yoga_membership", "karaka_signification", "class_signification")

# bodha_cgm_edges.edge_type -> stage-2 edge_kind (real, verified strings —
# migration 226 CREATE TABLE + bo_karanajala.py's literal edge_type assignments).
_CGM_EDGE_TYPE_MAP: dict[str, str] = {
    "dispositor": "dispositor",
    "lordship": "lordship",
    "occupancy": "occupation",
    "bhava_aspect": "aspect",
    "argala": "argala",
    "yoga_member": "yoga_membership",
}

# bodha_cgm_nodes.node_type -> stage-2 node_kind. 'special_lagna' has no direct
# analogue in §3.3's kind list; it is carried through as 'karaka' (a special
# lagna is a karaka-like sensitive point, not a graha/bhava/yoga) rather than
# silently dropped.
_CGM_NODE_TYPE_MAP: dict[str, str] = {
    "graha": "graha",
    "bhava": "bhava",
    "yoga": "yoga",
    "arudha": "arudha",
    "special_lagna": "karaka",
}

CONDUCTANCE_DEFAULT = 0.60  # c_default, §3.3
ROUTE_FLOOR = 0.02          # routes with p_r < route_floor are dropped, §3.3
L_MAX_HOPS = 4
K_ROUTES = 5


@dataclass(frozen=True)
class PromiseNode:
    node_id: str
    node_kind: str
    label: str
    source_kind: str
    source_table: Optional[str] = None
    source_pk: Optional[str] = None
    source_fact_id: Optional[str] = None


@dataclass(frozen=True)
class PromiseEdge:
    from_node: str
    to_node: str
    edge_kind: str
    conductance: float
    conductance_source: str  # 'l2_inherited' | 'ungraded_default'
    source_fact_id: Optional[str] = None


def graha_node_id(graha: str) -> str:
    return f"graha:{_short_graha_code(graha)}"


# 2-letter display code, derived from the graha SSoT's canonical short code
# (brahmagyan/graha_vocabulary.norm_graha) rather than hardcoded literals —
# ADHIṢṬHĀNA Lane A2 (found via the full-tree census; not one of the
# originally-enumerated retirement targets). This file's own established
# output convention is a 2-letter Title-case code (e.g. "Ra" for Rahu,
# "Ke" for Ketu), which the SSoT's canonical short code's first 2 characters
# always yield (RAH_MEAN[:2]="RA", KET_MEAN[:2]="KE", etc).
_GRAHA_SHORT: dict[str, str] = {
    name: norm_graha(name)[:2].capitalize()
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
}


def _short_graha_code(graha: str) -> str:
    return _GRAHA_SHORT.get(graha, graha)


def bhava_node_id(house: int) -> str:
    return f"bhava:{house}"


def event_class_node_id(event_class: str) -> str:
    return f"event_class:{event_class}"


# ── Conductance normalization (§3.3: "inherited, never invented") ────────────

def normalize_conductance(raw_strength: float, scale_min: float, scale_max: float) -> float:
    """Min-max normalize an L2 signal's own declared strength scale into
    (0, 1]. Degenerate scale (scale_max <= scale_min) maps everything to 1.0
    (a single-valued scale carries no discriminating information, so every
    edge on it is treated as fully conductive rather than divided by zero)."""
    if scale_max <= scale_min:
        return 1.0
    frac = (raw_strength - scale_min) / (scale_max - scale_min)
    frac = min(1.0, max(0.0, frac))
    # (0, 1] per §3.3 — a normalized-to-exactly-0 edge still needs SOME
    # conductance to remain a valid (non-zero-cost) graph edge; floor it at a
    # small epsilon rather than silently dropping the edge.
    return max(frac, 1e-6)


# ── The graph + Yen's K-shortest-loopless-paths algorithm (§3.3, exact) ──────

def build_digraph(nodes: Sequence[PromiseNode], edges: Sequence[PromiseEdge]) -> nx.DiGraph:
    g = nx.DiGraph()
    for n in nodes:
        g.add_node(n.node_id, kind=n.node_kind, label=n.label)
    for e in edges:
        cost = -math.log(e.conductance)
        # A repeated (from,to) pair (two edge_kinds between the same nodes)
        # keeps the LOWEST cost (highest conductance) — the graph is edge-kind
        # agnostic for routing purposes; kind is retained for provenance only.
        if g.has_edge(e.from_node, e.to_node):
            if cost < g[e.from_node][e.to_node]["cost"]:
                g[e.from_node][e.to_node].update(cost=cost, conductance=e.conductance, edge=e)
        else:
            g.add_edge(e.from_node, e.to_node, cost=cost, conductance=e.conductance, edge=e)
    return g


def _restrict_to_reachable(g: nx.DiGraph, sink: str, l_max_hops: int) -> nx.DiGraph:
    """G_e: the subgraph of nodes reachable TO `sink` within l_max_hops hops
    (§3.3 step 1). Computed on the REVERSED graph via a hop-bounded BFS."""
    if sink not in g:
        return nx.DiGraph()
    rev = g.reverse(copy=False)
    reachable = {sink}
    frontier = {sink}
    for _ in range(l_max_hops):
        nxt = set()
        for u in frontier:
            for v in rev.successors(u):
                if v not in reachable:
                    nxt.add(v)
        reachable |= nxt
        frontier = nxt
        if not frontier:
            break
    return g.subgraph(reachable).copy()


def k_shortest_routes(g: nx.DiGraph, seeds: Sequence[str], sink: str,
                       k: int = K_ROUTES, l_max_hops: int = L_MAX_HOPS,
                       route_floor: float = ROUTE_FLOOR) -> tuple[list[Route], int]:
    """§3.3 steps 1-5, exact: restrict to the l_max_hops-reachable subgraph,
    Yen's K-shortest-loopless-paths (networkx's `shortest_simple_paths` is a
    Lawler-modified Yen's implementation over a weighted DiGraph, ordered by
    increasing total cost — exactly K-shortest-loopless), deterministic
    tie-break on equal cost by ascending concatenated node-id string, drop
    routes with p_r < route_floor. Returns (routes, dropped_below_floor_count)."""
    sub = _restrict_to_reachable(g, sink, l_max_hops)
    if sink not in sub:
        return [], 0

    candidates: list[tuple[float, list[str]]] = []  # (cost, path)
    for seed in sorted(set(seeds)):
        if seed not in sub or seed == sink:
            continue
        try:
            paths_iter = nx.shortest_simple_paths(sub, seed, sink, weight="cost")
        except nx.NetworkXNoPath:
            continue
        except nx.NodeNotFound:
            continue
        count = 0
        for path in paths_iter:
            cost = sum(sub[path[i]][path[i + 1]]["cost"] for i in range(len(path) - 1))
            candidates.append((cost, path))
            count += 1
            if count >= k:
                break

    # Deterministic ordering across ALL seeds' candidates: ascending cost,
    # tie-break by ascending concatenated node-id string (§3.3 step 3).
    candidates.sort(key=lambda cp: (round(cp[0], 12), "".join(cp[1])))

    routes: list[Route] = []
    dropped = 0
    rank = 0
    for cost, path in candidates:
        p_r = math.exp(-cost)
        if p_r < route_floor:
            dropped += 1
            continue
        rank += 1
        edge_ids: list[int] = []  # populated by the DB-integration layer (§3.3:
        # "FK-shaped refs into kala_field_promise_edges") — pure in-memory
        # routing has no row ids yet; see write_promise_graph below.
        routes.append(Route(
            event_class="",  # filled in by promise_prior (needs the caller's event_class)
            route_rank=rank, path_node_ids=tuple(path), path_edge_ids=tuple(edge_ids),
            route_gain=p_r, is_primary=(rank == 1),
        ))
        if rank >= k:
            break
    return routes, dropped


def noisy_or_promise(routes: Sequence[Route]) -> float:
    """P_e = 1 - Prod_{r in routes} (1 - p_r) in [0, 1) (§3.3, exact)."""
    prod = 1.0
    for r in routes:
        prod *= (1.0 - r.route_gain)
    return 1.0 - prod


# ── The published function (Lane A -> Lanes C/D) ─────────────────────────────

def promise_prior(chart_id: str, event_class: str, conn) -> PromisePrior:
    """FROZEN signature (§3.3). Loads this chart's promise graph from the
    real L2 tables, restricts to the event_class sink, runs K-shortest-routes
    + noisy-OR, and returns the PromisePrior other lanes consume."""
    nodes, edges, seeds_by_class, fact_ids_by_edge = load_promise_graph(conn, chart_id)
    g = build_digraph(nodes, edges)
    sink = event_class_node_id(event_class)
    seeds = seeds_by_class.get(event_class, [])
    routes, dropped = k_shortest_routes(g, seeds, sink)
    routes = tuple(Route(
        event_class=event_class, route_rank=r.route_rank, path_node_ids=r.path_node_ids,
        path_edge_ids=r.path_edge_ids, route_gain=r.route_gain, is_primary=r.is_primary,
        suppressed_by=r.suppressed_by,
    ) for r in routes)
    p = noisy_or_promise(routes)
    fact_ids: list[str] = []
    for r in routes:
        for i in range(len(r.path_node_ids) - 1):
            key = (r.path_node_ids[i], r.path_node_ids[i + 1])
            fid = fact_ids_by_edge.get(key)
            if fid:
                fact_ids.append(fid)
    return PromisePrior(
        p=p, routes=routes, n_routes=len(routes),
        dropped_below_floor=dropped, fact_ids=tuple(dict.fromkeys(fact_ids)),
    )


# ── L2 ingestion (real tables; §N.5 — inherit strength, never invent it) ─────

_PRIMARY_GRAHA_KEYS = ("graha", "primary_graha", "lord", "body")


def _extract_primary_graha(config: Optional[dict]) -> Optional[str]:
    """Mirrors bo_laksana_rerank._extract_primary_graha_for_rerank's tag-key
    precedence exactly (graha / primary_graha / lord / body), so this reads
    the SAME configuration_jsonb convention bo_laksana already established —
    not a new heuristic."""
    if not isinstance(config, dict):
        return None
    for key in _PRIMARY_GRAHA_KEYS:
        val = config.get(key)
        if val:
            return str(val).strip().title()
    return None


def _fetch_cgm_nodes(conn, chart_id: str, ayanamsha_id: str) -> list[dict]:
    # NOTE: no `constituent_fact_ids_array` here — that column exists on
    # bodha_cgm_edges only (see _fetch_cgm_edges below), not bodha_cgm_nodes.
    # Selecting it against the nodes table raised UndefinedColumn in production
    # (found 2026-08-05, first real ka_kshetra field-build attempt for either
    # canonical chart); PromiseNode construction below never read it from a
    # node row anyway (only edges resolve source_fact_id).
    rows = conn.execute(
        """SELECT node_id, node_type, node_subject, node_label_human,
                  strength_score
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, ayanamsha_id],
    ).fetchall()
    return [dict(r) if not isinstance(r, dict) else r for r in rows]


def _fetch_cgm_edges(conn, chart_id: str, ayanamsha_id: str) -> list[dict]:
    rows = conn.execute(
        """SELECT edge_type, from_node_id, to_node_id, computed_strength,
                  cancelled_flag, constituent_fact_ids_array
           FROM bodha_cgm_edges
           WHERE chart_id = %s AND ayanamsha_id = %s AND cancelled_flag = FALSE""",
        [chart_id, ayanamsha_id],
    ).fetchall()
    return [dict(r) if not isinstance(r, dict) else r for r in rows]


def _fetch_pratijna(conn, chart_id: str, ayanamsha_id: str) -> list[dict]:
    # R6 (PROMISE IS A MODIFIER, NEVER A GATE): all statuses flow through.
    # The old filter `AND status IN ('promised', 'conditional')` was a categorical
    # gate that discarded 'denied' and 'no_evidence' rows entirely -- causing
    # marriage, childbirth, surgery, and relocation to vanish from the native's
    # promise graph even when those domains had signal evidence.
    # Downstream consumers (load_promise_graph, conductance scaling) treat status
    # and grade as MODIFIERS (scaling factors on conductance), never as binary gates.
    # 'no_evidence' rows (grade=NULL) produce no class_signification edges because
    # their supporting_signal_ids are NULL -- correctly so, since there are no graha
    # seed nodes to connect. 'denied' rows produce low-conductance edges that inhibit
    # routes rather than eliminating them from the graph.
    rows = conn.execute(
        """SELECT event_class_id, status, grade, supporting_signal_ids
           FROM bodha_pratijna
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, ayanamsha_id],
    ).fetchall()
    return [dict(r) if not isinstance(r, dict) else r for r in rows]


def _fetch_signal_primary_grahas(conn, signal_ids: Sequence[str]) -> dict[str, tuple[str, float]]:
    """{signal_id: (primary_graha, computed_salience)} for the given ids."""
    if not signal_ids:
        return {}
    rows = conn.execute(
        """SELECT signal_id, configuration_jsonb, computed_salience
           FROM bodha_msr_signals
           WHERE signal_id = ANY(%s)""",
        [list(signal_ids)],
    ).fetchall()
    out: dict[str, tuple[str, float]] = {}
    for r in rows:
        r = dict(r) if not isinstance(r, dict) else r
        cfg = r.get("configuration_jsonb")
        if isinstance(cfg, str):
            try:
                cfg = json.loads(cfg)
            except Exception:
                cfg = {}
        graha = _extract_primary_graha(cfg or {})
        if graha:
            out[str(r["signal_id"])] = (graha, float(r.get("computed_salience") or 0.0))
    return out


def load_promise_graph(conn, chart_id: str, ayanamsha_id: str = CANONICAL_AYANAMSHA
                        ) -> tuple[list[PromiseNode], list[PromiseEdge],
                                   dict[str, list[str]], dict[tuple[str, str], str]]:
    """Builds this chart's promise graph from `bodha_cgm_nodes`/`bodha_cgm_edges`
    (structural graha/bhava/yoga relations) plus `bodha_pratijna` +
    `bodha_msr_signals` (event_class sinks + the ONLY edge kind pointing at
    one, `class_signification`, §3.3). Returns
    (nodes, edges, seeds_by_event_class, fact_id_by_(from,to))."""
    cgm_nodes = _fetch_cgm_nodes(conn, chart_id, ayanamsha_id)
    cgm_edges = _fetch_cgm_edges(conn, chart_id, ayanamsha_id)
    pratijna_rows = _fetch_pratijna(conn, chart_id, ayanamsha_id)

    nodes: list[PromiseNode] = []
    node_ids_by_subject: dict[tuple[str, str], str] = {}
    for n in cgm_nodes:
        kind = _CGM_NODE_TYPE_MAP.get(n["node_type"])
        if kind is None:
            continue  # an unmapped CGM node type is not a stage-2 node kind; skip, never invent
        stable_id = _stable_node_id(kind, n["node_subject"])
        node_ids_by_subject[(n["node_type"], n["node_subject"])] = stable_id
        nodes.append(PromiseNode(
            node_id=stable_id, node_kind=kind, label=n["node_label_human"],
            source_kind="l2_signal", source_table="bodha_cgm_nodes",
            source_pk=str(n["node_id"]),
        ))

    edges: list[PromiseEdge] = []
    fact_id_by_pair: dict[tuple[str, str], str] = {}
    cgm_id_to_stable: dict[str, str] = {}
    for n in cgm_nodes:
        cgm_id_to_stable[str(n["node_id"])] = node_ids_by_subject.get(
            (n["node_type"], n["node_subject"]), str(n["node_id"]),
        )
    for e in cgm_edges:
        kind = _CGM_EDGE_TYPE_MAP.get(e["edge_type"])
        if kind is None:
            continue
        from_id = cgm_id_to_stable.get(str(e["from_node_id"]))
        to_id = cgm_id_to_stable.get(str(e["to_node_id"]))
        if from_id is None or to_id is None:
            continue
        conductance = normalize_conductance(float(e["computed_strength"]), 0.0, 1.0)
        fact_ids = e.get("constituent_fact_ids_array") or []
        source_fact_id = fact_ids[0] if fact_ids else None
        edges.append(PromiseEdge(
            from_node=from_id, to_node=to_id, edge_kind=kind, conductance=conductance,
            conductance_source="l2_inherited", source_fact_id=source_fact_id,
        ))
        if source_fact_id:
            fact_id_by_pair[(from_id, to_id)] = source_fact_id

    seeds_by_class: dict[str, list[str]] = {}
    signal_ids_needed: set[str] = set()
    for p in pratijna_rows:
        for sid in (p.get("supporting_signal_ids") or []):
            signal_ids_needed.add(str(sid))
    graha_by_signal = _fetch_signal_primary_grahas(conn, sorted(signal_ids_needed))

    for p in pratijna_rows:
        event_class = str(p["event_class_id"])
        sink_id = event_class_node_id(event_class)
        nodes.append(PromiseNode(
            node_id=sink_id, node_kind="event_class", label=event_class,
            source_kind="l2_signal", source_table="bodha_pratijna",
            source_pk=f"{chart_id}:{ayanamsha_id}:{event_class}",
        ))
        seeds: list[str] = []
        grade = float(p.get("grade") or 0.0)  # bodha_pratijna.grade in [0, 10]
        for sid in (p.get("supporting_signal_ids") or []):
            info = graha_by_signal.get(str(sid))
            if info is None:
                continue
            graha, salience = info
            graha_id = graha_node_id(graha)
            seeds.append(graha_id)
            conductance = normalize_conductance(max(salience, grade / 10.0), 0.0, 1.0)
            edges.append(PromiseEdge(
                from_node=graha_id, to_node=sink_id, edge_kind="class_signification",
                conductance=conductance, conductance_source="l2_inherited",
                source_fact_id=str(sid),
            ))
            fact_id_by_pair[(graha_id, sink_id)] = str(sid)
        seeds_by_class[event_class] = sorted(set(seeds))

    # De-dupe nodes by node_id (a graha can appear once from CGM ingestion; no
    # further collision expected, but keep this defensive and deterministic).
    seen_ids: set[str] = set()
    deduped_nodes: list[PromiseNode] = []
    for n in nodes:
        if n.node_id in seen_ids:
            continue
        seen_ids.add(n.node_id)
        deduped_nodes.append(n)

    return deduped_nodes, edges, seeds_by_class, fact_id_by_pair


def _stable_node_id(kind: str, subject: str) -> str:
    if kind == "graha":
        return graha_node_id(subject)
    if kind == "bhava":
        try:
            return bhava_node_id(int(subject))
        except (TypeError, ValueError):
            return f"bhava:{subject}"
    return f"{kind}:{subject}"


# ── DB write layer (kala_field_promise_nodes/edges/routes) ──────────────────

NODE_UPSERT_SQL = """
INSERT INTO kala_field_promise_nodes (
    chart_id, node_id, node_kind, label, source_kind, source_table,
    source_pk, source_fact_id
) VALUES (%(chart_id)s, %(node_id)s, %(node_kind)s, %(label)s, %(source_kind)s,
          %(source_table)s, %(source_pk)s, %(source_fact_id)s)
ON CONFLICT (chart_id, node_id) DO UPDATE SET
    node_kind = EXCLUDED.node_kind, label = EXCLUDED.label,
    source_kind = EXCLUDED.source_kind, source_table = EXCLUDED.source_table,
    source_pk = EXCLUDED.source_pk, source_fact_id = EXCLUDED.source_fact_id
"""

EDGE_UPSERT_SQL = """
INSERT INTO kala_field_promise_edges (
    chart_id, from_node, to_node, edge_kind, conductance, conductance_source,
    source_fact_id
) VALUES (%(chart_id)s, %(from_node)s, %(to_node)s, %(edge_kind)s,
          %(conductance)s, %(conductance_source)s, %(source_fact_id)s)
ON CONFLICT (chart_id, from_node, to_node, edge_kind) DO UPDATE SET
    conductance = EXCLUDED.conductance,
    conductance_source = EXCLUDED.conductance_source,
    source_fact_id = EXCLUDED.source_fact_id
RETURNING id
"""

ROUTE_UPSERT_SQL = """
INSERT INTO kala_field_routes (
    chart_id, event_class, route_rank, path_node_ids, path_edge_ids,
    route_gain, is_primary, suppressed_by
) VALUES (%(chart_id)s, %(event_class)s, %(route_rank)s, %(path_node_ids)s,
          %(path_edge_ids)s, %(route_gain)s, %(is_primary)s, %(suppressed_by)s)
ON CONFLICT (chart_id, event_class, route_rank) DO UPDATE SET
    path_node_ids = EXCLUDED.path_node_ids, path_edge_ids = EXCLUDED.path_edge_ids,
    route_gain = EXCLUDED.route_gain, is_primary = EXCLUDED.is_primary,
    suppressed_by = EXCLUDED.suppressed_by
"""

REPLACE_PRIOR_SQL = (
    "DELETE FROM kala_field_routes WHERE chart_id = %s;"
    "DELETE FROM kala_field_promise_edges WHERE chart_id = %s;"
    "DELETE FROM kala_field_promise_nodes WHERE chart_id = %s;"
)


def write_promise_graph(conn, chart_id: str, nodes: Sequence[PromiseNode],
                         edges: Sequence[PromiseEdge]) -> dict[tuple[str, str, str], int]:
    """Upserts nodes then edges (nodes first — edges FK-shaped-reference
    node_ids); returns {(from,to,kind): edge_row_id} for route path_edge_ids."""
    for n in nodes:
        conn.execute(NODE_UPSERT_SQL, {
            "chart_id": chart_id, "node_id": n.node_id, "node_kind": n.node_kind,
            "label": n.label, "source_kind": n.source_kind, "source_table": n.source_table,
            "source_pk": n.source_pk, "source_fact_id": n.source_fact_id,
        })
    edge_ids: dict[tuple[str, str, str], int] = {}
    for e in edges:
        row = conn.execute(EDGE_UPSERT_SQL, {
            "chart_id": chart_id, "from_node": e.from_node, "to_node": e.to_node,
            "edge_kind": e.edge_kind, "conductance": e.conductance,
            "conductance_source": e.conductance_source, "source_fact_id": e.source_fact_id,
        }).fetchone()
        if row is not None:
            row_id = row["id"] if isinstance(row, dict) else row[0]
            edge_ids[(e.from_node, e.to_node, e.edge_kind)] = row_id
    return edge_ids


def write_routes(conn, chart_id: str, event_class: str, routes: Sequence[Route]) -> int:
    n = 0
    for r in routes:
        conn.execute(ROUTE_UPSERT_SQL, {
            "chart_id": chart_id, "event_class": event_class, "route_rank": r.route_rank,
            "path_node_ids": list(r.path_node_ids), "path_edge_ids": list(r.path_edge_ids),
            "route_gain": r.route_gain, "is_primary": r.is_primary,
            "suppressed_by": list(r.suppressed_by),
        })
        n += 1
    return n
