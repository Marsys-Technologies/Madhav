---
artifact: NIRMANA_ELEVATION_CONTEXT_PACK_v6_0.md
version: "6.0"
status: CURRENT
campaign_id: nirmana-elevation
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
produced_on: 2026-08-25
---

# Nirmāṇa Elevation v6 — Context Pack

## North Star

For the canonical chart and its shared substrate, establish one evidence-backed denominator and DAG; make the orchestrator, invalidation, cockpit, and tracker truthful; then execute and independently verify each eligible asset in strict L0→L5 wave order.

## Verified starting state

- Integration branch/worktree: `codex/nirmana-elevation-v6` at `872df060152a3e0adb9433df9f8e297af9f00ff8`.
- Production: Cloud Run `amjis-web-01702-gbn`, Ready and serving the same commit SHA; observed 2026-08-25.
- Tracker release: PR #1522 merged at `362429bb29806ff8dd76fb80bf2ba01b532235c5`; its migration 592 is present in source but not yet live-verified.
- No Nirmāṇa process, active Cloud Run build job, or open Nirmāṇa PR is evidenced at takeover.
- The historical `campaign/nirmana-autonomous` state ends at stale R0 Stage-1 intake / a five-asset conform proposal. It is evidence only: it does not supply current task states, a denominator, accepted rebuilds, or a layer freeze.

## Sources and invariants

Primary truth is the live registry/build tables, deployed SHA/revision, the frozen campaign definition, and immutable evidence receipts. The old ledger is consulted only last-record-per-ID. A `lit` row, CI result, narrative seal, or tracker display alone is not completion.

The campaign may touch the canonical chart and shared substrate only. It must not touch unrelated campaigns, credentials, applied migrations, protected controls, or `main` directly. It must use isolated worktrees, explicit-path commits, immutable migrations, and independently verified deployment/rebuild evidence.

## Current F0 findings

The tracker currently lacks chart/run scoping for throughput and run-asset state, has no release-SHA provenance bridge, exposes no controlled definition/event writer, and cannot express the full T0 manifest contract. Until corrected, it must show unknown/degraded rather than a fabricated denominator or progress percentage.

The T0 production census requires read-only access to `asset_registry`, `asset_throughput`, `build_runs`, `build_run_assets`, `build_substep_progress`, `_migrations_applied`, and the two campaign-evidence tables. No local DB URL is configured. Existing configured Google Cloud identity may be used for read-only release and Cloud SQL discovery, but credentials must never be printed, copied, or recovered.

## Execution interface

ADHIKĀRIN records material rulings in the v6 plan amendment log before execution. PRAHARĪ reconciles the goal, agents, queue, Git/PR/CI, Cloud Run, build jobs, tracker freshness, and blockers every ten minutes. KĀRAKA and PARĪKṢAKA have disjoint change/certification ownership.

## Acceptance commands

Focused tracker tests are run from `platform` with Vitest for definitions, snapshot API, and tracker UI. Planner tests and the named orchestrator test set are required for F0 changes. Production verification uses only an explicit read-only SQL transaction and exact Cloud Run revision inspection; `migrate.ts --dry-run` is prohibited as a read-only probe because it can execute DDL.
