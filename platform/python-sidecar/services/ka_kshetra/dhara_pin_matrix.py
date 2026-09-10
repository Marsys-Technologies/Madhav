"""DHARA (stage x class) pin matrix.

Decomposes the monolithic config_pin into per-stage, per-class pins, enabling
selective invalidation when only a subset of a build's inputs change.

Pin definitions (DHARA_DESIGN_v1_0.md §5.2, F-04 amended):

    Stage 0 — Kinematics
        Inputs: code_version + chart_data_digest + cohort_version
        Note: does NOT depend on stage 3.

    Stage 1 — Symbolization
        Inputs: stage0_pin + stage3_pin + code_version
        Note (F-04): stage dispatch order is 0→2→3→1→4. Stage 1 reads
        kala_field_boundaries produced by stage 3, so its pin must include the
        stage 3 pin. Stages 0 and 1 are SEPARATE pins (not combined "0-1").

    Stage 2 — Promise
        Inputs: stage0_pin + promise_graph_version

    Stage 3 — Clocks + Boundaries
        Inputs: stage0_pin + kala_field_clocks_digest + boundary_data_digest

    Stage 4 — Field Assembly
        Inputs: stage0_pin + stage1_pin + stage2_pin + stage3_pin
                + weights_version + gochara_corpus_digest

    Stage 5 — Null Distribution
        Inputs: stage4_pin + null_replicate_count

Monolithic config_pin (F-07):
    config_pin = SHA256(canonical_json(pin_matrix))

    This is a BREAKING CHANGE relative to sampled-engine snapshots. A DHARA
    snapshot will NOT match any sampled-engine snapshot on config_pin lookup.
    This is intentional: the segment representation differs. Sampled-engine
    snapshots remain in kala_field_snapshots as historical records; the DHARA
    snapshot is a new row.

Authority: DHARA_DESIGN_v1_0.md §5, §8 (F-04, F-07 amendments)
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def _sha256_of(obj: Any) -> str:
    """Return 'sha256:<hex>' of the canonical JSON representation of obj.

    Canonical form: sort_keys=True, no extra whitespace, non-JSON types
    stringified via default=str.
    """
    serialized = json.dumps(obj, sort_keys=True, separators=(',', ':'), default=str)
    return 'sha256:' + hashlib.sha256(serialized.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Per-stage pin computations
# ---------------------------------------------------------------------------

def compute_stage0_pin(
    code_version: str,
    chart_data_digest: str,
    cohort_version: str,
) -> str:
    """Stage 0 (Kinematics) pin.

    Does NOT depend on stage 3 (F-04: stages 0 and 1 are separate).

    Args:
        code_version: DHARA engine version tag (e.g. a git sha or semver).
        chart_data_digest: SHA256 of birth params + natal positions hash for
            this chart.
        cohort_version: Version tag of the cohort baseline used for this
            chart's build.

    Returns:
        'sha256:<hex>' string uniquely identifying these kinematics inputs.
    """
    return _sha256_of({
        'stage': 0,
        'code_version': code_version,
        'chart_data_digest': chart_data_digest,
        'cohort_version': cohort_version,
    })


def compute_stage1_pin(
    stage0_pin: str,
    stage3_pin: str,
    code_version: str,
) -> str:
    """Stage 1 (Symbolization) pin.

    F-04 AMENDMENT: Stage 1 depends on stage 3 because the dispatch order is
    0→2→3→1→4. Stage 1 reads kala_field_boundaries produced by stage 3, so
    its pin must include the stage 3 pin.

    Args:
        stage0_pin: Pin returned by compute_stage0_pin().
        stage3_pin: Pin returned by compute_stage3_pin().
        code_version: DHARA engine version tag (same value used in stage 0).

    Returns:
        'sha256:<hex>' string.
    """
    return _sha256_of({
        'stage': 1,
        'stage0_pin': stage0_pin,
        'stage3_pin': stage3_pin,
        'code_version': code_version,
    })


def compute_stage2_pin(
    stage0_pin: str,
    promise_graph_version: str,
) -> str:
    """Stage 2 (Promise) pin.

    Args:
        stage0_pin: Pin returned by compute_stage0_pin().
        promise_graph_version: SHA256 of bo_pratijna corpus rows for this
            chart, sorted by natural key.

    Returns:
        'sha256:<hex>' string.
    """
    return _sha256_of({
        'stage': 2,
        'stage0_pin': stage0_pin,
        'promise_graph_version': promise_graph_version,
    })


def compute_stage3_pin(
    stage0_pin: str,
    kala_field_clocks_digest: str,
    boundary_data_digest: str,
) -> str:
    """Stage 3 (Clocks + Boundaries) pin.

    Args:
        stage0_pin: Pin returned by compute_stage0_pin().
        kala_field_clocks_digest: SHA256 of applicable-system rows from
            kala_field_clocks for this chart.
        boundary_data_digest: SHA256 of dasa ladder period rows from
            kala_field_boundaries for this chart.

    Returns:
        'sha256:<hex>' string.
    """
    return _sha256_of({
        'stage': 3,
        'stage0_pin': stage0_pin,
        'kala_field_clocks_digest': kala_field_clocks_digest,
        'boundary_data_digest': boundary_data_digest,
    })


def compute_stage4_pin(
    stage0_pin: str,
    stage1_pin: str,
    stage2_pin: str,
    stage3_pin: str,
    weights_version: str,
    gochara_corpus_digest: str,
) -> str:
    """Stage 4 (Field Assembly) pin.

    Args:
        stage0_pin: Pin from compute_stage0_pin().
        stage1_pin: Pin from compute_stage1_pin().
        stage2_pin: Pin from compute_stage2_pin().
        stage3_pin: Pin from compute_stage3_pin().
        weights_version: Version tag identifying the beta/w_s/rho weight set.
        gochara_corpus_digest: SHA256 of kala_field_primitives rows for this
            chart (the gochara transit stream used in field assembly).

    Returns:
        'sha256:<hex>' string.
    """
    return _sha256_of({
        'stage': 4,
        'stage0_pin': stage0_pin,
        'stage1_pin': stage1_pin,
        'stage2_pin': stage2_pin,
        'stage3_pin': stage3_pin,
        'weights_version': weights_version,
        'gochara_corpus_digest': gochara_corpus_digest,
    })


def compute_stage5_pin(
    stage4_pin: str,
    null_replicate_count: int,
) -> str:
    """Stage 5 (Null Distribution) pin.

    Args:
        stage4_pin: Pin from compute_stage4_pin().
        null_replicate_count: Number of circular-shift replicates used to
            build the null distribution (1024 for DHARA per ruling n3).

    Returns:
        'sha256:<hex>' string.
    """
    return _sha256_of({
        'stage': 5,
        'stage4_pin': stage4_pin,
        'null_replicate_count': null_replicate_count,
    })


# ---------------------------------------------------------------------------
# Full pin matrix builder
# ---------------------------------------------------------------------------

def build_pin_matrix(event_class: str, **inputs: Any) -> dict[str, dict[str, str]]:
    """Build the full (stage x class) pin matrix for one event class.

    Computes all six stage pins and assembles them under the event_class key.
    The dispatch order reflected in pin dependencies is 0→2→3→1→4→5 (F-04).

    Required keyword arguments (all str unless noted):
        code_version          — DHARA engine version tag
        chart_data_digest     — SHA256 of birth params + natal positions
        cohort_version        — cohort baseline version tag
        promise_graph_version — SHA256 of bo_pratijna corpus rows
        kala_field_clocks_digest — SHA256 of kala_field_clocks rows
        boundary_data_digest  — SHA256 of kala_field_boundaries rows
        weights_version       — weight set version tag
        gochara_corpus_digest — SHA256 of kala_field_primitives rows
        null_replicate_count  — int, number of null replicates

    Returns:
        {
            event_class: {
                'stage_0': 'sha256:...',
                'stage_1': 'sha256:...',
                'stage_2': 'sha256:...',
                'stage_3': 'sha256:...',
                'stage_4': 'sha256:...',
                'stage_5': 'sha256:...',
            }
        }
    """
    code_version = inputs['code_version']
    chart_data_digest = inputs['chart_data_digest']
    cohort_version = inputs['cohort_version']
    promise_graph_version = inputs['promise_graph_version']
    kala_field_clocks_digest = inputs['kala_field_clocks_digest']
    boundary_data_digest = inputs['boundary_data_digest']
    weights_version = inputs['weights_version']
    gochara_corpus_digest = inputs['gochara_corpus_digest']
    null_replicate_count = inputs['null_replicate_count']

    # Dispatch order: 0 → 2 → 3 → 1 → 4 → 5
    stage0 = compute_stage0_pin(code_version, chart_data_digest, cohort_version)
    stage2 = compute_stage2_pin(stage0, promise_graph_version)
    stage3 = compute_stage3_pin(stage0, kala_field_clocks_digest, boundary_data_digest)
    stage1 = compute_stage1_pin(stage0, stage3, code_version)
    stage4 = compute_stage4_pin(stage0, stage1, stage2, stage3, weights_version, gochara_corpus_digest)
    stage5 = compute_stage5_pin(stage4, null_replicate_count)

    return {
        event_class: {
            'stage_0': stage0,
            'stage_1': stage1,
            'stage_2': stage2,
            'stage_3': stage3,
            'stage_4': stage4,
            'stage_5': stage5,
        }
    }


def pin_matrix_to_config_pin(pin_matrix: dict[str, dict[str, str]]) -> str:
    """Derive the monolithic config_pin from the pin matrix.

    config_pin = SHA256(canonical_json(pin_matrix))

    NOTE (F-07): This config_pin is NOT backward-compatible with sampled-engine
    snapshots. A DHARA snapshot will have a different config_pin than any
    sampled-engine snapshot even for the same chart/event_class. The sampled-
    engine snapshots remain in kala_field_snapshots as historical records; a
    DHARA build produces a new, distinct row.

    Args:
        pin_matrix: Dict as returned by build_pin_matrix() — may cover multiple
            event classes: {event_class: {stage_N: sha256_str, ...}, ...}.

    Returns:
        'sha256:<hex>' string suitable for storage in kala_field_snapshots.config_pin.
    """
    return _sha256_of(pin_matrix)
