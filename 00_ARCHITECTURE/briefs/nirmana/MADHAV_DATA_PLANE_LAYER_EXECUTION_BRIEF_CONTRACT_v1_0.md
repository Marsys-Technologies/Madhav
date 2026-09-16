---
artifact: MADHAV_DATA_PLANE_LAYER_EXECUTION_BRIEF_CONTRACT
version: "1.0"
status: REUSABLE_EXECUTION_BRIEF_CONTRACT
produced_on: 2026-09-13
session_id: MADHAV-DATA-PLANE-EXECUTION-FOUNDATION-20260913
inherits: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
authority_boundary: "Template contract only; a populated brief requires separate strategic approval before execution."
changelog:
  - "1.0: Defines mandatory content, inventory, contracts, preservation, tests, gates and handoff for every later layer execution brief."
---

# Reusable layer execution-brief contract

## 1. Admission rule

A layer brief is executable only when the strategic parent has approved the exact populated brief and this task has opened a new bounded goal for that layer. Approval of a plan, a prior layer seal, code presence or a local commit is not execution authority. The brief must inherit every applicable `F01`–`F28` and `DP01`–`DP18` obligation from the [foundation contract](MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md); it may strengthen but not silently weaken them.

## 2. Required brief header

```yaml
artifact: MADHAV_DATA_PLANE_<LAYER>_EXECUTION_BRIEF
version: "<semver>"
status: APPROVED_FOR_EXECUTION
strategic_parent_task: "Madhav — Data Plane Strategic Architecture"
execution_task: "Madhav — Data Plane Execution"
approval_record: "<decision ID and immutable evidence>"
product_authority: "MADHAV_PRODUCT_DEFINITION v3.0"
strategy_version: "<adopted/amended data-plane strategy; never infer>"
layer: "<L0 Brahmagyan | L1 Gaṇita | L2 Bodha | L3 Kāla | L4 Phala | L5 Mīmāṃsā>"
goal_objective: "<exact bounded objective for create_goal>"
source_revision: "<full commit>"
accepted_upstream_contracts: ["<artifact/version/fingerprint>"]
owners: {implementation: "<one writer>", review: "<independent owner>", release: "<authority>"}
may_touch: ["<exact paths/globs>"]
must_not_touch: ["<positive protected paths/globs>"]
activation_prohibitions: ["<deploy/data/model/campaign/etc. not granted>"]
```

Missing approval, accepted upstream version, implementation owner, protected scope or exact goal is a hard admission failure.

## 3. Consumer contribution and non-goals

The brief must state:

- the layer's distinctive contribution to the full F02 path and the demanding consumer questions it changes;
- the specific earned distinctions, prevented errors, uncertainty reductions or exposed limitations expected;
- applicable product P/V requirements and F/DP obligations;
- what belongs to adjacent layers, serving or evaluation and is therefore a non-goal;
- safety, access, source-rights and excluded-output boundaries;
- the competent simpler baseline used for later value comparison.

No fixed asset count, inherited screen/view count or prose volume may serve as the contribution model.

## 4. Complete inventory and evidence classification

Inventory every in-scope and adjacent authority, including:

| Required class | Mandatory fields |
|---|---|
| Writers/data assets | identity, layer, source files, tables/views, registry metadata, generation, dependencies, actual/direct/transitive consumers, historical receipts |
| Non-writers/services | identity, callable surface, inputs/outputs, health/probe authority, consumers and service-specific proof |
| Projections/adapters | selected fields, transforms, filtering/ranking, fallbacks, context and caller |
| Answer authorities | retrieval, judgment/assessment, inquiry planner, synthesis, managed/raw MCP, persistence/replay/export owner |
| Historical/restricted capital | source, current authority, access/purpose gate, preservation and prohibited use |

Each observation declares `direct_source_read`, `generated_measurement`, `runtime_observation`, `historical_receipt` or `inference`, with source revision/time and search boundary. No private row inspection is performed merely to prove population. Historical counts remain attached to their original scope and revision.

## 5. Demand, offer and internal interplay contracts

For every material input/output, populate:

| Field | Requirement |
|---|---|
| Identity and owner | Canonical ID, semantic/interface version, producer/consumer owner |
| Exact grain | Subject/global scope, natural key, time/space/method/varga/configuration grain |
| Context | Tenant/subject, purpose/access, conventions, method/school, reference time/horizon |
| Semantics | Epistemic class, operator, units, precision, polarity/roles, occurrence/condition, missingness state |
| Lineage | Source/rule/fact/derivation/evidence-dependence IDs and upstream dependency set |
| Generation | Build/release ID, compatible consumed generations, snapshot/cache keys and freshness |
| Use | Actual transformation and exact receiving finding/decision; not merely fetched/available |
| Failure | Unavailable/inapplicable/unqualified/failed/stale/contradictory behavior and detector |
| Proof | Fixture, command/test, expected changed and invariant outputs, evidence destination |

Map internal asset interplay: which component defines, computes, enriches, projects, ranks, hydrates, interprets, serves, records or evaluates. Similar names do not prove duplicate authority; absence from a bounded caller search does not prove non-use.

## 6. Component dispositions and preserved kernels

Every component—not just every asset—receives one or more dispositions:

- `PRESERVE`: useful kernel/identity/relationship/interface/history remains unchanged;
- `INTEGRATE`: existing depth is present but not consumed or served;
- `ENRICH_CORRECT`: preserve working portions and fix/add the named semantics;
- `QUALIFY_LIMIT`: retain data/computation but narrow authority or method scope;
- `INVESTIGATE_CONSOLIDATION`: compare exact semantics/callers/value before choosing a successor;
- `HISTORICAL_RESTRICTED`: retain capital behind current gates;
- `RETIRE_AFTER_MIGRATION`: only with accepted successor, caller/history/provenance transfer and rollback;
- `UNRESOLVED_USE`: evidence gap remains explicit.

The disposition table names the preserved algorithm, stable IDs/natural keys, sources, tests, receipts and consumers. No whole asset is retired because it lacks a screen, has a low row count or resembles another name.

## 7. Layer-specific minimums

| Layer | Required focus | Boundary that must be tested |
|---|---|---|
| L0 Brahmagyan | identities/aliases, editions/rights, qualified rules, variants, prerequisites, exceptions, constants, event/activity ontology, temporal/geographic semantics | Source testimony ≠ executable rule ≠ empirical validation; no personal fate/global private observation |
| L1 Gaṇita | reproducible facts/configurations, frames/conventions, actual/partial formation, decomposed conditions, exact clocks/relationships/sensitivity | No invented meaning/fallback; L1 authority and honest unavailable/floored state |
| L2 Bodha | full participants/domains/polarity, signed paths, occurrence/condition, cancellations, contradictions, mechanisms and discovery hypotheses | Topology/score/navigation ≠ cause, formation or temporal activation; no authority inversion |
| L3 Kāla | applicable method bundles, exact contacts/intervals, clock hierarchy, structure identity, enable/inhibit, alternatives and recurrence | Activity/intensity ≠ event probability; shared inputs ≠ independent temporal evidence |
| L4 Phala | outcome-specific bridge, alternatives, falsifiers, constraints, feasibility, permitted claim framing and honest gap | No generic domain score as manifestation; no self-calibration or outcome leakage |
| L5 Mīmāṃsā | observation revisions, frozen claim identity, eligibility/denominators, challenge/comparison/evaluation and future-artifact admission | Capture ≠ learning; retrospective fit ≠ prospective validity; C3 firewall |

## 8. Compatibility, cascade, rebuild and rollback

The brief supplies a compatible-generation matrix and correction matrix. For each changed meaning/input/computation/observation/policy, name affected producers, projections, consumers, caches, delivered-current artifacts and protected historical artifacts. Define stale-before-reuse behavior, rebuild order, idempotency, resumability, partial-failure recovery, cost/latency visibility and a reversible prior compatible set.

Later writer implementation must conform to the frozen `WriterBase` contract, transaction ownership, no writer-authored throughput, layer idempotency and honest floors/statuses. Any apparent orchestrator contract change is returned to strategy/native authority.

## 9. Mandatory tests and proof tiers

The brief makes each applicable test executable, with fixture, expected result, invariant, detector, command and evidence path:

1. qualification/source and competing-witness scope;
2. computational or service correctness and failure;
3. relevant-input influence;
4. irrelevant-input/order/presentation control;
5. duplicate/shared-root/correlation control;
6. missingness and wrong subject/tenant/context/generation control;
7. boundary/precision/timezone/horizon/sensitivity;
8. omission challenge for applicable concepts/relationships/counterevidence;
9. served-evidence sentinel through projection, ranking, cache, adaptive passes, budgets and synthesis;
10. revision/invalidation/snapshot/replay/rollback;
11. managed Paripraśna/MCP equivalence and raw MCP scoped evidence;
12. competent simpler-baseline comparison with correct added distinctions, prevented errors, uncertainty, comprehension, added error, burden and cost;
13. separately governed empirical evaluation, only where eligible.

Verdicts are separated into: `COMPUTATIONAL_CORRECTNESS`, `EXPLANATORY_DISCRIMINATIVE_VALUE`, and `EMPIRICAL_OUTCOME_PERFORMANCE`. A producer perturbation or synthetic fixture cannot satisfy the third.

## 10. Exit gates and evidence packet

| State | Required layer evidence |
|---|---|
| `PRODUCER_READY` | Accepted contracts implemented; qualification/computation/context/failure/compatibility proof |
| `INTEGRATED` | Receiving consumers use the fields and pass influence/negative/duplication/missingness/omission tests |
| `DEPLOYED_OPERATIONALLY_ACCEPTED` | Authorized actual revision/environment, applicable migration/build, live managed path and rollback readiness |
| `CONSUMER_VALUE_DEMONSTRATED` | Equivalent-question simpler baseline comparison and consumer distinction evidence |
| `EMPIRICALLY_EVALUATED` | Governed prospective/held-out, frozen-claim, denominator-aware performance evidence |

The terminal packet includes full commits/revisions, exact files/tables/services, validation commands and raw results, state reached/not reached, independent review, preserved residuals, costs, rollback, and all unresolved strategic decisions. It returns decisions that change product meaning, architecture, safety, adoption or scope; execution does not decide them.

At close, the execution ledger returns to `WAITING_FOR_STRATEGIC_BRIEF`. The next layer/packet does not start automatically.

