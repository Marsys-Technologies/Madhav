import path from 'node:path'
import fs from 'node:fs'
import os from 'node:os'
import { fileURLToPath } from 'node:url'
import { createRequire } from 'node:module'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const REPO_PLATFORM = path.resolve(__dirname, '../../..')
process.chdir(REPO_PLATFORM)

const require = createRequire(path.join(REPO_PLATFORM, 'package.json'))
const { createServer } = require('vite')
const react = require('@vitejs/plugin-react').default
const { chromium } = require('playwright-core')

function resolveChromiumExecutablePath() {
  if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH) {
    return process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH
  }
  const cacheDir = path.join(os.homedir(), 'Library', 'Caches', 'ms-playwright')
  if (!fs.existsSync(cacheDir)) return undefined
  const entries = fs.readdirSync(cacheDir).sort().reverse()
  for (const entry of entries) {
    if (entry.startsWith('chromium_headless_shell-')) {
      const candidate = path.join(cacheDir, entry, 'chrome-headless-shell-mac-arm64', 'chrome-headless-shell')
      if (fs.existsSync(candidate)) return candidate
    }
    if (entry.startsWith('chromium-')) {
      const candidate = path.join(
        cacheDir,
        entry,
        'chrome-mac-arm64',
        'Google Chrome for Testing.app',
        'Contents',
        'MacOS',
        'Google Chrome for Testing',
      )
      if (fs.existsSync(candidate)) return candidate
    }
  }
  return undefined
}

function assert(cond, message) {
  if (!cond) {
    throw new Error(`ASSERTION FAILED: ${message}`)
  }
}

