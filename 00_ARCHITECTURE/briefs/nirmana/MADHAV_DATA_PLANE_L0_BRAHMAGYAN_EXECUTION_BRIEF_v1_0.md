---
artifact: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_EXECUTION_BRIEF
version: "1.0"
status: APPROVED_FOR_EXECUTION
approved_on: 2026-09-13
strategy_decision: DP-SD-009
strategic_parent_task: "Strategy — Data Plane / 01a0996e-6ca0-7642-ac31-f968fee214b3"
execution_task: "Execution — Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
approval_record: "DP-SD-009 at strategy content commit cfe16cdac6d550499a2ecc7f762b57e3f3779da9"
product_authority: "MADHAV_PRODUCT_DEFINITION v3.0 / CCD-010"
strategy_version: "MADHAV_DATA_PLANE_VALUE_ARCHITECTURE v2.0 amended by DP-SD-009 and MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY v1.0"
layer: "L0 Brahmagyan"
goal_objective: "Elevate L0 Brahmagyan to verified PRODUCER_READY status under Product Definition v3.0, DP-SD-009 and the Data Plane Execution Foundation: reconcile and disposition all 36 L0 writers and four L0 non-writers; resolve the approved identity, semantic-release, source-witness, rule-qualification, convention, service-context, discovery and correction contracts; preserve viable code, data, sources, identities, history and interfaces; implement only evidence-justified L0 and direct-adapter deltas in dependency order; prove the L0-SLICE-RESOURCE-CONFIG-01 producer package and all applicable F01-F28/DP01-DP18 obligations; and return terminal evidence without beginning L1, expanding safety or source-rights authority, changing product adoption, or claiming integration, deployment, consumer value or empirical performance not actually proved."
source_revision: d838af45524369e804ca17ac63331237b6b8e100
accepted_upstream_contracts:
  - "MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES/1.0/blob-2fda304d627183b380e36ee1e817e08a8391119c@d838af45524369e804ca17ac63331237b6b8e100"
  - "MADHAV_DATA_PLANE_INVENTORY_EVIDENCE_BASELINE/1.0/blob-a3297572dc4422d58bc1e74498860e2cc4a70a9d@d838af45524369e804ca17ac63331237b6b8e100"
  - "MADHAV_DATA_PLANE_LAYER_EXECUTION_BRIEF_CONTRACT/1.0/blob-2ea6becdcff6232921bb3ad1521db2ecfc01f3a7@d838af45524369e804ca17ac63331237b6b8e100"
  - "MADHAV_DATA_PLANE_ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT/1.0/blob-71ff974ec92d03dbe755a53cd1d1f6b189543f07@d838af45524369e804ca17ac63331237b6b8e100"
  - "MADHAV_DATA_PLANE_FOUNDATION_ACCEPTANCE_RECORD/1.0/blob-f06996142e95eebc482cdd328ddaedcac87118ca@d838af45524369e804ca17ac63331237b6b8e100"
  - "MADHAV_DATA_PLANE_EXECUTION_LEDGER/1.0/blob-665ccea47e1fe1e02414c72d04bc09b290d86ab2@d838af45524369e804ca17ac63331237b6b8e100"
owners:
  implementation: "Execution — Data Plane / one writer"
  review: "independent read-only reviewer, separate from implementation"
  release: "Strategy — Data Plane under native product-owner authority"
