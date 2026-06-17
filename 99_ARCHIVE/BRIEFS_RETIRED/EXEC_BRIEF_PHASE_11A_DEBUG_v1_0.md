---
brief_id: EXEC_BRIEF_PHASE_11A_DEBUG
version: 1.0
status: COMPLETE
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code
trigger_phrase: "Read EXEC_BRIEF_PHASE_11A_DEBUG_v1_0.md and execute it."
phase: 11A.debug
phase_name: Phase 11A — Investigate Wrong Chart Data + Missing UI Elements
risk_classification: LOW (read-mostly investigation; small surgical fixes permitted with clear evidence)
parallelizable_with: []
depends_on: [EXEC_BRIEF_PHASE_11A_RESTART_v1_0.md (COMPLETE — server is up on port 3000 with NEW_QUERY_PIPELINE_ENABLED=true and AUDIT_ENABLED=true)]
output_artifact: platform/scripts/cutover/stage1_debug_report.md
---

# EXEC_BRIEF — Phase 11A Debug — Investigate Wrong Chart Data + Missing UI

## Mission

Native confirms the new pipeline is active (server running on port 3000, flags ON). Visited `http://localhost:3000/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume`. Two distinct problems reported:

**Problem 1 — Wrong Chart Data (CRITICAL).** Query "what is my D1 chart" returns a completely different planet configuration than the native's actual chart. The `rag_chunks` / `msr_signals` / FORENSIC data is known correct. So the corruption is downstream of the corpus — somewhere in chart resolution, bundle composition, or synthesis. **This is a fundamental B.1 (facts/interpretation separation) and B.10 (no fabricated computation) violation per CLAUDE.md §I. Highest priority.**

**Problem 2 — Missing UI Elements.** Native does not see the super-query / panel button or other expected UI changes. Some of this may be by design (PANEL_MODE_ENABLED defaults to false → checkbox hidden), but the user expected to see *some* visible difference and is not. Lower priority but warrants a clear answer.

Native explicitly chose to keep the new pipeline ON during debugging — willing to accept wrong answers until both issues are resolved. Do NOT disable any flags during this investigation.

## Scope

**`may_touch` (read access):**
- All of `platform/src/`, `platform/python-sidecar/`, `platform/scripts/`, root project files (read-only inspection)
- The Cloud SQL `audit_log` table via existing read tooling (`audit:replay`, direct psql via Auth Proxy if available)
- The browser-rendered HTML at `http://localhost:3000/clients/[clientId]/consume` via curl (server-side rendered output) and via reading the running dev server's logs

**`may_touch` (write access — narrow):**
- `platform/scripts/cutover/stage1_debug_report.md` (new — output of this investigation)
- `platform/scripts/cutover/stage1_debug_*.json` (new — captured audit row dumps, bundle dumps, synthesis-input dumps; intermediate evidence files)
- **Surgical fixes only when ALL of the following are true:** (1) root cause is unambiguous, (2) fix is one to ten lines, (3) fix is in non-frozen scope per prior phase briefs, (4) fix is documented in the report with before/after diff. Anything else is documented as a recommended follow-up brief, NOT applied.

