/**
 * α1 — Web Vitals budget assertions.
 *
 * Verifies that the chat-v2 surface meets Core Web Vitals budgets:
 *   TTFB  < 800ms
 *   FCP   < 1500ms
 *   LCP   < 2500ms
 *   INP   < 200ms  (approx via long-task heuristic in fixture mode)
 *   CLS   < 0.1
 *
 * Gate: SOFT (continue-on-error) until γ; tightens to HARD at γ.
 *
 * Notes:
 *  - All measurements are against the spike page served locally with
 *    MARSYS_FIXTURE_MODE=true (no real provider latency).
 *  - These are conservative budgets; real-provider latency does not affect
 *    page render metrics (TTFB/FCP/LCP only measure resource delivery, not stream).
 */
import { test, expect } from '@playwright/test'

const SPIKE_URL = '/dev/chat-spike'

// Budgets (in ms or unitless for CLS)
const BUDGETS = {
  TTFB: 800,
  FCP: 1500,
  LCP: 2500,
  INP_PROXY: 200,  // measured as max interaction duration during stream
  CLS: 0.1,
}

test.describe('Web Vitals budget — chat-v2 spike page', () => {
  test.skip(
    !process.env.MARSYS_SUPER_ADMIN_SESSION,
    'Skipped: MARSYS_SUPER_ADMIN_SESSION not set',
  )

  test('TTFB and FCP within budget', async ({ page }) => {
    await page.goto(SPIKE_URL, { waitUntil: 'domcontentloaded' })

    const vitals = await page.evaluate(() => {
      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined
      const paintEntries = performance.getEntriesByType('paint')
      const fcp = paintEntries.find((e) => e.name === 'first-contentful-paint')

      return {
        ttfb: nav ? nav.responseStart - nav.requestStart : null,
        fcp: fcp ? fcp.startTime : null,
      }
    })

    if (vitals.ttfb !== null) {
      expect(vitals.ttfb, `TTFB ${vitals.ttfb}ms exceeds budget ${BUDGETS.TTFB}ms`).toBeLessThan(
        BUDGETS.TTFB,
      )
    }
    if (vitals.fcp !== null) {
      expect(vitals.fcp, `FCP ${vitals.fcp}ms exceeds budget ${BUDGETS.FCP}ms`).toBeLessThan(
        BUDGETS.FCP,
      )
    }
  })

  test('LCP within budget after page fully loads', async ({ page }) => {
    await page.goto(SPIKE_URL, { waitUntil: 'networkidle' })

    const lcp = await page.evaluate(
      () =>
        new Promise<number | null>((resolve) => {
          let lcpValue: number | null = null
          const obs = new PerformanceObserver((list) => {
            const entries = list.getEntries()
            if (entries.length > 0) {
              lcpValue = entries[entries.length - 1].startTime
            }
          })
          try {
            obs.observe({ type: 'largest-contentful-paint', buffered: true })
          } catch {
            // LCP not supported in this context
          }
          // Allow 500ms for LCP observer to fire
          setTimeout(() => {
            obs.disconnect()
            resolve(lcpValue)
          }, 500)
        }),
    )

    if (lcp !== null) {
      expect(lcp, `LCP ${lcp}ms exceeds budget ${BUDGETS.LCP}ms`).toBeLessThan(BUDGETS.LCP)
    }
  })

  test('CLS within budget during initial load', async ({ page }) => {
    await page.goto(SPIKE_URL, { waitUntil: 'networkidle' })

    const cls = await page.evaluate(
      () =>
        new Promise<number>((resolve) => {
          let clsValue = 0
          const obs = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              const layoutShift = entry as PerformanceEntry & {
                hadRecentInput?: boolean
                value?: number
              }
              if (!layoutShift.hadRecentInput && layoutShift.value) {
                clsValue += layoutShift.value
              }
            }
          })
          try {
            obs.observe({ type: 'layout-shift', buffered: true })
          } catch {
            // layout-shift not supported
          }
          setTimeout(() => {
            obs.disconnect()
            resolve(clsValue)
          }, 1000)
        }),
    )

    expect(cls, `CLS ${cls.toFixed(4)} exceeds budget ${BUDGETS.CLS}`).toBeLessThan(BUDGETS.CLS)
  })

  test('no long tasks during page load (INP proxy)', async ({ page }) => {
    // Collect long tasks (>50ms) during page load as an INP proxy
    const longTasks = await page.evaluate(
      () =>
        new Promise<number[]>((resolve) => {
          const durations: number[] = []
          const obs = new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              durations.push(entry.duration)
            }
          })
          try {
            obs.observe({ type: 'longtask', buffered: true })
          } catch {
            // longtask not supported in all browsers
          }
          setTimeout(() => {
            obs.disconnect()
            resolve(durations)
          }, 2000)
        }),
    )

    const maxLongTask = longTasks.length > 0 ? Math.max(...longTasks) : 0

    // Warn (not fail) on long tasks — this is a soft gate
    if (maxLongTask > BUDGETS.INP_PROXY) {
      console.warn(
        `[perf/web-vitals] Long task detected: ${maxLongTask.toFixed(1)}ms ` +
          `(budget: ${BUDGETS.INP_PROXY}ms). Review for INP issues.`,
      )
    }

    // Hard fail only if extremely bad (>500ms)
    expect(maxLongTask).toBeLessThan(500)
  })
})
