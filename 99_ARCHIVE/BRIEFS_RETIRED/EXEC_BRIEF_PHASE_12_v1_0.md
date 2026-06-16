---
brief_id: EXEC_BRIEF_PHASE_12
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_12_v1_0.md and execute it."
phase: 12
phase_name: Pipeline Data-Layer Repair (FUB-1 + FUB-2 + FUB-3 + FUB-4 combined)
risk_classification: MEDIUM
parallelizable_with: []
depends_on: [EXEC_BRIEF_PHASE_11A_DEBUG_v1_0.md (COMPLETE — Fix A + Fix B applied)]
output_artifact: code changes verified by live LLM smoke
---

# EXEC_BRIEF — Phase 12 — Pipeline Data-Layer Repair

## Mission

The Phase 11A debug surfaced three architectural gaps that, together, explain why the new pipeline fabricates chart data. Fix A (router authorizes `vector_search`) was applied surgically. The remaining repairs are bigger and need their own scoped brief. This is that brief.

**The fundamental claim being repaired:** when the LLM synthesizes an answer, it must have actual chart data — birth particulars, planetary positions, MSR signal claims — present in its context window. Currently it has none of these. Phase 12 fixes that across four streams.

This is also a learning moment for the Cowork-authored architecture: the original Phase 2 + Phase 3 briefs assumed but did not specify "the bundle carries content" and "the chart context is plumbed to synthesis." The mocked LLM tests passed without validating prompt content. Phase 12 closes that gap and adds a verification step that exercises the real LLM against canonical chart data.

## Pre-flight gate

Before any stream runs:

1. Verify `EXEC_BRIEF_PHASE_11A_DEBUG_v1_0.md` is COMPLETE (frontmatter `status: COMPLETE`).
2. Verify Fix A is in `platform/src/lib/router/prompt.ts`:
   ```bash
   grep -A1 "vector_search" platform/src/lib/router/prompt.ts | head -5
   ```
3. Verify Fix B is in `platform/src/app/clients/[id]/consume/page.tsx`:
   ```bash
   grep "panelModeEnabled" platform/src/app/clients/\[id\]/consume/page.tsx
   ```
4. **Cloud SQL Auth Proxy MUST be running.** Stream E (verification) needs DB access for `vector_search` to retrieve actual chunks. If `pgrep -fl cloud_sql_proxy` returns empty, **HALT** with a clear message asking the native to start the proxy.

If any of the above fails, print the failure and stop. Do not run any subsequent stream.

## Scope

**`may_touch`:**
- `platform/src/lib/synthesis/types.ts` (add `chart_context` field to `SynthesisRequest`)
- `platform/src/lib/synthesis/single_model_strategy.ts` (use real chart values; inject tool_results)
- `platform/src/lib/synthesis/panel_strategy.ts` (mirror single-model changes for parity)
- `platform/src/app/api/chat/consume/route.ts` (pass chart record through to synthesis)
- `platform/src/lib/bundle/rule_composer.ts` (load floor-asset content)
- `platform/src/lib/bundle/types.ts` (extend Bundle entry to carry content)
- `platform/src/lib/router/prompt.ts` (add `vector_search` to interpretive/holistic/cross_domain few-shots)
- `platform/src/lib/synthesis/__tests__/**`, `platform/src/lib/bundle/__tests__/**`, `platform/src/lib/router/__tests__/**` (update tests for new behavior)
- `platform/scripts/cutover/stage1_phase12_smoke.ts` (new — Stream E verification script)
- `platform/package.json` scripts: add `cutover:phase12-smoke`

