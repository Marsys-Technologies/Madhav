---
artifact: CHAT_V2_CAPABILITY_REACHABILITY_AUDIT_v1_0
canonical_id: CHAT_V2_CAPABILITY_REACHABILITY_AUDIT
version: 1.0
status: DRAFT
authored: 2026-05-17
author: Claude (Cowork research subagent)
governing_plan: 00_ARCHITECTURE/CHAT_V2_PLAN_v1_0.md v1.1
governing_remediations:
  - 00_ARCHITECTURE/CHAT_V2_REMEDIATION_PLAN_v1_0.md v1.0
  - 00_ARCHITECTURE/CHAT_V2_CHROME_PARITY_PLAN_v1_0.md v1.0
supersedes_partial:
  - 00_ARCHITECTURE/CHAT_V2_VERIFICATION_AUDIT_v1_0.md
  - 00_ARCHITECTURE/CHAT_V2_CHROME_GAP_AUDIT_v1_0.md
purpose: |
  Exhaustive capability reachability audit across all four Chat V2 passes
  (original ship + functional remediation + chrome parity + fix-wave). Inventories
  every component, hook, endpoint, data part, schema, flag, middleware, validator,
  prompt, adapter, migration, test-infra surface and classifies each by whether it
  is REACHABLE in production today, ORPHANED (built but not surfacing), DEAD,
  BACKEND-LEVERAGED, or FLAG-GATED-OFF. Produces a prioritized capability
  surfacing work plan (P0..P3) for fix-wave-extensions.
---

# CHAT V2 — CAPABILITY REACHABILITY AUDIT v1.0

Research-grade, exhaustive reachability audit. No file modifications.

The two predecessor audits (`CHAT_V2_VERIFICATION_AUDIT_v1_0.md`,
`CHAT_V2_CHROME_GAP_AUDIT_v1_0.md`) covered ~32 surfaces between them. This audit
sweeps every chat-v2-era artifact and asks one question per item: **is it
reachable + leveraged in the UI today?** Findings stand on file:line citations.

## §1 — Capability inventory

Type legend:
COMPONENT · HOOK · ENDPOINT · DATA-PART · SCHEMA · FLAG · PROMPT · VALIDATOR ·
MIDDLEWARE · ADAPTER · MIGRATION · TEST-INFRA · DOC.

Status legend:
- **REACHABLE** — wired, used by ConsumeChatV2 (or production server path); user can produce its behaviour.
- **BACKEND-LEVERAGED** — server-side capability that runs on every request even if not user-visible.
- **ORPHANED** — built, imported nowhere or rendered nowhere in V2; user cannot trigger it.
- **DEAD** — imported and rendered but has no behavior (missing handler, broken data-flow, null condition).
- **BACKEND-ORPHANED** — server-side capability that is never called by any caller.
- **FLAG-GATED-OFF** — code present, feature flag default `false` and not flipped.
- **UNCLEAR** — partial path exists; outcome depends on conditions not statically resolvable.

