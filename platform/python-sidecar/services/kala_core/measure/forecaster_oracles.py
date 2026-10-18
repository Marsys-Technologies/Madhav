"""Measured K1/K2/K3/K6 endpoints (concept note v1.1 §6.6).

(I) INTERPRETATION: callers predeclare endpoint and minimum_n. These descriptive
comparisons report their sample size and no inferential significance. No test
fixture is a scientific result; production starts with not_evaluable.
K4/K5 are structural correctness oracles, deliberately outside this report.

(I) INTERPRETATION: K2 remains not_evaluable until a predeclared
probability-conditional reliability detector is bound to Samiksha's Brier
eligibility predicate. Pooled signed bias cannot establish reliability, and
prospective/exposure/censoring declarations alone do not supply that detector.
"""
import math
from statistics import fmean
from . import Verdict


def interval_score(lower, upper, observed, alpha):
    if not all(math.isfinite(x) for x in (lower, upper, observed, alpha)) or lower > upper or not 0 < alpha < 1:
        raise ValueError('finite ordered bounds and nominal miscoverage in (0,1) required')
    return upper - lower + (2 / alpha) * max(lower - observed, observed - upper, 0.)


def _result(verdict, reason, n=0, value=None, endpoint=None):
    return dict(verdict=verdict, reason=reason, n=n, value=value, endpoint=endpoint,
                interpretation='descriptive_predeclared_endpoint; not a production qualification')


def _measure(key, row):
    endpoint = row.get('endpoint')
    minimum = row.get('minimum_n')
    if not endpoint or type(minimum) is not int or minimum < 1:
        return _result(Verdict.NOT_EVALUABLE, 'predeclared_protocol_required')
    if key == 'K1':
        if row.get('held_out') is not True or row.get('matched_controls') is not True:
            return _result(Verdict.NOT_EVALUABLE, 'held_out_matched_controls_required', endpoint=endpoint)
        pairs = row.get('pairs', [])
        if any(not (0 <= a <= 1 and 0 <= b <= 1) for a,b in pairs):
            raise ValueError('alignment tails must be finite probabilities')
        values = [a-b for a,b in pairs]
    elif key == 'K2':
        if row.get('prospective_issued') is not True or row.get('observation_mask_verified') is not True or row.get('censoring_accounted') is not True:
            return _result(Verdict.NOT_EVALUABLE, 'prospective_issued_exposure_non_events_and_censoring_required', endpoint=endpoint)
        tolerance = row.get('tolerance')
        if tolerance is None or not math.isfinite(tolerance) or not 0 < tolerance < 1:
            raise ValueError('declared reliability tolerance required')
        pairs = row.get('resolved_forecasts', [])
        if any(not 0 <= p <= 1 or type(y) is not int or y not in (0,1) for p,y in pairs):
            raise ValueError('probability and resolved event indicator required')
        return _result(
            Verdict.NOT_EVALUABLE,
            'conditional_reliability_and_samiksha_scoring_required',
            n=len(pairs), endpoint=endpoint,
        )
    elif key == 'K3':
        alpha = row.get('alpha')
        values = [interval_score(lo,hi,y,alpha) - interval_score(blo,bhi,y,alpha)
                  for lo,hi,y,blo,bhi in row.get('intervals', [])]
    else:
        if row.get('observation_mask_verified') is not True or row.get('held_out') is not True:
            return _result(Verdict.NOT_EVALUABLE, 'verified_held_out_observation_mask_required', endpoint=endpoint)
        exposure, events, baseline = row['exposure'], row['events'], row['baseline_rate']
        if not all(math.isfinite(x) for x in (exposure,events,baseline)) or exposure <= 0 or type(events) is not int or events < 0 or baseline <= 0:
            raise ValueError('class-specific finite rate and observed person-time required')
        # minimum_n for rates denotes observed exposure units, stated in endpoint.
        if exposure < minimum:
            return _result(Verdict.INSUFFICIENT_EVIDENCE, 'below_predeclared_exposure', exposure, endpoint=endpoint)
        value = events/exposure - baseline
        return _result(Verdict.PASS if value < 0 else Verdict.FAIL, None, exposure, value, endpoint)
    if not all(math.isfinite(v) for v in values):
        raise ValueError('non-finite measurement')
    if len(values) < minimum:
        return _result(Verdict.INSUFFICIENT_EVIDENCE, 'below_predeclared_minimum_n', len(values), endpoint=endpoint)
    value = fmean(values)
    return _result(Verdict.PASS if value < 0 else Verdict.FAIL, None, len(values), value, endpoint)


def measure_forecaster(evidence):
    answer = {}
    for key in ('K1','K2','K3','K6'):
        try:
            answer[key] = _measure(key, evidence.get(key, {}))
        except (ValueError, TypeError, KeyError, OverflowError):
            answer[key] = _result(Verdict.NOT_EVALUABLE, 'invalid_or_incomplete_measurement')
    return answer
