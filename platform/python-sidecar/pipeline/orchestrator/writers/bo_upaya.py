"""
bo_upaya — Remediation Map (L2 Bodha)
======================================
Reads bodha_msr_signals + L1 chart_facts + brahma_remedy_corpus →
writes:
  - bodha_rm_resonances          (one row per graha per ayanamsha: weakness + remedy priority)
  - bodha_rm_remedy_prescriptions (1-3 prescriptions per resonance, grounded to G27 corpus)

Resonance algorithm:
  For each of the 9 grahas:
    1. Fetch L1 shadbala_normalized + bhava_bala_normalized (chart_facts)
    2. Fetch combustion/debility/dignity from chart_facts (graha_special_state_rollup)
    3. Count dosha MSR signals touching this graha → contradiction_factor
    4. Compute resonance_score_v1 (formulas.py)
    5. Rank grahas by resonance_score DESC → weakest_rank_in_chart

Prescription grounding:
  For each resonance:
    1. Query brahma_remedy_corpus WHERE planet = graha.lower()
    2. Top 3 by confidence DESC
    3. Compute resonance_match_score_v1 (formulas.py)
    4. Write bodha_rm_remedy_prescriptions row

LIGHT writer.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from . import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

ENGINE_VERSION   = "bo_upaya_v1.0"
SNAPSHOT_TYPE    = "static_natal"
CANONICAL_AYAS   = ["LAHIRI", "RAMAN", "KRISHNAMURTI", "YUKTESHWAR", "TROPICAL"]

KNOWN_GRAHAS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
]

# Graha → Jaimini chara-karaka role (chart-specific; placeholder)
# In practice this comes from chart_facts karaka_chara_position
CHARA_ROLE_LOOKUP: dict[str, str] = {}   # populated from chart_facts at runtime

_RESONANCE_INSERT = """
INSERT INTO bodha_rm_resonances (
  resonance_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  graha, resonance_score, resonance_score_formula_version,
  weakness_score, contradiction_factor, domain_burden, motif_burden,
  is_yoga_karaka_flag, is_chara_karaka_role,
  weakest_rank_in_chart, remedy_priority_class,
  associated_doshas_array, associated_motifs_array, associated_cdlm_cells_array,
  ephemeris_audit_jsonb, verification_pass_status, citation_ref, citation_human, computed_at
) VALUES (
  %(resonance_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(graha)s, %(resonance_score)s, %(resonance_score_formula_version)s,
  %(weakness_score)s, %(contradiction_factor)s, %(domain_burden)s, %(motif_burden)s,
  %(is_yoga_karaka_flag)s, %(is_chara_karaka_role)s,
  %(weakest_rank_in_chart)s, %(remedy_priority_class)s,
  %(associated_doshas_array)s, NULL, NULL,
  NULL, %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s
)
"""

_PRESCRIPTION_INSERT = """
INSERT INTO bodha_rm_remedy_prescriptions (
  prescription_id, chart_id, ayanamsha_id, build_id, snapshot_type,
  target_graha, target_resonance_id,
  tradition, sub_tradition,
  remedy_category, remedy_id_g27, remedy_label_human,
  prescription_detail_jsonb,
  classical_strength_rating, classical_source_citation_id, classical_source_text_jsonb,
  targets_motif_id, targets_cell_id, targets_dosha_class,
  resonance_match_score, match_score_formula_version,
  counter_indications_array, incompatible_with_prescription_ids_array, prerequisite_prescription_ids_array,
  feasibility_score, estimated_cost_inr_range_jsonb, estimated_time_minutes_daily, ritual_complexity_class,
  requires_acharya_review_flag, acharya_review_reason_array,
  cross_tradition_corroboration_count, cross_tradition_corroborating_traditions_array,
  phase_sequence_class, phase_duration_days, count_prescription_jsonb,
  substitute_options_jsonb, yantra_geometry_jsonb, pranapratishtha_required_flag,
  pilgrimage_site_jsonb, pilgrimage_priority_rank,
  recommended_hora_lord_array, recommended_choghadiya_window_array,
  initiation_lunar_phase_recommendation_array, recommended_facing_direction,
  outcome_tracking_placeholder_jsonb, prescription_embedding_vec,
  verification_pass_status, citation_ref, citation_human, computed_at, engine_version
) VALUES (
  %(prescription_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s, %(snapshot_type)s,
  %(target_graha)s, %(target_resonance_id)s,
  %(tradition)s, NULL,
  %(remedy_category)s, %(remedy_id_g27)s, %(remedy_label_human)s,
  %(prescription_detail_jsonb)s::jsonb,
  %(classical_strength_rating)s, %(classical_source_citation_id)s, NULL,
  NULL, NULL, %(targets_dosha_class)s,
  %(resonance_match_score)s, %(match_score_formula_version)s,
  %(counter_indications_array)s, NULL, NULL,
  %(feasibility_score)s, NULL, NULL, %(ritual_complexity_class)s,
  %(requires_acharya_review_flag)s, NULL,
  %(cross_tradition_corroboration_count)s, NULL,
  NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
  NULL, NULL, NULL, NULL, NULL, NULL,
  %(verification_pass_status)s, %(citation_ref)s, %(citation_human)s, %(computed_at)s, %(engine_version)s
)
ON CONFLICT DO NOTHING
"""

_BATCH_SIZE = 50


# ── L1 data fetchers ───────────────────────────────────────────────────────────

def _fetch_shadbala(conn: Any, chart_id: str, aya: str) -> dict[str, float]:
    """graha → normalized shadbala (total / 390)."""
    rows = conn.execute(
        """SELECT fact_key, fact_value_numeric FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_shadbala_total'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, float] = {}
    for r in rows:
        key = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        graha = key.split(":")[0] if ":" in key else key
        val   = float(r[1] if isinstance(r, tuple) else r.get("fact_value_numeric") or 390.0)
        out[graha] = min(val / 390.0, 2.0)
    return out


def _fetch_bhava_bala(conn: Any, chart_id: str, aya: str) -> dict[int, float]:
    """house → normalized bhava bala (total / 300)."""
    rows = conn.execute(
        """SELECT fact_key, fact_value_numeric FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'bhava_bala_total'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[int, float] = {}
    for r in rows:
        key = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        try:
            house = int(key.split(":")[-1]) if ":" in key else int(key)
        except ValueError:
            continue
        val = float(r[1] if isinstance(r, tuple) else r.get("fact_value_numeric") or 300.0)
        out[house] = min(val / 300.0, 2.0)
    return out


def _fetch_special_states(conn: Any, chart_id: str, aya: str) -> dict[str, set[str]]:
    """graha → set of special state labels (combust/debilitated/retrograde/exalted)."""
    rows = conn.execute(
        """SELECT fact_key, fact_value_text FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category IN ('graha_special_state_rollup', 'graha_dignity_per_varga')
             AND (fact_key LIKE '%:D1%' OR fact_category = 'graha_special_state_rollup')""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, set[str]] = {}
    for r in rows:
        key = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        val = str(r[1] if isinstance(r, tuple) else r.get("fact_value_text") or "")
        graha = key.split(":")[0]
        if graha not in out:
            out[graha] = set()
        if val:
            out[graha].update(s.strip().lower() for s in val.split(",") if s.strip())
    return out


def _fetch_graha_house_placements(conn: Any, chart_id: str, aya: str) -> dict[str, int]:
    """graha → bhava number (D1 placement)."""
    rows = conn.execute(
        """SELECT fact_key, fact_value_numeric FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_position'
             AND fact_key LIKE '%:D1%:bhava%'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, int] = {}
    for r in rows:
        key = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        graha = key.split(":")[0]
        try:
            val = int(r[1] if isinstance(r, tuple) else r.get("fact_value_numeric") or 1)
            out[graha] = val
        except (TypeError, ValueError):
            pass
    return out


def _fetch_yoga_karaka_flags(conn: Any, chart_id: str, aya: str) -> set[str]:
    """Returns set of grahas that are yoga-karakas."""
    rows = conn.execute(
        """SELECT fact_key FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'graha_yoga_karaka_flag'
             AND fact_value_text IN ('true', '1', 'yes', 'yoga_karaka')""",
        [chart_id, aya],
    ).fetchall()
    result: set[str] = set()
    for r in rows:
        key = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        graha = key.split(":")[0]
        if graha in KNOWN_GRAHAS:
            result.add(graha)
    return result


def _fetch_chara_roles(conn: Any, chart_id: str, aya: str) -> dict[str, str]:
    """graha → chara karaka role (AK/AmK/BK/etc.)."""
    rows = conn.execute(
        """SELECT fact_key, fact_value_text FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'karaka_chara_position'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, str] = {}
    for r in rows:
        key = str(r[0] if isinstance(r, tuple) else r.get("fact_key", ""))
        val = str(r[1] if isinstance(r, tuple) else r.get("fact_value_text") or "")
        graha = key.split(":")[0]
        if graha in KNOWN_GRAHAS and val:
            out[graha] = val
    return out


def _fetch_msr_dosha_sigs_by_graha(conn: Any, chart_id: str, aya: str) -> dict[str, list[str]]:
    """graha → list of dosha signal_type_ids (from MSR signals of class dosha)."""
    rows = conn.execute(
        """SELECT configuration_jsonb, signal_type_id, computed_salience
           FROM bodha_msr_signals
           WHERE chart_id = %s AND ayanamsha_id = %s AND signal_type_class = 'dosha'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, list[str]] = {}
    for r in rows:
        cfg_raw = r[0] if isinstance(r, tuple) else r.get("configuration_jsonb") or {}
        type_id = str(r[1] if isinstance(r, tuple) else r.get("signal_type_id") or "")
        if isinstance(cfg_raw, str):
            try:
                cfg = json.loads(cfg_raw)
            except Exception:
                cfg = {}
        else:
            cfg = cfg_raw if isinstance(cfg_raw, dict) else {}
        graha = (cfg.get("graha") or cfg.get("primary_graha") or cfg.get("lord") or "").split(":")[0]
        if graha in KNOWN_GRAHAS:
            if graha not in out:
                out[graha] = []
            if type_id and type_id not in out[graha]:
                out[graha].append(type_id)
    return out


def _fetch_remedies_for_graha(conn: Any, planet: str, limit: int = 5) -> list[dict]:
    """Fetch top remedies from brahma_remedy_corpus for this planet."""
    rows = conn.execute(
        """SELECT remedy_id, remedy_type, prescription_text, confidence,
                  source_canonical_id, source_citation, classical_ref,
                  contraindications, cost_tier
           FROM brahma_remedy_corpus
           WHERE lower(planet) = %s AND scaffold_status = 'live'
           ORDER BY confidence DESC NULLS LAST
           LIMIT %s""",
        [planet.lower(), limit],
    ).fetchall()
    keys = [
        "remedy_id", "remedy_type", "prescription_text", "confidence",
        "source_canonical_id", "source_citation", "classical_ref",
        "contraindications", "cost_tier",
    ]
    return [dict(zip(keys, r)) if not isinstance(r, dict) else r for r in rows]


# ── Priority class ─────────────────────────────────────────────────────────────

def _priority_class(score: float) -> str:
    if score >= 0.70:
        return "critical"
    if score >= 0.45:
        return "high"
    if score >= 0.25:
        return "medium"
    return "low"


def _feasibility(remedy: dict) -> float:
    """Simple feasibility: mantra/charity → high, gem → low."""
    rt = str(remedy.get("remedy_type") or "mantra").lower()
    if rt in ("mantra", "japa", "vrata", "behavioral"):
        return 0.90
    if rt in ("charity", "puja", "homa"):
        return 0.75
    if rt in ("yantra",):
        return 0.60
    if rt in ("gemstone",):
        return 0.45
    return 0.70


def _complexity(remedy: dict) -> str:
    rt = str(remedy.get("remedy_type") or "mantra").lower()
    if rt in ("mantra", "japa", "behavioral"):
        return "simple"
    if rt in ("charity", "puja", "vrata"):
        return "moderate"
    return "complex"


# ── Main per-ayanamsha build ───────────────────────────────────────────────────

def _build_resonances_and_prescriptions(
    chart_id: str, aya: str, build_id: str, conn: Any, now: str
) -> tuple[list[dict], list[dict]]:
    from bodha_writers.formulas import (
        ResonanceInputs, resonance_score_v1,
        ResonanceMatchInputs, resonance_match_score_v1,
    )

    shadbala      = _fetch_shadbala(conn, chart_id, aya)
    bhava_bala    = _fetch_bhava_bala(conn, chart_id, aya)
    special_states = _fetch_special_states(conn, chart_id, aya)
    placements    = _fetch_graha_house_placements(conn, chart_id, aya)
    yoga_karakas  = _fetch_yoga_karaka_flags(conn, chart_id, aya)
    chara_roles   = _fetch_chara_roles(conn, chart_id, aya)
    dosha_by_graha = _fetch_msr_dosha_sigs_by_graha(conn, chart_id, aya)

    resonances: list[dict] = []

    for graha in KNOWN_GRAHAS:
        states       = special_states.get(graha, set())
        combustion   = 1.0 if "combust" in states else 0.0
        debility     = 1.0 if "debilitated" in states else (0.3 if "moolatrikona" not in states and "exalted" not in states else 0.0)
        afflictions  = min(len(dosha_by_graha.get(graha, [])) / 3.0, 1.0)
        house        = placements.get(graha, 1)
        sha_norm     = shadbala.get(graha, 0.5)
        bh_norm      = bhava_bala.get(house, 0.5)
        is_yk        = graha in yoga_karakas
        chara_role   = chara_roles.get(graha)

        r_inputs = ResonanceInputs(
            shadbala_normalized=min(sha_norm, 1.0),
            bhava_bala_normalized=min(bh_norm, 1.0),
            combustion_score=combustion,
            debility_score=debility,
            affliction_count_normalized=afflictions,
            cancellation_burden=0.0,
            dispositor_chain_weakness=0.0,
            vargottama_absence_score=0.5,
            dasha_proximity_activation_score=0.0,
            msr_signals_in_conflict=min(len(dosha_by_graha.get(graha, [])) * 0.1, 1.0),
            cdlm_weakest_constituent_count=0.0,
            cgm_motifs_weakest_node=0.0,
            is_yoga_karaka=is_yk,
            chara_role=chara_role,
        )
        r_result = resonance_score_v1(r_inputs)

        resonance_id = str(uuid.uuid4())
        resonances.append({
            "_graha": graha,
            "_resonance_id": resonance_id,
            "_resonance_score": float(r_result["resonance_score"]),
            "_is_yoga_karaka": is_yk,
            "_chara_role": chara_role,
            "resonance_id": resonance_id,
            "chart_id": chart_id,
            "ayanamsha_id": aya,
            "build_id": build_id,
            "snapshot_type": SNAPSHOT_TYPE,
            "graha": graha,
            "resonance_score": round(float(r_result["resonance_score"]), 6),
            "resonance_score_formula_version": r_result["resonance_score_formula_version"],
            "weakness_score": round(float(r_result["weakness_score"]), 6),
            "contradiction_factor": round(float(r_result["contradiction_factor"]), 6),
            "domain_burden": round(float(r_result["domain_burden"]), 6),
            "motif_burden": round(float(r_result["motif_burden"]), 6),
            "is_yoga_karaka_flag": is_yk,
            "is_chara_karaka_role": chara_role,
            "weakest_rank_in_chart": None,  # set after ranking
            "remedy_priority_class": None,  # set after ranking
            "associated_doshas_array": dosha_by_graha.get(graha),
            "verification_pass_status": "documented_approximation",
            "citation_ref": f"bo_upaya/resonance/{graha}",
            "citation_human": f"Resonance: {graha} | sha={sha_norm:.2f} dosha_count={len(dosha_by_graha.get(graha, []))}",
            "computed_at": now,
        })

    # Rank by resonance_score DESC
    resonances.sort(key=lambda x: x["_resonance_score"], reverse=True)
    for rank, row in enumerate(resonances, start=1):
        row["weakest_rank_in_chart"] = rank
        row["remedy_priority_class"] = _priority_class(row["_resonance_score"])

    # Prescriptions (top 3 remedies per graha from corpus)
    prescriptions: list[dict] = []
    for res in resonances:
        graha         = res["_graha"]
        resonance_id  = res["_resonance_id"]
        remedies_from_corpus = _fetch_remedies_for_graha(conn, graha, limit=3)

        for corpus_row in remedies_from_corpus:
            rm_inputs = ResonanceMatchInputs(
                classical_strength_for_graha=float(corpus_row.get("confidence") or 0.85),
                chart_typology="balanced",
                remedy_category=str(corpus_row.get("remedy_type") or "mantra"),
                cross_tradition_corroboration_count=1,
                has_active_counter_indication=False,
            )
            rm_result = resonance_match_score_v1(rm_inputs)

            prescriptions.append({
                "prescription_id": str(uuid.uuid4()),
                "chart_id": chart_id,
                "ayanamsha_id": aya,
                "build_id": build_id,
                "snapshot_type": SNAPSHOT_TYPE,
                "target_graha": graha,
                "target_resonance_id": resonance_id,
                "tradition": "parashari",
                "remedy_category": str(corpus_row.get("remedy_type") or "mantra"),
                "remedy_id_g27": str(corpus_row.get("remedy_id") or ""),
                "remedy_label_human": str(corpus_row.get("prescription_text") or "")[:200],
                "prescription_detail_jsonb": json.dumps({
                    "prescription_text": corpus_row.get("prescription_text"),
                    "mantra_text": corpus_row.get("mantra_text"),
                    "gemstone": corpus_row.get("gemstone"),
                    "charity_action": corpus_row.get("charity_action"),
                    "deity": corpus_row.get("deity"),
                }),
                "classical_strength_rating": str(corpus_row.get("confidence") or ""),
                "classical_source_citation_id": str(corpus_row.get("source_canonical_id") or "BPHS"),
                "targets_dosha_class": (dosha_by_graha.get(graha) or [None])[0],
                "resonance_match_score": round(float(rm_result["resonance_match_score"]), 6),
                "match_score_formula_version": rm_result["match_score_formula_version"],
                "counter_indications_array": (
                    [corpus_row["contraindications"]] if corpus_row.get("contraindications") else None
                ),
                "feasibility_score": round(_feasibility(corpus_row), 4),
                "ritual_complexity_class": _complexity(corpus_row),
                "requires_acharya_review_flag": str(corpus_row.get("remedy_type") or "").lower() in ("gemstone", "homa"),
                "cross_tradition_corroboration_count": 1,
                "verification_pass_status": "documented_approximation",
                "citation_ref": f"brahma_remedy_corpus/{corpus_row.get('remedy_id')}",
                "citation_human": f"G27 remedy {corpus_row.get('remedy_id')} for {graha}",
                "computed_at": now,
                "engine_version": ENGINE_VERSION,
            })

    return resonances, prescriptions


def _batch_insert(conn: Any, rows: list[dict], sql: str) -> int:
    inserted = 0
    for i in range(0, len(rows), _BATCH_SIZE):
        for row in rows[i:i + _BATCH_SIZE]:
            conn.execute(sql, row)
        inserted += len(rows[i:i + _BATCH_SIZE])
    return inserted


def _strip_private_keys(rows: list[dict]) -> list[dict]:
    """Remove _-prefixed helper keys before INSERT."""
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]


@register("bo_upaya")
class BoUpayaWriter(WriterBase):
    """bo_upaya: Remediation Map — resonances + prescriptions grounded to G27 corpus."""
    asset_id = "bo_upaya"

    def run(self, ctx: ContextSpec) -> WriterResult:
        from bodha_writers._idempotency import (
            replace_prior_rm_resonances, replace_prior_rm_prescriptions,
        )

        chart_id = ctx.config["chart_id"]
        build_id = ctx.build_id
        conn     = ctx.db_conn
        now      = datetime.now(timezone.utc).isoformat()
        total_res = 0
        total_presc = 0

        for aya in CANONICAL_AYAS:
            if ctx.dry_run:
                logger.info("[bo_upaya dry_run] %s", aya)
                continue

            resonances, prescriptions = _build_resonances_and_prescriptions(
                chart_id, aya, build_id, conn, now
            )

            replace_prior_rm_resonances(conn, chart_id, aya, SNAPSHOT_TYPE)
            replace_prior_rm_prescriptions(conn, chart_id, aya, SNAPSHOT_TYPE)

            clean_res = _strip_private_keys(resonances)
            logger.info("[bo_upaya] %s — %d resonances, %d prescriptions",
                        aya, len(resonances), len(prescriptions))
            total_res   += _batch_insert(conn, clean_res, _RESONANCE_INSERT)
            total_presc += _batch_insert(conn, prescriptions, _PRESCRIPTION_INSERT)

        return WriterResult(asset_id=self.asset_id, rows_inserted=total_res + total_presc,
                            notes=f"resonances={total_res} prescriptions={total_presc}")
