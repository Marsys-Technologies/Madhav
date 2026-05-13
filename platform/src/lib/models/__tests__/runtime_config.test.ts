import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── vi.hoisted must come before vi.mock calls ────────────────────────────────

const { mockGetFlag, mockQuery } = vi.hoisted(() => ({
  mockGetFlag: vi.fn(),
  mockQuery:   vi.fn(),
}))

vi.mock('server-only', () => ({}))
vi.mock('@/lib/config', () => ({ getFlag: mockGetFlag }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

vi.mock('@/lib/models/registry', async () => {
  const actual = await vi.importActual<typeof import('@/lib/models/registry')>('@/lib/models/registry')
  return {
    ...actual,
    DEFAULT_STACK_ID: 'gemini',
    STACK_ROUTING: {
      gemini: {
        synthesis:        { primary: 'gemini-2.5-pro',    fallback: 'gemini-2.0-flash' },
        planner_deep:     { primary: 'gemini-2.5-pro',    fallback: 'gemini-2.0-flash' },
        planner_fast:     { primary: 'gemini-2.0-flash',  fallback: 'gemini-flash-lite' },
        context_assembly: { primary: 'gemini-2.0-flash',  fallback: 'gemini-flash-lite' },
        worker:           { primary: 'gemini-flash-lite', fallback: 'gemini-2.0-flash' },
        eval_judge:       { primary: 'gemini-2.5-pro',    fallback: 'gemini-2.0-flash' },
        eval_generator:   { primary: 'gemini-2.5-pro',    fallback: 'gemini-2.0-flash' },
        smoke_synth:      { primary: 'gemini-2.0-flash',  fallback: 'gemini-flash-lite' },
        checkpoint_4_5:   { primary: 'gemini-flash-lite', fallback: 'gemini-2.0-flash' },
        checkpoint_5_5:   { primary: 'gemini-flash-lite', fallback: 'gemini-2.0-flash' },
        checkpoint_8_5:   { primary: 'gemini-2.5-pro',   fallback: 'gemini-2.0-flash' },
      },
      nim: {
        synthesis:        { primary: 'nim-llama-70b', fallback: 'nim-llama-8b' },
        planner_deep:     { primary: 'nim-llama-70b', fallback: 'nim-llama-8b' },
        planner_fast:     { primary: 'nim-llama-8b',  fallback: 'nim-llama-70b' },
        context_assembly: { primary: 'nim-llama-8b',  fallback: 'nim-llama-70b' },
        worker:           { primary: 'nim-llama-8b',  fallback: 'nim-llama-70b' },
        eval_judge:       { primary: 'nim-llama-70b', fallback: 'nim-llama-8b' },
        eval_generator:   { primary: 'nim-llama-70b', fallback: 'nim-llama-8b' },
        smoke_synth:      { primary: 'nim-llama-8b',  fallback: 'nim-llama-70b' },
        checkpoint_4_5:   { primary: 'nim-llama-8b',  fallback: 'nim-llama-70b' },
        checkpoint_5_5:   { primary: 'nim-llama-8b',  fallback: 'nim-llama-70b' },
        checkpoint_8_5:   { primary: 'nim-llama-70b', fallback: 'nim-llama-8b' },
      },
    },
  }
})

import {
  getEffectiveStack,
  getEffectiveModel,
  getEffectiveParam,
  invalidateRuntimeConfigCache,
} from '../runtime_config'

// ─── helpers ──────────────────────────────────────────────────────────────────

function makeDbEmpty() {
  mockQuery.mockResolvedValue({ rows: [] })
}

function makeDbWithStack(stack: string) {
  mockQuery.mockImplementation((sql: string) => {
    if (sql.includes('llm_stack_config'))         return Promise.resolve({ rows: [{ active_stack: stack }] })
    return Promise.resolve({ rows: [] })
  })
}

function makeDbWithRouting(stack: string, callType: string, primary: string, fallback: string) {
  mockQuery.mockImplementation((sql: string) => {
    if (sql.includes('llm_stack_config'))          return Promise.resolve({ rows: [] })
    if (sql.includes('llm_stack_routing_override')) return Promise.resolve({ rows: [{ stack, call_type: callType, primary_model: primary, fallback_model: fallback }] })
    return Promise.resolve({ rows: [] })
  })
}

function makeDbWithParam(stack: string, callType: string, paramName: string, paramValue: unknown) {
  mockQuery.mockImplementation((sql: string) => {
    if (sql.includes('llm_param_override')) return Promise.resolve({ rows: [{ stack, call_type: callType, param_name: paramName, param_value: paramValue }] })
    return Promise.resolve({ rows: [] })
  })
}

function makeRequest(headers: Record<string, string> = {}): Request {
  return new Request('http://localhost', { headers })
}

// ─── getEffectiveStack ────────────────────────────────────────────────────────

describe('getEffectiveStack', () => {
  beforeEach(() => {
    invalidateRuntimeConfigCache()
    vi.clearAllMocks()
  })

  it('returns DEFAULT_STACK_ID when AIOPS_OVERRIDES_ENABLED=false', async () => {
    mockGetFlag.mockReturnValue(false)
    const result = await getEffectiveStack()
    expect(result).toBe('gemini')
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns DB stack when flag is on and no header', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithStack('nim')
    const result = await getEffectiveStack()
    expect(result).toBe('nim')
  })

  it('header wins over DB stack', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithStack('nim')
    const req = makeRequest({ 'x-aiops-stack': 'deepseek' })
    const result = await getEffectiveStack(req)
    expect(result).toBe('deepseek')
  })

  it('rejects unknown stack in header and falls through to DB', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithStack('nim')
    const req = makeRequest({ 'x-aiops-stack': 'unknown-stack' })
    const result = await getEffectiveStack(req)
    expect(result).toBe('nim')
  })

  it('returns DEFAULT_STACK_ID when DB is empty', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbEmpty()
    const result = await getEffectiveStack()
    expect(result).toBe('gemini')
  })

  it('cache is valid within TTL — DB called once for two invocations', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithStack('nim')
    await getEffectiveStack()
    await getEffectiveStack()
    // 3 queries per DB hit: stack + routing + param tables
    expect(mockQuery).toHaveBeenCalledTimes(3)
  })

  it('invalidateRuntimeConfigCache forces fresh DB fetch', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithStack('nim')
    await getEffectiveStack()
    invalidateRuntimeConfigCache()
    await getEffectiveStack()
    expect(mockQuery).toHaveBeenCalledTimes(6) // 3+3
  })
})

