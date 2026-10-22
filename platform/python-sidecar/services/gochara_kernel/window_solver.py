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
                        spacing ≤ 5 d and the audited minimum station spacing > that spacing, `monotone_arc_not_established`);
                        a stretch/piece ≤ NEAR_STATION_S touching a listed station is a cut, read monotone within the S0 noise
                        NEAR_STATION_NOISE_DEG (N-3b, SR-STATION-NEAR-END) — AMENDED by SR-NEAR-STATION-TIE: such a window numbers UNLESS the
                        station zone can host a tied maximum (see KNOWN LIMIT H6)
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

KNOWN LIMIT (H6, SR-NEAR-STATION-TIE): within NEAR_STATION_S of a listed station the real curve is a noise COMB (the Swiss longitude steps by
~1e-9°, S0 K-2): dozens of local maxima, 0.3–1.3 s apart, ALL within TIE of the zone's top. The zone is read monotone (above), so the builder sees ONE
candidate there, and which instant of the comb is "the earliest distinct maximum within TIE" is not decidable — to the second (Q12) or at all. So when
the zone's value can reach within TIE + the zone's noise bound of the window's maximum, the window is the named blank `tie_isolation_unresolved`
(INCONCLUSIVE class, R-6), never a number. A zone clearly below the maximum does not interfere: that window numbers as before. The independent
checker applies the same rule from its own code (K12).

