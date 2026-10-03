"""A5.3 — the §4.0 daśā read contract as ONE shared implementation
(services/gochara_kernel/dasha_read.py): the build pin selection and the
`period_running_at` operand reader the registered '5.0' writer hands to the
record grain. Only the DB read (`dasha_data.fetch_dasha_periods_multilevel`) is
faked; the pin rule and row filtering under test are production code."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.gochara_grammar import dasha_data as DD
from services.gochara_kernel import dasha_read
from services.gochara_rules.permission import DASHA_READ_CONTRACT

CANON = DASHA_READ_CONTRACT["chart_id"]
PIN = DASHA_READ_CONTRACT["build_id"]
T = lambda d: datetime(2026, 1, d, tzinfo=timezone.utc)  # noqa: E731


def _row(lord, level, a, b, build, system="vimshottari"):
    return {"system_id": system, "lord_graha": lord, "level_n": level,
            "start_iso": T(a), "end_iso": T(b), "build_id": build}


class _FakeRead:
    """Stands in for fetch_dasha_periods_multilevel: serves rows from a build
    table, honouring `build_id` and recording every call."""

    def __init__(self, rows):
        self.rows, self.calls = rows, []

    def __call__(self, conn, chart_id, systems=None, canonicalize=True,
                 build_id=None, **_):
        self.calls.append({"canonicalize": canonicalize, "build_id": build_id})
        return [r for r in self.rows
                if (build_id is None or str(r["build_id"]) == str(build_id))]


@pytest.fixture(autouse=True)
def _no_g6_query(monkeypatch):
    """These tests drive the reader with a fake `fetch_dasha_periods_multilevel` and NO connection (conn=None). G6's own
    `assert_single_pinned_build` queries `chart_dashas` directly, so it is stubbed here; it is exercised against a real database
    in test_a53_r16_amendments.py (mixed builds, null build, unpinned build, other systems)."""
    monkeypatch.setattr(dasha_read, "assert_single_pinned_build", lambda conn, chart_id: [])


# ── select_dasha_read_contract ───────────────────────────────────────────────

def test_canonical_chart_is_pinned_to_the_frozen_build():
    c = dasha_read.select_dasha_read_contract(CANON, [_row("Saturn", 1, 1, 9, PIN)])
    assert c["build_id"] == PIN and c["ayanamsha_id"] == "lahiri_chitrapaksha"


def test_canonical_chart_on_any_other_build_is_a_conflict():
    with pytest.raises(DD.DashaReadConflict):
        dasha_read.select_dasha_read_contract(CANON, [_row("Saturn", 1, 1, 9, "other")])
    with pytest.raises(DD.DashaReadConflict):
        dasha_read.select_dasha_read_contract(CANON, [])


def test_other_charts_pin_to_the_single_build_or_refuse():
    assert dasha_read.select_dasha_read_contract(
        "x", [_row("Saturn", 1, 1, 9, "b1")])["build_id"] == "b1"
    assert dasha_read.select_dasha_read_contract("x", [])["build_id"] is None
    with pytest.raises(DD.DashaReadConflict):
        dasha_read.select_dasha_read_contract(
            "x", [_row("Saturn", 1, 1, 9, "b1"), _row("Saturn", 1, 1, 9, "b2")])
    with pytest.raises(DD.DashaReadConflict):
        dasha_read.select_dasha_read_contract("x", [_row("Saturn", 1, 1, 9, None)])


def test_only_vimshottari_rows_count_toward_the_pin():
    c = dasha_read.select_dasha_read_contract(
        "x", [_row("Saturn", 1, 1, 9, "b1"),
              _row("Saturn", 1, 1, 9, "zz", system="yogini")])
    assert c["build_id"] == "b1"


# ── make_period_rows_for ─────────────────────────────────────────────────────

def test_reader_returns_only_that_lords_rows_pinned_to_the_build(monkeypatch):
    fake = _FakeRead([_row("Saturn", 1, 1, 9, "b1"), _row("Saturn", 2, 2, 4, "b1"),
                      _row("Jupiter", 1, 9, 20, "b1"),
                      _row("Saturn", 1, 1, 9, "b-foreign")])
    monkeypatch.setattr(DD, "fetch_dasha_periods_multilevel", fake)
    # two builds for a non-canonical chart ⇒ a conflict, never a row-order pick
    with pytest.raises(DD.DashaReadConflict):
        dasha_read.make_period_rows_for(None, "x")[0]("saturn")
    fake2 = _FakeRead([_row("Saturn", 1, 1, 9, "b1"), _row("Saturn", 2, 2, 4, "b1"),
                       _row("Jupiter", 1, 9, 20, "b1")])
    monkeypatch.setattr(DD, "fetch_dasha_periods_multilevel", fake2)
    rows_for, contract = dasha_read.make_period_rows_for(None, "x")
    assert rows_for("SATURN") == [{"start_iso": T(1), "end_iso": T(9)},
                                  {"start_iso": T(2), "end_iso": T(4)}]
    assert rows_for("jupiter") == [{"start_iso": T(9), "end_iso": T(20)}]
    assert rows_for("venus") == []
    assert contract["read"] and contract["build_id"] == "b1"


def test_reader_reads_once_lazily_raw_then_pinned(monkeypatch):
    fake = _FakeRead([_row("Saturn", 1, 1, 9, "b1")])
    monkeypatch.setattr(DD, "fetch_dasha_periods_multilevel", fake)
    rows_for, contract = dasha_read.make_period_rows_for(None, "x")
    assert fake.calls == [] and contract["read"] is False       # lazy
    rows_for("saturn"), rows_for("jupiter"), rows_for("saturn")
    assert fake.calls == [{"canonicalize": False, "build_id": None},   # raw: select the pin
                          {"canonicalize": True, "build_id": "b1"}]    # pinned read, once


def test_reader_with_no_rows_is_honestly_empty_never_a_guess(monkeypatch):
    monkeypatch.setattr(DD, "fetch_dasha_periods_multilevel", _FakeRead([]))
    rows_for, contract = dasha_read.make_period_rows_for(None, "x")
    assert rows_for("saturn") == []
    assert contract["read"] and contract["build_id"] is None


def test_reader_propagates_a_canonical_chart_wrong_build_conflict(monkeypatch):
    monkeypatch.setattr(DD, "fetch_dasha_periods_multilevel",
                        _FakeRead([_row("Saturn", 1, 1, 9, "post-rebuild-build")]))
    with pytest.raises(DD.DashaReadConflict):
        dasha_read.make_period_rows_for(None, CANON)[0]("saturn")
