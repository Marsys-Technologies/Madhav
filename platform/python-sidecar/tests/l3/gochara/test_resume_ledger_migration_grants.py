"""SR-RESUME-INTEGRATION / SR-3916-NB-FIX-AMEND-1: migration 1410's post-apply block MEASURES and NAMES how `amjis_app` reads the committed-substep ledger.

The century resume readback runs as the app role, and the deploy runner connects as that role, so in production it OWNS what 1410 creates. The ruling (amended): the read
is a stated fact in exactly one of two admitted forms, each measured and named by the migration -- `owner` (pg_class.relowner is amjis_app) or `grant` (an explicit ACL
SELECT entry for amjis_app made by a different role); anything else raises. The three non-owner roles count only by explicit ACL grants (grantor <> grantee), never by
has_table_privilege, which ownership would satisfy.

CLAIMS, each with its own fail-on-revert oracle (the planted reversion is named in the docstring):
  A. applied by another owner with the role present, amjis_app reads by `grant` (an ACL entry from a different grantor) and holds no write privilege
  B. applied by another owner with the grant statement reverted, the post-apply block RAISES, naming amjis_app and the owner
  C. applied by amjis_app itself (the production deploy identity), the post-apply block passes and names the `owner` form
  D. with the builder's grant reverted, the post-apply block RAISES naming data_plane_builder (its privilege counts only from the ACL)
  E. applied by the builder ITSELF (an owner) without its grant, the post-apply block RAISES: ownership never satisfies a non-owner role's grant
  F. a SELECT that reaches amjis_app only through PUBLIC is not the `grant` form: the post-apply block RAISES
  G. an owner that revoked its own SELECT is refused: the `owner` form requires relowner = amjis_app AND has_table_privilege SELECT, and names both
  H. each read-only role (gochara_verifier, gochara_sealer) is in the post-apply ACL loop: its grant reverted => RAISE naming it

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


BUILDER_GRANT = "GRANT SELECT, INSERT, UPDATE, DELETE ON public.ka_gochara_build_ledger TO data_plane_builder;"


def _notices(conn):
    seen = []
    conn.add_notice_handler(lambda d: seen.append(d.message_primary or ""))
    return seen


def test_another_owner_applies_and_the_app_role_reads_by_an_explicit_grant_with_no_write_privilege(database):
    """Revert: remove the amjis_app GRANT and the post-apply `grant` branch from 1410 => no ACL entry for amjis_app exists and the first assertion fails."""
    seen = _notices(database)
    _apply(database, MIGRATION.read_text())
    assert database.execute("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = %s::regclass", (LEDGER,)).fetchone()[0] != "amjis_app"
    assert database.execute("SELECT count(*) FROM pg_class c, LATERAL aclexplode(c.relacl) a WHERE c.oid = %s::regclass AND a.grantee = 'amjis_app'::regrole::oid"
                            " AND a.privilege_type = 'SELECT' AND a.grantor <> a.grantee", (LEDGER,)).fetchone()[0] == 1, "an explicit ACL grant from another role"
    assert database.execute("SELECT has_table_privilege('amjis_app', %s, 'INSERT') OR has_table_privilege('amjis_app', %s, 'UPDATE')"
                            " OR has_table_privilege('amjis_app', %s, 'DELETE')", (LEDGER,) * 3).fetchone()[0] is False, "the app role reads the ledger only"
    assert any("amjis_app reads the ledger as grant" in m for m in seen), seen


def test_with_the_app_grant_reverted_the_post_apply_block_raises_naming_the_role_and_the_owner(database):
    """The migration's own detector: the grant is planted away (the one statement replaced by a no-op) and the post-apply block must RAISE, not pass.
    Revert: drop the amjis_app clause from the post-apply block => the migration applies cleanly without the grant and this test fails."""
    assert GRANT in MIGRATION.read_text(), "the migration no longer states the grant in the form this oracle reverts"
    reverted = MIGRATION.read_text().replace(GRANT, "NULL;")
    with pytest.raises(Exception, match="amjis_app can read the ledger in neither admitted form .*the owner is "):
        _apply(database, reverted)
    assert database.execute("SELECT to_regclass(%s)", (LEDGER,)).fetchone()[0] is None, "a refused migration left the table behind (its transaction must roll back)"


def test_applied_by_the_app_role_itself_the_owner_form_is_measured_and_named(database):
    """The production deploy identity: the runner connects as amjis_app, which then owns the ledger. The post-apply block must PASS and name the `owner` form.
    Revert: delete the `owner` branch (IF owner_name = 'amjis_app' ...) => the self-grant has grantor = grantee, neither form holds, and the apply raises."""
    database.execute("GRANT CREATE, USAGE ON SCHEMA public TO amjis_app")
    database.execute("GRANT REFERENCES, SELECT ON public.charts, public.kala_gochara_publication TO amjis_app")
    seen = _notices(database)
    with database.transaction():
        database.execute("SET LOCAL ROLE amjis_app")
        database.execute(MIGRATION.read_text())
    assert database.execute("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = %s::regclass", (LEDGER,)).fetchone()[0] == "amjis_app"
    assert any("amjis_app reads the ledger as owner" in m for m in seen), seen


def test_applied_by_the_builder_itself_without_its_grant_the_post_apply_block_raises(database):
    """A non-owner role's privilege must come from an explicit ACL entry, never from ownership. Here the builder OWNS the ledger and its GRANT is planted away:
    has_table_privilege would read true (an owner holds every privilege), the ACL has no grantor <> grantee entry for it, so the apply must RAISE.
    Revert: put has_table_privilege back in the three-role loop, or drop `grantor <> grantee` => the owner's own privileges count and the apply passes."""
    database.execute("GRANT CREATE, USAGE ON SCHEMA public TO data_plane_builder")
    database.execute("GRANT REFERENCES, SELECT ON public.charts, public.kala_gochara_publication TO data_plane_builder")
    assert BUILDER_GRANT in MIGRATION.read_text()
    with pytest.raises(Exception, match="data_plane_builder has no explicit ACL grant of SELECT"):
        with database.transaction():
            database.execute("SET LOCAL ROLE data_plane_builder")
            database.execute(MIGRATION.read_text().replace(BUILDER_GRANT, "NULL;"))


