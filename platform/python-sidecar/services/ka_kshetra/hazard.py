"""
services/ka_kshetra/hazard.py — §5.1 THE HAZARD FORMULA (E1, the wave's centre).

    λ_e(t)  =  λ⁰_e · P̃_e · C_e(t) · M_e(t) · S_e(t)

λ_e(t) is the HAZARD RATE of event class e at time t for this chart, in units of
EVENTS PER DAY, strictly positive everywhere. It is not a score, not an index and
not a 0–1 "intensity": it is the intensity function of an inhomogeneous Poisson
process, which is what makes ∫λ dt an expected NUMBER OF EVENTS and what lets
stage 9 fit it by a real Poisson log-likelihood and test it by the time-rescaling
theorem. Every design choice below exists to protect one of those two properties.

── WHY EVERY FACTOR IS MULTIPLICATIVE, AND WHY THAT MATTERS ──────────────────
Working in the log domain makes the whole model log-linear:

    ln λ_e(t) = ln λ⁰_e + ln P̃_e + Σ_s w_s·A_s·r_{s,e}(t)
                                  + Σ_j β_j·x_j(t)
                                  + Σ_m ln(1 − ρ_m·u_m(t))

Three consequences, each load-bearing somewhere else in the pipeline:

  1. STRICT POSITIVITY BY CONSTRUCTION. λ⁰ > 0; P̃ ≥ P_floor = 0.05; every clock
     factor is exp(·) > 0; every modifier factor is exp(·) > 0; and every
     suppression factor is (1 − ρ·u) ≥ 1 − 0.95 = 0.05 > 0 because ρ is bounded
     by the MODEL, not merely by a fitter's box constraint. There is no input for
     which λ = 0, so ln λ is always finite and the log-linear segment
     representation (integrator.py) is always well defined.

  2. EXACT PROVENANCE ADDITIVITY. Every factor contributes ln(factor) to a sum.
     That is precisely §5.4's RECONCILIATION INVARIANT — the provenance edges
     this module emits sum to ln λ by construction, not by a later reconciliation
     pass. A provenance row set that does not reconstruct the value it explains
     is not weak evidence; it is no evidence (CLAUDE.md §N.8), and here it cannot
     happen because the edges ARE the summands.

  3. SUPPRESSION THINS, IT NEVER SUBTRACTS (Elevation §3 stage-4 amendment,
     binding). A subtractive obstruction term can drive λ through zero and out
     the other side, at which point "hazard rate" is meaningless and the
     integrator's exp() form breaks. Multiplicative thinning is bounded below by
     0.05^|vighna| > 0. The signed negative a reader sees, −(1 − S), is computed
     and stored ALONGSIDE, and is never fed back into the math.

── PURITY (deliberate) ───────────────────────────────────────────────────────
NO DB, NO IO, NO CLOCK, NO RNG in this module. It is a pure function of its
arguments, which is what lets the same code path serve (a) the field build,
(b) the R = 256 circular-shift null replicates, and (c) the stage-9 fitter's
likelihood — the design's own load-bearing requirement that "if the fitter used a
different integral, the published skill score would be measuring a model the
product does not serve" (§7.2), applied one level up to λ itself.

Authority: KALA_W2_FIELD_DESIGN_v1_0.md §5.1, §5.4. Rails: CLAUDE.md §N.5
(L1 is authority — this module never restates a computed value, it consumes
values its callers inherited by reference), §N.8 (earned signal), B.10.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Sequence

from services.ka_kshetra.contracts import ClockApplicability, PromisePrior, ProvenanceEdge, Route

# ── Structural constants (v0-versioned; part of config_pin, §7.4) ────────────

#: §5.1 C-2. The Adṛṣṭa channel made STRUCTURAL: a class with zero natal promise
#: still receives 5% of baseline hazard. Two things depend on this being > 0 —
#: windows over absent promise are served and labelled rather than suppressed,
#: and λ can never be identically zero, which the hazard interpretation requires.
P_FLOOR: float = 0.05

#: §5.1 C-6. The model-level bound on a vighna's thinning strength. NOT a fitter
#: box constraint that could be relaxed: S_e(t) ≥ (1 − RHO_MAX)^|vighna(e)| > 0
#: is the inequality that keeps λ strictly positive however many obstructors are
#: simultaneously active.
RHO_MAX: float = 0.95

#: Days in a Julian century — the horizon λ⁰ is expressed over (§5.1 C-1, §5.2).
DAYS_PER_CENTURY: float = 36525.0

#: §5.1 C-5. The covariate vector is FROZEN at twelve for W2. Adding a
#: thirteenth is a weights-version-BREAKING change requiring a new
#: x_schema_version and a refit — never an in-place edit (§11.2).
COVARIATE_KEYS: tuple[str, ...] = (
    'contact_moon_ref',          # x1  max envelope over active Moon-referenced contacts
    'contact_lagna_ref',         # x2  same, Lagna-referenced
    'dual_reference_agreement',  # x3  = min(x1, x2)  — derived, see below
    'av_kaksha_gate',            # x4  normalized bindu/kakṣyā score
    'moorti_svarna',             # x5  0/1 step
    'moorti_rajata',             # x6  0/1 step
    'moorti_tamra',              # x7  0/1 step  (loha is the REFERENCE level — no dummy)
    'station_band',              # x8
    'sandhi_band',               # x9  from Lane B boundaries
    'syzygy_band',               # x10
    'eclipse_contact',           # x11 = syzygy_band × eclipse_candidate
    'panchanga_affinity',        # x12
)

#: Pinned into the field hash (§7.4) and onto every row. The name encodes BOTH
#: the covariate count and the schema generation, so a silent twelfth→thirteenth
#: change cannot masquerade as the same model.
X_SCHEMA_VERSION: str = 'x12_v0'

#: `beta:x1` … `beta:x12` — the weight_id each covariate reads.
COVARIATE_WEIGHT_IDS: dict[str, str] = {
    key: f'beta:x{i + 1}' for i, key in enumerate(COVARIATE_KEYS)
}

#: §5.1 C-3, verbatim. Overridden per weights-version by `d:<level>` rows; this
#: mapping is the fallback used only when a weights version omits them, and is
#: identical to migration 491's seeded v0_classical values.
DEFAULT_DEPTH_WEIGHTS: dict[str, float] = {
    'MD': 1.00, 'AD': 0.70, 'PD': 0.50, 'SD': 0.30, 'PrD': 0.15,
}

#: Roles whose ln(term_value) genuinely participates in the §5.1 product.
MULTIPLICATIVE_TERM_ROLES: frozenset[str] = frozenset(
    {'baseline', 'promise', 'clock', 'modifier', 'suppression'}
)

#: Roles that are REFERENCE edges rather than factors — they cite the row that
#: holds a value (§N.5: inherit, never restate) and are multiplicative
#: identities, so §5.4's reconciliation sum "over that window's provenance rows"
#: holds VERBATIM with them present. `route:rank2` cites its kala_field_routes
#: row (whose route_gain is already inside P̃ via Lane A's noisy-OR — restating
#: it here would double-count it); `gate:legacy_sweep_xref` cites the legacy
#: kala_gochara_windows row it cross-checks against, and must never copy that
#: row's signed_intensity into a field column (§5.3).
IDENTITY_TERM_ROLES: frozenset[str] = frozenset({'route', 'gate'})


# ── C-1 — baseline λ⁰_e ──────────────────────────────────────────────────────

def baseline_rate(lifetime_count: float) -> float:
    """λ⁰_e = N_e / 36525, in events per day.

    `lifetime_count` (N_e) is the class's classical lifetime expectation over a
    100-year horizon, read from `bg_class_priors`. It is NEVER invented: §5.1
    C-1 is explicit that "a class with no prior row is `not_computed` and is
    SKIPPED ENTIRELY (no field rows written for it) — never given a made-up
    baseline." This function therefore REJECTS a non-positive count rather than
    flooring it: a silent clamp to some tiny ε would manufacture a hazard for a
    class nobody has a prior for, which is the exact fabrication B.10 forbids.
    """
    if not math.isfinite(lifetime_count) or lifetime_count <= 0.0:
        raise ValueError(
            f'baseline lifetime_count must be finite and > 0, got {lifetime_count!r}. '
            'A class with no usable bg_class_priors row is SKIPPED (not_computed), '
            'never given a fabricated baseline (§5.1 C-1 / B.10).'
        )
    return lifetime_count / DAYS_PER_CENTURY


# ── C-2 — promise P̃_e and the Law-3 graded gate ─────────────────────────────

def promise_tilde(p: float) -> float:
    """P̃_e = P_floor + (1 − P_floor)·P_e — the structural Adṛṣṭa floor.

    `p` is Lane A's noisy-OR prior P_e ∈ [0, 1). An out-of-range value is a
    caller bug and is raised, not clamped: clamping would hide a broken promise
    graph behind a plausible-looking number (§N.7 item 6).
    """
    if not math.isfinite(p) or p < 0.0 or p > 1.0:
        raise ValueError(f'promise P_e must be finite in [0,1], got {p!r}')
    return P_FLOOR + (1.0 - P_FLOOR) * p


def promise_state(p: float) -> str:
    """The served `promise_state` label. Bands are declared here so the label and
    the arithmetic can never drift apart; `absent` is reserved for EXACTLY zero
    promise, because that is the state stage 6.5's `absence_of_expected` insight
    and Law 3's graded gate are about."""
    if p <= 0.0:
        return 'absent'
    if p < 0.30:
        return 'weak'
    if p < 0.60:
        return 'moderate'
    return 'strong'


