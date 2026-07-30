"""
bo_cdlm_summary — CDLM Chart Summary Writer (L2 Bodha)
======================================================
संकलन = "summary/compilation"

Reads bodha_cdlm_cells (written by bo_sangati) and aggregates per-chart
cross-domain linkage statistics into bodha_cdlm_chart_summary.

Emits 1 row per chart per ayanamsha with:
  - total_chart_linkage: sum of all computed_linkage_strength values
  - dominant_3_domains_array: 3 domains with highest total linkage
  - weakest_3_domains_array: 3 domains with lowest total linkage
  - contradiction_density: mean contradiction_density across CDLM cells
  - bridge_link_count: count of cells with asymmetric_linkage_flag = true
  - asymmetric_link_count: count of asymmetric linkage cells
  - strongest_linkage_pair_jsonb: {domain_a, domain_b, strength} of strongest cell
  - domain_connectivity_jsonb: {domain → total_linkage_strength} map

ANTI-DRIFT: this writer REFERENCES bodha_cdlm_cells — never invents values.

DESIGN FLOOR NOTE: this writer produces exactly 5 rows per chart — one per ayanamsha
(lahiri_chitrapaksha, raman, krishnamurti, surya_siddhanta_classical, true_chitra).
target_floor = 5 is the correct expectation for any single-chart build. A count of
fewer than 5 means at least one ayanamsha had no bodha_cdlm_cells to aggregate (valid
for sparse charts but worth investigating); a count of more than 5 indicates a
delete-then-insert idempotency failure.

LIGHT writer — one run() call, iterates 5 ayanamshas.
"""
from __future__ import annotations

import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_cdlm_summary_v1.0"
SNAPSHOT_TYPE  = "static_natal"

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

_SUMMARY_INSERT = """
INSERT INTO bodha_cdlm_chart_summary (
  summary_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord, tradition_view_id,
  chart_typology_class,
  pattern_cluster_markers_jsonb,
  total_chart_linkage,
  contradiction_density,
  house_to_domain_strength_jsonb,
  karaka_to_domain_strength_jsonb,
  dominant_3_domains_array,
  weakest_3_domains_array,
  bridge_link_count,
  asymmetric_link_count,
  verification_pass_status, citation_ref, citation_human,
  computed_at
) VALUES (
  %(summary_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  NULL, NULL, NULL, NULL,
  %(chart_typology_class)s,
  %(pattern_cluster_markers_jsonb)s::jsonb,
  %(total_chart_linkage)s,
  %(contradiction_density)s,
  %(house_to_domain_strength_jsonb)s::jsonb,
  %(karaka_to_domain_strength_jsonb)s::jsonb,
  %(dominant_3_domains_array)s,
  %(weakest_3_domains_array)s,
  %(bridge_link_count)s,
  %(asymmetric_link_count)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s,
  %(computed_at)s
)
"""


_ROLLUP_INSERT = """
INSERT INTO bodha_cdlm_domain_rollups (
  rollup_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord, tradition_view_id,
  domain, total_inbound_linkage, total_outbound_linkage, diagonal_density,
  signal_count_for_domain, top_3_linked_domains_jsonb, contradiction_density,
  pattern_markers_for_domain_array,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(rollup_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  NULL, NULL, NULL, NULL,
  %(domain)s, %(total_inbound_linkage)s, %(total_outbound_linkage)s, %(diagonal_density)s,
  %(signal_count_for_domain)s, %(top_3_linked_domains_jsonb)s::jsonb, %(contradiction_density)s,
  %(pattern_markers_for_domain_array)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
"""

