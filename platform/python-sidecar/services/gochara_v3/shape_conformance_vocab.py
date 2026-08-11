"""
gochara_v3.shape_conformance_vocab — named `shape_conformance` vocabulary
(PARIṢKĀRA MR-47, ADJUDICATOR ruling PK-R-10).

BACKGROUND (the defect this closes): `ka_gochara_v3_century_materialize.py`'s
`_build_row` hardcoded `"temporal_shape": "interval"` as a wrapper-local
literal for EVERY row it built — including the R8.12 flat-envelope branch
that runs for point-canonical classes (marriage, illness_acute, surgery, and
10 other classes; see `_fetch_event_class_temporal_shape`). That branch's row
is honestly interval-SHAPED in storage (`window_start < window_end`,
`resolution IS NULL`) but is NOT a genuine interval-canonical production —
it is a flat, coarse threshold-crossing envelope stamped with the same
`temporal_shape` literal as a real era⊃month⊃day hierarchy row. Nothing
tracked the difference: a caller reading `temporal_shape='interval'` on any
gen-3.0 row could not tell "this class's ontology genuinely IS
interval-shaped, and this row is the real thing" from "this class's ontology
is 'point', and this row is a flat context envelope wearing 'interval' as a
storage convenience" — exactly the §N.7 item 3 defect ("no wrapper-local
constant may shadow an L1-computed value") PK-R-10 identified.

PK-R-10's binding disposition (c): neither silently accept the mislabeling
(a) nor mint unearned day-precision point rows to make it moot (b). The
truthful fix is the SAME storage shape PLUS an earned, explicit marker
proving the row's `temporal_shape` was checked against
`brahma_event_ontology` at WRITE time — never inferred at read time, never a
hand-typed class list (PK-R-7(iv), corrected text).

THE TWO CONFORMANCE STATES (PK-R-10, binding)
-----------------------------------------------
  SHAPE_CONFORMANCE_ONTOLOGY_MATCH
      The row's stored `temporal_shape` genuinely equals its event_class's
      `brahma_event_ontology.temporal_shape` — the real era⊃month⊃day
      hierarchy branch (`class_shape == 'interval'`, `_build_row`) and the
      chain-milestone branch (`class_shape == 'chain'`, `_build_chain_row`)
      both earn this: their rows are exactly the shape the ontology
      declares, not an envelope wearing a borrowed label.
  SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE
      The R8.12 shape-gate flat-production branch for point-canonical (or
      lookup-failure-conservative-default) classes: the ontology declares
      'point', but the row is stored `temporal_shape='interval'`,
      `resolution IS NULL` — a flat threshold-crossing CONTEXT ENVELOPE
      (span-shaped, no hierarchy tiers, no day-refined peak search), never a
      day-precision timing claim. Marking it honestly lets the serving layer
      (register_gochara_windows.ts's `deriveResolutionDisclosure`) refuse
      `is_timing_window=true` for a documented, class-specific reason instead
      of relying on the generic `resolution IS NULL` fallback as an
      accidental (rather than earned) gate.

RETIREMENT: every NEW row this writer builds must carry an explicit
`shape_conformance` derived from the SAME `class_shape` value
`run_substep` already fetched via `_fetch_event_class_temporal_shape` — never
re-derived from a proxy (e.g. `resolution IS NULL`) and never a bare string
literal. `_build_row` and `_build_chain_row` both take `shape_conformance` as
a REQUIRED keyword parameter (no default) — the exact discipline
`peak_basis_vocab`'s three bases already established for `peak_basis`.

Writers MUST use these named constants, never a bare string literal — a
source guard (mirroring `test_peak_basis_vocab_used_not_literal`) bans
`"shape_conformance": "ontology_match"` / `"shape_conformance":
"point_class_context_envelope"` dict-literal assignments inside
`ka_gochara_v3_century_materialize.py`.
"""
from __future__ import annotations

# The row's stored `temporal_shape` genuinely equals its event_class's
# `brahma_event_ontology.temporal_shape` — a real interval hierarchy tier
# (era/month/day) or a real chain milestone row, never an envelope.
SHAPE_CONFORMANCE_ONTOLOGY_MATCH: str = "ontology_match"

# R8.12 flat-production branch for point-canonical classes: the ontology
# declares 'point', the row is stored `temporal_shape='interval'`,
# `resolution IS NULL` — an honest flat context envelope, never a
# day-precision timing claim, and never to be confused with a genuine
# interval-canonical production row.
SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE: str = "point_class_context_envelope"

# The complete set of conformance states this module knows about, for
# membership checks (e.g. detector code asking "is this stored value one of
# ours at all, vs. an unmigrated NULL or an unrecognized string").
ALL_SHAPE_CONFORMANCES: frozenset[str] = frozenset({
    SHAPE_CONFORMANCE_ONTOLOGY_MATCH,
    SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE,
})

__all__ = [
    "SHAPE_CONFORMANCE_ONTOLOGY_MATCH",
    "SHAPE_CONFORMANCE_POINT_CLASS_ENVELOPE",
    "ALL_SHAPE_CONFORMANCES",
]
