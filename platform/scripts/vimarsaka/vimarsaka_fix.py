#!/usr/bin/env python3
"""
Vimarśaka-FIX — 6-check acceptance gate for orchestrator D1+D2+D3+D4 fixes.

Run from repo root:
    PROD_DB_URL="postgresql://..." python platform/scripts/vimarsaka/vimarsaka_fix.py

All 6 checks must PASS before Tier 0 may proceed.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[2]  # platform/
REPO     = PLATFORM.parent                       # repo root
ROOT     = PLATFORM / "python-sidecar"           # python-sidecar/ (orchestrator code)

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    results.append((name, ok, detail))
    status = PASS if ok else FAIL
    print(f"  [{status}] {name}: {detail}")


# ── Check 1: D1 — discover_all() wired in runner.py AND asset_runner.py ──────

runner_src = (ROOT / "pipeline/orchestrator/runner.py").read_text()
asset_runner_src = (ROOT / "pipeline/orchestrator/asset_runner.py").read_text()

check(
    "D1_discover_all_wired",
    "discover_all()" in runner_src and "discover_all()" in asset_runner_src,
    "discover_all() present in runner.py and asset_runner.py",
)

# ── Check 2: D1 — registry actually populates after discover_all() ────────────

try:
    sys.path.insert(0, str(ROOT))
    from pipeline.orchestrator.writers import discover_all, list_writers
    discover_all()
    writers = list_writers()
    missing = [a for a in ("bg_reference", "bg_ontology") if a not in writers]
    check(
        "D1_registry_populates",
        len(missing) == 0,
        f"bg_reference + bg_ontology in registry; all registered: {sorted(writers)}" if not missing
        else f"MISSING from registry: {missing}",
    )
except Exception as exc:
    check("D1_registry_populates", False, f"import error: {exc}")

# ── Check 3: D2 — no stale module names in global_runner.py ──────────────────

STALE_NAMES = [
    "brahmagyan_sarani",
    "brahmagyan_kalapancanga",
    "brahmagyan_shastra",
    "brahmagyan_samanvaya",
    "brahmagyan_sutravali",
    "brahmagyan_upaya_kosha",
    "brahmagyan_text_index",
    "_build_writer_registry",
]

global_runner_src = (ROOT / "pipeline/orchestrator/global_runner.py").read_text()
found_stale = [n for n in STALE_NAMES if n in global_runner_src]

check(
    "D2_no_stale_global_registry",
    len(found_stale) == 0,
    "no stale module names in global_runner.py" if not found_stale
    else f"stale names still present: {found_stale}",
)

# ── Check 4: D3 — no bare `chart_id = %s` in asset_runner.py ────────────────

bare_eq = re.findall(r"chart_id\s*=\s*%s", asset_runner_src)
check(
    "D3_null_safe_throughput",
    len(bare_eq) == 0,
    "no bare 'chart_id = %s' in asset_runner.py" if not bare_eq
    else f"{len(bare_eq)} bare equality match(es) found — must use IS NOT DISTINCT FROM",
)

# ── Check 5: D3 — asset_throughput_global_idx present in DB ──────────────────

prod_url = os.environ.get("PROD_DB_URL", "")
if not prod_url:
    check("D3_global_index_present", False, "PROD_DB_URL not set — skip DB check (FAIL)")
else:
    try:
        import psycopg
        with psycopg.connect(prod_url, autocommit=True) as conn:
            row = conn.execute(
                "SELECT indexname FROM pg_indexes WHERE indexname = 'asset_throughput_global_idx'"
            ).fetchone()
        check(
            "D3_global_index_present",
            row is not None,
            "asset_throughput_global_idx exists in pg_indexes" if row
            else "index NOT FOUND — apply migration 184 first",
        )
    except Exception as exc:
        check("D3_global_index_present", False, f"DB error: {exc}")

# ── Check 6: D4 — topo regression test file exists on disk ───────────────────

topo_test = REPO / "platform/src/lib/build/__tests__/plan.l0-layer.test.ts"
check(
    "D4_plan_topo_test_exists",
    topo_test.exists(),
    str(topo_test) if topo_test.exists() else f"NOT FOUND: {topo_test}",
)

# ── Summary ───────────────────────────────────────────────────────────────────

print()
passed = sum(1 for _, ok, _ in results if ok)
total = len(results)
print(f"  {passed}/{total} PASS")

if passed == total:
    print("\n  SEAL: orchestrator-fixes APPROVED\n")
    sys.exit(0)
else:
    failed_names = [n for n, ok, _ in results if not ok]
    print(f"\n  BLOCKED — fix failing checks: {failed_names}\n")
    sys.exit(1)
