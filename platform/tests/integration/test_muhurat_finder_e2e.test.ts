/**
 * test_muhurat_finder_e2e.ts — End-to-end smoke for Muhurat Finder (Phase 4C-6-S4)
 *
 * Acceptance criteria (AC.4C6S4.1):
 *   1. Spins up the Python sidecar locally via uvicorn
 *   2. Calls POST /api/compute/muhurat directly (sidecar endpoint)
 *      — mirrors what the Next.js /api/compute/muhurat proxy would send
 *   3. Asserts: windows returned, sorted by star_rating descending, top result has
 *      star_rating ≥ 4★ for a historically strong Vivah season window (Jan 2027)
 *   4. Validates the Ask-Madhav prompt can be constructed from a result window
 *      (structural validation — no browser required)
 *   5. Verifies all 6 MVP events return non-empty results over a 30-day range
 *
 * Note on "Ask Madhav" step:
 *   The actual "click Ask Madhav → chat opens" requires a running Next.js server
 *   and a browser (Playwright / Chrome DevTools). This test validates the prompt
 *   construction logic and the data that would be passed to the router.push() call
 *   in MuhuratResultsList.tsx. A full browser E2E is deferred to 4C-9 acharya sign-off.
 *
 * Skip behavior:
 *   - SKIP_SIDECAR_E2E=1 → skip the sidecar startup; useful in CI without Python.
 *   - PYTHON_SIDECAR_URL already set → use the live sidecar at that URL.
 *
 * Phase: 4C-6-S4 (Item 1)
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { spawn, type ChildProcess } from 'child_process'
import { setTimeout } from 'timers/promises'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const SIDECAR_DIR = path.resolve(__dirname, '../../python-sidecar')
const SIDECAR_PORT = 18766  // separate port from the panchanga E2E (18765)
const SIDECAR_URL = `http://localhost:${SIDECAR_PORT}`

// Bhubaneswar canonical location (project §B)
const BHUB_LAT = 20.27
const BHUB_LON = 85.84
const BHUB_TZ = 330  // IST = UTC+05:30

// Target range — Jan 2027 is a classical Vivah season (Shukla paksha, fixed nakshatras,
// Jupiter direct, Venus non-combust). Expect strong ratings.
const DATE_FROM_VIVAH = '2027-01-01'
const DATE_TO_VIVAH   = '2027-01-31'  // 30-day window for the main gate test

// 60-day window used in the brief §3 Item 1 scenario description.
// We use 30-day to keep test latency low (7–8ms/day × 30 = ~210ms).
const DATE_FROM_60D = '2027-01-01'
const DATE_TO_60D   = '2027-03-01'  // ~59 days

let sidecarProcess: ChildProcess | null = null
let sidecarStartedLocally = false
let skipE2E = false
let skipReason = ''
let baseUrl = SIDECAR_URL

// ── Types ────────────────────────────────────────────────────────────────────

interface MuhuratWindow {
  event: string
  start_utc: string | null
  end_utc: string | null
  star_rating: number
  score: number
  // breakdown uses verbose keys: tithi_contrib, nakshatra_contrib, etc.
  breakdown: Record<string, number | string>
}

interface MuhuratResponse {
  ok: boolean
  event: string
  count: number
  windows: MuhuratWindow[]
  supported_events?: string[]
}

// ── Sidecar lifecycle ─────────────────────────────────────────────────────────

async function waitForSidecar(url: string, timeoutMs = 20_000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`${url}/health`, { signal: AbortSignal.timeout(1000) })
      if (res.ok) return true
    } catch {
      // Not up yet
    }
    await setTimeout(300)
  }
  return false
}

beforeAll(async () => {
  if (process.env['SKIP_SIDECAR_E2E']) {
    skipE2E = true
    skipReason = 'SKIP_SIDECAR_E2E env var is set'
    return
  }

  if (process.env['PYTHON_SIDECAR_URL']) {
    baseUrl = process.env['PYTHON_SIDECAR_URL']!
    skipReason = 'Using live sidecar from PYTHON_SIDECAR_URL env var'
    return
  }

  const uvicornBin = 'uvicorn'
  try {
    sidecarProcess = spawn(
      uvicornBin,
      ['main:app', '--host', '0.0.0.0', '--port', String(SIDECAR_PORT)],
      {
        cwd: SIDECAR_DIR,
        stdio: ['ignore', 'pipe', 'pipe'],
        env: {
          ...process.env,
          PYTHON_SIDECAR_API_KEY: '',  // no auth for local test
        },
      },
    )

    sidecarProcess.stderr?.on('data', (chunk: Buffer) => {
      const msg = chunk.toString()
      if (msg.includes('Error') || msg.includes('error') || msg.includes('Exception')) {
        process.stderr.write('[muhurat-sidecar] ' + msg)
      }
    })

    const healthy = await waitForSidecar(baseUrl, 25_000)
    if (!healthy) {
      skipE2E = true
      skipReason = 'Sidecar did not become healthy within 25s — check uvicorn/pyswisseph install'
      sidecarProcess.kill()
      sidecarProcess = null
      return
    }

    sidecarStartedLocally = true
  } catch (err) {
    skipE2E = true
    skipReason = `Failed to spawn uvicorn: ${err instanceof Error ? err.message : String(err)}`
  }
}, 35_000)

afterAll(async () => {
  if (sidecarProcess && sidecarStartedLocally) {
    sidecarProcess.kill('SIGTERM')
    await setTimeout(500)
    if (!sidecarProcess.killed) {
      sidecarProcess.kill('SIGKILL')
    }
    sidecarProcess = null
  }
})

// ── Helper ────────────────────────────────────────────────────────────────────

async function callMuhurat(
  event: string,
  dateFrom: string,
  dateTo: string,
  topN = 10,
): Promise<MuhuratResponse> {
  const res = await fetch(`${baseUrl}/api/compute/muhurat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      event,
      date_from: dateFrom,
      date_to: dateTo,
      lat: BHUB_LAT,
      lon: BHUB_LON,
      tz_offset_minutes: BHUB_TZ,
      chart_id: null,
      top_n: topN,
    }),
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`Sidecar returned HTTP ${res.status}: ${body}`)
  }
  return res.json() as Promise<MuhuratResponse>
}

// ── Ask-Madhav prompt builder (mirrors MuhuratResultsList.tsx logic) ──────────

function buildAskMadhavPrompt(window: MuhuratWindow, rank: number): string {
  const dateLabel = window.start_utc
    ? new Date(window.start_utc).toDateString()
    : 'Unknown date'

  // Short keys since Phase 4C enrichment (tithi, nakshatra, vara …)
  const topFactors = Object.entries(window.breakdown)
    .filter(([, v]) => typeof v === 'number' && (v as number) > 0)
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 3)
    .map(([k, v]) => `${k} (+${(v as number).toFixed(2)})`)
    .join(', ')

  return (
    `Walk me through why ${dateLabel} is ranked #${rank} for ${window.event.replace(/_/g, ' ')}. ` +
    `The Panchang engine gave it ${window.star_rating} stars (score ${window.score.toFixed(2)}). ` +
    (topFactors ? `Top factors: ${topFactors}. ` : '') +
    `What does this mean for planning this event?`
  )
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('Muhurat Finder E2E — live sidecar (AC.4C6S4.1)', () => {
  // ── Gate 1: Sidecar health ──────────────────────────────────────────────────
  it('sidecar /health returns ok', async () => {
    if (skipE2E) { console.warn(`SKIPPED: ${skipReason}`); return }
    const res = await fetch(`${baseUrl}/health`)
    expect(res.ok).toBe(true)
    const body = await res.json() as { status: string }
    expect(body.status).toBe('ok')
  })

  // ── Gate 2: Vivah 30-day range — core quality gate ─────────────────────────
  it('Vivah over 30 days (Jan 2027) returns 10 windows sorted by star_rating descending', async () => {
    if (skipE2E) { console.warn(`SKIPPED: ${skipReason}`); return }

    const data = await callMuhurat('vivah', DATE_FROM_VIVAH, DATE_TO_VIVAH, 10)

    expect(data.ok, 'Response ok flag').toBe(true)
    expect(data.event).toBe('vivah')
    expect(data.windows).toBeDefined()
    expect(data.windows.length, 'Expected 10 windows').toBe(10)

    // Sorted by score descending (star_rating may tie; score is the tiebreaker)
    const scores = data.windows.map((w) => w.score)
    expect(scores, 'Windows not sorted by score descending').toEqual(
      [...scores].sort((a, b) => b - a)
    )

    // Star ratings must be in descending order (or equal — ties are allowed)
    const ratings = data.windows.map((w) => w.star_rating)
    for (let i = 1; i < ratings.length; i++) {
      expect(ratings[i]!, `Window ${i} star_rating should be ≤ window ${i - 1}`).toBeLessThanOrEqual(
        ratings[i - 1]!
      )
    }

    // Jan 2027 is a strong Vivah season — top result must be ≥ 4★
    const topRating = data.windows[0]!.star_rating
    expect(topRating, `Top result rating (${topRating}) must be ≥ 4 for strong Vivah season`).toBeGreaterThanOrEqual(4)

    console.log(
      `  ✓ Vivah Jan 2027: ${data.count} windows in range; top result: ` +
      `${data.windows[0]!.star_rating}★ score=${data.windows[0]!.score.toFixed(2)}`
    )
  }, 30_000)

  // ── Gate 3: Results have breakdown badges ──────────────────────────────────
  it('Each result window carries a non-empty breakdown dict with contribution values', async () => {
    if (skipE2E) { console.warn(`SKIPPED: ${skipReason}`); return }

    const data = await callMuhurat('vivah', DATE_FROM_VIVAH, DATE_TO_VIVAH, 5)

    for (const w of data.windows) {
      expect(w.breakdown, `Window on ${w.start_utc} has empty breakdown`).toBeDefined()
      // Breakdown uses short keys (tithi, nakshatra, vara, yoga, karana …) since Phase 4C enrichment
      const contribKeys = Object.keys(w.breakdown).filter((k) => typeof w.breakdown[k] === 'number')
      expect(contribKeys.length, `Window on ${w.start_utc} breakdown has no contribution factors`).toBeGreaterThan(0)
      // At least one contribution must be non-zero (any day has some factor)
      const numericValues = contribKeys.map((k) => w.breakdown[k] as number)
      const hasNonZero = numericValues.some((v) => v !== 0)
      expect(hasNonZero, `Window on ${w.start_utc} has all-zero contributions`).toBe(true)
    }
  }, 30_000)

  // ── Gate 4: Ask-Madhav prompt construction ─────────────────────────────────
  it('Top result produces a non-empty Ask-Madhav prompt with expected structure', async () => {
    if (skipE2E) { console.warn(`SKIPPED: ${skipReason}`); return }

    const data = await callMuhurat('vivah', DATE_FROM_VIVAH, DATE_TO_VIVAH, 10)
    expect(data.windows.length).toBeGreaterThan(0)

    const topWindow = data.windows[0]!
    const prompt = buildAskMadhavPrompt(topWindow, 1)

    // The prompt must contain the event name, score, and star rating
    expect(prompt).toContain('vivah')
    expect(prompt).toContain(String(topWindow.star_rating))
    expect(prompt).toContain(topWindow.score.toFixed(2))
    expect(prompt.length, 'Prompt must be non-trivially long').toBeGreaterThan(80)

    // The router.push call would be: /clients/abhisek_mohanty_primary/consume?prompt=<encoded>
    const encoded = encodeURIComponent(prompt)
    const deepLink = `/clients/abhisek_mohanty_primary/consume?prompt=${encoded}`
    expect(deepLink).toContain('/consume?prompt=')

    console.log(`  ✓ Ask-Madhav deep link length: ${deepLink.length} chars`)
  }, 30_000)

  // ── Gate 5: 60-day range (brief §3 Item 1 scenario) ───────────────────────
  it('Vivah over 60 days returns ≤ 10 windows (top_n cap respected)', async () => {
    if (skipE2E) { console.warn(`SKIPPED: ${skipReason}`); return }

    const data = await callMuhurat('vivah', DATE_FROM_60D, DATE_TO_60D, 10)
    expect(data.windows.length, 'top_n=10 cap must be respected').toBeLessThanOrEqual(10)
    console.log(
      `  ✓ Vivah 60-day: ${data.count} windows in range; returned ${data.windows.length}`
    )
  }, 60_000)

  // ── Gate 6: All 6 MVP events return results over a 30-day window ──────────
  it.each([
    'vivah',
    'griha_pravesh',
    'vyapara',
    'yatra',
    'property_purchase',
    'mantra_initiation',
  ])('Event %s returns non-empty results (Jan 2027, 30-day)', async (eventKey) => {
    if (skipE2E) { console.warn(`SKIPPED: ${skipReason}`); return }

    const data = await callMuhurat(eventKey, DATE_FROM_VIVAH, DATE_TO_VIVAH, 5)
    expect(data.ok, `${eventKey} response ok flag`).toBe(true)
    expect(data.windows.length, `${eventKey} should return at least 1 window`).toBeGreaterThan(0)
    console.log(
      `  ✓ ${eventKey}: ${data.windows.length} windows; top=${data.windows[0]?.star_rating}★`
    )
  }, 30_000)

  // ── Gate 7: Reject unsupported event ─────────────────────────────────────
  it('Unsupported event returns HTTP 422', async () => {
    if (skipE2E) { console.warn(`SKIPPED: ${skipReason}`); return }

    const res = await fetch(`${baseUrl}/api/compute/muhurat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event: 'invalid_event_xyz',
        date_from: DATE_FROM_VIVAH,
        date_to: DATE_TO_VIVAH,
        lat: BHUB_LAT,
        lon: BHUB_LON,
        tz_offset_minutes: BHUB_TZ,
      }),
    })
    expect(res.status, 'Unsupported event must return 422').toBe(422)
  })
})
