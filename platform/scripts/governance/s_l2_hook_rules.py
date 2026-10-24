#!/usr/bin/env python3
"""Derivation of the S-L2 attribution hooks (rules + declared S-L1 deltas -> expected counts). No database, no network.

The hook files under 00_ARCHITECTURE/briefs/suvarna/exec/s_l2_attribution_hooks/l2/*.json are the OUTPUT of this module (`--write`), and
`__tests__/test_s_l2_hooks_expected_state.py` fails if a file and this module disagree. Nothing here is a measured count plus a margin:
every number is either (a) a production fact read once, on 2026-10-03, with a read-only login (BASE: row counts per table and category),
(b) a bound declared by an S-L1 hook (DELTAS: the largest number of L1 facts a declared change can add or remove, per downstream class),
or (c) a structural rule of the writers (RULES: which rows are keyed by a finite set, which cite re-keyed ids).
The record S_L2_ATTRIBUTION_HOOKS_v1_0.md explains each rule and says which one the rehearsal must confirm.

Usage:  python3 s_l2_hook_rules.py --write [DIR]   (default: the l2/ folder next to the other S-L2 hooks) ;  python3 s_l2_hook_rules.py --print
"""
from __future__ import annotations

import json
import pathlib
import sys

PR = "suvarna/land/TI-s-l2-prep-001"

# ------------------------------------------------------------------------------------------------------------- (a) BASE: production facts
# Canonical chart, read 2026-10-03 as suvarna_reader (one SELECT each). Per-category row counts as the flip detector's L2 registry reads them.
MSR = {  # bodha_msr_signals, signal_type_class -> rows (all five ayanamshas)
    "composite_state": 37694, "karaka_alignment": 6156, "sade_sati": 2871, "varga_pattern": 1400, "tradition_specific": 1169, "panchanga": 590,
    "annual": 315, "configuration": 150, "parivartana": 75, "yoga": 74, "nakshatra_semantic": 45, "sudarshana_agreement": 45, "dosha": 26,
    "arudha": 25, "special_lagna": 20, "dhana_axis": 10, "varga_ratification_divergence": 9, "vargottama_amplification": 4,
}
# Of the composite_state signals, how many cite ONLY facts whose id survives S-L1 (ga_positions: the one generation whose stored fact_id formula
# already excludes build_id). Every other class: 0 such signals; sudarshana_agreement and dhana_axis cite ga_positions facts only (read: n_stable_cite).
COMPOSITE_CITING_REKEYED = 36628
STABLE_CITE_ONLY_CLASSES = ("sudarshana_agreement", "dhana_axis")
CAT = {  # category -> rows, per table (all five ayanamshas)
    "bodha_cgm_nodes": {"arudha": 95, "bhava": 60, "domain": 65, "dosha": 16, "graha": 45, "special_lagna": 35, "yoga": 69},
    "bodha_cgm_edges": {"argala": 119, "arudha_house": 95, "aspect": 360, "bhava_aspect": 95, "dispositor": 40, "lordship": 60, "occupancy": 45, "special_lagna_house": 35},
    "bodha_cgm_paths": {"dispositor_chain": 45},
    "bodha_cgm_motifs": {"mutual_aspect": 180, "mutual_aspect_triangle": 420},
    "bodha_cgm_sub_graphs": {"connected_component": 5},
    "bodha_cgm_chart_topology_summary": {"topology": 5},
    "bodha_mechanisms": {"convergent_dispositor_chain": 5, "graha_bhava_affliction": 10, "mutual_aspect": 180, "mutual_aspect_triangle": 420},
    "bodha_contradictions": {"domain_promise_vs_denial": 15},
    "bodha_cdlm_cells": {"static_natal": 280},
    "bodha_convergence": {"static_natal": 60},
    "bodha_triangulation": {"career": 20, "character": 20, "education": 15, "family": 20, "health": 10, "progeny": 15, "relationship": 20, "residence": 15,
                            "spirituality": 20, "transition": 10, "travel": 15, "wealth": 15},
    "bodha_cdlm_chart_summary": {"summary": 5},
    "bodha_cdlm_domain_rollups": {"rollup": 60},
    "bodha_cdlm_pattern_clusters": {"unclassified_linkage_cluster": 5},
    "bodha_question_lenses": {"lens": 60},
    "bodha_chart_gestalt": {"gestalt": 5},
    "bodha_rm_resonances": {"static_natal": 45},
    "bodha_rm_remedy_prescriptions": {"charity": 50, "japa": 15, "mantra": 65, "puja": 5},
    "bodha_rm_chart_summary": {"summary": 5},
    "bodha_rm_dosha_remedy_bundles": {"bundle": 5},
    "bodha_rm_pattern_remedies": {"resonance": 45},
    "bodha_rm_dasha_windowed_prescriptions": {"vimshottari": 5},
    "bodha_pratijna": {"pratijna": 135},
    "bodha_discoveries": {"distributional_anomaly": 1127, "embedding_outlier": 34},
    "bodha_anomalies": {"distributional_anomaly": 3060, "embedding_outlier": 66, "low_salience_high_consequence": 150},
    "synthesis_quality_scorecard": {"scorecard": 1},
    "bodha_grounding_matches": {"msr_signal": 50678, "yoga_dosha_firing": 53},
}
AYAS = 5
DOMAINS = 13            # bodha_cgm_nodes node_type=domain: 13 per ayanamsha (CANONICAL_DOMAINS)
QUESTION_CLASSES = 12   # bodha_triangulation distinct question_class
TRADITIONS = 4          # bodha_triangulation distinct tradition (per ayanamsha)
VICHARA_CITING_EDGES = 754      # bodha_cgm_edges with a non-empty constituent_ga_vichara_ids_array
VICHARA_CITING_MECHANISMS = 605 # bodha_mechanisms with a non-empty constituent_ga_vichara_ids_array
ARGALA_EDGE_CAP_PER_AYA = 24    # bo_karanajala argala edges are capped at 24 per ayanamsha (W/bo_karanajala.py)

