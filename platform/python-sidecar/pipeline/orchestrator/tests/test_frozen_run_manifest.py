from __future__ import annotations

import pathlib
import sys
import uuid

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from pipeline.orchestrator.runner import (
    _canonical_manifest_digest,
    _terminalize_preflight_failure,
    _verify_registry_still_matches_manifest,
    validate_frozen_run_manifest,
)


def _run() -> dict:
    chart_id = "11111111-1111-4111-8111-111111111111"
    run = {
        "id": "run-1",
        "chart_id": chart_id,
        "scope": "layer",
        "scope_target": "ganita",
        "action": "rebuild",
        "plan": ["ga_positions", "ga_strength"],
        "plan_manifest": {
            "version": "nirmana-run-manifest/v1",
            "chart_id": chart_id,
            "scope": "layer",
            "scope_target": "ganita",
            "action": "rebuild",
            "waves": [["ga_positions"], ["ga_strength"]],
            "assets": [
                {"asset_id": "ga_positions", "scope": "per_chart", "depends_on": [], "natural_key_partition": "chart_id", "has_cowriters": False, "expected_code_digest": "7c19f23c5fa532ec0a111bb158f65ffa4339ab136c6897cb2cccda4f28918973"},
                {"asset_id": "ga_strength", "scope": "per_chart", "depends_on": ["ga_positions"], "natural_key_partition": "chart_id", "has_cowriters": True, "expected_code_digest": "4ed654f2e9c47eed089d2c95233be5b8c1e66fea72ed97ebdbcd0775c69c4d66"},
            ],
        },
        "plan_manifest_digest": "",
    }
    run["plan_manifest_digest"] = _canonical_manifest_digest(run["plan_manifest"])
    return run


def test_valid_manifest_restores_the_persisted_dag_not_the_live_registry():
    frozen = validate_frozen_run_manifest(_run())

    assert frozen.plan == ["ga_positions", "ga_strength"]
    assert frozen.asset_scopes == {"ga_positions": "per_chart", "ga_strength": "per_chart"}
    assert frozen.asset_deps == {"ga_positions": [], "ga_strength": ["ga_positions"]}
    assert frozen.asset_partitions == {"ga_positions": "chart_id", "ga_strength": "chart_id"}
    assert frozen.asset_has_cowriters == {"ga_positions": False, "ga_strength": True}
    assert frozen.expected_code_digests["ga_positions"].startswith("7c19f23c")


def test_valid_manifest_accepts_psycopg_uuid_chart_id():
    """Production returns UUID columns as uuid.UUID while JSONB stores strings."""
    run = _run()
    chart_id = str(uuid.uuid4())
    run["chart_id"] = uuid.UUID(chart_id)
    run["plan_manifest"]["chart_id"] = chart_id
    run["plan_manifest_digest"] = _canonical_manifest_digest(run["plan_manifest"])

    frozen = validate_frozen_run_manifest(run)

    assert frozen.plan == ["ga_positions", "ga_strength"]


def test_valid_manifest_canonicalizes_uppercase_json_uuid():
    run = _run()
    chart_id = uuid.uuid4()
    run["chart_id"] = chart_id
    run["plan_manifest"]["chart_id"] = str(chart_id).upper()
    run["plan_manifest_digest"] = _canonical_manifest_digest(run["plan_manifest"])

    frozen = validate_frozen_run_manifest(run)

    assert frozen.plan == ["ga_positions", "ga_strength"]


def test_preflight_failure_terminalizes_run_and_queued_assets_atomically():
    class Cursor:
        sql = ""
        params = ()

        def execute(self, sql, params):
            self.sql = " ".join(sql.split())
            self.params = params

    cur = Cursor()

    _terminalize_preflight_failure(cur, run_id="run-1", message="unsafe manifest")

    assert "WITH failed_run AS" in cur.sql
    assert "UPDATE build_runs" in cur.sql
    assert "state='failed'" in cur.sql
    assert "UPDATE build_run_assets" in cur.sql
    assert "state='aborted'" in cur.sql
    assert "state='queued'" in cur.sql
    assert cur.params == ("unsafe manifest", "run-1", "unsafe manifest")


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
                {"asset_id": "ga_positions", "scope": "per_chart", "depends_on": [], "natural_key_partition": "chart_id", "has_cowriters": False},
                # A later registry edit must not add an edge to an accepted run.
                {"asset_id": "ga_strength", "scope": "per_chart", "depends_on": ["ga_positions", "ga_extra"], "natural_key_partition": "chart_id", "has_cowriters": True},
            ]

    with pytest.raises(ValueError, match="changed after dispatch"):
        _verify_registry_still_matches_manifest(Cursor(), validate_frozen_run_manifest(_run()))


def test_registry_dependency_reorder_alone_does_not_fail_preflight():
    """Regression for #2137: asset_registry.depends_on is stored in authored order,
    but the frozen manifest's depends_on is stored sorted (matching the server's
    registryContractFingerprintInput). Same set, different order must not be
    treated as drift -- dependency order was never a real invariant."""
    run = _run()
    # ga_strength's manifest depends_on is ["ga_positions"] (single-element, so add
    # a second real dependency to make reordering observable).
    run["plan_manifest"]["assets"][1]["depends_on"] = ["ga_extra", "ga_positions"]
    run["plan_manifest_digest"] = _canonical_manifest_digest(run["plan_manifest"])

    class Cursor:
        def execute(self, _sql, _params):
            pass

        def fetchall(self):
            return [
                {"asset_id": "ga_positions", "scope": "per_chart", "depends_on": [], "natural_key_partition": "chart_id", "has_cowriters": False},
                # Live registry has the same two deps, authored (unsorted) order.
                {"asset_id": "ga_strength", "scope": "per_chart", "depends_on": ["ga_positions", "ga_extra"], "natural_key_partition": "chart_id", "has_cowriters": True},
            ]

    _verify_registry_still_matches_manifest(Cursor(), validate_frozen_run_manifest(run))
