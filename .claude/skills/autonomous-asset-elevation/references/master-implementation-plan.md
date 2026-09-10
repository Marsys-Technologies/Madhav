# Master Implementation Plan

Use this plan for one bounded layer or asset portfolio at a time. Later layers may be inventoried, but they do not enter implementation until the current layer freezes.

## 1. North Star and operating equation

The programme optimizes one outcome:

`accepted throughput = assets reaching an accepted terminal disposition per unit time`

The authoritative headline is:

`accepted_or_frozen_assets / frozen_layer_denominator`

Everything else—agent count, commits, pull requests, tests, reviews, build minutes, documents and token usage—is diagnostic or supporting evidence. Never optimize these proxies at the expense of accepted throughput or quality.

Track two kinds of speed separately:

- **Flow efficiency:** waiting, queueing, review, CI, deploy and blocker time.
- **Build efficiency:** the time and resources required to produce the asset when it genuinely must run.

## 2. Campaign contract

Before dispatch, record:

- layer or portfolio in scope and explicit exclusions;
- authoritative asset source and denominator-freeze method;
- accepted lifecycle and terminal dispositions;
- production, repository, tracker and evidence authorities;
- deployment and rollback mechanism;
- shared-write, database and infrastructure limits;
- surrogate decision charter;
- completion definition and recovery entrypoint.

Do not predesign later layers. Capture only cross-layer interfaces and downstream consumers needed to judge the current layer.

## 3. Truth and denominator freeze

Reconcile, without mutation:

1. Registry/catalogue identities, layer assignment, status and version.
2. Writers, seeds, migrations, services and runtime tables.
3. Orchestrator plan, hashes, dependencies and build-state projection.
4. Current code, open branches/PRs, worktrees and protected `main`.
5. Production revision, database state, natural monitor observations and UI surfaces.
6. Last lifecycle event per asset and any independent verdict.

Resolve duplicates, aliases, missing writers, source-only rows, dormant assets, probes, retired assets and unregistered implementations. Freeze a versioned definition only when every member is classified. If the definition must change later, use an explicit supersession event; never silently edit the denominator.

## 4. DAG truth audit

Treat the existing DAG as a hypothesis. For every declared or suspected edge, classify it as:

- hard build dependency;
- runtime data dependency;
- semantic/canonicalization dependency;
- validation-only dependency;
- optional enrichment dependency;
- false, stale or missing edge.

Prove edges using the strongest proportionate evidence available: imports and function calls, SQL reads/writes, foreign keys and fact references, service calls, build receipts, runtime traces, and controlled perturbation/removal tests. Record the consumed output or contract, not merely the upstream asset name.

Use two passes so the audit does not become a new pre-implementation campaign:

1. **Frontier pass:** prove the graph is cycle-free and establish the first safe hard-dependency frontier.
2. **Asset pass:** complete the deep edge, consumer and semantic audit immediately before each asset becomes implementation-eligible.

All edge questions must close before layer freeze, but safe root implementation need not wait for a speculative deep audit of every distant leaf.

Reject cycles or turn them into an explicit staged fixed-point design. Compute the transitive closure, critical path, fan-out and independent topological frontier. All hard edges of an asset must be proven before its production rebuild; behavioural perturbation is reserved for disputed, high-impact or current-frontier edges. An upstream asset freezes before a downstream production rebuild consumes it.

## 5. Asset portfolio triage

Create one Asset Elevation Record per denominator member using [asset-elevation-contract.md](asset-elevation-contract.md). Assign one disposition target:

- optimize implementation;
- enrich data or correct semantics;
- expand downstream adoption;
- consolidate duplication;
- split or merge asset boundaries;
- justified no-change;
- retain with intentional limited use;
- retire, supersede, source-only or probe-only.

Prioritize by critical-path value, not convenience:

1. correctness or security defects that invalidate the layer;
2. blockers on the longest DAG path;
3. assets with the greatest downstream unlock count or fan-out;
4. high build-time or failure-cost assets;
5. broad canonicalization and reuse opportunities;
6. remaining short independent assets.

### Cross-layer adoption boundary

