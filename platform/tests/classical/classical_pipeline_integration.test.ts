/**
 * M8-G-S1 — Classical pipeline integration tests (10 tests).
 * Tests: RetrievalTool wrappers, RETRIEVAL_TOOLS registry, QueryPlan
 * classical_grounding query_class, and disclosure filter.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => mockQuery(...args),
}))

const mockFetch = vi.fn()
global.fetch = mockFetch

vi.mock('google-auth-library', () => ({
  GoogleAuth: class {
    async getClient() {
      return { getAccessToken: async () => ({ token: 'mock-token' }) }
    }
  },
}))

const MOCK_EMBEDDING = Array.from({ length: 768 }, (_, i) => i * 0.001)

function makeChunkRow(overrides: Record<string, unknown> = {}) {
  return {
    chunk_id: 'chunk-uuid-1',
    text_key: 'bphs',
    title: 'Brihat Parashara Hora Shastra',
    author: 'Parashara',
    tradition: 'parashari',
    chapter: '26',
    verse_range: '26.19',
    content: 'Saturn exalted in Libra in a Kendra forms Sasha Mahapurusha Yoga.',
    attribution_baseline_confidence: 0.90,
    distance: 0.10,
    ...overrides,
  }
}

function makeAttrRow(overrides: Record<string, unknown> = {}) {
  return {
    attribution_id: 'attr-uuid-1',
    msr_signal_id: 'SIG.MSR.001',
    text_key: 'bphs',
    title: 'Brihat Parashara Hora Shastra',
    author: 'Parashara',
    chapter: '26',
    verse_range: '26.19',
    content: 'Saturn exalted in Libra in a Kendra forms Sasha Mahapurusha Yoga.',
    attribution_type: 'confirms',
    confidence: 0.90,
    confidence_tier: 'HIGH',
    derivation_notes: 'Direct verse reference',
    translation_cross_checked: true,
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  process.env.GCP_PROJECT = 'test-project'
  process.env.VERTEX_AI_LOCATION = 'us-central1'

  mockFetch.mockResolvedValue({
    ok: true,
    json: async () => ({ predictions: [{ embeddings: { values: MOCK_EMBEDDING } }] }),
    text: async () => '',
  })
  mockQuery.mockResolvedValue({ rows: [makeChunkRow()], rowCount: 1 })
})

// ── 1. classical_text_search_tool is registered in RETRIEVAL_TOOLS ──
describe('RETRIEVAL_TOOLS registry', () => {
  it('includes classical_text_search', async () => {
    const { RETRIEVAL_TOOLS } = await import('@/lib/retrieve/index')
    const names = RETRIEVAL_TOOLS.map(t => t.name)
    expect(names).toContain('classical_text_search')
  })

  it('includes classical_attribution_lookup', async () => {
    const { RETRIEVAL_TOOLS } = await import('@/lib/retrieve/index')
    const names = RETRIEVAL_TOOLS.map(t => t.name)
    expect(names).toContain('classical_attribution_lookup')
  })

  it('getTool resolves classical_text_search', async () => {
    const { getTool } = await import('@/lib/retrieve/index')
    const t = getTool('classical_text_search')
    expect(t).toBeDefined()
    expect(t?.name).toBe('classical_text_search')
  })

  it('getTool resolves classical_attribution_lookup', async () => {
    const { getTool } = await import('@/lib/retrieve/index')
    const t = getTool('classical_attribution_lookup')
    expect(t).toBeDefined()
    expect(t?.name).toBe('classical_attribution_lookup')
  })
})

// ── 2. classical_text_search_tool returns valid ToolBundle ──
describe('classical_text_search_tool.retrieve', () => {
  it('produces a ToolBundle with schema_version 1.0', async () => {
    const { tool } = await import('@/lib/retrieve/classical_text_search_tool')
    const plan = makePlan('classical_grounding', ['classical_text_search'])
    const bundle = await tool.retrieve(plan, { query: 'Saturn Libra Sasha yoga', limit: 3 })
    expect(bundle.schema_version).toBe('1.0')
    expect(bundle.tool_name).toBe('classical_text_search')
    expect(bundle.results.length).toBeGreaterThanOrEqual(1)
  })

  it('result.content includes text_key and similarity', async () => {
    const { tool } = await import('@/lib/retrieve/classical_text_search_tool')
    const plan = makePlan('classical_grounding', ['classical_text_search'])
    const bundle = await tool.retrieve(plan, { query: 'Saturn yoga' })
    const parsed = JSON.parse(bundle.results[0].content)
    expect(parsed.text_key).toBe('bphs')
    expect(typeof parsed.similarity).toBe('number')
  })
})

// ── 3. classical_attribution_lookup_tool returns valid ToolBundle ──
describe('classical_attribution_lookup_tool.retrieve', () => {
  it('produces a ToolBundle with tool_name classical_attribution_lookup', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [makeAttrRow()], rowCount: 1 })
    const { tool } = await import('@/lib/retrieve/classical_attribution_lookup_tool')
    const plan = makePlan('classical_grounding', ['classical_attribution_lookup'])
    const bundle = await tool.retrieve(plan, { signal_ids: ['SIG.MSR.001'] })
    expect(bundle.tool_name).toBe('classical_attribution_lookup')
    expect(bundle.results.length).toBe(1)
    expect(bundle.results[0].signal_id).toBe('SIG.MSR.001')
  })

  it('returns empty results for empty signal_ids', async () => {
    const { tool } = await import('@/lib/retrieve/classical_attribution_lookup_tool')
    const plan = makePlan('classical_grounding', ['classical_attribution_lookup'])
    const bundle = await tool.retrieve(plan, { signal_ids: [] })
    expect(bundle.results).toHaveLength(0)
    expect(bundle.result_hash).toMatch(/^sha256:/)
  })
})

// ── 4. classical_grounding as a QueryPlan query_class ──
describe('QueryPlan classical_grounding query_class', () => {
  it('accepts classical_grounding as a valid query_class', () => {
    const plan = makePlan('classical_grounding', ['classical_text_search'])
    expect(plan.query_class).toBe('classical_grounding')
  })
})

// ── 5. Disclosure filter ──
describe('applyClassicalDisclosureFilter', () => {
  it('emits confidence_tier and translation_cross_checked for all tiers', async () => {
    const { applyClassicalDisclosureFilter } = await import(
      '@/lib/retrieve/classical_disclosure_filter'
    )
    const records = [
      {
        attribution_id: 'a1',
        msr_signal_id: 'SIG.MSR.001',
        text_key: 'bphs',
        title: 'Brihat Parashara Hora Shastra',
        author: 'Parashara',
        chapter: '26',
        verse_range: '26.19',
        content: 'Saturn exalted in Libra.',
        attribution_type: 'confirms' as const,
        confidence: 0.90,
        confidence_tier: 'HIGH' as const,
        derivation_notes: null,
        translation_cross_checked: true,
      },
    ]
    const blocks = applyClassicalDisclosureFilter(records, 'client')
    expect(blocks[0].confidence_tier).toBe('HIGH')
    expect(blocks[0].translation_cross_checked).toBe(true)
    expect(blocks[0].content).toContain('Brihat Parashara Hora Shastra')
  })

  it('redacts verse content for public_redacted audience', async () => {
    const { applyClassicalDisclosureFilter } = await import(
      '@/lib/retrieve/classical_disclosure_filter'
    )
    const records = [
      {
        attribution_id: 'a1',
        msr_signal_id: 'SIG.MSR.001',
        text_key: 'bphs',
        title: 'BPHS',
        author: 'Parashara',
        chapter: '26',
        verse_range: '26.19',
        content: 'Saturn exalted in Libra forms Sasha Mahapurusha Yoga.',
        attribution_type: 'confirms' as const,
        confidence: 0.90,
        confidence_tier: 'HIGH' as const,
        derivation_notes: null,
        translation_cross_checked: true,
      },
    ]
    const blocks = applyClassicalDisclosureFilter(records, 'public_redacted')
    expect(blocks[0].content).toContain('acharya_reviewer+')
    expect(blocks[0].content).not.toContain('Sasha Mahapurusha')
  })
})

// ── Helper ──
function makePlan(
  query_class: string,
  tools_authorized: string[],
) {
  return {
    query_plan_id: '00000000-0000-0000-0000-000000000001',
    query_text: 'What classical texts support Saturn yoga?',
    query_class: query_class as 'classical_grounding',
    domains: ['career'],
    forward_looking: false,
    audience_tier: 'client' as const,
    tools_authorized,
    history_mode: 'synthesized' as const,
    panel_mode: false,
    expected_output_shape: 'single_answer' as const,
    manifest_fingerprint: 'test-fingerprint',
    schema_version: '1.0' as const,
  }
}
