/**
 * α0 spike E2E: verifies assistant-ui renders correctly against /api/chat/spike.
 *
 * Requires:
 *   - Next.js dev server running at http://localhost:3000
 *   - Auth session with super_admin role (set via storageState or cookie)
 *
 * In CI these run only if a super_admin session fixture is available.
 * The spike test is intentionally lenient — it does not assert pixel perfection,
 * only that the structural elements arrive and streaming completes without error.
 *
 * data-testid inventory (from ChatSpikeThread.tsx):
 *   chat-spike-root, thread-root, thread-viewport, thread-empty,
 *   reasoning-drawer, reasoning-toggle, reasoning-content,
 *   user-message, assistant-message, message-text,
 *   composer-input, send-btn, abort-btn, scroll-to-bottom, message-actions
 */

import { test, expect } from '@playwright/test'

const SPIKE_URL = '/dev/chat-spike'
const TEST_PROMPT = 'What does Rahu in the 7th house mean?'

// Timeout generous enough for the fixture to stream (~300 reasoning chunks + ~1500 text chunks at 4–8ms each ≈ 8s max)
const STREAM_TIMEOUT = 30_000

test.describe('α0 spike — assistant-ui fit verification', () => {
  test.skip(
    !process.env.MARSYS_SUPER_ADMIN_SESSION,
    'Skipped: MARSYS_SUPER_ADMIN_SESSION not set — requires auth session fixture',
  )

  test('page mounts and shows empty state', async ({ page }) => {
    await page.goto(SPIKE_URL)
    await expect(page.getByTestId('chat-spike-root')).toBeVisible()
    await expect(page.getByTestId('thread-empty')).toBeVisible()
    await expect(page.getByTestId('composer-input')).toBeVisible()
    await expect(page.getByTestId('send-btn')).toBeVisible()
  })

  test('sends message and streams fixture response', async ({ page }) => {
    await page.goto(SPIKE_URL)

    const input = page.getByTestId('composer-input')
    await input.fill(TEST_PROMPT)

    // Send
    await page.getByTestId('send-btn').click()

    // User message renders immediately
    await expect(page.getByTestId('user-message').first()).toBeVisible()

    // Abort button appears while streaming
    await expect(page.getByTestId('abort-btn')).toBeVisible({ timeout: 3000 })

    // Wait for streaming to complete — abort button disappears and send button returns
    await expect(page.getByTestId('send-btn')).toBeVisible({ timeout: STREAM_TIMEOUT })

    // Assistant message text is present
    await expect(page.getByTestId('message-text').first()).toBeVisible()

    // Reasoning drawer is rendered
    await expect(page.getByTestId('reasoning-drawer')).toBeVisible()
  })

  test('reasoning drawer expands and collapses', async ({ page }) => {
    await page.goto(SPIKE_URL)

    const input = page.getByTestId('composer-input')
    await input.fill(TEST_PROMPT)
    await page.getByTestId('send-btn').click()

    // Wait for stream to complete
    await expect(page.getByTestId('send-btn')).toBeVisible({ timeout: STREAM_TIMEOUT })

    const drawer = page.getByTestId('reasoning-drawer')
    const toggle = page.getByTestId('reasoning-toggle')
    const content = page.getByTestId('reasoning-content')

    // Initially collapsed — content not visible
    await expect(toggle).toBeVisible()
    await expect(content).not.toBeVisible()

    // Expand
    await toggle.click()
    await expect(content).toBeVisible()
    await expect(toggle).toHaveAttribute('aria-expanded', 'true')

    // Collapse
    await toggle.click()
    await expect(content).not.toBeVisible()
    await expect(toggle).toHaveAttribute('aria-expanded', 'false')
  })

  test('scroll anchoring — viewport stays near bottom during streaming', async ({ page }) => {
    await page.goto(SPIKE_URL)

    const input = page.getByTestId('composer-input')
    await input.fill(TEST_PROMPT)
    await page.getByTestId('send-btn').click()

    // Poll scroll position mid-stream (before abort-btn disappears)
    await expect(page.getByTestId('abort-btn')).toBeVisible({ timeout: 3000 })

    const scrollData = await page.evaluate(() => {
      const viewport = document.querySelector('[data-testid="thread-viewport"]')
      if (!viewport) return null
      return {
        scrollTop: viewport.scrollTop,
        scrollHeight: viewport.scrollHeight,
        clientHeight: viewport.clientHeight,
      }
    })

    if (scrollData && scrollData.scrollHeight > scrollData.clientHeight) {
      // Allow up to 200px from bottom during streaming (scroll anchor may lag slightly)
      const distanceFromBottom =
        scrollData.scrollHeight - scrollData.scrollTop - scrollData.clientHeight
      expect(distanceFromBottom).toBeLessThan(200)
    }

    // Wait for completion
    await expect(page.getByTestId('send-btn')).toBeVisible({ timeout: STREAM_TIMEOUT })
  })

  test('message actions appear on hover', async ({ page }) => {
    await page.goto(SPIKE_URL)

    const input = page.getByTestId('composer-input')
    await input.fill(TEST_PROMPT)
    await page.getByTestId('send-btn').click()

    await expect(page.getByTestId('send-btn')).toBeVisible({ timeout: STREAM_TIMEOUT })

    const assistantMsg = page.getByTestId('assistant-message').first()
    await assistantMsg.hover()
    await expect(page.getByTestId('message-actions').first()).toBeVisible()
    await expect(page.getByTestId('copy-btn').first()).toBeVisible()
    await expect(page.getByTestId('regenerate-btn').first()).toBeVisible()
  })
})

/**
 * Structural smoke — these run without auth (page renders 302 redirect to /login in real app,
 * but we verify the route exists and returns a response, not a 404).
 */
test.describe('α0 spike — structural smoke (no auth required)', () => {
  test('spike API route responds to POST', async ({ request }) => {
    const response = await request.post('/api/chat/spike', {
      data: { messages: [{ role: 'user', content: 'test' }] },
    })
    // 200 (fixture streams) or 401/302 (auth redirect) are both acceptable —
    // what we must NOT get is 404 (route missing) or 500 (unhandled crash)
    expect([200, 401, 302, 307, 308]).toContain(response.status())
  })
})
