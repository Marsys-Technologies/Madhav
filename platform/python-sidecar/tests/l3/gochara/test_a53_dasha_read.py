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
LEGACY_BUILD = "75524b3e-102a-43ec-8cee-3f57fee752c3"
SETTLED_BUILD = "7377833e-5d3b-4e70-8bef-1318904f470e"
FUTURE_BUILD = "22222222-2222-4222-8222-222222222222"  # synthetic successor, not an L1 assertion
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
    real = dasha_read.assert_single_pinned_build
    monkeypatch.setattr(dasha_read, "assert_single_pinned_build",
                        lambda conn, chart_id: [] if conn is None else real(conn, chart_id))


# ── select_dasha_read_contract ───────────────────────────────────────────────

@pytest.mark.parametrize("build", [SETTLED_BUILD])
def test_canonical_chart_accepts_the_governed_verified_build(build):
    c = dasha_read.select_dasha_read_contract(CANON, [_row("Saturn", 1, 1, 9, build)])
    assert c["build_id"] == build
    assert c["ayanamsha_id"] == "lahiri_chitrapaksha"
    assert c["tier"] == "two_pass_verified" and c["builds_seen"] == [build]


def test_canonical_chart_without_verified_rows_is_still_refused():
    with pytest.raises(DD.DashaReadConflict):
        dasha_read.select_dasha_read_contract(CANON, [])


@pytest.mark.parametrize("builds", [[LEGACY_BUILD, SETTLED_BUILD], [LEGACY_BUILD, None], [None]])
def test_canonical_selection_refuses_mixed_or_null_builds_even_if_the_old_pin_is_present(builds):
    with pytest.raises(DD.DashaReadConflict):
        dasha_read.select_dasha_read_contract(CANON, [_row("Saturn", 1, 1, 9, b) for b in builds])


@pytest.mark.parametrize("rows", [[], [_row("Saturn", 1, 1, 9, SETTLED_BUILD)]])
def test_other_charts_without_a_settlement_refuse(rows):
    with pytest.raises(dasha_read.DashaBuildRefused, match="chart_not_settled"):
        dasha_read.select_dasha_read_contract("x", rows)


def test_only_vimshottari_rows_count_toward_the_pin():
    c = dasha_read.select_dasha_read_contract(
        CANON, [_row("Saturn", 1, 1, 9, SETTLED_BUILD),
              _row("Saturn", 1, 1, 9, "zz", system="yogini")])
    assert c["build_id"] == SETTLED_BUILD


# ── make_period_rows_for ─────────────────────────────────────────────────────

def test_reader_returns_only_that_lords_rows_pinned_to_the_build(monkeypatch):
    fake = _FakeRead([_row("Saturn", 1, 1, 9, SETTLED_BUILD), _row("Saturn", 2, 2, 4, SETTLED_BUILD),
                      _row("Jupiter", 1, 9, 20, SETTLED_BUILD),
                      _row("Saturn", 1, 1, 9, "b-foreign")])
    monkeypatch.setattr(dasha_read, "_fetch_dasha_periods_multilevel", fake)
    # two builds for the settled chart ⇒ a conflict, never a row-order pick
    with pytest.raises(DD.DashaReadConflict):
        dasha_read.make_period_rows_for(None, CANON)[0]("saturn")
    fake2 = _FakeRead([_row("Saturn", 1, 1, 9, SETTLED_BUILD), _row("Saturn", 2, 2, 4, SETTLED_BUILD),
                       _row("Jupiter", 1, 9, 20, SETTLED_BUILD)])
    monkeypatch.setattr(dasha_read, "_fetch_dasha_periods_multilevel", fake2)
    rows_for, contract = dasha_read.make_period_rows_for(None, CANON)
    assert rows_for("SATURN") == [{"start_iso": T(1), "end_iso": T(9)},
                                  {"start_iso": T(2), "end_iso": T(4)}]
    assert rows_for("jupiter") == [{"start_iso": T(9), "end_iso": T(20)}]
    assert rows_for("venus") == []
    assert contract["read"] and contract["build_id"] == SETTLED_BUILD


