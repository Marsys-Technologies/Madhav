"""Independent prover of the numbers a window stores (SR-OD1 plan S2, §2.1-2.4 only).

WRITTEN FROM THE WRITTEN SPEC ALONE. This module imports nothing from `window_sweep` or `window_solver` (nor any other
kernel module): it shares with the builder only the pinned ephemeris (`position_at`, handed in), the frozen objective
definitions (restated below, compared by tests, never imported) and — lazily, at the one place it needs them — the L2
valence rule authority `services.gochara_rules.valence`. Everything else (the kernel arithmetic, the piece structure, the
bound, the extremum enumeration) is derived here from the objective statement, so a defect in the builder is not repeated
by construction.

WHAT IT PROVES for one numbered window (a stored peak instant `t*` and objective value `M`):

  1. VALUE        F(t*) = M within 1e-6 or the float4 rounding interval at M's magnitude, whichever is wider (the stored REAL is a
                  float4: its error is half a float4 spacing, which grows with the value, a fixed 1e-7 does not model it; R-1);
  2. UPPER BOUND  sup F <= M + the float4 interval (half a float4 spacing at M, plus 1e-10) — the stored REAL is compared with the
                  UNROUNDED maximum inside its own rounding interval (R-1 a) — by a FIRST-ORDER monotone enclosure: between cuts every term is constant or monotone,
                  so a piece [l, r) satisfies  sup F <= U(l, r) = sum over roots of max over records of max(f(l), f(r))
                  (tightened, per body, to max(H(l), H(r)) of the body's convex sum H; for the max-min objective: min over
                  the two agents). No speed constant, no acceleration bound (no H4);
                  a piece whose bound is above the threshold is bisected until the bound falls below it, a witness above
                  it is found, or the width floor is reached (then the window is UNVERIFIED, never passed);
  3. EARLIEST TIE the stored `t*` is the earliest DISTINCT LOCAL EXTREMUM of F within the frozen tie tolerance (1e-9) of the
                  UNROUNDED maximum. The tie rule is between distinct extrema, never on the shoulder of one smooth hump. The
                  +-2e-10 grey band around that threshold is ONLY an ambiguity detector (R-1 b): when the earliest qualifying
                  extremum differs across the band the window is UNVERIFIED `tie_ambiguous` (INCONCLUSIVE), never VERIFIED —
                  a window is never accepted because its stored instant lies between two candidates. ISOLATION IS DETECTED, NOT
                  PROVED (SR-PLAN-REVIEW-RECONCILED R-3): when two or more extrema within the tie tolerance of the maximum lie within
                  ISOLATION_S of each other, neither side can say which of them is the earliest distinct one (the enumeration, like
                  the builder's, resolves extrema only down to its own sampling scale); the window is UNVERIFIED
                  `tie_isolation_unresolved` (INCONCLUSIVE, a named blank at the seal, never a pass and never a refutation);
  4. INSTANT      the stored `t*` lies within PEAK_INSTANT_TOLERANCE (owner decision SOLVER-TOLERANCES, Q12 a: the strongest
                  moment exact to the second) of an ACTUAL qualifying extremum (one whose unrounded value reaches the tie
                  threshold), never of a point between extrema;
  5. H1, H2       H1: every tent-bearing support lies in one arc on which the body's longitude is monotone (velocity-sign
                  sampling at <= 5 d spacing + the audited minimum station spacing; a station within seconds of a support
                  end is a Swiss station the stored arc index (a spline of daily knots) does not coincide with: it is an
                  extra CUT, S0 finding K-2). H2: every step factor's change instants inside the support are listed and
                  asserted complete; the list is also checked against the factor's own values (a hidden change is found);
  6. AT THE PEAK  score, evidence_for, evidence_against and the valence the evidence implies, re-derived at `t*`.

(I) INTERPRETATIONS made where the spec is silent (each listed with its alternative in the job notes):
  - the stored arc index ends at spline stations that differ from the Swiss ones by up to 16.7 s (S0 K-2): a velocity sign change within
    NEAR_END_S (120 s) of a support end is a CUT, one farther inside is an H1 failure (alternative: a smaller window — risks refusing
    a legitimate arc);
  - the maximum is RE-DERIVED (the stored value is a float4, the stored instant may sit a second from the crest) and the ties are read off it;
  - check 3 and check 4 both carry the Q12 tolerance, so a peak 0.5 s from its crest is accepted and one 30 s away is not;
  - "the earliest qualifying extremum differs" across the grey band means by more than the Q12 tolerance (extrema within 1 s of each
    other are interchangeable at the stored instant's own resolution; alternative: any difference — flags more windows);
  - with ONE body behind every tent of a piece F is convex in that body's (monotone) longitude: its supremum is an end value and it has no
    interior local maximum, however the terms rise and fall (two natal points a fixed distance apart make F exactly flat);
  - the prover takes plain data (`CheckRecord`, `StoredWindow`, a `position_at` callable); adapting the stored rows is the integration's job.

A window the prover cannot settle inside its budget is UNVERIFIED (blocks the seal), never a pass. The prover never
repairs: it returns VERIFIED, REFUTED (with the findings, each naming the claim it falsifies) or UNVERIFIED.

Time: windows are half-open `[lo, hi)`; the value of an open right end is the limit (taken at `b - 1 us` where an
instant is needed). Internally time is float seconds from `lo`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Optional

# ── the frozen objective definitions, restated (plan §2.1) ──────────────────────────────────────────────────────────────
OBJ_SUM = "evidence_for_per_root_sum"          # P1, P2, P3: F(t) = sum over roots of the per-root max for-channel value
OBJ_MAXMIN = "max_min_agent_activity"          # P4: F(t) = min(act_Jupiter(t), act_Saturn(t)), defined where both are live
OBJECTIVES = (OBJ_SUM, OBJ_MAXMIN)
CH_FOR = "evidence_for_occurrence"
CH_AGAINST = "evidence_against_occurrence"
P4_AGENTS = frozenset({"jupiter", "saturn"})

# ── tolerances (each a statement of what is being compared) ─────────────────────────────────────────────────────────────
VALUE_TOL = 1e-6              # a stored REAL (float4) number against a double re-derivation
F4_ABS_SLACK = 1e-10          # added to the float4 half-spacing: the builder's own unrounded accuracy (R-1 a: half-ulp of M plus 1e-10)
TIE = 1e-9                    # the frozen peak-tie tolerance between distinct local extrema
GREY = 2e-10                  # grey band around the tie threshold: an ambiguity detector only (R-1 b)
PEAK_INSTANT_TOLERANCE_S = 1.0   # owner decision SOLVER-TOLERANCES (Q12 a): exact to the second
PLATEAU_EPS = 1e-12           # two objective samples this close are one plateau (float noise on longitudes of size 360 is ~6e-14)

# ── geometry of the proof ───────────────────────────────────────────────────────────────────────────────────────────────
H1_SAMPLE_S = 5.0 * 86400.0   # velocity-sign sampling spacing; premise: the audited minimum station spacing is 19.75 d
MIN_STATION_SPACING_D = 19.75  # S0 measurement 19.7585 d (Mercury); must exceed 2 x H1_SAMPLE_S for "no hidden pair"
NEAR_END_S = 120.0            # a station this close to a support end is a Swiss/spline offset (<= 16.7 s measured), a cut
VEL_H_S = 600.0               # half-width of the centred-difference velocity (the speed is read, never assumed)
MIN_WIDTH_S = 1e-3            # the bound search stops bisecting here (UNVERIFIED if still not certified)
LEAF_S = 0.0864               # resolution (1e-6 d) of the extremum enumeration; each extremum is then located to a microsecond
ISOLATION_S = 4.0             # R-3: tied extrema closer than this (2 x the builder's LEAF, <= 2 s on the real sky: window_solver H5) are not isolated
LOCATE_XTOL_S = 1e-6           # an extremum is located to a microsecond: a kinked peak loses < 1e-10 of value at that distance
US = 1e-6
H2_FRACTIONS = (1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7)
DEFAULT_MAX_EVALS = 2_000_000  # ephemeris evaluations; verifier budget = 20 x the builder's (plan §2.4)

assert 2 * H1_SAMPLE_S / 86400.0 < MIN_STATION_SPACING_D, "H1's no-hidden-reversal-pair premise needs the sampling finer than the station spacing"

VERIFIED, REFUTED, UNVERIFIED = "VERIFIED", "REFUTED", "UNVERIFIED"

# finding codes (REFUTED) and unverified reasons
F_VALUE = "peak_value_mismatch"
F_ABOVE = "objective_exceeds_stored_maximum"
F_EARLIER_TIE = "earlier_tie_not_taken"
F_INSTANT = "peak_instant_mismatch"
F_H1 = "monotone_arc_not_established"
F_H2 = "state_boundaries_incomplete"
F_UNDET = "operand_undeterminable"
F_UNQ = "unqualified_member_in_numbered_window"
F_RANGE = "factor_value_outside_unit_interval"
F_OUTSIDE = "peak_outside_window"
F_SCORE = "score_mismatch"
F_EVFOR = "evidence_for_mismatch"
F_EVAGAINST = "evidence_against_mismatch"
F_VALENCE = "valence_mismatch"
U_BUDGET = "verifier_budget_exhausted"
U_CERT = "solver_certificate_incomplete"
U_TIE = "tie_scan_inconclusive"
U_AMBIG = "tie_ambiguous"            # INCONCLUSIVE (R-6): the earliest qualifying extremum differs across theta +- GREY
U_ISOLATION = "tie_isolation_unresolved"

#: the claim each finding falsifies (plan §2.4 numbering; the prover's own list is in the tests)
CLAIM_OF = {F_VALUE: "value_at_peak", F_ABOVE: "upper_bound", F_EARLIER_TIE: "earliest_tie", F_INSTANT: "peak_instant",
            F_H1: "H1", F_H2: "H2", F_UNDET: "operands", F_UNQ: "qualification", F_RANGE: "operands",
            F_OUTSIDE: "value_at_peak", F_SCORE: "at_the_peak", F_EVFOR: "at_the_peak", F_EVAGAINST: "at_the_peak",
            F_VALENCE: "at_the_peak"}


class _NotGiven:
    def __repr__(self):
        return "NOT_GIVEN"


NOT_GIVEN = _NotGiven()           # a stored field the caller does not want compared (None means a stored NULL)


def _f4_tol(x: float) -> float:
    """The widest error a stored REAL (float4, 24-bit significand) can carry against the unrounded number it stores: half a float4
    spacing at `x`'s magnitude, plus F4_ABS_SLACK (R-1 a). A fixed absolute tolerance is wrong at both ends: below 1 it is slack, above
    ~2 a correct round-trip exceeds it."""
    _, e = math.frexp(abs(float(x)))
    return math.ldexp(1.0, e - 25) + F4_ABS_SLACK


@dataclass(frozen=True)
class StepFactor:
    """A factor that is piecewise constant in time (membership steps stay in `CheckRecord.constant`).

    value_at     the factor's value in [0,1] at an instant (None = undeterminable)
    boundaries   (lo, hi) -> the instants inside [lo, hi) at which THIS factor's state changes (None = no provider)
    complete     the store asserts that list is complete over every support of the record (H2)"""
    value_at: Callable[[datetime], Optional[float]]
    boundaries: Optional[Callable[[datetime, datetime], list]] = None
    complete: bool = False


@dataclass(frozen=True)
class TentFactor:
    """The angular kernel: value `max(0, 1 - d/orb)`, `d` the seam-safe angular distance between the body's longitude (shifted
    by the directed ray angle, if any) and the target level. The only continuous factor."""
    body: str
    level_deg: float
    orb_deg: float
    ray_deg: Optional[float] = None


@dataclass(frozen=True)
class CheckRecord:
    """One stored member: its supports, and its value `constant x steps x tent` on them.

    channel       CH_FOR / CH_AGAINST (static), or None = unknown (only legitimate when `channel_at` decides per instant)
    channel_at    the side at an instant (P1 agent_nature, Q3), with `channel_boundaries(lo, hi)` its change instants
    qualified     False = the stored qualification found the record's value undeterminable (allowed in a numbered window
                  only on the against channel; it then makes `evidence_against` NULL where it is live)"""
    record_id: str
    root: str
    agent: str
    supports: tuple
    constant: float = 1.0
    steps: tuple = ()
    tent: Optional[TentFactor] = None
    channel: Optional[str] = CH_FOR
    channel_at: Optional[Callable[[datetime], Optional[str]]] = None
    channel_boundaries: Optional[Callable[[datetime, datetime], list]] = None
    qualified: bool = True


@dataclass(frozen=True)
class StoredWindow:
    """What the build stored for a numbered window. Fields left NOT_GIVEN are not compared."""
    peak_instant: datetime
    objective_value: float
    score: object = NOT_GIVEN
    evidence_for: object = NOT_GIVEN
    evidence_against: object = NOT_GIVEN
    outcome_valence: object = NOT_GIVEN


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str

    @property
    def claim(self) -> str:
        return CLAIM_OF.get(self.code, self.code)


@dataclass(frozen=True)
class CheckReport:
    status: str
    findings: tuple
    unverified: tuple                 # ((reason, detail), ...)
    evals: int
    rederived: dict

    @property
    def verified(self) -> bool:
        return self.status == VERIFIED

    def codes(self) -> list:
        return [f.code for f in self.findings] + [r for r, _ in self.unverified]


class _Budget(Exception):
    pass


class _Undet(Exception):
    def __init__(self, what: str):
        super().__init__(what)
        self.what = what


@dataclass
class _Ent:
    rid: str
    root: str
    agent: str
    c: float
    tent: Optional[TentFactor]
    chan: Optional[str]


@dataclass
class _Piece:
    l: float
    r: float
    ents: list
    defined: bool
    groups: list = field(default_factory=list)
    vl: list = field(default_factory=list)
    vr: list = field(default_factory=list)
    pure: bool = True
    F_l: float = 0.0
    F_r: float = 0.0
    U: float = 0.0
    units: Optional[list] = None            # sum objective: the root groups, grouped by the ONE body their tents read
    mixed: list = field(default_factory=list)   # …and the roots whose tents read several bodies (bounded record by record)


@dataclass
class _R:
    rec: CheckRecord
    sup: list


class _Engine:
    def __init__(self, lo, hi, records, objective, stored, position_at, *, peak_tolerance_s, max_evals,
                 event_class, against_evaluated):
        if objective not in OBJECTIVES:
            raise ValueError(f"unknown objective {objective!r}")
        if not (lo.tzinfo and hi.tzinfo and stored.peak_instant.tzinfo):
            raise ValueError("instants must be timezone-aware")
        self.lo, self.hi, self.objective, self.stored = lo, hi, objective, stored
        self.L = (hi - lo).total_seconds()
        self.position_at = position_at
        self.tol_s = float(peak_tolerance_s)
        self.max_evals = int(max_evals)
        self.event_class, self.against_evaluated = event_class, against_evaluated
        self.evals = 0
        self.findings: list = []
        self.unverified: list = []
        self._lon_cache: dict = {}
        self._h1_cache: dict = {}
        self.rederived: dict = {}
        self.recs: list = []
        for rec in records:
            sup = []
            for a, b in rec.supports:
                x, y = max(self._sec(a), 0.0), min(self._sec(b), self.L)
                if x < y:
                    sup.append((x, y))
            if sup:
                self.recs.append(_R(rec, sup))
        self.pieces: list = []

    def _add(self, code: str, detail: str):
        f = Finding(code, detail)
        if f not in self.findings:
            self.findings.append(f)

    # ── time and the ephemeris ──────────────────────────────────────────────────────────────────────────────────────────
    def _dt(self, t: float) -> datetime:
        return self.lo + timedelta(seconds=t)

    def _sec(self, d: datetime) -> float:
        return (d - self.lo).total_seconds()

    def _lon(self, body: str, t: float) -> float:
        key = (body, t)
        v = self._lon_cache.get(key)
        if v is None:
            if self.evals >= self.max_evals:
                raise _Budget()
            self.evals += 1
            v = float(self.position_at(body, self._dt(t)))
            self._lon_cache[key] = v
        return v

    def _s(self, tent: TentFactor, t: float) -> float:
        """The signed seam-safe offset of the (ray-shifted) body longitude from the target level, in [-180, 180)."""
        eff = self._lon(tent.body, t)
        if tent.ray_deg is not None:
            eff = (eff + float(tent.ray_deg)) % 360.0
        return (eff - tent.level_deg + 180.0) % 360.0 - 180.0

    def _tent(self, tent: TentFactor, t: float) -> float:
        return max(0.0, 1.0 - abs(self._s(tent, t)) / float(tent.orb_deg))

    def _vel(self, body: str, t: float) -> float:
        a, b = self._lon(body, t - VEL_H_S), self._lon(body, t + VEL_H_S)
        return (((b - a + 180.0) % 360.0) - 180.0) / (2.0 * VEL_H_S)

    # ── root finding on a function whose sign changes exactly once in [p, q] ───────────────────────────────────────────
    @staticmethod
    def _bisect(g, p: float, q: float, gp: float) -> float:
        for _ in range(120):
            m = 0.5 * (p + q)
            if m <= p or m >= q or q - p < 1e-7:
                break
            gm = g(m)
            if gm == 0.0:
                return m
            if (gm > 0.0) == (gp > 0.0):
                p, gp = m, gm
            else:
                q = m
        return 0.5 * (p + q)

    # ── H1: the arc is monotone, and where a Swiss station sits within seconds of a support end it is a cut ───────────
    def _stations(self, body: str, a: float, b: float):
        """-> (cuts inside (a, b), None) or (None, reason). Samples the velocity sign every <= 5 d from a - E to b + E."""
        key = (body, a, b)
        if key in self._h1_cache:
            return self._h1_cache[key]
        e = NEAR_END_S
        if b - a > 2 * e:
            n = max(1, math.ceil((b - a - 2 * e) / H1_SAMPLE_S))
            pts = [a - e] + [a + e + (b - a - 2 * e) * i / n for i in range(n + 1)] + [b + e]
        else:
            pts = [a - e, b + e]
        vs = [self._vel(body, t) for t in pts]
        sg = [(v > 0.0) - (v < 0.0) for v in vs]
        cuts, why = [], None
        for i in range(len(pts) - 1):
            if sg[i] == 0:
                ts = pts[i]
            elif sg[i] * sg[i + 1] < 0:
                ts = self._bisect(lambda t: self._vel(body, t), pts[i], pts[i + 1], vs[i])
            else:
                continue
            if ts <= a or ts >= b:
                continue                                    # the station is outside the support: the arc is monotone inside
            if ts - a <= e or b - ts <= e:
                cuts.append(ts)                             # K-2: the Swiss station beside a spline-station end — a cut
            else:
                why = (f"{body}: the velocity changes sign at {self._dt(ts).isoformat()}, strictly inside the support "
                       f"[{self._dt(a).isoformat()}, {self._dt(b).isoformat()}) — more than {e:.0f} s from either end")
        res = (None, why) if why else (sorted(set(cuts)), None)
        self._h1_cache[key] = res
        return res

    def _tent_cuts(self, tent: TentFactor, a: float, b: float, rid: str) -> list:
        """Station cuts and the three roots (orb entry, crest, orb exit) of the monotone offset, inside one support."""
        cuts, why = self._stations(tent.body, a, b)
        if why:
            self._add(F_H1, f"record {rid}: {why}")
            return []
        edges = [a] + list(cuts) + [b]
        out = list(cuts)
        orb = float(tent.orb_deg)
        for x, y in zip(edges, edges[1:]):
            n = max(1, math.ceil((y - x) / H1_SAMPLE_S))
            ts = [x + (y - x) * i / n for i in range(n + 1)]
            ss = [self._s(tent, t) for t in ts]
            for level in (-orb, 0.0, orb):
                for i in range(n):
                    if abs(ss[i + 1] - ss[i]) >= 180.0:
                        continue                            # the +-180 seam, not a crossing
                    p, q = ss[i] - level, ss[i + 1] - level
                    if p == 0.0:
                        out.append(ts[i])
                    elif p * q < 0.0:
                        out.append(self._bisect(lambda t, lv=level: self._s(tent, t) - lv, ts[i], ts[i + 1], p))
        return [c for c in out if a < c < b]

    # ── the cuts and the pieces ─────────────────────────────────────────────────────────────────────────────────────────
    def _matters(self, rc: _R) -> bool:
        """Does the record's value enter the objective? (An against-only record cannot move a for-channel sum.)"""
        rec = rc.rec
        if not rec.qualified:
            return False
        if self.objective == OBJ_MAXMIN:
            return True
        return rec.channel != CH_AGAINST or rec.channel_at is not None

    def _cuts(self) -> list:
        cuts = {0.0, self.L}
        for rc in self.recs:
            rec = rc.rec
            for a, b in rc.sup:
                cuts.update((a, b))
            if not self._matters(rc):
                continue
            for a, b in rc.sup:
                for st in rec.steps:
                    if st.boundaries is None or not st.complete:
                        self._add(F_H2, f"record {rec.record_id}: a step factor's change instants are not listed "
                                        "completely (no provider, or not asserted complete)")
                        break
                    cuts.update(c for c in (self._sec(x) for x in st.boundaries(self._dt(a), self._dt(b))) if a < c < b)
                if rec.channel_at is not None and rec.channel_boundaries is not None:
                    cuts.update(c for c in (self._sec(x) for x in rec.channel_boundaries(self._dt(a), self._dt(b)))
                                if a < c < b)
                if rec.tent is not None:
                    cuts.update(self._tent_cuts(rec.tent, a, b, rec.record_id))
        return sorted(c for c in cuts if 0.0 <= c <= self.L)

    def _step_value(self, rec: CheckRecord, st: StepFactor, t: float) -> float:
        x = st.value_at(self._dt(t))
        if x is None:
            raise _Undet(f"record {rec.record_id}: a step factor is undeterminable at {self._dt(t).isoformat()}")
        if not (-1e-12 <= x <= 1.0 + 1e-12):
            self._add(F_RANGE, f"record {rec.record_id}: a step factor reads {x} outside [0, 1]")
        return float(x)

    def _make_piece(self, l: float, r: float) -> _Piece:
        ents = []
        for rc in self.recs:
            rec = rc.rec
            if not any(a <= l < b for a, b in rc.sup):
                continue
            if not rec.qualified:
                if self.objective == OBJ_SUM and rec.channel != CH_AGAINST:
                    self._add(F_UNQ, f"record {rec.record_id} is unqualified yet live on the for/unknown "
                                     "channel in a numbered window")
                continue
            chan = rec.channel_at(self._dt(l)) if rec.channel_at is not None else rec.channel
            if self.objective == OBJ_SUM:
                if chan is None:
                    raise _Undet(f"record {rec.record_id}: its channel is undeterminable at {self._dt(l).isoformat()}")
                if chan != CH_FOR:
                    continue
            c = float(rec.constant)
            for st in rec.steps:
                x0 = self._step_value(rec, st, l)
                if r - l > 2e-5:                              # H2: the piece is constant in the factor's own values
                    for fr in H2_FRACTIONS + (None,):
                        t = r - 1e-5 if fr is None else l + (r - l) * fr
                        if abs(self._step_value(rec, st, t) - x0) > 1e-12:
                            self._add(F_H2, (
                                f"record {rec.record_id}: a step factor changes inside the piece "
                                f"[{self._dt(l).isoformat()}, {self._dt(r).isoformat()}) near {self._dt(t).isoformat()} — "
                                "the listed change instants are not complete"))
                            break
                c *= x0
            ents.append(_Ent(rec.record_id, rec.root, rec.agent, c, rec.tent, chan))
        if self.objective == OBJ_SUM:
            roots: dict = {}
            for i, e in enumerate(ents):
                roots.setdefault(e.root, []).append(i)
            groups, defined = list(roots.values()), True
        else:
            agents: dict = {}
            for i, e in enumerate(ents):
                agents.setdefault(e.agent, []).append(i)
            groups, defined = list(agents.values()), set(agents) == P4_AGENTS
        pc = _Piece(l, r, ents, defined, groups)
        if not defined:
            return pc
        pc.vl, pc.vr = self._vals(pc, l), self._vals(pc, r)
        up = any(b > a + 1e-15 for a, b, e in zip(pc.vl, pc.vr, ents) if e.tent is not None)
        down = any(b < a - 1e-15 for a, b, e in zip(pc.vl, pc.vr, ents) if e.tent is not None)
        convex = False
        if self.objective == OBJ_SUM:
            by_body: dict = {}
            for g in groups:
                bs = {ents[i].tent.body for i in g if ents[i].tent is not None and ents[i].c != 0.0}
                if len(bs) > 1:
                    pc.mixed.append(g)
                else:
                    by_body.setdefault(next(iter(bs)) if bs else None, []).append(g)
            pc.units = list(by_body.values())
            # ONE body behind every tent of the piece: each tent is AFFINE in that body's longitude (a single branch, the cuts see to
            # it), a max over records and a sum over roots of affine functions is CONVEX in the longitude, and the longitude is monotone
            # in time (H1) — so F has no interior local maximum and its supremum is an end value, exactly, however the terms rise and
            # fall (two natal points a fixed distance apart make F exactly flat between them: a long plateau, no search)
            convex = not pc.mixed and len([k for k in by_body if k is not None]) <= 1
        pc.pure = (not (up and down)) or convex
        pc.F_l, pc.F_r, pc.U = self._reduce(pc, pc.vl), self._reduce(pc, pc.vr), self._reduce_upper(pc, pc.vl, pc.vr)
        return pc

    def _vals(self, pc: _Piece, t: float) -> list:
        return [e.c if (e.tent is None or e.c == 0.0) else e.c * self._tent(e.tent, t) for e in pc.ents]

    def _reduce(self, pc: _Piece, vals: list) -> float:
        if self.objective == OBJ_SUM:
            return sum(max(vals[i] for i in g) for g in pc.groups)
        return min(max(vals[i] for i in g) for g in pc.groups)

    def _reduce_upper(self, pc: _Piece, v1: list, v2: list) -> float:
        """An upper bound of F on a stretch of the piece whose end values are v1, v2: per one-body unit the larger end value of the
        (convex) unit sum; per several-body root the larger end value of each record."""
        if self.objective == OBJ_SUM and pc.units is not None:
            total = 0.0
            for groups in pc.units:
                total += max(sum(max(v1[i] for i in g) for g in groups), sum(max(v2[i] for i in g) for g in groups))
            for g in pc.mixed:
                total += max(max(v1[i], v2[i]) for i in g)
            return total
        return self._reduce(pc, [max(a, b) for a, b in zip(v1, v2)])

    # ── the objective at one instant, straight from the members (independent of the piece structure) ──────────────────
    def _live(self, t: float) -> dict:
        d = self._dt(t)
        live, unq = [], []
        for rc in self.recs:
            rec = rc.rec
            if not any(a <= t < b for a, b in rc.sup):
                continue
            if not rec.qualified:
                unq.append(rec)
                continue
            ch = rec.channel_at(d) if rec.channel_at is not None else rec.channel
            v = float(rec.constant)
            for st in rec.steps:
                v *= self._step_value(rec, st, t)
            if rec.tent is not None and v != 0.0:
                v *= self._tent(rec.tent, t)
            live.append((rec, ch, v))
        return {"live": live, "unq": unq}

    def _objective_at(self, t: float, live=None):
        lv = (live or self._live(t))["live"]
        if self.objective == OBJ_MAXMIN:
            act: dict = {}
            for rec, _, v in lv:
                act[rec.agent] = max(act.get(rec.agent, 0.0), v)
            return min(act.values()) if set(act) == P4_AGENTS else None
        per_root: dict = {}
        for rec, ch, v in lv:
            if ch is None:
                raise _Undet(f"record {rec.record_id}: its channel is undeterminable at {self._dt(t).isoformat()}")
            if ch == CH_FOR:
                per_root[rec.root] = max(per_root.get(rec.root, 0.0), v)
        return sum(per_root.values())

    # ── check 2: the first-order upper bound ────────────────────────────────────────────────────────────────────────────
    def _witness(self, t: float, thr: float):
        v = self._objective_at(t)
        return v if (v is not None and v > thr) else None

    def _bound(self, m_stored: float):
        thr = m_stored + _f4_tol(m_stored)
        worst = None
        for pc in self.pieces:
            if not pc.defined:
                continue
            if pc.pure:                                        # monotone: the supremum is an end value — exact, no search
                if pc.U > thr:
                    for t in (pc.l, pc.r - US):
                        w = self._witness(t, thr)
                        if w is not None:
                            self._above(t, w, m_stored)
                            return
                continue
            for t, f in ((pc.l, pc.F_l), (pc.r - US, pc.F_r)):
                if f > thr:
                    w = self._witness(t, thr)
                    if w is not None:
                        self._above(t, w, m_stored)
                        return
            stack = [(pc.l, pc.r, pc.vl, pc.vr)]
            while stack:
                l, r, vl, vr = stack.pop()
                if self._reduce_upper(pc, vl, vr) <= thr:
                    continue                                   # certified: nothing in [l, r) exceeds the threshold
                m = 0.5 * (l + r)
                vm = self._vals(pc, m)
                if self._reduce(pc, vm) > thr:
                    w = self._witness(m, thr)
                    if w is not None:
                        self._above(m, w, m_stored)
                        return
                if r - l <= MIN_WIDTH_S:
                    worst = (l, r)
                    continue
                stack.append((m, r, vm, vr))
                stack.append((l, m, vl, vm))
        if worst is not None:
            self.unverified.append((U_CERT, f"the bound could not be pushed under M + {_f4_tol(m_stored):.3g} on "
                                            f"[{self._dt(worst[0]).isoformat()}, {self._dt(worst[1]).isoformat()}) at the "
                                            f"{MIN_WIDTH_S} s width floor"))

    def _above(self, t: float, value: float, m_stored: float):
        self.findings.append(Finding(F_ABOVE, f"the objective reaches {value!r} at {self._dt(t).isoformat()}, above the "
                                              f"stored maximum {m_stored!r} + {_f4_tol(m_stored):.3g}"))
        self.rederived["witness"] = (self._dt(t), value)

    # ── checks 3-4: the earliest DISTINCT LOCAL EXTREMUM within the tie tolerance of the maximum ──────────────────────
    def _points(self, theta: float):
        """In time order: ('gap') for a stretch whose bound is below theta, else (t, F, kind) with kind 'start' / 'end'
        (the edge samples of a piece: F at l and the left limit at r) or 'interior' (a continuous sample inside a piece)."""
        gap = ("gap",)
        last_gap = False
        for pc in self.pieces:
            if not pc.defined or (pc.pure and pc.U < theta):
                if not last_gap:
                    yield gap
                last_gap = True
                continue
            if pc.pure:
                last_gap = False
                yield (pc.l, pc.F_l, "start")
                yield (pc.r, pc.F_r, "end")
                continue
            stack = [(pc.l, pc.r, pc.vl, pc.vr)]
            prev_end = None
            while stack:
                l, r, vl, vr = stack.pop()
                if self._reduce_upper(pc, vl, vr) < theta:
                    if not last_gap:
                        yield gap
                    last_gap, prev_end = True, None
                    continue
                if r - l > LEAF_S:
                    m = 0.5 * (l + r)
                    vm = self._vals(pc, m)
                    stack.append((m, r, vm, vr))
                    stack.append((l, m, vl, vm))
                    continue
                if prev_end != l:
                    yield (l, self._reduce(pc, vl), "start" if l == pc.l else "interior")
                yield (r, self._reduce(pc, vr), "end" if r == pc.r else "interior")
                last_gap, prev_end = False, r
        if not last_gap:
            yield gap

    def _extrema(self, theta: float) -> list:
        """Every distinct local maximum of F with F >= theta, in time order, as [(t, F), ...]. A local maximum is a maximal run of
        equal samples whose neighbours are both lower (a stretch below theta counts as lower); a plateau's instant is its start, an
        edge peak the last microsecond before the drop, an interior one is located by golden-section search. A sampled peak is only
        a candidate: the located one must itself reach theta (a kinked crest is narrower than a sample)."""
        ninf = float("-inf")
        out = []
        cur = None                                              # [value, first_point, n, point_before, left_lower]
        prev_pt = None
        for pt in self._points(theta):
            f = ninf if pt[0] == "gap" else pt[1]
            if cur is not None and ((f == ninf and cur[0] == ninf) or (f > ninf and cur[0] > ninf
                                                                       and abs(f - cur[0]) <= PLATEAU_EPS)):
                cur[2] += 1
                prev_pt = pt
                continue
            if cur is not None and cur[0] > ninf and cur[4] and f < cur[0]:
                got = self._locate(cur, pt)
                if got[1] >= theta:
                    out.append(got)
            cur = [f, pt, 1, prev_pt, cur is None or cur[0] < f]
            prev_pt = pt
        if cur is not None and cur[0] > ninf and cur[4]:
            got = self._locate(cur, None)
            if got[1] >= theta:
                out.append(got)
        return out

    def _locate(self, run, after):
        _, first, n, before, _ = run
        t0, f0, kind = first
        if n == 1 and kind == "end":
            return t0 - US, f0
        if n > 1 or kind != "interior":
            return t0, f0
        lo_t = before[0] if before is not None and before[0] != "gap" else t0 - LEAF_S
        hi_t = after[0] if after is not None and after[0] != "gap" else t0 + LEAF_S
        lo_t, hi_t = min(lo_t, t0), max(hi_t, t0)
        g = (math.sqrt(5.0) - 1.0) / 2.0
        a, b = lo_t, hi_t
        c, d = b - g * (b - a), a + g * (b - a)
        fc, fd = self._objective_at(c), self._objective_at(d)
        while b - a > LOCATE_XTOL_S:
            if fc is None or fd is None:
                break
            if fc >= fd:
                b, d, fd = d, c, fc
                c = b - g * (b - a)
                fc = self._objective_at(c)
            else:
                a, c, fc = c, d, fd
                d = a + g * (b - a)
                fd = self._objective_at(d)
        t = 0.5 * (a + b)
        ft = self._objective_at(t)
        return (t, ft) if ft is not None and ft >= f0 else (t0, f0)

    # ── check 6: the numbers carried by the peak ────────────────────────────────────────────────────────────────────────
    def _at_peak(self, t: float, f_peak: float):
        st = self.stored
        snap = self._live(t)
        lv, unq = snap["live"], snap["unq"]
        for_roots: dict = {}
        against_roots: dict = {}
        for rec, ch, v in lv:
            slot = for_roots if ch == CH_FOR else against_roots if ch == CH_AGAINST else None
            if slot is None:
                raise _Undet(f"record {rec.record_id}: its channel is undeterminable at {self._dt(t).isoformat()}")
            slot[rec.root] = max(slot.get(rec.root, 0.0), v)
        want_for = sum(for_roots.values())
        unq_against = [r for r in unq if r.channel != CH_FOR]
        against_null = (not self.against_evaluated) or bool(unq_against)
        want_against = None if against_null else sum(against_roots.values())
        if self.objective == OBJ_MAXMIN:
            want_score = f_peak
        elif unq:
            want_score = None
        else:
            want_score = max((v for _, _, v in lv), default=0.0)
        self.rederived.update(score=want_score, evidence_for=want_for, evidence_against=want_against)
        if st.score is not NOT_GIVEN and ((st.score is None) != (want_score is None) or (
                want_score is not None and abs(st.score - want_score) > max(VALUE_TOL, _f4_tol(want_score)))):
            self.findings.append(Finding(F_SCORE, f"score {st.score!r} != re-derived {want_score!r}"))
        if st.evidence_for is not NOT_GIVEN and (st.evidence_for is None or abs(st.evidence_for - want_for) > max(VALUE_TOL, _f4_tol(want_for))):
            self.findings.append(Finding(F_EVFOR, f"evidence_for {st.evidence_for!r} != re-derived {want_for!r}"))
        if st.evidence_against is not NOT_GIVEN and ((st.evidence_against is None) != (want_against is None) or (
                want_against is not None and abs(st.evidence_against - want_against) > max(VALUE_TOL, _f4_tol(want_against)))):
            self.findings.append(Finding(F_EVAGAINST, f"evidence_against {st.evidence_against!r} != re-derived "
                                                      f"{want_against!r}"))
        if st.outcome_valence is not NOT_GIVEN and self.event_class is not None:
            from services.gochara_rules import valence as _valence          # the rule authority, shared by design
            if want_against is not None:
                want_v = _valence.compute_valence(self.event_class, want_for, want_against, None)
            else:
                why = ("evidence_against_channel_unqualified" if any(r.channel != CH_FOR for r in self.recs_unq())
                       else "evidence_against_channel_not_evaluated")
                want_v = _valence.compute_valence(self.event_class, want_for, 0.0, why)
            self.rederived["valence"] = want_v.outcome_valence_for_native
            if st.outcome_valence != want_v.outcome_valence_for_native:
                self.findings.append(Finding(F_VALENCE, f"outcome valence {st.outcome_valence!r} != "
                                                        f"{want_v.outcome_valence_for_native!r} implied by the evidence"))

    def recs_unq(self):
        return [rc.rec for rc in self.recs if not rc.rec.qualified]

    # ── the run ─────────────────────────────────────────────────────────────────────────────────────────────────────────
    def run(self) -> CheckReport:
        try:
            self._run()
        except _Budget:
            self.unverified.append((U_BUDGET, f"more than {self.max_evals} ephemeris evaluations needed"))
        except _Undet as u:
            self.findings.append(Finding(F_UNDET, u.what))
        status = REFUTED if self.findings else UNVERIFIED if self.unverified else VERIFIED
        return CheckReport(status, tuple(self.findings), tuple(self.unverified), self.evals, dict(self.rederived))

    def _run(self):
        st = self.stored
        t_star = self._sec(st.peak_instant)
        if not (0.0 <= t_star < self.L):
            self.findings.append(Finding(F_OUTSIDE, f"peak {st.peak_instant.isoformat()} is outside [lo, hi)"))
            return
        xs = self._cuts()
        if self.findings:                                      # H1 / H2 failed: the numbers cannot be certified
            return
        xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 1e-9]
        self.pieces = [self._make_piece(l, r) for l, r in zip(xs, xs[1:])]
        if self.findings:
            return
        f_star = self._objective_at(t_star)
        self.rederived["value_at_peak"] = f_star
        if f_star is None or abs(f_star - st.objective_value) > max(VALUE_TOL, _f4_tol(st.objective_value)):
            self.findings.append(Finding(F_VALUE, f"the objective at the stored peak {st.peak_instant.isoformat()} is "
                                                  f"{f_star!r}, the stored value {st.objective_value!r}"))
        self._bound(st.objective_value)
        if self.findings:                                      # the stored maximum itself is wrong: a tie scan against it is moot
            return
        if f_star is not None:
            # The maximum itself is re-derived here (the stored value is a float4): every distinct local maximum within the widest
            # threshold of the stored peak's value is collected once; M-hat is the largest of them (UNROUNDED), the ties are read off it.
            cands = self._extrema(f_star - TIE - GREY - 1e-12)
            if not cands:
                self.unverified.append((U_TIE, "no local extremum reached the tie threshold — the scan is inconclusive"))
            else:
                m_hat = max(f for _, f in cands)
                self.rederived["maximum"] = m_hat
                if abs(st.objective_value - m_hat) > _f4_tol(m_hat):
                    self.findings.append(Finding(F_VALUE, (
                        f"the stored maximum {st.objective_value!r} is not the re-derived maximum {m_hat!r} inside its float4 "
                        f"interval (+-{_f4_tol(m_hat):.3g})")))
                theta = m_hat - TIE
                # the earliest QUALIFYING extremum (unrounded value >= theta) at the strict, nominal and lenient end of the grey band
                e_lo, e_mid, e_hi = (min(t for t, f in cands if f >= th) for th in (theta - GREY, theta, theta + GREY))
                self.rederived["earliest_tie"] = {"t": self._dt(e_mid), "grey": (self._dt(e_lo), self._dt(e_hi))}
                # R-3: which of several near-coincident tied extrema is the earliest DISTINCT one is not decided by either side's
                # sampling scale: a named blank, not a verdict (the value / bound / at-the-peak findings still stand).
                ties = sorted(t for t, f in cands if f >= theta)
                close = [(x, y) for x, y in zip(ties, ties[1:]) if y - x <= ISOLATION_S]
                if close:
                    self.rederived["tie_cluster"] = [(self._dt(x), self._dt(y)) for x, y in close]
                    self.unverified.append((U_ISOLATION, (
                        f"{len(ties)} extrema within the tie tolerance of the maximum, two of them {close[0][1] - close[0][0]:.3f} s "
                        f"apart from {self._dt(close[0][0]).isoformat()} (limit {ISOLATION_S} s): isolation is unresolved")))
                else:
                    widest = [t for t, f in cands if f >= theta - GREY]
                    if not any(abs(t_star - t) <= self.tol_s for t in widest):
                        self.findings.append(Finding(F_INSTANT, (
                            f"the stored peak {st.peak_instant.isoformat()} is within {self.tol_s} s of no extremum that reaches the tie "
                            f"threshold of the maximum (the earliest qualifying one is {self._dt(e_mid).isoformat()}, "
                            f"{t_star - e_mid:+.3f} s away)")))
                    elif e_hi - e_lo > self.tol_s:
                        self.unverified.append((U_AMBIG, (
                            f"the earliest extremum within the tie tolerance of the maximum is {self._dt(e_lo).isoformat()} at the strict "
                            f"end of the +-{GREY} grey band and {self._dt(e_hi).isoformat()} at the lenient end — which instant is the "
                            "frozen earliest tie is not decidable at this precision")))
                    elif abs(t_star - e_mid) > self.tol_s:
                        self.findings.append(Finding(F_EARLIER_TIE, (
                            f"a distinct local extremum within the tie tolerance of the maximum sits at {self._dt(e_mid).isoformat()}, "
                            f"before the stored peak {st.peak_instant.isoformat()}")))
            self._at_peak(t_star, f_star)


