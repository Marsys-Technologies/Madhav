---
artifact: CHAT_V2_TEST_STRATEGY_v1_0
name: CHAT V2 BIG BANG — TEST STRATEGY
canonical_id: CHAT_V2_TEST_STRATEGY
version: 1.0
status: CURRENT
authored: 2026-05-16
author: Claude (PA1 executor session)
governing_plan: 00_ARCHITECTURE/CHAT_V2_PLAN_v1_0.md §9
workstream: chat-v2-bigbang
---

# CHAT V2 TEST STRATEGY — v1.0

This document operationalises PLAN §9 (Test strategy) into a concrete, path-specific test plan. Every section maps directly to a §9.2.N category. Executor sessions use this as the authoritative reference for where to place tests and what to name them.

---

## §1 Fixture library root

All chat-v2 fixtures live under:

```
platform/tests/fixtures/chat-v2/
├── providers/                    # Provider record-replay (one subdir per provider)
│   ├── anthropic/
│   ├── anthropic_thinking/
│   ├── gemini_pro/
│   ├── gemini_thinking/
│   ├── openai/
│   ├── deepseek_v4/
│   ├── deepseek_r1/
│   └── nim/
├── conversations/                # Multi-turn conversation fixtures
├── multimodal/                   # Image + PDF payload fixtures
├── validator/                    # Citation gate + validator output fixtures
├── panel/                        # Panel-mode multi-member + adjudicator fixtures
├── streaming-chunks/             # Chunk-size variant streams
│   ├── 1char.json                # 1-char-per-chunk stream
│   ├── small.json                # ~50-char chunks
│   ├── large.json                # ~500-char chunks
│   └── mixed.json                # Provider-quirk mixed sizes
├── spike/                        # α0 spike fixtures
│   └── anthropic_thinking_6k.json   # 6000-token thinking-model response (TODO-record)
├── pdfs/                         # PDF upload test payloads
└── images/                       # Image upload test payloads
```

Provider fixture file naming convention: `<scenario>.json`

Scenario names per provider:
- `quick_nonstreaming.json`
- `long_streaming_4k.json`
- `reasoning_2k.json`
- `tool_call_3tools.json`
- `multimodal_image.json`
- `multimodal_pdf.json`
- `error_429_retry_after.json`
- `error_503.json`
- `error_empty_response.json`

All placeholder fixtures are marked with `"_fixture_status": "TODO-record"` at the top level of the JSON and contain realistic-shape skeleton data, not real provider responses. Real responses recorded in §M manual intervention.

---

## §2 Unit tests (vitest)

**Location**: `platform/tests/unit/chat-v2/` — mirrors `platform/src/` structure.

**Tool**: vitest (existing `vitest.config.ts`).

**Coverage target**: ≥90% lines, ≥85% branches on all new chat-v2 code.

### §2.1 File map by work item

| Work item | Test file(s) | Surfaces under test |
|---|---|---|
| α3 | `platform/tests/unit/chat-v2/streams/data_parts.test.ts` | Zod schema validation for all data part variants (StagePart, ToolPart, CostPart, ObservabilityPart, CitationGatePart, PersistencePart) |
| α4 | `platform/tests/unit/chat-v2/synthesis/history_building.test.ts` | `convertToModelMessages` round-trip; UIMessage with text+reasoning+tool-call parts; no part loss |
| α5 | `platform/tests/unit/chat-v2/synthesis/provider_quirks.test.ts` | Retry table: transient 503 → retried; persistent 503 → fallback; 4xx → not retried |
| α6 | `platform/tests/unit/chat-v2/config/feature_flags.test.ts` | `MARSYS_FLAG_CHAT_V2_ENABLED` exported with correct default |
| β3 | `platform/tests/unit/chat-v2/streams/interrupt_semantics.test.ts` | Cancel-and-replace timing logic |
| β8 | `platform/tests/unit/chat-v2/synthesis/history_compression.test.ts` | Short / long / boundary-crossing conversations; cache hit/miss |
| β10 | `platform/tests/unit/chat-v2/synthesis/streaming_citation_validator.test.ts` | Hard-fail path; soft-fail path; pass path; mutation targets |
| γ3 | `platform/tests/unit/chat-v2/ppl/prediction_detector.test.ts` | Pattern detection on corpus; false-positive rate |
| α2 | `platform/tests/unit/chat-v2/streaming/streamdown_render.test.ts` | Incomplete code fences (2/5/10 chunks); incomplete KaTeX; incomplete table; mixed stream |

