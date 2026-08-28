# Madhav / Nirmana Profile

Read this profile whenever the skill operates in the Madhav repository. It contains routing and durable invariants, never live counts or status.

## Governing sources

Read and obey the current versions required by `CLAUDE.md`, then route specifically to:

- `00_ARCHITECTURE/briefs/nirmana/AUTONOMOUS_ASSET_ELEVATION_MASTER_PLAN_v1_0.md` for the durable project adoption record for this skill.
- `00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v6_0.md` for the frozen campaign scope, state machine, T0/F0 gates and per-asset terminal contract.
- `00_ARCHITECTURE/NIRMANA_ELEVATION_CONTEXT_PACK_v6_0.md` for the compact takeover packet; revalidate all time-sensitive observations.
- `00_ARCHITECTURE/autonomy/CHARTER_v2_0.md` for delegated authority, role separation and hard prohibitions.
- `00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` for the frozen writer-facing contract.
- `00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` and `BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md` for proven role, deployment, canary and rollback patterns.
- `00_ARCHITECTURE/WORKTREE_ISOLATION_PROTOCOL_v1_0.md` for worktree ownership and cleanup.
- The accepted Nirmana database definition/event projection, current protected Git, production runtime/database and authenticated tracker observations for live truth.

Precedence is: fresh live database/release/tracker evidence and accepted definition/events; the frozen v6 plan and charter; then historical ledgers and narratives as evidence only. Do not use an old campaign snapshot or historical `lit` state as current task truth.

## Durable build invariants

- External layers are Brahmagyan, Ganita, Bodha, Kala, Phala and Mimamsa; internal IDs use `bg_`, `ga_`, `bo_`, `ka_`, `ph_` and `mi_` prefixes.
- Elevation proceeds sequentially from L0 through L5. Within the open layer, parallelize only the validated DAG frontier.
- Shared/global substrate assets and chart-specific assets have different domains. The planner and lock discipline must prevent concurrent writes to the same shared surface.
- Preserve the frozen `WriterBase` contract: registered writers, orchestrator-owned transactions and build state, no writer commit/close of `ctx.db_conn`, and resumable substeps for heavy assets.
- L0 shared assets use their governed upsert/idempotency rules; chart-specific layers rebuild by chart and natural key according to current repository standards.
- A row being present or `asset_throughput.state='lit'` is not campaign acceptance. Require witnessed execution, exact detectors, independent verdict and production proof.
- Floors are descriptive/aspirational, never row-generation targets. Verification tiers use canonical vocabulary and only real detectors earn promoted tiers.
- Facts, derivations, interpretations and narration stay separate. Downstream layers reference canonical upstream facts rather than re-deriving them locally.
- Every serving status, narration claim and completion signal must have a detector capable of returning false.

For Jyotish assets, the generic domain-context fields include ayanamsa, zodiac, house system, ephemeris, time zone, coordinates, tradition/school, chart type and version wherever applicable. Preserve classical-source variants and applicability rather than collapsing them into false consensus. Distinguish astronomical facts, deterministic chart derivations, classical rules, interpretive candidates and AI narration.

## Nirmana lifecycle adapter

For Nirmana, use the accepted current campaign definition and label catalogue as the denominator authority. Definition changes require a guarded supersession tied to the observed candidate. Tracker progress is derived from accepted lifecycle events and production/release reconciliation; historical `lit` counts are operational context only.

The mandatory state order is:

`BOOTSTRAP -> T0_CENSUS -> PLAN_FROZEN -> DENOMINATOR_FROZEN -> F0_FOUNDATION -> L0 -> L1 -> L2 -> L3 -> L4 -> L5 -> CLOSING -> COMPLETE`

T0 performs no asset rebuild. F0 must be deployed and independently accepted before any L0 accepted rebuild. Its partition canary proves machinery only and never earns asset acceptance. Complete these repository-mandated foundation gates before using the generic first-root conveyor proof.

Every manifest member remains explicit. Registry membership changes use an auditable lifecycle/disposition transition rather than silent row deletion. A `producer_covered` asset inherits the accepted producer receipt and must not rebuild a second time.

Before an accepted rebuild:

1. confirm the layer definition and DAG version;
2. confirm all hard upstream assets are frozen and deployed;
3. confirm F0 is accepted and the asset's final code/data change is on the serving production revision;
4. run the accepted production rebuild once through the witnessed orchestrator path;
5. obtain independent runtime, data, consumer and UI proof;
6. append the accepted freeze event and confirm the tracker projection.

The accepted execution/receipt must be bound to the current definition digest, serving code SHA, upstream hashes, lease fence and run generation. A result from an older definition, deployment or fence cannot self-promote after it eventually finishes.

## Isolation and release adapter

- The shared checkout is read-only for campaign mutation. Use a fresh dedicated worktree per writer, verifier, integration or release lane.
- Claim ownership before editing shared files or ledgers; use fences/leases where the current campaign defines them.
- Merge through protected GitHub workflows. Green candidate CI is not a merge, deployment or acceptance receipt.
- Verify migrations actually applied, the serving revision matches the accepted protected tree, production data reflects the rebuild and the tracker observes the same state naturally.
- Clean worktrees only after proving they are clean, merged, unowned and no longer evidence-bearing.

## Proportionality rule

Run focused asset/change-surface evidence plus mandatory protected checks. Do not let unrelated historical secret-scan findings, broad lint debt, old governance discrepancies or repeated certification of unchanged PASS items enter the active queue unless they invalidate the current asset or protected release path.