# ── C-3 — clocks C_e(t): the multiplicative concurrence (Law 2) ──────────────

def predictive_systems(
    clocks: Iterable[ClockApplicability],
) -> list[ClockApplicability]:
    """S_pred(e): applicable systems that are predictive AND have a quality.

    Three exclusions, each for a different reason and none of them a tuning
    choice:
      • `applicability_state != 'applicable'` — the system either does not apply
        to this chart (excluded_by_condition) or was never computed for it
        (not_computed). §4.1 step 2 is explicit that absent is NEVER treated as
        excluded; both simply contribute no factor.
      • `is_predictive is False` — rule C-4: `competence_class='life_stage'`
        (naisargika) is a CONTEXT band, never a predictor. Excluded BY
        CONSTRUCTION, so the stage-9 fitter is never even handed the parameter.
      • `quality is None` — A_s is undefined; a system whose determinability
        was never measured cannot lend confidence to a timing claim.
    """
    return [
        c for c in clocks
        if c.applicability_state == 'applicable'
        and c.is_predictive
        and c.quality is not None
    ]


def relevance(
    lord_stack: Sequence[tuple[str, str]],
    routes: Sequence[Route],
    depth_weights: Mapping[str, float],
) -> float:
    """r_{s,e}(t) = tanh( Σ_ℓ d_ℓ · sign_ℓ · g_ℓ ) ∈ [−1, +1].

    The SIGNED relevance of system s's running lord stack at time t to event
    class e, computed as promise-graph reachability of the running lords to the
    `event_class:e` sink.

    `lord_stack` is an ordered sequence of (level, lord) — MD outermost. A level
    whose `precision_state` is 'precision_unsupported' is ABSENT from this
    sequence (rule C-5): Lane B's `boundary_breakpoints`/ladder drops it, so its
    d_ℓ term simply does not appear. Absent is not the same as zero, and the
    difference is observable in the result.

    g_ℓ is the best route gain among routes containing the node `graha:<lord>`,
    and 0 when no route contains it — an honest zero, never an imputed default.
    sign_ℓ is −1 when that route lists the lord among its `suppressed_by` vighna
    keys, +1 otherwise.

    tanh bounds the sum into [−1, +1] so that no depth of lord stacking can make
    a single clock dominate the product; the bound is what keeps C_e(t) a
    proportional-hazards MODIFIER rather than a de facto second baseline.
    """
    total = 0.0
    for level, lord in lord_stack:
        d = depth_weights.get(level)
        if d is None:
            # An unknown level contributes nothing rather than silently
            # borrowing a neighbour's weight (§N.7 item 6: an honest null beats
            # an invented judgment).
            continue
        gain, suppressed = _best_route_for_lord(lord, routes)
        if gain <= 0.0:
            continue
        total += d * (-1.0 if suppressed else 1.0) * gain
    return math.tanh(total)


