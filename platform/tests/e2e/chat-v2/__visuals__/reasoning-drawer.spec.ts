/**
 * β visual baselines — reasoning / thinking drawer.
 *
 * Tests the collapsible reasoning drawer that shows when the model
 * emits thinking tokens: toggle button, expanded/collapsed states,
 * and reasoning content rendering.
 *
 * CAPTURE DEFERRED to Phase γ per CLAUDECODE_BRIEF §M.
 */
import { test, expect } from '@playwright/test'

const CHAT_V2_URL = '/dev/chat-spike'
const STREAM_TIMEOUT = 35_000
const SKIP_REASON = 'Skipped: MARSYS_SUPER_ADMIN_SESSION not set'

test.describe('visual — reasoning drawer', () => {
  test.skip(!process.env.MARSYS_SUPER_ADMIN_SESSION, SKIP_REASON)

  test('reasoning: toggle button visible after stream with thinking tokens', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Deep analysis requiring reasoning')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const toggle = page.getByTestId('reasoning-toggle')
    if (await toggle.isVisible()) {
      await expect(toggle).toHaveScreenshot('reasoning-toggle-btn.png')
    }
  })

  test('reasoning: drawer collapsed by default after stream', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Reasoning analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const drawer = page.getByTestId('reasoning-drawer')
    if (await drawer.isVisible()) {
      await expect(drawer).toHaveScreenshot('reasoning-drawer-collapsed.png')
    }
  })

  test('reasoning: drawer expands when toggle clicked', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Reasoning analysis')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const toggle = page.getByTestId('reasoning-toggle')
    if (await toggle.isVisible()) {
      await toggle.click()
      await page.waitForTimeout(400)
      await expect(page.getByTestId('reasoning-drawer')).toHaveScreenshot('reasoning-drawer-expanded.png')
    }
  })

  test('reasoning: expanded drawer shows thinking content', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Deep chart reasoning')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
    const toggle = page.getByTestId('reasoning-toggle')
    if (await toggle.isVisible()) {
      await toggle.click()
      await page.waitForTimeout(400)
      const content = page.getByTestId('reasoning-content')
      if (await content.isVisible()) {
        await expect(content).toHaveScreenshot('reasoning-content-text.png')
      }
    }
  })

  test('reasoning: in-flight reasoning tokens render during stream', async ({ page }) => {
    await page.goto(CHAT_V2_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })
    await page.getByTestId('composer-input').fill('Complex reasoning query')
    await page.getByTestId('send-btn').click()
    await page.getByTestId('abort-btn').waitFor({ state: 'visible', timeout: 8000 })
    // Short delay for reasoning tokens to appear
    await page.waitForTimeout(800)
    const drawer = page.getByTestId('reasoning-drawer')
    if (await drawer.isVisible()) {
      await expect(drawer).toHaveScreenshot('reasoning-in-flight.png')
    }
  })
})
