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


def test_fidelity_fails_when_a_test_exercises_the_module_but_references_no_declared_field():
    r = ac.narr_fidelity_scan(["statement"], CITE, _tests(test_a=T_NO_FIELD))
    assert r["v"] == ac.PARTIAL and r["covered"] == [] and "none names a declared field (direct or indirect)" in r["measured"], r


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
    assert ac.narr_fidelity_scan(["statement"], CITE, _tests(test_a=s2))["covered"] == []   # generic leaf only in the INPUT


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


def test_measure_scopes_a_shared_table_only_by_its_count_sql_and_reads_an_unshared_one_whole(monkeypatch, tmp_path):
    odd = "SELECT count(*) FROM {t} WHERE chart_id = $1 AND id IN (SELECT id FROM {t})"
    reg = {"bo_p": w1._reg_row("bo_p", "t_own", count_sql=odd.format(t="t_own")),
           "bo_q": w1._reg_row("bo_q", "t_own", count_sql=odd.format(t="t_own")),
           "bo_r": w1._reg_row("bo_r", "t_solo", count_sql=odd.format(t="t_solo"))}
    w1._stub_layer(monkeypatch, tmp_path, reg, tables={"t_own": (["id", "statement", "chart_id"], []),
                                                      "t_solo": (["id", "statement", "chart_id"], [])})
    decls = {a: _decl(["statement"], "platform/python-sidecar/x.py:1") for a in reg}
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decls)
    monkeypatch.setattr(ac, "python_tests", lambda *a, **k: [])
    seen = []
    base = w1._pg_like_psql({"t_own": 3, "t_solo": 3})

    def psql(sql, sep="\x1f", timeout=None):
        if "FILTER" in sql:
            seen.append(sql)
            return [["4", "0"]]
        return base(sql, sep, timeout)
    monkeypatch.setattr(ac, "psql", psql)
    c = ac.measure("L0")
    for a in ("bo_p", "bo_q"):
        m = w1._m(c, a, "Narr.checkable")
        assert m["v"] == ac.NO_DET and m["inconclusive"] is True, (a, m)
    r = w1._m(c, "bo_r", "Narr.checkable")
    assert r["v"] == ac.PARTIAL and r["scope"] == "whole-table upper bound", r      # F7: all-charts count is an upper bound
    assert len(seen) == 1 and seen[0].endswith(" FROM t_solo") and "t_own" not in seen[0], seen


# ───────────────────────── review round: F2 / F3 / F7 (owned-table resolution, scope) ─────────────────────────

def _cat(**tables):
    """table -> (columns, types, defaults)"""
    return dict(exists=set(tables), cols={t: v[0] for t, v in tables.items()}, keys={}, views=set(),
                types={t: v[1] for t, v in tables.items()}, defaults={t: v[2] for t, v in tables.items()})


def _mp(decl_fields, cat, ctables, shared=frozenset(), psql_rows=None, monkeypatch=None, csql=None):
    sqls = []

    def psql(sql, *a, **k):
        sqls.append(sql)
        if isinstance(psql_rows, Exception):
            raise psql_rows
        return psql_rows if psql_rows is not None else [["3", "0"] * len(decl_fields)][:1] and [["3", "0"] * len(decl_fields)]
    monkeypatch.setattr(ac, "psql", psql)
    r = dict(target_table="t_main", count_sql=csql or "SELECT count(*) FROM t_main WHERE chart_id = $1")
    out = ac._measure_prose("a", _decl(decl_fields, "platform/python-sidecar/x.py:1"), r, [], cat, ctables, shared, [], set())
    return out, sqls


def test_the_count_query_runs_against_the_owned_table_that_holds_the_declared_column(monkeypatch):
    cat = _cat(t_main=(["id", "chart_id"], {}, {}), t_facts=(["id", "citation_human"], {"citation_human": "text"}, {}))
    out, sqls = _mp(["citation_human"], cat, ["t_main", "t_facts"], monkeypatch=monkeypatch)
    assert len(sqls) == 1 and " FROM t_facts" in sqls[0] and "t_main" not in sqls[0], sqls
    assert out["Narr.checkable"]["v"] != ac.ERRORED and out["Narr.checkable"]["checkable"] == {"citation_human": 3}


def test_an_entry_no_owned_table_holds_is_unknown_for_that_entry_never_errored(monkeypatch):
    cat = _cat(t_main=(["id", "chart_id"], {}, {}))
    out, sqls = _mp(["ghost"], cat, ["t_main"], monkeypatch=monkeypatch)
    assert sqls == [] and out["Narr.checkable"]["v"] == ac.NO_DET and out["Narr.checkable"]["inconclusive"] is True
    assert out["Narr.agree"]["v"] == ac.FAIL
    assert out["Null.schema_default"]["v"] == ac.NO_DET and out["Null.blank_rows"]["v"] == ac.NO_DET


