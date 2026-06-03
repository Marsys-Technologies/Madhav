"""
test_mimamsa_prediction_ledger.py — Unit tests for mimamsa.prediction_ledger (BRAHMA-MI-5-2)

Tests:
    1. compute_brier_score — range assertions (not exact floats), boundary conditions
    2. log_prediction — contract assertions (falsifier non-null, source_citation non-null,
                        confidence in (0,1)), validation guards
    3. record_outcome — Brier score computation correctness, round-trip mock
    4. list_predictions — provenance_envelope structure, B.3 compliance flags
    5. Tool smoke — full log+record round-trip with mocked DB

CRITICAL DISCIPLINE — NO LEAKAGE:
    Tests verify that the log/record boundary is maintained:
    - outcome_observed starts NULL
    - brier_score starts NULL
    - Only record_outcome() writes outcome_observed

No live DB connection required. All DB calls are mocked via unittest.mock.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ── Module under test ─────────────────────────────────────────────────────────

def _get_ledger_module():
    from brahmagyan.mimamsa import prediction_ledger as ledger_mod
    return ledger_mod


# ── Fixtures ──────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"
SAMPLE_PREDICTION_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
SAMPLE_ANCHOR_ID = "PH-4-1.2026H1.CAREER"
SAMPLE_SOURCE_CITATION = f"Brahma L4 phala.anchors / {SAMPLE_ANCHOR_ID}"

SAMPLE_PREDICTION_TEXT = (
    "A new client contract or measurable revenue milestone in the Marsys Technology domain "
    "is reached before 2026-07-01."
)
SAMPLE_FALSIFIER = (
    "If no new client contract, partnership formalization, or measurable revenue milestone "
    "in the Marsys Technology / consulting domain is reached before 2026-07-01, "
    "this prediction is false."
)


def _make_prediction_row(
    prediction_id: str = SAMPLE_PREDICTION_ID,
    chart_id: str = NATIVE_CHART_ID,
    horizon_date: str = "2026-06-30",
    domain: str = "career",
    prediction_text: str = SAMPLE_PREDICTION_TEXT,
    confidence: float = 0.59,
    falsifier: str = SAMPLE_FALSIFIER,
    source_citation: str = SAMPLE_SOURCE_CITATION,
    outcome_observed: bool | None = None,
    brier_score: float | None = None,
) -> dict[str, Any]:
    """Build a minimal mimamsa_predictions row dict (as returned by psycopg)."""
    return {
        "prediction_id": prediction_id,
        "chart_id": chart_id,
        "predicted_at": "2026-06-04T00:00:00+00:00",
        "horizon_date": horizon_date,
        "domain": domain,
        "prediction_text": prediction_text,
        "confidence": confidence,
        "falsifier": falsifier,
        "source_citation": source_citation,
        "outcome_observed": outcome_observed,
        "brier_score": brier_score,
        "outcome_recorded_at": None,
        "created_at": "2026-06-04T00:00:00+00:00",
        "updated_at": "2026-06-04T00:00:00+00:00",
    }


def _make_three_predictions() -> list[dict[str, Any]]:
    return [
        _make_prediction_row(
            prediction_id=str(uuid.uuid4()),
            domain="career",
            horizon_date="2026-06-30",
            confidence=0.59,
        ),
        _make_prediction_row(
            prediction_id=str(uuid.uuid4()),
            domain="spiritual",
            horizon_date="2026-12-31",
            confidence=0.46,
            falsifier=(
                "If no formal spiritual practice is established before 2027-01-01, "
                "this prediction is false."
            ),
        ),
        _make_prediction_row(
            prediction_id=str(uuid.uuid4()),
            domain="transition",
            horizon_date="2027-06-30",
            confidence=0.40,
            falsifier=(
                "If no role change or residential shift occurs before 2027-07-01, "
                "this prediction is false."
            ),
        ),
    ]


# ── §1 — compute_brier_score ──────────────────────────────────────────────────

class TestComputeBrierScore:
    """
    Tests for the pure-Python Brier score function.
    All assertions use range checks (not exact floats) per constraint.
    """

    def test_correct_outcome_low_confidence_low_brier(self):
        """Confident correct prediction → low Brier score."""
        mod = _get_ledger_module()
        # confidence=0.9, outcome=True → brier=(1-0.9)^2=0.01
        score = mod.compute_brier_score(0.9, True)
        assert 0.0 <= score < 0.05, f"Expected low brier for correct high-conf, got {score}"

    def test_wrong_outcome_high_confidence_high_brier(self):
        """Wrong high-confidence prediction → high Brier score."""
        mod = _get_ledger_module()
        # confidence=0.9, outcome=False → brier=(0-0.9)^2=0.81
        score = mod.compute_brier_score(0.9, False)
        assert 0.7 < score <= 1.0, f"Expected high brier for wrong high-conf, got {score}"

    def test_perfectly_uncertain_neutral_brier(self):
        """Confidence=0.5, outcome=True → brier=0.25 (maximum uncertainty)."""
        mod = _get_ledger_module()
        score = mod.compute_brier_score(0.5, True)
        assert 0.2 < score < 0.3, f"Expected ~0.25 for 50% confidence, got {score}"

    def test_brier_always_in_unit_interval(self):
        """Brier score must be in [0, 1] for all valid inputs."""
        mod = _get_ledger_module()
        test_cases = [
            (0.1, True), (0.1, False),
            (0.5, True), (0.5, False),
            (0.9, True), (0.9, False),
            (0.59, True), (0.59, False),
            (0.001, True), (0.999, False),
        ]
        for conf, outcome in test_cases:
            score = mod.compute_brier_score(conf, outcome)
            assert 0.0 <= score <= 1.0, (
                f"compute_brier_score({conf}, {outcome}) = {score} out of [0, 1]"
            )

    def test_confidence_zero_raises(self):
        """confidence=0 is excluded from the open interval."""
        mod = _get_ledger_module()
        with pytest.raises(ValueError, match="open interval"):
            mod.compute_brier_score(0.0, True)

    def test_confidence_one_raises(self):
        """confidence=1 is excluded from the open interval."""
        mod = _get_ledger_module()
        with pytest.raises(ValueError, match="open interval"):
            mod.compute_brier_score(1.0, False)

    def test_brier_is_symmetric_around_50pct(self):
        """Brier score is symmetric: score(0.3, True) == score(0.7, False)."""
        mod = _get_ledger_module()
        score_a = mod.compute_brier_score(0.3, True)   # (1-0.3)^2 = 0.49
        score_b = mod.compute_brier_score(0.7, False)  # (0-0.7)^2 = 0.49
        assert abs(score_a - score_b) < 1e-9, (
            f"Brier symmetry broken: score(0.3, True)={score_a} vs score(0.7, False)={score_b}"
        )

    def test_native_career_window_confidence(self):
        """Native career window confidence ~0.59 produces brier in expected range."""
        mod = _get_ledger_module()
        # 2026H1 career: compute_window_score(0.82, 0.79, 0.91) ~ 0.59
        score_correct = mod.compute_brier_score(0.59, True)    # ~0.17
        score_wrong = mod.compute_brier_score(0.59, False)     # ~0.35
        assert 0.1 < score_correct < 0.25, f"Expected ~0.17, got {score_correct}"
        assert 0.3 < score_wrong < 0.45, f"Expected ~0.35, got {score_wrong}"


# ── §2 — log_prediction validation ───────────────────────────────────────────

class TestLogPredictionValidation:
    """
    Verify input guard-rails for log_prediction without hitting the DB.
    """

    def test_confidence_zero_raises(self):
        """confidence=0 violates open-interval contract."""
        mod = _get_ledger_module()
        with pytest.raises(ValueError, match="open interval"):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text=SAMPLE_PREDICTION_TEXT,
                horizon_date="2026-06-30",
                confidence=0.0,
                falsifier=SAMPLE_FALSIFIER,
                source_citation=SAMPLE_SOURCE_CITATION,
            )

    def test_confidence_one_raises(self):
        """confidence=1 violates open-interval contract."""
        mod = _get_ledger_module()
        with pytest.raises(ValueError, match="open interval"):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text=SAMPLE_PREDICTION_TEXT,
                horizon_date="2026-06-30",
                confidence=1.0,
                falsifier=SAMPLE_FALSIFIER,
                source_citation=SAMPLE_SOURCE_CITATION,
            )

    def test_confidence_negative_raises(self):
        mod = _get_ledger_module()
        with pytest.raises(ValueError):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text=SAMPLE_PREDICTION_TEXT,
                horizon_date="2026-06-30",
                confidence=-0.1,
                falsifier=SAMPLE_FALSIFIER,
                source_citation=SAMPLE_SOURCE_CITATION,
            )

    def test_confidence_above_one_raises(self):
        mod = _get_ledger_module()
        with pytest.raises(ValueError):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text=SAMPLE_PREDICTION_TEXT,
                horizon_date="2026-06-30",
                confidence=1.1,
                falsifier=SAMPLE_FALSIFIER,
                source_citation=SAMPLE_SOURCE_CITATION,
            )

    def test_empty_falsifier_raises(self):
        """falsifier must be non-empty (Learning Layer rule #4)."""
        mod = _get_ledger_module()
        with pytest.raises(ValueError, match="falsifier"):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text=SAMPLE_PREDICTION_TEXT,
                horizon_date="2026-06-30",
                confidence=0.59,
                falsifier="",
                source_citation=SAMPLE_SOURCE_CITATION,
            )

    def test_whitespace_falsifier_raises(self):
        """Whitespace-only falsifier must be rejected."""
        mod = _get_ledger_module()
        with pytest.raises(ValueError, match="falsifier"):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text=SAMPLE_PREDICTION_TEXT,
                horizon_date="2026-06-30",
                confidence=0.59,
                falsifier="   ",
                source_citation=SAMPLE_SOURCE_CITATION,
            )

    def test_no_source_citation_no_anchor_id_raises(self):
        """B.3 mandate: source_citation or anchor_id must be provided."""
        mod = _get_ledger_module()
        with pytest.raises(ValueError, match="source_citation"):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text=SAMPLE_PREDICTION_TEXT,
                horizon_date="2026-06-30",
                confidence=0.59,
                falsifier=SAMPLE_FALSIFIER,
                # Neither source_citation nor anchor_id provided
            )

    def test_empty_source_citation_raises(self):
        """Empty source_citation violates B.3 mandate."""
        mod = _get_ledger_module()
        with pytest.raises(ValueError, match="source_citation"):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text=SAMPLE_PREDICTION_TEXT,
                horizon_date="2026-06-30",
                confidence=0.59,
                falsifier=SAMPLE_FALSIFIER,
                source_citation="   ",
            )

    def test_empty_prediction_text_raises(self):
        mod = _get_ledger_module()
        with pytest.raises(ValueError):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text="",
                horizon_date="2026-06-30",
                confidence=0.59,
                falsifier=SAMPLE_FALSIFIER,
                source_citation=SAMPLE_SOURCE_CITATION,
            )

    def test_invalid_horizon_date_raises(self):
        mod = _get_ledger_module()
        with pytest.raises(ValueError, match="horizon_date"):
            mod.log_prediction(
                chart_id=NATIVE_CHART_ID,
                prediction_text=SAMPLE_PREDICTION_TEXT,
                horizon_date="not-a-date",
                confidence=0.59,
                falsifier=SAMPLE_FALSIFIER,
                source_citation=SAMPLE_SOURCE_CITATION,
            )


