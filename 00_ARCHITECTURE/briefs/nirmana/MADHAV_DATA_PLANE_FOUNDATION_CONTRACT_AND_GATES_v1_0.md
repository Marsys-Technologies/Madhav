---
artifact: MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES
version: "1.0"
status: EXECUTION_CONTROL
produced_on: 2026-09-13
session_id: MADHAV-DATA-PLANE-EXECUTION-FOUNDATION-20260913
product_authority: ../../MADHAV_PRODUCT_DEFINITION_v3_0.md
strategy_input: MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md
authority_boundary: >
  Reusable execution contract under the adopted product target. It does not adopt the strategy
  proposal, reopen historical seals, authorize implementation or create a competing product registry.
changelog:
  - "1.0: Encodes plane-wide invariants, DP01-DP18 operational contracts, evidence/delivery states, compatible-generation and correction rules, serving/evaluation firewalls, owners and acceptance gates."
---

# Madhav data-plane foundation contract and gates

## 1. Status and use

This is the single normative execution encoding of the plane-wide foundation. Later layer and asset/interface briefs reference these IDs instead of duplicating or weakening them. If a strategic brief conflicts with the adopted Product Definition v3.0, ratified architecture, safety policy or an accepted upstream contract, execution stops and returns the conflict to the strategic parent.

Product Definition v3.0 is adopted as the target. Data Plane Value Architecture v2.0 remains proposed until separately adopted or amended. No proposal becomes adopted because it was authored, committed, tested, deployed, previously sealed or left uncontested.

## 2. Plane-wide invariants

