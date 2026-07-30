"""
services/ka_kshetra/stage4_field.py — §5.2–§5.4 stage 4: field assembly,
segment construction, and the provenance edges (item 11).

Stage 4 is where the pipeline's separately-computed pieces become ONE object:
Lane A's kinematics/primitives/promise graph, Lane B's clocks/boundaries, the
pinned weights version, and the classical class priors compose into λ_e(t), which
is then STORED as log-linear segments (integrator.py) with every multiplicative
factor persisted as a provenance edge that must reconstruct the value it
explains.

── CIRCULARITY GUARD (§8.3, a HARD campaign gate — peer of LAW ZERO) ─────────
NOTHING on the stage 0–8 code path may read the life-event corpus. This module
issues no query against it and calls no capability that does. That is asserted
MECHANICALLY, by a textual census over every `services/ka_*` source file
(`tests/l3/test_ka_jivana_parva_circularity_guard.py`) and again,
ka_kshetra-specifically, by `tests/l3/ka_kshetra/test_circularity_guard.py`.

NOTE FOR ANYONE EDITING THIS DOCSTRING: the census is a plain token scan, so the
forbidden table/capability identifiers may not be written out even in a comment.
That is deliberate and it is the cheapest possible property to keep true — a
guard that had to parse imports would have blind spots a string scan does not.

The invariant CG-1 is stated over the field CONTENT hash: for any mutation of a
chart's lived-history corpus that leaves (corpus_pin, config_pin,
weights_version, cohort_version) unchanged, the hash is bit-identical before and
after. Stage 9 — and only stage 9 — may see lived outcomes.

── §N.5: L1/L3 ARE THE AUTHORITY ────────────────────────────────────────────
No table this module writes ever RESTATES a computed value owned by L1
(`chart_facts`, `chart_dashas`, `chart_positions`) or by the existing L3 writers
(`kala_gochara_windows`, `gochara_resonance_map`). Every dependent row stores a
REFERENCE — (source_table, source_pk, source_fact_id) — and inherits the value at
read time. The legacy sweep in particular is read as a CROSS-CHECK CORPUS only:
its `signed_intensity` is never copied into a field column, and W2 writes ZERO
rows to any legacy table (§1 rail 2, strangler-fig).

── WHY THE EVALUATOR IS A PURE, INJECTABLE OBJECT ───────────────────────────
`FieldEvaluator` holds no connection. Everything it needs is loaded ONCE per
(chart × event class) and then evaluated in memory. Two things depend on that:
  • the stage-5 null re-runs the SAME evaluator 256 times over circularly
    shifted envelopes; a DB round-trip per instant would make the null
    unaffordable and would tempt someone to approximate it, which would make
    every published p-value a different statistic from the documented one;
  • the whole thing is unit-testable without Postgres, so the numerics have real
    tests rather than integration-only smoke.

── LANE BOUNDARIES (§0 anti-collision contract) ─────────────────────────────
This module reads Lane A's and Lane B's TABLES and calls their published
FUNCTION SIGNATURES; it never reads their code. Where a lane's module has not
landed yet, the loaders fall back to the lane's table with the DESIGN
DOCUMENT's own stated aggregation (e.g. §3.3's noisy-OR over `kala_field_routes`)
and record which path was taken — never a silent guess.

Authority: KALA_W2_FIELD_DESIGN_v1_0.md §5.1–§5.4, §7.4, §8.3, §9.4.
"""
from __future__ import annotations

import bisect
import hashlib
import json
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Optional, Sequence

from services.ka_kshetra import hazard, integrator
from services.ka_kshetra.contracts import (
    ClockApplicability,
    PromisePrior,
    ProvenanceEdge,
    Route,
    Segment,
)

logger = logging.getLogger(__name__)

#: §5.2's horizon: birth → birth + 100 Julian years, matching the existing sweep
#: horizon so field windows and legacy sweep windows are directly comparable.
HORIZON_DAYS: float = 36525.0

#: §5.4's reconciliation tolerance, in NATS (log space). 1e-9 is ~30 orders of
#: magnitude above float64 noise for these summands, so a failure is a real
#: modelling defect, never a rounding artefact.
RECONCILIATION_TOLERANCE: float = 1e-9

#: Outermost-first ordering of the daśā ladder levels (§4.2's level vocabulary).
LEVEL_ORDER: tuple[str, ...] = ('MD', 'AD', 'PD', 'SD', 'PrD')
_LEVEL_RANK: dict[str, int] = {lvl: i for i, lvl in enumerate(LEVEL_ORDER)}

#: stage-1 `primitive_kind` → the frozen covariate key it feeds (§5.1 C-5).
#: `moorti_at_ingress` is resolved through its `class_label` (svarṇa/rajata/tāmra;
#: LOHA IS THE REFERENCE LEVEL AND GETS NO DUMMY — a fourth dummy would make the
#: design matrix rank-deficient and the fitted β's unidentifiable).
PRIMITIVE_TO_COVARIATE: dict[str, str] = {
    'contact_moon_ref': 'contact_moon_ref',
    'contact_lagna_ref': 'contact_lagna_ref',
    'av_kaksha_gate': 'av_kaksha_gate',
    'station_band': 'station_band',
    'sandhi_band': 'sandhi_band',
    'syzygy_band': 'syzygy_band',
    'panchanga_limb': 'panchanga_affinity',
}

