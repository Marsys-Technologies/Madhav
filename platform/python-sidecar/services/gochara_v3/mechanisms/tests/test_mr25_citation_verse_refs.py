"""
test_mr25_citation_verse_refs.py — MR-25 TDD gate test.

MR-25 remediation: Citations resolve to verse_refs in gochara serving.

Three citation sources were cataloged in the gochara windows serving layer
(w29_citation_resolution.py) but never resolved to classical_text_chunks
verse_refs. This test enforces the MR-25 gate condition:

  GATE: at minimum one citation string that maps to a non-empty verse_refs
        list in the bg_gochara_citation_resolution table (migration 565).

These tests are STATIC (no DB required) — they validate:

  AC-1. The migration file 565 exists and creates bg_gochara_citation_resolution.
  AC-2. The migration seeds at least one row for a known cited citation string
        (BPHS Ch.26 — Graha Drishti) that maps to a real classical_text_chunks
        chunk_id (bphs_ch26_v001, verse_ref CH26:V1-V4).
  AC-3. Every seeded row has citation_string, chunk_id, verse_ref, and text_id.
  AC-4. The serving module (register_gochara_windows.ts) references
        bg_gochara_citation_resolution (proves the serving join is present).
  AC-5. route.ts ALLOWED_TABLES includes 'bg_gochara_citation_resolution'
        (proves the MCP DB proxy whitelist was updated).
  AC-6. At least one seeded citation string matches a constant in citations.py
        (proves the resolution is grounded in the actual gochara citation catalog).

All checks are file-reads: no pg connection, no live DB, pure static analysis.
The tests FAIL before migration 565 and register_gochara_windows.ts are updated.
"""
from __future__ import annotations

import os
import re

import pytest


# ---------------------------------------------------------------------------
# Paths — all absolute, relative to this file's location in the repo
# ---------------------------------------------------------------------------

_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "..")
)
_MIGRATION_PATH = os.path.join(
    _REPO_ROOT, "platform", "supabase", "migrations",
    "565_bg_gochara_citation_resolution.sql",
)
_GOCHARA_WINDOWS_TS = os.path.join(
    _REPO_ROOT, "platform-mcp", "src", "tools", "retrieval",
    "register_gochara_windows.ts",
)
_ROUTE_TS = os.path.join(
    _REPO_ROOT, "platform", "src", "app", "api", "mcp", "db", "query", "route.ts",
)
_CITATIONS_PY = os.path.join(
    _REPO_ROOT, "platform", "python-sidecar", "services", "gochara_grammar",
    "citations.py",
)


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# AC-1: migration file exists and creates the resolution table
# ---------------------------------------------------------------------------

class TestMigrationExists:
    def test_migration_565_file_exists(self):
        """Migration 565 must exist at the canonical supabase/migrations path."""
        assert os.path.isfile(_MIGRATION_PATH), (
            f"Migration 565 not found at {_MIGRATION_PATH} — "
            "run the MR-25 implementation to create it."
        )

    def test_migration_creates_bg_gochara_citation_resolution(self):
        """Migration 565 must CREATE TABLE bg_gochara_citation_resolution."""
        sql = _read(_MIGRATION_PATH)
        assert "bg_gochara_citation_resolution" in sql, (
            "Migration 565 does not mention bg_gochara_citation_resolution"
        )
        assert re.search(
            r"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?bg_gochara_citation_resolution",
            sql, re.IGNORECASE
        ), "Migration 565 lacks a CREATE TABLE for bg_gochara_citation_resolution"

    def test_migration_has_citation_string_column(self):
        """Resolution table must have a citation_string primary key column."""
        sql = _read(_MIGRATION_PATH)
        assert "citation_string" in sql, (
            "bg_gochara_citation_resolution must have a citation_string column"
        )

    def test_migration_has_verse_ref_column(self):
        """Resolution table must have a verse_ref column (the gate field)."""
        sql = _read(_MIGRATION_PATH)
        assert "verse_ref" in sql, (
            "bg_gochara_citation_resolution must carry a verse_ref column"
        )

    def test_migration_has_chunk_id_column(self):
        """Resolution table must carry chunk_id linking to classical_text_chunks."""
        sql = _read(_MIGRATION_PATH)
        assert "chunk_id" in sql, (
            "bg_gochara_citation_resolution must carry a chunk_id column"
        )


# ---------------------------------------------------------------------------
# AC-2: at least one seeded row maps BPHS Ch.26 citation to its chunk
# ---------------------------------------------------------------------------

