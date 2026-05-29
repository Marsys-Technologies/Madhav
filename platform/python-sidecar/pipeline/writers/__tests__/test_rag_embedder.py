"""
INF10-S1: rag_embedder tests
[BUILD-ORCH-G4-08]
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure pipeline is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from pipeline.writers.rag_embedder import chunk_markdown, Chunk, _embed_texts, EMBEDDING_DIM


# ── chunk_markdown tests ──────────────────────────────────────────────────────

class TestChunkMarkdown:

    def test_splits_at_h2_boundaries(self):
        md = """## Section A

Content A paragraph.

## Section B

Content B paragraph.
"""
        chunks = chunk_markdown(md)
        assert len(chunks) == 2
        assert 'Section A' in chunks[0].heading
        assert 'Section B' in chunks[1].heading

    def test_splits_at_h3_boundaries(self):
        md = """## Main Section

Intro.

### Sub A

Sub A content.

### Sub B

Sub B content.
"""
        chunks = chunk_markdown(md)
        assert len(chunks) >= 2  # At least ## and each ###

    def test_strips_yaml_frontmatter(self):
        md = """---
chart_id: abc
rendered_at: 2026-05-30
---

## Planetary Positions

Sun: Capricorn
"""
        chunks = chunk_markdown(md)
        assert all('chart_id' not in c.body for c in chunks)
        assert any('Planetary Positions' in c.heading for c in chunks)

    def test_empty_document_returns_single_chunk(self):
        md = "No headings here at all."
        chunks = chunk_markdown(md)
        assert len(chunks) == 1
        assert chunks[0].heading == ''

    def test_chunk_index_sequential(self):
        md = "## A\n\nA body.\n\n## B\n\nB body.\n\n## C\n\nC body.\n"
        chunks = chunk_markdown(md)
        assert [c.chunk_index for c in chunks] == list(range(len(chunks)))

    def test_source_section_matches_heading(self):
        md = "## Planetary Positions\n\nSun in Capricorn.\n"
        chunks = chunk_markdown(md)
        assert '## Planetary Positions' in chunks[0].source_section or 'Planetary Positions' in chunks[0].source_section

    def test_long_section_splits_at_paragraphs(self):
        # Build a section with many paragraphs that exceeds MAX_CHUNK_TOKENS
        paras = [f"Paragraph {i}: " + " ".join([f"word{j}" for j in range(80)]) for i in range(10)]
        md = "## Long Section\n\n" + "\n\n".join(paras)
        chunks = chunk_markdown(md)
        # Should have been split into multiple chunks
        assert len(chunks) > 1

    def test_all_chunks_have_non_empty_body(self):
        md = "## A\n\nA body.\n\n## B\n\nB body.\n"
        chunks = chunk_markdown(md)
        for chunk in chunks:
            assert chunk.body.strip()


# ── _embed_texts tests ────────────────────────────────────────────────────────

class TestEmbedTexts:

    def test_returns_zero_vectors_when_no_model(self):
        import pipeline.writers.rag_embedder as rag
        original = rag._embed_model
        try:
            rag._embed_model = None
            result = _embed_texts(['hello', 'world'])
            assert len(result) == 2
            assert len(result[0]) == EMBEDDING_DIM
            assert all(v == 0.0 for v in result[0])
        finally:
            rag._embed_model = original

    def test_returns_one_vector_per_text(self):
        import pipeline.writers.rag_embedder as rag
        original = rag._embed_model
        try:
            rag._embed_model = None
            result = _embed_texts(['text1', 'text2', 'text3'])
            assert len(result) == 3
        finally:
            rag._embed_model = original


# ── No-narration lint integration ─────────────────────────────────────────────

class TestLintIntegration:

    def test_lint_clean_chunk_passes(self):
        from pipeline.writers.rag_embedder import _lint_chunk
        c = Chunk(heading='## Test', body='Sun: Capricorn, house 10.', chunk_index=0, source_section='test')
        _lint_chunk(c)  # Should not raise

    def test_lint_violation_raises(self):
        from pipeline.writers.rag_embedder import _lint_chunk
        c = Chunk(heading='## Test', body='This indicates a strong career.', chunk_index=0, source_section='test')
        with pytest.raises(Exception):
            _lint_chunk(c)


# ── embed_chart_document integration (mocked DB) ─────────────────────────────

class TestEmbedChartDocument:

    @patch('pipeline.writers.rag_embedder._init_vertexai')
    @patch('pipeline.writers.rag_embedder._embed_texts')
    @patch('psycopg.connect')
    def test_returns_zero_chunks_when_no_document(self, mock_connect, mock_embed, mock_init_v):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        from pipeline.writers.rag_embedder import embed_chart_document
        result = embed_chart_document('chart-1', 'lahiri', 'build-1', db_url='postgresql://test/db')
        assert result['chunks_written'] == 0

    @patch('pipeline.writers.rag_embedder._init_vertexai')
    @patch('pipeline.writers.rag_embedder._embed_texts')
    @patch('psycopg.connect')
    def test_writes_chunks_for_valid_document(self, mock_connect, mock_embed, mock_init_v):
        mock_embed.return_value = [[0.1] * EMBEDDING_DIM, [0.2] * EMBEDDING_DIM]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = (
            "## Planetary Positions\n\nSun: Capricorn, house 10.\n\n## House Cusps\n\nAscendant: Aries.\n",
        )
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        from pipeline.writers.rag_embedder import embed_chart_document
        result = embed_chart_document('chart-1', 'lahiri', 'build-1', db_url='postgresql://test/db')
        assert result['chunks_written'] >= 1
        assert result['source_type'] == 'forensic_render'
