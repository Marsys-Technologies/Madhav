/**
 * planner_regression_gate.test.ts — W2-EVAL-B AC.V.3
 *
 * CI-runnable regression gate. Replays a frozen baseline of mock planner
 * responses (`fixtures/regression_baseline.json`) through the smoke runner's
 * scoring path and asserts the published thresholds.
 *
 * The baseline mirrors each golden-set entry's `expected_tools`, so on a
 * correct planner implementation the gate yields recall = 1.00 and
 * precision = 1.00. If the baseline drifts (e.g., a tool is renamed, a
 * required tool is dropped from a mock response) the test fails with a
 * descriptive list of regressed entries.
 *
 * No live LLM calls — `callLlmPlanner` is mocked.
 */
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import { describe, it, expect, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  callPipelinePlanner: vi.fn(),
}))

import {
  runSmoke,
  RECALL_THRESHOLD,
  PRECISION_THRESHOLD,
  type GoldenSet,
  type PlannerFn,
} from './planner_smoke_runner'

interface BaselineEntry {
  id: string
  mock_tool_calls: Array<{
    tool_name: string
    params: Record<string, unknown>
    token_budget: number
    priority: 1 | 2 | 3
    reason: string
  }>
}

interface BaselineFile {
  entries: BaselineEntry[]
}

const here = path.dirname(fileURLToPath(import.meta.url))

function loadJson<T>(relative: string): T {
  return JSON.parse(readFileSync(path.resolve(here, relative), 'utf-8')) as T
}

describe('planner regression gate (mocked)', () => {
  const golden = loadJson<GoldenSet>('planner_golden_set.json')
  const baseline = loadJson<BaselineFile>('fixtures/regression_baseline.json')

  it('baseline covers every planner_golden_set entry by id', () => {
    const goldenIds = new Set(golden.entries.map(e => e.id))
    const baselineIds = new Set(baseline.entries.map(e => e.id))
    expect(goldenIds.size).toBe(baselineIds.size)
    for (const id of goldenIds) {
      expect(baselineIds.has(id)).toBe(true)
    }
  })

  it('avg_tool_recall ≥ 0.80 and avg_tool_precision ≥ 0.90', async () => {
    const idByQuery = new Map(golden.entries.map(e => [e.query, e.id] as const))
    const callsById = new Map(
      baseline.entries.map(e => [e.id, e.mock_tool_calls] as const),
    )

    const mockPlanner: PlannerFn = async query => {
      const id = idByQuery.get(query)
      if (!id) throw new Error(`no golden entry for query: ${query}`)
      const calls = callsById.get(id)
      if (!calls) throw new Error(`no baseline mock for id: ${id}`)
      return { tool_calls: calls.map(c => ({ tool_name: c.tool_name })) }
    }

    const { results, aggregate } = await runSmoke(
      golden,
      mockPlanner,
      'mock-planner',
      'mock-chart',
    )

    const regressed = results.filter(r => !r.pass)
    const summary = regressed
      .map(
        r =>
          `${r.id} recall=${r.tool_recall.toFixed(2)} precision=${r.tool_precision.toFixed(2)} ` +
          `required_hit=${r.required_hit} forbidden_violation=${r.forbidden_violation}` +
          (r.error ? ` error=${r.error}` : ''),
      )
      .join('\n')

    expect(
      aggregate.avg_tool_recall,
      `avg_tool_recall ${aggregate.avg_tool_recall.toFixed(3)} below threshold ${RECALL_THRESHOLD}\nregressed entries:\n${summary}`,
    ).toBeGreaterThanOrEqual(RECALL_THRESHOLD)

    expect(
      aggregate.avg_tool_precision,
      `avg_tool_precision ${aggregate.avg_tool_precision.toFixed(3)} below threshold ${PRECISION_THRESHOLD}\nregressed entries:\n${summary}`,
    ).toBeGreaterThanOrEqual(PRECISION_THRESHOLD)
  })
})
