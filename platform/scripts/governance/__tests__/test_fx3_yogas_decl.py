"""test_fx3_yogas_decl.py: the prose declaration of bg_yogas accounts for every open text column its writer writes (SS day-fix FX3, Narr.agree FAIL).

The census read Narr.agree FAIL on bg_yogas: fourteen text columns of its four produced tables were open (brahma_yoga_catalog.category / formation_rule_jsonb / formation_text / name_en / name_sa /
significations_jsonb / significations_text, reference_yogas.category / name_en, brahma_ontology.canonical_name_en / canonical_name_sa / description / source_citation / synonyms). What each one IS:

  * category (catalog and reference list): a CLOSED VOCABULARY. The catalog DDL carries the same six values as a CHECK constraint, the inline tables write one of them and the corpus extractor writes the
    return value of `_infer_category`. Declared closed (CHECKED against the data), not trusted.
  * name_en / name_sa / canonical_name_* / synonyms: labels of a yoga as the inline classical table spells them or as the corpus extractor matched them (base_name + ' Yoga'); transcription.
  * formation_rule_jsonb / formation_text / significations_jsonb / significations_text: the classical rule, clause and result of the source; the one DERIVED sentence is the restatement
    'Structured formation rule: ' + json.dumps(the row's own rule), emitted only when the chunk states no clause. Transcription (declared, NOT checked by the census).
  * description: significations_text[:150]; source_citation: the inline citation or the f-string '{TEXT} Ch.{n} ({verse_ref})' of the chunk row; transcription.

Nothing is invented: the writer (l0_yogas.py) is NOT changed by this declaration. The declared-not-checked columns are backed here by tests of what the REAL `seed_yogas` writes on a throw-away PostgreSQL
with the real DDL: every stored formation / signification clause of a corpus-extracted row is a substring of the corpus chunk it was cut from, or the derived restatement of the row's own rule, or empty;
the AST guard of every text-building expression in l0_yogas.py is test_e6_1_declarations.py::test_bg_yogas_every_text_building_expression_is_a_bound_label_or_pointer_or_not_stored.
"""
from __future__ import annotations

import ast
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
from _formgap_support import NA, FAIL, NO_DET  # noqa: E402

AID = "bg_yogas"
CAT, REF, ONT, SRC, CHK = "brahma_yoga_catalog", "reference_yogas", "brahma_ontology", "brahma_yoga_source_chunks", "classical_text_chunks"
DECLS = ac.load_asset_declarations()
PN = DECLS[AID]["prose_none"]
Y = ac.ROOT / "platform/python-sidecar/brahmagyan/l0_yogas.py"
CLOSED_CATEGORIES = ["aristha", "dhana", "other", "pancha_mahapurusha", "raja", "sannyasa"]
OPEN_COLUMNS = {CAT: ["formation_rule_jsonb", "formation_text", "name_en", "name_sa", "significations_jsonb", "significations_text"],
                REF: ["name_en"], ONT: ["canonical_name_en", "canonical_name_sa", "description", "source_citation", "synonyms"]}


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _closed(table, col):
    return next(c for c in PN["closed_columns"] if c.get("table") == table and c["column"] == col)


def _tc(table, col):
    return next(c for c in PN["transcription_columns"] if c.get("table") == table and c["column"] == col)


# ───────────────────────── the declaration, against the committed source ─────────────────────────

def test_the_declaration_is_sound_and_names_every_column_the_census_found_open():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    for t, cols in OPEN_COLUMNS.items():
        for c in cols:
            assert _tc(t, c)["evidence"].startswith("platform/python-sidecar/brahmagyan/l0_yogas.py:"), (t, c)
            assert "Declared, not checked" in _tc(t, c)["why"]                  # the declaration says what the census does NOT check
    for t in (CAT, REF):
        assert _closed(t, "category")["values"] == CLOSED_CATEGORIES


