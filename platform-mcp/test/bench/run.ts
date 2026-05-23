/**
 * run.ts — MCPT v3.2 Phase 8a Bench Harness: Scenario Runner
 *
 * Reads YAML scenarios from bench/scenarios/*.yaml (repo root),
 * executes each step through the registered MCP tool handlers (via mock
 * infrastructure — no live server needed), and records:
 *   - round_trips: number of steps in the scenario
 *   - response_bytes: sum of serialized response lengths
 *   - wall_time_ms: wall-clock time for all steps combined
 *
 * Output: bench/<git-sha>.json in the repo root bench/ directory.
 *
 * Vitest entry-point: npm run bench:capture
 * (vitest run test/bench/run.ts --reporter=verbose)
 *
 * MCPT v3.2 Phase 8a
 */

import { describe, it, expect, vi, beforeAll } from 'vitest'
import { execSync } from 'node:child_process'
import * as fs from 'node:fs'
import * as path from 'node:path'
import { fileURLToPath } from 'node:url'

// ── Mock cache module (holistic_bundle uses it) ───────────────────────────────
vi.mock('../../src/bundles/cache.js', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../src/bundles/cache.js')>()
  return {
    ...actual,
    cacheLookup: vi.fn().mockResolvedValue({ hit: false }),
    cacheStore: vi.fn().mockResolvedValue(undefined),
  }
})

// ── Set SERVICE_TOKEN to bypass GCP metadata fetch ────────────────────────────
process.env['SERVICE_TOKEN'] = 'bench-service-token'

// ── Directory constants ───────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
// __dirname = platform-mcp/test/bench → repo root is 3 levels up
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..')
const BENCH_DIR = path.join(REPO_ROOT, 'bench')
const SCENARIOS_DIR = path.join(BENCH_DIR, 'scenarios')
const PLATFORM_MCP_DIR = path.resolve(__dirname, '..', '..')

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ScenarioStep {
  tool: string
  args: Record<string, unknown>
}

export interface ScenarioDefinition {
  name: string
  description: string
  audience_tier: 'super_admin' | 'acharya' | 'client'
  mcp_base_url?: string
  steps: ScenarioStep[]
  metrics: string[]
  status?: string
}

export interface ScenarioMetrics {
  round_trips: number
  response_bytes: number
  wall_time_ms: number
}

export interface ScenarioResult {
  scenario: string
  description: string
  metrics: ScenarioMetrics
  steps_executed: number
  ok: boolean
  error?: string
}

export interface BenchCapture {
  git_sha: string
  captured_at: string
  platform_mcp_dir: string
  scenarios: Record<string, ScenarioResult>
}

// ── YAML parser (minimal — no external dependency) ───────────────────────────
// Parses the simple YAML format used in bench/scenarios/*.yaml.
// We handle: string scalars, flow arrays ([...]), flow objects ({...}),
// top-level keys, and nested list items (- key: value).
// This is intentionally narrow — it covers exactly what bench scenarios need.

