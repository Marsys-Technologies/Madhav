# NTAP Tracker Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/admin/nirmana-elevation` the reliable, single operational dashboard for the NTAP program by registering a verifiable plan baseline and continuously surfacing synchronization, drift, and plan-adaptation state.

**Architecture:** Add an append-only monitor-observation seam and a deterministic registry candidate builder. A scheduler-authenticated endpoint observes but never accepts work; the snapshot joins the latest observation to existing execution/evidence truth. The UI presents program synchronization and plan adaptation in the executive strip while retaining the approved campaign spine.

**Tech Stack:** Next.js/TypeScript, PostgreSQL migrations, Cloud Run, Cloud Scheduler Terraform, Vitest, React Testing Library.

**Spec:** `docs/superpowers/specs/2026-08-26-ntap-tracker-reliability-design.md`

## Global Constraints

- Preserve the exact state machine: `BOOTSTRAP → T0_CENSUS → PLAN_FROZEN → DENOMINATOR_FROZEN → F0_FOUNDATION → L0 → L1 → L2 → L3 → L4 → L5 → CLOSING → COMPLETE`.
- Use historical JSON/JSONL only as evidence; never initialize current progress, stage position, or completion from it.
- The monitor may observe and record observations; it must not freeze, supersede, advance stages, accept evidence, dispatch builds, or mutate build tables.
- Baseline and plan-adaptation acceptance remain explicit super-admin, audited, idempotent, and transactionally guarded operations.
- Do not alter the frozen chart-build orchestrator or the L0–L5 execution order/DAG rules.
- Unknown, unavailable, stale, quiet, and blocked are distinct visible states; no manual percentages or stale-green rendering.
- Keep `/api/admin/nirmana-elevation/*` super-admin protected; scheduler endpoints require the existing `MARSYS_CRON_SECRET` convention.
- Cloud Scheduler IaC is authored and tested but is applied only from protected `main`, not from this worktree.

---

### Task 1: Deterministic NTAP baseline and divergence classifier

**Files:**
- Create: `platform/src/lib/nirmana-elevation/monitor.ts`
- Create: `platform/src/lib/nirmana-elevation/__tests__/monitor.test.ts`
- Modify: `platform/src/lib/nirmana-elevation/definitions.ts`

**Interfaces:**
- Consumes: `NirmanaRegistryContractRow`, `NirmanaElevationManifest`, `canonicalManifestDigest`, and the existing registry contract/identity assertions.
- Produces: `buildNirmanaBaselineCandidate(rows): { manifest; manifest_sha256; labels; catalogue_sha256; registry_identity_sha256; registry_contract_sha256 }` and `classifyNirmanaDivergence(input): NirmanaMonitorStatus`.

- [ ] **Step 1: Write failing candidate-builder tests**

