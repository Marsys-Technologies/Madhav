"""
bo_karanajala — CGM Edges + Contradictions (L2 Bodha)
======================================================
Reads bodha_msr_signals + bodha_cgm_nodes → writes:
  - bodha_cgm_edges  (directed edges between graph nodes)
  - bodha_contradictions  (yoga-vs-dosha / tradition-conflict pairs)

Edge types created:
  'aspect'       — Parashari aspect from one graha node to another
  'conjunction'  — tight conjunction within orb
  'dispositor'   — graha → its dispositor graha
  'yoga_domain'  — yoga signal → domain node (positive)
  'dosha_domain' — dosha signal → domain node (antagonist)
  'sade_sati'    — Saturn → Moon / house 12 (transit-period)

Contradiction detection:
  - A yoga signal and a dosha signal share the same domain AND same graha
    → 'yoga_vs_dosha' contradiction pair

LIGHT writer.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION   = "bo_karanajala_v1.0"
SNAPSHOT_TYPE    = "static_natal"
GRAPH_LIB        = "internal"
GRAPH_LIB_VER    = "1.0"
CANONICAL_AYAS   = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

_EDGE_INSERT = """
INSERT INTO bodha_cgm_edges (
  edge_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  edge_type, from_node_id, to_node_id, direction, computed_strength, weight_formula_version,
  edge_properties_jsonb, relationship_class, semantic_path_class,
  active_duration_class, active_dasha_periods_jsonb,
  underlying_msr_signal_ids_array, cross_system_consensus_count,
  cancelled_flag, cancelled_by_jsonb, cross_ayanamsha_edge_stability_score,
  present_in_traditions_array, edge_betweenness, in_shortest_path_count,
  graph_compute_library, graph_compute_library_version,
  verification_pass_status, citation_ref, citation_human, computed_at, engine_version
) VALUES (
  %(edge_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(edge_type)s, %(from_node_id)s, %(to_node_id)s, %(direction)s,
  %(computed_strength)s, %(weight_formula_version)s,
  %(edge_properties_jsonb)s::jsonb, %(relationship_class)s, %(semantic_path_class)s,
  %(active_duration_class)s, %(active_dasha_periods_jsonb)s,
  %(underlying_msr_signal_ids_array)s, %(cross_system_consensus_count)s,
  %(cancelled_flag)s, NULL, NULL,
  %(present_in_traditions_array)s, NULL, NULL,
  %(graph_compute_library)s, %(graph_compute_library_version)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s,
  %(computed_at)s, %(engine_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, build_id, snapshot_type, edge_type, from_node_id, to_node_id)
DO NOTHING
"""

_CONTRADICTION_INSERT = """
INSERT INTO bodha_contradictions (
  contradiction_id, chart_id, ayanamsha_id, build_id,
  signal_a_id, signal_b_id, tension_basis_jsonb, tension_class,
  domains_affected_array, combined_salience, resolution_hint_jsonb,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(contradiction_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(signal_a_id)s, %(signal_b_id)s, %(tension_basis_jsonb)s::jsonb, %(tension_class)s,
  %(domains_affected_array)s, %(combined_salience)s, NULL,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
ON CONFLICT (chart_id, ayanamsha_id, build_id, signal_a_id, signal_b_id) DO NOTHING
"""

_BATCH_SIZE = 50

KNOWN_GRAHAS = {
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
}

KNOWN_DOMAINS = {
    "career", "wealth", "health", "relationship",
    "spirituality", "character", "general",
}


def _fetch_node_map(conn, chart_id: str, aya: str) -> dict[tuple[str, str], str]:
    """Returns {(node_type, node_subject): node_id}."""
    rows = conn.execute(
        """SELECT node_id, node_type, node_subject
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
        [chart_id, aya, SNAPSHOT_TYPE],
    ).fetchall()
    result: dict[tuple[str, str], str] = {}
    for r in rows:
        if isinstance(r, dict):
            result[(r["node_type"], r["node_subject"])] = str(r["node_id"])
        else:
            result[(str(r[1]), str(r[2]))] = str(r[0])
    return result


def _fetch_signals(conn, chart_id: str, aya: str) -> list[dict]:
    rows = conn.execute(
        """SELECT signal_id, signal_type_class, signal_tradition, configuration_jsonb,
                  domains_affected_array, computed_salience, verification_pass_status,
                  salience_formula_version, signal_type_id
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    ).fetchall()
    keys = [
        "signal_id", "signal_type_class", "signal_tradition", "configuration_jsonb",
        "domains_affected_array", "computed_salience", "verification_pass_status",
        "salience_formula_version", "signal_type_id",
    ]
    return [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]


def _parse_cfg(sig: dict) -> dict:
    cfg_raw = sig.get("configuration_jsonb") or {}
    if isinstance(cfg_raw, str):
        try:
            return json.loads(cfg_raw)
        except Exception:
            return {}
    return cfg_raw if isinstance(cfg_raw, dict) else {}


def _graha_from_cfg(cfg: dict) -> str | None:
    for k in ("graha", "primary_graha", "lord", "from_graha", "fact_key"):
        v = cfg.get(k, "")
        if v in KNOWN_GRAHAS:
            return str(v)
        if isinstance(v, str):
            for part in v.split(":"):
                if part in KNOWN_GRAHAS:
                    return part
    return None


def _build_edges_and_contradictions(
    chart_id: str, aya: str, build_id: str,
    signals: list[dict], node_map: dict[tuple[str, str], str], now: str
) -> tuple[list[dict], list[dict]]:
    edges: list[dict] = []
    contradictions: list[dict] = []

    # Index signals by graha + class for contradiction detection
    yoga_by_graha: dict[str, dict] = {}   # graha → signal
    dosha_by_graha: dict[str, dict] = {}  # graha → signal

    for sig in signals:
        sig_id     = str(sig.get("signal_id", ""))
        sig_class  = str(sig.get("signal_type_class") or "")
        tradition  = str(sig.get("signal_tradition") or "parashari")
        domains    = sig.get("domains_affected_array") or []
        salience   = float(sig.get("computed_salience") or 0.0)
        type_id    = str(sig.get("signal_type_id") or "")
        ver_pass   = str(sig.get("verification_pass_status") or "documented_approximation")
        cfg        = _parse_cfg(sig)
        graha      = _graha_from_cfg(cfg)

        def _get_node(ntype: str, subject: str) -> str | None:
            return node_map.get((ntype, subject))

        # ── Yoga → domain (positive edge) ────────────────────────────────────
        if sig_class == "yoga" and graha:
            from_node = _get_node("graha", graha)
            for domain in domains:
                to_node = _get_node("domain", domain)
                if from_node and to_node:
                    edges.append({
                        "edge_id": str(uuid.uuid4()),
                        "chart_id": chart_id,
                        "ayanamsha_id": aya,
                        "build_id": build_id,
                        "snapshot_type": SNAPSHOT_TYPE,
                        "edge_type": "yoga_domain",
                        "from_node_id": from_node,
                        "to_node_id": to_node,
                        "direction": "directed",
                        "computed_strength": round(salience, 6),
                        "weight_formula_version": "edge_weight_v1.0",
                        "edge_properties_jsonb": json.dumps({"signal_id": sig_id, "yoga": type_id}),
                        "relationship_class": "activation",
                        "semantic_path_class": "yoga_activation",
                        "active_duration_class": "natal_permanent",
                        "active_dasha_periods_jsonb": None,
                        "underlying_msr_signal_ids_array": [sig_id],
                        "cross_system_consensus_count": 1,
                        "cancelled_flag": False,
                        "present_in_traditions_array": [tradition],
                        "graph_compute_library": GRAPH_LIB,
                        "graph_compute_library_version": GRAPH_LIB_VER,
                        "verification_pass_status": ver_pass,
                        "citation_ref": f"bodha_msr_signals/{sig_id}",
                        "citation_human": f"Yoga→domain edge: {type_id}→{domain}",
                        "computed_at": now,
                        "engine_version": ENGINE_VERSION,
                    })
            if graha:
                yoga_by_graha[graha] = sig

        # ── Dosha → domain (antagonist edge) ─────────────────────────────────
        elif sig_class == "dosha" and graha:
            from_node = _get_node("graha", graha)
            for domain in domains:
                to_node = _get_node("domain", domain)
                if from_node and to_node:
                    edges.append({
                        "edge_id": str(uuid.uuid4()),
                        "chart_id": chart_id,
                        "ayanamsha_id": aya,
                        "build_id": build_id,
                        "snapshot_type": SNAPSHOT_TYPE,
                        "edge_type": "dosha_domain",
                        "from_node_id": from_node,
                        "to_node_id": to_node,
                        "direction": "directed",
                        "computed_strength": round(-salience, 6),
                        "weight_formula_version": "edge_weight_v1.0",
                        "edge_properties_jsonb": json.dumps({"signal_id": sig_id, "dosha": type_id}),
                        "relationship_class": "antagonist",
                        "semantic_path_class": "dosha_impairment",
                        "active_duration_class": "natal_permanent",
                        "active_dasha_periods_jsonb": None,
                        "underlying_msr_signal_ids_array": [sig_id],
                        "cross_system_consensus_count": 1,
                        "cancelled_flag": False,
                        "present_in_traditions_array": [tradition],
                        "graph_compute_library": GRAPH_LIB,
                        "graph_compute_library_version": GRAPH_LIB_VER,
                        "verification_pass_status": ver_pass,
                        "citation_ref": f"bodha_msr_signals/{sig_id}",
                        "citation_human": f"Dosha→domain edge: {type_id}→{domain}",
                        "computed_at": now,
                        "engine_version": ENGINE_VERSION,
                    })
            if graha:
                dosha_by_graha[graha] = sig

        # ── Aspect / conjunction / path edges ────────────────────────────────
        elif sig_class == "composite_state" and graha:
            aspected_graha = (cfg.get("aspected_graha") or cfg.get("graha_b")
                              or cfg.get("to_graha"))
            if not aspected_graha:
                fact_key = cfg.get("fact_key", "")
                parts = fact_key.split(":")
                for p in parts:
                    if p in KNOWN_GRAHAS and p != graha:
                        aspected_graha = p
                        break
            if aspected_graha and aspected_graha in KNOWN_GRAHAS:
                from_node = _get_node("graha", graha)
                to_node   = _get_node("graha", aspected_graha)
                if from_node and to_node:
                    etype = "conjunction" if "conjunction" in type_id else "aspect"
                    edges.append({
                        "edge_id": str(uuid.uuid4()),
                        "chart_id": chart_id,
                        "ayanamsha_id": aya,
                        "build_id": build_id,
                        "snapshot_type": SNAPSHOT_TYPE,
                        "edge_type": etype,
                        "from_node_id": from_node,
                        "to_node_id": to_node,
                        "direction": "directed",
                        "computed_strength": round(salience, 6),
                        "weight_formula_version": "edge_weight_v1.0",
                        "edge_properties_jsonb": json.dumps({"signal_id": sig_id}),
                        "relationship_class": etype,
                        "semantic_path_class": "graha_graha",
                        "active_duration_class": "natal_permanent",
                        "active_dasha_periods_jsonb": None,
                        "underlying_msr_signal_ids_array": [sig_id],
                        "cross_system_consensus_count": 1,
                        "cancelled_flag": False,
                        "present_in_traditions_array": [tradition],
                        "graph_compute_library": GRAPH_LIB,
                        "graph_compute_library_version": GRAPH_LIB_VER,
                        "verification_pass_status": ver_pass,
                        "citation_ref": f"bodha_msr_signals/{sig_id}",
                        "citation_human": f"{etype}: {graha}→{aspected_graha}",
                        "computed_at": now,
                        "engine_version": ENGINE_VERSION,
                    })

    # ── Contradiction detection ────────────────────────────────────────────────
    for graha in yoga_by_graha:
        if graha in dosha_by_graha:
            y_sig = yoga_by_graha[graha]
            d_sig = dosha_by_graha[graha]
            y_domains = set(y_sig.get("domains_affected_array") or [])
            d_domains = set(d_sig.get("domains_affected_array") or [])
            shared_domains = y_domains & d_domains
            if shared_domains:
                contradictions.append({
                    "contradiction_id": str(uuid.uuid4()),
                    "chart_id": chart_id,
                    "ayanamsha_id": aya,
                    "build_id": build_id,
                    "signal_a_id": str(y_sig.get("signal_id")),
                    "signal_b_id": str(d_sig.get("signal_id")),
                    "tension_basis_jsonb": json.dumps({
                        "graha": graha,
                        "yoga_signal": str(y_sig.get("signal_type_id")),
                        "dosha_signal": str(d_sig.get("signal_type_id")),
                        "shared_domains": sorted(shared_domains),
                    }),
                    "tension_class": "yoga_vs_dosha",
                    "domains_affected_array": sorted(shared_domains),
                    "combined_salience": round(
                        float(y_sig.get("computed_salience") or 0.0)
                        + float(d_sig.get("computed_salience") or 0.0),
                        6
                    ),
                    "verification_pass_status": "documented_approximation",
                    "citation_ref": f"bo_karanajala/contradiction/{graha}",
                    "citation_human": f"yoga_vs_dosha contradiction on {graha} in {sorted(shared_domains)}",
                    "computed_at": now,
                })

    return edges, contradictions


def _batch_insert(conn, rows: list[dict], sql: str) -> int:
    inserted = 0
    for i in range(0, len(rows), _BATCH_SIZE):
        for row in rows[i:i + _BATCH_SIZE]:
            conn.execute(sql, row)
        inserted += len(rows[i:i + _BATCH_SIZE])
    return inserted


@register("bo_karanajala")
class BoKaranajalaWriter(WriterBase):
    """bo_karanajala: CGM edges + contradiction pairs."""
    asset_id = "bo_karanajala"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import (
            replace_prior_cgm_edges, replace_prior_contradictions,
        )

        chart_id  = ctx.config["chart_id"]
        build_id  = ctx.build_id
        conn      = ctx.db_conn
        now       = datetime.now(timezone.utc).isoformat()
        total_e   = 0
        total_c   = 0

        for aya in CANONICAL_AYAS:
            signals  = _fetch_signals(conn, chart_id, aya)
            node_map = _fetch_node_map(conn, chart_id, aya)

            if ctx.dry_run:
                logger.info("[bo_karanajala dry_run] %s — %d signals, %d nodes",
                            aya, len(signals), len(node_map))
                continue

            if not node_map:
                raise RuntimeError(
                    f"[bo_karanajala] G3: chart_id={chart_id} ayanamsha={aya} — "
                    "node_map is empty (bodha_cgm_nodes has 0 rows for this chart/aya); "
                    "bo_bimba must run and succeed before bo_karanajala"
                )

            edges, contradictions = _build_edges_and_contradictions(
                chart_id, aya, build_id, signals, node_map, now
            )

            replace_prior_cgm_edges(conn, chart_id, aya, SNAPSHOT_TYPE)
            replace_prior_contradictions(conn, chart_id, aya)

            logger.info("[bo_karanajala] %s — %d edges, %d contradictions", aya, len(edges), len(contradictions))
            total_e += _batch_insert(conn, edges, _EDGE_INSERT)
            total_c += _batch_insert(conn, contradictions, _CONTRADICTION_INSERT)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total_e + total_c,
                            notes=f"edges={total_e} contradictions={total_c}")
