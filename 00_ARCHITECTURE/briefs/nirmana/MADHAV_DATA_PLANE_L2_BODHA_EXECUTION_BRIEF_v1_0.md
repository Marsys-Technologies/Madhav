---
artifact: MADHAV_DATA_PLANE_L2_BODHA_EXECUTION_BRIEF
version: "1.0"
status: APPROVED_FOR_EXECUTION
approved_on: 2026-09-14
strategy_decision: DP-SD-015
strategic_parent_task: "Strategy — Data Plane / 01a0996e-6ca0-7642-ac31-f968fee214b3"
execution_task: "Execution — Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
approval_record: "DP-SD-015 at strategy content commit 86374d65f3dc742085783e352a9999e2edb48715"
product_authority: "MADHAV_PRODUCT_DEFINITION v3.0 / CCD-010"
strategy_version: "MADHAV_DATA_PLANE_VALUE_ARCHITECTURE v2.0 amended by DP-SD-009, accepted L0 DP-SD-012, accepted L1 DP-SD-014 and MADHAV_DATA_PLANE_L2_BODHA_STRATEGY v1.0 / DP-SD-015"
layer: "L2 Bodha"
goal_objective: "Elevate L2 Bodha to verified PRODUCER_READY status under Product Definition v3.0, DP-SD-009, DP-SD-012, DP-SD-014, DP-SD-015 and the Data Plane Execution Foundation: consume the accepted L0 release at f6fed12c794224329f6b3b436f8b1b814499d06d and accepted L1 terminal at 18503e9c2dbb140f5d17b4bc34a5f6d087f97c38 without changing, contradicting or locally re-deriving their authority; reconcile and disposition all 23 current bo_* writer identities, including supporting bo_grounding while preserving the historical formal L2 campaign denominator of 22, plus every adjacent engine, helper, store, historical service and read-only projection that determines or materially projects Bodha output; establish compatible structural-context, proposition/configuration, signed-relationship, multidomain-mechanism, occurrence/condition/cancellation, contradiction/rival, evidence-independence, epistemic/grounding, discovery/investigator, practice-eligibility, generation and correction contracts; remove L3/Kala runtime dependencies and resolved activation-window semantics from new L2 producer generations while preserving legacy schema/history and non-interpreted L1 clock references; preserve viable kernels, identities, provenance, history, interfaces, WriterBase/idempotency and safety boundaries; implement only evidence-justified L2 and direct producer-adapter deltas in dependency order; prove L2-SLICE-RESOURCE-MECHANISM-01 with deterministic non-person fixtures, complete signed/multidomain evidence, honest unqualified/not-reachable states and no requirement to fabricate a positive qualified doctrine case; and return terminal evidence without beginning L3, reopening the historical campaign, changing L0/L1/product/safety/source-rights authority, or claiming integration, deployment, consumer value, timing, manifestation, causation or empirical performance not actually proved."
source_revision: 18503e9c2dbb140f5d17b4bc34a5f6d087f97c38
accepted_upstream_contracts:
  - "MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES/1.0/blob-2fda304d627183b380e36ee1e817e08a8391119c@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_LAYER_EXECUTION_BRIEF_CONTRACT/1.0/blob-2ea6becdcff6232921bb3ad1521db2ecfc01f3a7@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT/1.0/blob-71ff974ec92d03dbe755a53cd1d1f6b189543f07@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_L0_PRODUCER_READY_ACCEPTANCE/1.0/blob-2ff60068c8b578a269c7962b37b23822e356b211@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_L0_RESOURCE_CONFIG_SLICE/1.0/blob-9fe6787bb63b71c54a239ee4992c3c1c8b33bfa4@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_L1_PRODUCER_READY_ACCEPTANCE/1.0/blob-cfbd4d6e2292a414b1d691630ecf002aa6ebbbd8@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_L1_CURRENT_STATE_AND_DISPOSITION/1.0/blob-99a527374172f3f4cc1dd844859f549611201eb3@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_L1_CONTEXT_FACT_CONFIGURATION_CONTRACT/1.0/blob-bf6946ca07dcfb69183d59e528f92e045880acc2@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_L1_CONDITION_RELATION_CLOCK_CONTRACT/1.0/blob-99953b54749a794efee48760d718e387bc8743e2@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_L1_RESOURCE_CONFIG_SLICE/1.0/blob-c38b299a3d5e58b09209a2b36aa78923bee21420@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_L1_COMPATIBILITY_CORRECTION_ROLLBACK/1.0/blob-725e24ad03b17fdee35f0619cdb2fcc5318e7ce3@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
  - "MADHAV_DATA_PLANE_L1_VALIDATION_AND_REVIEW_RECORD/1.0/blob-8fc903bf3b8caa43e7cc53f15aa4349e2af1efe4@18503e9c2dbb140f5d17b4bc34a5f6d087f97c38"
