---
artifact: BUILD_TRACKER_CLEAR_BRIEF_v1_0.md
canonical_id: BUILD_TRACKER_CLEAR_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: BUILD_TRACKER_HARDENING_MASTER_v1_0.md
purpose: Prove Delete/Clear deletes COMPLETELY (no silent skips) and ONLY in-scope (no over-delete on shared tables), across asset/layer/global scopes.
audience: Claude Code (Antigravity)
---

# Clear / Delete Hardening — "deletes everything in scope, nothing out of scope"

## §0 — State of the fix (from audit)
Commits `c239d61d` + `7ac8f3c0` made `count_sql` the single source of truth for both counting and
deleting via `deriveDeleteSqlFromCountSql`, added per-asset SAVEPOINTs, and removed silent skips
(unresolved asset → `failed_tables`). The execute route resolution order is:
`EXPLICIT_CLEAR_OPS` → derived-from-count_sql → `target_table` fallback → fail. This is sound.

**Residual risk (audit F2):** the regex fails closed on non-simple SHAPE but not on a simple-but-
semantically-broad predicate. A `chart_facts` asset whose count_sql lacks its `fact_category`
predicate would derive a DELETE that wipes another layer's shared-table rows. Only an end-to-end
DB-arbitrated test catches this — which is exactly the in-flight verification.

## §1 — FIRST: consume the in-flight verification result
The native will paste the RESULT of the layer-clear UI verification (the verbatim prompt is in
`BUILD_TRACKER_HARDENING_HANDOFF_v1_0.md §3`). Read it before doing anything else:
- **If it reported PASS** (every L1/ga_ category → 0, every non-ga_ category UNCHANGED, zero
  failed_tables, UI/DB agree) → layer-clear is proven; skip to §2 (asset + global scope coverage).
- **If it found an UNDER-delete** (an L1 category still > 0) → that asset's count_sql didn't derive a
  working DELETE. Name the asset, inspect its `count_sql` + `target_table` in `asset_registry`, and
  add an `EXPLICIT_CLEAR_OPS` entry (like `ga_condition`) or fix the count_sql. Re-prove.
- **If it found an OVER-delete** (a non-ga_ category dropped) → a derived DELETE was too broad
  (F2 realized). HALT semantics: identify the asset, confirm its count_sql is missing a scoping
  predicate, and EITHER tighten count_sql to include the `fact_category`/`chart_id` predicate OR move
  it to `EXPLICIT_CLEAR_OPS` with the correctly-scoped DELETE. Re-prove the full BEFORE/AFTER.
- **If UI showed rows but DB was 0** → that is the stale-display class (F1), handled by the REFRESH
  brief, NOT a clear bug. Note it and proceed.

## §2 — Extend coverage to asset + global scopes (layer is covered by §1)
PASTE TO CLAUDE CODE (run only after §1 is PASS):
```
Prove the cockpit clear is complete + scope-tight for ASSET and GLOBAL scopes, on chart
1c826d5a-41cb-4450-b4dc-59d440e5f75a (SAFE non-native). NEVER touch native 482012f1. Chrome read-tier
→ mcp__Claude_in_Chrome__* for UI. DB reads via :5433 are the arbiter. Confirm dev server serves the
current main.

A — ASSET scope (3 representative ga_ assets covering all 3 resolution paths):
  pick one EXPLICIT_CLEAR_OPS asset (ga_condition), one derived-from-count_sql chart_facts asset
  (e.g. a panchanga_* or graha_avastha asset), and one dedicated-table asset (ga_dashas→chart_dashas).
  For each: PRE DB count → UI asset-scope clear → capture clear/execute response (failed_tables MUST
  be empty) → POST DB count == 0 for that asset's rows ONLY → assert NO other asset's rows changed
  (re-run the full fact_category breakdown; every OTHER category unchanged). Report a 3-row table.

B — OVER-DELETE GUARD on a shared table: before/after the chart_facts asset clear in (A), snapshot
  `SELECT fact_category, count(*) FROM chart_facts WHERE chart_id='1c826d5a-...' GROUP BY 1`. ONLY the
  cleared asset's category(ies) may drop to 0; every L0/other-layer category is byte-identical.

C — GLOBAL scope (super_admin + typed-confirmation path) — DO THIS READ-ONLY / DRY-RUN ONLY: open the
  global clear modal, screenshot it, confirm it (1) requires the typed subject-name confirmation and
  (2) the preview lists the full asset set. DO NOT confirm-execute a global clear on 1c826d5a in this
  step (global wipes L0 reference data shared across charts). Just prove the guard + preview render.
  If you believe a real global-clear execution is needed to fully prove it, STOP and ask the native.

Deliver: the asset-scope 3-row BEFORE/AFTER table, the shared-table category snapshot proving zero
over-delete, the global-modal screenshot proving the typed-confirm guard, and a PASS/FAIL per scope.
STOP and report.
```

## §3 — Hardening edits that may fall out (apply only if §1/§2 surface them)
- New/edited `EXPLICIT_CLEAR_OPS` entries for any asset whose count_sql can't derive a tight DELETE.
- A `count_sql` predicate tightening for any asset that derived an over-broad DELETE.
- (If F1 not yet shipped) ensure cleared assets null `rows_written` — but that lives in the REFRESH
  brief; cross-reference, don't duplicate.
Add a vitest case in `clear/__tests__` for every new EXPLICIT_CLEAR_OPS entry (asserts the exact
DELETE sql + params).

## §4 — Done when
Every scope (asset, layer, global-preview) proven on 1c826d5a with DB-arbitrated BEFORE/AFTER:
in-scope rows → 0, out-of-scope rows unchanged, zero failed_tables, and the global typed-confirm
guard renders. Any over-delete is a HALT until the offending derivation is tightened.
