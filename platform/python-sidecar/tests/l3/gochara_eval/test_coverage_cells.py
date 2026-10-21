"""J-5q: the per-(class, year) coverage cells of a governed generation (FIXTURE tests; no stored chart value is read).

Oracle: protocol v2.3 §6.5c — a (class, year) cell counts as computed only when the engine COMPLETED it; coverage is computed cells / horizon cells,
>= 50% per scored class, over a COMPLETE census of the 26 endpoint-eligible classes x the 29 horizon years (1998..2026). The ledger records one
completed horizon per event_class partition, so a year is complete iff that horizon contains the whole year (the last year cut at 2026-04-17).
"""
from __future__ import annotations

import datetime as dt
import json

import pytest

from services.gochara_eval import coverage_cells as cc
from services.gochara_eval.qualification import SCORED_CLASSES, YEARS, engineering_diagnostics

IST = cc.IST


def _t(y, m, d):
    return dt.datetime(y, m, d, tzinfo=IST)


FULL = (_t(1998, 1, 1), _t(2085, 1, 1))
WHY = "Moon-agent edges are on-demand (AM-4)"


class _Conn:
    """FIXTURE: the event_class partitions as the one SELECT returns them."""

    def __init__(self, rows):
        self.rows = rows
        self.seen = []

    def execute(self, sql, params=None):
        self.seen.append((sql, params))
        rows = self.rows

        class _R:
            def fetchall(self_inner):
                return rows
        return _R()


def part(cls, hz=FULL, why=None, lo_inc=True, hi_inc=False):
    return (cls, hz[0], hz[1], lo_inc, hi_inc, why)


def cells(rows, **kw):
    doc = cc.read_cells(_Conn(rows), chart_id="c", generation="5.0", **kw)
    return doc, {(x["event_class"], x["year"]): x for x in doc["cells"]}


def test_the_statement_is_one_read_only_select_scoped_to_one_chart_generation_and_the_event_class_kind():
    text = cc.COVERAGE_SQL.strip().upper()
    assert text.startswith("SELECT") and ";" not in text and "PARTITION_KIND = 'EVENT_CLASS'" in text
    assert "CHART_ID = %S::UUID" in text and "GENERATION = %S" in text
    for verb in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "ALTER", "CREATE", "DROP", "GRANT", "LOCK", "COPY"):
        assert f" {verb} " not in f" {text} "
    assert "EVAL_WINDOW" not in text                       # the cells come from the ledger, never from the admitted windows


def test_a_full_horizon_computes_every_year_including_the_cut_final_year():
    doc, by = cells([part("marriage")])
    assert [y for (c, y) in by] == list(YEARS) and all(x["computed"] for x in by.values())
    assert by[("marriage", 2026)]["horizon_covers_year"] is True          # 2026 is scored to 04-17 only


def test_a_year_the_completed_horizon_only_partly_covers_is_not_computed():
    """A horizon starting 1998-07-01 never completed 1998; one ending 2020-06-30 never completed 2020; both are partial years."""
    doc, by = cells([part("marriage", (_t(1998, 7, 1), _t(2020, 7, 1)))])
    assert by[("marriage", 1998)]["computed"] is False and by[("marriage", 1998)]["horizon_covers_year"] is False
    assert by[("marriage", 1999)]["computed"] is True and by[("marriage", 2019)]["computed"] is True
    assert by[("marriage", 2020)]["computed"] is False and by[("marriage", 2026)]["computed"] is False


def test_the_scored_horizon_end_is_the_last_day_of_the_final_year():
    """Ends (exclusive) 2026-04-18 = the scored horizon's last day 2026-04-17 included -> 2026 complete; one day short -> not."""
    assert cells([part("marriage", (_t(1998, 1, 1), _t(2026, 4, 18)))])[1][("marriage", 2026)]["computed"] is True
    assert cells([part("marriage", (_t(1998, 1, 1), _t(2026, 4, 17)))])[1][("marriage", 2026)]["computed"] is False


