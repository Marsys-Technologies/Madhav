"""Readback suites: reuse a guarded local cluster when KALA_ADMIN_DSN is set.

The fixture owns only a unique database, never the server. CI retains the
existing disposable-server fixture when no admin DSN is supplied.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import uuid

import pytest

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def disposable_pg():
    dsn = os.environ.get("KALA_ADMIN_DSN")
    if not dsn:
        from _disposable_pg import get_cluster, shutdown
        cluster = get_cluster()
        try:
            yield cluster
        finally:
            shutdown()
        return

    import psycopg
    guard_path = REPO / "platform/python-sidecar/tests/l3/_disposable_db_guard.py"
    spec = importlib.util.spec_from_file_location("j4b_db_guard", guard_path)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    info = guard.validate_disposable_dsn(dsn, "postgres")
    if (info.get("host"), info.get("port")) != ("127.0.0.1", "55433"):
        pytest.fail("J4B local readbacks require 127.0.0.1:55433/postgres")
    name = "j4b_ci_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True, connect_timeout=3) as admin:
        guard.assert_disposable_connection(admin, "postgres")
        existing = {r[0] for r in admin.execute("SELECT rolname FROM pg_roles")}
        admin.execute(psycopg.sql.SQL("CREATE DATABASE {}").format(psycopg.sql.Identifier(name)))
        try:
            class Database:
                user = info.get("user", "postgres")
                dbname = name
                bin_dir = Path(shutil.which("psql")).parent

                def env(self):
                    return {"PGHOST": "127.0.0.1", "PGPORT": "55433", "PGUSER": self.user,
                            "PGDATABASE": name, "PGCONNECT_TIMEOUT": "3"}

                def psql(self, sql):
                    env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
                    env.update(self.env())
                    proc = subprocess.run([str(self.bin_dir / "psql"), "-XqtA", "-v", "ON_ERROR_STOP=1", "-c", sql],
                                          env=env, capture_output=True, text=True, timeout=60)
                    assert proc.returncode == 0, proc.stderr
                    return proc.stdout.strip()

            yield Database()
        finally:
            admin.execute(psycopg.sql.SQL("DROP DATABASE {} WITH (FORCE)").format(psycopg.sql.Identifier(name)))
            # Only the inherited suites' known fixture roles, only if this
            # session created them. Never drop an already-existing principal.
            for role in ("amjis_app", "nirmana_campaign_control_writer", "nirmana_evidence_ingress_writer"):
                if role not in existing:
                    admin.execute(psycopg.sql.SQL("DROP ROLE IF EXISTS {}").format(psycopg.sql.Identifier(role)))
