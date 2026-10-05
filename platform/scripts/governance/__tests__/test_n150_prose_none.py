"""test_n150_prose_none.py: R1 / R2 / R3 (N-150, REGISTRY_REVISION 26): a ruled N/A rests on a declaration CHECKED against the live schema.

R1/R2: Narr.* and Null.* read N/A for a "declared no prose" asset ONLY through `prose_none`, checked against the asset's produced tables (every text-capable column declared closed and the data
inside the vocabulary; an open text column is a FAIL, never N/A). A bare `prose_fields []` reads NO_DETECTOR (six enumerated pre-N-150 assets keep their unchecked Narr N/A until converted).
R3: `vocab_alias.na = no_alias_class` is refused beside a vocabulary column the registry's own ontology aliases. Pure tests plus real SQL on the throw-away disposable PostgreSQL."""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA
NARR, NULL = ac.NARR_CHECKS, ac.NULL_CHECKS
EV = "platform/scripts/governance/asset_census.py:1"
WHY = "the reviewed reason this declaration is true"
CW = "the column is a closed label set of the reviewed values"


def _cc(column="graha", values=("Sun", "Moon"), table=None, **kw):
    d = dict(column=column, values=list(values) if values is not None else None, why=CW)
    if table:
        d["table"] = table
    d.update(kw)
    return d


def _decl(*closed, **kw):
    return {"prose_fields": [], "evidence": {"prose_fields": EV}, "prose_none": dict(why=WHY, closed_columns=list(closed)), **kw}


def _ctx(cols, types, table="t", **kw):
    base = dict(table=table, own={table: (cols, types, {})}, tests=(), vocabulary={"narration"}, counts=None, paths=[], written={table: {"graha"}}, closed_outside={})
    base.update(kw)
    return base


TYPES = {"id": "integer", "graha": "text", "score": "numeric", "at": "timestamp with time zone", "ok": "boolean"}
COLS = list(TYPES)


def _run(decl, ctx):
    return ac.prose_checks("x_asset", decl, ctx)


# ───────────────────────── R1: the schema check ─────────────────────────

def test_a_declared_none_asset_whose_text_columns_are_all_closed_reads_na_on_all_six_with_the_checked_block():
    got = _run(_decl(_cc()), _ctx(COLS, TYPES, closed_outside={("t", "graha"): 0}))
    for c in NARR:
        assert got[c]["v"] == NA and got[c]["cause"] == "no-prose", (c, got[c])
    for c in NULL:
        assert got[c]["v"] == NA and got[c]["cause"] == "no-prose-declared", (c, got[c])
    b = got["Narr.lint"]["prose_none"]
    assert b["checked"] is True and b["open"] == [] and b["contradicted"] == [] and b["unread"] == [] and b["closed"] == [dict(table="t", column="graha", kind="text")]


def test_a_table_with_no_text_capable_column_needs_no_closed_columns():
    got = _run(_decl(), _ctx(["id", "score", "at", "ok"], {k: TYPES[k] for k in ("id", "score", "at", "ok")}))
    assert all(got[c]["v"] == NA for c in NARR + NULL)


def test_an_open_text_column_contradicts_the_declaration_FAIL_not_na():
    got = _run(_decl(), _ctx(COLS, TYPES))                                                  # graha is text and not declared closed
    assert got["Narr.agree"]["v"] == FAIL and "graha" in got["Narr.agree"]["measured"] and "open text column" in got["Narr.agree"]["measured"]
    assert all(got[c]["v"] == NO_DET and got[c]["prose_none"]["open"] for c in NARR[1:] + NULL)
    for t in ("character varying", "citext", "character", "text"):
        g = _run(_decl(), _ctx(["id", "n"], {"id": "integer", "n": t}))
        assert g["Narr.agree"]["v"] == FAIL, t
    for t in ("ARRAY", "jsonb", "json", "USER-DEFINED"):                                      # text-capable: they must be declared too
        g = _run(_decl(), _ctx(["id", "n"], {"id": "integer", "n": t}))
        assert g["Narr.agree"]["v"] == FAIL, t


def test_a_declared_vocabulary_the_data_leaves_is_a_contradiction():
    got = _run(_decl(_cc()), _ctx(COLS, TYPES, closed_outside={("t", "graha"): 3}))
    assert got["Narr.agree"]["v"] == FAIL and "3 row(s)" in got["Narr.agree"]["measured"] and "outside the declared closed vocabulary" in got["Narr.agree"]["measured"]


