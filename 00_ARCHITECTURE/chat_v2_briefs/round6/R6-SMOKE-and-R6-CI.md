---
name: R6-SMOKE + R6-CI EXEC BRIEF — Playwright walkthrough spec + chat-v2-smoke workflow
canonical_id: CHAT_V2_R6_SMOKE_AND_CI_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored: 2026-05-18
governing_plan: 00_ARCHITECTURE/CHAT_V2_ROUND_6_PLAN_v1_0.md §5
governing_forensic: 00_ARCHITECTURE/CHAT_V2_F3_FORENSIC_v1_0.md §7
branch: chore/chat-v2-r6/smoke-spec-and-workflow
base: main
pr_title: "chore(chat-v2/r6): Playwright smoke spec + required-check workflow"
estimated_loc: ~400
estimated_files: 3
may_touch:
  - platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts (new)
  - platform/tests/e2e/chat-v2/fixtures/round6-mock-route.ts (new)
  - .github/workflows/chat-v2-smoke.yml (new)
  - platform/playwright.config.ts (only if chat-v2 project needs storageState bypass for mock fixture)
must_not_touch:
  - platform/src/components/** (this is the gate, not the fix)
  - platform/src/app/api/chat/consume/route.ts
  - platform/src/lib/synthesis/**
  - any feature flag file
  - any other workflow file
---

# §1 Mission

Round 5 shipped 11 PRs and a per-PR operator visual review gate. When that gate ran (F.3 walkthrough, 2026-05-18), it caught **13+ regressions** — stage stepper invisible, raw `SIG.MSR.NNN` markers left in body text, citation chips rendering in a footer instead of inline, layout offset from viewport center — all bugs that unit tests and type-checking had passed because they were testing code correctness, not UI reachability. The pattern is clear: the operator should not be the one who discovers that `stageHistory.length` is permanently zero because the route emits to `message.content` while V2 reads only `message.metadata.unstable_data`. That class of bug belongs in a binary CI gate.

This PR installs the gate. A Playwright spec (`round6-walkthrough.spec.ts`) asserts every F.3 finding's success criterion using a mocked consume route — no live LLM credentials needed, < 60 s wall time. A required-check workflow (`chat-v2-smoke.yml`) runs it on every PR that touches the files identified in Forensic Pattern A/B/C. The gate lands **before** any R6 fix PR. Its initial state on `main` is: **all 9 enabled tests FAIL** — because the bugs are still present. That failure mode is intentional. It proves the assertions are meaningful. Each fix PR (R6.1–R6.6) is expected to turn the assertions it addresses from FAIL to PASS. By the time all six fix PRs land, the spec must be fully green.

The automated gate narrows the operator's role to subjective visual quality and cross-domain regressions the spec cannot capture. That is the right division of labor between machine and human review.

# §2 Scope

Three files. No source code under `platform/src/` changes.

## File 1 — `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts`

One `test.describe('Round 6 walkthrough', ...)` block. One `test()` per enabled F.3 finding row in Forensic §7. The tests that are enabled in this PR (and will FAIL on current `main`) are:

| Test ID | F.3 finding | Enabled? |
|---|---|---|
| L1 | Chat content offset from viewport center | YES |
| L2 | Two sidebar toggle buttons | YES |
| L3 | Two send/stop buttons during streaming | YES |
| B1 | Stage stepper not visible | YES |
| B2/B3 | Raw `SIG.MSR.NNN` in body + chips in footer | YES |
| B4/B5 | Empty citation snippet in panel | YES |
| B6 | Regenerate icon too small | YES |
| O1 | Synthesis stage never transitions to `done` | YES |
| N1 | Reports library empty-state | YES |
| N2 | Sidebar grouping typography | DEFERRED to R7 (CSS letter-spacing assertion is brittle cross-platform) |
| N3 | Three-dot menu rename/delete | DEFERRED to R7 (N3 is deferred to R7 fix-wave per plan §3.4) |
| L4 | Sidebar bottom logo | DEFERRED to R7 (L4 is P1, not blocking reflip) |

Deferred tests are **not scaffolded as skipped tests** — they are simply absent. They will be added when their corresponding fix PRs are authored (R7 briefs).

## File 2 — `platform/tests/e2e/chat-v2/fixtures/round6-mock-route.ts`

Exports an async helper `applyRound6MockRoute(page: Page): Promise<void>` that registers a `page.route('**/api/chat/consume', ...)` handler. The handler fulfills the request with a canned SSE stream (see §3.3 for the exact byte sequence). No LLM call. No env vars beyond standard CI defaults.

