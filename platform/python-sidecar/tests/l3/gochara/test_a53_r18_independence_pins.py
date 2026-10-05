"""A5.3 — PR #2999 CI repairs: pure (database-free) pins, so they run everywhere.

* the verifier's independently restated dṛṣṭi table equals the kernel's (the D-01a allowlist justification rests on it);
* `ledger.py` resolves its `candidate_boundary` sibling when it is loaded BY PATH with no parent package (the a25 candidate writer loads it so);
* the verifier's tier literal is the sanctioned vocabulary constant (TAP-6).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from brahmagyan.verification_vocab import TWO_PASS_VERIFIED
from services.gochara_kernel import inventory_verifier as inv
from services.gochara_kernel.convention import SPECIAL_DRISHTI_DEG

LEDGER = Path(inv.__file__).with_name("ledger.py")


def test_the_inventory_verifiers_drishti_table_equals_the_kernels_nodes_cast_none():
    for body, angles in SPECIAL_DRISHTI_DEG.items():
        assert inv._DRISHTI_DEG[body.lower()] == tuple(angles), body
    assert set(inv._DRISHTI_DEG) == {b.lower() for b in SPECIAL_DRISHTI_DEG}
    assert inv._DRISHTI_DEG["rahu"] == () and inv._DRISHTI_DEG["ketu"] == ()


def test_ledger_loaded_by_path_without_a_package_still_resolves_the_candidate_boundary():
    spec = importlib.util.spec_from_file_location("a18_ledger_by_path", LEDGER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)                    # no parent package: a relative import here would raise
    cb = module._candidate_boundary()
    assert cb.is_governed("5.0") and not cb.is_governed("4.1")
    assert module._candidate_boundary() is cb          # cached: one module object per by-path ledger load family
    assert tuple(cb.EXCLUDED_ON_DEMAND_KINDS)


def test_the_verifiers_tier_is_the_sanctioned_vocabulary_constant():
    assert inv._C_TIER is TWO_PASS_VERIFIED or inv._C_TIER == TWO_PASS_VERIFIED