**`must_not_touch`:**
- Any feature flag default (keep `NEW_QUERY_PIPELINE_ENABLED=true`, `AUDIT_ENABLED=true`, all other flags at their current defaults)
- `platform/python-sidecar/**` (sidecar untouched; B.5/B.8 path independent)
- `platform/src/lib/audit/**`, `platform/src/lib/prediction/**` (Phase 4 territory; this brief emits via existing audit hook only)
- `platform/src/lib/checkpoints/**` (Phase 6 territory; checkpoints continue to work as-is post-fix)
- Any DB migration (no schema changes; Phase 12 is code-level data plumbing)
- Any flag-OFF code path (legacy is opt-out via env var; do not modify it)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (governance only)
- The legacy single-model behavior contract (existing single_model tests must still pass; Phase 12 ADDS data, doesn't change orchestration shape)

## Sub-streams (5 total — 4 fixes + verification)

### Stream A — FUB-1: Plumb chart context to synthesis

1. In `platform/src/lib/synthesis/types.ts`, add to `SynthesisRequest`:
   ```typescript
   chart_context?: {
     name: string;
     birth_date: string;       // ISO YYYY-MM-DD
     birth_time: string;       // HH:MM (24h)
     birth_place: string;      // human-readable; e.g., "Bhubaneswar, Odisha, India"
   };
   ```
   Field is optional to preserve backward compat with any callers that don't provide it (those paths fall back to current placeholder strings).

2. In `platform/src/lib/synthesis/single_model_strategy.ts:92-98`, replace hardcoded values:
   ```typescript
   // BEFORE
   chart_name: 'the native',
   birth_date: 'canonical birth data in context bundle',
   birth_time: '',
   birth_place: '',
   
   // AFTER
   chart_name: request.chart_context?.name ?? 'the native',
   birth_date: request.chart_context?.birth_date ?? '<birth date unavailable>',
   birth_time: request.chart_context?.birth_time ?? '<birth time unavailable>',
   birth_place: request.chart_context?.birth_place ?? '<birth place unavailable>',
   ```

3. Mirror the same change in `panel_strategy.ts` for the panel members' system prompt (same hardcoded placeholders likely exist there).

4. In `platform/src/app/api/chat/consume/route.ts`, find where `synthesize()` is called (around line 171). The `chart` record was fetched at lines 79-91. Construct `chart_context` from it and pass it through:
   ```typescript
   const synthesisRequest: SynthesisRequest = {
     // ...existing fields...
     chart_context: {
       name: chart.name ?? 'the native',
       birth_date: chart.birth_date,    // adjust column name to match the actual schema
       birth_time: chart.birth_time,
       birth_place: chart.birth_place,
     },
   };
   ```
   Verify the actual column names by reading the chart row schema (likely `birth_date_iso`, `birth_time_iso`, `birth_place` or similar — check `lib/db/charts.ts` or wherever the chart fetch query lives).

5. Update existing synthesis tests that construct `SynthesisRequest` to either provide `chart_context` (preferred) or omit it (verify fallback). Add 2-3 new tests:
   - Real `chart_context` produces a system prompt containing the actual values
   - Missing `chart_context` produces fallback placeholders ("birth date unavailable") rather than crashing
   - Panel strategy parity: same behavior

**Stream A acceptance:** types.ts compiles; both strategy files use real values when provided; route.ts passes the chart context through; tests pass; one rendered system prompt contains "1984-02-05" or whatever the canonical birth date is.

### Stream B — FUB-2: Bundle content loading for floor-role assets

This is the bigger piece. The bundle composer currently emits manifest references only. We need it to actually load content for `floor`-role assets so the LLM has them in context.

**Design decision before implementation:** there are two reasonable approaches. Pick one and document the choice in a header comment.

- **Approach A (eager load at compose time):** `rule_composer.ts` reads file content (or fetches from GCS / DB chunks) for every floor-role entry in the bundle. `Bundle` carries the content. Synthesis prompt reads it directly.
- **Approach B (lazy load via vector_search):** Bundle stays as references. Floor assets are pre-emptively retrieved by `vector_search` at synthesis time using the query as the search target. The LLM gets a "context block" injected before the user message containing top-K most-relevant chunks.

**Recommended: Approach B.** Reasons: (1) Phase 9 already built `vector_search` for exactly this purpose; (2) FORENSIC content can be tens of KB — loading the whole thing for every query inflates the prompt and cost; (3) semantic relevance ranking is better than blind eager-load; (4) less invasive change. Use Approach B unless you find a strong reason against it during implementation.

If Approach B:

1. In `single_model_strategy.ts` (and `panel_strategy.ts` for parity), before constructing the LLM messages: for each `floor`-role entry in `bundle.mandatory_context`, call `vector_search` with `q = request.query_text` and `top_k = 5`, scoped to the asset's chunks (filter by `asset_id` if the chunks index supports it; otherwise broad search and rely on relevance ranking).
2. Concatenate the top chunks (with citation markers `[chunk:rag_chunk_id]`) into a `CHART_CONTEXT_BLOCK` string.
3. Inject `CHART_CONTEXT_BLOCK` as a system message segment between the existing system prompt and the user query.
4. **Cap total injected content at ~6000 tokens** to leave headroom. If the chunks exceed the cap, truncate the lowest-relevance ones first.
5. Update `rule_composer.ts` to mark each floor entry with `requires_content_load: true` so the synthesis layer knows which entries need the lazy-load step.

If Approach A (only if Approach B has a blocker):

1. Add a `content_loader` map in `rule_composer.ts` keyed by canonical_id. For FORENSIC, load file content from `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`. For MSR, query `msr_signals` table. For CGM, query `rag_graph_nodes` + `rag_graph_edges`. Store as `Bundle.entries[i].content` string.
2. In `single_model_strategy.ts`, concatenate `bundle.entries.map(e => e.content).join('\n---\n')` into the system prompt.
3. Apply the same 6000-token cap.

Either approach: 8+ tests covering the new behavior — content actually present in prompt, cap enforcement, graceful degradation when content load fails, parity between single_model and panel strategies.

**Stream B acceptance:** for query "what is my D1 chart" against a real bundle, the system prompt sent to the LLM contains actual planetary position data (or actual MSR signal claims) that traces back to FORENSIC. Verify by inspecting a captured prompt during the verification stream.

### Stream C — FUB-3: Inject pre-fetched tool_results into modelMessages

`route.ts:145-157` already eagerly pre-fetches tool results (`validToolResults`) and passes them to `orchestrator.synthesize()` as `tool_results`. In `single_model_strategy.ts`, that field is destructured but never injected into `modelMessages`. The pre-fetched MSR signals are silently dropped.

1. In `single_model_strategy.ts`, after constructing the system prompt and before adding the user message: for each entry in `request.tool_results ?? []`, construct an inline injection:
   ```
   <pre_fetched_tool_result tool="${entry.tool_name}" params_hash="${entry.params_hash}">
   ${entry.result_summary}
   </pre_fetched_tool_result>
   ```
2. Append all such blocks as additional system message content.
3. Mirror in `panel_strategy.ts`.
4. Add a `MAX_TOOL_RESULTS_INJECTION_TOKENS` cap (~3000) to prevent prompt explosion when many tools were pre-fetched. Truncate oldest entries if needed.
5. 4+ tests: pre-fetched results land in prompt; empty `tool_results` is no-op; cap enforced; both strategies have parity.

**Stream C acceptance:** when `route.ts` pre-fetches MSR signals and passes them, those signals appear in the LLM prompt. Verify by capturing one prompt during verification.

### Stream D — FUB-4: Extend `vector_search` authorization to other query classes

Fix A added `vector_search` only to the `factual` few-shot. Other query classes that need chart-grounded answers also benefit.

1. In `platform/src/lib/router/prompt.ts`, find the few-shot examples for query classes:
   - `interpretive`
   - `holistic`
   - `cross_domain`
   - (do NOT add to `predictive` — those queries should be grounded in MSR + CGM, not raw FORENSIC chunks)
2. For each, add `vector_search` to `tools_authorized`.
3. Update or add 4 router tests verifying the new authorization for each class.

**Stream D acceptance:** router tests pass; manual inspection of one router output for an `interpretive` query shows `vector_search` in `tools_authorized`.

### Stream E — Live LLM verification smoke

This is the moment of truth. The previous Phase 11A.RESTART smoke was blocked by no Auth Proxy. We're explicitly requiring Auth Proxy here, and we're going to run a real query against a real LLM and verify the response contains real chart data.

1. New script `platform/scripts/cutover/stage1_phase12_smoke.ts`. Required env: `SMOKE_SESSION_COOKIE`, `SMOKE_CHART_ID`, Anthropic + OpenAI + Google API keys.

2. The script:
   a. Verifies Cloud SQL Auth Proxy is running (`pgrep cloud_sql_proxy`).
   b. POSTs to `/api/chat/consume` with the canonical D1 query: `"What is my D1 chart? List Sun, Moon, and Ascendant positions with sign and degree."`
   c. Captures the streamed response.
   d. **Asserts** that the response contains:
      - At least one `[signal:...]`, `[asset:...]`, or `[chunk:...]` citation marker (proves vector_search or tool_results was called)
      - A reference to the canonical Sun position (sign + house — match against the FORENSIC reference values)
      - A reference to the canonical Moon position
      - A reference to the canonical Ascendant
   e. Reads the matching `audit_log` row. Asserts `bundle_keys` contains FORENSIC_v8_0 (confirms bundle composer ran). Inspects `payload` for `chart_context` (confirms FUB-1 ran). Inspects `synthesis_input_tokens` is non-trivially high (confirms content was actually in the prompt — likely > 4000 tokens, vs the previous run where it was probably under 1000).
   f. Prints a green ✅ summary on success or red ✗ with the divergent assertions on failure.

3. The script's expected canonical values for assertions live in a header constant block. Native must verify them against `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` before merging this brief — they're the ground truth.

4. The script saves its captured response + audit row to `platform/scripts/cutover/stage1_phase12_smoke_evidence.json` regardless of pass/fail, so native can inspect the actual content.

**Stream E acceptance:** `npm run cutover:phase12-smoke` returns ✅ for the canonical D1 query, AND the captured response (when read by a human) describes the native's actual chart, not a fabrication.

## Critical constraints

- **All flags stay at current defaults.** No flag-flipping during this brief.
- **Backward compat for existing tests.** `chart_context` is optional. Existing tests that don't provide it must still pass (verify fallback path).
- **Phase 7 panel strategy parity.** Whatever lands in `single_model_strategy.ts` for FUB-1 / FUB-3 must mirror in `panel_strategy.ts`. Otherwise panel mode regresses while single-model is fixed.
- **Auth Proxy is non-negotiable for Stream E.** The smoke MUST run against live DB + live LLMs. Mocked smoke would defeat the purpose — mocks were the reason we missed this gap.
- **Token budget discipline.** Stream B's content load and Stream C's tool_results injection both have caps. Don't blow up the prompt to multi-hundred-thousand tokens.
- **Citation markers must be preserved.** When chunks are injected (Stream B Approach B) they must carry `[chunk:rag_chunk_id]` markers so the existing CitationChip rendering picks them up. When pre-fetched MSR signals are injected (Stream C) they must carry `[signal:...]` markers.
- **No legacy regression.** Run the existing test suite at the end. If anything was inadvertently broken (the legacy code path is still there, opt-out via env var), surface it and fix.

## Done criteria

1. Pre-flight gate passes (Phase 11A.DEBUG complete + Fix A/B verified + Auth Proxy running).
2. Stream A: chart_context plumbed; both strategies use real values; tests pass; rendered prompt contains canonical birth date.
3. Stream B: floor-asset content (or lazy-loaded chunks) reach the LLM prompt; cap enforced; tests pass.
4. Stream C: pre-fetched tool_results reach the LLM prompt; cap enforced; tests pass.
5. Stream D: `vector_search` authorized for `interpretive`, `holistic`, `cross_domain`; router tests pass.
6. Stream E: `cutover:phase12-smoke` returns ✅; captured response describes the native's actual D1 chart (not fabrication); audit row shows bundle_keys + chart_context + non-trivial synthesis tokens.
7. `lint` + `type-check` clean across all modified files.
8. Existing test suite passes (no legacy regression).
9. Native acceptance: native opens the consume page, asks "what is my D1 chart" through the UI, and the answer correctly identifies their actual planetary positions.

## Risk classification: MEDIUM

This is the largest behavioral fix since Phase 3. Touches synthesis, bundle, router, and route. Mitigations:
- All changes are additive (new fields, new injection points). Existing code paths still execute.
- Type changes are optional fields with fallback behavior.
- Phase 11A.DEBUG already verified the surrounding architecture (chart_id flows correctly, route is correct, components render correctly).
- Live smoke (Stream E) is the explicit verification gate — this brief doesn't claim done without proof against real LLM + real DB.
- Auth Proxy gate at the front prevents trying to verify against mocked infrastructure.

The unavoidable residual risk is content quality — even with all data plumbed correctly, the LLM's interpretation of FORENSIC content might not be acharya-grade. That's a separate prompt-engineering problem, not a data-plumbing problem. Phase 12 ensures the data reaches the LLM. The acharya-grade-ness of what comes back is governed by Phase 6 checkpoints + future prompt iterations.

## Forward implications

After Phase 12 ships:
- The wrong-chart-data bug is resolved.
- The architectural gap I implicitly assumed in Phase 2/3 is now closed and explicit.
- Phase 11B (legacy code deletion) becomes truly safe to trigger — it can run after Phase 12's smoke is green.
- The two synthesis surfaces question (TypeScript vs Python sidecar) remains open but is now decided on a fairer footing.
- Phase 10 (Calibration Loop) becomes truly authorable when prediction outcomes accumulate post-fix.

## How native triggers

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension):

> Read EXEC_BRIEF_PHASE_12_v1_0.md and execute it.

Make sure Cloud SQL Auth Proxy is running (`pgrep cloud_sql_proxy` returns at least one PID). Have your `SMOKE_SESSION_COOKIE` and `SMOKE_CHART_ID` env vars handy — Stream E will need them.

After Sonnet completes, you'll get:
- A green ✅ from `npm run cutover:phase12-smoke` proving the LLM now answers the canonical D1 query correctly
- An evidence JSON dump showing the prompt content, the audit row, and the LLM's response
- A clear native-acceptance step: ask the question through the UI yourself, see real chart data

If green and you're satisfied, the Phase 11B legacy-deletion brief becomes a defensible next step. If anything is off in the captured evidence, hold and we'll author another follow-up.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when all 9 done-criteria pass and native accepts