| ID | Capability | Type | Location | Built in | Status |
|---|---|---|---|---|---|
| C1 | ConsumeChat (flag-switch shell) | COMPONENT | `platform/src/components/consume/ConsumeChat.tsx` | original | REACHABLE |
| C2 | ConsumeChatLegacy (legacy path, post-PIV) | COMPONENT | `platform/src/components/consume/ConsumeChatLegacy.tsx` | original | REACHABLE (flag-off) |
| C3 | ConsumeChatV2 (assistant-ui shell) | COMPONENT | `platform/src/components/consume/ConsumeChatV2.tsx` | original | REACHABLE (flag-on) |
| C4 | V2 ConversationSidebar (inlined in C3) | COMPONENT | `ConsumeChatV2.tsx:95-199` | original | REACHABLE |
| C5 | ConversationSidebarV2 (parallel, branded) | COMPONENT | `consume/ConversationSidebarV2.tsx` | chrome-parity | **ORPHANED** (not imported by ConsumeChatV2) |
| C6 | V2Message | COMPONENT | `ConsumeChatV2.tsx:417-704` | original | REACHABLE |
| C7 | V2BranchPicker (alternates nav) | COMPONENT | `ConsumeChatV2.tsx:203-235` | original | REACHABLE (hover-only) |
| C8 | V2RegenerateButton (truncate+reload) | COMPONENT | `ConsumeChatV2.tsx:375-413` | fix-wave | REACHABLE (hover-only) |
| C9 | V2AssistantText (markdown+citation footer) | COMPONENT | `ConsumeChatV2.tsx:306-338` | fix-wave | REACHABLE |
| C10 | V2Composer (pill + paperclip-inside) | COMPONENT | `ConsumeChatV2.tsx:886-1071` | chrome-parity | REACHABLE |
| C11 | AttachmentStrip | COMPONENT | `ConsumeChatV2.tsx:813-882` | original (β5) | REACHABLE |
| C12 | V2BottomBar (Stack/Style + LEL + Tier) | COMPONENT | `ConsumeChatV2.tsx:1152-1187` | chrome-parity | REACHABLE |
| C13 | V2Thread (assistant-ui Viewport wrap) | COMPONENT | `ConsumeChatV2.tsx:1196-1234` | original | REACHABLE |
| C14 | V2QueryIdTracker (publishes queryId for Trace) | COMPONENT | `ConsumeChatV2.tsx:1077-1102` | chrome-parity | REACHABLE |
| C15 | V2StreamResumeTracker | COMPONENT | `ConsumeChatV2.tsx:1109-1148` | original (γ7) | REACHABLE |
| C16 | StageStepper | COMPONENT | `components/chat-v2/StageStepper.tsx` | fix-wave (O3) | REACHABLE (streaming-only) |
| C17 | ToolCallCard (chat-v2/) | COMPONENT | `components/chat-v2/ToolCallCard.tsx` | fix-wave (O3) | REACHABLE (streaming-only) |
| C18 | ToolCallCard (chat/, legacy) | COMPONENT | `components/chat/ToolCallCard.tsx` | original | **ORPHANED** (duplicate; V2 uses chat-v2/ variant) |
| C19 | PanelModeToggle | COMPONENT | `components/chat-v2/PanelModeToggle.tsx` | fix-wave (O2) | REACHABLE |
| C20 | ChatSpikeThread (dev) | COMPONENT | `components/chat-v2/spike/ChatSpikeThread.tsx` | α0 spike | REACHABLE (super-admin /dev/chat-spike) |
| C21 | PerMessageDetailsDrawer (ⓘ drawer) | COMPONENT | `components/chat/PerMessageDetailsDrawer.tsx` | β6 | REACHABLE (hover-only) |
| C22 | NumberedCitation (inline [N] badge) | COMPONENT | `components/chat/NumberedCitation.tsx` | β4 | REACHABLE (rendered in citation footer of V2AssistantText) |
| C23 | CitationSidePanel | COMPONENT | `components/chat/CitationSidePanel.tsx` | β4 | DEAD (rendered conditionally; `onPin` in V2 path is no-op — never produces pinned entries because handlePin is not wired to the runtime) |
| C24 | PanelConfidenceRibbon | COMPONENT | `components/chat/PanelConfidenceRibbon.tsx` | γ1 | REACHABLE (panel mode only) |
| C25 | PanelDissentTabs | COMPONENT | `components/chat/PanelDissentTabs.tsx` | γ1 | REACHABLE (panel mode + dissent toggle) |
| C26 | PredictionLogModal | COMPONENT | `components/chat/PredictionLogModal.tsx` | γ3 | REACHABLE (super-admin only) |
| C27 | ReasoningProgress (γ2 drawer) | COMPONENT | `components/chat/ReasoningProgress.tsx` | γ2 | REACHABLE (thinking-model only) |
| C28 | ValidatorFailureBand | COMPONENT | `components/chat/ValidatorFailureBand.tsx` | γ4 | REACHABLE (citation_gate=fail) |
| C29 | ValidatorFooterChip | COMPONENT | `components/chat/ValidatorFooterChip.tsx` | γ4 | REACHABLE (citation_gate=warn) |
| C30 | MarkdownContent (streamdown) | COMPONENT | `components/chat/MarkdownContent.tsx` | α2 | REACHABLE (V2 uses it via V2AssistantText) |
| C31 | ShareButton | COMPONENT | `components/chat/ShareButton.tsx` | chrome-parity (C.2) | REACHABLE |
| C32 | TraceDrawer | COMPONENT | `components/consume/TraceDrawer.tsx` | chrome-parity (C.2) | REACHABLE (super-admin only) |
| C33 | CommandPalette (⌘K) | COMPONENT | `components/chat/CommandPalette.tsx` | chrome-parity (C.7) | REACHABLE |
| C34 | ShortcutsDialog | COMPONENT | `components/chat/ShortcutsDialog.tsx` | chrome-parity (C.7) | REACHABLE |
| C35 | ModelStylePicker (Stack picker) | COMPONENT | `components/chat/ModelStylePicker.tsx` | chrome-parity (C.3) | REACHABLE |
| C36 | TierPicker | COMPONENT | `components/consume/TierPicker.tsx` | shared, chrome-parity wired | REACHABLE (super-admin) |
| C37 | EmptyState (chart-aware prompts) | COMPONENT | `components/consume/EmptyState.tsx` | chrome-parity (C.4+5) | REACHABLE |
| C38 | ContextUsageCue | COMPONENT | `components/consume/ContextUsageCue.tsx` | chrome-parity (C.8) | REACHABLE (when context_usage in metadata) |
| C39 | PostAnswerProvenance | COMPONENT | `components/consume/PostAnswerProvenance.tsx` | chrome-parity (C.8) | REACHABLE (when provenance in metadata) |
| C40 | ConsumeReportLibraryV2 (saved reports) | COMPONENT | `components/consume/ConsumeReportLibraryV2.tsx` | chrome-parity (C.6) | **ORPHANED** (never imported in ConsumeChatV2; reports prop unused) |
| C41 | LiveReasoningCard | COMPONENT | `components/consume/LiveReasoningCard.tsx` | legacy | **ORPHANED in V2** (legacy SSE marker stream; V2 ignores) |
| C42 | CorrectionNotice | COMPONENT | `components/consume/CorrectionNotice.tsx` | legacy | **ORPHANED in V2** (no `data-correction` part emitted) |
| C43 | OutOfDomainBanner | COMPONENT | `components/consume/OutOfDomainBanner.tsx` | legacy | **ORPHANED in V2** (no `data-out-of-domain` part emitted) |
| C44 | ProvenanceDrawer | COMPONENT | `components/consume/ProvenanceDrawer.tsx` | legacy | **ORPHANED in V2** |
| C45 | ConversationHistoryDrawer / Button | COMPONENT | `components/consume/ConversationHistory*.tsx` | legacy | **ORPHANED in V2** (V2 has its own ConversationSidebar) |
| C46 | LogPredictionAction (legacy) | COMPONENT | `components/consume/LogPredictionAction.tsx` | legacy | **ORPHANED in V2** (γ3 PredictionLogModal supersedes) |
| C47 | DivergenceReport | COMPONENT | `components/consume/DivergenceReport.tsx` | legacy panel | **ORPHANED in V2** |
| C48 | ReportGallery | COMPONENT | `components/consume/ReportGallery.tsx` | legacy | **ORPHANED in V2** |
| C49 | ReportLibrary (legacy version, in `consume/`) | COMPONENT | `components/consume/ReportLibrary.tsx` | legacy | REACHABLE in legacy only; ORPHANED in V2 |
| C50 | ReportReader | COMPONENT | `components/consume/ReportReader.tsx` | legacy | REACHABLE in legacy only; ORPHANED in V2 |
| C51 | SanskritTermSpan | COMPONENT | `components/consume/SanskritTermSpan.tsx` | legacy | **ORPHANED in V2** |
| C52 | StreamingAnswer (legacy renderer) | COMPONENT | `components/consume/StreamingAnswer.tsx` | legacy | REACHABLE in legacy only |
| C53 | AnswerView (legacy) | COMPONENT | `components/consume/AnswerView.tsx` | legacy | REACHABLE in legacy only |
| C54 | PanelAnswerView (legacy panel) | COMPONENT | `components/consume/PanelAnswerView.tsx` | legacy | REACHABLE in legacy only; ORPHANED in V2 (panel renders inline) |
| C55 | ValidatorFailureView (legacy) | COMPONENT | `components/consume/ValidatorFailureView.tsx` | legacy | REACHABLE in legacy only |
| C56 | Composer (legacy gold-rim) | COMPONENT | `components/chat/Composer.tsx` | legacy | REACHABLE in legacy only |
| C57 | ConsumeShell (legacy outer chrome) | COMPONENT | `components/consume/ConsumeShell.tsx` | legacy | REACHABLE in legacy only |
| C58 | ConsumeOverlayPortal | COMPONENT | `components/consume/ConsumeOverlayPortal.tsx` | shared | REACHABLE (wraps both surfaces) |
| C59 | ConversationSidebar (legacy chat/) | COMPONENT | `components/chat/ConversationSidebar.tsx` | legacy | REACHABLE in legacy only |
| C60 | ChatShell | COMPONENT | `components/chat/ChatShell.tsx` | legacy | REACHABLE elsewhere (not consume) |
| C61 | AssistantMessage (legacy renderer helper) | COMPONENT | `components/chat/AssistantMessage.tsx` | legacy | REACHABLE in legacy only |
| C62 | ScrollToBottomButton (brand) | COMPONENT | `components/chat/ScrollToBottomButton.tsx` | legacy | REACHABLE in legacy only; V2 uses inline `<button class="fixed bottom-24…">` |
| C63 | StreamingMarkdown / Markdown (older) | COMPONENT | `components/chat/StreamingMarkdown.tsx`, `chat/Markdown.tsx` | legacy | UNCLEAR (likely orphan; superseded by MarkdownContent) |
| C64 | StreamingDots | COMPONENT | `components/chat/StreamingDots.tsx` | legacy | UNCLEAR |
| C65 | UserMessage / PendingAssistantBubble | COMPONENT | `components/chat/UserMessage.tsx`, `chat/PendingAssistantBubble.tsx` | legacy | UNCLEAR |
| C66 | MessageList / AdaptiveMessageList / VirtualizedMessageList | COMPONENT | `components/chat/MessageList.tsx` etc. | legacy | UNCLEAR (used by `components/build/BuildChat.tsx` only? V2 path doesn't use any of them) |
| C67 | MessageActions | COMPONENT | `components/chat/MessageActions.tsx` | legacy | REACHABLE in legacy only |
| C68 | MessageErrorBoundary | COMPONENT | `components/chat/MessageErrorBoundary.tsx` | legacy | REACHABLE in legacy only |
| C69 | ConsumeRail | COMPONENT | `components/consume/ConsumeRail.tsx` | legacy | REACHABLE in legacy only |
| C70 | SharedConsumeError | COMPONENT | `components/consume/SharedConsumeError.tsx` | shared | REACHABLE (error.tsx) |
| C71 | lifecycle/* (MetadataBadge, StatusPip, etc.) | COMPONENT | `components/consume/lifecycle/*.tsx` | older co3 | REACHABLE in legacy only |
| H1 | useChatPreferences (per-chart stack+style) | HOOK | `hooks/useChatPreferences.ts` | chrome-parity (C.9) | REACHABLE |
| H2 | useChatLifecycle | HOOK | `lib/hooks/useChatLifecycle.ts` | legacy | REACHABLE in legacy only; ORPHANED in V2 |
| H3 | useKeyboardShortcuts | HOOK | `lib/hooks/useKeyboardShortcuts.ts` | legacy | REACHABLE in legacy only; V2 uses inline `useEffect` |
| H4 | useScrollAnchor (lib/) | HOOK | `lib/hooks/useScrollAnchor.ts` | legacy | REACHABLE in legacy only |
| H5 | useScrollAnchor (hooks/) | HOOK | `hooks/useScrollAnchor.ts` | legacy | UNCLEAR (duplicate or different consumer?) |
| H6 | useSidebarState | HOOK | `lib/hooks/useSidebarState.ts` | legacy | REACHABLE in legacy only; V2 uses inline `useState` |
| H7 | useChatSession | HOOK | `hooks/useChatSession.ts` | legacy | REACHABLE in legacy only (assistant-ui replaces it in V2) |
| H8 | useFeedback | HOOK | `hooks/useFeedback.ts` | legacy | REACHABLE in legacy only |
| H9 | useBranches | HOOK | `hooks/useBranches.ts` | legacy | REACHABLE in legacy only; V2 uses BranchPickerPrimitive |
| H10 | useTraceStream | HOOK | `hooks/useTraceStream.ts` | shared (TraceDrawer) | REACHABLE |
| H11 | useHotkeys | HOOK | `hooks/useHotkeys.ts` | legacy | REACHABLE in legacy only |
| H12 | useBuildChatAdapter | HOOK | `hooks/useBuildChatAdapter.ts` | build module | n/a (out of chat-v2 scope) |
| H13 | useAttachments | HOOK | `hooks/useAttachments.ts` | β5 | UNCLEAR (V2 uses inline `useAttachmentManager` in ConsumeChatV2.tsx:721; this `useAttachments` may be the legacy one) |
| H14 | useAttachmentManager (inline in V2) | HOOK | `ConsumeChatV2.tsx:721-809` | β5 | REACHABLE |
| EP1 | POST /api/chat/consume | ENDPOINT | `app/api/chat/consume/route.ts` | core | REACHABLE |
| EP2 | POST /api/chat/consume/regenerate | ENDPOINT | `app/api/chat/consume/regenerate/route.ts` | β1 | REACHABLE (fix-wave wired V2 caller) |
| EP3 | GET /api/chat/consume/resume | ENDPOINT | `app/api/chat/consume/resume/route.ts` | γ7 | REACHABLE (mount-time check) |
| EP4 | POST /api/chat/spike (dev) | ENDPOINT | `app/api/chat/spike/route.ts` | α0 | REACHABLE (super-admin spike) |
| EP5 | POST /api/chat/upload (legacy upload) | ENDPOINT | `app/api/chat/upload/route.ts` | legacy | UNCLEAR (β5 uses /api/uploads/*) |
| EP6 | POST /api/chat/build (build module) | ENDPOINT | `app/api/chat/build/route.ts` | build | n/a |
| EP7 | GET /api/conversations (list) | ENDPOINT | `app/api/conversations/route.ts` | β2 | REACHABLE |
| EP8 | POST /api/conversations (create) | ENDPOINT | `app/api/conversations/route.ts` | β2 | REACHABLE (route does eager create on consume) |
| EP9 | GET /api/conversations/[id] | ENDPOINT | `app/api/conversations/[id]/route.ts` | β2 | REACHABLE |
| EP10 | DELETE /api/conversations/[id] (archive) | ENDPOINT | `app/api/conversations/[id]/route.ts` | β2 | UNCLEAR (no archive button in V2 sidebar) |
| EP11 | GET /api/conversations/[id]/messages (restore) | ENDPOINT | `app/api/conversations/[id]/messages/route.ts` | β2 | REACHABLE |
| EP12 | POST /api/conversations/[id]/feedback | ENDPOINT | `app/api/conversations/[id]/feedback/route.ts` | feedback | UNCLEAR (V2 has no thumbs UI) |
| EP13 | GET/POST /api/conversations/[id]/share | ENDPOINT | `app/api/conversations/[id]/share/route.ts` | share | REACHABLE (via ShareButton) |
| EP14 | POST /api/predictions | ENDPOINT | `app/api/predictions/route.ts` | γ3 | REACHABLE (super-admin only; user_id check fixed in mig 064) |
| EP15 | POST /api/uploads/sign | ENDPOINT | `app/api/uploads/sign/route.ts` | β5 | REACHABLE (but B.11 stub — never returns real signed URL) |
| EP16 | PUT/GET /api/uploads/store/[token] | ENDPOINT | `app/api/uploads/store/[token]/route.ts` | β5 | REACHABLE (fake-gcs path) |
| EP17 | POST /api/admin/cron/reap-pending-streams | ENDPOINT | `app/api/admin/cron/reap-pending-streams/route.ts` | fix-wave (B.12) | **BACKEND-ORPHANED** (Cloud Scheduler job not provisioned — operator follow-up) |
| DP1 | stage data part | DATA-PART | `lib/streams/data_parts.ts:31-38` | α3 | REACHABLE (emitted by route; consumed by V2Message via StageStepper) |
| DP2 | tool data part | DATA-PART | `lib/streams/data_parts.ts:42-51` | α3 | REACHABLE (emitted + consumed by ToolCallCard) |
| DP3 | cost data part | DATA-PART | `lib/streams/data_parts.ts:55-65` | α3 (O1 fix-wave wiring) | REACHABLE (route emits in onFinish; drawer reads from message.content) |
| DP4 | observability data part | DATA-PART | `lib/streams/data_parts.ts:69-75` | α3 | **BACKEND-ORPHANED** (schema declared, no emitter — drawer falls back to meta.queryId) |
| DP5 | citation_gate data part | DATA-PART | `lib/streams/data_parts.ts:79-85` | β10 | REACHABLE (emitted by validator; consumed by V2Message) |
| DP6 | citation data part (β4 rich source) | DATA-PART | `lib/streams/data_parts.ts:89-97` | β4 | UNCLEAR (route emits in onFinish; V2 only counts chips from text — does NOT consume the rich snippet payload; CitationSidePanel.handlePin receives `snippet:''`) |
| DP7 | persistence data part | DATA-PART | `lib/streams/data_parts.ts:101-108` | β2 | REACHABLE (emitted; V2 sidebar does NOT subscribe — sidebar refresh only on mount) |
| DP8 | panel_member data part | DATA-PART | `lib/streams/data_parts.ts:114-124` | γ1 | REACHABLE (panel mode only) |
| DP9 | panel_meta data part | DATA-PART | `lib/streams/data_parts.ts:140-148` | γ1 | REACHABLE (panel mode only) |
| DP10 | prediction_candidate data part | DATA-PART | `lib/streams/data_parts.ts:130-138` | γ3 | REACHABLE (super-admin) |
| S1 | DataPartSchema (Zod discriminated union) | SCHEMA | `lib/streams/data_parts.ts:154-167` | α3 | BACKEND-LEVERAGED |
| S2 | AttachedFile types | SCHEMA | `ConsumeChatV2.tsx:60-70` | β5 | REACHABLE |
| S3 | ConversationSummary types | SCHEMA | `ConsumeChatV2.tsx:76-82` | β2 | REACHABLE |
| S4 | CitationPart (re-export from data_parts) | SCHEMA | `lib/citations/citation_data_part.ts` | β4 | REACHABLE |
| S5 | StagePart / ToolPart / CostPart types | SCHEMA | re-export | α3 | REACHABLE |
| F1 | CHAT_V2_ENABLED (master flag) | FLAG | `feature_flags.ts:85, 150` | α6 | REACHABLE (flipped true 2026-05-17) |
| F2 | HISTORY_COMPRESSION_ENABLED | FLAG | `feature_flags.ts:89, 152` | β8 | **FLAG-GATED-OFF** (default false; never flipped) |
| F3 | COST_VISIBILITY_FOR_USERS | FLAG | `feature_flags.ts:93, 154` | γ6 | **FLAG-GATED-OFF** (default false) |
| F4 | CITATION_GATE_OVERRIDE | FLAG | `feature_flags.ts:64, 138` | pre-existing | REACHABLE (route reads on every request) |
| F5 | PANEL_MODE_ENABLED | FLAG | `feature_flags.ts:2, 96` | pre-existing | REACHABLE (default true) |
| F6 | PANEL_DEGRADE_2_OF_3 | FLAG | `feature_flags.ts:27, 115` | Phase 7 | FLAG-GATED-OFF (panel internal; default false) |
| F7 | CHECKPOINT_*_ENABLED / *_FAIL_HARD (7 flags) | FLAG | `feature_flags.ts:19-25, 107-113` | Phase 6 | FLAG-GATED-OFF (legacy LLM checkpoints; not chat-v2 scope) |
| F8 | CONSUME_UI_V2_ENABLED | FLAG | `feature_flags.ts:82, 148` | AIOps Phase 3 | REACHABLE (default true) |
| F9 | OBSERVATORY_ENABLED | FLAG | `feature_flags.ts:69, 140` | Phase O | REACHABLE |
| F10 | LEL_CONTEXT_ENABLED | FLAG | `feature_flags.ts:54, 133` | M4 | REACHABLE (route reads; V2 bottom bar reads & writes effective state via body) |
| PR1 | consumeSystemPrompt (base) | PROMPT | `lib/synthesis/prompts/*` | pre-existing | REACHABLE |
| PR2 | consumeSystemPromptV2 + CITATION_APPENDIX | PROMPT | `lib/synthesis/prompts/synthesis_prompt_v2.ts` | β4 (B.9 wire) | REACHABLE (appended when CHAT_V2_ENABLED=true) |
| PR3 | adjudicator_prompt_v1 (panel mode) | PROMPT | `lib/synthesis/prompts/adjudicator_prompt_v1.ts` | β9 | REACHABLE (panel mode) |
| V1 | streaming_citation_validator | VALIDATOR | `lib/synthesis/streaming_citation_validator.ts` | β10 | BACKEND-LEVERAGED (route calls in onFinish) |
| V2 | b11_guard | VALIDATOR | `lib/synthesis/b11_guard.ts` | pre-existing | BACKEND-LEVERAGED |
| V3 | citation_check (older) | VALIDATOR | `lib/synthesis/citation_check.ts` | pre-existing | BACKEND-LEVERAGED |
| V4 | token_caps (per query class) | VALIDATOR | `lib/synthesis/token_caps.ts` | pre-existing | BACKEND-LEVERAGED |
| MW1 | history_compression (Haiku summarizer) | MIDDLEWARE | `lib/synthesis/history_compression.ts` | β8 | FLAG-GATED-OFF (only runs when F2 true) |
| MW2 | provider_quirks (per-provider retry table) | MIDDLEWARE | `lib/synthesis/provider_quirks.ts` | α5 | BACKEND-LEVERAGED |
| MW3 | conversation_writer (write-through + verify) | MIDDLEWARE | `lib/persistence/conversation_writer.ts` | β2 | BACKEND-LEVERAGED (route calls in onFinish) |
| MW4 | pending_streams_writer (γ7) | MIDDLEWARE | `lib/persistence/pending_streams_writer.ts` | γ7 | BACKEND-LEVERAGED (route wires onTextDelta) |
| MW5 | resolveAttachments + fakeGcsRetrieve | MIDDLEWARE | `route.ts:137-159`, `lib/multimodal/fake_gcs_store.ts` | β5 | BACKEND-LEVERAGED (always falls through to fake-gcs) |
| MW6 | upload_validator | MIDDLEWARE | `lib/multimodal/upload_validator.ts` | β5 | BACKEND-LEVERAGED |
| MW7 | pdf_extractor (with Vertex stub) | MIDDLEWARE | `lib/multimodal/pdf_extractor.ts` | β5 | BACKEND-LEVERAGED (always fixture path — Vertex code TODO) |
| MW8 | prediction_detector (regex scan) | MIDDLEWARE | `lib/ppl/prediction_detector.ts` | γ3 | BACKEND-LEVERAGED |
| MW9 | prediction_writer (client POST wrapper) | MIDDLEWARE | `lib/ppl/prediction_writer.ts` | γ3 | REACHABLE (called by PredictionLogModal) |
| MW10 | citation_data_part helpers | MIDDLEWARE | `lib/citations/citation_data_part.ts` | β4 | BACKEND-LEVERAGED (route emits) |
| AD1 | adapter_anthropic + abortSignal forward | ADAPTER | `lib/adapters/providers/adapter_anthropic.ts` | β7 | BACKEND-LEVERAGED |
| AD2 | adapter_gemini + abortSignal forward | ADAPTER | `lib/adapters/providers/adapter_gemini.ts` | β7 | BACKEND-LEVERAGED |
| AD3 | adapter_openai + abortSignal forward | ADAPTER | `lib/adapters/providers/adapter_openai.ts` | β7 | BACKEND-LEVERAGED |
| AD4 | adapter_deepseek + abortSignal forward | ADAPTER | `lib/adapters/providers/adapter_deepseek.ts` | β7 | BACKEND-LEVERAGED |
| AD5 | adapter_nim + abortSignal forward | ADAPTER | `lib/adapters/providers/adapter_nim.ts` | β7 | BACKEND-LEVERAGED |
| AD6 | streamAdapter (unified streaming path post-γ10) | ADAPTER | `lib/adapters/run_adapter.ts`, `raw.ts` | γ10 consolidation | BACKEND-LEVERAGED |
| M061 | 061_conversations_v2.sql | MIGRATION | `supabase/migrations/061_conversations_v2.sql` | β2 | APPLIED (Docker-local + prod) |
| M062 | 062_predictions.sql | MIGRATION | `supabase/migrations/062_predictions.sql` | γ3 | APPLIED |
| M063 | 063_pending_streams.sql | MIGRATION | `supabase/migrations/063_pending_streams.sql` | γ7 (P.5 fix) | APPLIED |
| M064 | 064_query_trace_steps_user_id.sql | MIGRATION | `supabase/migrations/064_query_trace_steps_user_id.sql` | fix-wave (O8) | APPLIED |
| T1 | Playwright config + chat-v2 spec tree | TEST-INFRA | `tests/e2e/chat-v2/playwright.config.ts` | α1 | REACHABLE (CI) |
| T2 | axe-core a11y specs | TEST-INFRA | `tests/e2e/chat-v2/a11y/axe.spec.ts` | α1 + γ8 | REACHABLE (auth-gated; mostly skipped without MARSYS_SUPER_ADMIN_SESSION) |
| T3 | web-vitals perf specs | TEST-INFRA | `tests/e2e/chat-v2/perf/web-vitals.spec.ts` | α1 | REACHABLE (soft-gated) |
| T4 | streaming perf specs | TEST-INFRA | `tests/e2e/chat-v2/perf/streaming.spec.ts` | α1+α2 | REACHABLE |
| T5 | mobile visual specs (15 cases + 4 baselines) | TEST-INFRA | `tests/e2e/chat-v2/__visuals__/mobile.spec.ts` | γ9 | REACHABLE; baselines DEFERRED-§M |
| T6 | validator_failure_surface E2E spec | TEST-INFRA | `tests/e2e/chat-v2/validator_failure_surface.spec.ts` | γ4 | REACHABLE (skip-gated) |
| T7 | feature-reachability spec (13 cases) | TEST-INFRA | `tests/e2e/chat-v2/feature-reachability.spec.ts` | remediation C.7 | REACHABLE (auth-gated) |
| T8 | side-by-side capture helper | TEST-INFRA | `tests/e2e/chat-v2/helpers/side-by-side.ts` | chrome-parity E.1 | REACHABLE |
| T9 | provider fixture tree (TODO-record) | TEST-INFRA | `tests/fixtures/chat-v2/providers/*` | α1 | **BACKEND-ORPHANED** (all `_fixture_status: TODO-record`; no fixtures recorded) |
| T10 | k6 load test dir | TEST-INFRA | `tests/load/k6/` | α1 | **BACKEND-ORPHANED** (`.gitkeep` only — no scripts authored) |
| T11 | fixture_mode_adapter | TEST-INFRA | `lib/fixtures/fixture_mode_adapter.ts` | α1 | REACHABLE (fixture replay) |
| D1 | CHAT_V2_PLAN_v1_0.md (v1.1) | DOC | `00_ARCHITECTURE/` | original | REACHABLE |
| D2 | CHAT_V2_PROGRESS.md (live tracker) | DOC | project root | original | REACHABLE |
| D3 | CHAT_V2_VERIFICATION_AUDIT_v1_0.md | DOC | `00_ARCHITECTURE/` | post-merge audit | REACHABLE |
| D4 | CHAT_V2_REMEDIATION_PLAN_v1_0.md | DOC | `00_ARCHITECTURE/` | remediation | REACHABLE |
| D5 | CHAT_V2_CHROME_GAP_AUDIT_v1_0.md | DOC | `00_ARCHITECTURE/` | chrome audit | REACHABLE |
| D6 | CHAT_V2_CHROME_PARITY_PLAN_v1_0.md | DOC | `00_ARCHITECTURE/` | chrome parity | REACHABLE |
| D7 | CHAT_V2_RED_TEAM_v1_0.md | DOC | `00_ARCHITECTURE/` | PM1 | REACHABLE |
| D8 | CHAT_V2_MASTER_GATE_EVIDENCE_v1_0.md | DOC | `00_ARCHITECTURE/` | PM2 | REACHABLE |
| D9 | CHAT_V2_CLOSE_v1_0.md (sealing) | DOC | `00_ARCHITECTURE/` | PM3 | REACHABLE |
| D10 | CHAT_V2_A11Y_REPORT(_v2_0).md | DOC | `00_ARCHITECTURE/` | γ8 | REACHABLE |
| D11 | CHAT_V2_MIGRATION_RUNBOOK.md | DOC | `00_ARCHITECTURE/` | §M.3 | REACHABLE |
| D12 | CHAT_V2_α0_SPIKE_REPORT.md | DOC | `00_ARCHITECTURE/chat_v2_briefs/` | α0 | REACHABLE |
| D13 | CHAT_V2_FLAG_RECONCILIATION_v1_0.md | DOC | `00_ARCHITECTURE/` | α6 | REACHABLE |
| D14 | CHAT_V2_PREVERGE_VERIFICATION_v1_0.md | DOC | `00_ARCHITECTURE/` | Phase H | REACHABLE |
| D15 | CHAT_V2_STAGING_E2E_REPORT(_v2_0).md | DOC | `00_ARCHITECTURE/` | §M.11 | REACHABLE |
| D16 | CHAT_V2_ACCEPTANCE_WALKTHROUGH(_v2_0).md | DOC | `00_ARCHITECTURE/` | §M.10 / C.8 | REACHABLE |
| D17 | MID_STREAM_BEHAVIOR.md | DOC | `components/chat/MID_STREAM_BEHAVIOR.md` | β3 | REACHABLE |

Row count: **128** entries (target ≥100 met).

---

## §2 — Orphaned components (built but not surfacing in V2)

For each component that exists but is NOT reachable from `ConsumeChatV2.tsx`
(checking import + render tree + render condition):

### S2.1 — ConsumeReportLibraryV2 (CRITICAL)
- **Path**: `platform/src/components/consume/ConsumeReportLibraryV2.tsx`
- **Built for**: chrome-parity C.6 (saved-reports surface for V2)
- **Why orphaned**: `grep ConsumeReportLibraryV2 platform/src` returns only the file itself. ConsumeChatV2 accepts `reports` via `ConsumeChatProps` but never reads or passes it. The C.6 brief documents the component shipped but C-LANE-SEQ wire-up never happened.
- **Severity**: CRITICAL — Legacy has a full saved-reports panel; V2 users cannot access any saved report.
- **Surfacing work**: Import in `ConsumeChatV2.tsx` and render either in a right-side overlay panel (mirror legacy's `ConsumeShell.tsx:196-205` Sheet) or as a header-action button. ~30 lines + new state.

### S2.2 — ConversationSidebarV2 (HIGH)
- **Path**: `platform/src/components/consume/ConversationSidebarV2.tsx`
- **Built for**: chrome-parity C.11 (branded sidebar with date grouping + rename/delete)
- **Why orphaned**: ConsumeChatV2 uses its own inlined `ConversationSidebar` at lines 95-199 (no rename, no delete, no date grouping). The C.11 component has those affordances but is never imported.
- **Severity**: HIGH — Inferior IA in V2 vs. legacy (no rename, no delete, no date-clustered list).
- **Surfacing work**: Replace inlined `ConversationSidebar` with imported `ConversationSidebarV2`. Verify wire-up of rename/delete handlers against `/api/conversations/[id]`.

### S2.3 — LiveReasoningCard (MEDIUM)
- **Path**: `platform/src/components/consume/LiveReasoningCard.tsx`
- **Built for**: Legacy SSE marker stream (mid-stream reasoning surface)
- **Why orphaned**: V2 ignores legacy SSE markers entirely; uses `MessagePrimitive.Parts.Reasoning` (ReasoningProgress) for native reasoning parts only.
- **Severity**: MEDIUM — Replaced by ReasoningProgress for thinking models. Documented as superseded in chrome-parity log line 1387 ("LiveReasoningCard superseded by ReasoningProgress").
- **Surfacing work**: Confirmed as superseded — delete or mark `@deprecated`.

### S2.4 — CorrectionNotice (HIGH)
- **Path**: `platform/src/components/consume/CorrectionNotice.tsx`
- **Built for**: ‹correction› SSE marker in legacy stream
- **Why orphaned**: V2 route never emits `data-correction` parts. Component would render if data flowed.
- **Severity**: HIGH — Native domain UX feature lost in V2 (model self-corrections invisible).
- **Surfacing work**: Add `CorrectionPartSchema` to `data_parts.ts`; have route emit `data-correction` on `‹correction›…‹/correction›` (or open-only ‹correction›) detection in final answer; render in V2Message.

### S2.5 — OutOfDomainBanner (HIGH)
- **Path**: `platform/src/components/consume/OutOfDomainBanner.tsx`
- **Built for**: ‹out_of_domain› SSE marker
- **Why orphaned**: V2 route never emits `data-out-of-domain` parts. Same shape as CorrectionNotice — chrome-parity log line 1389 explicitly notes deferral.
- **Severity**: HIGH — Honest-failure mode (model declining out-of-corpus questions) is invisible in V2.
- **Surfacing work**: Add part schema; emit in onFinish on detection; render at top of V2Message.

### S2.6 — ProvenanceDrawer (LOW)
- **Path**: `platform/src/components/consume/ProvenanceDrawer.tsx`
- **Built for**: Legacy provenance surface
- **Why orphaned**: V2 has `PostAnswerProvenance` already wired (inline component).
- **Severity**: LOW — likely superseded.
- **Surfacing work**: Confirm superseded; delete or `@deprecated`.

### S2.7 — ConversationHistoryDrawer / ConversationHistoryButton (LOW)
- **Path**: `platform/src/components/consume/ConversationHistoryDrawer.tsx`, `ConversationHistoryButton.tsx`
- **Why orphaned**: V2 has its own (inline) ConversationSidebar.
- **Severity**: LOW — superseded.
- **Surfacing work**: delete or `@deprecated`.

### S2.8 — LogPredictionAction (LOW)
- **Path**: `platform/src/components/consume/LogPredictionAction.tsx`
- **Why orphaned**: γ3 PredictionLogModal superseded it.
- **Severity**: LOW.
- **Surfacing work**: delete or `@deprecated`.

### S2.9 — DivergenceReport / ReportGallery / SanskritTermSpan / PanelAnswerView (LOW)
- All legacy components — V2 path doesn't use any of them.
- **Severity**: LOW each.
- **Surfacing work**: Audit + delete on legacy-deletion-pass.

### S2.10 — ToolCallCard (chat/) duplicate (LOW)
- **Path**: `platform/src/components/chat/ToolCallCard.tsx`
- **Why orphaned**: V2 imports `../chat-v2/ToolCallCard` (line 52). The `chat/` variant is the older legacy component, no remaining importers.
- **Severity**: LOW — naming confusion only.
- **Surfacing work**: Delete or rename one to remove ambiguity.

### S2.11 — StreamingMarkdown / Markdown / StreamingDots / UserMessage / PendingAssistantBubble (UNCLEAR)
- Older `components/chat/` rendering primitives.
- **Why orphaned**: V2 uses `MarkdownContent` (streamdown); messages render via assistant-ui primitives.
- **Severity**: LOW — likely orphans.
- **Surfacing work**: Verify zero importers + delete.

---

## §3 — Surfacing-but-dead UI affordances

### S3.1 — CitationSidePanel `onPin` snippet path is dead
- **Affordance**: Click `[N]` chip → "pinned in side panel with hover-readable snippet"
- **Location**: `ConsumeChatV2.tsx:306-338` (V2AssistantText) + `CitationSidePanel.tsx`
- **Why dead**: `extractCitations(text)` builds an index in V2AssistantText but the side panel state lives elsewhere (or is unwired). The previous audit's O3 fix lands inline citation chips in a footer below the answer, but **the rich `data-citation` snippet payload that the server emits in `onFinish` (route.ts:1128) is never read by V2Message** — `handlePin` in CitationCtx is constructed with empty snippet.
- **Fix shape**: Subscribe to `data-citation` parts in V2Message; build a `Map<index,CitationPart>`; provide via CitationCtx so handlePin can look up snippet/layer at click time.

### S3.2 — Action bar is hover-only on touch
- **Affordance**: Edit / Regenerate / Details / Copy icons require `opacity-0 group-hover:opacity-100` — invisible without hover (mobile/touch).
- **Location**: `ConsumeChatV2.tsx:517, 638`
- **Why dead on touch**: No focus/tap reveal; touch devices have no hover.
- **Fix shape**: Switch to `focus-within` or always-show on mobile; or tap-to-reveal on touch detection.

### S3.3 — V2 ConversationSidebar refresh after first turn
- **Affordance**: Auto-titled conversation should appear in sidebar after first turn
- **Location**: `ConsumeChatV2.tsx:106-117` (reload only called on mount + chartId change)
- **Why dead**: Sidebar `reload()` only fires on mount/chartId change. After first turn, server generates title and writes to DB, but the sidebar never re-fetches.
- **Fix shape**: Subscribe to `data-persistence` parts in the sidebar's parent context to trigger reload; or invalidate-on-conversation-id-change.

### S3.4 — Archive endpoint (DELETE /api/conversations/[id]) has no client trigger
- **Affordance**: Soft-delete from sidebar
- **Why dead**: V2 sidebar has no archive button. Endpoint exists, never called from V2 UI.
- **Fix shape**: Add archive button per item in ConversationSidebarV2 (which already has hover affordance scaffolding).

### S3.5 — `/api/conversations/[id]/feedback` endpoint exists; no V2 thumbs UI
- **Affordance**: Feedback rating from V2
- **Why dead**: No feedback button surfaces in V2 message action bar.
- **Fix shape**: Add `useFeedback`-like hook + thumbs to the assistant action bar.

### S3.6 — Stream resume tracker writes but resume restore message is a string suffix
- **Affordance**: Resume after disconnect with correct token position
- **Location**: `ConsumeChatV2.tsx:1283-1325`
- **Partial**: Works. But the "_(Stream interrupted — showing recovered partial response.)_" text is appended literally; no UI affordance to "continue" — the partial just sits there.
- **Fix shape**: Render a "Resume from here" CTA that re-submits the original prompt with the partial as context.

---

## §4 — Backend orphans (built but not leveraged)

### S4.1 — observabilityPart never emitted (BACKEND-ORPHANED)
- **Path**: `lib/streams/data_parts.ts:69-75` schema + `observabilityPart()` helper at line 188
- **Built in**: α3 (originally promised in plan §4.4 + γ5 deep-link)
- **Why orphaned**: `grep -r "data-observability\|observabilityPart" platform/src` returns 0 emitter hits — only the schema, the helper, and test files. Route never writes a `data-observability` part.
- **Impact**: PerMessageDetailsDrawer's `obsQueryId` (line 113-114) always undefined; falls back to `meta.queryId` (works, but indicates dead primary path).
- **Fix shape**: Single-line addition in `route.ts createUIMessageStream.execute`:
  `writer.write({ type: 'data-observability', data: observabilityPart({ query_id: queryId, trace_url: \`https://amjis-web.../observatory/trace/${queryId}\` })})`

### S4.2 — fakeGcsRetrieve hardcoded path in production route (BACKEND-LEVERAGED + degenerate)
- **Path**: `route.ts:143` `const entry = fakeGcsRetrieve(att.token)`
- **Built in**: β5 (with the explicit intent to swap to GCS at §M.1)
- **Why degenerate**: Always reads from in-process Map. Production uploads survive a single Cloud Run revision; on revision rollover or pod recycle (autoscaling), attachments are lost mid-conversation.
- **Impact**: Multi-modal feature works in same-process tests but breaks under production load.
- **Fix shape**: Implement `gcsRetrieve(token)` via `@google-cloud/storage`. Bucket `gs://madhav-astrology-chat-attachments` already provisioned per CHAT_V2_PROGRESS line 1277-1278. Switch routing in `resolveAttachments` based on env (already encoded in `hasGcsCredentials()`).

### S4.3 — pdf_extractor Vertex DU stub returns fixture even when credentials present
- **Path**: `lib/multimodal/pdf_extractor.ts:71-72`
- **Built in**: β5 (with `TODO(γ)` to implement)
- **Why orphaned**: `vertexExtract()` immediately returns `fixtureExtract()` — the actual `@google-cloud/documentai` integration is never written.
- **Impact**: All PDF uploads → model receives `[PDF FIXTURE] {filename} — N bytes`. Garbage in, garbage out. This is a B.10 (no fabricated computation) violation in production.
- **Fix shape**: Implement the documented stub (in-file comment lines 62-69 spells out the steps).

### S4.4 — streaming_citation_validator IS wired in onFinish but not at onChunk
- **Path**: `lib/synthesis/streaming_citation_validator.ts`, called at `route.ts:931-957`
- **Plan §4.11 spec**: "validator inspects the assembled answer at the SDK's `onChunk` boundary, and on hard-fail injects a `type:'error'` part into the data stream **before `onFinish` fires**."
- **Reality**: Validator runs in `onFinish` (post-stream). The user has already seen the full answer by the time the error band emits. Discipline-wise correct (no mid-stream UI flicker), but the plan's "wire-effective" intent (catch before delivery) is not met.
- **Severity**: LOW (works) but **divergent from plan**.
- **Fix shape**: Either accept current behavior + update plan, OR move to onChunk + buffer mode.

### S4.5 — history_compression module dormant
- **Path**: `lib/synthesis/history_compression.ts`, called only when `HISTORY_COMPRESSION_ENABLED=true`
- **Built in**: β8
- **Why dormant**: Flag F2 default false; never flipped. Module is correct, tested, unused in production.
- **Severity**: MEDIUM — long conversations (>32k tokens) silently truncate at 2-pair window without compression. Plan §4.10 promised sliding-window compression as default behavior eventually.
- **Fix shape**: Flip flag after staging smoke (compression latency tradeoff verified).

### S4.6 — pending_streams reaper endpoint has no caller (BACKEND-ORPHANED)
- **Path**: `app/api/admin/cron/reap-pending-streams/route.ts`
- **Built in**: fix-wave B.12
- **Why orphaned**: Cloud Scheduler job not provisioned. Documented as operator follow-up in `CHAT_V2_PROGRESS.md §B.12`.
- **Impact**: `pending_streams` table grows indefinitely; rows with TTL `expires_at < now()` accumulate.
- **Fix shape**: `gcloud scheduler jobs create http pending-streams-reaper --schedule="*/5 * * * *" ...` per progress §B.12 recipe.

### S4.7 — consumeSystemPromptV2 wired (B.9 fixed it)
- **Path**: `lib/synthesis/single_model_strategy.ts:340-342`
- **Status**: REACHABLE. The previous audit (O5) flagged the orphan; fix-wave B.9 wired `CITATION_APPENDIX` import + conditional append on `CHAT_V2_ENABLED`. Confirmed.

### S4.8 — useChatLifecycle / useKeyboardShortcuts / useSidebarState (hooks)
- **Paths**: `lib/hooks/useChatLifecycle.ts`, `useKeyboardShortcuts.ts`, `useSidebarState.ts`
- **Status**: REACHABLE in legacy only; ORPHANED in V2 (V2 uses inline `useEffect` for hotkeys and inline `useState` for sidebar). Acceptable: V2 took a different abstraction. Future legacy-deletion pass cleans them up.

### S4.9 — useChatPreferences uses chartId for namespacing
- **Path**: `hooks/useChatPreferences.ts`, wired in `ConsumeChatV2:1251`
- **Status**: REACHABLE.

### S4.10 — Conversation-finish persistence-data-part: client never re-fetches sidebar
- **Server**: Route emits `data-persistence` on every turn (route.ts:1096-1116)
- **Client**: V2 sidebar's `reload()` runs only on mount + chartId change (ConsumeChatV2.tsx:119-121)
- **Severity**: MEDIUM — first-turn-titled conversations and new conversations don't appear in sidebar until reload.

---

## §5 — Feature flags not wired (or partially-wired)

| Flag | Default | Where checked | Gates behavior? | Disposition |
|---|---|---|---|---|
| `CHAT_V2_ENABLED` (F1) | false (env true) | `ConsumeChat.tsx`, route, single_model_strategy | YES — master switch | Flipped 2026-05-17; clean-up post 7-day watch |
| `HISTORY_COMPRESSION_ENABLED` (F2) | false | `route.ts:730` | YES (no-op when false) | **DORMANT** — needs staging smoke before flip |
| `COST_VISIBILITY_FOR_USERS` (F3) | false | `page.tsx → ConsumeChat → ConsumeChatV2 → CostVisibilityCtx → PerMessageDetailsDrawer.costVisible` | YES (gates Cost row for non-admin) | DORMANT — but design decision; only flip when tier rollout decided |
| `CITATION_GATE_OVERRIDE` (F4) | false | route.ts:938 | YES | INTENTIONAL — admin override stays off |
| `PANEL_MODE_ENABLED` (F5) | true | orchestrator selection | YES | OK |
| `PANEL_DEGRADE_2_OF_3` (F6) | false | panel orchestrator | YES | INTENTIONAL — degradation off until needed |
| `CHECKPOINT_*` (F7, 7 flags) | false each | LLM checkpoint paths | YES | INTENTIONAL — Phase 6 dormant; not chat-v2 |
| `CONSUME_UI_V2_ENABLED` (F8) | true (since AIOps Phase 3) | page.tsx | YES | OK |
| `OBSERVATORY_ENABLED` (F9) | false (env true) | observatory routes | YES | OK |
| `LEL_CONTEXT_ENABLED` (F10) | true | route + V2 bottom bar | YES (body.lel_context_enabled) | OK; user toggle |
| `LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED` | false | msr_sql | YES | not chat-v2 scope |
| `LL3_ZERO_WEIGHT_DOMAIN_DISCLAIMER_ENABLED` | true | msr_sql | YES | not chat-v2 scope |
| `NVIDIA_PLANNER_ENABLED` | true | UQE planner | YES | not chat-v2 scope |
| `VALIDATOR_FAILURE_HALT` | true | validators | YES | OK |
| `SYNTHESIS_PROMPT_DEBUG` | false | logging | YES | INTENTIONAL |

**Unused-but-declared flags**: none of the chat-v2-era flags appear declared-but-unread. The dormant F2 and F3 do gate real code paths; they're "ready to flip" not "broken-wire".

**Plan-promised flags NOT declared:**
- `MARSYS_FLAG_STREAM_RESUME_ENABLED` — plan §8 listed it as a sub-flag for safe rollout. Not in `feature_flags.ts`. γ7 ships stream resume always-on.
- `MARSYS_FLAG_MULTIMODAL_PDF_ENABLED` — plan §8. Not declared; β5 ships always-on (with fixture extraction).

**Net assessment**: feature-flag hygiene is healthier than expected. Two design-decision flags dormant; two plan-promised sub-flags skipped (likely intentionally, given big-bang shipping discipline).

---

## §6 — Cross-cutting analysis: why does "built but not surfacing" keep happening?

The pattern across four passes (original ship → remediation → chrome parity → fix-wave) is a clean diagnostic: each pass found a new class of orphan that the prior pass's verification didn't probe.

**Pass 1 (original ship, 50 commits, 32 work items, ~165 files).** Audit found 10 findings — most of them server-emits-but-client-doesn't-consume orphans (data-cost, data-observability, data-citation snippet, data-stage/tool subscribers absent, consumeSystemPromptV2 never imported, regenerate endpoint never called, `lastAssistantMetadata` never passed). The original verification pass focused on **structural unit tests** (does the component render with mocked data, does the route emit the expected JSON) and on a "W1–W15 walkthrough" of *named features*. Nothing in that gate asked: *"is the data part the route emits actually consumed by anything on the client?"* The pipe was never traced end-to-end as a data-flow audit.

**Pass 2 (remediation, ~12 PRs).** Fixed all 10 findings *as named*. Each fix landed with a regression test for *the specific feature*. But the campaign was scoped to those 10 findings — it never asked "what other built things are orphans?" The chrome layer remained untouched because no finding was about chrome — they were about data flow.

**Pass 3 (chrome parity, ~15-18 PRs).** Wired ShareButton + TraceDrawer + CommandPalette + ShortcutsDialog + ModelStylePicker + TierPicker + LEL toggle + brand pill + EmptyState. Authored `ConsumeReportLibraryV2` and `ConversationSidebarV2` as parallel components — but the C-LANE-SEQ wire-up phase (when components are landed in V2) only got to 6/8 named C-lane items. C.6 (ReportLibrary) and C.11 (ConversationSidebarV2) were marked COMPLETE because the components shipped — not because they were rendered.

**Pass 4 (fix-wave-in-progress).** Targeting W3/W4/W5/W8/W10 failures from F.1 verification incident. Same pattern: scoped to named failures, not a sweep.

**Root causes converged.**
1. **No reachability check in PR review.** PR reviewers check `tsc + tests pass + diff makes sense`. None check "is the new component actually rendered in the surface that has the flag-on user." A `grep <ComponentName> ConsumeChatV2.tsx` would have caught C.6 and C.11 instantly.
2. **Component tests verify in-isolation behaviour; integration tests verify wire-level emit; nothing verifies "this server-emit reaches *and is consumed by* the V2 client component."** The discriminated union of data parts is tested for emission and for schema, but no test asserts that a `data-observability` part exists in `message.metadata.unstable_data` after a real-shape response.
3. **Audit/remediation campaigns are *findings-driven*, never *sweep-driven*.** O1–O10 came from one audit. The next audit will produce O11–O20. The capability-reachability question this audit asks (*"of everything we built, what is reachable?"*) was never asked at session-close or merge-gate.
4. **W-case verification looked at user-facing actions, not at the orphan question.** W3 "details drawer populates with model/tokens/cost" verified *one* drawer field after streaming, not *all* fields after reload. W6 "drawer persists after reload" was added in pass 4 — and exposed O9 (metadata not persisted), which had been missed by every prior verification.
5. **Plan-promised features without acceptance criteria slip silently.** Plan §4.4 promised `data-observability` for the trace deep-link. The deep-link works (via `meta.queryId` fallback) so no test/W-case fails. The orphan never produces a visible failure.

**Process change recommendation.**

Add a `reachability-sweep` step to every merge-gate (plan, remediation, parity). For every entry in `data_parts.ts` schema union, every component file in `chat-v2/` or imported anywhere in `consume/`, every endpoint in `app/api/chat/**` or `app/api/conversations/**` or `app/api/predictions/**` or `app/api/uploads/**`, the sweep:
1. greps for at least one emitter (server-side write or client-side render-site).
2. greps for at least one consumer (data part read OR component render).
3. If 1 or 2 returns zero hits, the entry is flagged as candidate orphan.

This sweep is one shell script. Run pre-merge. ~5 min. Catches every class of orphan documented in this audit.

The deeper fix is **integration tests that assert end-to-end data flow** — but that's expensive. The cheap fix is the sweep + a CI step that fails the PR if a newly-introduced component is not imported by anything in the V2 tree.

---

## §7 — Recommended capability surfacing work plan

Prioritized list of fix-wave-extensions. Effort: S=small (<1 day), M=medium (1-2 days), L=large (3+ days).

### P0 — Block re-flip / blocker

| # | Item | Effort | Files | Fix shape |
|---|---|---|---|---|
| P0.1 | Surface ConsumeReportLibraryV2 in V2 (saved-reports right panel) | M | `ConsumeChatV2.tsx`, possibly new layout cell | Mount via right panel like legacy `ConsumeShell.tsx:196-205`; toggle via header action |
| P0.2 | Wire data-citation rich payload into V2 (CitationCtx + snippet lookup) | M | `ConsumeChatV2.tsx` (CitationCtx provider, handlePin lookup), V2Message data extraction | Build `Map<index,CitationPart>` from data parts; supply to CitationCtx so handlePin can resolve snippet |
| P0.3 | data-observability emission (close primary path; remove fallback brittleness) | S | `route.ts createUIMessageStream.execute` | Single `writer.write(observabilityPart(...))` call |
| P0.4 | Replace inlined V2 ConversationSidebar with ConversationSidebarV2 (rename + delete + date groups) | M | `ConsumeChatV2.tsx` (delete inline 95-199; import C5) | Wire onRename/onDelete to PATCH/DELETE `/api/conversations/[id]` |
| P0.5 | Sidebar reload after first-turn auto-title (subscribe to data-persistence) | S | `ConsumeChatV2.tsx` (sidebar reload trigger) | Pass `onMessageFinish` from runtime subscribe to ConversationSidebar |
| P0.6 | Action bar reachability on touch | S | `ConsumeChatV2.tsx:517, 638` | Replace `opacity-0 group-hover:opacity-100` with `focus-within:opacity-100` + on-tap reveal |
| P0.7 | Replace fakeGcsRetrieve with real GCS retrieval | M | `lib/multimodal/fake_gcs_store.ts` or new `gcs_store.ts`; route resolveAttachments | Wire `@google-cloud/storage` get-buffer; preserve fixture path for dev/test |
| P0.8 | Implement Vertex DU PDF extraction | M | `lib/multimodal/pdf_extractor.ts:62-69` | Implement the documented stub against `@google-cloud/documentai` |

### P1 — This watch period (visible-to-user orphan features)

| # | Item | Effort | Files | Fix shape |
|---|---|---|---|---|
| P1.1 | Add CorrectionNotice surfacing path (data-correction part + emit + render) | M | `data_parts.ts`, `route.ts onFinish`, `V2Message` | Add schema + detection regex (open-only ‹correction›) + render |
| P1.2 | Add OutOfDomainBanner surfacing path | M | `data_parts.ts`, `route.ts onFinish`, `V2Message` | Same as P1.1 |
| P1.3 | Provision pending_streams reaper Cloud Scheduler job | S (operator) | gcloud command | Per `CHAT_V2_PROGRESS §B.12` recipe |
| P1.4 | Stream-resume "Continue?" CTA on recovered partial | S | `ConsumeChatV2.tsx:1311-1316` | Wrap recovered partial with a CTA button that re-submits original prompt |
| P1.5 | Archive button per item in ConversationSidebar | S | ConversationSidebarV2 or inline sidebar | Soft-delete via DELETE `/api/conversations/[id]` |
| P1.6 | Feedback thumbs in V2 action bar | M | `V2Message`, useFeedback (or new V2 hook) | POST `/api/conversations/[id]/feedback` |
| P1.7 | Move citation gate to onChunk (plan §4.11 intent) | M | `single_model_strategy.ts onChunk wiring`, validator buffer | Buffer accumulated text in onChunk; validate at threshold; emit error-part pre-onFinish |
| P1.8 | Flip HISTORY_COMPRESSION_ENABLED after staging smoke | S | env + `feature_flags.ts` default | Verify Haiku-summarizer latency budget on 50-turn fixture conversation |
| P1.9 | Auto-titling visible: fix V2 sidebar refresh after first turn (alternative to P0.5) | S | same as P0.5 | Trigger reload from data-persistence subscription |
| P1.10 | E2E reachability spec: assert every data part schema → V2 render path | M | new `tests/e2e/chat-v2/reachability-sweep.spec.ts` | One test per data part type — assert emission + consumption |
| P1.11 | Provider fixture recording — fill `_fixture_status: TODO-record` | M (operator) | `tests/fixtures/chat-v2/providers/*` | Record + commit |
| P1.12 | Visual baseline capture (≥60 target, currently 27) | M (operator) | `tests/e2e/chat-v2/__visuals__/*` | `MARSYS_UPDATE_VISUALS=true npx playwright test` |

### P2 — Next watch (polish + backend orphans + flag cleanup)

| # | Item | Effort | Files | Fix shape |
|---|---|---|---|---|
| P2.1 | Delete confirmed-superseded legacy components | S | LiveReasoningCard, CorrectionNotice (after P1.1), OutOfDomainBanner (after P1.2), ProvenanceDrawer, ConversationHistoryDrawer/Button, LogPredictionAction, DivergenceReport, ReportGallery, SanskritTermSpan, PanelAnswerView, ToolCallCard (chat/) | One legacy-deletion-pass PR |
| P2.2 | Delete confirmed-orphan legacy hooks | S | useChatLifecycle, useKeyboardShortcuts (V2 inline), useSidebarState (V2 inline), useChatSession (V2 assistant-ui), useBranches (V2 BranchPickerPrimitive), useFeedback (after P1.6 reroute), useHotkeys (V2 inline), useAttachments (V2 inline) | Same pass as P2.1 |
| P2.3 | Streaming primitives audit (UnknownState, UserMessage, etc.) | S | `chat/UserMessage.tsx`, `chat/PendingAssistantBubble.tsx`, etc. | grep importers; delete if none |
| P2.4 | Author k6 load test scripts | L | `tests/load/k6/*` | Per plan §9.2.8 |
| P2.5 | Retire `MARSYS_FLAG_CHAT_V2_ENABLED` flag (post 7-day watch) | S | `feature_flags.ts`, `deploy.yml`, ConsumeChat thin switch | Delete the switch; legacy path removed |
| P2.6 | Retire ConsumeChatLegacy.tsx (post-flag-removal) | M | `ConsumeChatLegacy.tsx` + legacy-only deps | Per Phase 11B pattern |
| P2.7 | Audit Composer (chat/) vs V2Composer (inline) — choose one | M | `components/chat/Composer.tsx` | Either delete legacy Composer or migrate V2 to use ComposerShell shared primitive |
| P2.8 | Audit ConsumeShell — make hostable for either runtime, or delete | M | `components/consume/ConsumeShell.tsx` | Per `CHAT_V2_CHROME_GAP_AUDIT_v1_0.md §5` option A |
| P2.9 | Provider drift CI workflow | M | `.github/workflows/` + dev keys | Per plan §9.2.9 |
| P2.10 | Stryker mutation tests on critical paths | L | `tests/mutation/*`, `package.json` scripts | Per plan §9.2.16 |
| P2.11 | OWASP ZAP scan | M (operator) | infra | Per plan §9.2.11 |

### P3 — V3 backlog (nice-to-have, not blocking)

| # | Item | Effort | Notes |
|---|---|---|---|
| P3.1 | Voice I/O (Whisper + TTS) | L | Plan §15 explicit defer |
| P3.2 | Real-time collaborative chat | L | Plan §15 explicit defer |
| P3.3 | Cross-native query-mode dedicated UI | L | Plan §15 explicit defer |
| P3.4 | SSR for first paint | L | Plan §15 explicit defer |
| P3.5 | WebRTC ultra-low-latency streaming | L | Plan §15 explicit defer |
| P3.6 | Sub-flag declarations: MARSYS_FLAG_STREAM_RESUME_ENABLED, MARSYS_FLAG_MULTIMODAL_PDF_ENABLED | S | If safe-rollout becomes useful again |
| P3.7 | Per-turn cost dashboard widget (uses data-cost stream) | M | Operator-side telemetry |
| P3.8 | Multi-tab same-conversation reconciliation | M | Cross-tab broadcast channel |
| P3.9 | Per-message details drawer mobile (full-sheet) | S | Mobile UX polish |

**Item count: 41 prioritized.** Target 20–40 met.

---

## §8 — Closing note

The Chat V2 workstream is structurally complete (32/32 work items shipped, all
master-gate criteria mapped, all migrations applied, P.5 security fix landed),
but the four-pass remediation history reveals a persistent "built ≠ surfaced"
gap. This audit identifies **9 ORPHANED components (C5, C18, C40–C48), 1 dead
side-panel handler (C23), 1 backend-orphan data part (DP4), 3 backend stubs
producing degenerate output (MW5, MW7, EP17), 2 dormant flags (F2, F3)**, and
five UI affordances dead-on-touch / dead-after-reload.

A reachability-sweep step added to merge-gate would have caught most of these
pre-merge. The P0 list (8 items, ~12 days work) closes the chrome-parity and
data-flow gaps that block flag stability; P1 (12 items, ~15 days) closes
operator-side and verification gaps; P2 (11 items, ~14 days) is the
legacy-deletion + tooling-hardening pass.

---

*End CHAT_V2_CAPABILITY_REACHABILITY_AUDIT_v1_0 DRAFT.*
