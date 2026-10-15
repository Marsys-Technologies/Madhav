"""test_formgap_decl_dignity.py: the FORM-GAP declaration of bg_dignity_reference is TRUE, shown on rows the REAL writer builds (SS N-191 / N-192).

Five tables seeded by the writer from literals (DIGNITY_REFERENCE in `brahmagyan/l0_dignity_reference.py`; four tuple / dict tables in the writer module): word columns are closed (per-key `values_from` of the seed
where the seed is dict displays, explicit lists where it is tuples), two jsonb columns are closed at their string leaves (the avastha rule at four declared paths, variant_traditions by its 14 literals), and the
four note columns are hand-curated corpora pinned by count and sha256. The real writer runs on a throw-away PostgreSQL carrying the real DDL (migrations 250 and 330); the engine's OWN `_measure_prose` reads all
five tables and the six cells must read N/A through a checked block. The tuple-seeded pins are also checked here against the seed OBJECT (the per-key AST read cannot name tuple items). Every claim has a mutation.
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

AID = "bg_dignity_reference"
T1, T2, T3, T4, T5 = "bg_dignity_reference", "bg_graha_naisargika_friendship", "bg_avastha_schemes", "bg_motion_state_thresholds", "bg_combustion_orbs"
TABLES = [T1, T2, T3, T4, T5]
DECLS = ac.load_asset_declarations()
RUN = "11111111-1111-4111-8111-111111111111"
GRAHA9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _closed(table, col):
    return next(c for c in DECLS[AID]["prose_none"]["closed_columns"] if c["column"] == col and (c.get("table") or T1) == table)


def _cc(table, col):
    return next(c for c in DECLS[AID]["curated_corpus"] if c["table"] == table and c["column"] == col)


def test_the_declaration_is_sound_and_names_its_forms():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and ac.curated_corpus_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    assert [(c["table"], c["column"], c["count"], bool(c.get("seed"))) for c in e["curated_corpus"]] == [(T1, "notes", 2, True), (T3, "notes", 35, False), (T4, "notes", 27, True), (T5, "retrograde_note", 4, False)]
    assert [e2 for e2 in e["produced_tables"]] == [{"table": t} for t in TABLES]


def test_the_pins_are_the_seed_objects_digests_including_the_tuple_seeds():
    import pipeline.orchestrator.writers.bg_dignity_reference as W
    from brahmagyan.l0_dignity_reference import DIGNITY_REFERENCE as DR
    assert pf.corpus_digest([r["notes"] for r in DR if r.get("notes")]) == _cc(T1, "notes")["digest"]
    assert pf.corpus_digest([t[5] for t in W._AVASTHA_SCHEMES if t[5]]) == _cc(T3, "notes")["digest"] and len([t for t in W._AVASTHA_SCHEMES if t[5]]) == 35
    assert pf.corpus_digest([r["notes"] for r in W._MOTION_STATE_THRESHOLDS if r.get("notes")]) == _cc(T4, "notes")["digest"]
    assert pf.corpus_digest([t[3] for t in W._COMBUSTION_ORBS if t[3]]) == _cc(T5, "retrograde_note")["digest"] and len([t for t in W._COMBUSTION_ORBS if t[3]]) == 4


def test_the_explicit_vocabularies_are_the_hand_stated_classical_words():
    assert _closed(T2, "graha")["values"] == GRAHA9 and sorted(_closed(T2, "other_graha")["values"]) == sorted(GRAHA9) and sorted(_closed(T2, "relation")["values"]) == ["enemy", "friend", "neutral"]
    assert sorted(_closed(T3, "scheme_name")["values"]) == sorted(["baladi", "jagradadi", "deeptaadi", "lajjitaadi", "sayanadi"]) and len(_closed(T3, "state_name")["values"]) == 34
    assert sorted(_closed(T4, "motion_state")["values"]) == sorted(["sama", "atichara", "vakra", "anuvakra", "manda"]) and sorted(_closed(T4, "threshold_type")["values"]) == ["above", "always", "below", "range"]
    assert _closed(T4, "graha")["values"] == GRAHA9 and _closed(T5, "graha")["values"] == ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"] and _closed(T4, "classical_citation")["values"] == ["SS / Saravali"]
    r = lambda c: pf.resolve_values_from(fs.REPO, _closed(T1, c)["values_from"])
    assert r("graha") == sorted(GRAHA9) and r("exaltation_sign") == sorted(["Aries", "Taurus", "Cancer", "Virgo", "Pisces", "Capricorn"]) or len(r("exaltation_sign")) >= 6
    assert set(r("own_signs")) == {"Aries", "Scorpio", "Taurus", "Libra", "Gemini", "Virgo", "Cancer", "Leo", "Sagittarius", "Pisces", "Capricorn", "Aquarius"}


def test_the_avastha_rule_paths_cover_every_string_leaf_of_the_seed_rules():
    import pipeline.orchestrator.writers.bg_dignity_reference as W
    pats = {p["path"]: set(p["values"]) for p in _closed(T3, "determination_rule")["json_leaf_patterns"]}
    seen = {}

    def walk(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, path + "." + k)
        elif isinstance(x, list):
            for v in x:
                walk(v, path + "[*]")
        elif isinstance(x, str):
            key = "$.dignity_map.*" if path.startswith("$.dignity_map.") else path
            seen.setdefault(key, set()).add(x)
    for t in W._AVASTHA_SCHEMES:
        walk(json.loads(t[3]), "$")
    assert set(seen) == set(pats) and all(seen[k] <= pats[k] for k in seen)
    assert sorted(pats["$.dignity_map.*"]) == ["jagrata", "sushupti", "svapna"]


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    pg = disposable_pg
    fs.drop_tables(pg, *TABLES)
    for t in TABLES:
        fs.psql(pg, fs.create_table_ddl(fs.MIG / "250_bg_dignity_reference.sql", t))
    fs.psql(pg, "ALTER TABLE bg_dignity_reference ADD COLUMN IF NOT EXISTS variant_traditions JSONB DEFAULT NULL")            # migration 330
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_dignity_reference import BgDignityReferenceWriter
    conn = psycopg.connect(pg.url, autocommit=True)
    res = BgDignityReferenceWriter().run(ContextSpec(asset_id=AID, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert res.rows_inserted == 151, res.notes
    yield pg
    fs.drop_tables(pg, *TABLES)


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T1, TABLES, decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_the_five_tables_read_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    f = got["Narr.agree"]["prose_none"]["forms"]
    assert sorted((x["table"], x["column"], x["count"]) for x in f["curated"]) == sorted([(T1, "notes", 2), (T3, "notes", 35), (T4, "notes", 27), (T5, "retrograde_note", 4)])


def test_REAL_WRITER_the_live_per_key_columns_equal_the_seed_words(db):
    for c in ("graha", "exaltation_sign", "debilitation_sign", "moolatrikona_sign"):
        live = sorted(x for x in fs.psql(db, f"SELECT DISTINCT {c} FROM {T1} WHERE {c} IS NOT NULL").split("\n") if x)
        assert live == pf.resolve_values_from(fs.REPO, _closed(T1, c)["values_from"]), c


# (table, primary key, column, new value, cast, needle)
MUTS = [
    (T1, "graha", "exaltation_sign", "'Atlantis'", "", "exaltation_sign"),
    (T1, "graha", "own_signs", "ARRAY['Atlantis']", "::text[]", "own_signs"),
    (T1, "graha", "notes", "'A note about dignity typed by hand later'", "", "notes"),
    (T1, "graha", "variant_traditions", "'[{\"sign\": \"Taurus\", \"source\": \"A source line nobody declared\", \"authority\": \"primary\", \"label\": \"Parashari mainstream\"}]'::jsonb", "::jsonb", "variant_traditions"),
    (T2, "id", "classical_citation", "'A citation nobody declared'", "", "classical_citation"),
    (T3, "id", "state_name", "'asleep'", "", "state_name"),
    (T3, "id", "determination_rule", "'{\"type\": \"degree_in_sign\", \"note\": \"A free sentence in the rule\"}'::jsonb", "::jsonb", "determination_rule"),
    (T3, "id", "determination_rule", "'{\"type\": \"made_up_rule_type\"}'::jsonb", "::jsonb", "determination_rule"),
    (T3, "id", "notes", "'A state note typed later'", "", "notes"),
    (T4, "id", "notes", "'A motion note typed later'", "", "notes"),
    (T5, "id", "graha", "'Pluto'", "", "graha"),
    (T5, "id", "retrograde_note", "'A retrograde remark typed later'", "", "retrograde_note"),
]


@pytest.mark.parametrize("table,pk,col,newv,cast,needle", MUTS)
def test_REAL_WRITER_MUTATION_a_value_outside_its_form_is_a_FAIL(db, monkeypatch, table, pk, col, newv, cast, needle):
    where = "retrograde_note IS NOT NULL" if col == "retrograde_note" else ("notes IS NOT NULL" if col == "notes" and table == T1 else "true")

    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, table, pk, col, newv, where, check, cast=cast)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_a_corpus_pin_that_is_not_the_data_is_a_FAIL(db, monkeypatch):
    for k in range(4):
        d = _own()
        d["curated_corpus"][k]["digest"] = "a" * 64
        got = _m(db, monkeypatch, d)
        assert got["Narr.agree"]["v"] == FAIL, k


def test_REAL_WRITER_MUTATION_a_note_written_into_a_row_that_had_none_is_drift_the_count_grows(db, monkeypatch):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "added" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, T5, "id", "retrograde_note", "'A fifth retrograde note typed later'", "retrograde_note IS NULL", check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


@pytest.mark.parametrize("table,col", [(T2, "relation"), (T4, "motion_state")])
def test_REAL_WRITER_MUTATION_a_word_dropped_from_a_check_constrained_vocabulary_is_a_FAIL(db, monkeypatch, table, col):
    """The real DDL's CHECK forbids a stray word in these two columns, so the closure is exercised from the other side: the declaration loses a word the data uses."""
    d = _own()
    c = next(x for x in d["prose_none"]["closed_columns"] if x["column"] == col and x.get("table") == table)
    c["values"] = c["values"][:-1]
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and col in got["Narr.agree"]["measured"]
