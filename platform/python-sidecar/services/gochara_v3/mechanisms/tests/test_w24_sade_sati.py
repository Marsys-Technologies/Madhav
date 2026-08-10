"""
Tests for W2.4: services/gochara_v3/mechanisms/w24_sade_sati.py

All tests are fixture-based (no DB). They construct synthetic
ClassContext-like objects and synthetic sade_sati_phases tuples that
mirror the exact schema ga_sade_sati_writer.py writes to chart_facts.

Chart_facts row structure for sade_sati_phases:
  {
    "fact_category": "sade_sati_phase" | "sade_sati_cancellation_check" | "sade_sati_cycle",
    "fact_subject":  "CY_2017.JANMA"  | "CY_2017",
    "fact_key":      "phase_start_iso" | "phase_end_iso" | "cancellation_active_flag" | ...,
    "fact_value_text": "2017-10-26T00:00:00+00:00",
    "fact_value_num": None,
  }
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from services.gochara_v3.mechanisms.w24_sade_sati import (
    MECHANISM_ID,
    PHASE_MODIFIERS,
    CANCELLATION_STEP_DOWN,
    MechanismResult,
    compute,
    _iso_to_jd,
    _extract_phase_intervals,
    _extract_cancellation_by_cycle,
)


# ---------------------------------------------------------------------------
# Helpers: build synthetic chart_facts rows in ga_sade_sati schema
# ---------------------------------------------------------------------------

def _phase_rows(cycle_id: str, phase_name: str, start_iso: str, end_iso: str) -> list[dict]:
    """Build the minimal sade_sati_phase rows for one phase window."""
    subj = f"{cycle_id}.{phase_name}"
    return [
        {
            "fact_category": "sade_sati_phase",
            "fact_subject": subj,
            "fact_key": "phase_start_iso",
            "fact_value_text": start_iso,
            "fact_value_num": None,
        },
        {
            "fact_category": "sade_sati_phase",
            "fact_subject": subj,
            "fact_key": "phase_end_iso",
            "fact_value_text": end_iso,
            "fact_value_num": None,
        },
    ]


def _cancellation_rows(
    cycle_id: str,
    active: bool,
    rules_fired: list[str] | None = None,
) -> list[dict]:
    """Build sade_sati_cancellation_check rows for a cycle."""
    rules = rules_fired or []
    return [
        {
            "fact_category": "sade_sati_cancellation_check",
            "fact_subject": cycle_id,
            "fact_key": "cancellation_active_flag",
            "fact_value_text": "true" if active else "false",
            "fact_value_num": None,
        },
        {
            "fact_category": "sade_sati_cancellation_check",
            "fact_subject": cycle_id,
            "fact_key": "cancellation_rules_invoked_jsonb",
            "fact_value_text": json.dumps(rules) if rules else "",
            "fact_value_num": None,
        },
    ]


def _build_context(
    sade_sati_phases: tuple[dict, ...],
    is_adverse: bool = True,
) -> SimpleNamespace:
    """Build a minimal context-like object with the fields compute() reads."""
    return SimpleNamespace(
        sade_sati_phases=sade_sati_phases,
        is_adverse=is_adverse,
    )


# ---------------------------------------------------------------------------
# JD reference values for test dates
# JD(2017-10-26) ≈ 2458052.5, JD(2020-06-15) ≈ 2458985.5
# We use _iso_to_jd() for precision.
# ---------------------------------------------------------------------------

_START_PEAK = "2017-10-26T00:00:00+00:00"
_END_PEAK   = "2020-06-15T00:00:00+00:00"
_START_RISE = "2015-01-01T00:00:00+00:00"
_END_RISE   = "2017-10-26T00:00:00+00:00"
_START_SET  = "2020-06-15T00:00:00+00:00"
_END_SET    = "2022-12-31T00:00:00+00:00"

# A JD firmly inside the peak phase window (2018-01-01 ≈ JD 2458120)
_JD_IN_PEAK   = _iso_to_jd("2018-01-01T00:00:00+00:00")
# A JD firmly inside the rising phase window (2016-01-01 ≈ JD 2457389)
_JD_IN_RISING = _iso_to_jd("2016-06-01T00:00:00+00:00")
# A JD firmly inside the setting phase window (2021-01-01 ≈ JD 2459216)
_JD_IN_SET    = _iso_to_jd("2021-01-01T00:00:00+00:00")
# A JD completely outside all windows
_JD_OUTSIDE   = _iso_to_jd("2025-01-01T00:00:00+00:00")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDisabled:
    """test_disabled_returns_unit_modifier"""

    def test_disabled_returns_unit_modifier(self):
        """When enabled=False, compute() returns modifier==1.0 unconditionally."""
        peak_rows = _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
        ctx = _build_context(tuple(peak_rows), is_adverse=True)

        result = compute(ctx, _JD_IN_PEAK, enabled=False)

        assert isinstance(result, MechanismResult)
        assert result.modifier == 1.0
        assert result.fired is False
        assert result.mechanism_id == MECHANISM_ID
        assert result.detail.get("reason") == "disabled"

    def test_disabled_also_unit_for_non_adverse(self):
        """Disabled returns unit regardless of is_adverse flag."""
        ctx = _build_context((), is_adverse=False)
        result = compute(ctx, _JD_IN_PEAK, enabled=False)
        assert result.modifier == 1.0
        assert result.fired is False


class TestNotInSadeSati:
    """test_not_in_sade_sati: empty phases → modifier==1.0"""

    def test_empty_sade_sati_phases_returns_unit(self):
        """Empty sade_sati_phases → modifier==1.0, honest reason recorded."""
        ctx = _build_context((), is_adverse=True)
        result = compute(ctx, _JD_IN_PEAK)

        assert result.modifier == 1.0
        assert result.fired is False
        assert result.detail.get("reason") == "no_sade_sati_phases"

    def test_t_jd_outside_all_windows_returns_unit(self):
        """t_jd outside all phase windows → modifier==1.0."""
        rows = (
            _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
            + _phase_rows("CY_2017", "VISHAKHA", _START_RISE, _END_RISE)
            + _phase_rows("CY_2017", "ANUMUKHA", _START_SET, _END_SET)
        )
        ctx = _build_context(tuple(rows), is_adverse=True)

        result = compute(ctx, _JD_OUTSIDE)

        assert result.modifier == 1.0
        assert result.fired is False
        assert result.detail.get("reason") == "not_in_sade_sati"


class TestPeakPhase:
    """test_peak_phase_amplifies: t_jd in peak phase → modifier==1.30"""

    def test_peak_phase_amplifies_adverse(self):
        """JANMA phase (peak) → modifier == PHASE_MODIFIERS['peak'] == 1.30."""
        rows = _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
        ctx = _build_context(tuple(rows), is_adverse=True)

        result = compute(ctx, _JD_IN_PEAK)

        assert result.modifier == pytest.approx(PHASE_MODIFIERS["peak"])  # 1.30
        assert result.fired is True
        assert result.detail["phase_type"] == "peak"
        assert result.detail["phase_name"] == "JANMA"
        assert result.detail["cycle_id"] == "CY_2017"
        assert result.detail["is_adverse"] is True

    def test_peak_phase_no_effect_on_non_adverse(self):
        """JANMA phase for a non-adverse event class → modifier == 1.0 (no amplification)."""
        rows = _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
        ctx = _build_context(tuple(rows), is_adverse=False)

        result = compute(ctx, _JD_IN_PEAK)

        assert result.modifier == 1.0
        assert result.fired is False
        assert result.detail.get("reason") == "not_adverse_class"
        # The suppressed modifier should still be recorded for audit
        assert result.detail.get("base_modifier_suppressed") == pytest.approx(PHASE_MODIFIERS["peak"])


class TestRisingPhase:
    """test_rising_phase: t_jd in rising phase → modifier==1.15"""

    def test_rising_phase_modifier(self):
        """VISHAKHA phase (rising) → modifier == PHASE_MODIFIERS['rising'] == 1.15."""
        rows = _phase_rows("CY_2017", "VISHAKHA", _START_RISE, _END_RISE)
        ctx = _build_context(tuple(rows), is_adverse=True)

        result = compute(ctx, _JD_IN_RISING)

        assert result.modifier == pytest.approx(PHASE_MODIFIERS["rising"])  # 1.15
        assert result.fired is True
        assert result.detail["phase_type"] == "rising"
        assert result.detail["phase_name"] == "VISHAKHA"


class TestSettingPhase:
    def test_setting_phase_modifier(self):
        """ANUMUKHA phase (setting) → modifier == PHASE_MODIFIERS['setting'] == 1.10."""
        rows = _phase_rows("CY_2017", "ANUMUKHA", _START_SET, _END_SET)
        ctx = _build_context(tuple(rows), is_adverse=True)

        result = compute(ctx, _JD_IN_SET)

        assert result.modifier == pytest.approx(PHASE_MODIFIERS["setting"])  # 1.10
        assert result.fired is True
        assert result.detail["phase_type"] == "setting"


class TestCancellationRules:
    """test_cancellation_recorded: when cancellation rule fires, detail carries it"""

    def test_cancellation_recorded_in_detail(self):
        """When cancellation_active_flag=true, the detail carries cancellation info."""
        rows = (
            _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
            + _cancellation_rows("CY_2017", active=True, rules_fired=["saturn_exalted"])
        )
        ctx = _build_context(tuple(rows), is_adverse=True)

        result = compute(ctx, _JD_IN_PEAK)

        assert result.detail["cancellation_active"] is True
        assert "saturn_exalted" in result.detail["rules_fired"]
        assert result.detail["cancellation_step_down"] == pytest.approx(CANCELLATION_STEP_DOWN)

    def test_cancellation_steps_down_modifier(self):
        """Cancellation reduces modifier by CANCELLATION_STEP_DOWN."""
        rows = (
            _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
            + _cancellation_rows("CY_2017", active=True, rules_fired=["saturn_own_sign", "dispositor_strong"])
        )
        ctx = _build_context(tuple(rows), is_adverse=True)

        result = compute(ctx, _JD_IN_PEAK)

        expected = PHASE_MODIFIERS["peak"] - CANCELLATION_STEP_DOWN  # 1.30 - 0.05 = 1.25
        assert result.modifier == pytest.approx(expected)
        assert result.fired is True

    def test_multiple_cancellation_rules_all_recorded(self):
        """All fired cancellation rules appear in detail.rules_fired."""
        rules = ["saturn_vargottama", "saturn_exalted", "jupiter_aspect_to_saturn"]
        rows = (
            _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
            + _cancellation_rows("CY_2017", active=True, rules_fired=rules)
        )
        ctx = _build_context(tuple(rows), is_adverse=True)

        result = compute(ctx, _JD_IN_PEAK)

        assert result.detail["cancellation_active"] is True
        for rule in rules:
            assert rule in result.detail["rules_fired"]

    def test_no_cancellation_no_step_down(self):
        """When no cancellation fires, modifier is the full phase modifier."""
        rows = (
            _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
            + _cancellation_rows("CY_2017", active=False, rules_fired=[])
        )
        ctx = _build_context(tuple(rows), is_adverse=True)

        result = compute(ctx, _JD_IN_PEAK)

        assert result.modifier == pytest.approx(PHASE_MODIFIERS["peak"])
        assert result.detail["cancellation_active"] is False
        assert result.detail["cancellation_step_down"] == pytest.approx(0.0)


class TestMultipleCycles:
    """Multiple Sade Sati cycles (e.g. 1984 and 2017); pick the active one."""

    def test_selects_correct_cycle_for_t_jd(self):
        """With two cycles, compute() matches the right one for t_jd."""
        # CY_2017 — peak phase
        rows_2017 = _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
        # CY_1984 — much earlier, outside range for our test JD
        rows_1984 = _phase_rows("CY_1984", "JANMA",
                                 "1984-01-01T00:00:00+00:00",
                                 "1986-12-31T00:00:00+00:00")

        ctx = _build_context(tuple(rows_2017 + rows_1984), is_adverse=True)

        result_2017 = compute(ctx, _JD_IN_PEAK)
        assert result_2017.detail["cycle_id"] == "CY_2017"

        jd_1985 = _iso_to_jd("1985-06-01T00:00:00+00:00")
        result_1984 = compute(ctx, jd_1985)
        assert result_1984.detail["cycle_id"] == "CY_1984"


class TestIsoToJd:
    """Unit tests for the _iso_to_jd helper."""

    def test_known_epoch(self):
        """JD(1970-01-01T12:00:00Z) = 2440588.0 (noon UTC epoch standard)."""
        jd = _iso_to_jd("1970-01-01T12:00:00+00:00")
        assert jd == pytest.approx(2440588.0, abs=0.01)

    def test_date_only_string(self):
        """Date-only string parses without crash and gives a plausible JD."""
        jd = _iso_to_jd("2017-10-26")
        assert jd is not None
        assert 2458000 < jd < 2459000

    def test_bad_string_returns_none(self):
        """Unparseable string returns None without raising."""
        assert _iso_to_jd("not-a-date") is None
        assert _iso_to_jd("") is None
        assert _iso_to_jd(None) is None  # type: ignore[arg-type]


class TestExtractHelpers:
    """Unit tests for the internal extraction helpers."""

    def test_extract_phase_intervals_basic(self):
        """_extract_phase_intervals returns one entry per valid phase."""
        rows = (
            _phase_rows("CY_2017", "JANMA", _START_PEAK, _END_PEAK)
            + _phase_rows("CY_2017", "VISHAKHA", _START_RISE, _END_RISE)
        )
        intervals = _extract_phase_intervals(tuple(rows))
        assert len(intervals) == 2
        phase_types = {i["phase_type"] for i in intervals}
        assert phase_types == {"peak", "rising"}

    def test_extract_phase_intervals_ignores_wrong_category(self):
        """Rows with category != sade_sati_phase are ignored."""
        rows = _cancellation_rows("CY_2017", active=True)
        # Inject one cycle row (wrong category) alongside the cancellation rows
        rows_tuple = tuple(rows) + (
            {
                "fact_category": "sade_sati_cycle",
                "fact_subject": "CY_2017",
                "fact_key": "cycle_start_iso",
                "fact_value_text": "2015-01-01T00:00:00+00:00",
                "fact_value_num": None,
            },
        )
        intervals = _extract_phase_intervals(rows_tuple)
        assert intervals == []

    def test_extract_cancellation_by_cycle(self):
        """_extract_cancellation_by_cycle parses cancellation rows correctly."""
        rows = _cancellation_rows("CY_2017", active=True, rules_fired=["saturn_exalted"])
        result = _extract_cancellation_by_cycle(tuple(rows))

        assert "CY_2017" in result
        assert result["CY_2017"]["cancellation_active"] is True
        assert "saturn_exalted" in result["CY_2017"]["rules_fired"]

    def test_extract_cancellation_inactive_cycle(self):
        """Inactive cancellation gives cancellation_active=False."""
        rows = _cancellation_rows("CY_2017", active=False, rules_fired=[])
        result = _extract_cancellation_by_cycle(tuple(rows))

        assert result["CY_2017"]["cancellation_active"] is False
        assert result["CY_2017"]["rules_fired"] == []


class TestMechanismResultProperties:
    """Verify MechanismResult dataclass invariants."""

    def test_mechanism_id_matches_module_constant(self):
        """MechanismResult.mechanism_id should equal MECHANISM_ID."""
        ctx = _build_context((), is_adverse=True)
        result = compute(ctx, _JD_IN_PEAK, enabled=False)
        assert result.mechanism_id == MECHANISM_ID

    def test_result_is_frozen(self):
        """MechanismResult is frozen — attempts to mutate it raise FrozenInstanceError."""
        import dataclasses
        ctx = _build_context((), is_adverse=True)
        result = compute(ctx, _JD_IN_PEAK, enabled=False)
        with pytest.raises((dataclasses.FrozenInstanceError, AttributeError)):
            result.modifier = 99.0  # type: ignore[misc]

    def test_modifier_in_expected_range(self):
        """All possible outputs have modifier in [1.0, 1.30]."""
        phase_scenarios = [
            ("VISHAKHA", _JD_IN_RISING, _START_RISE, _END_RISE),
            ("JANMA",    _JD_IN_PEAK,   _START_PEAK,  _END_PEAK),
            ("ANUMUKHA", _JD_IN_SET,    _START_SET,   _END_SET),
        ]
        for phase_name, t_jd, start, end in phase_scenarios:
            rows = _phase_rows("CY_TEST", phase_name, start, end)
            ctx = _build_context(tuple(rows), is_adverse=True)
            result = compute(ctx, t_jd)
            assert 1.0 <= result.modifier <= 1.30, (
                f"modifier out of range for phase {phase_name}: {result.modifier}"
            )
