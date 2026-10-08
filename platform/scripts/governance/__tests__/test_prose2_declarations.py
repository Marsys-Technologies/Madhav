"""test_prose2_declarations.py: prose-declaration batch 2 (L1 and L0): the checked `prose_none` declarations of ga_ayurdaya, ga_medical, ga_prashna and ga_vastu (L1) and
bg_cohort and bg_sky_calendar (L0) are TRUE, shown on rows the REAL writers build.

How each claim is shown (nothing here recomputes a value from the code that is being declared):
  * the declared closed vocabularies are stated by hand in this file (classical lists, enumerations of constants) and are compared with what the real builders write on fixtures;
  * every row the real builder (or the real writer function on a disposable PostgreSQL carrying the real migration DDL) produces is checked against the committed declaration;
  * the engine's OWN measure-time glue (`asset_census._measure_prose`: catalog read, writer scope, written columns, closure SQL, `prose_checks`) then reads the asset on that
    database, and the six Narr/Null cells must read N/A (cause no-prose) through a checked prose_none block with nothing open, contradicted or unread;
  * a mutation (a value outside a declared vocabulary, a text column the declaration does not close) must flip the same reading, so the closure is shown to be able to fail.
Offline apart from the throw-away disposable PostgreSQL (loopback only, deleted at exit); no production access of any kind.
"""
from __future__ import annotations

import itertools
import json
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
SIDECAR = REPO / "platform" / "python-sidecar"
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SIDECAR))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

NA, FAIL, NO_DET, PARTIAL, PASS = ac.NA, ac.FAIL, ac.NO_DET, ac.PARTIAL, ac.PASS
CELLS = ac.NARR_CHECKS + ac.NULL_CHECKS
MIG = REPO / "platform" / "migrations"
SMIG = REPO / "platform" / "supabase" / "migrations"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
AYANAMSHAS = ["lahiri_chitrapaksha", "krishnamurti", "true_chitra", "raman", "surya_siddhanta_classical"]
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
SEVEN = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
NINE = SEVEN + ["Rahu", "Ketu"]


# the assets prose batch 2 declares; the pins of test_e6_1_declarations / test_n150_declarations_schema / test_e6_l0_batch2_declarations read THESE tables (one place to edit per batch)
PROSE2_NONE = ("ga_ayurdaya", "ga_medical", "ga_prashna", "ga_vastu", "bg_cohort", "bg_sky_calendar")      # prose_fields [] with a CHECKED prose_none
PROSE2_FIELDS = {"ga_vichara": ["value_text", "source_citation", "citation_human"]}                    # prose_fields declared (asset: entries)


PROSE2_FIELDS_TABLES = {"ga_vichara": {"chart_vichara"}}      # the tables of the assets in PROSE2_FIELDS (their prose columns are narration in those tables only)
PROSE2_NEW_PROSE_COLUMNS = ("value_text", "source_citation")      # the column names prose batch 2 adds to the file's global narration vocabulary (ga_vichara); pinned by test_e6_l0_batch2_declarations.py's tripwire count


def _need(*mods):
    """The governance CI shards install only pyyaml and pytest; the tests that RUN a sidecar writer need its runtime (psycopg, PyJHora, pyswisseph) and skip, visibly, where it is absent.
    The declaration / AST tests of this file need none of it and always run."""
    for m in mods:
        pytest.importorskip(m)


RUNTIME = ("psycopg", "jhora", "swisseph")


def _decls():
    return ac.load_asset_declarations()


_PYTESTS: list = []


def _python_tests():
    """The sidecar test files the golden scan reads, read ONCE per run (the scan itself is the engine's)."""
    if not _PYTESTS:
        _PYTESTS.extend(ac.python_tests())
    return _PYTESTS


# ───────────────────────── the disposable database carrying the real DDL ─────────────────────────

def _psql(pg, sql=None, path=None):
    args = [str(pg.bin_dir / "psql"), pg.url, "-tAX", "-q", "-v", "ON_ERROR_STOP=1"] + (["-f", str(path)] if path is not None else ["-c", sql])
    p = subprocess.run(args, capture_output=True, text=True, timeout=180)
    assert p.returncode == 0, (path or sql, p.stderr.strip()[:400])
    return p.stdout


# the REAL migration files that create the produced tables (applied in this order; each is a standalone CREATE / ALTER)
REAL_DDL = [SMIG / "204_chart_facts.sql", SMIG / "215_chart_facts_formula_id.sql", SMIG / "216_chart_facts_partial_indexes.sql",
            MIG / "279_ga_medical.sql", MIG / "276_bg_medical_mappings.sql", MIG / "277_bg_nakshatra_medical.sql", MIG / "316_bg_nakshatra_medical_dosha.sql",
            MIG / "261_bg_prashna_rules_schema.sql", MIG / "288_prashna_charts.sql", MIG / "289_ga_prashna_lagna.sql", MIG / "290_ga_prashna_judgment.sql", MIG / "286_ga_vastu_planet_direction_map.sql"]
SIGN_MEDICAL_DDL = ("CREATE TABLE bg_sign_medical (sign_number INTEGER PRIMARY KEY CHECK (sign_number BETWEEN 1 AND 12), sign_name TEXT NOT NULL UNIQUE, body_part TEXT NOT NULL, organ_systems TEXT[], "
                    "element TEXT NOT NULL CHECK (element IN ('fire','earth','air','water')), dosha TEXT NOT NULL, classical_citation TEXT NOT NULL)")
STUBS = ["CREATE OR REPLACE FUNCTION public.authorize_l1_chart_facts_delete(uuid, text[], text[], text[]) RETURNS void LANGUAGE plpgsql AS $$ BEGIN END $$;",
         # test-only stand-in for the ga_condition output the ga_medical / ga_vastu writers READ (they read only these columns)
         "CREATE TABLE ga_condition_composite (chart_id uuid, ayanamsha_id text, graha text, condition_score numeric, dignity_d1 text)",
         # the CREATE TABLE of supabase/migrations/431_bg_sign_medical_kalapurusha.sql (that file also writes asset_registry, which this database does not have); the L0 loader seeds it too
         SIGN_MEDICAL_DDL,
         "ALTER TABLE chart_facts ADD COLUMN IF NOT EXISTS formula_provenance_text TEXT"]      # the post-pass INSERT of ga_structural_writer names it (migration 209)
TABLES = ["bg_sky_calendar", "bg_synthetic_cohort_md", "bg_synthetic_cohort", "chart_vichara", "chart_facts", "ga_medical", "bg_medical_mappings", "bg_nakshatra_medical", "bg_sign_medical", "ga_condition_composite", "prashna_charts", "ga_prashna_lagna",
          "ga_prashna_judgment", "bg_prashna_lagna_methods", "bg_prashna_tajik_yogas", "bg_prashna_significators", "bg_prashna_fructification_rules", "bg_prashna_special_techniques", "ga_vastu_planet_direction_map"]


