"""Disposable-database guards for Stream B's live-DB test fixtures (steward M20261002T154223-eb38: a guard that reads `urlparse().hostname` sees only the FIRST host of a
multi-host DSN — `postgresql://u:p@localhost:5432,db.prod.example.com:5432/x` — and libpq can fail over to the second host, after which a fixture drops and creates
objects). The rule here: parse with libpq's own parser, refuse any comma in the host or hostaddr, require an EXPLICIT loopback host (and hostaddr, if present), refuse
`service=` and the PGHOST / PGHOSTADDR / PGSERVICE / PGSERVICEFILE environment overrides, optionally require the exact database name — and, AFTER connecting and BEFORE any
destructive statement, assert the database and the server address actually reached. (Kimi's C24 fixes main's shared helper; reuse it once merged.)"""
from __future__ import annotations

import os
import re

LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
LOOPBACK_ADDRS = frozenset({"127.0.0.1", "::1"})
ENV_OVERRIDES = ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE")


class NotDisposable(RuntimeError):
    """The DSN or the connection is not provably a loopback, disposable database: refuse before anything destructive."""


def assert_disposable_dsn(dsn: str, *, dbname: str | None = None) -> dict:
    """Return the parsed conninfo, or raise `NotDisposable`. Pure: opens no connection."""
    from psycopg.conninfo import conninfo_to_dict
    if not isinstance(dsn, str) or not dsn.strip():
        raise NotDisposable("no DSN supplied")
    for k in ENV_OVERRIDES:
        if os.environ.get(k):
            raise NotDisposable(f"{k} is set in the environment: it can redirect the connection away from the explicit host")
    m = re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://([^/?#]*)", dsn)
    if m and "," in m.group(1).rsplit("@", 1)[-1]:
        raise NotDisposable("a multi-host DSN is refused (libpq can fail over to a later host)")
    try:
        d = conninfo_to_dict(dsn)
    except Exception as exc:                                       # noqa: BLE001
        raise NotDisposable(f"the DSN is not parseable by libpq: {exc}") from exc
    if d.get("service"):
        raise NotDisposable("a `service=` entry is refused (it can supply the host from a file)")
    host, hostaddr = d.get("host", ""), d.get("hostaddr", "")
    if not host:
        raise NotDisposable("no explicit host: the driver would use a default or PGHOST — an explicit loopback host is required")
    if "," in host or "," in hostaddr:
        raise NotDisposable("a multi-host DSN is refused (libpq can fail over to a later host)")
    if host not in LOOPBACK_HOSTS and not host.startswith("/"):                 # a local unix-socket directory is also local
        raise NotDisposable(f"host {host!r} is not an explicit loopback host")
    if hostaddr and hostaddr not in LOOPBACK_ADDRS:
        raise NotDisposable(f"hostaddr {hostaddr!r} is not a loopback address")
    if dbname is not None and d.get("dbname") != dbname:
        raise NotDisposable(f"the DSN names database {d.get('dbname')!r}, not the expected {dbname!r}")
    return d


def assert_connected_to(conn, *, expected_db: str | None = None) -> None:
    """After connecting and BEFORE any destructive statement: the database and the server address the session actually reached."""
    db, addr = conn.execute("SELECT current_database(), host(inet_server_addr())").fetchone()
    if expected_db is not None and db != expected_db:
        raise NotDisposable(f"connected to database {db!r}, expected {expected_db!r}")
    if addr is not None and addr not in LOOPBACK_ADDRS:                         # NULL = a unix socket (local)
        raise NotDisposable(f"the server answered from {addr}, which is not loopback")


__all__ = ["NotDisposable", "assert_connected_to", "assert_disposable_dsn"]
