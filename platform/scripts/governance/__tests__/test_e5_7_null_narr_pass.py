"""test_e5_7_null_narr_pass.py: E5.7 Worker E (SS N-150 R7): the REAL PASS paths of Null.schema_default / Null.blank_rows (the static writer scan),
Narr.fidelity_test (a declared, source-verified golden-value test) and the count_sql scope reading that Narr.checkable / Null.blank_rows stand on.

Every test drives the real census functions; the database is never touched. Real committed inputs: the registry count_sql texts of
NIRMANA_T0_MANIFEST_v1_1.json and two real L1 writers (ga_condition, ga_tajaka).

Run: python -m pytest platform/scripts/governance/__tests__/test_e5_7_null_narr_pass.py -q
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402

SC = ac.SIDECAR
NULL = ("Null.schema_default", "Null.blank_rows")


# ───────────────────────── the Python placeholder vocabulary (one definition) ─────────────────────────

@pytest.mark.parametrize("v", ["", "  ", "N/A.", "Ｎ/Ａ", "n​/a", "—", "pending", "Not found", "none", "0", "N / A", "!!", "unsourced"])
def test_placeholder_values_read_as_placeholders(v):
    assert ac.ldgr_placeholder_py(v) is True, v


@pytest.mark.parametrize("v", ["Graha node: Sun", "Sun is exalted in Aries", "प्रथम", "Bhava node: house 7", "ok"])
def test_real_text_is_not_a_placeholder(v):
    assert ac.ldgr_placeholder_py(v) is False, v


def test_the_python_port_agrees_with_the_closed_list():
    for w in ac.LDGR_PLACEHOLDERS:
        assert ac.ldgr_placeholder_py(w) is True, w


# ───────────────────────── the writer scan ─────────────────────────

def _units(src: str, name: str = "w.py"):
    tree = ast.parse(src)
    return [dict(rel=name, path=pathlib.Path(name), tree=tree, nodes=[tree], hop=0, via=name)]


def _scan(src, entries=("citation_human",), table="t"):
    ws = ac._lint_module("writer_literal_scan")
    holders = {ac.parse_prose_field(e)[0]: [table] for e in entries}
    return ws.scan(_units(src), list(entries), holders, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts,
                   parse_entry=ac.parse_prose_field)


CLEAN = '''
SQL = """INSERT INTO t (chart_id, citation_human) VALUES (%(chart_id)s, %(citation_human)s)"""

def run(conn, chart_id, rows):
    for graha in rows:
        row = {"chart_id": chart_id, "citation_human": f"Graha node: {graha}"}
        conn.execute(SQL, row)
'''


def test_a_clean_writer_reads_pass_with_its_write_path_named():
    r = _scan(CLEAN)
    assert r["v"] == "PASS", r
    assert r["entries"]["citation_human"]["writes"] == 1 and r["files"] == ["w.py"] and not r["problems"] and not r["unresolved"]


def test_or_literal_fallback_is_a_named_problem():
    r = _scan(CLEAN.replace('f"Graha node: {graha}"', 'graha or "N/A"'))
    assert r["v"] == "PARTIAL" and r["problems"][0]["kind"] == "literal_fallback" and "N/A" in r["problems"][0]["text"], r


def test_dict_get_getattr_and_conditional_defaults_are_fallbacks():
    for expr in ('d.get("k", "none")', 'getattr(o, "a", "-")', 'x if x else "unknown"', 'x if x is not None else "no data here"'):
        r = _scan(CLEAN.replace('f"Graha node: {graha}"', expr))
        assert r["v"] == "PARTIAL" and any(p["kind"] in ("literal_fallback", "constant_write") for p in r["problems"]), (expr, r)


def test_a_constant_column_is_a_constant_write():
    r = _scan(CLEAN.replace('f"Graha node: {graha}"', '"Classical citation text"'))
    assert r["v"] == "PARTIAL" and r["problems"][0]["kind"] == "constant_write", r


def test_an_enumerated_label_choice_is_not_a_fallback():
    r = _scan(CLEAN.replace('f"Graha node: {graha}"', '"Bhava node" if graha else "Domain node"'))
    assert r["v"] == "PASS", r


def test_sql_literals_are_read():
    base = 'SQL = """INSERT INTO t (chart_id, citation_human) VALUES (%s, {})"""\n\ndef run(conn, c):\n    conn.execute(SQL, (c,))\n'
    assert _scan(base.format("'n/a'"))["v"] == "PARTIAL"
    assert _scan(base.format("COALESCE(NULL, 'none')"))["v"] == "PARTIAL"
    assert _scan(base.format("NULL"))["v"] == "PASS"


def test_positional_tuple_values_are_followed():
    src = 'SQL = "INSERT INTO t (chart_id, citation_human) VALUES (%s, %s)"\n\ndef run(conn, c, g):\n    conn.execute(SQL, (c, @@V@@))\n'
    assert _scan(src.replace("@@V@@", 'f"Graha node: {g}"'))["v"] == "PASS"
    r = _scan(src.replace("@@V@@", 'g or ""'))
    assert r["v"] == "PARTIAL" and r["problems"][0]["kind"] == "literal_fallback", r


def test_a_parameter_is_followed_to_its_callers():
    src = ('SQL = "INSERT INTO t (chart_id, citation_human) VALUES (%(chart_id)s, %(citation_human)s)"\n'
           'def put(conn, c, text):\n    conn.execute(SQL, {"chart_id": c, "citation_human": text})\n'
           'def run(conn, c, g):\n    put(conn, c, CALLER)\n')
    assert _scan(src.replace("CALLER", 'f"Graha node: {g}"'))["v"] == "PASS"
    assert _scan(src.replace("CALLER", 'g or "N/A"'))["v"] == "PARTIAL"
    nocaller = src.split("def run")[0]
    r = _scan(nocaller)
    assert r["v"] == "PARTIAL" and any("no caller" in u for u in r["unresolved"]), r


def test_unresolved_paths_are_never_clean():
    # no column list; a dynamic column list; no write at all; a dict comprehension that could supply the key
    assert _scan('SQL = "INSERT INTO t VALUES (%s)"\n')["v"] == "PARTIAL"
    assert _scan('def f(conn, cols):\n    conn.execute(f"INSERT INTO t ({cols}) VALUES (%s)", [1])\n')["v"] == "PARTIAL"
    assert _scan('def f():\n    return 1\n')["v"] == "PARTIAL"
    # a dict comprehension / variable-key store only matters when the key NAME is enumerable (a column list that could drive it)
    r = _scan(CLEAN + '\nCOLS = ["chart_id", "citation_human"]\n\ndef other(rows):\n    return {c: v for c, v in rows}\n')
    assert r["v"] == "PARTIAL" and any("dict comprehension" in u for u in r["unresolved"]), r
    assert _scan(CLEAN + '\ndef other(rows):\n    return {c: v for c, v in rows}\n')["v"] == "PASS"


def test_a_column_list_built_from_a_literal_list_is_resolved():
    src = ('COLS = ["chart_id", "citation_human"]\n\ndef f(conn, c, g):\n    ph = ", ".join(["%s"] * len(COLS))\n'
           '    sql = f"INSERT INTO t ({\', \'.join(COLS)}) VALUES ({ph})"\n    conn.execute(sql, [c, f"Graha {g}"])\n')
    r = _scan(src)
    assert not any("dynamic" in u for u in r["unresolved"]), r


def test_json_path_entries_scan_the_nested_leaf_key():
    src = ('SQL = "INSERT INTO t (chart_id, derivation) VALUES (%(chart_id)s, %(derivation)s)"\n'
           'def f(conn, c, whys):\n    for why in whys:\n        d = {"denials": [{"reason": REASON}]}\n        conn.execute(SQL, {"chart_id": c, "derivation": json.dumps(d)})\n')
    assert _scan(src.replace("REASON", 'f"No {why}"'), entries=("derivation.$.denials[*].reason",))["v"] == "PASS"
    assert _scan(src.replace("REASON", 'why or "unknown"'), entries=("derivation.$.denials[*].reason",))["v"] == "PARTIAL"


def test_a_real_asset_writer_resolves_its_dynamic_column_list():
    # ga_condition / ga_tajaka (real L1 writers) build `INSERT INTO t ({col_str})` from a literal column list: the Narr.agree reverse leg could not read them before
    for aid, wf, tabs, col in (("ga_condition", ["ga_condition.py"], ["ga_condition_composite", "chart_facts"], "citation_human"),
                               ("ga_tajaka", ["ga_tajaka.py"], ["l1_tajik_varsha_year_lords"], "citation_human")):
        units, _ = ac._delegation_scope(aid, wf)
        w = ac.written_columns(units, tabs)
        assert w is not None and any(col in cols for cols in w.values()), aid


# ───────────────────────── the Null PASS through prose_checks and the rollup ─────────────────────────

CITE = "platform/python-sidecar/pipeline/orchestrator/writers/ph_x.py:10"
GOOD = {"checkable": 5, "blank": 0}


def _ctx(src=CLEAN, **kw):
    base = dict(table="t", columns=["chart_id", "citation_human"], types={"chart_id": "text", "citation_human": "text"}, defaults={},
                counts={"citation_human": GOOD}, units=_units(src), beyond=[], paths=[], tests=[], vocabulary={"citation_human"}, written={})
    base.update(kw)
    return base


def _decl(pf=("citation_human",)):
    return {"prose_fields": list(pf), "evidence": {"prose_fields": CITE}}


def test_both_null_records_read_pass_when_data_and_writer_are_clean():
    got = ac.prose_checks("a", _decl(), _ctx())
    for c in NULL:
        assert got[c]["v"] == ac.PASS and got[c]["writer_scan"]["verified"] is True, (c, got[c])
        assert got[c]["writer_scan"]["paths_per_entry"] == {"citation_human": 1} and ac.writer_scan_problem(got[c]) is None
    cells = ac.rollup_asset("L2", {c: got[c] for c in NULL})
    assert cells["Null"]["v"] == ac.PASS
    assert all(ch.get("null_writer_scan_verified") is True for ch in cells["Null"]["checks"]), cells["Null"]


def test_a_dirty_writer_keeps_both_null_records_at_partial_and_names_the_finding():
    got = ac.prose_checks("a", _decl(), _ctx(CLEAN.replace('f"Graha node: {graha}"', 'graha or "N/A"')))
    for c in NULL:
        assert got[c]["v"] == ac.PARTIAL and "writer scan NOT clean" in got[c]["measured"] and "N/A" in got[c]["measured"], (c, got[c])
    assert ac.rollup_asset("L2", {c: got[c] for c in NULL})["Null"]["v"] == ac.PARTIAL


def test_a_data_level_blank_row_still_fails_whatever_the_writer_says():
    got = ac.prose_checks("a", _decl(), _ctx(counts={"citation_human": {"checkable": 5, "blank": 2}}))
    assert got["Null.blank_rows"]["v"] == ac.FAIL


def test_no_writer_source_leaves_the_records_exactly_as_the_graders_wrote_them():
    got = ac.prose_checks("a", _decl(), _ctx(units=[]))
    assert all(got[c]["v"] == ac.PARTIAL and "never PASS" in got[c]["measured"] for c in NULL)


def test_a_forged_or_one_sided_writer_scan_block_does_not_lift_the_cap():
    got = ac.prose_checks("a", _decl(), _ctx())
    ms = {c: got[c] for c in NULL}
    # one-sided
    one = dict(ms, **{"Null.blank_rows": dict(ms["Null.blank_rows"], v=ac.PARTIAL, writer_scan=None)})
    assert ac.rollup_asset("L2", one)["Null"]["v"] == ac.PARTIAL
    # a covered entry with no write path
    bad = {c: dict(r, writer_scan=dict(r["writer_scan"], paths_per_entry={"citation_human": 0})) for c, r in ms.items()}
    assert ac.rollup_asset("L2", bad)["Null"]["v"] == ac.PARTIAL
    # a record narrowing the claim below the declared prose fields
    facts = {"declared_prose_fields": ["citation_human", "other"]}
    assert ac.rollup_asset("L2", ms, facts)["Null"]["v"] == ac.PARTIAL
    # a basis on the record
    based = {c: dict(r, basis="declaration") for c, r in ms.items()}
    assert ac.rollup_asset("L2", based)["Null"]["v"] != ac.PASS
    # PASS verdict without the block
    nob = {c: {k: v for k, v in r.items() if k != "writer_scan"} for c, r in ms.items()}
    assert ac.rollup_asset("L2", nob)["Null"]["v"] == ac.PARTIAL


def test_the_declared_convention_path_is_untouched():
    assert ac.null_lift_earned("Null.blank_rows", None, {}) is False and ac._convention_lift_earned("Null.blank_rows", {}, {}) is False


# ───────────────────────── Narr.fidelity_test: the declared golden test ─────────────────────────

TESTPATH = SC / "pipeline" / "orchestrator" / "writers" / "tests" / "test_golden.py"
REF = "platform/python-sidecar/pipeline/orchestrator/writers/tests/test_golden.py::test_sentence"
HEAD = "from pipeline.orchestrator.writers.ph_x import build_narration\nimport pytest\n\n"
GOLD = HEAD + '''
def test_sentence():
    out = build_narration({"graha": "Sun", "sign": "Aries"})
    assert out["citation_human"] == "Sun is exalted in Aries by the Parashari rule"
'''


def _fid(src, covers=("citation_human",), entries=("citation_human",), ref=REF):
    decl = [dict(test=ref, covers=list(covers))]
    return ac.narr_fidelity_scan(list(entries), CITE, [(TESTPATH, src)], decl)


def test_a_golden_value_test_reads_pass_with_the_pinned_sentence_echoed():
    r = _fid(GOLD)
    assert r["v"] == ac.PASS, r
    g = r["golden"]
    assert g["verified"] is True and g["tests"][0]["test"] == REF and len(g["tests"][0]["expected_sha256"]) == 64 and g["tests"][0]["line"] == 7
    assert ac.fidelity_pass_problem(r) is None


def test_without_a_declaration_the_reading_stays_structural_and_never_pass():
    r = ac.narr_fidelity_scan(["citation_human"], CITE, [(TESTPATH, GOLD)])
    assert r["v"] == ac.PARTIAL and "golden" not in r


def test_the_expected_value_produced_by_the_builder_is_not_golden():
    r = _fid(HEAD + 'def test_sentence():\n    out = build_narration({"a": 1})\n    assert out["citation_human"] == build_narration({"a": 1})["citation_human"]\n')
    assert r["v"] == ac.PARTIAL and "golden" not in r and "not independent" in r["measured"], r


def test_a_structural_assert_is_not_golden():
    for body in ('assert out["citation_human"]', 'assert isinstance(out["citation_human"], str)', 'assert len(out["citation_human"]) > 0',
                 'assert "exalted" in out["citation_human"]', 'assert out["citation_human"].startswith("Sun")'):
        r = _fid(HEAD + f'def test_sentence():\n    out = build_narration({{"a": 1}})\n    {body}\n')
        assert r["v"] == ac.PARTIAL and "golden" not in r, (body, r)


def test_a_label_only_expected_literal_is_not_a_sentence():
    r = _fid(HEAD + 'def test_sentence():\n    out = build_narration({"a": 1})\n    assert out["citation_human"] == "high"\n')
    assert r["v"] == ac.PARTIAL and "no sentence" in r["measured"], r


def test_the_golden_assertion_must_reference_every_covered_entry():
    r = _fid(GOLD, covers=("citation_human", "mechanism_name"), entries=("citation_human", "mechanism_name"))
    assert r["v"] == ac.PARTIAL and "mechanism_name" in r["measured"], r


def test_every_declared_prose_entry_must_be_covered():
    r = _fid(GOLD, entries=("citation_human", "mechanism_name"))
    assert r["v"] == ac.PARTIAL and "NOT covered" in r["measured"] and "mechanism_name" in r["measured"], r


def test_a_declared_test_that_does_not_exist_or_is_skipped_or_does_not_call_the_builder_is_not_verified():
    assert _fid(GOLD, ref=REF.replace("test_sentence", "test_nope"))["v"] == ac.PARTIAL
    assert _fid(GOLD.replace("def test_sentence", "@pytest.mark.skip\ndef test_sentence"))["v"] != ac.PASS
    assert _fid(HEAD + 'def test_sentence():\n    assert "Sun is exalted in Aries" == "Sun is exalted in Aries"\n')["v"] != ac.PASS
    other = REF.replace("test_golden.py", "test_other.py")
    assert _fid(GOLD, ref=other)["v"] == ac.PARTIAL


def test_a_parametrized_literal_expected_value_is_golden():
    src = HEAD + ('@pytest.mark.parametrize("g,expected", [("Sun", "Sun is exalted in Aries"), ("Moon", "Moon is exalted in Taurus")])\n'
                  'def test_sentence(g, expected):\n    out = build_narration({"graha": g})\n    assert out["citation_human"] == expected\n')
    assert _fid(src)["v"] == ac.PASS
    bad = src.replace('"Moon is exalted in Taurus"', 'build_narration({"graha": "Moon"})["citation_human"]')
    assert _fid(bad)["v"] == ac.PARTIAL


def test_a_module_constant_literal_and_assertEqual_are_golden():
    src = HEAD + 'WANT = "Sun is exalted in Aries by rule"\n\ndef test_sentence():\n    out = build_narration({"a": 1})\n    assert out["citation_human"] == WANT\n'
    assert _fid(src)["v"] == ac.PASS
    src2 = HEAD + 'class TestX:\n    def test_sentence(self):\n        out = build_narration({"a": 1})\n        self.assertEqual(out["citation_human"], "Sun is exalted in Aries")\n'
    assert _fid(src2, ref=REF.replace("::test_sentence", "::TestX::test_sentence"))["v"] == ac.PASS


def test_the_rollup_honours_only_a_complete_golden_block():
    r = _fid(GOLD)
    cells = ac.rollup_asset("L2", {"Narr.fidelity_test": r})
    chk = {c["criterion"]: c for c in cells["Narr"]["checks"]}["Narr.fidelity_test"]
    assert chk["v"] == ac.PASS and chk.get("fidelity_golden_verified") is True
    forged = dict(r, golden=dict(r["golden"], tests=[dict(r["golden"]["tests"][0], expected_sha256="x")]))
    assert {c["criterion"]: c for c in ac.rollup_asset("L2", {"Narr.fidelity_test": forged})["Narr"]["checks"]}["Narr.fidelity_test"]["v"] == ac.PARTIAL
    nob = {k: v for k, v in r.items() if k != "golden"}
    assert {c["criterion"]: c for c in ac.rollup_asset("L2", {"Narr.fidelity_test": nob})["Narr"]["checks"]}["Narr.fidelity_test"]["v"] == ac.PARTIAL
    facts = {"declared_prose_fields": ["citation_human", "other"]}
    assert {c["criterion"]: c for c in ac.rollup_asset("L2", {"Narr.fidelity_test": r}, facts)["Narr"]["checks"]}["Narr.fidelity_test"]["v"] == ac.PARTIAL


def test_the_declaration_validator_refuses_a_malformed_fidelity_tests():
    base = {"kind": "data", "prose_fields": ["citation_human"], "evidence": {"prose_fields": CITE}}
    ok = dict(base, fidelity_tests=[dict(test=REF, covers=["citation_human"])])
    ac.validate_declarations({"version": "1", "kind_enum": list(ac.DECLARED_KINDS), "assets": {"a": ok}})
    bad = [
        dict(base, fidelity_tests=[]),
        dict(base, fidelity_tests=[dict(test="x.py::t", covers=["citation_human"])]),
        dict(base, fidelity_tests=[dict(test=REF, covers=["nope"])]),
        dict(base, fidelity_tests=[dict(test=REF, covers=[])]),
        dict(base, fidelity_tests=[dict(test=REF, covers=["citation_human"]), dict(test=REF, covers=["citation_human"])]),
        dict(base, fidelity_tests=[dict(test=REF, covers=["citation_human"], extra=1)]),
        dict(base, fidelity_tests=[dict(test="platform/python-sidecar/pipeline/ph_x.py::test_a", covers=["citation_human"])]),   # not a test path
        {"kind": "data", "prose_fields": None, "fidelity_tests": [dict(test=REF, covers=["citation_human"])]},
        {"kind": "data", "prose_fields": [], "evidence": {"prose_fields": CITE}, "fidelity_tests": [dict(test=REF, covers=["citation_human"])]},
    ]
    for e in bad:
        with pytest.raises(ac.DeclarationsError):
            ac.validate_declarations({"version": "1", "kind_enum": list(ac.DECLARED_KINDS), "assets": {"a": e}})


# ───────────────────────── count_sql scope (Narr.checkable / Null.blank_rows) on the REAL registry texts ─────────────────────────

MANIFEST = ac.ROOT / "00_ARCHITECTURE" / "control" / "NIRMANA_T0_MANIFEST_v1_1.json"


def _count_sql():
    return {a["asset_id"]: a["registry_contract"]["count_sql"] for a in json.loads(MANIFEST.read_text(encoding="utf-8"))["assets"]}


@pytest.mark.parametrize("aid,tables", [
    ("ga_panchanga", ["chart_facts"]), ("ga_sensitive", ["chart_facts"]), ("ga_strength", ["chart_facts"]),
    ("ga_condition", ["chart_facts", "ga_condition_composite"]), ("bo_anveshana", ["bodha_discoveries", "bodha_anomalies"]),
    ("bo_upaya", ["bodha_rm_resonances", "bodha_rm_remedy_prescriptions"]),
])
def test_the_real_count_sql_shapes_scope_each_counted_table_to_the_chart(aid, tables):
    sql = _count_sql()[aid]
    for t in tables:
        own = {t: (["chart_id"], None, None)}
        sc = ac._table_scope(t, {"count_sql": sql}, own, set())
        assert sc is not None and sc[1] == "chart-scoped by count_sql", (aid, t, sc)


def test_a_chart_facts_count_sql_with_a_depth0_or_is_still_an_upper_bound():
    own = {"chart_facts": (["chart_id"], None, None)}
    sc = ac._table_scope("chart_facts", {"count_sql": "SELECT count(*) FROM chart_facts WHERE chart_id = $1 OR fact_category = 'x'"}, own, set())
    assert sc[1] == ac.UPPER_BOUND
    assert ac._chart_pinned(" WHERE chart_id = $1 AND (a OR b)") and not ac._chart_pinned(" WHERE a = 1 OR chart_id = $1")
    assert not ac._chart_pinned(" WHERE chart_id = $10")


def test_a_sum_that_counts_a_table_twice_or_joins_cannot_be_scoped():
    assert ac._count_scope_tail("SELECT (SELECT count(*) FROM a WHERE chart_id=$1) + (SELECT count(*) FROM a WHERE chart_id=$1)", "a") is None
    assert ac._count_scope_tail(_count_sql()["ga_structural"], "chart_facts") is None


def test_narr_checkable_reads_pass_on_a_chart_scoped_real_shape():
    r = ac.grade_narr_checkable(["citation_human"], {"citation_human": dict(checkable=437, blank=0, scope="chart-scoped by count_sql")})
    assert r["v"] == ac.PASS


# ───────────────────────── the ELEVATED reader (tracker) and the certificate writer consume the earned PASS ─────────────────────────

def _tracker():
    from _e6_3_fixtures import load_tracker
    return load_tracker()


def _local_ref_run(driver_src):
    """What `_e63_ref_run` does at a ref, run against THIS checkout's census: the driver executes with the governance directory as cwd."""
    import subprocess

    def run(sha, files, driver, req, what, required):
        p = subprocess.run([sys.executable, "-c", driver], input=req.decode("utf-8"), capture_output=True, text=True, cwd=str(HERE.parent), timeout=120)
        assert p.returncode == 0, p.stderr
        return json.loads(p.stdout.strip().splitlines()[-1])
    return run


