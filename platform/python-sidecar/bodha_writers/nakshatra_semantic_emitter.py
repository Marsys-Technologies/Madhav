"""
bodha_writers.nakshatra_semantic_emitter — Nakshatra-semantic MSR emitter
==========================================================================
D-2 Lane V-5 (CR-26/64). PURE L2 DERIVATION over existing L1 facts — no new
astronomical compute. For each of the 9 grahas + Lagna, reads:
  - own-star (nakshatra/nakshatra_lord/pada) from `graha_position` facts
    (written by ga_positions/ga_nakshatra, untouched by this writer);
  - dispositor chain (`graha_dispositor_chain`, fact_key='chain_jsonb_atomic',
    written by ga_structural — the sign-lord-of-sign-lord... chain to a
    fixed point or cycle);
  - tara bala (`graha_tara_bala`: tara_name/tara_count/tara_position, counted
    from natal Moon's nakshatra, written by ga_nakshatra);
  - end-degree/gandanta proximity (computed HERE from `longitude_sidereal` +
    nakshatra name — gandanta is the junction of a water-sign-ending
    nakshatra (Ashlesha/Jyeshtha/Revati) and the following fire-sign-opening
    nakshatra (Magha/Mula/Ashwini); classical zone = the final/first pada
    (3°20') of the adjoining pair — BPHS/Muhurta gandanta doctrine).

Emits one `nakshatra_semantic` MSR signal per (graha x ayanamsha) via a
STANDALONE emitter module (does not import or edit bo_laksana.py or
bo_sudarshana.py; imports read-only sign helpers from sudarshana_emitter —
an import, not an edit, per protocol §3(d) scope-warden), per
BRIEF_D2.md Lane V-5 ("each a NEW emitter module folding into the signal-
class registry" + the bo_sudarshana separate-writer precedent).

Salience: class_prior=1.00, subsystem='nakshatra' — ratified DIS.019/DR-6
(00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md). Neutral prior: high-volume
corroborative fabric that should enrich without flooding the ranking; a
gandanta/end-degree flag earns a PER-SIGNAL specificity boost, never a
class-wide one (DR-6 explicit instruction).
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from bodha_writers.formulas import salience_formula_v2, SalienceInputsV2
from bodha_writers.sudarshana_emitter import GRAHAS, SIGN_INDEX, sign_index
from brahmagyan.graha_vocabulary import to_title

ENGINE_VERSION = "bo_nakshatra_semantic_v1.0"

# ── DR-6 / DIS.019 ratified constant — do not edit without a new DR-n ───────
NAKSHATRA_SEMANTIC_CLASS_PRIOR = 1.00
NAKSHATRA_SEMANTIC_SUBSYSTEM = "nakshatra"
SIGNAL_TYPE_CLASS = "nakshatra_semantic"

# Values sourced from the graha SSoT's to_title() helper
# (brahmagyan/graha_vocabulary) rather than hardcoded literals — ADHIṢṬHĀNA
# Lane A2. Kept as a local dict so `.get(code, code)` preserves its
# fall-back-to-raw-input-unchanged behavior for unrecognized codes.
_GRAHA_DISPLAY: dict[str, str] = {
    code: to_title(code)
    for code in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
}

# ── Classical 27-nakshatra span (13°20' each), 0-indexed from Ashwini ───────
NAKSHATRA_ORDER: list[str] = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]
_NAKSHATRA_SPAN = 360.0 / 27.0  # 13.333...

# Gandanta pairs (BPHS/muhurta doctrine): the LAST pada of the water-ending
# nakshatra junctioning into the FIRST pada of the following fire-opening
# nakshatra. GANDANTA_TAIL = nakshatras whose PADA 4 is a gandanta zone;
# GANDANTA_HEAD = nakshatras whose PADA 1 is a gandanta zone.
_GANDANTA_TAIL = frozenset({"Ashlesha", "Jyeshtha", "Revati"})
_GANDANTA_HEAD = frozenset({"Magha", "Mula", "Ashwini"})

# Nakshatra lords cycle through the 9-graha Vimshottari sequence, 3x through
# 27 nakshatras — used only as a cross-check display, not re-derived here
# (the authoritative nakshatra_lord comes from the L1 fact).


def _degree_in_nakshatra(longitude_sidereal: float | None) -> float | None:
    if longitude_sidereal is None:
        return None
    lon = longitude_sidereal % 360.0
    return lon % _NAKSHATRA_SPAN


def _gandanta_flag(nakshatra: str | None, pada: int | None,
                    longitude_sidereal: float | None) -> tuple[bool, str]:
    """Returns (is_gandanta, zone_label). Classical zone: within the final
    ~48' (0.8 deg, roughly the last 1/4 of the last pada) of a GANDANTA_TAIL
    nakshatra, or the first ~48' of a GANDANTA_HEAD nakshatra."""
    if not nakshatra or pada is None:
        return False, "not_applicable"
    deg_in_nak = _degree_in_nakshatra(longitude_sidereal)
    threshold_deg = 0.8  # ~48 arcmin, the classical tight gandanta orb
    if nakshatra in _GANDANTA_TAIL and pada == 4:
        if deg_in_nak is not None and (_NAKSHATRA_SPAN - deg_in_nak) <= threshold_deg:
            return True, f"gandanta_tail_{nakshatra.lower().replace(' ', '_')}"
        return False, f"end_pada_{nakshatra.lower().replace(' ', '_')}"
    if nakshatra in _GANDANTA_HEAD and pada == 1:
        if deg_in_nak is not None and deg_in_nak <= threshold_deg:
            return True, f"gandanta_head_{nakshatra.lower().replace(' ', '_')}"
        return False, f"start_pada_{nakshatra.lower().replace(' ', '_')}"
    return False, "not_applicable"


