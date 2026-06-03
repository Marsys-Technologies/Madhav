"""
brahmagyan.phala — Brahma L4 Phala (Outcome) layer.

Sub-packages:
    anchors       — phala.anchors (PH-4-1)
                    Calibrated probabilistic event anchors.
    mitigation    — phala.mitigation (PH-4-2)
                    BPHS-grounded classical remedies per anchor.
    rectification — phala.rectification (PH-4-3)
                    Birth-time rectification via held-out LEL train/test split.
    muhurta       — phala.muhurta (PH-4-4)
                    Electional finder — inverts Phala prediction engine.
                    For each 48-hour window in date_range, computes:
                        auspiciousness_score = panchanga_quality(40%)
                                             + dasha_quality(30%)
                                             + transit_quality(20%)
                                             + signal_activation(10%)
                    action_types: marriage|travel|business|medical|education|property|general
                    BRAHMA-PH-4-4
    outlook       — phala.outlook (PH-4-5)
                    Composite predictive bundle — B.11 L4 entrypoint.
                    Aggregates PH-4-1 + PH-4-2 + PH-4-3 + PH-4-4 into one call.
"""
