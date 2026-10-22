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

import dataclasses

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, Mapping, Sequence

from . import window_solver as _solver
from .result_policy import ALL_NULL_REASON, POLICY_ALL_NULL, POLICY_QUALIFICATION, RESULT_POLICIES
from .substrate import DB_BODY

UNQUALIFIED = "unqualified"
OMIT = "omit"
CHANNEL_FOR = "evidence_for_occurrence"
CHANNEL_AGAINST = "evidence_against_occurrence"

# P3/P4: every record is a contact of an agent with the class's signature house / lord — an
# activation of the class, so evidence FOR it (Stream B, WINDOW_SWEEP_ANSWER (1)). P2 carries a
# DIRECTION per record (the house from janma-rāśi is in the cited favourable set, or in the adverse-
# residence set — D-RQ5), assigned to a channel through `score.channel_for`. A path in neither group
# has no window sweep yet (P1 is a later increment) and refuses loudly.
FOR_ONLY_PATHS = frozenset({"P3", "P4"})
DIRECTIONAL_PATHS = frozenset({"P2"})
# P1's four soft factors (dignity / combustion / agent_nature / maitrī) are CATEGORICAL or step rows
# that declare no [0,1] value mapping (dignity carries a virūpa ordering anchor "with no magnitude
# claim"). Its windows are formed (connected union of admitted supports) and stored UNQUALIFIED with
# the named reason `value_mapping_undeclared` until a row declares one; channel assignment through
# agent_nature is not implemented, and refuses if a record is ever qualified before it is.
CATEGORICAL_PATHS = frozenset({"P1"})
SWEEP_PATHS = FOR_ONLY_PATHS | DIRECTIONAL_PATHS | CATEGORICAL_PATHS
# `karaka_agent` (ND-H-20261005, K-A) is a RANK category with the FB-36 authored default mapping and null_state `omit`: it
# takes no part in the within-path product (it never admits, excludes or zeroes) — its category is read from
# `services.gochara_rules.registry.karaka_category`.
CATEGORICAL_FACTORS = frozenset({"dignity_of_transit_sign", "combustion", "agent_nature",
                                 "maitri_compound", "karaka_agent"})

# A factor row's `direction` that says only "which way is stronger" assigns no channel; one that
# names a channel/valence declares an against-channel operand; anything else is ambiguous.
MAGNITUDE_ONLY_DIRECTIONS = frozenset({"higher = stronger", "lower = stronger"})

# Span-kind and angular-kind object kinds are NOT enumerated here: the factor row's own
# applicability block lists them (activity_kernel@1.1.0). Nothing below names a kind.

_EPS = 1e-12
# The frozen measurement contract's peak-tie tolerance (1e-9): two objective values within it are ONE
# plateau and the EARLIEST instant wins. It is deliberately NOT the storage-comparison tolerance (the
# verifier's 1e-6 is the REAL/float4 round-trip, a different question). Search noise is kept below it
# by evaluating at exact `peak_hints` (a point contact's exact instant) rather than by loosening it.
_TIE = 1e-9


class SweepRefusal(RuntimeError):
    """The sweep cannot honestly evaluate this input (named, never a silent default)."""


@dataclass(frozen=True)
class OperandSource:
    """What the store supplies for ONE factor of a record (W0, SR-OD1 plan §2.7): the factor's change instants and their
    completeness are PER FACTOR, so a record carrying a dṛṣṭi offset, a vedha overlay and a P1 state is not made complete
    by whichever one of them happens to have a provider.

      boundaries     the instants inside `[lo, hi)` at which THIS factor's operand state changes (None = no provider)
      complete       the store asserts that list is complete over every support of the record
      value_at       the factor's value in [0,1] at t (None = undeterminable). Read ONLY for a categorical factor the
                     sweep cannot derive itself; dṛṣṭi / activity_kernel / vedha values stay the sweep's own
      channel_at     the channel this factor assigns the record at t (`CHANNEL_FOR` / `CHANNEL_AGAINST`; None =
                     undeterminable) — P1's agent_nature decides the side per instant (Q3(a)); absent ⇒ the record's
                     channel is the static one `record_channel` gives
      unknown_reason the named reason this factor's operand is undeterminable at t (None = it is not this factor's
                     operand that is unknown); passed through to the window's reason instead of the generic
                     `objective_unknown_over_component`
      not_applicable the factor is DECLARED not applicable to this record (P1 combustion of a node / the Sun: L1 M-19,
                     BPHS 7.28-29 translator's note PG99:C1) — it takes no part in the product (`na`), which is not the
                     same statement as "contributes 1.0"
    """
    boundaries: Callable[[datetime, datetime], list[datetime]] | None = None
    complete: bool = False
    value_at: Callable[[datetime], float | None] | None = None
    channel_at: Callable[[datetime], str | None] | None = None
    unknown_reason: Callable[[datetime], str | None] | None = None
    not_applicable: bool = False


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
    # Operand sources, supplied by the store ONLY when it has them. A callable returning None means "not
    # determinable at t" (a named missing operand). `longitude_at` is the transiting body's sidereal
    # longitude; the kernel's MEMBERSHIP and angular distance are computed from it by Stream B's
    # `kernel_factor` (validated geometry — never a caller flag); `aspect_rays` are the directed dṛṣṭi
    # angles an ASPECT record is evaluated along (empty for residence/conjunction).
    longitude_at: Callable[[datetime], float | None] | None = None
    aspect_rays: tuple = ()
    aspect_offset_at: Callable[[datetime], int | None] | None = None
    house_from_frame: int | None = None        # the record's own §1.2 inv 5 house (P2: from janma-rāśi)
    # R4: the record's physical object's canonical target (validated against `object_kind` BEFORE any
    # factor is evaluated) and, when the store has a position probe, whether the contact geometry
    # actually places the target inside/under the body's ray at t (None = not determinable).
    canonical_target: str | None = None
    # P1 only (migration 1233): the period lord whose strength the P1 factors judge. It is the TRANSITING `agent` for the lord's own
    # transit and a different graha for the AM-21 delivery forms (Sun / Jupiter through another lord's exaltation or debility
    # sign), so the factor sources read the ANCHOR's sky, never the agent's (`record_store._anchor`: anchor or agent). Lowercase token.
    period_anchor_lord: str | None = None
    # R7 [7]: instants INSIDE the support at which an operand's STATE changes (a dṛṣṭi source sign
    # ingress, a vedha interval edge): the objective is solved piecewise between them. And the instants
    # at which a smooth kernel is exactly maximal (a point contact's exact instant).
    state_boundaries: Callable[[datetime, datetime], list[datetime]] | None = None
    # R8-6: the store asserts the boundary list is COMPLETE over the support (every operand state change inside it is
    # listed). A record with a state-valued operand (dṛṣṭi source sign, vedha overlay) whose boundaries are absent or
    # not asserted complete is UNQUALIFIED (`state_boundaries_incomplete`): an unlisted change could hide an interior
    # gap that a piece would bridge, or an island that would score 0.
    state_boundaries_complete: bool = False
    peak_hints: Callable[[datetime, datetime], list[datetime]] | None = None
    # S3 (the solver's seams): the body's longitude AND its longitudinal speed (degrees, degrees per DAY — the Swiss speed output) from ONE ephemeris call, and the
    # Swiss station instants of the body (the stored, ephemeris-refined `t_exact`s: extra cuts, S0 K-2). Absent ⇒ the speed is a centred
    # difference of `longitude_at` and no station is listed (the solver then proves monotonicity from the velocity sign alone).
    longitude_speed_at: Callable[[datetime], tuple] | None = field(default=None, compare=False)
    station_instants: Callable[[], list] | None = field(default=None, compare=False)
    # W0: per-factor operand sources, keyed by factor_id. `state_boundaries` / `state_boundaries_complete` above are the
    # record-wide DEFAULT a state-valued factor (dṛṣṭi, vedha) falls back to when it has no source of its own here.
    operand_sources: dict = field(default_factory=dict, compare=False)


# ── R4: the boundary adapters and the geometry contract ──────────────────────

# The persisted graha tokens are lowercase (kgrr_agent_ck); the rule helpers speak Title case. A CLOSED,
# tested adapter — never `.title()` on whatever arrives. Derived from the brahmagyan.graha_vocabulary SSoT via
# substrate.DB_BODY (R17 adoption over addition — the local literal retired onto the SSoT helpers after the
# protected window).
GRAHA_TITLE = {db_value: title for title, db_value in DB_BODY.items()}


def graha_title(token: str) -> str:
    if token not in GRAHA_TITLE:
        raise SweepRefusal(f"graha token {token!r} is not in the closed lowercase vocabulary")
    return GRAHA_TITLE[token]


# kgrr_object_kind_ck's vocabulary → the canonical-target FORM each kind requires. Extents (a sign, a
# house, a 13°20′ nakṣatra) are `span:`/`star:`; the point kinds are `point:<longitude>`. 1155 does
# NOT enforce this agreement; the sweep does, before it evaluates anything. `varga_position` has no
# classified geometry here and stays explicitly unqualified (object_kind_not_covered_by_applicability).
KIND_TARGET_FORM = {"sign_span": "span:", "house_span": "span:", "star": "star:",
                    "degree_point": "point:", "derived_point": "point:", "saham": "point:",
                    "house_lord": "point:"}


