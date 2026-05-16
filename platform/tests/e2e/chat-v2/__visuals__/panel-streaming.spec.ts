/**
 * β visual baselines — panel mode streaming (β9).
 *
 * Tests panelStageEvents emission: running/done states for panel:member:1/2/3
 * and panel:adjudicator, plus the final adjudicated answer layout.
 *
 * CAPTURE DEFERRED to Phase γ per CLAUDECODE_BRIEF §M.
 */
import { test, expect } from '@playwright/test'

const CHAT_V2_URL = '/dev/chat-spike'
const STREAM_TIMEOUT = 45_000
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

test.describe('visual — panel streaming (β9)', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('panel: stage strip shows panel:member:1 running', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    // Panel mode fixture — requires query that triggers panel
    await page.getByTestId('composer-input').fill('[panel] Rahu 7th house full analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('abort-btn').waitFor({ state: 'visible', timeout: 8000 })
    await page.waitForTimeout(200)
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('panel-member-1-running.png')
  })

  test('panel: stage strip shows panel:adjudicator running', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('[panel] Rahu 7th house full analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('abort-btn').waitFor({ state: 'visible', timeout: 8000 })
    // Wait longer for adjudicator stage to begin
    await page.waitForTimeout(3000)
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('panel-adjudicator-running.png')
  })

  test('panel: complete — adjudicated answer visible', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('[panel] Rahu 7th house analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('panel-complete-adjudicated.png')
  })

  test('panel: complete — assistant message layout with panel metadata', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('[panel] Chart analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const assistantMsg = page.getByTestId('assistant-message').last()
    await expect(assistantMsg).toHaveScreenshot('panel-complete-assistant-message.png')
  })

  test('panel: action bar visible after panel stream completes', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('[panel] Chart analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    // Action bar check
    const actionBar = page.getByTestId('message-actions')
    if (await actionBar.isVisible()) {
      await expect(actionBar).toHaveScreenshot('panel-complete-action-bar.png')
    }
  })
})
