"""
test_phala_muhurta.py — Unit tests for phala.muhurta (BRAHMA-PH-4-4)

Tests:
    1. compute_muhurta_score — range assertions [0.0, 1.0], boundary conditions
    2. muhurta_finder — contract assertions (score range, action_type validation)
    3. muhurta_finder — provenance_envelope structure
    4. generate_muhurta_windows — returns >= 1 window for 90-day range (no DB)
    5. action_type validation — ValueError for invalid types
    6. _panchanga_quality_for_action — classical scoring heuristics

No live DB connection required. All DB calls are mocked via unittest.mock.
BRAHMA-PH-4-4
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ── Module under test ─────────────────────────────────────────────────────────

def _get_muhurta_module():
    from brahmagyan.phala import muhurta as muhurta_mod
    return muhurta_mod


# ── Fixtures ──────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"
DATE_RANGE_90 = {"start": "2026-06-04", "end": "2026-09-01"}
DATE_RANGE_30 = {"start": "2026-06-04", "end": "2026-07-04"}


# ── §1 — compute_muhurta_score ────────────────────────────────────────────────

class TestComputeMuhurtaScore:

    def test_score_is_zero_for_zero_inputs(self):
        mod = _get_muhurta_module()
        score = mod.compute_muhurta_score(0.0, 0.0, 0.0, 0.0)
        assert score == 0.0

    def test_score_is_one_for_maximum_inputs(self):
        mod = _get_muhurta_module()
        score = mod.compute_muhurta_score(1.0, 1.0, 1.0, 1.0)
        assert abs(score - 1.0) < 1e-9, f"Expected 1.0, got {score}"

    def test_score_in_range_for_average_inputs(self):
        mod = _get_muhurta_module()
        score = mod.compute_muhurta_score(0.6, 0.7, 0.5, 0.6)
        assert 0.0 <= score <= 1.0

    def test_score_clamped_to_zero_for_negative_inputs(self):
        mod = _get_muhurta_module()
        # Should clamp at 0.0 even with negative weighted sum
        score = mod.compute_muhurta_score(-1.0, 0.0, 0.0, 0.0)
        assert score >= 0.0

    def test_score_clamped_to_one_for_oversized_inputs(self):
        mod = _get_muhurta_module()
        # Should clamp at 1.0
        score = mod.compute_muhurta_score(2.0, 2.0, 2.0, 2.0)
        assert score <= 1.0

    def test_weighted_sum_correct(self):
        mod = _get_muhurta_module()
        # 0.40*0.8 + 0.30*0.6 + 0.20*0.5 + 0.10*0.4 = 0.32 + 0.18 + 0.10 + 0.04 = 0.64
        score = mod.compute_muhurta_score(0.8, 0.6, 0.5, 0.4)
        assert abs(score - 0.64) < 0.001, f"Expected 0.64, got {score}"

    def test_score_is_float(self):
        mod = _get_muhurta_module()
        score = mod.compute_muhurta_score(0.5, 0.5, 0.5, 0.5)
        assert isinstance(score, float)


# ── §2 — muhurta_finder — action_type validation ─────────────────────────────

class TestMuhurtaFinderValidation:

    def test_invalid_action_type_raises_value_error(self):
        mod = _get_muhurta_module()
        with pytest.raises(ValueError, match="Invalid action_type"):
            mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="INVALID_TYPE",
                date_range=DATE_RANGE_30,
            )

    def test_all_7_valid_action_types_accepted(self):
        mod = _get_muhurta_module()
        valid_types = [
            "marriage", "travel", "business", "medical",
            "education", "property", "general",
        ]
        for at in valid_types:
            with patch.object(mod, "fetch_muhurta_windows", return_value=[]):
                result = mod.muhurta_finder(
                    chart_id=NATIVE_CHART_ID,
                    action_type=at,
                    date_range=DATE_RANGE_30,
                )
                assert result["ok"] is True, f"action_type '{at}' should be accepted"
                assert result["action_type"] == at

    def test_date_range_start_after_end_raises(self):
        mod = _get_muhurta_module()
        with pytest.raises(ValueError, match="must not be after"):
            mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                date_range={"start": "2026-09-01", "end": "2026-06-01"},
            )

    def test_date_range_over_90_days_raises(self):
        mod = _get_muhurta_module()
        with pytest.raises(ValueError, match="90 days"):
            mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                date_range={"start": "2026-01-01", "end": "2027-01-01"},
            )

    def test_min_score_out_of_range_raises(self):
        mod = _get_muhurta_module()
        with patch.object(mod, "fetch_muhurta_windows", return_value=[]):
            with pytest.raises(ValueError, match="min_score"):
                mod.muhurta_finder(
                    chart_id=NATIVE_CHART_ID,
                    action_type="general",
                    date_range=DATE_RANGE_30,
                    min_score=1.5,
                )

    def test_invalid_date_format_raises(self):
        mod = _get_muhurta_module()
        with pytest.raises((ValueError, KeyError)):
            mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                date_range={"start": "not-a-date", "end": "2026-07-04"},
            )


# ── §3 — muhurta_finder — response structure ─────────────────────────────────

class TestMuhurtaFinderResponseStructure:

    def _make_window(
        self,
        score: float = 0.65,
        action_type: str = "education",
    ) -> dict[str, Any]:
        return {
            "muhurta_id": None,
            "action_type": action_type,
            "window_start": "2026-06-04T00:00:00+00:00",
            "window_end": "2026-06-06T00:00:00+00:00",
            "auspiciousness_score": score,
            "factors": {
                "panchanga_quality": 0.75,
                "dasha_quality": 0.72,
                "transit_quality": 0.60,
                "signal_activation": 0.78,
                "panchanga_details": {
                    "tithi_name": "Shukla Dvadashi",
                    "vara_lord": "Mercury",
                    "moon_nakshatra": "Pushya",
                    "yoga": "Brahma",
                    "inauspicious_windows": [],
                },
                "dasha_details": {"md_lord": "Mercury", "ad_lord": "Mercury"},
                "avoid_notes": [],
            },
            "source_citation": (
                "FORENSIC v8.0 §5.1 DSH.V.023; panchanga_daily 2026-06-04; "
                "MSR v5.0 SIG.08; BPHS ch.46; PH-4-4"
            ),
        }

    def test_ok_field_is_true(self):
        mod = _get_muhurta_module()
        w = self._make_window()
        with patch.object(mod, "fetch_muhurta_windows", return_value=[w]):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="education",
                date_range=DATE_RANGE_30,
            )
        assert result["ok"] is True

    def test_chart_id_echoed(self):
        mod = _get_muhurta_module()
        with patch.object(mod, "fetch_muhurta_windows", return_value=[]):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                date_range=DATE_RANGE_30,
            )
        assert result["chart_id"] == NATIVE_CHART_ID

    def test_action_type_echoed(self):
        mod = _get_muhurta_module()
        with patch.object(mod, "fetch_muhurta_windows", return_value=[]):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="marriage",
                date_range=DATE_RANGE_30,
            )
        assert result["action_type"] == "marriage"

    def test_query_window_present(self):
        mod = _get_muhurta_module()
        with patch.object(mod, "fetch_muhurta_windows", return_value=[]):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                date_range=DATE_RANGE_30,
            )
        assert "query_window" in result
        assert result["query_window"]["start"] == DATE_RANGE_30["start"]
        assert result["query_window"]["end"] == DATE_RANGE_30["end"]

    def test_provenance_envelope_present(self):
        mod = _get_muhurta_module()
        with patch.object(mod, "fetch_muhurta_windows", return_value=[]):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                date_range=DATE_RANGE_30,
            )
        env = result["provenance_envelope"]
        assert env["source"] == "phala.muhurta"
        assert env["asset"] == "PH-4-4"
        assert "algorithm" in env
        assert "queried_at" in env
        assert "l1_ground_truth" in env
        assert "b3_citation_compliant" in env

    def test_windows_is_list(self):
        mod = _get_muhurta_module()
        w = self._make_window()
        with patch.object(mod, "fetch_muhurta_windows", return_value=[w]):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="education",
                date_range=DATE_RANGE_30,
            )
        assert isinstance(result["windows"], list)

    def test_window_count_matches_windows_length(self):
        mod = _get_muhurta_module()
        w = self._make_window()
        with patch.object(mod, "fetch_muhurta_windows", return_value=[w, w]):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="education",
                date_range=DATE_RANGE_30,
            )
        assert result["window_count"] == len(result["windows"])


# ── §4 — generate_muhurta_windows (no DB) ────────────────────────────────────

class TestGenerateMuhurtaWindows:

    def test_returns_at_least_one_window_for_90_day_range(self):
        mod = _get_muhurta_module()
        windows = mod.generate_muhurta_windows(
            chart_id=NATIVE_CHART_ID,
            action_type="general",
            range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
            range_end=datetime(2026, 9, 1, 23, 59, 59, tzinfo=timezone.utc),
            min_score=0.0,
            limit=45,
        )
        assert len(windows) >= 1, "Expected at least 1 window for a 90-day range"

    def test_all_scores_in_range(self):
        mod = _get_muhurta_module()
        windows = mod.generate_muhurta_windows(
            chart_id=NATIVE_CHART_ID,
            action_type="education",
            range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
            range_end=datetime(2026, 7, 4, 23, 59, 59, tzinfo=timezone.utc),
            min_score=0.0,
            limit=20,
        )
        for w in windows:
            score = w["auspiciousness_score"]
            assert 0.0 <= score <= 1.0, f"Score {score} out of range [0.0, 1.0]"

    def test_source_citation_non_null_on_all_windows(self):
        """B.3 mandate: source_citation is NON-NULL on every row."""
        mod = _get_muhurta_module()
        windows = mod.generate_muhurta_windows(
            chart_id=NATIVE_CHART_ID,
            action_type="general",
            range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
            range_end=datetime(2026, 6, 30, 23, 59, 59, tzinfo=timezone.utc),
            min_score=0.0,
            limit=20,
        )
        for w in windows:
            assert w.get("source_citation"), "source_citation must be non-null (B.3 mandate)"

    def test_windows_sorted_by_score_desc(self):
        mod = _get_muhurta_module()
        windows = mod.generate_muhurta_windows(
            chart_id=NATIVE_CHART_ID,
            action_type="education",
            range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
            range_end=datetime(2026, 8, 4, 23, 59, 59, tzinfo=timezone.utc),
            min_score=0.0,
            limit=20,
        )
        if len(windows) >= 2:
            scores = [w["auspiciousness_score"] for w in windows]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1], (
                    f"Windows not sorted by score DESC: {scores[i]} < {scores[i+1]} at index {i}"
                )

    def test_min_score_filter_applied(self):
        mod = _get_muhurta_module()
        min_score = 0.60
        windows = mod.generate_muhurta_windows(
            chart_id=NATIVE_CHART_ID,
            action_type="general",
            range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
            range_end=datetime(2026, 9, 1, 23, 59, 59, tzinfo=timezone.utc),
            min_score=min_score,
            limit=45,
        )
        for w in windows:
            assert w["auspiciousness_score"] >= min_score, (
                f"Window score {w['auspiciousness_score']} below min_score {min_score}"
            )

    def test_factors_structure_present(self):
        mod = _get_muhurta_module()
        windows = mod.generate_muhurta_windows(
            chart_id=NATIVE_CHART_ID,
            action_type="education",
            range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
            range_end=datetime(2026, 6, 20, 23, 59, 59, tzinfo=timezone.utc),
            min_score=0.0,
            limit=5,
        )
        for w in windows:
            f = w.get("factors", {})
            assert "panchanga_quality" in f
            assert "dasha_quality" in f
            assert "transit_quality" in f
            assert "signal_activation" in f
            assert "panchanga_details" in f
            assert "avoid_notes" in f

    def test_limit_respected(self):
        mod = _get_muhurta_module()
        limit = 5
        windows = mod.generate_muhurta_windows(
            chart_id=NATIVE_CHART_ID,
            action_type="general",
            range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
            range_end=datetime(2026, 9, 1, 23, 59, 59, tzinfo=timezone.utc),
            min_score=0.0,
            limit=limit,
        )
        assert len(windows) <= limit


# ── §5 — _panchanga_quality_for_action ───────────────────────────────────────

class TestPanchangaQualityForAction:

    def test_pushya_nakshatra_gives_high_education_quality(self):
        mod = _get_muhurta_module()
        quality = mod._panchanga_quality_for_action(
            tithi_name="Shukla Panchami",
            vara_lord="Wednesday",
            moon_nakshatra="Pushya",
            yoga="Brahma",
            action_type="education",
        )
        assert quality >= 0.70, f"Pushya/Wed should give high education quality, got {quality}"

    def test_rohini_nakshatra_gives_high_marriage_quality(self):
        mod = _get_muhurta_module()
        quality = mod._panchanga_quality_for_action(
            tithi_name="Shukla Panchami",
            vara_lord="Thursday",
            moon_nakshatra="Rohini",
            yoga="Siddha",
            action_type="marriage",
        )
        assert quality >= 0.70, f"Rohini/Thursday should give high marriage quality, got {quality}"

    def test_ashtami_tithi_reduces_quality(self):
        mod = _get_muhurta_module()
        quality = mod._panchanga_quality_for_action(
            tithi_name="Krishna Ashtami",
            vara_lord="Thursday",
            moon_nakshatra="Rohini",
            yoga="Brahma",
            action_type="marriage",
        )
        # Ashtami is inauspicious — should reduce tithi component
        assert quality < 0.85, f"Ashtami tithi should reduce quality, got {quality}"

    def test_inauspicious_yoga_caps_score(self):
        mod = _get_muhurta_module()
        quality = mod._panchanga_quality_for_action(
            tithi_name="Shukla Panchami",
            vara_lord="Thursday",
            moon_nakshatra="Rohini",
            yoga="Vishkumbha",  # inauspicious yoga
            action_type="marriage",
        )
        # Vishkumbha yoga is inauspicious — overall quality should be lower
        quality_good_yoga = mod._panchanga_quality_for_action(
            tithi_name="Shukla Panchami",
            vara_lord="Thursday",
            moon_nakshatra="Rohini",
            yoga="Siddha",  # auspicious yoga
            action_type="marriage",
        )
        assert quality < quality_good_yoga, (
            "Inauspicious yoga should yield lower quality than auspicious yoga"
        )

    def test_result_always_in_range(self):
        mod = _get_muhurta_module()
        for action_type in ["marriage", "travel", "business", "medical", "education", "property", "general"]:
            quality = mod._panchanga_quality_for_action(
                tithi_name="Amavasya",
                vara_lord="Saturday",
                moon_nakshatra="Jyeshtha",
                yoga="Parigha",
                action_type=action_type,
            )
            assert 0.0 <= quality <= 1.0, (
                f"Quality {quality} out of range for action_type={action_type}"
            )
