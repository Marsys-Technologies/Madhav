"""SR-CHURN-CUT 3: executor-table pin shards (append-only new files instead of edits to the 71 KB monolith pin).

Claims, one oracle each (the named production line, reverted, fails the named test):
  1. a shard's kind is REPLACED in place and a new kind is INSERTED after its `after` kind (null: appended last)  [apply_shards]
  2. a shard whose stem is not its item, whose schema is wrong or that is empty is refused  [load_shards]
  3. scaffold drafts exactly the added/changed kinds with the right anchor, refuses what it cannot anchor  [scaffold]
  4. the pin stays independent: the real table + a kind no shard names FAILS test_executor_table.assert_table_matches_pin;
     the same kind with its shard passes; a shard does not excuse any OTHER edit  [monolith wiring, §N.8]
  5. the merged shard directory loads and every shard is a real plan-model item (so a typo cannot pin nothing)

SR-CHURN-CUT 5 (schema /2: classes, w4_bindings, function_hashes; the census tests fold the shards), one oracle each:
  6. a /2 shard's `classes` replace a kind's class set and change the expected signed-only set; planting `century_cancel` out of
     executor.SIGNED_ONLY_KINDS fails test_executor_mechanical_production (MECHANICAL_ACCEPTANCE_v1_0.md: the cancels are signed-only)  [classes_after]
  7. a `function_hashes` shard REPLACES one digest: the boundary test accepts the function body the shard names and refuses every other  [hashes_after]
  8. `scaffold` never emits a class or a digest; a shard that still carries a "TODO" placeholder is refused  [scaffold, load_shards]
  9. w4_after / hashes_after / classes_after / enabled_after are pure: a later shard replaces, a kind no shard names keeps its BASE, inputs are untouched
 10. the shard layer is wired to the table: `check` finds a shard entry the table does not carry
 11. the merge proof: two branches that each add one distinct kind with its own shard merge with no textual conflict (git merge-tree, read-only),
     touch no census test, and the folded pin passes on the merged table
 12. executor.py's kind sets and its validate() chain stay one element per line, sorted (what makes two additions a non-conflicting merge)
"""
import ast
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
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


def shard(item, entries, after=None):      # a schema /1 shard: still valid under /2
    return {"schema": eps.SCHEMA_1, "item": item, "after": after, "entries": entries}


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
        for kind, e in (doc.get("entries") or {}).items():      # a /2 shard may carry classes or digests only
            assert next(iter(e)) == "enabled", kind


# ───────────────────────────── SR-CHURN-CUT 5 ─────────────────────────────

REAL_SHARDS = eps.load_shards()       # the shards in the tree under test: the baseline every "plus one more shard" below is measured against


def shard2(item, **keys):
    return {"schema": eps.SCHEMA, "item": item, "after": None, **keys}


def fresh(name, filename, monkeypatch, shards):
    """A test module re-imported while `load_shards` returns `shards`: its folded census as that shard set would leave it."""
    monkeypatch.setattr(eps, "load_shards", lambda directory=eps.SHARD_DIR: shards)
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_classes_replace_in_full_and_change_the_expected_signed_only_set(tmp_path, monkeypatch):  # claim 6
    base = {"a": ["signed_only", "teardown"], "b": ["remote_async"]}
    out = eps.classes_after(base, [shard2("S1", classes={"a": ["cancel_lane"], "c": ["signed_only", "mechanical_exempt"]}),
                                   shard2("S2", classes={"b": []})])
    assert out == {"a": ["cancel_lane"], "c": ["mechanical_exempt", "signed_only"]}       # the full set replaces; [] removes every class
    assert base == {"a": ["signed_only", "teardown"], "b": ["remote_async"]}              # the input is not modified
    assert eps.kinds_with(out, "signed_only") == {"c"}
    # through the real census test: a shard that takes century_cancel out of signed_only changes what the test expects of executor.py
    real = fresh("mp_real", "test_executor_mechanical_production.py", monkeypatch, REAL_SHARDS)
    assert "century_cancel" in real.SIGNED_ONLY
    gone = [*REAL_SHARDS, shard2("ZZ-LAST", classes={"century_cancel": ["cancel_lane", "mechanical_exempt"]})]
    changed = fresh("mp_changed", "test_executor_mechanical_production.py", monkeypatch, gone)
    assert changed.SIGNED_ONLY == real.SIGNED_ONLY - {"century_cancel"}
    w, table = real.build(tmp_path, monkeypatch)
    real.oracle_x2_serving_and_cancel(w, table)                                            # the real executor satisfies the unshardowed expectation
    with pytest.raises(AssertionError, match="signed_only class"):                         # ...and not the shard's: the expectation follows the shard, not the code
        changed.oracle_x2_serving_and_cancel(w, table)