@pytest.fixture(scope="module")
def db(disposable_pg):
    _need(*RUNTIME)
    for t in TABLES:
        _psql(disposable_pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    for f in REAL_DDL:
        _psql(disposable_pg, path=f)
    for s in STUBS:
        _psql(disposable_pg, s)
    _psql(disposable_pg, _create_table_ddl(SMIG / "472_bg_synthetic_cohort.sql", "bg_synthetic_cohort"))
    _psql(disposable_pg, _create_table_ddl(SMIG / "484_bg_synthetic_cohort_md.sql", "bg_synthetic_cohort_md"))
    _psql(disposable_pg, _create_table_ddl(SMIG / "473_bg_sky_calendar.sql", "bg_sky_events").replace("bg_sky_events", "bg_sky_calendar"))      # the table as migration 597 / 934 renamed it
    yield disposable_pg
    for t in TABLES:
        _psql(disposable_pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def _create_table_ddl(path, table):
    """The CREATE TABLE statement of `table` in a migration file (balanced parentheses, comments dropped): those files also INSERT an asset_registry row this database does not have."""
    import re
    txt = re.sub(r"--[^\n]*", "", path.read_text(encoding="utf-8"))
    i = re.search(r"CREATE TABLE IF NOT EXISTS " + re.escape(table) + r"\s*\(", txt).start()
    j, depth = txt.index("(", i), 0
    for k in range(j, len(txt)):
        depth += (txt[k] == "(") - (txt[k] == ")")
        if depth == 0:
            return txt[i: k + 1] + ";"
    raise AssertionError(f"unbalanced CREATE TABLE {table}")


def _conn(pg):
    import psycopg
    return psycopg.connect(pg.url, autocommit=True)


def _measure(aid, db, monkeypatch, files, target, tables, decl=None):
    """What `measure()` does for one prose-declared asset: the catalog of the produced tables, the writer scope and the closure SQL, through `_measure_prose` itself."""
    point_psql_at(db, monkeypatch)
    decls = _decls()
    d = decl if decl is not None else decls[aid]
    cat = ac.catalog(list(dict.fromkeys([target] + list(tables))))
    # the per-asset narration vocabulary (what measure() hands prose_checks): every declared prose column scoped to the tables of the asset that declares it. The chart_facts assets
    # declare citation_human, ga_vichara declares its two columns in chart_vichara; the declarations of every other asset are scoped to a table no asset here writes.
    scope = {a: {"__other_table__"} for a in decls}
    scope.update({a: {"chart_facts"} for a, e in decls.items() if a.startswith("ga_") and "citation_human" in (e.get("prose_fields") or [])})
    scope.update(PROSE2_FIELDS_TABLES)
    scope[aid] = set(tables) | {target}
    vocab = ac.prose_vocabulary(dict(decls, **{aid: d}), scope)
    return ac._measure_prose(aid, d, {"target_table": target}, files, cat, list(tables), {}, (), vocab)


def _all_na(got):
    assert sorted(got) == sorted(CELLS), sorted(got)
    bad = {c: (v["v"], v["measured"][:300]) for c, v in got.items() if v["v"] != NA}
    assert not bad, bad
    for c in CELLS:
        b = got[c]["prose_none"]
        assert b["checked"] is True and b["open"] == [] and b["contradicted"] == [] and b["unread"] == [], (c, b)


# ───────────────────────── fixtures: the L1 position facts the L1 writers read ─────────────────────────

# a hand-built chart: (sign index 0..11, degree in sign, whole-sign house); the Lagna is Aries
CHART_POS = {"Lagna": (0, 12.5, 1), "Sun": (9, 21.8, 10), "Moon": (10, 5.0, 11), "Mars": (7, 3.0, 8), "Mercury": (9, 10.0, 10), "Jupiter": (5, 2.0, 6),
             "Venus": (9, 2.0, 10), "Saturn": (6, 28.0, 7), "Rahu": (3, 5.0, 4), "Ketu": (9, 5.0, 10)}
SUBJECT = {"Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER", "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT", "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN", "Lagna": "LAGNA"}
NAKSHATRA27 = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
               "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
               "Uttara Bhadrapada", "Revati"]


def _seed_positions(conn, pos=CHART_POS, ayanamshas=AYANAMSHAS):
    """The graha_position / graha_sign_attributes facts the real ga_positions writer stores (categories, keys and the sign / nakshatra names of the pyjhora adapter)."""
    for aya in ayanamshas:
        for g, (sn, deg, house) in pos.items():
            lon = sn * 30 + deg
            nak = NAKSHATRA27[int(lon // (360 / 27)) % 27]
            for cat, key, vtxt, vnum in (("graha_position", "longitude_sidereal", None, lon), ("graha_position", "sign", SIGNS[sn], None), ("graha_position", "nakshatra", nak, None),
                                         ("graha_position", "house_d1", None, house), ("graha_sign_attributes", "sign_num", None, sn + 1),
                                         ("graha_sign_attributes", "degree_in_sign", None, deg)):
                conn.execute("INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key, fact_value_text, fact_value_num, "
                             "citation_ref, citation_human, source_calculation, verification_pass_status, engine_version, computed_at) "
                             "VALUES (%s, %s, %s, gen_random_uuid(), %s, %s, %s, %s, %s, 'fixture', 'fixture', 'fixture', 'single', 'fixture', now())",
                             (f"{aya}|{g}|{key}"[:60], CHART, aya, cat, SUBJECT[g], key, vtxt, vnum))


# ═════════════════════════════════════════ ga_ayurdaya ═════════════════════════════════════════
# Hand-stated expectations (classical lists and the writer's constants, stated here, not read from the writer):
AYU_CLASSES = ["alpayu", "madhyayu", "purnayu"]
AYU_METHODS = ["pindayu", "nisargayu", "amsayu"]
AYU_KEYS = ["total_years", "pindayu_contribution_years", "nisargayu_contribution_years", "amsayu_contribution_years", "applicable_method", "maraka_grahas"]
# every maraka string: the sorted comma-joined subset of the seven grahas that always contains Saturn (the natural maraka)
AYU_MARAKA = sorted(",".join(sorted(set(c) | {"Saturn"})) for n in range(7) for c in itertools.combinations([g for g in SEVEN if g != "Saturn"], n))


def test_ga_ayurdaya_declaration_is_the_checked_none_form_with_the_stated_vocabularies():
    e = _decls()["ga_ayurdaya"]
    assert e["prose_fields"] == [] and e["evidence_kind"] == "writer" and ac.prose_none_problem(e) is None
    pn = e["prose_none"]
    assert pn["column_scope"] == "written"
    assert e["produced_tables"] == [dict(table="chart_facts", filter=dict(column="fact_category", equals="ayurdaya"), why=e["produced_tables"][0]["why"])]
    cc = {c["column"]: c for c in pn["closed_columns"]}
    assert all(c["table"] == "chart_facts" for c in cc.values())
    assert sorted(cc) == sorted(["ayanamsha_id", "fact_category", "fact_subject", "fact_key", "fact_value_text", "fact_value_jsonb", "unit", "citation_ref", "source_calculation",
                                 "verification_pass_status", "engine_version"])
    assert cc["ayanamsha_id"]["values"] == AYANAMSHAS
    assert cc["fact_category"]["values"] == ["ayurdaya"]
    assert cc["fact_subject"]["values"] == ["PINDAYU", "NISARGAYU", "AMSAYU", "CHART", "SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"]
    assert cc["fact_key"]["values"] == AYU_KEYS
    assert cc["fact_value_text"]["values"] == AYU_CLASSES + AYU_METHODS + AYU_MARAKA and len(cc["fact_value_text"]["values"]) == 70
    assert cc["unit"]["values"] == ["years"]
    assert cc["citation_ref"]["values"] == [f"WP-2.5/LCA-16/{k}" for k in AYU_KEYS]
    assert cc["source_calculation"]["values"] == [f"ga_ayurdaya_writer/{k}/single" for k in AYU_KEYS]
    assert cc["verification_pass_status"]["values"] == ["single"] and cc["engine_version"]["values"] == ["ga_ayurdaya_v1"]
    assert cc["fact_value_jsonb"]["values"] == AYU_CLASSES + AYU_METHODS + ["base_only_haranas_deferred_to_w3", "stronger_of_lagna_sun_moon", "lagna_unknown"] + SEVEN + SIGNS
    assert [i["column"] for i in pn["identifier_columns"]] == ["fact_id"]
    # citation_human is the declared source column (exempt) and the SS decline N-49 excludes it from the narration reverse leg
    assert [c["column"] for c in e["source"]["columns"]] == ["citation_human"]
    assert [(x["column"], x["decision_id"]) for x in e["prose_excluded"]] == [("citation_human", "N-49")]


def test_ga_ayurdaya_every_maraka_string_the_function_can_return_is_a_declared_value():
    """compute_marakas over every lagna sign and every occupant subset of the seven grahas (12 x 128 inputs): the joined string is always one of the 64 declared strings."""
    _need(*RUNTIME)
    from ga_writers import ga_ayurdaya_writer as w
    declared = set(AYU_MARAKA)
    seen = set()
    for lagna in range(12):
        for r in range(8):
            for occ in itertools.combinations(SEVEN, r):
                pos = {"Lagna": {"sign_num": lagna, "house_d1": 1}}
                pos.update({g: {"house_d1": 2 if i % 2 == 0 else 7} for i, g in enumerate(occ)})
                out = w.compute_marakas(pos)
                s = ",".join(out["maraka_grahas"])
                assert s in declared, (lagna, occ, s)
                seen.add(s)
    assert len(seen) > 20                                          # the declared set is not vacuous: many distinct strings really occur
    assert w.compute_marakas({}) == {"maraka_grahas": [], "reason": "lagna_unknown"}


def test_ga_ayurdaya_real_substep_rows_stay_inside_every_declared_vocabulary_and_the_engine_reads_na(db, monkeypatch):
    from ga_writers import ga_ayurdaya_writer as w
    conn = _conn(db)
    _psql(db, "DELETE FROM chart_facts")
    _seed_positions(conn)
    n = 0
    for aya in AYANAMSHAS:
        n += w.build_ga_ayurdaya_substep(CHART, "11111111-1111-1111-1111-111111111111", aya, conn)
    assert n == 5 * 26                                             # 3 totals + 21 contributions + applicable_method + maraka_grahas, per ayanamsha
    got = _measure("ga_ayurdaya", db, monkeypatch, ["ga_ayurdaya.py"], "chart_facts", ["chart_facts"])
    _all_na(got)
    blk = got["Narr.agree"]["prose_none"]
    assert sorted(c["column"] for c in blk["closed"]) == sorted(c["column"] for c in _decls()["ga_ayurdaya"]["prose_none"]["closed_columns"])
    assert "chart_facts.fact_id" in blk["identifier_columns"] and blk["column_scope"] == "written"
    assert "citation_human" in blk["source_columns"]


def test_ga_ayurdaya_mutations_flip_the_reading(db, monkeypatch):
    from ga_writers import ga_ayurdaya_writer as w
    conn = _conn(db)
    _psql(db, "DELETE FROM chart_facts")
    _seed_positions(conn)
    w.build_ga_ayurdaya_substep(CHART, "11111111-1111-1111-1111-111111111111", AYANAMSHAS[0], conn)
    # (1) a sentence in a closed column leaves the vocabulary: the closure read FAILs the declaration
    _psql(db, "UPDATE chart_facts SET fact_value_text = 'a long life is indicated' WHERE fact_category = 'ayurdaya' AND fact_key = 'applicable_method'")
    got = _measure("ga_ayurdaya", db, monkeypatch, ["ga_ayurdaya.py"], "chart_facts", ["chart_facts"])
    assert got["Narr.agree"]["v"] == FAIL and "fact_value_text" in got["Narr.agree"]["measured"]
    # (2) a free string leaf in the jsonb leaves the leaf vocabulary
    _psql(db, "DELETE FROM chart_facts WHERE fact_category = 'ayurdaya'")
    w.build_ga_ayurdaya_substep(CHART, "11111111-1111-1111-1111-111111111111", AYANAMSHAS[0], conn)
    _psql(db, "UPDATE chart_facts SET fact_value_jsonb = fact_value_jsonb || '{\"note\": \"longevity is reduced by affliction\"}'::jsonb WHERE fact_category = 'ayurdaya' AND fact_key = 'maraka_grahas'")
    got = _measure("ga_ayurdaya", db, monkeypatch, ["ga_ayurdaya.py"], "chart_facts", ["chart_facts"])
    assert got["Narr.agree"]["v"] == FAIL and "fact_value_jsonb" in got["Narr.agree"]["measured"]
    # (3) a declaration that forgets a column the writer writes is refused by the live schema check (an open text column)
    d = _decls()["ga_ayurdaya"]
    d["prose_none"]["closed_columns"] = [c for c in d["prose_none"]["closed_columns"] if c["column"] != "unit"]
    got = _measure("ga_ayurdaya", db, monkeypatch, ["ga_ayurdaya.py"], "chart_facts", ["chart_facts"], decl=d)
    assert got["Narr.agree"]["v"] == FAIL and "chart_facts.unit" in got["Narr.agree"]["measured"]
    # (4) without the N-49 exclusion the writer's citation_human write hits the narration vocabulary the other chart_facts assets declare: the reverse leg FAILs
    d = _decls()["ga_ayurdaya"]
    d["prose_excluded"] = None
    got = _measure("ga_ayurdaya", db, monkeypatch, ["ga_ayurdaya.py"], "chart_facts", ["chart_facts"], decl=d)
    assert got["Narr.agree"]["v"] == FAIL and "chart_facts.citation_human" in got["Narr.agree"]["measured"]


def test_ga_ayurdaya_the_writers_insert_names_exactly_the_columns_the_declaration_judges():
    """A new column in the INSERT (a new text column) must be seen here, not silently written beside a declaration that predates it."""
    src = (SIDECAR / "ga_writers" / "ga_ayurdaya_writer.py").read_text(encoding="utf-8")
    i = src.index("INSERT INTO chart_facts")
    cols = [c.strip() for c in src[src.index("(", i) + 1: src.index(")", i)].replace("\n", " ").split(",")]
    assert cols == ["fact_id", "chart_id", "ayanamsha_id", "build_id", "fact_category", "fact_subject", "fact_key", "fact_value_text", "fact_value_num", "fact_value_jsonb",
                    "unit", "citation_ref", "citation_human", "source_calculation", "verification_pass_status", "engine_version", "computed_at"]


# ═════════════════════════════════════════ ga_medical ═════════════════════════════════════════
MED_DOSHA = ["kapha", "pitta", "tridosha", "vata"]
MED_ORGANS = ["eyes", "heart", "intestines", "kidneys", "large_intestine", "liver", "lungs", "marrow", "mind", "nervous_system", "pancreas", "red_blood_cells", "reproductive", "skin",
              "spleen", "stomach"]
MED_PARTS = ["abdomen", "anus", "arms", "bile", "bones", "breast", "ears", "face", "genitals", "hands", "heart", "joints", "left_eye", "legs", "limbs", "liver", "neck", "right_ear",
             "right_eye", "skin", "spine", "teeth", "thighs", "tongue", "uterus"]
MED_NAK_PARTS = ["abdomen", "arms", "back/knees", "chest", "ears", "ears/chest", "ears/skin", "eyes/eyebrows", "eyes/face", "eyes/mind", "face/mouth", "feet", "feet/abdomen", "feet/hips",
                 "feet/knees", "fingers/hands", "forehead", "forehead/neck", "head", "left_side", "nose", "right_hand", "right_side", "right_side_body", "right_thigh", "thighs", "thighs/knees"]


def test_ga_medical_declaration_is_the_checked_none_form_with_the_stated_vocabularies():
    e = _decls()["ga_medical"]
    assert e["prose_fields"] == [] and e["evidence_kind"] == "writer" and ac.prose_none_problem(e) is None
    pn = e["prose_none"]
    assert pn.get("column_scope") is None and e.get("produced_tables") is None            # one table, every text column judged
    cc = {c["column"]: c["values"] for c in pn["closed_columns"]}
    assert cc == {"natal_sign": SIGNS, "natal_nakshatra": NAKSHATRA27, "indication_strength": ["strong", "moderate", "mild", "unknown"], "dosha_aggravated": MED_DOSHA,
                  "organ_watch": MED_ORGANS, "body_part_watch": MED_PARTS, "nakshatra_body_part": MED_NAK_PARTS, "indication_tier": ["jyotish_indication"]}
    assert [i["column"] for i in pn["identifier_columns"]] == ["ayanamsha_id", "graha"]
    assert [c["column"] for c in e["source"]["columns"]] == ["classical_citation"]


def test_ga_medical_the_forwarded_vocabularies_are_the_upstream_tables_complete_value_sets():
    """The closure of a forwarded column is the upstream writer's complete value set: the adapter's name tables (sign, nakshatra) and the L0 medical seed rows of the nine grahas."""
    _need(*RUNTIME)
    from brahmagyan import l0_medical as l0
    from pyjhora_adapter import _names
    assert SIGNS == _names.SIGN_NAMES and NAKSHATRA27 == _names.NAKSHATRA_NAMES[1:]
    rows = {r["graha"]: r for r in l0.MEDICAL_MAPPINGS if r["graha"] in NINE}
    assert sorted(rows) == sorted(NINE)
    for col, declared in (("dosha", MED_DOSHA), ("organ_systems", MED_ORGANS), ("body_part", MED_PARTS)):
        assert sorted({x for r in rows.values() for x in r[col]}) == declared, col
    assert sorted({r["body_part"] for r in l0.NAKSHATRA_MEDICAL}) == MED_NAK_PARTS and len(l0.NAKSHATRA_MEDICAL) == 27
    from ga_writers import ga_medical_writer as w
    assert sorted(set(w.INDICATION_STRENGTH_BY_BAND.values()) | {w.INDICATION_STRENGTH_UNKNOWN}) == sorted(["strong", "moderate", "mild", "unknown"])


def test_ga_medical_real_substep_rows_stay_inside_every_declared_vocabulary_and_the_engine_reads_na(db, monkeypatch):
    from brahmagyan import l0_medical as l0
    from ga_writers import ga_medical_writer as w
    conn = _conn(db)
    for t in ("ga_medical", "bg_medical_mappings", "bg_nakshatra_medical", "bg_sign_medical", "ga_condition_composite"):
        _psql(db, f"DELETE FROM {t}")
    _psql(db, "DELETE FROM chart_facts")
    l0.seed_medical_mappings(conn, "11111111-1111-1111-1111-111111111111", autocommit=False)          # the real L0 loader fills the tables the writer reads
    scores = {"low": 0.1, "mid": 0.5, "high": 0.9, "missing": None}
    rows_seen = []
    for k, nak_i in enumerate(range(27)):                       # the Moon walks all 27 nakshatras, the scores cycle through the three bands and a missing score
        _psql(db, "DELETE FROM chart_facts")
        pos = dict(CHART_POS)
        pos["Moon"] = (10, 5.0 + 0.001 * k, 11)
        _seed_positions(conn, pos, AYANAMSHAS[:1])
        _psql(db, f"UPDATE chart_facts SET fact_value_text = '{NAKSHATRA27[nak_i]}' WHERE fact_subject = 'MOON' AND fact_key = 'nakshatra'")
        _psql(db, "DELETE FROM ga_condition_composite")
        band = list(scores.values())[k % 4]
        for g in NINE:
            conn.execute("INSERT INTO ga_condition_composite (chart_id, ayanamsha_id, graha, condition_score) VALUES (%s, %s, %s, %s)", (CHART, AYANAMSHAS[0], g, band))
        assert w.build_ga_medical_substep(CHART, "11111111-1111-1111-1111-111111111111", AYANAMSHAS[0], conn) == 9
        rows_seen += [tuple(r.split("|")) for r in _psql(db, "SELECT graha, natal_sign, natal_nakshatra, indication_strength, nakshatra_body_part FROM ga_medical WHERE ayanamsha_id = '" + AYANAMSHAS[0] + "'").strip().splitlines()]
    assert {r[3] for r in rows_seen} == {"strong", "moderate", "mild", "unknown"}
    moon = {r[2]: r[4] for r in rows_seen if r[0] == "Moon"}
    assert moon["Purva Bhadrapada"] == "left_side"                                              # the FORENSIC native Moon nakshatra maps to the seeded body part
    assert sorted(v for v in moon.values() if v) == sorted(r["body_part"] for r in l0.NAKSHATRA_MEDICAL)       # all 27 nakshatras find their seeded body part since the writer's 23rd-nakshatra spelling fix (Exec 1e5d1b894)
    assert moon["Dhanishta"] == "back/knees"                                                                    # the adapter's 'Dhanishta' now resolves to the L0 table's Dhanishtha row (it used to find nothing)
    # keep one chart of every ayanamsha in the table for the engine reading
    _psql(db, "DELETE FROM ga_medical")
    for aya in AYANAMSHAS:
        _psql(db, "DELETE FROM chart_facts")
        _seed_positions(conn, CHART_POS, [aya])
        _psql(db, "DELETE FROM ga_condition_composite")
        for g in NINE:
            conn.execute("INSERT INTO ga_condition_composite (chart_id, ayanamsha_id, graha, condition_score) VALUES (%s, %s, %s, %s)", (CHART, aya, g, 0.5))
        w.build_ga_medical_substep(CHART, "11111111-1111-1111-1111-111111111111", aya, conn)
    got = _measure("ga_medical", db, monkeypatch, ["ga_medical.py"], "ga_medical", ["ga_medical"])
    _all_na(got)
    blk = got["Narr.agree"]["prose_none"]
    assert sorted(c["column"] for c in blk["closed"]) == sorted(cc["column"] for cc in _decls()["ga_medical"]["prose_none"]["closed_columns"])
    assert sorted(blk["identifier_columns"]) == ["ga_medical.ayanamsha_id", "ga_medical.graha"] and blk["source_columns"] == ["classical_citation"]


def test_ga_medical_mutations_flip_the_reading(db, monkeypatch):
    from ga_writers import ga_medical_writer as w
    conn = _conn(db)
    _psql(db, "DELETE FROM chart_facts")
    _psql(db, "DELETE FROM ga_medical")
    _seed_positions(conn, CHART_POS, AYANAMSHAS[:1])
    _psql(db, "DELETE FROM ga_condition_composite")
    for g in NINE:
        conn.execute("INSERT INTO ga_condition_composite VALUES (%s, %s, %s, %s)", (CHART, AYANAMSHAS[0], g, 0.5))
    w.build_ga_medical_substep(CHART, "11111111-1111-1111-1111-111111111111", AYANAMSHAS[0], conn)
    args = ("ga_medical", db, monkeypatch, ["ga_medical.py"], "ga_medical", ["ga_medical"])
    _all_na(_measure(*args))
    _psql(db, "UPDATE ga_medical SET organ_watch = ARRAY['heart', 'a weak heart is indicated'] WHERE graha = 'Sun'")
    got = _measure(*args)
    assert got["Narr.agree"]["v"] == FAIL and "organ_watch" in got["Narr.agree"]["measured"]
    _psql(db, "UPDATE ga_medical SET organ_watch = ARRAY['heart'] WHERE graha = 'Sun'")
    _psql(db, "ALTER TABLE ga_medical ADD COLUMN note text")                                   # a new text column the declaration does not close
    try:
        got = _measure(*args)
        assert got["Narr.agree"]["v"] == FAIL and "ga_medical.note" in got["Narr.agree"]["measured"]
    finally:
        _psql(db, "ALTER TABLE ga_medical DROP COLUMN note")
    _all_na(_measure(*args))


def test_ga_medical_the_writers_insert_names_exactly_the_columns_the_declaration_judges():
    src = (SIDECAR / "ga_writers" / "ga_medical_writer.py").read_text(encoding="utf-8")
    i = src.index("INSERT INTO ga_medical")
    cols = [c.strip() for c in src[src.index("(", i) + 1: src.index(")", i)].replace("\n", " ").split(",")]
    assert cols == ["chart_id", "ayanamsha_id", "graha", "natal_sign", "natal_nakshatra", "indication_strength", "dosha_aggravated", "organ_watch", "body_part_watch",
                    "nakshatra_body_part", "indication_tier", "not_diagnosis", "classical_citation", "computed_at"]


# ═════════════════════════════════════════ ga_prashna ═════════════════════════════════════════
PR_CLASSES = ["marriage", "career", "litigation_legal", "health_illness", "finance_wealth", "travel_journey", "property_land", "children_progeny", "death_longevity",
              "spiritual_religious", "enemy_conflict"]
PR_QUESITED = ["Venus", "Saturn", "Mars", "Moon", "Jupiter", "Mercury"]
PR_LAGNA_CITATION = "T\u0101jika N\u012blaka\u1e47\u1e6dh\u012b, Ch. 1 (Prashna Lagna Nir\u016bpa\u1e47a)"


def test_ga_prashna_declaration_is_the_checked_none_form_with_the_stated_vocabularies():
    e = _decls()["ga_prashna"]
    assert e["prose_fields"] == [] and e["evidence_kind"] == "writer" and ac.prose_none_problem(e) is None
    pn = e["prose_none"]
    assert pn["column_scope"] == "written"                      # ga_prashna_lagna.kp_sub_lord is a text column no writer statement writes
    assert [t["table"] for t in e["produced_tables"]] == ["ga_prashna_lagna", "ga_prashna_judgment"]
    cc = {(c["table"], c["column"]): c["values"] for c in pn["closed_columns"]}
    J, L = "ga_prashna_judgment", "ga_prashna_lagna"
    assert cc == {(J, "question_class"): PR_CLASSES, (J, "querent_significator"): ["Moon"], (J, "quesited_significator"): PR_QUESITED,
                  (J, "tajik_yoga"): ["ithasala", "eesarpha", "no_direct_aspect"], (J, "judgment_text"): ["YES", "NO", "UNCERTAIN"],
                  (J, "fructification_unit"): ["days", "months"], (J, "fructification_rule_id"): ["degree_to_days", "sign_to_months"], (J, "lagna_rashi"): SIGNS,
                  (L, "lagna_rashi"): SIGNS, (L, "classical_citation"): [PR_LAGNA_CITATION]}
    assert sorted((i["table"], i["column"]) for i in pn["identifier_columns"]) == sorted([(L, "ayanamsha_id"), (L, "lagna_method"), (J, "ayanamsha_id")])
    assert [c["column"] for c in e["source"]["columns"]] == ["classical_citation"]


def test_ga_prashna_the_forwarded_vocabularies_are_the_seeded_and_guarded_complete_sets():
    _need(*RUNTIME)
    from brahmagyan import l0_prashna as l0
    from ga_writers import ga_prashna_cast as cast
    usable = [r for r in l0.SIGNIFICATORS if r["quesited_planet"]]
    assert sorted(r["question_class"] for r in usable) == sorted(PR_CLASSES)
    assert set(cast.VALID_QUESTION_CLASSES) - {r["question_class"] for r in usable} == {"lost_object"}      # the one class with no quesited planet writes no row
    assert {r["querent_planet"].split(",")[0].strip() for r in l0.SIGNIFICATORS} == {"Moon"}
    assert sorted({r["quesited_planet"].split(",")[0].strip() for r in usable}) == sorted(PR_QUESITED)


def _seed_prashna_scenario(conn, chart_id, aya, question_class, moon_lon, quesited, quesited_lon, lagna_lon, method="tajik_moment_lagna"):
    conn.execute("INSERT INTO prashna_charts (chart_id, question_text, question_class, prashna_lagna_method, question_instant) VALUES (%s, 'fixture', %s, %s, now())",
                 (chart_id, question_class, method))
    for subj, lon in (("LAGNA", lagna_lon), ("MOON", moon_lon), (quesited, quesited_lon)):
        conn.execute("INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key, fact_value_num, citation_ref, citation_human, "
                     "source_calculation, verification_pass_status, engine_version, computed_at) VALUES (%s, %s, %s, gen_random_uuid(), 'graha_position', %s, 'longitude_sidereal', %s, "
                     "'fixture', 'fixture', 'fixture', 'single', 'fixture', now()) ON CONFLICT DO NOTHING", (f"{chart_id}|{aya}|{subj}", chart_id, aya, subj, lon))


def test_ga_prashna_real_writer_rows_stay_inside_every_declared_vocabulary_and_the_engine_reads_na(db, monkeypatch):
    import uuid
    from brahmagyan import l0_prashna as l0
    from ga_writers import ga_prashna_writer as w
    conn = _conn(db)
    for t in ("ga_prashna_lagna", "ga_prashna_judgment", "prashna_charts"):
        _psql(db, f"DELETE FROM {t}")
    _psql(db, "DELETE FROM chart_facts")
    l0.seed_prashna_rules(conn)
    sig = {r["question_class"]: r["quesited_planet"].split(",")[0].strip() for r in l0.SIGNIFICATORS if r["quesited_planet"]}
    written = 0
    k = 0
    for qc in PR_CLASSES + ["lost_object"]:
        for off in (298, 302, 320, 358, 2, 150, 230, 60):             # the Moon sits a little before / a little after a sextile or conjunction with the quesited planet, or well outside every orb
            cid = str(uuid.uuid4())
            aya = AYANAMSHAS[k % 5]
            lagna = (k * 37) % 360                                      # the rising sign walks the movable / fixed / dual signs
            quesited = SUBJECT.get(sig.get(qc, "Venus"), "VEN")
            _seed_prashna_scenario(conn, cid, aya, qc, (100 + off) % 360, quesited, 100.0, lagna)
            n = w.seed_prashna_judgment(conn, cid, aya, "11111111-1111-1111-1111-111111111111")
            assert n == (0 if qc == "lost_object" else 2)
            written += n
            k += 1
    assert written == 2 * 11 * 8
    seen = {c: {r for (r,) in [tuple(x.split("|")) for x in _psql(db, f"SELECT DISTINCT {c} FROM ga_prashna_judgment").split()]} for c in
            ("question_class", "tajik_yoga", "judgment_text", "fructification_unit", "fructification_rule_id", "lagna_rashi")}
    assert seen["question_class"] == set(PR_CLASSES) and seen["tajik_yoga"] == {"ithasala", "eesarpha", "no_direct_aspect"} and seen["judgment_text"] == {"YES", "NO", "UNCERTAIN"}
    assert seen["fructification_unit"] == {"days", "months"} and seen["fructification_rule_id"] == {"degree_to_days", "sign_to_months"}
    assert seen["lagna_rashi"] == set(SIGNS)
    got = _measure("ga_prashna", db, monkeypatch, ["ga_prashna.py"], "ga_prashna_judgment", ["ga_prashna_lagna", "ga_prashna_judgment"])
    _all_na(got)
    blk = got["Narr.agree"]["prose_none"]
    assert blk["column_scope"] == "written" and sorted(blk["identifier_columns"]) == ["ga_prashna_judgment.ayanamsha_id", "ga_prashna_lagna.ayanamsha_id", "ga_prashna_lagna.lagna_method"]
    assert blk["source_columns"] == ["classical_citation"] and sorted(blk["tables"]) == ["ga_prashna_judgment", "ga_prashna_lagna"]


def test_ga_prashna_mutations_flip_the_reading(db, monkeypatch):
    import uuid
    from brahmagyan import l0_prashna as l0
    from ga_writers import ga_prashna_writer as w
    conn = _conn(db)
    for t in ("ga_prashna_lagna", "ga_prashna_judgment", "prashna_charts"):
        _psql(db, f"DELETE FROM {t}")
    _psql(db, "DELETE FROM chart_facts")
    l0.seed_prashna_rules(conn)
    cid = str(uuid.uuid4())
    _seed_prashna_scenario(conn, cid, AYANAMSHAS[0], "marriage", 100.0, "VEN", 100.0, 10.0)
    assert w.seed_prashna_judgment(conn, cid, AYANAMSHAS[0], "11111111-1111-1111-1111-111111111111") == 2
    args = ("ga_prashna", db, monkeypatch, ["ga_prashna.py"], "ga_prashna_judgment", ["ga_prashna_lagna", "ga_prashna_judgment"])
    _all_na(_measure(*args))
    _psql(db, "UPDATE ga_prashna_judgment SET judgment_text = 'the marriage will happen soon'")
    got = _measure(*args)
    assert got["Narr.agree"]["v"] == FAIL and "judgment_text" in got["Narr.agree"]["measured"]
    _psql(db, "UPDATE ga_prashna_judgment SET judgment_text = 'YES'")
    _psql(db, "UPDATE ga_prashna_lagna SET classical_citation = 'a different citation sentence'")
    got = _measure(*args)
    assert got["Narr.agree"]["v"] == FAIL and "ga_prashna_lagna" in got["Narr.agree"]["measured"]


def test_ga_prashna_the_writers_inserts_name_exactly_the_columns_the_declaration_judges():
    src = (SIDECAR / "ga_writers" / "ga_prashna_writer.py").read_text(encoding="utf-8")
    import re
    cols = {m.group(1): [c.strip() for c in m.group(2).replace("\n", " ").split(",")] for m in re.finditer(r"INSERT INTO (\w+)\s*\(([^)]*)\)", src)}
    assert cols == {"ga_prashna_lagna": ["chart_id", "ayanamsha_id", "lagna_method", "lagna_rashi", "lagna_degree", "is_primary", "classical_citation"],
                    "ga_prashna_judgment": ["chart_id", "ayanamsha_id", "question_class", "querent_significator", "quesited_significator", "querent_longitude", "quesited_longitude",
                                            "longitudinal_gap", "is_applying", "tajik_yoga", "judgment_text", "fructification_value", "fructification_unit", "fructification_rule_id",
                                            "lagna_rashi", "classical_citation"]}


# ═════════════════════════════════════════ ga_vastu ═════════════════════════════════════════
VA_DIRECTIONS = ["East", "Northwest", "South", "North", "Northeast", "Southeast", "West", "Southwest"]
VA_DIGNITY = ["moolatrikona", "exalted", "debilitated", "own", "neutral_sign", "friend_sign", "enemy_sign"]
VA_IMPACT = ["weakened", "neutral", "strengthened", "unknown"]


def test_ga_vastu_declaration_is_the_checked_none_form_with_the_stated_vocabularies():
    e = _decls()["ga_vastu"]
    assert e["prose_fields"] == [] and e["evidence_kind"] == "writer" and ac.prose_none_problem(e) is None and ac.prose_empty_d1_problem(e) is None
    pn = e["prose_none"]
    assert pn.get("column_scope") is None and e.get("produced_tables") is None
    assert {c["column"]: c["values"] for c in pn["closed_columns"]} == {"direction": VA_DIRECTIONS, "dignity_d1": VA_DIGNITY, "direction_impact": VA_IMPACT, "indication_tier": ["traditional_vastu"]}
    assert [i["column"] for i in pn["identifier_columns"]] == ["ayanamsha_id", "graha"]
    assert [c["column"] for c in e["source"]["columns"]] == ["classical_citation"]
    assert e["carriage"]["nature"] == "unverified_transcription"           # the D1 carriage is a ceiling, not a coupling: prose_empty_d1_problem applies to nature transcription only


def test_ga_vastu_the_forwarded_dignity_words_are_the_complete_return_set_of_the_condition_function():
    """dignity_d1_from_sign over every graha, every sign and degrees across each sign (and with a dignity reference table): only the seven declared words come back."""
    _need(*RUNTIME)
    from ga_writers import ga_condition_writer as cw
    seen = set()
    for graha in NINE:
        for sign in SIGNS:
            for deg in (0.0, 1.0, 4.9, 10.0, 15.0, 20.0, 29.9):
                seen.add(cw.dignity_d1_from_sign(graha, sign, deg))
    assert seen == set(VA_DIGNITY)


def test_ga_vastu_real_substep_rows_stay_inside_every_declared_vocabulary_and_the_engine_reads_na(db, monkeypatch):
    from ga_writers import ga_vastu_writer as w
    conn = _conn(db)
    for t in ("ga_vastu_planet_direction_map", "ga_condition_composite"):
        _psql(db, f"DELETE FROM {t}")
    scores = [0.1, 0.5, 0.9, None]
    k = 0
    for aya in AYANAMSHAS:
        for i, g in enumerate(NINE):
            conn.execute("INSERT INTO ga_condition_composite (chart_id, ayanamsha_id, graha, condition_score, dignity_d1) VALUES (%s, %s, %s, %s, %s)",
                         (CHART, aya, g, scores[(i + k) % 4], (VA_DIGNITY + [None])[(i + k) % 8]))
        k += 1
        assert w.build_ga_vastu_substep(CHART, "11111111-1111-1111-1111-111111111111", aya, conn) == 8            # Ketu has no classical direction
    seen = {c: {x for x in _psql(db, f"SELECT DISTINCT {c} FROM ga_vastu_planet_direction_map").split()} for c in ("direction", "direction_impact", "indication_tier", "graha")}
    assert seen["direction"] == set(VA_DIRECTIONS) and seen["direction_impact"] == set(VA_IMPACT) and seen["indication_tier"] == {"traditional_vastu"}
    assert seen["graha"] == set(NINE) - {"Ketu"}
    got = _measure("ga_vastu", db, monkeypatch, ["ga_vastu.py"], "ga_vastu_planet_direction_map", ["ga_vastu_planet_direction_map"])
    _all_na(got)
    blk = got["Narr.agree"]["prose_none"]
    assert sorted(blk["identifier_columns"]) == ["ga_vastu_planet_direction_map.ayanamsha_id", "ga_vastu_planet_direction_map.graha"] and blk["source_columns"] == ["classical_citation"]


def test_ga_vastu_mutations_flip_the_reading(db, monkeypatch):
    from ga_writers import ga_vastu_writer as w
    conn = _conn(db)
    for t in ("ga_vastu_planet_direction_map", "ga_condition_composite"):
        _psql(db, f"DELETE FROM {t}")
    for g in NINE:
        conn.execute("INSERT INTO ga_condition_composite (chart_id, ayanamsha_id, graha, condition_score, dignity_d1) VALUES (%s, %s, %s, 0.5, 'own')", (CHART, AYANAMSHAS[0], g))
    w.build_ga_vastu_substep(CHART, "11111111-1111-1111-1111-111111111111", AYANAMSHAS[0], conn)
    args = ("ga_vastu", db, monkeypatch, ["ga_vastu.py"], "ga_vastu_planet_direction_map", ["ga_vastu_planet_direction_map"])
    _all_na(_measure(*args))
    _psql(db, "UPDATE ga_vastu_planet_direction_map SET direction_impact = 'the east side of the home is weakened' WHERE graha = 'Sun'")
    got = _measure(*args)
    assert got["Narr.agree"]["v"] == FAIL and "direction_impact" in got["Narr.agree"]["measured"]
    _psql(db, "UPDATE ga_vastu_planet_direction_map SET direction_impact = 'neutral' WHERE graha = 'Sun'")
    _psql(db, "UPDATE ga_vastu_planet_direction_map SET dignity_d1 = 'great_friend_sign' WHERE graha = 'Moon'")            # a word the condition writer never returns
    got = _measure(*args)
    assert got["Narr.agree"]["v"] == FAIL and "dignity_d1" in got["Narr.agree"]["measured"]


def test_ga_vastu_the_writer_does_not_read_the_l0_direction_table_so_its_text_cannot_reach_the_output():
    src = (SIDECAR / "ga_writers" / "ga_vastu_writer.py").read_text(encoding="utf-8")
    assert "bg_vastu_directions" not in src.replace("`bg_vastu_directions`", "")              # if a later change reads it, the direction column must be re-proved against its seed
    i = src.index("INSERT INTO ga_vastu_planet_direction_map")
    cols = [c.strip() for c in src[src.index("(", i) + 1: src.index(")", i)].replace("\n", " ").split(",")]
    assert cols == ["chart_id", "ayanamsha_id", "graha", "direction", "condition_score", "dignity_d1", "direction_impact", "indication_tier", "classical_citation", "computed_at"]


# ═════════════════════════════════════════ ga_vichara (prose_fields + golden tests) ═════════════════════════════════════════
def _chart_vichara_ddl():
    """The CREATE TABLE of migration 435 (that file also writes asset_registry, which this database does not have)."""
    txt = (MIG / "435_ga_vichara.sql").read_text(encoding="utf-8")
    i = txt.index("CREATE TABLE IF NOT EXISTS chart_vichara")
    j = txt.index("CONSTRAINT chart_vichara_ratification_factor_range")
    return txt[i: txt.index(");", j) + 2]


def test_ga_vichara_declares_the_three_composed_columns_with_golden_tests_the_scan_verifies():
    e = _decls()["ga_vichara"]
    assert e["prose_fields"] == ["value_text", "source_citation", "citation_human"] and e["evidence_kind"] == "writer" and e.get("prose_none") is None
    # the daridra post-pass row is part of the asset's output (SS N-196: the substep counts it in rows_written): its table is a declared produced table, its columns are declared cross-asset writes
    assert [(t["table"], t.get("filter")) for t in e["produced_tables"]] == [("chart_vichara", None), ("chart_facts", {"column": "fact_subject", "equals": "daridra"})]
    assert e["cross_asset_writes"] == ["chart_facts.fact_value_text", "chart_facts.citation_human"]
    ev = e["evidence"]["prose_fields"]
    for cite in ("ga_vichara_writer.py:676", "ga_vichara_writer.py:678", "ga_vichara_writer.py:371", "ga_vichara_writer.py:444", "ga_vichara_writer.py:526", "valence_doctrine.py:251",
                 "ga_vichara_writer.py:1088", "ga_vichara_writer.py:1090", "ga_vichara_writer.py:1220", "ga_vichara_writer.py:1221", "ga_daridra_postpass.py:281", "ga_daridra_postpass.py:215",
                 "ga_daridra_postpass.py:217", "ga_daridra_postpass.py:225", "ga_daridra_postpass.py:86", "ga_daridra_postpass.py:301", "ga_structural_writer.py:3103", "ga_structural_writer.py:3214",
                 "ga_structural_writer.py:3215", "ga_structural_writer.py:3221"):
        assert cite in ev, cite
    # the cited lines really hold what the evidence says they hold
    w = (SIDECAR / "ga_writers" / "ga_vichara_writer.py").read_text(encoding="utf-8").splitlines()
    v = (SIDECAR / "brahmagyan" / "valence_doctrine.py").read_text(encoding="utf-8").splitlines()
    pp = (SIDECAR / "ga_writers" / "ga_daridra_postpass.py").read_text(encoding="utf-8").splitlines()
    sw = (SIDECAR / "ga_writers" / "ga_structural_writer.py").read_text(encoding="utf-8").splitlines()
    assert '"value_text": (' in w[675] and "ratification fails in" in w[677] and "verdict.citation" in w[370] and '"source_citation": citation' in w[443] and '"source_citation": citation' in w[525]
    assert "citation = (" in v[250] and "value_text" in w[1087] and "source_citation" in w[1089]
    assert "import emit_daridra_label_post_pass" in w[1219] and "emit_daridra_label_post_pass(conn" in w[1220] and "return inserted + daridra_written" in w[1221]
    assert "def emit_daridra_label_post_pass" in pp[280] and '"citation_human": (' in pp[214] and "does not serve as a finding" in pp[216] and "Daridra stands uncancelled" in pp[224]
    assert "cur.execute(_DARIDRA_INSERT_SQL, (" in pp[85] and "insert_daridra_label_rows(conn, rows)" in pp[300]
    assert "def _build_dosha_rows" in sw[3102] and "citation_human = (" in sw[3213] and "labels chart" in sw[3214] and "CANCELLED:" in sw[3220]
    assert [t["covers"] for t in e["fidelity_tests"]] == [["value_text"], ["source_citation"], ["source_citation"], ["source_citation"], ["citation_human"], ["citation_human"]]
    got = ac.narr_fidelity_scan(e["prose_fields"], ev, _python_tests(), e["fidelity_tests"], None)
    assert got["v"] == PASS and "6 declared golden-value test(s) verified" in got["measured"] and "covers citation_human, source_citation, value_text" in got["measured"], got["measured"]


def test_ga_vichara_the_two_new_column_names_are_new_to_the_global_vocabulary():
    """The tripwire count of test_e6_l0_batch2_declarations (41 + these) holds only while neither new name was already declared by another asset; citation_human was already declared by the chart_facts assets."""
    others = {c for a, e in _decls().items() if a != "ga_vichara" for c in (ac.parse_prose_field(f)[0] for f in (e.get("prose_fields") or []))}
    assert set(PROSE2_NEW_PROSE_COLUMNS) == set(_decls()["ga_vichara"]["prose_fields"]) - {"citation_human"} and not set(PROSE2_NEW_PROSE_COLUMNS) & others
    assert "citation_human" in others


def test_ga_vichara_the_composed_columns_are_exactly_the_two_that_carry_sentences():
    """Every text value the builders can put in value_text / source_citation / target is accounted for: the sentence rows are declared, the rest are closed labels or fixed strings."""
    _need(*RUNTIME)
    sys.path.insert(0, str(SIDECAR / "tests"))
    import test_ga_vichara_narr_golden as g
    from ga_writers import ga_vichara_writer as gv
    facts = [g._link("l1", "Venus", 2, 2), g._link("l2", "Jupiter", 9, 2), g._functional("fc1", "JUP", "yogakaraka"), g._dignity("d1jup", "D1", "JUP", "exalted"),
             g._dignity("d9jup", "D9", "JUP", "debilitated"), g._dignity("d1ven", "D1", "VEN", "own"), g._dignity("d9ven", "D9", "VEN", "own")]
    idx = gv.VicharaFactIndex(facts)
    domains = {"wealth": {"vargas": ["D1", "D9"], "houses": [2], "karaka": "Jupiter", "provisional": False}}
    rows = gv.build_valence_pass_rows(idx, "D1", {}) + gv.build_varga_ratification_rows(idx, domains, 0.2, 0.6, 1.4)[0]
    by_family = {}
    for r in rows:
        by_family.setdefault(r["vichara_family"], []).append(r)
    assert sorted(by_family) == ["valence_pass", "varga_ratification", "varga_ratification_divergence"]
    assert {r["value_text"] for r in by_family["valence_pass"]} <= {"mixed", "strong_benefic", "benefic", "strong_malefic", "malefic", "neutral"}      # a closed label on the valence rows
    assert all(r["value_text"] is None for r in by_family["varga_ratification"]) and all(" — " in r["value_text"] for r in by_family["varga_ratification_divergence"])
    assert {r["source_citation"] for r in by_family["varga_ratification"]} == {"DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §11"}                         # a fixed provenance string
    assert all(r["source_citation"].startswith("BPHS Ch.3") and "\u2192" in r["source_citation"] and "[natural=" in r["source_citation"] for r in by_family["valence_pass"])
    assert all(r["target"].startswith("D1_HOUSE_") for r in by_family["valence_pass"])                                                                  # the structural code: an identity label


def _vichara_world(db, monkeypatch, *, daridra="uncancelled"):
    """The REAL substep (`build_ga_vichara_substep`: its own rows, INSERT, delete and post-pass call, the post-pass's own delete and literal-tuple INSERT) on the disposable database. Only the fact /
    constant / firing loaders and the chart computation behind the daridra label are fed fixtures: daridra "uncancelled" (the label stands), "cancelled" (a fired dhana structure cancels it) or
    "absent" (the dosha does not form on the chart: the 11th lord sits in a good house and neither 2nd nor 11th lord is afflicted). Returns (rows_written, chart_vichara rows, daridra rows)."""
    import copy
    import datetime
    import uuid
    sys.path.insert(0, str(SIDECAR / "tests"))
    import test_ga_vichara_narr_golden as g
    from ga_writers import ga_daridra_postpass as pp
    from ga_writers import ga_vichara_writer as gv
    _psql(db, "DROP TABLE IF EXISTS chart_vichara CASCADE")
    _psql(db, _chart_vichara_ddl())
    _psql(db, "DELETE FROM chart_facts")
    conn = _conn(db)
    facts = [g._link("l1", "Venus", 2, 2), g._link("l2", "Jupiter", 9, 2), g._functional("fc1", "JUP", "yogakaraka"), g._dignity("d1jup", "D1", "JUP", "exalted"),
             g._dignity("d9jup", "D9", "JUP", "debilitated"), g._dignity("d1ven", "D1", "VEN", "own"), g._dignity("d9ven", "D9", "VEN", "own")]
    domains = {"wealth": {"vargas": ["D1", "D9"], "houses": [2], "karaka": "Jupiter", "provisional": False}}
    constants = {"ratification_step": 0.2, "ratification_clamp": {"lo": 0.6, "hi": 1.4}, "operative_vargas": domains, "valence_matrix": {}, "dignity_score_map": {}, "leverage_weights": {},
                 "consistency_weights": {"w_sign": 0.5, "w_dignity": 0.5}}
    monkeypatch.setattr(gv, "_load_chart_facts", lambda c, cid, aid: facts)
    monkeypatch.setattr(gv, "_load_constants", lambda c: constants)
    monkeypatch.setattr(gv, "_load_yoga_firings", lambda c, cid, aid: [])
    monkeypatch.setattr(gv, "_load_dasha_md_rows", lambda c, cid, aid: [])
    chart = copy.deepcopy(g.DARIDRA_CHART)
    if daridra == "absent":
        next(x for x in chart["grahas"] if x["name"] == "Venus").update(sign="Libra", sign_id=7, house=4, longitude=190.0)      # the 11th lord in a kendra
    canned = g._CannedConn(yoga_rows=[("dhana_yoga_house_lords", '["sun", "mercury", "venus"]')] if daridra == "cancelled" else None)
    real = getattr(pp.build_daridra_label_rows, "_real", pp.build_daridra_label_rows)           # the original, even when an earlier call of this helper in the same test already patched it
    patched = lambda c, cid, bid, aya, **k: real(canned, cid, bid, aya, chart_output=chart, dosha_catalog=[g.DARIDRA_ENTRY])      # noqa: E731
    patched._real = real
    monkeypatch.setattr(pp, "build_daridra_label_rows", patched)
    rows_written = gv.build_ga_vichara_substep(CHART, str(uuid.uuid4()), AYANAMSHAS[0], conn, as_of=datetime.date(2026, 1, 1))
    n_v = int(_psql(db, f"SELECT count(*) FROM chart_vichara WHERE chart_id = '{CHART}'").strip())
    n_d = int(_psql(db, f"SELECT count(*) FROM chart_facts WHERE chart_id = '{CHART}' AND fact_subject = 'daridra'").strip())
    return rows_written, n_v, n_d


@pytest.mark.parametrize("variant,text", [
    ("uncancelled", "Dosha Daridra (daridra) labels chart 482012f1 (lahiri_chitrapaksha): bespoke_detector:daridra."),
    ("cancelled", "Dosha Daridra (daridra) labels chart 482012f1 (lahiri_chitrapaksha): bespoke_detector:daridra. CANCELLED: brahma_dosha_catalog daridra cancellation_conditions "
                  "('dhana/raja yoga present'): dhana_structure_fires:dhana_yoga_house_lords \u2014 Daridra does not serve as a finding.")])
def test_ga_vichara_the_engine_reads_the_cells_on_rows_the_real_substep_and_its_daridra_post_pass_write(db, monkeypatch, variant, text):
    _need(*RUNTIME)
    rows_written, n_v, n_d = _vichara_world(db, monkeypatch, daridra=variant)
    assert n_d == 1 and rows_written == n_v + 1
    assert _psql(db, "SELECT citation_human FROM chart_facts WHERE fact_subject = 'daridra'").strip() == text
    point_psql_at(db, monkeypatch)
    decls = _decls()
    cat = ac.catalog(["chart_vichara", "chart_facts"])
    # what measure() hands prose_checks: ga_vichara's declared columns scoped to its registry table, the other chart_facts assets' citation_human to chart_facts; its own tables are the DECLARED produced set
    vocab = ac.prose_vocabulary(decls, dict({a: {"chart_facts"} for a, e in decls.items() if a.startswith("ga_") and "citation_human" in (e.get("prose_fields") or []) and a != "ga_vichara"},
                                            **{a: {"__other_table__"} for a, e in decls.items() if not a.startswith("ga_")}, ga_vichara={"chart_vichara"}))
    r = {"target_table": "chart_vichara", "count_sql": "SELECT count(*) FROM chart_vichara WHERE chart_id = $1"}
    got = ac._measure_prose("ga_vichara", decls["ga_vichara"], r, ["ga_vichara.py"], cat, ["chart_vichara", "chart_facts"], {"chart_facts"}, _python_tests(), vocab)
    v = {c: x["v"] for c, x in got.items()}
    assert v["Narr.agree"] == PASS and v["Narr.fidelity_test"] == PASS and v["Narr.lint"] == PASS, {c: (x["v"], x["measured"][:300]) for c, x in got.items()}
    # chart_facts is a table other assets also produce into and ga_vichara's registry count_sql reads chart_vichara only, so the rows of its daridra citation_human cannot be counted under a
    # chart scope: "unknown", which the engine reads PARTIAL (never a false PASS). The writer scan is CLEAN now (Exec N-196 binds the row as a literal tuple: it used to stop at
    # ga_structural's mutated `tuples` list), so the count scope is the only thing left
    assert v["Narr.checkable"] == PARTIAL and "value_text=3" in got["Narr.checkable"]["measured"] and "source_citation=14" in got["Narr.checkable"]["measured"] and "citation_human=unknown" in got["Narr.checkable"]["measured"]
    for c in ("Null.schema_default", "Null.blank_rows"):
        assert v[c] == PARTIAL and "writer scan CLEAN: 4 write path(s)" in got[c]["measured"] and "no literal fallback, no constant write, nothing unresolved" in got[c]["measured"], got[c]["measured"]
    assert "unknown for citation_human" in got["Null.blank_rows"]["measured"]
    # the writer scan is what the census reads for citation_human: a constant written to it would flip the cells (the scan sees all 4 write paths)
    assert "citation_human" in got["Null.schema_default"]["measured"]


def test_ga_vichara_build_completion_reads_pass_with_the_declared_set_on_charts_where_the_daridra_row_forms_and_where_it_does_not(db, monkeypatch, tmp_path):
    """SS N-196 (Exec, main dd5ab8583): ga_vichara's substep counts the post-pass daridra row in rows_written. The REAL substep runs on the disposable database on three charts (daridra stands,
    daridra cancelled by a fired dhana structure, daridra does not form); the census's own `measure()` reads Build.completion for the committed declaration (chart_vichara + the chart_facts daridra
    slice): PASS on all three, sum == live == rows_written. The same record against the registry count_sql alone (no declared set) is a FAIL on the two charts where the row forms: the declaration
    is what makes the cell read the truth, and each undeclared / half-declared variant is held to its reading."""
    _need(*RUNTIME)
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import test_e6_n99_build_completion_integrity as n99
    committed = _decls()["ga_vichara"]

    def read(decl, rows_written, n_vichara):
        point_psql_at(db, monkeypatch)
        reg = {"ga_vichara": dict(n99._reg_row("ga_vichara"), target_table="chart_vichara", count_sql="SELECT count(*) FROM chart_vichara WHERE chart_id = $1", has_integrity=False, target_floor="1")}
        n99._stub_layer(monkeypatch, tmp_path, reg, live=n_vichara, rec=dict(n99._REC, rows_written=str(rows_written)))
        monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {"ga_vichara": {CHART: dict(n99._REC, rows_written=str(rows_written))}})
        monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"ga_vichara": decl})
        monkeypatch.setattr(ac, "registered_ids", lambda prefix: {"ga_vichara": ["ga_vichara.py"]})
        monkeypatch.setattr(ac, "idem_scan", lambda *x, **k: ("PASS", ["stub"]))
        monkeypatch.setattr(ac, "contract_scan", lambda *x, **k: ("PASS", []))
        monkeypatch.setattr(ac, "CHART_ID", CHART)
        return n99._cell(ac.measure("L1"), "ga_vichara")

    for variant in ("uncancelled", "cancelled", "absent"):
        rows_written, n_v, n_d = _vichara_world(db, monkeypatch, daridra=variant)
        formed = variant != "absent"
        assert n_d == (1 if formed else 0) and rows_written == n_v + n_d > 0, (variant, rows_written, n_v, n_d)      # the return value counts the daridra row when (and only when) it formed
        got = read(committed, rows_written, n_v)
        assert got["v"] == PASS and f"rows_written={rows_written} = live={rows_written}" in got["measured"] and f"chart_vichara={n_v}" in got["measured"] and f"= {rows_written}" in got["measured"], (variant, got)
        assert (f"chart_facts[fact_subject=daridra]={n_d}" in got["measured"]), (variant, got["measured"])
        assert got["produced_set"]["extra"] == [] and got["produced_set"]["complete"] is True, got["produced_set"]
        # the registry count_sql alone (no declared set): equal when the row did not form, one short when it did
        undeclared = read({k: v for k, v in committed.items() if k != "produced_tables"}, rows_written, n_v)
        assert undeclared["v"] == (FAIL if formed else PASS), (variant, undeclared)
        # a declared set that forgets the row's table is an undeclared extra table the writer scan sees
        only_vichara = read(dict(committed, produced_tables=[dict(table="chart_vichara")]), rows_written, n_v)
        assert only_vichara["v"] == FAIL and "chart_facts" in only_vichara["measured"], (variant, only_vichara)


