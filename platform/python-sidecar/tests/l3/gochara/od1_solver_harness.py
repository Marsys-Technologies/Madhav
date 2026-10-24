"""SR-OD1 S1 — the ANALYTIC HARNESS for the window solver (plan §2.6): worlds with closed-form maxima, no database, no Swiss.

A world is a `window_solver.Problem` whose tents are polynomial offsets `o0 + o1·(t−t0) + o2·(t−t0)²` (degrees, seconds) with the exact
velocity and an exact acceleration bound, so the true maximum, its instant and every cut are known on paper. `dense_max` is the
independent reference (a numpy scan of `objective_values`, locally polished) used by the randomised differential run; the closed-form
oracles in the test file never use it.

This module is test infrastructure only (it is NOT in the implementation digest and not imported by production code); the S2
checker's builder↔verifier differential reuses it.
"""
from __future__ import annotations

import numpy as np

from services.gochara_kernel import window_solver as sol

DAY = 86400.0
ORBS = (0.5, 1.0, 2.0, 5.0)


def poly_tent(orb, o0, o1=0.0, o2=0.0, *, t0=0.0, stations=(), h4=True, spacing=20 * DAY, hint=None, velocity=True):
    """offset(t) = o0 + o1·(t−t0) + o2·(t−t0)²  [deg, s]; velocity and |offset''| = 2|o2| are exact (H4 supplied iff `h4`)."""
    return sol.Tent(
        offset=lambda t: o0 + o1 * (t - t0) + o2 * (t - t0) ** 2,
        orb=orb,
        velocity=(lambda t: o1 + 2.0 * o2 * (t - t0)) if velocity else None,
        accel_bound=(lambda l, r: 2.0 * abs(o2)) if h4 else None,
        stations=tuple(stations), min_station_spacing=spacing, exact_hint=hint)


def member(key, group, supports, tent=None, steps=()):
    return sol.Member(key=key, group=group, supports=tuple(supports), steps=tuple(steps), tent=tent)


class Piecewise(sol.Step):
    """A step factor with the exact change instants listed, complete (the H2 contract), and a numpy path for the dense reference."""

    def __init__(self, edges, values, *, complete=True, list_edges=True):
        edges, values = tuple(edges), tuple(values)
        assert len(values) == len(edges) + 1

        def value_at(t, _e=edges, _v=values):
            return _v[sum(1 for e in _e if e <= t)]
        object.__setattr__(self, "value_at", value_at)
        object.__setattr__(self, "boundaries", (lambda lo, hi, _e=edges: [e for e in _e if lo < e < hi]) if list_edges else None)
        object.__setattr__(self, "complete", complete)
        object.__setattr__(self, "constant", False)
        object.__setattr__(self, "unknown_reason", None)
        object.__setattr__(self, "edges", edges)
        object.__setattr__(self, "values", values)

    def vec(self, ts):
        return np.asarray(self.values)[np.searchsorted(np.asarray(self.edges), ts, side="right")]


# ── the reference: a vectorised F ────────────────────────────────────────────────────────────────────────────────────────────

def objective_values(problem: sol.Problem, ts: np.ndarray) -> np.ndarray:
    """F on an array of instants (NaN where undeterminable: the min objective without both groups)."""
    groups: dict = {}
    for m in problem.members:
        live = np.zeros(ts.shape, dtype=bool)
        for s0, s1 in m.supports:
            live |= (ts >= s0) & (ts < s1)
        v = np.where(live, 1.0, 0.0)
        for st in m.steps:
            v = v * (st.vec(ts) if hasattr(st, "vec") else np.vectorize(st.value_at)(ts))
        if m.tent is not None:
            v = v * np.maximum(0.0, 1.0 - np.abs(m.tent.offset(ts)) / m.tent.orb)
        # liveness is tracked separately so a live member of value 0 still makes its group live
        g = groups.setdefault(m.group, [np.zeros(ts.shape), np.zeros(ts.shape, dtype=bool)])
        g[0] = np.maximum(g[0], v)
        g[1] |= live
    if problem.objective == sol.OBJECTIVE_SUM:
        return sum(g[0] for g in groups.values()) if groups else np.zeros(ts.shape)
    both = np.ones(ts.shape, dtype=bool)
    for g in groups.values():
        both &= g[1]
    out = np.minimum.reduce([g[0] for g in groups.values()])
    return np.where(both, out, np.nan)


