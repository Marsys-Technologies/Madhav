"""K6-4: monthly integrals over a build-bound forecaster candidate.

PRE-BUILD, SR-A4-01: ordinary dispatch is inactive. The explicit
``taranga_candidate`` rehearsal switch never publishes or writes legacy data.
K5-G1a's 1385 sibling field/snapshot contract is the upstream input. Months
are UTC half-open intervals; integration uses the forecaster's own evaluator.
Risk-set metadata is not in that contract yet and stays honestly unavailable.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import math

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from pipeline.orchestrator.writers.ka_read_model_integrity import bind_integrity_target
from services.ka_kshetra.contracts import Segment
from services.ka_kshetra.integrator import segment_integral
from services.kala_core.idempotency import replace_candidate_partition
from services.kala_core.manifest import Candidate, lock_candidate_inputs

FORMULA_VERSION = 'ka_taranga_integral_v2'


def _month_start(instant):
    return instant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _next_month(instant):
    return instant.replace(year=instant.year+1, month=1) if instant.month == 12 else instant.replace(month=instant.month+1)


def _project(segments, snapshots):
    """Validate before replacing anything; duplicate identities must agree."""
    unique = {}
    for row in segments:
        key = (row['event_class'], row['segment_index'])
        if key in unique and unique[key] != row:
            raise ValueError('conflicting duplicate field segment')
        unique[key] = row
    by_class = defaultdict(list)
    for row in unique.values():
        values = [row[k] for k in ('t_start','t_end','alpha','gamma','integral_days')]
        if not all(math.isfinite(v) for v in values) or row['t_end'] <= row['t_start'] or row['integral_days'] < 0:
            raise ValueError('invalid field segment')
        by_class[row['event_class']].append(row)
    output = {}
    for event, group in sorted(by_class.items()):
        group.sort(key=lambda r: (r['t_start'],r['t_end'],r['segment_index']))
        previous_end = None
        origins = set()
        for row in group:
            snap = snapshots.get(row['field_snapshot_id'])
            if snap is None or not snap['field_content_hash']:
                raise ValueError('finalized source snapshot required')
            pin = snap['config_pin']
            if not str(pin.get('axis','')).startswith('days_since_birth_UT') or not pin.get('birth_utc'):
                raise ValueError('pinned UTC birth axis required')
            origin = datetime.fromisoformat(pin['birth_utc'])
            if origin.tzinfo is None:
                raise ValueError('birth axis must include timezone')
            origin = origin.astimezone(timezone.utc)
            origins.add(origin)
            if len(origins) != 1:
                raise ValueError('conflicting field time axes')
            if previous_end is not None and row['t_start'] < previous_end:
                raise ValueError('overlapping field segments')
            previous_end = row['t_end']
            seg = Segment(row['segment_index'],row['t_start'],row['t_end'],row['alpha'],row['gamma'])
            month = _month_start(origin + timedelta(days=seg.t_start))
            end = origin + timedelta(days=seg.t_end)
            while month < end:
                next_month = _next_month(month)
                u = max(seg.t_start, (month-origin).total_seconds()/86400)
                v = min(seg.t_end, (next_month-origin).total_seconds()/86400)
                if v > u:
                    value = segment_integral(seg,u,v)
                    if not math.isfinite(value) or value < 0:
                        raise ValueError('nonfinite monthly integral')
                    key = (month.date(),event)
                    cell = output.setdefault(key, dict(values=[],snapshots=set(),segments=set()))
                    cell['values'].append(value)
                    cell['snapshots'].add(row['field_snapshot_id'])
                    cell['segments'].add(f'{event}:{row["segment_index"]}')
                month = next_month
    return output


@register('ka_taranga')
class KaTarangaWriter(WriterBase):
    """Read model only; caller owns the transaction and serving-head switch."""

    def run(self, ctx) -> WriterResult:
        if getattr(ctx, 'dry_run', False):
            return WriterResult(self.asset_id, 0, notes='dry_run: no output changed')
        if not ctx.config.get('taranga_candidate'):
            if getattr(ctx, 'db_conn', None) is not None:
                bind_integrity_target(ctx)
            return WriterResult(self.asset_id, 0, notes='pre-build SR-A4-01: inactive; served output unchanged')
        chart = str(ctx.config['chart_id'])
        build = str(ctx.build_id)
        conn = ctx.db_conn
        bind_integrity_target(ctx)
        # Same lock order as the manifest and K5 candidate guard, before reading
        # any stage rows. The row lock is held by the caller's transaction.
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute('SELECT generation FROM kala_layer_candidate WHERE chart_id=%s AND build_id=%s', (chart,build))
            bound = cur.fetchone()
            if bound is None:
                return WriterResult(self.asset_id, 0, notes='unbound build: zero candidate writes; served output unchanged')
            gen = bound['generation']
            lock_candidate_inputs(conn, Candidate(chart,gen,build,None))
            cur.execute('''SELECT c.state,c.conventions FROM kala_layer_candidate c
                JOIN build_runs b ON b.id=c.build_id AND b.chart_id=c.chart_id
                WHERE c.chart_id=%s AND c.generation=%s AND c.build_id=%s FOR UPDATE OF c''', (chart,gen,build))
            candidate = cur.fetchone()
            cur.execute('SELECT 1 FROM kala_layer_head WHERE chart_id=%s AND generation=%s', (chart,gen))
            if (not candidate or candidate['state'] != 'building' or gen in {'legacy','published','current','retained'} or cur.fetchone()):
                raise ValueError('building candidate bound to chart/build required; published generation is immutable')
            cur.execute('''SELECT event_class,segment_index,t_start,t_end,alpha,gamma,integral_days,field_snapshot_id
                FROM kala_field_candidate WHERE chart_id=%s AND generation=%s
                ORDER BY event_class,t_start,segment_index''', (chart,gen))
            segments = cur.fetchall()
            cur.execute('''SELECT field_snapshot_id,field_content_hash,config_pin FROM kala_field_snapshots_candidate
                WHERE chart_id=%s AND generation=%s ORDER BY field_snapshot_id''', (chart,gen))
            snapshots = {}
            for snap in cur.fetchall():
                key = snap['field_snapshot_id']
                if key in snapshots and snapshots[key] != snap:
                    raise ValueError('conflicting duplicate field snapshot')
                snapshots[key] = snap
            projected = _project(segments,snapshots)
            cur.execute('''SELECT event_class,domain,source FROM kala_taranga_class_domain
                WHERE chart_id=%s AND generation=%s ORDER BY event_class,domain,source''', (chart,gen))
            mappings = cur.fetchall()
            domains = defaultdict(set)
            sources = defaultdict(list)
            for m in mappings:
                domains[m['event_class']].add(m['domain'])
                sources[(m['event_class'],m['domain'])].append(m['source'])
            # (I) INTERPRETATION: an explicit candidate convention pins the
            # evaluated judge generation. No inferred "current"/legacy head.
            judge_gen = candidate['conventions'].get('taranga_judge_generation')
            judge = defaultdict(set)
            if judge_gen:
                cur.execute('''SELECT DISTINCT window_id,event_class,lower(interval) AS start,upper(interval) AS finish
                    FROM ka_gochara_eval_window WHERE chart_id=%s AND generation=%s
                    ORDER BY event_class,window_id''', (chart,judge_gen))
                for window in cur.fetchall():
                    month = _month_start(window['start'].astimezone(timezone.utc))
                    while month < window['finish']:
                        judge[(month.date(),window['event_class'])].add(str(window['window_id']))
                        month = _next_month(month)
        cells = {}
        for (month,event), cell in projected.items():
            for kind, scope in [('event_class',event), *(('domain',d) for d in sorted(domains[event]))]:
                key = (month,kind,scope)
                target = cells.setdefault(key,dict(values=[],classes=set(),snapshots=set(),segments=set(),windows=set(),sources=[],overlap=False))
                target['values'].extend(cell['values'])
                target['classes'].add(event)
                target['snapshots'].update(cell['snapshots'])
                target['segments'].update(cell['segments'])
                target['windows'].update(judge[(month,event)])
                target['overlap'] |= len(domains[event]) > 1
                if kind == 'domain':
                    target['sources'].extend(dict(event_class=event,domain=scope,source=s) for s in sources[(event,scope)])
        rows = []
        for (month,kind,scope), cell in sorted(cells.items()):
            rows.append(dict(chart_id=chart,generation=gen,month=month,scope_kind=kind,scope_id=scope,
                integral=math.fsum(cell['values']), units='expected_events', risk_set=None,
                risk_set_null_reason='upstream_risk_set_unavailable',
                judge_window_count=len(cell['windows']) if judge_gen else None,
                judge_count_null_reason=None if judge_gen else 'judge_generation_unpinned',
                overlap_flag=cell['overlap'], formula_version=FORMULA_VERSION,
                source_refs=Jsonb(dict(field_snapshot_ids=sorted(cell['snapshots']),
                    field_segment_ids=sorted(cell['segments']),event_classes=sorted(cell['classes']),
                    judge_generation=judge_gen,judge_window_ids=sorted(cell['windows']),
                    class_domain_sources=cell['sources'],overlap_rule='once_per_class_per_domain'))))
        count = replace_candidate_partition(conn,'kala_taranga_candidate',chart,gen,None,rows)
        return WriterResult(self.asset_id,count,notes=f'candidate={gen}; pre-build only; risk_set unavailable; no publication')
