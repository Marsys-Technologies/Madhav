"""
test_w45_post_fit_rebuild.py -- DB-free unit tests for W4.5 post-fit rebuild.

Tests the following in isolation:
  1. TestFittedWeightsLoading  -- mock DB rows -> correct weight dict; fallback 0.0
  2. TestCalibrationStateStamper -- §N.8 gate; correct WHERE clause
  3. TestProspectiveLedgerSeeding -- forward-only; INSERT shape; claim/falsifier text
  4. TestBuildReportShape -- all required report keys present
  5. TestI2ImportGuard -- no imports from gochara_grammar/intensity/sweep
  6. TestHonestFallback -- empty gochara_v3_calibration -> weights=0.0, rows_stamped=0

I2: no gochara_grammar/*, gochara_intensity/*, ka_gochara_sweep/* imports.
I4: empty corpus -> honest 0.0, no fabrication.
§N.8: calibration_state only stamped when real fit rows exist.
AC5: filing_method = 'explicit_filing_tool' in every INSERT.
AC4: forward windows only (window_end >= today).

All tests are fully DB-free — a lightweight recording fake connection is used.
"""
from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch, call

import pytest

# ── path setup ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parents[2]))   # scripts/
sys.path.insert(0, str(Path(__file__).parents[4]))   # platform/python-sidecar/

import kala_admission.w45_post_fit_rebuild as mod
from kala_admission.w45_post_fit_rebuild import (
    ADMITTED_MECHANISM_IDS,
    CHART_IDS,
    FILED_BY,
    FORMULA_VERSION,
    MODEL_TAG,
    NATIVE_CHART_ID,
    ABHINANDAN_CHART_ID,
    SOURCE_CITATION,
    STATE_EMPIRICALLY_CALIBRATED,
    STATE_STRUCTURAL_PRIOR,
    TABLE_CALIBRATION,
    TABLE_LEDGER,
    TABLE_WINDOWS,
    _build_claim,
    _build_confidence,
    _build_falsifier,
    build_post_fit_report,
    load_fitted_weights,
    seed_prospective_ledger,
    stamp_empirically_calibrated,
)


# ═══════════════════════════════════════════════════════════════════════════
# Fake connection infrastructure
# ═══════════════════════════════════════════════════════════════════════════

class _FakeCursor:
    """Records every statement; returns caller-injected rows."""

    def __init__(self, owner: "_FakeConn"):
        self._owner = owner
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.rowcount = self._owner._execute(sql, params)
        return self

    def fetchone(self):
        rows = self._owner._rows_for_next
        return rows[0] if rows else None

    def fetchall(self):
        return list(self._owner._rows_for_next)


class _FakeConn:
    """Lightweight recording fake connection.

    `responder(sql, params) -> list[dict]` drives return values per query.
    `rowcount_for_update` is returned as UPDATE rowcount.
    Commit/rollback/close raise AssertionError (§N.2 — writer must not call them).
    """

    def __init__(self, responder=None, rowcount_for_update: int = 0):
        self._responder = responder or (lambda sql, params: [])
        self._rowcount_for_update = rowcount_for_update
        self._rows_for_next: list = []
        self.statements: list[tuple[str, Any]] = []

    def cursor(self):
        return _FakeCursor(self)

    def _execute(self, sql: str, params=None) -> int:
        self.statements.append((sql, params))
        self._rows_for_next = self._responder(sql, params)
        # Return a rowcount for UPDATE statements.
        if sql.strip().upper().startswith("UPDATE"):
            return self._rowcount_for_update
        return 0

    def execute(self, sql, params=None):
        self._execute(sql, params)
        return _FakeCursor(self)

    def commit(self):  # pragma: no cover
        raise AssertionError("w45 script called conn.commit() on the test connection")

    def rollback(self):  # pragma: no cover
        raise AssertionError("w45 script called conn.rollback() on the test connection")

    def close(self):  # pragma: no cover
        raise AssertionError("w45 script called conn.close() on the test connection")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_calibration_row(toggle_key: str, weight: float, fit_run_id: str = "run-abc") -> dict:
    return {
        "weight_value": weight,
        "fit_run_id": fit_run_id,
        "fit_provenance": {"dataset_hash": "deadbeef01"},
    }


