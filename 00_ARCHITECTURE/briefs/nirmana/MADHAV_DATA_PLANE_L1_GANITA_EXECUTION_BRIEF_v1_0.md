---
artifact: MADHAV_DATA_PLANE_L1_GANITA_EXECUTION_BRIEF
version: "1.0"
status: APPROVED_FOR_EXECUTION
approved_on: 2026-09-14
strategy_decision: DP-SD-013
strategic_parent_task: "Strategy — Data Plane / 01a0996e-6ca0-7642-ac31-f968fee214b3"
execution_task: "Execution — Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
approval_record: "DP-SD-013 at strategy content commit 7e101ffc31e28ca902265def6de733a5286705e5"
product_authority: "MADHAV_PRODUCT_DEFINITION v3.0 / CCD-010"
strategy_version: "MADHAV_DATA_PLANE_VALUE_ARCHITECTURE v2.0 amended by DP-SD-009, accepted L0 DP-SD-012 and MADHAV_DATA_PLANE_L1_GANITA_STRATEGY v1.0 / DP-SD-013"
layer: "L1 Gaṇita"
goal_objective: "Elevate L1 Gaṇita to verified PRODUCER_READY status under Product Definition v3.0, DP-SD-009, DP-SD-012, DP-SD-013 and the Data Plane Execution Foundation: consume the accepted L0 release at f6fed12c794224329f6b3b436f8b1b814499d06d without changing its meaning; reconcile and disposition all 19 current L1 writers plus adjacent numerical services and producer projections; establish exact calculation-context, stable fact/configuration, decomposed-condition, typed-relation, precise-clock, sensitivity, epistemic, missingness, generation and correction contracts; preserve viable numerical kernels, data identities, history, interfaces, WriterBase/idempotency and Swiss-state boundaries; implement only evidence-justified L1 and direct producer-adapter deltas in dependency order; prove L1-SLICE-RESOURCE-CONFIG-01 with deterministic non-person fixtures and honest unqualified/not-reachable states; and return terminal evidence without beginning L2, reopening the historical campaign, changing L0/product/safety/source-rights authority, or claiming integration, deployment, consumer value or empirical performance not actually proved."
source_revision: f6fed12c794224329f6b3b436f8b1b814499d06d
accepted_upstream_contracts:
  - "MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES/1.0/blob-2fda304d627183b380e36ee1e817e08a8391119c@f6fed12c794224329f6b3b436f8b1b814499d06d"
  - "MADHAV_DATA_PLANE_LAYER_EXECUTION_BRIEF_CONTRACT/1.0/blob-2ea6becdcff6232921bb3ad1521db2ecfc01f3a7@f6fed12c794224329f6b3b436f8b1b814499d06d"
  - "MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT/1.0/blob-71ff974ec92d03dbe755a53cd1d1f6b189543f07@f6fed12c794224329f6b3b436f8b1b814499d06d"
  - "MADHAV_DATA_PLANE_L0_PRODUCER_READY_ACCEPTANCE/1.0/blob-2ff60068c8b578a269c7962b37b23822e356b211@f6fed12c794224329f6b3b436f8b1b814499d06d"
  - "MADHAV_DATA_PLANE_L0_SEMANTIC_RELEASE_AND_ADAPTER_CONTRACT/1.0/blob-ec1d3871675f0fdc38bf0eb28e8d38bb2a7814ff@f6fed12c794224329f6b3b436f8b1b814499d06d"
  - "MADHAV_DATA_PLANE_L0_SOURCE_RULE_QUALIFICATION_CONTRACT/1.0/blob-fb21d0bf8c46ae4dfc05ec5fc6c1dfdd373045cb@f6fed12c794224329f6b3b436f8b1b814499d06d"
  - "MADHAV_DATA_PLANE_L0_CONVENTION_SERVICE_RESTRICTED_CAPITAL_CONTRACT/1.0/blob-625070cad8ecea4ad4bb23dfad403f4594d45f88@f6fed12c794224329f6b3b436f8b1b814499d06d"
  - "MADHAV_DATA_PLANE_L0_RESOURCE_CONFIG_SLICE/1.0/blob-9fe6787bb63b71c54a239ee4992c3c1c8b33bfa4@f6fed12c794224329f6b3b436f8b1b814499d06d"
  - "MADHAV_DATA_PLANE_L0_COMPATIBILITY_CORRECTION_ROLLBACK/1.0/blob-fcd609fbb71e4c06b3e2a7ad757feeaadf74ffbd@f6fed12c794224329f6b3b436f8b1b814499d06d"
  - "MADHAV_DATA_PLANE_EXECUTION_LEDGER/1.0/blob-e9ca2eb6b6c6c2b4dd4dff4537b4548dcbc4f863@f6fed12c794224329f6b3b436f8b1b814499d06d"
