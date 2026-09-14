"""Contract checks for unapplied Purna Anvesana migration 1034."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pipeline.orchestrator.output_digest import _validate_spec


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations/1034_nirmana_purna_anvesana_wave1_output_digest_specs.sql"


def _specs() -> dict[str, tuple[str, dict]]:
    sql = MIGRATION.read_text()
    matches = re.findall(
        r"VALUES\s*\(\s*'([^']+)'\s*,\s*'([a-f0-9]{64})'\s*,\s*'(\{.*?\})'::jsonb\s*\)",
        sql,
        flags=re.DOTALL,
    )
    return {asset_id: (sha, json.loads(raw)) for asset_id, sha, raw in matches}


def test_migration_1034_has_exact_reviewed_asset_set_and_no_inner_transaction() -> None:
    sql = MIGRATION.read_text()
    assert "\nBEGIN;" not in sql
    assert "\nCOMMIT;" not in sql
    assert sorted(_specs()) == [
        "bg_gochara_citation_resolution",
        "bg_nakshatra_medical",
        "bg_sign_medical",
        "bg_transit_engine",
        "ka_avadhi",
        "ka_kalasutra",
    ]
    assert "ka_vighnakara" in sql and "ka_gochara_v3_century_materialize" in sql


def test_migration_1034_specs_pass_the_real_validator() -> None:
    for asset_id, (spec_sha, spec) in _specs().items():
        validated = _validate_spec(asset_id, spec, spec_sha)
        assert validated.asset_id == asset_id
        assert validated.spec_sha256 == spec_sha