def test_entries_in_two_owned_tables_are_counted_per_table_and_merged(monkeypatch):
    cat = _cat(t_main=(["id", "chart_id", "a"], {}, {}), t_facts=(["id", "b"], {}, {}))
    out, sqls = _mp(["a", "b"], cat, ["t_main", "t_facts"], psql_rows=[["2", "0"]], monkeypatch=monkeypatch)
    assert len(sqls) == 2 and out["Narr.checkable"]["checkable"] == {"a": 2, "b": 2}, (sqls, out["Narr.checkable"])


def test_a_count_that_raises_degrades_only_the_two_row_checks_to_errored(monkeypatch):
    cat = _cat(t_main=(["id", "chart_id", "a"], {}, {}))
    out, _ = _mp(["a"], cat, ["t_main"], psql_rows=ac.Unknown("boom"), monkeypatch=monkeypatch)
    assert out["Narr.checkable"]["v"] == ac.ERRORED and out["Null.blank_rows"]["v"] == ac.ERRORED
    assert out["Narr.agree"]["v"] == ac.PASS


def test_schema_default_reads_the_default_of_the_owned_table_that_holds_the_column():
    own = {"t_main": (["id"], {}, {"id": "0"}), "t_facts": (["citation_human"], {}, {"citation_human": "'none'::text"})}
    assert ac.grade_null_schema_default_tables(["citation_human"], own)["v"] == ac.FAIL
    own["t_facts"] = (["citation_human"], {}, {})
    assert ac.grade_null_schema_default_tables(["citation_human"], own)["v"] == ac.PARTIAL
    assert ac.grade_null_schema_default_tables(["ghost"], own)["v"] == ac.NO_DET
    assert ac.grade_null_schema_default_tables(["citation_human"], {"t": (["citation_human"], {}, None)})["v"] == ac.NO_DET


def test_a_default_on_a_same_named_column_of_another_table_is_not_read():
    own = {"t_main": (["id", "statement"], {}, {"statement": "'x'"}), "t_facts": (["citation_human"], {}, {})}
    assert ac.grade_null_schema_default_tables(["citation_human"], own)["v"] == ac.PARTIAL


def test_whole_table_count_on_a_chart_table_is_an_upper_bound_partial_with_the_scope_recorded(monkeypatch):
    cat = _cat(t_solo=(["id", "chart_id", "a"], {}, {}))
    odd = "SELECT count(*) FROM t_solo WHERE chart_id = $1 AND id IN (SELECT id FROM t_solo)"
    out, sqls = _mp(["a"], cat, ["t_solo"], monkeypatch=monkeypatch, csql=odd)
    assert sqls and out["Narr.checkable"]["v"] == ac.PARTIAL
    assert out["Narr.checkable"]["scope"] == "whole-table upper bound" and "upper bound" in out["Narr.checkable"]["measured"]


def test_a_table_without_chart_id_or_a_chart_scoped_count_sql_may_pass(monkeypatch):
    cat = _cat(t_solo=(["id", "a"], {}, {}))
    out, _ = _mp(["a"], cat, ["t_solo"], monkeypatch=monkeypatch, csql="SELECT count(*) FROM t_solo WHERE id IN (SELECT 1)")
    assert out["Narr.checkable"]["v"] == ac.PASS and "no chart_id" in out["Narr.checkable"]["scope"]
    cat = _cat(t_main=(["id", "chart_id", "a"], {}, {}))
    out, sqls = _mp(["a"], cat, ["t_main"], monkeypatch=monkeypatch)
    assert out["Narr.checkable"]["v"] == ac.PASS and out["Narr.checkable"]["scope"] == "chart-scoped by count_sql"


# ───────────────────────── review round: F1 (a lint PASS needs an applicable surface) ─────────────────────────

def test_lint_is_not_applicable_when_no_lint_surface_touches_the_asset(tmp_path):
    p = tmp_path / "w.py"
    p.write_text("def f(x):\n    return x + 1\n")
    r = ac.narr_lint_scan([p], ["citation_human"])
    assert r["v"] == ac.NO_DET and "not applicable" in r["measured"] and r["applied"] == [], r


def test_lint_passes_when_the_fact_category_surface_is_in_scope_and_names_it(tmp_path):
    p = tmp_path / "w.py"
    p.write_text(GOOD_SQL)
    r = ac.narr_lint_scan([p], ["citation_human"])
    assert r["v"] == ac.PASS and r["applied"] == ["fact-category-pin"], r


