"""K-CERT-2: dispatchable citation writer, sealed content and registry truth.

Fixture provenance: PR #3055's production read of 2026-10-03. PostgreSQL
oracles use migration 631's actual sealed detector, never a copied digest.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
import pytest

from pipeline.orchestrator.writers import ContextSpec, WriterBase, discover_all, get_writer

PLATFORM = Path(__file__).resolve().parents[4]
SIDECAR = PLATFORM / "python-sidecar"
LIVE = json.loads((SIDECAR / "tests/fixtures/gochara_citation_resolution_live.json").read_text())
ASSET = "bg_gochara_citation_resolution"
MIGRATION = PLATFORM / "migrations/1362_gochara_citation_resolution_dispatchable.sql"
COLS = "citation_string,chunk_id,text_id,verse_ref,status,source_citation,constant_name,note"
DDL = """
CREATE TABLE classical_text_chunks (chunk_id text PRIMARY KEY, text_id text, verse_ref text);
INSERT INTO classical_text_chunks VALUES ('phaladeepika_pg0353_c01','phaladeepika','PG353:C1');
CREATE TABLE bg_gochara_citation_resolution (
 citation_string text NOT NULL, chunk_id text NOT NULL, text_id text NOT NULL, verse_ref text NOT NULL,
 status text NOT NULL DEFAULT 'resolved' CHECK (status IN ('resolved','unresolved')),
 source_citation text NOT NULL, constant_name text, note text, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY (citation_string,chunk_id));
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, has_writer boolean,
 count_sql text, target_table text, scope text, is_active boolean);
INSERT INTO asset_registry VALUES
 ('bg_gochara_citation_resolution',false,'SELECT -1','bg_gochara_citation_resolution','global',true),
 ('bg_sarvatobhadra_grid',false,'SELECT 0','bg_sarvatobhadra_grid','global',true);
