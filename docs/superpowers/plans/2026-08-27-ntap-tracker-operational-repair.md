# NTAP Tracker Operational Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the live NTAP tracker so it is usable, explicit about its data state, presents assets in the approved plan vocabulary, and supplies the guarded UI and operations path to establish a current baseline without fabricating execution progress.

**Architecture:** Keep the existing immutable definitions/evidence/monitor model. Correct the snapshot-to-UI contract so missing campaign evidence cannot read as zero progress; add a guarded super-admin baseline-acceptance panel built on the existing acceptance endpoint; refactor the tracker cards/spine for human-facing plan identity and accessible asset lifecycle progress. Provisioning remains a protected-main operational task after code release.

**Tech Stack:** Next.js, TypeScript, React Testing Library, Vitest, PostgreSQL/Cloud Scheduler operational runbook.

**Spec:** `docs/superpowers/specs/2026-08-27-ntap-tracker-operational-repair-design.md`

## Global constraints

- Never import historical ledger data or create synthetic campaign/stage/asset receipts.
- Do not weaken cron authentication, print/read its secret, or place it in Terraform/source control.
- Preserve L0–L5 sequential execution and only show DAG peers in parallel.
- A baseline may be accepted only from the exact fresh `baseline_missing` observation and must not advance stages or start work.
- Keep all dashboard data super-admin protected and preserve audit evidence.

### Task 1: Correct truth-state language and plan-facing asset presentation

**Files:**
- Modify: `platform/src/components/nirmana-elevation/CampaignSnapshotStrip.tsx`
- Modify: `platform/src/components/nirmana-elevation/CampaignSpine.tsx`
- Modify: `platform/src/components/nirmana-elevation/AssetCard.tsx`
- Modify: `platform/src/components/nirmana-elevation/MilestoneBar.tsx`
- Modify: `platform/src/components/nirmana-elevation/LayerStage.tsx`
- Modify: `platform/src/components/nirmana-elevation/WaveLane.tsx`
- Modify: `platform/src/components/nirmana-elevation/NowNextRail.tsx`
- Modify: `platform/src/components/nirmana-elevation/vocab.ts`
- Modify: `platform/src/components/nirmana-elevation/CampaignSpine.test.tsx`
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx`
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.a11y.test.tsx`
- Modify: `platform/src/components/nirmana-elevation/LayerStage.test.tsx`
- Create: `platform/src/components/nirmana-elevation/AssetCard.test.tsx`

**Interfaces:** consume the existing `NirmanaElevationSnapshot`; preserve raw IDs as secondary metadata; emit an accessible asset completion `progressbar` and never show a numeric overall denominator unless both the frozen definition and accepted spine establish it.

- [ ] Write failing component tests for: no `0 / 128` denominator while the spine is unknown; human display labels for T0/F0; an asset with missing human metadata yields one compact availability statement; and each asset exposes an `aria-label`led progress bar.
- [ ] Run `cd platform && npx vitest run src/components/nirmana-elevation/CampaignSpine.test.tsx src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx src/components/nirmana-elevation/AssetCard.test.tsx`; verify the new tests fail.
- [ ] Implement the smallest presentation-only repair. Keep execution values unchanged. Make the neutral baseline inventory reachable when no stage is earned, surface one action/blocker line without disclosure, collapse completed/locked waves, use no more than two asset columns, and use the selected label catalogue where available. Registry-backed metadata must remain clearly provisional source context; never invent Sanskrit or asset numbers.
- [ ] Re-run the focused tests and commit `fix(nirmana): make tracker progress and asset identity truthful`.

### Task 2: Add a guarded baseline-acceptance control

**Files:**
- Create: `platform/src/components/nirmana-elevation/BaselineAcceptancePanel.tsx`
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.tsx`
- Modify: `platform/src/lib/nirmana-elevation/types.ts` only if the endpoint response needs a parsed command contract
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx`
- Create: `platform/src/components/nirmana-elevation/BaselineAcceptancePanel.test.tsx`

**Interfaces:** the existing authenticated `POST /api/admin/nirmana-elevation/evidence` acceptance command is the only mutation boundary. The panel accepts only exact candidate + catalogue digests from a fresh `program_sync.status === 'baseline_missing'` observation. Its safe retry identity is the exact source-observation UUID plus deterministic definition revision already guarded by the server; the strict endpoint intentionally does not accept a client idempotency key. No control renders as actionable for stale/unavailable/plan-adaptation state.

- [ ] Write failing UI tests proving that the panel appears only for a fresh baseline-missing snapshot, shows candidate scope without raw secrets, disables/withholds action otherwise, and posts the exact source-observation UUID, deterministic revision, and digest pair only after an explicit local confirmation.
- [ ] Run `cd platform && npx vitest run src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx src/components/nirmana-elevation/BaselineAcceptancePanel.test.tsx`; verify the new tests fail.
- [ ] Implement the panel with an explicit browser confirmation, disabled-in-flight state, no-store request, success refresh, and safe conflict/error copy. Reuse the existing API validation rather than duplicating acceptance logic.
- [ ] Re-run focused tests plus `src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts`; commit `feat(nirmana): surface guarded baseline acceptance`.

### Task 3: Review, verify, and release the application change

**Files:** no additional production source files unless review finds a defect in Tasks 1–2.

- [ ] Run the Nirmana targeted type/lint/test commands defined by `run-checks`, then the focused tracker suites. Capture commands and results in the SDD ledger.
- [ ] Request a fresh code review against the task requirements. Resolve only review findings within scope and re-run affected tests.
- [ ] Create a PR with the provided description skill, require protected CI, and merge only through the protected queue after green checks. Verify the deployed revision and tracker route after Cloud Run completes.

### Task 4: Restore the scheduled observation and establish current program identity

**Files:** no source edit expected; follow `docs/runbooks/ntap-tracker-monitor.md` and `infra/scheduler/README.md`.

- [ ] Before any operational action, close the recorded PR #1573 review findings: prove monitor state ownership with remote plans, enforce protected-main/environment-gated applies and module serialization, apply the exact reviewed saved plan, and replace the retired cron-secret-header runbook with OIDC-only verification. Treat this as a required source/CI repair, not a documentation waiver.
- [ ] Dispatch the protected-main isolated monitor Terraform **plan**, inspect that it targets only `amjis-nirmana-elevation-monitor` and its dedicated IAM resources, and record the result in the ledger.
- [ ] Dispatch the matching protected-main Terraform **apply** only when that saved plan is clean. Do not use a local Terraform apply.
- [ ] Verify the Scheduler job has the fixed OIDC audience and dedicated service-account identity. Do not configure or transmit a custom cron secret header; the approved route is OIDC-only.
- [ ] Wait for a naturally scheduled fresh observation (never invoke it manually). Verify public monitor access still returns `401` and the authenticated tracker shows a current baseline proposal.
- [ ] Use the guarded UI to accept the exact current baseline only after it is displayed as fresh and `baseline_missing`. Confirm the resulting snapshot has an accepted definition/label catalogue and still labels unevidenced execution as unknown/not yet evidenced.
- [ ] Verify at least two subsequent scheduler observations, automatic browser refresh, current release alignment, and no stale/unknown state caused by missing observations. Record objective evidence in the ledger.
