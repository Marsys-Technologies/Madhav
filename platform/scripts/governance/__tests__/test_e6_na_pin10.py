"""test_e6_na_pin10.py: REGISTRY_REVISION 10, SS N-72. Two rules declared on top of the six N-65 ones.

  S4  Build.dep_liveness#measured:no-declared-dependencies   (N-22 row 23 re-proposed): N/A only when the declared dependency list
      is EMPTY and the reads-match detector (the asset's own Build.dag) is PASS; else NO_DETECTOR, never N/A.
  NS  Earn.service_state#measured:not-a-service              (N-22 row 9): N/A only for a DECLARED kind that is not `service`
      (and that the registry does not call a service); services and undeclared kinds keep reading NO_DETECTOR.
Offline. The saved-census test skips when the evidence directory is absent (CI)."""
from __future__ import annotations

import collections
import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_a_na_causes as na_causes  # noqa: E402
import test_e6_na_r01_03 as r13  # noqa: E402

NA, NO_DET = ac.NA, ac.NO_DET
S4 = "Build.dep_liveness#measured:no-declared-dependencies"
NS = "Earn.service_state#measured:not-a-service"
NON_SERVICE_KINDS = ("data", "static", "view", "rider", "probe", "user_data")


def _na(cause, crit="Build.dep_liveness"):
    return dict(v=NA, measured="m", cause=cause)


def _check(cells, gate, crit):
    return next(c for c in cells[gate]["checks"] if c["criterion"] == crit)


# ───────────────────────── the declared rules ─────────────────────────

def test_the_two_pin10_rules_are_declared_with_their_decisions_and_the_cause_is_registered():
    assert {S4, NS} <= set(ac.NA_RULE_DECISIONS) and r13.PIN10_IDS == {S4, NS}
    assert "N-22" in ac.NA_RULE_DECISIONS[S4] and "N-72" in ac.NA_RULE_DECISIONS[S4] and "row 23" in ac.NA_RULE_DECISIONS[S4]
    assert "N-22" in ac.NA_RULE_DECISIONS[NS] and "N-72" in ac.NA_RULE_DECISIONS[NS] and "row 9" in ac.NA_RULE_DECISIONS[NS]
    assert "no-declared-dependencies" in ac.NA_CAUSES["Build.dep_liveness"]
    assert ac.NA_CAUSES["Earn.service_state"] == ("not-a-service",)
    ac.validate_na_rule_decisions()
    assert ac.REGISTRY_REVISION >= 10


# ───────────────────────── S4: the reads-match guard ─────────────────────────

def test_S4_empty_dependency_list_with_a_clean_dag_reads_na():
    rec = ac._grade_dep_liveness_none(dict(v=ac.PASS, measured="0 declared edge(s); ..."))
    assert rec["v"] == NA and rec["cause"] == "no-declared-dependencies"
    assert "reads-match" in rec["measured"]
    chk = _check(ac.rollup_asset("L0", {"Build.dep_liveness": rec}), "Build", "Build.dep_liveness")
    assert chk["v"] == NA and chk["rule_id"] == S4


def test_S4_a_ruled_bedrock_exempt_read_withholds_the_na_the_asset_consumes_another_assets_rows():
    rec = ac._grade_dep_liveness_none(dict(v=ac.PASS, bedrock_exempt=[dict(table="brahma_ontology")], measured="m"))
    assert rec["v"] == NO_DET and "cause" not in rec
    assert "brahma_ontology" in rec["measured"] and "bedrock exemption" in rec["measured"] and "not claimed" in rec["measured"]
    assert _check(ac.rollup_asset("L0", {"Build.dep_liveness": rec}), "Build", "Build.dep_liveness")["v"] == NO_DET


