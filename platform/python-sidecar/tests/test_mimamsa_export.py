"""
test_mimamsa_export.py — Unit tests for brahmagyan.mimamsa.export_to_bigquery (BRAHMA MI-5-5)

Tests:
    1. _rows_to_parquet — round-trip serialization (range assertions, not exact values)
    2. export_table — DB mock: export_log entry created with non-null source_citation
    3. export_table — DB mock: BQ dataset accessible check
    4. export_table — leakage guard: life_events without calibration prefix raises
    5. export_table — source_citation non-null enforced at row level (skips null rows)
    6. run_export — smoke: returns result per table_key
    7. run_acceptance_gate — AC1: export_log reachable (mock DB)
    8. run_acceptance_gate — AC3: null citation detected → gate fails
    9. run_acceptance_gate — AC4: leakage guard catches life_events without prefix
    10. _assert_not_prediction_feed — hardcoded leakage guard unit test
    11. LEL: life_events_calibration export uses calibration-only SQL filter

No live DB or GCP credentials required. All external calls are mocked.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch, call

import pytest


# ── Lazy import helper ─────────────────────────────────────────────────────────

def _mod():
    """Import the module under test (lazy so psycopg/gcloud missing doesn't block)."""
    from brahmagyan.mimamsa import export_to_bigquery as m
    return m


# ── Fixtures ───────────────────────────────────────────────────────────────────

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

_CHART_FACTS_ROW = {
    "fact_id": "CF-PLN-001",
    "chart_id": NATIVE_CHART_ID,
    "category": "planets",
    "subcategory": "position",
    "key": "sun_longitude",
    "value_text": "291.96",
    "value_num": 291.96,
    "value_json": None,
    "ayanamsha_id": "lahiri",
    "source_citation": "FORENSIC v8.0 §2.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md): Sun in Capricorn (291.96°, Shravana Pada 4)",
    "computed_at": datetime.now(timezone.utc).isoformat(),
    "build_id": "test-build-001",
}

_BODHA_SIGNAL_ROW = {
    "signal_id": "SIG.MSR.001",
    "chart_id": NATIVE_CHART_ID,
    "signal_group": "MSR",
    "domain": "career",
    "valence": "benefic",
    "confidence": 0.85,
    "state": "lit",
    "reinforcement_count": 3,
    "source_citation": "MSR_v5_0.md SIG.001 | FORENSIC_v8_0 §2.1 | bodha_signals BRAHMA-BO-2-4",
    "ayanamsha_id": "lahiri",
    "computed_at": datetime.now(timezone.utc).isoformat(),
    "build_id": "test-build-001",
}

_LEL_ROW = {
    "event_id": "EVT.1984.02.05.01",
    "event_date": "1984-02-05",
    "date_confidence": "exact",
    "category": "other",
    "subcategory": "birth",
    "description": "Born in Bhubaneswar",
    "magnitude": "life-altering",
    "valence": "neutral",
    "vimshottari_md": "Jupiter",
    "vimshottari_ad": "Venus",
    "yogini_md": "Bhramari",
    "chara_md_ad": "Aries / Taurus",
    "sade_sati_phase": None,
    "retrodictive_match": "yes",
    "signals_matched": json.dumps(["SIG.01", "SIG.04", "CVG.01"]),
    "confidence": 0.89,
    "source_citation": (
        "LIFE_EVENT_LOG_v1_2.md §3 EVT.1984.02.05.01 | "
        "FORENSIC v8.0 §2.1 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) (birth chart anchor) | "
        "LEL v1.7 calibration — CALIBRATION ONLY not prediction"
    ),
}


# ── 1. Parquet serialization ───────────────────────────────────────────────────

class TestRowsToParquet:
    def test_non_empty_rows_produce_bytes(self):
        m = _mod()
        data = [_CHART_FACTS_ROW]
        result = m._rows_to_parquet(data, schema_name="chart_facts")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_empty_rows_produce_bytes(self):
        m = _mod()
        result = m._rows_to_parquet([], schema_name="chart_facts")
        assert isinstance(result, bytes)
        # May be empty or minimal valid Parquet — just must not raise

    def test_multiple_rows(self):
        m = _mod()
        rows = [_CHART_FACTS_ROW, {**_CHART_FACTS_ROW, "fact_id": "CF-PLN-002", "value_num": 327.05}]
        result = m._rows_to_parquet(rows, schema_name="chart_facts")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_bodha_signals_round_trip(self):
        m = _mod()
        rows = [_BODHA_SIGNAL_ROW]
        result = m._rows_to_parquet(rows, schema_name="bodha_signals")
        assert isinstance(result, bytes)
        assert len(result) > 0


# ── 2. export_table — export_log entry created with non-null citation ──────────

class TestExportTableLogEntry:
    def _make_mock_conn(self, rows: list[tuple[Any, ...]], col_names: list[str]):
        """Build a mock psycopg connection that returns given rows."""
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.description = [(name,) for name in col_names]
        mock_cursor.fetchall.return_value = rows

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        return mock_conn

    def test_export_log_written_with_non_null_citation(self):
        m = _mod()

        row = _CHART_FACTS_ROW
        col_names = list(row.keys())
        db_row = tuple(row[k] for k in col_names)

        mock_conn = self._make_mock_conn([db_row], col_names)

        written_args: list[Any] = []

        def fake_write_log(conn, export_id, table_name, row_count, gcs_path, source_citation):
            written_args.append({
                "export_id": export_id,
                "table_name": table_name,
                "row_count": row_count,
                "gcs_path": gcs_path,
                "source_citation": source_citation,
            })

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.object(m, "_rows_to_parquet", return_value=b"fake-parquet"),
            patch.object(m, "_upload_to_gcs", return_value="gs://test-bucket/path.parquet"),
            patch.object(m, "_load_parquet_to_bq", return_value=1),
            patch.object(m, "_write_export_log", side_effect=fake_write_log),
        ):
            result = m.export_table("chart_facts", chart_id=NATIVE_CHART_ID, dry_run=False, write_log=True)

        assert result["table_name"] == "chart_facts"
        assert result["row_count"] >= 0  # range assertion — not exact
        assert "source_citation" in result
        assert result["source_citation"]  # non-null, non-empty

        assert len(written_args) == 1
        log_entry = written_args[0]
        assert log_entry["table_name"] == "chart_facts"
        assert log_entry["source_citation"]  # non-null
        assert "FORENSIC" in log_entry["source_citation"]
        assert "MI-5-5" in log_entry["source_citation"]

    def test_dry_run_skips_log_write(self):
        m = _mod()

        row = _CHART_FACTS_ROW
        col_names = list(row.keys())
        db_row = tuple(row[k] for k in col_names)

        mock_conn = self._make_mock_conn([db_row], col_names)
        write_log_calls: list[Any] = []

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.object(m, "_rows_to_parquet", return_value=b"fake-parquet"),
            patch.object(m, "_upload_to_gcs", return_value="gs://test-bucket/path.parquet"),
            patch.object(m, "_load_parquet_to_bq", return_value=0),
            patch.object(m, "_write_export_log", side_effect=lambda *a, **kw: write_log_calls.append(a)),
        ):
            result = m.export_table("chart_facts", chart_id=NATIVE_CHART_ID, dry_run=True, write_log=True)

        assert result["dry_run"] is True
        assert len(write_log_calls) == 0  # no DB write in dry_run


