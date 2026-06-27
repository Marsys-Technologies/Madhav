"""
test_a9_warnings.py — Agent A9 remediation tests
==================================================
Covers fixes W1–W5:
  W1: bo_upaya chart_typology derived from element distribution, not hardcoded
  W2: ka_vighnakara swisseph unavailability produces explicit signal, not silent score=0 rows
  W3: bo_samvada dead DDL branch removed; live VIEW path intact
  W4: mi_pramana stub functions explicitly marked
  W5: mi_darshana embeddings substep emits [EXTERNAL_COMPUTATION_REQUIRED] marker

All tests are pure unit tests: no real DB connections, no chart data operations.
"""
from __future__ import annotations

import collections
import importlib.util
import sys
import time
import types
from datetime import date
from unittest.mock import MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# Shared loader helpers
# ─────────────────────────────────────────────────────────────────────────────

_WORKTREE = (
    "/Users/Dev/Vibe-Coding/Apps/Madhav/"
    "platform/python-sidecar/pipeline/orchestrator/writers/"
)

_PKG = "pipeline.orchestrator.writers"

FakeWriterResult = collections.namedtuple(
    "WriterResult", ["asset_id", "rows_inserted", "notes", "duration_seconds"],
    defaults=[None, 0, None, 0.0],
)


_WRITERS_DIR = "/Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar/pipeline/orchestrator/writers"


def _ensure_writers_stub(extra_attrs: dict | None = None):
    """
    Ensure a pipeline.orchestrator.writers stub is in sys.modules.
    Rebuilds it fresh each call so tests don't bleed state between writer modules.
    Returns the stub.

    The stub always includes ``__path__`` pointing at the real writers directory
    so that subsequent tests can still do sub-module imports like
    ``from pipeline.orchestrator.writers.ph_muhurta import …`` without
    hitting "not a package" errors.
    """
    existing = sys.modules.get(_PKG)
    if existing is not None and hasattr(existing, "__file__"):
        # Real package is loaded — patch it non-destructively; leave __path__ intact.
        stub = existing
        if extra_attrs:
            for k, v in extra_attrs.items():
                setattr(stub, k, v)
        return stub

    stub = types.ModuleType(_PKG)
    stub.WriterBase = object
    stub.ContextSpec = object
    stub.WriterResult = FakeWriterResult
    stub.SubStep = MagicMock
    stub.register = lambda x: (lambda cls: cls)
    # Must set __path__ so Python can still resolve sub-module imports after this
    # stub is installed.  Without it, 'from pipeline.orchestrator.writers.X import …'
    # raises "not a package" in any test that runs after A9.
    stub.__path__ = [_WRITERS_DIR]
    stub.__package__ = _PKG
    if extra_attrs:
        for k, v in extra_attrs.items():
            setattr(stub, k, v)
    sys.modules[_PKG] = stub
    return stub


def _ensure_psycopg_stub():
    if "psycopg" not in sys.modules:
        psycopg_stub = types.ModuleType("psycopg")
        rows_stub = types.ModuleType("psycopg.rows")
        rows_stub.tuple_row = None
        rows_stub.dict_row = None
        psycopg_stub.rows = rows_stub
        sys.modules["psycopg"] = psycopg_stub
        sys.modules["psycopg.rows"] = rows_stub


