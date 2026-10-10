"""test_n430_views_logical_key.py: SS N-430 (part 1), a VIEW has no constraint to read a key from, and its passive writer writes nothing to count or replace.

bo_samvada is the registry identity of the view vw_chart_digest (GROUP BY chart_id, ayanamsha_id over bodha_msr_signals); its writer is a passive no-op. Three cells could not be read:
  Vocab.identity   -> the opt-in declaration `logical_key` {object, columns, basis group_by, why, evidence}, CHECKED: the object is a view that has the columns; a bounded pg_get_viewdef read shows ONE
                      top-level SELECT with a top-level GROUP BY of exactly those columns, each output under its own name (otherwise NO_DETECTOR, never PASS: a data probe alone cannot prove a key);
                      no NULL in a key column; no duplicate group (a duplicate is a FAIL); rows present;
  Idem.pattern / Build.count_integrity -> the opt-in declaration `passive_projection` {why, evidence}: N/A (new causes passive-projection / passive-projection-constant-count) only when the writer scope
                      (static_read machinery, executed DDL forbidden) writes nothing and the target is a live view.
No declaration = every cell measures exactly as before. Offline: fakes for the database reads, the real bo_samvada writer, synthetic writer trees. (The `test_live_pg_*` tests need a real PostgreSQL.)
"""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_w2_3_deeper_detectors as w3  # noqa: E402

NA, ND, FAIL, PARTIAL, PASS, ERRORED = ac.NA, ac.NO_DET, ac.FAIL, ac.PARTIAL, ac.PASS, ac.ERRORED
EV = "platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py:147"
LK = dict(object="vw_chart_digest", columns=["chart_id", "ayanamsha_id"], basis="group_by",
          why="the view is a GROUP BY of exactly chart_id and ayanamsha_id over the Bodha signals, so each pair is one row", evidence="platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py:131")
PP = dict(why="the asset is a read-only projection: the view definition is preserved and the writer runs no DDL or DML", evidence=EV)
SAMVADA = "bo_samvada"

# what pg_get_viewdef(oid, true) writes for the view (PostgreSQL's pretty form: columns qualified by the alias when the view joins or correlates a sub-select (a one-relation view is written unqualified, see VD_SINGLE), `AS` on every alias, a sub-select in parentheses, the GROUP BY last)
VD = """ SELECT m.chart_id,
    m.ayanamsha_id,
    count(DISTINCT m.signal_id) AS msr_signal_count,
    round(avg(m.computed_salience), 3) AS avg_salience,
    ( SELECT jsonb_agg(jsonb_build_object('domain', cv2.domain)) AS jsonb_agg
           FROM ( SELECT cv.domain
                   FROM bodha_convergence cv
                  WHERE cv.chart_id = m.chart_id
                  GROUP BY cv.domain
                  ORDER BY cv.domain
                 LIMIT 5) cv2) AS top_convergence_domains,
    now() AS digest_at
   FROM bodha_msr_signals m
  GROUP BY m.chart_id, m.ayanamsha_id;"""


# ───────────────────────── registry: the new causes and rules ─────────────────────────

def test_the_two_causes_and_their_rules_are_registered():
    assert "passive-projection" in ac.NA_CAUSES["Idem.pattern"] and "passive-projection-constant-count" in ac.NA_CAUSES["Build.count_integrity"]
    for rid in ("Idem.pattern#measured:passive-projection", "Build.count_integrity#measured:passive-projection-constant-count"):
        assert ac.NA_RULE_DECISIONS[rid].startswith("SS N-430") and "declaration-keyed" in ac.NA_RULE_DECISIONS[rid]
    ac.validate_na_rule_decisions()


# ───────────────────────── the declaration shapes ─────────────────────────

def _entry(**over):
    return dict(kind="view", logical_key=copy.deepcopy(LK), **over)


def test_a_sound_logical_key_is_accepted_and_only_bo_samvada_declares_one():
    assert ac.logical_key_problem(_entry()) is None and ac.logical_key_problem({}) is None
    committed = ac.load_asset_declarations()
    assert [a for a, e in committed.items() if e.get("logical_key") or e.get("passive_projection")] == [SAMVADA]       # SS N-431 declarations walk: the view's registry identity declares both (test_n431_gestalt_samvada_declared.py)


