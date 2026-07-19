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
this sandbox" cases). Instead, `safe_rollback` is called at sub-step
boundaries WITHIN this package's own code, right after any of ITS OWN
try/except blocks around a G-1/G-2 call catches something -- resetting the
connection's transaction state so the NEXT query in the sequence gets a
fair, uncontaminated attempt rather than inheriting a poisoned transaction.
Always a no-op (never raises) on an autocommit connection or when `conn` is
None; this module never performs a WRITE, so a rollback here can never lose
committed work -- G-3 is entirely read-only against the live database.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def safe_rollback(conn) -> None:
    if conn is None:
        return
    try:
        if getattr(conn, "autocommit", False):
            return
        conn.rollback()
    except Exception as exc:  # noqa: BLE001
        logger.debug("[gochara_intensity._dbutil] safe_rollback no-op/failed (non-fatal): %s", exc)


__all__ = ["safe_rollback"]
