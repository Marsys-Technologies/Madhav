"""C52 guard — no A5.3 suite is ever silently skipped in CI.

Every `tests/l3/gochara/test_a53_*.py` file must be either

  (a) in the A5.3 DB step's pytest file list in `.github/workflows/ci.yml`
      (the `python -m pytest tests/l3/gochara/...` invocation of the job that
      sets GOCHARA_A53_REQUIRE_DB=1), or

  (b) in the EXCLUDED dict below — explicit, one entry per file, each with its
      reason. An exclusion is a decision someone owns, never a file the list
      forgot about.

A new suite that is neither added to the CI list nor excluded here fails this
guard; an exclusion that has since been admitted to CI fails it too (stale).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
GOCHARA_DIR = Path(__file__).resolve().parent
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"

#: Files NOT run in the A5.3 DB step today. Reason for every entry, uniformly:
#: not yet admitted to the DB step — admission is decided file by file by
#: Stream A's audit of tests/l3/gochara (steward C52-ADD, 2026-10-03); the
#: guard pins the gap explicitly so the skip is never silent. Remove an entry
#: when the file is added to the CI list (this guard fails on stale entries).
EXCLUDED = {
    "test_a53_1241_fixture_pin.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_am5_writer.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_aspect_span.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_dasha_read.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_ephemeral_tier_rule.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_gochara_v5_writer.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_inventory.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_materialise.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_member_geometry.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_moon_on_demand.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_p1_house_descriptor.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_r18_graha_map_parity.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_r86_sweep.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_record_store.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_rule_registry.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_rule_registry_versions.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_substrate_store.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_targets.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_version_selection.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_window_evaluator.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_window_sweep.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_window_sweep_pg.py": "not yet admitted — Stream A audit decides (C52-ADD)",
    "test_a53_writerbase_conformance.py": "not yet admitted — Stream A audit decides (C52-ADD)",
}


def _ci_db_step_a53_files() -> set[str]:
    ci = CI_YML.read_text(encoding="utf-8")
    return set(re.findall(r"tests/l3/gochara/(test_a53_\w+\.py)", ci))


def test_every_a53_suite_is_in_the_ci_db_list_or_explicitly_excluded():
    listed = _ci_db_step_a53_files()
    on_disk = {p.name for p in GOCHARA_DIR.glob("test_a53_*.py")}

    unaccounted = sorted(f for f in on_disk if f not in listed and f not in EXCLUDED)
    assert not unaccounted, (
        "A5.3 suites that are neither in the CI DB step's file list nor in this guard's "
        f"exclusion list: {unaccounted} — add each to .github/workflows/ci.yml or exclude it "
        "here with a reason; a silent skip is not allowed")

    stale = sorted(f for f, reason in EXCLUDED.items() if f in listed)
    assert not stale, (
        f"excluded suites that are now in the CI DB step's list: {stale} — remove the stale "
        "exclusion entries")

    missing = sorted(set(EXCLUDED) - on_disk)
    assert not missing, (
        f"exclusion entries for files that do not exist: {missing} — remove them")

    # the guard guards itself: it must be run by the step it guards
    assert Path(__file__).name in listed, (
        "the guard test itself is not in the CI DB step's file list — it would never run")