# ═════════════════════════════════════════ bg_cohort ═════════════════════════════════════════
COH_SIGNS = SIGNS
COH_NAK = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
           "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
COH_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]


def test_bg_cohort_declaration_is_the_checked_none_form_with_the_stated_vocabularies():
    e = _decls()["bg_cohort"]
    assert e["prose_fields"] == [] and e["evidence_kind"] == "writer" and ac.prose_none_problem(e) is None
    pn = e["prose_none"]
    assert pn.get("column_scope") is None and pn.get("identifier_columns") is None and pn.get("transcription_columns") is None
    assert [t["table"] for t in e["produced_tables"]] == ["bg_synthetic_cohort", "bg_synthetic_cohort_md"]
    cc = {(c["table"], c["column"]): c["values"] for c in pn["closed_columns"]}
    C, M = "bg_synthetic_cohort", "bg_synthetic_cohort_md"
    assert cc == {(C, "ayanamsha_key"): ["lahiri"], (C, "positions"): COH_SIGNS + COH_NAK, (C, "sampling_method"): ["uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v3"],
                  (C, "source_citation"): ["pyswisseph file-backed Swiss Ephemeris sepl_18/semo_18/seas_18 corpus; Lahiri ayanamsha; TRUE_NODE Rahu; synthetic sampled birth parameters"],
                  (M, "md_lord"): COH_LORDS, (M, "chain_version"): ["vim_md_age_v1"]}
    assert not e["source"].get("columns")                                   # a table-level K3 source: nothing is exempt, so source_citation is closed above
    # the declared closed constants are the writer's CURRENT ones (read from its source, no import): a later bump of SAMPLING_METHOD_VERSION (v2 -> v3 in main #3215) must fail HERE, not read FAIL live
    import re
    src = (SIDECAR / "pipeline" / "orchestrator" / "writers" / "bg_cohort.py").read_text(encoding="utf-8")
    assert re.search(r'^SAMPLING_METHOD_VERSION = "([^"]+)"', src, re.M).group(1) == cc[(C, "sampling_method")][0]
    assert e["source"]["method"] == cc[(C, "sampling_method")][0]       # the source declaration's method text names the same current constant (it was left at v2 after #3215)
    assert re.search(r'^AYANAMSHA_KEY = "([^"]+)"', src, re.M).group(1) == cc[(C, "ayanamsha_key")][0] and re.search(r'^CHAIN_VERSION = "([^"]+)"', src, re.M).group(1) == cc[(M, "chain_version")][0]