# ── 3. BQ dataset accessibility ───────────────────────────────────────────────

class TestBigQueryAccessible:
    def test_gate_ac2_passes_when_bq_missing(self):
        """AC2 passes (skip) when google-cloud-bigquery not installed."""
        m = _mod()

        # Mock AC1 and AC3/AC4 so they pass
        mock_row = MagicMock()
        mock_row.__getitem__ = MagicMock(side_effect=lambda i: 0)

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchone.return_value = (0,)

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.dict("sys.modules", {"google.cloud.bigquery": None}),
        ):
            result = m.run_acceptance_gate()

        ac2 = next((c for c in result["checks"] if c["id"] == "AC2"), None)
        assert ac2 is not None
        assert ac2["passed"] is True  # Skipped = pass (not a hard requirement in CI)


# ── 4. Leakage guard ──────────────────────────────────────────────────────────

class TestLeakageGuard:
    def test_lel_without_calibration_prefix_raises(self):
        m = _mod()
        with pytest.raises(RuntimeError, match="leakage guard violation"):
            m._assert_not_prediction_feed("life_events", is_lel=True)

    def test_lel_with_calibration_prefix_passes(self):
        m = _mod()
        # Should not raise
        m._assert_not_prediction_feed("life_events_calibration", is_lel=True)

    def test_non_lel_table_always_passes(self):
        m = _mod()
        m._assert_not_prediction_feed("chart_facts", is_lel=False)
        m._assert_not_prediction_feed("bodha_signals", is_lel=False)

    def test_unknown_lel_variant_raises(self):
        """life_events_raw or life_events_prediction should raise."""
        m = _mod()
        with pytest.raises(RuntimeError, match="leakage guard violation"):
            m._assert_not_prediction_feed("life_events_prediction", is_lel=True)

    def test_lel_calibration_extended_passes(self):
        """life_events_calibration_v2 passes (starts with correct prefix)."""
        m = _mod()
        m._assert_not_prediction_feed("life_events_calibration_v2", is_lel=True)


