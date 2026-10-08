"""test_formgap_decl_dasha.py: the FORM-GAP declaration of bg_dasha_systems is TRUE, shown on rows the REAL writer builds (SS N-191 / N-192).

Three tables seeded from `brahmagyan/l0_dasha_systems.py` (20 systems): brahma_dasha_systems, reference_dasha_systems and the `dasha_system` slice of the SHARED brahma_ontology (declared `produced_tables` filter:
the ontology rows of other classes belong to other assets and are not judged). Word columns are closed by per-key `values_from` of the seed, the ontology description (a fixed f-string over seed values) by its 20
sentences (recomputed here from the seed objects), the aliases and citation words explicitly, two paragraph columns by curated corpora (20 each, the seed named), key columns as identifiers. sequence_jsonb
is closed by `json_leaf_patterns` (WFIX-B, census 5124c348a): the rulers, lords, yogini names and system types by closed values, the 11 hand-typed `note` sentences (two of them longer than the 200 characters a
`values` entry may hold) by sha256 pins that this file recomputes from the seed objects. The real writer runs on a throw-away PostgreSQL with the real DDL (migrations 176, 178, ws2 ontology); the engine's OWN `_measure_prose` reads the three tables.
"""
from __future__ import annotations

import json
import pathlib
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
from _formgap_support import NA, FAIL, NO_DET, CELLS  # noqa: E402

AID = "bg_dasha_systems"
T1, T2, T3 = "brahma_dasha_systems", "reference_dasha_systems", "brahma_ontology"
DECLS = ac.load_asset_declarations()
PN = DECLS[AID]["prose_none"]
RUN = "11111111-1111-4111-8111-111111111111"


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _own_isolated():
    """The committed declaration itself (sequence_jsonb is closed by its own json_leaf_patterns since WFIX-B; the earlier test-only transcription claim is gone)."""
    return _own()


def _closed(table, col):
    return next(c for c in PN["closed_columns"] if c["column"] == col and (c.get("table") or T1) == table)


def _cc(col):
    return next(c for c in DECLS[AID]["curated_corpus"] if c["column"] == col)


def test_the_declaration_is_sound_and_names_its_forms():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and ac.curated_corpus_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    assert [t["table"] for t in e["produced_tables"]] == [T1, T2, T3] and e["produced_tables"][2]["filter"] == {"column": "entity_class", "equals": "dasha_system"}
    assert [(c.get("table") or T1, c["column"]) for c in PN["identifier_columns"]] == [(T1, "canonical_id"), (T2, "canonical_id"), (T3, "canonical_id"), (T3, "entity_class")]
    assert "transcription_columns" not in PN and [(c["column"], c["count"]) for c in e["curated_corpus"]] == [("computation_pseudocode", 20), ("conditions_for_use", 20), ("description", 20), ("source_citation", 20)]


def test_the_declared_values_equal_the_seed_objects():
    import brahmagyan.l0_dasha_systems as DS
    sy = DS.DASHA_SYSTEMS
    assert len(sy) == 20 and len({s["canonical_id"] for s in sy}) == 20
    desc = [f"{s['name_en']} — {s['total_cycle_years']}-year {s['school']} dasha system" for s in sy]
    d3 = next(c for c in DECLS[AID]["curated_corpus"] if c["column"] == "description" and c["table"] == T3)
    assert d3["count"] == 20 and d3["digest"] == pf.corpus_digest(desc) and not any(c["column"] == "description" for c in PN["closed_columns"])
    r = lambda t, c: pf.resolve_values_from(fs.REPO, _closed(t, c)["values_from"])
    assert r(T1, "name_en") == sorted({s["name_en"] for s in sy}) == r(T2, "name_en") == r(T3, "canonical_name_en") and r(T3, "canonical_name_sa") == sorted({s["name_sa"] for s in sy})
    assert r(T1, "school") == sorted({s["school"] for s in sy}) == r(T2, "school") and r(T1, "python_impl_module") == sorted({s["python_impl_module"] for s in sy if s.get("python_impl_module")})
    assert r(T1, "computation_method") == sorted({s["computation_method"] for s in sy}) and r(T1, "base_unit") == sorted({s["base_unit"] for s in sy})
    assert sorted(_closed(T3, "synonyms")["values"]) == sorted({a for s in sy for a in DS._synonyms(s["canonical_id"])})
    sc = next(c for c in DECLS[AID]["curated_corpus"] if c["column"] == "source_citation" and c["table"] == T3)
    assert sc["count"] == 20 and sc["digest"] == pf.corpus_digest([s["source_citation"] for s in sy])
    assert pf.corpus_digest([s["computation_pseudocode"] for s in sy]) == _cc("computation_pseudocode")["digest"] and pf.corpus_digest([s["conditions_for_use"] for s in sy]) == _cc("conditions_for_use")["digest"]


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    pg = disposable_pg
    for t in (T1, T2, T3):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_ontology.sql", T3))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "176_l0_phase_alpha_new_content_tables.sql", T1))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "178_l0_phase_alpha_reference_tables.sql", T2))
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_dasha_systems import DashaSystemsWriter
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    res = DashaSystemsWriter().run(ContextSpec(asset_id=AID, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert res.rows_inserted == 60, res.notes
    yield pg
    for t in (T1, T2, T3):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T1, [T1, T2, T3], decl or _own_isolated(), registry=dict(has_writer=True))


def test_REAL_WRITER_the_three_tables_read_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    f = got["Narr.agree"]["prose_none"]["forms"]
    assert sorted(x["column"] for x in f["curated"]) == ["computation_pseudocode", "conditions_for_use", "description", "source_citation"] and all(x["count"] == 20 for x in f["curated"])
    assert all(x["seed"] is True for x in f["curated"] if x["column"] not in ("description", "source_citation"))


def test_REAL_WRITER_the_other_classes_of_the_shared_ontology_table_are_not_judged(db, monkeypatch):
    fs.psql(db, "INSERT INTO brahma_ontology (entity_class, canonical_id, canonical_name_en, description, source_citation) VALUES ('planet', 'sun', 'Sun', 'A free sentence about the Sun that another asset owns', 'x')")
    try:
        assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA
    finally:
        fs.psql(db, "DELETE FROM brahma_ontology WHERE entity_class = 'planet'")


# (table, pk columns, column, new SQL value, cast, needle)
MUTS = [
    (T1, ["canonical_id"], "name_en", "'Quantum Dasha'", "", "name_en"),
    (T1, ["canonical_id"], "school", "'new_school'", "", "school"),
    (T1, ["canonical_id"], "computation_pseudocode", "'A rewritten method paragraph'", "", "computation_pseudocode"),
    (T1, ["canonical_id"], "conditions_for_use", "'A rewritten applicability sentence'", "", "conditions_for_use"),
    (T2, ["canonical_id"], "name_en", "'Quantum Dasha'", "", "name_en"),
    (T3, ["entity_class", "canonical_id"], "description", "'A composed description the seed never writes'", "", "description"),
    (T3, ["entity_class", "canonical_id"], "synonyms", "ARRAY['a new alias']", "::text[]", "synonyms"),
    (T3, ["entity_class", "canonical_id"], "source_citation", "'A citation nobody declared'", "", "source_citation"),
]


@pytest.mark.parametrize("table,pk,col,newv,cast,needle", MUTS)
def test_REAL_WRITER_MUTATION_a_value_outside_its_form_is_a_FAIL(db, monkeypatch, table, pk, col, newv, cast, needle):
    where = "entity_class = 'dasha_system'" if table == T3 else "true"

    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, table, pk, col, newv, where, check, cast=cast)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_a_corpus_pin_that_is_not_the_data_is_a_FAIL(db, monkeypatch):
    for k in (0, 1):
        d = _own_isolated()
        d["curated_corpus"][k]["digest"] = "c" * 64
        assert _m(db, monkeypatch, d)["Narr.agree"]["v"] == FAIL, k