async function main() {
  const indexHtml = fs
    .readFileSync(path.join(__dirname, 'index.html'), 'utf8')
    .replace('/main.tsx', `/@fs${path.join(__dirname, 'main.tsx')}`)

  const server = await createServer({
    configFile: false,
    root: REPO_PLATFORM,
    css: {
      postcss: path.join(REPO_PLATFORM, 'postcss.config.mjs'),
    },
    plugins: [
      react(),
      {
        name: 'consult-viewport-harness',
        configureServer(srv) {
          srv.middlewares.use(async (req, res, next) => {
            if (req.url === '/' || req.url?.startsWith('/?')) {
              const transformed = await srv.transformIndexHtml(req.url, indexHtml)
              res.setHeader('Content-Type', 'text/html')
              res.end(transformed)
              return
            }
            next()
          })
        },
        async resolveId(source, importer, options) {
          if (
            importer &&
            importer.startsWith(__dirname) &&
            !source.startsWith('.') &&
            !source.startsWith('/') &&
            !source.startsWith('\0')
          ) {
            return this.resolve(source, path.join(REPO_PLATFORM, 'src', '__virtual__.ts'), {
              ...options,
              skipSelf: true,
            })
          }
          return null
        },
      },
    ],
    define: {
      'process.env': JSON.stringify({
        NEXT_PUBLIC_MARSYS_FLAG_R11B_LOOK_AND_FEEL: 'false',
        NEXT_PUBLIC_MARSYS_FLAG_R10_SCROLL_DISCIPLINE: 'false',
        NEXT_PUBLIC_MARSYS_FLAG_R10_EDIT_WHILE_STREAMING: 'false',
        NEXT_PUBLIC_MARSYS_FLAG_R9_PROJECTS: 'false',
        NEXT_PUBLIC_MARSYS_FLAG_R9_PERSONAS: 'false',
        NEXT_PUBLIC_MARSYS_ANTHROPIC_HIDDEN: 'true',
      }),
    },
    resolve: {
      alias: {
        '@/lib/firebase/client': path.join(__dirname, 'stubs.tsx'),
        '@': path.join(REPO_PLATFORM, 'src'),
        'next/link': path.join(__dirname, 'stubs.tsx'),
        'next/navigation': path.join(__dirname, 'stubs.tsx'),
        'next/dynamic': path.join(__dirname, 'stubs.tsx'),
      },
    },
    server: {
      host: '127.0.0.1',
      port: 0,
      fs: {
        allow: [REPO_PLATFORM, __dirname],
      },
    },
  })

  await server.listen()
  const address = server.httpServer?.address()
  const port = typeof address === 'object' && address ? address.port : 3199
  const baseUrl = `http://127.0.0.1:${port}`

  const executablePath = resolveChromiumExecutablePath()
  const browser = await chromium.launch({
    ...(executablePath ? { executablePath } : {}),
    headless: true,
  })

  try {
    const completeReadiness = {
      chart_id: 'chart-1',
      build_status: 'complete',
      ready: ['A3', 'A7', 'A8', 'A10', 'A15'],
      missing: [],
      partial_count: 5,
      total_count: 5,
    }
    const partialReadiness = {
      chart_id: 'chart-1',
      build_status: 'partial',
      ready: ['A3', 'A7'],
      missing: ['A8', 'A10'],
      partial_count: 2,
      total_count: 4,
    }

    const consultScenarios = [
      { name: 'saved-portal-complete', url: `${baseUrl}/?mode=saved-portal&pathname=/clients/chart-1/consult/conv-1`, readiness: completeReadiness, hasMessages: true },
      { name: 'saved-portal-partial', url: `${baseUrl}/?mode=saved-portal&pathname=/clients/chart-1/consult/conv-1`, readiness: partialReadiness, hasMessages: true },
      { name: 'fresh-portal-complete', url: `${baseUrl}/?mode=fresh-portal&pathname=/clients/chart-1/consult`, readiness: completeReadiness, hasMessages: false },
      { name: 'saved-inline-complete', url: `${baseUrl}/?mode=saved-inline&pathname=/clients/chart-1/consult/conv-1`, readiness: completeReadiness, hasMessages: true },
      { name: 'saved-inline-partial', url: `${baseUrl}/?mode=saved-inline&pathname=/clients/chart-1/consult/conv-1`, readiness: partialReadiness, hasMessages: true },
      { name: 'fresh-inline-complete', url: `${baseUrl}/?mode=fresh-inline&pathname=/clients/chart-1/consult`, readiness: completeReadiness, hasMessages: false },
    ]

    const viewports = [
      { width: 390, height: 844 },
      { width: 390, height: 544 },
      { width: 1280, height: 800 },
    ]

    async function setupPage(vp, readiness) {
      const ctx = await browser.newContext({ viewport: vp })
      const page = await ctx.newPage()
      page.on('pageerror', (e) => {
        throw e
      })
      await page.route('**/api/build/data-readiness**', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(readiness) }),
      )
      await page.route('**/api/conversations**', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ conversations: [] }) }),
      )
      await page.route('**/api/personas**', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ personas: [] }) }),
      )
      return { ctx, page }
    }

    for (const sc of consultScenarios) {
      for (const vp of viewports) {
        const { ctx, page } = await setupPage(vp, sc.readiness)
        await page.goto(sc.url, { waitUntil: 'networkidle' })
        await page.waitForSelector('[data-testid="v2-composer-input"]', { timeout: 10000 })
        await page.waitForTimeout(200)

        const metrics = await page.evaluate(() => {
          const rect = (sel) => {
            const el = document.querySelector(sel)
            if (!el) return null
            const r = el.getBoundingClientRect()
            return {
              top: Math.round(r.top),
              bottom: Math.round(r.bottom),
              left: Math.round(r.left),
              right: Math.round(r.right),
              height: Math.round(r.height),
              width: Math.round(r.width),
              scrollHeight: el.scrollHeight,
              clientHeight: el.clientHeight,
            }
          }
          const sendEl = document.querySelector('[data-testid="v2-send-btn"]')
          const inputEl = document.querySelector('[data-testid="v2-composer-input"]')
          const hitTest = (el) => {
            if (!el) return null
            const r = el.getBoundingClientRect()
            const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)
            return hit ? (el === hit || el.contains(hit) ? 'SELF' : hit.tagName + '.' + hit.className) : 'OUTSIDE'
          }
          const mainEl = document.querySelector('#main-content')
          const cfEl = document.querySelector('[data-testid="chart-page-frame"]')
          return {
            innerHeight: window.innerHeight,
            innerWidth: window.innerWidth,
            docScrollWidth: document.documentElement.scrollWidth,
            docScrollHeight: document.documentElement.scrollHeight,
            mainDisplay: mainEl ? getComputedStyle(mainEl).display : null,
            cfDisplay: cfEl ? getComputedStyle(cfEl).display : null,
            mainContent: rect('#main-content'),
            chartFrame: rect('[data-testid="chart-page-frame"]'),
            shell: rect('[data-testid="v2-chat-shell"]'),
            viewport: rect('[data-testid="v2-thread-viewport"]'),
            bottomBar: rect('[data-testid="v2-bottom-bar"]'),
            composer: rect('[data-testid="v2-composer"]'),
            input: rect('[data-testid="v2-composer-input"]'),
            sendBtn: rect('[data-testid="v2-send-btn"]'),
            inputHit: hitTest(inputEl),
            sendHit: hitTest(sendEl),
            inputRows: inputEl?.getAttribute('rows'),
            sidebarOpen: Boolean(document.querySelector('[data-testid="v2-sidebar"]')),
            hasTraceBtn: Boolean(document.querySelector('[data-testid="v2-trace-btn"]')),
          }
        })

        assert(metrics.docScrollWidth <= vp.width, `${sc.name} ${vp.width}x${vp.height}: docScrollWidth=${metrics.docScrollWidth} > ${vp.width}`)
        assert(metrics.composer && metrics.composer.top >= 0 && metrics.composer.bottom <= vp.height, `${sc.name} ${vp.width}x${vp.height}: composer out of viewport (${JSON.stringify(metrics.composer)})`)
        assert(metrics.input && metrics.input.top >= 0 && metrics.input.bottom <= vp.height, `${sc.name} ${vp.width}x${vp.height}: input out of viewport (${JSON.stringify(metrics.input)})`)
        assert(metrics.sendBtn && metrics.sendBtn.top >= 0 && metrics.sendBtn.bottom <= vp.height, `${sc.name} ${vp.width}x${vp.height}: sendBtn out of viewport (${JSON.stringify(metrics.sendBtn)})`)
        assert(metrics.inputHit === 'SELF', `${sc.name} ${vp.width}x${vp.height}: inputHit=${metrics.inputHit}`)
        assert(metrics.sendHit === 'SELF', `${sc.name} ${vp.width}x${vp.height}: sendHit=${metrics.sendHit}`)
        assert(metrics.viewport && metrics.viewport.height >= 80, `${sc.name} ${vp.width}x${vp.height}: thread viewport collapsed (${JSON.stringify(metrics.viewport)})`)
        assert(metrics.inputRows === '3', `${sc.name} ${vp.width}x${vp.height}: rows=${metrics.inputRows}`)
        assert(!metrics.sidebarOpen, `${sc.name} ${vp.width}x${vp.height}: sidebar should start collapsed`)
        assert(metrics.hasTraceBtn, `${sc.name} ${vp.width}x${vp.height}: missing v2-trace-btn`)
        if (vp.width < 768) {
          assert(metrics.sendBtn.height >= 44 && metrics.sendBtn.width >= 44, `${sc.name} ${vp.width}x${vp.height}: mobile sendBtn touch size ${metrics.sendBtn.width}x${metrics.sendBtn.height} < 44`)
        }

        let scrollCheck = null
        if (sc.hasMessages) {
          scrollCheck = await page.evaluate(async () => {
            const vpEl = document.querySelector('[data-testid="v2-thread-viewport"]')
            const composerBefore = document.querySelector('[data-testid="v2-composer"]').getBoundingClientRect().top
            const beforeTop = vpEl.scrollTop
            vpEl.scrollTop = 0
            vpEl.dispatchEvent(new Event('scroll', { bubbles: true }))
            await new Promise((r) => setTimeout(r, 120))
            const scrollToBottomEl = document.querySelector('[data-testid="v2-scroll-to-bottom"]')
            const sendEl = document.querySelector('[data-testid="v2-send-btn"]')
            const sr = sendEl.getBoundingClientRect()
            const hit = document.elementFromPoint(sr.left + sr.width / 2, sr.top + sr.height / 2)
            return {
              scrollHeight: vpEl.scrollHeight,
              clientHeight: vpEl.clientHeight,
              beforeTop,
              composerMoved: Math.abs(document.querySelector('[data-testid="v2-composer"]').getBoundingClientRect().top - composerBefore),
              scrollToBottomVisible: Boolean(scrollToBottomEl),
              sendHitWhileScrollBtnVisible: hit ? (sendEl === hit || sendEl.contains(hit) ? 'SELF' : hit.className) : 'OUTSIDE',
            }
          })
          assert(scrollCheck.scrollHeight > scrollCheck.clientHeight, `${sc.name} ${vp.width}x${vp.height}: expected thread overflow (${JSON.stringify(scrollCheck)})`)
          assert(scrollCheck.composerMoved <= 1, `${sc.name} ${vp.width}x${vp.height}: composer moved during scroll`)
          assert(scrollCheck.sendHitWhileScrollBtnVisible === 'SELF', `${sc.name} ${vp.width}x${vp.height}: send button occluded while scroll-to-bottom visible`)
        }

        await page.locator('[data-testid="v2-composer-input"]').click()
        await page.keyboard.type('Quick follow-up question')
        await page.keyboard.press('Tab')
        const focusedTestId = await page.evaluate(() => document.activeElement?.getAttribute('data-testid'))
        assert(focusedTestId === 'v2-send-btn', `${sc.name} ${vp.width}x${vp.height}: Tab focused ${focusedTestId}`)

        console.log(JSON.stringify({ scenario: sc.name, vp: `${vp.width}x${vp.height}`, metrics, scrollCheck }))
        await ctx.close()
      }
    }

    // Virtual keyboard visualViewport shrink check
    {
      const { ctx, page } = await setupPage({ width: 390, height: 844 }, completeReadiness)
      await page.addInitScript(() => {
        const listeners = new Set()
        let vvHeight = 844
        let vvOffsetTop = 0
        Object.defineProperty(window, 'visualViewport', {
          configurable: true,
          value: {
            get height() { return vvHeight },
            get width() { return 390 },
            get offsetTop() { return vvOffsetTop },
            get offsetLeft() { return 0 },
            addEventListener(type, fn) { if (type === 'resize' || type === 'scroll') listeners.add(fn) },
            removeEventListener(type, fn) { listeners.delete(fn) },
          },
        })
        window.__setVV = (h, top = 0) => {
          vvHeight = h
          vvOffsetTop = top
          listeners.forEach((fn) => fn())
        }
      })
      await page.goto(`${baseUrl}/?mode=saved-portal&pathname=/clients/chart-1/consult/conv-1`, { waitUntil: 'networkidle' })
      await page.waitForSelector('[data-testid="v2-composer-input"]')
      await page.evaluate(() => window.__setVV(490, 0))
      await page.waitForTimeout(100)
      const vvMetrics = await page.evaluate(() => {
        const sendR = document.querySelector('[data-testid="v2-send-btn"]').getBoundingClientRect()
        const compR = document.querySelector('[data-testid="v2-composer"]').getBoundingClientRect()
        const shellEl = document.querySelector('[data-testid="v2-chat-shell"]')
        const portal = shellEl?.parentElement?.parentElement?.getBoundingClientRect() ?? null
        return { portalH: portal ? Math.round(portal.height) : null, compBottom: Math.round(compR.bottom), sendBottom: Math.round(sendR.bottom) }
      })
      assert(vvMetrics.portalH === 490, `visualViewport portal height=${vvMetrics.portalH}`)
      assert(vvMetrics.compBottom <= 490 && vvMetrics.sendBottom <= 490, `composer exceeded virtual keyboard height: ${JSON.stringify(vvMetrics)}`)
      console.log(JSON.stringify({ scenario: 'visualViewport-keyboard', vp: '390x844->390x490', vvMetrics }))
      await ctx.close()
    }

    // HistoricalConversationView (portal + inline)
    for (const hMode of ['historical-portal', 'historical-inline']) {
      for (const vp of viewports) {
        const { ctx, page } = await setupPage(vp, completeReadiness)
        await page.goto(`${baseUrl}/?mode=${hMode}&pathname=/clients/chart-1/consult/conv-1`, { waitUntil: 'networkidle' })
        await page.waitForSelector('[data-testid="historical-reading"]')
        await page.waitForTimeout(150)
        const hMetrics = await page.evaluate(() => {
          const histMain = document.querySelector('[data-testid="historical-reading"]')
          const backLink = document.querySelector('[data-testid="historical-reading"] a[href="/clients/chart-1"]')
          return {
            docScrollWidth: document.documentElement.scrollWidth,
            innerWidth: window.innerWidth,
            hasTextarea: Boolean(document.querySelector('textarea')),
            hasComposer: Boolean(document.querySelector('[data-testid="v2-composer"]')),
            hasBackLink: Boolean(backLink),
            mainClientH: histMain?.clientHeight ?? 0,
            mainScrollH: histMain?.scrollHeight ?? 0,
          }
        })
        assert(!hMetrics.hasTextarea && !hMetrics.hasComposer, `${hMode}: rendered interactive input`)
        assert(hMetrics.hasBackLink, `${hMode}: missing back link to /clients/chart-1`)
        assert(hMetrics.docScrollWidth <= vp.width, `${hMode}: horizontal overflow ${hMetrics.docScrollWidth} > ${vp.width}`)
        assert(hMetrics.mainScrollH > hMetrics.mainClientH && hMetrics.mainClientH > 200, `${hMode}: did not scroll inside bounded container`)
        console.log(JSON.stringify({ scenario: hMode, vp: `${vp.width}x${vp.height}`, hMetrics }))
        await ctx.close()
      }
    }

    // Sibling route scroll check
    for (const vp of viewports) {
      const { ctx, page } = await setupPage(vp, completeReadiness)
      await page.goto(`${baseUrl}/?mode=timeline&pathname=/clients/chart-1/timeline`, { waitUntil: 'networkidle' })
      await page.waitForSelector('[data-testid="timeline-bottom-marker"]')
      const sib = await page.evaluate(() => {
        const mainEl = document.querySelector('#main-content')
        mainEl.scrollTop = mainEl.scrollHeight
        const marker = document.querySelector('[data-testid="timeline-bottom-marker"]').getBoundingClientRect()
        return {
          mainDisplay: getComputedStyle(mainEl).display,
          mainOverflowY: getComputedStyle(mainEl).overflowY,
          mainScrollH: mainEl.scrollHeight,
          mainClientH: mainEl.clientHeight,
          scrollTopAfter: mainEl.scrollTop,
          markerBottom: Math.round(marker.bottom),
        }
      })
      assert(sib.mainDisplay === 'block', `timeline #main-content display changed to ${sib.mainDisplay}`)
      assert(sib.mainScrollH > sib.mainClientH && sib.scrollTopAfter > 500, `timeline #main-content failed to scroll`)
      assert(sib.markerBottom <= vp.height + 5, `timeline bottom marker unreachable`)
      console.log(JSON.stringify({ scenario: 'timeline-sibling', vp: `${vp.width}x${vp.height}`, sib }))
      await ctx.close()
    }

    console.log('ALL CHROMIUM GEOMETRY & INTERACTION CHECKS PASSED')
  } finally {
    await browser.close()
    await server.close()
  }
}

main().catch((err) => {
  console.error(err)
  process.exit(1)
})