def test_every_transcription_pointer_lands_on_the_line_that_binds_its_column():
    lines = Y.read_text(encoding="utf-8").splitlines()
    special = {"canonical_name_en": 'y["name_en"]', "canonical_name_sa": 'y["name_sa"]', "synonyms": "_yoga_synonyms",
               "description": 'y["significations_text"][:150]', "source_citation": "_yoga_citation"}
    for t, cols in OPEN_COLUMNS.items():
        for c in cols:
            n = int(_tc(t, c)["evidence"].rsplit(":", 1)[1])
            window = " ".join(lines[n - 4:n + 2])
            key = 'y["name_en"]' if t == REF else special.get(c, f'y["{c}"]')
            if t == ONT:
                key = c                                                          # the ontology INSERT names its own columns (the n150 rule: the pointer line names the column)
            assert key in window, (t, c, n)


def test_the_closed_category_vocabulary_equals_the_ddl_check_and_every_value_the_writer_can_emit():
    ddl = (ac.ROOT / "platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql").read_text(encoding="utf-8")
    check = re.search(r"category\s+TEXT NOT NULL CHECK \(category IN \(([^)]*)\)\)", ddl).group(1)
    assert sorted(re.findall(r"'([a-z_]+)'", check)) == CLOSED_CATEGORIES
    import brahmagyan.l0_yogas as L
    emitted = {y["category"] for y in L.YOGAS_CORE + L.DETECTOR_YOGAS}
    tree = ast.parse(Y.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_infer_category")
    inferred = {r.value.value for r in ast.walk(fn) if isinstance(r, ast.Return) and isinstance(r.value, ast.Constant)}
    lookup = {v[1] for v in L.SARAVALI_YOGA_LOOKUP.values()}                    # the lookup table's own category slot
    assert (emitted | inferred | lookup) <= set(CLOSED_CATEGORIES)
    assert (emitted | inferred) == set(CLOSED_CATEGORIES)


# ───────────────────────── the REAL seeder on a throw-away database ─────────────────────────

CHUNKS = [
    # a chunk that states a formation clause and a result: the extractor cuts both verbatim
    ("11111111-1111-4111-8111-111111111111", "saravali", 27, "PG27:C1",
     "If the Moon is in a kendra from the Sun, Adhiyoga is formed. One born in Adhiyoga yoga will become a king and enjoy wealth."),
    # a chunk that names a yoga but states no clause: the restated structured rule, never an invented sentence
    ("22222222-2222-4222-8222-222222222222", "bphs", 358, "PG358:C1", "The Vajra yoga is named in this passage."),
]


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    pg = disposable_pg
    for t in (SRC, CAT, REF, ONT, CHK):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.psql(pg, f"CREATE TABLE {CHK} (id uuid PRIMARY KEY, text_id text, chapter int, verse_ref text, verse_start int, content_en text, tradition_school text)")
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "176_l0_phase_alpha_new_content_tables.sql", CAT))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "178_l0_phase_alpha_reference_tables.sql", REF))
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_ontology.sql", ONT))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "630_nirmana_l0_wave1_correctness_contract.sql", SRC))
    for cid, tid, ch, vr, txt in CHUNKS:
        fs.psql(pg, f"INSERT INTO {CHK} VALUES ('{cid}', '{tid}', {ch}, '{vr}', 1, '{txt}', 'parashari')")
    import brahmagyan.l0_yogas as L
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    try:
        counts = L.seed_yogas(conn)
    finally:
        conn.close()
    assert counts["catalog_inserted"] >= 148 and counts["extracted_count"] >= 1, counts
    yield pg
    for t in (SRC, CAT, REF, ONT, CHK):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], CAT, [CAT, SRC, REF, ONT], decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_the_four_tables_read_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert b["open"] == [] and b["contradicted"] == []
    cols = set(b["transcription_columns"])
    for t, cs in OPEN_COLUMNS.items():
        for c in cs:
            assert f"{t}.{c}" in cols, (t, c)


# the inline classical sentences, pinned by count and sha256 (computed from the committed constants with prose_forms.corpus_digest). A `curated_corpus` declaration cannot carry these two columns
# (mode `contained` is only for a column declared in prose_fields, and `equal` fails on the corpus-extracted rows), so the pin lives here: editing an inline sentence turns this red.
INLINE_PINS = {"canonical_id": (148, "adb2364005cc33f252c18169abd05af91be662daded2acc27e1f7946c30b5038"),
               "name_sa": (148, "c4c70aa70b723b4eed85f46bc7bd808cb551ee129d4d33e38fd4e5da8cf3f799"),
               "name_en": (148, "dde5efeebb25f81acf73797af488827484137f3b144debdc2e12c3f4972983c3"),
               "formation_text": (148, "37331c4bcc2f70d8d95a3a6e4c86964d5eaf5dcf6ae008922bfbc86ed64754e6"),
               "significations_text": (148, "597c50a1b6c416fe964204a73e2a95e9a296e2326d8fbafd94e82323d0526499")}
