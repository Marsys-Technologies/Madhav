"""An extract must query and describe the requested chart, with no native default."""
import json

import pytest

from services.gochara_eval import dump_extract as dx
from .test_freeze_and_dump import DASHA_BUILD, ROWS, RO, GOOD_EPH, OUT, conn_for, make_stage1

CHART = "11111111-1111-4111-8111-111111111111"


@pytest.fixture(autouse=True)
def settled_chart(tmp_path, monkeypatch):
    from tests.l3._dasha_settlement import settle_fixture_chart
    settle_fixture_chart(tmp_path, monkeypatch, chart_id=CHART, build_id=DASHA_BUILD)


def test_dump_and_readbacks_use_the_requested_chart_in_every_sql_predicate():
    conn = RO(ROWS, manifest=[("candidate", 5.0, "r", GOOD_EPH)])
    rows = dx.dump_rows(conn, "4.1", True, chart_id=CHART)
    dx.read_manifest_orb(conn, "4.1", chart_id=CHART)
    dx.read_av_donor_identity(conn, chart_id=CHART)
    dx.read_dasha_tiers(conn, chart_id=CHART)
    dx.read_coverage_summary(conn, "4.1", chart_id=CHART)
    assert conn.executed
    assert all(params[0] == CHART for _, params in conn.executed)
    donor_params = [params for sql, params in conn.executed if "ashtakavarga_bindu_contributor" in sql]
    assert donor_params == [(CHART, CHART)]
    assert f"chart_id='{CHART}'" in dx.header("4.1", "2026-10-05", 0, chart_id=CHART)["predicate"]
    assert f"chart_id='{CHART}'" in json.loads(dx.render("4.1", "2026-10-05", rows, chart_id=CHART))["predicate"]


def test_readback_without_chart_refuses_before_connecting(capsys):
    def forbidden():
        raise AssertionError("must refuse before connecting")
    assert dx.main(["--generation", "4.1", "--read-av-donor-rows"], conn_factory=forbidden) == 2
    assert "--chart-id" in capsys.readouterr().err


def test_candidate_uses_the_verified_cohort_chart_when_no_override_is_given(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cohort = {"chart_id": CHART, "held_out": 47, "timing_usable": 32,
              "year_grain": 15, "exact_cohort": 5, "interval_grain": 4}
    doc, stage1 = make_stage1(tmp_path, cohort=cohort)
    conn = conn_for(doc)
    assert dx.main(["--generation", "4.1", "--stage1", str(stage1),
                    "--pinned-at", "2026-10-05", "--out", OUT], conn_factory=lambda: conn) == 0
    assert all(params[0] == CHART for _, params in conn.executed)


def test_candidate_chart_override_cannot_change_the_frozen_cohort(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _, stage1 = make_stage1(tmp_path)
    def forbidden():
        raise AssertionError("must refuse before connecting")
    assert dx.main(["--chart-id", CHART, "--generation", "4.1", "--stage1", str(stage1),
                    "--pinned-at", "2026-10-05", "--out", OUT], conn_factory=forbidden) == 2
    assert "differs from the frozen cohort" in capsys.readouterr().err