def _seq():
    return _closed(T1, "sequence_jsonb")


def test_WFIXB_sequence_jsonb_is_closed_by_leaf_patterns_and_pins_every_seed_note_by_sha256():
    import hashlib
    import brahmagyan.l0_dasha_systems as DS
    c = _seq()
    pats = {p["path"]: p for p in c["json_leaf_patterns"]}
    assert sorted(pats) == ["$.lords[*]", "$.note", "$.ruler", "$.type", "$.yogini"] and "transcription_columns" not in PN
    notes = sorted(s["sequence_jsonb"]["note"] for s in DS.DASHA_SYSTEMS if isinstance(s["sequence_jsonb"], dict) and "note" in s["sequence_jsonb"])
    assert len(notes) == 11 and max(len(n) for n in notes) > 200                              # the reason `values` cannot hold them
    assert pats["$.note"]["sha256"] == sorted(hashlib.sha256(n.encode("utf-8")).hexdigest() for n in notes)
    assert ac.prose_none_problem(DECLS[AID]) is None


def test_WFIXB_every_string_leaf_of_every_seed_sequence_is_inside_the_declared_closure():
    """An independent re-derivation: walk the committed seed's own sequence_jsonb documents and test each string leaf against the declared pattern of its path (no SQL)."""
    import hashlib
    import brahmagyan.l0_dasha_systems as DS
    pats = {p["path"]: p for p in _seq()["json_leaf_patterns"]}
    seen = set()

    def ok(path, v):
        p = pats.get(path)
        if p is None:
            return False
        return v in p["values"] if "values" in p else hashlib.sha256(v.encode("utf-8")).hexdigest() in p["sha256"]

    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{path}.{k}")
        elif isinstance(x, list):
            for v in x:
                walk(v, f"{path}[*]")
        elif isinstance(x, str):
            seen.add(path)
            assert ok(re.sub(r"^\$\[\*\]", "$", path), x), (path, x[:60])
    import re
    for s in DS.DASHA_SYSTEMS:
        walk(s["sequence_jsonb"], "$")
    assert {re.sub(r"^\$\[\*\]", "$", p) for p in seen} == set(pats)                        # no declared path is dead, no seed path is undeclared


def test_WFIXB_REAL_WRITER_the_committed_declaration_reads_na_on_all_six_cells_including_sequence_jsonb(db, monkeypatch):
    got = _m(db, monkeypatch, _own())
    fs.all_na(got)
    assert any(x["table"] == T1 and x["column"] == "sequence_jsonb" for x in got["Narr.agree"]["prose_none"]["closed"])


def test_WFIXB_REAL_WRITER_MUTATION_an_edited_note_or_a_new_leaf_in_sequence_jsonb_is_a_FAIL(db, monkeypatch):
    for doc in ('{"type": "rashi_sequence", "note": "An edited note nobody pinned"}', '[{"ruler": "sun", "years": 6, "comment": "a free sentence"}]', '{"type": "a free type"}'):
        def check():
            got = _m(db, monkeypatch, _own())
            assert got["Narr.agree"]["v"] == FAIL and "sequence_jsonb" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:300]
        fs.mutate_and_restore(db, T1, ["canonical_id"], "sequence_jsonb", f"'{doc}'::jsonb", "canonical_id = 'vimshottari'", check, cast="::jsonb")
    assert _m(db, monkeypatch, _own())["Narr.agree"]["v"] == NA