@pytest.mark.parametrize("mut", [
    lambda d: d.update(extra=1), lambda d: d.pop("why"), lambda d: d.update(object="vw bad"), lambda d: d.update(columns=[]), lambda d: d.update(columns=["a", "a"]),
    lambda d: d.update(columns=["a"] * 0 + [f"c{i}" for i in range(9)]), lambda d: d.update(columns=["a b"]), lambda d: d.update(columns="chart_id"), lambda d: d.update(basis="unique"),
    lambda d: d.update(why="short"), lambda d: d.update(why="the view groups the signals, tbd later on"), lambda d: d.update(evidence="unverified:the view was read"),
    lambda d: d.update(evidence="platform/python-sidecar/nope.py:1"), lambda d: d.update(evidence="platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py"),
    lambda d: d.update(evidence="platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py:99999")])
def test_a_malformed_logical_key_is_refused(mut):
    e = _entry()
    mut(e["logical_key"])
    assert ac.logical_key_problem(e)


def test_a_logical_key_needs_a_view_and_is_validated_with_the_declarations_file():
    assert ac.logical_key_problem(dict(kind="data", logical_key=LK))
    doc = json.loads((ac.Path(ac.__file__).parent / "asset_declarations.json").read_text(encoding="utf-8"))
    doc["assets"][SAMVADA]["logical_key"] = copy.deepcopy(LK)
    doc["assets"][SAMVADA]["passive_projection"] = copy.deepcopy(PP)
    assert SAMVADA in ac.validate_declarations(doc)
    for bad in (dict(LK, basis="unique"), dict(LK, columns=[])):
        d2 = copy.deepcopy(doc)
        d2["assets"][SAMVADA]["logical_key"] = bad
        with pytest.raises(ac.DeclarationsError, match="logical_key"):
            ac.validate_declarations(d2)
    d3 = copy.deepcopy(doc)
    d3["assets"][SAMVADA]["passive_projection"] = dict(PP, why="the writer runs nothing at all, a plain view")
    with pytest.raises(ac.DeclarationsError, match="projection"):
        ac.validate_declarations(d3)


@pytest.mark.parametrize("bad", ["text", dict(why="x"), dict(PP, extra=1), dict(PP, why="short"), dict(PP, why="the writer runs no statement and the view is preserved as it is"),
                                 dict(PP, evidence="unverified:the writer was read"), dict(PP, evidence="platform/python-sidecar/nope.py:1"),
                                 dict(PP, evidence="platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py")])
def test_a_malformed_passive_projection_is_refused(bad):
    assert ac.passive_projection_problem(dict(kind="view", passive_projection=bad))


def test_passive_projection_needs_a_view_and_stands_alone():
    assert ac.passive_projection_problem(dict(kind="view", passive_projection=PP)) is None and ac.passive_projection_problem({}) is None
    assert ac.passive_projection_problem(dict(kind="data", passive_projection=PP))
    assert "produced_tables" in ac.passive_projection_problem(dict(kind="view", passive_projection=PP, produced_tables=[dict(table="t")]))
    assert "update_only" in ac.passive_projection_problem(dict(kind="view", passive_projection=PP, update_only=dict(why="x", evidence=EV)))


# ───────────────────────── the view definition parser ─────────────────────────

def _proves(defn, cols=("chart_id", "ayanamsha_id")):
    return ac.viewdef_proves_key(ac.viewdef_group_by(defn), list(cols))


def test_the_pg_style_definition_proves_the_group_by_key_and_ignores_the_inner_group_by():
    r = ac.viewdef_group_by(VD)
    assert r["ok"] and r["group_by"] == [("m", "chart_id"), ("m", "ayanamsha_id")]                       # the sub-select's own GROUP BY cv.domain is not the view's
    assert r["exposed"]["chart_id"] == ("m", "chart_id") and "msr_signal_count" not in r["exposed"]            # only plain column references are exposed
    assert _proves(VD) is None
    assert "not the whole GROUP BY" in _proves(VD, ("chart_id",))
    assert "is not a GROUP BY column" in _proves(VD, ("chart_id", "ayanamsha_id", "digest_at"))


VD_SINGLE = """ SELECT chart_id,
    ayanamsha_id,
    count(DISTINCT signal_id) AS n
   FROM lk_src m
  GROUP BY chart_id, ayanamsha_id;"""                                                                         # what PostgreSQL's pretty form writes for a one-relation view: no alias on a column


