# NTAP Label Acceptance Release Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure every monitor-proposed NTAP baseline label catalogue can be accepted atomically without manufacturing a human asset name or description.

**Architecture:** The accepted catalogue remains a deterministic projection of `asset_registry`. When all three optional human-label fields are absent, the candidate records the explicit governed placeholder `Not yet catalogued` in `description`; its source reference remains the registry asset. This makes the candidate valid for the existing catalogue contract, includes the decision in the exact catalogue digest, and leaves the manifest and execution progress untouched.

**Tech Stack:** Next.js/TypeScript, Vitest, Zod, PostgreSQL transaction seam.

**Spec:** `docs/superpowers/specs/2026-08-26-ntap-tracker-reliability-design.md` (§ baseline acceptance, especially line 34).

## Global Constraints

- The monitor remains proposal-only: it must not freeze definitions, accept a catalogue, advance stages, dispatch builds, or mutate execution tables.
- A missing human label is rendered exactly as `Not yet catalogued`; it is not a Sanskrit or English asset name.
- The canonical catalogue digest must contain the deterministic rendered placeholder so the displayed candidate and accepted evidence match exactly.
- Preserve registry-derived labels unchanged whenever any source label is present.
- Never import historical JSON/JSONL, manufacture progress, start/resume Nirmāṇa execution, use credentials, or modify production state.
- Verify the acceptance transaction accepts the all-null registry case and retains unknown stage/layer/progress semantics.

---

### Task 1: Make the baseline candidate acceptably complete

**Files:**
- Modify: `platform/src/lib/nirmana-elevation/monitor.ts:47-76,244-258`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/monitor.test.ts:94-107`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/definitions.test.ts:123-180`

**Interfaces:**
- Consumes: `NirmanaRegistryContractRow.sanskrit_name`, `.english_name`, and `.english_description`.
- Produces: `buildNirmanaBaselineCandidate(rows): NirmanaBaselineCandidate` whose `labels` validate under `NirmanaAssetLabelSchema` and whose `catalogue_sha256` is accepted by `acceptNirmanaBaselineCandidate`.

- [ ] **Step 1: Write the failing candidate test**

Replace the all-null expectation with an exact rendered placeholder assertion:

```ts
expect(candidate.labels).toEqual([expect.objectContaining({
  asset_id: 'bg_uncatalogued',
  sanskrit_name: null,
  english_name: null,
  description: 'Not yet catalogued',
  source_ref: 'asset_registry:bg_uncatalogued',
})])
expect(candidate.catalogue_sha256).toBe(canonicalLabelCatalogueDigest(candidate.labels))
```

- [ ] **Step 2: Run the focused candidate test and verify it fails**

Run: `cd platform && npx vitest run src/lib/nirmana-elevation/__tests__/monitor.test.ts`

Expected: the old all-null candidate fails the exact placeholder assertion.

- [ ] **Step 3: Write the failing acceptance integration test**

Add a `definitions.test.ts` case that supplies a live registry row with `sanskrit_name`, `english_name`, and `english_description` all `null`, derives its candidate, submits both exact candidate digests to `acceptNirmanaBaselineCandidate`, and asserts `created` plus an `INSERT INTO nirmana_elevation_asset_labels` call containing `Not yet catalogued`.

- [ ] **Step 4: Implement the smallest deterministic rendering rule**

In `buildNirmanaBaselineCandidate`, compute source values first. Only when all three are `null`, set `description` to the exact string `Not yet catalogued`; retain `sanskrit_name` and `english_name` as `null`, keep empty legacy aliases, and retain `source_ref: asset_registry:<asset_id>`. Do not change the manifest, classification status, or acceptance transaction.

- [ ] **Step 5: Run focused tests and type checking**

Run:

```bash
cd platform && npx vitest run src/lib/nirmana-elevation/__tests__/monitor.test.ts src/lib/nirmana-elevation/__tests__/definitions.test.ts src/lib/nirmana-elevation/__tests__/labels.test.ts
npx tsc --noEmit
```

Expected: all tests pass and TypeScript exits 0.

- [ ] **Step 6: Commit**

```bash
git add platform/src/lib/nirmana-elevation/monitor.ts \
  platform/src/lib/nirmana-elevation/__tests__/monitor.test.ts \
  platform/src/lib/nirmana-elevation/__tests__/definitions.test.ts \
  docs/superpowers/plans/2026-08-26-ntap-label-acceptance-release-fix.md
git commit -m "fix(nirmana): render missing baseline labels safely"
```

### Task 2: Re-establish release readiness after the upstream migration repair

**Files:**
- Modify if required by rebase conflicts only: files changed by Task 1.
- Verify: `.github/workflows/ci.yml`, `platform/migrations/629_nirmana_elevation_monitor_observations.sql`, `infra/scheduler/main.tf`, `docs/runbooks/ntap-tracker-monitor.md`.