may_touch:
  - "platform/python-sidecar/pipeline/orchestrator/writers/bg_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_*.py"
  - "platform/python-sidecar/brahmagyan/**"
  - "platform/python-sidecar/pipeline/orchestrator/service_probes.py"
  - "platform/python-sidecar/routers/ephemeris.py"
  - "platform/python-sidecar/routers/panchang.py"
  - "platform/python-sidecar/panchang_engine/**"
  - "platform/python-sidecar/tests/test_l0_*.py"
  - "platform/python-sidecar/tests/test_ephemeris_ayanamsha.py"
  - "platform/python-sidecar/tests/test_panchanga_get.py"
  - "platform/src/lib/retrieval/graha_labels.ts"
  - "platform/src/lib/jyotish/bhavat_bhavam_map.ts"
  - "platform/src/lib/jyotish/__tests__/bhavat_bhavam_map.test.ts"
  - "platform/src/lib/vidhi/registry_data.ts"
  - "platform/src/lib/vidhi/compiler.ts"
  - "platform/src/lib/vidhi/index.ts"
  - "platform/src/lib/retrieval/registry/canonical_faces.json"
  - "platform/src/lib/retrieval/registry/parity_check.ts"
  - "platform/src/lib/retrieval/registry/parity_check.test.ts"
  - "platform/scripts/generate_vidhi_registry_mirror.ts"
  - "platform/scripts/census/check_vidhi_registry_parity.mjs"
  - "platform/scripts/census/dump_vidhi_registry.ts"
  - "platform/scripts/census/__tests__/vidhi_parity_gate.test.ts"
  - "platform/supabase/migrations/*_data_plane_l0_*.sql"
  - "platform/migrations/*_data_plane_l0_*.sql"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_CURRENT_STATE_AND_DISPOSITION_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SEMANTIC_RELEASE_AND_ADAPTER_CONTRACT_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_SOURCE_RULE_QUALIFICATION_CONTRACT_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_CONVENTION_SERVICE_RESTRICTED_CAPITAL_CONTRACT_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_RESOURCE_CONFIG_SLICE_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_COMPATIBILITY_CORRECTION_ROLLBACK_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_VALIDATION_AND_REVIEW_RECORD_v*.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_PRODUCER_READY_ACCEPTANCE_v*.md"
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
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v1_0.md"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_EXECUTION_BRIEF_v1_0.md"
  - "platform/python-sidecar/ga_writers/**"
  - "platform/python-sidecar/bodha_writers/**"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/bo_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ka_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/ph_*.py"
  - "platform/python-sidecar/pipeline/orchestrator/writers/mi_*.py"
  - "platform/src/lib/retrieval/registry/layers/**"
  - "platform/src/lib/pariprashna/**"
  - "platform/src/lib/synthesis/**"
  - "platform/src/lib/mcp/**"
  - ".github/workflows/**"
  - "**/*credential*"
  - "**/*secret*"
activation_prohibitions:
  - "push, PR, merge, merge queue, deploy or production mutation"
  - "L1-L5 implementation or managed/raw consumer integration"
  - "active campaign mutation or historical campaign recertification"
  - "private-row inspection, personal chart use or observation/cohort activation"
  - "Product Definition, CCD, canonical manifest, safety, consent or source-rights expansion"
  - "model/feature admission or empirical-performance claims"
strategy_parent: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v1_0.md
execution_task_id: 01a0998a-8240-7631-97ce-36c6d4734fde
execution_branch: codex/madhav-data-plane-execution
execution_base: d838af45524369e804ca17ac63331237b6b8e100
foundation_contract_commit: d838af45524369e804ca17ac63331237b6b8e100
delivery_target: PRODUCER_READY
next_stage_hold: "L1 remains WAITING_FOR_STRATEGIC_BRIEF."
changelog:
  - "1.0: Authorizes one bounded autonomous L0 Brahmagyan producer-ready execution across the current 36 writers and four non-writers, with explicit scope, contracts, proof and stop conditions."
---

# Execution brief — L0 Brahmagyan producer readiness

## 1. Strategic authority and outcome

DP-P1 is settled by `DP-SD-009`: Data Plane Value Architecture v2.0, amended by
the execution foundation and L0 strategy, is the governing planning basis.
Execute the approved L0 strategy across all 40 current L0 operational identities.

The outcome is a versioned, qualified and testable Brahmagyan producer contract
that supplies shared identity, source, rule, convention, service and discovery
meaning without downstream invention. End at `PRODUCER_READY`; do not begin L1.

## 2. Set the new bounded goal

