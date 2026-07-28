/**
 * G-RAF — React commit count <= frames elapsed (coalesced rendering, not one
 * render per delta).
 *
 * A high-frequency fixture (1-byte-trickle sends 60+ single-character
 * deltas) must not translate into 60+ separate DOM commits — client.mjs
 * batches all pending mutations behind a single `requestAnimationFrame`
 * flush (see `scheduleRender`), incrementing `renderCount` once per actual
 * flush. Frames elapsed is tracked independently by the per-frame
 * measurement loop.
 *
 * Seeded violation (`?violate=raf`): `scheduleRender` bypasses the rAF queue
 * entirely and applies + counts a render synchronously per event, so
 * renderCount tracks 1:1 with event count regardless of frame budget.
 */
import { test, expect } from '@playwright/test'
import { getHarness, gotoHarness, mainRunViolate, waitForStreamDone } from './_helpers'

const HIGH_FREQUENCY_FIXTURES = ['1-byte-trickle', 'giant-table']

test.describe('G-RAF — rendering is coalesced, not one commit per delta', () => {
  for (const fixture of HIGH_FREQUENCY_FIXTURES) {
    test(`${fixture}: renderCount <= framesElapsed`, async ({ page }) => {
      await gotoHarness(page, fixture, mainRunViolate('raf'))
      await waitForStreamDone(page)
      const harness = await getHarness(page)
      expect(harness.renderCount).toBeLessThanOrEqual(harness.framesElapsed)
      // Sanity: the fixture actually generated enough events that coalescing
      // was doing real work (renderCount is meaningfully smaller than a
      // naive one-render-per-event count would have been) — otherwise the
      // assertion above could pass vacuously on a near-empty fixture. NOTE:
      // this is deliberately NOT "eventsReceived > framesElapsed" — frame
      // count scales with the fixture's real wall-clock duration (which the
      // 1-byte-trickle transport-level fragmentation can stretch well past
      // its own event count), so it is not a stable proxy for "coalescing
      // mattered" across fixtures with different transport timing.
      expect(harness.eventsReceived).toBeGreaterThan(harness.renderCount)
    })
  }

  test('RED PROOF: seeded raf violation is detected (renderCount > framesElapsed)', async ({ page }) => {
    await gotoHarness(page, '1-byte-trickle', 'raf')
    await waitForStreamDone(page)
    const harness = await getHarness(page)
    expect(harness.renderCount).toBeGreaterThan(harness.framesElapsed)
  })
})