def _best_route_for_lord(lord: str, routes: Sequence[Route]) -> tuple[float, bool]:
    """(g_ℓ, is_suppressed) for one lord.

    Deterministic tie-break: on equal gain, the LOWER route_rank wins, then the
    lexicographically smaller node path. Determinism here is not cosmetic — the
    field hash must be bit-reproducible across builds (§7.4), so a tie resolved
    by dict iteration order would break hash-replay.
    """
    node = f'graha:{lord}'
    best: Optional[Route] = None
    for r in routes:
        if node not in r.path_node_ids:
            continue
        if best is None:
            best = r
            continue
        key_r = (-r.route_gain, r.route_rank, tuple(r.path_node_ids))
        key_b = (-best.route_gain, best.route_rank, tuple(best.path_node_ids))
        if key_r < key_b:
            best = r
    if best is None:
        return 0.0, False
    suppressed = any(lord in key or node in key for key in best.suppressed_by)
    return best.route_gain, suppressed


def clock_log_factor(quality: float, relevance: float, w_s: float) -> float:
    """ln( a_{s,e}(t) ^ w_s ) = w_s · A_s · r_{s,e}(t).

    a_{s,e}(t) = exp(A_s · r_{s,e}(t)) > 0 always, so a_s^{w_s} > 0 always, so
    C_e(t) > 0 always.

    `w_s = 0` collapses the factor to EXACTLY 1 (this returns exactly 0.0), which
    is what lets a calibration run switch a clock off smoothly without changing
    the model's structure — and is how rule C-4 makes naisargika inert by
    construction rather than by a fitted value that merely happens to be small.
    """
    return w_s * quality * relevance


