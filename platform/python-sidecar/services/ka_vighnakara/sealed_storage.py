"""K3-2 explicit sealed-candidate dispatch; caller owns the transaction.

v1 fixture writers remain unchanged. The v2 schema guard and nonfixture
candidate conventions must exist before any deletion. No publication occurs.
"""
from dataclasses import asdict
from copy import deepcopy
import hashlib

from psycopg.rows import dict_row, tuple_row
from psycopg.types.json import Jsonb

from brahmagyan.verification_vocab import TWO_PASS_VERIFIED, UNVERIFIED_DEFAULT
from services.kala_core import clocks
from services.kala_core.idempotency import replace_candidate_partition
from services.kala_core.manifest import Candidate, lock_candidate_inputs
from services.kala_core.stored_verification import has_stored_verification
from services.ka_vighnakara.sealed import VERSION, canonical, prepare, read_export, span, stamp, wire


def read_clock_spans(conn, bundle):
    """Use the existing F2 reader on the pinned build, not an export's label.

    F2 row ids/lords/lineage/bounds remain separate from chart_facts ids.
    ClockUnavailable is retained as its real reason on a typed unavailable
    span; SQL and programming errors propagate before candidate replacement.
    """
    pins = bundle['pins']
    systems = sorted({b['f2_system'] for b in bundle['correspondence'] if b.get('f2_system')})
    horizons = [span(c['requested_horizon']) for c in bundle['coverage']]
    if not horizons:
        return []
    lo, hi = min(a for a, _ in horizons), max(b for _, b in horizons)
    output = []
    # Clock readers expect mapping rows. The wrapper owns no transaction or
    # connection; every query still executes on ctx.db_conn.
    class Reader:
        def execute(self, statement, params):
            cursor = conn.cursor(row_factory=dict_row)
            try:
                cursor.execute(statement, params)
                rows = cursor.fetchall()
            finally:
                cursor.close()
            class Result:
                def fetchall(self):
                    return rows
            return Result()
    reader = Reader()
    for system in systems:
        args = dict(build_id=pins['natal_build_id'],ayanamsha_id=pins['ayanamsha_id'],
                    tier=TWO_PASS_VERIFIED,scenario_id=pins['f2_scenario_id'])
        def unavailable(start,end,reason):
            return dict(interval=wire(start,end),applicability='unknown',period_ids={},lords={},lineage={},
                sources=[],system=system,null_reason=reason,**args)
        try:
            # F2.boundaries intentionally refuses inapplicable methods. Its
            # pinned row reader supplies exact stored endpoints; period_context
            # supplies applicability and validates the active lineage.
            source_rows = clocks._read_rows(reader,pins['chart_id'],clocks.stored_system(system),
                build_id=args['build_id'],ayanamsha_id=args['ayanamsha_id'],tier=args['tier'])
        except clocks.ClockUnavailable as exc:
            output.append(unavailable(lo,hi,str(exc)))
            continue
        cuts = sorted({lo,hi} | {r[k] for r in source_rows for k in ('start_iso','end_iso') if lo < r[k] < hi})
        for start,end in zip(cuts,cuts[1:]):
            try:
                context = clocks.period_context(reader,pins['chart_id'],start,system,**args)
            except clocks.ClockUnavailable as exc:
                output.append(unavailable(start,end,str(exc)))
                continue
            lineage = {str(r['dasha_row_id']): dict(parent_row_id=r['parent_row_id'],
                start=r['start_iso'].isoformat(),end=r['end_iso'].isoformat())
                for r in source_rows if str(r['dasha_row_id']) in context.period_ids.values()}
            output.append(dict(interval=wire(start,end),applicability=context.applicability,
                period_ids=context.period_ids,lords=context.lords,lineage=lineage,
                method=asdict(context.method),sources=list(context.method.sources),system=system,**args))
    return output


