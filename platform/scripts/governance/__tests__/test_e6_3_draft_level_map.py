"""E6.3 (SS ruling N-97 item 6): the DRAFT, pre-J1 LEVEL_MAP.json and FAMILY_ASSETS.json.

Offline, no database. The two files are generated (never hand-edited) by 00_ARCHITECTURE/control/generate_level_map.py, driven
by 00_ARCHITECTURE/control/regenerate_draft_level_map.py from the committed registry input (registry_input_draft.json) and
family input (family_lists_input.json). What is guarded here:

  fresh regeneration  the committed files equal a regeneration byte for byte, and the generator's own CLI makes the same bytes
  draft + stamp       both files say DRAFT and carry the registry revision AND fingerprint they were generated at. A DRAFT
                      whose recorded revision/fingerprint is behind asset_census is STALE: a pytest warning, never a failure
                      (engine PRs bump the revision constantly); any other status (the J1 freeze) FAILS on staleness. The
                      regeneration is made AT THE RECORDED stamp, so a stale draft still byte-equals it. A wrong registry-input
                      hash stays a failure
  coverage            every one of the 127 active registry assets appears exactly once in the level map
  levels              level == longest-path depth: strictly above every dependency, contiguous from 0
  family              family assets are marked (FAMILY_ASSETS.json) and the wave dispatch set (level minus family_set) holds none
  input provenance    the registry input equals what the committed sources derive; no later migration rewrites depends_on
  mutations           each guard above is shown to fail on a broken input (missing asset, cycle, dangling edge, equal level,
                      stale revision/fingerprint/hash, family asset dispatched, a new seed asset, a later depends_on migration)
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
import warnings

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
REPO = HERE.parents[3]
CTRL = REPO / "00_ARCHITECTURE" / "control"
MIGRATIONS = REPO / "platform" / "migrations"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("regenerate_draft_level_map_t", CTRL / "regenerate_draft_level_map.py")
G = R.G
import suvarna_level_wave as slw  # noqa: E402

LEVEL_MAP = CTRL / "LEVEL_MAP.json"
FAMILY = CTRL / "FAMILY_ASSETS.json"
REG_INPUT = CTRL / "registry_input_draft.json"
N_ACTIVE = 127

LM = G.strict_json_loads(LEVEL_MAP.read_text(encoding="utf-8"))
FA = G.strict_json_loads(FAMILY.read_text(encoding="utf-8"))
ROWS = G.load_registry_json(REG_INPUT)
PIN = R.census_pin()                                   # (REGISTRY_REVISION, registry_fingerprint()) of this checkout


# ───────────────────────── the checks (each one is mutated below) ─────────────────────────

def staleness_failures(doc, pin):
    """Staleness of a document's recorded registry revision/fingerprint against the census pin, as FAILURES. A DRAFT is only
    warned about (the warning is the visible signal); every other status fails."""
    stale = R.staleness(doc, pin)
    status = (doc.get("_stamp") or {}).get("status")
    if stale and status == "DRAFT":
        warnings.warn("STALE (draft): " + "; ".join(stale) + " -- regenerate_draft_level_map.py before J1", UserWarning, stacklevel=2)
        return []
    return [f"stale registry stamp ({status}): {s}" for s in stale]


def level_map_problems(lm, rows, pin=None):
    """Every HARD defect of a level map against the registry rows it claims to be made from, plus staleness for a document
    that is not a DRAFT. Empty list = clean."""
    out = []
    active = {r["asset_id"]: r for r in rows if r["active"]}
    levels = lm.get("levels", {})
    if not str(lm.get("version", "")).endswith("-draft"):
        out.append(f"version {lm.get('version')!r} is not marked -draft")
    stamp = lm.get("_stamp", {})
    if stamp.get("status") != "DRAFT":
        out.append("_stamp.status is not DRAFT")
    if lm.get("registry_revision") != stamp.get("registry_revision"):
        out.append("registry_revision and _stamp.registry_revision disagree")
    if not re.fullmatch(r"[0-9a-f]{64}", str(stamp.get("registry_fingerprint"))):
        out.append("_stamp.registry_fingerprint is not a sha256")
    if pin is not None:
        out += staleness_failures(lm, pin)
    missing, extra = sorted(set(active) - set(levels)), sorted(set(levels) - set(active))
    if missing:
        out.append(f"assets missing from the level map: {missing}")
    if extra:
        out.append(f"assets in the level map that are not active registry assets: {extra}")
    for a, r in sorted(active.items()):
        if a not in levels:
            continue
        for d in r["depends_on"]:
            if d in levels and not levels[a] > levels[d]:
                out.append(f"{a} (level {levels[a]}) is not above its dependency {d} (level {levels[d]})")
        known = [levels[d] for d in r["depends_on"] if d in levels]
        want = 0 if not r["depends_on"] else (1 + max(known) if known else None)
        if want is not None and levels[a] != want:
            out.append(f"{a} is at level {levels[a]}, longest-path depth is {want}")
    if levels and sorted(set(levels.values())) != list(range(max(levels.values()) + 1)):
        out.append("levels are not contiguous from 0")
    return out


def family_problems(fa, lm, rows):
    """Family marking and exclusion: the dispatch set of every level (level minus family_set) holds no family asset."""
    out = []
    levels = lm["levels"]
    members = set(fa["family_set"])
    inactive = {r["asset_id"] for r in rows if not r["active"]}
    family = {"state": "present", "family_set": frozenset(members),
              "families": {k: frozenset(fa[k]) for k in slw.FAMILY_LIST_KEYS}}
    for a in sorted(members):
        if a not in levels and a not in inactive:
            out.append(f"family member {a} is neither in the level map nor an inactive registry row")
    by_level = {}
    for a, lv in levels.items():
        by_level.setdefault(lv, []).append(a)
    for lv, assets in sorted(by_level.items()):
        dispatch = sorted(set(assets) - members)
        refusals = slw.family_refusals(dispatch, family, committing=True)
        if refusals:
            out.append(f"level {lv}: the non-family dispatch set is refused: {[r['code'] + ':' + r.get('asset', '') for r in refusals]}")
    for a in sorted(levels):
        if slw.FAMILY_NAME_PATTERN.match(a) and a not in members:
            out.append(f"{a} matches the family name pattern but is not in family_set")
    return out


def seed_problems(seed_rows, rows):
    """The seed's active ids must be exactly the registry input's active ids plus the recorded live-inactive overrides."""
    seed_active = {r["asset_id"] for r in seed_rows if r["active"]}
    reg_active = {r["asset_id"] for r in rows if r["active"]}
    out = []
    if seed_active - reg_active - set(R.LIVE_INACTIVE_OVERRIDES):
        out.append(f"seed has active assets the registry input lacks: {sorted(seed_active - reg_active - set(R.LIVE_INACTIVE_OVERRIDES))}")
    if reg_active - seed_active:
        out.append(f"registry input has active assets the seed lacks: {sorted(reg_active - seed_active)}")
    layer = {r["asset_id"]: r["layer"] for r in seed_rows}
    out += [f"{r['asset_id']}: layer {r['layer']} != seed {layer.get(r['asset_id'])}" for r in rows if layer.get(r["asset_id"]) != r["layer"]]
    return out


def later_depends_on_writers(files):
    """Names of migrations numbered after 1210 whose SQL (comments stripped) mentions depends_on."""
    bad = []
    for name, text in sorted(files.items()):
        m = re.match(r"(\d+)_", name)
        if not m or int(m.group(1)) <= 1210:
            continue
        code = re.sub(r"/\*.*?\*/", "", re.sub(r"--[^\n]*", "", text), flags=re.S)
        if re.search(r"\bdepends_on\b", code):
            bad.append(name)
    return bad


def _migration_texts():
    return {p.name: p.read_text(encoding="utf-8") for p in MIGRATIONS.glob("*.sql")}


def _fresh():
    """A regeneration AT THE RECORDED stamp (never the current census pin: that is the staleness check, which only warns)."""
    st = LM["_stamp"]
    return R.render(frozen_at=LM["frozen_at"], registry_revision=LM["registry_revision"],
                    registry_fingerprint=st["registry_fingerprint"], version=LM["version"], status=st["status"])


# ───────────────────────── the committed files ─────────────────────────

def test_committed_files_equal_a_fresh_regeneration_byte_for_byte():
    fresh = _fresh()
    for name, path in ((R.REGISTRY_INPUT_FILE, REG_INPUT), ("LEVEL_MAP.json", LEVEL_MAP), ("FAMILY_ASSETS.json", FAMILY)):
        assert path.read_text(encoding="utf-8") == fresh[name], f"{name} differs from a regeneration (run regenerate_draft_level_map.py)"


def test_regeneration_is_deterministic():
    assert _fresh() == _fresh()


def test_the_generators_own_cli_makes_the_same_bytes(tmp_path):
    notes = tmp_path / "notes.json"
    notes.write_text(json.dumps({"_stamp": LM["_stamp"]}), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    rc = G.main(["--registry-json", str(REG_INPUT), "--family-input", str(CTRL / R.FAMILY_INPUT_FILE), "--out-dir", str(out),
                 "--frozen-at", LM["frozen_at"], "--registry-revision", str(LM["registry_revision"]), "--version", LM["version"],
                 "--notes-json", str(notes)])
    assert rc == 0
    assert (out / "LEVEL_MAP.json").read_bytes() == LEVEL_MAP.read_bytes()
    assert (out / "FAMILY_ASSETS.json").read_bytes() == FAMILY.read_bytes()


def test_the_check_mode_of_the_tool_agrees(capsys):
    assert R.main(["--check"]) == 0                       # a stale DRAFT prints STALE (draft) and still exits 0
    if R.staleness(LM, PIN):
        assert "STALE (draft)" in capsys.readouterr().err


def test_both_files_are_drafts_made_together_at_the_current_registry_revision_and_fingerprint():
    assert LM["version"] == FA["version"] and LM["version"].endswith("-draft")
    assert LM["frozen_at"] == FA["frozen_at"] and LM["registry_revision"] == FA["registry_revision"]
    assert LM["_stamp"] == FA["_stamp"] and LM["_stamp"]["status"] == "DRAFT"
    assert level_map_problems(LM, ROWS, PIN) == []        # staleness of a DRAFT is a warning here, not a failure
    assert FA["registry_revision"] == LM["registry_revision"] == FA["_stamp"]["registry_revision"]
    assert staleness_failures(FA, PIN) == []
    assert LM["_stamp"]["registry_input_sha256"] == hashlib.sha256(REG_INPUT.read_bytes()).hexdigest()


def test_the_level_map_key_schema_is_the_pinned_one_plus_the_stamp():
    assert list(LM) == ["version", "frozen_at", "registry_revision", "levels", "_stamp"]
    assert list(LM["levels"]) == sorted(LM["levels"])


# ───────────────────────── coverage and levels ─────────────────────────

def test_every_active_registry_asset_appears_exactly_once():
    active = [r["asset_id"] for r in ROWS if r["active"]]
    assert len(active) == len(set(active)) == N_ACTIVE
    assert sorted(LM["levels"]) == sorted(active) and len(LM["levels"]) == N_ACTIVE      # strict JSON load refuses a duplicate key
    assert not {r["asset_id"] for r in ROWS if not r["active"]} & set(LM["levels"])


def test_each_asset_is_strictly_above_every_dependency_and_at_its_longest_path_depth():
    assert level_map_problems(LM, ROWS, PIN) == []
    assert G.compute_levels(ROWS) == LM["levels"]


def test_the_registry_input_has_no_dangling_edge_and_no_cycle():
    ids = {r["asset_id"] for r in ROWS if r["active"]}
    assert all(set(r["depends_on"]) <= ids for r in ROWS if r["active"])


# ───────────────────────── family ─────────────────────────

def test_family_assets_are_marked_and_excluded_from_every_wave_dispatch_set():
    assert family_problems(FA, LM, ROWS) == []
    members = set(FA["family_set"])
    in_map = members & set(LM["levels"])
    assert in_map and members - in_map == {"ka_gochara_sweep", "ka_gochara_v3_century_materialize", "ka_gochara_v4_41_candidate"}
    dispatch = {a for a in LM["levels"] if a not in members}
    assert dispatch | in_map == set(LM["levels"]) and not dispatch & members


def test_the_family_lists_are_the_strategist_input_unchanged_in_membership():
    inp = G.load_family_input(CTRL / R.FAMILY_INPUT_FILE)
    assert all(FA[k] == inp[k] for k in G.FAMILY_LIST_KEYS)
    assert len(FA["family_set"]) == 25


# ───────────────────────── where the DAG comes from ─────────────────────────

def test_the_registry_input_is_what_the_committed_sources_derive():
    assert R.derive_registry_rows() == ROWS
    assert seed_problems(G.parse_seed_text((REPO / "platform/scripts/seed/asset_registry_seed.ts").read_text(encoding="utf-8")), ROWS) == []


def test_migration_1210_added_twelve_edges_and_all_are_in_the_registry_input():
    edges = R.migration_1210_edges()
    assert len(edges) == 12
    by = {r["asset_id"]: set(r["depends_on"]) for r in ROWS}
    assert all(d in by[a] for a, d in edges)


def test_no_migration_after_1210_rewrites_depends_on():
    assert later_depends_on_writers(_migration_texts()) == []


# ───────────────────────── mutation tests: each guard fails ─────────────────────────

def test_mutation_an_asset_missing_from_the_level_map_is_a_failure():
    lm = copy.deepcopy(LM)
    del lm["levels"]["ga_positions"]
    assert any("missing from the level map" in p and "ga_positions" in p for p in level_map_problems(lm, ROWS, PIN))


def test_mutation_an_asset_in_the_map_that_the_registry_does_not_hold_is_a_failure():
    lm = copy.deepcopy(LM)
    lm["levels"]["ka_ghost"] = 0
    assert any("not active registry assets" in p for p in level_map_problems(lm, ROWS, PIN))
    lm = copy.deepcopy(LM)
    lm["levels"]["ka_gochara_sweep"] = 0                                        # an inactive row
    assert any("not active registry assets" in p for p in level_map_problems(lm, ROWS, PIN))


def test_mutation_a_dependency_at_an_equal_or_higher_level_is_a_failure():
    dep = next(r for r in ROWS if r["active"] and r["depends_on"])
    a, d = dep["asset_id"], dep["depends_on"][0]
    for bump in (0, 3):                                                          # equal to, then below, the dependency
        lm = copy.deepcopy(LM)
        lm["levels"][a] = lm["levels"][d] - bump
        assert any(f"{a} (level" in p and "not above its dependency" in p for p in level_map_problems(lm, ROWS, PIN)), bump
    lm = copy.deepcopy(LM)
    lm["levels"][d] = lm["levels"][a]                                            # dependency pushed up to the dependent
    assert any("not above its dependency" in p for p in level_map_problems(lm, ROWS, PIN))


def test_mutation_a_level_that_is_not_the_longest_path_is_a_failure():
    lm = copy.deepcopy(LM)
    top = max(lm["levels"], key=lambda a: lm["levels"][a])
    lm["levels"][top] += 5
    problems = level_map_problems(lm, ROWS, PIN)
    assert any("longest-path depth" in p for p in problems) and any("not contiguous" in p for p in problems)


def test_mutation_a_dependency_cycle_is_refused_by_the_generator_never_level_zero():
    fx = json.loads(R.FIXTURE.read_text(encoding="utf-8"))["edges"]
    fx = {a: list(d) for a, d in fx.items()}
    fx["ga_positions"] = ["ga_dashas"]                                           # ga_dashas -> ga_positions already: a 2-cycle
    rows = R.derive_registry_rows(fixture_edges=fx)
    with pytest.raises(G.LevelMapError, match="cycle"):
        R.render(frozen_at=LM["frozen_at"], registry_revision=PIN[0], registry_fingerprint=PIN[1], rows=rows)


def test_mutation_a_dangling_edge_is_refused_by_the_generator():
    fx = {a: list(d) for a, d in json.loads(R.FIXTURE.read_text(encoding="utf-8"))["edges"].items()}
    fx["ga_positions"] = ["ga_ghost"]
    with pytest.raises(G.LevelMapError, match="does not hold"):
        R.render(frozen_at=LM["frozen_at"], registry_revision=PIN[0], registry_fingerprint=PIN[1],
                 rows=R.derive_registry_rows(fixture_edges=fx))


def test_mutation_an_edge_to_an_inactive_asset_is_refused_by_the_generator():
    fx = {a: list(d) for a, d in json.loads(R.FIXTURE.read_text(encoding="utf-8"))["edges"].items()}
    fx["ga_positions"] = ["ka_gochara_sweep"]
    with pytest.raises(G.LevelMapError, match="inactive"):
        R.render(frozen_at=LM["frozen_at"], registry_revision=PIN[0], registry_fingerprint=PIN[1],
                 rows=R.derive_registry_rows(fixture_edges=fx))


def _stale(doc, how):
    doc = copy.deepcopy(doc)
    if how == "revision":
        doc["registry_revision"] = doc["_stamp"]["registry_revision"] = PIN[0] - 1
    else:
        doc["_stamp"]["registry_fingerprint"] = "0" * 64
    return doc


@pytest.mark.parametrize("how", ["revision", "fingerprint"])
def test_a_stale_draft_warns_and_does_not_fail(how):
    lm = _stale(LM, how)
    with pytest.warns(UserWarning, match=r"STALE \(draft\)"):
        assert level_map_problems(lm, ROWS, PIN) == []
    with pytest.warns(UserWarning, match=r"STALE \(draft\)"):
        assert staleness_failures(FA | {"_stamp": lm["_stamp"], "registry_revision": lm["registry_revision"]}, PIN) == []
    with warnings.catch_warnings():                                  # a current draft is silent
        warnings.simplefilter("error")
        assert level_map_problems(LM, ROWS, (LM["registry_revision"], LM["_stamp"]["registry_fingerprint"])) == []


@pytest.mark.parametrize("how", ["revision", "fingerprint"])
@pytest.mark.parametrize("status", ["FROZEN", "J1", ""])
def test_mutation_a_stale_stamp_on_anything_but_a_draft_is_a_failure(how, status):
    lm = _stale(LM, how)
    lm["_stamp"]["status"] = status
    assert any("stale registry stamp" in p for p in level_map_problems(lm, ROWS, PIN))
    fa = _stale(FA, how)
    fa["_stamp"]["status"] = status
    assert staleness_failures(fa, PIN)
    cur = copy.deepcopy(LM)                                           # ... and the frozen copy at the CURRENT pin is clean
    cur["_stamp"].update(status=status, registry_revision=PIN[0], registry_fingerprint=PIN[1])
    cur["registry_revision"] = PIN[0]
    assert not [p for p in level_map_problems(cur, ROWS, PIN) if "stale" in p]


def test_the_committed_draft_survives_a_census_revision_bump(monkeypatch, capsys):
    """The case this relaxation exists for: asset_census moves to a later revision/fingerprint. The committed draft must still
    pass every hard guard (it equals its regeneration at its own stamp) and only warn."""
    bumped = (PIN[0] + 1, "f" * 64)
    with pytest.warns(UserWarning, match=r"STALE \(draft\)"):
        assert level_map_problems(LM, ROWS, bumped) == [] and staleness_failures(FA, bumped) == []
    monkeypatch.setattr(R, "census_pin", lambda: bumped)
    assert R.main(["--check"]) == 0 and "STALE (draft)" in capsys.readouterr().err
    assert R.main(["--check", "--strict"]) == 1


def _write_copy(tmp_path, status, how=None, version=None):
    """A temp copy of the three files regenerated at a (possibly stale) stamp and status."""
    rev, fp = PIN[0] - (1 if how == "revision" else 0), ("0" * 64 if how == "fingerprint" else PIN[1])
    files = R.render(frozen_at=LM["frozen_at"], registry_revision=rev, registry_fingerprint=fp,
                     version=version or LM["version"], status=status)
    for n, t in files.items():
        (tmp_path / n).write_text(t, encoding="utf-8")
    return tmp_path


def test_check_mode_exit_codes_for_a_stale_draft(tmp_path, capsys):
    _write_copy(tmp_path, "DRAFT", "revision")
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 0
    assert "STALE (draft)" in capsys.readouterr().err
    assert R.main(["--check", "--strict", "--out-dir", str(tmp_path)]) == 1
    assert "STALE (draft)" in capsys.readouterr().err


def test_check_mode_is_clean_for_a_current_draft_even_with_strict(tmp_path, capsys):
    _write_copy(tmp_path, "DRAFT")
    assert R.main(["--check", "--strict", "--out-dir", str(tmp_path)]) == 0
    assert "STALE" not in capsys.readouterr().err


@pytest.mark.parametrize("how", ["revision", "fingerprint"])
def test_mutation_check_mode_fails_a_stale_frozen_copy_without_strict(tmp_path, capsys, how):
    _write_copy(tmp_path, "FROZEN", how, version="1.0")
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 1
    assert "STALE (FROZEN)" in capsys.readouterr().err
    cur = tmp_path / "cur"
    cur.mkdir()
    _write_copy(cur, "FROZEN", None, version="1.0")                   # the same freeze at the current pin passes
    assert R.main(["--check", "--out-dir", str(cur)]) == 0


def test_a_stale_draft_whose_files_differ_from_their_regeneration_still_fails(tmp_path):
    _write_copy(tmp_path, "DRAFT", "revision")
    doc = json.loads((tmp_path / "LEVEL_MAP.json").read_text(encoding="utf-8"))
    doc["levels"]["ga_positions"] = 1
    (tmp_path / "LEVEL_MAP.json").write_text(R.dumps(doc), encoding="utf-8")
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 1       # every other guard stays hard


def test_strict_without_check_is_refused(capsys):
    assert R.main(["--strict"]) == 2


def test_mutation_a_missing_draft_marker_is_a_failure():
    lm = copy.deepcopy(LM)
    lm["version"] = "1.0"
    assert any("not marked -draft" in p for p in level_map_problems(lm, ROWS, PIN))
    lm = copy.deepcopy(LM)
    lm["_stamp"]["status"] = "FROZEN"
    assert any("not DRAFT" in p for p in level_map_problems(lm, ROWS, PIN))


def test_mutation_a_changed_registry_input_changes_the_stamped_hash_and_the_committed_files_no_longer_match():
    rows = copy.deepcopy(ROWS)
    row = next(r for r in rows if r["active"] and r["depends_on"])
    row["depends_on"] = row["depends_on"][:-1]
    fresh = R.render(frozen_at=LM["frozen_at"], registry_revision=PIN[0], registry_fingerprint=PIN[1], version=LM["version"], rows=rows)
    assert fresh[R.REGISTRY_INPUT_FILE] != REG_INPUT.read_text(encoding="utf-8")
    assert json.loads(fresh["LEVEL_MAP.json"])["_stamp"]["registry_input_sha256"] != LM["_stamp"]["registry_input_sha256"]


def test_mutation_a_family_asset_in_a_dispatch_set_is_refused():
    members = set(FA["family_set"])
    level = LM["levels"]["ka_gochara"]
    same_level = sorted(a for a, lv in LM["levels"].items() if lv == level)
    assert "ka_gochara" in same_level
    family = {"state": "present", "family_set": frozenset(members), "families": {k: frozenset(FA[k]) for k in slw.FAMILY_LIST_KEYS}}
    assert slw.family_refusals(same_level, family, committing=True)                  # the whole level is refused
    assert not slw.family_refusals([a for a in same_level if a not in members], family, committing=True)


def test_mutation_a_family_list_that_loses_a_name_pattern_asset_is_a_failure():
    fa = copy.deepcopy(FA)
    for k in slw.FAMILY_LIST_KEYS:
        if "ka_gochara_resonance" in fa[k]:
            fa[k] = [a for a in fa[k] if a != "ka_gochara_resonance"]
    fa["family_set"] = sorted(set(fa["family_set"]) - {"ka_gochara_resonance"})
    assert any("ka_gochara_resonance" in p for p in family_problems(fa, LM, ROWS))


def test_mutation_a_family_member_unknown_to_the_registry_is_a_failure():
    fa = copy.deepcopy(FA)
    fa["family_set"] = sorted(set(fa["family_set"]) | {"ka_ghost"})
    assert any("ka_ghost" in p for p in family_problems(fa, LM, ROWS))


def test_mutation_a_new_active_seed_asset_the_registry_input_lacks_is_a_failure():
    seed = G.parse_seed_text((REPO / "platform/scripts/seed/asset_registry_seed.ts").read_text(encoding="utf-8"))
    seed.append(dict(asset_id="ka_new_asset", layer="kala", depends_on=[], active=True, asset_kind="data"))
    assert any("ka_new_asset" in p for p in seed_problems(seed, ROWS))


def test_mutation_a_later_migration_that_writes_depends_on_is_a_failure():
    files = _migration_texts()
    files["1299_x.sql"] = "-- depends_on in a comment is fine\nUPDATE asset_registry SET depends_on = ARRAY['a'] WHERE asset_id = 'b';"
    assert later_depends_on_writers(files) == ["1299_x.sql"]
    files["1299_x.sql"] = "-- depends_on in a comment is fine\n/* depends_on */ SELECT 1;"
    assert later_depends_on_writers(files) == []


def test_mutation_the_check_mode_reports_a_changed_committed_file(tmp_path, capsys):
    for p in (LEVEL_MAP, FAMILY, REG_INPUT):
        (tmp_path / p.name).write_bytes(p.read_bytes())
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 0
    doc = json.loads((tmp_path / "LEVEL_MAP.json").read_text(encoding="utf-8"))
    doc["levels"]["ga_positions"] = 1
    (tmp_path / "LEVEL_MAP.json").write_text(R.dumps(doc), encoding="utf-8")
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 1
    assert "DIFFERS" in capsys.readouterr().err