@pytest.mark.parametrize("col", ["signal_headline_text", "signal_text", "x_thesis", "obj_narrative"])
def test_lint_passes_when_a_declared_column_is_one_the_raw_token_lint_matches(tmp_path, col):
    p = tmp_path / "w.py"
    p.write_text("def f(x):\n    return x\n")
    r = ac.narr_lint_scan([p], [col])
    assert r["v"] == ac.PASS and r["applied"] == ["raw-token"], r


def test_lint_both_surfaces_are_recorded(tmp_path):
    p = tmp_path / "w.py"
    p.write_text(GOOD_SQL)
    assert ac.narr_lint_scan([p], ["signal_headline_text"])["applied"] == ["fact-category-pin", "raw-token"]


def test_lint_violation_fails_even_when_the_surface_is_only_inferred_from_the_violation(tmp_path):
    p = tmp_path / "w.py"
    p.write_text(BAD_SQL)
    assert ac.narr_lint_scan([p], ["citation_human"])["v"] == ac.FAIL


def test_lint_a_substring_column_name_is_not_a_raw_token_surface(tmp_path):
    p = tmp_path / "w.py"
    p.write_text("x = 1\n")
    assert ac.narr_lint_scan([p], ["signal_textual"])["v"] == ac.NO_DET


def test_lint_allowlisted_only_violations_read_partial_through_the_real_lint(tmp_path, monkeypatch):
    p = tmp_path / "w.py"
    p.write_text(BAD_SQL)
    fcp = ac._lint_module("check_fact_category_pinning")
    monkeypatch.setattr(fcp, "load_allowlist", lambda path: [dict(file=str(p), line=None, pattern="chart_facts")])
    r = ac.narr_lint_scan([p], ["citation_human"])
    assert r["v"] == ac.PARTIAL and "allowlisted" in r["measured"] and str(p) in r["measured"], r
    monkeypatch.setattr(fcp, "load_allowlist", lambda path: [])
    assert ac.narr_lint_scan([p], ["citation_human"])["v"] == ac.FAIL


# ───────────────────────── review round: F4 (no false credit for fidelity tests) ─────────────────────────
_H = "from pipeline.orchestrator.writers.ph_x import build_narration\n"


def _fid(src, entries=("statement",)):
    return ac.narr_fidelity_scan(list(entries), CITE, _tests(test_a=src))


@pytest.mark.parametrize("src", [
    _H + "def test_a():\n    out = build_narration(1)\n\ndef test_b():\n    assert {'statement': 1}['statement']\n",
    _H + "def check_it():\n    assert build_narration(1)['statement']\n",
    _H + "import pytest\n@pytest.mark.skip\ndef test_a():\n    assert build_narration(1)['statement']\n",
    _H + "import pytest\n@pytest.mark.skipif(True, reason='x')\ndef test_a():\n    assert build_narration(1)['statement']\n",
    _H + "import pytest\npytestmark = pytest.mark.skip\ndef test_a():\n    assert build_narration(1)['statement']\n",
    _H + "import pytest\ndef test_a():\n    pytest.skip('x')\n    assert build_narration(1)['statement']\n",
    _H + "def test_a():\n    build_narration(1)['statement']\n    assert True\n",
])
def test_fidelity_gives_no_credit_for_the_false_positive_shapes(src):
    assert _fid(src)["v"] == ac.FAIL, src


def test_fidelity_credits_a_method_of_a_test_class_and_an_assert_on_the_builders_result():
    src = _H + "class TestX:\n    def test_a(self):\n        assert build_narration(1)['statement']\n"
    assert _fid(src)["v"] == ac.PARTIAL


def test_a_generic_leaf_is_covered_only_in_an_assert_or_beside_a_specific_declared_key():
    src = _H + "def test_a():\n    out = build_narration({'statement': 1})\n    assert out['citation_human']\n"
    r = _fid(src, ("statement", "citation_human"))
    assert r["v"] == ac.PARTIAL and r["covered"] == ["statement", "citation_human"], r      # beside a specific key
    only = _H + "def test_a():\n    out = build_narration({'statement': 1})\n    assert out\n"
    assert _fid(only)["v"] == ac.PARTIAL and _fid(only)["covered"] == []


def test_importlib_import_module_of_the_cited_module_counts_as_an_import():
    src = ("import importlib\ndef test_a():\n    w = importlib.import_module('pipeline.orchestrator.writers.ph_x')\n"
           "    assert w.build_narration(1)['statement']\n")
    assert _fid(src)["v"] == ac.PARTIAL


