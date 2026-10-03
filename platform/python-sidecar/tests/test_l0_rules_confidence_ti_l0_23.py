"""TI-L0-23 (SS Q9 / Q22): bg_rules stores `confidence` as NULL (not scored), documented; no
backfill; `ON CONFLICT (rule_id) DO NOTHING` is kept (the delete-before-reseed already
reproduces every id); concept ids come from the pattern families exactly as before.

Production dry run behind this PR (reader-only, 2026-10-03, evidence ti23_rules_dryrun.json): the
CURRENT extractor over the live 10,651 chunks yields exactly the live 3,002 rows - same rule_ids,
same every column - so a rebuild changes ONE column: `confidence` 3,002 cells (0.6 x2, 0.8 x230,
1.0 x2770) -> NULL. yoga_canonical_id stays 17 populated; dasha_system_id stays 0 (the dasha_rule
pattern matches nothing in the corpus, so no source exists: honest NULL).

Proves: (1) static - every yielded rule has confidence None and a quality_score equal to the
documented 5-criterion score; the reason is stated; the served routers rank on quality_score so
the order of results is unchanged by the NULLs. (2) real PostgreSQL (env-gated): without the
relaxing migration the writer refuses BEFORE deleting anything; with it, the rebuild keeps every
rule_id and every column except confidence, which becomes NULL, and a rerun is a no-op.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from brahmagyan import l0_rules as R
from tests._l0d_pg import requires_pg, scratch_schema

SIDECAR = Path(__file__).resolve().parents[1]

CHUNKS = [
    {"id": "11111111-1111-1111-1111-111111111111", "text_id": "bphs", "verse_ref": "BPHS 1.1",
     "content_en": "Mars in the 10th house gives Ruchaka and confers great authority and command over others."},
    {"id": "22222222-2222-2222-2222-222222222222", "text_id": "bphs", "verse_ref": "BPHS 1.2",
     "content_en": "Mars in the 10th house gives great authority and command over others."},
    {"id": "33333333-3333-3333-3333-333333333333", "text_id": "phaladeepika", "verse_ref": "PG100:C1",
     "content_en": "Saturn in the 7th house causes delay in marriage and much sorrow to the native."},
]


def _rows():
    out = []
    for ch in CHUNKS:
        out += list(R.extract_rules_from_chunk(ch, valid_text_ids={"bphs", "phaladeepika"}))
    return out


# ── 1. static ────────────────────────────────────────────────────────────────

def test_every_yielded_rule_has_null_confidence_and_a_real_quality_score():
    rows = _rows()
    assert len(rows) >= 3
    for r in rows:
        assert r["confidence"] is None
        assert isinstance(r["quality_score"], float) and 0.6 <= r["quality_score"] <= 1.0
        assert r["_quality"] == r["quality_score"]


def test_the_reason_is_documented_and_names_the_column_that_carries_the_score():
    why = R.CONFIDENCE_NOT_SCORED_REASON
    assert "NULL by design" in why and "quality_score" in why and "SS Q9" in why


def test_rule_ids_and_concept_ids_are_unchanged_by_the_confidence_change():
    rows = _rows()
    ruchaka = [r for r in rows if r["yoga_canonical_id"] == "ruchaka"]
    assert ruchaka and all(r["dasha_system_id"] is None for r in rows)
    # rule_id is content-based (text_id|verse_ref|antecedent+prediction): confidence is not an input
    a = R._make_rule_id("bphs", "BPHS 1.1", [{"planet": "mars"}], {"result": "x y z"})
    assert str(a) == str(R._make_rule_id("bphs", "BPHS 1.1", [{"planet": "mars"}], {"result": "x y z"}))


def test_on_conflict_do_nothing_is_kept():
    import inspect
    src = inspect.getsource(R.seed_rules)
    assert "ON CONFLICT (rule_id) DO NOTHING" in src and "DO UPDATE" not in src


def test_served_routers_rank_on_quality_score_not_the_nulled_column():
    src = (SIDECAR / "routers" / "sutravali.py").read_text(encoding="utf-8")
    orders = re.findall(r"ORDER BY[^\n\"]*", src)
    assert orders and not any("confidence" in o for o in orders), orders
    assert sum("quality_score DESC" in o for o in orders) == 5


# ── 2. real PostgreSQL ───────────────────────────────────────────────────────

def ddl(confidence_nullable: bool) -> str:
    nn = "" if confidence_nullable else "NOT NULL DEFAULT 0.0"
    return f"""