**`must_not_touch`:**
- Any feature flag value (keep new pipeline ON throughout)
- Any DB schema or content (read-only; do NOT seed test data, do NOT modify chart records, do NOT modify msr_signals)
- The legacy code path under any circumstance (irrelevant to this debug; we're not reverting)
- `platform/python-sidecar/rag/embed.py` (canonical embedding source-of-truth — frozen)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (governance only)

## Sub-streams (6 sequential)

### Stream A — Capture the failing query trace from `audit_log`

Native has been submitting queries via the Consume tab. Since `AUDIT_ENABLED=true` post-restart, those queries should have left audit rows.

1. Connect to the live Cloud SQL DB (Auth Proxy must be running).
2. Pull the most recent audit row for chart_id `362f9f17-95a5-490b-a5a7-027d3e0efda0`. Filter by query_text containing "D1" or "chart" or by recent created_at. Capture the full row to `platform/scripts/cutover/stage1_debug_audit_row.json`.
3. From that row, extract and inspect:
   - `query_text` (exactly what the user asked)
   - `query_class` (what the router classified it as)
   - `bundle_keys` (which assets the pipeline pulled — JSON array)
   - `tools_called` (sequence of tool calls + params + latency + cached flag)
   - `validators_run` (P1/P2/P5 results)
   - `synthesis_model` (which LLM did the synthesis)
   - `synthesis_input_tokens` and `synthesis_output_tokens`
   - `disclosure_tier`
   - `final_output` (the wrong chart description)
   - any `payload.checkpoints` or `payload.panel` (likely empty since those flags are off)
4. **Critical first hypothesis test**: does `bundle_keys` contain the FORENSIC asset_id? If FORENSIC is absent from the bundle, the synthesis was operating without the canonical chart and necessarily fabricated. Document this finding either way.
5. **Critical second hypothesis test**: does `bundle_keys` reference a chart_id that matches `362f9f17-95a5-490b-a5a7-027d3e0efda0`? Or did the bundle composer pull a different chart (test fixture, default chart, another user's chart)?

Stream A output: section "Audit Row Trace" in the report with the full JSON dump linked + key findings extracted as bullet points.

### Stream B — Trace chart_id flow through pipeline stages

The chart_id from the URL must reach the bundle composer. Verify each handoff.

1. Open `platform/src/app/clients/[clientId]/consume/page.tsx`. Confirm: how does it read `clientId` from the route params? Does it pass it to `<ConsumeChat />`? With what prop name?
2. Open `platform/src/components/consume/ConsumeChat.tsx`. Find where it submits the query. Confirm: is the `clientId` (or chart_id) being included in the request body posted to `/api/chat/consume`?
3. Open `platform/src/app/api/chat/consume/route.ts`. Confirm: does the route handler extract chart_id from the request body? Does it pass it to the orchestrator (`createOrchestrator`)?
4. Open `platform/src/lib/synthesis/orchestrator.ts` and `platform/src/lib/synthesis/single_model_strategy.ts`. Confirm: does the strategy receive chart_id? Does it pass it to the router and bundle composer?
5. Open `platform/src/lib/router/**` and `platform/src/lib/bundle/**`. Confirm: does the router/bundle composer use chart_id when resolving entities and pulling signals?
6. **Critical hypothesis test**: at what stage (if any) does chart_id get lost, replaced with a default, or resolved to a different chart? Document the precise line where divergence happens.

Stream B output: section "Chart-ID Flow Trace" with a per-stage breakdown showing what chart_id each layer sees and any divergence points.

### Stream C — Bundle content audit

What did the bundle composer actually produce for the failing query?

1. Re-submit the same query the user submitted ("what is my D1 chart" or equivalent) directly via curl, with the native's session cookie + chart_id. Capture the response.
2. If the bundle composer has a debug or telemetry hook that logs the assembled bundle, enable it transiently and re-run. (DO NOT modify production telemetry permanently — this is just for capture.) Otherwise, add a temporary `console.log` of the bundle payload, run the query, then REVERT the log addition.
3. Compare the assembled bundle against:
   - The expected FORENSIC asset (read from `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` or its corresponding `rag_chunks` rows for the canonical chart)
   - The expected MSR signals for the native (read from `msr_signals` filtered by subject)
   - The expected CGM nodes for the native (read from `rag_graph_nodes` filtered by chart context)
4. Document the gap. Common patterns:
   - Bundle is empty → bundle composer is broken
   - Bundle is non-empty but contains only schema/architecture chunks (the corpus has both content + meta-chunks) → bundle composer is filtering wrong layer
   - Bundle contains the right chunk count but wrong chart → chart_id resolution problem
   - Bundle is correct but small → maybe correct, problem is downstream

Stream C output: section "Bundle Content Audit" with the captured bundle dumped to `stage1_debug_bundle.json`, plus a side-by-side comparison vs expected.

### Stream D — Synthesis input audit

What did the LLM actually see when generating the wrong answer?

1. From Stream C's bundle and Stream A's audit row, reconstruct (or re-capture via temporary log) the exact prompt that was sent to the synthesis model.
2. Inspect the prompt for:
   - Does it contain the FORENSIC chart data verbatim, or a summary, or nothing?
   - Does it include the user's actual planetary positions (Sun, Moon, Asc, etc.)?
   - Does it use the `msr_signals` data correctly?
   - Are there citation placeholders (`[signal:...]`, `[asset:...]`) the LLM was told to fill?
   - Is the prompt template saying "you have access to the native's chart" but then not actually including it?
3. **Three failure modes to distinguish:**
   - **Data-layer break**: bundle is wrong → prompt has wrong data → answer is necessarily wrong
   - **Prompt-layer break**: bundle is right but prompt template strips it or formats it incorrectly → LLM sees nothing useful → fabricates
   - **Synthesis-layer break**: bundle is right and prompt is right but LLM hallucinates anyway → either LLM provider issue, model misconfiguration, or temperature/sampling problem

Stream D output: section "Synthesis Input Audit" with the actual prompt text dumped to `stage1_debug_prompt.txt` (redact session tokens if present), plus identification of which of the three failure modes is in effect.

### Stream E — UI visibility check

Lower priority but resolve clearly.

1. Open `platform/src/app/clients/[clientId]/consume/page.tsx` again. Verify:
   - Does it pass `pipelineEnabled` AND `audienceTier` to `<ConsumeChat />` after the singleton refresh? (Both should now be `true` / `super_admin` since restart.)
2. Open `platform/src/components/consume/ConsumeChat.tsx`. Verify:
   - Does it conditionally render the panel checkbox? What flag gates it? (Almost certainly `PANEL_MODE_ENABLED` — which is still false. So the absence of the panel button is BY DESIGN.)
   - Does it render `<DisclosureTierBadge />` in the sticky header? Under what conditions?
   - Does it render `<StreamingAnswer />` in the message list? Under what conditions?
3. Capture a curl-rendered snapshot of the consume page HTML (server-side rendered) and grep for `DisclosureTierBadge`, `StreamingAnswer`, `panel-checkbox` (or however the panel button class is named). Note presence/absence.
4. **Verdict**: the missing panel button is by design (flag is off — to enable, set `PANEL_MODE_ENABLED=true`). The missing DisclosureTierBadge or StreamingAnswer would be a real bug. Document which.

Stream E output: section "UI Visibility Check" with grep results, conditional render summary, and clear verdict on which absences are intentional vs unintentional.

### Stream F — Synthesize, prioritize, and either fix or recommend

1. Synthesize Streams A-D into the **chart-data root cause**. State which layer is broken (chart-id flow, bundle composition, prompt construction, or synthesis).
2. State whether a surgical fix (1-10 lines, in non-frozen scope, unambiguous) is possible.
   - If YES: apply the fix. Document the diff in the report. Do NOT modify any flag values.
   - If NO: write a recommended follow-up brief outline (file paths, scope, risk classification) and do not apply changes.
3. State the UI verdict from Stream E in plain language for the native.
4. Final report at `platform/scripts/cutover/stage1_debug_report.md` with all sections, evidence files linked, and a clear "Native Action" closing section.

Stream F output: the report. If a fix was applied, the report's "Native Action" says "restart dev server and re-test query X to confirm fix." If no fix was applied, the report's "Native Action" outlines the recommended follow-up brief.

## Critical constraints

- **Keep the new pipeline ON.** Do NOT touch `NEW_QUERY_PIPELINE_ENABLED` or `AUDIT_ENABLED` defaults or env values. Native explicitly directed this.
- **Read-mostly.** Surgical fixes only with the four conditions in Scope. Anything ambiguous or larger gets documented, not applied.
- **No data mutation.** Do not seed test rows. Do not modify chart records. Do not write to `msr_signals` or `rag_chunks`.
- **Temporary instrumentation must be reverted.** If a `console.log` or temp telemetry hook is added during Stream C/D, it MUST be removed before Stream F closes. The codebase post-investigation should be byte-identical to pre-investigation EXCEPT (a) the report file, (b) evidence JSON files, (c) any surgical fix that was applied.
- **Cloud SQL Auth Proxy required.** If it isn't running locally, surface the requirement clearly and halt — don't try to debug without DB access.
- **Cite specific evidence.** Every finding must reference a file:line, an audit row column, or a specific section of a captured JSON dump.

## Done criteria

1. Audit row for the failing query is captured to `stage1_debug_audit_row.json`.
2. Chart-ID flow through pipeline is traced and divergence (if any) is identified.
3. Bundle content is captured and compared to expected.
4. Synthesis prompt is captured and the failure mode (data / prompt / synthesis) is identified.
5. UI visibility verdict is given for each missing element.
6. Either a surgical fix is applied (with documented diff) OR a follow-up brief is outlined.
7. `stage1_debug_report.md` exists with all sections + Native Action.
8. Any temporary instrumentation has been reverted.

## How native triggers

In a Claude Code session in Anti-Gravity (Sonnet 4.6 in VS Code extension):

> Read EXEC_BRIEF_PHASE_11A_DEBUG_v1_0.md and execute it.

Make sure Cloud SQL Auth Proxy is running locally before triggering. The investigation needs DB read access.

## Status updates

- AUTHORED 2026-04-28
- IN_PROGRESS_STREAM_X — set when Sonnet picks up the brief
- COMPLETE — set when the report exists with a clear root cause + Native Action
