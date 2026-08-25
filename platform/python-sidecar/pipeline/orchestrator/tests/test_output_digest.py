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
    def __init__(self, row=None, batches=()):
        self.row = row
        self.batches = list(batches)
        self.executed = []

    def execute(self, statement, params=None):
        self.executed.append((statement, params))

    def fetchone(self):
        return self.row

    def fetchmany(self, size):
        return self.batches.pop(0) if self.batches else []


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


def test_component_statement_materializes_aliases_before_collated_ordering():
    statement = _component_statement(SPEC["components"][0])
    assert "FROM (SELECT" in statement
    assert 'AS "__key_0"' in statement
    assert "AS digest_source" in statement
    assert 'digest_source.row_json COLLATE "C"' in statement
    assert 'to_jsonb(source."rule_id")::text COLLATE "C"' in statement


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
