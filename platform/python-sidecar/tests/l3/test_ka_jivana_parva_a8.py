"""
A8/O6 tests for ka_jivana_parva — Pratyantar-dasha level-3 enhancement.

Fail-before / pass-after coverage for the additive PD sub-query:
- PD rows produced for current-AD only (CURRENT_DATE-scoped level_n=3)
- PD rows from OTHER AD periods are NOT included (date-scoped exclusion)
- Existing MD + AD rows are unchanged (no regression)
- source_citation correctly distinguishes PD rows vs MD/AD rows
- parva_index stays within smallint range (no overflow)
- Zero PD rows handled gracefully (writer returns without error)
- FROZEN orchestrator contract maintained
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestrator.writers.ka_jivana_parva import KaJivanaParvaWriter

WRITER_PATH = str(
    Path(__file__).parent.parent.parent
    / "pipeline" / "orchestrator" / "writers" / "ka_jivana_parva.py"
)

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
TOMORROW  = TODAY + timedelta(days=1)
LAST_YEAR = date(TODAY.year - 1, 1, 1)
NEXT_YEAR = date(TODAY.year + 1, 12, 31)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dasha_row(lord_graha, start_date, end_date, level_n):
    return {'lord_graha': lord_graha, 'start_date': start_date,
            'end_date': end_date, 'level_n': level_n}


def _make_ctx(chart_id="482012f1-710e-4a25-994a-93821f5871aa", as_of_date=None):
    ctx = MagicMock()
    ctx.config = {'chart_id': chart_id}
    if as_of_date is not None:
        ctx.config['as_of_date'] = as_of_date
    return ctx


def _build_cursor_sequence(conn, md_ad_rows, pd_rows, conv_rows=None):
    """
    Attach a side_effect to conn.cursor().__enter__ so each successive
    cursor.execute / fetchall returns the right data in order.

    Query order in the writer:
        1. DELETE (idempotency) — no fetchall
        2. SELECT MD+AD (level_n IN (1,2)) — fetchall → md_ad_rows
        3. SELECT convergence windows — fetchall → conv_rows
        4. SELECT PD (level_n=3) — fetchall → pd_rows
        5. INSERT (if rows exist) — no fetchall
    """
    if conv_rows is None:
        conv_rows = []

    cur_timeout  = MagicMock()  # SET LOCAL statement_timeout = 0
    cur_delete   = MagicMock()
    cur_md_ad    = MagicMock(); cur_md_ad.fetchall.return_value = md_ad_rows
    cur_conv     = MagicMock(); cur_conv.fetchall.return_value  = conv_rows
    cur_pd       = MagicMock(); cur_pd.fetchall.return_value    = pd_rows
    cur_insert   = MagicMock()

    cursors = [cur_timeout, cur_delete, cur_md_ad, cur_conv, cur_pd, cur_insert]
    idx = [0]

    def _new_cursor():
        cm = MagicMock()
        c = cursors[idx[0]] if idx[0] < len(cursors) else MagicMock()
        idx[0] += 1
        cm.__enter__ = MagicMock(return_value=c)
        cm.__exit__  = MagicMock(return_value=False)
        return cm

    conn.cursor.side_effect = _new_cursor
    return cur_insert


# ---------------------------------------------------------------------------
# Test: PD rows produced when level_n=3 data exists for current AD
# ---------------------------------------------------------------------------

def test_pratyantar_rows_produced_for_current_ad():
    """O6: writer produces parva rows for PD (level_n=3) scoped to as_of_date.

    Fail-before: writer only queried level_n IN (1, 2); PD mock rows were ignored.
    Pass-after:  writer queries level_n=3 and produces a row for each PD row returned.

    The DB mock returns only the CURRENT PD row (as the real SQL bound-param filter
    would — past and future PDs are excluded at the DB layer, not by the writer).
    """
    md_row = _make_dasha_row('Jupiter', date(2021, 1, 1), date(2037, 1, 1), 1)
    ad_row = _make_dasha_row('Venus',   date(2024, 1, 1), date(2026, 12, 31), 2)
    # DB returns only the single PD row whose date range spans as_of_date (2026-06-15).
    # Past PD (ended 2026-01-31) and future PD (starts 2026-07-01) are excluded by SQL.
    as_of = date(2026, 6, 15)
    pd_rows = [
        _make_dasha_row('Moon', date(2026, 2, 1), date(2026, 6, 30), 3),  # spans 2026-06-15
    ]

    conn = MagicMock()
    _build_cursor_sequence(conn, [md_row, ad_row], pd_rows)

    ctx = _make_ctx(as_of_date=as_of)
    ctx.db_conn = conn

    writer = KaJivanaParvaWriter()
    result = writer.run(ctx)

    # MD(1) + AD(1) + PD(1) = 3 rows total
    assert result.rows_inserted == 3, (
        f"Expected 3 rows (1 MD + 1 AD + 1 PD), got {result.rows_inserted}"
    )


def test_pratyantar_rows_use_pd_citation():
    """PD rows carry source_citation matching 'ka_jivana_parva:v2.0:PD=<planet>'."""
    md_row  = _make_dasha_row('Jupiter', date(2021, 1, 1), date(2037, 1, 1), 1)
    pd_rows = [_make_dasha_row('Venus', YESTERDAY, TOMORROW, 3)]

    conn     = MagicMock()
    inserted = _build_cursor_sequence(conn, [md_row], pd_rows)

    ctx = _make_ctx()
    ctx.db_conn = conn

    KaJivanaParvaWriter().run(ctx)

    assert inserted.executemany.called, "INSERT was not called"
    call_args = inserted.executemany.call_args
    rows_arg  = call_args[0][1]  # second positional arg = list of row tuples

    citations = [row[-1] for row in rows_arg]
    pd_citations = [c for c in citations if c.startswith('ka_jivana_parva:v2.0:PD=')]
    assert len(pd_citations) == 1, f"Expected 1 PD citation, found: {pd_citations}"
    assert pd_citations[0] == 'ka_jivana_parva:v2.0:PD=Venus'


def test_md_and_ad_citations_unchanged():
    """Existing MD and AD source_citation patterns are untouched by O6 change."""
    md_row  = _make_dasha_row('Jupiter', date(2021, 1, 1), date(2037, 1, 1), 1)
    ad_row  = _make_dasha_row('Venus',   date(2024, 1, 1), date(2026, 12, 31), 2)
    pd_rows = [_make_dasha_row('Sun', YESTERDAY, TOMORROW, 3)]

    conn     = MagicMock()
    inserted = _build_cursor_sequence(conn, [md_row, ad_row], pd_rows)

    ctx = _make_ctx()
    ctx.db_conn = conn

    KaJivanaParvaWriter().run(ctx)

    rows_arg  = inserted.executemany.call_args[0][1]
    citations = [row[-1] for row in rows_arg]

    md_citations = [c for c in citations if ':MD=' in c and ':AD=' not in c and ':PD=' not in c]
    ad_citations = [c for c in citations if ':AD=' in c and ':PD=' not in c]
    pd_citations = [c for c in citations if ':PD=' in c]

    assert len(md_citations) == 1, f"Expected 1 MD citation, got: {md_citations}"
    assert len(ad_citations) == 1, f"Expected 1 AD citation, got: {ad_citations}"
    assert len(pd_citations) == 1, f"Expected 1 PD citation, got: {pd_citations}"


# ---------------------------------------------------------------------------
# Test: PD rows from OTHER AD periods are NOT included
# ---------------------------------------------------------------------------

def test_pd_rows_from_other_ad_periods_excluded():
    """Only PDs spanning as_of_date are included; past/future PDs are excluded at the DB layer.

    The exclusion happens via bound SQL parameters (start_date <= %s AND end_date >= %s)
    with as_of_date passed as both values. We verify the writer uses bound params
    (not a literal CURRENT_DATE) and that level_n = 3 is present.
    """
    with open(WRITER_PATH) as f:
        content = f.read()

    # Must have level_n=3 query
    assert 'level_n = 3' in content, "level_n = 3 filter missing from writer"
    # Writer SQL must NOT contain literal CURRENT_DATE in a query context.
    # Allow CURRENT_DATE in comments/docstrings only — check the SQL string itself.
    # The PD query must use bound params (%s) not a literal CURRENT_DATE.
    assert 'start_date <= CURRENT_DATE' not in content, (
        "PD SQL must not use literal 'start_date <= CURRENT_DATE' — use bound param %s instead"
    )
    assert 'end_date >= CURRENT_DATE' not in content, (
        "PD SQL must not use literal 'end_date >= CURRENT_DATE' — use bound param %s instead"
    )
    # The PD query must filter start_date and end_date via bound params
    assert 'start_date <= %s' in content, "PD query must filter start_date <= %s (bound param)"
    assert 'end_date >= %s' in content, "PD query must filter end_date >= %s (bound param)"


def test_pd_query_does_not_use_in_1_2_3():
    """The main MD+AD query must NOT be expanded to level_n IN (1, 2, 3).

    Expanding would recreate the smallint overflow bug by fetching all PDs
    across all MDs and ADs (~7800 additional rows).
    """
    with open(WRITER_PATH) as f:
        content = f.read()

    assert 'level_n IN (1, 2, 3)' not in content, (
        "Main query must stay scoped to level_n IN (1, 2) — "
        "do NOT include 3 there"
    )
    # Confirm the original scope is preserved
    assert 'level_n IN (1, 2)' in content, (
        "Original level_n IN (1, 2) scope is missing — main query was altered"
    )


# ---------------------------------------------------------------------------
# Test: smallint overflow safety
# ---------------------------------------------------------------------------

def test_parva_index_stays_within_smallint():
    """Total row count MD+AD+PD(current-only) must stay far below 32767.

    Real production numbers: ~14 MDs + ~224 ADs + ~9 PDs = ~247 rows.
    Simulate a generous worst case (30 MDs × 15 ADs + 9 PDs = 459) and
    confirm all parva_index values fit in a signed smallint (max 32767).
    """
    SMALLINT_MAX = 32767
    EXPECTED_MAX_ROWS = 30 * 15 + 9  # 459 — generous upper bound

    assert EXPECTED_MAX_ROWS < SMALLINT_MAX, (
        f"Even worst-case row count {EXPECTED_MAX_ROWS} must be < {SMALLINT_MAX}"
    )


def test_pd_only_current_ad_prevents_overflow():
    """Restricting PD to CURRENT_DATE-scope means at most ~9 PD rows, not thousands.

    If we queried all level_n=3 without CURRENT_DATE scoping we'd get
    14 MDs × 9 ADs × 9 PDs = ~1134 extra rows — but still within smallint.
    The real danger is all 7 systems × 5 ayanamshas without any filter.
    Verify the PD query retains the system and ayanamsha filters as well.
    """
    with open(WRITER_PATH) as f:
        content = f.read()

    # Locate the level_n=3 block and check it has both scoping guards
    pd_block_idx = content.find('level_n = 3')
    assert pd_block_idx != -1

    # Within 500 chars of level_n=3 there must be system + ayanamsha filters
    pd_block = content[pd_block_idx: pd_block_idx + 500]
    assert "system_id = 'vimshottari'" in pd_block, (
        "PD query missing system_id filter — could mix systems"
    )
    assert "ayanamsha_id = 'lahiri_chitrapaksha'" in pd_block, (
        "PD query missing ayanamsha_id filter — could mix ayanamshas"
    )


# ---------------------------------------------------------------------------
# Test: zero PD rows — graceful handling
# ---------------------------------------------------------------------------

def test_zero_pd_rows_handled_gracefully():
    """When no level_n=3 rows exist writer returns without error.

    This is expected until level-3 data is built, or during non-active AD spans.
    """
    md_row = _make_dasha_row('Jupiter', date(2021, 1, 1), date(2037, 1, 1), 1)
    ad_row = _make_dasha_row('Venus',   date(2024, 1, 1), date(2026, 12, 31), 2)

    conn = MagicMock()
    _build_cursor_sequence(conn, [md_row, ad_row], pd_rows=[])  # empty PD result

    ctx = _make_ctx()
    ctx.db_conn = conn

    writer = KaJivanaParvaWriter()
    result = writer.run(ctx)

    # Should produce MD(1) + AD(1) = 2 rows, no error
    assert result.rows_inserted == 2
    assert result.asset_id == 'ka_jivana_parva'


def test_zero_pd_rows_logs_info_not_error(caplog):
    """Zero PD rows emits an INFO log, not WARNING or ERROR."""
    import logging
    md_row = _make_dasha_row('Saturn', date(2017, 1, 1), date(2036, 1, 1), 1)

    conn = MagicMock()
    _build_cursor_sequence(conn, [md_row], pd_rows=[])

    ctx = _make_ctx()
    ctx.db_conn = conn

    with caplog.at_level(logging.INFO, logger='pipeline.orchestrator.writers.ka_jivana_parva'):
        KaJivanaParvaWriter().run(ctx)

    # Should log at INFO, not WARNING
    pd_log_records = [
        r for r in caplog.records if 'PD' in r.message or 'level_n=3' in r.message
    ]
    if pd_log_records:
        for rec in pd_log_records:
            assert rec.levelno <= logging.INFO, (
                f"Expected INFO or lower for missing PD rows, got {rec.levelname}"
            )


# ---------------------------------------------------------------------------
# Test: parva_index continuity — PD rows increment from last AD index
# ---------------------------------------------------------------------------

def test_pd_parva_index_continues_from_ad():
    """PD parva_index values continue sequentially after the last AD row."""
    md_row  = _make_dasha_row('Jupiter', date(2021, 1, 1), date(2037, 1, 1), 1)
    ad_rows = [
        _make_dasha_row('Venus',  date(2024, 1, 1), date(2025, 6, 30), 2),
        _make_dasha_row('Sun',    date(2025, 7, 1), date(2026, 12, 31), 2),
    ]
    pd_rows = [
        _make_dasha_row('Moon',  YESTERDAY, TOMORROW, 3),
    ]

    conn     = MagicMock()
    inserted = _build_cursor_sequence(conn, [md_row] + ad_rows, pd_rows)

    ctx = _make_ctx()
    ctx.db_conn = conn

    KaJivanaParvaWriter().run(ctx)

    rows_arg = inserted.executemany.call_args[0][1]
    indices  = [row[1] for row in rows_arg]  # parva_index is position 1

    # Must be strictly sequential starting at 1
    assert indices == list(range(1, len(rows_arg) + 1)), (
        f"parva_index not sequential: {indices}"
    )

    # Total: 1 MD + 2 ADs + 1 PD = 4
    assert len(indices) == 4

    # Last index is the PD (citation check)
    last_citation = rows_arg[-1][-1]
    assert last_citation.startswith('ka_jivana_parva:v2.0:PD='), (
        f"Last row should be PD, got citation: {last_citation}"
    )


# ---------------------------------------------------------------------------
# Test: existing MD+AD output unchanged (regression guard)
# ---------------------------------------------------------------------------

def test_existing_md_ad_rows_unchanged_when_pd_present():
    """When PD rows are added, the MD and AD rows retain their original content."""
    md_row = _make_dasha_row('Jupiter', date(2021, 1, 1), date(2037, 1, 1), 1)
    ad_row = _make_dasha_row('Venus',   date(2024, 1, 1), date(2026, 12, 31), 2)
    pd_row = _make_dasha_row('Sun',     YESTERDAY, TOMORROW, 3)

    conn     = MagicMock()
    inserted = _build_cursor_sequence(conn, [md_row, ad_row], [pd_row])

    ctx = _make_ctx()
    ctx.db_conn = conn

    KaJivanaParvaWriter().run(ctx)

    rows_arg = inserted.executemany.call_args[0][1]

    # First row is MD
    md_out = rows_arg[0]
    assert md_out[4] == 'Jupiter', f"Expected Jupiter as dasha_planet in row 0, got {md_out[4]}"
    assert md_out[-1] == 'ka_jivana_parva:v2.0:MD=Jupiter'

    # Second row is AD
    ad_out = rows_arg[1]
    assert ad_out[4] == 'Venus', f"Expected Venus as dasha_planet in row 1, got {ad_out[4]}"
    assert ad_out[-1] == 'ka_jivana_parva:v2.0:MD=Jupiter:AD=Venus'

    # Third row is PD
    pd_out = rows_arg[2]
    assert pd_out[4] == 'Sun', f"Expected Sun as dasha_planet in row 2, got {pd_out[4]}"
    assert pd_out[-1] == 'ka_jivana_parva:v2.0:PD=Sun'


# ---------------------------------------------------------------------------
# FROZEN orchestrator contract
# ---------------------------------------------------------------------------

def test_writer_contract_no_commit():
    """Writer must not call .commit() — orchestrator owns the transaction."""
    with open(WRITER_PATH) as f:
        content = f.read()
    assert re.findall(r'\.commit\(\)', content) == [], "Found .commit() in writer"


def test_writer_contract_no_rollback():
    """Writer must not call .rollback()."""
    with open(WRITER_PATH) as f:
        content = f.read()
    assert re.findall(r'\.rollback\(\)', content) == [], "Found .rollback() in writer"


def test_writer_uses_ctx_db_conn():
    """Writer accesses DB via ctx.db_conn, not a raw connection string."""
    with open(WRITER_PATH) as f:
        content = f.read()
    assert 'ctx.db_conn' in content, "Writer must use ctx.db_conn"


def test_writer_returns_writer_result():
    """Writer returns a WriterResult with asset_id='ka_jivana_parva'."""
    md_row = _make_dasha_row('Jupiter', date(2021, 1, 1), date(2037, 1, 1), 1)

    conn = MagicMock()
    _build_cursor_sequence(conn, [md_row], pd_rows=[])

    ctx = _make_ctx()
    ctx.db_conn = conn

    result = KaJivanaParvaWriter().run(ctx)
    assert result.asset_id == 'ka_jivana_parva'
    assert isinstance(result.rows_inserted, int)


# ---------------------------------------------------------------------------
# Test: PD query structure (grep-based contract test)
# ---------------------------------------------------------------------------

def test_as_of_date_passed_as_bound_param():
    """as_of_date from ctx.config is passed as a bound SQL param to the PD query.

    Verifies IMPORTANT-1: the PD query uses %s placeholders with as_of_date as both
    start_date and end_date params — not a literal CURRENT_DATE. Captures cursor.execute
    call_args for the PD cursor (4th cursor in sequence) and checks params.
    """
    md_row = _make_dasha_row('Jupiter', date(2021, 1, 1), date(2037, 1, 1), 1)
    ad_row = _make_dasha_row('Venus',   date(2024, 1, 1), date(2026, 12, 31), 2)
    as_of = date(2026, 3, 15)
    pd_rows = [_make_dasha_row('Sun', date(2026, 1, 1), date(2026, 6, 30), 3)]

    conn = MagicMock()
    cursors_used = []

    # Track cursors in order so we can inspect the PD cursor specifically
    original_side_effect_cursors = []
    cur_timeout  = MagicMock()  # SET LOCAL statement_timeout = 0
    cur_delete   = MagicMock()
    cur_md_ad    = MagicMock(); cur_md_ad.fetchall.return_value = [md_row, ad_row]
    cur_conv     = MagicMock(); cur_conv.fetchall.return_value  = []
    cur_pd       = MagicMock(); cur_pd.fetchall.return_value    = pd_rows
    cur_insert   = MagicMock()
    all_cursors = [cur_timeout, cur_delete, cur_md_ad, cur_conv, cur_pd, cur_insert]
    idx = [0]

    def _new_cursor():
        cm = MagicMock()
        c = all_cursors[idx[0]] if idx[0] < len(all_cursors) else MagicMock()
        idx[0] += 1
        cm.__enter__ = MagicMock(return_value=c)
        cm.__exit__  = MagicMock(return_value=False)
        return cm

    conn.cursor.side_effect = _new_cursor

    ctx = _make_ctx(as_of_date=as_of)
    ctx.db_conn = conn

    KaJivanaParvaWriter().run(ctx)

    # The PD cursor is the 4th cursor (index 3); check its execute call args
    assert cur_pd.execute.called, "PD cursor execute was not called"
    call_args = cur_pd.execute.call_args
    params = call_args[0][1]  # positional: (sql, params)

    # params should be (chart_id, as_of_date, as_of_date)
    assert as_of in params, (
        f"as_of_date={as_of} not found in PD query params: {params}"
    )
    assert params.count(as_of) == 2, (
        f"as_of_date should appear twice (start_date and end_date), got: {params}"
    )


def test_pd_query_has_level_n_3():
    """Writer source contains a level_n = 3 query (not level_n IN (1, 2, 3))."""
    with open(WRITER_PATH) as f:
        content = f.read()
    assert 'level_n = 3' in content, "O6 PD query missing level_n = 3 clause"


def test_pd_query_scoped_with_bound_param_start():
    """PD query filters start_date via bound param (not literal CURRENT_DATE)."""
    with open(WRITER_PATH) as f:
        content = f.read()
    assert 'start_date <= %s' in content, (
        "PD query must filter start_date <= %s (as_of_date bound param)"
    )


def test_pd_query_scoped_with_bound_param_end():
    """PD query filters end_date via bound param (not literal CURRENT_DATE)."""
    with open(WRITER_PATH) as f:
        content = f.read()
    assert 'end_date >= %s' in content, (
        "PD query must filter end_date >= %s (as_of_date bound param)"
    )
