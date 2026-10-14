"""Compare-and-switch authority primitives for the governed executor.

The caller owns the transaction and its commit. No generation data is deleted or
withdrawn: rollback restores the retained previous head explicitly. These functions
are preparation, not authority to dispatch or enable an executor operation.
"""
from __future__ import annotations
import re

_GOVERNED = re.compile(r'([5-9]|[1-9][0-9]+)\.[0-9]+\Z')


class AuthorityRefused(ValueError):
    pass


def _row(result):
    row = result.fetchone()
    return tuple(row.values()) if isinstance(row, dict) else row


def _switch(conn, chart_id, generation, expected_head, evidence_ref, operator):
    if not generation or not expected_head or not evidence_ref.strip() or not operator.strip():
        raise AuthorityRefused('operation_evidence_missing: target, expected head, operator and evidence are required')
    conn.execute('SELECT public.ka_gochara_lock_chart(%s::uuid)', (chart_id,))
    current = _row(conn.execute('SELECT authoritative_generation FROM public.kala_gochara_authority'
                               ' WHERE chart_id = %s ORDER BY chart_id LIMIT 1 FOR UPDATE', (chart_id,)))
    if current is None or current[0] != expected_head:
        raise AuthorityRefused('head_changed: authority differs from the pre-acceptance receipt')
    # Pre-ledger legacy heads (notably 3.0) have no publication manifest.
    # The retained head is explicit in the flip receipt; never guess a fallback.
    if _GOVERNED.fullmatch(generation):
        target = _row(conn.execute(
            "SELECT p.status, (p.input_generation_vector ->> 'stored_scope' = 'test_slice'"
            " OR p.input_generation_vector ? 'test_slice') AS test_slice,"
            " EXISTS (SELECT 1 FROM public.ka_gochara_generation_seal s WHERE s.chart_id = p.chart_id"
            " AND s.generation = p.generation AND s.manifest_id = p.manifest_id) AS sealed"
            " FROM public.kala_gochara_publication p WHERE p.chart_id = %s AND p.generation = %s"
            " ORDER BY p.manifest_id LIMIT 1", (chart_id, generation)))
        if target is None or target[0] != 'published' or target[1] or not target[2]:
            raise AuthorityRefused('target_not_servable: require published, non-test-slice and a matching governed seal')
    changed = _row(conn.execute(
        'UPDATE public.kala_gochara_authority SET authoritative_generation = %s, flipped_at = now(),'
        ' flipped_by = %s, evidence_ref = %s WHERE chart_id = %s AND authoritative_generation = %s'
        ' RETURNING authoritative_generation', (generation, operator, evidence_ref, chart_id, expected_head)))
    if changed is None or changed[0] != generation:
        raise AuthorityRefused('head_changed: compare-and-switch did not change the expected row')
    return {'chart_id': str(chart_id), 'previous_head': expected_head, 'head': generation, 'evidence_ref': evidence_ref}


def publish_head(conn, chart_id, *, generation, expected_head, evidence_ref, operator):
    if not _GOVERNED.fullmatch(generation):
        raise AuthorityRefused('target_not_governed: publish_head requires a governed generation')
    return _switch(conn, chart_id, generation, expected_head, evidence_ref, operator)


def rollback_head(conn, chart_id, *, generation, expected_head, evidence_ref, operator):
    return _switch(conn, chart_id, generation, expected_head, evidence_ref, operator)
