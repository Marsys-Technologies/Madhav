---
artifact: PURNA_ANVESANA_INDEPENDENT_REVIEW_HANDOFF
version: "1.0"
status: FOR_INDEPENDENT_REVIEW_NOT_AN_EXECUTION_AUTHORIZATION
prepared_on: "2026-09-22"
evidence_cutoff: "2026-09-22T12:20:00Z"
campaign_id: madhav-purna-anvesana
prepared_by: Codex, Madhav product-strategy task
intended_reader: Native-selected Anthropic Claude Code reviewer
purpose: Full-context independent diagnosis and elevated completion plan
product_parent: 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md
execution_plan: docs/superpowers/plans/2026-09-17-purna-product-completion-v2.md
execution_task_id: 01a0b7d8-9a90-74f3-aab9-80014919f8b2
execution_task_title: Madhav — Planner & Inquiry Product Completion II
authority_boundary: Review and planning only; no takeover, implementation, merge, deployment, infrastructure change, or production mutation authorized by this document
confidentiality: Internal engineering context; no credentials, raw chart payloads, or private life-event logs included
---

# Pūrṇa Anveṣaṇa — complete campaign context and independent-review handoff

## 1. The request to the independent reviewer

The Native—the product owner—wants an independent, technically deep review of a campaign that has produced substantial engineering but repeatedly struggled to achieve a demonstrably complete user-facing result. Please review the objective, architecture, implementation, execution method, blockers, and evidence standard together. Return an elevated, implementable completion plan, not merely a code review or another list of missing proofs.

The owner will bring that review back to the product-strategy conversation before deciding how to execute it. This is **not a transfer of execution ownership to Claude Code**. Do not start a second writer, change an existing execution task, merge a PR, dispatch production work, modify permissions, or reinterpret this document as approval to do so. Inspection and non-mutating diagnostics are appropriate; write your review as a separate artifact. Propose any required authority expansion explicitly.

Do not accept this handoff's diagnosis uncritically. It was prepared by the same strategic coordination context that helped direct the campaign. In particular, challenge whether its own instructions, gates, work decomposition, or ownership boundaries contributed to the delay.

The central review question is:

> How do we preserve the valuable foundation, correct the actual architectural and operational weaknesses, and deliver the intended deep, complete, evidence-grounded inquiry experience across all governed channels—with maximum execution velocity and only necessary controls?

### Reading guide

- Sections 2–5: product intent, requirements, architecture, and scope.
- Sections 6–9: original plans, execution history, achievements, and fresh status.
- Sections 10–13: remaining work, all 19 unavailable bindings, and diagnosis.
- Sections 14–17: review questions, proposed recovery structure, safeguards, and required reviewer outputs.
- Sections 18–21: exact source references, worktrees, reproduction guidance, original kickoff, and glossary.

This document is self-contained for the strategic review. Repository access is needed to validate implementation and produce a file-level recovery plan. Git-relative paths throughout refer to `Marsys-Technologies/Madhav`; use the stated revision, not whichever checkout happens to be open.

## 2. Executive assessment at the evidence cutoff

### 2.1 Bottom line

The campaign is **not complete**. It has a substantial implemented foundation, protected production-delivery repairs, a real three-channel collector, a defined automated acceptance protocol, and much better capability accounting. It does **not** have recorded acceptance of the complete product journey on either the candidate or live environment.

At this review:

| Dimension | Evidence-backed position | Qualification |
|---|---|---|
| Execution task | Idle when inspected on September 22 | Its last substantive September 20 completion message explicitly said the goal was marked blocked; the goal tool was not queried across tasks in this review. |
| Autonomous monitor | ACTIVE, scheduled every 10 minutes | Recent activations overwhelmingly reported unchanged external boundaries; an active timer is not continuing implementation. |
| Latest Pūrṇa integration candidate | PR #2705, open and blocked | Head `34991645b1d57926d97ac027d6fca59d8c2ecb53`; last commit September 20, 14:11:29 UTC. |
| Source capability accounting | 182 SCUs; 186 executable bindings; 167 explicit availability contracts; 19 deliberate-dark dispositions; zero uncovered bindings | This is the unmerged candidate's inventory, not live availability or semantic completeness. |
| Knowledge graph | 259 typed concepts; 53 edges; 156 isolated SCUs, all dispositioned | Zero unexplained gaps does not mean a richly connected graph. Whether these dispositions are appropriate is a major review question. |
| Pagination | 96 reviewed paginated descriptors; 5 exhaustible; 91 non-exhaustible | Bounded windows and top-k results may legitimately be non-exhaustible; material completeness must be justified per route. |
| Candidate acceptance | Full 35-case × 3-door corpus not recorded as run/passed | No aggregate candidate acceptance can be claimed. |
| Live acceptance | Last recorded initial wealth slice: 0 of 3 doors accepted | No fresh successful replacement is recorded in the inspected campaign state. |
| Production web | 100% traffic on `5ff0030f398dd1ef97ffc381005c8a1f2e600329` | Fresh direct revision-level verification on September 22. This is newer than the September 20 campaign ledger. |
| Production MCP and sidecar | Both 100% traffic on `09d998940069e00a4f09df60a03c3d07d6536ecf` | Fresh direct verification; differing component revisions require compatibility attestation, not an automatic assumption that every difference is a defect. |
| Shared L3 builder grant fix | PR #2700 merged | This review did not independently query production SQL to establish application, rebuild success, or recovered dasha consumption. |

### 2.2 What the numbers do—and do not—say

`167 / 186 = 89.8%` is **source availability-contract coverage**. `(167 + 19) / 186 = 100%` is **binding accounting**. Neither is an overall completion percentage. The 19 unavailable bindings include material product capabilities, not just irrelevant administration tools. Conversely, some descriptors are prompts, resources, or planning outputs; their correct treatment must respect their declared function rather than require them all to be completed astrological answers.

No defensible overall percentage is offered. The campaign's own plan explicitly rejects percentages inferred from catalogue counts, test counts, PRs, or elapsed time. The meaningful short-term indicator is whether one demanding inquiry actually completes with correct evidence, a complete delivered fact register, and equivalent governed closure across the three channels.

### 2.3 Evidence classification used here

- **Freshly observed:** inspected during this September 22 review through GitHub, local source, generated artifacts, task state/history, or Cloud Run metadata.
- **Recorded historical evidence:** a governed record describes an earlier result, with a revision/run where available. It has not automatically been re-earned on current source.
- **Implementation present:** relevant code/tests exist; that does not prove actual deployed integration.
- **Hypothesis:** an explanatory inference requiring independent challenge.
- **Not verified:** a specific question remains open; it must not be silently converted to success or failure.

No production chart data, private event log, or secret value was retrieved for this review. No acceptance suite or production database operation was executed. Tests cited below are recorded or CI-observed results, not a newly rerun full local suite.

## 3. Why this campaign exists: the consumer promise

### 3.1 Madhav is not intended to be a conventional astrology application

The adopted Product Definition v3.0 describes Madhav as a Jyotish intelligence, prediction, and discovery instrument. It should connect more relevant knowledge, chart structure, temporal information, relationships, competing explanations, and lived-event evidence than an individual practitioner can comfortably hold in working memory.

The intended distinction is not larger reports, more tool calls, obscure terminology, or persuasive prose. It is a useful, chart-specific understanding that changes what the user can discriminate, question, prepare for, or test. The product must explain both the connected basis and the limitations of its conclusions.

“Beyond-Ācārya” is a design ambition, not established predictive accuracy, supernatural authority, or proven universal superiority to experts. Automated engineering/answer evaluation is also not empirical validation of astrology. The system must be capable of finding misfit, uncertainty, and limits—not forcing every observation to confirm a chart.

### 3.2 Concrete questions motivating the work

The user expects the system to investigate questions such as:

- When might a financial promise in the rāśi chart activate? What mechanisms, periods, and triggers support that statement?
- When might financial strain ease? How do supportive indications coexist with loss, inhibition, or delay?
- When might business succeed or a promotion become plausible?
- When might a particular yoga manifest, including Nīcha-bhaṅga Rāja Yoga? If there are several windows, which is nearest and which is stronger?
- What relationship, marriage, children, family, or wellbeing indications are supported, and what cannot responsibly be inferred?
- Given an authorized chronology of life events, which proposed chart mechanisms fit, which are ambiguous, and which do not fit?
- What changes when a disputed method or sensitive birth-time assumption is excluded?

The answers must join structural promise with timing, cancellation, counterevidence, and actual manifestation conditions. A precise-sounding date without its supported chain is not the target product. Health interpretations must not become medical diagnoses, and financial interpretations must not become guarantees.

### 3.3 The user's three core concerns

**Complete visibility for planning.** The planner must know what the platform can provide below the asset level: facts, tables, mappings, graph relations, computed patterns, contextual qualifications, and drill paths. Information that exists but is undiscoverable or unreachable is stranded value.

