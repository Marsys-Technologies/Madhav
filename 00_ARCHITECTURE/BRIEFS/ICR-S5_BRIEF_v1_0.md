---
session_id: ICR-S5
stream: icr
audit_section: "§N.6 ICR-S5"
spec_artifact: 00_ARCHITECTURE/CAPABILITY_COVERAGE_AND_PERFORMANCE_AUDIT_v1_0.md
spec_version: "1.2"
status: IN_PROGRESS
attempt_count: 1
authored_at: "2026-05-21T10:15:00Z"
---

# ICR-S5 Brief — Confirmation UI + Atomic Apply

## Goal

Build the native confirmation workflow for ICR propose-patch artifacts. Deliver:

1. **API layer** — POST `/api/icr/confirm` (confirm/reject/escalate) and GET `/api/icr/patches`
2. **Atomic-apply with rollback** — two-step transaction (write MSR correction → move YAML) with full rollback on any mid-apply failure
3. **UI stub** — `ConflictPanel.tsx` minimal stub rendering "Conflict (N pending)" heading + placeholder for PERF-S5 full panel
4. **Tests** — atomic-apply rollback test + confirmation_ui_smoke mount test

## may_touch

```
platform/src/app/api/icr/**
platform/src/components/performance/ConflictPanel.tsx
platform/src/components/performance/PerformanceClient.tsx
platform/tests/icr/**
00_ARCHITECTURE/BRIEFS/ICR-S5_BRIEF_v1_0.md
```

## must_not_touch

```
00_ARCHITECTURE/CONFLICT_PATCHES/PROPOSED/**       # never auto-apply in this session
00_ARCHITECTURE/CONFLICT_PATCHES/RESOLVED/**
00_ARCHITECTURE/CONFLICT_PATCHES/REJECTED/**
00_ARCHITECTURE/CONFLICT_PATCHES/L1_REVIEW/**
platform/src/lib/icr/types.ts                       # stable types from ICR-S1
platform/src/lib/icr/detector.ts                    # ICR-S3 detector — no changes
platform/src/lib/icr/propose_patch.ts               # ICR-S4 emitter — no changes
025_HOLISTIC_SYNTHESIS/MSR_v3_0.md                  # never touched in ICR-S5; only by confirm action at runtime
```

## Files to create

### 1. `platform/src/app/api/icr/patches/route.ts`

GET handler returning `{ proposed: string[], resolved: string[], rejected: string[] }` — lists YAML filenames from each subdirectory of `00_ARCHITECTURE/CONFLICT_PATCHES/`.

### 2. `platform/src/app/api/icr/confirm/route.ts`

POST handler accepting `{ patch_file: string, action: 'confirm' | 'reject' | 'escalate', reason?: string }`.

**Path traversal prevention:** validate `patch_file` is a basename only (no `/`, no `..`), resolve final path as `PROPOSED/<patch_file>`, verify it starts with the expected PROPOSED dir before any FS operation.

**`confirm` action (atomic):**
1. Read YAML from `PROPOSED/<patch_file>`
2. Locate the MSR signal file: `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md`
3. Read MSR content; find line(s) matching `before:` value from the YAML
4. Write the corrected MSR content (replace `before` text with `after` text)
5. Move YAML from `PROPOSED/` → `RESOLVED/<patch_file>` (rename)
6. If step 4 fails: skip step 5 (MSR unchanged, YAML stays in PROPOSED)
7. If step 5 fails: restore original MSR content from backup taken at step 3, return 500

**`reject` action:** append `reject_reason: <reason>` to YAML, move to `REJECTED/<patch_file>`.

**`escalate` action:** move to `L1_REVIEW/<patch_file>`, write a stub DISAGREEMENT_REGISTER entry (append to `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` under the new dispute ID).

All subdirectory paths (`RESOLVED/`, `REJECTED/`, `L1_REVIEW/`) must be created with `mkdir -p` if missing before write.

### 3. `platform/src/components/performance/ConflictPanel.tsx`

Minimal stub component:
- Accepts prop `proposedCount: number`
- Renders a card heading: "Conflict Resolution (N pending)"
- Body: "Full conflict panel ships in PERF-S5. {N} patch(es) awaiting native review."
- If proposedCount === 0: "No pending conflicts."
- Mount as a section in PerformanceClient below the existing KPI tiles

### 4. `platform/src/components/performance/PerformanceClient.tsx` (modify)

Add `ConflictPanel` section below the existing four KPI tiles / existing sections. Fetch proposed count from `/api/icr/patches` on client side. Pass `proposedCount` to `ConflictPanel`.

### 5. `platform/tests/icr/atomic_apply.test.ts`

Vitest integration test with two cases:

**Case 1 — happy path:** Call confirm handler with synthetic PROPOSED/ artifact; assert YAML moved to RESOLVED/, MSR content updated.

**Case 2 — mid-apply failure (rollback test):** Mock `fs.rename` to throw after the MSR write step. Assert: YAML remains in PROPOSED/ (not in RESOLVED/), MSR file content is unchanged (rollback succeeded). This is the `atomic_apply_dry_run` gate.

**Case 3 — path traversal rejection:** Call POST with `patch_file: "../../../etc/passwd"` and assert 400 response.

**Case 4 — confirmation_ui_smoke:** Mount `ConflictPanel` with `proposedCount={1}` and assert renders without throwing; text "1 patch" appears. Mount with `proposedCount={0}` and assert "No pending conflicts" renders.

## Acceptance criteria

1. `tsc --noEmit` exits 0 (no new type errors)
2. `vitest run tests/icr/` — all tests pass including:
   - `atomic_apply_dry_run`: mid-apply failure leaves PROPOSED/ and MSR unchanged
   - `confirmation_ui_smoke`: ConflictPanel renders with both pending and empty states
   - path traversal test: 400 returned
3. API route validates `patch_file` is within `PROPOSED/` (path traversal prevention)
4. ConflictPanel stub mounts in PerformanceClient without errors

## Gates (local verification before PR)

```
npx tsc --noEmit --skipLibCheck 2>&1 | grep -v "tests/" | grep -v "plan_escalation" | head -20
npx vitest run platform/tests/icr/ --reporter=verbose
```

## Hard constraints

- `auto_apply: false` — the `confirm` action is the ONLY place that touches MSR_v3_0.md at runtime, and only when explicitly called by native via the API. This session does NOT call confirm itself.
- Do NOT move or delete any file in `PROPOSED/` in this session. The YAML at `DIS.013_MSR.377_proposed.yaml` stays in PROPOSED/ until the native confirms via the panel.
- The API route must reject any `patch_file` path that attempts directory traversal.