def test_a_specific_leaf_in_the_input_only_still_needs_the_assert_to_exist():
    src = _H + "def test_a():\n    build_narration({'citation_human': 1})\n"
    assert _fid(src, ("citation_human",))["v"] == ac.FAIL


# ───────────────────────── review round: F5 (agree is two-way: undeclared written vocabulary columns) ─────────────────────────

def test_agree_is_partial_when_the_writer_writes_a_prose_vocabulary_column_it_does_not_declare():
    got = ac.prose_checks("a", _decl(["statement"]), _ctx(written={"t": {"statement", "citation_human"}},
                                                          vocabulary={"statement", "citation_human"}))
    assert got["Narr.agree"]["v"] == ac.PARTIAL and "t.citation_human" in got["Narr.agree"]["measured"], got["Narr.agree"]
    assert "undeclared" in got["Narr.agree"]["measured"]


def test_agree_stays_pass_when_every_written_vocabulary_column_is_declared_or_the_writes_are_unread():
    ok = ac.prose_checks("a", _decl(["statement"]), _ctx(written={"t": {"statement", "valence"}}, vocabulary={"statement"}))
    assert ok["Narr.agree"]["v"] == ac.PASS
    unread = ac.prose_checks("a", _decl(["statement"]), _ctx(written=None, vocabulary={"statement", "citation_human"}))
    assert unread["Narr.agree"]["v"] == ac.PASS


def test_a_declared_json_path_column_counts_as_declared_for_the_two_way_check():
    own = {"t": (["n"], {"n": "jsonb"})}
    got = ac.prose_checks("a", _decl(["n.$.k"]), _ctx(own=own, written={"t": {"n"}}, vocabulary={"n"}, counts=None))
    assert got["Narr.agree"]["v"] == ac.PASS


def test_a_declared_but_absent_column_still_fails_whatever_is_written():
    got = ac.prose_checks("a", _decl(["ghost"]), _ctx(written={"t": {"citation_human"}}, vocabulary={"citation_human"}))
    assert got["Narr.agree"]["v"] == ac.FAIL


# ───────────────────────── review round: F6 (the rollup does not trust the record) ─────────────────────────

def _chk(crit, **rec):
    cells = ac.rollup_asset("L2", {crit: dict(measured="x", **rec)})
    gate = ac.CRITERION_REGISTRY[crit]["gate"]
    return next(c for c in cells[gate]["checks"] if c["criterion"] == crit), cells[gate]


@pytest.mark.parametrize("v", [ac.PASS, ac.PARTIAL])
def test_an_inconclusive_record_rolls_up_no_detector_and_carries_the_flag(v):
    c, cell = _chk("Narr.checkable", v=v, inconclusive=True)
    assert c["v"] == ac.NO_DET and c["inconclusive"] is True and "INCONCLUSIVE" in c["reason"], c
    assert cell["v"] == ac.NO_DET


def test_an_inconclusive_fail_or_errored_record_is_not_softened():
    assert _chk("Null.blank_rows", v=ac.FAIL, inconclusive=True)[0]["v"] == ac.FAIL
    assert _chk("Null.blank_rows", v=ac.ERRORED, inconclusive=True)[0]["v"] == ac.ERRORED


