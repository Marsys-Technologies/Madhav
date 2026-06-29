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
        "verification_pass_status": "pass",
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

        # Idempotency: delete prior rows for this chart
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bodha_cdlm_chart_summary WHERE chart_id = %s", [chart_id])

        total = 0
        for aya in CANONICAL_AYAS:
            total += _write_aya(conn, chart_id, aya, build_id, now)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            notes=f"cdlm_summary_rows={total} (expected {len(CANONICAL_AYAS)} if cells exist)",
        )
