"""
services/ka_kshetra/integrator.py — §5.2 the segment representation and EXACT
analytic integration.

On each segment [t_i, t_{i+1}] the field is stored LOG-LINEARLY:

    ln λ_e(t) = α_i + γ_i · (t − t_i)
    α_i = ln λ_e(t_i⁺)
    γ_i = [ ln λ_e(t_{i+1}⁻) − ln λ_e(t_i⁺) ] / (t_{i+1} − t_i)

This is a DEFINITION OF THE STORED FIELD, not an approximation claim. `kala_field`
holds (α_i, γ_i) and every downstream consumer — serving, integration, the
stage-5 null, the stage-9 fitter — reads THAT. The adaptive refinement below
bounds the gap between the stored field and the true product form; it does not
make the stored field "approximate", because the stored field IS what everything
downstream integrates.

── WHY LOG-LINEAR, AND WHAT IT BUYS ─────────────────────────────────────────
Three properties, each of which something downstream depends on:

  1. EXACT INTEGRATION IN CLOSED FORM.
         ∫_u^v exp(α + γ(t − t_i)) dt
           = ( exp(α + γ(v − t_i)) − exp(α + γ(u − t_i)) ) / γ           γ ≠ 0
           = exp(α) · (v − u)                                            γ = 0
     There is no quadrature anywhere in the serving or fitting path. §7.2 makes
     this load-bearing: "Λ is EXACTLY the §5.2 integrator — the same code path
     serves fitting and serving. ... if the fitter used a different integral, the
     published skill score would be measuring a model the product does not
     serve."

  2. MONOTONICITY PER SEGMENT ⇒ THE PEAK OF A WINDOW IS ALWAYS A BREAKPOINT.
     ln λ is linear on a segment, so λ attains its extremes at the segment's
     ends. A window's peak is therefore an argmax over a FINITE candidate set and
     needs no interior optimizer. §5.2: "this must not be 'improved' into one —
     the closed-form property is what makes the field hash-replayable."

  3. CLOSED-FORM WINDOW ENDPOINTS. A window boundary solves
     α_i + γ_i(t − t_i) = ln q, which is LINEAR in t. Endpoints are solved, never
     scanned, so two builds of the same field produce bit-identical window ids.

── THE NUMERICAL RULE THAT IS NOT OPTIONAL ──────────────────────────────────
For small |γ·(v−u)| the naive difference form
    ( e^{α+γΔ} − e^{α} ) / γ
subtracts two nearly-equal numbers and loses almost every significant digit —
relative error ≈ ε_machine / |γΔ|, so at γΔ = 1e-12 roughly four digits SURVIVE
out of sixteen. §5.2 therefore mandates the algebraically identical but
numerically stable form
    e^{α+γ(u−t_i)} · (v−u) · expm1(γΔ) / (γΔ)
This module uses that branch generously (|γΔ| < 1e-2, well beyond the 1e-4 the
design requires) and falls back to the difference form only where cancellation
cannot occur and where `expm1` itself could overflow. `test_integrator.py`'s
`TestAnalyticVsNumerical` pins the whole thing against a 10⁴-point composite
Simpson quadrature at 1e-9 relative, per §5.2's own acceptance requirement.

PURITY: no DB, no IO, no RNG. Same reason as hazard.py — this exact code path is
reused by the R = 256 circular-shift null replicates and by the stage-9 fitter.

Authority: KALA_W2_FIELD_DESIGN_v1_0.md §5.2, §5.3.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from typing import Callable, Iterable, Optional, Sequence

from services.ka_kshetra.contracts import Segment

#: §5.2's ε: below this |γ| the segment is treated as exactly flat. At |γ| ≤ 1e-12
#: per day the field changes by < 4e-8 nats across a whole century, which is
#: dozens of orders of magnitude below anything day-grade precision can support.
EPS_GAMMA: float = 1e-12

#: Cross-over to the `expm1` branch. The design mandates it below 1e-4; we use it
#: two orders of magnitude wider because it is strictly more accurate there and
#: because it keeps `expm1` away from its own overflow regime (|γΔ| ≳ 700).
EXPM1_BRANCH: float = 1e-2

#: §5.2 adaptive refinement: split while the midpoint residual exceeds τ nats.
#: 0.02 nats ≈ 2% in λ — below the resolution any downstream claim is served at.
DEFAULT_TAU: float = 0.02

#: §5.2: "to a MAXIMUM DEPTH OF 6 (≤ 64 sub-segments per original segment)".
DEFAULT_MAX_DEPTH: int = 6


@dataclass(frozen=True)
class Window:
    """A maximal interval where λ_e(t) ≥ q_e (§5.2).

    `t_peak` is an argmax over the window's BREAKPOINTS — see the module
    docstring's property (2). `expected_count` is Λ_e over the window: an
    expected NUMBER OF EVENTS, which is what makes PRIORITIZE's imminence and
    intensity axes dimensionally honest rather than unitless scores.
    """
    t_start: float
    t_end: float
    t_peak: float
    lambda_peak: float
    expected_count: float
    duration_days: float


# ── construction ─────────────────────────────────────────────────────────────

def build_segments(
    breakpoints: Sequence[float],
    ln_lambda: Callable[[float], float],
    *,
    tau: float = DEFAULT_TAU,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> list[Segment]:
    """Build the stored log-linear segments over the sorted, de-duplicated
    breakpoint set, with §5.2 adaptive refinement.

    `ln_lambda(t)` is the TRUE product form of §5.1 evaluated at t. Note it is
    called at `t_i` and `t_{i+1}` for every segment and at midpoints during
    refinement, so callers should make it cheap (the field evaluator memoizes its
    envelope lookups for exactly this reason).

    Refinement, per §5.2: evaluate the true ln λ at the segment midpoint; if it
    deviates from the stored linear form by more than τ nats, split there and
    recurse. A segment that still exceeds τ at `max_depth` is STORED ANYWAY with
    `refinement_exhausted = True` and its residual recorded — visible, never
    silent (LAW ZERO). Dropping such a segment would leave a hole in the field;
    silently accepting it would make the τ bound a claim with no detector.

    Fewer than two distinct breakpoints is an honest empty list, not an error:
    an event class with no computable horizon writes no field rows and is
    recorded in `kala_field_snapshots.skipped_classes` with its reason.
    """
    knots = sorted({float(t) for t in breakpoints if math.isfinite(t)})
    if len(knots) < 2:
        return []

    out: list[Segment] = []
    for t0, t1 in zip(knots, knots[1:]):
        _refine(t0, t1, ln_lambda, tau, max_depth, 0, out)
    return [replace(s, index=i) for i, s in enumerate(out)]


def _refine(
    t0: float,
    t1: float,
    ln_lambda: Callable[[float], float],
    tau: float,
    max_depth: int,
    depth: int,
    out: list[Segment],
) -> None:
    a = ln_lambda(t0)
    b = ln_lambda(t1)
    width = t1 - t0
    gamma = (b - a) / width
    tm = 0.5 * (t0 + t1)
    residual = abs(ln_lambda(tm) - (a + gamma * (tm - t0)))

    if residual <= tau:
        out.append(Segment(index=0, t_start=t0, t_end=t1, alpha=a, gamma=gamma,
                           refinement_depth=depth))
        return

    if depth >= max_depth:
        # Stored, flagged, and its residual recorded. §N.8: the flag has a real
        # detector behind it — this branch is exactly the code path that makes
        # `refinement_exhausted` correctly read True.
        out.append(Segment(index=0, t_start=t0, t_end=t1, alpha=a, gamma=gamma,
                           refinement_depth=depth, refinement_exhausted=True,
                           refinement_residual=residual))
        return

    _refine(t0, tm, ln_lambda, tau, max_depth, depth + 1, out)
    _refine(tm, t1, ln_lambda, tau, max_depth, depth + 1, out)


# ── evaluation ───────────────────────────────────────────────────────────────

def segment_ln_lambda(seg: Segment, t: float) -> float:
    """The STORED field's ln λ on this segment (no clamping to the span — the
    caller decides containment)."""
    return seg.alpha + seg.gamma * (t - seg.t_start)


def segment_lambda(seg: Segment, t: float) -> float:
    return math.exp(segment_ln_lambda(seg, t))


def lambda_at(segments: Sequence[Segment], t: float) -> float:
    """λ of the stored field at t, or 0.0 outside the field's span.

    At a shared breakpoint the RIGHT-hand segment wins, because α_i is DEFINED as
    ln λ(t_i⁺) (§5.2). Outside the span the value is 0.0, never an extrapolation:
    the field is defined on [0, H] and a claim outside it has no support.
    """
    seg = _segment_containing(segments, t)
    return 0.0 if seg is None else segment_lambda(seg, t)


def _segment_containing(segments: Sequence[Segment], t: float) -> Optional[Segment]:
    found: Optional[Segment] = None
    for seg in segments:
        if seg.t_start > t:
            break               # L1f: segments sorted by t_start; no later segment can contain t
        if seg.t_start <= t < seg.t_end:
            return seg
        if t == seg.t_end:
            found = seg          # keep looking: a right-hand neighbour wins
    return found


# ── EXACT analytic integration ───────────────────────────────────────────────

def segment_integral(seg: Segment, u: float, v: float) -> float:
    """∫_u^v λ dt over ONE segment's stored form. Exact; see module docstring.

    `u`/`v` are absolute times and are NOT clipped to the segment here — callers
    that need clipping use `integrate`. An empty or reversed interval is 0.0.
    """
    if not (v > u):
        return 0.0
    d = v - u
    g = seg.gamma
    base = seg.alpha + g * (u - seg.t_start)

    if abs(g) <= EPS_GAMMA:
        return math.exp(base) * d

    gd = g * d
    if abs(gd) < EXPM1_BRANCH:
        # THE MANDATED STABLE FORM. Algebraically identical to the difference
        # below; numerically it is the difference between ~12 correct digits and
        # ~4 (see module docstring).
        return math.exp(base) * d * (math.expm1(gd) / gd)

    # Cancellation-free regime: |e^{α+γΔ} − e^{α}| is comfortably larger than
    # either operand's ulp, and this form cannot overflow where the expm1 form
    # would (e^{α} tiny × expm1(γΔ) huge).
    return (math.exp(seg.alpha + g * (v - seg.t_start)) - math.exp(base)) / g


def integrate(segments: Sequence[Segment], a: float, b: float) -> float:
    """Λ_e(a, b) — the exact integrated hazard over [a, b].

    Additive over segments and over sub-intervals by construction, which is what
    lets `kala_field.integral_days` be denormalized per segment and summed by a
    consumer that never re-derives the exponentials.
    """
    if not (b > a):
        return 0.0
    total = 0.0
    for seg in segments:
        if seg.t_start >= b:
            break               # L1f: segments sorted by t_start; no later segment overlaps [a, b)
        u = max(a, seg.t_start)
        v = min(b, seg.t_end)
        if v > u:
            total += segment_integral(seg, u, v)
    return total


# ── windows: maximal super-threshold intervals, closed-form endpoints ────────

def find_windows(segments: Sequence[Segment], q: float) -> list[Window]:
    """Maximal intervals where λ_e(t) ≥ q, with peaks at breakpoints.

    `q` is stage 5's `q_e` — the 95th percentile of the chart's OWN
    circular-shifted null (§5.5) — so windows are null-calibrated BY
    CONSTRUCTION. A window is not "a stretch that scored highly"; it is "a
    stretch where this chart's hazard exceeds what its own shifted sky would
    produce 95% of the time".

    Endpoints are SOLVED, not scanned: on each segment λ ≥ q ⇔
    α + γ(t − t_i) ≥ ln q, linear in t. Adjacent super-threshold spans are merged
    so a window is genuinely MAXIMAL — three consecutive above-q segments are one
    window, not three.

    An empty result is an honest empty (LAW ZERO), and a caller must serve it as
    "no window exceeds this chart's own null", never as missing data.
    """
    if q <= 0.0 or not math.isfinite(q) or not segments:
        return []
    ln_q = math.log(q)

    spans: list[tuple[float, float]] = []
    for seg in segments:
        span = _super_threshold_span(seg, ln_q)
        if span is None:
            continue
        if spans and span[0] <= spans[-1][1] + _MERGE_EPS:
            spans[-1] = (spans[-1][0], max(spans[-1][1], span[1]))
        else:
            spans.append(span)

    windows: list[Window] = []
    for t_start, t_end in spans:
        t_peak, lambda_peak = _peak_over(segments, t_start, t_end)
        windows.append(Window(
            t_start=t_start,
            t_end=t_end,
            t_peak=t_peak,
            lambda_peak=lambda_peak,
            expected_count=integrate(segments, t_start, t_end),
            duration_days=t_end - t_start,
        ))
    return windows


#: Spans that touch to within this many days are the same window. Segment
#: boundaries are shared exactly (`a.t_end is b.t_start`), so this only absorbs
#: representation noise in a solved crossing, never a genuine gap: at day-grade
#: precision a 1e-9-day (86 µs) hole is not a real interruption.
_MERGE_EPS: float = 1e-9


def _super_threshold_span(seg: Segment, ln_q: float) -> Optional[tuple[float, float]]:
    """The sub-interval of `seg` where ln λ ≥ ln_q, or None."""
    lo = seg.alpha
    hi = seg.alpha + seg.gamma * (seg.t_end - seg.t_start)

    if abs(seg.gamma) <= EPS_GAMMA:
        return (seg.t_start, seg.t_end) if lo >= ln_q else None

    # Linear in t ⇒ a single crossing at t* = t_start + (ln_q − alpha)/gamma.
    t_cross = seg.t_start + (ln_q - seg.alpha) / seg.gamma
    if seg.gamma > 0:                      # rising: above threshold from t_cross on
        if hi < ln_q:
            return None
        return (max(seg.t_start, min(t_cross, seg.t_end)), seg.t_end)
    if lo < ln_q:                          # falling: above threshold up to t_cross
        return None
    return (seg.t_start, min(seg.t_end, max(t_cross, seg.t_start)))


def _peak_over(segments: Sequence[Segment], a: float, b: float) -> tuple[float, float]:
    """argmax λ over [a, b], evaluated ONLY at breakpoints.

    Valid because ln λ is linear — hence monotone — on every segment, so the
    extremes of each clipped piece are at its ends. Deterministic tie-break: the
    EARLIEST time wins, so a plateau reports its onset rather than an arbitrary
    interior point.
    """
    best_t = a
    best_v = -math.inf
    for seg in segments:
        if seg.t_start > b:
            break               # L1f: segments sorted; no later segment overlaps [a, b]
        u = max(a, seg.t_start)
        v = min(b, seg.t_end)
        if v < u:
            continue
        for t in (u, v):
            val = segment_lambda(seg, t)
            if val > best_v or (val == best_v and t < best_t):
                best_v, best_t = val, t
    if best_v == -math.inf:                # no overlap at all — degenerate span
        return a, lambda_at(segments, a)
    return best_t, best_v


# ── the window id (item 44's authority_basis value) ──────────────────────────

def window_id(
    chart_id: str,
    event_class: str,
    t_start: float,
    t_end: float,
    weights_version: str,
    x_schema_version: str,
) -> str:
    """§5.2's stable, deterministic window id — THE `authority_basis` VALUE.

    Every temporal claim product-wide cites this (item 44 / the SINGLE TEMPORAL
    AUTHORITY rail); a serving path that computes its own window is a build
    error, not a divergence to classify.

    Times are rounded to 6 decimals (≈ 0.09 s) inside the hash so a
    float-representation wobble far below day-grade precision cannot mint a new
    authority id for the same window. `weights_version` and `x_schema_version`
    are inputs BECAUSE a refit genuinely produces a different window — the id
    must not silently survive a model change, or a drill would resolve a claim to
    evidence computed under different weights.
    """
    payload = (
        f'{chart_id}|{event_class}|{round(float(t_start), 6)}|{round(float(t_end), 6)}'
        f'|{weights_version}|{x_schema_version}'
    )
    return 'kfw_' + hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]


def segment_target_id(event_class: str, segment_index: int) -> str:
    """`kala_field_provenance.target_id` for a segment target (§5.4)."""
    return f'{event_class}#{segment_index}'


__all__ = [
    'EPS_GAMMA', 'EXPM1_BRANCH', 'DEFAULT_TAU', 'DEFAULT_MAX_DEPTH',
    'Segment', 'Window',
    'build_segments', 'segment_ln_lambda', 'segment_lambda', 'lambda_at',
    'segment_integral', 'integrate', 'find_windows',
    'window_id', 'segment_target_id',
]
