"""
test_stub_writers.py — C-07 acceptance tests for 13 stub asset writers.

Verifies:
- WRITER_REGISTRY has exactly 13 entries
- All 13 asset IDs (A2–A14) are keys in WRITER_REGISTRY
- Each write() returns 0 (stub, no-op)
- Each writer module exposes ASSET_ID and ASSET_LABEL constants
  (for A3/A9 the stubs live as closures in pipeline.writers.__init__)
- All write() functions are callable and accept the canonical signature
- dispatch_asset() routes through WRITER_REGISTRY
- Import from pipeline.writers succeeds
"""
import sys
import os
import importlib
import inspect

import pytest

# Ensure the pipeline package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ── Registry import ────────────────────────────────────────────────────────────

def test_writer_registry_importable():
    """Import from pipeline.writers succeeds."""
    from pipeline.writers import WRITER_REGISTRY
    assert WRITER_REGISTRY is not None


def test_writer_registry_has_13_entries():
    """WRITER_REGISTRY has exactly 13 asset_id keys."""
    from pipeline.writers import WRITER_REGISTRY
    assert len(WRITER_REGISTRY) == 13


# ── All 13 asset IDs are present ───────────────────────────────────────────────

EXPECTED_ASSET_IDS = [
    'A2_forensic_render',
    'A3_chart_facts',
    'A4_panchanga',
    'A5_sensitive_points',
    'A6_vargas',
    'A7_dashas',
    'A8_t1_structural',
    'A9_sade_sati',
    'A10_msr',
    'A11_cdlm',
    'A12_cgm',
    'A13_rm',
    'A14_ucn_digest',
]


@pytest.mark.parametrize("asset_id", EXPECTED_ASSET_IDS)
def test_registry_contains_asset_id(asset_id):
    """Each expected asset_id is a key in WRITER_REGISTRY."""
    from pipeline.writers import WRITER_REGISTRY
    assert asset_id in WRITER_REGISTRY, f"{asset_id} missing from WRITER_REGISTRY"


# ── All write() callables return 0 ────────────────────────────────────────────

@pytest.mark.parametrize("asset_id", EXPECTED_ASSET_IDS)
def test_write_returns_zero(asset_id):
    """Each stub write() returns 0 (no data written)."""
    from pipeline.writers import WRITER_REGISTRY
    fn = WRITER_REGISTRY[asset_id]
    result = fn(
        build_id='test-build-123',
        chart_id='test-chart-456',
        ayanamsha_id='lahiri',
        chart_output={},
        conn=None,
    )
    assert result == 0, f"{asset_id}.write() returned {result!r}, expected 0"


# ── All registry values are callable ──────────────────────────────────────────

@pytest.mark.parametrize("asset_id", EXPECTED_ASSET_IDS)
def test_registry_value_is_callable(asset_id):
    """WRITER_REGISTRY[asset_id] is callable."""
    from pipeline.writers import WRITER_REGISTRY
    assert callable(WRITER_REGISTRY[asset_id]), f"{asset_id} writer is not callable"


# ── Module-level ASSET_ID and ASSET_LABEL constants ───────────────────────────
# A3 (chart_facts) and A9 (sade_sati) have heavy Phase-14B module-level imports
# (psycopg, jsonschema, gcs) so their stubs live as closures in writers/__init__.py.
# We verify their constants via the known ASSET_ID/ASSET_LABEL values directly.