**Cumulative targets**: α ≥80, β ≥120, γ ≥180.

---

## §3 Component tests (vitest + React Testing Library + jsdom)

**Location**: `platform/tests/components/chat-v2/`

**Tool**: vitest with jsdom environment + React Testing Library.

### §3.1 File map by component

| Component | Test file | Key assertions |
|---|---|---|
| StageStepper | `stage_stepper.test.tsx` | Each stage data part advances stepper; `done` marks step green; `error` marks red |
| ToolCallCard | `tool_call_card.test.tsx` | `pending` → `running` → `done` transitions; ok_count / err_count displayed |
| ReasoningDrawer | `reasoning_drawer.test.tsx` | Expands/collapses; live token count; collapse default at >2k tokens (γ2) |
| ElapsedTimer | `elapsed_timer.test.tsx` | Tick from first reasoning delta; format HH:MM:SS |
| NumberedCitation | `numbered_citation.test.tsx` | Renders `[N]` superscript; hover triggers CitationPreview |
| CitationSidePanel | `citation_side_panel.test.tsx` | Click pins citation; multi-pin; unpin |
| DisclosureTierBadge | `disclosure_tier_badge.test.tsx` | Correct tier labels and colours per tier |
| ValidatorFailureBand | `validator_failure_band.test.tsx` | Hard-fail renders red band with issues list |
| ValidatorFooterChip | `validator_footer_chip.test.tsx` | Soft-fail renders footer chip |
| PerMessageDetailsDrawer | `per_message_details_drawer.test.tsx` | All fields rendered; cost hidden below super_admin (γ6) |
| PanelDissentTabs | `panel_dissent_tabs.test.tsx` | Toggle shows member answers; disclosure tier check |
| PanelConfidenceRibbon | `panel_confidence_ribbon.test.tsx` | Confidence value displayed |
| PredictionLogModal | `prediction_log_modal.test.tsx` | Pre-filled fields; submit writes to API |
| MultiModalUploader | `multimodal_uploader.test.tsx` | Drop/paste/picker; image preview; PDF file-card |
| ConversationListSidebar | `conversation_list_sidebar.test.tsx` | List renders; archive action; new-conversation button |

**Cumulative targets**: α ≥15, β ≥30, γ ≥45.

---

## §4 Integration tests (vitest with module boundaries)

**Location**: `platform/tests/integration/chat-v2/`

**Tool**: vitest with real module imports but mocked network/DB calls.

### §4.1 File map by boundary

| Boundary | Test file | Key scenarios |
|---|---|---|
| route ↔ adapter | `route_adapter_boundary.test.ts` | Fixture response flows through route → adapter → UIMessage stream; data parts emitted |
| adapter ↔ provider (replay) | `adapter_provider_replay.test.ts` | Each provider fixture replayed; stream events match expected shape |
| persistence round-trip | `persistence_write_read.test.ts` | Write conversation + messages; read back; confirm identity |
| history_compression | `history_compression_integration.test.ts` | Mocked Haiku compresses tail; boundary crossing triggers recompute |
| stream_resume | `stream_resume_happy_path.test.ts` | Partial write → resume endpoint → suffix streams → client reconciles |
| citation_validator wired | `citation_validator_wired.test.ts` | `streamText` mock emits malformed citation → validator fires error data part |
| fixture-mode adapter | `fixture_mode_adapter.test.ts` | `MARSYS_FIXTURE_MODE=true` routes reads to fixture files instead of providers |
| data parts from route | `route_data_parts_emission.test.ts` | Route emits stage/tool/cost/observability/persistence parts for a fixture query |
| UIMessage preservation | `uimessage_e2e_preservation.test.ts` | Text + reasoning + tool-call parts survive history-building round-trip |
| abort propagation | `abort_propagation.test.ts` | AbortSignal cancels tool fetches + panel + adapter within 200ms |

**Cumulative targets**: α ≥10, β ≥30, γ ≥40.

---

## §5 End-to-end tests (Playwright)

**Location**: `platform/tests/e2e/chat-v2/`