# ── C-5 — modifiers M_e(t) ───────────────────────────────────────────────────

def derive_dual_reference_agreement(x: Mapping[str, float]) -> float:
    """x3 = min(x1, x2) — the gochara DUAL-REFERENCE agreement (§5.1 C-5 row 3).

    A transit that is strong from the Moon but absent from the Lagna (or vice
    versa) scores 0 here. `min` rather than a product or a mean is deliberate:
    agreement is the weaker leg, and only concurrence of both classical
    reference points earns the covariate.
    """
    return min(float(x.get('contact_moon_ref', 0.0)), float(x.get('contact_lagna_ref', 0.0)))


def modifier_log_term(x: Mapping[str, float], betas: Mapping[str, float]) -> float:
    """ln M_e(t) = Σ_j β_j · x_j(t) over the twelve frozen covariates.

    A covariate with no β in the pinned weights version contributes EXACTLY
    zero, not a default: an unfitted, unseeded coefficient must be inert. That
    is the same discipline as `w_s` above — an unweighted term may never smuggle
    an effect in under an implicit 1.0.
    """
    total = 0.0
    for key in COVARIATE_KEYS:
        beta = betas.get(COVARIATE_WEIGHT_IDS[key])
        if beta is None:
            continue
        total += float(beta) * float(x.get(key, 0.0))
    return total


# ── C-6 — suppression S_e(t): MULTIPLICATIVE THINNING ────────────────────────

def suppression_log_term(
    u: Mapping[str, float],
    rhos: Mapping[str, float],
    default_rho: float,
) -> float:
    """ln S_e(t) = Σ_m ln(1 − ρ_m · u_m(t)).

    `u` maps a vighna key (a stage-1 row with polarity='obstructive' that the
    class's routes list in `suppressed_by`) to its piecewise-linear envelope
    value at t, in [0, 1]. `rhos` maps `rho:<vighna_class>` to its fitted
    strength.

    ρ > RHO_MAX is REJECTED, not clamped. That bound is what proves
    S_e(t) ≥ (1 − RHO_MAX)^|vighna(e)| > 0, and a silently-clamped ρ = 1.0 would
    send ln λ to −∞ and take the whole segment representation with it. Better to
    fail at the weights version than to serve a broken field.
    """
    total = 0.0
    for key, u_val in sorted(u.items()):
        if u_val <= 0.0:
            continue
        if u_val > 1.0 or not math.isfinite(u_val):
            raise ValueError(f'obstruction envelope u[{key!r}] must be in [0,1], got {u_val!r}')
        rho = rhos.get(_rho_weight_id(key))
        if rho is None:
            rho = rhos.get('rho:default', default_rho)
        rho = float(rho)
        if rho < 0.0 or rho > RHO_MAX or not math.isfinite(rho):
            raise ValueError(
                f'rho for {key!r} must be in [0, {RHO_MAX}] — got {rho!r}. '
                'RHO_MAX is a MODEL bound, not a fitter box constraint: it is what '
                'keeps S_e(t) > 0 and therefore λ strictly positive (§5.1 C-6).'
            )
        total += math.log1p(-rho * u_val)
    return total


def _rho_weight_id(vighna_key: str) -> str:
    """`vedha:Sa->10` → `rho:vedha`. The vighna CLASS carries the weight; the
    specific instance carries the envelope. One fitted ρ per class keeps the
    stage-9 parameter count at ~25 rather than one per chart-specific obstruction
    (which could never be fitted from ~57 events)."""
    return f'rho:{vighna_key.split(":", 1)[0]}'


