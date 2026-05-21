---
artifact: MARSYS_JIS_ARCHITECTURE_v1_0.md
version: 1.0
status: APPROVED (2026-04-27, native; pending formal adoption via ND.2 or PHASE_B amendment v1.0.4)
revision: v1.0 (2026-04-27 initial; same-session §19 question resolution per native approval)
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
authoring_session: Cowork conversation — "Holistic architecture synthesis, post panel-addendum + retrieval-brief reconciliation"
purpose: Single source-of-truth architectural document for the MARSYS-JIS Consume + Retrieval system. Reconciles CONSUME_DESIGN_v0_1.md, PANEL_SYNTHESIS_ADDENDUM_v0_1.md, MARSYS_JIS_Architecture_Review_Brief.docx, and the design refinements from the 2026-04-27 brainstorm session (LLM-checkpoint hybrid, router-driven mandatory bundle, six-domain component decomposition).
governance_status: NOT YET ADOPTED. Awaits native review and approval. Path to adoption: ND.2 native directive binding B.6+ to honor it, OR a PHASE_B_PLAN amendment to v1.0.4 elevating this document as the canonical Consume + Retrieval architecture.
supersedes:
  - CONSUME_DESIGN_v0_1.md (DRAFT_PROPOSAL — content absorbed and refined; status will become SUPERSEDED on adoption)
  - PANEL_SYNTHESIS_ADDENDUM_v0_1.md (DRAFT_PROPOSAL at v0.2 — content absorbed as §10 panel synthesis strategy)
  - MARSYS_JIS_Architecture_Review_Brief.docx (DRAFT — content absorbed and refined per §8 retrieval architecture)
  - PANEL_IMPLEMENTATION_BRIEF_v1_0.md (AUTHORED — superseded; panel work becomes Phase 7 of master project plan)
relates_to:
  - PROJECT_ARCHITECTURE_v2_2.md §B Architectural Principles (B.1–B.12 inherited verbatim — this document refines but does not supersede them)
  - MACRO_PLAN_v2_0.md §Ethical Framework, §Cross-cutting workstreams, §Learning Layer (this document operationalizes their architectural implications)
  - PHASE_B_PLAN_v1_0.md §B.6 (Hybrid Retrieval), §B.7 (Synthesis Router) — this document specifies what those phases must deliver
  - GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K (multi-agent disagreement protocol — extended in §10 with DIS.class.extension)
  - CANONICAL_ARTIFACTS_v1_0.md (canonical artifact registry — to be subsumed over time by the Capability Manifest per §6)
  - FILE_REGISTRY_v1_11.md (delta registry — to be subsumed over time by the Capability Manifest per §6)
seeds:
  - Native intent: "build them into components or segments... modular componentized approach so that tomorrow we can update a component without breaking the entire system"
  - Native priority: "When we are testing the module, cost consideration is not my priority. My single most priority is accuracy."
  - Native domain-knowledge principle: "wherever domain knowledge is required, an LLM is in the loop; deterministic where the operation is integrity, lookup, persistence, or pure algorithm"
  - Native goal alignment: acharya-grade reading + future research instrument for Jyotish as a discipline
---

# MARSYS-JIS Architecture v1.0 — Holistic Consume + Retrieval

## §1 — Purpose and Scope

This is the single source-of-truth architectural document for the MARSYS-JIS Consume layer (the chat interface) and its supporting Retrieval pipeline, plus the cross-cutting Audit, Learning, and Foundation substrates that hold it together. It absorbs and supersedes four prior documents whose lineage is recorded in §18 Provenance. It does not supersede `PROJECT_ARCHITECTURE_v2_2.md` or `MACRO_PLAN_v2_0.md` — those remain the umbrella architecture and strategic-arc documents. This document is the focused architectural specification for the Consume + Retrieval slice.

The document serves three audiences. The native (Abhisek Mohanty) reviews it for architectural coherence and approves it for adoption. Cowork sessions read it as the canonical reference when authoring execution briefs. Claude Code executor sessions read it as the architectural intent that their implementation must honor. Every component decision, every interface contract, every evolution path the system anticipates is recorded here so that no execution session has to re-derive a design choice.

It is written to make architectural change cheap and architectural drift expensive. Each component declared in §4 carries an `interface_version` field; a bump signals a breaking change that other components must adapt to. Implementations behind those interfaces evolve freely. The contracts at §15 are what hold the system together as it grows.

This is `v1.0` because it is the first comprehensive synthesis. Prior `v0.x` artifacts (CONSUME_DESIGN, panel addendum, retrieval brief) were exploratory drafts that contributed components which now live in this unified spec. Subsequent versions will refine and extend; the migration path in §17 makes that incremental.

## §2 — Mission and Decision-Prioritization Rules

The project's stated mission, restated here so this document and the master project plan that follows it are anchored to it: build an LLM-operated Jyotish instrument that reads the native's chart with acharya-grade depth, surfaces patterns and contradictions across layers and systems that no individual astrologer could hold in working memory, makes time-indexed and probabilistic and calibrated predictions testable against lived reality, and — over time — extends beyond this native to become a research tool for astrology as a discipline. Bounded by the Ethical Framework in `MACRO_PLAN_v2_0.md §3.5`: probabilistic, calibrated, auditable outputs for consenting audiences under stated disclosure tiers; not a fortune-telling product.

This mission gives the architecture a four-rule decision-prioritization order, which is the lens this document uses to resolve every contested design choice:

**Quality over cost.** Acharya-grade is the bar. When a more accurate but more expensive design choice exists, take it. The brainstorm-confirmed corollary: during testing and validation, cost is not a priority; accuracy is.

**Auditability over speed.** Every claim cited; every retrieval transcript captured; every disagreement classified; every prediction logged before its outcome. A cheaper design that loses audit fidelity is rejected.

**Calibration over convenience.** The system is built to learn from outcomes. Decisions that make the calibration corpus cleaner (per-model logging, retrieval-path capture, explicit disagreement classification) outweigh decisions that make individual queries simpler.

**Multi-native research future over single-native present convenience.** The system is single-native today. The architecture must not preclude the research-instrument future. Decisions that bake in single-tenant assumptions (per-native-only manifest, hardcoded chart references) are rejected even if they're locally simpler.

Where these rules conflict — e.g., a decision that improves quality but harms auditability — quality wins; but the architecture is designed so such conflicts are rare. They are noted explicitly when they arise in the sections below.

## §3 — Architectural Principles

The architecture is governed by ten principles that apply across all components. The first six inherit from `PROJECT_ARCHITECTURE_v2_2.md §B`; the last four are specific to this Consume + Retrieval slice and were established through the 2026-04-27 brainstorm.

**P.1 Facts/interpretation separation (B.1).** Facts live at L1; derivations at the L1/L2 boundary with explicit ledger; interpretations at L2+ only. The Consume pipeline preserves this — every L2+ claim in any synthesized response carries inline L1 fact_id citations.

**P.2 Derivation-ledger mandate (B.3).** Every L2+ claim cites the specific L1 fact IDs it consumes. The Retrieval architecture's tools surface fact_id provenance with every signal; the Validator Service enforces resolution.

**P.3 Versioning discipline (B.8).** Every canonical artifact carries frontmatter `version`, `status`, and a changelog. The Capability Manifest at §6 is itself versioned and fingerprinted; consumers log the active fingerprint into every audit trail event.

**P.4 No fabricated computation (B.10).** If a numerical chart value is required and is not in L1, the system marks the gap as `[EXTERNAL_COMPUTATION_REQUIRED]` rather than inventing it. Stage-7 synthesis enforces this in prompt; Stage-8 P4 validator enforces it post-synthesis.

**P.5 Whole-Chart-Read discipline (B.11).** Every interpretive query routes through the L2.5 holistic synthesis substrate (UCN, CDLM, RM, CGM) before producing a domain-specific answer. The architecture enforces this at Stage-2 router level (rule-based bundle composition) and at Stage-8 validator level (P3).

**P.6 Acharya-grade quality bar.** An independent senior Jyotish acharya reviewing the corpus reaches one of three judgments: "this is my own level", "this is above my own level", or "this reveals things I would not have seen on first pass". This principle informs every quality-vs-cost trade-off.

**P.7 Modular componentization with stable interfaces.** Components are units of independent evolution. Each declares an interface; implementations evolve behind it. Cross-component coupling happens only through interfaces, never through shared mutable state or storage reach-through. New components arrive by registering against existing interfaces; new interfaces require explicit version bumps.

**P.8 Domain knowledge → LLM; integrity, lookup, persistence, algorithmic execution → deterministic.** Wherever a decision in the pipeline involves astrology-domain interpretation, an LLM sits in the loop. Wherever the operation is structural integrity, data lookup, durable persistence, or pure algorithmic execution (e.g. graph BFS), the implementation is deterministic. Three new LLM checkpoints (Stages 4.5, 5.5, 8.5) embody this principle; the deterministic operations they sit alongside are listed in §11.

