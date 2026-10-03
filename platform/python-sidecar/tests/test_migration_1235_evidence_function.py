"""Pravāha B (steward M20261003T131532-b179) — protected-class migration 1235 (the staged-candidate evidence function) against a REAL PostgreSQL.

The ordinary migration role has USAGE without CREATE on public; this file is applied only in the protected window, which grants amjis_app a bounded
CREATE capability and revokes it. The fixture mirrors that: CREATE is granted to amjis_app for the apply and revoked after; the routine path is shown
to REFUSE it (permission denied). Needs GOCHARA_A51_TEST_DATABASE_URL (a disposable server; the test creates and drops its own database)."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

PG = os.environ.get("GOCHARA_A51_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not PG, reason="needs GOCHARA_A51_TEST_DATABASE_URL (a disposable PostgreSQL server)")

MIGRATION = Path(__file__).resolve().parents[2] / "migrations" / "1235_ka_gochara_staged_candidate_evidence_function.sql"
V41, V5 = "ka_gochara_v4_41_candidate", "ka_gochara_v5"
FN = "public.ka_gochara_staged_candidate_has_runtime_evidence"
LOADER_ROLES = ("amjis_app", "nirmana_campaign_control_writer", "nirmana_evidence_ingress_writer")


@pytest.fixture(scope="module")
def dsn():
    import psycopg
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    base = conninfo_to_dict(PG)
    admin = psycopg.connect(make_conninfo(**{**base, "dbname": "postgres"}), autocommit=True)
    name = f"fn1235_{uuid.uuid4().hex[:10]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    try:
        yield make_conninfo(**{**base, "dbname": name})
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


@pytest.fixture()
def conn(dsn):
    import psycopg
    c = psycopg.connect(dsn, autocommit=True)
    c.execute(f"DROP FUNCTION IF EXISTS {FN}(text); DROP TABLE IF EXISTS asset_provenance_receipts, build_run_assets, asset_throughput CASCADE")
    for role in (*LOADER_ROLES, "outsider_role"):
        c.execute(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN CREATE ROLE {role} NOLOGIN; END IF; END $$")
    c.execute("REVOKE CREATE ON SCHEMA public FROM amjis_app; GRANT USAGE ON SCHEMA public TO amjis_app")        # production: USAGE without CREATE
    c.execute("CREATE TABLE asset_provenance_receipts (asset_id text); CREATE TABLE build_run_assets (asset_id text); CREATE TABLE asset_throughput (asset_id text)")
    for tbl in ("asset_provenance_receipts", "build_run_assets", "asset_throughput"):
        c.execute(f"ALTER TABLE {tbl} OWNER TO amjis_app")
    yield c
    c.close()


def _apply(c, window=True):
    """Apply as amjis_app; `window=True` mirrors the protected window (a bounded CREATE grant, revoked after, even on failure)."""
    if window:
        c.execute("GRANT CREATE ON SCHEMA public TO amjis_app")
    try:
        with c.transaction():
            c.execute("SET LOCAL ROLE amjis_app")
            c.execute(MIGRATION.read_text(encoding="utf-8"))
    finally:
        if window:
            c.execute("REVOKE CREATE ON SCHEMA public FROM amjis_app")


def test_a_the_routine_path_REFUSES_it_(conn):
    import psycopg
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _apply(conn, window=False)                                                    # USAGE without CREATE on public: why it is protected-class
    assert conn.execute(f"SELECT to_regprocedure('{FN}(text)')").fetchone()[0] is None


def test_b_the_window_applies_it_and_the_function_answers_for_receipts_build_runs_and_throughput(conn):
    import psycopg
    _apply(conn)
    ev = lambda i: conn.execute(f"SELECT {FN}(%s)", (i,)).fetchone()[0]
    assert ev(V5) is False and ev(V41) is False
    conn.execute("INSERT INTO asset_throughput VALUES (%s)", (V5,))                   # a cockpit refresh row
    assert ev(V5) is True and ev(V41) is False
    conn.execute("INSERT INTO build_run_assets VALUES (%s)", (V41,))
    conn.execute("INSERT INTO asset_throughput VALUES (%s)", (V41,))
    conn.execute("DELETE FROM build_run_assets WHERE asset_id = %s", (V41,))          # the watchdog PRUNES build_run_assets: the throughput row remains
    assert ev(V41) is True
    conn.execute("DELETE FROM asset_throughput WHERE asset_id = ANY(%s)", ([V41, V5],))
    conn.execute("INSERT INTO asset_provenance_receipts VALUES (%s)", (V5,))
    assert ev(V5) is True
    for bad in ("bg_texts", "ka_gochara", "KA_GOCHARA_V5", ""):
        with pytest.raises(psycopg.errors.InvalidParameterValue):
            ev(bad)
    with pytest.raises(psycopg.errors.InvalidParameterValue):
        conn.execute(f"SELECT {FN}(NULL)")


def test_c_owner_security_definer_search_path_and_an_ACL_with_exactly_the_three_roles_no_PUBLIC_no_grant_option(conn):
    _apply(conn)
    owner, secdef, config, vol, ret = conn.execute(
        "SELECT pg_get_userbyid(proowner), prosecdef, proconfig, provolatile, prorettype::regtype::text FROM pg_proc WHERE oid = %s::regprocedure", (FN + "(text)",)).fetchone()
    assert (owner, secdef, config, vol, ret) == ("amjis_app", True, ["search_path=pg_catalog, pg_temp"], "s", "boolean")
    rows = conn.execute("SELECT CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END, a.privilege_type, a.is_grantable "
                        "FROM pg_proc p, LATERAL aclexplode(p.proacl) a WHERE p.oid = %s::regprocedure ORDER BY 1", (FN + "(text)",)).fetchall()
    assert rows == [("amjis_app", "EXECUTE", False), ("nirmana_campaign_control_writer", "EXECUTE", False), ("nirmana_evidence_ingress_writer", "EXECUTE", False)]
    assert conn.execute("SELECT has_function_privilege('outsider_role', %s, 'EXECUTE')", (FN + "(text)",)).fetchone()[0] is False


def test_d_all_three_loader_roles_run_it_with_NO_select_on_the_evidence_tables_and_an_outsider_is_denied_loudly(conn):
    import psycopg
    _apply(conn)
    conn.execute("INSERT INTO asset_throughput VALUES (%s)", (V5,))
    for role in LOADER_ROLES[1:]:
        for tbl in ("asset_provenance_receipts", "build_run_assets", "asset_throughput"):
            assert conn.execute("SELECT has_table_privilege(%s, %s, 'SELECT')", (role, f"public.{tbl}")).fetchone()[0] is False
    for role in LOADER_ROLES:
        with conn.transaction():
            conn.execute(f"SET LOCAL ROLE {role}")
            assert conn.execute(f"SELECT {FN}(%s), {FN}(%s)", (V5, V41)).fetchone() == (True, False)    # IDENTICAL for the three roles (throughput-only ⇒ evidence)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with conn.transaction():
            conn.execute("SET LOCAL ROLE outsider_role")
            conn.execute(f"SELECT {FN}(%s)", (V5,))


def test_e_a_PRE_EXISTING_grant_option_is_rejected_and_the_migration_rolls_back_whole(conn):
    """CREATE OR REPLACE preserves an existing ACL: a function that already carries `WITH GRANT OPTION` for a non-owner must fail the post-check (P3)."""
    import psycopg
    conn.execute("GRANT CREATE ON SCHEMA public TO amjis_app")
    with conn.transaction():
        conn.execute("SET LOCAL ROLE amjis_app")
        conn.execute(f"CREATE FUNCTION {FN}(p_asset_id text) RETURNS boolean LANGUAGE sql AS $$ SELECT false $$")
        conn.execute(f"GRANT EXECUTE ON FUNCTION {FN}(text) TO nirmana_campaign_control_writer WITH GRANT OPTION")
    conn.execute("REVOKE CREATE ON SCHEMA public FROM amjis_app")
    with pytest.raises(psycopg.errors.RaiseException, match="1235: the evidence function ACL has 1 unexpected"):
        _apply(conn)
    # whole rollback: the stub body is still the stub (the CREATE OR REPLACE did not stick)
    assert "SELECT false" in conn.execute("SELECT prosrc FROM pg_proc WHERE oid = %s::regprocedure", (FN + "(text)",)).fetchone()[0]
    # a PUBLIC grant is rejected the same way
    conn.execute(f"REVOKE ALL ON FUNCTION {FN}(text) FROM nirmana_campaign_control_writer; GRANT EXECUTE ON FUNCTION {FN}(text) TO PUBLIC")
    conn.execute("ALTER FUNCTION %s(text) OWNER TO amjis_app" % FN)
    # (the migration's own REVOKE ALL FROM PUBLIC then removes it; the post-check passes)
    _apply(conn)
    assert conn.execute("SELECT count(*) FROM pg_proc p, LATERAL aclexplode(p.proacl) a WHERE p.oid = %s::regprocedure AND a.grantee = 0", (FN + "(text)",)).fetchone()[0] == 0
