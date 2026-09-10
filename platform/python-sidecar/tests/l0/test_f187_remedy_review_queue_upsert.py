"""
PARIŚEṢA-V4 F-187 — ``remedy_review_queue.remedy_id`` unique-index gap.

Authority: ``00_ARCHITECTURE/briefs/parisesa/state/OWNER_RULINGS_*.md`` (the
PARISESA-V4 F-187 ruling: fix via a schema migration adding
``ux_remedy_review_queue_remedy_id``, natural key ``remedy_id`` alone,
matching ``insert_to_review_queue()``'s own ``ON CONFLICT (remedy_id)``
intent — do not widen the key).

``brahmagyan.l0_remedy_loader.insert_to_review_queue()`` issues:

    INSERT INTO remedy_review_queue ( ... 25 columns ... )
    ON CONFLICT (remedy_id) DO UPDATE SET
        rejection_reason = EXCLUDED.rejection_reason,
        review_status = 'pending'

``remedy_review_queue`` was created by
``platform/supabase/migrations/081_l0fr_schema.sql`` with a surrogate `id`
primary key and no unique index/constraint on ``remedy_id`` — only two
non-unique indexes (``idx_remedy_review_status``, ``idx_remedy_review_planet``).
An ``ON CONFLICT (col)`` clause requires a unique index/constraint matching
its inference column to exist; Postgres validates the arbiter at plan time,
so the statement fails with 42P10 ("there is no unique or exclusion
constraint matching the ON CONFLICT specification") on EVERY execution, not
only when an actual duplicate ``remedy_id`` is inserted. Migration 584
(``584_remedy_review_queue_remedy_id_unique.sql``) adds
``CREATE UNIQUE INDEX IF NOT EXISTS ux_remedy_review_queue_remedy_id ON
remedy_review_queue (remedy_id);`` to fix this.

WHAT THE DETECTOR ACTUALLY MEASURES (CLAUDE.md §N.8): these tests exercise
real ``ON CONFLICT ... DO UPDATE`` arbiter-resolution semantics against a
live sqlite backend (not a string match on the SQL text). sqlite validates
an ON CONFLICT target the same way Postgres does — a call against a schema
with no matching unique index/constraint raises ``OperationalError`` on the
very first execution, with or without an actual duplicate key, which is
exactly the observed production failure mode (the loader's own docstring
notes this ON CONFLICT path "has never successfully executed"). A test that
merely checked the SQL string contains ``ON CONFLICT (remedy_id)`` would not
have caught this — the bug is in the SCHEMA, not the statement text; only
running the statement against each schema variant proves the fix.
"""
from __future__ import annotations

import re
import sqlite3
from typing import Any

import pytest

from brahmagyan import l0_remedy_loader


# ── DDL variants ────────────────────────────────────────────────────────────

# Mirrors remedy_review_queue as created by
# platform/supabase/migrations/081_l0fr_schema.sql:126-163 — surrogate `id`
# PK, remedy_id NOT NULL with NO unique index/constraint. This is the
# pre-F-187-fix, currently-live production schema.
_REVIEW_QUEUE_DDL_NO_UNIQUE = """
CREATE TABLE remedy_review_queue (
    id                         INTEGER PRIMARY KEY AUTOINCREMENT,
    remedy_id                  TEXT NOT NULL,
    planet                     TEXT NOT NULL,
    domain                     TEXT NOT NULL,
    remedy_type                TEXT NOT NULL,
    prescription_text          TEXT NOT NULL,
    mantra_text                TEXT,
    gemstone                   TEXT,
    charity_action              TEXT,
    day_of_week                TEXT,
    color_associated           TEXT,
    confidence                 NUMERIC NOT NULL DEFAULT 0.85,
    source_canonical_id        TEXT NOT NULL,
    source_citation             TEXT NOT NULL,
    classical_ref               TEXT,
    category                   TEXT,
    deity                      TEXT,
    mantra_sanskrit             TEXT,
    mantra_transliteration      TEXT,
    ingredients_jsonb           TEXT,
    timing_rules_jsonb          TEXT,
    cost_tier                  TEXT,
    contraindications           TEXT,
    classical_attestation_text  TEXT,
    rejection_reason           TEXT,
    review_status               TEXT NOT NULL DEFAULT 'pending',
    created_at                  TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

# Same table, PLUS migration 584's fix: a unique index on remedy_id — the
# post-fix schema.
_REVIEW_QUEUE_DDL_WITH_UNIQUE = _REVIEW_QUEUE_DDL_NO_UNIQUE + """;
CREATE UNIQUE INDEX ux_remedy_review_queue_remedy_id
  ON remedy_review_queue (remedy_id)
"""


class _SqliteCursor:
    """Runs the loader's psycopg SQL against sqlite (pyformat → named params)."""

    def __init__(self, cur: sqlite3.Cursor) -> None:
        self._cur = cur

    def __enter__(self) -> "_SqliteCursor":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def execute(self, sql: str, params: Any = None) -> None:
        sql = sql.replace('::jsonb', '')
        sql = re.sub(r'%\((\w+)\)s', r':\1', sql)
        self._cur.execute(sql, params or {})


