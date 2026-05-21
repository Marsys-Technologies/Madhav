---
artifact: CHAT_V2_ROUND_6_PLAN_v1_0
name: CHAT V2 ROUND 6 — F.3 FIX-WAVE + AUTOMATED SMOKE GATE
canonical_id: CHAT_V2_ROUND_6_PLAN
version: 1.0
status: DRAFT
authored: 2026-05-18
author: Claude (Cowork)
governing_audits:
  - 00_ARCHITECTURE/CHAT_V2_F3_FORENSIC_v1_0.md (Round 6 forensic)
predecessor_plans:
  - 00_ARCHITECTURE/CHAT_V2_PLAN_v1_0.md v1.1 (original ship)
  - 00_ARCHITECTURE/CHAT_V2_REMEDIATION_PLAN_v1_0.md v1.0 (Round 2)
  - 00_ARCHITECTURE/CHAT_V2_CHROME_PARITY_PLAN_v1_0.md v1.0 (Round 3)
  - 00_ARCHITECTURE/CHAT_V2_ROUND_5_PLAN_v1_0.md v1.0 (Round 5 — capability surfacing + per-PR visual gate)
workstream_relationship: sixth pass of Chat V2 Big Bang
target_branch: main
process_change: per-PR operator visual review gate RETAINED + automated smoke gate ADDED
estimated_pr_count: 8 (6 fix PRs + 1 smoke spec PR + 1 required-checks workflow PR)
estimated_duration_calendar_days: 2-3
mirror_pair: none
---

# CHAT V2 ROUND 6 — F.3 FIX-WAVE + AUTOMATED SMOKE GATE

## §1 Mission

