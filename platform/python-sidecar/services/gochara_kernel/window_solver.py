"""Window solver — certified piecewise-monotone branch-and-bound (CPM-BB) for the two frozen window objectives
(SR-OD1 plan §2; SR-SOLVER-PLAN-1; task S1).

Pure: no DB, no clock, no ephemeris of its own, no import from `window_sweep` / `window_verifier` (the sweep will call this
module in S3; the independent prover `window_solver_check` shares NOTHING with it). Time is a float number of SECONDS from a
caller-chosen origin; angles are degrees; the caller converts to/from datetimes (µs-quantised).

WHAT IT MAXIMISES (plan §2.1). A window `[lo, hi)` carries members (admitted records). Each member's value is a product of
factors — constants / STEP factors (piecewise constant between boundary instants the caller must supply completely) and at most
one TENT `max(0, 1 − |offset(t)|/orb)` (the point activity kernel, `kernel_factor.activity_kernel`'s arithmetic). Objectives:

  * `sum_of_group_max` (`evidence_for_per_root_sum`):  F(t) = Σ_roots max_members v(t)
  * `min_of_group_max` (`max_min_agent_activity`, P4):  F(t) = min(act_Jupiter(t), act_Saturn(t)),  act = max_members v(t)

and returns `M = max F` over the µs-quantised half-open window (a right-open end is taken at `b − 1 µs`) and `t*`, the EARLIEST
instant among F's DISTINCT LOCAL MAXIMA whose value is within `TIE = 1e-9` of `M` (frozen tie rule, N-11 — never "the first
instant within tolerance on a smooth hump's shoulder").

THE GUARANTEE (G) — under hypotheses H1–H4, the result is either a number or a NAMED BLANK; never a best-found value:

  H1 monotone arcs      every tent term's offset is monotone between listed Swiss stations (checked here: velocity sign at
                        spacing ≤ 5 d and the audited minimum station spacing > that spacing, `monotone_arc_not_established`)
  H2 complete steps     every non-constant step factor lists its change instants and asserts the list complete
                        (`state_boundaries_incomplete`); the piece values are cross-sampled as a second detector
  H3 the pinned ephemeris  `Tent.offset` is a deterministic continuous function (the caller's seam)
  H4 kinematic bounds   |offset''| ≤ A over an interval (`Tent.accel_bound`); the builder uses it to converge on smooth
                        interior maxima. Without it only the first-order (monotone-endpoint) bound is used — still rigorous,
                        slower, and the budget decides (`solver_budget_exhausted`).

  M̂ ≤ M ≤ M̂ + EPS_M (=1e-11 + root/quantisation terms ≤ the 1e-10 certificate) and t* is the earliest distinct local maximum
  within TIE of the top, located to TIME_TOL by bisection on the exact derivative (analytic worlds) — or blank.

KNOWN LIMIT (H5, stated, not hidden): two distinct interior stationary maxima closer together than one LEAF (K·h²/2 ≤ LEAF_CURV;
≈ 0.3–2 s on the real sky) and within TIE of each other are reported as the one the refinement finds. The independent
verifier derives its own earliest extremum; a disagreement there is UNVERIFIED (a seal blocker), not silent.

METHOD (plan §2.3). (1) CUTS: window ends, support ends, step boundaries, listed stations, and — for every tent on every monotone
stretch — the three roots of its monotone offset (`d = orb`, crest, exit) by BISECTION on a monotone function; a stored `t_exact`
is never trusted (`Tent.exact_hint` is ignored by design). (2) Between cuts every tent is constant, or monotone and C²; hence
sup F ≤ U1 = Σ_roots max_ρ max(f_ρ(l), f_ρ(r)) — a THEOREM needing no speed constant — and, with H4, the second-order bound
U2 (convex Taylor upper models about the midpoint, maximised at the interval ends). (3) A piece whose tents all rise (or all
fall, or none) is MONOTONE: its sup is an endpoint, exact. (4) A MIXED piece (a rising and a falling term) is searched:
pass 1 best-first on U proves M; pass 2 (pruning `U < M̂ − TIE`, never `U ≤ best`) resolves every alive stretch to a leaf where F is
affine to LEAF_CURV, samples it, and finds each distinct local maximum. (5) All pieces' samples form ONE ordered sequence; its
plateau-aware local maxima are the candidates; the earliest within TIE of the top is t*. (6) Budgets: `MAX_EVALS_WINDOW`, and a shared
`Budget` per grain — exhaustion ⇒ blank `solver_budget_exhausted`.

S0 findings used: the Swiss longitude is non-monotone by up to 3.9e-9° inside a stored (spline) segment next to a station, so a
caller lists the Swiss stations in `Tent.stations` (extra cuts); `A_QUIET` + limb windows (`accel_bound_provider`) are the H4 table
(audit and limb-window list generation are S3).
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Callable, Optional, Sequence

# ── objectives, reasons, tolerances ──────────────────────────────────────────

OBJECTIVE_SUM = "sum_of_group_max"          # evidence_for_per_root_sum (P1/P2/P3)
OBJECTIVE_MINMAX = "min_of_group_max"       # max_min_agent_activity    (P4)

SOLVED, BLANK = "solved", "blank"

# named reasons (the gate's `solver_certificate` group, added in S3)
REASON_BUDGET = "solver_budget_exhausted"
REASON_MONOTONE = "monotone_arc_not_established"
REASON_CERTIFICATE = "solver_certificate_incomplete"
REASON_BOUNDARIES = "state_boundaries_incomplete"          # the sweep's existing code, same string
REASON_UNKNOWN = "objective_unknown_over_component"        # the sweep's existing code, same string
REASON_UNDETERMINABLE = "objective_undeterminable"         # the sweep's existing code: the window has no determinable instant at all

QUANT = 1e-6                 # the µs quantisation: a right-open end is evaluated at b − QUANT
TIE = 1e-9                   # frozen peak-tie tolerance between DISTINCT local maxima (window_sweep._TIE)
EPS_PLATEAU = 1e-12          # values equal to float noise are ONE plateau (window_sweep._EPS)
EPS_M = 1e-11                # branch-and-bound stops when no interval can beat the incumbent by more than this
TIME_TOL = 5e-8              # root / extremum location (≈ float resolution of a 10^8 s window offset)
LEAF_CURV = 4e-12            # an interval is a LEAF when each term is affine to this much
MONO_TOL = 1e-11             # tent-value comparisons for the monotone-piece check
H1_SPACING_S = 5.0 * 86400.0
MAX_EVALS_WINDOW = 500_000   # ephemeris-call budget of ONE window (I: sized from S0 — 75.6 evals/record, 34,742 records, 6,629 windows)


class SolverRefusal(RuntimeError):
    """The input is malformed (a step value outside [0,1], a non-finite number): refused loudly, never defaulted."""


class _Blank(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(reason)
        self.reason, self.detail = reason, detail


class BudgetExhausted(Exception):
    pass


# ── the problem ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Tent:
    """`v(t) = max(0, 1 − |offset(t)|/orb)` — the point activity kernel. `offset` is the SIGNED angular offset of the body from
    the target (the aspect ray included), in degrees, continuous over the support (the caller unwraps the seam)."""
    offset: Callable[[float], float]
    orb: float
    velocity: Optional[Callable[[float], float]] = None             # d offset / dt, deg/s (H1; the ephemeris speed output)
    accel_bound: Optional[Callable[[float, float], Optional[float]]] = None   # bound on |offset''| over [l, r], deg/s² (H4); None = none
    stations: tuple = ()                                              # Swiss station instants (extra cuts, S0 K-2)
    min_station_spacing: Optional[float] = None                       # audited minimum spacing between stations, seconds (H1)
    exact_hint: Optional[float] = None                                # a stored `t_exact`: IGNORED by design (never trusted)


@dataclass(frozen=True)
class Step:
    """A step factor: constant between its change instants. `constant=True` asserts it never changes over any support (no
    boundaries needed); otherwise `boundaries(lo, hi)` must list EVERY change instant in the open interval and `complete`
    must be True (H2). `value_at` is right-continuous; None = undeterminable (a named blank, never a default)."""
    value_at: Callable[[float], Optional[float]]
    boundaries: Optional[Callable[[float, float], Sequence[float]]] = None
    complete: bool = False
    constant: bool = False
    unknown_reason: Optional[Callable[[float], Optional[str]]] = None


def constant_step(value: float) -> Step:
    return Step(value_at=lambda t, _v=value: _v, constant=True)


@dataclass(frozen=True)
class Member:
    """One admitted record. A PER-INSTANT channel (P1's agent_nature, W0 `channel_at`) is a `Step` valued 1.0 on the for-channel and 0.0
    on the against-channel (a record on the against side adds nothing to the for-sum), its change instants listed like any step's.
    `group` is the root (sum objective: per-root max over members, summed over roots) or the agent (min objective)."""
    key: str
    group: str                                   # the root (sum objective) or the agent (min objective)
    supports: tuple                              # ((lo, hi), ...) half-open
    steps: tuple = ()
    tent: Optional[Tent] = None


@dataclass(frozen=True)
class Problem:
    lo: float
    hi: float
    objective: str
    members: tuple


@dataclass(frozen=True)
class SolveResult:
    status: str                                  # SOLVED | BLANK
    value: Optional[float]                       # M̂ — the global maximum (None when blank)
    instant: Optional[float]                     # t* — the earliest distinct local maximum within TIE (None when blank)
    reason: Optional[str]                        # the named reason (None when solved)
    evals: int
    detail: str = ""
    certificate: Optional[dict] = None           # solved windows only: the facts the claim rests on

    @property
    def peak_value(self) -> Optional[float]:
        return None if self.certificate is None else self.certificate["value_at_instant"]


class Budget:
    """A shared evaluation budget (one per grain). `remaining` is decremented by every ephemeris call of every window solved
    against it."""

    def __init__(self, max_evals: int):
        self.remaining = int(max_evals)
        self.spent = 0


def grain_budget_evals(allowance_seconds: float, n_grains: int, seconds_per_eval: float) -> int:
    """MAX_EVALS_GRAIN = floor(allowance / (n_grains × c)) — S0 §1: 18,000 s, 104 grains; c = 2.1 µs … 100 µs."""
    return int(allowance_seconds // (n_grains * seconds_per_eval))


# ── H4: the audited kinematic-bound table (S0 §2.3; AUDIT + limb-window generation are S3) ───────────────────────────────────
# A_QUIET: the quiet-sky maximum |d²λ/dt²| per graha, degrees/day², × the 1.25 margin of plan H4. Near a solar-limb conjunction the
# Swiss longitude is NOT smooth (A up to 0.95 °/d² for Jupiter): inside a limb window the provider returns None and the solver
# falls back to the first-order bound (rigorous, H4-free).
A_QUIET_DEG_PER_DAY2 = {"sun": 6.6e-4, "mercury": 0.199, "venus": 0.0424, "mars": 0.0150, "jupiter": 0.0035, "saturn": 0.0019,
                        "rahu": 2e-5, "ketu": 2e-5, "moon": 0.515}
H4_MARGIN = 1.25


def accel_bound_provider(graha: str, limb_windows: Optional[Sequence[tuple]]) -> Callable[[float, float], Optional[float]]:
    """An `accel_bound` for `graha`: A_QUIET × margin (deg/s²) on an interval clear of every limb window, None on one that
    overlaps a limb window — and ALWAYS None when no limb-window list is supplied (without it the quiet bound is unproven)."""
    a_quiet = A_QUIET_DEG_PER_DAY2[graha] * H4_MARGIN / (86400.0 ** 2)
    if limb_windows is None:
        return lambda l, r: None
    wins = tuple(sorted(limb_windows))

    def provider(l: float, r: float) -> Optional[float]:
        for a, b in wins:
            if a < r and b > l:
                return None
        return a_quiet
    return provider


# ── evaluation context (the ONLY place an ephemeris call is counted) ──────────────────────────────────────────────────────────

class _Ctx:
    def __init__(self, max_evals: int, grain: Optional[Budget]):
        self.max_evals, self.grain, self.evals = int(max_evals), grain, 0
        self._kin: dict = {}

    def kin(self, tent: Tent, t: float):
        """(offset, velocity) of `tent` at `t`; ONE counted call per distinct (tent, t)."""
        key = (id(tent), t)
        got = self._kin.get(key)
        if got is None:
            if self.evals >= self.max_evals or (self.grain is not None and self.grain.remaining <= 0):
                raise BudgetExhausted()
            self.evals += 1
            if self.grain is not None:
                self.grain.remaining -= 1
                self.grain.spent += 1
            off = float(tent.offset(t))
            vel = None if tent.velocity is None else float(tent.velocity(t))
            if not math.isfinite(off) or (vel is not None and not math.isfinite(vel)):
                raise SolverRefusal("the ephemeris seam returned a non-finite value")
            got = self._kin[key] = (off, vel)
        return got


def _min_width(l: float, r: float) -> float:
    """The narrowest interval worth splitting: a few float ulps of the instants involved (a concave kink — the P4 minimum's crossing —
    converges only first-order, so the floor must be near the float resolution, not a fixed 1e-6)."""
    return max(1e-9, 8.0 * math.ulp(max(abs(l), abs(r), 1.0)))


def _sgn(x: float) -> int:
    return (x > 0) - (x < 0)


def _u(off: float, orb: float) -> float:
    return max(0.0, 1.0 - abs(off) / orb)


def _unit(v, what: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not (0.0 <= float(v) <= 1.0):
        raise SolverRefusal(f"{what}: factor value {v!r} outside [0,1]")
    return float(v)


def _combine(objective: str, group_values) -> float:
    vals = list(group_values)
    if objective == OBJECTIVE_SUM:
        return sum(vals)
    return min(vals)


# ── direct evaluation of the objective from the model (the brute-force / differential reference) ────────────────────────────────

def objective_value(problem: Problem, t: float) -> Optional[float]:
    """F(t) straight from the members — no pieces, no bounds. None = undeterminable at t (a step is unknown, or — for the min
    objective — an agent group has no live member). Used by tests as the dense-scan reference and by the differential suite."""
    groups: dict = {}
    for m in problem.members:
        if not any(s0 <= t < s1 for s0, s1 in m.supports):
            continue
        c = 1.0
        for st in m.steps:
            v = st.value_at(t)
            if v is None:
                return None
            c *= _unit(v, f"{m.key} step")
        if m.tent is not None:
            c *= _u(m.tent.offset(t), m.tent.orb)
        groups[m.group] = max(groups.get(m.group, 0.0), c)
    if problem.objective == OBJECTIVE_SUM:
        return sum(groups.values())
    return None if len(groups) < 2 else min(groups.values())


# ── pieces ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

UP, DOWN, FLAT = 1, -1, 0


class _Branch:
    __slots__ = ("group", "c", "tent", "dir")

    def __init__(self, group: str, c: float, tent: Optional[Tent], direction: int):
        self.group, self.c, self.tent, self.dir = group, c, tent, direction


class _Piece:
    """An elementary piece `[a, b)`: the live set is constant, every step is constant, every tent is constant-zero, rising or
    falling. Its domain is `[a, b_eff]`, `b_eff = b − QUANT` (the µs-quantised half-open end)."""

    def __init__(self, a: float, b: float, branches: list, objective: str, ctx: _Ctx):
        self.a, self.b, self.objective, self.ctx = a, b, objective, ctx
        self.b_eff = b - QUANT if b - a > 2 * QUANT else a
        self.groups: dict = {}
        for br in branches:
            self.groups.setdefault(br.group, []).append(br)
        ups = any(br.dir == UP for br in branches)
        downs = any(br.dir == DOWN for br in branches)
        if self.b_eff == self.a:
            self.kind = "point"
        elif ups and downs:
            self.kind = "mixed"
        elif ups:
            self.kind = "up"
        elif downs:
            self.kind = "down"
        else:
            self.kind = "const"

    # value / derivative ---------------------------------------------------------------------------------------------------
    def f(self, br: _Branch, t: float) -> float:
        if br.tent is None:
            return br.c
        return br.c * _u(self.ctx.kin(br.tent, t)[0], br.tent.orb)

    def df(self, br: _Branch, t: float) -> float:
        if br.tent is None or br.dir == FLAT:
            return 0.0
        off, vel = self.ctx.kin(br.tent, t)
        s = _sgn(off) or -br.dir * _sgn(vel)
        return br.c * (-s * vel / br.tent.orb)

    def value(self, t: float) -> float:
        return _combine(self.objective, (max(self.f(br, t) for br in brs) for brs in self.groups.values()))

    def dvalue(self, t: float) -> float:
        """dF/dt of the ACTIVE branches (right-hand choice on a tie: the larger derivative — a max kink is convex, so only a
        concave (min) kink or a smooth stationary point can turn + into −)."""
        acts = []
        for brs in self.groups.values():
            best = max(brs, key=lambda br: (self.f(br, t), self.df(br, t)))
            acts.append((self.f(best, t), self.df(best, t)))
        if self.objective == OBJECTIVE_SUM:
            return sum(d for _v, d in acts)
        return min(acts, key=lambda vd: (vd[0], vd[1]))[1]

    # bounds ---------------------------------------------------------------------------------------------------------------
    def bound(self, l: float, r: float) -> float:
        """A rigorous upper bound of F on [l, r] ⊂ [a, b_eff]: U1 (monotone-endpoint theorem) and, when every tent has an
        H4 bound, U2 (second-order convex Taylor models about the midpoint); the smaller of the two."""
        u1 = _combine(self.objective, (max(max(self.f(br, l), self.f(br, r)) for br in brs) for brs in self.groups.values()))
        m, h = 0.5 * (l + r), 0.5 * (r - l)
        ql: dict = {}
        qr: dict = {}
        for g, brs in self.groups.items():
            bl = br_ = 0.0
            for br in brs:
                if br.tent is None:
                    vl = vr = br.c
                else:
                    big_a = None if br.tent.accel_bound is None else br.tent.accel_bound(l, r)
                    if big_a is None:
                        return u1
                    off, vel = self.ctx.kin(br.tent, m)
                    s = _sgn(off) or -br.dir * _sgn(vel)
                    gm = br.c * (1.0 - abs(off) / br.tent.orb)
                    gp = br.c * (-s * vel / br.tent.orb)
                    kk = br.c * big_a / br.tent.orb
                    vl = min(br.c, max(0.0, gm - gp * h + 0.5 * kk * h * h))
                    vr = min(br.c, max(0.0, gm + gp * h + 0.5 * kk * h * h))
                bl, br_ = max(bl, vl), max(br_, vr)
            ql[g], qr[g] = bl, br_
        if self.objective == OBJECTIVE_SUM:
            u2 = max(sum(ql.values()), sum(qr.values()))
        else:
            u2 = min(max(ql[g], qr[g]) for g in ql)
        return min(u1, u2)

    def lower(self, l: float, r: float) -> float:
        """A rigorous LOWER bound of F on [l, r]: every branch is monotone there, so it is at least the smaller of its end values,
        and sum / max / min are monotone operators. `bound − lower ≤ EPS_PLATEAU` ⇒ F is one flat plateau on the interval."""
        return _combine(self.objective, (max(min(self.f(br, l), self.f(br, r)) for br in brs) for brs in self.groups.values()))

    def is_leaf(self, l: float, r: float) -> bool:
        """F is affine to LEAF_CURV on [l, r] (every term's second-order remainder, or — with no H4 bound — its first-order
        variation, is below it) or the interval cannot be split further."""
        w = r - l
        if w <= _min_width(l, r):
            return True
        h = 0.5 * w
        m = l + h
        curv = 0.0
        for brs in self.groups.values():
            for br in brs:
                if br.tent is None or br.dir == FLAT:
                    continue
                big_a = None if br.tent.accel_bound is None else br.tent.accel_bound(l, r)
                if big_a is None:
                    _off, vel = self.ctx.kin(br.tent, m)
                    curv += br.c * abs(vel) / br.tent.orb * w          # first-order variation over the interval
                else:
                    curv += 0.5 * (br.c * big_a / br.tent.orb) * h * h
        return curv <= LEAF_CURV


# ── the solver ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _bisect_root(tent: Tent, level: float, x: float, y: float, ctx: _Ctx) -> Optional[float]:
    """The unique instant in [x, y] where the monotone offset equals `level`, to TIME_TOL — or None if it does not cross."""
    gx, gy = ctx.kin(tent, x)[0] - level, ctx.kin(tent, y)[0] - level
    if gx == 0.0 or gy == 0.0 or (gx > 0) == (gy > 0):
        return None                       # an endpoint root is already a cut; no sign change ⇒ no crossing
    lo, hi, glo = x, y, gx
    while hi - lo > TIME_TOL:
        mid = 0.5 * (lo + hi)
        if not lo < mid < hi:
            break
        gm = ctx.kin(tent, mid)[0] - level
        if gm == 0.0:
            return mid
        if (gm > 0) == (glo > 0):
            lo, glo = mid, gm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _check_arc(tent: Tent, x: float, y: float, ctx: _Ctx, who: str) -> None:
    """H1 on one stretch between listed stations: the velocity keeps one sign at spacing ≤ 5 d, and the audited station spacing
    exceeds that spacing (so a reversal pair cannot hide between samples). The station-adjacent instants are inset."""
    if tent.velocity is None:
        raise _Blank(REASON_MONOTONE, f"{who}: no velocity operand")
    if tent.min_station_spacing is None or not tent.min_station_spacing > H1_SPACING_S:
        raise _Blank(REASON_MONOTONE, f"{who}: audited station spacing absent or ≤ the sampling spacing")
    length = y - x
    if length <= 2 * TIME_TOL:
        return
    n = max(1, math.ceil(length / H1_SPACING_S))
    inset = min(60.0, length / 4.0)
    signs = {_sgn(ctx.kin(tent, x + inset + k * (length - 2 * inset) / n)[1]) for k in range(n + 1)}
    if signs not in ({1}, {-1}):
        raise _Blank(REASON_MONOTONE, f"{who}: the velocity changes sign (or vanishes) inside [{x}, {y}] with no listed station")


def _classify_tent(tent: Tent, c: float, group: str, a: float, b_eff: float, ctx: _Ctx, who: str) -> _Branch:
    """The branch a tent term is on one piece: constant zero, rising or falling — verified, never assumed."""
    mid = 0.5 * (a + b_eff)
    kins = [ctx.kin(tent, t) for t in (a, mid, b_eff)]
    u_a, u_m, u_b = (_u(off, tent.orb) for off, _v in kins)
    # a piece next to a bisected root cut starts/ends up to speed × TIME_TOL/orb away from the exact level: that much is tolerated
    tol = MONO_TOL + 2.0 * max(abs(kins[0][1] or 0.0), abs(kins[2][1] or 0.0)) * TIME_TOL / tent.orb
    if u_m <= 0.0:
        if max(u_a, u_b) > tol:
            raise _Blank(REASON_MONOTONE, f"{who}: the kernel is zero mid-piece but positive at an end")
        return _Branch(group, 0.0, None, FLAT)
    if u_a <= u_m + tol and u_m <= u_b + tol:
        return _Branch(group, c, tent, UP)
    if u_a >= u_m - tol and u_m >= u_b - tol:
        return _Branch(group, c, tent, DOWN)
    raise _Blank(REASON_MONOTONE, f"{who}: the kernel is not monotone inside [{a}, {b_eff}]")


def _build(problem: Problem, ctx: _Ctx):
    lo, hi = problem.lo, problem.hi
    if not lo < hi:
        raise SolverRefusal("empty window")
    if problem.objective not in (OBJECTIVE_SUM, OBJECTIVE_MINMAX):
        raise SolverRefusal(f"unknown objective {problem.objective!r}")
    members = []
    for m in problem.members:
        sup = tuple((max(s0, lo), min(s1, hi)) for s0, s1 in m.supports if max(s0, lo) < min(s1, hi))
        if sup:
            members.append((m, sup))
    cuts = {lo, hi}
    for m, sup in members:
        for a, b in sup:
            cuts.update((a, b))
            for st in m.steps:
                if st.constant:
                    continue
                # H2: an unlisted change could hide an island a piece would bridge
                if st.boundaries is None or not st.complete:
                    raise _Blank(REASON_BOUNDARIES, f"{m.key}: a state factor without a complete boundary list")
                cuts.update(c for c in st.boundaries(a, b) if a < c < b)
            if m.tent is not None:
                tent = m.tent
                if not (math.isfinite(tent.orb) and tent.orb > 0.0):
                    raise SolverRefusal(f"{m.key}: orb must be finite and positive")
                stops = [a] + sorted(s for s in tent.stations if a < s < b) + [b]
                cuts.update(stops)
                for x, y in zip(stops, stops[1:]):
                    _check_arc(tent, x, y, ctx, m.key)
                    for level in (tent.orb, 0.0, -tent.orb):          # entry, crest, exit: re-derived, never `exact_hint`
                        root = _bisect_root(tent, level, x, y, ctx)
                        if root is not None:
                            cuts.add(root)
    ordered = sorted(cuts)
    pieces = []
    for idx, (a, b) in enumerate(zip(ordered, ordered[1:])):
        live = [m for m, sup in members if any(s0 <= a < s1 for s0, s1 in sup)]
        b_eff = b - QUANT if b - a > 2 * QUANT else a
        probes = sorted({a, 0.5 * (a + b_eff), b_eff})
        branches = []
        for m in live:
            c = 1.0
            for st in m.steps:
                v0 = st.value_at(a)
                if v0 is None:
                    name = None if st.unknown_reason is None else st.unknown_reason(a)
                    raise _Blank(name or REASON_UNKNOWN, f"{m.key}: a step factor is undeterminable at {a}")
                c *= _unit(v0, f"{m.key} step")
                if not st.constant:
                    # the second detector for H2: the step must hold its value across the piece
                    if any(st.value_at(p) != v0 for p in probes[1:]):
                        raise _Blank(REASON_BOUNDARIES, f"{m.key}: a step factor changes inside [{a}, {b}] unlisted")
            if m.tent is None or c == 0.0:
                branches.append(_Branch(m.group, c if m.tent is None else 0.0, None, FLAT))
            else:
                branches.append(_classify_tent(m.tent, c, m.group, a, b_eff, ctx, m.key))
        if problem.objective == OBJECTIVE_MINMAX and len({br.group for br in branches}) < 2:
            pieces.append(None)                                  # outside the joint support: not part of the domain
        elif not branches:
            pieces.append(_Piece(a, b, [_Branch("_none", 0.0, None, FLAT)], OBJECTIVE_SUM, ctx))   # the objective is identically 0
        else:
            pieces.append(_Piece(a, b, branches, problem.objective, ctx))
    return ordered, pieces


@dataclass
class _Sample:
    t: float
    v: float
    tag: str                  # 'start' | 'end' | 'leaf' | 'gap'
    piece: Optional[_Piece]


def _prove_max(mixed: list, best: float, ctx: _Ctx) -> float:
    """Pass 1: best-first branch-and-bound over the mixed pieces. Returns an incumbent M̂ with every interval's bound ≤ M̂ + EPS_M."""
    heap: list = []
    seq = 0
    for p in mixed:
        u = p.bound(p.a, p.b_eff)
        if u > best + EPS_M:
            heapq.heappush(heap, (-u, seq, p, p.a, p.b_eff))
            seq += 1
    while heap:
        negu, _s, p, l, r = heapq.heappop(heap)
        if -negu <= best + EPS_M:
            break
        m = 0.5 * (l + r)
        if not l < m < r or r - l <= _min_width(l, r):
            raise _Blank(REASON_CERTIFICATE, "the bound did not converge before the float resolution")
        best = max(best, p.value(m))
        for x, y in ((l, m), (m, r)):
            u = p.bound(x, y)
            if u > best + EPS_M:
                heapq.heappush(heap, (-u, seq, p, x, y))
                seq += 1
    return best


def _explore(p: _Piece, thresh: float) -> list:
    """Pass 2 on one mixed piece: the leaves (time order) whose bound is NOT below `thresh` (pruning is strict: `U < thresh`)."""
    leaves, stack = [], [(p.a, p.b_eff)]
    while stack:
        l, r = stack.pop()
        u = p.bound(l, r)
        if u < thresh:
            continue
        if u - p.lower(l, r) <= EPS_PLATEAU or p.is_leaf(l, r):       # a flat plateau (e.g. the min objective pinned at 0) needs no refinement
            leaves.append((l, r))
            continue
        m = 0.5 * (l + r)
        if not l < m < r:
            raise _Blank(REASON_CERTIFICATE, "an alive interval cannot be split")
        stack.append((m, r))
        stack.append((l, m))
    return leaves


def _refine(p: _Piece, x: float, y: float, seed_v: float, seed_t: float):
    """The local maximum of F on [x, y] ⊂ the piece's domain: bisection on the exact derivative's sign (+ → −) to TIME_TOL when it
    brackets one, else golden-section on the value. Returns (value, t); never worse than the seed."""
    best_v, best_t = seed_v, seed_t
    if y - x > TIME_TOL:
        if p.dvalue(x) > 0.0 and p.dvalue(y) < 0.0:
            lo, hi = x, y
            while hi - lo > TIME_TOL:
                mid = 0.5 * (lo + hi)
                if not lo < mid < hi:
                    break
                if p.dvalue(mid) > 0.0:
                    lo = mid
                else:
                    hi = mid
            cand_t = 0.5 * (lo + hi)
        else:
            phi = (math.sqrt(5.0) - 1.0) / 2.0
            lo, hi = x, y
            c, d = hi - (hi - lo) * phi, lo + (hi - lo) * phi
            fc, fd = p.value(c), p.value(d)
            while hi - lo > TIME_TOL:
                if fc >= fd:
                    hi, d, fd = d, c, fc
                    c = hi - (hi - lo) * phi
                    fc = p.value(c)
                else:
                    lo, c, fc = c, d, fd
                    d = lo + (hi - lo) * phi
                    fd = p.value(d)
                if not lo < c < d < hi:
                    break
            cand_t = 0.5 * (lo + hi)
        cand_v = p.value(cand_t)
        if cand_v > best_v + EPS_PLATEAU:
            best_v, best_t = cand_v, cand_t
    return best_v, best_t


def _local_maxima(samples: list) -> list:
    """Plateau-aware local maxima of the ordered sample sequence: a group of consecutive samples equal to float noise, strictly
    higher than the group on each side (or the sequence end). Returns [(first_index, last_index)]."""
    groups: list = []
    for i, s in enumerate(samples):
        if groups and abs(s.v - samples[groups[-1][0]].v) <= EPS_PLATEAU:
            groups[-1][1] = i
        else:
            groups.append([i, i])
    out = []
    for gi, (i0, i1) in enumerate(groups):
        v = max(samples[k].v for k in range(i0, i1 + 1))
        left = gi == 0 or samples[groups[gi - 1][0]].v < v - EPS_PLATEAU
        right = gi == len(groups) - 1 or samples[groups[gi + 1][0]].v < v - EPS_PLATEAU
        if left and right:
            out.append((i0, i1))
    return out


def solve(problem: Problem, *, max_evals: int = MAX_EVALS_WINDOW, grain: Optional[Budget] = None) -> SolveResult:
    """Solve one window: a certified number, or a named blank. Never a best-found value."""
    ctx = _Ctx(max_evals, grain)
    try:
        return _solve(problem, ctx)
    except _Blank as exc:
        return SolveResult(BLANK, None, None, exc.reason, ctx.evals, exc.detail)
    except BudgetExhausted:
        return SolveResult(BLANK, None, None, REASON_BUDGET, ctx.evals, f"more than {ctx.max_evals} ephemeris calls needed")


def _solve(problem: Problem, ctx: _Ctx) -> SolveResult:
    ordered, pieces = _build(problem, ctx)
    live = [p for p in pieces if p is not None]
    # incumbent from the exact values of every piece's ends (and the mixed pieces' midpoints)
    best = -1.0
    for p in live:
        best = max(best, p.value(p.a), p.value(p.b_eff))
        if p.kind == "mixed":
            best = max(best, p.value(0.5 * (p.a + p.b_eff)))
    mixed = [p for p in live if p.kind == "mixed"]
    proven = _prove_max(mixed, best, ctx) if mixed else best
    thresh = proven - TIE

    samples: list = []
    for p in pieces:
        if p is None:
            samples.append(_Sample(math.nan, -1.0, "gap", None))
        elif p.kind == "mixed":
            leaves = _explore(p, thresh)
            pts = sorted({p.a, p.b_eff} | {x for lf in leaves for x in lf})
            for t in pts:
                samples.append(_Sample(t, p.value(t), "start" if t == p.a else ("end" if t == p.b_eff else "leaf"), p))
        else:
            samples.append(_Sample(p.a, p.value(p.a), "start", p))
            if p.b_eff != p.a:
                samples.append(_Sample(p.b_eff, p.value(p.b_eff), "end", p))

    cands = []                                    # (value, instant)
    for i0, i1 in _local_maxima(samples):
        grp = samples[i0:i1 + 1]
        v0 = max(s.v for s in grp)
        first = min((s for s in grp if s.v >= v0 - EPS_PLATEAU), key=lambda s: s.t)
        best_v, best_t = v0, first.t
        for p in {id(s.piece): s.piece for s in grp if s.piece is not None and s.piece.kind == "mixed"}.values():
            idxs = [k for k in range(i0, i1 + 1) if samples[k].piece is p]
            k0, k1 = idxs[0], idxs[-1]
            x = samples[k0 - 1].t if k0 > 0 and samples[k0 - 1].piece is p else p.a
            y = samples[k1 + 1].t if k1 + 1 < len(samples) and samples[k1 + 1].piece is p else p.b_eff
            rv, rt = _refine(p, x, y, best_v, best_t)
            if rv > best_v + EPS_PLATEAU:
                best_v, best_t = rv, rt
        if best_v >= 0.0:                         # (a 'gap' sample — outside the joint support of the min objective — is not a candidate)
            cands.append((best_v, best_t))
    if not cands:
        raise _Blank(REASON_UNDETERMINABLE, "no instant of the window has both agents live")
    top = max(v for v, _t in cands)
    t_star = min(t for v, t in cands if v >= top - TIE)
    at_star = max(v for v, t in cands if t == t_star)
    cert = {"upper_bound": top + (EPS_M if mixed else 0.0), "value_at_instant": at_star, "pieces": len(live),
            "mixed_pieces": len(mixed), "candidates": len(cands), "ties": sum(1 for v, _t in cands if v >= top - TIE),
            "h4_used": any(br.tent is not None and br.tent.accel_bound is not None
                           for p in mixed for brs in p.groups.values() for br in brs)}
    return SolveResult(SOLVED, top, t_star, None, ctx.evals, certificate=cert)


__all__ = [
    "OBJECTIVE_SUM", "OBJECTIVE_MINMAX", "SOLVED", "BLANK", "REASON_BUDGET", "REASON_MONOTONE", "REASON_CERTIFICATE",
    "REASON_BOUNDARIES", "REASON_UNKNOWN", "REASON_UNDETERMINABLE", "QUANT", "TIE", "MAX_EVALS_WINDOW", "SolverRefusal", "BudgetExhausted", "Tent",
    "Step", "Member", "Problem", "SolveResult", "Budget", "constant_step", "grain_budget_evals", "accel_bound_provider",
    "A_QUIET_DEG_PER_DAY2", "H4_MARGIN", "objective_value", "solve",
]