# ------------------------------------------------------------------------------------------------------------- (b) DELTAS: declared S-L1 changes
# Largest number of NEW L1 facts of each kind a declared S-L1 hook can add (an appeared fact yields AT MOST one new signal; collapse by identity only lowers it)
APPEARED_COMPOSITE = {
    "argala_graha_natal": 156, "ashtakavarga_bindu_contributor": 3360,
    "sensitive_point_gulika_mandi": 35, "geometry categories (45+30+315+85; optional on this chart)": 45 + 30 + 315 + 85, "graha_gandanta twin rows": 50,
}
APPEARED_COMPOSITE_PER_AYANAMSHA = {"dasha_scope_cap (1 INVARIANT fact, fanned out to every ayanamsha)": 1}
APPEARED_KARAKA = {"karaka_chara_position PUTRAKARAKA": 35, "strikaraka_alias": 5, "karaka_web_per_varga (upper end of 950..1,300)": 1300}
APPEARED_PARIVARTANA = {"parivartana_pairs (optional)": 15}
DISAPPEARED_COMPOSITE = {"sun_required_rupa: graha_in_house_composite_strength": 240}
DISAPPEARED_KARAKA = {"karaka_chara_position STRIKARAKA relabel": 35}
TIER_RELABELS = 19870 + 245 + 300  # facts re-tiered by the tiers lane (informational: the per-signal bound below is the signal count)


def _sum(d):
    return sum(d.values())


def _derived():
    """Totals computed from the inputs AT CALL TIME (so a changed input changes the output; the mutation tests rely on it).
    -> (M0 signals before, A_COMPOSITE, A_KARAKA, A_PARIV, D_COMPOSITE, D_KARAKA, A_TOTAL most new signals, D_TOTAL most removed signals, ALL_MSR, classes_13)"""
    a_c, a_k, a_p = _sum(APPEARED_COMPOSITE) + AYAS * _sum(APPEARED_COMPOSITE_PER_AYANAMSHA), _sum(APPEARED_KARAKA), _sum(APPEARED_PARIVARTANA)
    d_c, d_k = _sum(DISAPPEARED_COMPOSITE), _sum(DISAPPEARED_KARAKA)
    cls13 = [c for c in MSR if c not in ("composite_state", "karaka_alignment", "varga_ratification_divergence", *STABLE_CITE_ONLY_CLASSES)]
    return _sum(MSR), a_c, a_k, a_p, d_c, d_k, a_c + a_k + a_p, d_c + d_k, sorted(MSR), cls13


def E(table, cats, types, ec, note, optional=False):
    e = {"table": table, "categories": sorted(cats), "change_types": list(types)}
    if ec is not None:
        e["expected_count"] = ec
    if optional:
        e["optional"] = True
    e["note"] = note
    return e


def rows(table):
    return _sum(CAT[table])


def zero(table, cats, types, why):
    return E(table, cats, types, {"exact": 0}, why)


def upto(table, cats, types, hi, why, lo=0, optional=False):
    return E(table, cats, types, {"min": lo, "max": hi}, why, optional)


def open_(table, cats, types, why):
    """Attribution only: the writers fix no upper bound a rule can derive (min 0, optional)."""
    return E(table, cats, types, {"min": 0}, why, optional=True)


R = "Rule R"  # rules are numbered in S_L2_ATTRIBUTION_HOOKS_v1_0.md section 3


