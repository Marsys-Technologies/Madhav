"""
brahmagyan.phala.life_events_scope -- the ONLY door an L4 (Phala) reader uses to read `life_events`.

WHY THIS EXISTS (SS ruling N-105)
    `life_events` is the people-entered, private, chart-scoped Life Event Log. Two facts bind every L4 reader:

      1. A read of it MUST be scoped to the build's own chart. `ph_pramana` used to read the whole table with no
         chart filter (`SELECT ... FROM life_events ORDER BY event_date`): every chart it built was classified
         against every other chart's life events. That is a cross-chart privacy leak and an unearned-evidence
         defect (a `life_event_miss` claimed from a stranger's events). `ph_rectification` already filtered.
      2. The shared build role (`data_plane_builder`) gets NO direct grant on the table. Its door is the
         chart-scoped, read-only, security-barrier view `public.life_events_chart_scoped` (migration 1274), which
         shows only the rows whose chart_id equals `app_chart_context()`, the transaction-local GUC
         `app.chart_context` (unset or malformed -> NULL -> zero rows: fail closed).

WHAT A READ DOES (every call, no exceptions)
    * normalizes the build's chart_id (`uuid.UUID` on the real runner path, `str` elsewhere) to a UUID; a value
      that is not a UUID raises ValueError (it is never coerced, swallowed or cast away);
    * pins `app.chart_context` to that chart for the statement (transaction-local `set_config(..., true)`), and
      RESTORES the value it had before (an orchestrator-level pin is never blanked);
    * issues `SELECT <whitelisted columns> FROM <relation> WHERE chart_id = %s ORDER BY <whitelisted columns>`,
      so the explicit chart predicate is present on the view path AND on the base-table path (belt and braces);
    * checks every returned row's chart_id equals the requested chart and raises ForeignChartRowError otherwise
      (a runtime guard behind the SQL predicate: a read can never hand back another chart's row);
    * runs inside its own SAVEPOINT, rolled back on any error, so an error in the read never poisons the
      orchestrator's transaction (the orchestrator owns the transaction; this module never commits).

RELATION CHOICE
    The view when it exists AND the current role can SELECT it; otherwise the base table (the pre-1274 path, only
    reachable by a role that already holds SELECT on it, still with the explicit predicate). If the role can read
    neither, the SELECT raises InsufficientPrivilege and that error PROPAGATES (callers must not turn it into an
    empty result: an unreadable log is not an empty log).

COLUMNS
    Exactly the columns the L4 readers need (see VIEW_COLUMNS); `chart_id` is always returned for the runtime guard.

RESOLVING A REFERENCE (SS N-109)
    A derived row stores `lel_entry_jsonb = {"id": <life_events.id>, ...}`, never the event text. `resolve_life_event_text` turns that id back
    into the text for an ENTITLED role (one that holds SELECT on the base table, e.g. the serving roles): chart-scoped (`id` AND `chart_id`), so an
    id that belongs to another chart does not resolve (None). The builder cannot resolve it: the view has no free-text column.
"""
from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from typing import Any

import psycopg
import psycopg.rows

logger = logging.getLogger(__name__)

CHART_CONTEXT_GUC = "app.chart_context"
BASE_TABLE = "life_events"
SCOPED_VIEW = "life_events_chart_scoped"
SAVEPOINT = "sp_l4_life_events_scope"

# Exactly the columns of migration 1274's view. Each is read by an L4 reader:
#   id                 ph_pramana   (lel_entry_jsonb.id: the audit pointer back to the source row)
#   event_id           ph_rectification (TrainingEvent.event_id)
#   event_date         both         (window match / dasha lord on the date)
#   category           both         (domain bucket)
#   domain             ph_rectification (TrainingEvent.domain)
#   (description is NOT a column: SS N-109, data minimisation. Private free text is never copied into a derived L4 row;
#    a derived row carries the life_event id reference and the text is resolved on demand by `resolve_life_event_text`.)
#   (outcome_observed is NOT a column either: ph_pramana set LelEntry.outcome_valence and nothing used or persisted it; SS N-112 minimal columns.)
#   chart_id           both         (the explicit predicate and the runtime guard)
VIEW_COLUMNS: tuple[str, ...] = (
    "id", "event_id", "event_date", "category", "domain", "chart_id",
)

_RESOLVE_SQL = (
    "SELECT (to_regclass('public." + SCOPED_VIEW + "') IS NOT NULL "
    "AND COALESCE(has_table_privilege(current_user, to_regclass('public." + SCOPED_VIEW + "'), 'SELECT'), false)) AS use_view"
)


class ForeignChartRowError(RuntimeError):
    """A life_events read returned a row of a chart other than the one requested. Never swallowed."""


def normalize_chart_id(chart_id: Any) -> uuid.UUID:
    """UUID in, UUID out; str -> UUID; anything else or a malformed string raises (never coerced, never dropped)."""
    if isinstance(chart_id, uuid.UUID):
        return chart_id
    if isinstance(chart_id, str):
        return uuid.UUID(chart_id.strip())
    raise TypeError(f"chart_id must be a uuid.UUID or str, got {type(chart_id).__name__}")