def _fid_world(monkeypatch, meas, entry):
    T = _tracker()
    head = dict(registry_revision=ac.REGISTRY_REVISION, registry_fingerprint=ac.registry_fingerprint())
    monkeypatch.setattr(T, "_e63_null_census_record", lambda repo, sha, rec: (head, dict(measurements={"Narr.fidelity_test": meas})))
    monkeypatch.setattr(T, "_e63_declared_entry", lambda repo, sha, asset: entry)
    monkeypatch.setattr(T, "_e63_ref_run", _local_ref_run(T._E63_FIDELITY_DRIVER))
    T._E63_FIDELITY_CACHE.clear()
    return T


def test_the_reader_counts_a_fidelity_pass_only_when_the_ref_census_earns_it_over_the_declared_tests(monkeypatch):
    r = _fid(GOLD)
    entry = {"kind": "data", "prose_fields": ["citation_human"], "evidence": {"prose_fields": CITE}, "fidelity_tests": [dict(test=REF, covers=["citation_human"])]}
    rec = dict(layer="L2", asset="a", criterion="Narr.fidelity_test", verdict="PASS", kind="gate", cert_id="a|gate|Narr.fidelity_test@1")
    T = _fid_world(monkeypatch, r, entry)
    assert T._e63_fidelity_earned("repo", "s" * 40, rec, b"") is True
    # the declaration at the ref names another test: the block no longer matches it
    T = _fid_world(monkeypatch, r, dict(entry, fidelity_tests=[dict(test=REF.replace("test_sentence", "test_other"), covers=["citation_human"])]))
    assert T._e63_fidelity_earned("repo", "s" * 40, rec, b"") is False
    # a PARTIAL record (no golden block) is never earned
    T = _fid_world(monkeypatch, {k: v for k, v in r.items() if k != "golden"}, entry)
    assert T._e63_fidelity_earned("repo", "s" * 40, rec, b"") is False


