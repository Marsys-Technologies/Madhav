"""
ka_yojaka classifier — maps signal_type_class → signature_class
RATIFIED: L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md §2
"""

SIGNAL_CLASS_MAP = {
    'yoga': 'YOGA',
    'dosha': 'DOSHA',
    'parivartana': 'DISPOSITOR_RELATIONAL',
    'karaka_alignment': 'DISPOSITOR_RELATIONAL',
    'tradition_specific': 'DIGNITY',
    'sade_sati': 'SUBSYSTEM',
    'panchanga': 'SUBSYSTEM',
    'varga_pattern': 'SUBSYSTEM',
    'composite_state': 'SUBSYSTEM',
    'annual': 'SUBSYSTEM',
}


def classify_signal(signal: dict) -> str:
    """Classify a bodha_msr_signals row into a signature_class."""
    stc = signal.get('signal_type_class', '')

    # Direct map first
    if stc in SIGNAL_CLASS_MAP:
        return SIGNAL_CLASS_MAP[stc]

    # 'configuration' needs sub-classification from signal_type_id
    if stc == 'configuration':
        sti = signal.get('signal_type_id', '')
        if 'kala_sarpa' in sti or 'ks_detection' in sti:
            return 'DOSHA'
        if 'conjunction' in sti or 'aspect' in sti:
            return 'CONJUNCTION_ASPECT'
        if any(k in sti for k in ('arudha', 'karakamsa', 'swamsa', 'kp_cusp', 'sensitive')):
            return 'SENSITIVE_POINT'
        return 'CONJUNCTION_ASPECT'  # default for configuration

    # Unknown → CLASSIFY_RESIDUAL
    return 'CLASSIFY_RESIDUAL'