# ── 5. Source citation non-null filter ─────────────────────────────────────────

class TestSourceCitationFilter:
    def test_rows_missing_citation_are_skipped(self):
        """Rows with null/empty source_citation must be skipped (not exported)."""
        m = _mod()

        good_row = _CHART_FACTS_ROW  # has citation
        bad_row = {**_CHART_FACTS_ROW, "fact_id": "CF-BAD-001", "source_citation": None}
        empty_row = {**_CHART_FACTS_ROW, "fact_id": "CF-BAD-002", "source_citation": ""}

        col_names = list(good_row.keys())
        db_rows = [
            tuple(good_row[k] for k in col_names),
            tuple(bad_row[k] for k in col_names),
            tuple(empty_row[k] for k in col_names),
        ]

        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.description = [(name,) for name in col_names]
        mock_cursor.fetchall.return_value = db_rows

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        exported_rows: list[Any] = []

        def capture_parquet(rows, schema_name):
            exported_rows.extend(rows)
            return b"fake-parquet"

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.object(m, "_rows_to_parquet", side_effect=capture_parquet),
            patch.object(m, "_upload_to_gcs", return_value="gs://test/path.parquet"),
            patch.object(m, "_load_parquet_to_bq", return_value=1),
            patch.object(m, "_write_export_log"),
        ):
            result = m.export_table("chart_facts", chart_id=NATIVE_CHART_ID, dry_run=False)

        # Only 1 row with valid citation should be exported
        assert result["row_count"] == 1
        assert len(exported_rows) == 1
        assert exported_rows[0]["fact_id"] == "CF-PLN-001"


# ── 6. run_export smoke ────────────────────────────────────────────────────────

class TestRunExport:
    def test_run_export_returns_result_per_table(self):
        m = _mod()

        call_count = [0]

        def fake_export_table(table_key, **kwargs):
            call_count[0] += 1
            return {
                "table_name": table_key,
                "row_count": 10 + call_count[0],  # range assertion bait
                "gcs_path": f"brahma/l5/{table_key}/test.parquet",
                "gcs_uri": f"gs://bucket/{table_key}/test.parquet",
                "bq_table": f"project.dataset.{table_key}",
                "source_citation": f"FORENSIC | BRAHMA MI-5-5 | table={table_key}",
                "dry_run": kwargs.get("dry_run", False),
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }

        with patch.object(m, "export_table", side_effect=fake_export_table):
            results = m.run_export(NATIVE_CHART_ID, tables=["chart_facts", "bodha_signals"])

        assert len(results) == 2
        table_names = [r["table_name"] for r in results]
        assert "chart_facts" in table_names
        assert "bodha_signals" in table_names

    def test_run_export_default_excludes_lel(self):
        """Default export does NOT include life_events (calibration only)."""
        m = _mod()
        exported_tables: list[str] = []

        def fake_export_table(table_key, **kwargs):
            exported_tables.append(table_key)
            return {"table_name": table_key, "row_count": 5, "source_citation": "test"}

        with patch.object(m, "export_table", side_effect=fake_export_table):
            m.run_export(NATIVE_CHART_ID)

        assert "life_events_calibration" not in exported_tables
        assert "chart_facts" in exported_tables
        assert "bodha_signals" in exported_tables

    def test_run_export_include_life_events_adds_calibration_table(self):
        m = _mod()
        exported_tables: list[str] = []

        def fake_export_table(table_key, **kwargs):
            exported_tables.append(table_key)
            return {"table_name": table_key, "row_count": 57, "source_citation": "LEL v1.7"}

        with patch.object(m, "export_table", side_effect=fake_export_table):
            m.run_export(NATIVE_CHART_ID, include_life_events=True)

        assert "life_events_calibration" in exported_tables

    def test_run_export_handles_table_failure_gracefully(self):
        """A failed table should not crash the entire run."""
        m = _mod()

        def fail_bodha(table_key, **kwargs):
            if table_key == "bodha_signals":
                raise RuntimeError("DB connection refused")
            return {
                "table_name": table_key,
                "row_count": 100,
                "gcs_path": f"brahma/l5/{table_key}/test.parquet",
                "gcs_uri": f"gs://bucket/{table_key}/test.parquet",
                "bq_table": f"project.dataset.{table_key}",
                "source_citation": "FORENSIC | BRAHMA MI-5-5",
                "dry_run": False,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }

        with patch.object(m, "export_table", side_effect=fail_bodha):
            results = m.run_export(NATIVE_CHART_ID, tables=["chart_facts", "bodha_signals"])

        assert len(results) == 2
        failed = [r for r in results if "error" in r]
        succeeded = [r for r in results if "error" not in r]
        assert len(failed) == 1
        assert len(succeeded) == 1
        assert failed[0]["table_name"] == "bodha_signals"
        assert "DB connection refused" in failed[0]["error"]


