"""test_e6_c_null_narr.py — E6 packet (c): the Null and Narr criteria, the prose_fields detector and the
update-only sub-reading of Idem.pattern (N-22 ruling principle 8; SS 2026-10-01).

Every test drives the real census functions; the database is never touched (psql is stubbed where a
query is built). Design: /Users/Dev/suvarna-evidence/E6.1/packet_c_design.md.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_e6_c_null_narr.py -q
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_w2_1_earned_verdicts as w1  # noqa: E402
import test_w2_3_deeper_detectors as w3  # noqa: E402

NARR = ("Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Narr.lint")
NULL = ("Null.schema_default", "Null.blank_rows")
GOOD = {"checkable": 5, "blank": 0}


# ───────────────────────── registry ─────────────────────────

def test_the_six_criteria_are_registered_measured_by_the_census_on_every_layer():
    for crit in NARR + NULL:
        e = ac.CRITERION_REGISTRY[crit]
        assert e["gate"] == crit.split(".")[0] and e["check"] == crit.split(".")[1]
        assert e["detector"] == "asset_census.py:measure()", crit
        assert e["layers"] == ac.ALL_LAYERS and e["columns_any"] is None and e["asset_kinds"] is None, crit
        assert e["revision"] == 1, crit
    assert {c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Narr"} == set(NARR)
    assert {c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Null"} == set(NULL)


def test_no_na_rule_is_declared_and_the_no_prose_causes_are_registered():
    assert ac.NA_RULE_DECISIONS == {}
    for crit in NARR:
        assert "no-prose" in ac.NA_CAUSES[crit], crit
    for crit in NULL:
        assert "no-prose-declared" in ac.NA_CAUSES[crit], crit


def test_the_registry_revision_is_5():
    assert ac.REGISTRY_REVISION == 5


# ───────────────────────── Narr.agree ─────────────────────────

def test_agree_passes_when_every_declared_entry_is_a_column_and_paths_sit_on_json_columns():
    r = ac.grade_narr_agree(["citation_human", "narrative.$.headline"], "t",
                            ["id", "citation_human", "narrative"], {"citation_human": "text", "narrative": "jsonb"})
    assert r["v"] == ac.PASS, r


def test_agree_fails_naming_a_declared_column_the_table_does_not_have():
    r = ac.grade_narr_agree(["citation_human", "headline"], "t", ["id", "citation_human"], {})
    assert r["v"] == ac.FAIL and "headline" in r["measured"] and "citation_human" not in r["measured"].split("not")[0], r


def test_agree_fails_for_a_json_path_on_a_non_json_column():
    r = ac.grade_narr_agree(["notes.$.a"], "t", ["notes"], {"notes": "text"})
    assert r["v"] == ac.FAIL and "notes" in r["measured"], r


def test_agree_is_partial_when_a_json_path_column_type_is_unread():
    r = ac.grade_narr_agree(["narrative.$.a"], "t", ["narrative"], None)
    assert r["v"] == ac.PARTIAL and "type" in r["measured"], r


def test_agree_is_no_detector_when_columns_or_table_are_unknown_never_zero_columns():
    assert ac.grade_narr_agree(["a"], "t", None, None)["v"] == ac.NO_DET
    assert ac.grade_narr_agree(["a"], None, ["a"], None)["v"] == ac.NO_DET
    assert ac.grade_narr_agree(["a"], "t", [], None)["v"] == ac.NO_DET


def test_agree_column_match_is_exact_not_case_folded_or_prefix():
    assert ac.grade_narr_agree(["Citation_Human"], "t", ["citation_human"], {})["v"] == ac.FAIL
    assert ac.grade_narr_agree(["citation"], "t", ["citation_human"], {})["v"] == ac.FAIL


# ───────────────────────── Null.schema_default ─────────────────────────

def test_schema_default_fails_on_a_non_null_default_on_a_declared_column():
    r = ac.grade_null_schema_default(["statement", "n.$.k"], ["statement", "n"], {"statement": "'none'::text"})
    assert r["v"] == ac.FAIL and "statement" in r["measured"] and "'none'" in r["measured"], r


def test_schema_default_is_partial_never_pass_when_no_default_is_found():
    r = ac.grade_null_schema_default(["statement"], ["statement"], {})
    assert r["v"] == ac.PARTIAL and "not measured" in r["measured"], r


def test_schema_default_is_no_detector_when_defaults_or_columns_are_unread():
    assert ac.grade_null_schema_default(["a"], ["a"], None)["v"] == ac.NO_DET
    assert ac.grade_null_schema_default(["a"], None, {})["v"] == ac.NO_DET


def test_a_default_on_a_non_declared_column_is_not_read():
    assert ac.grade_null_schema_default(["a"], ["a", "created_at"], {"created_at": "now()"})["v"] == ac.PARTIAL


def test_a_json_path_entry_checks_the_default_of_its_column():
    assert ac.grade_null_schema_default(["n.$.k"], ["n"], {"n": "'{\"k\": 1}'::jsonb"})["v"] == ac.FAIL


# ───────────────────────── row counts: scope + SQL ─────────────────────────

@pytest.mark.parametrize("sql,expect", [
    ("SELECT count(*) FROM t WHERE chart_id = $1", " WHERE chart_id = $1"),
    ("select COUNT(*) from t;", ""),
    ("SELECT count(*) AS n FROM t WHERE chart_id = $1 AND kind = 'x'", " WHERE chart_id = $1 AND kind = 'x'"),
    ("SELECT count(1) FROM t", ""),
])
def test_scope_tail_is_extracted_from_a_simple_count_sql(sql, expect):
    assert ac._count_scope_tail(sql, "t") == expect


@pytest.mark.parametrize("sql", [
    "SELECT count(*) FROM u WHERE chart_id = $1",
    "SELECT count(*) FROM t JOIN u ON u.id = t.id",
    "SELECT count(*) FROM t WHERE id IN (SELECT id FROM u)",
    "SELECT count(*) FROM t GROUP BY a",
    "SELECT 0 AS count",
    "",
    "SELECT count(*) FROM t UNION ALL SELECT count(*) FROM u",
])
def test_scope_tail_is_none_when_the_count_sql_is_not_a_plain_count_of_the_table(sql):
    assert ac._count_scope_tail(sql, "t") is None


def test_row_count_sql_for_a_plain_column_a_path_and_an_array_path():
    sql = ac.prose_row_counts_sql("t", ["statement", "narrative.$.headline", "d.$.items[*].reason"], " WHERE chart_id = 'x'")
    assert sql.startswith("SELECT ") and sql.endswith(" FROM t WHERE chart_id = 'x'"), sql
    assert '"statement"::text' in sql
    assert "(\"narrative\"::jsonb #>> '{headline}')" in sql
    assert "jsonb_path_query(\"d\"::jsonb, '$.\"items\"[*].\"reason\"')" in sql
    assert sql.count("count(*) FILTER") == 6          # checkable + blank per entry
    for p in ac.PROSE_PLACEHOLDERS:
        assert "'" + p + "'" in sql, p


def test_placeholder_vocabulary_is_closed_and_lowercase():
    assert {"", "n/a", "na", "none", "null", "unknown", "tbd", "-", "--", "undefined", "nan"} == set(ac.PROSE_PLACEHOLDERS)


def test_row_count_sql_rejects_an_unsafe_identifier():
    with pytest.raises(ValueError):
        ac.prose_row_counts_sql("t", ['a"; DROP TABLE x; --'], "")
    with pytest.raises(ValueError):
        ac.prose_row_counts_sql("t", [], "")


def test_prose_row_counts_reads_the_query_result_per_entry(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: seen.append(sql) or [["7", "2", "0", "0"]])
    got = ac.prose_row_counts("t", ["a", "b"], "")
    assert got == {"a": {"checkable": 7, "blank": 2}, "b": {"checkable": 0, "blank": 0}} and len(seen) == 1, got


def test_prose_row_counts_refuses_a_malformed_answer(monkeypatch):
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: [["7"]])
    with pytest.raises(ac.Unknown):
        ac.prose_row_counts("t", ["a", "b"], "")


# ───────────────────────── Narr.checkable / Null.blank_rows ─────────────────────────

def test_checkable_passes_only_with_a_checkable_row_on_every_entry_and_reports_the_counts():
    r = ac.grade_narr_checkable(["a", "b"], {"a": GOOD, "b": {"checkable": 1, "blank": 0}})
    assert r["v"] == ac.PASS and r["checkable"] == {"a": 5, "b": 1} and "a=5" in r["measured"], r


def test_checkable_is_partial_when_some_entry_has_no_checkable_row():
    r = ac.grade_narr_checkable(["a", "b"], {"a": GOOD, "b": {"checkable": 0, "blank": 0}})
    assert r["v"] == ac.PARTIAL and "b" in r["measured"], r


def test_zero_checkable_rows_is_inconclusive_never_pass():
    r = ac.grade_narr_checkable(["a", "b"], {"a": {"checkable": 0, "blank": 0}, "b": {"checkable": 0, "blank": 3}})
    assert r["v"] == ac.NO_DET and r["inconclusive"] is True and r["measured"].startswith("INCONCLUSIVE:"), r
    assert r["checkable"] == {"a": 0, "b": 0}


def test_unmeasured_row_counts_are_inconclusive_with_no_counts():
    r = ac.grade_narr_checkable(["a"], None)
    assert r["v"] == ac.NO_DET and r["inconclusive"] is True and "checkable" not in r, r


def test_blank_rows_fail_on_any_blank_or_placeholder_row():
    r = ac.grade_null_blank_rows(["a", "b"], {"a": GOOD, "b": {"checkable": 4, "blank": 2}})
    assert r["v"] == ac.FAIL and "b=2" in r["measured"] and "a=" not in r["measured"].split("blank")[0], r


def test_blank_rows_are_partial_never_pass_when_none_found():
    r = ac.grade_null_blank_rows(["a"], {"a": GOOD})
    assert r["v"] == ac.PARTIAL and "never PASS" in r["measured"], r


def test_blank_rows_are_inconclusive_without_checkable_rows_or_row_data():
    for counts in (None, {"a": {"checkable": 0, "blank": 0}}):
        r = ac.grade_null_blank_rows(["a"], counts)
        assert r["v"] == ac.NO_DET and r["inconclusive"] is True and r["measured"].startswith("INCONCLUSIVE:"), r


def test_a_null_grader_can_never_return_pass():
    for counts in (None, {"a": GOOD}, {"a": {"checkable": 0, "blank": 0}}, {"a": {"checkable": 9, "blank": 9}}):
        assert ac.grade_null_blank_rows(["a"], counts)["v"] != ac.PASS
    for defaults in (None, {}, {"a": "x"}):
        assert ac.grade_null_schema_default(["a"], ["a"], defaults)["v"] != ac.PASS


# ───────────────────────── Narr.fidelity_test ─────────────────────────

SC = ac.SIDECAR
CITE = "platform/python-sidecar/pipeline/orchestrator/writers/ph_x.py:10"
T_FULL = '''
from pipeline.orchestrator.writers.ph_x import build_narration

def test_it():
    out = build_narration({"a": 1})
    assert out["statement"].startswith("The")
'''
T_NO_FIELD = '''
from pipeline.orchestrator.writers.ph_x import build_narration

def test_it():
    assert build_narration({"a": 1}) is not None
'''
T_NO_CALL = '''
from pipeline.orchestrator.writers.ph_x import build_narration

def test_it():
    x = build_narration
    assert "statement"
'''
T_NO_ASSERT = '''
from pipeline.orchestrator.writers.ph_x import build_narration

def test_it():
    build_narration({"statement": 1})
'''
T_OTHER = '''
from pipeline.orchestrator.writers.other import build_narration

def test_it():
    assert build_narration({"statement": 1})
'''


def _tests(**srcs):
    return [(SC / "pipeline" / "orchestrator" / "writers" / "tests" / f"{n}.py", s) for n, s in srcs.items()]


def test_fidelity_never_reaches_pass_even_with_a_test_that_names_the_field_calls_the_builder_and_asserts():
    r = ac.narr_fidelity_scan(["statement"], CITE, _tests(test_a=T_FULL))
    assert r["v"] == ac.PARTIAL, r
    assert "structural" in r["measured"] and "not read" in r["measured"] and "test_a.py" in r["measured"], r
    assert r["covered"] == ["statement"]


def test_fidelity_is_partial_when_a_test_exercises_the_module_but_references_no_declared_field():
    r = ac.narr_fidelity_scan(["statement"], CITE, _tests(test_a=T_NO_FIELD))
    assert r["v"] == ac.PARTIAL and r["covered"] == [], r


def test_fidelity_names_the_uncovered_entries_when_only_some_are_covered():
    r = ac.narr_fidelity_scan(["statement", "citation_human"], CITE, _tests(test_a=T_FULL))
    assert r["v"] == ac.PARTIAL and r["covered"] == ["statement"] and "citation_human" in r["measured"], r


def test_the_leaf_of_a_json_path_is_the_last_key():
    r = ac.narr_fidelity_scan(["narrative.$.statement"], CITE, _tests(test_a=T_FULL))
    assert r["covered"] == ["narrative.$.statement"], r


@pytest.mark.parametrize("src", [T_NO_CALL, T_NO_ASSERT, T_OTHER, "def test_x():\n    assert 1\n", "def broken(:\n"])
def test_fidelity_fails_when_no_test_imports_calls_and_asserts_against_the_builder(src):
    r = ac.narr_fidelity_scan(["statement"], CITE, _tests(test_a=src))
    assert r["v"] == ac.FAIL and "N.7" in r["measured"], r


def test_fidelity_fails_with_no_tests_at_all():
    assert ac.narr_fidelity_scan(["statement"], CITE, [])["v"] == ac.FAIL


def test_fidelity_resolves_package_init_relative_imports_and_module_aliases():
    cite = "platform/python-sidecar/pipeline/orchestrator/writers/ph_r/__init__.py:3"
    rel = '''
from .. import ph_r
def test_a():
    assert ph_r.build()["statement"]
'''
    tests = [(SC / "pipeline" / "orchestrator" / "writers" / "tests" / "test_r.py", rel)]
    assert ac.narr_fidelity_scan(["statement"], cite, tests)["v"] == ac.PARTIAL
    mod = '''
import pipeline.orchestrator.writers.ph_r as w
def test_a():
    self_ok = w.build()
    assert self_ok["statement"]
'''
    tests = _tests(test_m=mod)
    assert ac.narr_fidelity_scan(["statement"], cite, tests)["covered"] == ["statement"]


def test_a_self_assert_call_and_pytest_raises_count_as_asserts():
    s = '''
import pytest
from pipeline.orchestrator.writers.ph_x import build_narration
class T:
    def test_a(self):
        self.assertEqual(build_narration(1)["statement"], "x")
'''
    assert ac.narr_fidelity_scan(["statement"], CITE, _tests(test_a=s))["covered"] == ["statement"]
    s2 = '''
import pytest
from pipeline.orchestrator.writers.ph_x import build_narration
def test_a():
    with pytest.raises(ValueError):
        build_narration({"statement": 1})
'''
    assert ac.narr_fidelity_scan(["statement"], CITE, _tests(test_a=s2))["v"] == ac.PARTIAL


def test_fidelity_is_no_detector_when_the_evidence_cites_no_readable_builder_module():
    r = ac.narr_fidelity_scan(["statement"], "no cite here", _tests(test_a=T_FULL))
    assert r["v"] == ac.NO_DET, r


# ───────────────────────── Narr.lint ─────────────────────────

BAD_SQL = 'Q = """SELECT fact_value_num FROM chart_facts WHERE fact_category = \'x\' ORDER BY fact_id LIMIT 1"""\n'
GOOD_SQL = 'Q = """SELECT fact_value_num FROM chart_facts WHERE fact_category = \'x\' AND fact_key = \'k\'"""\n'
BAD_TOKEN = 'def f(signal_type_id):\n    signal_headline_text = f"{signal_type_id}: something"\n'


