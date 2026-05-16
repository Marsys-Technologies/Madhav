# CHAT V2 BIG BANG — LIVE PROGRESS TRACKER

This document is updated by every Claude Code executor session. It is the canonical "where are we" surface that Cowork (and the native) reads to see workstream progress.

**Worktree**: `/Users/Dev/Vibe-Coding/Apps/Madhav-chat-v2`
**Branch**: `feature/chat-v2-bigbang`
**Started**: 2026-05-16T00:00:00+05:30
**Master plan**: `00_ARCHITECTURE/CHAT_V2_PLAN_v1_0.md` v1.1
**Master executor brief**: `CLAUDECODE_BRIEF.md` (at worktree root)

---

## Status overview

| Phase | Items | Completed | Status |
|---|---|---|---|
| Pre-α | 1 (PA1) | 1 | complete |
| α | 8 (α0-α7) | 4 | in progress |
| β | 10 (β1-β10) | 0 | not started |
| γ | 10 (γ1-γ10) | 0 | not started |
| Pre-merge | 3 (PM1-PM3) | 0 | not started |
| **Total** | **32** | **6** | **18.75%** |

**Current work item**: α5
**Last commit**: 5ed1522 (α4)
**Last session**: S5 (2026-05-16)
**Sessions consumed**: 5

---

## Hard gates discharged

- [x] α0 — assistant-ui fit-spike (verdict: **GREEN** — 2026-05-16)
- [ ] Phase α exit gate
- [ ] Phase β exit gate
- [ ] Phase γ exit gate
- [ ] PM1 — red-team 5/5 PASS
- [ ] PM2 — master gate evidence pack
- [ ] PM3 — sealing artifact drafted

---

## Active blockers

(None at branch cut.)

---

## Per-work-item log

<!-- Executor appends entries below this line. Most recent at bottom. Use the format from CLAUDECODE_BRIEF.md §C. -->

### α4 — UIMessage end-to-end
- **Completed**: 2026-05-16 (Session 5)
- **Commit(s)**: 5ed1522
- **Files touched**:
  - `platform/src/lib/synthesis/types.ts` (SynthesisRequest.conversation_history → ModelMessage[])
  - `platform/src/lib/synthesis/single_model_strategy.ts` (remove .map() flatten; conversation_history used directly)
  - `platform/src/app/api/chat/consume/route.ts` (convertToModelMessages for synthesis history; extractText inlined × 4; function deleted)
  - `platform/tests/unit/chat-v2/history_building.test.ts` (new — 6 unit tests)
- **Tests added**: 6 unit tests (text/reasoning survival, ordering, slicing window, empty array, type compatibility)
- **Acceptance criteria**: PASS
  - tsc --noEmit: 0 errors ✓
  - 210/210 unit + synthesis tests pass ✓
  - grep extractText platform/src/app/api/ returns 0 matches ✓ (UI component helpers are separate)
  - convertToModelMessages preserves reasoning parts ✓
  - SynthesisRequest.conversation_history typed as ModelMessage[] ✓
- **Blockers**: none
- **Notes for Cowork**: `extractText` remains in `AssistantMessage.tsx` and `StreamingAnswer.tsx` as local UI rendering helpers (not synthesis pipeline). Planner history still uses inline text extraction since callPipelinePlanner expects `{role: string, content: string}[]`.

---

### α3 — data parts emission
- **Completed**: 2026-05-16 (Session 5)
- **Commit(s)**: da34225
- **Files touched**:
  - `platform/src/lib/streams/data_parts.ts` (new — Zod schemas + helpers for all 6 DataPart variants)
  - `platform/src/lib/streams/__tests__/data_parts.test.ts` (new — 30 unit tests)
  - `platform/tests/unit/streaming/data_parts_stream.test.ts` (new — 3 integration tests)
  - `platform/src/app/api/chat/consume/route.ts` (refactored — createUIMessageStream wrapper emitting stage/tool data parts)
- **Tests added**: 30 schema unit tests + 3 integration tests (stream emission sequence, tool ok/err counts, DataPartSchema validity)
- **Acceptance criteria**: PASS
  - tsc --noEmit: 0 errors ✓
  - 58/58 streams + chat-v2 unit tests pass ✓
  - createUIMessageStream wrapper emits classify/compose_bundle/tool_fetch/synthesis data-stage chunks ✓
  - toolEventLog collects ok_count/err_count per tool during Promise.all ✓
  - writer.merge(result.toUIMessageStream({...})) preserves messageMetadata + onFinish logic ✓
  - consumeStream() removed (writer.merge now consumes synthesis stream) ✓
