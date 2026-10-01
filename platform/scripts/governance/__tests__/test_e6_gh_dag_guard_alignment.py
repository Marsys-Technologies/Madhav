"""test_e6_gh_dag_guard_alignment.py — SS ruling 2026-10-01: the reads-match clause of Build.dag is aligned with the repo's
own `pipeline/orchestrator/dag_edge_guard.py`.

(1) A read of an L0 BEDROCK table (the guard's `_UNGATED_PREFIXES` / `_UNGATED_EXACT` / `_EXTERNAL_TABLES`: bg_, reference_,
    brahma_, sutravali_, classical_, ephemeris_daily, life_event*) is satisfied without a direct edge: no missing-edge FAIL.
    The read stays visible as `bedrock_exempt` in the record. PROVISIONAL interpretation of T4, to be confirmed at the J1
    review. The exemption list is the guard's own, imported, never a second list.
(2) A read of a SOFT shared table (`_SHARED_SOFT_TABLES` = chart_facts, a polymorphic multi-producer table) is satisfied by
    ANY producer in the asset's declared TRANSITIVE closure (the guard's SOFT treatment). No producer in the closure at all
    keeps the FAIL.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_a_na_causes as pa  # noqa: E402
import test_e6_gh_declared_service_and_reads_match as g  # noqa: E402
import test_e6_gh_review_corrections as rc  # noqa: E402


def _w(*tables):
    return rc._writer(*[f'ctx.db_conn.execute("SELECT x FROM {t}")' for t in tables])


GRAPH = {"ka_up": [], "bg_up": [], "bg_other": [], "ga_a": [], "ga_b": [], "mid": [], "bg_cp": []}


def _rows(**kw):
    return {"bg_cp": pa._reg_row("bg_cp", "brahma_class_priors", has_writer=True),
            "ga_a": pa._reg_row("ga_a", "chart_facts", has_writer=True), "ga_b": pa._reg_row("ga_b", "chart_facts", has_writer=True),
            "mid": pa._reg_row("mid", "mid_t", has_writer=True), **kw}


# ═════════════════════════ the exemption list is the guard's own ═════════════════════════

def test_the_exemption_rule_is_read_from_dag_edge_guard_not_hand_rolled(monkeypatch):
    guard = ac._dag_guard()
    assert guard.__file__.endswith("pipeline/orchestrator/dag_edge_guard.py") and "bg_" in guard._UNGATED_PREFIXES
    assert ac._is_bedrock("brahma_class_priors") and ac._is_bedrock("reference_signs") and ac._is_bedrock("ephemeris_daily")
    assert ac._is_bedrock("sutravali_rules") and ac._is_bedrock("classical_text_chunks") and ac._is_bedrock("bg_ghatana")
    assert ac._is_bedrock("life_events") and ac._is_bedrock("life_event_log"), "the guard's external ingest tables"
    assert not ac._is_bedrock("chart_facts") and not ac._is_bedrock("kala_convergence") and not ac._is_bedrock("up_t")
    monkeypatch.setattr(guard, "_UNGATED_PREFIXES", guard._UNGATED_PREFIXES + ("zz_",))
    assert ac._is_bedrock("zz_table"), "a prefix added to the guard's list is exempt here too: one list"
    monkeypatch.setattr(guard, "_UNGATED_EXACT", {"only_this"})
    assert ac._is_bedrock("only_this") and not ac._is_bedrock("ephemeris_daily")


def test_an_unloadable_guard_is_an_errored_check_not_a_silent_pass(monkeypatch, tmp_path):
    def boom():
        raise ac.Unknown("dag_edge_guard could not be loaded")
    monkeypatch.setattr(ac, "_dag_guard", boom)
    rec = g._dag(monkeypatch, tmp_path, _w("brahma_class_priors"), owners={"brahma_class_priors": ["bg_cp"]},
                 extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.ERRORED and "dag_edge_guard" in rec["measured"], rec


# ═════════════════════════ (1) bedrock reads ═════════════════════════

def test_a_bedrock_read_alone_is_satisfied_without_an_edge_and_recorded(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, _w("brahma_class_priors"), owners={"brahma_class_priors": ["bg_cp"]},
                 extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.PASS, rec
    f, = rec["bedrock_exempt"]
    assert f["table"] == "brahma_class_priors" and f["needs"] == "bg_cp" and f["file"] == "ka_up.py" and f["line"] == 5, f
    assert "missing_edges" not in rec
    txt = rec["measured"]
    assert "bedrock" in txt and "dag_edge_guard" in txt and "provisional" in txt and "J1" in txt, txt


def test_a_bedrock_read_plus_a_real_missing_edge_fails_naming_only_the_real_one(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, _w("brahma_class_priors", "up_t"),
                 owners={"brahma_class_priors": ["bg_cp"], "up_t": ["bg_up"]}, extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.FAIL, rec
    assert [f["table"] for f in rec["missing_edges"]] == ["up_t"], rec
    assert "brahma_class_priors" not in rec["measured"].split("reads-match:")[1].split("bedrock")[0], rec
    assert [f["table"] for f in rec["bedrock_exempt"]] == ["brahma_class_priors"], "the exempt read stays visible on a FAIL"


def test_a_bedrock_read_with_a_declared_edge_is_covered_not_exempt(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, _w("brahma_class_priors"), depends_on=("bg_cp",), owners={"brahma_class_priors": ["bg_cp"]},
                 extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.PASS and "bedrock_exempt" not in rec, rec
    assert "reads-match: 1 read(s) of other assets' tables" in rec["measured"], rec


def test_the_other_ungated_names_of_the_guard_are_exempt_too(monkeypatch, tmp_path):
    for i, tbl in enumerate(("reference_signs", "sutravali_rules", "classical_text_chunks", "ephemeris_daily")):
        rec = g._dag(monkeypatch, tmp_path / str(i), _w(tbl), owners={tbl: ["bg_cp"]}, extra_rows=_rows(), graph=GRAPH)
        assert rec["v"] == ac.PASS and rec["bedrock_exempt"][0]["table"] == tbl, (tbl, rec)


def test_a_non_bedrock_table_of_a_bg_asset_is_still_a_missing_edge(monkeypatch, tmp_path):
    # the rule is the TABLE's name (the guard's rule), not the producing asset's prefix
    rec = g._dag(monkeypatch, tmp_path, _w("up_t"), owners={"up_t": ["bg_up"]}, extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.FAIL and "bedrock_exempt" not in rec, rec


def test_a_bedrock_read_is_a_resolved_satisfied_read_but_does_not_hide_an_incomplete_parse(monkeypatch, tmp_path):
    body = rc._writer('ctx.db_conn.execute("SELECT x FROM brahma_class_priors")', 'ctx.db_conn.execute(f"SELECT 1 FROM {table}")')\
        .replace("def run(self, ctx)", "def run(self, ctx, table)")
    rec = g._dag(monkeypatch, tmp_path, body, owners={"brahma_class_priors": ["bg_cp"]}, extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.PARTIAL, rec          # one resolved read, satisfied; the dynamic table keeps it from PASS
    assert len(rec["bedrock_exempt"]) == 1 and "dynamic" in rec["measured"], rec


# ═════════════════════════ (2) chart_facts: the SOFT treatment ═════════════════════════

CF = {"chart_facts": ["ga_a", "ga_b"]}


def test_chart_facts_is_satisfied_by_any_producer_in_the_transitive_closure(monkeypatch, tmp_path):
    graph = {**GRAPH, "ka_up": ["mid"], "mid": ["ga_a"]}
    rec = g._dag(monkeypatch, tmp_path, _w("chart_facts"), depends_on=("mid",), owners=CF, extra_rows=_rows(), graph=graph)
    assert rec["v"] == ac.PASS and "missing_edges" not in rec, rec
    f, = rec["soft_satisfied"]
    assert f["table"] == "chart_facts" and f["via"] == ["ga_a"], f
    assert "chart_facts" in rec["measured"] and "SOFT" in rec["measured"], rec


def test_chart_facts_with_no_producer_in_the_closure_stays_a_fail(monkeypatch, tmp_path):
    graph = {**GRAPH, "ka_up": ["mid"], "mid": []}
    rec = g._dag(monkeypatch, tmp_path, _w("chart_facts"), depends_on=("mid",), owners=CF, extra_rows=_rows(), graph=graph)
    assert rec["v"] == ac.FAIL, rec
    f, = rec["missing_edges"]
    assert f["table"] == "chart_facts" and f["needs"] == "ga_a | ga_b" and f["kind"] == "missing_edge", f
    assert "soft_satisfied" not in rec


def test_chart_facts_with_no_edges_at_all_fails(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, _w("chart_facts"), owners=CF, extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.FAIL and rec["missing_edges"][0]["table"] == "chart_facts", rec


def test_a_direct_chart_facts_edge_is_covered_as_before(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, _w("chart_facts"), depends_on=("ga_b",), owners=CF, extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.PASS and "soft_satisfied" not in rec, rec


def test_the_soft_rule_is_only_for_the_guards_shared_tables(monkeypatch, tmp_path):
    # another multi-producer table is NOT soft: a producer in the closure does not satisfy it
    graph = {**GRAPH, "ka_up": ["mid"], "mid": ["ga_a"]}
    rec = g._dag(monkeypatch, tmp_path, _w("shared_t"), depends_on=("mid",), owners={"shared_t": ["ga_a", "ga_b"]},
                 extra_rows=_rows(), graph=graph)
    assert rec["v"] == ac.FAIL and rec["missing_edges"][0]["transitive_via"] == ["mid"], rec
    monkeypatch.setattr(ac._dag_guard(), "_SHARED_SOFT_TABLES", {"chart_facts", "shared_t"})
    rec = g._dag(monkeypatch, tmp_path / "s", _w("shared_t"), depends_on=("mid",), owners={"shared_t": ["ga_a", "ga_b"]},
                 extra_rows=_rows(), graph=graph)
    assert rec["v"] == ac.PASS, "the soft set is the guard's own"


def test_an_unreadable_graph_cannot_compute_a_closure_so_the_soft_rule_does_not_apply(monkeypatch, tmp_path):
    rec = rc._unreadable_graph(monkeypatch, tmp_path, _w("chart_facts"), deps=("mid",), owners=CF)
    assert rec["v"] != ac.PASS, rec


def test_the_soft_closure_is_the_asset_with_its_own_declared_edges(monkeypatch, tmp_path):
    # the registry graph is stale for ka_up; the asset's own depends_on carries the chain
    graph = {**GRAPH, "ka_up": [], "mid": ["ga_a"]}
    rec = g._dag(monkeypatch, tmp_path, _w("chart_facts"), depends_on=("mid",), owners=CF, extra_rows=_rows(), graph=graph)
    assert rec["v"] == ac.PASS, rec


def test_transitive_chart_facts_findings_no_longer_count_toward_transitive_only(monkeypatch, tmp_path):
    graph = {**GRAPH, "ka_up": ["mid"], "mid": ["ga_a", "bg_up"]}
    rows = {**_rows(), "mid": pa._reg_row("mid", "mid_t", has_writer=True, depends_on=("ga_a", "bg_up"))}
    rec = g._dag(monkeypatch, tmp_path, _w("chart_facts", "up_t"), depends_on=("mid",),
                 owners={**CF, "up_t": ["bg_up"]}, extra_rows=rows, graph=graph)
    assert rec["v"] == ac.FAIL and [f["table"] for f in rec["missing_edges"]] == ["up_t"] and rec["transitive_only"] is True, rec


# ═════════════════════════ final review (PR #2809): F1-F4, F6 ═════════════════════════

# F1: a bedrock NAME is exempt only when EVERY producer that owns the table is an L0 asset (bg_*). Stricter than the guard.

@pytest.mark.parametrize("table,owners", [("brahma_x", ["bo_x"]), ("reference_y", ["ka_z"]), ("brahma_mixed", ["bg_cp", "bo_x"]),
                                          ("sutravali_q", ["ph_a", "bg_cp"])])
def test_a_bedrock_named_table_with_any_non_l0_owner_is_not_exempt(monkeypatch, tmp_path, table, owners):
    rows = {**_rows(), **{o: pa._reg_row(o, f"{o}_t", has_writer=True) for o in owners if o not in ("bg_cp",)}}
    graph = {**GRAPH, **{o: [] for o in owners}}
    rec = g._dag(monkeypatch, tmp_path, _w(table), owners={table: owners}, extra_rows=rows, graph=graph)
    assert rec["v"] == ac.FAIL and "bedrock_exempt" not in rec, rec
    f, = rec["missing_edges"]
    assert f["table"] == table and f["bedrock_name_non_l0_owner"] is True and f["kind"] == "missing_edge", f
    assert "bedrock-named" in rec["measured"] or "bedrock_name_non_l0_owner" in rec["measured"], rec


def test_a_bedrock_named_table_owned_only_by_l0_assets_is_exempt_and_the_text_says_so(monkeypatch, tmp_path):
    rows = {**_rows(), "bg_two": pa._reg_row("bg_two", "bg_two_t", has_writer=True)}
    rec = g._dag(monkeypatch, tmp_path, _w("brahma_class_priors"), owners={"brahma_class_priors": ["bg_cp", "bg_two"]},
                 extra_rows=rows, graph={**GRAPH, "bg_two": []})
    assert rec["v"] == ac.PASS and rec["bedrock_exempt"][0]["table"] == "brahma_class_priors", rec
    assert "bedrock-named table(s) owned only by L0 assets" in rec["measured"], rec
    assert "dag_edge_guard exemption list" in rec["measured"] and "stricter" in rec["measured"], rec


def test_a_non_bedrock_name_is_never_exempt_whoever_owns_it(monkeypatch, tmp_path):
    rec = g._dag(monkeypatch, tmp_path, _w("up_t"), owners={"up_t": ["bg_up"]}, extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.FAIL and "bedrock_name_non_l0_owner" not in rec["missing_edges"][0], rec


# F2: soft_satisfied states its limit

def test_the_soft_satisfied_verdict_states_that_fact_category_is_not_matched(monkeypatch, tmp_path):
    graph = {**GRAPH, "ka_up": ["mid"], "mid": ["ga_a"]}
    rec = g._dag(monkeypatch, tmp_path, _w("chart_facts"), depends_on=("mid",), owners=CF, extra_rows=_rows(), graph=graph)
    assert rec["v"] == ac.PASS, rec
    assert "satisfied by ANY chart_facts producer in the declared closure" in rec["measured"], rec
    assert "fact_category is not matched" in rec["measured"] and "does not prove the READ category is produced upstream" in rec["measured"], rec
    assert all(sf["fact_category_matched"] is False for sf in rec["soft_satisfied"]), rec


# F3: soft-only reads plus an incomplete parse stay PARTIAL

def test_soft_only_reads_with_an_incomplete_parse_are_partial(monkeypatch, tmp_path):
    graph = {**GRAPH, "ka_up": ["mid"], "mid": ["ga_a"]}
    body = rc._writer('ctx.db_conn.execute("SELECT x FROM chart_facts")', 'ctx.db_conn.execute(f"SELECT 1 FROM {table}")')\
        .replace("def run(self, ctx)", "def run(self, ctx, table)")
    rec = g._dag(monkeypatch, tmp_path, body, depends_on=("mid",), owners=CF, extra_rows=_rows(), graph=graph)
    assert rec["v"] == ac.PARTIAL and len(rec["soft_satisfied"]) == 1 and "dynamic" in rec["measured"], rec


# F4: the loader's required-attribute check

def test_a_guard_missing_a_required_list_is_an_errored_check(monkeypatch, tmp_path):
    bad = tmp_path / "bad_guard.py"
    bad.write_text('_UNGATED_PREFIXES = ("bg_",)\n_UNGATED_EXACT = set()\n_EXTERNAL_TABLES = set()\n')   # no _SHARED_SOFT_TABLES
    monkeypatch.setattr(ac, "_DAG_GUARD_PATH", bad)
    monkeypatch.setattr(ac, "_DAG_GUARD", [])
    rec = g._dag(monkeypatch, tmp_path / "w", _w("chart_facts"), owners=CF, extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.ERRORED and "_SHARED_SOFT_TABLES" in rec["measured"], rec


def test_a_missing_guard_file_is_an_errored_check(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "_DAG_GUARD_PATH", tmp_path / "nope.py")
    monkeypatch.setattr(ac, "_DAG_GUARD", [])
    rec = g._dag(monkeypatch, tmp_path / "w", _w("brahma_class_priors"), owners={"brahma_class_priors": ["bg_cp"]},
                 extra_rows=_rows(), graph=GRAPH)
    assert rec["v"] == ac.ERRORED and "dag_edge_guard" in rec["measured"], rec


# F6: inconclusive survives a transitive_only FAIL; the declaration basis is case-exact

def test_inconclusive_is_carried_through_a_transitive_only_fail():
    rec = dict(v=ac.FAIL, measured="x", transitive_only=True, inconclusive=True)
    c = ac._check_contribution("Build.dag", "L3", rec, None)
    assert c["v"] == ac.FAIL and c.get("inconclusive") is True and "transitive" in c["reason"], c


def test_a_mis_cased_or_unknown_basis_is_rejected_explicitly():
    for basis in ("Declaration", "DECLARATION", "declared", ""):
        c = ac._check_contribution("Build.target", "L3", dict(v=ac.PASS, measured="x", basis=basis), None)
        assert c["v"] == ac.NO_DET and "basis" in c["reason"] and repr(basis) in c["reason"], (basis, c)
    ok = ac._check_contribution("Build.target", "L3", dict(v=ac.PASS, measured="x", basis="declaration"), None)
    assert ok["v"] == ac.PASS and ok["basis"] == "declaration"
