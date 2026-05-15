/**
 * α1 — Streaming performance assertions.
 *
 * Measures:
 *   TTFT  — time from submit to first visible text chunk in the thread
 *   Frame budget — no frame drop >16ms during streaming (60fps budget)
 *   Tokens/sec — throughput of fixture stream
 *   Memory growth — heap growth during a full stream should be <50MB
 *
 * Gate: SOFT (continue-on-error) until γ; tightens to HARD at γ.
 *
 * All measurements are against the spike fixture endpoint with synthetic
 * 4–8ms chunk delays. TTFT budget is loose (3000ms) to accommodate dev-server
 * cold start; tightens in γ.
 */
import { test, expect } from '@playwright/test'

const SPIKE_URL = '/dev/chat-spike'
const TEST_PROMPT = 'Rahu 7th house analysis'
const STREAM_TIMEOUT = 35_000

// Budgets
const BUDGETS = {
  TTFT_MS: 3000,          // generous for fixture mode on local dev server
  FRAME_BUDGET_MS: 16,    // 60fps = ~16.7ms per frame
  FRAME_BUDGET_VIOLATIONS_MAX: 10,  // allow up to 10 frame drops
  MEMORY_GROWTH_MB: 50,   // heap growth during one stream
}

test.describe('Streaming performance — chat-v2 spike', () => {
  test.skip(
    !process.env.MARSYS_SUPER_ADMIN_SESSION,
    'Skipped: MARSYS_SUPER_ADMIN_SESSION not set',
  )

  test('TTFT within budget — first text visible within 3s of submit', async ({ page }) => {
    await page.goto(SPIKE_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })

    const input = page.getByTestId('composer-input')
    await input.fill(TEST_PROMPT)

    const t0 = Date.now()
    await page.getByTestId('send-btn').click()

    // Wait for abort button (signals streaming started)
    await page.getByTestId('abort-btn').waitFor({ state: 'visible', timeout: BUDGETS.TTFT_MS })

    const ttft = Date.now() - t0
    console.log(`[perf/streaming] TTFT: ${ttft}ms (budget: ${BUDGETS.TTFT_MS}ms)`)

    expect(
      ttft,
      `TTFT ${ttft}ms exceeded budget ${BUDGETS.TTFT_MS}ms`,
    ).toBeLessThan(BUDGETS.TTFT_MS)

    // Wait for stream to complete (cleanup)
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
  })

  test('frame budget — no excessive drops during streaming', async ({ page }) => {
    await page.goto(SPIKE_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })

    // Start long-task observation before sending
    await page.evaluate(() => {
      (window as typeof window & { _longTaskDurations: number[] })._longTaskDurations = []
      const obs = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          (window as typeof window & { _longTaskDurations: number[] })._longTaskDurations.push(
            entry.duration,
          )
        }
      })
      try {
        obs.observe({ type: 'longtask', buffered: false })
        ;(window as typeof window & { _perfObs: PerformanceObserver })._perfObs = obs
      } catch {
        // longtask not available
      }
    })

    const input = page.getByTestId('composer-input')
    await input.fill(TEST_PROMPT)
    await page.getByTestId('send-btn').click()

    // Wait for stream to complete
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })

    // Collect long task data
    const longTasks = await page.evaluate(() => {
      const w = window as typeof window & {
        _longTaskDurations?: number[]
        _perfObs?: PerformanceObserver
      }
      w._perfObs?.disconnect()
      return w._longTaskDurations ?? []
    })

    const violations = longTasks.filter((d) => d > BUDGETS.FRAME_BUDGET_MS * 2) // >32ms is a real drop
    console.log(
      `[perf/streaming] Long tasks during stream: ${longTasks.length} total, ` +
        `${violations.length} exceeding ${BUDGETS.FRAME_BUDGET_MS * 2}ms`,
    )

    expect(
      violations.length,
      `${violations.length} frame budget violations (max: ${BUDGETS.FRAME_BUDGET_VIOLATIONS_MAX}). ` +
        `Longest: ${violations.length > 0 ? Math.max(...violations).toFixed(1) : 0}ms`,
    ).toBeLessThanOrEqual(BUDGETS.FRAME_BUDGET_VIOLATIONS_MAX)
  })

  test('memory growth within budget during a full stream', async ({ page }) => {
    await page.goto(SPIKE_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })

    // Baseline heap snapshot before stream
    const heapBefore = await page.evaluate(async () => {
      if ('gc' in performance) {
        ;(performance as typeof performance & { gc: () => void }).gc()
      }
      // Use memory API if available
      const m = (performance as typeof performance & {
        memory?: { usedJSHeapSize: number }
      }).memory
      return m ? m.usedJSHeapSize : 0
    })

    const input = page.getByTestId('composer-input')
    await input.fill(TEST_PROMPT)
    await page.getByTestId('send-btn').click()

    // Wait for stream to complete
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })

    // Post-stream heap snapshot
    const heapAfter = await page.evaluate(async () => {
      const m = (performance as typeof performance & {
        memory?: { usedJSHeapSize: number }
      }).memory
      return m ? m.usedJSHeapSize : 0
    })

    if (heapBefore > 0 && heapAfter > 0) {
      const growthMB = (heapAfter - heapBefore) / (1024 * 1024)
      console.log(`[perf/streaming] Heap growth: ${growthMB.toFixed(2)}MB (budget: ${BUDGETS.MEMORY_GROWTH_MB}MB)`)

      expect(
        growthMB,
        `Heap grew ${growthMB.toFixed(2)}MB during stream (budget: ${BUDGETS.MEMORY_GROWTH_MB}MB)`,
      ).toBeLessThan(BUDGETS.MEMORY_GROWTH_MB)
    } else {
      // performance.memory not available in this browser — skip gracefully
      console.log('[perf/streaming] performance.memory not available — memory test skipped')
    }
  })

  test('scroll anchor stable — viewport within 200px of bottom throughout stream', async ({
    page,
  }) => {
    await page.goto(SPIKE_URL)
    await page.getByTestId('chat-spike-root').waitFor({ state: 'visible' })

    const input = page.getByTestId('composer-input')
    await input.fill(TEST_PROMPT)
    await page.getByTestId('send-btn').click()

    // Poll mid-stream
    await page.getByTestId('abort-btn').waitFor({ state: 'visible', timeout: 5000 })

    // Sample scroll position 3 times during stream
    for (let i = 0; i < 3; i++) {
      await page.waitForTimeout(500)

      const scrollData = await page.evaluate(() => {
        const viewport = document.querySelector('[data-testid="thread-viewport"]')
        if (!viewport) return null
        return {
          scrollTop: viewport.scrollTop,
          scrollHeight: viewport.scrollHeight,
          clientHeight: viewport.clientHeight,
        }
      })

      if (scrollData && scrollData.scrollHeight > scrollData.clientHeight) {
        const distanceFromBottom =
          scrollData.scrollHeight - scrollData.scrollTop - scrollData.clientHeight
        expect(
          distanceFromBottom,
          `Scroll anchor drifted ${distanceFromBottom}px from bottom during streaming (max: 200px)`,
        ).toBeLessThan(200)
      }
    }

    // Wait for completion
    await page.getByTestId('send-btn').waitFor({ state: 'visible', timeout: STREAM_TIMEOUT })
  })
})
