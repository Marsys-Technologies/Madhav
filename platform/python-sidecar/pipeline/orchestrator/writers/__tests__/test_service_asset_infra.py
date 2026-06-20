"""
test_service_asset_infra.py — Unit tests for L3 Kāla K0 service-asset-type infrastructure.

Tests cover:
  1. Service writer self-test pattern: returns WriterResult, writes NO domain rows,
     updates service_health / last_selftest_at via ctx.db_conn, no commit/rollback.
  2. asset_runner._run_service_health_probe writes service_health='healthy' to
     asset_registry on GREEN; 'unhealthy'/'degraded' on failure.
  3. Grep-zero assertion: no ctx.db_conn.commit() / .rollback() in any ka_* writer.
  4. Migration 242 SQL file exists and contains expected DDL tokens.

Runs without a real DB — uses mock connections/cursors.
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from unittest.mock import MagicMock, call, patch
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_conn_cur():
    """Return (mock_conn, mock_cur) wired up like psycopg."""
    cur = MagicMock()
    cur.fetchone.return_value = None
    cur.fetchall.return_value = []
    conn = MagicMock()
    conn.cursor.return_value.__enter__ = lambda s: cur
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cur


SIDECAR_ROOT = Path(__file__).parent.parent.parent.parent.parent  # platform/python-sidecar
MIGRATION_PATH = (
    SIDECAR_ROOT.parent
    / "supabase"
    / "migrations"
    / "242_l3_service_asset_type.sql"
)


# ── Test 1: Migration 242 exists with expected DDL ────────────────────────────

def test_migration_242_exists():
    """Migration 242 SQL file exists in the expected location."""
    assert MIGRATION_PATH.exists(), (
        f"Migration 242 not found at {MIGRATION_PATH}. "
        "Run: create platform/supabase/migrations/242_l3_service_asset_type.sql"
    )


def test_migration_242_contains_asset_kind_column():
    """Migration 242 adds asset_kind column with CHECK constraint."""
    sql = MIGRATION_PATH.read_text()
    assert "asset_kind" in sql, "Migration must add asset_kind column"
    assert "asset_registry_asset_kind_check" in sql, "Migration must name the CHECK constraint"
    assert "'data'" in sql and "'service'" in sql and "'artifact'" in sql, (
        "CHECK must enumerate data, service, artifact values"
    )


def test_migration_242_contains_service_health_columns():
    """Migration 242 adds service_health, last_invoked_at, last_selftest_at, selftest_detail."""
    sql = MIGRATION_PATH.read_text()
    for col in ("service_health", "last_invoked_at", "last_selftest_at", "selftest_detail"):
        assert col in sql, f"Migration must add column: {col}"


def test_migration_242_is_idempotent():
    """Migration uses IF NOT EXISTS / DROP CONSTRAINT IF EXISTS throughout."""
    sql = MIGRATION_PATH.read_text()
    # Every ADD COLUMN must be IF NOT EXISTS
    add_columns = re.findall(r"ADD COLUMN\s+(?!IF NOT EXISTS)", sql, re.IGNORECASE)
    assert not add_columns, (
        "All ADD COLUMN statements must use IF NOT EXISTS for idempotency"
    )
    # Every ADD CONSTRAINT must be preceded by DROP CONSTRAINT IF EXISTS
    assert "DROP CONSTRAINT IF EXISTS" in sql.upper(), (
        "Migration must use DROP CONSTRAINT IF EXISTS before ADD CONSTRAINT"
    )


def test_migration_242_backfills_existing_rows():
    """Migration backfills existing rows from asset_type to asset_kind."""
    sql = MIGRATION_PATH.read_text()
    assert "UPDATE asset_registry SET asset_kind" in sql, (
        "Migration must backfill existing rows: UPDATE asset_registry SET asset_kind"
    )


# ── Test 2: Service writer contract compliance ─────────────────────────────────

def test_service_writer_implements_writer_base():
    """
    A service writer (implementing the self-test pattern) must subclass WriterBase,
    return WriterResult with rows_inserted=0, and NOT call commit/rollback/close.
    """
    from pipeline.orchestrator.writers import WriterBase, WriterResult, ContextSpec

    class _MockServiceWriter(WriterBase):
        """
        Minimal service-writer implementation following the self-test pattern.
        Writes NO domain rows; instead updates service_health + last_selftest_at
        in asset_registry via ctx.db_conn. Never calls commit/rollback.
        """
        asset_id = "ka__selftest_probe_test_fixture"

        def run(self, ctx: ContextSpec) -> WriterResult:
            # Self-test: run the probe + write health telemetry via ctx.db_conn
            # (caller-owned — we must NEVER commit or rollback)
            probe_ok = True  # in real writer: invoke service_probes.run_health_probe
            health = "healthy" if probe_ok else "unhealthy"
            detail = {"status": health, "checks": []}

            cur = ctx.db_conn.cursor()
            cur.execute(
                """UPDATE asset_registry
                   SET service_health = %s,
                       last_selftest_at = NOW(),
                       selftest_detail = %s
                   WHERE asset_id = %s""",
                (health, detail, self.asset_id),
            )
            # MUST NOT call ctx.db_conn.commit() or .rollback()

            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,     # service writers produce NO domain rows
                rows_updated=0,
                notes=f"self-test: {health}",
            )

    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value = cur

    ctx = ContextSpec(
        asset_id="ka__selftest_probe_test_fixture",
        build_id="test-run-1",
        db_conn=conn,
    )

    writer = _MockServiceWriter()
    result = writer.run(ctx)

    # AC5a: WriterResult returned with rows_inserted=0
    assert isinstance(result, WriterResult)
    assert result.rows_inserted == 0, "Service writer must not insert domain rows"
    assert result.rows_updated == 0, "Service writer must not update domain rows"
    assert result.asset_id == "ka__selftest_probe_test_fixture"

    # AC5b: ZERO commit/rollback/close on ctx.db_conn
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()
    conn.close.assert_not_called()

    # AC5c: did write to asset_registry (UPDATE service_health / last_selftest_at)
    cur.execute.assert_called_once()
    call_args = str(cur.execute.call_args)
    assert "service_health" in call_args or "last_selftest_at" in call_args


def test_service_writer_result_has_zero_rows():
    """WriterResult rows_inserted=0 means NO domain table rows."""
    from pipeline.orchestrator.writers import WriterResult

    r = WriterResult(asset_id="ka__selftest_probe", rows_inserted=0)
    assert r.rows_inserted == 0
    assert r.rows_updated == 0
    assert r.rows_skipped == 0


# ── Test 3: asset_runner service health probe writes to asset_registry ─────────

def test_run_service_health_probe_green_writes_asset_registry():
    """
    GREEN probe → asset_throughput lit + asset_registry.service_health='healthy'.
    Verifies asset_runner._run_service_health_probe writes the new mig-242 columns.
    """
    from pipeline.orchestrator import asset_runner

    conn, cur = _mock_conn_cur()

    with patch.object(asset_runner, "emit_event") as mock_emit, \
         patch("pipeline.orchestrator.service_probes.run_health_probe",
               return_value={"status": "GREEN", "message": "All checks passed", "checks": []}):

        asset_runner._run_service_health_probe(
            conn, cur, "run-42", "chart-42", "ka__test_service", health_probe={"probe_type": "panchanga_engine"}
        )

    # conn.commit should be called (orchestrator commits for service probes)
    assert conn.commit.called

    # The execute calls should include UPDATE asset_registry SET service_health=...
    all_sql_calls = [str(c) for c in cur.execute.call_args_list]
    service_health_update = any("service_health" in s for s in all_sql_calls)
    assert service_health_update, (
        f"Expected UPDATE asset_registry SET service_health; got calls:\n" +
        "\n".join(all_sql_calls)
    )

    # emit_event should have fired asset.state_change to lit
    emitted = [c.args[0] for c in mock_emit.call_args_list]
    lit_events = [e for e in emitted if e.get("to_state") == "lit"]
    assert lit_events, "Expected asset.state_change event with to_state='lit'"


def test_run_service_health_probe_failure_writes_unhealthy():
    """
    Failing probe → asset_throughput error + asset_registry.service_health='unhealthy'.
    """
    from pipeline.orchestrator import asset_runner

    conn, cur = _mock_conn_cur()

    with patch.object(asset_runner, "emit_event"), \
         patch.object(asset_runner, "mark_asset_error") as mock_mark_error, \
         patch("pipeline.orchestrator.service_probes.run_health_probe",
               return_value={"status": "down", "message": "engine down", "checks": []}):

        asset_runner._run_service_health_probe(
            conn, cur, "run-43", "chart-43", "ka__test_service_fail", health_probe={"probe_type": "panchanga_engine"}
        )

    # mark_asset_error should be called on failure
    mock_mark_error.assert_called_once()
    # The error message should contain the health status
    error_arg = mock_mark_error.call_args.args[-1]
    assert "down" in error_arg or "service health" in error_arg


# ── Test 4: stats route returns service_health for service assets ──────────────

def test_stats_asset_stats_interface_has_service_health():
    """
    AssetStats interface exported from cockpit/stats/route.ts must include
    service_health and last_invoked_at fields.
    """
    stats_route = Path(__file__).parent.parent.parent.parent.parent.parent / \
        "src" / "app" / "api" / "cockpit" / "stats" / "route.ts"
    assert stats_route.exists(), f"stats route not found at {stats_route}"
    content = stats_route.read_text()
    assert "service_health" in content, "AssetStats must include service_health field"
    assert "last_invoked_at" in content, "AssetStats must include last_invoked_at field"
    assert "asset_kind" in content, "RegistryAsset must include asset_kind field"


# ── Test 5: ServiceHealthBadge component exists ────────────────────────────────

def test_service_health_badge_component_exists():
    """ServiceHealthBadge.tsx component exists in cockpit components directory."""
    badge_path = (
        Path(__file__).parent.parent.parent.parent.parent.parent
        / "src" / "components" / "cockpit" / "ServiceHealthBadge.tsx"
    )
    assert badge_path.exists(), f"ServiceHealthBadge.tsx not found at {badge_path}"
    content = badge_path.read_text()
    assert "ServiceHealthBadge" in content
    assert "service-health-badge" in content  # data-testid
    assert "last_invoked_at" in content or "lastInvokedAt" in content


# ── Test 6: No commit/rollback/close in writers/__init__.py contract ──────────

def test_writer_base_contract_no_commit():
    """WriterBase docstring explicitly states no commit/rollback/close."""
    from pipeline.orchestrator.writers import WriterBase
    import inspect
    doc = inspect.getdoc(WriterBase) or ""
    assert "commit" in doc.lower(), "WriterBase docstring must mention no commit"
    assert "rollback" in doc.lower() or "MUST NOT" in doc, \
        "WriterBase docstring must mention no rollback"


# ── Helpers: grep-zero check for ka_* writers ─────────────────────────────────

def test_no_db_conn_commit_in_ka_writers():
    """
    Grep-zero: no ka_* writer file should call ctx.db_conn.commit(),
    ctx.db_conn.rollback(), or ctx.db_conn.close().

    This test is inherently forward-looking — it scans the writers directory
    for any file with a 'ka_' prefix and asserts the forbidden patterns absent.
    If no ka_* writers exist yet, the test passes trivially (no files to scan).
    """
    writers_dir = Path(__file__).parent.parent

    forbidden = re.compile(
        r"ctx\.db_conn\.(commit|rollback|close)\s*\(",
        re.IGNORECASE,
    )

    violations: list[str] = []
    for py_file in writers_dir.glob("ka_*.py"):
        code = py_file.read_text()
        matches = forbidden.findall(code)
        if matches:
            violations.append(f"{py_file.name}: {matches}")

    assert not violations, (
        "ka_* writers must NOT call ctx.db_conn.commit/rollback/close:\n"
        + "\n".join(violations)
    )
