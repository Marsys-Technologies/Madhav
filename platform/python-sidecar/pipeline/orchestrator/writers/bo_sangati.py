"""
bo_sangati — Cross-Domain Linkage Matrix + Convergence (L2 Bodha)
=================================================================
Reads bodha_msr_signals → writes:
  - bodha_cdlm_cells     (one row per domain-pair that shares ≥1 signal)
  - bodha_convergence    (one row per domain: how many signals converge per domain)

Cross-domain linkage algorithm:
  For each pair (domain_A, domain_B) where A ≤ B (alphabetical):
    - shared_signals = signals whose domains_affected_array contains BOTH A and B
    - If shared_signal_count > 0: write a bodha_cdlm_cells row

Convergence algorithm (per domain):
  For each domain:
    - convergence_count = number of signals with that domain
    - convergence_score = computed via convergence_formula_v1
    - cross_tradition_count = distinct traditions in those signals

SPARSITY NOTE: Row count varies per chart (depends on how many domain pairs co-occur
in that chart's MSR signals). 100 rows for chart 482012f1-... is expected and correct.
Sparse charts with few cross-domain signals will produce fewer rows. This is by design.

LIGHT writer — one run() call.
"""
from __future__ import annotations

import json
import logging
import math
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from itertools import combinations

from . import WriterBase, ContextSpec, WriterResult, register
from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS, CANONICAL_DOMAINS_SORTED

logger = logging.getLogger(__name__)

ENGINE_VERSION   = "bo_sangati_v1.0"
SNAPSHOT_TYPE    = "static_natal"
CANONICAL_AYAS   = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

# G13/PA-4 (R17): local 7-domain KNOWN_DOMAINS deleted; import canonical 13-domain
# vocabulary from brahmagyan.domain_vocabulary (the L0 SSoT).
# KNOWN_DOMAINS was: ["career", "wealth", "health", "relationship",
#                     "spirituality", "character", "general"]
# Now: CANONICAL_DOMAINS (frozenset of 13) — all writers operate over the full set.
# Use CANONICAL_DOMAINS_SORTED for deterministic iteration (same as combinations()).
_KNOWN_DOMAINS = CANONICAL_DOMAINS  # module-local alias for clarity; not re-exported

_CDLM_INSERT = """
INSERT INTO bodha_cdlm_cells (
  cell_id, chart_id, ayanamsha_id, build_id,
  snapshot_type, dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord,
  dynamic_window_start_iso, dynamic_window_end_iso, tradition_view_id,
  domain_row, domain_col, subdomain_row, subdomain_col,
  shared_signal_count, shared_factor_count, unique_signals_row_domain, unique_signals_col_domain,
  shared_signal_salience_sum, shared_signal_max_salience,
  positive_contribution, negative_contribution, net_linkage_strength, computed_linkage_strength,
  linkage_formula_version,
  contradicting_signal_pairs_count, contradicting_signal_pairs_jsonb, cross_domain_contradiction_flag,
  shared_factor_keys_jsonb, shared_signal_ids_array, shared_signals_by_tradition_jsonb,
  shared_signals_high_convergence_count, recurring_pattern_markers_array,
  cross_ayanamsha_cell_stability_score, top_k_rank_in_snapshot,
  asymmetric_linkage_flag, asymmetry_score,
  cgm_subgraph_cluster_id, cgm_bridge_edge_seeds_jsonb, cgm_domain_super_node_strength_contribution_jsonb, cgm_antagonist_edge_seeds_jsonb,
  cell_remedy_priority_rank, weakest_constituent_graha_jsonb, pattern_remedy_theme_jsonb, cell_remedy_hooks_array,
  dominant_linkage_rank_in_chart, domain_relationship_class, narrative_thread_seed,
  predicted_activation_dasha_windows_jsonb, cell_evolution_gradient_score,
  channel_render_priority_jsonb, phase_aligned_pattern_marker,
  msr_salience_version_used, verification_pass_status, citation_ref, citation_human,
  computed_at, engine_version
) VALUES (
  %(cell_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
  %(snapshot_type)s, NULL, NULL, NULL, NULL, NULL, NULL,
  %(domain_row)s, %(domain_col)s, NULL, NULL,
  %(shared_signal_count)s, %(shared_factor_count)s, %(unique_signals_row_domain)s, %(unique_signals_col_domain)s,
  %(shared_signal_salience_sum)s, %(shared_signal_max_salience)s,
  %(positive_contribution)s, %(negative_contribution)s, %(net_linkage_strength)s, %(computed_linkage_strength)s,
  %(linkage_formula_version)s,
  %(contradicting_signal_pairs_count)s, NULL, %(cross_domain_contradiction_flag)s,
  NULL, %(shared_signal_ids_array)s, %(shared_signals_by_tradition_jsonb)s::jsonb,
  NULL, NULL,
  NULL, %(top_k_rank_in_snapshot)s,
  FALSE, NULL,
  NULL, NULL, NULL, NULL,
  NULL, NULL, NULL, NULL,
  NULL, NULL, NULL,
  NULL, NULL,
  NULL, NULL,
  %(msr_salience_version_used)s, %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s,
  %(computed_at)s, %(engine_version)s
)
"""

