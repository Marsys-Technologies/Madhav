---
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT
version: "1.0"
status: REUSABLE_EXECUTION_BRIEF_CONTRACT
produced_on: 2026-09-13
session_id: MADHAV-DATA-PLANE-EXECUTION-FOUNDATION-20260913
inherits:
  - MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
  - MADHAV_DATA_PLANE_LAYER_EXECUTION_BRIEF_CONTRACT_v1_0.md
authority_boundary: "Template contract only; no asset/interface work is authorized without a separately approved populated brief."
changelog:
  - "1.0: Defines exact ownership, semantic delta, preservation, compatibility, focused proof, review and terminal evidence for asset/interface execution packets."
---

# Reusable asset/interface execution-brief contract

## 1. Admission and exact authority

An asset/interface packet is executable only when the strategic parent approves this fully populated contract and the execution task opens a new bounded goal. The packet may implement only the stated semantic delta. It cannot infer authority from a layer plan, historical acceptance, current code, a migration number, generated inventory, tests or deployment.

Required header:

```yaml
artifact: MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF
version: "<semver>"
status: APPROVED_FOR_EXECUTION
approval_record: "<immutable decision evidence>"
parent_layer_contract: "<artifact/version/fingerprint>"
foundation_contract: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
asset_or_interface_ids: ["<exact IDs>"]
goal_objective: "<exact bounded create_goal objective>"
source_revision: "<full commit>"
accepted_upstream_contract: "<artifact/version/fingerprint>"
implementation_owner: "<single writer owner>"
independent_review_owner: "<read-only or isolated reviewer>"
release_authority: "<owner; NONE if not granted>"
may_touch: ["<exact files/tables/services>"]
must_not_touch: ["<protected surfaces>"]
```

If implementation owner, exact files/tables/services, accepted upstream contract/version, observed failure, expected consumer distinction or protected scope is missing, do not start.

## 2. Current-state evidence

The populated brief must identify:

- exact asset/interface identity, layer, owner and registry/catalog metadata;
- implementation files, tables/views, services/routes, migrations, projections/adapters and caches;
- current algorithm/operator, inputs, outputs, grain, units, conventions, failure/fallback behavior and idempotency;
- direct, transitive, dynamic, audit and historical consumers, with bounded-search limits;
- current generations, compatible upstream inputs, preserved snapshots/history and applicable receipts;
- epistemic class, operator and actual authority of every important field;
- source revision and observation time, separating source observation, generated measurement, runtime proof, historical receipt and inference.

No private-row read is justified solely to show population. A dormant or unreachable-looking component remains `UNRESOLVED_USE` until the approved investigation scope supports a stronger conclusion.

## 3. Failure or missing capability

State one falsifiable problem:

| Field | Required content |
|---|---|
| Observed behavior | Exact input/context and actual output/state |
| Evidence | File/line, query/test/receipt or runtime observation with revision/time |
| Expected contract | Accepted upstream/layer/foundation ID |
| Defect class | Missing, flattened, unqualified, unused, wrong authority, wrong context, stale/mixed generation, unserved, duplicate support, unsafe flow or detector mismatch |
| Impact | Specific wrong/missing consumer distinction, error, uncertainty or limitation |
| Non-claim | What the evidence does not prove (for example live incidence, doctrine validity or empirical causation) |

## 4. Semantic change and expected distinction

Describe the smallest sufficient semantic delta:

- fields/relations/operators added, corrected, consumed, qualified or removed;
- exact old versus new behavior for positive, negative, boundary, missing and duplicated inputs;
- epistemic and method authority; participants/roles/domains/polarity/occurrence/condition/ancestry where relevant;
- expected change in the receiving finding/decision and outputs that must remain invariant;
- why extension/composition is preferred, or why a new boundary is genuinely necessary;
- competent simpler baseline and the value metric; added error, burden, latency and cost.

No new field is “used” until the receiving transformation and served finding are proven. Computational influence is not astrological causation or empirical performance.