def test_a_null_check_never_rolls_up_pass_and_the_null_cell_never_reads_pass():
    c, _ = _chk("Null.schema_default", v=ac.PASS)
    assert c["v"] == ac.PARTIAL and "Null" in c["reason"], c
    ms = {crit: dict(v=ac.PASS, measured="x") for crit, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Null"}
    assert ac.rollup_asset("L2", ms)["Null"]["v"] == ac.PARTIAL


def test_a_fidelity_pass_record_is_capped_at_partial_in_the_rollup():
    assert _chk("Narr.fidelity_test", v=ac.PASS)[0]["v"] == ac.PARTIAL
    ms = {crit: dict(v=ac.PASS, measured="x") for crit, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Narr"}
    assert ac.rollup_asset("L2", ms)["Narr"]["v"] == ac.PARTIAL


def test_a_plain_measured_record_has_no_inconclusive_key():
    c, _ = _chk("Narr.agree", v=ac.PASS)
    assert c["v"] == ac.PASS and "inconclusive" not in c


# ───────────────────────── review round: F8 (blank trim covers tabs/newlines; non-string JSON leaves are not text) ─────────────────────────

def test_blank_detection_trims_tabs_newlines_and_carriage_returns():
    sql = ac.prose_row_counts_sql("t", ["a", "n.$.k", "d.$.i[*].r"], "")
    assert sql.count("btrim(") >= 6
    assert sql.count("btrim(") == sql.count("E' \\t\\r\\n')"), sql


def test_a_json_path_scalar_must_be_a_json_string_to_count_as_text():
    sql = ac.prose_row_counts_sql("t", ["narrative.$.headline"], "")
    assert "jsonb_typeof(\"narrative\"::jsonb #> '{headline}') = 'string'" in sql, sql
    assert sql.count("jsonb_typeof(\"narrative\"::jsonb #> '{headline}') = 'string'") == 2     # checkable and blank


def test_a_plain_json_column_must_hold_a_json_string_and_an_array_column_is_never_text():
    sql = ac.prose_row_counts_sql("t", ["j", "arr", "plain"], "", types={"j": "jsonb", "arr": "ARRAY", "plain": "text"})
    assert "jsonb_typeof(\"j\"::jsonb) = 'string'" in sql
    assert "(FALSE)" in sql and "\"arr\"::text" not in sql
    assert "\"plain\"::text" in sql


def test_prose_row_counts_passes_the_column_types_through(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: seen.append(sql) or [["1", "0"]])
    ac.prose_row_counts("t", ["arr"], "", types={"arr": "ARRAY"})
    assert "(FALSE)" in seen[0]


# ───────────────────────── review round: F9 (update-only: no false FAIL, more accumulating forms) ─────────────────────────

@pytest.mark.parametrize("expr", ["payload - 'key'", "payload - ARRAY['a','b']", "payload - %s::text"])
def test_update_only_jsonb_key_delete_is_idempotent_not_accumulating(monkeypatch, tmp_path, expr):
    v, n = _upd(monkeypatch, tmp_path, f"UPDATE t_s SET payload = {expr} WHERE chart_id = %s")
    assert v == ac.PARTIAL and "accumulating" not in n[0], (v, n)


def _two(monkeypatch, tmp_path, first, second, same_fn=True):
    body = (f'        ctx.db_conn.execute("""{first}""", (1,))\n'
            + ('' if same_fn else '    def other(self, ctx):\n')
            + f'        ctx.db_conn.execute("""{second}""", (1,))\n')
    w3._sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/bo_u.py": w3._HDR + (
        '@register("bo_u")\nclass U(WriterBase):\n    def run(self, ctx):\n' + body)})
    return ac.idem_scan("bo_u", ["bo_u.py"], "delete_then_insert", ["t_s"])


RESET = "UPDATE t_s SET hits = 0 WHERE chart_id = %s"
ACC = "UPDATE t_s SET hits = hits + 1 WHERE chart_id = %s"


def test_update_only_a_reset_of_the_same_column_earlier_in_the_same_function_is_not_accumulating(monkeypatch, tmp_path):
    v, n = _two(monkeypatch, tmp_path, RESET, ACC)
    assert v == ac.PARTIAL and "accumulating" not in n[0], (v, n)


def test_update_only_a_reset_after_the_accumulation_or_in_another_function_does_not_excuse_it(monkeypatch, tmp_path):
    assert _two(monkeypatch, tmp_path, ACC, RESET)[0] == ac.FAIL
    assert _two(monkeypatch, tmp_path, RESET, ACC, same_fn=False)[0] == ac.FAIL


def test_update_only_a_reset_of_a_different_column_does_not_excuse_it(monkeypatch, tmp_path):
    assert _two(monkeypatch, tmp_path, "UPDATE t_s SET other = 0 WHERE chart_id = %s", ACC)[0] == ac.FAIL


@pytest.mark.parametrize("sql", [
    "UPDATE t_s SET hits = concat(hits, %s) WHERE chart_id = %s",
    "UPDATE t_s SET doc = jsonb_insert(doc, '{a}', %s::jsonb) WHERE chart_id = %s",
    "UPDATE t_s SET (a, hits) = (%s, hits + 1) WHERE chart_id = %s",
    "UPDATE t_s SET (hits, b) = ROW(hits + 1, %s) WHERE chart_id = %s",
])
def test_update_only_more_accumulating_forms_fail(monkeypatch, tmp_path, sql):
    v, n = _upd(monkeypatch, tmp_path, sql)
    assert v == ac.FAIL and "accumulating-assignment" in n[0], (v, n)


def test_update_only_a_tuple_assignment_without_self_reference_is_not_accumulating(monkeypatch, tmp_path):
    v, n = _upd(monkeypatch, tmp_path, "UPDATE t_s SET (a, b) = (%s, %s) WHERE chart_id = %s")
    assert v == ac.PARTIAL and "accumulating" not in n[0], (v, n)