def write_sealed_candidate(ctx):
    if ctx.dry_run:
        return 0
    config = ctx.config['negative_space_sealed']
    chart = str(ctx.config['chart_id'])
    bundle = read_export(config['receipt'],config['expected'])
    if bundle['pins']['chart_id'] != chart:
        raise ValueError('source chart differs from build chart')
    conn = ctx.db_conn
    # Same advisory lock as publication, taken before the lifecycle row lock.
    with conn.cursor(row_factory=tuple_row) as cursor:
        row = cursor.execute('SELECT chart_id,generation,state,conventions FROM kala_layer_candidate '
            'WHERE build_id=%s', (str(ctx.build_id),)).fetchone()
    if row is None:
        raise ValueError('no candidate bound to this build')
    candidate = Candidate(chart, row[1], str(ctx.build_id), None)
    lock_candidate_inputs(conn,candidate)
    with conn.cursor(row_factory=tuple_row) as cursor:
        row = cursor.execute('SELECT chart_id,generation,state,conventions FROM kala_layer_candidate '
            'WHERE build_id=%s FOR UPDATE', (str(ctx.build_id),)).fetchone()
        if (row is None or str(row[0]) != chart or row[1] != candidate.generation or row[2] != 'building'
                or not row[1].startswith('candidate:') or row[1] == 'candidate:'):
            raise ValueError('only this build-bound private building candidate may be replaced')
        generation = row[1]
        conventions = row[3]
        if conventions.get('fixture') is True or conventions.get('negative_space') != bundle['pins']:
            raise ValueError('nonfixture candidate must pin exact negative-space producer inputs')
        head = cursor.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s FOR SHARE', (chart,)).fetchone()
        if head and head[0] == generation:
            raise ValueError('published candidate cannot be replaced')
        guard = cursor.execute("SELECT 1 FROM pg_constraint WHERE conrelid='public.kala_obstruction'::regclass "
            "AND conname='kala_obstruction_k3_sealed_check' AND convalidated", ()).fetchone()
        identity_guard = cursor.execute("SELECT 1 FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid "
            "WHERE i.indrelid='public.kala_obstruction'::regclass AND c.relname='kala_obstruction_k3_sealed_identity' "
            "AND i.indisunique AND i.indisvalid", ()).fetchone()
        if not guard or not identity_guard:
            raise ValueError('K3-2 live storage schema prerequisite is absent/unverified')
        inputs = read_clock_spans(conn,bundle)
        prepared = prepare(bundle,candidate_generation=generation,clock_spans=inputs)
        inventory_ref = dict(row_count=config['expected']['row_count'],
            counts={kind:len(keys) for kind,keys in config['expected']['keys'].items()},
            keys_sha256=hashlib.sha256(canonical(config['expected']['keys']).encode()).hexdigest())
        rows = []
        tier = has_stored_verification(cursor,'kala_obstruction')
        for result in prepared:
            result['provenance']['export_receipt'] = deepcopy(config['receipt'])
            result['provenance']['independent_inventory'] = deepcopy(inventory_ref)
            row = {k:result[k] for k in ('assertion_id','event_class_id','exposure','knowledge',
                'rule_conclusion','defeat_state','effective_state','measurement','what','by_what',
                'null_reason','release_reason')}
            row.update(chart_id=chart,generation=generation,negative_space_contract_version=VERSION,
                assertion=Jsonb(result),roots=Jsonb(result['roots']),release=Jsonb(result['release']),
                interval_start=stamp(result['interval']['t0']),interval_end=stamp(result['interval']['t1']),
                obstruction_type='malefic_transit',severity='mild',severity_score=0,override_score=0,
                obstruction_detail=Jsonb({}),source_citation=result['source']['locator'])
            if tier:
                row['verification_pass_status'] = UNVERIFIED_DEFAULT
            rows.append(row)
        return replace_candidate_partition(cursor,'kala_obstruction',chart,generation,None,rows)
