"""C7 (steward M20261001T234151-3592) — the ka_gochara_resonance writer's
row build + insert path, exercised AS the production builder role.

Four production builds failed on 2026-10-01 on privileges the suites never
exercised because they connected as a superuser. This suite builds the
production power structure on a THROWAWAY database via the shared fixture
(tests/l3/_builder_role.py — the disposable guard refuses any other target):
schema public owned by a NOLOGIN `amjis_app` with the governed bootstrap's
default-privilege revocations in force, and a LOGIN `data_plane_builder`
holding only what the REAL checked-in grant migrations give it (1211, 1216,
1220, 1225 and Suvarṇa's 1217 — applied verbatim by the fixture, as the
owner, never re-typed).

The resonance schema is DERIVED FROM THE CHECKED-IN MIGRATIONS exactly as
tests/l3/test_resonance_rebuild_rehearsal.py derives it — via the rehearsal
module's apply_rehearsal_schema (STUB_DDL + the ontology migrations verbatim
+ the input-table DDL extracted statement-by-statement + the resonance-map
migrations 459/550/1080 verbatim), executed AS amjis_app so no object is
superuser-owned and nothing carries PUBLIC EXECUTE by default.

What it proves (§N.8 — each assertion measures the claim it names):
  1. CONTROL — the mirror is faithful: schema public is owned by amjis_app,
     the builder holds NO CREATE on it, and no ka_gochara_* function is
     executable by PUBLIC (the bootstrap's revoke really is in force).
  2. SUCCEEDS — the writer's row build (build_resonance_rows, the same pure
     builder run() feeds) plus its exact insert path (_DELETE_SQL +
     executemany(_INSERT_SQL, …)) lands as an authenticated
     data_plane_builder connection, and the rows read back.
  3. FORBIDDEN — CREATE TABLE in schema public as the builder is refused.
  4. IDEMPOTENT — the seven real grant migrations apply a second time as a
     no-op and the insert path still works.

FINDING, NOW CLOSED: until migration 1231 (PR #2906) no migration in this repo
granted data_plane_builder anything on gochara_resonance_map — yet production
carries `data_plane_builder=arwd/amjis_app` on it (verified read-only
2026-10-02: pg_class.relacl for public.gochara_resonance_map). This suite
previously mirrored that ACL out-of-band as PRODUCTION_MIRROR_GRANTS; 1231
now records the verified production ACL, so the fixture applies it as the
sixth real grant migration and the mirror is gone. Migration 1237 (Pravāha
C16) likewise records the builder's production kala_gochara_windows ACL
(C15's finding) — the fixture builds that table from the real 460 file
(below) so the seventh grant migration applies verbatim here too.

Requires a THROWAWAY database; skipped unless C7_BUILDER_ROLE_TEST_DATABASE_URL
is set:

  createdb -h 127.0.0.1 -p 55432 -U postgres c7_builder_role_test
  C7_BUILDER_ROLE_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/c7_builder_role_test \
    python -m pytest tests/l3/test_builder_role_resonance_writer.py -q
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SIDECAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SIDECAR))
sys.path.insert(0, str(SIDECAR / "scripts" / "kala_gochara_cutover"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import resonance_rebuild_disposable_rehearsal as R  # noqa: E402
import _builder_role as BR  # noqa: E402

from services.ka_gochara_resonance.writer import (  # noqa: E402
    _DELETE_SQL,
    _INSERT_SQL,
    build_resonance_rows,
)

DSN = os.environ.get("C7_BUILDER_ROLE_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not DSN, reason="NOT_RUN: set C7_BUILDER_ROLE_TEST_DATABASE_URL to the disposable Postgres")

CHART = "482012f1-710e-4a25-994a-93821f5871aa"

# The grant migrations create no objects — these are the real DDL files that
# create the objects they grant on, located by prefix under the two migration
# roots (the 1220 TS suite's DDL set, plus the four grant-target tables whose
# DDL is extracted statement-by-statement per the rehearsal's derivation).
CONTRACT_DDL_PREFIXES = ("1081", "1153", "1154", "1155", "1156", "1157")
# table -> creating migration file (relative to either migration root)
DERIVED_GRANT_TARGETS = {
    "asset_throughput_state_audit": "586_f152_asset_throughput_state_audit.sql",
    "asset_freshness": "596_nirmana_provenance_receipts.sql",
    "bg_transit_moorti": "401_bg_transit_moorti.sql",
    "bg_transit_av_gates": "397_bg_transit_av_gates.sql",
    # 1237's grant target (C16): built from the real 460 file so the grant
    # migration applies verbatim (its BIGSERIAL creates the id sequence).
    "kala_gochara_windows": "460_kala_gochara_windows.sql",
}

def _build_schema_as_owner(conn) -> dict:
    """The whole surface the seven grant migrations touch plus the resonance
    writer's schema — every object created AS amjis_app, from the real files."""
    applied: dict = {"rehearsal": None, "derived_grant_targets": {}, "contract_ddl": []}
    with BR.as_owner(conn):
        cur = conn.cursor()
        # The resonance schema, derived per test_resonance_rebuild_rehearsal.py.
        applied["rehearsal"] = R.apply_rehearsal_schema(cur)
        # Stubs the grant-target and contract DDL reference (the 1220 TS
        # suite's stubs: the FK parent and the runner's tracker table),
        # created BY the owner.
        cur.execute("CREATE TABLE public.charts (id UUID PRIMARY KEY)")
        cur.execute("CREATE TABLE public._migrations_applied (filename TEXT PRIMARY KEY)")
        # The grant-target tables whose DDL is extracted from their real
        # creating migrations (the rehearsal's derivation idiom — no hand-copy).
        for table, fname in DERIVED_GRANT_TARGETS.items():
            stmts = R.table_ddl_statements(R.find_migration(fname).read_text(), table)
            assert stmts, f"no DDL statements for {table} found in {fname}"
            for st in stmts:
                cur.execute(st)
            applied["derived_grant_targets"][table] = {"migration": fname, "statements": len(stmts)}
        # The 1153–1157 contract DDL preflights read the runner's tracker
        # table (stubbed above, as in the 1220 TS suite).
        for prefix in CONTRACT_DDL_PREFIXES:
            path = BR._find_migration(prefix)
            cur.execute(path.read_text())
            cur.execute("INSERT INTO public._migrations_applied (filename) VALUES (%s)", (path.name,))
            applied["contract_ddl"].append(path.name)
    return applied