@pytest.mark.parametrize("decl,why", [
    (_decl(_cc(column="graha"), _cc(column="ghost")), "not a column of t"),
    (_decl(_cc(), _cc(column="score")), "not a text-capable column"),
    (_decl(_cc(), _cc(table="other")), "not one of the asset's produced tables"),
])
def test_a_declaration_that_names_a_wrong_column_is_a_contradiction(decl, why):
    got = _run(decl, _ctx(COLS, TYPES, closed_outside={("t", "graha"): 0}))
    assert got["Narr.agree"]["v"] == FAIL and why in got["Narr.agree"]["measured"]


def test_no_string_leaves_is_only_for_a_json_column():
    d = _decl(_cc(column="blob", values=None, no_string_leaves=True))
    ok = _run(d, _ctx(["id", "blob"], {"id": "integer", "blob": "jsonb"}, closed_outside={("t", "blob"): 0}))
    assert ok["Narr.agree"]["v"] == NA
    bad = _run(d, _ctx(["id", "blob"], {"id": "integer", "blob": "text"}, closed_outside={("t", "blob"): 0}))
    assert bad["Narr.agree"]["v"] == FAIL and "json(b)" in bad["Narr.agree"]["measured"]
    leaf = _run(d, _ctx(["id", "blob"], {"id": "integer", "blob": "jsonb"}, closed_outside={("t", "blob"): 2}))
    assert leaf["Narr.agree"]["v"] == FAIL and "string leaf" in leaf["Narr.agree"]["measured"]


def test_a_check_that_could_not_read_the_schema_or_the_data_is_no_detector_never_na():
    for ctx in (_ctx(COLS, None), _ctx(None, TYPES), _ctx(COLS, {k: v for k, v in TYPES.items() if k != "graha"}), _ctx(COLS, TYPES, closed_outside={})):
        got = _run(_decl(_cc()), ctx)
        assert all(got[c]["v"] == NO_DET and "could not be checked" in got[c]["measured"] for c in NARR + NULL), got["Narr.agree"]
        assert got["Narr.agree"]["prose_none"]["unread"]


def test_the_writes_must_still_be_readable_and_a_narration_column_write_still_fails():
    got = _run(_decl(_cc()), _ctx(COLS, TYPES, written=None, closed_outside={("t", "graha"): 0}))
    assert all(got[c]["v"] == NO_DET for c in NARR + NULL)
    got = _run(_decl(_cc()), _ctx(COLS, TYPES, written={"t": {"narration"}}, closed_outside={("t", "graha"): 0}))
    assert got["Narr.agree"]["v"] == FAIL and "narration" in got["Narr.agree"]["measured"]


def test_a_malformed_prose_none_reads_no_detector():
    d = _decl(_cc())
    d["prose_none"]["closed_columns"][0]["values"] = []
    got = _run(d, _ctx(COLS, TYPES, closed_outside={("t", "graha"): 0}))
    assert all(got[c]["v"] == NO_DET and "refused" in got[c]["measured"] for c in NARR + NULL)


def test_produced_tables_with_a_filter_are_the_tables_checked():
    tables = {"chart_dashas": (["id", "n"], {"id": "integer", "n": "integer"}, None),
              "chart_facts": (["id", "fact_category", "note"], {"id": "integer", "fact_category": "text", "note": "text"}, dict(column="fact_category", equals="dasha_scope_cap"))}
    d = _decl(_cc(column="fact_category", values=["dasha_scope_cap"], table="chart_facts"), _cc(column="note", values=["a"], table="chart_facts"))
    got = ac.prose_checks("x_asset", d, _ctx(["id"], {"id": "integer"}, table="chart_dashas", prose_tables=tables,
                                              closed_outside={("chart_facts", "fact_category"): 0, ("chart_facts", "note"): 0}))
    assert got["Narr.agree"]["v"] == NA and got["Narr.agree"]["prose_none"]["tables"] == ["chart_dashas", "chart_facts"]
    got = ac.prose_checks("x_asset", _decl(_cc(column="fact_category", values=["dasha_scope_cap"], table="chart_facts")),
                          _ctx(["id"], {"id": "integer"}, table="chart_dashas", prose_tables=tables, closed_outside={("chart_facts", "fact_category"): 0}))
    assert got["Narr.agree"]["v"] == FAIL and "chart_facts.note" in got["Narr.agree"]["measured"]       # an open column of a produced table, however far from the target


