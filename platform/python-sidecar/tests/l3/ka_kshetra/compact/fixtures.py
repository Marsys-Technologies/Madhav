"""Synthetic numerical fixtures; no native-chart values or DB substitutes."""
from services.ka_kshetra.contracts import ClockApplicability, PromisePrior, Route
from services.ka_kshetra.stage4_field import EnvelopeIndex, FieldEvaluator, LadderPeriod, Primitive


def primitive(kind, knots, *, polarity='supportive', subject='Ju'):
    return Primitive(kind, subject, None, polarity, None, tuple(knots))


def evaluator(primitives=(), *, horizon=32.0, extra=(), weights=None, clock=True):
    return FieldEvaluator(
        event_class='numerical_fixture', lifetime_count=2.0,
        promise=PromisePrior(p=0.6, routes=(Route(
            event_class='numerical_fixture', route_rank=1,
            path_node_ids=('graha:Ju', 'event_class:numerical_fixture'),
            path_edge_ids=(1,), route_gain=0.6, is_primary=True,
        ),), n_routes=1),
        clocks=[ClockApplicability('vimshottari', 'applicable', 'fruition', 1, True, 0.9)] if clock else [],
        ladder={'vimshottari': [
            LadderPeriod('vimshottari', 'MD', 'Jupiter', 0.0, horizon / 2),
            LadderPeriod('vimshottari', 'MD', 'Saturn', horizon / 2, horizon),
        ]} if clock else {},
        envelopes=EnvelopeIndex(primitives, horizon),
        weights=weights if weights is not None else {
            'w_s:vimshottari': 1.0, 'd:MD': 1.0,
            'beta:x1': 0.9, 'beta:x2': 0.4, 'beta:x3': 0.3,
            'rho:vedha': 0.9,
        }, horizon_days=horizon, extra_breakpoints=extra,
    )


def curved_evaluator():
    return evaluator([primitive('vedha', ((0, 0), (32, 1)), polarity='obstructive')])


def long_horizon_evaluator():
    """Nonconstant three-year field: every null bucket has sliding windows."""
    return evaluator([
        primitive('contact_moon_ref', ((0, 0), (173, .9), (421, .1), (713, .7), (1096, 0))),
    ], horizon=1096.0)
