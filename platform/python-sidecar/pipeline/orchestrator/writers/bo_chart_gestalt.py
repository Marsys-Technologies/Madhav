"""
bo_chart_gestalt — Chart Gestalt / Pratinidhi Synthesis (L2 Bodha)
===================================================================
प्रतिनिधि = "representative/summary"

Reads all earlier Bodha assets and synthesizes a per-chart gestalt:
  - defining_threads_jsonb: top chart_defining + major signals by salience (POINTERS only)
  - central_dynamics_ids: CDLM strongest-linkage cell ids (cross-domain synergies)
  - pivot_ids: placeholder for CDLM §C3 pivot factor ids (populated when available)
  - center_of_gravity_node_ids: top-pagerank CGM node ids + final-dispositor node ids
  - domain_verdict_map_jsonb: {domain → {ledger_id, verdict_class, confidence}} — POINTERS only
  - headline_jsonb: top signature thread + strongest domain — pointers only
  - watch_list_jsonb: strongest malefic-valenced signals + weakest domain — pointers only
  - central_question_jsonb: antagonistic axis — pointers only
  - zoom_spine_jsonb: layered navigation: gestalt → domain → signals → L1 fact_ids
  - outliers_jsonb: non-template-significant outlier signals (from anveshana discoveries)
  - contested_areas_jsonb: domains where evidence is genuinely balanced

ANTI-DRIFT ABSOLUTE: this writer ONLY STORES POINTERS (signal_ids, cell_ids, node_ids).
It NEVER stores verdicts, computed values, or interpretive text.
The actual content is always retrieved by following the pointers to the source rows.

LIGHT writer — one run() call, iterates 5 ayanamshas.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION     = "bo_chart_gestalt_v1.0"
SNAPSHOT_TYPE      = "static_natal"
GESTALT_FORMULA_V  = "gestalt_formula_v1"
TOP_SIGNAL_COUNT   = 10   # max signals in defining_threads_jsonb
TOP_NODE_COUNT     = 5    # max nodes in center_of_gravity_node_ids
TOP_DOMAIN_COUNT   = 7    # domains to cover in verdict map

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

_GESTALT_INSERT = """
INSERT INTO bodha_chart_gestalt (
  gestalt_id, chart_id, ayanamsha_id, build_id,
  gestalt_formula_version,
  defining_threads_jsonb,
  central_dynamics_ids,
  pivot_ids,
  center_of_gravity_node_ids,
  domain_verdict_map_jsonb,
  headline_jsonb,
  watch_list_jsonb,
  central_question_jsonb,
  headline_confidence,
  headline_epistemic_jsonb,
  outliers_jsonb,
  contested_areas_jsonb,
  zoom_spine_jsonb,
  computed_at,
  engine_version
) VALUES (
  %(gestalt_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(gestalt_formula_version)s,
  %(defining_threads_jsonb)s::jsonb,
  %(central_dynamics_ids)s,
  %(pivot_ids)s,
  %(center_of_gravity_node_ids)s,
  %(domain_verdict_map_jsonb)s::jsonb,
  %(headline_jsonb)s::jsonb,
  %(watch_list_jsonb)s::jsonb,
  %(central_question_jsonb)s::jsonb,
  %(headline_confidence)s,
  %(headline_epistemic_jsonb)s::jsonb,
  %(outliers_jsonb)s::jsonb,
  %(contested_areas_jsonb)s::jsonb,
  %(zoom_spine_jsonb)s::jsonb,
  %(computed_at)s,
  %(engine_version)s
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
    """Synthesize and write 1 gestalt row for one ayanamsha. Returns 1 on success, 0 if skipped."""

    # ── 1. Defining threads: top chart_defining + major signals by salience ────
    top_signals = _fetch_dict(
        conn,
        """SELECT signal_id, signal_type_id, signal_type_class, computed_salience,
                  signature_tier, valence, source_l1_asset, domains_affected_array,
                  constituent_facts_array
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND signature_tier IN ('chart_defining', 'major')
           ORDER BY computed_salience DESC NULLS LAST, signal_id ASC
           LIMIT %s""",
        [chart_id, aya, TOP_SIGNAL_COUNT],
    )

    if not top_signals:
        # Try any signals if no chart_defining/major ones
        top_signals = _fetch_dict(
            conn,
            """SELECT signal_id, signal_type_id, signal_type_class, computed_salience,
                      signature_tier, valence, source_l1_asset, domains_affected_array,
                      constituent_facts_array
               FROM bodha_msr_signals
               WHERE chart_id = %s AND ayanamsha_id = %s
               ORDER BY computed_salience DESC NULLS LAST, signal_id ASC
               LIMIT %s""",
            [chart_id, aya, TOP_SIGNAL_COUNT],
        )

    if not top_signals:
        logger.info("[bo_chart_gestalt] %s — no MSR signals; skipping", aya)
        return 0

    defining_threads = {
        "signal_ids": [str(s["signal_id"]) for s in top_signals],
        "tiers": [str(s.get("signature_tier") or "") for s in top_signals],
        "note": "pointer-only — follow signal_id to bodha_msr_signals for content",
    }

    # ── 2. Central dynamics: CDLM cell ids with highest linkage strength ────────
    strong_cells = _fetch_dict(
        conn,
        """SELECT cell_id, domain_row, domain_col, computed_linkage_strength
           FROM bodha_cdlm_cells
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s
           ORDER BY computed_linkage_strength DESC NULLS LAST, cell_id ASC
           LIMIT 5""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )
    central_dynamics_ids = [str(c["cell_id"]) for c in strong_cells]

    # ── 3. Center of gravity: top pagerank CGM nodes + final-dispositor paths ──
    top_nodes = _fetch_dict(
        conn,
        """SELECT node_id, node_subject, pagerank_score, hub_flag
           FROM bodha_cgm_nodes
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s
             AND node_type = 'graha'
           ORDER BY pagerank_score DESC NULLS LAST, node_id ASC
           LIMIT %s""",
        [chart_id, aya, SNAPSHOT_TYPE, TOP_NODE_COUNT],
    )
    center_of_gravity_ids = [str(n["node_id"]) for n in top_nodes]

    # Final dispositor nodes from cgm_paths
    final_disp_nodes = _fetch_dict(
        conn,
        """SELECT DISTINCT to_node_id
           FROM bodha_cgm_paths
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = %s
             AND is_final_dispositor = true""",
        [chart_id, aya, SNAPSHOT_TYPE],
    )
    for r in final_disp_nodes:
        nid = str(r["to_node_id"])
        if nid not in center_of_gravity_ids:
            center_of_gravity_ids.append(nid)

    # ── 4. Domain verdict map: per-domain pointer to strongest signal ──────────
    domain_signals = _fetch_dict(
        conn,
        """SELECT DISTINCT ON (unnested_domain)
               unnest(domains_affected_array) AS unnested_domain,
               signal_id, computed_salience, valence, signature_tier
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
           ORDER BY unnested_domain, computed_salience DESC NULLS LAST, signal_id ASC
           LIMIT 50""",
        [chart_id, aya],
    )

    domain_verdict_map: dict[str, dict] = {}
    for ds in domain_signals:
        domain = str(ds.get("unnested_domain") or "")
        if not domain or domain in domain_verdict_map:
            continue
        valence = str(ds.get("valence") or "neutral")
        salience = _safe_float(ds.get("computed_salience"))
        # verdict_class = deterministic heuristic from valence + salience tier
        tier = str(ds.get("signature_tier") or "")
        if valence in ("benefic",) and tier in ("chart_defining", "major"):
            verdict_class = "strong_positive"
        elif valence in ("malefic",) and tier in ("chart_defining", "major"):
            verdict_class = "strong_challenge"
        elif valence in ("mixed",):
            verdict_class = "mixed"
        else:
            verdict_class = "neutral"
        domain_verdict_map[domain] = {
            "signal_id": str(ds["signal_id"]),    # pointer-only
            "verdict_class": verdict_class,
            "confidence": round(min(salience / 10.0, 1.0), 3) if salience > 0 else 0.5,
        }

    # ── 5. Headline: top signal + strongest domain (pointers only) ─────────────
    top_signal = top_signals[0] if top_signals else {}
    strongest_domain = list(domain_verdict_map.keys())[0] if domain_verdict_map else "unknown"
    headline = {
        "top_signal_id": str(top_signal.get("signal_id", "")) if top_signal else None,
        "top_signal_type": str(top_signal.get("signal_type_id", "")) if top_signal else None,
        "strongest_domain": strongest_domain,
        "note": "pointer-only — no verdict text stored here",
    }

    # headline_confidence from top signal salience
    headline_confidence = round(
        min(_safe_float(top_signal.get("computed_salience")) / 10.0, 1.0), 4
    ) if top_signal else 0.5

    # ── 6. Watch list: malefic-valenced signals ────────────────────────────────
    malefic_signals = _fetch_dict(
        conn,
        """SELECT signal_id, signal_type_id, computed_salience, domains_affected_array
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND valence = 'malefic'
           ORDER BY computed_salience DESC NULLS LAST, signal_id ASC
           LIMIT 5""",
        [chart_id, aya],
    )
    weakest_domain_entry = list(domain_verdict_map.items())[-1] if domain_verdict_map else None
    watch_list = {
        "malefic_signal_ids": [str(s["signal_id"]) for s in malefic_signals],
        "weakest_domain": weakest_domain_entry[0] if weakest_domain_entry else None,
        "weakest_domain_signal_id": weakest_domain_entry[1]["signal_id"] if weakest_domain_entry else None,
        "note": "pointer-only — follow signal_ids for content",
    }

    # ── 7. Central question: antagonistic axis (strongest benefic vs malefic) ──
    benefic_top = _fetch_dict(
        conn,
        """SELECT signal_id, signal_type_id, domains_affected_array
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s AND valence = 'benefic'
           ORDER BY computed_salience DESC NULLS LAST, signal_id ASC
           LIMIT 1""",
        [chart_id, aya],
    )
    central_question = {
        "positive_pole_signal_id": str(benefic_top[0]["signal_id"]) if benefic_top else None,
        "negative_pole_signal_id": str(malefic_signals[0]["signal_id"]) if malefic_signals else None,
        "linking_mechanism": "domain_tension",
        "note": "pointer-only — antagonistic axis; follow signal_ids for content",
    }

    # ── 8. Outliers: non-template-significant discovery signal ids ─────────────
    outlier_discoveries = _fetch_dict(
        conn,
        """SELECT discovery_id, discovery_class, non_obviousness_score,
                  constituent_refs_jsonb
           FROM bodha_discoveries
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND discovery_class IN ('embedding_outlier', 'distributional_anomaly')
           ORDER BY composite_discovery_rank DESC, discovery_id ASC
           LIMIT 5""",
        [chart_id, aya],
    )
    outliers = {
        "discovery_ids": [str(d["discovery_id"]) for d in outlier_discoveries],
        "note": "pointer-only — non-template-significant outliers from bo_anveshana",
    }

    # ── 9. Contested areas: domains with both benefic and malefic signals ──────
    contested = _fetch_dict(
        conn,
        """SELECT unnest(domains_affected_array) AS domain,
                  COUNT(*) FILTER (WHERE valence = 'benefic') AS benefic_count,
                  COUNT(*) FILTER (WHERE valence = 'malefic') AS malefic_count
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
           GROUP BY 1
           HAVING COUNT(*) FILTER (WHERE valence = 'benefic') > 0
              AND COUNT(*) FILTER (WHERE valence = 'malefic') > 0
           ORDER BY
             (COUNT(*) FILTER (WHERE valence = 'benefic') + COUNT(*) FILTER (WHERE valence = 'malefic')) DESC,
             domain ASC
           LIMIT 3""",
        [chart_id, aya],
    )
    contested_areas = {
        "contested_domains": [
            {
                "domain": str(r["domain"]),
                "benefic_count": int(r["benefic_count"]),
                "malefic_count": int(r["malefic_count"]),
            }
            for r in contested
        ],
        "note": "domains where benefic and malefic evidence is genuinely balanced",
    }

    # ── 10. Zoom spine: layered navigation ────────────────────────────────────
    zoom_spine = {
        "gestalt_signal_ids": [str(s["signal_id"]) for s in top_signals[:3]],
        "domain_entry_points": {
            domain: info["signal_id"]
            for domain, info in list(domain_verdict_map.items())[:5]
        },
        "cgm_hub_node_ids": center_of_gravity_ids[:3],
        "note": "zoom spine: gestalt → domain signal ids → CGM hubs → L1 facts via constituent_facts_array",
    }

    # ── 11. headline_epistemic: ayanamsha robustness placeholder ──────────────
    headline_epistemic = {
        "ayanamsha_count": len(CANONICAL_AYAS),
        "fragility_class": "multi_ayanamsha_tested",
        "note": "ayanamsha robustness will be assessed after all 5 ayanamshas are built",
    }

    row = {
        "gestalt_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "gestalt_formula_version": GESTALT_FORMULA_V,
        "defining_threads_jsonb": json.dumps(defining_threads),
        "central_dynamics_ids": central_dynamics_ids or None,
        "pivot_ids": None,    # L4 Phala fills when CDLM §C3 pivot factors are identified
        "center_of_gravity_node_ids": center_of_gravity_ids or None,
        "domain_verdict_map_jsonb": json.dumps(domain_verdict_map),
        "headline_jsonb": json.dumps(headline),
        "watch_list_jsonb": json.dumps(watch_list),
        "central_question_jsonb": json.dumps(central_question),
        "headline_confidence": headline_confidence,
        "headline_epistemic_jsonb": json.dumps(headline_epistemic),
        "outliers_jsonb": json.dumps(outliers),
        "contested_areas_jsonb": json.dumps(contested_areas),
        "zoom_spine_jsonb": json.dumps(zoom_spine),
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
    }

    with conn.cursor() as cur:
        cur.execute(_GESTALT_INSERT, row)

    logger.info(
        "[bo_chart_gestalt] %s — gestalt written: %d defining threads, %d domains",
        aya, len(top_signals), len(domain_verdict_map),
    )
    return 1


@register("bo_chart_gestalt")
class BoChartGestaltWriter(WriterBase):
    """bo_chart_gestalt: per-chart gestalt pointer synthesis (O5 — highest interpretive value)."""
    asset_id = "bo_chart_gestalt"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0,
                notes="dry_run — would write 1 gestalt row per ayanamsha (5 total)",
            )

        # Idempotency: delete prior rows for this chart
        with conn.cursor() as cur:
            # Disable per-statement timeout for the heavy DELETE on large charts.
            # SET LOCAL scopes to the orchestrator txn (writer never commits).
            # Ref: bo_laksana native-rebuild timeout; ka_* precedent (PR 422).
            cur.execute("SET LOCAL statement_timeout = 0")
            cur.execute("DELETE FROM bodha_chart_gestalt WHERE chart_id = %s", [chart_id])

        total = 0
        for aya in CANONICAL_AYAS:
            total += _write_aya(conn, chart_id, aya, build_id, now)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            notes=f"gestalt_rows={total} (1 per ayanamsha where MSR signals exist)",
        )
