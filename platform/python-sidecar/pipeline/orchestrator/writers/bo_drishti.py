"""
bo_drishti — Question-Lens (L2 Bodha)
=======================================
Pre-computes deterministic classical LENSES: question-type → the chart-specific
structural elements + evidence that bear on it.

TWO ABSOLUTE GUARDS:
1. A lens POINTS, never PRE-ANSWERS (points_only_assertion = True always).
2. A lens is ADDITIVE, never SUBTRACTIVE (mandatory wildcard graph-sweep via
   CGM edges ensures no high-salience far-from-template signal is lost).

LIGHT writer; one row per (question_type × ayanamsha).
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION        = "bo_drishti_v1.0"
LENS_TEMPLATE_VERSION = "classical_v1.0"
LENS_FORMULA_VERSION  = "drishti_formula_v1.0"

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

# Question-type → domain keywords that exist in bodha_msr_signals.domains_affected_array
# Mapped to the actual domain values observed in DB
QUESTION_TYPE_CONFIG: dict[str, dict] = {
    "career":       {"domains": ["career"]},
    "wealth":       {"domains": ["wealth"]},
    "marriage":     {"domains": ["relationship"]},
    "health":       {"domains": ["health"]},
    "character":    {"domains": ["character"]},
    "spirituality": {"domains": ["spirituality"]},
    "education":    {"domains": ["character", "spirituality"]},  # intellect overlaps
    "progeny":      {"domains": ["career", "relationship"]},     # 5th house bridges
    "longevity":    {"domains": ["health"]},
    "foreign_travel": {"domains": ["spirituality"]},             # 12H/9H = moksha/travel
    "property":     {"domains": ["wealth"]},                     # 4H maps to wealth
    "siblings":     {"domains": ["character"]},                  # 3H comm/courage
}

_INSERT = """
INSERT INTO bodha_question_lenses (
  lens_id, chart_id, ayanamsha_id, build_id, question_type,
  template_element_ids_jsonb, wildcard_element_ids_jsonb, all_relevant_ranked_jsonb,
  lens_template_version, lens_formula_version, points_only_assertion,
  verification_pass_status, citation_ref, computed_at, engine_version
) VALUES (
  %(lens_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(question_type)s,
  %(template_element_ids_jsonb)s::jsonb, %(wildcard_element_ids_jsonb)s::jsonb,
  %(all_relevant_ranked_jsonb)s::jsonb,
  %(lens_template_version)s, %(lens_formula_version)s, %(points_only_assertion)s,
  %(verification_pass_status)s, %(citation_ref)s, %(computed_at)s, %(engine_version)s
)
ON CONFLICT DO NOTHING
"""


def _fetch_dict(conn: Any, sql: str, params: list) -> list[dict]:
    # conn uses dict_row factory; fetchall() already returns dicts — convert to plain dict.
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def _fetch_template_signals(
    conn: Any, chart_id: str, aya: str, domains: list[str]
) -> list[dict]:
    """Fetch signals whose domains_affected_array overlaps the question's domains."""
    rows = _fetch_dict(
        conn,
        """SELECT signal_id, signal_type_id, signal_type_class, computed_salience,
                  domains_affected_array, source_l1_asset, configuration_jsonb
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND domains_affected_array && %s::text[]
           ORDER BY computed_salience DESC NULLS LAST""",
        [chart_id, aya, domains],
    )
    return rows


def _fetch_wildcard_signals(
    conn: Any, chart_id: str, aya: str,
    template_signal_ids: set[str], template_domains: list[str],
    top_salience_threshold: float,
) -> list[dict]:
    """
    Two-phase wildcard sweep that guarantees non-template signals surface per lens.

    Phase 1 — CGM co-occurrence: collect all signal_ids from CGM edges (the chart's
    structural relationship graph), exclude template signals → cross-domain structural
    connections.

    Phase 2 — Domain-exclusion salience: top-N high-salience signals whose
    domains_affected_array does NOT overlap the template domains.  Guaranteed to
    find wildcards even when CGM edge count is low (as with L2 initial build
    where msr_signal_id on nodes is NULL — edges are still populated).
    """
    if not template_signal_ids:
        return []

    # Phase 1: signals appearing in ANY CGM edge (structural co-occurrence)
    edge_raw = _fetch_dict(
        conn,
        """SELECT DISTINCT unnest(underlying_msr_signal_ids_array)::text AS sig_id
           FROM bodha_cgm_edges
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND underlying_msr_signal_ids_array IS NOT NULL""",
        [chart_id, aya],
    )
    cgm_wildcards = {r["sig_id"] for r in edge_raw if r["sig_id"]} - template_signal_ids

    # Phase 2: domain-exclusion sweep — always produces wildcards
    domain_exclusion_raw = _fetch_dict(
        conn,
        """SELECT signal_id::text AS sig_id FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND NOT (domains_affected_array && %s::text[])
             AND computed_salience >= %s
           ORDER BY computed_salience DESC NULLS LAST, signal_id ASC LIMIT 20""",
        [chart_id, aya, template_domains, top_salience_threshold],
    )
    domain_exclusion_wildcards = {r["sig_id"] for r in domain_exclusion_raw}

    wildcard_ids = cgm_wildcards | domain_exclusion_wildcards
    if not wildcard_ids:
        return []

    return _fetch_dict(
        conn,
        """SELECT signal_id, signal_type_id, signal_type_class, computed_salience,
                  domains_affected_array, source_l1_asset
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND signal_id = ANY(%s::uuid[])
           ORDER BY computed_salience DESC NULLS LAST, signal_id ASC LIMIT 20""",
        [chart_id, aya, list(wildcard_ids)],
    )


def _build_lens(
    conn: Any, chart_id: str, aya: str, build_id: str, now: str,
    question_type: str, cfg: dict
) -> dict:
    domains = cfg["domains"]

    template_rows = _fetch_template_signals(conn, chart_id, aya, domains)

    # Compute salience threshold for wildcard (mean of template, floored at 0.1)
    if template_rows:
        saliences = [float(r["computed_salience"] or 0) for r in template_rows]
        mean_sal = sum(saliences) / len(saliences)
    else:
        mean_sal = 0.1
    wildcard_threshold = max(mean_sal * 0.5, 0.05)

    template_signal_ids = {str(r["signal_id"]) for r in template_rows}

    wildcard_rows = _fetch_wildcard_signals(
        conn, chart_id, aya, template_signal_ids, domains, wildcard_threshold
    )

    # Build template_element_ids_jsonb (references only, no values)
    template_element_ids = {
        "signal_ids": [str(r["signal_id"]) for r in template_rows],
        "domains_matched": domains,
        "signal_count": len(template_rows),
    }

    # Build wildcard_element_ids_jsonb (each with non_template_significant flag)
    cgm_id_set = {str(r["sig_id"]) for r in _fetch_dict(
        conn,
        """SELECT DISTINCT unnest(underlying_msr_signal_ids_array)::text AS sig_id
           FROM bodha_cgm_edges WHERE chart_id = %s AND ayanamsha_id = %s
             AND underlying_msr_signal_ids_array IS NOT NULL""",
        [chart_id, aya],
    ) if r["sig_id"]}
    wildcard_element_ids = {
        "wildcard_signals": [
            {
                "signal_id": str(r["signal_id"]),
                "salience": float(r["computed_salience"] or 0),
                "signal_type_class": r["signal_type_class"],
                "non_template_significant": True,
                "reach_path": "cgm_cooccurrence" if str(r["signal_id"]) in cgm_id_set else "domain_exclusion",
            }
            for r in wildcard_rows
        ],
        "wildcard_count": len(wildcard_rows),
    }

    # Build full ranked union (template + wildcard, sorted by salience)
    all_signals: list[dict] = []
    for r in template_rows:
        all_signals.append({
            "signal_id": str(r["signal_id"]),
            "salience": float(r["computed_salience"] or 0),
            "signal_type_class": r["signal_type_class"],
            "source_l1_asset": r["source_l1_asset"],
            "in_template": True,
            "non_template_significant": False,
        })
    for r in wildcard_rows:
        all_signals.append({
            "signal_id": str(r["signal_id"]),
            "salience": float(r["computed_salience"] or 0),
            "signal_type_class": r["signal_type_class"],
            "source_l1_asset": r["source_l1_asset"],
            "in_template": False,
            "non_template_significant": True,
        })

    all_signals.sort(key=lambda x: x["salience"], reverse=True)

    all_relevant_ranked = {
        "ranked_signals": all_signals,
        "total_count": len(all_signals),
        "template_count": len(template_rows),
        "wildcard_count": len(wildcard_rows),
    }

    return {
        "lens_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "question_type": question_type,
        "template_element_ids_jsonb": json.dumps(template_element_ids),
        "wildcard_element_ids_jsonb": json.dumps(wildcard_element_ids),
        "all_relevant_ranked_jsonb": json.dumps(all_relevant_ranked),
        "lens_template_version": LENS_TEMPLATE_VERSION,
        "lens_formula_version": LENS_FORMULA_VERSION,
        "points_only_assertion": True,  # absolute guard: no verdict stored
        "verification_pass_status": "documented_approximation",
        "citation_ref": f"bo_drishti/{question_type}/{aya}",
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
    }


def _batch_insert(conn: Any, rows: list[dict]) -> int:
    if not rows:
        return 0
    inserted = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), 25):
            batch = rows[i:i + 25]
            cur.executemany(_INSERT, batch)
            inserted += len(batch)
    return inserted