def test_S4_a_no_writer_asset_is_not_said_to_have_been_scanned():
    rec = ac._grade_dep_liveness_none(dict(v=ac.PASS, measured="no writer ..."), scanned=False)
    assert rec["v"] == NA and rec["cause"] == "no-declared-dependencies"
    assert "nothing to match" in rec["measured"] and "did not run" in rec["measured"] and "found no undeclared read" not in rec["measured"]
    scanned = ac._grade_dep_liveness_none(dict(v=ac.PASS, measured="m"), scanned=True)
    assert "found no undeclared read" in scanned["measured"]


def test_S4_a_co_registered_sibling_read_is_recorded_in_the_text_not_silently_skipped():
    rec = ac._grade_dep_liveness_none(dict(v=ac.PASS, co_registered_skipped=[dict(table="up_t", producers=["bg_up"])], measured="m"))
    assert rec["v"] == NA and "same writer class" in rec["measured"] and "up_t" in rec["measured"]


@pytest.mark.parametrize("dag", [
    None,                                                                                                      # dag not measured at all
    dict(v=ac.FAIL, missing_edges=[dict(table="t_other", kind="missing_edge")], measured="missing depends_on edge"),   # an undeclared read
    dict(v=ac.FAIL, missing_edges=[dict(kind="back_read")], measured="back-read"),
    dict(v=ac.PARTIAL, measured="parse incomplete"),
    dict(v=NO_DET, measured="not established: the parse is incomplete"),
    dict(v=ac.ERRORED, measured="check errored: reads-match scan failed"),
    dict(v=ac.PASS, missing_edges=[dict(table="t")], measured="inconsistent record: PASS with a finding"),
])
def test_S4_without_a_clean_reads_match_the_reading_is_no_detector_never_na(dag):
    rec = ac._grade_dep_liveness_none(dag)
    assert rec["v"] == NO_DET and "cause" not in rec and "did not establish" in rec["measured"]
    chk = _check(ac.rollup_asset("L0", {"Build.dep_liveness": rec}), "Build", "Build.dep_liveness")
    assert chk["v"] == NO_DET


def test_S4_cause_emitted_but_rule_not_declared_is_no_na(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {k: v for k, v in ac.NA_RULE_DECISIONS.items() if k != S4})
    chk = _check(ac.rollup_asset("L0", {"Build.dep_liveness": _na("no-declared-dependencies")}), "Build", "Build.dep_liveness")
    assert chk["v"] == NO_DET and "undecided" in chk["reason"]


def test_S4_measure_emits_na_for_a_clean_no_dependency_asset_and_leaves_a_dependent_asset_alone(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x"), "y": na_causes._reg_row("y", depends_on=["x"])}
    ms = na_causes._m(monkeypatch, tmp_path, reg, hist={"x": na_causes._h_unstarted(), "y": na_causes._h_unstarted()})
    assert ms["x"]["Build.dep_liveness"]["v"] == NA and ms["x"]["Build.dep_liveness"]["cause"] == "no-declared-dependencies"
    assert ms["y"]["Build.dep_liveness"]["v"] != NA and "cause" not in ms["y"]["Build.dep_liveness"]    # a non-empty list: graded as before


def test_S4_measure_says_nothing_to_match_for_a_no_writer_asset(monkeypatch, tmp_path):
    ms = na_causes._m(monkeypatch, tmp_path, {"x": na_causes._reg_row("x")}, hist={"y": na_causes._h_unstarted()})
    rec = ms["x"]["Build.dep_liveness"]
    assert rec["v"] == NA and "nothing to match" in rec["measured"] and "found no undeclared read" not in rec["measured"]


def test_S4_measure_withholds_the_na_when_the_asset_reads_an_undeclared_table(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x")}
    na_causes._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "_measure_dag", lambda *a, **k: dict(
        v=ac.FAIL, measured="missing depends_on edge: x -> y (reads t_y)", missing_edges=[dict(table="t_y", kind="missing_edge")]))
    m = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}["x"]
    assert m["Build.dag"]["v"] == ac.FAIL
    assert m["Build.dep_liveness"]["v"] == NO_DET and "cause" not in m["Build.dep_liveness"]
    assert ac.rollup_asset("L0", m)["Build"]["v"] == ac.FAIL                                              # the FAIL still holds the cell