## File 3 — `.github/workflows/chat-v2-smoke.yml`

GitHub Actions workflow. Trigger: `pull_request` + `merge_group` (Decision 3). Path filter covers the six P0 fix targets + the spec and fixture files themselves. Steps: checkout → `npm ci` → `npx playwright install chromium` → run spec.

# §3 Implementation specification

## §3.1 `round6-walkthrough.spec.ts` — full type signatures and structure

```typescript
import { test, expect, Page } from '@playwright/test';
import { applyRound6MockRoute } from './fixtures/round6-mock-route';

// One describe block wraps all tests. beforeEach navigates to the chat-v2
// URL with the master flag enabled (via query param or cookie set in fixture).
// applyRound6MockRoute intercepts /api/chat/consume before navigation.

test.describe('Round 6 walkthrough — smoke assertions against F.3 findings', () => {
  test.beforeEach(async ({ page }) => {
    await applyRound6MockRoute(page);
    // Navigate to the consume page with chat-v2 enabled.
    // The consume page is at /clients/[id]/consume. Use the dev-server
    // test client ID (check playwright.config.ts for the configured base URL
    // and the test client fixture). If no test client is configured, add
    // PLAYWRIGHT_CHAT_CLIENT_ID to the .env.test file and read it here.
    const clientId = process.env.PLAYWRIGHT_CHAT_CLIENT_ID ?? 'test-client';
    await page.goto(`/clients/${clientId}/consume?provider=mock`);
    // Wait for the page shell to mount before any test asserts.
    await page.waitForSelector('[data-testid="v2-chat-shell"]', { timeout: 10_000 });
  });

  // ── L1 — Chat column margin ────────────────────────────────────────────
  test('L1: chat column has no left margin offset', async ({ page }) => {
    const col = page.getByTestId('v2-chat-column');
    await expect(col).toHaveCSS('margin-left', '0px');
    // Spot-check at two additional viewport widths via resize.
    await page.setViewportSize({ width: 1440, height: 900 });
    await expect(col).toHaveCSS('margin-left', '0px');
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(col).toHaveCSS('margin-left', '0px');
  });

  // ── L2 — Single sidebar toggle ─────────────────────────────────────────
  test('L2: exactly one sidebar collapse control exists (the header toggle)', async ({ page }) => {
    // No in-sidebar collapse button.
    await expect(page.getByTestId('v2-sidebar-collapse')).toHaveCount(0);
    // The header toggle is present.
    await expect(page.getByTestId('v2-desktop-sidebar-toggle')).toHaveCount(1);
  });

  // ── L3 — Single streaming button ──────────────────────────────────────
  test('L3: exactly one button visible in composer during streaming', async ({ page }) => {
    // Submit a query to trigger the mocked stream.
    const composer = page.getByTestId('v2-composer-input');
    await composer.fill('What does the chart say about career?');
    await page.getByTestId('v2-composer-send').click();
    // The mock stream takes ~500 ms; assert during that window.
    // We expect exactly one button: the stop button.
    await expect(
      page.locator('[data-testid="v2-abort-btn"], [data-testid="v2-interrupt-send-btn"]')
    ).toHaveCount(1, { timeout: 3_000 });
    // The send button must not be visible simultaneously.
    await expect(page.getByTestId('v2-composer-send')).not.toBeVisible();
  });

  // ── B1 — Stage stepper visible during streaming ────────────────────────
  test('B1: stage stepper renders during streaming', async ({ page }) => {
    const composer = page.getByTestId('v2-composer-input');
    await composer.fill('Tell me about the tenth house.');
    await page.getByTestId('v2-composer-send').click();
    // Stage stepper mounts when stageHistory.length > 0 and isStreaming.
    // NOTE: this assertion requires v2-stage-stepper testid on StageStepper.
    // That testid is added by the R6.1 PR. On current main this FAILS because
    // the element does not render (data-parts source-of-truth bug).
    await expect(page.getByTestId('v2-stage-stepper')).toBeVisible({ timeout: 5_000 });
    // The synthesis pip must also be visible (first stage emitted by mock).
    // NOTE: v2-stage-synthesis testid added by R6.1.
    await expect(page.getByTestId('v2-stage-synthesis')).toBeVisible();
  });

  // ── B2/B3 — No raw SIG.MSR.NNN in body; inline chips present ──────────
  test('B2/B3: no raw signal markers in message body; citation chips are inline', async ({ page }) => {
    const composer = page.getByTestId('v2-composer-input');
    await composer.fill('Describe the native\'s career indications.');
    await page.getByTestId('v2-composer-send').click();
    // Wait for the stream to complete (mock stream ends after ~800 ms).
    await page.waitForSelector('[data-testid="v2-message-text"]', { timeout: 8_000 });
    const msgText = page.getByTestId('v2-message-text').first();
    // No raw SIG.MSR.NNN should appear in rendered text.
    // NOTE: v2-message-text testid added by R6.2 (currently may not exist on main).
    await expect(msgText).not.toContainText(/SIG\.MSR\.\d{3}/);
    // At least one inline citation chip must be present.
    // NOTE: v2-citation-badge testid added by R6.2.
    await expect(page.getByTestId('v2-citation-badge').first()).toBeVisible();
  });

  // ── B4/B5 — Citation panel shows non-empty snippet ────────────────────
  test('B4/B5: pinning a citation opens the panel with a non-empty snippet', async ({ page }) => {
    const composer = page.getByTestId('v2-composer-input');
    await composer.fill('What does Jupiter say about the fifth house?');
    await page.getByTestId('v2-composer-send').click();
    await page.waitForSelector('[data-testid="v2-citation-badge"]', { timeout: 8_000 });
    // Click the first citation chip to pin it.
    await page.getByTestId('v2-citation-badge').first().click();
    // The citation side panel should open.
    // NOTE: v2-citation-panel-item testid must already exist in CitationSidePanel.
    // If it does not, the R6.3 brief adds it.
    await expect(page.getByTestId('v2-citation-panel-item').first()).toBeVisible({ timeout: 3_000 });
    // The snippet text must start with a letter (not be empty or placeholder).
    const snippetText = await page.getByTestId('v2-citation-panel-item').first().textContent();
    expect(snippetText?.trim()).toMatch(/^[A-Za-z]/);
  });

  // ── B6 — Regenerate button is 32 px tall ──────────────────────────────
  test('B6: action-bar regenerate button height is 32px (h-8)', async ({ page }) => {
    const composer = page.getByTestId('v2-composer-input');
    await composer.fill('Summarize the chart briefly.');
    await page.getByTestId('v2-composer-send').click();
    // Wait for stream to finish so the action bar appears.
    await page.waitForSelector('[data-testid="v2-regenerate-btn"]', { timeout: 10_000 });
    await expect(page.getByTestId('v2-regenerate-btn')).toHaveCSS('height', '32px');
  });

  // ── O1 — Synthesis stage transitions to done ──────────────────────────
  test('O1: synthesis stage pip transitions from running to done after stream ends', async ({ page }) => {
    const composer = page.getByTestId('v2-composer-input');
    await composer.fill('What is the Dasha sequence for the next 10 years?');
    await page.getByTestId('v2-composer-send').click();
    // Wait for the mock stream to fully complete.
    await page.waitForSelector('[data-testid="v2-stage-synthesis"]', { timeout: 8_000 });
    // After stream ends, the synthesis pip should be in the done state.
    // The done state removes `animate-pulse` and may add a `done` data attribute.
    // Both conditions are checked. NOTE: v2-stage-synthesis testid added by R6.1.
    const pip = page.getByTestId('v2-stage-synthesis');
    // Running state: has animate-pulse class. Done state: does NOT have it.
    await expect(pip).not.toHaveClass(/animate-pulse/, { timeout: 8_000 });
  });

  // ── N1 — Reports library empty-state is visible ───────────────────────
  test('N1: reports library shows empty-state copy when no reports exist', async ({ page }) => {
    // Open the reports panel. The trigger depends on ConsumeChatV2 header wiring.
    // NOTE: v2-reports-btn testid must exist in the header (check ConsumeChatV2.tsx:1516 area).
    // If not present, the R6 docs brief adds it; note below.
    const reportsBtn = page.getByTestId('v2-reports-btn');
    if (await reportsBtn.isVisible()) {
      await reportsBtn.click();
      await expect(
        page.getByText(/No reports yet|Reports library is empty/i)
      ).toBeVisible({ timeout: 3_000 });
    } else {
      // testid not yet added — this test will fail on current main with element-not-found.
      // R6.4 or its companion brief must add data-testid="v2-reports-btn" to the trigger.
      await expect(reportsBtn).toBeVisible();
    }
  });
});
```