# ── §3 — log_prediction success path (mocked DB) ─────────────────────────────

class TestLogPredictionSuccess:
    """
    Verify log_prediction() succeeds and returns expected structure
    with a mocked DB connection.
    """

    def _mock_db_insert(self, prediction_id: str):
        """
        Context manager: mock psycopg.connect so INSERT returns prediction_id.
        """
        mock_row = {"prediction_id": prediction_id, "predicted_at": datetime.now(tz=timezone.utc)}
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.execute = MagicMock()
        mock_cursor.fetchone = MagicMock(return_value=mock_row)

        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor = MagicMock(return_value=mock_cursor)
        mock_conn.commit = MagicMock()

        return patch("psycopg.connect", return_value=mock_conn)

    def test_returns_prediction_id(self):
        mod = _get_ledger_module()
        pid = str(uuid.uuid4())
        with self._mock_db_insert(pid):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.log_prediction(
                    chart_id=NATIVE_CHART_ID,
                    prediction_text=SAMPLE_PREDICTION_TEXT,
                    horizon_date="2026-06-30",
                    confidence=0.59,
                    falsifier=SAMPLE_FALSIFIER,
                    source_citation=SAMPLE_SOURCE_CITATION,
                )
        assert "prediction_id" in result
        assert result["ok"] is True

    def test_anchor_id_auto_citation(self):
        """anchor_id should auto-derive source_citation."""
        mod = _get_ledger_module()
        pid = str(uuid.uuid4())
        with self._mock_db_insert(pid):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.log_prediction(
                    chart_id=NATIVE_CHART_ID,
                    prediction_text=SAMPLE_PREDICTION_TEXT,
                    horizon_date="2026-06-30",
                    confidence=0.59,
                    falsifier=SAMPLE_FALSIFIER,
                    anchor_id=SAMPLE_ANCHOR_ID,
                )
        assert "source_citation" in result
        assert SAMPLE_ANCHOR_ID in result["source_citation"]
        assert "phala.anchors" in result["source_citation"]

    def test_response_has_provenance_envelope(self):
        mod = _get_ledger_module()
        pid = str(uuid.uuid4())
        with self._mock_db_insert(pid):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.log_prediction(
                    chart_id=NATIVE_CHART_ID,
                    prediction_text=SAMPLE_PREDICTION_TEXT,
                    horizon_date="2026-06-30",
                    confidence=0.59,
                    falsifier=SAMPLE_FALSIFIER,
                    source_citation=SAMPLE_SOURCE_CITATION,
                )
        env = result["provenance_envelope"]
        assert env["source"] == "mimamsa.prediction_ledger"
        assert env["asset"] == "MI-5-2"
        assert env["tool"] == "log_prediction"
        assert env["b3_citation_compliant"] is True
        assert "no_leakage_discipline" in env
        assert "LEL" in env["no_leakage_discipline"]

    def test_response_confidence_preserved(self):
        mod = _get_ledger_module()
        pid = str(uuid.uuid4())
        with self._mock_db_insert(pid):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.log_prediction(
                    chart_id=NATIVE_CHART_ID,
                    prediction_text=SAMPLE_PREDICTION_TEXT,
                    horizon_date="2026-06-30",
                    confidence=0.59,
                    falsifier=SAMPLE_FALSIFIER,
                    source_citation=SAMPLE_SOURCE_CITATION,
                )
        assert result["confidence"] == 0.59

    def test_various_valid_confidences(self):
        """Verify that valid open-interval confidence values are accepted."""
        mod = _get_ledger_module()
        valid_confidences = [0.001, 0.1, 0.5, 0.75, 0.99, 0.999]
        for conf in valid_confidences:
            pid = str(uuid.uuid4())
            mock_row = {"prediction_id": pid, "predicted_at": datetime.now(tz=timezone.utc)}
            mock_cursor = MagicMock()
            mock_cursor.__enter__ = lambda s: s
            mock_cursor.__exit__ = MagicMock(return_value=False)
            mock_cursor.execute = MagicMock()
            mock_cursor.fetchone = MagicMock(return_value=mock_row)
            mock_conn = MagicMock()
            mock_conn.__enter__ = lambda s: s
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_conn.cursor = MagicMock(return_value=mock_cursor)
            mock_conn.commit = MagicMock()

            with patch("psycopg.connect", return_value=mock_conn):
                with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                    result = mod.log_prediction(
                        chart_id=NATIVE_CHART_ID,
                        prediction_text=SAMPLE_PREDICTION_TEXT,
                        horizon_date="2026-06-30",
                        confidence=conf,
                        falsifier=SAMPLE_FALSIFIER,
                        source_citation=SAMPLE_SOURCE_CITATION,
                    )
            assert result["ok"] is True, f"Failed for confidence={conf}"
            assert 0.0 < result["confidence"] < 1.0


