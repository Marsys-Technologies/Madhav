---
artifact: NIRMANA_ELEVATION_PLAN_v6_0.md
canonical_id: NIRMANA_ELEVATION_PLAN
version: "6.0"
status: CURRENT-FROZEN-FOR-EXECUTION
campaign_id: nirmana-elevation
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: NIRMANA_ELEVATION_PLAN_v4_0.md (internal version 5.0, PROPOSED)
produced_on: 2026-08-25
---

# Nirmāṇa Elevation Plan v6.0

## 1. Frozen North Star and scope

Complete Nirmāṇa elevation for canonical chart `482012f1-710e-4a25-994a-93821f5871aa` and its shared substrate. Completion means every in-scope asset is classified in one frozen denominator, is executed once after its dependencies and code are accepted or receives a permitted non-build disposition, is independently verified, and is frozen in strict L0→L5 order. Main, production, and the tracker must agree at close.

The old v5.0 plan is useful historical analysis only. Its counts, progress, ledger states, and seals are not authoritative until re-derived from current runtime evidence. The historical dirty checkout remains read-only.

## 2. Non-negotiable execution rules

1. T0 freezes no count until it reconciles the live registry, writer discovery, seed, migrations, planner/dispatch, producer coverage, consumer surfaces, and build evidence.
2. Every asset appears exactly once in the manifest, has a layer/wave/obligation, and has no dangling, cyclic, backward-layer, or duplicate producer relationship.
3. A build asset freezes only with accepted analysis, an optimization/correctness decision, one accepted post-deploy execution, integrity verification, and an independent freeze receipt. `lit`, row presence, or a historical seal cannot substitute.
4. L0 through L5 and each topological wave are sequential; independent work may be parallel only on disjoint code and write sets.
5. Optimizations preserve a declared output identity contract. Output changes are correctness changes with their own expected-output verification.
6. The tracker projects evidence; it never creates its own proof. Unknown, unavailable, stale, and degraded states remain visible.
7. No credentials, history rewrites, force pushes, direct-main writes, applied-migration edits, gate weakening, or unrecoverable data loss are permitted.

## 3. Context and current contradictions

`NIRMANA_ELEVATION_CONTEXT_PACK_v6_0.md` is the current compact task packet. At freeze time, production and `origin/main` both identify `872df060152a3e0adb9433df9f8e297af9f00ff8`; Cloud Run revision `amjis-web-01702-gbn` is Ready. There is no active Nirmāṇa build evidenced.

The historical campaign stopped at R0 intake, with no accepted Nirmāṇa rebuild or layer freeze. Its runner-provenance finding is retained as a T0/F0 hypothesis, not accepted completion. Local database credentials are absent, so the live SQL census is an explicit evidence gap until a configured, read-only connection is available without exposing secrets.

## 4. State machine

`BOOTSTRAP → T0_CENSUS → PLAN_FROZEN → DENOMINATOR_FROZEN → F0_FOUNDATION → L0 → L1 → L2 → L3 → L4 → L5 → CLOSING → COMPLETE`.

This plan is frozen now. The denominator and waves are deliberately not hardcoded: they become frozen only at the successful T0 exit. Material changes to this plan require an evidence-backed, append-only ADHIKĀRIN ruling; they cannot weaken §2.

## 5. T0 acceptance

T0 performs no asset rebuild. It creates a reconciling definition, resolves all catalog/DAG contradictions, computes the canonical manifest digest, supersedes only safely, inserts a frozen definition, and verifies that tracker totals and each layer/wave derive from that exact revision. It also records release main SHA, deployed SHA, deployed revision, observation time, freshness, and failure semantics.

## 6. F0 foundation lanes

- **A — asset/DAG census:** canonical identity, dependency/producer/partition/consumer/count/integrity contracts and reproducible fingerprints.
- **B — run/progress truth:** chart- and run-scoped state, terminal outcomes, retries, blockers, and determinate units only where real totals exist.
- **C — hash/invalidation:** reproducible digest inputs, bounded invalidation, and mutation proof for omission, ordering, partition, and collision cases.
- **D — tracker/release:** authoritative Git/Cloud Run reconciliation with explicit stale/unavailable semantics.
- **E — evidence control:** authenticated audited, idempotent definition/event writing with typed lifecycle receipts.

F0 is accepted only after focused and broader tests, migration verification where applicable, a partition-scale canary, independent deployment/release verification, and tracker synchronization. A canary is machinery proof, never an accepted full asset rebuild.

## 7. Per-asset method and close criteria

For every frozen-manifest asset: analyze purpose/dependencies/writes/consumers/integrity/baseline; decide optimization or disposition from measurement; make the smallest isolated change; independently review and deploy; execute once at its accepted point; independently verify outputs, consumer reachability, tracker evidence, and invalidation; then freeze. Producer-covered assets inherit their producer evidence and are not rebuilt twice.

Campaign completion requires a valid digest-verified manifest, no unresolved catalog/DAG contradiction, all F0 contracts accepted, every asset frozen or validly dispositioned, all six layers frozen sequentially, merged/deployed green changes, verified migrations and live revision provenance, reconciled tracker totals, no active orphaned run, and immutable evidence citations in the final report.

## 8. Decision and amendment log

### NIR-V6-D-001 — 2026-08-25 — No grandfathered acceptance; scoped re-execution

Prior L0–L5 seals can be retained as read-only baseline evidence only. They cannot define the v6 denominator or earn a v6 accepted-rebuild/freeze credit. T0 must freshly reconcile and freeze the manifest; after deployed F0, every `build` asset receives exactly one v6 accepted execution in frozen layer/wave order. Every non-build asset receives a formal permitted disposition, and a `producer_covered` asset inherits its producer’s execution and must not rebuild separately.

The ruling follows the user-authorized v6 terminal contract and the old campaign’s own durable state: v5.0 was PROPOSED, R0 stopped at intake, R1–R5 were never opened, and the old scorecard was measurement-only. This is reversible in documentation but preserves the non-reversible data-integrity constraint: no historical completion label is converted into a new acceptance receipt.
