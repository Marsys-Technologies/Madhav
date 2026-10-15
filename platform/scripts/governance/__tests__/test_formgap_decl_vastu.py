"""test_formgap_decl_vastu.py: the FORM-GAP declaration of bg_vastu_directions is TRUE, shown on rows the REAL writer builds (SS N-191 / N-192).

Two tables seeded from `brahmagyan/l0_vastu_directions.py` (8 compass directions, 24 remedial lines). The declaration closes each word column by per-key `values_from` of the committed seed, the five remedial
citation words explicitly, `secondary_graha` as `unset_columns`, and the 24 remedy sentences as a curated corpus (count + sha256, the committed seed named). The real writer runs on a throw-away PostgreSQL
carrying the real DDL (migration 284); the engine's OWN `_measure_prose` reads both tables and all six Narr / Null cells must read N/A through a checked block. Every claim has a mutation.
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

AID = "bg_vastu_directions"
T1, T2 = "bg_vastu_directions", "bg_vastu_direction_remedials"
DECLS = ac.load_asset_declarations()
S = "platform/python-sidecar/brahmagyan/l0_vastu_directions.py"
RUN = "11111111-1111-4111-8111-111111111111"


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _closed(table, col):
    return next(c for c in DECLS[AID]["prose_none"]["closed_columns"] if c["column"] == col and (c.get("table") or T1) == table)


# ═════════════════════════════ the declaration is the shape it says ═════════════════════════════

def test_the_declaration_is_sound_and_has_each_form():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and ac.curated_corpus_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    pn = e["prose_none"]
    assert [(c.get("table") or T1, c["column"]) for c in pn["unset_columns"]] == [(T1, "secondary_graha")] and "transcription_columns" not in pn
    cc = e["curated_corpus"]
    assert len(cc) == 1 and (cc[0]["table"], cc[0]["column"], cc[0]["mode"], cc[0]["count"]) == (T2, "remedy_description", "equal", 24) and cc[0]["seed"]["key"] == "remedy_description"


def test_the_closed_vocabularies_are_the_hand_stated_vastu_words():
    r = lambda t, c: pf.resolve_values_from(fs.REPO, _closed(t, c)["values_from"])
    assert r(T1, "direction") == r(T2, "direction") == sorted(["East", "North", "Northeast", "Northwest", "South", "Southeast", "Southwest", "West"])
    assert r(T1, "ruling_graha") == sorted(["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"])
    assert r(T1, "element") == sorted(["Water", "Fire", "Air", "Ether", "Earth"])
    assert r(T1, "favorable_color") == sorted(["Green", "Red", "Orange/Gold", "Grey/Black", "Yellow", "White/Pink", "White/Silver"])
    assert r(T2, "remedy_type") == sorted(["color", "function", "material", "space", "symbol"])
    assert sorted(_closed(T2, "classical_citation")["values"]) == sorted(["Brihat Samhita Ch.53 (Vastu-vidya)", "Mayamata Ch.6", "Brihat Samhita Ch.53", "Vastu Shastra tradition (Nairitya corner)", "Vastu Shastra tradition"])


def test_the_corpus_pin_is_the_seeds_digest_and_every_remedy_is_a_literal():
    import brahmagyan.l0_vastu_directions as V
    cc = DECLS[AID]["curated_corpus"][0]
    sents = [r["remedy_description"] for r in V.VASTU_DIRECTION_REMEDIALS]
    assert len(sents) == 24 == cc["count"] and pf.corpus_digest(sents) == cc["digest"]
    assert sorted(pf.resolve_seed_sentences(fs.REPO, cc["seed"])) == sorted(sents)                      # the per-key AST read finds every one of them as a plain literal
    assert all(isinstance(s, str) and 40 < len(s) < 200 for s in sents)


# ═════════════════════════════ the real writer on the real DDL ═════════════════════════════

@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    pg = disposable_pg
    fs.drop_tables(pg, T1, T2)
    for t in (T1, T2):
        fs.psql(pg, fs.create_table_ddl(fs.MIG / "284_bg_vastu_directions.sql", t))
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_vastu_directions import BgVastuDirectionsWriter
    conn = psycopg.connect(pg.url, autocommit=True)
    res = BgVastuDirectionsWriter().run(ContextSpec(asset_id=AID, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert res.rows_inserted == 32, res.notes
    yield pg
    fs.drop_tables(pg, T1, T2)


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T1, [T1, T2], decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_both_tables_read_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    f = got["Narr.agree"]["prose_none"]["forms"]
    assert [(x["table"], x["column"]) for x in f["unset"]] == [(T1, "secondary_graha")] and f["curated"][0]["count"] == 24 and f["curated"][0]["seed"] is True
    assert len(f["values_from"]) == 6


def test_REAL_WRITER_the_live_columns_equal_the_seed_vocabularies(db):
    for t, c in ((T1, "direction"), (T1, "ruling_graha"), (T1, "element"), (T1, "favorable_color"), (T2, "direction"), (T2, "remedy_type")):
        live = sorted(x for x in fs.psql(db, f"SELECT DISTINCT {c} FROM {t} WHERE {c} IS NOT NULL").split("\n") if x)
        assert live == pf.resolve_values_from(fs.REPO, _closed(t, c)["values_from"]), (t, c)
    live = sorted(x for x in fs.psql(db, f"SELECT DISTINCT classical_citation FROM {T2}").split("\n") if x)
    assert live == sorted(_closed(T2, "classical_citation")["values"])


@pytest.mark.parametrize("table,pk,col,newv,needle", [
    (T1, "direction", "ruling_graha", "'Pluto'", "ruling_graha"),
    (T1, "direction", "element", "'Plasma'", "element"),
    (T1, "direction", "favorable_color", "'Ultraviolet'", "favorable_color"),
    (T1, "direction", "secondary_graha", "'Ketu'", "secondary_graha"),
    (T1, "direction", "secondary_graha", "''", "secondary_graha"),
    (T2, "id", "remedy_type", "'ritual'", "remedy_type"),
    (T2, "id", "classical_citation", "'A freshly typed citation'", "classical_citation"),
    (T2, "id", "remedy_description", "'A new remedy line that is not in the pinned corpus at all'", "remedy_description"),
])
def test_REAL_WRITER_MUTATION_a_value_outside_its_form_is_a_FAIL(db, monkeypatch, table, pk, col, newv, needle):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, table, pk, col, newv, "true", check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_an_added_or_removed_remedy_line_is_drift(db, monkeypatch):
    fs.psql(db, f"INSERT INTO {T2} (direction, remedy_type, remedy_description, classical_citation) VALUES ('North', 'ritual', 'A twenty-fifth sentence', 'Mayamata Ch.6')")
    try:
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "sentence was added" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db, f"DELETE FROM {T2} WHERE remedy_type = 'ritual'")
    keep = fs.psql(db, f"SELECT direction || '|' || remedy_type || '|' || remedy_description || '|' || classical_citation FROM {T2} ORDER BY direction, remedy_type LIMIT 1").strip().split("|")
    fs.psql(db, f"DELETE FROM {T2} WHERE direction = '{keep[0]}' AND remedy_type = '{keep[1]}'")
    try:
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "sentence was removed" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db, f"INSERT INTO {T2} (direction, remedy_type, remedy_description, classical_citation) VALUES ('{keep[0]}', '{keep[1]}', '{keep[2].replace(chr(39), chr(39) * 2)}', '{keep[3]}')")
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_a_digest_pin_that_is_not_the_data_is_a_FAIL(db, monkeypatch):
    d = _own()
    d["curated_corpus"][0]["digest"] = "0" * 64
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and ("digest" in got["Narr.agree"]["measured"])


def test_REAL_WRITER_MUTATION_a_vocabulary_word_dropped_from_the_declaration_is_a_FAIL(db, monkeypatch):
    d = _own()
    c = next(x for x in d["prose_none"]["closed_columns"] if x["column"] == "classical_citation")
    c["values"] = c["values"][:-1]
    assert _m(db, monkeypatch, d)["Narr.agree"]["v"] == FAIL