def test_lint_passes_on_clean_scope_and_fails_on_a_fact_category_only_reduction(tmp_path):
    ok = tmp_path / "ok.py"
    ok.write_text(GOOD_SQL)
    bad = tmp_path / "bad.py"
    bad.write_text(BAD_SQL)
    assert ac.narr_lint_scan([ok])["v"] == ac.PASS
    r = ac.narr_lint_scan([ok, bad])
    assert r["v"] == ac.FAIL and "bad.py" in r["measured"] and "fact-category" in r["measured"], r


def test_lint_fails_on_a_raw_token_in_a_narrative_field(tmp_path):
    p = tmp_path / "w.py"
    p.write_text(BAD_TOKEN)
    r = ac.narr_lint_scan([p])
    assert r["v"] == ac.FAIL and "raw-token" in r["measured"], r


def test_lint_with_an_empty_scope_is_no_detector_never_pass():
    assert ac.narr_lint_scan([])["v"] == ac.NO_DET


def test_lint_unreadable_file_is_errored(tmp_path):
    assert ac.narr_lint_scan([tmp_path / "missing.py"])["v"] == ac.ERRORED


# ───────────────────────── reverse leg for [] ─────────────────────────

def _writer_units(monkeypatch, tmp_path, body):
    w3._sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/bo_p.py": w3._HDR + body})
    units, _ = ac._delegation_scope("bo_p", ["bo_p.py"])
    return units