## 5. Preservation, migration, history and rollback

The packet lists preserved kernels: algorithms, sources, stable IDs/natural keys, relationships, interfaces, tests, receipts, historical readings/claims, failures and restricted research capital. For every altered component, declare one of the foundation dispositions and explain why.

Migration/cutover requirements include:

- backward/forward compatibility and adapter lifetime;
- existing caller and dynamic-consumer handling;
- provenance and evidence-dependence transfer;
- correction blast radius, stale marks, cache invalidation and compatible-generation selection;
- idempotent/resumable rebuild or service transition;
- immutable historical delivered readings and issued claims;
- rollback trigger, procedure, prior compatible set and evidence that rollback does not erase history.

Retirement is forbidden until successor, caller migration, audit/history/provenance transfer and reversible rollback are proved and separately authorized.

## 6. Focused proof matrix

Every row names fixture/data boundary, command, expected result, invariant, detector and retained evidence.

| Proof | Required test |
|---|---|
| Positive | Qualifying input produces the exact changed semantic output. |
| Negative | Inapplicable/unsupported/forbidden input is rejected or returns the correct explicit state. |
| Relevant influence | Change one qualifying field; declared receiving output changes and unrelated outputs remain stable. |
| Irrelevant control | Alias order, array order, cosmetic/presentation or unrelated field cannot change evidential meaning. |
| Duplication/correlation | Repeated source/wrapper/path/total-component ancestry cannot inflate independent support. |
| Context/missingness | Wrong tenant/subject/purpose/method/generation fails or isolates; zero/absence/unavailable/unqualified/failed/unexplored remain distinct. |
| Boundary/precision | Adjacent interval, timezone, horizon, tolerance, varga/input sensitivity or method boundary preserves semantics. |
| Delivery | A decisive non-default sentinel survives SQL projection, retrieval/ranking, cache, adaptive inquiry, budget, synthesis, managed channel, persistence/replay and permitted export as applicable. |
| Revision | Correction invalidates current derivatives/caches, emits a coherent new generation, preserves original delivered/issued artifacts and can roll back. |
| Value | Equivalent question/context/budget versus simpler baseline measures correct distinction, prevented error, uncertainty, comprehension, added error, burden and cost. |
| Evaluation | Only if separately governed: frozen eligible claims, independent outcomes, denominators, held-out/prospective partitions, baselines and uncertainty. |

Service/source assets use response/source semantics and failure proofs, not fabricated row floors. Detector-backed status is mandatory: a claimed PASS must name a path that would produce failure under a negative fixture.

## 7. Implementation and review discipline

- One writer surface: this execution task’s isolated worktree or a separately authorized isolated worktree named in the brief.
- Preserve dirty/shared/foreign worktrees; no concurrent mutation of the same branch/ref.
- Follow accepted dependency order and frozen orchestrator/transaction/idempotency contracts.
- Use only authorized migrations/builds/deployments/data access; absence of authority is `NOT_RUN`, not a reason to improvise.
- Independent review receives the approved contract, diff and evidence; it checks correctness, authority, preservation, security/privacy, compatibility and test sufficiency. Findings are retained with disposition and re-verification.
- Green CI, a PR, deployment status, row count or dashboard is not terminal proof by itself.

## 8. Terminal evidence packet

Return:

1. approved brief/goal/authority and accepted upstream pin;
2. exact commits and changed files/tables/services/migrations;
3. old/new semantic examples and expected consumer distinction;
4. preservation/migration/compatibility/generation/invalidation/rollback evidence;
5. raw commands and results for every applicable focused proof;
6. independent review identity, findings, resolutions and re-check;
7. delivery state actually reached and explicitly unreached later states;
8. runtime/deploy/build/data evidence only if separately authorized and actually observed;
9. residual risks, unresolved use and decisions returned to the strategic parent;
10. confirmation of protected surfaces not touched and next stage remaining unauthorized.

The task then updates the execution ledger and waits. It never uses the packet to approve itself or begin another asset/layer.

