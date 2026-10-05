"""The admitted-day-share EXTRACTOR over stored v5 windows (ND-H-20261005 cond. 4; FB-50).

(a) pure: the row → span mapping, the day convention, the refusals, and that every statement is a SELECT;
(b) real schema (throwaway local database): the SQL runs against migrations 1155/1156 verbatim on a generation with
    one stored, admitted P3 window, and the report equals what that window is.
"""
from __future__ import annotations

import datetime as dt

import pytest

from services.gochara_eval import density_extract as dx
from services.gochara_kernel import window_sweep as ws

from .test_a53_window_sweep_pg import (  # noqa: F401  (fixtures: pg, grain, the geometry probe)
    CHART_ID, CLS, GEN, HORIZON, _geometry_probe_for_every_read, _sweep_and_write, grain, pg,
)

UTC = dt.timezone.utc


def _t(y, m, d, h=0):
    return dt.datetime(y, m, d, h, tzinfo=UTC)


class _Conn:
    """Answers the extractor's three statements from canned rows; refuses anything else."""

    def __init__(self, windows=(), members=(), horizons=((_t(2001, 1, 1), _t(2001, 4, 11)),)):
        self.answers = {dx.WINDOWS_SQL: list(windows), dx.MEMBERS_SQL: list(members), dx.HORIZON_SQL: list(horizons)}
        self.seen = []

    def execute(self, sql, params=None):
        assert sql in self.answers, f"unexpected statement: {sql[:60]}"
        self.seen.append((sql, params))
        rows = self.answers[sql]

        class _R:
            def fetchall(self_inner):
                return rows
        return _R()


def test_every_statement_is_one_read_only_select_scoped_to_one_chart_and_generation():
    for sql in dx.STATEMENTS:
        text = sql.strip().upper()
        assert text.startswith("SELECT") and ";" not in text
        for verb in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "ALTER", "CREATE", "DROP", "GRANT", "LOCK", "COPY"):
            assert f" {verb} " not in f" {text} "
        assert "CHART_ID = %S::UUID" in text and "GENERATION = %S" in text
    conn = _Conn()
    dx.report_from_store(conn, chart_id="c", generation="5.0")
    assert {p for _s, p in conn.seen} == {("c", "5.0")} and len(conn.seen) == 3


def test_days_are_counted_in_ist_and_a_half_open_bound_does_not_leak_into_the_next_day():
    # [2001-01-01 00:00 IST, 2001-01-03 00:00 IST) is exactly two IST days (18:30 UTC of the day before)
    lo = dt.datetime(2000, 12, 31, 18, 30, tzinfo=UTC)
    hi = dt.datetime(2001, 1, 2, 18, 30, tzinfo=UTC)
    assert dx._day_span(lo, hi, dx.IST) == (dt.date(2001, 1, 1), dt.date(2001, 1, 2))
    assert dx._day_span(lo, hi + dt.timedelta(seconds=1), dx.IST) == (dt.date(2001, 1, 1), dt.date(2001, 1, 3))
    assert dx._day_span(lo, lo, dx.IST) is None
    with pytest.raises(dx.ExtractRefused):
        dx._day_span(dt.datetime(2001, 1, 1), dt.datetime(2001, 1, 2), dx.IST)


def test_the_report_is_built_from_windows_and_member_supports_with_dvi_from_the_windows_own_h_table():
    windows = [("property_acquisition", "P3", "1.2.0", _t(2001, 1, 1), _t(2001, 1, 21)),
               ("property_acquisition", "P4", "1.2.0", _t(2001, 2, 1), _t(2001, 3, 20)),
               ("marriage", "P3", "1.0.0", _t(2001, 1, 5), _t(2001, 1, 9))]
    members = [("property_acquisition", "P3", "mars", "signature_house", _t(2001, 1, 1), _t(2001, 1, 11)),
               ("property_acquisition", "P3", "saturn", "lord", _t(2001, 1, 9), _t(2001, 1, 21)),
               ("marriage", "P3", "venus", "signature_house", _t(2001, 1, 5), _t(2001, 1, 9))]
    rep = dx.report_from_store(_Conn(windows, members), chart_id="c", generation="5.0", tz=UTC)
    assert rep["horizon"] == ["2001-01-01", "2001-04-10"] and rep["horizon_days"] == 100
    prop = rep["classes"]["property_acquisition"]
    assert prop["admitted_day_share"]["P3"] == 0.20 and prop["admitted_day_share"]["P3_fast"] == 0.10
    assert prop["admitted_day_share"]["P3_slow"] == 0.12 and prop["admitted_day_share"]["P4"] == 0.47
    # the guard reads the DVI member of the H table the P4 windows were BUILT under (1.2.0: the 11th)
    assert prop["dvi_guard"]["dvi_members"] == [11] and prop["dvi_guard"]["revert_dvi_to_support_next_generation"] == [11]
    assert prop["admitted_day_share"]["P4_no_dvi"] is None and "separate rerun required" in prop["series_notes"]["P4_no_dvi"]
    assert rep["classes"]["marriage"]["dvi_guard"]["dvi_members"] == []
    assert rep["source"]["kind"] == "stored_windows" and rep["source"]["p4_rule_versions"] == {"property_acquisition": "1.2.0"}
    assert (rep["source"]["window_spans"], rep["source"]["member_spans"]) == (3, 3)


