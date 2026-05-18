/**
 * A.1 — Chat column sidebar offset (Round 5).
 *
 * Verifies that the chat column's left margin matches the sidebar state:
 *   collapsed → md:ml-10 (40px) — clears the collapsed strip
 *   expanded  → md:ml-56 (224px) — clears the expanded panel; no content clipped
 *
 * Refs: CHAT_V2_ROUND_5_PLAN_v1_0.md §6.A.1
 */
import { test, expect, type Page } from '@playwright/test'

const CLIENT_ID = process.env.MARSYS_TEST_CLIENT_ID ?? '362f9f17-95a5-490b-a5a7-027d3e0efda0'
const CONSUME_URL = `/clients/${CLIENT_ID}/consume`
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

// Sidebar state detection: expanded = v2-conversation-sidebar visible; collapsed = v2-sidebar-expand visible.
// Sidebar state may be persisted in localStorage, so we always detect and normalise before asserting.

async function ensureCollapsed(page: Page) {
  const full = page.getByTestId('v2-conversation-sidebar')
  if (await full.isVisible({ timeout: 2_000 }).catch(() => false)) {
    await page.getByTestId('v2-sidebar-collapse').click()
    await page.getByTestId('v2-sidebar-expand').waitFor({ state: 'visible', timeout: 5_000 })
  }
  await page.waitForTimeout(300) // allow transition-[margin-left] to settle
}

async function ensureExpanded(page: Page) {
  const expandBtn = page.getByTestId('v2-sidebar-expand')
  if (await expandBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
    await expandBtn.click()
    await page.getByTestId('v2-conversation-sidebar').waitFor({ state: 'visible', timeout: 5_000 })
  }
  await page.waitForTimeout(300)
}

test.describe('A.1 — chat column sidebar offset', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  // Navigate to a known fresh state before each test.
  // Using page.goto on repeated navigations to the same Next.js app-router URL can leave
  // a second v2-chat-shell in the DOM during the transition. Going to '/' first
  // clears the old render before navigating to the consume page.
  test.beforeEach(async ({ page }) => {
    await page.goto('/', { waitUntil: 'domcontentloaded' })
  })

  test('sidebar collapsed: chat column left edge clears collapsed strip', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('v2-chat-shell').first().waitFor({ state: 'visible', timeout: 15_000 })

    await ensureCollapsed(page)

    const chatColumn = page.getByTestId('v2-chat-column')
    const box = await chatColumn.boundingBox()
    expect(box).not.toBeNull()
    // md:ml-10 = 40px; tolerance for sub-pixel rounding
    expect(box!.x).toBeGreaterThanOrEqual(36)
    expect(box!.x).toBeLessThan(50)
  })

  test('sidebar expanded: chat column left edge clears full sidebar (no clipping)', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('v2-chat-shell').first().waitFor({ state: 'visible', timeout: 15_000 })

    await ensureExpanded(page)

    const chatColumn = page.getByTestId('v2-chat-column')
    const box = await chatColumn.boundingBox()
    expect(box).not.toBeNull()
    // md:ml-56 = 224px; chat content must start at or beyond sidebar right edge
    expect(box!.x).toBeGreaterThanOrEqual(220)
  })

  test('A.1 — visual: sidebar collapsed', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('v2-chat-shell').first().waitFor({ state: 'visible', timeout: 15_000 })

    await ensureCollapsed(page)

    await expect(page.getByTestId('v2-chat-shell').first()).toHaveScreenshot('a1-sidebar-collapsed.png')
  })

  test('A.1 — visual: sidebar expanded (content not clipped)', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('v2-chat-shell').first().waitFor({ state: 'visible', timeout: 15_000 })

    await ensureExpanded(page)

    await expect(page.getByTestId('v2-chat-shell').first()).toHaveScreenshot('a1-sidebar-expanded.png')
  })
})
