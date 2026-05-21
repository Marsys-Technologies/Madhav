---
artifact: CHAT_V2_REMEDIATION_PLAN_v1_0
name: CHAT V2 REMEDIATION — MASTER PLAN
canonical_id: CHAT_V2_REMEDIATION_PLAN
version: 1.0
status: DRAFT
authored: 2026-05-16
author: Claude (Cowork)
governing_audit: 00_ARCHITECTURE/CHAT_V2_VERIFICATION_AUDIT_v1_0.md
predecessor_plan: 00_ARCHITECTURE/CHAT_V2_PLAN_v1_0.md v1.1
workstream_relationship: continuation of Chat V2 Big Bang workstream (NOT a new workstream)
target_branch: main (no new worktree)
mirror_pair: none
estimated_duration_calendar_days: 13 (6 days of remediation + 7-day watch)
estimated_pr_count: ~12-14
---

# CHAT V2 REMEDIATION — MASTER PLAN

## §1 Mission

Close the gap between what Chat V2 plan v1.1 promised and what actually shipped to production. The post-merge audit `CHAT_V2_VERIFICATION_AUDIT_v1_0.md` identified ten findings (O1–O10) where authored code is not reachable from the user-facing path or behaves incorrectly in production. Plus the §M.11 verification gap (96 of 116 Playwright tests skipped due to missing auth in the executor shell). This plan executes the verification campaign the workstream skipped and lands each audit fix as a focused PR.

This is **not a new workstream.** Chat V2 Big Bang remains the canonical workstream; this is its remediation phase. The CLAUDE.md §E entry for chat-v2 will reflect this status until §M.16 closes.

Bounded by the same Ethical Framework as the parent plan: probabilistic, calibrated, auditable outputs; disclosure tiers preserved; no loosening of any ethical commitment.

## §2 Workstream classification

Continuation of Chat V2 Big Bang. The §M.16 + §M.17 closeout dates slip by approximately 7-13 days (from 2026-05-23 to ~2026-05-29 through 2026-06-02 depending on remediation pace + new 7-day watch).

No worktree. All work lands as small PRs to `main` from short-lived feature branches (`fix/chat-v2/<audit-id>-<description>` per fix). Master feature flag `MARSYS_FLAG_CHAT_V2_ENABLED` rolled back to `false` in `deploy.yml` for the duration of the campaign (Phase A) and re-flipped to `true` when all critical fixes verify (Phase D).

`marsys-m6-prospective` worktree remains untouched. M5/M6 work proceeds in parallel and does not block this campaign.

## §3 Scope

### §3.1 IN scope

- **All 10 audit findings** (O1–O10) — each landed as a focused PR with implementation + regression test.
- **Database migration 064** — adds `user_id` column to `query_trace_steps` to unblock the PPL flow (O4).
- **§M.11 verification gap** — full Playwright suite executed with `MARSYS_SUPER_ADMIN_SESSION` set; all 116 tests run, not 20.
- **Visual regression baseline capture** — the 59 authored `.spec.ts` files actually exercised against a running dev server with `MARSYS_UPDATE_VISUALS=true`; baseline `.png` images committed.
- **Cross-browser verification** — Playwright suite run against Chromium + Firefox + WebKit.
- **Lighthouse CI against staging revision** — Web Vitals + streaming-specific metrics measured against `amjis-web-00128-f9r` (or its descendant).
- **Mobile profile run** — Playwright at 375px (iPhone Safari) and 768px (iPad Safari).
- **Manual a11y pass** — NVDA + VoiceOver desktop + VoiceOver iOS findings recorded in `CHAT_V2_A11Y_REPORT.md`.
- **New end-to-end feature-reachability spec** — a Playwright spec that exercises every audit-identified surface: details drawer populates, stage stepper renders, citations chip out, panel toggle works, PPL modal submits cleanly, reasoning drawer appears for thinking models, regenerate truncates persistence. The test that would have caught O1–O10 in one shot.
- **Re-do acceptance walkthrough** — operator runs against the verification matrix from `CHAT_V2_VERIFICATION_AUDIT_v1_0.md §5`, not the original 28 master-gate criteria alone.

### §3.2 OPTIONAL / opportunistic

