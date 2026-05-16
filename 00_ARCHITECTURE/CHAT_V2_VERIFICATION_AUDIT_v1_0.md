---
canonical_id: CHAT_V2_VERIFICATION_AUDIT
version: 1.0
status: DRAFT
authored: 2026-05-16
author: Claude (Cowork research subagent, pre-§M.16)
governing_plan: 00_ARCHITECTURE/CHAT_V2_PLAN_v1_0.md v1.1
merge_candidate: main @ 705beb3 (post-§M.15 flag flip)
purpose: Identify orphaned / unreachable Chat V2 features and verification gaps before the §M.16 quality campaign.
---

# CHAT V2 — VERIFICATION AUDIT v1.0

Research-grade reachability + verification audit of the 32 Chat V2 work items now live in production behind `MARSYS_FLAG_CHAT_V2_ENABLED=true`. Findings are evidence-based: file paths cited; no fixes applied.

## §1 — Feature reachability matrix

| Work item | What was shipped | User-facing affordance | UI component path | Triggered by | Reachable? | Tier | Notes |
|---|---|---|---|---|---|---|---|
| PA1 | TEST_STRATEGY + CI scaffold + fixture tree | none (governance) | n/a | n/a | YES (governance only) | n/a | Real provider fixtures still `TODO-record`. |
| α0 | Spike route + `/dev/chat-spike` page | dev-only spike Thread | `app/dev/chat-spike/page.tsx`, `components/chat-v2/spike/ChatSpikeThread.tsx` | URL `/dev/chat-spike` | YES (super-admin) | super_admin | Dead in prod path; only `chat-v2/` content. |
| α1 | Playwright config + a11y/perf specs | none (test infra) | n/a | CI | PARTIAL | n/a | Auth-gated; 96 of 116 specs skipped per §M.11. |
| α2 | streamdown swap in `MarkdownContent` | rich markdown | `components/chat/MarkdownContent.tsx` | render path | **NO in V2** | n/a | **`ConsumeChatV2.V2AssistantText` uses `<p className="whitespace-pre-wrap">`; MarkdownContent never imported** — α2 swap reaches only `ConsumeChatLegacy`. No code blocks, KaTeX, GFM in V2. |
| α3 | `data_parts.ts` + `createUIMessageStream` writer + stage/tool emission | StageStepper / ToolCallCard | none | server emit | PARTIAL | n/a | Server emits stage/tool/persistence parts; **no V2 component subscribes to `data-stage` or `data-tool`**. Server-side scaffolding without UI consumer. |
| α4 | `UIMessage` end-to-end (extractText removed from synthesis) | invisible structural | route + strategy | server | YES | n/a | Verified via grep. |
| α5 | Per-provider retry table | invisible structural | `provider_quirks.ts` | server | YES | n/a | OK. |
| α6 | Flag default reconciliation + `CHAT_V2_ENABLED` flag declared | invisible | `feature_flags.ts`, `deploy.yml` | server | YES | n/a | OK. |
| α7 | `ConsumeChat` thin switch | flag-gated UI | `components/consume/ConsumeChat.tsx` | flag read by page | YES | all | OK. |
| β1 | `ActionBarPrimitive.Edit` + `Reload` + `BranchPicker` + `/api/chat/consume/regenerate` | edit/regenerate icons (hover-only) | `ConsumeChatV2.tsx` lines 374, 475; `app/api/chat/consume/regenerate/route.ts` | hover over message + click pencil/reload | PARTIAL | all | Action bar has `opacity-0 group-hover:opacity-100` — invisible without hover. **`/api/chat/consume/regenerate` endpoint has zero client callers**; edit + regenerate run through normal consume route, so **DB truncation never happens** — old assistant turns accumulate in `conversation_messages` on every regenerate. |
| β2 | conversations write-through, sidebar, restore | sidebar + persistence | `ConsumeChatV2.ConversationSidebar` | sidebar click | YES | all | `loadConversationMessagesV2` returns `metadata_json`, but the route's `writeConversationMessages` call **does NOT pass `lastAssistantMetadata`** (search returns only the test file). All restored messages therefore carry `metadata = {}` → drawer shows `—` for every restored turn. |
| β3 | Cancel-and-replace via `runtime.cancelRun()` + 300ms resubmit | interrupt-send button | `V2Composer` lines 759–763, 866–877 | composer state `isRunning` then click "→" | YES | all | OK structurally. |
| β4 | Inline numbered citations + side panel | `[N]` badges + hover + side panel | `NumberedCitation.tsx`, `CitationSidePanel.tsx` | clickable on SIG.MSR.NNN in text | PARTIAL | all | Render works; but `handlePin` (ConsumeChatV2 line 1190) creates citation with `snippet: ''`. **Server emits rich `data-citation` parts with snippets, V2 never consumes them.** Tooltip + side panel always blank-source. Also: synthesis prompt v2 (`consumeSystemPromptV2`) with the citation appendix is **never imported anywhere** — model uses legacy prompt. |
| β5 | Multi-modal image + PDF upload | attach button + drag-drop + paste | `V2Composer` 828, `AttachmentStrip` | composer | PARTIAL | all | UI works. **GCS signed-URL path is stubbed `TODO(§M.1)` in `app/api/uploads/sign/route.ts:53`**; runtime always falls through to `fake_gcs_store` (in-process Map). Uploads lost on Cloud Run revision rollover or pod recycle. **PDF extractor is hardcoded to fixture path** even when Vertex creds present (`pdf_extractor.ts:62-72`). |
| β6 | Per-message metadata drawer | "ⓘ" icon (hover-only) | `PerMessageDetailsDrawer.tsx` | hover + click ⓘ | PARTIAL | all | Drawer reads `data-cost` and `data-observability` — **neither part is emitted by the route**. Tokens / Latency-synthesis / Cost / Trace-link fields will all show `—` or be absent in live traffic. |
| β7 | Abort propagation through adapters + tools | invisible structural | adapters | server | YES | n/a | Verified. |
| β8 | History compression module | invisible structural | `history_compression.ts` | flag | **FLAG-GATED OFF** | n/a | `HISTORY_COMPRESSION_ENABLED` default false; flag is read by route. Code is correct but dormant. |
| β9 | Honest panel streaming + adjudicator stream | adjudicator stream + member events | `panel_strategy.ts` | `panel_opt_in=true` in body | PARTIAL | all | **There is no UI affordance in `ConsumeChatV2` to send `panel_opt_in=true`.** Grep `panel_opt_in` in `ConsumeChatV2.tsx` → 0 matches. Legacy chat has `panelOptIn` checkbox; V2 dropped it. Panel feature is server-ready but user-unreachable in V2. |
| β10 | Streaming citation validator emits `data-citation-gate` | invisible structural | `streaming_citation_validator.ts` | onFinish | YES | n/a | Emits part to client. |
| γ1 | Panel confidence ribbon + dissent tabs | ribbon + toggle | `PanelConfidenceRibbon.tsx`, `PanelDissentTabs.tsx`, `V2Message` lines 394, 432 | server emits `data-panel-meta` | UNREACHABLE | super_admin (full) / others (summary) | Renders only when `isPanel` truthy, which depends on `data-panel-meta` part being received, which only fires when panel mode runs — which requires `panel_opt_in=true` (β9 orphan). Dependency chain broken at β9. |
| γ2 | Reasoning drawer with token + elapsed | drawer | `ReasoningProgress.tsx` | server emits reasoning chunks | YES (for thinking models) | all | Renders when reasoning parts arrive. |
| γ3 | Prediction logging | "📋 Log as prediction" pill (super_admin only) | `V2Message` lines 440-464, `PredictionLogModal.tsx`, `/api/predictions` route | server detects + emits `data-prediction-candidate` | **PARTIAL/BROKEN** | super_admin | UI renders only `isSuperAdmin && predictionCandidates.length`. **`POST /api/predictions` queries `query_trace_steps WHERE user_id=$2`** but `query_trace_steps` writer (`lib/trace/writer.ts:14`) never writes `user_id` column. So ownership check `rows.length === 0` → forbidden. Every submit returns 403. |
| γ4 | Validator failure band + footer chip | red band / amber chip | `ValidatorFailureBand.tsx`, `ValidatorFooterChip.tsx`, `V2Message` 405, 423 | server emits `data-citation-gate` | YES | super_admin (issues list) / others (summary) | Wired. |
| γ5 | "View trace" deep-link | link in drawer | `PerMessageDetailsDrawer` 122 | data-observability OR meta.queryId | PARTIAL | all | Falls back to `meta.queryId` because **`data-observability` is never emitted**. Fallback path works since route stamps `queryId` in `messageMetadata.start`. |
| γ6 | Cost visibility for non-admin | drawer Cost section | `PerMessageDetailsDrawer` 183 | `COST_VISIBILITY_FOR_USERS` flag | FLAG-GATED OFF | super_admin always / others gated | Code present; flag default false. Will show `—` regardless because `data-cost` is not emitted (see β6). |
| γ7 | Stream resume via `pending_streams` | partial recovery on reload | `V2StreamResumeTracker`, `resume/route.ts`, `pending_streams_writer.ts` | mount-time sessionStorage check | YES | all | Wired; P.5 fix applied (`user_id` ownership check). Reaper §M.4 not provisioned — TTL rows leak. |
| γ8 | role=log, aria-live, aria-labels | invisible (a11y) | `V2Thread` 956–963 | screen reader | YES | all | Programmatic axe-core green; manual NVDA / VoiceOver §M.8 deferred. |
| γ9 | Mobile h-dvh + 44px targets + bottom sheet | layout breakpoints | `ConsumeChatV2.tsx`, `CitationSidePanel.tsx` | viewport | YES | all | Verified; physical device §M.9 deferred. |
| γ10 | `streamBuildRaw` + `legacy_runAdapter` deletion | invisible structural | adapters/raw.ts | server | YES | n/a | Grep clean. |
| PM1 | Red-team 5/5 PASS + P.5 fix | invisible | `red_team.test.ts` + writer patches | n/a | YES | n/a | OK. |
| PM2 | Master gate evidence pack | governance | doc | n/a | YES | n/a | OK. |
| PM3 | Sealing artifact | governance | `CHAT_V2_CLOSE_v1_0.md` | n/a | YES | n/a | OK. |

