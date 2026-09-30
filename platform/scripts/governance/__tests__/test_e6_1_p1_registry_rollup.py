"""test_e6_1_p1_registry_rollup.py — E6.1 packet 1 (+ E6.2 rollup), Track E brief §8.

Covers: `layers` / `columns_any` / `asset_kinds` on EVERY CRITERION_REGISTRY entry; N/A decided by a
declared rule (never by absence); the worst-of rollup (FAIL > ERRORED > NO_DETECTOR > PARTIAL > PASS);
a gate with no checks = NO_DETECTOR; cells versioned with the registry revision; and a regression
fixture over all 127 assets' committed census cells (verdict-only compaction of census_L0..L5.json).
Pure functions only; no database.
"""
from __future__ import annotations

import inspect
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

FIXTURE = json.loads((HERE / "fixtures" / "census_cells_2026-09-30.json").read_text(encoding="utf-8"))
ALL_LAYERS = ("L0", "L1", "L2", "L3", "L4", "L5")

# Pinned registry content per revision. Changing ANY entry / rule / gate list without bumping
# REGISTRY_REVISION and adding the new pin here fails CI: the revision cannot lag the content.
PINNED_FINGERPRINTS = {
    1: "081076941ed6cec9abae08df5676e46e36c834764e84595f418f1155b701c909",
    # 2 (E6 packet a): measured-N/A rule ids are cause-keyed; NA_CAUSES joins the fingerprinted content
    2: "a0557b51341fdb5d86288b44ac459f1d19c6d9fd7f26eec15f28e8dbc05a99cf",
    # 3 (E6 review fix 2): Earn.build_record gains the cause no-registered-writer (healthy-non-execution narrowed)
    3: "7f30f61e123b473702eb37236b4c22628a5251ef7fd85a31cfb482ca304c6c5e",
    # 4 (E6.1 d): Dens.served revision 4 (contract AND a tier column in the served select; structural; cause no-served-surface)
    4: "220f839255b1c592f379a9e5923f0a34f31cda4241cb7e57e7448ca67d9e3274",
}


# ───────────────────────── registry shape ─────────────────────────

def test_every_entry_declares_layers_columns_any_and_asset_kinds_explicitly():
    for crit, e in ac.CRITERION_REGISTRY.items():
        for k in ("layers", "columns_any", "asset_kinds"):
            assert k in e, f"{crit} missing explicit key {k}"
        assert isinstance(e["layers"], tuple) and e["layers"], crit
        assert set(e["layers"]) <= set(ac.LAYERS), crit
        for k in ("columns_any", "asset_kinds"):
            assert e[k] is None or (isinstance(e[k], tuple) and e[k] and all(isinstance(x, str) for x in e[k])), (crit, k)


def test_layers_cover_every_layer_where_the_criterion_is_measured_today():
    """Narrowing `layers` below a measured layer would silently drop committed verdicts."""
    for layer, assets in FIXTURE["layers"].items():
        for aid, ms in assets.items():
            for crit in ms:
                assert crit in ac.CRITERION_REGISTRY, (aid, crit)
                assert layer in ac.CRITERION_REGISTRY[crit]["layers"], (layer, aid, crit)


def test_column_patterns_are_the_ones_measure_already_uses():
    assert ac.CRITERION_REGISTRY["Ldgr.source_presence"]["columns_any"] == ac.CITATION_COLUMNS
    assert ac.CITATION_COLUMNS == ("source_citation", "source_text_id", "classical_citation",
                                   "classical_citations", "citation_ref")
    assert ac.CRITERION_REGISTRY["Vocab.alias"]["columns_any"] == ("synonyms",)
    assert ac.CRITERION_REGISTRY["Earn.service_state"]["asset_kinds"] == ("service",)
    assert ac.ALIAS_COLUMN == "synonyms"
    assert ac.CRITERION_REGISTRY["Vocab.alias"]["columns_any"] == (ac.ALIAS_COLUMN,)


