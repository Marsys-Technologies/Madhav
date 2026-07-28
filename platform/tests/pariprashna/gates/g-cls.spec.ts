/**
 * G-CLS — settled-region layout-shift contribution must be 0 above the
 * volatile tail.
 *
 * Once a block commits and moves into the settled region, its position must
 * never drift again, no matter what streams in below it. The harness client
 * (client.mjs) records every committed block's post-settle bounding rect and
 * re-checks it every animation frame; any drift beyond 0.5px increments
 * `window.__harness.settledShiftCount`.
 *
 * Seeded violation (`?violate=cls`): after each commit, the client inserts a
 * spacer <div> at the TOP of the settled region, pushing every
 * already-committed block down — the exact class of bug this gate exists to
 * catch (e.g. a header/banner that grows above the thread).
 */
import { test, expect } from '@playwright/test'
import { getHarness, gotoHarness, mainRunViolate, waitForStreamDone } from './_helpers'

const FIXTURES_WITH_MULTIPLE_COMMITS = ['adaptive-3-pass', 'giant-table', 'citation-dense', 'honest-gap']

test.describe('G-CLS — settled region never shifts once committed', () => {
  for (const fixture of FIXTURES_WITH_MULTIPLE_COMMITS) {
    test(`${fixture}: zero settled-region shift contribution`, async ({ page }) => {
      await gotoHarness(page, fixture, mainRunViolate('cls'))
      await waitForStreamDone(page)
      const harness = await getHarness(page)
      expect(
        harness.settledShiftCount,
        `settled-region shift detected: ${JSON.stringify(harness.settledShiftDetails)}`,
      ).toBe(0)
    })
  }

  test('RED PROOF: seeded cls violation is detected (settledShiftCount > 0)', async ({ page }) => {
    await gotoHarness(page, 'adaptive-3-pass', 'cls')
    await waitForStreamDone(page)
    const harness = await getHarness(page)
    expect(harness.settledShiftCount).toBeGreaterThan(0)
    expect(harness.settledShiftDetails.length).toBeGreaterThan(0)
  })
})
