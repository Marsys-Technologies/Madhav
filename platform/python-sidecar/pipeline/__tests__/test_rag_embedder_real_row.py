"""
test_rag_embedder_real_row.py — Integration test for rag_embedder.embed_chart_document().

This test would have caught the schema drift: rag_embedder writes chart_id/ayanamsha_id/
source_type but the table lacked those columns until migration 163.

Two test layers:
  A. Schema-contract test (no live DB): asserts that the INSERT SQL in
     rag_embedder explicitly names 'chart_id', 'ayanamsha_id', and 'source_type'
     — i.e., the columns are not silently dropped or defaulted to NULL.

  B. Live-DB integration test (requires DATABASE_URL): creates a synthetic
     forensic_render row, calls embed_chart_document(), asserts rag_chunks rows
     appear with the correct chart_id/source_type, then cleans up.

Skips the live-DB test when DATABASE_URL is absent (safe for CI without a DB).
"""
from __future__ import annotations

import inspect
import os
import re
import sys
from contextlib import contextmanager
from typing import Any
import unittest.mock as mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pipeline.writers import rag_embedder

NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"
_HAS_DB = bool(os.environ.get("DATABASE_URL", ""))


# ---------------------------------------------------------------------------
# A. Schema-contract test (no live DB required)
# ---------------------------------------------------------------------------

class TestRagEmbedderSchemaContract:
    """
    Verify that the INSERT statement in rag_embedder explicitly names
    chart_id, ayanamsha_id, and source_type — the columns that triggered
    the schema drift before migration 163.
    """

    def test_insert_names_chart_id_column(self):
        source = inspect.getsource(rag_embedder)
        # The INSERT must name 'chart_id' in the column list, not just in values
        insert_blocks = re.findall(r'INSERT INTO rag_chunks\s*\((.*?)\)', source, re.DOTALL)
        assert insert_blocks, "No INSERT INTO rag_chunks found in rag_embedder source"
        for block in insert_blocks:
            assert 'chart_id' in block, (
                "INSERT INTO rag_chunks missing 'chart_id' column — "
                "schema drift: table lacked chart_id before migration 163"
            )

    def test_insert_names_ayanamsha_id_column(self):
        source = inspect.getsource(rag_embedder)
        insert_blocks = re.findall(r'INSERT INTO rag_chunks\s*\((.*?)\)', source, re.DOTALL)
        assert insert_blocks
        for block in insert_blocks:
            assert 'ayanamsha_id' in block, (
                "INSERT INTO rag_chunks missing 'ayanamsha_id' column"
            )

    def test_insert_names_source_type_column(self):
        source = inspect.getsource(rag_embedder)
        insert_blocks = re.findall(r'INSERT INTO rag_chunks\s*\((.*?)\)', source, re.DOTALL)
        assert insert_blocks
        for block in insert_blocks:
            assert 'source_type' in block, (
                "INSERT INTO rag_chunks missing 'source_type' column"
            )

    def test_embed_returns_correct_chart_id_in_metadata(self):
        """
        Mock test: embed_chart_document() inserts chart_id in the row payload,
        not just in metadata. Captures the positional params of the INSERT.
        """
        sample_md = (
            "## Section One {#s1}\n\nFact: Sun in Capricorn.\n\n"
            "## Section Two {#s2}\n\nFact: Moon in Aquarius.\n"
        )
        rows_inserted: list[dict] = []

        class _FakeCursor:
            def __init__(self):
                pass

            def execute(self, sql: str, params: Any = None):
                if params and "INSERT INTO rag_chunks" in sql:
                    # params positional order:
                    # (id, source_type, chart_id, ayanamsha_id, build_id,
                    #  source_section, text, embedding, metadata, NOW())
                    rows_inserted.append({
                        "id": params[0],
                        "source_type": params[1],
                        "chart_id": params[2],
                        "ayanamsha_id": params[3],
                        "build_id": params[4],
                    })

            def fetchone(self):
                return (sample_md,)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        class _FakeConn:
            autocommit = False

            @contextmanager
            def cursor(self):
                yield _FakeCursor()

            def commit(self):
                pass

            def rollback(self):
                pass

            def close(self):
                pass

        with mock.patch("psycopg.connect", return_value=_FakeConn()), \
             mock.patch.dict(os.environ, {"DATABASE_URL": "postgresql://fake"}):
            result = rag_embedder.embed_chart_document(
                chart_id=NATIVE_CHART_ID,
                ayanamsha_id="lahiri",
                build_id="test-rag-key-build",
                init_vertex=False,
            )

        assert result["source_type"] == "forensic_render"
        assert result["chunks_written"] >= 1, "No chunks written — check the markdown fixture"
        for row in rows_inserted:
            assert row["chart_id"] == NATIVE_CHART_ID, (
                f"chart_id mismatch: expected {NATIVE_CHART_ID!r}, got {row['chart_id']!r}"
            )
            assert row["source_type"] == "forensic_render", (
                f"source_type mismatch: {row['source_type']!r}"
            )
            assert row["ayanamsha_id"] == "lahiri", (
                f"ayanamsha_id mismatch: {row['ayanamsha_id']!r}"
            )


