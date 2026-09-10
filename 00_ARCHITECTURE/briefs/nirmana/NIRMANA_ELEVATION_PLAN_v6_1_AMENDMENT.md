---
artifact: NIRMANA_ELEVATION_PLAN_v6_1_AMENDMENT.md
canonical_id: NIRMANA_ELEVATION_PLAN_v6_1_AMENDMENT
version: "1.0"
status: NATIVE-AUTHORIZED
campaign_id: nirmana-elevation
produced_on: 2026-09-01
authorized_by: native (Abhisek Mohanty), 2026-09-01
basis: NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md §4, executive summary of the accepted amendments.
---

# Nirmāṇa Elevation Plan — v6.1 Amendment

Amends `NIRMANA_ELEVATION_PLAN_v6_0.md` in place. Full authority + rationale live in
`NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md §4`; this is the pointer-scale summary.

1. **§N.8 scoping.** Earned-Signal Principle applies at full force to terminal boundaries
   (capsules, integrity checks, freezes) and product data. Campaign-internal operational
   machinery earns readiness through live rehearsal, not pre-modeled readiness ontologies.
2. **Delivery ≠ certification.** Merged/deployed/executed work may exist as
   `delivered-but-uncertified` when certification is briefly unavailable, provided the evidence
   for later certification is immutable (SHAs, run ids, digests).
3. **One terminal capsule per asset generation** — a single new event type
   (`asset_terminal_accepted`) on the existing append-only `nirmana_evidence` ingress. No new
   evidence tables.
4. **Two planes.** Mutable operational state (queue, lease, active, blockers, retries, cost)
   lives outside `nirmana_evidence`, in enum-validated `nirmana_ops` tables.
5. **Release predicates.** Analysis-safe: immutable commit exists. Execution-safe: serving
   production commit contains (git ancestry) the required merged commit/migrations.
   Closure-safe: exact `main == production`, required only at batch/layer/campaign close.
6. **Rebuild policy.** Invalidation-driven; L0 default is `rebuild_only` (cheap reference
   assets); `verified_reuse` reserved for measurably expensive assets. Re-evaluate per layer.
7. **Finding fence.** Every discovery gets exactly one disposition from a fixed vocabulary
   (`BLOCKS_CURRENT_ASSET` … `NO_ACTION_JUSTIFIED`); only the first four may interrupt flow.
8. **Supersession is routine** — an ordinary, server-validated, evidence-logged executor action.
9. **Governance budget** — ≤15% of active effort on control-plane/governance work,
   self-measured at every microbatch boundary.
10. **Layer scope** — strict current-layer-only; layer N+1 opens only when layer N is frozen.

## Changelog
- 1.0 (2026-09-01): Initial amendment, landing the native-authorized §4 decisions from the
  velocity-reset independent review.
