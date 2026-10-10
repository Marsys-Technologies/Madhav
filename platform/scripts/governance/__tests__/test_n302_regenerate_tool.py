"""test_n302_regenerate_tool.py -- N-301/N-302: the one-command regenerator exists, runs the steps in dependency order, and every CI failure
message for a stale generated aggregate names it.

HONEST SCOPE: this is a STATIC pin (the file, the order of its steps, its two modes, the wording of the four failure messages). The behavioural
proof (change a writer: `--check` exits 1; the write run regenerates only the stale aggregates; restoring the writer and running again leaves a
clean tree) was run by hand against the real tools and is recorded in the PR; it needs node, the sidecar's Python dependencies and git, which this
test does not assume.
"""
from __future__ import annotations

import os
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]
TOOL = REPO / "platform/scripts/regenerate_generated.sh"
NAME = "regenerate_generated.sh"
MESSAGE_SOURCES = (
    "platform/python-sidecar/pipeline/orchestrator/provenance_inventory.py",
    "platform/scripts/generate_capability_estate_census.ts",
    "platform/scripts/generate_capability_knowledge.ts",
    "platform/scripts/governance/asset_census.py",
    "platform/scripts/governance/__tests__/test_e6_5_registry_check.py",           # the registry-report CI gate (a pytest assertion message)
)


def test_tool_exists_and_is_executable():
    assert TOOL.is_file()
    assert os.access(TOOL, os.X_OK)


def test_steps_run_in_dependency_order():
    text = TOOL.read_text(encoding="utf-8")
    order = [text.index(k) for k in ("1/4 writer digests", "2/4 capability estate census", "3/4 capability knowledge snapshot", "4/4 registry coverage report")]
    assert order == sorted(order), "digests, then the census that hashes them, then the snapshot compiled from the census"
    assert "--check" in text and 'MODE="check"' in text, "a check-only mode (what CI does)"


def test_a_step_writes_only_when_its_own_check_fails():
    text = TOOL.read_text(encoding="utf-8")
    assert "ensure()" in text and "left untouched" in text


def test_the_rule_is_stated_in_the_tool():
    text = TOOL.read_text(encoding="utf-8")
    assert "never hand-merge" in text.lower()


def test_every_stale_aggregate_message_names_the_tool():
    for rel in MESSAGE_SOURCES:
        assert NAME in (REPO / rel).read_text(encoding="utf-8"), rel


def test_the_snapshot_stamp_is_one_canonical_value_so_either_side_converges():
    import json
    text = TOOL.read_text(encoding="utf-8")
    stamp = json.loads((REPO / "platform/src/generated/capability_knowledge.snapshot.json").read_text(encoding="utf-8"))["generated_at"]
    assert f'SNAPSHOT_STAMP="{stamp}"' in text, "the tool's canonical stamp must equal the committed snapshot's"


def test_checks_keep_their_reason_and_the_tool_states_what_it_does_not_regenerate():
    text = TOOL.read_text(encoding="utf-8")
    assert "reason:" in text and "stale link can leave the links after it stale" in text
    assert "nirmana-analysis-layer-pins.json" in text