def test_written_columns_reads_insert_column_lists_and_update_set_targets_on_own_tables(monkeypatch, tmp_path):
    units = _writer_units(monkeypatch, tmp_path, '''
@register("bo_p")
class P(WriterBase):
    def run(self, ctx):
        ctx.db_conn.execute("INSERT INTO t_own (chart_id, citation_human, score) VALUES (%s, %s, %s)", (1, 2, 3))
        ctx.db_conn.execute("UPDATE t_own SET valence = %s, note_text = 'x' WHERE id = %s", (1, 2))
        ctx.db_conn.execute("INSERT INTO t_other (secret_text) VALUES (%s)", (1,))
''')
    w = ac.written_columns(units, {"t_own"})
    assert w == {"t_own": {"chart_id", "citation_human", "score", "valence", "note_text"}}, w


def test_reverse_leg_flags_a_write_to_a_column_the_file_treats_as_narration_elsewhere():
    assert ac.prose_reverse_leg({"t": {"a", "citation_human"}}, {"citation_human", "statement"}) == ["t.citation_human"]
    assert ac.prose_reverse_leg({"t": {"a", "valence"}}, {"citation_human"}) == []
    assert ac.prose_reverse_leg({}, {"citation_human"}) == []


def test_the_vocabulary_is_every_declared_prose_column_and_path_column():
    v = ac.prose_vocabulary({"x": {"prose_fields": ["citation_human", "narrative.$.h"]}, "y": {"prose_fields": []},
                             "z": {"prose_fields": None}, "w": {}})
    assert v == {"citation_human", "narrative"}


