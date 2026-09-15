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

PINS = json.loads(subprocess.check_output(
    [
        "git",
        "show",
        "5142109f7f219ea860f859e322646f79d875bee8:platform/src/generated/nirmana-analysis-layer-pins.json",
    ],
    cwd=REPO,
))
BASELINE = pins_module._inventory_at_commit(
    "c558e60d3267ded79d65fd25f50ee926ce27b75a"
)


def candidate_with_one_l2_delta() -> dict[str, str]:
    candidate = dict(BASELINE)
    candidate["bo_anveshana"] = "f" * 64
    return candidate


def admission(classification: str = "approved_intentional_change") -> dict:
    return pins_module.admit_successor(
        PINS,
        layer="L2",
        previous_writer_digests=BASELINE,
        candidate_writer_digests=candidate_with_one_l2_delta(),
        source_commit="1" * 40,
        review_refs=["review-artifact@" + "2" * 64],
        authority_decision="DP-SD-018",
        authority_commit="3" * 40,
        reason="bounded fixture successor",
        classifications={"bo_anveshana": classification},
        historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
    )


def test_successor_archives_complete_predecessor_and_exact_delta() -> None:
    result = admission()
    archived = result["history"]["L2"][0]
    active = result["layers"]["L2"]

    assert result["version"] == pins_module.PINS_VERSION
    assert archived["pin"] == PINS["layers"]["L2"]
    assert archived["writer_digests"] == {
        key: value for key, value in BASELINE.items() if key.startswith("bo_")
    }
    assert active["supersedes_generation_id"] == archived["generation_id"]
    assert archived["superseded_by_generation_id"] == active["generation_id"]
    assert active["admission"]["changed_assets"] == ["bo_anveshana"]
    assert active["admission"]["delta_classifications"] == {
        "bo_anveshana": "approved_intentional_change"
    }
    assert all(
        result["layers"][layer] == PINS["layers"][layer]
        for layer in pins_module.LAYER_PREFIX
        if layer != "L2"
    )


def test_successor_rejects_missing_or_excess_delta_classification() -> None:
    with pytest.raises(SystemExit, match="cover exactly"):
        pins_module.admit_successor(
            PINS,
            layer="L2",
            previous_writer_digests=BASELINE,
            candidate_writer_digests=candidate_with_one_l2_delta(),
            source_commit="1" * 40,
            review_refs=["2" * 40],
            authority_decision="DP-SD-018",
            authority_commit="3" * 40,
            reason="fixture",
            classifications={},
            historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
        )

    with pytest.raises(SystemExit, match="cover exactly"):
        pins_module.admit_successor(
            PINS,
            layer="L2",
            previous_writer_digests=BASELINE,
            candidate_writer_digests=candidate_with_one_l2_delta(),
            source_commit="1" * 40,
            review_refs=["2" * 40],
            authority_decision="DP-SD-018",
            authority_commit="3" * 40,
            reason="fixture",
            classifications={
                "bo_anveshana": "approved_intentional_change",
                "ga_positions": "derived_import_change",
            },
            historical_snapshot_commit="c558e60d3267ded79d65fd25f50ee926ce27b75a",
        )


def test_successor_rejects_unapproved_foreign_delta() -> None:
    with pytest.raises(SystemExit, match="cannot be admitted"):
        admission("unapproved_foreign_source")

    with pytest.raises(SystemExit, match="unsupported delta classifications"):
        admission("invented_bypass")


def test_check_detects_historical_snapshot_tampering() -> None:
    result = admission()
    result["history"]["L2"][0]["writer_digests"]["bo_anveshana"] = "0" * 64

    failures = pins_module.check(result, candidate_with_one_l2_delta())

    assert any("historical aggregate" in failure for failure in failures)

    result = admission()
    result["history"]["L2"][0]["historical_snapshot_commit"] = (
        "d2369b888e760e5b8d693328f00683877cbd5f28"
    )
    failures = pins_module.check(result, candidate_with_one_l2_delta())
    assert any("immutable historical commit" in failure for failure in failures)


def test_check_rejects_source_commit_with_a_different_inventory() -> None:
    result = admission()
    active = result["layers"]["L2"]
    active["convergence_commit"] = "c558e60d3267ded79d65fd25f50ee926ce27b75a"
    active["admission"]["source_commit"] = active["convergence_commit"]
    active["generation_id"] = pins_module.generation_id("L2", active)
    result["history"]["L2"][0]["superseded_by_generation_id"] = active[
        "generation_id"
    ]

    failures = pins_module.check(result, candidate_with_one_l2_delta())

    assert any("immutable source commit" in failure for failure in failures)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda document: document["layers"]["L2"]["admission"].update(
                source_commit="4" * 40
            ),
            "source commit",
        ),
        (
            lambda document: document["layers"]["L2"].update(
                generation_id="l2:stale:generation"
            ),
            "generation_id",
        ),
        (
            lambda document: document["layers"]["L2"]["admission"].update(
                authority_decision=""
            ),
            "authority decision",
        ),
        (
            lambda document: document["layers"]["L2"].update(
                writer_inventory_sha256="0" * 64
            ),
            "writer_inventory_sha256 is stale",
        ),
    ],
)
def test_check_rejects_wrong_source_stale_generation_definition_and_hash(
    mutate,
    message: str,
) -> None:
    result = copy.deepcopy(admission())
    mutate(result)

    failures = pins_module.check(result, candidate_with_one_l2_delta())

    assert any(message in failure for failure in failures)
