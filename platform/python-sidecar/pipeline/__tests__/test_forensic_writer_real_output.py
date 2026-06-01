"""
test_forensic_writer_real_output.py — §4 real-output test for A2_forensic_render.

Feeds the REAL pyjhora_adapter.compute_chart() output (not a synthetic fixture)
through forensic_writer.write() with a fake conn and asserts:
  1. write() returns 1 (one row written per ayanamsha).
  2. The captured content_md is non-empty.
  3. The no-narration linter passes on the persisted content.
  4. All 13 section anchors are present.
  5. dispatch_asset() with a writer that raises ModuleNotFoundError propagates
     the exception instead of silently returning 0 (regression guard for the
     ImportError-swallow bug fixed in dispatch_asset()).

This test uses the real engine, so it skips if pyjhora_adapter is unavailable.
All DB I/O uses _FakeConn (no live DB required).
"""
from __future__ import annotations

import json
import re
import sys
import os
import types
import unittest.mock as mock
from contextlib import contextmanager

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# ---------------------------------------------------------------------------
# Skip whole module if pyjhora_adapter not importable (headless CI without PyJHora)
# ---------------------------------------------------------------------------

try:
    from pyjhora_adapter import compute_chart as _compute_chart
    _PYJHORA_AVAILABLE = True
except Exception:
    _PYJHORA_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _PYJHORA_AVAILABLE,
    reason="pyjhora_adapter not available in this environment",
)

from pipeline.writers.forensic_writer import write, _SECTION_REGISTRY
from pipeline.render.base_renderer import anchor_id, FORBIDDEN_PATTERN


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeConn:
    """Records INSERT INTO chart_documents executions."""
    def __init__(self):
        self.rows_upserted: list[dict] = []

    @contextmanager
    def cursor(self):
        cur = mock.MagicMock()
        cur.execute = self._execute
        yield cur

    def _execute(self, sql: str, params: tuple) -> None:
        if "INSERT INTO chart_documents" in sql:
            chart_id, ayanamsha_id, doc_type, build_id, content_md, content_json_str, byte_size = params
            self.rows_upserted.append({
                "chart_id": chart_id,
                "ayanamsha_id": ayanamsha_id,
                "document_type": doc_type,
                "build_id": build_id,
                "content_md": content_md,
                "byte_size": byte_size,
                "content_json": json.loads(content_json_str),
            })

    def commit(self):
        pass


# Native birth data (1984-02-05 10:43 IST, Bhubaneswar)
_NATIVE_INPUTS = {
    "datetime_iso": "1984-02-05T10:43:00",
    "tz_offset_hours": 5.5,
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "place_name": "Bhubaneswar",
    "subject_label": "362f9f17-95a5-490b-a5a7-027d3e0efda0",
}

_NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"
_BUILD_ID = "sf-fix-real-output-test"


# ---------------------------------------------------------------------------
# §4 — Real compute_chart() output feeds forensic_writer correctly
# ---------------------------------------------------------------------------

class TestRealOutputForensicWriter:
    """
    These tests use REAL pyjhora_adapter.compute_chart() output and a _FakeConn.
    They prove that the live engine output shape is handled correctly end-to-end
    by the adapter shim + all 13 section renderers + writer.

    Pre-fix: these tests would fail in the Docker pipeline image because jinja2
    was absent, causing ModuleNotFoundError to be swallowed by dispatch_asset()
    and no row written. Post-fix (Jinja2 added to pipeline/requirements.txt):
    all assertions pass.
    """

    @pytest.fixture(scope="class")
    def real_chart_output(self):
        return _compute_chart(inputs=_NATIVE_INPUTS, ayanamsha_id="lahiri")

    def test_write_returns_one_with_real_output(self, real_chart_output):
        """write() returns 1 when called with real compute_chart() output."""
        conn = _FakeConn()
        result = write(
            build_id=_BUILD_ID,
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id="lahiri",
            chart_output=real_chart_output,
            conn=conn,
        )
        assert result == 1, f"Expected 1, got {result}"

    def test_one_row_upserted_with_real_output(self, real_chart_output):
        """Exactly one row is inserted into chart_documents."""
        conn = _FakeConn()
        write(
            build_id=_BUILD_ID,
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id="lahiri",
            chart_output=real_chart_output,
            conn=conn,
        )
        assert len(conn.rows_upserted) == 1

    def test_content_md_nonempty_with_real_output(self, real_chart_output):
        """content_md is non-empty (> 1000 chars for a full chart)."""
        conn = _FakeConn()
        write(
            build_id=_BUILD_ID,
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id="lahiri",
            chart_output=real_chart_output,
            conn=conn,
        )
        md = conn.rows_upserted[0]["content_md"]
        assert md, "content_md must not be empty"
        assert len(md) > 1000, f"content_md suspiciously short: {len(md)} chars"

    def test_linter_passes_on_real_output(self, real_chart_output):
        """No narration verbs in content rendered from real engine output."""
        conn = _FakeConn()
        write(
            build_id=_BUILD_ID,
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id="lahiri",
            chart_output=real_chart_output,
            conn=conn,
        )
        md = conn.rows_upserted[0]["content_md"]
        matches = FORBIDDEN_PATTERN.findall(md)
        assert not matches, f"Narration violations in real-output render: {set(matches)}"

    def test_all_13_anchors_present_with_real_output(self, real_chart_output):
        """All 13 section anchors are present in the rendered markdown."""
        conn = _FakeConn()
        write(
            build_id=_BUILD_ID,
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id="lahiri",
            chart_output=real_chart_output,
            conn=conn,
        )
        md = conn.rows_upserted[0]["content_md"]
        for title, _, _ in _SECTION_REGISTRY:
            aid = anchor_id(title)
            assert f"#{aid}" in md, f"Anchor #{aid!r} missing from real-output render"

    def test_dry_run_with_real_output(self, real_chart_output):
        """write() with conn=None returns 1 (dry-run; no DB write)."""
        result = write(
            build_id=_BUILD_ID,
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id="lahiri",
            chart_output=real_chart_output,
            conn=None,
        )
        assert result == 1

    @pytest.mark.parametrize("ayanamsha_id", ["lahiri", "true_chitra", "kp", "raman", "surya_siddhanta"])
    def test_all_five_ayanamshas(self, ayanamsha_id):
        """write() succeeds for all 5 canonical ayanamshas."""
        real_output = _compute_chart(inputs=_NATIVE_INPUTS, ayanamsha_id=ayanamsha_id)
        result = write(
            build_id=f"{_BUILD_ID}-{ayanamsha_id}",
            chart_id=_NATIVE_CHART_ID,
            ayanamsha_id=ayanamsha_id,
            chart_output=real_output,
            conn=None,
        )
        assert result == 1, f"Expected 1 for ayanamsha={ayanamsha_id}, got {result}"