def test_update_only_self_referencing_concat_is_named_with_the_type_unread_slug(monkeypatch, tmp_path):
    v, n = _upd(monkeypatch, tmp_path, "UPDATE t_s SET tags = tags || %s WHERE chart_id = %s")
    assert v == ac.PARTIAL and "update-only:self-referencing-concat-type-unread" in n[0], (v, n)


# ───────────────────────── review round: mutation gaps ─────────────────────────

def test_every_comparison_in_the_row_count_sql_is_case_insensitive_and_string_typed():
    sql = ac.prose_row_counts_sql("t", ["a", "n.$.k", "d.$.i[*].r"], "")
    assert sql.count("lower(btrim(") == sql.count("btrim(") >= 6
    assert sql.count("jsonb_typeof(x) = 'string'") == 2          # the wildcard form, checkable and blank


def test_a_terminal_array_wildcard_entry_builds_the_jsonpath_and_the_fidelity_leaf():
    sql = ac.prose_row_counts_sql("t", ["d.$.items[*]"], "")
    assert "'$.\"items\"[*]'" in sql, sql
    r = ac.narr_fidelity_scan(["d.$.items[*]"], CITE, _tests(test_a=_H + "def test_a():\n    assert build_narration(1)['items']\n"))
    assert r["covered"] == ["d.$.items[*]"], r


@pytest.mark.parametrize("tail", ["UNION VALUES (1)", "LIMIT 1", "ORDER BY id", "GROUP BY id", "HAVING 1 = 1",
                                  "INTERSECT VALUES (1)", "EXCEPT VALUES (1)", "; DROP TABLE x"])
def test_scope_tail_refuses_every_banned_keyword(tail):
    assert ac._count_scope_tail(f"SELECT count(*) FROM t WHERE a = 1 {tail}", "t") is None


def test_a_plain_entry_on_the_same_column_as_a_json_path_entry_keeps_the_empty_json_default_a_fail():
    assert ac.grade_null_schema_default(["n", "n.$.k"], ["n"], {"n": "'{}'::jsonb"})["v"] == ac.FAIL
    assert ac.grade_null_schema_default(["n.$.k", "n.$.j"], ["n"], {"n": "'{}'::jsonb"})["v"] == ac.PARTIAL


def test_update_only_any_keyed_predicate_form_is_named_keyed(monkeypatch, tmp_path):
    v, n = _upd(monkeypatch, tmp_path, "UPDATE t_s SET v = %s WHERE signal_id = ANY(%s)")
    assert v == ac.PARTIAL and "update-only:keyed-row-set-unproven" in n[0], (v, n)


def test_python_tests_reads_only_test_files_under_tests_or_dunder_tests(tmp_path):
    for rel in ("tests/test_a.py", "x/__tests__/test_b.py", "other/test_c.py", "tests/helper.py", "src/test_d.py"):
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("x = 1\n")
    assert sorted(p.name for p, _ in ac.python_tests(tmp_path)) == ["test_a.py", "test_b.py"]


def test_written_columns_strips_identifier_quotes(monkeypatch, tmp_path):
    units = _writer_units(monkeypatch, tmp_path, '''
@register("bo_p")
class P(WriterBase):
    def run(self, ctx):
        ctx.db_conn.execute('INSERT INTO public."t_own" ("citation_human", "score") VALUES (%s, %s)', (1, 2))
        ctx.db_conn.execute('UPDATE "t_own" SET "valence" = %s WHERE id = %s', (1, 2))
''')
    assert ac.written_columns(units, {"t_own"}) == {"t_own": {"citation_human", "score", "valence"}}


def test_written_columns_is_none_when_a_write_has_no_column_list_or_an_unresolved_name(monkeypatch, tmp_path):
    units = _writer_units(monkeypatch, tmp_path, '''
@register("bo_p")
class P(WriterBase):
    def run(self, ctx):
        ctx.db_conn.execute("INSERT INTO t_own SELECT * FROM t_src")
''')
    assert ac.written_columns(units, {"t_own"}) is None


def test_a_failing_types_and_defaults_read_leaves_the_columns_and_the_layer_intact(monkeypatch):
    def psql(sql, sep="\x1f", timeout=None):
        if "information_schema.tables" in sql:
            return [["t"]]
        if "column_default" in sql:
            raise ac.Unknown("denied")
        if "information_schema.columns" in sql:
            return [["t", "a"]]
        return []
    monkeypatch.setattr(ac, "psql", psql)
    cat = ac.catalog(["t"])
    assert cat["cols"] == {"t": ["a"]} and cat["types"] is None and cat["defaults"] is None


