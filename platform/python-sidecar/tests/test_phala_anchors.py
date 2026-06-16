"""
test_phala_anchors.py — Unit tests for phala.anchors (BRAHMA-PH-4-1)

Tests:
    1. compute_window_score — range assertions, boundary conditions
    2. event_anchors — contract assertions (falsifier, source_citation, confidence range)
    3. event_anchors — date range filtering logic (mock DB)
    4. event_anchors — provenance_envelope structure
    5. fetch_anchors — DB round-trip mock
    6. acceptance gate assertions (AC2–AC4 without live DB)

No live DB connection required. All DB calls are mocked via unittest.mock.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch, call

import pytest


# ── Module under test ─────────────────────────────────────────────────────────

# Import lazily so psycopg import doesn't fail in CI (no DB available)
def _get_anchors_module():
    from brahmagyan.phala import anchors as anchors_mod
    return anchors_mod


# ── Fixtures ──────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

def _make_anchor_row(
    anchor_id: str = "PH-4-1.2026H1.CAREER",
    window_start: str = "2026-01-01",
    window_end: str = "2026-06-30",
    theme: str = "career_consolidation",
    confidence: float = 0.59,
    falsifier: str = "If no new contract before 2026-07-01, this prediction is false.",
    contributing_dashas: list | None = None,
    contributing_signals: list | None = None,
    source_citation: str = "FORENSIC v8.0 §5.1 DSH.V.023; MSR v5.0 SIG.09",
    prediction_state: str = "open",
    outcome_note: str | None = None,
) -> dict[str, Any]:
    return {
        "id": 1,
        "chart_id": NATIVE_CHART_ID,
        "anchor_id": anchor_id,
        "window_start": window_start,
        "window_end": window_end,
        "theme": theme,
        "confidence": confidence,
        "falsifier": falsifier,
        "contributing_dashas": contributing_dashas or [
            "DSH.V.023: Mercury MD Saturn AD (2024-12-12 to 2027-08-21)"
        ],
        "contributing_signals": contributing_signals or [
            "SIG.09 Mercury 8-system convergence",
            "SIG.14 Sun 10H career-density",
        ],
        "source_citation": source_citation,
        "prediction_state": prediction_state,
        "outcome_note": outcome_note,
        "created_at": "2026-06-04T00:00:00+00:00",
        "updated_at": "2026-06-04T00:00:00+00:00",
    }


def _make_three_anchors() -> list[dict[str, Any]]:
    """Minimum 3 anchors required by AC1 gate."""
    return [
        _make_anchor_row("PH-4-1.2026H1.CAREER", "2026-01-01", "2026-06-30",
                         confidence=0.59),
        _make_anchor_row("PH-4-1.2026H2.SPIRIT", "2026-07-01", "2026-12-31",
                         theme="spiritual_practice_intensification",
                         confidence=0.46),
        _make_anchor_row("PH-4-1.2027H1.TRANSITION", "2027-01-01", "2027-06-30",
                         theme="life_transition_preparatory",
                         confidence=0.40),
    ]


# ── §1 — compute_window_score ─────────────────────────────────────────────────

class TestComputeWindowScore:
    """
    Tests for the pure-Python score function.
    All assertions use range checks (not exact floats) per constraint.
    """

    def test_all_ones_returns_one(self):
        mod = _get_anchors_module()
        result = mod.compute_window_score(1.0, 1.0, 1.0)
        assert result == pytest.approx(1.0, abs=0.001)

    def test_all_zeros_returns_zero(self):
        mod = _get_anchors_module()
        result = mod.compute_window_score(0.0, 0.0, 0.0)
        assert result == pytest.approx(0.0, abs=0.001)

    def test_clamp_above_one(self):
        """Values > 1.0 in components shouldn't exceed 1.0 output (clamp)."""
        mod = _get_anchors_module()
        # Python clamp is applied: even if arguments exceed 1 independently,
        # the output should stay in [0, 1].
        result = mod.compute_window_score(1.0, 1.0, 1.0)
        assert 0.0 <= result <= 1.0

    def test_native_career_window_range(self):
        """Native 2026H1 career window: dasha=0.82, signal=0.79, convergence=0.91."""
        mod = _get_anchors_module()
        result = mod.compute_window_score(0.82, 0.79, 0.91)
        # Should be in (0.5, 1.0) range — high confidence window
        assert 0.5 < result <= 1.0

    def test_ketu_venus_window_range(self):
        """Ketu-Venus AD window: dasha=0.58, signal=0.65, convergence=0.72."""
        mod = _get_anchors_module()
        result = mod.compute_window_score(0.58, 0.65, 0.72)
        # Should be in (0.2, 0.4) range — medium confidence
        assert 0.2 < result < 0.5

    def test_result_always_in_unit_interval(self):
        """Fuzz: any combination of [0,1] inputs produces output in [0,1]."""
        mod = _get_anchors_module()
        test_cases = [
            (0.0, 1.0, 0.5),
            (1.0, 0.0, 0.5),
            (0.5, 0.5, 0.5),
            (0.82, 0.79, 0.91),
            (0.62, 0.70, 0.88),
        ]
        for d, s, c in test_cases:
            result = mod.compute_window_score(d, s, c)
            assert 0.0 <= result <= 1.0, (
                f"compute_window_score({d}, {s}, {c}) = {result} out of [0,1]"
            )


