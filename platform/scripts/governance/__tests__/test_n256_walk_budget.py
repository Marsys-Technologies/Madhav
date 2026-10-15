"""test_n256_walk_budget.py: a TIME budget per column walk replaces the size cut (SS N-256).

`_prose_none_fetch_existence_chunked` tracks the cumulative walk time with `_chunk_clock`; past PROSE_NONE_WALK_BUDGET_SECS (600) with no violating row and no end of table the walk stops: the column is UNREAD
("unread: budget"), the cell NO_DETECTOR, never ERRORED, never a closure/PASS. Any other `Unknown` from the closure read path is likewise an UNREAD column, not an ERRORED cell. A violating row found within the
budget still ends the walk red; the TID-scan fix and the walk of a table that finishes inside the budget are untouched.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_n150_prose_none as pn  # noqa: E402
import test_wfixb_engine as wf  # noqa: E402

NO_DET, FAIL, NA, PASS = ac.NO_DET, ac.FAIL, ac.NA, ac.PASS
ENTRY = dict(wf.ENTRY, why="a json record whose leaves are a closed id/class set")


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def _scalar(clock, step, end_after=None, bad_at=None):
    """A fake `scalar` answering chunk statements: every chunk is full (never the end) unless `end_after`; each costs `step` seconds of the fake clock; `bad_at` chunk number returns a violating sample."""
    calls = []

    def fake(sql):
        n = len(calls)
        calls.append(sql)
        clock.t += step
        rows_asked = int(sql.split("LIMIT")[-1].split()[0].strip(")") or 0) if "LIMIT" in sql else 4
        if bad_at is not None and n == bad_at:
            return json.dumps({"rows": 1, "sample": ["a free sentence"], "last": f"({n + 1},1)"})
        if end_after is not None and n >= end_after:
            return json.dumps({"rows": 0, "sample": [], "last": None})
        return json.dumps({"rows": 10 ** 9, "sample": [], "last": f"({n + 1},1)"})
    fake.calls = calls
    return fake


def _fetch(monkeypatch, step, **kw):
    clock = Clock()
    monkeypatch.setattr(ac, "_chunk_clock", clock)
    fake = _scalar(clock, step, **kw)
    monkeypatch.setattr(ac, "scalar", fake)
    return fake


def test_the_budget_is_600_seconds_and_a_budget_stop_is_an_unknown_not_a_closure(monkeypatch):
    assert ac.PROSE_NONE_WALK_BUDGET_SECS == 600 and issubclass(ac.ProseNoneBudget, ac.Unknown)
    fake = _fetch(monkeypatch, step=100.0)                                           # 100 s per chunk, never reaching the end
    with pytest.raises(ac.ProseNoneBudget, match="budget"):
        ac.prose_none_fetch_existence("t", "c", "json", ENTRY, None)
    assert len(fake.calls) == 7                                                      # stopped right after the chunk that took the cumulative time past 600 s


def test_inside_the_budget_the_walk_reaches_the_end_exactly_as_before(monkeypatch):
    _fetch(monkeypatch, step=100.0, end_after=5)                                     # 500 s in total
    got = ac.prose_none_fetch_existence("t", "c", "json", ENTRY, None)
    assert got == dict(violating=False, sample=[], exact=False)


def test_a_violating_row_found_within_the_budget_still_ends_the_walk_red(monkeypatch):
    _fetch(monkeypatch, step=100.0, bad_at=3)
    got = ac.prose_none_fetch_existence("t", "c", "json", ENTRY, None)
    assert got["violating"] is True and got["sample"] == ["a free sentence"]


def test_a_violating_row_in_the_very_chunk_that_crosses_the_budget_wins_over_the_budget(monkeypatch):
    _fetch(monkeypatch, step=700.0, bad_at=0)
    assert ac.prose_none_fetch_existence("t", "c", "json", ENTRY, None)["violating"] is True


def test_the_end_of_the_table_in_the_chunk_that_crosses_the_budget_still_proves_the_closure(monkeypatch):
    _fetch(monkeypatch, step=700.0, end_after=0)
    assert ac.prose_none_fetch_existence("t", "c", "json", ENTRY, None)["violating"] is False


# ───────────────────────── the grader: NO_DETECTOR with the reason, never ERRORED, never PASS ─────────────────────────

TABLES = {"t": (["id", "c"], {"id": "integer", "c": "jsonb"}, None)}
PN = dict(why=pn.WHY, closed_columns=[dict(column="c", json_leaf_patterns=ENTRY["json_leaf_patterns"], why=pn.CW)])


def _outside(monkeypatch):
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: 10 ** 7)               # a big table: straight to the chunked existence read
    return ac.prose_none_fetch_outside(TABLES, "t", PN)


def _cells(outside):
    ctx = pn._ctx(["id", "c"], {"id": "integer", "c": "jsonb"}, closed_outside=outside)
    return ac.prose_checks("x_asset", {"prose_fields": [], "evidence": {"prose_fields": pn.EV}, "prose_none": PN}, ctx)


def test_a_budget_stop_is_an_unread_column_and_all_six_cells_read_no_detector(monkeypatch):
    _fetch(monkeypatch, step=100.0)
    out = _outside(monkeypatch)
    assert "unread: budget" in out[("t", "c")]["unread"] and "neither a PASS nor a FAIL" in out[("t", "c")]["unread"]
    cells = _cells(out)
    assert all(v["v"] == NO_DET for v in cells.values()), {k: v["v"] for k, v in cells.items()}
    assert not any(v["v"] in (PASS, NA, ac.ERRORED) for v in cells.values())


@pytest.mark.parametrize("msg", ["psql: connection refused", "prose_none_fetch_existence: malformed answer for t.c: 'x'", "ERROR:  permission denied for table t"])
def test_any_unknown_from_the_closure_read_path_is_unread_no_detector_not_errored(monkeypatch, msg):
    monkeypatch.setattr(ac, "source_estimate_rows", lambda t: 10 ** 7)
    def boom(*a, **k):
        raise ac.Unknown(msg)
    monkeypatch.setattr(ac, "scalar", boom)
    out = ac.prose_none_fetch_outside(TABLES, "t", PN)
    assert out[("t", "c")]["unread"].startswith("unread: ") and msg.split(":")[0][:10] in out[("t", "c")]["unread"]
    assert all(v["v"] == NO_DET for v in _cells(out).values())


def test_an_unknown_from_the_catalog_estimate_is_also_unread(monkeypatch):
    def boom(t):
        raise ac.Unknown("catalog read failed")
    monkeypatch.setattr(ac, "source_estimate_rows", boom)
    out = ac.prose_none_fetch_outside(TABLES, "t", PN)
    assert "unread: " in out[("t", "c")]["unread"] and all(v["v"] == NO_DET for v in _cells(out).values())


def test_no_pass_path_after_a_budget_stop_the_next_read_starts_a_fresh_budget_and_can_still_close(monkeypatch):
    _fetch(monkeypatch, step=100.0)
    assert "unread" in _outside(monkeypatch)[("t", "c")]
    _fetch(monkeypatch, step=10.0, end_after=3)
    out = _outside(monkeypatch)
    assert out[("t", "c")]["violating"] is False                                      # a walk that finishes inside ITS budget closes (budget is per column walk, not sticky)


def test_a_violating_row_inside_the_budget_is_a_fail_through_the_grader(monkeypatch):
    _fetch(monkeypatch, step=50.0, bad_at=2)
    cells = _cells(_outside(monkeypatch))
    assert cells["Narr.agree"]["v"] == FAIL