def _load_module(filename: str) -> types.ModuleType:
    """Load a writer module by filename, fresh each call.

    Uses the stub's no-op ``register`` function while loading the module so
    that re-loading a writer that was already registered by another test file
    does not raise a duplicate-registration ValueError.
    """
    stub = _ensure_writers_stub()
    _ensure_psycopg_stub()
    key = f"{_PKG}.{filename.replace('.py', '')}"
    sys.modules.pop(key, None)

    path = _WORKTREE + filename
    spec = importlib.util.spec_from_file_location(key, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _PKG
    sys.modules[key] = mod

    # Temporarily replace the writers-package `register` with a no-op so that
    # @register(…) decorators inside the loaded module don't fire on the real
    # _REGISTRY — which would raise ValueError if the writer was already
    # registered by a prior test file that imported it via the real package.
    _noop_register = lambda asset_id: (lambda cls: cls)
    original_register = getattr(stub, "register", _noop_register)
    stub.register = _noop_register
    try:
        spec.loader.exec_module(mod)
    finally:
        stub.register = original_register

    return mod


# ─────────────────────────────────────────────────────────────────────────────
# W1 — bo_upaya: chart_typology derived, not hardcoded "balanced"
# ─────────────────────────────────────────────────────────────────────────────

class TestW1ChartTypology:
    """W1: _fetch_chart_typology derives typology from element distribution."""

    def _load(self):
        _ensure_writers_stub()
        return _load_module("bo_upaya.py")

    def _conn_returning(self, rows):
        conn = MagicMock()
        result = MagicMock()
        result.fetchall.return_value = rows
        conn.execute.return_value = result
        return conn

    def test_fire_dominant_returns_pitta(self):
        mod = self._load()
        rows = [("fire", 5), ("earth", 2), ("air", 1), ("water", 1)]
        conn = self._conn_returning(rows)
        result = mod._fetch_chart_typology(conn, "chart-123", "lahiri_chitrapaksha")
        assert result == "pitta", f"Expected 'pitta', got '{result}'"

    def test_earth_dominant_returns_kapha_stable(self):
        mod = self._load()
        rows = [("earth", 6), ("fire", 2), ("air", 1)]
        conn = self._conn_returning(rows)
        result = mod._fetch_chart_typology(conn, "chart-123", "lahiri_chitrapaksha")
        assert result == "kapha_stable", f"Expected 'kapha_stable', got '{result}'"

    def test_air_dominant_returns_vata(self):
        mod = self._load()
        rows = [("air", 5), ("water", 2), ("fire", 1), ("earth", 1)]
        conn = self._conn_returning(rows)
        result = mod._fetch_chart_typology(conn, "chart-123", "lahiri_chitrapaksha")
        assert result == "vata", f"Expected 'vata', got '{result}'"

    def test_water_dominant_returns_kapha_fluid(self):
        mod = self._load()
        rows = [("water", 4), ("fire", 3), ("earth", 1), ("air", 1)]
        conn = self._conn_returning(rows)
        result = mod._fetch_chart_typology(conn, "chart-123", "lahiri_chitrapaksha")
        assert result == "kapha_fluid", f"Expected 'kapha_fluid', got '{result}'"

    def test_tie_returns_balanced(self):
        mod = self._load()
        rows = [("fire", 4), ("earth", 4), ("air", 1)]
        conn = self._conn_returning(rows)
        result = mod._fetch_chart_typology(conn, "chart-123", "lahiri_chitrapaksha")
        assert result == "balanced", f"Expected 'balanced' on tie, got '{result}'"

    def test_empty_rows_returns_balanced(self):
        mod = self._load()
        conn = self._conn_returning([])
        result = mod._fetch_chart_typology(conn, "chart-123", "lahiri_chitrapaksha")
        assert result == "balanced", f"Expected 'balanced' on empty, got '{result}'"

    def test_typology_not_hardcoded_balanced_for_fire_chart(self):
        """W1 core: typology differs based on chart data (not always 'balanced')."""
        mod = self._load()
        fire_rows = [("fire", 7), ("earth", 1), ("air", 1)]
        conn = self._conn_returning(fire_rows)
        result = mod._fetch_chart_typology(conn, "chart-123", "lahiri_chitrapaksha")
        assert result != "balanced", (
            "For an all-fire chart, typology should NOT be 'balanced'; "
            f"got '{result}'. Hardcoded value was not replaced."
        )


# ─────────────────────────────────────────────────────────────────────────────
# W2 — ka_vighnakara: swisseph unavailability → explicit result, not silent zeros
# ─────────────────────────────────────────────────────────────────────────────

class TestW2SwissephUnavailable:
    """W2: swisseph unavailability produces explicit signal, not silent score=0 rows."""

    def _load(self):
        _ensure_writers_stub()
        return _load_module("ka_vighnakara.py")

    def test_swisseph_unavailable_returns_zero_rows_not_silent_stubs(self):
        """W2: when swisseph cannot be imported, writer returns 0 rows with explicit notes."""
        mod = self._load()

        ctx = MagicMock()
        ctx.config = {"chart_id": "test-chart-id"}

        peak = date(2026, 3, 15)
        conv_row = ("conv-1", "sig-1", "dasha", peak, 0.8, 0.9, peak, peak)

        conn = MagicMock()
        ctx.db_conn = conn

        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=cm)
        cm.__exit__ = MagicMock(return_value=False)
        conn.cursor.return_value = cm
        cm.fetchall.return_value = [conv_row]

        # Patch swisseph to be unavailable
        with patch.dict(sys.modules, {"swisseph": None}):
            writer = mod.KaVighnakaraWriter()
            result = writer.run(ctx)

        assert result.rows_inserted == 0, (
            f"Expected rows_inserted=0 when swisseph unavailable, got {result.rows_inserted}"
        )
        assert result.notes is not None, "Expected non-None notes when swisseph unavailable"
        notes_lower = result.notes.lower()
        assert "swisseph" in notes_lower or "ephemeris" in notes_lower, (
            f"Notes should mention swisseph/ephemeris, got: '{result.notes}'"
        )

    def test_swisseph_unavailable_does_not_insert_rows(self):
        """W2 contrast: no INSERT INTO kala_obstruction when swisseph is absent."""
        mod = self._load()

        ctx = MagicMock()
        ctx.config = {"chart_id": "test-chart-id"}

        peak = date(2026, 3, 15)
        conn = MagicMock()
        ctx.db_conn = conn

        cm = MagicMock()
        cm.__enter__ = MagicMock(return_value=cm)
        cm.__exit__ = MagicMock(return_value=False)
        conn.cursor.return_value = cm
        cm.fetchall.return_value = [("conv-1", "sig-1", "dasha", peak, 0.8, 0.9, peak, peak)]

        with patch.dict(sys.modules, {"swisseph": None}):
            writer = mod.KaVighnakaraWriter()
            writer.run(ctx)

        # executemany must NOT have been called (no INSERT with stub rows)
        assert not cm.executemany.called, (
            "executemany was called even though swisseph was unavailable — "
            "silent stub rows were being inserted."
        )
        # DELETE must NOT have been called (prior data must not be wiped before swisseph check)
        delete_calls = [c for c in cm.execute.call_args_list if "DELETE" in str(c)]
        assert not delete_calls, (
            f"DELETE was called before swisseph check: {delete_calls}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# W3 — bo_samvada: dead DDL branch gone; live VIEW path intact
# ─────────────────────────────────────────────────────────────────────────────

class TestW3SamvadaDeadBranchRemoved:
    """W3: dead DDL branch (_CREATE_VIEW with GROUP BY bug) is gone; live path works."""

    def _load(self):
        _ensure_writers_stub()
        return _load_module("bo_samvada.py")

    def test_dead_variable_does_not_exist(self):
        """W3: _CREATE_VIEW (broken GROUP BY variant) must not exist in the module."""
        mod = self._load()
        assert not hasattr(mod, "_CREATE_VIEW"), (
            "_CREATE_VIEW (the dead DDL branch with the GROUP BY bug) still exists in "
            "bo_samvada.py — it was supposed to be removed."
        )

    def test_live_view_variable_exists_and_is_non_empty(self):
        """W3: _CREATE_VIEW_CLEAN (correct single-group-by view) must exist."""
        mod = self._load()
        assert hasattr(mod, "_CREATE_VIEW_CLEAN"), (
            "_CREATE_VIEW_CLEAN is missing from bo_samvada.py"
        )
        sql = mod._CREATE_VIEW_CLEAN
        assert "vw_chart_digest" in sql, "_CREATE_VIEW_CLEAN must contain vw_chart_digest"
        assert "GROUP BY m.chart_id, m.ayanamsha_id" in sql, (
            "_CREATE_VIEW_CLEAN must use the correct single GROUP BY"
        )

    def test_live_view_group_by_does_not_include_cv_columns(self):
        """W3: the live VIEW's GROUP BY must NOT include cv.domain / convergence columns."""
        mod = self._load()
        sql = mod._CREATE_VIEW_CLEAN
        group_by_clause = sql.split("GROUP BY")[-1]
        assert "cv.domain" not in group_by_clause, (
            "cv.domain found in GROUP BY clause of _CREATE_VIEW_CLEAN — "
            "this is the bug from the deleted dead branch."
        )

    def test_run_creates_view_using_clean_ddl(self):
        """W3: run() calls conn.execute with the correct VIEW DDL."""
        mod = self._load()

        ctx = MagicMock()
        ctx.dry_run = False
        conn = MagicMock()
        ctx.db_conn = conn

        writer = mod.BoSamvadaWriter()
        result = writer.run(ctx)

        # At least one execute call must CREATE the view
        calls_str = " ".join(str(c) for c in conn.execute.call_args_list)
        assert "CREATE OR REPLACE VIEW vw_chart_digest" in calls_str, (
            "run() did not issue CREATE OR REPLACE VIEW vw_chart_digest; "
            f"execute calls were: {calls_str[:400]}"
        )

    def test_dry_run_does_not_execute_ddl(self):
        """W3: dry_run returns 0 rows without touching the DB."""
        mod = self._load()

        ctx = MagicMock()
        ctx.dry_run = True
        conn = MagicMock()
        ctx.db_conn = conn

        writer = mod.BoSamvadaWriter()
        result = writer.run(ctx)

        assert result.rows_inserted == 0
        conn.execute.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# W4 — mi_pramana: stub functions explicitly marked
# ─────────────────────────────────────────────────────────────────────────────

class TestW4PramanaStubsMarked:
    """W4: _score_falsifier and _score_manifestation are visibly stubs."""

    def _load(self):
        _ensure_writers_stub()
        return _load_module("mi_pramana.py")

    def test_is_stub_falsifier_sentinel_is_true(self):
        """W4: _IS_STUB_FALSIFIER sentinel must be True."""
        mod = self._load()
        assert hasattr(mod, "_IS_STUB_FALSIFIER"), (
            "_IS_STUB_FALSIFIER sentinel missing from mi_pramana.py"
        )
        assert mod._IS_STUB_FALSIFIER is True, (
            f"_IS_STUB_FALSIFIER should be True, got {mod._IS_STUB_FALSIFIER}"
        )

    def test_is_stub_manifestation_sentinel_is_true(self):
        """W4: _IS_STUB_MANIFESTATION sentinel must be True."""
        mod = self._load()
        assert hasattr(mod, "_IS_STUB_MANIFESTATION"), (
            "_IS_STUB_MANIFESTATION sentinel missing from mi_pramana.py"
        )
        assert mod._IS_STUB_MANIFESTATION is True, (
            f"_IS_STUB_MANIFESTATION should be True, got {mod._IS_STUB_MANIFESTATION}"
        )

    def test_score_falsifier_docstring_contains_stub(self):
        """W4: _score_falsifier docstring must contain 'STUB'."""
        mod = self._load()
        doc = (mod._score_falsifier.__doc__ or "")
        assert "STUB" in doc, (
            f"_score_falsifier docstring must contain 'STUB'. Got: '{doc[:200]}'"
        )

    def test_score_manifestation_docstring_contains_stub(self):
        """W4: _score_manifestation docstring must contain 'STUB'."""
        mod = self._load()
        doc = (mod._score_manifestation.__doc__ or "")
        assert "STUB" in doc, (
            f"_score_manifestation docstring must contain 'STUB'. Got: '{doc[:200]}'"
        )

    def test_score_falsifier_still_returns_1_0(self):
        """W4: stub value (1.0) unchanged — only marking was added."""
        mod = self._load()
        result = mod._score_falsifier(None, {})
        assert result == 1.0, f"_score_falsifier should return 1.0 (stub), got {result}"

    def test_score_manifestation_still_returns_0_5(self):
        """W4: stub value (0.5, None) unchanged — only marking was added."""
        mod = self._load()
        score, channel = mod._score_manifestation([], {})
        assert score == 0.5, f"_score_manifestation should return 0.5 (stub), got {score}"
        assert channel is None, f"_score_manifestation channel should be None, got {channel}"


# ─────────────────────────────────────────────────────────────────────────────
# W5 — mi_darshana: embeddings substep emits [EXTERNAL_COMPUTATION_REQUIRED]
# ─────────────────────────────────────────────────────────────────────────────

class TestW5DarshanaExternalComputationMarker:
    """W5: mi_darshana marks the embedding substep as [EXTERNAL_COMPUTATION_REQUIRED]."""

    def _load(self):
        _ensure_writers_stub()
        return _load_module("mi_darshana.py")

    def test_module_docstring_contains_external_computation_required(self):
        """W5: module docstring must mention [EXTERNAL_COMPUTATION_REQUIRED]."""
        mod = self._load()
        doc = mod.__doc__ or ""
        assert "[EXTERNAL_COMPUTATION_REQUIRED]" in doc, (
            "mi_darshana module docstring must contain [EXTERNAL_COMPUTATION_REQUIRED]"
        )

    def test_embeddings_substep_returns_zero_rows_with_marker_in_notes(self):
        """W5: _substep_embeddings returns rows_inserted=0 and notes contain the marker."""
        mod = self._load()

        writer = mod.MiDarshanaWriter()
        writer._chart_id = "test-chart"
        writer._insight_count = 42  # simulate some prior insight units

        conn = MagicMock()
        t0 = time.time()
        result = writer._substep_embeddings(conn, "test-chart", t0)

        assert result.rows_inserted == 0, (
            f"_substep_embeddings should return 0 rows, got {result.rows_inserted}"
        )
        assert result.notes is not None, "_substep_embeddings notes must not be None"
        assert "[EXTERNAL_COMPUTATION_REQUIRED]" in result.notes, (
            f"_substep_embeddings notes must contain [EXTERNAL_COMPUTATION_REQUIRED], "
            f"got: '{result.notes}'"
        )

    def test_empty_upstream_returns_zero_rows(self):
        """W5: with no source data, insight_units substep returns 0 rows + explicit notes."""
        mod = self._load()

        writer = mod.MiDarshanaWriter()
        writer._chart_id = "test-chart"

        # Mock conn: all queries return empty results
        conn = MagicMock()
        cursor_cm = MagicMock()
        cursor_cm.__enter__ = MagicMock(return_value=cursor_cm)
        cursor_cm.__exit__ = MagicMock(return_value=False)
        cursor_cm.fetchall.return_value = []
        cursor_cm.fetchone.return_value = None
        conn.cursor.return_value = cursor_cm

        t0 = time.time()
        result = writer._substep_insight_units(conn, "test-chart", t0)

        assert result.rows_inserted == 0, (
            f"With empty upstream, insight_units should return 0 rows, "
            f"got {result.rows_inserted}"
        )
        assert result.notes is not None and len(result.notes) > 0, (
            "With empty upstream, notes must be non-empty"
        )