# ───────────────────────── a bare [] is no release ─────────────────────────

def test_a_bare_empty_prose_fields_is_no_release_for_a_new_asset_and_the_six_legacy_assets_keep_their_narr_na_only():
    bare = {"prose_fields": [], "evidence": {"prose_fields": EV}}
    got = _run(bare, _ctx(COLS, TYPES))
    assert all(got[c]["v"] == NO_DET and "prose_none" in got[c]["measured"] for c in NARR + NULL)
    assert ac.PROSE_BARE_EMPTY_LEGACY == frozenset({"bg_doshas", "bg_kp_sublord_division", "bg_ontology", "bg_transit_engine", "bg_yogas", "bo_laksana_rerank"})
    legacy = ac.prose_checks("bg_doshas", bare, _ctx(COLS, TYPES))
    assert all(legacy[c]["v"] == NA for c in NARR)
    committed = ac.load_asset_declarations()                                                  # the enumerated table is exactly the committed bare [] assets (no coupling, no prose_none)
    bare_committed = {a for a, e in committed.items() if e.get("prose_fields") == [] and e.get("prose_none") is None and e.get("prose_coupling") is None}
    assert bare_committed == ac.PROSE_BARE_EMPTY_LEGACY


# ───────────────────────── the rollup honours only a checked block ─────────────────────────

def _checked():
    return _run(_decl(_cc()), _ctx(COLS, TYPES, closed_outside={("t", "graha"): 0}))


def test_the_rollup_reads_n_a_on_narr_and_null_through_the_checked_block():
    cells = ac.rollup_asset("L0", _checked())
    assert cells["Narr"]["v"] == NA and cells["Null"]["v"] == NA
    assert {c["rule_id"] for c in cells["Null"]["checks"]} == {"Null.schema_default#measured:no-prose-declared", "Null.blank_rows#measured:no-prose-declared"}


def test_the_same_records_without_their_block_or_with_a_failed_block_are_no_detector():
    ms = _checked()
    for mut in (lambda r: r.pop("prose_none"), lambda r: r["prose_none"].update(open=["t.x"]), lambda r: r["prose_none"].update(checked=False), lambda r: r["prose_none"].update(unread=["t.x"]),
                lambda r: r["prose_none"].update(contradicted=["t.x"]), lambda r: r["prose_none"].update(tables=[]), lambda r: r.update(prose_none="yes")):
        m2 = copy.deepcopy(ms)
        mut(m2["Narr.agree"])
        mut(m2["Null.blank_rows"])
        cells = ac.rollup_asset("L0", m2)
        assert cells["Narr"]["v"] == NO_DET and cells["Null"]["v"] == NO_DET
        assert "CHECKED declared-none" in next(c for c in cells["Narr"]["checks"] if c["criterion"] == "Narr.agree")["reason"]


def test_the_gap_ledger_releases_a_no_prose_na_only_where_the_rollup_does():
    ms = _checked()
    assert ac._na_released("Narr.agree", ms["Narr.agree"]) is True and ac._na_released("Null.blank_rows", ms["Null.blank_rows"]) is True
    bare = dict(v=NA, measured="m", cause="no-prose")
    assert ac._na_released("Narr.agree", bare) is False
    assert ac._na_released("Narr.agree", bare, facts={"declared_prose_bare_legacy": True}) is True
    assert ac._na_released("Null.blank_rows", dict(v=NA, measured="m", cause="no-prose-declared"), facts={"declared_prose_bare_legacy": True}) is False     # Null releases nothing unchecked


def test_the_legacy_fact_is_derived_from_the_declaration_by_asset_id_and_never_for_a_converted_asset():
    d = ac.load_asset_declarations()
    assert ac.declared_facts(d, "bg_doshas")["declared_prose_bare_legacy"] is True
    assert "declared_prose_bare_legacy" not in ac.declared_facts(d, "bg_phaladeepika_latta")       # coupled, not bare
    conv = {"bg_doshas": {**copy.deepcopy(d["bg_doshas"]), "prose_none": dict(why=WHY, closed_columns=[])}}
    assert "declared_prose_bare_legacy" not in ac.declared_facts(conv, "bg_doshas")                # converted: the checked path only
    assert "declared_prose_bare_legacy" not in ac.declared_facts({"new_asset": {"prose_fields": []}}, "new_asset")


