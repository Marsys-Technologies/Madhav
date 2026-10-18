"""Explicit candidate-only KA-3b persistence on the orchestrator transaction."""
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

from psycopg.rows import dict_row, tuple_row
from psycopg.types.json import Jsonb

from services.kala_core.idempotency import replace_candidate_partition
from services.kala_core.manifest import Candidate, candidate_generation, lock_candidate_inputs, attest_grain
from .contested import AdapterPayload, canonical


def replace_candidate(ctx, payload):
    if not isinstance(payload, AdapterPayload):
        raise TypeError('typed KA-3b payload required')
    payload.validate()
    chart = str(ctx.config['chart_id'])
    pctx = payload.context
    if pctx.chart_id != chart:
        raise ValueError('payload belongs to another chart')
    if payload.family in ('tithi_pravesha', 'sudarshana_varsha'):
        params = ctx.config.get('birth_params') or {}
        try:
            birth = datetime.fromisoformat(params['datetime_iso'])
            if payload.family == 'sudarshana_varsha':
                same = payload.sources['birth_date'] == birth.date().isoformat()
            else:
                if birth.tzinfo is None:
                    birth = birth.replace(tzinfo=timezone(timedelta(hours=float(params['tz_offset_hours']))))
                supplied_birth = datetime.fromisoformat(payload.sources['birth_datetime'])
                same = supplied_birth.tzinfo is not None and birth == supplied_birth
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError('explicit orchestrator birth parameters required') from exc
        if not same:
            raise ValueError('candidate birth input differs from orchestrator birth parameters')
    conn = ctx.db_conn
    with conn.cursor(row_factory=tuple_row) as cur:
        generation = candidate_generation(SimpleNamespace(db_conn=cur, build_id=ctx.build_id))
        if generation != pctx.generation:
            raise ValueError('payload belongs to another candidate generation')
        candidate = Candidate(chart, generation, str(ctx.build_id), None)
        lock_candidate_inputs(cur, candidate)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute('SELECT * FROM kala_layer_candidate WHERE chart_id=%s AND generation=%s AND build_id=%s FOR UPDATE',
                    (chart, generation, str(ctx.build_id)))
        record = cur.fetchone()
        if record is None or record['state'] != 'building':
            raise ValueError('mutable building candidate bound to chart/build required')
        cur.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s FOR SHARE', (chart,))
        if any(r['generation'] == generation for r in cur.fetchall()):
            raise ValueError('published candidate cannot be replaced')
        cur.execute('SELECT chart_id FROM build_runs WHERE id=%s', (str(ctx.build_id),))
        build = cur.fetchone()
        pin = (record['conventions'] or {}).get('natal', {})
        if build is None or str(build['chart_id']) != chart:
            raise ValueError('candidate build belongs to another chart')
        if pin.get('build_id') != pctx.natal_build_id or pin.get('ayanamsha_id') != pctx.convention.ayanamsha_id:
            raise ValueError('candidate natal build/ayanamsha mismatch')
        cur.execute('SELECT chart_id FROM build_runs WHERE id=%s', (pctx.natal_build_id,))
        natal = cur.fetchone()
        if natal is None or str(natal['chart_id']) != chart:
            raise ValueError('natal build belongs to another chart')
        # Protect the exact read set, including absent facts/reference rows,
        # through replacement and orchestrator commit. Never own that commit.
        cur.execute('LOCK TABLE chart_facts IN SHARE MODE')
        required = (('LAGNA','sign'), ('MOON','sign'), ('SUN','sign')) if payload.family == 'sudarshana_varsha' else (('MOON','longitude_sidereal'),)
        supplied = {(f['fact_subject'], f['fact_key']): f for f in pctx.facts}
        for subject, key in set(required) | set(supplied):
            cur.execute('SELECT fact_id,fact_subject,fact_key,fact_value_num,fact_value_text FROM chart_facts '
                        'WHERE chart_id=%s AND build_id=%s AND ayanamsha_id=%s '
                        "AND fact_category='graha_position' AND fact_subject=%s AND fact_key=%s ORDER BY fact_id",
                        (chart, pctx.natal_build_id, pctx.convention.ayanamsha_id, subject, key))
            observed = cur.fetchall()
            fact = supplied.get((subject,key))
            if len(observed) > 1 or bool(observed) != (fact is not None):
                raise ValueError('L1 fact missing, ambiguous or changed')
            if observed:
                db = observed[0]
                if db['fact_id'] != fact['fact_id']:
                    raise ValueError('L1 fact reference changed')
                value_key = 'fact_value_num' if key == 'longitude_sidereal' else 'fact_value_text'
                a,b = db[value_key], fact.get(value_key)
                if a is None or b is None or (float(a) != float(b) if value_key == 'fact_value_num' else a != b):
                    raise ValueError('L1 fact value changed')
        if payload.family == 'moorti_nirnaya':
            cur.execute('LOCK TABLE bg_transit_moorti IN SHARE MODE')
            cur.execute('SELECT nakshatra_offset,moorti_name,quality_tier,phala_brief,classical_citation FROM bg_transit_moorti ORDER BY nakshatra_offset')
            if canonical(cur.fetchall()) != canonical(payload.sources['moorti_rows']):
                raise ValueError('moorti source authority changed')
        if payload.family == 'kota_chakra':
            cur.execute('LOCK TABLE bg_kota_chakra_rings IN SHARE MODE')
            cur.execute('SELECT ring_position,ring_name,table_version,citation FROM bg_kota_chakra_rings '
                        'WHERE table_version=(SELECT MAX(table_version) FROM bg_kota_chakra_rings) ORDER BY ring_position,ring_name')
            if canonical(cur.fetchall()) != canonical(payload.sources['ring_rows']):
                raise ValueError('kota source authority changed')
        grain = f'ka_{payload.family}:{pctx.convention.ayanamsha_id}'
        cur.execute('SELECT input_vector FROM kala_layer_candidate_grain WHERE chart_id=%s AND generation=%s AND grain_key=%s',
                    (chart,generation,grain))
        previous = cur.fetchone()
        if previous and previous['input_vector'] != payload.upstream_fingerprint['digest']:
            raise ValueError('stale input vector; new candidate required')
    if ctx.dry_run:
        return 0
    body = payload.content()
    body['schema'] = 'ka_contested_payload/1'
    row = {'chart_id':chart,'generation':generation,'ayanamsha_id':pctx.convention.ayanamsha_id,
           'family':payload.family,'natal_build_id':pctx.natal_build_id,
           'method_qualification':payload.method_qualification,'operator_role':payload.operator_role,
           'coverage':Jsonb(payload.coverage),'upstream_fingerprint':Jsonb(payload.upstream_fingerprint),
           'payload':Jsonb(body),'null_reason':payload.null_reason,'formula_version':payload.formula_version}
    replace_candidate_partition(conn,'kala_'+payload.family+'_candidate',chart,generation,('ayanamsha_id',pctx.convention.ayanamsha_id),[row])
    with conn.cursor(row_factory=tuple_row) as cur:
        attest_grain(cur,candidate,grain_key=grain,result_state='rows' if payload.entries else 'zero_rows',
                     input_vector=payload.upstream_fingerprint['digest'])
    return len(payload.entries)
