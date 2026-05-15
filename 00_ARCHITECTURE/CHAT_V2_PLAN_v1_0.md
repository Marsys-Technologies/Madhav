---
name: CHAT V2 BIG BANG — MASTER PLAN
canonical_id: CHAT_V2_PLAN
version: 1.1
status: DRAFT
author: Claude (Cowork planning session 2026-05-16)
created: 2026-05-16
amended: 2026-05-16 (v1.1 — comprehensive test strategy per native request)
ratification: pending native
supersedes: none
governance_classification: concurrent named workstream (parallel to M-series, per Phase O Observatory / Portal Redesign precedent)
mirror_pair: none (Claude-only governance surface at v1.0; revisit if Gemini takes ownership of any phase)
---

# CHAT V2 BIG BANG — MASTER PLAN

## §1 Mission

Deliver a single coherent rebuild of the MARSYS-JIS chat interface to best-in-class chat UX standards — parity with Claude / ChatGPT / Gemini on streaming, reasoning, tool/stage progress, message editing, conversation persistence, multi-modal input, mobile, accessibility, and stream resume — *plus* the MARSYS-specific surfaces that no commodity chat product offers (panel-mode display, validator-failure UX, prediction-logging affordance, observability deep-link, per-message cost visibility, disclosure tier reveal).

Executed as a **big-bang workstream**: one design, one branch, one master feature flag, three internal dogfood checkpoints, one merge to main when the master gate passes. No incremental ship to users mid-flight.

Bounded by `MACRO_PLAN_v2_0.md §Ethical Framework`: the chat surface remains a probabilistic, calibrated, auditable instrument with disclosure tiers — UX upgrades do not loosen any ethical commitment.

## §2 Workstream classification & governance

Per CLAUDE.md §E and the Phase O Observatory + Portal Redesign precedents, this is a **concurrent named workstream**, not a macro-phase. Properties:

- Runs in parallel to the M-series (currently M5-A active).
- Owns its own SESSION_LOG entries (`CHAT_V2_α_S1`, `CHAT_V2_β_S1`, etc.) per `CONVERSATION_NAMING_CONVENTION_v1_0.md §4`.
- Adds an entry to CLAUDE.md §E (Concurrent workstreams) on native ratification of this plan.
- Does NOT consume M-series red-team cadence; runs its own pre-merge red-team pass per `MACRO_PLAN_v2_0.md §IS.8` cadence (b) — "every macro-phase close before the SESSION_LOG seal" — applied to the chat-v2 merge.
- Closes via a sealing artifact (`CHAT_V2_CLOSE_v1_0.md`) at merge time.
- Does NOT introduce a new mirror pair at v1.0. If Gemini takes ownership of any phase, declare MP.10 at that time per `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md §K`.

**File-scope isolation from active M-series work.** This workstream touches:

- `platform/src/components/consume/**`
- `platform/src/components/chat/**`
- `platform/src/app/api/chat/consume/**`
- `platform/src/lib/adapters/**`
- `platform/src/lib/synthesis/**`
- `platform/src/lib/hooks/**`
- `platform/src/hooks/**`
- `platform/src/lib/consume/**`
- `platform/src/lib/config/feature_flags.ts` (additions only — no flag removals on this branch)
- `platform/supabase/migrations/**` (new migrations only — no edits to existing)
- `platform/package.json` + `package-lock.json`
- `platform/src/lib/citations/**` (new)
- `platform/src/lib/streams/**` (new)
- `platform/src/lib/persistence/**` (new for conversation persistence + resume)
- `platform/src/lib/ppl/**` (new for prediction logging affordance hooks)

M5-A active scope (L2.5 reconciliation, LL.8 + LL.9 scaffold, etc.) does **not** touch any of the above paths. Conflict surface should be near-zero with weekly rebase from main.

## §3 Scope

### §3.1 IN scope

- **Streaming render layer.** Incremental markdown rendering (streamdown), reasoning drawer, tool-call cards, stage stepper, elapsed-time indicator, code block copy/highlight, KaTeX math, inline citations.
- **Behavioral parity with best-in-class chat.** Edit-and-regenerate, message branching, conversation persistence with read-after-write + conversation list, mid-stream interrupt with defined semantics, multi-modal input (image + PDF), per-message metadata reveal, stream resume after disconnect, mobile responsive, accessibility (`aria-live`, keyboard nav, focus management).
- **MARSYS-specific UX.** Panel-mode display semantics, long-reasoning UX with token-count and elapsed-time progress, prediction-logging affordance, validator-failure surface placement, observability deep-link from each assistant message, per-message cost visibility (super-admin tier).
- **Backend protocol completion.** Stage / tool / reasoning data parts emitted via `writer.writeData(...)` from the route; UIMessage preservation end-to-end via `convertToModelMessages` (no string flattening); abort propagation through tool fetches + panel + adapter inner loops; right-sized retry policy; sliding-window history summarization; citation gate enforcement at a wire-effective point.
- **Architectural consolidation.** Resolve the `streamAdapter` / `streamBuildRaw` split: route synthesis through the unified adapter so abort + event channel + provider quirks live in one place.
- **Test scaffolding.** Playwright + token-trace fixtures + visual regression for the streaming UI; perf budgets; accessibility audit harness; mobile viewport tests.
- **Feature-flag reconciliation.** Reconcile dev / prod default drift across `feature_flags.ts`, `.env.local`, `deploy.yml`.
- **Governance.** SESSION_LOG entries per session; pre-merge red-team; sealing artifact at close.

### §3.2 OUT of scope (for v1; tracked for v2)