def _make_window_row(
    event_class: str = "career_advancement",
    window_start: Optional[date] = None,
    window_end: Optional[date] = None,
    signed_intensity: float = 0.72,
) -> dict:
    today = date.today()
    if window_start is None:
        window_start = today + timedelta(days=30)
    if window_end is None:
        window_end = today + timedelta(days=90)
    return {
        "event_class": event_class,
        "window_start": window_start,
        "window_end": window_end,
        "signed_intensity": signed_intensity,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 1. TestFittedWeightsLoading
# ═══════════════════════════════════════════════════════════════════════════

class TestFittedWeightsLoading:
    """Verify weight loading from gochara_v3_calibration mock rows."""

    def test_all_toggle_keys_present_in_output(self):
        """Output dict always has all 10 admitted toggle_keys."""
        conn = _FakeConn(responder=lambda sql, params: [])
        weights, _, _ = load_fitted_weights(conn)
        assert set(weights.keys()) == ADMITTED_MECHANISM_IDS

    def test_fitted_weight_loaded_correctly(self):
        """A row with weight_value=0.123 is loaded as 0.123."""
        target_key = "w21_av_gating"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [_make_calibration_row(target_key, 0.123)]
            return []

        conn = _FakeConn(responder=responder)
        weights, _, _ = load_fitted_weights(conn)
        assert abs(weights[target_key] - 0.123) < 1e-9

    def test_missing_toggle_key_falls_back_to_zero(self):
        """I4: a toggle_key absent from gochara_v3_calibration → 0.0."""
        conn = _FakeConn(responder=lambda sql, params: [])
        weights, _, _ = load_fitted_weights(conn)
        for tk in ADMITTED_MECHANISM_IDS:
            assert weights[tk] == 0.0, f"Expected 0.0 for missing key {tk}"

    def test_negative_weight_clamped_to_zero(self):
        """I4: negative weight_value in DB → clamped to 0.0 (max(0.0, value))."""
        target_key = "w22_moorti_nirnaya"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [_make_calibration_row(target_key, -0.05)]
            return []

        conn = _FakeConn(responder=responder)
        weights, _, _ = load_fitted_weights(conn)
        assert weights[target_key] == 0.0, "Negative weight must be clamped to 0.0"

    def test_fit_run_ids_collected(self):
        """fit_run_ids_used contains the fit_run_id from the row."""
        target_key = "w23_tara_bala"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [_make_calibration_row(target_key, 0.05, fit_run_id="run-xyz")]
            return []

        conn = _FakeConn(responder=responder)
        _, fit_run_ids, _ = load_fitted_weights(conn)
        assert "run-xyz" in fit_run_ids

    def test_dataset_hash_extracted_from_provenance(self):
        """dataset_hash is extracted from fit_provenance of the first match."""
        target_key = "w24_sade_sati"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [{
                    "weight_value": 0.08,
                    "fit_run_id": "run-111",
                    "fit_provenance": {"dataset_hash": "abc123"},
                }]
            return []

        conn = _FakeConn(responder=responder)
        _, _, dataset_hash = load_fitted_weights(conn)
        assert dataset_hash == "abc123"

    def test_db_error_on_one_key_falls_back_to_zero(self):
        """DB error on a single toggle_key → honest 0.0 for that key, others unaffected."""
        call_count = [0]

        def responder(sql, params):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("simulated DB error")
            return []

        conn = _FakeConn(responder=responder)
        # Should not raise; all weights default to 0.0.
        weights, _, _ = load_fitted_weights(conn)
        assert all(v == 0.0 for v in weights.values())


# ═══════════════════════════════════════════════════════════════════════════
# 2. TestCalibrationStateStamper
# ═══════════════════════════════════════════════════════════════════════════

class TestCalibrationStateStamper:
    """Verify §N.8 gate and correct UPDATE WHERE clause."""

    def test_no_fit_rows_skips_update(self):
        """§N.8: if fit_run_ids is empty, no UPDATE is issued."""
        conn = _FakeConn()
        count = stamp_empirically_calibrated(conn, fit_run_ids=[])
        assert count == 0
        updates = [s for s, _ in conn.statements if s.strip().upper().startswith("UPDATE")]
        assert updates == [], "No UPDATE should be issued when fit_run_ids is empty"

    def test_update_uses_correct_calibration_state_values(self):
        """UPDATE sets 'empirically_calibrated' from 'structural_prior'.

        Values are passed as parameterized %s placeholders, so we check
        both the SQL template (for column names) and the params tuple
        (for the actual state strings) — not the literal SQL text.
        """
        conn = _FakeConn(rowcount_for_update=7)
        count = stamp_empirically_calibrated(conn, fit_run_ids=["run-001"])
        assert count == 7

        updates = [(s, p) for s, p in conn.statements if s.strip().upper().startswith("UPDATE")]
        assert len(updates) == 1
        sql, params = updates[0]
        # SQL template must reference the column and use parameterized placeholders.
        assert "calibration_state" in sql.lower()
        assert "%s" in sql
        # The actual state values live in the params sequence.
        params_str = str(params)
        assert STATE_EMPIRICALLY_CALIBRATED in params_str, (
            f"'empirically_calibrated' not found in UPDATE params: {params}"
        )
        assert STATE_STRUCTURAL_PRIOR in params_str, (
            f"'structural_prior' not found in UPDATE params: {params}"
        )

    def test_update_is_scoped_to_g3_era_slice(self):
        """UPDATE WHERE clause includes era_slice_key LIKE 'g3_%'."""
        conn = _FakeConn(rowcount_for_update=3)
        stamp_empirically_calibrated(conn, fit_run_ids=["run-001"])
        updates = [s for s, _ in conn.statements if s.strip().upper().startswith("UPDATE")]
        assert len(updates) == 1
        sql = updates[0].lower()
        assert "g3_" in sql or "g3_%" in sql or "like" in sql

    def test_update_is_scoped_to_both_chart_ids(self):
        """UPDATE WHERE clause includes both chart IDs (ANY array)."""
        seen_params = []

        def responder(sql, params):
            if sql.strip().upper().startswith("UPDATE"):
                seen_params.append(params)
            return []

        conn = _FakeConn(responder=responder, rowcount_for_update=0)
        stamp_empirically_calibrated(conn, fit_run_ids=["run-001"])

        # Both chart IDs must appear in the params.
        assert len(seen_params) == 1
        flat_params = str(seen_params[0])
        assert NATIVE_CHART_ID in flat_params
        assert ABHINANDAN_CHART_ID in flat_params

    def test_zero_rows_updated_when_all_already_calibrated(self):
        """If rowcount is 0 (all rows already stamped), returns 0 — no fabrication."""
        conn = _FakeConn(rowcount_for_update=0)
        count = stamp_empirically_calibrated(conn, fit_run_ids=["run-001"])
        assert count == 0


# ═══════════════════════════════════════════════════════════════════════════
# 3. TestProspectiveLedgerSeeding
# ═══════════════════════════════════════════════════════════════════════════

class TestProspectiveLedgerSeeding:
    """Verify forward-only AC4, INSERT shape AC5, claim/falsifier text."""

    def _make_conn_with_windows(
        self,
        windows: list[dict],
        already_filed: bool = False,
        rowcount_for_update: int = 0,
    ) -> _FakeConn:
        """Build a fake connection that returns `windows` for SELECT and
        optionally returns a row for the 'already filed' check."""

        def responder(sql, params):
            sql_upper = sql.strip().upper()
            if sql_upper.startswith("SELECT") and TABLE_WINDOWS in sql:
                return windows
            if sql_upper.startswith("SELECT") and TABLE_LEDGER in sql:
                # _window_already_filed check
                return [{"1": 1}] if already_filed else []
            return []

        return _FakeConn(responder=responder, rowcount_for_update=rowcount_for_update)

    def test_forward_windows_only(self):
        """AC4: a window_end in the past is skipped even if SELECT returns it."""
        past_window = _make_window_row(
            window_start=date(2020, 1, 1),
            window_end=date(2020, 6, 1),  # in the past
        )
        conn = self._make_conn_with_windows([past_window])
        count = seed_prospective_ledger(conn, today=date.today())
        inserts = [s for s, _ in conn.statements
                   if s.strip().upper().startswith("INSERT") and TABLE_LEDGER in s]
        assert inserts == [], "Past-window must not be seeded"
        assert count == 0

    def test_forward_window_is_seeded(self):
        """A future window is inserted into brahma_prospective_ledger."""
        future_window = _make_window_row(signed_intensity=0.65)
        conn = self._make_conn_with_windows([future_window])
        count = seed_prospective_ledger(conn, today=date.today())
        inserts = [s for s, _ in conn.statements
                   if s.strip().upper().startswith("INSERT") and TABLE_LEDGER in s]
        # Two charts × 1 window (but the SELECT returns windows for each chart call).
        assert count > 0
        assert len(inserts) > 0

    def test_filing_method_is_explicit_filing_tool(self):
        """AC5: every INSERT must use 'explicit_filing_tool'."""
        future_window = _make_window_row(signed_intensity=0.5)
        conn = self._make_conn_with_windows([future_window])
        seed_prospective_ledger(conn, today=date.today())
        inserts = [s for s, _ in conn.statements
                   if s.strip().upper().startswith("INSERT") and TABLE_LEDGER in s]
        for sql in inserts:
            assert "explicit_filing_tool" in sql, (
                f"filing_method 'explicit_filing_tool' must appear in INSERT SQL: {sql[:120]}"
            )

    def test_claim_text_includes_event_class_and_intensity(self):
        """Claim text encodes event_class and signed_intensity."""
        claim = _build_claim("career_advancement", date(2026, 9, 1), date(2026, 12, 1), 0.73)
        assert "career_advancement" in claim
        assert "0.730" in claim

    def test_falsifier_references_event_class(self):
        """Falsifier text references the tracked event class."""
        falsifier = _build_falsifier("marriage")
        assert "marriage" in falsifier
        assert len(falsifier) > 10  # non-trivial

    def test_confidence_clamped_to_valid_range(self):
        """Confidence is in (0.0, 1.0) exclusive for any intensity value."""
        for intensity in (-5.0, 0.0, 0.5, 1.0, 5.0):
            conf = _build_confidence(intensity)
            assert 0.0 < conf < 1.0, f"confidence={conf} for intensity={intensity}"

    def test_confidence_increases_with_intensity(self):
        """Higher signed_intensity → higher confidence, capped at 0.9."""
        low = _build_confidence(0.0)
        high = _build_confidence(1.0)
        assert high > low
        assert _build_confidence(999.0) == 0.9

    def test_already_filed_window_is_skipped(self):
        """Idempotency: a window with an existing ledger row is not re-inserted."""
        future_window = _make_window_row(signed_intensity=0.6)
        conn = self._make_conn_with_windows([future_window], already_filed=True)
        count = seed_prospective_ledger(conn, today=date.today())
        inserts = [s for s, _ in conn.statements
                   if s.strip().upper().startswith("INSERT") and TABLE_LEDGER in s]
        assert inserts == [], "Already-filed window must not produce a second INSERT"
        assert count == 0

    def test_insert_includes_generator_class_engine(self):
        """generator_class = 'engine' must appear in every INSERT."""
        future_window = _make_window_row(signed_intensity=0.55)
        conn = self._make_conn_with_windows([future_window])
        seed_prospective_ledger(conn, today=date.today())
        inserts = [s for s, _ in conn.statements
                   if s.strip().upper().startswith("INSERT") and TABLE_LEDGER in s]
        for sql in inserts:
            assert "'engine'" in sql or "engine" in sql, (
                f"generator_class 'engine' must appear in INSERT: {sql[:120]}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 4. TestBuildReportShape
# ═══════════════════════════════════════════════════════════════════════════

class TestBuildReportShape:
    """Verify build_post_fit_report returns a dict with all required keys."""

    REQUIRED_KEYS = {
        "harness",
        "wave",
        "fitted_weights",
        "rows_stamped_empirically_calibrated",
        "prospective_rows_seeded",
        "fit_run_ids_used",
        "dataset_hash_linked",
    }

    def _make_empty_conn(self) -> _FakeConn:
        """Connection that returns empty results for everything."""
        return _FakeConn(responder=lambda sql, params: [])

    def test_report_has_all_required_keys(self):
        """AC1: build_post_fit_report returns dict with all required keys."""
        report = build_post_fit_report(self._make_empty_conn())
        missing = self.REQUIRED_KEYS - set(report.keys())
        assert not missing, f"Report missing keys: {missing}"

    def test_harness_field_value(self):
        report = build_post_fit_report(self._make_empty_conn())
        assert report["harness"] == "w45_post_fit_rebuild"

    def test_wave_field_value(self):
        report = build_post_fit_report(self._make_empty_conn())
        assert report["wave"] == "W4.5"

    def test_fitted_weights_is_dict_with_10_keys(self):
        report = build_post_fit_report(self._make_empty_conn())
        fw = report["fitted_weights"]
        assert isinstance(fw, dict)
        assert set(fw.keys()) == ADMITTED_MECHANISM_IDS

    def test_rows_stamped_is_integer(self):
        report = build_post_fit_report(self._make_empty_conn())
        assert isinstance(report["rows_stamped_empirically_calibrated"], int)

    def test_prospective_rows_seeded_is_integer(self):
        report = build_post_fit_report(self._make_empty_conn())
        assert isinstance(report["prospective_rows_seeded"], int)

    def test_fit_run_ids_used_is_list(self):
        report = build_post_fit_report(self._make_empty_conn())
        assert isinstance(report["fit_run_ids_used"], list)

    def test_report_callable_as_function(self):
        """AC1: build_post_fit_report(conn) is callable and returns a dict."""
        import inspect as _inspect
        assert callable(build_post_fit_report)
        sig = _inspect.signature(build_post_fit_report)
        params = list(sig.parameters.keys())
        assert "conn" in params


# ═══════════════════════════════════════════════════════════════════════════
# 5. TestI2ImportGuard
# ═══════════════════════════════════════════════════════════════════════════

class TestI2ImportGuard:
    """AC7: w45_post_fit_rebuild must not import from the three protected services."""

    FORBIDDEN_PREFIXES = (
        "services.gochara_grammar",
        "services.gochara_intensity",
        "services.ka_gochara_sweep",
    )

    def _source_excluding_docstring(self) -> str:
        source = inspect.getsource(mod)
        doc = mod.__doc__
        if doc and doc in source:
            return source.replace(doc, "", 1)
        return source

    def test_no_gochara_grammar_import(self):
        source = self._source_excluding_docstring()
        assert "services.gochara_grammar" not in source, (
            "w45_post_fit_rebuild must not import from services.gochara_grammar (I2)"
        )

    def test_no_gochara_intensity_import(self):
        source = self._source_excluding_docstring()
        assert "services.gochara_intensity" not in source, (
            "w45_post_fit_rebuild must not import from services.gochara_intensity (I2)"
        )

    def test_no_ka_gochara_sweep_import(self):
        source = self._source_excluding_docstring()
        assert "services.ka_gochara_sweep" not in source, (
            "w45_post_fit_rebuild must not import from services.ka_gochara_sweep (I2)"
        )

    def test_module_imports_are_clean(self):
        """Verify the module's actual sys.modules after import."""
        for prefix in self.FORBIDDEN_PREFIXES:
            for mod_name in sys.modules:
                assert not mod_name.startswith(prefix), (
                    f"Forbidden module {mod_name!r} found in sys.modules after import (I2)"
                )


# ═══════════════════════════════════════════════════════════════════════════
# 6. TestHonestFallback
# ═══════════════════════════════════════════════════════════════════════════

class TestHonestFallback:
    """AC6: when gochara_v3_calibration has no rows, honest 0.0 weights and 0 stamped."""

    def test_empty_calibration_table_yields_zero_weights(self):
        """I4: all weights are 0.0 when table is empty."""
        conn = _FakeConn(responder=lambda sql, params: [])
        weights, fit_run_ids, dataset_hash = load_fitted_weights(conn)
        assert all(v == 0.0 for v in weights.values()), (
            "All weights must be 0.0 when gochara_v3_calibration has no rows"
        )
        assert fit_run_ids == [], "No fit_run_ids when table is empty"
        assert dataset_hash is None

    def test_empty_calibration_skips_stamping(self):
        """§N.8: rows_stamped = 0 when no fitted weights exist."""
        conn = _FakeConn(responder=lambda sql, params: [])
        count = stamp_empirically_calibrated(conn, fit_run_ids=[])
        assert count == 0
        updates = [s for s, _ in conn.statements if s.strip().upper().startswith("UPDATE")]
        assert updates == [], "No UPDATE must be issued when fit_run_ids is empty (§N.8)"

    def test_full_report_with_empty_calibration(self):
        """build_post_fit_report with empty DB: all weights 0.0, rows_stamped=0."""
        conn = _FakeConn(responder=lambda sql, params: [])
        report = build_post_fit_report(conn)
        assert all(v == 0.0 for v in report["fitted_weights"].values())
        assert report["rows_stamped_empirically_calibrated"] == 0
        assert report["fit_run_ids_used"] == []
        assert report["dataset_hash_linked"] is None

    def test_no_fabrication_on_missing_keys(self):
        """I4: no weight is ever invented — missing always maps to 0.0, not a proxy."""
        conn = _FakeConn(responder=lambda sql, params: [])
        weights, _, _ = load_fitted_weights(conn)
        for tk in ADMITTED_MECHANISM_IDS:
            assert tk in weights
            assert weights[tk] == 0.0

    def test_n8_gate_is_inside_stamp_function_not_caller(self):
        """§N.8 gate lives in stamp_empirically_calibrated, not only at call site.

        Calling stamp with an empty fit_run_ids list must return 0 and issue
        no UPDATE regardless of how it is invoked.
        """
        conn = _FakeConn(rowcount_for_update=999)  # would return 999 if UPDATE ran
        result = stamp_empirically_calibrated(conn, fit_run_ids=[])
        assert result == 0
        updates = [s for s, _ in conn.statements if s.strip().upper().startswith("UPDATE")]
        assert not updates, "§N.8: UPDATE must not run when fit_run_ids is empty"
