"""
bodha_writers.special_lagna_emitter — Special-lagna domain-salience MSR emitter
==================================================================================
D-2 Lane V-5 (CR-76). PURE L2 DERIVATION over existing L1 `special_lagna`
facts — no new astronomical compute. Reads the already-computed Indu Lagna
(wealth-potential upapada), Sree Lagna (fame/prosperity), Ghati Lagna
(authority/timing), and Hora Lagna (secondary wealth) placements — each
carries `house_d1`, `sign`, `sign_lord`, `nakshatra`, `nakshatra_lord`,
`pada` per the L1 special_lagna fact category (§F0 substrate delta) — and
emits one `special_lagna` MSR signal per (lagna x ayanamsha), each carrying
a `domain_salience` field so the signal ranks correctly INSIDE its
classically-assigned domain despite the chart-wide 0.90 class-prior discount
(DR-6 explicit instruction — below-neutral chart-wide, domain-scoped rank
carried on the signal, not the class).

Classical domain assignment (BPHS/Jaimini upapada doctrine):
  - Indu Lagna  -> wealth (the primary dhana-potential upapada)
  - Sree Lagna  -> wealth (fame/prosperity axis, secondary wealth read)
  - Ghati Lagna -> career (authority/timing/public-standing upapada)
  - Hora Lagna  -> wealth (secondary wealth-timing upapada, Parashara)

Emits via a STANDALONE emitter module (does not import or edit bo_laksana.py
or bo_sudarshana.py), per the bo_sudarshana separate-writer precedent.

Salience: class_prior=0.90, subsystem='special_lagna' — ratified DIS.019/DR-6.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from bodha_writers.formulas import salience_formula_v2, SalienceInputsV2

ENGINE_VERSION = "bo_special_lagna_v1.0"

# ── DR-6 / DIS.019 ratified constant — do not edit without a new DR-n ───────
SPECIAL_LAGNA_CLASS_PRIOR = 0.90
SPECIAL_LAGNA_SUBSYSTEM = "special_lagna"
SIGNAL_TYPE_CLASS = "special_lagna"

# Only the four canonical special lagnas CR-76 names (Indu/Sree/Ghati/Hora).
# special_lagna also carries BHAVA_LAGNA/VARNADA_LAGNA/VIGHATI_LAGNA facts
# (used elsewhere / out of this CR's scope) — intentionally not emitted here.
_TARGET_LAGNAS: dict[str, tuple[str, list[str]]] = {
    "INDU_LAGNA": ("Indu Lagna", ["wealth"]),
    "SREE_LAGNA": ("Sree Lagna", ["wealth"]),
    "GHATI_LAGNA": ("Ghati Lagna", ["career"]),
    "HORA_LAGNA": ("Hora Lagna", ["wealth"]),
}


def _fetch_special_lagna_facts(conn: Any, chart_id: str, aya: str) -> dict[str, dict]:
    rows = conn.execute(
        """SELECT fact_id, fact_subject, fact_key, fact_value_text, fact_value_num
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'special_lagna'
             AND fact_subject = ANY(%s)""",
        [chart_id, aya, list(_TARGET_LAGNAS.keys())],
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, dict):
            fid, subj, key, vtext, vnum = r["fact_id"], r["fact_subject"], r["fact_key"], r["fact_value_text"], r["fact_value_num"]
        else:
            fid, subj, key, vtext, vnum = r[0], r[1], r[2], r[3], r[4]
        out.setdefault(subj, {})[key] = {"text": vtext, "num": vnum, "fact_id": fid}
    return out


def build_signal_row(
    *, chart_id: str, ayanamsha_id: str, build_id: str,
    lagna_key: str, facts: dict, now: str,
) -> dict[str, Any] | None:
    display, domains = _TARGET_LAGNAS[lagna_key]
    house_rec = facts.get("house_d1")
    if not house_rec or house_rec.get("num") is None:
        return None
    house_d1 = int(house_rec["num"])
    sign = (facts.get("sign") or {}).get("text")
    sign_lord = (facts.get("sign_lord") or {}).get("text")
    nakshatra = (facts.get("nakshatra") or {}).get("text")
    nakshatra_lord = (facts.get("nakshatra_lord") or {}).get("text")
    pada = None
    pada_rec = facts.get("pada")
    if pada_rec and pada_rec.get("num") is not None:
        pada = int(pada_rec["num"])

    constituent_facts = [rec["fact_id"] for rec in facts.values() if rec.get("fact_id")]

    # A special lagna landing in a kendra/trikona (1/4/5/7/9/10) from Lagna is
    # classically stronger for the domain it governs — modest specificity lift.
    _STRONG_HOUSES = frozenset({1, 4, 5, 7, 9, 10})
    specificity = 1.15 if house_d1 in _STRONG_HOUSES else 1.0

    inputs = SalienceInputsV2(
        orb_tightness=1.0,
        shadbala_norm=1.0,
        dignity_score=0.50,
        house_number=house_d1,
        ashtakavarga_bindus=4,
        vargottama_amplification=0.0,
        neechabhanga_modifier=1.0,
        cancellation_modifier=1.0,
        verification_pass_status="documented_approximation",
        class_prior=SPECIAL_LAGNA_CLASS_PRIOR,
        varga_id="D1",
        specificity=specificity,
        bala_gate=None,
        functional_context=1.0,
        inputs_complete=True,
    )
    sal = salience_formula_v2(inputs)
    computed_salience = sal["computed_salience"]

    # domain_salience carries in-domain rank independent of the chart-wide
    # 0.90 class discount — DR-6's explicit instruction. Boost by 1/0.90 so
    # the domain-scoped value reads at parity with a neutral-prior signal of
    # the same underlying strength (undoes only the class-prior discount,
    # not the specificity/house terms).
    domain_boost = computed_salience / SPECIAL_LAGNA_CLASS_PRIOR
    domain_salience_map = {d: round(domain_boost, 6) for d in domains}

    config = {
        "lagna": display,
        "lagna_key": lagna_key,
        "house_d1": house_d1,
        "sign": sign,
        "sign_lord": sign_lord,
        "nakshatra": nakshatra,
        "nakshatra_lord": nakshatra_lord,
        "pada": pada,
        "governs_domains": domains,
    }

    summary = (
        f"category=special_lagna | lagna={display} | house_d1={house_d1} | sign={sign} | "
        f"sign_lord={sign_lord} | nakshatra={nakshatra} | domains={domains}"
    )
    headline = f"{display} in H{house_d1} ({sign}, lord {sign_lord}) — governs {'/'.join(domains)}"

    return {
        "signal_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "signal_type_id": f"special_lagna:{lagna_key}",
        "signal_type_class": SIGNAL_TYPE_CLASS,
        "signal_tradition": "parashari",
        "fact_kind": "position",
        "source_l1_asset": "ga_sensitive",
        "source_subsystem": SPECIAL_LAGNA_SUBSYSTEM,
        "signal_summary_text": summary,
        "signal_headline_text": headline,
        "classical_sources_jsonb": json.dumps({
            "catalog_ids": [], "rule_ids": [], "text_chunk_ids": [],
            "citations": ["BPHS/Jaimini upapada doctrine: Indu/Sree/Ghati/Hora Lagna"],
        }),
        "varga_id": "D1",
        "varga_provenance_jsonb": None,
        "epistemic_tier": "documented_approximation",
        "epistemic_jsonb": json.dumps({
            "tradition_agreement_state": "single_tradition",
            "ayanamsha_fragility": "per_ayanamsha_computed",
            "computation_vs_interpretation": "computation",
            "calibration_hook": None,
        }),
        "salience_conditioned_by_jsonb": None,
        "signature_tier": None,
        "valence": "neutral",
        "lel_origin": False,
        "configuration_jsonb": json.dumps(config),
        "constituent_facts_array": constituent_facts,
        "constituent_signals_array": None,
        "classical_sources_array": None,
        "source_corroboration_count_by_text": None,
        "source_corroboration_count_by_verse": None,
        "orb_tightness": inputs.orb_tightness,
        "shadbala_norm": inputs.shadbala_norm,
        "dignity_score": inputs.dignity_score,
        "deterministic_strength": 1.0,
        "verification_certainty": 1.0,
        "divisional_corroboration_count": None,
        "dasha_activation_proximity_score": None,
        "house_weight_multiplier": None,
        "ashtakavarga_support_multiplier": None,
        "aspect_modifier": None,
        "vargottama_amplification": inputs.vargottama_amplification,
        "argala_modifier": None,
        "neechabhanga_modifier": inputs.neechabhanga_modifier,
        "cancellation_modifier": inputs.cancellation_modifier,
        "computed_salience": computed_salience,
        "salience_pctl_in_class": None,
        "salience_formula_version": "v2",
        "salience_confidence_interval_jsonb": None,
        "domains_affected_array": domains,
        "domain_salience_jsonb": json.dumps(domain_salience_map),
        "shared_factor_keys_jsonb": None,
        "cross_domain_shared_factor_count": None,
        "graph_edge_pattern_jsonb": None,
        "graph_node_strength_contribution_jsonb": None,
        "relationship_classification": "special_lagna_placement",
        "graha_weakness_indicators_jsonb": None,
        "remedy_hooks_array": None,
        "recurring_pattern_marker": None,
        "top_k_salience_rank": None,
        "system_convergence_count": None,
        "signature_class": "upapada",
        "contradicts_signals_array": None,
        "active_duration_class": "natal_permanent",
        "active_dasha_periods_jsonb": None,
        "activation_predicted_dates_jsonb": None,
        "predicted_outcome_class": None,
        "cross_ayanamsha_consistency_score": None,
        "strength_normalized_to_chart_max": None,
        "pada_precision_flag": None,
        "cross_system_consensus_count": None,
        "channel_render_priority_jsonb": None,
        "verification_pass_status": "documented_approximation",
        "verification_method": "l1_fact_composition_deterministic",
        "citation_ref": f"bo_special_lagna/{lagna_key}",
        "citation_human": f"Special lagna: {display}",
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
        "ratification_factor": None,
        "valence_source": "categorical_deterministic_v1",
    }