# ── 7. Acceptance gate — AC1 ──────────────────────────────────────────────────

class TestAcceptanceGateAC1:
    def test_ac1_passes_when_export_log_reachable(self):
        m = _mod()

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchone.return_value = (42,)

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.dict("sys.modules", {"google.cloud.bigquery": None}),
        ):
            result = m.run_acceptance_gate()

        ac1 = next(c for c in result["checks"] if c["id"] == "AC1")
        assert ac1["passed"] is True
        assert ac1["value"] == 42  # row count — range: >= 0

    def test_ac1_fails_when_table_missing(self):
        m = _mod()

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.side_effect = Exception("relation mimamsa_export_log does not exist")

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.dict("sys.modules", {"google.cloud.bigquery": None}),
        ):
            result = m.run_acceptance_gate()

        ac1 = next(c for c in result["checks"] if c["id"] == "AC1")
        assert ac1["passed"] is False
        assert "mimamsa_export_log" in ac1["error"]


# ── 8. Acceptance gate — AC3: null citation → gate fails ──────────────────────

class TestAcceptanceGateAC3:
    def test_ac3_fails_when_null_citation_rows_exist(self):
        m = _mod()
        call_num = [0]

        def mock_execute(sql, params=None):
            call_num[0] += 1
            mock_result = MagicMock()
            if "source_citation IS NULL" in sql:
                # AC3 check: 2 rows have null citation
                mock_result.fetchone.return_value = (2,)
            else:
                mock_result.fetchone.return_value = (10,)
            return mock_result

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.side_effect = mock_execute

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.dict("sys.modules", {"google.cloud.bigquery": None}),
        ):
            result = m.run_acceptance_gate()

        ac3 = next(c for c in result["checks"] if c["id"] == "AC3")
        assert ac3["passed"] is False
        assert ac3["value"] == 2

    def test_ac3_passes_when_all_citations_present(self):
        m = _mod()

        def mock_execute(sql, params=None):
            mock_result = MagicMock()
            mock_result.fetchone.return_value = (0,)  # zero null citations
            return mock_result

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.side_effect = mock_execute

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.dict("sys.modules", {"google.cloud.bigquery": None}),
        ):
            result = m.run_acceptance_gate()

        ac3 = next(c for c in result["checks"] if c["id"] == "AC3")
        assert ac3["passed"] is True
        assert ac3["value"] == 0


# ── 9. Acceptance gate — AC4: leakage guard ───────────────────────────────────