def lane_msr():
    M0, A_COMPOSITE, A_KARAKA, A_PARIV, D_COMPOSITE, D_KARAKA, A_TOTAL, D_TOTAL, ALL_MSR, cat13 = _derived()
    n13 = sum(MSR[c] for c in cat13)
    comp, kar = MSR["composite_state"], MSR["karaka_alignment"]
    all_class_tier = [c for c in ALL_MSR]
    return {
        "lane": "s_l2_msr_projection",
        "ruling": "S-L2 MSR projection (bo_laksana + five satellites)",
        "description": ("bodha_msr_signals after the S-L2 rebuild versus the S-L1-close snapshot. Row key (detector registry) = ayanamsha, signal_type_class, signal_type_id "
                        "(+ varga/fact_subject/fact_key); identity = signal_id and the digest of constituent_facts_array are CONTENT, so a re-keyed citation or a moved signal id "
                        "reads as a value change on the same key. Every count is derived from a rule (which L1 facts S-L1 re-keys; which declared S-L1 changes can add or remove "
                        "a projected fact; the writers' own projection) and from the production class counts of 2026-10-03; none is a measured count plus a margin. The "
                        "rehearsal must confirm each entry (HOOKS record section 6)."),
        "may_change": [
            E("bodha_msr_signals", cat13, ["value"], {"exact": n13},
              f"{len(cat13)} classes, every signal cites at least one fact S-L1 re-keys (read 2026-10-03: n_stable_cite = 0 for each), so every surviving signal changes its cites digest; no declared S-L1 change adds or removes a signal of these classes (rule: the declared appeared/disappeared facts map to composite_state, karaka_alignment and parivartana only, via bo_laksana._signal_type_class), so survivors = before count: "
              + "+".join(str(MSR[c]) for c in cat13) + ". Source: S_L2_ATTRIBUTION_HOOKS_v1_0.md section 3.1 (R1, R2)."),
            E("bodha_msr_signals", ["composite_state"], ["value"], {"min": COMPOSITE_CITING_REKEYED - D_COMPOSITE, "max": comp},
              f"{COMPOSITE_CITING_REKEYED:,} of {comp:,} signals cite a re-keyed fact ({comp - COMPOSITE_CITING_REKEYED:,} cite only ga_positions facts, whose ids survive); at most {D_COMPOSITE} composite signals disappear (sun_required_rupa: {D_COMPOSITE} graha_in_house_composite_strength facts); min = {COMPOSITE_CITING_REKEYED:,} - {D_COMPOSITE}; max = every signal. Source: section 3.1 (R1, R3)."),
            E("bodha_msr_signals", ["karaka_alignment"], ["value"], {"min": kar - D_KARAKA, "max": kar},
              f"All {kar:,} signals cite a re-keyed fact; at most {D_KARAKA} disappear (STRIKARAKA -> PUTRAKARAKA relabel); min = {kar:,} - {D_KARAKA}; max = all. Source: section 3.1 (R1, R3)."),
            E("bodha_msr_signals", list(STABLE_CITE_ONLY_CLASSES), ["value"], {"min": 0, "max": sum(MSR[c] for c in STABLE_CITE_ONLY_CLASSES)},
              "Their cited facts are ga_positions graha_position facts (ids survive S-L1) and their configurations hold discrete values only, so cites and identity do not move; only the bo_laksana_rerank enrichment digests can. 0 to all "
              + "+".join(str(MSR[c]) for c in STABLE_CITE_ONLY_CLASSES) + ". Source: section 3.1 (R2)."),
            E("bodha_msr_signals", ["composite_state"], ["appeared"], {"min": 0, "max": A_COMPOSITE},
              "Upper bound = every declared appeared fact that maps to composite_state yields at most one new signal: " + ", ".join(f"{k} {v:,}" for k, v in {**APPEARED_COMPOSITE, **{k: v * AYAS for k, v in APPEARED_COMPOSITE_PER_AYANAMSHA.items()}}.items())
              + ". Collapse by identity can only lower it. Source: section 3.1 and 3.2 (R3)."),
            E("bodha_msr_signals", ["composite_state"], ["disappeared"], {"min": 0, "max": D_COMPOSITE},
              f"Upper bound = the {D_COMPOSITE} graha_in_house_composite_strength facts that sun_required_rupa removes (simple_multiplication, cross_formula_divergence). Source: section 3.1 (R3)."),
            E("bodha_msr_signals", ["karaka_alignment"], ["appeared"], {"min": 0, "max": A_KARAKA},
              "karaka_chara_position +35 (PUTRAKARAKA) +5 (strikaraka_alias) and karaka_web_per_varga up to +1,300 (collapse by identity can only lower it). Source: section 3.1 (R3)."),
            E("bodha_msr_signals", ["karaka_alignment"], ["disappeared"], {"min": 0, "max": D_KARAKA},
              "karaka_chara_position STRIKARAKA -35. Source: section 3.1 (R3)."),
            E("bodha_msr_signals", ["parivartana"], ["appeared"], {"min": 0, "max": A_PARIV},
              "parivartana_pairs appeared, optional on this chart, max 15. Source: section 3.1 (R3)."),
            E("bodha_msr_signals", [c for c in ALL_MSR if c not in ("composite_state", "karaka_alignment", "parivartana", "varga_ratification_divergence")], ["appeared", "disappeared"], {"exact": 0},
              "No declared S-L1 change can create or remove a fact projected into these 14 classes on the canonical chart (the ephemeris move has no class flip there; the vichara dedupe touches only varga_ratification_divergence). Source: section 3.1 (R3)."),
            E("bodha_msr_signals", ["parivartana"], ["disappeared"], {"exact": 0},
              "Nothing removes a parivartana fact. Source: section 3.1 (R3)."),
            E("bodha_msr_signals", ["varga_ratification_divergence"], ["value", "appeared", "disappeared", "occurrence_count", "tier"], {"min": 0},
              "9 signals today (3 on three ayanamshas) from chart_vichara; the ga_vichara dedupe (8,524 -> 7,774 rows) can change them in either direction and no upper bound on appearances is derivable, so only the attribution is declared (min 0, no max). Source: section 3.1 (R4).",
              optional=True),
            E("bodha_msr_signals", all_class_tier, ["tier"], {"min": 0, "max": M0},
              f"verification_pass_status follows the cited facts' tiers; the tiers lane re-labels {TIER_RELABELS:,} facts; at most one tier change per signal ({M0:,} signals). Source: section 3.1 (R5)."),
            E("bodha_msr_signals", [c for c in ALL_MSR if c != "varga_ratification_divergence"], ["occurrence_count"], {"min": 0},
              "Signals whose semantic key repeats can change multiplicity when the identity collapse changes; no bound derivable, attribution only. Source: section 3.1 (R4).", optional=True),
        ],
    }