function parseScenarioYaml(content: string): ScenarioDefinition {
  // Strip comment lines
  const lines = content
    .split('\n')
    .map(l => l.replace(/#.*$/, '').trimEnd())
    .filter(l => l.trim() !== '')

  const result: Record<string, unknown> = {}
  let i = 0

  while (i < lines.length) {
    const line = lines[i] ?? ''
    // Top-level key: value
    const topMatch = line.match(/^(\w[\w_]*)\s*:\s*(.*)$/)
    if (topMatch) {
      const [, key, rawVal] = topMatch as [string, string, string]
      const trimmedVal = rawVal.trim()

      if (trimmedVal === '' || trimmedVal === undefined) {
        // Next lines may be a list
        i++
        const items: Record<string, unknown>[] = []
        while (i < lines.length) {
          const itemLine = lines[i] ?? ''
          if (itemLine.match(/^\s+-\s+/)) {
            // list item line: "  - key: value" or "  - tool: foo"
            const itemContent = itemLine.replace(/^\s+-\s+/, '')
            const item = parseFlowObject(`{${itemContent}}`)
            if (item && typeof item === 'object') {
              items.push(item as Record<string, unknown>)
            }
            i++
          } else if (itemLine.match(/^\s+\w/)) {
            // continuation key under the list item
            const lastItem = items[items.length - 1]
            if (lastItem) {
              const contMatch = itemLine.trim().match(/^(\w[\w_]*)\s*:\s*(.*)$/)
              if (contMatch) {
                const [, ck, cv] = contMatch as [string, string, string]
                lastItem[ck] = parseScalar(cv.trim())
              }
            }
            i++
          } else {
            break
          }
        }
        result[key] = items
      } else if (trimmedVal.startsWith('[')) {
        result[key] = parseFlowArray(trimmedVal)
        i++
      } else {
        result[key] = parseScalar(trimmedVal)
        i++
      }
    } else {
      i++
    }
  }

  return result as unknown as ScenarioDefinition
}

function parseScalar(val: string): unknown {
  if (val === 'true') return true
  if (val === 'false') return false
  if (val === 'null' || val === '~') return null
  if (/^-?\d+(\.\d+)?$/.test(val)) return Number(val)
  // Quoted string
  if ((val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))) {
    return val.slice(1, -1)
  }
  return val
}

function parseFlowArray(val: string): unknown[] {
  // Parse [a, b, c] or ["a", "b"] or [a,b]
  const inner = val.replace(/^\[/, '').replace(/\]$/, '').trim()
  if (!inner) return []
  return inner.split(',').map(s => parseScalar(s.trim()))
}

function parseFlowObject(val: string): Record<string, unknown> {
  // Parse { key: val, key2: val2 } — simple flow object
  const inner = val.replace(/^\{/, '').replace(/\}$/, '').trim()
  if (!inner) return {}
  const result: Record<string, unknown> = {}
  // Split by comma but not inside arrays or nested objects
  const parts = splitFlowObjectParts(inner)
  for (const part of parts) {
    const colonIdx = part.indexOf(':')
    if (colonIdx === -1) continue
    const k = part.slice(0, colonIdx).trim()
    const v = part.slice(colonIdx + 1).trim()
    result[k] = v.startsWith('[') ? parseFlowArray(v) : parseScalar(v)
  }
  return result
}

function splitFlowObjectParts(s: string): string[] {
  const parts: string[] = []
  let depth = 0
  let start = 0
  for (let i = 0; i < s.length; i++) {
    const c = s[i]
    if (c === '[' || c === '{') depth++
    else if (c === ']' || c === '}') depth--
    else if (c === ',' && depth === 0) {
      parts.push(s.slice(start, i).trim())
      start = i + 1
    }
  }
  const last = s.slice(start).trim()
  if (last) parts.push(last)
  return parts
}

// ── Git SHA helper ────────────────────────────────────────────────────────────

function getGitSha(): string {
  // Try repo root first, then cwd, then fall back
  const candidates = [REPO_ROOT, process.cwd()]
  for (const cwd of candidates) {
    try {
      return execSync('git rev-parse --short HEAD', {
        cwd,
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
      }).trim()
    } catch {
      // try next
    }
  }
  return 'unknown'
}

// ── Mock infrastructure ───────────────────────────────────────────────────────
// We don't spin up a live HTTP server. Instead we call the tool handlers
// directly via the same mock-server pattern used in the unit tests.
// Each tool's registerXxxTool() captures its handler; we call that handler
// with the scenario step args.
//
// For bench metrics:
//   round_trips = number of steps
//   response_bytes = sum of JSON.stringify(result).length across steps
//   wall_time_ms = Date.now() diff over all steps

// Stub fetch so callPlatformPrimitive doesn't try to hit a real server
vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({
  ok: true,
  status: 200,
  json: () => Promise.resolve({
    ok: true,
    result: {
      rows: Array.from({ length: 10 }, (_, i) => ({
        fact_id: `MOCK.${String(i + 1).padStart(3, '0')}`,
        category: 'mock',
        value_text: `mock fact ${i + 1}`,
      })),
      rows_by_category: {
        birth_metadata: [{ fact_id: 'BM.001', category: 'birth_metadata', value_text: 'mock birth metadata' }],
        planet: Array.from({ length: 9 }, (_, i) => ({
          fact_id: `PLN.${String(i + 1).padStart(3, '0')}`,
          category: 'planet',
          value_text: `mock planet ${i + 1}`,
        })),
        house: Array.from({ length: 12 }, (_, i) => ({
          fact_id: `HSE.${String(i + 1).padStart(3, '0')}`,
          category: 'house',
          value_text: `mock house ${i + 1}`,
        })),
        yoga: Array.from({ length: 5 }, (_, i) => ({
          fact_id: `YOG.${String(i + 1).padStart(3, '0')}`,
          category: 'yoga',
          value_text: `mock yoga ${i + 1}`,
        })),
        arudha: Array.from({ length: 3 }, (_, i) => ({
          fact_id: `ARU.${String(i + 1).padStart(3, '0')}`,
          category: 'arudha',
          value_text: `mock arudha ${i + 1}`,
        })),
        aspect: Array.from({ length: 8 }, (_, i) => ({
          fact_id: `ASP.${String(i + 1).padStart(3, '0')}`,
          category: 'aspect',
          value_text: `mock aspect ${i + 1}`,
        })),
        dasha_vimshottari: Array.from({ length: 4 }, (_, i) => ({
          fact_id: `DVS.${String(i + 1).padStart(3, '0')}`,
          category: 'dasha_vimshottari',
          value_text: `mock dasha ${i + 1}`,
        })),
        sensitive_point: Array.from({ length: 5 }, (_, i) => ({
          fact_id: `SNS.${String(i + 1).padStart(3, '0')}`,
          category: 'sensitive_point',
          value_text: `mock sensitive ${i + 1}`,
        })),
        signals: Array.from({ length: 20 }, (_, i) => ({
          signal_id: `MSR.${String(i + 1).padStart(3, '0')}`,
          value_text: `mock signal ${i + 1}`,
        })),
      },
      signals: Array.from({ length: 20 }, (_, i) => ({
        signal_id: `MSR.${String(i + 1).padStart(3, '0')}`,
        value_text: `mock signal ${i + 1}`,
      })),
      count: 20,
      total_rows: 50,
    },
    trace_id: 'bench-trace-001',
    epistemics: { surgical: true, confidence_band: 'high' },
  }),
})))

