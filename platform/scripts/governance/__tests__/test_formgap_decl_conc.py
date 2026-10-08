"""test_formgap_decl_conc.py: the FORM-GAP declarations of bg_concordance and bg_text_index are TRUE, shown on rows the REAL writers build (SS N-191, the scaled closed vocabulary).

Both assets close their text columns over the 481 reference topic tags. The 481 names / canonical ids in the declarations are compared with the reference seed's own generated list
(`brahmagyan.l0_reference.TOPIC_TAGS`, imported: a pure module), the seed is loaded into the REAL reference_topic_tags DDL and pinned by the md5 expression migration 607 carries, and the
real writers (bg_text_index classifies chunks, bg_concordance aggregates them) run on a throw-away PostgreSQL carrying the real DDL. The engine's own `_measure_prose` then reads each asset and all six
Narr / Null cells must read N/A through a checked block; every claim has a mutation that must turn the reading red.
"""
from __future__ import annotations

import itertools
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
from _formgap_support import NA, FAIL, NO_DET, CELLS  # noqa: E402

DECLS = ac.load_asset_declarations()
CW = "platform/python-sidecar/pipeline/orchestrator/writers/bg_concordance.py"
TW = "platform/python-sidecar/pipeline/orchestrator/writers/bg_text_index.py"
TABLES = ("classical_attributions", "classical_text_chunks", "classical_texts", "reference_topic_tags", "sutravali_rules")


def _own(aid):
    return json.loads(json.dumps(DECLS[aid]))


def _seed():
    pytest.importorskip("psycopg")
    import brahmagyan.l0_reference as R
    return R.TOPIC_TAGS


# ═════════════════════════════ the declared vocabularies are the seed's own ═════════════════════════════

def test_the_declared_names_ids_and_categories_are_the_reference_seeds_own_481_tags():
    tags = _seed()
    cn = {c["column"]: c for c in DECLS["bg_concordance"]["prose_none"]["closed_columns"]}
    assert len(tags) == 481
    assert cn["topic_canonical_name"]["values"] == [t["name"] for t in tags] and len(set(cn["topic_canonical_name"]["values"])) == 481
    assert cn["topic_category"]["values"] == ["placement", "lordship", "domain", "dasha", "transit"] == list(dict.fromkeys(t["category"] for t in tags))
    ti = DECLS["bg_text_index"]["prose_none"]["closed_columns"]
    assert [c["column"] for c in ti] == ["topic_tag"] and ti[0]["values"] == [t["canonical_id"] for t in tags] and len(set(ti[0]["values"])) == 481


def test_the_vocabularies_are_the_cross_products_the_seed_loops_state_written_out_by_hand():
    """481 = 108 planet-house + 108 planet-sign + 144 lordship + 90 domain + 25 dasha + 6 transit, spelled independently of the seed's code."""
    planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
    ords = ["1st", "2nd", "3rd"] + [f"{n}th" for n in range(4, 13)]
    signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    doms = ["career", "marriage", "wealth", "health", "progeny", "education", "longevity", "fame", "spirituality", "foreign_travel", "property", "vehicles", "litigation", "debts", "enemies",
            "father", "mother", "siblings", "friends", "speculation", "inheritance", "romance", "sexuality", "government", "politics", "arts", "research", "agriculture", "occult", "status"]
    want = [f"{p.title()} in the {o} house" for p, o in itertools.product(planets, ords)] + [f"{p.title()} in {s.title()}" for p, s in itertools.product(planets, signs)] \
        + [f"Lord of {a} in {b}" for a, b in itertools.product(ords, ords)] + [f"{d.title()} — {k}" for d, k in itertools.product(doms, ["general", "timing", "yoga"])] \
        + [f"{ds.title()} {p.title()} period" for ds, p in itertools.product(["vimshottari", "yogini", "ashtottari", "kalachakra", "chara_jaimini"], planets[:5])] \
        + [t.replace("_", " ").title() for t in ["sade_sati", "dhaiya", "saturn_transit", "jupiter_transit", "rahu_transit", "gochara_general"]]
    assert len(want) == 481 and len(set(want)) == 481
    assert sorted(want) == sorted(DECLS["bg_concordance"]["prose_none"]["closed_columns"][0]["values"])


