"""Legacy DHARA maxima preserve values without a Python scan of every window."""
import numpy as np
import pytest

from services.ka_kshetra.contracts import PromisePrior
from services.ka_kshetra.stage4_field import EnvelopeIndex, FieldEvaluator
from services.ka_kshetra import dhara_null as engine


def test_replicate_maxima_do_not_scalar_scan_the_grid(monkeypatch):
    reads = []
    class Counted(np.ndarray):
        def __getitem__(self, key):
            if isinstance(key, (int, np.integer)):
                reads.append(key)
            return super().__getitem__(key)
    real_empty = np.empty
    monkeypatch.setattr(engine.np, 'empty', lambda *a, **k: real_empty(*a, **k).view(Counted))
    evaluator = FieldEvaluator(event_class='synthetic:cost', lifetime_count=1.,
        promise=PromisePrior(.5), clocks=[], ladder={}, envelopes=EnvelopeIndex([], 1461.),
        weights={}, horizon_days=1461.)
    result = engine.dhara_compute_null(evaluator, replicates=4)
    # Each bucket may inspect endpoints; a per-start scan takes >60,000 Python
    # scalar reads here. This counts actual work, independent of runner speed.
    assert len(reads) <= 2 * 3 * len(engine.DURATION_BUCKETS), len(reads)
    assert result.shift_count == 3 and result.shift_grid_step == 365.25
    # All inputs are constant, so each window's integral scales with its length.
    one_day = result.max_stats[1][0]
    assert one_day > 0
    for bucket, values in result.max_stats.items():
        assert values == pytest.approx([one_day * bucket] * 3, rel=1e-11)
    assert result.q_threshold == pytest.approx(one_day, rel=1e-11)


def test_vectorized_maxima_are_bit_identical_to_the_scalar_definition(monkeypatch):
    """Null statistics unchanged: M_r(L) = max_k cum[k+L] - cum[k] (shared
    `kala_core.measure.field.sliding_window_max`, ALGO §5.5 matched filter).
    The same subtraction and max run in either form, so equality is exact."""
    from types import SimpleNamespace
    from unittest.mock import patch
    from services.kala_core.measure.field import sliding_window_max

    # Non-constant envelope so every shifted replicate has a different cum;
    # horizon 400 d also exercises the bucket >= horizon branch (365, 730).
    evaluator = SimpleNamespace(
        event_class='synthetic:cost', lifetime_count=1., promise=PromisePrior(.5),
        clocks=[], ladder={}, weights={}, baseline_source=None,
        extra_breakpoints=(), horizon_days=400.,
        ln_lambda=lambda t: -4. + .8 * np.sin(t / 7.) + .3 * np.cos(t / 31.),
    )
    clock = SimpleNamespace(ln_lambda=lambda t: -4.)
    seen = []
    real = engine._vec_sliding_window_max
    def recording(cum, bucket):
        value = real(cum, bucket)
        seen.append((np.array(cum, copy=True), bucket, value))
        return value
    monkeypatch.setattr(engine, '_vec_sliding_window_max', recording)
    with patch.object(engine, 'FieldEvaluator', return_value=clock):
        result = engine.dhara_compute_null(evaluator, replicates=6)
    assert len(seen) == 5 * len(engine.DURATION_BUCKETS)
    for cum, bucket, value in seen:
        assert value == sliding_window_max(cum.tolist(), bucket), bucket
    # The recorded values are exactly what the result reports, in replicate order.
    for bucket in engine.DURATION_BUCKETS:
        assert result.max_stats[bucket] == [v for _, b, v in seen if b == bucket]
    assert len({v for _, b, v in seen if b == 1}) > 1  # field really varies
