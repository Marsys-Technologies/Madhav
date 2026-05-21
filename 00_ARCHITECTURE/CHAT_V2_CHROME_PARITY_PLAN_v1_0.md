---
artifact: CHAT_V2_CHROME_PARITY_PLAN_v1_0
name: CHAT V2 CHROME PARITY — MASTER PLAN
canonical_id: CHAT_V2_CHROME_PARITY_PLAN
version: 1.0
status: DRAFT
authored: 2026-05-17
author: Claude (Cowork)
governing_audit: 00_ARCHITECTURE/CHAT_V2_CHROME_GAP_AUDIT_v1_0.md
predecessor_plan: 00_ARCHITECTURE/CHAT_V2_REMEDIATION_PLAN_v1_0.md v1.0
workstream_relationship: third remediation pass of Chat V2 Big Bang (after original ship + functional remediation)
target_branch: main (no new worktree)
mirror_pair: none
estimated_duration_calendar_days: 7-10
estimated_pr_count: ~15-18
---

# CHAT V2 CHROME PARITY — MASTER PLAN

## §1 Mission

Close the visual + chrome parity gap between `ConsumeChatV2` and `ConsumeChatLegacy` so that V2 is *better than legacy*, not "functional but visually broken." The Chat V2 functional remediation campaign (2026-05-17) verified every audit finding end-to-end — but it operated only on the functional axis. The V2 component never had the bespoke MARSYS chrome wired in, and the rendered UI today is substantially worse than legacy.

The audit at `CHAT_V2_CHROME_GAP_AUDIT_v1_0.md` identifies five root causes and ~15 missing or broken-wiring components. This plan executes the wire-up + layout fix + composer redesign + citation re-enable + brand-gradient restoration in a single coordinated workstream, with visual regression discipline as a first-class verification axis (closing the gap that all prior workstreams left open).

Bounded by the same Ethical Framework as parent plans. No new architectural commitments — this is wire-up + layout fixes.

## §2 Workstream classification

Third pass of the Chat V2 Big Bang workstream. The previous two passes were:
1. Original ship (2026-05-16) — shipped V2 functionally with master flag flipped on, audit then surfaced 10 findings
2. Remediation (2026-05-17) — fixed all 10 audit findings, ran comprehensive verification, re-merged

This third pass closes the visual/chrome parity gap that wasn't on either prior pass's verification axis. The `marsys-m6-prospective` worktree remains untouched. All work lands as small PRs to `main` from short-lived feature branches (`fix/chat-v2-parity/<id>-<slug>`).

Master flag `MARSYS_FLAG_CHAT_V2_ENABLED` rolled back to `false` (Phase A) for the duration of the campaign — users stay on legacy. Re-flipped (Phase G) only after visual-regression discipline confirms parity.

## §3 Scope

### §3.1 IN scope

**Layout structural fixes:**
- Sidebar mounting: in-flow → overlay portal (eliminates the `w-56` width steal)
- Container max-width: `max-w-3xl` → `max-w-4xl` (matches legacy)
- Brand background: remove hardcoded `bg-zinc-950`; let the gold-charcoal gradient surface through

**Chrome components to wire into V2 (~15):**
- ChartHeader (chart name · DOB · place)
- ShareButton (top-right)
- TraceDrawer / TraceButton (top-right) — closes γ5's deep-link surface
- ModelStylePicker (Gemini Stack 2M ctx)
- TierPicker / AcharyaDepth selector
- LifeEventsToggle ("Life Events: On")
- QueryTypeRow (Deep / Study / Brief / Panel)
- EmptyState (proper empty-thread rendering instead of "Ready")
- ReportLibrary (the saved-report surface)
- CommandPalette (Cmd-K)
- ShortcutsDialog
- LiveReasoningCard (mid-stream reasoning surface)
- CorrectionNotice + ContextUsageCue + OutOfDomainBanner + PostAnswerProvenance
- useChatPreferences hook (persisted preferences)
- branch-archive viewer

**Composer redesign:**
- Paperclip moved inside the rounded-3xl pill (cursor positioning fix)
- Keyboard shortcut hints ("SEND ↵" / "NEW LINE ⇧↵")
- Explicit `line-height` to fix `text-base md:text-sm` jitter
- Send/Stop button styling parity with legacy

**Citation chip re-enable:**
- Re-wire `V2AssistantText` to render `NumberedCitation` inline
- OR wire the `data-citation` parts path into `MarkdownContent` (whichever is cleaner architecturally)
- Hover preview + side-panel pin

