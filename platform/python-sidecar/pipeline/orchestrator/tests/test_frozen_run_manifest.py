from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from pipeline.orchestrator.runner import _verify_registry_still_matches_manifest, validate_frozen_run_manifest


def _run() -> dict:
    return {
        "id": "run-1",
        "chart_id": "chart-1",
        "scope": "layer",
        "scope_target": "ganita",
        "action": "rebuild",
        "plan": ["ga_positions", "ga_strength"],
        "plan_manifest": {
            "version": "nirmana-run-manifest/v1",
            "chart_id": "chart-1",
            "scope": "layer",
            "scope_target": "ganita",
            "action": "rebuild",
            "waves": [["ga_positions"], ["ga_strength"]],
            "assets": [
                {"asset_id": "ga_positions", "scope": "per_chart", "depends_on": []},
                {"asset_id": "ga_strength", "scope": "per_chart", "depends_on": ["ga_positions"]},
            ],
        },
        "plan_manifest_digest": "2bcc158a779ad25af158ae75b3f3dca19167f0c2909ac7b01a22026076ad75bd",
    }


def test_valid_manifest_restores_the_persisted_dag_not_the_live_registry():
    frozen = validate_frozen_run_manifest(_run())

    assert frozen.plan == ["ga_positions", "ga_strength"]
    assert frozen.asset_scopes == {"ga_positions": "per_chart", "ga_strength": "per_chart"}
    assert frozen.asset_deps == {"ga_positions": [], "ga_strength": ["ga_positions"]}


def test_tampered_manifest_is_rejected_before_any_writer_can_run():
    run = _run()
    run["plan_manifest"]["assets"][1]["depends_on"] = []

    with pytest.raises(ValueError, match="digest"):
        validate_frozen_run_manifest(run)


def test_registry_dependency_drift_fails_closed_instead_of_replanning_the_run():
    class Cursor:
        def execute(self, _sql, _params):
            pass

        def fetchall(self):
            return [
                {"asset_id": "ga_positions", "scope": "per_chart", "depends_on": []},
                # A later registry edit must not add an edge to an accepted run.
                {"asset_id": "ga_strength", "scope": "per_chart", "depends_on": ["ga_positions", "ga_extra"]},
            ]

    with pytest.raises(ValueError, match="changed after dispatch"):
        _verify_registry_still_matches_manifest(Cursor(), validate_frozen_run_manifest(_run()))