_CLUSTER_INSERT = """
INSERT INTO bodha_cdlm_pattern_clusters (
  pattern_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord, tradition_view_id,
  pattern_marker_type, involved_domains_array, cluster_strength_total,
  involved_cells_array, involved_signals_array, contradicts_other_patterns_array,
  remedy_theme_jsonb, cgm_subgraph_cluster_seed, classical_archetype_match,
  predicted_outcome_class, active_dasha_windows_jsonb,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(pattern_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  NULL, NULL, NULL, NULL,
  %(pattern_marker_type)s, %(involved_domains_array)s, %(cluster_strength_total)s,
  %(involved_cells_array)s, %(involved_signals_array)s, NULL,
  NULL, NULL, NULL,
  %(predicted_outcome_class)s, NULL,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
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


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _write_aya(conn: Any, chart_id: str, aya: str, build_id: str, now: str) -> int:
    """Aggregate CDLM cells and write 1 summary row for one ayanamsha."""

    cells = _fetch_dict(
        conn,
        """SELECT domain_row, domain_col, computed_linkage_strength,
                  asymmetry_score AS contradiction_density, asymmetric_linkage_flag
           FROM bodha_cdlm_cells
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )

    if not cells:
        logger.info("[bo_cdlm_summary] %s — no CDLM cells found; skipping", aya)
        return 0

    # Aggregate
    total_linkage = 0.0
    contradiction_scores: list[float] = []
    domain_strength: dict[str, float] = defaultdict(float)
    asymmetric_count = 0
    strongest_strength = -1.0
    strongest_pair: dict = {}

    for cell in cells:
        strength = _safe_float(cell.get("computed_linkage_strength"))
        d_row = str(cell.get("domain_row", ""))
        d_col = str(cell.get("domain_col", ""))
        contradiction = _safe_float(cell.get("contradiction_density"))
        asymm_flag = cell.get("asymmetric_linkage_flag")

        total_linkage += strength

        # Domain connectivity — each domain gets credit from cells it participates in
        if d_row:
            domain_strength[d_row] += strength
        if d_col and d_col != d_row:
            domain_strength[d_col] += strength

        if contradiction is not None and contradiction > 0:
            contradiction_scores.append(contradiction)

        if asymm_flag:
            asymmetric_count += 1

        if strength > strongest_strength:
            strongest_strength = strength
            strongest_pair = {
                "domain_a": d_row,
                "domain_b": d_col,
                "strength": round(strength, 6),
            }

    avg_contradiction = (
        sum(contradiction_scores) / len(contradiction_scores)
        if contradiction_scores else 0.0
    )

    # Sort domains by strength
    sorted_domains = sorted(domain_strength.items(), key=lambda x: x[1], reverse=True)
    dominant_3 = [d for d, _ in sorted_domains[:3]]
    weakest_3  = [d for d, _ in sorted_domains[-3:]] if len(sorted_domains) >= 3 else [d for d, _ in sorted_domains]

    # Chart typology class: deterministic heuristic from linkage pattern
    total_domains = len(domain_strength)
    mean_strength = total_linkage / max(len(cells), 1)
    if total_domains <= 2:
        typology = "concentrated"
    elif mean_strength > 0.7:
        typology = "highly_connected"
    elif avg_contradiction > 0.3:
        typology = "contradictory"
    elif asymmetric_count > len(cells) * 0.4:
        typology = "asymmetric"
    else:
        typology = "distributed"

    domain_connectivity = {d: round(s, 6) for d, s in sorted_domains}
    pattern_markers = {
        "strongest_pair": strongest_pair,
        "total_cells": len(cells),
        "mean_cell_strength": round(mean_strength, 6),
    }

    row = {
        "summary_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "snapshot_type": SNAPSHOT_TYPE,
        "chart_typology_class": typology,
        "pattern_cluster_markers_jsonb": json.dumps(pattern_markers),
        "total_chart_linkage": round(total_linkage, 6),
        "contradiction_density": round(avg_contradiction, 6),
        "house_to_domain_strength_jsonb": json.dumps({}),     # house mapping not yet available at this layer
        "karaka_to_domain_strength_jsonb": json.dumps({}),    # karaka mapping populated in L4+
        "dominant_3_domains_array": dominant_3,
        "weakest_3_domains_array": weakest_3,
        "bridge_link_count": asymmetric_count,
        "asymmetric_link_count": asymmetric_count,
        # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
        # "pass" — an unconditional stamp with no verification logic behind it, and a
        # live false-green the serve layer counted as verified. Audited: nothing here
        # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
        "verification_pass_status": UNVERIFIED_DEFAULT,
        "citation_ref": "bo_cdlm_summary:aggregation_v1:bodha_cdlm_cells",
        "citation_human": "CDLM chart summary aggregated from bodha_cdlm_cells by bo_sangati",
        "computed_at": now,
    }

    with conn.cursor() as cur:
        cur.execute(_SUMMARY_INSERT, row)

    logger.info(
        "[bo_cdlm_summary] %s — summary written: total_linkage=%.3f typology=%s",
        aya, total_linkage, typology,
    )
    return 1


