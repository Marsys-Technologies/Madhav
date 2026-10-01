"""E6.3 -- the LEVEL_MAP.json / FAMILY_ASSETS.json generators (00_ARCHITECTURE/control/generate_level_map.py).

Levels are longest-path depth in the dependency DAG of the ACTIVE registry assets; a cycle (or a dangling edge) is an
error, never level 0; family_set is the union of the six lists; both documents have EXACTLY the pinned key schema.
No database: the registry is an input (JSON rows, or the repo's seed file parsed as text).
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[4]
CTRL = REPO / "00_ARCHITECTURE" / "control"
SEED = REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"
FRESH = "2026-10-02T12:00:00+00:00"


def _load():
    import os
    path = pathlib.Path(os.environ.get("E6_3_GENERATOR_UNDER_TEST") or CTRL / "generate_level_map.py")
    spec = importlib.util.spec_from_file_location("generate_level_map_e6_3", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["generate_level_map_e6_3"] = mod
    spec.loader.exec_module(mod)
    return mod


G = _load()


def row(aid, deps=(), layer="bodha", active=True):
    return dict(asset_id=aid, layer=layer, depends_on=list(deps), active=active)


DIAMOND = [row("bg_a", layer="brahmagyan"), row("ga_b", ["bg_a"], "ganita"), row("ga_c", ["bg_a"], "ganita"),
           row("bo_d", ["ga_b", "ga_c"]), row("bo_e", ["bg_a", "bo_d"]), row("bo_f", ["ga_b"])]


# ───────────────────────── levels ─────────────────────────

def test_roots_are_level_zero_and_levels_are_longest_path_depth():
    assert G.compute_levels(DIAMOND) == {"bg_a": 0, "bo_d": 2, "bo_e": 3, "bo_f": 2, "ga_b": 1, "ga_c": 1}


def test_longest_path_not_shortest_path():
    # bo_e depends on bg_a (level 0) AND on bo_d (level 2): shortest-path depth would say 1
    assert G.compute_levels(DIAMOND)["bo_e"] == 3


def test_a_long_chain_does_not_hit_a_recursion_limit():
    rows = [row("bg_n0")] + [row(f"bg_n{i}", [f"bg_n{i - 1}"]) for i in range(1, 3000)]
    assert G.compute_levels(rows)["bg_n2999"] == 2999


def test_input_order_does_not_change_the_result():
    assert G.compute_levels(list(reversed(DIAMOND))) == G.compute_levels(DIAMOND)


@pytest.mark.parametrize("rows,needle", [
    ([row("bg_a", ["bg_b"]), row("bg_b", ["bg_a"])], "cycle"),
    ([row("bg_a", ["bg_a"])], "cycle"),
    ([row("bg_a", ["bg_b"]), row("bg_b", ["bg_c"]), row("bg_c", ["bg_a"]), row("bg_free")], "cycle"),
    ([row("bg_root"), row("ga_x", ["bg_root", "ga_y"]), row("ga_y", ["ga_z"]), row("ga_z", ["ga_x"])], "cycle"),
])
def test_a_dependency_cycle_is_an_error_never_level_zero(rows, needle):
    with pytest.raises(G.LevelMapError, match=needle):
        G.compute_levels(rows)


def test_the_cycle_error_names_the_cycle():
    with pytest.raises(G.LevelMapError) as e:
        G.compute_levels([row("bg_a", ["bg_b"]), row("bg_b", ["bg_a"])])
    assert "bg_a" in str(e.value) and "bg_b" in str(e.value)


def test_an_edge_to_an_unknown_asset_is_an_error():
    with pytest.raises(G.LevelMapError, match="does not hold"):
        G.compute_levels([row("bg_a", ["bg_ghost"])])


def test_an_edge_to_an_inactive_asset_is_an_error_not_a_silently_dropped_edge():
    with pytest.raises(G.LevelMapError, match="inactive"):
        G.compute_levels([row("bg_a"), row("bg_old", active=False), row("ga_b", ["bg_old"])])


def test_inactive_assets_are_not_in_the_map_and_their_own_edges_are_not_examined():
    rows = [row("bg_a"), row("bg_old", ["bg_ghost"], active=False), row("ga_b", ["bg_a"])]
    assert G.compute_levels(rows) == {"bg_a": 0, "ga_b": 1}


def test_no_active_asset_is_an_error():
    with pytest.raises(G.LevelMapError):
        G.compute_levels([row("bg_a", active=False)])


@pytest.mark.parametrize("bad", [
    [], "x", [1], [{"asset_id": "bg_a"}], [row("bg_a"), row("bg_a")], [row("BG_A")], [dict(row("bg_a"), active="yes")],
    [dict(row("bg_a"), depends_on="bg_b")], [dict(row("bg_a"), depends_on=["bg_b", "bg_b"])],
    [dict(row("bg_a"), layer="")],
])
def test_a_malformed_registry_is_refused(bad):
    with pytest.raises(G.LevelMapError):
        G.compute_levels(bad)


# ───────────────────────── LEVEL_MAP.json ─────────────────────────

def test_level_map_key_schema_is_exact():
    lm = G.build_level_map(DIAMOND, version="1.0", frozen_at=FRESH, registry_revision=7)
    assert list(lm) == ["version", "frozen_at", "registry_revision", "levels"]
    assert lm == {"version": "1.0", "frozen_at": FRESH, "registry_revision": 7,
                  "levels": {"bg_a": 0, "bo_d": 2, "bo_e": 3, "bo_f": 2, "ga_b": 1, "ga_c": 1}}
    assert list(lm["levels"]) == sorted(lm["levels"])


@pytest.mark.parametrize("kw", [dict(version=""), dict(frozen_at="2026-10-02"), dict(frozen_at="2026-10-02T12:00:00"),
                                dict(frozen_at=5), dict(registry_revision=0), dict(registry_revision=True),
                                dict(registry_revision="7")])
def test_level_map_metadata_is_validated(kw):
    args = dict(version="1.0", frozen_at=FRESH, registry_revision=7)
    args.update(kw)
    with pytest.raises(G.LevelMapError):
        G.build_level_map(DIAMOND, **args)


# ───────────────────────── FAMILY_ASSETS.json ─────────────────────────

REG = [row("ka_gochara", layer="kala"), row("ka_gochara_resonance", layer="kala"), row("ka_sangam", layer="kala"),
       row("ka_kshetra", layer="kala"), row("ka_reader", layer="kala"), row("ph_reader", layer="phala"),
       row("mi_reader", layer="mimamsa"), row("bo_other")]
LISTS = dict(family_gochara=["ka_gochara_resonance", "ka_gochara"], family_sangam=["ka_sangam"],
             family_kshetra=["ka_kshetra"], family_readers_L3=["ka_reader", "ka_gochara"],
             family_readers_L4=["ph_reader"], family_readers_L5=["mi_reader"])


def test_family_assets_key_schema_is_exact_and_family_set_is_the_union_of_the_six():
    fa = G.build_family_assets(LISTS, REG, version="1.0", frozen_at=FRESH, registry_revision=7)
    assert list(fa) == ["version", "frozen_at", "registry_revision", "family_gochara", "family_sangam", "family_kshetra",
                        "family_readers_L3", "family_readers_L4", "family_readers_L5", "family_set"]
    union = set()
    for k in ("family_gochara", "family_sangam", "family_kshetra", "family_readers_L3", "family_readers_L4",
              "family_readers_L5"):
        union |= set(fa[k])
    assert fa["family_set"] == sorted(union)
    assert "ka_gochara" in fa["family_readers_L3"] and fa["family_set"].count("ka_gochara") == 1   # union, no duplicate
    assert "bo_other" not in fa["family_set"]


def test_an_empty_list_is_allowed_when_it_is_present_but_a_missing_or_extra_key_is_refused():
    ok = dict(LISTS, family_sangam=[])
    assert G.build_family_assets(ok, REG, version="1.0", frozen_at=FRESH, registry_revision=7)["family_sangam"] == []
    missing = {k: v for k, v in LISTS.items() if k != "family_kshetra"}
    with pytest.raises(G.LevelMapError):
        G.build_family_assets(missing, REG, version="1.0", frozen_at=FRESH, registry_revision=7)
    with pytest.raises(G.LevelMapError):
        G.build_family_assets(dict(LISTS, family_extra=["ka_reader"]), REG, version="1.0", frozen_at=FRESH, registry_revision=7)


def test_provenance_notes_prefixed_with_underscore_are_ignored():
    fa = G.build_family_assets(dict(LISTS, _provenance="note"), REG, version="1.0", frozen_at=FRESH, registry_revision=7)
    assert "_provenance" not in fa


@pytest.mark.parametrize("patch,why", [
    (dict(family_sangam=["ka_ghost"]), "not in the registry"),
    (dict(family_sangam=["bo_other", "bo_other"]), "duplicate in a list"),
    (dict(family_readers_L4=["ka_reader"]), "reader in the wrong layer"),
    (dict(family_readers_L5=["ph_reader"]), "reader in the wrong layer"),
    (dict(family_gochara="ka_gochara"), "not a list"),
])
def test_family_membership_is_validated_against_the_active_registry(patch, why):
    with pytest.raises(G.LevelMapError):
        G.build_family_assets(dict(LISTS, **patch), REG, version="1.0", frozen_at=FRESH, registry_revision=7)


def test_an_inactive_registry_asset_cannot_be_a_family_member():
    reg = [r if r["asset_id"] != "ka_sangam" else dict(r, active=False) for r in REG]
    with pytest.raises(G.LevelMapError):
        G.build_family_assets(LISTS, reg, version="1.0", frozen_at=FRESH, registry_revision=7)


# ───────────────────────── the committed draft family input ─────────────────────────

def test_the_committed_family_input_validates_and_names_the_documented_sets():
    data = json.loads((CTRL / "family_lists_input.json").read_text(encoding="utf-8"))
    lists = G.validate_family_input(data)
    assert set(lists["family_gochara"]) == {"ka_gochara", "ka_gochara_resonance", "ka_vedha_gochara"}
    assert lists["family_sangam"] == ["ka_sangam"] and lists["family_kshetra"] == ["ka_kshetra"]
    assert len(set().union(*[set(v) for v in lists.values()])) == 18          # 5 family assets + the 13 other readers
    assert "_provenance" in data and "OPEN" in data["_provenance"]


# ───────────────────────── the repo seed as a stand-in registry ─────────────────────────

def test_the_seed_loader_parses_every_asset_and_reproduces_the_measured_family_levels():
    rows = G.load_registry_from_seed(SEED)
    assert len(rows) > 100 and all(set(r) == {"asset_id", "layer", "depends_on", "active"} for r in rows)
    levels = G.compute_levels(rows)
    # arch 6.1 (measured 2026-09-28/29): family assets at levels 1, 1, 5, 12, 13; 27 levels in all
    assert [levels[a] for a in ("ka_gochara_resonance", "ka_vedha_gochara", "ka_gochara", "ka_kshetra", "ka_sangam")] == [1, 1, 5, 12, 13]
    assert max(levels.values()) + 1 == 27


def test_the_seed_loader_handles_comments_strings_and_nested_braces(tmp_path):
    seed = tmp_path / "seed.ts"
    seed.write_text("""