- **§M.4 (pending-streams reaper Cloud Scheduler job)** — defer-friendly but can be folded in since we're touching maintenance endpoints anyway during O7/O8 work.
- **GCS bucket provisioning** for real multi-modal upload persistence (required for O8 to land as a non-stub).
- **Vertex AI Document Understanding API key provisioning** (required for O7 to land as a non-stub).

### §3.3 OUT of scope

- New features beyond what plan v1.1 promised.
- v2 backlog items (voice I/O, real-time collaborative chat, etc.).
- Mutation testing (Stryker) — defer to v3 hardening.
- k6 load tests — defer; not blocking remediation.
- Physical-device mobile spot-check — defer; Playwright profiles are sufficient.
- Provider drift CI run against live providers — defer; weekly cadence post-remediation.
- §M.5 synthetic monitor — defer; Observatory manual check is acceptable during the new watch.

## §4 Architecture / approach decisions

### §4.1 Master flag rollback first

**Phase A** rolls `MARSYS_FLAG_CHAT_V2_ENABLED` back to `false` in `deploy.yml` as the first PR. Users go back to `ConsumeChatLegacy` (which is the known-good pre-workstream production state). Fix PRs ship to main with the flag still off; users are never exposed to half-fixed intermediate states.

### §4.2 Each fix is a small focused PR

Roughly one PR per audit finding. Some related fixes may bundle (e.g., O3a + O3b + O3c — build StageStepper + ToolCallCard + subscribe ConsumeChatV2 — naturally group). Each PR includes:

- The implementation fix
- A new regression test (unit, integration, or E2E) that would have caught the audit finding
- An updated `CHAT_V2_PROGRESS.md` entry under a "Remediation" section
- A commit message with the audit ID and one-line description

### §4.3 Verification campaign runs after critical fixes land

Phase C (verification) is meaningful only after Phase B (fixes) land. Sequence: A → B → C → D. Within Phase B, fixes can be parallelized via subagents because they are mostly independent.

### §4.4 Re-flip flag only when master gate passes

Phase D re-flips `MARSYS_FLAG_CHAT_V2_ENABLED=true` in `deploy.yml` only after Phase C's full verification campaign passes. The new revision serves V2 with all 10 audit findings remediated.

### §4.5 No new architecture commitments

This is wiring repair, not redesign. Components, modules, schemas, and flags identified in plan v1.1 are honored as-is. New components are minimal additions (`StageStepper`, `ToolCallCard`) that fulfill the original plan's intent, not new architectural surfaces.

### §4.6 Regression-prevention discipline

Every fix's regression test must be the kind that would have caught the audit finding pre-merge. This means: tests that verify end-to-end reachability ("submit a query, observe drawer fields populate with non-empty values"), not just module-level structural checks. The audit's hidden lesson: structural unit tests pass while end-to-end behavior breaks. Phase B's tests close this gap permanently.

## §5 Phase A — Stabilize (1 work item, ~10 min)

### A.1 — Rollback master flag

**Goal**: Revert `MARSYS_FLAG_CHAT_V2_ENABLED` to `false` in `.github/workflows/deploy.yml`. Cloud Run picks up the change on next deploy; users go back to `ConsumeChatLegacy`.

**Branch**: `fix/chat-v2/A1-rollback-master-flag`

**Implementation**: One-line edit `MARSYS_FLAG_CHAT_V2_ENABLED=true → false`.

**PR commit message**: `fix(chat-v2/A.1): rollback master flag pending remediation campaign per audit v1.0`

**Tests added**: None (pure config).

**Exit criteria**:
- PR merged
- New Cloud Run revision deployed with `MARSYS_FLAG_CHAT_V2_ENABLED=false`
- Verify legacy path renders on `/consume` (one human glance)

## §6 Phase B — Fix Wave (12-14 work items, ~3-5 days)

Ordered by priority (CRITICAL → HIGH → MEDIUM → LOW). Items within a tier are parallelizable.

### CRITICAL TIER

#### B.1 — O4-mig: Migration 064 adds `user_id` to `query_trace_steps`

**Why critical**: O4 (PPL prediction logging always 403) is data corruption — every prediction submission silently fails because the SQL query references a column that doesn't exist. Migration must land first.

**Files to create**:
- `platform/supabase/migrations/064_query_trace_steps_user_id.sql`

