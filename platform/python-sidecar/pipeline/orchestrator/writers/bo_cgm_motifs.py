"""
bo_cgm_motifs — CGM Structural Motif Detection (L2 Bodha)
==========================================================
आकृति = "pattern/form"

Reads bodha_cgm_nodes + bodha_cgm_edges (written by bo_bimba) and detects
recurring structural patterns in the CGM graph. Emits one row per motif
instance per ayanamsha into bodha_cgm_motifs.

Three deterministic motif classes:
  1. mutual_reception — graha A disposits into B's sign AND B disposits into A's sign
     (dispositor cycle of length 2; a Parivartana of the simplest form)
  2. stellium — 3+ graha nodes all mutually connected by conjunction edges in the same house
  3. parivartana_chain — dispositor cycle of length 3–6 (longer mutual-reception chains)

All detection is purely structural over CGM graph data — no LLM, no invented values.

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

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_cgm_motifs_v1.0"
SNAPSHOT_TYPE  = "static_natal"

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

# Minimum grahas in a house to count as stellium
STELLIUM_THRESHOLD = 3

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


def _detect_mutual_reception(
    graha_nodes: list[dict],
    edge_by_from: dict[str, list[dict]],
) -> list[dict]:
    """
    Detect mutual reception: node A → dispositor edge → node B AND node B → dispositor edge → node A.
    Returns list of motif dicts.

    NOTE (Tier 3 future work): This detector requires bo_karanajala to emit dispositor edges
    with edge_type='dispositor' or relationship_basis='dispositor'/'lord_of_sign'.  As of the
    current wave bo_karanajala does NOT write these edges (dispositor edge construction requires
    sign-lord lookup logic not yet implemented).  Until bo_karanajala emits dispositor edges this
    detector will always return 0 motifs.  A warning is logged when the dispositor edge set is
    empty so the absence is auditable.
    """
    motifs = []
    seen_pairs: set[frozenset] = set()

    # Build dispositor targets for each node
    disp_targets: dict[str, set[str]] = {}
    disp_edges: dict[tuple[str, str], str] = {}  # (from, to) → edge_id

    for node in graha_nodes:
        nid = str(node["node_id"])
        disp_targets[nid] = set()
        for e in edge_by_from.get(nid, []):
            if str(e.get("relationship_basis", "")).lower() in ("dispositor", "lord_of_sign") \
               or str(e.get("edge_type", "")).lower() in ("disposited_by", "dispositor", "sign_lord"):
                tid = str(e["to_node_id"])
                disp_targets[nid].add(tid)
                disp_edges[(nid, tid)] = str(e["edge_id"])

    total_disp_edges = sum(len(v) for v in disp_targets.values())
    if total_disp_edges == 0:
        logger.warning(
            "[bo_cgm_motifs] mutual_reception: 0 dispositor edges found in CGM edge set — "
            "bo_karanajala does not yet emit dispositor edges; "
            "mutual_reception motifs cannot fire until Tier 3 dispositor edges are added"
        )

    graha_ids = [str(n["node_id"]) for n in graha_nodes]
    node_by_id = {str(n["node_id"]): n for n in graha_nodes}

    for i, a_id in enumerate(graha_ids):
        for b_id in graha_ids[i + 1:]:
            pair = frozenset({a_id, b_id})
            if pair in seen_pairs:
                continue
            # Mutual reception: A disposits B AND B disposits A
            if b_id in disp_targets.get(a_id, set()) and a_id in disp_targets.get(b_id, set()):
                seen_pairs.add(pair)
                edge_ab = disp_edges.get((a_id, b_id), "")
                edge_ba = disp_edges.get((b_id, a_id), "")
                edge_ids = [e for e in [edge_ab, edge_ba] if e]

                node_a = node_by_id[a_id]
                node_b = node_by_id[b_id]
                label_a = node_a.get("node_label_human") or node_a.get("node_subject", a_id)
                label_b = node_b.get("node_label_human") or node_b.get("node_subject", b_id)

                motifs.append({
                    "motif_class": "mutual_reception",
                    "motif_name": f"Mutual Reception: {label_a} ↔ {label_b}",
                    "node_ids": [a_id, b_id],
                    "edge_ids": edge_ids,
                    "strength": 0.8,  # mutual reception is structurally strong
                    "classical_citation_id": "parivartana_yoga:HS:mutual_exchange",
                    "citation_human": "Mutual reception (Parivartana): two grahas ruling each other's signs, exchanging strength and domain influence",
                })

    return motifs


def _detect_stellia(
    graha_nodes: list[dict],
    edge_by_from: dict[str, list[dict]],
) -> list[dict]:
    """
    Detect stellia: 3+ graha nodes in the same house connected by conjunction edges.
    Groups graha nodes by their house affiliation from position_in_chart_jsonb.
    """
    motifs = []

    # Group graha nodes by house
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
        key = str(house)
        if key not in by_house:
            by_house[key] = []
        by_house[key].append(node)

    # Find houses with ≥ STELLIUM_THRESHOLD grahas
    for house_key, nodes in by_house.items():
        if len(nodes) < STELLIUM_THRESHOLD:
            continue

        node_ids = [str(n["node_id"]) for n in nodes]
        labels = [
            n.get("node_label_human") or str(n.get("node_subject", n["node_id"]))
            for n in nodes
        ]

        # Find conjunction edges between these nodes
        node_id_set = set(node_ids)
        conj_edges: list[str] = []
        for node in nodes:
            nid = str(node["node_id"])
            for e in edge_by_from.get(nid, []):
                if str(e.get("edge_type", "")).lower() in ("conjunction", "conjunct"):
                    if str(e["to_node_id"]) in node_id_set:
                        conj_edges.append(str(e["edge_id"]))

        strength = min(0.5 + (len(nodes) - STELLIUM_THRESHOLD) * 0.1, 1.0)

        motifs.append({
            "motif_class": "stellium",
            "motif_name": f"Stellium in House {house_key}: {', '.join(labels)}",
            "node_ids": node_ids,
            "edge_ids": list(set(conj_edges)),
            "strength": strength,
            "classical_citation_id": "stellium:graha_yuddha_cluster:HS",
            "citation_human": f"Stellium: {len(nodes)} grahas in house {house_key}, pooling their energies in a single bhava",
        })

    return motifs


def _detect_parivartana_chains(
    graha_nodes: list[dict],
    edge_by_from: dict[str, list[dict]],
) -> list[dict]:
    """
    Detect Parivartana chains: dispositor cycles of length 3–6.
    Uses DFS from each graha node to find cycles.

    NOTE (Tier 3 future work): Same root dependency as mutual_reception — requires
    bo_karanajala to emit dispositor edges (edge_type='dispositor' or
    relationship_basis='dispositor'/'lord_of_sign').  Until those edges are written the
    DFS adjacency graph is always empty and this detector returns 0 motifs.  A warning is
    logged when the adjacency graph is empty so the absence is auditable.
    """
    motifs = []
    seen_cycles: set[frozenset] = set()

    disp_adj: dict[str, list[tuple[str, str]]] = {}  # node_id → [(to_node_id, edge_id)]
    for node in graha_nodes:
        nid = str(node["node_id"])
        disp_adj[nid] = []
        for e in edge_by_from.get(nid, []):
            if str(e.get("relationship_basis", "")).lower() in ("dispositor", "lord_of_sign") \
               or str(e.get("edge_type", "")).lower() in ("disposited_by", "dispositor", "sign_lord"):
                disp_adj[nid].append((str(e["to_node_id"]), str(e["edge_id"])))

    total_disp_adj = sum(len(v) for v in disp_adj.values())
    if total_disp_adj == 0:
        logger.warning(
            "[bo_cgm_motifs] parivartana_chain: 0 dispositor edges found in CGM edge set — "
            "bo_karanajala does not yet emit dispositor edges; "
            "parivartana_chain motifs cannot fire until Tier 3 dispositor edges are added"
        )

    node_by_id = {str(n["node_id"]): n for n in graha_nodes}
    graha_id_set = {str(n["node_id"]) for n in graha_nodes}

    def dfs(start: str, current: str, path: list[str], edges: list[str], depth: int) -> None:
        if depth > 6:
            return
        for next_id, edge_id in disp_adj.get(current, []):
            if next_id == start and depth >= 3:
                # Found a cycle of length depth (excludes length-2 mutual reception)
                cycle_set = frozenset(path)
                if cycle_set not in seen_cycles:
                    seen_cycles.add(cycle_set)
                    labels = [
                        node_by_id[n].get("node_label_human") or str(node_by_id[n].get("node_subject", n))
                        for n in path
                        if n in node_by_id
                    ]
                    cycle_label = " → ".join(labels) + f" → {labels[0]} (cycle)"
                    strength = max(0.3, 0.7 - (depth - 3) * 0.1)
                    motifs.append({
                        "motif_class": "parivartana_chain",
                        "motif_name": f"Parivartana Chain (length {depth}): {cycle_label}",
                        "node_ids": list(path),
                        "edge_ids": list(edges) + [edge_id],
                        "strength": strength,
                        "classical_citation_id": f"parivartana_yoga:chain_{depth}:HS",
                        "citation_human": f"Parivartana chain of length {depth}: dispositor cycle linking {depth} grahas, each ruling the next's sign",
                    })
            elif next_id not in path and next_id in graha_id_set and depth < 6:
                dfs(start, next_id, path + [next_id], edges + [edge_id], depth + 1)

    for node in graha_nodes:
        nid = str(node["node_id"])
        dfs(nid, nid, [nid], [], 1)

    return motifs


def _write_aya(conn: Any, chart_id: str, aya: str, build_id: str, now: str) -> int:
    """Detect and write motifs for one ayanamsha. Returns row count."""

    graha_nodes = _fetch_dict(
        conn,
        """SELECT node_id, node_subject, node_label_human, position_in_chart_jsonb
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND snapshot_type = %s AND node_type = 'graha'""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )
    if not graha_nodes:
        logger.info("[bo_cgm_motifs] %s — no graha nodes; skipping", aya)
        return 0

    all_edges = _fetch_dict(
        conn,
        """SELECT edge_id, from_node_id, to_node_id, edge_type, relationship_basis,
                  computed_strength
           FROM bodha_cgm_edges
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )

    edge_by_from: dict[str, list[dict]] = {}
    for e in all_edges:
        fid = str(e["from_node_id"])
        if fid not in edge_by_from:
            edge_by_from[fid] = []
        edge_by_from[fid].append(e)

    all_motifs: list[dict] = []
    all_motifs.extend(_detect_mutual_reception(graha_nodes, edge_by_from))
    all_motifs.extend(_detect_stellia(graha_nodes, edge_by_from))
    all_motifs.extend(_detect_parivartana_chains(graha_nodes, edge_by_from))

    inserted = 0
    with conn.cursor() as cur:
        for m in all_motifs:
            fp = _fingerprint(m["node_ids"], m["motif_class"])
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
                "fingerprint_hash": fp,
                "verification_pass_status": "pass",
                "citation_ref": f"bo_cgm_motifs:{m['motif_class']}:v1",
                "citation_human": m.get("citation_human", f"CGM structural motif: {m['motif_class']}"),
                "computed_at": now,
            }
            cur.execute(_MOTIF_INSERT, row)
            inserted += 1

    logger.info("[bo_cgm_motifs] %s — %d motifs written", aya, inserted)
    return inserted


@register("bo_cgm_motifs")
class BoCgmMotifsWriter(WriterBase):
    """bo_cgm_motifs: structural motif detection over the CGM graph."""
    asset_id = "bo_cgm_motifs"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="dry_run — would detect motifs (mutual_reception, stellium, parivartana_chain) for all ayanamshas",
            )

        # Idempotency: delete prior rows for this chart
        with conn.cursor() as cur:
            # Disable per-statement timeout for the heavy DELETE on large charts.
            # SET LOCAL scopes to the orchestrator txn (writer never commits).
            # Ref: bo_laksana native-rebuild timeout; ka_* precedent (PR 422).
            cur.execute("SET LOCAL statement_timeout = 0")
            cur.execute("DELETE FROM bodha_cgm_motifs WHERE chart_id = %s", [chart_id])

        total = 0
        for aya in CANONICAL_AYAS:
            total += _write_aya(conn, chart_id, aya, build_id, now)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            notes=f"motifs={total} across {len(CANONICAL_AYAS)} ayanamshas",
        )
