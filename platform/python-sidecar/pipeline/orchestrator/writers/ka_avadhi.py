"""K1-2: candidate period dossiers over pinned F2, L1 facts and F1.

The orchestrator owns transactions. Published/legacy rows remain untouched.
No domains, scores, quality labels or rule conclusions are invented here.
"""
from __future__ import annotations

from dataclasses import asdict
from bisect import bisect_right
from datetime import timezone
from decimal import Decimal
import json

import psycopg.rows
from psycopg.types.json import Jsonb

from brahmagyan.graha_vocabulary import norm_graha
from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.kala_core import clocks, sky
from services.kala_core.idempotency import replace_candidate_partition
from services.kala_core.vocab import LordKind, NullReason, YOGINI_GRAHA, period_lord

FORMULA_VERSION = 'K1-2/ALGO3.2/v1'

_PERIOD_SQL = """
SELECT dasha_row_id, system_id, level_n, lord_graha, parent_row_id,
       start_iso, end_iso, start_date, end_date, lord_to_parent_relationship,
       build_id, ayanamsha_id, verification_pass_status, applies_to_this_chart_flag,
       is_truncated_at_window_start, is_truncated_at_window_end
FROM chart_dashas
WHERE chart_id=%s AND build_id=%s AND ayanamsha_id=%s
  AND verification_pass_status=%s AND system_id=ANY(%s) AND level_n BETWEEN 1 AND 4
ORDER BY system_id, level_n, start_iso, dasha_row_id
"""
# Keep the measured M4 category/subject contract; no phantom key or silent cap.
_FETCH_FACT_REFS_SQL = """
SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_text,
       fact_value_num, fact_value_jsonb, citation_ref
FROM chart_facts
WHERE chart_id=%s AND build_id=%s AND ayanamsha_id=%s AND verification_pass_status=%s
  AND (fact_category='graha_position' AND fact_key IN
       ('sign','nakshatra','sign_lord','nakshatra_lord','house_d1',
        'combustion_state','retrograde_flag','longitude_sidereal')
       OR fact_category='graha_dignity_per_varga' AND fact_key='dignity_state'
          AND fact_value_jsonb->>'varga'='D1'
       OR fact_category='panchadha_maitri' AND fact_key='compound_relation')
ORDER BY fact_subject, fact_category, fact_key, fact_id
"""
_MECHANISM_SQL = """
SELECT mechanism_id, mechanism_route, derivation_ledger_jsonb, conclusion_state_jsonb
FROM kala_activation_predicates
WHERE chart_id=%s AND generation=%s AND ayanamsha_id=%s AND mechanism_id IS NOT NULL
ORDER BY mechanism_id, event_class_id NULLS FIRST, id
"""


def typed(value=None, reason=NullReason.MISSING_FACT, fact_ids=()):
    return {'value': value, 'null_reason': None if value is not None else str(reason),
            'fact_ids': list(fact_ids)}


def validate_dossier(value):
    """Reject scoring/quality mutants recursively, including copied payloads."""
    if isinstance(value, dict):
        if 'value' in value and 'null_reason' in value:
            if value['value'] is None and value['null_reason'] not in {r.value for r in NullReason}:
                raise ValueError('an undeterminable field requires a typed null reason')
            if value['value'] is not None and value['null_reason'] is not None:
                raise ValueError('a determined field cannot carry a null reason')
        for key, child in value.items():
            if 'score' in key.lower() or 'weight' in key.lower() or key in {'quality', 'quality_label'}:
                raise ValueError(f'period dossier cannot carry {key}')
            validate_dossier(child)
    elif isinstance(value, (list, tuple)):
        for child in value: validate_dossier(child)


def _graha(period):
    lord = period_lord(period['system_id'], period['lord_graha'])
    if lord.kind is LordKind.SIGN: return None
    return YOGINI_GRAHA[lord.value].value if lord.kind is LordKind.YOGINI else lord.value.value