# ---------------------------------------------------------------------------
# B. Live-DB integration test (requires DATABASE_URL)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _HAS_DB, reason="DATABASE_URL not set — skipping live DB test")
class TestRagEmbedderLiveDB:
    """
    Integration test against a real DB. Requires DATABASE_URL.
    Creates a synthetic chart_documents row, runs the embedder, asserts
    rag_chunks rows appear with chart_id=NATIVE_CHART_ID and
    source_type='forensic_render', then cleans up.
    """

    TEST_BUILD_ID = "test-rag-key-schema-check"
    TEST_AYA = "lahiri"
    TEST_CHART_ID = NATIVE_CHART_ID

    SAMPLE_MD = (
        "## Solar Position {#solar}\n\n"
        "Sun in Capricorn at 1°58' — 10th house, debilitated. "
        "Karaka: soul, authority, government.\n\n"
        "## Lunar Position {#lunar}\n\n"
        "Moon in Aquarius at 2°42' — 11th house, neutral. "
        "Nakshatra: Purva Bhadrapada pada 2.\n"
    )

    def _get_db_url(self) -> str:
        return os.environ["DATABASE_URL"]

    def setup_method(self):
        import psycopg
        db_url = self._get_db_url()
        with psycopg.connect(db_url) as conn:
            # Insert a synthetic forensic_render document
            conn.execute(
                """
                INSERT INTO chart_documents
                  (chart_id, ayanamsha_id, document_type, build_id,
                   content_md, content_json, byte_size, rendered_at)
                VALUES (%s, %s, 'forensic_render', %s, %s, '{}', %s, NOW())
                ON CONFLICT (chart_id, ayanamsha_id, document_type, build_id)
                DO UPDATE SET content_md = EXCLUDED.content_md
                """,
                (
                    self.TEST_CHART_ID,
                    self.TEST_AYA,
                    self.TEST_BUILD_ID,
                    self.SAMPLE_MD,
                    len(self.SAMPLE_MD.encode()),
                ),
            )
            # Clean any pre-existing test chunks for this build
            conn.execute(
                "DELETE FROM rag_chunks WHERE chart_id=%s AND ayanamsha_id=%s AND source_type='forensic_render'",
                (self.TEST_CHART_ID, self.TEST_AYA),
            )
            conn.commit()

    def teardown_method(self):
        import psycopg
        db_url = self._get_db_url()
        with psycopg.connect(db_url) as conn:
            conn.execute(
                "DELETE FROM rag_chunks WHERE chart_id=%s AND ayanamsha_id=%s AND source_type='forensic_render'",
                (self.TEST_CHART_ID, self.TEST_AYA),
            )
            conn.execute(
                "DELETE FROM chart_documents WHERE build_id=%s",
                (self.TEST_BUILD_ID,),
            )
            conn.commit()

    def test_embed_chart_document_lands_in_rag_chunks_with_chart_id(self):
        """
        This test would have caught the schema drift before migration 163:
        the INSERT INTO rag_chunks would have raised psycopg.errors.UndefinedColumn
        because chart_id/ayanamsha_id/source_type didn't exist.
        """
        result = rag_embedder.embed_chart_document(
            chart_id=self.TEST_CHART_ID,
            ayanamsha_id=self.TEST_AYA,
            build_id=self.TEST_BUILD_ID,
            db_url=self._get_db_url(),
            init_vertex=False,
        )

        assert result["source_type"] == "forensic_render"
        chunks_written = result["chunks_written"]
        assert chunks_written >= 1, f"embed_chart_document wrote 0 chunks: {result}"

        # Verify the rows landed with correct chart_id and source_type
        import psycopg
        with psycopg.connect(self._get_db_url()) as conn:
            rows = conn.execute(
                """
                SELECT chart_id, ayanamsha_id, source_type
                FROM rag_chunks
                WHERE chart_id = %s AND ayanamsha_id = %s
                  AND source_type = 'forensic_render'
                """,
                (self.TEST_CHART_ID, self.TEST_AYA),
            ).fetchall()

        assert len(rows) >= 1, (
            f"No rag_chunks rows found for chart_id={self.TEST_CHART_ID} "
            f"ayanamsha_id={self.TEST_AYA} source_type=forensic_render — "
            "this would have been a schema error before migration 163"
        )
        assert len(rows) == chunks_written, (
            f"DB row count ({len(rows)}) != chunks_written ({chunks_written})"
        )
        for row in rows:
            assert str(row[0]) == self.TEST_CHART_ID
            assert row[1] == self.TEST_AYA
            assert row[2] == "forensic_render"