**Deep investigation.** The planner should understand and decompose the question, retrieve, inspect new evidence, discover useful adjacent relationships, and continue until material obligations are settled or genuine limits are explicitly recorded. A fixed two-hop traversal or initial keyword list is not enough. Bhāvat Bhāvam and consequential chains were concrete examples of previously missed concepts.

**Complete delivery.** If 200 material facts contribute to synthesis, the response must account for all 200—not 199. The answer should carry each relevant fact and its individual or conjoint interpretive contribution, including contradictory findings. A readable narrative plus a complete durable evidence register is acceptable; silently losing a fact or requiring a later question to discover it is not.

The user does not want private internal model deliberation. They want facts, derivations, connected interpretation, limitations, and an understandable basis for conclusions.

### 3.4 Two kinds of velocity must not be confused

At query time, depth and completeness take priority over short response latency. At campaign-execution time, the owner wants maximum useful delivery velocity, minimal avoidable governance, and no repetitive idle loops. “Quality before speed” for a reading is not permission for an engineering campaign to spend days repeating status checks.

## 4. Required product outcomes and retained boundaries

The approved completion program requires ten connected outcomes:

1. Discover meaningful outputs, relationships, prerequisites, limitations, and drill paths—not merely tool names.
2. Keep the capability catalogue synchronized with descriptor, handler, output, relationship, producer, and channel changes.
3. Give required supported routes executable, chart/build-correct availability evidence.
4. Use the existing deep reasoning model policy for interpretive inquiries, with deterministic validation and honest fallback handling.
5. Add retrieval obligations in response to actual evidence, including late-discovered contradictions or temporal prerequisites.
6. Keep planning separate from final astrological synthesis.
7. Deliver every synthesis-visible material finding in an accountable response/register.
8. Share evidence and closure semantics across Portal, managed MCP, and a conforming raw-MCP client.
9. Preserve accepted evidence through pagination, interruption, restart, and cross-instance continuation.
10. Prove the intended release and actual automated acceptance on live traffic.

Important constraints remain:

- Keep L0 global and L1–L5 chart-specific. Preserve the frozen WriterBase/orchestrator interface.
- Preserve canonical L0 vocabulary and L1 fact identity; downstream interpretations reference authoritative facts rather than re-inventing constants or computations.
- Preserve chart/principal authorization, source and build identity, no cross-chart leakage, and replay safety.
- Never edit an already-applied migration or widen privileges merely to obtain a green result.
- Reuse existing registry, lifecycle, models, storage, and queue mechanisms; do not introduce a graph database or new orchestration platform without an evidenced need and explicit approval.
- Do not make unrelated lint cleanup, legacy retirement, broad infrastructure redesign, or whole-layer elevation prerequisites for every planner repair.
- Preserve the fixed acceptance denominator and distinguish deliberately insufficient cases from supported-complete cases.
- Human-expert research is separate and remains `NOT_RUN`; it is not the approved automated product-release gate.
- Keep raw private answers/events and credentials out of Git, public CI, and this handoff.

An arbitrary external AI client cannot be forced to use the planner correctly. The server can expose a governed lifecycle and withhold certified-complete status when that protocol or answer accountability is not satisfied. Managed MCP and a tested conforming raw client are the tractable acceptance surfaces.

## 5. Architecture to understand before reviewing implementation

### 5.1 Data-to-answer flow

```text
L0 knowledge + L1 facts + L2 structures + L3 timing + L4 outcomes + L5 evaluation
                       |
             retrieval descriptors / handlers
                       |
       source-owned Semantic Capability Units (SCUs)
                       |
       deterministic compiler -> immutable knowledge snapshot
                       |                    |
         concepts / relationships      chart/build availability overlay
                       \                    /
                        question + scope
                              |
              AI inquiry proposal + deterministic compiler
                              |
        obligations -> authorized retrieval -> observed evidence
              ^                                  |
              |------ omission / follow-up -------|
                              |
                 qualified closure + synthesis
                              |
        narrative + complete fact register + delivery receipt
                              |
            Portal / managed MCP / governed raw MCP
```

### 5.2 Four different authorities

| Authority | What it establishes | What it does not establish |
|---|---|---|
| Semantic capability declaration/snapshot | What a route can mean, return, depend on, and connect to | That a particular chart/build currently supplies its evidence |
| Availability contract/overlay | Whether the selected route's actual prerequisites are proven for the inquiry context | The truth or usefulness of the eventual interpretation |
| Inquiry Contract and deterministic closure | What obligations/actions are required, accepted, pending, failed, or exhausted | That the final narrative and every evidence part reached the user |
| Response accountability/delivery receipt | What admitted findings were actually represented and delivered | Empirical predictive accuracy or unlimited client compliance |

`COMPLETE` cannot mean merely “the LLM stopped” or “all attempted calls returned.” Required failed/dark/unexplored obligations and an open material frontier prevent supported-complete closure. Evidenced empty results, genuine inapplicability, unavailable data, and failed execution must remain distinct.

### 5.3 SCUs and catalogue maintenance

An SCU is a semantic capability unit, not necessarily one asset or one tool. It carries domains, concepts, inputs, meaningful output families, bindings, producer references, relation edges, pagination semantics, freshness, entitlement, and limitations. The snapshot is a generated derivative, not a second manually authored knowledge database.

The executable capability registry is not the same object as the governance `CAPABILITY_MANIFEST.json`. The latter indexes governed artifacts and canonical paths. Do not use its presence as proof that the inquiry planner sees every meaningful output.

The intended availability vocabulary already supports materialized producer outputs, runtime service probes, authenticated source queries, and compositions of dependencies. A request-specific composition should not be forced into a fabricated single producer digest. Conversely, an adjacent child's receipt cannot prove unrelated direct SQL, another handler mode, or a different sidecar endpoint.

### 5.4 Retained implementation surfaces

The main source areas are:

- `platform/src/lib/retrieval/registry/knowledge/`: semantic types, compiler, editorial review, projections, overlay loading, source-query availability.
- `platform/src/generated/capability_knowledge.snapshot.json` and `capability_estate_census.json`: generated knowledge and census.
- `platform/src/lib/vidhi/inquiry/`: compiler, graph traversal, omission challenger, planning policy, execution session, pagination, lifecycle, managed jobs, response accountability, channel parity.
- `platform/src/lib/pipeline/` and `platform/src/lib/pariprashna/pipeline/`: planner context, evidence, synthesis, and receipt integration.
- `platform/src/app/api/chat/consult/route.ts` and `platform/src/app/api/mcp/prashna_ask/route.ts`: managed entry points.
- `platform-mcp/src/tools/register_inquiry_lifecycle.ts`, `register_prashna_ask.ts`, and MCP inquiry/job libraries: client-facing lifecycle and managed bridge.
- `platform/scripts/purna/`: real collector, channel clients, cases, answer conversion, external raw-client synthesis, independent judge, and acceptance evaluator.
- `.github/workflows/deploy.yml` and protected database/release scripts: actual delivery controls.

Verify actual caller wiring. The existence of a correct helper or a passing isolated test is not proof that every channel invokes it.

## 6. Campaign lineage: what the plans actually authorized

### 6.1 Foundation and Waves 0–6: September 14

The foundation candidate was branch `codex/planner-knowledge-inquiry`, PR #2597, commit `fccfbb5ab11eadb33259ff987738068753d12ebc`. It introduced the federated SCU model, generated snapshot, chart/build overlay, Inquiry Contract/compiler, managed-channel wiring, raw-MCP lifecycle, and census.

Its original gaps were explicit: 177 of 182 SCUs were conservative descriptor-derived stubs; graph connectivity and public route resolution were weak; pagination proof was limited; chart availability was mostly dark; managed continuation/job durability and actual deployed validation were incomplete.

`CAMPAIGN_DEFINITION.json` authorized a **source-scope campaign under CCD-011**. Its terminal contract was `SOURCE_SCOPE_COMPLETE_WITH_AUTHORITY_BOUND_REMAINDER`; merge, deployment, production mutation, and empirical acceptance were outside that initial authority. The original packet plan was:

| Wave | Intended contribution |
|---|---|
| W0 | Freeze foundation, correct denominators, decompose delivery and ownership |
| W1 | Producer output contracts; route, provenance, pagination, public-door and unavailable-state bindings |
| W2 | Source-linked editorial SCUs; typed concepts/graph and synchronization gates |
| W3 | Intent normalization, traversal, deterministic floors, omission challenge, material-frontier closure |
| W4 | Iterative evidence and complete response accountability |
| W5 | Disposable migration/security/lifecycle proof; three-channel parity and failure behavior |
| W6 | Beyond-Ācārya source acceptance; honest source-scope close and authority-bound remainder |

The original source-only ceiling was legitimate at that time. It should not be retroactively presented as failure to do unauthorized production work. Equally, those historical ceilings must not now be treated as overriding later authorized product completion.

