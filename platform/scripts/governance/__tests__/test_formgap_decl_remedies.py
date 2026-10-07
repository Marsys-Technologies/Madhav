"""test_formgap_decl_remedies.py: the FORM-GAP (N-192) curated-corpus declaration of bg_remedies, shown on rows the REAL writer builds.

bg_remedies keeps `prose_fields [prescription_text, charity_action]` (the table also holds composed rows: the planet-matrix f-strings, 54-odd verbatim classical-text sweep slices, tantric YAML rows). Its hand-typed
literals are declared as TWO curated corpora in CONTAINED mode: 136 prescription sentences and 31 charity actions, pinned by count and sha256 and read from the five committed remedy tables by the per-key AST
reader; each carries a `constant_write` waiver pin (136, 31). What this does and does not do is stated, not hidden: it adds the drift check (a sentence added to the seed, removed from the table or edited FAILs
Narr.agree) and it names what keeps the Null cells capped (one database-read path of the sweep: the loader's literal fallbacks were removed on main); the Null cells do NOT lift.
The real writer (seed_remedy_corpus + the tantric loader) runs on a throw-away PostgreSQL with the real DDL (ws2_l0_remedy_corpus, migrations 081, 177) and one classical-text chunk for the sweep.
"""
from __future__ import annotations

import ast
import collections
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
from _formgap_support import NA, FAIL, NO_DET, PARTIAL, PASS, CELLS  # noqa: E402

AID = "bg_remedies"
T = "brahma_remedy_corpus"
DECLS = ac.load_asset_declarations()
S = "platform/python-sidecar/brahmagyan/l0_remedy_corpus.py"
RUN = "11111111-1111-4111-8111-111111111111"
CONSTS = ["DOSHA_REMEDIES", "LEGACY_REMEDIES", "STOTRA_REMEDIES", "DANA_EXPANSION_REMEDIES", "YANTRA_SPEC_REMEDIES"]


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _cc(col):
    return next(c for c in DECLS[AID]["curated_corpus"] if c["column"] == col)


def test_the_declaration_is_sound_and_keeps_the_prose_fields_it_had():
    e = DECLS[AID]
    assert ac.curated_corpus_problem(e) is None and e["prose_fields"] == ["prescription_text", "charity_action"] and e["lint_none"] and e["fidelity_tests"]
    assert [(c["column"], c["mode"], c["count"], c["waiver"]["covers"], c["waiver"]["pin"]) for c in e["curated_corpus"]] == [
        ("prescription_text", "contained", 136, ["constant_write"], {"constant_write": 136}), ("charity_action", "contained", 31, ["constant_write"], {"constant_write": 31})]
    assert all(c["seed"] == dict(file=S, constants=CONSTS, key=c["column"]) for c in e["curated_corpus"])


def test_the_seed_counts_are_an_independent_ast_count_of_the_literal_assignments():
    """Independent of the engine's reader: count, in the five constants, the dict keys whose value is a plain string literal; an f-string (composed) value is not a corpus sentence."""
    tree = ast.parse((fs.REPO / S).read_text(encoding="utf-8"))
    cnt, composed = collections.Counter(), collections.Counter()
    for node in tree.body:
        names = [t.id for t in node.targets if isinstance(t, ast.Name)] if isinstance(node, ast.Assign) else ([node.target.id] if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) else [])
        if not names or names[0] not in CONSTS:
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Dict):
                for k, v in zip(sub.keys, sub.values):
                    if isinstance(k, ast.Constant) and k.value in ("prescription_text", "charity_action"):
                        (cnt if isinstance(v, ast.Constant) and isinstance(v.value, str) else composed)[k.value] += 1
    assert (cnt["prescription_text"], cnt["charity_action"]) == (136, 31) == (_cc("prescription_text")["count"], _cc("charity_action")["count"])
    assert composed["prescription_text"] == 1 and composed["charity_action"] == 0                    # the one composed DOSHA_REMEDIES sentence is NOT in the corpus