def test_alias_census_reads_the_shared_alias_column_constant(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "ALIAS_COLUMN", "aka")
    monkeypatch.setattr(ac, "psql", lambda sql, *a, **k: seen.append(sql) or [["(all)", "3", "1"]])
    assert ac.alias_census("t", ["id", "synonyms"]) is None          # the old literal is no longer the alias column
    assert ac.alias_census("t", ["id", "aka"]) == {"(all)": dict(rows=3, no_alias=1)}
    assert "aka IS NULL OR cardinality(aka)=0" in seen[0] and "synonyms" not in seen[0]


def _reg_row(aid, target_table=None):
    return dict(asset_id=aid, has_writer=False, target_table=target_table, count_sql="",
                has_integrity=False, depends_on=[], target_floor=None, catalog_status="", asset_kind="")


def _stub_layer(monkeypatch, ctrl, reg, tables):
    # same offline measure() harness as test_r60_ldgr_source_presence_singular_citation.py
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg),
                                                                    excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(tables),
                                                       cols={t: c for t, (c, _k) in tables.items()},
                                                       keys={t: k for t, (_c, k) in tables.items()}))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: None for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=48, full=list(c), never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)


def test_measure_selects_the_first_of_citation_columns_when_a_table_has_two(monkeypatch, tmp_path):
    """Behavioural pin (replaces a substring check on measure()'s source): with two citation columns
    present, measure() must probe the FIRST of CITATION_COLUMNS, the one the registry declares first."""
    first, later = ac.CITATION_COLUMNS[0], ac.CITATION_COLUMNS[3]
    assert first != later
    # column order in the table is the reverse of CITATION_COLUMNS' priority, so a positional pick would differ
    _stub_layer(monkeypatch, tmp_path, {"bg_two": _reg_row("bg_two", "bg_two")},
                {"bg_two": (["id", later, first], [])})
    seen = []

    def fake_psql(sql, sep="\x1f", timeout=None):
        seen.append(sql)
        if "count(*)::text FROM bg_two WHERE" in sql:
            return [["48"]]
        raise AssertionError(f"unexpected query: {sql[:100]}")

    monkeypatch.setattr(ac, "psql", fake_psql)
    census = ac.measure("L0")
    res = next(a for a in census["assets"] if a["asset_id"] == "bg_two")["measurements"]["Ldgr.source_presence"]
    assert res == dict(v=ac.PASS, measured=f"{first} populated on 48/48 rows")
    cit_sql = [q for q in seen if "IS NOT NULL" in q]
    assert cit_sql == [f"SELECT count(*)::text FROM bg_two WHERE {first} IS NOT NULL"]


# ───────────────────────── applicability ─────────────────────────

def test_applicability_layer_columns_kind_and_unknown_are_distinct_states():
    f = ac.criterion_applicability
    assert f("Build.dag", "L2", None)["state"] == "APPLIES"
    # column pattern: facts absent -> UNKNOWN, never NOT_APPLICABLE
    assert f("Ldgr.source_presence", "L1", None)["state"] == "UNKNOWN"
    assert f("Ldgr.source_presence", "L1", {})["state"] == "UNKNOWN"
    assert f("Ldgr.source_presence", "L1", {"columns": ["id", "x"]})["state"] == "NOT_APPLICABLE"
    assert f("Ldgr.source_presence", "L1", {"columns": ["id", "classical_citation"]})["state"] == "APPLIES"
    assert f("Ldgr.source_presence", "L1", {"columns": []})["state"] == "UNKNOWN"
    assert f("Earn.service_state", "L3", None)["state"] == "UNKNOWN"
    assert f("Earn.service_state", "L3", {"asset_kind": "data"})["state"] == "NOT_APPLICABLE"
    assert f("Earn.service_state", "L3", {"asset_kind": "service"})["state"] == "APPLIES"
    # NOT_APPLICABLE dominates UNKNOWN when one fact disproves and the other is missing
    assert f("Earn.service_state", "L3", {"asset_kind": "data"})["rule_id"] == "Earn.service_state#asset_kinds"
    assert f("Ldgr.source_presence", "L1", {"columns": ["id"]})["rule_id"] == "Ldgr.source_presence#columns_any"


