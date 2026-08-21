import { test, expect } from '@playwright/test'

/**
 * P2-close item 5 — RightDock must actually hide below the mobile
 * breakpoint, not just gate `openToCitation`'s chip-tap routing
 * (DockController.tsx's own doc comment always claimed the dock hides;
 * nothing enforced it until RightDock.tsx's `max-[900px]:hidden` class).
 *
 * `tests/pariprashna/gates/g-mobile.spec.ts` cannot cover this: that
 * battery runs against `scripts/replay/server.ts`'s standalone hand-built
 * harness (deliberately no Next.js dependency — see its own
 * playwright.config.ts header), which has no RightDock/DockController in
 * its DOM at all. This spec runs against the real app instead, following
 * the same SMOKE_SESSION_COOKIE-gated pattern as
 * tests/e2e/portal/cockpit-rail.spec.ts. Requires an authenticated session
 * cookie — skipped in CI unless SMOKE_SESSION_COOKIE is set.
 */

const SESSION_COOKIE = process.env.SMOKE_SESSION_COOKIE
const CHART_ID = process.env.SMOKE_CHART_ID
const SKIP = !SESSION_COOKIE || !CHART_ID

test.describe('P2-close item 5 — RightDock mobile collapse', () => {
  test.skip(SKIP, 'SMOKE_SESSION_COOKIE / SMOKE_CHART_ID not set; skipping authenticated smoke tests')

  test('below the mobile breakpoint: dock hidden, main column keeps real width', async ({ browser }) => {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } })
    await ctx.addCookies([{ name: '__session', value: SESSION_COOKIE!, domain: 'localhost', path: '/' }])
    const page = await ctx.newPage()
    await page.goto(`/clients/${CHART_ID}/pariprashna`)

    const dock = page.locator('[data-testid="pp-right-dock"]')
    await expect(dock).toBeHidden()

    const mainColumn = page.locator('[data-testid="pp-main-column"]')
    await expect(mainColumn).toBeVisible()
    const box = await mainColumn.boundingBox()
    expect(box).not.toBeNull()
    // Crushed-column regression guard: pre-fix, the dock's fixed 312px/46px
    // width rendered unconditionally, leaving ~2px for the reading column
    // on a 390px viewport. Assert it retains the bulk of the viewport.
    expect(box!.width).toBeGreaterThan(300)

    await ctx.close()
  })

  test('at desktop width: dock is visible (breakpoint actually discriminates, not always-hidden)', async ({ browser }) => {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } })
    await ctx.addCookies([{ name: '__session', value: SESSION_COOKIE!, domain: 'localhost', path: '/' }])
    const page = await ctx.newPage()
    await page.goto(`/clients/${CHART_ID}/pariprashna`)

    const dock = page.locator('[data-testid="pp-right-dock"]')
    await expect(dock).toBeVisible()

    await ctx.close()
  })
})
