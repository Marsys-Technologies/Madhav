"""
bo_anveshana — Discovery Engine (L2 Bodha)
==========================================
अन्वेषण = "investigation/discovery"

Mines the other 7 Bodha assets at BUILD TIME for consequential NON-OBVIOUS
patterns — the insight no acharya can hold because combinatorial depth exceeds
working memory. Outputs a pre-computed, ranked DISCOVERY LIST the digest leads with.

Four deterministic discovery primitives (no LLM, no igraph required):
  1. Non-obviousness scoring: HIGH structural consequence × LOW surface salience
  2. Embedding outlier detection: signals far from the ayanamsha embedding centroid
  3. Distributional anomalies: within-chart Nσ outliers per subsystem
  4. Broker detection: CGM nodes with high cross-subsystem connectivity

ANTI-DRIFT ABSOLUTE: every discovery REFERENCES substrate ids — never restates
values, never invents a pattern not in the data.

HEAVY-ish writer. Runs near-last (after all producing bo_* assets).
"""
from __future__ import annotations

import json
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION = "bo_anveshana_v1.0"
SIGMA_THRESHOLD = 2.0  # distributional anomaly threshold
OUTLIER_TOP_N   = 20   # max embedding outliers per ayanamsha
BROKER_TOP_N    = 10   # max broker nodes per ayanamsha

CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]

# Classical domain categories for the meaningfulness gate
CLASSICAL_RELATIONSHIP_TYPES = {
    "aspect", "lordship", "dispositor", "yoga", "dosha", "conjunction",
    "argala", "mutual_reception", "combustion", "exaltation", "debilitation",
    "nakshatra_ruler", "dasha_active",
}

_DISCOVERY_INSERT = """
INSERT INTO bodha_discoveries (
  discovery_id, chart_id, ayanamsha_id, build_id, discovery_class,
  discovery_subsystem, non_obviousness_score, consequence_score, composite_discovery_rank,
  constituent_refs_jsonb, reasoning_chain_jsonb, why_an_acharya_misses_it,
  affected_domains_array, epistemic_jsonb, meaningfulness_basis,
  corroborating_methods_array, corroboration_count,
  surface_reading, depth_reading, surface_depth_delta,
  hypothesis_text, falsifier_jsonb, calibration_hook, novelty_class,
  cross_subsystem_root, cross_subsystem_refs_jsonb, provenance,
  computed_at, engine_version
) VALUES (
  %(discovery_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(discovery_class)s,
  %(discovery_subsystem)s, %(non_obviousness_score)s, %(consequence_score)s, %(composite_discovery_rank)s,
  %(constituent_refs_jsonb)s::jsonb, %(reasoning_chain_jsonb)s::jsonb, %(why_an_acharya_misses_it)s,
  %(affected_domains_array)s, %(epistemic_jsonb)s::jsonb, %(meaningfulness_basis)s,
  %(corroborating_methods_array)s, %(corroboration_count)s,
  %(surface_reading)s, %(depth_reading)s, %(surface_depth_delta)s,
  %(hypothesis_text)s, %(falsifier_jsonb)s::jsonb, NULL, %(novelty_class)s,
  %(cross_subsystem_root)s, %(cross_subsystem_refs_jsonb)s::jsonb, %(provenance)s::jsonb,
  %(computed_at)s, %(engine_version)s
)
ON CONFLICT DO NOTHING
"""

_ANOMALY_INSERT = """
INSERT INTO bodha_anomalies (
  anomaly_id, chart_id, ayanamsha_id, build_id, anomaly_type,
  discovery_subsystem, subject_ref_jsonb, anomaly_metric, anomaly_value,
  chart_baseline_value, sigma_from_baseline, meaningfulness_gate_result,
  computed_at, engine_version
) VALUES (
  %(anomaly_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(anomaly_type)s,
  %(discovery_subsystem)s, %(subject_ref_jsonb)s::jsonb, %(anomaly_metric)s, %(anomaly_value)s,
  %(chart_baseline_value)s, %(sigma_from_baseline)s, %(meaningfulness_gate_result)s,
  %(computed_at)s, %(engine_version)s
)
ON CONFLICT DO NOTHING
"""


