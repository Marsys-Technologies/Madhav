from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO / "platform/scripts/generate/nirmana_analysis_layer_pins.py"
SPEC = importlib.util.spec_from_file_location("nirmana_analysis_layer_pins", MODULE_PATH)
assert SPEC and SPEC.loader
pins_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pins_module)

LEGACY_PINS = json.loads(
    subprocess.check_output(
        [
            "git",
            "show",
            "5142109f7f219ea860f859e322646f79d875bee8:"
            "platform/src/generated/nirmana-analysis-layer-pins.json",
        ],
        cwd=REPO,
    )
)
CURRENT_PINS = json.loads(pins_module.PINS_PATH.read_text(encoding="utf-8"))
BASELINE = pins_module._inventory_at_commit(
    "c558e60d3267ded79d65fd25f50ee926ce27b75a"
)
CANDIDATE = pins_module._inventory_at_commit(
    "d2369b888e760e5b8d693328f00683877cbd5f28"
)
L2_CHANGED = sorted(
    asset_id
    for asset_id in set(BASELINE) | set(CANDIDATE)
    if asset_id.startswith("bo_") and BASELINE.get(asset_id) != CANDIDATE.get(asset_id)
)
L2_CLASSIFICATIONS = {
    asset_id: "approved_intentional_change" for asset_id in L2_CHANGED
}


def admission(classifications: dict[str, str] | None = None) -> dict:
    return pins_module.admit_successor(
        LEGACY_PINS,
        layer="L2",
        previous_writer_digests=BASELINE,
        candidate_writer_digests=CANDIDATE,
        source_commit="d2369b888e760e5b8d693328f00683877cbd5f28",
        review_artifacts=copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"]),
        authority_decision="DP-SD-018",
        authority_commit="7f21f27b14a7909424591a530096dc2f5d6e2b13",
        reason="bounded fixture successor",
        classifications=classifications or L2_CLASSIFICATIONS,
        historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
        definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
    )


def test_successor_archives_complete_predecessor_and_exact_delta() -> None:
    result = admission()
    archived = result["history"]["L2"][0]
    active = result["layers"]["L2"]

    assert result["version"] == pins_module.PINS_VERSION
    assert archived["pin"] == LEGACY_PINS["layers"]["L2"]
    assert archived["writer_digests"] == {
        key: value for key, value in BASELINE.items() if key.startswith("bo_")
    }
    assert active["supersedes_generation_id"] == archived["generation_id"]
    assert archived["superseded_by_generation_id"] == active["generation_id"]
    assert active["admission"]["changed_assets"] == L2_CHANGED
    assert active["admission"]["delta_classifications"] == L2_CLASSIFICATIONS
    assert result["definition_bindings"] == pins_module.build_definition_bindings(
        "5142109f7f219ea860f859e322646f79d875bee8"
    )
    assert all(
        result["layers"][layer] == LEGACY_PINS["layers"][layer]
        for layer in pins_module.LAYER_PREFIX
        if layer != "L2"
    )


def test_successor_rejects_missing_wrong_layer_and_unapproved_classification() -> None:
    missing = dict(L2_CLASSIFICATIONS)
    missing.pop(L2_CHANGED[0])
    with pytest.raises(SystemExit, match="cover exactly"):
        admission(missing)

    wrong_layer = dict(L2_CLASSIFICATIONS)
    wrong_layer["ga_positions"] = "derived_import_change"
    with pytest.raises(SystemExit, match="cover exactly"):
        admission(wrong_layer)

    foreign = dict(L2_CLASSIFICATIONS)
    foreign[L2_CHANGED[0]] = "unapproved_foreign_source"
    with pytest.raises(SystemExit, match="cannot be admitted"):
        admission(foreign)

    unsupported = dict(L2_CLASSIFICATIONS)
    unsupported[L2_CHANGED[0]] = "invented_bypass"
    with pytest.raises(SystemExit, match="unsupported delta classifications"):
        admission(unsupported)


def test_nonexistent_authority_and_review_commits_are_rejected() -> None:
    with pytest.raises(SystemExit, match="not bound"):
        pins_module.admit_successor(
            LEGACY_PINS,
            layer="L2",
            previous_writer_digests=BASELINE,
            candidate_writer_digests=CANDIDATE,
            source_commit="d2369b888e760e5b8d693328f00683877cbd5f28",
            review_artifacts=copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"]),
            authority_decision="DP-SD-018",
            authority_commit="0" * 40,
            reason="fixture",
            classifications=L2_CLASSIFICATIONS,
            historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
            definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
        )

    nonexistent = copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"][0])
    nonexistent["commit"] = "0" * 40
    with pytest.raises(SystemExit, match="does not carry"):
        pins_module.validate_artifact_binding(nonexistent, "fixture review")


def test_wrong_acceptance_artifact_or_content_digest_is_rejected() -> None:
    wrong_layer_artifact = copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L3"])
    with pytest.raises(SystemExit, match="required acceptance artifacts"):
        pins_module.admit_successor(
            LEGACY_PINS,
            layer="L2",
            previous_writer_digests=BASELINE,
            candidate_writer_digests=CANDIDATE,
            source_commit="d2369b888e760e5b8d693328f00683877cbd5f28",
            review_artifacts=wrong_layer_artifact,
            authority_decision="DP-SD-018",
            authority_commit="7f21f27b14a7909424591a530096dc2f5d6e2b13",
            reason="fixture",
            classifications=L2_CLASSIFICATIONS,
            historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
            definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
        )

    wrong_digest = copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"][0])
    wrong_digest["sha256"] = "0" * 64
    with pytest.raises(SystemExit, match="content digest"):
        pins_module.validate_artifact_binding(wrong_digest, "fixture review")