| ID | Binding invariant | Required execution evidence |
|---|---|---|
| F01 | Preserve exactly six responsibilities: Brahmagyan, Gaṇita, Bodha, Kāla, Phala and Mīmāṃsā. No seventh truth/knowledge/feedback layer. | Brief maps ownership to the six layers or records an authority question. |
| F02 | Preserve the end-to-end path: question → applicable concept → qualified rule → canonical fact → structural relationship → temporal mechanism → manifestation or explicit gap → delivered finding → protected evaluation. | Trace with IDs, operators, exact fields, lineage and honest gap state. |
| F03 | Value is an earned distinction, prevented error, reduced uncertainty or exposed limitation. Asset/row/tool/word counts and historical acceptance are not value. | Baseline comparison names the consumer distinction and added error/burden/cost. |
| F04 | Keep six epistemic classes distinct: source testimony; qualified rule; computed fact/configuration; interpretive inference; external claim/forecast; evaluation evidence. | Every important input/output declares class and authority. |
| F05 | Preserve facts, derivations, interpretations, stable identity, provenance and evidence dependence. Retrieval rank never overrules authority; repeated representations of one root are correlated, not independent. | Authority resolution and root-evidence/dependence IDs. |
| F06 | Completeness states are `applied`, `inapplicable`, `unavailable`, `unqualified`, `contradictory_unresolved`, `unexplored`. | No null/zero/empty fallback collapses these states. |
| F07 | Where qualified and applicable, preserve depth across graha roles; rāśi/bhāva/lord/kāraka; bala/dignity/avasthā; sambandha; Bhāvat Bhāvam; varga; yoga/doṣa/bhaṅga; nakshatra/KP; ārūḍha/special lagnas; Kāla; Pañcāṅga; Praśna; Muhūrta; and permitted attributed practice. | Applicable-concept ledger plus omission challenge and qualification source. |
| F08 | Form a coherent within-method bundle before cross-method comparison. Never average incompatible schools or count shared-input convergence as independent evidence. | Method/version/prerequisite pins and ancestry-aware comparison. |
| F09 | Select compatible dependency sets, not independent latest-per-layer rows. Preserve generations, consumed values, snapshots, invalidation, cache scope, correction propagation, history and rollback. | Compatibility manifest and consumed snapshot. |
| F10 | Preserve structural identity, participants, roles, domains, polarity, occurrence/condition, exceptions/cancellations and ancestry through L2→L3→L4→L5. | Cross-layer identity and field continuity tests. |
| F11 | Discovery, retrieval, SQL projections, answer-shaping tools, ranking, adaptive inquiry, synthesis, budgets, persistence, replay, export, Paripraśna, managed MCP and raw MCP belong to the data-to-answer chain. | Producer-to-served trace includes every material intermediary. |
| F12 | Every important input declares an operator: `computation`, `applicability`, `counterevidence`, `uncertainty`, `interpretation`, `exclusion`, `relevance_navigation` or `evaluation`. | Operator field plus receiving output and test. |
| F13 | Evidence maturity progresses separately: present → qualified → consumed → effect traceable → served → value evaluated. | Evidence per rung; no rung inferred from a later/earlier label. |
| F14 | Delivery progresses separately: strategy agreed → producer ready → integrated → deployed/operationally accepted → consumer-value demonstrated → empirically evaluated. | Named receipt for each reached state; unreached states stay explicit. |
| F15 | Keep event-free generation, permitted historical inquiry, protected evaluation and future context-conditioned prediction separate. The fourth is proposal-only. | Purpose code, allowed inputs, cutoff and forbidden-flow test. |
| F16 | Observations preserve subject, source, event time, knowledge time, precision, purpose, exposure, confirmation/dispute and revisions. Unknown is not a non-event. | Immutable revision lineage and missingness-aware adjudication. |
| F17 | Freeze completed issued claims before later outcomes: proposition, wording, window, probability, assumptions, cutoff, consumed evidence and eligibility. Never evaluate a retrospective rewrite. | Issuance receipt predates admitted evaluation outcome. |
| F18 | Enforce C1/C3/PPR-31 and indirect leakage controls. Feedback capture is not learning; later artifacts require immutable admission and separate authority. | Direct and indirect forbidden-flow tests, feature lineage and admission receipt. |
| F19 | Preserve useful source corpus, IDs, numerical kernels, relationships, interfaces, compatibility projections, historical readings, failed forecasts, tests, receipts and restricted research capital. | Component disposition and preservation/migration map. |
| F20 | Rationalize per component: preserve; integrate; enrich/correct; qualify/limit; investigate consolidation; retain historical/restricted; retire only after migration; unresolved use explicit. | Current callers/semantics/history and reversible successor proof before retirement. |
| F21 | Preserve safety, privacy, subject/tenant/purpose scope, source rights and current exclusions. No brief changes consent or disclosure implicitly. | Access/source-rights inheritance and negative authorization tests. |
| F22 | Require honest failure, idempotency, resumability, freshness, cost visibility, detector-backed statuses, compatibility and rollback. | Failure injection, repeat/resume checks, age/cost fields and detector trace. |
| F23 | Required proof set: qualification/source; computational/service; relevant-input influence; irrelevant-input control; duplication/correlation; missingness/context; boundary/precision; omission challenge; served-evidence sentinel; revision/invalidation; managed-channel proof; simpler-baseline comparison; added-error/burden/cost; separately governed empirical evaluation. | Executed results with fixtures and raw evidence; planned tests are not passes. |
| F24 | Keep computational correctness, explanatory/discriminative value and empirical outcome performance as separate proof tiers. | Separate claims, tests, datasets and verdicts. |
| F25 | Implement in accepted upstream dependency order, while keeping downstream demand and serving/evaluation needs visible from the start. | Accepted contract pins and demand ledger. |
| F26 | Preserve frozen orchestrator ownership and layer idempotency rules; later writers conform rather than extending the orchestrator unless separately authorized. | Conformance checklist and transaction/idempotency proof. |
| F27 | L1 facts/configurations retain authority over downstream restatements. Downstream disagreement is a bug or contested interpretation, not an alternate computed truth. | Canonical fact IDs, no local recomputation, mismatch halt. |
| F28 | Detector-backed status only: every PASS/state/grade names the code path that can turn it false. Otherwise the field is null/unknown. | Detector, negative fixture and measured claim alignment. |

## 3. Shared state vocabularies

### 3.1 Epistemic class

