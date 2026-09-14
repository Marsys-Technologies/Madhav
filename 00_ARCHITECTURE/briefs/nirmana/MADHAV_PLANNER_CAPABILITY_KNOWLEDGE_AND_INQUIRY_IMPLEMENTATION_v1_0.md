---
artifact: MADHAV_PLANNER_CAPABILITY_KNOWLEDGE_AND_INQUIRY_IMPLEMENTATION
version: "1.0"
status: "IMPLEMENTED BRANCH CANDIDATE — reviewed locally; not merged, deployed, migrated, or production-verified"
produced_on: 2026-09-14
decision_owner: Native
implementation_branch: codex/planner-knowledge-inquiry
source_baseline: b1a0f17eb65494f21a00fd2b22d6264da76c3c38
strategy_parent: MADHAV_DATA_PLANE_STRATEGIC_LEDGER_v1_0.md
product_parent: ../../MADHAV_PRODUCT_DEFINITION_v3_0.md
historical_input: MADHAV_DEEP_INQUIRY_AND_DATA_UTILIZATION_PLAN_v1_0.md
scope: "Planner-facing federated semantic capability knowledge, immutable snapshot, chart/build overlay contract, Inquiry Contract/compiler, managed-channel wiring, raw-MCP lifecycle, evidence receipts, estate census, tests and CI"
non_authority: "No merge, deployment, production data access/write, migration application, credential change, infrastructure change, build dispatch, or product acceptance"
---

# Planner capability knowledge and complete inquiry implementation

## 1. Outcome and exact status

This branch implements a candidate foundation for the data-plane requirement that Madhav investigate through explicit semantic obligations rather than infer completeness from a flat list of tools. It preserves the six-layer producer architecture and the live retrieval registry. It does not create a seventh truth store.

The implementation has five connected parts:

1. Federated Semantic Capability Unit (SCU) declarations live beside the registry descriptors that own the executable routes.
2. A deterministic compiler joins those declarations to the live registry and emits a sorted, immutable, SHA-256-addressed capability snapshot.
3. A chart/build overlay contract records per-chart availability independently of the semantic snapshot.
4. A versioned Inquiry Compiler creates obligations, executable plan items, omission findings, a material frontier, and deterministic closure state.
5. Portal, managed MCP, and raw MCP use the same Inquiry Contract core. Raw MCP gains a principal-bound, server-executed, durable lifecycle instead of accepting caller-authored completion claims.

This is source-tree implementation evidence only. Migration 1033 was reviewed but not applied. No endpoint was deployed or called against production. The generated estate census explicitly declines to resolve deployed current output-spec rows.

## 2. Strategic lineage and preserved boundaries

This work implements a bounded portion of DP-SD-008 and DP-P8 in the strategic ledger: retrieval, adaptive inquiry, managed delivery, and raw MCP are treated as one data-to-answer chain. It also implements the historical deep-inquiry plan's revisable obligation set, independent omission challenge, explicit frontier, and fail-honest closure mechanics. The historical plan remains historical; this brief does not silently promote its other proposals.

Preserved boundaries:

- L0–L5 writers and their storage remain the owners of facts, structures, timing, manifestation, and evaluation.
- `CapabilityDescriptor` remains execution truth. The D1 change is optional amendment 5, adding only `semantic_capabilities`.
- The compiled snapshot is a derived artifact/cache, not an authoring database.
- Chart/build state never mutates the immutable semantic snapshot.
- The planner decomposes and associates; it does not produce the final astrological interpretation.
- Calibration-only L5 descriptors remain excluded from planner addressability.
- Existing safety, chart authorization, no-leakage, cost-cap, and synthesis boundaries remain in force.

## 3. Architecture

```text
descriptor-owned SCU fragments ─┐
live CapabilityDescriptor catalog├─> deterministic SCU compiler
                                │      ├─ immutable knowledge snapshot
                                │      ├─ edge/integrity report
                                │      └─ bounded planner projection
asset/output authorities ───────┘              │
                                               v
question + scope + optional internal AI proposal
                   └─> Inquiry Compiler
                        ├─ semantic obligations
                        ├─ server-pinned execution plan
                        ├─ omission findings
                        ├─ material frontier
                        └─ semantic / execution / snapshot hashes
                                      │
                ┌─────────────────────┼─────────────────────┐
                v                     v                     v
          Portal pipeline       managed prashna_ask      raw MCP lifecycle
          evidence events       evidence events          server execution only
                └─────────────────────┼─────────────────────┘
                                      v
                         deterministic closure validator
                         COMPLETE | INCOMPLETE | BLOCKED
```

