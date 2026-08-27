---
artifact: B-007 cockpit Clear authorization outcome (P2-B-007)
version: "1.0"
status: FIXED_AWAITING_INDEPENDENT_VERIFICATION
as_of: "2026-08-28T01:20:00Z"
session: "Claude Code session, P2 blocker B-007 fix (test-driven, isolated worktree)"
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/P2_BLOCKER_INTAKE_v1_0.md (P2-B-007 row)
  - platform/src/app/api/cockpit/clear/route.ts
  - platform/src/app/api/cockpit/clear/execute/route.ts
  - platform/src/lib/cockpit/clearScopeFilter.ts
  - platform/src/lib/auth/authorizeChartAccess.ts
  - platform/src/app/api/cockpit/clear/__tests__/route.authz.test.ts
  - PR https://github.com/Marsys-Technologies/Madhav/pull/1602
discovered_during: "independent verification of the sibling P2-B-001 fix (PR #1597)"
severity: P2 blocker — live production vulnerability (cross-user irreversible data deletion + PII disclosure)
---

# B-007 cockpit Clear authorization outcome (P2-B-007) v1.0

## Verdict

**FIXED.** Both cockpit Clear routes now enforce per-chart authorization via the
same `authorizeChartAccess` brain used by the sibling B-001 fix. Landed on
branch `pariprashna/p2-b007-cockpit-clear-authz` as PR
[#1602](https://github.com/Marsys-Technologies/Madhav/pull/1602), **deliberately
not merged** — left for independent verification per the campaign's
fix/verify separation.

This blocker was not on the original P2 intake. It was found as a **collateral
finding** while independently verifying the P2-B-001 fix (PR #1597): B-001
closed a cross-user *read* of chart PII on `GET /api/charts/[id]`; the same
"only `requireUser()`, never `authorizeChartAccess`" pattern was then found on a
pair of routes whose consequence is *irreversible deletion*, not disclosure.

## The vulnerability

`platform/src/app/api/cockpit/clear/route.ts` (preview) and
`platform/src/app/api/cockpit/clear/execute/route.ts` (the actual delete) both
checked only `getServerUser() !== null`. Neither ever consulted `charts.owner_id`
or `chart_grants` for the caller-supplied `chart_id`.

The authorization these routes *did* carry was real but orthogonal: a role gate
on **what kind of asset** may be cleared (`FORBIDDEN_L0` — non-`super_admin`
cannot clear the brahmagyan layer or any `scope='global'` asset). Nothing gated
**whose chart** was being cleared. The distinction is the whole finding.

Any authenticated user — default role `guest`, no grant, no relationship to the
chart — could therefore:

### 1. Self-serve a delete token

`POST /api/cockpit/clear` with an arbitrary `chart_id` (including the native's
real chart `482012f1-710e-4a25-994a-93821f5871aa`) and
`scope: 'layer' | 'asset' | 'global'` returned `200` with a valid
`preview_hash` plus a full inventory of the victim chart's built assets and row
counts.

The `preview_hash` was never an authorization control and cannot be pressed into
service as one: it is a shape/staleness check — a SHA-256 over
`{chart_id, scope, scope_target, affectedAssetIds, timeSlot}` with a 15-minute
slot — fully computable by whoever just requested the preview.

### 2. Wipe another user's chart

`POST /api/cockpit/clear/execute` with that hash then ran, inside one
transaction:

- `DELETE FROM <target_table> WHERE chart_id = $1` for every in-scope
  build-derived table (or the derived/explicit clear ops equivalent);
- `UPDATE asset_throughput SET state='dormant', last_built_at=NULL,
  rows_written=0, …` for the cleared assets;
- `UPDATE asset_throughput SET state='stale'` for the transitive downstream
  closure.

Irreversible. For the native's chart this is the entire L1–L5 build
(`chart_facts`, `chart_dashas`, `chart_divisionals`, `bodha_*`, `kala_*`,
`phala_*`, `mimamsa_*`).

### 3. Read another user's PII — and thereby bypass the only confirmation gate

For `scope === 'global'` or `scope === 'layer' && scope_target === 'brahmagyan'`,
the preview route ran:

```sql
SELECT subject_name, name FROM charts WHERE id=$1
```

and returned the result as `preview.requires_typed_confirmation`, **regardless of
the caller's ownership**. That value is exactly what `execute` compares
`typed_confirmation` against (`SUBJECT_NAME_MISMATCH`). So the one human
confirmation gate in the whole flow handed the attacker its own answer.

A non-`super_admin` reached that branch because `filterScopeAssets` **silently
narrows** a non-admin's `scope: 'global'` request to `per_chart` assets rather
than rejecting it — the request stays a `scope === 'global'` request as far as
the `requires_typed_confirmation` branch is concerned. Confirmed by reading
`clearScopeFilter.ts` directly; see the decision below for why the narrowing was
nonetheless kept.

## The fix

Minimal and focused. Both handlers now route through the established
`authorizeChartAccess` brain — the same one used by `GET /api/charts/[id]`
(B-001) and `resolveChartPageAccess` — immediately after the role read and
**before** any registry load, hash verification, or transaction:

```ts
const permission = await authorizeChartAccess({
  principal: { uid: user.uid, role: isSuperAdmin ? 'super_admin' : 'guest' },
  chartId: chart_id,
  db: { query: (sql: string, params?: unknown[]) => query(sql, params).then(r => ({ rows: r.rows })) } as DbLike,
})
if (permission !== 'all') {
  return NextResponse.json({ error: 'Forbidden', code: 'FORBIDDEN_CHART' }, { status: 403 })
}
```

`'all'` (owner or `super_admin`) is required, **not** merely non-`'deny'`. A
clear is destructive, so a `chart_grants` `'view'` grantee must not pass. This
matches the Nirmāṇa page guard, which already gates the cockpit UI itself on
`canBuild === (permission === 'all')` — the API now enforces what the page guard
already assumed.

Nothing else was touched: the `FORBIDDEN_L0` asset-class gate, the
`filterScopeAssets` narrowing, the SHAD-DARSHANA sweep-protection withholding,
the hash check, and the transaction all remain exactly as they were.

## Decision: `scope: 'global'` for non-admins is NOT rejected outright

The brief's stated preference was to reject a non-admin `scope: 'global'`
request outright rather than silently narrow it, *unless* a legitimate non-admin
caller of that scope exists. **One does**, and it is the primary control on the
page:

`CockpitShell.tsx`'s **"Clear all / Rebuild"** button (`openGlobalClearModal`)
posts `{ chart_id, scope: 'global', scope_target: null }` for *every* caller the
page guard admits. That guard is `resolveChartPageAccess` in
`clients/[id]/nirmana/page.tsx`, which redirects only when `!access.canBuild` —
and `canBuild` is `permission === 'all'`, satisfied by a plain chart **owner**
via `owner_id`, not only by `super_admin`. Rejecting `scope: 'global'` for
non-admins would break Clear-all and Rebuild for every owner on their own chart.

The narrowing was therefore kept, and the finding re-stated precisely:
`filterScopeAssets`' narrowing (`allowedScopes = ['per_chart']` for non-admins,
plus the unconditional `layer !== 'brahmagyan'` exclusion that applies even to
super_admins) is what confines a non-admin global request to chart-scoped
assets. **That narrowing was never the defect. The defect was that nothing
checked whose `chart_id` it narrowed onto.** With the ownership gate in place,
the `subject_name` branch is reachable only by the chart's owner (reading their
own subject name — not a leak) or by a `super_admin`, so finding (3) is closed
without changing scope semantics at all.

