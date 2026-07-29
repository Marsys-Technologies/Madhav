"""
bo_cgm_paths — CGM Dispositor Chain Path Analysis (L2 Bodha)
=============================================================
दिशा = "direction/path"

Reads bodha_cgm_nodes + bodha_cgm_edges (written by bo_bimba) and computes
dispositor chain paths for each graha node per ayanamsha.

CONTRACT-3 (A7 → A5): ph_nimitta._load_cgm_meta() reads bodha_cgm_paths with
columns: path_id, path_label_human, path_length, is_final_dispositor.
These MUST be populated here.

Algorithm:
  For each graha-type node per ayanamsha:
    1. Find the DISPOSITOR edge (relationship_basis='dispositor') leaving this node.
    2. Follow the chain: current_graha → dispositor → dispositor's dispositor...
    3. Stop when: (a) self-ruling graha reached (is_final_dispositor=True),
       (b) cycle back to start (loop detected), or (c) depth > 9 (safety cap).
    4. Emit one bodha_cgm_paths row per unique (from_graha, final_node) chain.

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
from ga_writers.verification_vocab import UNVERIFIED_DEFAULT

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_cgm_paths_v1.1"
SNAPSHOT_TYPE  = "static_natal"
PATH_TYPE      = "dispositor_chain"
MAX_CHAIN_DEPTH = 9
# JL-013 (BA Phase 2.5 J4): path_strength = PRODUCT of constituent edges'
# computed_strength — never an average (a chain is only as strong as its
# weakest-compounding link; averaging would let one broken edge hide behind
# strong ones). This placeholder now only applies when NO edge in the chain
# has a computed_strength at all (honest fallback, not a fabricated value).
PATH_STRENGTH_PLACEHOLDER = 0.5   # fallback only when zero edges carry computed_strength


def _path_strength(edge_ids: list[str], edge_strength_by_id: dict[str, Any]) -> float:
    """PRODUCT of constituent edges' computed_strength (JL-013).

    A zero-hop (self-ruling) chain has no edges to weaken it — full strength (1.0).
    If some edges lack computed_strength, the product uses only the known ones
    (still a real product, not an average); only falls back to the documented
    placeholder when NONE of the chain's edges have a computed_strength.
    """
    if not edge_ids:
        return 1.0
    known = [
        float(edge_strength_by_id[eid])
        for eid in edge_ids
        if edge_strength_by_id.get(eid) is not None
    ]
    if not known:
        return PATH_STRENGTH_PLACEHOLDER
    product = 1.0
    for s in known:
        product *= s
    return round(product, 6)

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

# Grahas that rule their own signs (self-ruling = final dispositor candidate)
SELF_RULING_PAIRS: dict[str, set[str]] = {
    "sun":     {"leo"},
    "moon":    {"cancer"},
    "mars":    {"aries", "scorpio"},
    "mercury": {"gemini", "virgo"},
    "jupiter": {"sagittarius", "pisces"},
    "venus":   {"taurus", "libra"},
    "saturn":  {"capricorn", "aquarius"},
}

# Reverse map: sign → ruling graha
SIGN_RULER: dict[str, str] = {
    "aries": "mars", "taurus": "venus", "gemini": "mercury",
    "cancer": "moon", "leo": "sun", "virgo": "mercury",
    "libra": "venus", "scorpio": "mars", "sagittarius": "jupiter",
    "capricorn": "saturn", "aquarius": "saturn", "pisces": "jupiter",
}

_PATH_INSERT = """
INSERT INTO bodha_cgm_paths (
  path_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  path_type, from_node_id, to_node_id,
  path_node_ids_array, path_edge_ids_array,
  path_length, path_strength, is_final_dispositor, convergence_count,
  centrality_formula_version, path_label_human,
  verification_pass_status, citation_ref, citation_human,
  computed_at
) VALUES (
  %(path_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(path_type)s, %(from_node_id)s, %(to_node_id)s,
  %(path_node_ids_array)s, %(path_edge_ids_array)s,
  %(path_length)s, %(path_strength)s, %(is_final_dispositor)s, %(convergence_count)s,
  %(centrality_formula_version)s, %(path_label_human)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s,
  %(computed_at)s
)
ON CONFLICT (chart_id, ayanamsha_id, build_id, snapshot_type, path_type, from_node_id, to_node_id)
DO NOTHING
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


def _is_self_ruling(graha: str, position_in_chart_jsonb: Any) -> bool:
    """
    Returns True if the graha occupies a sign it rules (self-ruling = final dispositor).
    position_in_chart_jsonb expected to contain a 'sign' key (lowercase).
    """
    if not graha or not position_in_chart_jsonb:
        return False
    pos = position_in_chart_jsonb
    if isinstance(pos, str):
        try:
            pos = json.loads(pos)
        except (ValueError, TypeError):
            return False
    sign = str(pos.get("sign", "")).lower().strip()
    ruled_signs = SELF_RULING_PAIRS.get(graha.lower(), set())
    return sign in ruled_signs


def _build_dispositor_chains(
    graha_nodes: list[dict],
    edge_by_from: dict[str, list[dict]],
    node_by_id: dict[str, dict],
) -> list[dict]:
    """
    Build dispositor chains from CGM graph data.

    Returns list of chain dicts:
      {from_node_id, to_node_id, node_chain, edge_chain, is_final_dispositor, label}
    """
    chains = []

    for start_node in graha_nodes:
        start_id = str(start_node["node_id"])
        start_subject = str(start_node.get("node_subject", "unknown")).lower()

        node_chain: list[str] = [start_id]
        edge_chain: list[str] = []
        label_parts: list[str] = [start_node.get("node_label_human") or start_subject]
        visited: set[str] = {start_id}

        current_id = start_id
        is_final = _is_self_ruling(start_subject, start_node.get("position_in_chart_jsonb"))

        if is_final:
            # Self-ruling graha: chain of length 0 (it IS the dispositor)
            chains.append({
                "from_node_id": start_id,
                "to_node_id": start_id,
                "node_chain": [start_id],
                "edge_chain": [],
                "is_final_dispositor": True,
                "label": f"{label_parts[0]} (self-ruling / final dispositor)",
            })
            continue

        depth = 0
        while depth < MAX_CHAIN_DEPTH:
            # Find dispositor edge from current node
            dispos_edges = [
                e for e in edge_by_from.get(current_id, [])
                if str(e.get("relationship_basis", "")).lower() in ("dispositor", "lord_of_sign")
                   or str(e.get("edge_type", "")).lower() in ("disposited_by", "dispositor", "sign_lord")
            ]
            if not dispos_edges:
                break

            # Pick highest strength dispositor edge
            dispos_edges.sort(key=lambda e: float(e.get("computed_strength") or 0), reverse=True)
            next_edge = dispos_edges[0]
            next_node_id = str(next_edge["to_node_id"])

            if next_node_id in visited:
                # Cycle detected — chain ends here (not a clean final dispositor)
                break

            next_node = node_by_id.get(next_node_id)
            if not next_node:
                break

            edge_chain.append(str(next_edge["edge_id"]))
            node_chain.append(next_node_id)
            label_parts.append(next_node.get("node_label_human") or str(next_node.get("node_subject", "")))
            visited.add(next_node_id)
            current_id = next_node_id
            depth += 1

            # Check if this node is self-ruling
            next_subject = str(next_node.get("node_subject", "")).lower()
            next_pos = next_node.get("position_in_chart_jsonb")
            if _is_self_ruling(next_subject, next_pos):
                is_final = True
                break

        if len(node_chain) > 1:  # only emit chains with at least 1 hop
            separator = " → "
            label = separator.join(label_parts)
            if is_final:
                label += " (final dispositor)"
            chains.append({
                "from_node_id": start_id,
                "to_node_id": node_chain[-1],
                "node_chain": node_chain,
                "edge_chain": edge_chain,
                "is_final_dispositor": is_final,
                "label": label,
            })

    return chains


def _write_aya(conn: Any, chart_id: str, aya: str, build_id: str, now: str) -> int:
    """Compute and write dispositor chains for one ayanamsha. Returns row count."""

    # Fetch graha nodes
    graha_nodes = _fetch_dict(
        conn,
        """SELECT node_id, node_subject, node_label_human, position_in_chart_jsonb
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND snapshot_type = %s AND node_type = 'graha'""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )
    if not graha_nodes:
        logger.info("[bo_cgm_paths] %s — no graha nodes found; skipping", aya)
        return 0

    # Fetch all dispositor-class edges.
    # Post-WP-2.3 bo_karanajala emits real dispositor edges (edge_type='dispositor',
    # relationship_basis='dispositor'/'lord_of_sign') and bo_bimba hydrates
    # position_in_chart_jsonb['sign'], so multi-hop chains and self-ruling (length-0)
    # paths both fire on the native's real topology. A warning is logged only if the
    # dispositor edge set is entirely empty — post-WP-2.3 that would itself be a
    # build fault worth auditing.
    all_edges = _fetch_dict(
        conn,
        """SELECT edge_id, from_node_id, to_node_id, edge_type, relationship_basis,
                  computed_strength
           FROM bodha_cgm_edges
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND snapshot_type = %s
             AND (
               LOWER(relationship_basis) IN ('dispositor', 'lord_of_sign')
               OR LOWER(edge_type) IN ('disposited_by', 'dispositor', 'sign_lord')
             )""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )
    if not all_edges:
        logger.warning(
            "[bo_cgm_paths] %s — 0 dispositor edges found in bodha_cgm_edges; "
            "post-WP-2.3 bo_karanajala should emit dispositor edges — an empty set here "
            "means multi-hop chains cannot be built (only self-ruling length-0 paths); "
            "verify the build produced dispositor edges",
            aya,
        )

    # Also fetch all nodes so we can traverse
    all_nodes = _fetch_dict(
        conn,
        """SELECT node_id, node_subject, node_label_human, position_in_chart_jsonb
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )

    node_by_id: dict[str, dict] = {str(n["node_id"]): n for n in all_nodes}
    edge_by_from: dict[str, list[dict]] = {}
    edge_strength_by_id: dict[str, Any] = {}
    for e in all_edges:
        fid = str(e["from_node_id"])
        if fid not in edge_by_from:
            edge_by_from[fid] = []
        edge_by_from[fid].append(e)
        edge_strength_by_id[str(e["edge_id"])] = e.get("computed_strength")

    chains = _build_dispositor_chains(graha_nodes, edge_by_from, node_by_id)

    computed_strengths = [
        _path_strength(chain["edge_chain"], edge_strength_by_id) for chain in chains
    ]
    if len(computed_strengths) > 1 and len(set(computed_strengths)) == 1:
        logger.warning(
            "[bo_cgm_paths] %s — degeneracy gate: all %d path_strength values "
            "collapsed to the constant %s — check edge computed_strength population",
            aya, len(computed_strengths), computed_strengths[0],
        )

    inserted = 0
    with conn.cursor() as cur:
        for chain in chains:
            path_id = str(uuid.uuid4())
            row = {
                "path_id": path_id,
                "chart_id": chart_id,
                "ayanamsha_id": aya,
                "build_id": build_id,
                "snapshot_type": SNAPSHOT_TYPE,
                "path_type": PATH_TYPE,
                "from_node_id": chain["from_node_id"],
                "to_node_id": chain["to_node_id"],
                "path_node_ids_array": chain["node_chain"],
                "path_edge_ids_array": chain["edge_chain"] or [],
                "path_length": len(chain["node_chain"]) - 1,
                "path_strength": _path_strength(chain["edge_chain"], edge_strength_by_id),
                "is_final_dispositor": chain["is_final_dispositor"],
                "convergence_count": 1,
                "centrality_formula_version": ENGINE_VERSION,
                "path_label_human": chain["label"],
                # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
                # "pass" — an unconditional stamp with no verification logic behind it, and a
                # live false-green the serve layer counted as verified. Audited: nothing here
                # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
                "verification_pass_status": UNVERIFIED_DEFAULT,
                "citation_ref": "bo_cgm_paths:dispositor_chain_algorithm:v1",
                "citation_human": "CGM dispositor chain: graha → sign-lord traversal until self-ruling or max depth",
                "computed_at": now,
            }
            cur.execute(_PATH_INSERT, row)
            inserted += 1

    logger.info("[bo_cgm_paths] %s — %d chains written", aya, inserted)
    return inserted


@register("bo_cgm_paths")
class BoCgmPathsWriter(WriterBase):
    """bo_cgm_paths: dispositor chain path analysis over the CGM graph."""
    asset_id = "bo_cgm_paths"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="dry_run — would compute dispositor chains for all ayanamshas",
            )

        # Idempotency: delete prior rows for this chart
        with conn.cursor() as cur:
            # Disable per-statement timeout for the heavy DELETE on large charts.
            # SET LOCAL scopes to the orchestrator txn (writer never commits).
            # Ref: bo_laksana native-rebuild timeout; ka_* precedent (PR 422).
            cur.execute("SET LOCAL statement_timeout = 0")
            cur.execute("DELETE FROM bodha_cgm_paths WHERE chart_id = %s", [chart_id])

        total = 0
        for aya in CANONICAL_AYAS:
            total += _write_aya(conn, chart_id, aya, build_id, now)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            notes=f"dispositor_chains={total} across {len(CANONICAL_AYAS)} ayanamshas",
        )
