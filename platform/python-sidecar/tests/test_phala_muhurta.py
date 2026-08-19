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

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DATE_RANGE_90 = {"start": "2026-06-04", "end": "2026-09-01"}
DATE_RANGE_30 = {"start": "2026-06-04", "end": "2026-07-04"}


def _fetch_result(windows: list[dict[str, Any]]) -> dict[str, Any]:
    """
    R5.1 C3: fetch_muhurta_windows now returns a dict (windows + coverage
    diagnostics), not a bare list — see brahmagyan/phala/muhurta.py. Test
    helper to build that shape from a plain window list.
    """
    return {
        "windows": windows,
        "checked": len(windows),
        "skipped_no_panchanga": 0,
        "coverage": (None, None),
        "source": "phala_muhurta",
    }


def _empty_fetch_result() -> dict[str, Any]:
    return _fetch_result([])


def _fake_panchanga_row(
    tithi_name: str = "Shukla Panchami",
    vara_lord: str = "Wednesday",
    moon_nakshatra: str = "Hasta",
    yoga: str = "Shubha",
) -> dict[str, str]:
    """
    Simulate a real panchanga_daily row (as R5.1 C3's generate_muhurta_windows
    now requires — it never fabricates panchanga data itself; a missing DB
    row is skipped, not defaulted). Tests that exercise generate_muhurta_windows
    without a live DB patch _fetch_panchanga_row to return rows shaped like this.
    """
    return {
        "tithi_name": tithi_name,
        "vara_lord": vara_lord,
        "moon_nakshatra": moon_nakshatra,
        "yoga": yoga,
    }


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
            with patch.object(mod, "fetch_muhurta_windows", return_value=_empty_fetch_result()):
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
        with patch.object(mod, "fetch_muhurta_windows", return_value=_empty_fetch_result()):
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


class TestF47ActionSensitiveDasha:
    def test_live_dasha_quality_uses_canonical_action_significators(self):
        """F-47: identical live lords must not yield one action-agnostic score.

        The activity ontology distinguishes marriage (Venus/Jupiter) from a
        business start (Mercury/Jupiter/Sun).  With Mercury MD and Saturn AD,
        the business score must therefore be higher than marriage; this
        assertion prevents the old fixed native-chart score from returning the
        same value for every requested action.
        """
        mod = _get_muhurta_module()
        at = datetime(2026, 8, 19, tzinfo=timezone.utc)
        live_lords = {"md_lord": "Mercury", "ad_lord": "Saturn"}
        ontology = {
            "marriage": ["Venus", "Jupiter"],
            "business": ["Mercury", "Jupiter", "Sun"],
        }

        with patch.object(mod, "_current_dasha_lords", return_value=live_lords), \
             patch.object(mod, "_activity_significators_for_action", side_effect=lambda action: ontology[action]):
            marriage = mod._dasha_quality_for_chart(NATIVE_CHART_ID, at, "marriage")
            business = mod._dasha_quality_for_chart(NATIVE_CHART_ID, at, "business")

        assert business > marriage

    def test_weekday_overlay_uses_canonical_action_significators(self):
        """F-47: the weekday component cannot be one action-agnostic table."""
        mod = _get_muhurta_module()
        # 2026-08-19 is Wednesday / Mercury's weekday.
        at = datetime(2026, 8, 19, tzinfo=timezone.utc)
        ontology = {
            "marriage": ["Venus", "Jupiter"],
            "business": ["Mercury", "Jupiter", "Sun"],
        }

        with patch.object(mod, "_activity_significators_for_action", side_effect=lambda action: ontology[action]):
            marriage = mod._transit_quality_for_window(at, "marriage")
            business = mod._transit_quality_for_window(at, "business")

        assert business > marriage


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
        with patch.object(mod, "fetch_muhurta_windows", return_value=_fetch_result([w])):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="education",
                date_range=DATE_RANGE_30,
            )
        assert result["ok"] is True

    def test_chart_id_echoed(self):
        mod = _get_muhurta_module()
        with patch.object(mod, "fetch_muhurta_windows", return_value=_empty_fetch_result()):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                date_range=DATE_RANGE_30,
            )
        assert result["chart_id"] == NATIVE_CHART_ID

    def test_action_type_echoed(self):
        mod = _get_muhurta_module()
        with patch.object(mod, "fetch_muhurta_windows", return_value=_empty_fetch_result()):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="marriage",
                date_range=DATE_RANGE_30,
            )
        assert result["action_type"] == "marriage"

    def test_query_window_present(self):
        mod = _get_muhurta_module()
        with patch.object(mod, "fetch_muhurta_windows", return_value=_empty_fetch_result()):
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
        with patch.object(mod, "fetch_muhurta_windows", return_value=_empty_fetch_result()):
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
        with patch.object(mod, "fetch_muhurta_windows", return_value=_fetch_result([w])):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="education",
                date_range=DATE_RANGE_30,
            )
        assert isinstance(result["windows"], list)

    def test_window_count_matches_windows_length(self):
        mod = _get_muhurta_module()
        w = self._make_window()
        with patch.object(mod, "fetch_muhurta_windows", return_value=_fetch_result([w, w])):
            result = mod.muhurta_finder(
                chart_id=NATIVE_CHART_ID,
                action_type="education",
                date_range=DATE_RANGE_30,
            )
        assert result["window_count"] == len(result["windows"])


