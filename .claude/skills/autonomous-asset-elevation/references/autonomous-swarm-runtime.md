# Autonomous Swarm Runtime

This runtime keeps implementation moving without turning autonomy into uncontrolled concurrency or governance theatre.

## 0. Activation contract

A skill supplies execution doctrine; it does not keep a task alive by itself. Autonomous execution must activate:

- a persistent goal containing the exact layer objective and completion conditions;
- a heartbeat or automation that wakes the conductor after silence and after legitimate waits;
- durable event state and a deterministic recovery entrypoint;
- a monitor that checks both campaign work and the conductor task, not merely an HTTP endpoint;
- explicit authority for repository, GitHub, deployment and production actions in scope.

Do not claim unattended continuity until these mechanisms have fired successfully and the conductor has recovered from durable state once.

## 1. Runtime shape

Maintain three standing control roles:

1. **Conductor** — owns durable campaign state, computes the DAG-ready frontier, assigns work, protects layer order and drives closure.
2. **Native Surrogate** — resolves ambiguity, selects dispositions, adjudicates disagreements and authorizes charter-scoped actions from evidence and precedent.
3. **Monitor** — detects silence, stale leases, waiting CI/deploy/builds, dead agents and unclaimed eligible work; wakes or replaces the correct owner.

Spawn other roles elastically per work packet:

- Asset Architect / Jyotish-Data Analyst.
- Implementer.
- Data or Migration Specialist.
- Performance Specialist.
- Independent Verifier.
- Security Reviewer when the changed surface warrants it.
- Release Integrator.
- Tracker/Scribe.

Do not keep expensive specialists alive without eligible work. Resource availability means immediate on-demand spawning, not idle agents or speculative tasks.

## 2. Model and reasoning routing

Choose the lowest-cost model and effort that can reliably decide the claim. Current examples may be adapted to platform availability:

| Work | Recommended routing |
|---|---|
| Native Surrogate; contested DAG, domain semantics, correctness or irreversible blast-radius reasoning | Frontier model such as GPT-5.6 Sol, `xhigh`; use `max` only for unresolved high-impact contradictions |
| Per-asset architectural, astrological, data-gap and optimization analysis | GPT-5.6 Sol, at least `high` |
| Cross-cutting algorithm or orchestrator implementation | GPT-5.6 Sol `high`, or equivalent frontier coding model |
| Normal asset implementation and integration | GPT-5.6 Terra `medium/high`; raise to Sol when reasoning complexity warrants it |
| Mechanical inventory, deterministic scans, tracker projection, heartbeat and polling | GPT-5.6 Luna `low/medium` |
| Independent verification | Terra `high` for ordinary assets; Sol `high/xhigh` for global, high-fan-out, epistemically sensitive or contradictory assets |
| Security or migration review | Use the specialized reviewer role with `high` effort; `xhigh` for high-blast-radius production changes |

Do not run every role at maximum effort. Escalate based on ambiguity, epistemic risk, data-loss risk, fan-out and reversibility.

## 3. Durable state and ownership

Use one accepted control plane. At minimum it must provide:

- frozen campaign/layer definition and version;
- asset lifecycle event stream;
- last event per asset;
- DAG and current ready frontier;
- work packet owner, lease/fence, branch and worktree;
- decisions, independent verdicts and blockers;
- CI, merge, deploy, rebuild and production receipts;
- liveness/heartbeat observations;
- main/production/tracker reconciliation.

Prefer append-only schema-validated events with monotonic sequence numbers and derive snapshots. A stale snapshot never overrides newer events. Every mutating task has one live owner and a fence; expired ownership is reconciled and replaced with a higher fence, never revived.

Terminal evidence is a protected write surface. Builders, generic application roles and ordinary operators must be structurally unable to emit `accepted` or `frozen` events. Only the independently authenticated verifier/acceptance actor may append a terminal receipt, and the Native Surrogate may countersign without rewriting its evidence.

Every run and terminal receipt is bound to the layer-definition digest, code/merged-tree SHA, upstream content hashes, lease fence and run generation. Definition supersession, deployment change or a higher fence makes an older run ineligible to publish current acceptance even if it later finishes successfully.

## 4. Scheduler

After every event and on every monitor tick:

1. Refresh authoritative definition and asset terminal states.
2. Compute the topological ready frontier for the open layer.
3. Exclude claimed assets, unresolved shared-write conflicts and unmet automated preconditions.
4. Score remaining work by correctness risk, critical-path position, downstream unlock, expected duration and integration readiness.
5. Reserve capacity for analysis, implementation, independent verification and release—not just coding.
6. Spawn or assign the smallest complete work packet.
7. Write ownership before mutation.
8. Recompute after completion, failure, merge, deployment, rebuild or definition supersession.

The scheduler never opens the next layer to avoid idleness. It may run current-layer analysis, focused tests, tracker wiring, release preparation or DAG audit that directly unlocks the open layer.

## 5. Concurrency and backpressure

There is no fixed global agent cap in the doctrine. Actual concurrency is:

`min(DAG-independent ready work, isolated work surfaces, verifier capacity, CI capacity, database/write locks, deployment capacity)`

Rules:

