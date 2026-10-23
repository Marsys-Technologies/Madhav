"""The VERIFIER's check of the builder's solver certificate (SR-OD1 R-6 / R-7, plan-review ruling SR-PLAN-REVIEW-RECONCILED).

The builder (`window_solver`) stores the piece tree its answer rests on in the window's `qualification` jsonb under `solver_certificate`: the cuts,
the pieces, every cell with the bound it claims, the leaf brackets, the evaluation count and the limits it assumed. This module CHECKS that
certificate with the verifier's OWN first-order enclosure (`window_solver_check`, K12) — the builder's bounds are claims, never evidence — and
re-solves from scratch only (a) where the check cannot be completed, or (b) for a deterministic G-6 sample. It imports nothing from the builder
(`window_solver`, `window_sweep`): the certificate arrives as plain JSON and every literal it must agree with is restated below, equality with the
builder's own constants being asserted by a test.

WHAT IT DOES FOR A NUMBERED WINDOW (`check_numbered`)
  1. the certificate is well-formed, is for this objective, says "solved", assumes limits no weaker than the verifier's (tie 1e-9, 1 µs quantum,
     ≤ 5-day H1 spacing) and agrees with the STORED value and peak;
  2. every closed cell's claimed bound is WITNESSED: F at the cell's ends and middle (the verifier's own evaluation) must not exceed it — a claim
     the sky contradicts is a DISAGREEMENT, whatever the maximum;
  3. the verifier's own proof (`window_solver_check`: value, upper bound, earliest tie, instant, H1/H2, the numbers at the peak) runs with its
     search STARTED FROM THE CERTIFICATE'S PARTITION instead of from the whole piece. Soundness is the verifier's own: any partition of a monotone
     piece is covered by the first-order bound; an uncovered stretch is simply searched. If that check is UNVERIFIED (or refutes without an
     evaluated witness), the window is re-solved from scratch (no certificate) and THAT outcome stands; a refutation carrying an evaluated witness
     (`objective_exceeds_stored_maximum`, `peak_value_mismatch`) is a DISAGREEMENT as it stands — no re-solve can soften it. `resolve=True` (the G-6 sample) skips the certificate altogether.

WHAT IT DOES FOR A `solver_budget_exhausted` BLANK (`check_budget_blank`) — the blank is justified by its certificate, not by the reason string:
  the declared per-window budget is the policy's (500,000: a builder cannot blank an easy window by declaring a small one); the evaluation count
  reached it; the partial tree's closed-cell bounds are witnessed as above; and at least one OPEN cell remains that the verifier's own enclosure
  cannot discharge (its bound reaches the best value the verifier has seen, less the tie) — if every open cell is dischargeable the builder
  stopped with the work done, and the blank is not borne out.

TWO CLASSES OF UNVERIFIED (R-6). DISAGREEMENT — a bound violated, a different maximum, an earlier qualifying extremum, a certificate the sky or the
stored row contradicts, a blank whose certificate shows fewer evaluations than the declared budget or no open cell — blocks the seal, always.
INCONCLUSIVE — the verifier could not settle the window inside its own budget (`verifier_budget_exhausted`), or could not push its first-order bound under the
stored maximum + the float4 tolerance at its width floor with no evaluated point above it (`solver_certificate_incomplete`: nothing contradicts the stored number, the
verifier's bound is merely too loose to certify it; SR-TR2-DEFECT-B, see the note at `INCONCLUSIVE_REASONS`), or R-1/R-3's `tie_ambiguous` /
`tie_isolation_unresolved` — is demoted at seal to a named blank, counted, capped (see `numerical_window_gate`). An UNVERIFIED reason in none of these
is treated as a DISAGREEMENT: only the named reasons are ever demoted. A refutation (a point the verifier evaluated above the maximum) is a DISAGREEMENT whatever else is open.

(I) INTERPRETATIONS (each with its alternative in the job notes): "an unexpanded prunable leaf" is read as "a budget blank with no open cell the verifier
cannot discharge"; the G-6 sample rate defaults to 2 %; a H1/H2 failure the verifier finds under a budget-blank certificate makes the blank AGREED
(the window is blank either way; only the label differs) with the verifier's reason recorded.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from . import window_solver_check as chk

# ── restated literals (compared with the builder's by tests, never imported) ──────────────────────────────────────────────────
SCHEMA = "window_solver_certificate/1"
OBJECTIVE_NAMES = {chk.OBJ_SUM: "sum_of_group_max", chk.OBJ_MAXMIN: "min_of_group_max"}     # the frozen objective ↔ the builder's name for it
BUDGET_REASON = "solver_budget_exhausted"
POLICY_MAX_EVALS_WINDOW = 500_000      # the per-window builder budget the policy declares
OWN_QUANT = 1e-6
OWN_TIE = chk.TIE
OWN_H1_SPACING_S = chk.H1_SAMPLE_S
G6_SAMPLE_RATE = 0.02                  # the share of numbered windows re-solved from scratch (R-7; the rate is the caller's to raise)
STORED_INSTANT_TOL_S = 1e-5            # the builder's float seconds → a µs-quantised stored instant
CLOSED_KINDS = ("piece", "dead", "leaf", "pruned")
#: the verifier's findings that are an evaluated witness (not a partition-dependent search outcome): the objective at a real instant above the stored maximum, or other than the stored value
WITNESSED_REFUTATIONS = frozenset({chk.F_ABOVE, chk.F_VALUE})

AGREED, DISAGREEMENT, INCONCLUSIVE = "AGREED", "DISAGREEMENT", "INCONCLUSIVE"
#: the UNVERIFIED reasons that are demoted rather than blocking (R-6). `tie_ambiguous` (R-1) and `tie_isolation_unresolved` (R-3) are the
#: verifier's refusals to name an extremum it cannot isolate; `verifier_budget_exhausted` is its own work budget. `solver_certificate_incomplete` (SR-TR2-DEFECT-B):
#: the verifier's bound for a SUM over several bodies is the sum of each body's larger end value, which exceeds the function by the opposing bodies' variation across the
#: leaf (first order in the leaf width); a stored REAL may sit up to half a float4 spacing from the exact maximum, so where the rounding error is within that slack of
#: its limit the bound cannot get under M + tol at the 1 ms width floor although every point the verifier evaluated is at or under it. That is a bound too loose to certify,
#: not a sky that contradicts the number: the window is demoted to the named blank (counted, capped), never blocked as a DISAGREEMENT. A point above the threshold is a
#: witnessed refutation and stays a DISAGREEMENT (`classify` reads REFUTED first).
INCONCLUSIVE_REASONS = frozenset({chk.U_BUDGET, chk.U_CERT, "tie_isolation_unresolved", "tie_ambiguous"})

C_SCHEMA = "certificate_schema_invalid"
C_OBJECTIVE = "certificate_objective_mismatch"
C_LIMITS = "certificate_limits_not_the_policy"
C_STORED = "certificate_disagrees_with_stored_window"
C_WITNESS = "certificate_bound_violated"
C_BUDGET_DECLARED = "budget_declared_below_policy"
C_BUDGET_EVALS = "budget_blank_evals_below_declared"
C_NO_OPEN = "budget_blank_without_open_cell"
C_OUTCOME = "certificate_outcome_mismatch"


def _tol(kind: str, x: float) -> float:
    """The ONE place this module reads the verifier's numeric tolerances, both magnitude-aware (od1-r1 R-1, `window_solver_check._f4_tol`): `"bound"` — how far the
    verifier's own evaluation may exceed a cell's claimed bound `x`: half a float4 spacing at the bound's magnitude plus the checker's absolute slack (the same
    interval the checker's own upper-bound check uses); and `"value"` — how far the certificate's double maximum may sit from the stored REAL `x`: the wider of
    the checker's 1e-6 floor and half a float4 spacing at `x`. A fixed tolerance is wrong for a stored REAL of 32 or more, where half a spacing exceeds 1e-6 (GPT B2)."""
    if kind == "bound":
        return chk._f4_tol(x)
    if kind == "value":
        return max(chk.VALUE_TOL, chk._f4_tol(x))
    raise ValueError(kind)


def classify(report) -> str:
    """The class of a `window_solver_check.CheckReport`: AGREED (VERIFIED), DISAGREEMENT (REFUTED, or UNVERIFIED for any reason that is not a
    named INCONCLUSIVE one) or INCONCLUSIVE (UNVERIFIED for named reasons only)."""
    if report.status == chk.VERIFIED:
        return AGREED
    if report.status == chk.REFUTED or any(r not in INCONCLUSIVE_REASONS for r, _d in report.unverified):
        return DISAGREEMENT
    return INCONCLUSIVE


def g6_sampled(window_key: str, rate: float = G6_SAMPLE_RATE) -> bool:
    """Deterministic G-6 sampling: the window is re-solved from scratch iff the first 32 bits of sha256(key) fall below `rate`."""
    return int(hashlib.sha256(window_key.encode("utf-8")).hexdigest()[:8], 16) / 4294967296.0 < rate


@dataclass(frozen=True)
class CertReport:
    classification: str                       # AGREED | DISAGREEMENT | INCONCLUSIVE
    findings: tuple                           # ((code, detail), ...) — what makes it a DISAGREEMENT
    inconclusive: tuple                       # ((reason, detail), ...) — what makes it INCONCLUSIVE
    used_certificate: bool                    # the verification was seeded by (and witnessed against) the certificate
    fell_back: bool                           # the certificate check did not verify and the window was re-solved from scratch
    resolved: bool                            # a from-scratch re-solve was the whole check (the G-6 sample)
    evals: int
    cells_checked: int = 0
    open_cells: int = 0
    seeds: int = 0                            # sub-intervals the certificate's partition gave the verifier's search to start from
    inner: Optional[object] = None            # the `window_solver_check.CheckReport` that decided it (numbered windows)
    alternative_reason: Optional[str] = None  # a budget blank the verifier also finds blank for another named reason (H1/H2)

    @property
    def agreed(self) -> bool:
        return self.classification == AGREED

    def codes(self) -> list:
        return [c for c, _ in self.findings] + [r for r, _ in self.inconclusive]


# ── the engine: the verifier's own prover, its mixed-piece search seeded by the certificate's cells ─────────────────────────────

class _SeededEngine(chk._Engine):
    def __init__(self, *a, cells=None, **kw):
        super().__init__(*a, **kw)
        self.cells = cells                      # [(kind, l, r, u)] in engine seconds, or None = search from scratch
        self.witness_findings: list = []
        self.cells_checked = 0
        self.seed_count = 0

    def _seeds(self, pc):
        if not self.cells:
            return super()._seeds(pc)
        pts = {pc.l, pc.r}
        for _k, l, r, _u in self.cells:
            for x in (l, r):
                if pc.l < x < pc.r:
                    pts.add(x)
        ordered: list = []
        for x in sorted(pts):
            if not ordered or x - ordered[-1] > 1e-4:          # a sliver is absorbed: any partition of the piece is sound
                ordered.append(x)
        if ordered[-1] != pc.r:
            ordered[-1] = pc.r
        if len(ordered) < 3 or len(ordered) > 4000:
            return super()._seeds(pc)
        vals = [pc.vl] + [self._vals(pc, x) for x in ordered[1:-1]] + [pc.vr]
        self.seed_count += len(ordered) - 1
        return [(ordered[i], ordered[i + 1], vals[i], vals[i + 1]) for i in range(len(ordered) - 1)][::-1]

    def _run(self):
        super()._run()
        if self.cells and not self.findings:
            self._witness_cells()

    def _witness_cells(self):
        """A closed cell claims `sup F ≤ u` on [l, r]: F at the cell's ends and middle must not exceed it (the verifier's own evaluation)."""
        for kind, l, r, u in self.cells:
            if kind not in CLOSED_KINDS:
                continue
            for t in (l, 0.5 * (l + r), r):
                if not 0.0 <= t < self.L:
                    continue
                v = self._objective_at(t)
                self.cells_checked += 1
                if v is not None and v > u + _tol("bound", u):
                    self.witness_findings.append((C_WITNESS, f"a {kind} cell [{l!r}, {r!r}] claims the objective is at most {u!r}; "
                                                              f"the verifier evaluates {v!r} at {self._dt(t).isoformat()}"))
                    return


# ── the certificate's own consistency ────────────────────────────────────────────────────────────────────────────────────────

def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _parse(cert, *, objective: str, outcome: str, lo: datetime):
    """(problems, offset_seconds, cells, opens): offset maps the certificate's time origin onto this verifier's (seconds from `lo`)."""
    bad: list = []
    if not isinstance(cert, dict) or cert.get("schema") != SCHEMA:
        return [(C_SCHEMA, f"the window carries no {SCHEMA} certificate")], 0.0, [], []
    if cert.get("objective") != OBJECTIVE_NAMES.get(objective):
        bad.append((C_OBJECTIVE, f"the certificate is for objective {cert.get('objective')!r}, the window's is {OBJECTIVE_NAMES.get(objective)!r}"))
    if cert.get("outcome") != outcome:
        bad.append((C_OUTCOME, f"the certificate says {cert.get('outcome')!r}, this check is for a {outcome!r} window"))
    try:
        t0 = datetime.fromisoformat(cert["t0"])
        if t0.tzinfo is None:
            raise ValueError("naive")
        offset = (t0 - lo).total_seconds()
    except (KeyError, TypeError, ValueError):
        return bad + [(C_SCHEMA, "the certificate's t0 is not a timezone-aware instant")], 0.0, [], []
    lim = cert.get("limits")
    if not isinstance(lim, dict) or not all(_num(lim.get(k)) for k in ("QUANT", "TIE", "H1_SPACING_S")):
        bad.append((C_SCHEMA, "the certificate does not state its limits"))
    else:
        if lim["TIE"] != OWN_TIE or lim["QUANT"] != OWN_QUANT or lim["H1_SPACING_S"] > OWN_H1_SPACING_S:
            bad.append((C_LIMITS, f"the certificate assumes {lim!r}; the policy is tie {OWN_TIE}, quantum {OWN_QUANT} s, H1 spacing ≤ {OWN_H1_SPACING_S} s"))
    cells, opens = [], []
    for c in cert.get("cells") if isinstance(cert.get("cells"), list) else [None]:
        if not (isinstance(c, list) and len(c) == 4 and c[0] in CLOSED_KINDS and all(_num(x) for x in c[1:]) and c[1] <= c[2]):
            bad.append((C_SCHEMA, f"a certificate cell is malformed: {c!r}"))
            break
        cells.append((c[0], c[1] + offset, c[2] + offset, c[3]))
    for c in cert.get("open") if isinstance(cert.get("open"), list) else [None]:
        if not (isinstance(c, list) and len(c) == 2 and all(_num(x) for x in c) and c[0] <= c[1]):
            bad.append((C_SCHEMA, f"a certificate open cell is malformed: {c!r}"))
            break
        opens.append((c[0] + offset, c[1] + offset))
    for k in ("evals", "max_evals"):
        if not _num(cert.get(k)):
            bad.append((C_SCHEMA, f"the certificate states no {k}"))
    return bad, offset, cells, opens


def _report(findings, inconclusive, **kw) -> CertReport:
    cls = DISAGREEMENT if findings else INCONCLUSIVE if inconclusive else AGREED
    return CertReport(cls, tuple(findings), tuple(inconclusive), **kw)


def _from_inner(inner, *, extra=(), **kw) -> CertReport:
    findings = [(f.code, f.detail) for f in inner.findings] + list(extra)
    cls = classify(inner)
    if cls == DISAGREEMENT and not findings:                       # an UNVERIFIED reason that is not a named INCONCLUSIVE one blocks
        findings = [(r, d) for r, d in inner.unverified if r not in INCONCLUSIVE_REASONS]
    inconclusive = [(r, d) for r, d in inner.unverified if r in INCONCLUSIVE_REASONS] if cls == INCONCLUSIVE else []
    return _report(findings, inconclusive, inner=inner, **kw)


# ── a numbered window ────────────────────────────────────────────────────────────────────────────────────────────────────────

def check_numbered(*, lo: datetime, hi: datetime, records, objective: str, stored, position_at, certificate, resolve: bool = False,
                   peak_tolerance_s: float = chk.PEAK_INSTANT_TOLERANCE_S, max_evals: int = chk.DEFAULT_MAX_EVALS,
                   event_class: Optional[str] = None, against_evaluated: bool = False) -> CertReport:
    """Verify one numbered window against its stored certificate (module doc). `resolve=True` is the G-6 sample: no certificate is used."""
    kw = dict(peak_tolerance_s=peak_tolerance_s, max_evals=max_evals, event_class=event_class, against_evaluated=against_evaluated)

    def run(cells):
        eng = _SeededEngine(lo, hi, records, objective, stored, position_at, cells=cells, **kw)
        return eng, eng.run()

    if resolve:
        eng, rep = run(None)
        return _from_inner(rep, used_certificate=False, fell_back=False, resolved=True, evals=eng.evals)

    bad, offset, cells, _opens = _parse(certificate, objective=objective, outcome="solved", lo=lo)
    if not bad:
        if not _num(certificate.get("value")) or abs(certificate["value"] - stored.objective_value) > _tol("value", stored.objective_value):
            bad.append((C_STORED, f"the certificate's maximum {certificate.get('value')!r} is not the stored objective value {stored.objective_value!r}"))
        if not _num(certificate.get("instant")) or abs((lo - stored.peak_instant).total_seconds() + certificate["instant"] + offset) > STORED_INSTANT_TOL_S:
            bad.append((C_STORED, f"the certificate's peak instant {certificate.get('instant')!r} s is not the stored peak {stored.peak_instant.isoformat()}"))
    if bad:
        return _report(bad, (), used_certificate=False, fell_back=False, resolved=False, evals=0)
    eng, rep = run(cells)
    if eng.witness_findings:
        return _report(eng.witness_findings, (), used_certificate=True, fell_back=False, resolved=False, evals=eng.evals,
                       cells_checked=eng.cells_checked, inner=rep)
    if rep.status == chk.VERIFIED:
        return _from_inner(rep, used_certificate=True, fell_back=False, resolved=False, evals=eng.evals, cells_checked=eng.cells_checked,
                           seeds=eng.seed_count)
    if rep.status == chk.REFUTED and any(f.code in WITNESSED_REFUTATIONS for f in rep.findings):
        # a refutation the verifier's own evaluation witnessed (a point above the stored maximum, a different value at the stored peak) is a sound DISAGREEMENT whatever the
        # partition; a from-scratch run that merely exhausted its budget must not turn it into an INCONCLUSIVE, demotable blank (lane review N-1)
        return _from_inner(rep, used_certificate=True, fell_back=False, resolved=False, evals=eng.evals, cells_checked=eng.cells_checked, seeds=eng.seed_count)
    eng2, rep2 = run(None)                                         # the certificate-seeded check did not verify (UNVERIFIED, or a refutation no point witnesses): from scratch
    return _from_inner(rep2, used_certificate=True, fell_back=True, resolved=False, evals=eng.evals + eng2.evals, cells_checked=eng.cells_checked,
                       seeds=eng2.seed_count)                      # `seeds` is the DECIDING run's: 0 for a from-scratch re-solve


# ── a solver_budget_exhausted blank ──────────────────────────────────────────────────────────────────────────────────────────

def check_budget_blank(*, lo: datetime, hi: datetime, records, objective: str, position_at, certificate,
                       max_evals: int = chk.DEFAULT_MAX_EVALS, event_class: Optional[str] = None) -> CertReport:
    """Is this window's `solver_budget_exhausted` blank borne out by its certificate? (module doc)"""
    bad, offset, cells, opens = _parse(certificate, objective=objective, outcome="blank", lo=lo)
    if not bad:
        if certificate.get("reason") != BUDGET_REASON:
            bad.append((C_OUTCOME, f"the certificate's reason is {certificate.get('reason')!r}, not {BUDGET_REASON!r}"))
        if certificate["max_evals"] != POLICY_MAX_EVALS_WINDOW:
            bad.append((C_BUDGET_DECLARED, f"the certificate declares a per-window budget of {certificate['max_evals']!r}; the policy's is {POLICY_MAX_EVALS_WINDOW}"))
        if certificate["evals"] < certificate["max_evals"]:
            bad.append((C_BUDGET_EVALS, f"the certificate shows {certificate['evals']!r} evaluations, fewer than the declared budget {certificate['max_evals']!r}"))
    if bad:
        return _report(bad, (), used_certificate=False, fell_back=False, resolved=False, evals=0)
    stored = chk.StoredWindow(lo, 0.0)                              # the engine's structure only: a blank has no stored number
    eng = _SeededEngine(lo, hi, records, objective, stored, position_at, cells=cells, peak_tolerance_s=chk.PEAK_INSTANT_TOLERANCE_S,
                        max_evals=max_evals, event_class=event_class, against_evaluated=False)
    try:
        xs = eng._cuts()
        if eng.findings:       # H1 / H2 fails on the verifier's own derivation: the window is blank either way, only the label differs
            return _report((), (), used_certificate=True, fell_back=False, resolved=False, evals=eng.evals, cells_checked=0,
                           open_cells=len(opens), alternative_reason=eng.findings[0].code)
        xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 1e-9]
        eng.pieces = [eng._make_piece(l, r) for l, r in zip(xs, xs[1:])]
        eng._witness_cells()
        if eng.witness_findings:
            return _report(eng.witness_findings, (), used_certificate=True, fell_back=False, resolved=False, evals=eng.evals,
                           cells_checked=eng.cells_checked, open_cells=len(opens))
        # the best value the verifier has seen: F at real instants is a lower bound of the maximum
        low = max([pc.F_l for pc in eng.pieces if pc.defined] +
                  [v for _k, l, r, _u in cells for t in (l, 0.5 * (l + r), r) if 0.0 <= t < eng.L for v in [eng._objective_at(t)] if v is not None],
                  default=0.0)
        alive = 0
        for l, r in opens:
            l, r = max(l, 0.0), min(r, eng.L)
            for pc in eng.pieces:
                if not pc.defined or pc.r <= l or pc.l >= r:
                    continue
                x, y = max(l, pc.l), min(r, pc.r)
                u = pc.U if x <= pc.l and y >= pc.r else eng._reduce_upper(pc, eng._vals(pc, x), eng._vals(pc, y))
                if u >= low - chk.TIE:
                    alive += 1
                    break
            if alive:
                break
    except chk._Budget:
        return _report((), ((chk.U_BUDGET, f"more than {max_evals} ephemeris evaluations needed to check the blank's certificate"),),
                       used_certificate=True, fell_back=False, resolved=False, evals=eng.evals, open_cells=len(opens))
    except chk._Undet as u:
        return _report([(chk.F_UNDET, u.what)], (), used_certificate=True, fell_back=False, resolved=False, evals=eng.evals, open_cells=len(opens))
    if not alive:
        return _report([(C_NO_OPEN, "every open cell of the partial tree is dischargeable by the verifier's own enclosure: the builder stopped with the work done")],
                       (), used_certificate=True, fell_back=False, resolved=False, evals=eng.evals, cells_checked=eng.cells_checked, open_cells=len(opens))
    return _report((), (), used_certificate=True, fell_back=False, resolved=False, evals=eng.evals, cells_checked=eng.cells_checked, open_cells=len(opens))


__all__ = ["AGREED", "DISAGREEMENT", "INCONCLUSIVE", "INCONCLUSIVE_REASONS", "SCHEMA", "BUDGET_REASON", "POLICY_MAX_EVALS_WINDOW", "G6_SAMPLE_RATE",
           "CertReport", "check_budget_blank", "check_numbered", "classify", "g6_sampled"]