# ── §4 — generate_muhurta_windows (real-panchanga-shaped rows, DB mocked) ────
#
# R5.1 C3: generate_muhurta_windows() no longer fabricates panchanga data when
# the DB is unreachable — a missing panchanga_daily row is SKIPPED, never
# defaulted (B.10). These tests now patch _get_db_url + _fetch_panchanga_row
# to simulate a populated panchanga_daily cache, and unwrap the dict return
# shape ({"windows": [...], "checked", "skipped_no_panchanga", "coverage"}).

class TestGenerateMuhurtaWindows:

    def _patched(self, mod):
        """
        Context-manager tuple: fake DB url + every date resolves to a real-shaped
        row + coverage lookup short-circuited (no live network attempt in tests).

        T-8 fix (D-1.6 S-1): generate_muhurta_windows now also calls
        _current_dasha_lords() per window (live chart_dashas lookup, replacing the
        old hardcoded "Mercury MD (2026-2043)" citation) — mocked here the same way
        _fetch_panchanga_row already was, so these tests never attempt a real
        psycopg.connect() against the fake DB URL.
        """
        return (
            patch.object(mod, "_get_db_url", return_value="postgresql://fake/test"),
            patch.object(mod, "_fetch_panchanga_row", return_value=_fake_panchanga_row()),
            patch.object(mod, "_panchanga_coverage", return_value=("2026-06-01", "2027-06-01")),
            patch.object(mod, "_current_dasha_lords", return_value={
                "md_lord": "Mercury", "md_start": "2010-08-17", "md_end": "2027-08-17",
                "ad_lord": "Saturn",
            }),
            patch.object(mod, "_activity_significators_for_action", return_value=None),
            patch.object(mod, "_fetch_tara_bala_baseline", return_value={}),
        )

    def test_returns_at_least_one_window_for_90_day_range(self):
        mod = _get_muhurta_module()
        p1, p2, p3, p4, p5, p6 = self._patched(mod)
        with p1, p2, p3, p4, p5, p6:
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 9, 1, 23, 59, 59, tzinfo=timezone.utc),
                min_score=0.0,
                limit=45,
            )
        assert len(result["windows"]) >= 1, "Expected at least 1 window for a 90-day range"
        assert result["skipped_no_panchanga"] == 0

    def test_no_db_skips_every_window_never_fabricates(self):
        """B.10: with no DB reachable, every window is skipped — never defaulted."""
        mod = _get_muhurta_module()
        with patch.object(mod, "_get_db_url", side_effect=RuntimeError("no DB")):
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 6, 10, 23, 59, 59, tzinfo=timezone.utc),
                min_score=0.0,
                limit=45,
            )
        assert result["windows"] == []
        assert result["checked"] >= 1
        assert result["skipped_no_panchanga"] == result["checked"]

    def test_all_scores_in_range(self):
        mod = _get_muhurta_module()
        p1, p2, p3, p4, p5, p6 = self._patched(mod)
        with p1, p2, p3, p4, p5, p6:
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="education",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 7, 4, 23, 59, 59, tzinfo=timezone.utc),
                min_score=0.0,
                limit=20,
            )
        for w in result["windows"]:
            score = w["auspiciousness_score"]
            assert 0.0 <= score <= 1.0, f"Score {score} out of range [0.0, 1.0]"

    def test_source_citation_non_null_on_all_windows(self):
        """B.3 mandate: source_citation is NON-NULL on every row."""
        mod = _get_muhurta_module()
        p1, p2, p3, p4, p5, p6 = self._patched(mod)
        with p1, p2, p3, p4, p5, p6:
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 6, 30, 23, 59, 59, tzinfo=timezone.utc),
                min_score=0.0,
                limit=20,
            )
        for w in result["windows"]:
            assert w.get("source_citation"), "source_citation must be non-null (B.3 mandate)"

    def test_windows_sorted_by_score_desc(self):
        mod = _get_muhurta_module()
        p1, p2, p3, p4, p5, p6 = self._patched(mod)
        with p1, p2, p3, p4, p5, p6:
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="education",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 8, 4, 23, 59, 59, tzinfo=timezone.utc),
                min_score=0.0,
                limit=20,
            )
        windows = result["windows"]
        if len(windows) >= 2:
            scores = [w["auspiciousness_score"] for w in windows]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1], (
                    f"Windows not sorted by score DESC: {scores[i]} < {scores[i+1]} at index {i}"
                )

    def test_min_score_filter_applied(self):
        mod = _get_muhurta_module()
        min_score = 0.60
        p1, p2, p3, p4, p5, p6 = self._patched(mod)
        with p1, p2, p3, p4, p5, p6:
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 9, 1, 23, 59, 59, tzinfo=timezone.utc),
                min_score=min_score,
                limit=45,
            )
        for w in result["windows"]:
            assert w["auspiciousness_score"] >= min_score, (
                f"Window score {w['auspiciousness_score']} below min_score {min_score}"
            )

    def test_factors_structure_present(self):
        mod = _get_muhurta_module()
        p1, p2, p3, p4, p5, p6 = self._patched(mod)
        with p1, p2, p3, p4, p5, p6:
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="education",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 6, 20, 23, 59, 59, tzinfo=timezone.utc),
                min_score=0.0,
                limit=5,
            )
        for w in result["windows"]:
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
        p1, p2, p3, p4, p5, p6 = self._patched(mod)
        with p1, p2, p3, p4, p5, p6:
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 9, 1, 23, 59, 59, tzinfo=timezone.utc),
                min_score=0.0,
                limit=limit,
            )
        assert len(result["windows"]) <= limit


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