def test_the_unsearched_policy_is_declared_recorded_and_changes_only_the_computed_flag():
    rows = [part("bereavement", why=WHY)]
    strict_doc, strict = cells(rows)
    loose_doc, loose = cells(rows, unsearched_policy="horizon_only")
    assert strict_doc["unsearched_policy"] == "strict" and loose_doc["unsearched_policy"] == "horizon_only"
    assert not any(x["computed"] for x in strict.values()) and all(x["computed"] for x in loose.values())
    assert all(x["horizon_covers_year"] and x["unsearched_reason"] == WHY for x in strict.values())      # both facts are in the file either way
    with pytest.raises(cc.CoverageRefused, match="unsearched policy"):
        cells(rows, unsearched_policy="optimistic")


def test_a_class_with_no_partition_gets_no_cells_so_its_absence_is_not_read_as_either_answer():
    doc, by = cells([part("marriage")])
    assert doc["classes_without_partition"] == [c for c in SCORED_CLASSES if c != "marriage"] and {c for c, _y in by} == {"marriage"}
    diag = engineering_diagnostics([], doc["cells"])
    assert diag["coverage"]["status"] == "insufficient_evidence" and diag["pre_2020"]["status"] == "insufficient_evidence"


@pytest.mark.parametrize("row, needle", [
    (("marriage", FULL[0], FULL[1], False, False, None), "half-open"),
    (("marriage", FULL[0], FULL[1], True, True, None), "half-open"),
    (("marriage", None, None, True, False, None), "no completed horizon"),
    (("marriage", dt.datetime(1998, 1, 1), dt.datetime(2085, 1, 1), True, False, None), "timezone-aware"),
    (("birth_anchor", FULL[0], FULL[1], True, False, None), "outside the 26"),
    (("not_a_class", FULL[0], FULL[1], True, False, None), "outside the 26")])
def test_a_ledger_that_cannot_be_read_honestly_is_refused_by_name(row, needle):
    with pytest.raises(cc.CoverageRefused, match=needle):
        cells([row])


def test_two_partitions_of_one_class_are_refused():
    with pytest.raises(cc.CoverageRefused, match="two event_class partitions"):
        cells([part("marriage"), part("marriage")])


def test_the_census_feeds_the_report_gate_end_to_end():
    """A complete 26 x 29 census under 'horizon_only' passes the >=50% gate; under 'strict' with one class unsearched it FAILS that class's
    fraction (0 of 29), and the pre-2020 gate fails with it — the gate reads what the policy declared."""
    classes = list(SCORED_CLASSES)
    rows = [part(c, why=(WHY if c == "bereavement" else None)) for c in classes]
    full = cells(rows, unsearched_policy="horizon_only")[0]
    d = engineering_diagnostics([], full["cells"])
    assert (d["coverage"]["status"], d["pre_2020"]["status"]) == ("pass", "pass") and len(full["cells"]) == 26 * 29
    strict = cells(rows)[0]
    d = engineering_diagnostics([], strict["cells"])
    assert d["coverage"]["status"] == "fail" and d["coverage"]["measured"]["bereavement"]["fraction"] == 0.0
    assert d["pre_2020"]["status"] == "fail" and d["pre_2020"]["measured"] == {"computed": 25 * 22, "expected": 26 * 22}


def test_the_cli_writes_a_report_ready_cells_file(tmp_path, monkeypatch):
    monkeypatch.setenv("J5Q_TEST_DSN", "fixture")

    class Conn(_Conn):
        def execute(self, sql, params=None):
            return self if sql.startswith("SET TRANSACTION") else super().execute(sql, params)
        def rollback(self): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False

    out = tmp_path / "cells.json"
    rc = cc.main(["--chart-id", "c", "--generation", "5.0", "--dsn-env", "J5Q_TEST_DSN", "--output", str(out)],
                 connect=lambda dsn, autocommit: Conn([part("marriage")]))
    doc = json.loads(out.read_text())
    assert rc == 0 and doc["schema"] == "ky.coverage_cells/1" and doc["chart_id"] == "c" and doc["generation"] == "5.0" and len(doc["cells"]) == 29
