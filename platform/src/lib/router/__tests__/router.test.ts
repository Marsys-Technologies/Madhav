import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock server-only so the import guard doesn't fail in test environment
vi.mock('server-only', () => ({}))

// Mock the model resolver — we don't want real LLM calls
vi.mock('@/lib/models/resolver', () => ({
  resolveModel: vi.fn(() => ({ id: 'claude-haiku-4-5' })),
  resolveWorkerModel: vi.fn((id: string) => id ?? 'claude-haiku-4-5'),
}))

// Mock generateText at the ai module level
const mockGenerateText = vi.fn()
vi.mock('ai', () => ({
  generateText: (...args: unknown[]) => mockGenerateText(...args),
}))

import { classify } from '../router'
import type { RouterContext } from '../router'

const BASE_CONTEXT: RouterContext = {
  audience_tier: 'client',
  manifest_fingerprint: 'test-fingerprint-abc123',
}

function makeResponse(partial: Record<string, unknown>) {
  const base = {
    query_plan_id: '00000000-0000-0000-0000-000000000000',
    query_text: 'test query',
    domains: [],
    forward_looking: false,
    audience_tier: 'client',
    tools_authorized: ['msr_sql'],
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'single_answer',
    manifest_fingerprint: 'test-fingerprint-abc123',
    schema_version: '1.0',
  }
  return JSON.stringify({ ...base, ...partial })
}

function mockLLMResponse(text: string) {
  mockGenerateText.mockResolvedValueOnce({
    text,
    usage: { promptTokens: 100, completionTokens: 50 },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Router classify() — all 8 query classes', () => {
  it('classifies factual queries', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      domains: [],
      tools_authorized: ['msr_sql'],
      expected_output_shape: 'single_answer',
      planets: ['Mercury'],
    }))

    const plan = await classify('What sign is my Mercury in?', BASE_CONTEXT)

    expect(plan.query_class).toBe('factual')
    expect(plan.expected_output_shape).toBe('single_answer')
    expect(plan.planets).toContain('Mercury')
  })

  it('classifies interpretive queries', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'interpretive',
      domains: ['career'],
      tools_authorized: ['msr_sql', 'pattern_register'],
      expected_output_shape: 'three_interpretation',
    }))

    const plan = await classify('What does my chart say about career?', BASE_CONTEXT)

    expect(plan.query_class).toBe('interpretive')
    expect(plan.domains).toContain('career')
    expect(plan.expected_output_shape).toBe('three_interpretation')
  })

  it('classifies predictive queries', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'predictive',
      domains: ['career'],
      forward_looking: true,
      tools_authorized: ['msr_sql', 'temporal'],
      expected_output_shape: 'time_indexed_prediction',
      dasha_context_required: true,
    }))

    const plan = await classify('When will I see a career change?', BASE_CONTEXT)

    expect(plan.query_class).toBe('predictive')
    expect(plan.forward_looking).toBe(true)
    expect(plan.expected_output_shape).toBe('time_indexed_prediction')
    expect(plan.dasha_context_required).toBe(true)
  })

  it('classifies cross_domain queries', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'cross_domain',
      domains: ['career', 'relationships'],
      tools_authorized: ['msr_sql', 'pattern_register', 'contradiction_register'],
      expected_output_shape: 'three_interpretation',
    }))

    const plan = await classify('How do career and marriage interact in my chart?', BASE_CONTEXT)

    expect(plan.query_class).toBe('cross_domain')
    expect(plan.domains).toContain('career')
    expect(plan.domains).toContain('relationships')
  })

  it('classifies discovery queries', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'discovery',
      domains: [],
      tools_authorized: ['msr_sql', 'pattern_register', 'cluster_atlas'],
      history_mode: 'research',
      expected_output_shape: 'structured_data',
    }))

    const plan = await classify('What unusual patterns does my chart show?', BASE_CONTEXT)

    expect(plan.query_class).toBe('discovery')
    expect(plan.history_mode).toBe('research')
    expect(plan.expected_output_shape).toBe('structured_data')
  })

  it('classifies holistic queries', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'holistic',
      domains: ['career', 'finance', 'relationships', 'health'],
      tools_authorized: ['msr_sql', 'pattern_register', 'resonance_register', 'cluster_atlas'],
      panel_mode: true,
      expected_output_shape: 'three_interpretation',
      dasha_context_required: true,
    }))

    const plan = await classify('Give me a complete reading of my chart.', BASE_CONTEXT)

    expect(plan.query_class).toBe('holistic')
    expect(plan.panel_mode).toBe(true)
    expect(plan.expected_output_shape).toBe('three_interpretation')
  })

  it('classifies remedial queries', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'remedial',
      domains: [],
      tools_authorized: ['msr_sql', 'pattern_register'],
      expected_output_shape: 'single_answer',
      planets: ['Saturn'],
    }))

    const plan = await classify('What remedies should I do for my Saturn?', BASE_CONTEXT)

    expect(plan.query_class).toBe('remedial')
    expect(plan.planets).toContain('Saturn')
  })

  it('classifies cross_native queries', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'cross_native',
      domains: [],
      tools_authorized: ['msr_sql', 'cluster_atlas', 'query_msr_aggregate'],
      history_mode: 'research',
      expected_output_shape: 'structured_data',
    }))

    const plan = await classify(
      'Across charts with similar Saturn placements, what patterns are common?',
      BASE_CONTEXT
    )

    expect(plan.query_class).toBe('cross_native')
    expect(plan.history_mode).toBe('research')
    expect(plan.expected_output_shape).toBe('structured_data')
  })
})