def validate_geometry(rec: "SweepRecord") -> None:
    """Refuse a record whose object kind and canonical target disagree (a point labelled a span would
    take the membership step and bypass the unratified-orb branch), and a node-cast aspect (N-14)."""
    from . import targets as _targets
    if rec.relation == "aspect" and rec.agent in ("rahu", "ketu"):
        raise SweepRefusal(f"record {rec.record_id}: a node casts no dṛṣṭi (N-14) — aspect record refused")
    form = KIND_TARGET_FORM.get(rec.object_kind)
    if form is None:
        return
    if rec.canonical_target is None:
        raise SweepRefusal(f"record {rec.record_id}: object kind {rec.object_kind!r} requires its "
                           "canonical target to validate the geometry — none supplied")
    try:
        _targets.validate_canonical_target(rec.canonical_target)
    except ValueError as exc:
        raise SweepRefusal(f"record {rec.record_id}: {exc}") from exc
    if not rec.canonical_target.startswith(form):
        raise SweepRefusal(
            f"record {rec.record_id}: object kind {rec.object_kind!r} requires a {form!r} target, "
            f"got {rec.canonical_target!r} — geometry and kind disagree")


# ── factor outcomes ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Outcome:
    """What one factor says about one record. Exactly one of: not applicable (factor takes no part
    in the product), a constant, a function of t, or a missing operand (takes the row's null_state)."""
    kind: str                           # 'na' | 'const' | 'fn' | 'missing'
    value: float | None = None
    fn: Callable[[datetime], float | None] | None = None
    # a membership CONSTANT is still CHECKED against the contact geometry at every piece: True = the
    # geometry confirms the support, False = it contradicts it, None = undeterminable
    check: Callable[[datetime], bool | None] | None = None
    null_state: str | None = None
    reason: str | None = None
    factor: str | None = None
    # W0: a STATE-valued factor (a step function of the sky) is solved piecewise between its change instants, which
    # must be known completely; they are carried PER FACTOR, with the other `OperandSource` hooks.
    state_valued: bool = False
    boundaries: Callable[[datetime, datetime], list[datetime]] | None = None
    boundaries_complete: bool = False
    channel_at: Callable[[datetime], str | None] | None = None
    unknown_reason: Callable[[datetime], str | None] | None = None
    # S3: a POINT kernel's geometry for the solver — (target longitude, ratified orb) in degrees; the value is `max(0, 1 − d/orb)` along each directed ray
    tent: tuple | None = None


def _check_unit(value, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) \
            or not (0.0 <= float(value) <= 1.0):
        raise SweepRefusal(f"{what}: factor value {value!r} outside the declared [0,1] range (§2.1)")
    return float(value)


def _missing(row: dict, reason: str) -> Outcome:
    return Outcome("missing", null_state=row["null_state"], reason=reason, factor=row["factor_id"])


def _kernel_value_at(rec: SweepRecord, ref: tuple, t: datetime) -> float | None:
    """The activity kernel at `t`, from Stream B's validated `kernel_factor` (CALLED, never copied):
    membership of the body's longitude — carried along each directed dṛṣṭi ray of an aspect record — in
    the target's extent, or the seam-safe angular distance to a point. The best ray wins (any one ray
    on the target is the contact). None = undeterminable."""
    from services.gochara_rules import kernel_factor as _kf
    lon = rec.longitude_at(t)
    if lon is None:
        return None
    best = None
    for ang in (rec.aspect_rays or (None,)):
        r = _kf.activity_kernel(rec.object_kind, rec.canonical_target, factor_ref=ref,
                                body_longitude_deg=float(lon) % 360.0, aspect_angle_deg=ang)
        if r["value"] is not None:
            best = r["value"] if best is None else max(best, r["value"])
    return best


_JD_UNIX_EPOCH = 2440587.5       # the same JD <-> datetime convention the store writes boundaries under (record_store._JD_UNIX_EPOCH)


def jd_ulp_tolerance(t: datetime) -> timedelta:
    """ONE JD-ulp at `t`: the spacing of the double that carries the instant's Julian Day (≈ 4.7e-10 d ≈ 40 µs at JD 2.46e6), rounded UP to the
    datetime's microsecond, plus that one microsecond (the stored edge and the probe instant are each a whole-µs datetime). The substrate stores a contact boundary as a Julian-Day double that Swiss bisected to 1e-9 d (`swiss_bisect_tol_1e-9d`)
    and `record_store` converts to a datetime; a stored edge therefore sits at most one JD-ulp from the sign / orb edge it names (measured 19–22 µs
    on the real sky, AR_DIAG §2). This is the only slack the support/geometry check grants; a 1 s disagreement is 25,000 times larger."""
    jd = t.timestamp() / 86400.0 + _JD_UNIX_EPOCH
    return timedelta(microseconds=math.ceil(math.ulp(jd) * 86400.0 * 1e6) + 1)


def _geometry_at_edge(check, instant: datetime, side: str, lo: datetime, hi: datetime) -> bool | None:
    """The geometry check at one END of a stored piece `[lo, hi)`, under the boundary convention of the platform (half-open: a change instant is the
    FIRST microsecond of the NEW state, which owns it — p1_operands.py BOUNDARIES, p1_operands_check.py NAMED LIMITS; SR-OD1 R-2 / SR-H2-1S).
    A stored edge is exact only to one JD-ulp (`jd_ulp_tolerance`), so a `False` AT the edge is accepted iff the target is inside at the first
    instant one ulp INSIDE the piece (`start`: `instant + ulp`; `end`: `instant - ulp`), i.e. the true edge lies within one ulp of the stored one.
    Never looser: a `False` there too (the edge is further than one ulp off), or an undeterminable probe, keeps the `False`; a `True` or `None`
    at the edge itself is returned unchanged. The probe never leaves the piece (clamped to its midpoint when the piece is shorter than 2 ulp)."""
    g = check(instant)
    if g is not False:
        return g
    tol = jd_ulp_tolerance(instant)
    mid = lo + (hi - lo) / 2
    probe = min(instant + tol, mid) if side == "start" else max(instant - tol, mid)
    return check(probe) is True


def activity_kernel(row: dict, rec: SweepRecord) -> Outcome:
    """Routed through the validated row/geometry contract (Codex round 7 [8]): the factor row addressed by
    ITS membership reference declares applicability, the physical target is validated against the object
    kind, a numeric orb is admissible only when the row ratifies it with a decision reference, and
    membership is COMPUTED from the contact geometry. A row without `applicability` (the 1.0.0 row) leaves
    the operand unevaluable (unqualified)."""
    from services.gochara_rules import kernel_factor as _kf
    ap = row.get("applicability")
    if not ap:
        return _missing(row, "applicability_undeclared")
    ref = (row["factor_id"], row["rule_version"])
    try:
        parsed = _kf.parse_target(rec.object_kind, rec.canonical_target, ap)
    except _kf.TargetKindMismatch as exc:
        raise SweepRefusal(f"record {rec.record_id}: {exc}") from exc
    if parsed is None:
        return _missing(row, "object_kind_not_covered_by_applicability")
    if rec.longitude_at is None:        # missing geometry is a named missing operand, never "inside"
        return _missing(row, "geometry_operand_missing")
    try:                                 # a configured-but-invalid row fails closed HERE, never scores
        probe = _kf.activity_kernel(rec.object_kind, rec.canonical_target, factor_ref=ref,
                                    body_longitude_deg=0.0, aspect_angle_deg=None)
    except _kf.KernelFactorConfigError as exc:
        raise SweepRefusal(f"activity_kernel row {ref}: {exc}") from exc
    if parsed[0] in ("span", "star"):
        step = ap["span"]
        inside_v = _check_unit(step.get("inside"), "activity_kernel span.inside")
        outside_v = step.get("outside")

        def _check(t, _ref=ref, _in=inside_v, _out=outside_v):
            v = _kernel_value_at(rec, _ref, t)
            return None if v is None else (True if v == _in else (False if v == _out else None))
        return Outcome("const", value=inside_v, factor=row["factor_id"], check=_check)
    if probe["reason"] == "orb_not_ratified":
        return _missing(row, "orb_not_ratified")
    return Outcome("fn", fn=lambda t, _ref=ref: _kernel_value_at(rec, _ref, t),
                   null_state=row["null_state"], factor=row["factor_id"],
                   tent=(float(parsed[1]), float(ap["angular"]["orb_deg"])))


def graduated_drishti(row: dict, rec: SweepRecord,
                      drishti: Callable[[str, int, tuple], float] | None) -> Outcome:
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
    ref = (row["factor_id"], row["rule_version"])      # the membership's OWN factor ref, passed to the source

    def _fn(t: datetime, _o=off_at, _a=rec.agent, _ref=ref):
        off = _o(t)
        if off is None:
            return None
        v = drishti(_a, off, _ref)         # None = an operand the source cannot classify (unqualified)
        return None if v is None else _check_unit(v, "graduated_drishti")

    return Outcome("fn", fn=_fn, null_state=row["null_state"], factor=row["factor_id"])