def _run_cohort_writer(conn, monkeypatch, n=54):
    """The REAL BgCohortWriter.run on n synthetic charts: only the ephemeris (not available here) and the sampler are replaced; the row dicts, INSERTs and postflight are the writer's own."""
    pytest.importorskip("swisseph")
    from datetime import datetime, timezone
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers import bg_cohort as w
    monkeypatch.setattr(w, "COHORT_SIZE", n)
    monkeypatch.setattr(w, "_require_reproducible_write_runtime", lambda: None)
    monkeypatch.setattr(w, "_require_pinned_ephemeris_runtime", lambda swe, path: "stub")
    monkeypatch.setattr(w, "sample_birth_params", lambda *a, **k: [dict(synthetic_id=i + 1, birth_datetime_utc=datetime(1950 + i % 40, 1 + i % 12, 1 + i % 28, tzinfo=timezone.utc),
                                                                     lat=10.0 + i % 40, lon=20.0 + i) for i in range(n)])

    def fake_positions(birth_dt, lat, lon, swe, ephe_path):
        i = int(lon - 20.0)
        pos = {name: w._parse_sidereal((i * 7.3 + k * 37.1) % 360.0, -0.1 if k % 3 == 0 else 0.5) for k, name in enumerate(["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"])}
        pos["Ketu"] = w._parse_sidereal((pos["Rahu"]["sidereal_longitude"] + 180.0) % 360.0, 0.0)
        pos["Lagna"] = w._parse_sidereal((i * 13.7) % 360.0, 0.0)
        return pos
    monkeypatch.setattr(w, "compute_synthetic_positions", fake_positions)
    res = w.BgCohortWriter().run(ContextSpec(asset_id="bg_cohort", build_id="11111111-1111-1111-1111-111111111111", db_conn=conn, config={}))
    assert res.rows_inserted == n + 10 * n       # WFIX-A: the rows PRESENT across the declared produced set (cohort + its ten-row MD chains), not the cohort rows alone
    return w