```ts
expect(buildNirmanaBaselineCandidate(rows).manifest.assets).toHaveLength(rows.length)
expect(buildNirmanaBaselineCandidate(rows).manifest_sha256).toMatch(/^[a-f0-9]{64}$/)
expect(buildNirmanaBaselineCandidate(rows).labels).toEqual(expect.arrayContaining([
  expect.objectContaining({ asset_id: 'bg_reference', english_name: 'Reference data' }),
]))
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `cd platform && npx vitest run src/lib/nirmana-elevation/__tests__/monitor.test.ts`

Expected: FAIL because the monitor module does not exist.

- [ ] **Step 3: Implement deterministic candidate construction**

```ts
export function buildNirmanaBaselineCandidate(rows: NirmanaRegistryContractRow[]): NirmanaBaselineCandidate {
  const manifest = { chart_id: CANONICAL_NIRMANA_CHART_ID, assets: rows.map(toManifestAsset) }
  const parsed = NirmanaElevationManifestSchema.parse(manifest)
  assertFreezableManifest(parsed)
  return { manifest: parsed, manifest_sha256: canonicalManifestDigest(parsed), /* digests */ }
}
```

Map only authoritative registry fields. Derive wave indices deterministically from the DAG. Use registry Sanskrit/English/description values when present; emit `null` for absent human labels and never synthesize translations.

- [ ] **Step 4: Add divergence-classification tests and implementation**

```ts
expect(classifyNirmanaDivergence({ definition: null, candidate, observation: null }).status).toBe('baseline_missing')
expect(classifyNirmanaDivergence({ definition: frozenDefinition, candidate: changedDag, observation }).status).toBe('plan_adaptation_required')
expect(classifyNirmanaDivergence({ definition: frozenDefinition, candidate: changedContract, observation }).status).toBe('evidence_refresh_required')
```

Compare identity (asset IDs/layers/dependencies) independently from mutable registry contract digests. Keep affected asset IDs sorted.

- [ ] **Step 5: Run focused tests and commit**

Run: `cd platform && npx vitest run src/lib/nirmana-elevation/__tests__/monitor.test.ts src/lib/nirmana-elevation/__tests__/definitions.test.ts`

Commit: `feat(nirmana): derive NTAP baseline and divergence state`

### Task 2: Append-only monitor observations and scheduler endpoint

**Files:**
- Create: `platform/migrations/628_nirmana_elevation_monitor_observations.sql`
- Create: `platform/src/app/api/admin/internal/nirmana-elevation-monitor/route.ts`
- Create: `platform/src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/route.test.ts`
- Modify: `platform/src/lib/nirmana-elevation/monitor.ts`

**Interfaces:**
- Consumes: Task 1 candidate and divergence classifier plus `loadNirmanaReleaseStatus`.
- Produces: `runNirmanaElevationMonitor(): Promise<NirmanaMonitorObservation>` and an append-only monitor table.

- [ ] **Step 1: Write failing route and persistence tests**

```ts
expect(await POST(unauthenticatedRequest())).toHaveProperty('status', 401)
expect(await POST(authenticatedRequest())).toHaveProperty('status', 200)
expect(insertSql).toContain('INSERT INTO nirmana_elevation_monitor_observations')
expect(insertSql).not.toContain('nirmana_elevation_campaign_definitions')
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `cd platform && npx vitest run src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/route.test.ts`

Expected: FAIL because the monitor endpoint does not exist.

- [ ] **Step 3: Add the surgical append-only migration**

Create `nirmana_elevation_monitor_observations` with a UUID primary key, `observed_at`, `status`, sorted `affected_asset_ids`, all required digest columns, bounded public detail, and `source_error_code`. Add a latest-observation index and an UPDATE/DELETE-rejecting trigger. Do not alter campaign definition/event tables.

- [ ] **Step 4: Implement monitor execution and scheduler authentication**

```ts
if (!validateCronSecret(request)) return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
const observation = await runNirmanaElevationMonitor()
return NextResponse.json({ ok: true, observation_id: observation.id, status: observation.status }, { headers: { 'Cache-Control': 'no-store' } })
```

Use the established `X-Marsys-Cron-Secret` or Bearer fallback. The monitor reads registry/current definition/labels/runtime/release, records an observation, and on failure records only a safe source-unavailable result when the database remains writable. It does not call evidence/definition writes.

- [ ] **Step 5: Run focused tests and commit**

Run: `cd platform && npx vitest run src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/route.test.ts src/lib/nirmana-elevation/__tests__/monitor.test.ts`

Commit: `feat(nirmana): record scheduler monitor observations`

### Task 3: Controlled baseline proposal and explicit acceptance

**Files:**
- Modify: `platform/src/app/api/admin/nirmana-elevation/evidence/route.ts`
- Modify: `platform/src/lib/nirmana-elevation/definitions.ts`
- Modify: `platform/src/lib/nirmana-elevation/labels.ts`
- Modify: `platform/src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/definitions.test.ts`

**Interfaces:**
- Consumes: Task 1 candidate builder and existing evidence route.
- Produces: `accept_baseline_candidate` command that freezes only the exact current candidate and creates its catalogue atomically.

- [ ] **Step 1: Write failing acceptance tests**

