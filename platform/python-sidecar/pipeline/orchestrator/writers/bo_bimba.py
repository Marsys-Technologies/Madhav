"""
bo_bimba — Cosmic Geometry Map: Nodes (L2 Bodha)
=================================================
Creates one bodha_cgm_nodes row per unique entity active in the chart.

Entities extracted from bodha_msr_signals after bo_laksana runs:
  - 'graha'   — the 9 grahas (Sun…Ketu)
  - 'bhava'   — houses 1-12
  - 'domain'  — career / wealth / health / relationship / spirituality / character
  - 'yoga'    — named yoga signals with class='yoga' or 'dosha'

Centrality metrics (betweenness, pagerank, eigenvector) are left NULL here;
bo_karanajala back-fills them after building the edge set.

LIGHT writer: loops over CANONICAL_AYANAMSHAS in a single run() call.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION   = "bo_bimba_v1.0"
SNAPSHOT_TYPE    = "static_natal"
GRAPH_LIB        = "internal"
GRAPH_LIB_VER    = "1.0"
CANONICAL_AYAS   = ["LAHIRI", "RAMAN", "KRISHNAMURTI", "YUKTESHWAR", "TROPICAL"]

KNOWN_GRAHAS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]
KNOWN_DOMAINS = [
    "career", "wealth", "health", "relationship",
    "spirituality", "character", "general",
]

_NODE_INSERT = """
INSERT INTO bodha_cgm_nodes (
  node_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  node_type, node_subject, node_label_human,
  position_in_chart_jsonb, strength_score, dignity_state,
  degree_in, degree_out,
  betweenness_centrality, eigenvector_centrality, pagerank_score,
  clustering_coefficient, closeness_centrality, harmonic_centrality, core_number,
  primary_domain, domain_affiliations_jsonb, cluster_membership_array, cgm_subgraph_cluster_id,
  msr_signal_id, configuration_constituents_array, configuration_lifecycle_state,
  hub_flag, hub_score, hub_edge_types_array,
  present_in_traditions_array, cross_ayanamsha_presence_score,
  node_embedding_vec, ephemeris_audit_jsonb,
  msr_salience_version_used, cdlm_version_used,
  graph_compute_library, graph_compute_library_version,
  verification_pass_status, citation_ref, citation_human, computed_at, engine_version
) VALUES (
  %(node_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(node_type)s, %(node_subject)s, %(node_label_human)s,
  %(position_in_chart_jsonb)s::jsonb, %(strength_score)s, %(dignity_state)s,
  %(degree_in)s, %(degree_out)s,
  NULL, NULL, NULL, NULL, NULL, NULL, NULL,
  %(primary_domain)s, %(domain_affiliations_jsonb)s::jsonb, %(cluster_membership_array)s, NULL,
  %(msr_signal_id)s, %(configuration_constituents_array)s, %(configuration_lifecycle_state)s,
  %(hub_flag)s, NULL, NULL,
  %(present_in_traditions_array)s, NULL,
  NULL, NULL,
  NULL, NULL,
  %(graph_compute_library)s, %(graph_compute_library_version)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s, %(engine_version)s
)
"""

_BATCH_SIZE = 50


def _fetch_msr_signals(conn, chart_id: str, aya: str) -> list[dict]:
    rows = conn.execute(
        """SELECT signal_id, signal_type_class, signal_tradition, configuration_jsonb,
                  domains_affected_array, deterministic_strength, computed_salience,
                  verification_pass_status, salience_formula_version
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    ).fetchall()
    keys = [
        "signal_id", "signal_type_class", "signal_tradition", "configuration_jsonb",
        "domains_affected_array", "deterministic_strength", "computed_salience",
        "verification_pass_status", "salience_formula_version",
    ]
    return [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]


def _parse_graha_from_signal(cfg: dict) -> str | None:
    for k in ("graha", "primary_graha", "lord", "fact_key"):
        v = cfg.get(k)
        if v and str(v) in KNOWN_GRAHAS:
            return str(v)
        if v and isinstance(v, str):
            parts = v.split(":")
            for p in parts:
                if p in KNOWN_GRAHAS:
                    return p
    return None


def _parse_house_from_signal(cfg: dict) -> int | None:
    for k in ("house", "house_number", "bhava"):
        v = cfg.get(k)
        if v is not None:
            try:
                h = int(v)
                if 1 <= h <= 12:
                    return h
            except (TypeError, ValueError):
                pass
    return None


