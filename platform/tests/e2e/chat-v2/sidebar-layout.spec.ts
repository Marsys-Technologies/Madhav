/**
 * B.1 — Sidebar overlay layout verification.
 *
 * Verifies that ConversationSidebar renders as a fixed overlay (not in-flow)
 * so it never steals width from the chat column.
 */
import { test, expect } from '@playwright/test'

const CLIENT_ID = process.env.MARSYS_TEST_CLIENT_ID ?? '362f9f17-95a5-490b-a5a7-027d3e0efda0'
const CONSUME_URL = `/clients/${CLIENT_ID}/consume`
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

test.describe('B.1 — sidebar does not steal chat column width', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('sidebar open: chat column fills full viewport width', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('consume-chat-v2-root').waitFor({ state: 'visible', timeout: 15_000 })

    // Open sidebar
    const openBtn = page.getByTestId('v2-mobile-sidebar-open').first()
    if (await openBtn.isVisible()) await openBtn.click()

    // Sidebar should be visible as overlay
    await page.getByTestId('v2-conversation-sidebar').waitFor({ state: 'visible', timeout: 5_000 })

    // Chat column (flex-1 sibling) should still fill near-full viewport width
    const chatColumn = page.locator('[data-testid="consume-chat-v2-root"] > div.flex-1').first()
    const box = await chatColumn.boundingBox()
    expect(box).not.toBeNull()
    // Chat column should be close to full viewport width (sidebar is overlay, not in-flow)
    expect(box!.width).toBeGreaterThan(1200) // >1200px of 1280px = sidebar not stealing width
  })

  test('sidebar collapsed: chat column fills full viewport width', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('consume-chat-v2-root').waitFor({ state: 'visible', timeout: 15_000 })

    // Ensure sidebar is collapsed (default state)
    const collapseBtn = page.getByTestId('v2-sidebar-collapse').first()
    if (await collapseBtn.isVisible()) await collapseBtn.click()

    // Chat column should fill near-full viewport width
    const chatColumn = page.locator('[data-testid="consume-chat-v2-root"] > div.flex-1').first()
    const box = await chatColumn.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.width).toBeGreaterThan(1200)
  })
})

test.describe('B.1 — visual: sidebar open vs closed', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('sidebar closed state — desktop baseline', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('consume-chat-v2-root').waitFor({ state: 'visible', timeout: 15_000 })
    await expect(page.getByTestId('consume-chat-v2-root')).toHaveScreenshot('b1-sidebar-closed-desktop.png')
  })

  test('sidebar open state — desktop baseline', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('consume-chat-v2-root').waitFor({ state: 'visible', timeout: 15_000 })

    const openBtn = page.getByTestId('v2-mobile-sidebar-open').first()
    if (await openBtn.isVisible()) await openBtn.click()
    await page.getByTestId('v2-conversation-sidebar').waitFor({ state: 'visible', timeout: 5_000 })

    await expect(page.getByTestId('consume-chat-v2-root')).toHaveScreenshot('b1-sidebar-open-desktop.png')
  })
})
