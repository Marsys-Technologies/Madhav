"""Tests for A4-S9: MV refresh wiring and query_panchanga_at_birth retrieval tool."""
import uuid
from unittest.mock import MagicMock


def test_mv_refresh_called():
    from pipeline.writers.panchanga_writer_a4 import emit_panchanga_mv_refresh
    conn = MagicMock()
    emit_panchanga_mv_refresh(conn, str(uuid.uuid4()))
    assert conn.execute.called


def test_mv_refresh_calls_concurrent_first():
    from pipeline.writers.panchanga_writer_a4 import emit_panchanga_mv_refresh
    conn = MagicMock()
    emit_panchanga_mv_refresh(conn, str(uuid.uuid4()))
    call_args = conn.execute.call_args_list[0][0][0]
    assert 'CONCURRENTLY' in call_args


def test_mv_refresh_fallback_on_exception():
    """If CONCURRENTLY fails, falls back to plain REFRESH."""
    from pipeline.writers.panchanga_writer_a4 import emit_panchanga_mv_refresh
    conn = MagicMock()
    conn.execute.side_effect = [Exception("lock"), None]
    # Should not raise
    emit_panchanga_mv_refresh(conn, str(uuid.uuid4()))
    assert conn.execute.call_count == 2


def test_mv_refresh_silent_on_double_exception():
    """Both refresh paths failing is non-blocking (no exception raised)."""
    from pipeline.writers.panchanga_writer_a4 import emit_panchanga_mv_refresh
    conn = MagicMock()
    conn.execute.side_effect = Exception("no MV")
    emit_panchanga_mv_refresh(conn, str(uuid.uuid4()))  # must not raise


def test_query_panchanga_at_birth_import():
    from pipeline.retrieval.retrieval_tools import query_panchanga_at_birth
    assert callable(query_panchanga_at_birth)


def test_query_panchanga_at_birth_all_scope():
    from pipeline.retrieval.retrieval_tools import query_panchanga_at_birth
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = []
    conn.cursor.return_value = cur
    result = query_panchanga_at_birth(conn, str(uuid.uuid4()), scope_filter='all')
    assert result == []
    assert cur.execute.called
    sql = cur.execute.call_args[0][0]
    assert "panchanga_%" in sql


def test_query_panchanga_at_birth_core_scope():
    from pipeline.retrieval.retrieval_tools import query_panchanga_at_birth
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = []
    conn.cursor.return_value = cur
    result = query_panchanga_at_birth(conn, str(uuid.uuid4()), scope_filter='core')
    assert result == []
    sql = cur.execute.call_args[0][0]
    assert "IN (" in sql  # category filter applied


def test_query_panchanga_at_birth_default_ayanamsha_ids():
    from pipeline.retrieval.retrieval_tools import query_panchanga_at_birth
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = []
    conn.cursor.return_value = cur
    query_panchanga_at_birth(conn, str(uuid.uuid4()))
    params = cur.execute.call_args[0][1]
    # chart_id + 5 ayanamsha_ids
    assert len(params) == 6


def test_query_panchanga_at_birth_custom_ayanamsha_ids():
    from pipeline.retrieval.retrieval_tools import query_panchanga_at_birth
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = []
    conn.cursor.return_value = cur
    query_panchanga_at_birth(conn, str(uuid.uuid4()), ayanamsha_ids=['lahiri_chitrapaksha'])
    params = cur.execute.call_args[0][1]
    assert len(params) == 2  # chart_id + 1 ayanamsha_id


def test_query_panchanga_at_birth_returns_dicts():
    from pipeline.retrieval.retrieval_tools import query_panchanga_at_birth
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = [
        ('panchanga_tithi', 'birth', 'tithi_name', 'Shukla Tritiya', None,
         'lahiri_chitrapaksha', 'Tithi: Shukla Tritiya', 'single'),
    ]
    conn.cursor.return_value = cur
    result = query_panchanga_at_birth(conn, str(uuid.uuid4()), scope_filter='core')
    assert len(result) == 1
    assert result[0]['fact_category'] == 'panchanga_tithi'
    assert result[0]['fact_key'] == 'tithi_name'
    assert result[0]['fact_value_text'] == 'Shukla Tritiya'


def test_query_panchanga_at_birth_returns_empty_on_exception():
    from pipeline.retrieval.retrieval_tools import query_panchanga_at_birth
    conn = MagicMock()
    conn.cursor.side_effect = Exception("db error")
    result = query_panchanga_at_birth(conn, str(uuid.uuid4()))
    assert result == []


def test_query_panchanga_at_birth_unknown_scope_falls_back_to_all():
    from pipeline.retrieval.retrieval_tools import query_panchanga_at_birth
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = []
    conn.cursor.return_value = cur
    result = query_panchanga_at_birth(conn, str(uuid.uuid4()), scope_filter='nonexistent_scope')
    assert result == []
    sql = cur.execute.call_args[0][0]
    # unknown scope → category_filter=None → LIKE 'panchanga_%'
    assert "panchanga_%" in sql
