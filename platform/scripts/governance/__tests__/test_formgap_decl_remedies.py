"""test_formgap_decl_remedies.py: the FORM-GAP (N-192) curated-corpus declaration of bg_remedies, shown on rows the REAL writer builds.

bg_remedies keeps `prose_fields [prescription_text, charity_action]` (the table also holds composed rows: the planet-matrix f-strings, classical-text sweep slices, tantric YAML rows). Its 31 hand-typed charity actions
are declared as a curated corpus in CONTAINED mode (count and sha256 pin, the five committed remedy tables as the per-key seed, a `constant_write` waiver pin of 31). What this does and does not do is stated, not
hidden: it adds the drift check (a pinned sentence removed from the table or edited FAILs Narr.agree) and it does NOT lift the Null cells.
The hand-typed PRESCRIPTION sentences are pinned too (SS N-210): citation pass 2 (`apply_pass2`, brahmagyan/citation_pass2_remedies.py, #3210) removes rows and rewrites sentences, so the 136 committed literals are
not what reaches the table. The curated seed reads them THROUGH the overlay (a `seed.overlay` of the removed ids and the edits, by AST): 136 literals - 13 removed - 9 replaced + 9 + 27 overlay sentences = 150 pinned
sentences, contained mode. The tests show the pin against the writer's own `build_all_remedies()` rows and the live table, and that one edited sentence reads FAIL.
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
    assert [(c["column"], c["mode"], c["count"], (c.get("waiver") or {}).get("covers"), (c.get("waiver") or {}).get("pin")) for c in e["curated_corpus"]] == [
        ("prescription_text", "contained", 150, None, None), ("charity_action", "contained", 31, ["constant_write"], {"constant_write": 31})]
    assert _cc("charity_action")["seed"] == dict(file=S, constants=CONSTS, key="charity_action")
    ov = _cc("prescription_text")["seed"]["overlay"]
    assert {k: v for k, v in ov.items() if k != "apply_sha256"} == dict(file="platform/python-sidecar/brahmagyan/citation_pass2_remedies.py", removed="REMOVED_REMEDY_IDS", edits="PASS2_EDITS", id_key="remedy_id", apply_function="apply_pass2")
    assert ov["apply_sha256"] == pf.function_source_sha256(pf._parse_source(fs.REPO, ov["file"]), "apply_pass2", ov["file"])


def test_the_seed_count_is_an_independent_ast_count_of_the_literal_assignments():
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
    assert cnt["charity_action"] == 31 == _cc("charity_action")["count"] and cnt["prescription_text"] == 136 and composed["charity_action"] == 0


def test_the_pin_is_the_digest_of_the_seed_sentences():
    sents = pf.resolve_seed_sentences(fs.REPO, _cc("charity_action")["seed"])
    assert len(sents) == 31 and pf.corpus_digest(sents) == _cc("charity_action")["digest"] and len(set(sents)) == 31


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
    assert res.rows_inserted == 263, res.notes                                                    # 258 built rows after citation pass 2, one sweep row, 4 tantric YAML rows
    yield pg
    fs.drop_tables(pg, T, "remedy_review_queue", "classical_text_chunks", "classical_texts")


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T, [T], decl or _own(), registry=dict(has_writer=True, count_sql="SELECT COUNT(*) FROM brahma_remedy_corpus"))


def test_REAL_WRITER_every_pinned_charity_action_is_in_the_table_the_writer_built(db):
    rows = {pf.normalise_sentence(x) for x in fs.psql(db, f"SELECT replace(charity_action, E'\\n', ' ') FROM {T} WHERE charity_action IS NOT NULL").split("\n") if x}
    assert all(pf.normalise_sentence(s) in rows for s in pf.resolve_seed_sentences(fs.REPO, _cc("charity_action")["seed"]))
    assert int(fs.psql(db, f"SELECT count(*) FROM {T}").strip()) == 263


def test_REAL_WRITER_narr_agree_passes_and_the_null_cells_keep_their_cap_with_the_reason_named(db, monkeypatch):
    """The 31 charity constant_write findings are covered by the waiver pin; the 136 prescription constant writes (and the ones citation pass 2 adds) are covered by no corpus, and the sweep's
    `content_en` read from the database (l0_remedy_corpus.py:3259) is unresolved: the cap stays and says so."""
    got = _m(db, monkeypatch)
    assert got["Narr.agree"]["v"] == PASS
    for c in ("Null.schema_default", "Null.blank_rows"):
        m = got[c]["measured"]
        assert got[c]["v"] == PARTIAL and "declared curated corpus not applied:" in m and "outside every declared waiver" in m and "prescription_text" in m, (c, m[-400:])


@pytest.mark.parametrize("col", ["charity_action"])
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
    assert d["curated_corpus"][1]["column"] == "charity_action"
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "digesting to" in got["Narr.agree"]["measured"] and "charity_action" in got["Narr.agree"]["measured"]


def test_REAL_WRITER_MUTATION_a_row_added_to_the_table_is_not_drift_in_contained_mode_but_a_sentence_missing_is(db, monkeypatch):
    fs.psql(db, f"INSERT INTO {T} (remedy_id, planet, domain, remedy_type, prescription_text, source_canonical_id, source_citation) VALUES ('x_extra', 'Sun', 'general', 'mantra', 'An extra composed row', 'BPHS', 'BPHS')")
    try:
        assert _m(db, monkeypatch)["Narr.agree"]["v"] == PASS                                            # the table also holds composed / swept rows: contained mode does not read an extra row as drift
    finally:
        fs.psql(db, f"DELETE FROM {T} WHERE remedy_id = 'x_extra'")
    sent = pf.resolve_seed_sentences(fs.REPO, _cc("charity_action")["seed"])[3].replace("'", "''")
    rid = fs.psql(db, f"SELECT remedy_id FROM {T} WHERE charity_action = '{sent}' LIMIT 1").strip()
    row = fs.psql(db, f"SELECT row_to_json(t)::text FROM {T} t WHERE remedy_id = '{rid}'").strip()
    fs.psql(db, f"DELETE FROM {T} WHERE remedy_id = '{rid}'")
    try:
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "absent from the table" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db, f"INSERT INTO {T} SELECT * FROM json_populate_record(NULL::{T}, '{row.replace(chr(39), chr(39) * 2)}'::json)")
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == PASS


def test_the_prescription_pin_is_the_post_citation_pass_2_corpus_computed_two_independent_ways():
    """The engine's AST read of the five constants THROUGH the overlay equals the sentences the writer's own build_all_remedies() rows carry: every pinned sentence is a built row's prescription_text, and
    the rows the pass edits or removes are exactly the ones the overlay says (a removed row's literal is not in the corpus, a replaced literal is replaced)."""
    from brahmagyan import l0_remedy_corpus as R
    from brahmagyan import citation_pass2_remedies as P2
    cc = _cc("prescription_text")
    sents = pf.resolve_seed_sentences(fs.REPO, cc["seed"])
    rows = R.build_all_remedies()
    built = {r["prescription_text"] for r in rows}
    assert len(sents) == 150 == cc["count"] and pf.corpus_digest(sents) == cc["digest"] and set(sents) <= built
    raw = set(pf.resolve_seed_sentences(fs.REPO, dict(file=S, constants=CONSTS, key="prescription_text")))
    assert len(raw) == 136 and len(raw & set(sents)) == 136 - 13 - 9                                  # 13 removed rows and 9 replaced literals leave the raw seed
    assert len(P2.REMOVED_REMEDY_IDS) == 25 and not ({r["remedy_id"] for r in rows} & P2.REMOVED_REMEDY_IDS)
    assert sum(1 for v in P2.PASS2_EDITS.values() if "prescription_text" in v) == 36 and len(set(sents) - raw) == 36


def test_REAL_WRITER_every_pinned_prescription_sentence_is_in_the_table_the_writer_built(db):
    rows = {pf.normalise_sentence(x) for x in fs.psql(db, f"SELECT replace(prescription_text, E'\\n', ' ') FROM {T} WHERE prescription_text IS NOT NULL").split("\n") if x}
    assert all(pf.normalise_sentence(s_) in rows for s_ in pf.resolve_seed_sentences(fs.REPO, _cc("prescription_text")["seed"]))


def test_REAL_WRITER_MUTATION_one_edited_prescription_sentence_is_a_FAIL(db, monkeypatch):
    seed = pf.resolve_seed_sentences(fs.REPO, _cc("prescription_text")["seed"])[5]
    esc = seed.replace("'", "''")

    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "prescription_text" in got["Narr.agree"]["measured"] and "absent from the table" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, T, "remedy_id", "prescription_text", f"'{esc} (edited later)'", f"prescription_text = '{esc}'", check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == PASS


def test_REAL_WRITER_MUTATION_a_prescription_pin_the_seed_does_not_hold_is_a_FAIL(db, monkeypatch):
    for field, val in (("digest", "c" * 64), ("count", 151)):
        d = _own()
        d["curated_corpus"][0][field] = val
        got = _m(db, monkeypatch, d)
        assert got["Narr.agree"]["v"] == FAIL and "prescription_text" in got["Narr.agree"]["measured"], field


def _overlay_world(tmp_path, seed_extra="", ov_extra="", apply_body="    return rows\n"):
    base = tmp_path / "platform" / "python-sidecar"
    base.mkdir(parents=True, exist_ok=True)
    (base / "seed.py").write_text('ROWS = [dict(remedy_id="a", t="one"), dict(remedy_id="b", t="two"), {"remedy_id": "c", "t": "three"}, dict(remedy_id="d", t=f"{x}")]\n' + seed_extra, encoding="utf-8")
    (base / "ov.py").write_text('GONE = frozenset({"b"})\nEDITS = {"c": {"t": ("three" " edited")}, "d": {"t": "four"}, "e": {"t": "five"}, "f": {"u": "x"}}\n' + ov_extra + "def apply_it(rows):\n" + apply_body, encoding="utf-8")
    h = pf.function_source_sha256(pf._parse_source(tmp_path, "platform/python-sidecar/ov.py"), "apply_it", "ov.py") if "def apply_it" in (base / "ov.py").read_text() else None
    return dict(file="platform/python-sidecar/seed.py", constants=["ROWS"], key="t",
                overlay=dict(file="platform/python-sidecar/ov.py", removed="GONE", edits="EDITS", id_key="remedy_id", apply_function="apply_it", apply_sha256=h))


def test_the_overlay_reader_applies_removals_replacements_and_additions_by_ast(tmp_path):
    spec = _overlay_world(tmp_path)
    assert pf.seed_shape_problem(spec) is None
    assert sorted(pf.resolve_seed_sentences(tmp_path, spec)) == ["five", "four", "one", "three edited"]            # b removed; c replaced; d (composed) replaced by a literal; e added; f carries no t
    assert pf.seed_shape_problem(dict(spec, overlay=dict(spec["overlay"], extra=1))) is not None
    assert pf.seed_shape_problem(dict(spec, overlay=dict(spec["overlay"], removed="not a name"))) is not None
    assert pf.seed_shape_problem(dict(spec, overlay=dict(spec["overlay"], apply_sha256="abc"))) is not None


@pytest.mark.parametrize("seed_extra,ov_extra,needle", [
    ("ROWS.append(dict(remedy_id='z', t='injected'))\n", "", "a seed constant is changed"),
    ("ROWS += [dict(remedy_id='z', t='injected')]\n", "", "a seed constant is changed"),
    ("ROWS.extend([])\n", "", "a seed constant is changed"),
    ("ROWS[0] = dict(remedy_id='a', t='other')\n", "", "a seed constant is changed"),
    ("if True:\n    ROWS.append(dict(remedy_id='z', t='injected'))\n", "", "a seed constant is changed"),
    ("", "EDITS.update({'a': {'t': 'rewritten'}})\n", "an overlay constant is changed"),
    ("", "GONE |= {'a'}\n", "an overlay constant is changed"),
    ("", "EDITS['a'] = {'t': 'rewritten'}\n", "an overlay constant is changed"),
])
def test_FORGERY_a_mutation_after_the_assignment_makes_the_seed_unreadable(tmp_path, seed_extra, ov_extra, needle):
    """Re-review fix 4: the reader used to read the assignment only, so `EDITS.update(...)`, `GONE |= ...` or `ROWS.append(...)` left the count and the digest matching while the module held something else."""
    spec = _overlay_world(tmp_path, seed_extra, ov_extra)
    with pytest.raises(ValueError, match=needle):
        pf.resolve_seed_sentences(tmp_path, spec)


def test_FORGERY_an_edit_to_the_apply_function_changes_the_pinned_hash(tmp_path):
    spec = _overlay_world(tmp_path)
    pf.resolve_seed_sentences(tmp_path, spec)                                                             # the pinned function reads fine
    (tmp_path / "platform" / "python-sidecar" / "ov.py").write_text(
        'GONE = frozenset({"b"})\nEDITS = {"c": {"t": ("three" " edited")}, "d": {"t": "four"}, "e": {"t": "five"}, "f": {"u": "x"}}\ndef apply_it(rows):\n    rows.append({"remedy_id": "z"})\n    return rows\n', encoding="utf-8")
    with pytest.raises(ValueError, match="is not the function the overlay was pinned to"):
        pf.resolve_seed_sentences(tmp_path, spec)
    (tmp_path / "platform" / "python-sidecar" / "ov.py").write_text(
        'GONE = frozenset({"b"})\nEDITS = {"c": {"t": ("three" " edited")}, "d": {"t": "four"}, "e": {"t": "five"}, "f": {"u": "x"}}\n# a comment\ndef apply_it(rows):\n\n    return rows   # same code, new layout\n', encoding="utf-8")
    pf.resolve_seed_sentences(tmp_path, spec)                                                             # comments and layout do not move the hash


def test_the_real_pass_2_module_and_remedy_tables_are_unmutated_and_the_real_pin_holds():
    cc = _cc("prescription_text")
    assert len(pf.resolve_seed_sentences(fs.REPO, cc["seed"])) == cc["count"]
    assert pf.constant_mutations(pf._parse_source(fs.REPO, S), CONSTS) == []