### Testid map — what each R6 PR must add

The table below is the authority on which testid goes into which fix PR. Executor of each PR brief must add the listed testid before the smoke spec can turn green for that finding.

| testid | Component file | Added by PR |
|---|---|---|
| `v2-chat-shell` | ConsumeChatV2.tsx root wrapper | R6.4 |
| `v2-chat-column` | ConsumeChatV2.tsx chat-column div | R6.4 |
| `v2-desktop-sidebar-toggle` | ConsumeChatV2.tsx:1484 header toggle button | R6.4 |
| `v2-sidebar-collapse` | ConversationSidebarV2.tsx:238 (delete this element entirely in R6.4) | R6.4 (deletes it) |
| `v2-composer-input` | ConsumeChatV2.tsx ComposerPrimitive.Input | R6.5 or existing |
| `v2-composer-send` | ConsumeChatV2.tsx send ArrowUp button | R6.5 or existing |
| `v2-abort-btn` | ConsumeChatV2.tsx ComposerPrimitive.Cancel (stop button) | R6.5 |
| `v2-interrupt-send-btn` | ConsumeChatV2.tsx right-click cancel+resend affordance | R6.5 |
| `v2-stage-stepper` | StageStepper.tsx root element | R6.1 |
| `v2-stage-synthesis` | StageStepper.tsx synthesis pip element | R6.1 |
| `v2-message-text` | ConsumeChatV2.tsx V2AssistantText rendered text wrapper | R6.2 |
| `v2-citation-badge` | NumberedCitation.tsx root element | R6.2 |
| `v2-citation-panel-item` | CitationSidePanel.tsx per-citation row element | R6.3 or existing |
| `v2-regenerate-btn` | ConsumeChatV2.tsx:327 V2RegenerateButton wrapper | R6.6 |
| `v2-reports-btn` | ConsumeChatV2.tsx header reports trigger | R6.4 or existing |

