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


def migration_pin_problems(found, pinned):
    """Differences between the migrations that mention depends_on (both dirs the runner applies) and the committed pin, plus
    non-vacuity: migration 1210 must have been seen and both directories must hold migrations."""
    out = []
    if "1210_asset_registry_direct_edges.sql" not in found.get("platform/migrations", []):
        out.append("non-vacuity: migration 1210 was not seen (the scan reads the wrong place)")
    if set(found) != set(R.MIGRATION_DIRS):
        out.append(f"scanned directories {sorted(found)} != {sorted(R.MIGRATION_DIRS)}")
    for d in sorted(set(found) | set(pinned)):
        new = sorted(set(found.get(d, [])) - set(pinned.get(d, [])))
        gone = sorted(set(pinned.get(d, [])) - set(found.get(d, [])))
        if new:
            out.append(f"{d}: migration(s) mention depends_on but are not pinned: {new}")
        if gone:
            out.append(f"{d}: pinned migration(s) no longer mention depends_on or are gone: {gone}")
    return out


def _migration_texts():
    return {d: {p.name: p.read_text(encoding="utf-8", errors="replace") for p in (REPO / d).glob("*.sql")} for d in R.MIGRATION_DIRS}


PIN_FILE = CTRL / R.MIGRATION_PIN_FILE


def _fresh(rows=None):
    """A regeneration from the COMMITTED registry input, AT THE RECORDED stamp (never the current census pin: that is the
    staleness check, which only warns)."""
    st = LM["_stamp"]
    return R.render(frozen_at=LM["frozen_at"], registry_revision=LM["registry_revision"],
                    registry_fingerprint=st["registry_fingerprint"], version=LM["version"], status=st["status"],
                    rows=ROWS if rows is None else rows)


# ───────────────────────── the committed files ─────────────────────────

def test_committed_files_equal_a_fresh_regeneration_byte_for_byte():
    fresh = _fresh()
    for name, path in ((R.REGISTRY_INPUT_FILE, REG_INPUT), ("LEVEL_MAP.json", LEVEL_MAP), ("FAMILY_ASSETS.json", FAMILY)):
        assert path.read_text(encoding="utf-8") == fresh[name], f"{name} differs from a regeneration (run regenerate_draft_level_map.py)"