MOORTI_TO_COVARIATE: dict[str, str] = {
    'svarna': 'moorti_svarna',
    'rajata': 'moorti_rajata',
    'tamra': 'moorti_tamra',
    # 'loha' deliberately absent — the reference level.
}

#: A `syzygy_band` primitive carrying this class_label also feeds x11
#: (`eclipse_contact` = syzygy_band × eclipse_candidate, §5.1 C-5 row 11).
ECLIPSE_CANDIDATE_LABEL: str = 'eclipse_candidate'


# ── errors ───────────────────────────────────────────────────────────────────

class ProvenanceReconciliationError(RuntimeError):
    """§5.4's halting failure. Raised inside the substep so the orchestrator
    rolls the savepoint back: a field row whose provenance does not reconstruct
    it must never reach a reader."""


class ClassSkipped(Exception):
    """An event class that cannot be built HONESTLY, with the reason.

    Not an error condition to be swallowed: the reason is recorded on
    `kala_field_snapshots.skipped_classes` so a reader sees WHY a class has no
    windows rather than inferring the chart has no hazard for it (LAW ZERO).
    """

    def __init__(self, event_class: str, reason: str, detail: str = ''):
        super().__init__(f'{event_class}: {reason} {detail}'.strip())
        self.event_class = event_class
        self.reason = reason
        self.detail = detail


class UpstreamStageIncomplete(RuntimeError):
    """Raised by a substep whose upstream stage has not committed its rows.

    §8.1's mandated defensive check. Computing on partial upstream data would
    produce a field that is silently wrong rather than visibly absent.
    """


# ── canonical serialization (§7.4) ───────────────────────────────────────────

def _canonical(value: Any) -> Any:
    """Recursively canonicalize for hashing.

    Floats become their `repr` STRING (Python's repr is the shortest round-trip-
    exact decimal, ≤17 significant digits), so the hash is identical across
    platforms and across a dump/restore that might re-render a float. §7.4
    requires exactly this property.
    """
    if isinstance(value, float):
        if math.isnan(value):
            return 'nan'
        return repr(value)
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    """Deterministic JSON: keys sorted, no incidental whitespace, floats as
    round-trip-exact reprs."""
    return json.dumps(_canonical(value), sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, default=str)


@dataclass(frozen=True)
class FieldPins:
    """The PIN IDENTITY of one field build (see migration 492's header for why
    there are two snapshot identities and which one CG-1 is stated over).

    Every one of these is an input to `field_snapshot_id`, so a build under
    different weights, a different corpus, a different config or a different
    cohort is a DIFFERENT snapshot — never a silent overwrite of the previous one.
    """
    chart_id: str
    corpus_pin: str
    weights_version: str
    x_schema_version: str
    config_pin: Mapping[str, Any]
    cohort_version: Optional[str] = None

    @property
    def field_snapshot_id(self) -> str:
        payload = canonical_json({
            'chart_id': self.chart_id,
            'corpus_pin': self.corpus_pin,
            'weights_version': self.weights_version,
            'x_schema_version': self.x_schema_version,
            'cohort_version': self.cohort_version,
            'config_pin': dict(self.config_pin),
        })
        return 'kfs_' + hashlib.sha256(payload.encode('utf-8')).hexdigest()[:32]


def field_content_hash(
    pin_identity: str,
    rows: Iterable[tuple[str, tuple, Mapping[str, Any]]],
) -> str:
    """§7.4's FULL hash: the pin identity plus a canonical serialization of every
    stage 0–8 row, sorted by (table_name, natural key).

    `rows` yields (table_name, natural_key_tuple, payload) with the volatile
    columns (`id`, `computed_at`, `created_at`, `released_at`) ALREADY EXCLUDED by
    the caller — including them would make two identical builds hash differently
    and turn hash-replay into a permanently-red gate.

    Sorting by the natural key (not by insertion order) is what makes the hash
    independent of substep dispatch order, which the design requires because the
    orchestrator may dispatch a plan's substeps in any order.

    THIS is the value the hash-replay CI compares and the value CIRCULARITY GUARD
    CG-1 is stated over. Comparing the pin identity alone would be a claim with no
    detector behind it (§N.8).
    """
    entries = sorted(
        (table, canonical_json(list(key)), canonical_json(dict(payload)))
        for table, key, payload in rows
    )
    digest = hashlib.sha256()
    digest.update(pin_identity.encode('utf-8'))
    for table, key_json, payload_json in entries:
        digest.update(b'\x1e')
        digest.update(table.encode('utf-8'))
        digest.update(b'\x1f')
        digest.update(key_json.encode('utf-8'))
        digest.update(b'\x1f')
        digest.update(payload_json.encode('utf-8'))
    return 'kfh_' + digest.hexdigest()[:32]


