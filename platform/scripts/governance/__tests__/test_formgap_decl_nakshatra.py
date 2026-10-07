"""test_formgap_decl_nakshatra.py: the FORM-GAP declaration of bg_nakshatra is TRUE, shown on rows the REAL writer builds (SS N-191).

bg_nakshatra writes three tables from the committed seed `brahmagyan/l0_nakshatra.py` (28 nakshatras, 108 padas, a 2,721-row compatibility matrix). The declaration closes every text column through:
  * per-key `values_from` of NAKSHATRAS_ENRICHED (the live nakshatra column may hold only the committed literals), explicit closed vocabularies for the pada and matrix tables,
  * `run_stamp_columns` on the three build_id TEXT columns, `templated_columns` on the matrix notes (four fixed templates), `unset_columns` on eight columns the seed never fills.
The vocabularies are compared with hand-derived sets here (independent of the seed code); the real writer runs on a throw-away PostgreSQL carrying the real DDL (migration 238); the engine's OWN
`_measure_prose` reads the three tables and all six Narr / Null cells must read N/A through a checked block. Every claim has a mutation that must turn the reading red.
"""
from __future__ import annotations

import itertools
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
from _formgap_support import RUN_1, RUN_2, NA, FAIL, NO_DET, CELLS  # noqa: E402

AID = "bg_nakshatra"
T1, T2, T3 = "reference_nakshatra", "reference_nakshatra_pada", "reference_nakshatra_matrix"
TABLES = [T1, T2, T3]
DECLS = ac.load_asset_declarations()
N = "platform/python-sidecar/brahmagyan/l0_nakshatra.py"
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
GRAHA7L = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _pn():
    return DECLS[AID]["prose_none"]


def _closed(table, column):
    return next(c for c in _pn()["closed_columns"] if c["column"] == column and (c.get("table") or T1) == table)


# ═════════════════════════════ the declaration is the shape it says ═════════════════════════════

def test_the_declaration_is_sound_and_names_every_form():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    pn = _pn()
    assert sorted((x.get("table") or T1, x["column"]) for x in pn["run_stamp_columns"]) == sorted([(T1, "build_id"), (T2, "build_id"), (T3, "build_id")])
    assert [(x["table"], x["column"]) for x in pn["templated_columns"]] == [(T3, "notes")]
    assert sorted((x.get("table") or T1, x["column"]) for x in pn["unset_columns"]) == sorted([(T1, "basis_above"), (T1, "basis_below"), (T1, "net_result")] + [(T2, c) for c in
                                                                                         ("bija_sound", "mantra_prefix", "pada_deity_nuance", "element_shading", "dosha_shading")])
    assert "transcription_columns" not in pn and "column_scope" not in pn                     # every text column of the three tables is judged; none is trusted by exemption


def test_every_values_from_names_the_committed_seed_by_its_per_key_literals():
    refs = [c["values_from"] for c in _pn()["closed_columns"] if c.get("values_from")]
    assert len(refs) == 30 and all(r["file"] == N for r in refs)
    assert {r["constants"][0] for r in refs if "constants" in r} == {"NAKSHATRAS_ENRICHED"} and [r for r in refs if "constant" in r] == [dict(file=N, constant="_AKSHARAS")]


# ═════════════════════════════ vocabularies against hand-derived sets ═════════════════════════════

def _resolved(table, column):
    return pf.resolve_values_from(fs.REPO, _closed(table, column)["values_from"])


