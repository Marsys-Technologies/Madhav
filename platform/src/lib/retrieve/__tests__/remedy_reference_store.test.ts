import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { QueryPlan } from '../types'
interface Scenario {
  rows?: Record<string, unknown>[]
  queryThrows?: boolean
  queryError?: unknown
  endThrows?: boolean
  endError?: unknown
  gate?: Promise<void>
  result?: {
    rows: Record<string, unknown>[]
  }
  endAction?: () => void
}
interface CapturedPool {
  config: Record<string, unknown>
  queries: Array<[
    string,
    unknown[]
  ]>
  ended: number
}
const state = vi.hoisted(() => ({
  instances: [] as CapturedPool[], scenarios: [] as Scenario[]
}))
vi.mock('pg', () => ({
  Pool: class {
    config: Record<string, unknown>
    queries: Array<[
      string,
      unknown[]
    ]> = []
    ended = 0
    scenario: Scenario
    constructor(config: Record<string, unknown>) {
      this.config = config
      this.scenario = state.scenarios.shift() ?? {}
      state.instances.push(this)
    }
    async query(sql: string, params: unknown[]) {
      this.queries.push([sql, params])
      if (this.scenario.gate)
        await this.scenario.gate
      if (this.scenario.queryThrows)
        throw this.scenario.queryError
      return this.scenario.result ?? {
        rows: this.scenario.rows ?? []
      }
    }
    async end() {
      this.ended++
      this.scenario.endAction?.()
      if (this.scenario.endThrows)
        throw this.scenario.endError
    }
  },
}))
vi.mock('../pyhora_natal_positions', () => ({
  tool: {
    name: 'fixture_natal'
  }
}))
vi.mock('../pyhora_dasha_periods', () => ({
  tool: {
    name: 'fixture_dasha'
  }
}))
vi.mock('../pyhora_special_lagnas', () => ({
  tool: {
    name: 'fixture_lagna'
  }
}))
vi.mock('../sutravali_tools', () => ({
  SUTRAVALI_RETRIEVAL_TOOLS: []
}))
vi.mock('../../contract', () => ({
  CONTRACT_CATALOG: [],
  CONTRACT_CATALOG_BY_NAME: {},
  CONTRACT_TOOL_NAMES: [],
}))
import * as current from '../remedy_tools'
import { REMEDY_TOOLS, getTool } from '../index'
const plan: QueryPlan = {
  query_plan_id: 'fixture-plan',
  query_text: 'fixture',
  query_class: 'remedial',
  domains: [],
  forward_looking: false,
  audience_tier: 'client',
  tools_authorized: [],
  history_mode: 'research',
  panel_mode: false,
  expected_output_shape: 'structured_data',
  manifest_fingerprint: 'fixture',
  schema_version: '1.0',
}
const names = [
  'queryRemedies',
  'queryRemediesForChart',
  'listRemediesByCategory',
  'readRemedy',
  'queryTantricRemedies',
  'queryRemediesByPlanet',
  'queryMantras',
] as const

function reset() {
  state.instances.length = 0
  state.scenarios.length = 0
}

beforeEach(() => {
  reset()
  vi.stubEnv('DATABASE_URL', 'postgres://fixture_reader:fixture@127.0.0.1/fixture')
  vi.spyOn(Date, 'now').mockReturnValue(1000)
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.restoreAllMocks()
})

