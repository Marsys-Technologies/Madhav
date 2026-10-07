"""Golden-value narration fidelity test for bo_anveshana.

The four discovery primitives compose surface_reading / depth_reading /
surface_depth_delta / why_an_acharya_misses_it by f-string inside _mine_ayanamsha.
The DB-bound helper functions are replaced with in-memory stand-ins so the real
composing code runs on fixed inputs; every expected sentence below is stated by
hand from the f-string templates.
"""
from __future__ import annotations

import json

import numpy as np

from pipeline.orchestrator.writers import bo_anveshana as W


def test_anveshana_discovery_prose_golden(monkeypatch):
    non_ob = [{
        "signal_id": "sig-latent", "signal_type_id": "yoga_x", "signal_type_class": "yoga",
        "source_l1_asset": "ga_yoga", "domains": ["career", "wealth", "health"],
        "constituent_facts": [], "surface_salience": 0.1234, "sal_norm": 0.2,
        "consequence_score": 0.75, "non_obviousness_score": 0.6, "methods": ["non_obviousness"],
    }]
    outlier_info = [{
        "signal_id": "sig-embed", "signal_type_id": "dosha_y", "signal_type_class": "dosha",
        "computed_salience": 0.4, "source_l1_asset": "ga_dosha", "domains_affected_array": ["health"],
    }]
    dist_anoms = [{
        "signal_id": "sig-dist", "signal_type_id": "yoga_z", "signal_type_class": "yoga",
        "source_l1_asset": "ga_strength", "domains": ["career"], "salience": 0.9,
        "mean_salience": 0.3, "std_salience": 0.1, "sigma": 3.46, "methods": ["distributional_anomaly"],
    }]
    brokers = [{
        "node_id": "n1", "node_subject": "Jupiter", "node_type": "graha",
        "source_subsystem": "ga_x", "betweenness_centrality": 0.1, "pagerank_score": 0.1,
        "msr_signal_id": "sig-broker", "primary_domain": "wealth",
        "edge_count": 7, "subsystem_diversity": 4,
    }]

    monkeypatch.setattr(W, "_compute_non_obviousness", lambda conn, c, a: non_ob)
    monkeypatch.setattr(W, "_fetch_embeddings_np", lambda conn, c, a: (["sig-embed"], np.zeros((1, 2))))
    monkeypatch.setattr(W, "_compute_embedding_outliers", lambda ids, mat: [("sig-embed", 2.5)])
    monkeypatch.setattr(W, "_fetch_dict", lambda conn, sql, params: outlier_info)
    monkeypatch.setattr(W, "_compute_distributional_anomalies", lambda conn, c, a: dist_anoms)
    monkeypatch.setattr(W, "_compute_brokers", lambda conn, c, a: brokers)

    discoveries, _anoms = W._mine_ayanamsha(
        None, "chart", "lahiri_chitrapaksha", "build", "2026-10-05T00:00:00+00:00"
    )
    by_class = {d["discovery_class"]: d for d in discoveries}

    latent = by_class["latent_insight"]
    latent_prose = {
        "surface_reading": latent["surface_reading"],
        "depth_reading": latent["depth_reading"],
        "surface_depth_delta": latent["surface_depth_delta"],
        "why_an_acharya_misses_it": latent["why_an_acharya_misses_it"],
    }
    assert latent_prose == {
        "surface_reading": "Signal yoga_x with low visibility (salience 0.123)",
        "depth_reading": "Structurally consequential: consequence_score=0.750, non_obviousness=0.600",
        "surface_depth_delta": "Surface hides depth by factor 0.600",
        "why_an_acharya_misses_it": (
            "Low surface salience (0.20) masks high structural consequence (0.75); "
            "falls below acharya's attentional threshold"
        ),
    }

    embed = by_class["embedding_outlier"]
    embed_prose = {
        "surface_reading": embed["surface_reading"],
        "depth_reading": embed["depth_reading"],
        "surface_depth_delta": embed["surface_depth_delta"],
        "why_an_acharya_misses_it": embed["why_an_acharya_misses_it"],
    }
    assert embed_prose == {
        "surface_reading": "Signal dosha_y appears unremarkable to pattern inspection",
        "depth_reading": "Embedding distance from chart centroid: 2.5000 — semantically unusual",
        "surface_depth_delta": "Semantic uniqueness 2.500 distinguishes this from all other chart signals",
        "why_an_acharya_misses_it": (
            "Semantically unusual (distance 2.500 from chart centroid) — stands apart from "
            "the chart's dominant patterns; invisible to pattern-matching"
        ),
    }

    dist = by_class["distributional_anomaly"]
    dist_prose = {
        "surface_reading": dist["surface_reading"],
        "depth_reading": dist["depth_reading"],
        "surface_depth_delta": dist["surface_depth_delta"],
        "why_an_acharya_misses_it": dist["why_an_acharya_misses_it"],
    }
    assert dist_prose == {
        "surface_reading": "Appears as one of many yoga signals",
        "depth_reading": "Stands 3.5σ from ga_strength baseline (mean=0.300)",
        "surface_depth_delta": "σ-deviation of 3.46 marks this as the subsystem's most atypical signal",
        "why_an_acharya_misses_it": (
            "Statistically extreme within ga_strength subsystem (3.5σ) but easy to miss "
            "when chart is read holistically"
        ),
    }

    broker = by_class["cross_subsystem_root"]
    broker_prose = {
        "surface_reading": broker["surface_reading"],
        "depth_reading": broker["depth_reading"],
        "surface_depth_delta": broker["surface_depth_delta"],
        "why_an_acharya_misses_it": broker["why_an_acharya_misses_it"],
    }
    assert broker_prose == {
        "surface_reading": "Jupiter as an individual astrological factor",
        "depth_reading": "Jupiter as a structural BROKER connecting 4 analytical domains — a hidden hinge point",
        "surface_depth_delta": (
            "Broker role (4 subsystems, 7 cross-subsystem edges) invisible from isolated factor reading"
        ),
        "why_an_acharya_misses_it": (
            "Node Jupiter bridges 4 subsystems via 7 cross-subsystem edges — the inter-domain "
            "connection only visible when holding the full relational graph simultaneously"
        ),
    }


