"""Fact-backed F1 relations; never infer an event claim or an L0 rule identity."""
from __future__ import annotations

import re

from services.kala_core.promise.relationships import _integer, _subject


def _graha(value):
    return _subject(value)


def _relations(fact):
    """Read the atomic contracts emitted by ga_positions / ga_structural.

    These are references to already-computed relations, not re-derivations of
    aspects, lords, occupancy, or the argala count/strength comparison.
    """
    category, key, subject = fact['fact_category'], fact['fact_key'], fact['fact_subject']
    value = fact.get('fact_value_jsonb') or {}
    value = value if isinstance(value, dict) else {}
    graha = _graha(subject)
    text = fact.get('fact_value_text')
    number = fact.get('fact_value_num')
    if category == 'lord_in_house_per_varga' and key == 'lord_placement':
        lord, house, varga = _graha(value.get('lord')), _integer(value.get('house')), value.get('varga')
        if lord and house and varga:
            yield 'lordship', ('graha', lord), ('house', f'{varga}:H{house}'), 'lagna', False
    elif category == 'graha_position' and key == 'house_d1' and graha:
        house = _integer(number)
        if house:
            yield 'occupation', ('graha', graha), ('house', f'D1:H{house}'), 'lagna', False
    elif category == 'graha_position' and key == 'sign_lord' and graha and _graha(text):
        yield 'dispositor', ('graha', graha), ('graha', _graha(text)), 'zodiac', False
    elif category == 'graha_dispositor_chain' and key == 'chain_jsonb_atomic':
        chain = value.get('chain') or []
        for source, target in zip(chain, chain[1:]):
            if _graha(source) and _graha(target):
                yield 'dispositor', ('graha', _graha(source)), ('graha', _graha(target)), 'zodiac', False
    elif category == 'aspect_parashari_given' and graha:
        match = re.fullmatch(r'house_(\d+)', key)
        house = _integer(match[1]) if match else None
        if house and number is not None and number > 0:
            yield 'classical_aspect', ('graha', graha), ('house', f'D1:H{house}'), 'lagna', False
    elif category == 'aspect_jaimini' and key.startswith('on_') and number is not None and number > 0:
        yield 'classical_aspect', ('sign', subject), ('sign', key.removeprefix('on_')), 'zodiac', False
    elif category == 'karakatva_strength_per_significance' and key == 'natural_karaka' and _graha(text):
        yield 'karaka', ('graha', _graha(text)), ('significance', subject), 'natal', False
    elif category == 'argala_graha_natal':
        target, source = _graha(value.get('target_graha')), _graha(value.get('source_graha'))
        if source and target:
            yield 'argala', ('graha', source), ('graha', target), 'natal', True
            for obstructor in value.get('obstructor_grahas') or []:
                if _graha(obstructor):
                    yield 'virodha', ('graha', _graha(obstructor)), ('graha', target), 'natal', True
    elif category in {'argala_natal_matrix', 'virodha_argala_natal_matrix'}:
        target = re.fullmatch(r'(?:(D\d+)_)?SIGN_(\d+)', subject)
        source = re.fullmatch(r'from_sign_(\d+)_offset_\d+', key)
        # Zero matrix cells and no_occupant nulls assert no relation.
        if target and source and number is not None and number != 0:
            target_sign, source_sign = _integer(target[2]), _integer(source[1])
            if target_sign and source_sign:
                varga = target[1] or 'D1'  # producer's unprefixed D1 subjects
                relation = 'argala' if category == 'argala_natal_matrix' else 'virodha'
                yield relation, ('sign', f'{varga}:{source_sign}'), ('sign', f'{varga}:{target_sign}'), 'zodiac', True


def structural_bundle(facts, *, served_locators=()):
    output = []
    locators = set(served_locators)
    for fact in sorted(facts, key=lambda f: (str(f['ayanamsha_id']), str(f['fact_id']))):
        relations = list(_relations(fact))
        if not relations:
            continue
        ayan, fid = str(fact['ayanamsha_id']), str(fact['fact_id'])
        mid = f'{ayan}:structural:{fid}'
        nodes, edges, planets = {}, [], set()
        for relation, source, target, frame, d_local in relations:
            ids = []
            for kind, identity in (source, target):
                node_id = f'{ayan}:{kind}:{identity}'
                nodes[node_id] = dict(node_id=node_id, kind=kind, fact_ids=[fid])
                ids.append(node_id)
                if kind == 'graha':
                    planets.add(identity)
            locator = fact.get('citation_ref')
            provenance = 'verse_cited' if not d_local and locator and locator in locators else 'uncited_extension'
            edges.append(dict(source_id=ids[0], target_id=ids[1], relation=relation,
                polarity='opposes' if relation == 'virodha' else 'supports', frame=frame,
                rule_id=None, rule_version='unadmitted', provenance=provenance,
                source_locator=locator if provenance == 'verse_cited' else None,
                source_fact_id=fid, operator_role='testimony', weight=0,
                method_qualification='d_local' if d_local else None))
        # (I) INTERPRETATION: a descriptive L1 relation has no event binding or
        # admitted L0 rule version. Retain it as unscored testimony, even when
        # its citation resolves in the served corpus. Never infer an event.
        output.append(dict(mechanism_id=mid, conclusion_id=f'{mid}:conclusion',
            canonical_id=None, ayanamsha_id=ayan, event_class_id=None,
            route='testimony', operator_role='testimony', weight=0,
            formation_state='present', fact_state='present', fact_ids=[fid],
            rule_version='unadmitted', source=f'chart_facts:{fid}', binding=None,
            graph_nodes=list(nodes.values()), graph_edges=edges,
            qualification='unadmitted_structural_event_binding', effective_state='unresolved',
            scored=False, defeats=[], excepts=[], cancellation_unqualified=[], target=None,
            constituent_planets=sorted(planets), attachments=[],
            method_qualification='d_local' if any(e['method_qualification'] == 'd_local' for e in edges) else None,
        ))
    return output