describe('remedy reference ownership and lifecycle', () => {
  it('observes result rows after awaited teardown, matching the old driver boundary', async () => {
    reset()
    const result = { rows: [{ remedy_id: 'fixture-before-end' }] }
    state.scenarios.push({
      result,
      endAction: () => {
        result.rows = [{ remedy_id: 'fixture-after-end' }]
      },
    })
    const bundle = await current.readRemedy.retrieve(plan)
    expect(bundle.results[0].content).toBe('{"remedy_id":"fixture-after-end"}')
    expect(state.instances[0].ended).toBe(1)
  })

  it('an end failure precedes a later result-row accessor failure', async () => {
    reset()
    const result = {
      get rows(): Record<string, unknown>[] {
        throw new Error('fixture-row-access')
      },
    }
    state.scenarios.push({
      result,
      endThrows: true,
      endError: new Error('fixture-end-first'),
    })
    await expect(current.readRemedy.retrieve(plan)).rejects.toThrow('remedy_tools queryDb failed: Error: fixture-end-first')
    expect(state.instances[0].ended).toBe(1)
  })

  it('closes the owned pool after a query rejection while preserving its wrapped error', async () => {
    const error = new Error('fixture-query-error')
    state.scenarios.push({
      queryThrows: true,
      queryError: error,
    })
    await expect(current.queryRemedies.retrieve(plan)).rejects.toThrow('remedy_tools queryDb failed: Error: fixture-query-error')
    expect(state.instances[0].ended).toBe(1)
  })

  it('query rejection wins if teardown also rejects', async () => {
    state.scenarios.push({
      queryThrows: true,
      queryError: new Error('fixture-primary'),
      endThrows: true,
      endError: new Error('fixture-cleanup'),
    })
    await expect(current.readRemedy.retrieve(plan)).rejects.toThrow('remedy_tools queryDb failed: Error: fixture-primary')
    expect(state.instances[0].ended).toBe(1)
  })

  it('end rejection after a successful query keeps the original rejection behavior', async () => {
    reset()
    state.scenarios.push({
      endThrows: true,
      endError: new Error('fixture-end'),
    })
    await expect(current.readRemedy.retrieve(plan)).rejects.toThrow('remedy_tools queryDb failed: Error: fixture-end')
    expect(state.instances[0].ended).toBe(1)
  })

  it.each([undefined, null, false, 0, 'fixture-string'])('handles thrown non-Error values without mistaking success (%s)', async (value) => {
    reset()
    state.scenarios.push({
      queryThrows: true,
      queryError: value,
      endThrows: true,
      endError: new Error('fixture-end'),
    })
    await expect(current.readRemedy.retrieve(plan)).rejects.toThrow(`remedy_tools queryDb failed: ${String(value)}`)
    expect(state.instances[0].ended).toBe(1)
  })

  it.each([undefined, ''])('missing URL never falls back to PG environment or CloudSQL (%s)', async (url) => {
    vi.stubEnv('DATABASE_URL', url)
    vi.stubEnv('PGHOST', 'fixture-host')
    vi.stubEnv('PGUSER', 'fixture-other-role')
    vi.stubEnv('INSTANCE_CONNECTION_NAME', 'fixture-instance')
    reset()
    await expect(current.readRemedy.retrieve(plan)).rejects.toThrow('remedy_tools queryDb failed: Error: DATABASE_URL not set')
    expect(state.instances).toHaveLength(0)
  })

  it('parallel calls have independent URL snapshots, pools and awaited cleanup', async () => {
    let firstDone!: () => void
    let secondDone!: () => void
    const a = new Promise<void>(resolve => {
      firstDone = resolve
    })
    const b = new Promise<void>(resolve => {
      secondDone = resolve
    })
    state.scenarios.push({
      gate: a
    }, {
      gate: b
    })
    const first = current.readRemedy.retrieve(plan, {
      remedy_id: 'fixture-a'
    })
    await vi.waitFor(() => expect(state.instances).toHaveLength(1))
    vi.stubEnv('DATABASE_URL', 'postgres://fixture_second_role:fixture@127.0.0.1/fixture-second')
    const second = current.queryMantras.retrieve(plan)
    await vi.waitFor(() => expect(state.instances).toHaveLength(2))
    expect(state.instances[0]).not.toBe(state.instances[1])
    expect(state.instances.every(p => p.config.max === 5)).toBe(true)
    expect(state.instances[0].config.connectionString).toContain('fixture_reader:')
    expect(state.instances[1].config.connectionString).toContain('fixture_second_role:')
    expect(state.instances.map(p => p.ended)).toEqual([0, 0])
    secondDone()
    await second
    expect(state.instances.map(p => p.ended)).toEqual([0, 1])
    firstDone()
    await first
    expect(state.instances.map(p => p.ended)).toEqual([1, 1])
  })

  it('keeps every public and legacy facade tool object and lookup name', () => {
    expect(REMEDY_TOOLS).toBe(current.REMEDY_TOOLS)
    expect(REMEDY_TOOLS).toHaveLength(7)
    for (const name of names)
      expect(getTool(current[name].name)).toBe(current[name])
    expect(getTool('unknown-fixture-tool')).toBeUndefined()
  })

  it('for-chart remains an honest global reference lookup with unchanged binds', async () => {
    await current.queryRemediesForChart.retrieve(plan, {
      chart_id: 'ignored-fixture',
      affliction: 'fixture-affliction',
    })
    const [sql, values] = state.instances[0].queries[0]
    expect(sql).not.toContain('chart_id')
    expect(values).toEqual(['%fixture-affliction%', 5])
    expect(state.instances[0].queries).toHaveLength(1)
    expect(sql).toContain("scaffold_status = 'live'")
  })
})
