/**
 * G-AXE — axe-core clean; committed blocks must exit the aria-live region on
 * commit.
 *
 * Two independent checks, because "committed blocks must exit aria-live" is
 * a project-specific structural rule, not a standard WCAG success criterion
 * axe-core itself checks:
 *
 *  1. axe-core scan (standard a11y rules — labels, roles, landmarks) must
 *     report zero critical/serious violations.
 *  2. A custom structural assertion: no `[data-committed="true"]` block may
 *     be a descendant of the `[aria-live]` region (`#tail`) — a committed
 *     block that stays inside the live region would cause a screen reader
 *     to keep re-announcing settled content indefinitely.
 *
 * Seeded violation (`?violate=axe`): the client skips reparenting committed
 * blocks out of `#tail` (they stay in the aria-live region permanently).
 */
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { gotoHarness, mainRunViolate, waitForStreamDone } from './_helpers'

test.describe('G-AXE — accessibility baseline + committed-block live-region hygiene', () => {
  test('adaptive-3-pass: zero critical/serious axe violations at rest', async ({ page }) => {
    await gotoHarness(page, 'adaptive-3-pass', mainRunViolate('axe'))
    await waitForStreamDone(page)

    const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()
    const blocking = results.violations.filter((v) => v.impact === 'critical' || v.impact === 'serious')
    const report = blocking.map((v) => `  [${v.impact}] ${v.id}: ${v.description} — ${v.helpUrl}`).join('\n')
    expect(blocking, `axe found ${blocking.length} critical/serious violation(s):\n${report}`).toHaveLength(0)
  })

  test('adaptive-3-pass: composer input and action buttons have accessible names', async ({ page }) => {
    await gotoHarness(page, 'adaptive-3-pass', null)
    await waitForStreamDone(page)
    const composerLabel = await page.getByTestId('composer-input').getAttribute('aria-label')
    expect(composerLabel).toBeTruthy()
    const sendLabel = await page.getByTestId('send-btn').getAttribute('aria-label')
    expect(sendLabel).toBeTruthy()
  })

  test('adaptive-3-pass: committed blocks exit the aria-live region on commit', async ({ page }) => {
    await gotoHarness(page, 'adaptive-3-pass', mainRunViolate('axe'))
    await waitForStreamDone(page)
    const violatingCount = await page.evaluate(() => {
      const liveRegion = document.querySelector('[aria-live]')!
      return liveRegion.querySelectorAll('[data-committed="true"]').length
    })
    expect(violatingCount, 'committed block(s) still live inside the aria-live region').toBe(0)
  })

  test('RED PROOF: seeded axe violation is detected (a committed block stays inside aria-live)', async ({ page }) => {
    await gotoHarness(page, 'adaptive-3-pass', 'axe')
    await waitForStreamDone(page)
    const violatingCount = await page.evaluate(() => {
      const liveRegion = document.querySelector('[aria-live]')!
      return liveRegion.querySelectorAll('[data-committed="true"]').length
    })
    expect(violatingCount).toBeGreaterThan(0)
  })
})