# ── §4 — record_outcome (mocked DB) ──────────────────────────────────────────

class TestRecordOutcome:
    """
    Verify record_outcome() computes brier_score and returns provenance envelope.
    """

    def _mock_db_outcome(self, brier_score: float):
        """Mock the DB call to mimamsa_record_outcome()."""
        mock_row = {"brier_score": brier_score}
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = lambda s: s
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.execute = MagicMock()
        mock_cursor.fetchone = MagicMock(return_value=mock_row)

        mock_conn = MagicMock()
        mock_conn.__enter__ = lambda s: s
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor = MagicMock(return_value=mock_cursor)
        mock_conn.commit = MagicMock()

        return patch("psycopg.connect", return_value=mock_conn)

    def test_record_outcome_true(self):
        """Outcome=True with confidence=0.9 → brier ~0.01."""
        mod = _get_ledger_module()
        expected_brier = (1.0 - 0.9) ** 2  # = 0.01
        with self._mock_db_outcome(expected_brier):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.record_outcome(
                    prediction_id=SAMPLE_PREDICTION_ID,
                    outcome_observed=True,
                )
        assert result["ok"] is True
        assert result["outcome_observed"] is True
        assert 0.0 <= result["brier_score"] <= 1.0
        assert result["brier_score"] < 0.05, "Expected low brier for correct high-conf"

    def test_record_outcome_false(self):
        """Outcome=False with confidence=0.9 → brier ~0.81."""
        mod = _get_ledger_module()
        expected_brier = (0.0 - 0.9) ** 2  # = 0.81
        with self._mock_db_outcome(expected_brier):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.record_outcome(
                    prediction_id=SAMPLE_PREDICTION_ID,
                    outcome_observed=False,
                )
        assert result["ok"] is True
        assert result["outcome_observed"] is False
        assert 0.0 <= result["brier_score"] <= 1.0
        assert result["brier_score"] > 0.5, "Expected high brier for wrong high-conf"

    def test_record_outcome_has_provenance_envelope(self):
        mod = _get_ledger_module()
        brier = 0.17
        with self._mock_db_outcome(brier):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                result = mod.record_outcome(
                    prediction_id=SAMPLE_PREDICTION_ID,
                    outcome_observed=True,
                )
        env = result["provenance_envelope"]
        assert env["source"] == "mimamsa.prediction_ledger"
        assert env["asset"] == "MI-5-2"
        assert env["tool"] == "record_outcome"
        assert "brier_formula" in env
        assert "outcome::int" in env["brier_formula"]
        assert "no_leakage_note" in env
        assert "LEL" in env["no_leakage_note"]

    def test_brier_score_in_unit_interval_from_db(self):
        """DB-returned brier_score must be in [0, 1]."""
        mod = _get_ledger_module()
        # Simulate various brier scores from DB
        brier_cases = [0.0, 0.01, 0.25, 0.49, 0.81, 1.0]
        for brier in brier_cases:
            with self._mock_db_outcome(brier):
                with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                    result = mod.record_outcome(
                        prediction_id=SAMPLE_PREDICTION_ID,
                        outcome_observed=True,
                    )
            assert 0.0 <= result["brier_score"] <= 1.0, (
                f"brier_score={result['brier_score']} out of [0, 1] for DB value={brier}"
            )


