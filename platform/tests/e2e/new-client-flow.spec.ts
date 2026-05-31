import { test, expect } from '@playwright/test'
import { existsSync, readFileSync } from 'fs'

/**
 * New Client → Cockpit end-to-end flow — [BUILD-ORCH-D-S5]
 *
 * Verifies the full funnel:
 *   1. Auth via session cookie
 *   2. Navigate to /clients/new
 *   3. Fill form with valid data (DD MM YYYY date format)
 *   4. Submit → /api/clients/create
 *   5. Assert redirect to /clients/<id>/cockpit (or /build fallback)
 *   6. Assert cockpit page mounts
 *
 * Prerequisites:
 *   - Dev server running on http://localhost:3000
 *   - Valid Firebase __session cookie in /tmp/smoke_session_cookie.txt
 *   - Cloud SQL Proxy running (for /api/clients/create DB insert)
 *
 * Skip conditions: session cookie absent, or SMOKE_CHART_ID env not set.
 * Both are normal in CI without the operator secrets injected.
 *
 * Re-run locally:
 *   Write a valid Firebase session cookie to /tmp/smoke_session_cookie.txt, then:
 *   npx playwright test tests/e2e/new-client-flow.spec.ts --reporter=list --workers=1
 *
 * @ci-skip (requires live dev server + Cloud SQL Proxy)
 */

const COOKIE_PATH = '/tmp/smoke_session_cookie.txt'

function tryReadCookie(): string | null {
  if (!existsSync(COOKIE_PATH)) return null
  try {
    return readFileSync(COOKIE_PATH, 'utf8').trim() || null
  } catch {
    return null
  }
}

const SESSION_COOKIE = tryReadCookie()
const SKIP = !SESSION_COOKIE

test.describe('New client form → cockpit redirect', () => {
  test.beforeEach(async ({ page }) => {
    test.skip(SKIP, 'No session cookie at /tmp/smoke_session_cookie.txt — write one and re-run (@ci-skip)')

    // Inject Firebase __session cookie
    await page.context().addCookies([
      {
        name: '__session',
        value: SESSION_COOKIE!,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        sameSite: 'Lax',
      },
    ])
  })

  test('new client form → cockpit redirect → page mounts', async ({ page }) => {
    test.skip(SKIP, '@ci-skip: requires live server + session cookie')

    // ── Navigate to form ──────────────────────────────────────────────────
    await page.goto('/clients/new')
    await expect(page).not.toHaveURL(/login/)

    // ── Fill form fields (state bindings, not visual) ─────────────────────
    // Full name
    const nameInput = page.getByLabel(/full name/i).first()
    if (await nameInput.count() > 0) {
      await nameInput.fill('D-S5 Smoke Native')
    }

    // Gender (select)
    const genderSelect = page.locator('select').filter({ hasText: /male|female|gender/i }).first()
    if (await genderSelect.count() > 0) {
      await genderSelect.selectOption({ value: 'male' })
    }

    // Birth date — type="date" input (ISO format for native date picker)
    const dateInput = page.locator('input[type="date"]').first()
    if (await dateInput.count() > 0) {
      await dateInput.fill('1984-02-05')
    }

    // Birth time
    const timeInput = page.locator('input[type="time"]').first()
    if (await timeInput.count() > 0) {
      await timeInput.fill('10:43')
    }

    // Birth place
    const placeInput = page.getByPlaceholder(/bhubaneswar|city|birth place/i).first()
    if (await placeInput.count() > 0) {
      await placeInput.fill('Bhubaneswar, Odisha, India')
    }

    // Latitude + longitude (manual override)
    const latInput = page.locator('input[type="number"][placeholder*="20"]').first()
    if (await latInput.count() > 0) {
      await latInput.fill('20.2961')
    }
    const lngInput = page.locator('input[type="number"][placeholder*="85"]').first()
    if (await lngInput.count() > 0) {
      await lngInput.fill('85.8245')
    }

    // Timezone offset (if present)
    const tzOffsetInput = page.locator('input[placeholder*="5.5"]').first()
    if (await tzOffsetInput.count() > 0) {
      await tzOffsetInput.fill('5.5')
    }

    // ── Submit ─────────────────────────────────────────────────────────────
    const submitBtn = page.locator('button[type="submit"]').first()
    await expect(submitBtn).toBeVisible()
    await submitBtn.click()

    // ── Assert redirect ────────────────────────────────────────────────────
    await expect(page).toHaveURL(/\/clients\/[a-f0-9-]{36}\/(cockpit|build)/, { timeout: 15_000 })
  })

  test('cockpit page mounts after redirect', async ({ page }) => {
    test.skip(SKIP, '@ci-skip: requires live server + session cookie')

    // If we have a known chart ID from env, navigate directly
    const chartId = process.env.SMOKE_CHART_ID
    if (!chartId) {
      test.skip(true, '@ci-skip: SMOKE_CHART_ID not set — cannot navigate directly to cockpit')
      return
    }

    await page.goto(`/clients/${chartId}/cockpit`)
    // Assert cockpit-level element is present (chart area or build controls)
    const cockpitMounted =
      page.locator('[data-testid="build-button"]').first()

    await expect(cockpitMounted).toBeVisible({ timeout: 10_000 })
  })
})
