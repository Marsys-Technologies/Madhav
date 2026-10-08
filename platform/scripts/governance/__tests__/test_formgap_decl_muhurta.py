"""test_formgap_decl_muhurta.py: the FORM-GAP declaration of bg_muhurta_lattice is TRUE, shown on rows the REAL writer code builds (SS N-191, the leaf-pattern cap that scales).

`detail` is a jsonb record of table words and two timestamps: 26 string-leaf paths (24 closed vocabularies stated in the declaration, two iso8601_timestamp kinds). The vocabularies are compared with the
panchang_engine tables and with small hand-stated literals; the real `compute_day_factors` and the writer's own `_to_insert_dict` / `_flush_batch` run on a throw-away PostgreSQL carrying the real DDL
(migrations 484 and 530) for 450 days; the engine's OWN `_measure_prose` then reads the asset and all six Narr / Null cells must read N/A through a checked block. The Swiss .se1 file guard of
`run_substep` (files not available offline) is the only thing skipped: the computation runs on the Moshier fallback and the vocabularies do not depend on the ephemeris. Every claim has a mutation.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys
import uuid

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

AID = "bg_muhurta_lattice"
DECLS = ac.load_asset_declarations()
W = "platform/python-sidecar/pipeline/orchestrator/writers/bg_muhurta_lattice.py"
GRAHA7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
DIRS = ["East", "North", "South", "West"]
DAYS = 450
START = dt.date(2026, 8, 1)


def _own(aid=AID):
    return json.loads(json.dumps(DECLS[aid]))


def _cols():
    return {c["column"]: c for c in DECLS[AID]["prose_none"]["closed_columns"]}


def _paths():
    return {p["path"]: p for p in _cols()["detail"]["json_leaf_patterns"]}


# ═════════════════════════════ the declaration and the engine tables agree ═════════════════════════════

def test_the_declaration_is_sound_and_the_pattern_count_is_inside_the_scaled_cap():
    assert ac.prose_none_problem(DECLS[AID]) is None and DECLS[AID]["prose_fields"] == []
    n = len(_paths())
    assert n == 26 and pf.leaf_pattern_cap(n) == 33 and pf.leaf_pattern_cap(n) <= ac.PROSE_NONE_MAX_LEAF_PATTERNS == 64


def test_small_vocabularies_are_the_hand_stated_words():
    p, c = _paths(), _cols()
    assert c["factor_family"]["values"] == ["agnivasa", "combination_yoga", "kalam", "ghati_muhurta", "hora", "vara", "nakshatra", "tithi", "lagna"]
    assert c["reference_location_key"]["values"] == ["bhubaneswar"] and c["ayanamsha_key"]["values"] == ["lahiri"]
    assert sorted(c["corpus_status"]["values"]) == ["computed_cited", "computed_uncited_convention"]
    assert sorted(c["sampling_method"]["values"]) == sorted(["muhurta_lattice_agnivasa_yoga_kalam_ghati_hora_vara_nakshatra_tithi_lagna_v2", "muhurta_lattice_agnivasa_yoga_kalam_ghati_v1"])
    assert p["$.convention"]["values"] == ["A_agni_vasa_table", "B_mc_arithmetic"] and p["$.paksha"]["values"] == ["shukla", "krishna"] and p["$.period"]["values"] == ["day", "night"]
    for k in ("$.valence", "$.strength", "$.category"):
        assert p[k]["values"] == ["auspicious", "inauspicious"]
    assert p["$.quality"]["values"] == ["auspicious", "neutral"] and p["$.element"]["values"] == ["Akasha", "Jala", "Patala", "Prithvi", "Vayu"]
    for k in ("$.chandra_vasa", "$.rahu_vasa", "$.disha_vasa", "$.nakshatra_vasa"):
        assert p[k]["values"] == DIRS
    assert p["$.bhadra_vasa"]["values"] == ["Jala", "Madhya", "Prishtha", "Simha", "Svarga"]
    assert p["$.lord"]["values"] == GRAHA7 == p["$.vara_lord"]["values"]
    assert p["$.name_sanskrit"]["values"] == p["$.vara_name"]["values"] == ["Ravivara", "Somavara", "Mangalavara", "Budhavara", "Guruvara", "Shukravara", "Shanivara"]
    assert p["$.name_english"]["values"] == ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    assert p["$.sign_name"]["values"] == ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]
    assert p["$.anga_true_end_utc"] == {"path": "$.anga_true_end_utc", "kind": "iso8601_timestamp"} and p["$.graha_positions_at"]["kind"] == "iso8601_timestamp"
    assert p["$.span_convention"]["values"] == ["hindu_day_sunrise_to_next_sunrise", "true_anga_interval_clipped_to_hindu_day", "hindu_day_sunrise_to_next_sunrise_anga_at_sunrise"]   # WFIX-B: the last is the older word 66 past rows hold


def test_the_table_vocabularies_are_the_engines_own_tables():
    pytest.importorskip("swisseph")      # the governance CI environment has no swisseph (precedent: test_c1_3_carriage_d3.py); runs wherever the sidecar image does
    import panchang_engine.shastra_tables as S
    p = _paths()
    assert p["$.tithi_name"]["values"] == [S.TITHI_NAMES[i] for i in sorted(S.TITHI_NAMES)] and len(p["$.tithi_name"]["values"]) == 30
    assert p["$.name"]["values"] == p["$.tithi_name"]["values"] + list(S.NAKSHATRA_NAMES) and len(S.NAKSHATRA_NAMES) == 27
    assert set(p["$.element"]["values"]) == set(S.AGNI_VASA_TABLE.values()) | {"Prithvi", "Akasha", "Patala"}
    for k, t in (("$.chandra_vasa", S.CHANDRA_VASA_TABLE), ("$.rahu_vasa", S.RAHU_VASA_TABLE), ("$.disha_vasa", S.DISHA_SHUL_TABLE), ("$.nakshatra_vasa", S.NAKSHATRA_VASA_TABLE), ("$.bhadra_vasa", S.BHADRA_VASA_TABLE)):
        assert set(p[k]["values"]) == set(t.values()), k
    assert set(S.VARA_HORA_START.values()) == set(GRAHA7) == set(S.SIGN_LORDS) and p["$.sign_name"]["values"] == list(S.SIGN_NAMES)


def test_the_note_and_convention_words_are_the_writers_own_literals():
    src = (fs.REPO / W).read_text(encoding="utf-8")
    assert p_note() in src.replace('"\n                    "', "") or "Deliberately null" in src
    for w in ("A_agni_vasa_table", "B_mc_arithmetic", "ADJUDICATION-16: NOT native lineage; comparison only", "hindu_day_sunrise_to_next_sunrise", "true_anga_interval_clipped_to_hindu_day", "bhubaneswar", "lahiri"):
        assert w in src, w
    assert 'SAMPLING_METHOD_VERSION = (\n    "muhurta_lattice_agnivasa_yoga_kalam_ghati_"\n    "hora_vara_nakshatra_tithi_lagna_v2"\n)' in src


def p_note():
    """WFIX-B: the note leaf is pinned by sha256 (the current sentence and the longer one an earlier writer version left on 430 rows); this is the current writer's own sentence, hashed."""
    import hashlib
    cur = "Deliberately null (§N.5). Resolve dignity at query time against bg_dignity_reference and dṛṣṭi against BPHS Ch.26."
    assert hashlib.sha256(cur.encode("utf-8")).hexdigest() in _paths()["$.strength_verdict_note"]["sha256"]
    return cur[:20]


