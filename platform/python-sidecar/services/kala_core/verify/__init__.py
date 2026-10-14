"""Independent candidate verification, deliberately outside the writer path."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from services.kala_core.manifest import Candidate, lock_candidate_inputs

VERIFIER_PRINCIPAL = "verifier_principal"


class VerificationRefused(ValueError):
    """The verifier cannot attest this candidate without violating separation."""


def _value(row: Any) -> Any:
    return next(iter(row.values())) if isinstance(row, dict) else row[0]


def candidate_input_digest(conn: Any, candidate: Candidate) -> str:
    """Digest the stored per-grain inputs in a stable independent form."""
    rows = conn.execute(
        "SELECT grain_key, input_vector FROM kala_layer_candidate_grain "
        "WHERE chart_id = %s AND generation = %s ORDER BY grain_key",
        (candidate.chart_id, candidate.generation),
    ).fetchall()
    encoded = [(row[0], row[1]) for row in rows]
    return hashlib.sha256(json.dumps(encoded, separators=(",", ":")).encode()).hexdigest()


def verify_candidate(conn: Any, candidate: Candidate, *, independently_derived_digest: str) -> None:
    """Append one acceptance as the separate verifier; refuse an existing receipt.

    Receipts are immutable. Even an identical retry is explicitly refused;
    changed inputs require a new candidate generation, never a silent success
    that leaves an older receipt in place. RETURNING uses only the conflict-key
    read privilege already granted to the verifier by migration 1334.
    """
    principal = _value(conn.execute("SELECT current_user").fetchone())
    if principal != VERIFIER_PRINCIPAL:
        raise VerificationRefused("verification must run as verifier_principal")
    lock_candidate_inputs(conn, candidate)
    stored = candidate_input_digest(conn, candidate)
    if stored != independently_derived_digest:
        raise VerificationRefused("independent digest does not match stored candidate input")
    inserted = conn.execute(
        "INSERT INTO kala_layer_verification "
        "(chart_id, generation, verifier_principal, result, detail) VALUES (%s, %s, %s, 'accepted', %s) "
        "ON CONFLICT (chart_id, generation) DO NOTHING RETURNING chart_id",
        (candidate.chart_id, candidate.generation, VERIFIER_PRINCIPAL,
         json.dumps({"input_digest": stored}, sort_keys=True)),
    ).fetchone()
    if inserted is None:
        raise VerificationRefused("candidate already has an immutable receipt; use a new generation")
