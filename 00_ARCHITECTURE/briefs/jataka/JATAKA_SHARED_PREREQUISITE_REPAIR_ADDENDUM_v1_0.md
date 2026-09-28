---
artifact: JATAKA_SHARED_PREREQUISITE_REPAIR_ADDENDUM_v1_0.md
version: 1.0
status: ACTIVE
decision: CCD-020
session: JATAKA-SHARED-PREREQUISITE-REPAIR-20260928
branch: codex/jataka-bg-transit-repair
worktree: /Users/Dev/.codex/worktrees/jataka-shared-asset-repair/Madhav
parent: JATAKA_CHART_WORKSPACE_CONTROLLED_PRODUCTION_ROLLOUT_ADDENDUM_v1_0.md
purpose: >
  Govern the narrow production repair of the shared prerequisites that blocked the disposable
  Jataka chart's atomic correction, followed by only the previously blocked live acceptance.
---

# Jātaka Shared-Prerequisite Repair Addendum

## 1. Corrected starting evidence

The prior rollout correctly stopped before chart mutation, but its immediate-cause narrative was
overstated. Read-only production evidence now proves:

- `bg_transit_rules.id=133` is a valid, cited `double_transit` Jupiter rule referenced by three
  `gochara_resonance_map` rows and must be preserved;
- `bg_transit_rules` completed governed builds on 2026-09-04 under the newer scoped reconciliation
  writer, after the 2026-08-02 FK error still recorded on the covered `bg_transit_engine` identity;
- the correction planner did not execute a transit writer or attempt a delete: it refused during
  prerequisite freshness preflight;
- the disposable chart remains unchanged at birth time `12:34`, with zero build runs;
- current preflight inputs expose four out-of-plan shared prerequisites requiring resolution:
  `bg_transit_rules` and `bg_vedha_malefic_scale` are `lit` but registry-invalidated `stale`;
  `bg_panchanga` and `ka_muhurta_seva` are healthy services whose probe/self-test evidence cannot
  earn relational-output freshness (`bg_panchanga` is probe-only; `ka_muhurta_seva` has a
  WriterBase self-test but intentionally produces no domain rows).

The session must reproduce the exact planner blockers from live inputs and may narrow this set, but
must not broaden it without stopping and obtaining new authority.

## 2. Authorized implementation envelope

The source repair is limited to the planner/readiness metadata and focused tests needed to let a
currently healthy service prerequisite satisfy preflight from one of two exact earned evidence
shapes: a fresh legacy probe, or a successful WriterBase service self-test. Neither path may invent
a relational output receipt. Data prerequisites remain receipt-gated and must still be fresh.

The production sequence, only after review and deployment, is:

1. create a fresh recoverable Cloud SQL backup and record the rollback target;
2. run explicit governed service probes only for the proven blocking service identities;
3. run explicit governed rebuilds only for the proven blocking data identities;
4. verify service health, throughput, receipts/freshness, row counts, citations and rule IDs;
5. rerun exactly one birth-time correction on the disposable chart;
6. verify the same UUID, one build run, historical-conversation context behavior, final readiness,
   D1 rendering and production isolation.

No migration is anticipated. If a schema change becomes necessary, stop and request a separately
reserved migration and amended authority.

## 3. Hard prohibitions

- no direct SQL patch or manual freshness-state edit;
- no delete, remap or ID churn of `bg_transit_rules.id=133`;
- no broad Brahmagyan/L0 rebuild;
- no existing important chart or conversation mutation;
- no secret, Firebase, IAM, network, topology or database-role change;
- no frozen Python orchestrator-contract/control-flow change;
- no claim that deployment or Task 9 is complete without exact live receipts.

## 4. Rollback and stop conditions

Stop before chart correction if any bounded probe/rebuild selects an unexpected asset, changes a
referenced transit-rule identity/citation, changes a protected chart, produces non-baseline row
counts, leaves a prerequisite unready, or exposes a new dependency blocker. Roll back application
code to the last healthy revision through the protected path. Use the fresh backup only under a
separately reviewed recovery action; never destructively improvise against production data.

## 5. Close requirements

Record exact commits, PR/review/check results, backup ID, deployment run and revision, each bounded
shared operation/run ID, before/after shared-asset evidence, synthetic chart run and context receipts,
cross-chart isolation, residuals and lease release. Keep the parent rollout's partial result intact;
this addendum records only the follow-up.