# ═════════════════════════════ the real writer code on the real DDL ═════════════════════════════

@pytest.fixture(scope="module")
def built():
    pytest.importorskip("swisseph")
    from pipeline.orchestrator.writers import bg_muhurta_lattice as B
    rows = []
    for i in range(DAYS):
        rows.extend(B.compute_day_factors(START + dt.timedelta(days=i)))
    return B, rows


@pytest.fixture(scope="module")
def db(disposable_pg, built):
    psycopg = pytest.importorskip("psycopg")
    B, rows = built
    pg = disposable_pg
    fs.drop_tables(pg, AID)
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "484_bg_muhurta_lattice.sql", AID))
    mig530 = re.sub(r"--[^\n]*", "", (fs.SMIG / "530_bg_muhurta_lattice_panchangika_families.sql").read_text(encoding="utf-8"))
    alters = re.findall(r"ALTER TABLE bg_muhurta_lattice.*?;", mig530, re.S)
    assert len(alters) == 2
    for stmt in alters:
        fs.psql(pg, stmt)                                                                  # the migration's own widening of the family CHECK to nine families
    conn = psycopg.connect(pg.url, autocommit=True)
    build_id = str(uuid.UUID(int=7))
    with conn.cursor() as cur:
        batch = []
        for r in rows:
            batch.append(B.BgMuhurtaLatticeWriter._to_insert_dict(r, build_id))
            if len(batch) >= 2000:
                B.BgMuhurtaLatticeWriter._flush_batch(cur, batch)
                batch = []
        if batch:
            B.BgMuhurtaLatticeWriter._flush_batch(cur, batch)
    conn.close()
    yield pg
    fs.drop_tables(pg, AID)


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], AID, [AID], decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_CODE_the_450_day_lattice_has_all_nine_families(db, built):
    fams = set(fs.psql(db, f"SELECT DISTINCT factor_family FROM {AID}").split())
    assert fams == set(_cols()["factor_family"]["values"])
    assert int(fs.psql(db, f"SELECT count(*) FROM {AID}").strip()) == len(built[1])


