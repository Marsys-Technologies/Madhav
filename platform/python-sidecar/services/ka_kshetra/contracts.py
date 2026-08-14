"""
services/ka_kshetra/contracts.py — the cross-lane dataclass surface for W2.

OWNERSHIP: this file is SHARED and owned by NOBODY. It is frozen by
`KALA_W2_FIELD_DESIGN_v1_0.md` §0 and edited only by a cross-lane PR. Lane
boundaries in W2 are **table shapes + Python function signatures**, and these
dataclasses are the things that cross those boundaries. A lane never reads
another lane's *code*; it reads another lane's *table*, or calls its one
published function whose types live here.

WHY THE TYPES LIVE HERE AND NOT IN THE PRODUCING LANE'S MODULE: Lane C (stage 4,
the pipeline's centre of gravity) must be able to consume Lane A's promise prior
and Lane B's clock applicability, and must be unit-testable *before* those lanes'
modules exist on disk. Structural definitions in a shared, dependency-free module
let every lane type-check and test against the frozen contract independently, and
make a boundary change a visible diff in one file rather than a silent divergence
between two.

NOTHING IN THIS FILE MAY IMPORT A LANE MODULE, A DB DRIVER, OR NUMPY. It is pure
dataclasses so that importing it can never pull a half-landed lane into a test.

Additive discipline: a lane that needs a new field on an existing dataclass adds
it with a default, so a producer written against the older shape still
constructs. A lane that needs a field *removed or retyped* stops and raises
(§0: "If a lane believes it needs a boundary changed, it stops and raises — it
does not negotiate bilaterally").

MERGE-TRAIN NOTE (2026-07-30, Conductor integration pass): Lane C's own draft of
this file (written before Lane A/B's real code existed) independently defined
`Route`/`PromisePrior` (matching Lane A's live shapes closely — every consumer
across all five lanes constructs these via keyword arguments only, so the exact
field order/defaults never mattered operationally) and its OWN copy of
`ClockApplicability`, duplicating the class Lane B actually defined inside its
own `stage3_clocks.py`. Two classes with the same name and near-identical shape
but different identity is exactly the kind of silent divergence this file exists
to prevent. Consolidated here as the single source of truth; `stage3_clocks.py`
now imports it from here instead of defining its own copy (see that module's own
note). `Route`/`PromisePrior` keep Lane A's original field order/defaults — the
already-live, already-tested shape every lane's keyword-only construction sites
were written against.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Lane A · stage 2 promise graph (§3.3) ────────────────────────────────────

@dataclass(frozen=True)
class Route:
    """One Yen K-shortest-path routing from a significator seed to an
    `event_class` sink, mirroring a `kala_field_routes` row.

    `route_gain` = Π over the path's edges of the edge conductance
    = exp(−cost(path)) ∈ (0, 1]. `suppressed_by` names the stage-1 vighna keys
    that obstruct this route — Lane C's §5.1 C-6 suppression term reads exactly
    those keys, and the SIGN of a lord's contribution to r_{s,e}(t) (§5.1 C-3)
    flips to −1 when the lord appears here.
    """
    event_class: str
    route_rank: int
    path_node_ids: tuple[str, ...]
    path_edge_ids: tuple[int, ...]
    route_gain: float
    is_primary: bool
    suppressed_by: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromisePrior:
    """Return type of Lane A's published
    `stage2_promise.promise_prior(chart_id, event_class, conn)`.

    `p` is the NOISY-OR over routes, P_e = 1 − Π(1 − p_r) ∈ [0, 1). It is 0 when
    a class has no route at all — the "high natal promise absent" state. Lane C
    NEVER lets P_e = 0 zero the hazard: §5.1 C-2's structural Adṛṣṭa floor
    P̃_e = P_floor + (1 − P_floor)·P_e keeps λ strictly positive, so windows over
    absent promise are SERVED and LABELLED, never suppressed.
    """
    p: float
    routes: tuple[Route, ...] = ()
    n_routes: int = 0
    dropped_below_floor: int = 0
    fact_ids: tuple[str, ...] = ()


# ── Lane B · stage 3 clocks (§4.1) ───────────────────────────────────────────

@dataclass(frozen=True)
class ClockApplicability:
    """One row of Lane B's `kala_field_clocks`, returned by its published
    `stage3_clocks.applicable_systems(chart_id, conn)`.

    Applicability is NOT a boolean (§4.1): it is a (state, quality) pair plus a
    competence class. `quality` is A_s ∈ [0,1] — the system's own
    determination-robustness — and is NULL/None unless
    `applicability_state == 'applicable'`.

    `is_predictive` is FALSE for `competence_class == 'life_stage'` (naisargika).
    Lane C's §5.1 rule C-4 gives that class w_s ≡ 0 BY CONSTRUCTION, not by
    fitting: it is a context band, never a predictor, and the stage-9 fitter is
    never given the parameter at all.

    The SINGLE definition of this shape (see the module-level merge-train note):
    Lane B's `stage3_clocks.py` imports this class rather than defining its own.
    """
    system_id: str
    applicability_state: str          # 'applicable' | 'excluded_by_condition' | 'not_computed'
    competence_class: str             # fruition|arena|flavour|health|annual|life_stage
    seniority_rank: int
    is_predictive: bool
    quality: Optional[float] = None   # A_s ∈ [0,1]; None iff state != 'applicable'
    quality_basis: Optional[str] = None
    exclusion_reason: Optional[str] = None


# ── Lane C · stage 4/5 outward-facing shapes ─────────────────────────────────

@dataclass(frozen=True)
class ProvenanceEdge:
    """One `kala_field_provenance` row-to-be: a single multiplicative factor of
    the §5.1 hazard, evaluated at its target's peak.

    THE RECONCILIATION INVARIANT (§5.4) is stated over these: for a window
    target, |ln(lambda_peak) − Σ log_contribution| ≤ 1e-9. That is what makes
    provenance EARNED rather than decorative — a row set that does not
    reconstruct the value it explains is not weak evidence, it is no evidence,
    and the build fails.
    """
    term_role: str          # baseline|promise|route|clock|modifier|suppression|gate
    term_key: str
    term_value: float
    log_contribution: float
    source_kind: str        # l0_reference|l1_fact|l2_signal|l3_row|derived
    weight_id: Optional[str] = None
    weight_value: Optional[float] = None
    source_table: Optional[str] = None
    source_pk: Optional[str] = None
    source_fact_id: Optional[str] = None


@dataclass(frozen=True)
class Segment:
    """One `kala_field` row: ln λ = alpha + gamma·(t − t_start) on [t_start, t_end].

    This is a DEFINITION of the stored field, not an approximation claim (§5.2).
    Every downstream consumer — serving, integration, the null, the fitter —
    reads THIS, which is what keeps the fitter's likelihood and the served
    expected_count the same arithmetic.
    """
    index: int
    t_start: float
    t_end: float
    alpha: float
    gamma: float
    refinement_depth: int = 0
    refinement_exhausted: bool = False
    refinement_residual: Optional[float] = None


@dataclass(frozen=True)
class FieldWindow:
    """One `kala_field_windows` row: a maximal interval where λ_e(t) ≥ q_e."""
    window_id: str
    event_class: str
    t_start: float
    t_end: float
    t_peak: float
    lambda_peak: float
    expected_count: float
    duration_days: float
    promise_state: str
    temporal_shape: str
    precision_regime: str = 'day_grade'


@dataclass
class RobustnessVector:
    """§5.6. `confidence_tier` is the MINIMUM across dimensions and
    `weakest_link` names the FIRST false dimension in the fixed declaration
    order — deterministic, so two runs never disagree about which link was
    weakest when several are false.
    """
    ayanamsha_robust: Optional[bool] = None
    birth_time_robust: Optional[bool] = None
    system_concurrent: Optional[bool] = None
    null_exceeding: Optional[bool] = None
    authority_clean: Optional[bool] = None

    #: The fixed order §5.6 declares. `weakest_link` reads the first False here.
    ORDER: tuple[str, ...] = field(
        default=(
            'ayanamsha_robust',
            'birth_time_robust',
            'system_concurrent',
            'null_exceeding',
            'authority_clean',
        ),
        repr=False,
        compare=False,
    )

    def as_json(self) -> dict[str, Optional[bool]]:
        return {k: getattr(self, k) for k in self.ORDER}

    def weakest_link(self) -> Optional[str]:
        """First dimension that is not True, in the fixed §5.6 order.

        `None` (not-computed) counts as NOT true. §N.8: a dimension with no
        detector behind it is null, and null is not green — it must be able to
        name itself as the weakest link rather than silently pass.
        """
        for key in self.ORDER:
            if getattr(self, key) is not True:
                return key
        return None

    def confidence_tier(self) -> str:
        """'concurrent' iff every dimension is True, else 'structural_prior'.

        §5.6: the higher tiers ('calibrated_provisional' / 'calibrated') are
        OVERRIDES applied by stage 9's maturity index — stage 5 may never award
        them, because stage 5 has seen no outcome data. That is the whole point
        of the Circularity Guard: the field cannot promote its own confidence.
        """
        return 'concurrent' if self.weakest_link() is None else 'structural_prior'


# ── DHARA null · shared result type (P0.b, 2026-08-14) ───────────────────────

@dataclass(frozen=True)
class NullResult:
    """Canonical result type for the DHARA stage-5 null distribution.

    Moved here from dhara_null.py (P0.b) so writer.py and any future consumer
    can depend on this type without importing a lane module or numpy.

    Fields
    ------
    replicates : int
        The R value passed to dhara_compute_null (256 by default after OPT-N3).
    max_stats : dict
        Per-bucket sliding-window maxima keyed by duration bucket in days.
    q_threshold : float
        95th-percentile of pooled lambda values across all replicates and all
        1-day grid points.

    resolution
    ----------
    F-01 CORRECTION: 1/R (NOT 1/(R+1)).

    The F-01-corrected shift grid uses range(1, R), yielding R-1 independent
    shifts.  The p-value denominator is R (= 1 observation + R-1 shifts), so
    the minimum achievable p is 1/R.  The old getattr fallback in writer.py
    called S5.null_resolution(R) = 1/(R+1), which is wrong for this grid.
    """
    replicates: int
    max_stats: dict
    q_threshold: Optional[float]
    # Optional context fields (populated by dhara_compute_null; default to
    # sentinel values so callers that only need the core three fields can
    # construct without them).
    shift_grid_step: float = 0.0
    shift_count: int = 0
    horizon_days: float = 0.0
    alpha: float = 0.05

    @property
    def resolution(self) -> float:
        """p-value resolution = 1/R (F-01: denominator = R, not R+1)."""
        return 1.0 / self.replicates


# ── P3-a: shape_only synthetic baseline (DHARA_ENGINE_SPEC_v1_0.md §4.1, SM-R-10) ──────────

# Pinned. Never silently chosen per-build. This is the synthetic expected lifetime
# event count used for shape_only classes — exactly 1.0 event over the 100-year
# horizon, i.e. λ⁰ = 1/36525 ≈ 2.74e-5 events/day. Do NOT adjust without a
# native ruling: changing it produces cross-snapshot diffs in null_p comparisons
# (the null_p denominator is the window's expected_count, so any scalar change
# to SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT shifts every shape_only row's null_p).
SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT: float = 1.0


__all__ = [
    'Route',
    'PromisePrior',
    'ClockApplicability',
    'ProvenanceEdge',
    'Segment',
    'FieldWindow',
    'RobustnessVector',
    'NullResult',
    'SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT',
]
