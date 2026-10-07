"""Candidate-bound Kāla layer manifest; serving must resolve only a published head."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Candidate:
    chart_id: str
    generation: str
    build_id: str
    expected_head_generation: str | None


def open_candidate(
    conn: Any, *, chart_id: str, generation: str, build_id: str,
    model_digest: str, rule_registry_version: str, conventions: Mapping[str, Any],
) -> Candidate:
    """Open the one candidate bound to a build; never changes a published head."""
    if not all((chart_id, generation, build_id, model_digest, rule_registry_version)):
        raise ValueError("candidate identity and pinned inputs are required")
    if not conventions:
        raise ValueError("candidate conventions must be pinned")
    head = conn.execute(
        "SELECT generation FROM kala_layer_head WHERE chart_id = %s", (chart_id,)
    ).fetchone()
    expected = None if head is None else head[0]
    row = conn.execute(
        "SELECT generation, expected_head_generation FROM kala_layer_candidate "
        "WHERE build_id = %s", (build_id,)
    ).fetchone()
    if row is not None:
        if row[0] != generation or row[1] != expected:
            raise ValueError("build_id is already bound to another candidate")
        return Candidate(chart_id, generation, build_id, expected)
    conn.execute(
        "INSERT INTO kala_layer_candidate "
        "(chart_id, generation, build_id, expected_head_generation, model_digest, rule_registry_version, conventions) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (chart_id, generation, build_id, expected, model_digest, rule_registry_version, dict(conventions)),
    )
    return Candidate(chart_id, generation, build_id, expected)


def candidate_generation(ctx: Any) -> str:
    """Resolve only this build's candidate generation; never resolve current."""
    build_id = ctx.config.get("build_id")
    if not build_id:
        raise ValueError("build_id is required to resolve a candidate generation")
    row = ctx.db_conn.execute(
        "SELECT generation FROM kala_layer_candidate WHERE build_id = %s", (str(build_id),)
    ).fetchone()
    if row is None:
        raise LookupError("no candidate is bound to this build_id")
    return row[0]


def attest_grain(conn: Any, candidate: Candidate, *, grain_key: str,
                 result_state: str, input_vector: str) -> None:
    """Record every included grain, including an honestly empty result."""
    if not grain_key or result_state not in {"rows", "zero_rows", "failed"} or not input_vector:
        raise ValueError("grain key, result state, and input vector are required")
    conn.execute(
        "INSERT INTO kala_layer_candidate_grain "
        "(chart_id, generation, grain_key, result_state, input_vector) VALUES (%s, %s, %s, %s, %s) "
        "ON CONFLICT (chart_id, generation, grain_key) DO UPDATE SET "
        "result_state = EXCLUDED.result_state, input_vector = EXCLUDED.input_vector, recorded_at = now()",
        (candidate.chart_id, candidate.generation, grain_key, result_state, input_vector),
    )
