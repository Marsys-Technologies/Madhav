"""K0a-3c verification-harness oracles."""

import hashlib
import inspect
import json

import pytest

from services.kala_core.manifest import Candidate
from services.kala_core.verify import VerificationRefused, verify_candidate
from services.kala_core.verify import job


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
        if query.startswith("INSERT INTO kala_layer_verification"): return Cursor((params[0],))
        return Cursor(None)


def _digest(vector):
    return hashlib.sha256(json.dumps([("grain", vector)], separators=(",", ":")).encode()).hexdigest()


def test_builder_principal_cannot_write_a_verification_row():
    conn = Conn(principal="data_plane_builder")
    candidate = Candidate("chart", "candidate", "build", None)
    with pytest.raises(VerificationRefused, match="verifier_principal"):
        verify_candidate(conn, candidate, independently_derived_digest=_digest("stored"))
    assert not any("INSERT INTO kala_layer_verification" in query for query, _ in conn.calls)


def test_mutated_stored_input_refuses_independent_digest():
    conn = Conn(vector="mutated")
    candidate = Candidate("chart", "candidate", "build", None)
    with pytest.raises(VerificationRefused, match="digest"):
        verify_candidate(conn, candidate, independently_derived_digest=_digest("stored"))


def test_dispatch_requires_an_independently_supplied_digest():
    source = inspect.getsource(job.main)
    assert "--independently-derived-digest" in source
    assert "candidate_input_digest" not in source


@pytest.mark.parametrize("retry_vector", ["A", "B"])
def test_existing_receipt_is_refused_for_identical_or_changed_inputs(retry_vector):
    class ReceiptConn(Conn):
        receipt = None

        def execute(self, query, params=()):
            if query.startswith("INSERT INTO kala_layer_verification"):
                self.calls.append((query, params))
                if self.receipt is not None:
                    return Cursor(None)
                self.receipt = json.loads(params[-1])
                return Cursor((params[0],))
            return super().execute(query, params)

    conn = ReceiptConn(vector="A")
    candidate = Candidate("chart", "candidate", "build", None)
    verify_candidate(conn, candidate, independently_derived_digest=_digest("A"))
    assert conn.receipt == {"input_digest": _digest("A")}
    conn.vector = retry_vector
    with pytest.raises(VerificationRefused, match="receipt"):
        verify_candidate(conn, candidate, independently_derived_digest=_digest(retry_vector))
    assert conn.receipt == {"input_digest": _digest("A")}


def test_verification_locks_inputs_before_reading_or_inserting_receipt():
    class LockedConn(Conn):
        locked = False

        def execute(self, query, params=()):
            if "pg_advisory_xact_lock" in query:
                self.locked = True
            if "candidate_grain" in query or query.startswith("INSERT INTO kala_layer_verification"):
                assert self.locked, "verification read mutable evidence without the lifecycle lock"
            return super().execute(query, params)

    verify_candidate(LockedConn(), Candidate("chart", "candidate", "build", None),
                     independently_derived_digest=_digest("stored"))


def test_verifier_entry_point_propagates_receipt_conflict(monkeypatch):
    class ExistingReceiptConn(Conn):
        def __enter__(self): return self
        def __exit__(self, *exc): return False

        def execute(self, query, params=()):
            if query.startswith("INSERT INTO kala_layer_verification"):
                return Cursor(None)
            return super().execute(query, params)

    monkeypatch.setenv("KALA_VERIFIER_DSN", "fixture-only-no-connection")
    monkeypatch.setattr(job.psycopg, "connect", lambda dsn: ExistingReceiptConn())
    monkeypatch.setattr("sys.argv", ["verify", "--chart-id", "chart", "--generation", "candidate",
                                   "--build-id", "build", "--independently-derived-digest", _digest("stored")])
    with pytest.raises(VerificationRefused, match="immutable receipt"):
        job.main()
