"""ROWS2: bg_ontology reports the rows of the entity classes it OWNS; bg_texts' two-table figure is pinned to its declaration.

Production run 2af5c8a2 recorded bg_ontology rows_written=729 against 728 live rows and bg_texts rows_written=10,667 against a
registry count_sql of 10,651. Causes (see POST/ROWS2.md):

* bg_ontology: the count was the WHOLE of ``brahma_ontology``, taken when bg_ontology finished. bg_yogas, bg_doshas and
  bg_dasha_systems all ``depends_on`` bg_ontology and replace their own entity classes (yoga, dosha, dasha_system) of the same table
  afterwards, so the whole-table figure at count time (729) was not the figure the run left behind (728). The writer's own classes are
  stable (409). Fixed by counting only the thirteen classes the seeder owns.
* bg_texts: NOT a writer defect. 10,667 = classical_text_chunks 10,651 + classical_texts 16, exactly the asset's declared
  produced_tables; the census already reads PASS for it ("rows_written=10667 = live=10667 (declared produced-table set ...)").
  Only the registry count_sql names the chunks alone. The tests below pin the writer's statement to the declaration so the two
  cannot drift apart.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

from pipeline.orchestrator.writers._rows_present import present_count
from pipeline.orchestrator.writers.tests.test_wfix_a_rows_present import CountingConn, _ctx

ROOT = Path(__file__).resolve().parents[5]      # platform/
DECLARATIONS = ROOT / "scripts" / "governance" / "asset_declarations.json"


def _owned():
    from brahmagyan.l0_ontology import CO_WRITER_ENTITY_CLASSES, ENTITIES, ONTOLOGY_OWNED_ENTITY_CLASSES
    return ONTOLOGY_OWNED_ENTITY_CLASSES, CO_WRITER_ENTITY_CLASSES, ENTITIES


def _sql_classes(sql: str) -> list[str]:
    return re.findall(r"'([a-z_]+)'", sql)


def test_bg_ontology_counts_only_the_classes_it_owns(monkeypatch):
    from pipeline.orchestrator.writers import bg_ontology

    owned, co_writers, _ = _owned()
    monkeypatch.setattr(bg_ontology, "seed_ontology",
                        lambda *_a, **_k: {"total": 414, "inserted": 0, "skipped": 414, "by_class": {}})
    # the fake answers ONLY a statement scoped to the owned classes; the old whole-table statement is refused
    conn = CountingConn({"FROM brahma_ontology WHERE entity_class IN (": 409})
    result = bg_ontology.OntologyWriter().run(_ctx("bg_ontology", conn))
    assert result.rows_inserted == 409 and result.rows_updated == 0
    assert conn.tables == {"brahma_ontology"} and conn.commits == 0
    assert set(_sql_classes(conn.count_reads[0][0])) == set(owned)
    assert not set(_sql_classes(conn.count_reads[0][0])) & set(co_writers)


def test_the_literal_statement_is_the_seeders_owned_set_and_the_declaration():
    from pipeline.orchestrator.writers import bg_ontology

    owned, _, _ = _owned()
    assert sorted(_sql_classes(bg_ontology.ROWS_PRESENT_SQL)) == sorted(owned)
    decl = json.loads(DECLARATIONS.read_text())["assets"]["bg_ontology"]["produced_tables"]
    assert {t["table"] for t in decl} == {"brahma_ontology"}
    assert all(t["filter"]["column"] == "entity_class" for t in decl)
    assert sorted(t["filter"]["equals"] for t in decl) == sorted(owned)


def test_bg_texts_statement_is_exactly_its_declared_produced_set():
    from pipeline.orchestrator.writers import bg_texts

    decl = json.loads(DECLARATIONS.read_text())["assets"]["bg_texts"]["produced_tables"]
    declared = sorted(t["table"] for t in decl)
    assert declared == ["classical_text_chunks", "classical_texts"]
    assert all(not t.get("filter") for t in decl)
    assert sorted(re.findall(r"count\(\*\) FROM ([a-z_]+)", bg_texts.ROWS_PRESENT_SQL)) == declared


def test_bg_texts_figure_is_chunks_plus_text_rows_by_design():
    """10,667 = 10,651 chunks + 16 text-metadata rows. The +16 against the registry count_sql is the classical_texts table."""
    from pipeline.orchestrator.writers.bg_texts import TextsWriter

    conn = CountingConn({"(SELECT count(*) FROM classical_text_chunks) + (SELECT count(*) FROM classical_texts)": 10_651 + 16,
                         "AS n FROM classical_text_chunks": 10_651},
                        lambda sql, _p: [] if "GROUP BY text_id" in sql else None)
    result = TextsWriter().run(_ctx("bg_texts", conn, config={"rebuild_mode": "metadata_only"}))
    assert result.rows_inserted == 10_667


# -- real Postgres (disposable, loopback-guarded): the co-writers' later reseed must not move the figure -----------------

DSN = os.environ.get("WFIX_A_ROWS_PRESENT_TEST_DATABASE_URL")


@pytest.fixture()
def pg():
    if not DSN:
        pytest.skip("NOT_RUN: WFIX_A_ROWS_PRESENT_TEST_DATABASE_URL is unset (no disposable Postgres in this job)")
    import psycopg
    import psycopg.rows
    sys.path.insert(0, str(ROOT / "python-sidecar" / "tests" / "l3"))
    from _disposable_db_guard import validate_disposable_dsn

    validate_disposable_dsn(DSN, "rows2_test")
    conn = psycopg.connect(DSN, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def test_pg_owned_figure_survives_a_co_writer_reseed(pg):
    from pipeline.orchestrator.writers import bg_ontology

    owned, _co, entities = _owned()
    with pg.cursor() as cur:
        cur.execute("CREATE TEMP TABLE brahma_ontology (entity_class text, canonical_id text, PRIMARY KEY (entity_class, canonical_id))")
        for e in entities:
            if e["entity_class"] in owned:
                cur.execute("INSERT INTO brahma_ontology VALUES (%s, %s)", (e["entity_class"], e["canonical_id"]))
        # co-writer classes as they stood when bg_ontology finished: one row more than the next reseed leaves
        for cls, n in (("yoga", 234), ("dosha", 66), ("dasha_system", 20)):
            cur.execute("INSERT INTO brahma_ontology SELECT %s, %s || g FROM generate_series(1, %s) g", (cls, cls, n))
        cur.execute(bg_ontology.ROWS_PRESENT_SQL)
        at_write = present_count(cur.fetchone())
        cur.execute("SELECT count(*) AS n FROM brahma_ontology")
        whole_at_write = present_count(cur.fetchone())
        # bg_yogas replaces its class afterwards and ends one row short
        cur.execute("DELETE FROM brahma_ontology WHERE entity_class = 'yoga'")
        cur.execute("INSERT INTO brahma_ontology SELECT 'yoga', 'yoga' || g FROM generate_series(1, 233) g")
        cur.execute("SELECT count(*) AS n FROM brahma_ontology")
        whole_after = present_count(cur.fetchone())
        cur.execute(bg_ontology.ROWS_PRESENT_SQL)
        after = present_count(cur.fetchone())
    assert whole_at_write - whole_after == 1          # the +1 the old whole-table count recorded
    assert at_write == after == len([e for e in entities if e["entity_class"] in owned])