def test_S4_measure_withholds_the_na_when_the_scan_is_unavailable(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x")}
    na_causes._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "_measure_dag", lambda *a, **k: dict(v=ac.ERRORED, measured="check errored: reads-match scan failed"))
    m = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}["x"]
    assert m["Build.dep_liveness"]["v"] == NO_DET


# ───────────────────────── S4 end to end: the REAL reads_scan on a fixture writer ─────────────────────────
import test_e6_gh_declared_service_and_reads_match as gh  # noqa: E402


def _full(monkeypatch, tmp_path, body, owners, depends_on=(), extra_rows=None):
    """measure() with a real fixture writer file for `ka_up` (the real reads_scan and _reads_clause run); returns its measurements."""
    gh._side(monkeypatch, tmp_path, body)
    reg = {"ka_up": na_causes._reg_row("ka_up", "kala_up", has_writer=True, count_sql="SELECT count(*) FROM kala_up", depends_on=depends_on),
           "bg_up": na_causes._reg_row("bg_up", "up_t", has_writer=True)}
    reg.update(extra_rows or {})
    na_causes._stub_layer(monkeypatch, tmp_path, reg, registered={"ka_up": ["ka_up.py"]},
                          hist={a: na_causes._h_unstarted() for a in reg})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    monkeypatch.setattr(ac, "produced_table_owners", lambda: dict(owners), raising=False)
    return next(a for a in ac.measure("L0")["assets"] if a["asset_id"] == "ka_up")["measurements"]


def test_S4_e2e_an_empty_dependency_asset_that_reads_another_assets_table_is_not_na(monkeypatch, tmp_path):
    m = _full(monkeypatch, tmp_path, gh.WRITER_READING, {"up_t": ["bg_up"], "kala_up": ["ka_up"]})
    assert m["Build.dag"]["v"] == ac.FAIL and "ka_up -> bg_up" in m["Build.dag"]["measured"]            # the real scan found the read
    assert m["Build.dep_liveness"]["v"] == NO_DET and "cause" not in m["Build.dep_liveness"]
    assert ac.rollup_asset("L0", m)["Build"]["v"] == ac.FAIL


def test_S4_e2e_a_clean_empty_dependency_asset_reads_na(monkeypatch, tmp_path):
    m = _full(monkeypatch, tmp_path, gh.WRITER_SILENT, {"kala_up": ["ka_up"]})
    assert m["Build.dag"]["v"] == ac.PASS
    assert m["Build.dep_liveness"]["v"] == NA and m["Build.dep_liveness"]["cause"] == "no-declared-dependencies"
    assert "found no undeclared read" in m["Build.dep_liveness"]["measured"]


def test_S4_e2e_the_same_read_with_a_declared_edge_is_graded_not_na(monkeypatch, tmp_path):
    m = _full(monkeypatch, tmp_path, gh.WRITER_READING, {"up_t": ["bg_up"], "kala_up": ["ka_up"]}, depends_on=("bg_up",))
    assert m["Build.dep_liveness"]["v"] != NA and "cause" not in m["Build.dep_liveness"]


def test_S4_e2e_a_ruled_bedrock_read_withholds_the_na(monkeypatch, tmp_path):
    bedrock = sorted(ac._dag_guard()._UNGATED_EXACT)[0]
    body = ('@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'
            f'        ctx.db_conn.execute("SELECT x FROM {bedrock}")\n')
    m = _full(monkeypatch, tmp_path, body, {bedrock: ["bg_up"], "kala_up": ["ka_up"]})
    assert m["Build.dag"]["v"] == ac.PASS and m["Build.dag"].get("bedrock_exempt"), m["Build.dag"]
    assert m["Build.dep_liveness"]["v"] == NO_DET and bedrock in m["Build.dep_liveness"]["measured"]


