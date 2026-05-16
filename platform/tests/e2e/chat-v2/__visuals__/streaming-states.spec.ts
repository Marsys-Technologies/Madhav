/**
 * β visual baselines — streaming in-progress states.
 *
 * Captures mid-stream UI: streaming dots, abort button, partial markdown,
 * scroll anchor, and stage progress strip.
 *
 * CAPTURE DEFERRED to Phase γ per CLAUDECODE_BRIEF §M.
 */
import { test, expect } from '@playwright/test'

const CHAT_V2_URL = '/dev/chat-spike'
const STREAM_TIMEOUT = 35_000
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

test.describe('visual — streaming in-progress', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('streaming: abort button visible during active stream', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Analyze my natal chart')
    await page.getByTestId('send-btn').click()
    // Wait for stream to begin
    await page.getByTestId('abort-btn').waitFor({ state: 'visible', timeout: 8000 })
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('streaming-abort-btn-visible.png')
  })

  test('streaming: user message renders immediately before response', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Rahu 7th house')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('user-message').waitFor({ state: 'visible', timeout: 5000 })
    // Snapshot immediately after user message appears (before assistant response)
    await expect(page.getByTestId('user-message')).toHaveScreenshot('streaming-user-message-bubble.png')
  })

  test('streaming: partial assistant message renders markdown tokens', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Rahu analysis')
    await page.getByTestId('send-btn').click()
    // Wait for assistant message to appear
    await page.getByTestId('assistant-message').waitFor({ state: 'visible', timeout: 10000 })
    await page.waitForTimeout(500)
    await expect(page.getByTestId('assistant-message')).toHaveScreenshot('streaming-partial-assistant-message.png')
  })

  test('streaming: composer is disabled during active stream', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Rahu analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('abort-btn').waitFor({ state: 'visible', timeout: 8000 })
    const input = page.getByTestId('composer-input')
    await expect(input).toHaveScreenshot('streaming-composer-disabled.png')
  })

  test('streaming: complete — action bar appears after stream', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Rahu 7th house')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('streaming-complete-with-actions.png')
  })

  test('streaming: complete — message text region snapshot', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Rahu 7th house')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    await expect(page.getByTestId('message-text')).toHaveScreenshot('streaming-complete-message-text.png')
  })
})