The legacy `CAPABILITY_MANIFEST` remains temporarily in the LLM payload only as an execution-name compatibility projection. `capability_knowledge` is now explicitly identified as the semantic authority. This is a cutover, not a claim that all historical manifest consumers have been removed.

## 4. Semantic Capability Unit contract

An SCU describes what Madhav can know or do for planning. It is not synonymous with a tool or asset. Its contract includes:

- stable ID and version;
- semantic kind, domains, concepts, intents, horizons and scope;
- inputs and outputs at the semantic level;
- one primary binding plus optional many-to-many additional bindings;
- execution channels and public MCP name when source-proven;
- pagination semantics, exact response paths, ordering and a separate verification flag;
- prerequisite, enabling, related and contradiction edges;
- provenance, freshness, entitlement, safety, and known gaps;
- producer-output claims with an explicit quality disposition.

`editorial:false` has a strict meaning: the compiler derived a conservative routing stub from the descriptor. It is inventory coverage, not reviewed semantic decomposition, output usefulness, doctrinal coverage, or proof that the public MCP route exists.

Execution truth is split visibly:

- `platform_internal` means the registry handler/loader is callable through the platform dispatcher.
- `mcp_full`, `mcp_compact`, or `mcp_consult` are asserted only where an explicit public name is attached.
- An internal registry binding is never counted as proof of public MCP exposure.

## 5. Compiled snapshot and graph integrity

The generator emits `platform/src/generated/capability_knowledge.snapshot.json`. The current branch artifact has:

| Measure | Count |
|---|---:|
| Runtime descriptors | 185 |
| Planner-addressable descriptors | 182 |
| Excluded calibration-only descriptors | 3 |
| Compiled SCUs | 182 |
| Editorial SCUs | 5 |
| Conservative derived stubs | 177 |
| Executable bindings | 179 |
| Non-executable/discovery-only bindings | 6 |
| Bindings with a source-attached public name | 7 |
| Source-reviewed pagination bindings | 1 |
| Producer-output claims | 8 |
| Claims joined to a reviewed output-spec hash | 7 |

Snapshot content hash at the time of this brief: `sha256:5a2c37b7fefa30cd18769baa2138933eadf628187564dc38b41cff99cf65dd11`.

The runtime imports and deep-freezes this generated JSON artifact. It also recompiles the current registry to detect byte-affecting drift; the live catalog is not silently substituted for the pinned snapshot.

The compiler rejects duplicate SCU IDs, missing/multiple primary bindings, stale edge targets, non-executable registry bindings, orphan addressable descriptors, incompatible snapshot versions, and a paginated descriptor falsely presented as non-paginated. It reports unreviewed pagination on editorial SCUs as a warning so the gap remains visible without claiming exhaustion proof.

## 6. Representative deep-asset slice

Five editorial SCUs prove the many-to-many and cross-layer model:

| SCU | Primary internal route | Public route evidence | Producer-output links | Important truth boundary |
|---|---|---|---|---|
| `scu.bodha.mechanism.network` | `marsys://tool/L2/query_mechanisms` | `bodha_mechanisms_get` | `bo_yantra_mechanism` | D1-only; offset order lacks a unique final tiebreak, so pagination is not receipt-grade. |
| `scu.kala.temporal_activation` | `marsys://tool/L3/query_temporal_activation` | `kala_windows_get` | `ka_kalasutra`, `ka_yojaka`, `ka_bhavishya_lekha` | `top_k` bounded with no total/next/exhaustion proof. |
| `scu.catalog.get_divisionals` | `marsys://tool/L1/get_divisionals` | public MCP uses `ganita_chart_facts_get(divisional_chart=...)` | `ga_vargas` | No same-name public MCP tool; internal offset route has no total/exhaustion proof. |
| `scu.yoga.firing_and_cancellation` | `marsys://tool/L1/get_yoga_firings` | `ganita_yoga_firings_get`; related `kala_yoga_activation_get` | `ga_yoga` | Primary route has reviewed offset/total/more-available paths and deterministic order. |
| `scu.finance.prosperity_assessment` | `marsys://tool/L-DOMAIN/assess_wealth` | `assess_wealth` | `bo_cdlm_summary`, `bo_vargottama_dhana` | Nested bounded components are not misrepresented as exhaustively paged. |