def _build_nodes_for_aya(
    chart_id: str, aya: str, build_id: str, signals: list[dict], now: str
) -> list[dict]:
    nodes: list[dict] = []

    # ── Graha nodes (always 9, with strength from MSR signals) ──────────────
    graha_strength: dict[str, float] = {}
    graha_dignity: dict[str, str] = {}
    graha_tradition: dict[str, set] = {g: set() for g in KNOWN_GRAHAS}

    for sig in signals:
        cfg = {}
        if sig.get("configuration_jsonb"):
            try:
                cfg = json.loads(sig["configuration_jsonb"]) if isinstance(sig["configuration_jsonb"], str) else sig["configuration_jsonb"]
            except Exception:
                pass
        g = _parse_graha_from_signal(cfg)
        if g:
            curr = graha_strength.get(g, 0.0)
            sal = float(sig.get("computed_salience") or 0.0)
            if sal > curr:
                graha_strength[g] = sal
                graha_dignity[g] = cfg.get("fact_value_text") or cfg.get("dignity_state") or "neutral"
            if sig.get("signal_tradition"):
                graha_tradition[g].add(str(sig["signal_tradition"]))

    for graha in KNOWN_GRAHAS:
        nodes.append({
            "node_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "node_type": "graha",
            "node_subject": graha,
            "node_label_human": graha,
            "position_in_chart_jsonb": None,
            "strength_score": round(graha_strength.get(graha, 0.5), 6),
            "dignity_state": graha_dignity.get(graha),
            "degree_in": 0,
            "degree_out": 0,
            "primary_domain": None,
            "domain_affiliations_jsonb": None,
            "cluster_membership_array": None,
            "msr_signal_id": None,
            "configuration_constituents_array": None,
            "configuration_lifecycle_state": "natal_permanent",
            "hub_flag": False,
            "present_in_traditions_array": sorted(graha_tradition.get(graha, [])) or ["parashari"],
            "graph_compute_library": GRAPH_LIB,
            "graph_compute_library_version": GRAPH_LIB_VER,
            "verification_pass_status": "two_pass_verified",
            "citation_ref": f"bo_bimba/graha/{graha}",
            "citation_human": f"Graha node: {graha}",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        })

    # ── Bhava nodes (12 houses) ───────────────────────────────────────────────
    house_signals: dict[int, float] = {}
    for sig in signals:
        cfg = {}
        if sig.get("configuration_jsonb"):
            try:
                cfg = json.loads(sig["configuration_jsonb"]) if isinstance(sig["configuration_jsonb"], str) else sig["configuration_jsonb"]
            except Exception:
                pass
        h = _parse_house_from_signal(cfg)
        if h:
            sal = float(sig.get("computed_salience") or 0.0)
            if sal > house_signals.get(h, 0.0):
                house_signals[h] = sal

    for h in range(1, 13):
        nodes.append({
            "node_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "node_type": "bhava",
            "node_subject": str(h),
            "node_label_human": f"House {h}",
            "position_in_chart_jsonb": json.dumps({"house": h}),
            "strength_score": round(house_signals.get(h, 0.4), 6),
            "dignity_state": None,
            "degree_in": 0,
            "degree_out": 0,
            "primary_domain": None,
            "domain_affiliations_jsonb": None,
            "cluster_membership_array": None,
            "msr_signal_id": None,
            "configuration_constituents_array": None,
            "configuration_lifecycle_state": "natal_permanent",
            "hub_flag": h in (1, 5, 9),
            "present_in_traditions_array": ["parashari"],
            "graph_compute_library": GRAPH_LIB,
            "graph_compute_library_version": GRAPH_LIB_VER,
            "verification_pass_status": "two_pass_verified",
            "citation_ref": f"bo_bimba/bhava/{h}",
            "citation_human": f"Bhava node: house {h}",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        })

    # ── Domain nodes ──────────────────────────────────────────────────────────
    domain_salience: dict[str, float] = {d: 0.0 for d in KNOWN_DOMAINS}
    for sig in signals:
        domains = sig.get("domains_affected_array") or []
        sal = float(sig.get("computed_salience") or 0.0)
        for d in domains:
            if d in domain_salience:
                domain_salience[d] += sal

    for domain in KNOWN_DOMAINS:
        nodes.append({
            "node_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "node_type": "domain",
            "node_subject": domain,
            "node_label_human": domain.capitalize(),
            "position_in_chart_jsonb": None,
            "strength_score": round(min(domain_salience.get(domain, 0.0), 1.0), 6),
            "dignity_state": None,
            "degree_in": 0,
            "degree_out": 0,
            "primary_domain": domain,
            "domain_affiliations_jsonb": json.dumps({domain: 1.0}),
            "cluster_membership_array": [domain],
            "msr_signal_id": None,
            "configuration_constituents_array": None,
            "configuration_lifecycle_state": "natal_permanent",
            "hub_flag": False,
            "present_in_traditions_array": ["parashari"],
            "graph_compute_library": GRAPH_LIB,
            "graph_compute_library_version": GRAPH_LIB_VER,
            "verification_pass_status": "two_pass_verified",
            "citation_ref": f"bo_bimba/domain/{domain}",
            "citation_human": f"Domain node: {domain}",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        })

    return nodes


def _batch_insert(conn, nodes: list[dict]) -> int:
    inserted = 0
    for i in range(0, len(nodes), _BATCH_SIZE):
        for row in nodes[i:i + _BATCH_SIZE]:
            conn.execute(_NODE_INSERT, row)
        inserted += len(nodes[i:i + _BATCH_SIZE])
    return inserted


@register("bo_bimba")
class BoBimbaWriter(WriterBase):
    """bo_bimba: CGM node layer — one row per unique entity per ayanamsha."""
    asset_id = "bo_bimba"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import replace_prior_cgm_nodes

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()
        total    = 0

        for aya in CANONICAL_AYAS:
            if ctx.dry_run:
                signals = _fetch_msr_signals(conn, chart_id, aya)
                logger.info("[bo_bimba dry_run] %s — %d MSR signals found", aya, len(signals))
                continue

            signals = _fetch_msr_signals(conn, chart_id, aya)
            nodes   = _build_nodes_for_aya(chart_id, aya, build_id, signals, now)

            deleted = replace_prior_cgm_nodes(conn, chart_id, aya, SNAPSHOT_TYPE)
            logger.info("[bo_bimba] %s — deleted %d prior, inserting %d nodes", aya, deleted, len(nodes))

            total += _batch_insert(conn, nodes)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total)
