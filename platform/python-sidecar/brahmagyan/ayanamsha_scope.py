"""Chart-scoped ayanamsha set (ONE_AYANAMSHA Phase 1, SS N-309/N-311).

Every builder used to carry its own literal list of the five ayanamsha ids. This module is the single
place that answers "which ayanamshas does THIS chart build?":

    ayanamshas_for_chart(conn, chart_id) -> list[str]

* Default (no configuration anywhere): the five canonical ids, in canonical order. Phase 1 changes NO
  behaviour because nothing configures anything yet.
* Configuration: `charts.build_ayanamshas text[]` (added by a later, routine ALTER TABLE migration; NULL or
  empty = the default). Until that column exists the helper simply returns the five (checked once per
  minute, not per call). The legacy control field `charts.ayanamsa` is deliberately NOT read: it says
  'lahiri' on every chart, in another vocabulary.
* The pipeline's chart key is `charts.id` (for some charts `charts.chart_id` is a different uuid).
* A configured value is validated: unknown ids raise, duplicates are dropped, the result is always in
  canonical order, an empty/blank configured list raises rather than silently widening to five.

No psycopg import: the caller passes its own connection (ctx.db_conn). Never commits or closes it.
"""
from __future__ import annotations

import time
from typing import Any, Iterable

CANONICAL_FIVE: tuple[str, ...] = (
    "lahiri_chitrapaksha",
    "true_chitra",
    "krishnamurti",
    "raman",
    "surya_siddhanta_classical",
)

_COLUMN_TTL_S = 60.0
_column_cache: dict[str, Any] = {"at": None, "present": False}
_monotonic = time.monotonic          # injectable for tests


class AyanamshaScopeError(ValueError):
    """A configured ayanamsha set is invalid (unknown id, or configured but empty)."""


def default_ayanamshas() -> list[str]:
    return list(CANONICAL_FIVE)


def normalize_scope(values: Iterable[str]) -> list[str]:
    """Validate a configured set: ids must be canonical; result is de-duplicated, in canonical order."""
    seen = {str(v).strip() for v in values if v is not None and str(v).strip()}
    if not seen:
        raise AyanamshaScopeError("configured ayanamsha set is empty (use NULL for the default five)")
    unknown = sorted(seen - set(CANONICAL_FIVE))
    if unknown:
        raise AyanamshaScopeError(f"unknown ayanamsha id(s) {unknown}; allowed {list(CANONICAL_FIVE)}")
    return [a for a in CANONICAL_FIVE if a in seen]


def _first_value(row: Any) -> Any:
    if row is None:
        return None
    if isinstance(row, dict):
        return next(iter(row.values()), None)
    return row[0]


def _column_present(conn: Any) -> bool:
    now = _monotonic()
    at = _column_cache["at"]
    if at is not None and now - at < _COLUMN_TTL_S:
        return bool(_column_cache["present"])
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = 'charts' AND column_name = 'build_ayanamshas'"
        )
        present = cur.fetchone() is not None
    _column_cache["at"], _column_cache["present"] = now, present
    return present


def reset_cache() -> None:
    """Forget the cached column check (tests, and after the migration that adds the column)."""
    _column_cache["at"], _column_cache["present"] = None, False


def ayanamshas_for_chart(conn: Any, chart_id: Any) -> list[str]:
    """The ayanamsha ids this chart builds, in canonical order (default: all five)."""
    if not _column_present(conn):
        return default_ayanamshas()
    with conn.cursor() as cur:
        cur.execute("SELECT build_ayanamshas FROM charts WHERE id = %s::uuid", (str(chart_id),))
        value = _first_value(cur.fetchone())
    if value is None:
        return default_ayanamshas()
    return normalize_scope(value)
