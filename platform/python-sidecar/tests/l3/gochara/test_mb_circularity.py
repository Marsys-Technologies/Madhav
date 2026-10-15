"""The measuring field consumes ruled scope, never outcome-log rows."""
from datetime import date

from pipeline.orchestrator.writers import ka_gochara_v5 as writer
from .test_mb_horizon_shape_guard import BIRTH_PARAMS, FULL, _Conn, _ctx, _marker


def test_measuring_horizon_and_basis_are_invariant_under_unreadable_or_changed_outcomes():
    bases = []
    for rows in ([], [("unreadable",)], [("a revised outcome",)]):
        conn = _Conn(lel=rows, manifest={writer.TEST_SLICE_KEY: _marker()})
        ctx = _ctx(conn, birth_params=BIRTH_PARAMS)
        slice_ = writer._test_slice(ctx)
        assert slice_.horizon == FULL
        bases.append(writer._horizon_basis(ctx, slice_))
        assert not any("life_events" in sql for sql, _ in conn.statements)
    assert bases[0] == bases[1] == bases[2]
    assert bases[0]["basis"] == "ruled_horizon"
    assert bases[0]["rule"] == "ruled_scope+birth_centenary"
    assert bases[0]["consumed_rows"] == []
    assert bases[0]["birth_date"] == date(1984, 2, 5).isoformat()
