"""
Tests for services/gochara_v3/mechanisms/w22_moorti_nirnaya.py

All tests are fixture-based — zero DB access. The ClassContext used here is
built from hand-crafted dataclass instances or simple mocks; no live connection
is ever opened.

Test inventory:
  test_disabled_returns_unit_modifier      — enabled=False → modifier exactly 1.0
  test_modifier_in_range                   — result always within [0.0, 2.0]
  test_svarna_amplifies                    — svarna → modifier > 1.0
  test_loha_damps                          — loha → modifier < 1.0
  test_rajata_amplifies_less_than_svarna   — rajata modifier between 1.0 and svarna
  test_tamra_damps_less_than_loha          — tamra modifier between loha and 1.0
  test_honest_empty_when_no_moorti_data    — no moorti_rows → modifier == 1.0
  test_no_computed_row_returns_unit        — moorti_computed=False → modifier == 1.0
  test_swarna_alias_accepted               — "swarna" romanisation → treated as svarna
  test_unrecognised_name_returns_unit      — garbage moorti_name → modifier == 1.0
  test_detail_carries_moorti_name          — detail dict populated on success
  test_mechanism_id_constant               — MechanismResult.mechanism_id correct
  test_window_boundary_inclusive           — date ON window_start / window_end counts
  test_date_outside_window_misses          — date outside all windows → no data
  test_multipliers_map_completeness        — MOORTI_MULTIPLIERS has all 4 keys
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timezone, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from services.gochara_v3.mechanisms.w22_moorti_nirnaya import (
    MECHANISM_ID,
    MOORTI_MULTIPLIERS,
    MOORTI_MULTIPLIER_LOHA,
    MOORTI_MULTIPLIER_SVARNA,
    MOORTI_MULTIPLIER_RAJATA,
    MOORTI_MULTIPLIER_TAMRA,
    MULTIPLIER_MAX,
    MULTIPLIER_MIN,
    MechanismResult,
    compute,
)


# ── Fixture helpers ────────────────────────────────────────────────────────────

def _jd_for(d: date) -> float:
    """Return a Julian Day Number for noon UTC on the given date."""
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    dt = datetime(d.year, d.month, d.day, 12, 0, 0, tzinfo=timezone.utc)
    days = (dt - epoch).total_seconds() / 86400.0
    return days + 2440587.5


def _make_context(moorti_rows: list[dict] | None = None) -> Any:
    """Return a minimal mock ClassContext that carries the given moorti_rows.

    The mechanism only needs:
      - context.moorti_rows  — list of row dicts (injected via getattr)
      - context.chart_id     — string (for logging)

    This helper attaches moorti_rows directly as an attribute so the module's
    `getattr(context, 'moorti_rows', None)` picks it up.
    """
    ctx = MagicMock()
    ctx.chart_id = "test-chart-fixture"
    # Attach as a plain attribute so getattr() works without MagicMock magic
    ctx.moorti_rows = moorti_rows
    return ctx


def _moorti_row(
    moorti_name: str,
    window_start: date,
    window_end: date,
    moorti_computed: bool = True,
) -> dict:
    return {
        "moorti_name": moorti_name,
        "window_start": window_start,
        "window_end": window_end,
        "moorti_computed": moorti_computed,
    }


# Reference date for most tests: a day solidly inside a test window.
_REF_DATE = date(2025, 6, 15)
_WINDOW_START = date(2025, 6, 1)
_WINDOW_END = date(2025, 7, 31)
_REF_JD = _jd_for(_REF_DATE)


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestDisabled:
    def test_disabled_returns_unit_modifier(self):
        """enabled=False must return modifier exactly 1.0, regardless of context."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("svarna", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD, enabled=False)
        assert result.modifier == 1.0, (
            f"disabled compute must return modifier=1.0, got {result.modifier}"
        )

    def test_disabled_result_enabled_flag_is_false(self):
        ctx = _make_context()
        result = compute(ctx, _REF_JD, enabled=False)
        assert result.enabled is False

    def test_disabled_mechanism_id_unchanged(self):
        ctx = _make_context()
        result = compute(ctx, _REF_JD, enabled=False)
        assert result.mechanism_id == MECHANISM_ID