## §2 — Orphaned features

| # | Feature | Built | Why orphaned | Severity | Fix shape |
|---|---|---|---|---|---|
| O1 | **`data-cost` data part never emitted** | `PerMessageDetailsDrawer.tsx:86`, route computes `computeCostUsd` at `single_model_strategy.ts:641` | Cost computed for Observatory only; no `writer.write({type:'data-cost'...})` call. β6 drawer Tokens / Synthesis Latency / Cost rows always blank in production | **Critical** | Add `writer.write` of `costPart(...)` in `single_model_strategy.ts` onFinish via a callback; pipe into the route's `writer`. Multi-file. |
| O2 | **`data-observability` data part never emitted** | `PerMessageDetailsDrawer.tsx:107`, `data_parts.ts:69` | Schema declared, no emitter. γ5 trace link falls back to `meta.queryId` (works) but drawer's primary path is dead | **Medium** (falls back) | Single-line addition in route's `createUIMessageStream.execute`. |
| O3 | **`data-citation` rich parts not consumed by client** | route emits in onFinish (line 1076), schema at `data_parts.ts:89`, types imported | `ConsumeChatV2.handlePin` creates citation with `snippet: ''`. Side panel + NumberedCitation tooltip always show empty source. The rich parts emitted in onFinish are sent down the wire and dropped on the floor | **High** | Modify `ConsumeChatV2` to subscribe to `data-citation` parts from `message.metadata.unstable_data`, build a `Map<index, CitationPart>`, pass into `CitationCtx` so `handlePin` can look up snippet/layer at click time. |
| O4 | **`/api/chat/consume/regenerate` endpoint has zero callers** | `regenerate/route.ts` | Action bar `Reload` calls assistant-ui's runtime, which re-POSTs to normal consume route with truncated history. The dedicated truncation endpoint is dead code. Result: regenerate succeeds but old assistant messages from the previous attempt are still in `conversation_messages`, so reload restores both attempts | **High** | Either delete the endpoint and accept duplicate-message growth, OR wire client to call truncate-then-reload. The truncation runs server-side from message ID, so client needs to call it before runtime.reload(). |
| O5 | **`consumeSystemPromptV2` never imported** | `lib/synthesis/prompts/synthesis_prompt_v2.ts` | Grep returns only the file itself. Single-model strategy still uses base `consumeSystemPrompt`. The "use SIG.MSR.NNN format, UI numbers them" instruction is not in the live prompt — model citation discipline left to legacy prompt only | **High** | Wire `consumeSystemPromptV2` into `single_model_strategy.ts` when flag is on or when synthesis stack is V2-aware. |
| O6 | **Panel mode UI affordance missing in V2** | `panel_strategy.ts`, `PanelConfidenceRibbon`, `PanelDissentTabs` all built | No `panel_opt_in` toggle in `ConsumeChatV2.V2Composer`. Legacy chat has the checkbox. Therefore γ1 ribbon/dissent and β9 honest panel streaming are server-ready but a user cannot invoke panel mode | **Critical** | Add a "Panel" toggle near the send button (super_admin only, mirror Legacy). Wire into V2ChatRuntime's `body` callback. |
| O7 | **`data-stage` / `data-tool` parts not consumed** | route emits them, schema declared | `ConsumeChatV2` never subscribes. No StageStepper or ToolCallCard component exists. The plan's headline "pipeline progress visible" feature is invisible in V2 | **Critical** | Build `StageStepper.tsx` + `ToolCallCard.tsx`, render them in `V2Message` from `dataParts.filter(d => d.type==='data-stage' || d.type==='data-tool')`. Multi-file. |
| O8 | **`PredictionLogModal` POST will 403 every time** | `app/api/predictions/route.ts:47` `WHERE qts.user_id=$2` | `query_trace_steps` table has no `user_id` column written by `lib/trace/writer.ts`. The ownership check joins on a column that's never populated. | **Critical** | Two options: (a) add `user_id` column to `query_trace_steps` + writer + migration; (b) authorize via `conversations.user_id` joined through `conversation_id`. Multi-file. |
| O9 | **Streamdown not used in V2** | `MarkdownContent.tsx` swapped to streamdown at α2 | `V2AssistantText` uses `<p className="whitespace-pre-wrap">`; never imports MarkdownContent or streamdown. All α2 plumbing for KaTeX/GFM/code blocks reaches only ConsumeChatLegacy | **High** | Replace `V2AssistantText`'s `<p>` with `<MarkdownContent>`, ensuring citation substitution still happens (pre-process the markdown or post-process via rehype plugin). Risky because citation chips are JSX, not markdown nodes. Multi-file. |
| O10 | **`writeConversationMessages` never receives `lastAssistantMetadata`** | `conversation_writer.ts:31`, called from `route.ts:1040` | Parameter exists; route call site doesn't pass it. Restored messages from `loadConversationMessagesV2` have `metadata = {}`. Per-message drawer shows `—` for everything after reload | **High** | Single-file: build the metadata object at finish (model, queryId, planning_latency_ms, cost data, citation_gate) and pass through. |
| O11 | **GCS signed-URL path stubbed** | `app/api/uploads/sign/route.ts:53-58` | Inline `TODO(§M.1)` comment; falls through to `/api/uploads/store/[token]` in-memory store even when `GCS_BUCKET_NAME` is set | **High** | Implement the documented stub. §M.1 has been listed as deferred since β5 close. |
| O12 | **Vertex AI PDF extraction hardcoded to fixture** | `pdf_extractor.ts:71-72` `// For now, fall back to fixture even when credentials exist` | Direct return of `fixtureExtract` from `vertexExtract` | **High** | Wire actual Document AI call per the in-file TODO. |
| O13 | **`pending_streams_writer.onEvent()` is called exactly once** | `route.ts:869`, writer at `pending_streams_writer.ts:58` | Counter increments only for the pre-stream data-part block. Subsequent stage/tool emissions inside `createUIMessageStream.execute` don't bump `onEvent`. The `last_event_seq` column thus drifts away from accurate position. | **Low** | Wire `onEvent()` after each `writer.write` call. |
| O14 | **Cloud Scheduler reaper for `pending_streams` not provisioned (§M.4)** | migration 063 deployed; cron job not | TTL rows leak indefinitely until table grows | **Medium** | Provision Cloud Scheduler job per `progress §M.4`. |
| O15 | **Edit (`ActionBarPrimitive.Edit`) is hover-only** | `V2Message.tsx` lines 366, 367 use `opacity-0 group-hover:opacity-100` | On touch devices there's no hover. The action bar — including edit, regenerate, copy, details (ⓘ) — never appears | **High** | Always-show on mobile; or use focus-within / tap-to-reveal. |
| O16 | **No mid-conversation autoTitling read by V2** | `route.ts:807-822` generates title; V2 sidebar reloads via `fetch /api/conversations` but only on initial mount | After first turn, title is set in DB but `ConversationSidebar` doesn't refresh | **Medium** | Subscribe `data-persistence` to trigger sidebar reload, or move reload to a per-conversation invalidation event. |