Elevating an upstream layer includes proving that its canonical contract is useful downstream, but it does not open later-layer rebuild or freeze work.

- Read-only downstream tracing is always permitted for the current layer's value and DAG audit.
- Runtime/serving adapters needed to consume the current layer may be implemented and released as current-layer integration work when they do not claim later-layer elevation.
- Downstream writer changes may be prepared when required for compatibility, but their accepted production rebuild and freeze wait for their own layer unless current serving correctness would otherwise be broken.
- A current-layer asset may freeze with remaining future-layer adoption obligations only when it has at least one real consumption proof or an explicit source/reference purpose, and every remaining obligation is attached to a named downstream asset. Do not claim full utilization while those obligations remain.

## 6. Per-asset analysis and decision

Perform domain, DAG, data-model and correctness analysis with a frontier model at high reasoning effort. Cover:

- unique purpose and correct layer placement;
- actual consumers and unused capability;
- duplicated downstream constants, rules, calculations, names or citations;
- astrological/astronomical correctness and legitimate tradition variants;
- missing data, relations, provenance, uncertainty and product capability;
- current code path, algorithm, queries, external calls and failure modes;
- measured build/runtime baseline and hotspot classification;
- AI retrieval/narration readiness and UI expression;
- change blast radius, migration, compatibility and rollback;
- minimal acceptance proof.

The Native Surrogate selects the disposition and acceptance plan before implementation. Prefer the smallest change that realizes the material value. Do not optimize an asset with no measured hotspot or enrich it with data that has no identified consumer or research value.

Read-only asset analysis may fan out across the whole current layer once the denominator is frozen. Code/data mutation, integration and accepted rebuild remain constrained to the proven DAG-ready frontier.

## 7. Work packet design

Split an asset only into independently finishable work packets. Each packet contains:

- owned files, tables and interfaces;
- exact base commit and isolated worktree/branch;
- dependencies and expected upstream hashes;
- implementation objective and non-goals;
- focused tests and output-quality proof;
- migration/deploy/rebuild implications;
- completion evidence and handoff format.

Avoid two agents editing the same files or shared schema concurrently. Serialize migrations, registry changes, integration and production writes even when analysis and code changes run in parallel.

## 8. Elastic swarm and scheduling

Keep a small standing control plane and spawn specialists only when work becomes ready. Use [autonomous-swarm-runtime.md](autonomous-swarm-runtime.md) for roles and routing.

The scheduler continuously:

1. reads durable state and the accepted DAG;
2. computes the current ready frontier;
3. subtracts claimed work and shared-write conflicts;
4. prioritizes critical-path unlocks;
5. spawns the required analyst, implementer or verifier;
6. reserves integration, CI, database and production capacity;
7. advances completed packets or records exact blockers;
8. repeats after every event and heartbeat.

There is no arbitrary agent-count cap. Effective concurrency is bounded by proven independence and the slowest integration resource. Excess writers that create merge, CI or verification queues reduce velocity and must not be spawned.

Use a finish-before-start discipline: when integration or certification queues grow, allocate agents to finish those queues instead of starting more assets.

First complete any repository-mandated definition and foundation gates. Then prove the complete conveyor on the first suitable root asset before expanding further machinery work: isolated change, independent review, protected merge, deployment, accepted production rebuild, live verification and tracker freeze. Repair orchestrator, hash, tracker or release infrastructure only when a mandatory foundation contract or the asset conveyor demonstrates that it is required for trustworthy asset completion.

## 9. Implementation and quality protection

For each asset:

1. Capture pre-change output, build and product baselines.
2. Implement one coherent change in its isolated worktree.
3. Run focused correctness, boundary, lineage, contract and performance tests.
4. Prove output identity for pure optimization, using deterministic/sorted digests or declared numerical tolerances.
5. For intentional output changes, prove the corrected semantics, provenance, expected-delta contract, migration and downstream compatibility; do not mislabel them as optimization.
6. Re-measure the same workload and record the delta.
7. Obtain independent adversarial verification from raw artifacts and live operands, not the implementer's summary.

Prefer set-based or batched data flow, incremental/content-addressed builds, stable partitioning, reuse of canonical upstream assets, resumable substeps, idempotency, deterministic transforms and honest null/uncertainty. Optimize the algorithm before micro-optimizing code.

