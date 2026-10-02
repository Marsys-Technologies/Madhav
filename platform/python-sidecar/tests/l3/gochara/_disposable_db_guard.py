"""ONE guard for every A5.3 disposable-database fixture (steward M…154825, Stream B's audit).

A fixture that connects to "whatever the admin DSN says" and then CREATEs/DROPs databases and cluster roles is only safe if the DSN can
reach nothing but the local disposable server. `urlparse(dsn).hostname` is NOT such a check: `postgresql://u:p@localhost:5432,db.prod:5432/x`
reports only the first host, and libpq fails over to the second. So, before any connection:

  * a COMMA anywhere in the netloc / host / hostaddr / port is refused (multi-host failover);
  * the DSN is PARSED BY LIBPQ's own parser (`psycopg.conninfo`) — query-string `host=`/`hostaddr=`, keyword/value form and URL form all
    reduce to the same dict — and must carry EXACTLY ONE explicit host or hostaddr, each loopback (`localhost`, a 127.0.0.0/8 or ::1
    address) or a unix-socket directory (starts with '/'); an implicit host (the environment/default) is refused;
  * `service=` / `servicefile=` and the environment's PGHOST, PGHOSTADDR, PGSERVICE, PGSERVICEFILE (which libpq would otherwise honour
    behind our back) are refused;

and, after connecting but BEFORE any destructive statement, the SERVER'S address (`inet_server_addr()`) must be loopback (NULL = a unix
socket). A hostile DSN is a configuration ERROR, never a skip. The reference implementations are Stream B's libpq-parsed guard and Kimi's C24
shared helper on main; converge on that helper once it merges."""
from __future__ import annotations

import ipaddress
import os
from typing import Any, Mapping

LOOPBACK_NAMES = frozenset({"localhost", "ip6-localhost"})
FORBIDDEN_ENV = ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE")


class UnsafeAdminDSN(RuntimeError):
    """The admin DSN (or the environment) could reach a server other than the local disposable one."""


def _is_loopback_host(value: str) -> bool:
    if value.startswith("/"):                       # a unix-socket directory
        return True
    if value.lower() in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(value.strip("[]")).is_loopback
    except ValueError:
        return False


def check_admin_dsn(dsn: str, env: Mapping[str, str] | None = None) -> dict[str, str]:
    """No connection is made. Returns the libpq-parsed parameters; raises `UnsafeAdminDSN` for every hostile form."""
    from psycopg.conninfo import conninfo_to_dict
    env = os.environ if env is None else env
    if not isinstance(dsn, str) or not dsn.strip():
        raise UnsafeAdminDSN("the admin DSN is empty")
    set_env = [k for k in FORBIDDEN_ENV if k in env]
    if set_env:
        raise UnsafeAdminDSN(f"{set_env} are set in the environment: libpq would honour them behind the DSN's back")
    if "://" in dsn:
        authority = dsn.split("://", 1)[1].split("/", 1)[0].split("?", 1)[0]
        if "," in authority.rsplit("@", 1)[-1]:
            raise UnsafeAdminDSN("a comma in the DSN's netloc names several hosts (libpq fails over to the next)")
    try:
        parts = conninfo_to_dict(dsn)
    except Exception as exc:  # noqa: BLE001 — a DSN libpq cannot parse is not one we will connect with
        raise UnsafeAdminDSN(f"the admin DSN does not parse: {exc}") from exc
    for key in ("service", "servicefile"):
        if key in parts:
            raise UnsafeAdminDSN(f"{key}= pulls connection parameters from a service file")
    for key in ("host", "hostaddr", "port"):
        if "," in str(parts.get(key, "")):
            raise UnsafeAdminDSN(f"{key}={parts[key]!r} names several servers")
    explicit = [parts[k] for k in ("host", "hostaddr") if parts.get(k)]
    if not explicit:
        raise UnsafeAdminDSN("the DSN names no explicit host or hostaddr (the environment/default would decide)")
    bad = [v for v in explicit if not _is_loopback_host(v)]
    if bad:
        raise UnsafeAdminDSN(f"{bad} is not a loopback host or a unix-socket directory")
    return parts


def assert_loopback_server(conn: Any) -> str:
    """After connecting, BEFORE any CREATE/DROP: the server answered from a loopback address (or a unix socket)."""
    row = conn.execute("SELECT inet_server_addr()").fetchone()
    addr = row[0] if not isinstance(row, dict) else next(iter(row.values()))
    if addr is None:
        return "unix-socket"
    if not ipaddress.ip_address(str(addr).split("/")[0]).is_loopback:
        raise UnsafeAdminDSN(f"the connected server's address is {addr}, not loopback — refusing every destructive statement")
    return str(addr)


def guarded_admin_connect(dsn: str, **kwargs):
    """`psycopg.connect` for an ADMIN DSN: static DSN check → connect → server-address check. The returned connection is safe to
    CREATE/DROP databases and roles on. Unreachable ⇒ the connection error propagates (the fixture decides skip/fail); hostile ⇒
    `UnsafeAdminDSN` (never a skip)."""
    import psycopg
    check_admin_dsn(dsn)
    conn = psycopg.connect(dsn, **kwargs)
    try:
        assert_loopback_server(conn)
    except Exception:
        conn.close()
        raise
    return conn
