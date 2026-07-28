/**
 * G-MOBILE — full battery at 390x844 viewport; citation chips are
 * tap-open.
 *
 * The "full battery at 390x844" half of this requirement is satisfied by
 * `tests/pariprashna/playwright.config.ts`'s `mobile-390x844` project,
 * which runs every spec in this directory (including this one) at that
 * viewport — run via `npm run pariprashna:gates:mobile`. This file adds the
 * mobile-specific assertion the brief calls out by name: citation chips
 * must be tap-openable (real touch-sized target, opens on tap, not just
 * hover/click-precision-dependent).
 *
 * Seeded violation (`?violate=mobile-tap`): the client applies
 * `pointer-events: none` to citation chips, so a tap never reaches the
 * click handler and the detail never opens.
 */
import { test, expect } from '@playwright/test'
import { gotoHarness, mainRunViolate, tapOrClick, waitForStreamDone } from './_helpers'

test.describe('G-MOBILE — citation chips are tap-open', () => {
  test('citation-dense: tapping a chip opens its detail, min 28px hit target', async ({ page }) => {
    await gotoHarness(page, 'citation-dense', mainRunViolate('mobile-tap'))
    await waitForStreamDone(page)

    const chip = page.locator('.citation-chip').first()
    await expect(chip).toBeVisible()

    const box = await chip.boundingBox()
    expect(box).not.toBeNull()
    expect(box!.height).toBeGreaterThanOrEqual(28)
    expect(box!.width).toBeGreaterThanOrEqual(28)

    await tapOrClick(chip)
    await expect(chip).toHaveAttribute('aria-expanded', 'true')
    const detail = page.locator('.citation-detail').first()
    await expect(detail).toBeVisible()
  })

  test('RED PROOF: seeded mobile-tap violation is detected (tap does not open detail)', async ({ page }) => {
    await gotoHarness(page, 'citation-dense', 'mobile-tap')
    await waitForStreamDone(page)
    const chip = page.locator('.citation-chip').first()
    await expect(chip).toBeVisible()
    // pointer-events:none means Playwright's actionability check itself
    // will refuse the tap/click — that refusal (a timeout) IS the proof the
    // violation blocks interaction, so a bare try/catch documents it
    // without failing the whole suite.
    let tapSucceeded = true
    try {
      await tapOrClick(chip, 2000)
    } catch {
      tapSucceeded = false
    }
    expect(tapSucceeded, 'tap/click unexpectedly succeeded against a pointer-events:none chip').toBe(false)
  })
})
