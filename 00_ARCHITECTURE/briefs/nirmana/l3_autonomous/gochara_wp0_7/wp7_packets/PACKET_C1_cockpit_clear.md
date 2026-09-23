---
artifact: WP7_PACKET_C1
packet_id: C-1
version: "1.0"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "Owner of the cockpit Clear path (platform/src/lib/cockpit/assetClearSpec.ts + platform/src/app/api/cockpit/clear/execute/route.ts) and of the ka_gochara registry rows"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.3 (EXPLICIT_CLEAR_OPS row + clear_tables row), §6.4 (Clear rules); GOCHARA_RULING_SHEET_v1_0.md N-7 (condition: EXPLICIT_CLEAR_OPS is a release condition), N-9 (iv)
authority_note: "Owed to its owner. Anchors read at this checkout: assetClearSpec.ts:19 (ClearOp type), :29-46 (deriveDeleteSqlFromCountSql + JOIN guard), :52 (EXPLICIT_CLEAR_OPS map); clear/execute/route.ts:160-183 (resolution order EXPLICIT_CLEAR_OPS → count_sql → target_table, per-asset SAVEPOINT :194-209); clear/route.ts:93 (allowedScopes), :114-117 (registry load), :119-120 (stale migration-540 comment — step-0 cleanup target)."
---

# C-1 — Cockpit Clear: `EXPLICIT_CLEAR_OPS['ka_gochara']` — three generation-scoped DELETEs + authoritative-generation refusal

## 1. Why this entry exists (F-24, verbatim intent)

After the §6.3 registry re-pin, `ka_gochara.count_sql` becomes
`… kala_gochara_windows WHERE chart_id=$1 AND generation='4.0'`, so the derived DELETE
(`deriveDeleteSqlFromCountSql`, `assetClearSpec.ts:29-46`) reaches **only the windows**.
`clear_tables` is display metadata read by the Atlas view only — it is not a cleanup
mechanism. A chart-owner Clear would delete `'4.0'` windows and **orphan every
`kala_gochara_contacts` and `kala_gochara_coverage` row** (breaking §N.3 and registry
integrity conjunct (i)). This entry is the cleanup contract; it is a **release
condition** (N-7/N-9 iv), not an optimization.

## 2. The exact entry (ready to apply)

### 2.1 SQL artifact — three DELETEs in dependency order

