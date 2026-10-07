"""Publication switches only the chart head seen when a candidate opened."""

import os

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from services.kala_core.idempotency import (
    PublishCandidate,
    StalePublishedHead,
    publish_head,
)


@pytest.fixture
def conn():
    dsn = os.environ["KALA_ADMIN_DSN"]
    parts = conninfo_to_dict(dsn)
    assert parts.get("host") == "127.0.0.1"
    assert parts.get("port") == "55433"
    lane_dsn = make_conninfo(dsn, dbname=f"ky_{os.environ['KY_LANE']}")
    with psycopg.connect(lane_dsn) as connection:
        connection.execute(
            "CREATE TEMP TABLE kala_layer_head ("
            " chart_id text PRIMARY KEY, generation text NOT NULL)"
        )
        yield connection


def _heads(conn):
    return conn.execute(
        "SELECT chart_id, generation FROM kala_layer_head ORDER BY chart_id"
    ).fetchall()


def test_first_publish_update_stale_refusal_and_rollback(conn):
    publish_head(conn, "chart-a", PublishCandidate("generation-1", None))
    assert _heads(conn) == [("chart-a", "generation-1")]

    publish_head(conn, "chart-a", PublishCandidate("generation-2", "generation-1"))
    assert _heads(conn) == [("chart-a", "generation-2")]

    with pytest.raises(StalePublishedHead):
        publish_head(conn, "chart-a", PublishCandidate("stale", "generation-1"))
    with pytest.raises(StalePublishedHead):
        publish_head(conn, "chart-a", PublishCandidate("first-again", None))
    assert _heads(conn) == [("chart-a", "generation-2")]

    publish_head(conn, "chart-a", PublishCandidate("generation-1", "generation-2"))
    assert _heads(conn) == [("chart-a", "generation-1")]


def test_expected_head_is_required_and_other_chart_is_untouched(conn):
    publish_head(conn, "chart-a", PublishCandidate("a-1", None))
    publish_head(conn, "chart-b", PublishCandidate("b-1", None))
    with pytest.raises(StalePublishedHead):
        publish_head(conn, "chart-c", PublishCandidate("c-1", "unknown"))
    publish_head(conn, "chart-a", PublishCandidate("a-2", "a-1"))
    assert _heads(conn) == [("chart-a", "a-2"), ("chart-b", "b-1")]


def test_missing_identity_fails_before_write(conn):
    with pytest.raises(ValueError, match="must be pinned"):
        publish_head(conn, "", PublishCandidate("generation-1", None))
    with pytest.raises(ValueError, match="must be pinned"):
        publish_head(conn, "chart-a", PublishCandidate("", None))
    with pytest.raises(ValueError, match="pinned or null"):
        publish_head(conn, "chart-a", PublishCandidate("generation-1", ""))
    assert _heads(conn) == []