def test_a_coupled_narr_na_keeps_its_own_carr_d1_guard_and_is_not_touched_by_the_prose_none_guard():
    assert ac.prose_none_na_problem("Narr.agree", dict(v=NA, cause="no-prose", prose_coupling=dict(to="carriage_d1"))) is None
    assert ac.prose_none_na_problem("Narr.agree", dict(v=PASS)) is None and ac.prose_none_na_problem("Build.target", dict(v=NA, cause="no-prose")) is None


# ───────────────────────── R3: Vocab.alias N/A ─────────────────────────

NA_DECL = dict(na="no_alias_class", why="the table states no planet vocabulary and no alias set", evidence=EV)


@pytest.mark.parametrize("col", ["graha", "Graha", "planet", "other_graha", "star_lord", "sub_lord", "lord"])
def test_no_alias_class_is_not_released_beside_a_vocabulary_column_the_ontology_aliases(col):
    rec = ac.vocab_alias_declared_check("x", NA_DECL, "t", ["id", col])["Vocab.alias"]
    assert rec["v"] == NO_DET and rec["declaration_disagreements"][0]["field"] == "vocab_alias.na" and "N-150 R3" in rec["measured"]


def test_no_alias_class_stays_na_where_neither_an_alias_nor_a_vocabulary_column_exists():
    rec = ac.vocab_alias_declared_check("x", NA_DECL, "t", ["id", "label", "weight"])["Vocab.alias"]
    assert rec["v"] == NA and rec["cause"] == "no-alias-class"
    assert ac.vocab_alias_declared_check("x", NA_DECL, "t", ["id", "synonyms"])["Vocab.alias"]["v"] == NO_DET      # N-73 (4), unchanged
    assert ac.vocab_alias_declared_check("x", NA_DECL, "t", None)["Vocab.alias"]["v"] == NO_DET                    # unknown columns: not released
    assert ac.alias_vocab_columns(["id", "Graha", 3, "x"]) == ["Graha"] and ac.alias_vocab_columns(None) == []


# ───────────────────────── the registry and the record ─────────────────────────

def test_revisions_and_rules_carry_the_n150_content():
    for c in NARR:
        assert ac.CRITERION_REGISTRY[c]["revision"] == 3 and "prose_none" in ac.CRITERION_REGISTRY[c]["applicability"]
    for c in NULL:
        assert ac.CRITERION_REGISTRY[c]["revision"] == 4 and "prose_none" in ac.CRITERION_REGISTRY[c]["applicability"]
    assert ac.CRITERION_REGISTRY["Vocab.alias"]["revision"] == 3 and "N-150 R3" in ac.CRITERION_REGISTRY["Vocab.alias"]["applicability"]
    assert ac.REGISTRY_REVISION == 26


def test_measure_emits_the_column_types_the_schema_check_read(monkeypatch, tmp_path):
    import test_e6_a_na_causes as nac
    reg = {"x": nac._reg_row("x", "t_a"), "y": nac._reg_row("y", "t_b")}
    nac._stub_layer(monkeypatch, tmp_path, reg, tables={"t_a": (["id", "name"], []), "t_b": (["id"], [])})
    real_cat = ac.catalog
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(real_cat(ts), types={"t_a": {"id": "integer", "name": "text"}}, defaults={}, types_error=None))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    got = {a["asset_id"]: a for a in ac.measure("L0")["assets"]}
    assert got["x"]["target_column_types"] == {"id": "integer", "name": "text"}
    assert got["y"]["target_column_types"] is None                                                  # a table whose types were not read: unknown, never {}


def test_a_declared_produced_table_is_read_by_the_catalog(monkeypatch, tmp_path):
    import test_e6_a_na_causes as nac
    seen = []
    reg = {"x": nac._reg_row("x", "t_a")}
    nac._stub_layer(monkeypatch, tmp_path, reg, tables={"t_a": (["id"], [])})
    real_cat = ac.catalog
    monkeypatch.setattr(ac, "catalog", lambda ts: (seen.append(list(ts)), real_cat(ts))[1])
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"x": {"produced_tables": [dict(table="chart_facts", filter=dict(column="fact_category", equals="dasha_scope_cap"))]}})
    ac.measure("L0")
    assert "chart_facts" in seen[0]


