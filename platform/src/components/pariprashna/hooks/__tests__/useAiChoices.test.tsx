import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useAiChoices } from '../useAiChoices'

const CONVERSATION_ID = '11111111-1111-4111-8111-111111111111'
const CONNECTION_ID = '22222222-2222-4222-8222-222222222222'
const CONFIG_ID = '33333333-3333-4333-8333-333333333333'

const aggregate = {
  connections: [{ id: CONNECTION_ID, providerId: 'openai', name: 'Personal OpenAI', maskedSuffix: '•••1234',
    validationState: 'validated', confirmedValid: true, lastValidatedAt: null, lastCheckedAt: null, lastErrorCode: null, deletedAt: null }],
  models: [{ connectionId: CONNECTION_ID, modelId: 'gpt-safe', displayName: 'GPT Safe',
    compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: false,
    supportsStructuredOutput: true, available: true }],
  configurations: [{ id: CONFIG_ID, name: 'Research quartet', version: 2, deletedAt: null, roles: {
    synthesizer: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
    planner: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
    deep_planner: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
    worker: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
  }}],
  defaultChoice: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' },
  validationDisclosure: 'tiny charge',
}

const clis = { clis: [
  { cliId: 'claude_code', productName: 'Claude Code', state: 'reachable', detectedProduct: 'Claude Code',
    detectedVersion: '2.1.56', lastCheckedAt: null, models: [{ modelId: null, displayName: 'Built-in default',
      compatibleRoles: ['synthesizer', 'planner', 'deep_planner', 'worker'], supportsTools: false,
      supportsStructuredOutput: true, isBuiltinDefault: true }] },
  { cliId: 'codex', productName: 'Codex CLI', state: 'not_granted' },
] }

function response(body: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } }))
}

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks() })

