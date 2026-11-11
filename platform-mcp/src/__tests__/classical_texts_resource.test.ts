import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'

type ResourceHandler = (uri: URL, params: { text_key: string }) => Promise<{
  contents: Array<{ uri: string; mimeType: string; text: string }>
}>

const platformUrl = 'https://fixture.invalid'
const token = 'synthetic-service-token'
const uri = new URL('marsys://classical-texts/fixture-text')
const mockFetch = vi.fn<typeof fetch>()
let registerClassicalTextsResource: typeof import('../resources/classical_texts_resource.js').registerClassicalTextsResource

const legacySummary = {
  text_key: 'fixture-text',
  title: 'Synthetic Title',
  author: 'Synthetic Author',
  tradition: 'synthetic-tradition',
  school: 'synthetic-school',
  tier: 2,
  language_original: 'synthetic-language',
  translation_author: 'Synthetic Translator',
  chunk_count: 7,
  attribution_baseline_confidence: '0.500',
}

const legacyHeading = [
  '# Classical Text: Synthetic Title',
  '**text_key:** fixture-text  |  **tradition:** synthetic-tradition  |  **school:** synthetic-school  |  **tier:** 2',
]
const legacyFooter = [
  'Use `read_classical_text` tool with `query` to search this text semantically,',
  'or cite verses as `FIXTURE-TEXT.chapter.verse`.',
]

beforeAll(async () => {
  vi.stubEnv('PLATFORM_URL', platformUrl)
  vi.stubEnv('MCP_INTERNAL_TOKEN', token)
  try {
    ({ registerClassicalTextsResource } = await import('../resources/classical_texts_resource.js'))
  } finally {
    vi.unstubAllEnvs()
  }
})

beforeEach(() => {
  mockFetch.mockReset()
  vi.stubGlobal('fetch', mockFetch)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

function registerHandler(): ResourceHandler {
  const resource = vi.fn<(
    name: string,
    template: { uriTemplate: { toString(): string } },
    handler: ResourceHandler,
  ) => void>()
  registerClassicalTextsResource({ resource } as unknown as McpServer)
  expect(resource).toHaveBeenCalledTimes(1)
  const [call] = resource.mock.calls
  if (!call) throw new Error('Classical resource was not registered')
  const [name, template, handler] = call
  expect(name).toBe('classical-texts')
  expect(template.uriTemplate.toString()).toBe('marsys://classical-texts/{text_key}')
  return handler
}

describe('registered Classical Summary resource', () => {
  it('retains the exact complete legacy markdown and the signed request contract', async () => {
    const timeout = vi.spyOn(AbortSignal, 'timeout')
    mockFetch.mockResolvedValueOnce(Response.json(legacySummary))

    const result = await registerHandler()(uri, { text_key: 'fixture-text' })

    expect(result.contents).toEqual([{
      uri: uri.href,
      mimeType: 'text/markdown',
      text: [
        ...legacyHeading,
        '**Author:** Synthetic Author',
        '**Translation:** Synthetic Translator',
        '**Chunks available:** 7  |  **Attribution confidence baseline:** 0.500',
        ...legacyFooter,
      ].join('\n'),
    }])
    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(mockFetch).toHaveBeenCalledWith(
      `${platformUrl}/api/classical-texts/fixture-text/summary`,
      { headers: { 'x-mcp-internal-token': token }, signal: expect.any(AbortSignal) },
    )
    expect(timeout).toHaveBeenCalledTimes(1)
    expect(timeout).toHaveBeenCalledWith(6000)
  })

  it('renders unavailable count and confidence and omits empty optional metadata', async () => {
    mockFetch.mockResolvedValueOnce(Response.json({
      ...legacySummary,
      author: '',
      language_original: null,
      translation_author: null,
      chunk_count: null,
      attribution_baseline_confidence: null,
    }))

    const result = await registerHandler()(uri, { text_key: 'fixture-text' })

    expect(result.contents).toEqual([{
      uri: uri.href,
      mimeType: 'text/markdown',
      text: [
        ...legacyHeading,
        '**Chunks available:** unavailable  |  **Attribution confidence baseline:** unavailable',
        ...legacyFooter,
      ].join('\n'),
    }])
  })

  it('preserves recorded zero count and zero confidence', async () => {
    mockFetch.mockResolvedValueOnce(Response.json({
      ...legacySummary,
      chunk_count: 0,
      attribution_baseline_confidence: 0,
    }))

    const result = await registerHandler()(uri, { text_key: 'fixture-text' })

    expect(result.contents[0]?.text).toContain(
      '**Chunks available:** 0  |  **Attribution confidence baseline:** 0',
    )
  })

  it('keeps an opaque key on the same route and preserves the unavailable fallback', async () => {
    const textKey = 'opaque/path?key'
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 404 }))

    const result = await registerHandler()(uri, { text_key: textKey })

    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(mockFetch.mock.calls[0]?.[0]).toBe(`${platformUrl}/api/classical-texts/opaque%2Fpath%3Fkey/summary`)
    expect(result.contents).toEqual([{
      uri: uri.href,
      mimeType: 'text/markdown',
      text: '# Classical Text: opaque/path?key\n\nNot found or not yet ingested. ' +
        'Check brahmagyan.texts licensing_audit for status.',
    }])
  })
})