def test_bg_cohort_real_writer_rows_stay_inside_every_declared_vocabulary_and_the_engine_reads_na(db, monkeypatch):
    conn = _conn(db)
    _psql(db, "DELETE FROM bg_synthetic_cohort_md")
    _psql(db, "DELETE FROM bg_synthetic_cohort")
    w = _run_cohort_writer(conn, monkeypatch)
    assert w.NAKSHATRA_NAMES == COH_NAK and w.SIGN_NAMES == COH_SIGNS and w.NAK_LORD_CYCLE == COH_LORDS               # the writer's own lists are the declared vocabularies
    leaves = {x for x in _psql(db, "SELECT DISTINCT l.v #>> '{}' FROM bg_synthetic_cohort, jsonb_path_query(positions, 'strict $.**') AS l(v) WHERE jsonb_typeof(l.v) = 'string'").split("\n") if x}
    assert leaves == set(COH_SIGNS) | set(COH_NAK)                                                                    # all 39 words occur in the fixture and nothing else
    assert set(_psql(db, "SELECT DISTINCT md_lord FROM bg_synthetic_cohort_md").split()) == set(COH_LORDS)
    assert _psql(db, "SELECT ayanamsha_key || '|' || sampling_method FROM bg_synthetic_cohort GROUP BY 1").strip() == "lahiri|uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v3"
    got = _measure("bg_cohort", db, monkeypatch, ["bg_cohort.py"], "bg_synthetic_cohort", ["bg_synthetic_cohort", "bg_synthetic_cohort_md"])
    _all_na(got)
    blk = got["Narr.agree"]["prose_none"]
    assert sorted(blk["tables"]) == ["bg_synthetic_cohort", "bg_synthetic_cohort_md"] and sorted((c["table"], c["column"]) for c in blk["closed"]) == sorted(
        (c["table"], c["column"]) for c in _decls()["bg_cohort"]["prose_none"]["closed_columns"])


