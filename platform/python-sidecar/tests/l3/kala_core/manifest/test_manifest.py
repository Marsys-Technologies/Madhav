"""K0a-3a candidate manifest oracles."""

from types import SimpleNamespace

import pytest

from services.kala_core.manifest import (
    Candidate, CandidateNotPublishable, attest_grain, candidate_generation,
    lint_no_self_resolved_generation, open_candidate, publish_candidate,
)


class Cursor:
    def __init__(self, row): self.row = row
    def fetchone(self): return self.row
    def fetchall(self): return self.row


class Conn:
    def __init__(self, rows=()): self.rows = iter(rows); self.calls = []
    def execute(self, query, params=()):
        self.calls.append((query, params)); return Cursor(next(self.rows, None))


def test_read_model_resolves_its_unpublished_candidate_not_a_served_head():
    conn = Conn([None, ("published",), None, ("candidate",)])
    candidate = open_candidate(conn, chart_id="chart", generation="candidate", build_id="build",
                               model_digest="digest", rule_registry_version="rules", conventions={"aya": "lahiri"})
    assert candidate.generation == "candidate"
    assert candidate_generation(SimpleNamespace(build_id="build", config={}, db_conn=conn)) == "candidate"
    assert conn.calls[-1][1] == ("build",)


def test_candidate_open_serializes_conventions_for_postgres_jsonb():
    conn = Conn([None, None, None])
    open_candidate(conn, chart_id="chart", generation="candidate", build_id="build",
                   model_digest="digest", rule_registry_version="rules", conventions={"aya": "lahiri"})
    _, params = conn.calls[-1]
    assert params[-1] == '{"aya":"lahiri"}'


def test_attestation_records_zero_rows_as_a_result():
    conn = Conn()
    candidate = Candidate("chart", "candidate", "build", None)
    attest_grain(conn, candidate, grain_key="read-model", result_state="zero_rows", input_vector="digest")
    assert conn.calls[-1][1][-2:] == ("zero_rows", "digest")


def test_candidate_generation_refuses_missing_build_binding():
    with pytest.raises(ValueError, match="build_id"):
        candidate_generation(SimpleNamespace(build_id="", config={"build_id": "wrong-place"}, db_conn=Conn()))


def test_reopening_a_candidate_keeps_its_original_published_head_pin():
    """A retry must not silently bind an existing candidate to a newer head."""
    conn = Conn([("chart", "candidate", "older-published", "digest", "rules", {"aya": "lahiri"})])
    candidate = open_candidate(
        conn,
        chart_id="chart",
        generation="candidate",
        build_id="build",
        model_digest="digest",
        rule_registry_version="rules",
        conventions={"aya": "lahiri"},
    )
    assert candidate.expected_head_generation == "older-published"
    assert not any(query.startswith("INSERT INTO kala_layer_candidate") for query, _ in conn.calls)


@pytest.mark.parametrize(
    ("changed", "value"),
    (("chart_id", "other-chart"), ("model_digest", "other-digest"),
     ("rule_registry_version", "other-rules"), ("conventions", {"aya": "raman"})),
)
def test_reopening_candidate_refuses_changed_identity_or_pins(changed, value):
    values = {
        "chart_id": "chart", "generation": "candidate", "model_digest": "digest",
        "rule_registry_version": "rules", "conventions": {"aya": "lahiri"},
    }
    values[changed] = value
    conn = Conn([("chart", "candidate", "published", "digest", "rules", {"aya": "lahiri"})])
    with pytest.raises(ValueError, match="already bound"):
        open_candidate(conn, build_id="build", **values)


class PublishConn:
    def __init__(self, grain_rows, verification):
        self.grain_rows = grain_rows
        self.verification = verification
        self.calls = []

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if "candidate_grain" in query:
            return Cursor(self.grain_rows)
        if "layer_verification" in query:
            return Cursor(self.verification)
        if query.startswith("UPDATE kala_layer_head"):
            return Cursor(("candidate",))
        return Cursor(None)


def test_publish_refuses_missing_or_failed_grains_before_head_mutation():
    candidate = Candidate("chart", "candidate", "build", "published")
    conn = PublishConn([("writer", "rows"), ("reader", "failed")], ("accepted",))
    with pytest.raises(CandidateNotPublishable, match="reader"):
        publish_candidate(conn, candidate, expected_grains=("writer", "reader", "service"))
    assert not any("kala_layer_head" in query for query, _ in conn.calls)


def test_reader_current_lint_rejects_a_planted_bypass(tmp_path):
    reader = tmp_path / "reader.py"
    reader.write_text("generation = 'current'\n")
    with pytest.raises(ValueError, match="resolves current"):
        lint_no_self_resolved_generation([reader])
