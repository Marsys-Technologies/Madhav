---
artifact: CLAUDECODE_BRIEF_L3_KALA_BUILDPATH_CODE_FIX_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KALA_BUILDPATH_CODE_FIX
version: 1.0
status: AUTHORED — CODE-ONLY fix so a future click-Build builds all 12 Kāla assets correctly
executor: Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
HARD_CONSTRAINT: >
  CODE ONLY. Do NOT rebuild data, do NOT run any ka_* writer against prod, do NOT execute a
  build run, do NOT apply any migration that mutates chart data. The native will run the actual
  rebuild on the Nirmāṇa tracker. Migrations here only touch asset_registry metadata
  (has_writer flag / asset_type / service flags) — NO data tables. The ka_tulana writer is
  ADDED to code but NOT executed in this brief.
source_audit: build-path runtime audit (Cowork + subagent, 2026-06-21)
---

# L3 KĀLA BUILD-PATH — CODE-ONLY FIX

## WHY (the problem this fixes)

The Kāla layer **displays 12 assets** but a click-Build/Rebuild currently plans only **11** —
`ka_tulana` is silently excluded from every build plan. Root cause: the plan query
(`runs/route.ts:81`) filters `WHERE has_writer = true`, and migration 342's `has_writer=true`
list (lines 27-29) includes 11 ka_* assets but **OMITS `ka_tulana`**. `ka_tulana` is the only one
of the 5 Kāla services with no writer shim + no `@register` (it's a pure serve-time ranker,
`services/ka_tulana/ranker.py`). The other 4 services each have a thin self-test writer that
returns 0 rows. So today: **displayed = 12, built = 11, ka_tulana never regenerates or
health-checks.**

**Native decision (2026-06-21):** make displayed = built by giving `ka_tulana` a thin self-test
writer exactly like the other 4 services, then flag `has_writer=true`. This is CODE ONLY — the
writer is added but NOT run here.

The rest of the build path was audited and is **clean** (see §4): layer-rebuild plans all
writer-bearing ka_*, topo-sorts correctly, dispatches with chart_id, discover_all() imports all
shims without failure, services self-test to 0 rows, cascade-stale closes consistently. The only
code gap is ka_tulana's missing writer; two minor metadata items are in §3.

---

## §1 — ADD: ka_tulana self-test writer (mirror the ka_gochara pattern EXACTLY)

The reference pattern is `services/ka_gochara/writer.py` + `pipeline/orchestrator/writers/ka_gochara.py`
(a re-export shim). Replicate it for ka_tulana.

**1a. New file `platform/python-sidecar/services/ka_tulana/writer.py`:**
- Mirror `ka_gochara/writer.py` structure: module docstring stating the FROZEN-contract adherence
  (uses `ctx.db_conn`, NEVER commits/rolls back/closes, NEVER writes asset_throughput, returns
  `WriterResult(rows_inserted=0)` — service asset, no data rows).
- `_run_selftest() -> (ok, detail_json)`: exercise the REAL ranker so the health signal is
  meaningful. Build a small synthetic set of `WindowInput`s and assert a stable order:
  ```python
  from services.ka_tulana.ranker import KaTulanaService, WindowInput
  from datetime import date
  svc = KaTulanaService()
  # two synthetic windows: a rare high-convergence one must outrank a common low one
  a = WindowInput(window_id="t_a", convergence_score=0.9, rarity_years=30.0,
                  confidence_score=0.85, peak_date=date(2027,1,1), domains=["career"])
  b = WindowInput(window_id="t_b", convergence_score=0.4, rarity_years=2.0,
                  confidence_score=0.5,  peak_date=date(2027,1,1), domains=["wealth"])
  ranked = svc.rank_windows([a, b], reference_date=date(2026,1,1))
  ok = ranked[0].window_id == "t_a"   # the rarer/stronger window ranks first
  detail = json.dumps({"test":"tulana_rank_order","top":ranked[0].window_id,"n":len(ranked)})
  ```
  (Match the ACTUAL `WindowInput` / `rank_windows` signatures in ranker.py — adjust field names
  to what the dataclass really declares; the audit confirmed `KaTulanaService.rank_windows`,
  `.compare`, `.attention_map` + `WindowInput`/`RankedWindow` exist. Do NOT invent fields.)
