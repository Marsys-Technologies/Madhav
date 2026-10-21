"""J-5q: the admitted-day-share report is over the SCORED span, and says which span it is over (FIXTURE tests; no stored chart value is read).

Oracles: protocol v2.3 §1 (scored horizon 1998-01-01..2026-04-17, 10,334 days) and FB-50 ("the report over the SCORED horizon"). The century build's
span (1998..2084, the coverage ledger's completed horizon) is a different number: reporting the shares over it made a class's union share read
0.9970 where the scored-span share was 0.9988 (the dry run's F3), and the CLI used the build span without saying so.
"""
from __future__ import annotations

import datetime as dt
import json

import pytest

from services.gochara_eval import density_extract as dx

UTC = dt.timezone.utc
IST = dx.IST


def _t(y, m, d, h=0):
    return dt.datetime(y, m, d, h, tzinfo=IST)


class _Conn:
    """FIXTURE: canned answers to the extractor's statements (the build span, one P3 window), nothing else."""

    def __init__(self, windows, horizons):
        self.answers = {dx.WINDOWS_SQL: windows, dx.MEMBERS_SQL: [], dx.HORIZON_SQL: horizons, dx.CONTEXT_SQL: []}
        self.set_sql = []

    def execute(self, sql, params=None):
        if sql.startswith("SET TRANSACTION"):
            self.set_sql.append(sql)
            return self
        rows = self.answers[sql]

        class _R:
            def fetchall(self_inner):
                return rows
        return _R()

    def rollback(self): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False


# the build span of a century build: 1998-01-01 .. 2084-12-31 (half-open upper bound = 2085-01-01 IST)
BUILD = [(_t(1998, 1, 1), _t(2085, 1, 1))]
# one window that starts 10 days before the scored horizon ends and runs 5 years past it
WINDOW = [("marriage", "P3", "1.0.0", _t(2026, 4, 8), _t(2031, 4, 8))]


def test_the_default_span_is_the_scored_span_and_the_build_span_is_labelled_beside_it():
    rep = dx.report_from_store(_Conn(WINDOW, BUILD), chart_id="c", generation="5.0")
    assert rep["horizon"] == ["1998-01-01", "2026-04-17"] and rep["horizon_days"] == 10334          # protocol §1: 10,334 scored days
    assert rep["horizon_kind"] == "scored" and rep["scored_span"] == ["1998-01-01", "2026-04-17"]
    assert rep["build_span"] == ["1998-01-01", "2084-12-31"]
    # the window's days INSIDE the scored span only: 2026-04-08 .. 2026-04-17 = 10 days (the rest of its five years is outside the score)
    assert rep["classes"]["marriage"]["admitted_days"]["P3"] == 10
    assert rep["classes"]["marriage"]["admitted_day_share"]["P3"] == round(10 / 10334, 6)


def test_the_build_span_is_selectable_and_reported_as_such():
    rep = dx.report_from_store(_Conn(WINDOW, BUILD), chart_id="c", generation="5.0", span="build")
    assert rep["horizon"] == ["1998-01-01", "2084-12-31"] and rep["horizon_kind"] == "build" and rep["horizon_days"] == (dt.date(2084, 12, 31) - dt.date(1998, 1, 1)).days + 1
    assert rep["classes"]["marriage"]["admitted_days"]["P3"] == 1826            # the whole 5 years (2026-04-08 .. 2031-04-07, a leap day inside)
    assert rep["scored_span"] == ["1998-01-01", "2026-04-17"]


def test_an_explicit_horizon_is_an_override_and_is_labelled_so():
    rep = dx.report_from_store(_Conn(WINDOW, BUILD), chart_id="c", generation="5.0", horizon=(dt.date(2026, 1, 1), dt.date(2026, 12, 31)))
    assert rep["horizon_kind"] == "override" and rep["horizon_days"] == 365 and rep["build_span"] == ["1998-01-01", "2084-12-31"]


def test_a_scored_report_of_a_build_that_does_not_cover_the_scored_span_is_refused():
    """The uncovered days would read as 'nothing admitted' — a share computed over days the build never searched."""
    short = [(_t(2001, 1, 1), _t(2001, 4, 11))]
    with pytest.raises(dx.ExtractRefused, match="does not cover the scored span"):
        dx.report_from_store(_Conn(WINDOW, short), chart_id="c", generation="5.0")
    late = [(_t(1998, 1, 2), _t(2085, 1, 1))]                 # starts a day late
    with pytest.raises(dx.ExtractRefused, match="does not cover the scored span"):
        dx.report_from_store(_Conn(WINDOW, late), chart_id="c", generation="5.0")
    early_end = [(_t(1998, 1, 1), _t(2026, 4, 17))]            # ends (exclusive) at 2026-04-17 00:00 -> last covered day 2026-04-16
    with pytest.raises(dx.ExtractRefused, match="does not cover the scored span"):
        dx.report_from_store(_Conn(WINDOW, early_end), chart_id="c", generation="5.0")
    ok = [(_t(1998, 1, 1), _t(2026, 4, 18))]                   # exactly the scored span
    assert dx.report_from_store(_Conn(WINDOW, ok), chart_id="c", generation="5.0")["horizon_days"] == 10334


def test_the_cli_reports_over_the_scored_span_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("J5Q_TEST_DSN", "fixture")
    conn = _Conn(WINDOW, BUILD)
    out = tmp_path / "d.json"
    assert dx.main(["--chart-id", "c", "--generation", "5.0", "--dsn-env", "J5Q_TEST_DSN", "--output", str(out)], connect=lambda dsn, autocommit: conn) == 0
    rep = json.loads(out.read_text())
    assert rep["horizon_kind"] == "scored" and rep["horizon_days"] == 10334 and conn.set_sql == ["SET TRANSACTION READ ONLY"]
    out2 = tmp_path / "d2.json"
    assert dx.main(["--chart-id", "c", "--generation", "5.0", "--dsn-env", "J5Q_TEST_DSN", "--span", "build", "--output", str(out2)],
                   connect=lambda dsn, autocommit: conn) == 0
    assert json.loads(out2.read_text())["horizon_kind"] == "build"
