"""An issued forecast is inserted once and never changed by a retry."""

import os
from datetime import datetime

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from psycopg.types.json import Jsonb

from services.kala_core.idempotency import ImmutableIssueConflict, insert_immutable_checked


@pytest.fixture
def conn():
    dsn = os.environ["KALA_ADMIN_DSN"]
    parts = conninfo_to_dict(dsn)
    assert parts.get("host") == "127.0.0.1"
    assert parts.get("port") == "55433"
    lane_dsn = make_conninfo(dsn, dbname=f"ky_{os.environ['KY_LANE']}")
    with psycopg.connect(lane_dsn) as connection:
        connection.execute(
            "CREATE TEMP TABLE issued_forecast ("
            " issue_id text NOT NULL, version integer NOT NULL,"
            " episode_id text NOT NULL, statement text NOT NULL, payload jsonb NOT NULL,"
            " delivered_at timestamptz NOT NULL,"
            " PRIMARY KEY (issue_id, version))"
        )
        yield connection


def _issue(version=1, statement="original"):
    return {
        "issue_id": "issue-a",
        "version": version,
        "episode_id": "episode-a",
        "statement": statement,
        "payload": Jsonb({"probability": None}),
        "delivered_at": datetime.fromisoformat("2026-10-07T08:00:00+00:00"),
    }


def _key(row):
    return {"issue_id": row["issue_id"], "version": row["version"]}


def _stored(conn):
    return conn.execute(
        "SELECT issue_id, version, episode_id, statement "
        "FROM issued_forecast ORDER BY issue_id, version"
    ).fetchall()


def test_identical_retry_is_a_no_op_and_changed_issue_is_refused(conn):
    original = _issue()
    assert insert_immutable_checked(conn, "issued_forecast", _key(original), original)
    assert not insert_immutable_checked(conn, "issued_forecast", _key(original), original)

    changed = _issue(statement="silently changed")
    with pytest.raises(ImmutableIssueConflict, match="cannot be changed"):
        insert_immutable_checked(conn, "issued_forecast", _key(changed), changed)
    assert _stored(conn) == [("issue-a", 1, "episode-a", "original")]


def test_new_version_is_distinct_but_reusing_key_for_another_episode_fails(conn):
    first = _issue()
    second = _issue(version=2, statement="revision")
    assert insert_immutable_checked(conn, "issued_forecast", _key(first), first)
    assert insert_immutable_checked(conn, "issued_forecast", _key(second), second)

    wrong_episode = dict(first, episode_id="episode-b")
    with pytest.raises(ImmutableIssueConflict):
        insert_immutable_checked(conn, "issued_forecast", _key(wrong_episode), wrong_episode)
    assert _stored(conn) == [
        ("issue-a", 1, "episode-a", "original"),
        ("issue-a", 2, "episode-a", "revision"),
    ]


def test_bad_key_and_wrong_table_fail_before_any_write(conn):
    row = _issue()
    with pytest.raises(ValueError, match="issue key"):
        insert_immutable_checked(conn, "issued_forecast", {"episode_id": "episode-a"}, row)
    with pytest.raises(ValueError, match="does not match"):
        insert_immutable_checked(conn, "issued_forecast", {"issue_id": "other", "version": 1}, row)
    with pytest.raises(ValueError, match="not an immutable issue table"):
        insert_immutable_checked(conn, "kala_darshana", _key(row), row)
    assert _stored(conn) == []