def signed_obstruction(S: float) -> float:
    """−(1 − S_e) ∈ (−1, 0] — a SERVING-LAYER RENDERING ONLY (§5.1 C-6).

    Stored alongside the segment so the portal can show a reader a "negative",
    and NEVER fed back into the hazard math. Keeping the rendering and the model
    in separate columns is what stops a future session from "simplifying" the
    thinning back into a subtraction.
    """
    return -(1.0 - S)


# ── The assembled evaluation + its provenance edges ──────────────────────────

@dataclass(frozen=True)
class HazardTerms:
    """One evaluation of §5.1 at one instant, with its provenance edges.

    `edges` is the complete decomposition: Σ log_contribution == ln_lambda to
    machine precision, BY CONSTRUCTION rather than by a later reconciliation
    pass. §5.4's invariant is asserted again at write time (the writer halts with
    `provenance_reconciliation_failed`) — belt and braces, because the invariant
    is what makes the provenance earned rather than decorative.
    """
    ln_lambda: float
    baseline: float
    promise_term: float
    clock_term: float
    modifier_term: float
    suppression_term: float
    signed_obstruction: float
    edges: tuple[ProvenanceEdge, ...]

    @property
    def lambda_value(self) -> float:
        return math.exp(self.ln_lambda)


def identity_edge(
    term_role: str,
    term_key: str,
    source_kind: str,
    *,
    source_table: Optional[str] = None,
    source_pk: Optional[str] = None,
    source_fact_id: Optional[str] = None,
) -> ProvenanceEdge:
    """A REFERENCE edge: term_value = 1.0, log_contribution = 0.0.

    Used for `route` and `gate` roles. These cite the row that already holds the
    value (§N.5 — an L2+ derivation REFERENCES an L1/L3 value and inherits it; it
    never restates it) and are multiplicative identities, so §5.4's reconciliation
    sum over ALL of a window's rows is unchanged by their presence.

    A multiplicative role passed here is a programming error and raises: it would
    silently drop a real factor out of the product while leaving a row that
    *looks* like it explains something.
    """
    if term_role in MULTIPLICATIVE_TERM_ROLES:
        raise ValueError(
            f'{term_role!r} is a multiplicative term role; it must carry its real '
            'term_value/log_contribution, not the identity. Only '
            f'{sorted(IDENTITY_TERM_ROLES)} may be identity edges.'
        )
    if term_role not in IDENTITY_TERM_ROLES:
        raise ValueError(f'unknown term_role {term_role!r}')
    return ProvenanceEdge(
        term_role=term_role, term_key=term_key,
        term_value=1.0, log_contribution=0.0,
        source_kind=source_kind, source_table=source_table,
        source_pk=source_pk, source_fact_id=source_fact_id,
    )