owners:
  implementation: "Execution — Data Plane / one writer"
  review: "independent read-only reviewer, separate from implementation"
  release: "Strategy — Data Plane under native product-owner authority"
may_touch:
  - "platform/python-sidecar/ga_writers/**"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/tests/test_ga_*.py"
  - "platform/python-sidecar/brahmagyan/ganita/**"
  - "platform/python-sidecar/pyjhora_adapter/_ayanamsha.py"
  - "platform/python-sidecar/pyjhora_adapter/compute.py"
  - "platform/python-sidecar/pyjhora_adapter/dashas.py"
  - "platform/python-sidecar/pyjhora_adapter/dignities.py"
  - "platform/python-sidecar/pyjhora_adapter/houses.py"
  - "platform/python-sidecar/pyjhora_adapter/panchanga.py"
  - "platform/python-sidecar/pyjhora_adapter/positions.py"
  - "platform/python-sidecar/pyjhora_adapter/reconciliation.py"
  - "platform/python-sidecar/pyjhora_adapter/sensitive_points.py"
  - "platform/python-sidecar/pyjhora_adapter/special_lagnas.py"
  - "platform/python-sidecar/pyjhora_adapter/strength.py"
  - "platform/python-sidecar/pyjhora_adapter/transits.py"
  - "platform/python-sidecar/pyjhora_adapter/vargas.py"
  - "platform/python-sidecar/pyjhora_adapter/yogas.py"
  - "platform/python-sidecar/pyjhora_adapter/version.py"
  - "platform/python-sidecar/tests/test_ga_*.py"
  - "platform/python-sidecar/tests/test_l1_*.py"
  - "platform/python-sidecar/tests/test_ganita_*.py"
  - "platform/python-sidecar/tests/test_pyjhora_adapter/**"
  - "platform/python-sidecar/scripts/validate_data_plane_l1_*.py"
  - "platform/src/generated/nirmana-writer-digests.json"
  - "platform/supabase/migrations/*_data_plane_l1_*.sql"
  - "platform/migrations/*_data_plane_l1_*.sql"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_CURRENT_STATE_AND_DISPOSITION_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_CONTEXT_FACT_CONFIGURATION_CONTRACT_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_CONDITION_RELATION_CLOCK_CONTRACT_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_RESOURCE_CONFIG_SLICE_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_COMPATIBILITY_CORRECTION_ROLLBACK_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_VALIDATION_AND_REVIEW_RECORD_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_PRODUCER_READY_ACCEPTANCE_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_EXECUTION_LEDGER_v1_0.md"
