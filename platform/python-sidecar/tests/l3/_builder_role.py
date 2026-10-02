"""C7 (steward M20261001T234151-3592) — SHARED deployment-faithful role fixture
for py-sidecar database tests.

WHY THIS EXISTS
═══════════════
Four production builds failed on 2026-10-01 on privileges the test suites never
exercised, because those suites connected as a superuser. Production is
different: the routine migration runner connects as `amjis_app`, which OWNS
every public-schema object, and the governed bootstrap runs

    ALTER DEFAULT PRIVILEGES FOR ROLE amjis_app REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC

(platform/scripts/nirmana-evidence-ownership-preflight.ts:259), so nothing
amjis_app creates is callable by anyone else until granted; the build pipeline
authenticates as the LOGIN role `data_plane_builder`, which holds only what the
grant migrations give it. Tests that run as a superuser mask exactly this class
of gap (the 1216 suite passed while production was broken — see the 1220 suite's
header, platform/tests/integration/gochara_contract_builder_function_execute.db.test.ts).

WHAT THIS MODULE PROVIDES
═════════════════════════
  require_disposable(dsn)   — REFUSES anything that is not a loopback DSN to a
                              database named exactly `c7_builder_role_test`
                              (the disposable-identity discipline of
                              scripts/kala_gochara_cutover/resonance_rebuild_disposable_rehearsal.py,
                              adapted to the pytest env-DSN pattern of
                              tests/l3/test_i4_i5_output_digest_specs.py).
  provision(admin_conn)     — drops schema public and rebuilds the production
                              power structure: a NOLOGIN owner role literally
                              named `amjis_app` owns schema public; a LOGIN role
                              literally named `data_plane_builder` holds only
                              USAGE on schema public; the owner bootstrap's
                              default-privilege revocations are in force.
  apply_as_owner(conn, sql) — executes SQL under SET ROLE amjis_app, the way
                              the routine runner applies migrations.
  grant_migration_files()   — the REAL checked-in grant migration files
                              (1211, 1216, 1220, 1225 and Suvarṇa's 1217),
                              located by prefix under platform/migrations;
                              raises FileNotFoundError naming the missing one
                              rather than silently skipping it.
  apply_grant_migrations(conn) — applies those files verbatim, as the owner.
  builder_dsn(admin_dsn) / connect_as_builder(admin_dsn) — a connection
                              AUTHENTICATED as data_plane_builder
                              (session_user = data_plane_builder), the real
                              build-pipeline path — not a superuser SET ROLE.

The role names are the production names, literally, so the real migration
files (which GRANT TO `data_plane_builder` and post-check
has_table_privilege('data_plane_builder', …)) apply verbatim. This is safe
ONLY because of the disposable guard: the module refuses every other database.

Never import this from a test that has not passed require_disposable().
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse, urlunparse

SIDECAR = Path(__file__).resolve().parents[2]
# The production runner's two migration roots (platform/scripts/migrate.ts:834-835).
MIGRATION_ROOTS = (SIDECAR.parent / "migrations", SIDECAR.parent / "supabase" / "migrations")

OWNER_ROLE = "amjis_app"
BUILDER_ROLE = "data_plane_builder"
BUILDER_PASSWORD = "c7_builder_role_pw"

EXPECTED_DB_NAME = "c7_builder_role_test"
LOOPBACK = {"localhost", "127.0.0.1", "::1"}

# The grant migrations the fixture applies, by numeric prefix, in order.
# 1220 = PR #2884 (pravaha/b6-1220-builder-function-execute); 1231 = PR #2906
# (pravaha/c9-resonance-map-builder-grant-record — the builder's
# gochara_resonance_map ACL, previously mirrored out-of-band); 1237 = Pravāha
# C16 (pravaha/c16-windows-builder-grant-record — the builder's
# kala_gochara_windows ACL, C15's finding); 1238 = Pravāha C18
# (pravaha/c18-windows-v2-builder-grant-record — the builder's
# kala_gochara_windows_v2 ACL, C16's flag). If any prefix
# is absent from BOTH migration roots the fixture raises — a grant the repo
# does not carry is never re-typed here.
GRANT_MIGRATION_PREFIXES = ("1211", "1216", "1217", "1220", "1225", "1231", "1237", "1238")


class RefusedError(RuntimeError):
    """The disposable-identity guard refused the connection target."""


def require_disposable(dsn: str) -> str:
    """Refuse unless `dsn` is a loopback DSN to a database named exactly
    EXPECTED_DB_NAME. Returns the database name. This fixture drops schema
    public and creates/alters cluster roles — it must never reach production."""
    parsed = urlparse(dsn)
    if (parsed.hostname or "") not in LOOPBACK:
        raise RefusedError(f"REFUSED: DSN host {parsed.hostname!r} is not loopback")
    name = (parsed.path or "").lstrip("/")
    if name != EXPECTED_DB_NAME:
        raise RefusedError(
            f"REFUSED: database {name!r} is not the disposable {EXPECTED_DB_NAME!r} — "
            "this fixture drops schema public and alters the cluster roles "
            f"{OWNER_ROLE} / {BUILDER_ROLE}")
    return name


def provision(admin_conn) -> dict:
    """Rebuild the production power structure on the disposable database.

    Roles are cluster-global: another disposable database on the same cluster
    may still depend on them, so an existing role's objects are cleared in THIS
    database only (DROP OWNED is current-database-scoped) and the role is
    created only if absent (the pattern of the 1220 TS suite's beforeAll).
    """
    cur = admin_conn.cursor()
    cur.execute("DROP SCHEMA IF EXISTS public CASCADE")
    # Role names are this module's own constants (never user input), so they
    # are inlined — psycopg's placeholder lexer rejects format()'s %I.
    cur.execute(
        "DO $d$ DECLARE r text; BEGIN "
        f"  FOREACH r IN ARRAY ARRAY['{BUILDER_ROLE}', '{OWNER_ROLE}'] LOOP "
        "    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN "
        "      EXECUTE format('DROP OWNED BY %I CASCADE', r); "
        "    ELSE "
        "      EXECUTE format('CREATE ROLE %I NOLOGIN', r); "
        "    END IF; "
        "  END LOOP; "
        "END $d$")
    cur.execute(f"CREATE SCHEMA public AUTHORIZATION {OWNER_ROLE}")
    cur.execute(f"GRANT USAGE ON SCHEMA public TO {BUILDER_ROLE}")
    # The builder is a real LOGIN role so tests authenticate AS it.
    cur.execute(f"ALTER ROLE {BUILDER_ROLE} LOGIN PASSWORD '{BUILDER_PASSWORD}'")
    # The governed bootstrap (nirmana-evidence-ownership-preflight.ts:259-260):
    # pg_default_acl omits PostgreSQL's built-in PUBLIC EXECUTE (functions) and
    # PUBLIC USAGE (types) defaults, so they are revoked unconditionally there —
    # and here.
    cur.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE {OWNER_ROLE} REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC")
    cur.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE {OWNER_ROLE} REVOKE USAGE ON TYPES FROM PUBLIC")
    return {"owner": OWNER_ROLE, "builder": BUILDER_ROLE, "schema": "public"}


@contextmanager
def as_owner(conn):
    """Run statements under SET ROLE amjis_app — the routine migration runner's
    identity (platform/scripts/validate-migration-database-routes.ts:12)."""
    conn.execute(f"SET ROLE {OWNER_ROLE}")
    try:
        yield conn
    finally:
        conn.execute("RESET ROLE")


def apply_as_owner(conn, sql: str) -> None:
    with as_owner(conn):
        conn.execute(sql)


def _find_migration(prefix_or_name: str) -> Path:
    for root in MIGRATION_ROOTS:
        if prefix_or_name.endswith(".sql"):
            p = root / prefix_or_name
            if p.is_file():
                return p
        else:
            matches = sorted(root.glob(f"{prefix_or_name}_*.sql"))
            if matches:
                if len(matches) > 1:
                    raise RefusedError(f"ambiguous migration prefix {prefix_or_name!r}: {matches}")
                return matches[0]
    raise FileNotFoundError(
        f"migration {prefix_or_name!r} not found under {MIGRATION_ROOTS} — "
        "the fixture applies the REAL checked-in files only; it never re-types a grant")


def grant_migration_files() -> list[Path]:
    return [_find_migration(prefix) for prefix in GRANT_MIGRATION_PREFIXES]


def apply_grant_migrations(conn) -> list[str]:
    """Apply the real grant migration files verbatim, as the owner. Returns the
    file names applied. Idempotent: GRANT of an already-held privilege is a
    no-op in PostgreSQL (and 1217's post-conditions are privilege checks)."""
    applied = []
    for path in grant_migration_files():
        apply_as_owner(conn, path.read_text())
        applied.append(path.name)
    return applied


def builder_dsn(admin_dsn: str) -> str:
    parsed = urlparse(admin_dsn)
    return urlunparse(parsed._replace(
        netloc=f"{BUILDER_ROLE}:{BUILDER_PASSWORD}@{parsed.hostname}:{parsed.port}"))


def connect_as_builder(admin_dsn: str, **kwargs):
    """A connection AUTHENTICATED as data_plane_builder — the build pipeline's
    real path. session_user is data_plane_builder, which the session_user-gated
    contract functions (e.g. migration 1035's) distinguish from SET ROLE."""
    import psycopg
    return psycopg.connect(builder_dsn(admin_dsn), **kwargs)