def test_a_karaka_member_is_the_k_b_contribution():
    windows = [("psychological_arc", "P3", "1.2.0", _t(2001, 1, 1), _t(2001, 1, 11))]
    members = [("psychological_arc", "P3", "saturn", "karaka", _t(2001, 1, 1), _t(2001, 1, 11)),
               ("psychological_arc", "P3", "mars", "signature_house", _t(2001, 1, 7), _t(2001, 1, 11))]
    got = dx.report_from_store(_Conn(windows, members), chart_id="c", generation="5.0", tz=UTC)["classes"]["psychological_arc"]
    assert got["admitted_days"]["kb_only"] == 6 and got["admitted_days"]["P3"] == 10


@pytest.mark.parametrize("horizons, needle", [
    ([], "no event_class coverage partition"),
    ([(_t(2001, 1, 1), _t(2001, 4, 11)), (_t(2001, 1, 1), _t(2002, 1, 1))], "different completed horizons")])
def test_a_missing_or_ambiguous_horizon_is_refused_by_name(horizons, needle):
    with pytest.raises(dx.ExtractRefused) as exc:
        dx.report_from_store(_Conn(horizons=horizons), chart_id="c", generation="5.0")
    assert needle in str(exc.value)


def test_p4_windows_of_one_class_under_two_rule_versions_are_refused():
    windows = [("property_acquisition", "P4", v, _t(2001, 2, 1), _t(2001, 2, 3)) for v in ("1.0.0", "1.2.0")]
    with pytest.raises(dx.ExtractRefused):
        dx.report_from_store(_Conn(windows), chart_id="c", generation="5.0")


# ── (b) the real schema ──────────────────────────────────────────────────────────────────────────────────

def test_the_extractor_reads_a_real_stored_window_and_writes_nothing(grain):
    conn = grain
    _recs, drafts, _excluded, counts, _verified = _sweep_and_write(conn, ws.registry_factor_rows)
    assert counts["windows"] == 1 and len(drafts) == 1
    tables = ("ka_gochara_eval_window", "ka_gochara_eval_window_record", "ka_gochara_relationship_record",
              "kala_gochara_coverage")
    before = {t: conn.execute(f"SELECT count(*), max(xmin::text::bigint) FROM public.{t}").fetchone() for t in tables}
    rep = dx.report_from_store(conn, chart_id=CHART_ID, generation=GEN, tz=UTC)
    after = {t: conn.execute(f"SELECT count(*), max(xmin::text::bigint) FROM public.{t}").fetchone() for t in tables}
    assert after == before                                                    # read-only, by the rows' own versions
    lo, hi = HORIZON
    assert rep["horizon"] == [lo.date().isoformat(), (hi - dt.timedelta(microseconds=1)).date().isoformat()]
    got = rep["classes"][CLS]
    # the fixture: Saturn in Libra (the 7th) for [day 10, day 200) of a 400-day horizon — one P3 window, 190 days
    assert got["admitted_days"]["P3"] == 190 and rep["horizon_days"] == 400
    assert got["admitted_days"]["P3_slow"] == 190 and got["admitted_days"]["P3_fast"] == 0
    assert got["admitted_days"]["union"] == 190 and got["admitted_days"]["kb_only"] == 0
    assert got["admitted_day_share"]["P3"] == 0.475
    assert got["admitted_days"]["P4_no_dvi"] == got["admitted_days"]["P4"] == 0      # marriage has no DVI member
    assert rep["source"] == {**rep["source"], "window_spans": 1, "member_spans": 1, "chart_id": CHART_ID}
    assert rep["dvi_reversions_next_generation"] == {}


def test_the_extractor_on_a_generation_with_no_window_reports_no_class_and_does_not_invent_one(grain):
    rep = dx.report_from_store(grain, chart_id=CHART_ID, generation=GEN, tz=UTC)
    assert rep["classes"] == {} and rep["horizon_days"] == 400