def check_window(*, lo: datetime, hi: datetime, records, objective: str, stored: StoredWindow, position_at,
                 peak_tolerance_s: float = PEAK_INSTANT_TOLERANCE_S, max_evals: int = DEFAULT_MAX_EVALS,
                 event_class: Optional[str] = None, against_evaluated: bool = False) -> CheckReport:
    """Prove (or refute) one numbered window's stored peak and objective value.

    lo, hi          the window `[lo, hi)`, timezone-aware
    records         the window's members (`CheckRecord`), qualified or not
    objective       OBJ_SUM (P1, P2, P3) or OBJ_MAXMIN (P4)
    stored          the stored peak instant and objective value (and, optionally, the score / evidence / valence at the peak)
    position_at     `(body, aware datetime) -> sidereal longitude in degrees`: the pinned Swiss function, or a test's stub
    peak_tolerance_s  Q12: how far the stored peak may sit from the re-derived instant (default 1 s, owner-confirmed)
    max_evals       the verifier's ephemeris budget; exhausting it makes the window UNVERIFIED
    event_class     needed only to re-derive the valence; against_evaluated: whether the path can evaluate the against channel
    """
    return _Engine(lo, hi, records, objective, stored, position_at, peak_tolerance_s=peak_tolerance_s, max_evals=max_evals,
                   event_class=event_class, against_evaluated=against_evaluated).run()


def satisfies_gate(report: CheckReport) -> bool:
    """A numbered window passes a gate ONLY when it is VERIFIED: a refutation or an unsettled window never does."""
    return report.status == VERIFIED


__all__ = ["CH_AGAINST", "CH_FOR", "CheckRecord", "CheckReport", "Finding", "NOT_GIVEN", "OBJ_MAXMIN", "OBJ_SUM",
           "REFUTED", "StepFactor", "StoredWindow", "TentFactor", "UNVERIFIED", "VERIFIED", "check_window", "satisfies_gate"]