def lane_embeddings_grounding():
    M0, A_COMPOSITE, A_KARAKA, A_PARIV, D_COMPOSITE, D_KARAKA, A_TOTAL, D_TOTAL, ALL_MSR, _cls13 = _derived()
    t_e, t_g = "bodha_signal_embeddings", "bodha_grounding_matches"
    return {
        "lane": "s_l2_embeddings_grounding",
        "ruling": "S-L2 downstream of MSR: bo_samskara embeddings and bo_grounding matches",
        "description": ("One embedding per MSR signal (bo_samskara, 1:1; embedding_id derived from signal_id + model) and one grounding match per MSR signal plus one per fired yoga/dosha (bo_grounding). "
                        "Both tables therefore follow the MSR projection lane exactly in SET size: they can appear or disappear only where a signal does, so the bounds are the MSR appeared/disappeared bounds "
                        "(A_TOTAL, D_TOTAL), and a value change is bounded by the signal count. The embedding vector and the input summary enter the snapshot as 12-hex digests (the vendor call is not repeatable "
                        "byte for byte, which is why the value bound is the full row count, not a derived subset)."),
        "may_change": [
            E(t_e, ALL_MSR, ["appeared"], {"min": 0, "max": A_TOTAL}, f"An embedding exists only for a signal: at most the {A_TOTAL:,} signals the declared S-L1 changes can add (composite {A_COMPOSITE:,} + karaka {A_KARAKA:,} + parivartana {A_PARIV}). Source: section 3.3 (R6)."),
            E(t_e, ALL_MSR, ["disappeared"], {"min": 0, "max": D_TOTAL}, f"At most the {D_TOTAL} signals the declared S-L1 changes can remove (composite {D_COMPOSITE} + karaka {D_KARAKA}). Source: section 3.3 (R6)."),
            E(t_e, ALL_MSR, ["value"], {"min": 0, "max": M0}, f"embedding_id and the vector/input digests move with the signal id and the summary text; a surviving embedding changes only if its signal does; at most one per signal ({M0:,}). No lower bound: a signal whose id and summary are unchanged keeps an identical embedding. Source: section 3.3 (R6)."),
            E(t_e, ALL_MSR, ["occurrence_count"], {"min": 0}, "Several signals can share a key (class, model, signal type id); attribution only. Source: section 3.3 (R4).", optional=True),
            E(t_e, ALL_MSR, ["tier"], {"exact": 0}, "The registry carries no tier for the embeddings table (empty on both sides): a tier change cannot be read; declared zero so that none can ride. Source: section 3.3."),
            E(t_g, ["msr_signal"], ["appeared"], {"min": 0, "max": A_TOTAL}, f"One msr_signal match per signal: at most the {A_TOTAL:,} signals S-L1 can add. Source: section 3.3 (R6)."),
            E(t_g, ["msr_signal"], ["disappeared"], {"min": 0, "max": D_TOTAL}, f"At most the {D_TOTAL} signals S-L1 can remove. Source: section 3.3 (R6)."),
            E(t_g, ["msr_signal"], ["value"], {"min": 0, "max": CAT[t_g]["msr_signal"]}, f"target_id is the signal id and the chains/evidence digests follow the signal; at most one per match ({CAT[t_g]['msr_signal']:,}). Source: section 3.3 (R6)."),
            E(t_g, ["msr_signal"], ["tier"], {"min": 0, "max": CAT[t_g]["msr_signal"]}, "grounding_tier follows the rule match for the signal; at most one tier change per match. Source: section 3.3 (R5)."),
            E(t_g, ["msr_signal"], ["occurrence_count"], {"min": 0}, "Several signals share a (target kind, rule, signal type) key; attribution only. Source: section 3.3 (R4).", optional=True),
            E(t_g, ["yoga_dosha_firing"], ["value", "appeared", "disappeared", "tier", "occurrence_count"], {"min": 0},
              "The 53 firing matches follow ga_yoga_firings (id serial, re-created by the L1 rebuild); the yoga firings table is not read by the detector and no upper bound on its S-L1 effect is derivable: attribution only. Source: section 3.3 (R7).", optional=True),
        ],
    }


