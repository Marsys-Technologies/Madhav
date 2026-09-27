"""test_r80_schema_superseded_by_field.py — R80 (NIKASHA_CHANGE_REGISTER_v2_0.md, D4 ruling retained).

`asset_gaps.jsonl`'s `_schema` row documents every field the ledger carries, but did not mention
`superseded_by` — the flag `emit_gaps()` (asset_census.py) already reads and enforces at runtime
(an "ever_superseded" gap_id is never resurrected, across its whole history — F5, A_REVIEW.md).
R80 is the schema documentation catching up to a mechanism the code already implements.

This test proves `ledger_r81_migration.add_superseded_by_to_schema_doc` / `migrate_schema_line` —
idempotent, and NEVER touches the real ledger file (a hardcoded, in-memory copy of the real
`_schema` row's current `_doc` text is the fixture). The real file's own migration happens only in
R81's single authorized commit, together with the row fold.

Fails without the fix: the function does not exist / does not add the field.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import ledger_r81_migration as mig  # noqa: E402

REAL_LEDGER = HERE.parents[3] / "00_ARCHITECTURE/control/asset_gaps.jsonl"


def _real_schema_row() -> dict:
    """Reads (never writes) the real ledger's first line, so this test tracks the real current
    schema text instead of a second, driftable copy of it."""
    with REAL_LEDGER.open(encoding="utf-8") as f:
        return json.loads(f.readline())


def test_real_schema_row_does_not_yet_document_superseded_by():
    """Sanity check on the fixture itself — if this ever fails, R80 already landed for real and
    this test file is stale, not the code."""
    row = _real_schema_row()
    assert "superseded_by" not in row["_doc"]


def test_migrate_schema_line_adds_the_field_and_a_clause():
    row = _real_schema_row()
    migrated = mig.migrate_schema_line(row)
    assert "superseded_by" in migrated["_doc"]
    assert "the row is never edited or deleted" in migrated["_doc"]
    # Every other field documented before must still be documented after.
    for f in ("asset", "gap_id", "kind", "criterion", "what", "change", "detector", "owner",
              "gate", "state", "ts"):
        assert f in migrated["_doc"], f"field {f!r} lost during migration"


def test_migrate_schema_line_never_mutates_its_input():
    row = _real_schema_row()
    before = json.dumps(row)
    mig.migrate_schema_line(row)
    assert json.dumps(row) == before, "migrate_schema_line must return a new dict, never mutate its input"


def test_migration_is_idempotent_running_twice_matches_running_once():
    row = _real_schema_row()
    once = mig.migrate_schema_line(row)
    twice = mig.migrate_schema_line(once)
    assert once == twice, "applying the migration to its own output must be a no-op"
    assert once["_doc"].count("superseded_by") == twice["_doc"].count("superseded_by")


def test_add_superseded_by_to_schema_doc_raises_on_drifted_anchor_rather_than_silently_no_opping():
    import pytest
    with pytest.raises(ValueError):
        mig.add_superseded_by_to_schema_doc("some unrelated doc text with no Fields: anchor at all")


def test_is_schema_row():
    assert mig.is_schema_row({"asset": "_schema"})
    assert not mig.is_schema_row({"asset": "bg_x"})