def _first(row: Any) -> Any:
    if row is None:
        return None
    if isinstance(row, Mapping):
        return next(iter(row.values()), None)
    return row[0]


def _columns(names: Sequence[str], what: str) -> tuple[str, ...]:
    bad = [n for n in names if n not in VIEW_COLUMNS]
    if bad or not names:
        raise ValueError(f"{what} must be a non-empty subset of {VIEW_COLUMNS}, got {tuple(names)!r}")
    return tuple(names)


def resolve_relation(conn: Any) -> str:
    """The chart-scoped view when present and readable by the current role, else the base table."""
    with conn.cursor() as cur:
        cur.execute(_RESOLVE_SQL)
        return SCOPED_VIEW if _first(cur.fetchone()) is True else BASE_TABLE


def build_select_sql(relation: str, columns: Sequence[str], order_by: Sequence[str]) -> str:
    """The single SELECT every L4 life_events read issues. relation/columns/order are whitelisted; nothing else interpolated."""
    if relation not in (BASE_TABLE, SCOPED_VIEW):
        raise ValueError(f"unexpected relation {relation!r}")
    cols = list(_columns(columns, "columns"))
    if "chart_id" not in cols:
        cols.append("chart_id")
    order = _columns(order_by, "order_by")
    return f"SELECT {', '.join(cols)} FROM {relation} WHERE chart_id = %s ORDER BY {', '.join(order)}"


def _pin_guc(conn: Any, chart_id: str) -> str:
    """Pin app.chart_context for this transaction and return the value it had (so the caller can RESTORE it, not blank it)."""
    with conn.cursor() as cur:
        cur.execute("SELECT current_setting(%s, true)", (CHART_CONTEXT_GUC,))
        prev = _first(cur.fetchone())
    with conn.cursor() as cur:
        cur.execute("SELECT set_config(%s, %s, true)", (CHART_CONTEXT_GUC, chart_id))
    return prev if isinstance(prev, str) else ""


def _restore_guc(conn: Any, prev: str) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT set_config(%s, %s, true)", (CHART_CONTEXT_GUC, prev))


def _savepoint(conn: Any, statement: str) -> None:
    with conn.cursor() as cur:
        cur.execute(f"{statement} {SAVEPOINT}")


def fetch_chart_life_events(
    conn: Any,
    chart_id: Any,
    columns: Sequence[str],
    *,
    order_by: Sequence[str] = ("event_date",),
) -> list[dict]:
    """Read THIS chart's life_events rows (and only this chart's). See the module docstring for the full contract."""
    cid = normalize_chart_id(chart_id)
    wanted = _columns(columns, "columns")
    _columns(order_by, "order_by")
    _savepoint(conn, "SAVEPOINT")
    try:
        relation = resolve_relation(conn)
        sql = build_select_sql(relation, wanted, order_by)
        prev = _pin_guc(conn, str(cid))
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(sql, (cid,))
            rows = [dict(r) for r in cur.fetchall()]
        foreign = [r for r in rows if str(r.get("chart_id")) != str(cid)]
        if foreign:
            raise ForeignChartRowError(
                f"life_events read for chart {cid} returned {len(foreign)} row(s) of another chart "
                f"(relation={relation}); refusing to return any row"
            )
        _restore_guc(conn, prev)
        _savepoint(conn, "RELEASE SAVEPOINT")
        return rows
    except BaseException:
        try:
            _savepoint(conn, "ROLLBACK TO SAVEPOINT")
            _savepoint(conn, "RELEASE SAVEPOINT")
        except Exception:                                  # the connection may already be unusable; the original error wins
            logger.debug("life_events_scope: rollback to savepoint failed", exc_info=True)
        raise


def resolve_life_event_text(conn: Any, chart_id: Any, event_ref: Any) -> str | None:
    """The `description` of life event `event_ref` of THIS chart, for an entitled role; None when the id is unknown OR belongs to another chart.

    Reads the BASE table (the view carries no free text), so a role without SELECT on it gets InsufficientPrivilege (loud, never None)."""
    cid = normalize_chart_id(chart_id)
    ref = normalize_chart_id(event_ref)                      # an id is a uuid: same strict parse (malformed raises)
    _savepoint(conn, "SAVEPOINT")
    try:
        prev = _pin_guc(conn, str(cid))
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(f"SELECT description, chart_id FROM {BASE_TABLE} WHERE chart_id = %s AND id = %s", (cid, ref))
            rows = [dict(r) for r in cur.fetchall()]
        if any(str(r.get("chart_id")) != str(cid) for r in rows):
            raise ForeignChartRowError(f"life_events lookup for chart {cid} returned a row of another chart")
        _restore_guc(conn, prev)
        _savepoint(conn, "RELEASE SAVEPOINT")
        return rows[0]["description"] if rows else None
    except BaseException:
        try:
            _savepoint(conn, "ROLLBACK TO SAVEPOINT")
            _savepoint(conn, "RELEASE SAVEPOINT")
        except Exception:
            logger.debug("life_events_scope: rollback to savepoint failed", exc_info=True)
        raise
