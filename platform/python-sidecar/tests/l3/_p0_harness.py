"""Shared harness helpers for the L3 Kāla P0 safety regression tests.

Phase 0.2 of the Kāla (L3) pre-elevation setup campaign.
`MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §5 row P0 names two hazards and
demands, verbatim:

    "Zero planning/dry-run mutations; crash/resume and empty-generation tests;
     restore prior data/outcomes."

These tests satisfy that by EXECUTING the real writer code paths against a
disposable Postgres that carries production's schema AND its trigger layer —
never by asserting on code shape.

── WHY A DISPOSABLE POSTGRES, AND WHY THE TRIGGERS MATTER ─────────────────────
A table-scoped `pg_dump -t public.<table>` does NOT carry the trigger FUNCTIONS
those tables' triggers reference — every `CREATE TRIGGER` in such a dump fails
with `function public.<name>() does not exist`, leaving a harness with the
tables but none of production's guard layer. A run against that harness proves
nothing about production behaviour. The harness this module targets is built
functions-first (see the bootstrap script referenced in
`00_ARCHITECTURE/briefs/nirmana/l3_autonomous/setup/PHASE0_2_P0_SAFETY_EVIDENCE.md`
§2) so `l2_data_plane_guard_active_mutation`, `l2_data_plane_capture_row`,
`nirmana_invalidate_chart_receipts`, `phala_anchors_set_identity` and their
helpers are live while the writers run.

Set `KALA_P0_HARNESS_DSN` to point at your own instance. With no harness
reachable, every test in these modules SKIPS — it never silently passes
(§N.8: a signal with no detector behind it is null, not green).
"""
from __future__ import annotations

import os
import re
import sys
import uuid
from urllib.parse import parse_qsl, unquote, urlsplit

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

#: Default matches the Phase 0.2 bootstrap (port 59510, socket dir /tmp/kp0).
HARNESS_DSN = os.environ.get(
    "KALA_P0_HARNESS_DSN",
    "postgresql://kxuser@/kala_harness?host=/tmp/kp0&port=59510",
)



# ── destructive-test database guard (Track I-8, SS ruling) ──────────────────────
# The P0 DB tests DELETE the canonical chart's rows from four Kala tables in `_reset`. They must
# only ever run against a disposable database. Same rule as the B2 test's `isSafeTestDbUrl`
# (platform/tests/integration/downstream_dependents.db.test.ts): PARSE the connection target (a bare
# substring match over the whole DSN is how the original guard was bypassed), require a LOCAL host
# (loopback, or a unix-socket directory) AND a disposable database name; refuse otherwise.
_SAFE_DB_NAME = re.compile(r"^(kala_harness|kala_p0_harness|[a-z0-9]+(_[a-z0-9]+)*_(test|harness|disposable|scratch))$")
_PROD_TOKEN = re.compile(r"(^|_)(prod|production|live|amjis)(_|$)")
_LOOPBACK = {"127.0.0.1", "localhost", "[::1]", "::1"}


class HarnessSafetyError(RuntimeError):
    """The P0 harness was pointed at something that is not a disposable database."""


def _conninfo(dsn: str) -> dict[str, str]:
    """libpq conninfo as a dict, from a postgresql:// URL or a `key=value` string. Never raises."""
    dsn = (dsn or "").strip()
    out: dict[str, str] = {}
    if re.match(r"^postgres(ql)?://", dsn):
        try:
            u = urlsplit(dsn)
            u.hostname, u.port  # noqa: B018 - force the lazy parse errors here
        except ValueError:
            return {"dbname": "/unparseable"}
        if u.hostname:
            out["host"] = u.hostname if ":" not in u.hostname else f"[{u.hostname}]"
        out["dbname"] = unquote(u.path.lstrip("/")) if u.path.count("/") <= 1 else "/bad-path"
        out.update({k: v for k, v in parse_qsl(u.query)})  # query `host=`/`dbname=` override
        return out
    for m in re.finditer(r"(\w+)\s*=\s*('(?:[^'\\]|\\.)*'|\S+)", dsn):
        out[m.group(1)] = m.group(2).strip("'")
    return out


def is_safe_harness_dsn(dsn: str) -> bool:
    """True only for a local host AND a disposable, non-production-looking database name."""
    info = _conninfo(dsn)
    if info.get("service"):
        return False  # a pg_service.conf entry can redirect host/dbname to a remote server
    name = info.get("dbname", "")
    if not _SAFE_DB_NAME.match(name) or _PROD_TOKEN.search(name):
        return False
    for key in ("host", "hostaddr"):
        for h in (info.get(key) or "").split(","):
            if h and not (h in _LOOPBACK or h.startswith("/")):
                return False
    return True


def assert_safe_harness_dsn(dsn: str = None) -> None:
    dsn = HARNESS_DSN if dsn is None else dsn
    if not is_safe_harness_dsn(dsn):
        raise HarnessSafetyError(
            "refusing to run destructive P0 tests: KALA_P0_HARNESS_DSN must be a LOCAL database with a "
            "disposable name (kala_harness, or *_test/_harness/_disposable/_scratch), got "
            f"{_conninfo(dsn).get('dbname')!r} on {_conninfo(dsn).get('host')!r}"
        )


