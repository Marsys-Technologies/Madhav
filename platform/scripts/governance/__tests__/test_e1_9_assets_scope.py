"""test_e1_9_assets_scope.py — Suvarna E1.9: `--assets` scopes the census and the ledger emit.

A level wave measures and emits ONLY its assets. Four guarantees, each with its own tests:
  (1) measure(layer, assets=) reads/measures only those assets (validated against the layer registry);
  (2) a scoped output is LABELLED (`scope: {assets, partial: true}` in the layer header, the file header and the
      rollup header) and anything that expects the whole population REFUSES it;
  (3) emit_gaps on a scoped census touches ONLY rows of those assets — the rest of the ledger is byte-identical
      (never closed, withdrawn, reopened, appended to, reordered);
  (4) the same scoped emit twice appends nothing the second time.
Offline: the same `_stub_layer` harness as the other census tests, no database.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402


@pytest.fixture(autouse=True)
def _no_evaluation_copy_marker(monkeypatch):
    """SS N-327/N-332: census_stamp looks for the evaluation-copy marker. These tests fake the database wholesale (every query gets one canned answer), so the lookup is answered 'no marker' here;
    test_n317_evaluation_copy.py covers the lookup itself. The target is the conftest default, `disposable`."""
    monkeypatch.setattr(ac, "read_eval_copy_marker", lambda: dict(checked=True, marker_present=False))


# ───────────────────────── offline harness ─────────────────────────

def _reg_row(aid, target_table=None, has_writer=False, count_sql=""):
    return dict(asset_id=aid, has_writer=has_writer, target_table=target_table, count_sql=count_sql,
                has_integrity=False, depends_on=[], target_floor=None, catalog_status="", asset_kind="")


REG = {a: _reg_row(a) for a in ("bg_a", "bg_b", "bg_c", "bg_d")}
REG_L2 = {a: _reg_row(a) for a in ("bo_x", "bo_y")}
SEEN: dict = {}


def _stub(monkeypatch, ctrl, regs=None):
    """`regs`: layer -> registry dict (default: REG for every layer). Records what each per-asset read was given."""
    regs = regs or {k: REG for k in ac.LAYERS}
    SEEN.clear()
    monkeypatch.setattr(ac, "CTRL", ctrl)
    monkeypatch.setattr(ac, "registry", lambda k: (dict(regs.get(k, {})), dict(
        registry_total=len(regs.get(k, {})) + 1, active=len(regs.get(k, {})),
        excluded_inactive=[dict(asset_id="bg_retired")])))

    def cat(ts):
        SEEN["catalog"] = list(ts)
        return dict(exists=set(), cols={}, keys={}, views=set())
    monkeypatch.setattr(ac, "catalog", cat)
    monkeypatch.setattr(ac, "registered_ids", lambda prefix: {})

    def counts(r, *a, **k):
        SEEN["live_counts"] = sorted(r)
        return {x: None for x in r}, {}
    monkeypatch.setattr(ac, "live_counts", counts)

    def thru(prefix, ids=None, *a, **k):
        SEEN.setdefault("throughput", []).append(sorted(ids or []))
        return {}
    monkeypatch.setattr(ac, "throughput", thru)

    def hist(prefix, ids=None, *a, **k):
        SEEN["build_history"] = sorted(ids or [])
        return dict(per={}, global_runs=0, global_with_layer=0, lit=set())
    monkeypatch.setattr(ac, "build_history", hist)

    def attempts(ids):
        SEEN["latest_attempts"] = sorted(ids)
        return {}, None
    monkeypatch.setattr(ac, "latest_attempts", attempts)
    monkeypatch.setattr(ac, "dependency_graph", lambda: {a: [] for a in REG}, raising=False)
    monkeypatch.setattr(ac, "local_map_candidates", lambda prefix: -1)
    monkeypatch.setattr(ac, "duration_instrument_present", lambda: False)
    monkeypatch.setattr(ac, "capability_scan", lambda d, t, **kw: dict(modules=[], density=0, note="stub"))
    monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=48, full=list(c), never=[], note=""))
    monkeypatch.setattr(ac, "alias_census", lambda t, c: None)
    monkeypatch.setattr(ac, "psql", lambda sql, sep="\x1f", timeout=None: [["48"]])


def _ids(c):
    return [a["asset_id"] for a in c["assets"]]


def _write(ctrl, rows):
    (ctrl / "asset_gaps.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def _raw(ctrl) -> bytes:
    p = ctrl / "asset_gaps.jsonl"
    return p.read_bytes() if p.exists() else b""


def _row(asset, crit, state, **kw):
    return dict(asset=asset, gap_id=f"{asset}-{crit}", kind="gap", criterion=crit, what="w", change="c",
                detector="asset_census.py --layer L0 (x)", owner="asset_census",
                gate="this asset's certification", state=state, ts="t0", **kw)


def _census(layer, specs, scope=None):
    """specs: [(asset, crit, verdict)] -> a census dict; `scope` (a list) adds the scope label."""
    by: dict = {}
    for aid, crit, v in specs:
        by.setdefault(aid, {})[crit] = dict(v=v, measured="m")
    c = dict(layer=layer, assets=[dict(asset_id=a, measurements=m) for a, m in by.items()])
    if scope is not None:
        c["scope"] = dict(assets=sorted(scope), partial=True)
    return c


# ═════════════════════ (1a) parsing: forms, negatives ═════════════════════

def test_parse_comma_list_repeated_flag_and_at_file(tmp_path):
    f = tmp_path / "ids.txt"
    f.write_text("# a level wave\nbg_c\nbg_d, bg_e\n\n", encoding="utf-8")
    assert ac.parse_assets_arg(["bg_a,bg_b"]) == ["bg_a", "bg_b"]
    assert ac.parse_assets_arg(["bg_a", "bg_b"]) == ["bg_a", "bg_b"]
    assert ac.parse_assets_arg([f"@{f}"]) == ["bg_c", "bg_d", "bg_e"]
    assert ac.parse_assets_arg(["bg_a", f"@{f}"]) == ["bg_a", "bg_c", "bg_d", "bg_e"]


def test_parse_trims_surrounding_whitespace(tmp_path):
    assert ac.parse_assets_arg(["  bg_a ,\tbg_b  "]) == ["bg_a", "bg_b"]


@pytest.mark.parametrize("raw", [[""], ["   "], [","], ["bg_a,,bg_b"], ["bg_a,"], [",bg_a"], [], ["", ""]])
def test_parse_empty_list_or_entry_is_an_error(raw):
    with pytest.raises(ac.ScopeError):
        ac.parse_assets_arg(raw)


def test_parse_empty_at_file_is_an_error(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("# nothing\n\n", encoding="utf-8")
    with pytest.raises(ac.ScopeError, match="no asset"):
        ac.parse_assets_arg([f"@{f}"])


def test_parse_missing_at_file_and_nested_at_are_errors(tmp_path):
    with pytest.raises(ac.ScopeError, match="cannot read"):
        ac.parse_assets_arg([f"@{tmp_path / 'absent.txt'}"])
    f = tmp_path / "nest.txt"
    f.write_text("@other\n", encoding="utf-8")
    with pytest.raises(ac.ScopeError, match="nested"):
        ac.parse_assets_arg([f"@{f}"])


@pytest.mark.parametrize("raw", [["bg_a,bg_a"], ["bg_a", "bg_a"], ["bg_a, bg_b ,bg_a"]])
def test_parse_duplicates_are_an_error_naming_the_duplicate(raw):
    with pytest.raises(ac.ScopeError, match="duplicate.*bg_a"):
        ac.parse_assets_arg(raw)


@pytest.mark.parametrize("raw", [["bg a"], ["bg_a bg_b"], ["bg_a\tbg_b"]])
def test_parse_whitespace_inside_an_id_is_an_error(raw):
    with pytest.raises(ac.ScopeError, match="whitespace"):
        ac.parse_assets_arg(raw)


@pytest.mark.parametrize("bad", ["BG_A", "Bg_a", "bg-a", "bg.a", "1bg", "bg_a;", "bg_a'"])
def test_parse_case_and_malformed_ids_are_rejected_not_normalized(bad):
    with pytest.raises(ac.ScopeError, match="malformed|lowercase"):
        ac.parse_assets_arg([bad])


# ═════════════════════ (1b) validation against the registry set ═════════════════════

def test_validate_returns_ids_partitioned_by_layer_registry(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {"L0": REG, "L2": REG_L2})
    got = ac.validate_scope(["bo_y", "bg_c", "bg_a"], ["L0", "L2"])
    assert got == {"L0": ["bg_a", "bg_c"], "L2": ["bo_y"]}


def test_validate_unknown_asset_is_a_clear_error(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {"L0": REG})
    with pytest.raises(ac.ScopeError, match=r"bg_nope: unknown asset"):
        ac.validate_scope(["bg_a", "bg_nope"], ["L0"])


def test_validate_asset_of_another_layer_is_a_wrong_layer_error(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {"L0": REG, "L2": REG_L2})
    with pytest.raises(ac.ScopeError, match=r"bo_x.*belongs to L2.*not in the selected layer"):
        ac.validate_scope(["bg_a", "bo_x"], ["L0"])


def test_validate_retired_asset_is_refused_with_its_own_message(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {"L0": REG})
    with pytest.raises(ac.ScopeError, match=r"bg_retired.*retired|inactive"):
        ac.validate_scope(["bg_retired"], ["L0"])


def test_validate_reports_every_bad_id_at_once(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {"L0": REG, "L2": REG_L2})
    with pytest.raises(ac.ScopeError) as e:
        ac.validate_scope(["bg_zz", "bo_x", "bg_a"], ["L0"])
    assert "bg_zz" in str(e.value) and "bo_x" in str(e.value)


# ═════════════════════ (1c) measure() reads/measures only the scope ═════════════════════

def test_measure_scoped_measures_only_the_selected_assets(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    c = ac.measure("L0", assets=["bg_c", "bg_a"])
    assert _ids(c) == ["bg_a", "bg_c"] and c["n_assets"] == 2
    assert SEEN["live_counts"] == ["bg_a", "bg_c"]
    assert SEEN["build_history"] == ["bg_a", "bg_c"]
    assert SEEN["latest_attempts"] == ["bg_a", "bg_c"]
    assert SEEN["throughput"][0] == ["bg_a", "bg_c"]


def test_measure_scoped_carries_the_scope_label_and_unscoped_does_not(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    s = ac.measure("L0", assets=["bg_b"])
    assert s["scope"] == dict(assets=["bg_b"], partial=True)
    full = ac.measure("L0")
    assert "scope" not in full and _ids(full) == sorted(REG)


def test_measure_scoped_layer_facts_still_describe_the_whole_layer(monkeypatch, tmp_path):
    """The population facts are the layer's, not the scope's: a reader sees 4 active of 5 rows even in a 1-asset run."""
    _stub(monkeypatch, tmp_path)
    s = ac.measure("L0", assets=["bg_a"])
    full = ac.measure("L0")
    for k in ("population_active", "population_registry_total", "chart_scope", "registry_has_writer"):
        assert s[k] == full[k], k


def test_measure_scoped_assets_equal_their_unscoped_measurements(monkeypatch, tmp_path):
    """Scoping must not change what an asset measures to (Build.dag still sees the WHOLE layer's ids)."""
    _stub(monkeypatch, tmp_path)
    full = {a["asset_id"]: a for a in ac.measure("L0")["assets"]}
    for a in ac.measure("L0", assets=["bg_b", "bg_d"])["assets"]:
        assert a == full[a["asset_id"]]


def test_measure_scoped_unknown_asset_raises_before_measuring(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    with pytest.raises(ac.ScopeError, match="bg_nope"):
        ac.measure("L0", assets=["bg_a", "bg_nope"])
    assert "live_counts" not in SEEN


@pytest.mark.parametrize("bad", [[], ["bg_a", "bg_a"], ["BG_A"]])
def test_measure_scoped_refuses_an_empty_duplicate_or_miscased_list(monkeypatch, tmp_path, bad):
    _stub(monkeypatch, tmp_path)
    with pytest.raises(ac.ScopeError):
        ac.measure("L0", assets=bad)


# ═════════════════════ (2) labelled output; whole-population consumers refuse ═════════════════════

def _run_main(monkeypatch, tmp_path, argv, layer="L0", out="census.json"):
    o = tmp_path / out
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", layer, "--out", str(o), *argv])
    rc = ac.main()
    return rc, (json.loads(o.read_text(encoding="utf-8")) if o.exists() else None)


def test_cli_scoped_run_labels_file_layer_and_rollup_headers(monkeypatch, tmp_path, capsys):
    _stub(monkeypatch, tmp_path)
    rc, out = _run_main(monkeypatch, tmp_path, ["--assets", "bg_a,bg_c", "--rollup"])
    assert out["scope"] == dict(assets=["bg_a", "bg_c"], partial=True, layers=["L0"])
    assert out["L0"]["scope"] == dict(assets=["bg_a", "bg_c"], partial=True)
    assert out["rollup"]["scope"] == dict(assets=["bg_a", "bg_c"], partial=True, layers=["L0"],
                                          registry_revision=ac.REGISTRY_REVISION)
    assert out["rollup"]["registry_revision"] == ac.REGISTRY_REVISION
    assert set(out["rollup"]["layers"]["L0"]) == {"bg_a", "bg_c"}
    assert "SCOPED" in capsys.readouterr().out


def test_cli_unscoped_run_has_no_scope_key_anywhere(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    rc, out = _run_main(monkeypatch, tmp_path, ["--rollup"])
    assert "scope" not in out and "scope" not in out["L0"] and "scope" not in out["rollup"]


def test_cli_scoped_run_never_overwrites_the_default_full_census_path(monkeypatch, tmp_path, capsys):
    _stub(monkeypatch, tmp_path)
    full = tmp_path / "asset_census.json"
    full.write_text("FULL", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--assets", "bg_a",
                                      "--out", str(full)])
    assert ac.main() == ac.EXIT_SCOPE
    assert full.read_text(encoding="utf-8") == "FULL"
    assert "full census" in capsys.readouterr().err


def test_cli_scoped_run_without_out_writes_a_separate_scoped_file(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--assets", "bg_a"])
    (tmp_path / "asset_census.json").write_text("FULL", encoding="utf-8")
    monkeypatch.setattr(ac, "ROOT", tmp_path)
    rc = ac.main()
    assert rc in (0, 2, 3)
    assert (tmp_path / "asset_census.json").read_text(encoding="utf-8") == "FULL"
    assert json.loads((tmp_path / "asset_census_scoped.json").read_text(encoding="utf-8"))["scope"]["partial"] is True


def test_rollup_of_a_scoped_census_skips_the_whole_registry_id_check(monkeypatch, tmp_path):
    """`--layer all` reaching every layer is not a full run when the assets are a subset: the declarations id check
    needs the whole registry set, so a scoped run must not pass it a partial id list as if it were whole."""
    _stub(monkeypatch, tmp_path)
    seen = {}
    monkeypatch.setattr(ac, "load_asset_declarations", lambda registry_ids=None: seen.setdefault("ids", registry_ids) or {})
    census = {k: ac.measure(k, assets=["bg_a"]) for k in ac.LAYERS}
    seen.clear()                      # measure() itself reads the declarations file; only the rollup's call is under test
    ac.build_rollup_output(census)
    assert seen == {"ids": None}


def test_load_full_census_refuses_every_scoped_shape(tmp_path):
    full = tmp_path / "full.json"
    full.write_text(json.dumps({"L0": {"layer": "L0", "assets": []}}), encoding="utf-8")
    assert ac.load_full_census(full)["L0"]["assets"] == []
    for name, body in {"file": {"scope": dict(assets=["a"], partial=True), "L0": {"assets": []}},
                       "layer": {"L0": {"assets": [], "scope": dict(assets=["a"], partial=True)}},
                       "rollup": {"L0": {"assets": []}, "rollup": {"scope": dict(assets=["a"], partial=True)}}}.items():
        p = tmp_path / f"{name}.json"
        p.write_text(json.dumps(body), encoding="utf-8")
        with pytest.raises(ac.ScopeError, match="SCOPED|partial"):
            ac.load_full_census(p)


def test_require_full_census_accepts_a_layer_dict_too():
    with pytest.raises(ac.ScopeError):
        ac.require_full_census(dict(layer="L0", assets=[], scope=dict(assets=["a"], partial=True)), "x")
    ac.require_full_census(dict(layer="L0", assets=[]), "x")


# ═════════════════════ (3) emit isolation: only the scope's rows are touched ═════════════════════

def _mixed_ledger():
    """Rows for assets OUTSIDE the scope in every state the lifecycle knows, plus hand/superseded/malformed lines."""
    return [
        _row("bg_other", "Build.dag", "OPEN"),
        _row("bg_other", "Idem.pattern", "CLOSED"),
        _row("bg_other", "Cost.baseline", "WITHDRAWN"),
        _row("bg_other", "Build.target", "OPEN", superseded_by="bg_other-Build.dag"),
        dict(asset="bg_other", gap_id="bg_other-G07", kind="opportunity", criterion="Vocab.alias",
             what="hand", change="", detector="a probe", owner="human", gate="g", state="OPEN", ts="t1"),
        _row("bg_a", "Build.dag", "OPEN"),
        _row("bg_a", "Idem.pattern", "CLOSED"),
    ]


def test_scoped_emit_leaves_every_other_row_byte_identical_and_in_order(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    rows = _mixed_ledger()
    _write(tmp_path, rows)
    before = _raw(tmp_path)
    # the census MEASURES things that would transition other-asset rows if they were in scope:
    census = _census("L0", [("bg_a", "Build.dag", "PASS"),        # closes bg_a's OPEN row
                            ("bg_a", "Idem.pattern", "FAIL"),     # reopens bg_a's CLOSED row
                            ("bg_a", "Build.target", "FAIL")],    # new OPEN row for bg_a
                     scope=["bg_a"])
    added, skipped, closed, reopened = ac.emit_gaps(census)
    assert (added, closed, reopened) == (1, 1, 1)
    after = _raw(tmp_path)
    assert after.startswith(before), "existing rows (any asset) must be byte-identical and in the same order"
    new = [json.loads(x) for x in after[len(before):].decode().splitlines()]
    assert {r["asset"] for r in new} == {"bg_a"} and len(new) == 3


def test_emit_with_assets_filters_a_full_census_to_only_those_assets(tmp_path, monkeypatch):
    """The filter itself, not just the census's shape: a census holding every asset's failures, emit(assets=[bg_a])."""
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    _write(tmp_path, _mixed_ledger())
    before = _raw(tmp_path)
    census = _census("L0", [("bg_a", "Build.dag", "PASS"), ("bg_other", "Build.dag", "PASS"),    # other would CLOSE
                            ("bg_other", "Idem.pattern", "FAIL"),                                  # other would REOPEN
                            ("bg_other", "Cost.baseline", "FAIL"),                                 # WITHDRAWN stays
                            ("bg_new", "Build.dag", "FAIL")])                                      # other would OPEN
    ac.emit_gaps(census, assets=["bg_a"])
    after = _raw(tmp_path)
    assert after.startswith(before)
    new = [json.loads(x) for x in after[len(before):].decode().splitlines()]
    assert [(r["asset"], r["state"]) for r in new] == [("bg_a", "CLOSED")]


def test_scoped_emit_never_closes_withdraws_or_reopens_other_assets(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    _write(tmp_path, _mixed_ledger())
    before = _raw(tmp_path)
    census = _census("L0", [("bg_other", "Build.dag", "PASS"), ("bg_other", "Idem.pattern", "FAIL"),
                            ("bg_other", "Cost.baseline", "PASS"), ("bg_other", "Build.target", "FAIL")],
                     scope=["bg_a"])
    with pytest.raises(ac.ScopeError, match="bg_other"):
        ac.emit_gaps(census)        # a census whose assets contradict its own scope fails closed, writing nothing
    assert _raw(tmp_path) == before


def test_emit_on_an_empty_ledger_with_scope_writes_only_scope_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    census = _census("L0", [("bg_a", "Build.dag", "FAIL"), ("bg_b", "Build.dag", "FAIL")])
    ac.emit_gaps(census, assets=["bg_b"])
    assert [r["asset"] for r in (json.loads(x) for x in _raw(tmp_path).decode().splitlines())] == ["bg_b"]


def test_emit_assets_not_in_the_census_is_an_error_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    _write(tmp_path, _mixed_ledger())
    before = _raw(tmp_path)
    census = _census("L0", [("bg_a", "Build.dag", "PASS")])
    with pytest.raises(ac.ScopeError, match="bg_zz"):
        ac.emit_gaps(census, assets=["bg_a", "bg_zz"])
    assert _raw(tmp_path) == before


@pytest.mark.parametrize("bad_scope", [None, "x", dict(assets="bg_a", partial=True), dict(assets=["bg_a"], partial=False),
                                       dict(assets=[], partial=True), dict(partial=True)])
def test_emit_refuses_a_malformed_scope_label(tmp_path, monkeypatch, bad_scope):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    c = _census("L0", [("bg_a", "Build.dag", "FAIL")])
    c["scope"] = bad_scope
    with pytest.raises(ac.ScopeError):
        ac.emit_gaps(c)
    assert _raw(tmp_path) == b""


def test_emit_empty_assets_list_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    with pytest.raises(ac.ScopeError):
        ac.emit_gaps(_census("L0", [("bg_a", "Build.dag", "FAIL")]), assets=[])


def test_scoped_emit_rows_equal_the_unscoped_rows_for_the_same_assets(tmp_path, monkeypatch):
    """A scoped run writes exactly the rows an unscoped run would have written for those assets (ts aside)."""
    specs = [("bg_a", "Build.dag", "FAIL"), ("bg_b", "Build.dag", "FAIL"), ("bg_a", "Idem.pattern", "FAIL")]
    def rows_after(emit):
        d = tmp_path / emit.__name__
        d.mkdir()
        monkeypatch.setattr(ac, "CTRL", d)
        emit()
        return [{k: v for k, v in json.loads(x).items() if k != "ts"} for x in _raw(d).decode().splitlines()]
    def scoped():
        ac.emit_gaps(_census("L0", [s for s in specs if s[0] == "bg_a"], scope=["bg_a"]))
    def unscoped():
        ac.emit_gaps(_census("L0", specs))
    sc, un = rows_after(scoped), rows_after(unscoped)
    assert sc == [r for r in un if r["asset"] == "bg_a"]


# ═════════════════════ (4) idempotency ═════════════════════

def test_same_scoped_emit_twice_appends_nothing_the_second_time(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    _write(tmp_path, _mixed_ledger())
    census = _census("L0", [("bg_a", "Build.dag", "PASS"), ("bg_a", "Idem.pattern", "FAIL"),
                            ("bg_a", "Build.target", "FAIL")], scope=["bg_a"])
    first = ac.emit_gaps(census)
    mid = _raw(tmp_path)
    second = ac.emit_gaps(census)
    assert first[0] + first[2] + first[3] == 3
    assert (second[0], second[2], second[3]) == (0, 0, 0)
    assert _raw(tmp_path) == mid


def test_scoped_then_unscoped_is_idempotent_on_the_scoped_assets(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    specs = [("bg_a", "Build.dag", "FAIL"), ("bg_b", "Build.dag", "FAIL")]
    ac.emit_gaps(_census("L0", specs[:1], scope=["bg_a"]))
    ac.emit_gaps(_census("L0", specs))
    rows = [json.loads(x) for x in _raw(tmp_path).decode().splitlines()]
    assert sorted(r["asset"] for r in rows) == ["bg_a", "bg_b"]           # bg_a not duplicated by the full run


# ═════════════════════ CLI end to end (flags, exit codes) ═════════════════════

def test_cli_scoped_emit_end_to_end_touches_only_scoped_rows(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    _write(tmp_path, [_row("bg_b", "Build.registered", "OPEN"), _row("bg_c", "Build.registered", "CLOSED")])
    before = _raw(tmp_path)
    rc, out = _run_main(monkeypatch, tmp_path, ["--assets", "bg_a", "--emit-gaps"])
    after = _raw(tmp_path)
    assert after.startswith(before)
    assert {json.loads(x)["asset"] for x in after[len(before):].decode().splitlines()} <= {"bg_a"}
    again = _raw(tmp_path)
    _run_main(monkeypatch, tmp_path, ["--assets", "bg_a", "--emit-gaps"])
    assert _raw(tmp_path) == again


@pytest.mark.parametrize("argv", [["--assets", "bg_nope"], ["--assets", ""], ["--assets", "bg_a,bg_a"],
                                  ["--assets", "BG_A"], ["--assets", "bg_a bg_b"]])
def test_cli_bad_scope_exits_nonzero_and_writes_nothing(monkeypatch, tmp_path, capsys, argv):
    _stub(monkeypatch, tmp_path)
    _write(tmp_path, [_row("bg_b", "Build.registered", "OPEN")])
    before = _raw(tmp_path)
    rc, out = _run_main(monkeypatch, tmp_path, [*argv, "--emit-gaps"])
    assert rc == ac.EXIT_SCOPE and out is None
    assert _raw(tmp_path) == before
    assert "asset_census: scope error" in capsys.readouterr().err


def test_cli_wrong_layer_exits_nonzero(monkeypatch, tmp_path, capsys):
    _stub(monkeypatch, tmp_path, {"L0": REG, "L2": REG_L2})
    rc, out = _run_main(monkeypatch, tmp_path, ["--assets", "bo_x"], layer="L0")
    assert rc == ac.EXIT_SCOPE and out is None
    assert "belongs to L2" in capsys.readouterr().err


def test_cli_all_layers_skips_layers_with_no_scoped_assets(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path, {"L0": REG, "L2": REG_L2})
    rc, out = _run_main(monkeypatch, tmp_path, ["--assets", "bg_a,bo_y"], layer="all")
    assert set(k for k in out if k in ac.LAYERS) == {"L0", "L2"}
    assert out["scope"]["assets"] == ["bg_a", "bo_y"] and out["scope"]["layers"] == ["L0", "L2"]


def test_cli_at_file_form(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    f = tmp_path / "wave.txt"
    f.write_text("bg_b\nbg_d\n", encoding="utf-8")
    rc, out = _run_main(monkeypatch, tmp_path, ["--assets", f"@{f}"])
    assert out["scope"]["assets"] == ["bg_b", "bg_d"]


# ═════════════════════ mutation-found gaps (each test kills a mutant of the scoping logic) ═════════════════════

def test_emit_assets_narrows_a_scoped_census_to_the_intersection(tmp_path, monkeypatch):
    """A census labelled for {bg_a, bg_b} emitted with assets=[bg_a] writes bg_a only (intersection, never union)."""
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    census = _census("L0", [("bg_a", "Build.dag", "FAIL"), ("bg_b", "Build.dag", "FAIL")], scope=["bg_a", "bg_b"])
    ac.emit_gaps(census, assets=["bg_a"])
    assert [json.loads(x)["asset"] for x in _raw(tmp_path).decode().splitlines()] == ["bg_a"]


def test_scoped_asset_with_an_out_of_scope_dependency_measures_like_a_full_run(monkeypatch, tmp_path):
    """Build.dag resolves a declared dependency against the WHOLE layer's ids: scoping bg_a must not make its
    dependency on bg_b look unresolvable."""
    reg = {a: _reg_row(a) for a in ("bg_a", "bg_b", "bg_c")}
    reg["bg_a"] = dict(reg["bg_a"], depends_on=["bg_b"])
    _stub(monkeypatch, tmp_path, {k: reg for k in ac.LAYERS})

    def no_graph():
        raise ac.Unknown("registry-wide dependency read unavailable")
    monkeypatch.setattr(ac, "dependency_graph", no_graph)     # exists-clause then rests on the layer's `known` ids alone
    full = next(a for a in ac.measure("L0")["assets"] if a["asset_id"] == "bg_a")
    scoped = ac.measure("L0", assets=["bg_a"])["assets"][0]
    assert scoped["measurements"]["Build.dag"] == full["measurements"]["Build.dag"]
    assert "unknown or inactive" not in scoped["measurements"]["Build.dag"]["measured"]
    assert scoped == full


@pytest.mark.parametrize("sc", [dict(assets=[], partial=True), dict(assets=["a", ""], partial=True),
                                dict(assets=["a", 3], partial=True), dict(assets=["a"], partial=False),
                                dict(assets=["a"]), "a", None, ["a"]])
def test_census_scope_rejects_every_malformed_label(sc):
    with pytest.raises(ac.ScopeError):
        ac.census_scope({"scope": sc})


def test_census_scope_none_without_label_and_returns_a_valid_one():
    assert ac.census_scope({"layer": "L0"}) is None
    assert ac.census_scope({"scope": dict(assets=["a"], partial=True)}) == dict(assets=["a"], partial=True)


# ═════════════════════ review corrections (F2 guard bypass, F3 @file encoding, F4 layer facts, F5 stripped label) ═════════════════════
import os  # noqa: E402


def _case_insensitive_fs(d: pathlib.Path) -> bool:
    probe = d / "CaseProbe.tmp"
    probe.write_text("x", encoding="utf-8")
    try:
        return (d / "caseprobe.tmp").exists()
    finally:
        probe.unlink()


def _scoped_main(monkeypatch, tmp_path, out=None, extra=()):
    argv = ["asset_census.py", "--layer", "L0", "--assets", "bg_a", *extra]
    if out is not None:
        argv += ["--out", str(out)]
    monkeypatch.setattr(sys, "argv", argv)
    return ac.main()


def _full_file(tmp_path):
    f = tmp_path / "asset_census.json"
    f.write_text("FULL-CENSUS", encoding="utf-8")
    return f


def test_f2_case_variant_of_the_full_census_path_is_refused(monkeypatch, tmp_path, capsys):
    if not _case_insensitive_fs(tmp_path):
        pytest.skip("case-sensitive filesystem: ASSET_CENSUS.JSON is a different file here")
    _stub(monkeypatch, tmp_path)
    full = _full_file(tmp_path)
    assert _scoped_main(monkeypatch, tmp_path, out=tmp_path / "ASSET_CENSUS.JSON") == ac.EXIT_SCOPE
    assert full.read_text(encoding="utf-8") == "FULL-CENSUS"


def test_f2_hardlink_to_the_full_census_is_refused(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    full = _full_file(tmp_path)
    link = tmp_path / "alias.json"
    os.link(full, link)
    assert _scoped_main(monkeypatch, tmp_path, out=link) == ac.EXIT_SCOPE
    assert full.read_text(encoding="utf-8") == "FULL-CENSUS" and link.read_text(encoding="utf-8") == "FULL-CENSUS"


def test_f2_symlink_to_the_full_census_is_refused_explicit_and_default(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    full = _full_file(tmp_path)
    sym = tmp_path / "sym.json"
    sym.symlink_to(full)
    assert _scoped_main(monkeypatch, tmp_path, out=sym) == ac.EXIT_SCOPE
    # the DEFAULT scoped path being a link to the full census is refused too
    (tmp_path / "asset_census_scoped.json").symlink_to(full)
    assert _scoped_main(monkeypatch, tmp_path) == ac.EXIT_SCOPE
    assert full.read_text(encoding="utf-8") == "FULL-CENSUS"


def test_f2_default_scoped_path_hardlinked_to_the_full_census_is_refused(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    full = _full_file(tmp_path)
    os.link(full, tmp_path / "asset_census_scoped.json")
    assert _scoped_main(monkeypatch, tmp_path) == ac.EXIT_SCOPE
    assert full.read_text(encoding="utf-8") == "FULL-CENSUS"


def test_f2_a_distinct_existing_file_is_still_overwritten(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    _full_file(tmp_path)
    other = tmp_path / "wave1.json"
    other.write_text("old", encoding="utf-8")
    assert _scoped_main(monkeypatch, tmp_path, out=other) in (0, 2, 3)
    assert json.loads(other.read_text(encoding="utf-8"))["scope"]["partial"] is True


def test_f2_scoped_output_is_written_atomically(monkeypatch, tmp_path):
    """A failure at the final rename leaves the previous scoped file whole and no temp file behind."""
    _stub(monkeypatch, tmp_path)
    tgt = tmp_path / "wave.json"
    tgt.write_text("PREVIOUS", encoding="utf-8")
    real = os.replace
    monkeypatch.setattr(os, "replace", lambda *a, **k: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(OSError):
        _scoped_main(monkeypatch, tmp_path, out=tgt)
    assert tgt.read_text(encoding="utf-8") == "PREVIOUS"
    assert sorted(p.name for p in tmp_path.iterdir() if p.name.startswith(".") or p.suffix == ".tmp") == []
    monkeypatch.setattr(os, "replace", real)
    assert _scoped_main(monkeypatch, tmp_path, out=tgt) in (0, 2, 3)
    assert json.loads(tgt.read_text(encoding="utf-8"))["scope"]["partial"] is True
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp") or p.name.startswith(".asset_census")] == []


def test_f2_scoped_output_goes_through_a_temp_file_in_the_same_directory(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    seen = []
    real = os.replace
    monkeypatch.setattr(os, "replace", lambda s, d: (seen.append((str(s), str(d))), real(s, d))[1])
    tgt = tmp_path / "wave.json"
    _scoped_main(monkeypatch, tmp_path, out=tgt)
    assert len(seen) == 1 and seen[0][1] == str(tgt) and os.path.dirname(seen[0][0]) == str(tmp_path)


# F3: @file encoding
def test_f3_utf8_bom_file_is_accepted(tmp_path):
    f = tmp_path / "bom.txt"
    f.write_bytes(b"\xef\xbb\xbfbg_a\nbg_b\n")
    assert ac.parse_assets_arg([f"@{f}"]) == ["bg_a", "bg_b"]


@pytest.mark.parametrize("payload", ["bg_a\nbg_b\n".encode("utf-16"), b"bg_a\n\xff\xfe\x00", b"\x00\x01\x02\xff"])
def test_f3_non_utf8_file_is_a_clear_scope_error(tmp_path, payload):
    f = tmp_path / "bad.txt"
    f.write_bytes(payload)
    with pytest.raises(ac.ScopeError, match="not valid UTF-8"):
        ac.parse_assets_arg([f"@{f}"])


def test_f3_cli_utf16_file_exits_6_not_5(monkeypatch, tmp_path, capsys):
    _stub(monkeypatch, tmp_path)
    f = tmp_path / "u16.txt"
    f.write_bytes("bg_a\n".encode("utf-16"))
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--assets", f"@{f}"])
    assert ac.main() == ac.EXIT_SCOPE
    assert "not valid UTF-8" in capsys.readouterr().err


def test_f5_parse_duplicate_detection_is_linear():
    import time
    ids = [f"bg_{i}" for i in range(60000)]
    t = time.time()
    assert ac.parse_assets_arg([",".join(ids)]) == ids
    assert time.time() - t < 5
    with pytest.raises(ac.ScopeError, match="duplicate.*bg_7"):
        ac.parse_assets_arg([",".join(ids + ["bg_7"])])


# F4: layer-wide facts are never computed from the scoped ids
def test_f4_scoped_census_omits_the_scoped_only_build_history_facts(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    s = ac.measure("L0", assets=["bg_a"])
    assert "global_runs" not in s and "global_runs_touching_layer" not in s
    full = ac.measure("L0")
    assert "global_runs" in full and "global_runs_touching_layer" in full
    assert list(full)[:1] == ["generated"]


def test_f4_scoped_cli_never_says_the_global_path_never_exercises_the_layer(monkeypatch, tmp_path, capsys):
    _stub(monkeypatch, tmp_path)         # the stubbed history says global_with_layer == 0 for whatever ids it is given
    _scoped_main(monkeypatch, tmp_path, out=tmp_path / "w.json")
    out = capsys.readouterr().out
    assert "never exercises" not in out and "build scope:" not in out
    monkeypatch.setattr(sys, "argv", ["asset_census.py", "--layer", "L0", "--out", str(tmp_path / "full.json")])
    ac.main()
    assert "never exercises" in capsys.readouterr().out         # the unscoped message is unchanged


# F5: a census whose scope label was stripped
def test_f5_require_full_census_refuses_a_stripped_label_by_population(monkeypatch, tmp_path):
    _stub(monkeypatch, tmp_path)
    c = ac.measure("L0", assets=["bg_a"])
    c.pop("scope")
    assert c["n_assets"] < c["population_active"]
    with pytest.raises(ac.ScopeError, match="n_assets.*population_active"):
        ac.require_full_census(c, "x")
    with pytest.raises(ac.ScopeError, match="n_assets.*population_active"):
        ac.require_full_census({"L0": c}, "x")
    p = tmp_path / "stripped.json"
    p.write_text(json.dumps({"L0": c}), encoding="utf-8", )
    with pytest.raises(ac.ScopeError):
        ac.load_full_census(p)
    ac.require_full_census(ac.measure("L0"), "x")        # a genuinely full census passes


def test_f2_path_fallback_when_the_full_file_does_not_exist_yet(tmp_path):
    """No inode to compare: a case variant and a dangling symlink to the full path are still the full census path."""
    full = tmp_path / "asset_census.json"
    assert not full.exists()
    assert ac._is_full_census_path(tmp_path / "Asset_Census.JSON", full)          # case-folded fallback (conservative)
    sym = tmp_path / "dangling.json"
    sym.symlink_to(full)
    assert ac._is_full_census_path(sym, full)                                      # resolve() follows the dangling link
    assert ac._is_full_census_path(tmp_path / "sub" / ".." / "asset_census.json", full)
    assert not ac._is_full_census_path(tmp_path / "asset_census_scoped.json", full)
