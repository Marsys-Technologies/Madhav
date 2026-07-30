"""
services/ka_kshetra/stage6_salience.py — the salience vector (item 25).

KALA_W2_FIELD_DESIGN_v1_0.md §6.1. Five factors, each normalized to [0,1] and
served as a VECTOR alongside the ordering scalar (the auditability property
the native asked for). A factor that cannot be computed is `None` (honest
`not_computed`), never imputed as 0 — the ordering scalar renormalizes its
weights over whichever factors ARE present.

This module is a PURE computation layer: it never touches a database
connection. `factor_informativeness` is derived from a `CohortRate` the
caller already obtained from `services.ka_kshetra.cohort_client.
cohort_base_rate()` — Stage 6's orchestration (Lane C's `ka_kshetra` writer,
not yet built) is what wires the DB call to this pure function, exactly like
`bg_cohort.py`'s own `compute_md_lord_chain()` keeps its arithmetic
import-free of swisseph/PyJHora for testability.

CONSEQUENCE (Q) SCHEMA GAP, DISCLOSED (not silently patched):
§6.1's formula names three sub-terms sourced from `brahma_event_ontology`:
`severity_band`, `domains_touched`, `significance_class`. Migration 388 (the
REAL, shipped `brahma_event_ontology` — verified by reading the migration
file, not assumed from the design doc) has NO such columns; it has `domain`
(one value), `magnitude_floor` (5-level enum: trivial/moderate/significant/
major/life_altering), and `adjacency` (JSONB list of related event_class_ids).
Per CLAUDE.md B.10 (no fabrication) this module does NOT invent columns or a
second severity axis that does not exist in the corpus. Instead:
  - `severity_norm` is `magnitude_floor`'s ordinal position normalized to
    [0,1] (index / 4 across the 5-level enum) — the same [0,1] semantics
    §6.1's `severity_band/3` needs, over the real ordinal the corpus has.
  - `domains_touched_norm` is `min(1, |{domain} ∪ adjacent_domains| / 3)`,
    where `adjacent_domains` is resolved from the real `adjacency` column
    (the event classes it lists) — a genuine derived signal, not fabricated.
  - `significance_class` has NO independent real column: the corpus's only
    ordinal "how big a deal is this" signal is `magnitude_floor`, already
    spent on `severity_norm`. Rather than reuse it a second time under a
    different name (double-counting one signal as two), Q is renormalized
    over the two AVAILABLE sub-terms (0.5 and 0.3, renormalized to sum to 1)
    exactly as §6.1's own top-level formula renormalizes over present
    factors — `consequence_basis` records which sub-terms were used.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import log

# ── Salience factor weights, v0 (§6.1) ───────────────────────────────────────

SALIENCE_WEIGHTS_V0: dict[str, float] = {
    "I": 0.30, "Q": 0.25, "R": 0.20, "B": 0.15, "A": 0.10,
}
SALIENCE_WEIGHTS_VERSION = "salience_v0"
_FACTOR_ORDER = ("I", "Q", "R", "B", "A")

# 5-level ordinal, real column `brahma_event_ontology.magnitude_floor`.
_MAGNITUDE_ORDER = ["trivial", "moderate", "significant", "major", "life_altering"]

# §6.1 Reliability B, from confidence_tier (§5.6).
_RELIABILITY_BY_TIER: dict[str, float] = {
    "calibrated": 1.0, "calibrated_provisional": 0.85,
    "concurrent": 0.75, "structural_prior": 0.5,
}

# §6.1 Actionability A, from the tri-plane intervention_ref (§11 tri-plane).
_ACTIONABILITY_BY_REF: dict[str, float] = {
    "elect_upaya": 1.0, "ritual_only": 0.5, "no_lever": 0.0,
}


@dataclass(frozen=True)
class EventOntologyInfo:
    """Mirrors the REAL `brahma_event_ontology` columns this module reads
    (migration 388) -- not the design doc's assumed severity_band/
    domains_touched/significance_class, which do not exist."""

    event_class_id: str
    domain: str
    magnitude_floor: str
    adjacent_domains: frozenset[str] = frozenset()


@dataclass(frozen=True)
class QuestionFrame:
    """The `question_frame` compiler's output (E4), as far as Stage 6 needs
    it. All fields optional/None means "no constraint on this axis"."""

    domain: str | None = None
    horizon_start: float | None = None   # t_days
    horizon_end: float | None = None     # t_days
    entities: frozenset[str] = frozenset()


@dataclass(frozen=True)
class SalienceVector:
    informativeness: float | None
    consequence: float | None
    relevance: float
    reliability: float | None
    actionability: float | None
    salience: float
    salience_weights_version: str
    salience_basis: tuple[str, ...]
    consequence_basis: tuple[str, ...] = ()


def compute_informativeness(p_cohort: float | None, n_total: int) -> float | None:
    """
    I = min(1, -ln(p_cohort) / -ln(1/N_cohort)).

    `p_cohort` is None whenever `cohort_base_rate()` could not compute a rate
    (any fallback_reason) -- I is then `None`, never 0 (§6.1: "never
    imputed"). `p_cohort == 0.0` is the maximally-informative case (the
    configuration never occurs in the cohort): the ratio's numerator diverges
    to +inf, so `min(1, ...)` caps it at exactly 1.0.
    """
    if p_cohort is None:
        return None
    if n_total <= 1:
        return None  # ln(N) would be <= 0 -- not a meaningful denominator
    if p_cohort <= 0.0:
        return 1.0
    if p_cohort >= 1.0:
        return 0.0
    return min(1.0, -log(p_cohort) / log(n_total))


def compute_domains_touched(
    event_class_id: str,
    domain: str,
    adjacency: list[str] | None,
    domain_by_class: dict[str, str],
) -> frozenset[str]:
    """
    Resolve the REAL `adjacency` JSONB column (a list of related
    `event_class_id`s) into the set of domains touched by this class plus
    its adjacency-linked classes -- the derived (not fabricated) stand-in
    for §6.1's assumed `domains_touched` count. `domain_by_class` is a
    caller-supplied {event_class_id: domain} lookup (e.g. one query over
    `brahma_event_ontology`).
    """
    touched = {domain}
    for related_id in (adjacency or []):
        related_domain = domain_by_class.get(related_id)
        if related_domain:
            touched.add(related_domain)
    return frozenset(touched)


def compute_consequence(ontology: EventOntologyInfo | None) -> tuple[float | None, tuple[str, ...]]:
    """
    Q, renormalized over the sub-terms the REAL corpus actually supports.
    See module docstring "CONSEQUENCE (Q) SCHEMA GAP" for why this is two
    terms (severity, domains), not three.
    """
    if ontology is None:
        return None, ()

    severity_idx = _MAGNITUDE_ORDER.index(ontology.magnitude_floor)
    severity_norm = severity_idx / (len(_MAGNITUDE_ORDER) - 1)

    # domains_touched = {this class's own domain} ∪ {domains of its
    # adjacency-linked classes} (compute_domains_touched() is how a caller
    # resolves `ontology.adjacent_domains` from the real `adjacency` column
    # before constructing this EventOntologyInfo).
    domains_touched = {ontology.domain} | ontology.adjacent_domains
    domains_norm = min(1.0, len(domains_touched) / 3.0)

    w_severity, w_domains = 0.5, 0.3
    total_w = w_severity + w_domains
    q = (w_severity * severity_norm + w_domains * domains_norm) / total_w
    return q, ("severity", "domains")


def _interval_jaccard(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    inter_start, inter_end = max(a_start, b_start), min(a_end, b_end)
    intersection = max(0.0, inter_end - inter_start)
    union = (a_end - a_start) + (b_end - b_start) - intersection
    if union <= 0:
        return 0.0
    return intersection / union


def compute_relevance(
    event_domain: str | None,
    window_t_start: float,
    window_t_end: float,
    window_entities: frozenset[str],
    frame: QuestionFrame | None,
) -> float:
    """
    R = 0.5*domain_match + 0.3*horizon_overlap + 0.2*entity_match;
    R = 1.0 when no question_frame is supplied (§6.1).
    """
    if frame is None:
        return 1.0

    domain_match = 1.0 if (frame.domain is None or frame.domain == event_domain) else 0.0

    if frame.horizon_start is None or frame.horizon_end is None:
        horizon_overlap = 1.0
    else:
        horizon_overlap = _interval_jaccard(
            window_t_start, window_t_end, frame.horizon_start, frame.horizon_end
        )

    if not frame.entities:
        entity_match = 1.0
    else:
        entity_match = 1.0 if (window_entities & frame.entities) else 0.0

    return 0.5 * domain_match + 0.3 * horizon_overlap + 0.2 * entity_match


def compute_reliability(confidence_tier: str | None) -> float | None:
    """B, from the window's §5.6 confidence_tier."""
    if confidence_tier is None:
        return None
    return _RELIABILITY_BY_TIER.get(confidence_tier)


