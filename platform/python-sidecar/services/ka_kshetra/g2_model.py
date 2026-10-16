"""K5-3 G2 candidate mathematics; never selected by the registered G1 writer.

Contract: KSHETRA_G2_BRIEF_v1_0.md. Rates are sums of independently declared
route intensities, not noisy-OR promise or chart-wide suppression. Every operand
and coefficient is source-bound. No seeded parameter or calibrated status lives
here. Times are absolute Julian days and intervals are half-open.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Mapping

from services.kala_core.ontology import CLASS_ROSTER


@dataclass(frozen=True)
class InputValue:
    value: float | None
    state: str
    source: str
    fact_ids: tuple[str, ...]
    slope: float = 0.0  # derivative per day; an explicitly constant operand by default


@dataclass(frozen=True)
class Coefficient:
    key: str
    beta: float
    provenance: str
    origin: str
    preregistration: str | None = None


@dataclass(frozen=True)
class RouteModel:
    route_id: str
    mechanism_ids: tuple[str, ...]
    baseline: InputValue
    baseline_unit: str
    coefficients: tuple[Coefficient, ...]


@dataclass(frozen=True)
class EventModel:
    event_class: str
    model_id: str
    event_process: str
    risk_set_id: str
    eligibility_ref: str
    censoring_ref: str
    routes: tuple[RouteModel, ...]


@dataclass(frozen=True)
class RiskSet:
    risk_set_id: str
    intervals: tuple[tuple[float, float], ...]
    state: str
    source: str


@dataclass(frozen=True)
class RouteCell:
    start: float
    end: float
    terms: Mapping[str, InputValue]


@dataclass(frozen=True)
class Suppression:
    suppression_id: str
    route_id: str
    effect: str
    operand: InputValue


@dataclass(frozen=True)
class Calibration:
    status: str
    model_digest: str
    risk_set_id: str
    event_process: str
    source: str
    evaluation_id: str
    n: int
    interval: tuple[float, float]


@dataclass(frozen=True)
class RouteSegment:
    route_id: str
    start: float
    end: float
    alpha: float
    gamma: float
    contributions: tuple[tuple[str, float], ...]

    def integral(self) -> float:
        width = self.end - self.start
        x = self.gamma * width
        # Factor from the larger endpoint; only exponentiate the final area so
        # intermediate underflow/overflow cannot erase a representable integral.
        log_shape = math.log(-math.expm1(-abs(x)) / abs(x)) if x else 0.0
        return math.exp(self.alpha + max(x, 0.0) + math.log(width) + log_shape)


@dataclass(frozen=True)
class G2Field:
    model_digest: str
    routes: tuple[RouteSegment, ...]
    flags: tuple[str, ...]
    effects: tuple[tuple[str, str, str], ...]
    partial_integral: float | None
    integrated_hazard: float | None
    expected_count: float | None
    probability: float | None
    odds: float | None
    calibration_status: str
    parameter_uncertainty: None = None
    predictive_uncertainty: None = None
    numerical_uncertainty: None = None

    def rate_at(self, jd: float) -> float:
        _finite(jd, 'evaluation time')
        return math.fsum(math.exp(r.alpha + r.gamma * (jd-r.start))
                         for r in self.routes if r.start <= jd < r.end)


def _finite(value: float, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label} must be finite')


def _operand(item: InputValue) -> bool:
    if item.state not in {'evaluated', 'information_unavailable'} or not item.source:
        raise ValueError('input state and source provenance are required')
    _finite(item.slope, 'input slope')
    if item.state == 'information_unavailable':
        if item.value is not None or item.slope != 0:
            raise ValueError('information_unavailable must carry null, never a value')
        return False
    _finite(item.value, 'evaluated input')
    return True


def _interval(start: float, end: float) -> None:
    _finite(start, 'interval start')
    _finite(end, 'interval end')
    if end <= start:
        raise ValueError('interval end must follow start')


def validate_model(model: EventModel) -> None:
    if (model.event_class not in CLASS_ROSTER
            or model.event_process not in {'first_event', 'recurrent', 'span'}
            or not all((model.model_id, model.risk_set_id, model.eligibility_ref, model.censoring_ref))):
        raise ValueError('explicit event model, risk set, eligibility and censoring required')
    if model.event_class == 'psychological_arc' and model.event_process != 'span':
        raise ValueError('psychological_arc is a span, not a point event')
    ids = [r.route_id for r in model.routes]
    if not ids or any(not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError('unique nonempty route identities are required')
    for route in model.routes:
        if (not route.mechanism_ids or len(set(route.mechanism_ids)) != len(route.mechanism_ids)
                or any(not m for m in route.mechanism_ids)):
            raise ValueError('route must cite admitted mechanism identities')
        if route.baseline_unit != 'events/eligible_day':
            raise ValueError('baseline units must be events/eligible_day')
        if _operand(route.baseline) and (route.baseline.value <= 0 or route.baseline.slope != 0):
            raise ValueError('baseline must be a positive sourced constant rate')
        keys = [c.key for c in route.coefficients]
        if len(keys) != len(set(keys)) or any(not k for k in keys):
            raise ValueError('coefficient keys must be unique')
        for c in route.coefficients:
            _finite(c.beta, 'coefficient')
            if not c.provenance or c.origin not in {'declared', 'learned'}:
                raise ValueError('coefficient provenance is required')
            if c.origin == 'learned' and not c.preregistration:
                raise ValueError('learned coefficients require preregistration')


def model_digest(model: EventModel) -> str:
    validate_model(model)
    return hashlib.sha256(json.dumps(asdict(model), sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def build_field(
    model: EventModel, risk: RiskSet, cells: Mapping[str, tuple[RouteCell, ...]],
    suppressions: tuple[Suppression, ...] = (), *, calibration: Calibration | None = None,
) -> G2Field:
    """Evaluate supplied full partitions; no resampling, knot removal or fitting.

    (I) INTERPRETATION: independent cause-specific route rates add. Delays
    translate that route's complete field before risk clipping. Less-favourable
    effects annotate valence and do not assert a smaller occurrence rate.
    Recurrent-event output is an expected count; no Poisson probability is assumed.
    """
    digest = model_digest(model)
    if risk.risk_set_id != model.risk_set_id or not risk.source:
        raise ValueError('risk set must match the explicit model and cite its source')
    if risk.state not in {'evaluated', 'information_unavailable', 'outside_risk_set'}:
        raise ValueError('unknown risk state')
    if risk.state != 'evaluated' and risk.intervals:
        raise ValueError('unavailable/outside risk must not carry eligibility intervals')
    previous = -math.inf
    for start, end in risk.intervals:
        _interval(start, end)
        if start < previous:
            raise ValueError('risk intervals overlap or are unsorted')
        previous = end
    route_ids = {r.route_id for r in model.routes}
    if set(cells) != route_ids:
        raise ValueError('cells must supply every declared route exactly once')
    by_route: dict[str, list[Suppression]] = {r: [] for r in route_ids}
    suppression_ids: set[str] = set()
    for s in suppressions:
        if s.route_id not in route_ids or not s.suppression_id or s.suppression_id in suppression_ids:
            raise ValueError('suppression needs a unique id and an existing route')
        if s.effect not in {'less_favourable', 'delayed', 'reduced_intensity'}:
            raise ValueError('suppression effect must be typed')
        suppression_ids.add(s.suppression_id)
        _operand(s.operand)
        if s.operand.slope != 0:
            raise ValueError('suppression operand must be constant on the supplied partition')
        if s.operand.value is not None:
            if s.effect == 'reduced_intensity' and not 0 <= s.operand.value <= 1:
                raise ValueError('intensity factor must be in [0,1]')
            if s.effect in {'delayed', 'less_favourable'} and s.operand.value < 0:
                raise ValueError('delay/valence operand must be nonnegative')
        by_route[s.route_id].append(s)

    # Validate even unsupported / unavailable classes; malformed input is not a gap.
    for route in model.routes:
        partition = cells[route.route_id]
        if not partition:
            raise ValueError('full route partition is required')
        if any(a < partition[0].start or b > partition[-1].end for a, b in risk.intervals):
            raise ValueError('route partition must cover the eligible horizon before delay')
        previous = None
        for cell in partition:
            _interval(cell.start, cell.end)
            if previous is not None and cell.start != previous:
                raise ValueError('route partition must be contiguous and nonoverlapping')
            previous = cell.end
            if set(cell.terms) != {c.key for c in route.coefficients}:
                raise ValueError('cell terms must match declared coefficient keys')
            for operand in cell.terms.values():
                _operand(operand)
    if model.event_process == 'span' or model.event_class == 'birth_anchor':
        reason = ('birth_anchor_not_forecast' if model.event_class == 'birth_anchor'
                  else 'span_requires_duration_model')
        return G2Field(digest, (), (reason,), (), None, None, None, None, None,
                       'not_evaluable')
    if risk.state == 'information_unavailable':
        return G2Field(digest, (), ('risk:information_unavailable',), (), None, None, None, None, None,
                       'not_evaluable')

    segments, flags, effects = [], [], []
    for route in model.routes:
        if not _operand(route.baseline):
            flags.append(f'{route.route_id}:baseline:information_unavailable')
            continue
        delay, scale = 0.0, 1.0
        for s in sorted(by_route[route.route_id], key=lambda s: s.suppression_id):
            if not _operand(s.operand):
                flags.append(f'{route.route_id}:suppression:{s.suppression_id}:information_unavailable')
                continue
            effects.append((s.suppression_id, route.route_id, s.effect))
            if s.effect == 'delayed':
                delay += s.operand.value
            elif s.effect == 'reduced_intensity':
                scale *= s.operand.value
        for cell in cells[route.route_id]:
            contributions = [('baseline', math.log(route.baseline.value))]
            gamma = 0.0
            for c in route.coefficients:
                operand = cell.terms[c.key]
                if not _operand(operand):
                    flags.append(f'{route.route_id}:{c.key}:information_unavailable')
                    continue  # absence is recorded; no beta*0 substitute or legacy default
                contributions.append((c.key, c.beta * operand.value))
                gamma += c.beta * operand.slope
            if scale == 0:
                continue
            if scale != 1:
                contributions.append(('suppression:reduced_intensity', math.log(scale)))
            alpha = math.fsum(v for _, v in contributions)
            for start, end in risk.intervals:
                left, right = max(start, cell.start+delay), min(end, cell.end+delay)
                if right <= left:
                    continue
                offset = gamma * (left-cell.start-delay)
                adjusted = tuple(contributions) + ((('risk_clip_offset', offset),) if offset else ())
                segments.append(RouteSegment(route.route_id, left, right, alpha+offset, gamma, adjusted))
    segments.sort(key=lambda r: (r.route_id, r.start))
    total = math.fsum(s.integral() for s in segments)
    _finite(total, 'integrated route intensity')
    complete_total = None if flags else total
    integrated_hazard = complete_total if model.event_process == 'first_event' else None
    expected = complete_total if model.event_process == 'recurrent' else None
    probability = odds = None
    calibrated = bool(
        calibration and calibration.status == 'calibrated'
        and calibration.model_digest == digest and calibration.risk_set_id == model.risk_set_id
        and calibration.event_process == model.event_process and calibration.source
        and calibration.evaluation_id and isinstance(calibration.n, int)
        and not isinstance(calibration.n, bool) and calibration.n > 0
        and len(calibration.interval) == 2
        and all(isinstance(t, (int, float)) and math.isfinite(t) for t in calibration.interval)
        and calibration.interval[0] < calibration.interval[1]
        and all(calibration.interval[0] <= a and b <= calibration.interval[1]
                for a, b in risk.intervals)
    )
    if model.event_process == 'recurrent':
        flags.append('recurrent_count_is_not_first_event_odds')
    if calibrated and integrated_hazard is not None and risk.intervals:
        probability = -math.expm1(-integrated_hazard)
        # expm1 avoids cancellation for tiny hazards. An unrepresentable odds
        # value is honestly null, never an Infinity JSON token.
        odds = (math.expm1(integrated_hazard)
                if integrated_hazard <= math.log(float.fromhex('0x1.fffffffffffffp+1023')) else None)
    return G2Field(digest, tuple(segments), tuple(sorted(set(flags))), tuple(effects), total,
                   integrated_hazard, expected, probability, odds,
                   ('not_evaluable' if complete_total is None
                    else 'calibrated' if calibrated else 'uncalibrated'))