The representative wealth deep-dive floor includes prosperity assessment, mechanisms, divisional evidence, yoga firing/cancellation, temporal activation, dashas, transits, classical grounding and contradiction inquiry. Omission rules additionally seed Bhāvat Bhāvam, cancellation, varga contradiction, inhibitors, temporal prerequisites and cross-domain convergence when the question makes them material.

Seven producer-output links above pin exact migration-authored output-digest component hashes and are marked `reviewed_output`. `ka_kalasutra` remains the sole `route_evidence_only` link because no reviewed output-digest component hash is joined to it. These hashes prove a reviewed component contract exists in source; they do not prove the current deployed row, chart population, or empirical quality.

## 7. Estate census

`platform/scripts/generate_capability_estate_census.ts` creates a separate deterministic accounting artifact. It does not infer SCU coverage. Current branch census hash: `7f3525135db374d5e187f7768b5885951b1f01e088fa86e1e7bf202fdd3b57b4`.

| Denominator | Current source-tree result |
|---|---:|
| Runtime descriptors | 185: 179 tools, 5 resources, 1 prompt |
| Planner-addressable | 182 |
| Public registrar resolution | 59 verified-unambiguous, 3 ambiguous, 123 unresolved |
| Producer assets | 129 total, 128 active, 1 retired |
| Writer / non-writer identities | 123 / 6 |
| Assets with any statically inserted reviewed output spec | 33 |
| Assets without any such spec | 96 total, 95 active |
| Deployed current output-spec rows | `not_mechanically_resolved` |

The public registrar count is an audit of the existing source-text extractor. Its known false negatives are retained in the artifact. “Unresolved” is not silently translated to “absent at runtime.”

The reviewed-output figure is statement-level static migration evidence. It does not establish current deployed rows, live population, semantic value, planner reachability, or empirical accuracy.

## 8. Inquiry Contract and closure semantics

Each Inquiry Contract pins:

- contract/compiler versions;
- question, chart and normalized scope tuple;
- capability compatibility version and content hash;
- chart availability overlay version when supplied;
- semantic obligations and materiality;
- binding-specific plan items and exact arguments;
- omission findings and optional internal AI hypotheses;
- material frontier, iteration, cap and status reasons;
- distinct `semantic_contract_hash`, `execution_plan_hash`, and combined `contract_id`.

The hybrid authority split is intentional:

- An internal AI pass may propose question facets, associations and hypotheses; a valid adjacency is admitted only when its source is already selected and both endpoint SCUs exist in the immutable snapshot.
- The deterministic compiler resolves proposed terms only against live SCU IDs and discards invented IDs.
- Deterministic floors and omission rules are not waivable by the AI.
- Deterministic finalization is the only authority that may return `COMPLETE`.

`COMPLETE` requires every required obligation to be `served` or evidenced `empty`, with no open material frontier and a valid contract. Required `failed` or `dark` obligations remain incomplete and become blocked when the iteration cap is exhausted. Reaching a time, token, call, iteration, or page cap never becomes completeness by wording.

An honest empty result may close an obligation only when it has a server-observed evidence reference. It is distinct from dispatch failure, darkness, truncation and an unexecuted plan item.

## 9. Chart/build availability overlay

The overlay is a separate immutable value keyed by chart, snapshot hash, compatibility version, build ID, optional code revision and writer-inventory hash. Per SCU it records:

- available/partial/empty/dark/incompatible state;
- build status, build ID and freshness;
- executable binding IDs actually available;
- gaps;
- per-asset receipts including writer version, output-spec hash, state and receipt reference.

The overlay loader reads the latest completed build and matching provenance/freshness receipts in one database statement, requires exact reviewed output-spec hashes and the active build ID, and fails dark when evidence is missing, stale, incompatible, or unavailable. All three doors pin the resulting overlay in the Inquiry Contract, restrict dispatch to bindings it makes available, and revalidate the overlay immediately before closure or raw evidence commit.

