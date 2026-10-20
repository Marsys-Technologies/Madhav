"""K5-G1b-N2: the production jury caller receives one shift schedule per candidate.

PLAN §6.2(5): schedule and draw machinery run once per candidate; the jury keeps
its own witness geometry and estimand. Scope of the claim: sharing ACROSS THE
JURY CLASSES of one process. Sharing between the jury and the Kshetra field is
NOT claimed: the two writers ask for different schedules (exposure seconds vs
36525 days) in separate assets. That cross-writer remainder is carried, pending
the native's decision; the test below pins the real state so it cannot be
asserted by construction.
"""
import importlib

import pytest

from services.kala_core import measure
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
    assert career.agreement.schedule_digest == wealth.agreement.schedule_digest != ''


def test_jury_and_kshetra_production_schedules_are_not_shared_across_writers():
    # Cross-writer sharing is carried, not delivered (review K5-G1b-N2-R-B1): the
    # Kshetra field schedule is candidate_schedule(36525 days, candidate_null_shifts())
    # (writer._candidate_schedule); the jury's is over its exposure duration. If this
    # fails because the digests became equal, real sharing exists: re-widen the claim
    # in candidate.py / writer.py and assert both writers' digests here.
    from services.ka_kshetra import stage4_field as S4
    from services.ka_kshetra.writer import candidate_null_shifts
    kshetra = measure.candidate_schedule(S4.HORIZON_DAYS, candidate_null_shifts())
    jury = _compute('career').agreement
    assert jury.schedule_digest and kshetra.digest
    assert jury.schedule_digest != kshetra.digest


def test_jury_refuses_a_schedule_prepared_for_another_horizon_or_shift_count():
    other_horizon = measure.candidate_schedule(H.duration + 1, 31)
    other_count = measure.candidate_schedule(H.duration, 30)
    for schedule in (other_horizon, other_count):
        with pytest.raises(ValueError, match='schedule'):
            _compute('career', schedule=schedule)