def test_the_small_nakshatra_vocabularies_are_the_classical_words_stated_by_hand():
    want = {"gana": ["Deva", "Manushya", "Rakshasa"], "nadi": ["Adi", "Antya", "Madhya"], "guna": ["Rajas", "Sattva", "Tamas"], "tatva": ["Agni", "Akasha", "Jala", "Prithvi", "Vayu"],
            "varna": ["Brahmin", "Butcher", "Farmer", "Kshatriya", "Mleccha", "Shudra", "Vaishya"], "nakshatra_gender": ["Female", "Male", "Neutral"],
            "motivation": ["artha", "dharma", "kama", "moksha"], "paramayus": ["long", "medium", "short"], "disha": ["East", "North", "South", "West"],
            "muhurta_type": ["Chara", "Dhruva", "Kshipra", "Laghu", "Mishra", "Mridu", "Tikshna", "Ugra"],
            "tradition_scope": ["abhijit_28fold", "classical"],
            "yoni_en": ["Buffalo", "Cat", "Cow", "Dog", "Elephant", "Goat", "Hare", "Horse", "Lion", "Mongoose", "Monkey", "Rat", "Serpent", "Tiger"],
            "yoni_sa": ["Aja", "Ashva", "Gaja", "Go", "Mahisha", "Marjara", "Mushika", "Nakula", "Sarpa", "Shasha", "Shvana", "Simha", "Vanara", "Vyaghra"],
            "vimshottari_lord": sorted(GRAHA7L + ["rahu", "ketu"]), "ruling_planet": sorted(GRAHA7L + ["rahu", "ketu"])}
    for col, vals in want.items():
        assert _resolved(T1, col) == vals, col
    assert len(_resolved(T1, "pakshi")) == 22 and len(_resolved(T1, "name_en")) == 28 == len(_resolved(T1, "name_sa_iast")) == len(_resolved(T1, "name_sa_devanagari"))
    assert len(_resolved(T1, "alt_names")) == 46 and len(_resolved(T2, "pada_akshara")) == 91


def test_the_pada_vocabularies():
    assert _closed(T2, "pada_navamsa_sign")["values"] == SIGNS and _closed(T2, "pada_lord")["values"] == ["mars", "venus", "mercury", "moon", "sun", "jupiter", "saturn"]
    assert _closed(T2, "tradition_scope")["values"] == ["classical"] and _closed(T2, "classical_source")["values"] == ["bphs:ch92 + muhurta_chintamani:ch7"]


def test_the_matrix_vocabularies_are_derived_by_hand_from_the_twelve_kuta_structures():
    nums27 = [str(i) for i in range(1, 28)]
    gana, nadi = ["Deva", "Manushya", "Rakshasa"], ["Adi", "Madhya", "Antya"]
    yoni = ["Horse", "Elephant", "Goat", "Serpent", "Dog", "Cat", "Rat", "Cow", "Buffalo", "Tiger", "Hare", "Mongoose", "Monkey", "Lion"]
    varna = ["Brahmin", "Kshatriya", "Vaishya", "Shudra", "Farmer", "Butcher", "Mleccha"]
    vashya = ["Dwipada", "Chaturpada", "Jalasheela", "Keeta", "Vanachara"]
    rajju = ["Padha_Aroha", "Padha_Avaroha", "Kati_Aroha", "Kati_Avaroha", "Nabhi_Aroha", "Nabhi_Avaroha", "Kantha_Aroha", "Kantha_Avaroha", "Shira"]
    frm = set(nums27 + gana + nadi + yoni + varna + GRAHA7L + vashya)
    assert len(frm) == 66 and set(_closed(T3, "from_key")["values"]) == frm
    assert set(_closed(T3, "to_key")["values"]) == frm | set(rajju) and len(_closed(T3, "to_key")["values"]) == 75
    assert sorted(_closed(T3, "matrix_type")["values"]) == sorted(["gana_kuta", "nadi_kuta", "yoni_kuta", "tara_kuta", "rajju", "varna_kuta", "graha_maitri_kuta", "bhakoot_kuta", "vedha", "vashya_kuta", "mahendra", "stree_deergha"])
    rel = ({"Janma", "Sampat", "Vipat", "Kshema", "Pratyari", "Sadhaka", "Vadha", "Mitra", "Atimitra"} | {"compatible", "incompatible", "nadi_dosha", "same_yoni", "enemy", "friendly"}
           | {"aroha", "avaroha", "both", "mahendra", "non_mahendra", "dosha", "ok", "vedha_pair"} | {f"{a}_{b}" for a, b in itertools.product(("friend", "neutral", "enemy"), repeat=2)}
           | {f"{d}/{(12 - d) % 12 or 12}" for d in range(1, 13)})
    assert set(_closed(T3, "relation_value")["values"]) == rel and len(rel) == 44
    assert _closed(T3, "classical_source")["values"] == ["bphs:ch73"] and _closed(T3, "tradition_scope")["values"] == ["classical"]