def _value(fact):
    value = fact.get('fact_value_text')
    if value is None: value = fact.get('fact_value_num')
    if value is None: value = fact.get('fact_value_jsonb')
    return float(value) if isinstance(value, Decimal) else value


def _condition(graha, facts):
    if graha is None: return typed(reason=NullReason.METHOD_INAPPLICABLE), []
    subject = norm_graha(graha)
    selected = [f for f in facts if (
        f['fact_category'] == 'graha_position' and f['fact_subject'] == subject or
        f['fact_category'] == 'graha_dignity_per_varga' and f['fact_subject'] == 'D1_' + subject)]
    values, refs = {}, []
    for f in selected:
        key = f['fact_key']
        if key in values: raise ValueError(f'ambiguous pinned natal condition: {subject}/{key}')
        values[key] = typed(_value(f), fact_ids=(str(f['fact_id']),))
        refs.append({'fact_id': str(f['fact_id']), 'fact_subject': f['fact_subject'],
                     'fact_key': key, 'role': key, 'value': _value(f)})
    return (typed(values, fact_ids=[f['fact_id'] for f in refs]) if values else typed()), refs


def _lagna_relation(graha, facts):
    if not graha: return typed(reason=NullReason.METHOD_INAPPLICABLE)
    lords = [f for f in facts if f['fact_category'] == 'graha_position'
             and f['fact_subject'] == 'LAGNA' and f['fact_key'] == 'sign_lord']
    if len(lords) != 1 or _value(lords[0]) is None:
        return typed()
    subject = f"MAITRI_{norm_graha(graha)}_{norm_graha(_value(lords[0]))}"
    relations = [f for f in facts if f['fact_category'] == 'panchadha_maitri'
                 and f['fact_subject'] == subject and f['fact_key'] == 'compound_relation']
    if len(relations) != 1: return typed()
    return typed(_value(relations[0]), fact_ids=(lords[0]['fact_id'], relations[0]['fact_id']))


