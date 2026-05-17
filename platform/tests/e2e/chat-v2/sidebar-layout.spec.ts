/**
 * B.1 — Sidebar layout verification.
 *
 * After A.1 (Round 5), the chat column carries md:ml-{10|56} to match the
 * sidebar's collapsed/expanded width. The sidebar is still a fixed overlay
 * (never in-flow), but chat content is now offset so it is not occluded.
 *
 * Collapsed: md:ml-10 → chat column left edge ≈ 40px, width ≈ 1240px
 * Expanded:  md:ml-56 → chat column left edge ≈ 224px, width ≈ 1056px
 */
import { test, expect, type Page } from '@playwright/test'

const CLIENT_ID = process.env.MARSYS_TEST_CLIENT_ID ?? '362f9f17-95a5-490b-a5a7-027d3e0efda0'
const CONSUME_URL = `/clients/${CLIENT_ID}/consume`
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

async function ensureCollapsed(page: Page) {
  const full = page.getByTestId('v2-conversation-sidebar')
  if (await full.isVisible({ timeout: 2_000 }).catch(() => false)) {
    await page.getByTestId('v2-sidebar-collapse').click()
    await page.getByTestId('v2-sidebar-expand').waitFor({ state: 'visible', timeout: 5_000 })
  }
  await page.waitForTimeout(300)
}

async function ensureExpanded(page: Page) {
  const expandBtn = page.getByTestId('v2-sidebar-expand')
  if (await expandBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
    await expandBtn.click()
    await page.getByTestId('v2-conversation-sidebar').waitFor({ state: 'visible', timeout: 5_000 })
  }
  await page.waitForTimeout(300)
}

test.describe('B.1 — sidebar does not occlude chat column content', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('sidebar open: chat column is offset right so content is not clipped', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('consume-chat-v2-root').waitFor({ state: 'visible', timeout: 15_000 })

    await ensureExpanded(page)

    // A.1: chat column left edge must be ≥ sidebar width (224px) so no content is occluded
    const chatColumn = page.getByTestId('v2-chat-column')
    const box = await chatColumn.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.x).toBeGreaterThanOrEqual(220) // md:ml-56 = 224px; tolerance for sub-pixel
  })

  test('sidebar collapsed: chat column offset matches collapsed strip width', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('consume-chat-v2-root').waitFor({ state: 'visible', timeout: 15_000 })

    await ensureCollapsed(page)

    // A.1: chat column left edge ≈ 40px (md:ml-10) — clears the collapsed strip
    const chatColumn = page.getByTestId('v2-chat-column')
    const box = await chatColumn.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.x).toBeGreaterThanOrEqual(36) // md:ml-10 = 40px; tolerance for sub-pixel
    expect(box!.width).toBeGreaterThan(1200) // still fills most of viewport when collapsed
  })
})

test.describe('B.1 — visual: sidebar open vs closed', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('sidebar closed state — desktop baseline', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('consume-chat-v2-root').waitFor({ state: 'visible', timeout: 15_000 })
    await ensureCollapsed(page)
    await expect(page.getByTestId('consume-chat-v2-root')).toHaveScreenshot('b1-sidebar-closed-desktop.png')
  })

  test('sidebar open state — desktop baseline', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 })
    await page.goto(CONSUME_URL, { waitUntil: 'domcontentloaded' })
    await page.getByTestId('consume-chat-v2-root').waitFor({ state: 'visible', timeout: 15_000 })
    await ensureExpanded(page)
    await expect(page.getByTestId('consume-chat-v2-root')).toHaveScreenshot('b1-sidebar-open-desktop.png')
  })
})