describe('Router — caller-controlled fields are always overridden', () => {
  it('caller audience_tier overrides any LLM value', async () => {
    // LLM tries to set audience_tier to super_admin — caller says client
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      audience_tier: 'super_admin', // LLM attempts to escalate — must be ignored
      tools_authorized: ['msr_sql'],
      expected_output_shape: 'single_answer',
    }))

    const plan = await classify('test', { ...BASE_CONTEXT, audience_tier: 'client' })

    expect(plan.audience_tier).toBe('client')
  })

  it('manifest_fingerprint is always from context', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      manifest_fingerprint: 'llm-injected-fingerprint',
      tools_authorized: ['msr_sql'],
      expected_output_shape: 'single_answer',
    }))

    const plan = await classify('test', BASE_CONTEXT)

    expect(plan.manifest_fingerprint).toBe('test-fingerprint-abc123')
  })

  it('query_plan_id is a valid UUID generated by caller', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      tools_authorized: ['msr_sql'],
      expected_output_shape: 'single_answer',
    }))

    const plan = await classify('test', BASE_CONTEXT)

    expect(plan.query_plan_id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
    )
    // Must NOT be the all-zeros placeholder
    expect(plan.query_plan_id).not.toBe('00000000-0000-0000-0000-000000000000')
  })
})

describe('Router — schema validation occurs', () => {
  it('a valid plan returns router_confidence: 1.0', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      tools_authorized: ['msr_sql'],
      expected_output_shape: 'single_answer',
    }))

    const plan = await classify('test', BASE_CONTEXT)

    expect(plan.router_confidence).toBe(1.0)
  })

  it('schema_version is always "1.0"', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'interpretive',
      domains: ['career'],
      tools_authorized: ['msr_sql'],
      expected_output_shape: 'three_interpretation',
    }))

    const plan = await classify('test', BASE_CONTEXT)

    expect(plan.schema_version).toBe('1.0')
  })
})

describe('Router classify() — FUB-4: vector_search authorization', () => {
  it('interpretive queries include vector_search in tools_authorized', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'interpretive',
      domains: ['career'],
      tools_authorized: ['msr_sql', 'pattern_register', 'resonance_register', 'vector_search'],
      expected_output_shape: 'three_interpretation',
    }))

    const plan = await classify('What does my chart say about my career?', BASE_CONTEXT)

    expect(plan.query_class).toBe('interpretive')
    expect(plan.tools_authorized).toContain('vector_search')
  })

  it('holistic queries include vector_search in tools_authorized', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'holistic',
      domains: ['career', 'finance', 'relationships', 'health'],
      tools_authorized: ['msr_sql', 'pattern_register', 'resonance_register', 'cluster_atlas', 'contradiction_register', 'vector_search'],
      panel_mode: true,
      expected_output_shape: 'three_interpretation',
    }))

    const plan = await classify('Give me a complete reading of my chart.', BASE_CONTEXT)

    expect(plan.query_class).toBe('holistic')
    expect(plan.tools_authorized).toContain('vector_search')
  })

  it('cross_domain queries include vector_search in tools_authorized', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'cross_domain',
      domains: ['career', 'relationships'],
      tools_authorized: ['msr_sql', 'pattern_register', 'resonance_register', 'contradiction_register', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'three_interpretation',
    }))

    const plan = await classify('How do career and marriage interact in my chart?', BASE_CONTEXT)

    expect(plan.query_class).toBe('cross_domain')
    expect(plan.tools_authorized).toContain('vector_search')
  })

  it('predictive queries do NOT include vector_search in tools_authorized', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'predictive',
      domains: ['career'],
      tools_authorized: ['msr_sql', 'temporal', 'resonance_register'],
      forward_looking: true,
      expected_output_shape: 'time_indexed_prediction',
      dasha_context_required: true,
    }))

    const plan = await classify('When will I see a significant career shift?', BASE_CONTEXT)

    expect(plan.query_class).toBe('predictive')
    expect(plan.tools_authorized).not.toContain('vector_search')
  })
})

