/**
 * Shared helpers for the Paripraśna gate battery.
 *
 * Every gate spec navigates to the same test-only harness page
 * (tests/pariprashna/harness/public/index.html, served by
 * scripts/replay/server.ts) with `?fixture=<name>[&violate=<key>]`, waits
 * for the fixture to finish streaming, then reads `window.__harness` for
 * the counters/violations the harness client recorded during the run.
 *
 * Design note on the red-then-green proof pattern used throughout
 * gates/*.spec.ts: rather than committing a test that is expected to FAIL
 * (which would leave CI red), each gate file contains a "red proof" test
 * that navigates with `violate=<thisGate'sKey>` and asserts the harness DID
 * record the violation (metric > 0 / condition present). That assertion
 * itself passes in normal CI — what it proves is that the detector is
 * live and would have failed the "green" test in the same file had the
 * violation been present there instead. See the lane's final report for
 * the literal manual red-then-green transcript (clean assertion code path
 * run once against a seeded violation and observed to fail, then against a
 * clean harness and observed to pass) — `scripts/replay/selftest.ts`
 * automates that literal demonstration.
 */
import type { Locator, Page } from '@playwright/test'

export type ViolateKey =
  | 'cls'
  | 'caret'
  | 'transmute'
  | 'raf'
  | 'viewport'
  | 'pill'
  | 'axe'
  | 'mobile-tap'

export interface HarnessSnapshot {
  fixture: string
  violate: string | null
  ready: boolean
  done: boolean
  renderCount: number
  framesElapsed: number
  settledShiftCount: number
  settledShiftDetails: Array<{ blockId: string; drift: number; at: number }>
  caretViolations: Array<{ at: number; caretRect: DOMRectLike; tailRect: DOMRectLike }>
  caretChecks: number
  viewportShiftCount: number
  viewportShiftDetails: Array<{ heightDrift: number; pageDrift: number; at: number }>
  pillShown: boolean
  pillReSquelched: boolean
  eventsReceived: number
  eventsExpectedTotal: number | null
  malformedSkipped: number
  streamError?: string
}

interface DOMRectLike {
  top: number
  left: number
  bottom: number
  right: number
  width: number
  height: number
}

/** Navigate to the harness page for `fixture`, optionally seeding a
 *  deliberate violation via `violate`. */
export async function gotoHarness(page: Page, fixture: string, violate?: ViolateKey | null): Promise<void> {
  const qs = new URLSearchParams({ fixture })
  if (violate) qs.set('violate', violate)
  await page.goto(`/?${qs.toString()}`)
}

/** Wait until the fixture has finished streaming (normal completion,
 *  disconnect, or abrupt end — `done` is set in the client's `finally`
 *  block regardless of outcome). */
export async function waitForStreamDone(page: Page, timeoutMs = 15_000): Promise<void> {
  await page.waitForFunction(() => document.body.dataset.done === 'true', undefined, { timeout: timeoutMs })
}

/** Read the current `window.__harness` instrumentation snapshot. */
export async function getHarness(page: Page): Promise<HarnessSnapshot> {
  return page.evaluate(() => (window as unknown as { __harness: HarnessSnapshot }).__harness)
}

/** Convenience: navigate, wait for completion, return the snapshot. */
export async function runFixture(page: Page, fixture: string, violate?: ViolateKey | null): Promise<HarnessSnapshot> {
  await gotoHarness(page, fixture, violate)
  await waitForStreamDone(page)
  return getHarness(page)
}

/**
 * Lets `scripts/replay/selftest.ts` force a gate's "green"/main assertion to
 * run against a seeded violation, by setting `PARIPRASHNA_VIOLATE=<key>`
 * before invoking `npx playwright test`. Every gate's main test calls
 * `mainRunViolate('cls')` (its own key) instead of hardcoding `null` — in
 * normal CI this resolves to `null` (clean run); under selftest with a
 * matching env var it resolves to the violation, so the SAME assertion
 * code path that normally passes is the one selftest proves goes red.
 */
export function mainRunViolate(key: ViolateKey): ViolateKey | null {
  return process.env.PARIPRASHNA_VIOLATE === key ? key : null
}

/**
 * Tap on touch-capable contexts (the `mobile-390x844` project), gracefully
 * fall back to click on contexts without touch support (the `chromium`
 * desktop project, which also runs every gate spec — Playwright's
 * `.tap()` throws immediately there since it has no touch emulation). Both
 * ultimately exercise the same DOM `click` listener a real tap or click
 * would fire, so the fallback doesn't weaken the assertion.
 */
export async function tapOrClick(locator: Locator, timeout = 3000): Promise<void> {
  try {
    await locator.tap({ timeout })
  } catch (err) {
    if (String(err).includes('does not support tap')) {
      await locator.click({ timeout })
    } else {
      throw err
    }
  }
}

/** Fixtures that reach a normal, fully-committed completion — useful for
 *  gates that need "a real settled block exists" rather than a
 *  deliberately-truncated stream. */
export const CLEAN_COMPLETION_FIXTURES = [
  'adaptive-3-pass',
  'single-pass',
  'gemini-slabs',
  '1-byte-trickle',
  '3s-stall',
  'citation-dense',
  'giant-table',
  'honest-gap',
] as const