def test_measure_asks_the_catalog_for_the_count_sql_tables_too(monkeypatch, tmp_path):
    reg = {"bg_a": w1._reg_row("bg_a", "t_one", count_sql="SELECT count(*) FROM t_one WHERE chart_id = $1")}
    w1._stub_layer(monkeypatch, tmp_path, reg, tables={"t_one": (["a"], [])})
    asked = []
    monkeypatch.setattr(ac, "catalog", lambda ts: asked.append(list(ts)) or dict(exists={"t_one"}, cols={"t_one": ["a"]}, keys={}))
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"t_one": 3}))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    ac.measure("L0")
    assert asked and {"t_one"} <= set(asked[0]) and asked[0].count("t_one") == 2, asked      # target + count_sql table


def test_a_prose_helper_that_raises_degrades_only_the_six_checks_in_measure(monkeypatch, tmp_path):
    reg = {"bg_a": w1._reg_row("bg_a", "t_one", count_sql="SELECT count(*) FROM t_one")}
    w1._stub_layer(monkeypatch, tmp_path, reg, tables={"t_one": (["a"], [])})
    monkeypatch.setattr(ac, "psql", w1._pg_like_psql({"t_one": 3}))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"bg_a": _decl(["a"])})
    monkeypatch.setattr(ac, "python_tests", lambda *a, **k: (_ for _ in ()).throw(ac.Unknown("tests unreadable")))
    c = ac.measure("L0")
    assert w1._m(c, "bg_a", "Build.target")["v"] == ac.PASS
    for crit in NARR + NULL:
        assert w1._m(c, "bg_a", crit)["v"] == ac.ERRORED, crit


def test_an_unknown_entry_keeps_checkable_partial_and_is_named_unknown():
    r = ac.grade_narr_checkable(["a", "b"], {"a": {"checkable": 5, "blank": 0, "scope": "chart-scoped by count_sql"}, "b": None})
    assert r["v"] == ac.PARTIAL and "b=unknown" in r["measured"] and r["checkable"] == {"a": 5, "b": None}, r
    assert ac.grade_narr_checkable(["a", "b"], {"b": None})["v"] == ac.NO_DET        # nothing known: INCONCLUSIVE
    n = ac.grade_null_blank_rows(["a", "b"], {"a": GOOD, "b": None})
    assert n["v"] == ac.PARTIAL and "unknown for b" in n["measured"], n


# ───────────────────────── final review: item 2 (false FAILs in the fidelity scan) ─────────────────────────

def test_a_declared_leaf_matches_as_a_substring_of_the_names_a_test_uses():
    src = ("from pipeline.orchestrator.writers.ph_x import _citation_human_position\n"
           "def test_a():\n    assert _citation_human_position(1).endswith('.')\n")
    r = ac.narr_fidelity_scan(["citation_human"], CITE, _tests(test_a=src))
    assert r["v"] == ac.PARTIAL and r["covered"] == ["citation_human"], r


def test_a_test_name_that_is_a_token_of_the_declared_leaf_covers_it():
    src = _H + "def test_a():\n    v = build_narration(1)\n    assert v['reason']\n"
    assert ac.narr_fidelity_scan(["verdict_reason"], CITE, _tests(test_a=src))["covered"] == ["verdict_reason"]


def test_one_level_of_module_helper_is_followed_for_the_call_and_the_leaves():
    src = (_H + "def _run(x):\n    return build_narration(x)\n\n"
           "def test_a():\n    out = _run(1)\n    assert out['citation_human']\n")
    r = ac.narr_fidelity_scan(["citation_human"], CITE, _tests(test_a=src))
    assert r["v"] == ac.PARTIAL and r["covered"] == ["citation_human"], r
    helper_leaf = (_H + "def _run(x):\n    return build_narration({'citation_human': x})\n\n"
                   "def test_a():\n    assert _run(1)\n")
    assert ac.narr_fidelity_scan(["citation_human"], CITE, _tests(test_a=helper_leaf))["covered"] == ["citation_human"]


def test_a_helper_two_levels_down_is_not_followed():
    src = (_H + "def _a(x):\n    return build_narration(x)\n\ndef _b(x):\n    return _a(x)\n\n"
           "def test_a():\n    assert _b(1)['citation_human']\n")
    assert ac.narr_fidelity_scan(["citation_human"], CITE, _tests(test_a=src))["v"] == ac.FAIL


def test_an_importlib_fixture_that_binds_the_module_is_followed():
    src = ("import importlib, pytest\n@pytest.fixture\ndef mod():\n"
           "    return importlib.import_module('pipeline.orchestrator.writers.ph_x')\n"
           "def test_a(mod):\n    assert mod.build_narration(1)['citation_human']\n")
    r = ac.narr_fidelity_scan(["citation_human"], CITE, _tests(test_a=src))
    assert r["v"] == ac.PARTIAL and r["covered"] == ["citation_human"], r