def build_dossier(period, facts, mechanisms, context, commencement):
    """Project only the period lord's inputs; this is not an evaluator."""
    graha = _graha(period)
    condition, refs = _condition(graha, facts)
    values = condition['value'] or {}
    house = values.get('house_d1', typed())
    # The placement is the L1 house, not an invented auspiciousness class.
    placement = {'house_from_lagna': house,
                 'class': typed(reason=NullReason.INFORMATION_UNAVAILABLE),
                 'relation_to_lagna_lord': _lagna_relation(graha, facts)}
    parent = context.lords.get('MD') if period['level_n'] == 2 else None
    parent_condition, _ = _condition(_graha(dict(period, lord_graha=parent)), facts) if parent else (typed(), [])
    parent_house = (parent_condition['value'] or {}).get('house_d1', typed())
    relative = typed()
    if parent and house['value'] is not None and parent_house['value'] is not None:
        relative = typed((int(house['value']) - int(parent_house['value'])) % 12 + 1,
                         fact_ids=house['fact_ids'] + parent_house['fact_ids'])
    motion, longitude = values.get('retrograde_flag', typed()), values.get('longitude_sidereal', typed())
    phase = typed()
    if longitude['value'] is not None and motion['value'] in ('direct', 'retrograde'):
        third = int(float(longitude['value']) % 30 / 10)
        retrograde = motion['value'] == 'retrograde'
        phase = typed({'third': 3 - third if retrograde else third + 1,
                       'interpretation': 'equal_thirds', 'source': 'BPHS 47.3-4'},
                      fact_ids=longitude['fact_ids'] + motion['fact_ids'])
    elif motion['value'] == 'stationary':
        phase = typed(reason=NullReason.INFORMATION_UNAVAILABLE,
                      fact_ids=longitude['fact_ids'] + motion['fact_ids'])
    onset = typed(reason=commencement.null_reason or NullReason.INFORMATION_UNAVAILABLE)
    if graha and commencement.available:
        answer = commencement.values[0]
        position = answer.position(graha)
        onset = typed({'instant': period['start_iso'].isoformat(), 'jd': answer.jd,
                       'position': asdict(position), 'backend': answer.backend,
                       'convention_id': answer.convention_id}, fact_ids=(str(period['dasha_row_id']),))
    elif not graha: onset = typed(reason=NullReason.METHOD_INAPPLICABLE)
    attached = []
    for m in mechanisms:
        ledger, state = m['derivation_ledger_jsonb'], m['conclusion_state_jsonb']
        participants = {norm_graha(p) for p in ledger.get('constituent_planets', [])}
        # A grounding/context fact does not by itself confer a participant role.
        if graha is None or norm_graha(graha) not in participants:
            continue
        attached.append({'mechanism_id': m['mechanism_id'], 'route': m['mechanism_route'],
                         'effective_state': state['effective_state'], 'qualification': state.get('qualification'),
                         'roles': ledger.get('graph_edges', []), 'defeats': state.get('defeats', []),
                         'excepts': state.get('excepts', []), 'source': ledger['source'],
                         'rule_version': ledger.get('rule_version'), 'fact_ids': ledger.get('fact_ids', [])})
    result = {'lord_condition': condition, 'lord_condition_fact_refs': refs,
              'placement': placement, 'ad_placement_from_md': relative,
              'ad_relation_to_md': typed(period.get('lord_to_parent_relationship'),
                                         fact_ids=(str(period['dasha_row_id']),)) if parent else typed(reason=NullReason.METHOD_INAPPLICABLE),
              'sublord_modulation': {'graha': parent, 'note': f"AD lord {period['lord_graha']} modulates MD lord {parent}."} if parent else None,
              'commencement_condition': onset, 'commencement_coverage': asdict(commencement.coverage),
              'fruition_phase': phase, 'attached_mechanisms': attached,
              'attachment_evaluation': typed('evaluated' if mechanisms else None,
                                             reason=NullReason.INFORMATION_UNAVAILABLE),
              'applicability': asdict(context.applicability_detail),
              'sigma_boundary': typed(context.sigma_boundary.total_seconds() if context.sigma_boundary is not None else None,
                                      reason=NullReason.INFORMATION_UNAVAILABLE),
              'scenario': typed(context.scenario_id, reason=NullReason.INFORMATION_UNAVAILABLE),
              'evaluated_rule_conclusions': typed(reason=NullReason.INFORMATION_UNAVAILABLE)}
    validate_dossier(result)
    return result


def _read(conn, query, params):
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute(query, params)
        return cur.fetchall()


class PinnedClockIndex:
    """One validated SQL read; F2 receives the active MD–SD slice in O(log n).

    The clock API still owns applicability, parent-lineage checks and σ.
    Sibling overlap is invalid in one pinned F2 build and fails closed before
    a bisect can hide it. No period or boundary is constructed by this adapter.
    """
    def __init__(self, periods, chart, pin):
        self.chart, self.pin, self.groups = chart, pin, {}
        for row in periods:
            if row['end_iso'] <= row['start_iso']:
                raise clocks.ClockUnavailable('non-positive F2 period')
            self.groups.setdefault((row['system_id'], row['level_n']), []).append(row)
        self.starts = {}
        for key, group in self.groups.items():
            group.sort(key=lambda row: (row['start_iso'], str(row['dasha_row_id'])))
            if any(a['end_iso'] > b['start_iso'] for a, b in zip(group, group[1:])):
                raise clocks.ClockUnavailable('overlapping pinned F2 periods')
            self.starts[key] = [row['start_iso'] for row in group]

    def at(self, instant, system):
        active = []
        for level in range(1, 5):
            key = (system, level)
            index = bisect_right(self.starts.get(key, []), instant) - 1
            if index >= 0:
                row = self.groups[key][index]
                if instant < row['end_iso']: active.append(row)
        owner = self
        class Slice:
            def execute(self, query, params):
                expected = [owner.chart, system, owner.pin['build_id'],
                            owner.pin['ayanamsha_id'], owner.pin['tier']]
                if list(params) != expected:
                    raise ValueError('cached F2 slice cannot answer another pin')
                return self
            def fetchall(self): return active
        return Slice()