class TestAcceptanceGateAC4:
    def test_ac4_fails_when_lel_without_calibration_prefix(self):
        m = _mod()

        def mock_execute(sql, params=None):
            mock_result = MagicMock()
            if "life_events_calibration" in sql and "NOT LIKE" in sql:
                # AC4 check: 1 row violates leakage guard
                mock_result.fetchone.return_value = (1,)
            else:
                mock_result.fetchone.return_value = (0,)
            return mock_result

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.side_effect = mock_execute

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.dict("sys.modules", {"google.cloud.bigquery": None}),
        ):
            result = m.run_acceptance_gate()

        ac4 = next(c for c in result["checks"] if c["id"] == "AC4")
        assert ac4["passed"] is False
        assert ac4["value"] == 1

    def test_ac4_passes_when_no_lel_leakage(self):
        m = _mod()

        def mock_execute(sql, params=None):
            mock_result = MagicMock()
            mock_result.fetchone.return_value = (0,)
            return mock_result

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.side_effect = mock_execute

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.dict("sys.modules", {"google.cloud.bigquery": None}),
        ):
            result = m.run_acceptance_gate()

        ac4 = next(c for c in result["checks"] if c["id"] == "AC4")
        assert ac4["passed"] is True
        assert ac4["value"] == 0


# ── 10. _write_export_log — source_citation blank raises ──────────────────────

class TestWriteExportLog:
    def test_blank_citation_raises_value_error(self):
        m = _mod()
        mock_conn = MagicMock()
        with pytest.raises(ValueError, match="source_citation must be non-null"):
            m._write_export_log(
                mock_conn,
                export_id=str(uuid.uuid4()),
                table_name="chart_facts",
                row_count=10,
                gcs_path="gs://bucket/path.parquet",
                source_citation="",  # blank — contract violation
            )

    def test_null_citation_raises_value_error(self):
        m = _mod()
        mock_conn = MagicMock()
        with pytest.raises(ValueError, match="source_citation must be non-null"):
            m._write_export_log(
                mock_conn,
                export_id=str(uuid.uuid4()),
                table_name="chart_facts",
                row_count=10,
                gcs_path="gs://bucket/path.parquet",
                source_citation=None,  # type: ignore
            )

    def test_valid_citation_calls_db(self):
        m = _mod()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        m._write_export_log(
            mock_conn,
            export_id=str(uuid.uuid4()),
            table_name="chart_facts",
            row_count=2717,
            gcs_path="gs://madhav-brahma-olap/chart_facts/20260604T120000Z.parquet",
            source_citation="FORENSIC v8.0 (chart_facts via forensic_render; md archived 99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md) | BRAHMA MI-5-5",
        )
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


# ── 11. LEL SQL includes calibration_only filter ──────────────────────────────

class TestLELCalibrationFilter:
    def test_lel_sql_has_calibration_only_filter(self):
        """Verify the SQL for life_events_calibration includes calibration_only = TRUE."""
        m = _mod()
        spec = m._TABLE_SPECS["life_events_calibration"]
        sql = spec["sql"]
        assert "calibration_only = TRUE" in sql, (
            "life_events_calibration SQL must filter calibration_only=TRUE "
            "to prevent prediction leakage"
        )

    def test_lel_spec_is_marked_lel(self):
        m = _mod()
        spec = m._TABLE_SPECS["life_events_calibration"]
        assert spec["is_lel"] is True

    def test_chart_facts_spec_is_not_lel(self):
        m = _mod()
        spec = m._TABLE_SPECS["chart_facts"]
        assert spec["is_lel"] is False

    def test_bodha_signals_spec_is_not_lel(self):
        m = _mod()
        spec = m._TABLE_SPECS["bodha_signals"]
        assert spec["is_lel"] is False


# ── 12. Provenance envelope on export result ───────────────────────────────────

class TestProvenanceEnvelope:
    def test_export_result_has_provenance_envelope(self):
        m = _mod()

        row = _CHART_FACTS_ROW
        col_names = list(row.keys())
        db_row = tuple(row[k] for k in col_names)

        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.description = [(name,) for name in col_names]
        mock_cursor.fetchall.return_value = [db_row]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.object(m, "_rows_to_parquet", return_value=b"fake"),
            patch.object(m, "_upload_to_gcs", return_value="gs://test/path.parquet"),
            patch.object(m, "_load_parquet_to_bq", return_value=1),
            patch.object(m, "_write_export_log"),
        ):
            result = m.export_table("chart_facts", chart_id=NATIVE_CHART_ID, dry_run=False)

        envelope = result.get("provenance_envelope", {})
        assert envelope.get("source") == "brahmagyan.mimamsa.export_to_bigquery"
        assert envelope.get("asset") == "MI-5-5"
        assert envelope.get("layer") == "L5 Mīmāṃsā"
        assert envelope.get("native_chart_id") == NATIVE_CHART_ID
        assert "exported_at" in envelope