Round 5 shipped 11 PRs across Phases A-E and landed the per-PR operator visual review gate as a process change. Phase F.3 (the operator's full visual walkthrough) ran on 2026-05-18 and caught **13+ regressions** that the per-PR gate did not surface — most of them inherited from earlier rounds, several of them produced by the same kind of "tests pass but UI does not work" pattern the gate was meant to prevent.

Round 6 has two purposes, addressed simultaneously:

1. **Fix every F.3 finding.** The forensic at `CHAT_V2_F3_FORENSIC_v1_0.md §1–§4` traced each finding to a precise file:line root cause and grouped them into three cumulative patterns. Round 6 ships 6 P0 PRs that close every finding tagged "blocks reflip".

2. **Install an automated smoke gate.** The per-PR operator gate stays — operator visual review on every chat-v2 PR continues. But the operator should not be the one who detects "stage stepper is invisible because of a data-parts-source-of-truth bug." Round 6 ships a single Playwright spec (`round6-walkthrough.spec.ts`) that mocks the consume route and asserts every F.3 finding's success criterion as a binary pass/fail. Wired as a required CI check on chat-v2 PRs via `.github/workflows/chat-v2-smoke.yml`. Future regressions of the same class are caught in CI before review, not in operator's lap.

The end state of Round 6: every P0 finding from F.3 passes a Playwright assertion and an operator visual review; the smoke spec runs in < 60 s on every chat-v2 PR; the master flag `MARSYS_FLAG_CHAT_V2_ENABLED` can re-flip to `true` after a clean Phase F.4.

Bounded by the same Ethical Framework as parent plans. No new architectural commitments — fix-wave + automation only.

## §2 Workstream classification

Sixth pass of Chat V2 Big Bang. Prior passes:

| Round | Date | Theme | Outcome |
|---|---|---|---|
| 1 | 2026-05-16 | Original ship | Audit found 10 findings |
| 2 | 2026-05-17 | Functional remediation | Closed 10 findings; partial verification |
| 3 | 2026-05-17 | Chrome parity | 12 components wired; 5 W-case failures at F.3; flag rolled back |
| 4 | 2026-05-17 | Fix-wave | 5 W-cases closed |
| 5 | 2026-05-17/18 | Capability surfacing + per-PR visual gate | 11 PRs across Phases A-E; F.3 operator walkthrough found 13+ regressions |
| **6** | **2026-05-18 → ~05-21** | **F.3 fix-wave + automated smoke gate** | **(this plan)** |

No worktree (consistent with Round 5). Small focused PRs to `main` from short-lived feature branches (`fix/chat-v2-r6/<id>-<slug>`). Master flag remains `false` for the duration of Round 6. Re-flipped at Phase F.4 only after every P0 PR lands AND the smoke spec is green AND operator visual review confirms.

`marsys-m6-prospective` worktree remains untouched (consistent with all prior rounds).

## §3 Scope

### §3.1 IN scope — P0 (blocks reflip)

These six PRs together close every F.3 finding tagged P0 in the forensic §6:

- **R6.1 — Unified `useDataParts(message)` hook.** Fixes F.3 finding B1 *and* simultaneously surfaces stage stepper, ToolCallCard, prediction chips, panel confidence ribbon, and validator gate band — all of which were silently invisible because they read only `message.metadata.unstable_data` while assistant-ui lands route emissions in `message.content` as `{type:'data', name:'<x>'}`. Single source of truth for live + post-stream data parts. Plus emit `stagePart('synthesis', 'done')` in `onFinish` (closes F.3 O1).
- **R6.2 — Inline citation rendering via `[^N]` Markdown footnotes.** Fixes F.3 findings B2/B3 + O3. Synthesis prompt emits `[^1]`, `[^2]` markers instead of `SIG.MSR.NNN`; `MarkdownContent` gets a custom `footnoteReference` component rendering `NumberedCitation` at the `[^N]` site naturally; chip footer in `V2AssistantText` is dropped.
- **R6.3 — Enrich `extractCitations` against MSR signal store.** Fixes F.3 findings B4/B5 + O7. `extractCitations` (or sibling `enrichCitations` called in onFinish) resolves each `SIG.MSR.NNN` against the MSR signal store, populating `snippet` and true `layer`. CitationSidePanel then renders rich snippets, not empty conditionals.
- **R6.4 — Sidebar layout discipline.** Fixes F.3 findings L1 + L2. Drops `md:ml-{10,56}` from chat-column wrapper entirely (sidebar becomes a true overlay only); drops the redundant `mx-auto` from `MarkdownContent.tsx:108`; deletes the duplicate in-sidebar "Collapse" button in `ConversationSidebarV2.tsx:238-261`.
- **R6.5 — Single send/stop button during streaming.** Fixes F.3 finding L3. Reduces the streaming-state composer to a single white stop button by default; the "cancel + resend" affordance moves behind a long-press / right-click / hover-tooltip (whichever is most discoverable in operator review).
- **R6.6 — Action-bar icon scale-up.** Fixes F.3 finding B6. Scales `V2RegenerateButton`, Details, Copy, Edit from `h-6 w-6` (w/ `h-3 w-3` SVG) to `h-8 w-8` (w/ `h-4 w-4` SVG). `gap-1 → gap-1.5`. `min-h-[40px] min-w-[40px]` for touch parity. Applied consistently across the action bar.

### §3.2 IN scope — Process automation

- **R6-SMOKE — Playwright walkthrough spec.** Single new file `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts` covering every F.3 finding with the assertion table from forensic §7. Uses a mock route fixture (`platform/tests/e2e/chat-v2/fixtures/round6-mock-route.ts`) registering a stub for `POST /api/chat/consume` that emits a canned stream — no live LLM credentials required. Chromium-only, < 60s wall time.
- **R6-CI — Required-checks workflow.** New file `.github/workflows/chat-v2-smoke.yml` triggers on PR paths touching `platform/src/components/consume/ConsumeChatV2.tsx`, `platform/src/components/chat-v2/**`, `platform/src/components/chat/ConversationSidebarV2.tsx`, `platform/src/app/api/chat/consume/route.ts`. Steps: checkout → `npm ci` → `npx playwright install chromium` → `npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=github`. Branch protection adds this as a required check on `main` for `chat-v2-r6/*` and `fix/chat-v2-*` branches.

### §3.3 IN scope — Phase F.4 reflip

- **F.4 — Master flag reflip.** Once all six P0 PRs merge AND the smoke spec is green on `main` AND operator re-runs F.3 walkthrough manually and signs off, set `MARSYS_FLAG_CHAT_V2_ENABLED=true` in `.github/workflows/deploy.yml` env vars. Pair with `gcloud run services update --update-env-vars` per the deploy-cloudrun memory.

### §3.4 OUT of scope

Deferred to Round 7 (or later):

- **R7-N3 — Wire conversation rename + delete (3-dot menu).** F.3 N3. Requires backend `PATCH /api/conversations/[id]` endpoint + frontend Popover with `Rename` / `Delete` `MenuItem`s + new props on `ConversationSidebarV2`. ~100 lines. Not blocking reflip.
- **R7-L4 — Sidebar `<Logo />` at bottom + N2 brand typography tokens.** F.3 L4 + N2. Visual polish. Not blocking reflip.
- **R7-O5 — Consolidate three runtime trackers into one.** F.3 O5. Performance, not correctness.
- **R7-N1 — Reports library empty-state hero copy.** F.3 N1. Empty-state already exists; copy improvement only.
- **R7-O11 — Delete `LiveReasoningCard` + `LogPredictionAction` legacy components.** F.3 O11. Should have happened in Round 5 E.4; cleanup, not blocking.
- **R7-O6 — Mobile citation panel collapsed mode.** F.3 O6. Mobile polish.
- **R7-O4 — Audit `useChatPreferences` setter naming.** F.3 O4. Refactor.
- D.1 (Vertex DU) + D.2 (real GCS retrieval) remain credentialed-code-deferred from Round 5; unchanged in Round 6.
- `auth.setup.ts` wiring for live-credential F.1/F.2 walkthrough remains operator-side work, not blocking R6 because R6-SMOKE uses mocks.
- §M.16 (flag default flip in `feature_flags.ts` + `ConsumeChatLegacy.tsx` deletion) + §M.17 (CLAUDE.md §E mark CLOSED) remain deferred until 7-day clean watch post-F.4 reflip.

## §4 Architecture / approach decisions

### §4.1 Both gates run, automated first

Round 5 introduced per-PR operator visual review. It works, but the operator should be the *final* gate, not the *only* gate. Round 6 layers the automated smoke spec underneath: every chat-v2 PR runs the spec in CI; the spec must pass before the operator is asked to review. This means:

- The operator never reviews a PR where stage stepper is invisible (R6.1 contract is asserted in spec).
- The operator never reviews a PR where citation chips show raw `SIG.MSR.NNN` (R6.2 contract is asserted in spec).
- The operator never reviews a PR where layout has `ml-{10,56}` on the chat column (R6.4 contract is asserted in spec).
- The operator never reviews a PR where the action bar has `h-6 w-6` buttons (R6.6 contract is asserted in spec).

The operator's role narrows to "subjective visual quality + cross-domain regressions the spec cannot capture." That's the right division of labor.

### §4.2 Mock-route fixture, not live LLM

The smoke spec uses a mock route handler for `POST /api/chat/consume` (per forensic §7 fixture sketch). Reasons:

- Live LLM calls cost ~$0.05 per spec run; over 1000 PR-driven CI runs this adds up.
- Live LLM responses are non-deterministic; assertions on chip text or stage sequence flake.
- Live LLM calls take 5-15 s; mock-route streams finish in < 1 s.
- The smoke spec is testing *frontend reachability* — does V2 render what the route emits? It is NOT testing *backend correctness* — that's the `answer:eval` job's domain.

The fixture emits a canned stream: stage events (planning → tool_fetch → synthesis), two citation parts with non-empty snippets resolved against a hardcoded MSR row stub, a sample answer body containing two `[^1]` `[^2]` footnote markers, a footnote definition block, and a clean completion.

### §4.3 Per-PR EXEC briefs, not one mega-prompt

Same discipline as Round 5. Each of R6.1 → R6.6 + R6-SMOKE + R6-CI gets its own EXEC brief under `00_ARCHITECTURE/chat_v2_briefs/round6/`. Each brief is self-contained: scope, file:line precision, acceptance criteria, golden-set updates (none expected), smoke-spec assertion that validates the fix, branch name, PR title, screenshot capture commands.

### §4.4 Per-PR operator visual review gate retained

The Round 5 process change persists. Every Phase R6 PR description includes:

- `before.png` — current production V2 (`MARSYS_FLAG_CHAT_V2_ENABLED=true` on staging or pre-PR state).
- `after.png` — local dev with this PR's branch checked out.
- A 1-2 sentence written description of "what to look for."

Operator opens screenshots, opens local dev server, confirms the change, then approves via `gh pr review --approve` or web UI. Only after operator approval is `gh pr merge --squash --delete-branch` executed (no `--auto`).

### §4.5 PR sequencing

| Order | PR | Branch | Depends on | Why first |
|---|---|---|---|---|
| 1 | R6-SMOKE + R6-CI | `chore/chat-v2-r6/smoke-spec-and-workflow` | none | Land the gate BEFORE the fixes. R6-SMOKE will initially FAIL on `main` because the bugs are still there; that's the expected initial state — it proves the assertions are meaningful. Branch protection requires it green on the *fix* PRs but NOT on `main` until R6.1-R6.6 are all merged. (Alternatively, mark as non-blocking on `main` until all fixes land.) |
| 2 | R6.1 | `fix/chat-v2-r6/B1-unified-data-parts-hook` | R6-SMOKE | Highest leverage — one fix surfaces 5 capabilities |
| 3 | R6.4 | `fix/chat-v2-r6/L1L2-sidebar-layout-discipline` | R6-SMOKE | Independent of R6.1; visible to operator before reflip review |
| 4 | R6.5 | `fix/chat-v2-r6/L3-single-stream-button` | R6-SMOKE | Independent |
| 5 | R6.6 | `fix/chat-v2-r6/B6-action-bar-scale` | R6-SMOKE | Independent |
| 6 | R6.2 | `fix/chat-v2-r6/B2B3-inline-citation-footnotes` | R6.1 | Reads merged dataParts from R6.1 |
| 7 | R6.3 | `fix/chat-v2-r6/B4B5-enrich-citations` | R6.2 | Backend wiring landed before B4/B5 frontend assertion |
| 8 | F.4 reflip | `chore/chat-v2-r6/F4-master-flag-reflip` | R6.1-R6.6 merged + smoke green + operator F.3 sign-off | Final step |

## §5 Per-PR specification

Each row is a complete EXEC brief outline. Per §4.3 each will be expanded to a full brief at `00_ARCHITECTURE/chat_v2_briefs/round6/<id>.md` before its executor session.

### R6.1 — Unified `useDataParts(message)` hook

**Scope.** Author `platform/src/lib/chat-v2/useDataParts.ts` exporting:

```
type DataPart = { type: `data-${string}`; data: unknown }
function useDataParts(message: ThreadMessage): readonly DataPart[]
```

Implementation: returns the *merged + de-duplicated* set of:
- `message.metadata?.unstable_data ?? []` (filtered to `{type:'data-*'}`)
- `message.content` filtered to `{type:'data', name: string, data: unknown}` mapped to `{type: \`data-${name}\`, data}`

Replace these five call sites in `ConsumeChatV2.tsx` (lines per forensic §2 B1):
- Stage parsing (line 385 `filter type === 'data-stage'`)
- Tool call parsing (lines 549-554)
- Panel data (lines 261-285)
- Citation gate (lines 367-374)
- Prediction candidates (lines 410-419)

Plus the existing citation, correction, out-of-domain readers should be migrated to the same hook for uniformity (they already work — this is consolidation).

Plus in `platform/src/app/api/chat/consume/route.ts` `onFinish` block, add `writer.write({ type: 'data-stage', data: stagePart('synthesis', 'done', synthesisMs) })` after `result.toUIMessageStream` merge finishes (closes F.3 O1).

**Acceptance.**
- All five surfaces (stage stepper, tool call cards, panel ribbon, validator gate, prediction chips) appear on screen during a live query.
- Synthesis pip transitions from `running` (pulsing) to `done` (static).
- R6-SMOKE assertions L1.B1 + L1.O1 PASS.
- 0 TS errors, 0 ESLint errors.
- Existing tests stay green; one new unit test for `useDataParts` covering both source paths + de-duplication.

**Branch.** `fix/chat-v2-r6/B1-unified-data-parts-hook`

### R6.2 — Inline citation rendering via `[^N]` Markdown footnotes

**Scope.** Three coordinated changes:

1. `platform/src/lib/synthesis/prompts/synthesis_prompt_v2.ts` — change citation instruction from `→ SIG.MSR.NNN` format to `[^1]`, `[^2]` … `[^N]` GFM footnote format. Add per-prompt example showing the desired emit shape (literal `[^1]`, definition block at end).
2. `platform/src/components/markdown/MarkdownContent.tsx` — register a custom `footnoteReference` component (`remark-gfm` already parses `[^N]`; we override its React render). The component receives the footnote ID and looks up the citation in a context provided by V2AssistantText. Renders `NumberedCitation` at the inline site with click-to-pin behavior. Drop the `max-w-[68ch] mx-auto` (handled by R6.4).
3. `platform/src/components/consume/ConsumeChatV2.tsx` — in V2AssistantText (lines 196-256), drop `renderWithCitations` text-stripping (line 232-233) and drop the chip footer (lines 249-253). Provide the citation map via React Context to `MarkdownContent`.

**Acceptance.**
- Body text contains zero raw `SIG.MSR.NNN` references.
- Chips render inline at the `[^N]` site, not in a separate footer.
- Clicking a chip pins to `CitationSidePanel` (existing behavior preserved).
- R6-SMOKE assertions B2/B3 PASS.
- Synthesis golden eval at `npm run answer:eval` still produces correct citations (no eval regression).

**Branch.** `fix/chat-v2-r6/B2B3-inline-citation-footnotes`

### R6.3 — Enrich `extractCitations` against MSR signal store

**Scope.** In `platform/src/lib/citations/citation_data_part.ts`:

- Add async sibling `enrichCitations(citations: CitationPart[]): Promise<CitationPart[]>` that for each citation:
  - Look up the signal via `lib/citations/msr_lookup.ts` (or directly via `query_signal_state` against the loaded MSR JSON).
  - Populate `snippet` with the signal's gloss/title (or `null` if not found — never `''`).
  - Populate `layer` with the signal's true layer (L1 / L2.5 / L3).
- In `platform/src/app/api/chat/consume/route.ts` (line 1141-1161 area), after `extractCitations(lastAssistantText)`, await `enrichCitations` before forwarding via `writer.write`.

If `lib/citations/msr_lookup.ts` does not yet exist, scaffold it: synchronous lookup against MSR_v5_0.json loaded once at module init. ~30 lines.

**Acceptance.**
- Pinned citations render a non-empty snippet line in `CitationSidePanel`.
- R6-SMOKE assertion B4/B5 PASS (`snippet starts with a letter, not empty`).
- B.10 audit improves: every citation is auditable inline.

**Branch.** `fix/chat-v2-r6/B4B5-enrich-citations`

### R6.4 — Sidebar layout discipline

**Scope.** In `platform/src/components/consume/ConsumeChatV2.tsx`:

- Line 1466: **Remove** the `md:ml-10 md:ml-56` modifier from the chat-column wrapper.
- Lines 1443-1467: confirm sidebar wrapper remains `fixed inset-y-0 left-0 z-40` overlay; add explicit `pointer-events-none` to the collapsed-state strip wrapper (per forensic L2 fix), `pointer-events-auto` only on the expand button itself.
- Confirm chat column is `w-full mx-auto max-w-4xl` (centered in viewport).

In `platform/src/components/markdown/MarkdownContent.tsx`:
- Line 108: **Remove** the inner `max-w-[68ch] mx-auto` (let V2Message own centering).

In `platform/src/components/consume/ConversationSidebarV2.tsx`:
- Lines 238-261: **Delete** the in-sidebar "Collapse" `<` button. The header toggle at `ConsumeChatV2.tsx:1484-1492` remains the sole collapse/expand control. The "+" new-conversation button at lines 215-237 stays — distinct affordance.

**Acceptance.**
- At viewport 1280, 1440, 1920: chat column visually centered in the full viewport, not offset.
- Expanded sidebar overlays without shifting chat content.
- Exactly one sidebar toggle in the desktop layout (the header one).
- R6-SMOKE assertions L1 + L2 PASS (`margin-left: 0px`, `v2-sidebar-collapse count 0`).

**Branch.** `fix/chat-v2-r6/L1L2-sidebar-layout-discipline`

### R6.5 — Single send/stop button during streaming

**Scope.** In `platform/src/components/consume/ConsumeChatV2.tsx` lines 998-1033, the `{isRunning ? (...) : (...)}` ternary:

- Default streaming state renders the white `Square` stop button only (`ComposerPrimitive.Cancel`).
- The "cancel + resend" affordance moves behind one of (operator's choice in review):
  - Right-click → context menu with "Stop and send new query"
  - Long-press (~500 ms) → context menu
  - Hover tooltip + Shift+Enter keyboard shortcut documented

Pick one in the EXEC brief; the others are documented as future affordances.

**Acceptance.**
- During streaming there is exactly one visible button in the composer.
- The interrupt-send behavior remains *reachable* (via whichever affordance we chose).
- R6-SMOKE assertion L3 PASS (`single button visible during streaming`).

**Branch.** `fix/chat-v2-r6/L3-single-stream-button`

### R6.6 — Action-bar icon scale-up

**Scope.** In `platform/src/components/consume/ConsumeChatV2.tsx`:

- Line 327 (`V2RegenerateButton`): `h-6 w-6` → `h-8 w-8`; inner SVG `h-3 w-3` → `h-4 w-4`.
- Line 488 (Edit): same.
- Line 627 (Details): same.
- Line 638 (Copy): same.
- Container row: `gap-1` → `gap-1.5`.
- Add `min-h-[40px] min-w-[40px]` to each button for touch parity.

Apply consistently across all action-bar buttons (user, assistant, branch nav variants).

**Acceptance.**
- Action-bar buttons measure 32×32 px box with 16×16 px icons.
- Touch hit area ≥ 40×40 px.
- R6-SMOKE assertion B6 PASS (`height: 32px`).
- Visual review confirms parity with composer Send button proportions.

**Branch.** `fix/chat-v2-r6/B6-action-bar-scale`

### R6-SMOKE — Playwright walkthrough spec

**Scope.** Author:

- `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts` — one `test.describe('Round 6 walkthrough', ...)` block, one `test(...)` per F.3 finding in the forensic §7 assertion table (L1, L2, L3, L4, B1, B2/B3, B4/B5, B6, N2, O1 — N1 and N3 deferred to Round 7).
- `platform/tests/e2e/chat-v2/fixtures/round6-mock-route.ts` — registers a `page.route('**/api/chat/consume', ...)` handler that:
  - Streams stage events: `data-stage planning running` → `data-stage planning done` → `data-stage tool_fetch running` → `data-stage tool_fetch done` → `data-stage synthesis running`.
  - Streams two `data-citation` parts with non-empty snippets `{signal_id: 'SIG.MSR.001', snippet: 'Sun in Capricorn (10° 24\'')...', layer: 'L1'}` and `{signal_id: 'SIG.MSR.057', snippet: 'Saturn-ruled tenth lord activates ...', layer: 'L2.5'}`.
  - Streams an answer body `"The native's chart shows[^1]... Saturn period activates the tenth house[^2].\n\n[^1]: SIG.MSR.001\n[^2]: SIG.MSR.057"`.
  - Streams `data-stage synthesis done` then closes.
- Existing `platform/playwright.config.ts` — confirm `chat-v2` project's storageState dependency works against a no-auth mock-fixture mode (the smoke spec needs no real user).

**Acceptance.**
- `npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium` exits 0 after R6.1-R6.6 merge on a local branch.
- Spec runs in < 60 s wall time.
- Initial run on `main` (before R6 fixes land) demonstrates failures matching F.3 findings (proves assertions are meaningful).

**Branch.** `chore/chat-v2-r6/smoke-spec-and-workflow` (ships R6-CI in same PR — see below).

### R6-CI — Required-checks workflow

**Scope.** Author `.github/workflows/chat-v2-smoke.yml`:

```yaml
name: chat-v2 smoke

on:
  pull_request:
    paths:
      - 'platform/src/components/consume/ConsumeChatV2.tsx'
      - 'platform/src/components/chat-v2/**'
      - 'platform/src/components/chat/ConversationSidebarV2.tsx'
      - 'platform/src/app/api/chat/consume/route.ts'
      - 'platform/src/lib/synthesis/prompts/synthesis_prompt_v2.ts'
      - 'platform/src/lib/citations/**'
      - 'platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts'
      - 'platform/tests/e2e/chat-v2/fixtures/round6-mock-route.ts'

jobs:
  smoke:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: platform
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: platform/package-lock.json
      - run: npm ci
      - run: npx playwright install chromium
      - run: npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=github
```

**Acceptance.**
- Workflow runs and passes on a probe PR (e.g. README typo PR within the path filter — verify by adding a no-op character to `ConsumeChatV2.tsx` in a throwaway branch).
- Workflow runs and fails on a probe PR that *removes* `useDataParts` or *re-adds* `ml-{10,56}` to chat-column (verifies the gate is real, not vacuous).
- Branch protection rule on `main` adds `chat-v2 smoke / smoke` as a required check.

**Branch.** Same as R6-SMOKE (combined PR).

### F.4 — Master flag reflip

**Scope.** Update `.github/workflows/deploy.yml` env_vars block to set `MARSYS_FLAG_CHAT_V2_ENABLED=true`. Pair with explicit `gcloud run services update --update-env-vars MARSYS_FLAG_CHAT_V2_ENABLED=true` invocation per the `deploy_cloudrun_env_merge` memory.

**Acceptance.**
- All R6.1-R6.6 merged on `main`.
- `chat-v2 smoke / smoke` green on `main`.
- Operator re-runs F.3 walkthrough manually on staging Cloud Run revision. Operator approves.
- Master flag flipped. Production revision after flip has flag `true`.
- 7-day watch window begins.

**Branch.** `chore/chat-v2-r6/F4-master-flag-reflip`

## §6 Risk register

| Risk | Likelihood | Severity | Mitigation |
|---|---|---|---|
| `useDataParts` migration breaks existing citation/correction reading because they currently work | Low | Medium | Add unit test covering both source paths + de-duplication before refactoring; verify existing tests stay green; verify visual after each call-site swap |
| Synthesis prompt change (R6.2) regresses citation recall in `answer:eval` | Medium | High | Run `answer:eval` on the PR branch before merge; require recall ≥ 0.95; if recall drops, iterate on prompt or fall back to interim regex-replace path (forensic §2 B2/B3 alternate fix) |
| `MarkdownContent` `footnoteReference` integration breaks streamdown's incremental rendering during streaming | Medium | Medium | Smoke spec asserts streaming behavior; visual review during operator gate; if mid-stream rendering breaks, hold the PR and switch to interim regex-replace path |
| Mock-route fixture diverges from real route emission shape over time | Medium | Low | Add a comment in the fixture pointing to the real route file; add a follow-up Round 7 item to dual-run smoke against a recorded real-route trace once monthly |
| R6.4 layout fix breaks at non-1280/1440/1920 viewport widths | Medium | Medium | Add baseline visual capture at viewport widths 768, 1024, 1280, 1440, 1920 in operator review screenshot |
| Branch protection rule blocks legitimate non-chat-v2 PRs because path filter is too tight | Low | Low | Path filter scoped narrowly to V2-only files; verify before enabling required-check rule on `main` |
| R6.3 MSR lookup adds startup time | Low | Low | Module-init JSON load is ~10 ms; measure once after merge |
| F.4 reflip exposes additional regressions the smoke spec doesn't capture | Medium | High | Operator runs full F.3 walkthrough manually before reflip; 7-day watch with revert path ready (`gh workflow run rollback.yml` or git revert + redeploy) |
| Conversation rename/delete deferred to R7 leaves the decorative menu visible in production | High (it is true now) | Low | The `<span aria-hidden>` is decorative — it does not appear to most users as a button. If operator wants it removed for clarity, add a one-line R6.4 sub-item to hide the `<span>` until R7 wires it |
| Per-PR EXEC briefs balloon to 6+ documents in `00_ARCHITECTURE/chat_v2_briefs/round6/` | Medium | Low | Already an established pattern from Round 5; folder is git-tracked; cleaned up when workstream closes |

## §7 Open questions for operator

1. **R6.5 — Pick one of {long-press, right-click, hover-tooltip+Shift+Enter} for the "cancel + resend" affordance.** Forensic recommends right-click as most discoverable on desktop, with a hover tooltip explaining. The EXEC brief proceeds with that choice unless operator overrides.
2. **R6.3 — Should `enrichCitations` happen on the route (one-shot, after the model emits) or in `MarkdownContent`'s context provider (resolved on first render)?** Default is route-side per the forensic for separation of concerns. Operator confirm.
3. **R6-CI — Should the smoke workflow run in `merge_group` for queue-mode merges?** Probably yes — add `merge_group` trigger to the workflow alongside `pull_request`. Operator confirm.
4. **F.4 — How long is the post-reflip watch window?** Forensic uses "7-day clean watch" from the original §M.16 precondition. Operator confirm or override.
5. **Decorative three-dot menu in `ConversationSidebarV2.tsx:106-128`** — leave visible until R7 wires it, or hide via `display:none` in R6.4 as a one-liner addition? Hiding avoids confusing users; leaving signals upcoming feature.

These should be answered before the first EXEC brief is authored. Defaults shown above apply if operator does not override.

## §8 Sequencing and acceptance for workstream close

### §8.1 Round 6 internal sequencing

1. Author EXEC briefs for R6-SMOKE + R6-CI (combined). Land that PR first — sets up the gate.
2. Author EXEC briefs for R6.1, R6.4, R6.5, R6.6 in parallel — these are independent. Operator reviews each in turn; merge in order of review.
3. Author EXEC briefs for R6.2 and R6.3 — these depend on R6.1's hook being available. Author after R6.1 lands.
4. After all six P0 PRs merged + smoke green: operator re-runs F.3 walkthrough manually. Sign-off recorded in `CHAT_V2_PROGRESS.md`.
5. F.4 reflip PR opened, reviewed, merged. Production revision rolled with `MARSYS_FLAG_CHAT_V2_ENABLED=true`.
6. 7-day watch begins (~2026-05-21 → ~2026-05-28 if R6 ships clean).

### §8.2 Round 6 acceptance criteria

- [ ] All six P0 PRs merged to `main`.
- [ ] `chat-v2 smoke / smoke` green on `main` and configured as required check.
- [ ] Operator F.3 manual walkthrough on post-merge staging revision: PASS with no new findings.
- [ ] `npm run answer:eval` recall ≥ 0.95 after R6.2 + R6.3 land.
- [ ] `CHAT_V2_PROGRESS.md` updated with R6.* status rows + F.4 sign-off line.
- [ ] No Sentry alert volume increase attributable to V2 in the first 24h post-reflip.

### §8.3 Workstream close (§M discharge after Round 6 + watch)

After 7-day clean watch post-reflip:

- §M.16 — `feature_flags.ts` default for `MARSYS_FLAG_CHAT_V2_ENABLED` flipped from `false` to `true`. `MARSYS_FLAG_CHAT_V2_ENABLED` env override removed from `.github/workflows/deploy.yml`. `ConsumeChatLegacy.tsx` deleted. ConsumeChat wrapper trivially returns `<ConsumeChatV2 />`.
- §M.17 — `CLAUDE.md §E` updated: Chat V2 Big Bang workstream status → CLOSED with sealing artifact pointer. Memory file at `memory/project_chat_v2_workstream.md` rotated to historical record.

These remain Round 7 (or later) work — Round 6 only delivers the fix-wave + automated gate + reflip.

## §9 Changelog

- **v1.0 (2026-05-18, DRAFT)** — Initial authoring. Six P0 PRs (R6.1-R6.6) + automated smoke gate (R6-SMOKE + R6-CI) + F.4 reflip step + R7 deferred list. Per-PR operator visual review gate retained. Risk register, open questions, sequencing, acceptance criteria, workstream-close path documented. Pending operator sign-off + per-PR EXEC brief authoring before execution begins.

---

*End CHAT_V2_ROUND_6_PLAN v1.0 DRAFT.*