| Code | Meaning | May establish | Must not establish alone |
|---|---|---|---|
| `SOURCE_TESTIMONY` | What an identified source/edition/witness says | Textual testimony and attributed scope | Executability, consensus or empirical truth |
| `QUALIFIED_RULE` | Source-qualified operator with prerequisites, exceptions and method | Permitted applicability/computation/interpretive operation | Chart occurrence or life outcome |
| `COMPUTED_FACT_CONFIGURATION` | Reproducible subject/context calculation or formation state | The declared fact/configuration under pinned conventions | Unique meaning, manifestation or causation |
| `INTERPRETIVE_INFERENCE` | Qualified structural/temporal/manifestation reading | Reasoned interpretation and alternatives | Independent observation or calibrated probability |
| `EXTERNAL_CLAIM_FORECAST` | Frozen real-world proposition | What was actually claimed for a window | Outcome or accuracy |
| `EVALUATION_EVIDENCE` | Qualified observation/adjudication/score | Evaluation of an eligible frozen claim | Same-claim generation input or universal truth |

### 3.2 Completeness, maturity and delivery

Completeness uses only the six F06 values and records `reason`, `owner`, `evidence_ref` and `next_eligible_action`.

Evidence maturity uses ordered rungs: `present`, `qualified`, `consumed`, `effect_traceable`, `served`, `value_evaluated`. A component may reach different rungs for different questions, subjects, methods or channels.

Delivery uses ordered but independently evidenced states: `strategy_agreed`, `producer_ready`, `integrated`, `deployed_operationally_accepted`, `consumer_value_demonstrated`, `empirically_evaluated`. A green test or producer receipt cannot skip a state.

## 4. DP01-DP18 operational contracts

Every later brief declares applicable DP rows, accepted input contract/version, exact grain and owner, success/failure semantics, proof owner and exit receipt.