### 6.2 Wave 7 recovery: September 15

The recovery definition addressed receipted transit arguments, semantic quality across six layers, route/overlay/pagination contracts, restart-safe lifecycle, durable jobs, and source acceptance. Recorded source-local results reached the unchanged **34/34 route obligations**, with omission and mutation tests. Disposable database and focused channel tests also passed at their recorded revisions.

Those results were valuable but explicitly source-local. They were not deployed answer quality, live pagination, cross-instance acceptance, or empirical prediction evidence.

### 6.3 Live wrap-up and CCD-012: September 15–16

The Native subsequently authorized protected live completion. Recorded work includes production-compatible migration rehearsal, protected integration, ownership and signing/RLS canaries, live service delivery, and durable managed-job behavior. A live three-channel exercise established shared active snapshot/build identity and honest unavailable obligations.

The resulting status was `TECHNICAL_DELIVERY_COMPLETE_WITH_EXTERNAL_ACCEPTANCE_GATES_OPEN`. Matching unavailable states did not prove deep answered inquiries, full semantic parity, live route replay, or user-value acceptance.

### 6.4 Product-completion successor: September 17

The owner explicitly replaced human-expert recruitment as a product-release prerequisite with deterministic checks plus independent automated answer assessment. Human empirical research remained separate. A new execution task was approved to avoid perpetuating the predecessor's operating pattern.

The governing implementation plan is `docs/superpowers/plans/2026-09-17-purna-product-completion-v2.md`. Its header still says DRAFT/AWAITING APPROVAL, but the later protocol, successor matrix, takeover record, and user-approved task execution establish adoption. This stale header is a reconciliation issue; it is not, by itself, a reason to ask the Native to approve the whole campaign again.

The approved goal is:

> Complete and deploy Madhav's existing planner and inquiry campaign to PRODUCT_DELIVERY_COMPLETE_AUTOMATED_ACCEPTANCE: all supported catalogue capabilities accounted for with executable evidence contracts; deep reasoning and evidence-driven continuation operational; every synthesis-visible material fact delivered in an accountable response; Portal, managed MCP and governed raw MCP pass the original five/34-route corpus plus 30 product scenarios; pagination, interruption and cross-instance recovery pass; protected release is verified on live traffic; existing campaign records match the result. Preserve prior accepted work and required safety controls. Do not stop at a PR, green CI, source readiness, dark-state agreement, an acceptance harness, or an external-blocker report while independent in-scope work remains.

### 6.5 The nine implementation packages

| Package | Required exit—not merely activity |
|---|---|
| Task 0: takeover/baseline | One owner, approved goal, correct isolated worktree, fixed denominator, reconciled evidence |
| Task 1: real collector first | Actual successes/failures from all three channels, bound to chart, source, configuration and receipts |
| Task 2: shared release readiness | Aggregate preflight and genuinely earned protected delivery, or a precise isolated external dependency |
| Task 3: useful capability availability | Required routes actually usable with correct dependencies; all bindings accounted without denominator reduction |
| Task 4: deep adaptive planning | Real reasoning-enabled interpretive planning and a useful later-hop action learned from observed evidence |
| Task 5: fact accountability | Every material synthesis-visible finding delivered, including the 200th-fact omission regression through serialization |
| Task 6: pagination/recovery | Actual exhaustion and process/instance continuation with accepted evidence preserved |
| Task 7: independent assessment | Frozen answers pass deterministic gates and independent four-axis evaluation |
| Task 8: live close | Intended release serving traffic, separate live acceptance, bounded observation, compatibility disposition and reconciled records |

The plan specifically said **collector first; one canonical question before broad catalogue expansion**. It recommended a coordinator with at most two file-disjoint workers, independent review at meaningful integration/security boundaries, cohesive PRs, and no new governance framework.

### 6.6 Transfer to Product Completion II: September 19

The previous product-completion task stood down and preserved its worktree. The successor started from protected `4adcf04978757d2f8e8157492f1922f8b5fb92e3`, which contained PR #2681. The handoff recorded 152 availability contracts, source-only 34/34 acceptance, and no completed candidate/live 5+30 product corpus.

The currently relevant task is `Madhav — Planner & Inquiry Product Completion II`, ID `01a0b7d8-9a90-74f3-aab9-80014919f8b2`. Its initial campaign branch was `codex/purna-product-completion-v3`; later packets use dedicated worktrees/branches. Do not assume the task's registered working directory contains the latest integration candidate.

### 6.7 Production-delivery priority redirect: September 19–20

A real delivery defect took priority: a workflow could conclude success while intended migrations and deployment jobs were skipped. The campaign recorded production at `93a3a5eb8…` with protected main 65 commits ahead. Ownership/cutover prerequisites and the terminal deployment signal needed repair.

The corrected release path required intended mutation jobs to succeed and verified actual serving revisions. Historical recorded delivery reached `66b962f…` and then `09d99894…` across web/MCP/sidecar, with protected ownership/migration evidence. These were necessary repairs, not merely paperwork.

### 6.8 Real collection, upstream gaps, and current stop: September 20–22

The initial wealth collection exposed real failures: stale expected web revision, an incompatible managed-MCP scope, and raw-MCP blocked closure without an accountable answer. Repairs landed for chart binding, request deadlines, per-door revision tracking, and retention of failed evidence.

The attempted next step then encountered unresolved evidence-store designation/current chart-grant proof, a genuine missing wealth near-miss dependency, dasha receipt/build uncertainty, and PR integration/check failures. Independent source work continued until all 186 bindings were accounted for. On September 20 at 14:25:05 UTC, the task reported the goal blocked.

The September 22 task snapshot was idle. The monitor remains active, but the inspected history shows repetition rather than resumed implementation. Other L3 work has advanced meanwhile; its changes must be reconciled, not assumed to resolve the Pūrṇa blockers.

## 7. The acceptance contract—preserve it exactly

### 7.1 Original five cases and 34 route obligations

The immutable cases are:

1. `wealth_mechanism_timing_contradiction`
2. `career_bhava_varga_timing`
3. `marriage_varga_cancellation_timing`
4. `house_yoga_later_hop`
5. `long_divisional_continuation`

Their corpus fingerprint in `PRODUCT_ACCEPTANCE_PROTOCOL_v2.json` is `240e78a554b562b481aaebb907eeb93856a58f1d21676cfb498e8f9b09547111`. The original **34 obligations are a route denominator**, not 34 additional cases.

### 7.2 Thirty additional product scenarios

Six families each have five modes:

| Family | Required domain depth |
|---|---|
| Wealth/business | Natal promise, mechanisms, strength, vargas, cancellation/inhibitors, timing and strain |
| Career/promotion | Profession/bhāva-lord links, D10, strength, yoga, period/transit context and contradictions |
| Marriage/relationships | Houses/lords, kārakas, D9, cancellation, competing indications and timing |
| Children/family | Relevant houses/lords, D7 where applicable, strength, inhibitors and qualified family-event timing |
| Health/wellbeing | Vulnerability/resilience, Bhāvat Bhāvam, relevant vargas, timing and medical boundaries |
| Life events/yoga manifestation | Event provenance, frozen chronology, structural mechanisms, cancellation, trigger windows and counterevidence |

For each family the five modes are: focused fact; deep family inquiry; cross-domain/contradiction; time-bounded inquiry; deliberately insufficient evidence. Actual executable IDs are `wealth_1`–`wealth_5`, `career_1`–`career_5`, `marriage_1`–`marriage_5`, `family_1`–`family_5`, `health_1`–`health_5`, and `events_1`–`events_5`.

Total: **35 cases × 3 doors = 105 candidate executions, plus a separate 105 live executions**, with corresponding assessment. Failed diagnostic runs do not become accepted cases. Candidate results cannot simply be relabelled live after promotion.

### 7.3 Quality and hard gates

The planned independent evaluator scores relevance, evidence-based explanation, contradiction handling, and appropriately specific usefulness on 1–5 scales. Each dimension must average at least 4/5; no answer may score below 3/5 in any dimension.

Deterministic failures override model scores: wrong chart/date/fact, missing required evidence, unresolved citations, incomplete material-fact register, authorization failure, or false closure all fail the case. The evaluator must not see branch labels, desired verdicts, prior scores, or implementer rationales that could bias it.

Supported-complete cases cannot pass through a graceful refusal. Deliberately insufficient cases must identify the correct missing evidence and produce a bounded answer. Do not fabricate life events, near-miss rules, or positive yoga fixtures to make the suite pass.

The user has approved automated product acceptance, not unlimited spending or new access grants. Existing authorized capacity and principals apply. A missing external prerequisite needs one concrete request, not repeated generic “approval pending” messages.

## 8. What has genuinely been achieved

### 8.1 Architectural and source foundation

The record supports preservation of the following:

- Descriptor-owned semantic knowledge and deterministic generated snapshots.
- Source-linked editorial coverage replacing the original routing stubs.
- Typed concept universe and integrity/disposition checks.
- Chart/build overlay and explicit availability contract families.
- Inquiry obligations, deterministic floors, omission challenge, frontier/closure rules, and raw server-authorized lifecycle.
- Durable-session/job implementations and disposable database/security tests.
- Response fact-register and completeness-validation machinery.
- Source-local Beyond-Ācārya regressions, including omission/ablation checks.
- Reasoning policy source selecting `planner_deep` with `reasoning: 'enable'` for interpretive depth.
- Real collector, channel clients, judge/evaluator interfaces, raw external-synthesis handling, fixed product cases, and anti-fixture/anti-false-live checks.

These should not be discarded wholesale. The review must establish which paths are actually integrated and behaviorally effective, and repair only the demonstrated delta.

### 8.2 Source coverage trajectory

| Checkpoint | Source observation | Meaning |
|---|---|---|
| Original foundation | 5 editorial SCUs, 177 conservative stubs; limited exact links and pagination | Useful scaffold, not complete knowledge |
| September 17 audited baseline | 12 explicit availability contracts, 13 dark entries | Large practical availability deficit |
| September 19 transfer | 152 explicit contracts | Major source-contract expansion, still no product corpus acceptance |
| Previous strategy status | 166 contracts, 15 dark, 5 unclassified bindings | Continued inventory progress |
| September 22 inspection of final September 20 candidate | 167 contracts, 19 dark, 0 unclassified | Accounting complete; required unavailable routes remain unresolved |

Historical counts use their stated denominators and revisions. The portfolio identity count of 129, formal receipt denominator of 128, current active producer denominator of 128, SCU denominator of 182, and executable-binding denominator of 186 are **different sets**. Do not mix them to manufacture a progress measure.

### 8.3 Recent protected changes

| PR | State at review | Contribution |
|---|---|---|
| #2694 | Merged | Domain-reading availability evidence |
| #2696 | Merged | Wealth evidence provenance fencing |
| #2697 | Merged | Wealth inquiry acceptance evidence hardening |
| #2698 | Merged | Judgment contract provenance alignment |
| #2699 | Merged | Bind collected evidence to the approved chart |
| #2700 | Merged; L3-owned | Restore orchestrator metadata grants for `data_plane_builder` |
| #2701 | Merged | Bound Portal SSE body collection |
| #2702 | Merged | Bind expected/observed revisions separately by channel |
| #2703 | Merged | Retain incomplete/failed collection receipts without accepting them |
| #2704 | Open | Narrow Pūrṇa golden/source-artifact alignment on the L3 branch |
| #2705 | Open, blocked | Domain composite/source-query contracts and honest unavailable-state accounting |

PR URLs use `https://github.com/Marsys-Technologies/Madhav/pull/<number>`.

### 8.4 Current #2705 improvements

The candidate includes source-local derived contracts for career, health, and marriage assessments; exact Sutravali query contracts; spine-bundle dependencies; LEL intake queryability; and the raw yoga-activation binding's attachment to its existing exact probe.

It also corrects a material truthfulness defect: classical-attribution lookup had delegated to a retired source through an always-empty success stub. It now reports `CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE` rather than silently pretending to have found no attributions.

This is useful work. However, replacing an unavailable feature's misleading success with an honest failure does not complete the user requirement. Required replacements still need owners and implementation paths.

### 8.5 Real delivery repairs

The campaign recorded a genuine repaired protected-release chain: earned deployment outcome, strict ownership/isolation checks, routine migration verification, signing/RLS candidate canary, and actual service promotion. Migrations 1040/1041 and owner markers were historically attested at the corresponding release; this review did not re-query their SQL state.

These controls prevented falsely reporting deployment and cross-owner access. Their existence is not inherently governance overkill. The question is whether the execution process made their application more serial, repetitive, or broad than necessary.

## 9. Fresh operational state and preservation points

### 9.1 Source and PR identities

Fresh remote protected-main tip: `c58e86662e692e678f64934f1689ccaa0fdcd7d7`.

| Surface | Exact identity | Fresh state |
|---|---|---|
| Pūrṇa #2705 | `34991645b1d57926d97ac027d6fca59d8c2ecb53`, `codex/purna-wealth-near-miss` → `main` | OPEN/BLOCKED |
| Pūrṇa correction #2704 | `889ceaf9b7bb37e3699c921589498289d2e5aee5`, `codex/purna-pr2695-golden-alignment` → `codex/madhav-l3-claude-code` | OPEN/CLEAN; clean is not reviewed or merged |
| L3 #2695 | `5d8252dbefc053f9faa92aab693ad46310e0c5c5` → `main` | OPEN/BLOCKED |
| L3 #2709 | Dispatcher digest-path fix | MERGED September 21; overlaps part of #2695's purpose, not proof the entire old PR is resolved |

L3 documentation/readiness PRs #2706–#2712 have also moved main since the Pūrṇa candidate stopped. In particular, #2706 scopes campaign audit SQL to its frozen definition revision. This review did not audit the full L3 campaign; these changes are reconciliation inputs, not Pūrṇa acceptance.

### 9.2 Actual serving revisions on September 22

| Service | 100%-traffic revision | Revision-level `NIRMANA_DEPLOYED_SHA` |
|---|---|---|
| `amjis-web` | `amjis-web-probe-5ff0030f398d-35717960147-1` | `5ff0030f398dd1ef97ffc381005c8a1f2e600329` |
| `amjis-mcp` | `amjis-mcp-probe-09d998940069-35484057404-1` | `09d998940069e00a4f09df60a03c3d07d6536ecf` |
| `amjis-sidecar` | `amjis-sidecar-probe-09d998940069-35484057404-1` | `09d998940069e00a4f09df60a03c3d07d6536ecf` |

Project: `madhav-astrology`; region: `asia-south1`.

The newest web revision does not mean #2705 is deployed—it is unmerged. The ledger's September 20 web SHA `20f4d02d…` is now historical. Do not repeatedly force every component to a matching SHA merely for cosmetic uniformity. Determine required source/configuration compatibility, pin each component, and test the shared protocol/snapshot behavior. If a same-release deployment is required by the chosen acceptance contract, execute and prove that explicitly.

### 9.3 Current CI blockers

The latest #2705 head has two failing check categories:

1. **Unit Tests**, run `35515731646`, job `106091234309`: observed failing tests include `branch-deep-dive`, `branch-completeness-receipt`, and two Beyond-Ācārya v5 current-report/artifact assertions. The campaign records classify four failures as the narrow #2704 golden/provenance dependency.
2. **Fact-Category Pinning Gate**, same run, job `106091234247`: actual log findings include `source_query_availability.ts` and several L1 handler sites such as `get_tajik.ts` and `get_yoga_dosha.ts`.

The agent describes the scanner findings as inherited and involving zero-row probes. That is **not a complete independent disposition**: the fresh log spans both probe code and handler selectors. Review each category against the intended rule. A zero-row queryability probe, a multi-row set query, and a single-row category-only selector have different semantics. Do not globally disable the scanner or impose an arbitrary `fact_key` that falsifies an intentionally multi-row query. Equally, “inherited” does not resolve a required blocking check.

The latest recorded broad candidate unit result before the final documentation head was 12,441 passing tests with four failures. Treat that as revision-bound CI evidence, not the quality score of the product or a newly rerun suite.

### 9.4 Worktrees and uncommitted material

| Location | Role / caution |
|---|---|
| `/Users/Dev/.codex/worktrees/0ee2/Madhav` | Product-strategy workspace; contains unrelated pre-existing dirty/untracked strategic documents. This handoff is authored here. |
| `/Users/Dev/.codex/worktrees/a4c6/Madhav` | Registered successor-task workspace; not necessarily its latest implementation branch. |
| `/Users/Dev/.codex/worktrees/purna-wealth-near-miss/Madhav` | Current #2705 source/evidence branch, at `34991645b…` |
| `/private/tmp/purna-pr2695-audit.m8Qu23` | Located #2704 audit branch worktree at `889ceaf9…`; resolve again before use |
| `/Users/Dev/.codex/worktrees/purna-overnight-acceptance/Madhav` | Historical live config and failed collection artifacts; preserve, do not reuse blindly |
| `/Users/Dev/.codex/worktrees/23e4/Madhav` | Preserved prior product-completion executor; not a fresh execution baseline |

The #2705 worktree has two unfinished local test changes not included in the PR:

- Modified `platform/src/lib/retrieval/registry/layers/__tests__/register_d9_judgment.integration.test.ts`, replacing the old expected `not_computed` near-miss state with a desired `served` state and count.
- Untracked `platform/src/lib/retrieval/registry/layers/__tests__/register_d9_judgment.near_miss_contract.test.ts`, a source-level regression rejecting the hardcoded `not_computed` branch.

These are preserved failing/aspirational regressions, **not an implemented near-miss solution**. Do not delete, blindly stage, or present them as passing delivered behavior. A reviewer checking only GitHub will miss them.

