"""
bodha_writers.vargottama_dhana_emitter — Vargottama amplification + Dhana-axis MSR emitter
===============================================================================================
D-2 Lane V-5 (CR-36). PURE L2 DERIVATION over existing L1
`vargottama_per_varga` and `graha_position` facts — no new astronomical
compute. Emits TWO signal_type_classes from one module (BRIEF_D2.md Lane
V-5 groups them as one deliverable; DR-6/DIS.019 prices them as two
class-priors):

  - `vargottama_amplification` — one signal per graha that IS vargottama in
    D9 (Navamsha: same sign in D1 and D9 — the classical vargottama test,
    BPHS). A cross-frame confirmation class, epistemically identical to
    sudarshana_agreement's "two independent frames agree" (DR-3 precedent);
    fires ONLY when true (never a vacuous non-vargottama row — an
    amplification signal that never amplifies is not a signal).

  - `dhana_axis` — complete 2nd/11th-house (dhana/labha) tenancy analysis:
    for each of houses 2 and 11, which graha(s) occupy it (from
    `graha_position.house_d1`) and the classical sign-lord of that house
    (derived from the natal Lagna sign via the fixed 12-sign rulership
    table — standard BPHS knowledge, not a DB fact; the LAGNA sign itself
    IS read from the L1 `graha_position` fact, so the derivation is
    grounded in a real L1 constituent). One row per house (2 rows minimum
    per ayanamsha; occupied houses get their occupant graha references
    added as additional constituent facts).

Emits via a STANDALONE emitter module (does not import or edit bo_laksana.py
or bo_sudarshana.py); imports read-only sign helpers from sudarshana_emitter.

Salience: vargottama_amplification class_prior=1.15, dhana_axis class_prior=1.05
— ratified DIS.019/DR-6. Dedup discipline against the `yoga` class (dhana
yoga rows already fired elsewhere): dhana_axis signals are TENANCY facts
(who occupies/rules the house), never yoga-formation claims — no overlap
with `bo_laksana`'s yoga-class rows by construction.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from bodha_writers.formulas import salience_formula_v2, SalienceInputsV2
from bodha_writers.sudarshana_emitter import GRAHAS, SIGNS, sign_index
from brahmagyan import valence_doctrine as _vd
from brahmagyan.graha_vocabulary import to_title

ENGINE_VERSION = "bo_vargottama_dhana_v1.0"

# ── DR-6 / DIS.019 ratified constants — do not edit without a new DR-n ──────
VARGOTTAMA_AMPLIFICATION_CLASS_PRIOR = 1.15
VARGOTTAMA_AMPLIFICATION_SUBSYSTEM = "varga"
VARGOTTAMA_AMPLIFICATION_SIGNAL_TYPE_CLASS = "vargottama_amplification"

DHANA_AXIS_CLASS_PRIOR = 1.05
DHANA_AXIS_SUBSYSTEM = "structural"
DHANA_AXIS_SIGNAL_TYPE_CLASS = "dhana_axis"

# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2. Kept as a local dict so `.get(code, code)` preserves its
# fall-back-to-raw-input-unchanged behavior for unrecognized codes.
_GRAHA_DISPLAY: dict[str, str] = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
}

# Classical fixed sign-lordship (BPHS) — Rahu/Ketu are NOT sign lords in the
# classical 12-rashi rulership scheme (they are chara/shadow-graha karakas
# only); house lords are always one of the 7 classical grahas.
_SIGN_LORD: dict[str, str] = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}


def _fetch_vargottama_facts(conn: Any, chart_id: str, aya: str) -> dict[str, dict]:
    """{graha_code: {'is_vargottama': bool, 'fact_id': str}} from D9 rows."""
    rows = conn.execute(
        """SELECT fact_id, fact_subject, fact_value_num
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category = 'vargottama_per_varga' AND fact_key = 'is_vargottama'
             AND fact_subject LIKE 'D9_%%'""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, dict):
            fid, subj, vnum = r["fact_id"], r["fact_subject"], r["fact_value_num"]
        else:
            fid, subj, vnum = r[0], r[1], r[2]
        graha_code = str(subj).replace("D9_", "", 1)
        out[graha_code] = {"is_vargottama": bool(vnum), "fact_id": fid}
    return out


