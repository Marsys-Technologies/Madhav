"""Disposable-database fixture for the K0a idempotency oracle suite.

The lane rehearsal database and CI's throwaway PostgreSQL service are the only
permitted targets.  Tests create TEMP tables only, so no persistent schema or
row can be changed by this suite.
"""

from __future__ import annotations

import os

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict


def _disposable_test_dsn() -> str:
    """Return the explicitly enabled lane-server or CI disposable PostgreSQL DSN."""
    if os.environ.get("KALA_REQUIRE_DB") != "1":
        raise RuntimeError("KALA_REQUIRE_DB=1 is required for database oracle tests")

    dsn = os.environ["KALA_ADMIN_DSN"]
    parts = conninfo_to_dict(dsn)
    lane = os.environ.get("KY_LANE")
    is_lane_database = (
        parts.get("host") == "127.0.0.1"
        and parts.get("port") == "55433"
        and lane is not None
        and parts.get("dbname") == f"ky_{lane}"
    )
    is_lane_server_temp_endpoint = (
        parts.get("host") == "127.0.0.1"
        and parts.get("port") == "55433"
        and parts.get("dbname") == "postgres"
    )
    is_ci_service = (
        parts.get("host") == "localhost"
        and parts.get("port") == "5432"
        and parts.get("dbname") == "postgres"
    )
    if not (is_lane_database or is_lane_server_temp_endpoint or is_ci_service):
        raise RuntimeError("KALA_ADMIN_DSN must name the lane or CI disposable database")
    return dsn


@pytest.fixture
def conn():
    """A connection whose test tables are TEMP and session-local."""
    with psycopg.connect(_disposable_test_dsn()) as connection:
        yield connection