**P.9 Router-driven mandatory context, not unconditional load.** The Tier-1 eligible set of always-loadable assets exists, but per-query mandatory composition is decided by the Stage-2 Router based on query class. B.11 (Whole-Chart-Read) is enforced at the rule level (the router's classification rules guarantee L2.5 inclusion for any non-trivial interpretive query), not at the load level (unconditionally loading 178K tokens regardless of need).

**P.10 Multi-model and multi-native forward-compatibility.** The architecture treats LLM provider variation as the default (different context windows, different tool-use protocols, different prompt-caching capabilities) and treats per-native namespacing as a forward-compatible requirement. Today's single-native deployment is a special case of the multi-native architecture, not a precondition that must be unwound.

## §4 — The Component Architecture (Six Domains)

The system decomposes into six domains, each containing components bounded by their rate of change and direction of evolution. Components communicate via interfaces declared at §15. The six domains are:

**D1 — Data & Catalog.** Owns the corpus and how it is catalogued. Evolves with corpus growth.

**D2 — Query Pipeline.** Owns the path from user query to assembled retrieval bundle. Evolves with retrieval intelligence (better routers, better rerankers, new tools).

**D3 — Synthesis & Validation.** Owns the path from retrieval bundle to validated, disclosure-filtered synthesis output. Evolves with synthesis strategy and validator coverage.

**D4 — Audit & Learning.** Owns the durable record of every query and the calibration substrate that consumes it. Evolves with the M5 Learning Layer.

**D5 — Interface (Consume).** Owns the user-facing chat interface. Evolves with UX and audience-tier expansion.

**D6 — Foundation.** Owns the cross-cutting abstractions (LLM providers, schema registry, configuration, telemetry) that everything depends on. Evolves least; designed for stability.

The component-level specification follows.

### §4.1 — Domain D1: Data & Catalog

**C1.1 Asset Catalog (Capability Manifest).** Single source of truth for what data exists and is consumable. Auto-derived from filesystem walk of the data directories plus parsed frontmatter (`version`, `status`, `layer`, `expose_to_chat`, `supplements_parent`, `canonical_id`); merged with a curated overrides file (`manifest_overrides.yaml`) carrying routing intelligence (`preferred_for` per query class, cost weights, exclusions, classification hints). Published as `CAPABILITY_MANIFEST.json` with fingerprint rotation on every regeneration. Replaces, over time, the dual `FILE_REGISTRY` + `CANONICAL_ARTIFACTS` registries (see §6). Interface: `read(canonical_id) → AssetEntry`, `query(predicate) → AssetEntry[]`, `subscribe(callback)`, `fingerprint() → sha256`. Implementation: file-backed JSON with in-memory cache; fingerprint on every change. Evolution paths: schema-versioning, multi-native namespacing, live (sub-second) updates from the ingestion pipeline.

**C1.2 Ingestion Pipeline.** Transforms corpus files into queryable RAG representations. Triggered on commit for corpus directories (per §6 manifest discipline) and manually for governance directories. SHA256-deterministic chunking via per-doc-type chunkers (`msr_signal`, `ucn_section`, `cdlm_cell`, `l1_fact`, `domain_report`, `cgm_node`, plus future doc types as the corpus grows); embedding generation via Vertex AI `text-multilingual-embedding-002` (768-dim); graph node/edge extraction; structured-table loading (e.g., MSR → `msr_signals` table). Validators run during chunk writing (P1, P2, P5 today; P3, P4 added per §12). Output is atomic: filesystem state, RAG tables, and Capability Manifest update happen together. Interface: `ingest(file_path) → IngestResult`, `rebuild() → IngestResult` (full reindex), `subscribe(file_change_event)`. Implementation: Python sidecar (`platform/python-sidecar/rag/`). Evolution paths: incremental updates by content hash, new doc-type chunkers, learned chunk boundaries.

**C1.3 Storage Layer (abstraction).** Unified interface over the three storage backends: PostgreSQL (Cloud SQL with pgvector — RAG tables, MSR signals, prediction ledger, audit log, user settings, conversation messages); object storage (GCS — markdown files, archive); local filesystem (the canonical markdown corpus and governance documents). Components in higher domains never reach across backends; they call this abstraction. Interface: `query(table, predicate)`, `read(path)`, `write(table, record)`, `migrate(schema_change)`. Implementation: per-backend adapters with a uniform `StorageClient`. Evolution paths: schema migrations (versioned, reversible), data partitioning (per-native namespacing), cold-storage tiering, distributed cache layer.

### §4.2 — Domain D2: Query Pipeline

**C2.1 Router (Stage 2).** Stateless small-LLM service that reads the query (plus minimal conversation context) and produces a structured `QueryPlan` (schema in Appendix A). Classification dimensions: query class, domains, planets, houses, dasha context need, forward-looking flag, audience tier, graph seed hints, traversal depth, tools authorized, history mode, panel mode flag. Default model: Claude Haiku 4.5 (configurable via C6.3). Interface: `classify(query, context) → QueryPlan`. Evolution paths: fine-tuned classifier, learned classifier from M5 calibration data, tiered router (small model first, escalate to large on low-confidence classifications).

**C2.2 Bundle Composer.** Two sub-components composed: **C2.2a Rule Composer** (deterministic — applies the routing rules in §9 to QueryPlan + Manifest, produces a draft bundle of mandatory context per the floor + conditional rules) and **C2.2b Bundle Augmenter (Stage 4.5, LLM checkpoint)** (small LLM reviews the rule-composed bundle and may suggest additions the rules missed — e.g. "include Pattern Register because forward-looking" or "skip Financial L3 despite domain match because cross-domain coverage via MSR is preferred for this query"). Interface: `compose(QueryPlan, Manifest) → Bundle`. Evolution paths: rule learning (M5 surfaces correlations between augmenter additions and outcome quality, rules absorb the patterns over time), augmenter fade-out (eventually the augmenter becomes optional as rules mature), per-native rule sets.

**C2.3 Retrieval Tool Suite.** Plug-in registry of retrieval tools, each implementing a uniform `retrieve(QueryPlan) → ToolBundle` interface. Tools: MSR-SQL (structured query against the MSR signals table), CGM-Graph (BFS over CGM nodes by SUPPORTS / CONTRADICTS / CROSS_LINKS edges from query-plan-supplied seed hints), Pattern-Register / Resonance / Cluster / Contradiction (filtered queries against the L3.5 register tables), L3-Report (whole-document load by domain), Temporal (current dasha + transit lookups via Python sidecar / Swiss Ephemeris), Vector-Search (secondary — used only when other tools have no match), Manifest-Query (LLM meta-tool — lets the synthesizer ask "what's available about X" as a tool call). Tools run concurrently at Stage 5; each tool's full transcript is captured for audit. Interface (per tool): `retrieve(QueryPlan) → ToolBundle`. Evolution paths: new tools land per phase (e.g., Remedial-Codex tool when L4 directory materializes; Temporal-Engine tool when L5 directory materializes), tool-cost annotations for query-plan-aware tool selection, learned retrieval per tool.

**C2.4 Reranker (Stage 5.5, LLM checkpoint).** Replaces the simpler significance-weighted sort. Small LLM reads the query plus each candidate signal returned by C2.3 MSR-SQL (typically 60-100 candidates) and ranks by query-relevance with domain knowledge. Returns the top N (configurable, default 25). Catches signals where labeled metadata doesn't match the query but contextual relevance is high (e.g., a psychology-domain signal materially affecting financial decision-making). Interface: `rerank(query, candidates, top_n) → ranked_top_n`. Evolution paths: fine-tuned cross-encoder, learned ranker from M5 outcome correlations, dynamic top-N based on query difficulty.

**C2.5 Tool-Call Cache.** Request-scoped cache keyed on `(tool_name, hash(normalized_params))`. Prevents 3× duplicate tool execution when multiple panel members independently call the same tool. Audit trail records every invocation with `served_from_cache: true | false` flag, preserving extension-diversity signal even when actual execution happened once. Interface: `get(key) → CachedResult | null`, `put(key, value)`, `clear()`. Implementation: in-memory `Map` per request. Evolution paths: distributed cache for horizontal scaling; cross-request caching for stable tools (e.g., MSR queries that don't change across sessions).

**C2.6 Bundle Assembler (super-bundle composition).** Composes the merged super-bundle handed to the panel adjudicator at Stage 5.6: baseline bundle from C2.2 plus the deduplicated content of every unique extension that any panel member retrieved during Stage-7 generation. This ensures the adjudicator can perform B.10 (no-fabrication) validation against every claim any panel member made. Interface: `assemble(baseline_bundle, panel_member_extensions[]) → super_bundle`. Evolution paths: structured representation of extensions for richer adjudicator audit; cross-bundle deduplication metrics.

### §4.3 — Domain D3: Synthesis & Validation

**C3.1 Validator Service (Structural).** Plug-in registry of structural validators that run deterministic integrity checks on bundles and synthesis outputs. Validators today: P1 (layer separation), P2 (citation discipline), P5 (signal-id resolution). Validators planned: P3 (whole-chart-read enforcement on bundle), P4 (no-fabrication on synthesis), P7 structural (three interpretations present — count check), P8 structural (falsifier present for time-indexed claims — presence check), P9 (audit-trail completeness). Each validator votes pass | warn | fail; fail halts; warn annotates. Interface: `validate(artifact, validator_set) → ValidationResult`. Implementation: per-validator module with a uniform check interface. Evolution paths: validators added incrementally per phase, configurable validator severity (warn vs fail), per-validator metrics.

**C3.2 Synthesis Orchestrator (Stage 7).** Manages the synthesis step. Two strategies, selected at request time by the panel-mode flag in QueryPlan:

The **Single-Model Strategy** invokes the user's selected model with the validated bundle, system prompt, conversation history (per `history_mode`), and tool surface. Streams response. Logs synthesis prompt version into audit trail.

The **Panel Strategy** invokes the **Panel Resolver** sub-component (computes the 3-member panel by excluding the adjudicator's family from the panel slate per §10), the **Panel Runner** (parallel `streamText` invocations to the 3 panel members with concurrent retry up to N=3 per member, request-scoped tool cache active), the **Anonymizer** (labels A/B/C in randomized order), the **Adjudicator** (synthesizes from the 3 anonymized panel responses + super-bundle from C2.6 + retrieval transcripts + synthesis rubric), and the **Divergence Classifier** (separate small-LLM call extracts and labels divergences using `DIS.class.*` taxonomy with the new `DIS.class.extension` class added per §10). The adjudicator's synthesis is the unitary output flowing into Stage 8.

Interface: `synthesize(bundle, mode, model_selection) → stream`. Evolution paths: new synthesis strategies (debate-mode, review-mode, ensemble-with-self-consistency), panel slate evolution (config-driven), learned synthesis prompts per query class.

**C3.3 Semantic Discipline Gate (Stage 8.5, LLM checkpoint).** Small LLM reads the synthesis output post-Stage-8-structural and verifies the three interpretations are meaningfully orthogonal AND the falsifier is specific enough to be falsifiable. Catches synthesis output that passes structural gates but is semantically weak. On failure, triggers one revision pass to the synthesizer. Interface: `check(synthesis, query_class) → GateResult`. Evolution paths: more semantic checks (citation density, interpretation depth, classical-basis grounding), learned semantic-quality model.

**C3.4 Synthesis Prompt Registry.** Versioned prompt templates per query class, per audience tier, per synthesis strategy. Today hand-authored. Includes the consolidation rule revision from §11 (orthogonality + grounding, not consensus). Future: M5 Learning Layer optimizes prompts per query class based on outcome correlation. Interface: `get(class, tier, strategy) → PromptTemplate`, `register(template)`. Evolution paths: learned prompts, A/B testing infrastructure, per-native prompt customization.

**C3.5 Disclosure Tier Filter (Stage 8 gate).** Applies the four-audience disclosure rules (super_admin, acharya_reviewer, client, public_redacted) to the synthesis output and to the audit-view content. Today only super_admin tier exists; client tier lands at M6, public_redacted at M10. Interface: `filter(content, tier, content_type) → filtered_content`. Evolution paths: tier-specific redaction rules, calibration-band rendering, per-claim tier sensitivity.

**C3.6 Streaming Handler.** Vercel `ai` SDK abstraction for streaming response delivery. Uniform across single-model and panel-mode. Backpressure-aware. Interface: `stream(text_iterator) → SSE_response`. Evolution paths: client-side resumability, streaming-during-tool-call UX.

### §4.4 — Domain D4: Audit & Learning

**C4.1 Audit Trail Service.** Captures the complete execution record per query: capability snapshot (which manifest version, which assets), QueryPlan, bundle hash, validator votes, synthesis prompt version, panel_metadata (when panel_mode), classifier output, semantic gate result, response text, per-LLM-call token/latency/cost. Append-only log. Interface: `write(audit_event)`, `query(filter)`. Implementation: PostgreSQL `audit_log` table + structured JSON column. Evolution paths: enriched event schema, query patterns for analytics, archival to cold storage at scale.

**C4.2 Prediction Ledger.** Outcome-blind logging of time-indexed predictions. Every predictive claim emitted by the synthesis (or by panel members in panel mode — 4× ledger writes per predictive panel query) is logged with confidence, horizon, falsifier, source-model, panel-turn-id, and validated bundle hash *before* the response streams to the user. Append-only. Interface: `log(prediction)`, `query_unresolved()`, `resolve(prediction_id, outcome)`. Implementation: PostgreSQL `prediction_ledger` table (interim) → migrate to canonical `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl` per parent design when that surface stabilizes. Evolution paths: outcome-resolution UI for the native, calibration metrics dashboards, per-model accuracy tracking.

**C4.3 Calibration Loop (M5 future).** Reads from C4.1 and C4.2 over time, emits per-component signals back into D2 and D3: improved bundle-composition rules (so C2.2a can absorb what C2.2b learned), refined reranker signal weights, optimized synthesis prompts per class, per-model reliability scores per query class for panel weighting. Today: scaffolded only. Activated at M3+. Interface: `emit_signal(component_id, signal_type, payload)`, `consume_outcome(prediction_id, outcome)`. Evolution paths: live A/B testing infrastructure, automated rule discovery, learned-prompt deployment pipeline.

### §4.5 — Domain D5: Interface (Consume)

**C5.1 Chat API.** Thin HTTP orchestrator over D2 + D3 components. Stateless. Auth-gated (Firebase). Streams response. Interface: `POST /api/chat/consume`. Implementation: Next.js server route handler. Evolution paths: new query types (batch, scheduled), API versioning, alternative client protocols (WebSocket).

**C5.2 Composer.** User input UI: text, attachments, model picker, style picker, panel checkbox. Per-form state; auto-resets panel checkbox after send. Interface: emits `submit(query, options)` to C5.1. Implementation: React component. Evolution paths: voice input, query suggestions, conversation-history awareness, multi-modal attachments.

**C5.3 Conversation Renderer.** Streaming display of assistant responses. Single render path for both single-model and panel-mode messages — the conversation panel shows only the synthesized response in either case. Tier-conditional content rendering. Interface: `render(message, metadata)`. Implementation: React component. Evolution paths: rich rendering (citations as hover-cards, inline visualizations of dasha periods or chart sections), copy-with-attribution, share/permalink.

**C5.4 Audit View (UI).** Inspect affordance per assistant message. Renders the audit trail data from C4.1 with content tier-filtered via C3.5. Single-model audit: capability snapshot, retrieval bundle summary, validator votes, tool-call transcript, token/latency/cost, semantic gate result. Panel-mode audit: all of the above for the adjudicator + per-panel-member sub-panels (response text, tool transcript, validator votes, extracted predictions) + divergence list with `DIS.class.*` classifications + anonymization key. Available to all audience tiers; content tier-filtered. Interface: `render(message_id, audit_metadata, tier)`. Evolution paths: drill-down navigation (click a citation, see source), comparison views (compare two messages' bundles), export.

**C5.5 User Settings.** Persistent per-user preferences: selected model, selected style, `degrade_mode_allowed` toggle, `panel_research_mode` toggle, future per-native chart selection. Backed by C1.3 storage. Interface: `get(user_id, key) → value`, `set(user_id, key, value)`. Evolution paths: org-level settings, profile templates, role-based defaults.

**C5.6 Progress UX.** Three-state indicator during retrieval+synthesis: "Classifying..." → "Retrieving..." → "Synthesizing..." → streaming. No leak of panel composition before audit view is opened. Interface: `subscribe(stage) → state_updates`. Evolution paths: per-stage detail (with-explicit-consent), retry UI on failure, error-state styling.

### §4.6 — Domain D6: Foundation

**C6.1 LLM Provider Abstraction.** Uniform interface over Anthropic, OpenAI, Google, DeepSeek (and future labs). Wraps Vercel `ai` SDK adapters. Carries capability flags per model: `tool-use`, `prompt-caching`, `streaming`, `max_output_tokens`, `context_window`. Adding a new provider = implementing one adapter; no changes to D2 or D3. Interface: `streamText(model_id, messages, tools, options) → stream`, `getCapabilities(model_id) → CapabilityFlags`. Evolution paths: on-prem models, enterprise providers, capability flag expansion.

**C6.2 Schema Registry.** Versioned JSON schemas for the structured types crossing component boundaries: `QueryPlan`, `Bundle`, `ToolBundle`, `AuditEvent`, `panel_metadata`, `Prediction`, `ValidationResult`. Schemas live in `06_LEARNING_LAYER/SCHEMAS/` (extending the existing pattern there). Interface: `getSchema(name, version) → JSONSchema`, `validate(record, schema) → ValidationResult`. Evolution paths: schema migration tooling, backward-compatibility checking, schema-driven code generation.

**C6.3 Configuration Service.** Hot-reloadable configuration: feature flags, panel slate (per-lab model versions), classifier model selections, validator severity, environment-scoped overrides. Interface: `get(key, environment?) → value`, `subscribe(key, callback)`. Implementation: backed by C1.3 storage; cached in-memory with TTL. Evolution paths: per-user overrides, A/B testing config, gradual rollout flags.

**C6.4 Telemetry.** Per-component metrics: latency distribution, cost per call, error rate, capacity utilization. Drives monitoring, calibration, and A/B testing. Interface: `record_metric(component_id, metric_name, value, tags)`. Implementation: structured metrics export to Cloud Monitoring (or equivalent). Evolution paths: distributed tracing across components, performance regression alerts, calibration-quality metrics.

## §5 — The Eight-Stage Pipeline (with LLM Checkpoints)

Every Consume request traverses the same eight stages with three LLM checkpoints inserted at decision points. Stages are listed end-to-end; each names which component owns it.

**Stage 1 — RECEIVE.** Owned by C5.1 Chat API. Authenticates the request; loads conversation context; validates request body. Deterministic. Latency ~50ms.

**Stage 2 — CLASSIFY (Router, LLM).** Owned by C2.1. Small LLM produces the structured `QueryPlan` from the user query plus minimal conversation context. The QueryPlan is the structured contract that drives every downstream stage.

**Stage 3 — DISCOVER.** Owned by C1.1 Catalog and C2.2a Rule Composer. Reads the Capability Manifest at the active fingerprint; filters to assets marked CURRENT and matching the QueryPlan's class requirements. Deterministic data lookup, no decision-making.

**Stage 4 — RESOLVE (Bundle Composer, deterministic).** Owned by C2.2a. Applies the routing rules in §9 to compose the rule-based mandatory bundle: floor (FORENSIC + CGM, ~40K tokens) plus conditional adds based on query class. Deterministic; rules are encoded.

**Stage 4.5 — BUNDLE AUGMENTER (LLM checkpoint).** Owned by C2.2b. Small LLM reviews the rule-composed bundle and may suggest additions (or removals) the rules missed based on domain-knowledge interpretation of the QueryPlan. Output is the augmented bundle that will be passed to retrieval. This catches edge cases where the static rules under-fit the query.

**Stage 5 — RETRIEVE (parallel, deterministic).** Owned by C2.3 Retrieval Tool Suite. Concurrent execution of the tools authorized by the QueryPlan: MSR-SQL filter, CGM graph walk (with seeds from QueryPlan and depth from router classification), pattern/resonance/cluster/contradiction register queries (filtered), domain-report load (when single-domain), temporal lookup, vector search (secondary). Each tool returns a `ToolBundle`. The C2.5 Tool-Call Cache deduplicates identical concurrent calls.

**Stage 5.5 — MSR RERANKER (LLM checkpoint).** Owned by C2.4. Small LLM reads the query plus each MSR candidate signal (60-100 candidates from Stage 5) and reranks by query-relevance with domain knowledge. Returns top 25. Replaces the prior significance-weighted sort, which had no domain awareness. This is the place where signals labeled with one domain but contextually relevant to another get surfaced.

**Stage 6 — VALIDATE (deterministic, structural).** Owned by C3.1 Validator Service. Runs the structural validators (P1, P2, P5 today; expanding) on the assembled bundle. Boolean integrity checks; LLM mediation here would be a regression in consistency. Failures halt the pipeline with explicit error.

**Stage 7 — SYNTHESIZE (LLM, single-model OR panel).** Owned by C3.2 Synthesis Orchestrator. Branches on the QueryPlan's `panel_mode` flag. Single-model strategy: one selected model synthesizes from the validated bundle, with full tool surface available for retrieval extension during synthesis. Panel strategy: panel resolver computes 3-member panel (family-excluded), panel runner invokes 3 members in parallel with request-scoped tool cache, anonymizer labels A/B/C, adjudicator synthesizes from 3 anonymized responses + super-bundle (per C2.6), divergence classifier (separate small-LLM call) extracts and labels divergences.

**Stage 8 — DISCIPLINE (deterministic gates + persistence).** Owned by C3.1, C4.1, C4.2, C3.5. Runs P7 structural (count of three interpretations), P8 structural (falsifier presence for time-indexed claims), P9 audit trail completeness check. Writes audit-trail event (C4.1). Writes prediction-ledger entries pre-stream for predictive-class queries (C4.2). Applies disclosure-tier filter to the to-be-displayed content (C3.5).

**Stage 8.5 — SEMANTIC DISCIPLINE GATE (LLM checkpoint).** Owned by C3.3. Small LLM verifies that the three interpretations are meaningfully orthogonal and that the falsifier is specific enough. On failure, returns to Stage 7 for one revision pass. The structural gate at Stage 8 confirms presence; the semantic gate confirms quality.

The user sees one streamed response. The full transcript of every stage is recoverable through the audit view (C5.4).

## §6 — The Catalog (Capability Manifest)

The catalog is the single contract between author-time (writing markdown files, populating registers, running ingestion) and query-time (chat layer asking "what's available?"). It replaces, over time, the dual `FILE_REGISTRY_v1_11.md` + `CANONICAL_ARTIFACTS_v1_0.md` registries that exist today.

**Composition.** The Capability Manifest is auto-derived plus curated. The auto-derived base is produced by `manifest_builder.py` (a sub-component of C1.2 Ingestion Pipeline) which walks the data directories, parses each file's frontmatter (`version`, `status`, `layer`, `expose_to_chat`, `supplements_parent`, `canonical_id`), and emits a base manifest. The curated overrides file (`manifest_overrides.yaml`) carries routing intelligence that doesn't belong in individual files: `preferred_for` per query class per asset, cost weights, retrieval-cost tiers, exclusions, classification hints. The published manifest is the merge.

**Schema.** See Appendix A for the full schema. Key fields per asset: `canonical_id`, `path`, `version`, `status` (CURRENT | PREDECESSOR | ARCHIVE | SOURCE | QUALITY), `layer` (L1, L2, L2.5, L3, L3.5, L4, L5, L6), `expose_to_chat` (bool), `representations` (list of access patterns: file, chunks, embedding, graph, register), `preferred_for` (list of query classes), `interface_version`, `tool_binding` (for runtime dispatch), `cost_weight`, `always_required` (rare; restricted to absolute foundations).

**Consumers.** Four distinct readers use the manifest: the Chat API (runtime dispatch via the Router and Bundle Composer), the Build Pipeline (what to ingest, what shape each asset has), the governance tooling (drift detector, schema validator, mirror enforcer — replacing today's CANONICAL_ARTIFACTS dependence), and the LLM itself (a `Manifest-Query` tool exposes `query_manifest(question)` so the synthesizer can ask "what's available about Saturn" as a meta-query). All four consume the same manifest with stable `interface_version`.

**Migration from existing registries.** Today's `FILE_REGISTRY` and `CANONICAL_ARTIFACTS` continue to operate during the migration. Phase 1 of the master project plan introduces the Capability Manifest as a parallel artifact, validated against both existing registries (drift = bug). After two phase cycles of confirmed parity, governance tooling switches to read the manifest as the source of truth, and FILE_REGISTRY + CANONICAL_ARTIFACTS become reference artifacts (status: SUPERSEDED). The migration is bounded — explicit milestone in the project plan — and reversible if drift is detected.

**Manifest as a queryable asset.** The manifest itself is registered as an asset (canonical_id `MANIFEST`, layer `Foundation`, expose_to_chat `true`). This allows the LLM to reason about its own capabilities — useful for queries like "do you have any data on my parents?" where the answer depends on which assets are available. The synthesizer can call `query_manifest("parents")` and receive back the list of relevant assets. This turns the catalog into a capability the LLM can reason about, not just a configuration the chat dispatches over.

## §7 — Asset Lifecycle Management

Every asset belongs to exactly one of five lifecycle categories. The category is recorded in frontmatter (`status` field) and reflected in the manifest's `status` field. The manifest determines what the chat sees; the category determines policy.

**Canonical (CURRENT).** The current authoritative version. Exposed to chat (`expose_to_chat: true`), ingested, indexed in RAG tables, available to retrieval tools. Examples: `FORENSIC_ASTROLOGICAL_DATA_v8_0.md`, `CGM_v9_0.md`.

**Predecessor (PREDECESSOR).** Recent superseded version (within N=2 generations of CURRENT). Remains on disk for local audit. Not exposed to chat. Not ingested. Examples: `FORENSIC_ASTROLOGICAL_DATA_v6.0_ABHISEK_MOHANTY.md` (v6 when v8 is current), `MSR_v2_0.md` (v2 when v3 is current — archived earlier per existing pattern).

**Archive (ARCHIVE).** Long-superseded version (more than N=2 generations behind). Moved to `99_ARCHIVE/` directory. Available for long-term audit but not casually browsed. Not exposed to chat. Not ingested. Policy: at every phase close, the hygiene policy script moves predecessors that are now ≥2 generations behind to 99_ARCHIVE/.

**Source (SOURCE).** Authoring-time inputs whose content has been incorporated into a canonical file. Examples: `JHORA_TRANSCRIPTION_v8_0_SOURCE.md`, `EVENT_CHART_STATES_v1_0.md`. Lives in a `SOURCES/` subdirectory (or with `expose_to_chat: false` frontmatter pending the SOURCES migration). Used by the ingestion pipeline as input only; not exposed to chat.

**Quality (QUALITY).** Quality gates and audit records produced during build. Examples: `RED_TEAM_L2_5_v1_0.md`, `CROSS_REPORT_COHERENCE_AUDIT_v1_0.md`, `CGP_AUDIT_v1_0.md`. Live in place with `expose_to_chat: false`. Used by validators and governance tooling; not exposed to chat.

**Supplementary file handling.** Files whose name contains `SUPPLEMENT` (e.g., `FORENSIC_DATA_v8_0_SUPPLEMENT.md`) declare a `supplements_parent` frontmatter field pointing to their canonical parent. They share the parent's lifecycle category: when the parent moves to ARCHIVE, supplements move with it. The ingestion pipeline treats supplements as part of their parent for chunking purposes.

**Naming versus status discipline.** Filename versioning (`_v8_0.md`) records when the file was created. Frontmatter `status` records what the file is now. The manifest reads `status` (not filename) to determine category. This means a file can be created as v6.0 CURRENT and later become v6.0 ARCHIVE without renaming — preserving git history while updating policy.

## §8 — Retrieval Architecture

This section captures the central refinement of the 2026-04-27 brainstorm: replacing the original brief's "Tier 1 always-load" with a router-driven mandatory bundle composition over a Tier 1 *eligible* set.

**Tier 1 eligible set (the candidate pool).** The 11 files identified in the original retrieval brief as the highest-value mandatory candidates: `FORENSIC_ASTROLOGICAL_DATA_v8_0.md`, `LIFE_EVENT_LOG_v1_2.md`, `SADE_SATI_CYCLES_ALL.md`, `UCN_v4_0.md`, `CDLM_v1_1.md`, `RM_v2_0.md`, `CGM_v9_0.md`, plus the four L3.5 register JSONs (PATTERN, CONTRADICTION, CLUSTER, RESONANCE). Combined ~178K tokens. These are the *eligible* pool from which the per-query mandatory bundle is composed.

**Floor mandatory bundle (every query, regardless of class).** FORENSIC + CGM. ~40K tokens. Guarantees factual chart access (FORENSIC) and the holistic graph backbone (CGM) for any query. Fits inside every model's context window including DeepSeek V3 at 128K.

**Conditional adds (router-rule-based).** The Stage-2 Router classifies the query and adds Tier-1 files to the floor based on class:

- **Interpretive** (the 9 domain queries — career, finance, psychology, relationships, health, spiritual, children, parents, travel): adds UCN + CDLM + RM. Total bundle ~120K.
- **Predictive / time-indexed**: adds LEL + SADE_SATI. Total bundle ~70K alone, or layered with interpretive ~150K.
- **Discovery-layer queries** (patterns, contradictions, clusters, resonances): adds the 4 L3.5 registers. ~70K alone, layered as needed.
- **Cross-domain queries**: as interpretive but with stronger emphasis on CDLM cross-links during retrieval; bundle composition same as interpretive.
- **Holistic / "complete chart read"**: adds the full eligible set. ~178K. Only when the query explicitly asks for comprehensive coverage.
- **Pure factual lookup**: floor only. ~40K.

**B.11 (Whole-Chart-Read) enforcement.** The router's classification rules guarantee that any non-trivial interpretive query loads UCN + CDLM + CGM. B.11 is enforced at the rule level (the routing rules' classification of "interpretive" triggers the L2.5 substrate), not at the load level (unconditional loading regardless of query). This satisfies the original brief's elegant "B.11 satisfied by architecture" insight one level up.

**Tier 2 — On-demand retrieval pool.** Loaded by tool authorization in the QueryPlan. The MSR (the largest single asset at ~213K tokens; cannot fit in T1 anyway) is queried via SQL filter then reranked. Domain reports loaded by domain match. Matrix files loaded by topic. Remedial codex loaded for remedy-specific queries. Prediction ledger loaded for time-indexed queries. Temporal engines (when L5 lands) loaded for explicit timing queries. Tool inventory: see C2.3.

**Tier 3 — Lookup only.** The three large CSV files (`EPHEMERIS_MONTHLY_1900_2100.csv`, `ECLIPSES_1900_2100.csv`, `RETROGRADES_1900_2100.csv`). Never injected. Queried by date range via the Temporal tool against the storage layer.

**Representation pluralism.** Each asset can exist in multiple representations: full markdown file (narrative quotation), structured rows (typed metadata filter), vector embeddings (semantic similarity, secondary), graph nodes/edges (relational traversal), structured registers (filtered enumeration). The manifest declares which representations each asset offers. The Router's QueryPlan declares which representation matches the query intent. The Retrieval Tool Suite (C2.3) routes accordingly. This resolves the long-standing ambiguity in CONSUME_DESIGN about when to use which shape.

**KGAG strategy: build now, scale progressively.** The CGM graph walk tool (C2.3 sub-component) is built in B.6 alongside the rest of the retrieval suite. Its primary use, however, is gated by graph density: today's CGM has ~234 nodes and ~22 reconciled edges (sparse). The graph walk tool is enabled but rarely produces high-leverage signal until graph density grows past a threshold (rough heuristic: 5+ edges per node average, ~1000+ edges total). The architecture is correct now; the value will compound as the graph fills in.

**The transitional super-bundle (Phase 7 / panel mode).** Per the panel addendum content (now §10), the merged super-bundle handed to the panel adjudicator is the baseline bundle (from Stage 5) plus the deduplicated content of every unique extension that any panel member retrieved during Stage-7 generation. C2.6 owns this composition.

## §9 — The Router and QueryPlan

The Router is C2.1 — a stateless small-LLM service that converts free-form user queries into structured `QueryPlan` objects (schema in Appendix A). Every Consume request traverses the Router; the QueryPlan is the contract that drives every downstream stage.

**Query classes (the primary classification).** Seven canonical classes:

- **factual** — chart data lookup ("what's my Mercury position?"). Floor bundle only. No interpretation expected.
- **interpretive** — domain-bound interpretation ("what does my chart say about my career?"). Loads UCN+CDLM+RM on top of floor.
- **predictive** — time-indexed forward claim ("when will I see a career change?"). Loads LEL+SADE_SATI; triggers prediction ledger pre-stream write.
- **cross_domain** — interpretation spanning multiple domains ("how do my career and relationship patterns interact?"). Loads as interpretive with CDLM emphasis during retrieval.
- **discovery** — pattern-level meta-question ("what unusual patterns does my chart show?"). Loads the four L3.5 registers; queries the discovery surface.
- **holistic** — comprehensive chart read ("give me a complete picture"). Loads full eligible set; runs all retrieval tools; longest synthesis path.
- **remedial** — prescriptive query ("what remedies for my Saturn?"). Loads L4 Remedial Codex when available; loads relevant L1+L2.5 conditions as substrate.

**Dimensions beyond class.** The QueryPlan also captures: domains involved (subset of the 9 domain identifiers), planets and houses mentioned, dasha context need, forward-looking flag, audience tier (from auth), graph seed hints (CGM node IDs the router suggests), graph traversal depth, tools authorized, history mode (synthesized vs research per panel addendum), panel mode flag (from request), adjudicator model (when panel), expected output shape (single answer, three interpretations, time-indexed prediction, structured data).

**Bundle composition rules** (deterministic, encoded in C2.2a Rule Composer):

```
floor = [FORENSIC, CGM]                        # always

if class in [interpretive, cross_domain, holistic]:
  add [UCN, CDLM, RM]
if class in [predictive] or forward_looking:
  add [LEL, SADE_SATI]
if class in [discovery, holistic]:
  add [PATTERN_REGISTER, CONTRADICTION_REGISTER,
       CLUSTER_ATLAS, RESONANCE_REGISTER]
if class == holistic:
  add all remaining T1 eligible
```

These rules are the rule-based substrate. C2.2b Bundle Augmenter (the Stage 4.5 LLM checkpoint) reviews the rule output and may suggest additions for edge cases the rules don't cover.

**Router model selection.** Default: Claude Haiku 4.5 (or current Anthropic small flagship). Configurable via C6.3 to Gemini Flash, GPT-mini, or DeepSeek's smallest variant. Tiered router (small → escalate to large on low-confidence classifications) is a future enhancement noted at §16.

**QueryPlan as a versioned contract.** Schema versioning per §15 interface contracts. Adding new fields is additive; removing or repurposing fields requires a major version bump. The current schema is `v1.0`.

## §10 — Synthesis Strategies (Single-Model and Panel)

Stage 7 is owned by C3.2 Synthesis Orchestrator. Two strategies; panel-mode flag in QueryPlan selects.

### §10.1 Single-Model Strategy

The user-selected model receives the validated bundle, system prompt (with style suffix), conversation history (per `history_mode`), and the full Retrieval Tool Suite as available tools. The model may call additional tools during synthesis (extension). Streams response token-by-token. Logs synthesis prompt version into audit trail.

### §10.2 Panel Strategy

Opt-in via the panel checkbox in the Composer. When `panel_mode: true`:

**Panel Resolution.** The Panel Resolver computes the panel composition: three models, one from each non-adjudicator family. The user's selected model's family is excluded (family-level self-preference defense per the LLM-as-judge literature). The default panel slate (configurable via C6.3) is `claude-opus-4-7`, `gpt-5`, `gemini-3-pro-preview`, `deepseek-v3`. Panel size is always 3 (3 panel + 1 adjudicator = 4 large LLM calls), regardless of which family the user selected.

**Bundle Handoff.** Each of the three panel members receives the identical Stage-5 retrieval bundle (computed once, shared) — the uniform substrate for interpretive-divergence measurement.

**Parallel Panel Generation.** Three asynchronous `streamText` calls run in parallel. Each carries the same system prompt (with style suffix), same conversation history (per `history_mode`), same bundle, same tool surface. Panel members are not informed they are part of an ensemble; the system prompt does not mention adjudication or panels (naive-panel discipline). Each member may extend the bundle via additional tool calls during generation; C2.5 Tool-Call Cache prevents duplicate execution. Each member's full retrieval transcript is captured.

**Concurrent Retry.** On any panel-member API failure, retry fires concurrently while other panel members continue running. Up to N=3 retries per member within a 60-second total time budget. Math: 99% provider reaches ~99.9999% per-member success across four total attempts; even a degraded 90% provider reaches ~99.99%.

**Failure Handling.** Default: hard halt on exhausted retries. The user receives an explicit error identifying which panel member failed. Per-user setting (C5.5) `degrade_mode_allowed`: when on, exhausted retries proceed with 2-of-3 synthesis; audit trail flags `degrade_mode_triggered: true`; M5 calibration excludes degraded turns from training data.

**Panel-Member Validation.** Before adjudication, each panel response runs through the C3.1 structural validator stack. A panel response that fails a validator is marked failed; if hard-halt mode, the panel turn fails; if degrade-mode, the failed response is excluded from synthesis.

**Anonymization.** The (validated) panel responses are labeled A / B / C with model identity stripped, and shuffled into a randomized order. The adjudicator receives them without knowing which model produced which.

**Adjudicator Synthesis (Step 5.6).** The adjudicator (the user's selected model) is invoked with the synthesis prompt, the merged super-bundle (baseline bundle + deduplicated panel-member extensions, composed by C2.6), the three anonymized randomized panel responses, the per-panel-member retrieval transcripts (so the adjudicator can see which member fetched what), the synthesis rubric (B.1, B.3, B.10, B.11), and the style suffix. The adjudicator produces a single synthesized response that draws on whatever is correct, complete, or grounded in the panel responses, integrates its own perspective on the super-bundle, and produces synthesis reasoning. The adjudicator does not classify divergences (offloaded to the next step).

**Divergence Classification (Step 5.6b).** A separate small classifier model (default: the adjudicator's family's smallest variant — Haiku for Claude adjudicator, Flash for Gemini adjudicator, etc.) reads the three panel responses + the adjudicator's synthesis + the super-bundle, and classifies every detected divergence using the five-class taxonomy:

- `DIS.class.fact` — disagreement on a factual claim
- `DIS.class.interpretation` — same data, different reads
- `DIS.class.computation` — disagreement on a derivation result
- `DIS.class.scope` — disagreement on the scope of the question being answered
- `DIS.class.extension` — *new in this document, contributed by panel addendum* — different choices of additional retrieval at panel-member level (different panel members extended the bundle differently; not interpretation divergence but attention divergence)

Output is a structured `divergences` list appended to the audit-trail event.

**Three-Interpretation Consolidation Rule (revised).** For interpretive queries, each panel member's response carries three interpretations (per P7 structural). The adjudicator's synthesis consolidates the panel's nine total interpretations into a single three-interpretation structure visible to the user. The consolidation rule (revised in this document from the panel addendum's earlier version): *select three interpretations that maximize coverage of the explanatory possibility space, subject to the constraint that every selected interpretation must cite L1 fact_ids per B.3 derivation-ledger discipline.* Ungrounded interpretations are excluded from the user-visible three but logged in the audit trail as `interpretation_candidate_ungrounded` for outcome-driven resolution by M5. Where multiple panel members converge on the same interpretation, the convergence is preserved as audit metadata for calibration use but does not bias selection. The principle: orthogonality + grounding > consensus.

**Conversation History Modes.** Per-user setting `panel_research_mode`. When off (default): synthesized history (panel members see prior synthesized assistant turns; preserves user-conversation coherence; matches single-model behavior). When on: research mode (panel members receive only the system prompt and current user query; preserves naive-panel independence at the cost of multi-turn references). The audit trail records `history_mode: synthesized | research` per turn for M5 stratification.

**Panel Persistence.** The full `panel_metadata` (Appendix A schema) is persisted alongside the message: panel composition, super-bundle hash, per-member responses with retrieval transcripts and validator votes, anonymization key, adjudicator synthesis with reasoning and consolidation rule, divergence classifications, retry counts, degrade flag, history mode, total cost and latency.

**UI Interaction.** The conversation panel renders only the synthesized response — single-model and panel-mode messages are visually identical in the conversation. The Audit View (C5.4) reveals the full panel data on inspect, with content tier-filtered.

## §11 — The LLM-Mediated Checkpoints

The 2026-04-27 brainstorm established Principle P.8: domain knowledge → LLM; integrity / lookup / persistence / algorithmic execution → deterministic. Three new LLM checkpoints embody this. Their purpose is to inject domain-knowledge judgment at decision points the deterministic implementations could not handle.

**Stage 4.5 — Bundle Augmenter (C2.2b).** Inputs: rule-composed bundle + QueryPlan + Manifest. Output: augmented bundle (additions, removals, or unchanged). Domain-knowledge contribution: the rules are coarse; the augmenter is fine-grained. It catches edge cases like "this query is forward-looking but the rules didn't add the Pattern Register because they don't know the discovery surface has high-relevance forward-looking patterns" or "this is cross-domain but the rules added the Financial L3 report when the MSR signal density would actually serve better." Cost: one small-model call per query (~$0.001-$0.005). Latency: ~50-100ms.

**Stage 5.5 — MSR Reranker (C2.4).** Inputs: query + 60-100 candidate signals from MSR-SQL filter. Output: top 25 ranked by query-relevance. Domain-knowledge contribution: SQL filters by labeled metadata; the reranker reads each signal in light of the query and surfaces signals where labeled domain ≠ query domain but contextual relevance is high. Replaces the prior significance-weighted sort, which had no domain awareness. Cost: one small-model call (~$0.005). Latency: ~150-300ms.

**Stage 8.5 — Semantic Discipline Gate (C3.3).** Inputs: synthesis output + query class. Output: pass / fail with reason; on fail, one revision pass triggered. Domain-knowledge contribution: structural gates check presence (are three interpretations there? is a falsifier named?); the semantic gate checks quality (are the three meaningfully orthogonal? is the falsifier specific enough to be falsifiable?). Cost: one small-model call. Latency: ~100-200ms.

Total addition over the prior deterministic-heavy version: three small-model calls, ~$0.01 per query, ~300-600ms latency. Single-model totals: 4 small + 1 large LLM call (Router, Augmenter, Reranker, Synthesizer, Semantic Gate). Panel-mode totals: 5 small + 4 large LLM calls (Router, Augmenter, Reranker, 3 Panel members, Adjudicator, Divergence Classifier, Semantic Gate).

Each checkpoint is independently toggleable via C6.3 Configuration Service. During testing/validation phase (per native priority), all three are on by default. The M5 Calibration Loop captures whether each checkpoint changes the outcome — over time, rules underneath the augmenter improve and it may become optional; reranker thresholds tune; semantic gate gains additional checks.

**What stays deterministic (and why).** Per Principle P.8: structural validators (P1, P2, P5, P3, P4, P7-structural, P8-structural, P9) are integrity checks, not domain judgments — LLM mediation here would be a regression in consistency. Manifest reads are data lookups. Audit trail and prediction ledger writes are persistence. Graph BFS is pure algorithmic execution once seeds and depth are decided (the *decision* is LLM-mediated; the *execution* is mechanical). Swiss Ephemeris computations are calendar arithmetic; domain knowledge doesn't change Saturn's position on a date — interpretation of what the position means is LLM-mediated at synthesis, not at lookup.

## §12 — Discipline and Disclosure

**The validator stack.** Validators run during ingestion (C1.2 — gate writes to RAG tables), at Stage 6 of the pipeline (C3.1 — bundle integrity), and at Stage 8 (C3.1 — synthesis output). Today live: P1 (layer separation), P2 (citation discipline), P5 (signal-id resolution). Coming online per parent design phases: P3 (whole-chart-read enforcement on bundle — verifies L2.5 substrate is included in any non-trivial interpretive query's bundle), P4 (no-fabrication on synthesis — every numerical chart value in the output traces to a fact in the bundle), P7-structural (three interpretations present count check), P8-structural (falsifier present for time-indexed claims), P9 (audit-trail completeness). Plus the new P7-semantic and P8-semantic checks owned by C3.3 Semantic Discipline Gate (orthogonality + falsifier specificity).

**Three-interpretation gate (P7).** Applies to interpretive-class queries. Each interpretive response carries three interpretations. The semantic gate verifies orthogonality. In panel mode, the consolidation rule from §10.2 governs how the panel's nine total interpretations reduce to three.

**Falsifier gate (P8).** Applies to time-indexed claims. Every forward-looking claim names a falsifier — a specific observable that, if it doesn't manifest within the named horizon, falsifies the prediction. The semantic gate verifies specificity. The prediction ledger logs the falsifier alongside the prediction.

**Audit trail (P9).** Every query writes a complete audit-trail event (C4.1) — capability snapshot, QueryPlan, bundle hash, validator votes, synthesis prompt version, panel_metadata where applicable, classifier output, semantic gate result, response, per-LLM-call metrics. The audit trail is the substrate for the M5 Calibration Loop and the surface for the Audit View (C5.4).

**Prediction ledger pre-stream write.** For predictive-class queries, all predictive claims are written to the prediction ledger (C4.2) BEFORE the response begins streaming. In panel mode, this means 4× ledger entries per predictive panel query (3 panel + 1 adjudicator synthesis). Pre-stream discipline is sacrosanct per the M5 Learning Layer rule that outcome-blind prediction logging cannot be retroactive.

**Disclosure-tier filter.** Owned by C3.5. Applies to the synthesized response shown in the conversation AND to the audit-view content. Four tiers: super_admin (full content, all internal terminology, all panel data), acharya_reviewer (full content + methodology disclosure for peer review of the instrument), client (their own chart only; redacted internal terminology; calibration bands mandatory; no fate-adjacent assertions), public_redacted (no individual chart attribution; aggregated cohort findings only; calibration bands required). Today only super_admin tier is active; client lands at M6, public_redacted at M10. The architecture is forward-compatible — the filter component exists; tier-specific rules are added at their landing phase.

## §13 — Audit and Calibration Substrate (M5)

The architecture is built so that every query produces data that compounds value over time. This is the M5 Learning Layer substrate.

**What gets logged per query.** The audit-trail event (C4.1) is rich by design. Per query: which manifest version was active, which assets were loaded into the mandatory bundle (and which were *not*, with reasons), which retrieval tools fired and what they returned, which validators voted what, which synthesis prompt version was used, the response text, per-LLM-call token / latency / cost. In panel mode: all four panel-member responses with their retrieval extensions and validator votes, the adjudicator's synthesis reasoning, the divergence classifications. In single-model: a smaller record but the same shape. Plus, for predictive queries, the prediction ledger entries (C4.2) with confidence, horizon, falsifier.

**The calibration loop (M5).** Today scaffolded; activated at M3+. Reads from C4.1 + C4.2 over the full project history. Emits per-component improvement signals: which bundle-composition rules correlate with high-quality outcomes (improves C2.2a rules); which reranker decisions correlate with retrieval quality (improves C2.4 model or threshold); which synthesis prompt versions correlate with outcome accuracy (improves C3.4 registry); which panel members are reliable on which question types (drives panel-slate evolution and per-model weighting); which retrieval-extension patterns correlate with better answers (informs tool-suggestion logic). The loop closes the feedback: outputs of the calibration loop become inputs to the next phase's design.

**Self-improving architecture.** The combination of comprehensive audit + outcome-blind prediction ledger + per-component telemetry + structured divergence classification means the architecture has the substrate for continuous improvement built in. Panel mode is the highest-fidelity data source because every panel turn produces multi-model comparisons over identical inputs. Even single-model queries contribute calibration signal (which prompts work; which retrieval bundles correlate with quality).

**The research-instrument future.** The same calibration substrate, when extended across multiple natives, becomes the dataset for cross-chart pattern discovery — the "research instrument for Jyotish as a discipline" the project mission describes. Multi-native namespacing in the manifest and storage layer (per §14) makes this forward-compatible without architectural rework.

## §14 — Multi-Model and Multi-Native Compatibility

**Multi-model.** C6.1 LLM Provider Abstraction is the seam. Adding a new provider = implementing one adapter against the uniform `streamText` interface, registering capability flags. No changes propagate to D2 or D3. The architecture treats provider variation (different context windows, different tool-use protocols, different prompt-caching capabilities) as the default. Panel mode's fan-out across four labs is the canonical demonstration: each lab is just one model in the panel slate; expanding to a fifth lab is config-only.

**Per-model context window awareness.** The Bundle Composer (C2.2) consults C6.1 capability flags during composition. If the selected model (or any panel member) cannot fit the rule-composed bundle, the composer either omits non-floor adds (gracefully degrading toward the floor) or fails the request with explicit "context exceeded" error. The router can incorporate model selection into its bundle-composition logic if a future need arises. Today's slate composition (Claude / GPT / Gemini / DeepSeek) is constrained by DeepSeek V3's 128K context — the floor + interpretive (~120K) fits; the floor + interpretive + predictive (~150K) does not fit DeepSeek but fits the others. The router degrades for DeepSeek panel turns by prioritizing essential adds.

**Prompt caching strategy.** C6.1 capability flags include `prompt-caching`. For models supporting it (Claude today; OpenAI's automatic caching for GPT-5+; Gemini emerging support), the system prompt + stable bundle prefix is cached. Marginal cost for repeat queries on the same chart drops dramatically. Panel mode benefits less because each panel member's lab differs, but adjudicator caching still helps. No application-layer code changes; the abstraction handles cache hints.

**Multi-native forward-compatibility.** Today the system is single-native (Abhisek's chart). Tomorrow, multiple natives will use the same instrument. Architectural implications:

The Capability Manifest gains per-native namespacing — each asset declares `native_id` (or `universal` for cross-native assets like glossaries). Storage Layer C1.3 partitions per-native data (MSR signals, prediction ledger, audit log) by native_id. Router C2.1 reads native_id from auth context and routes accordingly. The Composer C5.2 gains a chart selector (or it's implicit from auth).

Cross-native research queries (e.g., "what patterns appear across charts with similar Saturn placements?") are a separate query class — the router classifies them differently, the bundle composition aggregates over multiple natives' MSR tables, the synthesis surfaces distribution properties rather than per-native facts. The architecture supports this without forking — adding the cross-native query class to the router's classification rules and adding a `query_msr_aggregate(filter, predicate)` tool to C2.3 covers it. The work is bounded; today's single-native deployment is a special case of the multi-native architecture.

## §15 — Interface Contracts (Load-Bearing)

Six interfaces hold the architecture together. If these stay stable, components evolve freely behind them. Each carries an `interface_version` field (semantic versioning); minor bumps signal additive changes; major bumps signal breaking changes that other components must adapt to.

**`Manifest.read(canonical_id) → AssetEntry`** (C1.1). The catalog interface. Every consumer of "what data exists" goes through this. AssetEntry shape is in Appendix A.

**`QueryPlan`** (emitted by C2.1, consumed by C2.2 + C2.3 + C3.2). The structured object the Router emits and the rest of the pipeline consumes. Schema in Appendix A. Most consequential contract in the system.

**`Bundle`** (emitted by C2.2, consumed by C3.2). The mandatory-context payload. Schema in Appendix A.

**`ToolBundle`** (emitted by each C2.3 tool, consumed by C2.6 + C3.2). The uniform return shape from any retrieval tool. Schema in Appendix A. Keeping this uniform is what makes the Retrieval Tool Suite plug-in style.

**`AuditEvent`** (emitted by every component, consumed by C4.1). The structured audit record. Schema in Appendix A. Versioned because schema evolution matters for long-term calibration data.

**`streamText(model_id, messages, tools, options) → stream`** (C6.1). The LLM Provider Abstraction interface. Every component that calls an LLM goes through this.

These six are versioned in the C6.2 Schema Registry. Cross-component changes that would touch any of them go through an explicit version-bump review.

## §16 — Evolution Paths

Nine evolution vectors anticipated. Each is absorbed by specific components without architectural rework.

**V1 — New asset types.** L4 Remedial Codex directory materializes; L5 Temporal Engines directory arrives; cross-native registers emerge. Absorbed by C1.1 (manifest schema) + C1.2 (new chunkers). Zero impact on D2-D5.

**V2 — Better retrieval models.** Significance-weighted sort → small LLM reranker (today) → fine-tuned cross-encoder → learned ranker from M5. Absorbed by C2.4. Stable interface; evolving implementation.

**V3 — More LLM providers.** Mistral, Grok, on-prem models. Absorbed by C6.1. New adapter; no other changes.

**V4 — More validators.** P3, P4, P7-semantic (in C3.3), P8-semantic (in C3.3), P9, plus future validators per phase plan. Absorbed by C3.1 plug-in registry.

**V5 — Bundle composition rule maturation.** M5 calibration learns which assets correlate with which outcomes; rules in C2.2a get smarter; the C2.2b augmenter becomes optional. Absorbed by C2.2 — rule layer and augmenter are independently evolvable sub-components.

**V6 — Panel slate evolution.** Claude versions advance, GPT-6 ships, DeepSeek V4 replaces V3. Absorbed by C6.3 — slate is config, not code.

**V7 — Multi-native arrival.** Per-native namespacing across C1.1, C1.3, C2.1, C5.5; cross-native query class added to C2.1 + C2.3.

**V8 — Mobile / alternative interface.** Absorbed entirely by D5. New rendering layer; same C5.1 Chat API contract.

**V9 — On-prem / air-gapped deployment.** Absorbed by C1.3, C6.1, deployment configs. Components don't change; their deployment changes.

The components most exposed to evolution (C2.2, C3.2, C2.3) are the architectural stress points. Their interfaces get the most discipline.

## §17 — Migration from Current State

The architecture isn't built from zero. The current state (per the 2026-04-27 codebase audit) is the starting point.

**What exists today.** A working Consume tab with 8 hardcoded retrieval tools (`get_birth_data`, `get_planetary_positions`, `get_dasha_periods`, `get_layer_document`, `search_signals`, `get_domain_report`, `get_transits`, `get_pyramid_status`). 8 models in the registry across Claude / Gemini / DeepSeek. A streaming Chat API. The full data corpus L1, L2, L2.5, L3, L3.5 populated. RAG tables (chunks, embeddings, graph nodes, graph edges) populated but unused by chat. FILE_REGISTRY and CANONICAL_ARTIFACTS as parallel registries. Python sidecar with chunkers, graph extractors, validator stack (P1, P2, P5 today). Prediction ledger scaffolded. Panel mode designed but not built.

**What gets retired (not deleted; status: SUPERSEDED).** The dual `FILE_REGISTRY` + `CANONICAL_ARTIFACTS` registries (subsumed by C1.1 Capability Manifest after migration cycles). The 8 hardcoded tools (replaced by C2.3 Retrieval Tool Suite — though some tools persist as the suite's foundational members). The static `get_layer_document` mandatory L2.5 routing instruction (replaced by C2.2 router-driven bundle composition).

**What gets migrated (extended, not replaced).** The Python sidecar evolves into the home for C1.2 Ingestion Pipeline + heavy retrieval tools in C2.3. The model registry evolves into C6.1 Provider Abstraction with capability flags. The validator stack (P1, P2, P5) evolves into C3.1 Validator Service with the plug-in registry pattern. The conversation messages table extends with `panel_metadata` JSONB column. The current Composer evolves to add the panel checkbox + audit-view affordance. The current Conversation Renderer extends to support the audit view. The prediction ledger formalizes into C4.2 with the pre-stream write discipline.

**What gets created from scratch.** The Capability Manifest (C1.1). The Router (C2.1). The Bundle Composer + Augmenter (C2.2). The Reranker (C2.4). The Tool-Call Cache (C2.5). The Bundle Assembler (C2.6). The Synthesis Orchestrator (C3.2) — orchestrating around the existing single-model path and adding the panel strategy. The Semantic Discipline Gate (C3.3). The Audit View UI (C5.4). The Synthesis Prompt Registry (C3.4). The Calibration Loop scaffold (C4.3). OpenAI/GPT integration (C6.1 adapter).

**The phased migration.** The Master Project Plan (Artifact 2 in this planning effort) details the phasing. Each phase is bounded; each phase has clean rollback; the system remains functional throughout the migration. Phases 0-5 deliver a working v2.0 chat with deterministic retrieval and single-model synthesis. Phase 6 lands the LLM checkpoints (the accuracy upgrades). Phase 7 lands panel mode. Phase 8 lands the audit view. Phase 9 lands advanced retrieval (graph walk, vector search). Phase 10 lands the calibration loop substrate.

Throughout the migration, single-model behavior never regresses. New behavior is additive and feature-flag-gated.

## §18 — Provenance

This document is the synthesis of a sustained design conversation. Honoring the lineage:

**The retrieval brief** (`MARSYS_JIS_Architecture_Review_Brief.docx`, authored using Sonnet, April 2026) introduced the Tier-1 / Tier-2 / Tier-3 classification, the token-budget reckoning, the Agentic KGAG combination, and the eight open architectural questions. Its identification of the Tier-1 eligible set is preserved here verbatim; its commitment to "always-load Tier 1" is replaced with router-driven composition (§3 Principle P.9, §8, §9) per the multi-model context-window reality and per the panel-mode cost economics.

**The Consume design** (`CONSUME_DESIGN_v0_1.md`, Cowork Opus 4.7, 2026-04-26) introduced the eight-stage pipeline, the capability manifest concept, the layer anatomy, the algorithm walkthrough, the layer epistemology, and the disclosure tiers. Its eight-stage pipeline is preserved here as §5 with the three new LLM checkpoints inserted at 4.5, 5.5, 8.5. Its capability manifest concept is implemented as C1.1 in §6. Its disclosure tiers are implemented as C3.5 in §12.

**The panel addendum** (`PANEL_SYNTHESIS_ADDENDUM_v0_1.md`, Cowork Opus 4.7, 2026-04-27, content at v0.2 post-critique) established the panel-mode synthesis strategy, the family-level adjudicator exclusion, the merged super-bundle, the orthogonality+grounding consolidation rule, the concurrent-retry failure handling, the opt-in 2-of-3 degrade mode, the request-scoped tool cache, the adjudicator/classifier split, and the new `DIS.class.extension` taxonomy class. Its full content is folded into §10 (Panel Strategy) of this document.

**The 2026-04-27 brainstorm.** Native and Cowork iterated through the data-layer integration, the catalog/lifecycle/representation/exposure/pipeline debates, the response to the critique pass, the LLM-checkpoint principle, the component decomposition, the planning workflow. The architectural decisions surfaced in that brainstorm are encoded throughout this document.

**The implementation brief that this supersedes.** `PANEL_IMPLEMENTATION_BRIEF_v1_0.md` (Cowork Opus 4.7, 2026-04-27, status AUTHORED) was authored to instruct Claude Code to build panel mode against the current Consume architecture (Path 2 transitional). With this holistic architecture in place, panel mode becomes Phase 7 of the Master Project Plan; the brief is superseded; its content is absorbed into Phase 7's execution brief when authored.

The four superseded documents remain on disk with `status: SUPERSEDED` for historical audit. New work proceeds against this v1.0 specification.

## §19 — Open Questions (RESOLVED 2026-04-27 by native)

All three questions resolved by native approval same-session as document authoring. Recorded for provenance:

**Q1 — Document scope. RESOLVED: stay as elaboration.** This v1.0 does not subsume `PROJECT_ARCHITECTURE_v2_2.md`'s Consume/Retrieval-related sections (§D.4, §H.4). PROJECT_ARCHITECTURE remains the umbrella reference; this document elaborates the Consume + Retrieval slice underneath it. The relationship: PROJECT_ARCHITECTURE establishes the layer pyramid, the architectural principles (B.1–B.12), and the system-wide structure; this v1.0 specifies how the Consume + Retrieval portion realizes those structures concretely.

**Q2 — Manifest replacement timing. RESOLVED: aggressive single-phase migration.** The Capability Manifest migration from FILE_REGISTRY + CANONICAL_ARTIFACTS happens in a single phase (Phase 1) with hard cutover, not parallel operation across multiple phases. Phase 1's deliverables include: building the manifest, migrating registry data into it, switching governance tooling (drift detector, schema validator, mirror enforcer) to read from the manifest, and flipping FILE_REGISTRY and CANONICAL_ARTIFACTS to status SUPERSEDED. Higher upfront migration risk; cleaner foundation; consistent with native priority on accuracy over caution.

**Q3 — Cross-native query class addition timing. RESOLVED: add at Phase 2.** Cross-native query class is added to the router's classification rules at Phase 2 (deferred-but-available), even though multi-native deployment is not on the immediate roadmap. The implication: per-native namespacing is built into the storage layer at Phase 1 (not just placeholder `native_id: "universal"` everywhere); the manifest's per-native fields are populated correctly from Phase 1; the router classifies cross-native queries from Phase 2; the retrieval suite includes a `query_msr_aggregate` placeholder tool from Phase 2 (returns "multi-native not yet deployed" until enabled). Higher upfront work; the architecture is genuinely multi-native-ready from Phase 1 forward.

## §20 — Adoption and Next Steps

This document is `DRAFT` until native review and approval. The path to adoption mirrors the panel addendum and CONSUME_DESIGN paths:

**Step 1 — Native review.** Native reads, annotates, requests revisions if any. This is the review you said you wanted before the master project plan is written.

**Step 2 — Adoption mechanism.** Either ND.2 (a binding native directive on B.6+ to honor this architecture) or a `PHASE_B_PLAN` amendment to v1.0.4 that elevates this document as the canonical Consume + Retrieval architecture. ND.2 is faster; the PHASE_B amendment is more durable. Recommendation: ND.2 first, with the requirement that B.6 / B.7 phase briefs incorporate this document's content into their per-task acceptance criteria.

**Step 3 — Master Project Plan (Artifact 2).** Once this document is adopted, Cowork (Opus) authors `MARSYS_JIS_PROJECT_PLAN_v1_0.md` — the phased work breakdown across the ten phases of §17. Each phase: dependencies, components touched, deliverables, acceptance criteria, parallelization opportunities, rollback path, test strategy. This is the second of three planning artifacts.

**Step 4 — Phase 0 Execution Brief (first Artifact 3).** Cowork authors `EXEC_BRIEF_PHASE_0_v1_0.md` — the executor brief Claude Code (Sonnet) reads and builds against. Phase 0 is the Foundation phase: D6 components (Provider Abstraction with OpenAI integration, Schema Registry, Configuration Service, Telemetry stubs).

**Step 5 — Iterative execution.** Each subsequent phase: Cowork authors the next execution brief; Claude Code executes; Cowork observes completion and authors the next brief. Master plan stays stable; briefs are short-lived. Parallel streams enabled (per native confirmation 2026-04-27) where domain isolation is clean.

The M2/B.5 governance/discovery stream resumes in parallel with Phase 0+ execution per native's pause/resume direction.

---

## Appendix A — Schema Definitions

Concise schema sketches for the six load-bearing types. Full JSON Schema definitions live in C6.2 Schema Registry.

### `AssetEntry`

```yaml
asset_entry:
  canonical_id: string             # stable identifier (e.g. "FORENSIC", "CGM")
  path: string                      # filesystem path
  version: string                   # e.g. "v8.0"
  status: CURRENT | PREDECESSOR | ARCHIVE | SOURCE | QUALITY
  layer: L1 | L2 | L2.5 | L3 | L3.5 | L4 | L5 | L6 | Foundation
  expose_to_chat: bool
  representations: [file | chunks | embedding | graph | register]
  preferred_for: [query_class]      # routing hints
  always_required: bool             # rare; restricted to absolute foundations
  interface_version: string
  tool_binding: string?              # which retrieval tool serves this asset
  cost_weight: float                 # for cost-aware planning
  supplements_parent: canonical_id?  # for supplement files
  fingerprint: sha256                # change detection
  native_id: string                  # multi-native namespacing (default: "universal")
```

### `QueryPlan`

```yaml
query_plan:
  query_plan_id: uuid
  query_text: string
  query_class: factual | interpretive | predictive | cross_domain | discovery | holistic | remedial
  domains: [string]                  # subset of 9 domains
  planets: [string]
  houses: [int]
  dasha_context_required: bool
  forward_looking: bool
  audience_tier: super_admin | acharya_reviewer | client | public_redacted
  graph_seed_hints: [string]         # CGM node IDs
  graph_traversal_depth: int
  bundle_directives:
    floor_overrides: [canonical_id]?
    conditional_overrides: object?
  tools_authorized: [tool_name]
  history_mode: synthesized | research
  panel_mode: bool
  adjudicator_model_id: string?
  expected_output_shape: single_answer | three_interpretation | time_indexed_prediction | structured_data
  router_confidence: float
  router_model_id: string
  manifest_fingerprint: sha256
  schema_version: "1.0"
```

### `Bundle`

```yaml
bundle:
  bundle_id: uuid
  query_plan_reference: query_plan_id
  manifest_fingerprint: sha256
  mandatory_context:
    - canonical_id
    - version
    - content_hash
    - token_count
    - role: floor | interpretive | predictive | discovery | holistic
    - source: rule_composer | bundle_augmenter
  retrieved_context:                 # populated post-Stage 5
    - tool_name
    - tool_invocation_params
    - tool_bundle_id
    - token_count
    - validator_votes: object
  total_tokens: int
  bundle_hash: sha256
  schema_version: "1.0"
```

### `ToolBundle`

```yaml
tool_bundle:
  tool_bundle_id: uuid
  tool_name: string
  tool_version: string
  invocation_params: object
  results:
    - content
    - source_canonical_id
    - source_version
    - confidence: float?
    - significance: float?
    - signal_id: string?
  served_from_cache: bool
  cache_key: string?
  latency_ms: int
  result_hash: sha256
  schema_version: "1.0"
```

### `AuditEvent`

```yaml
audit_event:
  event_id: uuid
  timestamp: iso8601
  conversation_id: uuid
  message_id: uuid
  user_id: string
  audience_tier: string
  query_plan: QueryPlan              # full structure
  manifest_fingerprint: sha256
  bundle_id: uuid
  bundle_hash: sha256
  retrieval_transcripts: [ToolBundle]
  validator_votes: object
  synthesis_prompt_version: string
  llm_calls:
    - call_type: router | augmenter | reranker | synthesizer | panel_member | adjudicator | classifier | discipline_gate
    - model_id: string
    - tokens: {input, output, cached}
    - latency_ms: int
    - cost_estimate_usd: float
  panel_metadata: PanelMetadata?      # when panel_mode was used; full schema per panel addendum
  semantic_gate_result: pass | fail
  semantic_gate_reason: string?
  response_text: string
  total_cost_estimate_usd: float
  total_latency_ms: int
  schema_version: "1.0"
```

### `PanelMetadata`

Full schema per panel addendum §7. Key fields: `panel_composition` (adjudicator + members + slate version + resolver rule + degrade flags + history_mode), `merged_super_bundle` (baseline hash + extensions per member + super hash + dedup count), `panel_responses[]` (per member: text + tool_calls + tokens + latency + finish_reason + validator_votes + extracted_predictions + retry_attempts), `anonymization` (label-to-model + presentation order), `adjudicator_synthesis` (text + reasoning + interpretations_consolidated + tokens + latency), `divergence_classification` (classifier model + tokens + latency + divergences[]), `panel_total_cost_estimate_usd`, `panel_total_latency_ms`.

## Appendix B — Glossary

Inline glossary of project-specific terms used in this document. Standard Jyotish terms are in `MARSYS_JIS_Architecture_Review_Brief.docx` Appendix B; not duplicated here.

**Acharya-grade.** The quality bar at which an independent senior Jyotish acharya reviewing the output reaches one of three judgments: "this is my own level", "this is above my own level", or "this reveals things I would not have seen on first pass".

**Audit View.** The expandable inspect affordance per assistant message in the Consume UI (C5.4). Surfaces the full audit-trail data for the message.

**B.11.** Whole-Chart-Read Protocol (`PROJECT_ARCHITECTURE §H.4`). Every interpretive query routes through the L2.5 holistic synthesis substrate before producing a domain-specific answer.

**Bundle.** The mandatory-context payload for a query, composed by C2.2 from the Tier-1 eligible set per the Router's QueryPlan.

**Capability Manifest.** Single source-of-truth catalog of available data assets (C1.1). Auto-derived + curated.

**DIS.class.* taxonomy.** The disagreement classification scheme for multi-agent disagreements (`GOVERNANCE_INTEGRITY_PROTOCOL §K`). Five classes: fact, interpretation, computation, scope, mirror_desync. Plus the new `extension` class added in this document for panel-mode attention divergence.

**Domain knowledge (in this document's principle P.8).** Astrology-specific interpretive knowledge — the kind of judgment a senior acharya brings.

**Family-level exclusion.** Panel composition rule that excludes the adjudicator's entire provider family (Anthropic / OpenAI / Google / DeepSeek) from the panel.

**Floor.** The minimum mandatory bundle loaded for every query: FORENSIC + CGM. ~40K tokens.

**Manifest fingerprint.** SHA256 of the Capability Manifest at a given moment. Logged into every audit-trail event for deterministic audit reconstruction.

**Naive panel.** The discipline that panel members are not informed they are part of an ensemble — system prompt does not mention adjudication, panels, or other LLMs.

**P.N (validator).** Numbered validator in the C3.1 Validator Service. P1 layer separation, P2 citation, P3 whole-chart-read, P4 no-fabrication, P5 signal-id resolution, P6 UCN-vs-L3 consistency, P7 three-interpretation, P8 falsifier, P9 audit-trail completeness.

**QueryPlan.** Structured object emitted by the Router (C2.1) that drives every downstream stage. Schema in Appendix A.

**Super-bundle.** Merged bundle handed to the panel adjudicator at Stage 5.6: baseline bundle + deduplicated panel-member extensions. Composed by C2.6.

**Tier-1 eligible set.** The 11 files identified as candidates for inclusion in the per-query mandatory bundle. Different from Tier-1-always-load (the original brief's terminology) which this document replaces.

---

*End of MARSYS_JIS_ARCHITECTURE_v1_0.md (DRAFT, 2026-04-27). Awaits native review and approval. On adoption, status flips to CURRENT and four predecessor documents (CONSUME_DESIGN_v0_1.md, PANEL_SYNTHESIS_ADDENDUM_v0_1.md, MARSYS_JIS_Architecture_Review_Brief.docx, PANEL_IMPLEMENTATION_BRIEF_v1_0.md) move to status SUPERSEDED. Next concrete artifact: MARSYS_JIS_PROJECT_PLAN_v1_0.md.*
