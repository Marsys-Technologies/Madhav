"""Migration 1361: bg_doshas' integrity_check_sql re-sealed after the formation_rule_jsonb leaves moved to ONE spelling family (names).

Static tier: the NEW check equals migration 1324's check with exactly one replacement (the catalog content hash), both texts hash to the md5 named in the migration.
LIVE tier on a DISPOSABLE local PostgreSQL (skipped loudly when no server binaries are found): the REAL seed_doshas writer fills the three projections; the NEW check is TRUE on
the rebuilt state and FALSE on drift (a leaf spelled back to the old lowercase id, a dropped row, an ontology-only edit); 1324's check is FALSE there (its catalog pin is the old
spelling's). The UPDATE is md5-guarded (a foreign text is left alone with a NOTICE), idempotent, and a silent no-op / a half-applied text is caught by the post-check.
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
_MIG = _REPO / "platform" / "migrations" / "1361_bg_doshas_formation_rule_one_spelling_family_reseal.sql"
_M1324 = _REPO / "platform" / "migrations" / "1324_bg_doshas_citation_pass2_integrity_reseal.sql"
OLD_TEXT = re.search(r"\$ic\$(.*?)\$ic\$", _M1324.read_text(), re.S).group(1)
NEW_TEXT = re.search(r"\$ic\$(.*?)\$ic\$", _MIG.read_text(), re.S).group(1)
OLD_PIN = "308ce2a6048c488eefcea3abe8fa9c9c90d383981f9133b667614ac31d94628b"
NEW_PIN = "5c5182366bdfcc36e5f56951ba3eedbf9a2b527d5d02875ddf8a12d162c9dc7e"
OLD_MD5, NEW_MD5 = "e4baff75780519cc4fdf76b6ce27c9fd", "58a572d44f8baf80884e4e581dae7d7d"
md5 = lambda s: hashlib.md5(s.encode()).hexdigest()

DDL = """
CREATE TABLE brahma_dosha_catalog(canonical_id text primary key,name_sa text,name_en text,category text,formation_rule_jsonb jsonb,formation_text text,effects_text text,severity_grades jsonb,cancellation_conditions jsonb,classical_citations jsonb,source_chunk_ids bigint[],associated_remedies uuid[],school text,created_at timestamptz);
CREATE TABLE brahma_ontology(entity_class text,canonical_id text,canonical_name_en text,canonical_name_sa text,synonyms text[],description text,source_citation text,created_at timestamptz,primary key(entity_class,canonical_id));
CREATE TABLE reference_doshas(canonical_id text primary key,name_en text,category text);
CREATE TABLE asset_registry(asset_id text primary key, integrity_check_sql text, target_floor bigint, volume_explanation text);
"""


def _setup(port, text=OLD_TEXT, floor=198):
    db = new_db(port)
    assert psql(port, db, DDL).returncode == 0
    conn = psycopg.connect(f"host=127.0.0.1 port={port} user=postgres dbname={db}", row_factory=dict_row)
    with conn.cursor() as c:
        c.execute("INSERT INTO asset_registry VALUES ('bg_doshas', %s, %s, 'kept')", (text, floor))
    conn.commit()
    return db, conn


def _check(conn, sql) -> bool:
    with conn.cursor() as c:
        c.execute(sql)
        return list(c.fetchone().values())[0] is True


def test_static_texts_hash_to_the_named_md5_and_differ_only_in_the_catalog_pin():
    assert md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == 2206
    assert md5(NEW_TEXT) == NEW_MD5 and len(NEW_TEXT) == 2206
    assert OLD_TEXT.count(OLD_PIN) == 1 and NEW_TEXT.count(NEW_PIN) == 1 and OLD_PIN not in NEW_TEXT and NEW_PIN not in OLD_TEXT
    assert OLD_TEXT.replace(OLD_PIN, NEW_PIN) == NEW_TEXT                  # exactly one replacement: counts, ontology hash, reference hash and the join are untouched
    assert "count(*) = 66" in NEW_TEXT and "ed74d67afa450fdbcc22940a155243e2dbd72a78bbc7f4c16585330de0cae72d" in NEW_TEXT and "29ff924c2627ff1d9f1f3036188249351ba51a46ef99757d3c271e55dd2c86b7" in NEW_TEXT


def test_static_migration_guards_on_the_1324_state_and_raises_on_a_stuck_update():
    sql = _MIG.read_text()
    assert f"md5(integrity_check_sql) = '{OLD_MD5}'" in sql and "target_floor = 198" in sql
    assert sql.count("RAISE EXCEPTION") == 2 and "update did not take" in sql
    code = "\n".join(l for l in sql.splitlines() if not l.startswith("--"))
    assert "COMMIT" not in code and not re.search(r"^\s*BEGIN\s*;", code, re.M)                                  # transaction ownership belongs to migrate.ts


def test_live_rebuilt_state_satisfies_the_new_check_only(pg):
    from brahmagyan import l0_doshas
    db, conn = _setup(pg)
    try:
        l0_doshas.seed_doshas(conn, autocommit=False)
        conn.commit()
        assert _check(conn, NEW_TEXT) is True
        assert _check(conn, OLD_TEXT) is False                      # 1324's catalog pin is the previous (mixed-spelling) seed's
        with conn.cursor() as c:                                    # the hash really covers the leaf spellings: one leaf spelled back to the old id breaks it
            c.execute("UPDATE brahma_dosha_catalog SET formation_rule_jsonb = jsonb_set(formation_rule_jsonb, '{planet}', '\"mars\"') WHERE canonical_id='manglik'")
        assert _check(conn, NEW_TEXT) is False
        conn.rollback()
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
            c.execute("SELECT formation_rule_jsonb->>'planet' AS p, formation_rule_jsonb->'reference' AS r FROM brahma_dosha_catalog WHERE canonical_id='manglik'")
            row = c.fetchone()
            assert row["p"] == "Mars" and row["r"] == ["Lagna", "Moon", "Venus"]
    finally:
        conn.close()


def test_live_migration_applies_once_is_guarded_and_idempotent(pg):
    db, conn = _setup(pg)
    conn.close()
    r = psql(pg, db, file=_MIG, single_transaction=True)
    assert r.returncode == 0, r.stderr
    assert q(pg, db, "SELECT md5(integrity_check_sql)||' '||target_floor||' '||volume_explanation FROM asset_registry WHERE asset_id='bg_doshas'") == f"{NEW_MD5} 198 kept"
    r2 = psql(pg, db, file=_MIG, single_transaction=True)                  # second apply: already carries NEW -> NOTICE, nothing rewritten
    assert r2.returncode == 0 and "already carries the one-spelling-family catalog pin" in r2.stderr


def test_live_foreign_text_is_left_alone_and_a_silent_noop_is_caught(pg):
    db, conn = _setup(pg, text="SELECT true", floor=198)
    conn.close()
    r = psql(pg, db, file=_MIG, single_transaction=True)
    assert r.returncode == 0 and "NO-OP" in r.stderr
    assert q(pg, db, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='bg_doshas'") == "SELECT true"
    # OLD text but a different floor: the guard matches 0 rows and the post-check raises (the update did not take)
    db2, conn2 = _setup(pg, text=OLD_TEXT, floor=999)
    conn2.close()
    r3 = psql(pg, db2, file=_MIG, single_transaction=True)
    assert r3.returncode != 0 and "update did not take" in r3.stderr