def vedha_attenuation(row: dict, rec: SweepRecord,
                      vedha: Callable[[SweepRecord, datetime], float | None] | None) -> Outcome:
    """The vedha operand is the state of the overlay interval at t (§5). Two sources are understood:

      * a STRUCTURED source (`vedha.overlay(rec, factor_ref)` — `vedha_source.VedhaProvider`, SR-OD1 C1): the factor is
        declared not-applicable (`na`: adverse residence, an uncited pair, a node as the transiting body) or a step function
        over the record's supports whose own change instants are COMPLETE and whose undeterminable stretches carry their named
        reason (`obstructor_residence_unknown`, `node_residence_unknown`). Each segment's value must equal the row's declared
        state→value mapping — a source that disagrees with the registry is refused, never trusted;
      * a plain `(rec, t) -> float` callable (the pre-C1 contract, kept for the sweep's own tests): value only; its boundaries come
        from the record-wide list or a per-factor `OperandSource`.

    With no source bound the operand is a named missing input — never 1.0."""
    if vedha is None:
        return _missing(row, "vedha_overlay_not_bound")
    overlay_of = getattr(vedha, "overlay", None)
    if overlay_of is None:
        return Outcome("fn", fn=lambda t, _r=rec: vedha(_r, t), null_state=row["null_state"],
                       factor=row["factor_id"])
    ap = row.get("applicability")
    if not ap:                    # the 1.0.0 row declares no mapping: there is nothing to apply a derived state to
        return _missing(row, "applicability_undeclared")
    mapping = ap["mapping"]
    ov = overlay_of(rec, (row["factor_id"], row["rule_version"]))
    if not ov.applicable:
        return Outcome("na", factor=row["factor_id"], reason=ov.not_applicable_reason)
    for seg in ov.segments:
        if seg.state in mapping and seg.value != float(mapping[seg.state]):
            raise SweepRefusal(f"record {rec.record_id}: the vedha source valued a {seg.state!r} stretch {seg.value!r}, but "
                               f"{row['factor_id']}@{row['rule_version']} maps {seg.state!r} to {mapping[seg.state]!r}")
        if seg.value is not None and seg.state not in mapping:
            raise SweepRefusal(f"record {rec.record_id}: the vedha source valued a {seg.state!r} stretch, which the row does not map")
    return Outcome("fn", fn=ov.value_at, null_state=row["null_state"], factor=row["factor_id"], state_valued=True,
                   boundaries=ov.boundaries, boundaries_complete=ov.complete, unknown_reason=ov.unknown_reason_at)


def categorical_factor(row: dict, rec: SweepRecord | None = None) -> Outcome:
    """A categorical/step factor with no declared value mapping cannot yield a number in [0,1]:
    the operand is a named missing input (`value_mapping_undeclared`), never a default. A row that
    DOES declare a `value_mapping` has a shape this sweep cannot interpret yet — refused by name.
    W0: a record whose store supplies an `OperandSource` WITH a `value_at` for this factor gets a function-valued
    outcome — the source (not the sweep) applied the factor's value rule; the sweep never maps a category itself."""
    if row.get("value_mapping"):
        raise SweepRefusal(
            f"factor {row['factor_id']!r} declares a value_mapping; the sweep has no reader for it yet "
            "— refused, never ignored")
    src = None if rec is None else rec.operand_sources.get(row["factor_id"])
    if src is not None and src.not_applicable:
        return Outcome("na", factor=row["factor_id"], reason="not_applicable_by_declaration")
    if src is not None and src.value_at is not None:
        return _stateful(Outcome("fn", fn=src.value_at, null_state=row["null_state"], factor=row["factor_id"]), rec)
    return _missing(row, "value_mapping_undeclared")


def _stateful(out: Outcome, rec: SweepRecord) -> Outcome:
    """Attach the factor's own boundaries / completeness / channel / reason hooks to its function-valued outcome. A factor
    with an `OperandSource` uses it; a state-valued factor without one inherits the record-wide `state_boundaries` (the
    pre-W0 behaviour, unchanged)."""
    if out.kind != "fn" or out.boundaries is not None:     # an outcome that brings its own boundaries (C1 vedha) keeps them
        return out
    src = rec.operand_sources.get(out.factor)
    if src is not None:
        b, done = src.boundaries, src.complete
    else:
        b, done = rec.state_boundaries, rec.state_boundaries_complete
    # dṛṣṭi / vedha are state-valued by name; a categorical factor is so by having a source that supplies its values
    return dataclasses.replace(
        out, state_valued=out.factor in STATE_VALUED_FACTORS or (src is not None and src.value_at is not None),
        boundaries=b, boundaries_complete=bool(done and b is not None),
        channel_at=None if src is None else src.channel_at,
        unknown_reason=None if src is None else src.unknown_reason)


def evaluate_factors(rec: SweepRecord, factor_rows: list[dict], *,
                     drishti: Callable[[str, int, tuple], float] | None = None,
                     vedha: Callable[[SweepRecord, datetime], float | None] | None = None) -> list[Outcome]:
    """One outcome per declared soft factor. A factor the sweep has no evaluator for REFUSES (a
    later increment's path must not be silently scored without it)."""
    out: list[Outcome] = []
    for row in factor_rows:
        fid = row["factor_id"]
        if fid == "activity_kernel":
            out.append(activity_kernel(row, rec))
        elif fid == "graduated_drishti":
            out.append(_stateful(graduated_drishti(row, rec, drishti), rec))
        elif fid == "vedha_attenuation":
            out.append(_stateful(vedha_attenuation(row, rec, vedha), rec))
        elif fid in CATEGORICAL_FACTORS:
            out.append(categorical_factor(row, rec))
        else:
            raise SweepRefusal(
                f"path {rec.path_id}: factor {fid!r} has no sweep evaluator yet "
                "— refused, never skipped")
    return out


# ── per-record program ───────────────────────────────────────────────────────

@dataclass
class RecordProgram:
    rec: SweepRecord
    qualified: bool
    null_states: set
    reasons: list                       # [(factor_id, reason)] of every missing operand
    outcomes: list = field(default_factory=list)
    channel: str = CHANNEL_FOR

    @property
    def has_channel_fn(self) -> bool:
        """True iff one of this record's factors assigns the side PER INSTANT (P1 agent_nature, Q3(a))."""
        return any(o.channel_at is not None for o in self.outcomes)

    def channel_at(self, t: datetime) -> str | None:
        """The record's channel at t: its deciding factor's per-instant side when it has one (None = undeterminable at
        t), else the static channel. A value that is not a channel is refused, never coerced."""
        for o in self.outcomes:
            if o.channel_at is not None:
                c = o.channel_at(t)
                if c is not None and c not in (CHANNEL_FOR, CHANNEL_AGAINST):
                    raise SweepRefusal(f"{o.factor}: channel {c!r} at {t.isoformat()} is neither the for nor the "
                                       "against channel")
                return c
        return self.channel

    def undeterminable_at(self, t: datetime) -> bool:
        return self.value_at(t) is None or self.channel_at(t) is None

    def unknown_reason_at(self, t: datetime) -> str | None:
        """The named reason a factor of this record gives for being undeterminable at t (None = no factor names one)."""
        for o in self.outcomes:
            if o.unknown_reason is not None:
                r = o.unknown_reason(t)
                if r is not None:
                    return r
        return None

    @property
    def checks(self) -> list:
        """The geometry checks of this record's membership constants (run at every piece)."""
        return [o.check for o in self.outcomes if o.kind == "const" and o.check is not None]

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


def p2_direction(agent: str, house: int | None) -> str:
    """P2 direction of a residence record: 'favourable' iff its house from janma-rāśi is in the
    cited favourable set (Phaladīpikā XXVI), 'adverse' iff in the adverse-residence set (D-RQ5).
    Stream B's rows are CALLED, never copied; a house in neither, or in both, is refused."""
    from services.gochara_rules import admission as _adm
    from services.gochara_rules import favourable_houses as _fav
    if house is None:
        raise SweepRefusal("P2 record without a house from janma-rāśi — direction undeterminable")
    name = graha_title(agent)
    fav = house in _fav.favourable_houses(name)
    adv = name in _adm.ADVERSE_RESIDENCE_BODIES and house in _adm.ADVERSE_RESIDENCE_HOUSES
    if fav == adv:
        raise SweepRefusal(
            f"P2 {name} house {house}: in the favourable set={fav} and the adverse set={adv} — "
            "direction is not decidable from the cited sets; refused, never defaulted")
    return "favourable" if fav else "adverse"