**SQL**:
```sql
ALTER TABLE query_trace_steps
  ADD COLUMN IF NOT EXISTS user_id TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_query_trace_steps_user_id
  ON query_trace_steps (user_id) WHERE user_id IS NOT NULL;

COMMENT ON COLUMN query_trace_steps.user_id IS
  'Added by 064 to support PPL ownership check in /api/predictions.';
```

**Branch**: `fix/chat-v2/B1-query-trace-steps-user-id`
**Commit**: `fix(chat-v2/O4-mig): migration 064 adds user_id to query_trace_steps`
**Tests added**: 1 schema-shape test in `platform/tests/unit/db/migration_064.test.ts`.
**Apply**: Migration file committed; operator applies via Cloud SQL proxy (same process as §M.3). Document in CHAT_V2_PROGRESS.md.

#### B.2 — O4: Fix PPL prediction logging endpoint

**Files to touch**:
- `platform/src/lib/trace/writer.ts` — writes `user_id` on every trace step (after migration 064)
- `platform/src/app/api/predictions/route.ts` — query already correct; no change needed if writer adds the column

**Implementation**:
1. Update `lib/trace/writer.ts` to capture `user_id` from session and persist on every `query_trace_steps` insert.
2. Verify endpoint returns 200 + persisted row for owner; 403 for non-owner; 404 for unknown query_id.

**Branch**: `fix/chat-v2/B2-ppl-user-id-wiring`
**Commit**: `fix(chat-v2/O4): wire user_id into trace writer to unblock PPL endpoint`
**Tests added**: 5 integration tests covering owner / non-owner / unknown-query / null-user / RLS happy-path.

#### B.3 — O10: Wire assistant-ui Reload to regenerate endpoint

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — override `ThreadPrimitive.Reload` (or equivalent) to POST `/api/chat/consume/regenerate` instead of the default consume route
- Verify `/api/chat/consume/regenerate/route.ts` truncates `conversation_messages` to the edit point before re-issuing synthesis

**Branch**: `fix/chat-v2/B3-regenerate-truncation`
**Commit**: `fix(chat-v2/O10): wire assistant-ui Reload to regenerate endpoint`
**Tests added**: 3 integration tests covering single regenerate / multiple regenerate / branch creation.

### HIGH TIER

#### B.4 — O6: Wire streamdown into V2AssistantText

**Why high**: The biggest single quality regression. V2 currently renders assistant text via `<p className="whitespace-pre-wrap">`. No markdown, no KaTeX, no code blocks. This was the headline α2 deliverable.

**Files to touch**:
- `platform/src/components/chat-v2/V2AssistantText.tsx` (or equivalent) — replace `<p>` with `MarkdownContent` from `platform/src/components/chat/MarkdownContent.tsx`

**Implementation**:
1. Import `MarkdownContent` into V2's text-part renderer.
2. Pass `props.text` through MarkdownContent.
3. Verify code blocks, KaTeX math, GFM tables, and footnote-style citations render.

**Branch**: `fix/chat-v2/B4-v2-streamdown`
**Commit**: `fix(chat-v2/O6): wire streamdown into V2AssistantText for full markdown rendering`
**Tests added**: 12 unit tests for incomplete fences / math / tables / footnotes during stream (mirror existing legacy MarkdownContent tests).

#### B.5 — O3 (a+b+c bundled): Stage progress + tool cards in V2

**Bundled because**: building two new components and one subscribe step naturally groups.

**Files to create**:
- `platform/src/components/chat-v2/StageStepper.tsx` — pipeline stage indicator
- `platform/src/components/chat-v2/ToolCallCard.tsx` — per-tool fetch status card

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — subscribe to `data-stage` and `data-tool` parts via the message lifecycle; render StageStepper above streaming text; render ToolCallCard inline per tool

**Branch**: `fix/chat-v2/B5-stage-tool-progress`
**Commit**: `fix(chat-v2/O3): build StageStepper + ToolCallCard; subscribe ConsumeChatV2 to data parts`
**Tests added**: 6 component tests (StageStepper + ToolCallCard isolation) + 3 E2E tests (live stage progression during streaming).

#### B.6 — O2: Panel-mode UI toggle in V2 composer

