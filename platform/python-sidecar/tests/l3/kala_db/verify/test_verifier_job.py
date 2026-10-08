"""Database boundary oracle for the separately dispatched Kāla verifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

import psycopg
from psycopg.conninfo import make_conninfo


def _digest(input_vector: str) -> str:
    return hashlib.sha256(
        json.dumps([("grain", input_vector)], separators=(",", ":")).encode()
    ).hexdigest()


def test_manifest_migration_grants_only_verifier_reads_and_receipt_writes():
    """The isolated verifier can read inputs and write its own receipt."""
    migrations = Path(__file__).resolve().parents[5] / "migrations"
    migration = "\n".join(
        (migrations / filename).read_text()
        for filename in (
            "1330_kala_layer_manifest_candidates.sql",
            "1333_kala_layer_verifier_conflict_read_grant.sql",
        )
    )

    assert re.search(
        r"GRANT\s+USAGE\s+ON\s+SCHEMA\s+public\s+TO\s+verifier_principal",
        migration,
        re.IGNORECASE,
    )
    assert re.search(
        r"GRANT\s+SELECT\s+ON\s+TABLE\s+public\.kala_layer_candidate_grain\s+TO\s+verifier_principal",
        migration,
        re.IGNORECASE,
    )
    assert re.search(
        r"GRANT\s+INSERT\s+ON\s+TABLE\s+public\.kala_layer_verification\s+TO\s+verifier_principal",
        migration,
        re.IGNORECASE,
    )
    assert re.search(
        r"GRANT\s+SELECT\s*\(\s*chart_id\s*,\s*generation\s*\)\s*"
        r"ON\s+TABLE\s+public\.kala_layer_verification\s+TO\s+verifier_principal",
        migration,
        re.IGNORECASE,
    )


def test_verifier_job_runs_in_a_separate_process_as_verifier_principal(kala_db_dsn):
    """Removing the verifier role boundary must stop the child before it writes."""
    chart_id = uuid.uuid4()
    generation = "candidate"
    build_id = uuid.uuid4()
    role_created = False
    with psycopg.connect(kala_db_dsn, autocommit=True) as conn:
        role_exists = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'verifier_principal')"
        ).fetchone()[0]
        if not role_exists:
            conn.execute("CREATE ROLE verifier_principal NOLOGIN")
            role_created = True
        conn.execute(
            "CREATE TABLE kala_layer_candidate_grain ("
            "chart_id uuid NOT NULL, generation text NOT NULL, grain_key text NOT NULL, "
            "input_vector text NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE kala_layer_verification ("
            "chart_id uuid NOT NULL, generation text NOT NULL, verifier_principal text NOT NULL, "
            "result text NOT NULL, detail jsonb NOT NULL, "
            "PRIMARY KEY (chart_id, generation))"
        )
        conn.execute("GRANT USAGE ON SCHEMA public TO verifier_principal")
        conn.execute("GRANT SELECT ON kala_layer_candidate_grain TO verifier_principal")
        conn.execute("GRANT INSERT ON kala_layer_verification TO verifier_principal")
        conn.execute(
            "GRANT SELECT (chart_id, generation) "
            "ON kala_layer_verification TO verifier_principal"
        )
        assert conn.execute(
            "SELECT has_table_privilege('verifier_principal', 'kala_layer_verification', 'INSERT'), "
            "has_column_privilege('verifier_principal', 'kala_layer_verification', 'chart_id', 'SELECT'), "
            "has_column_privilege('verifier_principal', 'kala_layer_verification', 'generation', 'SELECT')"
        ).fetchone() == (True, True, True)
        conn.execute(
            "INSERT INTO kala_layer_candidate_grain "
            "(chart_id, generation, grain_key, input_vector) VALUES (%s, %s, 'grain', 'stored')",
            (chart_id, generation),
        )
        verifier_dsn = make_conninfo(kala_db_dsn, options="-c role=verifier_principal")
        sidecar_root = Path(__file__).resolve().parents[4]
        child_env = {"KALA_VERIFIER_DSN": verifier_dsn, "PYTHONPATH": str(sidecar_root)}
        privilege_probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import os, psycopg; "
                    "conn = psycopg.connect(os.environ['KALA_VERIFIER_DSN']); "
                    "print(conn.execute(\"SELECT current_user, session_user, "
                    "has_table_privilege(current_user, 'kala_layer_verification', 'INSERT'), "
                    "has_column_privilege(current_user, 'kala_layer_verification', 'chart_id', 'SELECT'), "
                    "has_column_privilege(current_user, 'kala_layer_verification', 'generation', 'SELECT')\").fetchone())"
                ),
            ],
            env=child_env,
            capture_output=True,
            text=True,
        )
        assert privilege_probe.returncode == 0, privilege_probe.stderr
        assert privilege_probe.stdout.strip() == "('verifier_principal', 'postgres', True, True, True)"
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "services.kala_core.verify.job",
                "--chart-id",
                str(chart_id),
                "--generation",
                generation,
                "--build-id",
                str(build_id),
                "--independently-derived-digest",
                _digest("stored"),
            ],
            cwd=sidecar_root,
            env=child_env,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
        assert conn.execute(
            "SELECT verifier_principal, result, detail->>'input_digest' "
            "FROM kala_layer_verification"
        ).fetchall() == [("verifier_principal", "accepted", _digest("stored"))]
        if role_created:
            conn.execute("REVOKE ALL PRIVILEGES ON kala_layer_candidate_grain FROM verifier_principal")
            conn.execute("REVOKE ALL PRIVILEGES ON kala_layer_verification FROM verifier_principal")
            conn.execute("REVOKE ALL PRIVILEGES ON SCHEMA public FROM verifier_principal")
            conn.execute("DROP ROLE verifier_principal")