def test_the_certificate_writer_and_the_reader_share_the_census_predicate():
    import nikasha_certify as nc
    src = pathlib.Path(nc.__file__).read_text(encoding="utf-8")
    assert "ac.fidelity_pass_earned(meas)" in src and "ac.null_lift_earned(criterion, meas" in src


def test_the_reader_counts_a_writer_scan_null_pass_only_over_the_declared_prose_fields(monkeypatch):
    T = _tracker()
    got = ac.prose_checks("a", _decl(), _ctx())
    ms = {c: got[c] for c in NULL}
    head = dict(registry_revision=ac.REGISTRY_REVISION, registry_fingerprint=ac.registry_fingerprint())
    rec = dict(layer="L2", asset="a", criterion="Null.blank_rows", verdict="PASS", kind="gate", cert_id="a|gate|Null.blank_rows@1")
    monkeypatch.setattr(T, "_e63_null_census_record", lambda repo, sha, r: (head, dict(measurements=ms)))
    monkeypatch.setattr(T, "_e63_declared_null_convention", lambda repo, sha, a: None)
    monkeypatch.setattr(T, "_e63_ref_run", _local_ref_run(T._E63_NULL_DRIVER))
    monkeypatch.setattr(T, "_e63_declared_entry", lambda repo, sha, a: {"prose_fields": ["citation_human"]})
    T._E63_NULL_CACHE.clear()
    assert T._e63_null_lift_earned("repo", "s" * 40, rec, b"") is True
    T._E63_NULL_CACHE.clear()
    monkeypatch.setattr(T, "_e63_declared_entry", lambda repo, sha, a: {"prose_fields": ["citation_human", "other"]})
    assert T._e63_null_lift_earned("repo", "s" * 40, rec, b"") is False