def test_the_school_vocabulary_is_the_writers_map_plus_its_default():
    import ast
    tree = ast.parse((fs.REPO / CW).read_text(encoding="utf-8"))
    ts = next(n for n in tree.body if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", None) == "TEXT_SCHOOL")
    vals = set(ast.literal_eval(ts.value).values())
    school = next(c for c in DECLS["bg_concordance"]["prose_none"]["closed_columns"] if c["column"] == "school")
    assert set(school["values"]) == vals | {"parashari"} == {"parashari", "phaladeepika", "jaimini", "tajaka", "nadi"}


def test_the_declarations_are_sound_shapes():
    assert ac.prose_none_problem(DECLS["bg_concordance"]) is None and ac.prose_none_problem(DECLS["bg_text_index"]) is None
    assert DECLS["bg_text_index"]["prose_none"]["column_scope"] == "written" and "column_scope" not in DECLS["bg_concordance"]["prose_none"]
    assert [c["column"] for c in DECLS["bg_concordance"]["prose_none"]["identifier_columns"]] == ["topic_id"]


# ═════════════════════════════ the real DDL, the real seed, the real writers ═════════════════════════════

@pytest.fixture(scope="module")
def db(disposable_pg):
    pg = disposable_pg
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
    fs.drop_tables(pg, *TABLES)
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_texts.sql", "classical_texts"))
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_texts.sql", "classical_text_chunks"))
    # migration 177 adds topic_tag; migration 081 adds the vector column (pgvector is not in the throw-away cluster: an array of the same nullability stands in, it is never judged)
    fs.psql(pg, "ALTER TABLE classical_text_chunks ADD COLUMN IF NOT EXISTS topic_tag TEXT")
    fs.psql(pg, "ALTER TABLE classical_text_chunks ADD COLUMN IF NOT EXISTS embedding double precision[]")
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "178_l0_phase_alpha_reference_tables.sql", "reference_topic_tags"))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "081_l0fr_schema.sql", "sutravali_rules"))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "177_l0_phase_alpha_existing_table_schema.sql", "classical_attributions"))
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO reference_topic_tags (canonical_id, name, category, description, example_chunks) VALUES (%s, %s, %s, %s, %s)",
                        [(t["canonical_id"], t["name"], t["category"], t["description"], Jsonb(t["example_chunks"])) for t in _seed()])
    conn.close()
    for t in ["bphs", "bphs_jaimini", "bhrigu_nandi_nadi", "phaladeepika", "tajaka_neelakanthi"]:
        fs.psql(pg, f"INSERT INTO classical_texts (text_id, title_en, school, tradition, license) VALUES ('{t}', '{t}', 'fixture', 'vedic', 'public_domain')")
    chunks = [
        ("bphs", "Sun in the 1st house gives a person vigour and a commanding bearing."),
        ("bphs", "The Moon placed in the 4th house gives comfort and mother's affection."),
        ("bphs", "When Saturn is in Capricorn the native is patient and serious."),
        ("bphs", "The lord of the 1st house in the 10th house gives a rise through karma."),
        ("bphs", "Vimshottari dasha of Jupiter gives fruits of learning."),
        ("bphs_jaimini", "Sade sati begins when Saturn enters the twelfth sign from the Moon."),
        ("bphs_jaimini", "A marriage yoga combination in the scripture gives a happy spouse."),
        ("bhrigu_nandi_nadi", "Jupiter in the 5th house indicates children."),
        ("bhrigu_nandi_nadi", "Mars in Aries gives courage."),
        ("phaladeepika", "The sun in the 1st house makes one proud."),
        ("tajaka_neelakanthi", "A passage about nothing in particular that mentions no planet."),
        ("bphs", "Rahu transit through the sign gives gochara effects in the year."),
    ]
    for i, (t, txt) in enumerate(chunks):
        fs.psql(pg, f"INSERT INTO classical_text_chunks (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end, content_en, source_citation, embedding) VALUES "
                    f"('{t}', '{t}_c{i:03d}', 'CH1:V{i + 1}', 1, {i + 1}, {i + 1}, '{txt.replace(chr(39), chr(39) * 2)}', 'fixture citation', ARRAY[0.5])")
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    for t in ("bphs", "bphs_jaimini"):
        fs.psql(pg, f"INSERT INTO sutravali_rules (text_id, verse_ref) VALUES ('{t}', 'CH1:V1')")
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_text_index import TextIndexWriter
    from pipeline.orchestrator.writers.bg_concordance import ConcordanceWriter
    for aid, W in (("bg_text_index", TextIndexWriter), ("bg_concordance", ConcordanceWriter)):
        res = W().run(ContextSpec(asset_id=aid, build_id="11111111-1111-4111-8111-111111111111", db_conn=conn, config={}))
        assert res.rows_inserted > 0, (aid, res.notes)
    conn.close()
    yield pg
    fs.drop_tables(pg, *TABLES)


