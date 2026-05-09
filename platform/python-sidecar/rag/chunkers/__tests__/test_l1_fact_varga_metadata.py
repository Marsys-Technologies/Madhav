"""
Tests for rag.chunkers.l1_fact — VARGA-ETL-FULL-S1-CPA D10 metadata.

Verifies that §3.x divisional chart sections receive varga + layer_aspect metadata,
and that §3.15 specifically gets varga="CSI" + layer_aspect="divisional_transition".
"""
from __future__ import annotations


def test_augment_layer_metadata_d9_navamsha():
    from rag.chunkers.l1_fact import _augment_layer_metadata
    meta: dict = {}
    _augment_layer_metadata(meta, "§3.5", "D9 — Navamsa (Dharma / Spouse / General Strength)")
    assert meta.get("varga") == "D9"
    assert meta.get("layer_aspect") == "divisional"


def test_augment_layer_metadata_d10_dashamsha():
    from rag.chunkers.l1_fact import _augment_layer_metadata
    meta: dict = {}
    _augment_layer_metadata(meta, "§3.6", "D10 — Dashamsha (Career / Status)")
    assert meta.get("varga") == "D10"
    assert meta.get("layer_aspect") == "divisional"


def test_augment_layer_metadata_csi_ledger():
    from rag.chunkers.l1_fact import _augment_layer_metadata
    meta: dict = {}
    _augment_layer_metadata(meta, "§3.15", "CSI Ledger — D1→D9 and D1→D10 Comparative Status")
    assert meta.get("varga") == "CSI"
    assert meta.get("layer_aspect") == "divisional_transition"


def test_augment_layer_metadata_dasha_section():
    from rag.chunkers.l1_fact import _augment_layer_metadata
    meta: dict = {}
    _augment_layer_metadata(meta, "§5.1", "Vimshottari Dasha (Mahadasha / Antardasha)")
    assert meta.get("layer_aspect") == "dasha"
    assert "varga" not in meta  # §5.x is dasha-layer, not divisional


def test_augment_layer_metadata_strength_section():
    from rag.chunkers.l1_fact import _augment_layer_metadata
    meta: dict = {}
    _augment_layer_metadata(meta, "§6.4", "Bhavabala (FORENSIC engine — v6.0 sourced)")
    assert meta.get("layer_aspect") == "strength"


def test_augment_layer_metadata_no_match_passes_through():
    from rag.chunkers.l1_fact import _augment_layer_metadata
    meta: dict = {"section_id": "§1.1", "section_title": "Birth Metadata"}
    _augment_layer_metadata(meta, "§1.1", "Birth Metadata")
    # §1.x is not §3, §5, or §6 → no varga or layer_aspect added
    assert "varga" not in meta
    assert "layer_aspect" not in meta


def test_min_body_tokens_lowered_to_12():
    """D11 — MIN_BODY_TOKENS reduced to 12 so tiny §3.1 D2 Hora always chunks."""
    from rag.chunkers import l1_fact
    assert l1_fact.MIN_BODY_TOKENS == 12, (
        f"Expected MIN_BODY_TOKENS=12 (lowered for §3.1 D2 Hora coverage); "
        f"got {l1_fact.MIN_BODY_TOKENS}"
    )