def test_a_column_named_only_as_an_input_keyword_or_a_sibling_conjunct_is_not_covered():
    kw = HEAD + 'def test_sentence():\n    row = build_narration(citation_human="x")\n    assert row["fact_value_text"] == "Sun is exalted in Aries by rule"\n'
    r = _fid(kw)
    assert r["v"] == ac.PARTIAL and "not referenced" in r["measured"], r
    sib = HEAD + 'def test_sentence():\n    row = build_narration({"a": 1})\n    assert row["fact_value_text"] == "Sun is exalted in Aries by rule" and row["citation_human"] is not None\n'
    assert _fid(sib)["v"] == ac.PARTIAL


# ───────────────────────── review fixes, family 1: row lists that are mutated, and SELECT-sourced / expression writes ─────────────────────────

_EM = 'SQL = "INSERT INTO t (chart_id, citation_human) VALUES (%s, %s)"\n\n'


def test_review_high1_a_literal_row_list_that_is_appended_to_is_not_the_complete_row_set():
    bad = _EM + ('def run(conn, c, gs):\n    rows = []\n    for g in gs:\n        rows.append((c, g.get("t") or "N/A"))\n    conn.cursor().executemany(SQL, rows)\n')
    r = _scan(bad)
    assert r["v"] == "PARTIAL" and any("mutates" in u for u in r["unresolved"]), r
    for mut in ("rows.extend(more)", "rows += more", 'rows[0] = (c, "n/a")', "rows.insert(0, (c, 'x'))"):
        src = _EM + f'def run(conn, c, more):\n    rows = [(c, "Graha node: Sun")]\n    {mut}\n    conn.cursor().executemany(SQL, rows)\n'
        assert _scan(src)["v"] == "PARTIAL", mut
    assert _scan(_EM + 'def run(conn, c):\n    conn.cursor().executemany(SQL, [])\n')["v"] == "PARTIAL"
    assert _scan(_EM + 'def run(conn, c):\n    rows = []\n    conn.cursor().executemany(SQL, rows)\n')["v"] == "PARTIAL"
    good = _EM + 'def run(conn, c):\n    rows = [(c, "Graha node: Sun"), (c, "Graha node: Moon")]\n    conn.cursor().executemany(SQL, rows)\n'
    assert _scan(good)["v"] == "PASS" or _scan(good)["problems"]      # a clean literal list is read; its constant sentences are the reported problem, never silence