def _fetch_graha_positions(conn: Any, chart_id: str, aya: str) -> dict[str, dict]:
    """{fact_subject: {'house_d1': int|None, 'sign': str|None, fact ids}}"""
    rows = conn.execute(
        """SELECT fact_id, fact_subject, fact_key, fact_value_text, fact_value_num
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s AND fact_category = 'graha_position'
             AND fact_key IN ('house_d1', 'sign')""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, dict):
            fid, subj, key, vtext, vnum = r["fact_id"], r["fact_subject"], r["fact_key"], r["fact_value_text"], r["fact_value_num"]
        else:
            fid, subj, key, vtext, vnum = r[0], r[1], r[2], r[3], r[4]
        out.setdefault(str(subj).upper(), {})[key] = {"text": vtext, "num": vnum, "fact_id": fid}
    return out


def _base_inputs(class_prior: float, specificity: float, house: int | None) -> SalienceInputsV2:
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
        class_prior=class_prior,
        varga_id="D9",
        specificity=specificity,
        bala_gate=None,
        functional_context=1.0,
        inputs_complete=True,
    )


def _make_row(
    *, chart_id: str, ayanamsha_id: str, build_id: str, signal_type_class: str,
    subsystem: str, source_l1_asset: str, signal_subkey: str,
    summary: str, headline: str, config: dict, constituent_facts: list[str],
    class_prior: float, specificity: float, house: int | None, valence: str,
    domains: list[str], relationship_classification: str, varga_id: str, now: str,
    valence_source: str = "categorical_deterministic_v1",
) -> dict[str, Any]:
    inputs = _base_inputs(class_prior, specificity, house)
    inputs.varga_id = varga_id
    sal = salience_formula_v2(inputs)
    computed_salience = sal["computed_salience"]
    return {
        "signal_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "signal_type_id": f"{signal_type_class}:{signal_subkey}",
        "signal_type_class": signal_type_class,
        "signal_tradition": "parashari",
        "fact_kind": "relationship",
        "source_l1_asset": source_l1_asset,
        "source_subsystem": subsystem,
        "signal_summary_text": summary,
        "signal_headline_text": headline,
        "classical_sources_jsonb": json.dumps({
            "catalog_ids": [], "rule_ids": [], "text_chunk_ids": [],
            "citations": ["BPHS vargottama doctrine (same sign D1/D9)" if signal_type_class == VARGOTTAMA_AMPLIFICATION_SIGNAL_TYPE_CLASS
                          else "BPHS dhana/labha (2nd/11th house) tenancy doctrine"],
        }),
        "varga_id": varga_id,
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
        "signature_class": "varga_confirmation" if signal_type_class == VARGOTTAMA_AMPLIFICATION_SIGNAL_TYPE_CLASS else "house_tenancy",
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
        "citation_ref": f"bo_vargottama_dhana/{signal_subkey}",
        "citation_human": headline,
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
        "ratification_factor": None,
        "valence_source": valence_source,
    }


def build_vargottama_rows(
    *, chart_id: str, ayanamsha_id: str, build_id: str,
    vargottama_facts: dict[str, dict], positions: dict[str, dict], now: str,
) -> list[dict[str, Any]]:
    """One row per graha that IS vargottama in D9. Never emits for a
    non-vargottama graha — an amplification class fires only when it fires
    (B.10: no fabricated confidence, no vacuous non-events)."""
    rows: list[dict[str, Any]] = []
    for graha_code in GRAHAS:
        rec = vargottama_facts.get(graha_code)
        if not rec or not rec.get("is_vargottama"):
            continue
        graha_display = _GRAHA_DISPLAY.get(graha_code, graha_code)
        pos = positions.get(graha_code, {})
        house_d1 = None
        house_rec = pos.get("house_d1")
        if house_rec and house_rec.get("num") is not None:
            house_d1 = int(house_rec["num"])
        sign = (pos.get("sign") or {}).get("text")

        constituent_facts = [rec["fact_id"]]
        if house_rec:
            constituent_facts.append(house_rec["fact_id"])

        # DR-9 / VAL-ROOT: vargottama denotes CONFIRMED STRENGTH, not benevolence
        # — a vargottama malefic is a confirmed-strong malefic, not "benefic".
        # The signal's valence is the graha's own signed nature (natural ×
        # dignity incl. node exaltation × occupancy), amplified by the D1=D9
        # cross-frame agreement, never an unconditional benefic.
        vg_verdict = _vd.graha_valence(
            graha_code, contact_type="occupancy", target_house=house_d1,
            graha_sign=sign)

        rows.append(_make_row(
            chart_id=chart_id, ayanamsha_id=ayanamsha_id, build_id=build_id,
            signal_type_class=VARGOTTAMA_AMPLIFICATION_SIGNAL_TYPE_CLASS,
            subsystem=VARGOTTAMA_AMPLIFICATION_SUBSYSTEM,
            source_l1_asset="ga_vargas",
            signal_subkey=graha_code,
            summary=f"category=vargottama_amplification | graha={graha_display} | "
                    f"varga=D9 | house_d1={house_d1} | sign={sign} | valence={vg_verdict.valence}",
            headline=f"{graha_display} is VARGOTTAMA (D1=D9 sign {sign}) — cross-frame confirmed strength ({vg_verdict.valence})",
            config={"graha": graha_display, "graha_code": graha_code, "varga": "D9",
                    "house_d1": house_d1, "sign": sign, "is_vargottama": True,
                    "valence_net": vg_verdict.value_num, "valence_source": "valence_doctrine_v1"},
            constituent_facts=constituent_facts,
            class_prior=VARGOTTAMA_AMPLIFICATION_CLASS_PRIOR,
            specificity=1.5,  # maximal — two independent frames (D1/D9) agree exactly
            house=house_d1,
            valence=vg_verdict.valence,
            valence_source="valence_doctrine_v1",
            domains=["character", "career"],
            relationship_classification="vargottama_confirmed",
            varga_id="D9",
            now=now,
        ))
    return rows


def build_dhana_axis_rows(
    *, chart_id: str, ayanamsha_id: str, build_id: str,
    positions: dict[str, dict], now: str,
) -> list[dict[str, Any]]:
    """One row per dhana-axis house (2nd, 11th): occupant grahas + classical
    sign lord, derived from natal Lagna sign via fixed BPHS rulership."""
    rows: list[dict[str, Any]] = []
    lagna_pos = positions.get("LAGNA", {})
    lagna_sign_rec = lagna_pos.get("sign")
    if not lagna_sign_rec or not lagna_sign_rec.get("text"):
        return rows
    lagna_sign = lagna_sign_rec["text"]
    lagna_i = sign_index(lagna_sign)
    if lagna_i is None:
        return rows
    lagna_fact_id = lagna_sign_rec["fact_id"]

    for house_num, label, domain in ((2, "2nd house (dhana)", "wealth"), (11, "11th house (labha)", "wealth")):
        house_sign = SIGNS[(lagna_i + house_num - 1) % 12]
        house_lord = _SIGN_LORD[house_sign]

        occupants: list[str] = []
        occupant_fact_ids: list[str] = []
        occupant_verdicts: list[_vd.ValenceVerdict] = []
        lord_house_d1 = None
        lord_placement_fact_id = None
        for graha_code in GRAHAS:
            pos = positions.get(graha_code, {})
            hrec = pos.get("house_d1")
            if not hrec or hrec.get("num") is None:
                continue
            gh = int(hrec["num"])
            if gh == house_num:
                occupants.append(_GRAHA_DISPLAY.get(graha_code, graha_code))
                occupant_fact_ids.append(hrec["fact_id"])
                # DR-9 / VAL-ROOT: this house's tenancy valence is the occupant
                # grahas' natures (natural × dignity, incl. node exaltation from
                # sign), NOT an unconditional "benefic". A natural malefic (e.g.
                # Rahu) tenanting the dhana house is adverse/mixed, not a blessing.
                occ_sign = (pos.get("sign") or {}).get("text")
                occupant_verdicts.append(_vd.graha_valence(
                    graha_code, contact_type="occupancy", target_house=house_num,
                    graha_sign=occ_sign,
                ))
            # Track the lord's OWN placement (which house it sits in) —
            # sign lord is not a stored fact-subject, so match by display name.
            if _GRAHA_DISPLAY.get(graha_code, graha_code) == house_lord:
                lord_house_d1 = gh
                lord_placement_fact_id = hrec["fact_id"]

        constituent_facts = [lagna_fact_id] + occupant_fact_ids
        if lord_placement_fact_id:
            constituent_facts.append(lord_placement_fact_id)

        tenancy_valence, tenancy_net = _vd.combine_occupant_verdicts(occupant_verdicts)

        config = {
            "house": house_num, "label": label, "house_sign": house_sign,
            "house_lord": house_lord, "occupants": occupants,
            "lord_own_house_placement": lord_house_d1,
            "valence_net": tenancy_net,
            "valence_source": "valence_doctrine_v1",
        }
        summary = (
            f"category=dhana_axis | house={house_num} | sign={house_sign} | "
            f"lord={house_lord} | occupants={occupants} | lord_placed_in_house={lord_house_d1} "
            f"| valence={tenancy_valence}"
        )
        headline = (
            f"{label}: {house_sign}, lord {house_lord}"
            + (f" — tenanted by {', '.join(occupants)} ({tenancy_valence})" if occupants else " — untenanted")
            + (f"; {house_lord} itself sits in H{lord_house_d1}" if lord_house_d1 else "")
        )

        rows.append(_make_row(
            chart_id=chart_id, ayanamsha_id=ayanamsha_id, build_id=build_id,
            signal_type_class=DHANA_AXIS_SIGNAL_TYPE_CLASS,
            subsystem=DHANA_AXIS_SUBSYSTEM,
            source_l1_asset="ga_positions",
            signal_subkey=f"H{house_num}",
            summary=summary,
            headline=headline,
            config=config,
            constituent_facts=constituent_facts,
            class_prior=DHANA_AXIS_CLASS_PRIOR,
            specificity=1.2 if occupants else 1.0,
            house=house_num,
            valence=tenancy_valence,
            valence_source="valence_doctrine_v1",
            domains=[domain],
            relationship_classification="dhana_axis_tenancy",
            varga_id="D1",
            now=now,
        ))
    return rows