class TestModifierRange:
    @pytest.mark.parametrize("moorti_name", ["svarna", "rajata", "tamra", "loha"])
    def test_modifier_in_range(self, moorti_name: str):
        """Modifier must always be within [0.0, 2.0] for all classical tiers."""
        ctx = _make_context(
            moorti_rows=[_moorti_row(moorti_name, _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert 0.0 <= result.modifier <= 2.0, (
            f"modifier={result.modifier} out of [0.0, 2.0] for {moorti_name}"
        )

    @pytest.mark.parametrize("moorti_name", ["svarna", "rajata", "tamra", "loha"])
    def test_modifier_within_declared_bounds(self, moorti_name: str):
        """Modifier must also satisfy the tighter [MULTIPLIER_MIN, MULTIPLIER_MAX]."""
        ctx = _make_context(
            moorti_rows=[_moorti_row(moorti_name, _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert MULTIPLIER_MIN <= result.modifier <= MULTIPLIER_MAX


class TestSvarnaAmplifies:
    def test_svarna_amplifies(self):
        """Svarna quality must produce modifier strictly greater than 1.0."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("svarna", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert result.modifier > 1.0, (
            f"svarna should amplify (modifier > 1.0), got {result.modifier}"
        )

    def test_svarna_modifier_value(self):
        ctx = _make_context(
            moorti_rows=[_moorti_row("svarna", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert math.isclose(result.modifier, MOORTI_MULTIPLIER_SVARNA, rel_tol=1e-9)


class TestLohaDamps:
    def test_loha_damps(self):
        """Loha quality must produce modifier strictly less than 1.0."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("loha", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert result.modifier < 1.0, (
            f"loha should damp (modifier < 1.0), got {result.modifier}"
        )

    def test_loha_modifier_value(self):
        ctx = _make_context(
            moorti_rows=[_moorti_row("loha", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert math.isclose(result.modifier, MOORTI_MULTIPLIER_LOHA, rel_tol=1e-9)


class TestHonestEmptyWhenNoMoortiData:
    def test_honest_empty_when_no_moorti_data(self):
        """When context carries no moorti_rows at all, modifier must be 1.0."""
        ctx = _make_context(moorti_rows=None)
        result = compute(ctx, _REF_JD)
        assert result.modifier == 1.0, (
            f"no moorti data should yield modifier=1.0, got {result.modifier}"
        )

    def test_empty_moorti_rows_returns_unit(self):
        """Empty list is treated the same as None."""
        ctx = _make_context(moorti_rows=[])
        result = compute(ctx, _REF_JD)
        assert result.modifier == 1.0

    def test_detail_carries_reason_when_no_data(self):
        ctx = _make_context(moorti_rows=None)
        result = compute(ctx, _REF_JD)
        assert result.detail.get("reason") == "no_moorti_data"


class TestNotComputedRow:
    def test_no_computed_row_returns_unit(self):
        """A row with moorti_computed=False must be skipped → modifier=1.0."""
        ctx = _make_context(
            moorti_rows=[
                _moorti_row("svarna", _WINDOW_START, _WINDOW_END, moorti_computed=False)
            ]
        )
        result = compute(ctx, _REF_JD)
        assert result.modifier == 1.0, (
            "a non-computed moorti row must not contribute a modifier"
        )


class TestAliases:
    def test_swarna_alias_accepted(self):
        """The DB stores 'swarna' (with a 'w'); must be accepted and treated as svarna."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("swarna", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        # swarna → svarna normalisation → MOORTI_MULTIPLIER_SVARNA
        assert result.modifier > 1.0, (
            f"'swarna' alias should map to svarna (modifier > 1.0), got {result.modifier}"
        )
        assert math.isclose(result.modifier, MOORTI_MULTIPLIER_SVARNA, rel_tol=1e-9)


class TestUnrecognisedName:
    def test_unrecognised_name_returns_unit(self):
        """An unrecognised moorti_name (not in the normalisation map) must return
        modifier=1.0. _normalise_moorti_name('platinum') returns None, so
        _find_overlapping_moorti returns None, and compute reports no_moorti_data."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("platinum", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert result.modifier == 1.0

    def test_unrecognised_name_falls_back_to_no_moorti_data(self):
        """'platinum' is not in the normalisation map → treated as absent data.
        The reason is 'no_moorti_data' because normalisation returns None before
        the row can match — compute never sees a non-None unrecognised string."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("platinum", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        # The normalisation step maps unknown names to None, so the window is
        # skipped entirely and the result is indistinguishable from no data.
        assert result.detail.get("reason") == "no_moorti_data"

    def test_unrecognised_name_after_normalisation_returns_unit(self):
        """Test the unrecognised_moorti_name path: inject a row whose name
        passes _normalise_moorti_name but is absent from MOORTI_MULTIPLIERS.
        This is a defensive test for any future extension of the normalisation
        map that accidentally introduces a name not in the multipliers dict."""
        from unittest.mock import patch
        import services.gochara_v3.mechanisms.w22_moorti_nirnaya as mod

        # Patch _normalise_moorti_name to return a string not in MOORTI_MULTIPLIERS.
        with patch.object(mod, "_normalise_moorti_name", return_value="palladium"):
            ctx = _make_context(
                moorti_rows=[_moorti_row("palladium", _WINDOW_START, _WINDOW_END)]
            )
            result = compute(ctx, _REF_JD)
        assert result.modifier == 1.0
        assert result.detail.get("reason") == "unrecognised_moorti_name"


class TestDetailDict:
    def test_detail_carries_moorti_name(self):
        """On a successful quality application, detail must include moorti_name."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("rajata", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert "moorti_name" in result.detail
        assert result.detail["moorti_name"] == "rajata"

    def test_detail_carries_modifier_value(self):
        ctx = _make_context(
            moorti_rows=[_moorti_row("tamra", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert "modifier" in result.detail
        assert math.isclose(result.detail["modifier"], MOORTI_MULTIPLIER_TAMRA, rel_tol=1e-9)


class TestMechanismId:
    def test_mechanism_id_constant(self):
        """MechanismResult.mechanism_id must always equal MECHANISM_ID."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("svarna", _WINDOW_START, _WINDOW_END)]
        )
        result = compute(ctx, _REF_JD)
        assert result.mechanism_id == MECHANISM_ID

    def test_mechanism_id_on_no_data(self):
        ctx = _make_context(moorti_rows=None)
        result = compute(ctx, _REF_JD)
        assert result.mechanism_id == MECHANISM_ID

    def test_mechanism_id_value(self):
        assert MECHANISM_ID == "w22_moorti_nirnaya"


class TestWindowBoundaries:
    def test_window_boundary_start_inclusive(self):
        """A date exactly on window_start must count as inside the window."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("svarna", _WINDOW_START, _WINDOW_END)]
        )
        jd_on_start = _jd_for(_WINDOW_START)
        result = compute(ctx, jd_on_start)
        assert result.modifier > 1.0, "date on window_start must be inside the window"

    def test_window_boundary_end_inclusive(self):
        """A date exactly on window_end must count as inside the window."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("svarna", _WINDOW_START, _WINDOW_END)]
        )
        jd_on_end = _jd_for(_WINDOW_END)
        result = compute(ctx, jd_on_end)
        assert result.modifier > 1.0, "date on window_end must be inside the window"

    def test_date_outside_window_misses(self):
        """A date outside all windows must return modifier=1.0 (honest no-data)."""
        ctx = _make_context(
            moorti_rows=[_moorti_row("svarna", _WINDOW_START, _WINDOW_END)]
        )
        outside_date = _WINDOW_END + timedelta(days=1)
        jd_outside = _jd_for(outside_date)
        result = compute(ctx, jd_outside)
        assert result.modifier == 1.0, (
            f"date {outside_date} is outside window {_WINDOW_START}..{_WINDOW_END}; "
            f"expected modifier=1.0, got {result.modifier}"
        )


class TestMultipliersMap:
    def test_multipliers_map_completeness(self):
        """MOORTI_MULTIPLIERS must have exactly the four classical tier keys."""
        expected_keys = {"svarna", "rajata", "tamra", "loha"}
        assert set(MOORTI_MULTIPLIERS.keys()) == expected_keys

    def test_multiplier_ordering(self):
        """Classical ordering: svarna > rajata > 1.0 > tamra > loha."""
        assert MOORTI_MULTIPLIER_SVARNA > MOORTI_MULTIPLIER_RAJATA
        assert MOORTI_MULTIPLIER_RAJATA > 1.0
        assert 1.0 > MOORTI_MULTIPLIER_TAMRA
        assert MOORTI_MULTIPLIER_TAMRA > MOORTI_MULTIPLIER_LOHA

    def test_all_multipliers_in_module_bounds(self):
        for name, mult in MOORTI_MULTIPLIERS.items():
            assert MULTIPLIER_MIN <= mult <= MULTIPLIER_MAX, (
                f"{name} multiplier {mult} outside [{MULTIPLIER_MIN}, {MULTIPLIER_MAX}]"
            )


class TestIsoStringDates:
    def test_iso_string_window_dates_accepted(self):
        """Row dicts with ISO-string window_start/window_end must work correctly."""
        row = {
            "moorti_name": "loha",
            "window_start": _WINDOW_START.isoformat(),
            "window_end": _WINDOW_END.isoformat(),
            "moorti_computed": True,
        }
        ctx = _make_context(moorti_rows=[row])
        result = compute(ctx, _REF_JD)
        assert result.modifier < 1.0


class TestMultipleWindows:
    def test_first_matching_window_used(self):
        """When multiple windows exist, the first overlapping computed one wins."""
        rows = [
            _moorti_row("loha", date(2025, 5, 1), date(2025, 5, 31)),   # not overlapping
            _moorti_row("svarna", date(2025, 6, 1), date(2025, 6, 30)),  # overlapping
            _moorti_row("loha", date(2025, 7, 1), date(2025, 7, 31)),    # not overlapping
        ]
        ctx = _make_context(moorti_rows=rows)
        # _REF_DATE = 2025-06-15, inside the svarna window
        result = compute(ctx, _REF_JD)
        assert result.modifier > 1.0
        assert math.isclose(result.modifier, MOORTI_MULTIPLIER_SVARNA, rel_tol=1e-9)
