"""Fingerprint the ordered inputs to the positional Sangam resume ledger."""

from collections.abc import Sequence
from datetime import date, datetime
import hashlib
import json
from uuid import UUID


def _check_json(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError
            _check_json(item)
    elif isinstance(value, list):
        for item in value:
            _check_json(item)
    elif value is not None and type(value) not in (str, bool, int, float):
        raise ValueError


def _rule(value):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError
    _check_json(value)
    return value


def _optional_text(value):
    if value is not None and not isinstance(value, str):
        raise ValueError
    return value


def _predicate(row):
    signal_id = row.get('signal_id')
    if isinstance(signal_id, UUID):
        signal_id = str(signal_id)
    dignity = row.get('dignity_score', 0.5)
    if type(dignity) not in (int, float):
        raise ValueError
    return {
        'signal_id': _optional_text(signal_id),
        'signature_class': _optional_text(row.get('signature_class', 'UNKNOWN')),
        'ayanamsha_id': _optional_text(row.get('ayanamsha_id')),
        'dignity_score': float(dignity),
        'primary_domain': _optional_text(row.get('primary_domain')),
        'domain_lord': _optional_text(row.get('domain_lord')),
        'graha_name': _optional_text(row.get('graha_name')),
        'dispositor_lord': _optional_text(row.get('dispositor_lord')),
        'dasha_rule': _rule(row.get('dasha_eligibility_rule_jsonb')),
        'transit_trigger': _rule(row.get('transit_trigger_jsonb')),
    }


def _effective_day(value):
    if isinstance(value, datetime):
        value = value.date()
    if value is not None and not isinstance(value, date):
        raise ValueError
    return value.isoformat() if value is not None else None


def _native(context):
    if context is None:
        return None
    location = context.location
    lat, lon, offset = location['lat'], location['lon'], location['tz_offset_minutes']
    nakshatra = context.janma_nakshatra_idx
    if (type(nakshatra) is not int or type(offset) is not int
            or type(lat) not in (int, float) or type(lon) not in (int, float)):
        raise ValueError
    return [nakshatra, _optional_text(context.moon_sign), lat, lon, offset]


def _enrichment(context):
    if context is None:
        return None
    sarva = context.ashtakavarga_bindu.get('SARVA', {})
    # Mode D iterates this mapping, so preserve its sign order.
    if any(type(sign) is not int or type(bindu) is not int for sign, bindu in sarva.items()):
        raise ValueError
    return {
        'sarva': list(sarva.items()),
        'vedha': [
            [_optional_text(row.get('graha') or row.get('planet')),
             _effective_day(row.get('window_start')), _effective_day(row.get('window_end'))]
            for row in context.vedha_rules
        ],
        'tajika': [
            [_effective_day(row.get('varsha_start')), _effective_day(row.get('varsha_end')),
             _optional_text(row.get('varshesha')), _optional_text(row.get('muntha'))]
            for row in context.tajika_year_lords
        ],
        'school_consensus': _rule(context.school_consensus_by_domain),
    }


def plan_fingerprint(
    *, version: int, chart_id: str, generation: str, run_id: str, today: date,
    birth_year: int | None, near: Sequence[dict], lifetime: Sequence[dict],
    near_mode_d: int | None, lifetime_mode_d: int | None, native_context,
    enrichment_context, gochara_available: bool, muhurta_available: bool,
) -> str:
    """Encode selected inputs without re-ranking them or serializing runtime state."""
    try:
        if (not isinstance(chart_id, (str, UUID)) or not str(chart_id)
                or not isinstance(generation, str) or not generation
                or not isinstance(run_id, str) or not isinstance(today, date)
                or (birth_year is not None and type(birth_year) is not int)):
            raise ValueError
        for rows, carrier in ((near, near_mode_d), (lifetime, lifetime_mode_d)):
            if carrier is not None and (type(carrier) is not int or not 0 <= carrier < len(rows)):
                raise ValueError
        payload = {
            'version': f'ka-sangam-resume-v{version}',
            'chart': str(chart_id),
            'generation': generation,
            'run': run_id,
            'today': _effective_day(today),
            'birth_year': birth_year,
            'near': [_predicate(row) for row in near],
            'lifetime': [[f'lifetime:{index}', _predicate(row)] for index, row in enumerate(lifetime)],
            'mode_d': [near_mode_d, lifetime_mode_d],
            'native': _native(native_context),
            'enrichment': _enrichment(enrichment_context),
            'gochara_available': gochara_available,
            'muhurta_available': muhurta_available,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (AttributeError, KeyError, OverflowError, RecursionError, TypeError, ValueError):
        raise ValueError('ka_sangam: malformed resume identity') from None
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()