# ───────────────────────── prose_checks orchestration ─────────────────────────

def _ctx(**kw):
    base = dict(table="t", columns=["id", "statement"], types={"statement": "text"}, defaults={},
                counts={"statement": GOOD}, units=[], paths=[], tests=_tests(test_a=T_FULL), vocabulary={"statement"},
                written=None)
    base.update(kw)
    return base


def _decl(pf, evidence=CITE):
    return {"prose_fields": pf, "evidence": {"prose_fields": evidence}}


def test_an_undeclared_asset_reads_no_detector_on_all_six_and_says_undeclared_not_no_prose():
    for decl in (None, {}, {"prose_fields": None}):
        got = ac.prose_checks("a", decl, _ctx())
        assert set(got) == set(NARR + NULL)
        for c, r in got.items():
            assert r["v"] == ac.NO_DET and "undeclared" in r["measured"] and "no prose" in r["measured"], (c, r)
            assert "cause" not in r


def test_an_empty_declaration_is_a_measured_na_candidate_with_the_no_prose_causes():
    got = ac.prose_checks("a", _decl([]), _ctx(written={"t": {"valence"}}))
    for c in NARR:
        assert got[c]["v"] == ac.NA and got[c]["cause"] == "no-prose", (c, got[c])
    for c in NULL:
        assert got[c]["v"] == ac.NA and got[c]["cause"] == "no-prose-declared", (c, got[c])