```ts
const response = await POST(request({ command: 'accept_baseline_candidate', definition_revision: 'ntap-v1', expected_candidate_sha256: candidate.manifest_sha256 }))
expect(response.status).toBe(201)
expect(transactionSql).toEqual(expect.arrayContaining([
  expect.stringContaining('INSERT INTO nirmana_elevation_campaign_definitions'),
  expect.stringContaining("SET definition_status = 'frozen'"),
  expect.stringContaining('INSERT INTO nirmana_elevation_asset_labels'),
]))
expect(transactionSql.join('\n')).not.toContain('stage_transition_accepted')
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `cd platform && npx vitest run src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts src/lib/nirmana-elevation/__tests__/definitions.test.ts`

Expected: FAIL because `accept_baseline_candidate` is not a recognized command.

- [ ] **Step 3: Implement a single serializable acceptance transaction**

```ts
export async function acceptNirmanaBaselineCandidate(input: AcceptBaselineInput) {
  // lock campaign, re-read registry, rebuild candidate, compare exact expected digest
  // insert reconciling definition, freeze it, insert labels and catalogue receipt, commit
}
```

Reuse existing manifest and label validations. Require an exact candidate manifest digest and candidate label digest from the caller. Record only a catalogue acceptance receipt and audit log; do not append stage or lifecycle receipts. Return `created` or exact `idempotent`, otherwise conflict.

- [ ] **Step 4: Add race, stale-candidate, and idempotency tests**

```ts
expect(await acceptNirmanaBaselineCandidate(staleInput)).rejects.toThrow('candidate changed')
expect(await acceptNirmanaBaselineCandidate(exactRetry)).resolves.toBe('idempotent')
```

- [ ] **Step 5: Run focused tests and commit**

Run: `cd platform && npx vitest run src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts src/lib/nirmana-elevation/__tests__/definitions.test.ts src/lib/nirmana-elevation/__tests__/labels.test.ts`

Commit: `feat(nirmana): add controlled NTAP baseline acceptance`

### Task 4: Snapshot provenance, freshness, and adaptation contract

**Files:**
- Modify: `platform/src/lib/nirmana-elevation/types.ts`
- Modify: `platform/src/lib/nirmana-elevation/snapshot.ts`
- Modify: `platform/src/app/api/admin/nirmana-elevation/snapshot/route.ts`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/snapshot.test.ts`
- Modify: `platform/src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts`

**Interfaces:**
- Consumes: latest Task 2 observation.
- Produces: `snapshot.program_sync` with `status`, `observed_at`, `age_seconds`, `affected_asset_ids`, `current_definition_sha256`, and `candidate_definition_sha256`.

- [ ] **Step 1: Write failing snapshot contract tests**

```ts
expect(snapshot.program_sync.status).toBe('plan_adaptation_required')
expect(snapshot.sources.find((source) => source.source_id === 'program_monitor')?.state).toBe('stale')
expect(snapshot.data_quality.gaps).toContain('Plan adaptation is required before the program denominator can change.')
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `cd platform && npx vitest run src/lib/nirmana-elevation/__tests__/snapshot.test.ts src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts`

Expected: FAIL because the snapshot has no `program_sync` field or monitor source.

- [ ] **Step 3: Load and project the latest observation**

Add monitor rows to raw sources. Mark the monitor `fresh` through five minutes plus ten-minute grace, `stale` after that, `unknown` before any observation, and `unavailable` when its latest record reports a source failure. Separate `quiet` execution from synchronization freshness.

- [ ] **Step 4: Preserve existing evidence semantics**

Do not convert baseline acceptance into stage movement. A frozen definition without stage receipts retains `current_stage: null`, but reports `program_sync.status: in_sync` and a frozen denominator. Add explicit tests for this distinction.

- [ ] **Step 5: Run focused tests and commit**

Run: `cd platform && npx vitest run src/lib/nirmana-elevation/__tests__/snapshot.test.ts src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts`

Commit: `feat(nirmana): expose NTAP synchronization in snapshots`

### Task 5: One-dashboard operational UX

**Files:**
- Modify: `platform/src/components/nirmana-elevation/CampaignSnapshotStrip.tsx`
- Modify: `platform/src/components/nirmana-elevation/NowNextRail.tsx`
- Modify: `platform/src/components/nirmana-elevation/AuditDrawer.tsx`
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx`
- Modify: `platform/src/components/nirmana-elevation/CampaignSpine.test.tsx`

**Interfaces:**
- Consumes: Task 4 `program_sync` contract.
- Produces: clear baseline, quiet, stale, source failure, evidence-refresh, and plan-adaptation notices without altering campaign-spine layout.

- [ ] **Step 1: Write failing visible-state tests**