@pytest.mark.parametrize("bad_columns", [[], (), set(), "abc", "source_citation", 7, ["id", 3], {"columns": 1}])
def test_a_malformed_or_empty_columns_fact_is_not_evidence(bad_columns):
    """An empty list or a wrong-typed value is not a supplied fact: UNKNOWN, never NOT_APPLICABLE
    (and never APPLIES from a bare string whose substring matches)."""
    for layer in ("L1", "L0"):
        assert ac.criterion_applicability("Ldgr.source_presence", layer, {"columns": bad_columns})["state"] == "UNKNOWN"
    assert ac.rollup_asset("L1", {}, {"columns": bad_columns})["Ldgr"]["v"] != "N/A"


@pytest.mark.parametrize("bad_kind", ["", 3, None, ["service"], b"service"])
def test_a_malformed_or_empty_asset_kind_fact_is_not_evidence(bad_kind):
    assert ac.criterion_applicability("Earn.service_state", "L3", {"asset_kind": bad_kind})["state"] == "UNKNOWN"


def test_columns_known_true_makes_an_empty_column_list_evidence():
    f = ac.criterion_applicability
    r = f("Ldgr.source_presence", "L1", {"columns": [], "columns_known": True})
    assert r["state"] == "NOT_APPLICABLE" and r["rule_id"] == "Ldgr.source_presence#columns_any"
    # columns_known must be exactly True, and only relaxes the emptiness rule, not the type rule
    assert f("Ldgr.source_presence", "L1", {"columns": [], "columns_known": 1})["state"] == "UNKNOWN"
    assert f("Ldgr.source_presence", "L1", {"columns": "abc", "columns_known": True})["state"] == "UNKNOWN"
    assert f("Ldgr.source_presence", "L1", {"columns": ("id",), "columns_known": True})["state"] == "NOT_APPLICABLE"


def test_unknown_layer_raises_keyerror():
    with pytest.raises(KeyError):
        ac.criterion_applicability("Build.dag", "L9", None)
    with pytest.raises(KeyError):
        ac.criterion_applicability("Ldgr.source_presence", "", {"columns": ["id"]})


def test_out_of_layer_when_layer_not_declared(monkeypatch):
    reg = dict(ac.CRITERION_REGISTRY)
    reg["Build.dag"] = dict(reg["Build.dag"], layers=("L0",))
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    assert ac.criterion_applicability("Build.dag", "L2", None)["state"] == "OUT_OF_LAYER"
    assert ac.criterion_applicability("Build.dag", "L0", None)["state"] == "APPLIES"


def test_unregistered_criterion_raises():
    with pytest.raises(KeyError):
        ac.criterion_applicability("Nope.nope", "L0", None)


# ───────────────────────── rollup_verdicts ─────────────────────────

@pytest.mark.parametrize("vs,want", [
    (["PASS", "PASS"], "PASS"),
    (["PASS", "PARTIAL"], "PARTIAL"),
    (["PARTIAL", "NO_DETECTOR"], "NO_DETECTOR"),
    (["NO_DETECTOR", "ERRORED"], "ERRORED"),
    (["ERRORED", "FAIL", "PASS"], "FAIL"),
    (["FAIL", "N/A"], "FAIL"),
    (["PASS", "N/A"], "PASS"),
    (["N/A", "N/A"], "N/A"),
    ([], "NO_DETECTOR"),
])
def test_rollup_verdicts_worst_wins(vs, want):
    assert ac.rollup_verdicts(vs) == want
    assert ac.rollup_verdicts(list(reversed(vs))) == want