def test_an_empty_declaration_with_a_contradicting_write_fails_agree_and_the_rest_are_no_detector():
    got = ac.prose_checks("a", _decl([]), _ctx(written={"t": {"valence", "statement"}}))
    assert got["Narr.agree"]["v"] == ac.FAIL and "t.statement" in got["Narr.agree"]["measured"]
    for c in NARR[1:] + NULL:
        assert got[c]["v"] == ac.NO_DET and "cause" not in got[c], (c, got[c])


def test_an_empty_declaration_whose_writes_are_unreadable_is_no_detector_not_na():
    got = ac.prose_checks("a", _decl([]), _ctx(written=None))
    for c in NARR + NULL:
        assert got[c]["v"] == ac.NO_DET, (c, got[c])


def test_a_declared_asset_gets_every_check_measured():
    got = ac.prose_checks("a", _decl(["statement"]), _ctx())
    assert got["Narr.agree"]["v"] == ac.PASS
    assert got["Narr.checkable"]["v"] == ac.PASS and got["Narr.checkable"]["checkable"] == {"statement": 5}
    assert got["Narr.fidelity_test"]["v"] == ac.PARTIAL
    assert got["Narr.lint"]["v"] == ac.NO_DET            # no scope files supplied
    assert got["Null.schema_default"]["v"] == ac.PARTIAL and got["Null.blank_rows"]["v"] == ac.PARTIAL


def test_a_declared_asset_without_row_data_is_inconclusive_on_the_two_row_checks():
    got = ac.prose_checks("a", _decl(["statement"]), _ctx(counts=None))
    for c in ("Narr.checkable", "Null.blank_rows"):
        assert got[c]["v"] == ac.NO_DET and got[c]["inconclusive"] is True, (c, got[c])


def test_every_record_is_a_closed_vocabulary_verdict():
    for decl in (None, _decl([]), _decl(["statement"]), _decl(["nope"])):
        for r in ac.prose_checks("a", decl, _ctx()).values():
            assert r["v"] in (ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA, ac.ERRORED), r


