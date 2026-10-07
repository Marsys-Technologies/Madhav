"""Migration 1324 (CITATION-PASS2, decision OS-2026-10-05-CITATIONS): bg_doshas' integrity_check_sql / target_floor / volume_explanation re-sealed to the 66-row state.

LIVE tier on a DISPOSABLE local PostgreSQL (skipped loudly when no server binaries are found): the REAL seed_doshas writer fills the three projections, then the
REAL on-disk migration is applied to a registry row carrying migration 692's text. Proves: the OLD check is TRUE on the old 79-row state's shape and FALSE on the rebuilt
66-row state; the NEW check is TRUE on the rebuilt state and FALSE after a semantic drift, a dropped row and an ontology-only edit; the UPDATE is md5-guarded (a foreign text is
left alone with a NOTICE), idempotent, and a silent no-op is caught by the post-check.
"""
from __future__ import annotations

import hashlib
import pathlib
import re

import psycopg
import pytest
from psycopg.rows import dict_row

from tests.pg_disposable import new_db, psql, q, pg  # noqa: F401  (pg is a fixture)

_REPO = pathlib.Path(__file__).resolve().parents[4]
_MIG = _REPO / "platform" / "migrations" / "1324_bg_doshas_citation_pass2_integrity_reseal.sql"
_M692 = _REPO / "platform" / "migrations" / "692_bg_doshas_integrity_check_join_scope_fix.sql"
OLD_TEXT = re.search(r"\$check\$(.*?)\$check\$", _M692.read_text(), re.S).group(1)
NEW_TEXT = re.search(r"\$ic\$(.*?)\$ic\$", _MIG.read_text(), re.S).group(1)
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()

DDL = """
CREATE TABLE brahma_dosha_catalog(canonical_id text primary key,name_sa text,name_en text,category text,formation_rule_jsonb jsonb,formation_text text,effects_text text,severity_grades jsonb,cancellation_conditions jsonb,classical_citations jsonb,source_chunk_ids bigint[],associated_remedies uuid[],school text,created_at timestamptz);
CREATE TABLE brahma_ontology(entity_class text,canonical_id text,canonical_name_en text,canonical_name_sa text,synonyms text[],description text,source_citation text,created_at timestamptz,primary key(entity_class,canonical_id));
CREATE TABLE reference_doshas(canonical_id text primary key,name_en text,category text);
CREATE TABLE asset_registry(asset_id text primary key, integrity_check_sql text, target_floor bigint, volume_explanation text);
"""


def _setup(port, text=OLD_TEXT, floor=237):
    db = new_db(port)
    assert psql(port, db, DDL).returncode == 0
    conn = psycopg.connect(f"host=127.0.0.1 port={port} user=postgres dbname={db}", row_factory=dict_row)
    with conn.cursor() as c:
        c.execute("INSERT INTO asset_registry VALUES ('bg_doshas', %s, %s, 'old')", (text, floor))
    conn.commit()
    return db, conn


def _check(conn, sql) -> bool:
    with conn.cursor() as c:
        c.execute(sql)
        return list(c.fetchone().values())[0] is True


def _reg(conn):
    with conn.cursor() as c:
        c.execute("SELECT md5(integrity_check_sql) AS m, target_floor AS f, volume_explanation AS v FROM asset_registry WHERE asset_id='bg_doshas'")
        return c.fetchone()


def test_static_old_and_new_text_hash_to_the_named_md5():
    assert md5(OLD_TEXT) == "681d6b26ff4e5816a3f08650cdb76b4b" and len(OLD_TEXT) == 2206
    assert md5(NEW_TEXT) == "e4baff75780519cc4fdf76b6ce27c9fd" and len(NEW_TEXT) == 2206


def test_live_rebuilt_state_satisfies_the_new_check_only(pg):
    from brahmagyan import l0_doshas
    db, conn = _setup(pg)
    try:
        l0_doshas.seed_doshas(conn, autocommit=False)
        conn.commit()
        assert _check(conn, NEW_TEXT) is True
        assert _check(conn, OLD_TEXT) is False                      # 79-row pins no longer hold: the check is re-sealed, not loosened
        # drift detection on the NEW text
        with conn.cursor() as c:
            c.execute("UPDATE brahma_dosha_catalog SET effects_text='drift' WHERE canonical_id='angarak'")
        assert _check(conn, NEW_TEXT) is False
        conn.rollback()
        with conn.cursor() as c:
            c.execute("UPDATE brahma_ontology SET source_citation='drift' WHERE entity_class='dosha' AND canonical_id='angarak'")
        assert _check(conn, NEW_TEXT) is False
        conn.rollback()
        with conn.cursor() as c:
            c.execute("DELETE FROM reference_doshas WHERE canonical_id='angarak'")
        assert _check(conn, NEW_TEXT) is False
        conn.rollback()
        with conn.cursor() as c:
            c.execute("SELECT (SELECT count(*) FROM brahma_dosha_catalog) AS a, (SELECT count(*) FROM brahma_ontology WHERE entity_class='dosha') AS b, (SELECT count(*) FROM reference_doshas) AS c")
            assert tuple(c.fetchone().values()) == (66, 66, 66)
    finally:
        conn.close()


def test_live_migration_applies_once_is_guarded_and_idempotent(pg):
    db, conn = _setup(pg)
    conn.close()
    r = psql(pg, db, file=_MIG, single_transaction=True)
    assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT md5(integrity_check_sql)||' '||target_floor FROM asset_registry WHERE asset_id='bg_doshas'") == "e4baff75780519cc4fdf76b6ce27c9fd 198"
    r2 = psql(pg, db, file=_MIG, single_transaction=True)                  # second apply: already carries NEW -> NOTICE, nothing rewritten
    assert r2.returncode == 0 and "already carries the citation-pass-2 pins" in r2.stderr


def test_live_foreign_text_is_left_alone_and_a_silent_noop_is_caught(pg):
    db, conn = _setup(pg, text="SELECT true", floor=237)
    conn.close()
    r = psql(pg, db, file=_MIG, single_transaction=True)
    assert r.returncode == 0 and "NO-OP" in r.stderr
    assert q(pg, db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_doshas'") == "SELECT true"
    # OLD text but a different floor: the guard matches 0 rows and the post-check raises (the update did not take)
    db2, conn2 = _setup(pg, text=OLD_TEXT, floor=999)
    conn2.close()
    r3 = psql(pg, db2, file=_MIG, single_transaction=True)
    assert r3.returncode != 0 and "update did not take" in r3.stderr