def _build_rollups(chart_id: str, aya: str, build_id: str,
                   cells: list[dict], now: str) -> list[dict]:
    """Per-domain rollup aggregated from CDLM cells (WP-2.2 / LCA-5).

    Cells are undirected pairs written with domain_row < domain_col (alphabetical).
    For a domain D we treat cells where D == domain_row as OUTBOUND and
    D == domain_col as INBOUND — a deterministic, stable convention over the
    symmetric matrix. diagonal_density = mean linkage over D's participating cells
    (self-cohesion proxy; no D×D diagonal cell exists at static-natal).
    """
    by_domain: dict[str, dict] = defaultdict(lambda: {
        "inbound": 0.0, "outbound": 0.0, "cells": 0,
        "partners": defaultdict(float), "signals": set(),
        "contradiction_cells": 0, "markers": set(),
    })
    for c in cells:
        d_row = str(c.get("domain_row", ""))
        d_col = str(c.get("domain_col", ""))
        strength = _safe_float(c.get("computed_linkage_strength"))
        sig_ids = c.get("shared_signal_ids_array") or []
        contradiction = bool(c.get("cross_domain_contradiction_flag"))
        rel = c.get("domain_relationship_class")
        for d, partner, direction in ((d_row, d_col, "outbound"), (d_col, d_row, "inbound")):
            if not d:
                continue
            agg = by_domain[d]
            agg[direction] += strength
            agg["cells"] += 1
            if partner:
                agg["partners"][partner] += strength
            for sid in sig_ids:
                agg["signals"].add(str(sid))
            if contradiction:
                agg["contradiction_cells"] += 1
            if rel:
                agg["markers"].add(str(rel))

    rows: list[dict] = []
    for domain, agg in sorted(by_domain.items()):
        n_cells = max(agg["cells"], 1)
        top3 = sorted(agg["partners"].items(), key=lambda x: x[1], reverse=True)[:3]
        rows.append({
            "rollup_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "domain": domain,
            "total_inbound_linkage": round(agg["inbound"], 6),
            "total_outbound_linkage": round(agg["outbound"], 6),
            "diagonal_density": round((agg["inbound"] + agg["outbound"]) / n_cells, 6),
            "signal_count_for_domain": len(agg["signals"]),
            "top_3_linked_domains_jsonb": json.dumps(
                [{"domain": d, "strength": round(s, 6)} for d, s in top3]),
            "contradiction_density": round(agg["contradiction_cells"] / n_cells, 6),
            "pattern_markers_for_domain_array": sorted(agg["markers"]) or None,
            # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
            # "pass" — an unconditional stamp with no verification logic behind it, and a
            # live false-green the serve layer counted as verified. Audited: nothing here
            # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "citation_ref": f"bo_cdlm_summary:domain_rollup_v1:bodha_cdlm_cells:{domain}",
            "citation_human": f"CDLM domain rollup for {domain} aggregated from bodha_cdlm_cells",
            "computed_at": now,
        })
    return rows