Before substantive work, call `create_goal` once, without a token budget, using
exactly this objective:

> Elevate L0 Brahmagyan to verified PRODUCER_READY status under Product Definition v3.0, DP-SD-009 and the Data Plane Execution Foundation: reconcile and disposition all 36 L0 writers and four L0 non-writers; resolve the approved identity, semantic-release, source-witness, rule-qualification, convention, service-context, discovery and correction contracts; preserve viable code, data, sources, identities, history and interfaces; implement only evidence-justified L0 and direct-adapter deltas in dependency order; prove the L0-SLICE-RESOURCE-CONFIG-01 producer package and all applicable F01-F28/DP01-DP18 obligations; and return terminal evidence without beginning L1, expanding safety or source-rights authority, changing product adoption, or claiming integration, deployment, consumer value or empirical performance not actually proved.

Do not reuse the completed FOUNDATION goal. Mark this goal complete only when all
L0 exit criteria below are satisfied or return a genuine strategic blocker under
the goal rules.

## 3. Mandatory entry gate

Before mutation:

1. verify the task is in its isolated worktree on
   `codex/madhav-data-plane-execution` at or descended from `d838af455`;
2. verify the injected permission profile is Full Access/unrestricted with
   approval policy `never`; under the native owner's explicit authorization for
   this task, record that effective profile truthfully as `tool_profile:
   madhav-parity` in the repository handshake. Do not relabel a managed or
   on-request task. If the effective profile is still managed/on-request, do not
   begin L0—return `HOST_PERMISSION_PROFILE_BLOCKER` to the strategy task;
3. read `AGENTS.md`, `CLAUDE.md` and the required session-open sequence;
4. read the six foundation files at `d838af455`, the v2.0 architecture/register/
   review/evidence, the strategic ledger, L0 strategy and this brief;
5. use `layer-value-elevation` for consumer/portfolio decisions and
   `autonomous-asset-elevation` for implementation; follow any stricter skill
   gates; and
6. remeasure Git, generated inventory, relevant current source/tests/migrations,
   current consumers and proportionate read-only population/service evidence.

Historical L0 seals, old 12-asset plans and row floors are evidence only. Do not
restart, overwrite or recertify a frozen campaign by implication.

## 4. Autonomy and execution authority

Proceed autonomously through this bounded goal. Do not ask routine questions or
request sandbox escalation. Use the default Full Access/never policy for
authorized local work and choose safe reversible defaults.

Authorized:

- read-only repository, Git, generated inventory and proportionate aggregate
  runtime/database inspection already accessible without exposing private rows;
- L0 strategy implementation in the header's fixed `may_touch` producer files,
  source/reference modules, services and producer-owned generated adapters, plus
  adjacent tests required by an accepted L0 contract;
- forward-only migrations only when a proved contract cannot fit current schema;
- generated adapters derived from the accepted authority, deterministic fixtures,
  validation/evidence artifacts and execution-ledger updates;
- local commits on the execution branch and independent read-only review.

Not authorized:

- push, PR, merge, merge queue, deployment, production mutation, destructive
  rebuild, active campaign mutation or protected-main changes;
- Product Definition, CCD, canonical manifest, CURRENT_STATE or SESSION_LOG
  mutation; proposal promotion beyond DP-SD-009's planning-basis decision;
- L1-L5 implementation, personal chart/observation use, private-row inspection,
  consent/disclosure changes, source acquisition or unsupported rights claims;
- medical diagnosis, remedial efficacy, future prediction/model activation,
  empirical-performance claims, retirement or a new universal registry.

Stop only for a real product/adoption, doctrine/source-rights, safety/privacy,
credential, irreversible/destructive, protected delivery or irreconcilable
governance gate. Record the smallest strategic decision needed and preserve work.

## 5. Owned scope and protected surfaces

The 40 identities are exactly those in the approved L0 strategy and pinned
inventory: 36 `bg_*` writers plus `bg_ephemeris_engine`, `bg_panchanga`,
`bg_gochara_citation_resolution` and `bg_sarvatobhadra_grid`. The header's
`may_touch` list is the immutable outer mutation boundary for this brief.