**Critical rule**: The smoke spec itself must NOT add or modify any testid in source files. This table is notification to the P0 PR briefs. The smoke spec references the testids; the fix PRs add them.

## §3.2 `round6-mock-route.ts` — fixture type signatures and stream sketch

```typescript
import { Page, Route, Request } from '@playwright/test';

/**
 * Registers a page.route handler that intercepts POST /api/chat/consume
 * and returns a canned SSE stream representing a complete V2 response.
 * The stream includes:
 *   - Five stage events (planning → tool_fetch → synthesis, each with running + done)
 *   - Two data-citation parts with non-empty snippets
 *   - An answer body with two [^N] footnote markers
 *   - A footnote definition block at end-of-answer
 *   - A final data-stage synthesis done event
 *   - A proper SSE stream termination
 *
 * Call this BEFORE page.goto() so the route is registered before the request fires.
 */
export async function applyRound6MockRoute(page: Page): Promise<void> {
  await page.route('**/api/chat/consume', handleConsumeRoute);
}

async function handleConsumeRoute(route: Route, request: Request): Promise<void> {
  if (request.method() !== 'POST') {
    await route.continue();
    return;
  }

  const encoder = new TextEncoder();

  // Build the canned SSE stream as a ReadableStream body.
  const stream = new ReadableStream({
    async start(controller) {
      const emit = (line: string) => {
        controller.enqueue(encoder.encode(`${line}\n`));
      };

      // ── Stage: planning running ──────────────────────────────────────
      emit('data: {"type":"data","name":"stage","data":{"stage":"planning","state":"running","elapsed_ms":0}}');
      emit('');
      await delay(50);

      emit('data: {"type":"data","name":"stage","data":{"stage":"planning","state":"done","elapsed_ms":52}}');
      emit('');
      await delay(50);

      // ── Stage: tool_fetch running ────────────────────────────────────
      emit('data: {"type":"data","name":"stage","data":{"stage":"tool_fetch","state":"running","elapsed_ms":52}}');
      emit('');
      await delay(50);

      emit('data: {"type":"data","name":"stage","data":{"stage":"tool_fetch","state":"done","elapsed_ms":105}}');
      emit('');
      await delay(50);

      // ── Stage: synthesis running ─────────────────────────────────────
      emit('data: {"type":"data","name":"stage","data":{"stage":"synthesis","state":"running","elapsed_ms":105}}');
      emit('');
      await delay(50);

      // ── Citation parts with non-empty snippets ───────────────────────
      // signal SIG.MSR.001 — Sun in Capricorn (L1 fact)
      emit('data: {"type":"data","name":"citation","data":{"index":1,"signal_id":"SIG.MSR.001","layer":"L1","snippet":"Sun in Capricorn (10° 24′) — tenth lord in own sign, exalted in the angular tenth house. Core strength signal for career and public standing."}}');
      emit('');

      // signal SIG.MSR.057 — Saturn ruling the Tenth (L2.5 derivation)
      emit('data: {"type":"data","name":"citation","data":{"index":2,"signal_id":"SIG.MSR.057","layer":"L2.5","snippet":"Saturn rules the tenth house (Capricorn Ascendant). Its dasha periods activate career themes with the weight of its planetary period."}}');
      emit('');
      await delay(50);

      // ── Answer body — streamed in three chunks ───────────────────────
      emit('data: {"type":"text-delta","textDelta":"The native\'s chart reveals remarkable career potential through a combination of stellar placements.[^1] "}');
      emit('');
      await delay(30);

      emit('data: {"type":"text-delta","textDelta":"The tenth house receives Saturn\'s dasha energy in the coming period, activating ambition structures with unusual intensity.[^2]\\n\\n"}');
      emit('');
      await delay(30);

      // Footnote definition block (GFM footnotes, rendered by MarkdownContent after R6.2)
      emit('data: {"type":"text-delta","textDelta":"[^1]: SIG.MSR.001\\n[^2]: SIG.MSR.057\\n"}');
      emit('');
      await delay(30);

      // ── Stage: synthesis done ────────────────────────────────────────
      emit('data: {"type":"data","name":"stage","data":{"stage":"synthesis","state":"done","elapsed_ms":315}}');
      emit('');
      await delay(20);

      // ── Stream termination ───────────────────────────────────────────
      emit('data: [DONE]');
      emit('');

      controller.close();
    }
  });

  await route.fulfill({
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    },
    body: stream,
  });
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

**Key notes for the executor:**

- The SSE `data:` lines use the `@assistant-ui/react-ai-sdk` wire format. `type:"data"` with `name:"stage"` maps to `DataMessagePart { type:'data', name:'stage', data:{...} }` which lands in `message.content`. After R6.1 fixes the data-parts source-of-truth bug, V2Message will read these correctly.
- Citation parts use `name:"citation"` to match `extractCitations` output shape.
- The answer body uses `[^1]` and `[^2]` GFM footnote markers. After R6.2 these render as `NumberedCitation` chips inline. On current `main` they render as raw text (the `remark-gfm` footnote plugin needs the custom component override).
- The synthesis `state:"done"` event at the end closes O1. After R6.1 adds the matching `stagePart('synthesis','done')` route emission and the data-parts hook reads it, the pip transitions out of `animate-pulse`.
- `page.route` must be registered BEFORE `page.goto`. The `beforeEach` in the spec calls `applyRound6MockRoute(page)` first, then navigates.

## §3.3 `.github/workflows/chat-v2-smoke.yml` — exact YAML

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
  merge_group:
    branches:
      - main

jobs:
  smoke:
    name: smoke
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

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright Chromium
        run: npx playwright install chromium --with-deps

      - name: Run chat-v2 smoke spec
        run: npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=github
        env:
          PLAYWRIGHT_CHAT_CLIENT_ID: ${{ vars.PLAYWRIGHT_CHAT_CLIENT_ID || 'test-client' }}
          # No LLM credentials needed — mock route intercepts the API call.
          # MARSYS_FLAG_CHAT_V2_ENABLED is passed via ?provider=mock query param
          # in the spec's beforeEach; no env var required for the flag in CI.
```