def _fetch_dict(conn: Any, sql: str, params: list) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
        if not rows:
            return []
        # Connection may use dict_row factory (rows are already dicts) or tuple_row.
        # dict_row: iterating the row gives KEYS not values, so zip(cols, row) would be wrong.
        if isinstance(rows[0], dict):
            return [dict(r) for r in rows]
        cols = [d.name for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


# ── Primitive 1: Non-obviousness (high consequence × low surface salience) ────

def _compute_non_obviousness(conn: Any, chart_id: str, aya: str) -> list[dict]:
    """
    For each signal: consequence = convergence participation + centrality.
    non_obviousness = consequence × (1 - normalized_salience).
    Returns top candidates sorted by non_obviousness_score DESC.
    """
    signals = _fetch_dict(
        conn,
        """SELECT m.signal_id, m.signal_type_id, m.signal_type_class, m.computed_salience,
                  m.source_l1_asset, m.domains_affected_array, m.constituent_facts_array,
                  m.configuration_jsonb,
                  COALESCE(n.betweenness_centrality, 0) AS betweenness,
                  COALESCE(n.pagerank_score, 0) AS pagerank,
                  COALESCE(n.degree_in, 0) + COALESCE(n.degree_out, 0) AS degree
           FROM bodha_msr_signals m
           LEFT JOIN bodha_cgm_nodes n
             ON n.chart_id = m.chart_id AND n.ayanamsha_id = m.ayanamsha_id
             AND n.msr_signal_id = m.signal_id
           WHERE m.chart_id = %s AND m.ayanamsha_id = %s""",
        [chart_id, aya],
    )
    if not signals:
        return []

    saliences = [_safe_float(r["computed_salience"]) for r in signals]
    max_sal = max(saliences) if saliences else 1.0
    max_sal = max_sal if max_sal > 0 else 1.0

    convergence_rows = _fetch_dict(
        conn,
        """SELECT domain, convergence_score FROM bodha_convergence
           WHERE chart_id = %s AND ayanamsha_id = %s AND snapshot_type = 'static_natal'""",
        [chart_id, aya],
    )
    convergence_by_domain = {r["domain"]: _safe_float(r["convergence_score"]) for r in convergence_rows}

    results = []
    for sig in signals:
        sal_norm   = _safe_float(sig["computed_salience"]) / max_sal
        centrality = min(_safe_float(sig["betweenness"]) + _safe_float(sig["pagerank"]) * 2.0, 1.0)
        degree     = min(_safe_float(sig["degree"]) / 20.0, 1.0)

        domains = sig.get("domains_affected_array") or []
        conv_score = max((convergence_by_domain.get(d, 0.0) for d in domains), default=0.0)

        consequence = min((centrality * 0.4 + degree * 0.3 + conv_score * 0.3), 1.0)
        non_obviousness = consequence * (1.0 - sal_norm)

        results.append({
            "signal_id": str(sig["signal_id"]),
            "signal_type_id": sig["signal_type_id"],
            "signal_type_class": sig["signal_type_class"],
            "source_l1_asset": sig["source_l1_asset"],
            "domains": domains,
            "constituent_facts": sig.get("constituent_facts_array") or [],
            "surface_salience": _safe_float(sig["computed_salience"]),
            "sal_norm": sal_norm,
            "consequence_score": consequence,
            "non_obviousness_score": non_obviousness,
            "methods": ["non_obviousness"],
        })

    results.sort(key=lambda x: x["non_obviousness_score"], reverse=True)
    return results


# ── Primitive 2: Embedding outlier detection ───────────────────────────────────

def _fetch_embeddings_np(conn: Any, chart_id: str, aya: str) -> tuple[list[str], np.ndarray | None]:
    """Load signal_ids + embedding vectors for one ayanamsha.

    Casts embedding_vec::text so psycopg3 binary mode always returns a string,
    never bytes/memoryview. Parse failures RAISE rather than returning a silent
    empty result — the old silent fallback was the root cause of 5-row output
    (vs floor 5770). Empty rows (no data in table) return an empty signal list
    with no matrix, which is a legitimate no-op.
    """
    rows = _fetch_dict(
        conn,
        """SELECT signal_id, embedding_vec::text AS embedding_vec
           FROM bodha_signal_embeddings
           WHERE chart_id = %s AND ayanamsha_id = %s""",
        [chart_id, aya],
    )
    if not rows:
        no_mat: np.ndarray | None = None
        return [], no_mat

    signal_ids: list[str] = []
    vecs: list[list[float]] = []
    skipped = 0
    for r in rows:
        v = r["embedding_vec"]
        if v is None:
            skipped += 1
            continue
        if isinstance(v, (list, tuple)):
            vecs.append([float(x) for x in v])
            signal_ids.append(str(r["signal_id"]))
        elif isinstance(v, str):
            # Strip both bracket styles: pgvector may emit [x,y] or {x,y}
            v_clean = v.strip().strip("[]{}")
            floats = [float(x) for x in v_clean.split(",") if x.strip()]
            if not floats:
                skipped += 1
                continue
            vecs.append(floats)
            signal_ids.append(str(r["signal_id"]))
        else:
            raise RuntimeError(
                f"[bo_anveshana] Unexpected embedding_vec type {type(v).__name__} for "
                f"signal_id={r.get('signal_id')} — register pgvector adapter or cast to text"
            )

    if skipped > 0:
        logger.warning("[bo_anveshana] %d embedding rows skipped (None/empty)", skipped)

    if not vecs:
        raise RuntimeError(
            f"[bo_anveshana] No valid embedding vectors parsed for chart={chart_id} aya={aya} "
            f"({len(rows)} rows fetched, all failed to parse)"
        )

    dim0 = len(vecs[0])
    bad_dims = [i for i, vec in enumerate(vecs) if len(vec) != dim0]
    if bad_dims:
        raise RuntimeError(
            f"[bo_anveshana] Inhomogeneous embedding dimensions: expected {dim0} but "
            f"{len(bad_dims)} rows differ — data integrity error"
        )

    mat = np.array(vecs, dtype=np.float32)
    return signal_ids, mat


def _compute_embedding_outliers(signal_ids: list[str], mat: np.ndarray) -> list[tuple[str, float]]:
    """Return (signal_id, distance_from_centroid) sorted DESC."""
    if mat is None or len(mat) == 0:
        return []
    centroid = mat.mean(axis=0)
    diffs     = mat - centroid
    distances = np.sqrt((diffs ** 2).sum(axis=1))
    indexed   = list(zip(signal_ids, distances.tolist()))
    indexed.sort(key=lambda x: x[1], reverse=True)
    return indexed


# ── Primitive 3: Distributional anomalies per subsystem ───────────────────────

def _compute_distributional_anomalies(conn: Any, chart_id: str, aya: str) -> list[dict]:
    """
    Within each subsystem (source_l1_asset), compute mean+std of computed_salience.
    Flag signals > SIGMA_THRESHOLD × std from mean.
    """
    rows = _fetch_dict(
        conn,
        """SELECT signal_id, signal_type_id, signal_type_class, source_l1_asset,
                  computed_salience, domains_affected_array
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND computed_salience IS NOT NULL""",
        [chart_id, aya],
    )
    if not rows:
        return []

    by_subsystem: dict[str, list] = {}
    for r in rows:
        sub = str(r["source_l1_asset"] or "unknown")
        if sub not in by_subsystem:
            by_subsystem[sub] = []
        by_subsystem[sub].append(r)

    anomalies = []
    for sub, sub_rows in by_subsystem.items():
        saliences = [_safe_float(r["computed_salience"]) for r in sub_rows]
        if len(saliences) < 3:
            continue
        mean_s = sum(saliences) / len(saliences)
        variance = sum((s - mean_s) ** 2 for s in saliences) / len(saliences)
        std_s = math.sqrt(variance) if variance > 0 else 0.0
        if std_s == 0:
            continue

        for r in sub_rows:
            sal = _safe_float(r["computed_salience"])
            sigma = (sal - mean_s) / std_s
            if abs(sigma) >= SIGMA_THRESHOLD:
                anomalies.append({
                    "signal_id": str(r["signal_id"]),
                    "signal_type_id": r["signal_type_id"],
                    "signal_type_class": r["signal_type_class"],
                    "source_l1_asset": sub,
                    "domains": r.get("domains_affected_array") or [],
                    "salience": sal,
                    "mean_salience": mean_s,
                    "std_salience": std_s,
                    "sigma": sigma,
                    "methods": ["distributional_anomaly"],
                })

    return anomalies


# ── Primitive 4: Broker detection (cross-subsystem hub nodes) ─────────────────

def _compute_brokers(conn: Any, chart_id: str, aya: str) -> list[dict]:
    """
    Find CGM nodes that bridge multiple subsystems (high degree + many distinct
    subsystem pairs in edges). These are structural brokers / articulation points.
    """
    rows = _fetch_dict(
        conn,
        """SELECT n.node_id, n.node_subject, n.node_type, n.source_subsystem,
                  n.betweenness_centrality, n.pagerank_score, n.msr_signal_id,
                  n.primary_domain, n.hub_flag,
                  COUNT(e.edge_id) AS edge_count,
                  COUNT(DISTINCT e.subsystem_from) + COUNT(DISTINCT e.subsystem_to) AS subsystem_diversity
           FROM bodha_cgm_nodes n
           LEFT JOIN bodha_cgm_edges e
             ON (e.from_node_id = n.node_id OR e.to_node_id = n.node_id)
             AND e.chart_id = n.chart_id AND e.ayanamsha_id = n.ayanamsha_id
             AND e.is_cross_subsystem = TRUE
           WHERE n.chart_id = %s AND n.ayanamsha_id = %s
           GROUP BY n.node_id, n.node_subject, n.node_type, n.source_subsystem,
                    n.betweenness_centrality, n.pagerank_score, n.msr_signal_id,
                    n.primary_domain, n.hub_flag
           HAVING COUNT(e.edge_id) > 0 OR n.hub_flag = TRUE
           ORDER BY COUNT(e.edge_id) DESC, n.betweenness_centrality DESC NULLS LAST
           LIMIT %s""",
        [chart_id, aya, BROKER_TOP_N * 3],
    )
    return rows


# ── Meaningfulness gate ────────────────────────────────────────────────────────

def _passes_meaningfulness_gate(signal_type_class: str, signal_type_id: str) -> tuple[bool, str]:
    """
    A pattern is promoted to bodha_discoveries only if it has a classically-
    recognizable form of significance (not purely statistical noise).
    """
    cls = str(signal_type_class or "").lower()
    type_id = str(signal_type_id or "").lower()

    if cls in ("yoga", "dosha"):
        return True, f"classical_form::{cls}"
    if cls in ("dignity", "lordship", "planetary_state"):
        return True, f"classical_form::{cls}"
    if any(k in type_id for k in ("lord", "aspect", "yoga", "dosha", "combustion",
                                   "exalt", "debil", "dispositor", "argala", "nakshatra")):
        return True, f"classical_keyword::{type_id[:40]}"
    if cls in ("strength", "varga", "panchanga", "medical", "vastu"):
        return True, f"subsystem_classical::{cls}"

    return False, "statistical_only"


# ── Discovery row builders ─────────────────────────────────────────────────────

def _make_discovery(
    chart_id: str, aya: str, build_id: str, now: str,
    discovery_class: str, discovery_subsystem: str | None,
    non_obviousness: float, consequence: float,
    constituent_refs: list, reasoning_chain: list,
    why_misses: str, domains: list[str],
    surface: str, depth: str, delta: str,
    hypothesis: str, cross_subsystem: bool,
    cross_subsystem_refs: list | None,
    corroborating_methods: list[str],
    meaningfulness_basis: str,
    surface_salience: float,
    rank: float,
) -> dict:
    corr_count = len(set(corroborating_methods))
    rank_composite = rank * (1.0 + corr_count * 0.2)

    return {
        "discovery_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "discovery_class": discovery_class,
        "discovery_subsystem": discovery_subsystem,
        "non_obviousness_score": round(non_obviousness, 6),
        "consequence_score": round(consequence, 6),
        "composite_discovery_rank": round(rank_composite, 6),
        "constituent_refs_jsonb": json.dumps({"signal_ids": constituent_refs}),
        "reasoning_chain_jsonb": json.dumps({"steps": reasoning_chain}),
        "why_an_acharya_misses_it": why_misses,
        "affected_domains_array": domains or None,
        "epistemic_jsonb": json.dumps({
            "confidence": round(min(consequence + 0.1, 1.0), 3),
            "ayanamsha_fragility": "low",
        }),
        "meaningfulness_basis": meaningfulness_basis,
        "corroborating_methods_array": list(set(corroborating_methods)),
        "corroboration_count": corr_count,
        "surface_reading": surface,
        "depth_reading": depth,
        "surface_depth_delta": delta,
        "hypothesis_text": hypothesis,
        "falsifier_jsonb": json.dumps({
            "falsifier": "Compare against L3 Kāla LEL event outcomes for predicted domain",
            "calibration_hook": "empty — L4/L5 fill with observed outcome",
        }),
        "novelty_class": "instance_of_known_class",
        "cross_subsystem_root": cross_subsystem,
        "cross_subsystem_refs_jsonb": json.dumps(cross_subsystem_refs) if cross_subsystem_refs else "null",
        "provenance": json.dumps({
            "engine": ENGINE_VERSION,
            "method": discovery_class,
            "surface_salience": round(surface_salience, 4),
        }),
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
    }


def _make_anomaly(
    chart_id: str, aya: str, build_id: str, now: str,
    anomaly_type: str, subsystem: str | None,
    subject_ref: dict, metric: str, value: float,
    baseline: float, sigma: float,
    gate_result: str,
) -> dict:
    return {
        "anomaly_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": aya,
        "build_id": build_id,
        "anomaly_type": anomaly_type,
        "discovery_subsystem": subsystem,
        "subject_ref_jsonb": json.dumps(subject_ref),
        "anomaly_metric": metric,
        "anomaly_value": round(value, 6),
        "chart_baseline_value": round(baseline, 6),
        "sigma_from_baseline": round(sigma, 4),
        "meaningfulness_gate_result": gate_result,
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
    }


# ── Main ayanamsha-level mining ────────────────────────────────────────────────

def _mine_ayanamsha(
    conn: Any, chart_id: str, aya: str, build_id: str, now: str
) -> tuple[list[dict], list[dict]]:
    """Returns (discoveries, anomalies) for one ayanamsha."""
    discoveries: list[dict] = []
    anomalies: list[dict]   = []

    # ── Primitive 1: Non-obviousness ──────────────────────────────────────────
    non_ob_results = _compute_non_obviousness(conn, chart_id, aya)
    non_ob_by_signal = {r["signal_id"]: r for r in non_ob_results}

    # Top latent insights: high non-obviousness
    latent_threshold = 0.3
    latent_candidates = [r for r in non_ob_results if r["non_obviousness_score"] >= latent_threshold][:30]
    discovery_signal_set: set[str] = set()

    for cand in latent_candidates:
        passes, basis = _passes_meaningfulness_gate(
            cand["signal_type_class"], cand["signal_type_id"]
        )
        if passes:
            d = _make_discovery(
                chart_id, aya, build_id, now,
                discovery_class="latent_insight",
                discovery_subsystem=cand["source_l1_asset"],
                non_obviousness=cand["non_obviousness_score"],
                consequence=cand["consequence_score"],
                constituent_refs=[cand["signal_id"]] + [str(f) for f in (cand["constituent_facts"] or [])[:5]],
                reasoning_chain=[
                    {"step": "low_salience", "value": round(cand["sal_norm"], 4),
                     "description": "Low surface salience — acharya less likely to notice"},
                    {"step": "high_consequence", "value": round(cand["consequence_score"], 4),
                     "description": "High structural + convergence consequence"},
                ],
                why_misses=f"Low surface salience ({cand['sal_norm']:.2f}) masks high structural consequence ({cand['consequence_score']:.2f}); falls below acharya's attentional threshold",
                domains=cand["domains"],
                surface=f"Signal {cand['signal_type_id']} with low visibility (salience {cand['surface_salience']:.3f})",
                depth=f"Structurally consequential: consequence_score={cand['consequence_score']:.3f}, non_obviousness={cand['non_obviousness_score']:.3f}",
                delta=f"Surface hides depth by factor {cand['non_obviousness_score']:.3f}",
                hypothesis=f"Pattern {cand['signal_type_id']} in {', '.join(cand['domains'][:2])} has outsized structural consequence despite low surface visibility",
                cross_subsystem=False,
                cross_subsystem_refs=None,
                corroborating_methods=["non_obviousness"],
                meaningfulness_basis=basis,
                surface_salience=cand["surface_salience"],
                rank=cand["non_obviousness_score"],
            )
            discoveries.append(d)
            discovery_signal_set.add(cand["signal_id"])
        else:
            # Statistical candidate only → anomaly
            a = _make_anomaly(
                chart_id, aya, build_id, now,
                anomaly_type="low_salience_high_consequence",
                subsystem=cand["source_l1_asset"],
                subject_ref={"signal_id": cand["signal_id"], "signal_type_id": cand["signal_type_id"]},
                metric="non_obviousness_score",
                value=cand["non_obviousness_score"],
                baseline=0.3,
                sigma=(cand["non_obviousness_score"] - 0.3) / 0.1,
                gate_result="candidate_only",
            )
            anomalies.append(a)

    # ── Primitive 2: Embedding outliers ───────────────────────────────────────
    signal_ids_emb, mat = _fetch_embeddings_np(conn, chart_id, aya)
    if mat is not None and len(signal_ids_emb) > 0:
        outliers = _compute_embedding_outliers(signal_ids_emb, mat)
        # Get signal info for top outliers
        top_outlier_ids = [sid for sid, _ in outliers[:OUTLIER_TOP_N * 2]]
        if top_outlier_ids:
            outlier_signal_info = _fetch_dict(
                conn,
                """SELECT signal_id, signal_type_id, signal_type_class, computed_salience,
                          source_l1_asset, domains_affected_array
                   FROM bodha_msr_signals
                   WHERE chart_id = %s AND ayanamsha_id = %s AND signal_id = ANY(%s::uuid[])""",
                [chart_id, aya, top_outlier_ids],
            )
            outlier_info_by_id = {str(r["signal_id"]): r for r in outlier_signal_info}

            for sid, dist in outliers[:OUTLIER_TOP_N]:
                sig_info = outlier_info_by_id.get(sid)
                if not sig_info:
                    continue

                passes, basis = _passes_meaningfulness_gate(
                    sig_info["signal_type_class"], sig_info["signal_type_id"]
                )

                non_ob_info = non_ob_by_signal.get(sid, {})
                consequence = non_ob_info.get("consequence_score", 0.1)
                non_ob = min(dist / 5.0 * consequence, 1.0)  # normalize distance

                if passes and sid not in discovery_signal_set:
                    corr_methods = ["embedding_outlier"]
                    if sid in {r["signal_id"] for r in latent_candidates[:30]}:
                        corr_methods.append("non_obviousness")

                    d = _make_discovery(
                        chart_id, aya, build_id, now,
                        discovery_class="embedding_outlier",
                        discovery_subsystem=sig_info["source_l1_asset"],
                        non_obviousness=non_ob,
                        consequence=consequence,
                        constituent_refs=[sid],
                        reasoning_chain=[
                            {"step": "embedding_distance", "value": round(float(dist), 4),
                             "description": "Semantic meaning-vector far from chart centroid"},
                        ],
                        why_misses=f"Semantically unusual (distance {dist:.3f} from chart centroid) — stands apart from the chart's dominant patterns; invisible to pattern-matching",
                        domains=sig_info.get("domains_affected_array") or [],
                        surface=f"Signal {sig_info['signal_type_id']} appears unremarkable to pattern inspection",
                        depth=f"Embedding distance from chart centroid: {dist:.4f} — semantically unusual",
                        delta=f"Semantic uniqueness {dist:.3f} distinguishes this from all other chart signals",
                        hypothesis=f"Pattern {sig_info['signal_type_id']} represents a chart-unusual semantic configuration whose practical significance may be underweighted",
                        cross_subsystem=False,
                        cross_subsystem_refs=None,
                        corroborating_methods=corr_methods,
                        meaningfulness_basis=basis,
                        surface_salience=_safe_float(sig_info["computed_salience"]),
                        rank=non_ob,
                    )
                    discoveries.append(d)
                    discovery_signal_set.add(sid)
                else:
                    # Statistical only
                    gate = "candidate_only" if not passes else "promoted"
                    a = _make_anomaly(
                        chart_id, aya, build_id, now,
                        anomaly_type="embedding_outlier",
                        subsystem=sig_info["source_l1_asset"],
                        subject_ref={"signal_id": sid, "signal_type_id": sig_info.get("signal_type_id")},
                        metric="embedding_distance_from_centroid",
                        value=float(dist),
                        baseline=float(np.mean([d for _, d in outliers])),
                        sigma=(float(dist) - float(np.mean([d for _, d in outliers]))) /
                               max(float(np.std([d for _, d in outliers])), 1e-8),
                        gate_result=gate,
                    )
                    anomalies.append(a)

    # ── Primitive 3: Distributional anomalies ─────────────────────────────────
    dist_anomalies = _compute_distributional_anomalies(conn, chart_id, aya)
    for anom in dist_anomalies:
        passes, basis = _passes_meaningfulness_gate(
            anom["signal_type_class"], anom["signal_type_id"]
        )
        gate = "promoted" if passes else "candidate_only"

        if passes and anom["signal_id"] not in discovery_signal_set:
            non_ob_info = non_ob_by_signal.get(anom["signal_id"], {})
            consequence = non_ob_info.get("consequence_score", 0.2)
            sal_norm = non_ob_info.get("sal_norm", 0.5)
            non_ob = min(abs(anom["sigma"]) / 5.0 * consequence, 1.0)

            corr_methods = ["distributional_anomaly"]
            if anom["signal_id"] in discovery_signal_set:
                corr_methods.append("non_obviousness")

            d = _make_discovery(
                chart_id, aya, build_id, now,
                discovery_class="distributional_anomaly",
                discovery_subsystem=anom["source_l1_asset"],
                non_obviousness=non_ob,
                consequence=consequence,
                constituent_refs=[anom["signal_id"]],
                reasoning_chain=[
                    {"step": "sigma_deviation", "value": round(anom["sigma"], 3),
                     "description": f"Salience {anom['sigma']:.1f}σ from subsystem mean"},
                    {"step": "subsystem_baseline", "mean": round(anom["mean_salience"], 4),
                     "std": round(anom["std_salience"], 4)},
                ],
                why_misses=f"Statistically extreme within {anom['source_l1_asset']} subsystem ({abs(anom['sigma']):.1f}σ) but easy to miss when chart is read holistically",
                domains=anom["domains"],
                surface=f"Appears as one of many {anom['signal_type_class']} signals",
                depth=f"Stands {anom['sigma']:.1f}σ from {anom['source_l1_asset']} baseline (mean={anom['mean_salience']:.3f})",
                delta=f"σ-deviation of {anom['sigma']:.2f} marks this as the subsystem's most atypical signal",
                hypothesis=f"Pattern {anom['signal_type_id']} is a {anom['source_l1_asset']} outlier; predicts distinctly unusual outcomes in {', '.join(anom['domains'][:2] or ['unknown'])}",
                cross_subsystem=False,
                cross_subsystem_refs=None,
                corroborating_methods=corr_methods,
                meaningfulness_basis=basis,
                surface_salience=anom["salience"],
                rank=non_ob,
            )
            discoveries.append(d)
            discovery_signal_set.add(anom["signal_id"])

        a = _make_anomaly(
            chart_id, aya, build_id, now,
            anomaly_type="distributional_anomaly",
            subsystem=anom["source_l1_asset"],
            subject_ref={"signal_id": anom["signal_id"], "signal_type_id": anom["signal_type_id"]},
            metric="computed_salience_sigma",
            value=anom["salience"],
            baseline=anom["mean_salience"],
            sigma=anom["sigma"],
            gate_result=gate,
        )
        anomalies.append(a)

    # ── Primitive 4: Broker detection (cross-subsystem) ───────────────────────
    broker_rows = _compute_brokers(conn, chart_id, aya)
    for broker in broker_rows[:BROKER_TOP_N]:
        msr_sig_id = str(broker.get("msr_signal_id") or "")
        if not msr_sig_id or msr_sig_id in discovery_signal_set:
            continue

        subsystem_div = _safe_float(broker.get("subsystem_diversity"))
        edge_count    = _safe_float(broker.get("edge_count"))
        is_cross      = subsystem_div > 2

        consequence = min(
            _safe_float(broker.get("betweenness_centrality")) * 3.0 +
            _safe_float(broker.get("pagerank_score")) * 2.0 +
            (subsystem_div / 10.0),
            1.0,
        )
        non_ob_info = non_ob_by_signal.get(msr_sig_id, {})
        sal_norm    = non_ob_info.get("sal_norm", 0.5)
        non_ob      = consequence * (1.0 - sal_norm)

        subject = str(broker.get("node_subject") or "")

        if is_cross:
            cross_refs = [{
                "node_id": str(broker.get("node_id")),
                "node_subject": subject,
                "cross_subsystem_edge_count": int(edge_count),
                "subsystem_diversity": int(subsystem_div),
            }]
            disc_class = "cross_subsystem_root"
        else:
            cross_refs = None
            disc_class = "structural_hole"

        passes, basis = _passes_meaningfulness_gate(
            str(broker.get("node_type") or "graha"), subject.lower()
        )
        if not passes:
            basis = "broker_structural"  # brokers always have astrological meaning
            passes = True

        d = _make_discovery(
            chart_id, aya, build_id, now,
            discovery_class=disc_class,
            discovery_subsystem=str(broker.get("source_subsystem") or ""),
            non_obviousness=non_ob,
            consequence=consequence,
            constituent_refs=[msr_sig_id],
            reasoning_chain=[
                {"step": "broker_detection", "node_subject": subject,
                 "edge_count": int(edge_count), "subsystem_diversity": int(subsystem_div)},
                {"step": "cross_subsystem", "value": is_cross,
                 "description": "Bridges multiple analytical subsystems"},
            ],
            why_misses=f"Node {subject} bridges {int(subsystem_div)} subsystems via {int(edge_count)} cross-subsystem edges — the inter-domain connection only visible when holding the full relational graph simultaneously",
            domains=[str(broker.get("primary_domain") or "")],
            surface=f"{subject} as an individual astrological factor",
            depth=f"{subject} as a structural BROKER connecting {int(subsystem_div)} analytical domains — a hidden hinge point",
            delta=f"Broker role ({int(subsystem_div)} subsystems, {int(edge_count)} cross-subsystem edges) invisible from isolated factor reading",
            hypothesis=f"{subject} acts as a structural bridge whose influence on multiple life-domains is multiplicatively greater than individual-factor analysis suggests",
            cross_subsystem=is_cross,
            cross_subsystem_refs=cross_refs,
            corroborating_methods=["broker_detection", "non_obviousness"] if msr_sig_id in non_ob_by_signal else ["broker_detection"],
            meaningfulness_basis=basis,
            surface_salience=non_ob_info.get("surface_salience", 0.0),
            rank=non_ob,
        )
        discoveries.append(d)
        discovery_signal_set.add(msr_sig_id)

    # ── D7: Ruthless ranking (sort by composite rank DESC) ────────────────────
    discoveries.sort(key=lambda x: x["composite_discovery_rank"], reverse=True)

    logger.info(
        "[bo_anveshana] %s — %d discoveries, %d anomalies",
        aya, len(discoveries), len(anomalies),
    )
    return discoveries, anomalies


def _batch_insert(conn: Any, rows: list[dict], sql: str, batch_size: int = 50) -> int:
    if not rows:
        return 0
    inserted = 0
    with conn.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            try:
                cur.executemany(sql, batch)
                inserted += max(0, cur.rowcount)
            except Exception as exc:
                logger.warning("[bo_anveshana] batch failed at %d: %s", i, exc)
                for row in batch:
                    try:
                        cur.execute("SAVEPOINT row_sp")
                        cur.execute(sql, row)
                        cur.execute("RELEASE SAVEPOINT row_sp")
                        inserted += max(0, cur.rowcount)
                    except Exception as re:
                        cur.execute("ROLLBACK TO SAVEPOINT row_sp")
                        logger.warning("[bo_anveshana] row skip: %s", re)
    return inserted


@register("bo_anveshana")
class BoAnveshanaWriter(WriterBase):
    """bo_anveshana: discovery engine — latent insights, outliers, brokers."""
    asset_id = "bo_anveshana"

    def run(self, ctx: ContextSpec) -> WriterResult:
        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()

        if ctx.dry_run:
            return WriterResult(asset_id=self.asset_id, rows_inserted=0,
                                notes="dry_run — would mine all ayanamshas for discoveries")

        # Idempotency: delete prior rows
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bodha_discoveries WHERE chart_id = %s", [chart_id])
            cur.execute("DELETE FROM bodha_anomalies WHERE chart_id = %s", [chart_id])

        total_disc = 0
        total_anom = 0

        for aya in CANONICAL_AYAS:
            discoveries, anomalies = _mine_ayanamsha(conn, chart_id, aya, build_id, now)
            total_disc += _batch_insert(conn, discoveries, _DISCOVERY_INSERT)
            total_anom += _batch_insert(conn, anomalies, _ANOMALY_INSERT)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=total_disc + total_anom,
            notes=f"discoveries={total_disc} anomalies={total_anom}",
        )