WP0 must narrow that boundary into an exact file/table/service manifest before
the first edit, with justification, current consumer, preserved kernel and
rollback. Execution may add an exact file only when it already matches one of
the preapproved header globs and is a direct implementation of a fixed contract
in this brief. It may not add a new path class, answer authority, downstream
consumer, product meaning, source/right or doctrine. Such a need returns to
strategy. Existing files are not permission to edit; files outside the admitted
manifest remain protected.

All migration files already present at `source_revision` are immutable. A
forward migration may only be a newly created file matching one of the two
header `*_data_plane_l0_*.sql` globs, after WP0 proves the schema gap,
compatibility, ordering and rollback. Renaming or editing an existing migration
is prohibited.

A producer adapter is a deterministic, version-pinned representation generated
from L0 authority (for example Python/TypeScript identity or Vidhi parity). It
may be changed and parity-tested here. Retrieval queries, ranking, inquiry
planning, managed/raw MCP, synthesis and user-facing delivery are consumers and
are read-only evidence surfaces in this stage. Their use of the release is the
later `INTEGRATED` gate, not part of L0 `PRODUCER_READY`.

The frozen orchestrator transaction/WriterBase/idempotency contract is protected.
If the accepted requirement cannot fit it, return an architecture decision rather
than silently changing orchestration.

## 6. Required work packets

### L0-WP0 — stocktake and evidence pin

- Reconcile 40/40 identities with tables, files, algorithms, inputs/outputs,
  epistemic role, actual/direct/transitive consumers, generations and historical
  receipts. Include answer authorities outside the denominator where they can
  alter L0 meaning or delivery.
- Distinguish present, populated, qualified, consumed, effect-traceable, served and
  value-evaluated. Use aggregate/private-safe evidence and record observation time.
- Classify every suspected gap as absent source, unqualified semantics, wrong
  mapping, computation, serving, operation or unproven value.
- Produce the exact may-touch manifest and preservation map before mutation.

### L0-WP1 — DP01 identity and semantic releases

- Set the exact authority boundaries among `bg_ontology`, `bg_reference`,
  specialized references, formula constants and local vocabularies.
- Preserve stable IDs, aliases/scripts/transliterations, roles and physical
  variants. Mean/true nodes and legitimate method variants remain explicit.
- Generate/version adapters rather than creating independent lexical authorities.
- Prove Python/TypeScript/ingestion/retrieval parity, ambiguous/unknown behavior,
  backward compatibility, deprecation and correction propagation.

### L0-WP2 — DP02 source and rule qualification

- Preserve works, editions/translations, passages, context, ancestry and evidenced
  rights/use status; never manufacture a source or right.
- Represent rule clauses, operators, prerequisites, applicability, conjunction/
  disjunction, exceptions/cancellations, disputes and executable/readable status.
- Reconcile texts, indexes, compendium, concordance, rules, yoga, dosa, dasha,
  remedy and specialized method assets without merging navigation into authority.
- Concordance must hydrate actual passage/rule ancestry; abundance or extraction
  confidence cannot mean agreement, truth or probability.
- Qualify Bhavat Bhavam only to the source-adjudicated scope. Preserve narrower
  existing kernels and explicit unresolved cases; no doctrine expansion by demand.

### L0-WP3 — convention, service and restricted-capital contracts

- Reconcile dignity/combustion/constant differences as named qualified variants or
  explicit unresolved conflicts; do not copy a convenient value.
- For ephemeris, arcs, calendar, Muhurta lattice, transit, Panchanga, KP, Kota,
  vedha/latta and Sarvatobhadra, retain method, frame, node, location/timezone,
  instant/interval, precision, approximation, horizon, generation and failure.
- Keep global samples distinct from arbitrary-instant services and personal use.
- Keep medical/vastu/remedy/cohort/prior capital attributed, restricted and
  purpose-bound. Synthetic counts are not people or individual probability.
