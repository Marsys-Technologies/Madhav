"""Shared fixture for the argala migration tests (1219 and 1221): a minimal asset_registry plus the three serving tables,
with the REAL nirmana_invalidate_registry_receipts() function body and the REAL trigger definition, both read from the live
database as suvarna_reader (fixtures/argala_registry_trigger/). Kept byte-identical in the two PRs that add it.

The trigger fires only on UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor,
asset_kind, asset_type, scope, has_writer, is_active, target_table (count_sql is not in the list): it marks the asset's
asset_freshness rows stale ('registry_changed'). served_generation.ts additionally treats a receipt whose
output_digest_spec_sha256 is not an ACTIVE asset_output_digest_specs row as receipt_spec_retired.
"""
from __future__ import annotations

import pathlib

from tests.pg_disposable import q

DIR = pathlib.Path(__file__).resolve().parent / "fixtures" / "argala_registry_trigger"
TRIGGER_COLUMNS = ["depends_on", "natural_key_partition", "health_probe", "integrity_check_sql", "target_floor",
                   "asset_kind", "asset_type", "scope", "has_writer", "is_active", "target_table"]
REGISTRY_DDL = """
CREATE TABLE asset_registry (asset_id text PRIMARY KEY, depends_on text[], natural_key_partition text, health_probe jsonb,
  integrity_check_sql text, target_floor integer, asset_kind text, asset_type text, scope text, has_writer boolean,
  is_active boolean, target_table text, count_sql text);
"""


def install(port: int, db: str) -> None:
    """asset_registry (columns of the live trigger + count_sql), the serving tables, the real trigger function/trigger."""
    q(port, db, REGISTRY_DDL)
    q(port, db, (DIR / "serving_tables.sql").read_text(encoding="utf-8"))
    q(port, db, (DIR / "trigger_and_function.sql").read_text(encoding="utf-8"))


def seed_fresh(port: int, db: str, asset_ids: list[str]) -> None:
    """One fresh asset_freshness row per asset (observed_at pinned so any trigger touch changes the row)."""
    values = ", ".join(f"('{a}', NULL, 'chart', 'canonical', 'fresh', 'v1', '2026-10-01T00:00:00Z')" for a in asset_ids)
    q(port, db, "INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, receipt_version, observed_at) "
                f"VALUES {values}")


def freshness_snapshot(port: int, db: str) -> str:
    return q(port, db, "SELECT coalesce(string_agg(to_jsonb(f)::text, E'\\n' ORDER BY asset_id, scope_key, partition_key), '') FROM asset_freshness f")


def specs_snapshot(port: int, db: str) -> str:
    return q(port, db, "SELECT coalesce(string_agg(to_jsonb(s)::text, E'\\n' ORDER BY asset_id, spec_sha256), '') FROM asset_output_digest_specs s")
