"""
gochara_intensity._dbutil — tiny connection-hygiene helper.

Live-verification at G-3 build time (chart 482012f1) surfaced a real
operational hazard specific to this engine's shape: `compute_lambda_e`
issues MANY sequential defensive-catch queries per instant (through G-1's
`resonance_map`, G-2's `dasha_data`/`primitives`, and this package's own
`valence`/`engine.fetch_temporal_shape`). On a non-autocommit connection, if
ANY single query in that sequence raises (a real DB-shape surprise, or
simply querying a table that happens not to exist in a given environment),
psycopg leaves the connection's transaction in "aborted" state -- EVERY
subsequent query on that same connection then fails with "current
transaction is aborted, commands ignored until end of transaction block",
even though each individual query is independently caught and degrades to
an honest empty result. The net effect, observed live: one early failure
silently zeroes out PROMISE/PERMISSION/X(t) for the rest of that
`compute_lambda_e` call (and any later call reusing the same connection),
NOT because the data was actually absent, but because the connection's
transaction state was poisoned by an unrelated earlier query.

This module cannot fix the root queries (they live in G-1/G-2's
must_not_touch code, or are simply real, expected "table doesn't exist in
this sandbox" cases).

## D-5 G-4 incident (2026-07-19/20, job brahma-build-pipeline-job-kb4zr) --
## SAVEPOINT-SAFETY CORRECTION (full sweep)

The ORIGINAL version of this module's `safe_rollback(conn)` called a bare
`conn.rollback()` -- a FULL transaction rollback. That is only harmless when
`conn` has no OUTER savepoint on it (a true standalone connection with no
enclosing transaction control). It is NOT harmless when this code runs
inside `pipeline.orchestrator.asset_runner._drive_substeps`'s `SAVEPOINT
writer_exec` -- which `ka_gochara_sweep` (G-4) does: G-4's `run_substep`
calls straight into `gochara_grammar.primitives` AND `gochara_intensity.
engine` / `permission` / `valence` / `enrichment` / `configuration_activity`,
every one of which called this module's old `safe_rollback`. A bare
`conn.rollback()` on Postgres destroys EVERY savepoint on the connection,
including an outer one it didn't create -- so when the orchestrator later
tries `RELEASE SAVEPOINT writer_exec`, that savepoint no longer exists
(`InvalidSavepointSpecification`), and the cascading attempt to record the
error via `mark_asset_error` then also fails (`InFailedSqlTransaction`)
because the connection is left fully aborted with no valid savepoint to
unwind to.

The fix, applied across every call site in this package (`primitives.py`,
`engine.py`, `permission.py`, `valence.py`, `enrichment.py`,
`configuration_activity.py`, `ka_gochara_sweep/sweep.py`):
`savepoint_scope(conn, label)` wraps a risky read (or a call into
G-1/G-2 must_not_touch code that might itself hit a DB-shape surprise) in
its OWN uniquely-named SAVEPOINT (`SAVEPOINT <name>` before, `RELEASE
SAVEPOINT <name>` on success, `ROLLBACK TO SAVEPOINT <name>` on failure).
This is safe to nest arbitrarily deep -- a SAVEPOINT is valid as the very
first statement of a transaction too, so it degrades gracefully to "just
this block's own undo point" when there is no outer savepoint (standalone
usage), and it never touches any OUTER savepoint or the ambient transaction
when there is one (G-4 orchestrator-driven usage).

Two call shapes exist across this package, and `savepoint_scope` handles
both:
  1. A query that RAISES on failure, caught by the caller's own
     `try/except` (`primitives.py`'s `_fetch_*` helpers, `engine.py`'s
     `fetch_temporal_shape`, `permission.py`'s several DB reads). Handled by
     the block-raises path: `ROLLBACK TO SAVEPOINT` + re-raise.
  2. A call into ANOTHER function (typically G-1/G-2 must_not_touch code
     like `resonance_map.fetch_resonance_targets` or `dasha_data.
     fetch_dasha_periods`) that catches its OWN DB exception internally and
     returns an honest degraded result WITHOUT re-raising -- so from this
     module's point of view the wrapped block "succeeds", but the
     connection may have been left in Postgres' aborted-transaction state
     by the swallowed exception. Handled by the success path's RELEASE
     fallback below: if `RELEASE SAVEPOINT` itself fails (the tell that the
     transaction is aborted despite no exception surfacing), this falls
     back to `ROLLBACK TO SAVEPOINT` on the SAME savepoint to un-abort the
     connection -- still never touching anything outside this savepoint.

`safe_rollback` (the bare-`conn.rollback()` helper) has been REMOVED
entirely: after this fix there are zero remaining call sites (confirmed via
`grep -rn "safe_rollback" services/gochara_intensity services/gochara_grammar
services/ka_gochara_sweep`, excluding this module's own docstrings/tests),
so keeping a dangerous, unused function around as an "attractive nuisance"
for future code to accidentally reach for was judged worse than deleting it.
"""
from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger(__name__)