**Files to create**:
- `platform/src/components/chat-v2/PanelModeToggle.tsx` — composer-area toggle

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — render toggle in composer; thread `panel_opt_in` state through `useChatRuntime` body params

**Implementation**:
1. Toggle defaults to off; persists in `sessionStorage` per conversation.
2. When on, route receives `panel_opt_in=true` in the request body; orchestrator factory selects panel strategy.
3. Visible affordance includes a tooltip explaining panel mode.

**Branch**: `fix/chat-v2/B6-panel-toggle`
**Commit**: `fix(chat-v2/O2): add panel mode toggle to V2 composer`
**Tests added**: 4 component tests + 2 E2E tests (toggle + full panel mode flow).

#### B.7 — O9: Persist `lastAssistantMetadata` in writeConversationMessages

**Files to touch**:
- `platform/src/app/api/chat/consume/route.ts` — pass `lastAssistantMetadata` to `writeConversationMessages` after stream completes
- `platform/src/lib/persistence/conversation_writer.ts` — already accepts the parameter; ensure it's written

**Implementation**:
1. In route's `onFinish`, assemble metadata from `messageMetadata` and pass to `writeConversationMessages`.
2. On reload, fetched messages have populated `metadata_json`.

**Branch**: `fix/chat-v2/B7-metadata-persistence`
**Commit**: `fix(chat-v2/O9): persist lastAssistantMetadata to conversation_messages`
**Tests added**: 3 integration tests (write-then-read round trip with full metadata; reload restores drawer fields).

### MEDIUM TIER

#### B.8 — O1: Emit `data-cost` from route's onFinish

**Files to touch**:
- `platform/src/app/api/chat/consume/route.ts` — `dataStream.writeData({ type: 'cost', ... })` in `onFinish` with model, tokens, dollars, ms

**Branch**: `fix/chat-v2/B8-cost-data-part`
**Commit**: `fix(chat-v2/O1): emit data-cost from route onFinish for details drawer`
**Tests added**: 2 integration tests (data-cost emitted with correct shape; drawer populates).

#### B.9 — O5: Import consumeSystemPromptV2 + wire into synthesis

**Files to touch**:
- `platform/src/lib/synthesis/single_model_strategy.ts` — import `consumeSystemPromptV2` from `platform/src/lib/synthesis/prompts/consume_system_prompt_v2.ts`
- Synthesis selects V2 prompt when `chatV2Enabled` is true; legacy prompt otherwise

**Branch**: `fix/chat-v2/B9-citation-prompt-v2`
**Commit**: `fix(chat-v2/O5): wire consumeSystemPromptV2 with SIG.MSR.NNN format instruction`
**Tests added**: 3 prompt-output tests verifying citation appendix appears + LLM is instructed to emit footnote markers.

### LOW / OPPORTUNISTIC TIER

#### B.10 — O7: Real Vertex Document Understanding for PDFs

**Gated on**: Vertex DU API credentials available in environment.

**Files to touch**:
- `platform/src/lib/multimodal/pdf_extractor.ts` — replace hardcoded `return fixtureExtract` with real Vertex DU call

**Branch**: `fix/chat-v2/B10-pdf-real-extraction`
**Commit**: `fix(chat-v2/O7): wire Vertex Document Understanding for real PDF extraction`
**Tests added**: 4 integration tests (small PDF, multi-page PDF, image-heavy PDF, fallback on API error).

**Defer condition**: If Vertex DU credentials are not available by Phase B end, mark O7 as `OPEN-deferred-to-v3` and proceed without it. PDF uploads remain stubbed but the rest of the multi-modal flow works.

#### B.11 — O8: Real GCS signed-URL implementation

**Gated on**: GCS bucket `marsys-chat-uploads-prod` provisioned.

**Files to touch**:
- `platform/src/app/api/uploads/sign/route.ts` — remove fallback to `fake_gcs_store`; require credentials

**Branch**: `fix/chat-v2/B11-gcs-real-uploads`
**Commit**: `fix(chat-v2/O8): wire real GCS signed-URL upload path`
**Tests added**: 3 integration tests (sign-URL issuance / upload / retrieval).

**Defer condition**: Same as O7 — if GCS bucket isn't provisioned by Phase B end, defer and document.

#### B.12 — §M.4 (opportunistic): pending-streams reaper

