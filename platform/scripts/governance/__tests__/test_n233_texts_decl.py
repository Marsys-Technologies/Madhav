"""test_n233_texts_decl.py: the prose declaration of bg_texts accounts for every text column its writer writes (SS ruling N-233, task T4, declarations 1.62.0).

The final census read Narr.agree FAIL on bg_texts: twelve text columns of its two produced tables were open (classical_text_chunks.content_en / content_sha256 / tradition_school / verse_ref and
classical_texts.author / license / school / source_edition / text_id / title_en / title_sa / tradition). The writer composes no narration; it binds source text and registry metadata. The declaration now says
exactly what each column is, with the strongest CHECKED form the engine has for it:

  classical_texts   text_id : identifier (UNIQUE) ; title_en / title_sa / author / school / tradition / license : closed to the literals of the committed TEXTS registry (values_from, by AST) ;
                    source_edition : the 15 edition lines pinned as a curated corpus (count + sha256 digest, seed TEXTS)
  classical_text_chunks   verse_ref : templated PG{int}:C{int} ; tradition_school : templated {tradition}:{school} over the registry's closed sets ;
                    content_sha256 : templated {hex64} (a NEW checked placeholder class, prose_forms.TEMPLATE_CLASSES["hex64"]) ; content_en : transcription (cut verbatim from the pinned source file)

The REAL `TextsWriter.run` runs on a throw-away PostgreSQL with the real DDL, with only its three external inputs replaced (the GCS download, the PDF page extraction and the embedding call; a `vector` domain stands
in for pgvector), so the chunk records are built by the writer's own code. The engine's `_measure_prose` then reads the six cells, and every closure has a mutation that must turn the reading red.
content_en is a declared transcription, not a checked closure: nothing in the engine reads 10,651 chunks of free text, and this file does not pretend otherwise.
"""
from __future__ import annotations

import hashlib
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
import prose_forms as pf  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET  # noqa: E402

AID = "bg_texts"
TC, TT = "classical_text_chunks", "classical_texts"
DECLS = ac.load_asset_declarations()
RUN = "11111111-1111-4111-8111-111111111111"
PN = DECLS[AID]["prose_none"]


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _closed(col):
    return next(c for c in PN["closed_columns"] if c["column"] == col and c.get("table") == TT)


def _tm(col):
    return next(c for c in PN["templated_columns"] if c["column"] == col and c.get("table") == TC)


def test_the_declaration_is_sound_and_the_new_class_is_a_real_regex_valid_in_both_engines():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer" and PN["column_scope"] == "written"
    assert sorted(c["column"] for c in PN["closed_columns"]) == ["author", "license", "school", "title_en", "title_sa", "tradition"]
    assert sorted(t["column"] for t in PN["templated_columns"]) == ["content_sha256", "tradition_school", "verse_ref"]
    assert [(c["table"], c["column"]) for c in e["curated_corpus"]] == [(TT, "source_edition")]
    assert {"content_en", "content_sa", "translator", "text_id"} <= {c["column"] for c in PN["transcription_columns"]}
    rx = pf.TEMPLATE_CLASSES["hex64"]
    assert re.fullmatch(rx, hashlib.sha256(b"x").hexdigest()) and not re.fullmatch(rx, "A" * 64) and not re.fullmatch(rx, "a" * 63) and not re.fullmatch(rx, "a" * 65)
    assert "\\" not in rx                                                                                      # the engine's own rule: no backslash, so Python re and PostgreSQL ARE agree


def test_the_declared_closures_equal_the_committed_registry():
    from brahmagyan.l0_texts import TEXTS
    assert len(TEXTS) == 15
    for col in ("title_en", "title_sa", "author", "school", "tradition", "license"):
        got = _closed(col).get("values") if col == "title_sa" else pf.resolve_values_from(ac.ROOT, _closed(col)["values_from"])      # one entry has no Sanskrit title, so that vocabulary is listed (values_from reads strings only)
        assert got == sorted({t[col] for t in TEXTS if t.get(col)}), col
    cc = DECLS[AID]["curated_corpus"][0]
    assert cc["count"] == 15 and cc["digest"] == pf.corpus_digest([t["source_edition"] for t in TEXTS])
    assert sorted(_tm("tradition_school")["placeholders"]["s"]["values"]) == sorted({t["school"] for t in TEXTS}) and _tm("tradition_school")["placeholders"]["t"]["values"] == ["vedic"]


def test_the_templates_match_the_writers_own_f_strings():
    src = (ac.ROOT / "platform/python-sidecar/pipeline/orchestrator/writers/bg_texts.py").read_text(encoding="utf-8")
    assert 'return f"PG{page}:C{idx}"' in src and "f\"{text.get('tradition','')}:{text.get('school','')}\"" in src and "hashlib.sha256(" in src and ".hexdigest()" in src


# ───────────────────────── the REAL writer on a throw-away database ─────────────────────────