def test_the_unqualified_single_relation_pretty_form_proves_the_same_key(monkeypatch):
    r = ac.viewdef_group_by(VD_SINGLE)
    assert r["ok"] and r["group_by"] == [(None, "chart_id"), (None, "ayanamsha_id")] and r["exposed"]["chart_id"] == (None, "chart_id")
    assert _proves(VD_SINGLE) is None and "not the whole GROUP BY" in _proves(VD_SINGLE, ("chart_id",))
    World(monkeypatch, defn=VD_SINGLE)
    res = _ident()
    assert res["v"] == PASS and res["logical_key"]["group_by"] == ["chart_id", "ayanamsha_id"]
    assert ac.logical_key_block_problem(res) is None                                                          # the block validator accepts the unqualified names too


def test_the_real_writers_view_statement_proves_the_same_key():
    import ast
    tree = ast.parse((ac.ROOT / "platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py").read_text(encoding="utf-8"))
    sql = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "_CREATE_VIEW_CLEAN" for t in n.targets))
    assert _proves(sql) is None                                                                          # the committed statement, read exactly like the live definition


@pytest.mark.parametrize("defn,needle", [
    (" SELECT m.chart_id, m.ayanamsha_id FROM t m;", "no single top-level GROUP BY"),
    (" SELECT m.chart_id, m.ayanamsha_id FROM (SELECT x.chart_id, x.ayanamsha_id FROM t x GROUP BY x.chart_id, x.ayanamsha_id) m;", "no single top-level GROUP BY"),
    (" SELECT m.chart_id, m.ayanamsha_id FROM t m GROUP BY date_trunc('day', m.chart_id), m.ayanamsha_id;", "not a plain column"),
    (" SELECT m.chart_id, m.ayanamsha_id FROM t m GROUP BY 1, 2;", "not a plain column"),
    (" SELECT m.chart_id, m.ayanamsha_id FROM t m GROUP BY ROLLUP (m.chart_id, m.ayanamsha_id);", "not a plain column"),
    (" SELECT m.chart_id, m.ayanamsha_id FROM t m GROUP BY GROUPING SETS ((m.chart_id), (m.ayanamsha_id));", "not a plain column"),
    (" SELECT m.chart_id, m.ayanamsha_id FROM t m GROUP BY m.chart_id, m.ayanamsha_id UNION SELECT a, b FROM u GROUP BY a, b;", "set operation"),
    (" SELECT m.chart_id, m.ayanamsha_id FROM t m GROUP BY m.chart_id, m.ayanamsha_id", None),
    (" SELECT DISTINCT ON (m.chart_id) m.chart_id, m.ayanamsha_id FROM t m GROUP BY m.chart_id, m.ayanamsha_id;", "DISTINCT ON"),
    (" SELECT m.chart_id FROM t m GROUP BY m.chart_id, m.ayanamsha_id;", "is not a GROUP BY column"),
    (" SELECT m.chart_id AS cid, m.ayanamsha_id FROM t m GROUP BY m.chart_id, m.ayanamsha_id;", "declared column chart_id is not a GROUP BY column"),
    (" SELECT a.id AS chart_id, b.id AS ayanamsha_id FROM a JOIN b ON true GROUP BY a.id;", "declared column ayanamsha_id is not a GROUP BY column"),
    (" SELECT b.id AS chart_id, a.k AS ayanamsha_id FROM a JOIN b ON true GROUP BY a.id, a.k;", "declared column chart_id is not a GROUP BY column"),
    (" SELECT a.id AS chart_id, a.id AS ayanamsha_id FROM a GROUP BY a.id, a.k;", "same GROUP BY column"),
    (" SELECT a.id AS chart_id, a.k AS ayanamsha_id FROM a GROUP BY a.id, a.k;", None),                       # an alias of a plain GROUP BY column is fine
    (" SELECT m.chart_id, m.ayanamsha_id FROM t m WHERE (m.x = 1 GROUP BY m.chart_id, m.ayanamsha_id;", "do not balance"),
])
def test_what_the_definition_does_not_prove_is_named(defn, needle):
    got = _proves(defn)
    if needle is None:
        assert got is None                                                                                   # a definition without the trailing semicolon reads the same
    else:
        assert got and needle in got, got


def test_comments_strings_and_clauses_after_the_group_by_do_not_move_the_reading():
    d = " SELECT m.chart_id, m.ayanamsha_id, 'GROUP BY z' AS note /* GROUP BY y */ FROM t m -- GROUP BY q\n GROUP BY m.chart_id, m.ayanamsha_id HAVING count(*) > 1 ORDER BY 1 LIMIT 3;"
    assert _proves(d) is None
    assert ac.viewdef_group_by(d)["group_by"] == [("m", "chart_id"), ("m", "ayanamsha_id")]
    q = ' SELECT "m"."Chart Id" AS "Chart Id", m.b FROM t "m" GROUP BY "m"."Chart Id", m.b;'
    assert ac.viewdef_proves_key(ac.viewdef_group_by(q), ["Chart Id", "b"]) is None


