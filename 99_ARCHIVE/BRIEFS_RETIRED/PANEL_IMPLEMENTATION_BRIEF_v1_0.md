---
artifact: PANEL_IMPLEMENTATION_BRIEF_v1_0.md
status: SUPERSEDED (2026-04-27 — Path 2 transitional approach abandoned; panel mode now Phase 7 of MARSYS_JIS_PROJECT_PLAN_v1_0.md against the holistic architecture, not the current Consume architecture; retained in place for historical audit)
authored_by: Cowork (Claude Opus 4.7)
authored_on: 2026-04-27
authoring_session: Cowork conversation — "Multi-LLM panel synthesis brainstorm with native, brief authoring round"
executor: Claude Code Extension (VS Code / anti-gravity setup per Abhisek's environment — NOT the CLI)
trigger_phrase: "Read PANEL_IMPLEMENTATION_BRIEF_v1_0.md and execute it."
parent_design: 00_ARCHITECTURE/PANEL_SYNTHESIS_ADDENDUM_v0_1.md (v0.2 current — the architectural spec; this brief is the executor counterpart)
grandparent_design: 00_ARCHITECTURE/CONSUME_DESIGN_v0_1.md (DRAFT_PROPOSAL — context only; this brief does NOT depend on its adoption per Path 2 transitional decision)
chosen_path: Path 2 transitional — panel mode implemented against the CURRENT Consume architecture (tool-based JIT retrieval, no pre-assembled Stage-5 bundle, no layered retriever). Migration debt to target architecture is documented and deferred until B.6 lands and parent design is live.
parallel_stream_warning: |
  M2/B.5 work is in flight via the active CLAUDECODE_BRIEF.md at project root.
  This brief is a SEPARATE, parallel workstream and MUST NOT touch the M2/B.5 surface area.
  See §3 "Hard constraints" below for the must-not-touch glob list.
governance_status: This brief executes panel mode IMPLEMENTATION. The DESIGN it implements
  (PANEL_SYNTHESIS_ADDENDUM_v0_1.md v0.2) remains DRAFT_PROPOSAL pending native ratification —
  but native has authorized implementation against current Consume architecture (Path 2)
  ahead of formal addendum adoption. Post-implementation, native will ratify the design
  retroactively or amend based on what was learned during build.
---

# PANEL IMPLEMENTATION BRIEF v1.0 — Multi-LLM Panel Synthesis (Transitional)

## §0 — Trigger and execution model

Native triggers this brief by saying to a Claude Code session: **"Read PANEL_IMPLEMENTATION_BRIEF_v1_0.md and execute it."**

On trigger, Claude Code MUST:
1. Read this entire brief end-to-end before any other action.
2. Read the mandatory pre-flight artifacts in §2 in the order specified.
3. Read the relevant codebase files in §2 to understand the current Consume implementation.
4. Execute Phase A (plan authoring) and HALT for native approval before proceeding to Phase B.
5. After native approves the plan, proceed through Phases B → C → D → E in sequence, halting between phases for native check-in if anything ambiguous arises.
6. On completion of Phase E, set this brief's `status` field to `COMPLETE` and notify native.

The brief is the sole entry point. Do NOT proceed if the trigger phrase is ambiguous or if the workspace state appears to conflict with §3 hard constraints — instead, halt and ask native for clarification.

## §1 — Mission

Implement multi-LLM panel synthesis as an opt-in feature of the Consume tab, per the architectural design in `00_ARCHITECTURE/PANEL_SYNTHESIS_ADDENDUM_v0_1.md` (v0.2 current). The mission is **transitional implementation** (Path 2 per native decision 2026-04-27): panel mode is built against the CURRENT Consume architecture as it exists today, accepting that some addendum-specified mechanisms (the pre-assembled Stage-5 retrieval bundle, the layered tool decomposition, the capability manifest) do not yet exist and will not exist until the parent design `CONSUME_DESIGN_v0_1.md` is adopted and B.6 (Hybrid Retrieval) ships.

The transitional implementation is fully functional and shippable. The migration work to bring panel mode into compliance with the target architecture (when B.6 lands) is bounded and tracked in the migration-debt register that this brief produces as part of Phase E.

The mission's success criteria, in plain language:

A user opens the Consume tab, picks a model, ticks a new "Run as super query" checkbox in the composer, sends a query. The system fans the query out to three independent frontier-lab models (panel members), collects their responses, has the user's selected model (the adjudicator) synthesize a final answer from the three, and streams the synthesis to the user. The conversation displays one answer (the synthesis). An "Inspect" affordance on the message reveals the full panel — three raw responses, each with its own tool-call transcript, the adjudicator's reasoning, and a structured list of `DIS.class.*` divergences classified by a small same-family classifier model. Single-model behavior is unchanged when the checkbox is unticked. Panel mode is opt-in per query and the checkbox auto-resets after each send.

Plus the operational integrity requirements: hard-halt at 3-of-3 panel by default with concurrent retry (N=3 per panel member); opt-in 2-of-3 degrade mode in user settings; rich `panel_metadata` JSON persisted alongside each panel-mode message; audit view universally available across all users.

## §2 — Mandatory pre-flight reading

In this exact order. Do not skip any item. Note your understanding of each before proceeding to the next.

**§2.1 — Architectural context (read first):**
1. `CLAUDE.md` (project root) — project orientation, principles, current execution position.
2. `00_ARCHITECTURE/PANEL_SYNTHESIS_ADDENDUM_v0_1.md` — THE design document. v0.2 content is current; §17 changelog summarizes the v0.1 → v0.2 evolution with the six critique-driven fixes that are non-negotiable. Pay particular attention to §3 (panel composition rules), §5 (the seven-step algorithm including super-bundle and classifier split), §6 (DIS.class.* taxonomy), §7 (panel_metadata schema), §10 (failure handling), §11 (UX), §17 (changelog).
3. `00_ARCHITECTURE/CONSUME_DESIGN_v0_1.md` — context only. This is the parent design and is NOT yet adopted. Read it to understand where panel mode is intended to live (Stage 7 of the 8-stage pipeline) but DO NOT implement parent-design machinery. Path 2 transitional explicitly works within today's Consume architecture, not the target architecture.

**§2.2 — Current Consume implementation (read to understand what you're modifying):**
4. `platform/src/app/api/chat/consume/route.ts` — the existing single-model server route that you will extend with a panel-mode branch.
5. `platform/src/lib/claude/consume-tools.ts` — the current 8-tool surface that panel members will call (extend bundle via tool calls; this IS the transitional retrieval mechanism).
6. `platform/src/lib/claude/system-prompts.ts` — the existing system-prompt assembly with the L2.5 routing mandate.
7. `platform/src/lib/models/registry.ts` and `platform/src/lib/models/resolver.ts` — the model abstraction. You will add OpenAI/GPT here in Phase B.
8. `platform/src/components/consume/ConsumeChat.tsx` and the Composer subcomponent — where the panel checkbox lands.
9. `platform/src/components/consume/ModelStylePicker.tsx` — the existing model and style selectors (no changes needed here; panel mode does not touch model selection itself).
10. `platform/src/hooks/useChatSession.ts` and `platform/src/hooks/useChatPreferences.ts` — request lifecycle and per-chart persistence.

**§2.3 — Database schema:**
11. The current `messages` table schema in Supabase (find via existing migration files or schema declarations under `platform/`). You will add a `panel_metadata` JSONB column.
12. The existing user-settings storage mechanism (likely a `user_preferences` table or similar — find it, do not invent). You will add two boolean fields for the new toggles.

**§2.4 — Optional but recommended:**
13. The memory pointer file (read by Cowork sessions, not by Claude Code, but useful context): `MEMORY.md` index entry for "Panel Synthesis Addendum" describes locked decisions and parallel-stream context.

After completing pre-flight reading, summarize your understanding back to native in 4-6 sentences before proceeding to Phase A. This confirms the design landed correctly and gives native a chance to course-correct if anything is misread.

## §3 — Hard constraints (must NOT touch)

The M2/B.5 governance and execution stream is in flight via the active `CLAUDECODE_BRIEF.md` at project root. This brief MUST NOT collide with that work. The following surfaces are off-limits — read-only at most, never modified:

**Governance and architecture (read-only):**
- `00_ARCHITECTURE/` — entire directory. Read for context only. The parallel stream may add or modify files here at any time. Do not write anything in this directory.
- The active `CLAUDECODE_BRIEF.md` at project root — under no circumstances modify, rename, or delete it. It belongs to the M2/B.5 stream.

**Data layers (read-only):**
- `01_FACTS_LAYER/` — L1 facts; immutable canonical data.
- `02_*` (any directory starting with 02) — L2 analysis layer.
- `025_HOLISTIC_SYNTHESIS/` — L2.5 holistic layer (CGM, MSR, UCN, CDLM, RM).
- `03_DOMAIN_REPORTS/` — L3 reports.
- `04_DISCOVERY_LAYER/` (or wherever L3.5 discovery work is being authored by B.5) — read-only.
- `05_REMEDIAL_CODEX/` — L4 remedial.
- `06_LEARNING_LAYER/` — L6 learning. Includes the prediction ledger and pattern register (B.5 active surface). DO NOT write here. The interim prediction-ledger home for panel mode v1.0 transitional is documented in §6 below.

**Parallel-stream code surfaces (do not modify):**
- `platform/python-sidecar/` — the Python sidecar serving ephemeris and transit calculations. Used by parallel stream.
- Anything under `platform/` related to: RAG corpus chunking and embedding, RAG graph node and edge population, two-pass discovery, pattern register authoring, signal-id resolution machinery, retrieval client (`platform/src/lib/rag/` if it exists). These are all M2/B.5 surfaces.
- The `rag_chunks`, `rag_embeddings`, `rag_graph_nodes`, `rag_graph_edges` Cloud SQL tables — read-only at most.

**Behavioral constraints:**
- Single-model Consume behavior MUST NOT regress. A user who never ticks the panel checkbox should observe identical behavior to today, including streaming latency, tool-call patterns, and conversation history rendering. Any change that affects the single-model path requires explicit native approval before merge.
- Existing model registry entries (Claude variants, Gemini variants, DeepSeek variants) MUST NOT be modified. You may ADD entries (OpenAI/GPT in Phase B) but do not change existing ones.
- The mandatory L2.5 routing instruction in `system-prompts.ts` MUST NOT be removed or weakened, even when panel mode is active. Each panel member should still receive the L2.5 mandate in its system prompt.

**If you encounter a situation where panel implementation seems to require touching one of the above, halt and ask native.** Do not proceed under any interpretation that loosens these constraints.

## §4 — Phase A: Author the elaborate implementation plan (HALT after)

Produce a single deliverable file: `PANEL_IMPLEMENTATION_PLAN_v1_0.md` placed at project root. This file is the elaborate plan that native will review and approve before implementation begins.

**Required sections in the plan:**

**§A.1 — Architecture deltas (current vs. transitional vs. target).** A side-by-side table or three-column comparison showing: how the current Consume implementation behaves; how the transitional v1.0 panel mode will behave (Path 2); how the target architecture (parent design + B.6 layered retriever, when eventually live) will behave. The reader should understand exactly what is being built now and what migration debt is being incurred.

**§A.2 — File-by-file change inventory.** Every file that will be created, modified, or deleted. For each: full path, change type (create | modify | migration), summary of the change, line-count estimate, and dependencies on other files in the inventory.

**§A.3 — Database schema migration plan.** The exact migration to add `panel_metadata` JSONB column to the `messages` table. Includes: forward migration SQL, rollback migration SQL, default value handling for existing rows (NULL is correct — single-model messages have no panel_metadata), index strategy if any (probably none — panel_metadata is rarely queried, mostly displayed alongside its message). Plus the migration for adding the two user-settings boolean fields (`allow_2of3_degrade`, `panel_research_mode`) to the user-preferences storage.

**§A.4 — Panel orchestrator design.** Pseudocode or detailed prose for the server-side orchestrator that fans out to 3 panel members, collects responses, runs the adjudicator, runs the classifier, persists `panel_metadata`. Must specify: parallelism strategy (Promise.all? p-limit?); concurrent retry implementation (per addendum §10); request-scoped tool cache (per addendum §13 — for Path 2, this is a per-panel-turn in-memory cache keyed on (tool_name, hash(normalized_params)) at the orchestrator level, since tools are called via the Vercel `ai` SDK's tool-execution mechanism); how the transitional super-bundle is composed from per-panel-member tool-call results.

**§A.5 — Adjudicator and classifier prompt templates.** Full prompt text for both. Adjudicator prompt must include: the user query, the transitional super-bundle (union of per-panel-member tool-call results, deduplicated), the three anonymized panel responses with retrieval transcripts, the synthesis rubric (B.1, B.3, B.10, B.11), the style suffix. Classifier prompt must include: the three anonymized panel responses, the adjudicator's synthesis output, the super-bundle, the DIS.class.* taxonomy with instruction to extract and classify every detected divergence into a structured JSON list. Both prompts must explicitly instruct the model NOT to mention being part of an ensemble (anonymization integrity).

**§A.6 — Failure handling matrix.** A table mapping every failure mode to its handling: panel-member API timeout (concurrent retry), rate limit (concurrent retry with backoff), content policy violation (no retry — record failure mode), validator failure on a panel response (record + retry that member), classifier failure (record + degrade to "unclassified divergences" but don't fail the synthesis), adjudicator failure (concurrent retry, then hard halt with explicit error). Hard-halt cases produce specific error messages per addendum §10.

**§A.7 — UI implementation plan.** Where the panel checkbox lives in `Composer`, how the auto-reset works (probably: form state resets the checkbox after `sendMessage` resolves), the audit view component design (universal across all assistant messages — for single-model messages, audit view shows tool-call transcript, validator votes, model identity; for panel messages, audit view shows all panel data per addendum §11), the user-settings UI for the two new toggles.

**§A.8 — Test strategy.** Unit tests (panel resolver, super-bundle composition, divergence parsing); integration tests (end-to-end panel turn with mocked panel members + mocked adjudicator + mocked classifier); manual test plan (real panel turn with real LLMs; budget for ~10 manual test queries during development at native's expense via the production API keys); regression tests confirming single-model behavior unchanged.

**§A.9 — Feature flag plan.** A server-side feature flag (`PANEL_MODE_ENABLED`, env var or config) gates the entire panel-mode code path. When the flag is off, the panel checkbox is not rendered and the panel_mode request flag is rejected at the route handler. This allows the implementation to ship dark first and be enabled progressively. Default for development: ON. Default for first production deploy: OFF until native explicitly enables.

**§A.10 — Latency and cost analysis.** Measured baseline of current single-model latency for a representative query. Estimated panel-mode latency: max(panel_member_latencies with 3 retries within 60s budget) + adjudicator_latency + classifier_latency. Estimated cost per panel turn: sum of (3 × panel-member tokens × per-model price) + (adjudicator tokens × adjudicator price) + (classifier tokens × classifier price). Provide low/median/high estimates based on token-count assumptions.

**§A.11 — Rollout strategy.** Three stages: (1) dark deploy behind feature flag, internal testing only; (2) opt-in beta — flag enabled, panel checkbox available to all users, monitoring for failure rates and cost; (3) general availability — same as beta but graduated. Each stage has explicit go/no-go criteria.

**§A.12 — Migration debt register.** The explicit list of items that will need to be re-implemented or migrated when the target architecture (parent design + B.6 layered retriever) becomes live. Each item: what's transitional today, what the target is, the migration cost estimate, and whether it can be migrated incrementally or requires a single cutover. This register is the single most important deliverable for Phase A — it is what makes Path 2 acceptable, because the debt is explicit and bounded.

**§A.13 — Open questions for native.** Anything the implementation needs decided that this brief doesn't already lock. Surface them here for native to answer before Phase B begins.

After writing the plan file, **HALT and notify native**. Do NOT proceed to Phase B until native has reviewed and explicitly approved the plan (with any amendments native requests).

## §5 — Phase B: v0.5 OpenAI registry integration

Smallest possible change. Independent of the rest of panel mode — even useful by itself (lets native pick GPT as a single-model option).

**Tasks:**
1. Install `@ai-sdk/openai` package via npm. Verify version compatibility with the existing Vercel `ai` SDK version in use.
2. Add the OpenAI flagship model entry to `platform/src/lib/models/registry.ts`. Use `gpt-5` (or whatever the current OpenAI flagship at implementation time is — verify against OpenAI's current model list; do not invent model IDs). Capability flags: `tool-use: true`, `prompt-caching: false` (OpenAI's prompt caching is automatic and doesn't need explicit cache-control headers; verify this assumption against the `@ai-sdk/openai` documentation), reasonable `maxOutputTokens` per the model's specs.
3. Add the resolver case in `platform/src/lib/models/resolver.ts` for the `openai` provider.
4. Document the new env var requirement: `OPENAI_API_KEY` must be set. Update any env-var documentation files (`.env.example` if present, README env section if present).
5. Verify the integration end-to-end: native picks GPT-5 in the model picker (will need to be added to ModelStylePicker dropdown — modify the picker to include the new entry), sends a query, gets a streaming response. Single-turn and multi-turn both verified.

**Acceptance criteria for Phase B:**
- ☐ `@ai-sdk/openai` installed.
- ☐ GPT-5 (or current flagship) appears in registry with correct capability flags.
- ☐ Resolver handles `openai` provider without errors.
- ☐ ModelStylePicker shows the new model option.
- ☐ End-to-end query with GPT-5 selected works (streaming, tool-use, no errors).
- ☐ Existing model selections (Claude, Gemini, DeepSeek) remain functional and unchanged.
- ☐ `OPENAI_API_KEY` documented as required env var.

## §6 — Phase C: v1.0 transitional panel orchestration

The substantive piece. Implement the panel orchestrator on the server side per addendum §5 algorithm, adapted for current Consume architecture.

**Key design points specific to Path 2 transitional:**

**Transitional super-bundle.** The addendum's Step 5.6 specifies a "merged super-bundle" = baseline bundle ∪ deduplicated panel-member extensions. In Path 2 there is NO baseline bundle (no Stage-5 layered retriever exists yet). The transitional super-bundle is constructed as the **deduplicated union of all unique tool-call results from all panel members during their generation**. Each panel member generates its response by calling tools (via Vercel `ai` SDK's tool-use loop); their tool-call results are captured and merged into the super-bundle handed to the adjudicator. This is the Path 2 substitute for the parent design's Stage-5 bundle.

**Tool-cache scope.** The request-scoped tool cache (addendum §13 / §17 Fix 5) prevents 3× duplicate tool execution. Implementation: a per-panel-turn `Map<string, Promise<ToolResult>>` keyed on `(tool_name + JSON-stable-stringify(normalized_params))`. First panel member to call a tool with a given key creates the promise; subsequent members await the same promise. Cache cleared at panel-turn boundary. The audit trail's per-call `served_from_cache` flag is true for the second and third members' calls when they hit the cache.

**Concurrent retry.** Implement per addendum §10. When a panel-member API call fails, fire a retry concurrently while other panel members continue. Bounded by N=3 retries per member and a 60-second total time budget per panel turn (configurable). Use AbortController for the time budget. Use the Vercel `ai` SDK's error handling to detect failures.

**Adjudicator/classifier split.** Two separate `streamText` (or `generateText` for the classifier — non-streaming is fine for classification since it's not user-facing) calls per panel turn. Adjudicator prompt per Phase A §A.5; classifier prompt per Phase A §A.5. The adjudicator's response is what streams to the user. The classifier's response is parsed as JSON and merged into `panel_metadata.divergence_classification`.

**Family-level adjudicator exclusion.** When `panel_mode: true`, look up the user's selected model's provider family (`anthropic` | `openai` | `google` | `deepseek`). Build the panel slate by excluding the adjudicator's family and picking the configured "panel-best" version from each remaining family. Configuration source: a TypeScript constant or config file at `platform/src/lib/panel/slate.ts` (or similar — Phase A plan should propose the location). Initial slate: `claude-opus-4-7`, `gpt-5`, `gemini-3-pro-preview`, `deepseek-v3`. Native can override per-family via config edit.

**System prompt for panel members.** Identical to the current Consume single-model system prompt (with the L2.5 routing mandate), plus the user's selected style suffix. Panel members MUST NOT be informed they are part of an ensemble — the system prompt does not mention adjudication, panels, or other LLMs. Naive panel.

**Persistence.** Extend `replaceConversationMessages` (or the equivalent function in `consume/route.ts`'s `onFinish` callback) to write `panel_metadata` for panel-mode turns. The schema follows addendum §7 exactly.

**Prediction ledger interim.** Per addendum §9, predictive-class queries write all four panel responses (3 panel + adjudicator synthesis) as separate prediction-ledger entries before streaming begins. Per parent design §9 question 4, the canonical prediction-ledger home is `06_LEARNING_LAYER/PREDICTION_LEDGER/` once Step 11 / B.5 scaffolds it. **The interim home for v1.0 transitional is a new database table** `prediction_ledger_interim` (rather than touching `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` which is in the must-not-touch list). Schema: `(id, conversation_id, message_id, panel_turn_id, source_type ['panel_member' | 'adjudicator'], source_model_id, claim, horizon, falsifier, confidence, validated_bundle_hash, written_at)`. Migration plan in Phase A §A.3 includes this table.

**Predictive-vs-not classification.** For now, every panel-mode query is treated as predictive iff the user's query contains time-indexed language ("when", "by", "next year", date ranges, etc.) — implement as a small regex/keyword classifier in the orchestrator. This is intentionally crude; the proper classifier comes with parent design's Stage-2 router. Document this as migration debt.

**Acceptance criteria for Phase C:**
- ☐ `panel_metadata` JSONB column added to `messages` table; migration tested forward and rollback.
- ☐ `prediction_ledger_interim` table created; migration tested.
- ☐ Server-side panel orchestrator implemented behind feature flag `PANEL_MODE_ENABLED`.
- ☐ Family-level adjudicator exclusion works correctly for all four adjudicator-family choices.
- ☐ Concurrent retry with N=3 verified by injecting deliberate failures in test.
- ☐ Request-scoped tool cache verified by counting actual tool executions when 3 panel members call the same tool.
- ☐ Adjudicator and classifier separate calls; classifier output parses cleanly into `divergence_classification` JSON.
- ☐ `panel_metadata` persisted correctly per addendum §7 schema for a real panel turn.
- ☐ Prediction-ledger interim writes happen BEFORE streaming for predictive queries; verified by checking row count vs. stream timing.
- ☐ Hard-halt path produces explicit user-facing error matching addendum §10 wording.
- ☐ Unit and integration tests in Phase A §A.8 plan all pass.
- ☐ Single-model regression test suite passes — no behavior change for non-panel queries.

## §7 — Phase D: v1.1 UI wiring

**Tasks:**

**Composer panel checkbox.** Add a checkbox labeled "Run as super query" to the Composer component, positioned adjacent to the model selector. State management: per-form-instance state (NOT persisted to localStorage). Auto-reset to unchecked after `sendMessage` resolves successfully. Tooltip on hover: "Fan this query out to a panel of frontier models and synthesize the best answer. Costs ~4× a normal query and takes ~10-30 seconds." Hidden when feature flag is off.

**Audit view component.** A new collapsible/expandable component on every assistant message. For single-model messages: shows tool-call transcript, model identity, token counts, latency, validator votes (whatever validators run today). For panel-mode messages: shows everything from `panel_metadata` per addendum §11 — panel composition (with anonymization key revealed for super_admin), per-panel-member sub-panels with their tool-call transcripts and validator votes, adjudicator synthesis reasoning, divergence list with `DIS.class.*` classifications, total cost and latency.

**Disclosure-tier filter for audit view content.** The audit view EXISTENCE is universal (all users see the "Inspect" affordance). The audit view CONTENT respects the user's audience tier per addendum §11 final paragraph and parent design §6. Today only the `super_admin` tier exists, so practically everyone with access sees raw content. When future tiers come online (M6 client tier, M10 public tier), the audit view's renderer must apply tier-appropriate redaction. For now: implement the rendering logic with a tier check that always returns "raw" for super_admin, and a TODO-with-issue-link for the future tier filters.

**User settings: two new toggles.** Add to wherever user preferences live (likely a settings page or user-profile page). Two boolean toggles:
- "Allow 2-of-3 degrade if a panel member fails" (default: false). Tooltip: "When enabled, panel queries proceed with 2 responses if 1 panel member fails after retries. Audit-trail-marked; excluded from research calibration data by default."
- "Research mode (no history in panel turns)" (default: false). Tooltip: "When enabled, panel members see only the current query, not prior conversation history. Preserves naive-panel independence at the cost of multi-turn references."

Wire both settings to the orchestrator from Phase C: the orchestrator reads them at panel-turn start and modifies behavior accordingly.

**Latency UX.** Three-state progress indicator in the conversation panel during a panel-mode turn: "Running panel..." → "Adjudicator synthesizing..." → streaming. No per-panel-member progress disclosure (would leak panel composition before audit view is opened).

**Acceptance criteria for Phase D:**
- ☐ Composer checkbox renders behind feature flag, auto-resets after send.
- ☐ Audit view component renders correctly for single-model messages (existing data only).
- ☐ Audit view component renders correctly for panel-mode messages (full `panel_metadata`).
- ☐ Tier-conditional content rendering scaffolded (super_admin = raw; future tiers TODO).
- ☐ Two new user-settings toggles render and persist; orchestrator reads them at panel-turn start.
- ☐ Latency progress indicator transitions through three states correctly.
- ☐ Composer checkbox state visually clear; tooltip readable.
- ☐ Manual end-to-end test: native ticks the box, sends a query, sees the synthesis stream, opens the audit view, sees the four-perspective breakdown with divergence classifications.

## §8 — Phase E: Migration debt register

A standalone deliverable file: `PANEL_MIGRATION_DEBT_v1_0.md` placed at project root.

This file enumerates every transitional decision made during Phases B-D that diverges from the addendum's target architecture, with explicit migration paths to be followed when B.6 lands and the parent design is live.

**Required content (per item):**

**Item 1 — Super-bundle composition.** Today: union of per-panel-member tool-call results, computed at orchestrator level. Target: pre-assembled Stage-5 bundle from the layered retriever. Migration: replace orchestrator's bundle composition with a call to the layered retriever's `retrieve(QueryPlan) → RetrievalBundle`; panel members no longer compute their own retrieval (they receive the pre-assembled bundle as context); each panel member's tool calls during synthesis become "extensions" not "primary retrieval." Estimated effort: medium; probably one focused session.

**Item 2 — Predictive query classification.** Today: regex/keyword classifier for time-indexed language. Target: parent design's Synthesis Router (B.7) classifies query class as part of Stage 2. Migration: remove the regex; route query-class detection through the router's classifier. Estimated effort: small.

**Item 3 — Prediction ledger location.** Today: `prediction_ledger_interim` Cloud SQL table. Target: `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl` per Step 11 / B.5 scaffold. Migration: bulk migration script that ports interim entries to the canonical home, dual-write window during transition, then cutover. Estimated effort: medium.

**Item 4 — Capability manifest entry.** Today: panel slate is a hardcoded TypeScript config. Target: `PANEL_SYNTHESIS` family in the capability manifest per addendum §12. Migration: when manifest is created (parent design v1.0), register `PANEL_SYNTHESIS` per the addendum §12 schema; remove hardcoded config. Estimated effort: small.

**Item 5 — Validator wiring.** Today: only validators that exist in current Consume run on panel responses (P1, P2, P5 per parent §7). Target: full P-validator stack including P3 whole-chart-read enforcement, P4 no-fabrication on synthesis output, P7 three-interpretation gate, P8 falsifier gate, P9 audit-trail completeness. Migration: as each validator lands per its parent-design phase, extend the orchestrator's per-panel-member validation step to call it. P7 in particular requires the consolidation rule from addendum §8 — implement it at B.5 Task 0 close.

**Item 6 — Falsifier extraction.** Today: predictions are written to interim ledger but falsifier extraction is rudimentary. Target: P8 enforces falsifier presence on every time-indexed claim. Migration: at B.5 Task 0, the orchestrator runs P8 on each panel response and on the synthesis; failures fail the panel turn. Estimated effort: small once P8 exists.

**Item 7 — Disclosure-tier filter for client and public_redacted tiers.** Today: only super_admin tier exists. Target: full four-tier filter per parent §6. Migration: as M6 client tier lands and M10 public tier lands, extend the audit view renderer's tier check to apply appropriate redaction. Estimated effort: medium per tier.

**Item 8 — Three-interpretation consolidation.** Today: not enforced (P7 doesn't exist yet). Target: addendum §8's revised consolidation rule (orthogonality + grounding) governs how 9 panel-member interpretations are consolidated to 3 user-visible. Migration: when P7 lands at B.5 Task 0, implement the consolidation rule in the adjudicator's synthesis prompt and post-process the synthesis output to surface ungrounded candidates per the schema's `interpretations_consolidated.ungrounded_excluded` field.

**Acceptance criteria for Phase E:**
- ☐ `PANEL_MIGRATION_DEBT_v1_0.md` file created at project root.
- ☐ All 8 migration items present with: today/target/migration/effort.
- ☐ Cross-references back to specific phase deliverables (which file/function embodies each transitional choice).
- ☐ The register is the canonical reference — when B.6 lands, the implementation team can work this register top-to-bottom.

## §9 — Brief completion

After Phase E acceptance criteria are checked:
1. Set this brief's `status` field in the frontmatter to `COMPLETE` and the `completed_on` field to today's date.
2. Run all tests one final time end-to-end. All must pass.
3. Verify all hard-constraint surfaces in §3 remain unmodified — run a quick `git status` or equivalent and confirm no unintended changes.
4. Notify native that the brief is complete, the implementation is done, and panel mode is ready for the rollout sequence (currently dark behind feature flag — native enables when ready).
5. Write a short close-out summary as a comment or appended section to this brief, listing: what shipped, what didn't ship and why, any runtime issues encountered, the final cost and latency measurements from real panel turns.

## §10 — Operational guidance

**Style.** This is production code in Abhisek's astrology research instrument. Code quality matters. Follow existing project conventions for TypeScript style, file organization, naming. When in doubt about a convention, look at how existing Consume code does it and match.

**Commits.** One commit per logical unit (one phase task = one commit, ideally). Clear commit messages referencing this brief and the addendum.

**Testing.** The test strategy in Phase A §A.8 is the definitive plan. Implement tests as you build, not at the end. Panel mode introduces real complexity (parallelism, retries, anonymization, schema migration) and tests are how you keep yourself honest.

**Cost during development.** Manual testing of panel mode burns API credits at 4× single-model rates. Be deliberate about test queries — use mocked panel members for most integration tests; reserve real-API testing for end-to-end verification. Native's API budget is real money; minimize wasted spend.

**When in doubt, halt and ask.** This brief is detailed but cannot anticipate every edge case. If you encounter a decision that the brief doesn't cover and the addendum doesn't cover, halt and ask native rather than guessing. Ambiguity-resolution by guessing is exactly what produces the kind of architectural drift this project's governance discipline exists to prevent.

---

*End of PANEL_IMPLEMENTATION_BRIEF_v1_0.md (status: AUTHORED, 2026-04-27). Trigger: native says "Read PANEL_IMPLEMENTATION_BRIEF_v1_0.md and execute it." On completion, status flips to COMPLETE.*