def test_an_owner_that_revoked_its_own_select_is_refused(database):
    """The owner form needs BOTH facts: relowner = amjis_app AND has_table_privilege SELECT. An owner can revoke its own SELECT; relowner then still says it owns
    while the read is denied. Planted: applied AS amjis_app with its GRANT replaced by REVOKE SELECT ... FROM amjis_app => the post-apply block must RAISE.
    Revert: test only relowner in the owner branch => the owner form passes over a denied read and this test fails."""
    database.execute("GRANT CREATE, USAGE ON SCHEMA public TO amjis_app")
    database.execute("GRANT REFERENCES, SELECT ON public.charts, public.kala_gochara_publication TO amjis_app")
    assert GRANT in MIGRATION.read_text()
    revoked = MIGRATION.read_text().replace(GRANT, "REVOKE SELECT ON public.ka_gochara_build_ledger FROM amjis_app;")
    with pytest.raises(Exception, match="amjis_app OWNS the ledger but cannot read it"):
        with database.transaction():
            database.execute("SET LOCAL ROLE amjis_app")
            database.execute(revoked)


def test_a_public_read_grant_is_not_the_app_roles_explicit_grant(database):
    """The `grant` form is an ACL entry naming amjis_app itself. A read that reaches amjis_app only through PUBLIC must not count.
    Revert: test the grant branch with has_table_privilege => PUBLIC SELECT satisfies it and the apply passes."""
    assert GRANT in MIGRATION.read_text()
    with pytest.raises(Exception, match="amjis_app can read the ledger in neither admitted form"):
        _apply(database, MIGRATION.read_text().replace(GRANT, "GRANT SELECT ON public.ka_gochara_build_ledger TO PUBLIC;"))


@pytest.mark.parametrize("role", ["gochara_verifier", "gochara_sealer"])
def test_with_a_reader_grant_reverted_the_post_apply_block_raises_naming_that_reader(database, role):
    """Each read-only role is in the post-apply ACL loop. Planted: its GRANT replaced by a no-op => the apply must RAISE naming it.
    Revert: drop the role from the three-role loop => the migration applies cleanly without its grant and this test fails."""
    grant = f"GRANT SELECT ON public.ka_gochara_build_ledger TO {role};"
    assert grant in MIGRATION.read_text(), f"the migration no longer states the {role} grant in the form this oracle reverts"
    with pytest.raises(Exception, match=f"{role} has no explicit ACL grant of SELECT"):
        _apply(database, MIGRATION.read_text().replace(grant, "NULL;"))


def test_with_the_builder_grant_reverted_the_post_apply_block_raises_naming_the_builder(database):
    """The builder's privileges count only from an explicit ACL entry. Revert: check the builder with has_table_privilege again (or drop it from the ACL loop) =>
    with its grant planted away the migration still applies only if ownership/another path satisfied it; here no path does and the RAISE must name the role."""
    assert BUILDER_GRANT in MIGRATION.read_text(), "the migration no longer states the builder grant in the form this oracle reverts"
    with pytest.raises(Exception, match="data_plane_builder has no explicit ACL grant of SELECT"):
        _apply(database, MIGRATION.read_text().replace(BUILDER_GRANT, "NULL;"))
