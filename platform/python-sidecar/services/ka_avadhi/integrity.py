"""Read-only K-AVADHI-C candidate proof, awaiting canonical evidence/admission.

This is deliberately NOT installed as asset_registry.integrity_check_sql.
Callers supply the dispatched chart/build, never a latest-generation heuristic.
Only the lord-condition grounding and retained 1341 candidate obligations are
measured. Legacy health, prose fidelity and full layer acceptance are not earned
by this result. No transactions, rows, publication state or telemetry are changed.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json

import psycopg.rows

from brahmagyan.graha_vocabulary import norm_graha
from services.gochara_kernel.dasha_read import dasha_query, execute_governed_dasha_query
from services.kala_core.vocab import LordKind, NullReason, YOGINI_GRAHA, period_lord


@dataclass(frozen=True)
class CandidateInspection:
    passed: bool
    generation: str | None
    rows_checked: int
    issues: tuple[str, ...]
    # This is the retained authorization boundary, not a legacy health detector.
    certification_hold: bool = True
    warning: str = ('Candidate validation does not repair legacy rows; retain the '
                    'legacy detector, certification HOLD and served warning.')


def _read(conn, sql, params):
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _inherited_value(fact):
    for column in ('fact_value_text', 'fact_value_num', 'fact_value_jsonb'):
        value = fact[column]
        if value is not None:
            return float(value) if isinstance(value, Decimal) else value
    return None


def _typed(value, fact_ids=(), reason=NullReason.MISSING_FACT):
    return {'value': value, 'null_reason': None if value is not None else str(reason),
            'fact_ids': list(fact_ids)}


def _expected_condition(row, facts):
    """Inherit the pinned L1 values. Do not compute or guess missing inputs.

    Mirrors the admitted field selection in ka_avadhi._condition; identity
    adapters come from the shared vocabulary, including sign/Yogini lords.
    """
    lord = period_lord(row['system_id'], row['lord_graha'])
    if lord.kind is LordKind.SIGN:
        return _typed(None, reason=NullReason.METHOD_INAPPLICABLE), []
    graha = YOGINI_GRAHA[lord.value] if lord.kind is LordKind.YOGINI else lord.value
    subject = norm_graha(graha)
    values, refs = {}, []
    for fact in facts:
        category, key = fact['fact_category'], fact['fact_key']
        position = (category == 'graha_position' and fact['fact_subject'] == subject
                    and key in {'sign', 'nakshatra', 'sign_lord', 'nakshatra_lord',
                                'house_d1', 'combustion_state', 'retrograde_flag', 'longitude_sidereal'})
        dignity = (category == 'graha_dignity_per_varga' and fact['fact_subject'] == 'D1_' + subject
                   and key == 'dignity_state' and isinstance(fact['fact_value_jsonb'], dict)
                   and fact['fact_value_jsonb'].get('varga') == 'D1')
        if not (position or dignity):
            continue
        if key in values:
            raise ValueError('ambiguous pinned lord fact')
        identity, value = str(fact['fact_id']), _inherited_value(fact)
        values[key] = _typed(value, (identity,))
        refs.append({'fact_id': identity, 'fact_subject': fact['fact_subject'],
                     'fact_key': key, 'role': key, 'value': value})
    return _typed(values or None, [ref['fact_id'] for ref in refs]), refs


def _spine_matches(row, period, f2, natal):
    return (row['quality'] is None
            and str(row['source_dasha_build_id']) == f2['build_id']
            and str(row['source_natal_build_id']) == natal['build_id']
            and row['ayanamsha_id'] == f2['ayanamsha_id'] == natal['ayanamsha_id']
            and row['tier'] == f2['tier']
            and all(row[a] == period[d] for a, d in (
                ('system_id', 'system_id'), ('level_n', 'level_n'), ('lord_graha', 'lord_graha'),
                ('period_start', 'start_date'), ('period_end', 'end_date'),
                ('period_start_iso', 'start_iso'), ('period_end_iso', 'end_iso'))))


def inspect_candidate(conn, chart_id: str, build_id: str) -> CandidateInspection:
    """Inspect one explicitly dispatched candidate; return no global/legacy PASS.

    Caller owns the connection and snapshot. For concurrent/executor inspection,
    use a caller-owned stable snapshot; this helper never changes isolation or
    acquires a writer lease. SQL errors propagate rather than becoming green.
    """
    candidates = _read(conn, '''SELECT generation,state,conventions FROM kala_layer_candidate
        WHERE chart_id=%s AND build_id=%s''', (chart_id, build_id))
    if len(candidates) != 1:
        return CandidateInspection(False, None, 0, ('dispatched_candidate_missing_or_ambiguous',))
    candidate = candidates[0]
    gen = candidate['generation']
    if gen == 'legacy' or candidate['state'] != 'building' or _read(conn,
            'SELECT generation FROM kala_layer_head WHERE chart_id=%s AND generation=%s', (chart_id, gen)):
        return CandidateInspection(False, gen, 0, ('candidate_not_mutable_build',))
    pins = candidate['conventions']
    try:
        f2, natal = pins['f2'], pins['natal']
        required = (f2['build_id'], f2['ayanamsha_id'], f2['tier'], f2['systems'],
                    natal['build_id'], natal['ayanamsha_id'], natal['tier'])
        if not all(required) or not isinstance(f2['systems'], list) or f2['ayanamsha_id'] != natal['ayanamsha_id']:
            raise ValueError('incomplete or mixed pins')
    except (KeyError, TypeError, ValueError):
        return CandidateInspection(False, gen, 0, ('invalid_candidate_pins',))
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        execute_governed_dasha_query(
            conn, chart_id, dasha_query('avadhi_integrity_periods'),
            (chart_id, f2['build_id'], f2['ayanamsha_id'], f2['tier'], f2['systems']),
            ayanamsha_id=f2['ayanamsha_id'], cursor=cur, clock_tier=f2['tier'])
        periods = cur.fetchall()
    facts = _read(conn, '''SELECT * FROM chart_facts WHERE chart_id=%s AND build_id=%s
        AND ayanamsha_id=%s AND verification_pass_status=%s
        ORDER BY fact_subject,fact_category,fact_key,fact_id''',
        (chart_id, natal['build_id'], natal['ayanamsha_id'], natal['tier']))
    rows = _read(conn, '''SELECT * FROM kala_avadhi WHERE chart_id=%s AND generation=%s
        ORDER BY system_id,level_n,period_start_iso,avadhi_id''', (chart_id, gen))
    mechanisms = _read(conn, '''SELECT mechanism_id,conclusion_state_jsonb FROM kala_activation_predicates
        WHERE chart_id=%s AND generation=%s AND ayanamsha_id=%s''', (chart_id, gen, f2['ayanamsha_id']))
    source = {str(p['dasha_row_id']): p for p in periods}
    issues = []
    if (not periods or {p['system_id'] for p in periods} != set(f2['systems'])
            or len(source) != len(periods)
            or len(rows) != len(periods)
            or {str(r['source_dasha_row_id']) for r in rows} != set(source)):
        issues.append('pinned_period_coverage_mismatch')
    for row in rows:
        identity = str(row['source_dasha_row_id'])
        period = source.get(identity)
        if period is None or not _spine_matches(row, period, f2, natal):
            issues.append(f'{identity}:period_or_pin_mismatch')
            continue
        dossier = row['dossier']
        try:
            expected, refs = _expected_condition(row, facts)
            # Exact ids, subject, key, role AND value: a real but unrelated fact
            # cannot satisfy grounding. Missing facts must be independently absent.
            # Python equality treats True == 1; JSON values must preserve type.
            if (json.dumps(dossier['lord_condition'], sort_keys=True) != json.dumps(expected, sort_keys=True)
                    or json.dumps(dossier['lord_condition_fact_refs'], sort_keys=True) != json.dumps(refs, sort_keys=True)):
                issues.append(f'{identity}:lord_grounding_mismatch')
            attached = dossier['attached_mechanisms']
            if not isinstance(attached, list):
                raise ValueError('mechanism array absent')
            for m in attached:
                if not any(p['mechanism_id'] == m['mechanism_id']
                           and p['conclusion_state_jsonb'].get('effective_state') is not None
                           and p['conclusion_state_jsonb']['effective_state'] == m['effective_state']
                           for p in mechanisms):
                    issues.append(f'{identity}:mechanism_state_mismatch')
        except (KeyError, TypeError, ValueError):
            issues.append(f'{identity}:invalid_grounding_payload')
    return CandidateInspection(not issues, gen, len(rows), tuple(issues))
