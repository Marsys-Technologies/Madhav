"""
Migration 1224 (chart_grants SELECT schema-of-record for data_plane_builder).

Two tiers:
  * STATIC (always runs, DB-free): file shape, exactly one GRANT, header discloses the guarded no-op.
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration file to a DISPOSABLE cluster
    this module creates with initdb in a temp dir (own port, trust auth, removed at session end). It never
    connects to anything else. Skipped, loudly, when no `initdb`/`pg_ctl` is found (looked up via $PG_BIN, PATH,
    homebrew, /usr/lib/postgresql/*/bin). Set $PG_BIN to pin a version (production is PostgreSQL 15).

What the LIVE tier proves: on a database lacking the grant it issues exactly one privilege (SELECT, one role, one
table; the ACL diff is exactly that), is a byte-identical no-op when already granted, leaves other roles' grants
alone, is idempotent, and RAISES on a missing table / missing role / a pre-existing broader privilege.
It does NOT prove production state (that is read from production structure after deploy; Trap 103).
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_M1224 = _REPO / "platform" / "migrations" / "1224_chart_grants_select_schema_of_record.sql"

# ── STATIC tier ──────────────────────────────────────────────────────────────

def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def test_migration_does_not_own_the_transaction_and_has_no_destructive_sql():
    code = _code(_M1224)
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code), "migrate.ts owns the transaction"
    assert "SET LOCAL lock_timeout = '5s';" in code
    # lock_timeout is the FIRST executable statement, and the header says why
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';"), code.strip()[:80]
    assert "a blocked migrate job must fail fast, not hang a shared deploy" in _M1224.read_text()
    # statement-start match: privilege names inside string literals (1224 lists TRUNCATE) are not statements
    assert not re.search(r"^\s*(DROP|TRUNCATE|DELETE\s+FROM|REVOKE|ALTER)\b", code, re.I | re.M)


def test_1224_header_states_guarded_noop_and_exactly_one_privilege():
    sql = _M1224.read_text()
    code = _code(_M1224)
    for needle in ("GUARDED NO-OP", "already holds", "SELECT only", "Trap 103", "FRESH-FROM-MIGRATIONS"):
        assert needle.lower() in sql.lower(), needle
    assert code.count("GRANT SELECT ON TABLE public.chart_grants TO data_plane_builder;") == 1
    assert len(re.findall(r"\bGRANT\b", code)) == 1


# ── LIVE tier: disposable PostgreSQL ─────────────────────────────────────────

def _find_pg_bin() -> Path | None:
    cands: list[Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


@pytest.fixture(scope="session")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1224pg"))
    data = root / "data"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8",
                    "--no-sync"], check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={root} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute("CREATE ROLE data_plane_builder NOLOGIN")
            c.execute("CREATE ROLE other_reader NOLOGIN")
        yield {"port": port, "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)


_db_counter = 0


@pytest.fixture()
def db(pg_cluster):
    """A fresh database per test; yields a connect() factory (autocommit off)."""
    global _db_counter
    _db_counter += 1
    name = f"t{_db_counter}"
    psycopg, port = pg_cluster["psycopg"], pg_cluster["port"]
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect():
        return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=name)

    yield connect
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


def _apply(connect, path: Path):
    """Run a migration file the way migrate.ts does: one transaction around the whole file."""
    conn = connect()
    try:
        conn.execute(path.read_text())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _exec(connect, sql: str, params=None):
    with connect() as c:
        c.execute(sql, params)


def _q(connect, sql: str, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


# ── 1224 ─────────────────────────────────────────────────────────────────────

def _relacl(connect):
    return _q(connect, "SELECT relacl::text FROM pg_class WHERE oid = 'public.chart_grants'::regclass")[0][0]


def _grants_snapshot(connect):
    return sorted(_q(connect, """
        SELECT COALESCE(r.rolname,'PUBLIC'), a.privilege_type
          FROM pg_class c CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl, acldefault('r', c.relowner))) a
          LEFT JOIN pg_roles r ON r.oid = a.grantee
         WHERE c.oid = 'public.chart_grants'::regclass"""))


def _make_chart_grants(connect, grant_other: bool = True):
    with connect() as c:
        c.execute("CREATE TABLE public.chart_grants (chart_id uuid, principal_id uuid, permission text)")
        if grant_other:
            c.execute("GRANT SELECT ON public.chart_grants TO other_reader")
        c.commit()


def _builder_privs(connect):
    return {p: _q(connect, "SELECT has_table_privilege('data_plane_builder','public.chart_grants',%s)", (p,))[0][0]
            for p in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")}


def test_1224_grants_exactly_select_to_the_builder_on_a_db_lacking_it(db):
    _make_chart_grants(db)
    before = _grants_snapshot(db)
    assert _builder_privs(db)["SELECT"] is False
    _apply(db, _M1224)
    privs = _builder_privs(db)
    assert privs == {"SELECT": True, "INSERT": False, "UPDATE": False, "DELETE": False, "TRUNCATE": False,
                     "REFERENCES": False, "TRIGGER": False}
    after = _grants_snapshot(db)
    assert sorted(set(after) - set(before)) == [("data_plane_builder", "SELECT")]
    assert not (set(before) - set(after)), "a pre-existing grant disappeared"
    # the builder can really read it, as the builder
    with db() as c:
        c.execute("SET LOCAL ROLE data_plane_builder")
        assert c.execute("SELECT count(*) FROM public.chart_grants").fetchone()[0] == 0


def test_1224_is_a_byte_identical_noop_when_already_granted(db):
    _make_chart_grants(db)
    _exec(db, "GRANT SELECT ON public.chart_grants TO data_plane_builder")
    acl = _relacl(db)
    notices: list[str] = []
    conn = db()
    conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    try:
        conn.execute(_M1224.read_text())
        conn.commit()
    finally:
        conn.close()
    assert _relacl(db) == acl
    assert any("already holds SELECT" in n and "no-op" in n for n in notices), notices


def test_1224_second_run_is_idempotent(db):
    _make_chart_grants(db)
    _apply(db, _M1224)
    acl = _relacl(db)
    _apply(db, _M1224)
    assert _relacl(db) == acl


@pytest.mark.parametrize("extra", ["INSERT", "UPDATE", "DELETE", "TRUNCATE"])
def test_1224_refuses_when_the_builder_already_holds_a_broader_privilege(db, extra):
    _make_chart_grants(db)
    _exec(db, f"GRANT {extra} ON public.chart_grants TO data_plane_builder")
    with pytest.raises(Exception) as ei:
        _apply(db, _M1224)
    assert "more than SELECT" in str(ei.value) and extra in str(ei.value), str(ei.value)


def test_1224_refuses_when_the_table_is_missing(db):
    with pytest.raises(Exception) as ei:
        _apply(db, _M1224)
    assert "chart_grants does not exist" in str(ei.value)


def test_1224_refuses_when_the_role_is_missing(db, pg_cluster):
    _make_chart_grants(db)
    psycopg, port = pg_cluster["psycopg"], pg_cluster["port"]
    admin = lambda sql: psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres",
                                        autocommit=True).execute(sql)
    admin("ALTER ROLE data_plane_builder RENAME TO dpb_parked")
    try:
        with pytest.raises(Exception) as ei:
            _apply(db, _M1224)
        assert "role data_plane_builder does not exist" in str(ei.value)
    finally:
        admin("ALTER ROLE dpb_parked RENAME TO data_plane_builder")
