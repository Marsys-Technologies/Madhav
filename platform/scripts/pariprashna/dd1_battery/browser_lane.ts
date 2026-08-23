/**
 * dd1_battery/browser_lane.ts — the LIVE-SURFACE lane of the DD-1 battery.
 *
 * MACHINE PROXY — NOT AC-15 (metrics.ts PROXY_LABEL).
 *
 * Charter §10.1's binding difference from everything already in this repo:
 * this lane runs against the **post-flip live default surface, not a fixture**.
 * The repo's existing gate battery (tests/pariprashna/gates/*.spec.ts) drives
 * a standalone test-only harness page (tests/pariprashna/harness/public/
 * index.html) served by the replay server — an excellent fixture suite, and it
 * is included in this battery as the EDGE lane, but it is not the shipped
 * React surface and cannot answer "does the live default surface behave".
 * This lane opens a real browser against the real route with a real
 * authenticated session and drives a real turn.
 *
 * DEVICE EMULATION (charter §10.1 requirement 3): 390x844 via Playwright's
 * isMobile/hasTouch context options, which Chromium implements through CDP
 * `Emulation.setDeviceMetricsOverride(mobile: true)` + touch emulation — a
 * real device-metrics override, not a resized desktop viewport. The M8-emu
 * check reads the metrics back from inside the page and FAILS if the override
 * did not actually take.
 *
 * THE SELECTOR-PRESENCE GATE (§N.8, the important part):
 * Every counter this lane reads is zero when the selectors match nothing. A
 * detector pointed at a DOM that never contains its target reports a VACUOUS
 * green. So each metric declares which selectors it depends on, and if those
 * selectors were never observed during the run, the metric reports
 * NOT_IMPLEMENTED ("selector never observed on the live surface"), never PASS.
 */
import { chromium, devices, type Browser, type BrowserContext, type Page } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { recorderSource, SELECTORS, type Dd1Recording } from './instrumentation'
import type { CheckOutcome } from './prose_checks'
import type { RedProofEntry } from './red_proof'

export interface BrowserLaneOptions {
  baseUrl: string
  chartId: string
  cookie: string
  question: string
  headless: boolean
  /** ms to allow one live turn to settle. */
  turnTimeoutMs: number
  log: (s: string) => void
}

export interface BrowserLaneResult {
  available: boolean
  unavailableReason: string | null
  checks: Record<string, CheckOutcome>
  recording: Dd1Recording | null
  deviceReadback: Record<string, unknown> | null
  observedTurnStatus: string | null
}

const MOBILE_PROFILE = {
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 3,
  isMobile: true,
  hasTouch: true,
  userAgent: devices['Pixel 5'].userAgent,
}

function cookieDomain(baseUrl: string): string {
  return new URL(baseUrl).hostname
}

async function openContext(browser: Browser, opts: BrowserLaneOptions, mobile: boolean): Promise<BrowserContext> {
  const ctx = await browser.newContext(
    mobile ? MOBILE_PROFILE : { viewport: { width: 1440, height: 900 } },
  )
  await ctx.addCookies([
    {
      name: '__session',
      value: opts.cookie,
      domain: cookieDomain(opts.baseUrl),
      path: '/',
      httpOnly: true,
      secure: opts.baseUrl.startsWith('https'),
      sameSite: 'Lax',
    },
  ])
  await ctx.addInitScript(recorderSource())
  return ctx
}

async function readDeviceMetrics(page: Page): Promise<Record<string, unknown>> {
  return page.evaluate(() => ({
    innerWidth: window.innerWidth,
    innerHeight: window.innerHeight,
    devicePixelRatio: window.devicePixelRatio,
    maxTouchPoints: navigator.maxTouchPoints,
    hasOntouchstart: 'ontouchstart' in window,
    pointerCoarse: window.matchMedia('(pointer: coarse)').matches,
    userAgent: navigator.userAgent,
  }))
}