def _fetch_facts(conn: Any, chart_id: str, aya: str) -> dict[str, dict]:
    """{fact_subject: {fact_key: {'text':..,'num':..,'fact_id':..}}} scoped to
    the categories this emitter reads (graha_position, graha_dispositor_chain,
    graha_tara_bala) for chart+ayanamsha."""
    rows = conn.execute(
        """SELECT fact_id, fact_category, fact_subject, fact_key,
                  fact_value_text, fact_value_num, fact_value_jsonb
           FROM chart_facts
           WHERE chart_id = %s AND ayanamsha_id = %s
             AND fact_category IN ('graha_position', 'graha_dispositor_chain',
                                    'graha_tara_bala')""",
        [chart_id, aya],
    ).fetchall()
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, dict):
            fid, cat, subj, key, vtext, vnum, vjsonb = (
                r["fact_id"], r["fact_category"], r["fact_subject"],
                r["fact_key"], r["fact_value_text"], r["fact_value_num"],
                r["fact_value_jsonb"],
            )
        else:
            fid, cat, subj, key, vtext, vnum, vjsonb = r[0], r[1], r[2], r[3], r[4], r[5], r[6]
        bucket = out.setdefault(f"{cat}:{subj}", {})
        bucket[key] = {"text": vtext, "num": vnum, "jsonb": vjsonb, "fact_id": fid}
    return out


