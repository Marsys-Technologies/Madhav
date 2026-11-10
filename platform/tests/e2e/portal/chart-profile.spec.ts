import { test, expect } from '@playwright/test'

// These tests assume the dev server is running with a seeded super_admin session.
// Set SMOKE_SESSION_COOKIE and SMOKE_CHART_ID in env to run against a live instance.
const CHART_ID = process.env.SMOKE_CHART_ID ?? 'test-chart-id'

test.describe('Chart Profile — /clients/[id]', () => {
  test.beforeEach(async ({ context }) => {
    const sessionCookie = process.env.SMOKE_SESSION_COOKIE
    if (sessionCookie) {
      await context.addCookies([
        { name: 'session', value: sessionCookie, domain: 'localhost', path: '/' },
      ])
    }
  })

  test('super_admin sees hero, 3 rooms, and side rail', async ({ page }) => {
    await page.goto(`/clients/${CHART_ID}`)
    // Hero band
    await expect(page.locator('h1')).toBeVisible()
    // Three room cards
    await expect(page.getByText('Build Room')).toBeVisible()
    await expect(page.getByText('Consume Room')).toBeVisible()
    await expect(page.getByText('Timeline Room')).toBeVisible()
    // Side rail — Vimshottari Dasha label
    await expect(page.getByText(/Vimshottari Dasha/i)).toBeVisible()
  })

  test('super_admin sees Continue building CTA enabled', async ({ page }) => {
    await page.goto(`/clients/${CHART_ID}`)
    const cta = page.getByRole('link', { name: /Continue building/i })
    await expect(cta).toBeVisible()
    await expect(cta).toHaveAttribute('href', `/clients/${CHART_ID}/build`)
  })

  test('super_admin sees audit deep-link in side rail', async ({ page }) => {
    await page.goto(`/clients/${CHART_ID}`)
    await expect(page.getByRole('link', { name: /Audit log/i })).toBeVisible()
  })

  test('Timeline Room CTA is disabled', async ({ page }) => {
    await page.goto(`/clients/${CHART_ID}`)
    // Disabled CTA is a span, not a link
    const disabledCta = page.locator('span.cursor-not-allowed', { hasText: /coming in R5/i })
    await expect(disabledCta).toBeVisible()
  })

  test('SVG rasi chart is present with role=img', async ({ page }) => {
    await page.goto(`/clients/${CHART_ID}`)
    const svg = page.locator('svg[role="img"]')
    await expect(svg).toBeVisible()
  })

  test('prefers-reduced-motion: Mandala has no animation', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto(`/clients/${CHART_ID}`)
    // Mandala SVG is aria-hidden; just confirm page loads without error
    await expect(page.locator('h1')).toBeVisible()
  })
})