async function axeScan(page: Page, stateLabel: string): Promise<{ label: string; violations: Array<{ id: string; impact: string | null; nodes: number; help: string }> }> {
  const results = await new AxeBuilder({ page }).analyze()
  return {
    label: stateLabel,
    violations: results.violations
      .filter((v) => v.impact === 'critical' || v.impact === 'serious')
      .map((v) => ({ id: v.id, impact: v.impact ?? null, nodes: v.nodes.length, help: v.help })),
  }
}

function outcome(ok: boolean, findings: string[], detail: Record<string, unknown>): CheckOutcome {
  return { ok, findings, detail }
}

/**
 * Selector-presence gate. Returns a NOT-IMPLEMENTED-shaped outcome when the
 * metric's evidence never existed on the surface — a metric that "passed"
 * because its selector matched nothing is exactly the §N.8 defect.
 */
function selectorGate(
  rec: Dd1Recording,
  needed: Array<keyof Dd1Recording['selectorsSeen']>,
): string | null {
  const missing = needed.filter((k) => (rec.selectorsSeen[k] ?? 0) === 0)
  return missing.length
    ? `selector(s) never observed on the live surface: ${missing.map((k) => `${k} (${SELECTORS[k as keyof typeof SELECTORS]})`).join(', ')} — ` +
        'this metric has no evidence and must not report PASS'
    : null
}

