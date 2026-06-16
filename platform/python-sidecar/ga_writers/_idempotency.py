"""Idempotency helpers for the L1 Gaṇita writers — make a rebuild REPLACE, not accrete.

The `chart_facts` and `chart_dashas` unique keys include `build_id`
(`(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)` and
`(chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id)` respectively),
so re-running a writer under a fresh `build_id` *appends* a second copy instead of
replacing the first. Repeated rebuilds therefore accrete stale rows
(the 13-build chart_facts / 7-build chart_dashas bloat that had to be hand-cleaned).

Each writer calls the relevant `replace_prior_*` helper immediately before its
INSERT, in the same transaction, deleting the chart's prior rows for *exactly the
scope it is about to (re)write* — scoped to `chart_id` plus the `ayanamsha_id`s and
the natural-key discriminators (fact_category / system_id / varga) present in the
rows. Scoping this way means:

  * writers never delete each other's rows (disjoint category/system/varga scopes),
  * a per-ayanamsha insert call never wipes a sibling ayanamsha written earlier in
    the same build,
  * a rebuild under any build_id leaves exactly one copy per natural key.

All helpers are no-ops on empty input and return the number of rows deleted.
`conn` is a psycopg connection/cursor exposing `.execute(sql, params)` returning a
cursor with `.rowcount`.
"""

from __future__ import annotations

from typing import Any, Iterable


def _distinct(rows: Iterable[dict], key: str) -> list:
    return sorted({r[key] for r in rows if r.get(key) is not None})


def _delete(conn: Any, sql: str, params: list) -> int:
    cur = conn.execute(sql, params)
    return getattr(cur, "rowcount", 0) or 0


def replace_prior_chart_facts(conn: Any, rows: list[dict]) -> int:
    """Delete prior chart_facts rows for the (chart_id, ayanamsha_id, fact_category)
    scope present in `rows`, so the subsequent INSERT replaces rather than accretes."""
    if not rows:
        return 0
    cats = _distinct(rows, "fact_category")
    if not cats:
        return 0
    ayanamshas = _distinct(rows, "ayanamsha_id")
    deleted = 0
    for cid in _distinct(rows, "chart_id"):
        sql = "DELETE FROM chart_facts WHERE chart_id = %s AND fact_category = ANY(%s)"
        params: list = [cid, cats]
        if ayanamshas:
            sql += " AND ayanamsha_id = ANY(%s)"
            params.append(ayanamshas)
        deleted += _delete(conn, sql, params)
    return deleted


def replace_prior_chart_dashas(conn: Any, rows: list[dict]) -> int:
    """Delete prior chart_dashas rows for the (chart_id, ayanamsha_id, system_id)
    scope present in `rows`."""
    if not rows:
        return 0
    systems = _distinct(rows, "system_id")
    ayanamshas = _distinct(rows, "ayanamsha_id")
    if not systems:
        return 0
    deleted = 0
    for cid in _distinct(rows, "chart_id"):
        sql = "DELETE FROM chart_dashas WHERE chart_id = %s AND system_id = ANY(%s)"
        params: list = [cid, systems]
        if ayanamshas:
            sql += " AND ayanamsha_id = ANY(%s)"
            params.append(ayanamshas)
        deleted += _delete(conn, sql, params)
    return deleted


def replace_prior_chart_divisionals(conn: Any, rows: list[dict]) -> int:
    """Delete prior chart_divisionals rows for the (chart_id, ayanamsha_id, varga)
    scope present in `rows`."""
    if not rows:
        return 0
    vargas = _distinct(rows, "varga")
    ayanamshas = _distinct(rows, "ayanamsha_id")
    if not vargas:
        return 0
    deleted = 0
    for cid in _distinct(rows, "chart_id"):
        sql = "DELETE FROM chart_divisionals WHERE chart_id = %s AND varga = ANY(%s)"
        params: list = [cid, vargas]
        if ayanamshas:
            sql += " AND ayanamsha_id = ANY(%s)"
            params.append(ayanamshas)
        deleted += _delete(conn, sql, params)
    return deleted


def replace_prior_tajik_varsha(conn: Any, rows: list[dict]) -> int:
    """Delete prior l1_tajik_varsha_year_lords rows for the
    (chart_id, ayanamsha_id, varsha_year) scope present in `rows`, regardless of
    build_id, so a rebuild under any build_id REPLACES rather than accretes.

    The table's UNIQUE key includes build_id, so without this a re-run would
    append a second copy per varsha. Scoped to the exact (chart, ayanamsha,
    varsha_year) triples being (re)written; per-varsha so a partial rebuild never
    wipes siblings outside its window."""
    if not rows:
        return 0
    years = _distinct(rows, "varsha_year")
    ayanamshas = _distinct(rows, "ayanamsha_id")
    if not years:
        return 0
    deleted = 0
    for cid in _distinct(rows, "chart_id"):
        sql = ("DELETE FROM l1_tajik_varsha_year_lords "
               "WHERE chart_id = %s AND varsha_year = ANY(%s)")
        params: list = [cid, years]
        if ayanamshas:
            sql += " AND ayanamsha_id = ANY(%s)"
            params.append(ayanamshas)
        deleted += _delete(conn, sql, params)
    return deleted


def clear_table_for_chart(conn: Any, table: str, chart_id: str) -> int:
    """Delete all rows for a chart from a whole-table-per-chart asset
    (e.g. chart_dashas). `table` is a trusted literal — never user input."""
    return _delete(conn, f"DELETE FROM {table} WHERE chart_id = %s", [chart_id])