def test_bg_cohort_mutations_flip_the_reading(db, monkeypatch):
    conn = _conn(db)
    _psql(db, "DELETE FROM bg_synthetic_cohort_md")
    _psql(db, "DELETE FROM bg_synthetic_cohort")
    _run_cohort_writer(conn, monkeypatch, n=12)
    args = ("bg_cohort", db, monkeypatch, ["bg_cohort.py"], "bg_synthetic_cohort", ["bg_synthetic_cohort", "bg_synthetic_cohort_md"])
    _all_na(_measure(*args))
    _psql(db, "UPDATE bg_synthetic_cohort SET sampling_method = 'uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v1' WHERE synthetic_id = 1")          # a pre-rebuild value: honest FAIL
    got = _measure(*args)
    assert got["Narr.agree"]["v"] == FAIL and "sampling_method" in got["Narr.agree"]["measured"]
    _psql(db, "UPDATE bg_synthetic_cohort SET sampling_method = 'uniform_1900_2099_lat60_lon180_true_node_pinned_se1_v3' WHERE synthetic_id = 1")
    _psql(db, "UPDATE bg_synthetic_cohort SET positions = jsonb_set(positions, '{Sun,note}', '\"a strong Sun\"') WHERE synthetic_id = 2")          # a free string leaf in the document
    got = _measure(*args)
    assert got["Narr.agree"]["v"] == FAIL and "positions" in got["Narr.agree"]["measured"]


