"""K3-1b binding scaffold; no producer is admitted or evaluated here."""
import json
from pathlib import Path
from typing import Literal

from services.kala_core.assertion import Ref, Typed
from services.ka_vighnakara.model import Finding, NegativeSpace, interpret


CONTRACT_PATH = Path(__file__).parents[1] / 'ka_vighnakara/input_contract_v1.json'
BindingId = Literal['judge_vedha', 'F1', 'F2', 'trigger_mechanisms']


class UnboundBinding(Typed):
    """Only the current refusal contract; source mappings await admission."""
    state: Literal['unbound']
    reason: Ref

def load_unbound_binding(binding_id: BindingId) -> UnboundBinding:
    """Read the versioned artifact each time; never invent a fallback mapping.

    A future bound state requires its own admitted producer implementation.
    This scaffold refuses it rather than treating it as evaluated coverage.
    """
    if binding_id not in {'judge_vedha', 'F1', 'F2', 'trigger_mechanisms'}:
        raise ValueError(f'unknown live binding: {binding_id}')
    contract = json.loads(CONTRACT_PATH.read_text())
    binding = contract['live_bindings'][binding_id]
    return UnboundBinding.model_validate({'state': binding.get('state'),
                                         'reason': binding.get('reason')})


def unavailable_binding(binding_id: BindingId, context: Finding,
                        *, mechanism_id: str | None = None) -> NegativeSpace:
    """Carry the named binding hole with the request's candidate identity."""
    binding = load_unbound_binding(binding_id)
    finding = Finding.model_validate({**context.model_dump(),
        'mechanism': mechanism_id if mechanism_id is not None else context.mechanism,
        'binding': binding.state, 'null_reason': binding.reason,
        'knowledge': 'unsearched', 'coverage': 'absent',
        'rule_conclusion': 'none', 'defeat_state': 'unresolved',
        'judge_state': None, 'protections': (), 'release': {'kind': 'unknown'},
    })
    result = interpret(finding)
    if result is None:
        raise ValueError('non-natal mechanism cannot be requested as a natal trigger')
    return result


def unavailable_trigger(mechanism_id: str, context: Finding) -> NegativeSpace:
    """Every unadmitted trigger stays unavailable with its contract reason."""
    if not mechanism_id or not mechanism_id.strip():
        raise ValueError('trigger mechanism id is required')
    if mechanism_id in {'rikta_tithi', 'daily_gandanta', 'kulika', 'transit_combustion'}:
        raise ValueError('non-natal mechanism cannot be requested as a natal trigger')
    return unavailable_binding('trigger_mechanisms', context, mechanism_id=mechanism_id)