def test_REAL_DDL_the_seed_loaded_into_reference_topic_tags_is_the_md5_pin_of_migration_607(db):
    text = (fs.SMIG / "607_nirmana_bg_reference_integrity_contract.sql").read_text(encoding="utf-8")
    m = re.search(r"\(SELECT md5\(COALESCE\(string_agg\(jsonb_build_array\(canonical_id,name,category,description,example_chunks\)::text.*?FROM reference_topic_tags\)", text)
    assert m is not None and "7ad2a364dc208f9f8b9f2e131bbf8514" in m.group(0)
    assert fs.psql(db, f"SELECT {m.group(0)}").strip() == "t"
    assert fs.psql(db, "SELECT count(*), count(DISTINCT name), count(DISTINCT canonical_id) FROM reference_topic_tags").strip() == "481|481|481"


def test_REAL_WRITERS_the_fixture_run_produced_tags_and_attributions_in_several_families_and_schools(db):
    tags = set(fs.psql(db, "SELECT DISTINCT topic_tag FROM classical_text_chunks WHERE topic_tag IS NOT NULL").split())
    assert {"sun_in_1st", "moon_in_4th", "saturn_in_capricorn", "lord_1st_in_10th", "vimshottari_jupiter_dasha", "sade_sati", "marriage_yoga"} <= tags
    assert fs.psql(db, "SELECT count(*) FROM classical_text_chunks WHERE topic_tag IS NULL").strip() != "0"            # a chunk that matches nothing keeps NULL
    assert set(fs.psql(db, "SELECT DISTINCT school FROM classical_attributions").split()) == {"parashari", "jaimini", "nadi", "phaladeepika"}


def _m_conc(db, mp, decl=None):
    return fs.measure("bg_concordance", db, mp, ac.registered_ids("")["bg_concordance"], "classical_attributions", ["classical_attributions"], decl or _own("bg_concordance"), registry=dict(has_writer=True))


def _m_idx(db, mp, decl=None):
    return fs.measure("bg_text_index", db, mp, ac.registered_ids("")["bg_text_index"], "classical_text_chunks", ["classical_text_chunks"], decl or _own("bg_text_index"), registry=dict(has_writer=True))


def test_REAL_WRITER_bg_concordance_rows_read_na_on_all_six(db, monkeypatch):
    got = _m_conc(db, monkeypatch)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert {c["column"] for c in b["closed"]} == {"topic_canonical_name", "topic_category", "school", "match_method"} and b["identifier_columns"] == ["classical_attributions.topic_id"]
    assert any(f.get("column") == "topic_canonical_name" for f in b["forms"]["scaled_vocabulary"])                    # the 481-name vocabulary went through the scaled read


def test_REAL_WRITER_bg_text_index_reads_na_on_all_six_judging_only_the_column_it_writes(db, monkeypatch):
    got = _m_idx(db, monkeypatch)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert [c["column"] for c in b["closed"]] == ["topic_tag"] and b["column_scope"] == "written"