/** Drive one live turn under mobile emulation and evaluate M1/M2/M3/M6/M8-emu/M9. */
export async function runBrowserLane(opts: BrowserLaneOptions): Promise<BrowserLaneResult> {
  const empty: BrowserLaneResult = {
    available: false,
    unavailableReason: null,
    checks: {},
    recording: null,
    deviceReadback: null,
    observedTurnStatus: null,
  }

  let browser: Browser | null = null
  try {
    browser = await chromium.launch({ headless: opts.headless })
  } catch (err) {
    return { ...empty, unavailableReason: `chromium failed to launch: ${String(err)}` }
  }

  try {
    const ctx = await openContext(browser, opts, true)
    const page = await ctx.newPage()
    const url = `${opts.baseUrl.replace(/\/$/, '')}/clients/${opts.chartId}/pariprashna`
    opts.log(`[browser] navigating to ${url}`)

    const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60_000 })
    const finalUrl = page.url()
    if (!finalUrl.includes('/pariprashna')) {
      return {
        ...empty,
        unavailableReason:
          `the route redirected away from the Paripraśna surface (landed on ${finalUrl}, ` +
          `HTTP ${resp?.status() ?? '?'}). Post-flip this must be the default surface; ` +
          'pre-flip PARIPRASHNA_ENABLED=false redirects to /consult by design.',
      }
    }

    const deviceReadback = await readDeviceMetrics(page)

    // Composer must exist or this is not the surface under test.
    try {
      await page.waitForSelector(SELECTORS.composer, { timeout: 30_000 })
    } catch {
      return {
        ...empty,
        deviceReadback,
        unavailableReason: `the composer (${SELECTORS.composer}) never appeared — the live surface did not render`,
      }
    }

    const axeStates: Array<Awaited<ReturnType<typeof axeScan>>> = []
    axeStates.push(await axeScan(page, 'idle'))

    opts.log(`[browser] submitting: ${opts.question}`)
    await page.fill(SELECTORS.composer, opts.question)
    await page.click(SELECTORS.send)

    // Streaming state: scan once the band or a tail exists.
    try {
      await page.waitForSelector(`${SELECTORS.band}, ${SELECTORS.tail}`, { timeout: 30_000 })
      axeStates.push(await axeScan(page, 'streaming'))
    } catch {
      opts.log('[browser] WARNING: neither the working band nor a tail appeared within 30s')
    }

    // Settled: a turn whose data-turn-status reaches settled (or errored).
    let observedTurnStatus: string | null = null
    try {
      await page.waitForFunction(
        (sel) => {
          const turns = Array.from(document.querySelectorAll(sel))
          return turns.some((t) => ['settled', 'errored', 'interrupted'].includes(t.getAttribute('data-turn-status') ?? ''))
        },
        SELECTORS.turn,
        { timeout: opts.turnTimeoutMs },
      )
      observedTurnStatus = await page.evaluate((sel) => {
        const turns = Array.from(document.querySelectorAll(sel))
        const t = turns.reverse().find((x) => ['settled', 'errored', 'interrupted'].includes(x.getAttribute('data-turn-status') ?? ''))
        return t?.getAttribute('data-turn-status') ?? null
      }, SELECTORS.turn)
      axeStates.push(await axeScan(page, `settled(${observedTurnStatus})`))
    } catch {
      opts.log(`[browser] WARNING: no turn reached a terminal status within ${opts.turnTimeoutMs}ms`)
    }

    const rec = (await page.evaluate(() => (window as unknown as { __dd1: Dd1Recording }).__dd1)) as Dd1Recording

    const checks: Record<string, CheckOutcome> = {}

    // ── M1 ────────────────────────────────────────────────────────────────
    {
      const gate = selectorGate(rec, ['settled'])
      checks.M1 = gate
        ? outcome(false, [`M1 NOT MEASURED — ${gate}`], { not_measured: true, selectorsSeen: rec.selectorsSeen })
        : outcome(rec.settledShiftCount === 0, rec.settledShiftDetails.map((d) => `M1 settled block ${d.id} drifted ${d.drift}px at t=${d.at}ms`), {
            settledShiftCount: rec.settledShiftCount, frames: rec.frames,
          })
      if (gate) checks.M1.detail.gate_reason = gate
    }

    // ── M2 ────────────────────────────────────────────────────────────────
    {
      const gate = selectorGate(rec, ['caret', 'tail'])
      checks.M2 = gate
        ? outcome(false, [`M2 NOT MEASURED — ${gate}`], { not_measured: true, selectorsSeen: rec.selectorsSeen })
        : outcome(rec.caretViolations.length === 0, rec.caretViolations.map((v) => `M2 caret orphaned at t=${v.at}ms: ${v.reason}`), {
            caretChecks: rec.caretChecks, violations: rec.caretViolations.length,
          })
      if (gate) checks.M2.detail.gate_reason = gate
    }

    // ── M3 ────────────────────────────────────────────────────────────────
    {
      const gate = selectorGate(rec, ['band'])
      if (gate) {
        checks.M3 = outcome(false, [`M3 NOT MEASURED — ${gate}`], { not_measured: true, gate_reason: gate })
      } else if (rec.submitAt === null || rec.bandFirstSeenAt === null) {
        checks.M3 = outcome(false, ['M3 NOT MEASURED — submit or working-region timestamp missing'], {
          not_measured: true, submitAt: rec.submitAt, bandFirstSeenAt: rec.bandFirstSeenAt,
        })
      } else {
        const ttfs = rec.bandFirstSeenAt - rec.submitAt
        checks.M3 = outcome(ttfs < 300, ttfs < 300 ? [] : [`M3 TTFS ${Math.round(ttfs)}ms >= the 300ms threshold`], {
          ttfs_ms: Math.round(ttfs),
        })
      }
    }

    // ── M6 (DOM half) ─────────────────────────────────────────────────────
    {
      const gate = selectorGate(rec, ['settled'])
      const findings = [
        ...rec.domMutationDetails.map((d) => `M6 committed block ${d.id} mutated at t=${d.at}ms: ${JSON.stringify(d.before.slice(0, 80))} → ${JSON.stringify(d.after.slice(0, 80))}`),
        ...rec.chipGeometryChanges.map((c) => `M6 citation chip ${c.id} changed geometry at t=${c.at}ms: ${c.before} → ${c.after}`),
      ]
      checks.M6 = gate
        ? outcome(false, [`M6 NOT MEASURED — ${gate}`], { not_measured: true, gate_reason: gate, selectorsSeen: rec.selectorsSeen })
        : outcome(findings.length === 0, findings, {
            committed_block_mutations: rec.domMutationCount,
            chip_geometry_changes: rec.chipGeometryChanges.length,
            chips_seen: rec.selectorsSeen.chip,
          })
    }

    // ── M8-emu ────────────────────────────────────────────────────────────
    {
      const findings: string[] = []
      if (deviceReadback.innerWidth !== 390) findings.push(`M8-emu innerWidth=${deviceReadback.innerWidth}, expected 390`)
      if (deviceReadback.innerHeight !== 844) findings.push(`M8-emu innerHeight=${deviceReadback.innerHeight}, expected 844`)
      if (Number(deviceReadback.devicePixelRatio) <= 1) findings.push(`M8-emu devicePixelRatio=${deviceReadback.devicePixelRatio}, expected > 1 (a resized desktop viewport would read 1)`)
      if (!deviceReadback.hasOntouchstart) findings.push('M8-emu "ontouchstart" in window === false — touch emulation did not take')
      if (!deviceReadback.pointerCoarse) findings.push('M8-emu (pointer: coarse) === false — mobile device metrics override did not take')
      checks['M8-emu'] = outcome(findings.length === 0, findings, deviceReadback)
    }

    // ── M9 ────────────────────────────────────────────────────────────────
    {
      const findings: string[] = []
      for (const s of axeStates) {
        for (const v of s.violations) {
          findings.push(`M9 axe ${v.impact} violation "${v.id}" in state ${s.label} on ${v.nodes} node(s): ${v.help}`)
        }
      }
      checks.M9 = axeStates.length === 0
        ? outcome(false, ['M9 NOT MEASURED — no state was scanned'], { not_measured: true })
        : outcome(findings.length === 0, findings, { states_scanned: axeStates.map((s) => s.label) })
    }

    await ctx.close()
    return { available: true, unavailableReason: null, checks, recording: rec, deviceReadback, observedTurnStatus }
  } catch (err) {
    return { ...empty, unavailableReason: `browser lane threw: ${String(err)}` }
  } finally {
    await browser?.close().catch(() => {})
  }
}

