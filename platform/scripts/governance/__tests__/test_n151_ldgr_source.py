"""test_n151_ldgr_source.py: the declared `source` reading of Ldgr.source_presence (N-151, REGISTRY_REVISION 26).

Pure tests (a fake `scalar`) cover every branch of `source_declared_check`; REAL-SQL tests run the row-level predicates on the throw-away disposable PostgreSQL (K2 id strings, mixed K1/K2,
K3 columns, LEDGER fact ids against chart_facts). No production database, no register: K2 is a decision-id STRING (N-154)."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, NA = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA
LDGR = "Ldgr.source_presence"
EV = "platform/scripts/governance/asset_census.py:1"
WHY = "the reviewed reason this declaration is true"


def _src(**kw):
    d = dict(why=WHY, evidence=EV)
    d.update(kw)
    return d


def _chk(src, table="t", cols=("id", "name"), **kw):
    return ac.source_declared_check("x", src, table, list(cols) if cols is not None else None, **kw)[LDGR]


# ───────────────────────── placeholders: the python mirror of the SQL predicate ─────────────────────────

@pytest.mark.parametrize("v", [None, 5, "", "  ", "-", "n/a", "N / A", "none", "UNSOURCED", "UNSOURCED - no house-transit doctrine", "classical_tradition",
                               "Classical tradition (Jyotish)", "TBD", "not traced", "​none​", "ＮＯＮＥ", "....", "unknown"])
def test_placeholders_state_no_source(v):
    assert ac.ldgr_placeholder_text(v) is True


@pytest.mark.parametrize("v", ["Brihat Parashara Hora Shastra 3.12", "BPHS ch. 3", "सारावली 4.1", "classical tradition Saravali 12", "Unsourcedly cited in Phaladeepika 4"])
def test_real_citations_are_not_placeholders(v):
    assert ac.ldgr_placeholder_text(v) is False


# ───────────────────────── table level ─────────────────────────

K1 = dict(level="table", kind="K1", citation="Brihat Parashara Hora Shastra", locus="chapter 3, verses 12-14", citation_state="sourced")
K2 = dict(level="table", kind="K2", decision_id="N-150")
K3 = dict(level="table", kind="K3", generator="bg_cohort_builder", method="seeded sampling", seed="20260101")


@pytest.mark.parametrize("decl", [K1, K2, K3])
def test_a_resolving_table_level_source_on_a_table_with_rows_is_pass(decl):
    rec = _chk(_src(**decl), rows=12)
    assert rec["v"] == PASS and rec["declared"] is True and rec["source"]["level"] == "table" and rec["source"]["resolved"] is True
    assert rec["citation_state"] == ("sourced")


def test_a_table_level_source_never_passes_without_rows_a_table_or_a_state():
    assert _chk(_src(**K2), rows=0)["v"] == NO_DET and _chk(_src(**K2), rows=None)["v"] == NO_DET          # a source for no data is vacuous
    assert _chk(_src(**K2), table=None, cols=None, rows=5)["v"] == NO_DET and _chk(_src(**K2), cols=None, rows=5)["v"] == NO_DET
    for st in ("unsourced", "refuted"):
        rec = _chk(_src(**{**K1, "citation_state": st}), rows=3)
        assert rec["v"] == NO_DET and rec["citation_state"] == st and "never a PASS" in rec["measured"]
    assert _chk(_src(**K2), rows=True)["v"] == NO_DET                                                         # a bool is not a row count


@pytest.mark.parametrize("decl,frag", [
    ({**K1, "citation": "classical_tradition"}, "placeholder"),
    ({**K1, "citation": "UNSOURCED - nothing"}, "placeholder"),
    ({**K1, "locus": "BPHS"}, "number"),                       # a locus names a chapter / verse / page number
    ({**K1, "locus": "n/a"}, "placeholder"),
    ({**K2, "decision_id": "ratified"}, "decision id"),
    ({**K3, "generator": "TBD"}, "placeholder"),
    ({**K3, "method": "none"}, "placeholder"),
    ({**K3, "seed": "unknown"}, "placeholder"),
])
def test_a_placeholder_source_is_FAIL_never_a_pass(decl, frag):
    rec = _chk(_src(**decl), rows=5) if decl.get("decision_id") != "ratified" else ac.source_declared_check("x", _src(**decl), "t", ["id"], rows=5)[LDGR]
    # the shape validator refuses 'ratified' (a bare word) before the detector: the detector then reads NO_DETECTOR (malformed), never PASS
    assert rec["v"] in (FAIL, NO_DET) and rec["v"] != PASS
    if rec["v"] == FAIL:
        assert frag in rec["measured"]


def test_the_citation_state_default_is_sourced_only_for_k2_k3_and_k1_must_state_it():
    assert _chk(_src(**K2), rows=1)["citation_state"] == "sourced"
    assert ac.source_declaration_problem(_src(**{k: v for k, v in K1.items() if k != "citation_state"})) is not None


def test_a_malformed_declaration_reads_no_detector_not_an_exception():
    rec = _chk({"na": "no_data"}, rows=1)            # no why / evidence
    assert rec["v"] == NO_DET and "malformed" in rec["measured"]
    assert ac.source_declared_check("x", None, "t", ["id"]) == {} and ac.source_declared_check("x", {}, "t", ["id"]) == {} and ac.source_declared_check("x", "K2", "t", ["id"]) == {}


# ───────────────────────── N/A: only by a CHECKED declaration ─────────────────────────

def test_no_data_is_na_only_for_an_asset_that_owns_no_existing_table():
    rec = _chk(_src(na="no_data"), table=None, cols=None, owned=())
    assert rec["v"] == NA and rec["cause"] == "no-data" and rec["declared"] is True


def test_no_data_is_contradicted_by_an_existing_table_and_not_released_for_an_unseen_one():
    rec = _chk(_src(na="no_data"), table="t", cols=["id"], owned=["t"])
    assert rec["v"] == FAIL and rec["declaration_disagreements"][0]["field"] == "source.na"
    assert _chk(_src(na="no_data"), table=None, cols=None, owned=["count_t"])["v"] == FAIL                  # a count_sql table is owned data too
    assert _chk(_src(na="no_data"), table="t", cols=None, owned=())["v"] == NO_DET                           # declared table absent from production: unproven, not released


PN_OK = dict(v=NA, prose_none=dict(checked=True))


def test_no_claims_is_na_only_when_the_prose_check_passed_and_no_citation_or_ledger_column_exists():
    rec = _chk(_src(na="no_claims"), cols=["id", "name"], prose_record=PN_OK)
    assert rec["v"] == NA and rec["cause"] == "no-claims"
    for col in ("source_citation", "classical_citation", "constituent_facts_array", "source_fact_ids", "derivation_ledger"):
        rec = _chk(_src(na="no_claims"), cols=["id", col], prose_record=PN_OK)
        assert rec["v"] == FAIL and col in rec["measured"], col                                              # the asset carries a source column: it makes claims
    assert _chk(_src(na="no_claims"), cols=["id"], prose_record=dict(v=FAIL, prose_none=dict(checked=True)))["v"] == FAIL     # an open text column contradicts it
    assert _chk(_src(na="no_claims"), cols=["id"], prose_record=None)["v"] == NO_DET
    assert _chk(_src(na="no_claims"), cols=["id"], prose_record=dict(v=NA))["v"] == NO_DET                  # an N/A with no checked block is not the check
    assert _chk(_src(na="no_claims"), cols=None, prose_record=PN_OK)["v"] == NO_DET
    assert _chk(_src(na="no_claims"), table=None, cols=None, prose_record=PN_OK)["v"] == NO_DET


def test_the_rollup_honours_the_two_new_na_words_and_the_gate_cell_reads_na():
    for form, kw in (("no_data", dict(table=None, cols=None)), ("no_claims", dict(cols=["id"], prose_record=PN_OK))):
        rec = _chk(_src(na=form), **kw)
        cell = ac.rollup_asset("L0", {LDGR: rec})["Ldgr"]
        assert cell["v"] == NA and cell["checks"][0]["rule_id"] == f"{LDGR}#measured:{rec['cause']}"
    assert f"{LDGR}#measured:no-data" in ac.NA_RULE_DECISIONS and f"{LDGR}#measured:no-claims" in ac.NA_RULE_DECISIONS


def test_the_rollup_reads_a_declared_pass_with_its_state_and_not_without_it():
    rec = _chk(_src(**K2), rows=3)
    assert ac.rollup_asset("L0", {LDGR: rec})["Ldgr"]["v"] == PASS
    no_state = {k: v for k, v in rec.items() if k != "citation_state"}
    assert ac.rollup_asset("L0", {LDGR: no_state})["Ldgr"]["v"] == NO_DET


# ───────────────────────── row level: a fake `scalar` ─────────────────────────

class _Fake:
    def __init__(self, types, stats):
        self.types, self.stats, self.sql = types, stats, []

    def __call__(self, q):
        self.sql.append(q)
        return json.dumps(self.types if "pg_attribute" in q else self.stats)


def _row(*entries, **kw):
    return _src(level="row", columns=list(entries), **kw)


def test_row_level_grades_by_the_rows_that_no_entry_sources(monkeypatch):
    f = _Fake({"ratified_by": "text"}, dict(rows=10, lacking=0, sample=[]))
    monkeypatch.setattr(ac, "scalar", f)
    src = _row(dict(column="ratified_by", kinds=["K2"]))
    assert _chk(src, cols=["id", "ratified_by"])["v"] == PASS
    f.stats = dict(rows=10, lacking=3, sample=[dict(id="a")])
    rec = _chk(src, cols=["id", "ratified_by"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 3 and rec["declared"] is True and rec["citation_state"] == "sourced"
    f.stats = dict(rows=10, lacking=10, sample=[])
    assert _chk(src, cols=["id", "ratified_by"])["v"] == FAIL
    f.stats = dict(rows=0, lacking=0, sample=[])
    assert _chk(src, cols=["id", "ratified_by"])["v"] == NO_DET


def test_row_level_refusals(monkeypatch):
    monkeypatch.setattr(ac, "scalar", _Fake({"a": "integer"}, dict(rows=1, lacking=0, sample=[])))
    assert _chk(_row(dict(column="zzz", kinds=["K2"])), cols=["id", "a"])["v"] == FAIL                # the named column is not on the table
    assert _chk(_row(dict(column="a", kinds=["K2"])), cols=["id", "a"])["v"] == NO_DET                # an integer cannot carry a decision id
    assert _chk(_row(dict(column="a", kinds=["K1"]), citation_state="sourced"), cols=["id", "a"])["v"] == NO_DET
    assert _chk(_row(dict(column="a", kinds=["LEDGER"])), cols=["id", "a"])["v"] == NO_DET
    assert _chk(_row(dict(column="a", kinds=["K2"])), table=None, cols=None)["v"] == NO_DET
    for st in ("unsourced", "refuted"):
        monkeypatch.setattr(ac, "scalar", _Fake({"a": "text"}, dict(rows=4, lacking=0, sample=[])))
        rec = _chk(_row(dict(column="a", kinds=["K1"]), citation_state=st), cols=["id", "a"])
        assert rec["v"] == NO_DET and "never a PASS" in rec["measured"]


def test_a_failed_read_degrades_only_this_check(monkeypatch):
    def boom(q):
        raise ac.Unknown("connection refused")
    monkeypatch.setattr(ac, "scalar", boom)
    rec = _chk(_row(dict(column="a", kinds=["K2"])), cols=["id", "a"])
    assert rec["v"] == "ERRORED" and "connection refused" in rec["measured"]


def test_the_entries_are_alternatives_and_the_key_columns_are_the_sample(monkeypatch):
    f = _Fake({"c1": "text", "c2": "text"}, dict(rows=2, lacking=0, sample=[]))
    monkeypatch.setattr(ac, "scalar", f)
    _chk(_row(dict(column="c1", kinds=["K2"]), dict(column="c2", kinds=["K2"])), cols=["id", "name", "c1", "c2"], keys=[["id"], ["name"]])
    q = f.sql[-1]
    assert " AND " in q and q.count("btrim") >= 2 and '"name"' in q and "LIMIT 5" in q          # lacking = lacks via ALL entries; the first non-`id` key identifies rows


# ───────────────────────── measure(): the wiring ─────────────────────────

def test_measure_reads_a_declared_source_and_fails_an_undeclared_l0_asset_that_holds_data(monkeypatch, tmp_path):
    import test_e6_a_na_causes as nac
    reg = {"x": nac._reg_row("x", "t_a"), "y": nac._reg_row("y", "t_b"), "z": nac._reg_row("z", None)}
    nac._stub_layer(monkeypatch, tmp_path, reg, tables={"t_a": (["id", "name"], []), "t_b": (["id", "name"], [])})
    decl = {"x": {"source": _src(**K2)}, "z": {"source": _src(na="no_data")}}
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decl)
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert ms["x"][LDGR]["v"] in (PASS, NO_DET) and ms["x"][LDGR]["declared"] is True           # declared: read by the declared source (rows come from the stub's depth census)
    assert ms["y"][LDGR]["v"] == FAIL and "no source declared" in ms["y"][LDGR]["measured"]
    assert ms["z"][LDGR]["v"] == NA and ms["z"][LDGR]["cause"] == "no-data"


# ───────────────────────── REAL SQL ─────────────────────────

def _real_chk(monkeypatch, pg, setup, src, table, cols, **kw):
    s3._real(monkeypatch, pg, setup)
    return ac.source_declared_check("x", src, table, cols, rows=kw.pop("rows", 1), **kw)[LDGR]


def _tbl(name, ddl, rows):
    return [f"CREATE TEMP TABLE {name} (id int, {ddl}) ON COMMIT DROP;"] + [f"INSERT INTO {name} VALUES ({i + 1}, {r});" for i, r in enumerate(rows)]


def test_REAL_SQL_k2_decision_id_strings(monkeypatch, disposable_pg):
    src = _row(dict(column="ratified_by", kinds=["K2"]))
    ok = ["'N-150'", "'D-4'", "'N-72a'", "'  F-2  '"]
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("k2t", "ratified_by text", ok), src, "k2t", ["id", "ratified_by"])
    assert rec["v"] == PASS and rec["source"]["rows"] == 4
    bad = ["'N-150'", "'ratified'", "NULL", "''", "'TBD'", "'N-'"]
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("k2t", "ratified_by text", bad), src, "k2t", ["id", "ratified_by"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 5 and rec["source"]["rows"] == 6
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("k2t", "ratified_by text", bad[1:]), src, "k2t", ["id", "ratified_by"])
    assert rec["v"] == FAIL


def test_REAL_SQL_a_mixed_k1_k2_column_reads_each_value_by_its_shape(monkeypatch, disposable_pg):
    src = _row(dict(column="citation_or_ratification", kinds=["K1", "K2"]), citation_state="sourced")
    good = ["'N-150'", "'Brihat Parashara Hora Shastra 3.12'", "'BPHS ch. 4'", "'D-4'"]
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("mx", "citation_or_ratification text", good), src, "mx", ["id", "citation_or_ratification"])
    assert rec["v"] == PASS
    bad = good + ["'classical_tradition'", "'UNSOURCED - none'", "'n/a'", "NULL"]
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("mx", "citation_or_ratification text", bad), src, "mx", ["id", "citation_or_ratification"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 4, rec["measured"]


def test_REAL_SQL_k1_on_arrays_and_json(monkeypatch, disposable_pg):
    src = _row(dict(column="cites", kinds=["K1"]), citation_state="sourced")
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("ar", "cites text[]", ["ARRAY['BPHS 1.1']", "ARRAY['Saravali 2','classical_tradition']", "ARRAY[]::text[]"]), src, "ar", ["id", "cites"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 2        # an element that is a placeholder, or an empty array, is no source
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("js", "cites jsonb", ["'[{\"text_id\":\"BPHS 1.1\"}]'::jsonb", "'[{\"text_id\":\"classical_tradition\"}]'::jsonb"]), src, "js", ["id", "cites"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 1


def test_REAL_SQL_k3_columns(monkeypatch, disposable_pg):
    src = _row(dict(kinds=["K3"], generator_column="gen", method_column="meth", seed_column="seed", version_column="ver"))
    ddl = "gen text, meth text, seed text, ver text"
    rows = ["'bg_cohort', 'seeded sampling', '20260101', NULL", "'bg_cohort', 'seeded sampling', NULL, 'v2'"]
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("k3", ddl, rows), src, "k3", ["id", "gen", "meth", "seed", "ver"])
    assert rec["v"] == PASS                                                    # version OR seed
    rows += ["'bg_cohort', 'seeded sampling', NULL, NULL", "'TBD', 'm', '1', NULL", "'g', 'none', '1', '2'"]
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("k3", ddl, rows), src, "k3", ["id", "gen", "meth", "seed", "ver"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 3


def test_REAL_SQL_ledger_fact_ids_must_resolve_against_chart_facts(monkeypatch, disposable_pg):
    facts = ["CREATE TEMP TABLE chart_facts (fact_id text PRIMARY KEY) ON COMMIT DROP;", "INSERT INTO chart_facts VALUES ('F1'), ('F2'), ('F3');"]
    src = _row(dict(column="facts", kinds=["LEDGER"]))
    rows = ["ARRAY['F1','F2']", "ARRAY['F3']"]
    rec = _real_chk(monkeypatch, disposable_pg, facts + _tbl("la", "facts text[]", rows), src, "la", ["id", "facts"])
    assert rec["v"] == PASS
    rows += ["ARRAY['F1','F999']", "ARRAY[]::text[]", "NULL"]                  # an unresolved id, an empty ledger and a NULL are no derivation source
    rec = _real_chk(monkeypatch, disposable_pg, facts + _tbl("la", "facts text[]", rows), src, "la", ["id", "facts"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 3
    jrows = ["'[\"F1\",\"F2\"]'::jsonb", "'[{\"fact_id\":\"F3\"}]'::jsonb", "'[\"F1\",\"Nope\"]'::jsonb", "'[]'::jsonb", "'{\"a\":1}'::jsonb", "'[{\"x\":\"F1\"}]'::jsonb"]
    rec = _real_chk(monkeypatch, disposable_pg, facts + _tbl("lj", "facts jsonb", jrows), src, "lj", ["id", "facts"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 4, rec["measured"]


# ───────────────────────── LEDGER path / resolves_to, except_when, K3 version_digest ─────────────────────────

FACTS = ["CREATE TEMP TABLE chart_facts (fact_id text PRIMARY KEY) ON COMMIT DROP;", "INSERT INTO chart_facts VALUES ('F1'), ('F2'), ('F3');"]
SIGS = ["CREATE TEMP TABLE bodha_msr_signals (signal_id uuid PRIMARY KEY, constituent_facts_array text[] NOT NULL) ON COMMIT DROP;",
        "INSERT INTO bodha_msr_signals VALUES ('00000000-0000-0000-0000-000000000001', ARRAY['F1','F2']), ('00000000-0000-0000-0000-000000000002', ARRAY['F3']),"
        " ('00000000-0000-0000-0000-000000000003', ARRAY['F1','F404']), ('00000000-0000-0000-0000-000000000004', ARRAY[]::text[]);"]
S1, S2, S3, S4 = (f"00000000-0000-0000-0000-00000000000{i}" for i in (1, 2, 3, 4))


def test_REAL_SQL_ledger_path_into_an_object_column_resolves_to_facts(monkeypatch, disposable_pg):
    src = _row(dict(column="refs", kinds=["LEDGER"], path="$.factor_ledger[*]"))
    good = ["'{\"factor_ledger\":[\"F1\",\"F2\"]}'::jsonb", "'{\"factor_ledger\":[{\"fact_id\":\"F3\"}]}'::jsonb"]
    assert _real_chk(monkeypatch, disposable_pg, FACTS + _tbl("po", "refs jsonb", good), src, "po", ["id", "refs"])["v"] == PASS
    bad = good + ["'{\"factor_ledger\":[\"F1\",\"F404\"]}'::jsonb", "'{\"factor_ledger\":[]}'::jsonb", "'{\"other\":[\"F1\"]}'::jsonb", "NULL", "'{\"factor_ledger\":\"F1\"}'::jsonb"]
    rec = _real_chk(monkeypatch, disposable_pg, FACTS + _tbl("po", "refs jsonb", bad), src, "po", ["id", "refs"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 4, rec["measured"]       # unresolved id, empty path, absent path, NULL lack; a scalar at the path is one id and resolves


def test_REAL_SQL_ledger_path_without_the_star_reads_the_array_at_the_key(monkeypatch, disposable_pg):
    src = _row(dict(column="refs", kinds=["LEDGER"], path="$.signal_ids", resolves_to="bodha_msr_signals.signal_id"))
    rows = [f"'{{\"signal_ids\":[\"{S1}\",\"{S2}\"]}}'::jsonb"]
    assert _real_chk(monkeypatch, disposable_pg, FACTS + SIGS + _tbl("ps", "refs jsonb", rows), src, "ps", ["id", "refs"])["v"] == PASS


def test_REAL_SQL_a_signal_id_must_chain_down_to_chart_facts(monkeypatch, disposable_pg):
    src = _row(dict(column="refs", kinds=["LEDGER"], path="$.signal_ids", resolves_to="bodha_msr_signals.signal_id"))
    rows = [f"'{{\"signal_ids\":[\"{S1}\"]}}'::jsonb",                              # resolves: its constituent facts F1, F2 exist
            f"'{{\"signal_ids\":[\"{S3}\"]}}'::jsonb",                              # the signal exists but F404 does not: the chain breaks
            f"'{{\"signal_ids\":[\"{S4}\"]}}'::jsonb",                              # the signal exists with an empty constituent array: nothing derived
            "'{\"signal_ids\":[\"00000000-0000-0000-0000-0000000000ff\"]}'::jsonb",  # no such signal
            "'{\"signal_ids\":[\"F1\"]}'::jsonb"]                                   # a fact id is not a signal id
    rec = _real_chk(monkeypatch, disposable_pg, FACTS + SIGS + _tbl("pc", "refs jsonb", rows), src, "pc", ["id", "refs"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 4 and rec["source"]["rows"] == 5, rec["measured"]
    rows2 = [f"'[\"{S1}\",\"{S2}\"]'::jsonb", f"'[{{\"signal_id\":\"{S1}\"}}]'::jsonb"]            # no path: a json array of ids or objects carrying signal_id
    src2 = _row(dict(column="refs", kinds=["LEDGER"], resolves_to="bodha_msr_signals.signal_id"))
    assert _real_chk(monkeypatch, disposable_pg, FACTS + SIGS + _tbl("pc", "refs jsonb", rows2), src2, "pc", ["id", "refs"])["v"] == PASS
    rows3 = [f"ARRAY['{S1}','{S2}']"]                                                              # a text[] of signal ids
    assert _real_chk(monkeypatch, disposable_pg, FACTS + SIGS + _tbl("pc", "refs text[]", rows3), src2, "pc", ["id", "refs"])["v"] == PASS


def test_a_path_on_a_non_json_column_is_no_detector(monkeypatch):
    monkeypatch.setattr(ac, "scalar", _Fake({"refs": "text[]"}, dict(rows=1, lacking=0, sample=[])))
    rec = _chk(_row(dict(column="refs", kinds=["LEDGER"], path="$.a")), cols=["id", "refs"])
    assert rec["v"] == NO_DET and "json" in rec["measured"]


def test_REAL_SQL_except_when_excepts_the_rows_of_one_tier_by_declaration(monkeypatch, disposable_pg):
    src = _row(dict(column="derivation_chain", kinds=["K1"], except_when=dict(column="grounding_tier", equals="pratyaksa")), citation_state="sourced")
    ddl = "grounding_tier text, derivation_chain text"
    rows = ["'pratyaksa', NULL", "'anumana', 'BPHS 3.12'", "'anumana', 'Saravali 4'", "'pratyaksa', 'n/a'"]
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("ex", ddl, rows), src, "ex", ["id", "grounding_tier", "derivation_chain"])
    assert rec["v"] == PASS and rec["source"]["excepted"] == 2 and rec["source"]["rows"] == 2 and "excepted by declaration" in rec["measured"]      # the other tiers are judged
    rows += ["'anumana', NULL", "'agama', 'classical_tradition'"]
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("ex", ddl, rows), src, "ex", ["id", "grounding_tier", "derivation_chain"])
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 2 and rec["source"]["rows"] == 4 and rec["source"]["excepted"] == 2
    only = ["'pratyaksa', NULL", "'pratyaksa', 'x 1'"]
    rec = _real_chk(monkeypatch, disposable_pg, _tbl("ex", ddl, only), src, "ex", ["id", "grounding_tier", "derivation_chain"])
    assert rec["v"] == NO_DET and "no row was judged" in rec["measured"]                               # nothing judged is never a PASS
    absent = _row(dict(column="derivation_chain", kinds=["K1"], except_when=dict(column="ghost", equals="x")), citation_state="sourced")
    assert _real_chk(monkeypatch, disposable_pg, _tbl("ex", ddl, rows), absent, "ex", ["id", "grounding_tier", "derivation_chain"])["v"] == FAIL


def test_the_excepted_rows_never_count_as_sourced_when_another_entry_judges_them(monkeypatch):
    f = _Fake({"a": "text", "b": "text"}, dict(rows=4, lacking=1, sample=[], excepted=1))
    monkeypatch.setattr(ac, "scalar", f)
    rec = _chk(_row(dict(column="a", kinds=["K2"], except_when=dict(column="tier", equals="p")), dict(column="b", kinds=["K2"])), cols=["id", "tier", "a", "b"])
    assert rec["v"] == PARTIAL and rec["source"]["rows"] == 3 and rec["source"]["excepted"] == 1
    assert "FILTER (WHERE" in f.sql[-1] and "'excepted'" in f.sql[-1]


# a real, committed file whose digest the declaration records (the K3 version for a writer with no version constant)
DIGEST_FILE = "platform/scripts/governance/carriage_d1.py"


def _digest():
    import hashlib
    return hashlib.sha256((ac.ROOT / DIGEST_FILE).read_bytes()).hexdigest()


def test_a_k3_code_digest_stands_as_the_version_only_while_it_matches_the_committed_file():
    k3 = dict(level="table", kind="K3", generator="ga_transit_anchors", method="direct transcription", version_digest={"file": DIGEST_FILE, "sha256": _digest()})
    assert _chk(_src(**k3), rows=5)["v"] == PASS
    stale = dict(k3, version_digest={"file": DIGEST_FILE, "sha256": "0" * 64})
    rec = _chk(_src(**stale), rows=5)
    assert rec["v"] == FAIL and "does not match" in rec["measured"] and "generator changed" in rec["measured"]
    gone = dict(k3, version_digest={"file": "platform/scripts/governance/no_such_writer.py", "sha256": _digest()})
    assert _chk(_src(**gone), rows=5)["v"] == FAIL and "cannot be read" in _chk(_src(**gone), rows=5)["measured"]
    assert _chk(_src(**{**k3, "version_digest": {"file": "00_ARCHITECTURE/../../outside.py", "sha256": _digest()}}), rows=5)["v"] in (FAIL, NO_DET)
