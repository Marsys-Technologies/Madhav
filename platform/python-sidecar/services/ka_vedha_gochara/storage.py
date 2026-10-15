"""Candidate-only persistence on the orchestrator transaction; never publishes."""
from types import SimpleNamespace

from psycopg.rows import dict_row, tuple_row
from psycopg.types.json import Jsonb

from services.kala_core.idempotency import replace_candidate_partition
from services.kala_core.manifest import Candidate, candidate_generation, lock_candidate_inputs, attest_grain
from services.ka_vedha_gochara.candidate import KINDS, VedhaPayload, canonical


def replace_candidate(ctx, payload: VedhaPayload):
    if not isinstance(payload,VedhaPayload) or len(payload.headers)!=3:
        raise ValueError('three typed family headers required')
    conn=ctx.db_conn
    chart=str(ctx.config['chart_id'])
    with conn.cursor(row_factory=tuple_row) as cur:
        generation=candidate_generation(SimpleNamespace(db_conn=cur,build_id=ctx.build_id))
        if generation in ('legacy','current','published','retained'):
            raise ValueError('mutable new candidate required')
        candidate=Candidate(chart,generation,str(ctx.build_id),None)
        lock_candidate_inputs(cur,candidate)
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute('SELECT * FROM kala_layer_candidate WHERE chart_id=%s AND generation=%s AND build_id=%s FOR UPDATE',
                    (chart,generation,str(ctx.build_id)))
        c=cur.fetchone()
        if c is None or c['state']!='building':
            raise ValueError('mutable building candidate bound to chart/build required')
        cur.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s FOR SHARE',(chart,))
        if any(row['generation']==generation for row in cur.fetchall()):
            raise ValueError('published candidate is immutable')
        cur.execute('SELECT chart_id FROM build_runs WHERE id=%s',(str(ctx.build_id),))
        build=cur.fetchone()
        if build is None or str(build['chart_id'])!=chart:
            raise ValueError('candidate build belongs to another chart')
        pin=(c['conventions'] or {}).get('natal',{})
        if not pin.get('build_id') or not pin.get('ayanamsha_id'):
            raise ValueError('candidate natal build/ayanamsha pin required')
        cur.execute('LOCK TABLE chart_facts IN SHARE MODE')
        cur.execute('SELECT fact_id,fact_value_num FROM chart_facts WHERE chart_id=%s AND build_id=%s AND ayanamsha_id=%s '
                    "AND fact_category='graha_position' AND fact_subject='MOON' AND fact_key='longitude_sidereal' ORDER BY fact_id",
                    (chart,pin['build_id'],pin['ayanamsha_id']))
        facts=cur.fetchall()
        if len(facts)>1:
            raise ValueError('contradictory natal Moon facts')
        fact=None if not facts else facts[0]
        if canonical(fact)!=canonical(payload.janma_fact):
            # Decimal DB numbers and Python floats compare numerically below.
            if fact is None or payload.janma_fact is None or fact['fact_id']!=payload.janma_fact['fact_id'] or float(fact['fact_value_num'])!=float(payload.janma_fact['fact_value_num']):
                raise ValueError('candidate natal fact changed or belongs to another build')
        # Pin the authoritative read set through transaction end, including
        # honestly empty source sets; candidate source drift cannot race DELETE.
        cur.execute('LOCK TABLE chart_facts,bg_transit_rules,bg_phaladeepika_latta,classical_text_chunks IN SHARE MODE')
        from services.gochara_rules.vedha_derive import pairs_content_digest
        if not payload.sources:
            raise ValueError('candidate source input ledger required')
        cur.execute('SELECT graha,primary_house,vedha_house,classical_citation,rule_type FROM bg_transit_rules WHERE vedha_house IS NOT NULL')
        db_pairs=cur.fetchall()
        source_pairs=[dict(zip(('graha','primary_house','vedha_house','classical_citation','rule_type'),r))
                      if not isinstance(r,dict) else r for r in payload.sources['pairs_rows']]
        if pairs_content_digest(db_pairs)!=pairs_content_digest(source_pairs):
            raise ValueError('L0 pair authority changed; rebuild candidate source')
        cur.execute('SELECT graha,count_from_graha,direction,source_citation,verse_ref FROM bg_phaladeepika_latta')
        db_latta=cur.fetchall()
        keys=('graha','count_from_graha','direction','source_citation','verse_ref')
        supplied=[{k:r.get(k) for k in keys} for r in payload.sources['latta_rules']]
        if sorted(map(canonical,db_latta))!=sorted(map(canonical,supplied)):
            raise ValueError('L0 latta source changed; rebuild candidate')
        enrichment=payload.sources['enrichment']
        if enrichment.get('passage'):
            cur.execute("SELECT content_en FROM classical_text_chunks WHERE chunk_id=%s AND text_id='phaladeepika' "
                        'AND chapter=26 AND verse_start<=47 AND verse_end>=48', (enrichment['locator'],))
            passages=cur.fetchall()
            if len(passages)!=1 or passages[0]['content_en']!=enrichment['passage']:
                raise ValueError('enrichment passage is not the verbatim cited source')
        headers=list(payload.headers)
        if {h['vedha_kind'] for h in headers}!=set(KINDS):
            raise ValueError('all three family headers required')
        for row in [*headers,*payload.intervals]:
            if str(row['chart_id'])!=chart or row['generation']!=generation or row['ayanamsha_id']!=pin['ayanamsha_id']:
                raise ValueError('row outside candidate chart/generation/ayanamsha')
        for h in headers:
            if str(h['natal_build_id'])!=pin['build_id'] or h['janma_reference_fact_id']!=(fact['fact_id'] if fact else '[EXTERNAL_COMPUTATION_REQUIRED]'):
                raise ValueError('header natal pin mismatch')
            grain=f"ka_vedha_gochara:{pin['ayanamsha_id']}:{h['vedha_kind']}"
            cur.execute('SELECT input_vector FROM kala_layer_candidate_grain WHERE chart_id=%s AND generation=%s AND grain_key=%s',
                        (chart,generation,grain))
            previous=cur.fetchone()
            if previous and previous['input_vector']!=h['upstream_fingerprint']['digest']:
                raise ValueError('stale input vector; new candidate required')
    if ctx.dry_run:
        return 0
    # Everything above (including lifecycle and source pins) precedes deletion.
    # The orchestrator owns rollback if insertion or a DB constraint fails.
    def adapted(rows):
        return [{k:Jsonb(v) if k in ('coverage','upstream_fingerprint','payload','detail') else v
                 for k,v in row.items()} for row in rows]
    grain=('ayanamsha_id',pin['ayanamsha_id'])
    replace_candidate_partition(conn,'kala_vedha_gochara_interval',chart,generation,grain,[])
    replace_candidate_partition(conn,'kala_vedha_gochara_candidate',chart,generation,grain,adapted(headers))
    count=replace_candidate_partition(conn,'kala_vedha_gochara_interval',chart,generation,grain,adapted(payload.intervals))
    with conn.cursor(row_factory=tuple_row) as cur:
        for h in headers:
            has_rows=any(r['vedha_kind']==h['vedha_kind'] for r in payload.intervals)
            attest_grain(cur,candidate,grain_key=f"ka_vedha_gochara:{pin['ayanamsha_id']}:{h['vedha_kind']}",
                         result_state='rows' if has_rows else 'zero_rows', input_vector=h['upstream_fingerprint']['digest'])
    return count
