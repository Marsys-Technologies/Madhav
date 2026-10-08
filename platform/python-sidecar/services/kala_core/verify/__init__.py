"""Independent candidate verification, deliberately outside the writer path."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

from services.kala_core.manifest import Candidate

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


def verify_candidate(conn: Any, candidate: Candidate, *, independently_derived_digest: str,
                     derive: Callable[[Candidate], str]) -> None:
    """Persist one acceptance only as the separate local verifier principal."""
    principal = _value(conn.execute("SELECT current_user").fetchone())
    if principal != VERIFIER_PRINCIPAL:
        raise VerificationRefused("verification must run as verifier_principal")
    stored = candidate_input_digest(conn, candidate)
    if stored != independently_derived_digest or derive(candidate) != stored:
        raise VerificationRefused("independent digest does not match stored candidate input")
    conn.execute(
        "INSERT INTO kala_layer_verification "
        "(chart_id, generation, verifier_principal, result, detail) VALUES (%s, %s, %s, 'accepted', %s) "
        "ON CONFLICT (chart_id, generation) DO NOTHING",
        (candidate.chart_id, candidate.generation, VERIFIER_PRINCIPAL,
         {"input_digest": stored}),
    )
