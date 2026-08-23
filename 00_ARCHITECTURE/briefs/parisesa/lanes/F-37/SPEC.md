---
lane: F-37
spec_status: DRAFT
layer: L0_brahmagyan retrieval (chart-agnostic, global scope)
parent_diagnosis: /Users/Dev/par-night/coord-wt/00_ARCHITECTURE/briefs/parisesa/lanes/F-37/DIAGNOSIS.md
---

# F-37 SPEC — `query_yoga_catalog.ts`: `total` is page-length, not COUNT(*)

## 1. Root-cause statement

`query_yoga_catalog.ts:61` assigns `total: rows.length` — the size of the LIMIT-bounded page just fetched — because the handler runs only one SQL query (`SELECT * FROM brahma_yoga_catalog … LIMIT $1 OFFSET $2`) with no parallel `SELECT COUNT(*)`, so `total` is mathematically capped at `limit` and changes across pages of an unchanging catalog.

## 2. Files to change

| File | Change | Why |
|------|--------|-----|
| `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_yoga_catalog.ts` | Build `countSql` from the same `WHERE` predicates without `LIMIT`/`OFFSET`; run both via `Promise.all`; replace `total: rows.length` with `total_matching: Number(countResult.rows[0]?.total ?? 0)` and add `more_available: total_matching > rows.length`. | Sole file containing the defect. Correct pattern already exists at `L1_ganita/get_condition_composite.ts:87-99` in the same repo — apply verbatim. No schema migration required. |

## 3. Exit test

**Verification target:** `ref_yogas_get` tool (MCP shadow harness, Level 0)

```bash
# FAILS on today's code: total === 10 (page size), so the assertion total_matching > 10 fails.
# PASSES after fix: total_matching reflects the full catalog count (~175 rows per description).
ref_yogas_get(offset=50, limit=10)
  assert content.rows.length === 10
  assert typeof content.total_matching === 'number' && content.total_matching > 10
  assert content.more_available === true

# Stability check — same total_matching at a different page:
ref_yogas_get(offset=0, limit=1)
  assert content.total_matching === <same value as above call>
```

Named unit-test file (for CI): `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/test_query_yoga_catalog_total.ts`

Today's `total: rows.length` makes the first assertion fail at `total_matching > 10` (it returns 10). After fix, `total_matching` is ~175 and consistent across pages.

## 4. Sibling sites covered

F-37's DIAGNOSIS explicitly delegates the full Flavor-A census to `F-12/DIAGNOSIS.md §4a`. F-37 is responsible for exactly one site:

| Site | Lane | Disposition |
|------|------|-------------|
| `L0_brahmagyan/query_yoga_catalog.ts:61` | F-37 (this lane) | Fixed by this SPEC |
| `L1_ganita/get_dignity.ts:85`, `get_avasthas.ts:72`, `get_karakas.ts:118` | F-12 | Covered by F-12's SPEC |
| Remaining ~16 Flavor-A census sites in F-12/DIAGNOSIS §4a | F-12 or future lanes | Out of scope for F-37 — tracked under their own lanes, not excluded |

No sites are silently dropped: census ownership is assigned lane-by-lane; unlaned sites are F-12's scheduling burden.

## 5. Recurrence guard

Add to `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/test_query_yoga_catalog_total.ts`:

```typescript
it('total_matching is independent of limit/offset (no regression to rows.length)', async () => {
  const r1 = await handler({ limit: 1, offset: 0 }, {});
  const r2 = await handler({ limit: 1, offset: 100 }, {});
  // Both pages: 1 row served, but total_matching must be the same large number
  expect(r1.content.rows.length).toBe(1);
  expect(r2.content.rows.length).toBe(1);
  expect(r1.content.total_matching).toEqual(r2.content.total_matching);
  expect(r1.content.total_matching).toBeGreaterThan(1);
  expect(r1.content.more_available).toBe(true);
});
```

Fails closed on any regression: if `total_matching` reverts to `rows.length`, both calls return 1, `toEqual` passes but `toBeGreaterThan(1)` catches it.

## 6. Dependencies and rollback

**Lease pre-condition (blocker):** `L0_brahmagyan/**` is owned by S5 MŪLA, not S2. Lease transfer is documented in `F-12/NEEDS_LEASE.md` (covers this file family). No builder may open a PR until the conductor confirms the lease is assigned to S5 MŪLA.

**Other lane dependencies:** None — no other lane touches `query_yoga_catalog.ts`.

**Rebuild:** Not applicable. This is an L0 reference-catalog reader; it writes nothing to any asset table. Level 0 shadow run (above exit test) is sufficient before `CODE-LANDED` status is set. No Level 1 asset rebuild triggered.

**Rollback:** Revert one file (`query_yoga_catalog.ts`). No migration, no data side-effects.

**Not a writer-layer fix:** `writer_asset: null`, `data_delta: narrow`.

## 7. Coverage table

| Diagnosis sub-claim | Spec element |
|---------------------|--------------|
| F-37a: `total` = `rows.length` of LIMIT-bounded query | §2: parallel COUNT query → `total_matching` field |
| F-37b: `total` varies per page for unchanging catalog | §3 exit test: stability assert across two pages; §5 recurrence guard enforces equality |
| §3 mechanism: single SQL, no COUNT sibling | §2: `Promise.all([pageQuery, countQuery])` from established `get_condition_composite.ts:87-99` pattern |
| §4 sibling census: F-37's site is `query_yoga_catalog.ts:61` only | §4 table: single site scoped, others accounted for by lane |
| §5 BRANCH-EXISTS wrong (branch doesn't touch this file) | §6: no branch dependency; fix is standalone on a fresh worktree |
| §6 blast radius: S5 MŪLA lease, not S2 | §6: lease pre-condition stated as blocker |
| §6 no other-lane collision | §6: confirmed, no ordering constraint beyond lease |
