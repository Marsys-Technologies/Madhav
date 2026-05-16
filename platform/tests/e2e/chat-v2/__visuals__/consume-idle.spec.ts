/**
 * β visual baselines — ConsumeChatV2 idle / empty states.
 *
 * Capture gate: MARSYS_UPDATE_VISUALS must be set for toHaveScreenshot to write
 * snapshots. In CI the flag is absent, so these tests run in comparison mode
 * (they pass when no snapshot exists yet — first run always green).
 *
 * CAPTURE DEFERRED to Phase γ per CLAUDECODE_BRIEF §M.
 * AUTHORING (this file) is the β gate requirement.
 */
import { test, expect } from '@playwright/test'

const CHAT_V2_URL = '/dev/chat-spike'
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

test.describe('visual — ConsumeChatV2 idle states', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('idle: empty thread shows empty state placeholder', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('thread-empty').waitFor({ state: 'visible' })
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('idle-empty-thread.png')
  })

  test('idle: composer input focused shows focus ring', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').focus()
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('idle-composer-focused.png')
  })

  test('idle: composer with text shows send button enabled', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Rahu in the 7th house — full analysis')
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('idle-composer-with-text.png')
  })

  test('idle: page title and header render correctly', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('idle-header-region.png')
  })

  test('idle: mobile 375px viewport empty state', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('idle-mobile-375-empty.png')
  })

  test('idle: tablet 768px viewport empty state', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await expect(page.getByTestId('chat-spike-root')).toHaveScreenshot('idle-tablet-768-empty.png')
  })
})
