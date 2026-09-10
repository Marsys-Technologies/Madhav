---
name: autonomous-asset-elevation
description: Plan, execute, resume, or audit a velocity-first autonomous campaign that elevates assets layer by layer with DAG-safe parallelism, independent verification, isolated worktrees, and production closure. Use for multi-asset or multi-layer implementation programmes; do not use for a single ordinary bug fix.
metadata:
  version: "1.0.0"
---

# Autonomous Asset Elevation

Run an asset or layer campaign to accepted production completion. Optimize for the number of assets that reach the accepted terminal state, not for commits, agents, tests, reports, or apparent activity.

## Select the operating mode

- **Stocktake:** reconcile the authoritative denominator, current lifecycle state, DAG, code, data, consumers, runtime, UI, Git and production evidence. Read [asset-elevation-contract.md](references/asset-elevation-contract.md).
- **Plan:** produce an implementation-ready layer plan, ready queue and acceptance contract. Read [master-implementation-plan.md](references/master-implementation-plan.md), [asset-elevation-contract.md](references/asset-elevation-contract.md), [autonomous-swarm-runtime.md](references/autonomous-swarm-runtime.md), and use [runtime-schemas.md](references/runtime-schemas.md) when creating the durable control packets.
- **Execute or resume:** run the plan autonomously, recover durable state first, and continue until the scoped layer is frozen or genuinely impossible to complete. Read all execution references, including [autonomous-swarm-runtime.md](references/autonomous-swarm-runtime.md) and [runtime-schemas.md](references/runtime-schemas.md).
- **Audit:** compare claims with current code, data, accepted evidence and live production. Do not mutate unless the user also authorized implementation.

When operating in Madhav, also read [madhav-profile.md](references/madhav-profile.md).

## Non-negotiable outcome

Define an asset as complete only when it has reached the campaign's accepted terminal lifecycle. Unless the repository defines a stricter lifecycle, use:

`RECONCILED -> ELIGIBLE -> ANALYZED -> OPTIMIZED or JUSTIFIED_NO_CHANGE -> INTEGRATED -> DEPLOYED -> REBUILT_ONCE -> INDEPENDENTLY_VERIFIED -> FROZEN`

A retired, merged, source-only or service-probe asset needs an explicit terminal disposition and applicable proof instead of a fabricated rebuild.

The primary progress measure is `accepted_or_frozen_assets / frozen_denominator` for the open layer. Layers are sequential. Parallelize only assets or work packets that the validated DAG and shared-write boundaries prove independent.

## Essential execution rules

1. Reconcile live truth before planning or resuming. Do not trust a stale summary, historical green state, branch name, PR, test run, or tracker percentage as completion proof.
2. Freeze the current layer's denominator and validate its DAG before production rebuilds. Audit declared edges against real code reads, SQL lineage, runtime calls and controlled perturbation where safe.
3. For every asset, assess purpose, epistemic type, correctness, missing data, implementation efficiency, downstream adoption, duplication, AI readiness, product/UI expression, provenance, reliability and operating cost.
4. Preserve the product's epistemic boundaries: distinguish source facts, deterministic derivations, domain rules, interpretive/model output and user-facing narration; preserve legitimate variants and all required calculation context. Apply the Jyotish-specific form in the Madhav profile.
5. Profile before optimizing. Protect quality with pre/post output identity or an explicitly adjudicated correctness change. No measured hotspot means no optimization work.
6. Use isolated worktrees and explicit file ownership for concurrent writers. Use an independent clean context for certification. Do not use the shared checkout as a parallel build surface when repository policy forbids it.
7. Keep routine decisions autonomous. A Native Surrogate decides charter-scoped ambiguity from evidence and precedent; builders never certify themselves. Do not invent authority for irreversible or out-of-scope acts—quarantine that lane and continue every independent eligible lane.
8. Keep the fleet active through useful work, not busywork. Waiting CI, builds or deployment are monitoring states, not campaign-wide blockers. Never cross into a later layer merely to avoid idleness.
9. Integrate in DAG-safe micro-batches when that reduces CI/deploy overhead without delaying the critical path. Merge through the repository's protected path, deploy, prove production, then rebuild and freeze.
10. Apply verification proportionally to the claim and blast radius. Run focused changed-surface checks plus one independent acceptance pass. Do not widen into unrelated repository hygiene unless it blocks the asset or a mandatory protected gate.

## Repository adaptation

At campaign open, read the repository's agent instructions, current-state authority, build/orchestrator contract, worktree policy, tracker schema and release process. Reuse existing ledgers and trackers instead of building a second control plane. Record any necessary repository-specific adapter in the campaign plan; do not copy mutable project state into this skill.

## Completion behavior

Continue autonomously while safe eligible work exists. Completion requires every denominator member to have an accepted terminal disposition, the layer gate to pass independently, main and production to be reconciled according to repository policy, the tracker to reflect live truth, and temporary worktrees/branches to be cleaned only after their evidence is durable.

If no safe eligible work exists, state the exact unresolved external condition and preserve resumable state. Never manufacture progress or weaken a gate to avoid an honest wait.