// ═══════════════════════════════════════════════════════════════════════════
//  BROWSER-LANE RED PROOFS
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Red-proving a DOM detector needs a DOM that can be deliberately broken.
 * Breaking the LIVE surface is not an option (it is production), so the
 * browser-lane detectors are red-proven against a SYNTHETIC page that carries
 * the PRODUCTION selectors — the same `recorderSource()` runs against it, so
 * the code path under proof is byte-identical to the one that runs live.
 *
 * WHAT THIS PROVES AND WHAT IT DOES NOT — stated plainly because the
 * difference is the whole §N.8 question:
 *   PROVES:      the detector logic reports FAIL when the violation is
 *                present and PASS when it is not.
 *   DOES NOT:    prove the selectors match the live DOM. That second half is
 *                covered by the separate selector-presence gate in
 *                `runBrowserLane` above, which refuses PASS for any metric
 *                whose selector was never observed during the live run.
 */
// NOTE (bug found + fixed during the P4 overnight build): this fixture must
// be genuinely axe-clean and must genuinely read back as a 390x844 mobile
// viewport, or the m9_axe / m8_device_emulation "clean counterpart" proofs
// fail for a reason that has nothing to do with the detector under test — see
// the finding recorded in the PR description. <title>, <html lang>, a
// <meta name="viewport"> (without it Chromium lays out an unstyled page at
// its 980px desktop-compat default width even under isMobile emulation, so
// window.innerWidth reads 980, not 390), and a real <label> for the composer
// are all load-bearing for that, not decoration.
const SYNTH_PAGE = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>DD-1 battery synthetic fixture</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;font:16px/1.5 sans-serif}#col{padding:12px}
.pp-band{height:24px;background:#eee}
[data-pp-caret]{display:inline-block;width:2px;height:1em;background:#000;vertical-align:text-bottom}
[data-testid="pp-citation-chip"]{display:inline-block;min-width:18px;text-align:center;border:1px solid #999;border-radius:3px}
</style></head><body>
<div id="col">
  <div id="blocks">
    <div data-committed="true" data-block-kind="paragraph"><p>The chart is distinctly more likely than not to favour a change of role <span data-testid="pp-citation-chip">1</span>.</p></div>
    <div data-committed="true" data-block-kind="paragraph"><p>The tenth house is tenanted rather than merely aspected.</p></div>
  </div>
  <p data-testid="pp-tail" data-pp-tail-live="true">Saturn is strong here<span data-pp-caret></span></p>
  <label for="dd1-composer">Ask the chart</label>
  <textarea id="dd1-composer" data-testid="pp-composer-textarea"></textarea>
  <button data-testid="pp-composer-send">Send</button>
</div></body></html>`

export interface BrowserRedProofOptions {
  headless: boolean
  log: (s: string) => void
}

async function withSynthPage<T>(
  headless: boolean,
  mobile: boolean,
  fn: (page: Page) => Promise<T>,
): Promise<T> {
  const browser = await chromium.launch({ headless })
  try {
    const ctx = await browser.newContext(mobile ? MOBILE_PROFILE : { viewport: { width: 1440, height: 900 } })
    await ctx.addInitScript(recorderSource())
    const page = await ctx.newPage()
    // NOTE (bug found + fixed during the P4 overnight build): `page.setContent()`
    // internally does `document.open()/write()/close()` on an already-loaded
    // `about:blank` document, which REPLACES the Document object per HTML spec.
    // `addInitScript`'s listeners (e.g. the M3 submit-click hook in
    // instrumentation.ts, registered via `document.addEventListener`) get bound
    // to the pre-replacement Document and are silently orphaned — the click
    // still happens, but the listener never sees it, so `rec.submitAt` stays
    // null forever (this is why m3_ttfs's "clean" red-proof counterpart failed:
    // it was genuinely unmeasurable, not a detector bug). The rAF-driven
    // polling checks (M1/M2/M6) were unaffected because they re-resolve the
    // live global `document` on every frame rather than binding to one Document
    // instance. Mobile-emulation readback (M8-emu's `"ontouchstart" in window`)
    // has the same failure mode. A real navigation avoids it entirely — there
    // is exactly one Document, and it is the one addInitScript's listeners are
    // bound to — so this loads the fixture via `page.goto('data:…')` instead of
    // `page.setContent()`, matching how the real browser lane above navigates.
    await page.goto(`data:text/html,${encodeURIComponent(SYNTH_PAGE)}`)
    const out = await fn(page)
    await ctx.close()
    return out
  } finally {
    await browser.close().catch(() => {})
  }
}

/**
 * Advance `n` animation frames inside the page.
 *
 * IMPLEMENTATION NOTE (bug found + fixed during the P4 overnight build): the
 * obvious recursive form — a `const step = () => … requestAnimationFrame(step)`
 * closure passed to `page.evaluate` — breaks under `tsx`'s esbuild transform,
 * which injects a `__name(step, "step")` call to preserve the function's
 * `.name` for stack traces. Playwright serializes the callback via
 * `Function.prototype.toString()` and evaluates the source INSIDE the page,
 * where `__name` does not exist, so every call threw
 * `ReferenceError: __name is not defined` before a single browser-lane red
 * proof could run. The fix is structural, not a workaround: never bind an
 * inner function to a name inside a closure that will be serialized into the
 * page — one un-named `page.evaluate` call per frame, awaited from Node,
 * carries no named binding for esbuild to wrap.
 */
async function frames(page: Page, n: number): Promise<void> {
  for (let i = 0; i < n; i++) {
    await page.evaluate(() => new Promise<void>((resolve) => requestAnimationFrame(() => resolve())))
  }
}

async function read(page: Page): Promise<Dd1Recording> {
  return page.evaluate(() => (window as unknown as { __dd1: Dd1Recording }).__dd1)
}

export async function runBrowserRedProof(opts: BrowserRedProofOptions): Promise<Record<string, RedProofEntry>> {
  const out: Record<string, RedProofEntry> = {}
  const { log } = opts

  const record = (key: string, check: string, red: { fired: boolean; findings: string[] }, green: { clean: boolean; findings: string[] }, note?: string) => {
    log('')
    log(`── RED PROOF · ${check} (${key}) ─────────────────────────`)
    log(`   observed on the seeded violation: ${red.fired ? 'FAIL  ← detector fired, as required' : 'PASS  ← DETECTOR DID NOT FIRE'}`)
    for (const f of red.findings) log(`     · ${f}`)
    log(`   observed on the clean counterpart: ${green.clean ? 'PASS  ← clean, as required' : 'FAIL  ← fires on clean input too'}`)
    for (const f of green.findings) log(`     · ${f}`)
    out[key] = { check, red_fired: red.fired, red_findings: red.findings, green_clean: green.clean, green_findings: green.findings, note }
  }

  // ── m1_settled_shift ──────────────────────────────────────────────────
  {
    const red = await withSynthPage(opts.headless, true, async (page) => {
      await frames(page, 4)
      await page.evaluate(() => {
        const spacer = document.createElement('div')
        spacer.style.height = '120px'
        document.getElementById('blocks')!.prepend(spacer)
      })
      await frames(page, 6)
      const rec = await read(page)
      return { fired: rec.settledShiftCount > 0, findings: rec.settledShiftDetails.map((d) => `settled block ${d.id} drifted ${d.drift}px at t=${d.at}ms`) }
    })
    const green = await withSynthPage(opts.headless, true, async (page) => {
      await frames(page, 10)
      const rec = await read(page)
      return { clean: rec.settledShiftCount === 0, findings: rec.settledShiftDetails.map((d) => `settled block ${d.id} drifted ${d.drift}px`) }
    })
    record('m1_settled_shift', 'M1', red, green)
  }

  // ── m2_caret_orphan ───────────────────────────────────────────────────
  {
    const red = await withSynthPage(opts.headless, true, async (page) => {
      await frames(page, 4)
      await page.evaluate(() => {
        // Detach the caret from the tail's last text node — the exact bug
        // AC-2 names ("caret rendered detached ... on its own line").
        const caret = document.querySelector('[data-pp-caret]')!
        document.body.appendChild(caret)
      })
      await frames(page, 6)
      const rec = await read(page)
      return { fired: rec.caretViolations.length > 0, findings: rec.caretViolations.map((v) => `t=${v.at}ms: ${v.reason}`) }
    })
    const green = await withSynthPage(opts.headless, true, async (page) => {
      await frames(page, 10)
      const rec = await read(page)
      return { clean: rec.caretViolations.length === 0, findings: rec.caretViolations.map((v) => `t=${v.at}ms: ${v.reason}`) }
    })
    record('m2_caret_orphan', 'M2', red, green)
  }

  // ── m3_ttfs ───────────────────────────────────────────────────────────
  {
    // RED: click send on a page whose working band NEVER mounts — the check
    // must report "not measured / FAIL", not a silent pass.
    const red = await withSynthPage(opts.headless, true, async (page) => {
      await page.click(SELECTORS.send)
      await frames(page, 8)
      const rec = await read(page)
      const measurable = rec.submitAt !== null && rec.bandFirstSeenAt !== null
      return {
        fired: !measurable || rec.bandFirstSeenAt! - rec.submitAt! >= 300,
        findings: [`submitAt=${rec.submitAt === null ? 'null' : Math.round(rec.submitAt)}, bandFirstSeenAt=${rec.bandFirstSeenAt === null ? 'null (working region never mounted)' : Math.round(rec.bandFirstSeenAt)} — TTFS unmeasurable ⇒ the check cannot report PASS`],
      }
    })
    // GREEN: the band mounts within one frame of the click.
    const green = await withSynthPage(opts.headless, true, async (page) => {
      await page.evaluate(() => {
        document.querySelector('[data-testid="pp-composer-send"]')!.addEventListener('click', () => {
          const b = document.createElement('div')
          b.className = 'pp-band'
          b.textContent = 'CONSULTING THE CHART · 0s'
          document.getElementById('col')!.prepend(b)
        })
      })
      await page.click(SELECTORS.send)
      await frames(page, 8)
      const rec = await read(page)
      const ttfs = rec.submitAt !== null && rec.bandFirstSeenAt !== null ? rec.bandFirstSeenAt - rec.submitAt : null
      return {
        clean: ttfs !== null && ttfs < 300,
        findings: [`TTFS = ${ttfs === null ? 'unmeasurable' : Math.round(ttfs) + 'ms'} (threshold 300ms)`],
      }
    })
    record('m3_ttfs', 'M3', red, green)
  }

  // ── m6_transmute ──────────────────────────────────────────────────────
  {
    const red = await withSynthPage(opts.headless, true, async (page) => {
      await frames(page, 4)
      await page.evaluate(() => {
        // A committed block whose serialized DOM changes after commit, and a
        // chip that grows from plain-text width to badge width.
        const blocks = document.querySelectorAll('[data-committed="true"]')
        blocks[0].querySelector('p')!.innerHTML =
          'The chart is <strong>close to unequivocal</strong> here <span data-testid="pp-citation-chip" style="min-width:64px">1</span>.'
      })
      await frames(page, 6)
      const rec = await read(page)
      return {
        fired: rec.domMutationCount > 0 || rec.chipGeometryChanges.length > 0,
        findings: [
          ...rec.domMutationDetails.map((d) => `committed block ${d.id} mutated at t=${d.at}ms`),
          ...rec.chipGeometryChanges.map((c) => `chip ${c.id} geometry ${c.before} → ${c.after}`),
        ],
      }
    })
    const green = await withSynthPage(opts.headless, true, async (page) => {
      await frames(page, 10)
      const rec = await read(page)
      return {
        clean: rec.domMutationCount === 0 && rec.chipGeometryChanges.length === 0,
        findings: rec.domMutationDetails.map((d) => `committed block ${d.id} mutated at t=${d.at}ms`),
      }
    })
    record('m6_transmute', 'M6', red, green)
  }

  // ── m8_device_emulation ───────────────────────────────────────────────
  {
    const evaluate = (m: Record<string, unknown>): string[] => {
      const f: string[] = []
      if (m.innerWidth !== 390) f.push(`innerWidth=${m.innerWidth}, expected 390`)
      if (m.innerHeight !== 844) f.push(`innerHeight=${m.innerHeight}, expected 844`)
      if (Number(m.devicePixelRatio) <= 1) f.push(`devicePixelRatio=${m.devicePixelRatio}, expected > 1`)
      if (!m.hasOntouchstart) f.push('"ontouchstart" in window === false')
      if (!m.pointerCoarse) f.push('(pointer: coarse) === false')
      return f
    }
    // RED: a plain desktop context — a "resized desktop viewport" is exactly
    // what charter §10.1 requirement 3 forbids, so the check must reject it.
    const redMetrics = await withSynthPage(opts.headless, false, async (page) => {
      await page.setViewportSize({ width: 390, height: 844 }) // resized desktop, NOT device emulation
      return readDeviceMetrics(page)
    })
    const redFindings = evaluate(redMetrics)
    const greenMetrics = await withSynthPage(opts.headless, true, async (page) => readDeviceMetrics(page))
    const greenFindings = evaluate(greenMetrics)
    record(
      'm8_device_emulation',
      'M8-emu',
      { fired: redFindings.length > 0, findings: redFindings.map((f) => `desktop viewport resized to 390x844: ${f}`) },
      { clean: greenFindings.length === 0, findings: greenFindings },
      'red input is a DESKTOP context resized to 390x844 — the exact substitution the charter forbids',
    )
  }

  // ── m9_axe ────────────────────────────────────────────────────────────
  {
    const red = await withSynthPage(opts.headless, true, async (page) => {
      await page.evaluate(() => {
        const img = document.createElement('img')
        img.src =
          'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        document.body.appendChild(img) // no alt → axe "image-alt" (critical)
        const btn = document.createElement('button')
        document.body.appendChild(btn) // no accessible name → axe "button-name" (critical)
      })
      const scan = await axeScan(page, 'red')
      return {
        fired: scan.violations.length > 0,
        findings: scan.violations.map((v) => `${v.impact} "${v.id}" on ${v.nodes} node(s): ${v.help}`),
      }
    })
    const green = await withSynthPage(opts.headless, true, async (page) => {
      const scan = await axeScan(page, 'green')
      return {
        clean: scan.violations.length === 0,
        findings: scan.violations.map((v) => `${v.impact} "${v.id}": ${v.help}`),
      }
    })
    record('m9_axe', 'M9', red, green)
  }

  return out
}
