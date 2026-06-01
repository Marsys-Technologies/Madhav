"""
test_forensic_writer_integration.py — Integration tests for A2 forensic writer.

S4b acceptance criteria:
  6. One chart_documents row per ayanamsha with non-empty content_md,
     all 13 section anchors present, linter clean.
  7. rag_embedder.embed_chart_document() picks up is_embedded=false row
     and produces rag_chunks with source_type='forensic_render'.
  8. (See EXPECTED_ROW_COUNTS.yaml — 1 doc per chart × ayanamsha × build.)

All DB interactions are mocked so this suite runs without a live DB.
"""
from __future__ import annotations

import json
import re
import sys
import os
import unittest.mock as mock
from contextlib import contextmanager
from typing import Any

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from pipeline.writers.forensic_writer import write, _SECTION_REGISTRY
from pipeline.render.base_renderer import anchor_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ANCHOR_RE = re.compile(r'#([a-z0-9-]+)', re.IGNORECASE)

_MINIMAL: dict = {}

_TYPICAL: dict = {
    "planets": [
        {"id": "sun", "name": "Sun", "degree_in_sign": 1.96, "sign": "Capricorn",
         "sign_id": 10, "nakshatra": "Uttara Ashadha", "pada": 1,
         "retrograde": False, "dignity_status": "debilitated", "house": 10,
         "longitude_deg": 291.96},
        {"id": "moon", "name": "Moon", "degree_in_sign": 2.70, "sign": "Aquarius",
         "sign_id": 11, "nakshatra": "Purva Bhadrapada", "pada": 2,
         "retrograde": False, "dignity_status": "neutral", "house": 11,
         "longitude_deg": 302.70},
    ],
    "houses": [
        {"house_number": h + 1, "house_num": h + 1,
         "sign": s, "sign_id": h + 1, "sign_lord": lord}
        for h, (s, lord) in enumerate([
            ("Aries","Mars"), ("Taurus","Venus"), ("Gemini","Mercury"),
            ("Cancer","Moon"), ("Leo","Sun"), ("Virgo","Mercury"),
            ("Libra","Venus"), ("Scorpio","Mars"), ("Sagittarius","Jupiter"),
            ("Capricorn","Saturn"), ("Aquarius","Saturn"), ("Pisces","Jupiter"),
        ])
    ],
    "panchanga": {
        "tithi": "Shukla Tritiya", "vara": "Ravivara",
        "nakshatra": "Purva Bhadrapada", "nakshatra_pada": 2,
        "yoga": "Shiva", "karana": "Garaja",
    },
    "dashas": {
        "system": "vimshottari",
        "mahadasha_sequence": [
            {"lord": "Saturn", "years": 19,
             "start_iso": "1984-02-05T00:00:00", "end_iso": "2003-02-05T00:00:00"},
        ],
    },
}


class _FakeConn:
    """
    Minimal conn mock that records the INSERT/UPDATE and simulates commit().
    Exposes .rows_upserted list with the captured chart_documents rows.
    """
    def __init__(self):
        self.rows_upserted: list[dict] = []
        self._cur = None

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


# ---------------------------------------------------------------------------
# 6. One chart_documents row with required properties
# ---------------------------------------------------------------------------

