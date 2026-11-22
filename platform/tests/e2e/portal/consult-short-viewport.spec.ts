import { test, expect } from '@playwright/test'

/**
 * NIR-10: Saved & fresh Consult viewport geometry regression across
 * desktop (1280x800), standard phone (390x844), and short mobile height (390x544).
 *
 * Requires a running Next.js app (see playwright.config.ts webServer) and
 * optionally SMOKE_SESSION_COOKIE / SMOKE_CHART_ID / SMOKE_CONVERSATION_ID.
 */
const CHART_ID = process.env.SMOKE_CHART_ID ?? 'test-chart-id'
const CONV_ID = process.env.SMOKE_CONVERSATION_ID

const VIEWPORTS = [
  { name: 'mobile-390x844', width: 390, height: 844 },
  { name: 'short-390x544', width: 390, height: 544 },
  { name: 'desktop-1280x800', width: 1280, height: 800 },
] as const

test.describe('Consult Short-Viewport Layout (NIR-10)', () => {
  test.beforeEach(async ({ context }) => {
    const sessionCookie = process.env.SMOKE_SESSION_COOKIE
    if (sessionCookie) {
      await context.addCookies([
        { name: 'session', value: sessionCookie, domain: 'localhost', path: '/' },
      ])
    }
  })

  for (const vp of VIEWPORTS) {
    test(`fresh consult keeps composer and send action unoccluded at ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height })
      await page.goto(`/clients/${CHART_ID}/consult`)

      const input = page.getByTestId('v2-composer-input')
      await expect(input).toBeVisible()

      const sendBtn = page.getByTestId('v2-send-btn')
      await expect(sendBtn).toBeVisible()

      const geometry = await page.evaluate(() => {
        const inputEl = document.querySelector('[data-testid="v2-composer-input"]')
        const sendEl = document.querySelector('[data-testid="v2-send-btn"]')
        if (!inputEl || !sendEl) return null
        const ir = inputEl.getBoundingClientRect()
        const sr = sendEl.getBoundingClientRect()
        const inputHit = document.elementFromPoint(ir.left + ir.width / 2, ir.top + ir.height / 2)
        const sendHit = document.elementFromPoint(sr.left + sr.width / 2, sr.top + sr.height / 2)
        return {
          docScrollWidth: document.documentElement.scrollWidth,
          innerWidth: window.innerWidth,
          innerHeight: window.innerHeight,
          inputTop: ir.top,
          inputBottom: ir.bottom,
          sendTop: sr.top,
          sendBottom: sr.bottom,
          sendWidth: sr.width,
          sendHeight: sr.height,
          inputSelfHit: Boolean(inputHit && (inputEl === inputHit || inputEl.contains(inputHit))),
          sendSelfHit: Boolean(sendHit && (sendEl === sendHit || sendEl.contains(sendHit))),
        }
      })

      expect(geometry).not.toBeNull()
      if (!geometry) return
      expect(geometry.docScrollWidth).toBeLessThanOrEqual(vp.width)
      expect(geometry.inputTop).toBeGreaterThanOrEqual(0)
      expect(geometry.inputBottom).toBeLessThanOrEqual(vp.height)
      expect(geometry.sendTop).toBeGreaterThanOrEqual(0)
      expect(geometry.sendBottom).toBeLessThanOrEqual(vp.height)
      expect(geometry.inputSelfHit).toBe(true)
      expect(geometry.sendSelfHit).toBe(true)
      if (vp.width < 768) {
        expect(geometry.sendWidth).toBeGreaterThanOrEqual(44)
        expect(geometry.sendHeight).toBeGreaterThanOrEqual(44)
      }
    })
  }

  test('saved consultation scrolls thread cleanly inside short 390x544 viewport', async ({ page }) => {
    test.skip(!CONV_ID, 'Set SMOKE_CONVERSATION_ID to exercise live saved conversation route')
    await page.setViewportSize({ width: 390, height: 544 })
    await page.goto(`/clients/${CHART_ID}/consult/${CONV_ID}`)

    const input = page.getByTestId('v2-composer-input')
    await expect(input).toBeVisible()

    const bounds = await page.evaluate(() => {
      const vpEl = document.querySelector('[data-testid="v2-thread-viewport"]')
      const sendEl = document.querySelector('[data-testid="v2-send-btn"]')
      const sr = sendEl?.getBoundingClientRect()
      const sendHit = sr ? document.elementFromPoint(sr.left + sr.width / 2, sr.top + sr.height / 2) : null
      return {
        viewportHeight: vpEl?.getBoundingClientRect().height ?? 0,
        sendBottom: sr?.bottom ?? 9999,
        sendSelfHit: Boolean(sendHit && sendEl && (sendEl === sendHit || sendEl.contains(sendHit))),
        docScrollWidth: document.documentElement.scrollWidth,
      }
    })

    expect(bounds.docScrollWidth).toBeLessThanOrEqual(390)
    expect(bounds.viewportHeight).toBeGreaterThanOrEqual(80)
    expect(bounds.sendBottom).toBeLessThanOrEqual(544)
    expect(bounds.sendSelfHit).toBe(true)
  })
})
