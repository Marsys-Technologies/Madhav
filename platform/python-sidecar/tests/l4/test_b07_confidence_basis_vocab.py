"""
B-07 golden tests — confidence_basis named constants (§N.4, CLAUDE.md).

Finding F-68: 'structural_not_yet_empirical' was spelled as a bare string literal
in ph_nimitta/engine.py, ph_sankrama/engine.py, and ph_sodhana/engine.py.
These tests enforce the fix: the string is defined once as a named constant in
brahmagyan.phala.confidence_vocab and all emission sites import + use it.

TDD order: tests were written first (RED), then the implementation (GREEN).
"""
from __future__ import annotations

import ast
import textwrap
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import the constants we require to exist (will fail until the module is created)
# ---------------------------------------------------------------------------
from brahmagyan.phala.confidence_vocab import (
    STRUCTURAL_NOT_YET_EMPIRICAL,
    CALIBRATED_EMPIRICAL,
)


# ---------------------------------------------------------------------------
# 1. Canonical string values
# ---------------------------------------------------------------------------

def test_STRUCTURAL_NOT_YET_EMPIRICAL_matches_expected_string():
    assert STRUCTURAL_NOT_YET_EMPIRICAL == 'structural_not_yet_empirical'


def test_CALIBRATED_EMPIRICAL_matches_expected_string():
    assert CALIBRATED_EMPIRICAL == 'calibrated_empirical'


# ---------------------------------------------------------------------------
# 2. ph_nimitta/engine.py: AnchorRecord.confidence_basis default uses the constant
# ---------------------------------------------------------------------------

def test_nimitta_engine_default_uses_constant_not_literal():
    """AnchorRecord().confidence_basis must equal STRUCTURAL_NOT_YET_EMPIRICAL.

    AnchorRecord has one required positional field: anchor_source.
    All other fields (including confidence_basis) have defaults.
    """
    from services.ph_nimitta.engine import AnchorRecord
    record = AnchorRecord(anchor_source='convergence')
    assert record.confidence_basis == STRUCTURAL_NOT_YET_EMPIRICAL


# ---------------------------------------------------------------------------
# 3. ph_sodhana/engine.py: no bare 'structural_not_yet_empirical' string literal
# ---------------------------------------------------------------------------

def test_sodhana_leakage_check_uses_constant_not_literal():
    """
    ph_sodhana/engine.py must not contain the bare string literal
    'structural_not_yet_empirical' (i.e. "'structural_not_yet_empirical'" in source).
    After the fix only the imported constant name should appear.
    """
    engine_path = (
        Path(__file__).parent.parent.parent
        / 'services' / 'ph_sodhana' / 'engine.py'
    )
    source = engine_path.read_text(encoding='utf-8')
    # A bare string literal looks like: 'structural_not_yet_empirical'
    # After the fix the source should reference only the constant name.
    assert "'structural_not_yet_empirical'" not in source, (
        "ph_sodhana/engine.py still contains the bare string literal "
        "'structural_not_yet_empirical'. Replace it with the imported "
        "STRUCTURAL_NOT_YET_EMPIRICAL constant from brahmagyan.phala.confidence_vocab."
    )


# ---------------------------------------------------------------------------
# 4. ph_sankrama/engine.py: SankramaRecord.confidence_basis default uses the constant
# ---------------------------------------------------------------------------

def test_sankrama_engine_default_uses_constant():
    """SankramaRecord.confidence_basis field default must equal STRUCTURAL_NOT_YET_EMPIRICAL."""
    from services.ph_sankrama.engine import SankramaRecord
    from datetime import date
    record = SankramaRecord(
        source_anchor_id='src',
        cdlm_cell_id=None,
        source_domain='career',
        target_domain='wealth',
        relationship_type='contagion',
        linkage_strength=0.5,
        asymmetry_score=0.0,
        trajectory='stable',
        bridge_path_jsonb={},
        mechanism_text='test',
        source_window_start=None,
        source_window_end=None,
        projected_window_start=None,
        projected_window_end=None,
        projected_peak_date=None,
        cascade_chain_jsonb=None,
        cascade_depth=0,
        spillover_confidence=0.5,
    )
    assert record.confidence_basis == STRUCTURAL_NOT_YET_EMPIRICAL