METHOD (plan §2.3). (1) CUTS: window ends, support ends, step boundaries, listed stations, and — for every tent on every monotone
stretch — the three roots of its monotone offset (`d = orb`, crest, exit) by BISECTION on a monotone function; a stored `t_exact`
is never trusted (`Tent.exact_hint` is ignored by design). (2) Between cuts every tent is constant, or monotone and C²; hence
sup F ≤ U1 = Σ_roots max_ρ max(f_ρ(l), f_ρ(r)) — a THEOREM needing no speed constant — and, with H4, the second-order bound
U2 (convex Taylor upper models about the midpoint, maximised at the interval ends). (3) A piece whose tents all rise (or all
fall, or none) is MONOTONE: its sup is an endpoint, exact. (4) A MIXED piece (a rising and a falling term) is searched:
pass 1 best-first on U proves M; pass 2 (pruning `U < M̂ − TIE`, never `U ≤ best`) resolves every alive stretch to a leaf where F is
affine to LEAF_CURV, samples it, and finds each distinct local maximum. (5) All pieces' samples form ONE ordered sequence; its
plateau-aware local maxima are the candidates; the earliest within TIE of the top is t*. (6) Budget: `MAX_EVALS_WINDOW` PER WINDOW and nothing
shared across windows (R-6: a grain-level budget made a window's result depend on the windows solved before it) — exhaustion ⇒ blank
`solver_budget_exhausted`. (7) CERTIFICATE (R-7): the piece tree the answer rests on — the cuts, the pieces with their kind, every cell with
its claimed upper bound (monotone pieces, pass-1 pruned cells, pass-2 dead cells and the leaf brackets the maximum was located in), the
evaluation count and the limits assumed — is returned as `SolveResult.tree`; `stored_certificate` turns it into the JSON object the window's
`qualification` carries. A budget-exhausted blank carries the partial tree and its OPEN cells, so the independent verifier can check that the
exhaustion was real. The verifier CHECKS the cells with its own first-order enclosure (`window_cert_check`); it never trusts a claimed bound.

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
REASON_TIE_ISOLATION = "tie_isolation_unresolved"          # SR-NEAR-STATION-TIE: a station zone can host the earliest tie (the verifier's R-3 code, same string)

QUANT = 1e-6                 # the µs quantisation: a right-open end is evaluated at b − QUANT
TIE = 1e-9                   # frozen peak-tie tolerance between DISTINCT local maxima (window_sweep._TIE)
EPS_PLATEAU = 1e-12          # values equal to float noise are ONE plateau (window_sweep._EPS)
EPS_M = 1e-11                # branch-and-bound stops when no interval can beat the incumbent by more than this
TIME_TOL = 5e-8              # root / extremum location (≈ float resolution of a 10^8 s window offset)
LEAF_CURV = 4e-12            # an interval is a LEAF when each term is affine to this much
MONO_TOL = 1e-11             # tent-value comparisons for the monotone-piece check
# SR-STATION-NEAR-END (N-3b). A stored (spline) station and the Swiss station of the same contact differ by up to 16.7 s (S0 K-2), and
# inside that stretch the Swiss speed is ~1e-8 °/day with a noisy sign and the longitude is non-monotone by up to 3.9e-9° (S0 K-2).
# So a stretch or piece NO LONGER than NEAR_STATION_S that touches a LISTED station is a cut for H1 and is read monotone within the
# S0 noise bound (kernel units: NEAR_STATION_NOISE_DEG / orb). The value (120 s ≈ 7 × the 16.7 s measured offset) is EQUAL to the independent checker's NEAR_END_S
# (window_solver_check.py:42-44) by owner ruling, but it is this module's OWN constant and code (K12: nothing is imported from it;
# `test_od1_n3b_station_cut` pins the two equal by reading the checker's source text).
NEAR_STATION_S = 120.0
NEAR_STATION_NOISE_DEG = 3.9e-9
H1_SPACING_S = 5.0 * 86400.0
MAX_EVALS_WINDOW = 500_000   # ephemeris-call budget of ONE window (I: sized from S0 — 75.6 evals/record, 34,742 records, 6,629 windows)
CERT_SCHEMA = "window_solver_certificate/1"   # the object the window's `qualification` carries under `solver_certificate` (R-7)
MAX_OPEN_CELLS = 200         # an exhausted window's certificate lists the open cells of highest claimed bound, at most this many (`open_total` counts all)
MAX_CERT_CELLS = 400         # a certificate is coarsened (adjacent closed cells merged, the claimed bound the max) to at most this many cells


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
    tree: Optional[dict] = None                  # the piece tree (solved, or budget-exhausted with its open cells): `stored_certificate` input

    @property
    def peak_value(self) -> Optional[float]:
        return None if self.certificate is None else self.certificate["value_at_instant"]


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

class _Trace:
    """The piece tree being built (R-7). `cells` are the CLOSED cells — `[kind, l, r, u]`, `u` the claimed upper bound of F on [l, r] —
    of kind `piece` (a monotone/constant elementary piece: its supremum is an end value, exact), `pruned` (a pass-1 sub-interval whose bound
    is within EPS_M of the incumbent), `dead` (a pass-2 interval whose bound is below the threshold M̂ − TIE) and `leaf` (a pass-2 interval
    where F is affine to LEAF_CURV: the bracket a local maximum is located in). `open` are the cells still unresolved when the budget ran
    out. `phase` is where the solver was."""

    def __init__(self):
        self.phase = "build"
        self.cuts: list = []
        self.pieces: list = []          # [a, b_eff, kind]
        self.cells: list = []
        self.heap = None                # pass 1: the live best-first heap (read at exhaustion)
        self.stack = None               # pass 2: the live stack of the piece being explored
        self.current = None             # the cell being split when the budget ran out
        self.pending_pieces: list = []  # mixed pieces not yet started by the pass that was running


class _Ctx:
    def __init__(self, max_evals: int):
        self.max_evals, self.evals = int(max_evals), 0
        self._kin: dict = {}
        self.trace = _Trace()
        self.zones: list = []           # SR-NEAR-STATION-TIE: (lo, hi, noise_F) of each listed station's zone, per support of each tent member

    def kin(self, tent: Tent, t: float):
        """(offset, velocity) of `tent` at `t`; ONE counted call per distinct (tent, t)."""
        key = (id(tent), t)
        got = self._kin.get(key)
        if got is None:
            if self.evals >= self.max_evals:
                raise BudgetExhausted()
            self.evals += 1
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


def _touches_station(tent: Tent, x: float, y: float) -> bool:
    """The interval [x, y] is NO LONGER than NEAR_STATION_S and one of its ends is a LISTED station of the tent (N-3b)."""
    return y - x <= NEAR_STATION_S and (x in tent.stations or y in tent.stations)


def _check_arc(tent: Tent, x: float, y: float, ctx: _Ctx, who: str) -> None:
    """H1 on one stretch between listed stations: the velocity keeps one sign at spacing ≤ 5 d, and the audited station spacing
    exceeds that spacing (so a reversal pair cannot hide between samples). The station-adjacent instants are inset. A stretch of at
    most NEAR_STATION_S next to a listed station is the Swiss/spline offset of that station (S0 K-2): a cut, its velocity sign is
    noise, so it is not sampled — the kernel on it is read monotone within NEAR_STATION_NOISE_DEG by `_classify_tent`."""
    if tent.velocity is None:
        raise _Blank(REASON_MONOTONE, f"{who}: no velocity operand")
    if tent.min_station_spacing is None or not tent.min_station_spacing > H1_SPACING_S:
        raise _Blank(REASON_MONOTONE, f"{who}: audited station spacing absent or ≤ the sampling spacing")
    length = y - x
    if length <= 2 * TIME_TOL or _touches_station(tent, x, y):
        return
    n = max(1, math.ceil(length / H1_SPACING_S))
    inset = min(60.0, length / 4.0)
    signs = {_sgn(ctx.kin(tent, x + inset + k * (length - 2 * inset) / n)[1]) for k in range(n + 1)}
    if signs not in ({1}, {-1}):
        raise _Blank(REASON_MONOTONE, f"{who}: the velocity changes sign (or vanishes) inside [{x}, {y}] with no listed station")


def _classify_tent(tent: Tent, c: float, group: str, a: float, b_eff: float, ctx: _Ctx, who: str, near_station: bool = False) -> _Branch:
    """The branch a tent term is on one piece: constant zero, rising or falling — verified, never assumed. `near_station`: the piece is
    no longer than NEAR_STATION_S and touches a listed station — the kernel is then read monotone within the S0 near-station noise
    (NEAR_STATION_NOISE_DEG / orb on top of the usual tolerance)."""
    mid = 0.5 * (a + b_eff)
    kins = [ctx.kin(tent, t) for t in (a, mid, b_eff)]
    u_a, u_m, u_b = (_u(off, tent.orb) for off, _v in kins)
    # a piece next to a bisected root cut starts/ends up to speed × TIME_TOL/orb away from the exact level: that much is tolerated
    tol = MONO_TOL + 2.0 * max(abs(kins[0][1] or 0.0), abs(kins[2][1] or 0.0)) * TIME_TOL / tent.orb
    if near_station:
        tol += NEAR_STATION_NOISE_DEG / tent.orb
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
                ctx.zones.extend((max(a, st - NEAR_STATION_S), min(b, st + NEAR_STATION_S), NEAR_STATION_NOISE_DEG / tent.orb)
                                 for st in tent.stations if st - NEAR_STATION_S <= b and st + NEAR_STATION_S >= a)
                for x, y in zip(stops, stops[1:]):
                    _check_arc(tent, x, y, ctx, m.key)
                    for level in (tent.orb, 0.0, -tent.orb):          # entry, crest, exit: re-derived, never `exact_hint`
                        root = _bisect_root(tent, level, x, y, ctx)
                        if root is not None:
                            cuts.add(root)
    ordered = sorted(cuts)
    ctx.trace.cuts = list(ordered)
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
                branches.append(_classify_tent(m.tent, c, m.group, a, b_eff, ctx, m.key, near_station=_touches_station(m.tent, a, b)))
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
    tr = ctx.trace
    tr.heap = heap
    seq = 0
    for k, p in enumerate(mixed):
        tr.pending_pieces = [(q.a, q.b_eff) for q in mixed[k:]]
        u = p.bound(p.a, p.b_eff)
        if u > best + EPS_M:
            heapq.heappush(heap, (-u, seq, p, p.a, p.b_eff))
            seq += 1
        else:
            tr.cells.append(["pruned", p.a, p.b_eff, u])
    tr.pending_pieces = []
    while heap:
        negu, _s, p, l, r = heapq.heappop(heap)
        if -negu <= best + EPS_M:
            tr.cells.append(["pruned", l, r, -negu])
            for _n, _q, p2, l2, r2 in heap:
                tr.cells.append(["pruned", l2, r2, -_n])
            heap.clear()
            break
        tr.current = (l, r)
        m = 0.5 * (l + r)
        if not l < m < r or r - l <= _min_width(l, r):
            raise _Blank(REASON_CERTIFICATE, "the bound did not converge before the float resolution")
        best = max(best, p.value(m))
        for x, y in ((l, m), (m, r)):
            u = p.bound(x, y)
            if u > best + EPS_M:
                heapq.heappush(heap, (-u, seq, p, x, y))
                seq += 1
            else:
                tr.cells.append(["pruned", x, y, u])
        tr.current = None
    return best


def _explore(p: _Piece, thresh: float, ctx: _Ctx) -> list:
    """Pass 2 on one mixed piece: the leaves (time order) whose bound is NOT below `thresh` (pruning is strict: `U < thresh`). Every interval
    it closes — dead (`U < thresh`) or a leaf — is recorded in the trace: together they tile the piece."""
    tr = ctx.trace
    leaves, stack = [], [(p.a, p.b_eff)]
    tr.stack = stack
    while stack:
        l, r = stack.pop()
        tr.current = (l, r)
        u = p.bound(l, r)
        if u < thresh:
            tr.cells.append(["dead", l, r, u])
            tr.current = None
            continue
        if u - p.lower(l, r) <= EPS_PLATEAU or p.is_leaf(l, r):       # a flat plateau (e.g. the min objective pinned at 0) needs no refinement
            leaves.append((l, r))
            tr.cells.append(["leaf", l, r, u])
            tr.current = None
            continue
        m = 0.5 * (l + r)
        if not l < m < r:
            raise _Blank(REASON_CERTIFICATE, "an alive interval cannot be split")
        stack.append((m, r))
        stack.append((l, m))
        tr.current = None
    tr.stack = None
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


def _zone_clusters(zones: list, objective: str) -> list:
    """The listed stations' zones merged where they overlap: [(lo, hi, noise_F)], noise_F the kernel-unit noise bound of F over the merged zone —
    the SUM of the member bounds for the sum objective (their noises can add), the largest for the min objective (a min moves by at most its larger leg)."""
    out: list = []
    for lo, hi, noise in sorted(zones):
        if out and lo <= out[-1][1]:
            prev = out[-1]
            out[-1] = (prev[0], max(prev[1], hi), prev[2] + noise if objective == OBJECTIVE_SUM else max(prev[2], noise))
        else:
            out.append((lo, hi, noise))
    return out


def _station_zone_tie(problem: Problem, ctx: _Ctx, pieces: list, samples: list, top: float, ties: tuple) -> Optional[str]:
    """SR-NEAR-STATION-TIE (H6). A description when some listed station's zone (±NEAR_STATION_S, within the support) can host a maximum tied with the
    window's: the zone's value (the largest F read there, the zone being read monotone) is within TIE + the zone's noise bound of `top`, AND every tied
    maximum (`ties`, the instants of the candidates within TIE of `top`) lies inside that zone cluster — the ruling's "tie set lies inside the zone". A tie set
    that reaches outside it (a plateau over the window) is not a noise comb: it numbers. None otherwise."""
    for lo, hi, noise in _zone_clusters(ctx.zones, problem.objective):
        zone_top = -1.0
        for p in pieces:
            if p is None:
                continue
            x, y = max(p.a, lo), min(p.b_eff, hi)
            if x > y:
                continue
            pts = {x, y} | ({0.5 * (x + y)} if p.kind == "mixed" else set())
            zone_top = max(zone_top, max(p.value(t) for t in pts))
        zone_top = max([zone_top] + [s.v for s in samples if s.piece is not None and lo <= s.t <= hi])
        if zone_top >= top - TIE - noise and all(lo <= t <= hi for t in ties):
            return (f"a station zone [{lo:.3f}, {hi:.3f}] s reaches {zone_top!r}, within TIE + {noise:.3g} of the maximum {top!r}: its noise comb of "
                    "tied maxima is not isolated (SR-NEAR-STATION-TIE)")
    return None


def solve(problem: Problem, *, max_evals: int = MAX_EVALS_WINDOW) -> SolveResult:
    """Solve one window: a certified number, or a named blank. Never a best-found value. The budget is this window's alone."""
    ctx = _Ctx(max_evals)
    try:
        return _solve(problem, ctx)
    except _Blank as exc:
        return SolveResult(BLANK, None, None, exc.reason, ctx.evals, exc.detail)
    except BudgetExhausted:
        return SolveResult(BLANK, None, None, REASON_BUDGET, ctx.evals, f"more than {ctx.max_evals} ephemeris calls needed",
                           tree=_exhausted_tree(problem, ctx))


def _tree(ctx: _Ctx, *, outcome: str, value=None, instant=None, upper=None, reason=None, open_cells=(), h4_used=False) -> dict:
    tr = ctx.trace
    cells = [c for c in tr.cells if outcome != "solved" or c[0] != "pruned"]      # a solved tree is tiled by pass 2; pass-1 cells are only a trace
    return {"outcome": outcome, "reason": reason, "phase": "done" if outcome == "solved" else tr.phase, "value": value, "instant": instant,
            "upper_bound": upper, "evals": ctx.evals, "max_evals": ctx.max_evals, "cuts": list(tr.cuts), "pieces": [list(x) for x in tr.pieces],
            "cells": [list(c) for c in cells], "open": [[l, r] for l, r in open_cells], "h4_used": bool(h4_used)}


def _exhausted_tree(problem: Problem, ctx: _Ctx) -> dict:
    """The partial tree when the budget ran out: what is closed, and every cell still OPEN. In the build phase nothing is known, so the
    whole window is open; later, the open cells are the live heap / stack / the cell being split / the pieces not yet started; in the
    refinement phase the leaves are all open (the bound is proven, the instant is not located)."""
    tr = ctx.trace
    if tr.phase == "build":
        return _tree(ctx, outcome="blank", reason=REASON_BUDGET, open_cells=[(problem.lo, problem.hi)])
    opened: list = []
    total_heap = len(tr.heap) if tr.heap else 0
    if tr.heap:
        opened += [(l, r) for _n, _q, _p, l, r in heapq.nsmallest(MAX_OPEN_CELLS, tr.heap, key=lambda e: (e[0], e[1]))]    # highest claimed bound first
    n_heap_listed = len(opened)
    if tr.stack:
        opened += list(tr.stack)
    if tr.current is not None:
        opened.append(tr.current)
    opened += list(tr.pending_pieces)
    cells = tr.cells
    if tr.phase == "refine":
        opened += [(c[1], c[2]) for c in cells if c[0] == "leaf"]
    for a, b, kind in tr.pieces:
        if kind == "gap":
            continue
        if not any(c[1] < b and c[2] > a or (c[1] == a and c[2] == b) for c in cells) and not any(l < b and r > a or (l == a and r == b) for l, r in opened):
            opened.append((a, b))
    tree = _tree(ctx, outcome="blank", reason=REASON_BUDGET, open_cells=sorted(set(opened)))
    tree["open_total"] = total_heap + len(set(opened[n_heap_listed:]))
    return tree


def _coarsen(cells: list, cap: int) -> tuple:
    """At most `cap` cells: adjacent closed cells of one kind are merged (the claimed bound the larger — a bound of the union), `leaf` cells
    only when that is not enough; if it still is not, the narrowest closed `pruned`/`dead` cells are dropped (the verifier searches an
    uncovered stretch itself) and the result is flagged truncated. `piece` cells are never dropped."""
    def merge(cs: list, kinds: tuple) -> list:
        out: list = []
        for c in sorted(cs, key=lambda c: (c[1], c[2])):
            if out and out[-1][0] == c[0] and c[0] in kinds and c[1] - out[-1][2] <= 2.0 * QUANT + 1e-9:
                out[-1] = [c[0], out[-1][1], max(c[2], out[-1][2]), max(c[3], out[-1][3])]
            else:
                out.append(list(c))
        return out
    out = merge(cells, ("dead", "pruned", "piece"))
    if len(out) > cap:
        out = merge(out, ("dead", "pruned", "piece", "leaf"))
    if len(out) <= cap:
        return out, False
    keep = [c for c in out if c[0] in ("leaf", "piece")]
    closed = sorted((c for c in out if c[0] in ("dead", "pruned")), key=lambda c: -(c[2] - c[1]))
    return sorted(keep + closed[:max(0, cap - len(keep))], key=lambda c: (c[1], c[2])), True


def stored_certificate(result: SolveResult, *, objective: str, t0_iso: str, max_evals: Optional[int] = None) -> Optional[dict]:
    """The JSON object a window's `qualification` carries under `solver_certificate` (R-7), or None when the result has no tree (a blank
    other than budget exhaustion). Times are SECONDS from `t0_iso` (the window start the caller used as its origin). It is split in two on
    purpose: `geometry` (cuts and piece kinds — they depend on the tents and step boundaries only, so a re-evaluation under different
    doctrine VALUES can reuse them, and the cells' time partition, as a search seed) and the value claims (`cells`' bounds, `value`,
    `instant`), which a re-evaluation must re-check. `geometry_digest` is the sha256 of the canonical geometry."""
    tree = result.tree
    if tree is None:
        return None
    import hashlib
    import json
    cells, truncated = _coarsen(tree["cells"], MAX_CERT_CELLS)
    geometry = {"cuts": tree["cuts"], "pieces": tree["pieces"]}
    blob = json.dumps(geometry, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        "schema": CERT_SCHEMA, "objective": objective, "t0": t0_iso, "outcome": tree["outcome"], "reason": tree["reason"], "phase": tree["phase"],
        "value": tree["value"], "instant": tree["instant"], "upper_bound": tree["upper_bound"],
        "evals": tree["evals"], "max_evals": tree["max_evals"] if max_evals is None else int(max_evals), "budget_scope": "window",
        "limits": {"QUANT": QUANT, "TIE": TIE, "EPS_M": EPS_M, "TIME_TOL": TIME_TOL, "LEAF_CURV": LEAF_CURV, "H1_SPACING_S": H1_SPACING_S,
                   "NEAR_STATION_S": NEAR_STATION_S, "NEAR_STATION_NOISE_DEG": NEAR_STATION_NOISE_DEG, "h4_used": tree["h4_used"]},
        "geometry": geometry, "geometry_digest": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "cells": cells, "open": tree["open"][:MAX_OPEN_CELLS], "open_total": tree.get("open_total", len(tree["open"])), "truncated": truncated}


def _solve(problem: Problem, ctx: _Ctx) -> SolveResult:
    tr = ctx.trace
    ordered, pieces = _build(problem, ctx)
    tr.pieces = [[ordered[i], ordered[i + 1] - QUANT if ordered[i + 1] - ordered[i] > 2 * QUANT else ordered[i], "gap"]
                 if p is None else [p.a, p.b_eff, p.kind] for i, p in enumerate(pieces)]
    tr.phase = "prove"
    live = [p for p in pieces if p is not None]
    # incumbent from the exact values of every piece's ends (and the mixed pieces' midpoints)
    best = -1.0
    for p in live:
        v0, v1 = p.value(p.a), p.value(p.b_eff)
        best = max(best, v0, v1)
        if p.kind == "mixed":
            best = max(best, p.value(0.5 * (p.a + p.b_eff)))
        else:
            tr.cells.append(["piece", p.a, p.b_eff, max(v0, v1)])      # monotone / constant: the supremum IS an end value
    mixed = [p for p in live if p.kind == "mixed"]
    proven = _prove_max(mixed, best, ctx) if mixed else best
    thresh = proven - TIE

    tr.phase = "explore"
    samples: list = []
    for p in pieces:
        if p is None:
            samples.append(_Sample(math.nan, -1.0, "gap", None))
        elif p.kind == "mixed":
            tr.pending_pieces = [(q.a, q.b_eff) for q in mixed[mixed.index(p) + 1:]]      # not yet started if the budget runs out inside this one
            leaves = _explore(p, thresh, ctx)
            pts = sorted({p.a, p.b_eff} | {x for lf in leaves for x in lf})
            for t in pts:
                samples.append(_Sample(t, p.value(t), "start" if t == p.a else ("end" if t == p.b_eff else "leaf"), p))
        else:
            samples.append(_Sample(p.a, p.value(p.a), "start", p))
            if p.b_eff != p.a:
                samples.append(_Sample(p.b_eff, p.value(p.b_eff), "end", p))

    tr.phase, tr.pending_pieces = "refine", []
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
    zone_tie = _station_zone_tie(problem, ctx, pieces, samples, top, tuple(t for v, t in cands if v >= top - TIE))
    if zone_tie is not None:
        raise _Blank(REASON_TIE_ISOLATION, zone_tie)
    at_star = max(v for v, t in cands if t == t_star)
    h4_used = any(br.tent is not None and br.tent.accel_bound is not None for p in mixed for brs in p.groups.values() for br in brs)
    cert = {"upper_bound": top + (EPS_M if mixed else 0.0), "value_at_instant": at_star, "pieces": len(live),
            "mixed_pieces": len(mixed), "candidates": len(cands), "ties": sum(1 for v, _t in cands if v >= top - TIE),
            "h4_used": h4_used}
    tree = _tree(ctx, outcome="solved", value=top, instant=t_star, upper=cert["upper_bound"], h4_used=h4_used)
    return SolveResult(SOLVED, top, t_star, None, ctx.evals, certificate=cert, tree=tree)


__all__ = [
    "OBJECTIVE_SUM", "OBJECTIVE_MINMAX", "SOLVED", "BLANK", "REASON_BUDGET", "REASON_MONOTONE", "REASON_CERTIFICATE",
    "REASON_BOUNDARIES", "REASON_UNKNOWN", "REASON_UNDETERMINABLE", "REASON_TIE_ISOLATION", "QUANT", "TIE", "MAX_EVALS_WINDOW", "SolverRefusal", "BudgetExhausted", "Tent",
    "Step", "Member", "Problem", "SolveResult", "constant_step", "accel_bound_provider", "CERT_SCHEMA", "MAX_CERT_CELLS", "MAX_OPEN_CELLS",
    "A_QUIET_DEG_PER_DAY2", "H4_MARGIN", "objective_value", "solve", "stored_certificate",
]