def build_signal_row(
    *,
    chart_id: str,
    ayanamsha_id: str,
    build_id: str,
    graha_code: str,
    position_facts: dict,
    dispositor_facts: dict | None,
    tara_facts: dict | None,
    now: str,
) -> dict[str, Any] | None:
    """Build one bodha_msr_signals row for a graha's nakshatra-semantic
    profile. Returns None if the graha's own-star facts are missing."""
    nak_rec = position_facts.get("nakshatra")
    nak_lord_rec = position_facts.get("nakshatra_lord")
    pada_rec = position_facts.get("pada")
    lon_rec = position_facts.get("longitude_sidereal")
    house_rec = position_facts.get("house_d1")
    if not nak_rec or not nak_rec.get("text"):
        return None

    nakshatra = nak_rec["text"]
    nakshatra_lord = (nak_lord_rec or {}).get("text")
    pada = int(pada_rec["num"]) if pada_rec and pada_rec.get("num") is not None else None
    longitude_sidereal = float(lon_rec["num"]) if lon_rec and lon_rec.get("num") is not None else None
    house_d1 = int(house_rec["num"]) if house_rec and house_rec.get("num") is not None else None

    is_gandanta, gandanta_zone = _gandanta_flag(nakshatra, pada, longitude_sidereal)

    chain: list[str] = []
    chain_length = None
    cycle_detected = None
    dispositor_fact_id = None
    if dispositor_facts and "chain_jsonb_atomic" in dispositor_facts:
        rec = dispositor_facts["chain_jsonb_atomic"]
        j = rec.get("jsonb") or {}
        if isinstance(j, dict):
            chain = j.get("chain") or []
            chain_length = j.get("length")
            cycle_detected = j.get("cycle_detected_at_step")
        dispositor_fact_id = rec.get("fact_id")

    tara_name = tara_count = tara_position = None
    tara_fact_id = None
    if tara_facts:
        if "tara_name" in tara_facts:
            tara_name = tara_facts["tara_name"].get("text")
            tara_fact_id = tara_facts["tara_name"].get("fact_id")
        if "tara_count" in tara_facts:
            tv = tara_facts["tara_count"].get("num")
            tara_count = int(tv) if tv is not None else None
        if "tara_position" in tara_facts:
            tv = tara_facts["tara_position"].get("num")
            tara_position = int(tv) if tv is not None else None

    # Auspicious tara categories (classical 9-fold tara-chakra):
    # Janma/Vipat/Pratyak/Naidhana are cautionary; Sampat/Kshema/Sadhaka/
    # Mitra/Parama-mitra are favorable. tara_position is 1..9 by
    # construction (count-from-natal-Moon mod 9, 1-based).
    _INAUSPICIOUS_TARA_POS = frozenset({1, 3, 5, 7})  # Janma/Vipat/Pratyak/Naidhana
    tara_favorable = (tara_position is not None) and (tara_position not in _INAUSPICIOUS_TARA_POS)

    graha_display = _GRAHA_DISPLAY.get(graha_code, graha_code)

    config = {
        "graha": graha_display,
        "graha_code": graha_code,
        "nakshatra": nakshatra,
        "nakshatra_lord": nakshatra_lord,
        "pada": pada,
        "house_d1": house_d1,
        "dispositor_chain": chain,
        "dispositor_chain_length": chain_length,
        "dispositor_cycle_detected_at_step": cycle_detected,
        "tara_name": tara_name,
        "tara_count": tara_count,
        "tara_position": tara_position,
        "tara_favorable": tara_favorable,
        "gandanta_flag": is_gandanta,
        "gandanta_zone": gandanta_zone,
    }

    constituent_facts = [f for f in (
        (position_facts.get("nakshatra") or {}).get("fact_id"),
        (position_facts.get("nakshatra_lord") or {}).get("fact_id"),
        (position_facts.get("pada") or {}).get("fact_id"),
        (position_facts.get("longitude_sidereal") or {}).get("fact_id"),
        dispositor_fact_id,
        tara_fact_id,
    ) if f]

    # specificity: gandanta is a genuinely rare, classically-flagged extremity
    # — the ONE per-signal boost DR-6 explicitly reserves off the class prior.
    specificity = 1.4 if is_gandanta else (1.1 if tara_favorable is False else 1.0)
    valence = "malefic" if is_gandanta else ("benefic" if tara_favorable else "neutral")

    inputs = SalienceInputsV2(
        orb_tightness=1.0,
        shadbala_norm=1.0,
        dignity_score=0.50,
        house_number=house_d1 or 1,
        ashtakavarga_bindus=4,
        vargottama_amplification=0.0,
        neechabhanga_modifier=1.0,
        cancellation_modifier=1.0,
        verification_pass_status="documented_approximation",
        class_prior=NAKSHATRA_SEMANTIC_CLASS_PRIOR,
        varga_id="D1",
        specificity=specificity,
        bala_gate=None,
        functional_context=1.0,
        inputs_complete=True,
    )
    sal = salience_formula_v2(inputs)
    computed_salience = sal["computed_salience"]

    headline_bits = [f"{graha_display}: {nakshatra} pada {pada} (lord {nakshatra_lord})"]
    if chain:
        headline_bits.append(f"dispositor chain: {' -> '.join(chain)}")
    if tara_name:
        headline_bits.append(f"tara={tara_name}({'favorable' if tara_favorable else 'cautionary'})")
    if is_gandanta:
        headline_bits.append(f"GANDANTA ({gandanta_zone})")
    headline = " | ".join(headline_bits)

    summary = (
        f"category=nakshatra_semantic | graha={graha_display} | nakshatra={nakshatra} | "
        f"nakshatra_lord={nakshatra_lord} | pada={pada} | "
        f"dispositor_chain_length={chain_length} | tara_name={tara_name} | "
        f"tara_position={tara_position} | tara_favorable={tara_favorable} | "
        f"gandanta_flag={is_gandanta} | gandanta_zone={gandanta_zone}"
    )

    return {
        "signal_id": str(uuid.uuid4()),
        "chart_id": chart_id,
        "ayanamsha_id": ayanamsha_id,
        "build_id": build_id,
        "signal_type_id": f"nakshatra_semantic:{graha_code}",
        "signal_type_class": SIGNAL_TYPE_CLASS,
        "signal_tradition": "parashari",
        "fact_kind": "position",
        "source_l1_asset": "ga_nakshatra",
        "source_subsystem": NAKSHATRA_SEMANTIC_SUBSYSTEM,
        "signal_summary_text": summary,
        "signal_headline_text": headline,
        "classical_sources_jsonb": json.dumps({
            "catalog_ids": [], "rule_ids": [], "text_chunk_ids": [],
            "citations": ["BPHS nakshatra/dispositor doctrine",
                          "Muhurta gandanta junction doctrine (Ashlesha/Jyeshtha/"
                          "Revati -> Magha/Mula/Ashwini)",
                          "Tara-chakra 9-fold tara bala from natal Moon"],
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
        "domains_affected_array": ["character"],
        "domain_salience_jsonb": json.dumps({"character": computed_salience}),
        "shared_factor_keys_jsonb": None,
        "cross_domain_shared_factor_count": None,
        "graph_edge_pattern_jsonb": None,
        "graph_node_strength_contribution_jsonb": None,
        "relationship_classification": "gandanta" if is_gandanta else "standard",
        "graha_weakness_indicators_jsonb": None,
        "remedy_hooks_array": None,
        "recurring_pattern_marker": None,
        "top_k_salience_rank": None,
        "system_convergence_count": None,
        "signature_class": "planetary",
        "contradicts_signals_array": None,
        "active_duration_class": "natal_permanent",
        "active_dasha_periods_jsonb": None,
        "activation_predicted_dates_jsonb": None,
        "predicted_outcome_class": None,
        "cross_ayanamsha_consistency_score": None,
        "strength_normalized_to_chart_max": None,
        "pada_precision_flag": is_gandanta,
        "cross_system_consensus_count": None,
        "channel_render_priority_jsonb": None,
        "verification_pass_status": "documented_approximation",
        "verification_method": "l1_fact_composition_deterministic",
        "citation_ref": f"bo_nakshatra_semantic/{graha_code}",
        "citation_human": f"Nakshatra-semantic profile: {graha_display}",
        "computed_at": now,
        "engine_version": ENGINE_VERSION,
        "ratification_factor": None,
        "valence_source": "categorical_deterministic_v1",
    }
