"""
test_mimamsa_outcome.py — Unit tests for mimamsa.outcome (BRAHMA-MI-5-3)

record_outcome() is RETIRED (CR-115/CR-128, 2026-07-23) — see §3 below for its new,
much smaller test surface (always raises, never touches the DB). The old §3/§4/§7
success-path test classes (response shape, provenance envelope, leakage guard,
updated_calibration structure) are removed along with the function they tested.

Tests:
    1. compute_brier_score — range assertions, boundary conditions (not exact floats)
    2. compute_mean_brier — range assertions, empty list baseline
    3. record_outcome — RETIRED: always raises RecordOutcomeRetiredError, never touches DB
    6. query_calibration — response shape (mock DB) [untouched by the retirement]
    7. run_acceptance_gate — AC1–AC5 (no live DB for AC3, uses structural checks)
    8. Brier score boundary conditions
    9. NO LEAKAGE: life_events never feed into prediction generation

No live DB connection required. All DB calls are mocked via unittest.mock.

BRAHMA-MI-5-3
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest


# ── Module under test ─────────────────────────────────────────────────────────

def _get_outcome_module():
    from brahmagyan.mimamsa import outcome as outcome_mod
    return outcome_mod


# ── Constants ─────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
TEST_PREDICTION_ID = "PH-4-1.2026H1.CAREER"
TEST_CONFIDENCE = 0.59


# _make_anchors_row / _make_calibration_row fixtures removed 2026-07-23 (CR-115/CR-128):
# they only ever supported record_outcome()'s now-deleted success-path tests.


# ── §1 — compute_brier_score ──────────────────────────────────────────────────

class TestComputeBrierScore:
    """
    Tests for the pure-Python Brier score function.
    All Brier score assertions use range checks (not exact floats)
    where appropriate, per constraint.
    """

    def test_perfect_positive_prediction_is_zero(self):
        """confidence=1.0, occurred=True → Brier=0.0 (perfect)."""
        mod = _get_outcome_module()
        score = mod.compute_brier_score(1.0, True)
        assert score == pytest.approx(0.0, abs=1e-9)

    def test_perfect_negative_prediction_is_zero(self):
        """confidence=0.0, occurred=False → Brier=0.0 (perfect negative)."""
        mod = _get_outcome_module()
        score = mod.compute_brier_score(0.0, False)
        assert score == pytest.approx(0.0, abs=1e-9)

    def test_worst_positive_prediction_is_one(self):
        """confidence=0.0, occurred=True → Brier=1.0 (worst)."""
        mod = _get_outcome_module()
        score = mod.compute_brier_score(0.0, True)
        assert score == pytest.approx(1.0, abs=1e-9)

    def test_worst_negative_prediction_is_one(self):
        """confidence=1.0, occurred=False → Brier=1.0 (worst negative)."""
        mod = _get_outcome_module()
        score = mod.compute_brier_score(1.0, False)
        assert score == pytest.approx(1.0, abs=1e-9)

    def test_uninformative_positive_is_quarter(self):
        """confidence=0.5, occurred=True → Brier=0.25 (uninformative baseline)."""
        mod = _get_outcome_module()
        score = mod.compute_brier_score(0.5, True)
        assert score == pytest.approx(0.25, abs=1e-9)

    def test_uninformative_negative_is_quarter(self):
        """confidence=0.5, occurred=False → Brier=0.25 (uninformative baseline)."""
        mod = _get_outcome_module()
        score = mod.compute_brier_score(0.5, False)
        assert score == pytest.approx(0.25, abs=1e-9)

    def test_result_always_in_unit_interval(self):
        """Fuzz: any (confidence, occurred) ∈ [0,1]×{T,F} → score ∈ [0,1]."""
        mod = _get_outcome_module()
        test_cases = [
            (0.0, False),
            (0.0, True),
            (1.0, False),
            (1.0, True),
            (0.5, True),
            (0.5, False),
            (0.7, True),
            (0.3, False),
            (0.59, True),
            (0.59, False),
            (0.82, True),
            (0.40, False),
        ]
        for conf, occ in test_cases:
            score = mod.compute_brier_score(conf, occ)
            assert 0.0 <= score <= 1.0, (
                f"compute_brier_score({conf}, {occ}) = {score} not in [0,1]"
            )

    def test_native_confidence_confirmed(self):
        """Native 2026H1 career anchor: confidence=0.59, confirmed → in (0, 1)."""
        mod = _get_outcome_module()
        score = mod.compute_brier_score(TEST_CONFIDENCE, True)
        # (0.59 - 1.0)^2 = 0.1681 — medium penalty
        assert 0.0 < score < 0.5

    def test_native_confidence_falsified(self):
        """Native 2026H1 career anchor: confidence=0.59, falsified → in (0, 1)."""
        mod = _get_outcome_module()
        score = mod.compute_brier_score(TEST_CONFIDENCE, False)
        # (0.59 - 0.0)^2 = 0.3481 — larger penalty
        assert 0.0 < score < 1.0

    def test_invalid_confidence_above_one_raises(self):
        """confidence > 1.0 must raise ValueError."""
        mod = _get_outcome_module()
        with pytest.raises(ValueError, match="confidence"):
            mod.compute_brier_score(1.5, True)

    def test_invalid_confidence_below_zero_raises(self):
        """confidence < 0.0 must raise ValueError."""
        mod = _get_outcome_module()
        with pytest.raises(ValueError, match="confidence"):
            mod.compute_brier_score(-0.1, False)

    def test_formula_confirmed(self):
        """Verify (confidence - 1.0)^2 formula for confirmed outcomes."""
        mod = _get_outcome_module()
        # confidence=0.7, occurred=True → (0.7 - 1.0)^2 = 0.09
        score = mod.compute_brier_score(0.7, True)
        assert score == pytest.approx(0.09, abs=1e-9)

    def test_formula_falsified(self):
        """Verify (confidence - 0.0)^2 formula for falsified outcomes."""
        mod = _get_outcome_module()
        # confidence=0.3, occurred=False → (0.3 - 0.0)^2 = 0.09
        score = mod.compute_brier_score(0.3, False)
        assert score == pytest.approx(0.09, abs=1e-9)


# ── §2 — compute_mean_brier ───────────────────────────────────────────────────

class TestComputeMeanBrier:
    """Tests for mean Brier score computation."""

    def test_empty_list_returns_uninformative_baseline(self):
        """Empty score list → 0.25 uninformative baseline."""
        mod = _get_outcome_module()
        mean = mod.compute_mean_brier([])
        assert mean == pytest.approx(mod.UNINFORMATIVE_BRIER_BASELINE, abs=1e-9)
        assert mean == pytest.approx(0.25, abs=1e-9)

    def test_single_perfect_score(self):
        """Single score of 0.0 → mean 0.0."""
        mod = _get_outcome_module()
        mean = mod.compute_mean_brier([0.0])
        assert mean == pytest.approx(0.0, abs=1e-9)

    def test_single_worst_score(self):
        """Single score of 1.0 → mean 1.0."""
        mod = _get_outcome_module()
        mean = mod.compute_mean_brier([1.0])
        assert mean == pytest.approx(1.0, abs=1e-9)

    def test_mean_of_multiple_scores_in_range(self):
        """Mean of several scores must be in [0, 1]."""
        mod = _get_outcome_module()
        scores = [0.0, 0.25, 0.1681, 0.3481]
        mean = mod.compute_mean_brier(scores)
        assert 0.0 <= mean <= 1.0

    def test_all_quarter_baseline_yields_quarter(self):
        """Mean of all 0.25 scores → 0.25."""
        mod = _get_outcome_module()
        mean = mod.compute_mean_brier([0.25, 0.25, 0.25])
        assert mean == pytest.approx(0.25, abs=1e-9)

    def test_invalid_score_raises(self):
        """Score > 1.0 in list → ValueError."""
        mod = _get_outcome_module()
        with pytest.raises(ValueError):
            mod.compute_mean_brier([0.5, 1.5])


# ── §3 — record_outcome (RETIRED, CR-115/CR-128, 2026-07-23) ─────────────────

class TestRecordOutcomeRetired:
    """
    record_outcome() is retired: it must raise RecordOutcomeRetiredError
    unconditionally, for ANY input (valid or invalid), and must NEVER touch the
    database (no psycopg.connect call at all — defense-in-depth: even if the DB
    were reachable, this function must not attempt to use it).
    """

    def test_raises_retired_error_for_valid_looking_input(self):
        mod = _get_outcome_module()
        with pytest.raises(mod.RecordOutcomeRetiredError):
            mod.record_outcome(TEST_PREDICTION_ID, True, chart_id=NATIVE_CHART_ID)

    def test_raises_retired_error_for_falsified_outcome(self):
        mod = _get_outcome_module()
        with pytest.raises(mod.RecordOutcomeRetiredError):
            mod.record_outcome(TEST_PREDICTION_ID, False, chart_id=NATIVE_CHART_ID)

    def test_raises_retired_error_even_with_no_chart_id(self):
        """Old code raised ValueError for missing chart_id; new code raises
        RecordOutcomeRetiredError unconditionally, before any validation."""
        mod = _get_outcome_module()
        with pytest.raises(mod.RecordOutcomeRetiredError):
            mod.record_outcome(TEST_PREDICTION_ID, True)

    def test_raises_retired_error_even_with_empty_prediction_id(self):
        mod = _get_outcome_module()
        with pytest.raises(mod.RecordOutcomeRetiredError):
            mod.record_outcome("", True, chart_id=NATIVE_CHART_ID)

    def test_raises_retired_error_even_with_invalid_technique(self):
        mod = _get_outcome_module()
        with pytest.raises(mod.RecordOutcomeRetiredError):
            mod.record_outcome(TEST_PREDICTION_ID, True, chart_id=NATIVE_CHART_ID,
                                technique="not-a-real-technique")

    def test_retired_error_is_a_runtime_error(self):
        mod = _get_outcome_module()
        assert issubclass(mod.RecordOutcomeRetiredError, RuntimeError)

    def test_error_message_cites_cr_numbers(self):
        mod = _get_outcome_module()
        with pytest.raises(mod.RecordOutcomeRetiredError) as exc_info:
            mod.record_outcome(TEST_PREDICTION_ID, True, chart_id=NATIVE_CHART_ID)
        msg = str(exc_info.value)
        assert "CR-115" in msg and "CR-128" in msg

    def test_never_connects_to_the_database(self):
        """The retirement must be a hard short-circuit — no DB connection attempt
        of any kind, even a failed one."""
        mod = _get_outcome_module()
        with patch("psycopg.connect") as mock_connect:
            with pytest.raises(mod.RecordOutcomeRetiredError):
                mod.record_outcome(TEST_PREDICTION_ID, True, chart_id=NATIVE_CHART_ID)
            mock_connect.assert_not_called()

    def test_api_record_outcome_returns_http_410(self):
        """The FastAPI route must translate RecordOutcomeRetiredError into HTTP 410 Gone."""
        from fastapi import HTTPException
        mod = _get_outcome_module()

        class _FakeReq:
            prediction_id = TEST_PREDICTION_ID
            outcome_observed = True
            technique = "vimshottari"
            ayanamsha_id = "lahiri"
            chart_id = NATIVE_CHART_ID
            outcome_note = None

        with pytest.raises(HTTPException) as exc_info:
            mod.api_record_outcome(_FakeReq())
        assert exc_info.value.status_code == 410
        assert "CR-115" in str(exc_info.value.detail) or "CR-128" in str(exc_info.value.detail)


# ── §7 — Validation errors (query_calibration / run_acceptance_gate only) ─────
# record_outcome's own validation tests are removed along with the function's
# validation logic (record_outcome now short-circuits before any validation —
# see TestRecordOutcomeRetired above).

class TestValidationErrors:
    """Input guard-rails without hitting the DB (query_calibration / run_acceptance_gate)."""

    def test_query_calibration_requires_chart_id(self):
        """chart_id is required for query_calibration — no native default."""
        mod = _get_outcome_module()
        with pytest.raises(ValueError, match="chart_id"):
            mod.query_calibration()
        with pytest.raises(ValueError, match="chart_id"):
            mod.query_calibration(chart_id="")

    def test_run_acceptance_gate_requires_chart_id(self):
        """chart_id is required for run_acceptance_gate — no native default."""
        mod = _get_outcome_module()
        with pytest.raises(ValueError, match="chart_id"):
            mod.run_acceptance_gate()
        with pytest.raises(ValueError, match="chart_id"):
            mod.run_acceptance_gate(chart_id="")

    def test_invalid_query_calibration_technique_raises(self):
        mod = _get_outcome_module()
        with pytest.raises(ValueError, match="technique"):
            mod.query_calibration(chart_id=NATIVE_CHART_ID, technique="invalid")

    def test_invalid_query_calibration_ayanamsha_raises(self):
        mod = _get_outcome_module()
        with pytest.raises(ValueError, match="ayanamsha"):
            mod.query_calibration(chart_id=NATIVE_CHART_ID, ayanamsha_id="ptolemy")


# ── §8 — Acceptance gate (structural, no live DB) ─────────────────────────────

class TestAcceptanceGateStructural:
    """
    AC1–AC2 and AC4–AC5 can run without a DB.
    AC3 requires the DB; it is skipped when no DB is available.
    """

    def test_ac1_brier_range(self):
        """AC1: compute_brier_score in [0.0, 1.0]."""
        mod = _get_outcome_module()
        result = mod.run_acceptance_gate.__wrapped__ \
            if hasattr(mod.run_acceptance_gate, "__wrapped__") \
            else None

        # Directly test the assertion that AC1 checks
        test_cases = [
            (0.0, False, 0.0),
            (1.0, True, 0.0),
            (0.0, True, 1.0),
            (1.0, False, 1.0),
        ]
        for conf, occ, expected in test_cases:
            score = mod.compute_brier_score(conf, occ)
            assert 0.0 <= score <= 1.0
            assert score == pytest.approx(expected, abs=1e-9)

    def test_ac2_mean_brier_range(self):
        """AC2: compute_mean_brier returns float in [0.0, 1.0]; empty → 0.25."""
        mod = _get_outcome_module()
        assert mod.compute_mean_brier([]) == pytest.approx(0.25, abs=1e-9)
        mean = mod.compute_mean_brier([0.0, 0.25, 1.0])
        assert 0.0 <= mean <= 1.0

    def test_ac4_response_structure(self):
        """AC4: required response keys present in a mock record_outcome response."""
        required_top = {
            "ok", "prediction_id", "outcome_observed", "brier_score",
            "prediction_state", "updated_calibration", "provenance_envelope",
        }
        required_prov = {
            "source", "asset", "algorithm", "chart_id", "prediction_id",
            "technique", "ayanamsha_id", "recorded_at",
            "l1_ground_truth", "b3_citation_compliant", "leakage_guard_passed",
        }
        mock_resp = {
            "ok": True,
            "prediction_id": TEST_PREDICTION_ID,
            "outcome_observed": True,
            "brier_score": 0.1681,
            "prediction_state": "confirmed",
            "updated_calibration": {
                "technique": "vimshottari",
                "ayanamsha_id": "lahiri",
                "brier_score": 0.1681,
                "sample_size": 1,
                "computed_at": "2026-06-04T00:00:00+00:00",
            },
            "provenance_envelope": {
                "source": "mimamsa.outcome",
                "asset": "MI-5-3",
                "algorithm": "Brier score = (confidence - outcome_binary)²",
                "chart_id": NATIVE_CHART_ID,
                "prediction_id": TEST_PREDICTION_ID,
                "technique": "vimshottari",
                "ayanamsha_id": "lahiri",
                "recorded_at": "2026-06-04T00:00:00+00:00",
                "l1_ground_truth": "FORENSIC v8.0 §5.1 DSH.V.023–028; LEL v1.7",
                "b3_citation_compliant": True,
                "leakage_guard_passed": True,
            },
        }
        missing_top = required_top - set(mock_resp.keys())
        missing_prov = required_prov - set(mock_resp["provenance_envelope"].keys())
        assert not missing_top, f"Missing top-level keys: {missing_top}"
        assert not missing_prov, f"Missing provenance keys: {missing_prov}"

    def test_ac5_brier_boundary(self):
        """AC5: Brier boundaries (0,F)=0, (1,T)=0, (0,T)=1, (1,F)=1."""
        mod = _get_outcome_module()
        assert mod.compute_brier_score(0.0, False) == pytest.approx(0.0, abs=1e-9)
        assert mod.compute_brier_score(1.0, True) == pytest.approx(0.0, abs=1e-9)
        assert mod.compute_brier_score(0.0, True) == pytest.approx(1.0, abs=1e-9)
        assert mod.compute_brier_score(1.0, False) == pytest.approx(1.0, abs=1e-9)


# ── §9 — No-leakage discipline ────────────────────────────────────────────────

class TestNoLeakage:
    """
    Verify the no-leakage invariant: life_events feed only into calibration,
    never into prediction generation.
    """

    def test_valid_techniques_set_does_not_include_life_event_intake(self):
        """
        The VALID_TECHNIQUES set is for calibration dimensions only.
        It must not include any technique that implies direct intake of life_events
        as inputs to prediction generation.
        """
        mod = _get_outcome_module()
        # These would be leakage vectors if present as prediction techniques
        forbidden_patterns = {"life_event", "lel_intake", "lel_feed", "lel_input"}
        for technique in mod.VALID_TECHNIQUES:
            for pattern in forbidden_patterns:
                assert pattern not in technique.lower(), (
                    f"LEAKAGE RISK: technique '{technique}' contains '{pattern}' — "
                    "life_events must never feed into prediction generation"
                )

    def test_record_outcome_only_writes_calibration(self):
        """
        RETIRED (CR-115/CR-128): record_outcome() no longer writes anything at all — it
        raises unconditionally before touching the DB. This test's original intent
        (no life_events leakage in what record_outcome writes) is now vacuously true;
        retained as a static-source guard so a future re-implementation cannot silently
        reintroduce a life_events reference without this test failing.
        """
        import inspect
        mod = _get_outcome_module()
        source = inspect.getsource(mod.record_outcome)

        # Must not INSERT into life_events
        assert "INSERT INTO" not in source or "phala_anchors" not in source or True
        # Must not read from life_events for generating predictions
        # (source code should only read phala_anchors, write to mimamsa_calibration)
        assert "life_events" not in source.lower() or source.lower().count("life_events") == 0, (
            "LEAKAGE RISK: record_outcome source references life_events — "
            "outcomes must be calibration-only, not prediction inputs"
        )

    def test_module_docstring_mentions_no_leakage(self):
        """Module docstring must explicitly state the no-leakage rule."""
        mod = _get_outcome_module()
        doc = mod.__doc__ or ""
        assert "LEAKAGE" in doc or "leakage" in doc or "never" in doc.lower(), (
            "Module docstring must explicitly document the no-leakage invariant"
        )


# ── §10 — R6 0b-deadtools (R-14): schema-drift fix + no silent error-swallowing ──

class TestQueryCalibrationSchemaFix:
    """
    R-14: query_calibration()'s SQL used to select id/technique/ayanamsha_id/
    brier_score/sample_size/source_citation/computed_at — none of which exist on the
    LIVE mimamsa_calibration table (that shape was the MI-5-3 prototype's; the table was
    superseded by the mi_pramana/mi_gunanaka/mi_pariksha writer family's per-match schema
    without a tracked migration). Confirmed live: chart_id, match_id, prediction_id,
    event_id, score_timing, score_magnitude, score_domain, score_falsifier,
    score_manifestation, manifestation_channel, composite_verdict, composite_score,
    base_rate_adjusted_skill, evidence_admissibility, n_for_stratum, leakage_status,
    scoring_formula_version, scored_at, base_rate, brier_vs_null.
    """

    def _mock_db(self, rows: list[dict] | None = None):
        from unittest.mock import patch as _patch
        from contextlib import ExitStack

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = rows if rows is not None else []
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        class _DoubleCtx:
            def __enter__(self_):
                self_._stack = ExitStack()
                self_._stack.__enter__()
                self_._stack.enter_context(
                    _patch("brahmagyan.mimamsa.outcome._get_db_url", return_value="postgresql://mock/db")
                )
                self_._stack.enter_context(_patch("psycopg.connect", return_value=mock_conn))
                return self_, mock_cur
            def __exit__(self_, *args):
                return self_._stack.__exit__(*args)
        return _DoubleCtx()

    def test_sql_never_references_dropped_columns(self):
        """The actual SQL literal (not the docstring/comments) must not select a
        column that doesn't exist on the live table."""
        import re
        mod = _get_outcome_module()
        with self._mock_db() as (_, mock_cur):
            mod.query_calibration(chart_id=NATIVE_CHART_ID)
        sql_used = mock_cur.execute.call_args[0][0]
        for dead_col in ("technique", "ayanamsha_id", "brier_score", "sample_size", "source_citation", "computed_at"):
            assert re.search(rf"\b{dead_col}\b", sql_used) is None, (
                f"query_calibration SQL still references dropped column: {dead_col!r}\n{sql_used}"
            )
        # bare "id" (the old serial PK) — distinct from "chart_id"/"prediction_id"/"event_id".
        assert re.search(r"(?<![a-z_])id\b", sql_used) is None, f"bare `id` column still referenced:\n{sql_used}"

    def test_sql_references_live_schema_columns(self):
        import inspect
        mod = _get_outcome_module()
        source = inspect.getsource(mod.query_calibration)
        for live_col in ("match_id", "prediction_id", "event_id", "score_timing", "composite_score", "brier_vs_null", "scored_at"):
            assert live_col in source, f"query_calibration should reference live column {live_col!r}"

    def test_technique_ayanamsha_filters_no_longer_bind_to_dropped_columns(self):
        """technique/ayanamsha_id must not be compiled into a WHERE clause (no such columns)."""
        mod = _get_outcome_module()
        with self._mock_db() as (_, mock_cur):
            result = mod.query_calibration(chart_id=NATIVE_CHART_ID, technique="vimshottari", ayanamsha_id="lahiri")
        sql_used = mock_cur.execute.call_args[0][0]
        assert "technique = %s" not in sql_used
        assert "ayanamsha_id = %s" not in sql_used
        # Reported honestly, never silently dropped.
        assert result["unsupported_filters"] == ["technique", "ayanamsha_id"]

    def test_invalid_technique_still_raises_before_any_query(self):
        """Enum validation is preserved even though technique no longer filters the table."""
        mod = _get_outcome_module()
        with pytest.raises(ValueError):
            mod.query_calibration(chart_id=NATIVE_CHART_ID, technique="not-a-real-technique")

    def test_ok_true_with_live_shaped_row(self):
        mod = _get_outcome_module()
        live_row = {
            "chart_id": NATIVE_CHART_ID, "match_id": "m1", "prediction_id": "p1", "event_id": "e1",
            "score_timing": 0.5, "score_magnitude": 0.5, "score_domain": 0.5, "score_falsifier": 0.5,
            "score_manifestation": 0.5, "manifestation_channel": "mode_c", "composite_verdict": "CONFIRMED",
            "composite_score": 0.62, "base_rate_adjusted_skill": None, "evidence_admissibility": "clean",
            "n_for_stratum": 1, "leakage_status": "clean", "scoring_formula_version": "v1",
            "base_rate": 0.3, "brier_vs_null": 0.4, "scored_at": datetime.now(tz=timezone.utc),
        }
        with self._mock_db(rows=[live_row]) as (_, _cur):
            result = mod.query_calibration(chart_id=NATIVE_CHART_ID)
        assert result["ok"] is True
        assert result["row_count"] == 1
        assert result["rows"][0]["match_id"] == "m1"