def test_definition_binding_rejects_wrong_digest_overlap_and_retired_sweep_loss() -> None:
    wrong_digest = copy.deepcopy(CURRENT_PINS)
    wrong_digest["definition_bindings"]["L3"]["membership_sha256"] = "0" * 64
    assert any(
        "definition membership digest" in failure
        for failure in pins_module.check(wrong_digest, CANDIDATE)
    )

    overlap = copy.deepcopy(CURRENT_PINS)
    overlap["layers"]["L3"]["non_writer_assets"].append("ka_sangam")
    overlap["layers"]["L3"]["non_writer_assets"].sort()
    assert any(
        "writer-disjoint" in failure for failure in pins_module.check(overlap, CANDIDATE)
    )

    retired_removed = copy.deepcopy(CURRENT_PINS)
    retired_removed["layers"]["L3"]["non_writer_assets"] = []
    retired_removed["layers"]["L3"]["receipt_count"] = 22
    assert any(
        "active membership differs from immutable definition" in failure
        for failure in pins_module.check(retired_removed, CANDIDATE)
    )


def test_historical_pin_and_writer_rewrites_are_rejected() -> None:
    rewritten_writers = copy.deepcopy(CURRENT_PINS)
    rewritten_writers["history"]["L2"][0]["writer_digests"]["bo_anveshana"] = "0" * 64
    failures = pins_module.check(rewritten_writers, CANDIDATE)
    assert any("immutable historical snapshot" in failure for failure in failures)

    rewritten_pin = copy.deepcopy(CURRENT_PINS)
    rewritten_pin["history"]["L2"][0]["pin"]["convergence_commit"] = "0" * 40
    failures = pins_module.check(rewritten_pin, CANDIDATE)
    assert any("archived pin differs" in failure for failure in failures)


def test_full_two_successor_chain_is_valid_and_rewrite_is_detected(monkeypatch) -> None:
    second_source = "1" * 40
    second_snapshot = "2" * 40
    second_inventory = dict(CANDIDATE)
    second_inventory["bo_anveshana"] = "f" * 64
    real_inventory_at_commit = pins_module._inventory_at_commit
    real_pins_at_commit = pins_module._pins_at_commit
    real_commit_exists = pins_module._commit_exists

    def inventory_at_commit(commit: str) -> dict[str, str]:
        if commit == second_source:
            return second_inventory
        if commit == second_snapshot:
            return CANDIDATE
        return real_inventory_at_commit(commit)

    def pins_at_commit(commit: str) -> dict:
        if commit == second_snapshot:
            return CURRENT_PINS
        return real_pins_at_commit(commit)

    def commit_exists(commit: str) -> bool:
        return commit in {second_source, second_snapshot} or real_commit_exists(commit)

    monkeypatch.setattr(pins_module, "_inventory_at_commit", inventory_at_commit)
    monkeypatch.setattr(pins_module, "_pins_at_commit", pins_at_commit)
    monkeypatch.setattr(pins_module, "_commit_exists", commit_exists)
    monkeypatch.setitem(
        pins_module.AUTHORIZED_SOURCE_COMMITS["DP-SD-018"],
        "L2",
        frozenset({"d2369b888e760e5b8d693328f00683877cbd5f28", second_source}),
    )
    two_successors = pins_module.admit_successor(
        CURRENT_PINS,
        layer="L2",
        previous_writer_digests=CANDIDATE,
        candidate_writer_digests=second_inventory,
        source_commit=second_source,
        review_artifacts=copy.deepcopy(pins_module.EXPECTED_REVIEW_ARTIFACTS["L2"]),
        authority_decision="DP-SD-018",
        authority_commit="7f21f27b14a7909424591a530096dc2f5d6e2b13",
        reason="second bounded fixture successor",
        classifications={"bo_anveshana": "approved_intentional_change"},
        historical_snapshot_commit=second_snapshot,
        definition_snapshot_commit="5142109f7f219ea860f859e322646f79d875bee8",
    )
    assert pins_module.check(two_successors, second_inventory) == []

    two_successors["history"]["L2"][1]["pin"]["convergence_commit"] = "0" * 40
    failures = pins_module.check(two_successors, second_inventory)
    assert any("archived pin differs" in failure for failure in failures)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda document: document["layers"]["L2"]["admission"].update(
                source_commit="0" * 40
            ),
            "source commit",
        ),
        (
            lambda document: document["layers"]["L2"].update(
                generation_id="l2:stale:generation"
            ),
            "generation id",
        ),
        (
            lambda document: document["layers"]["L2"].update(
                writer_inventory_sha256="0" * 64
            ),
            "writer_inventory_sha256 is stale",
        ),
    ],
)
def test_check_rejects_wrong_source_stale_generation_and_hash(
    mutate,
    message: str,
) -> None:
    result = copy.deepcopy(CURRENT_PINS)
    mutate(result)

    failures = pins_module.check(result, CANDIDATE)

    assert any(message in failure for failure in failures)