def test_rollup_order_constant():
    assert ac.ROLLUP_ORDER == ("FAIL", "ERRORED", "NO_DETECTOR", "PARTIAL", "PASS")


def test_rollup_verdicts_accepts_any_iterable_and_does_not_drain_it():
    assert ac.rollup_verdicts(iter(["FAIL"])) == "FAIL"
    assert ac.rollup_verdicts(("FAIL",)) == "FAIL"
    assert ac.rollup_verdicts(v for v in ["PASS", "PARTIAL"]) == "PARTIAL"
    assert ac.rollup_verdicts(iter([])) == "NO_DETECTOR"


def test_rollup_verdicts_rejects_a_bare_string():
    for bare in ("FAIL", "PASS", "N/A", ""):
        with pytest.raises(TypeError):
            ac.rollup_verdicts(bare)


@pytest.mark.parametrize("bad", ["NOT_GENERIC", "UNKNOWN", "pass", "", None])
def test_rollup_verdicts_rejects_a_verdict_outside_the_closed_set(bad):
    with pytest.raises(ValueError):
        ac.rollup_verdicts(["PASS", bad])


# ───────────────────────── rollup_asset ─────────────────────────

def _m(v, measured="x"):
    return dict(v=v, measured=measured)


def test_gate_with_no_registered_check_is_no_detector():
    cells = ac.rollup_asset("L2", {})
    assert set(cells) == set(ac.CELL_GATES)
    for g in ("Null", "Narr"):
        assert cells[g]["v"] == "NO_DETECTOR"
        assert cells[g]["checks"] == []