## §3 — Testing dimensions beyond UI/UX

### A — Done and verified

- Unit + component + integration: 563 unit pass at 159872b (PM2 evidence).
- α2 streamdown render unit tests (12).
- β2 conversation_writer round-trip unit (9).
- β7 abort propagation (21).
- γ7 stream-resume writer mechanics (14).
- PM1 red-team probes (15).

### B — Done structurally but not in live environment

- E2E (Playwright): 96 of 116 specs auth-gated and skipped in §M.11 (only 20/20 ran in chromium).
- Perf budgets: soft-gated; never measured against running dev server with real provider.
- a11y axe-core: programmatic only; no NVDA or VoiceOver pass.
- Mobile: Playwright profiles ran but no physical device.
- Visual baselines: 59 spec authored, 0 image baselines committed.

### C — Authored as placeholders only

- Provider fixtures (`tests/fixtures/chat-v2/providers/`): all `_fixture_status: TODO-record`.
- k6 load test directory: `.gitkeep` only.

### D — Not done at all

- k6 steady-state / burst / sustained / multi-modal-storm / stream-resume-storm.
- Stryker mutation tests on critical paths.
- Lighthouse CI run.
- Manual screen-reader audit (NVDA + VoiceOver desktop + VoiceOver iOS).
- Physical-device touch testing (iPhone Safari / Android Chrome).
- Cross-browser E2E with auth (Firefox + WebKit).
- Provider-drift weekly CI.
- OWASP ZAP scan.