FK-child-first (coverage and contacts are manifest-generation metadata owned beside the
windows; no FK constraints exist among the three yet, but the WP6 migration may add
them — this order is safe either way). **No JOIN anywhere** (§6.4 rule: the derived
path bails on JOIN; explicit ops must stay WHERE-scoped plain DELETEs so the execute
route's per-asset SAVEPOINT semantics apply uniformly):

```sql
-- EXPLICIT_CLEAR_OPS['ka_gochara'] — generation-scoped, dependency order:
-- coverage first, then contacts, then windows. Each DELETE is a plain
-- WHERE-scoped statement (no JOIN — §6.4), chart-scoped, and pinned to
-- generation '4.0' so v1 / '3.0' / g3_* rows can never be reached here.
-- The authoritative-generation refusal (§3) is enforced BEFORE these run.
DELETE FROM kala_gochara_coverage WHERE chart_id = $1 AND generation = '4.0';
DELETE FROM kala_gochara_contacts WHERE chart_id = $1 AND generation = '4.0';
DELETE FROM kala_gochara_windows   WHERE chart_id = $1 AND generation = '4.0';
```

Note: the generation literal is `'4.0'` because this Clear contract is scoped to the
`'4.0'` publication generation by the registry re-pin (the count_sql being protected
carries the same literal). When a later generation (`'4.1'`) is published and the
count_sql re-pinned, this entry re-pins in the same migration — the same discipline as
the count_sql itself (plan §6.3). It is the Clear spec's mirror of the registry pin,
not a second source of truth.

### 2.2 TS spec-entry shape (mirroring assetClearSpec.ts conventions)

```ts
export const EXPLICIT_CLEAR_OPS: Record<string, ClearOp[] | null> = {
  // ... existing entries unchanged ...

  // ── L3 Kāla Gochara — contact ledger + coverage + windows (F-24) ─────────
  // ka_gochara's re-pinned count_sql reaches ONLY kala_gochara_windows; without
  // this entry a chart-owner Clear would orphan every kala_gochara_contacts /
  // kala_gochara_coverage row (§N.3 violation; integrity conjunct (i)). Three
  // generation-scoped DELETEs in dependency order, each WHERE chart_id=$1 AND
  // generation='4.0'. No JOIN (§6.4). Clears the '4.0' candidate/publication
  // generation ONLY — v1 / '3.0' / g3_* rows are unreachable here, and the
  // (table, generation) guard from runbook step 3 is the second lock.
  // REFUSAL: if '4.0' is this chart's authoritative_generation, a non-release
  // principal is refused before any statement runs (§3 below).
  ka_gochara: [
    { sql: "DELETE FROM kala_gochara_coverage WHERE chart_id = $1 AND generation = '4.0'" },
    { sql: "DELETE FROM kala_gochara_contacts WHERE chart_id = $1 AND generation = '4.0'" },
    { sql: "DELETE FROM kala_gochara_windows   WHERE chart_id = $1 AND generation = '4.0'" },
  ],
}
```

## 3. The refusal condition (§6.4) — what the cockpit owner must build

The plan's rule: a Clear whose target generation is the chart's
`authoritative_generation` is **refused** for an ordinary principal; the **release
authority** may perform it, and that execution **cascades an authority reset** (delete
the chart's `kala_gochara_authority` row — generation becomes `unpublished`, N-10
P-1d) **and marks the manifest `cleared`** (`UPDATE kala_gochara_publication SET
status='cleared'` — a status the WP6 CHECK must admit; WP1_CONTRACTS §5.2's enum is
`{candidate, published, superseded, rolled_back}`, so the CHECK needs `'cleared'` added
at WP6 — flagged here so the two owners coordinate). Otherwise serving returns empty
rows under a `published` label — the "appears built" failure Strategy §5 forbids
(conjunct (k) is its detector).

`ClearOp` today is only `{ sql: string }` (`assetClearSpec.ts:19`) and the execute
route (`clear/execute/route.ts:160-183`) maps entries to `{sql, params}` and runs them
under a per-asset SAVEPOINT. The refusal needs one small shape extension — either is
acceptable, pick one:

**Option A (recommended — minimal route change):** extend the entry to carry a guard:

```ts
export type ClearOp = { sql: string; guard?: { sql: string; refuse_message: string } }
// ka_gochara entry gains, on the FIRST op only:
guard: {
  sql: "SELECT 1 FROM kala_gochara_authority WHERE chart_id = $1 AND authoritative_generation = '4.0'",
  refuse_message: "Refused: '4.0' is this chart's authoritative generation. Only the release authority may clear it (cascades authority reset + manifest 'cleared').",
}
```

Execute-route semantics: if `guard` returns ≥1 row **and** the principal is not the
release authority, refuse the whole asset op (push to `failed_tables` with
`refuse_message`, no statements run). If the principal **is** the release authority,
run the three DELETEs **plus** the cascade, inside the same per-asset SAVEPOINT:
`DELETE FROM kala_gochara_authority WHERE chart_id = $1` and
`UPDATE kala_gochara_publication SET status = 'cleared' WHERE chart_id = $1 AND
generation = '4.0'`.

**Option B (no type change):** the refusal lives entirely in the route keyed on
`asset_id === 'ka_gochara'`. Rejected as a pattern (asset-specific logic in the generic
route is how F-24's class of bug grows), but recorded as the fallback if the shared
type is frozen.

## 4. Registry display value (with the F-24 caveat)

In the same §6.3 migration that re-pins `ka_gochara`:

```sql
UPDATE asset_registry
   SET clear_tables = '[kala_gochara_windows, kala_gochara_contacts, kala_gochara_coverage]'
 WHERE asset_id = 'ka_gochara';
```

**F-24 caveat (must accompany the migration comment):** `clear_tables` is **display
only** — read by the Atlas display (`atlas/schema/route.ts`, `AtlasView.tsx`,
`atlas/page.tsx`), never by the Clear runtime. The actual cleanup is the
`EXPLICIT_CLEAR_OPS['ka_gochara']` entry above. Setting `clear_tables` without the
explicit entry would make the Atlas *claim* a cleanup the runtime does not perform —
the exact v2.0 error F-24 caught.

## 5. Acceptance test (the §10 Clear/cleanup row)

On a disposable DB: fixture chart with `'4.0'` rows in all three relations + a
`published` manifest + authority row. (a) Chart-owner Clear → **refused**, all rows
intact, `failed_tables` carries the refusal message. (b) Release-authority Clear →
**zero rows** in all three relations, authority row gone, manifest `status='cleared'`,
and the serving layer now returns the `unpublished` coverage object (P-1d). (c) A chart
whose authority is `'3.0'` → `'4.0'` Clear proceeds (authority untouched). (d) The
derived count_sql path is never reached for `ka_gochara` (entry takes precedence,
`:160-163`). (e) Conjunct (k) fails loudly on any chart carrying a `published` manifest
over an empty generation.

## 6. What this packet does NOT do

- It does not touch the `(table, generation)` guard or the `is_active` filter (runbook
  steps 0/3, separate owners) — it composes with them.
- It does not clear `kala_gochara_publication` rows (the manifest survives, marked
  `cleared`/`rolled_back` — §4.7's immutability-with-history).
- It does not introduce a JOIN, a generation literal other than the pinned `'4.0'`, or
  any reach toward `v1`/`'3.0'`/`g3_*` rows.
- It does not edit the registry itself (migration ≥1071, WP10-adjacent authority class
  — this packet is the design artifact that migration lifts verbatim).
