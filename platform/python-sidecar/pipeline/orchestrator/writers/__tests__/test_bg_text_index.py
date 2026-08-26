from unittest.mock import MagicMock, patch


def test_writer_repairs_a_wrong_non_null_topic_tag():
    from pipeline.orchestrator.writers.bg_text_index import TextIndexWriter

    cursor = MagicMock()
    cursor.fetchall.side_effect = [
        [{"canonical_id": "career_general"}],
        [{"chunk_id": "chunk-1", "content_en": "career text", "topic_tag": "wrong_tag"}],
    ]
    cursor.fetchone.side_effect = [
        {"count": 1},
        {"count": 0},
        {"count": 1},
    ]
    cursor.rowcount = 1
    connection = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor

    context = MagicMock()
    context.db_conn = connection
    context.dry_run = False

    with patch(
        "pipeline.orchestrator.writers.bg_text_index.classify_chunk",
        return_value="career_general",
    ):
        result = TextIndexWriter().run(context)

    cursor.executemany.assert_called_once_with(
        "UPDATE classical_text_chunks SET topic_tag = %s "
        "WHERE chunk_id = %s AND topic_tag IS DISTINCT FROM %s",
        [("career_general", "chunk-1", "career_general")],
    )
    assert result.rows_inserted == 1
    assert "changed=1" in result.notes