# ── stage-1 primitives and their envelopes ───────────────────────────────────

@dataclass(frozen=True)
class Primitive:
    """One `kala_field_primitives` row: an interval with a piecewise-LINEAR
    strength envelope.

    The envelope contract is FROZEN by §3.2 and stage 4 depends on it: ≥2 knots,
    `t` strictly ascending (coincident knots are permitted precisely to make a
    STEP explicit), `v ∈ [0,1]`, linear between knots, and ZERO outside the span.
    Piecewise-linearity is not a convenience — it is what makes the log-linear
    segment representation FAITHFUL rather than merely close, because a
    breakpoint is placed at every knot.
    """
    primitive_kind: str
    subject: str
    object_ref: Optional[str]
    polarity: str
    class_label: Optional[str]
    knots: tuple[tuple[float, float], ...]
    source_pk: Optional[str] = None
    source_fact_id: Optional[str] = None
    source_table: Optional[str] = None

    @property
    def t_start(self) -> float:
        return self.knots[0][0]

    @property
    def t_end(self) -> float:
        return self.knots[-1][0]

    def value_at(self, t: float) -> float:
        if len(self.knots) < 2:
            raise ValueError(
                f'{self.primitive_kind}:{self.subject} envelope has '
                f'{len(self.knots)} knot(s); the frozen §3.2 contract requires ≥2. '
                'A one-knot envelope has no defined value anywhere and would read '
                'as an honest 0 for the entire horizon.'
            )
        ts = [k[0] for k in self.knots]
        if t < ts[0] or t > ts[-1]:
            return 0.0
        i = bisect.bisect_right(ts, t) - 1
        if i >= len(self.knots) - 1:
            return self.knots[-1][1]
        t0, v0 = self.knots[i]
        t1, v1 = self.knots[i + 1]
        if t1 == t0:
            # Coincident knots: the STEP's right-hand value wins, matching
            # integrator.lambda_at's right-hand-limit convention.
            return v1
        return v0 + (v1 - v0) * ((t - t0) / (t1 - t0))

    def vighna_key(self) -> str:
        """`vedha:Sa->10` — CLASS:instance. `hazard._rho_weight_id` splits on the
        first ':' to find the fitted ρ, so the class must lead."""
        return (f'{self.primitive_kind}:{self.subject}->{self.object_ref}'
                if self.object_ref else f'{self.primitive_kind}:{self.subject}')