def _build_clusters(chart_id: str, aya: str, build_id: str,
                    cells: list[dict], now: str) -> list[dict]:
    """Group cells into pattern clusters by their domain_relationship_class.

    Each distinct relationship class present (positive_strong, inverse, …) becomes
    one cluster: the involved domains, member cell ids, and constituent MSR signal
    ids that produced that structural pattern. predicted_outcome_class maps the
    valence of the relationship class (harmonious vs tension) — deterministic, no
    time data (active_dasha_windows stays NULL, an L3 hook).
    """
    by_marker: dict[str, dict] = defaultdict(lambda: {
        "domains": set(), "cells": [], "signals": set(), "strength": 0.0,
    })
    for c in cells:
        rel = str(c.get("domain_relationship_class") or "unclassified")
        agg = by_marker[rel]
        agg["domains"].update(d for d in (c.get("domain_row"), c.get("domain_col")) if d)
        agg["cells"].append(str(c.get("cell_id")))
        for sid in (c.get("shared_signal_ids_array") or []):
            agg["signals"].add(str(sid))
        agg["strength"] += _safe_float(c.get("computed_linkage_strength"))

    rows: list[dict] = []
    for marker, agg in sorted(by_marker.items()):
        outcome = (
            "reinforcing" if marker.startswith("positive") else
            "conflicting" if marker in ("inverse", "neutral") else
            "mixed"
        )
        rows.append({
            "pattern_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "pattern_marker_type": f"{marker}_linkage_cluster",
            "involved_domains_array": sorted(agg["domains"]),
            "cluster_strength_total": round(agg["strength"], 6),
            "involved_cells_array": agg["cells"],
            "involved_signals_array": sorted(agg["signals"]),
            "predicted_outcome_class": outcome,
            # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 2): this was the literal
            # "pass" — an unconditional stamp with no verification logic behind it, and a
            # live false-green the serve layer counted as verified. Audited: nothing here
            # re-derives or cross-checks the row, so per §N.8 it is unverified, not green.
            "verification_pass_status": UNVERIFIED_DEFAULT,
            "citation_ref": f"bo_cdlm_summary:pattern_cluster_v1:bodha_cdlm_cells:{marker}",
            "citation_human": f"CDLM pattern cluster '{marker}' over {len(agg['cells'])} cells",
            "computed_at": now,
        })
    return rows


def _fetch_cells_full(conn: Any, chart_id: str, aya: str) -> list[dict]:
    return _fetch_dict(
        conn,
        """SELECT cell_id::text, domain_row, domain_col,
                  computed_linkage_strength, cross_domain_contradiction_flag,
                  domain_relationship_class, shared_signal_ids_array
           FROM bodha_cdlm_cells
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )


@register("bo_cdlm_summary")
class BoCdlmSummaryWriter(WriterBase):
    """bo_cdlm_summary: aggregates CDLM cell data into per-chart summary."""
    asset_id = "bo_cdlm_summary"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="dry_run — would aggregate bodha_cdlm_cells into 5 summary rows (1 per ayanamsha)",
            )

        # Idempotency: delete prior rows for this chart (all three sibling tables).
        with conn.cursor() as cur:
            # Disable per-statement timeout for the heavy DELETE on large charts.
            # SET LOCAL scopes to the orchestrator txn (writer never commits).
            # Ref: bo_laksana native-rebuild timeout; ka_* precedent (PR 422).
            cur.execute("SET LOCAL statement_timeout = 0")
            cur.execute("DELETE FROM bodha_cdlm_chart_summary WHERE chart_id = %s", [chart_id])
            cur.execute("DELETE FROM bodha_cdlm_domain_rollups WHERE chart_id = %s", [chart_id])
            cur.execute("DELETE FROM bodha_cdlm_pattern_clusters WHERE chart_id = %s", [chart_id])

        total = 0
        total_rollups = 0
        total_clusters = 0
        for aya in CANONICAL_AYAS:
            total += _write_aya(conn, chart_id, aya, build_id, now)

            # WP-2.2 / LCA-5: populate the previously-empty CDLM sibling tables.
            # Both are deterministic aggregations of bodha_cdlm_cells (same source
            # bo_sangati wrote). No time data is invented (B.10) — evolution_gradients
            # is intentionally NOT populated here: its dynamic_system_id is NOT NULL
            # and its peak/trough/predicted-next columns require L3 dasha-window data
            # unavailable at static-natal L2 (flagged §7.3 deferred, not fabricated).
            cells = _fetch_cells_full(conn, chart_id, aya)
            if not cells:
                continue
            rollups = _build_rollups(chart_id, aya, build_id, cells, now)
            clusters = _build_clusters(chart_id, aya, build_id, cells, now)
            with conn.cursor() as cur:
                for r in rollups:
                    cur.execute(_ROLLUP_INSERT, r)
                for c in clusters:
                    cur.execute(_CLUSTER_INSERT, c)
            total_rollups += len(rollups)
            total_clusters += len(clusters)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total + total_rollups + total_clusters,
            notes=(f"cdlm_summary_rows={total} domain_rollups={total_rollups} "
                   f"pattern_clusters={total_clusters} "
                   f"(evolution_gradients deferred §7.3 — needs L3 temporal data)"),
        )