must_not_touch:
  - "CLAUDE.md"
  - "CLAUDECODE_BRIEF.md"
  - "00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md"
  - "00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md"
  - "00_ARCHITECTURE/CAPABILITY_MANIFEST.json"
  - "00_ARCHITECTURE/CURRENT_STATE_v1_0.md"
  - "00_ARCHITECTURE/SESSION_LOG.md"
  - "00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md"
  - "00_ARCHITECTURE/MACRO_PLAN_v2_0.md"
  - "00_ARCHITECTURE/L1_GANITA_CLOSURE_v2_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_GANITA_STRATEGY_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_GANITA_EXECUTION_BRIEF_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_*.md"
  - "platform/python-sidecar/brahmagyan/l0_*.py"
  - "platform/python-sidecar/brahmagyan/l0_*.json"
  - "platform/python-sidecar/ga_writers/__tests__/test_l0_*.py"
  - "platform/python-sidecar/pyjhora_adapter/_isolation.py"
  - "platform/python-sidecar/tests/test_l0_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/base.py"
  - "platform/python-sidecar/pipeline/orchestrator/runner.py"
  - "platform/python-sidecar/pipeline/orchestrator/asset_runner.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/bg_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/bo_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ka_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ph_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/mi_*.py"
  - "platform/python-sidecar/bodha_writers/**"
  - "platform/src/lib/retrieval/registry/layers/**"
  - "platform/src/lib/pariprashna/**"
  - "platform/src/lib/synthesis/**"
  - "platform/src/lib/mcp/**"
  - "platform/src/generated/nirmana-analysis-layer-pins.json"
  - "00_ARCHITECTURE/briefs/nirmana/sessions/**"
  - ".github/workflows/**"
  - "**/*credential*"
  - "**/*secret*"
activation_prohibitions:
  - "push, PR, merge, merge queue, deploy, production mutation or destructive rebuild"
  - "active Nirmāṇa campaign event, registry, lease, queue, freeze or historical-receipt mutation"
  - "L0 meaning/source/right changes; L2-L5 implementation; retrieval/Paripraśna/synthesis/MCP cutover"
  - "private-row inspection, stored personal chart use, life-observation/cohort/claim/evaluation activation"
  - "medical diagnosis, individualized mortality/lifespan output, remedial-efficacy or Vāstu-service expansion"
  - "Product Definition, CCD, canonical manifest, consent, safety or source-rights expansion"
  - "future convergence-pin fabrication, model/feature admission or empirical-performance claims"
strategy_parent: MADHAV_DATA_PLANE_L1_GANITA_STRATEGY_v1_0.md
execution_task_id: 01a0998a-8240-7631-97ce-36c6d4734fde
execution_branch: codex/madhav-data-plane-execution
execution_base: f6fed12c794224329f6b3b436f8b1b814499d06d
delivery_target: PRODUCER_READY
next_stage_hold: "L2 remains WAITING_FOR_STRATEGIC_BRIEF."
changelog:
  - "1.0: Authorizes one bounded autonomous L1 Gaṇita producer-ready execution across the current 19 writers and adjacent numerical service/projection capital, with exact accepted-L0 pins, scope, first slice, evidence and stop conditions."
---

# Execution brief — L1 Gaṇita producer readiness

## 1. Strategic authority and outcome

Execute `DP-SD-013` and the paired L1 strategy against the accepted L0 terminal
revision. The result must be a versioned, reproducible and challengeable Gaṇita
producer contract across all 19 current writers, with exact context, fact,
condition, configuration, relation, clock, sensitivity, generation and failure
semantics.

The historical 19/19 Nirmāṇa freeze is preserved as evidence. This work does not
reopen or replay that campaign and does not infer current population, deployment,
serving, value or empirical status from it. End at `PRODUCER_READY`; do not begin
L2 or consumer integration.

## 2. Set the new bounded goal

Before substantive work, call `create_goal` once, without a token budget, using
exactly the `goal_objective` from this brief's header:

> Elevate L1 Gaṇita to verified PRODUCER_READY status under Product Definition v3.0, DP-SD-009, DP-SD-012, DP-SD-013 and the Data Plane Execution Foundation: consume the accepted L0 release at f6fed12c794224329f6b3b436f8b1b814499d06d without changing its meaning; reconcile and disposition all 19 current L1 writers plus adjacent numerical services and producer projections; establish exact calculation-context, stable fact/configuration, decomposed-condition, typed-relation, precise-clock, sensitivity, epistemic, missingness, generation and correction contracts; preserve viable numerical kernels, data identities, history, interfaces, WriterBase/idempotency and Swiss-state boundaries; implement only evidence-justified L1 and direct producer-adapter deltas in dependency order; prove L1-SLICE-RESOURCE-CONFIG-01 with deterministic non-person fixtures and honest unqualified/not-reachable states; and return terminal evidence without beginning L2, reopening the historical campaign, changing L0/product/safety/source-rights authority, or claiming integration, deployment, consumer value or empirical performance not actually proved.

Do not reuse the completed L0 goal. Mark the new goal complete only after every
L1 producer-ready exit gate is satisfied. A hard blocker is returned under the
goal rules with the smallest missing strategy decision; routine uncertainty is
resolved autonomously from the pinned evidence and safe defaults.

## 3. Mandatory entry gate

Before mutation:

1. verify the permanent execution task is in its isolated worktree on
   `codex/madhav-data-plane-execution`, clean at exact commit `f6fed12c7`;
2. verify the injected permission profile is Full Access/unrestricted with
   approval policy `never`, and that the repository handshake truthfully records
   `tool_profile: madhav-parity`; if the host is managed/on-request, do not start
   L1 and return `HOST_PERMISSION_PROFILE_BLOCKER` to Strategy;
3. read `AGENTS.md`, `CLAUDE.md` and its complete mandatory session-open sequence;
4. read the accepted upstream artifacts by the immutable blob/revision pins in
   the header, the L1 strategy and this exact approved brief;
5. use `layer-value-elevation` for portfolio/consumer contracts and
   `autonomous-asset-elevation` for implementation; follow any stricter gates;
6. verify this brief's strategy content/metadata commits are present on the
   execution branch, normally by clean cherry-pick of the exact commits named in
   the kickoff prompt; and
7. remeasure Git, current generated 19-writer inventory, source/tests/schema,
   producer projections/consumers and proportionate aggregate/service evidence.

Historical counts, floors, PRs, freeze events and closure prose retain their
bounded revision/time. They are leads and regression evidence, not current truth.

## 4. Autonomous operating contract

Proceed fully autonomously inside the fixed scope. Do not ask for routine
approvals, permission escalation, implementation preferences, test choices or
whether to continue. Use reversible local actions and make evidence-backed
choices in dependency order. Keep one implementation writer and obtain a
separate read-only independent review before acceptance.

Authorized:

- read-only repository/Git/inventory/current-source and proportionate aggregate
  runtime/database inspection already available without private rows;
- local L1 producer, numerical adapter, deterministic fixture, validation,
  forward-only schema and producer-contract work inside `may_touch`;
- exact current-consumer tracing anywhere read-only;
- local commits on `codex/madhav-data-plane-execution`;
- deterministic generated writer-digest regeneration when required, without
  inventing a protected convergence commit; and
- independent read-only review and correction of all in-scope HIGH/CRITICAL.

Not authorized:

- push, PR, merge/queue, deploy, production/data mutation, live migration,
  destructive rebuild, campaign event/lease/freeze/receipt mutation;
- any L0 semantic/source/right edit or L2-L5 implementation;
- retrieval/query/ranking, Paripraśna, synthesis, MCP, delivery/replay/export or
  evaluation cutover;
- product/safety/consent/source-rights adoption, private chart/observation use,
  specialized-service activation, feature/model admission or empirical claim;
- modification of frozen WriterBase/orchestrator/Swiss-state boundaries; or
- fabrication of `nirmana-analysis-layer-pins.json` with a future merge SHA.