owners:
  implementation: "Execution — Data Plane / one primary writer with bounded non-overlapping helper lanes only if the execution skill permits"
  review: "independent read-only reviewer, separate from implementation"
  release: "Strategy — Data Plane under native product-owner authority"
may_touch:
  - "platform/python-sidecar/bodha_writers/**"
  - "platform/python-sidecar/pipeline/orchestrator/writers/bo_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_bo_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bo_*.py"
  - "platform/python-sidecar/tests/l2/**"
  - "platform/python-sidecar/tests/test_bo_*.py"
  - "platform/python-sidecar/tests/test_l2_*.py"
  - "platform/python-sidecar/scripts/validate_data_plane_l2_*.py"
  - "platform/src/generated/nirmana-writer-digests.json"
  - "platform/supabase/migrations/*_data_plane_l2_*.sql"
  - "platform/migrations/*_data_plane_l2_*.sql"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_CURRENT_STATE_AND_DISPOSITION_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_STRUCTURAL_PROPOSITION_AND_RELATION_CONTRACT_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_MECHANISM_CONTRADICTION_INVESTIGATOR_CONTRACT_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_RESOURCE_MECHANISM_SLICE_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_COMPATIBILITY_CORRECTION_ROLLBACK_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_VALIDATION_AND_REVIEW_RECORD_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_PRODUCER_READY_ACCEPTANCE_v*.md"
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
  - "00_ARCHITECTURE/L2_BODHA_CAMPAIGN_HANDOFF_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_BODHA_STRATEGY_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L2_BODHA_EXECUTION_BRIEF_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L1_*.md"
  - "00_ARCHITECTURE/briefs/nirmana/sessions/**"
  - "platform/python-sidecar/brahmagyan/**"
  - "platform/python-sidecar/ga_writers/**"
  - "platform/python-sidecar/pipeline/orchestrator/base.py"
  - "platform/python-sidecar/pipeline/orchestrator/runner.py"
  - "platform/python-sidecar/pipeline/orchestrator/asset_runner.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/bg_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ka_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ph_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/mi_*.py"
  - "platform/src/lib/retrieval/**"
  - "platform/src/lib/pariprashna/**"
  - "platform/src/lib/synthesis/**"
  - "platform/src/lib/mcp/**"
  - "platform-mcp/**"
  - "platform/src/generated/nirmana-analysis-layer-pins.json"
  - ".github/workflows/**"
  - "**/*credential*"
  - "**/*secret*"
activation_prohibitions:
  - "push, PR, merge, merge queue, deploy, production mutation, live migration or destructive rebuild"
  - "active Nirmāṇa campaign definition, event, registry, lease, queue, freeze or historical-receipt mutation"
  - "L0/L1 semantic or data change; L3-L5 implementation; retrieval/Paripraśna/synthesis/MCP cutover"
  - "private-row inspection, stored personal chart use, life-observation/cohort/claim/evaluation activation"
  - "medical diagnosis, individualized mortality/lifespan output, remedy-efficacy/prescription or Vāstu-service expansion"
  - "Product Definition, CCD, canonical manifest, consent, safety or source-rights expansion"
  - "temporal activation, manifestation, causation, future convergence-pin fabrication, model/feature admission or empirical-performance claim"
strategy_parent: MADHAV_DATA_PLANE_L2_BODHA_STRATEGY_v1_0.md
execution_task_id: 01a0998a-8240-7631-97ce-36c6d4734fde
execution_branch: codex/madhav-data-plane-execution
execution_base: 18503e9c2dbb140f5d17b4bc34a5f6d087f97c38
delivery_target: PRODUCER_READY
next_stage_hold: "L3 remains WAITING_FOR_STRATEGIC_BRIEF."
changelog:
  - "1.0: Authorizes one bounded autonomous L2 Bodha producer-ready execution across all 23 current writers including supporting bo_grounding, with exact accepted-L0/L1 pins, complete signed/multidomain structural contracts, first slice, evidence and stop conditions."