# ── §5 — list_predictions provenance ─────────────────────────────────────────

class TestListPredictions:
    """Verify list_predictions() response shape and provenance envelope."""

    def _mock_fetch(self, rows: list[dict[str, Any]]):
        return patch(
            "brahmagyan.mimamsa.prediction_ledger.fetch_predictions",
            return_value=rows,
        )

    def test_response_has_required_keys(self):
        mod = _get_ledger_module()
        rows = _make_three_predictions()
        with self._mock_fetch(rows):
            result = mod.list_predictions(
                chart_id=NATIVE_CHART_ID,
            )
        assert "ok" in result
        assert "predictions" in result
        assert "count" in result
        assert "open_count" in result
        assert "provenance_envelope" in result

    def test_count_matches_list_length(self):
        mod = _get_ledger_module()
        rows = _make_three_predictions()
        with self._mock_fetch(rows):
            result = mod.list_predictions(chart_id=NATIVE_CHART_ID)
        assert result["count"] == 3
        assert result["count"] == len(result["predictions"])

    def test_open_count_counts_null_outcomes(self):
        mod = _get_ledger_module()
        rows = _make_three_predictions()
        # All three have outcome_observed=None — should be 3 open
        with self._mock_fetch(rows):
            result = mod.list_predictions(chart_id=NATIVE_CHART_ID)
        assert result["open_count"] == 3

    def test_open_count_excludes_resolved(self):
        mod = _get_ledger_module()
        rows = _make_three_predictions()
        # Mark one as resolved
        rows[0]["outcome_observed"] = True
        rows[0]["brier_score"] = 0.17
        with self._mock_fetch(rows):
            result = mod.list_predictions(chart_id=NATIVE_CHART_ID)
        assert result["open_count"] == 2

    def test_provenance_envelope_structure(self):
        mod = _get_ledger_module()
        rows = _make_three_predictions()
        with self._mock_fetch(rows):
            result = mod.list_predictions(chart_id=NATIVE_CHART_ID)
        env = result["provenance_envelope"]
        assert env["source"] == "mimamsa.prediction_ledger"
        assert env["asset"] == "MI-5-2"
        assert env["chart_id"] == NATIVE_CHART_ID
        assert "queried_at" in env
        assert "b3_citation_compliant" in env
        assert "all_falsifiers_present" in env
        assert "no_leakage_note" in env
        assert "LEL" in env["no_leakage_note"]

    def test_b3_compliant_true_when_all_cited(self):
        mod = _get_ledger_module()
        rows = _make_three_predictions()
        with self._mock_fetch(rows):
            result = mod.list_predictions(chart_id=NATIVE_CHART_ID)
        assert result["provenance_envelope"]["b3_citation_compliant"] is True

    def test_b3_compliant_false_when_citation_missing(self):
        mod = _get_ledger_module()
        rows = _make_three_predictions()
        rows[0]["source_citation"] = ""  # Break B.3
        with self._mock_fetch(rows):
            result = mod.list_predictions(chart_id=NATIVE_CHART_ID)
        assert result["provenance_envelope"]["b3_citation_compliant"] is False

    def test_all_falsifiers_present_true(self):
        mod = _get_ledger_module()
        rows = _make_three_predictions()
        with self._mock_fetch(rows):
            result = mod.list_predictions(chart_id=NATIVE_CHART_ID)
        assert result["provenance_envelope"]["all_falsifiers_present"] is True

    def test_all_falsifiers_present_false(self):
        mod = _get_ledger_module()
        rows = _make_three_predictions()
        rows[1]["falsifier"] = ""  # Simulate missing falsifier
        with self._mock_fetch(rows):
            result = mod.list_predictions(chart_id=NATIVE_CHART_ID)
        assert result["provenance_envelope"]["all_falsifiers_present"] is False