def record_channel(event_class: str, rec: SweepRecord) -> str:
    if rec.path_id in CATEGORICAL_PATHS:
        raise SweepRefusal(
            f"{rec.path_id}: channel assignment through agent_nature/dignity is not implemented — "
            "a qualified P1 record cannot be placed in a channel yet")
    if rec.path_id in FOR_ONLY_PATHS:
        return CHANNEL_FOR
    if rec.path_id in DIRECTIONAL_PATHS:
        from services.gochara_rules.score import channel_for
        return channel_for(p2_direction(rec.agent, rec.house_from_frame), event_class)
    raise SweepRefusal(f"path {rec.path_id} has no window sweep yet")


def against_channel_state(factor_rows: list[dict]) -> str:
    """Derived from the path's own soft-factor rows (never from a path name): 'none_declared' iff
    every factor's `direction` says only which way is stronger; 'declared' iff one names a
    channel/valence; 'ambiguous' otherwise (silent/unparseable ⇒ the against sum is NULL)."""
    state = "none_declared"
    for row in factor_rows:
        d = row.get("direction")
        if d in MAGNITUDE_ONLY_DIRECTIONS:
            continue
        if isinstance(d, str) and ("channel" in d or "valence" in d):
            return "declared"
        state = "ambiguous"
    return state


#: factors whose operand is a STATE (a step function of the sky: the dṛṣṭi source's sign, the vedha overlay interval)
#: — the objective is solved piecewise between its change instants, which therefore must be known completely
STATE_VALUED_FACTORS = frozenset({"graduated_drishti", "vedha_attenuation"})
STATE_BOUNDARIES_REASON = "state_boundaries_incomplete"


def build_program(rec: SweepRecord, factor_rows: list[dict], *,
                  drishti: Callable[[str, int, tuple], float] | None = None,
                  vedha: Callable[[SweepRecord, datetime], float | None] | None = None,
                  channel: str = CHANNEL_FOR) -> RecordProgram:
    validate_geometry(rec)
    outcomes = evaluate_factors(rec, factor_rows, drishti=drishti, vedha=vedha)
    null_states: set = set()
    reasons: list = []
    qualified = True
    for o in outcomes:
        if o.kind == "missing":
            null_states.add(o.null_state)
            if o.null_state == UNQUALIFIED:
                reasons.append((o.factor, o.reason))
                qualified = False
            # an OMITTED operand (a rank factor, K-A) takes no part in the product and breaks no qualification:
            # it is not an unresolved reason of the member (`unresolved` classifies unqualified members only)
    if sum(1 for o in outcomes if o.channel_at is not None) > 1:
        raise SweepRefusal(f"record {rec.record_id}: more than one factor assigns the channel — the side is "
                           "decided by exactly one factor")
    # W0: completeness is judged PER FACTOR — every state-valued function-valued factor (a channel-deciding one is
    # state-valued) must carry its own complete boundary list; one factor's provider never vouches for another's
    if qualified and any(o.state_valued and o.kind == "fn"
                         and not (o.boundaries is not None and o.boundaries_complete) for o in outcomes):
        null_states.add(UNQUALIFIED)
        reasons.append(("state_boundaries", STATE_BOUNDARIES_REASON))
        qualified = False
    return RecordProgram(rec=rec, qualified=qualified, null_states=null_states,
                         reasons=reasons, outcomes=outcomes, channel=channel)


# ── maximisation (interior extrema, never endpoint-only — §7.2 inv 2, O-SM-4) ─

def maximise_earliest(f: Callable[[datetime], float | None], lo: datetime, hi: datetime, *,
                      samples: int = 96, tol_seconds: float = 0.001,
                      hints: Iterable[datetime] = ()) -> tuple[float, datetime] | None:
    """(max value, earliest instant achieving it) of `f` over `[lo, hi)`, or None if `f` is UNKNOWN
    anywhere it was evaluated. The caller partitions at exact operand-state boundaries first, so within
    `[lo, hi)` every function is smooth/unimodal or constant; the method then establishes the maximum
    from candidates that include (a) the piece start, (b) every exact `hint` inside it (a smooth
    kernel's exact maximum — never found by luck), and (c) a dense uniform scan.

    EXTREMA, not points (Codex round 8, R8-6): the scan is reduced to its DISTINCT local extrema — a run of
    exactly equal scan values is ONE plateau, a run higher than both neighbouring runs is one candidate — and each
    candidate is resolved on its OWN: an interior hump by bracketed golden-section to `tol_seconds` (its true peak,
    never an earlier scan point that merely sits within a tolerance of it), a plateau/step by bisecting its start to
    the earliest instant that reaches the plateau value EXACTLY. The frozen 1e-9 tie tolerance (`_TIE`) is applied
    ONLY BETWEEN these distinct extrema: among candidates whose resolved values are within it of the best, the
    earliest instant wins. It never moves a peak within one smooth hump (that was the 27-second shift).
    An unknown value ANYWHERE makes the whole piece unknown (R7 [1]: an unknown portion cannot be dropped)."""
    span = (hi - lo).total_seconds()
    if span <= 0:
        raise SweepRefusal("empty support piece")
    pts = sorted({lo} | {h for h in hints if lo <= h < hi}
                 | {lo + timedelta(seconds=span * k / samples) for k in range(1, samples)})
    vals = [f(p) for p in pts]
    if any(v is None for v in vals):
        return None
    n = len(pts)
    # runs of scan values equal to FLOAT NOISE (`_EPS` = 1e-12, three orders below the tie tolerance and nothing like it:
    # a sum of linear kernels is a flat plateau whose computed values differ in the last bit) → (first index, last index)
    runs: list[tuple[int, int]] = []
    start = 0
    for i in range(1, n + 1):
        if i == n or abs(vals[i] - vals[start]) > _EPS:
            runs.append((start, i - 1))
            start = i
    phi = (math.sqrt(5) - 1) / 2
    resolved: list[tuple[float, datetime]] = []
    for k, (a, b) in enumerate(runs):
        v = max(vals[a:b + 1])
        if (k > 0 and v <= max(vals[runs[k - 1][0]:runs[k - 1][1] + 1])) or \
                (k + 1 < len(runs) and v <= max(vals[runs[k + 1][0]:runs[k + 1][1] + 1])):
            continue                                    # not a local extremum of the scan
        best_v, best_t = v, pts[vals.index(v, a, b + 1)]
        # (1) an interior hump: bracketed golden-section around the run, to `tol_seconds`
        left = pts[max(a - 1, 0)]
        right = pts[b + 1] if b + 1 < n else hi - timedelta(microseconds=1)
        x, y = left, right
        c = y - timedelta(seconds=(y - x).total_seconds() * phi)
        d = x + timedelta(seconds=(y - x).total_seconds() * phi)
        fc, fd = f(c), f(d)
        if fc is None or fd is None:
            return None
        while (y - x).total_seconds() > tol_seconds:
            if fc >= fd:
                y, d, fd = d, c, fc
                c = y - timedelta(seconds=(y - x).total_seconds() * phi)
                fc = f(c)
            else:
                x, c, fc = c, d, fd
                d = x + timedelta(seconds=(y - x).total_seconds() * phi)
                fd = f(d)
            if fc is None or fd is None:
                return None
        mid = x + (y - x) / 2
        fm = f(mid)
        if fm is None:
            return None
        if fm > best_v + _EPS and lo <= mid < hi:        # a genuine interior maximum above every scan point of the run
            resolved.append((fm, mid))
            continue
        # (2) a plateau / step / exact hint / piece start: the EARLIEST instant that reaches the run's value. A run of
        # several scan points is a plateau (reached to float noise); a single point (an exact hint, the piece start) is
        # reached EXACTLY — a value merely CLOSE to it belongs to the hump's shoulder, not to the peak.
        floor_v = best_v - _EPS if b > a else best_v
        if a > 0:
            l, r = pts[a - 1], pts[a]
            while (r - l).total_seconds() > tol_seconds:
                m = l + (r - l) / 2
                fm2 = f(m)
                if fm2 is None:
                    return None
                if fm2 >= floor_v:
                    r = m
                else:
                    l = m
            best_t = r
        elif b > a:
            best_t = pts[a]
        resolved.append((best_v, best_t))
    top = max(v for v, _ in resolved)
    return top, min(t for v, t in resolved if v >= top - _TIE)


# ── window formation ─────────────────────────────────────────────────────────