def lane_cgm_graph():
    n, e, p, m, sg, tp, mech, con = ("bodha_cgm_nodes", "bodha_cgm_edges", "bodha_cgm_paths", "bodha_cgm_motifs", "bodha_cgm_sub_graphs",
                                      "bodha_cgm_chart_topology_summary", "bodha_mechanisms", "bodha_contradictions")
    rn, re_ = rows(n), rows(e)
    argala_max = ARGALA_EDGE_CAP_PER_AYA * AYAS
    non_argala = [c for c in CAT[e] if c != "argala"]
    v_lo = VICHARA_CITING_EDGES - CAT[e]["argala"]
    return {
        "lane": "s_l2_cgm_graph",
        "ruling": "S-L2 Bodha graph: bo_bimba, bo_karanajala, bo_cgm_paths, bo_cgm_motifs, bo_yantra_mechanism",
        "description": ("The graph is a deterministic function of the MSR yoga/dosha classes and a few static structural facts. Node, edge, path and motif identities are derived from semantic keys "
                        "(node type + subject, edge type + endpoints), never from signal or fact ids, so they are stable; what moves is the CITED ids stored in arrays (fact ids, signal ids, chart_vichara ids), which "
                        "enter the snapshot as digests. Sets whose members are physically fixed (9 grahas, 12 bhavas, 13 domains per ayanamsha) carry an explicit zero claim for appeared/disappeared; sets that depend on "
                        "the MSR yoga/dosha membership are zero because no declared S-L1 change creates or removes a yoga/dosha signal on the canonical chart."),
        "may_change": [
            zero(n, CAT[n], ["appeared", "disappeared"], "Node set = 9 grahas + 12 bhavas + 13 domains per ayanamsha (fixed) + yoga/dosha nodes from the MSR yoga (74) and dosha (26) classes, which S-L1 cannot change (R3) + arudha/special_lagna nodes (write-once, ON CONFLICT DO NOTHING, never deleted). Source: section 3.4 (R8)."),
            upto(n, CAT[n], ["value"], rn, f"node text = id, dignity, domain, hub, MSR signal id digest, position digest, constituents digest, degrees; a moved MSR id or an ephemeris-shifted position changes it; at most every node ({rn}). Source: section 3.4 (R8)."),
            upto(n, CAT[n], ["tier"], rn, f"verification_pass_status; at most one change per node ({rn}). Source: section 3.4 (R5)."),
            zero(e, non_argala, ["appeared", "disappeared"], "Edge types other than argala come from static structure (sign lordship, occupancy, aspects, bhava aspects, arudha/special-lagna houses) and the fixed node set; the ephemeris move has no class flip on the canonical chart, so no edge appears or disappears. Source: section 3.4 (R8)."),
            upto(e, ["argala"], ["appeared"], argala_max, f"bo_karanajala caps argala edges at {ARGALA_EDGE_CAP_PER_AYA} per ayanamsha: {ARGALA_EDGE_CAP_PER_AYA} x {AYAS} = {argala_max}; the declared argala changes (argala_graha_natal +156, argala_natal_matrix value churn) can move the argala set within that cap. Source: section 3.4 (R8)."),
            upto(e, ["argala"], ["disappeared"], CAT[e]["argala"], f"At most the {CAT[e]['argala']} argala edges that exist. Source: section 3.4 (R8)."),
            upto(e, list(CAT[e]), ["value"], re_, f"The {VICHARA_CITING_EDGES} edges that cite chart_vichara ids all change (every post-S-L1 vichara row has a new id, S-L1 hooks section 8), less the argala edges that may disappear ({CAT[e]['argala']}): min {v_lo}; the 330 edges that cite chart_facts ids also change; max = every edge ({re_}). Source: section 3.4 (R9)."
                 , lo=v_lo),
            upto(e, list(CAT[e]), ["tier"], re_ + argala_max, f"verification_pass_status; at most one change per edge ({re_} + up to {argala_max} argala). Source: section 3.4 (R5)."),
            zero(p, CAT[p], ["appeared", "disappeared", "value"], "One dispositor chain per graha node per ayanamsha (9 x 5 = 45). Path identity and the node/edge chains are digests of stable deterministic ids; chain length, final-dispositor flag and convergence count come from static sign lordship. Strength is a continuous score, not a class. Source: section 3.4 (R8)."),
            upto(p, CAT[p], ["tier"], rows(p), "verification_pass_status; at most one change per path. Source: section 3.4 (R5)."),
            zero(m, CAT[m], ["appeared", "disappeared", "value"], "Motifs are structural detectors over the (stable) edge set: mutual_aspect pairs and triangles. Identity = fingerprint hash of stable node ids; involved node/edge digests are stable. Source: section 3.4 (R8)."),
            upto(m, CAT[m], ["tier"], rows(m), "verification_pass_status; at most one change per motif. Source: section 3.4 (R5)."),
            zero(sg, CAT[sg], ["value"], "Node/edge id digests of the connected component and its centroid are stable. Source: section 3.4 (R8)."),
            open_(sg, CAT[sg], ["appeared", "disappeared"], "The number of connected components is a graph property no rule bounds; attribution only. Source: section 3.4."),
            upto(sg, CAT[sg], ["tier"], rows(sg), "verification_pass_status; at most one per sub-graph. Source: section 3.4 (R5)."),
            zero(tp, CAT[tp], ["appeared", "disappeared"], "One topology summary per ayanamsha (5). Source: section 3.4 (R8)."),
            upto(tp, CAT[tp], ["value"], rows(tp), "The hub jsonb carries centrality scores, so its digest can move with the strengths; at most one per ayanamsha. Source: section 3.4 (R8)."),
            upto(tp, CAT[tp], ["tier"], rows(tp), "verification_pass_status. Source: section 3.4 (R5)."),
            zero(mech, CAT[mech], ["appeared", "disappeared"], "Mechanisms promote the (stable) motifs (420 + 180), plus 10 graha_bhava_affliction and 5 convergent_dispositor_chain: stable keys and stable member ids. Source: section 3.4 (R8)."),
            upto(mech, CAT[mech], ["value"], rows(mech), f"{VICHARA_CITING_MECHANISMS} of {rows(mech)} mechanisms cite chart_vichara ids, which all change: min {VICHARA_CITING_MECHANISMS}, max every mechanism. Source: section 3.4 (R9).", lo=VICHARA_CITING_MECHANISMS),
            upto(mech, CAT[mech], ["tier"], rows(mech), "verification_pass_status. Source: section 3.4 (R5)."),
            zero(con, CAT[con], ["appeared", "disappeared"], "Contradictions are yoga-vs-dosha pairs sharing a domain and graha (3 per ayanamsha); the yoga/dosha signal sets cannot change (R3), and the key is the two signal TYPE ids. Source: section 3.4 (R8)."),
            upto(con, CAT[con], ["value"], rows(con), "contradiction_id and the a/b columns are signal ids; they move when either signal's id moves; at most every pair. Source: section 3.4 (R6)."),
            upto(con, CAT[con], ["tier"], rows(con), "verification_pass_status. Source: section 3.4 (R5)."),
        ],
    }