def test_a_cte_body_and_a_lateral_sub_select_are_not_the_views_own_group_by():
    d = " WITH c AS (SELECT x.chart_id FROM t x GROUP BY x.chart_id) SELECT c.chart_id, c.chart_id AS ayanamsha_id FROM c;"
    assert _proves(d) and "no single top-level GROUP BY" in _proves(d)


# ───────────────────────── the Vocab.identity reading, with the database reads faked ─────────────────────────

class World:
    """What the four live reads answer; every call is recorded."""
    def __init__(self, monkeypatch, defn=VD, dup=(False, "0 duplicate(s)"), null=False, rows=True, vd_error=None):
        self.calls = []
        self.defn, self.dup, self.null, self.rows, self.vd_error = defn, dup, null, rows, vd_error
        monkeypatch.setattr(ac, "identity_duplicates", lambda tbl, kd: (self.calls.append(("dup", tbl, kd)), self.dup)[1])
        monkeypatch.setattr(ac, "identity_has_rows", lambda tbl: (self.calls.append(("rows", tbl)), self.rows)[1])
        monkeypatch.setattr(ac, "scalar", lambda sql: (self.calls.append(("scalar", sql)), ("t" if self.null else "f") if "IS NULL" in sql else None)[1])
        monkeypatch.setattr(ac, "view_definition", self._vd)

    def _vd(self, view):
        self.calls.append(("viewdef", view))
        if self.vd_error:
            raise ac.Unknown(self.vd_error)
        return (self.defn, len(self.defn)) if self.defn is not None else (None, 0)


CAT = dict(views={"vw_chart_digest"}, cols={"vw_chart_digest": ["chart_id", "ayanamsha_id", "msr_signal_count"]})
DECL = dict(logical_key=LK)


def _ident(cat=CAT, decl=DECL, tbl="vw_chart_digest"):
    return ac.logical_key_identity(tbl, decl, cat)


def test_a_proven_group_by_key_with_no_duplicate_and_no_null_reads_pass_with_its_block(monkeypatch):
    w = World(monkeypatch)
    r = _ident()
    assert r["v"] == PASS and r["logical_key"]["group_by"] == ["m.chart_id", "m.ayanamsha_id"] and r["logical_key"]["duplicates"] == r["logical_key"]["null_keys"] == 0
    assert ac.logical_key_block_problem(r) is None
    assert ("dup", "vw_chart_digest", '"chart_id", "ayanamsha_id"') in w.calls and ("viewdef", "vw_chart_digest") in w.calls and ("rows", "vw_chart_digest") in w.calls
    nullsql = next(c[1] for c in w.calls if c[0] == "scalar" and "IS NULL" in c[1])
    assert '"chart_id" IS NULL OR "ayanamsha_id" IS NULL' in nullsql


def test_the_null_probe_is_chart_scoped(monkeypatch):
    w = World(monkeypatch)
    ac.set_read_scope({"vw_chart_digest": dict(where="chart_id = '482012f1-710e-4a25-994a-93821f5871aa'", label="measured chart")})
    try:
        _ident()
    finally:
        ac.set_read_scope(None)
    assert "(\"chart_id\" IS NULL OR \"ayanamsha_id\" IS NULL) AND (chart_id = '482012f1-710e-4a25-994a-93821f5871aa')" in next(c[1] for c in w.calls if c[0] == "scalar" and "IS NULL" in c[1])


def test_a_duplicate_group_reads_fail_and_a_null_key_reads_fail(monkeypatch):
    World(monkeypatch, dup=(True, "1 duplicate(s) in 1 duplicate group(s)"))
    r = _ident()
    assert r["v"] == FAIL and "1 duplicate(s)" in r["measured"] and "logical_key" not in r
    World(monkeypatch, null=True)
    r = _ident()
    assert r["v"] == FAIL and "NULL" in r["measured"]


@pytest.mark.parametrize("defn", [" SELECT m.chart_id, m.ayanamsha_id FROM t m;", " SELECT m.chart_id FROM t m GROUP BY m.chart_id;", None])
def test_clean_data_without_a_provable_group_by_never_reads_pass(monkeypatch, defn):
    World(monkeypatch, defn=defn)
    r = _ident()
    assert r["v"] == ND and "logical_key" not in r and ("a data probe alone cannot prove a key" in r["measured"] or "absent" in r["measured"])