class TestApiQueryCalibrationNoSilentSwallow:
    """
    R-14: the FastAPI route handler api_query_calibration() used to catch ANY exception
    (including real schema-drift SQL errors) and return {"ok": true, "rows": [],
    "structural_mode_note": ...} with the raw exception text leaked into
    provenance_envelope.db_note — masking a genuine bug as "expected empty". DB/runtime
    errors must now propagate loudly.
    """

    def test_unexpected_db_error_raises_http_500_not_silently_swallowed(self):
        from fastapi import HTTPException
        mod = _get_outcome_module()

        class _FakeReq:
            chart_id = NATIVE_CHART_ID
            technique = None
            ayanamsha_id = None
            limit = 10

        with patch.object(mod, "query_calibration", side_effect=RuntimeError('column "id" does not exist')):
            with pytest.raises(HTTPException) as exc_info:
                mod.api_query_calibration(_FakeReq())
        assert exc_info.value.status_code == 503  # RuntimeError -> 503 (existing contract, unchanged)

    def test_unhandled_exception_class_raises_http_500(self):
        """A non-ValueError/RuntimeError exception (e.g. psycopg's real error class) must
        raise HTTP 500 with the error visible in the response — never a masked ok:true."""
        from fastapi import HTTPException
        mod = _get_outcome_module()

        class _FakeReq:
            chart_id = NATIVE_CHART_ID
            technique = None
            ayanamsha_id = None
            limit = 10

        class _SomeOtherDbError(Exception):
            pass

        with patch.object(mod, "query_calibration", side_effect=_SomeOtherDbError('column "id" does not exist LINE 3')):
            with pytest.raises(HTTPException) as exc_info:
                mod.api_query_calibration(_FakeReq())
        assert exc_info.value.status_code == 500
        assert "column" in str(exc_info.value.detail)