describe('Router classify() — CGM graph_seed_hints and edge_type_filter extraction', () => {
  it('Mercury support query → PLN.MERCURY seed + SUPPORTS filter', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'interpretive',
      domains: [],
      tools_authorized: ['msr_sql', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'three_interpretation',
      graph_seed_hints: ['PLN.MERCURY'],
      edge_type_filter: ['SUPPORTS'],
    }))

    const plan = await classify('What does my Mercury support in my chart?', BASE_CONTEXT)

    expect(plan.graph_seed_hints).toEqual(['PLN.MERCURY'])
    expect(plan.edge_type_filter).toEqual(['SUPPORTS'])
  })

  it('Saraswati yoga query → YOG.SARASWATI seed, no edge filter', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'interpretive',
      domains: ['spiritual'],
      tools_authorized: ['msr_sql', 'pattern_register', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'three_interpretation',
      graph_seed_hints: ['YOG.SARASWATI'],
    }))

    const plan = await classify('Tell me about my Saraswati yoga.', BASE_CONTEXT)

    expect(plan.graph_seed_hints).toEqual(['YOG.SARASWATI'])
    expect(plan.edge_type_filter).toBeUndefined()
  })

  it('dispositor query → PLN.SATURN seed + DISPOSITED_BY filter', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      domains: [],
      tools_authorized: ['msr_sql', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'single_answer',
      graph_seed_hints: ['PLN.SATURN'],
      edge_type_filter: ['DISPOSITED_BY'],
    }))

    const plan = await classify('Which dispositor governs my Saturn?', BASE_CONTEXT)

    expect(plan.graph_seed_hints).toEqual(['PLN.SATURN'])
    expect(plan.edge_type_filter).toEqual(['DISPOSITED_BY'])
  })

  it('7th house query → HSE.7 seed, no edge filter', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'interpretive',
      domains: ['relationships'],
      tools_authorized: ['msr_sql', 'pattern_register', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'three_interpretation',
      graph_seed_hints: ['HSE.7'],
    }))

    const plan = await classify('What does the 7th house show in my chart?', BASE_CONTEXT)

    expect(plan.graph_seed_hints).toEqual(['HSE.7'])
    expect(plan.edge_type_filter).toBeUndefined()
  })

  it('Saturn dasha + career query → PLN.SATURN and DSH.MD.SATURN in seeds', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'cross_domain',
      domains: ['career'],
      tools_authorized: ['msr_sql', 'pattern_register', 'temporal', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'three_interpretation',
      dasha_context_required: true,
      graph_seed_hints: ['PLN.SATURN', 'DSH.MD.SATURN', 'HSE.10'],
    }))

    const plan = await classify('How does my Saturn dasha affect my career?', BASE_CONTEXT)

    expect(plan.graph_seed_hints).toContain('PLN.SATURN')
    expect(plan.graph_seed_hints).toContain('DSH.MD.SATURN')
  })

  it('karaka contradiction query → KARAKA.DUAL_SYSTEM_DIVERGENCE + CONTRADICTS filter', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'cross_domain',
      domains: [],
      tools_authorized: ['msr_sql', 'contradiction_register', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'three_interpretation',
      graph_seed_hints: ['KARAKA.DUAL_SYSTEM_DIVERGENCE'],
      edge_type_filter: ['CONTRADICTS'],
    }))

    const plan = await classify('Are there contradictions in my karaka assignment?', BASE_CONTEXT)

    expect(plan.graph_seed_hints).toEqual(['KARAKA.DUAL_SYSTEM_DIVERGENCE'])
    expect(plan.edge_type_filter).toEqual(['CONTRADICTS'])
  })

  it('UCN section IV.1 query → UCN.SEC.IV.1 seed', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'interpretive',
      domains: [],
      tools_authorized: ['msr_sql', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'three_interpretation',
      graph_seed_hints: ['UCN.SEC.IV.1'],
    }))

    const plan = await classify('Describe section IV.1 of my unified narrative.', BASE_CONTEXT)

    expect(plan.graph_seed_hints).toEqual(['UCN.SEC.IV.1'])
    expect(plan.edge_type_filter).toBeUndefined()
  })

  it('generic chart query → empty graph_seed_hints', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'holistic',
      domains: ['career', 'finance', 'relationships'],
      tools_authorized: ['msr_sql', 'pattern_register', 'resonance_register', 'vector_search'],
      panel_mode: true,
      expected_output_shape: 'three_interpretation',
      graph_seed_hints: [],
    }))

    const plan = await classify('What does my chart say about life direction?', BASE_CONTEXT)

    expect(plan.graph_seed_hints).toEqual([])
    expect(plan.edge_type_filter).toBeUndefined()
  })

  it('Mars and Saturn interaction query → both PLN seeds', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'cross_domain',
      domains: [],
      tools_authorized: ['msr_sql', 'pattern_register', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'three_interpretation',
      graph_seed_hints: ['PLN.MARS', 'PLN.SATURN'],
    }))

    const plan = await classify('How do my Mars and Saturn interact?', BASE_CONTEXT)

    expect(plan.graph_seed_hints).toContain('PLN.MARS')
    expect(plan.graph_seed_hints).toContain('PLN.SATURN')
    expect(plan.edge_type_filter).toBeUndefined()
  })

  it('Atmakaraka query → KRK.C8.AK seed, factual class', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      domains: [],
      tools_authorized: ['msr_sql', 'cgm_graph_walk', 'vector_search'],
      expected_output_shape: 'single_answer',
      graph_seed_hints: ['KRK.C8.AK'],
    }))

    const plan = await classify("What's my Atmakaraka?", BASE_CONTEXT)

    expect(plan.query_class).toBe('factual')
    expect(plan.graph_seed_hints).toEqual(['KRK.C8.AK'])
  })
})