- One write owner per file, table and contract surface.
- One production migration writer and one production build writer per conflicting domain.
- Parallel analysis is broader than parallel mutation.
- Keep verifier and integrator capacity proportional to implementers.
- If review, CI, deploy or rebuild queues grow, stop starting assets and swarm the bottleneck.
- Prefer completing a nearly frozen asset over starting another low-unlock asset.

## 6. Worktree, database and Git isolation

- Create an isolated worktree from current protected `main` for every independent mutation lane.
- Name the branch and worktree after the asset or work packet.
- Record base SHA, owned paths, database/schema isolation and dependencies before editing.
- Reserve migration identifiers or otherwise serialize migration creation according to repository convention.
- Do not absorb unrelated dirty changes or use a branch name as proof of isolation.
- Rebase or reconcile immediately before integration; verify the exact candidate tree.
- Use protected pull requests or merge queues and never bypass mandatory checks.
- Delete worktrees and branches only after merge, deployment, accepted evidence and durable handoff.
- Clean obsolete worktrees in bounded batches after proving they are merged, clean and unowned. Never use broad destructive cleanup.

## 7. Decision and clarification protocol

Agents do not ask the user routine implementation questions. They send a structured decision packet to the Native Surrogate:

- decision required;
- evidence and governing constraints;
- viable options and trade-offs;
- recommended option;
- reversibility and blast radius;
- effect on accepted throughput.

The surrogate records a ruling before action. It prefers, in order:

1. correctness, data preservation and recoverability;
2. accepted layer/DAG architecture and product truth;
3. actual product value, standardization and reuse;
4. critical-path throughput;
5. the least complex reversible implementation.

When an action requires authority the campaign does not possess or has no recoverable option, quarantine that dependent lane with an exact unblock condition and continue all independent work. Autonomy must not fabricate credentials, external availability, evidence or authorization.

## 8. Verification proportionality

Use one independent verifier for every terminal asset claim. Scale proof to risk:

- **Low blast radius:** focused tests, contract check, deployment/rebuild receipt and live consumer proof.
- **Normal:** add boundary cases, output digest or semantic diff and database integrity.
- **High fan-out/global/epistemically sensitive:** add independent re-derivation, controlled perturbation, provenance and downstream sampling.
- **Security/migration/destructive:** add specialized review, snapshot/restore or rollback proof and adjacent-bypass checks.

Do not run broad repository audits merely because they exist. A failing unrelated standing check becomes owned backlog; it blocks the asset only when it invalidates its acceptance or a mandatory merge/deploy path.

## 9. Release batching

Code and verify assets independently, but integrate compatible assets in a topological wave when this saves repeated CI and deployments. A release batch must have:

- no overlapping unresolved ownership;
- compatible migrations and contracts;
- independently reviewable commits;
- a single exact candidate tree;
- per-asset acceptance evidence after deployment.

Use a short adaptive batch window. Release a critical-path asset immediately when waiting for another item would delay downstream unlocks. High-risk roots, migrations and high-fan-out assets should normally release alone; ordinary independent assets may release in a small wave.

## 10. Anti-idle and recovery loop

Monitor numerical liveness signals, not impressions:

- last durable event per active task;
- agent/task status and lease expiry;
- build/run heartbeat and substep progress;
- CI, merge queue and deployment state;
- ready-but-unclaimed asset count;
- verifier/integration queue age;
- main/production divergence age.

Graduated response:

1. Refresh external state and distinguish legitimate wait from stall.
2. Nudge the current owner with the exact pending action.
3. Reconcile its worktree, branch, lease and partial results.
4. Replace a dead owner using a higher fence and durable state.
5. Dispatch a root-cause specialist after repeated identical failure.
6. Ask the Native Surrogate to adjudicate ambiguity.
7. Dispatch another independent critical-path task while the wait continues.

Before dispatch, the campaign adapter declares numeric ceilings for transient retries, wall clock, continuations and repeated failure fingerprints. A practical default is two bounded transient retries; a repeated identical deterministic fingerprint dispatches one root-cause lane rather than replaying the same work. Reaching the configured ceiling quarantines only the affected dependency cone and invokes the Native Surrogate.

Never create reports, reviews, agents or code changes solely to appear active. If no safe eligible work exists, an honest monitored wait is correct.

## 11. Tracker contract

The live tracker is a deterministic projection of accepted events and live systems. Show:

- frozen denominator and definition version;
- accepted/frozen count and remaining count;
- current layer, DAG wave and ready frontier;
- each asset's lifecycle state and last evidence time;
- active owners and legitimate waits;
- blockers with exact unblock conditions;
- quality and efficiency outcome after acceptance;
- main, deployed revision, production and data synchronization;
- source freshness, uncertainty and degraded states.

Do not display historical row presence or `lit` as campaign completion. Do not display a percentage when the denominator or lifecycle evidence is unknown.

## 12. Completion and cleanup

The conductor stops only when the scoped layer satisfies the master plan's layer-close contract. Then:

1. derive the final report from durable events;
2. verify no owned or unmerged work is hidden;
3. reconcile main, deployment, production data and tracker;
4. close leases and archive evidence;
5. remove only proven-safe temporary worktrees and branches;
6. record reusable learning without expanding the next layer;
7. mark the goal complete only after every scoped outcome is achieved.