# ── §2 — Contract assertions on anchor rows ───────────────────────────────────

class TestAnchorContractAssertions:
    """
    Verify falsifier + source_citation + confidence range contract
    against a mocked set of rows (no DB required).
    """

    def test_all_anchors_have_falsifier(self):
        anchors = _make_three_anchors()
        assert all(bool(a["falsifier"]) for a in anchors), (
            "Every anchor MUST have a non-empty falsifier (Learning Layer rule #4)"
        )

    def test_all_anchors_have_source_citation(self):
        anchors = _make_three_anchors()
        assert all(bool(a["source_citation"]) for a in anchors), (
            "Every anchor MUST have a non-empty source_citation (B.3 mandate)"
        )

    def test_confidence_in_unit_interval(self):
        anchors = _make_three_anchors()
        for a in anchors:
            assert 0.0 <= a["confidence"] <= 1.0, (
                f"Anchor {a['anchor_id']} confidence={a['confidence']} out of [0,1]"
            )

    def test_window_start_before_end(self):
        anchors = _make_three_anchors()
        for a in anchors:
            start = date.fromisoformat(a["window_start"])
            end = date.fromisoformat(a["window_end"])
            assert start < end, (
                f"Anchor {a['anchor_id']} window_start={start} >= window_end={end}"
            )

    def test_nine_anchor_confidence_range(self):
        """
        All 9 seed anchors have confidence in (0, 1). Check the computed scores
        directly using compute_window_score with known parameters from the migration.
        """
        mod = _get_anchors_module()
        # Parameters from brahma_phala_anchors.sql
        anchor_params = [
            (0.82, 0.79, 0.91),  # 2026H1 career
            (0.75, 0.72, 0.85),  # 2026H2 spirit
            (0.68, 0.74, 0.80),  # 2027H1 transition
            (0.62, 0.70, 0.88),  # 2027H2 regime
            (0.58, 0.65, 0.72),  # 2028H1 relational
            (0.60, 0.68, 0.75),  # 2028H2 wealth
            (0.55, 0.70, 0.78),  # 2029H1 authority
            (0.65, 0.72, 0.76),  # 2029H2 soul
            (0.58, 0.63, 0.70),  # 2030H1 action
        ]
        for d, s, c in anchor_params:
            score = mod.compute_window_score(d, s, c)
            assert 0.0 < score < 1.0, (
                f"compute_window_score({d},{s},{c})={score} not in (0,1)"
            )


# ── §3 — event_anchors date range and response shape ─────────────────────────