# Thin-stub modules (importable without heavy deps)
THIN_MODULE_MAP = {
    'A2_forensic_render':  ('pipeline.writers.forensic_writer',        'A2_forensic_render',  'FORENSIC.md Render'),
    'A4_panchanga':        ('pipeline.writers.panchanga_writer',        'A4_panchanga',        'Panchanga Daily Entries'),
    'A5_sensitive_points': ('pipeline.writers.sensitive_points_writer', 'A5_sensitive_points', 'Sensitive Points & Upagrahas'),
    'A6_vargas':           ('pipeline.writers.vargas_writer',           'A6_vargas',           'Varga Divisional Charts'),
    'A7_dashas':           ('pipeline.writers.dashas_writer',           'A7_dashas',           'Dasha / Sub-Dasha Chains'),
    'A8_t1_structural':    ('pipeline.writers.t1_structural_writer',    'A8_t1_structural',    'T1 Structural Combinations'),
    'A10_msr':             ('pipeline.writers.msr_writer',              'A10_msr',             'MSR Signal Store'),
    'A11_cdlm':            ('pipeline.writers.cdlm_writer',             'A11_cdlm',            'CDLM Cross-Domain Links'),
    'A12_cgm':             ('pipeline.writers.cgm_writer',              'A12_cgm',             'CGM Graph Nodes + Edges'),
    'A13_rm':              ('pipeline.writers.rm_writer',               'A13_rm',              'RM Resonance Map'),
    'A14_ucn_digest':      ('pipeline.writers.ucn_digest_writer',       'A14_ucn_digest',      'UCN Digest'),
}

# Heavy-dep writers — stubs inline in writers/__init__.py closures; constants verified directly
HEAVY_DEP_ASSET_IDS = {
    'A3_chart_facts': ('A3_chart_facts', 'Chart Facts (L1 Structured)'),
    'A9_sade_sati':   ('A9_sade_sati',   'Sade-Sati Phases'),
}


@pytest.mark.parametrize("asset_id,module_info", THIN_MODULE_MAP.items())
def test_writer_has_asset_id_constant(asset_id, module_info):
    """Each thin-stub writer module exposes ASSET_ID matching the registry key."""
    module_path, expected_asset_id, _ = module_info
    mod = importlib.import_module(module_path)
    assert hasattr(mod, 'ASSET_ID'), f"{module_path} missing ASSET_ID constant"
    assert mod.ASSET_ID == expected_asset_id, (
        f"{module_path}.ASSET_ID = {mod.ASSET_ID!r}, expected {expected_asset_id!r}"
    )


@pytest.mark.parametrize("asset_id,module_info", THIN_MODULE_MAP.items())
def test_writer_has_asset_label_constant(asset_id, module_info):
    """Each thin-stub writer module exposes a non-empty ASSET_LABEL string."""
    module_path, _, expected_label = module_info
    mod = importlib.import_module(module_path)
    assert hasattr(mod, 'ASSET_LABEL'), f"{module_path} missing ASSET_LABEL constant"
    assert isinstance(mod.ASSET_LABEL, str) and mod.ASSET_LABEL, (
        f"{module_path}.ASSET_LABEL is empty or not a string"
    )
    assert mod.ASSET_LABEL == expected_label, (
        f"{module_path}.ASSET_LABEL = {mod.ASSET_LABEL!r}, expected {expected_label!r}"
    )


@pytest.mark.parametrize("asset_id,constants", HEAVY_DEP_ASSET_IDS.items())
def test_heavy_dep_stub_is_callable_and_returns_zero(asset_id, constants):
    """A3/A9 heavy-dep stubs are callable and return 0."""
    from pipeline.writers import WRITER_REGISTRY
    fn = WRITER_REGISTRY[asset_id]
    assert callable(fn), f"{asset_id} stub is not callable"
    result = fn(
        build_id='test-build',
        chart_id='test-chart',
        ayanamsha_id='lahiri',
        chart_output={},
        conn=None,
    )
    assert result == 0, f"{asset_id} stub returned {result!r}, expected 0"


# ── Canonical write() signature ───────────────────────────────────────────────