def evaluate(
    *,
    lifetime_count: float,
    promise: PromisePrior,
    clocks: Sequence[ClockApplicability],
    lord_stacks: Mapping[str, Sequence[tuple[str, str]]],
    covariates: Mapping[str, float],
    obstructions: Mapping[str, float],
    weights: Mapping[str, float],
    baseline_source: Optional[tuple[str, str, str]] = None,
) -> HazardTerms:
    """Evaluate §5.1 at ONE instant and return every factor plus its edges.

    `lord_stacks` maps system_id → the running (level, lord) stack at t, already
    filtered of precision-unsupported levels by Lane B (rule C-5).
    `covariates` maps the twelve frozen keys → x_j(t) ∈ [0,1].
    `obstructions` maps vighna key → u_m(t) ∈ [0,1].
    `weights` is the PINNED weights version's `weight_id → weight_value` map.
    `baseline_source` optionally carries (source_table, source_pk, source_fact_id)
    for the baseline edge, so the classical prior is CITED rather than asserted.

    The covariate x3 (`dual_reference_agreement`) is DERIVED here rather than
    trusted from the caller, so the "min of the two legs" definition lives in
    exactly one place and cannot drift between the field build and the null
    replicates.
    """
    depth_weights = {
        level: float(weights.get(f'd:{level}', default))
        for level, default in DEFAULT_DEPTH_WEIGHTS.items()
    }

    edges: list[ProvenanceEdge] = []

    # ── baseline ─────────────────────────────────────────────────────────────
    lam0 = baseline_rate(lifetime_count)
    src_table, src_pk, src_fact = baseline_source or (None, None, None)
    edges.append(ProvenanceEdge(
        term_role='baseline', term_key='baseline',
        term_value=lam0, log_contribution=math.log(lam0),
        source_kind='l0_reference',
        source_table=src_table, source_pk=src_pk, source_fact_id=src_fact,
    ))

    # ── promise ──────────────────────────────────────────────────────────────
    p_tilde = promise_tilde(promise.p)
    edges.append(ProvenanceEdge(
        term_role='promise', term_key='promise',
        term_value=p_tilde, log_contribution=math.log(p_tilde),
        source_kind='l2_signal',
        source_table='kala_field_promise_edges',
        source_fact_id=promise.fact_ids[0] if promise.fact_ids else None,
    ))

    # ── clocks ───────────────────────────────────────────────────────────────
    clock_log = 0.0
    for clock in sorted(predictive_systems(clocks), key=lambda c: c.system_id):
        w_s = float(weights.get(f'w_s:{clock.system_id}', 0.0))
        stack = list(lord_stacks.get(clock.system_id, ()))
        r = relevance(stack, promise.routes, depth_weights)
        contribution = clock_log_factor(float(clock.quality or 0.0), r, w_s)
        clock_log += contribution
        deepest_level, deepest_lord = (stack[-1] if stack else ('none', 'none'))
        edges.append(ProvenanceEdge(
            term_role='clock',
            term_key=f'clock:{clock.system_id}:{deepest_level}:{deepest_lord}',
            term_value=math.exp(contribution),
            log_contribution=contribution,
            weight_id=f'w_s:{clock.system_id}', weight_value=w_s,
            source_kind='l3_row', source_table='kala_field_clocks',
            source_pk=clock.system_id,
        ))

    # ── modifiers ────────────────────────────────────────────────────────────
    x: dict[str, float] = {k: float(covariates.get(k, 0.0)) for k in COVARIATE_KEYS}
    x['dual_reference_agreement'] = derive_dual_reference_agreement(x)
    modifier_log = modifier_log_term(x, weights)
    for i, key in enumerate(COVARIATE_KEYS):
        weight_id = COVARIATE_WEIGHT_IDS[key]
        beta = weights.get(weight_id)
        contribution = 0.0 if beta is None else float(beta) * x[key]
        # Every one of the twelve is emitted, including the zeros: a reader must
        # be able to see the WHOLE covariate vector at the peak, not only the
        # entries that happened to fire (§N.6 — density signalling is data).
        edges.append(ProvenanceEdge(
            term_role='modifier', term_key=f'modifier:x{i + 1}_{key}',
            term_value=math.exp(contribution), log_contribution=contribution,
            weight_id=weight_id, weight_value=None if beta is None else float(beta),
            source_kind='derived', source_table='kala_field_primitives',
        ))

    # ── suppression ──────────────────────────────────────────────────────────
    default_rho = float(weights.get('rho:default', 0.25))
    suppression_log = suppression_log_term(obstructions, weights, default_rho)
    for key, u_val in sorted(obstructions.items()):
        if u_val <= 0.0:
            continue
        rho = float(weights.get(_rho_weight_id(key), default_rho))
        contribution = math.log1p(-rho * float(u_val))
        edges.append(ProvenanceEdge(
            term_role='suppression', term_key=f'suppression:{key}',
            term_value=math.exp(contribution), log_contribution=contribution,
            weight_id=_rho_weight_id(key), weight_value=rho,
            source_kind='l3_row', source_table='kala_field_primitives', source_pk=key,
        ))

    ln_lambda = math.log(lam0) + math.log(p_tilde) + clock_log + modifier_log + suppression_log
    S = math.exp(suppression_log)

    return HazardTerms(
        ln_lambda=ln_lambda,
        baseline=lam0,
        promise_term=p_tilde,
        clock_term=math.exp(clock_log),
        modifier_term=math.exp(modifier_log),
        suppression_term=S,
        signed_obstruction=signed_obstruction(S),
        edges=tuple(edges),
    )


__all__ = [
    'P_FLOOR', 'RHO_MAX', 'DAYS_PER_CENTURY',
    'COVARIATE_KEYS', 'COVARIATE_WEIGHT_IDS', 'X_SCHEMA_VERSION',
    'DEFAULT_DEPTH_WEIGHTS',
    'MULTIPLICATIVE_TERM_ROLES', 'IDENTITY_TERM_ROLES',
    'HazardTerms',
    'baseline_rate', 'promise_tilde', 'promise_state',
    'predictive_systems', 'relevance', 'clock_log_factor',
    'derive_dual_reference_agreement', 'modifier_log_term',
    'suppression_log_term', 'signed_obstruction',
    'identity_edge', 'evaluate',
]
