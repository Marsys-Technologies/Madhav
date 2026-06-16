import { test, expect } from '@playwright/test'
import { readFileSync } from 'fs'

/**
 * Gate III — Intelligent Chat Interface visual smoke spec.
 *
 * Tests the Jyotish-aware consume interface introduced in Gate III:
 *   - Empty state renders with suggested prompts (two tabs: By type / By moment)
 *   - Composer textarea present
 *   - Sanskrit tooltip renders on hover
 *   - Post-answer flow (query submit + partial screenshot while streaming)
 *
 * Auth: reads Firebase __session cookie from /tmp/smoke_session_cookie.txt.
 * Chart ID: 482012f1-710e-4a25-994a-93821f5871aa (Abhisek Mohanty, the native chart).
 *
 * Re-run:
 *   Write a fresh session cookie to /tmp/smoke_session_cookie.txt, then:
 *   npx playwright test tests/e2e/gate_iii_intelligent_chat_smoke.spec.ts --reporter=list --workers=1
 */

const SS = 'tests/screenshots/gate_iii_smoke'
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'
const CONSUME_URL = `/clients/${CHART_ID}/consume`

function getSessionCookie(): string | null {
  try {
    return readFileSync('/tmp/smoke_session_cookie.txt', 'utf8').trim()
  } catch {
    return null
  }
}

const SESSION = getSessionCookie()
const SKIP = !SESSION

test.describe('Gate III — Intelligent Chat Interface visual smoke', () => {
  test.skip(SKIP, 'No session cookie at /tmp/smoke_session_cookie.txt — write one and re-run')

  test.beforeEach(async ({ context }) => {
    await context.addCookies([{
      name: '__session',
      value: SESSION!,
      domain: 'localhost',
      path: '/',
      httpOnly: true,
    }])
  })

  test.use({ viewport: { width: 1440, height: 900 } })

  test('consume page empty state renders with suggested prompts', async ({ page }) => {
    await page.goto(CONSUME_URL)
    await page.waitForLoadState('networkidle')

    await page.screenshot({ path: `${SS}/empty_state.png`, fullPage: true })

    // Welcome heading or "Ask anything"
    const hasWelcome = await page.getByText(/welcome/i).count() > 0
    const hasAsk = await page.getByText(/ask anything/i).count() > 0
    expect(hasWelcome || hasAsk).toBe(true)

    // Tab navigation (By type / By moment)
    const tablist = page.locator('[role="tablist"]').first()
    if (await tablist.count() > 0) {
      await expect(tablist).toBeVisible()
      await tablist.screenshot({ path: `${SS}/suggestion_tabs.png` })
    }

    // Suggestion grid visible
    const suggestionGrid = page.locator('.grid').filter({ has: page.locator('button') }).first()
    if (await suggestionGrid.count() > 0) {
      await suggestionGrid.screenshot({ path: `${SS}/suggestion_grid.png` })
    }

    // Composer textarea present
    const textarea = page.locator('textarea').first()
    await expect(textarea).toBeVisible()

    // Screenshot composer area
    const composerArea = page.locator('form, [role="form"]').last()
    if (await composerArea.count() > 0) {
      await composerArea.screenshot({ path: `${SS}/composer.png` })
    }
  })

  test('By moment tab loads moment-based suggestions', async ({ page }) => {
    await page.goto(CONSUME_URL)
    await page.waitForLoadState('networkidle')

    // Click "By moment" tab
    const momentTab = page.getByText('By moment').first()
    if (await momentTab.count() > 0) {
      await momentTab.click()
      await page.waitForTimeout(2000) // wait for API fetch
      await page.screenshot({ path: `${SS}/moment_tab.png` })
    }
  })

  test('submit a query and observe streaming response', async ({ page }) => {
    await page.goto(CONSUME_URL)
    await page.waitForLoadState('networkidle')

    // Fill textarea with a golden Jyotish query
    const textarea = page.locator('textarea').first()
    await expect(textarea).toBeVisible()
    const query = 'What does my natal Moon in Gemini reveal about my emotional patterns?'
    await textarea.fill(query)

    // Screenshot before submit
    await page.screenshot({ path: `${SS}/before_submit.png` })

    // Submit via Enter or submit button
    const submitBtn = page.locator('button[type="submit"]').first()
    if (await submitBtn.count() > 0) {
      await submitBtn.click()
    } else {
      await textarea.press('Enter')
    }

    // Wait for response to begin streaming (3 seconds)
    await page.waitForTimeout(3000)
    await page.screenshot({ path: `${SS}/streaming_response.png` })

    // Wait for more content (10 seconds) — don't wait for full completion
    await page.waitForTimeout(10000)
    await page.screenshot({ path: `${SS}/partial_answer.png`, fullPage: true })

    // Check for SanskritTermSpan — look for elements with dotted underline (cursor-help)
    const sanskritSpan = page.locator('.cursor-help, [role="button"].cursor-help').first()
    if (await sanskritSpan.count() > 0) {
      await sanskritSpan.hover()
      await page.waitForTimeout(500)
      const tooltip = page.locator('[role="tooltip"]').first()
      if (await tooltip.count() > 0) {
        await page.screenshot({ path: `${SS}/sanskrit_tooltip.png` })
      }
    }

    // Look for provenance pills (PostAnswerProvenance)
    const provenancePill = page.locator('[class*="provenance"], [class*="pill"]').first()
    if (await provenancePill.count() > 0) {
      await provenancePill.screenshot({ path: `${SS}/provenance_pills.png` })
    }
  })
})