**Config**: `platform/tests/e2e/chat-v2/playwright.config.ts`

**Browser matrix**: Chromium (always), Firefox (from β), WebKit (from β), plus two mobile viewport profiles.

### §5.1 Mobile profiles

```ts
// playwright.config.ts mobile profiles
{ name: 'Mobile Safari 375', use: { ...devices['iPhone SE'] } },
{ name: 'iPad Safari 768', use: { ...devices['iPad (gen 7)'] } },
```

### §5.2 File map by scenario

| File | Scenarios | Active from |
|---|---|---|
| `spike.spec.ts` | streaming completion; reasoning drawer presence; scroll position after stream | α0 |
| `send_and_stream.spec.ts` | Compose → submit → stream → completion | α7 |
| `abort.spec.ts` | Stop button during stream; stop during tool-fetch; stop during panel | β7 |
| `edit_regenerate.spec.ts` | Edit first / middle / last message; regenerate; branching nav; edit-cancel | β1 |
| `mid_stream_interrupt.spec.ts` | Submit while streaming → cancel prior within 300ms → new query begins | β3 |
| `conversation_persistence.spec.ts` | Reload preserves; list shows all; archive works; persistence ack in stream | β2 |
| `multimodal.spec.ts` | Image upload + display; PDF upload + extraction; multi-turn survival | β5 |
| `panel_mode.spec.ts` | Panel first-stage-event <1s; dissent toggle; adjudicator streams | β9, γ1 |
| `citations.spec.ts` | Inline `[N]` render; hover preview; click pins in side panel | β4 |
| `validator_failure.spec.ts` | Hard-fail red band; soft-fail footer chip; super-admin detail | β10, γ4 |
| `prediction_logging.spec.ts` | Detector fires on test corpus; modal E2E; row lands in DB | γ3 |
| `observability_deep_link.spec.ts` | "View trace" link opens observatory with correct query_id | γ5 |
| `cost_visibility.spec.ts` | Cost shown to super-admin; hidden to lower tiers | γ6 |
| `stream_resume.spec.ts` | Kill tab mid-stream; reload; resume at correct position | γ7 |
| `a11y/axe.spec.ts` | axe-core WCAG 2.1 AA audit on every chat page | α1 |
| `a11y/keyboard_nav.spec.ts` | Tab through all interactive elements; focus visible; Enter/Esc drawers | γ8 |
| `perf/web_vitals.spec.ts` | TTFB <800ms; FCP <1.5s; LCP <2.5s; INP <200ms; CLS <0.1 | α1 |
| `perf/streaming.spec.ts` | TTFT <1.5s; first-stage-event <500ms; frame <16ms; ≥80 t/s; memory <30MB | α1 |
| `mobile/mobile_375.spec.ts` | Full behavioral parity at 375px | γ9 |
| `mobile/mobile_768.spec.ts` | Full behavioral parity at 768px | γ9 |
| `security/auth_bypass.spec.ts` | Anonymous + cross-user access to conversation routes | β2 |
| `security/xss.spec.ts` | Script injection in composer, markdown output, citation, filename | β5 |
| `flag_switch.spec.ts` | Flag-off renders legacy ConsumeChat; flag-on renders ConsumeChatV2 | α7 |

**Cumulative targets**: α ≥10, β ≥25, γ ≥40.

---

## §6 Visual regression tests

**Location**: `platform/tests/e2e/chat-v2/__visuals__/`

**Tool**: Playwright screenshot diff. Threshold: 0.1% pixel delta.

**Viewports**: 1280px (desktop), 768px (tablet), 375px (mobile).

**Theme**: Modern Dark Pro.

### §6.1 Baseline states