This is source-wired and unit-tested, not production-verified. Because most SCUs still have no reviewed producer-output claim, the loader will honestly leave most of the estate dark until those claims and live receipts exist.

## 10. Managed-channel wiring

Portal plan stage compiles the Inquiry Contract from the same pinned snapshot used by raw MCP. The server-compiled ready actions replace the planner tool list: unmatched, blocked, dark and duplicate planner-only calls do not survive into dispatch. Evidence stage classifies actual results through binding-specific reviewed response paths, follows verified page continuations within the bounded iteration budget, revalidates the overlay, and finalizes deterministically. Receipt stage emits an `inquiry_contract` grade with required-obligation, open-frontier and normalized closure-receipt data.

Managed `prashna_ask` now:

- compiles the same Inquiry Contract core;
- treats server-compiled ready actions and exact arguments as execution authority rather than planner suggestions;
- maps successful, empty and failed tool events to observations;
- distinguishes adapter-item counts from semantic result counts and reports the latter only for reviewed collection paths;
- follows verified page continuations within call, wall-clock and iteration caps;
- revalidates the chart/build overlay before closure;
- treats dispatch errors, compiler failure, unmapped floor items, caps, unresolved tools, and a non-complete Inquiry Contract as partial;
- returns the Inquiry Contract beside its existing reading envelope;
- keeps final synthesis in the synthesis component, outside the planner.

The existing Portal and managed-MCP completeness receipts remain for compatibility. The Inquiry Contract is the semantic closure authority, and every door emits the same normalized `inquiry-closure-v1` coverage/frontier receipt shape. Older receipt families are not deleted in this candidate.

## 11. Raw MCP lifecycle and security

The raw MCP surface is full-profile only:

1. `inquiry_start` accepts a strict managed-compatible scope tuple and returns a durable contract plus the only authorized next action IDs.
2. `inquiry_execute_next` verifies the signed lifecycle token, current DB revision/JTI, principal, chart entitlement, semantic hash, execution-plan hash, revision-specific contract-state hash, execution channel, overlay/build, compatibility version and snapshot hash. The server selects the binding and arguments; the caller cannot nominate a tool or claim an observation.
3. The platform consumes the one-use JTI before dispatch, executes only an authorized `mcp_full` handler-backed registry route, caps the returned payload at 512 KiB, stores only result hashes and minimal trace/byte metadata in an append-only evidence receipt, and rotates the token after an atomic state transition.
4. Verified multi-page routes remain executable until the server observes exhaustion. Unreviewed pagination produces `next:"unproven"` and an open material frontier.
5. `inquiry_finalize` returns the deterministic closure receipt and never performs synthesis.

Token security uses HMAC-SHA-256 with a dedicated `INQUIRY_LIFECYCLE_SIGNING_KEY`, a minimum key length, fixed issuer/audience, user-and-API-key subject binding, short expiry, random JTI, revision, authenticated mutable-state hash, allowed transition and next-action allowlist. The raw token is never stored; only its SHA-256 JTI hash is retained. Fresh chart authorization and overlay/build compatibility run on every transition. Unknown internal failures are logged under a trace ID and returned as a stable public error rather than leaking exception details.

Migration 1033 creates principal/chart-bound lifecycle state and append-only evidence receipts with:

- profile and chart foreign keys using deliberate `ON DELETE RESTRICT`;
- RLS on both tables using principal and chart context;
- no sidecar access;
- explicit least-privilege grants to `role_web_serve`;
- immutable authorization JSON separated from authenticated mutable progress;
- atomic compare-and-swap over revision and current JTI hash;
- a database-serialized ceiling of 32 creations per principal/hour and eight active lifecycles per principal/chart;
- 30-day immutable retention, with global expiry cleanup attached to the already-scheduled pending-stream reaper;
- multiple receipts for verified pagination, one receipt per lifecycle revision;
- cascade deletion of child receipts only after lifecycle retention expiry, plus documented export requirements.

The independent migration guard returned `MIGRATION SAFE` after the retention/quota amendment. The migration remains unapplied; this is static review, not application evidence.

## 12. Adjacent managed-job security repair

`prashna_status` no longer treats a UUID job ID as sufficient authority. Jobs are bound to the creating user and key, and polling rechecks current chart entitlement before returning progress or results. Expired in-memory jobs are swept opportunistically on create/get. Managed job state itself remains process-local and restart-volatile; the new durable store applies to the raw Inquiry lifecycle, not the older `prashna_ask` job wrapper.