def lane_cdlm_sangati():
    cells, conv, tri, cs, ro, pc, ql, ge = ("bodha_cdlm_cells", "bodha_convergence", "bodha_triangulation", "bodha_cdlm_chart_summary", "bodha_cdlm_domain_rollups",
                                           "bodha_cdlm_pattern_clusters", "bodha_question_lenses", "bodha_chart_gestalt")
    grid_cells = DOMAINS * DOMAINS * AYAS
    grid_dom = DOMAINS * AYAS
    grid_tri = QUESTION_CLASSES * TRADITIONS * AYAS
    return {
        "lane": "s_l2_cdlm_sangati",
        "ruling": "S-L2 Bodha synthesis: bo_sangati, bo_cdlm_summary, bo_drishti, bo_chart_gestalt",
        "description": ("These tables aggregate the MSR signals by domain/question and store arrays of signal ids (hundreds of thousands of cites). The sets are indexed by finite grids (13 domains, 12 question "
                        "classes, 4 traditions, 5 ayanamshas), so the number of rows that can ever exist is bounded by the grid, whatever S-L1 does; the grids' current occupation is smaller, which is where the appeared "
                        "bounds come from. A value change is bounded by the row count: a row changes only if a cited signal's id or a strength moves, and signal ids move only where the MSR lane declares it."),
        "may_change": [
            upto(cells, CAT[cells], ["appeared"], grid_cells - rows(cells), f"Row key = ordered domain pair (13 x 13) per ayanamsha: at most {DOMAINS} x {DOMAINS} x {AYAS} = {grid_cells} cells, {rows(cells)} exist. Source: section 3.5 (R10)."),
            upto(cells, CAT[cells], ["disappeared"], rows(cells), "At most the cells that exist. Source: section 3.5 (R10)."),
            upto(cells, CAT[cells], ["value"], rows(cells), "Shared-signal-id digest and counts move with the cited signals; at most every cell. Source: section 3.5 (R6)."),
            upto(cells, CAT[cells], ["tier"], rows(cells), "verification_pass_status. Source: section 3.5 (R5)."),
            upto(conv, CAT[conv], ["appeared"], grid_dom - rows(conv), f"Row key = domain per ayanamsha: at most {grid_dom}; {rows(conv)} exist. Source: section 3.5 (R10)."),
            upto(conv, CAT[conv], ["disappeared"], rows(conv), "At most the rows that exist. Source: section 3.5 (R10)."),
            upto(conv, CAT[conv], ["value"], rows(conv), "Top-signal-id digest and counts; at most every row. Source: section 3.5 (R6)."),
            upto(conv, CAT[conv], ["tier"], rows(conv), "verification_pass_status. Source: section 3.5 (R5)."),
            upto(tri, CAT[tri], ["appeared"], grid_tri - rows(tri), f"Row key = question class x tradition per ayanamsha: at most {QUESTION_CLASSES} x {TRADITIONS} x {AYAS} = {grid_tri}; {rows(tri)} exist. Source: section 3.5 (R10)."),
            upto(tri, CAT[tri], ["disappeared"], rows(tri), "At most the rows that exist. Source: section 3.5 (R10)."),
            upto(tri, CAT[tri], ["value"], rows(tri), "Signal-id digest and verdict-input digest; at most every row. Source: section 3.5 (R6)."),
            zero(tri, CAT[tri], ["occurrence_count"], "The key (question class, tradition) is unique per ayanamsha: no multiplicity change is possible. Source: section 3.5."),
            zero(cs, CAT[cs], ["appeared", "disappeared"], "One summary per ayanamsha (5). Source: section 3.5 (R8)."),
            upto(cs, CAT[cs], ["value"], rows(cs), "Dominant/weakest domain arrays and cluster markers move with the signals. Source: section 3.5 (R6)."),
            upto(cs, CAT[cs], ["tier"], rows(cs), "verification_pass_status. Source: section 3.5 (R5)."),
            upto(ro, CAT[ro], ["appeared"], grid_dom - rows(ro), f"Row key = domain per ayanamsha: at most {grid_dom}; {rows(ro)} exist. Source: section 3.5 (R10)."),
            upto(ro, CAT[ro], ["disappeared"], rows(ro), "At most the rows that exist. Source: section 3.5 (R10)."),
            upto(ro, CAT[ro], ["value"], rows(ro), "Counts and arrays move with the signals. Source: section 3.5 (R6)."),
            upto(ro, CAT[ro], ["tier"], rows(ro), "verification_pass_status. Source: section 3.5 (R5)."),
            open_(pc, CAT[pc], ["appeared", "disappeared"], "Pattern clusters come from a graph clustering of the cells; their number is not bounded by a rule; attribution only. Source: section 3.5."),
            upto(pc, CAT[pc], ["value"], rows(pc), "Involved cell/signal digests; at most every cluster. Source: section 3.5 (R6)."),
            upto(pc, CAT[pc], ["tier"], rows(pc), "verification_pass_status. Source: section 3.5 (R5)."),
            zero(ql, CAT[ql], ["appeared", "disappeared", "occurrence_count"], "12 question types x 5 ayanamshas = 60, a fixed template list. Source: section 3.5 (R8)."),
            upto(ql, CAT[ql], ["value"], rows(ql), "Ranked relevant-signal and element digests carry signal ids; at most every lens. Source: section 3.5 (R6)."),
            upto(ql, CAT[ql], ["tier"], rows(ql), "verification_pass_status. Source: section 3.5 (R5)."),
            zero(ge, CAT[ge], ["appeared", "disappeared"], "One gestalt per ayanamsha (5). Source: section 3.5 (R8)."),
            upto(ge, CAT[ge], ["value"], rows(ge), "Threads/dynamics/pivot digests carry signal ids; at most one per ayanamsha. Source: section 3.5 (R6)."),
        ],
    }


