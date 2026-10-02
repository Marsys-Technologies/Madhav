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
  2. a URI whose query string carries dbname, host, hostaddr or service is
     refused outright (Suvarṇa F1: `…/x_test?dbname=madhav` connects to
     `madhav` while a path-only name check reads `x_test`); then parsed with
     psycopg's OWN conninfo parser (conninfo_to_dict — the same
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
     equals the expected name AND inet_server_addr() is NULL (a unix-socket
     connection) or loopback (v4-mapped IPv6 unwrapped before classifying);
     an RFC 1918 IPv4 address (EXACTLY 10/8, 172.16/12, 192.168/16 — not
     Python's wider is_private) is accepted ONLY inside GitHub Actions
     (Postgres runs there as a Docker service container and legitimately
     reports a bridge address such as 172.18.0.2 — everywhere else that
     shape is a local proxy to a remote database); everything else
     non-loopback is refused everywhere — checked before any destructive
     statement. NOT COVERED (documented): a loopback port tunnel to a remote
     server (ssh -L) whose address still reads loopback/NULL, and PGPORT.

Pure string checks connect to nothing; only step 5 needs a connection.
"""
from __future__ import annotations

import ipaddress
import os
from urllib.parse import parse_qs, urlparse

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
    # Suvarṇa re-look (M20261002T182540-5346): whitespace is refused up front,
    # as a RULE — newer libpq (18 / psycopg 3.3.x) TRIMS a trailing space, so a
    # whitespace-padded DSN can parse to the disposable name while the string
    # the caller audited is not the string libpq used. dsn != dsn.strip()
    # covers leading/trailing space, newline and tab, in both modes.
    if dsn != dsn.strip():
        raise RefusedError(
            "REFUSED: the DSN carries leading or trailing whitespace — the "
            "audited string must be exactly the string libpq parses")
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
    if "://" in dsn and parsed_uri.query:
        # F1 (Suvarṇa review): target-deciding options in a URI QUERY STRING are
        # refused outright — `postgresql://u@localhost/x_test?dbname=madhav`
        # connects to `madhav` while a path-only name check reads `x_test`.
        # (The keyword/value DSN form legitimately carries the same keys as
        # words, not a query string, and is fully parsed by conninfo below.)
        smuggled = {"dbname", "host", "hostaddr", "service"} & {
            k.lower() for k in parse_qs(parsed_uri.query)}
        if smuggled:
            raise RefusedError(
                f"REFUSED: URI query string carries {sorted(smuggled)} — "
                "target-deciding options belong in the URI authority/path or in "
                "the keyword/value form, never smuggled into the query string")
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


_RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(cidr)
    for cidr in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


def assert_disposable_connection(
    conn,
    expected_dbname: str,
    *,
    env: dict | None = None,
) -> None:
    """Post-connect proof, before ANY destructive statement: the session really is
    on the disposable database and on a server that cannot be remote.

    inet_server_addr() is accepted when it is NULL (unix socket) or loopback.
    A v4-mapped IPv6 address is UNWRAPPED before classification (on Python
    < 3.13 is_private reads ::ffff:8.8.8.8 as private — Suvarṇa F2). An
    RFC 1918 IPv4 address (EXACTLY 10.0.0.0/8, 172.16.0.0/12 or
    192.168.0.0/16 — not Python's wider is_private, which also admits
    link-local, ULA, 0.0.0.0 and the documentation ranges) is accepted ONLY
    inside GitHub Actions (os.environ GITHUB_ACTIONS == 'true'): CI runs
    Postgres as a service container — the runner connects to localhost:5432,
    Docker port-forwards onto the bridge network, and the server legitimately
    reports its own bridge address (e.g. 172.18.0.2/32). Everywhere else an
    RFC 1918 address is REFUSED, because on a developer machine a local
    cloud-sql-proxy listening on 127.0.0.1 and forwarding to a remote (e.g.
    production) database reports exactly that shape (steward ruling
    M20261002T174717-5721). Everything else non-loopback (public, link-local,
    ULA, unspecified, documentation ranges, v4-mapped public) is refused
    everywhere.

    NOT COVERED (documented, Suvarṇa DOC): a loopback PORT tunnelling to a
    remote server whose address still reads loopback/NULL (e.g. ssh -L), and
    PGPORT — the port never decides the target's identity the way host does,
    but a tunnel can. The DSN-level discipline (loopback host, no env
    overrides, exact dbname, post-connect dbname proof) is the mitigation;
    a full port-tunnel defence is out of scope for a string+session guard."""
    env = os.environ if env is None else env
    in_github_actions = env.get("GITHUB_ACTIONS", "") == "true"
    row = conn.execute(
        "SELECT current_database(), inet_server_addr()::text").fetchone()
    dbname, server_addr = row[0], row[1]
    if dbname != expected_dbname:
        raise RefusedError(
            f"REFUSED: connected to database {dbname!r}, not the disposable "
            f"{expected_dbname!r}")
    if server_addr is None:
        return  # unix socket — local by construction
    # inet::text carries the mask ('172.18.0.2/32'); ip_interface takes both.
    try:
        addr = ipaddress.ip_interface(server_addr).ip
    except ValueError as exc:
        raise RefusedError(
            f"REFUSED: unparseable inet_server_addr() {server_addr!r} — "
            "a server that cannot report a sane address is not trusted") from exc
    # F2: unwrap v4-mapped IPv6 BEFORE classifying, so ::ffff:8.8.8.8 is the
    # public 8.8.8.8 (and ::ffff:10.0.0.1 the private 10.0.0.1).
    addr = getattr(addr, "ipv4_mapped", None) or addr
    if addr.is_loopback:
        return
    if addr.version == 4 and any(addr in net for net in _RFC1918_NETWORKS):
        if in_github_actions:
            return
        raise RefusedError(
            f"REFUSED: the server reports a private address {server_addr!r} — "
            "a local proxy to a remote database looks exactly like this "
            "(accepted only inside GitHub Actions, where Postgres runs as a "
            "Docker service container)")
    raise RefusedError(
        f"REFUSED: the server reports a non-loopback, non-RFC1918 address "
        f"{server_addr!r} — the connection did not land where the loopback "
        "DSN claimed")
