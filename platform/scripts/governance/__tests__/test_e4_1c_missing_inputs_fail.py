"""test_e4_1c_missing_inputs_fail.py -- the Nikasha input skip map is retired; a missing input now FAILS.

Before E4.1c, `__tests__/conftest.py` skipped ~51 tests whenever the campaign artifact they pin (T4 template, L0 v3
strategy, L0 pilot briefs, asset_gaps.jsonl, producer_provenance.derived.json) was absent from the tree. That was a
skip that could never fail, i.e. a test that reads green whether or not the thing it guards exists (CLAUDE.md
section N.8). The inputs are on main now (E4.1-build-002a, E4.3-fold-001), so the map is gone.

This test earns that signal without touching a real file. It builds two tmp copies of the minimal repo layout the
13 formerly mapped modules need and runs those modules in a subprocess:

  * CONTROL  -- every input present            -> 0 failed, 0 errors, 0 skipped (the harness itself is sound);
  * ABSENT   -- the mapped inputs left out      -> 0 skipped and >= 1 failed/errored per module (a missing input
                                                   fails; it does not skip).

A conftest skip map reintroduced into the real __tests__ dir is copied into the tmp tree and turns ABSENT's
"0 skipped" assertion red.

Live-DB skips are not in scope: they live inside the test files (skipif / pytest.skip on missing PG env), never in
conftest, and are untouched.
"""
import pathlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
N = "00_ARCHITECTURE/briefs/nirmana"

# the inputs the retired skip map named (path -> why it is a test input)
MAPPED_INPUTS = [
    f"{N}/ASSET_ELEVATION_TEMPLATE_v2_0.md",
    f"{N}/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md",
    f"{N}/l0_assets/BG_ONTOLOGY_ELEVATION_BRIEF_v1_0.md",
    f"{N}/l0_assets/BG_PANCHANGA_ELEVATION_BRIEF_v1_0.md",
    f"{N}/l0_assets/BG_EPHEMERIS_ELEVATION_BRIEF_v1_0.md",
    f"{N}/l0_assets/BG_RULES_ELEVATION_BRIEF_v1_0.md",
    f"{N}/l0_assets/BG_SARVATOBHADRA_GRID_ELEVATION_BRIEF_v1_0.md",
    "00_ARCHITECTURE/control/asset_gaps.jsonl",
    f"{N}/nikasha_test/provenance/producer_provenance.derived.json",
]

# module -> the input whose absence must now fail it (every module in the old map)
FORMER_MAP = {
    "test_f7_l0v3_line526_320_gates.py": f"{N}/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md",
    "test_r63_t4_nine_gates.py": f"{N}/ASSET_ELEVATION_TEMPLATE_v2_0.md",
    "test_r64_t4_nine_checks_heading.py": f"{N}/ASSET_ELEVATION_TEMPLATE_v2_0.md",
    "test_r68_t4_na_spelling.py": f"{N}/ASSET_ELEVATION_TEMPLATE_v2_0.md",
    "test_r69_l0v3_0_360_gates.py": f"{N}/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md",
    "test_r70_l0v3_stale_figures_datestamped.py": f"{N}/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v3_0.md",
    "test_r77_l0_pilot_briefs_build_row.py": f"{N}/l0_assets/BG_ONTOLOGY_ELEVATION_BRIEF_v1_0.md",
    "test_catalog_provenance.py": f"{N}/nikasha_test/provenance/producer_provenance.derived.json",
    "test_r15_r29_hand_row_census_run_id.py": "00_ARCHITECTURE/control/asset_gaps.jsonl",
    "test_r80_schema_superseded_by_field.py": "00_ARCHITECTURE/control/asset_gaps.jsonl",
    "test_r81_apply_script.py": "00_ARCHITECTURE/control/asset_gaps.jsonl",
    "test_r81_ledger_overlap_fold.py": "00_ARCHITECTURE/control/asset_gaps.jsonl",
}

# repo files the governance modules read besides the mapped inputs (everything else a module needs is inside
# platform/scripts/governance itself)
SUPPORT = [
    "platform/src/generated/capability_knowledge.snapshot.json",
    "00_ARCHITECTURE/control/asset_elevation_tracker.py",
]


def _build_tree(dest: pathlib.Path, with_inputs: bool) -> pathlib.Path:
    shutil.copytree(REPO / "platform/scripts/governance", dest / "platform/scripts/governance",
                    ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    rels = list(SUPPORT) + (MAPPED_INPUTS if with_inputs else [])
    for rel in rels:
        src = REPO / rel
        if not src.exists():
            continue
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest / rel)
    return dest


def _run(tree: pathlib.Path, tmp_path: pathlib.Path, tag: str) -> dict:
    junit = tmp_path / f"{tag}.xml"
    mods = [str(tree / "platform/scripts/governance/__tests__" / m) for m in FORMER_MAP]
    subprocess.run([sys.executable, "-m", "pytest", *mods, "-q", "--no-header", "-p", "no:cacheprovider",
                    f"--junitxml={junit}"], cwd=tree, capture_output=True, text=True, timeout=900,
                   env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": "0", "HOME": str(tmp_path)})
    per: dict = {m: {"passed": 0, "failed": 0, "skipped": 0} for m in FORMER_MAP}
    for tc in ET.parse(junit).getroot().iter("testcase"):
        mod = tc.get("classname", "").split(".")[-1] + ".py"
        if mod not in per:
            continue
        kinds = {c.tag for c in tc}
        key = "skipped" if "skipped" in kinds else "failed" if kinds & {"failure", "error"} else "passed"
        per[mod][key] += 1
    return per


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    base = tmp_path_factory.mktemp("e41c")
    control = _build_tree(base / "control", with_inputs=True)
    absent = _build_tree(base / "absent", with_inputs=False)
    return {"control": _run(control, base, "control"), "absent": _run(absent, base, "absent")}


def test_the_real_conftest_no_longer_carries_a_skip_map():
    conftest = HERE / "conftest.py"
    if conftest.exists():
        text = conftest.read_text(encoding="utf-8")
        assert "_REQUIRES" not in text and "pytest.mark.skip" not in text and "pytest_collection_modifyitems" not in text


def test_control_tree_with_every_input_present_has_no_failure_and_no_skip(runs):
    for mod, c in runs["control"].items():
        assert c["passed"] > 0, f"{mod}: the control run collected nothing ({c})"
        assert c["failed"] == 0 and c["skipped"] == 0, f"{mod}: control run not clean: {c}"


@pytest.mark.parametrize("mod", sorted(FORMER_MAP))
def test_a_missing_input_fails_the_formerly_mapped_module_instead_of_skipping(runs, mod):
    a = runs["absent"][mod]
    assert a["skipped"] == 0, f"{mod}: a missing input skipped {a['skipped']} test(s) -- a skip that cannot fail"
    assert a["failed"] >= 1, f"{mod}: a missing input ({FORMER_MAP[mod]}) failed nothing: {a}"
