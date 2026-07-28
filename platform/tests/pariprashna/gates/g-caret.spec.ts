/**
 * G-CARET — caret rect must be a subset of the tail-block rect, every frame.
 *
 * The streaming caret must always visually belong to the block currently
 * receiving text, never drift over settled content, a table, or empty
 * space. client.mjs recomputes the caret's position on every render flush
 * and the per-frame measurement loop checks containment every animation
 * frame, recording any violation.
 *
 * Seeded violation (`?violate=caret`): the client positions the caret using
 * the LAST SETTLED block instead of the live tail block — reproducing the
 * "caret ends up under a table" class of bug named in the brief. This only
 * has an observable effect once at least one EARLIER block has already
 * committed (there must be a wrong element to point at), so the red proof
 * below uses `adaptive-3-pass` (2 sequential blocks) rather than a
 * single-block fixture.
 */
import { test, expect } from '@playwright/test'
import { getHarness, gotoHarness, mainRunViolate, waitForStreamDone } from './_helpers'

const STREAMING_FIXTURES = ['giant-table', 'citation-dense', '1-byte-trickle', 'gemini-slabs']

test.describe('G-CARET — caret stays within the active tail block', () => {
  for (const fixture of STREAMING_FIXTURES) {
    test(`${fixture}: caret never leaves the tail block rect`, async ({ page }) => {
      await gotoHarness(page, fixture, mainRunViolate('caret'))
      await waitForStreamDone(page)
      const harness = await getHarness(page)
      // A gate that never actually checked anything would trivially "pass" —
      // assert the measurement loop ran enough to be meaningful.
      expect(harness.caretChecks, 'caret containment was never actually measured').toBeGreaterThan(0)
      expect(
        harness.caretViolations,
        `caret escaped the tail block: ${JSON.stringify(harness.caretViolations)}`,
      ).toHaveLength(0)
    })
  }

  test('RED PROOF: seeded caret violation is detected (caretViolations > 0)', async ({ page }) => {
    // adaptive-3-pass commits block b1 before opening block b2 — during
    // b2's streaming, "point the caret at the last SETTLED block instead of
    // the tail" has a genuinely wrong (already-committed) block to land on.
    await gotoHarness(page, 'adaptive-3-pass', 'caret')
    await waitForStreamDone(page)
    const harness = await getHarness(page)
    expect(harness.caretViolations.length).toBeGreaterThan(0)
  })
})