## 10. What remains: outcome-level work register

This is a review snapshot, not a new competing campaign ledger. Reconcile changes into the existing matrix if a later execution plan is approved.

| ID | Remaining outcome | What currently stops it | Required proof / decision | Suggested accountable role |
|---|---|---|---|---|
| R-A | Integrate the valid current candidate | #2705 checks; #2704 stack on a separate L3 branch; newer main | Exact-head semantic comparison, narrow golden integration, precise scanner disposition, protected checks | Pūrṇa integrator with L3 coordination |
| R-B | Establish a valid acceptance environment | Restricted evidence-store designation and fresh existing chart-grant verification not recorded | Named store/access/retention policy; verified authorized principal/chart; versioned per-door config | Release/privacy authority plus Pūrṇa collector owner |
| R-C | Complete wealth evidence | `notably_absent_yogas` permanently `not_computed`; selected-build L2 near-miss evidence missing | Agreed candidate/rule/admission semantics, authoritative inputs, persisted build-scoped evidence and truthful consumer | L2 owner and Pūrṇa consumer owner |
| R-D | Restore dasha-backed temporal consumption | Guarded replacement/build/receipt/freshness state not proven recovered | Right-owner live read, completed intended build, matching receipts/freshness, actual guarded consumer succeeds | Data-plane/L3 build owner |
| R-E | Make required unavailable routes useful | Nineteen dark bindings include strength, portraits, PACT, transit and synthesis paths | Requirement mapping; correct contracts or actual implementation; live/candidate evidence | Pūrṇa plus exact producer/service owners |
| R-F | Establish semantic depth, not just catalogue membership | Isolated-SCU and coarse-output questions remain despite dispositions | Output-family/use-case coverage, novel-chain retrieval, adversarial omission tests | Semantic/planner reviewer and implementer |
| R-G | Prove deep adaptive planning | Source policy present, candidate/live outcome not earned | Provider request reasoning evidence and a useful late-hop retrieval from observed data | Inquiry owner |
| R-H | Complete answer delivery | Accountability matrix remains in progress | Real synthesized answer + complete fact manifest; 200th-fact removal fails through each channel | Synthesis/delivery owner |
| R-I | Prove pagination/recovery at actual boundaries | Source/disposable evidence exists; deployed proof open | Required route exhaustion, crash/restart/cross-instance continuation and durable results | Lifecycle owner |
| R-J | Earn candidate automated acceptance | No accepted full corpus | 105 real candidate executions, deterministic gates and independent assessment | Acceptance owner |
| R-K | Earn live close | No accepted live corpus; compatibility/release proof must be current | Separate 105 live executions, final compatibility census, bounded observation, consistent records | Integrator/release owner |

Historical residual IDs PA-R01–PA-R13 remain intact. This review's R-A–R-K labels are explanatory, not replacements. The matrix still records live route replay (PA-R03), recovery (PA-R04), semantic parity (PA-R07), automated answer acceptance (PA-R08), pagination (PA-R11), and compatibility disposition (PA-R12) as incomplete or partial.

### 10.1 Evidence store and chart authorization: exact issue

The old config resides under `verification_artifacts/purna/live-config-20260920.json` in the overnight-acceptance worktree. The ledger says its expected revision is stale and the chart once called synthetic actually corresponds to a named operator. Do not copy that misclassification into a new run.

The ledger identifies a pre-existing probe principal and historical chart-view grant, but no fresh run-bound verification. It also records an existing GCS prefix without an approved restricted-access/retention designation, and an alternative bucket with broad legacy access.

This review did not independently audit bucket policies or query grants. The reviewer should determine whether an already-authorized, existing store can be formally designated and verified with a narrow action, or whether one explicit administrative decision is required. A broad security program should not be invented. Nor should private evidence be put in an unverified bucket merely to avoid that decision.

No permission or consent can be created by writing an approval-looking string into a config. A suitably labelled authorized synthetic fixture can support candidate tests, but it does not erase the separate live/real-evidence obligations.

### 10.2 Wealth near-miss dependency: exact issue

The consumer's source still contains `unit: 'notably_absent_yogas'` with `state: 'not_computed'` in `register_d9_judgment.ts` around line 1684 at the inspected head. This is not a temporary transport error.

The campaign investigation records that L0 has rules/citations, L1 firing storage contains fired rows rather than a complete classified non-firing universe, and L2 lacks the required selected-build near-miss band. A missing firing row is therefore not sufficient evidence of a significant absence or near miss.

The needed domain contract must specify:

1. Which yoga candidates and classical sources are eligible.
2. How prerequisites, partial satisfaction, cancellation, and missing inputs are classified.
3. What makes an absence materially notable; any threshold must be justified rather than guessed.
4. How method/frame/build identity and source fact IDs are retained.
5. What the persisted output and freshness/receipt contract are.
6. Which answers require the band and how unavailable evidence is represented.

Review whether the current consumer requirement faithfully reflects the approved product promise and whether its scope is overbroad. If a requirement needs amendment, propose it transparently to the Native; do not relabel the missing implementation `not_applicable` to pass the test. If the existing requirement is valid, attach an exact producer-owner packet instead of leaving a permanent “upstream” note.

### 10.3 Dasha/build dependency and L3 coordination

The supplied L3 cross-campaign notice identified missing builder-role access to orchestrator metadata after ownership changes. PR #2700 added narrowly scoped grants. The notice also identified a hardcoded foreign-worktree writer-digest path and an ayanamsha default mismatch in #2695.

Merge of a grant migration does not prove it applied, that a rebuild finished, or that `ga_dashas_replacement_in_progress` is safely resolved. The consumer is designed to refuse stale/mismatched state. Do not clear that guard or bypass the reader. Establish the real build/asset/receipt/freshness chain through the appropriate owner.

Since #2709 separately merged the dispatcher-path repair, #2695 now needs an exact remainder/overlap review. Neither cherry-pick the entire old branch nor assume all its work is superseded. Historical migration allocations were Pūrṇa 1042–1069 and L3 1070–1119; refresh coordination before any future allocation or application. Applied 1033–1041 are not editing targets.

## 11. The nineteen deliberately unavailable bindings

These are extracted from the candidate snapshot, not invented backlog. The review must classify each as a required product dependency, a legitimate non-answer planning/resource capability, an optional feature, or an actual unsupported implementation. Every classification needs a requirement mapping; “dark” is not automatically a valid final disposition.

| Binding / SCU suffix | Recorded reason | Independent review focus |
|---|---|---|
| `call_transit_search` | No dedicated authenticated route-specific sidecar probe | Can the existing approved service-probe family cover the actual route? |
| `channel_chat_dispatch` | Descriptor reports pending registry migration; static introspection | Separate this descriptor's meaning from the actual Portal caller path; do not infer all Portal dispatch is absent. |
| `channel_mcp_wiring` | Static five-entry wiring map | Generate from real bindings if needed; do not treat introspection as execution. |
| `classical_attribution_lookup` | Retired attribution source; no replacement | Preserve newly honest failure, but identify the canonical replacement for required citations. |
| `compose_large_n` | Mandatory gestalt path includes uncontracted tail-watch | Contract the whole material chain or expose qualified components without false completeness. |
| `get_av_transit_gating` | Both chart-fact and sidecar Kakshya modes need coverage | Prove each material mode; avoid all-or-nothing denial of independently proven modes unless required. |
| `get_strength` | One total-strength receipt does not cover 21 categories and frame inputs | Obtain exact category/frame coverage without shrinking required output or inventing proof. |
| `graha_portrait` | Mandatory strength child incomplete | Repair the shared strength dependency rather than repeatedly fencing every parent. |
| `intent_classify` | Returns a prompt template, not a model classification | Is prompt rendering its legitimate declared capability? Distinguish a prompt resource from a missing execution service. |
| `maro_mcp_surface` | Static unmeasured profile-derived surface | Determine whether it belongs in answer-evidence readiness at all. |
| `maro_orchestrate` | Static profile selection, not measured execution | Separate planning metadata from claimed orchestration execution. |
| `maro_profiles` | Resource explicitly labels profiles unmeasured | A dossier can be valid as a dossier without proving performance; preserve that type distinction. |
| `pact_query` | Judgment, direct varga SQL, dasha, and transit-trigger stages lack one complete chain contract | Inspect actual stage obligations and errors, not only child availability. |
| `query_muhurat` | Writer self-test is not proof of the distinct authenticated sidecar endpoint | Require route-specific dependencies/probe; preserve practice-specific semantics. |
| `query_planet` | Mandatory strength facet incomplete | Shares root cause with strength and portrait; group repair. |
| `route` | Produces a plan but does not execute its trajectory | Planning output may be its purpose; do not demand synthesis as a condition of planner usability. |
| `synergy_cross_layer` | Direct-DB whole-chart composition lacks full contract | Cover actual reads and transformations; reuse common chain proof. |
| `synergy_pipeline` | Same direct-DB composition; dry-run is a plan | Separate dry-run planning and executed evidence modes. |
| `tool_search` | Process-local catalogue search lacks deployed-process receipt | Avoid circularity where discovery cannot reveal routes because discovery itself needs the unavailable route proof. |

