/**
 * G-VIEWPORT — thread container height and page height stay constant during
 * streaming.
 *
 * The thread viewport is a fixed-height, internally-scrolling region; new
 * content must never grow the container itself or the surrounding page.
 * client.mjs samples `#thread-viewport`'s bounding-rect height and
 * `document.documentElement.scrollHeight` every animation frame and flags
 * any drift beyond 1px.
 *
 * Seeded violation (`?violate=viewport`): the client adds a class that sets
 * the viewport to `height: auto; overflow-y: visible`, so it (and the page)
 * grow with streamed content instead of scrolling internally.
 */
import { test, expect } from '@playwright/test'
import { getHarness, gotoHarness, mainRunViolate, waitForStreamDone } from './_helpers'

const GROWING_CONTENT_FIXTURES = ['giant-table', 'adaptive-3-pass']

test.describe('G-VIEWPORT — container and page height stay constant while streaming', () => {
  for (const fixture of GROWING_CONTENT_FIXTURES) {
    test(`${fixture}: zero viewport/page height drift`, async ({ page }) => {
      await gotoHarness(page, fixture, mainRunViolate('viewport'))
      await waitForStreamDone(page)
      const harness = await getHarness(page)
      expect(
        harness.viewportShiftCount,
        `viewport/page height drift detected: ${JSON.stringify(harness.viewportShiftDetails)}`,
      ).toBe(0)
    })
  }

  test('RED PROOF: seeded viewport violation is detected (viewportShiftCount > 0)', async ({ page }) => {
    await gotoHarness(page, 'giant-table', 'viewport')
    await waitForStreamDone(page)
    const harness = await getHarness(page)
    expect(harness.viewportShiftCount).toBeGreaterThan(0)
  })
})