describe('Router classify() — vector_search_filter emission per query class', () => {
  it('factual class: classifier emits layer=L1 and doc_type=[l1_fact]', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      domains: [],
      tools_authorized: ['msr_sql', 'vector_search'],
      expected_output_shape: 'single_answer',
      planets: ['Mercury'],
      graph_seed_hints: ['PLN.MERCURY'],
      vector_search_filter: { layer: 'L1', doc_type: ['l1_fact'] },
    }))

    const plan = await classify('What sign is my Mercury?', BASE_CONTEXT)

    expect(plan.query_class).toBe('factual')
    expect(plan.vector_search_filter).toEqual({ layer: 'L1', doc_type: ['l1_fact'] })
  })

  it('interpretive class: classifier emits doc_type covering L1+L2.5 and no layer restriction', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'interpretive',
      domains: ['career'],
      tools_authorized: ['msr_sql', 'pattern_register', 'vector_search'],
      expected_output_shape: 'three_interpretation',
      vector_search_filter: { doc_type: ['l1_fact', 'ucn_section', 'msr_signal', 'cdlm_cell'] },
    }))

    const plan = await classify('What does my chart say about career?', BASE_CONTEXT)

    expect(plan.query_class).toBe('interpretive')
    expect(plan.vector_search_filter?.doc_type).toEqual(
      expect.arrayContaining(['l1_fact', 'ucn_section', 'msr_signal', 'cdlm_cell'])
    )
    expect(plan.vector_search_filter?.layer).toBeUndefined()
  })

  it('discovery class: classifier emits doc_type limited to synthesis-layer signals', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'discovery',
      domains: [],
      tools_authorized: ['msr_sql', 'pattern_register', 'cluster_atlas', 'vector_search'],
      history_mode: 'research',
      expected_output_shape: 'structured_data',
      vector_search_filter: { doc_type: ['msr_signal', 'ucn_section', 'domain_report', 'cdlm_cell'] },
    }))

    const plan = await classify('What unusual patterns does my chart show?', BASE_CONTEXT)

    expect(plan.query_class).toBe('discovery')
    expect(plan.vector_search_filter?.doc_type).toEqual(
      expect.arrayContaining(['msr_signal', 'ucn_section', 'domain_report', 'cdlm_cell'])
    )
  })

  it('predictive class: classifier emits doc_type=[l1_fact, msr_signal]', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'predictive',
      domains: ['career'],
      forward_looking: true,
      tools_authorized: ['msr_sql', 'temporal', 'vector_search'],
      expected_output_shape: 'time_indexed_prediction',
      dasha_context_required: true,
      vector_search_filter: { doc_type: ['l1_fact', 'msr_signal'] },
    }))

    const plan = await classify('When is my next career change?', BASE_CONTEXT)

    expect(plan.query_class).toBe('predictive')
    expect(plan.vector_search_filter?.doc_type).toEqual(
      expect.arrayContaining(['l1_fact', 'msr_signal'])
    )
  })
})

