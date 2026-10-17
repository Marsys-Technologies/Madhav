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