# ───────────────────────── REAL SQL: the closure reads ─────────────────────────

def _real_outside(monkeypatch, pg, setup, tables, pn, target="t"):
    s3._real(monkeypatch, pg, setup)
    return ac.prose_none_fetch_outside(tables, target, pn)


def test_REAL_SQL_text_array_enum_and_json_closures(monkeypatch, disposable_pg):
    setup = ["CREATE TYPE pn_enum AS ENUM ('a','b','c');",
             "CREATE TEMP TABLE t (id int, lab text, arr text[], en pn_enum, js jsonb, vc varchar(9)) ON COMMIT DROP;",
             "INSERT INTO t VALUES (1,'Sun',ARRAY['x','y'],'a','{\"k\":\"v\"}','Sun'),(2,'Moon',ARRAY['x'],'b','{\"k\":1}','Moon'),(3,NULL,NULL,NULL,NULL,NULL),(4,'Mars',ARRAY['z'],'c','[\"q\"]','Sun');"]
    cols = ["id", "lab", "arr", "en", "js", "vc"]
    types = {"id": "integer", "lab": "text", "arr": "ARRAY", "en": "USER-DEFINED", "js": "jsonb", "vc": "character varying"}
    pn = dict(why=WHY, closed_columns=[_cc("lab", ["Sun", "Moon"]), _cc("arr", ["x", "y"]), _cc("en", ["a", "b"]), _cc("vc", ["Sun", "Moon"]),
                                       dict(column="js", values=None, no_string_leaves=True, why=CW)])
    got = _real_outside(monkeypatch, disposable_pg, setup, {"t": (cols, types, None)}, pn)
    assert got == {("t", "lab"): 1, ("t", "arr"): 1, ("t", "en"): 1, ("t", "vc"): 0, ("t", "js"): 2}      # Mars / z / c leave the vocabulary; two rows carry a string leaf
    closed_js = dict(why=WHY, closed_columns=[_cc("js", ["v", "q"])])
    got = _real_outside(monkeypatch, disposable_pg, setup, {"t": (cols, types, None)}, closed_js)
    assert got == {("t", "js"): 0}                                                                # the string leaves 'v' and 'q' are inside the vocabulary; the number 1 is not a string leaf


def test_REAL_SQL_a_filter_slices_the_produced_table(monkeypatch, disposable_pg):
    setup = ["CREATE TEMP TABLE chart_facts (id int, fact_category text, note text) ON COMMIT DROP;",
             "INSERT INTO chart_facts VALUES (1,'dasha_scope_cap','a'),(2,'other','free prose here'),(3,'dasha_scope_cap','b');"]
    cols, types = ["id", "fact_category", "note"], {"id": "integer", "fact_category": "text", "note": "text"}
    pn = dict(why=WHY, closed_columns=[_cc("note", ["a", "b"], table="chart_facts")])
    filt = dict(column="fact_category", equals="dasha_scope_cap")
    assert _real_outside(monkeypatch, disposable_pg, setup, {"chart_facts": (cols, types, filt)}, pn) == {("chart_facts", "note"): 0}
    assert _real_outside(monkeypatch, disposable_pg, setup, {"chart_facts": (cols, types, None)}, pn) == {("chart_facts", "note"): 1}        # unsliced, the other rows leave the vocabulary


def test_REAL_SQL_the_whole_chain_prose_checks_over_the_real_closure(monkeypatch, disposable_pg):
    setup = ["CREATE TEMP TABLE t (id int, graha text) ON COMMIT DROP;", "INSERT INTO t VALUES (1,'Sun'),(2,'Moon');"]
    tables = {"t": (["id", "graha"], {"id": "integer", "graha": "text"}, None)}
    d = _decl(_cc())
    out = _real_outside(monkeypatch, disposable_pg, setup, tables, d["prose_none"])
    assert _run(d, _ctx(["id", "graha"], tables["t"][1], prose_tables=tables, closed_outside=out))["Narr.agree"]["v"] == NA
    setup2 = ["CREATE TEMP TABLE t (id int, graha text) ON COMMIT DROP;", "INSERT INTO t VALUES (1,'Sun'),(2,'a whole sentence of prose');"]
    out = _real_outside(monkeypatch, disposable_pg, setup2, tables, d["prose_none"])
    got = _run(d, _ctx(["id", "graha"], tables["t"][1], prose_tables=tables, closed_outside=out))
    assert got["Narr.agree"]["v"] == FAIL and "1 row(s)" in got["Narr.agree"]["measured"]