**Why fold in here**: Touches maintenance-endpoint infrastructure; cheaper to do alongside O7/O8 than separately later.

**Files to create**:
- `platform/src/app/api/admin/cron/reap-pending-streams/route.ts` — header-secret-authed endpoint that runs `DELETE FROM pending_streams WHERE expires_at < now()`
- Cloud Scheduler job spec (provisioning happens operator-side post-PR)

**Branch**: `fix/chat-v2/B12-pending-streams-reaper`
**Commit**: `fix(chat-v2/§M.4): pending-streams reaper endpoint + scheduler spec`
**Tests added**: 3 integration tests (reaper runs cleanly; expired rows deleted; current rows preserved).

**Operator follow-up**: provision Cloud Scheduler job via `gcloud scheduler jobs create http` against the new endpoint, every 5 min.

## §7 Phase C — Verification campaign (8 work items, ~2-3 days)

The §M.11 work that didn't happen, done right this time. Phase B must complete before Phase C starts.

### C.1 — Full Playwright suite with authenticated session

**Goal**: All 116 chat-v2 E2E tests run, not 20.

**Procedure**:
1. Start dev server with `MARSYS_FLAG_CHAT_V2_ENABLED=true` (locally, not in deploy.yml yet).
2. Generate a super-admin session cookie via `platform/scripts/mint_session_cookie.ts <super-admin-email>`.
3. Export `MARSYS_SUPER_ADMIN_SESSION` and `PLAYWRIGHT_BASE_URL=http://localhost:3000`.
4. Run `npx playwright test tests/e2e/chat-v2/ --reporter=list`.
5. Capture results in `00_ARCHITECTURE/CHAT_V2_STAGING_E2E_REPORT_v2_0.md`.

**Exit criteria**: All 116 tests pass OR documented design-skips only (zero failures, zero environment-skipped).

### C.2 — Visual regression baseline capture

**Procedure**:
1. Dev server running with `MARSYS_UPDATE_VISUALS=true`.
2. `npx playwright test tests/e2e/chat-v2/__visuals__/` runs and writes `.png` baselines.
3. Commit baselines under `platform/tests/e2e/chat-v2/__visuals__/<test-name>.<browser>-<platform>.png`.

**Exit criteria**: ≥60 baseline images committed across all major chat states.

### C.3 — Cross-browser run

**Procedure**: Re-run C.1 + C.2 against Firefox and WebKit. Playwright config supports multi-browser via project profiles.

**Exit criteria**: Chromium + Firefox + WebKit all green. Document any browser-specific quirks in `00_ARCHITECTURE/CHAT_V2_BROWSER_COMPAT_v1_0.md`.

### C.4 — Lighthouse CI against staging revision

**Procedure**:
1. Deploy a staging-tagged Cloud Run revision with `MARSYS_FLAG_CHAT_V2_ENABLED=true` (use revision tagging, not full traffic flip).
2. Run Lighthouse CI against the tagged URL.
3. Assert Web Vitals: TTFB <800ms, FCP <1.5s, LCP <2.5s, INP <200ms, CLS <0.1.
4. Assert streaming metrics: TTFT <1.5s, first-stage-event <500ms, render <16ms/frame, ≥80 t/s.

**Exit criteria**: All budgets met; results recorded in `CHAT_V2_PERF_REPORT_v1_0.md`.

### C.5 — Mobile profile run

**Procedure**: Playwright mobile profiles at 375px (iPhone Safari) and 768px (iPad Safari) against the live dev server. All chat-v2 E2E tests run at these viewports.

**Exit criteria**: All mobile-tagged E2E tests pass; bottom-sheet citation panel + sidebar overlay + 16px input font verified per audit §4.

### C.6 — Manual a11y pass (operator work)

**Procedure (operator)**:
1. NVDA + Firefox (Windows) — full streaming conversation, reasoning drawer, citation panel, details drawer.
2. VoiceOver + Safari (macOS) — same.
3. VoiceOver + Safari (iOS) — mobile streaming conversation.
4. Keyboard-only navigation: every interactive element reachable, focus order logical.

**Output**: Populate `CHAT_V2_A11Y_REPORT.md` (currently placeholder) with findings per assistive tech.

**Exit criteria**: No serious/critical accessibility violations; minor findings filed as post-§M.16 backlog.

