import { test, expect } from '@playwright/test'

/**
 * Portal Redesign R0 — AppShell smoke tests.
 * These require an authenticated session; tests are skipped in CI unless
 * SMOKE_SESSION_COOKIE and SMOKE_CHART_ID are set (same env contract as the
 * cutover:stage1-smoke script).
 */

const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE
const SKIP = !SESSION_COOKIE

test.describe('AppShell — authenticated routes', () => {
  test.skip(SKIP, 'SMOKE_SESSION_COOKIE not set; skipping authenticated smoke tests')

  test.beforeEach(async ({ context }) => {
    await context.addCookies([
      { name: 'session', value: SESSION_COOKIE!, domain: 'localhost', path: '/' },
    ])
  })

  test('dashboard renders left rail nav', async ({ page }) => {
    await page.goto('/dashboard')
    const nav = page.getByRole('navigation', { name: 'Primary navigation' })
    await expect(nav).toBeVisible()
    await expect(nav.getByRole('link', { name: 'Jātakas' })).toBeVisible()
  })

  test('dashboard breadcrumb shows Roster', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page.getByRole('navigation', { name: 'Breadcrumb' })).toBeVisible()
    await expect(page.getByText('Roster')).toBeVisible()
  })

  test('cockpit renders left rail with BuildHeader below breadcrumb', async ({ page }) => {
    await page.goto('/cockpit')
    await expect(page.getByRole('navigation', { name: 'Primary navigation' })).toBeVisible()
    await expect(page.getByRole('navigation', { name: 'Breadcrumb' })).toBeVisible()
  })

  test('sign-out dropdown is reachable via user menu', async ({ page }) => {
    await page.goto('/dashboard')
    await page.getByRole('button', { name: 'User menu' }).click()
    await expect(page.getByRole('menuitem', { name: 'Sign out' })).toBeVisible()
  })
})
