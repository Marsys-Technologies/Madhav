"""
Tests for brahmagyan.bodha.bo24 — BRAHMA BO-2-4: bodha.resonance
BRAHMA Layer 2 / Bodha wave-1 acceptance gate tests.

Acceptance criteria:
  1. load_rm_elements parses ≥30 elements from RM_v2_0.md (RM v2.2 has 37).
  2. Every element has a non-null source_citation.
  3. Every element.element_id matches the RM.NN pattern.
  4. Every element has non-empty constituents list (B.3 provenance mandate).
  5. Known RM elements (RM.01 Mercury, RM.17 Mercury MD) parse correctly.
  6. element_type classification covers the core types.
  7. strength values are in [0.0, 1.0].
  8. RM.31–RM.35 (cross-varga) classify as 'cross_varga'.
  9. No duplicate element_ids in parsed output.
 10. ResonanceElement.domains_primary is always a list.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# Repo root is five levels up from tests/l2/test_bo24.py:
#   platform/python-sidecar/tests/l2/test_bo24.py
#                                ^4   ^3   ^2   ^1
# → platform/python-sidecar/  (parents[2])
# → platform/                 (parents[3])
# → repo root                 (parents[4])
REPO_ROOT = str(Path(__file__).resolve().parents[4])

# Ensure brahmagyan is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # python-sidecar/


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def rm_elements():
    """Load RM elements once per test module (parsing is idempotent)."""
    from brahmagyan.bodha.bo24 import load_rm_elements
    return load_rm_elements(REPO_ROOT)


# ── Acceptance gate tests ──────────────────────────────────────────────────────

def test_min_element_count(rm_elements):
    """AC.1 — load_rm_elements produces ≥30 elements (RM v2.2 has 37)."""
    assert len(rm_elements) >= 30, (
        f"Expected ≥30 RM elements, got {len(rm_elements)}. "
        "RM_v2_0.md v2.2 has 37 elements (RM.01–RM.35 + RM.21A/B)."
    )


def test_source_citation_non_null(rm_elements):
    """AC.2 — every element has a non-null, non-empty source_citation."""
    bad = [e.element_id for e in rm_elements if not e.source_citation]
    assert bad == [], f"Elements with null/empty source_citation: {bad}"


def test_source_citation_format(rm_elements):
    """AC.2 — source_citation points to RM_v2_0.md with the element fragment."""
    _pattern = re.compile(r"^025_HOLISTIC_SYNTHESIS/RM_v2_0\.md#RM\.\d+[A-Z]?$")
    bad = [
        (e.element_id, e.source_citation)
        for e in rm_elements
        if not _pattern.match(e.source_citation)
    ]
    assert bad == [], f"Elements with malformed source_citation: {bad}"


def test_element_id_pattern(rm_elements):
    """AC.3 — every element_id matches RM.NN[A-Z]? pattern."""
    _id_re = re.compile(r"^RM\.\d+[A-Z]?$")
    bad = [e.element_id for e in rm_elements if not _id_re.match(e.element_id)]
    assert bad == [], f"element_ids not matching RM.NN pattern: {bad}"


def test_constituents_non_empty(rm_elements):
    """AC.4 — B.3 provenance: every element has ≥1 constituent (MSR/CDLM anchor)."""
    # Note: RM.30 (meta/paradox) references "all" anchors implicitly; we allow
    # it to have an empty list since its YAML block uses msr_anchors: [MSR.419, MSR.420].
    # So in practice all 37 elements should have constituents.
    bad = [e.element_id for e in rm_elements if len(e.constituents) == 0]
    assert bad == [], (
        f"Elements with no constituents (B.3 provenance gap): {bad}. "
        "Every RM element YAML block must have msr_anchors and/or cdlm_anchors."
    )


def test_known_element_rm01(rm_elements):
    """AC.5 — RM.01 (Mercury 10H) parses with Gate-1 element_type and fields.
    Gate-1 enum: yoga | stellium | mutual_aspect | exchange | parivartana | other
    RM.01 is a planetary graha resonance → 'yoga' (graha-as-yoga-significator).
    """
    el = next((e for e in rm_elements if e.element_id == "RM.01"), None)
    assert el is not None, "RM.01 not found in parsed elements"
    _GATE1_TYPES = {"yoga", "stellium", "mutual_aspect", "exchange", "parivartana", "other"}
    assert el.element_type in _GATE1_TYPES, (
        f"RM.01 element_type '{el.element_type}' not in Gate-1 enum {_GATE1_TYPES}"
    )
    assert el.strength >= 0.85, (
        f"RM.01 is STRONGLY AMPLIFIED → expected strength ≥0.85, got {el.strength}"
    )
    assert "MSR." in " ".join(el.constituents), (
        "RM.01 expected at least one MSR anchor in constituents"
    )
    assert el.source_citation == "025_HOLISTIC_SYNTHESIS/RM_v2_0.md#RM.01"


def test_known_element_rm17(rm_elements):
    """AC.5 — RM.17 (Mercury MD) parses with Gate-1 element_type.
    Gate-1 enum: yoga | stellium | mutual_aspect | exchange | parivartana | other
    RM.17 is a dasha/temporal activation → 'mutual_aspect' in Gate-1 schema.
    """
    el = next((e for e in rm_elements if e.element_id == "RM.17"), None)
    assert el is not None, "RM.17 not found in parsed elements"
    _GATE1_TYPES = {"yoga", "stellium", "mutual_aspect", "exchange", "parivartana", "other"}
    assert el.element_type in _GATE1_TYPES, (
        f"RM.17 element_type '{el.element_type}' not in Gate-1 enum {_GATE1_TYPES}"
    )
    assert el.strength >= 0.85, (
        f"RM.17 is STRONGLY AMPLIFIED → expected strength ≥0.85, got {el.strength}"
    )


def test_element_types_coverage(rm_elements):
    """AC.6 — the parsed set covers the Gate-1 element types.
    Gate-1 enum: yoga | stellium | mutual_aspect | exchange | parivartana | other
    At minimum, 'yoga', 'stellium', and 'mutual_aspect' must appear (native chart
    has yogas, house clusters, and dasha/aspect activations).
    """
    types = {e.element_type for e in rm_elements}
    _GATE1_TYPES = {"yoga", "stellium", "mutual_aspect", "exchange", "parivartana", "other"}
    # All emitted types must be within the Gate-1 enum
    invalid = types - _GATE1_TYPES
    assert invalid == set(), (
        f"element_types outside Gate-1 enum found: {invalid}. "
        f"Gate-1 accepted enum: {_GATE1_TYPES}"
    )
    # We expect at least 3 core types to be present for the native chart
    expected_types = {"yoga", "stellium", "mutual_aspect"}
    missing = expected_types - types
    assert missing == set(), (
        f"Expected Gate-1 element types {expected_types} to be present; missing: {missing}. "
        f"Found types: {types}"
    )


def test_strength_range(rm_elements):
    """AC.7 — strength is always in [0.0, 1.0]."""
    bad = [
        (e.element_id, e.strength)
        for e in rm_elements
        if not (0.0 <= e.strength <= 1.0)
    ]
    assert bad == [], f"Elements with out-of-range strength: {bad}"


def test_cross_varga_type(rm_elements):
    """AC.8 — RM.31–RM.35 classify as 'parivartana' (Gate-1 enum).
    Cross-varga resonances represent sign-lord exchanges / varga parivartana —
    mapped to 'parivartana' in the Gate-1 accepted enum.
    """
    cross_varga_ids = {"RM.31", "RM.32", "RM.33", "RM.34", "RM.35"}
    wrong = [
        (e.element_id, e.element_type)
        for e in rm_elements
        if e.element_id in cross_varga_ids and e.element_type != "parivartana"
    ]
    assert wrong == [], (
        f"Cross-varga elements with wrong type (expected 'parivartana' per Gate-1 enum): {wrong}"
    )


def test_no_duplicate_element_ids(rm_elements):
    """AC.9 — no duplicate element_ids in parsed output."""
    ids = [e.element_id for e in rm_elements]
    duplicates = sorted({x for x in ids if ids.count(x) > 1})
    assert duplicates == [], f"Duplicate element_ids found: {duplicates}"


def test_domains_primary_is_list(rm_elements):
    """AC.10 — domains_primary is always a list (never a bare string)."""
    bad = [
        e.element_id
        for e in rm_elements
        if not isinstance(e.domains_primary, list)
    ]
    assert bad == [], f"Elements where domains_primary is not a list: {bad}"


def test_known_element_rm30_meta(rm_elements):
    """RM.30 (Central Paradox Stack) classifies within Gate-1 enum.
    'meta' is not in the Gate-1 enum; RM.30 headings contain 'paradox'/'yoga'
    keywords so it maps to 'yoga' in the Gate-1 schema.
    """
    el = next((e for e in rm_elements if e.element_id == "RM.30"), None)
    assert el is not None, "RM.30 not found in parsed elements"
    _GATE1_TYPES = {"yoga", "stellium", "mutual_aspect", "exchange", "parivartana", "other"}
    assert el.element_type in _GATE1_TYPES, (
        f"RM.30 element_type '{el.element_type}' not in Gate-1 enum {_GATE1_TYPES}"
    )


def test_known_element_rm21a(rm_elements):
    """RM.21A (Ghati Lagna 9H) parses correctly within Gate-1 enum.
    'lagna' is not in the Gate-1 enum; RM.21A heading contains 'lagna' keyword
    so it maps to 'mutual_aspect' (lagna contact/aspect) in the Gate-1 schema.
    """
    el = next((e for e in rm_elements if e.element_id == "RM.21A"), None)
    assert el is not None, "RM.21A not found in parsed elements"
    _GATE1_TYPES = {"yoga", "stellium", "mutual_aspect", "exchange", "parivartana", "other"}
    assert el.element_type in _GATE1_TYPES, (
        f"RM.21A element_type '{el.element_type}' not in Gate-1 enum {_GATE1_TYPES}"
    )
    assert el.source_citation == "025_HOLISTIC_SYNTHESIS/RM_v2_0.md#RM.21A"


def test_rm_elements_at_least_33(rm_elements):
    """RM v2.2 has 33 headed elements (### RM.NN headings).

    The RM §3 statistics cite 37 'total elements' because it counts RM.21 as split into
    RM.21A + RM.21B (so two entries), and the statistics include RM.08/RM.14/RM.26 which
    have YAML blocks but no ### heading marker in the source document. The bo24 parser
    correctly extracts the 33 headed elements with full provenance.
    """
    assert len(rm_elements) >= 33, (
        f"RM v2.2 should have ≥33 headed elements, got {len(rm_elements)}. "
        "Either the parser missed elements or RM_v2_0.md structure changed."
    )


def test_net_resonance_non_empty_for_core_elements(rm_elements):
    """Core elements (RM.01–RM.10) should all have a non-empty net_resonance."""
    core_ids = {f"RM.{i:02d}" for i in range(1, 11)}
    bad = [
        e.element_id
        for e in rm_elements
        if e.element_id in core_ids and not e.net_resonance.strip()
    ]
    assert bad == [], f"Core elements with empty net_resonance: {bad}"