### C.7 — New end-to-end "feature reachability" Playwright spec

**Goal**: The test that would have caught all 10 audit findings in one run.

**Files to create**:
- `platform/tests/e2e/chat-v2/feature-reachability.spec.ts`

**Test cases**:
1. Send a query; observe StageStepper render through each pipeline stage.
2. Observe at least one ToolCallCard render during retrieval.
3. After completion, open details drawer; assert all fields populated (non-`—`): model, input tokens, output tokens, latency, cost.
4. Observe inline `[N]` citation chips in the answer.
5. Click a citation chip; assert hover preview + side-panel pin work.
6. Toggle panel mode; submit a panel-eligible query; assert dissent tabs visible to super-admin.
7. For a thinking model: assert reasoning drawer renders with live token count.
8. Reload the page; assert details drawer still populates from persisted metadata.
9. Regenerate the assistant message; assert old assistant turn removed from `conversation_messages`.
10. Submit a query containing a time-indexed prediction; assert "Log as prediction" affordance appears for super-admin.
11. Click "Log as prediction"; submit modal; assert 200 response + row in `predictions`.
12. Upload an image; assert it renders inline + reaches synthesis.
13. Upload a PDF; if Vertex DU is wired (O7), assert real text extraction; if not, assert fixture marker visible (deferred).

**Exit criteria**: All 13 reachability cases pass.

### C.8 — Re-do acceptance walkthrough (operator work)

**Procedure**: Operator runs against the verification matrix from `CHAT_V2_VERIFICATION_AUDIT_v1_0.md §5`, not the original 28 master-gate criteria alone.

**Output**: `CHAT_V2_ACCEPTANCE_WALKTHROUGH_v2_0.md` — supersedes v1.0; explicitly addresses each audit finding's expected behavior.

**Exit criteria**: Verdict PASS.

## §8 Phase D — Re-flip + close (3 work items)

### D.1 — Master flag flip to true via PR

**Goal**: Re-enable `MARSYS_FLAG_CHAT_V2_ENABLED` in production after Phase C clears.

**Branch**: `fix/chat-v2/D1-reflip-master-flag-post-remediation`
**Implementation**: One-line edit in `deploy.yml` (false → true).
**Commit**: `fix(chat-v2/D.1): re-enable master flag post-remediation`
**Exit criteria**: PR merged; new Cloud Run revision deployed with flag on; verify V2 renders for super-admin.

### D.2 — New 7-day watch starts

**Goal**: Same as original §M.15 watch, restarted from D.1 deploy timestamp.

**Watch end**: D.1 deploy + 7 days.
**Monitoring**: Observatory dashboard, 5xx error rate, streaming completion rate, cost trends, user reports.
**Rollback path**: Same one-line PR (true → false). Master flag remains the kill switch.

### D.3 — §M.16 + §M.17 close

**After D.2's 7-day clean watch**:
- Flip `feature_flags.ts` default to `true`.
- Remove the flag entirely from code.
- Delete `ConsumeChatLegacy.tsx`.
- Update CLAUDE.md §E to mark Chat V2 workstream CLOSED.
- Sealing artifact `CHAT_V2_CLOSE_v1_0.md` final update with `closed_by` and `closed_at`.

## §9 Acceptance criteria (Master gate)

The workstream re-closes only when ALL of the following are true. Phase B and Phase C cumulative.

### Audit findings (Phase B)
- [O1] `data-cost` emitted; details drawer shows non-`—` cost for every assistant message.
- [O2] Panel-mode toggle visible in V2 composer; panel mode actually triggers when toggled.
- [O3] StageStepper renders during streaming with per-stage progression; ToolCallCard renders per tool fetch.
- [O4] PPL endpoint returns 200 for valid owner; row persisted in `predictions`.
- [O5] Synthesis prompt includes citation appendix; LLM emits `[^N]` markers reliably.
- [O6] V2 assistant text rendered via `MarkdownContent`; code blocks + KaTeX + GFM all work.
- [O7] PDF extraction via real Vertex DU (or documented as deferred).
- [O8] GCS uploads persist across Cloud Run revisions (or documented as deferred).
- [O9] Reload after persistence shows fully populated details drawer.
- [O10] Regenerate truncates old assistant turns; no accumulation on repeated regenerate.

