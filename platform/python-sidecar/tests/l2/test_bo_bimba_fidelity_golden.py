"""Golden-value fidelity test for bo_bimba narration (citation_human).

The yoga/dosha node citation is the sentence "<Class> node: <name>" where Class is
the capitalized signal class ('yoga' -> 'Yoga', 'dosha' -> 'Dosha') and name is the
configuration's human name (first non-empty of fact_value_text, yoga_name,
dosha_name, name, label). Expected sentences below are stated by hand.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.bo_bimba import _build_nodes_for_aya


def _sig(signal_id: str, sig_class: str, cfg: dict) -> dict:
    return {
        "signal_id": signal_id,
        "signal_type_id": f"{sig_class}_type",
        "signal_type_class": sig_class,
        "configuration_jsonb": cfg,
        "computed_salience": 0.7,
        "domains_affected_array": ["career"],
        "signal_tradition": "parashari",
        "verification_pass_status": "single_pass",
    }


def test_yoga_and_dosha_node_citation_human_names_class_and_configuration() -> None:
    signals = [
        _sig("sig-yoga-1", "yoga", {"yoga_name": "Gajakesari Yoga"}),
        _sig("sig-dosha-1", "dosha", {"dosha_name": "Kemadruma Dosha"}),
    ]
    nodes = _build_nodes_for_aya(
        "chart-1", "lahiri", "build-1", signals, "2026-01-01T00:00:00+00:00"
    )
    by_type = {n["node_type"]: n for n in nodes if n["node_type"] in ("yoga", "dosha")}

    yoga_row = by_type["yoga"]
    dosha_row = by_type["dosha"]
    citation_human = yoga_row["citation_human"]
    assert citation_human == "Yoga node: Gajakesari Yoga"
    assert dosha_row["citation_human"] == "Dosha node: Kemadruma Dosha"