CREATE TABLE classical_text_chunks (id uuid PRIMARY KEY, text_id text NOT NULL, verse_ref text, chapter integer, verse_start integer, content_en text);
CREATE TABLE brahma_dasha_systems (canonical_id text PRIMARY KEY);
CREATE TABLE brahma_yoga_catalog (canonical_id text PRIMARY KEY);
CREATE TABLE sutravali_rules (
  rule_id uuid PRIMARY KEY, text_id text NOT NULL, verse_ref text, antecedent_jsonb jsonb, predicate_jsonb jsonb,
  prediction_jsonb jsonb, confidence numeric {nn} CONSTRAINT sutravali_rules_confidence_check CHECK (confidence >= 0 AND confidence <= 1),
  extracted_by text, extraction_pass_log jsonb, created_at timestamptz, quality_score numeric NOT NULL DEFAULT 0.0,
  yoga_canonical_id text, dasha_system_id text, transit_marker boolean DEFAULT false);
INSERT INTO brahma_yoga_catalog VALUES ('ruchaka'); INSERT INTO brahma_dasha_systems VALUES ('vimshottari');
"""


def _load_chunks(conn):
    for i, ch in enumerate(CHUNKS):
        conn.execute("INSERT INTO classical_text_chunks(id,text_id,verse_ref,chapter,verse_start,content_en) VALUES (%s,%s,%s,%s,%s,%s)",
                     (ch["id"], ch["text_id"], ch["verse_ref"], 1, i, ch["content_en"]))
    conn.commit()


SEL = "SELECT rule_id::text,text_id,verse_ref,antecedent_jsonb,predicate_jsonb,prediction_jsonb,extracted_by,quality_score,yoga_canonical_id,dasha_system_id,transit_marker FROM sutravali_rules ORDER BY rule_id"


@requires_pg
def test_real_writer_refuses_before_deleting_when_the_migration_is_not_applied():
    with scratch_schema(ddl(False)) as conn:
        _load_chunks(conn)
        conn.execute("INSERT INTO sutravali_rules(rule_id,text_id,verse_ref,confidence,extracted_by,quality_score) "
                     "VALUES ('99999999-9999-9999-9999-999999999999','bphs','x',0.8,%s,0.8)", (R.EXTRACTED_BY,))
        conn.commit()
        with pytest.raises(RuntimeError, match="confidence-nullable migration"):
            R.seed_rules(conn, autocommit=False)
        conn.rollback()
        assert conn.execute("SELECT count(*) AS n FROM sutravali_rules").fetchone()["n"] == 1, "nothing was deleted"


@requires_pg
def test_real_writer_nulls_only_the_confidence_column_and_is_idempotent():
    with scratch_schema(ddl(True)) as conn:
        _load_chunks(conn)
        R.seed_rules(conn, autocommit=False)
        conn.commit()
        # live shape: confidence = quality_score on every row
        conn.execute("UPDATE sutravali_rules SET confidence = quality_score")
        conn.commit()
        n = conn.execute("SELECT count(*) AS n FROM sutravali_rules").fetchone()["n"]
        assert n >= 3
        before = list(conn.execute(SEL))
        assert conn.execute("SELECT count(*) AS n FROM sutravali_rules WHERE confidence IS DISTINCT FROM quality_score").fetchone()["n"] == 0

        out = R.seed_rules(conn, autocommit=False)
        conn.commit()
        assert out["rows_inserted"] == n
        assert list(conn.execute(SEL)) == before, "every column except confidence is byte-identical, ids included"
        assert conn.execute("SELECT count(*) AS n FROM sutravali_rules WHERE confidence IS NULL").fetchone()["n"] == n
        snap = list(conn.execute("SELECT * FROM sutravali_rules ORDER BY rule_id"))
        R.seed_rules(conn, autocommit=False)
        conn.commit()
        rows2 = list(conn.execute("SELECT * FROM sutravali_rules ORDER BY rule_id"))
        strip = lambda rows: [{k: v for k, v in r.items() if k != "created_at"} for r in rows]
        assert strip(rows2) == strip(snap)
