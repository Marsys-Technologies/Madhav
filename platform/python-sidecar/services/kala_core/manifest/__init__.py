"""Candidate-bound Kāla layer manifest; serving must resolve only a published head."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from services.kala_core.idempotency import PublishCandidate, publish_head


@dataclass(frozen=True)
class Candidate:
    chart_id: str
    generation: str
    build_id: str
    expected_head_generation: str | None


class CandidateNotPublishable(ValueError):
    """A candidate has not earned a change to the serving head."""


def open_candidate(
    conn: Any, *, chart_id: str, generation: str, build_id: str,
    model_digest: str, rule_registry_version: str, conventions: Mapping[str, Any],
) -> Candidate:
    """Open the one candidate bound to a build; never changes a published head."""
    if not all((chart_id, generation, build_id, model_digest, rule_registry_version)):
        raise ValueError("candidate identity and pinned inputs are required")
    if not conventions:
        raise ValueError("candidate conventions must be pinned")
    row = conn.execute(
        "SELECT generation, expected_head_generation FROM kala_layer_candidate "
        "WHERE build_id = %s", (build_id,)
    ).fetchone()
    if row is not None:
        if row[0] != generation:
            raise ValueError("build_id is already bound to another candidate")
        # A retry resumes the candidate's original compare-and-swap baseline.
        # Looking up the live head first would turn a concurrent publication
        # into a different candidate contract.
        return Candidate(chart_id, generation, build_id, row[1])
    head = conn.execute(
        "SELECT generation FROM kala_layer_head WHERE chart_id = %s", (chart_id,)
    ).fetchone()
    expected = None if head is None else head[0]
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


def publish_candidate(conn: Any, candidate: Candidate, *, expected_grains: Iterable[str]) -> None:
    """Publish only a complete, independently accepted candidate via CAS.

    ``expected_grains`` comes from the build plan, rather than treating the
    presence of any successful grain as evidence of a complete build.
    """
    required = tuple(expected_grains)
    if not required or any(not grain for grain in required):
        raise ValueError("expected grains must be explicit and non-empty")
    rows = conn.execute(
        "SELECT grain_key, result_state FROM kala_layer_candidate_grain "
        "WHERE chart_id = %s AND generation = %s",
        (candidate.chart_id, candidate.generation),
    ).fetchall()
    observed = {row[0]: row[1] for row in rows}
    missing = set(required) - set(observed)
    failed = [grain for grain in required if observed.get(grain) == "failed"]
    if missing or failed:
        raise CandidateNotPublishable(
            "candidate is incomplete: " + ", ".join(sorted(missing | set(failed)))
        )
    verification = conn.execute(
        "SELECT result FROM kala_layer_verification WHERE chart_id = %s AND generation = %s",
        (candidate.chart_id, candidate.generation),
    ).fetchone()
    if verification is None or verification[0] != "accepted":
        raise CandidateNotPublishable("candidate lacks independent accepted verification")
    publish_head(conn, candidate.chart_id,
                 PublishCandidate(candidate.generation, candidate.expected_head_generation))
    conn.execute(
        "UPDATE kala_layer_candidate SET state = 'published' "
        "WHERE chart_id = %s AND generation = %s",
        (candidate.chart_id, candidate.generation),
    )


def rollback_head(conn: Any, *, chart_id: str, retained_generation: str,
                  expected_head_generation: str) -> None:
    """Restore a retained candidate with the same compare-and-swap discipline."""
    if not all((chart_id, retained_generation, expected_head_generation)):
        raise ValueError("rollback identities must be pinned")
    exists = conn.execute(
        "SELECT 1 FROM kala_layer_candidate WHERE chart_id = %s AND generation = %s",
        (chart_id, retained_generation),
    ).fetchone()
    if exists is None:
        raise CandidateNotPublishable("rollback target is not a retained candidate")
    publish_head(conn, chart_id, PublishCandidate(retained_generation, expected_head_generation))


_SELF_RESOLVED_CURRENT = re.compile(
    r"(?:generation|manifest)\s*=\s*['\"]current['\"]|"
    r"(?:resolve_generation|published_generation)\s*\([^)]*current",
    re.IGNORECASE,
)


def lint_no_self_resolved_generation(reader_paths: Iterable[str | Path]) -> None:
    """Refuse a reader that bypasses its build binding or serving head."""
    offenders = [str(path) for path in reader_paths
                 if _SELF_RESOLVED_CURRENT.search(Path(path).read_text())]
    if offenders:
        raise ValueError("reader resolves current generation itself: " + ", ".join(offenders))
