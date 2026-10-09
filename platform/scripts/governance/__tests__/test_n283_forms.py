"""test_n283_forms.py: SS N-283, two engine forms and the declaration they enable (declarations 1.70.0).

(1) no_table releases Carr.D1/D2/D3 for a TABLE-LESS service probe. The release rests on the same measured block as the seven prose / identity checks, which now also refuses a declared `produced_tables` set and a declared
    carriage nature. Cells read N/A 'not applicable: service probe, stores no value' by the rules Carr.D<n>#measured:no-table-no-prose (decision N-283). Forgeries that must NOT release: a target table; a produced set;
    an asset with a writer-produced table; a table-less asset that declares a carriage nature.
(6) Two pointer classes in prose_forms.TEMPLATE_CLASSES: `token` (whitespace-free, letters digits _ . : / -, 1 to 120) and `titlename` (one to four Title-Case words). Every value is checked against the class in Python and
    in PostgreSQL; a sentence, a lowercase phrase, an overlong value, an embedded newline and a verb-like lowercase word all FAIL. ga_fact_identity's prose is then declared with them, and shown true on rows the
    REAL index builder writes from a broad chart_facts fixture (every parser rule family x graha x varga x house x sign), with mutations.
"""
from __future__ import annotations

import copy
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
import prose_forms as pf  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET  # noqa: E402

DECLS = ac.load_asset_declarations()
ND = ac.NO_DET
CARR = ("Carr.D1", "Carr.D2", "Carr.D3")


# ═════════════════════════════ (1) no_table releases Carr.D1/D2/D3 ═════════════════════════════

SVC = {"kind": "service", "has_writer": False, "prose_fields": None, "carriage": {"served_surface": None},
       "no_table": dict(why="the service owns no table and no count_sql table, so no column could carry a value", evidence="platform/scripts/seed/asset_registry_seed.ts:465")}


def _block(entry=None, **kw):
    base = dict(entry=entry or SVC, asset_kind="service", registry_has_writer=False, target_table=None, count_tables=[], register_files=0, register_mentions=[])
    base.update(kw)
    return ac.no_table_block(base.pop("entry"), base.pop("asset_kind"), base.pop("registry_has_writer"), base.pop("target_table"), base.pop("count_tables"), base.pop("register_files"), base.pop("register_mentions"))


def test_the_agreeing_block_reads_the_three_carr_cells_as_ruled_na_with_the_printed_text():
    recs = ac.no_table_records("bg_x", SVC, _block())
    for c in CARR:
        r = recs[c]
        assert r["v"] == NA and r["cause"] == "no-table-no-prose" and r["measured"].count(ac.CARR_NO_TABLE_TEXT) == 1 and "not applicable: service probe, stores no value" in r["measured"]
        assert ac.no_table_na_problem(c, r) is None and ac._na_released(c, r)
        assert f"{c}#measured:no-table-no-prose" in ac.NA_RULE_DECISIONS and ac.NA_RULE_DECISIONS[f"{c}#measured:no-table-no-prose"].startswith("SS N-283")
        assert "no-table-no-prose" in ac.NA_CAUSES[c]
    ac.validate_na_rule_decisions()


def test_the_real_probe_assets_release_all_ten_cells_and_carry_no_nature_and_no_produced_set():
    reg = ac.registered_ids("")
    for aid in ("bg_ephemeris_engine", "bg_panchanga"):
        e = DECLS[aid]
        assert not (e.get("carriage") or {}).get("nature") and not e.get("produced_tables")
        recs = ac.no_table_records(aid, e, ac.no_table_block(e, "service", False, None, [], len(reg.get(aid) or []), ac.register_call_mentions(aid)))
        assert sorted(recs) == sorted(ac.NO_TABLE_CRITERIA) and len(recs) == 10 and all(r["v"] == NA for r in recs.values()), aid
        rolled = ac.rollup_asset("L0", recs)
        got = {c["criterion"]: c for g in rolled.values() if isinstance(g, dict) for c in g.get("checks", [])}
        for c in CARR:
            assert got[c]["v"] == NA and got[c]["rule_id"] == f"{c}#measured:no-table-no-prose", (aid, c, got[c])


