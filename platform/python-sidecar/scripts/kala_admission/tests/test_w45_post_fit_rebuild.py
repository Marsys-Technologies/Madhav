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
    ALL_CLAIM_SHAPES,
    CHART_IDS,
    CLAIM_SHAPE_CHAIN,
    CLAIM_SHAPE_INTERVAL,
    CLAIM_SHAPE_POINT,
    FILED_BY,
    FORMULA_VERSION,
    MODEL_TAG,
    NATIVE_CHART_ID,
    ABHINANDAN_CHART_ID,
    SOURCE_CITATION,
    STATE_EMPIRICALLY_CALIBRATED,
    STATE_STRUCTURAL_PRIOR,
    TABLE_CALIBRATION,
    TABLE_EVENT_ONTOLOGY,
    TABLE_LEDGER,
    TABLE_WINDOWS,
    _build_claim,
    _build_confidence,
    _build_falsifier,
    _fetch_event_class_claim_shape,
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
        weights, _, _, _ = load_fitted_weights(conn)
        assert set(weights.keys()) == ADMITTED_MECHANISM_IDS

    def test_fitted_weight_loaded_correctly(self):
        """A row with weight_value=0.123 is loaded as 0.123."""
        target_key = "w21_av_gating"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [_make_calibration_row(target_key, 0.123)]
            return []

        conn = _FakeConn(responder=responder)
        weights, _, _, _ = load_fitted_weights(conn)
        assert abs(weights[target_key] - 0.123) < 1e-9

    def test_missing_toggle_key_falls_back_to_zero(self):
        """I4: a toggle_key absent from gochara_v3_calibration → 0.0."""
        conn = _FakeConn(responder=lambda sql, params: [])
        weights, _, _, _ = load_fitted_weights(conn)
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
        weights, _, _, _ = load_fitted_weights(conn)
        assert weights[target_key] == 0.0, "Negative weight must be clamped to 0.0"

    def test_fit_run_ids_collected(self):
        """fit_run_ids_used contains the fit_run_id from the row."""
        target_key = "w23_tara_bala"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [_make_calibration_row(target_key, 0.05, fit_run_id="run-xyz")]
            return []

        conn = _FakeConn(responder=responder)
        _, fit_run_ids, _, _ = load_fitted_weights(conn)
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
        _, _, dataset_hash, _ = load_fitted_weights(conn)
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
        weights, _, _, _ = load_fitted_weights(conn)
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


def _make_conn_with_windows(
    windows: list[dict],
    already_filed: bool = False,
    rowcount_for_update: int = 0,
    ontology_shapes: Optional[dict[str, Optional[str]]] = None,
    default_ontology_shape: Optional[str] = CLAIM_SHAPE_INTERVAL,
    fail_insert_for_event_classes: Optional[set] = None,
) -> _FakeConn:
    """Build a fake connection that returns `windows` for SELECT and
    optionally returns a row for the 'already filed' check.

    ontology_shapes: per-event_class temporal_shape override for the
    brahma_event_ontology lookup (defaults to `default_ontology_shape`
    for any event_class not explicitly listed; None omits the row
    entirely, simulating "no ontology row found").
    fail_insert_for_event_classes: event_classes whose INSERT into
    TABLE_LEDGER should raise, simulating a DB-level rejection (used to
    test the per-row SAVEPOINT isolation).
    """
    ontology_shapes = ontology_shapes or {}
    fail_insert_for_event_classes = fail_insert_for_event_classes or set()

    def responder(sql, params):
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT") and TABLE_WINDOWS in sql:
            return windows
        if sql_upper.startswith("SELECT") and TABLE_EVENT_ONTOLOGY in sql:
            event_class = params[0] if params else None
            shape = ontology_shapes.get(event_class, default_ontology_shape)
            if shape is None:
                return []
            return [{"temporal_shape": shape}]
        if sql_upper.startswith("SELECT") and TABLE_LEDGER in sql:
            # _window_already_filed check
            return [{"1": 1}] if already_filed else []
        if sql_upper.startswith("INSERT") and TABLE_LEDGER in sql:
            event_class = params[2] if params else None
            if event_class in fail_insert_for_event_classes:
                raise RuntimeError(
                    f"simulated INSERT rejection for event_class={event_class}"
                )
            return []
        return []

    return _FakeConn(responder=responder, rowcount_for_update=rowcount_for_update)