def test_every_unproven_step_is_no_detector_and_a_failed_read_is_errored(monkeypatch):
    World(monkeypatch)
    assert _ident(tbl="other")["v"] == ND and "not the asset's target" in _ident(tbl="other")["measured"]
    assert _ident(cat=dict(CAT, views=set()))["v"] == ND and "not a view" in _ident(cat=dict(CAT, views=set()))["measured"]
    assert _ident(cat=dict(CAT, cols={"vw_chart_digest": ["chart_id"]}))["v"] == ND and "no column ayanamsha_id" in _ident(cat=dict(CAT, cols={"vw_chart_digest": ["chart_id"]}))["measured"]
    World(monkeypatch, rows=False)
    assert _ident()["v"] == ND and "vacuous" in _ident()["measured"]
    World(monkeypatch, defn="x" * (ac.VIEWDEF_MAX_CHARS + 1))
    assert _ident()["v"] == ND and "longer than" in _ident()["measured"]
    World(monkeypatch, vd_error="connection lost")
    assert _ident()["v"] == ERRORED


def test_the_view_definition_read_is_bounded_hex_and_chart_free(monkeypatch):
    seen = []
    text = "SELECT 1"
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: (seen.append(sql), [[str(len(text)), text.encode().hex()]])[1])
    assert ac.view_definition("vw_chart_digest") == (text, len(text))
    assert f"substr(d, 1, {ac.VIEWDEF_MAX_CHARS + 1})" in seen[0] and "pg_get_viewdef(to_regclass('public.vw_chart_digest'), true)" in seen[0] and "encode(" in seen[0]
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: [["0", ""]])
    assert ac.view_definition("vw_chart_digest") == (None, 0)
    with pytest.raises(ValueError):
        ac.view_definition("a; DROP TABLE x")


def test_the_rollup_honours_a_complete_block_and_refuses_a_forged_one(monkeypatch):
    World(monkeypatch)
    r = _ident()
    assert ac._check_contribution("Vocab.identity", "L2", r, None)["v"] == PASS
    for mut in (lambda b: b.update(duplicates=1), lambda b: b.update(null_keys=1), lambda b: b.update(rows_exist=False), lambda b: b.update(group_by=["m.chart_id"]),
                lambda b: b.update(basis="unique"), lambda b: b.update(declared=False), lambda b: b.update(viewdef_sha256="")):
        f = copy.deepcopy(r)
        mut(f["logical_key"])
        got = ac._check_contribution("Vocab.identity", "L2", f, None)
        assert got["v"] == ND and "logical-key PASS" in got["reason"]
    plain = dict(v=PASS, measured="declared key (id): 0 duplicate(s)")                                       # a record without the block is judged exactly as before
    assert ac._check_contribution("Vocab.identity", "L2", plain, None)["v"] == PASS


# ───────────────────────── the passive projection, on the real and on synthetic writers ─────────────────────────

def _cell(rollup, gate, crit):
    return next(c for c in rollup[gate]["checks"] if c["criterion"] == crit)["v"]


def _facts(aid, tables, is_view=True, const=True):
    return ac.passive_projection_facts(aid, ac.registered_ids("")[aid], tables, is_view, const)


def _declared(block):
    return dict(block, why=PP["why"], evidence=PP["evidence"])


def test_the_real_bo_samvada_writer_is_a_passive_projection():
    b = _facts(SAMVADA, ["vw_chart_digest"])
    assert b["written"] == b["update_only"] == b["delete_only"] == b["scan_hit"] == [] and b["writes_complete"] and b["scan_complete"] and b["target_is_view"]
    assert ac.passive_projection_scan_problem(b) is None and ac.passive_projection_scan_problem(b, "Build.count_integrity") is None
    r = ac._measure_idem(SAMVADA, ac.registered_ids("")[SAMVADA], "upsert", True, ["vw_chart_digest"], False, None, passive=_declared(b))
    assert r["v"] == NA and r["cause"] == "passive-projection" and r["passive_projection"]["written"] == [] and ac.passive_projection_na_problem("Idem.pattern", r) is None
    assert ac.rollup_asset("L2", {"Idem.pattern": r})["Idem"]["checks"][0]["v"] == NA
    assert ac._na_released("Idem.pattern", r)