class TestOneDocumentRow:
    def test_exactly_one_row_upserted(self):
        conn = _FakeConn()
        result = write(
            build_id="integ-build-01",
            chart_id="362f9f17-95a5-490b-a5a7-027d3e0efda0",
            ayanamsha_id="lahiri",
            chart_output=_TYPICAL,
            conn=conn,
        )
        assert result == 1
        assert len(conn.rows_upserted) == 1

    def test_content_md_nonempty(self):
        conn = _FakeConn()
        write(
            build_id="integ-build-02",
            chart_id="test-chart",
            ayanamsha_id="raman",
            chart_output=_MINIMAL,
            conn=conn,
        )
        assert conn.rows_upserted
        row = conn.rows_upserted[0]
        assert row["content_md"], "content_md must be non-empty"
        assert len(row["content_md"]) > 100

    def test_document_type_is_forensic_render(self):
        conn = _FakeConn()
        write(
            build_id="integ-build-03",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            chart_output=_MINIMAL,
            conn=conn,
        )
        assert conn.rows_upserted[0]["document_type"] == "forensic_render"

    def test_byte_size_matches_content_md(self):
        conn = _FakeConn()
        write(
            build_id="integ-build-04",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            chart_output=_TYPICAL,
            conn=conn,
        )
        row = conn.rows_upserted[0]
        expected = len(row["content_md"].encode("utf-8"))
        assert row["byte_size"] == expected

    def test_all_13_section_anchors_present(self):
        conn = _FakeConn()
        write(
            build_id="integ-build-05",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            chart_output=_MINIMAL,
            conn=conn,
        )
        md = conn.rows_upserted[0]["content_md"]
        for title, _, _ in _SECTION_REGISTRY:
            aid = anchor_id(title)
            assert f"#{aid}" in md, (
                f"Anchor #{aid!r} (from section {title!r}) missing in rendered markdown"
            )

    def test_linter_passes_on_persisted_content(self):
        from pipeline.render.base_renderer import FORBIDDEN_PATTERN
        conn = _FakeConn()
        write(
            build_id="integ-build-06",
            chart_id="test-chart",
            ayanamsha_id="lahiri",
            chart_output=_TYPICAL,
            conn=conn,
        )
        md = conn.rows_upserted[0]["content_md"]
        matches = FORBIDDEN_PATTERN.findall(md)
        assert not matches, f"Narration violations in persisted content: {set(matches)}"

    def test_idempotent_two_calls_two_upserts(self):
        """Two calls with same (chart_id, ayanamsha_id, build_id) produce 2 upsert calls
        (the ON CONFLICT clause handles dedup at DB level)."""
        conn = _FakeConn()
        write(build_id="dup-build", chart_id="c1", ayanamsha_id="lahiri",
              chart_output=_MINIMAL, conn=conn)
        write(build_id="dup-build", chart_id="c1", ayanamsha_id="lahiri",
              chart_output=_MINIMAL, conn=conn)
        assert len(conn.rows_upserted) == 2


# ---------------------------------------------------------------------------
# 7. rag_embedder picks up the row and produces source_type='forensic_render'
# ---------------------------------------------------------------------------

class TestRagEmbedder:
    def test_embed_chart_document_uses_forensic_render_source_type(self):
        """
        Verify rag_embedder.embed_chart_document() reads a 'forensic_render'
        document and inserts rag_chunks with source_type='forensic_render'.

        All external I/O (psycopg, Vertex AI) is mocked.
        """
        from pipeline.writers import rag_embedder

        sample_md = (
            "---\nchart_id: c1\nayanamsha_id: lahiri\n---\n\n"
            "## Section One {#section-one}\n\nFact: Sun in Capricorn 1°58'\n\n"
            "## Section Two {#section-two}\n\nFact: Moon in Aquarius 2°42'\n"
        )

        rows_inserted: list[dict] = []

        class _FakeCursor:
            def __init__(self):
                self.result = None

            def execute(self, sql, params=None):
                if params and "INSERT INTO rag_chunks" in sql:
                    rows_inserted.append({
                        "source_type": params[1],
                        "chart_id": params[2],
                        "ayanamsha_id": params[3],
                        "build_id": params[4],
                    })
                elif params and "SELECT content_md" in sql:
                    pass
                elif params and "DELETE FROM rag_chunks" in sql:
                    pass

            def fetchone(self):
                return (sample_md,)

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        class _FakePsycopgConn:
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

        with mock.patch("psycopg.connect", return_value=_FakePsycopgConn()), \
             mock.patch.dict(os.environ, {"DATABASE_URL": "postgresql://fake"}):
            result = rag_embedder.embed_chart_document(
                chart_id="c1",
                ayanamsha_id="lahiri",
                build_id="rag-test-build",
                init_vertex=False,
            )

        assert result["source_type"] == "forensic_render"
        assert result["chunks_written"] >= 1
        # Every inserted chunk must carry source_type='forensic_render'
        for row in rows_inserted:
            assert row["source_type"] == "forensic_render", (
                f"Unexpected source_type: {row['source_type']!r}"
            )
