"""
bodha_writers.arudha_emitter — Jaimini Ārūḍha (perception-layer) MSR emitter
==============================================================================
D-2 Lane V-5 (CR-61). PURE L2 DERIVATION over existing L1 `arudha_pada` and
`graha_position` facts — no new astronomical compute. Reads the already-
computed Arūḍha Lagna (AL / ARUDHA_A1), A2 (dhana ārūḍha) and A11 (lābha
ārūḍha) house/sign placements, plus each graha's own house placement, and
derives:
  - AL–bhāva relation: which classical quadrant category (kendra/trikoṇa/
    dusthāna/upachaya/maraka, counted FROM Lagna) the AL itself occupies —
    Jaimini doctrine treats the "image" (ārūḍha) house class as materially
    different from the physical (rāśi) house class;
  - AL conjunctions: which grahas (if any) occupy the SAME house as AL —
    Jaimini doctrine: a benefic conjunct AL supports the public image/
    perception; a malefic conjunct/aspecting AL corrodes it;
  - A2/A11 tenancy: which grahas occupy the dhana/lābha ārūḍhas — these
    "arūḍha wealth pādas" are read independently of the rāśi 2nd/11th
    (CR-61's whole point: they never surface today).

Emits `arudha` MSR signals via a STANDALONE emitter module — imports
(read-only) the sign/house helpers from sudarshana_emitter, does not edit it,
per the bo_sudarshana separate-writer precedent (protocol §3(d) scope-warden).

Salience: class_prior=1.10, subsystem='jaimini' — ratified DIS.019/DR-6.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from bodha_writers.formulas import salience_formula_v2, SalienceInputsV2
from bodha_writers.sudarshana_emitter import GRAHAS, classify_house
from brahmagyan import valence_doctrine as _vd
from brahmagyan.graha_vocabulary import to_title

ENGINE_VERSION = "bo_arudha_v1.0"

# ── DR-6 / DIS.019 ratified constant — do not edit without a new DR-n ───────
ARUDHA_CLASS_PRIOR = 1.10
ARUDHA_SUBSYSTEM = "jaimini"
SIGNAL_TYPE_CLASS = "arudha"

# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2. Kept as a local dict so `.get(code, code)` preserves its
# fall-back-to-raw-input-unchanged behavior for unrecognized codes.
_GRAHA_DISPLAY: dict[str, str] = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
}

# Classical malefic/benefic split (natural, unconditioned — used only to
# flag AL-conjunction tenor; a full functional-benefic pass is V-6's remit).
_NATURAL_BENEFICS = frozenset({"JUP", "VEN", "MER", "MOON"})
_NATURAL_MALEFICS = frozenset({"SUN", "MAR", "SAT", "RAH_MEAN", "KET_MEAN"})


def _fetch_arudha_facts(conn: Any, chart_id: str, aya: str) -> dict[str, dict]:
    rows = conn.execute(
        """SELECT fact_id, fact_subject, fact_key, fact_value_text, fact_value_num
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'arudha_pada'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, dict):
            fid, subj, key, vtext, vnum = r["fact_id"], r["fact_subject"], r["fact_key"], r["fact_value_text"], r["fact_value_num"]
        else:
            fid, subj, key, vtext, vnum = r[0], r[1], r[2], r[3], r[4]
        out.setdefault(subj, {})[key] = {"text": vtext, "num": vnum, "fact_id": fid}
    return out