_CONVERGENCE_INSERT = """
INSERT INTO bodha_convergence (
  convergence_id, chart_id, ayanamsha_id, build_id, domain, snapshot_type,
  dynamic_system_id, dynamic_maha_lord, dynamic_antar_lord,
  convergence_count, convergence_score, convergence_formula_version,
  cross_tradition_count, top_signal_ids_array, tradition_breakdown_jsonb,
  salience_weighted_sum, salience_max, contradiction_count,
  verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(convergence_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(domain)s, %(snapshot_type)s,
  NULL, NULL, NULL,
  %(convergence_count)s, %(convergence_score)s, %(convergence_formula_version)s,
  %(cross_tradition_count)s, %(top_signal_ids_array)s, %(tradition_breakdown_jsonb)s::jsonb,
  %(salience_weighted_sum)s, %(salience_max)s, %(contradiction_count)s,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
"""

_BATCH_SIZE = 50

# BA-P3B EXT ──────────────────────────────────────────────────────────────────
_TRIANGULATION_INSERT = """
INSERT INTO bodha_triangulation (
    triangulation_id, chart_id, ayanamsha_id, build_id,
    question_class, tradition,
    verdict_inputs, concordance_score, signal_ids,
    formula_version, computed_at, engine_version
) VALUES (
    %(triangulation_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
    %(question_class)s, %(tradition)s,
    %(verdict_inputs)s::jsonb, %(concordance_score)s, %(signal_ids)s,
    %(formula_version)s, %(computed_at)s, %(engine_version)s
)
ON CONFLICT (chart_id, ayanamsha_id, question_class, tradition)
DO UPDATE SET
    verdict_inputs      = EXCLUDED.verdict_inputs,
    concordance_score   = EXCLUDED.concordance_score,
    signal_ids          = EXCLUDED.signal_ids,
    computed_at         = EXCLUDED.computed_at,
    engine_version      = EXCLUDED.engine_version
"""

_TRIANGULATION_TRADITIONS = ("parashari", "jaimini", "kp", "tajika")
_TRIANGULATION_FORMULA    = "v1.0"


