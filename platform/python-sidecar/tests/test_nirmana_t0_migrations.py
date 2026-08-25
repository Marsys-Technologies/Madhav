"""T0 guards for production-applied migration recovery and forward repairs."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


PLATFORM_ROOT = Path(__file__).resolve().parents[2]


def test_recovered_applied_migrations_are_byte_exact():
    expected = {
        "588_remove_asset_build_protection.sql": "a626570346237ed7b3cc609f986e333c615c83f89a7de082d3de46f88b39040c",
        "589_drop_orphaned_protection_functions.sql": "80ba7c0e5976411f188ca6b6469fb33e1ad15cf49dda063b6b309195b07f0e43",
        "590_nirmana_m0_catalogue_contract_columns.sql": "813267f75e845c071a2025eb88e1d23aa4192263977267ad5a8b27da21ee2c4b",
        "591_nirmana_m0_partition_and_dead_flag_columns.sql": "666c0062f2c133ab09d52b2af1e2a87715aa62e5c16ea78ec793b21f7bf578bf",
    }
    for filename, digest in expected.items():
        payload = (PLATFORM_ROOT / "migrations" / filename).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == digest


def test_retired_sweep_disposition_is_forward_only_metadata():
    sql = (PLATFORM_ROOT / "migrations" / "593_nirmana_t0_retired_gochara_disposition.sql").read_text()
    assert "superseded_by = 'ka_gochara'" in sql
    assert "data_disposition = 'RETAINED_AS_CAPITAL'" in sql
    assert "DELETE FROM kala_gochara_windows" not in sql
    assert "UPDATE kala_gochara_windows" not in sql


def test_sky_calendar_contract_repair_targets_the_existing_relation():
    sql = (PLATFORM_ROOT / "migrations" / "594_nirmana_t0_sky_calendar_contract.sql").read_text()
    assert "target_table = 'bg_sky_calendar'" in sql
    assert "count_sql = 'SELECT COUNT(*) FROM bg_sky_calendar'" in sql
    assert "to_regclass('public.bg_sky_calendar')" in sql
    assert "ALTER TABLE" not in sql


def test_manifest_producer_coverage_matches_multi_registered_writer_classes():
    manifest = json.loads(
        (PLATFORM_ROOT.parent / "00_ARCHITECTURE" / "control" / "NIRMANA_T0_MANIFEST_v1_0.json").read_text()
    )
    declared = {
        asset["asset_id"]: asset["producer_id"]
        for asset in manifest["assets"]
        if asset["execution_obligation"] == "producer_covered"
    }

    discovered: dict[str, str] = {}
    writer_root = PLATFORM_ROOT / "python-sidecar" / "pipeline" / "orchestrator" / "writers"
    for path in writer_root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            registrations = [
                decorator.args[0].value
                for decorator in node.decorator_list
                if isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "register"
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
            ]
            if len(registrations) < 2:
                continue
            primary = next(
                (
                    statement.value.value
                    for statement in node.body
                    if isinstance(statement, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == "asset_id" for target in statement.targets)
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)
                ),
                None,
            )
            assert primary in registrations
            for registration in registrations:
                if registration != primary:
                    discovered[registration] = primary

    assert declared == discovered
