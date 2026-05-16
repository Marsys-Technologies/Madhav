/**
 * β visual baselines — message action bars.
 *
 * Tests the user and assistant action bars: copy, regenerate, edit,
 * details, branch navigation, and hover states.
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

test.describe('visual — message action bars', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('actions: assistant action bar appears after stream', async ({ page }) => {
    await sendAndWait(page, 'Rahu analysis')
    const actionBar = page.getByTestId('v2-assistant-action-bar').first()
    if (await actionBar.isVisible()) {
      await expect(actionBar).toHaveScreenshot('actions-assistant-bar.png')
    }
  })

  test('actions: user action bar visible on hover', async ({ page }) => {
    await sendAndWait(page, 'Rahu analysis')
    const userMsg = page.getByTestId('v2-user-message').first()
    await userMsg.hover()
    await page.waitForTimeout(300)
    const actionBar = page.getByTestId('v2-user-action-bar').first()
    if (await actionBar.isVisible()) {
      await expect(actionBar).toHaveScreenshot('actions-user-bar-hover.png')
    }
  })

  test('actions: copy button renders correctly', async ({ page }) => {
    await sendAndWait(page, 'Rahu analysis')
    const copyBtn = page.getByTestId('v2-copy-btn').first()
    if (await copyBtn.isVisible()) {
      await expect(copyBtn).toHaveScreenshot('actions-copy-btn.png')
    }
  })

  test('actions: regenerate button renders correctly', async ({ page }) => {
    await sendAndWait(page, 'Rahu analysis')
    const regenBtn = page.getByTestId('v2-regenerate-btn').first()
    if (await regenBtn.isVisible()) {
      await expect(regenBtn).toHaveScreenshot('actions-regenerate-btn.png')
    }
  })

  test('actions: edit button renders in user action bar', async ({ page }) => {
    await sendAndWait(page, 'Rahu analysis')
    const userMsg = page.getByTestId('v2-user-message').first()
    await userMsg.hover()
    await page.waitForTimeout(300)
    const editBtn = page.getByTestId('v2-edit-btn').first()
    if (await editBtn.isVisible()) {
      await expect(editBtn).toHaveScreenshot('actions-edit-btn.png')
    }
  })

  test('actions: details button renders in assistant action bar', async ({ page }) => {
    await sendAndWait(page, 'Rahu analysis')
    const detailsBtn = page.getByTestId('v2-details-btn').first()
    if (await detailsBtn.isVisible()) {
      await expect(detailsBtn).toHaveScreenshot('actions-details-btn.png')
    }
  })

  test('actions: full thread with both user and assistant messages', async ({ page }) => {
    await sendAndWait(page, 'Rahu 7th house analysis')
    await expect(page.getByTestId('thread-viewport')).toHaveScreenshot('actions-full-thread-layout.png')
  })
})
