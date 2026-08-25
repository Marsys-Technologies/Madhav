"""Content-digest specs must be deterministic, bounded, and fail closed."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from pipeline.orchestrator.output_digest import (
    compute_output_digest,
    load_output_digest_spec,
)


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
