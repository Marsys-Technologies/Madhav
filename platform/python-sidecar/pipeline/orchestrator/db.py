"""DB connection helper shared across orchestrator modules."""
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
    return psycopg.connect(
        db_url(),
        row_factory=psycopg.rows.dict_row,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
        options="-c idle_in_transaction_session_timeout=0",
    )
