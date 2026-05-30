"""
Tests for Migration 149 — UTEE Envelope Column Additions.

All tests are static / unit-level — no database connection required.
Validates:
  1. Migration file exists and is well-formed
  2. Each expected table name appears in the migration
  3. Each core UTEE column appears with the DO $$ BEGIN ... EXCEPTION pattern
  4. Idempotency pattern (EXCEPTION WHEN duplicate_column THEN NULL) is used
     for every ADD COLUMN statement
  5. utee_schema.py registry is self-consistent

Stream D — UTEE-S1 [BUILD-ORCH-STREAM-D-UTEE-S1]
"""

from __future__ import annotations

import os
import re
import sys

import pytest

# ---------------------------------------------------------------------------
# Path wiring — allow import of pipeline modules without installing the pkg
# ---------------------------------------------------------------------------
_PIPELINE_ROOT = os.path.join(os.path.dirname(__file__), "..")
if _PIPELINE_ROOT not in sys.path:
    sys.path.insert(0, _PIPELINE_ROOT)

from utee_schema import (  # noqa: E402
    UTEE_COLUMNS,
    UTEE_EXTRA_COLUMNS,
    UTEE_TABLES,
    all_columns_for_table,
    table_for_asset,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_MIGRATIONS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../migrations")
)
_MIGRATION_FILE = os.path.join(_MIGRATIONS_DIR, "149_utee_envelope_columns.sql")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _load_migration() -> str:
    with open(_MIGRATION_FILE, encoding="utf-8") as fh:
        return fh.read()


# ===========================================================================
# T01 — Migration file exists
# ===========================================================================

class TestMigrationFileExists:
    def test_file_exists(self) -> None:
        assert os.path.isfile(_MIGRATION_FILE), (
            f"Migration file not found: {_MIGRATION_FILE}"
        )

    def test_file_non_empty(self) -> None:
        size = os.path.getsize(_MIGRATION_FILE)
        assert size > 500, f"Migration file suspiciously small: {size} bytes"


# ===========================================================================
# T02 — All 7 target tables appear in the migration
# ===========================================================================

class TestAllTablesPresent:
    @pytest.mark.parametrize("table_name", list(UTEE_TABLES.values()))
    def test_table_referenced(self, table_name: str) -> None:
        sql = _load_migration()
        assert table_name in sql, (
            f"Table '{table_name}' not referenced in migration 149"
        )


# ===========================================================================
# T03 — Core UTEE columns appear for every table
# ===========================================================================

# A subset of the most critical core columns that MUST appear for every table.
_REQUIRED_CORE_COLS = [
    "severity_normalized_0_1",
    "confidence_normalized_0_1",
    "confidence_class",
    "cross_ayanamsha_stability_score",
    "m6_outcome_tracking_placeholder_jsonb",
    "channel_render_priority_jsonb",
]


class TestCoreCoverage:
    @pytest.mark.parametrize("col", _REQUIRED_CORE_COLS)
    def test_core_column_in_migration(self, col: str) -> None:
        sql = _load_migration()
        assert col in sql, f"Core UTEE column '{col}' missing from migration 149"

    def test_all_utee_columns_present(self) -> None:
        sql = _load_migration()
        missing = [col for col in UTEE_COLUMNS if col not in sql]
        assert not missing, f"Core UTEE columns missing from migration: {missing}"


# ===========================================================================
# T04 — Idempotency pattern enforced on every ADD COLUMN statement
# ===========================================================================

