"""Weight-free F1 target projection. Resolve frames before matching L0 rules."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Any, TypedDict
from enum import StrEnum
import hashlib
import json
import math
import re

from services.kala_core.vocab import graha_id
from services.gochara_grammar.derived_points import (
    M6_EVENT_CLASSES, MANDI_DISTANCE_CITATION, MANDI_DISTANCE_REF,
    YAMAKANTAKA_FORMULAS, difference_sign_num, fifth_star_lord,
    mandi_distance_target_sign_num, sign_num_of,
)


class FactRow(TypedDict):
    fact_id: str
    fact_subject: str
    fact_category: str
    fact_key: str
    fact_value_num: float | Decimal | None
    fact_value_text: str | None
    unit: str | None


class TransitRule(TypedDict):
    id: int
    graha: str
    rule_type: str
    primary_house: int
    classical_citation: str


class Frame(StrEnum):
    LAGNA = 'lagna'
    MOON = 'moon'
    ZODIAC = 'zodiac'


class Role(StrEnum):
    BHAVA = 'bhava'
    LORD = 'lord'
    KARAKA = 'karaka'
    TRANSIT = 'mechanism_node'
    SENSITIVE = 'sensitive_degree'
    ARUDHA = 'arudha'
    BHAVA_ARUDHA = 'bhava_arudha'
    YOGA = 'yoga_constituent'
    DASHA = 'dasha_lord_portfolio'
    MANDI = 'gulika_mandi_distance'
    YAMAKANTAKA = 'yamakantaka_difference'
    PROMISE = 'promise_participant'


@dataclass(frozen=True)
class TargetObject:
    object_id: str
    object_type: str
    longitude_deg: float | None
    sign_num: int | None
    fact_ids: tuple[str, ...]


@dataclass(frozen=True)
class Relationship:
    edge_id: str
    event_class_id: str
    object_id: str | None
    role: Role
    frame: Frame
    mechanism_id: str
    rule_id: str
    provenance: str
    target_ref: str
    qualifier: str | None
    resolution_state: str


@dataclass(frozen=True)
class Projection:
    objects: tuple[TargetObject, ...]
    edges: tuple[Relationship, ...]


def _reject_weight(value):
    if isinstance(value, dict):
        if 'weight' in value:
            raise ValueError('F1 relationships do not admit weight')
        for v in value.values():
            _reject_weight(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            _reject_weight(v)


def _subject(value):
    try:
        return graha_id(str(value)).value
    except ValueError:
        return None


def _integer(value, maximum=12):
    try:
        number = float(value)
        return int(number) if math.isfinite(number) and number.is_integer() and 1 <= number <= maximum else None
    except (ValueError, TypeError):
        return None


def resolve_relationships(
    event_class: str, *, facts: Iterable[FactRow], sign_lords: Mapping[int, str],
    signature: Mapping[str, Any], citations: Iterable[str] = (),
    transit_rules: Iterable[TransitRule] = (), sensitive: Iterable[FactRow] = (),
    arudhas: Iterable[FactRow] = (), yogas: Iterable[Mapping[str, Any]] = (),
    dasha_lords: Iterable[str] = (), promises: Iterable[Mapping[str, Any]] = (),
) -> Projection:
    """Project one convention/class; all missing operands remain explicit nulls.

    Inputs are source rows (no L1 computation copied into F1). Longitude zero is
    valid; absent/ambiguous/invalid longitude is not zero. The caller isolates
    ayanamsha and candidate generation before invoking this pure computation.
    """
    facts, transit_rules, promises = list(facts), list(transit_rules), list(promises)
    arudhas, citations = list(arudhas), tuple(citations)
    _reject_weight([signature, transit_rules, promises])
    by_id = {str(f['fact_id']): f for f in facts}
    objects, edges = {}, {}

    def find(subject, category, key):
        matches = [f for f in facts if f['fact_subject'] == subject and
                   f['fact_category'] == category and f['fact_key'] == key]
        return matches[0] if len(matches) == 1 else None

    def anchor(subject):
        row = find(subject, 'graha_sign_attributes', 'sign_num')
        return (_integer(row.get('fact_value_num')), (str(row['fact_id']),)) if row else (None, ())

    lagna, lagna_ids = anchor('LAGNA')
    moon, moon_ids = anchor('MOON')

    def sign_target(sign, refs):
        sign = _integer(sign)
        return TargetObject(f'sign:{sign}', 'sign_interval', None, sign, tuple(sorted(set(refs)))) if sign else None

    def graha_target(subject, refs=()):
        subject = _subject(subject)
        matches = [f for f in facts if _subject(f['fact_subject']) == subject and subject is not None
                   and f['fact_category'] == 'graha_position' and f['fact_key'] == 'longitude_sidereal']
        if len(matches) != 1:
            return None
        row = matches[0]
        try:
            value = float(row['fact_value_num'])
        except (ValueError, TypeError):
            return None
        if row.get('unit') not in {'deg', 'degrees'} or not math.isfinite(value) or not 0 <= value < 360:
            return None
        return TargetObject(f'graha:{subject}', 'graha', value, None,
                            tuple(sorted({str(row['fact_id']), *refs})))

    def emit(target, role, frame, ref, *, mechanism=None, rule=None,
             provenance=None, qualifier=None, state='unavailable'):
        role, frame = Role(role), Frame(frame)
        if target:
            prior = objects.get(target.object_id)
            if prior:
                target = replace(target, fact_ids=tuple(sorted(set(prior.fact_ids) | set(target.fact_ids))))
            objects[target.object_id] = target
        values = dict(event_class_id=event_class, object_id=target.object_id if target else None,
                      role=role, frame=frame, target_ref=str(ref), qualifier=qualifier,
                      mechanism_id=mechanism or f'ontology:{event_class}',
                      rule_id=rule or f'ontology:{event_class}',
                      provenance=provenance if provenance is not None else json.dumps(list(citations), sort_keys=True),
                      resolution_state='resolved' if target else state)
        edge_id = hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()
        edges[edge_id] = Relationship(edge_id=edge_id, **values)

    houses = sorted({_integer(h) for h in signature.get('houses', ())} - {None})
    signs = {h: ((lagna + h - 2) % 12 + 1 if lagna else None) for h in houses}
    for h, sign in signs.items():
        emit(sign_target(sign, lagna_ids), Role.BHAVA, Frame.LAGNA, h)
    for text in signature.get('lords', ()):
        for h in re.findall(r'(\d+)L', str(text)):
            house = _integer(h)
            sign = (lagna + house - 2) % 12 + 1 if lagna and house else None
            lord = sign_lords.get(sign)
            emit(graha_target(lord, lagna_ids) if lord else None, Role.LORD, Frame.LAGNA, f'{h}L',
                 qualifier='afflicted' if re.search(r'\bafflicted\b', str(text), re.I) else None,
                 state='unqualified' if sign and not lord else 'unavailable')
    karakas = {_subject(k) for k in signature.get('karakas', ())} - {None}
    for k in sorted(karakas):
        emit(graha_target(k), Role.KARAKA, Frame.LAGNA, k)
    # Convert lagna signature signs into Moon-house coordinates FIRST. Never
    # compare Moon-house rule numbers directly with lagna-house signatures.
    moon_houses = {(s - moon) % 12 + 1: s for s in signs.values() if s and moon}
    for r in transit_rules:
        if _subject(r.get('graha')) not in karakas:
            continue
        h = _integer(r.get('primary_house'))
        if not h:
            continue
        if moon and lagna and h not in moon_houses:
            continue
        target = sign_target(moon_houses.get(h), (*lagna_ids, *moon_ids))
        emit(target, Role.TRANSIT, Frame.MOON, h, mechanism=f"transit:{r['id']}",
             rule=f"bg_transit_rules:{r['id']}", provenance=r.get('classical_citation') or '',
             qualifier=r.get('rule_type'))
    positive = {'mrityu_bhaga': {'fired'}, 'gandanta': {'gandanta'},
                'kartari': {'papa_kartari', 'shubha_kartari'}, 'pushkara': {'pushkara'}}
    for r in sensitive:
        if r.get('fact_value_text') in positive.get(r.get('fact_key'), set()):
            emit(graha_target(r['fact_subject'], (str(r['fact_id']),)), Role.SENSITIVE, Frame.ZODIAC,
                 r['fact_id'], provenance='own_extension:sensitive_degree', qualifier=r['fact_key'])
    for r in arudhas:
        sign = sign_num_of(str(r.get('fact_value_text') or ''))
        target = sign_target(sign, (str(r['fact_id']),))
        emit(target, Role.ARUDHA, Frame.ZODIAC, r['fact_id'], provenance='own_extension:arudha')
        emit(target, Role.BHAVA_ARUDHA, Frame.LAGNA, r['fact_subject'], provenance='own_extension:bhava_arudha')
    for h in houses:
        if not any(r['fact_subject'] == f'ARUDHA_A{h}' for r in arudhas):
            emit(None, Role.BHAVA_ARUDHA, Frame.LAGNA, f'ARUDHA_A{h}', provenance='own_extension:bhava_arudha')
    for r in yogas:
        if r.get('fired') is not True:
            continue
        refs = tuple(str(i) for i in r.get('constituent_fact_ids') or ())
        for planet in r.get('constituent_planets') or (None,):
            target = (graha_target(planet, refs) if refs and set(refs) <= by_id.keys() and
                      any(_subject(by_id[ref]['fact_subject']) == _subject(planet) for ref in refs) else None)
            emit(target, Role.YOGA, Frame.ZODIAC, str(planet), mechanism=f"yoga:{r['yoga_canonical_id']}",
                 provenance='own_extension:live_yoga_constituency', qualifier='bhanga_active' if r.get('bhanga_active') else None)
    for lord in sorted(set(dasha_lords)):
        emit(graha_target(lord), Role.DASHA, Frame.ZODIAC, lord, provenance='own_extension:dasha_portfolio')
    for p in promises:
        binding = p.get('binding') or {}
        # No sourced frame or rule: preserve the testimony as unqualified.
        frame = binding.get('frame')
        valid = frame in {f.value for f in Frame} and bool(binding.get('rule_id'))
        for ref in p.get('fact_ids') or ('missing_fact',):
            row = by_id.get(str(ref))
            target = (graha_target(row['fact_subject'], (str(ref),)) if row and valid and
                      row['fact_category'] in {'graha_position', 'graha_sign_attributes', 'graha_nakshatra'} else None)
            emit(target, Role.PROMISE, frame if valid else Frame.ZODIAC, ref,
                 mechanism=p['mechanism_id'], rule=binding.get('rule_id') or p['mechanism_id'],
                 provenance=p.get('source') or '', state='unavailable' if valid else 'unqualified')
    if event_class in M6_EVENT_CLASSES:
        def operand(role: str) -> tuple[int | None, str]:
            if role in {'mandi', 'yamakantaka'}:
                row = find(role.upper(), 'sensitive_point_gulika_mandi', 'sign')
                return (sign_num_of(str(row.get('fact_value_text') or '')) if row else None,
                        'unavailable')
            if role in {'lagna_lord', 'eighth_lord'}:
                h = 1 if role == 'lagna_lord' else 8
                sign = (lagna + h - 2) % 12 + 1 if lagna else None
                if sign is None:
                    return None, 'unavailable'
                if sign not in sign_lords:
                    return None, 'unqualified'
                role = sign_lords.get(sign)
            elif role == 'fifth_star_lord':
                row = find('MOON', 'graha_nakshatra', 'nakshatra_id')
                n = _integer(row.get('fact_value_num'), 27) if row else None
                role = fifth_star_lord(n) if n else None
            subject = _subject(role)
            sign, _ = anchor(subject) if subject else (None, ())
            return sign, 'unavailable'

        def missing_state(*operands: tuple[int | None, str]) -> str:
            # R4: keep missing L0 rulership distinct from missing L1 operands.
            return ('unqualified' if any(sign is None and state == 'unqualified'
                                        for sign, state in operands) else 'unavailable')

        eighth, mandi = operand('eighth_lord'), operand('mandi')
        sign = mandi_distance_target_sign_num(eighth[0], mandi[0]) if eighth[0] and mandi[0] else None
        emit(sign_target(sign, tuple(by_id)), Role.MANDI, Frame.ZODIAC, MANDI_DISTANCE_REF,
             rule=MANDI_DISTANCE_CITATION, provenance=MANDI_DISTANCE_CITATION, qualifier='agent:Saturn',
             state=missing_state(eighth, mandi))
        for formula in YAMAKANTAKA_FORMULAS:
            a, b = operand(formula['minuend']), operand(formula['subtrahend'])
            emit(sign_target(difference_sign_num(a[0], b[0]) if a[0] and b[0] else None, tuple(by_id)),
                 Role.YAMAKANTAKA, Frame.ZODIAC, formula['ref'], rule=formula['citation'],
                 provenance=formula['citation'], qualifier=f"agent:{formula['agent']}",
                 state=missing_state(a, b))
    return Projection(tuple(objects[k] for k in sorted(objects)),
                      tuple(sorted(edges.values(), key=lambda e: (e.role, e.target_ref, e.qualifier or '', e.rule_id, e.edge_id))))