def test_from_importlib_import_module_aliases_are_resolved():
    src = ("from importlib import import_module as im\ndef test_a():\n"
           "    w = im('pipeline.orchestrator.writers.ph_x')\n    assert w.build_narration(1)['citation_human']\n")
    assert ac.narr_fidelity_scan(["citation_human"], CITE, _tests(test_a=src))["v"] == ac.PARTIAL


def test_qualifying_tests_that_name_no_declared_field_read_partial_with_the_stated_text_not_fail():
    r = ac.narr_fidelity_scan(["citation_human"], CITE, _tests(test_a=T_NO_FIELD))
    assert r["v"] == ac.PARTIAL and r["covered"] == [] and "tests call the builder but none names a declared field (direct or indirect)" in r["measured"]
    assert ac.narr_fidelity_scan(["citation_human"], CITE, _tests(test_a=T_NO_ASSERT))["v"] == ac.FAIL   # no qualifying test


# ───────────────────────── final review: item 3 (a parseable count_sql is not chart-scoped unless it binds chart_id) ─────────────────────────

@pytest.mark.parametrize("csql", ["SELECT count(*) FROM t_main",
                                  "SELECT count(*) FROM t_main WHERE kind = 'x'",
                                  "SELECT count(*) FROM t_main WHERE chart_id = $1 OR kind = 'x'",
                                  "SELECT count(*) FROM t_main WHERE chart_id IS NOT NULL"])
def test_a_parseable_count_sql_that_does_not_bind_chart_id_is_an_upper_bound_on_a_chart_table(monkeypatch, csql):
    cat = _cat(t_main=(["id", "chart_id", "a"], {}, {}))
    out, _ = _mp(["a"], cat, ["t_main"], monkeypatch=monkeypatch, csql=csql)
    r = out["Narr.checkable"]
    assert r["v"] == ac.PARTIAL and r["scope"] == "whole-table upper bound", r


def test_a_count_sql_that_binds_chart_id_to_the_census_chart_is_chart_scoped(monkeypatch):
    cat = _cat(t_main=(["id", "chart_id", "a"], {}, {}))
    for csql in ("SELECT count(*) FROM t_main WHERE chart_id = $1",
                 "SELECT count(*) FROM t_main WHERE kind = 'x' AND chart_id = $1"):
        out, _ = _mp(["a"], cat, ["t_main"], monkeypatch=monkeypatch, csql=csql)
        assert out["Narr.checkable"]["v"] == ac.PASS and out["Narr.checkable"]["scope"] == "chart-scoped by count_sql", csql


def test_a_parseable_count_sql_on_a_table_without_chart_id_keeps_its_own_predicate_scope(monkeypatch):
    cat = _cat(t_glob=(["id", "a"], {}, {}))
    out, _ = _mp(["a"], cat, ["t_glob"], monkeypatch=monkeypatch, csql="SELECT count(*) FROM t_glob WHERE kind = 'x'")
    assert out["Narr.checkable"]["v"] == ac.PASS and out["Narr.checkable"]["scope"] == "count_sql predicate (not chart-scoped)"


# ───────────────────────── final review: item 4 (blank rows honour the count's scope) ─────────────────────────

def test_blank_rows_in_a_whole_table_upper_bound_count_never_fail_this_chart():
    c = {"a": {"checkable": 3, "blank": 2, "scope": "whole-table upper bound"}}
    r = ac.grade_null_blank_rows(["a"], c)
    assert r["v"] == ac.PARTIAL and "upper bound" in r["measured"] and "a=2" in r["measured"], r
    assert ac.grade_null_blank_rows(["a"], {"a": dict(c["a"], scope="chart-scoped by count_sql")})["v"] == ac.FAIL
    assert ac.grade_null_blank_rows(["a"], {"a": dict(c["a"], scope="whole-table (table has no chart_id column)")})["v"] == ac.FAIL
    assert ac.grade_null_blank_rows(["a"], {"a": {"checkable": 3, "blank": 2}})["v"] == ac.FAIL


def test_a_chart_scoped_blank_row_still_fails_beside_an_upper_bound_entry():
    c = {"a": {"checkable": 3, "blank": 2, "scope": "whole-table upper bound"}, "b": {"checkable": 3, "blank": 1, "scope": "chart-scoped by count_sql"}}
    r = ac.grade_null_blank_rows(["a", "b"], c)
    assert r["v"] == ac.FAIL and "column(s): b=1" in r["measured"] and "not counted: a=2" in r["measured"], r