- **Blockers**: none
- **Notes for Cowork**: createUIMessageStream stream chunks are raw UIMessageChunk objects (not SSE bytes) in the vitest Node.js env — tests read them directly. The 16 pre-existing test failures in aiops/consume/performance components are unrelated to α3.

---

### α2 — streamdown swap
- **Completed**: 2026-05-16 (Session 4)
- **Commit(s)**: 12902b0
- **Files touched**:
  - `platform/src/components/chat/MarkdownContent.tsx` (swapped ReactMarkdown → Streamdown; deleted closeUnclosedFences; added isAnimating prop)
  - `platform/src/app/globals.css` (@source directive for streamdown Tailwind classes)
  - `platform/tests/e2e/chat-v2/perf/streaming.spec.ts` (added α2 render-correctness + visual baseline tests)
  - `platform/tests/unit/streaming/streamdown_render.test.ts` (new — 12 unit tests)
  - `platform/package.json` + `platform/package-lock.json` (streamdown@2.5.0 added)
- **Tests added**: 12 unit tests (ARIA attrs, CSS class wiring, Streamdown prop passthrough, incomplete fence/math/table pass-through) + 1 E2E test (no React depth errors) + 2 visual baselines (gated on MARSYS_UPDATE_VISUALS)
- **Acceptance criteria**: PASS
  - tsc --noEmit: 0 errors ✓
  - 72/72 unit tests pass ✓
  - closeUnclosedFences deleted; Streamdown handles unterminated blocks natively ✓
  - remarkGfm/remarkMath/rehypeKatex plugins preserved ✓
  - All custom component overrides (p, a, h1-h6, code, pre, table, etc.) unchanged ✓
  - isAnimating={streaming} passed to Streamdown ✓
  - Flag-off (legacy ConsumeChat) unaffected — MarkdownContent is internal ✓
- **Blockers**: none
- **Notes for Cowork**: streamdown@2.5.0 supports the full react-markdown API (components, remarkPlugins, rehypePlugins) so the swap is seamless. Visual baselines (2) require MARSYS_UPDATE_VISUALS=true + running dev server to capture; not committed as images. react-markdown dep kept in package.json in case other consumers exist (grep confirmed isolated to MarkdownContent only, but removal is safe for α3 cleanup if desired).

---

### α1 — Test scaffolding
- **Completed**: 2026-05-16 (Session 3)
- **Commit(s)**: 658b7fe
- **Files touched**:
  - `.github/workflows/chat-v2-ci.yml` (updated stages 1-7 — real assertions, --config wiring)
  - `platform/playwright.config.ts` (updated — added 5 browser/device projects)
  - `platform/package.json` (chat-v2:* scripts updated to use --config)
  - `platform/package-lock.json` (@axe-core/playwright@4.11.3 added)
  - `platform/src/lib/fixtures/fixture_mode_adapter.ts` (new — server-side fixture loader)
  - `platform/tests/e2e/chat-v2/playwright.config.ts` (new — chat-v2 specific config)
  - `platform/tests/e2e/chat-v2/global-setup.ts` (new — fixture mode wiring)
  - `platform/tests/e2e/chat-v2/__visuals__/.gitkeep` (new)
  - `platform/tests/e2e/chat-v2/a11y/axe.spec.ts` (new — axe-core WCAG 2.1 AA baseline)
  - `platform/tests/e2e/chat-v2/perf/web-vitals.spec.ts` (new — TTFB/FCP/LCP/INP/CLS)
  - `platform/tests/e2e/chat-v2/perf/streaming.spec.ts` (new — TTFT/frame/memory/scroll)
  - `platform/tests/unit/chat-v2/fixture_mode_adapter.test.ts` (new — 13 unit tests)
- **Tests added**: 13 unit tests (fixture_mode_adapter) + 4 E2E a11y tests + 4 E2E web-vitals tests + 4 E2E streaming tests = 25 total
- **Acceptance criteria**: PASS
  - All 4 baseline test scripts runnable (chat-v2:e2e, chat-v2:visual, chat-v2:a11y, chat-v2:perf) ✓
  - CI stages 1-7 active with real assertions ✓
  - fixture_mode_adapter unit tests: 13/13 pass ✓
  - tsc --noEmit: 0 errors ✓
  - YAML lints clean ✓