class EnvelopeIndex:
    """The in-memory stage-1 envelope index, and the ONE place the circular
    shift is applied (§5.5).

    Splitting supportive covariates from obstructive vighna at construction time
    is deliberate: it makes it structurally impossible for an obstruction to leak
    into the log-linear modifier term M_e (where it would ADD, i.e. subtract from
    λ) instead of the multiplicative thinning term S_e (where it THINS). The
    Elevation §3 stage-4 amendment exists because that leak is easy to write and
    invisible once written.
    """

    def __init__(self, primitives: Sequence[Primitive], horizon_days: float):
        self.horizon_days = float(horizon_days)
        self.supportive: list[Primitive] = []
        self.obstructive: list[Primitive] = []
        for p in primitives:
            (self.obstructive if p.polarity == 'obstructive' else self.supportive).append(p)

    # ── evaluation ───────────────────────────────────────────────────────────

    def covariates_at(self, t: float) -> dict[str, float]:
        """The ACTIVE entries of the twelve-covariate vector at t.

        Aggregation is MAX over same-kind primitives (§5.1 C-5 row 1: "max
        envelope over active Moon-referenced contacts"). Sum would let two weak
        simultaneous contacts masquerade as one strong one; max keeps the
        covariate on its declared [0,1] scale.

        Only non-zero entries are returned. An absent key is an honest zero, and
        `hazard.modifier_log_term` reads a missing key as exactly 0 — so an
        inactive covariate contributes nothing and emits a zero-valued (still
        present, still auditable) provenance edge.
        """
        out: dict[str, float] = {}
        for p in self.supportive:
            v = p.value_at(t)
            if v <= 0.0:
                continue
            for key in self._covariate_keys(p):
                if v > out.get(key, 0.0):
                    out[key] = v
        return out

    @staticmethod
    def _covariate_keys(p: Primitive) -> tuple[str, ...]:
        if p.primitive_kind == 'moorti_at_ingress':
            key = MOORTI_TO_COVARIATE.get((p.class_label or '').lower())
            return (key,) if key else ()
        key = PRIMITIVE_TO_COVARIATE.get(p.primitive_kind)
        if key is None:
            return ()
        if p.primitive_kind == 'syzygy_band' and p.class_label == ECLIPSE_CANDIDATE_LABEL:
            # x11 = syzygy_band × eclipse_candidate. A non-eclipse syzygy
            # contributes x11 = 0 by simply not appearing here.
            return (key, 'eclipse_contact')
        return (key,)

    def obstructions_at(self, t: float) -> dict[str, float]:
        """Active vighna envelopes u_m(t) ∈ (0, 1], keyed CLASS:instance.

        Inactive obstructors are ABSENT rather than present-with-zero: a u = 0
        entry contributes ln(1) = 0 to the hazard (harmless) but would emit a
        provenance edge asserting an obstruction that was not active (not
        harmless — a reader would see a reason that is not a reason).
        """
        out: dict[str, float] = {}
        for p in self.obstructive:
            v = p.value_at(t)
            if v <= 0.0:
                continue
            key = p.vighna_key()
            if v > out.get(key, 0.0):
                out[key] = v
        return out

    def breakpoints(self) -> list[float]:
        """Every envelope knot. Placing a breakpoint at each is what makes the
        stored log-linear field FAITHFUL to the piecewise-linear covariates
        rather than an approximation of them."""
        return sorted({k[0] for p in self.supportive + self.obstructive for k in p.knots})

    def obstruction_sources(self) -> dict[str, Primitive]:
        return {p.vighna_key(): p for p in self.obstructive}

    # ── §5.5 the circular shift ──────────────────────────────────────────────

    def circular_shift(self, delta: float) -> 'EnvelopeIndex':
        """Rebuild the index with every primitive's knots translated by −δ and
        wrapped into [0, H), i.e. x^{(r)}(t) = x((t + δ) mod H).

        A primitive whose translated span straddles the wrap point is SPLIT into
        two pieces with the crossing value interpolated, so no signal is created
        or destroyed. That conservation is not cosmetic: if a shift could weaken
        the sky, every replicate would be a slightly easier opponent and every
        published p-value would be optimistic — the null would flatter the model
        it is supposed to falsify.

        Only stage-1 envelopes move. Clock terms C_e, promise P̃_e, the baseline
        λ⁰_e and all weights are UNCHANGED (§5.5) — that asymmetry IS the null
        hypothesis.
        """
        H = self.horizon_days
        delta = float(delta) % H if H > 0 else 0.0
        if delta == 0.0:
            return EnvelopeIndex(self.supportive + self.obstructive, H)
        out: list[Primitive] = []
        for p in self.supportive + self.obstructive:
            out.extend(_shift_primitive(p, delta, H))
        return EnvelopeIndex(out, H)


def _shift_primitive(p: Primitive, delta: float, H: float) -> list[Primitive]:
    """Translate one primitive's knots by −δ, wrapping into [0, H)."""
    knots = [(t - delta, v) for t, v in p.knots]
    shift_k = -math.floor(knots[0][0] / H) * H
    knots = [(t + shift_k, v) for t, v in knots]

    if knots[-1][0] <= H:
        return [_with_knots(p, knots)]

    # Straddles the wrap: interpolate the crossing value and emit two pieces.
    cross_v = _interp(knots, H)
    head = [(t, v) for t, v in knots if t < H] + [(H, cross_v)]
    tail = [(0.0, cross_v)] + [(t - H, v) for t, v in knots if t > H]
    pieces = []
    if len(head) >= 2:
        pieces.append(_with_knots(p, head))
    if len(tail) >= 2:
        pieces.append(_with_knots(p, tail))
    return pieces


def _with_knots(p: Primitive, knots: Sequence[tuple[float, float]]) -> Primitive:
    return Primitive(
        primitive_kind=p.primitive_kind, subject=p.subject, object_ref=p.object_ref,
        polarity=p.polarity, class_label=p.class_label,
        knots=tuple((float(t), float(v)) for t, v in knots),
        source_pk=p.source_pk, source_fact_id=p.source_fact_id, source_table=p.source_table,
    )


def _interp(knots: Sequence[tuple[float, float]], t: float) -> float:
    ts = [k[0] for k in knots]
    if t <= ts[0]:
        return knots[0][1]
    if t >= ts[-1]:
        return knots[-1][1]
    i = bisect.bisect_right(ts, t) - 1
    t0, v0 = knots[i]
    t1, v1 = knots[i + 1]
    if t1 == t0:
        return v1
    return v0 + (v1 - v0) * ((t - t0) / (t1 - t0))


# ── the daśā ladder ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LadderPeriod:
    """One precision-SUPPORTED period from Lane B's `kala_field_boundaries`.

    Rule C-5: a level whose `precision_state = 'precision_unsupported'` is never
    loaded, so it simply does not appear in the running lord stack and its d_ℓ
    term is ABSENT. That is the operational form of "no claim is ever served at a
    precision the input uncertainty cannot support" — the level does not get a
    down-weighted vote, it gets no vote.
    """
    system_id: str
    level: str
    lord: str
    t_start: float
    t_end: float


