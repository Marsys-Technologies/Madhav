"""DB connection helper shared across orchestrator modules.

PARIṢKĀRA MR-39: `connect()` below is the orchestrator's own build-session
connection factory (used by `runner.py` and `global_runner.py`, the two
entry points that drive real chart builds). It already carries the MR-39
remediation — a SESSION-scoped `SET idle_in_transaction_session_timeout = 0`
at connection setup (never `ALTER DATABASE`/`ALTER ROLE`) — landed prior to
this campaign. MR-39 closed the remaining gap: several standalone
build-runner scripts at the sidecar root (`run_heavy_writer_standalone.py`,
`run_elev_beta_d_rebuild.py`, `run_elev_beta_integration_rebuild.py`) drove
writer substeps via a bare `psycopg.connect()` that bypassed this factory
entirely and therefore lacked the same protection; those now route through
`connect()` below. `run_ka_sangam_prod.py` / `run_ph_pratikara_prod.py`
needed to keep their own `prepare_threshold=None` pooler-compatibility flag
so they were given the equivalent `SET` directly instead of being routed
through this factory.
"""
from __future__ import annotations

import os

import psycopg
import psycopg.rows


def db_url() -> str:
    for key in ("DATABASE_URL", "DIRECT_DATABASE_URL", "POSTGRES_URL"):
        v = os.environ.get(key, "")
        if v:
            return v
    raise RuntimeError("[orchestrator] DATABASE_URL not set")


def connect() -> psycopg.Connection:
    # keepalives prevent Cloud SQL from closing an idle connection mid-transaction
    # (the orchestrator holds a transaction open while a writer does CPU-heavy work).
    # idle_in_transaction_session_timeout=0 disables the server-side idle-in-txn
    # killer for this connection — correct for build workers that legitimately hold
    # open transactions for up to several minutes per ayanamsha substep.
    conn = psycopg.connect(
        db_url(),
        row_factory=psycopg.rows.dict_row,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
        options="-c idle_in_transaction_session_timeout=0",
    )
    # Defense-in-depth: the `options` startup parameter above is NOT guaranteed to
    # reach the server unmodified through every connection path (a local Cloud SQL
    # Auth Proxy — or any intermediate pooler — may not forward arbitrary libpq
    # startup options). The amjis_app role carries its own
    # `ALTER ROLE ... SET idle_in_transaction_session_timeout=600s` default
    # (10 minutes) — if the startup option above is dropped in transit, that
    # role-level 600s killer silently wins and any writer whose transaction sits
    # idle-in-transaction for >10 minutes of pure CPU work (no SQL activity) gets
    # its connection terminated by the server, independent of TCP keepalive health.
    # An explicit SET, issued as a real statement, cannot be stripped by a proxy —
    # it is indistinguishable from any other query on the wire.
    with conn.cursor() as cur:
        cur.execute("SET idle_in_transaction_session_timeout = 0")
        cur.execute("SET statement_timeout = 0")
    conn.commit()
    return conn