**Visual regression discipline:**
- Side-by-side capture: legacy + V2 at each of the major chat states (empty, streaming, complete, drawer open, citation pinned, panel mode, reasoning drawer, etc.)
- Visual diff threshold + reviewer approval for any deviation
- Baselines for both flag-on (V2) AND flag-off (legacy) committed

**Verification:**
- Re-do the W1-W15 walkthrough with explicit visual parity checks added
- New W-row category: "Visual chrome present" for each of the 15 wired components
- Side-by-side operator review against legacy

### §3.2 OUT of scope

- The 3 γ-scope code TODOs from prior remediation (B.10 Vertex DU code, B.11 GCS retrieval, Anthropic force-route) — those remain post-watch backlog
- New features beyond legacy parity
- Refactoring shared components for reuse across V2/Legacy (just wire what exists)
- Mobile layout polish beyond what's needed for parity (the γ9 mobile-responsive work already shipped)
- Disclosure-tier negative-case verification (separate work)
- Stryker mutation testing, k6 load tests, physical-device mobile spot-check (deferred from prior plans; still deferred)

## §4 Architecture / approach decisions

### §4.1 Wire-up not refactor

Every chrome component listed in §3.1 already exists in the codebase. This plan **imports and renders** existing components into V2, not refactors them for reuse. If a component is too tightly coupled to legacy to be imported cleanly, file a small wrapper PR; do not block on refactoring.

### §4.2 No shared "Chat shell" abstraction

Tempting to create a shared `ChatShell` component that both Legacy and V2 wrap. **Don't.** That's a v4-class refactor. V2 imports the chrome pieces directly. Legacy stays as-is. Code duplication is acceptable for this campaign.

### §4.3 Flag rollback during campaign

Phase A rolls master flag to `false`. Users on legacy. Fixes ship with flag off. Re-flip at Phase G after visual-regression discipline confirms parity.

### §4.4 Visual regression as first-class verification

Every PR in Phase B-F includes:
- A side-by-side screenshot capture (legacy + V2 of the area being changed)
- Updated visual regression baseline in `platform/tests/e2e/chat-v2/__visuals__/`
- An "operator side-by-side compare" gate before merge

This is the discipline missing from prior campaigns. The audit pattern proved that functional verification doesn't catch UX gaps; this campaign installs the missing check.

### §4.5 Each fix is a focused PR

One component (or one closely-related group) per PR. Roughly 15-18 PRs across the campaign.

### §4.6 Composer redesign is one bundled PR

The composer changes (paperclip position, keyboard hints, line-height, send-button styling) are visually intertwined; bundle them so reviewers see the full new composer in one diff.

## §5 Phase A — Stabilize (1 work item, ~10 min)

### A.1 — Rollback master flag

**Goal**: Revert `MARSYS_FLAG_CHAT_V2_ENABLED` to `false` in `.github/workflows/deploy.yml`. Users on legacy during the campaign.

**Branch**: `fix/chat-v2-parity/A1-rollback-flag`
**PR commit**: `fix(chat-v2/parity-A.1): rollback master flag pending chrome parity workstream`
**Tests added**: none (config)

**Exit criteria**: PR merged + new Cloud Run revision deployed + legacy path renders on `/consume`.

## §6 Phase B — Layout structural fixes (3 work items, ~half day)

### B.1 — Sidebar mounting fix