COL_OF = {"canonical_id": "id", "name_sa": "na", "name_en": "ne", "formation_text": "ft", "significations_text": "st"}


def _committed(key):
    """The committed inline sentences of one key, read from the SOURCE FILE by AST (prose_forms.resolve_seed_sentences), never from the imported module: a run-time mutation of YOGAS_CORE does not reach it."""
    import prose_forms as pf
    return pf.resolve_seed_sentences(ac.ROOT, {"file": "platform/python-sidecar/brahmagyan/l0_yogas.py", "constants": ["YOGAS_CORE", "DETECTOR_YOGAS"], "key": key})


def test_REAL_WRITER_every_row_is_a_committed_inline_literal_or_a_cut_of_its_chunk_or_the_restated_own_rule_or_empty(db):
    """EVERY catalog row is checked (review of #3346): an inline id must equal the committed YOGAS_CORE / DETECTOR_YOGAS literals; any other row must carry source_chunk and be a cut of that chunk."""
    import brahmagyan.l0_yogas as L
    inline_ids = set(_committed("canonical_id"))                                  # from the committed source text, not the run-time constants
    rows = json.loads(fs.psql(db, f"SELECT json_agg(json_build_object('id', c.canonical_id, 'ft', c.formation_text, 'st', c.significations_text, 'rule', c.formation_rule_jsonb, "
                                  f"'sj', c.significations_jsonb, 'na', c.name_sa, 'ne', c.name_en, 'src', c.significations_jsonb->>'source_chunk', 'desc', o.description, 'ocit', o.source_citation, "
                                  f"'syn', o.synonyms)) FROM {CAT} c JOIN {ONT} o ON o.entity_class = 'yoga' AND o.canonical_id = c.canonical_id"))
    assert len(rows) == int(fs.psql(db, f"SELECT count(*) FROM {CAT}").strip())
    text = {cid: txt for cid, _t, _c, _v, txt in CHUNKS}

    def norm(s):
        return " ".join(s.split())

    n_inline = n_cut = 0
    for r in rows:
        if r["id"] in inline_ids:
            n_inline += 1
        else:
            assert r["src"] in text, ("a row that is neither a committed inline literal nor tagged with a corpus chunk", r["id"])
            chunk = norm(text[r["src"]])
            restated = "Structured formation rule: " + json.dumps(r["rule"], sort_keys=True, ensure_ascii=False)
            assert norm(r["ft"]) in chunk or norm(r["ft"]) == norm(restated), r["id"]
            assert r["st"] == "" or norm(r["st"]) in chunk, r["id"]
            assert r["na"].lower() in r["ne"].lower() and r["ne"].lower().endswith("yoga") and (r["na"].lower() in chunk.lower() or r["na"] in L.SARAVALI_YOGA_LOOKUP), r["id"]       # matched in the chunk text, or a key of the committed lookup table
            assert re.fullmatch(r"[A-Z]+ Ch\.[0-9]+ \(PG[0-9]+:C[0-9]+\)", r["ocit"]), r["ocit"]
            n_cut += 1
        assert r["desc"] is None or (r["st"] != "" and r["desc"] == r["st"][:150]), r["id"]
    # the STORED inline rows equal the committed pins (count + sha256 over the stored values), so a run-time mutation of the seed constants that the writer then stores is caught
    import prose_forms as pf
    stored = [r for r in rows if r["id"] in inline_ids]
    assert n_inline == len(inline_ids) == len(stored) == 148 and n_cut >= 1
    for key, (n, dig) in INLINE_PINS.items():
        vals = [r[COL_OF[key]] for r in stored]
        assert (len(vals), pf.corpus_digest(vals)) == (n, dig), key
    assert any(r["ft"].startswith("Structured formation rule: ") for r in rows)       # the clauseless chunk exercised the derived fallback