## 13. Generated artifacts and CI

Commands:

```text
cd platform
npm run codegen:capability-knowledge
npm run codegen:capability-knowledge:check
npm run codegen:capability-estate-census
npm run codegen:capability-estate-census:check
```

Ordinary CI now checks:

- snapshot byte drift and graph integrity;
- estate-census byte drift and denominator invariants;
- deterministic snapshot/search/edge/overlay behavior;
- Inquiry Compiler floors, AI-ID filtering, omission/frontier closure and blocked caps;
- required failure never completing;
- lifecycle token binding, tamper, subject, expiry and weak-key rejection;
- independently reviewed semantic-empty classification, pagination advance, terminal exhaustion and unproven handling;
- raw-route principal-header enforcement, user-and-key/token-state binding, pre-dispatch replay exclusion, verified page continuation, mutable-state forgery rejection and overlay-drift termination;
- migration FKs, RLS, grants, append-only evidence and independent hashes;
- raw MCP lifecycle registration/profile restriction;
- principal-bound `prashna_status`, managed `prashna_ask`, and server registration.

No test in this branch is described as live production proof. Database behavior is statically and unit tested; a throwaway PostgreSQL application/integration run remains required before deployment.

## 14. Files and ownership seams

| Area | Primary path |
|---|---|
| SCU schema/compiler/query/overlay | `platform/src/lib/retrieval/registry/knowledge/` |
| Descriptor amendment and editorial fragments | `platform/src/lib/retrieval/registry/types.ts`; owning L1/L2/L3/domain descriptor files |
| Inquiry Compiler/lifecycle/token/store/pagination | `platform/src/lib/vidhi/inquiry/` |
| Raw lifecycle HTTP authority | `platform/src/app/api/mcp/inquiry/route.ts` |
| MCP bridge and tools | `platform-mcp/src/lib/inquiry_bridge.ts`; `platform-mcp/src/tools/register_inquiry_lifecycle.ts` |
| Portal/managed integration | `platform/src/lib/pariprashna/pipeline/`; `platform/src/app/api/mcp/prashna_ask/route.ts` |
| Durable DDL | `platform/migrations/1033_planner_inquiry_lifecycle.sql` |
| Knowledge generator/artifact | `platform/scripts/generate_capability_knowledge.ts`; `platform/src/generated/capability_knowledge.snapshot.json` |
| Estate census generator/artifact | `platform/scripts/generate_capability_estate_census.ts`; `platform/src/generated/capability_estate_census.json` |

## 15. Honest residual register

| ID | Residual | Consequence / next proof |
|---|---|---|
| R1 | 177/182 SCUs are conservative descriptor-derived stubs. | Editorially decompose by high-value slice; do not claim semantic estate completion. |
| R2 | 95/128 active assets lack any statically evidenced reviewed output spec. | Author/review output contracts or explicitly exclude/darken each output; regenerate census. |
| R3 | One of eight representative producer claims (`ka_kalasutra`) remains route-only. | Join it to an exact reviewed current component hash or retain it as an explicit dark/route-only boundary. |
| R4 | Public registrar scanner resolves only 59 unambiguous descriptors and has known false negatives. | Replace source-text inference with structured registrar declarations; explicitly adjudicate three ambiguities. |
| R5 | Only yoga firing currently has source-reviewed, receipt-grade pagination metadata. | Add total/next/exhaustion and total ordering to material routes, then golden-test first/middle/last pages. |
| R6 | Chart/build overlay loading is source-wired but not exercised against a deployed schema; most SCUs have no reviewed producer claim and therefore remain dark. | Rehearse against throwaway/staging data, then expand exact producer claims and receipt population without weakening the dark default. |
| R7 | `CAPABILITY_MANIFEST` remains as an execution-name compatibility projection. | Complete adapter coverage, then remove flat semantic authority and its prompt assumptions. |
| R8 | A normalized channel-neutral closure receipt and semantic-hash parity tests exist, but no deployed cross-door trace proves equivalent runtime observations. | Run identical staging inquiries through Portal, managed MCP and raw MCP and compare normalized receipts without equating delivery envelopes. |
| R9 | Portal and managed MCP perform bounded in-request multi-pass continuation but do not checkpoint/resume managed frontier expansion through the durable lifecycle. | Add managed lifecycle persistence/resumption while preserving the same server execution authority. |
| R10 | Raw MCP lifecycle requires migration application and a dedicated signing key. | Provision through normal secrets/change control, apply DDL in a throwaway DB first, then staging; none was done here. |
| R11 | Managed `prashna_ask` job wrapper remains process-local. | Adopt durable job delivery separately; principal binding fixes disclosure but not restart/cross-instance continuity. |
| R12 | No live database, deployed endpoint, production overlay, or empirical answer-quality proof was run. | Treat all current results as branch/source verification only. |

