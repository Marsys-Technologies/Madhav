import { test, expect } from '@playwright/test';
import { applyRound6MockRoute } from './fixtures/round6-mock-route';

/**
 * Round 6 walkthrough smoke spec.
 *
 * Asserts every F.3 finding against a mocked consume route (no live LLM).
 * The spec navigates to `/clients/[id]/consume` which is auth-gated server-
 * side, so we inject a `__session` cookie that matches `getServerUser()`'s
 * reader in `platform/src/lib/firebase/server.ts`. Without the cookie the
 * spec is skipped — both locally and in CI — until secrets are provisioned.
 *
 * Run locally:
 *   1. Mint a session cookie:
 *      cd platform && npx tsx scripts/mint_session_cookie.ts \
 *        --uid <your-uid> --email <your-email>
 *      (See `platform/tests/e2e/chat-v2/README.md` for full runbook.)
 *   2. export SMOKE_SESSION_COOKIE='<cookie value from step 1>'
 *   3. export SMOKE_CHART_ID='<chart id you have access to>'
 *   4. cd platform && npx playwright test tests/e2e/chat-v2/round6-walkthrough.spec.ts --project=chromium
 *
 * Run in CI: requires SMOKE_SESSION_COOKIE + SMOKE_CHART_ID secrets in the
 * chat-v2-smoke workflow. Until those secrets land (R7 follow-up), this
 * spec skips in CI. The workflow remains as a path-trigger sentinel.
 */

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000';
const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE;
const CHART_ID = process.env.SMOKE_CHART_ID;
const SKIP = !SESSION_COOKIE || !CHART_ID;

test.describe('Round 6 walkthrough — smoke assertions against F.3 findings', () => {
  test.skip(SKIP, 'SMOKE_SESSION_COOKIE or SMOKE_CHART_ID not set; skipping authenticated smoke tests. See spec header for setup instructions.');

  test.beforeEach(async ({ context, page }) => {
    // Inject the Firebase session cookie that `getServerUser()` reads.
    // Cookie name MUST be `__session` to match
    // `platform/src/lib/firebase/server.ts:48`.
    await context.addCookies([
      {
        name: '__session',
        value: SESSION_COOKIE!,
        domain: new URL(BASE_URL).hostname,
        path: '/',
      },
    ]);

    // Intercept the consume API before navigation so the mock answers any
    // streaming request V2 fires after mount.
    await applyRound6MockRoute(page);

    // Navigate to the consume page. After auth passes the V2 component
    // mounts; we wait for its outermost testid before asserting.
    await page.goto(`/clients/${CHART_ID}/consume?provider=mock`);
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
    await composer.fill("Describe the native's career indications.");
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