@pytest.mark.parametrize("key", sorted(INLINE_PINS))
def test_the_inline_classical_sentences_are_pinned_by_count_and_digest(key):
    import prose_forms as pf
    sents = _committed(key)
    assert (len(sents), pf.corpus_digest(sents)) == INLINE_PINS[key]


def test_the_row_dict_the_extractor_stores_binds_the_bare_locals_only():
    """The AST guard pins what is assigned to the locals; this pins what the row dict STORES: the transcribed values are exactly the bare locals, so no lookup / override can replace them (review of #3346)."""
    tree = ast.parse(Y.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "extract_yogas_from_corpus")
    rowdicts = [n for n in ast.walk(fn) if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "significations_text" for k in n.keys)]
    assert len(rowdicts) == 1
    got = {k.value: ast.unparse(v) for k, v in zip(rowdicts[0].keys, rowdicts[0].values) if isinstance(k, ast.Constant)}
    assert {k: got[k] for k in ("canonical_id", "name_sa", "name_en", "category", "school", "formation_rule_jsonb", "formation_text", "significations_text")} == {
        "canonical_id": "cid", "name_sa": "base_name", "name_en": "name_en", "category": "cat", "school": "school", "formation_rule_jsonb": "formation_rule_jsonb",
        "formation_text": "formation_text", "significations_text": "sig_text"}
    assert got["significations_jsonb"] == "{'gives': [], 'subcategory': derivation, 'source_chunk': chunk_id}"
    assert got["source_citation"] == "f'{text_id.upper()} Ch.{chapter} ({verse_ref})'"
    assert got["classical_citations"] == "[citation]"
    # the same for the values the seeder binds into the INSERTs of all four tables: bare reads of the row dict, nothing else
    seed = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "seed_yogas")
    src = ast.unparse(seed)
    for expr in ("y['name_sa']", "y['name_en']", "y['category']", "y['formation_text']", "y['significations_text']", "y['significations_text'][:150] or None", "_yoga_synonyms(y)", "_yoga_citation(y)"):
        assert expr in src, expr


def test_REAL_WRITER_the_ontology_and_reference_rows_are_the_catalog_labels_unchanged(db):
    bad = fs.psql(db, f"SELECT count(*) FROM {CAT} c JOIN {ONT} o ON o.entity_class = 'yoga' AND o.canonical_id = c.canonical_id JOIN {REF} r ON r.canonical_id = c.canonical_id "
                      f"WHERE o.canonical_name_en IS DISTINCT FROM c.name_en OR o.canonical_name_sa IS DISTINCT FROM c.name_sa OR r.name_en IS DISTINCT FROM c.name_en "
                      f"OR r.category IS DISTINCT FROM c.category OR o.description IS DISTINCT FROM NULLIF(left(c.significations_text, 150), '')").strip()
    n = fs.psql(db, f"SELECT count(*) FROM {CAT}").strip()
    assert bad == "0" and int(n) >= 148


# ───────────────────────── mutations: the closure is checked against the data, the declaration against the table ─────────────────────────

def test_REAL_WRITER_MUTATION_a_category_outside_the_closed_vocabulary_is_a_FAIL(db, monkeypatch):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "category" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
        assert all(got[c]["v"] == NO_DET for c in fs.CELLS if c != "Narr.agree")
    fs.mutate_and_restore(db, REF, ["canonical_id"], "category", "'a free sentence about the yoga that someone typed here'", "true", check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


@pytest.mark.parametrize("table,col", [(t, c) for t, cs in OPEN_COLUMNS.items() for c in cs] + [(CAT, "category"), (REF, "category")])
def test_REAL_WRITER_MUTATION_dropping_any_declared_column_is_a_FAIL_naming_it(db, monkeypatch, table, col):
    d = _own()
    pn = d["prose_none"]
    pn["transcription_columns"] = [c for c in pn["transcription_columns"] if not (c["column"] == col and c.get("table") == table)]
    pn["closed_columns"] = [c for c in pn["closed_columns"] if not (c["column"] == col and c.get("table") == table)]
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and f"{table}.{col}" in got["Narr.agree"]["measured"], (table, col, got["Narr.agree"]["measured"][:300])
    assert all(got[c]["v"] == NO_DET for c in fs.CELLS if c != "Narr.agree")        # the other five never read N/A on a contradicted declaration
