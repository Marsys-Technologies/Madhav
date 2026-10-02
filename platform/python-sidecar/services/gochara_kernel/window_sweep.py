"""Window sweep (A5.3 design v1.5; steward rulings M20261002T001617-5a34 / -dd2f).

Pure: no DB, no clock, no ephemeris. The store (`window_store`) reads a grain's records
and writes the windows this module drafts.

What is stored per window (ONE path-version × class — cross-path `max` is a serve/measure-time
reduction, never stored):

  interval         the CONNECTED UNION of its admitted records' supports (half-open `[lo, hi)`;
                   abutting supports are one set). No `min_lambda`, no producer-side threshold,
                   no clipping. A long residence span that blows the false-positive budget is an
                   honest outcome — fixed by a rule_version ruling, never by narrowing.
  peak_instant     the EARLIEST instant of the maximum (plateau tie rule); NULL when the window
                   has no qualified record (no score ⇒ no peak).
  score            max over the window's admitted records of the within-path factor product in
                   the for-channel at the peak, ∈ [0,1]; NULL (never 0) when no member record is
                   qualified.
  evidence_for / _against
                   per-channel Σ over roots of the per-root max at the peak instant, never netted;
                   NULL when the window is unqualified. P3/P4 records are class-signature
                   activations: every one lands in the FOR channel (no against-direction operand
                   exists in either path), so `evidence_against` is the genuine, evaluated 0.0 of
                   an empty sum on a qualified window and NULL on an unqualified one.
  valence          `valence.compute_valence` at the peak; 'unqualified' when the window is.
  severity         NULL — a named null: no cited severity rule exists; never 0.

Factor operands are read FROM THE FACTOR ROW, never hard-coded (ruling 3). A row that declares an
`applicability` block (activity_kernel@1.1.0 — span ⇒ membership step, point ⇒ angular with the
row's `orb_deg`) lights up from the row alone; a row without one (activity_kernel@1.0.0) leaves
every record's operand unevaluable, hence `unqualified` — exactly what is stored. A point orb that
the row does not carry (ND-ORB open) is `unqualified (orb_not_ratified)`: a caller-supplied number
is never accepted in its place.

Admission (§2.3 inv 3): only `admitted` records with operator_role `scored` and a computed support
form a window. A `not_admitted` record is pruned by a false necessary predicate; an `unqualified`
admission (unknown prerequisite) is not an admitted record, so it forms no window — it stays in the
record table and in the coverage counts; testimony rows never carry weight (§1.2 inv 2).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable

UNQUALIFIED = "unqualified"
OMIT = "omit"
CHANNEL_FOR = "evidence_for_occurrence"
CHANNEL_AGAINST = "evidence_against_occurrence"

# P3/P4: every record is a contact of an agent with the class's signature house / lord — an
# activation of the class, so evidence FOR it (Stream B, WINDOW_SWEEP_ANSWER (1)). A path with
# no entry here has no window sweep yet (P2/P1 are later increments) and refuses loudly.
PATH_CHANNEL: dict[str, str] = {"P3": CHANNEL_FOR, "P4": CHANNEL_FOR}

# Span-kind and angular-kind object kinds are NOT enumerated here: the factor row's own
# applicability block lists them (activity_kernel@1.1.0). Nothing below names a kind.

_EPS = 1e-12
# Two members' maxima that differ by less than the maximiser's own resolution (1 s on a 5° orb is
# ~1e-6 of kernel value) are one plateau: the earliest instant wins, not whichever search landed
# a hair higher.
_TIE = 1e-6


class SweepRefusal(RuntimeError):
    """The sweep cannot honestly evaluate this input (named, never a silent default)."""


@dataclass(frozen=True)
class SweepRecord:
    record_id: str
    root_id: str                       # contact_id on transit rows (§2.1 amendment 2)
    path_id: str
    rule_version: str
    relation: str
    object_kind: str
    agent: str
    operator_role: str
    admission_state: str
    supports: tuple                    # ((lo, hi), ...) aware UTC datetimes, half-open
    # Point-kernel / drishti operand sources, supplied by the store ONLY when it has them. A
    # callable returning None means "not determinable at t" (a named missing operand).
    delta_lambda_at: Callable[[datetime], float | None] | None = None
    aspect_offset_at: Callable[[datetime], int | None] | None = None


# ── factor outcomes ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Outcome:
    """What one factor says about one record. Exactly one of: not applicable (factor takes no part
    in the product), a constant, a function of t, or a missing operand (takes the row's null_state)."""
    kind: str                           # 'na' | 'const' | 'fn' | 'missing'
    value: float | None = None
    fn: Callable[[datetime], float | None] | None = None
    null_state: str | None = None
    reason: str | None = None
    factor: str | None = None


def _check_unit(value, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) \
            or not (0.0 <= float(value) <= 1.0):
        raise SweepRefusal(f"{what}: factor value {value!r} outside the declared [0,1] range (§2.1)")
    return float(value)


def _missing(row: dict, reason: str) -> Outcome:
    return Outcome("missing", null_state=row["null_state"], reason=reason, factor=row["factor_id"])


def activity_kernel(row: dict, rec: SweepRecord) -> Outcome:
    """Reads the ROW. `applicability` absent ⇒ the operand is not evaluable (unqualified)."""
    ap = row.get("applicability")
    if not ap:
        return _missing(row, "applicability_undeclared")
    span, angular = ap.get("span") or {}, ap.get("angular") or {}
    if rec.object_kind in (span.get("object_kinds") or ()):
        # A support interval IS the membership: every instant the sweep evaluates is inside it.
        return Outcome("const", value=_check_unit(span.get("inside"), "activity_kernel span.inside"),
                       factor=row["factor_id"])
    if rec.object_kind in (angular.get("object_kinds") or ()):
        orb = angular.get("orb_deg")
        if orb is None:
            return _missing(row, "orb_not_ratified")
        if not (isinstance(orb, (int, float)) and not isinstance(orb, bool) and orb > 0
                and math.isfinite(orb)):
            raise SweepRefusal(f"activity_kernel angular.orb_deg {orb!r} is not a positive finite number")
        if rec.delta_lambda_at is None:
            return _missing(row, "delta_lambda_operand_missing")
        dl = rec.delta_lambda_at

        def _fn(t: datetime, _dl=dl, _orb=float(orb)):
            d = _dl(t)
            if d is None:
                return None
            return max(0.0, 1.0 - abs(float(d)) / _orb)

        return Outcome("fn", fn=_fn, null_state=row["null_state"], factor=row["factor_id"])
    return _missing(row, "object_kind_not_covered_by_applicability")


def graduated_drishti(row: dict, rec: SweepRecord,
                      drishti: Callable[[str, int], float] | None) -> Outcome:
    """Aspect records only. The table is Stream B's (`services/gochara_rules/drishti.py`) and is
    CALLED through `drishti`, never copied; until it is supplied the operand is a named missing
    input."""
    ap = row.get("applicability")
    if ap and rec.relation not in (ap.get("relations") or ()):
        return Outcome("na", factor=row["factor_id"], reason="not_applicable_to_relation")
    if not ap:
        return _missing(row, "applicability_undeclared")
    if drishti is None:
        return _missing(row, "graduated_drishti_source_not_landed")
    if rec.aspect_offset_at is None:
        return _missing(row, "aspect_offset_operand_missing")
    off_at = rec.aspect_offset_at

    def _fn(t: datetime, _o=off_at, _a=rec.agent):
        off = _o(t)
        return None if off is None else _check_unit(drishti(_a, off), "graduated_drishti")

    return Outcome("fn", fn=_fn, null_state=row["null_state"], factor=row["factor_id"])


def evaluate_factors(rec: SweepRecord, factor_rows: list[dict], *,
                     drishti: Callable[[str, int], float] | None = None) -> list[Outcome]:
    """One outcome per declared soft factor. A factor the sweep has no evaluator for REFUSES (a
    later increment's path must not be silently scored without it)."""
    out: list[Outcome] = []
    for row in factor_rows:
        fid = row["factor_id"]
        if fid == "activity_kernel":
            out.append(activity_kernel(row, rec))
        elif fid == "graduated_drishti":
            out.append(graduated_drishti(row, rec, drishti))
        else:
            raise SweepRefusal(
                f"path {rec.path_id}: factor {fid!r} has no sweep evaluator yet "
                "(P2/P1 are later increments) — refused, never skipped")
    return out


# ── per-record program ───────────────────────────────────────────────────────

@dataclass
class RecordProgram:
    rec: SweepRecord
    qualified: bool
    null_states: set
    reasons: list                       # [(factor_id, reason)] of every missing operand
    outcomes: list = field(default_factory=list)

    def value_at(self, t: datetime) -> float | None:
        """The within-path product at t; None if any live operand is undeterminable at t."""
        product = 1.0
        for o in self.outcomes:
            if o.kind == "na":
                continue
            if o.kind == "missing":
                if o.null_state == OMIT:
                    continue
                return None
            v = o.value if o.kind == "const" else o.fn(t)
            if v is None:
                return None
            product *= _check_unit(v, f"{o.factor}@{t.isoformat()}")
        return product

    @property
    def constant(self) -> float | None:
        """The record's value when every live factor is constant (a plain step product)."""
        product = 1.0
        for o in self.outcomes:
            if o.kind == "na" or (o.kind == "missing" and o.null_state == OMIT):
                continue
            if o.kind != "const":
                return None
            product *= o.value
        return product


def build_program(rec: SweepRecord, factor_rows: list[dict], *,
                  drishti: Callable[[str, int], float] | None = None) -> RecordProgram:
    outcomes = evaluate_factors(rec, factor_rows, drishti=drishti)
    null_states: set = set()
    reasons: list = []
    qualified = True
    for o in outcomes:
        if o.kind == "missing":
            null_states.add(o.null_state)
            reasons.append((o.factor, o.reason))
            if o.null_state == UNQUALIFIED:
                qualified = False
    return RecordProgram(rec=rec, qualified=qualified, null_states=null_states,
                         reasons=reasons, outcomes=outcomes)


# ── maximisation (interior extrema, never endpoint-only — §7.2 inv 2, O-SM-4) ─

def maximise_earliest(f: Callable[[datetime], float | None], lo: datetime, hi: datetime, *,
                      samples: int = 64, tol_seconds: float = 1.0) -> tuple[float, datetime] | None:
    """(max value, earliest instant achieving it) of `f` over `[lo, hi)`; None when `f` is
    undeterminable everywhere. Bracketed scan, then golden-section refinement of the best
    bracket — an interior maximum is found even when both endpoints are lower."""
    span = (hi - lo).total_seconds()
    if span <= 0:
        raise SweepRefusal("empty support piece")
    pts = [lo + timedelta(seconds=span * k / samples) for k in range(samples)]
    vals = [f(p) for p in pts]
    live = [i for i, v in enumerate(vals) if v is not None]
    if not live:
        return None
    best = max(vals[i] for i in live)
    i0 = min(i for i in live if vals[i] >= best - _EPS)
    lo_b = pts[max(i0 - 1, 0)]
    hi_b = pts[min(i0 + 1, samples - 1)] if i0 + 1 < samples else hi - timedelta(microseconds=1)
    best_t, best_v = pts[i0], vals[i0]
    # golden-section on [lo_b, hi_b]
    phi = (math.sqrt(5) - 1) / 2
    a, b = lo_b, hi_b
    c = b - timedelta(seconds=(b - a).total_seconds() * phi)
    d = a + timedelta(seconds=(b - a).total_seconds() * phi)
    fc, fd = f(c), f(d)
    while (b - a).total_seconds() > tol_seconds:
        if fd is None or (fc is not None and fc >= fd):
            b, d, fd = d, c, fc
            c = b - timedelta(seconds=(b - a).total_seconds() * phi)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + timedelta(seconds=(b - a).total_seconds() * phi)
            fd = f(d)
    mid = a + (b - a) / 2
    fm = f(mid)
    if fm is not None and fm > best_v + _EPS and lo <= mid < hi:
        best_t, best_v = mid, fm
    return best_v, best_t


# ── window formation ─────────────────────────────────────────────────────────

def union_components(pieces: Iterable[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Maximal connected unions of half-open intervals; abutting `[a,b)`,`[b,c)` are one set."""
    ordered = sorted(pieces)
    out: list[list[datetime]] = []
    for lo, hi in ordered:
        if hi <= lo:
            raise SweepRefusal(f"empty or inverted support piece [{lo}, {hi})")
        if out and lo <= out[-1][1]:
            if hi > out[-1][1]:
                out[-1][1] = hi
        else:
            out.append([lo, hi])
    return [(a, b) for a, b in out]


@dataclass
class WindowDraft:
    interval: tuple
    peak_instant: datetime | None
    score: float | None
    evidence_for: float | None
    evidence_against: float | None
    outcome_valence_for_native: str
    severity: float | None
    record_ids: tuple
    null_states_used: list
    unresolved: dict                    # reason -> count of member records
    members: int
    qualified_members: int


def _contains(supports, t: datetime) -> bool:
    return any(lo <= t < hi for lo, hi in supports)


def draft_windows(event_class: str, records: list[SweepRecord],
                  factor_rows_for: Callable[[str, str], list[dict]], *,
                  drishti: Callable[[str, int], float] | None = None,
                  compute_valence: Callable | None = None) -> tuple[list[WindowDraft], dict]:
    """The grain's windows (one path-version) and an exclusion ledger. Every record is accounted:
    admitted members, plus each excluded one under a named reason."""
    from services.gochara_rules import valence as _valence_mod
    valence_fn = compute_valence or _valence_mod.compute_valence

    excluded = {"not_admitted": 0, "admission_unqualified": 0, "testimony": 0, "no_support": 0}
    members: list[SweepRecord] = []
    keys = {(r.path_id, r.rule_version) for r in records}
    if len(keys) > 1:
        raise SweepRefusal(f"a window grain is one path-version; got {sorted(keys)}")
    for r in records:
        if r.path_id not in PATH_CHANNEL:
            raise SweepRefusal(f"path {r.path_id} has no window sweep yet")
        if r.operator_role != "scored":
            excluded["testimony"] += 1
        elif r.admission_state == "not_admitted":
            excluded["not_admitted"] += 1
        elif r.admission_state != "admitted":
            excluded["admission_unqualified"] += 1
        elif not r.supports:
            excluded["no_support"] += 1
        else:
            members.append(r)
    if not members:
        return [], excluded

    path_id, version = next(iter(keys))
    factor_rows = factor_rows_for(path_id, version)
    programs = {r.record_id: build_program(r, factor_rows, drishti=drishti) for r in members}

    components = union_components(p for r in members for p in r.supports)
    drafts: list[WindowDraft] = []
    for lo, hi in components:
        in_win = [r for r in members if any(lo <= a and b <= hi for a, b in r.supports)]
        if not in_win:
            raise SweepRefusal("component without a member record — union invariant violated")
        progs = [programs[r.record_id] for r in in_win]
        candidates: list[tuple[float, datetime]] = []
        for prog in progs:
            if not prog.qualified:
                continue
            for a, b in prog.rec.supports:
                if not (lo <= a and b <= hi):
                    continue
                const = prog.constant
                if const is not None:
                    candidates.append((const, a))
                else:
                    got = maximise_earliest(prog.value_at, a, b)
                    if got is not None:
                        candidates.append(got)
        unresolved: dict = {}
        null_states: set = set()
        for prog in progs:
            null_states |= prog.null_states
            for reason in {r for _f, r in prog.reasons}:     # records per reason, not factor-misses
                unresolved[reason] = unresolved.get(reason, 0) + 1
        if candidates:
            best = max(v for v, _ in candidates)
            peak = min(t for v, t in candidates if v >= best - _TIE)
            # evidence at the peak: Σ over roots of the per-root max over records live at the peak
            per_root: dict[str, float] = {}
            for prog in progs:
                if not prog.qualified or not _contains(prog.rec.supports, peak):
                    continue
                v = prog.value_at(peak)
                if v is None:
                    continue
                per_root[prog.rec.root_id] = max(per_root.get(prog.rec.root_id, 0.0), v)
            ev_for = sum(per_root.values())
            ev_against = 0.0
            val = valence_fn(event_class, ev_for, ev_against, None)
            drafts.append(WindowDraft(
                interval=(lo, hi), peak_instant=peak, score=best, evidence_for=ev_for,
                evidence_against=ev_against, outcome_valence_for_native=val.outcome_valence_for_native,
                severity=None, record_ids=tuple(sorted(r.record_id for r in in_win)),
                null_states_used=sorted(null_states), unresolved=unresolved,
                members=len(in_win), qualified_members=sum(1 for p in progs if p.qualified)))
        else:
            first = sorted(unresolved)[0] if unresolved else "no_qualified_member"
            val = valence_fn(event_class, 0.0, 0.0, first)
            drafts.append(WindowDraft(
                interval=(lo, hi), peak_instant=None, score=None, evidence_for=None,
                evidence_against=None, outcome_valence_for_native=val.outcome_valence_for_native,
                severity=None, record_ids=tuple(sorted(r.record_id for r in in_win)),
                null_states_used=sorted(null_states), unresolved=unresolved,
                members=len(in_win), qualified_members=0))
    return drafts, excluded


def registry_factor_rows(path_id: str, rule_version: str) -> list[dict]:
    """The path-version's declared soft-factor rows, from the registry the path is sealed against
    (the path→version map comes from the RECORDS' own `rule_version`, never a global constant)."""
    from services.gochara_rules import registry as _reg
    path = _reg.RULE_PATHS[_reg.composite_ref(path_id, rule_version)]
    return [_reg.FACTORS[ref] for ref in path["soft_factors"]]


def utc(t: datetime) -> datetime:
    if t.tzinfo is None:
        raise SweepRefusal("naive datetime refused (UTC aware only)")
    return t.astimezone(timezone.utc)


__all__ = [
    "CHANNEL_AGAINST", "CHANNEL_FOR", "Outcome", "PATH_CHANNEL", "RecordProgram", "SweepRecord",
    "SweepRefusal", "WindowDraft", "activity_kernel", "build_program", "draft_windows",
    "evaluate_factors", "graduated_drishti", "maximise_earliest", "registry_factor_rows",
    "union_components",
]