Stop only for a real product/adoption, source-rights/doctrine, safety/privacy,
credential, irreversible/destructive, protected-delivery, permission-profile or
irreconcilable governance gate. Preserve completed work and state the exact
smallest decision needed. Missing live credentials simply make that proof
`NOT_RUN` unless live proof is itself an entry requirement.

## 5. Fixed owned inventory and mutation boundary

The denominator is exactly these 19 current writers:

`ga_positions`, `ga_vargas`, `ga_dashas`, `ga_nakshatra`, `ga_panchanga`,
`ga_sensitive`, `ga_sensitive_degree`, `ga_strength`, `ga_structural`,
`ga_condition`, `ga_yoga`, `ga_vichara`, `ga_sade_sati`,
`ga_transit_anchors`, `ga_tajaka`, `ga_ayurdaya`, `ga_medical`, `ga_vastu` and
`ga_prashna`.

The header's `may_touch` list is the immutable outer boundary. L1-WP0 must narrow
it to exact files, tables/categories/natural keys, services and tests before the
first edit. An existing file is not permission to edit it. A path may be added
to the working manifest only when it already matches a header class and directly
implements a fixed L1 contract. A new path class, L0 semantic change, L2-
consumer change, orchestrator change or activation decision returns to Strategy.

All existing migrations are immutable. A new migration must match an approved
`*_data_plane_l1_*.sql` glob and is created only after proof that the accepted
contract cannot fit the current schema, with forward compatibility, idempotency,
ordering and rollback/read-compatibility. It is tested locally and never applied
to a live database in this goal.

Shared tables are protected by asset/category/natural-key ownership. Do not
delete, rewrite or reinterpret another writer's rows. The frozen WriterBase,
caller-owned transaction, no-writer-commit/close/throughput, idempotency and
shared `SWISS_STATE_LOCK` contracts remain unchanged.

## 6. Required work packets

### L1-WP0 — stocktake, consumer backcast and exact evidence pin

- Reconcile 19/19 current writer identities to orchestrator adapter, numerical
  source files, dependencies, tables/categories/natural keys, algorithms,
  epistemic role, outputs, direct/transitive/dynamic consumers, generated
  digests and historical receipts.
- Resolve adjacent `ga_chart_service` history to actual current engine/adapters/
  routes and record its callable/status evidence without changing denominator.
- Audit L1 retrieval projections and L2-L4 consumers read-only for dropped fields,
  local re-derivation, date truncation, fallback, filtering/ranking, shared-root
  duplication and wrong-context joins. These are demand findings, not mutation
  authority.
- Separate `present`, `populated`, `qualified`, `consumed`, `effect_traced`,
  `served` and `value_evaluated`; record source revision/time/search boundary.
- Classify all historical findings as current, fixed, superseded, unavailable or
  unresolved. In particular recheck precise clocks, sign-keyed AV, contributor
  prastāra, numerical-failure fallbacks and specialized-method restrictions.
- Produce the exact mutation manifest, preserved-kernel map and baseline before
  editing.

### L1-WP1 — calculation context and stable DP03 fact contract

- Define one versioned L1 calculation-context identity including subject/chart/
  build/generation, exact instant/location/timezone/precision, frame, ayanāṃśa,
  node, house convention, varga formula/domain, karaka/method school and engine
  version where applicable.
- Bind material L1 IDs and roles to the accepted L0 semantic release; preserve
  explicit mean/true nodes and reject ambiguous/unknown/wrong-generation values.
- Establish stable fact/configuration/interval identities, exact grain, units,
  typed value, source dependencies, verification class and failure/missingness.
- Prove cross-chart/build/context mismatch rejection, deterministic replay and
  no ordinary fact on numerical failure. Existing stable IDs remain compatible
  unless a proved correctness defect requires a versioned correction.

### L1-WP2 — DP04/DP05 conditions and configurations

- Preserve dignity, avasthā, motion, combustion, friendship, ṣaḍbala, bhāvabala,
  AV and other components with their own units/reasons and shared roots.