def _build_triangulation_rows(
    chart_id: str, aya: str, build_id: str,
    signals: list[dict], now: str,
) -> list[dict]:
    """Per (domain × tradition) concordance: mean salience of top-5 signals."""
    rows: list[dict] = []
    for domain in CANONICAL_DOMAINS_SORTED:
        for trad in _TRIANGULATION_TRADITIONS:
            trad_sigs = [
                s for s in signals
                if str(s.get("signal_tradition") or "").lower() == trad
                and domain in (s.get("domains_affected_array") or [])
            ]
            if not trad_sigs:
                continue
            trad_sigs.sort(
                key=lambda s: float(s.get("computed_salience") or 0.0), reverse=True
            )
            top5      = trad_sigs[:5]
            top5_sal  = [float(s.get("computed_salience") or 0.0) for s in top5]
            concordance = round(sum(top5_sal) / len(top5_sal), 6) if top5_sal else 0.0
            sig_ids   = [str(s.get("signal_id") or "") for s in trad_sigs]
            rows.append({
                "triangulation_id": str(uuid.uuid4()),
                "chart_id":         chart_id,
                "ayanamsha_id":     aya,
                "build_id":         build_id,
                "question_class":   domain,
                "tradition":        trad,
                "verdict_inputs":   json.dumps({
                    "domain": domain, "tradition": trad,
                    "signal_count": len(trad_sigs),
                    "top5_saliences": top5_sal,
                }),
                "concordance_score": concordance,
                "signal_ids":       sig_ids or None,
                "formula_version":  _TRIANGULATION_FORMULA,
                "computed_at":      now,
                "engine_version":   ENGINE_VERSION,
            })
    return rows


def _fetch_dict(conn, sql: str, params: list) -> list[dict]:
    # conn uses dict_row factory; fetchall() already returns dicts — convert to plain dict.
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def _fetch_signals(conn, chart_id: str, aya: str) -> list[dict]:
    return _fetch_dict(conn, """
        SELECT signal_id::text, signal_type_class, signal_tradition, domains_affected_array,
               computed_salience, verification_pass_status, salience_formula_version,
               signal_type_id
        FROM bodha_msr_signals
        WHERE chart_id = %s AND ayanamsha_id = %s
    """, [chart_id, aya])


def _fetch_contradiction_domains(conn, chart_id: str, aya: str) -> set[str]:
    """Returns set of domains that appear in bodha_contradictions rows (may be empty)."""
    try:
        rows = _fetch_dict(conn, """
            SELECT domains_affected_array FROM bodha_contradictions
            WHERE chart_id = %s AND ayanamsha_id = %s
        """, [chart_id, aya])
    except Exception:
        return set()
    result: set[str] = set()
    for r in rows:
        arr = r.get("domains_affected_array") or []
        if arr:
            result.update(arr)
    return result