| State | Filename prefix | Added in |
|---|---|---|
| Empty thread | `empty_thread` | α1 |
| Composer focused | `composer_focused` | α1 |
| Streaming in progress | `streaming_in_progress` | α2 |
| Complete message | `complete_message` | α1 |
| Reasoning expanded | `reasoning_expanded` | α0 |
| Reasoning collapsed | `reasoning_collapsed` | α0 |
| Citation pinned | `citation_pinned` | β4 |
| Citation side panel open | `citation_side_panel_open` | β4 |
| Panel dissent expanded | `panel_dissent_expanded` | γ1 |
| Panel dissent collapsed | `panel_dissent_collapsed` | γ1 |
| Validator error band | `validator_error_band` | γ4 |
| Validator warning footer | `validator_warning_footer` | γ4 |
| Multi-modal image attached | `multimodal_image_attached` | β5 |
| Multi-modal PDF attached | `multimodal_pdf_attached` | β5 |
| Per-message details drawer | `per_message_details_drawer` | β6 |
| Conversation list sidebar | `conversation_list_sidebar` | β2 |
| Mobile bottom-sheet | `mobile_bottom_sheet` | γ9 |
| Edit mode | `edit_mode` | β1 |
| Regenerate confirmation | `regenerate_confirmation` | β1 |
| Stage stepper active | `stage_stepper_active` | α3 |

Each state × 3 viewports = 60+ baselines at end of γ.

---

## §7 Performance tests

**Location**: `platform/tests/e2e/chat-v2/perf/`

### §7.1 Web Vitals budgets (Lighthouse CI)

| Metric | Budget | CI gate |
|---|---|---|
| TTFB | <800ms | Hard from α |
| FCP | <1.5s | Soft until γ, hard at γ |
| LCP | <2.5s | Soft until γ, hard at γ |
| INP | <200ms | Hard from γ |
| CLS | <0.1 | Hard from α (layout stability critical during streaming) |

Lighthouse CI config: `.lighthouserc.json` at platform root (created in α1).

### §7.2 Custom streaming metrics

| Metric | Budget | Assertion |
|---|---|---|
| Time-to-first-token | <1.5s | Playwright: time between submit and first `textDelta` event in stream |
| Time-to-first-stage-event | <500ms | Playwright: time between submit and first `StagePart` in stream |
| Frame budget under streaming | <16ms/frame | Playwright `page.evaluate` → Performance observer; max frame duration |
| Tokens-per-second render | ≥80 t/s | Playwright: token count / elapsed stream time |
| Memory growth (50-turn conv) | <30MB | Playwright: `jsHeapUsedSize` before vs. after 50-turn replay |

---

## §8 Accessibility tests

**Location**: `platform/tests/e2e/chat-v2/a11y/`

### §8.1 Programmatic (axe-core)

File: `axe.spec.ts`

- Full WCAG 2.1 AA audit injected into every E2E test via a global `afterEach` fixture.
- Zero serious/critical violations allowed (PR-blocking from α1).
- Color contrast checked for: streaming caret, reasoning drawer handle, citation chips, validator error band, disclosure tier badge.

### §8.2 Manual screen-reader passes (γ8 gate)

Document at: `00_ARCHITECTURE/CHAT_V2_A11Y_REPORT.md`

Required passes:
- NVDA + Firefox (Windows) — full streaming conversation
- VoiceOver + Safari (macOS) — full streaming conversation
- VoiceOver + Safari (iOS) — mobile streaming conversation
- Keyboard-only: every interaction reachable; focus order logical; Enter/Esc for drawers; Tab cycling through message list

Note: physical assistive-tech environment may require §M manual intervention.

---

## §9 Load / stress tests (k6)

**Location**: `platform/tests/load/k6/`

Files:
- `steady_state.js` — 100 concurrent, 10 min, <1% error, p95 TTFT <2s
- `burst.js` — 500 concurrent, 2 min, <5% error, no cascade
- `sustained.js` — 200 concurrent, 1h, no memory growth
- `long_conversation.js` — 1 user, 50-turn, compression triggers
- `multimodal_storm.js` — 50 concurrent, image+PDF, GCS p95 <3s
- `stream_resume.js` — 100 disconnect-reconnect cycles, 100% success

CI: Nightly on dogfood + hard gate pre-merge (PM1/PM2).

---

## §10 Provider contract tests

**Location**: `platform/tests/fixtures/chat-v2/providers/{provider}/`

Each provider directory contains the scenario files listed in §1. The record-replay adapter (`MARSYS_FIXTURE_MODE=true`) intercepts provider SDK calls and returns the fixture JSON.

**Fixture-mode adapter location**: `platform/tests/e2e/chat-v2/global-setup.ts` (registers the intercept) + `platform/src/lib/test-utils/fixture_provider_adapter.ts` (implementation).

**Provider drift CI**: `.github/workflows/chat-v2-ci.yml` stage 9 — weekly, dev keys, $20 budget cap, alerts on schema diff.

