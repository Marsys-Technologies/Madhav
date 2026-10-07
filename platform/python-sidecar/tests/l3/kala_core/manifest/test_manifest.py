"""K0a-3a candidate manifest oracles."""

from types import SimpleNamespace

import pytest

from services.kala_core.manifest import Candidate, attest_grain, candidate_generation, open_candidate


class Cursor:
    def __init__(self, row): self.row = row
    def fetchone(self): return self.row


class Conn:
    def __init__(self, rows=()): self.rows = iter(rows); self.calls = []
    def execute(self, query, params=()):
        self.calls.append((query, params)); return Cursor(next(self.rows, None))


def test_read_model_resolves_its_unpublished_candidate_not_a_served_head():
    conn = Conn([("published",), None, None, ("candidate",)])
    candidate = open_candidate(conn, chart_id="chart", generation="candidate", build_id="build",
                               model_digest="digest", rule_registry_version="rules", conventions={"aya": "lahiri"})
    assert candidate.generation == "candidate"
    assert candidate_generation(SimpleNamespace(config={"build_id": "build"}, db_conn=conn)) == "candidate"


def test_attestation_records_zero_rows_as_a_result():
    conn = Conn()
    candidate = Candidate("chart", "candidate", "build", None)
    attest_grain(conn, candidate, grain_key="read-model", result_state="zero_rows", input_vector="digest")
    assert conn.calls[-1][1][-2:] == ("zero_rows", "digest")


def test_candidate_generation_refuses_missing_build_binding():
    with pytest.raises(ValueError, match="build_id"):
        candidate_generation(SimpleNamespace(config={}, db_conn=Conn()))