class TestIdempotencyPattern:
    def test_no_bare_add_column(self) -> None:
        """Every ADD COLUMN must be wrapped in DO $$ BEGIN...EXCEPTION block.

        Strategy: strip SQL comment lines, then count ADD COLUMN statements
        and compare to EXCEPTION WHEN duplicate_column occurrences — must be equal.
        """
        raw = _load_migration()
        # Strip single-line SQL comments so header documentation doesn't skew counts
        non_comment_lines = [
            line for line in raw.splitlines()
            if not line.lstrip().startswith("--")
        ]
        sql = "\n".join(non_comment_lines)
        add_col_count = len(re.findall(r"\bADD COLUMN\b", sql, re.IGNORECASE))
        exception_count = len(
            re.findall(r"EXCEPTION WHEN duplicate_column THEN NULL", sql, re.IGNORECASE)
        )
        assert add_col_count == exception_count, (
            f"ADD COLUMN count ({add_col_count}) != "
            f"EXCEPTION WHEN duplicate_column count ({exception_count}). "
            "Every ADD COLUMN must be wrapped in idempotent DO $$ BEGIN...END $$."
        )

    def test_do_block_pattern_present(self) -> None:
        sql = _load_migration()
        assert "DO $$" in sql or "DO $" in sql, (
            "Migration does not use DO $$ BEGIN...END $$ blocks"
        )

    def test_exception_pattern_used(self) -> None:
        sql = _load_migration()
        assert "EXCEPTION WHEN duplicate_column THEN NULL" in sql, (
            "Migration does not use the idempotent EXCEPTION WHEN duplicate_column pattern"
        )


# ===========================================================================
# T05 — utee_schema.py registry consistency
# ===========================================================================

class TestSchemaRegistryConsistency:
    def test_utee_tables_has_seven_entries(self) -> None:
        assert len(UTEE_TABLES) == 7, (
            f"Expected 7 UTEE table entries, got {len(UTEE_TABLES)}"
        )

    def test_utee_core_columns_non_empty(self) -> None:
        assert len(UTEE_COLUMNS) >= 15, (
            f"Expected >= 15 core UTEE columns, got {len(UTEE_COLUMNS)}"
        )

    def test_all_extra_column_tables_are_known(self) -> None:
        known_tables = set(UTEE_TABLES.values())
        for tbl in UTEE_EXTRA_COLUMNS:
            assert tbl in known_tables, (
                f"UTEE_EXTRA_COLUMNS references unknown table '{tbl}'"
            )

    def test_table_for_asset_roundtrip(self) -> None:
        for asset_id, table_name in UTEE_TABLES.items():
            assert table_for_asset(asset_id) == table_name

    def test_table_for_asset_unknown_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown UTEE asset id"):
            table_for_asset("ZZZ_NONEXISTENT")

    def test_all_columns_for_table_includes_core(self) -> None:
        for table_name in UTEE_TABLES.values():
            cols = all_columns_for_table(table_name)
            for core_col in UTEE_COLUMNS:
                assert core_col in cols, (
                    f"Core column '{core_col}' missing from all_columns_for_table('{table_name}')"
                )

    def test_all_columns_for_table_includes_extras(self) -> None:
        for table_name, extras in UTEE_EXTRA_COLUMNS.items():
            cols = all_columns_for_table(table_name)
            for extra in extras:
                assert extra in cols, (
                    f"Extra column '{extra}' missing from all_columns_for_table('{table_name}')"
                )

    def test_all_columns_returns_sorted_list(self) -> None:
        for table_name in UTEE_TABLES.values():
            cols = all_columns_for_table(table_name)
            assert cols == sorted(cols), (
                f"all_columns_for_table('{table_name}') is not sorted"
            )


# ===========================================================================
# T06 — Header / provenance comment present
# ===========================================================================

class TestMigrationHeader:
    def test_migration_number_in_header(self) -> None:
        sql = _load_migration()
        assert "Migration 149" in sql, "Migration file header missing 'Migration 149'"

    def test_utee_tag_in_header(self) -> None:
        sql = _load_migration()
        assert "UTEE" in sql, "Migration file header missing 'UTEE' identifier"

    def test_stream_d_tag_in_header(self) -> None:
        sql = _load_migration()
        assert "UTEE-S1" in sql, "Migration file missing Stream-D UTEE-S1 tag"

    def test_temporal_spine_citation_in_header(self) -> None:
        sql = _load_migration()
        assert "TEMPORAL_SPINE_ENHANCEMENTS" in sql, (
            "Migration file missing TEMPORAL_SPINE_ENHANCEMENTS spec citation"
        )