def test_the_pins_are_the_digests_of_the_seed_sentences():
    for col in ("prescription_text", "charity_action"):
        sents = pf.resolve_seed_sentences(fs.REPO, _cc(col)["seed"])
        assert len(sents) == _cc(col)["count"] and pf.corpus_digest(sents) == _cc(col)["digest"], col
        assert len(set(sents)) == len(sents)                                                          # no sentence twice: contained mode can then name each one


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    pg = disposable_pg
    fs.drop_tables(pg, T, "remedy_review_queue", "classical_text_chunks", "classical_texts")
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_texts.sql", "classical_texts"))
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_texts.sql", "classical_text_chunks"))
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_remedy_corpus.sql", T))
    m = re.search(r"ALTER TABLE brahma_remedy_corpus.*?;", (fs.SMIG / "081_l0fr_schema.sql").read_text(encoding="utf-8"), re.S)
    fs.psql(pg, m.group(0))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "081_l0fr_schema.sql", "remedy_review_queue"))
    fs.psql(pg, "ALTER TABLE brahma_remedy_corpus ADD COLUMN IF NOT EXISTS scaffold_status TEXT DEFAULT 'live' CHECK (scaffold_status IN ('live','review','rejected'))")        # migration 177
    fs.psql(pg, "INSERT INTO classical_texts (text_id, title_en, school, tradition, license) VALUES ('bphs', 'b', 'parashari', 'vedic', 'public_domain')")
    fs.psql(pg, "INSERT INTO classical_text_chunks (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end, content_en, source_citation) VALUES "
                "('bphs', 'bphs_c1', 'CH1:V1', 1, 1, 1, 'Recite the Surya mantra on Sunday at dawn to please the Sun.', 'BPHS Ch1')")
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_remedies import RemediesWriter
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    res = RemediesWriter().run(ContextSpec(asset_id=AID, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert res.rows_inserted == 288, res.notes
    yield pg
    fs.drop_tables(pg, T, "remedy_review_queue", "classical_text_chunks", "classical_texts")


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T, [T], decl or _own(), registry=dict(has_writer=True, count_sql="SELECT COUNT(*) FROM brahma_remedy_corpus"))


def test_REAL_WRITER_every_pinned_sentence_is_in_the_table_the_writer_built(db):
    for col in ("prescription_text", "charity_action"):
        rows = [pf.normalise_sentence(x) for x in fs.psql(db, f"SELECT replace({col}, E'\\n', ' ') FROM {T} WHERE {col} IS NOT NULL").split("\n") if x]
        assert all(pf.normalise_sentence(s) in set(rows) for s in pf.resolve_seed_sentences(fs.REPO, _cc(col)["seed"])), col
    assert int(fs.psql(db, f"SELECT count(*) FROM {T}").strip()) == 288                                      # 284 built rows (283 live, one sweep row) + 4 tantric YAML rows


def test_REAL_WRITER_narr_agree_passes_with_the_corpora_and_the_null_cells_keep_their_cap_with_the_one_remaining_reason_named(db, monkeypatch):
    """Every constant_write finding (136 + 31) is covered by the waiver pins; the two literal fallbacks of the tantric loader were removed on main (prose-batch-2 writer edits); what keeps the cap is ONE unresolved
    path: the classical-text sweep reads `content_en` from the database (l0_remedy_corpus.py:3259, a verbatim slice of a stored chunk), which the writer scan cannot follow."""
    got = _m(db, monkeypatch)
    assert got["Narr.agree"]["v"] == PASS
    for c in ("Null.schema_default", "Null.blank_rows"):
        m = got[c]["measured"]
        assert got[c]["v"] == PARTIAL and "declared curated corpus not applied: the scan left 1 write path(s) unresolved" in m and "content_en" in m and "outside every declared waiver" not in m, (c, m[-400:])


def test_the_merged_loader_has_no_literal_fallback_left_so_the_waiver_needs_only_constant_write():
    units, beyond = ac.writer_scan_scope(AID, ac.registered_ids("")[AID])
    ws = ac._lint_module("writer_literal_scan").scan(units, ["prescription_text", "charity_action"], {"prescription_text": [T], "charity_action": [T]}, is_placeholder=ac.ldgr_placeholder_py,
                                                      sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field, beyond=beyond)
    assert {p["kind"] for p in ws["problems"]} == {"constant_write"} and len(ws["unresolved"]) == 1 and "content_en" in ws["unresolved"][0]
    per = collections.Counter(ac.parse_prose_field(p["entry"])[0] for p in ws["problems"])
    assert per == {"prescription_text": 136, "charity_action": 31}                                       # exactly the two waiver pins


@pytest.mark.parametrize("col", ["prescription_text", "charity_action"])
def test_REAL_WRITER_MUTATION_an_edited_pinned_sentence_in_the_table_is_a_FAIL(db, monkeypatch, col):
    seed = pf.resolve_seed_sentences(fs.REPO, _cc(col)["seed"])[0]
    esc = seed.replace("'", "''")

    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and col in got["Narr.agree"]["measured"] and "absent from the table" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, T, "remedy_id", col, f"'{esc} (edited later)'", f"{col} = '{esc}'", check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == PASS


def test_REAL_WRITER_MUTATION_a_pin_the_seed_does_not_hold_is_a_FAIL(db, monkeypatch):
    d = _own()
    d["curated_corpus"][1]["digest"] = "b" * 64
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "digesting to" in got["Narr.agree"]["measured"] and "charity_action" in got["Narr.agree"]["measured"]


def test_REAL_WRITER_MUTATION_a_row_added_to_the_table_is_not_drift_in_contained_mode_but_a_sentence_missing_is(db, monkeypatch):
    fs.psql(db, f"INSERT INTO {T} (remedy_id, planet, domain, remedy_type, prescription_text, source_canonical_id, source_citation) VALUES ('x_extra', 'Sun', 'general', 'mantra', 'An extra composed row', 'BPHS', 'BPHS')")
    try:
        assert _m(db, monkeypatch)["Narr.agree"]["v"] == PASS                                            # the table also holds composed / swept rows: contained mode does not read an extra row as drift
    finally:
        fs.psql(db, f"DELETE FROM {T} WHERE remedy_id = 'x_extra'")
    sent = pf.resolve_seed_sentences(fs.REPO, _cc("prescription_text")["seed"])[3].replace("'", "''")
    rid = fs.psql(db, f"SELECT remedy_id FROM {T} WHERE prescription_text = '{sent}' LIMIT 1").strip()
    row = fs.psql(db, f"SELECT row_to_json(t)::text FROM {T} t WHERE remedy_id = '{rid}'").strip()
    fs.psql(db, f"DELETE FROM {T} WHERE remedy_id = '{rid}'")
    try:
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "absent from the table" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db, f"INSERT INTO {T} SELECT * FROM json_populate_record(NULL::{T}, '{row.replace(chr(39), chr(39) * 2)}'::json)")
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == PASS
