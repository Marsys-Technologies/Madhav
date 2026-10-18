"""Explicit candidate read through KA-3b's sole testimony boundary.

No head resolution, scoring, method promotion or astronomy occurs here. Decode
and validate the producer's stored fingerprint before handing entries to a
consumer that needs the full interval set (for example Kṣetra's breakpoints).
"""
from psycopg import sql
from psycopg.rows import dict_row

from services.kala_core.sky import SkyConvention
from services.kala_core.vocab import MethodQualification, OperatorRole
from .contested import AdapterContext, AdapterPayload, FAMILIES


def load_candidate_payload(conn, *, chart_id, generation, ayanamsha_id, family):
    if family not in FAMILIES:
        raise ValueError('unknown contested adapter family')
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql.SQL('SELECT payload,upstream_fingerprint FROM {} '
                           'WHERE chart_id=%s AND generation=%s AND ayanamsha_id=%s').format(
            sql.Identifier('kala_'+family+'_candidate')), (chart_id,generation,ayanamsha_id))
        row=cur.fetchone()
    if row is None:
        return None
    body=row['payload']; context=body['context']
    ctx=AdapterContext(context['chart_id'],context['generation'],context['natal_build_id'],
                       SkyConvention(**context['convention']),tuple(context['facts']))
    if (ctx.chart_id != str(chart_id) or ctx.generation != generation
            or ctx.convention.ayanamsha_id != ayanamsha_id):
        raise ValueError('stored adapter does not match candidate/convention')
    payload=AdapterPayload(body['family'],ctx,body['coverage'],tuple(body['entries']),body['sources'],
        tuple(body['external_computation_required']),body['null_reason'],
        MethodQualification(body['method_qualification']),OperatorRole(body['operator_role']),
        row['upstream_fingerprint'],body['formula_version'])
    if payload.family != family:
        raise ValueError('stored adapter family mismatch')
    return payload.validate()


def load_sudarshana_method(conn, *, chart_id, generation, ayanamsha_id, year, evidence):
    """Explicit, read-only J7 candidate evaluation; never resolve a served head.

    F1 evidence is a caller-supplied snapshot, pinned by the method to this
    adapter's natal build/convention and the period's commencement. This does
    not persist conclusions in KA-3b's deliberately conclusion-free table.
    """
    from services.ka_sudarshana_varsha.method import evaluate_candidate

    payload = load_candidate_payload(conn, chart_id=chart_id, generation=generation,
                                     ayanamsha_id=ayanamsha_id, family='sudarshana_varsha')
    if payload is None:
        return None
    result = evaluate_candidate(payload, year=year, evidence=evidence)
    # F1 owns its derived assessments. Its cited L1 operands must nevertheless
    # resolve in this exact chart/build/ayanamsha, including operands that did
    # not win an occupancy/aspect/strength branch of the method.
    refs = sorted({str(ref) for h in evidence.houses
                   for i in (*h.occupants, *h.aspects, *((h.lord,) if h.lord else ()))
                   for ref in (*i.nature.fact_ids, *i.strength.fact_ids)})
    if refs:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute('SELECT fact_id FROM chart_facts WHERE fact_id=ANY(%s) '
                        'AND chart_id=%s AND build_id=%s AND ayanamsha_id=%s',
                        (refs, chart_id, payload.context.natal_build_id, ayanamsha_id))
            if {str(r['fact_id']) for r in cur.fetchall()} != set(refs):
                raise ValueError('F1 L1 reference missing or outside candidate natal pin')
    return result