- Distinguish raw constituent, total, normalization and judged classification.
  Real zero is zero; unavailable, floored, inapplicable, unqualified, failed and
  unexplored are not zero.
- For each rule-derived occurrence, require exact L0 rule/version/qualification,
  participants/roles, satisfied/failed clauses, exceptions/cancellations and
  `formed|partial|not_formed|failed|method_inapplicable|unqualified_source`.
- No catalog label/citation or engineering fixture may create a qualified
  doctrinal firing. Bhāvat Bhāvam remains L2-owned and `UNQUALIFIED_SOURCE` under
  the accepted L0 package.

### L1-WP3 — relationships, vargas, clocks and sensitivity

- Retain typed aspect/conjunction/exchange/dispositor/argalā and related
  primitives with actor/target roles, method/orb, constituent facts and ancestry.
  Emit no structural meaning, causation or independent-support count.
- Preserve varga formula/domain/own-lagna house/degree/dignity and D1 ancestry;
  compare relevant input precision and boundary crossings. Do not treat every
  varga as an interchangeable vote.
- Preserve complete daśā parent/child hierarchy, exact ISO interval boundaries,
  applicability, coverage, failure and horizon. Retain Tājaka, Sāḍe-sātī and
  transit-anchor method/frame identities. Never reduce exact producer clocks to
  dates or infer activation/manifestation.
- Treat persisted sign-keyed AV as existing capital; investigate contributor
  prastāra specifically as computed-discarded. Add it only if a named consumer
  distinction and cost/compatibility proof justify the payload.

### L1-WP4 — specialized and restricted capital

- Birth Pañcāṅga remains distinct from arbitrary-day/place service, Praśna
  question-moment and Muhūrta interval.
- Preserve R-1: `ga_prashna` remains dormant and legitimate natal zero-output
  does not become missing data. Do not open endpoints or build method breadth.
- `ga_medical` stays traditional, attributed and non-diagnostic;
  `ga_ayurdaya` stays scholarly/restricted with no individualized mortality or
  lifespan delivery; `ga_vastu` is not a complete spatial assessment.
- Preserve honest approximation, unsupported prerequisites and explicit
  omissions. Do not improve a safety boundary into an activation path.

### L1-WP5 — first producer slice

Implement `L1-SLICE-RESOURCE-CONFIG-01` exactly as frozen in L1 strategy §7.
Use only deterministic synthetic non-person fixtures. Pin the exact fixture
inputs and expected producer outputs before implementation. The bundle must
carry accepted L0 release/package digests, complete calculation context, stable
facts, decomposed conditions, varga/sensitivity result, configuration state
schema and generation/correction metadata.

The L0 Bhāvat package remains present but unapplied at
`UNQUALIFIED_SOURCE`. A positive doctrinal arm is `NOT_REACHABLE` unless WP0
finds an already-admitted L0 dossier satisfying the accepted qualification
contract; execution may not create or admit one. Engineering fixtures may prove
the state machine but must remain typed as engineering evidence.

### L1-WP6 — compatibility, field manifest and proof

- Complete 19/19 component dispositions and the exact upstream-demand/
  downstream-offer matrix.
- Publish a compatible-generation, dependency/cascade, stale-before-use,
  correction, cache, replay and rollback contract. Preserve prior compatible
  facts and historical delivered artifacts.
- Publish producer capability/field/gap metadata for later DP10-DP12 integration,
  without editing the registry or claiming serving.
- Regenerate deterministic writer digests when required. Do not edit the
  protected layer-pin file or invent a future convergence commit; record that
  protected-delivery step as unreached.

### L1-WP7 — validation, independent challenge and handoff

- Execute qualification, computation, relevant/irrelevant perturbation,
  shared-root/duplication, missingness, wrong-context/generation, precision/
  boundary, clock hierarchy, specialized-safety, revision/replay/rollback and
  first-slice tests.
