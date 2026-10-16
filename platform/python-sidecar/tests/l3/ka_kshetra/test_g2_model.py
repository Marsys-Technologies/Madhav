"""K5-3: replacement-model semantics, with explicit synthetic test parameters."""
from dataclasses import replace
import math

import pytest

from services.ka_kshetra.g2_model import (
    Calibration, Coefficient, EventModel, InputValue, RiskSet, RouteCell,
    RouteModel, Suppression, build_field, model_digest,
)


def value(number, *, slope=0.0):
    return InputValue(number, 'evaluated', 'fixture:declared-input', ('fact:test',), slope)


def unknown():
    return InputValue(None, 'information_unavailable', 'fixture:missing-input', ())


def model(process='first_event', routes=None):
    return EventModel('marriage', 'fixture:g2:first-marriage:v1', process,
        'fixture:risk:first-marriage', 'fixture:eligible-and-event-free-at-cutoff',
        'fixture:right-censor-at-horizon', tuple(routes or [
            RouteModel('r1', ('m1',), value(0.01), 'events/eligible_day',
                       (Coefficient('count', 0.5, 'fixture:declared-coefficient', 'declared'),)),
        ]))


def risk():
    return RiskSet('fixture:risk:first-marriage', ((100.0, 110.0),), 'evaluated', 'fixture:F2-risk')


def cells():
    return {'r1': (RouteCell(100.0, 105.0, {'count': value(2.0)}),
                   RouteCell(105.0, 110.0, {'count': value(4.0)}))}


def calibration(m, **kwargs):
    params = dict(status='calibrated', model_digest=model_digest(m),
                  risk_set_id=m.risk_set_id, event_process=m.event_process,
                  source='fixture:independent-calibration-report', evaluation_id='fixture:eval',
                  n=100, interval=(100.0, 110.0))
    return Calibration(**(params | kwargs))


def test_unavailable_term_is_absent_flagged_and_never_defaulted():
    f = build_field(model(), risk(), {'r1': (RouteCell(100, 110, {'count': unknown()}),)})
    assert f.routes[0].alpha == pytest.approx(math.log(.01))
    assert f.routes[0].contributions == (('baseline', math.log(.01)),)
    assert 'r1:count:information_unavailable' in f.flags
    assert f.integrated_hazard is None
    assert f.expected_count is None
    assert f.odds is None
    assert f.partial_integral == pytest.approx(.1)


def test_missing_and_explicit_zero_are_distinct():
    with pytest.raises(ValueError, match='terms'):
        build_field(model(), risk(), {'r1': (RouteCell(100, 110, {}),)})
    f = build_field(model(), risk(), {'r1': (RouteCell(100, 110, {'count': value(0)}),)})
    assert not f.flags
    assert f.integrated_hazard == pytest.approx(.1)


def test_no_baseline_or_risk_default_and_no_rate_for_span():
    m = model()
    no_baseline = replace(m, routes=(replace(m.routes[0], baseline=unknown()),))
    assert build_field(no_baseline, risk(), cells()).expected_count is None
    assert build_field(no_baseline, risk(), cells()).integrated_hazard is None
    assert not build_field(no_baseline, risk(), cells()).routes
    no_risk = replace(risk(), state='information_unavailable', intervals=())
    missing = build_field(m, no_risk, cells())
    assert missing.expected_count is missing.integrated_hazard is None
    assert missing.routes == ()
    assert 'risk:information_unavailable' in missing.flags
    span = build_field(model('span'), risk(), cells(), calibration=calibration(model('span')))
    assert span.expected_count is span.odds is None
    assert 'span_requires_duration_model' in span.flags


def test_complete_partition_and_censoring_are_preserved_one_sided():
    f = build_field(model(), replace(risk(), intervals=((102., 108.),)), cells())
    assert [(r.start, r.end) for r in f.routes] == [(102., 105.), (105., 108.)]
    assert f.rate_at(104.999) == pytest.approx(.01 * math.exp(1))
    assert f.rate_at(105) == pytest.approx(.01 * math.exp(2))
    assert f.rate_at(108) == 0
    assert f.integrated_hazard == pytest.approx(3 * .01 * (math.exp(1) + math.exp(2)))