def test_a_function_hashes_shard_replaces_one_digest_and_the_boundary_test_follows_it(monkeypatch):  # claim 7
    real_src = (FLEET / "executor.py").read_text()
    segment = ast.get_source_segment(real_src, next(n for n in ast.parse(real_src).body if isinstance(n, ast.FunctionDef) and n.name == "canonical_sha"))
    altered_segment = segment.replace("sort_keys=True", "sort_keys=False")
    assert altered_segment != segment
    altered_src = real_src.replace(segment, altered_segment, 1)
    digest = hashlib.sha256(altered_segment.encode()).hexdigest()
    plain = fresh("tt_plain", "test_executor_table.py", monkeypatch, REAL_SHARDS)
    base = plain.base_text(plain.PY_REL)
    assert plain.boundary_violations(base, real_src) == []
    assert plain.boundary_violations(base, altered_src), "an altered reviewed function must fail the boundary test"
    replaced = fresh("tt_replaced", "test_executor_table.py", monkeypatch, [*REAL_SHARDS, shard2("ZZ-LAST", function_hashes={"W4": {"canonical_sha": digest}})])
    assert replaced.W4_FUNCTION_HASHES["canonical_sha"] == digest != plain.W4_FUNCTION_HASHES["canonical_sha"]
    assert replaced.boundary_violations(base, altered_src) == []                       # the digest the shard names is the one reviewed body
    assert replaced.boundary_violations(base, real_src), "the replaced digest no longer admits the old body"
    assert replaced.K9_FUNCTION_HASHES == plain.K9_FUNCTION_HASHES and replaced.W4_FUNCTION_HASHES.keys() == plain.W4_FUNCTION_HASHES.keys()


def test_scaffold_never_fills_classes_or_digests_and_a_placeholder_shard_is_refused(tmp_path):  # claim 8
    base = {"ops": {"a": entry(), "b": entry()}}
    now = {"ops": {"a": entry(), "b": entry(), "n": entry(enabled=True)}}
    draft = eps.scaffold(base, now, "K9-90")
    assert draft["schema"] == eps.SCHEMA and list(draft["entries"]) == ["n"]
    assert draft["classes"] == {"n": eps.PLACEHOLDER} and draft["function_hashes"] == {"W4": {eps.PLACEHOLDER: eps.PLACEHOLDER}}
    text = json.dumps(draft)
    assert not any(name in text for name in eps.CLASS_NAMES) and not any(len(w) == 64 for w in text.replace('"', " ").split())
    (tmp_path / "K9-90.json").write_text(json.dumps(draft))
    with pytest.raises(ValueError, match="placeholder"):
        eps.load_shards(tmp_path)
    for key in ("classes", "function_hashes"):                                               # each placeholder is refused on its own
        only = {k: v for k, v in draft.items() if k != ("function_hashes" if key == "classes" else "classes")}
        (tmp_path / "K9-90.json").write_text(json.dumps(only))
        with pytest.raises(ValueError, match="placeholder"):
            eps.load_shards(tmp_path)
    reviewed = {**draft, "classes": {"n": ["no_dryrun"]}}
    del reviewed["function_hashes"]
    (tmp_path / "K9-90.json").write_text(json.dumps(reviewed))
    assert eps.load_shards(tmp_path)[0]["classes"] == {"n": ["no_dryrun"]}                    # replaced by a reviewed value, it loads