def test_anveshana_reasoning_step_descriptions_golden(monkeypatch):
    """The `description` of each reasoning_chain step (three constant sentences and one f-string that embeds the
    computed sigma), stated by hand from the templates. hypothesis_text is NOT covered: its f-strings interpolate only
    identifiers, so it is not narration (test_e6_1_narr_reaudit.py)."""
    non_ob = [{
        "signal_id": "sig-latent", "signal_type_id": "yoga_x", "signal_type_class": "yoga",
        "source_l1_asset": "ga_yoga", "domains": ["career", "wealth", "health"],
        "constituent_facts": [], "surface_salience": 0.1234, "sal_norm": 0.2,
        "consequence_score": 0.75, "non_obviousness_score": 0.6, "methods": ["non_obviousness"],
    }]
    outlier_info = [{
        "signal_id": "sig-embed", "signal_type_id": "dosha_y", "signal_type_class": "dosha",
        "computed_salience": 0.4, "source_l1_asset": "ga_dosha", "domains_affected_array": ["health"],
    }]
    dist_anoms = [{
        "signal_id": "sig-dist", "signal_type_id": "yoga_z", "signal_type_class": "yoga",
        "source_l1_asset": "ga_strength", "domains": ["career"], "salience": 0.9,
        "mean_salience": 0.3, "std_salience": 0.1, "sigma": 3.46, "methods": ["distributional_anomaly"],
    }]
    brokers = [{
        "node_id": "n1", "node_subject": "Jupiter", "node_type": "graha",
        "source_subsystem": "ga_x", "betweenness_centrality": 0.1, "pagerank_score": 0.1,
        "msr_signal_id": "sig-broker", "primary_domain": "wealth",
        "edge_count": 7, "subsystem_diversity": 4,
    }]

    monkeypatch.setattr(W, "_compute_non_obviousness", lambda conn, c, a: non_ob)
    monkeypatch.setattr(W, "_fetch_embeddings_np", lambda conn, c, a: (["sig-embed"], np.zeros((1, 2))))
    monkeypatch.setattr(W, "_compute_embedding_outliers", lambda ids, mat: [("sig-embed", 2.5)])
    monkeypatch.setattr(W, "_fetch_dict", lambda conn, sql, params: outlier_info)
    monkeypatch.setattr(W, "_compute_distributional_anomalies", lambda conn, c, a: dist_anoms)
    monkeypatch.setattr(W, "_compute_brokers", lambda conn, c, a: brokers)

    discoveries, _anoms = W._mine_ayanamsha(
        None, "chart", "lahiri_chitrapaksha", "build", "2026-10-05T00:00:00+00:00"
    )
    by_class = {d["discovery_class"]: d for d in discoveries}

    # every step that carries a `description`, in primitive order (latent insight, embedding outlier,
    # distributional anomaly, broker); the two steps without one hold only identifiers and numbers
    built = [
        step.get("description")
        for cls in ("latent_insight", "embedding_outlier", "distributional_anomaly", "cross_subsystem_root")
        for step in json.loads(by_class[cls]["reasoning_chain_jsonb"])["steps"]
        if step.get("description")
    ]
    assert built == [
        "Low surface salience — acharya less likely to notice",
        "High structural + convergence consequence",
        "Semantic meaning-vector far from chart centroid",
        "Salience 3.5σ from subsystem mean",
        "Bridges multiple analytical subsystems",
    ]