def test_log_linear_input_and_integral_use_full_route_partition():
    c = {'r1': (RouteCell(100, 105, {'count': value(2, slope=.2)}),
                RouteCell(105, 110, {'count': value(0)}))}
    f = build_field(model(), risk(), c)
    assert f.routes[0].gamma == pytest.approx(.1)
    assert f.integrated_hazard == pytest.approx(.01*math.e*math.expm1(.5)/.1 + .05)
    assert f.parameter_uncertainty is f.predictive_uncertainty is None
    assert f.numerical_uncertainty is None  # analytic integration does not measure roundoff


@pytest.mark.parametrize(('alpha', 'gamma', 'expected'), [
    (-750.0, 75.0, 3.571515949077437e-35),
    (-75.0, -75.0, 3.571515949077437e-35),
    (-900.0, 100.0, 0.01),
])
def test_extreme_log_linear_hazard_preserves_representable_integral(alpha, gamma, expected):
    # Synthetic adversarial inputs. References integrate exp(alpha + gamma*t)
    # on [0, 9]; the decreasing case is the first curve reflected in time.
    m = model()
    route = replace(m.routes[0], coefficients=(
        Coefficient('count', 1.0, 'fixture:extreme-integral', 'declared'),
    ))
    m = replace(m, routes=(route,))
    exposure = replace(risk(), intervals=((100.0, 109.0),))
    partition = {'r1': (RouteCell(100.0, 109.0, {
        'count': value(alpha - math.log(0.01), slope=gamma),
    }),)}
    f = build_field(m, exposure, partition, calibration=calibration(m))
    assert f.rate_at(108.0) > 0
    # abs=0 is essential: pytest's default absolute tolerance would accept zero.
    assert f.routes[0].integral() == pytest.approx(expected, rel=1e-12, abs=0)
    assert f.integrated_hazard == pytest.approx(expected, rel=1e-12, abs=0)
    assert f.probability == pytest.approx(-math.expm1(-expected), rel=1e-12, abs=0)
    assert f.odds == pytest.approx(math.expm1(expected), rel=1e-12, abs=0)
    assert f.numerical_uncertainty is None


@pytest.mark.parametrize('status', ['uncalibrated', 'not_evaluable', 'calibrated'])
def test_odds_require_declared_model_and_exact_calibration(status):
    m = model()
    assert build_field(m, risk(), cells()).odds is None
    f = build_field(m, risk(), cells(), calibration=calibration(m, status=status))
    if status == 'calibrated':
        p = -math.expm1(-f.integrated_hazard)
        assert f.probability == pytest.approx(p)
        assert f.odds == pytest.approx(p/(1-p))
    else:
        assert f.odds is f.probability is None


@pytest.mark.parametrize('changes', [
    {'model_digest': 'different'}, {'risk_set_id': 'different'}, {'n': 0},
    {'event_process': 'recurrent'}, {'interval': (101., 109.)}, {'source': ''},
])
def test_wrong_calibration_never_earns_odds(changes):
    m = model()
    assert build_field(m, risk(), cells(), calibration=calibration(m, **changes)).odds is None


def test_recurrent_count_is_not_first_event_probability():
    m = model('recurrent')
    f = build_field(m, risk(), cells(), calibration=calibration(m))
    assert f.expected_count > 0
    assert f.probability is f.odds is None
    assert 'recurrent_count_is_not_first_event_odds' in f.flags