describe('Router classify() — chart_facts_query and temporal extension fields (GQ-002 regression)', () => {
  it('GQ-002: factual 7th-house query with chart_facts_query passes schema validation', async () => {
    // Regression: query_plan.schema.json was missing chart_facts_query (and 11 other fields
    // present in the QueryPlan TS interface). The haiku router correctly includes
    // chart_facts_query for placement queries, but the schema rejected it with
    // additionalProperties:false → PipelineError → HTTP 500. Fixed by adding all missing
    // fields to the schema.
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      domains: [],
      tools_authorized: ['msr_sql', 'chart_facts_query', 'vector_search', 'cgm_graph_walk'],
      expected_output_shape: 'single_answer',
      houses: [7],
      graph_seed_hints: ['HSE.7'],
      vector_search_filter: { layer: 'L1', doc_type: ['l1_fact'] },
      chart_facts_query: { category: 'house', house: 7, limit: 10 },
    }))

    const plan = await classify(
      'Which planets are in the 7th house in my birth chart, and what are their degrees?',
      BASE_CONTEXT,
    )

    expect(plan.query_class).toBe('factual')
    expect(plan.expected_output_shape).toBe('single_answer')
    expect(plan.houses).toEqual([7])
    expect(plan.chart_facts_query).toEqual({ category: 'house', house: 7, limit: 10 })
    expect(plan.tools_authorized).toContain('chart_facts_query')
  })

  it('chart_facts_query with category as array passes schema validation', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'factual',
      domains: [],
      tools_authorized: ['msr_sql', 'chart_facts_query'],
      expected_output_shape: 'single_answer',
      chart_facts_query: { category: ['house', 'planet'], limit: 20 },
    }))

    const plan = await classify('What is placed in the 7th house?', BASE_CONTEXT)

    expect(plan.chart_facts_query).toEqual({ category: ['house', 'planet'], limit: 20 })
  })

  it('temporal extension fields pass schema validation', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'predictive',
      domains: [],
      forward_looking: true,
      tools_authorized: ['msr_sql', 'temporal'],
      expected_output_shape: 'time_indexed_prediction',
      dasha_context_required: true,
      time_window: { start: '2026-01-01', end: '2026-12-31' },
      retrograde_query: true,
      retrograde_planet: 'Saturn',
    }))

    const plan = await classify('When is Saturn retrograde next year?', BASE_CONTEXT)

    expect(plan.time_window).toEqual({ start: '2026-01-01', end: '2026-12-31' })
    expect(plan.retrograde_query).toBe(true)
    expect(plan.retrograde_planet).toBe('Saturn')
  })

  it('sade_sati_query and eclipse_query fields pass schema validation', async () => {
    mockLLMResponse(makeResponse({
      query_class: 'predictive',
      domains: [],
      forward_looking: true,
      tools_authorized: ['msr_sql', 'temporal'],
      expected_output_shape: 'time_indexed_prediction',
      sade_sati_query: true,
      eclipse_query: false,
    }))

    const plan = await classify('Am I in Sade Sati right now?', BASE_CONTEXT)

    expect(plan.sade_sati_query).toBe(true)
    expect(plan.eclipse_query).toBe(false)
  })
})