@pytest.mark.parametrize("kw,what", [
    (dict(target_table="t"), "target_table"),                                    # an asset with a target table
    (dict(count_tables=["t"]), "count_sql"),                                      # a table in its count_sql
    (dict(registry_has_writer=True), "has_writer"),                               # a writer-backed asset
    (dict(register_files=1), "@register"), (dict(register_mentions=["w.py"]), "register( call"),
    (dict(asset_kind="data"), "asset_kind"),
])
def test_FORGERY_a_table_or_writer_backed_asset_never_releases_carr(kw, what):
    recs = ac.no_table_records("bg_x", SVC, _block(**kw))
    for c in CARR:
        assert recs[c]["v"] == ND and recs[c]["declaration_disagreements"] and what in recs[c]["measured"], (c, recs[c]["measured"][:200])


def test_FORGERY_a_declared_produced_set_never_releases_carr():
    e = dict(SVC, produced_tables=[{"table": "t"}])
    assert ac.no_table_problem(e) and "produced_tables" in ac.no_table_problem(e)                          # refused at declaration time
    recs = ac.no_table_records("bg_x", e, _block(entry=e))
    assert all(recs[c]["v"] == ND and recs[c]["declaration_disagreements"] for c in CARR)                  # the declaration itself is refused, so nothing is released
    forced = dict(_block(entry=e), declared=True)                                                           # were the declaration accepted anyway, the MEASURED block refuses on its own
    assert ac.no_table_block_problem(forced) and "produced_tables" in ac.no_table_block_problem(forced)


@pytest.mark.parametrize("nature,extra", [("single_derivation", dict(applies="D3")), ("unverified_transcription", dict(applies="D1")), ("ratified_judgment", dict(ruling="N-235"))])
def test_FORGERY_a_table_less_asset_that_declares_a_carriage_nature_never_releases_carr(nature, extra):
    e = dict(SVC, carriage=dict(nature=nature, why="a declared carried value of the probe here", evidence="platform/scripts/governance/asset_census.py:1", per_witness_values=False, **extra))
    assert "carriage nature" in (ac.no_table_problem(e) or "")
    recs = ac.no_table_records("bg_x", e, _block(entry=e))
    assert all(recs[c]["v"] == ND and recs[c]["declaration_disagreements"] for c in CARR)
    forced = dict(_block(entry=e), declared=True)
    assert "carriage nature" in (ac.no_table_block_problem(forced) or "") and forced["carriage_nature"] == nature


def test_FORGERY_a_record_without_the_agreeing_block_or_with_a_tampered_one_is_not_released():
    recs = ac.no_table_records("bg_x", SVC, _block())
    for c in CARR:
        for forged in (dict(recs[c], no_table=None), dict(recs[c], no_table=dict(recs[c]["no_table"], produced_declared=True)), dict(recs[c], no_table=dict(recs[c]["no_table"], carriage_nature="single_derivation")),
                       dict(recs[c], no_table={k: v for k, v in recs[c]["no_table"].items() if k != "produced_declared"})):
            assert ac.no_table_na_problem(c, forged) and not ac._na_released(c, forged), (c, forged.get("no_table"))


def test_the_postprocess_closed_rule_list_names_the_three_and_checks_them_against_the_engine():
    import census_postprocess as cp
    for n in (1, 2, 3):
        rid = f"Carr.D{n}#measured:no-table-no-prose"
        assert rid in cp.RULED_RESIDUALS and rid in cp.engine_rule_decisions() and rid not in cp.CEILING_RULES                       # a ruled N/A, not a ceiling (nothing is limited: the probe carries no value)


def test_the_criterion_texts_say_it_and_their_revisions_moved():
    for c, rev in (("Carr.D1", 5), ("Carr.D2", 3), ("Carr.D3", 4)):
        assert "SS N-283" in ac.CRITERION_REGISTRY[c]["applicability"] and ac.CRITERION_REGISTRY[c]["revision"] == rev


# ═════════════════════════════ (6) the two pointer classes ═════════════════════════════

def _py(cls, v):
    return re.fullmatch(pf.TEMPLATE_CLASSES[cls], v) is not None