---

# Execution brief — L2 Bodha producer readiness

## 1. Strategic authority and outcome

Execute `DP-SD-015` and the paired L2 strategy against exact accepted L1
terminal revision `18503e9c2`. Produce a versioned, reproducible and
challengeable Bodha producer contract across all 23 current writer identities,
with exact upstream context, stable structural identity, signed relationships,
complete domains, occurrence/condition/cancellation ledgers, contradictions,
alternatives, evidence-dependence, epistemic grounding, discovery/investigator
metadata, compatible generations and honest failure semantics.

Preserve the historical 22/22 formal Nirmāṇa receipt as bounded evidence. Do not
reopen or replay that campaign or treat current rows, `lit`, a generated pin or a
prior production build as present data-plane acceptance. End at
`PRODUCER_READY`; do not begin L3 or consumer integration.

## 2. Set the new bounded goal

Before substantive execution, call `create_goal` once, without a token budget,
using exactly the `goal_objective` in this brief's header. The completed L1 goal
must not be reused or silently reopened.

Mark the new goal complete only after every L2 producer-ready exit gate is
satisfied. A real blocker is returned under the goal rules with the smallest
missing Strategy decision. Routine uncertainty, implementation choice, tests and
safe reversible corrections are resolved autonomously from pinned evidence and
governing precedent.

## 3. Mandatory entry gate

Before mutation:

1. verify the permanent execution task is in its isolated worktree on
   `codex/madhav-data-plane-execution`, clean at exact commit `18503e9c2`;
2. verify the injected profile is Full Access/unrestricted with approval policy
   `never`; if the actual host profile is managed/on-request, do not start and
   return `HOST_PERMISSION_PROFILE_BLOCKER` to Strategy;
3. read `AGENTS.md`, `CLAUDE.md` and its complete mandatory sequence, then the
   `layer-value-elevation` and `autonomous-asset-elevation` skills and all
   references those skills require for execution;
4. verify every accepted upstream blob/revision pin in this header and read the
   exact L2 strategy plus this approved brief from their pinned commits;
5. cherry-pick only the exact Strategy content and approval-pin commits named in
   the kickoff prompt; resolve only mechanical overlap and return any substantive
   authority conflict;
6. remeasure Git state, 23-writer source census, historical formal denominator,
   output schemas/natural keys, actual DAG, tests, generated digests, current
   source-qualified semantics and read-only consumer demand; and
7. freeze a narrowed exact mutation manifest before the first edit.

Historical counts, current production rows, prior W1/W2 findings and closures
are leads. Classify each as current, fixed, superseded, unavailable or unresolved
at the exact execution base before relying on it.

## 4. Autonomous operating contract

Proceed fully autonomously inside the fixed scope. Do not ask for routine
approvals, permission escalation, implementation preferences, test choices,
continuation or status confirmation. Use reversible local actions and make
evidence-backed decisions in the accepted DAG order. Maintain durable resumable
state in the existing execution ledger, not a new campaign runtime.

Keep one primary implementation writer. Bounded helper lanes may perform
non-overlapping analysis/tests only when the execution skill proves file/table
ownership and useful independence. Builders do not certify themselves; obtain a
fresh read-only independent challenge before terminal acceptance.

Authorized:

- read-only repository/Git/source/schema/current-consumer tracing and
  proportionate aggregate runtime/database inspection available without private
  rows or mutation;
- local L2 producer, direct producer-adapter, deterministic fixture, validation,
  forward-only schema and producer-contract work inside `may_touch`;
- exact read-only tracing of L3/retrieval/Paripraśna/synthesis/MCP consumers to
  establish requirements and field loss;
- local commits on `codex/madhav-data-plane-execution`;
- deterministic writer-digest regeneration, without inventing a protected
  convergence commit; and
- correction of every in-scope independent-review finding material to producer
  readiness.

Not authorized:

- push, PR, merge/queue, deploy, production/data mutation, live migration,
  destructive rebuild, campaign event/lease/freeze/receipt mutation;
- L0/L1 semantic/data edits, L3-L5 implementation or any temporal/
  manifestation/evaluation output;