class TestMigrationSeeds:
    def test_seeds_bphs_ch26_graha_drishti(self):
        """Migration seeds the BPHS Ch.26 Graha Drishti citation (verified in corpus)."""
        sql = _read(_MIGRATION_PATH)
        # The GRAHA_DRISHTI_BPHS_26 constant value starts with "BPHS Ch.26"
        assert "BPHS Ch.26" in sql, (
            "Migration 565 must seed at least one BPHS Ch.26 row "
            "(GRAHA_DRISHTI_BPHS_26 / GRAHA_DRISHTI_RASI_BPHS_26 are in corpus)"
        )

    def test_seeds_bphs_ch26_chunk_id(self):
        """Migration seeds chunk_id 'bphs_ch26_v001' (confirmed in classical_text_chunks corpus)."""
        sql = _read(_MIGRATION_PATH)
        assert "bphs_ch26_v001" in sql, (
            "Migration 565 must reference chunk_id 'bphs_ch26_v001' — "
            "BPHS Ch.26 v1-4 is in the classical_text_chunks seed corpus "
            "(l0_texts.py SEED_CHUNKS line ~531)"
        )

    def test_seeds_bphs_ch26_verse_ref(self):
        """Migration seeds verse_ref 'CH26:V1-V4' (the BPHS Ch.26 chunk's verse_ref)."""
        sql = _read(_MIGRATION_PATH)
        assert "CH26:V1" in sql, (
            "Migration 565 must include verse_ref 'CH26:V1-V4' for the BPHS Ch.26 row"
        )

    def test_migration_uses_on_conflict_idempotent_pattern(self):
        """Migration must use ON CONFLICT / IF NOT EXISTS — never a bare INSERT."""
        sql = _read(_MIGRATION_PATH)
        assert re.search(r"ON\s+CONFLICT", sql, re.IGNORECASE), (
            "Migration 565 must use ON CONFLICT (idempotent seed pattern, "
            "per §N.3 and mig-528 verified-before-seeded pattern)"
        )

    def test_migration_wrapped_in_transaction(self):
        """Migration must be wrapped in BEGIN/COMMIT."""
        sql = _read(_MIGRATION_PATH)
        assert re.search(r"\bBEGIN\b", sql, re.IGNORECASE), (
            "Migration 565 must wrap its DDL+DML in a transaction (BEGIN)"
        )
        assert re.search(r"\bCOMMIT\b", sql, re.IGNORECASE), (
            "Migration 565 must wrap its DDL+DML in a transaction (COMMIT)"
        )

    def test_migration_has_bphs_ch27_row(self):
        """Migration seeds BPHS Ch.27 for VAKRA_RETROGRADE_BPHS_27 citation."""
        sql = _read(_MIGRATION_PATH)
        assert "bphs_ch27" in sql, (
            "Migration 565 must seed BPHS Ch.27 (VAKRA_RETROGRADE_BPHS_27 — "
            "Ch.27 v1-3 is in the classical_text_chunks corpus)"
        )


# ---------------------------------------------------------------------------
# AC-3: seeded rows have all required columns
# ---------------------------------------------------------------------------

class TestMigrationRowShape:
    def test_seeds_have_text_id(self):
        """INSERT rows must supply text_id (references classical_texts)."""
        sql = _read(_MIGRATION_PATH)
        # text_id must appear in the column list of the INSERT
        assert "text_id" in sql, (
            "Migration 565 INSERT must include text_id column"
        )

    def test_seeds_have_source_citation_ref(self):
        """INSERT rows should include source_citation for audit trail."""
        sql = _read(_MIGRATION_PATH)
        assert "source_citation" in sql, (
            "Migration 565 INSERT should include source_citation column"
        )


# ---------------------------------------------------------------------------
# AC-4: register_gochara_windows.ts references bg_gochara_citation_resolution
# ---------------------------------------------------------------------------

class TestServingJoinPresent:
    def test_gochara_windows_ts_references_resolution_table(self):
        """register_gochara_windows.ts must reference bg_gochara_citation_resolution."""
        ts = _read(_GOCHARA_WINDOWS_TS)
        assert "bg_gochara_citation_resolution" in ts, (
            "register_gochara_windows.ts does not reference bg_gochara_citation_resolution — "
            "the MR-25 serving join is missing. Add a lookup function that queries "
            "this table and enriches served windows with verse_refs."
        )

    def test_gochara_windows_ts_references_verse_refs(self):
        """register_gochara_windows.ts must output verse_refs in the served response."""
        ts = _read(_GOCHARA_WINDOWS_TS)
        assert "verse_refs" in ts, (
            "register_gochara_windows.ts does not mention verse_refs — "
            "served windows must carry verse_refs when resolved."
        )


# ---------------------------------------------------------------------------
# AC-5: route.ts ALLOWED_TABLES includes bg_gochara_citation_resolution
# ---------------------------------------------------------------------------

class TestWhitelistEntry:
    def test_route_ts_whitelists_resolution_table(self):
        """route.ts ALLOWED_TABLES must include 'bg_gochara_citation_resolution'."""
        ts = _read(_ROUTE_TS)
        assert "'bg_gochara_citation_resolution'" in ts, (
            "route.ts ALLOWED_TABLES does not include 'bg_gochara_citation_resolution' — "
            "the MCP DB proxy will 400 every verse_refs lookup. "
            "Add the entry alongside 'kala_gochara_windows' in route.ts."
        )


# ---------------------------------------------------------------------------
# AC-6: at least one seeded citation string is a citations.py constant value
# ---------------------------------------------------------------------------

class TestCitationsGrounding:
    def test_seeded_citations_include_at_least_one_citations_py_constant(self):
        """At least one seeded citation string must match a citations.py constant value."""
        import services.gochara_grammar.citations as _C

        sql = _read(_MIGRATION_PATH)

        matched = []
        for name in _C.__all__:
            value = getattr(_C, name)
            # Check if any substring of the constant's value appears in the migration.
            # We check the first 30 chars to avoid false negatives from long strings.
            if value[:30] in sql:
                matched.append(name)

        assert len(matched) >= 1, (
            f"No citations.py constant value found in migration 565. "
            f"Constants checked: {_C.__all__}. "
            "Migration must seed rows for at least one known gochara citation string."
        )
