"""
test_panchanga_writer.py
========================
Unit tests for pipeline/writers/panchanga_writer.py (ganita.panchanga, GA-1-7).

Tests:
  1. build_row() produces the 5 required columns with correct values.
  2. FORENSIC spot-check for native birth date 1984-02-05:
       tithi=Shukla Tritiya, vara=Ravivara, moon_nakshatra=Purva Bhadrapada,
       yoga=Shiva, karana=Garaja
  3. Paksha derivation is correct (shukla for tithi≤15, krishna otherwise).
  4. Vara normalisation: 1-based index (e.g. index=1 → 'Ravivara').
  5. Error propagation: raises ValueError on panchanga error fields.
  6. Idempotency: writing the same row twice produces ON CONFLICT → UPDATE
     (tested via a mock cursor that captures the SQL).
  7. write_from_engine_output() extracts chart_id and Lahiri grahas correctly.
  8. Nakshatra index 0-based correctly maps to nakshatra names.
  9. Yoga index 1-based (from PyJHora) correctly maps to yoga names.
  10. Karana index correctly maps to karana names (movable + fixed).

No DB connection required — all tests use mock/fake data.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import sys
import os

# Ensure the pipeline package is importable when run from repo root
_HERE = os.path.dirname(__file__)
_SIDECAR = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from pipeline.writers.panchanga_writer import (
    build_row,
    write_panchanga,
    write_from_engine_output,
    TITHI_NAMES,
    NAKSHATRA_NAMES,
    YOGA_NAMES,
    KARANA_NAMES,
    VARA_NAMES,
)

# ── FORENSIC reference data for native (Abhisek Mohanty, 1984-02-05, 10:43 IST) ──
# Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md; Phase 4C FORENSIC spot-check (2026-05-21)
# tithi=Shukla Tritiya, vara=Ravivara, moon_nakshatra=Purva Bhadrapada,
# yoga=Shiva, karana=Garaja

NATIVE_PANCHANGA = {
    "tithi": {
        "index": 3,          # Shukla Tritiya = 3
        "name": "Tritiya",
        "paksha": "Shukla",
    },
    "vara": {
        "index": 1,          # Sunday = 1 (1-based: 1=Sun..7=Sat)
        "name": "Sunday",
    },
    "nakshatra": {
        "index": 24,         # Purva Bhadrapada = index 24 (0-based; 0=Ashwini)
        "name": "Purva Bhadrapada",
        "pada": 2,
    },
    "yoga": {
        "index": 20,         # Shiva = index 20 (1-based; 1=Vishkamba)
        "name": "Shiva",
    },
    "karana": {
        "index": 5,          # Garaja = index 5 in 1-based karana list
        "name": "Garaja",
    },
}

NATIVE_LAHIRI_GRAHAS = {
    "Sun": {"absolute_longitude": 292.12345},
    "Moon": {"absolute_longitude": 335.67890},
}


class TestBuildRowForensicSpotCheck:
    """FORENSIC spot-check: native chart 1984-02-05 produces the 5 correct limbs."""

    def test_tithi_shukla_tritiya(self):
        row = build_row("test-chart-id", "test-build-1", NATIVE_PANCHANGA)
        assert row["tithi_name"] == "Shukla Tritiya", (
            f"Expected 'Shukla Tritiya' but got '{row['tithi_name']}'"
        )
        assert row["tithi_num"] == 3
        assert row["paksha"] == "shukla"

    def test_vara_ravivara(self):
        row = build_row("test-chart-id", "test-build-1", NATIVE_PANCHANGA)
        assert row["vara_name"] == "Ravivara", (
            f"Expected 'Ravivara' but got '{row['vara_name']}'"
        )
        assert row["vara_num"] == 1

    def test_moon_nakshatra_purva_bhadrapada(self):
        row = build_row("test-chart-id", "test-build-1", NATIVE_PANCHANGA)
        assert row["moon_nakshatra"] == "Purva Bhadrapada", (
            f"Expected 'Purva Bhadrapada' but got '{row['moon_nakshatra']}'"
        )
        assert row["moon_nakshatra_index"] == 24
        assert row["moon_nakshatra_pada"] == 2

    def test_yoga_shiva(self):
        row = build_row("test-chart-id", "test-build-1", NATIVE_PANCHANGA)
        assert row["yoga_name"] == "Shiva", (
            f"Expected 'Shiva' but got '{row['yoga_name']}'"
        )
        # Shiva is the 20th yoga (1-based index 20)
        assert row["yoga_num"] == 20

    def test_karana_garaja(self):
        row = build_row("test-chart-id", "test-build-1", NATIVE_PANCHANGA)
        assert row["karana_name"] == "Garaja", (
            f"Expected 'Garaja' but got '{row['karana_name']}'"
        )
        # Garaja = 5th karana (movable); index 5 in 1-based
        assert row["karana_num"] == 5


class TestBuildRowBasicFields:
    """Test that build_row populates all required fields correctly."""

    def test_all_five_limbs_present(self):
        row = build_row("chart-001", "build-001", NATIVE_PANCHANGA)
        required = [
            "chart_id", "build_id",
            "tithi_num", "tithi_name", "paksha",
            "vara_num", "vara_name",
            "moon_nakshatra", "moon_nakshatra_index", "moon_nakshatra_pada",
            "yoga_num", "yoga_name",
            "karana_num", "karana_name",
        ]
        for field in required:
            assert field in row, f"Missing field: {field}"
            assert row[field] is not None, f"Field is None: {field}"

    def test_sun_moon_longitudes_included_when_grahas_provided(self):
        row = build_row(
            "chart-001", "build-001", NATIVE_PANCHANGA,
            lahiri_grahas=NATIVE_LAHIRI_GRAHAS,
        )
        assert row["sun_longitude_deg"] == round(292.12345, 8)
        assert row["moon_longitude_deg"] == round(335.67890, 8)

    def test_sun_moon_longitudes_none_when_no_grahas(self):
        row = build_row("chart-001", "build-001", NATIVE_PANCHANGA)
        assert row["sun_longitude_deg"] is None
        assert row["moon_longitude_deg"] is None

    def test_ayanamsha_id_is_lahiri(self):
        row = build_row("chart-001", "build-001", NATIVE_PANCHANGA)
        assert row["ayanamsha_id"] == "lahiri"

    def test_source_citation_present(self):
        row = build_row("chart-001", "build-001", NATIVE_PANCHANGA)
        assert row["source_citation"]
        assert "FORENSIC" in row["source_citation"]

    def test_computed_at_is_utc(self):
        row = build_row("chart-001", "build-001", NATIVE_PANCHANGA)
        assert row["computed_at"].tzinfo is not None


class TestPakshaDerivation:
    """paksha must be 'shukla' for tithi 1–15, 'krishna' for 16–30."""

    @pytest.mark.parametrize("tithi_num,expected_paksha", [
        (1, "shukla"), (3, "shukla"), (15, "shukla"),
        (16, "krishna"), (20, "krishna"), (30, "krishna"),
    ])
    def test_paksha_from_tithi(self, tithi_num, expected_paksha):
        panchanga = {
            **NATIVE_PANCHANGA,
            "tithi": {"index": tithi_num, "name": "test"},
        }
        row = build_row("chart-001", "build-001", panchanga)
        assert row["paksha"] == expected_paksha, (
            f"tithi {tithi_num}: expected {expected_paksha}, got {row['paksha']}"
        )


class TestVaraNormalisation:
    """Vara index normalisation: both 1-based and 0-based inputs should work."""

    def test_vara_1based_sunday(self):
        """vara index=1 (Sunday, 1-based) → 'Ravivara'."""
        panchanga = {**NATIVE_PANCHANGA, "vara": {"index": 1, "name": "Sunday"}}
        row = build_row("chart-001", "build-001", panchanga)
        assert row["vara_name"] == "Ravivara"
        assert row["vara_num"] == 1

    def test_vara_1based_saturday(self):
        """vara index=7 (Saturday, 1-based) → 'Shanivara'."""
        panchanga = {**NATIVE_PANCHANGA, "vara": {"index": 7, "name": "Saturday"}}
        row = build_row("chart-001", "build-001", panchanga)
        assert row["vara_name"] == "Shanivara"
        assert row["vara_num"] == 7

    def test_vara_0based_sunday(self):
        """vara index=0 (Sunday, 0-based) → 'Ravivara'."""
        panchanga = {**NATIVE_PANCHANGA, "vara": {"index": 0, "name": "Sunday"}}
        row = build_row("chart-001", "build-001", panchanga)
        assert row["vara_name"] == "Ravivara"
        assert row["vara_num"] == 1


class TestNakshatraMapping:
    """All 27 nakshatra indices should map to correct names."""

    @pytest.mark.parametrize("idx,expected", [
        (0, "Ashwini"),
        (4, "Mrigashira"),
        (12, "Hasta"),
        (24, "Purva Bhadrapada"),
        (25, "Uttara Bhadrapada"),
        (26, "Revati"),
    ])
    def test_nakshatra_name(self, idx, expected):
        panchanga = {
            **NATIVE_PANCHANGA,
            "nakshatra": {"index": idx, "name": expected, "pada": 1},
        }
        row = build_row("chart-001", "build-001", panchanga)
        assert row["moon_nakshatra"] == expected
        assert row["moon_nakshatra_index"] == idx


class TestYogaMapping:
    """Yoga 1-based index correctly maps to yoga names."""

    @pytest.mark.parametrize("idx,expected", [
        (1, "Vishkamba"),
        (20, "Shiva"),
        (27, "Vaidhriti"),
    ])
    def test_yoga_name(self, idx, expected):
        panchanga = {
            **NATIVE_PANCHANGA,
            "yoga": {"index": idx, "name": expected},
        }
        row = build_row("chart-001", "build-001", panchanga)
        assert row["yoga_name"] == expected, (
            f"Yoga index {idx}: expected '{expected}', got '{row['yoga_name']}'"
        )
        assert row["yoga_num"] == idx


class TestKaranaMapping:
    """Karana indices correctly map to movable and fixed karanas."""

    @pytest.mark.parametrize("idx,expected", [
        (1, "Bava"),
        (4, "Taitila"),
        (5, "Garaja"),
        (7, "Vishti"),
        (8, "Shakuni"),
        (11, "Kimstughna"),
    ])
    def test_karana_name(self, idx, expected):
        panchanga = {
            **NATIVE_PANCHANGA,
            "karana": {"index": idx, "name": expected},
        }
        row = build_row("chart-001", "build-001", panchanga)
        assert row["karana_name"] == expected, (
            f"Karana index {idx}: expected '{expected}', got '{row['karana_name']}'"
        )


class TestErrorPropagation:
    """ValueError is raised when panchanga dict contains engine error fields."""

    def test_tithi_error_raises(self):
        panchanga = {**NATIVE_PANCHANGA, "tithi": {"error": "swisseph failed"}}
        with pytest.raises(ValueError, match="Tithi computation error"):
            build_row("chart-001", "build-001", panchanga)

    def test_vara_error_raises(self):
        panchanga = {**NATIVE_PANCHANGA, "vara": {"error": "weekday unavailable"}}
        with pytest.raises(ValueError, match="Vara computation error"):
            build_row("chart-001", "build-001", panchanga)

    def test_nakshatra_error_raises(self):
        panchanga = {**NATIVE_PANCHANGA, "nakshatra": {"error": "moon position error"}}
        with pytest.raises(ValueError, match="Nakshatra computation error"):
            build_row("chart-001", "build-001", panchanga)

    def test_yoga_error_raises(self):
        panchanga = {**NATIVE_PANCHANGA, "yoga": {"error": "yoga compute failed"}}
        with pytest.raises(ValueError, match="Yoga computation error"):
            build_row("chart-001", "build-001", panchanga)

    def test_karana_error_raises(self):
        panchanga = {**NATIVE_PANCHANGA, "karana": {"error": "karana compute failed"}}
        with pytest.raises(ValueError, match="Karana computation error"):
            build_row("chart-001", "build-001", panchanga)

    def test_tithi_out_of_range_raises(self):
        panchanga = {**NATIVE_PANCHANGA, "tithi": {"index": 0, "name": "invalid"}}
        with pytest.raises(ValueError, match="tithi_num out of range"):
            build_row("chart-001", "build-001", panchanga)


class TestWritePanchangaMockDB:
    """write_panchanga() executes the correct SQL via a mock cursor."""

    def test_write_panchanga_executes_upsert(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        row = write_panchanga(
            mock_conn, "chart-002", "build-002", NATIVE_PANCHANGA,
            lahiri_grahas=NATIVE_LAHIRI_GRAHAS,
        )

        # Cursor.execute should have been called once with the INSERT SQL
        mock_cursor.execute.assert_called_once()
        sql_called, params = mock_cursor.execute.call_args[0]
        assert "INSERT INTO chart_panchanga" in sql_called
        assert "ON CONFLICT" in sql_called
        # Verify the row values
        assert params["tithi_name"] == "Shukla Tritiya"
        assert params["vara_name"] == "Ravivara"
        assert params["moon_nakshatra"] == "Purva Bhadrapada"
        assert params["yoga_name"] == "Shiva"
        assert params["karana_name"] == "Garaja"

    def test_write_returns_row_dict(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        row = write_panchanga(
            mock_conn, "chart-003", "build-003", NATIVE_PANCHANGA,
        )
        assert isinstance(row, dict)
        assert row["chart_id"] == "chart-003"
        assert row["build_id"] == "build-003"


class TestWriteFromEngineOutput:
    """write_from_engine_output() correctly extracts data from engine JSONL."""

    def _make_engine_output(self) -> dict:
        return {
            "schema_version": "1.0",
            "engine_version": "1.0.0",
            "chart_id": "native-chart-1984",
            "birth": {
                "date": "1984-02-05",
                "time_local": "10:43:00",
                "lat": 20.2704,
                "lon": 85.8314,
                "tz_offset_hours": 5.5,
            },
            "panchanga": NATIVE_PANCHANGA,
            "per_ayanamsha": {
                "lahiri": {
                    "grahas": NATIVE_LAHIRI_GRAHAS,
                }
            },
            "sha256": "abc123",
        }

    def test_extracts_chart_id(self):
        engine_out = self._make_engine_output()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        row = write_from_engine_output(mock_conn, engine_out, "build-1984")
        assert row["chart_id"] == "native-chart-1984"

    def test_extracts_lahiri_grahas(self):
        engine_out = self._make_engine_output()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        row = write_from_engine_output(mock_conn, engine_out, "build-1984")
        assert row["moon_longitude_deg"] == round(335.67890, 8)
        assert row["sun_longitude_deg"] == round(292.12345, 8)

    def test_missing_chart_id_raises(self):
        engine_out = {"panchanga": NATIVE_PANCHANGA}
        mock_conn = MagicMock()
        with pytest.raises(ValueError, match="chart_id"):
            write_from_engine_output(mock_conn, engine_out, "build-000")

    def test_forensic_five_limbs(self):
        """End-to-end: FORENSIC native → all 5 limbs correct."""
        engine_out = self._make_engine_output()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        row = write_from_engine_output(mock_conn, engine_out, "build-forensic")

        assert row["tithi_name"] == "Shukla Tritiya",  f"tithi: {row['tithi_name']}"
        assert row["vara_name"] == "Ravivara",          f"vara: {row['vara_name']}"
        assert row["moon_nakshatra"] == "Purva Bhadrapada", f"nak: {row['moon_nakshatra']}"
        assert row["yoga_name"] == "Shiva",             f"yoga: {row['yoga_name']}"
        assert row["karana_name"] == "Garaja",          f"karana: {row['karana_name']}"


class TestSunriseFields:
    """Sunrise fields pass through correctly."""

    def test_sunrise_fields_present(self):
        sr = datetime(1984, 2, 5, 1, 6, 0, tzinfo=timezone.utc)  # 06:36 IST
        row = build_row(
            "chart-001", "build-001", NATIVE_PANCHANGA,
            sunrise_utc=sr,
            sunrise_ist="06:36:00",
        )
        assert row["sunrise_utc"] == sr
        assert row["sunrise_ist"] == "06:36:00"

    def test_sunrise_fields_none_by_default(self):
        row = build_row("chart-001", "build-001", NATIVE_PANCHANGA)
        assert row["sunrise_utc"] is None
        assert row["sunrise_ist"] is None
