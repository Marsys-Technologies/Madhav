"""Content-bound, non-destructive substep resume helpers.

``build_substep_progress`` predates candidates, so its fingerprint is the
compatibility envelope: candidate generation, every consumed input, writer
code digest, and the grain key.  A record from any other envelope is ignored.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ResumeContext:
    candidate_generation: str
    input_vector: str
    code_digest: str

    def fingerprint(self, grain: str) -> str:
        """Return a stable, content-bound ledger fingerprint for one grain."""
        if not all((self.candidate_generation, self.input_vector, self.code_digest, grain)):
            raise ValueError("candidate, input vector, code digest, and grain are required")
        encoded = json.dumps(
            {
                "candidate_generation": self.candidate_generation,
                "code_digest": self.code_digest,
                "grain": grain,
                "input_vector": self.input_vector,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def _value(row: Any, key: str, position: int) -> Any:
    return row[key] if isinstance(row, Mapping) else row[position]


def completed_grains(conn: Any, *, chart_id: str, asset_id: str,
                     context: ResumeContext) -> frozenset[str]:
    """Read matching completed grains without mutating the progress ledger."""
    with conn.cursor() as cursor:
        cursor.execute(
            """SELECT substep_key, build_fingerprint
                 FROM build_substep_progress
                WHERE chart_id = %s AND asset_id = %s""",
            (chart_id, asset_id),
        )
        rows = cursor.fetchall()
    return frozenset(
        grain
        for row in rows
        if (grain := str(_value(row, "substep_key", 0)))
        and _value(row, "build_fingerprint", 1) == context.fingerprint(grain)
    )


def pending_grains(conn: Any, *, chart_id: str, asset_id: str,
                   context: ResumeContext, grains: Iterable[str]) -> tuple[str, ...]:
    """Plan unfinished grains only; this intentionally performs no DELETE."""
    completed = completed_grains(
        conn, chart_id=chart_id, asset_id=asset_id, context=context
    )
    return tuple(grain for grain in grains if grain not in completed)


def record_completion(conn: Any, *, chart_id: str, asset_id: str,
                      context: ResumeContext, grain: str, rows_written: int) -> None:
    """Persist successful grain progress under its complete content identity."""
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT INTO build_substep_progress
                   (chart_id, asset_id, substep_key, build_fingerprint,
                    rows_written, completed_at)
               VALUES (%s, %s, %s, %s, %s, now())
               ON CONFLICT (chart_id, asset_id, substep_key) DO UPDATE SET
                 build_fingerprint = EXCLUDED.build_fingerprint,
                 rows_written = EXCLUDED.rows_written,
                 completed_at = EXCLUDED.completed_at""",
            (chart_id, asset_id, grain, context.fingerprint(grain), rows_written),
        )


__all__ = ["ResumeContext", "completed_grains", "pending_grains", "record_completion"]