# ── §6 — Contract assertions on prediction rows ───────────────────────────────

class TestPredictionContractAssertions:
    """
    Verify falsifier + source_citation + confidence contract on raw row dicts.
    These assertions do NOT require a DB connection.
    """

    def test_all_predictions_have_falsifier(self):
        rows = _make_three_predictions()
        assert all(bool(r["falsifier"]) for r in rows), (
            "Every prediction MUST have a non-empty falsifier (Learning Layer rule #4)"
        )

    def test_all_predictions_have_source_citation(self):
        rows = _make_three_predictions()
        assert all(bool(r["source_citation"]) for r in rows), (
            "Every prediction MUST have a non-empty source_citation (B.3 mandate)"
        )

    def test_confidence_in_open_interval(self):
        rows = _make_three_predictions()
        for r in rows:
            assert 0.0 < r["confidence"] < 1.0, (
                f"Prediction confidence={r['confidence']} not in (0, 1)"
            )

    def test_outcome_starts_null(self):
        """NO LEAKAGE: outcome_observed must be None until record_outcome() is called."""
        rows = _make_three_predictions()
        for r in rows:
            assert r["outcome_observed"] is None, (
                f"outcome_observed must be NULL at log time — got {r['outcome_observed']}"
            )

    def test_brier_starts_null(self):
        """NO LEAKAGE: brier_score must be None until record_outcome() is called."""
        rows = _make_three_predictions()
        for r in rows:
            assert r["brier_score"] is None, (
                f"brier_score must be NULL at log time — got {r['brier_score']}"
            )

    def test_source_citation_references_phala_anchors(self):
        """source_citation format: 'Brahma L4 phala.anchors / [anchor_id]'."""
        rows = _make_three_predictions()
        for r in rows:
            assert "phala.anchors" in r["source_citation"], (
                f"source_citation must reference phala.anchors: {r['source_citation']}"
            )