class FieldEvaluator:
    """λ_e(t) for ONE (chart × event class), evaluable at any instant.

    Holds no connection: everything is loaded once and evaluated in memory. See
    the module docstring for why that is load-bearing rather than a style choice.
    """

    def __init__(
        self,
        *,
        event_class: str,
        lifetime_count: float,
        promise: PromisePrior,
        clocks: Sequence[ClockApplicability],
        ladder: Mapping[str, Sequence[LadderPeriod]],
        envelopes: EnvelopeIndex,
        weights: Mapping[str, float],
        horizon_days: float = HORIZON_DAYS,
        baseline_source: Optional[tuple[str, str, str]] = None,
        extra_breakpoints: Sequence[float] = (),
    ):
        self.event_class = event_class
        self.lifetime_count = float(lifetime_count)
        self.promise = promise
        self.clocks = list(clocks)
        self.ladder = {
            sid: sorted(periods, key=lambda p: (_LEVEL_RANK.get(p.level, 99), p.t_start))
            for sid, periods in ladder.items()
        }
        self.envelopes = envelopes
        self.weights = dict(weights)
        self.horizon_days = float(horizon_days)
        self.baseline_source = baseline_source
        self.extra_breakpoints = tuple(float(t) for t in extra_breakpoints)

    # ── inputs at an instant ─────────────────────────────────────────────────

    def lord_stacks_at(self, t: float) -> dict[str, list[tuple[str, str]]]:
        """The running (level, lord) stack per system at t, OUTERMOST FIRST.

        Half-open containment `[t_start, t_end)` so a boundary instant belongs to
        exactly one period — the same discipline §6.3's cohort MD-chain join
        uses, and for the same reason: a closed interval double-counts the
        boundary and an open one drops it.
        """
        out: dict[str, list[tuple[str, str]]] = {}
        for sid, periods in self.ladder.items():
            stack = [(p.level, p.lord) for p in periods if p.t_start <= t < p.t_end]
            if stack:
                out[sid] = stack
        return out

    def terms_at(self, t: float) -> hazard.HazardTerms:
        """The full §5.1 decomposition at t, including its provenance edges."""
        return hazard.evaluate(
            lifetime_count=self.lifetime_count,
            promise=self.promise,
            clocks=self.clocks,
            lord_stacks=self.lord_stacks_at(t),
            covariates=self.envelopes.covariates_at(t),
            obstructions=self.envelopes.obstructions_at(t),
            weights=self.weights,
            baseline_source=self.baseline_source,
        )

    def ln_lambda(self, t: float) -> float:
        return self.terms_at(t).ln_lambda

    # ── breakpoints + segments ───────────────────────────────────────────────

    def breakpoints(self) -> list[float]:
        """§5.2's breakpoint set B_e, clipped to [0, H].

        The union of: every stage-0 kinematics root (passed in as
        `extra_breakpoints`), every stage-1 envelope knot, every
        precision-supported daśā boundary, and the horizon ends. λ is smooth
        between these and kinked at them, so refining anywhere else buys nothing
        and refining nowhere else misses every real kink.
        """
        pts = {0.0, self.horizon_days}
        pts.update(self.envelopes.breakpoints())
        for periods in self.ladder.values():
            for p in periods:
                pts.add(p.t_start)
                pts.add(p.t_end)
        pts.update(self.extra_breakpoints)
        return sorted(t for t in pts if math.isfinite(t) and 0.0 <= t <= self.horizon_days)

    def build_segments(
        self,
        *,
        tau: float = integrator.DEFAULT_TAU,
        max_depth: int = integrator.DEFAULT_MAX_DEPTH,
    ) -> list[Segment]:
        return integrator.build_segments(self.breakpoints(), self.ln_lambda,
                                         tau=tau, max_depth=max_depth)


# ── §5.4 the reconciliation invariant ────────────────────────────────────────

def assert_provenance_reconciles(
    edges: Sequence[ProvenanceEdge],
    lambda_value: float,
    *,
    target_id: str,
    tolerance: float = RECONCILIATION_TOLERANCE,
) -> None:
    """THE §5.4 INVARIANT: |ln(λ) − Σ log_contribution| ≤ 1e-9.

    Asserted here (halting the substep, so the orchestrator rolls its savepoint
    back) AND in CI over both canonical charts.

    This is the §N.8 detector for the claim "this window's provenance explains
    it". The code paths that make it correctly read FALSE are real and were both
    exercised in test: a term added to λ without a matching edge, and an edge
    whose stored value drifts from what the evaluator actually multiplied in.
    Identity edges (`route`, `gate`) carry log_contribution = 0.0 by construction,
    so the sum is over ALL of the target's rows exactly as §5.4 words it.
    """
    if lambda_value <= 0.0 or not math.isfinite(lambda_value):
        raise ProvenanceReconciliationError(
            f'provenance_reconciliation_failed: target={target_id} has non-positive '
            f'lambda={lambda_value!r}. λ is strictly positive by construction (§5.1); '
            'a non-positive value means the hazard model is broken upstream.'
        )
    total = math.fsum(e.log_contribution for e in edges)
    delta = abs(math.log(lambda_value) - total)
    if delta > tolerance:
        raise ProvenanceReconciliationError(
            f'provenance_reconciliation_failed: target={target_id} '
            f'ln(lambda)={math.log(lambda_value)!r} but Σ log_contribution={total!r} '
            f'(|Δ|={delta!r} > {tolerance}). A provenance row set that does not '
            'reconstruct the value it explains is not weak evidence — it is no '
            'evidence (§5.4 / CLAUDE.md §N.8).'
        )