The final rows are especially important: **a uniform evidence gate may be misclassifying unlike capability kinds**. This is a hypothesis, not an instruction to weaken provenance. The original product explicitly separates planning from synthesis; the availability model should preserve that separation too.

## 12. Why progress has been slow: evidence and hypotheses

### 12.1 Product proof arrived too late

**Observed:** extensive source coverage and source-local acceptance preceded the first real three-door wealth attempt. The September 17 plan explicitly called for the collector and one working inquiry first. The latest full candidate/live corpus is still not earned.

**Hypothesis:** the campaign optimized for individually provable components and catalogue closure more than an early vertical product slice. This delayed exposure of ordinary integration defects—wrong scope vocabulary, stale run revision, missing evidence storage, and permanently unmet judgment obligations.

**Test:** reconstruct when the first runnable collector, valid config, real synthesized answer, and complete fact delivery each became available. Compare that to the number of catalogue/contract batches and broad CI cycles before the first attempt.

### 12.2 Accounting can conceal unresolved product work

**Observed:** 186/186 bindings are accounted for, while 19 remain dark. The graph has 156 isolated SCUs that are all formally dispositioned, and only five descriptors are classified exhaustible.

**Hypothesis:** “zero unexplained gaps” became an intermediate optimization target with weak coupling to consumer value. Dispositions can correctly explain a limitation while leaving the original requirement wholly unsatisfied.

**Test:** map every required scenario/evidence dimension to actual output families, graph/drill paths, available handlers, and delivery checks. Determine which dispositions are sufficient and which are unfinished implementations.

Do not assume every SCU must connect to every other SCU or every bounded route must paginate. More edges or pages are not inherently better. The test is whether material inquiry paths are discoverable and complete for their stated scope.

### 12.3 Required missing data surfaced as a late ownership blocker

**Observed:** the complete wealth path includes a hardcoded uncomputed near-miss obligation. The producer-side rule/admission/persistence contract has not been established in the reviewed record.

**Hypothesis:** consumer completeness was specified before a producer dependency feasibility pass, and there is no operationally effective mechanism for resolving the small necessary upstream change without turning it into whole-layer elevation.

**Test:** determine whether an existing authorized producer path can supply the evidence; otherwise prepare the smallest domain-owner decision and implementation packet with named inputs, outputs, acceptance, and ownership. Do not invent astrology or silently reduce the requirement.

### 12.4 Real release defects caused necessary but expensive diversion

**Observed:** false-green skipped deployment, ownership rearm/bootstrap requirements, schema-USAGE allowlisting, migration configuration, and service-revision drift required actual repairs.

**Hypothesis:** preflight coverage was incomplete, so failures were discovered serially. Some operational prerequisites assumed by the plan—especially approved evidence storage and current grants—were not established as working inputs before repeated live attempts.

**Test:** build a single prerequisite dependency graph from observed failure traces. Identify which inputs could have been validated together before a release attempt, and which genuinely depended on successful prior mutation.

### 12.5 Ownership protection may have become an integration deadlock

**Observed:** Pūrṇa's four-file test/provenance correction is in #2704 against the L3 branch. #2705 remains blocked by corresponding tests; #2695 remains open; a portion of #2695's runtime work has since landed separately as #2709.

**Hypothesis:** the protection against editing another campaign's branch was applied as a reason to wait for a particular branch sequence, even where a narrowly reviewed, coordinated main-targeted correction might remove the dependency. That alternative is not proven safe until exact diffs are compared.

**Test:** compare current main, #2695, #2704, and #2705. Establish substantive versus identity-only changes, choose one integrator, and propose the smallest safe delivery graph. Do not automatically bless regenerated goldens.

### 12.6 Automated activity was mistaken for autonomous progress

**Fresh evidence:** from September 20 14:00 UTC through September 22 12:14 UTC, the task log contains 264 `task_complete` records. Of those, 238 contain heartbeat-formatted responses; 195 match the phrases “No changed external state” or “unchanged and clean.” These are message counts, not a CPU-time or financial-cost measurement.

The task explicitly reported blocked at September 20 14:25:05 UTC. Many subsequent activations took only seconds and repeated the boundary. The monitor prompt nevertheless instructed execution, continuation of independent work, quiet unchanged-state handling, and no campaign-wide stall from a single dependency.

**Hypothesis:** the control loop ceased to maintain an executable independent-work queue. It could detect that a narrow upstream PR was unchanged, but did not demonstrate exhaustion of all source, integration, semantic, lifecycle, or acceptance-preparation work. A heartbeat cannot create authority; it also cannot substitute for a missing owner action.

**Test:** enumerate each remaining outcome, its actual blocker, and all safe tasks that could advance it. Determine whether the blocked goal was justified, whether the external request reached someone able to act, and whether the monitor should have been paused until a meaningful event rather than repeatedly rechecking.

The history also records GitHub API rate limiting during repetitive CI observation. This suggests an avoidable monitoring cost, but this review has not quantified its share of total delay.

### 12.7 Governance: necessary floor versus avoidable overhead

The evidence does **not** support saying all security work was waste. Chart isolation, private evidence protection, immutable migration history, actual deployment verification, and false-completion prevention protect the product's central promise.

Likely avoidable overhead to test:

- Full-suite/CI cycles triggered by small status-record changes while known blockers remained unchanged.
- Many tiny accounting commits and repeated snapshot/census generation before a cohesive integration boundary.
- Repeated narration of unchanged CI states despite explicit anti-stall instructions.
- Stale approval headers, historical source-only ceilings, and current release statuses coexisting without a concise effective-authority summary.
- Treating all scanner findings as a broad governance problem instead of separating exact query/selector classes.
- Recording that an external owner is needed without creating a small actionable decision packet and confirming its receipt.

The remedy is proportional, risk-specific control—not disabling checks, widening roles, hiding failures, or treating every inherited failure as exempt.

### 12.8 Strategic coordination also needs review

Repeated prompts to “continue autonomously” increased urgency but did not necessarily provide the missing evidence-store designation, domain ruling, or owner integration. Some wording may have reinforced over-conservative cross-campaign boundaries. Earlier status reports sometimes emphasized contract coverage even while correctly qualifying it as not acceptance.

The independent reviewer should assess the strategic task's contribution to the problem: unrealistic assumptions about existing resources, incomplete handoffs, confusing old/new authority, insufficiently concrete upstream requests, or too much focus on task activity. Do not place all responsibility on the execution agent or the model.

## 13. Specific architectural concerns deserving independent challenge

1. **Is semantic coverage genuinely below asset/tool level?** An editorial flag on 182 SCUs is not proof that hundreds of meaningful fields, mappings, and relationships inside deep assets are discoverable.
2. **Does the graph support the intended non-obvious chains?** Inspect the 53 edges and isolated-node dispositions against actual questions, not an arbitrary density target. Test Bhāvat Bhāvam, cancellation, varga conflict, and structure–time–event links.
3. **Is availability appropriately typed?** Distinguish a prompt resource, discovery service, plan, static reference, runtime calculation, materialized evidence, and final composite. Avoid both unsupported promotion and unnecessary global darkness.
4. **Are multi-mode tools all-or-nothing?** A missing optional mode should not suppress a separately proven requested mode; a missing mandatory facet must still prevent complete composite status.
5. **Do zero-row source probes prove too little?** They can establish queryability/schema/access, not row completeness, semantic correctness, required joins, or actual useful results.
6. **Does deep model policy reach the provider?** Verify actual adapter requests, fallback behavior, real evidence feedback, and next-action execution—not only a helper returning `planner_deep`.
7. **Can synthesis see and account for every admitted finding?** Distinguish retrieved, admitted, synthesis-visible, cited, and delivered sets. Check facts lost at normalization, budget trimming, streaming, persistence, and client rendering.
8. **Are fact identities stable?** Current golden churn involves order-derived IDs and provenance hashes. Assess whether stable semantic identity can reduce incidental changes without hiding real provenance differences.
9. **Is raw-MCP completeness overclaimed?** Server lifecycle closure and external-agent prose accountability are separate. Inspect the conforming reference client and its actual final answer evidence.
10. **Are closure obligations scoped correctly?** Required unimplemented units can make every answer permanently incomplete; optional or irrelevant units should not be silently mandatory. Any change needs a domain-grounded requirement decision, not a test shortcut.
11. **Is pagination required where evidence is bounded?** Finite horizon closure is different from unbounded table exhaustion. Neither a top-k result nor a full page proves completeness by itself.
12. **Can a new build invalidate accepted readings correctly?** Preserve snapshot-on-consume and build-specific evidence while preventing stale current-answer claims; do not invalidate or rewrite historical delivered readings without their provenance.

