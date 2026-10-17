"""MB-6 producer/consumer regression for the outcome-free measuring scope.

Reverting the verifier's ruled-scope support must reject this actual writer
output. Corrupting that output must still refuse, even with a valid row hash.
The verifier itself must remain independent of the producer implementation.
"""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json

import pytest

from services.gochara_kernel import measuring_report as mr
from .test_measuring_report import BIRTH, BUILD, H, T, _mb6_accept, _mb6_view
from .test_mb_horizon_shape_guard import BIRTH_PARAMS, _Conn, _ctx, _marker


def producer_basis():
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer

    class OutcomeBlindConnection(_Conn):
        def execute(self, sql, params=()):
            if "life_events" in sql:
                raise AssertionError("field scope must consume no outcomes")
            return super().execute(sql, params)

    conn = OutcomeBlindConnection(created=T(2026, 10, 5),
                                  manifest={writer.TEST_SLICE_KEY: _marker()})
    ctx = _ctx(conn, birth_params=BIRTH_PARAMS)
    return writer._horizon_basis(ctx, writer._test_slice(ctx))


def test_mb6_real_producer_basis_passes_without_outcome_inputs():
    view = _mb6_view()
    view.horizon_basis = producer_basis()
    result = _mb6_accept(view)
    assert result["accepted"] is True, result["refusals"]
    assert result["refusals"] == []
    assert result["marker_digest_verified"] is None


@pytest.mark.parametrize("field,bad", [
    ("schema", "invented/1"), ("rule", "invented"),
    ("basis", "first_dated_event"), ("rule", "ruling7+ruling13"),
    ("chart_id", "other-chart"), ("birth_date", "1985-02-05"),
    ("build_date", "2026-10-06"),
    ("horizon", ["1999-01-01", "2084-02-05"]),
    ("horizon", ["1998-01-01", "2083-02-05"]),
    ("rows_total", 1), ("rows_total", False),
    ("excluded_not_fully_dated", 1), ("excluded_not_fully_dated", False),
    ("consumed_rows_digest", "0" * 64),
    ("chosen", {"event_id": "outcome"}), ("birth_row", {"event_id": "birth"}),
    ("fully_dated_readings", {"conjunction_start": "1998-01-01"}),
    ("shape_readings", {"event_date_start": "1998-01-01"}),
    ("flag_exact_but_id_undated", ["outcome"]),
    ("rows_without_lel_id", [{"event_id": "outcome"}]),
])
def test_mb6_wrong_real_producer_basis_still_refuses(field, bad):
    view = _mb6_view()
    view.horizon_basis = producer_basis()
    view.horizon_basis[field] = bad
    result = _mb6_accept(view)
    assert result["accepted"] is False
    assert any(r.startswith(("horizon_basis_", "horizon_mismatch")) for r in result["refusals"])


def test_mb6_ruled_basis_cannot_hide_rehashed_outcome_rows():
    view = _mb6_view()
    rows = deepcopy(view.horizon_basis["consumed_rows"])
    basis = view.horizon_basis = producer_basis()
    basis.update(consumed_rows=rows, rows_total=len(rows))
    basis["consumed_rows_digest"] = sha256(json.dumps(
        rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    result = _mb6_accept(view)
    assert result["accepted"] is False
    assert "horizon_basis_invalid: ruled_scope" in result["refusals"]


@pytest.mark.parametrize("context,reason", [
    ({"birth_date": date(1983, 2, 5)}, "horizon_mismatch"),
    ({"build_date": date(1997, 12, 31)}, "horizon_start_in_future"),
    ({"birth_date": date(2000, 2, 29)}, "horizon_birth_anniversary_undefined"),
])
def test_mb6_rederives_ruled_bounds_from_independent_context(context, reason):
    view = _mb6_view()
    basis = view.horizon_basis = producer_basis()
    for key, value in context.items():
        basis[key] = value.isoformat()
    result = mr.measuring_acceptance(
        view, expected_horizon=H, chart_id=basis["chart_id"],
        birth_date=context.get("birth_date", BIRTH), build_date=context.get("build_date", BUILD))
    assert result["accepted"] is False
    assert reason in result["refusals"]
