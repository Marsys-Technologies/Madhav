"""ledger_r81_migration.py — R80/R81 (NIKASHA_CHANGE_REGISTER_v2_0.md, D4 ruling).

R80: adds `superseded_by` to the `_schema` row's own field-list documentation, so folding a
duplicate sets it on the thinner (superseded) row while the ledger stays append-only.
`emit_gaps()` (asset_census.py) already reads and honours `superseded_by` at runtime (an
"ever_superseded" row is never resurrected) — R80 is documentation catching up to a mechanism the
census already implements, not a behaviour change.

R81 (added in the next commit): the reviewed migration folding the 11 hand<->census overlap pairs
measured in T5_LEDGER_DRIFT.md §A.

Both operations are pure functions proven idempotent on a COPY (this module never opens the real
ledger itself — the caller decides which file to point at) before either is ever run against the
real `00_ARCHITECTURE/control/asset_gaps.jsonl`. See __tests__/test_r80_schema_superseded_by_field.py
and __tests__/test_r81_ledger_overlap_fold.py.
"""
from __future__ import annotations

import json

_FIELDS_ANCHOR = "gate, state (OPEN|IN_PROGRESS|CLOSED|WITHDRAWN), ts."
_FIELDS_REPLACEMENT = (
    "gate, state (OPEN|IN_PROGRESS|CLOSED|WITHDRAWN), ts, superseded_by (optional, R80)."
)
_SUPERSEDED_BY_CLAUSE = (
    " `superseded_by` (R80): set on a row whose identity has been folded into another — the row "
    "is never edited or deleted (append-only), but the gap_id it names carries the fold going "
    "forward and the superseded row's own identity is never resurrected by a later measurement "
    "(emit_gaps() already enforces this at runtime, across the id's whole history, not only its "
    "latest row — F5, A_REVIEW.md)."
)


def add_superseded_by_to_schema_doc(doc: str) -> str:
    """Idempotent: inserts `superseded_by` into the Fields: list (right after `gate, state (...),
    ts.`) and appends `_SUPERSEDED_BY_CLAUSE`, unless the field is already documented — running
    this twice on its own output makes no further change."""
    if "superseded_by" in doc:
        return doc
    if _FIELDS_ANCHOR not in doc:
        raise ValueError("schema doc's Fields: list has drifted — expected anchor text not found; "
                          "review before migrating")
    return doc.replace(_FIELDS_ANCHOR, _FIELDS_REPLACEMENT, 1) + _SUPERSEDED_BY_CLAUSE


def migrate_schema_line(schema_row: dict) -> dict:
    """Returns a NEW dict (never mutates the input) with `_doc` migrated. Idempotent: applying
    this to its own output is a no-op (the returned dict compares equal)."""
    row = dict(schema_row)
    row["_doc"] = add_superseded_by_to_schema_doc(row["_doc"])
    return row


def is_schema_row(row: dict) -> bool:
    return row.get("asset") == "_schema"