def _new_savepoint_name(label: str) -> str:
    """Build a unique, SQL-identifier-safe savepoint name.

    Postgres savepoint names are identifiers, not bindable query parameters
    -- `SAVEPOINT %s` / `cur.execute("SAVEPOINT %s", [name])` is not valid
    SQL, so a savepoint name can never be passed the normal parameterized
    way. This never interpolates the caller-supplied `label` directly: it is
    reduced to an allowlisted `[A-Za-z0-9_]` token (every other character
    dropped) and combined with a `uuid.uuid4().hex` suffix, which is what
    actually guarantees uniqueness -- a per-process counter would collide
    across threads/greenlets/re-entrant calls sharing one connection,
    whereas a UUID4 suffix carries no shared mutable state and cannot
    collide in practice. The result is composed into the `SAVEPOINT
    <name>` / `RELEASE SAVEPOINT <name>` / `ROLLBACK TO SAVEPOINT <name>`
    strings directly (deliberately NOT via `psycopg.sql.Identifier`, so this
    helper has no hard psycopg dependency and works uniformly against any
    DB-API-shaped connection -- including the plain `sqlite3` connection
    `tests/test_gochara_grammar.py`'s orchestrator-savepoint-survival test
    uses to prove this property without a live Postgres); safety comes
    entirely from the fact that the name is 100% code-generated from an
    allowlisted character set, never from raw untrusted input.
    """
    safe_label = "".join(ch if (ch.isalnum() or ch == "_") else "_" for ch in label)[:40] or "sp"
    if not (safe_label[0].isalpha() or safe_label[0] == "_"):
        safe_label = f"sp_{safe_label}"
    return f"safe_{safe_label}_{uuid.uuid4().hex[:12]}"


@contextmanager
def savepoint_scope(conn, label: str) -> Iterator[None]:
    """Run the wrapped block inside its own uniquely-named SAVEPOINT.

    - On any exception raised inside the block: `ROLLBACK TO SAVEPOINT
      <name>` (undoing only what happened inside THIS block), then the
      original exception is re-raised unchanged -- callers keep their
      existing `try/except ...: return []` degrade pattern, just wrapping
      the query in `with savepoint_scope(conn, "..."):` instead of calling
      the old `safe_rollback(conn)` in the except clause.
    - On success (block returns normally): `RELEASE SAVEPOINT <name>`. If
      THAT fails -- which happens when the wrapped block called into other
      code (e.g. G-1/G-2 must_not_touch helpers) that caught its own DB
      exception internally and degraded without re-raising, silently
      leaving the transaction aborted -- this falls back to `ROLLBACK TO
      SAVEPOINT <name>` on the SAME savepoint to un-abort the connection.
      Both outcomes only ever touch THIS savepoint.
    - Never touches any OUTER savepoint or the ambient transaction -- safe
      to call whether or not the caller is itself already inside another
      SAVEPOINT (e.g. the orchestrator's `SAVEPOINT writer_exec`).
    - No-op passthrough when `conn` is None or the connection is in
      autocommit mode (no ambient transaction for a SAVEPOINT to nest
      inside; each statement is already its own transaction, so there is
      nothing to isolate).
    """
    if conn is None or getattr(conn, "autocommit", False):
        yield
        return

    name = _new_savepoint_name(label)
    # Safe to interpolate directly: `name` is 100% code-generated (allowlisted
    # chars + uuid4 hex) by `_new_savepoint_name`, never derived from
    # untrusted input -- see that function's docstring.
    savepoint_sql = f"SAVEPOINT {name}"
    release_sql = f"RELEASE SAVEPOINT {name}"
    rollback_sql = f"ROLLBACK TO SAVEPOINT {name}"

    try:
        conn.execute(savepoint_sql)
    except Exception as exc:  # noqa: BLE001
        # Can't even open a savepoint -- connection is already dead/closed
        # or in some state we can't safely act on. Nothing more we can do
        # here; let the caller's own try/except around the query handle it.
        logger.debug("[gochara_intensity._dbutil] savepoint_scope(%s) could not open SAVEPOINT: %s", label, exc)
        yield
        return

    try:
        yield
    except Exception:
        try:
            conn.execute(rollback_sql)
        except Exception as rb_exc:  # noqa: BLE001
            logger.debug(
                "[gochara_intensity._dbutil] savepoint_scope(%s) ROLLBACK TO SAVEPOINT %s failed "
                "(connection likely already dead): %s", label, name, rb_exc,
            )
        raise
    else:
        try:
            conn.execute(release_sql)
        except Exception as rel_exc:  # noqa: BLE001
            logger.debug(
                "[gochara_intensity._dbutil] savepoint_scope(%s) RELEASE SAVEPOINT %s failed "
                "(%s) -- wrapped code likely swallowed its own DB exception without re-raising; "
                "falling back to ROLLBACK TO SAVEPOINT %s to un-abort the connection.",
                label, name, rel_exc, name,
            )
            try:
                conn.execute(rollback_sql)
            except Exception as rb_exc:  # noqa: BLE001
                logger.debug(
                    "[gochara_intensity._dbutil] savepoint_scope(%s) fallback ROLLBACK TO SAVEPOINT "
                    "%s also failed (connection likely already dead): %s", label, name, rb_exc,
                )


__all__ = ["savepoint_scope"]
