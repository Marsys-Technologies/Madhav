"""test_e6_1_p2a_census_facts_rollup_cli.py — E6.1 packet 2a.

measure() emits the facts the rollup needs (`target_columns`, `asset_kind`, `has_count_sql`) without changing
any measurement; `facts_for_asset()` turns them into the `facts` mapping `rollup_asset` expects, with an
unsupplied / unknown / empty / wrong-typed fact staying UNKNOWN (never N/A: N/A is only by a declared rule,
and NA_RULE_DECISIONS is still empty, the N-22 decision being pending); `--rollup` writes the nine-gate cells
into the census JSON; `--emit-gaps` neither changes nor consumes it. Offline: the `_stub_layer` harness, no
database.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

FIXTURE = json.loads((HERE / "fixtures" / "census_cells_2026-09-30.json").read_text(encoding="utf-8"))


# ───────────────────────── offline measure() harness (same as packet 1 / a4) ─────────────────────────

def _reg_row(aid, target_table=None, has_writer=False, count_sql="", asset_kind=""):
    return dict(asset_id=aid, has_writer=has_writer, target_table=target_table, count_sql=count_sql,
                has_integrity=False, depends_on=[], target_floor=None, catalog_status="", asset_kind=asset_kind)


def _stub_layer(monkeypatch, ctrl, reg, tables, exists=None, views=None):
    """`tables`: table -> (columns, declared keys). `exists` overrides the set the catalog reports as existing
    (default: every table in `tables`), so a test can express an existing relation with NO column rows."""
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(reg), dict(registry_total=len(reg), active=len(reg),
                                                                    excluded_inactive=[])))
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists=set(tables) if exists is None else set(exists),
                                                       cols={t: c for t, (c, _k) in tables.items()},
                                                       keys={t: k for t, (_c, k) in tables.items()},
                                                       views=set(views or ())))
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})
    monkeypatch.setattr(ac, "live_counts", lambda r, *a, **k: ({x: None for x in r}, {}))
    monkeypatch.setattr(ac, "throughput", lambda prefix, *a, **k: {})
    monkeypatch.setattr(ac, "build_history", lambda prefix, *a, **k: dict(per={}, global_runs=0, global_with_layer=0, lit=set()))
    monkeypatch.setattr(ac, "latest_attempts", lambda ids: ({}, None))
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in reg}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=48, full=list(c), never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)

    def fake_psql(sql, sep="\x1f", timeout=None):
        if "IS NOT NULL" in sql:
            return [["48"]]
        raise AssertionError(f"unexpected query: {sql[:100]}")
    monkeypatch.setattr(ac, "psql", fake_psql)


def _asset(census, aid):
    return next(a for a in census["assets"] if a["asset_id"] == aid)


TABLES = {"t_cols": (["zeta", "alpha", "classical_citation", "id"], [])}
REG = {
    "bg_known": _reg_row("bg_known", "t_cols", count_sql="SELECT count(*) FROM t_cols", asset_kind="data"),
    "bg_notable": _reg_row("bg_notable", None, asset_kind="service"),
    "bg_absent": _reg_row("bg_absent", "t_absent"),                    # target table not in the catalog
    "bg_blank": _reg_row("bg_blank", None, count_sql="  \n ", asset_kind=""),
}


# ───────────────────────── (1) measure() emits the three facts ─────────────────────────

def test_measure_emits_target_columns_asset_kind_and_has_count_sql(monkeypatch, tmp_path):
    _stub_layer(monkeypatch, tmp_path, REG, TABLES)
    c = ac.measure("L0")
    a = _asset(c, "bg_known")
    assert a["target_columns"] == ["alpha", "classical_citation", "id", "zeta"]      # sorted list
    assert a["asset_kind"] == "data"
    assert a["has_count_sql"] is True
    n = _asset(c, "bg_notable")
    assert n["asset_kind"] == "service" and n["has_count_sql"] is False
    assert _asset(c, "bg_blank")["has_count_sql"] is False                            # whitespace-only is no count_sql


def test_unknown_columns_and_kind_are_an_explicit_marker_never_an_empty_list(monkeypatch, tmp_path):
    _stub_layer(monkeypatch, tmp_path, REG, TABLES)
    c = ac.measure("L0")
    assert _asset(c, "bg_notable")["target_columns"] == ac.UNKNOWN_FACT       # no target table
    assert _asset(c, "bg_absent")["target_columns"] == ac.UNKNOWN_FACT        # table not in production
    assert _asset(c, "bg_blank")["asset_kind"] == ac.UNKNOWN_FACT             # '' in the registry row
    assert ac.UNKNOWN_FACT == "unknown"
    for a in c["assets"]:
        tc = a["target_columns"]
        assert tc == ac.UNKNOWN_FACT or (isinstance(tc, list) and tc and all(isinstance(x, str) for x in tc)), a["asset_id"]


def test_an_existing_relation_with_no_column_rows_is_unknown_not_zero_columns(monkeypatch, tmp_path):
    """A materialized view is in the catalog's `exists` but information_schema lists no columns for it:
    introspection is incomplete there, which is UNKNOWN, not 'the table has zero columns'."""
    reg = {"bg_mv": _reg_row("bg_mv", "mv_x")}
    _stub_layer(monkeypatch, tmp_path, reg, {}, exists={"mv_x"}, views={"mv_x"})
    assert _asset(ac.measure("L0"), "bg_mv")["target_columns"] == ac.UNKNOWN_FACT


def test_zero_column_rows_and_columns_for_a_table_not_in_exists_are_both_unknown(monkeypatch, tmp_path):
    """An empty column list for an existing relation is incomplete introspection (UNKNOWN); columns reported for
    a relation the catalog does not list as existing are not trusted either."""
    reg = {"bg_empty": _reg_row("bg_empty", "t_empty"), "bg_ghost": _reg_row("bg_ghost", "t_ghost")}
    _stub_layer(monkeypatch, tmp_path, reg, {"t_empty": ([], []), "t_ghost": (["id", "classical_citation"], [])},
                exists={"t_empty"})
    c = ac.measure("L0")
    assert _asset(c, "bg_empty")["target_columns"] == ac.UNKNOWN_FACT
    assert _asset(c, "bg_ghost")["target_columns"] == ac.UNKNOWN_FACT
    assert "columns" not in ac.facts_for_asset(_asset(c, "bg_empty"))


def test_new_facts_leave_every_measurement_untouched(monkeypatch, tmp_path):
    _stub_layer(monkeypatch, tmp_path, REG, TABLES)
    c = ac.measure("L0")
    a = _asset(c, "bg_known")
    assert a["measurements"]["Ldgr.source_presence"] == dict(v=ac.PASS, measured="classical_citation populated on 48/48 rows")
    for x in c["assets"]:
        assert not any(k.startswith(("target_columns", "asset_kind", "has_count_sql")) for k in x["measurements"])


# ───────────────────────── (2) facts_for_asset ─────────────────────────

def test_facts_for_asset_maps_emitted_facts_to_the_rollup_facts_mapping():
    f = ac.facts_for_asset(dict(target_columns=["a", "b"], asset_kind="data", has_count_sql=True))
    assert f == dict(columns=["a", "b"], asset_kind="data", has_count_sql=True)
    assert "columns_known" not in f            # never asserted from an emitted list


@pytest.mark.parametrize("rec", [
    {},                                                            # a record from before packet 2a
    None,
    dict(target_columns="unknown", asset_kind="unknown"),          # the explicit unknown markers
    dict(target_columns=[], asset_kind=""),                        # empty never stands for known
    dict(target_columns="id", asset_kind=None),                    # wrong type: a bare string is not a column list
    dict(target_columns=["a", 3], asset_kind=7),
    dict(target_columns=["a", ""], asset_kind="  "),
    dict(target_columns=("a",), asset_kind=["data"]),
    dict(target_columns=None, has_count_sql="yes"),
    dict(target_columns={"a"}, has_count_sql=1),
])
def test_facts_for_asset_leaves_unusable_or_unknown_facts_out(rec):
    assert ac.facts_for_asset(rec) == {}


def test_facts_for_asset_carries_a_false_has_count_sql():
    assert ac.facts_for_asset(dict(has_count_sql=False)) == dict(has_count_sql=False)


def test_unknown_facts_keep_applicability_unknown_never_not_applicable(monkeypatch, tmp_path):
    """The whole point: an unknown fact must not turn into a disproving one. The marker string 'unknown'
    would, if passed through, match none of ('service',) and read NOT_APPLICABLE."""
    _stub_layer(monkeypatch, tmp_path, REG, TABLES)
    c = ac.measure("L0")
    for aid, crit, want in (("bg_notable", "Ldgr.source_presence", "UNKNOWN"),      # no table -> columns unknown
                            ("bg_absent", "Ldgr.source_presence", "UNKNOWN"),
                            ("bg_blank", "Earn.service_state", "UNKNOWN"),            # kind unknown
                            ("bg_known", "Ldgr.source_presence", "APPLIES"),
                            ("bg_known", "Earn.service_state", "NOT_APPLICABLE"),     # kind 'data' disproves 'service'
                            ("bg_notable", "Earn.service_state", "APPLIES")):
        got = ac.criterion_applicability(crit, "L0", ac.facts_for_asset(_asset(c, aid)))
        assert got["state"] == want, (aid, crit, got)


def test_known_columns_without_a_citation_column_are_not_applicable_but_the_cell_is_not_na(monkeypatch, tmp_path):
    reg = {"bg_nocit": _reg_row("bg_nocit", "t_plain")}
    _stub_layer(monkeypatch, tmp_path, reg, {"t_plain": (["id", "v"], [])})
    a = _asset(ac.measure("L0"), "bg_nocit")
    facts = ac.facts_for_asset(a)
    assert ac.criterion_applicability("Ldgr.source_presence", "L0", facts)["state"] == "NOT_APPLICABLE"
    cells = ac.rollup_asset("L0", a["measurements"], facts)
    ch = next(x for x in cells["Ldgr"]["checks"] if x["criterion"] == "Ldgr.source_presence")
    assert ch["state"] == "NOT_APPLICABLE" and ch["v"] == ac.NO_DET and "undecided" in ch["reason"]   # no declared rule
    assert ac.NA_RULE_DECISIONS == {}
    assert all(c["v"] != ac.NA for c in cells.values())


# ───────────────────────── (3) --rollup ─────────────────────────

def _run_main(monkeypatch, tmp_path, argv):
    out = tmp_path / "census.json"
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--out", str(out), *argv])
    rc = ac.main()
    return rc, json.loads(out.read_text(encoding="utf-8"))


def _strip(o):
    o = json.loads(json.dumps(o))
    o["L0"].pop("generated", None)
    return o


def test_rollup_flag_writes_nine_gate_cells_per_asset_with_registry_versioning(monkeypatch, tmp_path):
    _stub_layer(monkeypatch, tmp_path, REG, TABLES)
    rc, out = _run_main(monkeypatch, tmp_path, ["--rollup"])
    assert "rollup" in out and "rollup_excluded" in out and "L0" in out
    r = out["rollup"]
    assert r["registry_revision"] == ac.REGISTRY_REVISION
    assert r["registry_fingerprint"] == ac.registry_fingerprint()
    assert set(r["layers"]) == {"L0"}
    assert set(r["layers"]["L0"]) == set(REG)
    for aid, cells in r["layers"]["L0"].items():
        assert list(cells) == list(ac.CELL_GATES), aid
        for g, cell in cells.items():
            assert cell["gate"] == g
            assert cell["registry_revision"] == ac.REGISTRY_REVISION
            assert cell["registry_fingerprint"] == ac.registry_fingerprint()
            assert cell["v"] in ac.ROLLUP_ORDER
    # the facts the cells were computed from were the emitted ones: bg_known has the citation column, so its
    # Ldgr.source_presence is a measured PASS; bg_notable has no table, so the check stays UNKNOWN-state
    def chk(aid, gate, crit):
        return next(x for x in r["layers"]["L0"][aid][gate]["checks"] if x["criterion"] == crit)
    assert chk("bg_known", "Ldgr", "Ldgr.source_presence")["state"] == "MEASURED"
    assert chk("bg_notable", "Ldgr", "Ldgr.source_presence")["state"] == "UNKNOWN"
    assert chk("bg_known", "Earn", "Earn.service_state")["state"] == "NOT_APPLICABLE"
    assert chk("bg_notable", "Earn", "Earn.service_state")["state"] == "APPLIES"
    # nothing reads N/A while NA_RULE_DECISIONS is empty
    assert all(cell["v"] != ac.NA for cells in r["layers"]["L0"].values() for cell in cells.values())


def test_rollup_excluded_lists_only_non_nine_gate_criteria(monkeypatch, tmp_path):
    _stub_layer(monkeypatch, tmp_path, REG, TABLES)
    rc, out = _run_main(monkeypatch, tmp_path, ["--rollup"])
    ex = out["rollup_excluded"]["L0"]
    assert set(ex) == set(REG)
    assert ex["bg_known"], "a measured asset has measured non-nine criteria (Complete/Reach/Count/...)"
    for aid, d in ex.items():
        for crit, v in d.items():
            assert ac.CRITERION_REGISTRY[crit]["gate"] not in ac.CELL_GATES, crit
            assert v == _asset(out["L0"], aid)["measurements"][crit]["v"]


def test_without_rollup_flag_the_output_has_no_rollup_keys_and_is_otherwise_identical(monkeypatch, tmp_path):
    _stub_layer(monkeypatch, tmp_path, REG, TABLES)
    rc0, plain = _run_main(monkeypatch, tmp_path, [])
    rc1, rolled = _run_main(monkeypatch, tmp_path, ["--rollup"])
    assert rc0 == rc1
    assert "rollup" not in plain and "rollup_excluded" not in plain
    rolled_wo = {k: v for k, v in rolled.items() if k not in ("rollup", "rollup_excluded")}
    assert _strip(rolled_wo) == _strip(plain)


def test_a_rollup_failure_still_writes_the_census_and_exits_5(monkeypatch, tmp_path, capsys):
    _stub_layer(monkeypatch, tmp_path, REG, TABLES)

    def boom(*a, **k):
        raise ValueError("ungradable")
    monkeypatch.setattr(ac, "build_rollup_output", boom)
    rc, out = _run_main(monkeypatch, tmp_path, ["--rollup"])
    assert rc == 5 and "rollup" not in out and "L0" in out
    assert "rollup failed" in capsys.readouterr().err


# ───────────────────────── (4) --emit-gaps unchanged, and never fed the rollup ─────────────────────────

def _ledger_rows(tmp_path):
    p = tmp_path / "asset_gaps.jsonl"
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []
    for r in rows:
        r.pop("ts", None)
    return rows


FAILING_REG = {"bg_fail": _reg_row("bg_fail", "t_cols", has_writer=True, count_sql="SELECT count(*) FROM t_cols", asset_kind="data")}


def test_emit_gaps_is_unchanged_by_rollup_and_never_receives_it(monkeypatch, tmp_path):
    seen = []
    real = ac.emit_gaps

    def spy(census):
        seen.append(json.loads(json.dumps(census, default=str)))
        return real(census)

    d1, d2 = tmp_path / "a", tmp_path / "b"
    d1.mkdir(); d2.mkdir()
    monkeypatch.setattr(ac, "emit_gaps", spy)
    _stub_layer(monkeypatch, d1, FAILING_REG, TABLES)
    _run_main(monkeypatch, d1, ["--emit-gaps"])
    _stub_layer(monkeypatch, d2, FAILING_REG, TABLES)
    _run_main(monkeypatch, d2, ["--emit-gaps", "--rollup"])
    rows1, rows2 = _ledger_rows(d1), _ledger_rows(d2)
    assert rows1, "the fixture must open at least one gap or this test proves nothing"
    assert rows1 == rows2
    assert len(seen) == 2
    for s in seen:
        assert "rollup" not in s and "rollup_excluded" not in s
    a, b = ({k: v for k, v in s.items() if k != "generated"} for s in seen)
    assert a == b                                                   # emit_gaps saw the same census either way
    assert not any("rollup" in json.dumps(r) or "Ldgr" in r.get("gate", "") and "cell" in json.dumps(r) for r in rows2)


def test_emit_gaps_ignores_new_asset_keys():
    census = dict(layer="L0", assets=[dict(asset_id="bg_x", measurements={"Build.dag": dict(v=ac.PASS, measured="ok")},
                                           target_columns="unknown", asset_kind="unknown", has_count_sql=False)])
    # a PASS with no prior row is a no-op; the new keys must not be read as measurements or break the walk
    import os
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        old = ac.CTRL
        ac.CTRL = pathlib.Path(d)
        try:
            assert ac.emit_gaps(census) == (0, 0, 0, 0)
        finally:
            ac.CTRL = old


# ───────────────────────── (5) saved census outputs: facts absent => everything stays UNKNOWN ─────────────────────────

def _fixture_census():
    """The committed verdict-only compaction of census_L0..L5.json, rebuilt into `measure()`-shaped layers that
    (like the saved outputs themselves) carry NO packet-2a facts."""
    out = {}
    for layer, assets in FIXTURE["layers"].items():
        out[layer] = dict(layer=layer, assets=[
            dict(asset_id=aid, layer=layer, measurements={c: dict(v=v if isinstance(v, str) else v[0], measured="")
                                                          for c, v in ms.items()})
            for aid, ms in assets.items()])
    return out


def test_records_without_the_new_facts_roll_up_exactly_as_with_no_facts():
    for layer, c in _fixture_census().items():
        with_facts_fn = ac.rollup_census(c, {a["asset_id"]: ac.facts_for_asset(a) for a in c["assets"]})
        no_facts = ac.rollup_census(c, None)
        assert json.dumps(with_facts_fn, sort_keys=True) == json.dumps(no_facts, sort_keys=True), layer


def test_build_rollup_output_over_the_saved_shape_is_serialisable_and_versioned():
    cs = _fixture_census()
    o = ac.build_rollup_output(cs)
    json.dumps(o)
    assert set(o["rollup"]["layers"]) == set(cs)
    assert o["rollup"]["registry_revision"] == ac.REGISTRY_REVISION
    n = sum(len(v) for v in o["rollup"]["layers"].values())
    assert n == sum(len(c["assets"]) for c in cs.values())
