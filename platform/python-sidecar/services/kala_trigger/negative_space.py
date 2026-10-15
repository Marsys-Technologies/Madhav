"""KYD-134 trigger boundary: no survivor is selected without doctrine admission.

The legacy composition shim remains in trigger.py until K4-2b. This module
neither calls legacy detectors nor converts their numbers or NULLs to facts.
"""
from services.ka_vighnakara.model import Finding, NegativeSpace, interpret


def unavailable_trigger(mechanism_id: str, context: Finding) -> NegativeSpace:
    """Expose the named missing mapping rather than fabricated quiet coverage."""
    if not mechanism_id or not mechanism_id.strip():
        raise ValueError('trigger mechanism id is required')
    if mechanism_id in {'rikta_tithi', 'daily_gandanta', 'kulika', 'transit_combustion'}:
        raise ValueError('non-natal mechanism cannot be requested as a natal trigger')
    finding = Finding.model_validate({**context.model_dump(),
        'mechanism': mechanism_id, 'binding': 'unbound',
        'null_reason': 'trigger_survivor_roster_and_doctrine_unadmitted',
        'knowledge': 'unsearched', 'coverage': 'absent',
        'rule_conclusion': 'none', 'defeat_state': 'unresolved',
        'judge_state': None, 'protections': (), 'release': {'kind': 'unknown'},
    })
    return interpret(finding)
