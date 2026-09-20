"""Contract checks for the unapplied Pūrṇa wealth output-digest revision."""
from __future__ import annotations

import json
import re
from pathlib import Path

from pipeline.orchestrator.output_digest import _validate_spec


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations/1042_nirmana_purna_wealth_ga_strength_ashtakavarga_digest_spec.sql"
OLD_SHA = "7251b1192714e6e1b09720fff165f78f6089bc74dca862dfaab0f7537ee677c3"
NEW_SHA = "3743484c996bf41a9b957224fd5c54cf04f1f1de27ef91116726b60b483bb07a"


def _new_spec() -> tuple[str, dict]:
    sql = MIGRATION.read_text()
    match = re.search(
        r"VALUES\s*\(\s*'ga_strength'\s*,\s*'([a-f0-9]{64})'\s*,\s*'(\{.*?\})'::jsonb\s*\)",
        sql,
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group(1), json.loads(match.group(2))


def test_migration_1042_has_no_inner_transaction_and_fails_closed_on_unknown_active_spec() -> None:
    sql = MIGRATION.read_text()
    assert "\nBEGIN;" not in sql
    assert "\nCOMMIT;" not in sql
    assert "DO $$" in sql
    assert "spec_sha256 NOT IN" in sql
    assert OLD_SHA in sql
    assert NEW_SHA in sql
    assert "RAISE EXCEPTION" in sql
    assert "ON CONFLICT (asset_id, spec_sha256) DO NOTHING" in sql


def test_migration_1042_new_spec_passes_real_validator_with_exact_ashtakavarga_categories() -> None:
    spec_sha, spec = _new_spec()
    validated = _validate_spec("ga_strength", spec, spec_sha)
    assert validated.spec_sha256 == NEW_SHA
    component = spec["components"][0]
    assert component["where_in"]["fact_category"] == [
        "ashtakavarga_bindu_per_varga",
        "ashtakavarga_pinda_sarva_per_varga",
        "graha_shadbala_total",
    ]