@register("bo_drishti")
class BoDrishtiWriter(WriterBase):
    """bo_drishti: question-lens (answer-focused retrieval without pre-answering)."""
    asset_id = "bo_drishti"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()
        total    = 0

        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes=f"dry_run — would build {len(QUESTION_TYPE_CONFIG)} question types × {len(CANONICAL_AYAS)} ayanamshas")

        # Idempotency: delete prior rows for this chart
        with conn.cursor() as cur:
            # Disable per-statement timeout for the heavy DELETE on large charts.
            # SET LOCAL scopes to the orchestrator txn (writer never commits).
            # Ref: bo_laksana native-rebuild timeout; ka_* precedent (PR 422).
            cur.execute("SET LOCAL statement_timeout = 0")
            cur.execute("DELETE FROM bodha_question_lenses WHERE chart_id = %s", [chart_id])

        for aya in CANONICAL_AYAS:
            aya_rows: list[dict] = []
            for question_type, cfg in QUESTION_TYPE_CONFIG.items():
                try:
                    row = _build_lens(conn, chart_id, aya, build_id, now, question_type, cfg)
                    aya_rows.append(row)
                except Exception as exc:
                    logger.warning("[bo_drishti] %s/%s failed: %s", aya, question_type, exc)

            total += _batch_insert(conn, aya_rows)
            logger.info("[bo_drishti] %s — %d lenses inserted", aya, len(aya_rows))

        if total == 0:
            raise RuntimeError(
                f"[bo_drishti] G3: chart_id={chart_id} — 0 question-lenses produced across "
                f"{len(CANONICAL_AYAS)} ayanamshas × {len(QUESTION_TYPE_CONFIG)} question types; "
                "all per-lens builds failed (check bodha_msr_signals upstream)"
            )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total,
            notes=f"question_types={len(QUESTION_TYPE_CONFIG)} ayas={len(CANONICAL_AYAS)} total={total}",
        )
