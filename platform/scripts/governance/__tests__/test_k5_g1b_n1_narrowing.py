"""K5-G1b-N1 (PR #3758 review finding K5-G1b-N1-R-B1): an accepted verdict must not read as full closure.

The PR lands only the shift-schedule object. The jury-shared once-per-candidate preparation (PLAN
KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md §6.2(2,5,7)) is registered as the child K5-G1b-N2, and the tracker, given
K5-G1b-N1 accepted, must still show the child not done. Reverting the plan model to the unnarrowed item fails here.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "platform/scripts/governance"))
from pravaha_tracker.state import build_snapshot  # noqa: E402


def items():
    model = json.loads((ROOT / "00_ARCHITECTURE/control/kalayantra/plan_model.json").read_text(encoding="utf-8"))
    return model, {row["id"]: row for row in model["items"]}


def test_the_unfinished_jury_sharing_is_a_tracked_child_not_claimed_by_the_parent():
    _, by_id = items()
    parent, child = by_id["K5-G1b-N1"], by_id["K5-G1b-N2"]
    assert child["depends_on"] == ["K5-G1b-N1"] and child["mandatory"] is True
    # the three gaps the review found are the child's contract, named at their code locations
    for gap in ("ka_sangam/jury/agreement.py", "rebuilt per", "content-bound"):
        assert gap in json.dumps(child["brief"]) or gap in json.dumps(parent["brief"]["contract"]), gap
    assert "K5-G1b-N2" in parent["brief"]["contract"]
    # the parent no longer titles itself as the unfinished jury-shared preparation
    assert "remains unfinished" not in parent["title"] and "schedule object only" in parent["title"]


def test_an_accepted_parent_leaves_the_child_open():
    model, _ = items()
    events = [dict(kind="item", item=row["id"], actor="steward", state="done", guarded=True,
                   evidence="synthetic independently accepted input", ts="2026-10-19T00:00:00Z")
              for row in model["items"] if row["id"] != "K5-G1b-N2" and row.get("done_by") != "decision"]
    view = build_snapshot(model, events, {}, {}, {})
    rows = {r["id"]: r for track in view["tracks"] for r in track["items"]}
    assert rows["K5-G1b-N1"]["status"] == "done"
    assert rows["K5-G1b-N2"]["status"] != "done"
