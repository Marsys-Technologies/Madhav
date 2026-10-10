"""Candidate-only F1 storage; caller owns transaction and publication lifecycle."""
from collections.abc import Iterable
from dataclasses import asdict, replace
from typing import Any
import json

import psycopg.rows

from services.kala_core.promise.relationships import Projection, resolve_relationships


def store_projection(conn: Any, *, chart_id: str, ayanamsha_id: str, generation: str,
                     build_id: str, projections: Iterable[Projection]) -> int:
    if not generation.startswith('candidate:') or not generation.removeprefix('candidate:'):
        raise ValueError('F1 writer requires a candidate: generation')
    if not build_id:
        raise ValueError('F1 candidate must be bound to a build')
    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        # Row-level exclusive candidate lock serializes repeat builds and state
        # transitions. Published heads and retained/sealed candidates are refused.
        cur.execute('SELECT state, build_id FROM kala_layer_candidate WHERE chart_id=%s AND generation=%s FOR UPDATE',
                    (chart_id, generation))
        candidate = cur.fetchone()
        if not candidate or candidate['state'] != 'building':
            raise ValueError('F1 requires a registered building candidate')
        if str(candidate['build_id']) != str(build_id):
            raise ValueError('F1 candidate is bound to a different build')
        cur.execute('SELECT generation FROM kala_layer_head WHERE chart_id=%s FOR SHARE', (chart_id,))
        if any(row['generation'] == generation for row in cur.fetchall()):
            raise ValueError('F1 must not replace a published head')
        objects, edges = {}, {}
        for projection in projections:
            for obj in projection.objects:
                old = objects.get(obj.object_id)
                if old:
                    if (old.object_type, old.longitude_deg, old.sign_num) != (obj.object_type, obj.longitude_deg, obj.sign_num):
                        raise ValueError('conflicting physical target geometry')
                    obj = replace(obj, fact_ids=tuple(sorted(set(old.fact_ids) | set(obj.fact_ids))))
                objects[obj.object_id] = obj
            for edge in projection.edges:
                edges[edge.edge_id] = edge
        identity = dict(chart_id=chart_id, ayanamsha_id=ayanamsha_id, generation=generation)
        cur.execute('DELETE FROM kala_f1_relationship WHERE chart_id=%s AND ayanamsha_id=%s AND generation=%s',
                    (chart_id, ayanamsha_id, generation))
        cur.execute('DELETE FROM kala_f1_target_object WHERE chart_id=%s AND ayanamsha_id=%s AND generation=%s',
                    (chart_id, ayanamsha_id, generation))
        object_rows = [{**identity, **asdict(objects[k]), 'fact_ids': json.dumps(objects[k].fact_ids)} for k in sorted(objects)]
        edge_rows = [{**identity, **asdict(edges[k])} for k in sorted(edges)]
        if object_rows:
            cur.executemany('''INSERT INTO kala_f1_target_object
              (chart_id,ayanamsha_id,generation,object_id,object_type,longitude_deg,sign_num,fact_ids)
              VALUES (%(chart_id)s,%(ayanamsha_id)s,%(generation)s,%(object_id)s,%(object_type)s,
                      %(longitude_deg)s,%(sign_num)s,%(fact_ids)s::jsonb)''', object_rows)
        if edge_rows:
            cur.executemany('''INSERT INTO kala_f1_relationship
              (chart_id,ayanamsha_id,generation,edge_id,event_class_id,object_id,role,frame,mechanism_id,
               rule_id,provenance,target_ref,qualifier,resolution_state)
              VALUES (%(chart_id)s,%(ayanamsha_id)s,%(generation)s,%(edge_id)s,%(event_class_id)s,%(object_id)s,
                      %(role)s,%(frame)s,%(mechanism_id)s,%(rule_id)s,%(provenance)s,%(target_ref)s,
                      %(qualifier)s,%(resolution_state)s)''', edge_rows)
    return len(objects) + len(edges)