def test_REAL_WRITER_CODE_every_string_leaf_the_writer_builds_is_inside_its_declared_vocabulary_by_an_independent_python_walk(built):
    """Independent of the engine's SQL closure: the same rows walked in Python."""
    _, rows = built
    decl = _paths()
    seen = {}
    for r in rows:
        for k, v in r.detail.items():
            if isinstance(v, str):
                seen.setdefault("$." + k, set()).add(v)
            elif isinstance(v, (dict, list)):
                assert k in ("graha_sign_ids",) and all(isinstance(x, int) for x in v.values()), (k, v)       # the one nested object holds integers only
    assert set(seen) <= set(decl), sorted(set(seen) - set(decl))
    for path, vals in seen.items():
        spec = decl[path]
        if "values" in spec:
            assert vals <= set(spec["values"]), (path, sorted(vals - set(spec["values"])))
        elif "sha256" in spec:                                                                                  # WFIX-B: a pinned sentence (the note leaf)
            import hashlib
            assert {hashlib.sha256(v.encode("utf-8")).hexdigest() for v in vals} <= set(spec["sha256"]), path
        else:
            assert all(re.match(ac.PROSE_NONE_LEAF_KINDS[spec["kind"]], v) for v in vals), path
    assert set(seen) == set(decl), sorted(set(decl) - set(seen))                                          # every declared path really occurs: no dead pattern


