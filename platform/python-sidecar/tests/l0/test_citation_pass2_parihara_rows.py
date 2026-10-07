"""CITATION-PASS2 side effect on bg_parihara_rules (decision OS-2026-10-05-CITATIONS, SS ruling 2026-10-05).

bg_parihara_rules reads brahma_dosha_catalog.classical_citations (its `_DOSHA_QUERY` keeps doshas whose citations hold a real text_id). Citation pass 2 verified a K1 source for the DEFINITION of 14 doshas;
nobody checked that the same passage states each cancellation condition, so those 14 are DECLARED out of the graph (PARIHARA_K1_SOURCE_CHECK_PENDING) and K1_ANALOGUE objects never qualify:
the parihara row set stays IDENTICAL, migration 703's pin (60 rows + a content hash) is untouched, no reseal. The 27 would-be rows are a fix-list item (ACHARYA/PARIHARA_27_PENDING.tsv).
Two tests, on a DISPOSABLE PostgreSQL with the REAL query and row builder:
  * the row set and its content hash are IDENTICAL before / after the overlay (60 rows);
  * the declared list equals the doshas the overlay newly K1-sources (derived here, not copied): a dosha that gets a K1 source without being listed fails this test.
"""
from __future__ import annotations

import hashlib
import json

import psycopg
from psycopg.rows import dict_row

from brahmagyan import l0_doshas
from pipeline.orchestrator.writers import bg_parihara_rules as P
from tests.pg_disposable import new_db, psql, pg  # noqa: F401  (pg is a fixture)

DDL = """
CREATE TABLE classical_texts(text_id text primary key, title_en text);
CREATE TABLE brahma_dosha_catalog(canonical_id text primary key, name_en text, category text, cancellation_conditions jsonb, classical_citations jsonb);
"""

def _rows(port, doshas):
    db = new_db(port)
    assert psql(port, db, DDL).returncode == 0
    conn = psycopg.connect(f"host=127.0.0.1 port={port} user=postgres dbname={db}", row_factory=dict_row)
    try:
        with conn.cursor() as c:
            for t in ("phaladeepika", "bphs", "muhurta_chintamani", "jataka_parijata", "saravali", "classical_tradition"):
                c.execute("INSERT INTO classical_texts VALUES (%s, %s)", (t, t.title()))
            for d in doshas:
                c.execute("INSERT INTO brahma_dosha_catalog VALUES (%s,%s,%s,%s::jsonb,%s::jsonb)",
                          (d["canonical_id"], d["name_en"], d["category"], json.dumps(d.get("cancellation_conditions") or {}), json.dumps(d.get("classical_citations") or [])))
        conn.commit()
        rows = P.fetch_parihara_rows(conn, "citation-pass2-test")
    finally:
        conn.close()
    return sorted((r["dosha_canonical_id"], r["cancellation_index"], r["cancellation_condition_text"], r["source_text_id"], r["source_chapter"], r["source_citation"], r["net_standing"], r["scope"]) for r in rows)


def _digest(rows) -> str:
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _real(d) -> bool:
    return any(c.get("text_id") and c["text_id"] != "classical_tradition" for c in (d.get("classical_citations") or []))


def test_parihara_row_set_and_content_hash_are_identical_before_and_after_the_overlay(pg):
    before = _rows(pg, l0_doshas.DOSHAS)
    after = _rows(pg, l0_doshas.pass2_doshas())
    assert len(before) == 60                                              # migration 703's pin
    assert len(after) == 60 and after == before and _digest(after) == _digest(before)


def test_the_declared_pending_list_is_exactly_the_doshas_the_overlay_newly_k1_sources():
    authored = {d["canonical_id"]: d for d in l0_doshas.DOSHAS}
    derived = set()
    for d in l0_doshas.pass2_doshas():
        old = authored.get(d["canonical_id"])
        has_k1 = any(c.get("kind") == "K1" for c in d["classical_citations"])
        if has_k1 and d.get("cancellation_conditions") and (old is None or not _real(old)):
            derived.add(d["canonical_id"])
    assert len(derived) == 14
    assert set(P.PARIHARA_K1_SOURCE_CHECK_PENDING) == derived             # fails if a dosha gets K1-sourced without being listed (or stays listed after losing it)


def test_pending_doshas_and_k1_analogue_never_become_parihara_rows(pg):
    doshas = [{"canonical_id": "only_analogue", "name_en": "x", "category": "c", "cancellation_conditions": {"bhanga": ["a"]},
               "classical_citations": [{"kind": "K2", "decision_id": "d", "label": "l"}, {"kind": "K1_ANALOGUE", "text_id": "bphs", "locus": "PG1:C1", "human_locus": "h", "excerpt": "e"}]},
              {"canonical_id": "k1_then_analogue", "name_en": "y", "category": "c", "cancellation_conditions": {"bhanga": ["b"]},
               "classical_citations": [{"kind": "K1_ANALOGUE", "text_id": "saravali", "locus": "PG1:C1", "human_locus": "h", "excerpt": "e"},
                                       {"kind": "K1", "text_id": "phaladeepika", "locus": "PG2:C1", "human_locus": "h", "excerpt": "e"}]},
              {"canonical_id": "nadi_dosha", "name_en": "z", "category": "c", "cancellation_conditions": {"bhanga": ["c"]},
               "classical_citations": [{"kind": "K1", "text_id": "muhurta_chintamani", "locus": "PG96:C1", "human_locus": "h", "excerpt": "e"}]}]
    rows = _rows(pg, doshas)
    assert {r[0] for r in rows} == {"k1_then_analogue"}                   # nadi_dosha is declared pending; only_analogue has no non-analogue text_id
    assert {r[3] for r in rows} == {"phaladeepika"}                       # the source is the K1 object, not the analogue listed first
