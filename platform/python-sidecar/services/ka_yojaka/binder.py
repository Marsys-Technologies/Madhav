"""
ka_yojaka binder — instantiates RATIFIED template for a given signature_class
RATIFIED: L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2 (FROZEN, READ-ONLY)
"""
from typing import Any


def _extract_constituent_lords(signal: dict) -> list:
    """Best-effort extraction of constituent lords from configuration_jsonb.

    CR-37 (SARVA-SIDDHI W-1 T-3) root-cause fix: the previous implementation,
    when configuration_jsonb carried no graha-valued key (the case for EVERY
    `yoga_label:yoga_name` MSR signal — their config holds only yoga_name +
    citations), fell back to `constituent_facts_array[:10]` and dumped those
    values verbatim into `constituent_lords`. But `constituent_facts_array`
    holds L1 `chart_facts.fact_id` HASHES (e.g. '050b754375d2181d'), not graha
    names — so downstream `date_resolver.normalize_graha` rejected every one of
    them, no daśā period ever matched, and 100% of yoga_label activations came
    out UNDATED. Worse, because the returned list was non-empty, it suppressed
    ka_yojaka's own `if not existing_lords` lord-enrichment chain, so the
    authoritative forming-graha source was never consulted. Dropping the
    fact-id fallback here lets ka_yojaka resolve real forming grahā(s) from
    L1 `ga_yoga_firings.constituent_planets` (see ka_yojaka.py CR-37 block).
    No fabrication (B.10): a fact-id hash was never a valid lord.
    """
    cfg = signal.get('configuration_jsonb') or {}
    lords = []
    if isinstance(cfg, dict):
        for key in ('grahas', 'lords', 'planets', 'constituent_lords', 'graha'):
            val = cfg.get(key)
            if isinstance(val, list):
                lords.extend(str(v) for v in val)
            elif isinstance(val, str):
                lords.append(val)
    return lords


def _build_yoga(signal: dict) -> dict:
    lords = _extract_constituent_lords(signal)
    return {
        'dasha_eligibility_rule': {
            'type': 'dasha_lord_in_constituents',
            'match': 'MD_or_AD_lord IN constituent_lords OR dispositors OR house_lords',
            'constituent_lords': lords,
            'strength_ranking': ['exact_lord', 'dispositor', 'house_lord'],
        },
        'transit_trigger': {
            'type': 'benefic_transit_to_kendra_trikona',
            'trigger_events': [
                'constituent_lord_ingress_kendra_trikona',
                'benefic_transit_conjoin_yoga_lord',
                'constituent_lord_return',
            ],
            'kendra': [1, 4, 7, 10],
            'trikona': [1, 5, 9],
            'orb_deg': 1.0,
        },
        'strength_affliction_hook': {
            'scale_by': 'dignity_score',
            'veto_if': 'combust OR dusthana_transit OR malefic_conjunction',
        },
        'derivation_ledger': {
            'bg_transit_rules_ids': [1, 2, 3, 4],
            'template_version': 'v1.0',
            'ratified_by': 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2',
        },
    }


def _build_dosha(signal: dict) -> dict:
    return {
        'dasha_eligibility_rule': {
            'type': 'afflicting_lord_dasha',
            'match': 'MD_or_AD lord IN afflicting_grahas OR afflicted_bhava_lord',
        },
        'transit_trigger': {
            'type': 'malefic_transit_over_afflicted_point',
            'trigger_events': ['saturn_over_afflicted', 'rahu_station', 'eclipse_on_point'],
        },
        'strength_affliction_hook': {
            'severity_scale': 'affliction_count',
            'mitigate_if': 'strong_benefic_aspects',
        },
        'derivation_ledger': {
            'bg_transit_rules_ids': [5, 6, 7],
            'template_version': 'v1.0',
            'ratified_by': 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2',
        },
    }


def _build_dignity(signal: dict) -> dict:
    return {
        'dasha_eligibility_rule': {
            'type': 'own_dasha',
            'match': 'MD_or_AD lord = the graha itself OR dispositor',
        },
        'transit_trigger': {
            'type': 'graha_activation',
            'trigger_events': ['benefic_aspect_to_graha', 'graha_return', 'ingress_dignity_sign'],
        },
        'strength_affliction_hook': {
            'scale_by': 'dignity_score',
            'neechabhanga_boost': True,
        },
        'derivation_ledger': {
            'bg_transit_rules_ids': [1, 2, 3, 8, 9, 10],
            'template_version': 'v1.0',
            'ratified_by': 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2',
        },
    }


