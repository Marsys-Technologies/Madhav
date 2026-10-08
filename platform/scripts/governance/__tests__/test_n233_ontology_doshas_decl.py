"""test_n233_ontology_doshas_decl.py: the prose declarations of bg_ontology and bg_doshas now close the shared brahma_ontology columns their writers write (SS ruling N-233, task T4, declarations 1.62.0).

The final census read Narr.agree FAIL on both, each with a single open column family of the shared table brahma_ontology: bg_ontology left `description` and `synonyms` undeclared, bg_doshas left `description`
(of its dosha rows). Both are hand-authored seed text the writers bind, not composed narration:

  * bg_ontology  : `description` and the alias array `synonyms` are the literals of the seed tuples (a house, domain, concept, karaka or varga entry), the aliases joined with fixed storage-code aliases;
  * bg_doshas    : a dosha ontology row's `description` is `effects_text[:200]` of the catalog row (platform/python-sidecar/brahmagyan/l0_doshas.py), the hand-authored classical effects statement, cut.

The REAL writers run on a throw-away PostgreSQL with the real DDL, the engine's own `_measure_prose` reads the six cells (N/A on both through a checked block), the stored rows are compared with the seed
objects, and every claim has a mutation that must turn the reading red. NOT claimed here: bg_yogas, bg_texts (their open columns are extracted from the DB-only corpus; see N233/DECL_REPORT.md).
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
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET  # noqa: E402

ONT, DOS = "bg_ontology", "bg_doshas"
T_ONT, T_CAT, T_REF = "brahma_ontology", "brahma_dosha_catalog", "reference_doshas"
DECLS = ac.load_asset_declarations()
RUN = "11111111-1111-4111-8111-111111111111"


def _own(aid):
    return json.loads(json.dumps(DECLS[aid]))


def _tc(aid):
    return {(c.get("table"), c["column"]): c for c in DECLS[aid]["prose_none"]["transcription_columns"]}


def test_the_declarations_are_sound_and_name_the_columns_the_census_found_open():
    for aid in (ONT, DOS):
        assert ac.prose_none_problem(DECLS[aid]) is None and DECLS[aid]["prose_fields"] == [] and DECLS[aid]["evidence_kind"] == "writer"
    assert (None, "description") in _tc(ONT) and (None, "synonyms") in _tc(ONT)
    assert (T_ONT, "description") in _tc(DOS)
    for aid, k in ((ONT, (None, "description")), (ONT, (None, "synonyms")), (DOS, (T_ONT, "description"))):
        f, line = _tc(aid)[k]["evidence"].rsplit(":", 1)
        lines = (ac.ROOT / f).read_text(encoding="utf-8").splitlines()
        assert "description" in " ".join(lines[int(line) - 4:int(line) + 3]) and "INSERT INTO brahma_ontology" in " ".join(lines[int(line) - 4:int(line) + 3])


def test_the_dosha_ontology_description_is_cut_from_the_catalog_effects_text_in_the_seed_source():
    src = (ac.ROOT / "platform/python-sidecar/brahmagyan/l0_doshas.py").read_text(encoding="utf-8")
    assert 'd["effects_text"][:200] if d.get("effects_text") else None' in src
    import brahmagyan.l0_doshas as D
    assert all(isinstance(d["effects_text"], str) and d["effects_text"].strip() for d in D.DOSHAS)           # every seed dosha carries the hand-authored statement the description is cut from


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    pg = disposable_pg
    for t in (T_ONT, T_CAT, T_REF):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_ontology.sql", T_ONT))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "176_l0_phase_alpha_new_content_tables.sql", T_CAT))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "178_l0_phase_alpha_reference_tables.sql", T_REF))
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_doshas import DoshasWriter
    from pipeline.orchestrator.writers.bg_ontology import OntologyWriter
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    r1 = DoshasWriter().run(ContextSpec(asset_id=DOS, build_id=RUN, db_conn=conn, config={}))
    r2 = OntologyWriter().run(ContextSpec(asset_id=ONT, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert r1.rows_inserted == 198 and "total': 414" in r2.notes, (r1.notes, r2.notes)
    yield pg
    for t in (T_ONT, T_CAT, T_REF):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def _m(db, mp, aid, decl=None):
    tables, target = ([T_ONT], T_ONT) if aid == ONT else ([T_CAT, T_REF, T_ONT], T_CAT)
    return fs.measure(aid, db, mp, ac.registered_ids("")[aid], target, tables, decl or _own(aid), registry=dict(has_writer=True))


@pytest.mark.parametrize("aid", [ONT, DOS])
def test_REAL_WRITER_each_asset_reads_na_on_all_six_cells_through_a_checked_block(db, monkeypatch, aid):
    got = _m(db, monkeypatch, aid)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert b["open"] == [] and b["contradicted"] == []
    cols = set(b["transcription_columns"])
    assert (f"{T_ONT}.description" in cols) and (aid != ONT or f"{T_ONT}.synonyms" in cols)


def test_REAL_WRITER_the_stored_ontology_rows_are_the_seed_objects_so_the_two_columns_are_what_the_declaration_says(db):
    import brahmagyan.l0_ontology as O
    rows = json.loads(fs.psql(db, f"SELECT json_agg(json_build_object('ec', entity_class, 'id', canonical_id, 'd', description, 's', synonyms)) FROM {T_ONT} WHERE entity_class <> 'dosha'"))
    got = {(r["ec"], r["id"]): (r["d"], r["s"] or []) for r in rows}
    seed = {(e["entity_class"], e["canonical_id"]): (e.get("description"), list(e["synonyms"])) for e in O.ENTITIES}
    assert set(got) == set(seed)
    for k, v in got.items():
        assert seed.get(k) == v, (k, v, seed.get(k))
    assert sum(1 for v in got.values() if v[0]) > 100                                                         # real descriptions, not an empty column


def test_REAL_WRITER_the_stored_dosha_description_is_exactly_the_first_200_characters_of_the_catalog_effects_text(db):
    bad = fs.psql(db, f"SELECT count(*) FROM {T_ONT} o JOIN {T_CAT} c ON c.canonical_id = o.canonical_id WHERE o.entity_class = 'dosha' AND o.description IS DISTINCT FROM left(c.effects_text, 200)").strip()
    n = fs.psql(db, f"SELECT count(*) FROM {T_ONT} WHERE entity_class = 'dosha'").strip()
    assert bad == "0" and int(n) == 66


def test_REAL_WRITER_MUTATION_dropping_a_declared_column_is_a_FAIL_naming_it(db, monkeypatch):
    for aid, key, col, tbl in ((ONT, "transcription_columns", "description", None), (ONT, "transcription_columns", "synonyms", None), (DOS, "transcription_columns", "description", T_ONT)):
        d = _own(aid)
        d["prose_none"][key] = [c for c in d["prose_none"][key] if not (c["column"] == col and c.get("table") == tbl)]
        got = _m(db, monkeypatch, aid, d)
        assert got["Narr.agree"]["v"] == FAIL and f"{T_ONT}.{col}" in got["Narr.agree"]["measured"], (aid, col, got["Narr.agree"]["measured"][:300])
        assert all(got[c]["v"] == NO_DET for c in fs.CELLS if c != "Narr.agree")               # the other five never read N/A on a contradicted declaration


def test_REAL_WRITER_MUTATION_a_new_open_text_column_on_the_table_bg_ontology_owns_whole_is_caught(db, monkeypatch):
    fs.psql(db, f"ALTER TABLE {T_ONT} ADD COLUMN IF NOT EXISTS extra_note TEXT")
    try:
        fs.psql(db, f"UPDATE {T_ONT} SET extra_note = 'a free sentence another writer added' WHERE entity_class = 'planet' AND canonical_id = (SELECT min(canonical_id) FROM {T_ONT} WHERE entity_class = 'planet')")
        got = _m(db, monkeypatch, ONT)
        assert got["Narr.agree"]["v"] == FAIL and "extra_note" in got["Narr.agree"]["measured"]            # a new open text column is caught on the table bg_ontology owns whole
    finally:
        fs.psql(db, f"ALTER TABLE {T_ONT} DROP COLUMN IF EXISTS extra_note")
    assert _m(db, monkeypatch, ONT)["Narr.agree"]["v"] == NA