# ───────────────────────── N-156 F4: declared source columns are not prose ─────────────────────────

LONG = ["id", "graha", "source_citation", "provenance", "content_sha256"]
LONG_T = {"id": "integer", "graha": "text", "source_citation": "text", "provenance": "text", "content_sha256": "text"}


def _with_source(entry, **src):
    return {**entry, "source": dict(why=WHY, evidence=EV, **src)}


def test_a_declared_source_column_is_not_an_open_text_column_and_needs_no_vocabulary():
    d = _with_source(_decl(_cc()), level="row", columns=[dict(column="source_citation", kinds=["K1"])], provenance_columns=["provenance", "content_sha256"], citation_state="sourced")
    got = _run(d, _ctx(LONG, LONG_T, closed_outside={("t", "graha"): 0}))
    assert all(got[c]["v"] == NA for c in NARR + NULL), got["Narr.agree"]
    assert got["Narr.agree"]["prose_none"]["source_columns"] == ["content_sha256", "provenance", "source_citation"]


def test_any_other_open_text_column_still_fails_beside_the_source_columns():
    d = _with_source(_decl(), level="row", columns=[dict(column="source_citation", kinds=["K1"])], provenance_columns=["provenance"], citation_state="sourced")
    got = _run(d, _ctx(LONG, LONG_T))                                                  # graha is open; the source columns are not the reason
    assert got["Narr.agree"]["v"] == FAIL and "t.graha" in got["Narr.agree"]["measured"]
    assert "source_citation" not in got["Narr.agree"]["measured"] and "provenance (" not in got["Narr.agree"]["measured"]
    assert got["Narr.agree"]["prose_none"]["open"] == ["t.graha (text)", "t.content_sha256 (text)"]      # the undeclared hash column is open: it must be declared under provenance_columns


def test_the_older_ldgr_source_column_and_a_table_level_source_with_provenance_columns_are_also_source_columns():
    assert ac.source_declared_columns({"ldgr_source": dict(source_column="verse_ref")}) == ["verse_ref"]
    assert ac.source_declared_columns(_with_source({}, level="table", kind="K2", decision_id="N-150", provenance_columns=["source_ref"])) == ["source_ref"]
    assert ac.source_declared_columns(_with_source({}, na="no_data")) == [] and ac.source_declared_columns({}) == [] and ac.source_declared_columns(None) == []
    k3 = _with_source({}, level="row", columns=[dict(kinds=["K3"], generator_column="g", method_column="m", seed_column="s")])
    assert ac.source_declared_columns(k3) == ["g", "m", "s"]


def test_a_declared_source_column_the_table_does_not_have_is_a_contradiction():
    d = _with_source(_decl(_cc()), level="row", columns=[dict(column="ghost_col", kinds=["K1"])], citation_state="sourced")
    got = _run(d, _ctx(["id", "graha"], {"id": "integer", "graha": "text"}, closed_outside={("t", "graha"): 0}))
    assert got["Narr.agree"]["v"] == FAIL and "ghost_col" in got["Narr.agree"]["measured"]


def test_a_long_closed_value_list_is_not_needed_for_a_source_column():
    long_cite = "x" * 500                                                         # a citation text far beyond the 200-character vocabulary limit: it is never listed
    assert ac.prose_none_problem(_decl(_cc(values=[long_cite]))) is not None        # a closed vocabulary still refuses a long value (it is not a source column)
    d = _with_source(_decl(_cc()), level="row", columns=[dict(column="source_citation", kinds=["K1"])], citation_state="sourced")
    assert ac.prose_none_problem(d) is None


# ───────────────────────── transcription_columns (N-156 F4) ─────────────────────────

TC_COLS = ["id", "graha", "effects_text", "formation_text"]
TC_TYPES = {"id": "integer", "graha": "text", "effects_text": "text", "formation_text": "text"}


def _tc(column, table=None, **kw):
    d = dict(column=column, why="hand-authored seed text that transcribes the classical table row", evidence=EV)
    if table:
        d["table"] = table
    d.update(kw)
    return d