@pytest.fixture(scope="module")
def builder_world():
    import psycopg

    BR.require_disposable(DSN)
    admin = psycopg.connect(DSN, autocommit=True, connect_timeout=5)
    try:
        BR.provision(admin)
        applied = _build_schema_as_owner(admin)
        applied["grant_migrations"] = BR.apply_grant_migrations(admin)
        yield {"admin": admin, "applied": applied}
    finally:
        # Best-effort teardown: leave the disposable database empty of this
        # suite's objects; a role another database on the cluster still
        # depends on stays (the 1220 TS suite's convention).
        try:
            admin.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
            for role in (BR.BUILDER_ROLE, BR.OWNER_ROLE):
                admin.execute(f"DROP OWNED BY {role} CASCADE")
        finally:
            admin.close()


def _resonance_rows() -> list[dict]:
    """The writer's pure row build — the same builder run() feeds — for one
    real seeded event class ('marriage' is in the 388/456 ontology seed)."""
    rows = build_resonance_rows(
        "marriage",
        houses=[7, 2],
        lords=["7L"],
        karakas=["Venus"],
        ontology_citation="c7 fixture citation",
    )
    assert rows, "the writer's row build produced no rows for 'marriage'"
    for row in rows:
        row["chart_id"] = CHART
    return rows


def test_control_mirror_is_deployment_faithful(builder_world):
    admin = builder_world["admin"]
    row = admin.execute(
        "SELECT pg_get_userbyid(nspowner) AS owner FROM pg_namespace WHERE nspname = 'public'"
    ).fetchone()
    assert row[0] == BR.OWNER_ROLE
    create_priv = admin.execute(
        "SELECT has_schema_privilege(%s, 'public', 'CREATE')", (BR.BUILDER_ROLE,)
    ).fetchone()[0]
    assert create_priv is False
    # The bootstrap's revoke is really in force: PUBLIC can execute none of the
    # ka_gochara_* contract functions the owner created (from the real 1153–1157 files).
    public_exec = admin.execute(
        "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname = 'public' AND p.proname LIKE 'ka\\_gochara\\_%' "
        "AND has_function_privilege('public', p.oid, 'EXECUTE')"
    ).fetchone()[0]
    assert public_exec == 0
    # And the fixture applied all seven real grant migrations.
    assert [Path(p).name for p in BR.grant_migration_files()] == builder_world["applied"]["grant_migrations"]


def test_resonance_writer_insert_path_succeeds_as_builder(builder_world):
    rows = _resonance_rows()
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            # The writer's exact replacement path: scoped delete, then insert.
            cur.execute(_DELETE_SQL, (CHART,))
            cur.executemany(_INSERT_SQL, rows)
        conn.commit()
        count = conn.execute(
            "SELECT count(*) FROM gochara_resonance_map WHERE chart_id = %s", (CHART,)
        ).fetchone()[0]
    assert count == len(rows)


def test_forbidden_create_table_in_public_fails_as_builder(builder_world):
    import psycopg

    with BR.connect_as_builder(DSN, connect_timeout=5) as conn, conn.cursor() as cur:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("CREATE TABLE public.c7_forbidden (id int)")
        conn.rollback()


def test_grant_migrations_idempotent(builder_world):
    admin = builder_world["admin"]
    again = BR.apply_grant_migrations(admin)
    assert again == builder_world["applied"]["grant_migrations"]
    # The insert path still works after the second application.
    rows = _resonance_rows()
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute(_DELETE_SQL, (CHART,))
            cur.executemany(_INSERT_SQL, rows)
        conn.commit()
