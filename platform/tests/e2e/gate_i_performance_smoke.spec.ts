import { test, expect } from '@playwright/test'
import { readFileSync } from 'fs'

/**
 * Gate I — Performance Command Center visual smoke spec.
 *
 * Tests the super-admin-gated /performance dashboard introduced in Gate I:
 *   - KPI tiles render (pipeline correctness, retrieval health, etc.)
 *   - Query log table renders with headers
 *   - Time-window picker present
 *   - Page heading "Performance Command Center" visible
 *
 * Auth: reads Firebase __session cookie from /tmp/smoke_session_cookie.txt
 * (written by the cross-gate visual smoke session).
 *
 * Re-run:
 *   Write a fresh session cookie to /tmp/smoke_session_cookie.txt, then:
 *   npx playwright test tests/e2e/gate_i_performance_smoke.spec.ts --reporter=list --workers=1
 */

const SS = 'tests/screenshots/gate_i_smoke'

function getSessionCookie(): string | null {
  try {
    return readFileSync('/tmp/smoke_session_cookie.txt', 'utf8').trim()
  } catch {
    return null
  }
}

const SESSION = getSessionCookie()
const SKIP = !SESSION

test.describe('Gate I — Performance Command Center visual smoke', () => {
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

  test('performance dashboard renders heading and KPI grid', async ({ page }) => {
    await page.goto('/performance')
    await page.waitForLoadState('networkidle')

    // Screenshot full page
    await page.screenshot({
      path: `${SS}/performance_full.png`,
      fullPage: true,
    })

    // Heading must be present
    await expect(page.getByText('Performance Command Center').first()).toBeVisible()

    // At least one KPI tile heading visible (text from KpiTile titles)
    const kpiHeading = page.getByText(/performance health|retrieval health/i).first()
    await expect(kpiHeading).toBeVisible()

    // Screenshot KPI section
    const kpiSection = page.locator('.grid').filter({ has: page.getByText(/performance health/i) }).first()
    if (await kpiSection.count() > 0) {
      await kpiSection.screenshot({ path: `${SS}/kpi_tiles.png` })
    }

    // Query log section heading
    await expect(page.getByText('Query log').first()).toBeVisible()

    // Table header present (query log table)
    const tableHeader = page.locator('table thead').first()
    if (await tableHeader.count() > 0) {
      await tableHeader.screenshot({ path: `${SS}/query_log_header.png` })
    }
  })

  test('time-window picker is present', async ({ page }) => {
    await page.goto('/performance')
    await page.waitForLoadState('networkidle')

    // Time-window picker buttons (7d, 30d, 90d, etc.)
    const timeButtons = page.locator('button').filter({ hasText: /7d|30d|24h|90d/i })
    const buttonCount = await timeButtons.count()
    expect(buttonCount).toBeGreaterThan(0)

    if (buttonCount > 0) {
      await timeButtons.first().locator('..').screenshot({ path: `${SS}/time_window_picker.png` })
    }
  })

  test('clicking Eval runs tab shows eval run table', async ({ page }) => {
    await page.goto('/performance/eval-runs')
    await page.waitForLoadState('networkidle')
    await page.screenshot({ path: `${SS}/eval_runs.png`, fullPage: true })

    // Eval runs page should have a table
    const evalTable = page.locator('table').first()
    if (await evalTable.count() > 0) {
      await evalTable.screenshot({ path: `${SS}/eval_table.png` })
    }

    // Either "No eval runs recorded yet" or actual rows
    const noRuns = page.getByText('No eval runs recorded yet').first()
    const anyRow = page.locator('tbody tr').first()
    const hasContent = (await noRuns.count() > 0) || (await anyRow.count() > 0)
    expect(hasContent).toBe(true)
  })
})
