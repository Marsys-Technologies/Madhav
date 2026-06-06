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
    return psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row)
