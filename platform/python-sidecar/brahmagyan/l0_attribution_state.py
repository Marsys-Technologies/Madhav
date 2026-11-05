"""
brahmagyan.l0_attribution_state - carry the L0 ``attribution_state`` column across a delete-then-insert rebuild.

Context (SS N-111, pair of migration 1268). Migration 1268 adds ``attribution_state`` (``sourced | unsourced |
refuted``, nullable, NULL = not classified) to the L0 catalogues and backfills the token-exact states. The bg_doshas
and bg_yogas writers replace their catalogue wholesale (DELETE + INSERT, section N.3 of CLAUDE.md), and an INSERT that
does not name the column leaves it NULL: without this module every rebuild would silently reset the state (a signal
with no durability, section N.8). The orchestrator owns the surrounding transaction; nothing here commits.

Contract (kept minimal, deterministic, no LLM):
  * ``capture`` reads ``(natural key, state, citation)`` of every row that carries a state, BEFORE the writer's DELETE.
  * ``restore`` runs AFTER the writer's INSERTs and writes a captured state back to the row with the same natural key
    ONLY IF that row's citation is byte-identical to the captured one (jsonb text). A removed entry's state is
    dropped with its row. A re-cited entry's state is dropped too: the old state described the old citation, so
    carrying it would be a stale signal; the row is re-classified by the default rule below.
  * DEFAULT RULE (same as migration 1268, the only state a writer derives): a row still NULL whose citation is
    exactly the bare placeholder ``[{"text_id": "classical_tradition"}]`` becomes ``unsourced``. A new entry with a
    real citation stays NULL (not classified). ``sourced`` and ``refuted`` are never derived here.
  * If the column does not exist yet (writer deployed before migration 1268) both calls are no-ops and the writer
    behaves exactly as before.

Identifiers are module constants of the callers, never user input.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

PLACEHOLDER_CITATION_JSON = '[{"text_id": "classical_tradition"}]'


def _cell(row, name: str, idx: int):
    return row[name] if isinstance(row, dict) else row[idx]


def has_attribution_column(cur, table: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' "
        "AND table_name = %s AND column_name = 'attribution_state'",
        (table,),
    )
    return cur.fetchone() is not None


def capture(cur, table: str, key_col: str, citation_col: str):
    """Return ``None`` (column absent) or ``[(key, state, citation_text), ...]`` of rows carrying a state."""
    if not has_attribution_column(cur, table):
        return None
    cur.execute(
        f"SELECT {key_col} AS k, attribution_state AS s, {citation_col}::text AS c "
        f"FROM {table} WHERE attribution_state IS NOT NULL ORDER BY {key_col}"
    )
    return [(_cell(r, "k", 0), _cell(r, "s", 1), _cell(r, "c", 2)) for r in cur.fetchall()]


def restore(cur, table: str, key_col: str, citation_col: str, saved) -> dict[str, int]:
    """Write captured states back (same key AND same citation), then apply the default rule. No-op if ``saved is None``."""
    if saved is None:
        return {"carried": 0, "dropped": 0, "defaulted": 0, "column_absent": 1}
    carried = 0
    if saved:
        cur.execute(
            f"UPDATE {table} AS t SET attribution_state = v.s "
            f"FROM unnest(%s::text[], %s::text[], %s::text[]) AS v(k, s, c) "
            f"WHERE t.{key_col} = v.k AND t.{citation_col}::text = v.c",
            ([s[0] for s in saved], [s[1] for s in saved], [s[2] for s in saved]),
        )
        carried = cur.rowcount
    cur.execute(
        f"UPDATE {table} SET attribution_state = 'unsourced' "
        f"WHERE attribution_state IS NULL AND {citation_col} = %s::jsonb",
        (PLACEHOLDER_CITATION_JSON,),
    )
    defaulted = cur.rowcount
    stats = {"carried": carried, "dropped": len(saved) - carried, "defaulted": defaulted, "column_absent": 0}
    logger.info("[L0/attribution_state] %s: carried=%d dropped=%d defaulted=%d", table, carried, stats["dropped"], defaulted)
    return stats
