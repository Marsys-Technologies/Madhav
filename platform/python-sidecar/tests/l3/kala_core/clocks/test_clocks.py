"""K1-1a F2 clock reader contract."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.kala_core.clocks import boundaries, period_context


UTC = timezone.utc
CHART = "482012f1-710e-4a25-994a-93821f5871aa"


class _Result:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def fetchall(self) -> list[dict]:
        return self._rows


class _ClockConnection:
    """Read-only chart_dashas stand-in which rejects an unpinned read."""

    def __init__(self) -> None:
        self.rows = [
            {
                "dasha_row_id": "md-sun", "level_n": 1, "lord_graha": "Sun",
                "lord_sign": None, "parent_row_id": None,
                "start_iso": datetime(2024, 1, 1, tzinfo=UTC),
                "end_iso": datetime(2024, 7, 1, tzinfo=UTC),
                "build_id": "build-1", "ayanamsha_id": "lahiri_chitrapaksha",
                "verification_pass_status": "two_pass_verified",
                "applies_to_this_chart_flag": True, "system_id": "vimshottari",
                "is_truncated_at_window_start": False, "is_truncated_at_window_end": False,
            },
            {
                "dasha_row_id": "ad-moon", "level_n": 2, "lord_graha": "Moon",
                "lord_sign": None, "parent_row_id": "md-sun",
                "start_iso": datetime(2024, 1, 1, tzinfo=UTC),
                "end_iso": datetime(2024, 4, 1, tzinfo=UTC),
                "build_id": "build-1", "ayanamsha_id": "lahiri_chitrapaksha",
                "verification_pass_status": "two_pass_verified",
                "applies_to_this_chart_flag": True, "system_id": "vimshottari",
                "is_truncated_at_window_start": False, "is_truncated_at_window_end": False,
            },
            {
                "dasha_row_id": "ad-mars", "level_n": 2, "lord_graha": "Mars",
                "lord_sign": None, "parent_row_id": "md-sun",
                "start_iso": datetime(2024, 4, 1, tzinfo=UTC),
                "end_iso": datetime(2024, 7, 1, tzinfo=UTC),
                "build_id": "build-1", "ayanamsha_id": "lahiri_chitrapaksha",
                "verification_pass_status": "two_pass_verified",
                "applies_to_this_chart_flag": True, "system_id": "vimshottari",
                "is_truncated_at_window_start": False, "is_truncated_at_window_end": False,
            },
            {
                "dasha_row_id": "pd-mercury", "level_n": 3, "lord_graha": "Mercury",
                "lord_sign": None, "parent_row_id": "ad-moon",
                "start_iso": datetime(2024, 1, 1, tzinfo=UTC),
                "end_iso": datetime(2024, 4, 1, tzinfo=UTC),
                "build_id": "build-1", "ayanamsha_id": "lahiri_chitrapaksha",
                "verification_pass_status": "two_pass_verified",
                "applies_to_this_chart_flag": True, "system_id": "vimshottari",
                "is_truncated_at_window_start": False, "is_truncated_at_window_end": False,
            },
            {
                "dasha_row_id": "sd-jupiter", "level_n": 4, "lord_graha": "Jupiter",
                "lord_sign": None, "parent_row_id": "pd-mercury",
                "start_iso": datetime(2024, 1, 1, tzinfo=UTC),
                "end_iso": datetime(2024, 4, 1, tzinfo=UTC),
                "build_id": "build-1", "ayanamsha_id": "lahiri_chitrapaksha",
                "verification_pass_status": "two_pass_verified",
                "applies_to_this_chart_flag": True, "system_id": "vimshottari",
                "is_truncated_at_window_start": False, "is_truncated_at_window_end": False,
            },
        ]
        self.calls: list[tuple[str, list[object]]] = []

    def execute(self, sql: str, params: list[object]) -> _Result:
        self.calls.append((sql, params))
        assert "build_id = %s" in sql
        assert "ayanamsha_id = %s" in sql
        assert "system_id = %s" in sql
        assert "verification_pass_status = %s" in sql
        assert "applies_to_this_chart_flag" in sql
        assert "is_truncated_at_window_start" in sql
        assert "is_truncated_at_window_end" in sql
        assert "tier = %s" not in sql
        assert "sigma_boundary_seconds" not in sql
        assert "scenario_id" not in sql
        assert "applicability" not in sql
        assert params[-1] == "two_pass_verified"
        assert params[:4] == [CHART, "vimshottari", "build-1", "lahiri_chitrapaksha"]
        return _Result(self.rows)


def test_boundaries_equal_the_pinned_l1_rows_for_the_canonical_fixture() -> None:
    conn = _ClockConnection()

    result = boundaries(
        conn, CHART, "vimshottari", build_id="build-1",
        ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified",
    )

    assert [(row.instant, row.source_row_id) for row in result] == [
        (datetime(2024, 1, 1, tzinfo=UTC), "md-sun"),
        (datetime(2024, 1, 1, tzinfo=UTC), "ad-moon"),
        (datetime(2024, 4, 1, tzinfo=UTC), "ad-mars"),
        (datetime(2024, 1, 1, tzinfo=UTC), "pd-mercury"),
        (datetime(2024, 1, 1, tzinfo=UTC), "sd-jupiter"),
    ]


def test_period_context_requires_explicit_as_of_and_only_changes_at_a_boundary() -> None:
    conn = _ClockConnection()
    early = period_context(
        conn, CHART, datetime(2024, 2, 1, tzinfo=UTC), "vimshottari",
        build_id="build-1", ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified",
    )
    late = period_context(
        conn, CHART, datetime(2024, 5, 1, tzinfo=UTC), "vimshottari",
        build_id="build-1", ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified",
    )

    assert early.lords == {"MD": "Sun", "AD": "Moon", "PD": "Mercury", "SD": "Jupiter"}
    assert early.period_ids["SD"] == "sd-jupiter"
    assert late.lords == {"MD": "Sun", "AD": "Mars"}
    with pytest.raises(TypeError):
        period_context(  # type: ignore[call-arg]
            conn, CHART, system="vimshottari", build_id="build-1",
            ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified",
        )


def test_sandhi_band_is_three_percent_of_its_own_period_span() -> None:
    conn = _ClockConnection()
    result = period_context(
        conn, CHART, datetime(2024, 4, 2, tzinfo=UTC), "vimshottari",
        build_id="build-1", ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified",
    )

    assert result.sandhi is True
    assert result.sandhi_window == timedelta(days=91 * 0.03)


def test_hierarchy_ignores_an_overlapping_child_from_another_parent() -> None:
    conn = _ClockConnection()
    conn.rows.append({
        "dasha_row_id": "orphan-ad", "level_n": 2, "lord_graha": "Rahu",
        "lord_sign": None, "parent_row_id": "another-md",
        "start_iso": datetime(2024, 1, 1, tzinfo=UTC),
        "end_iso": datetime(2024, 4, 1, tzinfo=UTC),
        "build_id": "build-1", "ayanamsha_id": "lahiri_chitrapaksha",
        "verification_pass_status": "two_pass_verified",
        "applies_to_this_chart_flag": True, "system_id": "vimshottari",
    })

    result = period_context(
        conn, CHART, datetime(2024, 2, 1, tzinfo=UTC), "vimshottari",
        build_id="build-1", ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified",
    )

    assert "Rahu" not in result.lords.values()


def test_boundaries_can_be_projected_to_one_hierarchy_level() -> None:
    conn = _ClockConnection()

    result = boundaries(
        conn, CHART, "vimshottari", build_id="build-1",
        ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified", level="PD",
    )

    assert [row.source_row_id for row in result] == ["pd-mercury"]


def test_boundary_and_context_preserve_window_truncation() -> None:
    conn = _ClockConnection()
    conn.rows[0]["is_truncated_at_window_start"] = True
    conn.rows[0]["is_truncated_at_window_end"] = True

    result = boundaries(
        conn, CHART, "vimshottari", build_id="build-1",
        ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified", level="MD",
    )
    context = period_context(
        conn, CHART, datetime(2024, 2, 1, tzinfo=UTC), "vimshottari",
        build_id="build-1", ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified",
    )

    assert result[0].boundary_truncated is True
    assert context.boundary_truncated is True


def test_active_descendant_without_its_parent_is_hierarchy_unavailable() -> None:
    conn = _ClockConnection()
    conn.rows = [row for row in conn.rows if row["dasha_row_id"] != "ad-moon"]

    with pytest.raises(RuntimeError, match="hierarchy_unavailable"):
        period_context(
            conn, CHART, datetime(2024, 2, 1, tzinfo=UTC), "vimshottari",
            build_id="build-1", ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified",
        )


def test_active_deepest_period_without_its_parent_is_hierarchy_unavailable() -> None:
    """An active SD cannot be silently omitted when its PD link is broken."""
    conn = _ClockConnection()
    next(row for row in conn.rows if row["dasha_row_id"] == "sd-jupiter")["parent_row_id"] = "absent-pd"

    with pytest.raises(RuntimeError, match="hierarchy_unavailable"):
        period_context(
            conn, CHART, datetime(2024, 2, 1, tzinfo=UTC), "vimshottari",
            build_id="build-1", ayanamsha_id="lahiri_chitrapaksha", tier="two_pass_verified",
        )