```tsx
render(<NirmanaElevationTrackerView snapshot={planAdaptationSnapshot} fetchedAt={new Date()} />)
expect(screen.getByText('Plan adaptation required')).toBeInTheDocument()
expect(screen.getByText(/affected assets/i)).toBeInTheDocument()
expect(screen.getByText('L0 · Brahmagyan')).toBeInTheDocument()
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `cd platform && npx vitest run src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx src/components/nirmana-elevation/CampaignSpine.test.tsx`

Expected: FAIL because program synchronization is not rendered.

- [ ] **Step 3: Implement executive synchronization language**

Add a fifth metric or compact notice titled `Program synchronization`. Render exact status-specific language:

```tsx
const copy = {
  baseline_missing: 'Baseline awaiting acceptance',
  plan_adaptation_required: 'Plan adaptation required',
  evidence_refresh_required: 'Evidence refresh required',
  label_refresh_required: 'Label catalogue refresh required',
  in_sync: 'In sync',
  source_unavailable: 'Source unavailable',
}
```

Show the observation age and affected asset count. Keep hashes, source references, and observation history in `AuditDrawer`, not the primary canvas.

- [ ] **Step 4: Verify accessibility and no-stale-green behavior**

Ensure stale/degraded notices use `role="alert"` or `role="status"` appropriately, text does not depend on color, and a quiet in-sync program does not render an error. Preserve expand/collapse behavior for stages, layers, waves, and assets.

- [ ] **Step 5: Run focused tests and commit**

Run: `cd platform && npx vitest run src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx src/components/nirmana-elevation/CampaignSpine.test.tsx src/components/nirmana-elevation/NirmanaElevationTracker.a11y.test.tsx`

Commit: `feat(nirmana): show NTAP synchronization on dashboard`

### Task 6: Scheduler IaC, deployment verification, and operator evidence

**Files:**
- Modify: `infra/scheduler/main.tf`
- Modify: `infra/scheduler/README.md`
- Create: `platform/src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/scheduler-contract.test.ts`
- Create: `docs/runbooks/ntap-tracker-monitor.md`

**Interfaces:**
- Consumes: Task 2 endpoint and existing scheduler service account.
- Produces: `amjis-nirmana-elevation-monitor` running every five minutes, plus a runbook for baseline acceptance and plan-adaptation review.

- [ ] **Step 1: Write failing scheduler-contract tests**

```ts
expect(terraform).toContain('resource "google_cloud_scheduler_job" "nirmana_elevation_monitor"')
expect(terraform).toContain('schedule         = "*/5 * * * *"')
expect(terraform).toContain('/api/admin/internal/nirmana-elevation-monitor')
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `cd platform && npx vitest run src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/scheduler-contract.test.ts`

Expected: FAIL because the scheduler resource does not exist.

- [ ] **Step 3: Add the least-privilege scheduler resource and documentation**

Use the existing `scheduler_invoker_sa`, OIDC audience, and secret-header convention. Configure five-minute cadence, two retries, bounded deadline, and the production URL variable. Document that Terraform apply runs only from protected `main`; do not apply it in this task.

- [ ] **Step 4: Add a precise operational runbook**

Document how an authorized super-admin retrieves the candidate from the authenticated dashboard/API, accepts only its exact digest, reviews `plan_adaptation_required`, adopts a new definition via explicit supersession, and verifies observation freshness. Explicitly prohibit direct SQL, historical-ledger import, and manual progress edits.

- [ ] **Step 5: Run relevant checks and commit**

Run: `cd platform && npx vitest run src/app/api/admin/internal/nirmana-elevation-monitor/__tests__/scheduler-contract.test.ts && npx tsc --noEmit`

Commit: `feat(nirmana): schedule NTAP tracker monitoring`

### Task 7: Authorized candidate-detail completion