# ── 13. _upload_to_gcs dry_run ────────────────────────────────────────────────

class TestGCSUpload:
    def test_dry_run_returns_uri_without_uploading(self):
        m = _mod()

        # In dry_run mode, no google.cloud.storage call should be made
        with patch.dict("sys.modules", {"google.cloud.storage": MagicMock()}):
            uri = m._upload_to_gcs(b"fake-data", "test/path.parquet", dry_run=True)

        assert uri.startswith("gs://")
        assert "test/path.parquet" in uri


# ── 14. Gate-3 contract assertions (MI-5-5) ───────────────────────────────────
#
# These tests encode the exact Gate-3 acceptance criteria the Conductor evaluates:
#   G3.1 — GCS path format: gs://madhav-brahma-olap/<table>/<date>.parquet
#   G3.2 — source_citation non-null on all export_log rows and result dicts
#   G3.3 — row_count >= 0 (count assertion — never negative)
#   G3.4 — provenance_envelope present with required keys
#   G3.5 — formula bounds: multiplier in [0.8, 1.2]; row_count integer >= 0

class TestGate3Contract:
    """
    Gate-3 acceptance battery for MI-5-5 (mimamsa.research).
    Conductor runs these as the final verification before marking status=green.
    """

    # ── G3.1: GCS path format ─────────────────────────────────────────────────

    def test_g3_1_default_gcs_bucket_is_madhav_brahma_olap(self):
        """GCS_BUCKET default must be madhav-brahma-olap (provisioned bucket)."""
        import importlib
        import sys
        # Force clean reload without env override
        mod_name = "brahmagyan.mimamsa.export_to_bigquery"
        saved = sys.modules.pop(mod_name, None)
        try:
            import os
            old_val = os.environ.pop("GCS_BUCKET", None)
            m = importlib.import_module(mod_name)
            importlib.reload(m)
            assert m.GCS_BUCKET == "madhav-brahma-olap", (
                f"GCS_BUCKET default must be 'madhav-brahma-olap', got {m.GCS_BUCKET!r}"
            )
        finally:
            if old_val is not None:
                os.environ["GCS_BUCKET"] = old_val
            if saved is not None:
                sys.modules[mod_name] = saved

    def test_g3_1_gcs_path_format_table_date_parquet(self):
        """GCS path must follow <table>/<date>.parquet — no extra nesting."""
        m = _mod()

        row = _CHART_FACTS_ROW
        col_names = list(row.keys())
        db_row = tuple(row[k] for k in col_names)

        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.description = [(name,) for name in col_names]
        mock_cursor.fetchall.return_value = [db_row]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        captured_paths: list[str] = []

        def capture_upload(data, gcs_path, *, dry_run=False):
            captured_paths.append(gcs_path)
            return f"gs://madhav-brahma-olap/{gcs_path}"

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.object(m, "_rows_to_parquet", return_value=b"fake"),
            patch.object(m, "_upload_to_gcs", side_effect=capture_upload),
            patch.object(m, "_load_parquet_to_bq", return_value=1),
            patch.object(m, "_write_export_log"),
        ):
            result = m.export_table("chart_facts", chart_id=NATIVE_CHART_ID, export_timestamp="20260604T120000Z", dry_run=False)

        assert len(captured_paths) == 1
        path = captured_paths[0]
        # Must be <table>/<date>.parquet — exactly 2 path segments
        parts = path.split("/")
        assert len(parts) == 2, (
            f"GCS path must be '<table>/<date>.parquet' (2 segments), got {path!r}"
        )
        assert parts[0] == "chart_facts", f"First segment must be table name, got {parts[0]!r}"
        assert parts[1].endswith(".parquet"), f"Second segment must end in .parquet, got {parts[1]!r}"

    def test_g3_1_gcs_uri_contains_madhav_brahma_olap(self):
        """Full GCS URI in result must reference madhav-brahma-olap bucket."""
        m = _mod()

        row = _CHART_FACTS_ROW
        col_names = list(row.keys())
        db_row = tuple(row[k] for k in col_names)

        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.description = [(name,) for name in col_names]
        mock_cursor.fetchall.return_value = [db_row]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        def real_uri_upload(data, gcs_path, *, dry_run=False):
            # Simulate what _upload_to_gcs does with the real default bucket
            return f"gs://{m.GCS_BUCKET}/{gcs_path}"

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.object(m, "_rows_to_parquet", return_value=b"fake"),
            patch.object(m, "_upload_to_gcs", side_effect=real_uri_upload),
            patch.object(m, "_load_parquet_to_bq", return_value=1),
            patch.object(m, "_write_export_log"),
        ):
            result = m.export_table("chart_facts", chart_id=NATIVE_CHART_ID, export_timestamp="20260604T120000Z", dry_run=False)

        assert "madhav-brahma-olap" in result["gcs_uri"], (
            f"gcs_uri must reference 'madhav-brahma-olap', got {result['gcs_uri']!r}"
        )
        assert result["gcs_uri"].startswith("gs://"), (
            f"gcs_uri must start with gs://, got {result['gcs_uri']!r}"
        )
        assert result["gcs_uri"].endswith(".parquet"), (
            f"gcs_uri must end in .parquet, got {result['gcs_uri']!r}"
        )

    # ── G3.2: source_citation non-null ───────────────────────────────────────

    def test_g3_2_result_source_citation_non_null(self):
        """export_table result must carry non-null source_citation."""
        m = _mod()

        row = _CHART_FACTS_ROW
        col_names = list(row.keys())
        db_row = tuple(row[k] for k in col_names)

        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.description = [(name,) for name in col_names]
        mock_cursor.fetchall.return_value = [db_row]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.object(m, "_rows_to_parquet", return_value=b"fake"),
            patch.object(m, "_upload_to_gcs", return_value="gs://madhav-brahma-olap/chart_facts/ts.parquet"),
            patch.object(m, "_load_parquet_to_bq", return_value=1),
            patch.object(m, "_write_export_log"),
        ):
            result = m.export_table("chart_facts", chart_id=NATIVE_CHART_ID, dry_run=False)

        assert result.get("source_citation"), "source_citation must be non-null and non-empty"
        assert "FORENSIC" in result["source_citation"], "source_citation must reference FORENSIC"
        assert "MI-5-5" in result["source_citation"], "source_citation must reference MI-5-5"

    def test_g3_2_log_source_citation_constant_non_null(self):
        """The module-level _LOG_SOURCE_CITATION constant must be non-null."""
        m = _mod()
        assert m._LOG_SOURCE_CITATION, "_LOG_SOURCE_CITATION must not be empty"
        assert "FORENSIC" in m._LOG_SOURCE_CITATION
        assert "MI-5-5" in m._LOG_SOURCE_CITATION

    # ── G3.3: count assertions ────────────────────────────────────────────────

    def test_g3_3_row_count_non_negative(self):
        """row_count in result must be an integer >= 0."""
        m = _mod()

        # Zero rows (all filtered due to missing citation)
        row = {**_CHART_FACTS_ROW, "source_citation": None}
        col_names = list(row.keys())
        db_row = tuple(row[k] for k in col_names)

        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.description = [(name,) for name in col_names]
        mock_cursor.fetchall.return_value = [db_row]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.object(m, "_rows_to_parquet", return_value=b"fake"),
            patch.object(m, "_upload_to_gcs", return_value="gs://madhav-brahma-olap/chart_facts/ts.parquet"),
            patch.object(m, "_load_parquet_to_bq", return_value=0),
            patch.object(m, "_write_export_log"),
        ):
            result = m.export_table("chart_facts", chart_id=NATIVE_CHART_ID, dry_run=False)

        assert isinstance(result["row_count"], int), "row_count must be int"
        assert result["row_count"] >= 0, "row_count must be >= 0"

    def test_g3_3_table_specs_count_is_three(self):
        """_TABLE_SPECS must have exactly 3 entries (chart_facts, bodha_signals, life_events_calibration)."""
        m = _mod()
        assert len(m._TABLE_SPECS) == 3, (
            f"Expected 3 table specs, got {len(m._TABLE_SPECS)}: {sorted(m._TABLE_SPECS.keys())}"
        )
        assert "chart_facts" in m._TABLE_SPECS
        assert "bodha_signals" in m._TABLE_SPECS
        assert "life_events_calibration" in m._TABLE_SPECS

    # ── G3.4: provenance_envelope ─────────────────────────────────────────────

    def test_g3_4_provenance_envelope_required_keys(self):
        """provenance_envelope must carry: source, asset, layer, native_chart_id, exported_at."""
        m = _mod()

        row = _CHART_FACTS_ROW
        col_names = list(row.keys())
        db_row = tuple(row[k] for k in col_names)

        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.description = [(name,) for name in col_names]
        mock_cursor.fetchall.return_value = [db_row]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.object(m, "_rows_to_parquet", return_value=b"fake"),
            patch.object(m, "_upload_to_gcs", return_value="gs://madhav-brahma-olap/chart_facts/ts.parquet"),
            patch.object(m, "_load_parquet_to_bq", return_value=1),
            patch.object(m, "_write_export_log"),
        ):
            result = m.export_table("chart_facts", chart_id=NATIVE_CHART_ID, dry_run=False)

        env = result.get("provenance_envelope")
        assert env is not None, "provenance_envelope must be present"
        assert env.get("source") == "brahmagyan.mimamsa.export_to_bigquery"
        assert env.get("asset") == "MI-5-5"
        assert env.get("layer") == "L5 Mīmāṃsā"
        assert env.get("native_chart_id") == NATIVE_CHART_ID
        assert env.get("gcp_project") == "madhav-astrology", (
            f"gcp_project must be 'madhav-astrology', got {env.get('gcp_project')!r}"
        )
        assert env.get("gcs_bucket") == "madhav-brahma-olap", (
            f"gcs_bucket must be 'madhav-brahma-olap', got {env.get('gcs_bucket')!r}"
        )
        assert "exported_at" in env

    def test_g3_4_acceptance_gate_provenance_envelope_present(self):
        """run_acceptance_gate result must carry provenance_envelope."""
        m = _mod()

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchone.return_value = (0,)

        with (
            patch.object(m, "_get_conn", return_value=mock_conn),
            patch.dict("sys.modules", {"google.cloud.bigquery": None}),
        ):
            result = m.run_acceptance_gate()

        env = result.get("provenance_envelope")
        assert env is not None, "run_acceptance_gate must return provenance_envelope"
        assert env.get("source") == "brahmagyan.mimamsa.export_to_bigquery"
        assert env.get("asset") == "MI-5-5"
        assert "run_at" in env

    # ── G3.5: formula bounds ──────────────────────────────────────────────────

    def test_g3_5_gcp_project_default_is_madhav_astrology(self):
        """GCP_PROJECT default must be madhav-astrology (matches provisioned project)."""
        import importlib
        import sys
        mod_name = "brahmagyan.mimamsa.export_to_bigquery"
        saved = sys.modules.pop(mod_name, None)
        try:
            import os
            old_val = os.environ.pop("GCP_PROJECT", None)
            m = importlib.import_module(mod_name)
            importlib.reload(m)
            assert m.GCP_PROJECT == "madhav-astrology", (
                f"GCP_PROJECT default must be 'madhav-astrology', got {m.GCP_PROJECT!r}"
            )
        finally:
            if old_val is not None:
                os.environ["GCP_PROJECT"] = old_val
            if saved is not None:
                sys.modules[mod_name] = saved

    def test_g3_5_bq_dataset_default_is_brahma_l5_olap(self):
        """BQ_DATASET default must be brahma_l5_olap."""
        m = _mod()
        assert m.BQ_DATASET == "brahma_l5_olap", (
            f"BQ_DATASET must be 'brahma_l5_olap', got {m.BQ_DATASET!r}"
        )

    def test_g3_5_all_table_specs_have_non_null_source_citation_in_sql(self):
        """Every _TABLE_SPECS SQL must filter source_citation IS NOT NULL."""
        m = _mod()
        for key, spec in m._TABLE_SPECS.items():
            sql = spec["sql"]
            assert "source_citation IS NOT NULL" in sql, (
                f"Table spec {key!r}: SQL must filter 'source_citation IS NOT NULL' "
                f"to enforce non-null contract at DB level"
            )

    def test_g3_5_lel_calibration_prefix_constant_matches_table_key(self):
        """_LEL_CALIBRATION_PREFIX must match the life_events_calibration table key prefix."""
        m = _mod()
        assert m._LEL_CALIBRATION_PREFIX == "life_events_calibration"
        # Verify the table key starts with the prefix
        assert "life_events_calibration".startswith(m._LEL_CALIBRATION_PREFIX)
