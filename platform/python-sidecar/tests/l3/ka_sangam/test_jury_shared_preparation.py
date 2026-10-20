"""K5-G1b-N2: the production jury caller receives the candidate's shift schedule.

PLAN §6.2(5): schedule and draw machinery run once per candidate; the jury keeps
its own witness geometry and estimand. The same schedule digest is what the
Kshetra field null binds (tests/l3/ka_kshetra/test_g1b_n2_shared_preparation.py).
"""
import importlib

import pytest

from services.kala_core import measure
from services.kala_core.measure.field import prepare_field
from tests.l3.ka_sangam.test_jury_writer import H, api, fixture_input

agreement_module = importlib.import_module('services.ka_sangam.jury.agreement')


def _compute(event_class, **kwargs):
    return api().compute(api().ClassInput.model_validate(fixture_input(event_class)), **kwargs)


def test_production_jury_receives_one_candidate_schedule_shared_with_the_field(monkeypatch):
    measure.candidate_schedule.cache_clear()
    prepared, handed = [], []
    real_schedule, real_draws = measure.prepare_schedule, agreement_module.prepare_draws
    monkeypatch.setattr(measure, 'prepare_schedule', lambda *a, **k: prepared.append(a) or real_schedule(*a, **k))
    monkeypatch.setattr(agreement_module, 'prepare_draws',
                        lambda *a, **k: handed.append(k.get('schedule')) or real_draws(*a, **k))
    career, wealth = _compute('career'), _compute('wealth')
    # Every class's jury preparation was handed a schedule, the same prepared object.
    assert len(handed) == 2 and handed[0] is not None and handed[0] is handed[1]
    assert len(prepared) == 1
    # The field (own estimand, own geometry) binds the identical schedule.
    field = prepare_field('career', H.duration, schedule=handed[0])
    assert career.agreement.schedule_digest == wealth.agreement.schedule_digest == field.schedule_digest != ''
    assert tuple(d.offset for d in real_draws(H, (measure.Witness('G-P', (H,)),), anchor_id='G-P',
        non_identity_shifts=31, exchangeable=False, schedule=handed[0]).null_draws) == field.offsets
    assert career.agreement.conditional.experiment.estimand != field.experiment.estimand


def test_jury_refuses_a_schedule_prepared_for_another_horizon_or_shift_count():
    other_horizon = measure.candidate_schedule(H.duration + 1, 31)
    other_count = measure.candidate_schedule(H.duration, 30)
    for schedule in (other_horizon, other_count):
        with pytest.raises(ValueError, match='schedule'):
            _compute('career', schedule=schedule)