- Run proportionate broad L1 suites and reproduce any inherited failures against
  the accepted base before classifying them. Unavailable DB/service proof is
  `NOT_RUN`, never green.
- Obtain independent read-only challenge of all 19 dispositions, every changed
  file, first-slice semantics, frozen-boundary compliance and terminal claims.
  Correct all owned HIGH/CRITICAL and any material producer-readiness finding.
- Update the execution ledger, locally commit the bounded result, return the
  terminal packet to Strategy, call `update_goal(complete)` only if true, and
  stop with L2 waiting.

## 7. Mandatory deliverables

Use the existing Nirmāṇa brief/evidence hierarchy; do not create a rival
registry. At minimum return:

1. L1 current-state/evidence record and complete 19-writer plus adjacent-capital
   disposition register;
2. L1 calculation-context, stable fact and configuration producer contract;
3. L1 condition, relation, varga, clock, sensitivity and epistemic contract;
4. `L1-SLICE-RESOURCE-CONFIG-01` versioned package and non-person fixtures;
5. compatible-generation, correction/cascade/invalidation/cache/replay/rollback
   record;
6. executed validation and independent-review record; and
7. L1 producer-ready acceptance/handoff with exact commits, tests, residuals,
   cost and terminal truth matrix.

Reuse and version adequate artifacts rather than duplicating authorities. A
documented schema without implementation/negative proof is not producer ready.

## 8. Acceptance tests and terminal truth

Acceptance requires:

- generated/source census remains exactly 19 writers and no formal L1 nonwriter;
- every writer and adjacent service/projection has current evidence and a fixed
  component disposition;
- L0 semantic/configuration pins are verified and no L0 meaning changed;
- every material L1 fact has exact context/grain/unit/epistemic/generation and
  honest failure/missingness;
- configurations cannot be positively qualified from an unqualified source;
- relevant input changes declared outputs, irrelevant input/order/alias does not,
  and shared-root duplication cannot inflate evidence;
- wrong subject/chart/build/context/varga/generation joins fail closed;
- timestamps, clock hierarchies and sensitivity survive at producer precision;
- numerical failure cannot become a normal zero/empty/Aries fallback;
- restricted/dormant/excluded capital remains restricted;
- deterministic replay and rollback preserve the prior compatible generation;
- focused tests pass; broad and live results retain exact failures/skips/
  `NOT_RUN`; independent review has zero owned HIGH/CRITICAL; and
- no protected or prohibited surface changed.

Report states separately:

| State | Required final truth |
|---|---|
| `STRATEGY_AGREED` | YES — DP-SD-013 and immutable brief pin |
| `PRODUCER_READY` | YES only if every criterion above is evidenced |
| `INTEGRATED` | NO — L2/retrieval/managed consumers unmodified |
| `DEPLOYED_OPERATIONALLY_ACCEPTED` | NO — no protected delivery/live mutation |
| `CONSUMER_VALUE_DEMONSTRATED` | NO — producer fixture is not user evidence |
| `EMPIRICALLY_EVALUATED` | NO — no eligible outcomes/evaluation |

## 9. Final return packet

Return in one self-contained message:

- branch, execution base, strategy content/metadata pins and terminal commit;
- exact changed files/tables/categories/interfaces and preserved kernels;
- 19/19 disposition summary and adjacent-service resolution;
- first-slice release/generation/digest, fixture IDs and L0 pins;
- commands, exits, pass/fail/skip/`NOT_RUN`, negative controls and independent
  review verdict;
- inherited failures and unresolved strategic decisions;
- compatibility/cascade/rollback and any unreached protected-delivery step;
- confirmation of zero L2, campaign, private-data, push/PR/merge/deploy or
  production mutation; and
- terminal state matrix plus `L2 remains WAITING_FOR_STRATEGIC_BRIEF`.

Only after that packet is truthful may the task mark the L1 goal complete.
