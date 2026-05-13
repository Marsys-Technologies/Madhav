import { describe, it, expect, vi, beforeEach } from 'vitest'

// ─── global fetch mock ────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ─── helpers ──────────────────────────────────────────────────────────────────

function okResponse(body: unknown): Response {
  return new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } })
}

function statusResponse(status: number): Response {
  return new Response('', { status })
}

function abortError(): Promise<never> {
  const e = Object.assign(new Error('AbortError'), { name: 'AbortError' })
  return Promise.reject(e)
}

function networkError(): Promise<never> {
  return Promise.reject(new Error('network fail'))
}

// ─────────────────────────────────────────────────────────────────────────────
// NIM
// ─────────────────────────────────────────────────────────────────────────────

describe('fetchNimCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('NVIDIA_NIM_API_KEY', 'nim-test-key')
  })

  it('returns unconfigured when env key is missing', async () => {
    vi.unstubAllEnvs()
    const { fetchNimCatalog } = await import('../fetcher_nim')
    const result = await fetchNimCatalog()
    expect(result.status).toBe('unconfigured')
    expect(result.models).toHaveLength(0)
  })

  it('returns ok with models on 200', async () => {
    const { fetchNimCatalog } = await import('../fetcher_nim')
    mockFetch.mockResolvedValueOnce(okResponse({ data: [{ id: 'meta/llama-3.1-70b', owned_by: 'meta' }] }))
    const result = await fetchNimCatalog()
    expect(result.status).toBe('ok')
    expect(result.models).toHaveLength(1)
  })

  it('returns auth_fail on 401', async () => {
    const { fetchNimCatalog } = await import('../fetcher_nim')
    mockFetch.mockResolvedValueOnce(statusResponse(401))
    const result = await fetchNimCatalog()
    expect(result.status).toBe('auth_fail')
  })

  it('returns auth_fail on 403', async () => {
    const { fetchNimCatalog } = await import('../fetcher_nim')
    mockFetch.mockResolvedValueOnce(statusResponse(403))
    const result = await fetchNimCatalog()
    expect(result.status).toBe('auth_fail')
  })

  it('returns timeout on AbortError', async () => {
    const { fetchNimCatalog } = await import('../fetcher_nim')
    mockFetch.mockImplementationOnce(() => abortError())
    const result = await fetchNimCatalog()
    expect(result.status).toBe('timeout')
  })

  it('returns error on network failure', async () => {
    const { fetchNimCatalog } = await import('../fetcher_nim')
    mockFetch.mockImplementationOnce(() => networkError())
    const result = await fetchNimCatalog()
    expect(result.status).toBe('error')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Gemini
// ─────────────────────────────────────────────────────────────────────────────

describe('fetchGeminiCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('GOOGLE_API_KEY', 'google-test-key')
  })

  it('returns unconfigured when env key is missing', async () => {
    vi.unstubAllEnvs()
    const { fetchGeminiCatalog } = await import('../fetcher_gemini')
    const result = await fetchGeminiCatalog()
    expect(result.status).toBe('unconfigured')
  })

  it('strips models/ prefix from model names', async () => {
    const { fetchGeminiCatalog } = await import('../fetcher_gemini')
    mockFetch.mockResolvedValueOnce(okResponse({ models: [{ name: 'models/gemini-2.5-pro', displayName: 'Gemini 2.5 Pro' }] }))
    const result = await fetchGeminiCatalog()
    expect(result.status).toBe('ok')
    const entry = result.models[0] as unknown as { id: string }
    expect(entry.id).toBe('gemini-2.5-pro')
  })

  it('returns auth_fail on 401', async () => {
    const { fetchGeminiCatalog } = await import('../fetcher_gemini')
    mockFetch.mockResolvedValueOnce(statusResponse(401))
    const result = await fetchGeminiCatalog()
    expect(result.status).toBe('auth_fail')
  })

  it('returns timeout on AbortError', async () => {
    const { fetchGeminiCatalog } = await import('../fetcher_gemini')
    mockFetch.mockImplementationOnce(() => abortError())
    const result = await fetchGeminiCatalog()
    expect(result.status).toBe('timeout')
  })

  it('returns error on non-ok status', async () => {
    const { fetchGeminiCatalog } = await import('../fetcher_gemini')
    mockFetch.mockResolvedValueOnce(statusResponse(500))
    const result = await fetchGeminiCatalog()
    expect(result.status).toBe('error')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// DeepSeek
// ─────────────────────────────────────────────────────────────────────────────

describe('fetchDeepseekCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('DEEPSEEK_API_KEY', 'deepseek-test-key')
  })

  it('returns unconfigured when env key is missing', async () => {
    vi.unstubAllEnvs()
    const { fetchDeepseekCatalog } = await import('../fetcher_deepseek')
    const result = await fetchDeepseekCatalog()
    expect(result.status).toBe('unconfigured')
  })

  it('returns ok with models on 200', async () => {
    const { fetchDeepseekCatalog } = await import('../fetcher_deepseek')
    mockFetch.mockResolvedValueOnce(okResponse({ data: [{ id: 'deepseek-chat' }, { id: 'deepseek-reasoner' }] }))
    const result = await fetchDeepseekCatalog()
    expect(result.status).toBe('ok')
    expect(result.models).toHaveLength(2)
  })

  it('returns auth_fail on 403', async () => {
    const { fetchDeepseekCatalog } = await import('../fetcher_deepseek')
    mockFetch.mockResolvedValueOnce(statusResponse(403))
    const result = await fetchDeepseekCatalog()
    expect(result.status).toBe('auth_fail')
  })

  it('returns timeout on AbortError', async () => {
    const { fetchDeepseekCatalog } = await import('../fetcher_deepseek')
    mockFetch.mockImplementationOnce(() => abortError())
    const result = await fetchDeepseekCatalog()
    expect(result.status).toBe('timeout')
  })

  it('returns error on network failure', async () => {
    const { fetchDeepseekCatalog } = await import('../fetcher_deepseek')
    mockFetch.mockImplementationOnce(() => networkError())
    const result = await fetchDeepseekCatalog()
    expect(result.status).toBe('error')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// OpenAI
// ─────────────────────────────────────────────────────────────────────────────

describe('fetchOpenaiCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('OPENAI_API_KEY', 'openai-test-key')
  })

  it('returns unconfigured when env key is missing', async () => {
    vi.unstubAllEnvs()
    const { fetchOpenaiCatalog } = await import('../fetcher_openai')
    const result = await fetchOpenaiCatalog()
    expect(result.status).toBe('unconfigured')
  })

  it('filters to gpt-* models only', async () => {
    const { fetchOpenaiCatalog } = await import('../fetcher_openai')
    mockFetch.mockResolvedValueOnce(okResponse({
      data: [
        { id: 'gpt-4o' },
        { id: 'whisper-1' },
        { id: 'dall-e-3' },
        { id: 'gpt-3.5-turbo' },
      ],
    }))
    const result = await fetchOpenaiCatalog()
    expect(result.status).toBe('ok')
    expect(result.models).toHaveLength(2)
    const ids = (result.models as unknown as Array<{ id: string }>).map(m => m.id)
    expect(ids).toContain('gpt-4o')
    expect(ids).toContain('gpt-3.5-turbo')
    expect(ids).not.toContain('whisper-1')
  })

  it('returns auth_fail on 401', async () => {
    const { fetchOpenaiCatalog } = await import('../fetcher_openai')
    mockFetch.mockResolvedValueOnce(statusResponse(401))
    const result = await fetchOpenaiCatalog()
    expect(result.status).toBe('auth_fail')
  })

  it('returns timeout on AbortError', async () => {
    const { fetchOpenaiCatalog } = await import('../fetcher_openai')
    mockFetch.mockImplementationOnce(() => abortError())
    const result = await fetchOpenaiCatalog()
    expect(result.status).toBe('timeout')
  })

  it('returns error on non-ok status', async () => {
    const { fetchOpenaiCatalog } = await import('../fetcher_openai')
    mockFetch.mockResolvedValueOnce(statusResponse(429))
    const result = await fetchOpenaiCatalog()
    expect(result.status).toBe('error')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Anthropic
// ─────────────────────────────────────────────────────────────────────────────

describe('fetchAnthropicCatalog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('ANTHROPIC_API_KEY', 'anthropic-test-key')
  })

  it('returns unconfigured when env key is missing', async () => {
    vi.unstubAllEnvs()
    const { fetchAnthropicCatalog } = await import('../fetcher_anthropic')
    const result = await fetchAnthropicCatalog()
    expect(result.status).toBe('unconfigured')
  })

  it('returns ok and maps display_name to label', async () => {
    const { fetchAnthropicCatalog } = await import('../fetcher_anthropic')
    mockFetch.mockResolvedValueOnce(okResponse({
      data: [{ id: 'claude-opus-4-7', display_name: 'Claude Opus 4.7' }],
    }))
    const result = await fetchAnthropicCatalog()
    expect(result.status).toBe('ok')
    expect(result.models).toHaveLength(1)
    const entry = result.models[0] as unknown as { id: string; label: string }
    expect(entry.id).toBe('claude-opus-4-7')
    expect(entry.label).toBe('Claude Opus 4.7')
  })

  it('returns auth_fail on 401', async () => {
    const { fetchAnthropicCatalog } = await import('../fetcher_anthropic')
    mockFetch.mockResolvedValueOnce(statusResponse(401))
    const result = await fetchAnthropicCatalog()
    expect(result.status).toBe('auth_fail')
  })

  it('returns timeout on AbortError', async () => {
    const { fetchAnthropicCatalog } = await import('../fetcher_anthropic')
    mockFetch.mockImplementationOnce(() => abortError())
    const result = await fetchAnthropicCatalog()
    expect(result.status).toBe('timeout')
  })

  it('returns error on network failure', async () => {
    const { fetchAnthropicCatalog } = await import('../fetcher_anthropic')
    mockFetch.mockImplementationOnce(() => networkError())
    const result = await fetchAnthropicCatalog()
    expect(result.status).toBe('error')
  })
})