---

## §11 Chaos / fault injection tests

**Location**: `platform/tests/integration/chat-v2/chaos/`

Files:
- `provider_429_mid_stream.test.ts`
- `provider_503_mid_stream.test.ts`
- `provider_timeout.test.ts` (10s, 30s, 60s variants)
- `network_partition.test.ts` (Toxiproxy — requires Toxiproxy in CI)
- `db_write_failure.test.ts`
- `gcs_upload_failure.test.ts`
- `concurrent_abort_race.test.ts`
- `disclosure_tier_change.test.ts`
- `master_flag_flip_mid_conversation.test.ts`
- `adjudicator_unavailable.test.ts`
- `pending_streams_expiry.test.ts`

Each asserts: error reaches user; no orphan DB state; no silent token waste; kill switch still works.

---

## §12 Security tests

**Location**: `platform/tests/e2e/chat-v2/security/`

| File | Class |
|---|---|
| `xss.spec.ts` | XSS in composer, markdown output, citation, filename |
| `ssrf.spec.ts` | SSRF via citation URL (169.254.x.x) |
| `file_upload_validation.spec.ts` | Zip, executable, polyglot upload |
| `auth_bypass.spec.ts` | Anonymous + cross-user conversation access |
| `conversation_ownership.spec.ts` | User A reads user B's conversation |
| `disclosure_tier_bypass.spec.ts` | Lower tier requests super-admin API data |
| `prompt_injection_input.spec.ts` | Adversarial system-prompt override in user message |
| `prompt_injection_pdf.spec.ts` | Adversarial instructions in extracted PDF text |
| `token_budget_exhaustion.spec.ts` | Sustained 50k-token messages; budget enforcement |
| `resume_token_forgery.spec.ts` | Request resume with another user's query_id |

---

## §13 Mobile / device tests

**Location**: `platform/tests/e2e/chat-v2/mobile/`

Files:
- `mobile_375.spec.ts` — all behavioral parity scenarios at 375px (iPhone SE profile)
- `mobile_768.spec.ts` — tablet layout at 768px (iPad profile)

Specific mobile assertions:
- Composer auto-resize on rotation (no viewport jump)
- Citation bottom-sheet at <768px (not side-panel)
- Sidebar slide-out drawer at <768px
- Reasoning drawer collapse default at <768px
- Touch targets ≥44px (verified via bounding box assertions)
- No iOS input-zoom (font-size ≥16px on all inputs)

---

## §14 Streaming-specific tests

**Location**: `platform/tests/unit/chat-v2/streaming/` + `platform/tests/integration/chat-v2/streaming/`

| Scenario | File | Tool |
|---|---|---|
| 1-char-per-chunk | `chunk_1char.test.ts` | vitest integration |
| 1k-char-per-chunk | `chunk_1k.test.ts` | vitest integration |
| Mixed chunk sizes | `chunk_mixed.test.ts` | vitest integration |
| Incomplete code fence | `streamdown_incomplete_fence.test.ts` | vitest unit |
| Incomplete KaTeX | `streamdown_incomplete_math.test.ts` | vitest unit |
| Incomplete table row | `streamdown_incomplete_table.test.ts` | vitest unit |
| Reasoning interleaved | `reasoning_interleaved.test.ts` | vitest integration |
| Tool call mid-stream | `tool_call_mid_stream.test.ts` | vitest integration |
| Multi-citation (10+) | `multi_citation.test.ts` | vitest integration |
| Abort at byte 0 | `abort_byte_0.spec.ts` | Playwright E2E |
| Abort mid-stream | `abort_mid_stream.spec.ts` | Playwright E2E |
| Abort near end | `abort_near_end.spec.ts` | Playwright E2E |
| Resume from mid-stream | `resume_mid_stream.spec.ts` | Playwright E2E |
| Back-pressure slow client | `backpressure.test.ts` | vitest integration |

---

## §15 Type tests (tsd)

**Location**: `platform/tests/types/chat-v2/`

Files:
- `uimessage_round_trip.test-d.ts` — UIMessage → convertToModelMessages → no lossy narrowing
- `data_part_schemas.test-d.ts` — Zod schemas infer expected TS types
- `query_request_shape.test-d.ts` — QueryRequest shape stability

