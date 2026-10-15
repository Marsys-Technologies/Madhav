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
