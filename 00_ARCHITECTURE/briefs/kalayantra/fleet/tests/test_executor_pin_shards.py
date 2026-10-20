"""SR-CHURN-CUT 3: executor-table pin shards (append-only new files instead of edits to the 71 KB monolith pin).

Claims, one oracle each (the named production line, reverted, fails the named test):
  1. a shard's kind is REPLACED in place and a new kind is INSERTED after its `after` kind (null: appended last)  [apply_shards]
  2. a shard whose stem is not its item, whose schema is wrong or that is empty is refused  [load_shards]
  3. scaffold drafts exactly the added/changed kinds with the right anchor, refuses what it cannot anchor  [scaffold]
  4. the pin stays independent: the real table + a kind no shard names FAILS test_executor_table.assert_table_matches_pin;
     the same kind with its shard passes; a shard does not excuse any OTHER edit  [monolith wiring, §N.8]
  5. the merged shard directory loads and every shard is a real plan-model item (so a typo cannot pin nothing)
"""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FLEET = HERE.parent
sys.path.insert(0, str(FLEET))
import executor_pin_shards as eps  # noqa: E402

REPO = FLEET.parents[3]
MODEL = REPO / "00_ARCHITECTURE/control/kalayantra/plan_model.json"


def monolith():
    spec = importlib.util.spec_from_file_location("test_executor_table_for_shards", HERE / "test_executor_table.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def entry(**more):
    return {"enabled": False, "needs": "none", "script": "x.py", "fixed_args": [], "allowed_args": [], **more}


def shard(item, entries, after=None):
    return {"schema": eps.SCHEMA, "item": item, "after": after, "entries": entries}


def test_replace_in_place_insert_after_anchor_and_append_last():  # claim 1
    expected = {"a": entry(), "b": entry(), "c": entry()}
    order = ["a", "b", "c"]
    out, new_order = eps.apply_shards(expected, order, [
        shard("S1", {"b": entry(enabled=True), "n1": entry(), "n2": entry()}, after="a"),
        shard("S2", {"z": entry()}, after=None)])
    assert new_order == ["a", "n1", "n2", "b", "c", "z"]
    assert out["b"]["enabled"] is True and set(out) == {"a", "b", "c", "n1", "n2", "z"}
    assert expected["b"]["enabled"] is False and order == ["a", "b", "c"]          # the inputs are not modified
    # a replacement alone never moves the kind
    assert eps.apply_shards(expected, order, [shard("S3", {"a": entry(needs="owner")}, after="c")])[1] == order
    with pytest.raises(ValueError, match="not in the table"):
        eps.apply_shards(expected, order, [shard("S4", {"n": entry()}, after="ghost")])
    assert eps.enabled_kinds([shard("S1", {"b": entry(enabled=True), "n1": entry()})]) == {"b"}


def test_malformed_shards_are_refused(tmp_path):  # claim 2
    def put(name, doc):
        (tmp_path / name).write_text(json.dumps(doc))
    put("K1.json", shard("K1", {"k": entry()}))
    assert [s["item"] for s in eps.load_shards(tmp_path)] == ["K1"]
    for bad, doc, why in (("K2.json", shard("K9", {"k": entry()}), "file stem"),
                          ("K3.json", {**shard("K3", {"k": entry()}), "schema": "other"}, "schema"),
                          ("K4.json", shard("K4", {}), "no entries")):
        put(bad, doc)
        with pytest.raises(ValueError, match=why):
            eps.load_shards(tmp_path)
        (tmp_path / bad).unlink()
    assert eps.load_shards(tmp_path / "missing") == []


def test_scaffold_drafts_added_and_changed_kinds_with_the_anchor():  # claim 3
    base = {"ops": {"a": entry(), "b": entry(), "c": entry()}}
    now = {"ops": {"a": entry(), "n": entry(), "b": entry(needs="owner"), "c": entry()}}
    now["ops"] = {"a": entry(), "b": entry(needs="owner"), "n": entry(), "c": entry()}
    draft = eps.scaffold(base, now, "K9-77")
    assert draft["item"] == "K9-77" and draft["after"] == "b" and list(draft["entries"]) == ["b", "n"]
    assert eps.apply_shards(base["ops"], list(base["ops"]), [draft])[0] == now["ops"]
    appended = {"ops": {**base["ops"], "z": entry()}}
    assert eps.scaffold(base, appended, "K9-78")["after"] is None
    with pytest.raises(ValueError, match="nothing to pin"):
        eps.scaffold(base, base, "K9-79")
    with pytest.raises(ValueError, match="no anchor"):
        eps.scaffold(base, {"ops": {"first": entry(), **base["ops"]}}, "K9-80")
    with pytest.raises(ValueError, match="contiguous"):
        eps.scaffold(base, {"ops": {"a": entry(), "x": entry(), "b": entry(), "y": entry(), "c": entry()}}, "K9-81")


def test_the_pin_is_not_regenerated_from_the_table_it_checks():  # claim 4
    mod = monolith()
    now = mod.load_ops(mod.OPS_FILE.read_text())
    mod.assert_table_matches_pin(now)                                   # the live table passes today
    new_kind = copy.deepcopy(now["ops"]["measuring_dispatch_dryrun"])
    new_kind["enabled"] = False
    grown = copy.deepcopy(now)
    grown["ops"]["brand_new_kind"] = new_kind
    with pytest.raises(AssertionError, match="set of kinds"):            # no shard names it: refused, as before
        mod.assert_table_matches_pin(grown)
    named = [shard("K9-TEST", {"brand_new_kind": new_kind})]
    mod.assert_table_matches_pin(grown, named)                          # the reviewed shard excuses exactly that kind
    sneaky = copy.deepcopy(grown)
    sneaky["ops"]["brand_new_kind"]["script"] = "other.py"
    with pytest.raises(AssertionError, match="brand_new_kind.script"):   # ...and exactly its reviewed content
        mod.assert_table_matches_pin(sneaky, named)
    other = copy.deepcopy(grown)
    other["ops"]["finalize"]["needs"] = "pgenv"
    with pytest.raises(AssertionError, match="finalize.needs"):          # a shard excuses no other edit
        mod.assert_table_matches_pin(other, named)
    ordered = list(now["ops"])
    placed = copy.deepcopy(now)
    placed["ops"] = {k: (new_kind if k == "brand_new_kind" else now["ops"][k]) for k in ordered[:2] + ["brand_new_kind"] + ordered[2:]}
    mod.assert_table_matches_pin(placed, [shard("K9-TEST", {"brand_new_kind": new_kind}, after=ordered[1])])
    with pytest.raises(AssertionError, match="order"):                   # the anchor is part of the pin
        mod.assert_table_matches_pin(placed, [shard("K9-TEST", {"brand_new_kind": new_kind}, after=ordered[0])])


def test_merged_shards_load_and_name_real_plan_items():  # claim 5
    ids = {i["id"] for i in json.loads(MODEL.read_text())["items"]}
    for doc in eps.load_shards():
        assert doc["item"] in ids, doc["item"]
        for kind, e in doc["entries"].items():
            assert next(iter(e)) == "enabled", kind