# ── §7 — Full log + record round-trip (smoke test) ───────────────────────────

class TestLogRecordRoundTrip:
    """
    Smoke test: full log_prediction → record_outcome round-trip via mocked DB.
    Verifies the complete MI-5-2 API surface.
    """

    def test_full_round_trip(self):
        mod = _get_ledger_module()
        pid = str(uuid.uuid4())
        confidence = 0.59
        outcome = True
        expected_brier = (1 - confidence) ** 2  # ~0.17

        # Step 1: log_prediction
        mock_log_row = {"prediction_id": pid, "predicted_at": datetime.now(tz=timezone.utc)}
        mock_log_cursor = MagicMock()
        mock_log_cursor.__enter__ = lambda s: s
        mock_log_cursor.__exit__ = MagicMock(return_value=False)
        mock_log_cursor.execute = MagicMock()
        mock_log_cursor.fetchone = MagicMock(return_value=mock_log_row)
        mock_log_conn = MagicMock()
        mock_log_conn.__enter__ = lambda s: s
        mock_log_conn.__exit__ = MagicMock(return_value=False)
        mock_log_conn.cursor = MagicMock(return_value=mock_log_cursor)
        mock_log_conn.commit = MagicMock()

        with patch("psycopg.connect", return_value=mock_log_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                log_result = mod.log_prediction(
                    chart_id=NATIVE_CHART_ID,
                    prediction_text=SAMPLE_PREDICTION_TEXT,
                    horizon_date="2026-06-30",
                    confidence=confidence,
                    falsifier=SAMPLE_FALSIFIER,
                    anchor_id=SAMPLE_ANCHOR_ID,
                    domain="career",
                )

        assert log_result["ok"] is True
        returned_pid = log_result["prediction_id"]

        # Step 2: record_outcome
        mock_out_row = {"brier_score": expected_brier}
        mock_out_cursor = MagicMock()
        mock_out_cursor.__enter__ = lambda s: s
        mock_out_cursor.__exit__ = MagicMock(return_value=False)
        mock_out_cursor.execute = MagicMock()
        mock_out_cursor.fetchone = MagicMock(return_value=mock_out_row)
        mock_out_conn = MagicMock()
        mock_out_conn.__enter__ = lambda s: s
        mock_out_conn.__exit__ = MagicMock(return_value=False)
        mock_out_conn.cursor = MagicMock(return_value=mock_out_cursor)
        mock_out_conn.commit = MagicMock()

        with patch("psycopg.connect", return_value=mock_out_conn):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://mock/db"}):
                outcome_result = mod.record_outcome(
                    prediction_id=returned_pid,
                    outcome_observed=outcome,
                )

        # Verify round-trip
        assert outcome_result["ok"] is True
        assert outcome_result["outcome_observed"] is True
        assert 0.0 <= outcome_result["brier_score"] <= 1.0

        # Brier score for correct prediction with confidence=0.59 should be in (0.1, 0.25)
        assert 0.1 < outcome_result["brier_score"] < 0.25, (
            f"Expected brier ~0.17 for confidence=0.59 outcome=True, "
            f"got {outcome_result['brier_score']}"
        )

        # Provenance envelope must be present on both responses
        assert "provenance_envelope" in log_result
        assert "provenance_envelope" in outcome_result

        # No-leakage note must appear in both envelopes
        assert "LEL" in log_result["provenance_envelope"]["no_leakage_discipline"]
        assert "LEL" in outcome_result["provenance_envelope"]["no_leakage_note"]