## 10. Integration and release flow

Integrate through the repository's protected path:

1. Refresh from protected `main` and confirm worktree ownership.
2. Reconcile overlapping changes and current upstream asset hashes.
3. Run changed-surface checks plus mandatory protected gates.
4. Perform one independent code/data review proportional to blast radius.
5. Commit, push and open or update the canonical pull request.
6. Merge in topological order or a compatible DAG-wave micro-batch.
7. Confirm the exact merged tree and required migrations.
8. Deploy through the normal release mechanism.
9. Prove the serving revision and production database state.

Batch compatible assets in a wave when it removes redundant CI and deployment cycles. Do not hold a critical-path asset for an unrelated slow item merely to make the batch larger.

Treat unrelated repository-wide lint, historical secret-scan noise or adjacent hygiene as separate backlog unless it blocks a mandatory gate or the changed surface. Never bypass a real protected failure.

If an unrelated failure is nevertheless mandatory for protected integration, open one narrow gate-unblocker lane, verify it independently, close it, and return immediately to the asset critical path. Do not convert it into a repository-wide cleanup programme.

## 11. Rebuild-once discipline

After the optimized or corrected upstream chain is merged and deployed, rebuild each current-layer asset once in production for campaign acceptance. Development, rehearsal and test builds do not count as the accepted production rebuild.

- Use the smallest real rehearsal partition before a destructive or expensive full build.
- Verify snapshot/rollback readiness where data can be lost.
- Record input definition and upstream content hashes.
- Resume committed substeps rather than restart them.
- Do not rebuild unchanged upstream assets for every downstream asset.
- If output is unchanged, retain the equality receipt and avoid invalidating downstream consumers.
- If output changes, mark only the proven transitive downstream closure stale.

Retired, merged, source-only and probe assets receive their applicable terminal evidence instead of a fictitious rebuild.

## 12. Independent acceptance and freeze

An asset freezes only when the verifier independently establishes all applicable criteria from the Asset Elevation Record, including:

- correct identity, layer and disposition;
- proven dependency and consumer contracts;
- correctness, coverage, provenance and uncertainty;
- implementation and data opportunity resolved or justified no-change;
- focused tests and output identity/correctness proof;
- merged protected tree, deployed revision and production state;
- one accepted production rebuild where applicable;
- integrity, freshness, downstream availability and UI/AI wiring;
- tracker event with raw evidence references.

The Native Surrogate adjudicates disagreements from evidence and signs the freeze. It may send the asset back with named gaps; it cannot convert unknown evidence into a pass.

## 13. Layer close

Do not open the next layer until:

- denominator membership and definition digest are frozen;
- every member has an accepted terminal disposition;
- no in-layer hard DAG edge or consumer contract is unresolved;
- current-layer outputs are available to downstream consumers;
- all applicable assets have one accepted post-elevation rebuild;
- a clean full-layer verification passes;
- tracker, protected `main`, production and database state reconcile;
- open worktrees and branches are either owned and active or safely cleaned;
- residuals are explicit, non-blocking and do not contradict layer completion.

The layer close should be a short derived report, not a new research campaign.

## 14. Anti-waste controls

- Pre-register the minimum proof required before implementation.
- Use one independent verifier pass, adding angles only for high-blast-radius or contradictory evidence.
- Stop profiling when the measured bottleneck is outside the asset.
- Stop optimization at the asset's plausible floor or when value is immaterial.
- Do not repeat a stocktake whose authorities and hashes have not changed.
- Do not create a second tracker or ledger when an accepted one can be extended.
- Do not count meetings, reports, agents, token use or green CI as asset progress.
- Convert every discovered issue into the owning asset/layer or a clearly separate backlog; do not let a global hygiene queue swallow the critical path.

## 15. Learning and reuse

At asset and layer close, capture only reusable discoveries:

- corrected dependency pattern;
- recurring optimization technique;
- missing acceptance detector;
- consumer/adoption pattern;
- release or recovery improvement.

Change the reusable skill only when evidence shows a systematic rule. Do not encode every one-off incident into permanent governance.