def lane_remedy_discovery_misc():
    res, pre, rs, bu, pr, dw, pj, di, an, sc = ("bodha_rm_resonances", "bodha_rm_remedy_prescriptions", "bodha_rm_chart_summary", "bodha_rm_dosha_remedy_bundles",
                                               "bodha_rm_pattern_remedies", "bodha_rm_dasha_windowed_prescriptions", "bodha_pratijna", "bodha_discoveries",
                                               "bodha_anomalies", "synthesis_quality_scorecard")
    return {
        "lane": "s_l2_remedy_discovery_misc",
        "ruling": "S-L2 Bodha remedies, pratijna, discoveries, anomalies, scorecard: bo_upaya, bo_pratijna, bo_anveshana, bo_pramana_mapa",
        "description": ("Remedy tables are keyed by graha / remedy catalogue / dosha class (finite, static for the chart); pratijna is keyed by event class x ayanamsha (27 x 5); discoveries and anomalies are "
                        "data-dependent lists with no natural key, re-keyed one hundred percent because their ids embed signal ids. bo_upaya deletes the legacy dasha-windowed table and never writes it again, "
                        "so its five rows disappear exactly."),
        "may_change": [
            zero(res, CAT[res], ["appeared", "disappeared"], "9 grahas x 5 ayanamshas = 45, a fixed set. Source: section 3.6 (R8)."),
            upto(res, CAT[res], ["value"], rows(res), "Scores are continuous (not a class); the class flags, rank and the digests of doshas/motifs/cells move with the strengths and the cited ids; at most every row. Source: section 3.6 (R6)."),
            upto(res, CAT[res], ["tier"], rows(res), "verification_pass_status. Source: section 3.6 (R5)."),
            open_(pre, CAT[pre], ["appeared", "disappeared"], "The prescription set depends on the resonance match scores (thresholds); no rule bounds it; attribution only. Source: section 3.6."),
            upto(pre, CAT[pre], ["value"], rows(pre) * 2, "A prescription changes if its resonance, strength or detail digest does; it can also be re-created (paired); bounded by twice the rows. Source: section 3.6.", optional=True),
            upto(pre, CAT[pre], ["tier"], rows(pre) * 2, "verification_pass_status. Source: section 3.6 (R5).", optional=True),
            zero(rs, CAT[rs], ["appeared", "disappeared"], "One summary per ayanamsha. Source: section 3.6 (R8)."),
            upto(rs, CAT[rs], ["value"], rows(rs), "Top-resonance and top-prescription digests; at most one per ayanamsha. Source: section 3.6 (R6)."),
            upto(rs, CAT[rs], ["tier"], rows(rs), "verification_pass_status. Source: section 3.6 (R5)."),
            open_(bu, CAT[bu], ["appeared", "disappeared"], "One bundle per active dosha class; the active set is static (R3) but not rule-bounded here; attribution only. Source: section 3.6."),
            upto(bu, CAT[bu], ["value"], rows(bu), "Prescription-id digests. Source: section 3.6 (R6)."),
            upto(bu, CAT[bu], ["tier"], rows(bu), "verification_pass_status. Source: section 3.6 (R5)."),
            open_(pr, CAT[pr], ["appeared", "disappeared"], "Pattern remedies follow resonances/motifs/cells; attribution only. Source: section 3.6."),
            upto(pr, CAT[pr], ["value"], rows(pr), "Prescription-id digest. Source: section 3.6 (R6)."),
            upto(pr, CAT[pr], ["tier"], rows(pr), "verification_pass_status. Source: section 3.6 (R5)."),
            E(dw, CAT[dw], ["disappeared"], {"exact": rows(dw)}, f"bo_upaya deletes this table (replace_prior_rm_dasha_windowed) and the producer is a tombstone: the {rows(dw)} legacy rows disappear exactly. Source: section 3.6 (R11)."),
            zero(dw, CAT[dw], ["appeared", "value"], "Nothing writes this table. Source: section 3.6 (R11)."),
            upto(pj, CAT[pj], ["value"], rows(pj), f"The derivation digest holds chart_divisionals ids (all {rows(pj)} rows carry one; the F-A2 rebuild regenerates every id) and chart_facts ids; a row whose status also flips reads as disappeared + appeared instead. Source: section 3.6 (R12)."),
            upto(pj, CAT[pj], ["appeared"], rows(pj), "The status is part of the key (a status flip is one disappeared + one appeared); 27 event classes x 5 ayanamshas = 135 rows always exist, so at most 135 appear and the same number disappear. Source: section 3.6 (R12)."),
            upto(pj, CAT[pj], ["disappeared"], rows(pj), "As above: equal in number to the rows that appeared (the row set is fixed). Source: section 3.6 (R12)."),
            zero(pj, CAT[pj], ["tier", "occurrence_count"], "The pratijna registry entry carries no tier, and (ayanamsha, event class) is unique. Source: section 3.6."),
            open_(di, CAT[di], ["appeared", "disappeared"], "Discoveries are data-dependent anomalies/outliers over the MSR set with no natural key; attribution only. Source: section 3.6 (R13)."),
            upto(di, CAT[di], ["value"], rows(di), "discovery_id embeds the cited signal ids; at most every row. Source: section 3.6 (R13)."),
            open_(di, CAT[di], ["occurrence_count"], "Many rows share a semantic key; attribution only. Source: section 3.6 (R13)."),
            open_(an, CAT[an], ["appeared", "disappeared"], "Anomalies are data-dependent with no natural key; attribution only. Source: section 3.6 (R13)."),
            upto(an, CAT[an], ["value"], rows(an), "anomaly_id embeds the subject reference (a signal id); at most every row. Source: section 3.6 (R13)."),
            open_(an, CAT[an], ["occurrence_count"], "Many rows share a semantic key; attribution only. Source: section 3.6 (R13)."),
            zero(sc, CAT[sc], ["appeared", "disappeared"], "One scorecard row per chart (bo_pramana_mapa deletes and re-inserts it). Source: section 3.6 (R8)."),
            upto(sc, CAT[sc], ["value"], rows(sc), "Counts, flags and gate results can change (counts of signals, embeddings, cells, orphan references); the percentages are continuous scores. Source: section 3.6."),
        ],
    }


