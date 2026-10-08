"""test_formgap_decl_compendium.py: bg_compendium_index (a detector-limit asset of SS N-191, no new form): its declaration and the real writer on the real DDL.

The writer builds the `significance` sentences in a helper (`_build_desired_rows`: two f-strings over the text id, chapter / topic and the passage count) and `executemany`s the tuples; the old scan could not
follow `a, b = helper()` rows built by `.append((...))` and read the write path as unresolved. The scan now follows them (tests: test_formgap_scan_limits.py) and reads the two paths CLEAN. Here the declaration
is measured on rows the REAL writer builds on a throw-away PostgreSQL (migrations 176 and 178, ws2 text tables): Narr.agree PASS, both Null cells PASS (clean scan, clean data), and a blank / placeholder
significance or a changed write path turns the reading red. The evidence pointer cites the right DDL (migration 176, line 85), checked here against the file.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET, PARTIAL, PASS  # noqa: E402

AID = "bg_compendium_index"
T = "brahma_compendium_index"
DECLS = ac.load_asset_declarations()
RUN = "11111111-1111-4111-8111-111111111111"
NULLS = ("Null.schema_default", "Null.blank_rows")


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def test_the_evidence_pointer_cites_the_real_ddl_of_the_significance_column():
    e = DECLS[AID]
    txt = e["evidence"]["prose_fields"]
    assert "migrations/001_baseline.sql" not in txt and "176_l0_phase_alpha_new_content_tables.sql, line 85" in txt
    lines = (fs.SMIG / "176_l0_phase_alpha_new_content_tables.sql").read_text(encoding="utf-8").splitlines()
    assert lines[84].split()[0] == "significance" and lines[73].startswith("CREATE TABLE IF NOT EXISTS brahma_compendium_index")           # line 85 is the column, inside that CREATE TABLE
    assert e["prose_fields"] == ["significance"] and e["lint_none"] and e["fidelity_tests"][0]["covers"] == ["significance"]


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
    import brahmagyan.l0_reference as R
    pg = disposable_pg
    fs.drop_tables(pg, T, "classical_text_chunks", "classical_texts", "reference_topic_tags")
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_texts.sql", "classical_texts"))
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_texts.sql", "classical_text_chunks"))
    fs.psql(pg, "ALTER TABLE classical_text_chunks ADD COLUMN IF NOT EXISTS topic_tag TEXT")                                         # migration 177
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "178_l0_phase_alpha_reference_tables.sql", "reference_topic_tags"))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "176_l0_phase_alpha_new_content_tables.sql", T))
    fs.psql(pg, "CREATE UNIQUE INDEX IF NOT EXISTS compendium_dedup_idx ON brahma_compendium_index (text_id, COALESCE(chapter_num,-1), COALESCE(topic_id,''))")      # the owner's migration; the writer only VERIFIES it since main 18473f081
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO reference_topic_tags (canonical_id, name, category, description, example_chunks) VALUES (%s, %s, %s, %s, %s)",
                        [(t["canonical_id"], t["name"], t["category"], t["description"], Jsonb(t["example_chunks"])) for t in R.TOPIC_TAGS])
    for t in ("bphs", "saravali"):
        fs.psql(pg, f"INSERT INTO classical_texts (text_id, title_en, school, tradition, license) VALUES ('{t}', '{t}', 'parashari', 'vedic', 'public_domain')")
    rows = [("bphs", 1, 1, "sun_in_1st", "The Sun in the first house gives vigour."), ("bphs", 1, 2, "moon_in_4th", "The Moon in the fourth gives comfort."), ("bphs", 2, 1, None, "A chapter two passage."),
            ("saravali", 5, 1, "sun_in_1st", "Saravali on the Sun.")]
    for i, (t, ch, v, tag, txt) in enumerate(rows):
        fs.psql(pg, f"INSERT INTO classical_text_chunks (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end, content_en, source_citation, topic_tag) VALUES "
                    f"('{t}', '{t}_{i}', 'CH{ch}:V{v}', {ch}, {v}, {v}, '{txt}', 'fixture', {'NULL' if tag is None else repr(tag)})")
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_compendium_index import CompendiumIndexWriter
    res = CompendiumIndexWriter().run(ContextSpec(asset_id=AID, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert res.rows_inserted == 6, res.notes                                      # 3 chapters (bphs 1, bphs 2, saravali 5) + 3 topics (bphs sun_in_1st, bphs moon_in_4th, saravali sun_in_1st)
    yield pg
    fs.drop_tables(pg, T, "classical_text_chunks", "classical_texts", "reference_topic_tags")


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T, [T], decl or _own(), registry=dict(has_writer=True, count_sql="SELECT COUNT(*) FROM brahma_compendium_index"))


def test_REAL_WRITER_the_significance_sentences_are_the_two_f_strings_over_the_passage_count(db):
    sig = sorted(x for x in fs.psql(db, f"SELECT significance FROM {T}").split("\n") if x)
    assert sig == sorted(["bphs chapter 1: 2 passage(s)", "bphs chapter 2: 1 passage(s)", "saravali chapter 5: 1 passage(s)", "bphs covers sun_in_1st in 1 passage(s)", "bphs covers moon_in_4th in 1 passage(s)",
                          "saravali covers sun_in_1st in 1 passage(s)"])


def test_REAL_WRITER_the_scan_reads_both_write_paths_clean_and_the_null_cells_read_pass(db, monkeypatch):
    got = _m(db, monkeypatch)
    assert got["Narr.agree"]["v"] == PASS
    for c in NULLS:
        assert got[c]["v"] == PASS and "writer scan CLEAN" in got[c]["measured"] and "2 write path(s)" in got[c]["measured"], (c, got[c]["measured"][-300:])
    assert got["Narr.lint"]["v"] == NA


@pytest.mark.parametrize("bad", ["", "tbd", "n/a"])
def test_REAL_WRITER_MUTATION_a_blank_or_placeholder_significance_in_the_table_keeps_the_cell_from_passing(db, monkeypatch, bad):
    def check():
        got = _m(db, monkeypatch)
        assert got["Null.blank_rows"]["v"] == FAIL, got["Null.blank_rows"]["measured"][:300]
    fs.mutate_and_restore(db, T, "index_id", "significance", f"'{bad}'", "true", check)
    assert _m(db, monkeypatch)["Null.blank_rows"]["v"] == PASS


def test_REAL_WRITER_MUTATION_a_writer_that_writes_a_constant_sentence_loses_the_clean_scan(db, monkeypatch, tmp_path):
    """The refinement must not hide a constant write: the same helper-built rows with a literal sentence in the tuple are a constant_write finding."""
    import ast
    sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))
    from pipeline.orchestrator.writers import bg_compendium_index as mod
    src = pathlib.Path(mod.__file__).read_text(encoding="utf-8").replace('f"{text_id} chapter {chapter_num}: {len(rows)} passage(s)"', '"A fixed chapter sentence"')
    assert "A fixed chapter sentence" in src
    tree = ast.parse(src)
    units = [dict(rel="pipeline/orchestrator/writers/bg_compendium_index.py", path=pathlib.Path("bg_compendium_index.py"), tree=tree, nodes=[tree], hop=0, via="bg_compendium_index.py")]
    ws = ac._lint_module("writer_literal_scan").scan(units, ["significance"], {"significance": [T]}, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field, beyond=())
    assert ws["v"] != PASS and any(p["kind"] == "constant_write" for p in ws["problems"]), ws["measured"][:300]
