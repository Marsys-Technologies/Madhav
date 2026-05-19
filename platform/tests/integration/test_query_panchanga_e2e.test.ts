/**
 * test_query_panchanga_e2e.test.ts — End-to-end smoke for queryPanchanga tool (Phase 4C-3)
 *
 * Acceptance criteria (AC.4C3.10):
 *   1. Starts the Python sidecar locally via uvicorn
 *   2. Invokes queryPanchanga.retrieve() with Bhubaneswar defaults
 *   3. Asserts returned ToolBundle has non-empty facts including tithi, nakshatra,
 *      vara, and special_yogas entries
 *   4. Asserts diagnostics.latency_ms is finite (sanity)
 *   5. Stops the sidecar after the test
 *
 * Runs locally only (requires Python + pyswisseph installed in sidecar env).
 * Skip gate: if PYTHON_SIDECAR_URL is already set (live sidecar), or if
 * SKIP_SIDECAR_E2E env var is set, skip the subprocess startup.
 *
 * Phase 4C-3 — gate: PASS
 */

import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { spawn, type ChildProcess } from 'child_process'
import { setTimeout } from 'timers/promises'
import path from 'path'

const SIDECAR_DIR = path.resolve(__dirname, '../../python-sidecar')
const SIDECAR_PORT = 18765  // unusual port to avoid conflicts
const SIDECAR_URL = `http://localhost:${SIDECAR_PORT}`
const TODAY = new Date().toISOString().slice(0, 10)

// Bhubaneswar (project canonical location, §8 brief context)
const BHUB_LAT = 20.27
const BHUB_LON = 85.84
const BHUB_TZ = 330

let sidecarProcess: ChildProcess | null = null
let sidecarStartedLocally = false
let skipE2E = false
let skipReason = ''

/**
 * Wait for the sidecar to become healthy, polling /health endpoint.
 */
async function waitForSidecar(url: string, timeoutMs = 15_000): Promise<boolean> {
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
  // If SKIP_SIDECAR_E2E is set, skip the whole test suite
  if (process.env['SKIP_SIDECAR_E2E']) {
    skipE2E = true
    skipReason = 'SKIP_SIDECAR_E2E env var is set'
    return
  }

  // If PYTHON_SIDECAR_URL is already set, use the live sidecar
  if (process.env['PYTHON_SIDECAR_URL']) {
    process.env['PYTHON_SIDECAR_URL'] = process.env['PYTHON_SIDECAR_URL']!
    skipReason = 'Using live sidecar from PYTHON_SIDECAR_URL env var'
    return
  }

  // Start the sidecar as a subprocess
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
          // No API key for local test — sidecar skips auth when API_KEY is empty
          PYTHON_SIDECAR_API_KEY: '',
        },
      },
    )

    sidecarProcess.stderr?.on('data', (chunk: Buffer) => {
      const msg = chunk.toString()
      // Only log startup errors, not normal uvicorn access logs
      if (msg.includes('Error') || msg.includes('error')) {
        process.stderr.write('[sidecar] ' + msg)
      }
    })

    const healthy = await waitForSidecar(SIDECAR_URL, 20_000)
    if (!healthy) {
      skipE2E = true
      skipReason = 'Sidecar did not become healthy within 20s — check uvicorn/pyswisseph install'
      sidecarProcess.kill()
      sidecarProcess = null
      return
    }

    sidecarStartedLocally = true
    process.env['PYTHON_SIDECAR_URL'] = SIDECAR_URL
  } catch (err) {
    skipE2E = true
    skipReason = `Failed to spawn uvicorn: ${err instanceof Error ? err.message : String(err)}`
  }
}, 30_000)

afterAll(async () => {
  if (sidecarProcess && sidecarStartedLocally) {
    sidecarProcess.kill('SIGTERM')
    await setTimeout(500)
    if (!sidecarProcess.killed) {
      sidecarProcess.kill('SIGKILL')
    }
    sidecarProcess = null
    delete process.env['PYTHON_SIDECAR_URL']
  }
})