**Goal**: Move `ConversationSidebar` from in-flow flex sibling to overlay portal (matching legacy's pattern).

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` (around line 1200)
- The page layout wrapper if it provides the portal mount point

**Implementation**:
- Render `ConversationSidebar` via React portal to a body-level container
- Sidebar slides in over content; doesn't claim row width
- Keep collapsed state but as an absolute-positioned strip, not in flow

**Tests added**: 1 visual regression (sidebar open vs closed) + 1 E2E (sidebar doesn't shift chat area width)
**Branch + PR + tests + visual diff per conventions**

### B.2 — Container max-width parity

**Goal**: Match legacy's `max-w-4xl` for thread + composer.

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` — search for `max-w-3xl`; change to `max-w-4xl`

**Tests added**: 1 visual regression baseline post-change
**Branch + PR**

### B.3 — Brand gradient restoration

**Goal**: Remove hardcoded `bg-zinc-950` at `ConsumeChatV2.tsx:1184`. Let the `ConsumeOverlayPortal`'s gold-charcoal gradient surface through.

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` (line 1184 region)
- Verify `globals.css` brand tokens are reachable in this component

**Tests added**: 1 visual regression (background tone matches legacy)
**Branch + PR**

## §7 Phase C — Chrome components wire-up (10-12 work items, ~3-4 days)

Ordered by user-visible impact. Each work item is one PR unless explicitly bundled.

### C.1 — ChartHeader (chart name · DOB · place)

**Goal**: Render the bespoke chart-aware header at the top of V2 (matches legacy's "Abhisek Mohanty · 1984-02-05 · BHUBANESWAR" pattern).

**Implementation**: Import existing `ChartHeader` from `platform/src/components/consume/` (locate exact path). Render at the top of `ConsumeChatV2`. Pass chart props from page-level props.

**Tests added**: 1 component test + 1 visual baseline
**Branch + PR**

### C.2 — Top-bar: ShareButton + TraceButton (with TraceDrawer)

**Goal**: Render Share + Trace controls in the top-right of V2. Wire TraceDrawer (γ5's deep-link target) to open from the Trace button.

**Implementation**: Import `ShareButton`, `TraceButton`, `TraceDrawer` from existing locations. Render in a top-bar slot. Wire `query_id` from message metadata into TraceDrawer.

**Tests added**: 2 component + 1 E2E (click Trace → drawer opens with correct query_id) + 1 visual baseline
**Branch + PR**

### C.3 — Bottom-bar selectors (bundled)

**Goal**: Render the "Gemini Stack 2M ctx · Acharya depth · Life Events: On · Deep · Study · Brief · Panel" row at the bottom of the V2 thread, above the composer.

**Implementation**: Import `ModelStylePicker`, `TierPicker` / `AcharyaDepthSelector`, `LifeEventsToggle`, `QueryTypeRow`. Wire state to `useChatPreferences` hook (also wire that hook if it's missing).

**Tests added**: 4 component tests + 1 E2E (selector changes persist) + 1 visual baseline
**Branch + PR**

### C.4 — Composer redesign (bundled)

**Goal**: Fix the cursor positioning bug + add keyboard shortcut hints + line-height fix + send/stop button styling.

**Files to touch**:
- Composer block in `ConsumeChatV2.tsx` (lines 914-947 region)

**Implementation**:
1. Move paperclip INSIDE the rounded-3xl pill (footer row below textarea, matching legacy)
2. Add "SEND ↵ · NEW LINE ⇧↵" keyboard shortcut hints below or beside the textarea
3. Add explicit `line-height` (e.g., `leading-6`) to the textarea
4. Use brand-styled send + stop buttons matching legacy

**Tests added**: 3 component tests (paperclip-inside, keyboard hints, button styling) + 1 visual regression + 1 E2E (cursor lands at start of textarea after click)
**Branch + PR**

### C.5 — EmptyState

**Goal**: Replace the generic "Ready / Chat V2 — assistant-ui" with the brand `EmptyState` component (which legacy uses).

**Implementation**: Import `EmptyState` from existing path. Render when `messages.length === 0`.

**Tests added**: 1 component + 1 visual baseline
**Branch + PR**

### C.6 — ReportLibrary

**Goal**: Wire the saved-report surface into V2 (the "saved reports" or "library" panel that legacy provides).

**Implementation**: Import `ReportLibrary`; mount in the appropriate location (likely sidebar or modal-triggered).

**Tests added**: 2 component + 1 E2E
**Branch + PR**

### C.7 — CommandPalette + ShortcutsDialog (bundled)

**Goal**: Wire Cmd-K command palette and shortcuts help dialog.

**Implementation**: Import both components. Register Cmd-K + `?` keybindings. Mount at top of V2 tree.

**Tests added**: 2 component + 1 E2E (Cmd-K opens palette)
**Branch + PR**

### C.8 — In-message chrome (bundled)

**Goal**: Wire `LiveReasoningCard`, `CorrectionNotice`, `ContextUsageCue`, `OutOfDomainBanner`, `PostAnswerProvenance` into V2's per-message rendering.

**Implementation**: Render each at the appropriate point in the assistant message envelope. Use data parts where applicable (provenance from `messageMetadata`; correction/context-usage from new data part types if not yet defined).

**Tests added**: 5 component tests + 1 visual baseline per state
**Branch + PR**

### C.9 — useChatPreferences hook

**Goal**: Wire the persisted preferences hook so selector states (model, depth, life-events) survive sessions.

**Implementation**: Import hook; wire into C.3's selector components.

**Tests added**: 3 unit + 1 E2E (preferences persist across reload)
**Branch + PR**

### C.10 — Branch-archive viewer

**Goal**: Wire the branch/archive viewer that legacy uses for navigating regenerated answer branches.

**Implementation**: Import existing component; mount in message envelope when branches > 1.

**Tests added**: 2 component + 1 E2E
**Branch + PR**

### C.11 — Conversation list refinement

**Goal**: Match legacy's sidebar styling: conversation grouping (Today / Yesterday / Older), proper hover/active states, archive affordance.

**Files to touch**: `ConversationSidebar` styling (in the existing component path)

**Tests added**: 2 visual baseline + 1 E2E (group rendering)
**Branch + PR**

### C.12 — Page-level layout shell

**Goal**: Match legacy's page-level wrapper structure (any nav, breadcrumbs, footer that legacy renders but V2 doesn't).

**Files to touch**: `platform/src/app/clients/[id]/consume/page.tsx` + `platform/src/app/clients/[id]/consume/[conversationId]/page.tsx`

**Tests added**: 1 visual baseline per page entry
**Branch + PR**

## §8 Phase D — Citation chip re-enable (1 work item, ~half day)

### D.1 — Re-enable inline NumberedCitation rendering

**Goal**: Fix the dead citation-chip rendering. Pick one of two paths:

**Path 1 (preferred — simpler)**: Re-enable inline `NumberedCitation` rendering in `V2AssistantText` (`ConsumeChatV2.tsx:270-273`). Remove the disabling comment about "handled by data-citation parts path". This puts citation rendering back in the markdown render pipeline.

**Path 2 (more architectural)**: Wire the `data-citation` parts path into `MarkdownContent`. Render citations from data parts emitted by the route. More aligned with the "data parts drive UI" pattern but requires extending `MarkdownContent` to accept data-part overlays.

Recommend Path 1 unless Path 2 yields better cross-provider consistency.

**Files to touch**:
- `platform/src/components/consume/ConsumeChatV2.tsx` (V2AssistantText section)
- Possibly `platform/src/components/chat-v2/NumberedCitation.tsx` (verify import works)

**Tests added**: 3 component tests + 1 E2E (citation chips render + hover + side-panel pin) + 1 visual baseline
**Branch + PR**

## §9 Phase E — Visual regression discipline scaffold (2 work items, ~1 day)

### E.1 — Side-by-side capture helper

**Goal**: Add a Playwright helper that captures legacy + V2 of the same conversation state in one test, producing side-by-side images for reviewer inspection.

**Files to create**:
- `platform/tests/e2e/chat-v2/__visuals__/side-by-side/` directory
- `platform/tests/e2e/chat-v2/helpers/side-by-side.ts`

**Implementation**: Helper accepts a test scenario, runs it twice (flag-off + flag-on), captures both screenshots, composites side-by-side.

**Tests added**: 5 side-by-side scenarios (empty, streaming, complete, drawer open, citation pinned)
**Branch + PR**

### E.2 — Visual baseline regeneration with chrome present

**Goal**: With Phase B-C-D shipped, regenerate all visual baselines so they capture the now-chromed V2 (not the bare scaffold).

**Implementation**: Run `MARSYS_UPDATE_VISUALS=true npx playwright test tests/e2e/chat-v2/__visuals__/` after Phase B-C-D complete.

**Tests added**: ≥80 baseline `.png` files (up from the 27 captured during remediation)
**Branch + PR**

## §10 Phase F — Verification (5 work items, ~1 day)

### F.1 — Full Playwright re-run with auth

Run the comprehensive walkthrough spec against the flag-on V2 (post-Phase-A-E merge). All 15 W cases + 3 Anthropic cases. Generate `CHAT_V2_PARITY_E2E_REPORT_v1_0.md`.

### F.2 — Cross-browser run (Chromium + Firefox + WebKit)

Re-verify the parity across browsers. Capture browser-specific findings if any.

### F.3 — Visual side-by-side review (operator)

Operator reviews each side-by-side capture from E.1. Approves or flags deltas. Output: `CHAT_V2_VISUAL_PARITY_REPORT_v1_0.md` with per-scenario verdicts.

### F.4 — Lighthouse re-run against staging

Re-run Lighthouse against the new staging revision. Verify Web Vitals didn't regress.

### F.5 — Acceptance walkthrough v3.0

Operator runs `CHAT_V2_ACCEPTANCE_WALKTHROUGH_v3_0.md` — superset of v2.0 plus the visual parity dimension (each of the 15 chrome components present + working).

## §11 Phase G — Re-flip + close (3 work items)

### G.1 — Re-flip master flag

After Phase F clear: PR setting `MARSYS_FLAG_CHAT_V2_ENABLED=true` in `deploy.yml`. New Cloud Run revision deploys with V2 active + full chrome + correct layout.

### G.2 — New 7-day watch

Same pattern as prior watches. Monitor Observatory + Slack + user reports.

### G.3 — Close out

After clean watch: §M.16 (flag default flip + flag removal + `ConsumeChatLegacy.tsx` deletion) + §M.17 (CLAUDE.md §E mark CLOSED + remediation log finalized).

## §12 Acceptance criteria (Master gate)

### Layout
- Sidebar overlays, doesn't steal width
- Container max-width matches legacy (`max-w-4xl`)
- Brand gold-charcoal gradient visible
- Chat column uses full available viewport width minus sidebar overlay

### Chrome components (all 15+ present in V2)
- ChartHeader, ShareButton, TraceButton+Drawer, ModelStylePicker, TierPicker, LifeEventsToggle, QueryTypeRow, EmptyState, ReportLibrary, CommandPalette, ShortcutsDialog, LiveReasoningCard, CorrectionNotice, ContextUsageCue, OutOfDomainBanner, PostAnswerProvenance, useChatPreferences, branch-archive viewer
- Each verified rendered in F.1 walkthrough

### Composer
- Cursor lands at start of textarea on click
- Paperclip inside the pill (no 44px offset)
- Keyboard shortcut hints visible
- No font-size jitter at md breakpoint

### Citations
- Inline `[N]` chips render
- Click pins in side panel
- Hover shows preview

### Visual regression
- ≥80 baselines committed (up from 27)
- Side-by-side captures for 5+ major states
- Operator-approved deltas only

### Browser parity
- Chromium + Firefox + WebKit all pass full walkthrough

### Performance
- Web Vitals within plan v1.1 §9.2.6 budgets
- No regression vs. pre-parity Lighthouse (Perf 93 / A11y 98 / BP 100 baseline)

## §13 Risks + mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Some chrome components are too tightly coupled to legacy to import cleanly | Medium | Medium | Small wrapper PR per stubborn case; don't refactor |
| R2 | Sidebar overlay change breaks layout on mobile | Medium | Low | Test at 375px + 768px viewports in Phase F.2 |
| R3 | Brand gradient differs subtly between V2 and legacy after restoration | Medium | Low | Side-by-side captures (E.1) catch any drift |
| R4 | useChatPreferences hook conflicts with assistant-ui's internal state | Low | Medium | Hook integration test in C.9 |
| R5 | Composer redesign breaks textarea auto-resize | Medium | Low | Visual + E2E test for multi-line input behavior |
| R6 | Citation chip re-enable surfaces bugs in NumberedCitation that were hidden | Medium | Medium | D.1 includes regression test suite |
| R7 | Phase B-C parallelism causes merge conflicts | Medium | Low | Sequential PRs per work item; weekly rebase from main |
| R8 | Visual regression baselines drift between runs (font rendering, etc.) | High | Low | Threshold tolerance + ignore-zone helpers in Playwright config |

## §14 Open questions (settle before Phase B)

1. **Does shared `useChatPreferences` hook already exist?** Audit says yes. If no, who owns authoring it?
2. **Brand gradient implementation** — is it CSS variable, Tailwind class, or external stylesheet? Determines C.5 (EmptyState) styling approach.
3. **Are there existing visual regression baselines for legacy?** If yes, we can compare V2 against them directly. If no, capture legacy baselines in E.1 first.
4. **Is the assistant-ui Thread primitive overridable** for the chrome layers needed (e.g., LiveReasoningCard between thinking and answer), or does V2 need a wrapper component?

## §15 Sequencing

| Phase | Work items | Sessions | Calendar |
|---|---|---|---|
| Pre-A | Settle §14 open questions | 1 Cowork session | day 0 (today) |
| A | A.1 rollback | 1 (10 min) | day 1 |
| B | B.1-B.3 layout fixes | 1-2 sessions | day 1-2 |
| C | C.1-C.12 chrome wire-up | 4-5 sessions (parallelizable) | days 2-5 |
| D | D.1 citation chips | 1 session | day 5 |
| E | E.1-E.2 visual regression | 1-2 sessions | day 5-6 |
| F | F.1-F.5 verification | 1-2 sessions + 1 operator session | day 6-7 |
| G | G.1-G.3 reflip + close | 1 session (G.1) + 7-day watch + 1 session (G.3) | day 7-14 |
| **Total** | **~25 work items + 5 verification activities** | **~14-16 sessions** | **~14-16 calendar days** |

## §16 Changelog

- **v1.0 (2026-05-17 evening, DRAFT)** — Initial authoring. Awaits native ratification of §14 open questions before Phase B starts.

---

*End CHAT_V2_CHROME_PARITY_PLAN v1.0 DRAFT.*