def compute_actionability(intervention_ref: str | None) -> float | None:
    """A, from the tri-plane `intervention_ref` pointer state (§11)."""
    if intervention_ref is None:
        return None
    return _ACTIONABILITY_BY_REF.get(intervention_ref)


def compute_salience_vector(
    *,
    p_cohort: float | None,
    cohort_n_total: int,
    ontology: EventOntologyInfo | None,
    event_domain: str | None,
    window_t_start: float,
    window_t_end: float,
    window_entities: frozenset[str] = frozenset(),
    confidence_tier: str | None,
    intervention_ref: str | None,
    frame: QuestionFrame | None = None,
    weights: dict[str, float] | None = None,
    weights_version: str = SALIENCE_WEIGHTS_VERSION,
) -> SalienceVector:
    """
    The full §6.1 vector + versioned ordering scalar. Missing factors are
    renormalized over the present ones (never imputed as 0); `salience_basis`
    records exactly which factors survived into the scalar, in the fixed
    order I, Q, R, B, A.
    """
    v = weights if weights is not None else SALIENCE_WEIGHTS_V0

    informativeness = compute_informativeness(p_cohort, cohort_n_total)
    consequence, consequence_basis = compute_consequence(ontology)
    relevance = compute_relevance(event_domain, window_t_start, window_t_end, window_entities, frame)
    reliability = compute_reliability(confidence_tier)
    actionability = compute_actionability(intervention_ref)

    factors: dict[str, float | None] = {
        "I": informativeness, "Q": consequence, "R": relevance,
        "B": reliability, "A": actionability,
    }
    present = {k: val for k, val in factors.items() if val is not None}
    total_weight = sum(v[k] for k in present)
    if total_weight > 0:
        salience = sum(v[k] * present[k] for k in present) / total_weight
    else:
        salience = 0.0
    salience_basis = tuple(k for k in _FACTOR_ORDER if k in present)

    return SalienceVector(
        informativeness=informativeness,
        consequence=consequence,
        relevance=relevance,
        reliability=reliability,
        actionability=actionability,
        salience=salience,
        salience_weights_version=weights_version,
        salience_basis=salience_basis,
        consequence_basis=consequence_basis,
    )