def test_the_count_integrity_na_needs_a_constant_count_view():
    b = _declared(_facts(SAMVADA, ["vw_chart_digest"]))
    rec = dict(v=PARTIAL, measured="count_sql=yes, integrity_check_sql=yes — a constant count_sql cannot fail")
    r = ac.passive_count_integrity(rec, "count_sql=yes, integrity_check_sql=yes", b)
    assert r["v"] == NA and r["cause"] == "passive-projection-constant-count" and ac.passive_projection_na_problem("Build.count_integrity", r) is None
    assert _cell(ac.rollup_asset("L2", {"Build.count_integrity": r}), "Build", "Build.count_integrity") == NA
    assert ac._na_released("Build.count_integrity", r)
    r2 = ac.passive_count_integrity(rec, "x", dict(b, constant_count_view=False))
    assert r2["v"] == PARTIAL and r2["declaration_disagreements"] and "not applied" in r2["measured"]
    assert ac.passive_count_integrity(rec, "x", None) is rec                                                  # nothing declared: the PARTIAL, untouched


def test_without_the_declaration_the_cells_read_exactly_as_before():
    files = ac.registered_ids("")[SAMVADA]
    r = ac._measure_idem(SAMVADA, files, "upsert", True, ["vw_chart_digest"], False, None)
    assert r["v"] == PARTIAL and "no write to the asset's own table(s)" in r["measured"] and "passive_projection" not in r
    assert r == ac._measure_idem(SAMVADA, files, "upsert", True, ["vw_chart_digest"], False, None, passive=None)


@pytest.mark.parametrize("aid,tabs,needle", [("bg_text_index", ["classical_text_chunks"], "touches tables"), ("bo_laksana", ["bodha_msr_signals"], "not shown complete")])
def test_a_writer_that_writes_contradicts_the_declaration_on_the_real_writers(aid, tabs, needle):
    b = _declared(_facts(aid, tabs))
    r = ac._measure_idem(aid, ac.registered_ids("")[aid], "upsert", True, tabs, False, None, passive=b)
    assert r["v"] in (ND, FAIL), r
    if r["v"] == ND:
        assert r["declaration_disagreements"] and "contradicted" in r["measured"]
        assert ac.rollup_asset("L2", {"Idem.pattern": r})["Idem"]["checks"][0]["v"] == ND
    assert needle in (ac.passive_projection_scan_problem(b) or "")


CLS = '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'


def _synth(monkeypatch, tmp_path, body, is_view=True):
    w3._sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/ka_up.py": w3._HDR + body})
    b = ac.passive_projection_facts("ka_up", ["ka_up.py"], ["kala_up"], is_view, True)
    return b, ac._measure_idem("ka_up", ["ka_up.py"], "upsert", True, ["kala_up"], False, None, passive=_declared(b))


def test_synthetic_a_writer_that_executes_nothing_agrees(monkeypatch, tmp_path):
    b, r = _synth(monkeypatch, tmp_path, CLS + '        return None\n')
    assert ac.passive_projection_scan_problem(b) is None and r["v"] == NA and r["cause"] == "passive-projection"


def test_synthetic_a_view_statement_kept_as_a_constant_and_never_executed_agrees(monkeypatch, tmp_path):
    body = 'VIEW_SQL = "CREATE OR REPLACE VIEW kala_up AS SELECT 1 AS one"\n' + CLS + '        return None\n'
    b, r = _synth(monkeypatch, tmp_path, body)
    assert ac.passive_projection_scan_problem(b) is None and r["v"] == NA


@pytest.mark.parametrize("stmt,needle", [
    ('"CREATE OR REPLACE VIEW kala_up AS SELECT 1 AS one"', "DDL (CREATE)"), ('"DROP VIEW IF EXISTS kala_up"', "DDL (DROP)"), ('"ALTER TABLE kala_other ADD COLUMN x int"', "DDL (ALTER)"),
    ('"GRANT SELECT ON kala_up TO reader"', "DDL (GRANT)"), ('"INSERT INTO kala_other (a) VALUES (1)"', "touches tables"), ('"UPDATE kala_up SET a = 1"', "touches tables"),
    ('"DELETE FROM kala_other WHERE a = 1"', "touches tables"), ('"TRUNCATE kala_other"', "touches tables")])
def test_synthetic_any_executed_ddl_or_write_contradicts(monkeypatch, tmp_path, stmt, needle):
    b, r = _synth(monkeypatch, tmp_path, CLS + f'        ctx.db_conn.execute({stmt})\n')
    prob = ac.passive_projection_scan_problem(b)
    assert prob and (needle in prob or needle in (b["scan_why"] or "")), (prob, b)
    assert r["v"] in (ND, FAIL) and r.get("cause") is None


