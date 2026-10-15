"""K5-2b lossless compact candidate field; PRE-BUILD, SR-A4-01.

No solver, knot thinning, publication or legacy DML lives here. Source contract:
K5-G1a migration 1385's ``kala_field_candidate`` (LIKE legacy migration 492,
with generation in every natural key). It may land after this pre-build.

(I) INTERPRETATION: retain *every* corrected-reference segment and coefficient.
This admits a storage projection, not a new approximation or a promised row-count
reduction. Structural and null arithmetic therefore stay bitwise identical.
(I) INTERPRETATION: G1 has no specified event-process risk set (ALGO 3.20 G2).
Persist an unknown mask with its reason; never turn unknown eligibility into true.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Mapping, Sequence

from pipeline.orchestrator.writers import SubStep, WriterResult
from services.kala_core.manifest import Candidate, lock_candidate_inputs
from services.ka_kshetra.contracts import Segment
from services.ka_kshetra.integrator import segment_integral
from services.ka_kshetra.stage4_field import _rows

VERSION = 'compact-coefficients-v1'
_COLUMNS = (
    'segment_index', 't_start', 't_end', 'alpha', 'gamma', 'integral_days',
    'refinement_depth', 'refinement_exhausted', 'refinement_residual',
    'field_snapshot_id', 'weights_version', 'x_schema_version',
)
_SELECT = ', '.join(_COLUMNS)


def decode_segments(rows: Sequence[Mapping]) -> list[Segment]:
    """Restore exactly the reference representation used by integration/nulls."""
    return [Segment(index=r['segment_index'], t_start=r['t_start'], t_end=r['t_end'],
                    alpha=r['alpha'], gamma=r['gamma'],
                    refinement_depth=r['refinement_depth'],
                    refinement_exhausted=r['refinement_exhausted'],
                    refinement_residual=r['refinement_residual']) for r in rows]


def encode_segments(rows: Sequence[Mapping]) -> list[dict]:
    """Validate the whole class before deletion, retaining coefficients verbatim.

    The sole tolerance (5e-13 relative) validates the source's denormalized
    integral against the existing analytic integrator; the stored source value
    itself is copied, so no arithmetic or evaluation order changes in storage.
    """
    encoded = []
    previous_end = None
    indices = set()
    pins = None
    for row in rows:
        r = {column: row[column] for column in _COLUMNS}
        if (type(r['segment_index']) is not int or r['segment_index'] < 0
                or r['segment_index'] in indices):
            raise ValueError('invalid or duplicate compact segment index')
        indices.add(r['segment_index'])
        if not all(math.isfinite(r[k]) for k in ('t_start','t_end','alpha','gamma','integral_days')):
            raise ValueError('non-finite compact coefficient or integral')
        if r['t_end'] <= r['t_start'] or (previous_end is not None and r['t_start'] != previous_end):
            raise ValueError('compact source has a gap, overlap or reversed span')
        if not 0 <= r['refinement_depth'] <= 6:
            raise ValueError('invalid compact refinement depth')
        residual = r['refinement_residual']
        if residual is not None and (not math.isfinite(residual) or residual < 0):
            raise ValueError('invalid compact refinement residual')
        identity = tuple(r[k] for k in ('field_snapshot_id','weights_version','x_schema_version'))
        if not all(identity) or (pins is not None and identity != pins):
            raise ValueError('compact source mixes field identity pins')
        pins = identity
        segment = decode_segments([r])[0]
        try:
            integral = segment_integral(segment, segment.t_start, segment.t_end)
        except OverflowError as exc:
            raise ValueError('compact source integral overflow') from exc
        if (not math.isfinite(integral) or r['integral_days'] < 0
                or not math.isclose(r['integral_days'], integral, rel_tol=5e-13, abs_tol=0.)):
            raise ValueError('compact source integral disagrees with coefficients')
        previous_end = r['t_end']
        r.update(risk_mask=None, risk_mask_reason='risk_set_not_specified')
        encoded.append(r)
    return encoded


def _candidate(ctx, *, lock=False) -> tuple[str, str, str]:
    chart = str(ctx.config['chart_id'])
    generation = ctx.config['kshetra_compact_candidate']
    build = str(ctx.build_id)
    if (not isinstance(generation, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,128}', generation)
            or generation in {'legacy','current','retained','published'}):
        raise ValueError('explicit fresh compact candidate required')
    with ctx.db_conn.cursor() as cur:
        if lock:
            lock_candidate_inputs(cur, Candidate(chart, generation, build, None))
        cur.execute('''SELECT c.state FROM kala_layer_candidate c
            JOIN build_runs b ON b.id=c.build_id AND b.chart_id=c.chart_id
            WHERE c.chart_id=%s AND c.generation=%s AND c.build_id=%s'''
            + (' FOR UPDATE OF c' if lock else ''), (chart,generation,build))
        candidates = _rows(cur)
        if len(candidates) != 1 or candidates[0]['state'] != 'building':
            raise ValueError('compact field requires a building candidate bound to this chart/build')
        cur.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s', (chart,))
        if any(r['generation'] == generation for r in _rows(cur)):
            raise ValueError('compact field cannot replace a published head')
    return chart, generation, build


def plan_substeps(ctx) -> list[SubStep]:
    """Read-only plan; ordinary dispatch stays inactive until explicit admission."""
    if not ctx.config.get('kshetra_compact_candidate'):
        return [SubStep(key='compact:inactive', label='compact field pre-build; activation gated')]
    chart, generation, _ = _candidate(ctx)
    with ctx.db_conn.cursor() as cur:
        cur.execute('''SELECT DISTINCT event_class FROM kala_field_candidate
            WHERE chart_id=%s AND generation=%s ORDER BY event_class''', (chart,generation))
        classes = _rows(cur)
    if not classes:
        raise RuntimeError('upstream_stage_incomplete: no G1 candidate field; no compact empty attestation')
    return [SubStep(key='compact:'+r['event_class'], label='compact field '+r['event_class']) for r in classes]


def run_substep(ctx, step: SubStep) -> WriterResult:
    """Replace one unpublished class partition in the orchestrator transaction."""
    if not ctx.config.get('kshetra_compact_candidate'):
        if step.key != 'compact:inactive':
            raise ValueError('compact candidate was not admitted')
        return WriterResult('ka_kshetra',0,notes='SR-A4-01 pre-build inactive; published and dense rows preserved')
    if not step.key.startswith('compact:') or step.key == 'compact:inactive':
        raise ValueError('invalid compact field substep')
    chart,generation,build = _candidate(ctx,lock=not ctx.dry_run)
    event_class = step.key.split(':',1)[1]
    grain = 'ka_kshetra:compact:'+event_class
    with ctx.db_conn.cursor() as cur:
        cur.execute(f'''SELECT {_SELECT} FROM kala_field_candidate
            WHERE chart_id=%s AND generation=%s AND event_class=%s
            ORDER BY t_start,segment_index''', (chart,generation,event_class))
        source = _rows(cur)
        if not source:
            raise RuntimeError('upstream_stage_incomplete: G1 candidate class has no segments')
        encoded = encode_segments(source)
        cur.execute("""SELECT field_content_hash,config_pin,horizon_days,
            weights_version,x_schema_version,event_classes,skipped_classes
            FROM kala_field_snapshots_candidate
            WHERE chart_id=%s AND generation=%s AND field_snapshot_id=%s""",
            (chart,generation,source[0]['field_snapshot_id']))
        snapshots = _rows(cur)
        if len(snapshots) != 1 or not snapshots[0]['field_content_hash']:
            raise RuntimeError('upstream_stage_incomplete: finalized G1 snapshot required')
        snapshot = snapshots[0]
        if (source[0]['t_start'] != 0. or source[-1]['t_end'] != snapshot['horizon_days']
                or event_class not in snapshot['event_classes']
                or any(r['event_class'] == event_class for r in snapshot['skipped_classes'])):
            raise ValueError('compact source does not cover the finalized class horizon')
        if any(source[0][key] != snapshot[key] for key in ('weights_version','x_schema_version')):
            raise ValueError('compact input pins changed from finalized snapshot')
        vector = hashlib.sha256(json.dumps({'representation':VERSION,'source':source,'snapshot':snapshot},
            sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        cur.execute('''SELECT input_vector FROM kala_layer_candidate_grain
            WHERE chart_id=%s AND generation=%s AND grain_key=%s''', (chart,generation,grain))
        prior = _rows(cur)
        if prior and prior[0]['input_vector'] != vector:
            raise ValueError('compact input vector changed; new candidate required')
        if not ctx.dry_run:
            cur.execute('''DELETE FROM kala_field_compact
                WHERE chart_id=%s AND generation=%s AND event_class=%s''', (chart,generation,event_class))
            columns = ('chart_id','generation','build_id','event_class') + _COLUMNS + ('risk_mask','risk_mask_reason')
            values = [(chart,generation,build,event_class)+tuple(r[k] for k in columns[4:]) for r in encoded]
            cur.executemany('INSERT INTO kala_field_compact (' + ','.join(columns) + ') VALUES ('
                            + ','.join(['%s']*len(columns)) + ')',values)
            cur.execute('''INSERT INTO kala_layer_candidate_grain
                (chart_id,generation,grain_key,result_state,input_vector)
                VALUES (%s,%s,%s,'rows',%s) ON CONFLICT (chart_id,generation,grain_key)
                DO UPDATE SET result_state=EXCLUDED.result_state,input_vector=EXCLUDED.input_vector''',
                (chart,generation,grain,vector))
    return WriterResult('ka_kshetra',0 if ctx.dry_run else len(encoded),
        notes=f'{VERSION}; source_segments={len(source)}; compact_segments={len(encoded)}; '
              'risk_mask=unknown; publication_gated')
