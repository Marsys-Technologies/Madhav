import { test, expect, type Page } from '@playwright/test'
import { existsSync, readFileSync } from 'fs'

/**
 * New Client → Nirmāṇa and the direct cockpit bookmark — [BUILD-ORCH-D-S5].
 *
 * Manual prerequisites: a dev server with Google Places unconfigured for
 * manual birth-place entry, an existing Firebase session cookie at COOKIE_PATH,
 * and a Cloud SQL connection for chart creation. The bookmark check uses
 * SMOKE_CHART_ID for an existing chart the session can prepare.
 *
 * npx playwright test tests/e2e/new-client-flow.spec.ts --reporter=list --workers=1
 *
 * @ci-skip (requires live dev server, session and Cloud SQL)
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

export async function expectPreparation(page: Page, chartId: string, timeout = 15_000) {
  await expect(page).toHaveURL(`/clients/${chartId}/nirmana`, { timeout })
  const preparation = page.getByTestId('build-page-root')
  await expect(preparation).toHaveAttribute('data-permission', 'all', { timeout })
  const toolbar = preparation.locator('.preparation-toolbar')
  await expect(toolbar.getByRole('button', { name: /^(?:Build all|Rebuild all|■ Stop)$/i })).toBeVisible({ timeout })
}

export async function expectDirectCockpit(page: Page, chartId: string, timeout = 10_000) {
  await expect(page).toHaveURL(`/clients/${chartId}/cockpit`, { timeout })
  await expect(
    page.getByRole('button', { name: /^(?:Build Chart|Continue Build|Rebuild All|Stop)$/ }).first(),
  ).toBeVisible({ timeout })
}

export async function blockBuildCommands(page: Page) {
  const attempts: string[] = []
  await page.route(
    (url) => url.pathname.startsWith('/api/build/') || url.pathname.startsWith('/api/cockpit/'),
    async (route) => {
      const request = route.request()
      const method = request.method()
      if (['GET', 'HEAD', 'OPTIONS'].includes(method)) {
        await route.fallback()
        return
      }
      attempts.push(`${method} ${new URL(request.url()).pathname}`)
      await route.abort()
    },
  )
  return attempts
}

type ChartCreation = { ok: boolean; chartId: unknown }

async function observeChartCreation(page: Page) {
  let record!: (creation: ChartCreation) => void
  const creation = new Promise<ChartCreation>((resolve) => { record = resolve })
  await page.exposeBinding('__recordNewClientSmokeCreation', ({ frame }, result: ChartCreation) => {
    if (frame === page.mainFrame()) record(result)
  })
  await page.addInitScript(() => {
    const fetch = window.fetch.bind(window)
    window.fetch = async (input, init) => {
      const request = input instanceof Request ? input : null
      const url = new URL(request?.url ?? String(input), location.href)
      const method = init?.method ?? request?.method ?? 'GET'
      const response = await fetch(input, init)
      if (url.origin === location.origin && url.pathname === '/api/clients/create' && method.toUpperCase() === 'POST') {
        // Capture the clone before the form can navigate away and discard the network response body.
        const body = await response.clone().json().catch(() => null)
        const smokeWindow = window as Window & {
          __recordNewClientSmokeCreation?: (result: ChartCreation) => Promise<void>
        }
        const recordCreation = smokeWindow.__recordNewClientSmokeCreation
        if (!recordCreation) throw new Error('Chart creation observer was not registered')
        await recordCreation({ ok: response.ok, chartId: body?.chart_id })
      }
      return response
    }
  })
  return { creation }
}

test.describe('New client preparation and direct cockpit', () => {
  test.beforeEach(async ({ page }) => {
    const sessionCookie = tryReadCookie()
    if (!sessionCookie) {
      test.skip(true, 'No manual smoke session cookie (@ci-skip)')
      return
    }
    await page.context().addCookies([
      {
        name: '__session',
        value: sessionCookie,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        sameSite: 'Lax',
      },
    ])
  })

  test('new client form lands on the created chart’s preparation page', async ({ page }) => {
    const buildCommands = await blockBuildCommands(page)
    const { creation } = await observeChartCreation(page)
    const chartName = 'D-S5 Smoke Native'
    await page.goto('/clients/new')
    await expect(page).not.toHaveURL(/login/)

    await page.getByLabel('Full name', { exact: true }).fill(chartName)
    await page.getByRole('combobox', { name: 'Gender' }).click()
    await page.getByRole('option', { name: 'Prefer not to say' }).click()
    await page.getByLabel('Birth date in DD-MMM-YYYY format').fill('12-Mar-1991')
    await page.getByLabel(/^Time \(24 h\)/).fill('09:15')
    await page.getByLabel(/^Birth place/).fill('Puri, Odisha, India')
    await page.getByLabel(/^Latitude/).fill('19.81')
    await page.getByLabel(/^Longitude/).fill('85.83')

    const [created] = await Promise.all([
      creation,
      page.getByRole('button', { name: 'Build chart', exact: true }).click(),
    ])
    expect(created.ok).toBe(true)
    const chartId = created.chartId
    if (typeof chartId !== 'string') throw new Error('Create response did not include a chart UUID')
    expect(chartId).toMatch(/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i)
    await expectPreparation(page, chartId)
    await expect(page.getByTestId('build-page-root').locator('.preparation-toolbar').getByText(chartName, { exact: true })).toBeVisible()
    expect(buildCommands).toEqual([])
  })

  test('the direct chart cockpit bookmark still shows current build controls', async ({ page }) => {
    const chartId = process.env.SMOKE_CHART_ID
    if (!chartId) {
      test.skip(true, '@ci-skip: SMOKE_CHART_ID not set — cannot navigate directly to cockpit')
      return
    }

    const buildCommands = await blockBuildCommands(page)
    await page.goto(`/clients/${chartId}/cockpit`)
    await expectDirectCockpit(page, chartId)
    expect(buildCommands).toEqual([])
  })
})
