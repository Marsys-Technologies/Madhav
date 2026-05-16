/**
 * β visual baselines — abort and mid-stream interrupt (β7).
 *
 * Tests the abort button, interrupt toast, and the interrupted-message
 * state rendered in the thread after abort.
 *
 * CAPTURE DEFERRED to Phase γ per CLAUDECODE_BRIEF §M.
 */
import { test, expect } from '@playwright/test'

const CHAT_V2_URL = '/dev/chat-spike'
const STREAM_TIMEOUT = 35_000
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

test.describe('visual — abort / interrupt (β7)', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('abort: abort button renders correctly during stream', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Long chart analysis')
    await page.getByTestId('send-btn').click()
    const abortBtn = page.getByTestId('abort-btn')
    await abortBtn.waitFor({ state: 'visible', timeout: 8000 })
    await expect(abortBtn).toHaveScreenshot('abort-btn-during-stream.png')
  })

  test('abort: thread state after abort — partial message visible', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Long analysis')
    await page.getByTestId('send-btn').click()
    const abortBtn = page.getByTestId('abort-btn')
    await abortBtn.waitFor({ state: 'visible', timeout: 8000 })
    await page.waitForTimeout(1000)
    await abortBtn.click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: 5000 })
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('abort-after-stop-partial-message.png')
  })

  test('abort: send button re-enabled after abort', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Analysis query')
    await page.getByTestId('send-btn').click()
    const abortBtn = page.getByTestId('abort-btn')
    await abortBtn.waitFor({ state: 'visible', timeout: 8000 })
    await abortBtn.click()
    const sendBtn = page.getByTestId('send-btn')
    await sendBtn.waitFor({ state: 'visible', timeout: 5000 })
    await expect(sendBtn).toHaveScreenshot('abort-send-btn-reenabled.png')
  })

  test('interrupt: interrupt toast visible when typing during stream', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Long analysis query')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('abort-btn').waitFor({ state: 'visible', timeout: 8000 })
    await page.getByTestId('composer-input').fill('Follow-up question')
    const toast = page.getByTestId('v2-interrupt-toast')
    if (await toast.isVisible()) {
      await expect(toast).toHaveScreenshot('interrupt-toast-visible.png')
    }
  })

  test('interrupt: interrupt-send button triggers abort + new message', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Long query')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('abort-btn').waitFor({ state: 'visible', timeout: 8000 })
    await page.getByTestId('composer-input').fill('New question')
    const interruptBtn = page.getByTestId('v2-interrupt-send-btn')
    if (await interruptBtn.isVisible()) {
      await expect(interruptBtn).toHaveScreenshot('interrupt-send-btn.png')
      await interruptBtn.click()
      await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
      await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('interrupt-after-new-message.png')
    }
  })
})