**Files:**
- Modify: `platform/src/lib/nirmana-elevation/types.ts`
- Modify: `platform/src/lib/nirmana-elevation/snapshot.ts`
- Modify: `platform/src/components/nirmana-elevation/AuditDrawer.tsx`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/snapshot.test.ts`
- Modify: `platform/src/components/nirmana-elevation/CampaignSpine.test.tsx`

**Interfaces:**
- Consumes: Task 2 persisted `candidate_catalogue_sha256` and Task 3 `accept_baseline_candidate` exact two-digest contract.
- Produces: authenticated `program_sync.candidate_catalogue_sha256` alongside `candidate_definition_sha256`, available in the Audit Drawer only.

- [ ] **Step 1: Write failing snapshot and audit-detail tests**

```ts
expect(snapshot.program_sync.candidate_catalogue_sha256).toMatch(/^[a-f0-9]{64}$/)
expect(screen.getByText(`Candidate label catalogue: ${candidateDigest}`)).toBeInTheDocument()
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `cd platform && npx vitest run src/lib/nirmana-elevation/__tests__/snapshot.test.ts src/components/nirmana-elevation/CampaignSpine.test.tsx`

Expected: FAIL because the candidate catalogue digest is not in the public V2 contract.

- [ ] **Step 3: Project the persisted candidate catalogue digest read-only**

Add nullable `candidate_catalogue_sha256` to `program_sync`. Select and schema-validate it from the latest monitor row. Include it in the deterministic generation hash. Do not recompute, accept, write, or infer any candidate on the snapshot path.

- [ ] **Step 4: Render only in Audit Drawer**

```tsx
<p>Candidate label catalogue: {snapshot.program_sync.candidate_catalogue_sha256 ?? 'Not available'}</p>
```

Do not put either digest in the executive canvas. This value is super-admin-only because the full snapshot is super-admin-only.

- [ ] **Step 5: Run focused checks and commit**

Run: `cd platform && npx vitest run src/lib/nirmana-elevation/__tests__/snapshot.test.ts src/components/nirmana-elevation/CampaignSpine.test.tsx && npx tsc --noEmit && npx eslint src/lib/nirmana-elevation/types.ts src/lib/nirmana-elevation/snapshot.ts src/components/nirmana-elevation/AuditDrawer.tsx`

Commit: `fix(nirmana): expose authorized baseline candidate digests`

### Task 8: Integrated verification and branch review

**Files:**
- Modify: `platform/src/lib/nirmana-elevation/__tests__/fixture-v2.ts`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/types-v2.test.ts`
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.a11y.test.tsx`

**Interfaces:**
- Consumes: all preceding contracts.
- Produces: cross-layer fixtures that prove baseline, observation, divergence, and dashboard behavior together.

- [ ] **Step 1: Add an integrated plan-adaptation fixture**

```ts
export const planAdaptationSnapshot = makeSnapshot({
  program_sync: { status: 'plan_adaptation_required', affected_asset_ids: ['ga_positions'] },
})
```

- [ ] **Step 2: Add regression tests for forbidden transitions**

```ts
expect(snapshot.campaign.current_stage).toBeNull()
expect(snapshot.progress.denominator_status).toBe('frozen')
expect(snapshot.program_sync.status).toBe('in_sync')
```

This proves identity initialization does not manufacture campaign stage progress.

- [ ] **Step 3: Run the complete tracker suite**

Run: `cd platform && npx vitest run src/lib/nirmana-elevation/__tests__ src/app/api/admin/nirmana-elevation src/app/api/admin/internal/nirmana-elevation-monitor src/components/nirmana-elevation`

Expected: PASS.

- [ ] **Step 4: Run TypeScript, targeted lint, and governance checks**

Run: `cd platform && npx tsc --noEmit && npx eslint src/lib/nirmana-elevation src/app/api/admin/nirmana-elevation src/app/api/admin/internal/nirmana-elevation-monitor src/components/nirmana-elevation && python3 scripts/governance/check_earned_signal.py`

Expected: PASS. Do not expand this scope into pre-existing portal-wide lint debt.

- [ ] **Step 5: Commit and prepare independent review**

Commit: `test(nirmana): prove NTAP tracker synchronization behavior`

## Plan self-review

- Spec coverage: Tasks 1–3 provide baseline identity, controlled acceptance, and non-mutating monitor behavior; Tasks 4–5 expose freshness/adaptation in the snapshot and dashboard; Task 6 provides scheduler and operation boundary; Task 7 proves the no-fabrication and UX constraints end to end.
- Placeholder scan: no deferred-placeholder steps; each test and implementation step has concrete files, commands, and expected behavior.
- Interface consistency: Task 1 provides candidate/classifier, Task 2 writes observations, Task 3 uses candidate acceptance, Task 4 projects observations, Tasks 5–7 consume the V2 contract.