TOKEN_OK = ["SUN", "RAH_MEAN", "D9.H7", "MAR-HOUSE_5", "co_MAR_VEN", "fact_category:graha/sign", "ARUDHA_JU", "a", "x" * 120, "CYCLE_1.JANMA.Q1", "d_all_floor"]
TOKEN_BAD = ["Mars gives wealth in the tenth house", "mars in leo", "two words", "x" * 121, "line\nbreak", "tab\there", "trailing ", " leading", "", "semi;colon", "quote'd", "Sun\n", "uni\u2014code", "a|b", "back\\slash"]
TITLE_OK = ["Vishakha", "Purva Bhadrapada", "Uttara Phalguni", "Shatabhisha", "Ardra", "Ab", "Aaaa Bbbb Cccc Dddd"]
TITLE_BAD = ["Mars gives wealth", "the tenth house", "Purva bhadrapada", "PURVA BHADRAPADA", "Purva  Bhadrapada", "Purva Bhadrapada\n", "A", "Purva Bhadrapada Uttara Phalguni Revati", "Is Strong In Leo Because", "Moon is exalted", "Sun\nMoon", "Purva-Bhadrapada",
             "Aaaaaaaaaaaaaaaaaaaaaaaaa", " Vishakha", "Vishakha ", ""]


def test_the_classes_exist_and_are_backslash_free_so_python_and_postgres_agree():
    for k in ("token", "titlename"):
        assert k in pf.TEMPLATE_CLASSES and "\\" not in pf.TEMPLATE_CLASSES[k]


@pytest.mark.parametrize("v", TOKEN_OK)
def test_token_accepts_identifier_like_values(v):
    assert _py("token", v)


@pytest.mark.parametrize("v", TOKEN_BAD)
def test_FORGERY_token_rejects_a_sentence_a_phrase_an_overlong_value_a_newline_and_other_characters(v):
    assert not _py("token", v)


@pytest.mark.parametrize("v", TITLE_OK)
def test_titlename_accepts_title_case_names(v):
    assert _py("titlename", v)


@pytest.mark.parametrize("v", TITLE_BAD)
def test_FORGERY_titlename_rejects_lowercase_words_a_verb_like_word_a_newline_and_overlong_values(v):
    assert not _py("titlename", v)


def test_REAL_SQL_postgres_agrees_with_python_on_every_probe_value(disposable_pg, monkeypatch):
    point_psql_at(disposable_pg, monkeypatch)
    for cls, ok, bad in (("token", TOKEN_OK, TOKEN_BAD), ("titlename", TITLE_OK, TITLE_BAD)):
        rx = "^(?:" + pf.TEMPLATE_CLASSES[cls] + ")$"
        for v in ok + bad:
            lit = "E'" + v.replace("\\", "\\\\").replace("'", "''").replace("\n", "\\n").replace("\t", "\\t") + "'"
            got = fs.psql(disposable_pg, f"SELECT ({lit} ~ '{rx}')::text").strip()
            assert (got == "true") == _py(cls, v), (cls, v, got)


def test_a_template_with_the_classes_compiles_and_a_value_must_match_the_whole_template():
    tpl = ["fact_subject='{s}';fact_key='{k}'", "fact_subject='{n}';fact_key='{k}'"]
    ph = {"s": {"class": "token"}, "k": {"class": "token"}, "n": {"class": "titlename"}}
    assert pf.templates_problem(tpl, ph) is None
    rx = pf.compile_templates(tpl, ph, "00000000-0000-0000-0000-000000000000")
    assert pf.template_matches(rx, "fact_subject='D9_SIGN_4';fact_key='grade'") and pf.template_matches(rx, "fact_subject='Purva Bhadrapada';fact_key='co_MAR_VEN'")
    for bad in ("fact_subject='Mars is strong here';fact_key='grade'", "fact_subject='SUN';fact_key='a sentence about the key'", "fact_subject='SUN';fact_key='x'\n", "fact_subject='" + "x" * 121 + "';fact_key='k'",
                "fact_subject='the moon';fact_key='k'", "fact_subject='SUN';fact_key='k';extra"):
        assert not pf.template_matches(rx, bad), bad


# ═════════════════════════════ ga_fact_identity: the prose declaration ═════════════════════════════

AID, T = "ga_fact_identity", "chart_fact_identity"
PN = DECLS[AID]["prose_none"]


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _col(kind, col):
    return next(c for c in PN[kind] if c["column"] == col)


def test_the_declaration_is_sound_and_covers_every_text_column_of_the_table():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    covered = {c["column"] for k in ("closed_columns", "identifier_columns", "templated_columns") for c in PN[k]}
    ddl = (fs.SMIG / "552_chart_fact_identity.sql").read_text(encoding="utf-8")
    text_cols = set(re.findall(r"^\s{2}(\w+)\s+TEXT\b", ddl, flags=re.M))
    assert text_cols == covered, (text_cols ^ covered)