export const ASSETS: AssetDef[] = [
  { asset_id: 'bg_a', layer: 'brahmagyan', english_description: "it's a // not-a-comment, [x]",
    expected_volume_inputs: { A: 1, nested: { b: [1, 2] } }, depends_on: [], scope: 'global', is_active: true },
  // asset_id: 'bg_commented', depends_on: ['nope']
  { asset_id: 'ga_b', layer: 'ganita', depends_on: ['bg_a' /* trailing note */, ], is_active: false },
]
export const COEFFICIENTS = []
""", encoding="utf-8")
    assert G.load_registry_from_seed(seed) == G.validate_registry(
        [row("bg_a", [], "brahmagyan"), row("ga_b", ["bg_a"], "ganita", False)])


def test_the_seed_parser_reads_the_asset_kind_with_asset_kind_winning_over_asset_type():
    rows = G.parse_seed_text("""export const ASSETS: AssetDef[] = [
      { asset_id: 'bg_a', layer: 'brahmagyan', depends_on: [], is_active: true },
      { asset_id: 'bg_b', layer: 'brahmagyan', depends_on: [], is_active: true, asset_type: 'service' },
      { asset_id: 'bg_c', layer: 'brahmagyan', depends_on: [], is_active: true, asset_type: 'data', asset_kind: 'artifact' },
    ]""")
    assert [r["asset_kind"] for r in rows] == ["data", "service", "artifact"]


def test_the_real_seed_has_service_assets_the_tracker_can_see():
    kinds = {r["asset_id"]: r["asset_kind"] for r in G.parse_seed_text(SEED.read_text(encoding="utf-8"))}
    assert "service" in kinds.values() and kinds["bg_ontology"] == "data"


@pytest.mark.parametrize("body", [
    "{ asset_id: 'bg_a', layer: 'brahmagyan', is_active: true }",                               # no depends_on
    "{ asset_id: 'bg_a', layer: 'brahmagyan', depends_on: [...OTHER], is_active: true }",       # spread
    "{ asset_id: 'bg_a', layer: 'brahmagyan', depends_on: [], is_active: flag }",               # not a literal
    "{ asset_id: NAME, layer: 'brahmagyan', depends_on: [], is_active: true }",
])
def test_the_seed_loader_refuses_what_it_cannot_read_exactly(tmp_path, body):
    seed = tmp_path / "seed.ts"
    seed.write_text(f"export const ASSETS: AssetDef[] = [\n  {body},\n]\n", encoding="utf-8")
    with pytest.raises(G.LevelMapError):
        G.load_registry_from_seed(seed)


# ───────────────────────── the CLI ─────────────────────────

def _run(tmp_path, rows=DIAMOND + REG, lists=LISTS, extra=()):
    reg = tmp_path / "registry.json"
    fam = tmp_path / "family.json"
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    reg.write_text(json.dumps(rows), encoding="utf-8")
    fam.write_text(json.dumps(lists), encoding="utf-8")
    rc = G.main(["--registry-json", str(reg), "--family-input", str(fam), "--out-dir", str(out), "--frozen-at", FRESH,
                 "--registry-revision", "7", *extra])
    return rc, out


def test_cli_writes_both_files_with_the_pinned_keys(tmp_path, capsys):
    rc, out = _run(tmp_path)
    assert rc == 0
    lm = json.loads((out / "LEVEL_MAP.json").read_text(encoding="utf-8"))
    fa = json.loads((out / "FAMILY_ASSETS.json").read_text(encoding="utf-8"))
    assert list(lm) == ["version", "frozen_at", "registry_revision", "levels"] and lm["levels"]["bo_e"] == 3
    assert fa["family_set"] == sorted(set(fa["family_set"])) and "ka_sangam" in fa["family_set"]
    assert (out / "LEVEL_MAP.json").read_text(encoding="utf-8").endswith("}\n")


def test_cli_a_cycle_writes_nothing_and_exits_2(tmp_path, capsys):
    rc, out = _run(tmp_path, rows=[row("bg_a", ["bg_b"]), row("bg_b", ["bg_a"])] + REG)
    assert rc == 2 and list(out.iterdir()) == []
    assert "cycle" in capsys.readouterr().err


def test_cli_a_family_error_writes_neither_file(tmp_path):
    rc, out = _run(tmp_path, lists=dict(LISTS, family_sangam=["ka_ghost"]))
    assert rc == 2 and list(out.iterdir()) == []


def test_cli_refuses_to_overwrite_a_frozen_file_without_force(tmp_path):
    assert _run(tmp_path)[0] == 0
    rc, out = _run(tmp_path)
    assert rc == 2
    assert _run(tmp_path, extra=("--force",))[0] == 0


def test_cli_default_registry_revision_is_the_census_pin_read_as_source():
    assert G._default_registry_revision() >= 7