- retrieval/query/ranking, Paripraśna, synthesis, MCP, managed delivery,
  replay/export or UI cutover;
- private chart/observation use, dormant/restricted service activation,
  product/safety/consent/source-rights adoption, feature/model admission or
  empirical/causal claim;
- changes to frozen WriterBase/orchestrator/transaction boundaries; or
- modification of the protected layer-pin file or historical campaign records.

Stop only for a real product/adoption, doctrine/source-rights, safety/privacy,
credential, irreversible/destructive, protected-delivery, permission-profile,
frozen-orchestrator or irreconcilable governance gate. Quarantine its dependency
cone and continue every independent eligible packet. Missing live credentials
make the corresponding proof `NOT_RUN` unless the brief explicitly makes live
proof an entry requirement.

## 5. Fixed inventory and mutation boundary

The data-plane denominator is exactly these 23 current writer identities:

`bo_laksana`, `bo_laksana_rerank`, `bo_bimba`, `bo_karanajala`,
`bo_cgm_paths`, `bo_cgm_motifs`, `bo_yantra_mechanism`, `bo_sangati`,
`bo_cdlm_summary`, `bo_pratijna`, `bo_arudha`, `bo_special_lagna`,
`bo_sudarshana`, `bo_vargottama_dhana`, `bo_nakshatra_semantic`, `bo_upaya`,
`bo_samskara`, `bo_anveshana`, `bo_drishti`, `bo_chart_gestalt`, `bo_samvada`,
`bo_pramana_mapa` and supporting `bo_grounding`.

The historical formal campaign denominator remains 22 because `bo_grounding`
is support outside its frozen definition. Record both numbers and never convert
the current 23-writer producer review into a rewritten campaign receipt.

The header's `may_touch` list is the immutable outer boundary. L2-WP0 narrows it
to exact files, stores, natural keys, migrations and tests. A new path class,
upstream edit, L3/consumer edit, orchestrator edit, protected-pin update,
campaign mutation or activation decision returns to Strategy.

Existing migrations are immutable. A new migration must match an approved
`*_data_plane_l2_*.sql` glob and is created only when the accepted contract
cannot fit the current schema. It must be forward-compatible, ordered,
idempotent on reapplication where applicable and locally proven with rollback/
read compatibility. Never apply it live in this goal.

Shared tables remain partitioned by exact writer and natural-key ownership. Do
not rewrite another asset's rows or fabricate pre-migration history. Preserve
caller-owned transactions, no writer commit/close/throughput writes, resumable
substeps and current L1+ delete-then-insert semantics unless an accepted
append-only history envelope wraps them without changing active interfaces.

## 6. Required work packets

### L2-WP0 — stocktake, denominator, DAG and consumer backcast

- Reconcile 23/23 current writer identities to implementation files, actual
  imports/SQL reads, declared and real dependencies, output stores/natural keys,
  epistemic type, current consumers, generated digests and historical receipts.
- Build a separate adjacent-authority register covering every non-registered
  engine/helper/projection that can determine or materially project L2 output:
  `bodha_writers` formulas/idempotency/emitters/Bhāvat/grounding helpers,
  `bo_pratijna_v4_engine.py`, `bo_pratijna_karyatva.py`, retained `bo_2-*`
  services, physical stores/specs/history, read-only retrieval/answer projections,
  local Bhāvat maps and every imported L3 helper. Record path, role, authority,
  mutation/read-only status, callers/consumers and exact disposition without
  adding any of them to the 23-writer denominator.
- Preserve and explain the 23 operational versus 22 formal denominator split.
- Audit the DAG in two passes: prove a cycle-free first frontier, then close every
  hard/semantic/optional/validation edge before producer acceptance. Record the
  exact consumed field/contract, not only an upstream asset name.
- Trace L1 inputs and L3/retrieval/inquiry consumers read-only for local
  re-derivation, first-domain selection, unsigned flattening, cancelled-edge
  deletion, condition-polarity reversal, legacy-grade takeover, date/temporal
  contamination, top-K loss, summary-only use and shared-root duplication.
- Recheck historical W1/W2 findings rather than replaying them blindly,
  including current Bhāvat code, cancellation reasons, domain polarity,
  `bo_pratijna` axes, mechanism verification, grounding, low-salience candidates,
  quality detectors and generation/freshness semantics.
