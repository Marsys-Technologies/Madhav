"""J-7b: executable field contract, not evidence of a production flip/readback.

The document's storage declaration is checked against PostgreSQL after applying
the existing guarded fixture's real migrations. No sky, seal or chart result is
fabricated. The post-flip J-7b-b62 receipt remains a separate campaign operation.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path
import re

import psycopg
from psycopg import sql
import pytest
import yaml

from services.gochara_kernel import serving_reader
from .test_a53_inventory import create_am5_database, drop_am5_database

ROOT = Path(__file__).resolve().parents[5]
DOCUMENT = ROOT / "00_ARCHITECTURE/briefs/pravaha/L5_HANDOFF_5_0_v1_0.md"
SUITE = "tests/l3/gochara/test_j7b_l5_handoff.py"


def declaration():
    assert DOCUMENT.is_file(), "J-7b requires the versioned L5 hand-off"
    blocks = re.findall(r"```json\n(.*?)\n```", DOCUMENT.read_text(), re.S)
    assert len(blocks) == 1, "one machine-readable storage contract is required"
    return json.loads(blocks[0])


def test_handoff_is_prebuild_with_post_flip_acceptance_still_pending():
    contract = declaration()
    assert contract["schema"] == "gochara_l5_handoff/1"
    assert contract["status"] == "PREBUILD"
    assert contract["chart_id"] == "482012f1-710e-4a25-994a-93821f5871aa"
    assert contract["generation"] == "5.0"
    assert contract["sealed_generation_readback"] is None
    assert set(contract["activation_gates"]) == {"J-6l", "J-7b-b62:sealed_field_readback"}
    assert contract["probability_target"] is None
    assert contract["forecast_delivery"] == "separate_issued_forecast_lifecycle"


def test_document_names_the_existing_reader_and_every_required_backing_table():
    contract = declaration()
    assert contract["reader"] == "services.gochara_kernel.serving_reader.read_v5"
    assert contract["envelope_schema"] == serving_reader.ENVELOPE_SCHEMA
    assert {"conn", "chart_id", "generation", "event_classes", "date_from", "date_to",
            "at_instant", "limit"} == set(inspect.signature(serving_reader.read_v5).parameters)
    assert set(serving_reader.REQUIRED_TABLES) <= set(contract["storage"])
    # These are essential to calibration lineage beyond the served envelope.
    assert {"ka_gochara_seal_approval", "ka_gochara_search_input_snapshot",
            "ka_gochara_search_path_pin", "ka_gochara_factor",
            "ka_gochara_rule_path_soft_factor", "ka_gochara_rule_path_seal"} <= set(contract["storage"])


@pytest.fixture(scope="module")
def schema_db():
    admin, name, dsn = create_am5_database("j7b")
    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            yield conn
    finally:
        drop_am5_database(admin, name)


def test_every_declared_field_exists_in_the_real_migration_schema(schema_db):
    storage = declaration()["storage"]
    assert storage
    with schema_db.transaction():
        schema_db.execute("SET TRANSACTION READ ONLY")
        for table, columns in storage.items():
            assert columns and len(columns) == len(set(columns)), table
            # PostgreSQL, not a handwritten schema regex, resolves each field.
            query = sql.SQL("SELECT {} FROM public.{} LIMIT 0").format(
                sql.SQL(", ").join(map(sql.Identifier, columns)), sql.Identifier(table))
            result = schema_db.execute(query)
            assert [column.name for column in result.description] == columns


def test_documented_identity_readback_is_executable_and_empty_is_not_acceptance(schema_db):
    declaration()  # fail clearly if the contract itself is absent
    queries = re.findall(r"```sql\n(.*?)\n```", DOCUMENT.read_text(), re.S)
    assert len(queries) == 1, "one read-only identity/readback query is required"
    with schema_db.transaction():
        schema_db.execute("SET TRANSACTION READ ONLY")
        result = schema_db.execute(queries[0])
        assert {"chart_id", "generation", "manifest_id", "seal_manifest_id", "approval_manifest_id",
                "brief_digest", "input_generation_vector", "horizon", "status"} <= {
                    c.name for c in result.description}
        assert result.fetchall() == [], "this fixture does not manufacture a sealed generation"


def test_handoff_source_citations_resolve_to_real_lines():
    declaration()
    citations = re.findall(r"`((?:platform|00_ARCHITECTURE)/[^`\n]+):(\d+)`", DOCUMENT.read_text())
    assert len(citations) >= 8
    for path, line in citations:
        source = ROOT / path
        assert source.is_file(), path
        assert 0 < int(line) <= len(source.read_text().splitlines()), (path, line)


def test_field_readback_is_in_the_existing_mandatory_database_ci_command():
    from ci_discovery import expanded_workflow
    jobs = expanded_workflow(yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())["jobs"])
    job = jobs["db-integration-tests"]
    steps = [step for step in job["steps"] if SUITE in step.get("run", "")]
    assert len(steps) == 1, "J-7b field readback must run in mandatory DB CI"
    assert not job.get("continue-on-error") and not steps[0].get("continue-on-error")
    assert steps[0].get("env", {}).get("GOCHARA_A53_REQUIRE_DB") == "1"
    assert "pytest" in steps[0]["run"] and "-p no:cacheprovider" in steps[0]["run"]

import sys as _ci_sys
_ci_sys.path.insert(0, str(ROOT / "platform/scripts/governance"))