def test_the_note_templates_and_their_placeholders():
    t = _pn()["templated_columns"][0]
    assert t["templates"] == ["dist={d},pos={p}", "nakshatra_id={n} → rajju '{r}'", "dist={d}", "min_dist={d}"]
    assert t["placeholders"]["d"] == {"class": "int"} and t["placeholders"]["r"]["values"] == ["Padha_Aroha", "Padha_Avaroha", "Kati_Aroha", "Kati_Avaroha", "Nabhi_Aroha", "Nabhi_Avaroha", "Kantha_Aroha", "Kantha_Avaroha", "Shira"]


# ═════════════════════════════ the real writer on the real DDL ═════════════════════════════

@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    pg = disposable_pg
    fs.install_run_tables(pg)
    fs.drop_tables(pg, *TABLES)
    for t in TABLES:
        fs.psql(pg, fs.create_table_ddl(fs.SMIG / "238_bg_nakshatra_tables.sql", t))
    fs.add_run(pg, RUN_1, AID)
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_nakshatra import NakshatraReferenceWriter
    conn = psycopg.connect(pg.url, autocommit=True)
    res = NakshatraReferenceWriter().run(ContextSpec(asset_id=AID, build_id=RUN_1, db_conn=conn, config={}))
    conn.close()
    assert res.rows_inserted == 28 + 108 + 2721, res.notes
    yield pg
    fs.drop_tables(pg, *TABLES, "asset_provenance_receipts", "build_run_assets", "build_runs", "charts", "asset_registry")


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T1, TABLES, decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_the_three_tables_read_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    f = got["Narr.agree"]["prose_none"]["forms"]
    assert sorted((x["table"], x["column"]) for x in f["run_stamp"]) == sorted((t, "build_id") for t in TABLES)
    assert [(x["table"], x["column"]) for x in f["templated"]] == [(T3, "notes")] and len(f["unset"]) == 8 and all(x["empty"] for x in f["unset"])
    assert len(f["values_from"]) == 30


def test_REAL_WRITER_the_live_columns_are_exactly_the_committed_seed_vocabularies(db):
    """Data equals the vocabulary: the resolved seed literals are the DISTINCT values the real writer stored (no word the seed lacks, none missing)."""
    for col in ("gana", "nadi", "guna", "tatva", "varna", "pakshi", "muhurta_type", "yoni_en", "name_en", "symbol", "shakti", "deity_domain", "presiding_deity"):
        live = sorted(x for x in fs.psql(db, f"SELECT DISTINCT {col} FROM {T1} WHERE {col} IS NOT NULL").split("\n") if x)
        assert live == _resolved(T1, col), col
    live = sorted(x for x in fs.psql(db, f"SELECT DISTINCT pada_akshara FROM {T2}").split("\n") if x)
    assert live == _resolved(T2, "pada_akshara")
    for col in ("matrix_type", "from_key", "to_key", "relation_value"):
        live = sorted(x for x in fs.psql(db, f"SELECT DISTINCT {col} FROM {T3}").split("\n") if x)
        assert live == sorted(_closed(T3, col)["values"]), col