**Interfaces:**
- Consumes: the post-PR-1561 `origin/main` deployment revision and migration ledger state.
- Produces: a protected NTAP PR based on repaired main, with hosted CI and deploy evidence before live configuration.

- [ ] **Step 1: Wait for and verify PR #1561’s protected merge and deployment**

Read the PR, required checks, deploy workflow, migration ledger, and serving Cloud Run revision. Confirm migration 628 was applied once with the expected hash and that web/MCP deploy jobs ran. Stop on a failed required check or a disagreement between main, migration ledger, and serving revision.

- [ ] **Step 2: Rebase the NTAP branch onto repaired `origin/main`**

Run `git fetch origin` then `git rebase origin/main`. Resolve only genuine conflicts using the Task 1 semantics. Re-run `git diff --check origin/main...HEAD`.

- [ ] **Step 3: Re-run branch evidence**

Run focused NTAP monitor, definitions, labels, snapshot, route, component, and migration-contract tests; TypeScript; targeted ESLint; `actionlint`; Terraform formatting/validation; governance gate; and diff check. Record any inherited portal-wide lint baseline separately rather than hiding it.

- [ ] **Step 4: Obtain independent review and open the protected PR**

The PR must state that migration 629 and scheduler IaC are additive, that no campaign progress is initialized, and that scheduler secret configuration occurs only through approved secret-aware operations after deploy. Use the required merge queue; do not bypass protections.

- [ ] **Step 5: Verify the live operational chain**

After protected deployment, check that unauthenticated monitor POST changes from `404` to `401`, apply reviewed scheduler/IAM, wait for three scheduled append-only observations, accept the same-observation pair of digests only if the authoritative status is `baseline_missing`, then prove the dashboard remains unknown for progress until typed evidence arrives.

### Task 3: Make the observed baseline acceptance request constructible

**Files:**
- Modify: `platform/src/lib/nirmana-elevation/types.ts:292-300`
- Modify: `platform/src/lib/nirmana-elevation/snapshot.ts:50-60,132-136,187-222,1169-1176`
- Modify: `platform/src/components/nirmana-elevation/AuditDrawer.tsx:106-123`
- Modify: `docs/runbooks/ntap-tracker-monitor.md:20-45`
- Modify: `platform/src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts`
- Modify: `platform/src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts`

**Interfaces:**
- Consumes: latest append-only `nirmana_elevation_monitor_observations.id` selected for `program_sync`.
- Produces: authenticated snapshot `program_sync.source_observation_id: UUID | null` and Audit Drawer display of that exact ID; the `accept_baseline_candidate` command submits it unchanged.

- [x] **Step 1: Write the failing snapshot-to-command contract test**

Seed a fresh `baseline_missing` monitor row with a UUID. Assert the authenticated snapshot validates and exposes `program_sync.source_observation_id`, and that the documented command payload accepts this exact field. Assert unavailable/no-observation projections expose `null`, never a fabricated ID.

- [x] **Step 2: Run the focused snapshot/evidence route tests and verify failure**

Run:

```bash
cd platform && ./node_modules/.bin/vitest run \
  src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts \
  src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts
```

Expected: the new snapshot assertion fails because `source_observation_id` is absent.

- [x] **Step 3: Carry the exact observation identity through the read-only projection**

Add nullable UUID validation to `ProgramSyncSchema`, select the monitor row's existing `id`, copy it only when the monitor source remains available, and include it in the snapshot generation digest. Do not expose it in the execution canvas; display it in the authenticated Audit Drawer with the same copy boundary as the two candidate digests.

- [x] **Step 4: Update the governed operator procedure**

Require the operator to copy `source_observation_id` together with both candidate digests from one fresh, `baseline_missing` Audit Drawer observation and include the exact UUID in the `accept_baseline_candidate` payload. Preserve the prohibition on scheduler-endpoint bypass or hand-derived substitutes.

- [x] **Step 5: Run focused tests and type/lint checks**

Run the focused route tests plus the NTAP snapshot/component suite, `npx tsc --noEmit`, and targeted ESLint for touched files. Confirm `git diff --check` exits 0.

- [x] **Step 6: Commit**

```bash
git add platform/src/lib/nirmana-elevation/types.ts \
  platform/src/lib/nirmana-elevation/snapshot.ts \
  platform/src/components/nirmana-elevation/AuditDrawer.tsx \
  docs/runbooks/ntap-tracker-monitor.md \
  platform/src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts \
  platform/src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts \
  docs/superpowers/plans/2026-08-26-ntap-label-acceptance-release-fix.md
git commit -m "fix(nirmana): expose baseline observation provenance"
```