@pytest.mark.parametrize("key,value,why", [
    ("classes", {"k": ["not_a_class"]}, "classes"),
    ("classes", {"k": ["signed_only", "signed_only"]}, "classes"),
    ("w4_bindings", {"k": ["owner", "s.py", [], []]}, "w4_bindings"),
    ("w4_bindings", {"k": ["owner", "s.py", [], [], "yes", None]}, "w4_bindings"),
    ("function_hashes", {"W4": {"f": "abc"}}, "function_hashes"),
    ("function_hashes", {"X9": {"f": "0" * 64}}, "function_hashes"),
    ("rebase", False, "rebase"),
])
def test_malformed_v2_keys_and_v1_shards_carrying_them_are_refused(tmp_path, key, value, why):  # claim 8
    (tmp_path / "K1.json").write_text(json.dumps(shard2("K1", entries={"k": entry()}, **{key: value})))
    with pytest.raises(ValueError, match=why):
        eps.load_shards(tmp_path)
    (tmp_path / "K1.json").write_text(json.dumps({**shard("K1", {"k": entry()}), key: value}))
    with pytest.raises(ValueError, match="needs schema"):
        eps.load_shards(tmp_path)


def test_a_w4_binding_must_agree_with_the_entry_it_accompanies(tmp_path):  # claim 8
    good = ["none", "x.py", [], [], False, None]       # entry() is needs "none", script "x.py"
    (tmp_path / "K1.json").write_text(json.dumps(shard2("K1", entries={"k": entry()}, w4_bindings={"k": good})))
    assert eps.load_shards(tmp_path)[0]["w4_bindings"] == {"k": good}
    (tmp_path / "K1.json").write_text(json.dumps(shard2("K1", entries={"k": entry()}, w4_bindings={"k": ["none", "other.py", [], [], False, None]})))
    with pytest.raises(ValueError, match="disagrees"):
        eps.load_shards(tmp_path)


def test_folding_helpers_are_pure_and_a_later_shard_replaces(tmp_path):  # claim 9
    h_base = {"W4": {"f": "1" * 64, "g": "2" * 64}, "K9": {"h": "3" * 64}}
    w_base = {"k": ["owner", "a.py", [], [], True, 5]}
    s1 = shard2("S1", function_hashes={"W4": {"f": "4" * 64, "n": "5" * 64}}, w4_bindings={"k": ["owner", "b.py", [], [], True, 5], "m": ["none", "c.py", [], [], False, None]},
                entries={"k": entry(enabled=True, production=True), "m": entry(enabled=True, production=False), "z": entry(enabled=False)})
    s2 = shard2("S2", function_hashes={"W4": {"f": "6" * 64}, "K9": {"h": "7" * 64}}, entries={"m": entry(enabled=False)})
    hashes = eps.hashes_after(h_base, [s1, s2])
    assert hashes == {"W4": {"f": "6" * 64, "g": "2" * 64, "n": "5" * 64}, "K9": {"h": "7" * 64}}
    assert h_base == {"W4": {"f": "1" * 64, "g": "2" * 64}, "K9": {"h": "3" * 64}}
    assert eps.w4_after(w_base, [s1]) == {"k": ["owner", "b.py", [], [], True, 5], "m": ["none", "c.py", [], [], False, None]}
    assert w_base == {"k": ["owner", "a.py", [], [], True, 5]}
    base_kinds = {"x", "k"}
    assert eps.enabled_after(base_kinds, [s1]) == {"x", "k", "m"} and eps.enabled_after(base_kinds, [s1, s2]) == {"x", "k"}   # the LAST entry per kind decides
    assert base_kinds == {"x", "k"}
    assert eps.production_after({"x"}, [s1, s2]) == {"x", "k"}
    assert eps.hashes_after(h_base, []) == h_base and eps.classes_after({}, []) == {}
    # a /2 shard that carries only a digest (no entries) is valid; one with nothing is not
    (tmp_path / "K1.json").write_text(json.dumps(shard2("K1", function_hashes={"W4": {"f": "6" * 64}})))
    assert eps.load_shards(tmp_path)[0]["item"] == "K1"
    (tmp_path / "K1.json").write_text(json.dumps(shard2("K1")))
    with pytest.raises(ValueError, match="no entries"):
        eps.load_shards(tmp_path)


