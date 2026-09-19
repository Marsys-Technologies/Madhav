"""N1-A DEFECT-1 regression.

dispatch_frozen_rebuild.py used to hardcode WRITER_DIGESTS_PATH to an absolute path under
a different, unrelated worktree (`/Users/Dev/nirmana-s/l3/...`) — the old L3 fleet's checkout,
last updated 2026-09-10 and stale relative to this repo. A dispatch built on that stale digest
would feed `expected_code_digest` into the run manifest without it actually describing the code
that runs, defeating the digest gate this script exists to enforce. Proves the path now resolves
relative to the repository root and matches the real generated-digests file that ships in this repo.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO / "platform/scripts/dispatch_frozen_rebuild.py"
SPEC = importlib.util.spec_from_file_location("dispatch_frozen_rebuild", MODULE_PATH)
assert SPEC and SPEC.loader
dispatch_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dispatch_module)


def test_writer_digests_path_resolves_inside_this_repo() -> None:
    assert dispatch_module.WRITER_DIGESTS_PATH.is_relative_to(REPO)
    assert dispatch_module.WRITER_DIGESTS_PATH == (
        REPO / "platform/src/generated/nirmana-writer-digests.json"
    )


def test_writer_digests_path_exists_and_is_not_the_old_fleet_worktree() -> None:
    assert dispatch_module.WRITER_DIGESTS_PATH.exists()
    assert "nirmana-s" not in str(dispatch_module.WRITER_DIGESTS_PATH)


def test_loaded_digest_matches_current_generated_inventory() -> None:
    inventory = json.loads(dispatch_module.WRITER_DIGESTS_PATH.read_text(encoding="utf-8"))
    for asset_id in ("ga_positions", "ga_dashas"):
        assert dispatch_module._load_writer_digest(asset_id) == inventory["writers"][asset_id]