def require_baseline(lifetime_count: Optional[float], event_class: str) -> float:
    """§5.1 C-1's honest-skip gate.

    "A class with no prior row is `not_computed` and is SKIPPED ENTIRELY (no
    field rows written for it) — NEVER GIVEN A MADE-UP BASELINE."

    This is the single place that rule is enforced, and it deliberately raises
    rather than returning a sentinel: a caller that forgets to check a sentinel
    would silently build a class on a fabricated λ⁰, which is precisely the B.10
    violation the rule exists to prevent.
    """
    if lifetime_count is None:
        raise ClassSkipped(event_class, 'no_class_prior_row',
                           'no bg_class_priors lifetime-count row for this event class')
    if not math.isfinite(lifetime_count) or lifetime_count <= 0.0:
        raise ClassSkipped(event_class, 'class_prior_not_positive',
                           f'lifetime_count={lifetime_count!r}')
    return float(lifetime_count)


# ── DB loaders (lane-boundary crossings are TABLE reads or published fns) ────

def _rows(cur) -> list[dict]:
    """Normalize psycopg2 tuple rows and psycopg3/dict-cursor rows alike —
    the same defensive shape `ka_gochara_sweep` uses, because the sidecar runs
    against both cursor factories depending on entry point."""
    fetched = cur.fetchall()
    if not fetched:
        return []
    if isinstance(fetched[0], dict):
        return [dict(r) for r in fetched]
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in fetched]