- Voice input/output (Whisper / TTS provider integration). Deferred to CHAT_V3 if/when warranted.
- Real-time collaborative chat (multi-user shared session). Not a current MARSYS use case.
- Custom model fine-tuning. Out of remit — sits in MACRO_PLAN M6/M7 territory.
- Cross-native query mode UI changes beyond what already exists. Cross-native is a corpus + retrieval concern; chat surface inherits whatever the bundle delivers.
- New synthesis prompts or new evaluation cadence. Lives in M5/M9/L workstreams.
- Changes to the L2.5 ↔ L1 derivation ledger or B.10 discipline. Substrate-level; not chat-interface concerns.
- Server-side rendering / streaming SSR. Not pursued at v1 (would interact poorly with assistant-ui's client-state model).

## §4 Architecture decisions

### §4.1 SDK stack (unchanged — best-in-class)

- **`ai@^6.0.168`** + `@ai-sdk/react@^3.0.170`. Confirmed best-in-class multi-provider TS chat SDK. Stays.
- Provider packages: `@ai-sdk/anthropic`, `@ai-sdk/google`, `@ai-sdk/openai`, `@ai-sdk/deepseek` — stay. NIM custom adapter — stays.
- Server-client wire protocol: `result.toUIMessageStreamResponse(...)` ↔ `useChat`. Correct shape. No swap.

### §4.2 UI primitives — **adopt assistant-ui**

Rationale: AI-SDK-team-built, year-plus iteration on streaming chat edge cases (scroll anchoring under back-pressure, message branching, reasoning incremental rendering, message editing, regenerate, copy/branch/edit UI affordances). Re-skinned with MARSYS visual system (Modern Dark Pro reskin already in main per commit `a837a99`) and our domain components (`CitationChip`, `DisclosureTierBadge`, `ValidatorFailureView`, methodology expander). Avoids re-deriving solutions to known-hard problems and reduces long-term maintenance surface. Spike α0 verifies fit before commitment.

### §4.3 Markdown rendering — **streamdown**

`react-markdown@^10` is full-AST re-parse per render → O(N²) on streaming output. Swap to `streamdown` (Vercel AI team, purpose-built for streaming LLM markdown). Preserves remark/rehype plugin ecosystem (gfm, math, katex). Single biggest "feels-broken" lever.

### §4.4 Custom data parts for stage / tool / reasoning

The pipeline already emits stage transitions (`classify` → `compose_bundle` → `plan_per_tool` → `tool_fetch` → `synthesis` → `audit`) to `query_trace_steps` for observability. Mirror those writes into the AI SDK data stream via `dataStream.writeData({...})`. `useChat` delivers them in `message.parts[]`. assistant-ui composers render them. Reasoning parts (`type: 'reasoning'`) flow natively from `streamText` for thinking models.

### §4.5 UIMessage preserved end-to-end

Remove all string-flattening at the synthesis boundary (`single_model_strategy.ts:305-309`, `route.ts:987-988`). Use `convertToModelMessages(uiMessages)` at the exact LLM-call boundary; everywhere else holds `UIMessage[]`. Multi-modal parts, reasoning parts, tool-call parts all survive end to end.

### §4.6 Master feature flag

**`MARSYS_FLAG_CHAT_V2_ENABLED`** (default `false`). All v2 chat surface rendering, route logic, data-part emission, and assistant-ui mounting gates on this flag. Flag-OFF returns to current production chat (post-PIV state at `a7d4baf`). Flip date is the merge date. After 7 days of in-production verification, flag is removed and the legacy path deleted (mirrors the AIOps Phase 11B pattern).

### §4.7 Single feature branch

**`feature/chat-v2-bigbang`** off main at branch-cut. Weekly `git pull --rebase origin main` cadence. No partial merges to main. Internal dogfood deploys via per-revision Cloud Run tags so the team can test the in-progress branch behind the flag without disturbing production traffic.

### §4.8 Conversation persistence model

Adopt **write-through with confirmation** + a conversation list endpoint. On message-finish, the route writes the new turn to `conversations` + `conversation_messages` tables and acknowledges the write back into the data stream (`writer.writeData({type: 'persistence', status: 'ok', conversation_id})`). Client only marks the conversation as "saved" after receiving the ack. On page reload, the client fetches `/api/conversations/[id]/messages` to restore. New schema: see §5.B2.

### §4.9 Stream resume after disconnect

Server-side **partial-output store** (Postgres table `pending_streams` with `query_id`, `accumulated_text`, `last_event_seq`, `expires_at`). On client reconnect, `GET /api/chat/consume/resume?query_id=...&since_seq=...` returns the suffix as a UIMessage stream. assistant-ui handles client-side reconciliation. Aligns with current state-of-the-art (ChatGPT / Claude both implement this).

### §4.10 Sliding-window history summarization

Replace the hard 2-pair truncate (`route.ts:631-638`) with: when conversation tokens exceed budget B (default 32k), summarize all turns older than the most recent K (default 4) into a single system-tagged turn. Summarization runs as a fast Haiku call gated by `MARSYS_FLAG_HISTORY_COMPRESSION_ENABLED` (sub-flag of master). Summarization result cached against conversation_id + tail-position so it's only recomputed when the tail moves past the boundary.

### §4.11 Citation gate enforcement at the wire

Move citation gate from `onFinish` (decorative — admits it cannot enforce, route.ts:882-889) to a **streaming validator pattern**: validator inspects the assembled answer at the SDK's `onChunk` boundary, and on hard-fail injects a `type: 'error'` part into the data stream before `onFinish` fires. Client-side renders an inline warning band. Soft-fail (warnings) injects an `info` part rendered as a footer.

### §4.12 Right-sized retry policy

PIV.QG7.2 set `maxRetries: 0`. Replace with a **bounded retry policy**: `maxRetries: 1` on transient classes only (network timeout, 5xx, rate-limit-with-retry-after); `maxRetries: 0` on hard classes (4xx, auth, bad-request). Route-level fallback fires only after both attempts on the primary model fail. Configured per provider in `provider_quirks.ts`.

### §4.13 Adapter / streamBuildRaw consolidation

Route synthesis (`single_model_strategy.ts:425` currently bypasses the adapter layer) is redirected through `streamAdapter`. The adapter's `QueryRequest` type gains `abortSignal: AbortSignal | undefined`. Provider adapters' `for await` loops check `req.abortSignal?.aborted` on each iteration. Result: single source of truth for provider streaming; `ModelInteractionEvent` channel and chat stream become the same stream.

## §5 Phase α — Foundation (≈ week 1-2)

Exit state: assistant-ui shell mounted behind master flag, real stream of stage/tool/reasoning data parts, UIMessage shape preserved, retry policy right-sized, flag drift reconciled, test scaffolding in place. No new chrome yet beyond what assistant-ui ships out of the box.

### α0 — assistant-ui fit-spike (2 days)

Mount a minimal assistant-ui `Thread` in `platform/src/app/_dev/chat-spike/page.tsx` (super-admin only, no auth changes). Wire to a stub `/api/chat/spike` endpoint that streams a known fixture via `streamText`. Verify: scroll anchoring under load, message-edit UX, branching navigation, reasoning drawer, code block rendering, KaTeX math, copy button, regenerate. Decision gate: green-light assistant-ui or fall back to custom build. Documented at `00_ARCHITECTURE/CHAT_V2_α0_SPIKE_v1_0.md`. **Hard gate** — if assistant-ui fails the spike, plan is paused and re-scoped.

### α1 — Test scaffolding (3 days, runs in parallel with α0)

- Playwright config at `platform/tests/e2e/chat-v2/playwright.config.ts`.
- Token-trace fixtures: deterministic provider responses for streaming, reasoning, tool-call, multi-modal, panel-mode test cases under `platform/tests/fixtures/chat-v2/`.
- Visual regression via Playwright's screenshot diff against committed baselines.
- Perf-budget assertions: TTFB <800ms, FCP <1.5s, message-render <16ms/frame, no `Maximum update depth exceeded` warnings.
- a11y audit via axe-core integrated into Playwright.
- CI job `chat-v2-e2e` added to `.github/workflows/` (initially required only on the `feature/chat-v2-bigbang` branch).

### α2 — streamdown swap (1 day)

Replace `react-markdown` in assistant-message rendering with `streamdown`. Preserve `remark-gfm`, `remark-math`, `rehype-katex`. Delete `closeUnclosedFences` workaround (streamdown handles unterminated fences natively).

### α3 — Data parts emission from route (3 days)

- Define data part schema in `platform/src/lib/streams/data_parts.ts`: `{stage, tool, reasoning, persistence, citation_gate, cost, observability, error, info}`.
- Emit `stage` events at each pipeline transition in `route.ts`.
- Emit `tool` events around each tool fetch in the `Promise.all` loop.
- Emit `cost` event at `onFinish` with token + dollar figures.
- Emit `observability` event with `query_id` for the deep-link.
- Type-safe via Zod schemas; assistant-ui composers consume strongly-typed parts.

### α4 — UIMessage end-to-end (2 days)

- Delete `extractText` flattening (route.ts:987-988).
- Replace planner-history rebuild (route.ts:240-247) with `convertToModelMessages(uiMessages.slice(-N))`.
- Replace synthesis-history rebuild (route.ts:631-638) with same.
- Update `single_model_strategy.ts:305-310` to accept `ModelMessage[]` directly.
- Reasoning parts, multi-modal parts, tool-call parts now flow through unchanged.

### α5 — Retry policy right-sized (1 day)

- Replace `maxRetries: 0` in `single_model_strategy.ts:441` with `maxRetries: providerQuirks[provider].maxRetries`.
- Add `provider_quirks.ts` lookup table.
- Route-level fallback (`route.ts:695-702`) fires after both primary attempts fail.

### α6 — Feature-flag reconciliation (1 day)

- Choose: flip `feature_flags.ts` defaults to match prod, OR add `.env.development` that mirrors `deploy.yml`. Decision documented in `00_ARCHITECTURE/CHAT_V2_FLAG_RECONCILIATION_v1_0.md`.
- Add `MARSYS_FLAG_CHAT_V2_ENABLED` to `feature_flags.ts` (default `false`) and `deploy.yml` (`false` until merge).

### α7 — Master flag wiring (1 day)

`ConsumeChat.tsx` becomes a thin switch: flag-off renders the legacy `ConsumeChatLegacy` (current production); flag-on renders the new `ConsumeChatV2` shell built on assistant-ui. Legacy path remains untouched and shippable until the merge.

### §5.A Acceptance criteria (Phase α gate)

- α0 spike green-lit OR plan paused for re-scope.
- Streaming a 6000-token fixture answer: zero dropped frames in perf timeline; no console warnings.
- Stage / tool / reasoning data parts visible in browser devtools network stream.
- Reasoning parts from a thinking-model fixture surface in assistant-ui's reasoning drawer.
- `extractText` removed from codebase (grep returns zero).
- Retry policy verified via fixture: transient 503 → retried once → succeeds.
- All Phase α Playwright tests pass.
- assistant-ui re-skinned to match Modern Dark Pro tokens; visual regression baseline committed.

## §6 Phase β — Behavioral parity (≈ week 3-4)

Exit state: chat behaves like Claude / ChatGPT for users. Edit, regenerate, persistence, mid-stream interrupt, citations, multi-modal, per-message reveal, abort, summarization, panel honesty, citation gate enforcement.

### β1 — Edit & regenerate (3 days)

assistant-ui's `MessageEdit` + `MessageRegenerate` primitives wired to a `POST /api/chat/consume/regenerate` endpoint that truncates the conversation to the edit point and re-issues the synthesis. Edit history kept as a sibling chain in `conversation_messages` (new column `parent_message_id`).

### β2 — Conversation persistence done right (4 days)

- New tables: `conversations(id, owner_id, title, created_at, updated_at, archived_at)`, `conversation_messages(id, conversation_id, parent_message_id, role, parts_json, metadata_json, created_at)`.
- Migration `055_conversation_v2.sql`.
- New endpoints: `GET /api/conversations` (list), `GET /api/conversations/[id]` (fetch), `POST /api/conversations` (create), `DELETE /api/conversations/[id]` (archive), `GET /api/conversations/[id]/messages` (restore).
- Write-through with ack: route writes turn after `onFinish`, then emits `persistence:ok` data part. Client marks saved only on ack receipt.
- Reload restores via `GET /api/conversations/[id]/messages`.
- Conversation list UI in the left sidebar (assistant-ui `ThreadList` primitive).

### β3 — Mid-stream interrupt semantics (2 days)

Defined behavior: **cancel-and-replace** (ChatGPT model). When user submits while a prior stream is in flight, client calls `chat.stop()` (aborts client fetch + via β7 the server work), server marks the in-flight `query_id` as `cancelled`, persistence writes the partial output if any, and the new query begins. Documented in `platform/src/components/chat/MID_STREAM_BEHAVIOR.md`.

### β4 — Inline numbered citations + side panel (4 days)

- Synthesis prompt emits citations as `[^N]` footnote-style markers with a citation-block at end of answer.
- streamdown's footnote plugin renders inline numbered superscripts.
- Hover → CitationPreview popover (already exists, currently in side panel).
- Click → pins citation in a side panel anchored to the message; multi-citation pin support.
- Citation source data flows via `citation` data parts (one per cited source) and is reconciled with the inline numbering on render.

### β5 — Multi-modal input — image + PDF (4 days)

- Composer accepts file drop / paste / picker for images (JPEG, PNG, WebP, max 20MB) and PDFs (max 50MB).
- Files uploaded to GCS bucket `marsys-chat-uploads-{env}` under `chat/{user_id}/{conversation_id}/{message_id}/`.
- Upload returns a signed-URL token.
- Token attached to UIMessage as a file part; survives end-to-end (depends on α4).
- Synthesis route resolves token → signed URL → passes to provider via AI SDK's multi-modal API.
- PDFs run through Vertex AI Document Understanding (already used elsewhere in MARSYS) → extracted text + per-page images attached.
- Image previews render inline in user message; PDFs render as a file-card with page count and a thumbnail.

### β6 — Per-message metadata reveal (2 days)

assistant-ui's message action menu gains "Show details" → drawer with model, tokens (input + output + reasoning), latency, validators run, disclosure tier, citation count, cost, panel members (if panel), and an observability deep-link (see γ5). Data sourced from `messageMetadata` callback (already populated).

### β7 — Abort propagation completion (2 days)

- `request.signal` passed into `Promise.all` tool-fetch loop (`route.ts:523-571`).
- Passed into `panel_strategy.ts:118` passthrough.
- `QueryRequest` type in `lib/adapters/types.ts` gains `abortSignal: AbortSignal | undefined`.
- Each provider adapter's `for await` checks `req.abortSignal?.aborted` and breaks on abort.
- Cancelled streams persist partial output to `pending_streams` (see γ7) so they're resumable.

### β8 — Sliding-window history summarization (3 days)

Per §4.10. New module `platform/src/lib/synthesis/history_compression.ts`. Cached against `conversation_id + tail_position`. Sub-flag `MARSYS_FLAG_HISTORY_COMPRESSION_ENABLED` for safe rollout.

### β9 — Honest panel streaming (3 days)

Replace `panel_strategy.ts` passthrough-through-Haiku model with: panel members fire in parallel as before; adjudication is itself a `streamText` call against a "adjudicator" prompt, with the panel members' answers in its context; that adjudication stream IS the user-visible stream. Members + adjudicator progress reported as `stage` data parts (`panel:member:1:running` → `panel:member:1:done` → ... → `panel:adjudicator:running`). User sees real progress; final answer streams real tokens.

### β10 — Citation gate at the wire (2 days)

Per §4.11. New `streaming_citation_validator.ts` runs against the SDK's `onChunk` hook (or via a buffered `onFinishStep`). On hard-fail, injects `error` data part; on soft-fail, injects `info` data part. Client renders inline.

### §6.A Acceptance criteria (Phase β gate)

- User can edit any prior user-message and regenerate from that point.
- Reload preserves conversation; conversation list shows all owned conversations.
- Mid-stream submit cancels prior and starts new within 300ms.
- Inline `[1]` `[2]` citations render and pin in side panel on click.
- Image upload + display works; PDF upload + Document Understanding extraction works; both survive a multi-turn conversation.
- Per-message details drawer shows all fields, including a working observability deep-link stub.
- Stop button cancels server within 200ms (verified via `query_trace_steps`).
- Turn 5 of a conversation correctly references information from turn 1 (verified via `answer:eval` harness).
- Panel-mode user sees first stage event within 1s; adjudicator answer streams token-by-token; no Haiku passthrough.
- Citation-gate failure produces a user-visible error band.
- All Phase β Playwright tests pass; visual regression baselines updated.

## §7 Phase γ — Domain & polish (≈ week 5-6)

Exit state: MARSYS-grade. Domain-specific UX complete, accessibility verified, mobile responsive, test suite mature, single source of streaming truth.

### γ1 — Panel mode display UX (3 days)

Panel answer surfaces a top-of-message confidence ribbon. "Show panel dissent" toggle reveals per-member answers in a collapsible tabbed view (assistant-ui `Tabs` primitive). Adjudicator's rationale shown as a footer. Disclosure-tier gated: tier `super_admin` sees full dissent; tier `consenting_individual` sees summary only.

### γ2 — Long-reasoning UX for thinking models (2 days)

Reasoning drawer shows live token-count and elapsed-time-in-thought while reasoning streams (assistant-ui's reasoning composer already supports progress; we add the count from `reasoning_delta` lengths and the elapsed timer). For reasoning >2k tokens, drawer is collapsed by default with a "Show 3,420 tokens of reasoning ⌄" affordance.

### γ3 — Prediction logging affordance (3 days)

- Detect time-indexed predictions in assistant output via a lightweight pattern detector (regex + Haiku classifier) emitted as a `prediction_candidate` data part.
- UI surfaces an inline "📋 Log as prediction" button on detected sentences.
- On click, opens a modal with pre-filled `prediction_text`, `confidence`, `horizon`, `falsifier` fields; user reviews and submits.
- Submission writes to `predictions` table (sacrosanct — outcome left null per Learning Layer discipline rule #4).
- Lives in `platform/src/lib/ppl/` to surface clearly as the PPL workstream's chat hook.
- Documented in CLAUDE.md §E PPL entry as the v1 chat-side capture surface.

### γ4 — Validator failure surface (2 days)

Validator hard-fails render as an inline red band above the assistant message ("⚠ This answer failed citation validation. View details."). Soft-fails render as a footer chip. Both link into a per-message validator detail drawer (existing `ValidatorFailureView` re-skinned as assistant-ui composer). Super-admin tier shows full validator output; lower tiers see a summary.

### γ5 — Observability deep-link (1 day)

"View trace" link in the per-message details drawer (β6) opens `/observatory/trace/[query_id]` in a new tab. Existing Observatory route handles the rest.

### γ6 — Per-message cost visibility (1 day)

Cost (`$0.014` / `1,820 tokens` / `4.2s` / `Sonnet 4.6`) in the per-message details drawer. Super-admin always; other tiers gated by `MARSYS_FLAG_COST_VISIBILITY_FOR_USERS` (default `false`).

### γ7 — Stream resume after disconnect (4 days)

- New table `pending_streams` (migration `056_pending_streams.sql`): `query_id PK, conversation_id, accumulated_text, last_event_seq, expires_at (now + 10m)`.
- Route writes to `pending_streams` on every data part + text chunk (debounced 100ms).
- New endpoint `GET /api/chat/consume/resume?query_id=...&since_seq=...` returns the suffix as a UIMessage stream.
- Client detects abrupt disconnect (transport error, beforeunload), stores `query_id + last_event_seq` in `sessionStorage`, and on reconnect / reload calls the resume endpoint.
- assistant-ui handles client-side reconciliation (well-supported per `assistant-ui/docs/persistence.md`).
- `pending_streams` rows reaped by a Cloud Scheduler job every 5m for `expires_at < now()`.

### γ8 — Accessibility (3 days)

- `aria-live="polite"` on assistant message streaming region.
- `role="log"` on the thread.
- Focus management: new user-message focuses the thread; new assistant message announced to screen reader without stealing focus.
- Keyboard navigation: `Tab` cycles between composer / message thread / sidebar; `↑/↓` within message list; `Enter` to expand reasoning / citation; `Esc` to collapse.
- Screen reader test pass with NVDA (Windows fixture) + VoiceOver (macOS).
- a11y CI assertion against axe-core baseline.

### γ9 — Mobile responsive (3 days)

- Layout breaks at 375px (iPhone SE) and 768px (tablet).
- Composer auto-resizes; iOS keyboard handling (no input-zoom; viewport stable).
- Sidebar collapses to a slide-out drawer at <768px.
- Citation side panel becomes a bottom sheet at <768px.
- Reasoning drawer collapses by default at <768px.
- Touch targets ≥44px.
- Playwright mobile-viewport tests at 375px and 768px.

### γ10 — Adapter / streamBuildRaw consolidation (2 days)

Per §4.13. Synthesis route uses `streamAdapter` instead of `streamBuildRaw`. `streamBuildRaw` is deleted. `lib/adapters/legacy_runAdapter.ts` also deleted (already flag-gated; flag retired here). Result: single streaming path; single event channel; single source of truth.

### §7.A Acceptance criteria (Phase γ gate)

- Panel-mode dissent toggle reveals per-member answers; super-admin sees full content.
- Long-reasoning drawer shows live token-count + elapsed time; collapse default at >2k tokens.
- Prediction-candidate detection fires on a known test corpus; "Log as prediction" modal works end-to-end; writes to `predictions` table.
- Validator hard-fail shows inline error band; soft-fail shows footer chip; super-admin detail drawer works.
- "View trace" deep-link opens Observatory trace view in new tab with correct `query_id`.
- Cost visibility renders for super-admin; flag-gated for others.
- Stream resume verified: kill the browser tab mid-stream; reload; conversation resumes at correct token position.
- a11y: NVDA + VoiceOver test pass; axe-core CI assertion green.
- Mobile: 375px and 768px viewports pass all behavioral parity tests.
- `streamBuildRaw` and `legacy_runAdapter.ts` removed from codebase (grep returns zero).
- All Phase γ Playwright tests pass.

## §8 Branch + flag strategy

- **Branch**: `feature/chat-v2-bigbang` cut from main at plan ratification.
- **Cadence**: weekly rebase from main (Monday morning). Conflicts escalated to native within 24h.
- **Master flag**: `MARSYS_FLAG_CHAT_V2_ENABLED` (default `false` everywhere — `feature_flags.ts`, `.env.local`, `deploy.yml`).
- **Sub-flags** (default `false`): `MARSYS_FLAG_HISTORY_COMPRESSION_ENABLED`, `MARSYS_FLAG_COST_VISIBILITY_FOR_USERS`, `MARSYS_FLAG_STREAM_RESUME_ENABLED`, `MARSYS_FLAG_MULTIMODAL_PDF_ENABLED`. Used for safe partial rollout post-merge.
- **Dogfood deploys**: per-revision Cloud Run tags `--tag=chat-v2-alpha`, `--tag=chat-v2-beta`, `--tag=chat-v2-gamma`. Internal URLs `https://chat-v2-alpha---amjis-web-{hash}-uc.a.run.app` etc. Native + executor test against these without touching production traffic.
- **Merge gate**: master gate (§10) passes; pre-merge red-team passes (per `MACRO_PLAN_v2_0.md §IS.8(b)`); sealing artifact `CHAT_V2_CLOSE_v1_0.md` drafted.
- **Merge style**: `--no-ff` to preserve the workstream's commit history as a discoverable subtree.
- **Post-merge flag flip**: flag default `true` in `deploy.yml` only (NOT in `feature_flags.ts`) for 7 days of in-production verification. If clean, flip `feature_flags.ts` default to `true` and remove the flag entirely (Phase 11B pattern). If not clean, flip `deploy.yml` back to `false` (instant kill switch) and triage.

## §9 Test strategy

A chat interface of this complexity demands testing across ~16 categories spanning the full test pyramid (unit → component → integration → E2E) plus the non-functional axes (perf, a11y, load, security, chaos) plus chat-specific concerns (streaming, provider contracts, multi-modal, mobile). This section defines the taxonomy, tooling, coverage targets, CI/CD structure, and phase-specific test gates. Amended in v1.1 to address the v1.0 gap.

### §9.1 Philosophy + test pyramid

Distribution targets across the codebase (not strict, but indicative of intent):

| Layer | Target volume | Tool | Latency budget |
|---|---|---|---|
| Unit | ~70% | vitest | <30s suite |
| Component | ~15% | vitest + React Testing Library + jsdom | <2 min suite |
| Integration | ~10% | vitest with module boundaries | <3 min suite |
| E2E | ~5% | Playwright | <12 min suite, parallelized |

Principles:
- **Fail-fast in CI.** Unit + lint + typecheck run on every commit (<2 min). Heavier suites gated to PR.
- **Behavioral coverage over line coverage.** Every master-gate criterion (§10) maps to at least one E2E test plus at least one unit/integration test.
- **Deterministic fixtures.** Provider responses, multi-modal payloads, streaming chunks all live as committed fixtures so tests are reproducible offline.
- **Test the seam, not the framework.** We don't re-test AI SDK or assistant-ui internals; we test our wiring of them.
- **Write tests with the work item.** No work item is "done" without its tests passing alongside the implementation in the same commit.

### §9.2 Test taxonomy

#### §9.2.1 Unit tests (vitest)

All pure functions and reducers. Coverage target: ≥90% lines, ≥85% branches on new code.

Surfaces tested: marker_parser, prediction_detector (γ3), streaming_citation_validator (β10), history_compression (β8), data_part schema validators (Zod), provider_quirks, citation renderer logic, file-upload validation, prompt templates, format helpers. Approximate count by phase: α ≥ 80, β ≥ 120, γ ≥ 180 (cumulative).

#### §9.2.2 Component tests (vitest + React Testing Library + jsdom)

assistant-ui composers in isolation against mocked data-part inputs. No real network, no real LLM.

Components tested: StageStepper, ToolCallCard, ReasoningDrawer, ElapsedTimer, CitationChip (re-skinned), CitationPreview, NumberedCitation, DisclosureTierBadge, ValidatorFailureView, MessageEditor, MessageRegenerate, ConversationListSidebar, MultiModalUploader, ImageAttachmentPreview, PdfAttachmentPreview, PanelDissentTabs, PerMessageDetailsDrawer, MobileBottomSheet. Count by phase: α ≥ 15, β ≥ 30, γ ≥ 45 (cumulative).

#### §9.2.3 Integration tests (vitest with module boundaries)

Boundaries tested: route ↔ adapter, adapter ↔ provider (with recorded responses), persistence write-then-read round-trip, history_compression with mocked Haiku, stream_resume happy path, citation_validator wired against `streamText` mock. Approximate count: ≥40 by end of γ.

#### §9.2.4 End-to-end tests (Playwright)

Full user flows across Chromium / Firefox / WebKit. Headless in CI, headed for local debugging. Mobile viewports (375px Mobile Safari, 768px iPad) covered.

Test scenarios: send-and-stream, edit-and-regenerate, mid-stream-interrupt-cancel-and-replace, reload-restores-conversation, conversation-list-navigation, multi-modal-image-upload, multi-modal-pdf-upload, abort-during-stream, abort-during-tool-fetch, panel-mode-dissent-toggle, reasoning-drawer-expand, citation-inline-and-side-panel, validator-failure-band, prediction-candidate-log, observability-deep-link, cost-visibility-super-admin, stream-resume-after-disconnect, mobile-375px-full-flow, mobile-768px-full-flow, keyboard-only-navigation. Count by phase: α ≥ 10, β ≥ 25, γ ≥ 40 (cumulative).

#### §9.2.5 Visual regression tests (Playwright screenshot diff)

Committed baselines per major chat state, per viewport (1280px, 768px, 375px), per theme (Modern Dark Pro). Diff threshold 0.1% pixel delta default.

States captured: empty thread, composer focused, streaming-in-progress, complete-message, reasoning-expanded, reasoning-collapsed, citation-pinned, citation-side-panel-open, panel-dissent-expanded, panel-dissent-collapsed, validator-error-band, validator-warning-footer, multi-modal-image-attached, multi-modal-pdf-attached, per-message-details-drawer, conversation-list-sidebar, mobile-bottom-sheet, edit-mode, regenerate-confirmation. Count by end of γ: ≥60 baselines.

#### §9.2.6 Performance tests (Lighthouse CI + Web Vitals + custom streaming metrics)

**Web Vitals budgets (asserted in CI):**

| Metric | Budget | Rationale |
|---|---|---|
| TTFB | <800ms | Composer to first byte from `/api/chat/consume` |
| FCP | <1.5s | Page load |
| LCP | <2.5s | Largest contentful paint |
| INP | <200ms | Interaction latency (composer typing, button clicks) |
| CLS | <0.1 | Layout shift during streaming |

**Streaming-specific metrics (custom):**

| Metric | Budget | Rationale |
|---|---|---|
| Time-to-first-token | <1.5s | From submit to first text delta |
| Time-to-first-stage-event | <500ms | From submit to first stage data part |
| Frame budget under streaming | <16ms/frame | 60fps target |
| Tokens-per-second render | ≥80 t/s | Threshold below which UX feels janky |
| Memory growth over 50-turn conversation | <30MB | Detect leaks |

Lighthouse CI runs nightly on a known fixture conversation against the dogfood deploy. Regressions >10% on any metric fail the PR check.

#### §9.2.7 Accessibility tests (axe-core programmatic + manual screen reader passes)

**Programmatic (axe-core in Playwright):**
- WCAG 2.1 AA full audit on every E2E test page.
- Zero serious/critical violations allowed (PR-blocking).
- Color contrast verified for streaming caret + reasoning drawer + citation chips.

**Manual passes (γ8 gate):**
- NVDA + Firefox (Windows) — full streaming conversation
- VoiceOver + Safari (macOS) — full streaming conversation
- VoiceOver + Safari (iOS) — mobile streaming conversation
- Keyboard-only navigation: every interaction reachable, focus visible, focus order logical

#### §9.2.8 Load / stress tests (k6)

Test scenarios run nightly against the dogfood deploy and pre-merge against staging:

| Scenario | Load | Target |
|---|---|---|
| Steady-state | 100 concurrent users, 10 min | <1% error rate, p95 TTFT <2s |
| Burst | 500 concurrent users, 2 min | <5% error rate, no cascading failure |
| Sustained | 200 concurrent users, 1h | No memory growth, no DB connection leaks |
| Long conversation | 1 user, 50-turn conversation | History compression triggers correctly; no perf regression |
| Multi-modal storm | 50 concurrent users, image+PDF on every turn | GCS upload latency p95 <3s |
| Stream resume | 100 disconnect-reconnect cycles | 100% resume success; correct token position |

Scripts at `platform/tests/load/k6/`.

#### §9.2.9 Provider contract tests (record-replay fixtures)

Each provider (Anthropic Claude Sonnet/Opus/Haiku, Anthropic thinking, Gemini 2.5 Pro/Flash, Gemini 2.5 thinking, OpenAI gpt-5 family, DeepSeek V4/R1, NIM) gets a recorded fixture set covering:

- Quick non-streaming response
- Long streaming response (≥4k tokens)
- Reasoning model response (≥2k reasoning + answer)
- Tool-call interleaving (≥3 tool calls)
- Multi-modal input acceptance (image, PDF)
- Mid-stream error (429 with retry-after, 503, timeout)
- Empty / malformed response

Fixtures live at `platform/tests/fixtures/providers/{provider}/`. Refreshed monthly and on every AI SDK / provider-SDK upgrade. A "provider drift" CI job runs weekly against live provider APIs (with dev keys, dollar-budget-capped) to detect protocol drift early.

#### §9.2.10 Chaos / fault injection tests

Deliberate failure injection to verify graceful degradation. Run pre-merge + weekly.

Scenarios:
- Provider 429 mid-stream (with and without retry-after header)
- Provider 503 mid-stream
- Provider timeout (request hangs at 10s, 30s, 60s)
- Network partition mid-stream (Toxiproxy)
- Database write failure during persistence
- GCS upload failure during multi-modal
- Concurrent abort + new query race
- Disclosure tier change mid-conversation
- Master flag flipped mid-conversation
- Synthesis prompt missing a required ledger field
- Adjudicator model unavailable during panel mode
- pending_streams expiry during active resume

Each scenario asserts: error reaches user with appropriate message, no orphan state in DB, no silent token waste, kill switch (master flag) still works.

#### §9.2.11 Security tests

| Class | Test |
|---|---|
| XSS in composer | Paste `<script>` and `javascript:` URLs; verify sanitization |
| XSS in assistant markdown | Provider returns malformed HTML / dangerous SVG; verify streamdown sanitizes |
| XSS in citation preview | Citation source title contains script tag |
| XSS in filename | Upload file named `<script>alert(1)</script>.pdf` |
| SSRF via citation URL | Citation source URL = `http://169.254.169.254/...` |
| File upload validation | Upload zip, executable, image-with-payload (polyglot); verify mimetype check, size check, magic byte check |
| Path traversal | GCS key construction with `../../../` user input |
| Auth bypass | Anonymous request to `/api/conversations`, `/api/chat/consume/resume`, `/api/conversations/[id]/messages` |
| Conversation ownership bypass | User A tries to read user B's conversation |
| Disclosure tier bypass | Lower tier requests super-admin-only data via API |
| Prompt injection in user input | User input contains `Ignore previous instructions...`; verify our prompt template structure prevents escape |
| Prompt injection in PDF text | PDF Document Understanding extracts adversarial instructions |
| Token budget exhaustion | Sustained 50k-token messages; verify budget enforcement |
| Resume token forgery | Request resume with another user's `query_id` |

Run pre-merge. OWASP ZAP optional for deeper scan; not gating.

#### §9.2.12 Mobile / device tests

Real device emulation via Playwright's mobile profiles AND occasional manual passes on physical devices (BrowserStack or available hardware).

- iOS Safari (iPhone 14, iOS 17+) — keyboard handling, viewport stability, no input-zoom, touch target ≥44px, bottom-sheet navigation
- Android Chrome (Pixel 7, Android 13+) — same
- iPad Safari (10.9") — tablet layout
- Mobile-specific scenarios: composer auto-resize on rotation, sidebar drawer slide, citation bottom-sheet swipe, reasoning drawer collapse default

#### §9.2.13 Streaming-specific tests

The class of bug that broke v1. Dedicated suite at `platform/tests/streaming/`.

| Scenario | Assertion |
|---|---|
| 1-char-per-chunk stream | Renders correctly; no re-parse storm |
| 1k-char-per-chunk stream | Renders correctly |
| Mixed chunk sizes (provider quirk) | Renders correctly |
| Incomplete code fence streamed across chunks | streamdown handles unterminated fence; no flicker |
| Incomplete KaTeX math streamed across chunks | KaTeX renders incrementally; no flicker |
| Incomplete table row | Table renders progressively |
| Reasoning interleaved with answer | Reasoning drawer + answer body update independently |
| Tool call mid-stream | ToolCallCard appears; answer continues after |
| Multi-citation answer (10+ citations) | All inline numbers render; side panel shows all sources |
| Abort at byte 0 (first token) | Clean cancel, no orphan state |
| Abort at byte 1000 (mid-stream) | Partial saved to pending_streams; resumable |
| Abort at byte 5999 of 6000 (near end) | Partial saved; resumable |
| Stream completes during disconnect | onFinish still fires server-side; persistence succeeds |
| Resume from byte 800 of 2000 | Suffix streams correctly; client reconciles to full message |
| Back-pressure (slow client) | Stream pauses; no buffer overflow; no token loss |

#### §9.2.14 Type tests (tsd)

Critical type contracts asserted at compile time, not runtime. Lives at `platform/tests/types/`.

- `UIMessage` round-trips through `convertToModelMessages` without lossy narrowing.
- Data part schemas (Zod) infer the expected TypeScript types.
- `QueryRequest`, `ModelInteractionEvent`, `SynthesisRequest` shape stability.

#### §9.2.15 Snapshot tests

Schema serialization stability and API response shape stability. JSON schema diffs require explicit review (no silent shape drift).

#### §9.2.16 Mutation tests (Stryker — selective)

Run on critical paths only (high-stakes correctness; not blanket). Verifies that the unit test suite catches deliberately-introduced bugs.

Paths covered:
- citation_gate streaming validator
- abort propagation through adapter inner loops
- persistence write-confirm acknowledgment
- prediction_detector
- history_compression boundary logic
- stream_resume token-position reconciliation

Target mutation score: ≥75% on these paths. Runs weekly + pre-merge.

### §9.3 Test data management

- **Fixture library** at `platform/tests/fixtures/chat-v2/` with subdirs: `providers/`, `conversations/`, `multimodal/`, `validator/`, `panel/`, `streaming-chunks/`, `pdfs/`, `images/`.
- **Versioned with code.** Fixture updates require review + a PR.
- **Seeded test database** via Supabase migrations + `platform/tests/db/seed_chat_v2.ts`. Isolated test schema per CI worker.
- **Provider key isolation.** Test runs use dedicated dev keys per provider, dollar-budget-capped via Observatory alerts.
- **GCS test bucket** `marsys-chat-uploads-test-{worker}` with auto-delete after 24h.

### §9.4 CI/CD pipeline

Multi-stage pipeline at `.github/workflows/chat-v2-ci.yml`. Stages parallelize where dependencies allow.

| Stage | Trigger | Duration target | Gate |
|---|---|---|---|
| 1. Lint + typecheck + unit | Every commit | <2 min | Hard |
| 2. Component + integration | Every PR | <5 min | Hard |
| 3. E2E (Chromium) | Every PR | <12 min | Hard |
| 4. E2E (Firefox + WebKit) | Every PR | <15 min parallelized | Hard from β onward |
| 5. Visual regression | Every PR | <8 min | Hard |
| 6. a11y (axe-core) | Every PR | <3 min | Hard from γ8 onward |
| 7. Perf (Lighthouse CI) | Every PR | <10 min | Soft (warn) until γ; hard at γ |
| 8. Load / stress (k6) | Nightly + pre-merge | <30 min | Soft nightly; hard pre-merge |
| 9. Provider drift | Weekly | <20 min | Soft (alert) |
| 10. Chaos / fault injection | Weekly + pre-merge | <15 min | Hard pre-merge |
| 11. Security | Pre-merge | <10 min | Hard |
| 12. Mobile (Playwright profiles) | Every PR | <8 min parallelized | Hard from γ9 onward |
| 13. Mutation (Stryker, selective) | Weekly + pre-merge | <30 min | Soft weekly; hard pre-merge |
| 14. Cross-browser smoke (staging deploy) | Pre-merge | <10 min | Hard |
| 15. Synthetic monitoring (post-merge) | Continuous | n/a | Alerts only |

PRs blocked on hard-gate failures. Soft-gate failures comment on PR with details and require explicit acknowledgment.

### §9.5 Coverage targets

| Layer | Target |
|---|---|
| Line coverage (new code in workstream) | ≥85% |
| Branch coverage (new code) | ≥75% |
| Behavioral coverage (master-gate criteria → tests) | 100% (every §10 criterion has tests) |
| Mutation score (critical paths) | ≥75% |
| E2E scenarios for each user-facing work item | ≥1 |

Coverage drift is monitored via Codecov (or self-hosted equivalent); regressions >2% fail the PR.

### §9.6 Test environment parity

| Environment | Postgres | GCS | Providers | Auth | LLM cost |
|---|---|---|---|---|---|
| Local dev | docker-compose Postgres | fake-gcs-server | Fixture replay | Local mock | $0 |
| CI | ephemeral Postgres per worker | fake-gcs-server | Fixture replay | Mock | $0 |
| Staging | Cloud SQL replica | Real GCS test bucket | Real providers (dev keys, capped) | Firebase test tenant | <$20/day budget |
| Production dogfood | Cloud SQL prod | Real GCS prod bucket | Real providers (prod keys) | Firebase prod | Behind master flag (no user traffic) |
| Production | Cloud SQL prod | Real GCS prod bucket | Real providers | Firebase prod | Full |

Local + CI deliberately use fixture replay so contributors don't burn provider tokens running tests.

### §9.7 Synthetic monitoring (post-merge)

Cloud Scheduler probes hitting `/api/chat/consume` every 5 min with a known short-prompt fixture; assertions on TTFT, stream completion, persistence ack. Alerts route to Slack via Observatory. Existing Observatory `query_trace_steps` pipeline ingests these probe traces under a synthetic-source tag so they don't pollute user metrics.

### §9.8 Test ownership + review

- Every work-item owner writes the tests in the same PR as the implementation.
- Each PR has a "Tests added" section in its description listing the test files touched.
- Native or peer reviewer must approve test additions + diffs.
- Test debt (skipped tests, `it.todo`, flaky tests) is tracked in `platform/tests/TEST_DEBT.md` and triaged at end of each phase.
- Flaky tests quarantined to a `flaky/` subdir within 24h of first flake; retried up to 3x in CI; flagged for owner.

### §9.9 Phase-specific test gates

Cumulative tests required at each phase exit, in addition to the master gate (§10).

**Phase α exit:**
- Test scaffolding complete (Playwright config, fixtures, visual baseline, perf budget, axe-core CI integration).
- Unit ≥80, component ≥15, integration ≥10, E2E ≥10, visual baselines ≥20.
- TTFT and frame-budget metrics asserted green against fixtures.
- α0 spike test suite green (assistant-ui edge cases).

**Phase β exit:**
- Cumulative unit ≥120, component ≥30, integration ≥30, E2E ≥25, visual baselines ≥40.
- Chaos tests for abort + persistence + mid-stream interrupt pass.
- Provider contract fixtures cover all listed providers + scenarios.
- Multi-modal upload security tests pass.
- Cross-browser E2E (Firefox + WebKit) hard-gated from β onward.

**Phase γ exit:**
- Cumulative unit ≥180, component ≥45, integration ≥40, E2E ≥40, visual baselines ≥60.
- Load tests (steady-state + burst + sustained) pass.
- a11y manual screen-reader passes (NVDA + VoiceOver desktop + VoiceOver iOS) documented green.
- Mobile Playwright profiles hard-gated.
- Security suite fully green.
- Mutation tests on critical paths ≥75%.
- Stream resume scenarios all pass (clean disconnect, dirty disconnect, network partition).

### §9.10 Pre-merge verification (master gate test discharge)

The master-gate criteria in §10 each map to test artifacts. Pre-merge verification produces a master-gate evidence pack listing the passing test SHA for each criterion. Native reviews the pack and signs the sealing artifact `CHAT_V2_CLOSE_v1_0.md`.

In addition:

- Full CI pipeline green on the merge commit candidate.
- Manual native acceptance walk-through executed against §10 criteria, recorded in a session at `00_ARCHITECTURE/CHAT_V2_PREMERGE_S1_log.md`.
- Red-team pass: 5 probes targeting the workstream's risk surface per `MACRO_PLAN_v2_0.md §IS.8(b)`. Red-team plan documented at `00_ARCHITECTURE/CHAT_V2_RED_TEAM_v1_0.md`. 5/5 PASS required.
- Performance regression check against pre-α baseline (no regression >10% on any Web Vital or streaming metric).
- Test debt register reviewed; nothing blocking on the path to merge.

### §9.11 Tooling summary

| Concern | Tool |
|---|---|
| Unit + component + integration | vitest |
| Component rendering | React Testing Library + jsdom |
| E2E + visual regression + cross-browser | Playwright |
| Perf | Lighthouse CI + custom Web Vitals harness |
| a11y programmatic | axe-core (via Playwright) |
| a11y manual | NVDA, VoiceOver |
| Load / stress | k6 |
| Provider contract | Custom record-replay fixture library |
| Chaos / fault injection | Toxiproxy (network) + custom in-process injectors |
| Security | Manual test suite + OWASP ZAP (optional) |
| Type tests | tsd |
| Mutation | Stryker |
| Coverage | Codecov (or self-hosted) |
| Mobile | Playwright mobile profiles + occasional BrowserStack |
| Synthetic monitoring | Cloud Scheduler + Observatory |

## §10 Master gate — acceptance criteria for merge to main

Cumulative across all three phases. Every item must pass before merge.

1. Streaming a 6000-token answer (with code blocks + KaTeX math + inline citations): zero dropped frames in browser perf timeline; render <16ms/frame; no `Maximum update depth exceeded` warnings under any input.
2. Stop button cancels server-side LLM call + tool fetches + panel passthrough within 200ms (verified via `query_trace_steps`).
3. Turn 5 of a conversation correctly references content from turn 1 (verified via `answer:eval` harness).
4. Panel-mode user sees first stage event within 1s; adjudicator answer streams real tokens (no Haiku passthrough).
5. Citation-gate hard-failure produces a user-visible error band.
6. Edit + regenerate work across all message positions (first, middle, last); branching navigation works.
7. Page reload preserves conversation; conversation list shows all owned conversations; archive works.
8. Mid-stream submit cancels prior within 300ms and starts new.
9. Multi-modal: image upload + display works; PDF upload + extraction works; both survive a multi-turn conversation.
10. Stream resume after disconnect works: kill tab mid-stream, reload, conversation resumes at correct token position.
11. Mobile responsive at 375px (iPhone SE) and 768px (tablet); all behavioral parity tests pass at those viewports.
12. Accessibility: NVDA + VoiceOver screen-reader test pass; axe-core CI assertion green.
13. Per-message details drawer shows model / tokens / latency / validators / cost / disclosure tier; "View trace" deep-link works.
14. Prediction-candidate detection fires on a test corpus; "Log as prediction" modal end-to-end works.
15. `streamBuildRaw` + `legacy_runAdapter.ts` + `extractText` removed (grep returns zero); single streaming path through `streamAdapter`.
16. Cumulative test count met: ≥180 unit, ≥45 component, ≥40 integration, ≥40 E2E, ≥60 visual baselines — all green.
17. Web Vitals budgets met: TTFB <800ms, FCP <1.5s, LCP <2.5s, INP <200ms, CLS <0.1. Streaming budgets met: TTFT <1.5s, first-stage-event <500ms, render <16ms/frame, ≥80 t/s render throughput, memory growth <30MB over 50-turn conversation.
18. a11y: axe-core CI green (zero serious/critical violations); NVDA + VoiceOver (macOS + iOS) manual screen-reader passes documented green; keyboard-only navigation verified.
19. Cross-browser: Chromium + Firefox + WebKit E2E suites green.
20. Mobile: Playwright profiles at 375px (iPhone Safari) and 768px (iPad Safari) green; physical-device spot check on iOS + Android documented.
21. Load: k6 steady-state (100 concurrent, 10 min) <1% error rate, p95 TTFT <2s; burst (500 concurrent, 2 min) <5% error, no cascade; sustained (200 concurrent, 1h) no leak.
22. Chaos: all listed §9.2.10 fault-injection scenarios pass.
23. Security: all listed §9.2.11 tests pass; no XSS / SSRF / auth-bypass / prompt-injection findings unresolved.
24. Provider contract fixtures cover all listed providers + scenarios; weekly provider-drift CI clean for the trailing two weeks.
25. Mutation score on critical paths ≥75%.
26. Coverage targets met: ≥85% lines + ≥75% branches on new code; behavioral coverage 100% (every master-gate criterion mapped to passing tests).
27. Red-team pass: 5/5 probes PASS.
28. Master-gate evidence pack assembled at `00_ARCHITECTURE/CHAT_V2_MASTER_GATE_EVIDENCE_v1_0.md`; native sign-off recorded.

## §11 Risks + mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | 4-6 week branch life with no user ship | High | Med | Per-revision Cloud Run dogfood deploys keep native+executor close to the work; weekly progress reviews. |
| R2 | Branch rot vs. main (M5-A and concurrent work) | Med | Med | Weekly rebase; file-scope isolation per §2; explicit conflict-watch list (`feature_flags.ts`, `route.ts`, `package.json`). |
| R3 | assistant-ui doesn't handle a MARSYS edge case | Med | High | α0 spike is a hard gate; if spike fails, fall back to custom build at +2 weeks scope. |
| R4 | Test surface unverifiable at end of γ | Med | High | α1 invests in scaffolding *first*; each phase adds tests inline. |
| R5 | M5-A macro-phase work conflicts | Low | Med | File-scope isolation; chat workstream avoids L2.5 + learning-layer paths entirely. |
| R6 | One phase bug blocks the train | Med | Med | Master flag is the kill switch; legacy path remains shippable until merge. |
| R7 | Master gate criteria not all reachable | Low | High | Pre-merge red-team flags this; can defer specific γ items to v2 if shown infeasible, with native sign-off + plan amendment. |
| R8 | Provider streaming protocol drift mid-flight (Anthropic / Gemini ship a breaking change) | Low | Low | AI SDK v6 abstracts; adapter layer absorbs. Track AI SDK release notes weekly. |
| R9 | Multi-modal upload bucket cost / quota | Low | Low | Lifecycle rule: chat-upload bucket auto-deletes objects after 30d; quota monitored via Observatory. |
| R10 | PPL prediction detector false-positive rate | Med | Low | Detector emits *candidate* only; user must explicitly confirm before write. False positives are inert. |

## §12 Open questions (settle before α start)

1. **Validator failure: block vs. warn.** Should a hard-failed citation gate prevent the message from displaying, or display with a prominent red band? My recommendation: display + red band + super-admin can see the validator detail. User retains agency; calibration discipline preserved via visible warning. Awaits native decision.
2. **Prediction logging: opt-in per message vs. always-prompted.** When detector fires, does the "Log as prediction" affordance appear inline (every detected sentence) or is it gathered into a single end-of-message review modal? Recommendation: end-of-message review modal — less interrupted UX. Awaits native decision.
3. **Per-message cost visibility for non-super-admin users.** Default to never-shown, with sub-flag `MARSYS_FLAG_COST_VISIBILITY_FOR_USERS` to enable. Should this be enabled at merge time or kept off as v2 work? Recommendation: keep off at merge; revisit when consenting-individual disclosure tier launches.
4. **Conversation auto-titling.** assistant-ui supports auto-titles from first turn. Use it? Recommendation: yes, with the existing `title_generator` Haiku flow already in `route.ts`.

## §13 Execution sequencing (estimate)

| Phase | Work items | Executor sessions | Calendar |
|---|---|---|---|
| Pre-α | TEST_STRATEGY authoring (`00_ARCHITECTURE/CHAT_V2_TEST_STRATEGY_v1_0.md`) — concrete test plans per §9 taxonomy with file paths, fixture inventory, CI pipeline YAML scaffold | 1 session | day 0 |
| α | α0 (spike), α1 (tests), α2 (streamdown), α3 (data parts), α4 (UIMessage), α5 (retry), α6 (flags), α7 (master flag wiring) | 8 sessions | week 1-2 |
| β | β1-β10 | 14 sessions | week 3-4 |
| γ | γ1-γ10 | 12 sessions | week 5-6 |
| Pre-merge | red-team + master gate verification + evidence pack + sealing artifact | 3 sessions | week 6-7 |
| **Total** | **32 work items** | **~38 sessions** | **~6-7 weeks** |

Sessions parallelizable within each phase where dependencies allow. Native may compress with subagent fan-out per phase. Sessions follow CONVERSATION_NAMING_CONVENTION: `CHAT_V2_α_S1`, `CHAT_V2_α_S2`, ..., `CHAT_V2_γ_S12`, `CHAT_V2_PREMERGE_S1`.

## §14 Mirror & cross-workstream notes

- **No mirror pair declared at v1.0.** This workstream is Claude-side governance. If any phase work passes through Gemini (e.g., L4 Discovery query rendering in the same chat), declare MP.10 at that time.
- **PPL workstream cross-link.** γ3 is the first concrete chat-side surface for PPL (Prospective Prediction Logging, per CLAUDE.md §E). On ratification of this plan, add a cross-reference from PPL workstream notes to `CHAT_V2_PLAN_v1_0.md §γ3`.
- **Observatory cross-link.** γ5 deep-link consumes existing Observatory endpoints. No Observatory changes required.
- **Macro-phase M-series.** No M-series dependency. M6 (time-gated 2026-11-14) may have downstream chat-side implications; not in scope here.

## §15 Open work surfaces deferred to CHAT_V3

- Voice I/O (Whisper STT + TTS provider integration).
- Real-time collaborative chat / multi-user shared sessions.
- Cross-native query-mode dedicated UI.
- Server-side rendering for first-paint optimization.
- WebRTC for ultra-low-latency token streaming (currently HTTP streaming is sufficient).

## §16 Ratification checklist

Before α0 begins, the native confirms:

- [ ] §4 architecture decisions accepted (assistant-ui adoption, streamdown, master flag, branch strategy, write-through persistence, stream resume, sliding-window summarization, citation gate at the wire, retry policy, adapter consolidation).
- [ ] §3 scope IN / OUT accepted.
- [ ] §9 test strategy accepted in principle (taxonomy, tooling, gates, coverage targets); detailed test plan to be produced as Pre-α deliverable.
- [ ] §12 open questions answered (validator failure mode, prediction logging UX, cost visibility default, auto-titling).
- [ ] §13 sequencing roughly accepted (6-7 weeks, 32 work items, ~38 sessions).
- [ ] CLAUDE.md §E updated to list this workstream as concurrent (parallel to M-series).
- [ ] Branch `feature/chat-v2-bigbang` cut from main.
- [ ] Pre-α TEST_STRATEGY authoring session scheduled (1 session, day 0).
- [ ] α0 spike session scheduled.

## §17 Changelog

- **v1.0 (2026-05-16, DRAFT)** — Initial authoring by Claude during Cowork planning session 2026-05-16. Pending native ratification per §16. Workstream classification, scope, three-phase structure (α/β/γ), architecture decisions, branch + flag strategy, test strategy, master gate, risks, open questions, sequencing.
- **v1.1 (2026-05-16, DRAFT)** — Amended same-day per native request to address §9 thinness. Expanded test strategy to 11 sub-sections covering 16 test categories (unit, component, integration, E2E, visual regression, perf incl. Web Vitals + streaming-specific, a11y programmatic + manual, load/stress, provider contract, chaos/fault injection, security, mobile, streaming-specific, type, snapshot, mutation), plus test data management, CI/CD pipeline (15 stages), coverage targets, environment parity, synthetic monitoring, ownership/review, phase-specific test gates, and tooling summary. §10 master gate expanded from 18 to 28 criteria with explicit test-discharge requirements. §13 sequencing adds a Pre-α TEST_STRATEGY authoring session (day 0) and bumps total to ~38 sessions across 6-7 weeks. §16 ratification checklist adds a test-strategy review checkpoint.

---

*End CHAT_V2_PLAN_v1_1 DRAFT. Awaits native ratification before Pre-α TEST_STRATEGY session begins.*
