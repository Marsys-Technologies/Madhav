/**
 * G-PILL — a "follow" pill appears on upward scroll during streaming and
 * re-pins on click.
 *
 * client.mjs auto-scrolls the thread viewport to the bottom as content
 * streams in, UNLESS the user has scrolled away from the bottom, in which
 * case a "Follow" pill appears; clicking it jumps back to the bottom and
 * re-enables auto-follow.
 *
 * Seeded violation (`?violate=pill`): the client never attaches the scroll
 * listener that shows the pill, so scrolling away from the bottom mid-stream
 * is silently ignored — the pill never appears.
 */
import { test, expect, type Page } from '@playwright/test'
import { gotoHarness } from './_helpers'

async function scrollUpMidStream(page: Page, fixture: string, violate: 'pill' | null): Promise<void> {
  await gotoHarness(page, fixture, violate)
  // Wait until the thread viewport is ACTUALLY scrollable (content taller
  // than the fixed 480px viewport) before scrolling up — giant-table's
  // early rows don't yet overflow the viewport, so scrolling "up" before
  // that point is a no-op (scrollTop is already 0 at the bottom) and would
  // never legitimately cross the pill's distance-from-bottom threshold.
  await page.waitForFunction(
    () => {
      const el = document.querySelector('#thread-viewport')
      return !!el && el.scrollHeight > el.clientHeight + 60
    },
    undefined,
    { timeout: 15_000 },
  )
  await page.locator('#thread-viewport').evaluate((el) => {
    el.scrollTop = 0 // scroll to the top, away from the streaming tail
    el.dispatchEvent(new Event('scroll'))
  })
  // Give the scroll handler + a render tick time to react.
  await page.waitForTimeout(150)
}

test.describe('G-PILL — follow pill appears on scroll-up and re-pins on click', () => {
  test('giant-table: pill appears after scrolling up mid-stream, re-pins on click', async ({ page }) => {
    await scrollUpMidStream(page, 'giant-table', null)
    const pill = page.getByTestId('follow-pill')
    await expect(pill).toBeVisible()

    await pill.click()
    await expect(pill).toBeHidden()

    // Re-pinned: once the stream finishes, the viewport should have
    // returned to (and stayed at) the bottom.
    await page.waitForFunction(() => document.body.dataset.done === 'true', undefined, { timeout: 15_000 })
    const distanceFromBottom = await page.locator('#thread-viewport').evaluate((el) => {
      return el.scrollHeight - el.scrollTop - el.clientHeight
    })
    expect(distanceFromBottom).toBeLessThan(40)
  })

  test('RED PROOF: seeded pill violation is detected (pill never appears)', async ({ page }) => {
    await scrollUpMidStream(page, 'giant-table', 'pill')
    const pill = page.getByTestId('follow-pill')
    await expect(pill).toBeHidden()
    const harness = await page.evaluate(() => (window as unknown as { __harness: { pillShown: boolean } }).__harness)
    expect(harness.pillShown).toBe(false)
  })
})