# ───────────────────────── rollup: nothing becomes N/A or PASS by itself ─────────────────────────

def test_the_na_candidates_read_no_detector_in_the_rollup_until_a_rule_is_declared():
    m = ac.prose_checks("a", _decl([]), _ctx(written={"t": set()}))
    cells = ac.rollup_asset("L2", m)
    assert cells["Narr"]["v"] == ac.NO_DET and cells["Null"]["v"] == ac.NO_DET
    for c in cells["Narr"]["checks"] + cells["Null"]["checks"]:
        assert c["v"] == ac.NO_DET and "undecided" in c["reason"], c


def test_the_null_cell_never_reads_pass_and_the_narr_cell_never_reads_pass_through_fidelity():
    m = ac.prose_checks("a", _decl(["statement"]), _ctx(paths=[]))
    m["Narr.lint"] = dict(v=ac.PASS, measured="x")
    cells = ac.rollup_asset("L2", m)
    assert cells["Null"]["v"] == ac.PARTIAL
    assert cells["Narr"]["v"] == ac.PARTIAL


def test_an_asset_with_no_prose_measurements_still_reads_no_detector():
    assert ac.rollup_asset("L2", {})["Narr"]["v"] == ac.NO_DET
    assert ac.rollup_asset("L2", {})["Null"]["v"] == ac.NO_DET


# ───────────────────────── measure() integration ─────────────────────────

def test_measure_emits_the_six_records_for_every_asset_and_reads_the_catalog_extras(monkeypatch, tmp_path):
    reg = {"bo_p": w1._reg_row("bo_p", "t_own", count_sql="SELECT count(*) FROM t_own WHERE chart_id = $1")}
    w1._stub_layer(monkeypatch, tmp_path, reg, tables={"t_own": (["id", "statement", "chart_id"], [])},
                   writers={"bo_p": ["bo_p.py"]})
    w3._sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/bo_p.py": w3._HDR + '''
@register("bo_p")
class P(WriterBase):
    def run(self, ctx):
        ctx.db_conn.execute("INSERT INTO t_own (chart_id, statement) VALUES (%s, %s)", (1, "x"))