// ─── getEffectiveModel ────────────────────────────────────────────────────────

describe('getEffectiveModel', () => {
  beforeEach(() => {
    invalidateRuntimeConfigCache()
    vi.clearAllMocks()
  })

  it('returns registry default when flag=false', async () => {
    mockGetFlag.mockReturnValue(false)
    const result = await getEffectiveModel('gemini', 'synthesis', 'primary')
    expect(result).toBe('gemini-2.5-pro')
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns registry fallback value when flag=false', async () => {
    mockGetFlag.mockReturnValue(false)
    const result = await getEffectiveModel('gemini', 'planner_fast', 'fallback')
    expect(result).toBe('gemini-flash-lite')
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('DB override wins over registry when flag=true', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithRouting('gemini', 'synthesis', 'gemini-2.5-exp', 'gemini-2.0-flash')
    const result = await getEffectiveModel('gemini', 'synthesis', 'primary')
    expect(result).toBe('gemini-2.5-exp')
  })

  it('header model wins over DB override', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithRouting('gemini', 'synthesis', 'gemini-2.5-exp', 'gemini-2.0-flash')
    const req = makeRequest({ 'x-aiops-model-synthesis-primary': 'gemini-override-from-header' })
    const result = await getEffectiveModel('gemini', 'synthesis', 'primary', req)
    expect(result).toBe('gemini-override-from-header')
  })

  it('falls back to registry when no DB override and flag=true', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbEmpty()
    const result = await getEffectiveModel('nim', 'planner_deep', 'primary')
    expect(result).toBe('nim-llama-70b')
  })
})

// ─── getEffectiveParam ────────────────────────────────────────────────────────

describe('getEffectiveParam', () => {
  beforeEach(() => {
    invalidateRuntimeConfigCache()
    vi.clearAllMocks()
  })

  it('returns fallback when flag=false', async () => {
    mockGetFlag.mockReturnValue(false)
    const result = await getEffectiveParam('gemini', 'synthesis', 'temperature', 0.7)
    expect(result).toBe(0.7)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('returns DB param when flag=true and DB has value', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithParam('gemini', 'synthesis', 'temperature', 0.2)
    const result = await getEffectiveParam('gemini', 'synthesis', 'temperature', 0.7)
    expect(result).toBe(0.2)
  })

  it('header param wins over DB', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithParam('gemini', 'synthesis', 'temperature', 0.2)
    const req = makeRequest({ 'x-aiops-param-synthesis-temperature': '0.1' })
    const result = await getEffectiveParam('gemini', 'synthesis', 'temperature', 0.7, req)
    expect(result).toBe(0.1)
  })

  it('header param parses JSON objects', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbEmpty()
    const req = makeRequest({ 'x-aiops-param-synthesis-max_output_tokens': '{"value":4096}' })
    const result = await getEffectiveParam('gemini', 'synthesis', 'max_output_tokens', 2048, req)
    expect(result).toEqual({ value: 4096 })
  })

  it('returns fallback when DB is empty and no header', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbEmpty()
    const result = await getEffectiveParam('gemini', 'synthesis', 'temperature', 0.9)
    expect(result).toBe(0.9)
  })
})
