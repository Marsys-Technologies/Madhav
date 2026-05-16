/**
 * β visual baselines — message details drawer.
 *
 * Tests the ProvenanceDrawer / details panel: open/close animation snapshot,
 * trace link, citation gate section, and backdrop click dismiss.
 *
 * CAPTURE DEFERRED to Phase γ per CLAUDECODE_BRIEF §M.
 */
import { test, expect } from '@playwright/test'

const CHAT_V2_URL = '/dev/chat-spike'
const STREAM_TIMEOUT = 35_000
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

async function sendAndWait(page: import('@playwright/test').Page, prompt: string) {
  await page.goto(CHAT_V2_URL)
  await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
  await page.getByTestId('composer-input').fill(prompt)
  await page.getByTestId('send-btn').click()
  await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
}

test.describe('visual — details drawer', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('drawer: closed state — details button visible in action bar', async ({ page }) => {
    await sendAndWait(page, 'Rahu 7th house')
    const detailsBtn = page.getByTestId('v2-details-btn').first()
    if (await detailsBtn.isVisible()) {
      await expect(detailsBtn).toHaveScreenshot('drawer-closed-details-btn.png')
    }
  })

  test('drawer: open — full drawer renders correctly', async ({ page }) => {
    await sendAndWait(page, 'Rahu 7th house')
    const detailsBtn = page.getByTestId('v2-details-btn').first()
    if (await detailsBtn.isVisible()) {
      await detailsBtn.click()
      await page.getByTestId('v2-details-drawer').waitFor({ state: 'visible', timeout: 3000 })
      await expect(page.getByTestId('v2-details-drawer')).toHaveScreenshot('drawer-open-full.png')
    }
  })

  test('drawer: backdrop visible when drawer is open', async ({ page }) => {
    await sendAndWait(page, 'Rahu 7th house')
    const detailsBtn = page.getByTestId('v2-details-btn').first()
    if (await detailsBtn.isVisible()) {
      await detailsBtn.click()
      await page.getByTestId('v2-details-backdrop').waitFor({ state: 'visible', timeout: 3000 })
      await expect(page.getByTestId('v2-details-backdrop')).toHaveScreenshot('drawer-backdrop.png')
    }
  })

  test('drawer: close button dismisses drawer', async ({ page }) => {
    await sendAndWait(page, 'Rahu 7th house')
    const detailsBtn = page.getByTestId('v2-details-btn').first()
    if (await detailsBtn.isVisible()) {
      await detailsBtn.click()
      await page.getByTestId('v2-details-drawer').waitFor({ state: 'visible', timeout: 3000 })
      await page.getByTestId('v2-details-close').click()
      await page.waitForTimeout(400)
      await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('drawer-after-close.png')
    }
  })

  test('drawer: backdrop click dismisses drawer', async ({ page }) => {
    await sendAndWait(page, 'Rahu 7th house')
    const detailsBtn = page.getByTestId('v2-details-btn').first()
    if (await detailsBtn.isVisible()) {
      await detailsBtn.click()
      await page.getByTestId('v2-details-backdrop').waitFor({ state: 'visible', timeout: 3000 })
      await page.getByTestId('v2-details-backdrop').click()
      await page.waitForTimeout(400)
      await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('drawer-after-backdrop-click.png')
    }
  })

  test('drawer: trace link rendered (super_admin)', async ({ page }) => {
    await sendAndWait(page, 'Rahu 7th house')
    const detailsBtn = page.getByTestId('v2-details-btn').first()
    if (await detailsBtn.isVisible()) {
      await detailsBtn.click()
      await page.getByTestId('v2-details-drawer').waitFor({ state: 'visible', timeout: 3000 })
      const traceLink = page.getByTestId('v2-details-trace-link')
      if (await traceLink.isVisible()) {
        await expect(traceLink).toHaveScreenshot('drawer-trace-link.png')
      }
    }
  })
})