def _build_dispositor_relational(signal: dict) -> dict:
    return {
        'dasha_eligibility_rule': {
            'type': 'related_lords_dasha',
            'match': 'MD_or_AD lord IN related_lords',
        },
        'transit_trigger': {
            'type': 'relational_link_transit',
            'trigger_events': ['lord_transits_other_bhava', 'aspect_completing_exchange'],
        },
        'strength_affliction_hook': {
            'scale_by': 'composite_dispositor_strength',
            'dampen_if': 'either_lord_afflicted',
        },
        'derivation_ledger': {
            'bg_transit_rules_ids': [1, 2, 3],
            'template_version': 'v1.0',
            'ratified_by': 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2',
        },
    }


def _build_sensitive_point(signal: dict) -> dict:
    return {
        'dasha_eligibility_rule': {
            'type': 'significator_dasha',
            'match': 'MD_or_AD lord = significator of sensitive point',
        },
        'transit_trigger': {
            'type': 'transit_over_sensitive_point',
            'trigger_events': ['planet_conjoin_point', 'planet_station_on_point'],
            'orb_deg': 1.0,
        },
        'strength_affliction_hook': {
            'scale_by': 'transiting_graha_nature',
            'benefic_trigger': 'opportune',
            'malefic_trigger': 'caution',
        },
        'derivation_ledger': {
            'bg_transit_rules_ids': [1, 8],
            'template_version': 'v1.0',
            'ratified_by': 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2',
        },
    }


def _build_conjunction_aspect(signal: dict) -> dict:
    return {
        'dasha_eligibility_rule': {
            'type': 'natal_pair_dasha',
            'match': 'MD_or_AD lord IN natal_pair',
        },
        'transit_trigger': {
            'type': 'transit_reforms_natal_aspect',
            'trigger_events': ['transit_reforms_angle', 'transit_reconjoins_natal_pair'],
            'aspect_degrees': [0, 60, 90, 120, 180],
        },
        'strength_affliction_hook': {
            'scale_by': 'orb_strength',
            'applying_weight': 1.0,
            'separating_weight': 0.7,
        },
        'derivation_ledger': {
            'bg_transit_rules_ids': [1, 5],
            'template_version': 'v1.0',
            'ratified_by': 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2',
        },
    }


def _build_subsystem(signal: dict) -> dict:
    stc = signal.get('signal_type_class', 'subsystem')
    return {
        'dasha_eligibility_rule': {
            'type': 'subsystem_specific',
            'subsystem': stc,
        },
        'transit_trigger': {
            'type': 'subsystem_trigger',
            'subsystem': stc,
        },
        'strength_affliction_hook': {
            'scale_by': 'subsystem_severity',
        },
        'derivation_ledger': {
            'bg_transit_rules_ids': [],
            'template_version': 'v1.0',
            'ratified_by': 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2',
        },
    }


def _build_classify_residual(signal: dict) -> dict:
    return {
        'dasha_eligibility_rule': {'type': 'unclassified'},
        'transit_trigger': {'type': 'unclassified'},
        'strength_affliction_hook': {'scale_by': 'none'},
        'derivation_ledger': {
            'bg_transit_rules_ids': [],
            'template_version': 'v1.0',
            'ratified_by': 'L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2',
        },
    }


_BUILDERS = {
    'YOGA': _build_yoga,
    'DOSHA': _build_dosha,
    'DIGNITY': _build_dignity,
    'DISPOSITOR_RELATIONAL': _build_dispositor_relational,
    'SENSITIVE_POINT': _build_sensitive_point,
    'CONJUNCTION_ASPECT': _build_conjunction_aspect,
    'SUBSYSTEM': _build_subsystem,
    'CLASSIFY_RESIDUAL': _build_classify_residual,
}


def build_predicate(signal: dict, signature_class: str) -> dict:
    """
    Instantiate the RATIFIED template for the given signature_class.
    Returns dict with keys: dasha_eligibility_rule, transit_trigger,
    strength_affliction_hook, derivation_ledger.
    """
    builder = _BUILDERS.get(signature_class, _build_classify_residual)
    return builder(signal)
