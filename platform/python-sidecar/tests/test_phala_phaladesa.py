"""
test_phala_outlook.py — Unit tests for phala.outlook (BRAHMA-PH-4-5)

Acceptance criteria (per contract):
  AC1 — all 4 subsystems present: anchors, mitigations, rectification, auspicious_windows
  AC2 — summary_confidence in [0.0, 1.0]
  AC3 — tool smoke: native chart returns structurally valid response

Test sections:
  §1 — _mean_confidence helper
  §2 — phala_outlook response shape (all 4 subsystems present)
  §3 — summary_confidence correctness (mean of anchor confidences)
  §4 — provenance_envelope structure and contents
  §5 — input validation errors
  §6 — graceful degradation (sub-system failures)
  §7 — acceptance gate logic (AC1–AC5 via mocked sub-systems)

No live DB required — all sub-system fetchers are patched.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from unittest.mock import patch, MagicMock
import pytest


# ── Lazy import to avoid psycopg at import time ────────────────────────────────

def _get_outlook_module():
    from brahmagyan.phala import outlook as mod
    return mod


# ── Fixtures ───────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

DEFAULT_ANCHOR_1: dict[str, Any] = {
    "anchor_id": "PH-4-1.2026H1.CAREER",
    "window": {"start": "2026-01-01", "end": "2026-06-30"},
    "theme": "career_consolidation",
    "confidence": 0.59,
    "falsifier": "If no new contract before 2026-07-01, this prediction is false.",
    "contributing_dashas": ["DSH.V.023: Mercury MD Saturn AD"],
    "contributing_signals": ["SIG.09 Mercury 8-system convergence"],
    "source_citation": "FORENSIC v8.0 §5.1 DSH.V.023; MSR v5.0 SIG.09",
    "prediction_state": "open",
    "outcome_note": None,
}

DEFAULT_ANCHOR_2: dict[str, Any] = {
    "anchor_id": "PH-4-1.2026H2.SPIRIT",
    "window": {"start": "2026-07-01", "end": "2026-12-31"},
    "theme": "spiritual_practice_intensification",
    "confidence": 0.46,
    "falsifier": "If no formal spiritual practice before 2027-01-01, false.",
    "contributing_dashas": ["DSH.V.023: Mercury MD Saturn AD"],
    "contributing_signals": ["SIG.14 Sun 10H career-density"],
    "source_citation": "FORENSIC v8.0 §5.1 DSH.V.023; SADE_SATI cycle 2",
    "prediction_state": "open",
    "outcome_note": None,
}

DEFAULT_ANCHORS_PROV: dict[str, Any] = {
    "source": "phala.anchors",
    "asset": "PH-4-1",
    "algorithm": "dasha_quality × signal_strength × convergence_score",
    "min_confidence_applied": 0.0,
    "chart_id": NATIVE_CHART_ID,
    "queried_at": "2026-06-04T00:00:00+00:00",
    "l1_ground_truth": "FORENSIC v8.0 §5.1 DSH.V.023–028",
    "b3_citation_compliant": True,
    "all_falsifiers_present": True,
}

DEFAULT_MITIGATION_1: dict[str, Any] = {
    "anchor_id": "PH-4-1.2026H1.CAREER",
    "theme": "career",
    "mitigation_type": "mantra",
    "mitigation_text": "Recite the beej mantra of the 10th lord daily.",
    "source_l0_rule_id": "BPHS-CAREER-MANTRA",
    "source_citation": "BPHS.3.6-8",
    "l2_remediation_hub_id": None,
    "asset_version": "1.0",
    "computed_at": "2026-06-04T00:00:00+00:00",
}

DEFAULT_MITIGATIONS_PROV: dict[str, Any] = {
    "chart_id": NATIVE_CHART_ID,
    "anchor_id_filter": None,
    "mitigation_type_filter": None,
    "asset": "phala.mitigation",
    "asset_version": "1.0",
    "build_tag": "PH-4-2",
    "source": "phala.mitigation",
    "computed_at": "2026-06-04T00:00:00+00:00",
}

DEFAULT_RECTIFICATION: dict[str, Any] = {
    "chart_id": NATIVE_CHART_ID,
    "best_candidate_time": "10:44",
    "confidence": 0.68,
    "train_score": 0.71,
    "test_score": 0.64,
    "candidate_count": 61,
    "source_citation": "FORENSIC v8.0 §5.1 + LEL v1.7 (train 1–43 / test 44–57)",
}

DEFAULT_RECTIFICATION_PROV: dict[str, Any] = {
    "source": "phala.rectification",
    "asset": "PH-4-3",
    "algorithm": "dasha_alignment_train_test_split",
    "train_split": "events 1–43 (75%)",
    "test_split": "events 44–57 (25%, held-out)",
    "leakage_check": "PASS",
    "b10_compliance": "dasha-level only",
    "computed_at": "2026-06-04T00:00:00+00:00",
}

DEFAULT_AUSPICIOUS_WINDOWS: list[dict[str, Any]] = [
    {
        "date": "2026-06-10",
        "tithi": "Dvitiya",
        "vara": "Budhavara",
        "moon_nakshatra": "Rohini",
        "yoga": "Siddhi",
        "karana": "Bava",
        "auspicious_metadata": {},
        "top_windows": [
            {"type": "amrit_kalam", "start_time": "08:00", "end_time": "09:30", "score": 0.9}
        ],
        "source": "panchanga_daily / phala.outlook-PH-4-4",
    }
]

DEFAULT_AUSPICIOUS_PROV: dict[str, Any] = {
    "source": "panchanga_daily",
    "asset": "PH-4-4 / PANCHANG_DAILY",
    "date_range": {"start": "2026-06-04", "end": "2026-12-04"},
    "rows_returned": 1,
    "queried_at": "2026-06-04T00:00:00+00:00",
}


# ── Patch helpers ──────────────────────────────────────────────────────────────

def _patch_all_subsystems(
    anchors=None,
    anchors_prov=None,
    mitigations=None,
    mitigations_prov=None,
    rectification=None,
    rectification_prov=None,
    auspicious_windows=None,
    auspicious_prov=None,
):
    """Return a context manager that patches all 4 sub-system fetchers."""
    from unittest.mock import patch

    _anchors = anchors if anchors is not None else [DEFAULT_ANCHOR_1, DEFAULT_ANCHOR_2]
    _anchors_prov = anchors_prov if anchors_prov is not None else DEFAULT_ANCHORS_PROV
    _mitigations = mitigations if mitigations is not None else [DEFAULT_MITIGATION_1]
    _mitigations_prov = mitigations_prov if mitigations_prov is not None else DEFAULT_MITIGATIONS_PROV
    _rectification = rectification if rectification is not None else DEFAULT_RECTIFICATION
    _rectification_prov = rectification_prov if rectification_prov is not None else DEFAULT_RECTIFICATION_PROV
    _auspicious = auspicious_windows if auspicious_windows is not None else DEFAULT_AUSPICIOUS_WINDOWS
    _auspicious_prov = auspicious_prov if auspicious_prov is not None else DEFAULT_AUSPICIOUS_PROV

    return [
        patch(
            "brahmagyan.phala.outlook._fetch_anchors",
            return_value=(_anchors, _anchors_prov),
        ),
        patch(
            "brahmagyan.phala.outlook._fetch_mitigations",
            return_value=(_mitigations, _mitigations_prov),
        ),
        patch(
            "brahmagyan.phala.outlook._fetch_rectification",
            return_value=(_rectification, _rectification_prov),
        ),
        patch(
            "brahmagyan.phala.outlook._fetch_auspicious_windows",
            return_value=(_auspicious, _auspicious_prov),
        ),
    ]


# ── §1 — _mean_confidence helper ───────────────────────────────────────────────

class TestMeanConfidence:
    """Tests for the pure-Python _mean_confidence function."""

    def test_empty_list_returns_zero(self):
        mod = _get_outlook_module()
        result = mod._mean_confidence([])
        assert result == 0.0

    def test_single_anchor(self):
        mod = _get_outlook_module()
        result = mod._mean_confidence([{"confidence": 0.6}])
        assert result == pytest.approx(0.6, abs=0.0001)

    def test_two_anchors_mean(self):
        mod = _get_outlook_module()
        result = mod._mean_confidence([
            {"confidence": 0.59},
            {"confidence": 0.46},
        ])
        # mean(0.59, 0.46) = 0.525
        assert result == pytest.approx(0.525, abs=0.0001)

    def test_all_ones_returns_one(self):
        mod = _get_outlook_module()
        result = mod._mean_confidence([
            {"confidence": 1.0},
            {"confidence": 1.0},
        ])
        assert result == pytest.approx(1.0, abs=0.0001)

    def test_all_zeros_returns_zero(self):
        mod = _get_outlook_module()
        result = mod._mean_confidence([
            {"confidence": 0.0},
            {"confidence": 0.0},
        ])
        assert result == pytest.approx(0.0, abs=0.0001)

    def test_clamp_above_one(self):
        """Result must be clamped to [0.0, 1.0]."""
        mod = _get_outlook_module()
        result = mod._mean_confidence([{"confidence": 1.5}])
        assert 0.0 <= result <= 1.0

    def test_missing_confidence_key_treated_as_zero(self):
        mod = _get_outlook_module()
        result = mod._mean_confidence([{"theme": "no_confidence_key"}])
        assert result == pytest.approx(0.0, abs=0.0001)

    def test_nine_anchor_mean(self):
        """Nine anchors as seeded in PH-4-1."""
        mod = _get_outlook_module()
        confidences = [0.59, 0.46, 0.40, 0.38, 0.27, 0.31, 0.30, 0.36, 0.26]
        anchors = [{"confidence": c} for c in confidences]
        result = mod._mean_confidence(anchors)
        expected = sum(confidences) / len(confidences)
        assert result == pytest.approx(expected, abs=0.001)
        assert 0.0 <= result <= 1.0


# ── §2 — phala_outlook response shape ─────────────────────────────────────────

class TestPhalOutlookResponseShape:
    """
    AC1: all 4 subsystems present.
    AC2: summary_confidence in [0.0, 1.0].
    AC3: response has ok=True.
    """

    def test_all_four_subsystems_present(self):
        """AC1: anchors, mitigations, rectification, auspicious_windows all in response."""
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)

        assert "anchors" in result, "anchors subsystem missing"
        assert "mitigations" in result, "mitigations subsystem missing"
        assert "rectification" in result, "rectification subsystem missing"
        assert "auspicious_windows" in result, "auspicious_windows subsystem missing"

    def test_ok_is_true(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert result["ok"] is True

    def test_chart_id_echoed(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert result["chart_id"] == NATIVE_CHART_ID

    def test_horizon_months_echoed(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID, horizon_months=6)
        assert result["horizon_months"] == 6

    def test_query_window_present(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert "query_window" in result
        assert "start" in result["query_window"]
        assert "end" in result["query_window"]
        # start == today
        assert result["query_window"]["start"] == date.today().isoformat()

    def test_summary_confidence_in_result(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert "summary_confidence" in result

    def test_provenance_envelope_present(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert "provenance_envelope" in result


# ── §3 — summary_confidence correctness ───────────────────────────────────────

class TestSummaryConfidence:
    """AC2: summary_confidence = mean(anchor.confidence), in [0.0, 1.0]."""

    def test_summary_confidence_is_mean_of_anchor_confidences(self):
        mod = _get_outlook_module()
        anchors = [
            {**DEFAULT_ANCHOR_1, "confidence": 0.59},
            {**DEFAULT_ANCHOR_2, "confidence": 0.46},
        ]
        patches = _patch_all_subsystems(anchors=anchors)
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        expected = (0.59 + 0.46) / 2
        assert result["summary_confidence"] == pytest.approx(expected, abs=0.001)

    def test_summary_confidence_in_unit_interval(self):
        """AC2: summary_confidence always in [0.0, 1.0]."""
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        sc = result["summary_confidence"]
        assert 0.0 <= sc <= 1.0, f"summary_confidence={sc} not in [0.0, 1.0]"

    def test_summary_confidence_zero_when_no_anchors(self):
        """Zero anchors → summary_confidence = 0.0."""
        mod = _get_outlook_module()
        patches = _patch_all_subsystems(anchors=[])
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert result["summary_confidence"] == pytest.approx(0.0, abs=0.0001)

    def test_summary_confidence_single_anchor(self):
        mod = _get_outlook_module()
        anchors = [{**DEFAULT_ANCHOR_1, "confidence": 0.73}]
        patches = _patch_all_subsystems(anchors=anchors)
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert result["summary_confidence"] == pytest.approx(0.73, abs=0.001)


# ── §4 — provenance_envelope structure ────────────────────────────────────────

class TestProvenanceEnvelope:
    """Verify provenance_envelope shape and contents."""

    def _run(self, horizon_months=12):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID, horizon_months=horizon_months)
        return result["provenance_envelope"]

    def test_source_is_phala_outlook(self):
        prov = self._run()
        assert prov["source"] == "phala.outlook"

    def test_asset_is_ph_4_5(self):
        prov = self._run()
        assert prov["asset"] == "PH-4-5"

    def test_layers_contains_all_four(self):
        prov = self._run()
        layers = prov["layers"]
        for expected in ["PH-4-1", "PH-4-2", "PH-4-3", "PH-4-4"]:
            assert expected in layers, f"{expected} missing from layers={layers}"

    def test_layer_provenances_present(self):
        prov = self._run()
        assert "layer_provenances" in prov
        lp = prov["layer_provenances"]
        for key in ("PH-4-1", "PH-4-2", "PH-4-3", "PH-4-4"):
            assert key in lp, f"layer_provenances missing {key}"

    def test_chart_id_echoed_in_provenance(self):
        prov = self._run()
        assert prov["chart_id"] == NATIVE_CHART_ID

    def test_computed_at_present(self):
        prov = self._run()
        assert "computed_at" in prov
        assert isinstance(prov["computed_at"], str)
        assert len(prov["computed_at"]) > 0

    def test_horizon_months_in_provenance(self):
        prov = self._run(horizon_months=6)
        assert prov["horizon_months"] == 6

    def test_date_range_in_provenance(self):
        prov = self._run()
        assert "date_range" in prov
        assert "start" in prov["date_range"]
        assert "end" in prov["date_range"]

    def test_summary_confidence_algorithm_in_provenance(self):
        prov = self._run()
        assert "summary_confidence_algorithm" in prov
        assert "mean" in prov["summary_confidence_algorithm"].lower()


# ── §5 — Input validation ──────────────────────────────────────────────────────

class TestInputValidation:
    """Validate input guard-rails."""

    def test_empty_chart_id_raises_value_error(self):
        mod = _get_outlook_module()
        with pytest.raises(ValueError, match="chart_id"):
            mod.phala_outlook("", horizon_months=12)

    def test_horizon_months_zero_raises(self):
        mod = _get_outlook_module()
        with pytest.raises(ValueError, match="horizon_months"):
            mod.phala_outlook(NATIVE_CHART_ID, horizon_months=0)

    def test_horizon_months_negative_raises(self):
        mod = _get_outlook_module()
        with pytest.raises(ValueError, match="horizon_months"):
            mod.phala_outlook(NATIVE_CHART_ID, horizon_months=-1)

    def test_horizon_months_too_large_raises(self):
        mod = _get_outlook_module()
        with pytest.raises(ValueError, match="horizon_months"):
            mod.phala_outlook(NATIVE_CHART_ID, horizon_months=121)

    def test_horizon_months_boundary_1_ok(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID, horizon_months=1)
        assert result["ok"] is True

    def test_horizon_months_boundary_120_ok(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems()
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID, horizon_months=120)
        assert result["ok"] is True


# ── §6 — Graceful degradation ──────────────────────────────────────────────────

class TestGracefulDegradation:
    """
    Sub-system failures should degrade gracefully.
    The composite call must still return all 4 keys, with empty/error values
    for the failed sub-system.
    """

    def test_anchors_failure_degrades_gracefully(self):
        """If PH-4-1 fails, anchors=[] and result is still valid."""
        mod = _get_outlook_module()
        patches = _patch_all_subsystems(anchors=[], anchors_prov={"error": "DB down", "source": "phala.anchors"})
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert result["anchors"] == []
        assert result["ok"] is True
        # summary_confidence must still be 0.0
        assert result["summary_confidence"] == pytest.approx(0.0, abs=0.0001)

    def test_mitigations_failure_degrades_gracefully(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems(mitigations=[], mitigations_prov={"error": "no table"})
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert result["mitigations"] == []
        assert result["ok"] is True

    def test_rectification_failure_degrades_gracefully(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems(
            rectification={"error": "no candidates", "best_candidate_time": None},
            rectification_prov={"error": "no candidates"},
        )
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert "rectification" in result
        assert result["ok"] is True

    def test_auspicious_windows_failure_degrades_gracefully(self):
        mod = _get_outlook_module()
        patches = _patch_all_subsystems(auspicious_windows=[], auspicious_prov={"error": "table empty"})
        with patches[0], patches[1], patches[2], patches[3]:
            result = mod.phala_outlook(NATIVE_CHART_ID)
        assert result["auspicious_windows"] == []
        assert result["ok"] is True


# ── §7 — Acceptance gate ───────────────────────────────────────────────────────

class TestAcceptanceGate:
    """AC1–AC5 validated through run_acceptance_gate with mocked sub-systems."""

    def _run_gate(self, **kwargs) -> dict[str, Any]:
        mod = _get_outlook_module()
        patches = _patch_all_subsystems(**kwargs)
        with patches[0], patches[1], patches[2], patches[3]:
            return mod.run_acceptance_gate(NATIVE_CHART_ID)

    def test_gate_passes_with_valid_inputs(self):
        gate = self._run_gate()
        assert gate["gate_passed"] is True, f"Gate failed: {gate['checks']}"

    def test_gate_checks_list_has_five_items(self):
        gate = self._run_gate()
        assert len(gate["checks"]) == 5

    def test_gate_ac1_all_subsystems_present(self):
        gate = self._run_gate()
        ac1 = next(c for c in gate["checks"] if c["id"] == "AC1")
        assert ac1["passed"] is True

    def test_gate_ac2_summary_confidence_in_range(self):
        gate = self._run_gate()
        ac2 = next(c for c in gate["checks"] if c["id"] == "AC2")
        assert ac2["passed"] is True

    def test_gate_ac3_provenance_source_correct(self):
        gate = self._run_gate()
        ac3 = next(c for c in gate["checks"] if c["id"] == "AC3")
        assert ac3["passed"] is True

    def test_gate_ac4_layers_all_present(self):
        gate = self._run_gate()
        ac4 = next(c for c in gate["checks"] if c["id"] == "AC4")
        assert ac4["passed"] is True

    def test_gate_ac5_no_exception(self):
        gate = self._run_gate()
        ac5 = next(c for c in gate["checks"] if c["id"] == "AC5")
        assert ac5["passed"] is True

    def test_gate_fails_when_phala_outlook_raises(self):
        """
        AC5 fails when phala_outlook raises at the top level.

        _fetch_anchors raising RuntimeError is internally caught by phala_outlook
        and degrades gracefully (returns empty anchors). AC5 still passes.

        To trigger an AC5 failure we need to patch phala_outlook itself to raise.
        """
        mod = _get_outlook_module()
        with patch(
            "brahmagyan.phala.outlook.phala_outlook",
            side_effect=ValueError("fatal — should not happen"),
        ):
            gate = mod.run_acceptance_gate(NATIVE_CHART_ID)
        # AC5 fails: phala_outlook raised
        ac5 = next(c for c in gate["checks"] if c["id"] == "AC5")
        assert ac5["passed"] is False
        assert gate["gate_passed"] is False

    def test_gate_returns_chart_id(self):
        gate = self._run_gate()
        assert gate["chart_id"] == NATIVE_CHART_ID


# ── §8 — Gate-1 class-1 fix regressions ───────────────────────────────────────

class TestGate1ClassOneRegressions:
    """
    Regression tests for BRAHMA-PH-4-5 Gate-1 class-1 fixes:

      FIX-1  source_citation must be non-null (B.3 mandate) even when PH-4-3
             has no candidates seeded yet. Prior code returned None.

      FIX-2  provenance_envelope fallback must carry a `source` key. Prior code
             returned {} (bare empty dict) when a sub-system result omitted the
             provenance_envelope key.

      FIX-3  registerPhalaOutlookTool wired into server.ts (tested indirectly
             via the import/registration path; direct server-level wiring is
             verified in the TS test suite).
    """

    # ── FIX-1: source_citation non-null from _fetch_rectification ─────────────

    def test_fetch_rectification_no_candidates_source_citation_not_none(self):
        """
        When phala_rectification has no rows (raw=None), _fetch_rectification
        must NOT return source_citation=None. B.3 mandate: every row carries
        a non-null source citation.

        The no-candidates path is exercised by patching psycopg2 inside the
        function's local import scope.
        """
        mod = _get_outlook_module()

        # Build mock DB cursor that returns None (no rectification rows)
        cur_mock = MagicMock()
        cur_mock.__enter__ = MagicMock(return_value=cur_mock)
        cur_mock.__exit__ = MagicMock(return_value=False)
        cur_mock.fetchone.return_value = None
        conn_mock = MagicMock()
        conn_mock.cursor.return_value = cur_mock
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)

        psycopg2_mock = MagicMock()
        psycopg2_mock.connect.return_value = conn_mock
        psycopg2_mock.extras.RealDictCursor = MagicMock()

        with patch.dict("sys.modules", {"psycopg2": psycopg2_mock,
                                         "psycopg2.extras": psycopg2_mock.extras}):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test/db"}):
                rectification, prov = mod._fetch_rectification(NATIVE_CHART_ID)

        # source_citation must be non-null
        assert rectification.get("source_citation") is not None, (
            "source_citation must be non-null even when no candidates exist (B.3 mandate)"
        )
        assert isinstance(rectification["source_citation"], str)
        assert len(rectification["source_citation"]) > 0

    def test_fetch_rectification_no_candidates_source_citation_contains_forensic(self):
        """
        The no-candidates source_citation placeholder must reference FORENSIC (B.3).
        """
        mod = _get_outlook_module()

        cur_mock = MagicMock()
        cur_mock.__enter__ = MagicMock(return_value=cur_mock)
        cur_mock.__exit__ = MagicMock(return_value=False)
        cur_mock.fetchone.return_value = None
        conn_mock = MagicMock()
        conn_mock.cursor.return_value = cur_mock
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)

        psycopg2_mock = MagicMock()
        psycopg2_mock.connect.return_value = conn_mock
        psycopg2_mock.extras.RealDictCursor = MagicMock()

        with patch.dict("sys.modules", {"psycopg2": psycopg2_mock,
                                         "psycopg2.extras": psycopg2_mock.extras}):
            with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test/db"}):
                rectification, _ = mod._fetch_rectification(NATIVE_CHART_ID)

        assert "FORENSIC" in rectification["source_citation"], (
            "source_citation placeholder must cite FORENSIC (B.3 derivation-ledger)"
        )

    # ── FIX-2: provenance_envelope fallback has `source` key ──────────────────

    def test_fetch_anchors_returns_prov_with_source_key_when_engine_omits_it(self):
        """
        When event_anchors() returns a result without provenance_envelope,
        _fetch_anchors must return a fallback provenance dict that includes
        a non-empty `source` key (not bare {}).
        """
        mod = _get_outlook_module()

        # Simulate event_anchors returning result with NO provenance_envelope key
        with patch("brahmagyan.phala.anchors.event_anchors",
                   return_value={"anchors": [DEFAULT_ANCHOR_1]}):
            _, prov = mod._fetch_anchors(NATIVE_CHART_ID, {"start": "2026-01-01", "end": "2026-12-31"})

        assert "source" in prov, (
            "provenance_envelope must include 'source' key even when sub-system omits it"
        )
        assert prov["source"], "provenance_envelope.source must be non-empty"

    def test_fetch_mitigations_returns_prov_with_source_key_when_engine_omits_it(self):
        """
        When mitigation_map() returns a result without provenance_envelope,
        _fetch_mitigations must return a fallback provenance dict with `source` key.
        """
        mod = _get_outlook_module()

        conn_mock = MagicMock()
        conn_mock.__enter__ = MagicMock(return_value=conn_mock)
        conn_mock.__exit__ = MagicMock(return_value=False)

        psycopg2_mock = MagicMock()
        psycopg2_mock.connect.return_value = conn_mock
        psycopg2_mock.extras = MagicMock()

        # mitigation_map returns result without provenance_envelope
        with patch.dict("sys.modules", {"psycopg2": psycopg2_mock,
                                         "psycopg2.extras": psycopg2_mock.extras}):
            with patch("brahmagyan.phala.mitigation.mitigation_map",
                       return_value={"mitigations": [DEFAULT_MITIGATION_1]}) as mitigation_map:
                with patch.dict("os.environ", {"DATABASE_URL": "postgresql://test/db"}):
                    query_range = {"start": "2026-08-17", "end": "2028-02-08"}
                    _, prov = mod._fetch_mitigations(NATIVE_CHART_ID, query_range)

        assert "source" in prov, (
            "provenance_envelope must include 'source' key even when sub-system omits it"
        )
        assert prov["source"], "provenance_envelope.source must be non-empty"
        mitigation_map.assert_called_once_with(
            conn_mock, NATIVE_CHART_ID, date_range=query_range
        )

    def test_fetch_anchors_uses_returned_prov_when_present(self):
        """
        When event_anchors() returns a valid provenance_envelope, it is used as-is.
        """
        mod = _get_outlook_module()

        expected_prov = {"source": "phala.anchors", "asset": "PH-4-1", "extra": "data"}
        with patch("brahmagyan.phala.anchors.event_anchors",
                   return_value={"anchors": [], "provenance_envelope": expected_prov}):
            _, prov = mod._fetch_anchors(NATIVE_CHART_ID, {"start": "2026-01-01", "end": "2026-12-31"})

        assert prov == expected_prov
