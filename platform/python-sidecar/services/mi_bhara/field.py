"""
field.py — the stored segment representation of the hazard field, and its EXACT analytic
integrator.

Spec: `KALA_W2_FIELD_DESIGN_v1_0.md` §5.2.

── THE STORED FIELD IS A DEFINITION, NOT AN APPROXIMATION ─────────────────────────────────
On each breakpoint segment `[t_i, t_{i+1}]` the field is stored log-linearly:

    ln λ(t) = α_i + γ_i · (t − t_i)
    α_i = ln λ(t_i⁺)
    γ_i = [ ln λ(t_{i+1}⁻) − ln λ(t_i⁺) ] / (t_{i+1} − t_i)

`kala_field` holds `(α_i, γ_i)` and EVERY downstream consumer — serving, integration, the
null, and the fitter in this package — reads *that*. So "the integral is exact" is a claim
about the stored representation, and it is exactly true; the separate question of how closely
the stored representation tracks the true product form is answered by stage 4's adaptive
refinement (§5.2, `τ = 0.02` nats), which is Lane C's, not this module's.

── WHY LANE E OWNS A COPY OF THE INTEGRATOR AT ALL ────────────────────────────────────────
It does not own a *copy*: it owns THE integrator for the fitting path, and the §7.2 contract
is that the fitter and the serving path use the SAME one. Lane C's stage-4 writer computes the
`(α, γ)` rows; this module consumes them. Cross-lane, the contract is the TABLE SHAPE
(`kala_field`'s `t_start / t_end / alpha / gamma`) — never the other lane's code (§0). If a
future session finds two integrators in the tree, one of them is wrong by construction and the
right fix is to delete it, not to reconcile them.

Everything in this module is a pure function. No DB, no clock, no RNG.
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from typing import Iterable, Sequence

# `ε` from §5.2: below this |γ| the segment is treated as flat. The stable `expm1` form below
# is exact for every non-zero γ, so this constant only guards a literal division by zero.
GAMMA_EPSILON = 1e-12


@dataclass(frozen=True)
class FieldSegment:
    """One row of `kala_field`, in the shape §5.2 freezes.

    `alpha` is `ln λ` at `t_start⁺`; `gamma` is `d(ln λ)/dt` on the segment. Both are stored,
    not derived, so a consumer never has to re-evaluate the five-factor product form.
    """

    t_start: float
    t_end: float
    alpha: float
    gamma: float

    def __post_init__(self) -> None:
        if not (self.t_end > self.t_start):
            raise ValueError(
                f"FieldSegment must have t_end > t_start; got [{self.t_start}, {self.t_end}]"
            )

    @property
    def duration(self) -> float:
        return self.t_end - self.t_start

    def log_lambda_at(self, t: float) -> float:
        """`ln λ(t)` on this segment (no containment check — see `log_lambda`)."""
        return self.alpha + self.gamma * (t - self.t_start)

    def lambda_at(self, t: float) -> float:
        return math.exp(self.log_lambda_at(t))


def _validate_contiguous(segments: Sequence[FieldSegment]) -> None:
    for a, b in zip(segments, segments[1:]):
        if b.t_start < a.t_end - 1e-9:
            raise ValueError(
                "field segments overlap or are unsorted: "
                f"[{a.t_start}, {a.t_end}] then [{b.t_start}, {b.t_end}]"
            )


def log_lambda(segments: Sequence[FieldSegment], t: float) -> float:
    """`ln λ(t)`, read from the stored representation.

    Boundary convention (fixed, and it matters for the log-likelihood's `Σ_k ln λ(t_k)` term):
    a `t` sitting exactly on an interior breakpoint belongs to the segment STARTING there —
    i.e. `α_i` wins over `α_{i−1} + γ_{i−1}·Δ`. The two agree to within the refinement
    tolerance in practice, but the rule is stated so two implementations cannot disagree.

    A `t` outside the field's support raises. Returning `-inf` (λ = 0) would be a lie: the
    hazard is strictly positive everywhere by construction (§5.1's `P_floor` and `ρ_max`
    exist precisely to guarantee that), so "outside the support" is a caller bug, not a zero.
    """
    if not segments:
        raise ValueError("cannot evaluate ln λ on an empty field")
    starts = [s.t_start for s in segments]
    idx = bisect.bisect_right(starts, t) - 1
    if idx < 0:
        raise ValueError(f"t={t} precedes the field's support (starts at {segments[0].t_start})")
    seg = segments[idx]
    if t > seg.t_end + 1e-9:
        raise ValueError(
            f"t={t} falls outside the field's support (last segment ends at {segments[-1].t_end})"
        )
    return seg.log_lambda_at(t)


def _segment_integral(seg: FieldSegment, u: float, v: float) -> float:
    """`∫_u^v λ` over one segment, `[u, v] ⊆ [t_start, t_end]`.

    §5.2's closed form is
        (exp(α + γ(v − t_i)) − exp(α + γ(u − t_i))) / γ
    which is algebraically identical to
        exp(α + γ(u − t_i)) · expm1(γ·(v − u)) / γ.
    The second form is used ALWAYS, not only in the small-|γΔ| branch the design flags: it is
    exact for every non-zero γ and it removes the catastrophic cancellation that the first
    form suffers whenever the two exponentials are close (the design's mandated numerical
    rule, applied unconditionally rather than behind a threshold, because a threshold is one
    more thing that can be wrong).
    """
    width = v - u
    if width <= 0.0:
        return 0.0
    if abs(seg.gamma) <= GAMMA_EPSILON:
        return math.exp(seg.alpha) * width
    g_dt = seg.gamma * width
    return math.exp(seg.alpha + seg.gamma * (u - seg.t_start)) * math.expm1(g_dt) / seg.gamma


def integrate(segments: Sequence[FieldSegment], a: float, b: float) -> float:
    """`Λ(a, b) = ∫_a^b λ(t) dt` — the integrated hazard, in expected events.

    Exact for the stored representation (§5.2). This is the single integral used by BOTH the
    serving path and the fitter: `expected_count` on a window, `Λ_e(0, T)` in the Poisson
    log-likelihood, and `τ_k = Λ(t_{k−1}, t_k)` in the time-rescaling GOF are all this call.
    """
    if b < a:
        raise ValueError(f"integrate() requires b >= a; got a={a}, b={b}")
    if not segments:
        raise ValueError("cannot integrate an empty field")
    _validate_contiguous(segments)
    total = 0.0
    for seg in segments:
        u = max(a, seg.t_start)
        v = min(b, seg.t_end)
        if v > u:
            total += _segment_integral(seg, u, v)
    return total


def support(segments: Sequence[FieldSegment]) -> tuple[float, float]:
    """`(t_start of the first segment, t_end of the last)`."""
    if not segments:
        raise ValueError("empty field has no support")
    return segments[0].t_start, segments[-1].t_end


def constant_field(rate: float, t_start: float, t_end: float) -> list[FieldSegment]:
    """A single flat segment with `λ ≡ rate`.

    Not a test helper living in production code by accident: the circular-shift null's own
    degenerate case, the LEL-absent baseline, and every closed-form verification of this
    module's arithmetic are homogeneous-Poisson, and a homogeneous field must be expressible
    in exactly the same representation as an inhomogeneous one or the two paths diverge.
    """
    if rate <= 0.0:
        raise ValueError(f"hazard rate must be strictly positive (§5.1); got {rate}")
    return [FieldSegment(t_start=t_start, t_end=t_end, alpha=math.log(rate), gamma=0.0)]


def segments_from_rows(rows: Iterable[dict]) -> list[FieldSegment]:
    """Adapt `kala_field` rows (Lane C's table) into `FieldSegment`s, sorted by `t_start`.

    The cross-lane contract is this table shape and nothing else (§0): four columns, read-only.
    """
    segs = [
        FieldSegment(
            t_start=float(r["t_start"]),
            t_end=float(r["t_end"]),
            alpha=float(r["alpha"]),
            gamma=float(r["gamma"]),
        )
        for r in rows
    ]
    segs.sort(key=lambda s: s.t_start)
    _validate_contiguous(segs)
    return segs