@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    pg = disposable_pg
    for t in (TC, TT):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.psql(pg, "DROP DOMAIN IF EXISTS vector CASCADE")
    fs.psql(pg, "CREATE DOMAIN vector AS bytea")                                     # stands in for pgvector (a non-text type, as the real one): the writer casts '[..]'::vector
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_texts.sql", TT))
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_texts.sql", TC))
    fs.psql(pg, f"ALTER TABLE {TC} ADD COLUMN IF NOT EXISTS translator text, ADD COLUMN IF NOT EXISTS tradition_school text, ADD COLUMN IF NOT EXISTS embedding vector, ADD COLUMN IF NOT EXISTS content_sha256 text")
    import pipeline.orchestrator.writers.bg_texts as B
    from pipeline.orchestrator.writers import ContextSpec

    def pages(path):
        dev = "अआइईउ " * 12                                      # Devanagari: passes the Hindi OCR gate of the two sa+hi texts
        return [f"{path} page {i} of the fixture text. " * 3 + "\n\n" + dev + "\n\n" + f"A second paragraph on page {i} that is long enough to be kept. " * 2 for i in range(1, 4)]
    mp = pytest.MonkeyPatch()
    mp.setattr(B, "_download_gcs", lambda p: p.encode())
    mp.setattr(B, "_extract_pages", lambda b: pages(b.decode()))
    mp.setattr(B, "_embed_batch", lambda texts: [[0.0, 0.5, 1.0] for _ in texts])
    mp.setattr(B, "_fetch_sarvartha_djvu", lambda: None)
    mp.setattr(B, "_fetch_patel_djvu_from_gcs", lambda: None)
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    try:
        res = B.TextsWriter().run(ContextSpec(asset_id=AID, build_id=RUN, db_conn=conn, config={}))
    finally:
        conn.close()
        mp.undo()
    assert res.rows_inserted >= 15 * 3, res.notes
    yield pg
    for t in (TC, TT):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.psql(pg, "DROP DOMAIN IF EXISTS vector CASCADE")


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], TC, [TC, TT], decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_the_two_tables_read_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert b["open"] == [] and b["contradicted"] == [] and b["column_scope"] == "written"
    f = b["forms"]
    assert sorted(x["column"] for x in f["templated"]) == ["content_sha256", "tradition_school", "verse_ref"] and [x["column"] for x in f["curated"]] == ["source_edition"]
    assert {f"{TT}.{c}" for c in ("title_en", "author", "license")} <= {f"{x['table']}.{x['column']}" for x in b["closed"]}


def test_REAL_WRITER_the_stored_rows_are_what_the_declaration_says(db):
    from brahmagyan.l0_texts import TEXTS
    rows = json.loads(fs.psql(db, f"SELECT json_agg(json_build_object('t', text_id, 'a', author, 'e', source_edition)) FROM {TT}"))
    assert {r["t"] for r in rows} == {t["text_id"] for t in TEXTS} and {r["e"] for r in rows} == {t["source_edition"] for t in TEXTS}
    bad_sha = fs.psql(db, f"SELECT count(*) FROM {TC} WHERE content_sha256 !~ '^[0-9a-f]{{64}}$'").strip()
    bad_ref = fs.psql(db, f"SELECT count(*) FROM {TC} WHERE verse_ref !~ '^PG[0-9]+:C[0-9]+$'").strip()
    ts = sorted(fs.psql(db, f"SELECT DISTINCT tradition_school FROM {TC}").split())
    assert (bad_sha, bad_ref) == ("0", "0") and set(ts) <= {f"vedic:{s}" for s in {t["school"] for t in TEXTS}} and len(ts) >= 4
    one = json.loads(fs.psql(db, f"SELECT row_to_json(c) FROM (SELECT text_id, content_en, content_sha256 FROM {TC} ORDER BY chunk_id LIMIT 1) c"))
    assert one["content_sha256"] == hashlib.sha256(f"{one['text_id']}::{one['content_en']}".encode()).hexdigest()


# (table, pk columns, column, new SQL value, needle)
MUTS = [
    (TC, ["chunk_id"], "verse_ref", "'Chapter 3, verse 7'", "verse_ref"),
    (TC, ["chunk_id"], "content_sha256", "'not-a-digest'", "content_sha256"),
    (TC, ["chunk_id"], "content_sha256", "upper(content_sha256)", "content_sha256"),
    (TC, ["chunk_id"], "tradition_school", "'vedic:western'", "tradition_school"),
    (TT, ["text_id"], "author", "'A new author'", "author"),
    (TT, ["text_id"], "license", "'proprietary'", "license"),
    (TT, ["text_id"], "title_en", "'A retitled work'", "title_en"),
    (TT, ["text_id"], "school", "'kp'", "school"),
    (TT, ["text_id"], "tradition", "'western'", "tradition"),
    (TT, ["text_id"], "source_edition", "'A different edition line typed later'", "source_edition"),
]


@pytest.mark.parametrize("table,pk,col,newv,needle", MUTS)
def test_REAL_WRITER_MUTATION_a_value_outside_its_form_is_a_FAIL(db, monkeypatch, table, pk, col, newv, needle):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:500]
        assert all(got[c]["v"] == NO_DET for c in fs.CELLS if c != "Narr.agree")
    fs.mutate_and_restore(db, table, pk, col, newv, "true", check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_an_extra_registry_row_breaks_the_equal_corpus_pin(db, monkeypatch):
    fs.psql(db, f"INSERT INTO {TT} (text_id, title_en, school, tradition, license, source_edition) SELECT 'zz_extra', title_en, school, tradition, license, 'an edition line no registry entry holds' FROM {TT} LIMIT 1")
    try:
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "source_edition" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db, f"DELETE FROM {TT} WHERE text_id = 'zz_extra'")
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_dropping_a_declared_form_is_a_FAIL_naming_the_column(db, monkeypatch):
    d = _own()
    d["prose_none"]["transcription_columns"] = [c for c in d["prose_none"]["transcription_columns"] if c["column"] != "content_en"]
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and f"{TC}.content_en" in got["Narr.agree"]["measured"]
    d = _own()
    d["prose_none"]["templated_columns"] = [t for t in d["prose_none"]["templated_columns"] if t["column"] != "content_sha256"]
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and f"{TC}.content_sha256" in got["Narr.agree"]["measured"]
    d = _own()
    d["prose_none"]["identifier_columns"] = [c for c in d["prose_none"]["identifier_columns"] if not (c.get("table") == TT and c["column"] == "text_id")]
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and f"{TT}.text_id" in got["Narr.agree"]["measured"]
