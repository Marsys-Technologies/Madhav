"""test_formgap_decl_dasha.py: the FORM-GAP declaration of bg_dasha_systems is TRUE, shown on rows the REAL writer builds (SS N-191 / N-192).

Three tables seeded from `brahmagyan/l0_dasha_systems.py` (20 systems): brahma_dasha_systems, reference_dasha_systems and the `dasha_system` slice of the SHARED brahma_ontology (declared `produced_tables` filter:
the ontology rows of other classes belong to other assets and are not judged). Word columns are closed by per-key `values_from` of the seed, the ontology description (a fixed f-string over seed values) by its 20
sentences (recomputed here from the seed objects), the aliases and citation words explicitly, two paragraph columns by curated corpora (20 each, the seed named), key columns as identifiers. ONE column is not
checked against the data: sequence_jsonb (hand-typed `note` leaves up to 405 characters: no checked form holds a json string leaf past 200 characters); it is declared a transcription column and the last test
states the gap. The real writer runs on a throw-away PostgreSQL with the real DDL (migrations 176, 178, ws2 ontology); the engine's OWN `_measure_prose` reads the three tables.
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


def _closed(table, col):
    return next(c for c in PN["closed_columns"] if c["column"] == col and (c.get("table") or T1) == table)


def _cc(col):
    return next(c for c in DECLS[AID]["curated_corpus"] if c["column"] == col)


def test_the_declaration_is_sound_and_names_its_forms():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and ac.curated_corpus_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    assert [t["table"] for t in e["produced_tables"]] == [T1, T2, T3] and e["produced_tables"][2]["filter"] == {"column": "entity_class", "equals": "dasha_system"}
    assert [(c.get("table") or T1, c["column"]) for c in PN["identifier_columns"]] == [(T1, "canonical_id"), (T2, "canonical_id"), (T3, "canonical_id"), (T3, "entity_class")]
    assert [c["column"] for c in PN["transcription_columns"]] == ["sequence_jsonb"] and [(c["column"], c["count"]) for c in e["curated_corpus"]] == [("computation_pseudocode", 20), ("conditions_for_use", 20)]


def test_the_declared_values_equal_the_seed_objects():
    import brahmagyan.l0_dasha_systems as DS
    sy = DS.DASHA_SYSTEMS
    assert len(sy) == 20 and len({s["canonical_id"] for s in sy}) == 20
    assert _closed(T3, "description")["values"] == sorted({f"{s['name_en']} — {s['total_cycle_years']}-year {s['school']} dasha system" for s in sy}) and len(_closed(T3, "description")["values"]) == 20
    r = lambda t, c: pf.resolve_values_from(fs.REPO, _closed(t, c)["values_from"])
    assert r(T1, "name_en") == sorted({s["name_en"] for s in sy}) == r(T2, "name_en") == r(T3, "canonical_name_en") and r(T3, "canonical_name_sa") == sorted({s["name_sa"] for s in sy})
    assert r(T1, "school") == sorted({s["school"] for s in sy}) == r(T2, "school") and r(T1, "python_impl_module") == sorted({s["python_impl_module"] for s in sy if s.get("python_impl_module")})
    assert r(T1, "computation_method") == sorted({s["computation_method"] for s in sy}) and r(T1, "base_unit") == sorted({s["base_unit"] for s in sy})
    assert sorted(_closed(T3, "synonyms")["values"]) == sorted({a for s in sy for a in DS._synonyms(s["canonical_id"])})
    assert sorted(_closed(T3, "source_citation")["values"]) == sorted({s["source_citation"] for s in sy})
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
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T1, [T1, T2, T3], decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_the_three_tables_read_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    f = got["Narr.agree"]["prose_none"]["forms"]
    assert sorted(x["column"] for x in f["curated"]) == ["computation_pseudocode", "conditions_for_use"] and all(x["count"] == 20 and x["seed"] is True for x in f["curated"])


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
        d = _own()
        d["curated_corpus"][k]["digest"] = "c" * 64
        assert _m(db, monkeypatch, d)["Narr.agree"]["v"] == FAIL, k


def test_THE_ONE_UNCHECKED_COLUMN_a_changed_sequence_note_is_not_seen_and_that_is_stated(db, monkeypatch):
    """sequence_jsonb is a transcription column (hand-typed note leaves past the 200-character bound of a closed vocabulary): the data is NOT checked against the seed. This test pins the gap so it cannot be forgotten."""
    def check():
        assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA
    fs.mutate_and_restore(db, T1, ["canonical_id"], "sequence_jsonb", "'[{\"note\": \"An edited note nobody checks\"}]'::jsonb", "true", check, cast="::jsonb")
    why = next(c for c in PN["transcription_columns"])["why"]
    assert "the one column of the asset the data is not checked against" in why
