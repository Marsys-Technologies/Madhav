"""
gochara_v3.shape_conformance_check — PARIṢKĀRA MR-47 (PK-R-10) real detector.

Pure, DB-free classifier: given a row's OWN stored `temporal_shape` /
`resolution` and its event_class's `brahma_event_ontology.temporal_shape`,
returns the `shape_conformance` value that row SHOULD carry per PK-R-10's
binding disposition — the SAME logic migration 570's backfill UPDATE runs as
SQL, expressed here as Python so both the live-corpus detector script
(`scripts/mr47_shape_conformance_gate.py`) and a mutation-proof unit test
(no DB required) can share one non-duplicated derivation.

§N.8 (Earned-Signal Principle): a detector must measure the SPECIFIC claim
it asserts, not a proxy. This module's `expected_shape_conformance` reads
ONLY the three inputs PK-R-10 named (a row's own `temporal_shape`,
`resolution`, and its class's ontology-declared `temporal_shape`) — it never
trusts a row's OWN `shape_conformance` column as evidence for itself. The
detector script compares this function's independently-recomputed answer
against what is actually stored; any disagreement is a real, catchable
defect (proven by `test_shape_conformance_check_mutation_proof.py`'s
deliberate-mismatch fixture).
"""
from __future__ import annotations

from typing import Optional

from services.gochara_v3.shape_conformance_vocab import (
    SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE,
)


def expected_shape_conformance(
    *,
    stored_temporal_shape: str,
    stored_resolution: Optional[str],
    ontology_temporal_shape: Optional[str],
) -> Optional[str]:
    """Return the `shape_conformance` value a row with these attributes
    SHOULD carry, per PK-R-10's binding disposition — or None if the
    combination is unclassifiable (an honest gap, never a guessed default;
    §N.7 item 6).

    Classification (mirrors migration 570's backfill UPDATE exactly, and
    `run_substep`'s own per-substep derivation from `class_shape`):

      1. `stored_temporal_shape == ontology_temporal_shape`
         -> SHAPE_CONFORMANCE_ONTOLOGY_MATCH. Covers the real era⊃month⊃day
            hierarchy branch (ontology='interval', row stored 'interval'),
            the chain-milestone branch (ontology='chain', row stored
            'chain'), and any genuine point row (ontology='point', row
            stored 'point', e.g. MR-10's v1-promoted rows).
      2. `ontology_temporal_shape == 'point'` AND `stored_temporal_shape ==
         'interval'` AND `stored_resolution is None`
         -> SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE. The R8.12 flat-production
            branch: a point-canonical class's row, honestly a flat
            threshold-crossing context envelope, never a genuine interval
            production.
      3. Anything else (no ontology row found, or a shape/resolution
         combination neither rule above covers — e.g. ontology='interval'
         but the row is stored 'point', which should be structurally
         impossible under this writer but is not silently waved through)
         -> None. An honest, reportable gap, not a fabricated classification.
    """
    if ontology_temporal_shape is None:
        return None

    if stored_temporal_shape == ontology_temporal_shape:
        return SHAPE_CONFORMANCE_ONTOLOGY_MATCH

    if (
        ontology_temporal_shape == "point"
        and stored_temporal_shape == "interval"
        and stored_resolution is None
    ):
        return SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE

    return None


def diagnose_row(
    *,
    stored_temporal_shape: str,
    stored_resolution: Optional[str],
    ontology_temporal_shape: Optional[str],
    stored_shape_conformance: Optional[str],
) -> Optional[str]:
    """Compare a row's ACTUALLY STORED `shape_conformance` against the
    independently-recomputed expected value. Returns None when they agree
    (or both honestly agree on "unclassifiable" -> None == None), else a
    human-readable mismatch description.

    This is the actual detector §N.8 requires: it reads the row's stored
    value and the ontology's independently-fetched value, and FAILS when
    they disagree — the code path a mutation-proof test can prove actually
    runs and actually fires (see
    test_shape_conformance_check_mutation_proof.py).
    """
    expected = expected_shape_conformance(
        stored_temporal_shape=stored_temporal_shape,
        stored_resolution=stored_resolution,
        ontology_temporal_shape=ontology_temporal_shape,
    )
    if expected == stored_shape_conformance:
        return None
    return (
        f"shape_conformance MISMATCH: stored={stored_shape_conformance!r} "
        f"expected={expected!r} "
        f"(stored_temporal_shape={stored_temporal_shape!r}, "
        f"stored_resolution={stored_resolution!r}, "
        f"ontology_temporal_shape={ontology_temporal_shape!r})"
    )


__all__ = ["expected_shape_conformance", "diagnose_row"]