| ID | Responsibility and minimum operational fields | Acceptance / owner / proof type |
|---|---|---|
| DP01 | Identity/release: `identity_id`, canonical aliases, physical variant, layer owner, semantic/interface version, release/admission status, supersession and compatibility. | No rival definitions; generated consumer adapters agree. Owner L0 + consuming interface; semantic/parity proof. |
| DP02 | Rule qualification: source witness/edition/rights, method/school, operator, prerequisites, applicability, exception/cancellation, dispute, executable/readable status. | Actual clause supports operator and scope; competing witnesses retained. Owner L0/source steward; source/qualification proof. |
| DP03 | Chart facts: subject/tenant, chart/build/generation, instant/location/timezone, ayanāṃśa/frame/node/house/varga/method, units/precision, fact/configuration ID, value, verification and failure reason. | Reproducible under pinned context; wrong context fails/isolates. Owner L1/service; computational/service proof. |
| DP04 | Condition decomposition: participant, condition type, component value/unit, reference scale, polarity/role, uncertainty, source/fact lineage and aggregation rule. | Components survive; capacity/beneficence/ease/prominence/probability are not silently collapsed. Owner L1 with L2 consumer; computation + influence proof. |
| DP05 | Configuration: configuration identity, participants/roles, method, formation/partial/not-formed state, prerequisites, exceptions/bhaṅga, constituent fact/rule IDs and verification. | Actual conditions tested, catalog label not promoted. Owner L1 with L2 hydration; formation/negative-case proof. |
| DP06 | Structural relationship: source/target/mediator, relation type/basis, domain, sign/polarity, occurrence/condition, path/cycle, counterpath, ancestry and evidence dependence. | Multi-hop and cancellation meaning survives; shared root not independent. Owner L2; graph/lineage/duplication proof. |
| DP07 | Precise clocks/contacts: method/system, parent/child clock, start/end/instant precision, timezone, hierarchy, contact geometry, tolerance, recurrence, reference date/horizon and source generation. | Adjacent/boundary intervals and nearest/strongest semantics correct. Owner L1/L3/service; numeric/boundary proof. |
| DP08 | Temporal mechanism: structural identity, applicable clocks/contacts, enabling/inhibiting conditions, interval intersection, route, alternatives, recurrence, coverage and gap. | Same structure is temporalized; activity is not event probability. Owner L3; mechanism/influence proof. |
| DP09 | Manifestation: mechanism identity, outcome proposition/class, alternatives, constraints, falsifier, ordinary expression, feasibility, allowed audience, claim readiness and explicit unresolved bridge. | Qualified bridge or honest stop; no generic score converted to outcome. Owner L4; source/contrastive proof. |
| DP10 | Capability discovery: concept/operator/method/field, source capability, input/output contract, authorization, availability/freshness, cost and drill path. | Specific concept maps to callable evidence, not tool-count coverage. Owner retrieval/catalog; discovery and access proof. |
| DP11 | Investigation completeness: question obligations, applicability state per concept, omission challenges, competing interpretations, evidence dependence, passes/checkpoints, budget, progress/cancel/resume and residual gaps. | Material obligations completed or explicitly incomplete; no arbitrary pass count. Owner inquiry planner; omission/resume proof. |
| DP12 | Complete delivery: finding/part IDs, conjoint interpretation, decisive/counter evidence, citations, gap/status, channel, budget treatment, persistence/replay/export and receipt. | Relevant authorized findings survive all intermediaries and managed channels. Owner synthesis/delivery; sentinel/parity/replay proof. |
| DP13 | Observation intake: observation/subject/source IDs, testimony, event/state/intention type, event time, knowledge time, precision/location, purpose, exposure, confirmation/dispute, duplicate links and revisions. | Canonical owner resolved; unknown/silence/non-event distinct. Owner observation authority; chronology/revision/access proof. |
| DP14 | Historical comparison: frozen hypothesis/reading reference, admitted observation revision, fit/misfit/unassessable, unmatched activation, hindsight/exposure, rival criteria, burden and purpose. | Permitted comparison without chart-fact rewrite or prospective leakage. Owner historical inquiry/L5; blind/chronology proof. |
| DP15a | Claim issuance: immutable claim ID, proposition, exact wording, claim type, model probability and separate operator band, window, assumptions, cutoff, eligibility, consumed snapshot and completion/interruption state. | Seal before exposure/evaluation; interrupted content excluded as required. Owner protected claim authority; immutability/firewall proof. |
| DP15b | Later evaluation: frozen claim ID/version, eligible observation revision, capture/confirmation/observation/scoring denominators, adjudication, censoring/dispute, score/baseline and evaluation version. | Original forecast scored against independent outcome; C3 never enters provider synthesis. Owner protected L5; prospective/held-out proof. |
| DP16 | Version/correction: correction ID/type/reason/authority, old/new value, dependency edges, affected current artifacts/caches, stale marks, rebuild generation, snapshot retention and rollback. | Coherent propagation with originals retained. Owner producer + dependency coordinator; invalidation/replay/rollback proof. |
| DP17 | Controlled comparison: matched identity, changed dimension, fixed context/budget, alternate computation/application, shared ancestry and changed/unchanged/unsupported findings. | Real changed computation/application, not two unconstrained essays. Owner comparison authority; differential proof. |
| DP18 | Future qualification: admitted artifact ID/version, population, cutoff, features/lineage, permitted consumers, independent evaluation and admission authority. | Immutable separate admission; no automatic personal tuning, model activation or proposal promotion. Owner L5/admission authority; independent-evaluation proof. |

## 5. Compatible generation, correction and rollback contract

A `dependency_set_id` binds each consumed producer tuple: `{asset_or_service_id, semantic_version, interface_version, generation_or_build_id, upstream_dependency_set_id, subject, context, method, reference_time_or_horizon, purpose, access_scope, policy_version, model_version_if_any}`. Layers need not share one global build ID, but every selected generation must be compatible with the generations it consumed. `latest` is never a compatibility rule.

A delivered reading stores an immutable consumed snapshot of material values and provenance, not only mutable pointers. Partial refreshes publish only after compatibility passes; otherwise retain the earlier qualified result with age and limitation or report unavailable/stale.

Corrections declare type (`source_meaning`, `input`, `computation`, `interpretation`, `observation`, `claim_parse`, `policy`), authority, dependency blast radius and required stale marks. Current derivatives/caches invalidate before reuse; historical delivered readings and issued claims remain unchanged. Rebuilds are idempotent and resumable, preserve history, and produce a new generation. Rollback restores a compatible prior set and records why; it never rewrites the original receipt.

Cache keys include subject/tenant, context/conventions, compatible generation set, purpose/access scope, query/inquiry state, and policy/model version. Permission withdrawal or changed meaning invalidates affected entries. Snapshot retention never broadens access, and hashes/tombstones are not assumed anonymous.