def test_synthetic_an_unreadable_statement_is_not_a_release(monkeypatch, tmp_path):
    b, r = _synth(monkeypatch, tmp_path, CLS + '        sql = ctx.sql\n        ctx.db_conn.execute(sql)\n')
    assert b["scan_complete"] is False and r["v"] == ND and "not shown complete" in r["measured"]


def test_synthetic_a_target_that_is_not_a_view_is_not_a_release(monkeypatch, tmp_path):
    b, r = _synth(monkeypatch, tmp_path, CLS + '        return None\n', is_view=False)
    assert r["v"] == ND and "not a view" in r["measured"]


def test_the_ddl_check_is_opt_in_the_static_scan_is_unchanged_without_it(monkeypatch, tmp_path):
    w3._sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/ka_up.py": w3._HDR + CLS + '        ctx.db_conn.execute("CREATE OR REPLACE VIEW kala_up AS SELECT 1 AS one")\n'})
    assert ac.static_write_scan("ka_up", ["ka_up.py"], ["kala_up"])["complete"] is True                      # default: DDL is not a write the static_read form looks for
    assert ac.static_write_scan("ka_up", ["ka_up.py"], ["kala_up"], forbid_ddl=True)["complete"] is False


def test_a_forged_passive_projection_release_is_refused_by_the_rollup():
    good = _facts(SAMVADA, ["vw_chart_digest"])
    base = dict(v=NA, cause="passive-projection", measured="m")
    assert ac.passive_projection_na_problem("Idem.pattern", base)                                              # no block at all
    for mut in (lambda b: b.update(written=["t"]), lambda b: b.update(scan_complete=False), lambda b: b.update(writes_complete=False), lambda b: b.update(target_is_view=False),
                lambda b: b.update(declared=False), lambda b: b.update(writer_files=[]), lambda b: b.update(scan_hit=["t"]), lambda b: b.update(update_only=["t"])):
        b = copy.deepcopy(good)
        mut(b)
        rec = dict(base, passive_projection=b)
        assert ac.passive_projection_na_problem("Idem.pattern", rec)
        assert ac.rollup_asset("L2", {"Idem.pattern": rec})["Idem"]["checks"][0]["v"] == ND
        assert not ac._na_released("Idem.pattern", rec)
    assert ac.passive_projection_na_problem("Idem.pattern", dict(base, passive_projection=good)) is None
    cnt = dict(v=NA, cause="passive-projection-constant-count", measured="m", passive_projection=dict(good, constant_count_view=False))
    assert ac.passive_projection_na_problem("Build.count_integrity", cnt)
    assert ac.passive_projection_na_problem("Idem.pattern", dict(base, cause="update-only-by-intent", passive_projection=good)) is None      # another cause: not this check's business
    assert ac.passive_projection_na_problem("Build.contract", dict(base, passive_projection=good)) is None


# ───────────────────────── real PostgreSQL (CI shard with a database; not run on a loaded workstation, SS N-436) ─────────────────────────

pgmod = pytest.importorskip("_disposable_pg")
disposable_pg = pgmod.disposable_pg


@pytest.fixture()
def pgview(disposable_pg, monkeypatch):
    import _formgap_support as fs
    pgmod.point_psql_at(disposable_pg, monkeypatch)
    for sql in ("DROP VIEW IF EXISTS vw_lk CASCADE", "DROP TABLE IF EXISTS lk_src CASCADE",
                "CREATE TABLE lk_src (chart_id uuid, ayanamsha_id text, signal_id int)",
                f"INSERT INTO lk_src VALUES ('{fs.CHART_A}', 'lahiri', 1), ('{fs.CHART_A}', 'lahiri', 2), ('{fs.CHART_A}', 'raman', 3), ('{fs.CHART_B}', 'lahiri', 4)",
                "CREATE VIEW vw_lk AS SELECT m.chart_id, m.ayanamsha_id, count(DISTINCT m.signal_id) AS n FROM lk_src m GROUP BY m.chart_id, m.ayanamsha_id",
                "CREATE VIEW vw_lk_nogroup AS SELECT DISTINCT m.chart_id, m.ayanamsha_id FROM lk_src m"):
        fs.psql(disposable_pg, sql)
    yield fs, disposable_pg
    ac.set_read_scope(None)
    for sql in ("DROP VIEW IF EXISTS vw_lk_nogroup", "DROP VIEW IF EXISTS vw_lk", "DROP TABLE IF EXISTS lk_src"):
        fs.psql(disposable_pg, sql)