def resolve_weights_pin(conn) -> tuple[str, dict[str, float]]:
    """§7.5 step 2 + sub-rule 5: resolve the ACTIVE weights version ONCE.

    The caller must do this in `plan_substeps` and carry the result in the plan;
    every substep reads the PINNED value from the plan and never re-queries. A
    long build that straddles an `mi_bhara` release would otherwise produce
    segments under two different weights versions in one snapshot — a
    non-deterministic field hash and a silently mixed model.

    NOTE this is a DATA dependency, not a build edge: `ka_kshetra` never lists
    `mi_bhara` in `depends_on` (that cycle would break every chart build). The
    loop closes ACROSS builds by version pin.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT version_id FROM kala_field_weight_versions "
            "WHERE status = 'active' ORDER BY activated_at DESC, version_id DESC LIMIT 1"
        )
        rows = _rows(cur)
    if not rows:
        raise RuntimeError(
            'no active kala_field_weight_versions row. migration 491 seeds '
            "'v0_classical' and MUST land before ka_kshetra ever runs — it is the "
            'acyclicity keystone (§7.5). There is deliberately no unpinned code path.'
        )
    version_id = rows[0]['version_id']
    with conn.cursor() as cur:
        cur.execute(
            'SELECT weight_id, weight_value FROM kala_field_weights WHERE version_id = %s',
            (version_id,),
        )
        weights = {r['weight_id']: float(r['weight_value']) for r in _rows(cur)}
    return version_id, weights


def load_class_lifetime_count(conn, event_class: str) -> tuple[Optional[float], Optional[tuple]]:
    """N_e — the class's expected lifetime count over 100 years (§5.1 C-1).

    Read from `brahma_class_priors` (asset `bg_class_priors`) at the reserved
    coordinate

        fact_kind = 'lifetime_count_per_100y'
        signal_type_class = <event_class>
        source_subsystem = '*'  ·  signal_tradition = '*'

    ⚠ HONEST GAP, DISCLOSED RATHER THAN PAPERED OVER. As of this lane's build,
    `brahma_class_priors` (migration 387) contains ONLY signal-salience priors
    keyed by `signal_type_class` ∈ {configuration, yoga, relationship, position,
    …} — there is NO per-event-class lifetime-count row anywhere in the corpus,
    and `brahma_event_ontology.base_rate_by_age` is a DISTRIBUTION OVER AGE BANDS
    (its five values sum to ≈1 for a class that happens at most once), NOT an
    expected count over a century. Reading it as N_e would be exactly the
    "plausible-sounding default standing in for I-don't-know" that CLAUDE.md
    §N.7 item 6 forbids, and §5.1 C-1 forecloses it explicitly: "never given a
    made-up baseline."

    So this returns None for every class until an L0 lane seeds the rows, and
    every class is then honestly SKIPPED with `no_class_prior_row` recorded on
    the snapshot. That is a CROSS-LANE PREREQUISITE of the same shape as §6.3's
    `bg_synthetic_cohort_md` — flagged for the Conductor, not silently invented
    here.
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT prior_version, class_prior
                 FROM brahma_class_priors
                WHERE fact_kind = 'lifetime_count_per_100y'
                  AND signal_type_class = %s
                ORDER BY prior_version DESC
                LIMIT 1""",
            (event_class,),
        )
        rows = _rows(cur)
    if not rows:
        return None, None
    pk = f"{rows[0]['prior_version']}|lifetime_count_per_100y|{event_class}"
    return float(rows[0]['class_prior']), ('brahma_class_priors', pk, None)


def load_event_shape(conn, event_class: str) -> Optional[str]:
    """`brahma_event_ontology.temporal_shape` for this class — READ, never derived.

    The shape (point / interval / chain) is a property of the EVENT CLASS, fixed
    by the ontology (migration 456), not a property of how long a particular
    window happens to be. Deriving it from a window's duration would be exactly
    the §N.7-item-3 defect: a local constant shadowing an authoritative value,
    and one that would silently reclassify the same class differently on two
    charts. Returns None when the class has no ontology row, which the caller
    turns into an honest skip rather than a default.
    """
    with conn.cursor() as cur:
        cur.execute(
            'SELECT temporal_shape FROM brahma_event_ontology WHERE event_class_id = %s',
            (event_class,),
        )
        rows = _rows(cur)
    if not rows or not rows[0].get('temporal_shape'):
        return None
    return str(rows[0]['temporal_shape'])


def require_event_shape(shape: Optional[str], event_class: str) -> str:
    """Honest-skip gate for the ontology, mirroring `require_baseline`.

    A class with no ontology row has no known shape, no magnitude floor and no
    domain — §6.1's Consequence factor reads the same table. Guessing 'interval'
    because it is the commonest value is a plausible-sounding default standing in
    for "I don't know" (§N.7 item 6); the class is skipped instead, with the
    reason recorded on the snapshot.
    """
    if shape not in ('point', 'interval', 'chain'):
        raise ClassSkipped(event_class, 'no_event_ontology_row',
                           f'brahma_event_ontology.temporal_shape={shape!r}')
    return shape


def load_promise_prior(conn, chart_id: str, event_class: str) -> PromisePrior:
    """Lane A's promise prior (§3.3).

    Prefers Lane A's published function `stage2_promise.promise_prior` — the ONE
    function §3.3 publishes across the A→C boundary. If that module has not
    landed yet, falls back to reading Lane A's TABLE `kala_field_routes` and
    applying §3.3's OWN stated aggregation, the noisy-OR

        P_e = 1 − Π_{r ∈ routes(e)} (1 − p_r)

    Reading another lane's table is explicitly permitted by §0; re-deriving its
    routing algorithm would not be, and this does not — Yen's K-shortest-paths
    result is consumed as stored.
    """
    try:                                     # pragma: no cover - lane-landing dependent
        from services.ka_kshetra.stage2_promise import promise_prior  # type: ignore
    except Exception:
        pass
    else:                                    # pragma: no cover - lane-landing dependent
        return promise_prior(chart_id, event_class, conn)

    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, route_rank, path_node_ids, path_edge_ids, route_gain,
                      is_primary, suppressed_by
                 FROM kala_field_routes
                WHERE chart_id = %s AND event_class = %s
                ORDER BY route_rank""",
            (chart_id, event_class),
        )
        rows = _rows(cur)

    routes = tuple(
        Route(
            event_class=event_class,
            route_rank=int(r['route_rank']),
            path_node_ids=tuple(r['path_node_ids'] or ()),
            route_gain=float(r['route_gain']),
            is_primary=bool(r['is_primary']),
            suppressed_by=tuple(r['suppressed_by'] or ()),
            path_edge_ids=tuple(r['path_edge_ids'] or ()),
        )
        for r in rows
    )
    p = 1.0 - math.prod(1.0 - r.route_gain for r in routes) if routes else 0.0
    return PromisePrior(p=min(max(p, 0.0), 1.0), routes=routes, n_routes=len(routes),
                        fact_ids=tuple(f'kala_field_routes:{r["id"]}' for r in rows))


def load_clocks(conn, chart_id: str) -> list[ClockApplicability]:
    """Lane B's `kala_field_clocks`, read as a table (§0-permitted crossing)."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT system_id, applicability_state, exclusion_reason, competence_class,
                      seniority_rank, quality, quality_basis, is_predictive
                 FROM kala_field_clocks
                WHERE chart_id = %s
                ORDER BY seniority_rank, system_id""",
            (chart_id,),
        )
        rows = _rows(cur)
    return [
        ClockApplicability(
            system_id=r['system_id'],
            applicability_state=r['applicability_state'],
            competence_class=r['competence_class'],
            seniority_rank=int(r['seniority_rank']),
            is_predictive=bool(r['is_predictive']),
            quality=None if r['quality'] is None else float(r['quality']),
            quality_basis=r.get('quality_basis'),
            exclusion_reason=r.get('exclusion_reason'),
        )
        for r in rows
    ]


