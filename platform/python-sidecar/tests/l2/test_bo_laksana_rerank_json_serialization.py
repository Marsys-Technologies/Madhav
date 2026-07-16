"""
Regression test — D-2 cycle-1 rebuild incident (build_run ed317097).

bo_laksana_rerank's CR-84 re-rank pass failed on the real deployed rebuild
with `TypeError: Object of type Decimal is not JSON serializable`:
bodha_cgm_nodes' centrality columns are Postgres NUMERIC, so psycopg
returns python Decimal for them, and json.dumps() cannot serialize Decimal
by default. _structural_role_from_centrality already cast every field via
float(c.get(...) or 0.0) internally, but the payload dict written alongside
it (pagerank_score/eigenvector_centrality/betweenness_centrality/
harmonic_centrality) passed the raw Decimal values straight through into
json.dumps(). Fixed to cast each field to float (None-preserving) before
building the payload.
"""
from __future__ import annotations

from decimal import Decimal
import json

from pipeline.orchestrator.writers.bo_laksana import _structural_role_from_centrality


def test_structural_role_handles_decimal_input_without_raising():
    # bodha_cgm_nodes' NUMERIC columns arrive as Decimal via psycopg.
    c = {
        "pagerank_score": Decimal("0.4231"),
        "eigenvector_centrality": Decimal("0.1150"),
        "betweenness_centrality": Decimal("0.0"),
        "harmonic_centrality": Decimal("0.6720"),
    }
    role = _structural_role_from_centrality(c)
    assert isinstance(role, float)
    assert 0.8 <= role <= 1.5


def test_payload_construction_pattern_is_json_serializable_with_decimal_input():
    """Reproduces the exact payload-construction pattern in
    BoLaksanaRerankWriter.run() (bo_laksana.py ~line 3345) with Decimal
    inputs, as the real deployed rebuild's bodha_cgm_nodes rows produce —
    this is the exact shape that raised TypeError before the fix."""
    c = {
        "pagerank_score": Decimal("0.4231"),
        "eigenvector_centrality": Decimal("0.1150"),
        "betweenness_centrality": Decimal("0.0"),
        "harmonic_centrality": Decimal("0.6720"),
    }
    payload = {
        "structural_role_score": _structural_role_from_centrality(c),
        "primary_graha": "Jupiter",
        "pagerank_score": float(c["pagerank_score"]) if c.get("pagerank_score") is not None else None,
        "eigenvector_centrality": float(c["eigenvector_centrality"]) if c.get("eigenvector_centrality") is not None else None,
        "betweenness_centrality": float(c["betweenness_centrality"]) if c.get("betweenness_centrality") is not None else None,
        "harmonic_centrality": float(c["harmonic_centrality"]) if c.get("harmonic_centrality") is not None else None,
        "formula_version": "structural_role_rerank_v1",
        "computed_at": "2026-07-17T00:00:00+00:00",
    }
    # Must not raise TypeError — this is the exact call site that failed live.
    dumped = json.dumps(payload)
    reloaded = json.loads(dumped)
    assert isinstance(reloaded["pagerank_score"], float)
    assert reloaded["pagerank_score"] == 0.4231


def test_payload_construction_handles_none_centrality_fields():
    """A graha with no centrality row yet (None fields) must not raise on
    the None-preserving float cast."""
    c = {
        "pagerank_score": None,
        "eigenvector_centrality": None,
        "betweenness_centrality": None,
        "harmonic_centrality": None,
    }
    payload = {
        "pagerank_score": float(c["pagerank_score"]) if c.get("pagerank_score") is not None else None,
        "eigenvector_centrality": float(c["eigenvector_centrality"]) if c.get("eigenvector_centrality") is not None else None,
        "betweenness_centrality": float(c["betweenness_centrality"]) if c.get("betweenness_centrality") is not None else None,
        "harmonic_centrality": float(c["harmonic_centrality"]) if c.get("harmonic_centrality") is not None else None,
    }
    dumped = json.dumps(payload)  # must not raise
    reloaded = json.loads(dumped)
    assert reloaded["pagerank_score"] is None