### Beyond plan §9 — dimensions not explicitly called out but matter

| Dimension | Severity | Why it matters |
|---|---|---|
| Data integrity round-trip (write conv → reload → assert message content + metadata equal) | ESSENTIAL | O10 makes this fail today — metadata round-trip is broken. |
| Multi-tab same conversation (write conflicts, optimistic UI divergence) | IMPORTANT | β2's write-through is per-request; two tabs streaming into the same conversation race the row trigger. |
| Mid-stream submit during tool fetch (not just during synthesis) | IMPORTANT | β3 covers synthesis abort; tool fetch abort not E2E-covered. |
| Stream resume during a session active in a *different* tab | IMPORTANT | sessionStorage is per-tab; cross-tab leaks could mis-restore. |
| Cross-provider parity: reasoning shape, citation acceptance, multi-modal acceptance | ESSENTIAL | Gemini and Anthropic emit reasoning differently; nothing in the test suite covers Gemini reasoning chunks specifically. |
| Disclosure-tier enforcement at API boundary (not just UI hiding) | ESSENTIAL | super-admin checks in drawer / panel-dissent / prediction-log all rely on `meta.disclosure_tier`; never independently validated server-side. |
| Conversation ownership bypass (read user B's conversation) | ESSENTIAL | β2 `getConversation({userId})` enforces; needs an explicit E2E probe. |
| Stream-resume token forgery | ESSENTIAL | P.5 fix in PM1 — still needs E2E. |
| Multi-modal end-to-end with real GCS + real Vertex | ESSENTIAL | O11 + O12 make this currently impossible to assert. |
| PDF prompt injection round-trip (extracted text reaches synthesis) | ESSENTIAL | red-team P.2 covered architecture but not the actual extracted content path because PDF extractor returns `[PDF FIXTURE] {filename} — N bytes`. |
| Slow-client back-pressure | IMPORTANT | `pending_streams_writer` debounces at 100ms; behavior under 5s/chunk client never tested. |
| Long conversation (50 turns) with HISTORY_COMPRESSION on | IMPORTANT | Flag is dormant; assertion that turn 5 references turn 1 only verified at history_compression unit level, not E2E. |
| Long reasoning (5k+ reasoning tokens) on Anthropic + Gemini thinking | IMPORTANT | Token-count estimation `chars/4` — heavy under-count on Sanskrit / multilingual. |
| Empty / malformed provider response | IMPORTANT | Retry policy verified; downstream UI rendering empty assistant message not asserted. |
| Provider 429 with Retry-After across QG6.1 fallback chain | ESSENTIAL | red-team P.3 unit-level; live behavior unverified. |
| Cancellation race (user submits B while A streaming) | ESSENTIAL | β3 unit; A's onFinish persistence may corrupt B's conversation_messages row order. |
| Stream resume after dirty disconnect (network partition vs. tab close) | IMPORTANT | Both paths share the same client logic; unverified in live env. |
| `conversation_messages` accumulating after regenerate (O4 consequence) | HIGH | E2E: regenerate 5×, reload, assert visible messages == expected count. |

## §4 — Cross-cutting feature dependencies

Pairs where bug-A masks the symptom of bug-B (or makes it untestable):

1. **O7 (no stage UI subscriber) masks β9 panel streaming events** — even if β9 sends member events, no UI renders them, so panel "honest streaming" can't be visually verified.
2. **O6 (no panel UI) masks γ1 (panel ribbon)** — γ1 is unreachable until O6 is fixed; γ1's tests are structural-only.
3. **O5 (V2 prompt orphan) masks β4 citation rendering quality** — without the SIG.MSR.NNN instruction in the prompt, model may emit footnote-style `[1]` directly, breaking the regex `SIG\.MSR\.\d{3}` in `renderWithCitations`.
4. **O3 (citation snippet missing) masks β4 hover tooltip value** — NumberedCitation hover tooltip will always be empty even if the user successfully gets citations to render.
5. **O1 (no `data-cost`) masks γ6 (cost-visibility flag)** — the flag governs visibility, but the underlying value never arrives at the client; flipping the flag will show `—`.
6. **O10 (metadata not persisted) masks β6 + γ5 on reload** — first-render after reload, drawer is hollow; trace link absent.
7. **O8 (predictions 403) masks γ3 UX** — the button works, modal opens, user fills, submits, gets a 403 toast. End-to-end never succeeds.
8. **O12 (PDF fixture) masks β5 PDF feature** — uploads succeed, model receives `[PDF FIXTURE] filename — N bytes`, answers garbage. Test ran with fixture; bug only shows in live use.
9. **O11 (fake-gcs in prod) masks β5 image-survives-multi-turn** — pod recycle or revision rollover wipes the in-memory Map between turns. Multi-turn test ran in same process so passed.
10. **O4 (regenerate truncation orphan) masks β1's conversation hygiene** — regenerate appears to work but accumulates dead turns; manifests as confusing reload after multiple regenerates.
11. **O15 (action bar hover-only) masks β1 + β6 entirely on mobile** — γ9 mobile tests assert layout, not hover-affordance reachability.
12. **O7 (no stage UI) masks the entire "real time pipeline progress" claim of α3** — the whole point of stage parts is invisible.

## §5 — Recommended verification matrix

| Pri | Concern | Method | Effort | Owner |
|---|---|---|---|---|
| P0 | O1: emit `data-cost` part on synthesis finish | new automated integration test + code wiring required first | medium | executor |
| P0 | O3: V2 subscribes to `data-citation` parts | new component test + wiring | medium | executor |
| P0 | O6: add panel-mode UI affordance in V2 composer | new component test + wiring | medium | executor |
| P0 | O7: render `data-stage` + `data-tool` parts in V2 (StageStepper + ToolCallCard) | new components + tests + wiring | large | executor |
| P0 | O8: fix prediction-ownership SQL or add `user_id` to `query_trace_steps` | migration + writer + route fix + tests | large | executor |
| P0 | O10: pass `lastAssistantMetadata` from route to `writeConversationMessages` | unit test + wiring | small | executor |
| P0 | O5: wire `consumeSystemPromptV2` into single_model_strategy | unit test + small refactor | small | executor |
| P0 | O15: action bar reachable on touch | component test + CSS fix | small | executor |
| P0 | Data-integrity round-trip E2E (write→reload→assert metadata equal) | new Playwright spec | medium | executor |
| P0 | Conversation ownership bypass E2E (user A reads user B) | new Playwright spec | medium | executor |
| P0 | Multi-tab race (two tabs same conversation, sequential submits) | new Playwright spec | medium | executor |
| P0 | Production smoke against live providers: send a real query, assert drawer fields populate | manual operator + observatory | small | operator |
| P1 | O2: emit `data-observability` part | small wiring | small | executor |
| P1 | O4: decide regenerate truncation policy + wire or delete | architecture choice + small change | small | operator first, executor after |
| P1 | O9: V2 uses Streamdown for markdown rendering | medium refactor | medium | executor |
| P1 | O11: GCS signed-URL implementation | API integration | medium | executor |
| P1 | O12: Vertex AI Document Understanding integration | API integration | medium | executor |
| P1 | O14: pending-streams reaper Cloud Scheduler job | infra | small | operator |
| P1 | O16: sidebar live-refresh after first turn | small wiring + component test | small | executor |
| P1 | Manual NVDA screen-reader pass | manual | medium | operator |
| P1 | Manual VoiceOver desktop pass | manual | medium | operator |
| P1 | Manual VoiceOver iOS pass | manual | medium | operator |
| P1 | Physical-device touch test (iPhone Safari + Android Chrome) | manual | medium | operator |
| P1 | Lighthouse CI run against running dev server | observability metric | medium | executor |
| P1 | Auth-gated Playwright run (currently 96 skipped) | re-run with valid session | medium | operator |
| P1 | k6 steady-state 100-user, 10-min load test | k6 script + run | large | operator |
| P1 | k6 burst 500-user, 2-min load test | k6 script + run | large | operator |
| P1 | k6 stream-resume disconnect-reconnect 100× | k6 script + run | large | operator |
| P1 | Provider 429 + Retry-After live integration | observatory + chaos | medium | operator |
| P1 | Provider 503 mid-stream live integration | observatory + chaos | medium | operator |
| P1 | Cross-provider reasoning parity (Anthropic vs Gemini thinking) | new component test + fixture | medium | executor |
| P1 | Slow-client back-pressure (5s/chunk) | new Playwright test | medium | executor |
| P1 | Long reasoning (5k tokens) UX | new Playwright test | medium | executor |
| P1 | Long conversation (50 turns) with HISTORY_COMPRESSION_ENABLED | E2E + flag flip | medium | executor |
| P1 | Cancellation race (submit B while A still streaming) | new Playwright spec | medium | executor |
| P1 | Stream-resume dirty disconnect (network partition) | new Playwright + Toxiproxy | medium | executor |
| P1 | PDF prompt injection round-trip | new integration test (after O12) | medium | executor |
| P1 | Stream-resume token forgery E2E | new Playwright spec | medium | executor |
| P2 | Provider drift weekly CI workflow | infra + budget | medium | operator |
| P2 | Stryker mutation on critical paths | infra + tooling | large | executor |
| P2 | OWASP ZAP scan | infra + tooling | medium | operator |
| P2 | Provider contract fixture recording (real keys) | scripted record run | medium | operator |
| P2 | Visual regression baseline capture (59 specs) | MARSYS_UPDATE_VISUALS run | medium | operator |
| P2 | Multi-modal storm (50 concurrent users) | k6 + observatory | large | operator |
| P2 | Empty / malformed provider response handling | fixture + unit | small | executor |
| P2 | Resume after browser process kill (vs tab close) | manual | small | operator |

---

*End CHAT_V2_VERIFICATION_AUDIT_v1_0 DRAFT.*