def dense_max(problem: sol.Problem, *, dt=0.02, polish=True):
    """(max F, argmax) of a dense scan of the in-domain window, with the best few scan maxima locally polished. A LOWER bound of the
    true maximum that converges to it; the solver must be ≥ it and within a few ·slope·dt′ above."""
    hi = problem.hi - sol.QUANT
    ts = np.arange(problem.lo, hi, dt)
    ts = np.append(ts, hi)
    f = objective_values(problem, ts)
    f = np.where(np.isnan(f), -1.0, f)
    order = np.argsort(f)[::-1][:8]
    best_v, best_t = f[order[0]], ts[order[0]]
    if polish:
        for i in order:
            lo, hi2 = max(problem.lo, ts[i] - 2 * dt), min(hi, ts[i] + 2 * dt)
            fine = np.linspace(lo, hi2, 4001)
            fv = objective_values(problem, fine)
            fv = np.where(np.isnan(fv), -1.0, fv)
            j = int(np.argmax(fv))
            if fv[j] > best_v:
                best_v, best_t = fv[j], fine[j]
    return float(best_v), float(best_t)


# ── closed-form worlds ───────────────────────────────────────────────────────────────────────────────────────────────────────

def hump_world(orb, *, T=2.0e5, sigma=0.25, a0=0.95, b0=0.10, t_start=0.0, lift=0.0, group_a="rA", group_b="rB", h4=True, key="h"):
    """Plan C-S1 / spec O-SM-4: a RISING linear tent A (offset a0·orb − σ·orb·τ) plus a FALLING quadratic tent B (offset b0·orb + σ·orb·τ²),
    τ = (t − t_start)/T ∈ [0,1], two different roots. Both stay inside the orb throughout, so there is NO cut: one mixed piece.

        F(τ) = 2 − (a0 + b0) + lift + σ·τ(1−τ)        maximum  M = 2 − a0 − b0 + lift + σ/4   at   t* = t_start + T/2.
    (`lift` shifts F by a constant through B's offset: b0 → b0 − lift.)  Returns (members, M, t*)."""
    b0 = b0 - lift
    v = sigma * orb / T                                   # deg/s
    k = sigma * orb / (T * T)                             # deg/s²
    ta = poly_tent(orb, a0 * orb, -v, 0.0, t0=t_start, h4=h4)
    tb = poly_tent(orb, b0 * orb, 0.0, k, t0=t_start, h4=h4)
    sup = ((t_start, t_start + T),)
    ms = (member(f"{key}A", group_a, sup, ta), member(f"{key}B", group_b, sup, tb))
    return ms, 2.0 - a0 - b0 + sigma / 4.0, t_start + T / 2.0


def sinusoid_tent(orb, radius, omega, phase, *, stations=(), spacing=None):
    """A body oscillating about its target: offset = R·sin(ω·t + φ) — the plan's "sinusoid-with-station" world. Stations (velocity zero) are at
    ω·t + φ = π/2 + mπ; the half-period is the station spacing."""
    return sol.Tent(
        offset=lambda t: radius * float(np.sin(omega * t + phase)),
        orb=orb,
        velocity=lambda t: radius * omega * float(np.cos(omega * t + phase)),
        accel_bound=lambda l, r: radius * omega * omega,
        stations=tuple(stations),
        min_station_spacing=(np.pi / omega) if spacing is None else spacing)


def crest_member(key, group, orb, *, t_crest, speed, support, h4=True, hint=None):
    """A single tent whose body crosses its target (offset 0) at exactly `t_crest` at `speed` deg/s: v(t) is a triangle, crest 1.0 there."""
    return member(key, group, (support,), poly_tent(orb, 0.0, speed, 0.0, t0=t_crest, h4=h4, hint=hint))
