"""Content-digest specs must be deterministic, bounded, and fail closed."""
from __future__ import annotations

import pathlib
import json
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from pipeline.orchestrator.output_digest import (
    _component_statement,
    compute_output_digest,
    load_output_digest_spec,
)
from pipeline.orchestrator.provenance import canonical_digest


class _Cursor:
    def __init__(self, row=None, batches=(), null_key=False):
        self.row = row
        self.batches = list(batches)
        self.null_key = null_key
        self.executed = []
        self._next_row = row

    def execute(self, statement, params=None):
        self.executed.append((statement, params))
        self._next_row = ({"invalid_key": 1} if self.null_key else None) \
            if "SELECT 1 AS invalid_key" in statement else self.row

    def fetchone(self):
        return self._next_row

    def fetchmany(self, size):
        return self.batches.pop(0) if self.batches else []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class _Connection:
    def __init__(self, stream_cursor):
        self.stream_cursor = stream_cursor
        self.cursor_calls = []

    def cursor(self, **kwargs):
        self.cursor_calls.append(kwargs)
        return self.stream_cursor


SPEC = {
    "version": "nirmana-output-digest-spec-v1",
    "components": [{
        "name": "rules",
        "relation": "bg_rules",
        "key_columns": ["rule_id"],
        "value_columns": ["rule_id", "rule_text"],
    }],
}


def test_missing_spec_is_explicitly_unproven_without_querying_output_rows():
    cursor = _Cursor(row=None)
    assert compute_output_digest(cursor, asset_id="bg_unknown") == (None, None)
    assert len(cursor.executed) == 1


def test_digest_streams_ordered_canonical_rows_and_never_fetches_all():
    cursor = _Cursor(
        row={"spec": SPEC, "spec_sha256": load_output_digest_spec.__module__ and ""},
        batches=[[{"row_json": '{"rule_id":"a","rule_text":"first"}'}], [{"row_json": '{"rule_id":"b","rule_text":"second"}'}]],
    )
    # The persisted SHA is checked against canonical spec content, rather than trusted.
    from pipeline.orchestrator.provenance import canonical_digest
    cursor.row["spec_sha256"] = canonical_digest(SPEC)

    first = compute_output_digest(cursor, asset_id="bg_rules")
    assert first[0] is not None
    assert first[1] == canonical_digest(SPEC)
    assert "ORDER BY" in cursor.executed[-1][0]
    assert "public" in cursor.executed[-1][0]


def test_component_statement_orders_by_reviewed_natural_keys_without_a_json_sort():
    statement = _component_statement(SPEC["components"][0])
    assert 'ORDER BY source."rule_id"' in statement
    assert 'to_jsonb(source."rule_id")' not in statement
    assert "row_json COLLATE" not in statement


def test_digest_uses_a_named_server_cursor_instead_of_client_buffering():
    stream = _Cursor(
        batches=[[{"row_json": '{"rule_id":"a","rule_text":"first"}'}]],
    )
    spec_cursor = _Cursor(row={"spec": SPEC, "spec_sha256": canonical_digest(SPEC)})
    spec_cursor.connection = _Connection(stream)

    digest, spec_sha = compute_output_digest(spec_cursor, asset_id="bg_rules")

    assert digest is not None
    assert spec_sha == canonical_digest(SPEC)
    assert len(spec_cursor.executed) == 2  # spec lookup + key-null preflight
    assert len(stream.executed) == 1
    assert spec_cursor.connection.cursor_calls[0]["name"].startswith("nirmana_digest_")
    assert spec_cursor.connection.cursor_calls[0]["row_factory"] is not None


def test_digest_fails_closed_before_scanning_rows_when_a_reviewed_key_is_null():
    cursor = _Cursor(
        row={"spec": SPEC, "spec_sha256": canonical_digest(SPEC)},
        null_key=True,
    )
    try:
        compute_output_digest(cursor, asset_id="bg_rules")
    except ValueError as exc:
        assert "NULL" in str(exc)
    else:
        raise AssertionError("NULL digest key was accepted")
    assert len(cursor.executed) == 2


def test_invalid_spec_identifier_fails_closed_before_querying_a_relation():
    from pipeline.orchestrator.provenance import canonical_digest
    invalid = {"version": "nirmana-output-digest-spec-v1", "components": [{
        "name": "rules", "relation": "bg_rules; DROP TABLE asset_registry", "key_columns": ["rule_id"], "value_columns": ["rule_id"],
    }]}
    cursor = _Cursor(row={"spec": invalid, "spec_sha256": canonical_digest(invalid)})
    try:
        load_output_digest_spec(cursor, "bg_rules")
    except ValueError as exc:
        assert "identifier" in str(exc)
    else:  # pragma: no cover - assertion reads more clearly than pytest.raises here
        raise AssertionError("invalid digest spec was accepted")
    assert len(cursor.executed) == 1


