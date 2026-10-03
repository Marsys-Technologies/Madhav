"""TI-L0-20 ordering rule, encoded (independent review L0C H-1).

THE HAZARD. The orchestrator's writer-gap pre-flight (pipeline/orchestrator/runner.py `_check_writer_registry_gaps`, default mode
`enforce`) makes EVERY run exit 1 when any @register()'d writer's asset_registry.has_writer is false (or the row is missing). PR #3055
registers two writers (bg_gochara_citation_resolution, bg_sarvatobhadra_grid) whose flags are false in production. If #3055's code
deploys BEFORE the has_writer flip migration (1280) has applied, every build in the system fails. The orchestrator is FROZEN, so the gate
cannot move into the runner.

THE MECHANISM (safest available without touching the frozen orchestrator). This test fails unless a migration under platform/migrations
sets has_writer = true for each of the two ids. migrate.ts applies a migration at the deploy of the commit that adds it, BEFORE that
deploy's images roll; so a tree in which this test passes has the flip merged (and therefore applied) no later than the writer code. #3055
can therefore not go green, and so not merge, before migration 1280 is in main (rebase #3055 after it). The reverse order is the safe one:
the flip first leaves two assets plannable without a registered writer (the guard is one-directional: has_writer true with no writer is not a
gap) until #3055 deploys - so no L0 build may be dispatched in between (wave plan: SS notifies Pravaha before 1280 is merged, and the L0 wave
window opens only after #3055 is deployed).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations"
IDS = ("bg_gochara_citation_resolution", "bg_sarvatobhadra_grid")


def flipped_ids(directory: Path) -> set[str]:
    """Asset ids some migration in `directory` sets has_writer = true for (statement-level, comments removed)."""
    found: set[str] = set()
    for f in sorted(directory.glob("*.sql")):
        code = "\n".join(l for l in f.read_text(encoding="utf-8", errors="ignore").splitlines() if not l.lstrip().startswith("--"))
        for m in re.finditer(r"UPDATE\s+asset_registry\s+SET\s+has_writer\s*=\s*true\b(.*?);", code, re.I | re.S):
            for i in IDS:
                if i in m.group(1):
                    found.add(i)
    return found


def test_the_two_new_writers_may_only_be_registered_in_a_tree_that_already_carries_the_has_writer_flip_migration():
    missing = set(IDS) - flipped_ids(MIGRATIONS)
    assert not missing, (
        f"writers registered for {sorted(missing)} but no migration in platform/migrations sets has_writer = true for them: "
        "with the orchestrator's writer-gap pre-flight in enforce mode every run would exit 1. Merge migration 1280 "
        "(L0 wave, suvarna/land/TI-mig-1280-001) FIRST, then rebase this PR."
    )


def test_the_scanner_can_fail(tmp_path):
    (tmp_path / "1.sql").write_text("-- UPDATE asset_registry SET has_writer = true WHERE asset_id IN ('bg_sarvatobhadra_grid');\nSELECT 1;")
    assert flipped_ids(tmp_path) == set(), "a commented-out flip must not count"
    (tmp_path / "2.sql").write_text("UPDATE asset_registry SET has_writer = true\n WHERE asset_id IN ('bg_sarvatobhadra_grid');")
    assert flipped_ids(tmp_path) == {"bg_sarvatobhadra_grid"}
    (tmp_path / "3.sql").write_text("UPDATE asset_registry SET has_writer = false WHERE asset_id = 'bg_gochara_citation_resolution';")
    assert flipped_ids(tmp_path) == {"bg_sarvatobhadra_grid"}, "has_writer = false is not a flip"
    (tmp_path / "4.sql").write_text("UPDATE asset_registry SET has_writer = true WHERE asset_id IN ('bg_gochara_citation_resolution', 'bg_sarvatobhadra_grid')\n   AND has_writer IS NOT TRUE;")
    assert flipped_ids(tmp_path) == set(IDS)