def _build_cdlm_cells(
    chart_id: str, aya: str, build_id: str,
    signals: list[dict], contradiction_domains: set[str], now: str
) -> list[dict]:
    """Build CDLM cells: one row per (domain_row, domain_col) pair with shared signals."""
    from bodha_writers.formulas import LinkageInputs, linkage_formula_v1

    # Group signals by domain
    domain_signals: dict[str, list[dict]] = defaultdict(list)
    for sig in signals:
        for d in (sig.get("domains_affected_array") or []):
            if d in _KNOWN_DOMAINS:
                domain_signals[d].append(sig)

    cells: list[dict] = []

    # For each ordered pair (A, B) where A < B (alphabetically)
    # G13/PA-4: operate over all 13 canonical domains (was 7).
    all_pairs = list(combinations(CANONICAL_DOMAINS_SORTED, 2))
    ranked_cells: list[tuple[float, dict]] = []

    for domain_a, domain_b in all_pairs:
        sigs_a = set(str(s.get("signal_id")) for s in domain_signals.get(domain_a, []))
        sigs_b = set(str(s.get("signal_id")) for s in domain_signals.get(domain_b, []))
        shared_ids = sigs_a & sigs_b
        if not shared_ids:
            continue

        shared_sigs = [s for s in signals if str(s.get("signal_id")) in shared_ids]
        saliencies  = [float(s.get("computed_salience") or 0.0) for s in shared_sigs]
        sal_sum     = sum(saliencies)
        sal_max     = max(saliencies) if saliencies else 0.0

        # Tradition breakdown
        tradition_breakdown: dict[str, int] = defaultdict(int)
        for s in shared_sigs:
            t = str(s.get("signal_tradition") or "parashari")
            tradition_breakdown[t] += 1

        # Linkage formula (positive/negative derived internally from in_contradiction flag)
        high_conv_count = sum(1 for s in shared_sigs if float(s.get("computed_salience") or 0.0) >= 0.6)
        lf_inputs = LinkageInputs(
            shared_signals=[{"salience": float(s.get("computed_salience") or 0.0),
                             "in_contradiction": s.get("signal_type_class") == "dosha"}
                            for s in shared_sigs],
            high_convergence_count=high_conv_count,
            shared_factor_count=len(shared_ids),
        )
        lf_result = linkage_formula_v1(lf_inputs)
        computed_strength = float(lf_result["computed_linkage_strength"])
        positive = float(lf_result["positive_contribution"])
        negative = float(lf_result["negative_contribution"])
        net      = float(lf_result["net_linkage_strength"])

        contradiction_flag = (domain_a in contradiction_domains and domain_b in contradiction_domains)

        cell = {
            "cell_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "domain_row": domain_a,
            "domain_col": domain_b,
            "shared_signal_count": len(shared_ids),
            "shared_factor_count": len(shared_ids),
            "unique_signals_row_domain": len(sigs_a),
            "unique_signals_col_domain": len(sigs_b),
            "shared_signal_salience_sum": round(sal_sum, 6),
            "shared_signal_max_salience": round(sal_max, 6),
            "positive_contribution": round(positive, 6),
            "negative_contribution": round(negative, 6),
            "net_linkage_strength": round(net, 6),
            "computed_linkage_strength": round(computed_strength, 6),
            "domain_relationship_class": (
                "positive_strong" if net >= 2000 else
                "positive_moderate" if net >= 500 else
                "positive_weak" if net > 0 else
                "neutral" if net == 0 else
                "inverse"
            ),
            "linkage_formula_version": lf_result["linkage_formula_version"],
            "contradicting_signal_pairs_count": 1 if contradiction_flag else 0,
            "cross_domain_contradiction_flag": contradiction_flag,
            "shared_signal_ids_array": sorted(shared_ids),
            "shared_signals_by_tradition_jsonb": json.dumps(dict(tradition_breakdown)),
            "top_k_rank_in_snapshot": None,  # set after ranking
            "msr_salience_version_used": (shared_sigs[0].get("salience_formula_version") or "v1.0") if shared_sigs else "v1.0",
            "verification_pass_status": "documented_approximation",
            "citation_ref": f"bo_sangati/cdlm/{domain_a}_{domain_b}",
            "citation_human": f"CDLM cell: {domain_a}×{domain_b}, {len(shared_ids)} shared signals",
            "computed_at": now,
            "engine_version": ENGINE_VERSION,
        }
        ranked_cells.append((computed_strength, cell))

    # Rank by linkage strength descending
    ranked_cells.sort(key=lambda x: x[0], reverse=True)
    for rank, (_, cell) in enumerate(ranked_cells, start=1):
        cell["top_k_rank_in_snapshot"] = rank

    return [c for _, c in ranked_cells]