### Verification (Phase C)
- C.1 all 116 Playwright tests run (no auth-skips); all pass.
- C.2 ≥60 visual baselines committed.
- C.3 Chromium + Firefox + WebKit all green.
- C.4 Web Vitals + streaming metrics within plan v1.1 §9.2.6 budgets.
- C.5 Mobile profiles green at 375px + 768px.
- C.6 NVDA + VoiceOver desktop + VoiceOver iOS passes documented with no critical findings.
- C.7 New 13-case feature-reachability spec all green.
- C.8 Acceptance walkthrough v2.0 verdict PASS.

### Master flag (Phase D)
- D.1 flag flipped to true in production.
- D.2 new 7-day watch initiated; Observatory + error rate + streaming metrics nominal.

## §10 Risks + mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Vertex DU API credentials not available → O7 stays deferred | High | Medium | O7 explicit defer-condition; mark `OPEN-deferred-to-v3` in close artifact; PDF answers remain best-effort until creds. |
| R2 | GCS bucket not provisioned → O8 stays deferred | High | Medium | Same pattern as R1; in-memory store acceptable for current user volume (operator is primary user). |
| R3 | Migration 064 applied successfully on staging-like local but fails on prod | Low | High | Apply via Docker-local first (same recipe as §M.3); verify ALTER on local before prod. |
| R4 | New regression tests in Phase B surface MORE issues beyond the 10 findings | Medium | Medium | Each new finding filed as additional Phase B PR; doesn't block existing PRs from merging. |
| R5 | Visual regression baselines reveal unexpected drift on legacy path | Low | Low | Capture both flag-off + flag-on baselines; document any differences. |
| R6 | Phase C cross-browser surfaces Firefox/WebKit-specific bugs | Medium | Medium | File as Phase B-extension PRs; not blocking flag flip if Chromium is clean (document caveats). |
| R7 | Manual a11y pass surfaces critical findings | Medium | High | Each finding → dedicated remediation PR. Critical findings block D.1 flip. |
| R8 | New 7-day watch surfaces production issues | Low | Medium | Same kill switch as before (one-line flag revert). |
| R9 | Phase B work uncovers architectural issues that need plan amendment | Low | High | Amend this plan to v1.1; native review required. |

## §11 Open questions (settle before Phase B starts)

1. **Vertex AI Document Understanding API credentials** — are they provisioned for this project? If yes, what env var name? If no, native authorize provisioning or defer O7?
2. **GCS bucket `marsys-chat-uploads-prod`** — provisioned? If no, native authorize provisioning or defer O8?
3. **Acceptable user-facing impact during Phase A-C** — operator goes back to legacy chat for ~6 days. Is that acceptable, or do you want fixes shipped incrementally with flag on per fix?
4. **Migration 064 risk tolerance** — apply via Docker-local first (same as §M.3), or accept direct-to-prod since the migration is purely additive (`ADD COLUMN IF NOT EXISTS` + new index)?
5. **Phase B parallelism** — should fixes be authored sequentially by one Antigravity session, or fanned out across parallel sessions via subagents?

## §12 Sequencing

| Phase | Work items | Sessions | Calendar |
|---|---|---|---|
| Pre-A | Settle §11 open questions | 1 Cowork session | day 0 (today) |
| A | A.1 rollback | 1 (5 min) | day 1 |
| B | B.1–B.12 (3 critical + 4 high + 2 medium + 2 opportunistic + 1 §M.4) | 3-5 Antigravity sessions (parallelizable) | days 1-4 |
| C | C.1–C.8 (verification + walkthrough) | 2-3 sessions + 1 operator session for C.6 + C.8 | days 4-6 |
| D | D.1 reflip + D.2 watch start | 1 session (5 min) | day 6 |
| Watch | D.2 → D.3 transition | passive (7 days) | days 6-13 |
| Close | D.3 §M.16 + §M.17 | 1 session | day 13-14 |
| **Total** | **~24-26 work items** | **~10-12 sessions** | **~13-14 calendar days** |

## §13 Changelog

- **v1.0 (2026-05-16 evening, DRAFT)** — Initial authoring by Claude in Cowork. Awaits native ratification of §11 open questions before Phase A starts.

---

*End CHAT_V2_REMEDIATION_PLAN v1.0 DRAFT.*