# ── §7 — T-8 fix: live dasha-lord citation (D-1.6 S-1) ───────────────────────
#
# Regression coverage for the T-8 fix: the muhurta citation used to hardcode
# "FORENSIC v8.0 §5.1 DSH.V.023 Mercury MD (2026-2043)" on every window
# regardless of chart or date — wrong even for the native, whose actual
# Mercury MD (per chart_dashas) runs 2010-08-17 -> 2027-08-17. These tests
# pin the fix: (1) _current_dasha_lords queries chart_dashas, not a hardcoded
# literal; (2) the built citation never contains the stale "2026-2043" string;
# (3) an honest fallback when no chart_dashas row matches (never fabricated).

class TestLiveDashaCitation:

    def _mock_conn(self, mod, md_row, ad_row):
        """Build a psycopg-connect mock returning md_row then ad_row (2 cursor.execute calls)."""
        cursor = MagicMock()
        cursor.fetchone.side_effect = [md_row, ad_row]
        cursor.__enter__ = MagicMock(return_value=cursor)
        cursor.__exit__ = MagicMock(return_value=False)
        conn = MagicMock()
        conn.cursor.return_value = cursor
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        return conn

    def setup_method(self):
        # _current_dasha_lords caches by (chart_id, ayanamsha_id, date) — clear
        # between tests so mocks aren't short-circuited by a prior test's cache hit.
        mod = _get_muhurta_module()
        mod._DASHA_LORD_CACHE.clear()

    def test_current_dasha_lords_queries_chart_dashas_live(self):
        """The MD/AD lord is read from chart_dashas via a real SQL query, not hardcoded."""
        mod = _get_muhurta_module()
        md_row = {"lord_graha": "Mercury", "start_date": "2010-08-17", "end_date": "2027-08-17"}
        ad_row = {"lord_graha": "Saturn"}
        conn = self._mock_conn(mod, md_row, ad_row)
        with patch.object(mod, "_get_db_url", return_value="postgresql://fake/test"), \
             patch("psycopg.connect", return_value=conn):
            result = mod._current_dasha_lords(
                NATIVE_CHART_ID, datetime(2026, 7, 16, tzinfo=timezone.utc)
            )
        assert result is not None
        assert result["md_lord"] == "Mercury"
        assert result["md_start"] == "2010-08-17"
        assert result["md_end"] == "2027-08-17"
        assert result["ad_lord"] == "Saturn"
        # SQL actually targets chart_dashas, level_n=1/2 — not a hardcoded value.
        executed_sql = [c.args[0] for c in conn.cursor.return_value.execute.call_args_list]
        assert any("chart_dashas" in sql for sql in executed_sql)
        assert any("level_n = 1" in sql for sql in executed_sql)
        assert any("level_n = 2" in sql for sql in executed_sql)

    def test_current_dasha_lords_honest_none_when_no_row(self):
        """No matching chart_dashas row -> honest None, never a fabricated fallback."""
        mod = _get_muhurta_module()
        conn = self._mock_conn(mod, None, None)
        with patch.object(mod, "_get_db_url", return_value="postgresql://fake/test"), \
             patch("psycopg.connect", return_value=conn):
            result = mod._current_dasha_lords(
                "00000000-0000-0000-0000-000000000000", datetime(2026, 7, 16, tzinfo=timezone.utc)
            )
        assert result is None

    def test_current_dasha_lords_honest_none_on_db_error(self):
        """DB unreachable -> honest None (B.10), not a fabricated Mercury default."""
        mod = _get_muhurta_module()
        with patch.object(mod, "_get_db_url", side_effect=RuntimeError("no DB")):
            result = mod._current_dasha_lords(
                NATIVE_CHART_ID, datetime(2026, 7, 16, tzinfo=timezone.utc)
            )
        assert result is None

    def test_citation_fragment_never_contains_stale_hardcoded_string(self):
        """The exact T-8 regression: no window citation may claim 'Mercury MD (2026-2043)'
        or the stale FORENSIC DSH.V.023 fragment — this must always be LIVE-derived."""
        mod = _get_muhurta_module()
        live = {"md_lord": "Mercury", "md_start": "2010-08-17", "md_end": "2027-08-17", "ad_lord": "Saturn"}
        fragment = mod._dasha_citation_fragment_from(live)
        assert "2026-2043" not in fragment
        assert "DSH.V.023" not in fragment
        assert "Mercury MD" in fragment
        assert "2010-08-17" in fragment and "2027-08-17" in fragment

    def test_citation_fragment_honest_when_no_live_data(self):
        fragment = _get_muhurta_module()._dasha_citation_fragment_from(None)
        assert "unavailable" in fragment
        assert "2026-2043" not in fragment

    def test_generate_muhurta_windows_citation_reflects_live_dasha(self):
        """End-to-end: a window's source_citation and dasha_details come from the
        live-mocked dasha lookup, not the old hardcoded Mercury/2026-2043 string."""
        mod = _get_muhurta_module()
        with patch.object(mod, "_get_db_url", return_value="postgresql://fake/test"), \
             patch.object(mod, "_fetch_panchanga_row", return_value=_fake_panchanga_row()), \
             patch.object(mod, "_panchanga_coverage", return_value=("2026-06-01", "2027-06-01")), \
             patch.object(mod, "_current_dasha_lords", return_value={
                 "md_lord": "Mercury", "md_start": "2010-08-17", "md_end": "2027-08-17",
                 "ad_lord": "Saturn",
             }), \
             patch.object(mod, "_activity_significators_for_action", return_value=None), \
             patch.object(mod, "_fetch_tara_bala_baseline", return_value={}):
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 6, 10, 23, 59, 59, tzinfo=timezone.utc),
                min_score=0.0,
                limit=45,
            )
        assert len(result["windows"]) >= 1
        for w in result["windows"]:
            assert "2026-2043" not in w["source_citation"]
            assert w["factors"]["dasha_details"]["md_lord"] == "Mercury"
            assert w["factors"]["dasha_details"]["ad_lord"] == "Saturn"
            assert "chart_dashas" in w["source_citation"]

    def test_generate_muhurta_windows_resolves_dasha_per_window_across_boundary(self):
        """A later 48-hour window must not reuse the range-start dasha score."""
        mod = _get_muhurta_module()
        seen_dates: list[datetime] = []

        def dasha_quality(_chart_id: str, at: datetime, _action_type: str) -> float:
            seen_dates.append(at)
            return 0.20 if at.date().isoformat() == "2026-06-04" else 0.80

        with patch.object(mod, "_get_db_url", return_value="postgresql://fake/test"), \
             patch.object(mod, "_fetch_panchanga_row", return_value=_fake_panchanga_row()), \
             patch.object(mod, "_panchanga_coverage", return_value=("2026-06-01", "2027-06-01")), \
             patch.object(mod, "_dasha_quality_for_chart", side_effect=dasha_quality), \
             patch.object(mod, "_current_dasha_lords", return_value=None), \
             patch.object(mod, "_fetch_tara_bala_baseline", return_value={}):
            result = mod.generate_muhurta_windows(
                chart_id=NATIVE_CHART_ID,
                action_type="general",
                range_start=datetime(2026, 6, 4, tzinfo=timezone.utc),
                range_end=datetime(2026, 6, 9, tzinfo=timezone.utc),
                min_score=0.0,
                limit=45,
            )

        assert [at.date().isoformat() for at in seen_dates] == ["2026-06-04", "2026-06-06"]
        assert {window["factors"]["dasha_quality"] for window in result["windows"]} == {0.2, 0.8}
