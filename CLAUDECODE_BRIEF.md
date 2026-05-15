---
canonical_id: CHAT_V2_MASTER_EXECUTOR
version: 1.0
status: ACTIVE
authored: 2026-05-16
author: Claude (Cowork planning session)
governing_plan: 00_ARCHITECTURE/CHAT_V2_PLAN_v1_0.md
intended_destination: /Users/Dev/Vibe-Coding/Apps/Madhav-chat-v2/CLAUDECODE_BRIEF.md
worktree_branch: feature/chat-v2-bigbang
current_phase: pre_alpha
current_work_item: PA1
total_work_items: 32
completed_work_items: 0
expected_duration_weeks: 6
executor_mode: autonomous (bypass-permissions + skip-permissions in Antigravity IDE)
manual_intervention_deferred: yes (all items collected in §M of this brief)
---

# CHAT V2 BIG BANG — MASTER EXECUTOR BRIEF

You (Claude Code) are executing the chat-v2 big-bang workstream autonomously inside a git worktree at `/Users/Dev/Vibe-Coding/Apps/Madhav-chat-v2` on branch `feature/chat-v2-bigbang`. This is a **single coherent ship** spanning ~6 weeks and ~38 Claude Code sessions. Native is running you with `--dangerously-skip-permissions` in Antigravity IDE and will not intervene during execution unless this brief explicitly tells you to pause.

The governing plan is `00_ARCHITECTURE/CHAT_V2_PLAN_v1_0.md` v1.1. Re-read it once at session open so you have the architecture context. This brief operationalizes the plan into 32 executable work items.

## §H — How to use this brief

### Your loop, every session:

1. **At session open**: read this brief's frontmatter to find `current_phase` and `current_work_item`. Read `CHAT_V2_PROGRESS.md` at the worktree root for the detailed progress state and any `RESUME_HERE` marker from the previous session.
2. **Re-read** `00_ARCHITECTURE/CHAT_V2_PLAN_v1_0.md` §3 (scope), §4 (architecture decisions), §9 (test strategy), §10 (master gate). You don't need to re-read the whole plan every session — just these.
3. **Navigate** to §P (Pre-α), §A (Alpha), §B (Beta), §G (Gamma), or §PM (Pre-merge) below to find your current work item's section.
4. **Execute** the work item per its embedded brief: implement → test → verify acceptance criteria → commit.
5. **Update** `CHAT_V2_PROGRESS.md` with what you did (the new entry includes work item ID, commit SHA(s), tests added, files touched, time, blockers if any).
6. **Advance frontmatter**: update `current_work_item` to the next item; if you completed the last item in a phase, advance `current_phase`. Increment `completed_work_items`.
7. **Decide whether to continue or stop** (see §S — Stop conditions).

### When to continue vs. stop in a session:

- **Continue** if: context budget feels healthy (you've completed fewer than 3 work items this session), no `MANUAL_INTERVENTION` marker hit, no hard gate just discharged, no work-item blocker.
- **Stop** if: any of the above are false, OR you've been running >2 hours, OR you've completed 3+ work items already, OR you just discharged a hard gate (α0).

When stopping, write a `RESUME_HERE` block to `CHAT_V2_PROGRESS.md` describing the precise next step.

### When to halt for manual intervention:

A `MANUAL_INTERVENTION_REQUIRED` marker means STOP and do NOT attempt the action. Most are deferred to §M (end of brief). The mid-flight ones:

- **α0 spike fail**: if assistant-ui can't satisfy the spike's acceptance criteria, STOP. Document the failure in `CHAT_V2_PROGRESS.md` under a `SPIKE_FAILURE` block. Do not proceed to α1.
- **Master gate evidence pack incomplete (PM2)**: if any §10 criterion cannot be discharged in evidence, STOP and emit a `MASTER_GATE_GAP` block listing the gaps.

## §C — Conventions

### Commit messages

Format: `<type>(chat-v2/<work_item>): <short description>`

Types:
- `feat` — new behavior visible to user (most work items)
- `test` — new tests (test scaffolding, fixture additions)
- `refactor` — internal restructure, no behavior change
- `fix` — repair a bug introduced earlier in the workstream
- `chore` — tooling, deps, CI, config
- `docs` — documentation
- `milestone` — phase exits

Examples:
```
feat(chat-v2/α2): swap react-markdown for streamdown
test(chat-v2/α1): scaffold playwright + token-trace fixtures
refactor(chat-v2/α4): convert synthesis history to UIMessage end-to-end
milestone(chat-v2/α): phase alpha complete - foundation
```

One commit per work item if possible. If a work item needs multiple commits, prefix each with the work-item ID.

### Progress tracker (`CHAT_V2_PROGRESS.md`)

Live document at the worktree root. After each commit, append an entry:

```markdown
## <work_item_id> — <work_item_name>
- **Completed**: <ISO timestamp>
- **Commit(s)**: <SHA1>, <SHA2>
- **Files touched**: <list>
- **Tests added**: <count + paths>
- **Acceptance criteria**: <PASS|PARTIAL with notes>
- **Blockers**: <none | description>
- **Notes for Cowork**: <anything the native should know>
```

If you stop mid-flight, append a `RESUME_HERE` block:
```markdown
## RESUME_HERE
- **Last completed**: <work_item_id>
- **Next**: <next_work_item_id>
- **State**: <clean | dirty with description>
- **Reason for stop**: <context budget | time | hard gate | blocker>
```

### Test failures during work items

If a test fails:
1. Try to fix the bug (up to 3 attempts, ~30 min total).
2. If unfixable in that budget, mark the work item BLOCKED, commit what works (compiles, lints clean) with `wip(chat-v2/<work_item>): <description> — BLOCKED: <reason>`, update the progress tracker with the blocker, and stop.

### Dependency installation

When a work item needs `npm install <pkg>`, run it and commit the `package.json` + `package-lock.json` deltas as part of the work item's commit. Do not split deps into a separate commit unless they're large (>5 packages).

### Migration creation

When a work item needs a database migration, create the file under `platform/supabase/migrations/<NNN>_<name>.sql` with the next available number. DO NOT apply the migration automatically. Note in the progress tracker that it's pending application. Migration application is deferred to §M manual intervention.

### Provider fixture recording

Fixture recording requires real provider keys + budget caps. DO NOT record fixtures during autonomous execution. Generate fixture *placeholders* with realistic shape, marked `// TODO(provider-record): replace with recorded response`. Fixture recording is deferred to §M.

### Visual regression baselines

When you add visual regression tests in α1 onward, generate baselines locally and commit them under `platform/tests/e2e/chat-v2/__visuals__/`. Visual diffs are gated to the workstream branch CI only.

### Master flag discipline

ALL new behavior is gated on `MARSYS_FLAG_CHAT_V2_ENABLED`. Flag-off must preserve current production behavior at commit `a7d4baf` (PIV close). Verify after every work item that flag-off code path still compiles and renders the legacy `ConsumeChat`.

## §S — Stop conditions

Stop at the END of a work item (never mid-work-item except for hard-gate failure or blocker). Stop reasons:

1. **Context budget low** (~40% remaining): "Save state and resume next session."
2. **Time budget** (~2h elapsed): same.
3. **Hard gate discharged** (α0 spike completed, α phase complete, β phase complete, γ phase complete, PM2 evidence pack complete): "Native review checkpoint. Pause."
4. **Blocker hit**: "Cannot proceed without manual intervention. See progress tracker."
5. **3+ work items completed this session**: "Healthy chunk shipped. Pause for review opportunity."

Always commit clean state before stopping. Never leave the worktree dirty across sessions.

## §R — Resumption protocol

When a new Claude Code session opens this worktree:

1. Read this brief's frontmatter for `current_phase` + `current_work_item`.
2. Read `CHAT_V2_PROGRESS.md` for the latest `RESUME_HERE` block.
3. Verify `git status` is clean. If dirty, halt and ask the native — this should not happen but we don't trust silently.
4. Verify the most recent commit matches the last progress-tracker entry. If they disagree, halt and ask.
5. Proceed with the work item.

## §P — Phase Pre-α (1 work item)

### PA1 — TEST_STRATEGY authoring

**Goal**: Translate the test strategy taxonomy in PLAN §9 into a concrete test plan with file paths, fixture inventory, and a CI pipeline YAML scaffold. This is the first concrete artifact; it un-blocks every test asserted in subsequent work items.

**Files to create**:
- `00_ARCHITECTURE/CHAT_V2_TEST_STRATEGY_v1_0.md` — the detailed test plan
- `platform/tests/fixtures/chat-v2/.gitkeep` + subdirs (`providers/`, `conversations/`, `multimodal/`, `validator/`, `panel/`, `streaming-chunks/`, `pdfs/`, `images/`)
- `.github/workflows/chat-v2-ci.yml` — the 15-stage CI pipeline (placeholder jobs that succeed; real assertions added per work item)
- `platform/tests/load/k6/.gitkeep`

**Implementation steps**:
1. Author `CHAT_V2_TEST_STRATEGY_v1_0.md` with sections matching PLAN §9.2.1-§9.2.16, each with concrete file paths and example test descriptions.
2. Create fixture directory tree.
3. Scaffold `chat-v2-ci.yml` with the 15 stages from PLAN §9.4 — each stage a no-op job for now that will be populated as work items add tests.
4. Add `npm run chat-v2:test` script to `platform/package.json` that runs the cumulative workstream test set.

**Tests added**: None (this is meta-test infrastructure).

**Commit**: `chore(chat-v2/PA1): scaffold test strategy + CI pipeline + fixture tree`

**Exit criteria**:
- `CHAT_V2_TEST_STRATEGY_v1_0.md` covers every category in PLAN §9.
- CI pipeline YAML lints clean.
- Fixture directories committed (via `.gitkeep`).

## §A — Phase α: Foundation (8 work items)

### α0 — assistant-ui fit-spike  [HARD GATE]

**Goal**: Verify that assistant-ui can satisfy MARSYS's edge-case requirements before committing the full path. If spike fails, plan pauses for re-scope.

**Files to create**:
- `platform/src/app/_dev/chat-spike/page.tsx` — super-admin-gated dev route
- `platform/src/app/api/chat/spike/route.ts` — stub endpoint streaming a known fixture via `streamText`
- `platform/tests/fixtures/chat-v2/spike/anthropic_thinking_6k.json` — placeholder for a 6000-token Anthropic thinking-model response (marked TODO-record)
- `00_ARCHITECTURE/chat_v2_briefs/CHAT_V2_α0_SPIKE_REPORT.md` — write the spike findings here

**Implementation steps**:
1. `npm install @assistant-ui/react @assistant-ui/react-ai-sdk @assistant-ui/styles` — verify versions compatible with `ai@^6.0.168` and `@ai-sdk/react@^3.0.170`.
2. Build minimal `Thread` mount at `/dev/chat-spike` with `useChat` against `/api/chat/spike`.
3. Spike endpoint streams a hand-authored 6000-token markdown fixture with code blocks, KaTeX math, inline citations, reasoning, and tool calls (use `dataStream.writeData` to inject synthetic data parts).
4. Verify by manual or Playwright-driven inspection: scroll anchoring under load (no jump on each token), message-edit UX, branching navigation, reasoning drawer expand/collapse, code block rendering + copy button, KaTeX math, regenerate button, abort button.
5. Verify visual quality with Modern Dark Pro tokens applied via assistant-ui's theming API (consult `assistant-ui/docs/theming.md`).
6. Document findings in `CHAT_V2_α0_SPIKE_REPORT.md`. Verdict must be one of: `GREEN` (proceed to α1), `YELLOW` (proceed with named workarounds), `RED` (halt plan, escalate to native).

**Tests added**: 1 Playwright test at `platform/tests/e2e/chat-v2/spike.spec.ts` that loads the spike page and asserts streaming completion + reasoning drawer presence + scroll position after stream.

**Commit**: `feat(chat-v2/α0): assistant-ui fit-spike + report`

**Exit criteria**:
- `CHAT_V2_α0_SPIKE_REPORT.md` exists with a clear verdict.
- Spike endpoint streams 6000-token fixture cleanly under Playwright.
- If verdict is `RED`: STOP, mark frontmatter `status: SPIKE_FAILED`, do NOT proceed to α1.
- If verdict is `GREEN` or `YELLOW`: STOP for native review (this is a hard gate). Commit + update progress tracker + stop.

### α1 — Test scaffolding

**Goal**: Stand up the Playwright + axe-core + Lighthouse CI + visual regression infrastructure so subsequent work items can add tests immediately.

**Files to create**:
- `platform/tests/e2e/chat-v2/playwright.config.ts` — Chromium + Firefox + WebKit + mobile viewports (375px iPhone Safari, 768px iPad Safari)
- `platform/tests/e2e/chat-v2/global-setup.ts` — fixture-mode adapter wiring
- `platform/tests/e2e/chat-v2/__visuals__/.gitkeep`
- `platform/tests/e2e/chat-v2/a11y/axe.spec.ts` — axe-core baseline assertion
- `platform/tests/e2e/chat-v2/perf/web-vitals.spec.ts` — Web Vitals budget assertions (TTFB <800ms, FCP <1.5s, LCP <2.5s, INP <200ms, CLS <0.1)
- `platform/tests/e2e/chat-v2/perf/streaming.spec.ts` — streaming metric assertions (TTFT, first-stage-event, frame budget, tokens/sec, memory growth)
- `platform/tests/fixtures/chat-v2/providers/<provider>/.gitkeep` for each of: anthropic, anthropic_thinking, gemini_pro, gemini_thinking, openai, deepseek_v4, deepseek_r1, nim
- `platform/tests/fixtures/chat-v2/streaming-chunks/{1char,small,large,mixed}.json` — chunk-size variants

**Implementation steps**:
1. `npm install -D @playwright/test @axe-core/playwright lighthouse-ci`
2. Configure Playwright with three browser projects + two mobile profiles.
3. Implement fixture-mode adapter: a test-time provider override that reads from `platform/tests/fixtures/chat-v2/providers/<provider>/<scenario>.json` instead of calling real providers. Routed via env var `MARSYS_FIXTURE_MODE=true`.
4. Author the four perf/a11y baseline tests; they pass against the spike fixture from α0.
5. Populate CI `.github/workflows/chat-v2-ci.yml` stages 1-7 with real assertions (stages 8-15 remain stubs until later work items).
6. Add `npm run chat-v2:e2e`, `npm run chat-v2:visual`, `npm run chat-v2:a11y`, `npm run chat-v2:perf` scripts.

**Tests added**: ~10 baseline E2E tests + ~5 unit tests for the fixture-mode adapter.

**Commit**: `test(chat-v2/α1): scaffold playwright + axe-core + lighthouse + visual baseline + fixture-mode adapter`

**Exit criteria**:
- All four baseline test scripts run green locally.
- CI pipeline stages 1-7 active and green.
- Fixture-mode adapter unit tests pass.

### α2 — streamdown swap

**Goal**: Replace `react-markdown` with `streamdown` for assistant message rendering. Single biggest visible-quality lever.

**Files to touch**:
- `platform/src/components/chat/MarkdownContent.tsx` — swap import + remove `closeUnclosedFences`
- `platform/src/components/chat/StreamingMarkdown.tsx` — keep memo wrapper, verify it still memoizes correctly
- `platform/package.json` — add `streamdown` (latest), remove `react-markdown` if unused elsewhere (grep first; if other usages, keep both)
- `platform/tests/unit/streaming/streamdown_render.test.ts` — new unit tests verifying incomplete fences, incomplete math, incomplete tables render correctly during stream

**Implementation steps**:
1. `npm install streamdown`
2. Grep for `react-markdown` usages outside `MarkdownContent.tsx`. If isolated, remove `react-markdown` from deps; if not, keep both.
3. Refactor `MarkdownContent` to use streamdown's component. Preserve `remarkPlugins: [remarkGfm, remarkMath]` and `rehypePlugins: [rehypeKatex]` (streamdown supports remark/rehype pass-through).
4. Delete `closeUnclosedFences` function — streamdown handles unterminated fences natively.
5. Add unit tests covering: incomplete code fence streamed across 2/5/10 chunks, incomplete KaTeX math, incomplete table, mixed-content stream.
6. Update visual regression baseline for a streaming-in-progress chat state.

**Tests added**: ~8 unit tests + 1 E2E test for streaming render correctness + 2 visual baselines.

**Commit**: `feat(chat-v2/α2): swap react-markdown for streamdown`

**Exit criteria**:
- All unit tests pass.
- Streaming-in-progress visual baseline matches expected.
- No `Maximum update depth exceeded` warnings under any input.
- Perf test asserts render <16ms/frame on streamed fixture.

### α3 — Data parts emission from route

**Goal**: Emit stage / tool / reasoning / cost / observability / citation_gate / persistence data parts from the consume route so the UI can render live progress.

**Files to create**:
- `platform/src/lib/streams/data_parts.ts` — Zod schemas + TS types for all data part variants
- `platform/src/lib/streams/__tests__/data_parts.test.ts` — schema unit tests

**Files to touch**:
- `platform/src/app/api/chat/consume/route.ts` — wrap pipeline stages with `dataStream.writeData(...)` calls
- `platform/src/lib/synthesis/single_model_strategy.ts` — emit cost data part in `onFinish`

**Implementation steps**:
1. Define Zod schemas at `platform/src/lib/streams/data_parts.ts`:
   ```ts
   type StagePart = { type: 'stage', stage: 'classify'|'compose_bundle'|'plan_per_tool'|'tool_fetch'|'synthesis'|'audit'|'panel:member:1'|... , status: 'running'|'done'|'error', ms?: number }
   type ToolPart = { type: 'tool', name: string, status: 'pending'|'running'|'done'|'error', ms?: number, ok_count?: number, err_count?: number }
   type CostPart = { type: 'cost', model: string, input_tokens: number, output_tokens: number, reasoning_tokens?: number, dollars: number, ms: number }
   type ObservabilityPart = { type: 'observability', query_id: string, trace_url: string }
   type CitationGatePart = { type: 'citation_gate', status: 'pass'|'warn'|'fail', issues?: string[] }
   type PersistencePart = { type: 'persistence', conversation_id: string, message_id: string, status: 'ok'|'error' }
   ```
2. Wrap each pipeline stage in `route.ts` with running/done writes.
3. Wrap each tool fetch in the `Promise.all` with running/done writes.
4. Emit cost in `onFinish` callback.
5. Emit observability + persistence in `onFinish`.

**Tests added**: ~12 unit tests for schemas + 3 integration tests verifying route emits expected data parts for a fixture query.

**Commit**: `feat(chat-v2/α3): emit stage/tool/cost/observability/persistence data parts`

**Exit criteria**:
- All data parts visible in browser devtools network stream for a test query (verified via Playwright network capture).
- Schema unit tests pass.
- No legacy code paths broken (flag-off `ConsumeChat` still works).

### α4 — UIMessage end-to-end

**Goal**: Eliminate string-flattening at the synthesis boundary. UIMessage parts (text, reasoning, tool-call, file) survive end-to-end. Closes prior Finding 8.

**Files to touch**:
- `platform/src/app/api/chat/consume/route.ts` — delete `extractText`; use `convertToModelMessages(uiMessages.slice(-N))` for both planner and synthesis history
- `platform/src/lib/synthesis/single_model_strategy.ts` — accept `ModelMessage[]` directly; remove `{role,content:string}` flattening at lines 305-309
- `platform/src/lib/synthesis/panel_strategy.ts` — same
- `platform/src/lib/adapters/types.ts` — verify `QueryRequest.messages` accepts full `ModelMessage[]`

**Implementation steps**:
1. Delete `extractText` function from `route.ts` (lines 987-988).
2. Replace planner-history rebuild at route.ts:240-247 with `convertToModelMessages(messages.slice(-N))`.
3. Replace synthesis-history rebuild at route.ts:631-638 with same.
4. Update `single_model_strategy.synthesize()` signature to accept `historyMessages: ModelMessage[]` instead of array of strings; remove the local map.
5. Update `panel_strategy.ts` similarly.
6. Grep for any remaining string flattening of message parts; refactor.
7. Add a unit test that pumps a UIMessage with text + reasoning + tool-call parts through the route's history building and asserts no parts are lost.

**Tests added**: ~6 unit tests for history building + 2 integration tests covering thinking-model + multi-modal scenarios.

**Commit**: `refactor(chat-v2/α4): preserve UIMessage end-to-end, remove extractText flattening`

**Exit criteria**:
- `grep -r extractText platform/src` returns zero matches.
- Reasoning parts from a thinking-model fixture surface intact in synthesis ModelMessage input.
- All existing tests still pass (no regressions).

### α5 — Retry policy right-sized

**Goal**: Replace blanket `maxRetries: 0` with a bounded provider-aware retry policy.

**Files to create**:
- `platform/src/lib/synthesis/provider_quirks.ts` — per-provider retry policy table

**Files to touch**:
- `platform/src/lib/synthesis/single_model_strategy.ts` — replace `maxRetries: 0` (line 441) with `maxRetries: providerQuirks[provider].maxRetries`
- `platform/src/app/api/chat/consume/route.ts` — fallback fires only after both primary attempts fail (current logic already does single-shot; verify no change needed beyond retry count)

**Implementation steps**:
1. Author `provider_quirks.ts`:
   ```ts
   export const providerQuirks = {
     anthropic: { maxRetries: 1, retryOn: ['network', '5xx', '429-with-retry-after'] },
     google: { maxRetries: 1, retryOn: ['network', '5xx'] },
     openai: { maxRetries: 1, retryOn: ['network', '5xx', '429-with-retry-after'] },
     deepseek: { maxRetries: 1, retryOn: ['network', '5xx'] },
     nim: { maxRetries: 0, retryOn: [] }, // NIM custom adapter has its own logic
   }
   ```
2. Update synthesis strategy to use the table.
3. Add chaos tests asserting: transient 503 retried once → succeeds; persistent 503 retried once → fallback fires; 4xx not retried.

**Tests added**: ~5 chaos tests + 3 unit tests for the quirks table.

**Commit**: `feat(chat-v2/α5): right-size retry policy per provider`

**Exit criteria**:
- Chaos tests assert correct retry behavior for each provider.
- Persistent 503 → fallback → user sees error (not silent failure).

### α6 — Feature-flag reconciliation

**Goal**: Eliminate dev / prod default drift across `feature_flags.ts`, `.env.local`, `deploy.yml`. Add `MARSYS_FLAG_CHAT_V2_ENABLED` flag.

**Files to touch**:
- `platform/src/lib/config/feature_flags.ts` — flip `ADAPTERS_ENABLED` and `CONSUME_UI_V2_ENABLED` defaults to `true` to match prod
- `.env.local` (in worktree only — does NOT get committed if .gitignored; but verify in plan) — add the new flag = false for dev
- `.github/workflows/deploy.yml` — add `MARSYS_FLAG_CHAT_V2_ENABLED=false` to env_vars

**Implementation steps**:
1. Audit current state: `grep -n "ADAPTERS_ENABLED\|CONSUME_UI_V2_ENABLED" platform/src/lib/config/feature_flags.ts .env.local .github/workflows/deploy.yml`.
2. Document the divergence at `00_ARCHITECTURE/CHAT_V2_FLAG_RECONCILIATION_v1_0.md`.
3. Choose strategy: flip `feature_flags.ts` defaults to `true` so local dev matches prod. Add `.env.development` if needed for local opt-out.
4. Add `MARSYS_FLAG_CHAT_V2_ENABLED` default `false` to all three locations.

**Tests added**: 1 unit test asserting `feature_flags.ts` exports the new flag.

**Commit**: `chore(chat-v2/α6): reconcile feature flag defaults, add MARSYS_FLAG_CHAT_V2_ENABLED`

**Exit criteria**:
- Local dev `npm run dev` against this branch behaves identically to production for chat (modulo master flag still `false`).
- New flag defined everywhere; defaults are coherent.

### α7 — Master flag wiring

**Goal**: Wire `MARSYS_FLAG_CHAT_V2_ENABLED` to switch between legacy `ConsumeChat` (current production) and new `ConsumeChatV2` (assistant-ui shell). Legacy path untouched.

**Files to create**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — new shell built on assistant-ui (initial scaffold; populated in β phase)

**Files to touch**:
- `platform/src/components/consume/ConsumeChat.tsx` — becomes thin switch: flag-off renders `<ConsumeChatLegacy />` (which IS the current ConsumeChat under a rename), flag-on renders `<ConsumeChatV2 />`
- Rename current `ConsumeChat.tsx` content to `ConsumeChatLegacy.tsx`

**Implementation steps**:
1. Copy current `ConsumeChat.tsx` contents to `ConsumeChatLegacy.tsx`.
2. Replace `ConsumeChat.tsx` with a thin switch component.
3. Create initial `ConsumeChatV2.tsx` that mounts assistant-ui `Thread` against the existing `/api/chat/consume` endpoint. At α7 it's intentionally minimal (no MARSYS chrome yet — that comes in β).
4. Add a Playwright test that verifies flag-off renders legacy + flag-on renders ConsumeChatV2.

**Tests added**: 2 E2E tests + 1 component test.

**Commit**: `feat(chat-v2/α7): wire master flag to switch between legacy and ConsumeChatV2`

**Exit criteria**:
- Flag-off behavior byte-identical to legacy.
- Flag-on renders assistant-ui Thread.
- Both paths in Playwright green.

### Phase α exit

After α7 completes, run the **Phase α gate** from PLAN §9.9:
- Cumulative unit ≥80, component ≥15, integration ≥10, E2E ≥10, visual baselines ≥20 — verify counts.
- TTFT and frame-budget metrics green against fixtures.
- α0 spike report `GREEN` or `YELLOW`.

Commit: `milestone(chat-v2/α): phase alpha complete — foundation`

Update progress tracker with phase summary. STOP for native review (hard gate).

## §B — Phase β: Behavioral parity (10 work items)

### β1 — Edit & regenerate

**Goal**: User can edit a prior user-message and regenerate from that point. Branching navigation works.

**Files to create**:
- `platform/src/app/api/chat/consume/regenerate/route.ts` — POST endpoint that truncates conversation to edit point and re-issues synthesis
- `platform/supabase/migrations/055_conversation_messages_parent.sql` — add `parent_message_id` column to `conversation_messages` (created in β2 — if β2 not yet run, skip this column and add it in β2)

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — wire assistant-ui's `MessageEdit` and `MessageRegenerate` composers

**Implementation steps**:
1. Wire assistant-ui `MessageEdit` primitive to enable in-thread editing of past user messages.
2. Wire `MessageRegenerate` primitive on assistant messages — triggers POST `/api/chat/consume/regenerate` with `{conversation_id, parent_message_id}`.
3. Regenerate endpoint reuses `consume` route's pipeline.
4. Add branching navigation UI (assistant-ui composer chooses between alternates).

**Tests added**: ~5 E2E tests covering edit/regenerate at first/middle/last positions, branching navigation, edit-cancel, regenerate-while-streaming.

**Commit**: `feat(chat-v2/β1): edit & regenerate via assistant-ui primitives`

**Exit criteria**: All edit-regenerate E2E tests green.

### β2 — Conversation persistence done right

**Goal**: Write-through persistence with confirmation. Conversation list. Reload restores. Closes prior issue where `replaceConversationMessages` was fire-and-forget.

**Files to create**:
- `platform/supabase/migrations/055_conversations.sql` — new schema:
  ```sql
  CREATE TABLE conversations (id UUID PK, owner_id UUID, title TEXT, created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ, archived_at TIMESTAMPTZ);
  CREATE TABLE conversation_messages (id UUID PK, conversation_id UUID FK, parent_message_id UUID NULL, role TEXT, parts_json JSONB, metadata_json JSONB, created_at TIMESTAMPTZ);
  CREATE INDEX ON conversation_messages (conversation_id, created_at);
  ```
- `platform/src/app/api/conversations/route.ts` — GET (list), POST (create)
- `platform/src/app/api/conversations/[id]/route.ts` — GET (fetch), DELETE (archive)
- `platform/src/app/api/conversations/[id]/messages/route.ts` — GET (restore)
- `platform/src/lib/persistence/conversation_writer.ts` — write-through helper

**Files to touch**:
- `platform/src/app/api/chat/consume/route.ts` — replace fire-and-forget `replaceConversationMessages` with confirmed write; emit `persistence:ok` data part
- `platform/src/components/consume/ConsumeChatV2.tsx` — add conversation list sidebar (assistant-ui `ThreadList`); restore on mount

**Implementation steps**:
1. Author migration 055.
2. Implement four route handlers.
3. Implement write-through writer with read-after-write verification.
4. Wire ConsumeChatV2's sidebar to `GET /api/conversations`.
5. On `/consume/[conversation_id]` mount, call `GET /api/conversations/[id]/messages` to restore.
6. Persistence data part triggers client `saved=true` only on receipt.

**Tests added**: ~8 integration tests + ~6 E2E tests.

**Commit**: `feat(chat-v2/β2): conversation persistence with write-through + restore + list`

**Exit criteria**: Reload preserves conversation; conversation list shows all owned conversations; archive works; persistence ack arrives in stream.

### β3 — Mid-stream interrupt semantics

**Goal**: Defined behavior when user submits while prior stream in-flight: cancel-and-replace (ChatGPT model).

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — composer's submit handler calls `chat.stop()` first if `isStreaming`
- `platform/src/app/api/chat/consume/route.ts` — accept abort signal (depends on β7); on cancellation, write partial output to `pending_streams` and mark `query_id` as cancelled in `query_trace_steps`

**Files to create**:
- `platform/src/components/chat/MID_STREAM_BEHAVIOR.md` — documents the cancel-and-replace contract

**Implementation steps**:
1. Composer submit while streaming: client calls `chat.stop()` → server abort → new query starts after 300ms.
2. Server marks cancelled `query_id` in `query_trace_steps` with `status='cancelled'` and `cancelled_at` timestamp.
3. UI shows "Cancelled — sending new query" toast briefly.

**Tests added**: ~4 E2E + ~3 integration tests.

**Commit**: `feat(chat-v2/β3): mid-stream interrupt semantics — cancel-and-replace`

**Exit criteria**: Mid-stream submit cancels prior within 300ms; new query begins; trace records show cancellation cleanly.

### β4 — Inline numbered citations + side panel

**Goal**: Perplexity-style `[1] [2]` superscripts with hover preview and side-panel pin.

**Files to create**:
- `platform/src/lib/citations/citation_data_part.ts` — citation data part schema
- `platform/src/components/chat/NumberedCitation.tsx` — inline `[N]` superscript renderer
- `platform/src/components/chat/CitationSidePanel.tsx` — pinned-citations panel

**Files to touch**:
- `platform/src/lib/synthesis/prompts/synthesis_prompt_v2.ts` (new — fork from current synthesis prompt) — instruct model to emit `[^N]` footnote markers + a citation block at end of answer
- `platform/src/components/consume/ConsumeChatV2.tsx` — wire side panel
- streamdown's footnote-render config

**Implementation steps**:
1. Update synthesis prompt to emit `[^N]` markers (streamdown footnote-style).
2. Route emits `citation` data parts with source metadata, indexed by N.
3. NumberedCitation renders inline + hover triggers existing `CitationPreview`.
4. Click pins citation in the side panel; multi-citation pin support.

**Tests added**: ~6 E2E + ~4 unit tests + 3 visual baselines.

**Commit**: `feat(chat-v2/β4): inline numbered citations + side panel`

**Exit criteria**: Inline `[1] [2]` render; hover shows preview; click pins in side panel.

### β5 — Multi-modal input (image + PDF)

**Goal**: Composer accepts image and PDF uploads. Files flow end-to-end via UIMessage parts.

**Files to create**:
- `platform/src/app/api/uploads/sign/route.ts` — signed URL token issuer
- `platform/src/lib/multimodal/upload_validator.ts` — mimetype, size, magic-byte validation
- `platform/src/lib/multimodal/pdf_extractor.ts` — Vertex AI Document Understanding integration

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — composer drop/paste/picker
- `platform/src/app/api/chat/consume/route.ts` — resolve file tokens → signed URLs → pass to provider

**Implementation steps**:
1. Upload flow: client → POST `/api/uploads/sign` → receives signed-URL token → uploads to GCS → token attached as UIMessage part.
2. Image part: passed directly to provider (Anthropic, Gemini, OpenAI all accept image URLs natively).
3. PDF part: Vertex AI Document Understanding extracts text + per-page images; attached as multiple text+image parts.
4. UI: image preview inline; PDF as file-card with page count + thumbnail.
5. **DO NOT** provision real GCS buckets — use fake-gcs-server for dev. Real bucket creation deferred to §M manual.

**Tests added**: ~10 E2E + ~5 integration tests + security tests (file upload validation).

**Commit**: `feat(chat-v2/β5): multi-modal input — image + PDF`

**Exit criteria**: Upload works in dev (fake-gcs); images and PDFs survive multi-turn conversation; security tests green.

### β6 — Per-message metadata reveal

**Goal**: assistant-ui message action menu's "Show details" → drawer with model, tokens, latency, validators, disclosure tier, citation count, cost, panel members, observability deep-link.

**Files to create**:
- `platform/src/components/chat/PerMessageDetailsDrawer.tsx`

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — wire drawer
- Use `messageMetadata` from existing `onFinish` callback as the data source

**Implementation steps**:
1. Drawer reads `message.metadata` (populated via existing callback).
2. Fields: model, input/output/reasoning tokens, latency, validators run + outcomes, disclosure tier, citation count, dollars, panel-member breakdown (if panel), "View trace" link (γ5 stub for now).

**Tests added**: ~3 E2E + ~2 component tests + 1 visual baseline.

**Commit**: `feat(chat-v2/β6): per-message details drawer`

**Exit criteria**: Drawer renders all fields for a complete message.

### β7 — Abort propagation completion

**Goal**: Pass `request.signal` through tool fetches, panel passthrough (until β9 replaces it), and adapter inner loops. Completes prior partial PIV.QG6.2 fix.

**Files to touch**:
- `platform/src/app/api/chat/consume/route.ts` — pass `request.signal` into `Promise.all(toolsAuthorized.map(...))`
- `platform/src/lib/synthesis/panel_strategy.ts` — pass abort into existing passthrough (will be replaced in β9)
- `platform/src/lib/adapters/types.ts` — add `abortSignal: AbortSignal | undefined` to `QueryRequest`
- `platform/src/lib/adapters/providers/adapter_anthropic.ts`, `adapter_gemini.ts`, `adapter_openai.ts`, `adapter_deepseek.ts`, `adapter_nim.ts` — each provider's `for await` checks `req.abortSignal?.aborted` and breaks

**Implementation steps**:
1. Update `QueryRequest` type.
2. Update each adapter's stream loop.
3. Pass signal into tool fetches and panel.
4. Chaos test: abort during retrieval phase aborts tool fetches; abort during synthesis aborts streamText; abort during panel aborts panel members.

**Tests added**: ~6 chaos tests + 2 unit tests.

**Commit**: `feat(chat-v2/β7): complete abort propagation through tool fetches + panel + adapters`

**Exit criteria**: Stop button cancels server-side within 200ms across all pipeline stages.

### β8 — Sliding-window history summarization

**Goal**: Replace hard 2-pair history truncate with sliding-window summarization at token budget threshold.

**Files to create**:
- `platform/src/lib/synthesis/history_compression.ts` — summarizer module with caching
- `platform/src/lib/synthesis/__tests__/history_compression.test.ts`

**Files to touch**:
- `platform/src/app/api/chat/consume/route.ts` — replace `historyMessageCap` truncate with compression call
- `platform/src/lib/config/feature_flags.ts` — add `MARSYS_FLAG_HISTORY_COMPRESSION_ENABLED` (default `false`; flipped on at γ exit)

**Implementation steps**:
1. Compression module: when conversation tokens > B (default 32k), summarize all turns older than the most recent K (default 4) via Haiku call.
2. Cache by `(conversation_id, tail_position)`. Recompute only when tail moves past boundary.
3. Sub-flag gates this so it can be safely disabled if issues arise.

**Tests added**: ~12 unit + ~4 integration tests covering short / long / boundary-crossing conversations.

**Commit**: `feat(chat-v2/β8): sliding-window history summarization`

**Exit criteria**: Turn 20 of a long conversation correctly references turn 1; summarization caches; sub-flag toggles cleanly.

### β9 — Honest panel streaming

**Goal**: Replace `PASSTHROUGH_MODEL = 'claude-haiku-4-5'` passthrough with real progressive adjudication. User sees stage events for each panel member + adjudicator.

**Files to touch**:
- `platform/src/lib/synthesis/panel_strategy.ts` — restructure: panel members fire in parallel as before; adjudication is itself a `streamText` call whose stream IS the user-visible stream; emit `stage` data parts for each member's status + adjudicator status
- `platform/src/lib/synthesis/prompts/adjudicator_prompt_v1.ts` — adjudicator prompt with panel members' answers in context

**Implementation steps**:
1. Remove `PASSTHROUGH_MODEL`.
2. Panel members run via `streamAdapter` in parallel; their final answers feed adjudicator's prompt.
3. Adjudicator's `streamText` call IS what the route streams to the user.
4. Member progress emitted as `stage: 'panel:member:N'` data parts.

**Tests added**: ~5 E2E + ~3 integration tests.

**Commit**: `feat(chat-v2/β9): honest panel streaming with real adjudicator stream`

**Exit criteria**: Panel-mode first stage event within 1s; adjudicator streams real tokens; no Haiku passthrough remains.

### β10 — Citation gate at the wire

**Goal**: Move citation gate from `onFinish` (decorative) to inline streaming validator that can emit error/info data parts mid-stream.

**Files to create**:
- `platform/src/lib/synthesis/streaming_citation_validator.ts`

**Files to touch**:
- `platform/src/app/api/chat/consume/route.ts` — wire validator to SDK's `onChunk` or `onFinishStep` hook; remove the decorative onFinish gate

**Implementation steps**:
1. Validator inspects accumulated answer + citation data parts at each chunk boundary (or step boundary).
2. On hard-fail: inject `{type:'error', code:'CITATION_GATE_FAIL', issues}` data part.
3. On soft-fail: inject `{type:'info', code:'CITATION_WARNING', issues}`.
4. Client renders inline red band (hard) or footer chip (soft) — composers in γ4.

**Tests added**: ~5 unit + ~3 chaos tests (gate hard-fail, soft-fail, pass).

**Commit**: `feat(chat-v2/β10): citation gate enforced at the wire via streaming validator`

**Exit criteria**: Hard-fail produces user-visible error part; gate is enforceable.

### Phase β exit

Run Phase β gate from PLAN §9.9. Verify cumulative test counts. Verify all behavioral parity master-gate criteria green.

Commit: `milestone(chat-v2/β): phase beta complete — behavioral parity`

STOP for native review.

## §G — Phase γ: Domain & polish (10 work items)

### γ1 — Panel mode display UX

**Goal**: Panel answer renders with confidence ribbon + collapsible per-member dissent + adjudicator rationale footer. Disclosure-tier gated.

**Files to create**:
- `platform/src/components/chat/PanelDissentTabs.tsx`
- `platform/src/components/chat/PanelConfidenceRibbon.tsx`

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — wire when message metadata indicates panel-mode

**Implementation steps**:
1. Ribbon at top of panel answer shows confidence (from adjudicator).
2. "Show panel dissent" toggle reveals tabbed view of per-member answers.
3. Adjudicator rationale as footer.
4. Disclosure tier: `super_admin` full content; lower tiers see summary only.

**Tests added**: ~4 E2E + ~2 component + 3 visual baselines.

**Commit**: `feat(chat-v2/γ1): panel mode display UX`

**Exit criteria**: Toggle reveals dissent; super-admin sees full content.

### γ2 — Long-reasoning UX for thinking models

**Goal**: Reasoning drawer shows live token-count + elapsed-time-in-thought. Collapse default at >2k reasoning tokens.

**Files to touch**:
- `platform/src/components/chat/ReasoningProgress.tsx` (new) — progress indicator within reasoning
- assistant-ui's reasoning composer wrapper

**Implementation steps**:
1. Count reasoning tokens via cumulative `reasoning_delta` lengths.
2. Elapsed timer starts on first reasoning delta.
3. If reasoning >2k tokens, drawer collapsed by default with `Show 3,420 tokens of reasoning ⌄` affordance.

**Tests added**: ~3 E2E + ~2 unit tests.

**Commit**: `feat(chat-v2/γ2): long-reasoning UX with live progress`

**Exit criteria**: Drawer shows live count + timer; collapse-default at >2k.

### γ3 — Prediction logging affordance (PPL)

**Goal**: Detect time-indexed predictions in assistant output; expose "Log as prediction" affordance; write to `predictions` table with falsifier captured.

**Files to create**:
- `platform/src/lib/ppl/prediction_detector.ts` — pattern detector (regex + Haiku classifier)
- `platform/src/lib/ppl/prediction_writer.ts` — Postgres writer
- `platform/src/app/api/predictions/route.ts` — POST endpoint
- `platform/src/components/chat/PredictionLogModal.tsx`
- `platform/supabase/migrations/056_predictions.sql` — schema:
  ```sql
  CREATE TABLE predictions (id UUID PK, query_id UUID FK, conversation_id UUID FK, prediction_text TEXT, confidence NUMERIC, horizon TEXT, falsifier TEXT, logged_at TIMESTAMPTZ, outcome TEXT NULL, outcome_observed_at TIMESTAMPTZ NULL);
  ```

**Implementation steps**:
1. Detector emits `prediction_candidate` data part per detected sentence.
2. UI surfaces inline "📋 Log as prediction" button on detected sentences (end-of-message review modal per PLAN §12).
3. Modal pre-fills fields; user reviews + submits.
4. Writer records with `outcome=NULL` (sacrosanct per Learning Layer rule #4).

**Tests added**: ~8 unit + ~3 E2E.

**Commit**: `feat(chat-v2/γ3): prediction logging affordance (PPL chat surface)`

**Exit criteria**: Detector fires on test corpus; modal end-to-end works; rows land in `predictions`.

### γ4 — Validator failure surface

**Goal**: Hard-fail renders inline red band; soft-fail renders footer chip. Both link to detail drawer.

**Files to create**:
- `platform/src/components/chat/ValidatorFailureBand.tsx`
- `platform/src/components/chat/ValidatorFooterChip.tsx`

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — wire based on `citation_gate` data part from β10

**Implementation steps**:
1. β10's data parts drive rendering.
2. Super-admin tier shows full validator output in detail drawer (β6).
3. Lower tiers see summary chip only.

**Tests added**: ~3 E2E + ~2 component tests + 2 visual baselines.

**Commit**: `feat(chat-v2/γ4): validator failure surface`

**Exit criteria**: Hard-fail visible; soft-fail visible; super-admin detail works.

### γ5 — Observability deep-link

**Goal**: "View trace" link in details drawer opens `/observatory/trace/[query_id]` in new tab.

**Files to touch**:
- `platform/src/components/chat/PerMessageDetailsDrawer.tsx` (from β6) — add link

**Implementation steps**:
1. Use `query_id` from `observability` data part (α3).
2. Link target: existing Observatory route.

**Tests added**: ~1 E2E.

**Commit**: `feat(chat-v2/γ5): observability deep-link from message details`

**Exit criteria**: Link opens trace view with correct query_id.

### γ6 — Per-message cost visibility

**Goal**: Cost figure ($X, N tokens, Ms, model) in details drawer. Super-admin always; flag-gated for others.

**Files to touch**:
- `platform/src/components/chat/PerMessageDetailsDrawer.tsx` — add cost block
- `platform/src/lib/config/feature_flags.ts` — add `MARSYS_FLAG_COST_VISIBILITY_FOR_USERS` (default `false`)

**Implementation steps**:
1. Data source: `cost` data part from α3 + tier check.

**Tests added**: ~2 E2E.

**Commit**: `feat(chat-v2/γ6): per-message cost visibility`

**Exit criteria**: Super-admin sees cost; flag-gated for others.

### γ7 — Stream resume after disconnect

**Goal**: Persist partial output server-side; resume endpoint streams suffix on reconnect.

**Files to create**:
- `platform/supabase/migrations/057_pending_streams.sql` — schema:
  ```sql
  CREATE TABLE pending_streams (query_id UUID PK, conversation_id UUID FK, accumulated_text TEXT, last_event_seq BIGINT, expires_at TIMESTAMPTZ);
  CREATE INDEX ON pending_streams (expires_at);
  ```
- `platform/src/app/api/chat/consume/resume/route.ts` — GET endpoint
- `platform/src/lib/persistence/pending_streams_writer.ts` — debounced 100ms

**Files to touch**:
- `platform/src/app/api/chat/consume/route.ts` — write to pending_streams on every data part + text chunk (debounced)
- `platform/src/components/consume/ConsumeChatV2.tsx` — detect abrupt disconnect; store `query_id + last_event_seq` in sessionStorage; on reconnect call resume endpoint

**Implementation steps**:
1. Migration 057.
2. Debounced writer.
3. Resume endpoint returns suffix as UIMessage stream.
4. Client reconciliation via assistant-ui's persistence integration.

**Tests added**: ~6 chaos/streaming tests covering clean/dirty/partition disconnect.

**Commit**: `feat(chat-v2/γ7): stream resume after disconnect`

**Exit criteria**: Kill tab mid-stream; reload; conversation resumes at correct position.

### γ8 — Accessibility

**Goal**: WCAG 2.1 AA compliance. Programmatic axe-core green + manual screen-reader passes documented.

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — `aria-live="polite"` on streaming region, `role="log"` on thread, focus management
- `platform/src/components/chat/*.tsx` — keyboard navigation (Tab cycling, ↑↓ in message list, Enter/Esc for drawers)

**Implementation steps**:
1. Add aria attributes per PLAN §9.2.7.
2. Implement focus management.
3. Verify with axe-core (programmatic).
4. Manual screen-reader passes: NVDA + VoiceOver desktop + VoiceOver iOS. Document at `00_ARCHITECTURE/CHAT_V2_A11Y_REPORT.md`.

**Tests added**: ~8 a11y E2E tests covering keyboard nav + axe assertions.

**Commit**: `feat(chat-v2/γ8): accessibility — WCAG 2.1 AA compliance`

**Exit criteria**: Programmatic axe-core green (PR-blocking). Manual screen-reader report documented. Note: manual screen-reader passes against real assistive tech may require **§M manual intervention** if NVDA/VoiceOver hardware isn't available in the dev environment — flag this in the progress tracker.

### γ9 — Mobile responsive

**Goal**: Layout works at 375px and 768px. Touch targets, keyboard, viewport stability.

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — responsive breakpoints
- `platform/src/components/chat/*.tsx` — bottom-sheet citation panel <768px, slide-out sidebar <768px, reasoning collapse default <768px

**Implementation steps**:
1. Tailwind responsive classes throughout.
2. iOS keyboard handling: viewport-fit + correct meta tag; no input-zoom (font-size ≥16px on inputs).
3. Touch targets ≥44px.
4. Playwright mobile profiles cover all behavioral parity scenarios.

**Tests added**: ~15 mobile E2E (re-running parity tests at 375px and 768px) + 4 mobile visual baselines.

**Commit**: `feat(chat-v2/γ9): mobile responsive layout`

**Exit criteria**: All mobile Playwright tests green at 375px and 768px.

### γ10 — Adapter / streamBuildRaw consolidation

**Goal**: Route synthesis through `streamAdapter` instead of `streamBuildRaw`. Delete dead paths.

**Files to touch**:
- `platform/src/lib/synthesis/single_model_strategy.ts` — replace `streamBuildRaw` call with `streamAdapter`-equivalent that returns a `StreamTextResult`-compatible shape
- `platform/src/lib/adapters/build_bridge.ts` — DELETE
- `platform/src/lib/adapters/legacy_runAdapter.ts` — DELETE (flag was retired in earlier PIV)

**Implementation steps**:
1. Add a streamAdapter variant that returns `StreamTextResult` shape so `result.toUIMessageStreamResponse(...)` works at the route.
2. Update synthesis to use the new variant.
3. Delete `build_bridge.ts` and `legacy_runAdapter.ts`.
4. Verify `streamAdapter` now serves both the trace SSE channel AND the chat stream.

**Tests added**: ~3 integration tests verifying single streaming path.

**Commit**: `refactor(chat-v2/γ10): consolidate adapter — delete streamBuildRaw + legacy_runAdapter`

**Exit criteria**: `grep -r "streamBuildRaw\|legacy_runAdapter" platform/src` returns zero. All integration tests green. Single source of streaming truth.

### Phase γ exit

Run Phase γ gate from PLAN §9.9. Verify all cumulative test counts. Verify all master-gate criteria green.

Commit: `milestone(chat-v2/γ): phase gamma complete — domain & polish`

STOP for native review.

## §PM — Pre-merge (3 work items)

### PM1 — Red-team pass

**Goal**: 5-probe red-team per `MACRO_PLAN_v2_0.md §IS.8(b)`. All probes must PASS.

**Files to create**:
- `00_ARCHITECTURE/CHAT_V2_RED_TEAM_v1_0.md` — red-team plan with 5 probes

**Probes**:
1. **P.1 Prompt injection in user input** — adversarial user message attempting to override system prompt.
2. **P.2 Prompt injection in PDF text** — adversarial extracted PDF content.
3. **P.3 Mid-stream provider 429 with retry-after** — verify graceful retry then fallback.
4. **P.4 Auth bypass on conversation routes** — anonymous + cross-user access attempts.
5. **P.5 Stream resume token forgery** — request resume with another user's query_id.

**Implementation steps**:
1. Author red-team plan.
2. Execute each probe — document in plan.
3. All 5 must PASS. If any FAIL, halt, file remediation work item, STOP.

**Tests added**: 5 chaos/security tests corresponding to the probes.

**Commit**: `chore(chat-v2/PM1): red-team pass — 5/5 PROBES PASS`

**Exit criteria**: 5/5 PASS documented.

### PM2 — Master gate evidence pack

**Goal**: Assemble evidence pack mapping each §10 master-gate criterion to passing test artifacts.

**Files to create**:
- `00_ARCHITECTURE/CHAT_V2_MASTER_GATE_EVIDENCE_v1_0.md` — for each of §10 #1-#28, list passing test file + commit SHA + observed metric value

**Implementation steps**:
1. For every criterion in PLAN §10, identify the test(s) and metrics that discharge it.
2. Run the full CI pipeline against the merge candidate.
3. Document all green results.
4. If any criterion cannot be discharged, emit `MASTER_GATE_GAP` block listing gaps — STOP for §M manual intervention.

**Tests added**: None (this is verification).

**Commit**: `chore(chat-v2/PM2): master gate evidence pack`

**Exit criteria**: All 28 §10 criteria discharged with cited evidence; OR `MASTER_GATE_GAP` block emitted and STOP.

### PM3 — Sealing artifact

**Goal**: Author `CHAT_V2_CLOSE_v1_0.md` — the sealing artifact that closes the workstream.

**Files to create**:
- `00_ARCHITECTURE/CHAT_V2_CLOSE_v1_0.md` — close-checklist per `SESSION_CLOSE_TEMPLATE_v1_0.md` schema, plus workstream summary

**Implementation steps**:
1. Summarize: workstream duration, sessions consumed, commit count, line counts added/removed, test counts.
2. Reference the master gate evidence pack.
3. List items deferred to v2 (per PLAN §15).
4. Sign with `closed_by: pending_native_signoff`.

**Commit**: `docs(chat-v2/PM3): sealing artifact drafted — awaits native signoff`

**Exit criteria**: Sealing artifact drafted. STOP for §M manual intervention (native signoff + merge).

## §M — Manual intervention checklist (deferred to end of execution)

These items require the native or human operator. Executor does NOT attempt them. At the end of PM3, the executor STOPS and surfaces this list.

1. **Provision GCS buckets**: `marsys-chat-uploads-{env}` in production project; lifecycle rule (30d auto-delete). Run `gcloud storage buckets create gs://marsys-chat-uploads-prod --location=asia-south1` etc.
2. **Record provider fixtures**: With dev API keys and budget caps (<$20 total), record real provider responses for each scenario listed in `platform/tests/fixtures/chat-v2/providers/*`. Replace TODO-marked placeholder fixtures.
3. **Apply database migrations**: 055_conversations.sql, 056_predictions.sql, 057_pending_streams.sql, and any others created during execution. Apply to staging first, verify, then production.
4. **Provision Cloud Scheduler job**: `pending-streams-reaper` — every 5 min runs `DELETE FROM pending_streams WHERE expires_at < now()`.
5. **Provision Cloud Scheduler job**: `chat-v2-synthetic-monitor` — every 5 min hits `/api/chat/consume` with a known short-prompt fixture; alerts to Slack on failure.
6. **Run Lighthouse CI against staging dogfood**: verify Web Vitals budgets met against real provider latency.
7. **Run k6 load tests against staging**: 100/500/200 concurrent scenarios.
8. **Manual screen-reader testing**: NVDA + Firefox (Windows), VoiceOver + Safari (macOS), VoiceOver + Safari (iOS).
9. **Physical-device mobile spot-check**: iPhone Safari + Android Chrome.
10. **Provider drift sanity check**: run weekly provider-drift CI once against live providers with budget cap.
11. **Native acceptance walkthrough**: against §10 master-gate criteria. Record in a session note at `00_ARCHITECTURE/CHAT_V2_PREMERGE_S1_log.md`.
12. **Sign sealing artifact**: native updates `CHAT_V2_CLOSE_v1_0.md` with `closed_by: <native>` and `closed_at: <ISO>`.
13. **Create PR**: from `feature/chat-v2-bigbang` to `main` with `--no-ff`. PR body references PLAN + EVIDENCE + CLOSE artifacts.
14. **Merge PR**: after CI green + final native review.
15. **Post-merge: flip `MARSYS_FLAG_CHAT_V2_ENABLED`** to `true` in `deploy.yml` (NOT in `feature_flags.ts`). Watch production for 7 days.
16. **Post-7-days clean**: flip `feature_flags.ts` default to `true` and remove the flag entirely (Phase 11B pattern). Delete `ConsumeChatLegacy.tsx`.
17. **Post-merge: update CLAUDE.md §E** to add the workstream to concurrent workstreams (or mark CLOSED).

## §F — Frontmatter advancement rules

When you complete a work item:
1. Update `current_work_item` to the next ID in the §P/§A/§B/§G/§PM sequence.
2. Increment `completed_work_items`.
3. If you just completed the LAST item in a phase:
   - Update `current_phase` to the next phase.
   - Run that phase's exit gate; commit `milestone(...)`.
   - Update `current_work_item` to the FIRST item of the next phase.
4. If you completed PM3, update `status: COMPLETE` and STOP.

Sequence reference:
```
PA1 → α0 → α1 → α2 → α3 → α4 → α5 → α6 → α7 → (phase α exit gate)
β1 → β2 → β3 → β4 → β5 → β6 → β7 → β8 → β9 → β10 → (phase β exit gate)
γ1 → γ2 → γ3 → γ4 → γ5 → γ6 → γ7 → γ8 → γ9 → γ10 → (phase γ exit gate)
PM1 → PM2 → PM3 → (workstream complete; §M manual intervention)
```

## §X — Out-of-scope reminders

During execution, you may notice opportunities for improvements outside this brief's scope. DO NOT pursue them. Common temptations to resist:

- Refactoring code that the brief doesn't touch (even if "obviously" better).
- Adding new features beyond PLAN §3 IN-scope.
- Modifying files in `must_not_touch` zones (M-series macro-phase paths: L2.5 corpus, learning layer, anything under `06_LEARNING_LAYER/`, `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`).
- Cleaning up unrelated tech debt.
- Upgrading dependencies beyond what work items require.

If you find a real bug outside scope that's hurting your work-item implementation, document it in `CHAT_V2_PROGRESS.md` under a `SCOPE_ADJACENT` block and skip it. Native triages.

---

*End master executor brief. Authored 2026-05-16. v1.0 TEMPLATE. Copied to worktree root as CLAUDECODE_BRIEF.md at branch-cut. Live worktree copy advances frontmatter as work progresses.*