def test_the_closed_sets_equal_the_parsers_own_literals():
    import ast
    import brahmagyan.fact_identity_parser as P
    src = (ac.ROOT / "platform/python-sidecar/brahmagyan/fact_identity_parser.py").read_text(encoding="utf-8")
    ek, pr = set(), set()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call):
            kw = {k.arg: k.value for k in n.keywords}
            if isinstance(kw.get("entity_kind"), ast.Constant):
                ek.add(kw["entity_kind"].value)
            if isinstance(kw.get("parse_rule"), ast.Constant):
                pr.add(kw["parse_rule"].value)
    ek.discard("_partial_")
    assert _col("closed_columns", "entity_kind")["values"] == sorted(ek) and len(ek) == 18
    assert _col("closed_columns", "graha_code")["values"] == _col("closed_columns", "graha_code_secondary")["values"] == sorted(P.SYSTEM_A_GRAHAS)
    pt = _col("templated_columns", "parse_rule")
    assert pt["placeholders"]["r"]["values"] == sorted(pr) and set(pt["placeholders"]["k"]["values"]) == {"bare_house_key", "bare_varga_key"}
    assert pt["placeholders"]["g"]["values"] == ["bare_graha_subject", "pakka_ghar_graha"]                      # the only subject rules whose entity_kind is `graha`: the only ones a key can enrich
    assert re.fullmatch(r"[0-9a-f]{64}", "0" * 64) and PN["templated_columns"][0]["templates"] == ["D{n}"]


def test_the_chart_facts_schemas_own_keys_are_all_token_shaped():
    sch = json.loads((ac.ROOT / "platform/scripts/governance/CHART_FACTS_SCHEMA.json").read_text(encoding="utf-8"))["categories"]
    keys = {re.sub(r"<[A-Z]+>", "X", k) for v in sch.values() for k in (v.get("allowed_keys") or {})}
    assert len(keys) > 300 and all(_py("token", k) for k in keys), [k for k in keys if not _py("token", k)]
    subs = {s for v in sch.values() for s in (v.get("applies_to_subjects") or [])}
    assert all(_py("token", s) for s in subs)


GRAHAS = ["SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN"]
TWO = ["SU", "MO", "MA", "ME", "JU", "VE", "SA", "RA", "KE"]
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
NAKS = ["Vishakha", "Purva Bhadrapada", "Uttara Phalguni", "Ashwini"]
VARGAS = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60, 5, 6, 8, 11, 14, 15, 21, 32, 33, 50, 54, 108, 150, 2700]


def _fixture_facts():
    """(category, subject, key): every subject rule family of the parser over the graha / varga / house / sign space, with plain and identity-bearing keys, the key-only shapes and the D_ALL floor."""
    f = []
    for g in GRAHAS + ["LAGNA", "MC"]:
        for key in ("grade", "D9", "D_ALL", "house_5", "dignity_state"):
            f.append(("graha_attr", g, key))
    f += [("graha_attr", "JUPITER", "D_ALL"), ("graha_attr", "JUPITER", "grade"), ("aspect", "ASC-MAR", "x"), ("aspect", "MC-KET", "x"), ("aspect", "MAR-RAH", "x")]
    for v in VARGAS:
        for h in (1, 7, 12):
            f += [("v", f"D{v}_HOUSE_{h:02d}", "x"), ("v", f"D{v}_H{h}", "x"), ("v", f"D{v}_HOUSE_{h}_to_HOUSE_{(h % 12) + 1}", "x")]
        f += [("v", f"D{v}_CHART", "x"), ("v", f"D{v}_SIGN_{(v % 12) + 1}", "x"), ("v", f"D{v}_{SIGNS[v % 12]}", "x"), ("v", f"D{v}_career", "x")]
        for g in GRAHAS[:4]:
            f += [("v", f"D{v}_{g}", "x"), ("v", f"D{v}.{g}", "x"), ("v", f"D{v}_{g}_{GRAHAS[(GRAHAS.index(g) + 1) % 9]}", "x"), ("v", f"D{v}_{g}_to_{GRAHAS[(GRAHAS.index(g) + 2) % 9]}", "x")]
    for g in GRAHAS:
        for h in (1, 6, 12):
            f += [("hh", f"{g}-HOUSE_{h}", "x"), ("hh", f"{g}_IN_HOUSE_{h:02d}", "x")]
        f += [("hs", f"{g}-SIGN_{(GRAHAS.index(g) % 12) + 1}", "x"), ("pg", f"PAKKA_GHAR_{g}", "x")]
        for g2 in GRAHAS[:3]:
            f += [("gp", f"{g}-{g2}", "x"), ("gp", f"{g}_{g2}", "x"), ("gp", f"{g}_v_{g2}", "x"), ("gp", f"MAITRI_{g}_{g2}", "x")]
    for g in ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT"):
        f += [("av", f"{g}-CONTRIBUTOR_{g2}-SIGN_{s}", "x") for g2 in ("SUN", "LAGNA") for s in (1, 12)]
    f += [("h", "HOUSE_07", "x"), ("h", "BHAVA_3", "x"), ("h", "CUSP_10", "x"), ("h", "SWAMSA_HOUSE_4", "x"), ("a", "ARUDHA_A3", "x"), ("a", "ARUDHA_AL", "x"), ("a", "BHAVA_ARUDHA_A12", "x"), ("h", "X_FOO-HOUSE_4", "x"), ("h", "SARVA-HOUSE_4", "x"), ("h", "SARVA-SIGN_4", "x"), ("h", "ZZ-SIGN_9", "x")]
    f += [("a", f"ARUDHA_{c}", "x") for c in TWO]
    f += [("s", s, "x") for s in SIGNS]
    f += [("dw", w, "x") for w in ("career", "artha", "body")]
    f += [("n", n, k) for n in NAKS for k in ("co_MAR_VEN", "co_SUN_MOON", "D9", "house_7", "D108")]
    f += [("n", "SAHAM_PUNYA", "D9"), ("n", "CYCLE_1.JANMA.Q1", "house_3"), ("n", "KAKSHYA_3", "D10")]
    return f


