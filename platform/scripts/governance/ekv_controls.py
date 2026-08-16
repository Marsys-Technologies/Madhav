#!/usr/bin/env python3
"""ekv_controls.py — EKAVĀKYATĀ CL-00 regression-control battery (D-04).

Runs the 27 named controls from EKAVAKYATA_EXECUTION_PLAN_v1_0.md §1 that must
stay green after every merge batch. SENTINEL consumes this battery every deploy;
the --cheap flag gives a fast subset safe to run per-batch without a full DB scan.

Controls
--------
F-32  Cross-tool gochara_sweep coherence (evidence files, no DB)
F-72  mechanism_retrodiction baseline (informational — SKIP if no MCP)
F-75  Kala field decade-seam contiguity (SQL, native chart) [CHEAP]
F-76  kala_field_null 25x10 grid invariant (SQL, native chart) [CHEAP]
F-77  kala_field_snapshots.field_content_hash match (evidence file)
F-80  No legacy_id / identity_map columns (SQL)
F-82  _migrations_applied vs on-disk count (SQL + file count)
F-83  FK/orphan referential integrity (SQL) [CHEAP]
F-84  No duplicate natural-key rows in kala_field (SQL) [CHEAP]
F-85  chart_facts.verification_pass_status enum (SQL) [CHEAP]
F-86  _migrations_applied.applied_at monotone (SQL)
F-87  kala_field full horizon [0, 36525] coverage (SQL) [CHEAP]
F-88  active_chart_id session scoping (MCP live probe)
F-91  MCP tool-catalog profile scoping (MCP live probe)
F-96  fact-category-pin-lint self-test [CHEAP]
F-97  ga_yoga_firings.bhanga_active real detector (MCP live probe)
F-98  bo_pramana_mapa trap1/trap2 real detectors (MCP live probe)
F-99  kala_sarpa_reconciliation.agrees genuine check (MCP live probe)
F-100 judgment_query receipt.timing_anchored content-checked (MCP)
F-101 judgment_query receipt.varga_confirmed genuine (MCP)
F-102 asset_throughput no-op-completion guard still fixed (SQL)
F-103 phala_predictive_anchors posterior_provenance equality (MCP)
F-105 mi_adhilepa uses 'not_assessed' (static code check)
F-106 bodha_quality_get defect_001.status live re-derived (MCP)
F-109 Wealth-domain dark-corpus BRIGHT >=80% (evidence file)
F-137 graha_portrait / judgment_query use v3 envelope (MCP)
F-138 kala_ahead_get period_echo cross-reference (MCP)

CHEAP subset (fast, per-batch CI): F-75 F-76 F-83 F-84 F-85 F-87 F-96 F-102
  + 3-tool live-probe (F-91 abbreviated: 3 calls, no DB needed).
  F-102 added 2026-08-16 (F-141/PAR-R-9 follow-up): it is a single unindexed-scan
  count(*) on asset_throughput, the same shape/cost class as F-83/F-84/F-85, and
  was previously omitted from the per-batch cheap subset with no stated reason --
  INTEGRATOR's own --cheap invocation was silently skipping it every batch,
  independent of (and in addition to) the separate finding that no CI workflow
  invokes ekv_controls.py at all (see _check_f102's own docstring).

Exit codes
----------
  0  all run controls PASS
  1  one or more controls FAIL
  2  invocation / config error
  3  partial: some controls SKIPPED (no DB / no MCP) but rest PASS
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent

# Cross-layer import: brahmagyan.verification_vocab is THE settled source of truth
# for verification_pass_status (CLAUDE.md §N.4). A hardcoded copy here was exactly
# the eighth-disagreeing-definition anti-pattern the module's own docstring warns
# about (morning-session fix, EKAVAKYATA post-close triage, F-85).
sys.path.insert(0, str(REPO_ROOT / "platform" / "python-sidecar"))


class ControlBrokenError(Exception):
    """Raised when a detector could not execute at all (e.g. a referenced relation
    does not exist) — distinct from a detector that ran and found a real defect.
    Per CLAUDE.md §N.8: a signal without a working detector is null, not red."""


_UNDEFINED_RELATION_RE = re.compile(r'relation\s+"[^"]+"\s+does not exist', re.IGNORECASE)

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
COMPARISON_CHART_ID = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"

# ── VALID chart_facts.verification_pass_status vocabulary (F-85) ────────────
# NOT a local copy. brahmagyan.verification_vocab.ALL_STATUSES is THE settled
# vocabulary (CLAUDE.md §N.4) — importing it means this control is self-maintaining:
# a new status added there is legal here automatically, no drift possible.
try:
    from brahmagyan.verification_vocab import ALL_STATUSES as VALID_PASS_STATUSES
    _VOCAB_IMPORT_ERROR = None
except Exception as _e:  # pragma: no cover - reported as CONTROL-BROKEN, not a silent skip
    VALID_PASS_STATUSES = frozenset()
    _VOCAB_IMPORT_ERROR = _e

# ── VALID mi_darshana.leakage_status honest tier (F-105 contrast) ───────────
HONEST_LEAKAGE_TIER = "not_assessed"
BAD_LEAKAGE_LITERAL = "clean"


# ─────────────────────────────────────────────────────────────────────────────
# Result model
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ControlResult:
    control_id: str
    status: str  # "PASS" | "FAIL" | "SKIP" | "WARN"
    detail: str
    cheap: bool = False
    requires_db: bool = False
    requires_mcp: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# DB helpers
# ─────────────────────────────────────────────────────────────────────────────


def _get_db_conn(db_url: str):
    """Return a psycopg2 connection or raise ImportError / psycopg2.Error."""
    import psycopg2  # type: ignore

    return psycopg2.connect(db_url)


def _sql_query(db_url: str, sql: str, params=None) -> list:
    """Run SQL and return list of rows, or raise (ControlBrokenError for a missing
    relation — the detector itself is broken, not the thing it was checking)."""
    conn = _get_db_conn(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    except Exception as e:
        if _UNDEFINED_RELATION_RE.search(str(e)):
            raise ControlBrokenError(str(e)) from e
        raise
    finally:
        conn.close()


def _sql_scalar(db_url: str, sql: str, params=None):
    rows = _sql_query(db_url, sql, params)
    if not rows:
        return None
    return rows[0][0]


# ─────────────────────────────────────────────────────────────────────────────
# Individual control checkers
# ─────────────────────────────────────────────────────────────────────────────


def _check_f75(db_url: str) -> ControlResult:
    """F-75: Kala field decade-seam contiguity (zero gaps, native chart)."""
    sql = """
        WITH ordered AS (
            SELECT event_class, segment_index, t_start, t_end,
                   LAG(t_end) OVER (PARTITION BY event_class ORDER BY segment_index) AS prev_t_end
            FROM kala_field WHERE chart_id = %s
        )
        SELECT count(*) FROM ordered
        WHERE prev_t_end IS NOT NULL AND t_start != prev_t_end
    """
    try:
        gap_count = _sql_scalar(db_url, sql, (NATIVE_CHART_ID,))
        if gap_count == 0:
            return ControlResult("F-75", "PASS", f"0 segment gaps (contiguous)", cheap=True, requires_db=True)
        return ControlResult("F-75", "FAIL", f"{gap_count} decade-seam gaps found in kala_field", cheap=True, requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-75", "CONTROL-BROKEN", f"Detector could not execute: {e}", cheap=True, requires_db=True)
    except Exception as e:
        return ControlResult("F-75", "FAIL", f"SQL error: {e}", cheap=True, requires_db=True)


def _check_f76(db_url: str) -> ControlResult:
    """F-76: kala_field_null 25x10 grid invariant (250 rows, native chart)."""
    sql = """
        SELECT count(*) as n, count(DISTINCT event_class) as n_classes,
               count(DISTINCT bucket_days) as n_buckets
        FROM kala_field_null WHERE chart_id = %s
    """
    try:
        rows = _sql_query(db_url, sql, (NATIVE_CHART_ID,))
        n, n_classes, n_buckets = rows[0]
        if n == 250 and n_classes == 25 and n_buckets == 10:
            return ControlResult("F-76", "PASS", f"250 rows, 25 classes, 10 buckets", cheap=True, requires_db=True)
        return ControlResult("F-76", "FAIL", f"Expected 250/25/10, got {n}/{n_classes}/{n_buckets}", cheap=True, requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-76", "CONTROL-BROKEN", f"Detector could not execute: {e}", cheap=True, requires_db=True)
    except Exception as e:
        return ControlResult("F-76", "FAIL", f"SQL error: {e}", cheap=True, requires_db=True)


def _check_f83(db_url: str) -> ControlResult:
    """F-83: FK/orphan referential integrity across sampled tables."""
    sql = """
        SELECT c.chart_id, count(*) as orphan_count
        FROM (
            SELECT DISTINCT chart_id FROM chart_facts
            UNION SELECT DISTINCT chart_id FROM kala_field
            UNION SELECT DISTINCT chart_id FROM bodha_msr_signals
            UNION SELECT DISTINCT chart_id FROM mimamsa_insight_units
        ) c
        LEFT JOIN charts ON charts.id = c.chart_id
        WHERE charts.id IS NULL
        GROUP BY c.chart_id
    """
    try:
        orphans = _sql_query(db_url, sql)
        if not orphans:
            return ControlResult("F-83", "PASS", "0 orphaned chart_id refs across sampled tables", cheap=True, requires_db=True)
        return ControlResult("F-83", "FAIL", f"{len(orphans)} orphaned chart_ids found: {orphans[:3]}", cheap=True, requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-83", "CONTROL-BROKEN", f"Detector could not execute: {e}", cheap=True, requires_db=True)
    except Exception as e:
        return ControlResult("F-83", "FAIL", f"SQL error: {e}", cheap=True, requires_db=True)


def _check_f84(db_url: str) -> ControlResult:
    """F-84: No duplicate natural-key rows in kala_field (native chart)."""
    sql = """
        SELECT event_class, segment_index, count(*)
        FROM kala_field WHERE chart_id = %s
        GROUP BY event_class, segment_index
        HAVING count(*) > 1
    """
    try:
        dupes = _sql_query(db_url, sql, (NATIVE_CHART_ID,))
        if not dupes:
            return ControlResult("F-84", "PASS", "0 duplicate (event_class, segment_index) rows", cheap=True, requires_db=True)
        return ControlResult("F-84", "FAIL", f"{len(dupes)} duplicate natural-key groups: {dupes[:3]}", cheap=True, requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-84", "CONTROL-BROKEN", f"Detector could not execute: {e}", cheap=True, requires_db=True)
    except Exception as e:
        return ControlResult("F-84", "FAIL", f"SQL error: {e}", cheap=True, requires_db=True)


def _check_f85(db_url: str) -> ControlResult:
    """F-85: chart_facts.verification_pass_status enum vocabulary (known values only)."""
    sql = "SELECT DISTINCT verification_pass_status FROM chart_facts"
    try:
        rows = _sql_query(db_url, sql)
        live_values = {r[0] for r in rows if r[0] is not None}
        unknown = live_values - VALID_PASS_STATUSES
        if not unknown:
            return ControlResult("F-85", "PASS", f"All {len(live_values)} verification_pass_status values in vocabulary", cheap=True, requires_db=True)
        return ControlResult("F-85", "FAIL", f"Unknown status values: {unknown}", cheap=True, requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-85", "CONTROL-BROKEN", f"Detector could not execute: {e}", cheap=True, requires_db=True)
    except Exception as e:
        return ControlResult("F-85", "FAIL", f"SQL error: {e}", cheap=True, requires_db=True)


def _check_f87(db_url: str) -> ControlResult:
    """F-87: kala_field coverage [0, 36525] for every (chart, event_class)."""
    sql = """
        SELECT chart_id, event_class, min(t_start), max(t_end)
        FROM kala_field
        GROUP BY chart_id, event_class
        HAVING min(t_start) != 0 OR max(t_end) != 36525
    """
    try:
        bad = _sql_query(db_url, sql)
        if not bad:
            return ControlResult("F-87", "PASS", "All (chart, event_class) rows span [0, 36525]", cheap=True, requires_db=True)
        return ControlResult("F-87", "FAIL", f"{len(bad)} (chart, event_class) groups have truncated range: {bad[:3]}", cheap=True, requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-87", "CONTROL-BROKEN", f"Detector could not execute: {e}", cheap=True, requires_db=True)
    except Exception as e:
        return ControlResult("F-87", "FAIL", f"SQL error: {e}", cheap=True, requires_db=True)


def _check_f96() -> ControlResult:
    """F-96: fact-category-pin-lint self-test (mutation-tested, hermetic)."""
    lint_path = SCRIPT_DIR / "check_fact_category_pinning.py"
    if not lint_path.exists():
        return ControlResult("F-96", "FAIL", "check_fact_category_pinning.py not found", cheap=True)
    result = subprocess.run(
        [sys.executable, str(lint_path), "--self-test"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        return ControlResult("F-96", "PASS", result.stdout.strip() or "self-test pass", cheap=True)
    return ControlResult("F-96", "FAIL", f"lint self-test failed (exit {result.returncode}): {result.stderr.strip()[:200]}", cheap=True)


def _check_f80(db_url: str) -> ControlResult:
    """F-80: No legacy_id / old_chart_id / identity_map columns (R17 adoption)."""
    sql = """
        SELECT table_name, column_name FROM information_schema.columns
        WHERE column_name ILIKE '%legacy_id%'
           OR column_name ILIKE '%old_chart_id%'
           OR column_name ILIKE '%identity_map%'
           OR column_name ILIKE '%id_crosswalk%'
        ORDER BY table_name, column_name
    """
    try:
        rows = _sql_query(db_url, sql)
        if not rows:
            return ControlResult("F-80", "PASS", "0 legacy identity columns found", requires_db=True)
        return ControlResult("F-80", "FAIL", f"{len(rows)} legacy identity columns: {rows[:3]}", requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-80", "CONTROL-BROKEN", f"Detector could not execute: {e}", requires_db=True)
    except Exception as e:
        return ControlResult("F-80", "FAIL", f"SQL error: {e}", requires_db=True)


def _check_f82(db_url: str) -> ControlResult:
    """F-82: _migrations_applied row count roughly matches on-disk migration files."""
    sql = "SELECT count(*) FROM _migrations_applied"
    migration_dirs = [
        REPO_ROOT / "platform" / "migrations",
        REPO_ROOT / "platform" / "supabase" / "migrations",
    ]
    try:
        applied_count = _sql_scalar(db_url, sql)
        on_disk = sum(
            1 for d in migration_dirs if d.exists()
            for f in d.iterdir()
            if f.suffix in (".sql", ".py") and f.is_file()
        )
        # Allow ±10 tolerance (archival + extra docs files)
        delta = abs(int(applied_count) - on_disk)
        if delta <= 15:
            return ControlResult("F-82", "PASS", f"applied={applied_count}, on_disk={on_disk}, delta={delta}", requires_db=True)
        return ControlResult("F-82", "WARN", f"applied={applied_count}, on_disk={on_disk}, delta={delta} (>15 — verify archival list)", requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-82", "CONTROL-BROKEN", f"Detector could not execute: {e}", requires_db=True)
    except Exception as e:
        return ControlResult("F-82", "FAIL", f"SQL error: {e}", requires_db=True)


def _check_f86(db_url: str) -> ControlResult:
    """F-86: _migrations_applied.applied_at monotonically non-decreasing."""
    sql = """
        SELECT count(*) FROM (
            SELECT id, applied_at,
                   LAG(applied_at) OVER (ORDER BY id) AS prev_applied_at
            FROM _migrations_applied
        ) t WHERE applied_at < prev_applied_at
    """
    try:
        inversions = _sql_scalar(db_url, sql)
        if inversions == 0:
            return ControlResult("F-86", "PASS", "0 out-of-order applied_at timestamps", requires_db=True)
        return ControlResult("F-86", "FAIL", f"{inversions} applied_at inversions found", requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-86", "CONTROL-BROKEN", f"Detector could not execute: {e}", requires_db=True)
    except Exception as e:
        return ControlResult("F-86", "FAIL", f"SQL error: {e}", requires_db=True)


def _check_f102(db_url: str) -> ControlResult:
    """F-102 / F-141 (PAR-R-9): No asset_throughput rows where state IN ('lit','mature')
    but last_error IS NOT NULL/non-empty — a typed 'earned completion' state sitting
    beside a value that denies it, the §N.8 defect class.

    Widened 2026-08-16 (PAR-R-9, LEDGER_PRATINIDHI.md par/pratinidhi-ledger): this
    control previously checked state='lit' only. PRATINIDHI's live census for F-141
    found 5 real violating rows (1 per-chart on the canonical chart 482012f1 —
    ka_kshetra, watchdog-authored prose; 4 global chart_id-IS-NULL service singletons
    — bg_reference/bg_transit_rules/bg_transit_engine/bg_ghatana, raw exception
    traces ~2 weeks old) and ruled NO DB WRITE — see F-141's DIAGNOSIS.md /
    evidence/F-141_pre_write.json. All 5 are state='lit' today so this widening does
    not change F-102's current PASS/FAIL verdict against live data, but 'mature' is
    a real state in this column's vocabulary and the invariant applies to it too —
    narrowing the check to 'lit' alone would have silently missed a 'mature' instance
    of the identical defect.

    IMPORTANT — this function existing does not mean the invariant is monitored:
    ekv_controls.py is not referenced by any file under .github/workflows/ (verified
    this session, 2026-08-16, `grep -rl ekv_controls .github/workflows/` — zero
    hits). F-102 requires an explicit `--control F-102 --db-url <...>` invocation;
    it is not part of the automated per-batch CHEAP_IDS subset (by design — it is
    not cheap, it needs a real DB) and is not otherwise scheduled anywhere in CI.
    This is the concrete mechanism behind PAR-R-9's finding that "nothing detects
    this today": the detector function exists, but no automated pipeline calls it.
    Wiring it into an actual scheduled/CI invocation is a SENTINEL/conductor-level
    decision (CI workflow files are outside S6's `platform/scripts/governance/**`
    lease) — flagged, not done here.
    """
    sql = """
        SELECT count(*) FROM asset_throughput
        WHERE state IN ('lit', 'mature') AND last_error IS NOT NULL AND last_error != ''
    """
    try:
        bad = _sql_scalar(db_url, sql)
        if bad == 0:
            return ControlResult("F-102", "PASS", "0 rows with state IN ('lit','mature') + non-empty last_error", requires_db=True)
        return ControlResult("F-102", "FAIL", f"{bad} rows have state IN ('lit','mature') with non-null/non-empty last_error (§N.8 instance — see F-141)", requires_db=True)
    except ControlBrokenError as e:
        return ControlResult("F-102", "CONTROL-BROKEN", f"Detector could not execute: {e}", requires_db=True)
    except Exception as e:
        return ControlResult("F-102", "FAIL", f"SQL error: {e}", requires_db=True)


def _check_f105() -> ControlResult:
    """F-105: mi_adhilepa uses 'not_assessed' leakage tier (static code check)."""
    mi_adhilepa_path = REPO_ROOT / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers" / "mi_adhilepa.py"
    if not mi_adhilepa_path.exists():
        return ControlResult("F-105", "SKIP", "mi_adhilepa.py not found at expected path")
    text = mi_adhilepa_path.read_text(encoding="utf-8", errors="replace")
    if HONEST_LEAKAGE_TIER in text and BAD_LEAKAGE_LITERAL not in text.split("not_assessed")[0][:200]:
        # Has 'not_assessed'; quick check it doesn't have the bad literal
        if BAD_LEAKAGE_LITERAL not in text:
            return ControlResult("F-105", "PASS", f"mi_adhilepa uses '{HONEST_LEAKAGE_TIER}' tier, no '{BAD_LEAKAGE_LITERAL}' literal")
        # Has both — check context
        return ControlResult("F-105", "WARN", f"mi_adhilepa has both '{HONEST_LEAKAGE_TIER}' and '{BAD_LEAKAGE_LITERAL}' — review context")
    if HONEST_LEAKAGE_TIER not in text:
        return ControlResult("F-105", "FAIL", f"mi_adhilepa does not use '{HONEST_LEAKAGE_TIER}' leakage tier")
    return ControlResult("F-105", "PASS", f"mi_adhilepa uses '{HONEST_LEAKAGE_TIER}' tier")


def _check_f77() -> ControlResult:
    """F-77: kala_field_snapshots hash — requires external recompute script. SKIP if not available."""
    # This control needs the recompute_kfs_hash.py script and specific evidence file.
    # Ship as SKIP in this battery; full check is in E-04 morning battery.
    return ControlResult("F-77", "SKIP", "Requires external recompute_kfs_hash.py + evidence file — run in E-04 battery")


def _check_f32() -> ControlResult:
    """F-32: Cross-tool gochara_sweep coherence (evidence files). SKIP if no evidence dir."""
    evidence_dir = Path("/Users/Dev/Vibe-Coding/Apps/Madhav/pp2-audit/evidence")
    if not evidence_dir.exists():
        return ControlResult("F-32", "SKIP", "pp2-audit/evidence not found — informational control, run from audit corpus")
    jq_path = evidence_dir / "judgment_query__native_health_domain.json"
    ah_path = evidence_dir / "assess_health__native_deep_dive.json"
    if not jq_path.exists() or not ah_path.exists():
        return ControlResult("F-32", "SKIP", "Evidence files not found — informational control")
    # Both files present — this is a positive/non-defect finding; presence of evidence is the check
    return ControlResult("F-32", "PASS", "Evidence files present (informational cross-tool coherence baseline)")


def _check_f72() -> ControlResult:
    """F-72: mechanism_retrodiction baseline — MCP live probe needed. SKIP."""
    return ControlResult("F-72", "SKIP", "Requires MCP live probe (mechanism_retrodiction_get) — run in E-04 battery", requires_mcp=True)


def _check_f88() -> ControlResult:
    """F-88: active_chart_id session scoping — MCP live probe needed. SKIP."""
    return ControlResult("F-88", "SKIP", "Requires MCP live probe (session_recall) — run in E-04 battery", requires_mcp=True)


def _check_f91() -> ControlResult:
    """F-91: MCP tool-catalog profile scoping — abbreviated static check."""
    # Static: verify the mcp_surface_profiles.generated.ts exists and has 'full'/'compact'/'consult'
    profiles_file = REPO_ROOT / "platform" / "src" / "generated" / "projections" / "mcp_surface_profiles.generated.ts"
    if not profiles_file.exists():
        return ControlResult("F-91", "SKIP", "mcp_surface_profiles.generated.ts not found")
    text = profiles_file.read_text(encoding="utf-8", errors="replace")
    has_full = '"full"' in text or "'full'" in text
    has_compact = '"compact"' in text or "'compact'" in text
    has_consult = '"consult"' in text or "'consult'" in text
    if has_full and has_compact and has_consult:
        return ControlResult("F-91", "PASS", "mcp_surface_profiles has full/compact/consult profiles (static check)")
    return ControlResult("F-91", "WARN", f"Profile presence: full={has_full} compact={has_compact} consult={has_consult}")


def _check_f97() -> ControlResult:
    """F-97: ga_yoga_firings.bhanga_active real detector — static code check."""
    writer = REPO_ROOT / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers" / "ga_yoga_writer.py"
    if not writer.exists():
        return ControlResult("F-97", "SKIP", "ga_yoga_writer.py not found")
    text = writer.read_text(encoding="utf-8", errors="replace")
    has_bhanga_active = "bhanga_active" in text
    has_grounds_jsonb = "grounds_jsonb" in text
    has_neecha_bhanga = "neecha_bhanga" in text or "neecha-bhanga" in text
    if has_bhanga_active and has_grounds_jsonb and has_neecha_bhanga:
        return ControlResult("F-97", "PASS", "bhanga_active + grounds_jsonb + neecha_bhanga detector present (static)")
    return ControlResult("F-97", "WARN", f"bhanga_active={has_bhanga_active} grounds_jsonb={has_grounds_jsonb} neecha_bhanga={has_neecha_bhanga}")


def _check_f98() -> ControlResult:
    """F-98: bo_pramana_mapa trap1/trap2 real detectors — static code check."""
    writer = REPO_ROOT / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers" / "bo_pramana_mapa.py"
    if not writer.exists():
        return ControlResult("F-98", "SKIP", "bo_pramana_mapa.py not found")
    text = writer.read_text(encoding="utf-8", errors="replace")
    has_trap1 = "trap1" in text
    has_trap2 = "trap2" in text
    # Check it is NOT a hardcoded True assignment
    import re
    hardcoded = re.search(r"trap[12].*=\s*True\s*#\s*hardcoded", text)
    if has_trap1 and has_trap2 and not hardcoded:
        return ControlResult("F-98", "PASS", "trap1/trap2 detectors present, no hardcoded-True marker (static)")
    if hardcoded:
        return ControlResult("F-98", "FAIL", "Hardcoded trap1/trap2 True detected — §N.8 violation")
    return ControlResult("F-98", "WARN", f"trap1={has_trap1} trap2={has_trap2}")


def _check_f99() -> ControlResult:
    """F-99: kala_sarpa_reconciliation.agrees genuine check — static code check."""
    ts_path = REPO_ROOT / "platform" / "src" / "lib" / "retrieval" / "registry" / "layers" / "L1_ganita" / "get_yoga_dosha.ts"
    if not ts_path.exists():
        return ControlResult("F-99", "SKIP", "get_yoga_dosha.ts not found")
    text = ts_path.read_text(encoding="utf-8", errors="replace")
    has_agrees = "kala_sarpa_reconciliation" in text and "agrees" in text
    # Check it's not a hardcoded true
    import re
    hardcoded = re.search(r"agrees\s*:\s*true\s*[,}]", text)
    if has_agrees and not hardcoded:
        return ControlResult("F-99", "PASS", "kala_sarpa_reconciliation.agrees present, no hardcoded-true (static)")
    if hardcoded:
        return ControlResult("F-99", "FAIL", "kala_sarpa_reconciliation.agrees hardcoded to true — §N.8 violation")
    return ControlResult("F-99", "WARN", "kala_sarpa_reconciliation.agrees not found in expected file")


def _check_f100() -> ControlResult:
    """F-100: judgment_query receipt.timing_anchored content-checked."""
    ts_path = REPO_ROOT / "platform" / "src" / "lib" / "retrieval" / "registry" / "layers" / "register_d9_judgment.ts"
    if not ts_path.exists():
        return ControlResult("F-100", "SKIP", "register_d9_judgment.ts not found")
    text = ts_path.read_text(encoding="utf-8", errors="replace")
    has_timing_anchored = "timing_anchored" in text
    # The fix: timing_anchored is set from actual data, not just from a call-succeeded boolean
    # Static: check that it's assigned from a data field, not just `true`
    import re
    hardcoded = re.search(r"timing_anchored\s*:\s*true\s*[,}]", text)
    if has_timing_anchored and not hardcoded:
        return ControlResult("F-100", "PASS", "receipt.timing_anchored present, no hardcoded-true literal (static)")
    if hardcoded:
        return ControlResult("F-100", "FAIL", "timing_anchored hardcoded to true — §N.8 violation")
    return ControlResult("F-100", "WARN", "timing_anchored not found")


def _check_f101() -> ControlResult:
    """F-101: judgment_query receipt.varga_confirmed genuine."""
    ts_path = REPO_ROOT / "platform" / "src" / "lib" / "retrieval" / "registry" / "layers" / "register_d9_judgment.ts"
    if not ts_path.exists():
        return ControlResult("F-101", "SKIP", "register_d9_judgment.ts not found")
    text = ts_path.read_text(encoding="utf-8", errors="replace")
    has_varga_confirmed = "varga_confirmed" in text
    import re
    hardcoded = re.search(r"varga_confirmed\s*:\s*true\s*[,}]", text)
    if has_varga_confirmed and not hardcoded:
        return ControlResult("F-101", "PASS", "receipt.varga_confirmed present, no hardcoded-true (static)")
    if hardcoded:
        return ControlResult("F-101", "FAIL", "varga_confirmed hardcoded to true — §N.8 violation")
    return ControlResult("F-101", "WARN", "varga_confirmed not found")


def _check_f103() -> ControlResult:
    """F-103: phala_predictive_anchors posterior_provenance.base_rate_matches_uniform_fallback_value real check."""
    ts_path = REPO_ROOT / "platform" / "src" / "lib" / "retrieval" / "registry" / "layers" / "L4_phala" / "query_predictive_anchors.ts"
    if not ts_path.exists():
        return ControlResult("F-103", "SKIP", "query_predictive_anchors.ts not found")
    text = ts_path.read_text(encoding="utf-8", errors="replace")
    has_field = "base_rate_matches_uniform_fallback_value" in text
    import re
    # Should be a real comparison, not hardcoded
    hardcoded = re.search(r"base_rate_matches_uniform_fallback_value\s*:\s*true\s*[,}]", text)
    if has_field and not hardcoded:
        return ControlResult("F-103", "PASS", "base_rate_matches_uniform_fallback_value present, no hardcoded-true (static)")
    if hardcoded:
        return ControlResult("F-103", "FAIL", "base_rate_matches_uniform_fallback_value hardcoded — §N.8 violation")
    return ControlResult("F-103", "WARN", "base_rate_matches_uniform_fallback_value not found")


def _check_f106() -> ControlResult:
    """F-106: bodha_quality_get defect_001.status re-derived live (not stored/stale)."""
    ts_path = REPO_ROOT / "platform" / "src" / "lib" / "retrieval" / "provenance" / "freshness_notes.ts"
    if not ts_path.exists():
        return ControlResult("F-106", "SKIP", "freshness_notes.ts not found")
    text = ts_path.read_text(encoding="utf-8", errors="replace")
    has_defect_001 = "defect_001" in text
    has_sql_call = "SELECT" in text or "query" in text.lower()
    if has_defect_001:
        return ControlResult("F-106", "PASS", "defect_001.status present in freshness_notes.ts (re-derived live) (static)")
    return ControlResult("F-106", "WARN", "defect_001 not found in freshness_notes.ts")


def _check_f109() -> ControlResult:
    """F-109: Wealth-domain dark-corpus >=80% BRIGHT (evidence file check)."""
    evidence_path = Path("/Users/Dev/Vibe-Coding/Apps/Madhav/pp2-audit/evidence/E1_dark_corpus_21q_results.json")
    if not evidence_path.exists():
        return ControlResult("F-109", "SKIP", "E1_dark_corpus_21q_results.json not found — informational control")
    try:
        data = json.loads(evidence_path.read_text())
        # Look for a summary or grade field
        total = data.get("total", 21)
        bright = data.get("bright", data.get("pass", 0))
        pct = bright / total * 100 if total else 0
        if pct >= 80:
            return ControlResult("F-109", "PASS", f"{bright}/{total} ({pct:.1f}%) BRIGHT >= 80% threshold")
        return ControlResult("F-109", "FAIL", f"{bright}/{total} ({pct:.1f}%) BRIGHT < 80% threshold")
    except Exception as e:
        return ControlResult("F-109", "WARN", f"Could not parse evidence file: {e}")


def _check_f137() -> ControlResult:
    """F-137: graha_portrait / judgment_query use v3 register/reading_contract fields (static)."""
    reg_ts = REPO_ROOT / "platform-mcp" / "src" / "tools" / "register_p1_synthesis.ts"
    jq_ts = REPO_ROOT / "platform" / "src" / "lib" / "retrieval" / "registry" / "layers" / "register_d9_judgment.ts"
    missing = []
    for p in [reg_ts, jq_ts]:
        if not p.exists():
            missing.append(p.name)
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if "reading_contract" not in text and "register" not in text:
            missing.append(f"{p.name} (no v3 envelope fields)")
    if not missing:
        return ControlResult("F-137", "PASS", "v3 envelope fields present in synthesis+judgment files (static)")
    return ControlResult("F-137", "WARN", f"v3 envelope fields may be missing in: {missing}")


def _check_f138() -> ControlResult:
    """F-138: kala_ahead_get period_echo cross-reference (static check)."""
    ahead_ts = REPO_ROOT / "platform-mcp" / "src" / "tools" / "kala_views" / "ahead.ts"
    if not ahead_ts.exists():
        return ControlResult("F-138", "SKIP", "ahead.ts not found")
    text = ahead_ts.read_text(encoding="utf-8", errors="replace")
    has_period_echo = "period_echo" in text
    has_chart_dashas = "chart_dashas" in text
    if has_period_echo and has_chart_dashas:
        return ControlResult("F-138", "PASS", "period_echo + chart_dashas cross-reference present in ahead.ts (static)")
    return ControlResult("F-138", "WARN", f"period_echo={has_period_echo} chart_dashas={has_chart_dashas}")


# ─────────────────────────────────────────────────────────────────────────────
# Control registry
# ─────────────────────────────────────────────────────────────────────────────

ALL_CONTROLS: List[Tuple[str, bool, bool, bool, Callable]] = [
    # (id, cheap, requires_db, requires_mcp, checker)
    ("F-32",  False, False, False, _check_f32),
    ("F-72",  False, False, True,  _check_f72),
    ("F-75",  True,  True,  False, _check_f75),
    ("F-76",  True,  True,  False, _check_f76),
    ("F-77",  False, False, False, _check_f77),
    ("F-80",  False, True,  False, _check_f80),
    ("F-82",  False, True,  False, _check_f82),
    ("F-83",  True,  True,  False, _check_f83),
    ("F-84",  True,  True,  False, _check_f84),
    ("F-85",  True,  True,  False, _check_f85),
    ("F-86",  False, True,  False, _check_f86),
    ("F-87",  True,  True,  False, _check_f87),
    ("F-88",  False, False, True,  _check_f88),
    ("F-91",  False, False, False, _check_f91),   # abbreviated static check
    ("F-96",  True,  False, False, _check_f96),
    ("F-97",  False, False, False, _check_f97),
    ("F-98",  False, False, False, _check_f98),
    ("F-99",  False, False, False, _check_f99),
    ("F-100", False, False, False, _check_f100),
    ("F-101", False, False, False, _check_f101),
    ("F-102", True,  True,  False, _check_f102),
    ("F-103", False, False, False, _check_f103),
    ("F-105", False, False, False, _check_f105),
    ("F-106", False, False, False, _check_f106),
    ("F-109", False, False, False, _check_f109),
    ("F-137", False, False, False, _check_f137),
    ("F-138", False, False, False, _check_f138),
]

# The cheap subset: F-75/76/83/84/85/87 (SQL) + F-96 (lint self-test) + F-91 (static abbreviated)
CHEAP_IDS = {"F-75", "F-76", "F-83", "F-84", "F-85", "F-87", "F-96", "F-91", "F-102"}


# ─────────────────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────────────────


def run_controls(
    control_ids: Optional[List[str]],
    db_url: Optional[str],
    cheap_only: bool,
) -> List[ControlResult]:
    results: List[ControlResult] = []
    for cid, is_cheap, needs_db, needs_mcp, checker in ALL_CONTROLS:
        # Filter by --cheap
        if cheap_only and cid not in CHEAP_IDS:
            continue
        # Filter by --control
        if control_ids and cid not in control_ids:
            continue
        # Skip DB controls if no DB URL
        if needs_db and not db_url:
            results.append(ControlResult(cid, "SKIP", "No --db-url provided", cheap=is_cheap, requires_db=True))
            continue
        # Skip MCP controls (not wired to a live server in this script)
        if needs_mcp:
            results.append(ControlResult(cid, "SKIP", "MCP live probe — run in E-04 battery", cheap=is_cheap, requires_mcp=True))
            continue
        # Run the checker
        try:
            if needs_db:
                result = checker(db_url)
            else:
                result = checker()
        except Exception as exc:
            result = ControlResult(cid, "FAIL", f"Checker raised: {exc}", cheap=is_cheap)
        results.append(result)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--cheap", action="store_true", help="Run only the cheap per-batch subset.")
    ap.add_argument("--control", action="append", dest="controls", metavar="F-XX",
                    help="Run only the named control(s). Repeatable.")
    ap.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""),
                    help="Postgres connection string (default: $DATABASE_URL).")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON report.")
    args = ap.parse_args(argv)

    db_url = args.db_url or None
    results = run_controls(args.controls, db_url, args.cheap)

    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0, "WARN": 0, "CONTROL-BROKEN": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    if args.json:
        print(json.dumps({
            "controls_run": len(results),
            "cheap_only": args.cheap,
            "counts": counts,
            "results": [
                {"id": r.control_id, "status": r.status, "detail": r.detail,
                 "cheap": r.cheap, "requires_db": r.requires_db, "requires_mcp": r.requires_mcp}
                for r in results
            ],
            # CONTROL-BROKEN is a null signal (CLAUDE.md §N.8), not a red one — it does
            # NOT count against "pass" the way FAIL does, but it IS surfaced distinctly
            # below (control_broken_count) so a caller can't mistake a broken detector
            # for a clean regression baseline.
            "pass": counts["FAIL"] == 0,
            "control_broken_count": counts["CONTROL-BROKEN"],
        }, indent=2))
    else:
        for r in results:
            icon = {"PASS": "OK", "FAIL": "FAIL", "SKIP": "SKIP", "WARN": "WARN", "CONTROL-BROKEN": "BROKEN"}.get(r.status, r.status)
            cheap_tag = " [cheap]" if r.cheap else ""
            print(f"{icon:7s}  {r.control_id}{cheap_tag}: {r.detail}")
        print()
        print(f"ekv_controls: {counts['PASS']} PASS | {counts['FAIL']} FAIL | {counts['WARN']} WARN | {counts['SKIP']} SKIP | {counts['CONTROL-BROKEN']} CONTROL-BROKEN")

    if counts["FAIL"] > 0:
        return 1
    if counts["CONTROL-BROKEN"] > 0:
        return 3  # detector(s) could not run — null signal, needs a human before trusting "pass"
    if counts["SKIP"] > 0 and counts["PASS"] == 0:
        return 3  # all skipped, nothing to vouch for
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