## 14. What the reviewer must return

Please produce a cohesive review and execution proposal with these deliverables:

### A. Independent verdict

- What is sound and should be preserved?
- What is incomplete, over-engineered, incorrectly modelled, or insufficiently integrated?
- Which claims in this handoff are confirmed, corrected, or refuted?
- Is the current architecture salvageable with focused changes? If not, identify the precise failed abstraction and smallest replacement—not a blanket rewrite.

### B. Requirements-to-runtime matrix

For each core user outcome: applicable concepts/output families; exact source paths; retrieval bindings; availability state; actual consumer; tests; candidate/live evidence; gap; owner. Include at least the five original cases and the material dependencies of the six product families.

### C. Root-cause and critical-path analysis

Separate producer-data gaps, semantic discovery gaps, handler defects, planner/continuation defects, delivery/accountability gaps, test/integration problems, release configuration, true authority dependencies, and operating-loop failures. Mark confidence and a falsifying check for each major diagnosis.

### D. Elevated execution plan

For each cohesive packet provide:

- Objective and named owner/responsibility.
- Exact files/modules and any producer/service coordination surface.
- Starting branch/worktree assumptions and preserved dirty work.
- Required authority/prerequisites and whether they already exist.
- Minimal failing reproduction and intended repair.
- Tests and exact measurable exit.
- Dependencies and work that can proceed concurrently.
- Integration/release sequence and evidence to retain.
- Stop conditions, recovery path, and next action on failure.
- Rough effort range with assumptions, not an invented finish date.

### E. Concrete decision requests

If external action is indispensable, specify the exact decision: named evidence store and retention/access conditions; principal/chart verification; exact near-miss domain contract; owner approval for a narrow integration; or bounded existing-capacity issue. Avoid “needs governance,” “needs admin,” or “awaiting upstream” without means to resolve it.

### F. An execution control mechanism that will not repeat this stall

Define one integrator, a runnable dependency queue, limited parallel file ownership, meaningful review boundaries, anti-repeat failure rules, and event-driven/bounded waiting. Show how the next work item is selected when one release or upstream dependency is blocked. Define when monitoring is useful and when it should stop awaiting a named external action.

### G. Acceptance and handback

Keep the original 5/34 plus 30-case denominator and candidate/live distinction. If you believe a requirement is wrong, propose a separately visible change with reasons and impact; do not quietly edit it. Return a copy-ready kickoff brief only after the plan is explicit, with no implied authority beyond the Native's later decision.

## 15. Candidate recovery structure to challenge—not pre-approved execution

The following is a proposed direction, deliberately open to improvement:

1. **Reconcile once.** Freeze exact source, open PR relationships, unfinished local tests, current live revisions, and effective authority. Retire stale status assumptions without deleting history.
2. **Resolve the small enabling decisions immediately.** Establish evidence storage/chart access, give the near-miss requirement a named domain owner and decision packet, and settle #2704/#2695/#2705 integration ownership. Do not let these remain vague parallel blockers.
3. **Choose one demanding vertical slice.** Use the original wealth case across all three doors. If its producer dependency cannot be resolved immediately, an additional already-supported case can provide integration feedback in parallel, but it cannot replace the wealth acceptance obligation.
4. **Repair shared roots.** Group strength/planet/portrait, direct-DB composites, service endpoints, discovery/planning types, and source-attribution replacement by common dependency rather than treating each dark row as a separate mini-campaign.
5. **Prove actual intelligence and delivery.** Demonstrate late-hop evidence-driven retrieval, non-obvious required concept coverage, complete fact delivery, and real recovery on the selected candidate.
6. **Expand from a working slice.** Run the fixed candidate corpus; repair measured failures in cohesive batches. Do not expand inventory work as a substitute for executing answers.
7. **Deliver and close.** Protect the intended integrated release, verify the actual component matrix, execute the separate live corpus, perform the bounded observation, and reconcile the existing records.

This sequence should be revised if the independent review finds a more direct path. No new implementation is initiated by proposing it here.

## 16. Preserve, simplify, and do not compromise

### Preserve

- Canonical L0/L1 identities and six-layer ownership.
- Working retrieval handlers, contract types, compiler, lifecycle, and synthesis infrastructure.
- Existing evidence and failed results with their original revision/environment identity.
- Already-earned migration and protected-delivery results; do not rerun one-shot bootstrap casually.
- Original acceptance cases and explicit scientific/empirical limitations.
- Dirty worktrees and unmerged review history until their content is safely reconciled.

### Simplify where evidence supports it

- Use one concise current-state projection with dated history beneath it.
- Review/generate/test at cohesive integration boundaries instead of each accounting edit.
- Group repeated unavailable composites by shared prerequisite.
- Replace polling that cannot change a decision with a named owner action/event.
- Separate semantic correctness from incidental golden identity churn.
- Use the correct proof contract for each capability type instead of requiring every resource to look like a completed inquiry.

### Do not compromise

- Do not hide missing facts, incomplete data, or absent implementation behind polished prose.
- Do not substitute healthy adjacent receipts for the requested route/build/chart.
- Do not lower acceptance scores, remove original cases, or turn supported-complete cases into insufficiency cases without explicit change approval.
- Do not weaken chart authorization, private-evidence protection, replay safety, or protected-release truth.
- Do not infer actual predictive accuracy from test volume, expert-sounding output, or automated rubric scores.

## 17. Review-session operating boundary

The desired Claude Code session is a **review and planning session**. Begin with the repository's `CLAUDE.md` and applicable directory instructions, then use the reading list below. Existing campaign task conversations explain intent and history; governed documents and exact source/runtime evidence establish shared state.

Do not run a second implementation campaign during the review. Do not edit L3 producer code, allocate migrations, modify the active monitor, create a new execution goal, or change PR targets merely because this document identifies a possible improvement. Return the proposed action and its authority needs.

If a bounded non-mutating test would materially discriminate between diagnoses, run it in an isolated review environment and label its evidence. Do not point disposable/reset tests at production or assume a stale historical config authorizes new live calls. Do not retrieve or publish raw private answers merely to make the review more detailed.

The user's objective is a better executable plan after independent scrutiny, not automatic continuation under a different model before that scrutiny is complete.

## 18. Source index and reading order

All paths below are repository-relative unless explicitly absolute. The best current candidate source for this review is #2705 at `34991645b…`; protected main and historical sources differ. Some product/plan headers intentionally preserve their old state and must be read with later decisions.

| ID | Source | Why it matters |
|---|---|---|
| S01 | `CLAUDE.md`; applicable `AGENTS.md`; `00_ARCHITECTURE/ROOT_FILE_POLICY.md` | Canonical instructions, domain principles, placement and ownership rules |
| S02 | `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md` | Product promise, domain depth, complete findings, empirical boundaries |
| S03 | `00_ARCHITECTURE/briefs/nirmana/MADHAV_DEEP_INQUIRY_AND_DATA_UTILIZATION_PLAN_v1_0.md` | Earlier strategic reasoning; historical input, not a substitute for later adopted scope |
| S04 | `00_ARCHITECTURE/briefs/nirmana/MADHAV_PLANNER_CAPABILITY_KNOWLEDGE_AND_INQUIRY_IMPLEMENTATION_v1_0.md` | Original architecture, FC0 implementation, residuals R1–R12 |
| S05 | `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/CAMPAIGN_DEFINITION.json` | September 14 source-only authority, denominators and Waves 0–6 |
| S06 | Same directory, `RECOVERY_DEFINITION_v1.json` | Wave 7 recovery and its historical source-local ceiling |
| S07 | Same directory, `LIVE_RELEASE_AND_COMPLETE_WRAPUP_PLAN_v1_0.md` | Live-wrapup transition and release path |
| S08 | `docs/superpowers/plans/2026-09-17-purna-product-completion-v2.md` | Approved nine-package product completion plan; stale draft header explicitly noted |
| S09 | Campaign directory, `TRANSFER_HANDOFF_2026-09-19.md` | Predecessor stand-down, preservation, exact transfer baseline |
| S10 | Campaign directory, `PRODUCT_ACCEPTANCE_PROTOCOL_v2.json` | Immutable original cases, 30 additional scenarios, product versus research gates |
| S11 | Campaign directory, `LIVE_COMPLETION_MATRIX_v1.json` | Product/source/candidate/live status and PA-R01–PA-R13 |
| S12 | Campaign directory, `CAMPAIGN_STATE.md` and `EVENTS.jsonl` | Detailed chronological evidence; beware mixed historical/current statements |
| S13 | Campaign directory, `AUTONOMOUS_EXECUTION_CONTROL_v1.json` | Anti-stall, queue/release truth, bounded surrogate and authority rules |
| S14 | Campaign directory, `BEYOND_ACARYA_ACCEPTANCE_v2.json` through later versions, including v5 | Revision-pinned source evidence; not live acceptance |
| S15 | Generated snapshot and estate census under `platform/src/generated/` | Recompute exact denominators, source graph and availability dispositions |
| S16 | `platform/scripts/purna/` and its tests | Real collector, frozen cases, raw synthesis, judge, acceptance and coverage |
| S17 | Inquiry/registry/pipeline files in §5.4 | Implementation, actual caller wiring, type-specific availability and closure |
| S18 | PRs #2694, #2696–#2705; latest #2705 CI run `35515731646` | Recent changes, exact-head blockers and unmerged content |
| S19 | L3 PRs #2695, #2700, #2706, #2709 and current coordination record | Cross-campaign seams and possible supersession/overlap |