// Principal used for all bench tool calls
const BENCH_PRINCIPAL = {
  user_uid: 'bench-uid',
  audience_tier: 'super_admin' as const,
  key_id: 'bench-key-001',
}

// ── Tool handler registry ─────────────────────────────────────────────────────
// Mirrors the makeMockServer() pattern from chart_summary.test.ts.
// Registers all needed tool handlers, then dispatches by tool name.

type ToolHandler = (args: Record<string, unknown>) => Promise<unknown>

async function buildToolRegistry(): Promise<Map<string, ToolHandler>> {
  const registry = new Map<string, ToolHandler>()

  function makeMockServer(toolName: string): {
    server: { tool: (...args: unknown[]) => void }
  } {
    return {
      server: {
        tool: vi.fn((
          _name: string,
          _description: string,
          _schema: Record<string, unknown>,
          handler: ToolHandler
        ) => {
          registry.set(toolName, handler)
        }),
      },
    }
  }

  // Register chart_summary
  {
    const { registerChartSummaryTool } = await import('../../src/tools/chart_summary.js')
    const { server } = makeMockServer('chart_summary')
    registerChartSummaryTool(
      server as unknown as Parameters<typeof registerChartSummaryTool>[0],
      () => BENCH_PRINCIPAL
    )
  }

  // Register query_chart_facts
  {
    const { registerQueryChartFacts } = await import('../../src/tools/query_chart_facts.js')
    const { server } = makeMockServer('query_chart_facts')
    registerQueryChartFacts(
      server as unknown as Parameters<typeof registerQueryChartFacts>[0],
      () => BENCH_PRINCIPAL
    )
  }

  // Register holistic_bundle
  {
    const { registerHolisticBundle } = await import('../../src/tools/holistic_bundle_tool.js')
    const { server } = makeMockServer('holistic_bundle')
    registerHolisticBundle(
      server as unknown as Parameters<typeof registerHolisticBundle>[0],
      () => BENCH_PRINCIPAL
    )
  }

  return registry
}

// ── Scenario loader ───────────────────────────────────────────────────────────

function loadScenarios(): ScenarioDefinition[] {
  if (!fs.existsSync(SCENARIOS_DIR)) return []
  const files = fs.readdirSync(SCENARIOS_DIR).filter(f => f.endsWith('.yaml') || f.endsWith('.yml'))
  const scenarios: ScenarioDefinition[] = []
  for (const file of files) {
    const content = fs.readFileSync(path.join(SCENARIOS_DIR, file), 'utf8')
    try {
      const scenario = parseScenarioYaml(content)
      if (scenario.name) scenarios.push(scenario)
    } catch (err) {
      console.warn(`[bench] Failed to parse ${file}: ${err}`)
    }
  }
  return scenarios
}

// ── Scenario executor ─────────────────────────────────────────────────────────

async function executeScenario(
  scenario: ScenarioDefinition,
  registry: Map<string, ToolHandler>
): Promise<ScenarioResult> {
  const startTime = Date.now()
  let totalResponseBytes = 0
  let stepsExecuted = 0
  let lastError: string | undefined

  for (const step of scenario.steps) {
    const handler = registry.get(step.tool)
    if (!handler) {
      lastError = `No handler registered for tool: ${step.tool}`
      break
    }
    try {
      const result = await handler(step.args)
      const serialized = JSON.stringify(result)
      totalResponseBytes += serialized.length
      stepsExecuted++
    } catch (err) {
      lastError = String(err)
      break
    }
  }

  const wallTimeMs = Date.now() - startTime

  return {
    scenario: scenario.name,
    description: scenario.description ?? '',
    metrics: {
      round_trips: stepsExecuted,
      response_bytes: totalResponseBytes,
      wall_time_ms: wallTimeMs,
    },
    steps_executed: stepsExecuted,
    ok: lastError === undefined,
    error: lastError,
  }
}

// ── Capture + write output ────────────────────────────────────────────────────