# ═══════════════════════════════════════════════════════════════════════════
# 3. TestProspectiveLedgerSeeding
# ═══════════════════════════════════════════════════════════════════════════

class TestProspectiveLedgerSeeding:
    """Verify forward-only AC4, INSERT shape AC5, claim/falsifier text."""

    _make_conn_with_windows = staticmethod(_make_conn_with_windows)

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
# 3a. TestClaimShapeDerivation — PARIṢKĀRA MR-48 regression suite (item 1)
# ═══════════════════════════════════════════════════════════════════════════

class TestClaimShapeDerivation:
    """MR-48: Stage C previously hardcoded claim_shape="interval" for EVERY
    row. These tests prove claim_shape is now honestly derived, per row,
    from a LIVE brahma_event_ontology.temporal_shape lookup — never a bare
    literal, never a hand-typed class list (PK-R-7(iv), same discipline as
    the sibling MR-47/PK-R-10 fix).
    """

    _make_conn_with_windows = staticmethod(_make_conn_with_windows)

    def _claim_shape_param_for(self, conn: _FakeConn, event_class: str) -> str:
        inserts = [
            p for s, p in conn.statements
            if s.strip().upper().startswith("INSERT") and TABLE_LEDGER in s
            and p and p[2] == event_class
        ]
        assert inserts, f"No INSERT recorded for event_class={event_class}"
        # INSERT params order: chart_id, claim, event_class, claim_shape, ...
        return inserts[0][3]

    def test_claim_shape_derived_as_interval(self):
        """An event_class whose ontology temporal_shape='interval' seeds
        claim_shape='interval' — the honest, correctly-derived value (which
        happens to equal the OLD hardcoded default for this one case)."""
        window = _make_window_row(event_class="psychological_arc")
        conn = self._make_conn_with_windows(
            [window],
            ontology_shapes={"psychological_arc": CLAIM_SHAPE_INTERVAL},
        )
        seed_prospective_ledger(conn, today=date.today())
        assert self._claim_shape_param_for(conn, "psychological_arc") == CLAIM_SHAPE_INTERVAL

    def test_claim_shape_derived_as_chain_not_hardcoded_interval(self):
        """THE regression test: an event_class whose ontology
        temporal_shape='chain' (e.g. education_milestone — the exact class
        that tripped the live DR-13/DIS.026 trigger 2026-08-12) must seed
        claim_shape='chain', NOT the old hardcoded 'interval' literal."""
        window = _make_window_row(event_class="education_milestone")
        conn = self._make_conn_with_windows(
            [window],
            ontology_shapes={"education_milestone": CLAIM_SHAPE_CHAIN},
        )
        seed_prospective_ledger(conn, today=date.today())
        assert self._claim_shape_param_for(conn, "education_milestone") == CLAIM_SHAPE_CHAIN, (
            "claim_shape must be derived from brahma_event_ontology, never "
            "hardcoded 'interval' — this is the exact MR-48 defect"
        )

    def test_claim_shape_derived_as_point(self):
        """An event_class whose ontology temporal_shape='point' seeds
        claim_shape='point'."""
        window = _make_window_row(event_class="marriage")
        conn = self._make_conn_with_windows(
            [window],
            ontology_shapes={"marriage": CLAIM_SHAPE_POINT},
        )
        seed_prospective_ledger(conn, today=date.today())
        assert self._claim_shape_param_for(conn, "marriage") == CLAIM_SHAPE_POINT

    def test_ontology_query_issued_against_event_class(self):
        """The ontology lookup is a live, parameterized query keyed on
        event_class — never a hand-typed class-name switch/dict literal in
        this module (PK-R-7(iv))."""
        window = _make_window_row(event_class="wealth_shift")
        conn = self._make_conn_with_windows(
            [window],
            ontology_shapes={"wealth_shift": CLAIM_SHAPE_INTERVAL},
        )
        seed_prospective_ledger(conn, today=date.today())
        ontology_queries = [
            (s, p) for s, p in conn.statements
            if s.strip().upper().startswith("SELECT") and TABLE_EVENT_ONTOLOGY in s
        ]
        assert ontology_queries, "seed_prospective_ledger must query brahma_event_ontology"
        assert any(p and p[0] == "wealth_shift" for _, p in ontology_queries)

    def test_missing_ontology_row_skips_row_honestly(self):
        """I4: no brahma_event_ontology row for event_class → the row is
        skipped (never inserted with a fabricated/guessed claim_shape)."""
        window = _make_window_row(event_class="no_ontology_row_class")
        conn = self._make_conn_with_windows(
            [window],
            ontology_shapes={"no_ontology_row_class": None},
        )
        count = seed_prospective_ledger(conn, today=date.today())
        inserts = [s for s, _ in conn.statements
                   if s.strip().upper().startswith("INSERT") and TABLE_LEDGER in s]
        assert inserts == [], "A row with no resolvable claim_shape must never be inserted"
        assert count == 0

    def test_ontology_query_error_skips_row_honestly(self):
        """A DB error on the ontology lookup degrades to an honest skip, not
        a crash and not a fabricated claim_shape."""
        window = _make_window_row(event_class="db_error_class")

        def responder(sql, params):
            su = sql.strip().upper()
            if su.startswith("SELECT") and TABLE_WINDOWS in sql:
                return [window]
            if su.startswith("SELECT") and TABLE_EVENT_ONTOLOGY in sql:
                raise RuntimeError("simulated ontology DB error")
            if su.startswith("SELECT") and TABLE_LEDGER in sql:
                return []
            return []

        conn = _FakeConn(responder=responder)
        count = seed_prospective_ledger(conn, today=date.today())
        inserts = [s for s, _ in conn.statements
                   if s.strip().upper().startswith("INSERT") and TABLE_LEDGER in s]
        assert inserts == [], "An ontology-query error must never fall back to a guessed shape"
        assert count == 0

    def test_unrecognized_ontology_shape_skips_row_honestly(self):
        """A stored temporal_shape outside {'point','interval','chain'} is
        treated as unclassifiable (I4), not silently coerced."""
        assert _fetch_event_class_claim_shape(
            _FakeConn(responder=lambda sql, params: (
                [{"temporal_shape": "not_a_real_shape"}]
                if TABLE_EVENT_ONTOLOGY in sql else []
            )),
            "weird_class",
        ) is None

    def test_fetch_event_class_claim_shape_returns_known_vocabulary_only(self):
        """The helper never returns a value outside ALL_CLAIM_SHAPES."""
        for shape in (CLAIM_SHAPE_POINT, CLAIM_SHAPE_INTERVAL, CLAIM_SHAPE_CHAIN):
            conn = _FakeConn(responder=lambda sql, params, _shape=shape: (
                [{"temporal_shape": _shape}] if TABLE_EVENT_ONTOLOGY in sql else []
            ))
            result = _fetch_event_class_claim_shape(conn, "any_class")
            assert result in ALL_CLAIM_SHAPES
            assert result == shape