## 6. Observation, issuance and evaluation firewall

| Purpose lane | Allowed flow | Forbidden flow |
|---|---|---|
| Event-free generation | Qualified L0/L1/L2/L3/L4 evidence and permitted question context | Life events/outcomes, indirect event features, personal selectors/weights, outcome-derived summaries, rectification derived from events under PPR-31 |
| Permitted historical inquiry | Purpose-qualified observations joined after an independently preserved structural/temporal context where required | Hindsight represented as prospective success; observation rewriting chart fact |
| Protected evaluation | Frozen issued claim + eligible observation revision inside C3/L5 boundary | C3 content to provider/synthesis; retrospective substitute claim; denominator collapse |
| Future context-conditioned prediction | None under this foundation | Any implementation or activation without explicit policy amendment, immutable feature lineage, separate authority and evaluation |

Claim candidates and rebuildable Phala/Mīmāṃsā outputs are not protected issuance history. Issuance must occur before an exposed completed forecast can enter evaluation. Every direct and indirect path—prompts, retrieval summaries, caches, model overlays, rectification, selectors, weights and prior reading context—is tested. Feedback capture alone changes no model, rule, weight or future artifact.

## 7. Serving, managed channels, safety and access

The producer-to-answer trace includes discovery, projection, ranking, hydration, adaptive passes, synthesis, budgets, persistence, replay and permitted export. A decisive low-ranked/non-default field must survive to the finding and receipt. Every status and omission reason is detector-backed.

Paripraśna and managed MCP must provide equivalent authorized substantive evidence, qualification, gaps and completion semantics for equivalent requests; prose may differ. Raw MCP guarantees scoped correct evidence, discoverability, provenance, pagination and honest gaps, not an external client's complete investigation. Retrieval rank and response-budget pressure cannot promote lower authority or erase decisive counterevidence.

All existing safety exclusions, tenant/subject/purpose checks, access grants, source rights and disclosure controls are inherited. Medical/mortality and other restricted capital remains restricted. Later briefs must name the access/source-rights owner and test negative authorization, wrong tenant/subject, withdrawn permission and prohibited purpose. This foundation grants no new access or disclosure.

## 8. Gate matrix

| Gate | Minimum entry | Required exit | May not be claimed from |
|---|---|---|---|
| Strategy agreed | Explicit strategic decision/version | Decision record with unresolved scope | Draft presence, commit or silence |
| Producer ready | Accepted upstream contract + owner | Qualification/computation/service, context, failure and compatibility tests | Row count or code existence |
| Integrated | Producer ready + consuming implementation | Relevant/irrelevant/duplication/missingness/boundary/omission tests and effect trace | Producer tests alone |
| Deployed/operationally accepted | Integrated candidate + release authority | Actual revision/environment, migration/build as applicable, managed-path receipt and rollback readiness | CI, PR, local run or dashboard |
| Consumer value demonstrated | Operational path + simpler baseline | Correct added distinction/prevented error/uncertainty/comprehension plus error/burden/cost | Computational influence or richer prose |
| Empirically evaluated | Frozen eligible claims + governed observations | Prospective/held-out, denominator-aware comparison with uncertainty and baselines | Fixtures, retrodiction or explanatory value |

## 9. Brief-consumption workflow

1. Verify strategic brief authority, status, branch/base, accepted upstream contracts and no unresolved meaning/safety/adoption decision hidden in execution scope.
2. Open a new bounded goal for exactly one stage or packet; update the execution ledger. Never reuse FOUNDATION for L0.
3. Reconcile current repository/generated/live evidence proportionately before mutation; protect shared/foreign worktrees.
4. Produce a field-level demand/offer and preservation map before choosing physical changes.
5. Implement only owned scope in dependency order; preserve frozen contracts and current campaign gates.
6. Execute focused proof for applicable F/DP obligations and separate proof tiers/states.
7. Obtain independent review where the approved brief requires it; retain findings and corrections.
8. Return a terminal packet with commits, changed surfaces, raw checks, release evidence, residuals and next strategic decisions.
9. Stop in `WAITING_FOR_STRATEGIC_BRIEF`. Activity, checks or deployment never self-authorize the next stage.
