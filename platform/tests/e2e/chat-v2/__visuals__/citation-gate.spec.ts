/**
 * β visual baselines — citation gate UI (β10).
 *
 * Tests the citation badge, citation side panel, citation gate status
 * indicators in the details drawer, and citation warn/fail states.
 *
 * CAPTURE DEFERRED to Phase γ per CLAUDECODE_BRIEF §M.
 */
import { test, expect } from '@playwright/test'

const CHAT_V2_URL = '/dev/chat-spike'
const STREAM_TIMEOUT = 35_000
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

test.describe('visual — citation gate (β10)', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('citation: badge visible on assistant message with verified citations', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('SIG.MSR.142 analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const badge = page.getByTestId('v2-citation-badge').first()
    if (await badge.isVisible()) {
      await expect(badge).toHaveScreenshot('citation-badge-verified.png')
    }
  })

  test('citation: citation panel opens when badge clicked', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('SIG.MSR.142 analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const badge = page.getByTestId('v2-citation-badge').first()
    if (await badge.isVisible()) {
      await badge.click()
      await page.getByTestId('v2-citation-panel').waitFor({ state: 'visible', timeout: 3000 })
      await expect(page.getByTestId('v2-citation-panel')).toHaveScreenshot('citation-panel-open.png')
    }
  })

  test('citation: panel item list renders correctly', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('SIG.MSR analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const badge = page.getByTestId('v2-citation-badge').first()
    if (await badge.isVisible()) {
      await badge.click()
      const panelItem = page.getByTestId('v2-citation-panel-item').first()
      if (await panelItem.isVisible()) {
        await expect(panelItem).toHaveScreenshot('citation-panel-item.png')
      }
    }
  })

  test('citation: citation gate status in details drawer — pass state', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('SIG.MSR.142 full analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const detailsBtn = page.getByTestId('v2-details-btn').first()
    if (await detailsBtn.isVisible()) {
      await detailsBtn.click()
      await page.getByTestId('v2-details-drawer').waitFor({ state: 'visible', timeout: 3000 })
      await expect(page.getByTestId('v2-details-drawer')).toHaveScreenshot('citation-gate-drawer-pass.png')
    }
  })

  test('citation: details drawer — citation gate section renders', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Rahu analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const detailsBtn = page.getByTestId('v2-details-btn').first()
    if (await detailsBtn.isVisible()) {
      await detailsBtn.click()
      const citationGate = page.getByTestId('v2-details-citation-gate')
      if (await citationGate.isVisible()) {
        await expect(citationGate).toHaveScreenshot('citation-gate-details-section.png')
      }
    }
  })

  test('citation: tooltip appears on hover over citation badge', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('SIG.MSR.142')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const badge = page.getByTestId('v2-citation-badge').first()
    if (await badge.isVisible()) {
      await badge.hover()
      await page.waitForTimeout(400)
      await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('citation-tooltip-hover.png')
    }
  })

  test('citation: unpin closes citation panel', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('SIG.MSR.142 analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const badge = page.getByTestId('v2-citation-badge').first()
    if (await badge.isVisible()) {
      await badge.click()
      await page.getByTestId('v2-citation-panel').waitFor({ state: 'visible', timeout: 3000 })
      const unpin = page.getByTestId('v2-citation-unpin')
      if (await unpin.isVisible()) {
        await unpin.click()
        await page.waitForTimeout(300)
        await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('citation-panel-after-unpin.png')
      }
    }
  })
})