def union_components(pieces: Iterable[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Maximal connected unions of half-open intervals; abutting `[a,b)`,`[b,c)` are one set. A gap
    is never bridged."""
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


def intersect_components(xs: list[tuple[datetime, datetime]],
                         ys: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    """Intersection of two lists of DISJOINT, sorted, non-touching half-open components."""
    out: list[tuple[datetime, datetime]] = []
    i = j = 0
    while i < len(xs) and j < len(ys):
        lo, hi = max(xs[i][0], ys[j][0]), min(xs[i][1], ys[j][1])
        if lo < hi:
            out.append((lo, hi))
        if xs[i][1] <= ys[j][1]:
            i += 1
        else:
            j += 1
    return out


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
    objective: str = ""                 # which function the peak maximises (a NAME)
    unqualified_reason: str | None = None
    objective_value: float | None = None   # that function's value at the peak — distinct from `score`
    affected_channels: tuple = ()          # the channels an UNQUALIFIED member feeds (an unknown channel feeds both)
    policy: str = "window_qualification/1"  # the result policy this window was drafted under (R9-1; the manifest's)
    #: R4 (SR-Q6-L1-AMEND): the identity of the combustion authority a P1 grain's states were derived from — the `bg_combustion_orbs` row ids and
    #: content digest, and the L1 combustion module's digest (`p1_operands.P1Operands.combustion_inheritance`). None for every other grain.
    combustion_inheritance: dict | None = None
    solver_certificate: dict | None = None  # R-7: the solver's piece tree (`window_solver.stored_certificate`) — numbered, or a budget-exhausted blank

    def qualification(self) -> dict:
        """The structured provenance persisted with the window (1240 `qualification`; closed keys, plus `combustion_inheritance` for a P1 grain bound
        to the Form B operands and `solver_certificate` for a solved or budget-exhausted window — both admitted by migration 1402)."""
        q = {"policy": self.policy, "unqualified_reason": self.unqualified_reason, "unresolved": dict(sorted(self.unresolved.items())),
             "affected_channels": sorted(self.affected_channels), "members": self.members,
             "qualified_members": self.qualified_members}
        if self.combustion_inheritance is not None:
            q["combustion_inheritance"] = self.combustion_inheritance
        if self.solver_certificate is not None:
            q["solver_certificate"] = self.solver_certificate
        return q


#: R8-4/R8-6 (RETIRED for the writer by S3): a window with a qualified function-valued member used to be unqualified under this named reason
#: until a solver with a stated global-maximum guarantee existed. The writer now passes `solver=PRODUCTION_SOLVER` and the window is SOLVED (a
#: certified number) or blank under one of the solver's named reasons (`window_qualification_table/2`, rule 2). The switch still answers a caller
#: that supplies NEITHER `solver` nor `allow_dynamic` (so a stale caller blanks rather than numbers), and `allow_dynamic=True` stays as the LEGACY
#: SAMPLER (`maximise_earliest`) that the solver's tests use as a weak oracle; the writer never passes it.
DYNAMIC_SWITCH_REASON = "dynamic_objective_solver_guarantee_not_available"

#: the audited minimum spacing of two consecutive Swiss stations of one body (Mercury, 19.7585 d: S0 §2.3, `window_verifier._junction_problem`), rounded DOWN —
#: the premise of the solver's H1 (a hidden reversal pair cannot fit between samples taken at most 5 d apart)
AUDITED_MIN_STATION_SPACING_S = 19.75 * 86400.0


@dataclass(frozen=True)
class SolverConfig:
    """How the sweep calls the window solver. The budget is PER WINDOW only (R-6: no grain-level budget, so no order dependence)."""
    max_evals: int = _solver.MAX_EVALS_WINDOW
    min_station_spacing_s: float = AUDITED_MIN_STATION_SPACING_S
    fd_half_seconds: float = 30.0          # the centred-difference half-width of the speed when the record carries no speed seam


PRODUCTION_SOLVER = SolverConfig()


def _wrap180(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def _kinematics(rec: "SweepRecord", origin: datetime, cfg: SolverConfig):
    """`s (seconds from origin) -> (longitude deg, speed deg/s)` for the record's body: ONE ephemeris call when the record carries the speed seam (deg/day), else a centred
    difference of `longitude_at`. The last few instants are memoised so the solver's offset and velocity reads of one instant cost one evaluation."""
    cache: dict = {}

    def at(s: float):
        got = cache.get(s)
        if got is None:
            t = origin + timedelta(seconds=s)
            if rec.longitude_speed_at is not None:
                lon, per_day = rec.longitude_speed_at(t)
                spd = None if per_day is None else float(per_day) / 86400.0
            else:
                h = timedelta(seconds=cfg.fd_half_seconds)
                lon = rec.longitude_at(t)
                a, b = rec.longitude_at(t - h), rec.longitude_at(t + h)
                spd = None if a is None or b is None else _wrap180(float(b) - float(a)) / (2.0 * cfg.fd_half_seconds)
            if lon is None or spd is None:
                raise SweepRefusal(f"record {rec.record_id}: the ephemeris seam returned no longitude/speed at {t.isoformat()} — refused, never defaulted")
            if len(cache) > 16:
                cache.clear()
            got = cache[s] = (float(lon), float(spd))
        return got
    return at


def _solver_steps(p: "RecordProgram", origin: datetime) -> list:
    """The record's non-tent factors as solver steps: constants, state-valued functions (their own change instants, completeness and named reasons), and the
    per-instant channel as a 1/0 multiplier (a record on the against side adds nothing to the for-sum)."""
    def at(s: float) -> datetime:
        return origin + timedelta(seconds=s)

    def secs(t: datetime) -> float:
        return (t - origin).total_seconds()

    steps: list = []
    for o in p.outcomes:
        if o.kind == "na":
            continue
        if o.kind == "missing":
            if o.null_state == OMIT:
                continue
            raise SweepRefusal(f"record {p.rec.record_id}: a qualified record carries a missing operand {o.factor!r} (null_state {o.null_state!r}) — refused")
        if o.kind == "const":
            steps.append(_solver.constant_step(o.value))
            continue
        if o.tent is not None:
            continue
        steps.append(_solver.Step(
            value_at=lambda s, _o=o: _o.fn(at(s)),
            boundaries=None if o.boundaries is None else (lambda lo_s, hi_s, _o=o: [secs(c) for c in _o.boundaries(at(lo_s), at(hi_s))]),
            complete=bool(o.boundaries_complete),
            unknown_reason=None if o.unknown_reason is None else (lambda s, _o=o: _o.unknown_reason(at(s)))))
    decider = next((o for o in p.outcomes if o.channel_at is not None), None)
    if decider is not None:
        steps.append(_solver.Step(
            value_at=lambda s: (lambda c: None if c is None else (1.0 if c == CHANNEL_FOR else 0.0))(p.channel_at(at(s))),
            boundaries=None if decider.boundaries is None else (lambda lo_s, hi_s, _o=decider: [secs(c) for c in _o.boundaries(at(lo_s), at(hi_s))]),
            complete=bool(decider.boundaries_complete),
            unknown_reason=None if decider.unknown_reason is None else (lambda s, _o=decider: _o.unknown_reason(at(s)))))
    return steps


def solver_problem(path_id: str, programs: list, lo: datetime, hi: datetime, cfg: SolverConfig):
    """The `window_solver.Problem` for ONE window: the qualified members' factors, time in seconds from `lo`. A point-kernel record becomes one tent member per
    directed ray (the kernel is the best ray: a max inside the record's root/agent group); a record on the against channel is not a member of a for-channel
    objective. Pure: the only ephemeris contact is through the records' own seams."""
    origin = lo
    L = (hi - lo).total_seconds()
    members: list = []
    for p in programs:
        rec = p.rec
        if not p.has_channel_fn and p.channel == CHANNEL_AGAINST:
            continue
        steps = tuple(_solver_steps(p, origin))
        supports = tuple(((a - origin).total_seconds(), (b - origin).total_seconds()) for a, b in rec.supports)
        group = rec.agent if path_id == "P4" else rec.root_id
        tent_o = next((o for o in p.outcomes if o.tent is not None), None)
        if tent_o is None:
            members.append(_solver.Member(key=rec.record_id, group=group, supports=supports, steps=steps))
            continue
        level, orb = tent_o.tent
        at = _kinematics(rec, origin, cfg)
        # a station just OUTSIDE the window still leaves its noise comb in the window's end (SR-NEAR-STATION-TIE): listed within NEAR_STATION_S of it
        # (the solver cuts only at the ones inside; the others only mark a zone)
        stations = () if rec.station_instants is None else tuple(sorted((t - origin).total_seconds() for t in rec.station_instants()
                                                                        if -_solver.NEAR_STATION_S <= (t - origin).total_seconds() <= L + _solver.NEAR_STATION_S))
        for k, ray in enumerate(rec.aspect_rays or (None,)):
            shift = 0.0 if ray is None else float(ray)
            members.append(_solver.Member(
                key=f"{rec.record_id}#{k}", group=group, supports=supports, steps=steps,
                tent=_solver.Tent(offset=lambda s, _a=at, _sh=shift, _lv=level: _wrap180(_a(s)[0] + _sh - _lv), orb=orb,
                                  velocity=lambda s, _a=at: _a(s)[1], stations=stations,
                                  min_station_spacing=cfg.min_station_spacing_s)))
    return _solver.Problem(lo=0.0, hi=L, objective=_solver.OBJECTIVE_MINMAX if path_id == "P4" else _solver.OBJECTIVE_SUM, members=tuple(members))

OBJECTIVE_P4 = "max_min_agent_activity"          # S:321-323, O-RP-3
OBJECTIVE_EVIDENCE = "evidence_for_per_root_sum"  # Σ over roots of the per-root max, for-channel


def _contains(supports, t: datetime) -> bool:
    return any(lo <= t < hi for lo, hi in supports)


def _overlaps(supports, lo: datetime, hi: datetime) -> bool:
    return any(a < hi and b > lo for a, b in supports)


def _program_channel(event_class: str, rec: SweepRecord, qualified: bool) -> str | None:
    """The record's channel, or None when it cannot be known (an UNQUALIFIED record whose channel
    is not determinable — it then affects BOTH channels). A QUALIFIED record must have one."""
    try:
        return record_channel(event_class, rec)
    except SweepRefusal:
        if qualified:
            raise
        return None


def _known_nowhere(prog: "RecordProgram", a: datetime, b: datetime, samples: int = 24) -> bool:
    """True iff the record's value is undeterminable at EVERY sampled instant of `[a, b)` — then the
    record itself is unqualified (§2.1). A value known somewhere but unknown elsewhere stays qualified:
    the unknown portion is handled where it matters, in the objective (an unknown piece ⇒ unqualified)."""
    span = (b - a).total_seconds()
    return all(prog.value_at(a + timedelta(seconds=span * k / samples)) is None for k in range(samples))


def _named_reason_everywhere(prog: "RecordProgram", supports, samples: int = 24) -> str | None:
    """The ONE reason the record's factors name for the operand being undeterminable at every sampled instant of `supports` (P1a: a node
    in a sign the verse reserves, `node_dignity_unclassified`; a Mercury / Venus without stored stations); None when no factor names one or
    the names differ — the generic reason then stands, a reason is never picked among several."""
    seen: set = set()
    for a, b in supports:
        span = (b - a).total_seconds()
        for k in range(samples):
            seen.add(prog.unknown_reason_at(a + timedelta(seconds=span * k / samples)))
    return next(iter(seen)) if len(seen) == 1 and None not in seen else None


def _pieces(lo: datetime, hi: datetime, progs: list[RecordProgram]):
    """Elementary pieces of [lo, hi): between consecutive support endpoints the live set is constant."""
    cuts = {lo, hi}
    for p in progs:
        for a, b in p.rec.supports:
            if a < hi and b > lo:
                cuts.add(max(a, lo))
                cuts.add(min(b, hi))
                # R7 [7]: the EXACT instants at which an operand's state changes inside the support — the record-wide
                # list and, W0, each factor's own
                providers = ([] if p.rec.state_boundaries is None else [p.rec.state_boundaries]) + \
                    [o.boundaries for o in p.outcomes if o.boundaries is not None]
                for provider in providers:
                    cuts.update(c for c in provider(max(a, lo), min(b, hi)) if lo < c < hi)
    ordered = sorted(cuts)
    return [(a, b, [p for p in progs if _contains(p.rec.supports, a)])
            for a, b in zip(ordered, ordered[1:])]


def reduce_at(progs: list[RecordProgram], t: datetime, event_class: str) -> dict:
    """The per-channel root reduction at instant `t` — Stream B's `score.path_channel_scores` CALLED
    (never copied): per root the max over its aliases, Σ over roots, channel-preserving, and — the
    Codex round 6 R1 repair — QUALIFICATION PROPAGATES: a channel any live record could not evaluate
    is None, never a complete-looking subtotal (`known_partial_subtotals` are lower bounds and are not
    stored). `progs` are the members live at `t`; an unqualified member, or one whose operand is
    undeterminable at `t`, carries its channel (None = unknown ⇒ both)."""
    from services.gochara_rules import score as _score
    evals: dict[str, dict] = {}
    for p in progs:
        v = p.value_at(t) if p.qualified else None
        ch = p.channel_at(t)               # W0: per instant when a factor decides the side, else the static channel
        if p.qualified and v is not None and ch in _score.CHANNELS:
            evals[p.rec.record_id] = {c: (v if c == ch else 0.0) for c in _score.CHANNELS}
        else:
            ev = {"unqualified": True,
                  "unqualified_reasons": [r for _f, r in p.reasons]
                  or [p.unknown_reason_at(t) or "operand_undeterminable_at_instant"]}
            if ch in _score.CHANNELS:
                ev["unqualified_channel"] = ch
            evals[p.rec.record_id] = ev
    return _score.path_channel_scores([p.rec for p in progs], event_class, evals)


def _agent_activity(live: list[RecordProgram], agent: str, t: datetime) -> float | None:
    """act_g(t) = max over agent g's live admitted records of the within-path product (the reduction
    P4's frozen max-min objective is taken over; max, not Σ: one strong contact suffices — union
    semantics, and it stays in [0,1]). None when ANY of the agent's live records is unknown at `t`."""
    vals = [p.value_at(t) for p in live if p.rec.agent == agent]
    if not vals or any(v is None for v in vals):
        return None          # R8-6: an unknown record is never dropped before the max — the true maximum may be ITS value
    return max(vals)


UNKNOWN_OVER_COMPONENT = "objective_unknown_over_component"


def _noting_unknown(f, live: list[RecordProgram], seen: set):
    """`f` unchanged, plus: whenever it is undeterminable at t, the named reasons the live records' factors give for t are
    added to `seen` (W0 reason pass-through). It adds no evaluation of `f` and changes none of its values."""
    def noted(t):
        v = f(t)
        if v is None:
            seen.update(r for p in live if p.undeterminable_at(t) for r in [p.unknown_reason_at(t)] if r is not None)
        return v
    return noted


def _objective_fn(path_id: str, live: list[RecordProgram], event_class: str):
    if path_id == "P4":
        def f(t, _l=live):
            j, s = _agent_activity(_l, "jupiter", t), _agent_activity(_l, "saturn", t)
            return None if j is None or s is None else min(j, s)
    else:
        def f(t, _l=live):
            return reduce_at(_l, t, event_class)[CHANNEL_FOR]     # None = the objective is unqualified at t
    return f


def draft_windows(event_class: str, records: list[SweepRecord],
                  factor_rows_for: Callable[[str, str], list[dict]], *,
                  drishti: Callable[[str, int, tuple], float] | None = None,
                  vedha: Callable[[SweepRecord, datetime], float | None] | None = None,
                  compute_valence: Callable | None = None,
                  allow_dynamic: bool = False,
                  solver: SolverConfig | None = None,
                  policy: str = POLICY_QUALIFICATION,
                  combustion_inheritance: dict | None = None,
                  window_solver: Callable[[dict], object] | None = None) -> tuple[list[WindowDraft], dict]:
    """The grain's windows (one path-version) and an exclusion ledger — every record accounted.

    Window construction (Codex round 6, R3): ONE window per MAXIMAL CONNECTED COMPONENT of the
    prerequisite-satisfied support, never bridging a gap. For every path but P4 that support is the
    union of the admitted scored records' supports; for P4 it is the INTERSECTION of Jupiter's and
    Saturn's influence unions (a window exists only where both are active). Members are the admitted
    records OVERLAPPING the window (a P4 record may extend past it).

    The peak maximises a NAMED objective and takes its earliest attained maximum: P4 — the frozen
    max-min `min(act_Jupiter, act_Saturn)`; every other path — `evidence_for` = Σ over roots of the
    per-root max for-channel value. `score` = the max live for-channel product at the peak (P4: the
    max-min value itself); evidence per channel at the peak, never netted.

    RESULT POLICY (R9-1). `policy` is the one the generation's MANIFEST selected (`result_policy`):
    `all_null_candidate/1` — EVERY window carries no number at all (score, evidence_for, evidence_against,
    objective_value, severity NULL; peak absent; valence `unqualified`; reason `all_null_candidate_policy`) for every
    path and channel composition, constant objectives and empty sums included; the interval, members, record ids and
    accounting counts stay populated and the per-member classification below still fills `unresolved`.
    `window_qualification/1` — the table that follows, which applies when numbers are enabled.

    QUALIFICATION POLICY (frozen, `window_qualification/1`; the independent verifier implements the same table
    from its own code). Members = admitted scored records overlapping the component; each has a channel
    (for / against / unknown) and is qualified or not:
      1. an UNQUALIFIED member whose channel is `for` or unknown ⇒ the objective is unqualified: peak, score,
         evidence_for and evidence_against are NULL (reason = the first unresolved reason, sorted);
      2. else, a QUALIFIED FUNCTION-VALUED member ⇒ the window is SOLVED by the certified solver (`solver=`, `window_qualification_table/2`):
         a proven global maximum and its earliest tie instant, or no number and a named solver reason (`window_solver` reasons). A caller that passes
         neither `solver` nor the legacy sampler (`allow_dynamic`) is answered with the retired switch `dynamic_objective_solver_guarantee_not_available`;
      3. else the objective Σ-over-roots-of-the-per-root-max FOR-channel value is determined — a population with
         no for-channel member (against-only) has the identically-zero objective, whose earliest maximum is the
         component start — and `peak`, `evidence_for` are stored;
      4. `score` = the max LIVE record product at the peak over ALL live members of any channel (P4: the
         max-min value); NULL when a live member at the peak is unqualified (its product is unknown);
      5. `evidence_against` is the per-instant against reduction at the peak: NULL iff the path cannot
         evaluate it, or a live unqualified against/unknown-channel member could feed it.
    Admission and admitted support are unchanged; known partial subtotals are never stored as complete.

    SOLVER SEAM (R-6/R-7). `window_solver`, when given, solves a component that has a function-valued qualified member INSTEAD of the piece
    sampler and lifts the dynamic switch for it. It is called with {path_id, lo, hi, objective, members (the qualified programs), event_class}
    and returns an object with `.status` ('solved' | 'blank'), `.value`, `.instant` (an aware datetime), `.reason` and `.certificate` (the JSON
    object `window_solver.stored_certificate` builds, or None). The budget is the callable's and is PER WINDOW: nothing is shared between
    components, so an exhausted window never blanks the next. A blank outcome is a named blank (reason, `unresolved[reason] = 1`, unqualified
    valence) that carries its certificate; a solved one flows through the common tail below with its certificate attached. The adapter that
    turns programs into the solver's problem is the integration's (S3)."""
    from services.gochara_rules import valence as _valence_mod
    valence_fn = compute_valence or _valence_mod.compute_valence
    if policy not in RESULT_POLICIES:
        raise SweepRefusal(f"result policy {policy!r} is not one of {RESULT_POLICIES}")
    if sum(x for x in (solver is not None, allow_dynamic, window_solver is not None)) > 1:
        raise SweepRefusal("`solver`, `allow_dynamic` (the legacy sampler) and `window_solver` (the callable seam) are mutually exclusive — a window is numbered by exactly one engine")

    excluded = {"not_admitted": 0, "admission_unqualified": 0, "testimony": 0, "no_support": 0}
    members: list[SweepRecord] = []
    keys = {(r.path_id, r.rule_version) for r in records}
    if len(keys) > 1:
        raise SweepRefusal(f"a window grain is one path-version; got {sorted(keys)}")
    for r in records:
        if r.path_id not in SWEEP_PATHS:
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
    # The against channel is EVALUATED when the path assigns a direction per record (P2), or when
    # its registry row declares no against-channel operand at all (empty sum = 0.0). A declared or
    # ambiguous row leaves it NULL — derived from the row, never from the path's name.
    # P1B: P1's rows DECLARE the operand (agent_nature: benefic → favourable channel, malefic → adverse) and the sweep now places
    # every qualified P1 record in a channel per instant (`record_channel` refuses a P1 record no factor places), so a declared
    # operand on a categorical path is EVALUATED; an unqualified member whose side is unknown still makes the sum unqualified
    # (`against_unq`). An ambiguous row stays NULL.
    against_evaluated = (path_id in DIRECTIONAL_PATHS or against_channel_state(factor_rows) == "none_declared"
                         or (path_id in CATEGORICAL_PATHS and against_channel_state(factor_rows) == "declared"))
    programs = {r.record_id: build_program(r, factor_rows, drishti=drishti, vedha=vedha)
                for r in members}
    # A record whose operand is undeterminable over its WHOLE support is unqualified — never a 0.0
    # (§2.1: a missing operand takes its null_state).
    for prog in programs.values():
        if prog.qualified and prog.constant is None:
            if all(_known_nowhere(prog, a, b) for a, b in prog.rec.supports):
                prog.qualified = False
                prog.null_states.add(UNQUALIFIED)
                prog.reasons.append(("operand", _named_reason_everywhere(prog, prog.rec.supports) or "operand_undeterminable_over_support"))
    for prog in programs.values():
        # W0: a record whose side is decided per instant by a factor has no static channel (None = both, for an
        # unqualified one); every other record's channel is the static `record_channel`
        prog.channel = None if prog.has_channel_fn else _program_channel(event_class, prog.rec, prog.qualified)

    if path_id == "P4":
        by_agent: dict[str, list] = {}
        for r in members:
            if r.agent not in ("jupiter", "saturn"):
                raise SweepRefusal(f"P4 record on agent {r.agent!r} — O-RP-3 violated upstream")
            by_agent.setdefault(r.agent, []).extend(r.supports)
        if set(by_agent) != {"jupiter", "saturn"}:
            return [], excluded            # a double transit needs both agents: no joint support
        components = intersect_components(union_components(by_agent["jupiter"]),
                                          union_components(by_agent["saturn"]))
    else:
        components = union_components(p for r in members for p in r.supports)

    objective_name = OBJECTIVE_P4 if path_id == "P4" else OBJECTIVE_EVIDENCE
    drafts: list[WindowDraft] = []
    for lo, hi in components:
        in_win = [programs[r.record_id] for r in members if _overlaps(r.supports, lo, hi)]
        if not in_win:
            raise SweepRefusal("component without a member record — support invariant violated")
        unresolved: dict = {}
        null_states: set = set()
        for prog in in_win:
            null_states |= prog.null_states
            for reason in {r for _f, r in prog.reasons}:     # records per reason, not factor-misses
                unresolved[reason] = unresolved.get(reason, 0) + 1
        ids = tuple(sorted(p.rec.record_id for p in in_win))
        affected = sorted({c for p in in_win if not p.qualified
                           for c in ((CHANNEL_FOR, CHANNEL_AGAINST) if p.channel is None else (p.channel,))})
        base = dict(interval=(lo, hi), severity=None, record_ids=ids,
                    null_states_used=sorted(null_states), unresolved=unresolved,
                    members=len(in_win), qualified_members=sum(1 for p in in_win if p.qualified),
                    objective=objective_name, affected_channels=tuple(affected))
        if policy == POLICY_ALL_NULL:
            # R9-1: the numeric result is NOT produced at all — decided before any objective is evaluated, so a
            # constant objective, an empty for-channel sum or an all-against population cannot store a number
            val = valence_fn(event_class, 0.0, 0.0, ALL_NULL_REASON)
            drafts.append(WindowDraft(
                peak_instant=None, score=None, evidence_for=None, evidence_against=None,
                outcome_valence_for_native=val.outcome_valence_for_native,
                unqualified_reason=ALL_NULL_REASON, **base))
            continue
        for_unq = [p for p in in_win if not p.qualified and p.channel in (CHANNEL_FOR, None)]
        against_unq = [p for p in in_win if not p.qualified and p.channel in (CHANNEL_AGAINST, None)]
        if for_unq:
            first = sorted(unresolved)[0] if unresolved else "unqualified_member"
            val = valence_fn(event_class, 0.0, 0.0, first)
            drafts.append(WindowDraft(
                peak_instant=None, score=None, evidence_for=None, evidence_against=None,
                outcome_valence_for_native=val.outcome_valence_for_native,
                unqualified_reason=first, **base))
            continue

        qualified = [p for p in in_win if p.qualified]
        use_solver = solver is not None and any(p.constant is None for p in qualified)
        if not allow_dynamic and solver is None and window_solver is None and any(p.constant is None for p in qualified):
            n_dyn = sum(1 for p in qualified if p.constant is None)
            unresolved[DYNAMIC_SWITCH_REASON] = n_dyn
            base["unresolved"] = unresolved
            val = valence_fn(event_class, 0.0, 0.0, DYNAMIC_SWITCH_REASON)
            drafts.append(WindowDraft(
                peak_instant=None, score=None, evidence_for=None, evidence_against=None,
                outcome_valence_for_native=val.outcome_valence_for_native,
                unqualified_reason=DYNAMIC_SWITCH_REASON, **base))
            continue
        cands: list[tuple[float, datetime]] = []
        unknown_pieces = 0
        reason_pieces: dict[str, int] = {}     # W0: unknown pieces per NAMED reason a factor passed through
        unnamed_pieces = 0                     # unknown pieces no factor gave a reason for
        solver_certificate = None
        solved_by_solver = False
        if window_solver is not None and any(p.constant is None for p in qualified):
            out = window_solver({"path_id": path_id, "lo": lo, "hi": hi, "objective": objective_name, "members": qualified,
                                 "event_class": event_class})
            solver_certificate = out.certificate
            if out.status != "solved":
                if not out.reason:
                    raise SweepRefusal("the window solver returned a blank without a reason")
                base["unresolved"] = {**unresolved, out.reason: 1}
                val = valence_fn(event_class, 0.0, 0.0, out.reason)
                drafts.append(WindowDraft(
                    peak_instant=None, score=None, evidence_for=None, evidence_against=None,
                    outcome_valence_for_native=val.outcome_valence_for_native,
                    unqualified_reason=out.reason, solver_certificate=solver_certificate, **base))
                continue
            cands.append((out.value, out.instant))
            solved_by_solver = True
        for a, b, live in (() if solved_by_solver else _pieces(lo, hi, qualified)):
            if path_id == "P4":
                if {p.rec.agent for p in live} != {"jupiter", "saturn"}:
                    continue               # outside the joint support within this piece: not a candidate
            elif not live:
                if not use_solver:
                    cands.append((0.0, a))     # no for-channel contributor: the objective is identically 0 here (the solver models it the same way)
                continue
            # membership comes from the CONTACT GEOMETRY across the whole component, not only at the
            # chosen peak (R7 [8]): at every piece start, and just inside its end, a live member's
            # geometry must not place the target outside its stored support; an undeterminable
            # geometry makes the piece unknown (never affirmative membership)
            geometry_unknown = False
            for p in live:
                for check in p.checks:
                    for instant, side in ((a, "start"), (b - timedelta(microseconds=1), "end")):
                        g = _geometry_at_edge(check, instant, side, a, b)
                        if g is False:
                            raise SweepRefusal(
                                f"record {p.rec.record_id}: its stored support contains {instant.isoformat()} "
                                "but the contact geometry places the target outside — support/geometry disagree")
                        if g is None:
                            geometry_unknown = True
            if geometry_unknown:
                unknown_pieces += 1
                unnamed_pieces += 1
                continue
            f = _objective_fn(path_id, live, event_class)
            seen: set = set()
            if any(o.unknown_reason is not None for p in live for o in p.outcomes):
                # W0 reason pass-through: at every instant the objective is unknown, ask the live factors why
                f = _noting_unknown(f, live, seen)
            if use_solver:
                # S3: the objective's MAXIMUM over the whole component is the solver's; this loop keeps the geometry checks above and the legacy
                # per-piece UNKNOWN classification (an operand undeterminable at a piece's start, with the factor's own named reasons), so a
                # blank window's reasons and counts are exactly what the independent verifier derives
                v = f(a)
                got = None if v is None else (v, a)
                if got is not None:
                    continue
            elif all(p.constant is not None for p in live):
                v = f(a)
                got = None if v is None else (v, a)
            else:
                hints = [h for p in live if p.rec.peak_hints is not None for h in p.rec.peak_hints(a, b)]
                got = maximise_earliest(f, a, b, hints=hints)
            if got is None:
                unknown_pieces += 1
                if seen:
                    for reason in seen:
                        reason_pieces[reason] = reason_pieces.get(reason, 0) + 1
                else:
                    unnamed_pieces += 1
            else:
                cands.append(got)
        solved = None
        if use_solver and not unknown_pieces:
            problem = solver_problem(path_id, qualified, lo, hi, solver)
            try:
                res = _solver.solve(problem, max_evals=solver.max_evals)
            except _solver.SolverRefusal as exc:
                raise SweepRefusal(f"window {lo.isoformat()}: {exc}") from exc
            # R-7 (the one engine): the certificate is the piece tree of THIS solve, named by the solver's own objective (the migration admits `sum_of_group_max` /
            # `min_of_group_max`, not the sweep's `objective_name`); None for a blank that has no tree (only budget exhaustion keeps one)
            solver_certificate = _solver.stored_certificate(res, objective=problem.objective, t0_iso=lo.isoformat(), max_evals=solver.max_evals)
            if res.status == _solver.BLANK:
                unknown_pieces, unnamed_pieces = 1, 0
                reason_pieces = {res.reason: 1}
            else:
                solved = (res.value, lo + timedelta(seconds=res.instant))
                if not lo <= solved[1] < hi:
                    raise SweepRefusal(f"window {lo.isoformat()}: the solver's instant {solved[1].isoformat()} lies outside the window")
        if unknown_pieces or (solved is None and not cands):
            # R7 [1]: a peak is qualified only when the objective's maximum AND its earliest maximising
            # instant are established over the ENTIRE component — an unknown portion is never dropped
            if reason_pieces:
                # W0: the factors' own reasons are carried through; the generic one stays only for pieces none named
                for reason, n in reason_pieces.items():
                    unresolved[reason] = unresolved.get(reason, 0) + n
                if unnamed_pieces:
                    unresolved[UNKNOWN_OVER_COMPONENT] = unnamed_pieces
                first = sorted(reason_pieces)[0]
            else:
                first = UNKNOWN_OVER_COMPONENT if unknown_pieces else "objective_undeterminable"
                unresolved[first] = unknown_pieces or 1
            base["unresolved"] = unresolved
            val = valence_fn(event_class, 0.0, 0.0, first)
            drafts.append(WindowDraft(
                peak_instant=None, score=None, evidence_for=None, evidence_against=None,
                outcome_valence_for_native=val.outcome_valence_for_native,
                unqualified_reason=first, solver_certificate=solver_certificate, **base))
            continue
        if solved is not None:
            best, peak = solved
        else:
            best = max(v for v, _ in cands)
            peak = min(t for v, t in cands if v >= best - _TIE)
        live_at_peak = [p for p in in_win if _contains(p.rec.supports, peak)]
        red = reduce_at(live_at_peak, peak, event_class)
        ev_for = red[CHANNEL_FOR]
        if ev_for is None:                     # cannot happen when the objective qualified; refuse, don't guess
            raise SweepRefusal("for-channel evidence unqualified at a peak chosen on a qualified objective")
        if path_id == "P4":
            score = best
        else:
            # the max LIVE record product at the peak over ALL live members (any channel); a live unqualified
            # member's product is unknown, so the maximum is not established
            live_prods = [p.value_at(peak) if p.qualified else None for p in live_at_peak]
            score = None if any(v is None for v in live_prods) else max(live_prods, default=0.0)
        ev_against = red[CHANNEL_AGAINST] if against_evaluated else None
        if ev_against is not None:
            val = valence_fn(event_class, ev_for, ev_against, None)
        else:
            val = valence_fn(event_class, ev_for, 0.0,
                             "evidence_against_channel_not_evaluated" if not against_unq
                             else "evidence_against_channel_unqualified")
        drafts.append(WindowDraft(
            peak_instant=peak, score=score, evidence_for=ev_for, evidence_against=ev_against,
            outcome_valence_for_native=val.outcome_valence_for_native, objective_value=best,
            solver_certificate=solver_certificate, **base))
    drafts = [d if d.policy == policy else dataclasses.replace(d, policy=policy) for d in drafts]
    if combustion_inheritance is not None:        # R4: every window of the grain carries the identity of the combustion authority it consumed
        drafts = [dataclasses.replace(d, combustion_inheritance=combustion_inheritance) for d in drafts]
    return drafts, excluded


#: SR-NEAR-STATION-TIE (madhav-44): the share of ALL windows that may be blanked by the station-zone tie rule before the run must stop and tell the surrogate:
#: 0.5 %, compared in integers (`blanked × 1000 > windows × 5`) like the gate's INCONCLUSIVE cap. The harness-side refusal is the cockpit's; this is its number.
NEAR_STATION_TIE_CAP_PER_MILLE = 5
NEAR_STATION_TIE_SCHEMA = "near_station_tie_blanked/1"


def near_station_tie_report(drafts_by_class: Mapping[str, Sequence[WindowDraft]]) -> dict:
    """SR-NEAR-STATION-TIE: how many windows the builder blanked under `tie_isolation_unresolved` (the solver's station-zone rule), per class and in all.
    `drafts_by_class` maps a class label (the caller's: event class, path-version…) to the drafts `draft_windows` returned for it. The count is READ FROM THE
    DRAFTS' OWN `unqualified_reason` — the stored rows themselves, not a side counter — so it reads false when no window carries the reason. The named field
    is `near_station_tie_blanked`; `cap_exceeded` is the 0.5 % test over all the windows given (a numbered window the VERIFIER later demotes under the same
    reason is counted by the gate's `demoted`, not here)."""
    per_class = {}
    for cls in sorted(drafts_by_class):
        ds = list(drafts_by_class[cls])
        per_class[cls] = {"windows": len(ds), "blanked": sum(1 for d in ds if d.unqualified_reason == _solver.REASON_TIE_ISOLATION)}
    windows = sum(v["windows"] for v in per_class.values())
    blanked = sum(v["blanked"] for v in per_class.values())
    return {"schema": NEAR_STATION_TIE_SCHEMA, "rule": "SR-NEAR-STATION-TIE", "near_station_tie_blanked": blanked, "windows": windows,
            "per_class": per_class, "cap_per_mille": NEAR_STATION_TIE_CAP_PER_MILLE,
            "cap_exceeded": blanked * 1000 > windows * NEAR_STATION_TIE_CAP_PER_MILLE}


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
    "CHANNEL_AGAINST", "CHANNEL_FOR", "DIRECTIONAL_PATHS", "ALL_NULL_REASON", "POLICY_ALL_NULL", "POLICY_QUALIFICATION", "STATE_BOUNDARIES_REASON", "STATE_VALUED_FACTORS", "FOR_ONLY_PATHS", "Outcome",
    "RecordProgram", "SWEEP_PATHS", "SweepRecord", "SweepRefusal", "WindowDraft",
    "activity_kernel", "against_channel_state", "build_program", "draft_windows",
    "CATEGORICAL_PATHS", "DYNAMIC_SWITCH_REASON", "GRAHA_TITLE", "KIND_TARGET_FORM", "OperandSource", "UNKNOWN_OVER_COMPONENT", "categorical_factor", "graha_title",
    "validate_geometry", "p2_direction", "record_channel", "vedha_attenuation",
    "evaluate_factors", "graduated_drishti", "intersect_components", "maximise_earliest",
    "reduce_at", "registry_factor_rows", "union_components", "near_station_tie_report", "NEAR_STATION_TIE_CAP_PER_MILLE", "NEAR_STATION_TIE_SCHEMA",
]