def test_route_scoped_effects_do_not_suppress_unrelated_route():
    m = model(routes=[model().routes[0], replace(model().routes[0], route_id='r2', mechanism_ids=('m2',))])
    c = cells() | {'r2': cells()['r1']}
    plain = build_field(m, risk(), c)
    reduced = build_field(m, risk(), c, (Suppression('s1', 'r1', 'reduced_intensity', value(.2)),))
    assert [r for r in reduced.routes if r.route_id == 'r2'] == [r for r in plain.routes if r.route_id == 'r2']
    assert reduced.integrated_hazard == pytest.approx(plain.integrated_hazard * .6)
    less = build_field(m, risk(), c, (Suppression('s2', 'r1', 'less_favourable', value(1)),))
    assert less.integrated_hazard == plain.integrated_hazard
    assert ('s2', 'r1', 'less_favourable') in less.effects
    delayed = build_field(model(), risk(), cells(), (Suppression('s3', 'r1', 'delayed', value(2)),))
    assert [(r.start, r.end) for r in delayed.routes] == [(102., 107.), (107., 110.)]
    assert delayed.rate_at(106) == pytest.approx(.01*math.e)
    assert delayed.rate_at(107) == pytest.approx(.01*math.exp(2))
    assert delayed.integrated_hazard == pytest.approx(.01*(5*math.e+3*math.exp(2)))


def test_unavailable_suppression_is_omitted_with_flag():
    f = build_field(model(), risk(), cells(), (Suppression('s1', 'r1', 'reduced_intensity', unknown()),))
    assert f.partial_integral == build_field(model(), risk(), cells()).partial_integral
    assert 'r1:suppression:s1:information_unavailable' in f.flags
    assert f.expected_count is None


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -1.])
def test_invalid_baseline_rejected(bad):
    m = model()
    with pytest.raises(ValueError):
        build_field(replace(m, routes=(replace(m.routes[0], baseline=value(bad)),)), risk(), cells())


def test_parameter_provenance_and_preregistration_are_required():
    m = model()
    for coef in [Coefficient('count', .5, '', 'declared'),
                 Coefficient('count', .5, 'fixture:fit', 'learned')]:
        with pytest.raises(ValueError, match='provenance|registration'):
            build_field(replace(m, routes=(replace(m.routes[0], coefficients=(coef,)),)), risk(), cells())


@pytest.mark.parametrize('change', [
    {'event_process': 'poisson'}, {'eligibility_ref': ''}, {'censoring_ref': ''}, {'event_class': 'invented'},
])
def test_model_contract_cannot_be_implicit(change):
    with pytest.raises(ValueError):
        build_field(replace(model(), **change), risk(), cells())


def test_partition_overlap_gap_duplicate_route_and_wrong_risk_are_rejected():
    for c in [
        {'r1': (RouteCell(100, 106, {'count': value(1)}), RouteCell(105, 110, {'count': value(1)}))},
        {'r1': (RouteCell(100, 104, {'count': value(1)}), RouteCell(105, 110, {'count': value(1)}))},
    ]:
        with pytest.raises(ValueError, match='partition'):
            build_field(model(), risk(), c)
    with pytest.raises(ValueError):
        build_field(replace(model(), routes=model().routes*2), risk(), cells())
    with pytest.raises(ValueError, match='risk'):
        build_field(model(), replace(risk(), risk_set_id='other'), cells())


def test_partition_must_cover_eligible_horizon_before_declared_delay():
    with pytest.raises(ValueError, match='cover'):
        build_field(model(), risk(), {'r1': (RouteCell(101, 109, {'count': value(0)}),)})


def test_first_event_integrated_hazard_is_not_an_expected_event_count():
    m = model()
    f = build_field(m, risk(), cells())
    assert f.integrated_hazard > 0
    assert f.expected_count is None
    calibrated = build_field(m, risk(), cells(), calibration=calibration(m))
    assert calibrated.expected_count is None
    assert calibrated.probability < calibrated.integrated_hazard


def test_span_and_birth_anchor_cannot_be_relabelled_as_recurrent_hazards():
    with pytest.raises(ValueError, match='span'):
        build_field(replace(model('recurrent'), event_class='psychological_arc'), risk(), cells())
    f = build_field(replace(model(), event_class='birth_anchor'), risk(), cells())
    assert f.integrated_hazard is f.expected_count is f.probability is None
    assert 'birth_anchor_not_forecast' in f.flags