def _build_convergence_rows(
    chart_id: str, aya: str, build_id: str,
    signals: list[dict], contradiction_domains: set[str], now: str
) -> list[dict]:
    from bodha_writers.formulas import ConvergenceInputs, convergence_formula_v1

    domain_signals: dict[str, list[dict]] = defaultdict(list)
    for sig in signals:
        for d in (sig.get("domains_affected_array") or []):
            if d in _KNOWN_DOMAINS:
                domain_signals[d].append(sig)

    rows: list[dict] = []
    # G13/PA-4: iterate over all 13 canonical domains (was 7).
    for domain in CANONICAL_DOMAINS_SORTED:
        sigs = domain_signals.get(domain, [])
        if not sigs:
            continue

        saliencies = [float(s.get("computed_salience") or 0.0) for s in sigs]
        sal_sum    = sum(saliencies)
        sal_max    = max(saliencies) if saliencies else 0.0
        traditions = {str(s.get("signal_tradition") or "parashari") for s in sigs}
        tradition_breakdown = defaultdict(int)
        for s in sigs:
            tradition_breakdown[str(s.get("signal_tradition") or "parashari")] += 1

        # Top 5 by salience
        sorted_sigs = sorted(sigs, key=lambda s: float(s.get("computed_salience") or 0.0), reverse=True)
        top_ids = [str(s.get("signal_id")) for s in sorted_sigs[:5]]

        c_inputs = ConvergenceInputs(
            domain=domain,
            signal_saliencies=saliencies,
            signal_traditions=[str(s.get("signal_tradition") or "parashari") for s in sigs],
            contradiction_count=1 if domain in contradiction_domains else 0,
        )
        c_result = convergence_formula_v1(c_inputs)
        conv_score = float(c_result["convergence_score"])

        rows.append({
            "convergence_id": str(uuid.uuid4()),
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "domain": domain,
            "snapshot_type": SNAPSHOT_TYPE,
            "convergence_count": len(sigs),
            "convergence_score": round(conv_score, 6),
            "convergence_formula_version": c_result["convergence_formula_version"],
            "cross_tradition_count": int(c_result["cross_tradition_count"]),
            "top_signal_ids_array": top_ids,
            "tradition_breakdown_jsonb": json.dumps(dict(tradition_breakdown)),
            "salience_weighted_sum": round(sal_sum, 6),
            "salience_max": round(sal_max, 6),
            "contradiction_count": 1 if domain in contradiction_domains else 0,
            "verification_pass_status": "documented_approximation",
            "citation_ref": f"bo_sangati/convergence/{domain}",
            "citation_human": f"Convergence: {domain} — {len(sigs)} signals",
            "computed_at": now,
        })

    return rows


def _batch_insert(conn, rows: list[dict], sql: str) -> int:
    inserted = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), _BATCH_SIZE):
            batch = rows[i:i + _BATCH_SIZE]
            cur.executemany(sql, batch)
            inserted += len(batch)
    return inserted


@register("bo_sangati")
class BoSangatiWriter(WriterBase):
    """bo_sangati: Cross-Domain Linkage Matrix + Convergence density."""
    asset_id = "bo_sangati"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import (
            replace_prior_cdlm_cells, replace_prior_convergence,
        )

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()
        total_cells  = 0
        total_conv   = 0
        total_triang = 0

        # Disable per-statement timeout for the heavy DELETEs below (incl. the
        # inline bodha_triangulation delete in the per-ayanamsha loop). One
        # SET LOCAL persists to txn end and scopes to the orchestrator txn
        # (writer never commits). Ref: bo_laksana native-rebuild timeout;
        # ka_* precedent (PR 422).
        conn.execute("SET LOCAL statement_timeout = 0")

        for aya in CANONICAL_AYAS:
            signals = _fetch_signals(conn, chart_id, aya)
            contradiction_domains = _fetch_contradiction_domains(conn, chart_id, aya)

            if ctx.dry_run:
                logger.info("[bo_sangati dry_run] %s — %d signals", aya, len(signals))
                continue

            cells = _build_cdlm_cells(chart_id, aya, build_id, signals, contradiction_domains, now)
            conv  = _build_convergence_rows(chart_id, aya, build_id, signals, contradiction_domains, now)

            replace_prior_cdlm_cells(conn, chart_id, aya, SNAPSHOT_TYPE)
            replace_prior_convergence(conn, chart_id, aya, SNAPSHOT_TYPE)

            logger.info("[bo_sangati] %s — %d CDLM cells, %d convergence rows", aya, len(cells), len(conv))
            total_cells += _batch_insert(conn, cells, _CDLM_INSERT)
            total_conv  += _batch_insert(conn, conv,  _CONVERGENCE_INSERT)

            # BA-P3B EXT: write bodha_triangulation rows (multi-tradition concordance)
            triang = _build_triangulation_rows(chart_id, aya, build_id, signals, now)
            conn.execute(
                "DELETE FROM bodha_triangulation WHERE chart_id=%s AND ayanamsha_id=%s",
                [chart_id, aya],
            )
            for row in triang:
                conn.execute(_TRIANGULATION_INSERT, row)
            total_triang += len(triang)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total_cells + total_conv + total_triang,
                            notes=f"cdlm_cells={total_cells} convergence={total_conv} triangulation={total_triang}")