- Treat the current `bo_karanajala` import of `services.ka_temporal` and its
  computed `active_dasha_periods_jsonb` as a live boundary violation to close:
  remove the L3 runtime dependency and stop producing activation windows in new
  L2 generations without editing L3. Preserve legacy columns/history for read
  compatibility and expose exact L1 clock references only as non-interpreted
  upstream evidence. Audit every other L2 producer for the same inversion.
- Separate `present`, `populated`, `qualified`, `consumed`, `effect_traced`,
  `served` and `value_evaluated`; record observation time and evidence gaps.
- Produce the exact mutation manifest, preserved-kernel map, dependency vector,
  baseline/digest and 23 per-asset elevation records before mutation.

### L2-WP1 — accepted-upstream and structural-context contract

- Bind every material L2 row to the accepted L0 release and exact compatible L1
  context, build/generation, fact/configuration IDs, units, epistemic class,
  verification and missingness. Reject mixed-latest or wrong subject/chart/
  ayanāṃśa/frame/varga/generation joins.
- L1 facts win. A Bodha row references and hydrates them; any conflicting
  restatement fails the partition instead of being stored as divergence.
- Define stable proposition, configuration, relationship, contradiction and
  mechanism identities independent of transient build/time metadata, with an
  observation generation around them.
- Preserve explicit states: present, zero, unavailable, floored, inapplicable,
  unqualified source, failed and unexplored. Every status/verification claim
  needs a detector capable of returning false.

### L2-WP2 — propositions, occurrence, condition and cancellation

- Elevate `bo_laksana`, `bo_laksana_rerank` and applicable satellite emitters to
  one typed structural-proposition contract rather than multiple votes.
- Require exact admitted rule/method, all participants and roles, satisfied/
  failed clauses, exceptions, cancellation and original L1 evidence.
- Preserve formation state separately from structural meaning. A catalog match,
  label or observed firing under an unqualified rule remains unqualified.
- Preserve occurrence and condition as separate ledgers. Validate field units
  and polarity, especially `bo_pratijna`'s occurrence `[0,1]` and condition
  affliction `[0,10]`; legacy grades remain compatibility projections only.
- Cancellation identifies its target and original sign. Cancelling inhibition,
  cancelling support and relief from debility must produce different structural
  states; none automatically yields a stronger yoga or promised outcome.
- Keep Bhāvat Bhāvam `UNQUALIFIED_SOURCE` with positive doctrinal arm
  `NOT_REACHABLE`; engineering-only fixtures cannot promote it. Producer
  readiness is valid with zero positive qualified doctrinal propositions when
  the accepted L0 release contains none.

### L2-WP3 — graph, signed paths and mechanisms

- Elevate `bo_bimba`, `bo_karanajala`, `bo_cgm_paths`, `bo_cgm_motifs` and
  `bo_yantra_mechanism` to stable typed node/edge/path/mechanism contracts.
- Every relationship carries actor, relation, target, original polarity,
  magnitude semantics, basis, direct/transitive/candidate class, configuration
  membership, exact roots and cancellation detail where available.
- Do not convert opposition to nonnegative conductance, discard a cancelled
  edge, take the first source fact, infer causal direction from alphabetical
  order or treat topology/centrality as a temporal gate.
- Paths and motifs retain ordered edges and shared-root groups. A mechanism is
  admitted only by a qualified structural rule/contract; otherwise it remains a
  discovery candidate. Replace unearned fixed verification with a detector or
  null.

### L2-WP4 — multidomain structure, contradictions and alternatives

- Elevate `bo_sangati`, `bo_cdlm_summary` and `bo_pratijna` to retain every
  material domain, the semantic role of each domain, paired positive/negative
  drivers, supporting/opposing paths, contradictions and unresolved rivals.
- Domain array order, display aliases and summary direction cannot change
  meaning. Preserve both sides of a pair and hydrate underlying signals.
- Qualify any doṣa-class proxy before using it as negative evidence; a
  navigation statistic does not become causal direction or independent support.
- Preserve full evidence for compatible tensions, genuine contradictions,
  disputed methods and missing discriminators. Never force a winner merely to
  populate a gestalt or downstream promise.

### L2-WP5 — reference frames and specialized structural capital

- Qualify `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`,
  `bo_vargottama_dhana` and `bo_nakshatra_semantic` as method-specific
  perspectives with exact L1 roots, formula/reference frame, domain roles,
  limits and shared-dependence groups.