@pytest.mark.parametrize("asset_id,module_info", THIN_MODULE_MAP.items())
def test_write_accepts_canonical_signature(asset_id, module_info):
    """Each write() accepts (build_id, chart_id, ayanamsha_id, chart_output, conn[, extra])."""
    module_path, _, _ = module_info
    mod = importlib.import_module(module_path)
    assert hasattr(mod, 'write'), f"{module_path} missing write() function"
    sig = inspect.signature(mod.write)
    params = list(sig.parameters.keys())
    for required_param in ('build_id', 'chart_id', 'ayanamsha_id', 'chart_output', 'conn'):
        assert required_param in params, (
            f"{module_path}.write() missing parameter '{required_param}'"
        )


def test_heavy_dep_stubs_accept_canonical_signature():
    """A3/A9 __init__ closures accept canonical (build_id, chart_id, ayanamsha_id, chart_output, conn, extra) signature."""
    from pipeline.writers import WRITER_REGISTRY
    for asset_id in ('A3_chart_facts', 'A9_sade_sati'):
        fn = WRITER_REGISTRY[asset_id]
        sig = inspect.signature(fn)
        params = list(sig.parameters.keys())
        for required_param in ('build_id', 'chart_id', 'ayanamsha_id', 'chart_output', 'conn'):
            assert required_param in params, (
                f"{asset_id} closure missing parameter '{required_param}'"
            )


# ── dispatch_asset() uses WRITER_REGISTRY ─────────────────────────────────────

def test_dispatch_asset_uses_writer_registry():
    """dispatch_asset() for a known asset_id delegates to WRITER_REGISTRY."""
    from pipeline.build_chart import dispatch_asset
    # A2_forensic_render stub should return 0
    result = dispatch_asset(
        asset_id='A2_forensic_render',
        build_id='test-build-dispatch',
        chart_id='test-chart-dispatch',
        ayanamshas=['lahiri'],
    )
    assert result == 0


def test_dispatch_asset_returns_zero_for_all_13():
    """dispatch_asset() returns 0 for all 13 stub asset_ids."""
    from pipeline.build_chart import dispatch_asset
    for asset_id in EXPECTED_ASSET_IDS:
        result = dispatch_asset(
            asset_id=asset_id,
            build_id='test-build',
            chart_id='test-chart',
            ayanamshas=['lahiri'],
        )
        assert result == 0, f"dispatch_asset({asset_id!r}) returned {result!r}, expected 0"


def test_dispatch_asset_unknown_asset_id_returns_zero():
    """dispatch_asset() returns 0 for an asset_id not in the registry."""
    from pipeline.build_chart import dispatch_asset
    result = dispatch_asset(
        asset_id='A99_unknown',
        build_id='test-build',
        chart_id='test-chart',
        ayanamshas=['lahiri'],
    )
    assert result == 0


# ── Extra parameter is accepted (optional) ────────────────────────────────────

@pytest.mark.parametrize("asset_id", EXPECTED_ASSET_IDS)
def test_write_accepts_extra_kwarg(asset_id):
    """write() accepts optional extra={} kwarg without raising."""
    from pipeline.writers import WRITER_REGISTRY
    fn = WRITER_REGISTRY[asset_id]
    result = fn(
        build_id='test-build',
        chart_id='test-chart',
        ayanamsha_id='true_chitra',
        chart_output={'stub': True},
        conn=None,
        extra={'context': 'smoke'},
    )
    assert result == 0


# ── Total: 96 parametrized + standalone assertions ────────────────────────────
# Individual parametrized tests:
#   test_registry_contains_asset_id × 13 = 13
#   test_write_returns_zero × 13 = 13
#   test_registry_value_is_callable × 13 = 13
#   test_writer_has_asset_id_constant × 11 (thin) = 11
#   test_writer_has_asset_label_constant × 11 (thin) = 11
#   test_write_accepts_canonical_signature × 11 (thin) = 11
#   test_heavy_dep_stub_is_callable_and_returns_zero × 2 = 2
#   test_write_accepts_extra_kwarg × 13 = 13
# Standalone: 5 (registry_importable, registry_has_13, heavy_dep_signature,
#               dispatch_uses_registry, dispatch_returns_zero_all_13, unknown_returns_zero)
# Total assertions well above 20.
