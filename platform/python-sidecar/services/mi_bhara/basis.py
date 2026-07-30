"""
basis.py — the θ-INDEPENDENT per-segment basis, and `ln λ(t; θ)` rebuilt from it.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §5.1 (the hazard formula), §5.2 (the segment
representation the rebuild must land in).

── WHY A BASIS EXISTS AT ALL ──────────────────────────────────────────────────────────────
The fitter evaluates `ℓ(θ)` a few hundred times. Re-deriving the whole five-factor product
from the raw stage-0..3 rows on every one of those evaluations would be both slow and, worse,
a SECOND implementation of the hazard formula that could drift from stage 4's. So Lane C's
stage 4 emits, per segment, the value of every θ-independent basis function at the segment's
two endpoints, and this module recombines them:

    ln λ(t) = ln λ⁰_e + ln P̃_e                        (C-1, C-2 — constant in t and in θ)
            + Σ_s  w_s · ln a_{s,e}(t)                (C-3 — clocks, linear in w in log space)
            + Σ_j  β_j · x_{j,e}(t)                   (C-5 — modifiers, linear in β)
            + Σ_m  ln(1 − ρ_m · u_m(t))               (C-6 — multiplicative thinning)

Three properties of that decomposition are load-bearing and are asserted below:

  • `Σ_s w_s ln a_s` is the log of `Π_s a_s^{w_s}` — so `w_s = 0` collapses a clock's factor to
    EXACTLY 1. A calibration run can switch a clock off smoothly without changing the model's
    structure (§5.1 C-3). It is not a knock-out flag.
  • `S(t) = Π_m (1 − ρ_m u_m)` with `ρ_m ≤ 0.95` and `u_m ∈ [0,1]` is bounded strictly BELOW by
    `0.05^{|vighna|} > 0`. Suppression is multiplicative THINNING, never subtraction, so `λ`
    stays strictly positive by construction — the whole point of the Elevation's stage-4
    amendment. `ln(1 − ρ u)` is therefore always finite here, and a `ρ u ≥ 1` input is a
    caller bug we raise on rather than clamp silently.
  • The rebuilt segment is stored LOG-LINEARLY between the two endpoint evaluations — which is
    §5.2's DEFINITION of the stored field, not an approximation this module introduces. The
    fitter therefore optimises exactly the object the product serves.

── ORDERING IS PART OF THE CONTRACT ───────────────────────────────────────────────────────
`ParameterVector`'s three tuples are positional, and `weight_ids` on `FieldBasis` names them
in the same order. Every `kala_field_weights.weight_id` (`'w_s:vimshottari'`, `'beta:x4'`,
`'rho:vedha'`) round-trips through that naming, so a fitted vector can never be written back
against the wrong parameter. `assert_conformable` is the detector.

Pure functions only. No DB, no clock, no RNG.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from services.mi_bhara.field import FieldSegment

# §5.1 C-5 box constraints, and §5.1 C-6's ρ_max. Frozen at W2; a thirteenth covariate or a
# wider box is an `x_schema_version` bump plus a refit (§11 open question 2), never an edit.
W_BOUNDS = (0.0, 1.0)
BETA_BOUNDS = (-2.0, 2.0)
RHO_BOUNDS = (0.0, 0.95)

X_SCHEMA_VERSION = "x_schema/1"
N_COVARIATES = 12


@dataclass(frozen=True)
class ParameterVector:
    """θ = (w_s for predictive systems, β_j for j=1..12, ρ_m for the vighna classes).

    Positional throughout. `FieldBasis.weight_ids` is the name map.
    """

    w: tuple[float, ...]
    beta: tuple[float, ...]
    rho: tuple[float, ...]

    def as_flat(self) -> tuple[float, ...]:
        return tuple(self.w) + tuple(self.beta) + tuple(self.rho)

    @staticmethod
    def from_flat(flat: Sequence[float], n_w: int, n_beta: int, n_rho: int) -> "ParameterVector":
        expected = n_w + n_beta + n_rho
        if len(flat) != expected:
            raise ValueError(f"flat vector has {len(flat)} entries, expected {expected}")
        return ParameterVector(
            w=tuple(float(v) for v in flat[:n_w]),
            beta=tuple(float(v) for v in flat[n_w : n_w + n_beta]),
            rho=tuple(float(v) for v in flat[n_w + n_beta :]),
        )

    @property
    def dimension(self) -> int:
        return len(self.w) + len(self.beta) + len(self.rho)


@dataclass(frozen=True)
class SegmentBasis:
    """One segment's θ-independent inputs, evaluated at both endpoints.

    `log_base` is `ln λ⁰_e + ln P̃_e` — constant in `t` AND in `θ`, so it never enters the
    optimiser. Everything else is a per-endpoint tuple whose length must match θ's.
    """

    t_start: float
    t_end: float
    log_base: float
    log_a_start: tuple[float, ...] = ()
    log_a_end: tuple[float, ...] = ()
    x_start: tuple[float, ...] = ()
    x_end: tuple[float, ...] = ()
    u_start: tuple[float, ...] = ()
    u_end: tuple[float, ...] = ()


@dataclass(frozen=True)
class FieldBasis:
    """The whole basis for one `(chart, event_class)` — the fitter's per-class unit of work."""

    event_class: str
    segments: tuple[SegmentBasis, ...]
    #: positional names, e.g. ('w_s:vimshottari', 'w_s:yogini')
    system_ids: tuple[str, ...] = ()
    covariate_ids: tuple[str, ...] = ()
    vighna_ids: tuple[str, ...] = ()

    @property
    def weight_ids(self) -> tuple[str, ...]:
        """Every `kala_field_weights.weight_id` this basis's θ maps to, in θ's own order."""
        return (
            tuple(f"w_s:{s}" for s in self.system_ids)
            + tuple(f"beta:{c}" for c in self.covariate_ids)
            + tuple(f"rho:{v}" for v in self.vighna_ids)
        )

    @property
    def dimensions(self) -> tuple[int, int, int]:
        return (len(self.system_ids), len(self.covariate_ids), len(self.vighna_ids))

    def assert_conformable(self, theta: ParameterVector) -> None:
        """The detector for "a fitted vector written back against the wrong parameter"."""
        n_w, n_b, n_r = self.dimensions
        if (len(theta.w), len(theta.beta), len(theta.rho)) != (n_w, n_b, n_r):
            raise ValueError(
                f"θ shape {(len(theta.w), len(theta.beta), len(theta.rho))} does not match "
                f"basis {self.event_class}'s {(n_w, n_b, n_r)}"
            )
        for i, seg in enumerate(self.segments):
            if (
                len(seg.log_a_start) != n_w
                or len(seg.log_a_end) != n_w
                or len(seg.x_start) != n_b
                or len(seg.x_end) != n_b
                or len(seg.u_start) != n_r
                or len(seg.u_end) != n_r
            ):
                raise ValueError(
                    f"segment {i} of basis {self.event_class} has endpoint tuples inconsistent "
                    f"with its declared dimensions {(n_w, n_b, n_r)}"
                )