- `_update_registry_health(conn, ok, detail)`: same UPDATE asset_registry SET service_health,
  last_selftest_at, selftest_detail WHERE asset_id='ka_tulana'. NO commit.
- `_build_writer_class()`: `@register("ka_tulana")` class `KaTulanaWriter(WriterBase)` with
  `asset_id="ka_tulana"`, `run(ctx)` that honors `ctx.dry_run` (return early, 0 rows), else
  runs selftest + updates health, returns `WriterResult(asset_id, rows_inserted=0, notes=...)`.
- Trigger registration at module load: `KaTulanaWriter = _build_writer_class()`.

**1b. New file `platform/python-sidecar/pipeline/orchestrator/writers/ka_tulana.py`** (shim):
```python
"""Orchestrator registration shim for ka_tulana (L3 Kāla — cross-pattern prioritization service).
All logic lives in services/ka_tulana/writer.py. Service asset: run(ctx)→WriterResult(rows_inserted=0)."""
from services.ka_tulana.writer import KaTulanaWriter  # noqa: F401
__all__ = ["KaTulanaWriter"]
```

**1c.** Confirm `discover_all()` (`writers/__init__.py`) auto-imports the new shim (it iterates the
writers dir — no manual registration needed). Verify the import chain resolves.

## §2 — FLAG: has_writer=true for ka_tulana (asset_registry metadata only — NO data)

New migration `platform/supabase/migrations/<next>_ka_tulana_has_writer.sql`:
```sql
-- ka_tulana now has a self-test writer; include it in build plans so displayed=built (12/12).
UPDATE asset_registry SET has_writer = true WHERE asset_id = 'ka_tulana';
```
Idempotent metadata-only UPDATE. **Touches asset_registry only — NO chart data.** Note: per the
CI silent-skip finding, confirm this migration actually applies to prod via the proper path (it
will be applied when the native next deploys / runs migrations; it does NOT rebuild data).

## §3 — Two minor metadata items found in the audit (fix in the same PR; metadata-only)

**3a. Service-type flags for ka_gochara + ka_dasha_kala (verify, fix only if wrong).** Migration
342 set `asset_type='service'` for ONLY ka_graha_sancara + ka_muhurta_seva. ka_gochara +
ka_dasha_kala rely on the original (non-version-controlled) seed for their service flag. Add to
the §2 migration a DEFENSIVE idempotent set so prod is guaranteed correct:
```sql
UPDATE asset_registry SET asset_type = 'service'
  WHERE asset_id IN ('ka_gochara','ka_dasha_kala','ka_tulana') AND asset_type = 'data';
```
(Build impact today: none — the runner marks services lit regardless; this only fixes the cosmetic
stats display via the dual-check. Including it makes the registry self-consistent.)

**3b. (OPTIONAL, governance — flag, do not necessarily do now) ka_* registry rows + depends_on are
not in any migration.** The ka_* asset_registry rows + their `depends_on` edges were seeded by the
retired `run_ka_*_prod.py` path directly into prod, not via a version-controlled migration. topoSort
correctness depends on those prod-resident edges. A fresh DB cannot reconstruct the L3 DAG from
source. Recommend (separate task, not this PR) back-filling a `register_ka_assets` migration that
INSERTs the 12 ka_* rows + depends_on idempotently. NOT required for the native's click-Build to
work (prod already has the edges) — but required for true reproducibility. Flag it; defer the build.

## §4 — What was audited CLEAN (no change needed; for confidence)

- Layer-rebuild (`scope='layer'`, `'kala'`, `action='rebuild'`) → plans ALL has_writer ka_* (will
  be 12 after §1+§2). topoSort (`plan.ts:218`) orders by depends_on; valid acyclic order.
- Dispatch passes run-id; runner.py loads chart_id+plan from build_runs; walks plan in order.
- discover_all() hard-fails on any broken writer import (CI net via test_ga_orchestrator_conformance)
  — all 11 (→12) ka_ shims import clean; heavy deps (swisseph) are lazy-imported inside methods.