def _ghatana_spec():
    migration = pathlib.Path(__file__).resolve().parents[4] / "supabase/migrations/598_nirmana_output_digest_specs.sql"
    match = re.search(r"'bg_ghatana',\s*'([a-f0-9]{64})',\s*'({.+?})'::jsonb", migration.read_text(), re.DOTALL)
    assert match, "migration 598 must seed a reviewed bg_ghatana digest spec"
    spec = json.loads(match.group(2))
    assert canonical_digest(spec) == match.group(1)
    return spec


def test_ghatana_spec_hashes_every_serving_semantic_event_shape_column():
    spec = _ghatana_spec()
    event_component = next(component for component in spec["components"] if component["name"] == "event_ontology")
    required = {
        "temporal_shape", "duration_prior", "milestone_template", "irreversibility_milestone",
        "evidence_requirements", "self_report_non_discriminating", "kill_switch_criteria",
    }
    assert required <= set(event_component["value_columns"])
    statement = _component_statement(event_component)
    assert all(f'"{column}"' in statement for column in required)


def test_ghatana_digest_changes_when_a_serving_semantic_event_shape_value_changes():
    spec = _ghatana_spec()
    sha = canonical_digest(spec)
    point = '{"event_class_id":"career_entry","temporal_shape":"point","duration_prior":null}'
    interval = '{"event_class_id":"career_entry","temporal_shape":"interval","duration_prior":{"min_days":1}}'
    left = _Cursor(row={"spec": spec, "spec_sha256": sha}, batches=[[{"row_json": point}], [], [], []])
    right = _Cursor(row={"spec": spec, "spec_sha256": sha}, batches=[[{"row_json": interval}], [], [], []])
    assert compute_output_digest(left, asset_id="bg_ghatana")[0] != compute_output_digest(right, asset_id="bg_ghatana")[0]


def _migration_specs(path: pathlib.Path):
    matches = re.findall(
        r"\(\s*'([^']+)',\s*'([a-f0-9]{64})',\s*'({.+?})'::jsonb\s*\)",
        path.read_text(),
        re.DOTALL,
    )
    return {asset_id: (spec_sha, json.loads(raw_spec)) for asset_id, spec_sha, raw_spec in matches}


def test_every_frozen_l0_wave0_build_has_a_reviewed_canonical_digest_spec():
    platform_root = pathlib.Path(__file__).resolve().parents[4]
    repo_root = platform_root.parent
    seeded = {}
    for filename in (
        "598_nirmana_output_digest_specs.sql",
        "600_nirmana_l0_wave0_output_digest_specs.sql",
    ):
        seeded.update(_migration_specs(platform_root / "supabase/migrations" / filename))

    manifest = json.loads(
        (repo_root / "00_ARCHITECTURE/control/NIRMANA_T0_MANIFEST_v1_0.json").read_text()
    )
    wave0_builds = {
        asset["asset_id"]
        for asset in manifest["assets"]
        if asset["layer"] == "L0"
        and asset["wave_index"] == 0
        and asset["execution_obligation"] == "build"
    }
    assert wave0_builds <= set(seeded)

    execution_only = {"build_id", "created_at", "computed_at", "ingested_at", "updated_at"}
    for asset_id in wave0_builds:
        spec_sha, spec = seeded[asset_id]
        assert canonical_digest(spec) == spec_sha
        assert spec["components"]
        for component in spec["components"]:
            assert set(component["key_columns"]) <= set(component["value_columns"])
            assert execution_only.isdisjoint(component["value_columns"])
            _component_statement(component)


def test_migration_600_closes_exactly_the_previously_unspecced_wave0_gap():
    platform_root = pathlib.Path(__file__).resolve().parents[4]
    specs_598 = _migration_specs(
        platform_root / "supabase/migrations/598_nirmana_output_digest_specs.sql"
    )
    specs_600 = _migration_specs(
        platform_root / "supabase/migrations/600_nirmana_l0_wave0_output_digest_specs.sql"
    )
    assert len(specs_600) == 20
    assert not (set(specs_598) & set(specs_600))
    assert {"bg_reference", "bg_transit_rules", "bg_medical_mappings"} <= set(specs_600)

    reference_relations = {
        component["relation"]
        for component in specs_600["bg_reference"][1]["components"]
    }
    assert "reference_nakshatras" in reference_relations
    assert len(reference_relations) == 12

    transit_relations = {
        component["relation"]
        for component in specs_600["bg_transit_rules"][1]["components"]
    }
    assert transit_relations == {"bg_transit_rules", "bg_transit_engine", "bg_transit_moorti"}