def test_S4_e2e_a_co_registered_read_is_recorded_in_build_dag_and_in_the_na_text(monkeypatch, tmp_path):
    body = gh.WRITER_READING.replace('@register("ka_up")', '@register("bg_up")\n@register("ka_up")')
    m = _full(monkeypatch, tmp_path, body, {"up_t": ["bg_up"], "kala_up": ["ka_up"]})
    assert m["Build.dag"]["v"] == ac.PASS
    assert m["Build.dag"]["co_registered_skipped"][0]["table"] == "up_t" and "same writer class" in m["Build.dag"]["measured"].lower()
    assert m["Build.dep_liveness"]["v"] == NA and "same writer class" in m["Build.dep_liveness"]["measured"]


def test_S4_a_build_cell_never_reads_na_from_this_rule_alone():
    cells = ac.rollup_asset("L0", {"Build.dep_liveness": _na("no-declared-dependencies"), "Build.dag": dict(v=ac.PASS, measured="m")})
    assert cells["Build"]["v"] == NO_DET and _check(cells, "Build", "Build.dep_liveness")["v"] == NA      # other Build checks unmeasured


def test_S4_ledger_closes_the_open_row_of_a_released_na_only(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    rows = [r13._row("bg_x", "Build.dep_liveness"), r13._row("bg_y", "Build.dep_liveness")]
    r13._ledger(tmp_path, rows)
    ac.emit_gaps(r13._census(bg_x={"Build.dep_liveness": _na("no-declared-dependencies")},
                             bg_y={"Build.dep_liveness": ac._grade_dep_liveness_none(dict(v=ac.FAIL, missing_edges=[1]))}))
    assert r13._closed(tmp_path) == ["bg_x-Build.dep_liveness"]


# ───────────────────────── NS: not-a-service keyed on the declared kind ─────────────────────────

@pytest.mark.parametrize("kind", NON_SERVICE_KINDS)
def test_NS_a_declared_non_service_kind_reads_na_not_a_service(kind):
    rec = ac._service_state_na(kind, "data")
    assert rec["v"] == NA and rec["cause"] == "not-a-service" and kind in rec["measured"]
    chk = _check(ac.rollup_asset("L0", {"Earn.service_state": rec}), "Earn", "Earn.service_state")
    assert chk["v"] == NA and chk["rule_id"] == NS


@pytest.mark.parametrize("declared, registry", [
    ("service", "service"), ("service", "data"),          # a declared service never reads N/A
    (None, "data"), (None, "service"), (None, ""),        # an undeclared / null kind never reads N/A (the census does not guess)
    ("data", "service"),                                  # the registry calls it a service: the disagreement is not resolved by N/A
    ("static", "service"),
])
def test_NS_services_undeclared_kinds_and_a_contradicting_registry_are_never_na(declared, registry):
    assert ac._service_state_na(declared, registry) is None


def test_NS_cause_emitted_but_rule_not_declared_is_no_na(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {k: v for k, v in ac.NA_RULE_DECISIONS.items() if k != NS})
    chk = _check(ac.rollup_asset("L0", {"Earn.service_state": ac._service_state_na("data", "data")}), "Earn", "Earn.service_state")
    assert chk["v"] == NO_DET and "undecided" in chk["reason"]


def test_NS_a_service_with_no_measurement_keeps_reading_no_detector():
    chk = _check(ac.rollup_asset("L0", {}, dict(asset_kind="service")), "Earn", "Earn.service_state")
    assert chk["v"] == NO_DET and chk["state"] == "APPLIES"


def test_NS_the_earn_cell_does_not_move_while_build_record_is_unmeasured():
    cells = ac.rollup_asset("L0", {"Earn.service_state": ac._service_state_na("data", "data")})
    assert cells["Earn"]["v"] == NO_DET and _check(cells, "Earn", "Earn.service_state")["v"] == NA


def test_NS_measure_emits_the_candidate_only_for_a_declared_non_service_kind(monkeypatch, tmp_path):
    reg = {"d": na_causes._reg_row("d", asset_kind="data"), "s": na_causes._reg_row("s", asset_kind="service"),
           "u": na_causes._reg_row("u", asset_kind="data"), "c": na_causes._reg_row("c", asset_kind="service")}
    decl = {"d": dict(kind="data"), "s": dict(kind="service"), "u": dict(kind=None), "c": dict(kind="data")}      # c: declared data, registry service
    na_causes._stub_layer(monkeypatch, tmp_path, reg)
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decl)
    monkeypatch.setattr(ac, "service_records", lambda layer: {})
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert ms["d"]["Earn.service_state"]["v"] == NA and ms["d"]["Earn.service_state"]["cause"] == "not-a-service"
    assert "Earn.service_state" not in ms["u"]
    for aid in ("s", "c"):      # E5.7: a registry service is now graded (here: no declared service_probe, so NO_DETECTOR naming it), never N/A
        assert ms[aid]["Earn.service_state"]["v"] == NO_DET and "service_probe" in ms[aid]["Earn.service_state"]["measured"], aid