def build_candidate_projection(ctx: Any) -> tuple[int, str]:
    """Fetch actual source contracts once; never read a published promise as candidate."""
    from services.ka_gochara_resonance.writer import TARGET_EVENT_CLASSES
    chart_id = ctx.config['chart_id']
    generation = ctx.config['candidate_generation']
    ayan = ctx.config.get('ayanamsha_id', 'lahiri_chitrapaksha')
    with ctx.db_conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute('''SELECT fact_id,fact_subject,fact_category,fact_key,fact_value_num,fact_value_text,unit
          FROM chart_facts WHERE chart_id=%s AND ayanamsha_id=%s''', (chart_id, ayan))
        facts = cur.fetchall()
        cur.execute('SELECT sign_id,lord FROM reference_signs')
        sign_lords = {row['sign_id']: row['lord'] for row in cur.fetchall()}
        cur.execute('''SELECT event_class_id,signature_model,citations FROM brahma_event_ontology
          WHERE event_class_id=ANY(%s) ORDER BY event_class_id''', (list(TARGET_EVENT_CLASSES),))
        ontology = cur.fetchall()
        if {r['event_class_id'] for r in ontology} != set(TARGET_EVENT_CLASSES) or any(r['signature_model'] is None for r in ontology):
            raise ValueError('F1 ontology coverage incomplete; candidate preserved')
        # L0 has Moon-house numbers, not lagna numbers. No house filtering is
        # allowed at this fetch boundary; the pure resolver transforms frames.
        cur.execute('SELECT id,rule_type,graha,primary_house,classical_citation FROM bg_transit_rules ORDER BY id')
        rules = cur.fetchall()
        cur.execute('''SELECT yoga_canonical_id,fired,constituent_fact_ids,constituent_planets,constituent_houses,bhanga_active
          FROM ga_yoga_firings WHERE chart_id=%s AND ayanamsha_id=%s AND fired=true''', (chart_id, ayan))
        yogas = cur.fetchall()
        cur.execute('''SELECT DISTINCT lord_graha FROM chart_dashas WHERE chart_id=%s AND ayanamsha_id=%s
          AND system_id='vimshottari' AND level_n=1''', (chart_id, ayan))
        dashas = [r['lord_graha'] for r in cur.fetchall()]
        cur.execute('''SELECT event_class_id,mechanism_id,derivation_ledger_jsonb FROM kala_activation_predicates
          WHERE chart_id=%s AND ayanamsha_id=%s AND generation=%s''', (chart_id, ayan, generation))
        promises = cur.fetchall()
    from services.kala_core.promise.relationships import _subject
    projections = []
    for row in ontology:
        event_class, sig = row['event_class_id'], row['signature_model']
        karakas = {_subject(k) for k in sig.get('karakas', ())} - {None}
        houses = {str(h) for h in sig.get('houses', ())}
        class_yogas = [r for r in yogas if
            any(_subject(p) in karakas for p in r.get('constituent_planets') or ()) or
            any(str(h) in houses for h in r.get('constituent_houses') or ())]
        class_promises = [{**r['derivation_ledger_jsonb'], 'mechanism_id': r['mechanism_id']}
                          for r in promises if r['event_class_id'] == event_class]
        projections.append(resolve_relationships(event_class, facts=facts, sign_lords=sign_lords,
            signature=sig, citations=row['citations'] or (), transit_rules=rules,
            sensitive=[r for r in facts if r['fact_category'] == 'sensitive_degree_check' and _subject(r['fact_subject']) in karakas],
            arudhas=[r for r in facts if r['fact_category'] == 'arudha_pada' and r['fact_key'] == 'sign'
                     and r['fact_subject'] in {f'ARUDHA_A{h}' for h in houses}],
            yogas=class_yogas, dasha_lords=[d for d in dashas if _subject(d) in karakas], promises=class_promises))
    count = store_projection(ctx.db_conn, chart_id=chart_id, ayanamsha_id=ayan,
                             generation=generation, build_id=ctx.build_id, projections=projections)
    return count, json.dumps({'projection': 'F1-relationships-v1', 'generation': generation,
                             'event_classes': len(ontology), 'legacy_map_unchanged': True}, sort_keys=True)
