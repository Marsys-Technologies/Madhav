"""K5-2b: lossless storage, rather than a second field solver."""
import math
import random

import pytest

from services.ka_kshetra import integrator as I
from services.ka_kshetra.contracts import Segment
from services.ka_kshetra.writer import KaKshetraWriter
from tests.l3.ka_kshetra.fake_db import FakeConn, FakeCtx
from tests.l3.ka_kshetra import fixtures as F


def compact():
    from services.ka_kshetra import compact_field
    return compact_field


def source_rows():
    # Clock jump at 2, envelope peak at 4, refinement metadata retained.
    spans = [(0., 2., math.log(.25), 0.), (2., 4., 0., math.log(2.)),
             (4., 6., math.log(4.), -math.log(2.))]
    return [dict(segment_index=i, t_start=a, t_end=b, alpha=alpha, gamma=gamma,
                 integral_days=(.5 if i == 0 else 3. / math.log(2.)),
                 field_snapshot_id='fixture-v1', weights_version='classical',
                 x_schema_version='x1', refinement_depth=int(i == 2),
                 refinement_exhausted=i == 2,
                 refinement_residual=.03 if i == 2 else None)
            for i, (a,b,alpha,gamma) in enumerate(spans)]


def test_default_dispatch_completes_with_zero_dml_and_preserves_dense_output():
    import copy
    conn = FakeConn(F.build_tables())
    before = copy.deepcopy(conn.tables)
    writer = KaKshetraWriter()
    ctx = FakeCtx(conn, F.CHART_ID)
    steps = writer.plan_substeps(ctx)
    assert [s.key for s in steps] == ['compact:inactive']
    result = writer.run_substep(ctx, steps[0])
    assert result.rows_inserted == 0
    assert 'SR-A4-01' in result.notes
    assert conn.tables == before
    assert not conn.deletes


def test_projection_preserves_every_coefficient_partition_and_unknown_mask():
    rows = source_rows()
    encoded = compact().encode_segments(rows)
    assert len(encoded) == 3
    for source, stored in zip(rows, encoded):
        assert all(stored[k] == value for k, value in source.items())
        assert stored['risk_mask'] is None
        assert stored['risk_mask_reason'] == 'risk_set_not_specified'
    decoded = compact().decode_segments(encoded)
    assert decoded == [Segment(index=r['segment_index'], t_start=r['t_start'],
        t_end=r['t_end'], alpha=r['alpha'], gamma=r['gamma'],
        refinement_depth=r['refinement_depth'], refinement_exhausted=r['refinement_exhausted'],
        refinement_residual=r['refinement_residual']) for r in rows]
    assert I.lambda_at(decoded, math.nextafter(2., 0.)) == pytest.approx(.25)
    assert I.lambda_at(decoded, 2.) == 1.
    assert I.lambda_at(decoded, 4.) == 4.
    assert I.lambda_at(decoded, 6.) == pytest.approx(1.)
    assert I.integrate(decoded, 0., 6.) == pytest.approx(.5 + 6./math.log(2.), rel=5e-13)
    windows = I.find_windows(decoded, 2.)
    assert len(windows) == 1
    assert (windows[0].t_start, windows[0].t_end) == pytest.approx((3.,5.))
    assert windows[0].expected_count == pytest.approx(4./math.log(2.), rel=5e-13)


def test_random_evaluations_integrals_and_shift_null_statistics_are_bitwise_equal():
    from services.ka_kshetra import stage5_null as N
    from tests.l3.ka_kshetra.test_dhara_properties import _make_evaluator
    ev = _make_evaluator(horizon=400., with_suppression=True)
    rng = random.Random(1729)
    original_stats, stored_stats = [], []
    original_pool, stored_pool = N.QuantilePool(), N.QuantilePool()
    for shift in N.shift_grid(400., 8):
        original = N._null_build_segments(N.replicate_evaluator(ev, shift))
        rows = [dict(segment_index=s.index, t_start=s.t_start, t_end=s.t_end,
            alpha=s.alpha, gamma=s.gamma, integral_days=I.segment_integral(s,s.t_start,s.t_end),
            refinement_depth=s.refinement_depth, refinement_exhausted=s.refinement_exhausted,
            refinement_residual=s.refinement_residual, field_snapshot_id='shift-fixture',
            weights_version='classical',x_schema_version='x1') for s in original]
        stored = compact().decode_segments(compact().encode_segments(rows))
        for _ in range(40):
            a,b = sorted([rng.uniform(0,400),rng.uniform(0,400)])
            assert I.lambda_at(original,a).hex() == I.lambda_at(stored,a).hex()
            assert I.integrate(original,a,b).hex() == I.integrate(stored,a,b).hex()
        original_stats.append(N.replicate_stats(ev,shift,400.,buckets=(1,30),segments=original))
        stored_stats.append(N.replicate_stats(ev,shift,400.,buckets=(1,30),segments=stored))
        original_pool.add([I.lambda_at(original,t/2.) for t in range(801)])
        stored_pool.add([I.lambda_at(stored,t/2.) for t in range(801)])
    assert original_stats == stored_stats
    assert original_pool.value().hex() == stored_pool.value().hex()


@pytest.mark.parametrize('change', [
    {'t_end':float('inf')}, {'alpha':float('nan')}, {'integral_days':42.},
    {'t_start':3.}, {'segment_index':-1},
])
def test_malformed_source_is_rejected_before_replacing_candidate(change):
    rows = source_rows(); rows[1].update(change)
    with pytest.raises(ValueError):
        compact().encode_segments(rows)


def test_projection_rejects_gaps_overlaps_duplicate_indices_and_mixed_pins():
    for column, value in [('t_start',1.),('t_start',3.),('segment_index',0),
                          ('field_snapshot_id','other'),('weights_version','other')]:
        rows=source_rows(); rows[1][column]=value
        with pytest.raises(ValueError): compact().encode_segments(rows)