'''})
    decls = {"bo_p": _decl(["statement"], "platform/python-sidecar/pipeline/orchestrator/writers/bo_p.py:5")}
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decls)
    monkeypatch.setattr(ac, "python_tests", lambda *a, **k: [])
    seen = []

    base = w1._pg_like_psql({"t_own": 3})

    def psql(sql, sep="\x1f", timeout=None):
        seen.append(sql)
        if "FILTER" in sql:
            return [["4", "0"]]
        return base(sql, sep, timeout)
    monkeypatch.setattr(ac, "psql", psql)
    c = ac.measure("L0")
    m = next(a for a in c["assets"] if a["asset_id"] == "bo_p")["measurements"]
    for crit in NARR + NULL:
        assert crit in m, crit
    assert m["Narr.agree"]["v"] == ac.PASS               # a plain column needs no type; the stub catalog has none
    assert m["Narr.checkable"]["v"] == ac.PASS and m["Narr.checkable"]["checkable"] == {"statement": 4}
    assert m["Null.schema_default"]["v"] == ac.NO_DET    # the stub catalog carries no defaults: unread, not "none"
    assert any("FILTER" in s and "chart_id = '482012f1" in s for s in seen), seen


def test_measure_isolates_an_unreadable_declarations_file_to_the_six_checks(monkeypatch, tmp_path):
    reg = {"bg_a": w1._reg_row("bg_a", "t_one", count_sql="SELECT count(*) FROM t_one")}
    w1._stub_layer(monkeypatch, tmp_path, reg, tables={"t_one": (["a"], [])})
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"t_one": 3}))

    def boom(*a, **k):
        raise ac.DeclarationsError("unreadable")
    monkeypatch.setattr(ac, "load_asset_declarations", boom)
    c = ac.measure("L0")
    m = w1._m(c, "bg_a", "Build.target")
    assert m["v"] == ac.PASS
    for crit in NARR + NULL:
        assert w1._m(c, "bg_a", crit)["v"] == ac.ERRORED, crit


# ───────────────────────── catalog extras ─────────────────────────

def test_catalog_adds_types_and_defaults_and_leaves_cols_unchanged(monkeypatch):
    calls = []

    def psql(sql, sep="\x1f", timeout=None):
        calls.append(sql)
        if "information_schema.tables" in sql:
            return [["t"]]
        if "column_default" in sql:
            return [["t", "a", "text", "'x'::text"], ["t", "b", "jsonb", ""]]
        if "information_schema.columns" in sql:
            return [["t", "a"], ["t", "b"]]
        return []
    monkeypatch.setattr(ac, "psql", psql)
    cat = ac.catalog(["t"])
    assert cat["cols"] == {"t": ["a", "b"]}
    assert cat["types"] == {"t": {"a": "text", "b": "jsonb"}}
    assert cat["defaults"] == {"t": {"a": "'x'::text"}}


# ───────────────────────── update-only sub-reading of Idem.pattern ─────────────────────────

def _upd(monkeypatch, tmp_path, sql):
    w3._sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/bo_u.py": w3._HDR + (
        '@register("bo_u")\nclass U(WriterBase):\n    def run(self, ctx):\n'
        f'        ctx.db_conn.execute("""{sql}""", (1, 2))\n')})
    return ac.idem_scan("bo_u", ["bo_u.py"], "delete_then_insert", ["t_s"])


def test_update_only_accumulating_arithmetic_assignment_fails(monkeypatch, tmp_path):
    v, n = _upd(monkeypatch, tmp_path, "UPDATE t_s SET hits = hits + 1 WHERE chart_id = %s")
    assert v == ac.FAIL and "update-only:accumulating-assignment" in n[0] and "t_s (bo_u.py:" in n[0], (v, n)


@pytest.mark.parametrize("expr", ["COALESCE(hits, 0) + %s", "array_append(hits, %s)", "hits * 2", "array_cat(hits, %s)"])
def test_update_only_other_accumulating_forms_fail(monkeypatch, tmp_path, expr):
    v, n = _upd(monkeypatch, tmp_path, f"UPDATE t_s SET hits = {expr} WHERE chart_id = %s")
    assert v == ac.FAIL and "accumulating-assignment" in n[0], (v, n)


def test_update_only_literal_with_minus_or_self_name_in_a_string_is_not_accumulating(monkeypatch, tmp_path):
    v, n = _upd(monkeypatch, tmp_path, "UPDATE t_s SET hits = 'hits-1' WHERE id = %s")
    assert v == ac.PARTIAL and "accumulating" not in n[0], (v, n)


@pytest.mark.parametrize("sql,slug", [
    ("UPDATE t_s SET v = %s WHERE signal_id = %s", "keyed-row-set-unproven"),
    ("UPDATE t_s SET v = %s WHERE chart_id = %s", "scope-row-set-unproven"),
    ("UPDATE t_s SET v = NULL WHERE chart_id = %s AND v IS NOT NULL", "state-conditional-row-set-unproven"),
    ("UPDATE t_s SET v = %s WHERE chunk_id = %s AND v IS DISTINCT FROM %s", "guarded-row-set-unproven"),
    ("UPDATE t_s SET v = %s", "no-predicate-row-set-unproven"),
])
def test_update_only_non_accumulating_reads_partial_with_the_named_predicate_shape(monkeypatch, tmp_path, sql, slug):
    v, n = _upd(monkeypatch, tmp_path, sql)
    assert v == ac.PARTIAL and f"update-only:{slug}" in n[0], (v, n)
    assert "only UPDATEd in place" in n[0] and "rehearsal" in n[0], n


def test_update_only_never_reads_pass(monkeypatch, tmp_path):
    for sql in ("UPDATE t_s SET v = %s WHERE signal_id = %s", "UPDATE t_s SET v = %s WHERE chart_id = %s"):
        assert _upd(monkeypatch, tmp_path, sql)[0] != ac.PASS


def test_update_only_accumulation_with_a_cut_delegation_chain_stays_partial(monkeypatch, tmp_path):
    w3._sidecar(monkeypatch, tmp_path, {
        "pipeline/orchestrator/writers/bo_u.py": w3._HDR + (
            "from ga_writers.deep import go\n"
            '@register("bo_u")\nclass U(WriterBase):\n    def run(self, ctx):\n'
            '        ctx.db_conn.execute("UPDATE t_s SET hits = hits + 1 WHERE chart_id = %s", (1,))\n'
            "        go(ctx)\n"),
        "ga_writers/__init__.py": "", "ga_writers/deep.py": "from ga_writers.deeper import go2\ndef go(c):\n    go2(c)\n",
        "ga_writers/deeper.py": "from ga_writers.deepest import go3\ndef go2(c):\n    go3(c)\n",
        "ga_writers/deepest.py": 'def go3(c):\n    c.db_conn.execute("DELETE FROM t_s")\n'})
    v, n = ac.idem_scan("bo_u", ["bo_u.py"], "delete_then_insert", ["t_s"])
    assert v == ac.PARTIAL and "accumulating-assignment" in n[0], (v, n)


def test_a_replacing_writer_with_an_accumulating_update_is_still_pass(monkeypatch, tmp_path):
    w3._sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/bo_u.py": w3._HDR + (
        '@register("bo_u")\nclass U(WriterBase):\n    def run(self, ctx):\n'
        '        ctx.db_conn.execute("DELETE FROM t_s WHERE chart_id = %s", (1,))\n'
        '        ctx.db_conn.execute("INSERT INTO t_s (chart_id) VALUES (%s)", (1,))\n'
        '        ctx.db_conn.execute("UPDATE t_s SET hits = hits + 1 WHERE chart_id = %s", (1,))\n')})
    assert ac.idem_scan("bo_u", ["bo_u.py"], "delete_then_insert", ["t_s"])[0] == ac.PASS


def test_the_two_real_update_only_writers_stay_partial_with_a_named_reading():
    v, n = ac.idem_scan("bg_text_index", ["bg_text_index.py"], "upsert", ["classical_text_chunks"])
    assert v == ac.PARTIAL and "update-only:" in n[0] and "guarded-row-set-unproven" in n[0], (v, n)
    v, n = ac.idem_scan("bo_laksana_rerank", ["bo_laksana.py"], "delete_then_insert", ["bodha_msr_signals"])
    assert v == ac.PARTIAL and "update-only:" in n[0], (v, n)


# ───────────────────────── refinements found by the saved-census regression ─────────────────────────

def test_agree_resolves_a_declared_column_against_every_table_the_asset_owns():
    own = {"t_main": (["id"], {"id": "int"}), "t_facts": (["citation_human"], {"citation_human": "text"})}
    assert ac.grade_narr_agree_tables(["citation_human"], own)["v"] == ac.PASS


def test_agree_fails_only_when_every_owned_table_is_known_and_none_has_the_column():
    own = {"a": (["id"], {}), "b": (["x"], {})}
    r = ac.grade_narr_agree_tables(["nope"], own)
    assert r["v"] == ac.FAIL and "nope" in r["measured"] and "a, b" in r["measured"], r


def test_agree_is_no_detector_when_a_missing_column_could_sit_in_a_table_whose_columns_are_unknown():
    own = {"a": (["id"], {}), "b": (None, None)}
    assert ac.grade_narr_agree_tables(["nope"], own)["v"] == ac.NO_DET


def test_agree_json_path_needs_a_json_column_in_the_table_that_holds_it():
    own = {"a": (["n"], {"n": "text"}), "b": (["n"], {"n": "jsonb"})}
    assert ac.grade_narr_agree_tables(["n.$.k"], own)["v"] == ac.PASS
    assert ac.grade_narr_agree_tables(["n.$.k"], {"a": (["n"], {"n": "text"})})["v"] == ac.FAIL


@pytest.mark.parametrize("dflt", ["'{}'::jsonb", "'{}'", "'[]'::jsonb", "'{}'::json"])
def test_an_empty_json_container_default_is_not_a_prose_stand_in_for_a_json_path_entry(dflt):
    r = ac.grade_null_schema_default(["narrative.$.headline"], ["narrative"], {"narrative": dflt})
    assert r["v"] == ac.PARTIAL, r


def test_a_non_empty_json_default_or_any_default_on_a_plain_prose_column_still_fails():
    assert ac.grade_null_schema_default(["n.$.k"], ["n"], {"n": "'{\"k\": \"none\"}'::jsonb"})["v"] == ac.FAIL
    assert ac.grade_null_schema_default(["statement"], ["statement"], {"statement": "'{}'"})["v"] == ac.FAIL
    assert ac.grade_null_schema_default(["statement"], ["statement"], {"statement": "''::text"})["v"] == ac.FAIL


def test_fidelity_follows_a_module_returned_by_a_test_helper():
    s = '''
def _mod():
    from pipeline.orchestrator.writers import ph_x
    return ph_x

def test_a():
    w = _mod()
    out = w.build_narration({})
    assert out["statement"]
'''
    r = ac.narr_fidelity_scan(["statement"], CITE, _tests(test_a=s))
    assert r["v"] == ac.PARTIAL and r["covered"] == ["statement"], r


def test_prose_checks_uses_the_owned_tables_when_supplied():
    own = {"t": (["id"], {}), "u": (["statement"], {"statement": "text"})}
    got = ac.prose_checks("a", _decl(["statement"]), _ctx(own=own))
    assert got["Narr.agree"]["v"] == ac.PASS