# ---------------------------------------------------------------------------
# §3 regression guard — dispatch_asset() ImportError propagation
# ---------------------------------------------------------------------------

class TestDispatchAssetImportErrorPropagation:
    """
    Regression guard for the ImportError-swallow bug:
    dispatch_asset() must NOT catch ImportError from inside a registered writer's
    call. It must only catch ImportError from the WRITER_REGISTRY import itself.

    Before the fix, a ModuleNotFoundError raised by a lazy import inside
    forensic_writer.write() (e.g. 'from jinja2 import ...') was caught by
    'except ImportError: pass' in dispatch_asset(), causing silent return 0.

    After the fix, writer call exceptions propagate to the caller.
    """

    def test_registered_writer_importerror_propagates(self):
        """
        A ModuleNotFoundError raised INSIDE a registered writer propagates out of
        dispatch_asset() rather than being caught by the except ImportError block.
        """
        # Stub WRITER_REGISTRY so the module loads without pyjhora/psycopg2
        stub_writers = types.ModuleType("pipeline.writers")

        def _raising_writer(*args, **kwargs):
            raise ModuleNotFoundError("No module named 'jinja2'")

        stub_writers.WRITER_REGISTRY = {"A2_forensic_render": _raising_writer}

        import pipeline.build_chart as bc

        with mock.patch.dict("sys.modules", {"pipeline.writers": stub_writers}):
            # Re-bind the name inside build_chart's namespace so its lazy import
            # sees our stub instead of the real module.
            with mock.patch.object(bc, "dispatch_asset",
                                   wraps=bc.dispatch_asset):
                with pytest.raises(ModuleNotFoundError):
                    bc.dispatch_asset(
                        "A2_forensic_render",
                        "build-001",
                        "chart-001",
                        ["lahiri"],
                        conn=None,
                        chart_output={},
                        ayanamsha_id="lahiri",
                    )

    def test_unregistered_asset_still_returns_zero(self):
        """
        An asset NOT in WRITER_REGISTRY still returns 0 (stub path unchanged).
        """
        import pipeline.build_chart as bc

        # Use an asset_id that is never registered
        result = bc.dispatch_asset(
            "A99_nonexistent",
            "build-001",
            "chart-001",
            ["lahiri"],
            conn=None,
            chart_output={},
            ayanamsha_id="lahiri",
        )
        assert result == 0, f"Expected stub return 0 for unregistered asset, got {result}"

    def test_registry_importerror_still_returns_zero(self):
        """
        If the WRITER_REGISTRY import itself fails with ImportError, dispatch_asset
        still falls through to the stub path and returns 0.
        """
        import builtins
        import pipeline.build_chart as bc

        real_import = builtins.__import__

        def _block_writers(name, *args, **kwargs):
            if name == "pipeline.writers":
                raise ImportError("simulated writers package unavailable")
            return real_import(name, *args, **kwargs)

        # Remove cached module so the import runs fresh inside the function
        import sys
        saved = sys.modules.pop("pipeline.writers", None)
        try:
            with mock.patch("builtins.__import__", side_effect=_block_writers):
                result = bc.dispatch_asset(
                    "A2_forensic_render",
                    "build-001",
                    "chart-001",
                    ["lahiri"],
                    conn=None,
                    chart_output={},
                    ayanamsha_id="lahiri",
                )
        finally:
            if saved is not None:
                sys.modules["pipeline.writers"] = saved

        assert result == 0, f"Expected 0 when registry import fails, got {result}"