# ═══════════════════════════════════════════════════════════════════════════
# 3b. TestStageCSavepointIsolation — PARIṢKĀRA MR-48 regression suite (item 2)
# ═══════════════════════════════════════════════════════════════════════════

class TestStageCSavepointIsolation:
    """MR-48: Stage C previously issued all of one chart's INSERTs on a
    single shared transaction/cursor with no per-row isolation — one
    legitimate rejection cascaded into collateral failures for every
    subsequent, otherwise-valid row (confirmed live 2026-08-12: one
    education_milestone shape-mismatch rejection collateral-damaged 8 valid
    psychological_arc inserts). These tests prove each row's INSERT is now
    wrapped in its own SAVEPOINT / RELEASE SAVEPOINT (ROLLBACK TO SAVEPOINT
    on failure) so one row's rejection cannot cascade.
    """

    _make_conn_with_windows = staticmethod(_make_conn_with_windows)

    @staticmethod
    def _statement_kinds(conn: _FakeConn) -> list[str]:
        kinds = []
        for sql, _ in conn.statements:
            su = sql.strip().upper()
            if su.startswith("SAVEPOINT"):
                kinds.append("SAVEPOINT")
            elif su.startswith("RELEASE SAVEPOINT"):
                kinds.append("RELEASE")
            elif su.startswith("ROLLBACK TO SAVEPOINT"):
                kinds.append("ROLLBACK")
            elif su.startswith("INSERT") and TABLE_LEDGER in sql:
                kinds.append("INSERT")
        return kinds

    def test_savepoint_and_release_bracket_a_successful_insert(self):
        """A successful row: SAVEPOINT, INSERT, RELEASE SAVEPOINT, in order."""
        window = _make_window_row(event_class="career_advancement")
        conn = self._make_conn_with_windows(
            [window], ontology_shapes={"career_advancement": CLAIM_SHAPE_INTERVAL}
        )
        seed_prospective_ledger(conn, today=date.today())
        kinds = self._statement_kinds(conn)
        # At least one full SAVEPOINT -> INSERT -> RELEASE triple must appear.
        assert "SAVEPOINT" in kinds and "INSERT" in kinds and "RELEASE" in kinds
        sp_idx = kinds.index("SAVEPOINT")
        ins_idx = kinds.index("INSERT")
        rel_idx = kinds.index("RELEASE")
        assert sp_idx < ins_idx < rel_idx, f"Expected SAVEPOINT < INSERT < RELEASE, got {kinds}"
        assert "ROLLBACK" not in kinds, "No rollback expected on a successful insert"

    def test_rejected_row_issues_rollback_to_savepoint(self):
        """A row whose INSERT fails is rolled back to its own savepoint, not
        left to abort the whole connection."""
        window = _make_window_row(event_class="education_milestone")
        conn = self._make_conn_with_windows(
            [window],
            ontology_shapes={"education_milestone": CLAIM_SHAPE_CHAIN},
            fail_insert_for_event_classes={"education_milestone"},
        )
        count = seed_prospective_ledger(conn, today=date.today())
        kinds = self._statement_kinds(conn)
        assert "ROLLBACK" in kinds, f"Expected a ROLLBACK TO SAVEPOINT, got {kinds}"
        assert count == 0

    def test_one_rejected_row_does_not_block_a_later_valid_row(self):
        """THE regression test: a rejected row (chain-mismatch, simulating
        the live education_milestone trigger rejection) must NOT prevent a
        later, unrelated, genuinely-valid row (psychological_arc) in the
        SAME chart's batch from being inserted successfully — the exact
        collateral-cascade defect confirmed live 2026-08-12 (8 valid rows
        lost to one rejection)."""
        rejected_window = _make_window_row(
            event_class="education_milestone", signed_intensity=0.9,
        )
        valid_window = _make_window_row(
            event_class="psychological_arc", signed_intensity=0.5,
        )
        conn = self._make_conn_with_windows(
            [rejected_window, valid_window],
            ontology_shapes={
                "education_milestone": CLAIM_SHAPE_CHAIN,
                "psychological_arc": CLAIM_SHAPE_INTERVAL,
            },
            fail_insert_for_event_classes={"education_milestone"},
        )
        count = seed_prospective_ledger(conn, today=date.today())

        successful_inserts = [
            p for s, p in conn.statements
            if s.strip().upper().startswith("INSERT") and TABLE_LEDGER in s
        ]
        # Both charts iterate the same two windows; every attempted INSERT
        # for psychological_arc must have actually gone through (the fake
        # only raises for education_milestone), and none of them are lost
        # to cascading transaction-abort behavior.
        psych_inserts = [p for p in successful_inserts if p[2] == "psychological_arc"]
        assert len(psych_inserts) == len(CHART_IDS), (
            f"Expected one successful psychological_arc insert per chart "
            f"({len(CHART_IDS)}), got {len(psych_inserts)} — the education_milestone "
            f"rejection must not cascade"
        )
        # count only reflects genuinely successful inserts.
        assert count == len(CHART_IDS)

        # Verify ordering: for each chart, a ROLLBACK for the failed row is
        # followed later by a fresh SAVEPOINT/INSERT/RELEASE triple for the
        # valid row — proving the connection remained usable afterward.
        kinds = self._statement_kinds(conn)
        assert kinds.count("ROLLBACK") == len(CHART_IDS)
        assert kinds.count("RELEASE") == len(CHART_IDS)
        assert kinds.count("INSERT") == 2 * len(CHART_IDS)

    def test_rejected_row_is_logged_distinguishably(self, caplog):
        """The warning for a rejected row names the event_class and
        claim_shape actually used, and explicitly notes SAVEPOINT isolation
        — distinguishable from a generic 'INSERT failed', unlike the
        original defect where a collateral cascade failure was logged
        identically to the real one."""
        import logging
        window = _make_window_row(event_class="education_milestone")
        conn = self._make_conn_with_windows(
            [window],
            ontology_shapes={"education_milestone": CLAIM_SHAPE_CHAIN},
            fail_insert_for_event_classes={"education_milestone"},
        )
        with caplog.at_level(logging.WARNING, logger="kala_admission.w45_post_fit_rebuild"):
            seed_prospective_ledger(conn, today=date.today())
        messages = [r.getMessage() for r in caplog.records]
        joined = "\n".join(messages)
        assert "education_milestone" in joined
        assert "chain" in joined
        assert "SAVEPOINT" in joined


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
        "earned_fit_run_ids_used",
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
        weights, fit_run_ids, dataset_hash, earned_fit_run_ids = load_fitted_weights(conn)
        assert all(v == 0.0 for v in weights.values()), (
            "All weights must be 0.0 when gochara_v3_calibration has no rows"
        )
        assert fit_run_ids == [], "No fit_run_ids when table is empty"
        assert earned_fit_run_ids == [], "No earned_fit_run_ids when table is empty"
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
        assert report["earned_fit_run_ids_used"] == []
        assert report["dataset_hash_linked"] is None

    def test_no_fabrication_on_missing_keys(self):
        """I4: no weight is ever invented — missing always maps to 0.0, not a proxy."""
        conn = _FakeConn(responder=lambda sql, params: [])
        weights, _, _, _ = load_fitted_weights(conn)
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