def test_REAL_WRITER_CODE_the_lattice_reads_na_on_all_six_through_the_leaf_patterns(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert "bg_muhurta_lattice.factor_key" in b["identifier_columns"] and {c["column"] for c in b["closed"]} >= {"factor_family", "sampling_method", "corpus_status"}
    assert "detail" in {c["column"] for c in b["closed"]}


def _restore_after(db, sql_mut, check):
    """Apply one mutation to a single row and always put it back, by the primary key."""
    rid, snap = fs.psql(db, f"SELECT id || '|' || detail::text || '|' || sampling_method || '|' || corpus_status || '|' || reference_location_key || '|' || ayanamsha_key FROM {AID} WHERE factor_family = 'tithi' ORDER BY id LIMIT 1").strip().split("|", 1)
    detail, sm, cs, rl, ay = snap.rsplit("|", 4)
    try:
        fs.psql(db, sql_mut.replace("<ID>", rid))
        check()
    finally:
        fs.psql(db, f"UPDATE {AID} SET detail = '{detail.replace(chr(39), chr(39) * 2)}'::jsonb, sampling_method = '{sm}', corpus_status = '{cs}', reference_location_key = '{rl}', ayanamsha_key = '{ay}' WHERE id = {rid}")


@pytest.mark.parametrize("mut,needle", [
    ("UPDATE bg_muhurta_lattice SET detail = jsonb_set(detail, '{paksha}', '\"a free sentence about the waxing fortnight\"') WHERE id = <ID>", "detail"),
    ("UPDATE bg_muhurta_lattice SET detail = detail || '{\"note\": \"a free sentence the writer never builds\"}'::jsonb WHERE id = <ID>", "detail"),
    ("UPDATE bg_muhurta_lattice SET detail = jsonb_set(detail, '{anga_true_end_utc}', '\"tomorrow afternoon\"') WHERE id = <ID>", "detail"),
    ("UPDATE bg_muhurta_lattice SET detail = jsonb_set(detail, '{name}', '\"Krishna Fortnight\"') WHERE id = <ID>", "detail"),
    ("UPDATE bg_muhurta_lattice SET sampling_method = 'muhurta_lattice_v3' WHERE id = <ID>", "sampling_method"),
    ("UPDATE bg_muhurta_lattice SET reference_location_key = 'puri' WHERE id = <ID>", "reference_location_key"),
    ("UPDATE bg_muhurta_lattice SET ayanamsha_key = 'raman' WHERE id = <ID>", "ayanamsha_key"),
])
def test_REAL_WRITER_CODE_MUTATION_a_value_outside_the_declared_closure_is_a_FAIL(db, monkeypatch, mut, needle):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    _restore_after(db, mut, check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_CODE_MUTATION_corpus_status_is_a_CHECK_enforced_word_so_the_declaration_is_what_a_dropped_word_breaks(db, monkeypatch):
    d = _own()
    col = next(c for c in d["prose_none"]["closed_columns"] if c["column"] == "corpus_status")
    col["values"] = ["computed_cited"]
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "corpus_status" in got["Narr.agree"]["measured"]
    with pytest.raises(AssertionError):
        fs.psql(db, f"UPDATE {AID} SET corpus_status = 'computed_guess' WHERE id = (SELECT min(id) FROM {AID})")            # the real DDL refuses a word outside the declared pair


def test_REAL_WRITER_CODE_MUTATION_dropping_a_vocabulary_word_the_data_uses_is_a_FAIL(db, monkeypatch):
    d = _own()
    pat = next(p for p in next(c for c in d["prose_none"]["closed_columns"] if c["column"] == "detail")["json_leaf_patterns"] if p["path"] == "$.sign_name")
    pat["values"] = [v for v in pat["values"] if v != "Meena"]
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "detail" in got["Narr.agree"]["measured"]


def test_REAL_WRITER_CODE_MUTATION_a_missing_pattern_for_a_path_the_data_has_is_a_FAIL(db, monkeypatch):
    d = _own()
    col = next(c for c in d["prose_none"]["closed_columns"] if c["column"] == "detail")
    col["json_leaf_patterns"] = [p for p in col["json_leaf_patterns"] if p["path"] != "$.paksha"]
    assert _m(db, monkeypatch, d)["Narr.agree"]["v"] == FAIL


def test_the_leaf_pattern_count_beyond_the_hard_bound_is_refused_by_the_validator():
    d = _own()
    col = next(c for c in d["prose_none"]["closed_columns"] if c["column"] == "detail")
    col["json_leaf_patterns"] = [dict(path=f"$.k{i}", values=["a"]) for i in range(65)]
    assert "1 to 64" in ac.prose_none_problem(d)