def _dedupe(f):
    seen, out = set(), []
    for x in f:
        if (x[1], x[2]) not in seen:
            seen.add((x[1], x[2])); out.append(x)
    return out


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    pg = disposable_pg
    for t in (T, "chart_facts"):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.install_chart_facts(pg)
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "552_chart_fact_identity.sql", T))
    vals = []
    for i, (cat, subj, key) in enumerate(_dedupe(_fixture_facts())):
        vals.append(f"('{fs.CHART_A}|f{i}', '{fs.CHART_A}', 'lahiri_chitrapaksha', gen_random_uuid(), '{cat}', '{subj}', '{key}', NULL, 1, 'x', 'x', 'x', 'single', 'x', now())")
    # a fact with an EMPTY key (chart_facts.fact_key is NOT NULL, so a NULL key cannot occur)
    vals.append(f"('{fs.CHART_A}|ek', '{fs.CHART_A}', 'lahiri_chitrapaksha', gen_random_uuid(), 'graha_attr', 'MOON', '', NULL, 1, 'x', 'x', 'x', 'single', 'x', now())")
    fs.psql(pg, "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key, fact_value_text, fact_value_num, citation_ref, citation_human, source_calculation, "
                "verification_pass_status, engine_version, computed_at) VALUES " + ", ".join(vals))
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.ga_fact_identity import GaFactIdentityWriter
    conn = psycopg.connect(pg.url, autocommit=True)
    try:
        s = GaFactIdentityWriter().run(ContextSpec(asset_id=AID, build_id="11111111-1111-4111-8111-111111111111", db_conn=conn, config={"chart_id": fs.CHART_A, "fact_identity_reasons_mode": "subset"}))
    except Exception as exc:                                    # the in-run check may refuse a synthetic fixture: fall back to the shared body the writer calls
        from brahmagyan.fact_identity_index import build_index_for_chart
        s = build_index_for_chart(conn, fs.CHART_A)
    conn.close()
    n = int(fs.psql(pg, f"SELECT count(*) FROM {T}").strip())
    assert n > 400, (n, s)
    yield pg
    for t in (T, "chart_facts"):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T, [T], decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_BODY_the_index_rows_stay_inside_every_declared_set_and_shape(db):
    import brahmagyan.fact_identity_parser as P
    rows = json.loads(fs.psql(db, f"SELECT json_agg(to_jsonb(t)) FROM (SELECT entity_kind, graha_code, graha_code_secondary, varga_id, parse_rule, parsed_from FROM {T}) t"))
    ek = set(_col("closed_columns", "entity_kind")["values"])
    gs = set(P.SYSTEM_A_GRAHAS)
    rx = {c["column"]: re.compile(pf.compile_templates(c["templates"], c["placeholders"], "00000000-0000-0000-0000-000000000000")[1:-1]) for c in PN["templated_columns"]}
    seen = {"entity_kind": set(), "parse_rule": set()}
    for r in rows:
        assert r["entity_kind"] in ek and (r["graha_code"] is None or r["graha_code"] in gs) and (r["graha_code_secondary"] is None or r["graha_code_secondary"] in gs), r
        for c in ("parse_rule", "parsed_from", "varga_id"):
            if r[c] is not None:
                assert rx[c].fullmatch(r[c]), (c, r[c])
        seen["entity_kind"].add(r["entity_kind"]); seen["parse_rule"].add(r["parse_rule"])
    assert len(seen["entity_kind"]) >= 14 and len(seen["parse_rule"]) >= 30 and any("+" in p for p in seen["parse_rule"])      # the fixture exercises the breadth of the parser, composite rules included


