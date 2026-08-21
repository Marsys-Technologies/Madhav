"""Versioned, pure, unit-tested formula functions for L2 Bodha.

All functions are deterministic: same inputs → same output, always.
No I/O, no randomness, no external state.

Versions are embedded in the function name and in a VERSION_* constant so
writers can stamp rows with the formula version they used.  When a formula
changes, bump the version (v1 → v2), add a new function, keep the old one
for backward compat during a transition build.

Spec references:
  salience_formula_v1     — A10 §4
  linkage_formula_v1      — A11 §3
  resonance_score_v1      — A13 §3
  resonance_match_score_v1 — A13 §3
  convergence_formula_v1  — Campaign §13.1 (new; not in A10/A11 — native sign-off
                             required before bo_sangati brief is authored)
  centrality_formula_v1   — Campaign §13.1 (new; native sign-off required before
                             bo_karanajala brief is authored)
  remedy_leverage_join_v1 — Doctrine Wave D-4b, BRIEF_D4B.md §1 Lane B-4
                             (Remedy-leverage join = v2.0 Lane C-5): leverage_index
                             (L1 ga_vichara, referenced not recomputed) x sadhana
                             history (LEL life_events, pre-embargo only) x dasha
                             runway (fresh L1 chart_dashas re-derivation).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
# Version constants — writers stamp these on each row
# ──────────────────────────────────────────────────────────────────────────────

VERSION_SALIENCE_FORMULA = "v1.0"
VERSION_LINKAGE_FORMULA = "v1.0"
VERSION_RESONANCE_FORMULA = "v1.0"
VERSION_RESONANCE_MATCH_FORMULA = "v1.0"
VERSION_CONVERGENCE_FORMULA = "v1.0"
VERSION_CENTRALITY_FORMULA = "v1.0"
VERSION_REMEDY_LEVERAGE_JOIN_FORMULA = "v1.0"


# ──────────────────────────────────────────────────────────────────────────────
# A10 §4  salience_formula_v1
# ──────────────────────────────────────────────────────────────────────────────

# Dignity score lookup (A10 §4 table)
#
# F-62: the canonical key is "moolatrikona" — the spelling
# `brahmagyan.dignity_oracle.classify_dignity` actually emits and the spelling
# stored in `chart_facts.graha_dignity_per_varga`. This table previously carried
# only "mooltrikona" (no 'a'), so every moolatrikona graha missed the lookup and
# fell to the caller's 0.50 neutral default — scoring BELOW the plain "own"
# (0.85) it would have received before the oracle learned the tier at all.
# "mooltrikona" is retained as a same-valued legacy alias so any historic caller
# still passing that string does not regress; nothing emits it.
DIGNITY_SCORE: dict[str, float] = {
    "exalted":       1.00,
    "moolatrikona":  0.95,
    "mooltrikona":   0.95,   # legacy alias — not emitted; see F-62 note above
    "own":           0.85,
    "friend":        0.65,
    "neutral":       0.50,
    "enemy":         0.35,
    "debilitated":   0.10,
}

# House weight multiplier (A10 §4 table)
# Houses 1/4/5/7/9/10 are kendra/trikona; 3/6/10/11 upachaya; 6/8/12 dusthana.
# House 10 appears in both upachaya and kendra — kendra value wins per spec
# ("kendra+trikona (1) = 1.30").
HOUSE_WEIGHT: dict[int, float] = {
    1: 1.30,   # kendra + trikona
    5: 1.20,   # trikona
    9: 1.20,   # trikona
    4: 1.15,   # kendra
    7: 1.15,   # kendra
    10: 1.15,  # kendra (overrides upachaya)
    3: 1.05,   # upachaya
    6: 0.90,   # upachaya ∩ dusthana → dusthana wins
    11: 1.05,  # upachaya
    8: 0.90,   # dusthana
    12: 0.90,  # dusthana
    2: 1.00,   # other
}

# Ashtakavarga support multiplier (A10 §4 table)
def _av_multiplier(bindus: int) -> float:
    if bindus >= 7:
        return 1.15
    if bindus >= 5:
        return 1.05
    if bindus >= 3:
        return 1.00
    if bindus >= 1:
        return 0.85
    return 0.70


@dataclass
class SalienceInputs:
    """All deterministic inputs for salience_formula_v1.

    Callers supply only what applies to the signal; unset fields default to
    neutral (no boost, no penalty).
    """
    # Core strength decomposition
    orb_tightness: float = 1.0          # [0,1]; 1 = exact, 0 = at max orb
    shadbala_norm: float = 1.0          # shadbala_total / required, capped at 2.0
    dignity_score: float = 0.50         # use DIGNITY_SCORE[state] or pass raw

    # Verification certainty (from classical sources)
    source_corroboration_count_by_text: int = 1   # distinct texts confirming

    # Activation context
    dasha_activation_proximity_score: float = 0.0  # 0..1 across 7 dasha systems
    house_number: int = 2                           # house the primary graha occupies
    ashtakavarga_bindus: int = 4                    # bindu count for that house

    # Modifiers
    aspect_modifier: float = 0.0            # 0..0.30
    vargottama_amplification: float = 0.0   # 0 / 0.20 / 0.50
    argala_modifier: float = 0.0            # 0..0.20
    neechabhanga_modifier: float = 1.0      # 1.0 normal / 1.3 cancelled debility
    cancellation_modifier: float = 1.0      # 1.0 normal / 0.1 cancelled yoga

    # Pre-computed optional overrides (set to override table lookups above)
    house_weight_multiplier_override: float | None = None
    ashtakavarga_support_multiplier_override: float | None = None


def salience_formula_v1(s: SalienceInputs) -> dict[str, float]:
    """A10 §4 salience formula v1.0.

    Returns a dict with all intermediate components AND the final
    computed_salience so callers can store decomposed columns.
    """
    # Component 1: deterministic structural strength
    deterministic_strength = s.orb_tightness * s.shadbala_norm * s.dignity_score

    # Component 2: verification certainty (logarithmic; capped at 1.0)
    verification_certainty = min(
        math.log(1 + s.source_corroboration_count_by_text) / math.log(10),
        1.0,
    )

    # Multipliers (use override if provided, else table lookup)
    house_wt = (
        s.house_weight_multiplier_override
        if s.house_weight_multiplier_override is not None
        else HOUSE_WEIGHT.get(s.house_number, 1.00)
    )
    av_mult = (
        s.ashtakavarga_support_multiplier_override
        if s.ashtakavarga_support_multiplier_override is not None
        else _av_multiplier(s.ashtakavarga_bindus)
    )

    computed_salience = (
        deterministic_strength
        * verification_certainty
        * (1 + s.dasha_activation_proximity_score * 0.5)
        * house_wt
        * av_mult
        * (1 + s.aspect_modifier)
        * (1 + s.vargottama_amplification)
        * (1 + s.argala_modifier)
        * s.neechabhanga_modifier
        * s.cancellation_modifier
    )

    return {
        "deterministic_strength": round(deterministic_strength, 6),
        "verification_certainty": round(verification_certainty, 6),
        "house_weight_multiplier": round(house_wt, 6),
        "ashtakavarga_support_multiplier": round(av_mult, 6),
        "computed_salience": round(computed_salience, 6),
        "salience_formula_version": VERSION_SALIENCE_FORMULA,
    }


# ──────────────────────────────────────────────────────────────────────────────
# A11 §3  linkage_formula_v1
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class LinkageInputs:
    shared_signals: list[dict] = field(default_factory=list)
    # Each signal dict: {salience: float, in_contradiction: bool}
    high_convergence_count: int = 0       # signals with cross_ayanamsha_consistency_score >= 0.8
    shared_factor_count: int = 0
    cross_ayanamsha_stability_score: float = 1.0


def linkage_formula_v1(cell: LinkageInputs) -> dict[str, float]:
    """A11 §3 linkage formula v1.0."""
    positive = sum(
        s["salience"] for s in cell.shared_signals if not s.get("in_contradiction", False)
    )
    negative = sum(
        s["salience"] for s in cell.shared_signals if s.get("in_contradiction", False)
    ) * 0.5
    net = positive - negative

    signal_count = max(len(cell.shared_signals), 1)
    high_convergence_bonus = (cell.high_convergence_count / signal_count) * 0.3
    factor_density_bonus = math.log(1 + cell.shared_factor_count) * 0.1
    stability_factor = max(cell.cross_ayanamsha_stability_score, 0.0)

    computed_linkage = (
        net
        * (1 + factor_density_bonus)
        * (1 + high_convergence_bonus)
        * stability_factor
    )

    return {
        "positive_contribution": round(positive, 6),
        "negative_contribution": round(negative * 0.5 * 2, 6),  # stored as gross
        "net_linkage_strength": round(net, 6),
        "computed_linkage_strength": round(computed_linkage, 6),
        "linkage_formula_version": VERSION_LINKAGE_FORMULA,
    }


# ──────────────────────────────────────────────────────────────────────────────
# A13 §3  resonance_score_v1  (graha weakness score)
# ──────────────────────────────────────────────────────────────────────────────

# Chara karaka amplification map
CHARA_KARAKA_AMP: dict[str, float] = {
    "AK":  1.30,
    "AmK": 1.15,
    "BK":  1.10,
    "MK":  1.05,
    "PK":  1.05,
    "PiK": 1.05,
    "DK":  1.10,
}


@dataclass
class ResonanceInputs:
    # From A8 T1 structural
    shadbala_normalized: float = 0.5       # 0..1
    bhava_bala_normalized: float = 0.5
    combustion_score: float = 0.0          # 0..1; 1 = fully combust
    debility_score: float = 0.0            # 0..1; 1 = fully debilitated
    affliction_count_normalized: float = 0.0
    cancellation_burden: float = 0.0       # 0..1; cancelled benefic effects
    dispositor_chain_weakness: float = 0.0 # 0..1
    vargottama_absence_score: float = 0.0  # 0..1; 1 = not vargottama at all
    dasha_proximity_activation_score: float = 0.0  # 0..1

    # From MSR, CDLM, CGM
    msr_signals_in_conflict: float = 0.0  # normalized sum of saliences in conflict
    cdlm_weakest_constituent_count: float = 0.0  # normalized
    cgm_motifs_weakest_node: float = 0.0          # normalized

    # Karaka flags
    is_yoga_karaka: bool = False
    chara_role: str | None = None  # AK | AmK | BK | MK | PK | PiK | DK | None


def resonance_score_v1(g: ResonanceInputs) -> dict[str, float]:
    """A13 §3 resonance score v1.0 (graha weakness / remedy candidacy)."""
    weakness_score = (
        (1.0 - g.shadbala_normalized) * 0.30
        + (1.0 - g.bhava_bala_normalized) * 0.15
        + g.combustion_score * 0.10
        + g.debility_score * 0.10
        + g.affliction_count_normalized * 0.10
        + g.cancellation_burden * 0.10
        + g.dispositor_chain_weakness * 0.05
        + g.vargottama_absence_score * 0.05
        + g.dasha_proximity_activation_score * 0.05
    )

    contradiction_factor = min(g.msr_signals_in_conflict, 1.0)
    domain_burden = min(g.cdlm_weakest_constituent_count, 1.0)
    motif_burden = min(g.cgm_motifs_weakest_node, 1.0)

    yoga_karaka_amp = 1.20 if g.is_yoga_karaka else 1.0
    chara_amp = CHARA_KARAKA_AMP.get(g.chara_role or "", 1.0)

    resonance = (
        weakness_score
        * (1 + contradiction_factor * 0.20)
        * (1 + domain_burden * 0.15)
        * (1 + motif_burden * 0.10)
        * yoga_karaka_amp
        * chara_amp
    )

    return {
        "weakness_score": round(weakness_score, 6),
        "contradiction_factor": round(contradiction_factor, 6),
        "domain_burden": round(domain_burden, 6),
        "motif_burden": round(motif_burden, 6),
        "resonance_score": round(resonance, 6),
        "resonance_score_formula_version": VERSION_RESONANCE_FORMULA,
    }


# ──────────────────────────────────────────────────────────────────────────────
# A13 §3  resonance_match_score_v1  (how well a prescription fits a target)
# ──────────────────────────────────────────────────────────────────────────────

# Typology bias matrix — (typology, remedy_category) → bias multiplier.
# Partial representation; extend as G27 corpus is built.
TYPOLOGY_BIAS_MATRIX: dict[tuple[str, str], float] = {
    ("career_dominant",        "mantra"):           0.10,
    ("career_dominant",        "gem"):              0.15,
    ("career_dominant",        "yantra"):           0.10,
    ("spirituality_focused",   "mantra"):           0.20,
    ("spirituality_focused",   "tantric_heavy"):    0.15,
    ("relationship_centric",   "dana"):             0.15,
    ("relationship_centric",   "color"):            0.10,
    ("balanced",               "mantra"):           0.05,
    ("fragmented",             "mantra"):           0.05,
}


@dataclass
class ResonanceMatchInputs:
    classical_strength_for_graha: float = 0.5   # 0..1; from G27
    chart_typology: str = "balanced"
    remedy_category: str = "mantra"
    cross_tradition_corroboration_count: int = 1
    targets_motif_id: str | None = None
    active_motif_ids: set[str] = field(default_factory=set)
    has_active_counter_indication: bool = False


def resonance_match_score_v1(p: ResonanceMatchInputs) -> dict[str, float]:
    """A13 §3 resonance-match score v1.0."""
    base = p.classical_strength_for_graha
    typology_bias = TYPOLOGY_BIAS_MATRIX.get((p.chart_typology, p.remedy_category), 0.0)
    cross_tradition_boost = math.log(1 + p.cross_tradition_corroboration_count) * 0.10
    pattern_alignment = (
        0.15
        if p.targets_motif_id and p.targets_motif_id in p.active_motif_ids
        else 0.0
    )
    cancellation_penalty = 0.5 if p.has_active_counter_indication else 1.0

    score = (
        base
        * (1 + typology_bias)
        * (1 + cross_tradition_boost + pattern_alignment)
        * cancellation_penalty
    )

    return {
        "resonance_match_score": round(score, 6),
        "match_score_formula_version": VERSION_RESONANCE_MATCH_FORMULA,
    }


# ──────────────────────────────────────────────────────────────────────────────
# §13.1  convergence_formula_v1
# Computes the convergence score for a (chart, domain) pair — the weight of
# evidence from N independent L1 signals converging on one domain.
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ConvergenceInputs:
    domain: str
    signal_saliencies: list[float] = field(default_factory=list)
    # Per-signal tradition labels (must parallel signal_saliencies)
    signal_traditions: list[str] = field(default_factory=list)
    contradiction_count: int = 0   # contradictions within this domain's signal pool


def convergence_formula_v1(c: ConvergenceInputs) -> dict[str, Any]:
    """§13.1 convergence formula v1.0.

    convergence_score = (N × salience_weighted_mean × cross_tradition_multiplier)
                        × contradiction_penalty

    Rationale:
      - N (convergence_count) is the primary signal: more independent firings = stronger case.
      - salience_weighted_mean ensures quality (high-salience signals count more than noise).
      - cross_tradition_multiplier rewards multi-tradition agreement (4+ traditions 1.5×,
        3 = 1.3×, 2 = 1.1×, 1 = 1.0×) — mirrors the "weight of evidence" principle.
      - contradiction_penalty discounts convergence when the domain has active conflicts.
    """
    n = len(c.signal_saliencies)
    if n == 0:
        return {
            "convergence_count": 0,
            "convergence_score": 0.0,
            "cross_tradition_count": 0,
            "salience_weighted_sum": 0.0,
            "salience_max": 0.0,
            "convergence_formula_version": VERSION_CONVERGENCE_FORMULA,
        }

    salience_sum = sum(c.signal_saliencies)
    salience_max = max(c.signal_saliencies)
    salience_mean = salience_sum / n

    distinct_traditions = len(set(c.signal_traditions)) if c.signal_traditions else 1
    tradition_multiplier = (
        1.50 if distinct_traditions >= 4
        else 1.30 if distinct_traditions == 3
        else 1.10 if distinct_traditions == 2
        else 1.00
    )

    contradiction_penalty = max(1.0 - (c.contradiction_count / max(n, 1)) * 0.3, 0.5)

    convergence_score = n * salience_mean * tradition_multiplier * contradiction_penalty

    return {
        "convergence_count": n,
        "convergence_score": round(convergence_score, 6),
        "cross_tradition_count": distinct_traditions,
        "salience_weighted_sum": round(salience_sum, 6),
        "salience_max": round(salience_max, 6),
        "convergence_formula_version": VERSION_CONVERGENCE_FORMULA,
    }


# ──────────────────────────────────────────────────────────────────────────────
# §13.1  centrality_formula_v1
# Composite centrality score for a graph node — the deterministic "most
# consequential factor" ranking.
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CentralityInputs:
    pagerank_score: float = 0.0
    eigenvector_centrality: float = 0.0
    betweenness_centrality: float = 0.0   # normalized [0,1]
    harmonic_centrality: float = 0.0      # normalized [0,1]
    degree_total: int = 0                  # degree_in + degree_out
    max_degree_in_graph: int = 1           # for normalization
    strength_score: float = 0.5            # A8 composite strength [0,1]
    # Dispositor chain terminus weight: 1.0 + (chains_converging / total_nodes)
    terminus_convergence_weight: float = 1.0


def centrality_formula_v1(node: CentralityInputs) -> dict[str, float]:
    """§13.1 centrality formula v1.0.

    composite_centrality = weighted_average(pagerank, eigenvector, betweenness, harmonic)
                           × degree_norm × strength_amplifier × terminus_weight

    Weights reflect the classical insight that:
      - PageRank (0.35): captures prestige — a planet aspected by strong planets matters more.
      - Eigenvector (0.25): global influence — connected to influential nodes.
      - Betweenness (0.20): bridge importance — controls paths between other factors.
      - Harmonic (0.20): accessibility — can reach all other factors efficiently.

    degree_norm prevents pure high-degree nodes from dominating (log-dampened).
    strength_amplifier: a classically strong planet at a central graph position
      is more consequential than a weak one in the same position.
    terminus_weight: amplifies the "final dispositor" — all chains converge here.
    """
    graph_centrality = (
        node.pagerank_score * 0.35
        + node.eigenvector_centrality * 0.25
        + node.betweenness_centrality * 0.20
        + node.harmonic_centrality * 0.20
    )

    degree_norm = math.log(1 + node.degree_total) / math.log(1 + max(node.max_degree_in_graph, 1))
    strength_amplifier = 0.5 + node.strength_score * 0.5   # [0.5, 1.0]

    composite_centrality = (
        graph_centrality
        * (1 + degree_norm * 0.3)
        * strength_amplifier
        * node.terminus_convergence_weight
    )

    return {
        "composite_centrality": round(composite_centrality, 6),
        "centrality_formula_version": VERSION_CENTRALITY_FORMULA,
    }


# ──────────────────────────────────────────────────────────────────────────────
# BA-P3B  salience_formula_v2  (ONE canonical site — C5 fix)
# Replaces verification_certainty (0.778 ceiling) with verification_rescale.
# Adds class_prior × varga_weight × specificity × bala_gate × functional_context.
# bo_laksana MUST call this function; the inline formula there is deleted.
# ──────────────────────────────────────────────────────────────────────────────

VERSION_SALIENCE_FORMULA_V2 = "v2.0"

# verification_rescale lookup — replaces log(1+corroboration)/log(10)
VERIFICATION_RESCALE: dict[str, float] = {
    "two_pass_verified":        1.00,
    "single_pass":              0.85,
    "documented_approximation": 0.60,
}

# Varga weight by divisional chart suffix
VARGA_WEIGHT: dict[str, float] = {
    "D1": 1.00, "D2": 0.90, "D3": 0.85, "D4": 0.85,
    "D7": 0.80, "D9": 0.90, "D10": 0.85, "D12": 0.80,
    "D16": 0.75, "D20": 0.75, "D24": 0.75, "D27": 0.75,
    "D30": 0.70, "D40": 0.70, "D45": 0.70, "D60": 0.65,
}


@dataclass
class SalienceInputsV2:
    """All deterministic inputs for salience_formula_v2 (BA-P3B).

    Callers supply only what applies; unset fields default to neutral.
    Completeness is tracked via inputs_complete — FALSE when any field
    falls back to a silent default (trap #17).
    """
    # Condition terms — carry over from v1
    orb_tightness: float = 1.0
    shadbala_norm: float = 1.0          # rupas, clamped to 2.0 max
    dignity_score: float = 0.50         # use DIGNITY_SCORE lookup or pass raw
    house_number: int = 2
    ashtakavarga_bindus: int = 4
    vargottama_amplification: float = 0.0
    neechabhanga_modifier: float = 1.0
    cancellation_modifier: float = 1.0

    # V2 additions
    verification_pass_status: str = "documented_approximation"
    class_prior: float = 1.0        # from brahma_class_priors; 1.0 if row not found
    varga_id: str = "D1"            # used to look up VARGA_WEIGHT
    specificity: float = 1.0        # 1 + 0.5×extremity_pctl; 1.0 before percentile pass
    bala_gate: float | None = None  # yoga-class: clamp(shadbala_norm, 0.30, 1.00); None=N/A
    functional_context: float = 1.0 # benefic=1.1, malefic=0.9, neutral=1.0

    # Completeness tracking
    inputs_complete: bool = True    # set False when any field fell back to a default


def salience_formula_v2(s: SalienceInputsV2) -> dict[str, Any]:
    """BA-P3B salience formula v2.0 — ONE canonical site (C5 fix).

    salience_v2 = class_prior × varga_weight × specificity
                × verification_rescale
                × condition_terms(orb × shadbala × dignity × house_wt × av_mult
                                  × vargottama × neechabhanga × cancellation)
                × bala_gate   [yoga-class only; 1.0 for all others]
                × functional_context

    verification_rescale eliminates the 0.778 ceiling of log(1+corroboration)/log(10).
    bala_gate: yoga signals with weak constituent planets are demoted, not excluded.
    specificity and salience_pctl_in_class are filled in a second pass by bo_laksana.
    """
    verification_rescale = VERIFICATION_RESCALE.get(
        s.verification_pass_status,
        VERIFICATION_RESCALE["documented_approximation"],
    )
    varga_weight = VARGA_WEIGHT.get(s.varga_id or "D1", 1.00)
    house_wt = HOUSE_WEIGHT.get(s.house_number, 1.00)
    av_mult = _av_multiplier(s.ashtakavarga_bindus)

    condition_terms = (
        s.orb_tightness
        * min(s.shadbala_norm, 2.0)
        * s.dignity_score
        * house_wt
        * av_mult
        * (1 + s.vargottama_amplification)
        * s.neechabhanga_modifier
        * s.cancellation_modifier
    )

    gate = s.bala_gate if s.bala_gate is not None else 1.0
    present_but_enfeebled = (s.bala_gate is not None) and (s.bala_gate < 0.60)

    computed_salience = (
        s.class_prior
        * varga_weight
        * s.specificity
        * verification_rescale
        * condition_terms
        * gate
        * s.functional_context
    )

    return {
        "class_prior":              round(s.class_prior, 6),
        "varga_weight":             round(varga_weight, 6),
        "specificity":              round(s.specificity, 6),
        "verification_rescale":     round(verification_rescale, 6),
        "condition_terms":          round(condition_terms, 6),
        "bala_gate":                round(gate, 6),
        "functional_context":       round(s.functional_context, 6),
        "computed_salience":        round(computed_salience, 6),
        "salience_formula_version": VERSION_SALIENCE_FORMULA_V2,
        "salience_inputs_complete": s.inputs_complete,
        "present_but_enfeebled":    present_but_enfeebled,
        # v1 compat keys — callers that stored these column names still work
        "house_weight_multiplier":           round(house_wt, 6),
        "ashtakavarga_support_multiplier":   round(av_mult, 6),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Doctrine Wave D-4b, BRIEF_D4B.md §1 Lane B-4  remedy_leverage_join_v1
# bo_upaya populated from: leverage_index (weakest load-bearing graha) x
# existing sadhana history (LEL spiritual arc) x dasha runway (intervention
# window = years BEFORE the weak lord's Mahadasha opens).
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class RemedyLeverageJoinInputs:
    # L1 ga_vichara leverage_index value for the target graha x domain —
    # READ from chart_vichara, never recomputed here (§N.5).
    leverage_index_value: float = 0.0
    # Count of pre-embargo (event_date < 2020-01-01, ESCALATION_POLICY §4
    # sealed test split) LEL life_events rows with event_type='spiritual' for
    # this chart — the native's demonstrated sadhana/devata-adoption track
    # record. NOT graha-specific (a sustained personal practice supports
    # adherence to any prescribed remedy, not only ones targeting the graha
    # the practice happened to invoke).
    sadhana_milestone_count: int = 0
    # Bounded dasha-runway weight for the target graha's next/current
    # Vimshottari Mahadasha, using the SAME registry-sourced curve as
    # ga_vichara_writer.py's own _dasha_runway() (brahma_vichara_constants.
    # leverage_weights: runway_base/scale/duration_norm/start_horizon) —
    # recomputed fresh from live chart_dashas by the caller, not read back
    # from chart_vichara.leverage_index's own embedded runway sub-field.
    dasha_runway_weight: float = 1.0


def remedy_leverage_join_v1(j: RemedyLeverageJoinInputs) -> dict[str, float]:
    """BRIEF_D4B §1 Lane B-4 — the remedy-leverage join.

    sadhana_history_factor: each distinct pre-embargo sustained-practice
    milestone (Shani sadhana initiation, a devata adoption, a spiritual-arc
    transmission event, ...) adds a bounded amplification on the theory that
    a chart with a demonstrated multi-year sadhana track record is more
    likely to sustain a NEW prescribed remedy program than one with none on
    record. Capped at 5 milestones (diminishing evidentiary value beyond
    that, and to keep the multiplier bounded like every other formula in
    this module). Zero milestones on record -> factor=1.0 (neutral; absence
    of a recorded milestone is not evidence the native lacks a practice —
    B.10 forbids penalizing on an absence).

    remedy_leverage_score is the plain product of all three named factors —
    this is the join itself, not a re-derivation of any one factor.
    """
    n = min(max(j.sadhana_milestone_count, 0), 5)
    sadhana_history_factor = 1.0 + 0.15 * n
    remedy_leverage_score = (
        j.leverage_index_value * sadhana_history_factor * j.dasha_runway_weight
    )
    return {
        "sadhana_history_factor": round(sadhana_history_factor, 6),
        "remedy_leverage_score": round(remedy_leverage_score, 6),
        "remedy_leverage_join_formula_version": VERSION_REMEDY_LEVERAGE_JOIN_FORMULA,
    }