## Demonstrated-can-fail proof

New test file: `platform/src/app/api/cockpit/clear/__tests__/route.authz.test.ts`
— 10 cases, 5 DENY and 5 ALLOW, exercising the real `authorizeChartAccess`
implementation with only `@/lib/db/client` and `@/lib/firebase/server` mocked
(the same isolation discipline as the B-001 test).

### Before the fix — every DENY case returns `200`

```
 ❯ src/app/api/cockpit/clear/__tests__/route.authz.test.ts (10 tests | 5 failed)
   × (a)  DENIES a non-owner, non-admin authenticated user previewing another chart
   × (c)  DENIES the scope:global branch to a non-owner — no subject_name PII leak
   × (c2) DENIES a chart_grants view-grantee — a read grant is not a delete grant
   × (b)  DENIES a non-owner, non-admin user executing a clear — and issues NO DELETE
   × (b2) DENIES a view-grantee executing a clear

AssertionError: expected 200 not to be 200      // (a) preview
AssertionError: expected 200 to be 403          // (c) global-branch PII
AssertionError: expected 200 to be 403          // (c2) view-grantee preview
AssertionError: expected 200 not to be 200      // (b) execute
AssertionError: expected 200 to be 403          // (b2) view-grantee execute

 Test Files  1 failed (1)
      Tests  5 failed | 5 passed (10)
```