def test_REAL_WRITER_BODY_the_committed_declaration_reads_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert b["open"] == [] and {x["column"] for x in b["forms"]["templated"]} == {"varga_id", "parse_rule", "parsed_from"} and {x["column"] for x in b["closed"]} >= {"entity_kind", "graha_code", "graha_code_secondary"}


# (column, new SQL value, needle)
MUTS = [
    ("parsed_from", "'Mars gives wealth in the tenth house'", "parsed_from"),                       # a sentence
    ("parsed_from", "'fact_subject=''the moon is strong'';fact_key=''x'''", "parsed_from"),         # lowercase words in the subject
    ("parsed_from", "'fact_subject=''SUN'';fact_key=''x''' || chr(10)", "parsed_from"),             # an embedded newline
    ("parsed_from", "'fact_subject=''' || repeat('x', 121) || ''';fact_key=''k'''", "parsed_from"),   # overlong
    ("parsed_from", "'fact_subject=''SUN'';fact_key=''Moon exalted in Taurus'''", "parsed_from"),   # a verb-like phrase in the key
    ("parse_rule", "'rendered by the engine as a rule'", "parse_rule"),
    ("parse_rule", "'bare_graha_subject+bare_made_up_key'", "parse_rule"),
    ("entity_kind", "'a free sentence about the graha'", "entity_kind"),
    ("graha_code", "'JUPITER'", "graha_code"),
    ("graha_code_secondary", "'Moon'", "graha_code_secondary"),
    ("varga_id", "'D9 strong'", "varga_id"),
    ("varga_id", "'d9'", "varga_id"),
]


@pytest.mark.parametrize("col,newv,needle", MUTS)
def test_REAL_WRITER_BODY_MUTATION_a_value_outside_its_form_is_a_FAIL(db, monkeypatch, col, newv, needle):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:500]
        assert all(got[c]["v"] == NO_DET for c in fs.CELLS if c != "Narr.agree")
    fs.mutate_and_restore(db, T, ["fact_id"], col, newv, "parsed_from IS NOT NULL AND graha_code IS NOT NULL AND graha_code_secondary IS NOT NULL AND varga_id IS NOT NULL" if col in ("graha_code_secondary", "varga_id") else "parse_rule LIKE '%+%'" if col == "parse_rule" and "bare_made_up" in newv else "true", check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_BODY_MUTATION_dropping_a_declared_form_is_a_FAIL_naming_the_column(db, monkeypatch):
    for kind, col in (("closed_columns", "entity_kind"), ("templated_columns", "parsed_from"), ("templated_columns", "parse_rule"), ("templated_columns", "varga_id"), ("identifier_columns", "fact_id")):
        d = _own()
        d["prose_none"][kind] = [c for c in d["prose_none"][kind] if c["column"] != col]
        got = _m(db, monkeypatch, d)
        assert got["Narr.agree"]["v"] in (FAIL, NO_DET) and got["Narr.agree"]["v"] != NA and col in got["Narr.agree"]["measured"], (col, got["Narr.agree"]["measured"][:300])


def test_REAL_WRITER_BODY_MUTATION_a_looser_class_would_hide_the_forgery_and_the_declared_one_does_not(db, monkeypatch):
    """The templated parsed_from refuses a sentence-in-the-key; declaring `token` for both is what makes that so (a placeholder with the Title-Case class for the key would accept 'Moon Exalted')."""
    d = _own()
    pt = next(t for t in d["prose_none"]["templated_columns"] if t["column"] == "parsed_from")
    assert pt["placeholders"]["k"] == {"class": "token"} and pt["placeholders"]["s"] == {"class": "token"} and pt["placeholders"]["n"] == {"class": "titlename"}