LANES = {
    "s_l2_msr_projection": lane_msr,
    "s_l2_embeddings_grounding": lane_embeddings_grounding,
    "s_l2_cgm_graph": lane_cgm_graph,
    "s_l2_cdlm_sangati": lane_cdlm_sangati,
    "s_l2_remedy_discovery_misc": lane_remedy_discovery_misc,
}


def build(lane):
    h = LANES[lane]()
    h["pr"] = PR
    return {k: h[k] for k in ("lane", "ruling", "pr", "description", "may_change")}


def render(lane):
    return json.dumps(build(lane), indent=2, ensure_ascii=False) + "\n"


def default_dir():
    here = pathlib.Path(__file__).resolve()
    return here.parents[3] / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec" / "s_l2_attribution_hooks" / "l2"


def main(argv):
    if "--print" in argv:
        for lane in LANES:
            print(f"{lane}: {len(build(lane)['may_change'])} entries")
        return 0
    if "--write" in argv:
        rest = [a for a in argv if a != "--write"]
        out = pathlib.Path(rest[0]) if rest else default_dir()
        out.mkdir(parents=True, exist_ok=True)
        for lane in LANES:
            (out / f"{lane}.json").write_text(render(lane), encoding="utf-8")
            print("wrote", out / f"{lane}.json")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