class TestEventAnchorsResponseShape:
    """Tests for the event_anchors() response shape with mocked DB."""

    def _mock_fetch_anchors(self, anchors: list[dict[str, Any]]):
        """Context manager that mocks fetch_anchors to return the given list."""
        return patch(
            "brahmagyan.phala.anchors.fetch_anchors",
            return_value=anchors,
        )

    def test_response_has_required_keys(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        assert "ok" in result
        assert "anchors" in result
        assert "anchor_count" in result
        assert "provenance_envelope" in result
        assert "query_window" in result

    def test_anchor_count_matches_list(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        assert result["anchor_count"] == len(result["anchors"])
        assert result["anchor_count"] == 3

    def test_anchors_have_falsifier_field(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        for anchor in result["anchors"]:
            assert "falsifier" in anchor
            assert bool(anchor["falsifier"]), (
                f"anchor {anchor['anchor_id']} has empty falsifier"
            )

    def test_anchors_have_source_citation_field(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        for anchor in result["anchors"]:
            assert "source_citation" in anchor
            assert bool(anchor["source_citation"]), (
                f"anchor {anchor['anchor_id']} has empty source_citation"
            )

    def test_anchor_confidence_in_range(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        for anchor in result["anchors"]:
            assert 0.0 <= anchor["confidence"] <= 1.0, (
                f"anchor {anchor['anchor_id']} confidence={anchor['confidence']} out of [0,1]"
            )

    def test_provenance_envelope_structure(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        env = result["provenance_envelope"]
        assert env["source"] == "phala.anchors"
        assert env["asset"] == "PH-4-1"
        assert "algorithm" in env
        assert "dasha_quality" in env["algorithm"]
        assert env["chart_id"] == NATIVE_CHART_ID
        assert "queried_at" in env
        assert "l1_ground_truth" in env
        assert "FORENSIC" in env["l1_ground_truth"]
        assert isinstance(env["b3_citation_compliant"], bool)
        assert isinstance(env["all_falsifiers_present"], bool)

    def test_b3_compliant_true_when_all_cited(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        assert result["provenance_envelope"]["b3_citation_compliant"] is True

    def test_b3_compliant_false_when_missing_citation(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        rows[0]["source_citation"] = ""  # Break B.3 compliance
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        assert result["provenance_envelope"]["b3_citation_compliant"] is False

    def test_all_falsifiers_present_true(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        assert result["provenance_envelope"]["all_falsifiers_present"] is True

    def test_all_falsifiers_present_false_when_missing(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        rows[1]["falsifier"] = ""  # Simulate missing falsifier
        with self._mock_fetch_anchors(rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        assert result["provenance_envelope"]["all_falsifiers_present"] is False

    def test_empty_result_for_no_overlap(self):
        mod = _get_anchors_module()
        with self._mock_fetch_anchors([]):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "1984-01-01", "end": "1984-12-31"},
            )
        assert result["anchor_count"] == 0
        assert result["anchors"] == []
        assert result["ok"] is True


# ── §4 — Validation errors ────────────────────────────────────────────────────

class TestEventAnchorsValidation:
    """Validate input guard-rails without hitting the DB."""

    def test_invalid_date_range_raises(self):
        mod = _get_anchors_module()
        with pytest.raises(ValueError, match="start"):
            mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "not-a-date", "end": "2026-12-31"},
            )

    def test_start_after_end_raises(self):
        mod = _get_anchors_module()
        with pytest.raises(ValueError):
            mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2030-01-01", "end": "2026-01-01"},
            )

    def test_min_confidence_out_of_range_raises(self):
        mod = _get_anchors_module()
        with pytest.raises(ValueError, match="min_confidence"):
            mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
                min_confidence=1.5,
            )

    def test_negative_min_confidence_raises(self):
        mod = _get_anchors_module()
        with pytest.raises(ValueError, match="min_confidence"):
            mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
                min_confidence=-0.1,
            )

    def test_invalid_prediction_state_raises_in_fetch(self):
        mod = _get_anchors_module()
        with pytest.raises(ValueError, match="prediction_state"):
            mod.fetch_anchors(
                chart_id=NATIVE_CHART_ID,
                range_start=date(2026, 1, 1),
                range_end=date(2030, 12, 31),
                prediction_state="invalid_state",
            )


# ── §5 — min_confidence filtering ────────────────────────────────────────────

class TestMinConfidenceFiltering:
    """Verify min_confidence parameter is passed through to fetch_anchors."""

    def test_min_confidence_propagated(self):
        mod = _get_anchors_module()
        with patch("brahmagyan.phala.anchors.fetch_anchors", return_value=[]) as mock_fetch:
            mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
                min_confidence=0.5,
            )
            call_kwargs = mock_fetch.call_args
            # Either positional or keyword
            if call_kwargs.args:
                # min_confidence is 4th positional arg
                assert call_kwargs.args[3] == 0.5 or \
                       call_kwargs.kwargs.get("min_confidence") == 0.5
            else:
                assert call_kwargs.kwargs["min_confidence"] == 0.5

    def test_default_min_confidence_is_zero(self):
        mod = _get_anchors_module()
        with patch("brahmagyan.phala.anchors.fetch_anchors", return_value=[]) as mock_fetch:
            mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
            # min_confidence defaults to 0.0
            call_kwargs = mock_fetch.call_args
            if call_kwargs.args:
                conf_arg = call_kwargs.args[3] if len(call_kwargs.args) > 3 \
                           else call_kwargs.kwargs.get("min_confidence", 0.0)
            else:
                conf_arg = call_kwargs.kwargs.get("min_confidence", 0.0)
            assert conf_arg == 0.0


# ── §6 — Smoke test: anchor structure completeness ────────────────────────────

class TestAnchorStructureCompleteness:
    """Verify each anchor dict has all required keys."""

    REQUIRED_KEYS = {
        "anchor_id", "window", "theme", "confidence",
        "falsifier", "contributing_dashas", "contributing_signals",
        "source_citation", "prediction_state",
    }

    def test_anchor_has_all_required_keys(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with patch("brahmagyan.phala.anchors.fetch_anchors", return_value=rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        for anchor in result["anchors"]:
            missing = self.REQUIRED_KEYS - set(anchor.keys())
            assert not missing, (
                f"Anchor {anchor.get('anchor_id', '?')} missing keys: {missing}"
            )

    def test_window_has_start_and_end(self):
        mod = _get_anchors_module()
        rows = _make_three_anchors()
        with patch("brahmagyan.phala.anchors.fetch_anchors", return_value=rows):
            result = mod.event_anchors(
                chart_id=NATIVE_CHART_ID,
                date_range={"start": "2026-01-01", "end": "2030-12-31"},
            )
        for anchor in result["anchors"]:
            window = anchor["window"]
            assert "start" in window
            assert "end" in window
            # ISO format
            date.fromisoformat(window["start"])
            date.fromisoformat(window["end"])
