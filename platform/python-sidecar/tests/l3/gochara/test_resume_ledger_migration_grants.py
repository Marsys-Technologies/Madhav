"""SR-RESUME-INTEGRATION: migration 1410 grants SELECT on the committed-substep ledger to `amjis_app`, explicitly, and its post-apply block raises without it.

The century resume readback (the executor's accepted ledger readback) runs as the app role. The ruling: "Do NOT rely on ownership ... the privilege is a stated fact." So
the migration states it in the same existence-guarded pattern as its other grants, and the post-apply block (the migration's own detector) raises unless the role, when it
exists, holds SELECT — a table the app role merely happens to own would read green on a privilege check only if the grant were absent AND the check were ownership-based.

CLAIMS, each with its own fail-on-revert oracle (the planted reversion is named in the docstring):
  A. applied with the role present, `has_table_privilege('amjis_app', ledger, 'SELECT')` is true (and the role holds no write privilege)
  B. with the grant statement reverted the post-apply block RAISES, naming amjis_app

Runs on the guarded local disposable cluster (GOCHARA_A53_ADMIN_DSN; NOT_RUN skip when unreachable, a FAILURE under GOCHARA_A53_REQUIRE_DB=1) in a throwaway database; the
cluster-wide roles are created only if absent and dropped again only if this test created them.
"""
from __future__ import annotations

import os
import uuid

import pytest

from ._disposable_db_guard import UnsafeAdminDSN, guarded_admin_connect
from .test_a53_record_store import ADMIN_DSN, DB_PREFIX, MIGRATIONS

MIGRATION = MIGRATIONS / "1410_ka_gochara_build_ledger.sql"
ROLES = ("data_plane_builder", "gochara_verifier", "gochara_sealer", "amjis_app")
GRANT = "GRANT SELECT ON public.ka_gochara_build_ledger TO amjis_app;"
LEDGER = "public.ka_gochara_build_ledger"


@pytest.fixture()
def database():
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    try:
        admin = guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except UnsafeAdminDSN:
        raise
    except Exception as exc:  # noqa: BLE001
        if os.environ.get("GOCHARA_A53_REQUIRE_DB") == "1":
            pytest.fail(f"GOCHARA_A53_REQUIRE_DB=1 but the disposable database server is unreachable ({exc})")
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    created = [r for r in ROLES if admin.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (r,)).fetchone() is None]
    for role in created:
        admin.execute(f'CREATE ROLE "{role}" NOLOGIN')
    name = f"{DB_PREFIX}grants_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    conn = psycopg.connect(make_conninfo(ADMIN_DSN, dbname=name), autocommit=True, connect_timeout=3)
    try:
        # the migration's two prerequisites, as bare tables (the grants do not depend on anything else of the chain)
        conn.execute("CREATE TABLE public.charts (id uuid PRIMARY KEY)")
        conn.execute("CREATE TABLE public.kala_gochara_publication (chart_id uuid, generation text)")
        yield conn
    finally:
        conn.close()
        assert name.startswith(DB_PREFIX), name                       # never drop what we did not create
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        for role in created:                                          # only what this test created (privileges lived in the dropped database)
            admin.execute(f'DROP ROLE IF EXISTS "{role}"')
        admin.close()


def _apply(conn, text):
    with conn.transaction():                                          # the migration runner owns the transaction (SET LOCAL lock_timeout)
        conn.execute(text)


def test_the_applied_migration_grants_select_to_the_app_role_and_no_write_privilege(database):
    """Revert: remove the amjis_app GRANT (and its check) from 1410 => `has_table_privilege` reads false and this assertion fails."""
    _apply(database, MIGRATION.read_text())
    assert database.execute("SELECT has_table_privilege('amjis_app', %s, 'SELECT')", (LEDGER,)).fetchone()[0] is True
    assert database.execute("SELECT has_table_privilege('amjis_app', %s, 'INSERT') OR has_table_privilege('amjis_app', %s, 'UPDATE')"
                            " OR has_table_privilege('amjis_app', %s, 'DELETE')", (LEDGER,) * 3).fetchone()[0] is False, "the app role reads the ledger only"
    assert database.execute("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = %s::regclass", (LEDGER,)).fetchone()[0] != "amjis_app", \
        "the privilege is stated, not inherited from ownership"


def test_with_the_app_grant_reverted_the_post_apply_block_raises_naming_the_role(database):
    """The migration's own detector: the grant is planted away (the one statement replaced by a no-op) and the post-apply block must RAISE, not pass.
    Revert: drop the amjis_app clause from the post-apply block => the migration applies cleanly without the grant and this test fails."""
    assert GRANT in MIGRATION.read_text(), "the migration no longer states the grant in the form this oracle reverts"
    reverted = MIGRATION.read_text().replace(GRANT, "NULL;")
    with pytest.raises(Exception, match="amjis_app cannot read the ledger"):
        _apply(database, reverted)
    assert database.execute("SELECT to_regclass(%s)", (LEDGER,)).fetchone()[0] is None, "a refused migration left the table behind (its transaction must roll back)"
