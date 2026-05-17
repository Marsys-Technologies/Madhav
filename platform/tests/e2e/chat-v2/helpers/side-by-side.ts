/**
 * E.1 — Side-by-side capture helper.
 *
 * Captures legacy (flag-off) and V2 (flag-on) screenshots of the same
 * conversation state, returning both for composite review or toMatchSnapshot.
 *
 * Usage:
 *   const { legacy, v2 } = await captureSideBySide(page, scenario)
 *
 * The helper toggles the `chatV2Enabled` query param (dev-mode override) to
 * render each variant without needing two full deploys.
 */

import type { Page } from '@playwright/test'

const CLIENT_ID = process.env.MARSYS_TEST_CLIENT_ID ?? '362f9f17-95a5-490b-a5a7-027d3e0efda0'

export interface SideBySideScenario {
  name: string
  setup?: (page: Page) => Promise<void>
  waitFor?: (page: Page) => Promise<void>
  /** Viewport width; default 1280 */
  width?: number
  /** Viewport height; default 800 */
  height?: number
}

export interface SideBySideCapture {
  legacy: Buffer
  v2: Buffer
}

export async function captureSideBySide(
  page: Page,
  scenario: SideBySideScenario,
): Promise<SideBySideCapture> {
  const width = scenario.width ?? 1280
  const height = scenario.height ?? 800
  await page.setViewportSize({ width, height })

  async function captureVariant(variant: 'legacy' | 'v2'): Promise<Buffer> {
    const base = `/clients/${CLIENT_ID}/consume`
    const url = variant === 'v2' ? `${base}?__chatV2=1` : base
    await page.goto(url, { waitUntil: 'domcontentloaded' })
    const root = variant === 'v2'
      ? page.getByTestId('consume-chat-v2-root')
      : page.locator('[data-testid="consume-shell-root"], main').first()
    await root.waitFor({ state: 'visible', timeout: 20_000 })
    if (scenario.setup) await scenario.setup(page)
    if (scenario.waitFor) await scenario.waitFor(page)
    return page.screenshot({ fullPage: false, type: 'png' })
  }

  const legacy = await captureVariant('legacy')
  const v2 = await captureVariant('v2')
  return { legacy, v2 }
}

// ─── Predefined scenarios ────────────────────────────────────────────────────

export const SCENARIOS: SideBySideScenario[] = [
  {
    name: 'empty-state',
    waitFor: async (page) => {
      await page.waitForTimeout(1000)
    },
  },
  {
    name: 'sidebar-open',
    waitFor: async (page) => {
      const btn = page.getByTestId('v2-mobile-sidebar-open').first()
      if (await btn.isVisible()) await btn.click()
      await page.waitForTimeout(500)
    },
  },
  {
    name: 'composer-focused',
    waitFor: async (page) => {
      const input = page
        .getByTestId('v2-composer-input')
        .or(page.getByPlaceholder('Reply to Claude…').first())
      await input.click()
      await page.waitForTimeout(300)
    },
  },
  {
    name: 'bottom-bar-visible',
    waitFor: async (page) => {
      await page.getByTestId('v2-bottom-bar').waitFor({ state: 'visible', timeout: 5_000 }).catch(() => {})
      await page.waitForTimeout(300)
    },
  },
  {
    name: 'header-desktop',
    waitFor: async (page) => {
      await page.getByTestId('v2-header').waitFor({ state: 'visible', timeout: 5_000 }).catch(() => {})
      await page.waitForTimeout(300)
    },
  },
]