- ka_sangam top-level imports (KaDashaKalaService, KaGocharaService, engine symbols) all resolve.
- pipeline/transit_search.py exists with find_aspect_events (the old "never built" note is STALE).
- Services return rows_inserted=0 → marked lit; artifacts read ctx.config['chart_id'].
- Cascade-stale: a full layer rebuild runs all downstream in the same plan → ends all-lit, no
  trailing stale (so the current ka_vighnakara/ka_yojaka stale badges WILL clear on the native's
  rebuild — they are downstream-stale from prior partial activity, and a full Kāla rebuild
  re-lits them through the orchestrator's own asset_throughput stamp; no reconcile hack needed).

## §5 — Acceptance criteria (CODE-ONLY; NO data rebuild)

1. **[verify: file exists]** `services/ka_tulana/writer.py` + `writers/ka_tulana.py` shim created,
   mirroring the ka_gochara pattern; `@register("ka_tulana")` present.
2. **[verify: pytest, NO prod]** a unit test imports the writer, runs `_run_selftest()` in isolation
   (no DB), asserts it returns ok=True on the synthetic window set. Add to tests/l3.
3. **[verify: import]** `discover_all()` imports the new shim without error (run the existing
   orchestrator-conformance test; it must stay green with 12 ka_ writers discoverable).
4. **[verify: grep]** the ka_tulana writer NEVER calls `ctx.db_conn.commit()/.rollback()/.close()`
   and NEVER writes asset_throughput (FROZEN contract).
5. **[verify: migration is metadata-only]** the new migration only UPDATEs asset_registry
   (has_writer / asset_type) — touches NO chart-data table. Do NOT apply it in a way that triggers
   a build.
6. **[do NOT do]** do NOT POST a build run, do NOT execute any ka_* writer against prod, do NOT
   call reconcile. The native runs the rebuild on the Nirmāṇa tracker.
7. **[verify: plan math]** after has_writer=true lands, a layer-rebuild plan for 'kala' would
   include 12 ka_* (confirm by reading resolveBuildPlan logic / a unit test on the plan resolver
   with a mock registry — NOT by running a real build).

## §6 — Embedded commands
```bash
git checkout main && git pull --ff-only origin main
git checkout -b fix/l3-ka-tulana-buildable
# reference pattern:
sed -n '1,113p' platform/python-sidecar/services/ka_gochara/writer.py
# confirm the real ranker API before writing the selftest:
grep -nE "class WindowInput|def rank_windows|def __init__" platform/python-sidecar/services/ka_tulana/ranker.py
# ... author the two files + migration ...
cd platform/python-sidecar && python -m pytest tests/l3 -k "tulana or orchestrator or discover" -q
# DO NOT run any run_*_prod.py, DO NOT POST /api/cockpit/runs, DO NOT apply migration to prod here.
git add -A && git commit -m "fix(l3): add ka_tulana self-test writer + has_writer flag so click-Build plans all 12 Kāla assets (code only; no data rebuild)"
git push -u origin fix/l3-ka-tulana-buildable
gh pr create --fill --base main
```

## §7 — Definition of done
- [ ] ka_tulana writer + shim added (ka_gochara pattern); @register fires; contract-clean.
- [ ] has_writer=true + defensive service-type migration (metadata-only) added, NOT data-applied.
- [ ] Unit test: ka_tulana selftest passes in isolation; orchestrator-conformance green with 12 ka_.
- [ ] Plan-resolver confirmed (by logic/unit test) to include all 12 ka_* on a 'kala' layer rebuild.
- [ ] §3b governance gap (ka_* registry-in-migration) FLAGGED for a separate task; not built here.
- [ ] ZERO data writes, ZERO build runs, ZERO writer executions against prod. Native rebuilds on the tracker.

---
*End of brief. After this lands + the native clicks Rebuild on Kāla: 12 displayed = 12 planned =
12 built, DAG-ordered, counts reconcile (7 artifacts sum to layer total; 5 services = 0 rows),
and the stale badges clear through the orchestrator's own build-state stamp.*