def _fetch_graha_houses(conn: Any, chart_id: str, aya: str) -> dict[str, dict]:
    rows = conn.execute(
        """SELECT fact_id, fact_subject, fact_value_num
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'graha_position' AND fact_key = 'house_d1'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, dict):
            fid, subj, vnum = r["fact_id"], r["fact_subject"], r["fact_value_num"]
        else:
            fid, subj, vnum = r[0], r[1], r[2]
        if subj and vnum is not None:
            out[str(subj).upper()] = {"house_d1": int(vnum), "fact_id": fid}
    return out


def _base_inputs(specificity: float, house: int | None) -> SalienceInputsV2:
    return SalienceInputsV2(
        orb_tightness=1.0,
        shadbala_norm=1.0,
        dignity_score=0.50,
        house_number=house or 1,
        ashtakavarga_bindus=4,
        vargottama_amplification=0.0,
        neechabhanga_modifier=1.0,
        cancellation_modifier=1.0,
        verification_pass_status="documented_approximation",
        class_prior=ARUDHA_CLASS_PRIOR,
        varga_id="D1",
        specificity=specificity,
        bala_gate=None,
        functional_context=1.0,
        inputs_complete=True,
    )


def _make_row(
    *, chart_id: str, ayanamsha_id: str, build_id: str, signal_subkey: str,
    summary: str, headline: str, config: dict, constituent_facts: list[str],
    specificity: float, house: int | None, valence: str,
    domains: list[str], relationship_classification: str, now: str,
    valence_source: str = "categorical_deterministic_v1",
) -> dict[str, Any]:
    inputs = _base_inputs(specificity, house)
    sal = salience_formula_v2(inputs)
    computed_salience = sal["computed_salience"]
    return {
        "signal_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "signal_type_id": f"arudha:{signal_subkey}",
        "signal_type_class": SIGNAL_TYPE_CLASS,
        "signal_tradition": "jaimini",
        "fact_kind": "relationship",
        "source_l1_asset": "ga_structural",
        "source_subsystem": ARUDHA_SUBSYSTEM,
        "signal_summary_text": summary,
        "signal_headline_text": headline,
        "classical_sources_jsonb": json.dumps({
            "catalog_ids": [], "rule_ids": [], "text_chunk_ids": [],
            "citations": ["Jaimini Sutram: Arudha Lagna (perceived self) doctrine",
                          "Arudha Pada (A2/A11 dhana/labha padas) tenancy analysis"],
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
        "valence": valence,
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
        "domain_salience_jsonb": json.dumps({d: computed_salience for d in domains}),
        "shared_factor_keys_jsonb": None,
        "cross_domain_shared_factor_count": None,
        "graph_edge_pattern_jsonb": None,
        "graph_node_strength_contribution_jsonb": None,
        "relationship_classification": relationship_classification,
        "graha_weakness_indicators_jsonb": None,
        "remedy_hooks_array": None,
        "recurring_pattern_marker": None,
        "top_k_salience_rank": None,
        "system_convergence_count": None,
        "signature_class": "jaimini_arudha",
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
        "citation_ref": f"bo_arudha/{signal_subkey}",
        "citation_human": f"Arudha: {headline}",
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
        "ratification_factor": None,
        "valence_source": valence_source,
    }


def build_signal_rows(
    *, chart_id: str, ayanamsha_id: str, build_id: str,
    arudha_facts: dict[str, dict], graha_houses: dict[str, dict], now: str,
) -> list[dict[str, Any]]:
    """Build all `arudha` MSR rows for one ayanamsha: AL bhava-relation,
    A2/A11 tenancy, and per-graha AL-conjunction rows."""
    rows: list[dict[str, Any]] = []

    al = arudha_facts.get("ARUDHA_A1")
    if not al or al.get("house_d1", {}).get("num") is None:
        return rows  # AL is the load-bearing input; nothing else is derivable without it
    al_house = int(al["house_d1"]["num"])
    al_sign = (al.get("sign") or {}).get("text")
    al_house_fact_id = al["house_d1"]["fact_id"]
    al_category = classify_house(al_house)

    # ── Row 1: AL bhava-relation ────────────────────────────────────────────
    rows.append(_make_row(
        chart_id=chart_id, ayanamsha_id=ayanamsha_id, build_id=build_id,
        signal_subkey="AL_bhava_relation",
        summary=f"category=arudha | AL_house={al_house} | AL_sign={al_sign} | AL_category={al_category}",
        headline=f"Arudha Lagna (AL) in H{al_house} ({al_sign}) — classical category: {al_category}",
        config={"al_house": al_house, "al_sign": al_sign, "al_category": al_category},
        constituent_facts=[al_house_fact_id],
        specificity=1.2 if al_category in ("trikona", "kendra") else 1.0,
        house=al_house,
        valence="benefic" if al_category in ("trikona", "kendra") else "neutral",
        domains=["character", "career"],
        relationship_classification=f"al_{al_category}",
        now=now,
    ))

    # ── AL conjunctions: grahas sharing AL's house ──────────────────────────
    for graha_code in GRAHAS:
        grec = graha_houses.get(graha_code)
        if not grec or grec.get("house_d1") != al_house:
            continue
        graha_display = _GRAHA_DISPLAY.get(graha_code, graha_code)
        tenor = "benefic" if graha_code in _NATURAL_BENEFICS else (
            "malefic" if graha_code in _NATURAL_MALEFICS else "neutral")
        rows.append(_make_row(
            chart_id=chart_id, ayanamsha_id=ayanamsha_id, build_id=build_id,
            signal_subkey=f"AL_conjunction:{graha_code}",
            summary=f"category=arudha | AL_house={al_house} | graha={graha_display} | tenor={tenor}",
            headline=f"{graha_display} conjunct Arudha Lagna in H{al_house} — {tenor} on public image",
            config={"al_house": al_house, "graha": graha_display, "graha_code": graha_code, "tenor": tenor},
            constituent_facts=[al_house_fact_id, grec["fact_id"]],
            specificity=1.3,
            house=al_house,
            valence=tenor,
            domains=["character", "career"],
            relationship_classification="al_conjunction",
            now=now,
        ))

    # ── A2 / A11 (dhana / labha arudha) tenancy ─────────────────────────────
    for pada_key, pada_label, domain in (
        ("ARUDHA_A2", "A2 (dhana arudha)", "wealth"),
        ("ARUDHA_A11", "A11 (labha arudha)", "wealth"),
    ):
        rec = arudha_facts.get(pada_key)
        if not rec or rec.get("house_d1", {}).get("num") is None:
            continue
        pada_house = int(rec["house_d1"]["num"])
        pada_sign = (rec.get("sign") or {}).get("text")
        pada_fact_id = rec["house_d1"]["fact_id"]

        occupant_codes = [gc for gc in GRAHAS
                          if graha_houses.get(gc, {}).get("house_d1") == pada_house]
        occupants = [_GRAHA_DISPLAY.get(gc, gc) for gc in occupant_codes]
        occupant_fact_ids = [graha_houses[gc]["fact_id"] for gc in occupant_codes]
        # DR-9 / VAL-ROOT: the ārūḍha-pāda tenancy valence is the occupant
        # grahas' natures (natural × dignity, incl. node exaltation from the
        # pāda's sign — occupants share the pāda house/sign), NOT unconditional
        # benefic. A malefic tenanting the dhana/lābha ārūḍha corrodes it.
        occ_verdicts = [
            _vd.graha_valence(gc, contact_type="occupancy", target_house=pada_house,
                              graha_sign=pada_sign)
            for gc in occupant_codes
        ]
        tenancy_valence, tenancy_net = _vd.combine_occupant_verdicts(occ_verdicts)
        rows.append(_make_row(
            chart_id=chart_id, ayanamsha_id=ayanamsha_id, build_id=build_id,
            signal_subkey=f"{pada_key}_tenancy",
            summary=(f"category=arudha | pada={pada_label} | house={pada_house} | sign={pada_sign} "
                     f"| occupants={occupants} | valence={tenancy_valence}"),
            headline=(f"{pada_label} in H{pada_house} ({pada_sign})"
                      + (f" — tenanted by {', '.join(occupants)} ({tenancy_valence})" if occupants else " — untenanted")),
            config={"pada": pada_key, "house": pada_house, "sign": pada_sign,
                    "occupants": occupants, "valence_net": tenancy_net,
                    "valence_source": "valence_doctrine_v1"},
            constituent_facts=[pada_fact_id] + occupant_fact_ids,
            specificity=1.2 if occupants else 1.0,
            house=pada_house,
            valence=tenancy_valence,
            valence_source="valence_doctrine_v1",
            domains=[domain],
            relationship_classification="arudha_pada_tenancy",
            now=now,
        ))

    return rows
