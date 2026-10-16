"""Operator-complete G1 trial compiler; not imported by a live writer.

After all max/min roots and supplied boundaries, only sum(log(1-rho*u)) is
curved. Its second derivative magnitude is bounded by
sum((rho*u' / min(1-rho*u))**2). Linear interpolation error is <= M*h*h/8
on EACH segment, not just its midpoint. Real-arithmetic analytic bounds are
separate from the declared 1e-12 floating evaluation tolerance in the trial.
Reaching depth six does not establish the bound: exhaustion stays visible.

(I) INTERPRETATION: G1's existing extra_breakpoints carries upstream kinematic,
scenario and mask edges; this compiler preserves them. It does not invent a
risk-set/masking model or G2 schema absent from FieldEvaluator.
"""
from __future__ import annotations

import bisect
import math
from dataclasses import dataclass

from services.ka_kshetra import hazard
from services.ka_kshetra.contracts import Segment
from services.ka_kshetra.stage4_field import FieldEvaluator, EnvelopeIndex
from .representation import CompactField


@dataclass(frozen=True)
class Compilation:
    field: CompactField
    bounds: tuple[float, ...]
    tau: float
    operator_knots: tuple[float, ...]

    @property
    def proven(self) -> bool:
        return (len(self.bounds) == len(self.field.segments()) and
                all(math.isfinite(b) and 0 <= b <= self.tau for b in self.bounds) and
                not any(s.refinement_exhausted for s in self.field.segments()))


def _validate(ev: FieldEvaluator) -> None:
    # The curvature proof is for THIS formula, not an arbitrary callable or an
    # override that could hide extra operators between the declared knots.
    if type(ev) is not FieldEvaluator or type(ev.envelopes) is not EnvelopeIndex:
        raise ValueError('only the existing G1 FieldEvaluator formula is supported')
    if not math.isfinite(ev.horizon_days) or ev.horizon_days <= 0:
        raise ValueError('positive finite horizon required')
    if ev.envelopes.horizon_days != ev.horizon_days:
        raise ValueError('envelope horizon mismatch')
    if not all(math.isfinite(v) for v in ev.weights.values()):
        raise ValueError('finite weights required')
    if not all(math.isfinite(t) for t in ev.extra_breakpoints):
        raise ValueError('finite extra breakpoints required')
    for periods in ev.ladder.values():
        for p in periods:
            if not all(math.isfinite(t) for t in (p.t_start, p.t_end)) or p.t_end <= p.t_start:
                raise ValueError('invalid clock boundaries')
    for p in ev.envelopes.supportive + ev.envelopes.obstructive:
        knots = p.knots
        if (len(knots) < 2 or knots[-1][0] <= knots[0][0] or
                any(not math.isfinite(t) or not math.isfinite(v) or not 0 <= v <= 1 for t, v in knots) or
                any(t > u for (t, _), (u, _) in zip(knots, knots[1:]))):
            raise ValueError('invalid primitive knots')


def _line(p, a: float, b: float) -> tuple[float, float]:
    """The exact affine branch's values at a+ and b- (duplicate knots = steps)."""
    mid = a + (b - a) / 2
    if mid < p.t_start or mid > p.t_end:
        return 0.0, 0.0
    i = bisect.bisect_right([t for t, _ in p.knots], mid) - 1
    t0, v0 = p.knots[i]
    t1, v1 = p.knots[i + 1]
    slope = (v1 - v0) / (t1 - t0)
    return v0 + slope * (a - t0), v0 + slope * (b - t0)


def _groups(ev, a, b):
    groups: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for p in ev.envelopes.supportive:
        for key in ev.envelopes._covariate_keys(p):
            groups.setdefault(('x', key), [(0.0, 0.0)]).append(_line(p, a, b))
    for p in ev.envelopes.obstructive:
        groups.setdefault(('u', p.vighna_key()), [(0.0, 0.0)]).append(_line(p, a, b))
    return groups