---

## §16 Snapshot tests

**Location**: `platform/tests/unit/chat-v2/snapshots/`

Files:
- `data_parts_schema_snapshot.test.ts` — JSON schema diffs require explicit review
- `api_response_shape.test.ts` — `/api/chat/consume` response shape stability

---

## §17 Mutation tests (Stryker)

**Location**: `platform/tests/mutation/` (config: `stryker.conf.json` at platform root)

**Paths under mutation**:
- `platform/src/lib/synthesis/streaming_citation_validator.ts`
- `platform/src/lib/adapters/` (abort propagation methods only)
- `platform/src/lib/persistence/conversation_writer.ts`
- `platform/src/lib/ppl/prediction_detector.ts`
- `platform/src/lib/synthesis/history_compression.ts`
- `platform/src/lib/persistence/pending_streams_writer.ts` (stream_resume token-position logic)

**Target score**: ≥75% mutation score on all listed paths.

**Schedule**: Weekly + pre-merge (PM2 gate).

---

## §18 CI pipeline — stage-to-file mapping

This maps PLAN §9.4 stages to the test files/scripts that discharge them.

| Stage | File(s) | Gate | Active from |
|---|---|---|---|
| 1. Lint + typecheck + unit | `eslint` + `tsc` + `vitest run tests/unit/chat-v2` | Hard | α0 |
| 2. Component + integration | `vitest run tests/components/chat-v2 tests/integration/chat-v2` | Hard | α1 |
| 3. E2E (Chromium) | `playwright test --project=chromium tests/e2e/chat-v2` | Hard | α0 (spike only) |
| 4. E2E (Firefox + WebKit) | `playwright test --project=firefox --project=webkit tests/e2e/chat-v2` | Hard from β | β |
| 5. Visual regression | `playwright test --project=visual tests/e2e/chat-v2/__visuals__` | Hard | α1 |
| 6. a11y (axe-core) | `playwright test tests/e2e/chat-v2/a11y/axe.spec.ts` | Hard from γ8 | γ8 |
| 7. Perf (Lighthouse CI) | `lhci autorun` + `playwright test tests/e2e/chat-v2/perf` | Soft→Hard | α1 (soft), γ (hard) |
| 8. Load / stress (k6) | `k6 run tests/load/k6/*.js` | Soft nightly; Hard pre-merge | PM1 |
| 9. Provider drift | custom drift script against live providers | Soft (alert) | α1 |
| 10. Chaos / fault injection | `vitest run tests/integration/chat-v2/chaos` | Hard pre-merge | PM1 |
| 11. Security | `playwright test tests/e2e/chat-v2/security` | Hard pre-merge | PM1 |
| 12. Mobile (Playwright profiles) | `playwright test --project='Mobile Safari 375' --project='iPad Safari 768'` | Hard from γ9 | γ9 |
| 13. Mutation (Stryker) | `stryker run` | Soft weekly; Hard pre-merge | PM1 |
| 14. Cross-browser smoke | `playwright test --project=staging-smoke` | Hard pre-merge | PM2 |
| 15. Synthetic monitoring | Cloud Scheduler → Observatory | Alerts only | post-merge |

---

## §19 `npm run chat-v2:test` script

Added to `platform/package.json`. Runs the cumulative workstream test set:

```bash
vitest run tests/unit/chat-v2 tests/components/chat-v2 tests/integration/chat-v2 && \
playwright test tests/e2e/chat-v2 --project=chromium
```

Additional scripts:
- `chat-v2:e2e` — Playwright E2E across all browser projects
- `chat-v2:visual` — Visual regression only
- `chat-v2:a11y` — axe-core suite only
- `chat-v2:perf` — Perf (Lighthouse CI + streaming metrics)

---

## §20 Phase exit test gates (condensed reference)

| Phase | Unit | Component | Integration | E2E | Visual |
|---|---|---|---|---|---|
| α | ≥80 | ≥15 | ≥10 | ≥10 | ≥20 |
| β | ≥120 | ≥30 | ≥30 | ≥25 | ≥40 |
| γ | ≥180 | ≥45 | ≥40 | ≥40 | ≥60 |

---

*End CHAT_V2_TEST_STRATEGY_v1_0.md. Authored PA1, 2026-05-16.*