# ═══════════════════════════════════════════════════════════════════════════
# 7. TestEarnedSignalGate — PARIṢKĀRA MR-37 regression suite
# ═══════════════════════════════════════════════════════════════════════════

class TestEarnedSignalGate:
    """PARIṢKĀRA MR-37: the §N.8 gate must test EARNED signal (non-zero weight
    from an engine-wired mechanism), not row existence. These tests reproduce
    the exact proven exploit — a gochara_v3_calibration row exists for every
    admitted toggle_key with weight_value=0.0 (today's REAL production state:
    all 10 mechanisms are mechanism_not_wired, per MECHANISM_ENGINE_WIRED) —
    and assert the fix refuses to stamp anything, where the pre-fix gate
    (checking `fit_run_ids` row-existence alone) would have stamped.
    """

    def _all_zero_not_wired_responder(self, fit_run_id: str = "run-exploit"):
        """Mimics the real production exploit fixture: every admitted
        toggle_key has a gochara_v3_calibration row (fit_run_id present,
        weight_value=0.0) — the exact shape a mechanism_not_wired W4.4 fit
        writes. Row EXISTS; signal is NOT earned.
        """
        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params:
                return [_make_calibration_row(params[0], 0.0, fit_run_id=fit_run_id)]
            return []
        return responder

    def test_exploit_fixture_produces_nonempty_fit_run_ids(self):
        """Sanity check: the exploit fixture DOES produce row-existence
        (fit_run_ids non-empty) — proving the old row-existence-only gate
        really would have passed this fixture.
        """
        conn = _FakeConn(responder=self._all_zero_not_wired_responder())
        _, fit_run_ids, _, _ = load_fitted_weights(conn)
        assert fit_run_ids != [], (
            "Exploit fixture must produce non-empty fit_run_ids (row exists) — "
            "otherwise this isn't testing the row-existence-vs-earned-signal gap"
        )

    def test_exploit_fixture_produces_empty_earned_fit_run_ids(self):
        """The fix: the same fixture must NOT count as earned signal — all
        weights are 0.0 (mechanism_not_wired's honest zero-delta), so
        earned_fit_run_ids must be empty despite fit_run_ids being non-empty.
        """
        conn = _FakeConn(responder=self._all_zero_not_wired_responder())
        _, fit_run_ids, _, earned_fit_run_ids = load_fitted_weights(conn)
        assert fit_run_ids != [], "precondition: row-existence must be non-empty"
        assert earned_fit_run_ids == [], (
            "MR-37: an all-zero fit (mechanism_not_wired) must NOT be earned "
            "signal, even though gochara_v3_calibration rows exist for it"
        )

    def test_exploit_end_to_end_refused_via_build_post_fit_report(self):
        """THE regression test: the exact proven exploit, run through the full
        build_post_fit_report path. Pre-fix, this fixture (120 rows' worth of
        row-existing, all-zero, all-not-wired fit — the real production shape
        that had already dishonestly stamped 107 staging rows once) would
        have stamped every eligible structural_prior row
        'empirically_calibrated'. Post-fix, it must stamp ZERO.
        """
        conn = _FakeConn(
            responder=self._all_zero_not_wired_responder(),
            rowcount_for_update=120,  # would return 120 if the UPDATE ran
        )
        report = build_post_fit_report(conn)
        assert report["rows_stamped_empirically_calibrated"] == 0, (
            "MR-37 REGRESSION: the proven exploit (row exists, weight=0.0, "
            "mechanism not wired) must be refused — stamping 0 rows, not 120"
        )
        updates = [s for s, _ in conn.statements if s.strip().upper().startswith("UPDATE")]
        assert updates == [], "No UPDATE may be issued for an unearned fit"

    def test_wired_mechanism_with_nonzero_weight_is_earned(self):
        """Positive case: a toggle_key that IS engine-wired AND has a
        genuinely non-zero weight must count as earned signal — the gate
        must not become impossible to pass, only impossible to fake.
        """
        target_key = "w21_av_gating"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [_make_calibration_row(target_key, 0.42, fit_run_id="run-earned")]
            return []

        conn = _FakeConn(responder=responder)
        with patch.dict(mod.MECHANISM_ENGINE_WIRED, {target_key: True}):
            _, _, _, earned_fit_run_ids = load_fitted_weights(conn)
        assert "run-earned" in earned_fit_run_ids, (
            "A wired mechanism with non-zero weight must be earned signal"
        )

    def test_wired_mechanism_with_zero_weight_is_not_earned(self):
        """Weight=0.0 is never earned signal, even for a wired mechanism —
        weight and wiring are both required, not either/or.
        """
        target_key = "w21_av_gating"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [_make_calibration_row(target_key, 0.0, fit_run_id="run-zero")]
            return []

        conn = _FakeConn(responder=responder)
        with patch.dict(mod.MECHANISM_ENGINE_WIRED, {target_key: True}):
            _, _, _, earned_fit_run_ids = load_fitted_weights(conn)
        assert earned_fit_run_ids == [], "Zero weight is never earned, wired or not"

    def test_unwired_mechanism_with_nonzero_weight_is_not_earned(self):
        """A non-zero weight for a mechanism NOT wired into the engine is
        never earned signal — guards against a future drift where the fit
        computation stops honestly zeroing mechanism_not_wired deltas.
        """
        target_key = "w22_moorti_nirnaya"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [_make_calibration_row(target_key, 0.99, fit_run_id="run-drift")]
            return []

        conn = _FakeConn(responder=responder)
        with patch.dict(mod.MECHANISM_ENGINE_WIRED, {target_key: False}):
            _, _, _, earned_fit_run_ids = load_fitted_weights(conn)
        assert earned_fit_run_ids == [], (
            "A non-zero weight for an unwired mechanism must still be refused"
        )

    def test_unknown_toggle_key_defaults_wired_true(self):
        """A toggle_key absent from MECHANISM_ENGINE_WIRED defaults wired=True
        (matches w44's own `.get(key, True)` convention) — only mechanisms
        POSITIVELY confirmed dormant are excluded, never an unknown one.
        """
        target_key = "w23_tara_bala"

        def responder(sql, params):
            if TABLE_CALIBRATION in sql and params and params[0] == target_key:
                return [_make_calibration_row(target_key, 0.5, fit_run_id="run-default")]
            return []

        conn = _FakeConn(responder=responder)
        with patch.dict(mod.MECHANISM_ENGINE_WIRED, {}, clear=False):
            # Remove the key entirely to simulate "unknown to the registry".
            saved = mod.MECHANISM_ENGINE_WIRED.pop(target_key, None)
            try:
                _, _, _, earned_fit_run_ids = load_fitted_weights(conn)
            finally:
                if saved is not None:
                    mod.MECHANISM_ENGINE_WIRED[target_key] = saved
        assert "run-default" in earned_fit_run_ids, (
            "An unknown toggle_key must default to wired=True, not be silently excluded"
        )