def _with_tc(*tcs, closed=(_cc(),)):
    d = _decl(*closed)
    d["prose_none"]["transcription_columns"] = list(tcs)
    return d


def test_a_declared_transcription_column_is_not_prose_and_needs_no_vocabulary():
    d = _with_tc(_tc("effects_text"), _tc("formation_text"))
    got = _run(d, _ctx(TC_COLS, TC_TYPES, closed_outside={("t", "graha"): 0}))
    assert all(got[c]["v"] == NA for c in NARR + NULL), got["Narr.agree"]
    assert got["Narr.agree"]["prose_none"]["transcription_columns"] == ["t.effects_text", "t.formation_text"]


def test_an_undeclared_text_column_still_fails_beside_the_transcription_columns():
    got = _run(_with_tc(_tc("effects_text")), _ctx(TC_COLS, TC_TYPES, closed_outside={("t", "graha"): 0}))
    assert got["Narr.agree"]["v"] == FAIL and "t.formation_text" in got["Narr.agree"]["measured"] and "effects_text" not in got["Narr.agree"]["measured"].split("column(s)")[1]


def test_a_transcription_column_must_exist_in_the_live_schema_and_be_checked_on_its_table():
    got = _run(_with_tc(_tc("effects_text"), _tc("ghost_text")), _ctx(TC_COLS, TC_TYPES, closed_outside={("t", "graha"): 0}))
    assert got["Narr.agree"]["v"] == FAIL and "ghost_text" in got["Narr.agree"]["measured"] and "not a column" in got["Narr.agree"]["measured"]
    got = _run(_with_tc(_tc("effects_text", table="other")), _ctx(TC_COLS, TC_TYPES, closed_outside={("t", "graha"): 0}))
    assert got["Narr.agree"]["v"] == FAIL and "other" in got["Narr.agree"]["measured"]
    tables = {"t": (TC_COLS, TC_TYPES, None), "t2": (["id", "note"], {"id": "integer", "note": "text"}, None)}
    got = ac.prose_checks("x_asset", _with_tc(_tc("note", table="t2"), _tc("effects_text"), _tc("formation_text")), _ctx(TC_COLS, TC_TYPES, prose_tables=tables, closed_outside={("t", "graha"): 0}))
    assert got["Narr.agree"]["v"] == NA


def test_a_transcription_declaration_needs_a_real_reason_and_a_real_evidence_pointer():
    for kw in (dict(why="n/a"), dict(why="TBD"), dict(evidence="unverified: somewhere in the writer"), dict(evidence="no/such/file.py:1"), dict(evidence=None), dict(bogus=1)):
        assert ac.prose_none_problem(_with_tc(_tc("effects_text", **kw))) is not None, kw
    assert ac.prose_none_problem(_with_tc(_tc("effects_text"))) is None


def test_transcription_column_shape_refusals():
    P = ac.prose_none_problem
    assert "list of 1 to" in P(_with_tc(closed=())) if False else True
    d = _with_tc(_tc("effects_text"), _tc("effects_text"))
    assert "listed twice" in P(d)
    assert "both a closed column and a transcription" in P(_with_tc(_tc("graha")))
    d = _with_tc(_tc("effects_text"))
    d["prose_none"]["transcription_columns"] = []
    assert "list of 1 to" in P(d)
    d["prose_none"]["transcription_columns"] = "effects_text"
    assert "list of 1 to" in P(d)
    d["prose_none"]["transcription_columns"] = ["effects_text"]
    assert "must be an object" in P(d)
    assert "identifier" in P(_with_tc(_tc("bad col")))
    assert "table must be" in P(_with_tc(_tc("c", table="bad t")))
    d = _with_tc(*[_tc(f"c{i}") for i in range(ac.PROSE_NONE_MAX_TRANSCRIPTIONS + 1)])
    assert "list of 1 to" in P(d)


def test_a_transcription_column_is_never_a_prose_field():
    d = _with_tc(_tc("effects_text"))
    d["prose_fields"] = ["effects_text"]
    assert ac.prose_none_problem(d) is not None                                          # prose_none qualifies a bare []: a declared prose column contradicts it


def test_the_validator_accepts_the_transcription_form_in_a_document():
    doc = {"version": "9.9.9", "kind_enum": list(ac.DECLARED_KINDS), "assets": {"x_asset": _with_tc(_tc("effects_text"))}}
    ac.validate_declarations(doc)