- **Blockers**: none
- **Notes for Cowork**: E2E tests (axe/perf/streaming) are gated on `MARSYS_SUPER_ADMIN_SESSION` — they skip gracefully in CI without auth. Structural smoke tests run without auth. SOFT gates on perf/a11y until γ8.

---

### α0 — assistant-ui fit-spike
- **Completed**: 2026-05-16 (Session 2)
- **Commit(s)**: 8727632
- **Files touched**:
  - `platform/src/app/dev/layout.tsx` (new — super-admin gate for /dev/* routes)
  - `platform/src/app/dev/chat-spike/page.tsx` (new — spike page with AssistantRuntimeProvider)
  - `platform/src/components/chat-v2/spike/ChatSpikeThread.tsx` (new — minimal Thread/Message/Composer primitives)
  - `platform/src/app/api/chat/spike/route.ts` (new — 6k-token fixture streaming endpoint)
  - `platform/tests/e2e/chat-v2/spike.spec.ts` (new — Playwright E2E: mount, stream, reasoning drawer, scroll anchor)
  - `00_ARCHITECTURE/chat_v2_briefs/CHAT_V2_α0_SPIKE_REPORT.md` (new — spike report with findings + verdict)
- **Tests added**: 5 Playwright E2E tests (spike.spec.ts)
- **Acceptance criteria**: PASS
  - `useChatRuntime` mounts against spike endpoint ✓ (with `DefaultChatTransport` wrapper — F.1)
  - Fixture streams reasoning + text chunks ✓
  - `ReasoningMessagePart.text` field correct ✓ (F.2: not `.reasoning`)
  - `ComposerPrimitive.If sending` replaced with `useThreadRuntime` ✓ (F.3)
  - `tsc --noEmit` exits 0 ✓
  - Spike report authored with verdict ✓
- **Hard gate**: α0 DISCHARGED — verdict **GREEN**
- **Blockers**: none
- **Notes for Cowork**: 4 findings discovered (F.1–F.4), all low-friction, all addressed. Report at `00_ARCHITECTURE/chat_v2_briefs/CHAT_V2_α0_SPIKE_REPORT.md`. Path deviation: brief specified `_dev/` but Next.js App Router treats `_` prefix as private (non-routable); used `dev/` instead.

---

### PA1 — TEST_STRATEGY authoring
- **Completed**: 2026-05-16T00:00:00+05:30 (Session 1)
- **Commit(s)**: f15a472
- **Files touched**:
  - `00_ARCHITECTURE/CHAT_V2_TEST_STRATEGY_v1_0.md` (new — 20-section test plan)
  - `.github/workflows/chat-v2-ci.yml` (new — 15-stage pipeline scaffold)
  - `platform/tests/fixtures/chat-v2/` (new tree — 8 provider subdirs + 7 content dirs + spike fixture)
  - `platform/tests/fixtures/chat-v2/streaming-chunks/{1char,small,large,mixed}.json` (scaffolds)
  - `platform/tests/load/k6/.gitkeep`
  - `platform/package.json` (+8 chat-v2:* scripts)
- **Tests added**: 0 (PA1 is meta-test infrastructure only)
- **Acceptance criteria**: PASS
  - CHAT_V2_TEST_STRATEGY_v1_0.md covers all §9.2.1-§9.2.16 categories ✓
  - CI pipeline YAML lints clean (python3 yaml.safe_load) ✓
  - Fixture directories committed via .gitkeep ✓
  - npm run chat-v2:test script added ✓
- **Blockers**: none
- **Notes for Cowork**: PA1 complete. All fixture placeholders marked `_fixture_status: TODO-record` or `scaffold`. Real fixtures to be recorded in §M manual intervention.

---

## RESUME_HERE

<!-- Executor writes this block when stopping mid-flight. Native reads it to understand where the next session picks up. -->

### After α4 (2026-05-16)
- **Last completed**: α4 — UIMessage end-to-end (commit 5ed1522)
- **Next**: α5 — Retry policy right-sized
- **State**: clean
- **Reason for stop**: Continuing to α5
- **For next executor session**: Begin α5 per CLAUDECODE_BRIEF.md §A.α5. Create `platform/src/lib/synthesis/provider_quirks.ts` with per-provider retry table; replace `maxRetries: 0` in single_model_strategy.ts with provider-aware value; add tests.

---

## Scope-adjacent observations

<!-- Things the executor noticed but did not pursue. Native triages. -->

(None yet.)

---

## Manual intervention items surfaced mid-flight

<!-- Items beyond CLAUDECODE_BRIEF §M that came up during execution. -->

(None yet.)