Useful direct links:

- [Current Pūrṇa candidate #2705](https://github.com/Marsys-Technologies/Madhav/pull/2705)
- [Pūrṇa golden correction #2704](https://github.com/Marsys-Technologies/Madhav/pull/2704)
- [L3 combined correction #2695](https://github.com/Marsys-Technologies/Madhav/pull/2695)
- [Builder grant repair #2700](https://github.com/Marsys-Technologies/Madhav/pull/2700)
- [Separately merged digest-path repair #2709](https://github.com/Marsys-Technologies/Madhav/pull/2709)
- [Current candidate failed checks](https://github.com/Marsys-Technologies/Madhav/actions/runs/35515731646)

### Local operational evidence, if the reviewer runs on this machine

- Task log: `/Users/Dev/.codex/sessions/2026/09/19/rollout-2026-09-19T09-37-01-01a0b7d8-9a90-74f3-aab9-80014919f8b2.jsonl`.
- Monitor definition: `/Users/Dev/.codex/automations/planner-and-inquiry-autonomous-monitor/automation.toml`.
- User-supplied L3 notice: `/Users/Dev/.codex/attachments/aa39402b-85c0-414d-814b-fef469ab4e65/Pasted text.txt`.
- Historical collector config/receipts: overnight-acceptance worktree, `verification_artifacts/purna/`. These are private historical artifacts, not attachment-ready evidence or permission to rerun.

Do not upload the raw task log or private collection directory as a convenient context bundle. Use redacted summaries and exact evidence references. This handoff intentionally avoids secrets and personal chart/event content.

## 19. Safe reproduction and freshness checks

These commands are read-only examples, not an execution authorization. Run in a repository whose identity and instructions have been verified. Refresh exact heads before making conclusions; do not silently mutate a shared checkout to obtain them.

```sh
git status --short
git worktree list --porcelain
git ls-remote origin refs/heads/main refs/heads/codex/purna-wealth-near-miss
gh pr view 2705 --repo Marsys-Technologies/Madhav --json state,headRefOid,baseRefName,statusCheckRollup
gh pr view 2704 --repo Marsys-Technologies/Madhav --json state,headRefOid,baseRefName,files
gh pr view 2695 --repo Marsys-Technologies/Madhav --json state,headRefOid,baseRefName,files
gh pr view 2709 --repo Marsys-Technologies/Madhav --json state,mergeCommit,files
```

Inspect the generated candidate without treating it as live:

```sh
jq '.census' platform/src/generated/capability_knowledge.snapshot.json
jq -r '.scus[] | . as $s | .availability_dispositions[]? |
  select(.status == "deliberately_dark") |
  [$s.scu_id, .binding_id, .reason] | @tsv' \
  platform/src/generated/capability_knowledge.snapshot.json
```

For production delivery, select only safe metadata; never print all environment variables:

```sh
gcloud run services describe amjis-web \
  --project madhav-astrology --region asia-south1 \
  --format='json(status.latestReadyRevisionName,status.traffic)'
```

Resolve the actual traffic-serving revision, not merely the latest created name, then inspect only the deployed-SHA field and image identity. Repeat for MCP and sidecar. A successful workflow and a revision-shaped name are not sufficient attestation.

Useful focused test areas for an isolated review include knowledge availability/overlay contracts, inquiry compiler/omission/planning policy, response accountability/channel parity, lifecycle/pagination, and `platform/scripts/purna/__tests__/`. Verify each test's environment and side effects before running. This document intentionally does not prescribe a production collector invocation using the stale config.

### Verification limits of this handoff

The review refreshed source/PR/check/task/serving metadata but did not re-run the full application suite, independently inspect live chart grants/bucket ACLs, query production build/receipt tables, execute the 35-case corpus, or test the actual rendered evidence UI. Those are named gaps, not implied passes.

## 20. Original kickoff intent, preserved for the reviewer

The approved successor brief instructed the executor to be the sole owner in an isolated worktree, preserve the predecessor, and continue the existing product program rather than rebuild it. Its decisive operational instructions were:

> Your first deliverables are a real three-door evidence collector, one demanding end-to-end inquiry, and a complete release-configuration diagnosis. Resolve the shared release dependency in coordination with its owner while implementing independent product work. Do not idle the whole campaign over one credential. Do not repeat unchanged full deployments.
>
> Complete supported capability evidence contracts, activate the existing deep-planning path, follow new evidence beyond the initial plan, repair web/MCP evidence delivery, account for every synthesis-visible material fact, and prove pagination and durable recovery. Then run the frozen original and additional product cases with actual answers and independent automated assessment, use protected release, verify live traffic and live acceptance, and close existing records once.
>
> Source tests, green CI, a merged PR, a deployed old revision, an offline scorer, matching dark states, or truthful abstention on a supported-complete case are not terminal success. Do not shrink scope or scores to earn a pass. Human-expert scientific research remains separately NOT_RUN and is not this release gate.

The original plan's completion loop was: reproduce the first failing real boundary, repair the smallest reusable cause, verify the affected outcomes, integrate, and select the next runnable item. After two identical failures, investigate rather than repeat. After roughly 60–90 minutes without a working increment, reduce the slice or obtain a concrete executable reproduction. These were intervention triggers, not permission to weaken tests.

The originally stated planning allowance was approximately 4–7 focused engineering days plus shared-release external wait, to be revised from the first real inquiry. It was not a guaranteed calendar deadline. The appropriate review is whether work was sequenced to obtain that early information and use it—not merely whether a date slipped.

## 21. Copy-ready request for the Claude Code review session

Read this handoff and the referenced governing product, implementation, acceptance, and current-state documents. Review Pūrṇa Anveṣaṇa independently, starting from the Native's actual consumer requirements rather than the current agent's preferred architecture or status labels. Verify the exact current main and open PRs, preserve dirty work, and distinguish source evidence, candidate execution, live delivery, automated answer acceptance, and empirical research.

Investigate why substantial engineering and complete catalogue accounting have not produced accepted end-to-end inquiry. Challenge the semantic graph, type-specific availability model, producer dependencies, deep-planning integration, complete fact delivery, actual recovery, release/configuration prerequisites, cross-campaign ownership, CI coupling, and autonomous control loop. Explicitly assess whether safe in-scope work remained when the campaign declared itself blocked, and whether strategic instructions contributed to the stall.

Return the deliverables in §14: an evidence-backed verdict; requirements-to-runtime matrix; root-cause analysis; preserve/change/remove decisions; a detailed, dependency-ordered completion plan with exact means, owners, files, tests, measurable exits, narrow authority requests, and anti-stall rules; and a proposed kickoff brief. Preserve the original five cases/34 obligations plus 30 scenarios, with 105 candidate and 105 live executions. Do not infer empirical astrology validity from automated acceptance.

This session is review and planning only. Do not implement, merge, deploy, mutate production, change IAM/secrets, alter the active Codex task, or take over execution. The Native will review your proposal in the product-strategy session before authorizing the next execution step.

### Glossary

- **Native:** product owner and final decision authority in this project.
- **Pūrṇa Anveṣaṇa:** planner knowledge and complete-inquiry campaign.
- **SCU:** Semantic Capability Unit—an addressable semantic contribution with executable/semantic bindings.
- **Binding:** a specific route/channel connection; not synonymous with an asset or SCU.
- **Dark:** unavailable under the current proof/admission contract; not necessarily nonexistent data, and not automatically a completed requirement.
- **Overlay:** chart/build-specific availability over the immutable semantic snapshot.
- **Three doors:** Portal/Paripraśna, managed MCP, and governed raw MCP.
- **Receipt:** machine-checkable record supporting a specific claim; it proves only what its detector and bound inputs actually establish.
- **Candidate acceptance:** actual isolated intended-release execution, not a unit fixture.
- **Live acceptance:** separate execution through verified serving channels.
- **Empirical research:** evaluation of interpretive/predictive claims beyond engineering and automated product acceptance; separately not performed.

---

**Handoff disposition:** Prepared for independent review. No campaign implementation, task resumption, PR mutation, deployment, or authority expansion was performed while producing this document. Existing campaign records and unrelated local changes were preserved. This document is a dated review input, not a second live campaign ledger or a claim of completion.