def test_all_pass_measurements_do_not_make_a_gate_pass_while_an_applicable_check_is_unmeasured():
    # Build: every Build.* criterion measured PASS -> PASS
    ms = {c: _m("PASS") for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Build"}
    assert ac.rollup_asset("L2", ms)["Build"]["v"] == "PASS"
    # drop one applicable check: it is NOT dropped from the gate, it reads NO_DETECTOR
    ms.pop("Build.dag")
    cell = ac.rollup_asset("L2", ms)["Build"]
    assert cell["v"] == "NO_DETECTOR"
    chk = next(c for c in cell["checks"] if c["criterion"] == "Build.dag")
    assert chk["v"] == "NO_DETECTOR" and "not measured" in chk["reason"]


def test_worst_measured_verdict_wins_in_a_gate():
    ms = {c: _m("PASS") for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Build"}
    ms["Build.completion"] = _m("PARTIAL")
    assert ac.rollup_asset("L2", ms)["Build"]["v"] == "PARTIAL"
    ms["Build.history"] = _m("FAIL")
    assert ac.rollup_asset("L2", ms)["Build"]["v"] == "FAIL"
    ms["Build.contract"] = _m("ERRORED")
    assert ac.rollup_asset("L2", ms)["Build"]["v"] == "FAIL"


def test_measured_na_is_not_na_without_a_declared_rule_and_is_na_with_one(monkeypatch):
    ms = {c: _m("PASS") for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Build"}
    ms["Build.registered"] = dict(_m("N/A"), cause="no-writer-registry-agrees")    # E6 (a): N/A carries a cause
    cell = ac.rollup_asset("L2", ms)["Build"]
    assert cell["v"] == "NO_DETECTOR"
    chk = next(c for c in cell["checks"] if c["criterion"] == "Build.registered")
    assert chk["v"] == "NO_DETECTOR" and "N/A rule undecided" in chk["reason"]
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.registered#measured:no-writer-registry-agrees": "N-22/test"})
    cell = ac.rollup_asset("L2", ms)["Build"]
    assert cell["v"] == "PASS"
    chk = next(c for c in cell["checks"] if c["criterion"] == "Build.registered")
    assert chk["v"] == "N/A" and chk["decision"] == "N-22/test"


def test_a_gate_is_na_only_when_every_check_is_na_by_declared_rule(monkeypatch):
    crits = [c for c, e in ac.CRITERION_REGISTRY.items() if e["gate"] == "Idem"]
    ms = {c: dict(_m("N/A"), cause="no-writer-registry-agrees") for c in crits}
    assert ac.rollup_asset("L2", ms)["Idem"]["v"] == "NO_DETECTOR"
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {f"{c}#measured:no-writer-registry-agrees": "N-22/test" for c in crits})
    assert ac.rollup_asset("L2", ms)["Idem"]["v"] == "N/A"


def test_not_applicable_by_supplied_fact_needs_a_declared_rule(monkeypatch):
    ms = {"Ldgr.source_presence": None}
    ms = {}
    facts = {"columns": ["id"]}
    cell = ac.rollup_asset("L1", ms, facts)["Ldgr"]
    assert cell["v"] == "NO_DETECTOR"
    assert cell["checks"][0]["state"] == "NOT_APPLICABLE" and "N/A rule undecided" in cell["checks"][0]["reason"]
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Ldgr.source_presence#columns_any": "N-22/test"})
    assert ac.rollup_asset("L1", ms, facts)["Ldgr"]["v"] == "N/A"


def test_absent_facts_never_yield_na_even_with_a_declared_rule(monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Ldgr.source_presence#columns_any": "N-22/test"})
    cell = ac.rollup_asset("L1", {}, None)["Ldgr"]
    assert cell["v"] == "NO_DETECTOR"
    assert cell["checks"][0]["state"] == "UNKNOWN"


def test_detector_none_criterion_never_reaches_pass():
    # Carr.D1 is detector NONE; even if some caller hands it a PASS it is capped.
    ms = {"Carr.detector": _m("PASS"), "Carr.D1": _m("PASS"), "Carr.D2": _m("PASS"), "Carr.D3": _m("PASS")}
    cell = ac.rollup_asset("L2", ms)["Carr"]
    assert cell["v"] == "NO_DETECTOR"
    d1 = next(c for c in cell["checks"] if c["criterion"] == "Carr.D1")
    assert d1["v"] == "NO_DETECTOR" and "detector NONE" in d1["reason"]


def test_measured_criterion_outside_its_layers_raises_never_dropped(monkeypatch):
    reg = dict(ac.CRITERION_REGISTRY)
    reg["Build.dag"] = dict(reg["Build.dag"], layers=("L0",))
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    with pytest.raises(ValueError):
        ac.rollup_asset("L2", {"Build.dag": _m("FAIL")})


def test_unregistered_or_ungradable_measurement_raises():
    with pytest.raises(KeyError):
        ac.rollup_asset("L2", {"Made.up": _m("PASS")})
    with pytest.raises(ValueError, match="Build.dag"):   # the error names the offending criterion
        ac.rollup_asset("L2", {"Build.dag": _m("NOT_GENERIC")})


def test_non_cell_gates_are_excluded_visibly_not_dropped():
    ms = {"Count.floor": _m("FAIL"), "Cost.baseline": _m("PASS")}
    out = ac.rollup_asset("L2", ms)
    assert set(out) == set(ac.CELL_GATES)
    ex = ac.rollup_excluded("L2", ms)
    assert ex == {"Count.floor": "FAIL", "Cost.baseline": "PASS"}


def test_unknown_layer_raises():
    with pytest.raises(KeyError):
        ac.rollup_asset("L9", {})


# ───────────────────────── versioning ─────────────────────────

def test_cells_carry_registry_revision_and_fingerprint():
    cells = ac.rollup_asset("L2", {})
    for g, c in cells.items():
        assert c["gate"] == g
        assert c["registry_revision"] == ac.REGISTRY_REVISION
        assert c["registry_fingerprint"] == ac.registry_fingerprint()


def test_fingerprint_is_stable_and_changes_with_any_content(monkeypatch):
    fp = ac.registry_fingerprint()
    assert fp == ac.registry_fingerprint() and len(fp) == 64
    reg = {k: dict(v) for k, v in ac.CRITERION_REGISTRY.items()}
    reg["Build.dag"]["layers"] = ("L0",)
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    assert ac.registry_fingerprint() != fp
    monkeypatch.undo()
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {"Build.dag#measured:x": "d"})
    assert ac.registry_fingerprint() != fp
    monkeypatch.undo()
    monkeypatch.setattr(ac, "CELL_GATES", ac.CELL_GATES[:-1])
    assert ac.registry_fingerprint() != fp


def test_revision_pin_content_cannot_change_without_a_bump():
    assert isinstance(ac.REGISTRY_REVISION, int) and ac.REGISTRY_REVISION >= 1
    assert ac.REGISTRY_REVISION in PINNED_FINGERPRINTS, "bump: add the new revision's fingerprint pin"
    assert ac.registry_fingerprint() == PINNED_FINGERPRINTS[ac.REGISTRY_REVISION], (
        "the registry content changed: bump REGISTRY_REVISION and pin the new fingerprint")


# ───────────────────────── 127-asset regression ─────────────────────────

def _census_layer(layer):
    return {"layer": layer, "assets": [dict(asset_id=a, layer=layer, measurements={k: dict(v=v, measured="") for k, v in ms.items()})
                       for a, ms in FIXTURE["layers"][layer].items()]}


def test_fixture_is_the_127_asset_2457_cell_census():
    assert sum(len(v) for v in FIXTURE["layers"].values()) == 127
    assert sum(len(ms) for v in FIXTURE["layers"].values() for ms in v.values()) == 2457


def test_rollup_over_all_127_assets_is_total_versioned_and_never_better_than_the_worst_measured_check():
    rank = {v: i for i, v in enumerate(ac.ROLLUP_ORDER)}
    n = 0
    for layer in ALL_LAYERS:
        out = ac.rollup_census(_census_layer(layer))
        assert set(out) == set(FIXTURE["layers"][layer])
        for aid, cells in out.items():
            assert set(cells) == set(ac.CELL_GATES)
            n += 1
            for g, c in cells.items():
                assert c["registry_revision"] == ac.REGISTRY_REVISION
                # no facts were supplied and no N/A rule is declared: no cell may read N/A
                assert c["v"] != "N/A", (aid, g)
                worst = [ms_v for crit, ms_v in FIXTURE["layers"][layer][aid].items()
                         if ac.CRITERION_REGISTRY[crit]["gate"] == g and ms_v in rank]
                for v in worst:
                    assert rank[c["v"]] <= rank[v], (aid, g, c["v"], v)
                # a FAIL measured in the gate is a FAIL cell (worst wins)
                if "FAIL" in worst:
                    assert c["v"] == "FAIL", (aid, g)
                # Null and Narr have no registered check: NO_DETECTOR for every asset
                if g in ("Null", "Narr"):
                    assert c["v"] == "NO_DETECTOR"
    assert n == 127


def test_rollup_over_the_fixture_never_changes_an_input_measurement():
    for layer in ALL_LAYERS:
        census = _census_layer(layer)
        before = json.dumps(census, sort_keys=True)
        ac.rollup_census(census)
        assert json.dumps(census, sort_keys=True) == before


def test_existing_pure_functions_are_unchanged_on_every_measured_cell():
    """gap_id_for / lookup_criterion on all 2,457 cells: identity form and gate/check/detector/revision
    are exactly what the registry declared before E6.1."""
    for layer, assets in FIXTURE["layers"].items():
        for aid, ms in assets.items():
            for crit in ms:
                assert ac.gap_id_for(aid, crit) == f"{aid}-{crit}"
                gid, e = ac.lookup_criterion(aid, None, crit)
                assert gid == f"{aid}-{crit}" and crit == f"{e['gate']}.{e['check']}"
