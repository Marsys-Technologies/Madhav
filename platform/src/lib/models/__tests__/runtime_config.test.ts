import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── vi.hoisted must come before vi.mock calls ────────────────────────────────

const { mockGetFlag, mockQuery } = vi.hoisted(() => ({
  mockGetFlag: vi.fn(),
  mockQuery:   vi.fn(),
}))

vi.mock('server-only', () => ({}))
vi.mock('@/lib/config', () => ({ getFlag: mockGetFlag }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

// In-process fake of shared_cache so this test stays hermetic and continues
// to assert "1 DB hit per TTL window" semantics post-Memorystore migration.
// Wave 4 unit 4.memorystore_caching commit 3/3.
const { __fakeCache } = vi.hoisted(() => ({
  __fakeCache: new Map<string, { v: unknown; exp: number }>(),
}))
vi.mock('@/lib/cache/shared_cache', () => ({
  buildKey: (surface: string, parts: Record<string, unknown>) =>
    `marsys:${surface}:${JSON.stringify(parts)}`,
  cacheGetOrCompute: async <T,>(
    _surface: string,
    key: string,
    ttlSeconds: number,
    compute: () => Promise<T>,
  ): Promise<T> => {
    const hit = __fakeCache.get(key)
    if (hit && hit.exp > Date.now()) return hit.v as T
    const v = await compute()
    __fakeCache.set(key, { v, exp: Date.now() + ttlSeconds * 1000 })
    return v
  },
  invalidateNamespace: async (_surface: string) => {
    __fakeCache.clear()
    return 0
  },
}))

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

function makeRequest(headers: Record<string, string> = {}): Request {
  return new Request('http://localhost', { headers })
}

// ─── getEffectiveStack ────────────────────────────────────────────────────────

describe('getEffectiveStack', () => {
  beforeEach(() => {
    invalidateRuntimeConfigCache()
    vi.clearAllMocks()
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
    // 1 query per DB hit: stack only
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it('invalidateRuntimeConfigCache forces fresh DB fetch', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbWithStack('nim')
    await getEffectiveStack()
    invalidateRuntimeConfigCache()
    await getEffectiveStack()
    expect(mockQuery).toHaveBeenCalledTimes(2) // 1+1
  })
})

// ─── getEffectiveModel ────────────────────────────────────────────────────────

describe('getEffectiveModel', () => {
  beforeEach(() => {
    invalidateRuntimeConfigCache()
    vi.clearAllMocks()
  })

  it('header model wins over registry default', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbEmpty()
    const req = makeRequest({ 'x-aiops-model-synthesis-primary': 'gemini-override-from-header' })
    const result = await getEffectiveModel('gemini', 'synthesis', 'primary', req)
    expect(result).toBe('gemini-override-from-header')
  })

  it('falls back to registry when DB is empty', async () => {
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

  it('header param wins over fallback', async () => {
    mockGetFlag.mockReturnValue(true)
    makeDbEmpty()
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