def test_NS_with_the_real_declarations_file_119_assets_read_na_8_services_and_1_undeclared_do_not():
    kinds = {a: ac._declared_kind(ac.load_asset_declarations(), a) for a in ac.load_asset_declarations()}
    assert len(kinds) == 127                  # 127 snapshot assets + ga_fact_identity (kind data, 1.37.0) - bg_sarvatobhadra_grid (retired by migration 1360, declaration dropped at rev28b: kind static)
    na = [a for a, k in kinds.items() if ac._service_state_na(k, "data") is not None]
    svc = [a for a, k in kinds.items() if k == "service"]
    unk = [a for a, k in kinds.items() if k is None]
    assert (len(na), len(svc), len(unk)) == (118, 8, 1) and unk == ["mi_vistara"]      # (id kept; was 119 incl. the retired grid, now 118) the expectation includes mi_vistara, whose kind is undeclared


def test_NS_ledger_closes_an_open_earn_service_state_row_only_for_a_released_na(monkeypatch, tmp_path):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    r13._ledger(tmp_path, [r13._row("bg_x", "Earn.service_state"), r13._row("bg_s", "Earn.service_state")])
    ac.emit_gaps(r13._census(bg_x={"Earn.service_state": ac._service_state_na("data", "data")}, bg_s={}))
    assert r13._closed(tmp_path) == ["bg_x-Earn.service_state"]


# ───────────────────────── the saved Track A censuses: exactly ten gate cells move ─────────────────────────

EV = pathlib.Path("/Users/Dev/suvarna-evidence")
_EDGES = EV / "E6gh" / "reg_edges_reconstructed.json"
_SAVED = {L: EV / ("census2" if L in ("L1", "L2") else "census") / f"census_{L}.json" for L in ac.LAYERS}
saved = pytest.mark.skipif(not (_EDGES.exists() and all(p.exists() for p in _SAVED.values())),
                           reason="saved Track A census JSONs / reconstructed registry edges not on this machine")
MOVED_BUILD_PASS = ("bg_class_priors", "bg_dignity_reference", "bg_ghatana", "bg_kota_chakra_rings", "bg_nakshatra",
                    "bg_phaladeepika_latta", "bg_prashna_rules", "bg_vastu_directions", "bg_vedha_malefic_scale")