def test_check_finds_a_shard_entry_the_table_does_not_carry_and_prints_the_folded_census(capsys):  # claim 10
    table = {"ops": {"a": entry(), "n": entry(enabled=True)}}
    ok = [shard2("S1", entries={"n": entry(enabled=True)}, classes={"n": ["no_dryrun"]})]
    assert eps.check(ok, table) == []
    later = ok + [shard2("S2", entries={"n": entry(enabled=False)})]
    assert eps.check(later, table) == ["n: the table entry differs from the last shard that names it"]
    assert eps.check([shard2("S3", entries={"ghost": entry()})], table) == ["ghost: named by a shard but absent from the table"]
    assert eps.check([shard2("S4", classes={"ghost": ["teardown"]})], table) == ["S4: classes names 'ghost', which is not in the table"]
    text = eps.census(later)
    assert "shard S1" in text and "shard S2" in text and '"n": ["no_dryrun"]' in text and "enabled by shards: []" in text
    assert eps.main(["check"]) == 0                                                          # the real shards against the real table
    assert "classes (shards only)" in capsys.readouterr().out


def _git(repo, *args, check=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="f", GIT_AUTHOR_EMAIL="f@example.invalid",
               GIT_COMMITTER_NAME="f", GIT_COMMITTER_EMAIL="f@example.invalid")
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    assert done.returncode == 0 or not check, done.stderr
    return done.stdout.strip()


CENSUS_TESTS = ("test_executor_table.py", "test_operation_adapters.py", "test_executor_a8.py", "test_operation_dryrun.py",
                "test_executor_mechanical_production.py", "test_executor_mechanical_acceptance.py", "test_w4_smalltest_enablement.py")
OPS_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/executor_ops.json"
SHARD_REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/tests/executor_pin_shards/"