def test_reader_reads_once_lazily_raw_then_pinned(monkeypatch):
    fake = _FakeRead([_row("Saturn", 1, 1, 9, SETTLED_BUILD)])
    monkeypatch.setattr(dasha_read, "_fetch_dasha_periods_multilevel", fake)
    rows_for, contract = dasha_read.make_period_rows_for(None, CANON)
    assert fake.calls == [] and contract["read"] is False       # lazy
    rows_for("saturn"), rows_for("jupiter"), rows_for("saturn")
    assert fake.calls == [{"canonicalize": False, "build_id": None},   # raw: select the pin
                          {"canonicalize": True, "build_id": SETTLED_BUILD}]    # pinned read, once


def test_reader_with_no_rows_refuses_never_guesses(monkeypatch):
    monkeypatch.setattr(dasha_read, "_fetch_dasha_periods_multilevel", _FakeRead([]))
    rows_for, contract = dasha_read.make_period_rows_for(None, CANON)
    with pytest.raises(dasha_read.DashaBuildRefused, match="settled_build_absent"):
        rows_for("saturn")
    assert not contract["read"]


@pytest.mark.parametrize("build", [SETTLED_BUILD])
def test_reader_records_the_actual_canonical_build_and_pins_the_second_read(monkeypatch, build):
    fake = _FakeRead([_row("Saturn", 1, 1, 9, build)])
    monkeypatch.setattr(dasha_read, "_fetch_dasha_periods_multilevel", fake)
    rows_for, contract = dasha_read.make_period_rows_for(None, CANON)
    assert rows_for("saturn") == [{"start_iso": T(1), "end_iso": T(9)}]
    assert contract["read"] and contract["build_id"] == build
    assert fake.calls == [{"canonicalize": False, "build_id": None},
                          {"canonicalize": True, "build_id": build}]


class _BuildConn:
    """Only the all-tier SQL boundary is faked; the production G6 guard runs."""

    def __init__(self, builds):
        self.builds = builds

    def execute(self, sql, params):
        assert "verification_pass_status" not in sql and "level_n" not in sql
        assert "chart_id = %s AND system_id = %s AND ayanamsha_id = %s" in sql
        assert params == (CANON, "vimshottari", "lahiri_chitrapaksha")
        return self

    def fetchall(self):
        return [(b,) for b in self.builds]


@pytest.mark.parametrize("build", [LEGACY_BUILD, SETTLED_BUILD, FUTURE_BUILD])
def test_all_tier_guard_accepts_any_single_non_null_build(build):
    assert dasha_read.assert_single_pinned_build(_BuildConn([build]), CANON) == [build]


@pytest.mark.parametrize("builds, code", [
    ([LEGACY_BUILD, SETTLED_BUILD], "settled_build_ambiguous"),
    ([SETTLED_BUILD, "NULL"], "settled_build_ambiguous"),
    (["NULL"], "dasha_build_null"),
])
def test_all_tier_guard_refuses_mixed_and_null_builds_by_name(builds, code):
    with pytest.raises(dasha_read.DashaBuildRefused) as exc:
        dasha_read.assert_single_pinned_build(_BuildConn(builds), CANON)
    assert exc.value.code == code


@pytest.mark.parametrize("build", [
    "7377833e-5d3b-4e70-8bef-1318904f470e",
])
def test_reader_and_independent_verifier_accept_the_same_single_build(build):
    from services.gochara_kernel import inventory_verifier as inv
    a, b = datetime(2025, 1, 1, tzinfo=timezone.utc), datetime(2025, 2, 1, tzinfo=timezone.utc)
    row = {"dasha_row_id": "11111111-1111-4111-8111-111111111111", "level_n": 1,
           "parent_row_id": None, "lord_graha": "Saturn", "start_iso": a, "end_iso": b,
           "build_id": build, "system_id": "vimshottari", "ayanamsha_id": "lahiri_chitrapaksha",
           "verification_pass_status": "two_pass_verified"}
    assert dasha_read.select_dasha_read_contract(CANON, [row])["build_id"] == build
    assert inv.check_dasha_population([row], [row], chart_id=CANON,
                                      horizon=(a, b), consumed_ids=[row["dasha_row_id"]]) == []


