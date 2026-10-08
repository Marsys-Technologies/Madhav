"""K0a-3c verification-harness oracles."""

import hashlib
import json

import pytest

from services.kala_core.manifest import Candidate
from services.kala_core.verify import VerificationRefused, verify_candidate


class Cursor:
    def __init__(self, value): self.value = value
    def fetchone(self): return self.value
    def fetchall(self): return self.value


class Conn:
    def __init__(self, principal="verifier_principal", vector="stored"):
        self.principal, self.vector, self.calls = principal, vector, []
    def execute(self, query, params=()):
        self.calls.append((query, params))
        if query == "SELECT current_user": return Cursor((self.principal,))
        if "candidate_grain" in query: return Cursor([("grain", self.vector)])
        return Cursor(None)


def _digest(vector):
    return hashlib.sha256(json.dumps([("grain", vector)], separators=(",", ":")).encode()).hexdigest()


def test_builder_principal_cannot_write_a_verification_row():
    conn = Conn(principal="data_plane_builder")
    candidate = Candidate("chart", "candidate", "build", None)
    with pytest.raises(VerificationRefused, match="verifier_principal"):
        verify_candidate(conn, candidate, independently_derived_digest=_digest("stored"),
                         derive=lambda _: _digest("stored"))
    assert not any("INSERT INTO kala_layer_verification" in query for query, _ in conn.calls)


def test_mutated_stored_input_refuses_independent_digest():
    conn = Conn(vector="mutated")
    candidate = Candidate("chart", "candidate", "build", None)
    with pytest.raises(VerificationRefused, match="digest"):
        verify_candidate(conn, candidate, independently_derived_digest=_digest("stored"),
                         derive=lambda _: _digest("stored"))
