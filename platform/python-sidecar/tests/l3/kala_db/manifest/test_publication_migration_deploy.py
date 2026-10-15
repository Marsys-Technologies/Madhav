"""K9-23 verifier grants must defer alongside their protected prerequisite."""
from pathlib import Path

import psycopg
import pytest


PLATFORM = Path(__file__).resolve().parents[5]
PREREQUISITE = "1330_kala_layer_manifest_candidates.sql"
GRANTS = "1386_kala_layer_operation_verifier_reads.sql"


@pytest.fixture
def deployment_db(isolated_kala_db_dsn):
    with psycopg.connect(isolated_kala_db_dsn) as conn:
        try:
            if not conn.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'verifier_principal')"
            ).fetchone()[0]:
                conn.execute("CREATE ROLE verifier_principal NOLOGIN")
            yield conn
        finally:
            conn.rollback()


def test_routine_deploy_can_leave_protected_predecessors_pending(deployment_db):
    # Reproduce migrate.ts's routine policy: skip listed pending files, then
    # execute later unlisted SQL. Omitting GRANTS from the real list must fail
    # against PostgreSQL's absent relation, as a routine deploy would.
    protected = {
        name
        for line in (PLATFORM / "scripts/kala_protected_migrations.txt").read_text().splitlines()
        if (name := line.split("#", 1)[0].strip())
    }
    assert PREREQUISITE in protected
    assert deployment_db.execute(
        "SELECT to_regclass('public.kala_layer_candidate')"
    ).fetchone()[0] is None

    applied = []
    pending = [
        (PREREQUISITE, (PLATFORM / "migrations" / PREREQUISITE).read_text()),
        (GRANTS, (PLATFORM / "migrations" / GRANTS).read_text()),
        ("later_routine_probe.sql", "CREATE TABLE k923_routine_probe (id integer)"),
    ]
    for name, sql in pending:
        if name not in protected:
            deployment_db.execute(sql)
            applied.append(name)

    assert applied == ["later_routine_probe.sql"]
    assert deployment_db.execute(
        "SELECT to_regclass('public.kala_layer_candidate'), to_regclass('k923_routine_probe')"
    ).fetchone() == (None, "k923_routine_probe")


def test_verifier_grants_reapply_after_protected_prerequisites(deployment_db):
    deployment_db.execute((PLATFORM / "migrations" / PREREQUISITE).read_text())
    deployment_db.execute("""CREATE TABLE build_runs (
        id uuid, chart_id uuid, scope text, scope_target text, action text,
        plan jsonb, state text, plan_manifest jsonb, plan_manifest_digest text)""")
    migration = (PLATFORM / "migrations" / GRANTS).read_text()
    deployment_db.execute(migration)
    deployment_db.execute(migration)
    for table, column in [("kala_layer_candidate", "conventions"), ("build_runs", "plan_manifest_digest")]:
        assert deployment_db.execute(
            "SELECT has_column_privilege('verifier_principal', %s, %s, 'SELECT')",
            (table, column),
        ).fetchone()[0] is True
