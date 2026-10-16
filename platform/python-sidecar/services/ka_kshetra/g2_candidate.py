"""Private K5-3 candidate persistence; never publishes or registers a writer.

The orchestrator/caller owns the connection and transaction. A separate future
activation change must consume D-VC/D-G2 and K9-4b before any serving cutover.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
from typing import Mapping

from services.kala_core.manifest import Candidate, lock_candidate_inputs
from services.ka_kshetra.g2_model import (
    Calibration, EventModel, RiskSet, RouteCell, Suppression, build_field, model_digest,
)


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def write_candidate(
    ctx, *, model: EventModel, risk: RiskSet, cells: Mapping[str, tuple[RouteCell, ...]],
    source_pin: str, suppressions: tuple[Suppression, ...] = (),
    calibration: Calibration | None = None,
) -> int:
    """Replace only this build's NEW candidate × class with an input-pinned field.

    (I) INTERPRETATION: G2 has separate additive storage, not a semantic rewrite
    of G1 columns. No registered dispatch hook exists in this pre-build.
    The explicit manifest pin restricts this API to pre-build candidates.
    """
    digest = model_digest(model)
    field = build_field(model, risk, cells, suppressions, calibration=calibration)
    if not source_pin:
        raise ValueError('an upstream source pin is required')
    inputs = dict(model=asdict(model), risk=asdict(risk), source_pin=source_pin,
                  cells={key: [asdict(c) for c in rows] for key, rows in sorted(cells.items())},
                  suppressions=[asdict(s) for s in suppressions],
                  calibration=asdict(calibration) if calibration else None)
    input_digest = hashlib.sha256(_json(inputs).encode()).hexdigest()
    if ctx.dry_run:
        return 0
    chart_id, build_id = ctx.config.get('chart_id'), getattr(ctx, 'build_id', None)
    if not chart_id or not build_id:
        raise ValueError('chart_id and build_id are required')
    conn = ctx.db_conn
    identity = conn.execute('SELECT chart_id, generation FROM kala_layer_candidate WHERE build_id=%s',
                            (str(build_id),)).fetchone()
    if identity is None:
        raise LookupError('no candidate bound to this build')
    if str(identity[0]) != str(chart_id):
        raise ValueError('candidate belongs to another chart')
    generation = identity[1]
    if not generation.startswith('candidate:'):
        raise ValueError('a new candidate generation is required')
    candidate = Candidate(str(chart_id), generation, str(build_id), None)
    lock_candidate_inputs(conn, candidate)
    row = conn.execute('SELECT state, conventions FROM kala_layer_candidate '
                       'WHERE chart_id=%s AND generation=%s AND build_id=%s FOR UPDATE',
                       (chart_id, generation, str(build_id))).fetchone()
    if row is None or row[0] != 'building':
        raise ValueError('only the owning building candidate may be replaced')
    head = conn.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s FOR SHARE',
                        (chart_id,)).fetchone()
    if head and head[0] == generation:
        raise ValueError('published generation cannot be replaced')
    conventions = row[1] if isinstance(row[1], dict) else json.loads(row[1])
    pin = conventions.get('kshetra_g2', {})
    if (pin.get('prebuild_only') is not True or pin.get('source_pin') != source_pin
            or pin.get('model_digests', {}).get(model.event_class) != digest
            or not isinstance(pin.get('as_of_jd'), (int, float))
            or isinstance(pin['as_of_jd'], bool) or not math.isfinite(pin['as_of_jd'])):
        raise ValueError('candidate G2 source/model/prebuild pin does not match')
    # Full input bytes, including unavailable flags and evidence references, are
    # immutable on retry. A changed read set needs a different generation.
    grain_key = f'ka_kshetra:g2:{model.event_class}'
    prior = conn.execute('SELECT input_vector FROM kala_layer_candidate_grain '
                         'WHERE chart_id=%s AND generation=%s AND grain_key=%s',
                         (chart_id, generation, grain_key)).fetchone()
    if prior and prior[0] != input_digest:
        raise ValueError('G2 candidate input changed; open a new generation')
    payload = dict(schema='ka_kshetra_g2/1', prebuild_only=True, as_of_jd=pin['as_of_jd'],
                   model=asdict(model), risk_set=asdict(risk), field=asdict(field),
                   inputs=inputs,
                   source_pin=source_pin, input_digest=input_digest,
                   null_statistics=None, null_reason='G2_null_estimands_not_evaluated')
    # Serialize before deleting: malformed output cannot erase a valid retry.
    serialized = _json(payload)
    conn.execute('DELETE FROM kala_kshetra_g2_candidate '
                 'WHERE chart_id=%s AND generation=%s AND event_class=%s',
                 (chart_id, generation, model.event_class))
    conn.execute('INSERT INTO kala_kshetra_g2_candidate '
                 '(chart_id,generation,build_id,event_class,model_digest,input_digest,payload) '
                 'VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb)',
                 (chart_id, generation, str(build_id), model.event_class, digest, input_digest, serialized))
    conn.execute('INSERT INTO kala_layer_candidate_grain '
                 '(chart_id,generation,grain_key,result_state,input_vector) '
                 'VALUES (%s,%s,%s,%s,%s) ON CONFLICT (chart_id,generation,grain_key) DO NOTHING',
                 (chart_id, generation, grain_key, 'rows' if field.routes else 'zero_rows', input_digest))
    return 1


def write_graph_candidate(ctx, *, feature_specs, graph, relationships,
                          available_fact_ids, complete, dominance=None, **request) -> int:
    """End-to-end typed F1 projection → field → candidate, retaining every knot."""
    from services.ka_kshetra.g2_features import assemble_cells
    request['cells'] = assemble_cells(request['model'], request['cells'], feature_specs,
        graph, relationships, available_fact_ids, complete=complete, dominance=dominance)
    return write_candidate(ctx, **request)