def test_bg_cohort_the_writers_inserts_name_exactly_the_columns_the_declaration_judges():
    import re
    src = (SIDECAR / "pipeline" / "orchestrator" / "writers" / "bg_cohort.py").read_text(encoding="utf-8")
    cols = {m.group(1): [c.strip() for c in m.group(2).replace("\n", " ").split(",")] for m in re.finditer(r"INSERT INTO (\w+)\s*\(([^)]*)\)", src)}
    assert cols == {"bg_synthetic_cohort": ["synthetic_id", "birth_datetime_utc", "birth_lat", "birth_lon", "ayanamsha_key", "positions", "sampling_method", "source_citation", "build_id", "computed_at"],
                    "bg_synthetic_cohort_md": ["synthetic_id", "md_index", "md_lord", "start_age_years", "end_age_years", "md_full_years", "is_partial", "chain_version", "computed_at"]}


# ═════════════════════════════════════════ bg_sky_calendar ═════════════════════════════════════════
SKY_NAK = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
           "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]
SKY_DETAIL = SIGNS + ["retrograde", "direct", "total", "annular", "annular_total", "partial", "penumbral", "unknown"]


def test_bg_sky_calendar_declaration_is_the_checked_none_form_with_the_stated_vocabularies():
    e = _decls()["bg_sky_calendar"]
    assert e["prose_fields"] == [] and e["evidence_kind"] == "writer" and ac.prose_none_problem(e) is None
    pn = e["prose_none"]
    assert pn.get("column_scope") is None and e.get("produced_tables") is None
    assert {c["column"]: c["values"] for c in pn["closed_columns"]} == {
        "secondary_body": ["Moon", "Sun", "Saturn"], "sign": SIGNS, "nakshatra": SKY_NAK, "detail": SKY_DETAIL, "ayanamsha_key": ["lahiri"],
        "sampling_method": ["sky_calendar_ingress_station_eclipse_doubletransit_v1"],
        "source_citation": ["pyswisseph DE441 (Swiss Ephemeris) via pipeline.transit_search + sol_eclipse_when_glob/lun_eclipse_when; Lahiri ayanamsha"]}
    assert [i["column"] for i in pn["identifier_columns"]] == ["event_type", "primary_body", "secondary_body_key"]
    assert not e["source"].get("columns")                                  # a table-level K3 source: nothing is exempt, so source_citation is closed above
    import re                                                                # the declared constants are the writer's CURRENT ones (read from its source, no import)
    src = (SIDECAR / "pipeline" / "orchestrator" / "writers" / "bg_sky_calendar.py").read_text(encoding="utf-8")
    cc = {c["column"]: c["values"] for c in pn["closed_columns"]}
    assert re.search(r'^SAMPLING_METHOD_VERSION = "([^"]+)"', src, re.M).group(1) == cc["sampling_method"][0] and re.search(r'^AYANAMSHA_KEY = "([^"]+)"', src, re.M).group(1) == cc["ayanamsha_key"][0]


def test_bg_sky_calendar_the_name_lists_and_eclipse_labels_are_the_complete_producer_sets():
    _need(*RUNTIME)
    swe = pytest.importorskip("swisseph")
    from pipeline import transit_search as ts
    from pipeline.orchestrator.writers import bg_sky_calendar as w
    seen = {ts._sign_nak(x / 4.0) for x in range(0, 360 * 4)}                          # every quarter degree of the zodiac
    assert {s for s, _n in seen} == set(SIGNS) and {n for _s, n in seen} == set(SKY_NAK) and list(ts.NAKSHATRAS) == SKY_NAK and list(w.SIGN_NAMES) == SIGNS
    for label, const in w._SOLAR_TYPE_BITS + w._LUNAR_TYPE_BITS:
        assert w._decode_eclipse_type(swe, getattr(swe, const), w._SOLAR_TYPE_BITS + w._LUNAR_TYPE_BITS) == label
        assert label in SKY_DETAIL
    assert w._decode_eclipse_type(swe, 0, w._SOLAR_TYPE_BITS) == "unknown" and w._decode_eclipse_type(swe, 0, w._LUNAR_TYPE_BITS) == "unknown"
    assert {l for l, _c in w._SOLAR_TYPE_BITS + w._LUNAR_TYPE_BITS} | {"unknown"} == {"total", "annular", "annular_total", "partial", "penumbral", "unknown"}
    assert {b for p in w.DOUBLE_TRANSIT_PAIRS for b in p} == {"Jupiter", "Saturn"} and set(w.INGRESS_PLANETS) | set(w.STATION_PLANETS) == set(NINE)


_SKY_BATCH: list = []