def log_lambda_endpoint(
    log_base: float,
    log_a: Sequence[float],
    x: Sequence[float],
    u: Sequence[float],
    theta: ParameterVector,
) -> float:
    """`ln λ` at ONE endpoint — the §5.1 five-factor product, in log space.

    Raises rather than clamps on `ρ_m · u_m ≥ 1`: that would make a suppression factor
    non-positive, i.e. `λ ≤ 0`, which §5.1 C-6 forbids by construction. Silently clamping it
    would convert a broken input into a plausible-looking output — the exact substitution
    §N.7 item 6 rules out.
    """
    total = log_base
    for w_s, la in zip(theta.w, log_a):
        total += w_s * la
    for b_j, x_j in zip(theta.beta, x):
        total += b_j * x_j
    for rho_m, u_m in zip(theta.rho, u):
        factor = 1.0 - rho_m * u_m
        if factor <= 0.0:
            raise ValueError(
                f"suppression factor (1 − ρ·u) = {factor} is not positive — §5.1 C-6 bounds "
                f"ρ ≤ 0.95 and u ≤ 1 exactly so this cannot happen; got ρ={rho_m}, u={u_m}"
            )
        total += math.log(factor)
    return total


def build_segments(basis: FieldBasis, theta: ParameterVector) -> list[FieldSegment]:
    """Rebuild the stored log-linear field for a given θ.

    `α_i = ln λ(t_i⁺)`, `γ_i = [ln λ(t_{i+1}⁻) − ln λ(t_i⁺)] / Δt` — §5.2's definition,
    applied verbatim. This is the ONLY place θ becomes a field, and it is what makes "the
    fitter optimises the model the product serves" true rather than aspirational.
    """
    basis.assert_conformable(theta)
    out: list[FieldSegment] = []
    for seg in basis.segments:
        alpha = log_lambda_endpoint(
            seg.log_base, seg.log_a_start, seg.x_start, seg.u_start, theta
        )
        log_end = log_lambda_endpoint(seg.log_base, seg.log_a_end, seg.x_end, seg.u_end, theta)
        width = seg.t_end - seg.t_start
        if width <= 0.0:
            raise ValueError(f"basis segment [{seg.t_start}, {seg.t_end}] has non-positive width")
        out.append(
            FieldSegment(
                t_start=seg.t_start,
                t_end=seg.t_end,
                alpha=alpha,
                gamma=(log_end - alpha) / width,
            )
        )
    return out


def clip_to_bounds(theta: ParameterVector) -> ParameterVector:
    """Project θ into its §5.1 box. Used only where the design says to project, never to hide
    an out-of-range fit: `fit.py` records a clip on the version row (`clipped = TRUE`)."""
    return ParameterVector(
        w=tuple(min(max(v, W_BOUNDS[0]), W_BOUNDS[1]) for v in theta.w),
        beta=tuple(min(max(v, BETA_BOUNDS[0]), BETA_BOUNDS[1]) for v in theta.beta),
        rho=tuple(min(max(v, RHO_BOUNDS[0]), RHO_BOUNDS[1]) for v in theta.rho),
    )


def bounds_for(basis: FieldBasis) -> list[tuple[float, float]]:
    """The L-BFGS-B box, in θ's own order."""
    n_w, n_b, n_r = basis.dimensions
    return [W_BOUNDS] * n_w + [BETA_BOUNDS] * n_b + [RHO_BOUNDS] * n_r