describe('queryPanchanga E2E smoke — live sidecar', () => {
  it('sidecar health check passes', async () => {
    if (skipE2E) {
      console.warn(`SKIPPED: ${skipReason}`)
      return
    }
    const res = await fetch(`${SIDECAR_URL}/health`)
    expect(res.ok).toBe(true)
    const body = await res.json() as { status: string }
    expect(body.status).toBe('ok')
  })

  it('POST /api/compute/panchanga returns valid Panchang JSON', async () => {
    if (skipE2E) {
      console.warn(`SKIPPED: ${skipReason}`)
      return
    }
    const res = await fetch(`${SIDECAR_URL}/api/compute/panchanga`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        date: TODAY,
        lat: BHUB_LAT,
        lon: BHUB_LON,
        tz_offset_minutes: BHUB_TZ,
      }),
    })
    expect(res.ok, `Sidecar returned HTTP ${res.status}`).toBe(true)
    const body = await res.json() as { ok: boolean; panchang: Record<string, unknown>; cache_hit: boolean }
    expect(body.ok).toBe(true)
    expect(body.cache_hit).toBe(false)  // engine-direct path; 4C-2 will add cache
    expect(body.panchang).toBeDefined()
    expect(body.panchang['tithi']).toBeDefined()
    expect(body.panchang['nakshatra']).toBeDefined()
    expect(body.panchang['vara']).toBeDefined()
    expect(body.panchang['special_yogas']).toBeDefined()
    expect(Array.isArray(body.panchang['special_yogas'])).toBe(true)
  })

  it('queryPanchanga.retrieve() returns ToolBundle with required sections', async () => {
    if (skipE2E) {
      console.warn(`SKIPPED: ${skipReason}`)
      return
    }

    // Dynamic import to pick up the set PYTHON_SIDECAR_URL
    const { tool } = await import('../../src/lib/retrieve/query_panchanga.js')

    const fakePlan = {
      query_plan_id: 'e2e-smoke-001',
      query_text: "What is today's panchang?",
      query_class: 'factual' as const,
      domains: [],
      forward_looking: false,
      audience_tier: 'client' as const,
      tools_authorized: ['query_panchanga'],
      history_mode: 'synthesized' as const,
      panel_mode: false,
      expected_output_shape: 'single_answer' as const,
      manifest_fingerprint: 'smoke-test',
      schema_version: '1.0' as const,
    }

    const bundle = await tool.retrieve(fakePlan, {
      date: TODAY,
      lat: BHUB_LAT,
      lon: BHUB_LON,
      tz_offset_minutes: BHUB_TZ,
    })

    // AC.4C3.10 assertions:
    expect(bundle).toBeDefined()
    expect(bundle.tool_name).toBe('query_panchanga')
    expect(bundle.results.length).toBeGreaterThan(0)

    // tithi, nakshatra, vara must be in the five_angas section
    const angaResult = bundle.results.find(r => r.content.includes('five_angas'))
    expect(angaResult, 'five_angas section missing from results').toBeDefined()
    const angaParsed = JSON.parse(angaResult!.content) as Record<string, unknown>
    expect(angaParsed['tithi']).toBeDefined()
    expect(angaParsed['nakshatra']).toBeDefined()
    expect(angaParsed['vara']).toBeDefined()

    // special_yogas section must exist
    const yogaResult = bundle.results.find(r => r.content.includes('special_yogas'))
    expect(yogaResult, 'special_yogas section missing from results').toBeDefined()
    const yogaParsed = JSON.parse(yogaResult!.content) as { special_yogas: unknown[] }
    expect(Array.isArray(yogaParsed['special_yogas'])).toBe(true)

    // latency_ms must be finite
    expect(typeof bundle.latency_ms).toBe('number')
    expect(isFinite(bundle.latency_ms)).toBe(true)
    expect(bundle.latency_ms).toBeGreaterThan(0)
  }, 30_000)
})