def _fill_sky_calendar(db, conn):
    """Real scans (the writer's own scan_* functions on pyswisseph, Moshier here because the pinned corpus is not available; scanned once per run), the writer's own row dict and its own upsert."""
    swe = pytest.importorskip("swisseph")
    from pipeline.orchestrator.writers import bg_sky_calendar as w
    if not _SKY_BATCH:
        rows = []
        for (y0, m0), (y1, m1) in (((2020, 6), (2021, 1)), ((2024, 3), (2024, 11))):          # 2020-21: the Jupiter-Saturn conjunction, annular and total solar eclipses; 2024: total / annular solar, partial lunar
            jd0, jd1 = swe.julday(y0, m0, 1, 0.0), swe.julday(y1, m1, 1, 0.0)
            rows += w.scan_ingresses(swe, jd0, jd1) + w.scan_stations(swe, jd0, jd1) + w.scan_eclipses(swe, jd0, jd1) + w.scan_double_transits(swe, jd0, jd1)
        _SKY_BATCH.extend(w.BgSkyCalendarWriter._to_insert_dict(r, "11111111-1111-1111-1111-111111111111") for r in rows)
    _psql(db, "DELETE FROM bg_sky_calendar")
    with conn.cursor() as cur:
        w.BgSkyCalendarWriter._flush_batch(cur, [dict(r) for r in _SKY_BATCH])
    return len(_SKY_BATCH)


def test_bg_sky_calendar_real_scan_rows_stay_inside_every_declared_vocabulary_and_the_engine_reads_na(db, monkeypatch):
    conn = _conn(db)
    n = _fill_sky_calendar(db, conn)
    assert n > 200 and int(_psql(db, "SELECT count(*) FROM bg_sky_calendar").strip()) == n
    kinds = set(_psql(db, "SELECT DISTINCT event_type FROM bg_sky_calendar").split())
    assert kinds == {"ingress", "station", "eclipse_solar", "eclipse_lunar", "double_transit"}
    leaves = {x for x in _psql(db, "SELECT DISTINCT l.v #>> '{}' FROM bg_sky_calendar, jsonb_path_query(detail, 'strict $.**') AS l(v) WHERE jsonb_typeof(l.v) = 'string'").split("\n") if x}
    assert leaves <= set(SKY_DETAIL) and {"retrograde", "direct", "total", "annular", "partial", "penumbral"} <= leaves and set(SIGNS) <= leaves
    assert set(_psql(db, "SELECT DISTINCT secondary_body FROM bg_sky_calendar WHERE secondary_body IS NOT NULL").split()) == {"Moon", "Sun", "Saturn"}
    got = _measure("bg_sky_calendar", db, monkeypatch, ["bg_sky_calendar.py"], "bg_sky_calendar", ["bg_sky_calendar"])
    _all_na(got)
    blk = got["Narr.agree"]["prose_none"]
    assert sorted(blk["identifier_columns"]) == ["bg_sky_calendar.event_type", "bg_sky_calendar.primary_body", "bg_sky_calendar.secondary_body_key"]
    assert sorted(c["column"] for c in blk["closed"]) == sorted(c["column"] for c in _decls()["bg_sky_calendar"]["prose_none"]["closed_columns"])


def test_bg_sky_calendar_mutations_flip_the_reading(db, monkeypatch):
    conn = _conn(db)
    _fill_sky_calendar(db, conn)
    args = ("bg_sky_calendar", db, monkeypatch, ["bg_sky_calendar.py"], "bg_sky_calendar", ["bg_sky_calendar"])
    _all_na(_measure(*args))
    _psql(db, "UPDATE bg_sky_calendar SET detail = detail || '{\"note\": \"a malefic ingress\"}'::jsonb WHERE id = (SELECT min(id) FROM bg_sky_calendar WHERE event_type = 'ingress')")
    got = _measure(*args)
    assert got["Narr.agree"]["v"] == FAIL and "detail" in got["Narr.agree"]["measured"]
    _psql(db, "UPDATE bg_sky_calendar SET detail = '{}'::jsonb WHERE detail ? 'note'")
    _psql(db, "UPDATE bg_sky_calendar SET nakshatra = 'Mrigasira' WHERE id = (SELECT min(id) FROM bg_sky_calendar WHERE nakshatra IS NOT NULL)")                # the cohort spelling, not the sky calendar's
    got = _measure(*args)
    assert got["Narr.agree"]["v"] == FAIL and "nakshatra" in got["Narr.agree"]["measured"]


def test_bg_sky_calendar_the_writers_insert_names_exactly_the_columns_the_declaration_judges():
    src = (SIDECAR / "pipeline" / "orchestrator" / "writers" / "bg_sky_calendar.py").read_text(encoding="utf-8")
    i = src.index("INSERT INTO bg_sky_calendar")
    cols = [c.strip() for c in src[src.index("(", i) + 1: src.index(")", i)].replace("\n", " ").split(",")]
    assert cols == ["event_type", "primary_body", "secondary_body", "event_jd", "event_datetime_utc", "sign", "nakshatra", "longitude_deg", "speed_dps", "detail", "ayanamsha_key",
                    "sampling_method", "source_citation", "build_id", "computed_at"]


# ═════════════════════════════════════════ bg_medical_mappings (the checked prose_none completed over its sibling tables) ═════════════════════════════════════════
MM_TABLES = ["bg_medical_mappings", "bg_nakshatra_medical", "bg_sign_medical"]


def test_bg_medical_mappings_declaration_covers_every_text_column_of_its_three_produced_tables():
    e = _decls()["bg_medical_mappings"]
    assert e["prose_fields"] == [] and ac.prose_none_problem(e) is None and [t["table"] for t in e["produced_tables"]] == MM_TABLES
    pn = e["prose_none"]
    got = {(x.get("table") or "bg_medical_mappings", x["column"]): k for k in ("closed_columns", "transcription_columns", "identifier_columns") for x in pn[k]}
    assert {c for t, c in got if t == "bg_nakshatra_medical"} == {"nakshatra_name", "body_part", "dosha", "classical_citation"}
    assert {c for t, c in got if t == "bg_sign_medical"} == {"sign_name", "body_part", "organ_systems", "element", "dosha", "classical_citation"}
    assert got[("bg_nakshatra_medical", "nakshatra_name")] == "identifier_columns" and got[("bg_sign_medical", "sign_name")] == "identifier_columns"
    assert got[("bg_sign_medical", "element")] == "closed_columns" and got[("bg_sign_medical", "dosha")] == "closed_columns" and got[("bg_nakshatra_medical", "dosha")] == "closed_columns"
    assert {(x["table"], x["column"]): x["values"] for x in pn["closed_columns"] if x.get("table")} == {
        ("bg_nakshatra_medical", "dosha"): ["vata", "pitta", "kapha"], ("bg_sign_medical", "dosha"): ["pitta", "kapha", "vata"], ("bg_sign_medical", "element"): ["fire", "earth", "air", "water"]}


def test_bg_medical_mappings_the_seed_rows_are_literals_and_the_writer_binds_them_verbatim():
    """AST proof of the transcription claim: NAKSHATRA_MEDICAL and SIGN_MEDICAL hold only literal strings, numbers and lists of strings (or a module-level string constant), and the loader's execute
    parameters for both tables are plain `row["<column>"]` subscripts: no f-string, join, slice, call or format touches any value on its way into the table."""
    import ast
    src = (SIDECAR / "brahmagyan" / "l0_medical.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    consts = {n.targets[0].id for n in tree.body if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str) and isinstance(n.targets[0], ast.Name)}
    assert {"AH_HS_BPHS_CH3", "KALAPURUSHA"} <= consts

    def literal(v):
        return (isinstance(v, ast.Constant) and isinstance(v.value, (str, int))) or (isinstance(v, ast.Name) and v.id in consts) or (isinstance(v, ast.List) and all(literal(x) for x in v.elts))
    for name, n_rows in (("NAKSHATRA_MEDICAL", 27), ("SIGN_MEDICAL", 12)):
        node = next(n for n in tree.body if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == name).value
        assert isinstance(node, ast.List) and len(node.elts) == n_rows
        for row in node.elts:
            assert isinstance(row, ast.Dict) and all(isinstance(k, ast.Constant) and literal(v) for k, v in zip(row.keys, row.values)), (name, ast.dump(row)[:200])
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "seed_medical_mappings")
    seen = 0
    for call in (n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "execute" and len(n.args) == 2):
        if getattr(call.args[0], "id", "") in ("nak_sql", "sign_sql"):
            assert isinstance(call.args[1], ast.Tuple) and all(isinstance(x, ast.Subscript) and getattr(x.value, "id", "") == "row" and isinstance(x.slice, ast.Constant) for x in call.args[1].elts)
            seen += 1
    assert seen == 2


def test_bg_medical_mappings_the_engine_reads_every_cell_na_over_the_three_tables_the_real_loader_seeds(db, monkeypatch):
    from brahmagyan import l0_medical as l0
    conn = _conn(db)
    for t in MM_TABLES:
        _psql(db, f"DELETE FROM {t}")
    l0.seed_medical_mappings(conn, "11111111-1111-1111-1111-111111111111", autocommit=False)
    assert [int(_psql(db, f"SELECT count(*) FROM {t}").strip()) for t in MM_TABLES] == [21, 27, 12]
    args = ("bg_medical_mappings", db, monkeypatch, ["bg_medical_mappings.py"], "bg_medical_mappings", MM_TABLES)
    got = _measure(*args)
    _all_na(got)
    blk = got["Narr.agree"]["prose_none"]
    assert sorted(blk["tables"]) == sorted(MM_TABLES) and "bg_sign_medical.sign_name" in blk["identifier_columns"] and "bg_nakshatra_medical.body_part" in blk["transcription_columns"]
    # the previous declaration (no entry for the two sibling tables) reads FAIL on the same database: the ten columns were open
    old = _decls()["bg_medical_mappings"]
    pn = old["prose_none"]
    for k in ("closed_columns", "transcription_columns", "identifier_columns"):
        pn[k] = [x for x in pn[k] if not x.get("table")]
    got = _measure(*args, decl=old)
    assert got["Narr.agree"]["v"] == FAIL and "bg_sign_medical.element" in got["Narr.agree"]["measured"] and "bg_nakshatra_medical.nakshatra_name" in got["Narr.agree"]["measured"]
    # a closed column's closure is checked on data
    _psql(db, "UPDATE bg_sign_medical SET element = 'fire' WHERE sign_number = 1")
    _all_na(_measure(*args))
    try:
        _psql(db, "ALTER TABLE bg_sign_medical DROP CONSTRAINT IF EXISTS bg_sign_medical_element_check")
        _psql(db, "UPDATE bg_sign_medical SET element = 'the sign of the head' WHERE sign_number = 1")
        got = _measure(*args)
        assert got["Narr.agree"]["v"] == FAIL and "element" in got["Narr.agree"]["measured"]
    finally:
        _psql(db, "DROP TABLE bg_sign_medical")
        _psql(db, SIGN_MEDICAL_DDL)