## 16. Review and rollout gates

Before merge:

1. Independent code/security review of the raw execution authority and evidence retention.
2. Throwaway PostgreSQL migration up/down rehearsal, RLS-role tests and concurrent CAS/replay tests.
3. Extend route integration coverage to revoked access, stale snapshot, wrong action, failed dispatch and terminal incomplete closure; user/key binding, concurrent replay exclusion, state forgery rejection, overlay drift and verified multi-page continuation are covered.
4. Rehearse normalized semantic-contract/closure parity across Portal, managed MCP and raw MCP for identical staging question/scope/snapshot.
5. Confirm the dedicated signing-key provisioning/rotation runbook without exposing a key.

Before deployment:

1. Merge and protected CI are necessary but not deployment proof.
2. Apply migration 1033 under approved change control.
3. Provision the signing key and verify service-to-service headers/role context in staging.
4. Run staging lifecycle journeys, including restart/cross-instance behavior and evidence retention.
5. Validate the wired chart/build overlay against real staging receipts before claiming chart-aware capability availability.

Before any “complete data estate” claim:

1. Close or explicitly disposition all 95 active output-spec gaps.
2. Replace derived stubs with reviewed semantic units for the material slices.
3. Prove public execution bindings and pagination/exhaustion paths.
4. Join producer-output hashes and chart/build receipts.
5. Re-run the mechanical census and independent omission/mutation tests.

### Current branch verification boundary (2026-09-14)

The scoped candidate checks are green under the CI-pinned Node 20 runtime and a
clean `npm ci`: the exact added platform CI selection passes 87/87; the exact MCP
lifecycle CI selection passes 27/27; both package typechecks pass; the migration
number guard passes; the capability snapshot, estate census, MCP envelope and MCP
registry-shim drift checks pass; and full platform lint exits zero with no errors
(590 pre-existing warnings remain).
The broader focused evidence remains green at 157 platform tests, 56 golden-stream
cases, 90 independent completion-review tests, and 86 independent security-review
tests. Independent completion, security, and migration reviews reported no open
HIGH or MEDIUM blocker in the changed surface.

The CI-faithful full platform unit run is also green: 1,093 files passed and 71
were skipped; 11,614 tests passed, 662 were skipped and 2 are todo. Reinstalling
`platform-mcp` from its committed lockfile also removed the apparent SDK/Zod
typecheck failure, and the two stale generated MCP contracts were regenerated.
The full MCP suite remains outside CI by an explicit workflow decision because
it carries pre-existing unrelated failures; the current run reports 184 files
passed, 25 failed and 1 skipped (2,125 tests passed, 80 failed and 20 skipped).

The mandatory local `run-checks` gate is now green. The original block was a
repository-wide backlog of 199 ESLint errors under the current Next/React compiler
rules, reproduced identically at the protected base. The branch resolves those
errors at source without changing lint configuration or adding rule suppressions:
unsafe casts/CommonJS imports were replaced, render-time mutation was removed,
portal/media/storage state now uses hydration-safe external stores, lifecycle
transitions are modeled declaratively or scheduled through cancellable external
subscriptions, and the affected source guards were updated. Full lint now reports
0 errors and 590 warnings; TypeScript passes; the full platform unit suite remains
green at 1,093 files and 11,614 tests passed.

## 17. Candidate disposition

The branch is reviewable as a coherent foundation and is intentionally incomplete as an estate-wide semantic mapping. Its durable claims are the implemented contracts, generated source-tree snapshots, tests and static migration review. It makes no claim of merge, deployment, migration application, production health, complete public reachability, live chart availability, or full producer-output semantic coverage.
