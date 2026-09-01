from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "dispatch_nirmana_f0_canary.py"


def _load_dispatch_module():
    if not SCRIPT_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location("dispatch_nirmana_f0_canary", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_builds_runner_compatible_single_asset_frozen_manifest() -> None:
    """Catches a dispatcher that omits or changes runner-validated manifest metadata."""
    module = _load_dispatch_module()
    assert module is not None, "the governed F0 canary dispatcher is missing"

    manifest, digest = module.build_canary_manifest(
        chart_id="482012f1-710e-4a25-994a-93821f5871aa",
        candidate={
            "asset_id": "bg_vedha_malefic_scale",
            "layer": "brahmagyan",
            "scope": "global",
            "asset_kind": "data",
            "depends_on": [],
            "natural_key_partition": None,
            "has_cowriters": False,
        },
        expected_code_digest="6441652129a1c35e3759a4beb83830b1f470a12bae93ee218abb9091aa00469f",
    )

    assert manifest == {
        "version": "nirmana-run-manifest/v1",
        "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
        "scope": "asset_set",
        "scope_target": "bg_vedha_malefic_scale",
        "action": "rebuild",
        "waves": [["bg_vedha_malefic_scale"]],
        "assets": [{
            "asset_id": "bg_vedha_malefic_scale",
            "scope": "global",
            "depends_on": [],
            "natural_key_partition": None,
            "has_cowriters": False,
            "expected_code_digest": "6441652129a1c35e3759a4beb83830b1f470a12bae93ee218abb9091aa00469f",
        }],
    }
    assert digest == "a57cb88591b9873400e9ea2999bf683ffac8bfe00c4c29227809d8b3777761de"


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"layer": "ganita"}, "must be an L0 asset"),
        ({"scope": "per_chart"}, "must be global"),
        ({"asset_kind": "service"}, "must be a data asset"),
        ({"depends_on": ["bg_reference"]}, "must have no dependencies"),
        ({"has_cowriters": True}, "must not share its target table"),
        ({"natural_key_partition": "constant_id"}, "must use the whole-asset partition"),
        ({"asset_id": "bg_ghatana"}, "only approved asset"),
    ],
)
def test_rejects_a_canary_that_cannot_isolate_foundation_machinery(override, message) -> None:
    """Catches widening the canary into downstream, dependency, or co-writer work."""
    module = _load_dispatch_module()
    assert module is not None, "the governed F0 canary dispatcher is missing"
    candidate = {
        "asset_id": "bg_vedha_malefic_scale",
        "layer": "brahmagyan",
        "scope": "global",
        "asset_kind": "data",
        "depends_on": [],
        "natural_key_partition": None,
        "has_cowriters": False,
    }
    candidate.update(override)

    with pytest.raises(ValueError, match=message):
        module.build_canary_manifest(
            chart_id="482012f1-710e-4a25-994a-93821f5871aa",
            candidate=candidate,
            expected_code_digest="6441652129a1c35e3759a4beb83830b1f470a12bae93ee218abb9091aa00469f",
        )


def test_rejects_any_chart_other_than_the_frozen_campaign_chart() -> None:
    """Catches an operator override widening the canary to another chart."""
    module = _load_dispatch_module()
    assert module is not None
    with pytest.raises(ValueError, match="only approved chart"):
        module.build_canary_manifest(
            chart_id="11111111-1111-4111-8111-111111111111",
            candidate={
                "asset_id": "bg_vedha_malefic_scale",
                "layer": "brahmagyan",
                "scope": "global",
                "asset_kind": "data",
                "depends_on": [],
                "natural_key_partition": None,
                "has_cowriters": False,
            },
            expected_code_digest="6441652129a1c35e3759a4beb83830b1f470a12bae93ee218abb9091aa00469f",
        )


def test_dispatches_the_committed_run_with_only_the_ratified_run_id_override() -> None:
    """Catches stale env-var/no-args Cloud Run dispatches and wrong job targeting."""
    module = _load_dispatch_module()
    assert module is not None
    observed = []

    def run(command, **kwargs):
        observed.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="execution-123\n", stderr="")

    execution = module.dispatch_canary_run(
        run_id="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        project="madhav-astrology",
        region="asia-south1",
        job="brahma-build-pipeline-job",
        run_command=run,
    )

    assert execution == "execution-123"
    assert observed == [(
        [
            "gcloud", "run", "jobs", "execute", "brahma-build-pipeline-job",
            "--project=madhav-astrology",
            "--region=asia-south1",
            "--args=--run-id,aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
            "--async",
            "--format=value(metadata.name)",
        ],
        {"capture_output": True, "check": False, "text": True},
    )]


def test_terminalizes_a_run_when_cloud_run_dispatch_fails() -> None:
    """Catches a dispatch failure leaving an active planned run or queued asset."""
    module = _load_dispatch_module()
    assert module is not None

    class RecordingCursor:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params):
            self.calls.append((" ".join(sql.split()), params))

    cur = RecordingCursor()
    module.terminalize_dispatch_failure(
        cur,
        run_id="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        error="permission denied",
    )

    assert cur.calls == [(
        "WITH failed_run AS ( UPDATE build_runs SET state='failed', ended_at=NOW(), last_error=%s WHERE id=%s AND state='planned' RETURNING id ) UPDATE build_run_assets SET state='aborted', ended_at=NOW(), error=%s WHERE run_id IN (SELECT id FROM failed_run) AND state='queued'",
        (
            "canary dispatch failed: permission denied",
            "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
            "canary dispatch failed: permission denied",
        ),
    )]