def test_live_pg_the_real_pg_get_viewdef_proves_the_key_and_the_data_probes_run(pgview):
    fs, _pg = pgview
    cat = ac.catalog(["vw_lk", "vw_lk_nogroup"])
    ac.set_read_scope({"vw_lk": dict(where=f"chart_id = '{fs.CHART_A}'", label="measured chart")})
    decl = dict(logical_key=dict(LK, object="vw_lk"))
    r = ac.logical_key_identity("vw_lk", decl, cat)
    # pg_get_viewdef(oid, true) drops the table alias on a single-relation view (CI's PostgreSQL wrote `GROUP BY chart_id, ayanamsha_id`) and keeps it when a join or a correlated
    # sub-select needs it: what is proven is the COLUMNS, qualifier or not
    assert r["v"] == PASS and [g.rsplit(".", 1)[-1] for g in r["logical_key"]["group_by"]] == ["chart_id", "ayanamsha_id"], r
    ungrouped = dict(logical_key=dict(LK, object="vw_lk_nogroup"))
    r = ac.logical_key_identity("vw_lk_nogroup", ungrouped, cat)
    assert r["v"] == ND and "cannot prove a key" in r["measured"]                                             # the same columns, unique today by luck of the data: a data probe alone is not a proof


# ───────────────────────── measure() end to end on the offline harness: the three cells of a view asset ─────────────────────────

def _measure_view(monkeypatch, tmp_path, decl, **world):
    import test_ss_rd_service_static as rd
    real_regs = ac.registered_ids("")
    row = rd._row(SAMVADA, "data", has_writer=True, count_sql="SELECT 0 AS count", target_table="vw_chart_digest")
    row["has_integrity"] = True
    rd._stub(monkeypatch, tmp_path, {SAMVADA: row}, {SAMVADA: decl})
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {SAMVADA: real_regs[SAMVADA]})
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={"vw_chart_digest"}, cols={"vw_chart_digest": ["chart_id", "ayanamsha_id", "msr_signal_count"]}, keys={}, views={"vw_chart_digest"},
                                                      types=None, defaults=None, types_error="stub", udts=None))
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: 15 for x in r}, {}))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=15, full=list(c), never=[], note=""))
    World(monkeypatch, **world)
    return rd._cells(ac.measure("L2"), SAMVADA)


def test_measure_reads_the_three_cells_of_a_declared_view_asset(monkeypatch, tmp_path):
    decl = {"kind": "view", "logical_key": copy.deepcopy(LK), "passive_projection": copy.deepcopy(PP)}
    m = _measure_view(monkeypatch, tmp_path, decl)
    assert m["Vocab.identity"]["v"] == PASS and m["Vocab.identity"]["logical_key"]["columns"] == ["chart_id", "ayanamsha_id"], m["Vocab.identity"]
    assert m["Idem.pattern"]["v"] == NA and m["Idem.pattern"]["cause"] == "passive-projection", m["Idem.pattern"]
    assert m["Build.count_integrity"]["v"] == NA and m["Build.count_integrity"]["cause"] == "passive-projection-constant-count", m["Build.count_integrity"]
    roll = {c["criterion"]: c["v"] for g in ("Vocab", "Idem", "Build") for c in ac.rollup_asset("L2", m)[g]["checks"]}
    assert roll["Vocab.identity"] == PASS and roll["Idem.pattern"] == NA and roll["Build.count_integrity"] == NA


def test_measure_without_the_declarations_reads_the_three_cells_exactly_as_before(monkeypatch, tmp_path):
    m = _measure_view(monkeypatch, tmp_path, {"kind": "view"})
    assert "Vocab.identity" not in m or m["Vocab.identity"]["v"] == ND                                         # no keys, no declaration: unread, as before
    assert m["Idem.pattern"]["v"] == PARTIAL and "passive_projection" not in m["Idem.pattern"]
    assert m["Build.count_integrity"]["v"] == PARTIAL and "constant" in m["Build.count_integrity"]["measured"] and "passive_projection" not in m["Build.count_integrity"]


def test_measure_with_a_contradicted_declaration_reads_no_release(monkeypatch, tmp_path):
    decl = {"kind": "view", "logical_key": dict(LK, columns=["chart_id"]), "passive_projection": copy.deepcopy(PP)}
    m = _measure_view(monkeypatch, tmp_path, decl, defn=VD)
    assert m["Vocab.identity"]["v"] == ND and "not the whole GROUP BY" in m["Vocab.identity"]["measured"]
    m = _measure_view(monkeypatch, tmp_path, {"kind": "view", "passive_projection": copy.deepcopy(PP)}, dup=(True, "x"))
    assert m["Idem.pattern"]["v"] == NA                                                                        # the writer scan, not the data, decides the passive projection
