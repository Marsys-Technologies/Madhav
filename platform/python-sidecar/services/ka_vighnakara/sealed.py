"""K3-2: deterministic interpretation of sealed producer records, never astrology.

(I) INTERPRETATION: the executor's TSV transports full JSON rows as
(kind,key,payload). Independent pins/key inventories are cockpit inputs, never
learned from that artifact. Correspondence and licensed F1 edge intervals are
prerequisite exports; absence remains unavailable, not an inferred join.
See PACKET_K3-2_v1 §4/§6 and migration 1155:465-505 / 1081:225-248.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import csv
import hashlib
import io
import json
from pathlib import Path

from brahmagyan.verification_vocab import TWO_PASS_VERIFIED
from services.kala_core.assertion import Interval, Source
from services.kala_core.sky.coverage import SkyCoverage
from services.kala_core.vocab import graha_id, GrahaId
from services.gochara_kernel.substrate import jd_to_utc
from services.ka_vighnakara.model import Protection
from services.gochara_rules.vedha_derive import check_callback_result

VERSION = 'k3-negative-space/2.0.0'
KINDS = ('seal', 'publication', 'verifier', 'record', 'coverage', 'vedha_header',
         'vedha_interval', 'correspondence', 'f1', 'fact')
REMOVED = frozenset({'rikta_tithi', 'daily_gandanta', 'kulika', 'transit_combustion'})
ROSTER = frozenset({'vedha', 'bhava_destruction', 'dusthana_lord_in_own_house',
                    'badhaka_movable_lagna', 'papakartari'})


def stamp(value):
    parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timezone-aware producer instant required')
    return parsed


def span(value):
    if isinstance(value, str):
        if not value.startswith('[') or not value.endswith(')'):
            raise ValueError('finite half-open PostgreSQL range required')
        bounds = next(csv.reader([value[1:-1]]))
        if len(bounds) != 2:
            raise ValueError('malformed PostgreSQL range')
        value = dict(t0=stamp(bounds[0]),t1=stamp(bounds[1]))
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        value = dict(t0=jd_to_utc(value[0]),t1=jd_to_utc(value[1]))
    parsed = Interval.model_validate(value)
    return parsed.t0, parsed.t1


def wire(start, end):
    return {'t0': start.isoformat(), 't1': end.isoformat()}


def contains(outer, inner):
    a, b = span(outer)
    c, d = span(inner)
    return a <= c < d <= b


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def row_key(kind, row):
    """Natural source identity, independent of display labels or row order."""
    if kind == 'correspondence':
        return canonical([row['record_id'],graha_id(row['graha']).value,row['factor'],wire(*span(row['primary_span']))])
    fields = {
        'seal': ('chart_id', 'generation'), 'publication': ('manifest_id',),
        'verifier': ('chart_id', 'generation', 'execution_id'), 'record': ('record_id',),
        'coverage': ('chart_id', 'generation', 'partition_kind', 'partition_key'),
        'vedha_header': ('chart_id', 'generation', 'ayanamsha_id', 'vedha_kind'),
        'vedha_interval': ('chart_id', 'generation', 'ayanamsha_id', 'vedha_kind', 'graha', 't_in'),
        'correspondence': ('record_id',), 'f1': ('id',), 'fact': ('fact_id',),
    }
    if kind not in fields or any(row.get(k) is None for k in fields[kind]):
        raise ValueError('missing source natural key')
    return canonical([str(row[k]) for k in fields[kind]])


def _json(text):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('non-finite JSON input')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def read_export(receipt, expected):
    """Read complete executor output, checking bytes, logical rows AND keys."""
    if receipt.get('status') != 'COMPLETED' or receipt.get('exit_code') != 0:
        raise ValueError('export receipt is not completed')
    body = Path(receipt['output_file']).read_bytes()
    if (len(body) != receipt.get('output_bytes')
            or hashlib.sha256(body).hexdigest() != receipt.get('output_sha256')):
        raise ValueError('export bytes/hash mismatch; a tail is not evidence')
    reader = csv.reader(io.StringIO(body.decode('utf-8'), newline=''), delimiter='\t', strict=True)
    if next(reader, None) != ['kind', 'key', 'payload']:
        raise ValueError('export requires one exact TSV header')
    result = {kind: [] for kind in KINDS}
    keys = {kind: [] for kind in KINDS}
    count = 0
    for row in reader:
        count += 1
        if len(row) != 3:
            raise ValueError('export logical row is malformed')
        kind, key, payload = row
        value = _json(payload)
        if not isinstance(value, dict):
            raise ValueError('source row must be a JSON object')
        if kind == 'pins':
            if key != 'pins' or 'pins' in result or value != expected['pins']:
                raise ValueError('export pins mismatch or duplicated')
            result['pins'] = value
        else:
            if kind not in KINDS or key != row_key(kind, value) or key in keys[kind]:
                raise ValueError('unknown, substituted or duplicate export key')
            keys[kind].append(key)
            result[kind].append(value)
    if 'pins' not in result:
        raise ValueError('export pins absent')
    if count != expected.get('row_count') or {k: sorted(v) for k, v in keys.items()} != expected.get('keys'):
        raise ValueError('export counts/independent keys mismatch')
    return result


def _pin(row, pins, generation=None, natal=False):
    if str(row.get('chart_id')) != pins['chart_id']:
        raise ValueError('source chart mismatch')
    if generation is not None and row.get('generation') != generation:
        raise ValueError('source generation mismatch')
    if 'ayanamsha_id' in row and row['ayanamsha_id'] != pins['ayanamsha_id']:
        raise ValueError('source ayanamsha mismatch')
    if natal and str(row.get('build_id')) != pins['natal_build_id']:
        raise ValueError('source natal build mismatch')


def _validate_bundle(bundle):
    pins = bundle['pins']
    if (pins.get('judge_generation') != '5.0' or not pins.get('upstream_fingerprint')
            or any(not pins.get(k) for k in ('chart_id', 'manifest_id', 'verifier_execution_id',
                'natal_build_id', 'judge_build_id', 'vedha_generation', 'f1_generation', 'ayanamsha_id', 'convention_id'))
            or 'f2_scenario_id' not in pins):
        raise ValueError('sealed 5.0 pins required')
    for kind in KINDS:
        keys = [row_key(kind, row) for row in bundle[kind]]
        if len(set(keys)) != len(keys):
            raise ValueError('duplicate/ambiguous source key')
    for kind in ('seal', 'publication', 'verifier'):
        if len(bundle[kind]) != 1:
            raise ValueError('one same-snapshot seal/publication/verifier required')
        row = bundle[kind][0]
        _pin(row, pins, pins['judge_generation'])
        if row.get('manifest_id') != pins['manifest_id']:
            raise ValueError('manifest mismatch')
    publication = bundle['publication'][0]
    vector = publication.get('input_generation_vector', {})
    if (publication['status'] != 'published' or vector.get('stored_scope') == 'test_slice'
            or 'test_slice' in vector or publication['convention_id'] != pins['convention_id']):
        raise ValueError('full published manifest required')
    verifier = bundle['verifier'][0]
    if (verifier.get('execution_id') != pins['verifier_execution_id']
            or not verifier.get('brief_digest') or not verifier.get('state_digest')):
        raise ValueError('verifier run mismatch')
    # Actual corpus key inventories are verified by read_export. Where the
    # manifest provides this count, it supplies an additional independent check.
    for name, kind in (('records', 'record'), ('coverage', 'coverage')):
        count = publication.get('row_counts', {}).get(name)
        if count is not None and count != len(bundle[kind]):
            raise ValueError('sealed manifest row count mismatch')
    for kind in ('record', 'coverage'):
        for row in bundle[kind]:
            _pin(row, pins, pins['judge_generation'])
            if kind == 'coverage' and str(row.get('build_id')) != pins['judge_build_id']:
                raise ValueError('judge coverage build mismatch')
            if kind == 'record' and row.get('fixture') is not False:
                raise ValueError('live-as-fixture refused')
    for row in bundle['fact']:
        _pin(row, pins, natal=True)
    for row in bundle['f1']:
        _pin(row, pins, pins['f1_generation'])
    for kind in ('vedha_header', 'vedha_interval'):
        for row in bundle[kind]:
            _pin(row, pins, pins['vedha_generation'])
            if row.get('vedha_kind') != 'house_vedha':
                raise ValueError('only admitted house_vedha may bind')
            if kind == 'vedha_header' and (str(row['natal_build_id']) != pins['natal_build_id']
                    or row['upstream_fingerprint'] != pins['upstream_fingerprint']):
                raise ValueError('stale vedha fingerprint/build')
    return pins


def _coverage_reason(coverage, record, interval, pins):
    if not coverage:
        return 'judge_coverage_unavailable'
    if (coverage.get('convention_id') != pins['convention_id']
            or not contains(coverage['completed_horizon'], coverage['requested_horizon'])
            or not contains(coverage['completed_horizon'], interval)
            or not contains(coverage['requested_horizon'], interval)
            or coverage.get('targets_unresolved') != 0 or coverage.get('unavailable_inputs') != {}
            or coverage.get('unsearched_reason') is not None
            or (record and record['relation'] not in coverage.get('relations_searched', []))):
        return 'judge_coverage_unavailable'
    if record:
        snapshot = record.get('coverage_facts', {})
        horizon = snapshot.get('horizon')
        if horizon is not None:
            if horizon.get('lower_inc') is not True or horizon.get('upper_inc') is not False:
                raise ValueError('coverage snapshot bounds mismatch')
            snapshot_span = span(dict(t0=horizon['lower'],t1=horizon['upper']))
        else:
            snapshot_span = span(snapshot['completed_horizon'])
        if (snapshot.get('convention_id') != coverage['convention_id']
                or sorted(snapshot.get('relations_searched', [])) != sorted(coverage['relations_searched'])
                or snapshot_span != span(coverage['completed_horizon'])):
            raise ValueError('record coverage snapshot drift')
    return None


def _facts_exist(ids, facts):
    return bool(ids) and all(ref in facts for ref in ids)


def _f1(row, binding, facts):
    """No full-window inference from a defeat edge that lacks a licensed interval."""
    if not row:
        return [], 'unresolved', 'f1_inputs_unqualified'
    state, ledger = row.get('conclusion_state_jsonb', {}), row.get('derivation_ledger_jsonb', {})
    if (row.get('mechanism_route') != 'admitted' or row.get('event_class_id') != binding['event_class_id']
            or row.get('mechanism_id') != binding['mechanism'] or ledger.get('route') != 'admitted'
            or state.get('qualification') != 'sourced' or state.get('fact_state') != 'present'
            or state.get('conclusion_id') != binding['assertion_id']
            or not _facts_exist(ledger.get('fact_ids', []), facts)
            or ledger.get('cancellation_unqualified')):
        return [], 'unresolved', 'f1_inputs_unqualified'
    for key in ('conclusion_id', 'formation_state', 'fact_state', 'effective_state',
                'defeats', 'excepts', 'qualification'):
        if key not in state or ledger.get(key) != state[key]:
            return [], 'unresolved', 'f1_inputs_unqualified'
    try:
        source = _json(ledger['source']) if isinstance(ledger['source'], str) else ledger['source']
        if not all(source.get(k) for k in ('l1', 'l0', 'citations')):
            raise ValueError('source missing')
    except (KeyError, TypeError, ValueError):
        return [], 'unresolved', 'source_locator_missing'
    edges = []
    for edge in state['defeats'] + state['excepts']:
        if 'interval' not in edge:
            return [], 'unresolved', 'f1_protection_interval_unassessed'
        try:
            if 'conclusion_id' in edge:
                if (edge.get('evidence_reason') is not None or not edge.get('rule_id')
                        or not edge.get('rule_version') or not edge.get('source_locator')):
                    return [], 'unresolved', 'f1_inputs_unqualified'
                normalized = dict(target_assertion_id=edge['conclusion_id'],kind=edge['kind'],
                    fact_ids=edge['fact_ids'],source=dict(text=edge['rule_id'],locator=edge['source_locator']),
                    interval=edge['interval'])
            else:
                normalized = edge
            parsed = Protection.model_validate(normalized)
        except ValueError:
            return [], 'unresolved', 'f1_inputs_unqualified'
        if parsed.target_assertion_id != binding['assertion_id'] or not _facts_exist(parsed.fact_ids, facts):
            return [], 'unresolved', 'f1_inputs_unqualified'
        edges.append(parsed)
    effective = state.get('effective_state')
    translated = {'in_force': 'active', 'defeated': 'cancelled', 'partly_defeated': 'partly_cancelled',
                  'contested': 'contested', 'unresolved': 'unresolved'}.get(effective)
    if translated is None or translated == 'unresolved':
        return edges, 'unresolved', 'f1_inputs_unqualified'
    if translated != 'active' and not edges:
        return [], 'unresolved', 'defeating_evidence_unavailable'
    if (translated == 'contested' and not any(e.kind == 'contests' for e in edges)
            or translated == 'active' and edges):
        return [], 'unresolved', 'f1_inputs_unqualified'
    return edges, translated, None


def _binding(record, binding, headers, intervals, pins):
    if binding is None:
        return None, [], 'producer_record_correspondence_unavailable'
    for target, source in (('event_class_id', 'event_class'), ('frame_kind', 'frame_kind'),
                           ('frame_arg', 'frame_arg'), ('contact_id', 'contact_id')):
        if binding.get(target) != record.get(source):
            raise ValueError('producer-record correspondence mismatch')
    if (binding.get('source_fact_ids') != record.get('source_fact_ids')
            or binding.get('upstream_fingerprint') != pins['upstream_fingerprint']
            or graha_id(binding.get('graha')) != graha_id(record.get('agent'))):
        raise ValueError('producer-record references/fingerprint mismatch')
    if record['frame_kind'] != 'moon' or record.get('frame_arg') is not None:
        raise ValueError('house_vedha requires the Moon reference frame')
    source = Source.model_validate(binding['source'])
    if (record.get('source_text') and record.get('source_page')
            and source.model_dump() != dict(text=record['source_text'],locator=record['source_page'])):
        raise ValueError('judge source locator correspondence mismatch')
    callback = binding.get('callback')
    if not isinstance(callback, dict):
        raise ValueError('structured callback required, no aggregate state')
    factor = binding.get('factor')
    if not isinstance(factor, (list, tuple)) or len(factor) != 2:
        raise ValueError('factor ref required')
    check_callback_result(callback, tuple(factor))
    if callback.get('applicable') is False:
        return None, [], 'vedha_factor_not_applicable'
    if callback.get('applicable') is not True:
        raise ValueError('callback applicability must be explicit')
    if not headers:
        return None, [], 'judge_vedha_rows_absent'
    if len(headers) != 1:
        raise ValueError('ambiguous house_vedha header')
    header = headers[0]
    if binding.get('janma_reference_fact_id') != header['janma_reference_fact_id']:
        raise ValueError('Moon fact correspondence mismatch')
    primary = binding['primary_span']
    lo, hi = span(primary)
    segments = sorted((row for row in intervals if graha_id(row['graha']) == graha_id(binding['graha'])
        and stamp(row['t_in']) < hi and lo < stamp(row['t_out'])), key=lambda r: stamp(r['t_in']))
    if not segments:
        return header, [], 'judge_vedha_rows_absent'
    results = callback.get('results', [])
    if len(results) != len(segments):
        raise ValueError('callback/interval key count mismatch')
    boundaries = sorted({stamp(s[k]) for s in segments for k in ('t_in', 't_out')})
    if [stamp(x) for x in callback.get('boundaries', [])] != boundaries:
        raise ValueError('callback boundaries mismatch; interior island may be lost')
    scopes = sorted({s['moon_scope'] for s in segments if s.get('moon_scope')})
    if callback.get('scopes') != scopes:
        raise ValueError('callback scopes mismatch')
    for index, (segment, result) in enumerate(zip(segments, results)):
        a, b = stamp(segment['t_in']), stamp(segment['t_out'])
        if a >= b or (index and stamp(segments[index - 1]['t_out']) != a):
            raise ValueError('producer intervals overlap or have a gap')
        if (stamp(result['t_in']) != a or stamp(result['t_out']) != b
                or any(result.get(x) != segment.get(y) for x, y in (
                    ('state', 'state'), ('reason', 'unqualified_reason'), ('reasons', 'reasons'),
                    ('scope', 'moon_scope'), ('obstructors', 'obstructors'), ('unknown_obstructors', 'unknown_obstructors')))):
            raise ValueError('callback/interval semantics mismatch')
        expected_value = {'active': 0.0, 'inactive': 1.0, 'unqualified': None}
        if (segment['state'] not in expected_value or result.get('null_state') != 'unqualified'
                or isinstance(result.get('value'),bool)
                or result.get('value') != expected_value[segment['state']]
                or result.get('qualification') != ('vedha_active' if segment['state'] == 'active' else None)):
            raise ValueError('callback state qualification mismatch')
        if segment['state'] == 'unqualified' and (not segment.get('unqualified_reason')
                or segment['unqualified_reason'] not in segment.get('reasons', [])):
            raise ValueError('unqualified producer interval requires its original reasons')
        if segment['state'] == 'active' and not segment.get('obstructors'):
            raise ValueError('active producer interval requires its actual obstructors')
        if segment['state'] == 'inactive' and graha_id(binding['graha']) != GrahaId.MERCURY and segment.get('moon_scope') != 'excluding_on_demand_moon_obstruction':
            raise ValueError('inactive scope lost')
    primary = binding['primary_span']
    if span(primary) != (stamp(segments[0]['t_in']), stamp(segments[-1]['t_out'])):
        raise ValueError('callback primary support mismatch')
    if not any(contains(s, primary) for s in record['temporal_support_intervals']):
        raise ValueError('producer support not contained in judge support')
    return header, segments, None


def _clock_reason(clock, interval, pins, system):
    if clock is None:
        return 'f2_coverage_gap'
    if (str(clock.get('build_id')) != pins['natal_build_id'] or clock.get('ayanamsha_id') != pins['ayanamsha_id']
            or clock.get('tier') != TWO_PASS_VERIFIED or clock.get('system') != system
            or clock.get('scenario_id') != pins['f2_scenario_id']):
        raise ValueError('F2 pinned build/tier/convention/system mismatch')
    if clock.get('applicability') == 'unknown':
        return clock.get('null_reason') or 'f2_applicability_unknown'
    if (not contains(clock['interval'], interval) or not clock.get('period_ids') or not clock.get('sources')
            or not clock.get('lineage') or not clock.get('lords')):
        return 'f2_coverage_gap'
    if clock.get('applicability') not in {'applicable', 'method_inapplicable'}:
        raise ValueError('F2 applicability invalid')
    return None


def prepare(bundle, *, candidate_generation, clock_spans):
    """Materialise exact producer partitions, F2 boundaries and scoped protections.

    The independent export inventory defines the universe. Unmatched records
    and zero-record coverage retain named gaps; nothing invents a horizon or
    takes a Cartesian product of presumed mechanisms.
    """
    bundle = deepcopy(bundle)
    pins = _validate_bundle(bundle)
    if not candidate_generation.startswith('candidate:') or candidate_generation == 'candidate:':
        raise ValueError('private candidate generation required')
    facts = {row['fact_id']: row for row in bundle['fact']}
    bindings = {}
    for row in bundle['correspondence']:
        bindings.setdefault(row['record_id'], []).append(row)
    records = {row['record_id']: row for row in bundle['record']}
    if any(key not in records for key in bindings):
        raise ValueError('unmatched correspondence references absent record')
    coverage = {(row['partition_kind'], row['partition_key']): row for row in bundle['coverage']}
    f1s = {str(row['id']): row for row in bundle['f1']}
    rows = []
    covered_support = {}

    def emit(record, cov, binding, header, segment, interval, clock, edges, defeat, reason):
        mechanism = binding['mechanism'] if binding else 'unmapped_judge_record'
        knowledge = 'inputs_missing' if reason else 'complete'
        judge_state = segment['state'] if segment else None
        conclusion = (binding or {}).get('rule_conclusion')
        if conclusion is None:
            conclusion = {'active': 'obstructed', 'inactive': 'none', 'unqualified': 'none'}.get(judge_state, 'none')
        if conclusion not in {'none', 'supportive', 'adverse', 'obstructed', 'conditionally_deferred', 'denied'}:
            raise ValueError('unrecognised rule conclusion')
        exposure = binding.get('exposure') if binding else 'in_risk_set'
        if exposure not in {'in_risk_set','outside_risk_set','method_inapplicable'}:
            raise ValueError('explicit source exposure axis required')
        if exposure != 'outside_risk_set' and clock and clock.get('applicability') == 'method_inapplicable':
            exposure = 'method_inapplicable'
        if (judge_state == 'active' and conclusion in {'none','supportive'}
                or judge_state == 'inactive' and conclusion in {'adverse','obstructed','denied'}):
            raise ValueError('producer state and rule conclusion contradict')
        relevant = [e for e in edges if e.interval.t0 < interval[1] and e.interval.t1 > interval[0]]
        # F1's global state cannot licence cancellation outside an edge's scope.
        local_defeat = 'active' if defeat != 'unresolved' else defeat
        if any(e.kind == 'contests' for e in relevant):
            local_defeat = 'contested'
        elif any(e.kind in {'defeats', 'excepts'} and e.interval.t0 <= interval[0] and interval[1] <= e.interval.t1 for e in relevant):
            local_defeat = 'cancelled'
        elif relevant:
            local_defeat = 'partly_cancelled'
        if not reason and conclusion == 'conditionally_deferred':
            reason = 'rule_conclusion_conditionally_deferred'
            knowledge = 'inputs_missing'
        if reason:
            effective = 'information_unavailable'
        elif exposure in {'outside_risk_set','method_inapplicable'}:
            effective = exposure
        elif judge_state == 'inactive' or conclusion in {'none', 'supportive'}:
            effective = 'evaluated_silent'
        else:
            effective = {'active': 'obstruction_in_force', 'cancelled': 'obstruction_cancelled',
                'partly_cancelled': 'obstruction_partly_cancelled', 'contested': 'obstruction_contested',
                'unresolved': 'information_unavailable'}[local_defeat]
        refs = set(record.get('source_fact_ids', []) if record else [])
        refs.update(ref for edge in relevant for ref in edge.fact_ids)
        f1_row = f1s.get(str(binding.get('f1_id'))) if binding else None
        if f1_row:
            refs.update(f1_row.get('derivation_ledger_jsonb', {}).get('fact_ids', []))
        release = {'kind': 'unknown'}
        if segment and judge_state == 'active' and not reason:
            release = {'kind': 'instant', 'instant': stamp(segment['t_out']).isoformat()}
            if local_defeat == 'cancelled':
                onsets = [e.interval.t0 for e in relevant if e.kind in {'defeats','excepts'}
                          and e.interval.t0 == interval[0] and interval[1] <= e.interval.t1]
                release = ({'kind':'instant','instant':min(onsets).isoformat()} if onsets else {'kind':'unknown'})
        if binding and binding.get('release_predicate_ref'):
            release = {'kind': 'conditional', 'predicate_ref': binding['release_predicate_ref']}
        base_id = binding['assertion_id'] if binding else ('record:' + record['record_id'] if record else 'coverage:' + row_key('coverage', cov))
        identity = [pins['chart_id'],candidate_generation,
            record['record_id'] if record else row_key('coverage',cov),mechanism,wire(*interval)]
        assertion_id = 'k3:' + hashlib.sha256(canonical(identity).encode()).hexdigest()
        source = binding['source'] if binding else ({'text': record.get('source_text') or 'judge',
            'locator': record.get('source_page') or 'source_locator_missing'} if record else
            {'text': 'kala_gochara_coverage', 'locator': row_key('coverage', cov)})
        result = dict(contract_version=VERSION, assertion_id=assertion_id, source_assertion_id=base_id, chart_id=pins['chart_id'],
            generation=candidate_generation, event_class_id=record['event_class'] if record else cov['partition_key'],
            mechanism=mechanism, exposure=exposure, knowledge=knowledge, rule_conclusion=conclusion,
            defeat_state=local_defeat, measurement='not_estimated_here', effective_state=effective,
            interval=wire(*interval), roots=dict(record_ids=[record['record_id']] if record else [],
                contact_ids=[record['contact_id']] if record and record.get('contact_id') else [],fact_ids=sorted(refs)),
            source=source, what=mechanism, by_what=','.join(segment.get('obstructors', [])) if segment else None,
            protections=[dict(e.model_dump(mode='json'),interval=wire(e.interval.t0,e.interval.t1))
                for e in relevant], release=release,
            release_reason={'unknown':'release_unknown','conditional':'release_conditional'}.get(release['kind']),
            null_reason=reason, acceptance_scope='sealed_producers',
            provenance=dict(pins=pins,record=record,coverage=cov,header=header,interval=segment,
                correspondence=binding,callback=binding.get('callback') if binding else None,
                F1=f1s.get(str(binding.get('f1_id'))) if binding else None,F2=clock))
        rows.append(result)

    work = []
    for record in bundle['record']:
        key = (record['coverage_partition_kind'],record['coverage_partition_key'])
        cov = coverage.get(key)
        supports = record.get('temporal_support_intervals', [])
        if not supports:
            supports = [cov['requested_horizon']] if cov else []
        if not supports:
            raise ValueError('record has no support or coverage horizon')
        covered_support.setdefault(key, []).extend(span(s) for s in supports)
        candidates = bindings.get(record['record_id'], [])
        occupied = []
        for binding in candidates:
            lo,hi = span(binding['primary_span'])
            if any(a < hi and lo < b for a,b in occupied):
                raise ValueError('ambiguous overlapping producer correspondence')
            if not any(contains(s,binding['primary_span']) for s in supports):
                raise ValueError('producer support outside judge record')
            occupied.append((lo,hi))
            work.append((record,binding,[binding['primary_span']]))
        for support in supports:
            start,end = span(support)
            clipped = sorted((max(start,a),min(end,b)) for a,b in occupied if a < end and start < b)
            position = start
            for a,b in clipped + [(end,end)]:
                if position < a:
                    work.append((record,None,[wire(position,a)]))
                position = max(position,b)
    for record,binding,supports in work:
        key = (record['coverage_partition_kind'],record['coverage_partition_key'])
        cov = coverage.get(key)
        mechanism = binding['mechanism'] if binding else None
        if mechanism in REMOVED:
            continue
        header, segments, binding_reason = (None, [], 'producer_record_correspondence_unavailable')
        if mechanism == 'vedha' and record.get('temporal_support_state') != 'computed':
            binding_reason = 'judge_support_uncomputed'
        elif mechanism == 'vedha':
            header, segments, binding_reason = _binding(record, binding, bundle['vedha_header'], bundle['vedha_interval'], pins)
        elif binding:
            binding_reason = ('source_not_served' if mechanism == 'badhaka_movable_lagna'
                              else 'mechanism_evaluation_absent')
        f1 = f1s.get(str(binding.get('f1_id'))) if binding else None
        edges, defeat, f1_reason = _f1(f1, binding, facts) if binding else ([], 'unresolved', 'f1_inputs_unqualified')
        for support in supports:
            start, end = span(support)
            cuts = {start, end}
            for segment in segments:
                cuts.update(t for t in (stamp(segment['t_in']),stamp(segment['t_out'])) if start < t < end)
            for edge in edges:
                cuts.update(t for t in (edge.interval.t0,edge.interval.t1) if start < t < end)
            for clock in clock_spans:
                cuts.update(t for t in span(clock['interval']) if start < t < end)
            ordered = sorted(cuts)
            for a, b in zip(ordered, ordered[1:]):
                interval = wire(a, b)
                matched = [s for s in segments if stamp(s['t_in']) <= a < b <= stamp(s['t_out'])]
                clocks = [c for c in clock_spans if (not binding or c.get('system') == binding.get('f2_system')) and contains(c['interval'], interval)]
                if len(matched) > 1 or len(clocks) > 1:
                    raise ValueError('ambiguous producer/F2 interval')
                segment = matched[0] if matched else None
                clock = clocks[0] if clocks else None
                reason = _coverage_reason(cov, record, interval, pins)
                reason = reason or binding_reason
                if not reason and not _facts_exist(record['source_fact_ids'], facts):
                    raise ValueError('judge references absent natal facts')
                if not reason and (not record.get('source_text') or not record.get('source_page')):
                    reason = 'source_locator_missing'
                if not reason and record.get('admission_state') != 'admitted':
                    reason = 'judge_inputs_unqualified'
                if not reason and header:
                    if header['janma_reference_fact_id'] not in facts:
                        raise ValueError('Moon reference does not resolve to pinned natal fact')
                    moon = facts[header['janma_reference_fact_id']]
                    if (moon.get('fact_category') != 'graha_position'
                            or moon.get('fact_key') != 'longitude_sidereal'
                            or graha_id(moon.get('fact_subject')) != GrahaId.MOON):
                        raise ValueError('janma reference must resolve to the pinned Moon longitude fact')
                    hc = header['coverage']
                    if isinstance(hc.get('requested'), (list, tuple)):
                        SkyCoverage(**{key: tuple(hc[key]) if hc.get(key) is not None and key in
                            {'requested','source_interval','covered'} else hc.get(key) for key in
                            ('requested','source_interval','covered','complete','backend','convention_id')})
                        if hc.get('convention_id') != pins['convention_id']:
                            raise ValueError('sky convention mismatch')
                    if (hc.get('search_state') != 'searched' or hc.get('complete') is not True
                            or hc.get('gaps') or not contains(hc['covered'], interval)
                            or header.get('method_qualification') != 'qualified'):
                        reason = 'judge_coverage_unavailable'
                if not reason and not segment:
                    reason = 'judge_vedha_rows_absent'
                if not reason and segment.get('source_qualification') != 'verse_cited':
                    reason = 'judge_inputs_unqualified'
                if not reason and segment['state'] == 'unqualified':
                    reason = segment['unqualified_reason']
                reason = reason or f1_reason
                if binding:
                    reason = reason or _clock_reason(clock, interval, pins, binding.get('f2_system'))
                emit(record,cov,binding,header,segment,(a,b),clock,edges,defeat,reason)
    for key, cov in coverage.items():
        start, end = span(cov['requested_horizon'])
        covered = sorted((max(start,a), min(end,b)) for a,b in covered_support.get(key, [])
                         if a < end and b > start)
        position = start
        for a,b in covered + [(end,end)]:
            if position < a:
                emit(None,cov,None,None,None,(position,a),None,[],'unresolved','mechanism_evaluation_absent')
            position = max(position,b)
    return sorted(rows, key=lambda row: (row['event_class_id'],row['interval']['t0'],row['assertion_id']))


def validate_certification_mapping(root):
    """Validate current K8-K3 evidence, never award production certification."""
    from services.kala_core.certification import validate_detector_bindings, validate_fidelity_bindings
    mapping_path = Path('platform/python-sidecar/services/ka_vighnakara/certification_mapping.json')
    try:
        mapping = _json((root / mapping_path).read_text())
        required = {'version','registry_revision','asset','kind','carriage','ldgr_source','vocab_alias',
            'prose_fields','fidelity_tests','null_convention','produced_tables','density_tier_columns',
            'semantic_fingerprint','writer_digest','disposition','production_certification','gates'}
        errors = [] if required <= mapping.keys() else ['missing K8 declarations']
        if mapping.get('asset') != 'ka_vighnakara' or mapping.get('kind') != 'data':
            errors.append('wrong asset identity/kind')
        if 'production_certification' not in mapping or mapping['production_certification'] is not None:
            errors.append('production certification must be explicitly null')
        errors.extend(validate_detector_bindings(root,mapping,gates={
            'Build','Idem','Earn','Vocab','Ldgr','Dens','Narr','Null','Carr'}))
        errors.extend(validate_fidelity_bindings(root,mapping.get('fidelity_tests'),required={
            'tests/l3/ka_vighnakara/test_sealed.py::test_segments_scopes_and_all_source_fields_survive',
            'tests/l3/kala_db/ka_vighnakara/test_sealed_storage.py::test_live_storage_schema_and_repeat_content',
            'tests/l3/kala_db/ka_vighnakara/test_sealed_storage.py::test_migration_repeat_and_served_legacy_bytes'}))
        return errors
    except (OSError,ValueError,KeyError,TypeError,AttributeError,StopIteration,SyntaxError) as exc:
        return [f'mapping source unavailable: {exc}']