def load_ladder(conn, chart_id: str) -> dict[str, list[LadderPeriod]]:
    """Precision-SUPPORTED periods from Lane B's `kala_field_boundaries`.

    `precision_state = 'precision_unsupported'` rows are EXCLUDED at the query
    (rule C-5): such a level contributes no hazard factor at all, rather than a
    reduced one. A boundary row gives the period START; its end is the next
    boundary at the same (system, level), or the horizon.
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT system_id, level, lord, t_boundary, period_days, precision_state
                 FROM kala_field_boundaries
                WHERE chart_id = %s AND precision_state <> 'precision_unsupported'
                ORDER BY system_id, level, t_boundary""",
            (chart_id,),
        )
        rows = _rows(cur)

    by_key: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        by_key.setdefault((r['system_id'], r['level']), []).append(r)

    out: dict[str, list[LadderPeriod]] = {}
    for (system_id, level), group in by_key.items():
        for i, r in enumerate(group):
            t0 = float(r['t_boundary'])
            t1 = (float(group[i + 1]['t_boundary']) if i + 1 < len(group)
                  else t0 + float(r['period_days'] or 0.0))
            if t1 <= t0:
                continue
            out.setdefault(system_id, []).append(
                LadderPeriod(system_id=system_id, level=level, lord=r['lord'],
                             t_start=t0, t_end=t1)
            )
    return out


def load_primitives(conn, chart_id: str) -> list[Primitive]:
    """Lane A's `kala_field_primitives`, parsed into evaluable envelopes."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT primitive_kind, subject, object_ref, envelope, polarity,
                      class_label, source_table, source_pk, source_fact_id
                 FROM kala_field_primitives
                WHERE chart_id = %s
                ORDER BY primitive_kind, subject, COALESCE(object_ref,''), t_start""",
            (chart_id,),
        )
        rows = _rows(cur)

    out: list[Primitive] = []
    for r in rows:
        env = r['envelope']
        if isinstance(env, str):
            env = json.loads(env)
        knots = tuple((float(k['t']), float(k['v'])) for k in env)
        if len(knots) < 2:
            # §3.2's contract is violated upstream. Skipping silently would make
            # the field quietly weaker; halting names the producing lane's bug.
            raise ValueError(
                f'kala_field_primitives envelope for {r["primitive_kind"]}:{r["subject"]} '
                f'has {len(knots)} knot(s); the frozen §3.2 contract requires ≥2.'
            )
        out.append(Primitive(
            primitive_kind=r['primitive_kind'], subject=r['subject'],
            object_ref=r.get('object_ref'), polarity=r['polarity'],
            class_label=r.get('class_label'), knots=knots,
            source_table=r.get('source_table'), source_pk=r.get('source_pk'),
            source_fact_id=r.get('source_fact_id'),
        ))
    return out


def load_kinematics_breakpoints(conn, chart_id: str) -> list[float]:
    """Every `kala_field_kinematics.t_days` — the stage-0 Brent roots."""
    with conn.cursor() as cur:
        cur.execute(
            'SELECT DISTINCT t_days FROM kala_field_kinematics WHERE chart_id = %s '
            'ORDER BY t_days',
            (chart_id,),
        )
        return [float(r['t_days']) for r in _rows(cur)]


def load_legacy_crosscheck(conn, chart_id: str, event_class: str) -> list[dict]:
    """READ-ONLY cross-check corpus: the legacy `kala_gochara_windows` rows.

    §5.3: W2 writes NOTHING to this table and NEVER copies `signed_intensity`
    into a field column (§N.5). It records only the CLASSIFICATION of
    agreement/divergence as a `term_role='gate'` provenance edge, so W6 has a
    reference to classify against. The equivalence corpus and the cutover are W6
    work; W2 only ensures the reference exists.
    """
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, window_start, window_end, peak_date, temporal_shape
                 FROM kala_gochara_windows
                WHERE chart_id = %s AND event_class = %s
                ORDER BY window_start, peak_date""",
            (chart_id, event_class),
        )
        return _rows(cur)


__all__ = [
    'HORIZON_DAYS', 'RECONCILIATION_TOLERANCE', 'LEVEL_ORDER',
    'PRIMITIVE_TO_COVARIATE', 'MOORTI_TO_COVARIATE', 'ECLIPSE_CANDIDATE_LABEL',
    'ProvenanceReconciliationError', 'ClassSkipped', 'UpstreamStageIncomplete',
    'canonical_json', 'FieldPins', 'field_content_hash',
    'Primitive', 'EnvelopeIndex', 'LadderPeriod', 'FieldEvaluator',
    'assert_provenance_reconciles', 'require_baseline', 'require_event_shape',
    'resolve_weights_pin', 'load_class_lifetime_count', 'load_event_shape',
    'load_promise_prior',
    'load_clocks', 'load_ladder', 'load_primitives',
    'load_kinematics_breakpoints', 'load_legacy_crosscheck',
]