def assert_disposable_connection(conn) -> None:
    """Runtime twin of the DSN check: the server's own `current_database()` must be disposable."""
    with conn.cursor() as cur:
        cur.execute("SELECT current_database() AS d")
        row = cur.fetchone()
    name = row["d"] if isinstance(row, dict) else row[0]
    if not _SAFE_DB_NAME.match(name) or _PROD_TOKEN.search(name):
        raise HarnessSafetyError(f"refusing to run: connected database {name!r} is not disposable")


def connect():
    """A harness connection shaped exactly like the orchestrator's own.

    `pipeline/orchestrator/db.py:46-70` builds the real build-session connection
    with `row_factory=psycopg.rows.dict_row` and `statement_timeout = 0` (that
    file documents the ~20-minute pure-CPU substep this protects). Writers index
    rows by column name, so a harness connection without `dict_row` would fail
    for a reason that has nothing to do with the hazard under test.
    """
    assert_safe_harness_dsn(HARNESS_DSN)  # refuse (raise), never skip, a non-disposable target
    try:
        import psycopg
        import psycopg.rows
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"psycopg (v3) unavailable: {exc}")
    # A production dbenv may export PGOPTIONS=-c default_transaction_read_only=on
    # and PG* connection vars; neither may leak into the disposable harness.
    saved = {k: os.environ.pop(k) for k in (
        "PGHOST", "PGPORT", "PGUSER", "PGPASSWORD", "PGDATABASE",
        "PGOPTIONS", "PGSERVICE", "DATABASE_URL",
    ) if k in os.environ}
    try:
        conn = psycopg.connect(HARNESS_DSN, row_factory=psycopg.rows.dict_row)
    except Exception as exc:  # pragma: no cover - harness-dependent
        pytest.skip(f"P0 harness Postgres not reachable ({HARNESS_DSN!r}): {exc}")
    finally:
        os.environ.update(saved)
    conn.autocommit = False
    try:
        assert_disposable_connection(conn)  # the server's own current_database(), not just the DSN text
    except HarnessSafetyError:
        conn.close()
        raise
    with conn.cursor() as cur:
        cur.execute("SET statement_timeout = 0")
    return conn


def make_ctx(conn, asset_id, chart_id=CANONICAL_CHART_ID, dry_run=False):
    from pipeline.orchestrator.writers import ContextSpec

    return ContextSpec(
        asset_id=asset_id,
        build_id=str(uuid.uuid4()),
        db_conn=conn,
        config={"chart_id": chart_id},
        dry_run=dry_run,
    )


# ── the detectors ─────────────────────────────────────────────────────────────

def xid(conn):
    """The transaction's assigned xid, or None.

    THE detector for "this code path performed no write". Postgres assigns a
    real transaction id LAZILY — only when a transaction first writes. A
    transaction that has only read has `txid_current_if_assigned() IS NULL`.
    (`txid_current()` would ASSIGN one and destroy the measurement; it is
    deliberately not used.) This cannot be satisfied by a writer that merely
    looks read-only: an INSERT that is later rolled back still assigns an xid.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT txid_current_if_assigned() AS x")
        return cur.fetchone()["x"]


def content_digest(conn, tables, chart_id=CANONICAL_CHART_ID):
    """(row_count, md5-of-content) per table, scoped to one chart.

    The independent second detector. `xid` proves no write statement executed;
    this proves the observable content is identical, and is the form that also
    answers the strategy's "restore prior data/outcomes" clause.
    """
    out = {}
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(
                f"SELECT count(*) AS n,"
                f" md5(coalesce(string_agg(t.rowtext, '|' ORDER BY t.rowtext), '')) AS d"
                f" FROM (SELECT x::text AS rowtext FROM {table} x"
                f"        WHERE x.chart_id = %s) t",
                (chart_id,),
            )
            row = cur.fetchone()
            out[table] = (row["n"], row["d"])
    return out


def owned_tables():
    """The writer's OWN declaration of what it owns — not a copy of it.

    Reading `_OWNED_TABLES` from the module under test means a table added to
    the writer's replacement set is automatically covered by the digest
    detector, rather than silently escaping it.
    """
    from services.ka_kshetra.writer import _OWNED_TABLES

    return [t for t, _pred in _OWNED_TABLES]


def xact_tuple_counters(conn, tables):
    """Per-table (inserted, updated, deleted) tuple counters for THIS transaction.

    The detector to use when the code path under test legitimately takes row
    locks. MEASURED on the harness (not assumed):

        SELECT ... FOR UPDATE  -> assigns an xid, counters stay 0/0/0
        DELETE (1 row matched) -> counters move to 0/0/1

    So `xid()` reports true for a pure row-lock, while these counters report
    only real tuple modifications. `ka_bhavishya_lekha` takes `FOR UPDATE` on
    the chart's existing projections BEFORE deciding whether to write, so for
    that writer `xid()` is the wrong instrument and this is the right one.
    `ka_kshetra.plan_substeps` takes no locks at all, so `xid()` is exact there.
    """
    out = {}
    with conn.cursor() as cur:
        for table in tables:
            cur.execute(
                "SELECT pg_stat_get_xact_tuples_inserted(%s::regclass) AS i,"
                "       pg_stat_get_xact_tuples_updated(%s::regclass) AS u,"
                "       pg_stat_get_xact_tuples_deleted(%s::regclass) AS d",
                (table, table, table),
            )
            r = cur.fetchone()
            out[table] = (r["i"], r["u"], r["d"])
    return out