"""


def writer():
    discover_all()
    cls = get_writer(ASSET)
    assert cls is not None, "citation asset must be dispatchable without an environment flag"
    return cls()


def context(conn=None, *, dry_run=False):
    return ContextSpec(asset_id=ASSET, build_id="k-cert-2-fixture", db_conn=conn, dry_run=dry_run)


def sealed_sql():
    source = (PLATFORM / "supabase/migrations/631_nirmana_l0_gochara_citation_chunk_repair.sql").read_text()
    match = re.search(r"citation_check constant text := \$check\$(.*?)\$check\$;", source, re.S)
    assert match
    return match.group(1).strip()


def rows(conn):
    return [dict(r) for r in conn.execute(
        f'SELECT {COLS} FROM bg_gochara_citation_resolution '
        'ORDER BY citation_string COLLATE "C", chunk_id COLLATE "C"'
    )]


def insert_live(conn):
    for row in LIVE:
        conn.execute(f"INSERT INTO bg_gochara_citation_resolution ({COLS}) "
                     "VALUES (%(citation_string)s,%(chunk_id)s,%(text_id)s,%(verse_ref)s,"
                     "%(status)s,%(source_citation)s,%(constant_name)s,%(note)s)", row)


@pytest.fixture
def db(kala_db_dsn):
    with psycopg.connect(kala_db_dsn, row_factory=dict_row) as conn:
        conn.execute(DDL)
        conn.commit()
        try:
            yield conn
        finally:
            conn.rollback()
            conn.execute("DROP TABLE asset_registry, bg_gochara_citation_resolution, classical_text_chunks")
            conn.commit()


def test_registered_writer_honors_frozen_contract_and_dry_run():
    instance = writer()
    assert isinstance(instance, WriterBase)
    assert instance.run(context(dry_run=True)).rows_inserted == 14


def test_seed_matches_the_independent_live_fixture():
    writer()
    from brahmagyan.l0_gochara_citation_resolution import ROWS
    assert ROWS == LIVE


def test_registry_bootstrap_matches_dispatchable_writer():
    source = (PLATFORM / "scripts/seed/asset_registry_seed.ts").read_text()
    entry = re.search(r"asset_id: 'bg_gochara_citation_resolution',(.*?)\n  },", source, re.S)
    assert entry and "has_writer: true" in entry.group(1)


def test_real_writer_repairs_damaged_content_and_recomputes_sealed_digest(db):
    instance = writer()
    insert_live(db)
    assert next(iter(db.execute(sealed_sql()).fetchone().values())) is True
    db.execute("INSERT INTO bg_gochara_citation_resolution VALUES "
               "('zz stray','CORPUS_GAP:zz','bphs','CH1','unresolved','x','ZZ',NULL)")
    db.execute("UPDATE bg_gochara_citation_resolution SET verse_ref='TAMPERED' "
               "WHERE constant_name='GOCHARA_PHALA_BPHS_29'")
    db.execute("DELETE FROM bg_gochara_citation_resolution WHERE constant_name='SADE_SATI_BPHS_71'")
    assert next(iter(db.execute(sealed_sql()).fetchone().values())) is False
    assert instance.run(context(db)).rows_inserted == 14
    assert rows(db) == LIVE
    assert next(iter(db.execute(sealed_sql()).fetchone().values())) is True
    instance.run(context(db))
    assert rows(db) == LIVE


def test_writer_leaves_transaction_and_connection_owned_by_caller(db):
    instance = writer()
    insert_live(db)
    db.commit()
    db.execute("DELETE FROM bg_gochara_citation_resolution WHERE constant_name='SADE_SATI_BPHS_71'")
    db.commit()
    instance.run(context(db))
    db.rollback()
    assert db.execute("SELECT COUNT(*) AS n FROM bg_gochara_citation_resolution").fetchone()["n"] == 13


def test_dry_run_does_not_replace_existing_rows(db):
    instance = writer()
    insert_live(db)
    db.execute("DELETE FROM bg_gochara_citation_resolution WHERE constant_name='SADE_SATI_BPHS_71'")
    instance.run(context(db, dry_run=True))
    assert db.execute("SELECT COUNT(*) AS n FROM bg_gochara_citation_resolution").fetchone()["n"] == 13


@pytest.mark.parametrize("damage", ["rename", "invent_chunk", "missing_row"])
def test_sealed_oracle_rejects_seed_mutations(db, monkeypatch, damage):
    instance = writer()
    from brahmagyan import l0_gochara_citation_resolution as module
    mutant = copy.deepcopy(module.ROWS)
    if damage == "rename":
        mutant[0]["constant_name"] = "INVENTED_CONSTANT"
    elif damage == "invent_chunk":
        mutant[0].update(chunk_id="invented_chunk", status="resolved")
    else:
        mutant.pop()
    monkeypatch.setattr(module, "ROWS", mutant)
    instance.run(context(db))
    assert next(iter(db.execute(sealed_sql()).fetchone().values())) is False


def test_migration_makes_exactly_one_asset_plannable_and_count_truthful(db):
    instance = writer()
    instance.run(context(db))
    db.commit()
    assert MIGRATION.is_file(), "registry migration is required alongside the writer"
    sql = MIGRATION.read_text()
    db.execute(sql)
    db.execute(sql)  # applied twice: registry update remains idempotent
    row = db.execute("SELECT * FROM asset_registry WHERE asset_id=%s", (ASSET,)).fetchone()
    assert row["has_writer"] is True
    assert next(iter(db.execute(row["count_sql"]).fetchone().values())) == 14
    assert db.execute("SELECT asset_id FROM asset_registry WHERE is_active AND has_writer").fetchall() == [{"asset_id": ASSET}]
    assert db.execute("SELECT has_writer FROM asset_registry WHERE asset_id='bg_sarvatobhadra_grid'").fetchone()["has_writer"] is False


def test_migration_refuses_a_missing_registry_contract(db):
    assert MIGRATION.is_file(), "registry migration is required alongside the writer"
    db.execute("DELETE FROM asset_registry WHERE asset_id=%s", (ASSET,))
    db.commit()
    with pytest.raises(psycopg.errors.RaiseException, match="citation registry contract"):
        db.execute(MIGRATION.read_text())