class _SqliteConn:
    def __init__(self, raw: sqlite3.Connection) -> None:
        self._raw = raw

    def cursor(self) -> _SqliteCursor:
        return _SqliteCursor(self._raw.cursor())

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()


def _make_conn(ddl: str) -> _SqliteConn:
    raw = sqlite3.connect(':memory:')
    raw.executescript(ddl)
    raw.row_factory = sqlite3.Row
    return _SqliteConn(raw)


def _review_row(*, remedy_id: str = 'f187_saturn_tantric') -> dict[str, Any]:
    """A minimal row shape sufficient for insert_to_review_queue()."""
    return {
        'remedy_id': remedy_id,
        'planet': 'Saturn',
        'domain': 'health',
        'category': 'tantric',
        'remedy_text': 'A tantric remedy pending review.',
        'source_text': 'unknown',
    }


def _stored_rows(conn: _SqliteConn) -> list[sqlite3.Row]:
    return conn._raw.execute('SELECT * FROM remedy_review_queue').fetchall()


class TestMissingUniqueIndexReproducesTheLiveDefect:
    """Pre-fix schema (081 as shipped, no migration 584): every call fails.

    This is the must-fail-today case — the exact live 42P10 failure mode.
    sqlite validates the ON CONFLICT arbiter the same way Postgres does: the
    statement fails on its very first execution because no unique index
    matches the inference clause, independent of whether a real duplicate
    remedy_id is ever inserted.
    """

    def test_single_insert_raises_with_no_unique_index(self):
        conn = _make_conn(_REVIEW_QUEUE_DDL_NO_UNIQUE)

        with pytest.raises(Exception):
            l0_remedy_loader.insert_to_review_queue(
                conn, _review_row(), reason='missing required source columns',
            )

        # insert_to_review_queue re-raises (does not swallow) — no row landed.
        assert _stored_rows(conn) == []

    def test_loader_reraises_rather_than_swallowing(self):
        """Confirms the function's own contract: except/log/raise, not except/pass."""
        conn = _make_conn(_REVIEW_QUEUE_DDL_NO_UNIQUE)

        with pytest.raises(Exception) as excinfo:
            l0_remedy_loader.insert_to_review_queue(
                conn, _review_row(), reason='missing required source columns',
            )
        # sqlite's arbiter-mismatch error text, standing in for Postgres 42P10.
        assert 'ON CONFLICT' in str(excinfo.value)


class TestUniqueIndexFixesTheUpsert:
    """Post-fix schema (081 + migration 584): the upsert works as intended."""

    def test_first_insert_succeeds(self):
        conn = _make_conn(_REVIEW_QUEUE_DDL_WITH_UNIQUE)

        l0_remedy_loader.insert_to_review_queue(
            conn, _review_row(), reason='missing required source columns',
        )

        rows = _stored_rows(conn)
        assert len(rows) == 1
        assert rows[0]['remedy_id'] == 'f187_saturn_tantric'
        assert rows[0]['rejection_reason'] == 'missing required source columns'
        assert rows[0]['review_status'] == 'pending'

    def test_second_insert_same_remedy_id_upserts_one_row(self):
        """The assertion that closes the finding (§F-187.3 step 6, in-process
        harness form): two inserts of the same remedy_id must produce exactly
        one row, carrying the SECOND call's rejection_reason."""
        conn = _make_conn(_REVIEW_QUEUE_DDL_WITH_UNIQUE)

        l0_remedy_loader.insert_to_review_queue(
            conn, _review_row(), reason='missing required source columns',
        )
        l0_remedy_loader.insert_to_review_queue(
            conn, _review_row(), reason='unacceptable tantric source',
        )

        rows = _stored_rows(conn)
        assert len(rows) == 1, f'expected exactly one row (upsert), got {len(rows)}'
        assert rows[0]['rejection_reason'] == 'unacceptable tantric source', (
            "second call's rejection_reason must win — this is the upsert's "
            'whole reason to exist'
        )
        assert rows[0]['review_status'] == 'pending'

    def test_upsert_does_not_touch_other_remedy_ids(self):
        conn = _make_conn(_REVIEW_QUEUE_DDL_WITH_UNIQUE)

        l0_remedy_loader.insert_to_review_queue(
            conn, _review_row(remedy_id='f187_saturn_tantric'),
            reason='missing required source columns',
        )
        l0_remedy_loader.insert_to_review_queue(
            conn, _review_row(remedy_id='f187_rahu_tantric'),
            reason='missing required source columns',
        )
        l0_remedy_loader.insert_to_review_queue(
            conn, _review_row(remedy_id='f187_saturn_tantric'),
            reason='unacceptable tantric source',
        )

        rows = {row['remedy_id']: row for row in _stored_rows(conn)}
        assert set(rows) == {'f187_saturn_tantric', 'f187_rahu_tantric'}
        assert rows['f187_saturn_tantric']['rejection_reason'] == 'unacceptable tantric source'
        assert rows['f187_rahu_tantric']['rejection_reason'] == 'missing required source columns'