def test_REAL_WRITER_MUTATION_bg_text_index_without_the_written_scope_the_other_open_text_columns_fail(db, monkeypatch):
    d = _own("bg_text_index")
    del d["prose_none"]["column_scope"]
    got = _m_idx(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "content_en" in got["Narr.agree"]["measured"]


@pytest.mark.parametrize("sql,needle", [
    ("UPDATE classical_attributions SET topic_canonical_name = 'A free sentence about the Sun in the first house' WHERE attribution_id = (SELECT min(attribution_id) FROM classical_attributions)", "topic_canonical_name"),
    ("UPDATE classical_attributions SET topic_category = 'house_placement' WHERE attribution_id = (SELECT min(attribution_id) FROM classical_attributions)", "topic_category"),
    ("UPDATE classical_attributions SET school = 'lal-kitab' WHERE attribution_id = (SELECT min(attribution_id) FROM classical_attributions)", "school"),
    ("UPDATE classical_attributions SET match_method = 'keyword' WHERE attribution_id = (SELECT min(attribution_id) FROM classical_attributions)", "match_method"),
])
def test_REAL_WRITER_MUTATION_bg_concordance_a_value_outside_a_vocabulary_is_a_FAIL(db, monkeypatch, sql, needle):
    snap = fs.psql(db, "SELECT attribution_id || '|' || topic_canonical_name || '|' || topic_category || '|' || school || '|' || match_method FROM classical_attributions WHERE attribution_id = (SELECT min(attribution_id) FROM classical_attributions)").strip()
    aid, name, cat, school, mm = snap.split("|")
    try:
        fs.psql(db, sql)
        got = _m_conc(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:300]
    finally:
        fs.psql(db, f"UPDATE classical_attributions SET topic_canonical_name = '{name}', topic_category = '{cat}', school = '{school}', match_method = '{mm}' WHERE attribution_id = {aid}")
    assert _m_conc(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_bg_concordance_a_name_dropped_from_the_declared_vocabulary_is_a_FAIL(db, monkeypatch):
    d = _own("bg_concordance")
    used = fs.psql(db, "SELECT topic_canonical_name FROM classical_attributions LIMIT 1").strip()
    col = next(c for c in d["prose_none"]["closed_columns"] if c["column"] == "topic_canonical_name")
    col["values"] = [v for v in col["values"] if v != used]
    got = _m_conc(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "topic_canonical_name" in got["Narr.agree"]["measured"]


def test_REAL_WRITER_MUTATION_bg_text_index_a_tag_outside_the_reference_vocabulary_is_a_FAIL(db, monkeypatch):
    cid = fs.psql(db, "SELECT chunk_id FROM classical_text_chunks WHERE topic_tag IS NULL LIMIT 1").strip()
    try:
        fs.psql(db, f"UPDATE classical_text_chunks SET topic_tag = 'a_hand_typed_tag' WHERE chunk_id = '{cid}'")
        got = _m_idx(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "topic_tag" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db, f"UPDATE classical_text_chunks SET topic_tag = NULL WHERE chunk_id = '{cid}'")
    assert _m_idx(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_the_scaled_bound_refuses_a_flood_of_distinct_values(db, monkeypatch):
    """The live DISTINCT read of a closed column is bounded by the scaled cap (min(max(1.25 x 481, 300), 5000) = 602): a column holding more distinct values than that is not read as inside the vocabulary."""
    ac_cap = __import__("prose_forms").values_cap(481)
    assert ac_cap == 602
    d = _own("bg_text_index")
    try:
        fs.psql(db, "INSERT INTO classical_text_chunks (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end, content_en, source_citation, topic_tag) "
                    "SELECT 'bphs', 'flood_' || g, 'CH9:V' || g, 9, 1, 1, 'x', 'fixture citation', 'flood_tag_' || g FROM generate_series(1, 700) g")
        got = _m_idx(db, monkeypatch, d)
        assert got["Narr.agree"]["v"] == FAIL and "topic_tag" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db, "DELETE FROM classical_text_chunks WHERE chunk_id LIKE 'flood\\_%'")
    assert _m_idx(db, monkeypatch)["Narr.agree"]["v"] == NA


# ═════════════════════════════ the classifier can only return a reference tag ═════════════════════════════

def test_classify_chunk_returns_only_tags_of_the_loaded_vocabulary_or_nothing():
    from pipeline.orchestrator.writers import bg_text_index as T
    tags = frozenset(t["canonical_id"] for t in _seed())
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Surya", "Guru", "Shani"]
    houses = ["1st house", "second house", "seventh", "10th", "12th house", "lagna", "karma"]
    signs = ["Aries", "Capricorn", "Pisces", "mesha", "Leo"]
    extras = ["lord of the", "vimshottari dasha", "yogini period", "gochara", "transit of", "sade sati", "dhaiya", "marriage yoga", "career timing", "wealth", "health combination", "father", "foreign travel"]
    seen = set()
    n = 0
    for combo in itertools.chain(itertools.product(planets[:4], houses, extras[:5]), itertools.product(planets[4:], signs, extras[5:]), itertools.product(extras, houses, signs)):
        text = " ".join(combo)
        n += 1
        got = T.classify_chunk(text, tags)
        assert got is None or got in tags, (text, got)
        assert T.classify_chunk(text, frozenset()) is None, text                                  # an empty vocabulary can return nothing: no tag is invented outside valid_tags
        if got:
            seen.add(got)
        if n > 4000:
            break
    assert len(seen) >= 20, sorted(seen)