- Do not count correlated Lagna/Moon/Sun views, repeated varga facts or
  restated nakshatra/dispositor evidence as independent witnesses.
- Preserve current valid kernels; correct only measured semantic loss,
  misleading fixed modifiers, missing scope or false verification.
- `bo_upaya` emits attributed practice eligibility, source, target,
  constraints, contraindications and unknowns only. No efficacy, prescription,
  timing, clinical claim or guaranteed relief is permitted.

### L2-WP6 — grounding, discovery, investigator and quality projections

- `bo_grounding` must bind a proposition to the exact available source/rule,
  qualification, target class and citation granularity. Empty/unavailable source
  evidence stays honest; corpus abundance is not corroboration or truth.
- `bo_samskara` remains versioned content-addressed navigation. Reuse may be
  optimized only after profiling and output-equivalence proof; similarity is not
  evidence, verification or confidence.
- `bo_anveshana` emits typed candidates with detector reason and evidence
  pointers. Preserve uncommon/low-ranked high-consequence candidates; do not
  promote anomaly, broker or embedding-outlier scores into findings.
- `bo_drishti`, `bo_chart_gestalt` and `bo_samvada` expose question obligations,
  whole-chart pointers, contradictions, rival routes, missing sections and
  hydration requirements. They must not pre-answer, replace the underlying
  graph, hide a decisive second domain or use query time as build freshness.
- `bo_pramana_mapa` implements exact reachable detectors for orphan references,
  context/generation consistency, domain/ledger completeness, sign/polarity,
  shared-root duplication and producer integrity. Each result states its scope;
  a constant green flag is a failure.
- Publish producer-side capability/field/gap metadata for later DP10-DP12
  integration without editing retrieval, planner, MCP or managed channels.

### L2-WP7 — first producer slice

Implement `L2-SLICE-RESOURCE-MECHANISM-01` exactly as frozen in L2 strategy §7.
Use only deterministic synthetic non-person fixtures. Pin fixture inputs and
expected outputs before implementation.

The slice consumes accepted L1 fixture digest
`25c46b559def7e1a9f8e1a05114be5a6c306a846a23b2665b1b5c917128d3279`
and must carry all upstream pins, structural IDs, full participants/domains,
separate occurrence/condition ledgers, signed support/opposition, shared-root
groups, cancellation target/polarity, contradictions/rivals, grounding,
missingness and discovery/hydration pointers.

Run the relevant-condition, cancellation-polarity, irrelevant-input,
domain-order, duplicate-root, unrelated-configuration, low-rank second-domain,
wrong-context/generation and unqualified-source controls from Strategy §7.
Record a deterministic content digest. The Bhāvat positive doctrinal arm remains
unreachable unless an already-admitted accepted-L0 dossier is found; execution
may not create one. Exercise positive/negative/partial/cancellation machinery
with an explicit `ENGINEERING_ONLY` fixture that cannot be promoted. Zero
qualified positive doctrinal rows is an honest passing result when accepted L0
has no qualified executable rule; an already-admitted qualified control is
optional and must carry its exact L0 pin.

### L2-WP8 — generations, validation, challenge and handoff

- Implement compatible dependency-set selection, exact stale propagation,
  deterministic replay, idempotent current-state rebuild, retained prior
  structural generations, head selection and rollback without rewriting
  historical delivered evidence.
- A semantic L0/L1/context/rule change rotates or invalidates only its proven
  dependent closure. Row order, aliases, reranking and display changes cannot
  silently change structural identity.
- Regenerate deterministic writer digests only if required. Do not edit the
  protected layer pin or invent a future merge/convergence SHA.
- Run focused contracts plus proportionate broad Bodha suites. Reproduce any
  inherited failure against the accepted base before classifying it. Unavailable
  live DB/service proof is `NOT_RUN`, not green.
- Obtain independent read-only challenge of all 23 dispositions, the 22/23
  denominator distinction, every changed file, DAG, first slice, upstream pins,
  sign/polarity/dependence semantics, safety boundaries and terminal claims.
- Correct every owned material producer-readiness finding, update the execution
  ledger, commit the bounded result locally, send the exact packet to Strategy,
  call `update_goal(complete)` only when true and stop with L3 waiting.

## 7. Mandatory deliverables

At minimum return:

1. L2 current-state/evidence record and complete 23-writer disposition register,
   explicitly reconciling the historical formal denominator of 22;
2. L2 structural-context, proposition, configuration, cancellation, signed-
   relationship and evidence-dependence producer contract;
3. L2 mechanism, multidomain, contradiction/rival, grounding, discovery,
   investigator, practice-eligibility and quality-detector contract;
4. `L2-SLICE-RESOURCE-MECHANISM-01` package, version and non-person fixtures;
5. compatible-generation, dependency/cascade, stale-before-use, correction,
   cache, replay and rollback record;
6. executed validation and independent-review record; and
7. L2 producer-ready acceptance/handoff with exact commits, tests, residuals,
   cost and terminal truth matrix.

Reuse and version adequate artifacts instead of creating rival registries. A
schema or prose contract without actual runtime adoption and negative proof is
not producer ready.

## 8. Acceptance tests and terminal truth

Acceptance requires:

- generated/source census is exactly 23 current `bo_*` writers, with the
  historical campaign's 22 formal receipt denominator preserved and explained;
- every writer has current evidence, exact ownership and a terminal component
  disposition; no hidden hard DAG edge or write collision remains;
- exact accepted L0/L1 blobs, contexts, generations and stable IDs are verified;
- no L2 row contradicts or re-derives an L1 authoritative value;
- no L2 producer imports an L3/Kāla engine or emits resolved activation windows
  as new L2 truth; legacy temporal fields/history remain explicitly compatible
  but unavailable/non-authoritative for the new contract;
- every material proposition retains all participants, domains, rule/method,
  occurrence/condition/cancellation ledgers, signed paths, roots, epistemics,
  missingness and alternatives required by its contract;
- relevant condition/cancellation changes only the declared structural result;
  reversing cancellation target polarity yields a different result;
- domain/alias/order changes are invariant and a decisive second-domain/
  low-ranked item cannot disappear from the producer package;
- duplicate wrappers, totals/components, repeated sources and graph paths sharing
  roots do not inflate independent support;
- wrong subject/chart/context/ayanāṃśa/varga/generation and unqualified rules
  fail closed;
- candidate, navigation, grounding and quality flags cannot self-promote without
  executable detectors and exact evidence;
- Bhāvat Bhāvam remains honestly unqualified and no temporal, manifestation,
  remedial-efficacy, causal or empirical authority is introduced;
- zero qualified positive doctrinal propositions remains a valid result when
  the accepted L0 release contains none; engineering fixtures remain visibly
  non-doctrinal and non-promotable;
- deterministic replay, idempotency, compatibility, stale propagation and
  rollback preserve the prior qualified generation;
- focused tests pass; broad and live results retain exact failures/skips/
  `NOT_RUN`; independent review has zero owned material findings; and
- no protected or prohibited surface changed.

Report states separately:

| State | Required final truth |
|---|---|
| `STRATEGY_AGREED` | YES — DP-SD-015 and immutable brief pin |
| `PRODUCER_READY` | YES only if every criterion above is evidenced |
| `INTEGRATED` | NO — L3/retrieval/managed consumers unmodified |
| `DEPLOYED_OPERATIONALLY_ACCEPTED` | NO — no protected delivery/live mutation |
| `CONSUMER_VALUE_DEMONSTRATED` | NO — producer fixture is not user evidence |
| `EMPIRICALLY_EVALUATED` | NO — no eligible outcomes/evaluation |

## 9. Final return packet

Return in one self-contained message:

- branch, execution base, strategy content/approval pins and terminal commit;
- exact changed files/tables/natural keys/interfaces and preserved kernels;
- 23/23 disposition summary plus explicit 22-formal/23-operational accounting;
- first-slice generation/content digest, fixture IDs and exact L0/L1 pins;
- commands, exits, pass/fail/skip/`NOT_RUN`, negative controls and independent
  review verdict;
- inherited failures, current/superseded historical findings and unresolved
  strategic decisions;
- DAG, compatibility/cascade/rollback and unreached protected-delivery steps;
- confirmation of zero L0/L1/L3+, campaign, private-data, retrieval, push/PR/
  merge/deploy or production mutation; and
- terminal state matrix plus `L3 remains WAITING_FOR_STRATEGIC_BRIEF`.

Only after that packet is truthful may the task mark the L2 goal complete.