def test_review_high2_select_sourced_and_expression_writes_are_never_silently_clean():
    base = "INSERT INTO t (chart_id, citation_human) {}"
    for sql in (base.format("SELECT %s, s.x FROM staging s"), base.format("SELECT %s, s.x FROM (SELECT x FROM staging) s")):
        r = _scan(f'SQL = """{sql}"""\n\ndef run(conn, c):\n    conn.execute(SQL, (c,))\n')
        assert r["v"] == "PARTIAL" and any("another column" in u for u in r["unresolved"]), (sql, r)
    r = _scan('SQL = "UPDATE t SET citation_human = s.x FROM staging s WHERE t.id = s.id"\n\ndef run(conn):\n    conn.execute(SQL)\n')
    assert r["v"] == "PARTIAL" and r["unresolved"], r
    r = _scan('SQL = """INSERT INTO t (chart_id, citation_human) SELECT %s, q.txt FROM (SELECT COALESCE(a, \'n/a\') AS txt FROM staging) q"""\n\ndef run(conn, c):\n    conn.execute(SQL, (c,))\n')
    assert r["v"] == "PARTIAL" and any(p["kind"] == "literal_fallback" and "n/a" in p["text"] for p in r["problems"]), r
    r = _scan('SQL = "INSERT INTO t (chart_id, citation_human) VALUES (%s, lower(col))"\n\ndef run(conn, c):\n    conn.execute(SQL, (c,))\n')
    assert r["v"] == "PARTIAL" and r["unresolved"], r
    ok = _scan('SQL = "INSERT INTO t (chart_id, citation_human) VALUES (%s, %s) ON CONFLICT (chart_id) DO UPDATE SET citation_human = EXCLUDED.citation_human"\n\n'
               'def run(conn, c, gs):\n    for g in gs:\n        conn.execute(SQL, (c, f"Graha node: {g}"))\n')
    assert ok["v"] == "PASS", ok
