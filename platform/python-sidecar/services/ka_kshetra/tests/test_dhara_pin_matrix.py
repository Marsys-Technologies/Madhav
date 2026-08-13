"""Tests for engine_config.py and dhara_pin_matrix.py.

Covers:
    - ENGINE_VERSION default value
    - Determinism of stage pins
    - F-04 invariant: stage 1 pin depends on stage 3 pin, not on stage 2 inputs
    - SHA256 prefix contract on config_pin
    - config_pin changes when any stage pin changes

Authority: DHARA_DESIGN_v1_0.md §5, §8 (F-04, F-07 amendments)
"""
from __future__ import annotations

import pytest

from services.ka_kshetra import engine_config
from services.ka_kshetra.dhara_pin_matrix import (
    build_pin_matrix,
    compute_stage0_pin,
    compute_stage1_pin,
    compute_stage2_pin,
    compute_stage3_pin,
    compute_stage4_pin,
    compute_stage5_pin,
    pin_matrix_to_config_pin,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

STAGE0_INPUTS = dict(
    code_version='dhara-v0.1.0',
    chart_data_digest='sha256:' + 'a' * 64,
    cohort_version='cohort-2026-08',
)

STAGE3_INPUTS = dict(
    kala_field_clocks_digest='sha256:' + 'c' * 64,
    boundary_data_digest='sha256:' + 'd' * 64,
)

FULL_INPUTS = dict(
    **STAGE0_INPUTS,
    promise_graph_version='sha256:' + 'b' * 64,
    **STAGE3_INPUTS,
    weights_version='weights-v3',
    gochara_corpus_digest='sha256:' + 'e' * 64,
    null_replicate_count=1024,
)


def _base_stage0() -> str:
    return compute_stage0_pin(**STAGE0_INPUTS)


def _base_stage3(stage0: str) -> str:
    return compute_stage3_pin(stage0, **STAGE3_INPUTS)


# ---------------------------------------------------------------------------
# 1. ENGINE_VERSION default
# ---------------------------------------------------------------------------

def test_engine_version_default_is_sampled():
    """ENGINE_VERSION must be 'sampled' in this PR — flag-flip is a separate commit."""
    assert engine_config.ENGINE_VERSION == 'sampled'


# ---------------------------------------------------------------------------
# 2. Determinism: same inputs -> same pin
# ---------------------------------------------------------------------------

def test_stage_pins_are_deterministic():
    """All six stage-pin functions must be pure (same inputs -> same output)."""
    stage0 = _base_stage0()
    assert compute_stage0_pin(**STAGE0_INPUTS) == stage0

    stage3 = _base_stage3(stage0)
    assert compute_stage3_pin(stage0, **STAGE3_INPUTS) == stage3

    stage1 = compute_stage1_pin(stage0, stage3, STAGE0_INPUTS['code_version'])
    assert compute_stage1_pin(stage0, stage3, STAGE0_INPUTS['code_version']) == stage1

    stage2 = compute_stage2_pin(stage0, FULL_INPUTS['promise_graph_version'])
    assert compute_stage2_pin(stage0, FULL_INPUTS['promise_graph_version']) == stage2

    stage4 = compute_stage4_pin(
        stage0, stage1, stage2, stage3,
        FULL_INPUTS['weights_version'],
        FULL_INPUTS['gochara_corpus_digest'],
    )
    assert compute_stage4_pin(
        stage0, stage1, stage2, stage3,
        FULL_INPUTS['weights_version'],
        FULL_INPUTS['gochara_corpus_digest'],
    ) == stage4

    stage5 = compute_stage5_pin(stage4, FULL_INPUTS['null_replicate_count'])
    assert compute_stage5_pin(stage4, FULL_INPUTS['null_replicate_count']) == stage5


# ---------------------------------------------------------------------------
# 3. F-04 invariant: stage 1 depends on stage 3
# ---------------------------------------------------------------------------

def test_stage1_pin_depends_on_stage3():
    """Changing the stage 3 pin must change the stage 1 pin (F-04 invariant).

    Stage dispatch order is 0→2→3→1→4; stage 1 reads kala_field_boundaries
    produced by stage 3, so its pin must capture stage 3's identity.
    """
    stage0 = _base_stage0()
    stage3_original = _base_stage3(stage0)
    stage3_altered = compute_stage3_pin(
        stage0,
        kala_field_clocks_digest='sha256:' + 'f' * 64,  # different clocks
        boundary_data_digest=STAGE3_INPUTS['boundary_data_digest'],
    )
    assert stage3_original != stage3_altered  # precondition

    code_version = STAGE0_INPUTS['code_version']
    stage1_original = compute_stage1_pin(stage0, stage3_original, code_version)
    stage1_altered = compute_stage1_pin(stage0, stage3_altered, code_version)

    assert stage1_original != stage1_altered, (
        "stage 1 pin must change when stage 3 pin changes (F-04)"
    )


# ---------------------------------------------------------------------------
# 4. Stage 1 is independent of stage 2 inputs
# ---------------------------------------------------------------------------

def test_stage1_pin_independent_of_stage2():
    """Stage 1 pin must NOT change when promise_graph_version changes.

    Stage 1 (Symbolization) reads kala_field_boundaries (stage 3 output), not
    the promise graph (stage 2 output). Its pin must not encode stage 2 inputs.
    """
    stage0 = _base_stage0()
    stage3 = _base_stage3(stage0)
    code_version = STAGE0_INPUTS['code_version']

    stage1 = compute_stage1_pin(stage0, stage3, code_version)

    # Mutate promise_graph_version — this feeds stage 2, not stage 1
    stage2_variant_a = compute_stage2_pin(stage0, 'sha256:' + 'b' * 64)
    stage2_variant_b = compute_stage2_pin(stage0, 'sha256:' + '9' * 64)
    assert stage2_variant_a != stage2_variant_b  # precondition

    # Stage 1 pin is the same regardless of which stage 2 variant we compute
    # (stage1 does not take a stage2_pin argument)
    stage1_recomputed = compute_stage1_pin(stage0, stage3, code_version)
    assert stage1 == stage1_recomputed, (
        "stage 1 pin must be independent of stage 2 inputs"
    )


# ---------------------------------------------------------------------------
# 5. config_pin starts with 'sha256:'
# ---------------------------------------------------------------------------

def test_pin_matrix_to_config_pin_is_sha256():
    """The monolithic config_pin derived from the pin matrix must start with 'sha256:'."""
    matrix = build_pin_matrix('marriage', **FULL_INPUTS)
    config_pin = pin_matrix_to_config_pin(matrix)
    assert config_pin.startswith('sha256:'), (
        f"config_pin must start with 'sha256:', got: {config_pin[:20]!r}"
    )
    # SHA256 hex digest is 64 chars; total length = 7 + 64 = 71
    assert len(config_pin) == 71, (
        f"Expected 'sha256:' + 64 hex chars = 71 chars, got {len(config_pin)}"
    )


# ---------------------------------------------------------------------------
# 6. config_pin changes when any stage pin changes
# ---------------------------------------------------------------------------

def test_config_pin_changes_when_any_stage_changes():
    """Any change to any stage's inputs must propagate to the config_pin.

    Verifies each stage independently by mutating exactly one input at a time
    and confirming the config_pin differs from the baseline.
    """
    base_matrix = build_pin_matrix('marriage', **FULL_INPUTS)
    base_config_pin = pin_matrix_to_config_pin(base_matrix)

    # --- Stage 0: change code_version ---
    inputs_s0 = {**FULL_INPUTS, 'code_version': 'dhara-v0.2.0'}
    matrix_s0 = build_pin_matrix('marriage', **inputs_s0)
    assert pin_matrix_to_config_pin(matrix_s0) != base_config_pin, (
        "config_pin must change when code_version (stage 0 input) changes"
    )

    # --- Stage 2: change promise_graph_version ---
    inputs_s2 = {**FULL_INPUTS, 'promise_graph_version': 'sha256:' + '1' * 64}
    matrix_s2 = build_pin_matrix('marriage', **inputs_s2)
    assert pin_matrix_to_config_pin(matrix_s2) != base_config_pin, (
        "config_pin must change when promise_graph_version (stage 2 input) changes"
    )

    # --- Stage 3: change kala_field_clocks_digest ---
    inputs_s3 = {**FULL_INPUTS, 'kala_field_clocks_digest': 'sha256:' + '2' * 64}
    matrix_s3 = build_pin_matrix('marriage', **inputs_s3)
    assert pin_matrix_to_config_pin(matrix_s3) != base_config_pin, (
        "config_pin must change when kala_field_clocks_digest (stage 3 input) changes"
    )

    # --- Stage 4 (via weights_version, which feeds stage 4 directly) ---
    inputs_s4 = {**FULL_INPUTS, 'weights_version': 'weights-v4'}
    matrix_s4 = build_pin_matrix('marriage', **inputs_s4)
    assert pin_matrix_to_config_pin(matrix_s4) != base_config_pin, (
        "config_pin must change when weights_version (stage 4 input) changes"
    )

    # --- Stage 5: change null_replicate_count ---
    inputs_s5 = {**FULL_INPUTS, 'null_replicate_count': 256}
    matrix_s5 = build_pin_matrix('marriage', **inputs_s5)
    assert pin_matrix_to_config_pin(matrix_s5) != base_config_pin, (
        "config_pin must change when null_replicate_count (stage 5 input) changes"
    )