@pytest.mark.parametrize("seed", ["0", "1", "4242"])
def test_regeneration_is_identical_across_processes_and_hash_seeds(tmp_path, seed):
    import os
    import subprocess
    out = tmp_path / "out"
    out.mkdir()
    env = dict(os.environ, PYTHONHASHSEED=seed)
    proc = subprocess.run([sys.executable, str(CTRL / "regenerate_draft_level_map.py"), "--out-dir", str(out),
                           "--frozen-at", LM["frozen_at"]], env=env, capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    for n in (R.REGISTRY_INPUT_FILE, "LEVEL_MAP.json", "FAMILY_ASSETS.json"):
        got = (out / n).read_text(encoding="utf-8")
        committed = (CTRL / n).read_text(encoding="utf-8")
        if R.staleness(LM, PIN):                     # a stale draft: the new write is at the CURRENT pin; compare the registry input only
            if n == R.REGISTRY_INPUT_FILE:
                assert got == committed
        else:
            assert got == committed, f"{n} differs under PYTHONHASHSEED={seed}"


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
    assert in_map and members - in_map == {"ka_gochara_sweep", "ka_gochara_v3_century_materialize", "ka_gochara_v4_41_candidate",
                                           "ka_gochara_v5"}
    dispatch = {a for a in LM["levels"] if a not in members}
    assert dispatch | in_map == set(LM["levels"]) and not dispatch & members


def test_the_family_lists_are_the_strategist_input_unchanged_in_membership():
    inp = G.load_family_input(CTRL / R.FAMILY_INPUT_FILE)
    assert all(FA[k] == inp[k] for k in G.FAMILY_LIST_KEYS)
    assert len(FA["family_set"]) == 26


# ───────────────────────── where the DAG comes from ─────────────────────────

def test_the_registry_input_is_what_the_committed_sources_derive():
    assert R.derive_registry_rows() == ROWS
    assert seed_problems(G.parse_seed_text((REPO / "platform/scripts/seed/asset_registry_seed.ts").read_text(encoding="utf-8")), ROWS) == []


def test_migration_1210_added_twelve_edges_and_all_are_in_the_registry_input():
    edges = R.migration_1210_edges()
    assert len(edges) == 12
    by = {r["asset_id"]: set(r["depends_on"]) for r in ROWS}
    assert all(d in by[a] for a, d in edges)


def test_the_set_of_migrations_that_mention_depends_on_is_the_pinned_set_in_both_directories():
    found = R.depends_on_migrations()
    pinned = json.loads(PIN_FILE.read_text(encoding="utf-8"))["migrations"]
    assert migration_pin_problems(found, pinned) == []
    assert "1210_asset_registry_direct_edges.sql" in found["platform/migrations"]          # non-vacuity
    assert len(found["platform/migrations"]) > 20 and len(found["platform/supabase/migrations"]) > 20
    assert PIN_FILE.read_text(encoding="utf-8") == R.migration_pin_text(found)               # the pin is what the tool writes


def test_the_seed_and_the_input_differ_on_exactly_eight_assets_in_exactly_these_edges():
    seed = {r["asset_id"]: set(r["depends_on"]) for r in G.parse_seed_text((REPO / "platform/scripts/seed/asset_registry_seed.ts").read_text(encoding="utf-8"))}
    diff = {r["asset_id"]: (sorted(set(r["depends_on"]) - seed[r["asset_id"]]), sorted(seed[r["asset_id"]] - set(r["depends_on"])))
            for r in ROWS if r["active"] and set(r["depends_on"]) != seed[r["asset_id"]]}
    # The three ga_* entries are migration 1226's four applied L1 edges, which the seed now carries (tests-only PR) but the
    # DRAFT registry input (pre-1210 graph + 1210's edges, registry revision 16) does not: the input is a stale draft that
    # is re-derived at J1, so the seed-only side of each pair is the pinned, expected divergence.
    assert diff == {
        "ga_dashas": ([], ["ga_sensitive", "ga_vargas"]),
        "ga_vargas": ([], ["ga_sensitive"]),
        "ga_yoga": ([], ["ga_vargas"]),
        "bo_nakshatra_semantic": (["ga_structural"], []),
        "ka_kshetra": (["ka_vedha_gochara"], []),
        "ka_muhurta_seva": ([], ["ka_graha_sancara"]),
        "ka_sangam": (["ka_vedha_gochara"], []),
        "ka_vighnakara": (["bg_dignity_reference", "ka_yojaka"], ["ka_gochara"]),
    }


def test_the_inactive_rows_are_pinned_and_none_is_seed_only_since_1243():
    assert sorted(r["asset_id"] for r in ROWS if not r["active"]) == [
        "ka_gochara_sweep", "ka_gochara_v3_century_materialize", "ka_gochara_v4_41_candidate", "ka_gochara_v5"]
    # migration 1243 made ka_gochara_v4_41_candidate and ka_gochara_v5 live inactive rows: nothing is seed-only any more
    assert set(R.SEED_ONLY_INACTIVE) == set() and set(R.LIVE_INACTIVE_OVERRIDES) == {"ka_gochara_v3_century_materialize"}


def test_the_stamp_binds_the_dag_and_says_the_census_fields_are_not_the_dag():
    st = LM["_stamp"]
    assert st["dag_sha256"] == R.dag_sha256(ROWS) and len(st["dag_sha256"]) == 64
    assert "CENSUS CRITERIA registry" in st["registry_stamp_scope"] and "not the asset_registry dependency graph" in st["registry_stamp_scope"]


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


WRITER = "UPDATE asset_registry SET depends_on = ARRAY['a'] WHERE asset_id = 'b';"


def _scan_with(extra):
    texts = _migration_texts()
    for d, name, sql in extra:
        texts[d][name] = sql
    return R.depends_on_migrations(texts)


PINNED = json.loads(PIN_FILE.read_text(encoding="utf-8"))["migrations"]


@pytest.mark.parametrize("d,name", [
    ("platform/migrations", "1299_new_edge.sql"),                  # M12: a new high-numbered writer
    ("platform/supabase/migrations", "1299_new_edge.sql"),         # M14: the OTHER directory the runner applies
    ("platform/migrations", "0100_old_number.sql"),                # M15: a low number (the old '> 1210' rule would miss it)
    ("platform/supabase/migrations", "0100_old_number.sql"),
])
def test_mutation_a_new_migration_mentioning_depends_on_in_either_directory_fails_the_pin(d, name):
    found = _scan_with([(d, name, WRITER)])
    assert any(name in p and "not pinned" in p for p in migration_pin_problems(found, PINNED))
    found = _scan_with([(d, name, WRITER.replace("depends_on", "DEPENDS_ON"))])          # case is not an escape
    assert any(name in p for p in migration_pin_problems(found, PINNED))


def test_mutation_a_comment_only_mention_is_not_a_writer():
    found = _scan_with([("platform/migrations", "1299_c.sql", "-- depends_on in a comment\n/* depends_on */ SELECT 1;")])
    assert migration_pin_problems(found, PINNED) == []


def test_mutation_a_pinned_migration_that_vanishes_or_stops_mentioning_it_fails_the_pin():
    texts = _migration_texts()
    victim = PINNED["platform/supabase/migrations"][0]
    del texts["platform/supabase/migrations"][victim]
    assert any(victim in p and "no longer" in p for p in migration_pin_problems(R.depends_on_migrations(texts), PINNED))
    texts = _migration_texts()
    texts["platform/migrations"]["913_bo_nakshatra_semantic_add_ga_structural_dep.sql"] = "SELECT 1;"
    assert any("913_bo_nakshatra" in p for p in migration_pin_problems(R.depends_on_migrations(texts), PINNED))


def test_mutation_a_scan_that_cannot_see_migration_1210_is_a_failure_not_a_pass():
    texts = _migration_texts()
    del texts["platform/migrations"]["1210_asset_registry_direct_edges.sql"]
    pinned = {d: [n for n in v if n != "1210_asset_registry_direct_edges.sql"] for d, v in PINNED.items()}
    assert any("non-vacuity" in p for p in migration_pin_problems(R.depends_on_migrations(texts), pinned))
    assert any("scanned directories" in p for p in migration_pin_problems({"platform/migrations": PINNED["platform/migrations"]}, PINNED))


def test_mutation_the_check_mode_reports_a_changed_committed_file(tmp_path, capsys):
    for p in (LEVEL_MAP, FAMILY, REG_INPUT):
        (tmp_path / p.name).write_bytes(p.read_bytes())
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 0
    doc = json.loads((tmp_path / "LEVEL_MAP.json").read_text(encoding="utf-8"))
    doc["levels"]["ga_positions"] = 1
    (tmp_path / "LEVEL_MAP.json").write_text(R.dumps(doc), encoding="utf-8")
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 1
    assert "DIFFERS" in capsys.readouterr().err


# ───────────────────────── --check compares all three files; staleness fields; the pre-freeze gate ─────────────────────────

def _copy_set(tmp_path):
    for p in (LEVEL_MAP, FAMILY, REG_INPUT):
        (tmp_path / p.name).write_bytes(p.read_bytes())
    return tmp_path


@pytest.mark.parametrize("name", [R.REGISTRY_INPUT_FILE, "LEVEL_MAP.json", "FAMILY_ASSETS.json"])
def test_mutation_check_compares_all_three_files(tmp_path, capsys, name):
    _copy_set(tmp_path)
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 0
    path = tmp_path / name
    doc = json.loads(path.read_text(encoding="utf-8"))
    if name == R.REGISTRY_INPUT_FILE:
        path.write_text(json.dumps(doc, indent=4) + "\n", encoding="utf-8")            # same rows, other bytes
    else:
        doc["_stamp"]["freeze"] = "edited by hand"                                      # the check inputs are untouched
        path.write_text(R.dumps(doc), encoding="utf-8")
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert f"DIFFERS: {path}" in err and err.count("DIFFERS") == 1


def test_a_missing_file_is_a_difference_not_a_pass(tmp_path):
    _copy_set(tmp_path)
    (tmp_path / "FAMILY_ASSETS.json").unlink()
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 1


def test_staleness_compares_the_top_level_revision_and_the_stamp_fields_separately():
    base = (LM["registry_revision"], LM["_stamp"]["registry_fingerprint"])
    assert R.staleness(LM, base) == []
    top = copy.deepcopy(LM)
    top["registry_revision"] = base[0] - 1                       # only the top-level field is behind
    assert [x.split(" ")[0] for x in R.staleness(top, base)] == ["registry_revision"]
    st = copy.deepcopy(LM)
    st["_stamp"]["registry_revision"] = base[0] - 1
    assert [x.split(" ")[0] for x in R.staleness(st, base)] == ["_stamp.registry_revision"]
    fp = copy.deepcopy(LM)
    fp["_stamp"]["registry_fingerprint"] = "0" * 64
    assert [x.split(" ")[0] for x in R.staleness(fp, base)] == ["_stamp.registry_fingerprint"]
    assert R.staleness({}, base) and R.staleness({"_stamp": "x"}, base)                   # no stamp is stale, never a crash
    frozen = copy.deepcopy(top)
    frozen["_stamp"]["status"] = "FROZEN"
    assert staleness_failures(frozen, base)                                               # a top-level lag alone fails a freeze


def test_pre_freeze_is_the_gate_a_relabelled_stale_draft_passes_check_but_fails_it(tmp_path, capsys):
    _write_copy(tmp_path, "FROZEN", "revision", version="1.0")
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 1                             # honest: stale AND not a draft
    # the same stale content relabelled DRAFT (status and version edited, regenerated consistently)
    _write_copy(tmp_path, "DRAFT", "revision")
    capsys.readouterr()
    assert R.main(["--check", "--out-dir", str(tmp_path)]) == 0                             # only warned ...
    assert "STALE (draft)" in capsys.readouterr().err
    assert R.main(["--check", "--pre-freeze", "--out-dir", str(tmp_path)]) == 1             # ... the gate fails it
    assert "PRE-FREEZE FAIL" in capsys.readouterr().err


def test_pre_freeze_fails_every_draft_even_a_current_one(tmp_path, capsys):
    _write_copy(tmp_path, "DRAFT")
    assert R.main(["--check", "--strict", "--out-dir", str(tmp_path)]) == 0
    assert R.main(["--check", "--pre-freeze", "--out-dir", str(tmp_path)]) == 1
    assert "status is DRAFT" in capsys.readouterr().err


def test_pre_freeze_passes_only_a_current_frozen_set_and_fails_a_stale_one(tmp_path, capsys):
    _write_copy(tmp_path, "FROZEN", version="1.0")
    assert R.main(["--check", "--pre-freeze", "--out-dir", str(tmp_path)]) == 0
    stale = tmp_path / "stale"
    stale.mkdir()
    _write_copy(stale, "FROZEN", "fingerprint", version="1.0")
    assert R.main(["--check", "--pre-freeze", "--out-dir", str(stale)]) == 1


def test_pre_freeze_and_registry_export_are_refused_outside_their_modes(capsys):
    assert R.main(["--pre-freeze"]) == 2
    assert R.main(["--registry-export", "x.json"]) == 2
    assert R.main(["--check", "--freeze"]) == 2


def test_a_draft_version_must_say_draft_and_a_freeze_must_not():
    with pytest.raises(G.LevelMapError):
        R.render(frozen_at=LM["frozen_at"], registry_revision=PIN[0], registry_fingerprint=PIN[1], version="1.0", status="DRAFT")
    with pytest.raises(G.LevelMapError):
        R.render(frozen_at=LM["frozen_at"], registry_revision=PIN[0], registry_fingerprint=PIN[1], version="0.2-draft", status="FROZEN")
    with pytest.raises(G.LevelMapError):
        R.render(frozen_at=LM["frozen_at"], registry_revision=PIN[0], registry_fingerprint=PIN[1], status="J1")


# ───────────────────────── F1: a write never clobbers a frozen set; the three files are all-or-nothing ─────────────────────────

NOW = "2026-12-01T00:00:00+00:00"


def _bytes(d):
    return {n: (d / n).read_bytes() for n in (R.REGISTRY_INPUT_FILE, "LEVEL_MAP.json", "FAMILY_ASSETS.json")}


def test_a_write_refuses_to_overwrite_a_frozen_set(tmp_path, capsys):
    _write_copy(tmp_path, "FROZEN", version="1.0")                   # the reviewer's repro: version 1.0 + status FROZEN
    before = _bytes(tmp_path)
    assert R.main(["--out-dir", str(tmp_path), "--frozen-at", NOW]) == 2
    assert _bytes(tmp_path) == before and "refusing to overwrite" in capsys.readouterr().err
    assert R.main(["--out-dir", str(tmp_path), "--frozen-at", NOW, "--force"]) == 0
    assert json.loads((tmp_path / "LEVEL_MAP.json").read_text(encoding="utf-8"))["_stamp"]["status"] == "DRAFT"


@pytest.mark.parametrize("which", ["LEVEL_MAP.json", "FAMILY_ASSETS.json"])
@pytest.mark.parametrize("how", ["frozen", "nostamp", "garbage"])
def test_a_write_refuses_when_either_existing_file_is_not_a_plain_draft(tmp_path, which, how):
    _write_copy(tmp_path, "DRAFT")
    path = tmp_path / which
    doc = json.loads(path.read_text(encoding="utf-8"))
    if how == "frozen":
        doc["_stamp"]["status"] = "FROZEN"
        doc["version"] = "1.0"
    elif how == "nostamp":
        del doc["_stamp"]
    path.write_text("{" if how == "garbage" else R.dumps(doc), encoding="utf-8")
    before = _bytes(tmp_path)
    assert R.main(["--out-dir", str(tmp_path), "--frozen-at", NOW]) == 2
    assert _bytes(tmp_path) == before
    assert R.main(["--out-dir", str(tmp_path), "--frozen-at", NOW, "--force"]) == 0


def test_a_write_over_a_plain_draft_or_an_empty_directory_is_allowed(tmp_path):
    assert R.main(["--out-dir", str(tmp_path), "--frozen-at", NOW]) == 0
    assert R.main(["--out-dir", str(tmp_path), "--frozen-at", NOW]) == 0


@pytest.mark.parametrize("fail_on", [1, 2, 3])
def test_a_failure_part_way_through_the_replace_restores_the_originals(tmp_path, monkeypatch, capsys, fail_on):
    import os
    _write_copy(tmp_path, "DRAFT", "revision")
    before = _bytes(tmp_path)
    real, calls = os.replace, {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] == fail_on:
            raise OSError("disk full (injected)")
        return real(src, dst)

    monkeypatch.setattr(R, "_replace", flaky)
    assert R.main(["--out-dir", str(tmp_path), "--frozen-at", NOW]) == 5
    assert _bytes(tmp_path) == before
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(before)                  # no stage or restore temp left behind
    assert "originals restored" in capsys.readouterr().err


def test_a_failure_while_staging_leaves_the_originals_and_a_fresh_directory_empty(tmp_path, monkeypatch):
    import tempfile
    _write_copy(tmp_path, "DRAFT", "revision")
    before = _bytes(tmp_path)
    real, calls = tempfile.mkstemp, {"n": 0}

    def flaky(*a, **k):
        calls["n"] += 1
        if calls["n"] == 3:
            raise OSError("no space (injected)")
        return real(*a, **k)

    monkeypatch.setattr(tempfile, "mkstemp", flaky)
    assert R.main(["--out-dir", str(tmp_path), "--frozen-at", NOW]) == 5
    assert _bytes(tmp_path) == before and sorted(p.name for p in tmp_path.iterdir()) == sorted(before)
    calls["n"] = 0
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    assert R.main(["--out-dir", str(fresh), "--frozen-at", NOW]) == 5
    assert list(fresh.iterdir()) == []


# ───────────────────────── F2: the J1 freeze path ─────────────────────────

def _export(tmp_path, mutate=None):
    rows = [dict(asset_id=r["asset_id"], layer=r["layer"], depends_on=list(r["depends_on"]), active=r["active"]) for r in ROWS]
    if mutate:
        mutate(rows)
    f = tmp_path / "live_export.json"
    f.write_text(json.dumps(rows), encoding="utf-8")
    return f


def _row(rows, aid):
    return next(r for r in rows if r["asset_id"] == aid)


def test_freeze_writes_a_frozen_set_from_a_matching_live_export_and_passes_the_gate(tmp_path, capsys):
    work = tmp_path / "w"
    work.mkdir()
    _write_copy(work, "DRAFT")
    exp = _export(tmp_path)
    assert R.main(["--freeze", "--registry-export", str(exp), "--out-dir", str(work), "--frozen-at", NOW]) == 0
    lm = json.loads((work / "LEVEL_MAP.json").read_text(encoding="utf-8"))
    fa = json.loads((work / "FAMILY_ASSETS.json").read_text(encoding="utf-8"))
    assert lm["_stamp"]["status"] == fa["_stamp"]["status"] == "FROZEN"
    assert lm["version"] == fa["version"] == "1.0" and not lm["version"].endswith("-draft")
    assert lm["registry_revision"] == PIN[0] and lm["_stamp"]["registry_fingerprint"] == PIN[1]
    assert lm["levels"] == LM["levels"] and lm["_stamp"]["dag_sha256"] == LM["_stamp"]["dag_sha256"]
    assert "FROZEN at J1" in lm["_stamp"]["registry_basis"] and "DRAFT" not in lm["_stamp"]["registry_basis"]
    assert R.main(["--check", "--pre-freeze", "--out-dir", str(work)]) == 0                   # the gate passes the frozen set
    assert R.main(["--out-dir", str(work), "--frozen-at", NOW]) == 2                          # a draft write cannot clobber it
    assert R.main(["--freeze", "--registry-export", str(exp), "--out-dir", str(work), "--frozen-at", NOW]) == 2
    assert R.main(["--freeze", "--registry-export", str(exp), "--out-dir", str(work), "--frozen-at", NOW, "--force"]) == 0


@pytest.mark.parametrize("what,mutate,needle", [
    ("an extra edge", lambda rows: _row(rows, "bg_texts")["depends_on"].append("bg_ontology"), "bg_texts: edge only in the export: bg_ontology"),
    ("a dropped edge", lambda rows: _row(rows, "ga_condition")["depends_on"].remove("ga_dashas"), "ga_condition: edge only in the draft input: ga_dashas"),
    ("an active asset missing", lambda rows: rows.remove(_row(rows, "lel_events")), "active asset only in the draft input: lel_events"),
    ("an extra active asset", lambda rows: rows.append(dict(asset_id="ka_new_asset", layer="kala", depends_on=[], active=True)),
     "active asset only in the export: ka_new_asset"),
])
def test_freeze_refuses_an_export_whose_active_edges_differ_and_prints_the_diff(tmp_path, capsys, what, mutate, needle):
    work = tmp_path / "w"
    work.mkdir()
    _write_copy(work, "DRAFT")
    before = _bytes(work)
    assert R.main(["--freeze", "--registry-export", str(_export(tmp_path, mutate)), "--out-dir", str(work), "--frozen-at", NOW]) == 2
    err = capsys.readouterr().err
    assert needle in err and "nothing written" in err, what
    assert _bytes(work) == before


def test_freeze_needs_an_export_and_a_timestamp(tmp_path):
    work = tmp_path / "w"
    work.mkdir()
    _write_copy(work, "DRAFT")
    assert R.main(["--freeze", "--out-dir", str(work), "--frozen-at", NOW]) == 2
    assert R.main(["--freeze", "--registry-export", str(_export(tmp_path)), "--out-dir", str(work)]) == 2


def test_export_diff_ignores_inactive_rows_and_row_order():
    rows = [dict(r) for r in ROWS]
    assert R.export_diff(ROWS, list(reversed(rows))) == []
    inactive = [r for r in rows if not r["active"]]
    assert R.export_diff(ROWS, [r for r in rows if r["active"]]) == [] and inactive