def test_two_kind_branches_merge_with_no_textual_conflict_and_the_folded_pin_passes(tmp_path):  # claim 11
    rel = "00_ARCHITECTURE/briefs/kalayantra/fleet/"
    repo = tmp_path / "r"
    for name in ("executor_ops.json", "executor.py", "executor_pin_shards.py"):
        (repo / rel / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel / name).write_bytes((FLEET / name).read_bytes())
    for name in CENSUS_TESTS:
        (repo / rel / "tests" / name).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel / "tests" / name).write_bytes((HERE / name).read_bytes())
    (repo / SHARD_REL).mkdir(parents=True, exist_ok=True)
    (repo / SHARD_REL / "README.md").write_text("readme\n")
    for existing in eps.SHARD_DIR.glob("*.json"):                   # the merged shards of the PR head are part of the common ancestor
        (repo / SHARD_REL / existing.name).write_bytes(existing.read_bytes())
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "pr head")
    start = _git(repo, "rev-parse", "HEAD")
    ops_text = (repo / OPS_REL).read_text()
    kinds = list(json.loads(ops_text)["ops"])

    def add_kind(branch, kind, anchor):
        """One branch = one new kind inserted right after `anchor` in executor_ops.json, plus its own shard. Nothing else."""
        _git(repo, "checkout", "-q", "-b", branch, start)
        new_entry = {"enabled": False, "needs": "none", "script": "00_ARCHITECTURE/briefs/kalayantra/fleet/http_probe.py", "fixed_args": [], "allowed_args": ["probe"],
                     "requesters": ["adhikarin"], "production": False, "read_only": True, "timeout_s": 300, "enabled_by": "J-6l"}
        lines = ops_text.split("\n")
        at = next(n for n, line in enumerate(lines) if line.lstrip().startswith(f'"{anchor}":'))
        assert lines[at].endswith(","), "the anchor entry is one line and not the last"
        lines.insert(at + 1, f'    "{kind}": {json.dumps(new_entry)},')       # the table is one entry per line: a kind PR adds one line
        (repo / OPS_REL).write_text("\n".join(lines))
        shard_doc = shard2(branch.upper(), after=anchor, entries={kind: new_entry}, classes={kind: ["dryrun_census"]} if kind.endswith("_dryrun") else {})
        (repo / SHARD_REL / f"{branch.upper()}.json").write_text(json.dumps(shard_doc, indent=2) + "\n")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", branch)
        return _git(repo, "rev-parse", "HEAD")

    a = add_kind("kind-a", "synthetic_kind_a", kinds[2])
    b = add_kind("kind-b", "synthetic_kind_b", kinds[-3])
    merged = _git(repo, "merge-tree", start, a, b)                  # the old three-argument form: read-only, prints the merged result
    assert "changed in both" in merged       # both branches edited executor_ops.json (a read-only 3-way merge reports such a file either way) ...
    assert not [l for l in merged.splitlines() if l[1:].startswith(("<<<<<<<", ">>>>>>>"))], merged[:1500]       # ... and no hunk of it carries a conflict marker
    _git(repo, "checkout", "-q", "-b", "merged", a)
    _git(repo, "merge", "-q", "--no-edit", b)
    touched = set(_git(repo, "diff", "--name-only", start, "merged").splitlines())
    assert touched == {OPS_REL, SHARD_REL + "KIND-A.json", SHARD_REL + "KIND-B.json"}, touched    # no census test, executor.py or module is edited by either branch
    merged_ops = json.loads((repo / OPS_REL).read_text())
    shards = eps.load_shards(repo / SHARD_REL)
    assert [s["item"] for s in shards if s["item"] not in {r["item"] for r in REAL_SHARDS}] == ["KIND-A", "KIND-B"]
    assert {"synthetic_kind_a", "synthetic_kind_b"} <= set(merged_ops["ops"])
    assert eps.check(shards, merged_ops) == []
    mod = monolith()
    mod.assert_table_matches_pin(merged_ops, shards)                # the folded table pin passes on the merged table, with both kinds placed where their shards say
    with pytest.raises(AssertionError):
        mod.assert_table_matches_pin(merged_ops, shards[:1])        # ...and not with a shard missing: each kind is pinned by its own shard


def _kind_set_nodes(tree, name):
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == name for t in n.targets))
    value = node.value
    return value.args[0].elts if isinstance(value, ast.Call) else value.elts


def test_executor_kind_sets_and_the_validate_chain_are_one_element_per_line_and_sorted():  # claim 12
    tree = ast.parse((FLEET / "executor.py").read_text())
    for name in ("SIGNED_ONLY_KINDS", "REMOTE_ASYNC_KINDS", "TEARDOWN_KINDS", "FENCE_EXEMPT_KINDS"):
        elts = _kind_set_nodes(tree, name)
        values = [e.value for e in elts]
        assert values == sorted(values) and len(set(values)) == len(values), name
        assert len({e.lineno for e in elts}) == len(elts), f"{name}: two elements share a line"
    validate = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate")
    loop = next(n for n in ast.walk(validate) if isinstance(n, ast.For) and isinstance(n.iter, ast.Tuple) and all(isinstance(e, ast.Lambda) for e in n.iter.elts))
    checks = [ast.unparse(e.body).split("(")[0] for e in loop.iter.elts]
    assert checks == sorted(checks) and len({e.lineno for e in loop.iter.elts}) == len(checks)
    # century_contract_problem and smalltest_policy_problem both admit century_dispatch: the contract's reason must stay first
    assert checks.index("century_contract_problem") < checks.index("smalltest_policy_problem")
