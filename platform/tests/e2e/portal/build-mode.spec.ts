import { test, expect } from '@playwright/test'

/**
 * Portal Redesign R3b — Build mode E2E smoke tests.
 * Covers EXEC_BRIEF §3.2: three-pane layout, message send, streaming render,
 * command palette via Cmd+K.
 *
 * Run: npx playwright test tests/e2e/portal/build-mode.spec.ts
 * Requires: dev server at BASE_URL (default http://localhost:3000),
 *           SMOKE_SESSION_COOKIE (super_admin session),
 *           SMOKE_CHART_ID (a chart the session user has access to).
 */

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000'
const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE
const CHART_ID = process.env.SMOKE_CHART_ID
const SKIP = !SESSION_COOKIE || !CHART_ID

test.describe('/clients/[id]/build — R3b Build mode', () => {
  test.skip(SKIP, 'SMOKE_SESSION_COOKIE or SMOKE_CHART_ID not set; skipping authenticated smoke tests')

  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      {
        name: 'session',
        value: SESSION_COOKIE!,
        domain: new URL(BASE_URL).hostname,
        path: '/',
      },
    ])
  })

  // ── Three-pane layout ──────────────────────────────────────────────────────

  test('renders three-pane layout: sidebar | chat area | right pane', async ({ page }) => {
    await page.goto(`${BASE_URL}/clients/${CHART_ID}/build`)

    // Left pane — ConversationSidebar: "New conversation" button is a reliable anchor
    await expect(page.getByText('New conversation')).toBeVisible()

    // Center pane — Composer textarea (placeholder when no messages yet)
    const composer = page.getByRole('textbox')
    await expect(composer).toBeVisible()

    // Right pane — BuildRightPane renders a "Pyramid layers" toggle button
    await expect(page.getByRole('button', { name: /Pyramid layers/i })).toBeVisible()
  })

  // ── Send a message ─────────────────────────────────────────────────────────

  test('typing in composer and submitting adds message to the list', async ({ page }) => {
    await page.goto(`${BASE_URL}/clients/${CHART_ID}/build`)

    const composer = page.getByRole('textbox')
    await expect(composer).toBeVisible()

    const testMessage = 'E2E smoke — please ignore this message'
    await composer.fill(testMessage)

    // Submit via Enter (Composer submits on Enter without Shift)
    await composer.press('Enter')

    // The user bubble containing the sent text should appear in the message list
    await expect(page.getByText(testMessage)).toBeVisible({ timeout: 10_000 })
  })

  // ── Streaming response renders ─────────────────────────────────────────────

  test('streaming response renders after message send', async ({ page }) => {
    await page.goto(`${BASE_URL}/clients/${CHART_ID}/build`)

    const composer = page.getByRole('textbox')
    await composer.fill('E2E streaming check — one word reply please')
    await composer.press('Enter')

    // Either a pending-assistant bubble appears immediately while streaming,
    // or an assistant message bubble appears once streaming completes.
    // We look for the assistant turn — role="article" or the pending bubble class.
    const assistantTurn = page
      .locator('[data-role="assistant"], [data-message-role="assistant"]')
      .first()
      .or(page.locator('.pending-assistant, [class*="PendingAssistant"]').first())

    // Allow generous timeout for a real LLM call
    await expect(assistantTurn.or(page.getByText(/\.\.\./))).toBeVisible({ timeout: 30_000 })
  })

  // ── Command palette via Cmd+K ──────────────────────────────────────────────

  test('Cmd+K opens command palette with search input', async ({ page }) => {
    await page.goto(`${BASE_URL}/clients/${CHART_ID}/build`)

    // Ensure the page is focused before firing the hotkey
    await page.locator('body').click()
    await page.keyboard.press('Meta+k')

    // CommandPalette renders a Dialog with an input labelled "Search commands"
    const paletteInput = page.getByRole('textbox', { name: /Search commands/i })
    await expect(paletteInput).toBeVisible({ timeout: 3_000 })

    // Verify at least one command entry is visible (palette is populated)
    await expect(page.getByText('New build chat')).toBeVisible()
  })

  test('command palette closes on Escape', async ({ page }) => {
    await page.goto(`${BASE_URL}/clients/${CHART_ID}/build`)

    await page.locator('body').click()
    await page.keyboard.press('Meta+k')

    const paletteInput = page.getByRole('textbox', { name: /Search commands/i })
    await expect(paletteInput).toBeVisible({ timeout: 3_000 })

    await page.keyboard.press('Escape')
    await expect(paletteInput).not.toBeVisible({ timeout: 3_000 })
  })

  // ── Auth guard ─────────────────────────────────────────────────────────────

  test('unauthenticated request redirects away from build page', async ({ context }) => {
    // Open a fresh context without the session cookie
    const freshContext = await context.browser()!.newContext()
    const freshPage = await freshContext.newPage()

    await freshPage.goto(`${BASE_URL}/clients/${CHART_ID}/build`)

    // Should land on /login (or /dashboard), not on the build page
    await expect(freshPage).not.toHaveURL(/\/build/, { timeout: 5_000 })

    await freshContext.close()
  })
})