def _selected(ev, a, b):
    return {key: max(lines, key=lambda v: v[0] + v[1]) for key, lines in _groups(ev, a, b).items()}


def _root(a, b, left, right):
    if (left < 0 < right) or (right < 0 < left):
        root = a + (b - a) * (-left) / (right - left)
        if a < root < b:
            return root
    return None


def operator_breakpoints(ev: FieldEvaluator) -> tuple[float, ...]:
    _validate(ev)
    base = ev.breakpoints()
    roots = set(base)
    for a, b in zip(base, base[1:]):
        for lines in _groups(ev, a, b).values():
            for i, x in enumerate(lines):
                for y in lines[i + 1:]:
                    r = _root(a, b, x[0] - y[0], x[1] - y[1])
                    if r is not None:
                        roots.add(r)
    max_knots = sorted(roots)
    for a, b in zip(max_knots, max_knots[1:]):
        values = _selected(ev, a, b)
        moon = values.get(('x', 'contact_moon_ref'), (0, 0))
        lagna = values.get(('x', 'contact_lagna_ref'), (0, 0))
        r = _root(a, b, moon[0] - lagna[0], moon[1] - lagna[1])
        if r is not None:
            roots.add(r)
    return tuple(sorted(roots))


def _limits_and_curvature(ev, a, b):
    values = _selected(ev, a, b)
    covariates = [{}, {}]
    obstructions = [{}, {}]
    curvature = 0.0
    for (kind, key), ends in values.items():
        for j, v in enumerate(ends):
            (covariates if kind == 'x' else obstructions)[j][key] = v
        if kind == 'u':
            rho = float(ev.weights.get(hazard._rho_weight_id(key), ev.weights.get('rho:default', 0.25)))
            if not math.isfinite(rho) or not 0 <= rho <= hazard.RHO_MAX:
                raise ValueError('invalid suppression rho')
            slope = (ends[1] - ends[0]) / (b - a)
            curvature += (rho * slope / (1 - rho * max(ends))) ** 2
    stacks = ev.lord_stacks_at(a + (b - a) / 2)
    limits = tuple(hazard.evaluate(
        lifetime_count=ev.lifetime_count, promise=ev.promise, clocks=ev.clocks,
        lord_stacks=stacks, covariates=covariates[j], obstructions=obstructions[j],
        weights=ev.weights, baseline_source=ev.baseline_source, shape_only=ev.shape_only,
    ).ln_lambda for j in (0, 1))
    if not all(math.isfinite(v) for v in limits):
        raise ValueError('nonfinite log field')
    return limits, curvature


def compile_field(ev: FieldEvaluator, *, tau: float = 0.02, max_depth: int = 6) -> Compilation:
    if not math.isfinite(tau) or tau <= 0 or type(max_depth) is not int or not 0 <= max_depth <= 6:
        raise ValueError('positive finite tau and depth in [0,6] required')
    knots = operator_breakpoints(ev)
    rows, bounds = [], []

    def refine(a, b, depth):
        (left, right), curvature = _limits_and_curvature(ev, a, b)
        bound = curvature * (b - a) ** 2 / 8
        if bound > tau and depth < max_depth:
            mid = a + (b - a) / 2
            if not a < mid < b:
                raise ValueError('refinement is below floating time resolution')
            refine(a, mid, depth + 1)
            refine(mid, b, depth + 1)
            return
        gamma = (right - left) / (b - a)
        mid = a + (b - a) / 2
        residual = abs(ev.ln_lambda(mid) - (left + gamma * (mid - a))) if bound > tau else None
        rows.append(Segment(len(rows), a, b, left, gamma, depth, bound > tau, residual))
        bounds.append(bound)

    for a, b in zip(knots, knots[1:]):
        refine(a, b, 0)
    return Compilation(CompactField.from_segments(rows), tuple(bounds), tau, knots)