class _PopulationConn:
    """Fake SQL boundary; the independent verifier's real population checks run."""

    def __init__(self, builds, *, tier="two_pass_verified", consumed_build=None):
        self.builds, self.tier = builds, tier
        self.consumed_build = consumed_build
        self.sql = []

    def execute(self, sql, params):
        self.sql.append((sql, params))
        if "search_input_snapshot" in sql:
            self.result = [(["11111111-1111-4111-8111-111111111111"],)]
        elif "search_inventory" in sql:
            self.result = [(T(1), T(9))]
        elif "SELECT DISTINCT" in sql:
            eligible = "verification_pass_status" in sql
            assert params[:3] == (CANON, "vimshottari", "lahiri_chitrapaksha")
            if eligible:
                assert params[3:] == ("two_pass_verified", [1, 2, 3])
            else:
                assert "level_n" not in sql
            self.result = [(b,) for b in self.builds if not eligible or self.tier == "two_pass_verified"]
        else:
            assert "chart_dashas" in sql
            build = self.builds[0] if self.builds else None
            consumed = "dasha_row_id = ANY" in sql
            if consumed and self.consumed_build is not None:
                build = self.consumed_build
            if not consumed:
                assert params[:5] == (CANON, "lahiri_chitrapaksha", "vimshottari",
                                      "two_pass_verified", [1, 2, 3])
                assert params[-1] == build  # the guarded build pins this read
            self.result = [("11111111-1111-4111-8111-111111111111", 1, None,
                            "Saturn", T(1), T(9), build, "vimshottari",
                            "lahiri_chitrapaksha", self.tier)]
            if not self.builds or (not consumed and self.tier != "two_pass_verified"):
                self.result = []
        return self

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return self.result


@pytest.mark.parametrize("build", [SETTLED_BUILD])
def test_independent_verifier_queries_and_pins_the_guarded_build_without_builder_code(monkeypatch, build):
    from services.gochara_kernel import inventory_verifier as inv
    def forbidden(*args, **kwargs):
        raise AssertionError("independent verifier called the builder")
    monkeypatch.setattr(dasha_read, "select_dasha_read_contract", forbidden)
    monkeypatch.setattr(dasha_read, "assert_single_pinned_build", forbidden)
    out = inv.validate_consumed_dasha_population(_PopulationConn([build]),
                                                chart_id=CANON, generation="5.0")
    assert out == {"consumed": 1, "pinned_overlapping": 1}


@pytest.mark.parametrize("builds, tier, code", [
    ([LEGACY_BUILD, SETTLED_BUILD], "two_pass_verified", "settled_build_ambiguous"),
    ([SETTLED_BUILD, "NULL"], "single", "settled_build_ambiguous"),
    (["NULL"], "two_pass_verified", "dasha_build_null"),
    ([], "two_pass_verified", "settled_build_absent"),
    ([SETTLED_BUILD], "single", "settled_build_absent"),
])
def test_independent_verifier_refuses_mixed_null_and_unsettled_builds(builds, tier, code):
    from services.gochara_kernel import inventory_verifier as inv
    with pytest.raises(inv.Unverifiable, match=code):
        inv.validate_consumed_dasha_population(_PopulationConn(builds, tier=tier),
                                               chart_id=CANON, generation="5.0")


def test_independent_verifier_refuses_a_consumed_build_outside_the_guarded_population():
    from services.gochara_kernel import inventory_verifier as inv
    with pytest.raises(inv.Unverifiable, match="several builds"):
        inv.validate_consumed_dasha_population(
            _PopulationConn([SETTLED_BUILD], consumed_build=LEGACY_BUILD),
            chart_id=CANON, generation="5.0")


@pytest.mark.parametrize("builds", [[None], [SETTLED_BUILD, FUTURE_BUILD], []])
def test_pure_verifier_refuses_null_mixed_or_unsettled_populations(builds):
    from services.gochara_kernel import inventory_verifier as inv
    rows = [dict(_row("Saturn", 1, 1, 9, build),
                 dasha_row_id=str(i), parent_row_id=None,
                 ayanamsha_id="lahiri_chitrapaksha", verification_pass_status="two_pass_verified")
            for i, build in enumerate(builds)]
    assert inv.check_dasha_population(rows, rows, chart_id=CANON, horizon=(T(1), T(9)),
                                      consumed_ids=[r["dasha_row_id"] for r in rows])