describe('useAiChoices', () => {
  it('starts with symbolic Default, then offers exactly the three explicit groups in order', async () => {
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL) => {
      if (String(url) === '/api/ai-console') return response(aggregate)
      if (String(url) === '/api/ai-console/clis') return response(clis)
      throw new Error(`unexpected ${url}`)
    }))
    const { result } = renderHook(() => useAiChoices(null, true))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.selection).toEqual({ kind: 'default' })
    expect(result.current.options.map(option => option.group)).toEqual([
      null, 'Provider connections', 'Custom configurations', 'Local CLIs',
    ])
    expect(result.current.options[0].label).toBe('Default — Personal OpenAI · GPT Safe')
    expect(result.current.options.some(option => option.label.includes('Codex'))).toBe(false)
    expect(result.current.canSubmit).toBe(true)
  })

  it('refreshes the live Default label on window focus and picker-open refresh', async () => {
    let aggregateView = aggregate
    let failRefresh = false
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL) => {
      if (failRefresh) return Promise.reject(new Error('offline'))
      if (String(url) === '/api/ai-console') return response(aggregateView)
      if (String(url) === '/api/ai-console/clis') return response(clis)
      throw new Error(`unexpected ${url}`)
    }))
    const { result } = renderHook(() => useAiChoices(null, true))
    await waitFor(() => expect(result.current.options[0]?.label).toBe('Default — Personal OpenAI · GPT Safe'))

    aggregateView = {
      ...aggregate,
      connections: [{ ...aggregate.connections[0], name: 'Renamed OpenAI' }],
    }
    act(() => window.dispatchEvent(new Event('focus')))
    await waitFor(() => expect(result.current.options[0]?.label).toBe('Default — Renamed OpenAI · GPT Safe'))

    aggregateView = {
      ...aggregate,
      connections: [{ ...aggregate.connections[0], name: 'Latest OpenAI' }],
    }
    act(() => result.current.refresh())
    await waitFor(() => expect(result.current.options[0]?.label).toBe('Default — Latest OpenAI · GPT Safe'))

    failRefresh = true
    act(() => result.current.refresh())
    await waitFor(() => expect(result.current.statusMessage).toMatch(/could not be loaded/i))
    expect(result.current.canSubmit).toBe(false)
  })

  it('keeps pre-conversation intent local, then acknowledges it through PUT after a real server ID exists', async () => {
    const explicit = { kind: 'explicit', choice: { kind: 'custom_configuration', configurationId: CONFIG_ID } } as const
    const calls: Array<[string, RequestInit | undefined]> = []
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      calls.push([String(url), init])
      if (String(url) === '/api/ai-console') return response(aggregate)
      if (String(url) === '/api/ai-console/clis') return response(clis)
      if (String(url).endsWith('/ai-selection') && init?.method === 'PUT') return response({
        selection: explicit, availability: 'ready', label: 'Research quartet', resolvedLabel: null, remediation: null,
      })
      throw new Error(`unexpected ${url}`)
    }))
    const { result, rerender } = renderHook(({ id }) => useAiChoices(id, true), { initialProps: { id: null as string | null } })
    await waitFor(() => expect(result.current.loading).toBe(false))
    await act(() => result.current.select(explicit))
    expect(result.current.selection).toEqual(explicit)
    expect(calls.some(([url]) => url.endsWith('/ai-selection'))).toBe(false)

    rerender({ id: CONVERSATION_ID })
    expect(result.current.canSubmit).toBe(false)
    await waitFor(() => expect(calls.some(([url, init]) => url.endsWith('/ai-selection') && init?.method === 'PUT')).toBe(true))
    const put = calls.find(([url, init]) => url.endsWith('/ai-selection') && init?.method === 'PUT')!
    expect(JSON.parse(String(put[1]?.body))).toEqual(explicit)
    await waitFor(() => expect(result.current.mutationPending).toBe(false))
    expect(result.current.selection).toEqual(explicit)
  })

  it('retains the last server-confirmed selection when a later PUT fails', async () => {
    const confirmed = { kind: 'explicit', choice: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'gpt-safe' } } as const
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url) === '/api/ai-console') return response(aggregate)
      if (String(url) === '/api/ai-console/clis') return response(clis)
      if (String(url).endsWith('/ai-selection') && init?.method === 'PUT') {
        return response({ error: 'AI_CHOICE_BROKEN' }, 409)
      }
      if (String(url).endsWith('/ai-selection')) return response({ selection: confirmed, availability: 'ready', label: 'Personal OpenAI · GPT Safe', resolvedLabel: null, remediation: null })
      throw new Error(`unexpected ${url}`)
    }))
    const { result } = renderHook(() => useAiChoices(CONVERSATION_ID, true))
    await waitFor(() => expect(result.current.loading).toBe(false))
    const replacement = { kind: 'default' } as const
    await act(() => result.current.select(replacement))
    await waitFor(() => expect(result.current.statusMessage).toMatch(/could not be saved/i))
    expect(result.current.selection).toEqual(confirmed)
  })

  it('blocks without a usable default and preserves a selected broken identity as a repair row', async () => {
    const broken = { kind: 'explicit', choice: { kind: 'provider_model', connectionId: CONNECTION_ID, modelId: 'removed' } } as const
    vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL) => {
      if (String(url) === '/api/ai-console') return response({ ...aggregate, defaultChoice: null })
      if (String(url) === '/api/ai-console/clis') return response(clis)
      if (String(url).endsWith('/ai-selection')) return response({
        selection: broken, availability: 'default_required', label: 'Personal OpenAI · removed',
        resolvedLabel: null, remediation: 'Choose a default in AI Console before asking a question.',
      })
      throw new Error(`unexpected ${url}`)
    }))
    const { result } = renderHook(() => useAiChoices(CONVERSATION_ID, true))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.canSubmit).toBe(false)
    expect(result.current.selection).toEqual(broken)
    expect(result.current.options.find(option => option.key.includes(':removed'))).toMatchObject({
      label: 'Personal OpenAI · removed', disabled: true,
    })
  })

  it('falls back to the byte-compatible legacy picker when the aggregate route is flag-off 404', async () => {
    vi.stubGlobal('fetch', vi.fn(() => response({ error: 'not_found' }, 404)))
    const { result } = renderHook(() => useAiChoices(null, true))
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.legacy).toBe(true)
    expect(result.current.options).toEqual([])
  })
})