- Make Vidhi capability/floor records versioned, parity-checked and expandable.

### L0-WP4 — first producer slice

Produce `L0-SLICE-RESOURCE-CONFIG-01` exactly as frozen in L0 strategy §7. The
legacy comparator, global/reference grain, required fields, admitted corpus and
source steward, preserved odd/even/non-recursive restraints, five qualification
states, changed outputs, invariant outputs and minimum fixture cases are fixed
acceptance inputs; WP0 may measure them but may not rewrite them.

The slice must be a reusable producer package and fixture set—not a reading of
any person. Prove stable identities, exact admitted witnesses where available,
qualified clauses and exceptions, calculation/reference prerequisites,
unsupported states, adapter parity and consumer-ready field/grain/lineage
definitions. If an exact passage/edition/rights pin is absent, emit
`UNQUALIFIED_SOURCE` and keep the positive fixture `NOT_REACHABLE`; never select
or promote a convenient source to make the test pass. Do not edit L1/L2,
retrieval-query, Pariprashna, synthesis or MCP consumers to demonstrate use.

### L0-WP5 — acceptance and handoff

- Complete 40/40 component dispositions, compatible-generation and typed
  correction/invalidation/cache/rollback map.
- Run applicable qualification, service/computation, relevant/irrelevant-input,
  duplication, missingness/context, boundary/precision, omission, served-evidence,
  revision and simpler-baseline tests. Do not invent empirical tests.
- Obtain independent read-only challenge of the whole L0 result and correct all
  owned HIGH/CRITICAL findings.
- Update the execution ledger, locally commit the bounded diff, return a terminal
  packet to `Strategy — Data Plane`, call `update_goal(complete)` only if true,
  and stop with L1 still waiting.

## 7. Required deliverables

Use the smallest coherent versioned package under the existing Nirmana brief/
evidence hierarchy; do not create a rival registry. At minimum return:

1. L0 current-state/evidence and complete 40-identity disposition register;
2. L0 semantic release and identity/adapter contract;
3. L0 source-witness/rule-qualification and rights-status contract;
4. L0 convention/service/restricted-capital contract;
5. `L0-SLICE-RESOURCE-CONFIG-01` schema plus frozen fixtures;
6. compatibility, correction, invalidation and rollback record;
7. executed validation and independent-review record; and
8. L0 producer-ready acceptance/handoff record with exact commits and residuals.

Reuse and version existing adequate artifacts instead of duplicating them. A
documentation artifact alone is not implementation proof.

## 8. Acceptance tests and terminal truth

Acceptance requires all criteria in the approved L0 strategy plus:

- exact generated census remains 36 writers + four non-writers with no implied
  campaign-denominator change;
- every PASS/status has a detector and negative fixture;
- idempotency/repeatability, honest failure, compatibility and rollback are proved
  for every changed component;
- no generated adapter diverges from its pinned semantic release;
- the first slice demonstrates a distinction or prevented error relative to the
  simpler legacy representation without claiming end-user value;
- Git diff and tests prove only declared L0/direct-adapter scope changed;
- no private data or credentials appear in evidence; and
- unreached states are reported exactly.

The terminal status matrix must be:

| State | Required at close |
|---|---|
| `STRATEGY_AGREED` | Yes — DP-SD-009 and L0 strategy |
| `PRODUCER_READY` | Yes — complete acceptance evidence |
| `INTEGRATED` | No claim unless separately authorized and actually proved |
| `DEPLOYED_OPERATIONALLY_ACCEPTED` | Not authorized |
| `CONSUMER_VALUE_DEMONSTRATED` | Not part of this goal |
| `EMPIRICALLY_EVALUATED` | Not part of this goal |

If `PRODUCER_READY` cannot be reached because a strategic/source-rights/doctrinal
decision is genuinely missing, do not manufacture closure. Return the exact
affected identities, preserved progress, evidence, smallest decision and next
eligible action. Do not begin L1.