Case (b) is the sharpest: against unpatched code an attacker's `execute` call
returned `200` with `cleared.assets = 2` and real `DELETE` statements issued on
the pooled client.

### After the fix — 10/10 pass

All five DENY cases return `403 FORBIDDEN_CHART`. Case (b) additionally asserts
`mockGetPool` was **never called** and zero `DELETE` statements reached the
client — the destructive transaction never opens, rather than opening and
rolling back.

### The ALLOW cases are the regression guard

The five ALLOW cases — owner preview, owner `scope:'global'` preview (asserting
`requires_typed_confirmation === subject_name` still arrives), `super_admin`
preview of a chart they do not own, owner execute, `super_admin` execute —
**passed before the fix too**. They exist to prove the fix does not break the
real feature, and they still pass after it. This is the honest reading of the
proof: 5 of 10 could fail and did; 5 could not and were never expected to.

## Verification

| Gate | Result |
|---|---|
| New authz tests | 10/10 pass (5 demonstrated-can-fail) |
| `vitest run src/app/api/cockpit/ src/app/api/charts/ src/lib/auth/` | 121/121 pass |
| Full suite `npx vitest run` | **10222 passed**, 574 skipped, 2 todo, **0 failed** (973 files) |
| `npx tsc --noEmit` | clean (exit 0) |
| `npx eslint src/app/api/cockpit/clear/` | clean (exit 0) |

One pre-existing fixture was updated: `route.protected-assets.test.ts`'s
`seedRole()` helper queues one additional `owner_id` row, because that test uses
ordered `mockResolvedValueOnce` and the new gate issues one query ahead of the
registry load (its user owns `c1`, so `authorizeChartAccess` Rule 2
short-circuits and `chart_grants` is never read). **No assertion in that test
changed.**

## Items a reviewer should double-check

1. **The `scope: 'global'` decision.** The load-bearing claim is that
   `CockpitShell`'s Clear-all is owner-reachable, not admin-only. Worth
   confirming independently (`clients/[id]/nirmana/page.tsx` →
   `resolveChartPageAccess` → `canBuild`) before accepting that the narrowing
   stays.
2. **`'all'` vs `'view'`.** A `chart_grants` view-grantee is now denied the
   *preview* as well as the execute. Intentional — the preview yields the delete
   token and the PII — but it is a behavior tightening if any grantee-facing UI
   ever surfaced a Clear control.
3. **Non-existent `chart_id`** now yields `403 FORBIDDEN_CHART` instead of an
   empty `200` preview, via `authorizeChartAccess` Rule 4 (and the super_admin
   existence check). A minor, deliberate behavior change.
4. **Two copies of the gate.** Each route carries its own ~8-line call, mirroring
   the pre-existing verbatim duplication of `requireUser` / `getUserRole` /
   `FORBIDDEN_L0` across the pair. Both must stay in sync; consolidating them was
   judged out of scope for a minimal security fix, but it is a standing drift
   hazard worth a follow-up.
5. **Sibling routes not audited in this lane.** This session fixed only the two
   Clear routes. `POST /api/cockpit/runs`, `POST /api/cockpit/plan`,
   `POST /api/cockpit/refresh` and the cockpit stats routes take the same
   caller-supplied `chart_id` and were not examined here. Given that this
   blocker and B-001 are the same defect class found twice, a systematic sweep of
   every `chart_id`-accepting route against `authorizeChartAccess` is the
   obvious next lane.

## Disposition

- Branch: `pariprashna/p2-b007-cockpit-clear-authz`
- PR: https://github.com/Marsys-Technologies/Madhav/pull/1602 — **open, not
  merged**, awaiting independent verification.
- Worktree: `.clone/worktrees/pariprashna-b007-fix` (isolated; the shared
  checkout and all other worktrees were untouched).
- No migration, role, credential, or production data was touched by this session.