@pytest.mark.parametrize("sql,needle", [
    (f"UPDATE {T1} SET symbol = 'A winged horse that the writer composed' WHERE nakshatra_id = 1", "symbol"),
    (f"UPDATE {T1} SET shakti = 'a new power sentence' WHERE nakshatra_id = 2", "shakti"),
    (f"UPDATE {T1} SET alt_names = ARRAY['Made-up name'] WHERE nakshatra_id = 3", "alt_names"),
    (f"UPDATE {T1} SET favorable_acts = ARRAY['a free activity'] WHERE nakshatra_id = 4", "favorable_acts"),
    (f"UPDATE {T1} SET gana = 'Asura' WHERE nakshatra_id = 5", "gana"),
    (f"UPDATE {T1} SET degree_in_rashi_ranges = '[{{\"rashi\": \"Zodiac\", \"start_in_rashi\": 0, \"end_in_rashi\": 1}}]'::jsonb WHERE nakshatra_id = 6", "degree_in_rashi_ranges"),
    (f"UPDATE {T1} SET net_result = 'a verdict about the net result' WHERE nakshatra_id = 7", "net_result"),
    (f"UPDATE {T1} SET basis_below = '' WHERE nakshatra_id = 8", "basis_below"),
    (f"UPDATE {T2} SET pada_akshara = 'Zzz' WHERE pada_id = 1", "pada_akshara"),
    (f"UPDATE {T2} SET pada_lord = 'pluto' WHERE pada_id = 2", "pada_lord"),
    (f"UPDATE {T2} SET bija_sound = 'om' WHERE pada_id = 3", "bija_sound"),
    (f"UPDATE {T2} SET element_shading = 'fiery' WHERE pada_id = 4", "element_shading"),
    (f"UPDATE {T3} SET relation_value = 'maybe' WHERE id = (SELECT min(id) FROM {T3})", "relation_value"),
    (f"UPDATE {T3} SET from_key = 'Sun' WHERE id = (SELECT min(id) FROM {T3})", "from_key"),
    (f"UPDATE {T3} SET notes = 'a note the writer never builds' WHERE notes IS NOT NULL AND id = (SELECT min(id) FROM {T3} WHERE notes IS NOT NULL)", "notes"),
    (f"UPDATE {T3} SET notes = 'dist=3,pos=x' WHERE id = (SELECT min(id) FROM {T3} WHERE notes LIKE 'dist=%,pos=%')", "notes"),
    (f"UPDATE {T3} SET classical_source = 'bphs:ch99' WHERE id = (SELECT min(id) FROM {T3})", "classical_source"),
    (f"UPDATE {T1} SET build_id = 'manual-rebuild' WHERE nakshatra_id = 9", "build_id"),
    (f"UPDATE {T3} SET build_id = 'manual' WHERE id = (SELECT min(id) FROM {T3})", "build_id"),
])
def test_REAL_WRITER_MUTATION_a_value_outside_its_form_is_a_FAIL(db, monkeypatch, sql, needle):
    table = sql.split("UPDATE ")[1].split(" ")[0]
    pk = {T1: "nakshatra_id", T2: "pada_id", T3: "id"}[table]
    col = sql.split(" SET ")[1].split(" = ")[0]
    where_pk = sql.split("WHERE ", 1)[1]
    snap = fs.psql(db, f"SELECT {pk}::text || '|' || coalesce({col}::text, '<NIL>') FROM {table} WHERE {pk} = ({'SELECT ' + pk + ' FROM ' + table + ' WHERE ' + where_pk + ' LIMIT 1'})").strip()
    rid, old = snap.split("|", 1)
    try:
        fs.psql(db, sql)
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    finally:
        val = "NULL" if old == "<NIL>" else "'" + old.replace("'", "''") + "'"
        cast = {"alt_names": "::text[]", "favorable_acts": "::text[]", "degree_in_rashi_ranges": "::jsonb"}.get(col, "")
        fs.psql(db, f"UPDATE {table} SET {col} = {val}{cast} WHERE {pk} = {rid}")
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_a_uuid_no_run_of_the_asset_holds_is_no_detector_not_pass(db, monkeypatch):
    fs.psql(db, f"UPDATE {T2} SET build_id = '{RUN_2}' WHERE pada_id = 1")
    try:
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == NO_DET and "no run id of this asset" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db, f"UPDATE {T2} SET build_id = '{RUN_1}' WHERE pada_id = 1")
    fs.add_run(db, RUN_2, AID)                                                         # the same stamp, now a run of this asset: resolved
    fs.psql(db, f"UPDATE {T2} SET build_id = '{RUN_2}' WHERE pada_id = 1")
    try:
        assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA
    finally:
        fs.psql(db, f"UPDATE {T2} SET build_id = '{RUN_1}' WHERE pada_id = 1")
        fs.psql(db, f"DELETE FROM build_run_assets WHERE run_id = '{RUN_2}'")
        fs.psql(db, f"DELETE FROM build_runs WHERE id = '{RUN_2}'")


def test_REAL_WRITER_MUTATION_a_vocabulary_word_dropped_from_the_declaration_is_a_FAIL(db, monkeypatch):
    d = _own()
    c = next(x for x in d["prose_none"]["closed_columns"] if x["column"] == "relation_value")
    c["values"] = [v for v in c["values"] if v != "Janma"]
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "relation_value" in got["Narr.agree"]["measured"]


def test_REAL_WRITER_MUTATION_without_the_forms_the_asset_is_open_text_and_the_old_no_go(db, monkeypatch):
    d = _own()
    pn = d["prose_none"]
    for k in ("run_stamp_columns", "templated_columns", "unset_columns"):
        pn.pop(k)
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL
    for col in ("build_id", "notes", "basis_above", "bija_sound"):
        assert col in got["Narr.agree"]["measured"], col                                  # the very columns the five forms exist for are what stays open
