"""Writer-side candidate-grain attestation for the K9 publication path.

A writer dispatched under a build that is bound to a layer candidate attests
its own input grain under THAT candidate's generation (the contract
`services.kala_core.publication` verifies: every planned writer, exactly the
planned grain keys, state rows|zero_rows). A build with no bound candidate is
an ordinary rebuild: nothing is attested and predicate reads keep their
head-or-legacy resolution.

Planning stays read-only (ORCHESTRATOR_CONVERGENCE_CLOSE §7.1): `grain_steps`
only READS whether the grain is attested and offers a `grain:inputs` substep
when it is not; the substep's `run_substep` calls `attest_inputs`.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

from psycopg.rows import tuple_row

from pipeline.orchestrator.writers import SubStep
from services.kala_core.manifest import Candidate, attest_grain, lock_candidate_inputs

GRAIN_STEP = 'grain:inputs'
_RESERVED = ('legacy', 'current', 'published', 'retained')


def grain_key(asset_id: str) -> str:
    return f'{asset_id}:inputs'


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str)


def _first(conn: Any, query: str, params: tuple) -> tuple | None:
    """One row as a tuple, whatever row factory the (orchestrator, dict-row) connection uses."""
    row = conn.execute(query, params).fetchone()
    if row is None:
        return None
    return tuple(row.values()) if isinstance(row, dict) else tuple(row)


def bound_candidate(conn: Any, build_id: Any, chart_id: Any) -> Candidate | None:
    """The candidate THIS build is bound to, or None for an ordinary rebuild.

    Never resolves a head or a 'current' generation: a candidate-bound build
    reads and attests only its own candidate.
    """
    if not build_id:
        return None
    row = _first(conn, 'SELECT chart_id, generation FROM kala_layer_candidate WHERE build_id = %s',
                 (str(build_id),))
    if row is None:
        return None
    if str(row[0]) != str(chart_id):
        raise ValueError('candidate is bound to another chart')
    if row[1] in _RESERVED:
        raise ValueError('mutable new candidate required')
    # expected_head_generation is the publisher's compare-and-swap pin; attestation never uses it.
    return Candidate(str(row[0]), row[1], str(build_id), None)


def predicate_generation(conn: Any, chart_id: Any, candidate: Candidate | None) -> str:
    """Generation of `kala_activation_predicates` a reader consumes.

    A candidate-bound build reads its OWN candidate generation. An ordinary
    rebuild keeps the served resolution: the published head, else 'legacy'.
    """
    if candidate is not None:
        return candidate.generation
    row = _first(conn, 'SELECT generation FROM kala_layer_head WHERE chart_id = %s', (chart_id,))
    return row[0] if row else 'legacy'


def _prior_vector(conn: Any, candidate: Candidate, key: str) -> str | None:
    row = _first(conn, 'SELECT input_vector FROM kala_layer_candidate_grain '
                       'WHERE chart_id = %s AND generation = %s AND grain_key = %s',
                 (candidate.chart_id, candidate.generation, key))
    return row[0] if row else None


def grain_steps(ctx: Any, candidate: Candidate | None, asset_id: str,
                sources: Mapping[str, Iterable[Any]]) -> list[SubStep]:
    """Read-only: the attestation substep while the candidate lacks the grain OR holds
    a different input vector (drift is then refused loudly by `attest_inputs`, never
    left as a stale attestation over recomputed output)."""
    if candidate is None or getattr(ctx, 'dry_run', False):
        return []
    prior = _prior_vector(ctx.db_conn, candidate, grain_key(asset_id))
    if prior is not None and prior == input_vector({n: list(r) for n, r in sources.items()}):
        return []
    return [SubStep(key=GRAIN_STEP, label=f'{asset_id} candidate grain attestation')]


def input_vector(sources: Mapping[str, Iterable[Any]]) -> str:
    """Order-free digest of the rows a writer consumed (empty sets are hashed, not certified)."""
    return hashlib.sha256(_canonical(
        {name: sorted(_canonical(row) for row in rows) for name, rows in sources.items()}
    ).encode()).hexdigest()


def attest_inputs(conn: Any, candidate: Candidate, asset_id: str, *,
                  sources: Mapping[str, Iterable[Any]], produced_rows: int) -> str:
    """Attest `<asset_id>:inputs` under the candidate generation; refuse input drift.

    The input vector is immutable per candidate (as for ka_yojaka): a changed
    read set needs a new candidate, never a silent overwrite.
    """
    key = grain_key(asset_id)
    sources = {name: list(rows) for name, rows in sources.items()}
    vector = input_vector(sources)
    lock_candidate_inputs(conn, candidate)
    prior = _prior_vector(conn, candidate, key)
    if prior is not None and prior != vector:
        raise ValueError(f'candidate input vector changed for {key}; new candidate required')
    with conn.cursor(row_factory=tuple_row) as cur:
        attest_grain(cur, candidate, grain_key=key,
                     result_state='rows' if produced_rows > 0 else 'zero_rows', input_vector=vector)
    return vector
