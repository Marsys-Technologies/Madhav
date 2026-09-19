---
artifact: MADHAV_PURNA_ANVESANA_MIGRATION_BARRIER_DECISION
version: 1.0.0
status: ADOPTED_FOR_TECHNICAL_DELIVERY
decided_at: 2026-09-20T01:17:53+05:30
scope: protected deployment sequencing after migrations 1040 and 1041
---

# Migration barrier decision

## Decision

Retain the existing fail-closed migration barrier. A protected deployment may promote traffic only
after its exact SHA has passed protected state inspection, strict data-plane isolation, routine
migration replay, ownership postflight, and the relevant zero-traffic candidate checks. The
terminal earned-outcome gate must continue to require every source-implied mutation to succeed.

This is not a global migration/deploy decoupling decision. No migration, ownership, isolation,
candidate canary, or terminal-outcome check was skipped to obtain the release.

## Evidence and rationale

The barrier caught two distinct production-relevant defects before any unearned release:

- The former generic no-op migration identity for 1041 collided with an existing applied identity.
  The forward source correction gave 1041 its unique `SELECT 1041` identity; current production
  contains exactly one 1041 ledger row.
- After the owner-USAGE repair, predecessor run `35461533371` detected canonical public-schema ACL
  drift. The required `purna_inquiry_owner` USAGE capability was present in the live least-privilege
  posture but absent from the global allowlist. PR #2690 corrected the canonical contract without
  granting CREATE or recreating bootstrap authority.

The repaired path passed at protected `main@66b962f2994f0a7500c285025740cd5861534d8c`: automatic
run `35463402314` and force-all run `35464335676` completed successfully. The latter required
successful migration, web, MCP, sidecar, and pipeline mutations before its earned outcome could
pass. Read-only post-release attestation found migrations 1040 and 1041 exactly once; absent
`purna_inquiry_bootstrap`; and marked data-plane, Nirmāṇa, and Pūrṇa ownership state.

## Operating rule

On a future failure, stop the affected deployment at that gate, preserve its candidate/no-traffic
state, and diagnose the exact source or state discrepancy. Do not use automatic retry, a force
flag, or a staged traffic promotion to cross the barrier. A new deployment attempt requires a
fresh exact-SHA state read and an active operation-specific lease.

## Narrow exception standard

A future proposal may sequence one specifically named compatible migration differently only when a
separate reviewed packet supplies all of the following:

1. An exact compatibility manifest naming the migration, affected consumers, precondition,
   postcondition, and retained safety gates.
2. Forward and rollback contracts that are idempotent and tested against the same supported
   database topology.
3. A bounded consumer-impact analysis and an exact-environment candidate proof.
4. An explicit protected-release decision. Absence of one item retains this barrier unchanged.

This decision records technical delivery discipline only. It neither changes the product-acceptance
denominator nor treats deployment, health, or migration evidence as the successor's unrun 5+30
three-door automated acceptance or human-expert empirical research.