@saved
def test_saved_censuses_exactly_ten_gate_cells_move_and_no_cell_reads_na_or_lowers(monkeypatch):
    """Emission emulated with the REAL `_measure_dag` (reads-match) over the reconstructed registry edges (seed + migrations
    913/1084/730/676; they predate 1210 and later edges), then the real rollup with the six N-65 rules vs the eight."""
    import re
    census = {L: json.loads(_SAVED[L].read_text(encoding="utf-8"))[L] for L in ac.LAYERS}
    E = json.loads(_EDGES.read_text(encoding="utf-8"))
    assets = {a["asset_id"]: (L, a) for L, c in census.items() for a in c["assets"]}
    decls = ac.load_asset_declarations()
    rows = {}
    for aid, (L, a) in assets.items():
        ct = a.get("count_sql_tables") or []
        mk = re.search(r"asset_kind='(\w*)'", a["measurements"]["Build.target"]["measured"])
        rows[aid] = dict(asset_id=aid, has_writer=a["has_writer"], target_table=a["target_table"],
                         count_sql=("SELECT 1 FROM " + " JOIN ".join(ct)) if ct else "", depends_on=E[aid],
                         asset_kind=mk.group(1) if mk else "data")
    owners = ac.build_table_owners((aid, r["target_table"], r["count_sql"], r["has_writer"]) for aid, r in rows.items())
    prefix = {"L0": "bg_", "L1": "ga_", "L2": "bo_", "L3": "ka_", "L4": "ph_", "L5": "mi_"}
    att = {"Build.contract": "no-writer-registry-agrees", "Idem.pattern": "no-writer-registry-agrees", "Build.registered": "no-writer-registry-agrees",
           "Build.history": "never-run", "Build.dep_liveness": "no-declared-dependencies", "Count.floor": "target-floor-zero",
           "Build.count_integrity": "no-writer-no-count-sql"}
    M = {}
    for aid, (L, a) in assets.items():
        m = copy.deepcopy(a["measurements"])
        m.pop("Carr.detector", None)
        for k, r in m.items():
            if r["v"] == NA and "cause" not in r and k in att:
                r["cause"] = att[k]
        files = a.get("writer_files") or []
        m["Build.dag"] = ac._measure_dag(aid, rows[aid], files, set(rows), prefix[L], lambda: owners, E)
        if not E[aid]:
            m["Build.dep_liveness"] = ac._grade_dep_liveness_none(m["Build.dag"], scanned=bool(files))
        ss = ac._service_state_na(ac._declared_kind(decls, aid), rows[aid]["asset_kind"])
        if ss:
            m["Earn.service_state"] = ss
        M[aid] = m
    after = dict(ac.NA_RULE_DECISIONS)

    def cells(rules):
        monkeypatch.setattr(ac, "NA_RULE_DECISIONS", dict(rules))
        return {aid: ac.rollup_asset(assets[aid][0], M[aid], ac.facts_for_asset(assets[aid][1], decls)) for aid in assets}
    B = cells({k: v for k, v in after.items() if k not in r13.PIN10_IDS})
    A = cells(after)
    moves = sorted((aid, g, B[aid][g]["v"], A[aid][g]["v"]) for aid in assets for g in ac.CELL_GATES if B[aid][g]["v"] != A[aid][g]["v"])
    assert moves == sorted([(a, "Build", NO_DET, ac.PASS) for a in MOVED_BUILD_PASS] + [("mi_vistara", "Build", NO_DET, ac.PARTIAL)]), moves
    assert not [1 for aid in assets for g in ac.CELL_GATES if A[aid][g]["v"] == NA and B[aid][g]["v"] != NA]      # no cell reads N/A
    released = collections.Counter()
    for aid in assets:
        for g in ac.CELL_GATES:
            bc = {c["criterion"]: c for c in B[aid][g]["checks"]}
            for c in A[aid][g]["checks"]:
                if c["v"] == NA and bc[c["criterion"]]["v"] != NA:
                    released[c["criterion"]] += 1
                    assert (M[aid].get(c["criterion"]) or {}).get("v") == NA, (aid, c["criterion"])       # only a measured N/A is released
    # Earn.service_state was 118 when the saved censuses' bg_sarvatobhadra_grid still had a declared kind (static); the asset is retired (migration 1360), its declaration was dropped at rev28b, so its undeclared kind (None) is no longer released: 117.
    assert dict(released) == {"Build.dep_liveness": 28, "Earn.service_state": 117}, released
    assert not [aid for aid in assets if not E[aid] and M[aid]["Build.dep_liveness"]["v"] != NA]       # 28 no-dependency assets, none withheld there
