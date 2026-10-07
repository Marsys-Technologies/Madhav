"""L0-M's bounded scope-domain preparation (migration 1328).

The coordinated Suvarṇa reseal decides the extracted rows and their new
count/hash.  This slice may only widen the domain needed to represent their
plan-mandated scopes; it must retain the two live scopes and must not write
reference rows or registry pins prematurely.
"""
from __future__ import annotations

import re
from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[4]
    / "migrations"
    / "1329_l0_muhurta_parihara_scope_prepare.sql"
)


def _code() -> str:
    return "\n".join(
        line for line in MIGRATION.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("--")
    )


def test_scope_constraint_preserves_live_values_and_admits_only_l0_m_scopes():
    """Mutants dropping a live scope or a required L0-M scope must fail."""
    code = _code()
    match = re.search(
        r"CHECK\s*\(\s*scope\s+IN\s*\(([^)]*)\)\s*\)", code, re.I | re.S
    )
    assert match, "migration must install an explicit scope CHECK"
    scopes = set(re.findall(r"'([^']+)'", match.group(1)))
    assert scopes == {"natal", "muhurta", "marriage", "upanayana", "general"}


def test_preparation_does_not_ingest_rows_or_repin_shared_integrity_state():
    """Mutants that add data or alter a pin before coordination must fail."""
    code = _code()
    assert "DROP CONSTRAINT IF EXISTS bg_parihara_rules_scope_check" in code
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|TRUNCATE)\b", code, re.I)
    assert "asset_registry" not in code