@register('ka_avadhi')
class KaAvdhiWriter(WriterBase):
    asset_id = 'ka_avadhi'

    def run(self, ctx):
        if ctx.dry_run: return WriterResult(self.asset_id, 0, notes='dry_run=True')
        chart = ctx.config['chart_id']
        if not getattr(ctx, 'build_id', None):
            return WriterResult(self.asset_id, 0, notes='no build-bound candidate; published rows preserved')
        conn = ctx.db_conn
        candidates = _read(conn, '''SELECT generation, state, conventions FROM kala_layer_candidate
            WHERE chart_id=%s AND build_id=%s FOR SHARE''', (chart, str(ctx.build_id)))
        if not candidates:
            return WriterResult(self.asset_id, 0, notes='no build-bound candidate; published rows preserved')
        candidate = candidates[0]; gen = candidate['generation']
        if candidate['state'] != 'building' or gen == 'legacy':
            raise ValueError('Avadhi requires a building candidate')
        if _read(conn, 'SELECT generation FROM kala_layer_head WHERE chart_id=%s AND generation=%s FOR SHARE', (chart, gen)):
            raise ValueError('Avadhi cannot replace a published head')
        pins = candidate['conventions']
        f2, natal = pins['f2'], pins['natal']
        if f2['ayanamsha_id'] != natal['ayanamsha_id']:
            raise ValueError('F2 and natal conventions must agree')
        periods = _read(conn, _PERIOD_SQL, (chart, f2['build_id'], f2['ayanamsha_id'], f2['tier'], f2['systems']))
        facts = _read(conn, _FETCH_FACT_REFS_SQL, (chart, natal['build_id'], natal['ayanamsha_id'], natal['tier']))
        mechanisms = _read(conn, _MECHANISM_SQL, (chart, gen, f2['ayanamsha_id']))
        uncertainty = clocks.BoundaryUncertainty(**f2['uncertainty']) if f2.get('uncertainty') else None
        convention = sky.SkyConvention(f2['ayanamsha_id'], pins['node_model'])
        cache = sky.EphemerisCache()
        index = PinnedClockIndex(periods, chart, f2)
        rows = []
        # F2 itself validates the hierarchy and computes only its admitted σ.
        for period in periods:
            context = clocks.period_context(index.at(period['start_iso'], period['system_id']),
                chart, period['start_iso'], period['system_id'], build_id=f2['build_id'],
                ayanamsha_id=f2['ayanamsha_id'], tier=f2['tier'],
                uncertainty=uncertainty, scenario_id=f2.get('scenario_id'))
            graha = _graha(period)
            # Exact UTC instant conversion; all geometry stays behind sky's door.
            at = period['start_iso'].astimezone(timezone.utc)
            jd = at.timestamp() / 86400 + 2440587.5
            commencement = sky.ephemeris_at(jd, convention, bodies=(graha,) if graha else (), cache=cache)
            dossier = build_dossier(period, facts, mechanisms, context, commencement)
            rows.append(dict(chart_id=chart, generation=gen, system_id=period['system_id'],
                level_n=period['level_n'], lord_graha=period['lord_graha'],
                period_start=period['start_date'], period_end=period['end_date'],
                period_start_iso=period['start_iso'], period_end_iso=period['end_iso'],
                source_dasha_row_id=period['dasha_row_id'], source_dasha_build_id=f2['build_id'],
                source_natal_build_id=natal['build_id'], ayanamsha_id=f2['ayanamsha_id'], tier=f2['tier'],
                dossier=Jsonb(dossier), quality=None,
                citations=list(clocks.dasha_method(period['system_id']).sources) + ['BPHS 47.3-6; 52.11-14'],
                formula_version=FORMULA_VERSION))
        count = replace_candidate_partition(conn, 'kala_avadhi', chart, gen, None, rows)
        return WriterResult(self.asset_id, count, notes=f'candidate={gen}; pinned F2/F1/L1 dossiers')
