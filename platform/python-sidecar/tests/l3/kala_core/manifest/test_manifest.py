"""K0a-3a candidate manifest oracles."""

from types import SimpleNamespace
from uuid import UUID

import pytest

from services.kala_core.manifest import (
    Candidate, CandidateNotPublishable, attest_grain, candidate_generation,
    lint_no_self_resolved_generation, open_candidate, publish_candidate, rollback_head,
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


def test_candidate_generation_cannot_substitute_the_served_head_for_its_build_candidate():
    class CandidateOnlyConn:
        def execute(self, query, params=()):
            assert "FROM kala_layer_candidate" in query
            assert params == ("build",)
            return Cursor(("unpublished-candidate",))

    generation = candidate_generation(
        SimpleNamespace(build_id="build", db_conn=CandidateOnlyConn())
    )
    assert generation == "unpublished-candidate"


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


def test_reopening_a_candidate_accepts_the_same_postgres_uuid_chart_id():
    """Changing the stored UUID representation must not break an idempotent retry."""
    chart_id = "019c6e27-e55b-73d1-87d8-4e01f1f75043"
    conn = Conn([(UUID(chart_id), "candidate", "older-published", "digest", "rules", {"aya": "lahiri"})])

    candidate = open_candidate(
        conn,
        chart_id=chart_id,
        generation="candidate",
        build_id="build",
        model_digest="digest",
        rule_registry_version="rules",
        conventions={"aya": "lahiri"},
    )

    assert candidate.chart_id == chart_id
    assert candidate.expected_head_generation == "older-published"


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
            if "verifier_principal" not in query or "detail" not in query:
                return Cursor(("accepted",))
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


@pytest.mark.parametrize(
    "verification",
    [
        ("verifier_principal", "accepted", '{"input_digest":"stale"}'),
        ("data_plane_builder", "accepted", '{"input_digest":"digest"}'),
    ],
)
def test_publish_requires_a_verifier_receipt_for_the_current_grain_inputs(verification):
    candidate = Candidate("chart", "candidate", "build", "published")
    conn = PublishConn([("writer", "rows", "digest")], verification)

    with pytest.raises(CandidateNotPublishable, match="verification"):
        publish_candidate(conn, candidate, expected_grains=("writer",))

    assert not any("kala_layer_head" in query for query, _ in conn.calls)


class RollbackConn:
    def __init__(self, state):
        self.state = state
        self.calls = []

    def execute(self, query, params=()):
        self.calls.append((query, params))
        if "kala_layer_candidate" in query:
            if "state = 'published'" not in query:
                return Cursor((1,))
            return Cursor((self.state,)) if self.state == "published" else Cursor(None)
        if query.startswith("UPDATE kala_layer_head"):
            return Cursor(("retained",))
        return Cursor(None)


def test_rollback_refuses_a_building_candidate_and_restores_only_a_retained_head():
    building = RollbackConn("building")
    with pytest.raises(CandidateNotPublishable, match="retained"):
        rollback_head(
            building,
            chart_id="chart",
            retained_generation="building",
            expected_head_generation="published",
        )
    assert not any("kala_layer_head" in query for query, _ in building.calls)

    retained = RollbackConn("published")
    rollback_head(
        retained,
        chart_id="chart",
        retained_generation="retained",
        expected_head_generation="published",
    )
    assert any("kala_layer_head" in query for query, _ in retained.calls)


def test_reader_current_lint_rejects_a_planted_bypass(tmp_path):
    reader = tmp_path / "reader.py"
    reader.write_text("generation = 'current'\n")
    with pytest.raises(ValueError, match="resolves current"):
        lint_no_self_resolved_generation([reader])