async function captureBaseline(
  scenarios: ScenarioDefinition[],
  registry: Map<string, ToolHandler>
): Promise<BenchCapture> {
  const gitSha = getGitSha()
  const results: Record<string, ScenarioResult> = {}

  for (const scenario of scenarios) {
    const result = await executeScenario(scenario, registry)
    results[scenario.name] = result
  }

  return {
    git_sha: gitSha,
    captured_at: new Date().toISOString(),
    platform_mcp_dir: PLATFORM_MCP_DIR,
    scenarios: results,
  }
}

// ── Vitest test suite ─────────────────────────────────────────────────────────

describe('MCPT v3.2 P8a — Bench Harness: Scenario Runner', () => {
  let registry: Map<string, ToolHandler>
  let scenarios: ScenarioDefinition[]
  let capture: BenchCapture

  beforeAll(async () => {
    registry = await buildToolRegistry()
    scenarios = loadScenarios()
    capture = await captureBaseline(scenarios, registry)

    // Write bench/<git-sha>.json to repo bench/ dir
    if (!fs.existsSync(BENCH_DIR)) {
      fs.mkdirSync(BENCH_DIR, { recursive: true })
    }

    const outputPath = path.join(BENCH_DIR, `${capture.git_sha}.json`)
    fs.writeFileSync(outputPath, JSON.stringify(capture, null, 2))

    // Also write bench/mcpt-v32-baseline.json (phase 0 baseline capture)
    const baselinePath = path.join(BENCH_DIR, 'mcpt-v32-baseline.json')
    if (!fs.existsSync(baselinePath)) {
      fs.writeFileSync(baselinePath, JSON.stringify(capture, null, 2))
    }
  })

  it('loads scenario definitions from bench/scenarios/', () => {
    expect(scenarios.length).toBeGreaterThanOrEqual(1)
    for (const s of scenarios) {
      expect(s.name).toBeTruthy()
      expect(Array.isArray(s.steps)).toBe(true)
      expect(s.steps.length).toBeGreaterThanOrEqual(1)
    }
  })

  it('all scenario tool handlers are registered', () => {
    for (const scenario of scenarios) {
      for (const step of scenario.steps) {
        expect(
          registry.has(step.tool),
          `Handler missing for tool: ${step.tool} in scenario: ${scenario.name}`
        ).toBe(true)
      }
    }
  })

  it('all scenarios execute without errors', async () => {
    for (const [name, result] of Object.entries(capture.scenarios)) {
      expect(result.ok, `Scenario ${name} failed: ${result.error ?? 'unknown'}`).toBe(true)
      expect(result.steps_executed).toBeGreaterThanOrEqual(1)
    }
  })

  it('records round_trips matching step count for each scenario', () => {
    for (const scenario of scenarios) {
      const result = capture.scenarios[scenario.name]
      if (result?.ok) {
        expect(result.metrics.round_trips).toBe(scenario.steps.length)
      }
    }
  })

  it('records non-zero response_bytes for each scenario', () => {
    for (const [name, result] of Object.entries(capture.scenarios)) {
      if (result.ok) {
        expect(result.metrics.response_bytes, `response_bytes is 0 for ${name}`).toBeGreaterThan(0)
      }
    }
  })

  it('records non-negative wall_time_ms for each scenario', () => {
    for (const [name, result] of Object.entries(capture.scenarios)) {
      if (result.ok) {
        expect(result.metrics.wall_time_ms, `wall_time_ms negative for ${name}`).toBeGreaterThanOrEqual(0)
      }
    }
  })

  it('canonical_d9_workflow: round_trips == 2 (chart_summary + query_chart_facts)', () => {
    const result = capture.scenarios['canonical_d9_workflow']
    if (result?.ok) {
      expect(result.metrics.round_trips).toBe(2)
    }
  })

  it('portal_synthesis_floor: round_trips == 5 (5 separate query_chart_facts calls)', () => {
    const result = capture.scenarios['portal_synthesis_floor']
    if (result?.ok) {
      expect(result.metrics.round_trips).toBe(5)
    }
  })

  it('holistic_d9: round_trips == 1 (single holistic_bundle call)', () => {
    const result = capture.scenarios['holistic_d9']
    if (result?.ok) {
      expect(result.metrics.round_trips).toBe(1)
    }
  })

  it('bench capture written to bench/<git-sha>.json', () => {
    const outputPath = path.join(BENCH_DIR, `${capture.git_sha}.json`)
    expect(fs.existsSync(outputPath)).toBe(true)
    const written = JSON.parse(fs.readFileSync(outputPath, 'utf8')) as BenchCapture
    expect(written.git_sha).toBe(capture.git_sha)
    expect(Object.keys(written.scenarios).length).toBeGreaterThanOrEqual(1)
  })
})
