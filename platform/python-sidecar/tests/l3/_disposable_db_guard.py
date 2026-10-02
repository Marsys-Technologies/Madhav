"""C24 (steward M20261002T154223-e3e1) — ONE shared disposable-database guard
for every py-sidecar DB test fixture that DROPs / CREATEs schema objects or
cluster roles.

THE ATTACK THIS CLOSES
══════════════════════
The C7 guard (tests/l3/_builder_role.py, pre-C24) checked the host with
``urlparse(dsn).hostname`` — which sees only the FIRST host of a multi-host
DSN. ``postgresql://u:p@localhost:5432,db.prod.example.com:5432/db`` PASSED
while libpq can fail over to the second host, and the fixture then DROPs and
recreates a schema there. The same blind spot existed for keyword/value DSNs,
``host=``/``hostaddr=`` smuggled into the query string, and the libpq
environment variables (PGHOST / PGHOSTADDR / PGSERVICE / PGSERVICEFILE) libpq
merges into every connection.

WHAT THE GUARD REQUIRES (all of them, or it refuses)
════════════════════════════════════════════════════
  1. no comma anywhere in the URI netloc (fast multi-host reject — urlparse
     cannot be trusted to see past the first host);
  2. parsed with psycopg's OWN conninfo parser (conninfo_to_dict — the same
     libpq-faithful interpretation the connection will actually use), valid
     for BOTH URI and keyword/value DSNs: EVERY host AND hostaddr entry
     (comma-separated lists included) must be loopback
     (localhost / 127.0.0.1 / ::1);
  3. the dbname is EXACTLY the fixture's expected name (unless the caller
     passes expected_dbname=None — the wp10 fixture, whose admin DSN targets
     the cluster's admin database while the fixture CREATEs its own uniquely
     named disposable database; host discipline still applies in full);
  4. PGHOST, PGHOSTADDR, PGSERVICE and PGSERVICEFILE are absent from the
     environment (libpq merges them into the parsed DSN — an override the
     string itself does not show);
  5. assert_disposable_connection(): AFTER connecting, current_database()
     equals the expected name AND inet_server_addr() is loopback or NULL
     (a unix-socket connection) — checked before any destructive statement.

Pure string checks connect to nothing; only step 5 needs a connection.
"""
from __future__ import annotations

import os
from urllib.parse import urlparse

from psycopg.conninfo import conninfo_to_dict

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}
DANGEROUS_ENV_VARS = ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE")


class RefusedError(RuntimeError):
    """The disposable-identity guard refused the connection target."""


def _is_loopback(value: str | None) -> bool:
    if not value:
        return False
    # psycopg reports an IPv6 literal without brackets; a URI carries '[::1]'.
    return value.strip().strip("[]") in LOOPBACK_HOSTS


def _every_entry_loopback(value: str | None) -> bool:
    """Every entry of a (possibly comma-separated) host/hostaddr list is loopback."""
    if value is None:
        return True  # absent — nothing to fail over to
    entries = [e.strip() for e in value.split(",") if e.strip()]
    return bool(entries) and all(_is_loopback(e) for e in entries)


def validate_disposable_dsn(
    dsn: str,
    expected_dbname: str | None,
    *,
    env: dict | None = None,
) -> dict:
    """Refuse unless `dsn` targets loopback everywhere (and, when given, the exact
    disposable dbname). Returns the parsed conninfo dict. Connects to nothing.

    expected_dbname=None is for fixtures that CREATE their own database on a
    disposable cluster (host discipline only); the post-connect check must then
    be done with assert_disposable_connection against the created name.
    """
    env = os.environ if env is None else env
    for var in DANGEROUS_ENV_VARS:
        if env.get(var, "").strip():
            raise RefusedError(
                f"REFUSED: {var} is set in the environment — libpq merges it into "
                "every connection, so the DSN string alone does not decide the target")
    parsed_uri = urlparse(dsn)
    if parsed_uri.netloc and "," in parsed_uri.netloc:
        raise RefusedError(
            f"REFUSED: multi-host DSN (comma in netloc {parsed_uri.netloc!r}) — "
            "libpq can fail over to any of the hosts; a disposable fixture takes "
            "exactly one loopback host")
    try:
        info = conninfo_to_dict(dsn)
    except Exception as exc:
        raise RefusedError(f"REFUSED: unparseable DSN ({exc})") from exc
    if not _every_entry_loopback(info.get("host")):
        raise RefusedError(
            f"REFUSED: DSN host {info.get('host')!r} is not loopback on every entry")
    if not _every_entry_loopback(info.get("hostaddr")):
        raise RefusedError(
            f"REFUSED: DSN hostaddr {info.get('hostaddr')!r} is not loopback on every entry")
    if info.get("service"):
        raise RefusedError(
            "REFUSED: DSN names a pg_service — the service file decides the real target")
    if expected_dbname is not None and info.get("dbname") != expected_dbname:
        raise RefusedError(
            f"REFUSED: database {info.get('dbname')!r} is not the disposable "
            f"{expected_dbname!r} — this fixture drops schema objects and alters "
            "cluster roles")
    return info


def assert_disposable_connection(conn, expected_dbname: str) -> None:
    """Post-connect proof, before ANY destructive statement: the session really is
    on the disposable database and on a loopback (or local unix-socket) server."""
    row = conn.execute(
        "SELECT current_database(), inet_server_addr()::text").fetchone()
    dbname, server_addr = row[0], row[1]
    if dbname != expected_dbname:
        raise RefusedError(
            f"REFUSED: connected to database {dbname!r}, not the disposable "
            f"{expected_dbname!r}")
    if server_addr is not None and not _is_loopback(server_addr):
        raise RefusedError(
            f"REFUSED: the server reports a non-loopback address {server_addr!r} — "
            "the connection did not land where the DSN claimed")