**Decision 3 baked in**: `merge_group` trigger is present alongside `pull_request`. This ensures the smoke gate runs for queue-mode merges (GitHub's merge queue) as well as ordinary PR checks.

**Job name is exactly `smoke`**: The required-check rule on `main` branch protection must reference `chat-v2 smoke / smoke` (workflow name `/` job name). The executor must not rename the job.

# §4 Acceptance criteria

## Criterion 1 — Spec runs cleanly
```bash
cd platform
npm ci
npx playwright install chromium
npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium --reporter=list
```

This command must exit **with failure (exit code 1)** on current `main` because the bugs are still present. The failure output must show 9 tests in the `Round 6 walkthrough` suite, each failing with a specific reason. See the per-test expected failure mode table below.

## Per-test expected state on current `main` (before any R6 fix lands)

| Test | Expected result on current `main` | Expected result after R6.x |
|---|---|---|
| L1 | **FAIL** — `v2-chat-column` has `margin-left: 40px` (collapsed) or `margin-left: 224px` (expanded), not `0px` | PASS after R6.4 |
| L2 | **FAIL** — `v2-sidebar-collapse` found with count 1 (the in-sidebar button exists), or `v2-desktop-sidebar-toggle` not found | PASS after R6.4 |
| L3 | **FAIL** — two buttons visible during streaming (both `v2-abort-btn` and the golden ArrowUp appear), or testids not found | PASS after R6.5 |
| B1 | **FAIL** — `v2-stage-stepper` never appears within 5000ms (stageHistory empty due to data-parts bug) | PASS after R6.1 |
| B2/B3 | **FAIL** — `v2-message-text` contains `SIG.MSR.NNN` raw text, or `v2-citation-badge` not found in the message body | PASS after R6.2 |
| B4/B5 | **FAIL** — `v2-citation-panel-item` snippet text is empty or starts with whitespace | PASS after R6.3 |
| B6 | **FAIL** — `v2-regenerate-btn` height is `24px` (h-6), not `32px` (h-8) | PASS after R6.6 |
| O1 | **FAIL** — `v2-stage-synthesis` retains `animate-pulse` class after stream ends (synthesis-done event never emitted or never reaches the pip) | PASS after R6.1 |
| N1 | **FAIL** — `v2-reports-btn` not found or reports panel shows no empty-state text | PASS after R6.4 (empty-state copy already exists; may need testid only) |

## Criterion 2 — Spec is self-contained (no live LLM)
Running the spec with no `ANTHROPIC_API_KEY`, `GOOGLE_CLOUD_PROJECT`, or any LLM credential in the environment must produce the same results. The mock fixture replaces all backend SSE.

## Criterion 3 — Workflow YAML lints clean
```bash
# Install actionlint:
brew install actionlint   # macOS
# or: go install github.com/rhysd/actionlint/cmd/actionlint@latest

actionlint .github/workflows/chat-v2-smoke.yml
# Expected: no output (exit 0)
```

## Criterion 4 — Zero source code changes
```bash
git diff HEAD -- 'platform/src/**'
# Expected: empty output
```

## Criterion 5 — Playwright config compatibility
Verify `playwright.config.ts` has a project named `chromium` (or equivalent) that can run against a `localhost` dev server. The smoke spec uses no `storageState` (mock fixture bypasses auth). If the existing `chat-v2` project requires a `storageState` that a fresh CI environment won't have, add an explicit `use: { storageState: undefined }` override in `playwright.config.ts` **only for the `chat-v2-smoke` project** (a new named project that runs only `round6-walkthrough.spec.ts`). This is the only permitted `playwright.config.ts` change.

# §5 Hard constraints

1. **Mock route does NOT call any LLM.** The fixture returns a fixed byte sequence. No `process.env.ANTHROPIC_API_KEY` access. No `fetch()` to any external service. The spec must run in an environment with zero LLM credentials.

2. **Spec must NOT add or modify any `data-testid` in source files.** The testid map in §3.1 is a notification to P0 brief authors. The spec references those testids; the fix PRs add them. If a testid does not yet exist on `main`, the corresponding test will fail with "element not found" — that is the expected failure mode on `main`. It does not mean the spec should work around the missing testid.

3. **Workflow path filter EXACTLY matches plan §5 R6-CI.** Do not narrow (e.g. removing `platform/src/lib/citations/**`) or broaden (e.g. adding `platform/src/**`). The eight path entries in §3.3 are authoritative.

4. **`merge_group` trigger is required.** Decision 3 from the plan §7 open-questions defaults: the `merge_group` trigger is added alongside `pull_request`. Do not omit it.

5. **Branch protection NOT configured in this PR.** The operator configures `chat-v2 smoke / smoke` as a required check via the GitHub UI manually, AFTER the probe PR confirms the workflow triggers correctly. This PR does not modify `.github/branch-protection.yml` or any equivalent declarative protection file (none exists in this repo). Document the manual step in PR description.

6. **No existing workflow files modified.** `deploy.yml`, `ci.yml`, or any other workflow file is untouched. Only the new `chat-v2-smoke.yml` is created.

7. **No feature flag files modified.** The master flag `MARSYS_FLAG_CHAT_V2_ENABLED` remains `false` in all files. The smoke spec reaches the V2 consume page via a `?provider=mock` query parameter (added in E.3 / PR #71) plus the mock route fixture, not by flipping the flag.

# §6 Verification commands

```bash
# From repo root:
cd platform

# 1. Run the smoke spec (expect 9 FAIL on current main)
npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts \
  --project=chromium \
  --reporter=list

# Expected output (current main):
#
#   ✗ [chromium] › chat-v2/round6-walkthrough.spec.ts › Round 6 walkthrough … L1: chat column has no left margin offset (xx ms)
#   ✗ [chromium] › chat-v2/round6-walkthrough.spec.ts › Round 6 walkthrough … L2: exactly one sidebar collapse control exists (the header toggle) (xx ms)
#   ✗ [chromium] › chat-v2/round6-walkthrough.spec.ts › Round 6 walkthrough … L3: exactly one button visible in composer during streaming (xx ms)
#   ✗ [chromium] › chat-v2/round6-walkthrough.spec.ts › Round 6 walkthrough … B1: stage stepper renders during streaming (xx ms)
#   ✗ [chromium] › chat-v2/round6-walkthrough.spec.ts › Round 6 walkthrough … B2/B3: no raw signal markers in message body; citation chips are inline (xx ms)
#   ✗ [chromium] › chat-v2/round6-walkthrough.spec.ts › Round 6 walkthrough … B4/B5: pinning a citation opens the panel with a non-empty snippet (xx ms)
#   ✗ [chromium] › chat-v2/round6-walkthrough.spec.ts › Round 6 walkthrough … B6: action-bar regenerate button height is 32px (h-8) (xx ms)
#   ✗ [chromium] › chat-v2/round6-walkthrough.spec.ts › Round 6 walkthrough … O1: synthesis stage pip transitions from running to done after stream ends (xx ms)
#   ✗ [chromium] › chat-v2/round6-walkthrough.spec.ts › Round 6 walkthrough … N1: reports library shows empty-state copy when no reports exist (xx ms)
#
#   9 failed

# 2. Lint the workflow YAML
actionlint .github/workflows/chat-v2-smoke.yml
# Expected: (no output, exit 0)

# 3. Confirm zero source changes
git diff HEAD -- 'platform/src/**'
# Expected: (empty)

# 4. List the three new files created by this PR
git status --short
# Expected lines (among others):
#   A  .github/workflows/chat-v2-smoke.yml
#   A  platform/tests/e2e/chat-v2/fixtures/round6-mock-route.ts
#   A  platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts
```

# §7 Post-merge steps (operator)

These steps happen AFTER this PR merges to `main`. They are operator actions, not executor actions.

## Step 1 — Probe PR to verify workflow triggers

Open a throwaway branch (`git checkout -b probe/chat-v2-smoke-probe`) and make a whitespace-only no-op change to `platform/src/components/consume/ConsumeChatV2.tsx` (e.g. add a trailing space to a comment line). Push and open a PR. Confirm:

- The `chat-v2 smoke` workflow runs under the PR's checks tab.
- The workflow reaches the `Run chat-v2 smoke spec` step (it will show 9 failures — that is correct and expected).
- Close/delete the probe PR and branch without merging.

## Step 2 — Enable required check on main branch protection

In GitHub → repository → Settings → Branches → `main` protection rule → "Require status checks to pass before merging":

- Search for and add: `chat-v2 smoke / smoke`
- The rule should apply to branches matching `fix/chat-v2-*` and `chore/chat-v2-r6/*`.
- Do NOT make it block ALL PRs (it only triggers on the paths listed in the workflow) — but the required-check setting is global. Confirm that the path filter is narrow enough that the check is simply "not required" (skipped) on PRs that don't touch those paths (GitHub treats a skipped required check as passing).

## Step 3 — Author and execute R6.1 brief

The next Antigravity round branches fresh from `main` (after this PR merges). Executor follows the R6.1 EXEC brief at `00_ARCHITECTURE/chat_v2_briefs/round6/R6.1-unified-data-parts-hook.md` (to be authored next session).

Each fix PR is expected to turn a subset of the 9 failing tests green. Full green = all six P0 PRs merged.

## Step 4 — F.4 reflip (after all six P0 PRs green)

Only after all 9 tests pass on `main`:

1. Operator runs F.3 manual walkthrough on staging revision with `MARSYS_FLAG_CHAT_V2_ENABLED=true`.
2. Operator signs off in `CHAT_V2_PROGRESS.md`.
3. F.4 reflip PR is executed.

---

*End R6-SMOKE + R6-CI EXEC BRIEF v1.0.*
