import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const mockGetFlag = vi.fn()
vi.mock('@/lib/config/index', () => ({ getFlag: (...args: unknown[]) => mockGetFlag(...args) }))

vi.mock('@/lib/telemetry/index', () => ({
  telemetry: {
    recordMetric: vi.fn(),
    recordLatency: vi.fn(),
    recordError: vi.fn(),
  },
}))

// Mock storage — default returns no rows (unit-safe; DB not available)
const mockQuery = vi.fn().mockResolvedValue({ rows: [] })
vi.mock('@/lib/storage', () => ({
  getStorageClient: () => ({ query: (...args: unknown[]) => mockQuery(...args) }),
}))

import {
  detectDashaRelevance,
  extractDashaClaims,
  validateClaimsAgainstChartFacts,
  runCheckpointDasha,
} from '../checkpoint_dasha'
import { CheckpointHaltError } from '../types'
import type { CheckpointDashaInput, DashaClaim } from '../types'

function makeQueryPlan(toolNames: string[] = []): CheckpointDashaInput['query_plan'] {
  return {
    query_plan_id: 'test-qp-001',
    query_text: 'test query',
    query_class: 'predictive',
    domains: [],
    forward_looking: true,
    audience_tier: 'super_admin',
    history_mode: 'synthesized',
    panel_mode: false,
    expected_output_shape: 'time_indexed_prediction',
    manifest_fingerprint: 'fp-test',
    schema_version: '1.0',
    tools_authorized: toolNames,
    tool_calls: toolNames.map(name => ({ tool_name: name, params: {} })),
  } as unknown as CheckpointDashaInput['query_plan']
}

function makeInput(overrides: Partial<CheckpointDashaInput> = {}): CheckpointDashaInput {
  return {
    query: "what's my next mahadasha?",
    query_plan: makeQueryPlan(['query_dasha_periods']),
    synthesized_text:
      'Your next MD is Ketu (→ DSH.V.024, 2027-08-21 to 2034-08-18). After that Venus MD begins.',
    ...overrides,
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockGetFlag.mockReturnValue(false)
  mockQuery.mockResolvedValue({ rows: [] })
})

// ─────────────────────────────────────────────────────────────────────────────
// detectDashaRelevance
// ─────────────────────────────────────────────────────────────────────────────

describe('detectDashaRelevance', () => {
  it('returns true when query contains "mahadasha"', () => {
    expect(
      detectDashaRelevance({
        query: "what's my next mahadasha?",
        query_plan: makeQueryPlan(),
      }),
    ).toBe(true)
  })

  it('returns true when query contains "MD" abbreviation', () => {
    expect(
      detectDashaRelevance({
        query: 'which MD am I running?',
        query_plan: makeQueryPlan(),
      }),
    ).toBe(true)
  })

  it('returns true when query_plan has query_dasha_periods tool_call', () => {
    expect(
      detectDashaRelevance({
        query: 'tell me about my chart',
        query_plan: makeQueryPlan(['query_dasha_periods']),
      }),
    ).toBe(true)
  })

  it('returns true when query_plan has temporal with dasha_context_required=true', () => {
    const plan = {
      ...makeQueryPlan(),
      tool_calls: [{ tool_name: 'temporal', params: { dasha_context_required: true } }],
    } as CheckpointDashaInput['query_plan']
    expect(
      detectDashaRelevance({ query: 'what is happening now?', query_plan: plan }),
    ).toBe(true)
  })

  it('returns false for a non-dasha query with no dasha tools', () => {
    expect(
      detectDashaRelevance({
        query: "what's my lagna?",
        query_plan: makeQueryPlan(['msr_sql']),
      }),
    ).toBe(false)
  })

  it('returns false for a career query with no dasha signal', () => {
    expect(
      detectDashaRelevance({
        query: 'explain my career prospects in the next few years',
        query_plan: makeQueryPlan(['msr_sql', 'cgm_graph_walk']),
      }),
    ).toBe(false)
  })

  it('returns true when query contains "yogini"', () => {
    expect(
      detectDashaRelevance({
        query: 'what is my current yogini dasha?',
        query_plan: makeQueryPlan(),
      }),
    ).toBe(true)
  })

  it('returns true when query contains "chara" (Jaimini)', () => {
    expect(
      detectDashaRelevance({
        query: 'which sign is my chara dasha lord?',
        query_plan: makeQueryPlan(),
      }),
    ).toBe(true)
  })

  it('returns true when query contains "jaimini"', () => {
    expect(
      detectDashaRelevance({
        query: 'explain my jaimini dasha sequence',
        query_plan: makeQueryPlan(),
      }),
    ).toBe(true)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// extractDashaClaims
// ─────────────────────────────────────────────────────────────────────────────

describe('extractDashaClaims', () => {
  it('captures "Saturn MD next" as a claim with temporal="next" and no citation', () => {
    const text = 'After Mercury MD ends, Saturn MD next will be a significant period.'
    const claims = extractDashaClaims(text)
    const saturnClaim = claims.find(c => c.lord === 'Saturn')
    expect(saturnClaim).toBeDefined()
    expect(saturnClaim!.has_citation).toBe(false)
  })

  it('captures "next MD is Ketu" with adjacent DSH.V.024 citation as has_citation=true', () => {
    const text =
      'Your next MD is Ketu (→ DSH.V.024, 2027-08-21 to 2034-08-18). The Ketu period will be intense.'
    const claims = extractDashaClaims(text)
    const ketuClaim = claims.find(c => c.lord === 'Ketu' && c.has_citation)
    expect(ketuClaim).toBeDefined()
    expect(ketuClaim!.cited_fact_id).toBe('DSH.V.024')
  })

  it('captures generic "Saturn MD was..." mention (no temporal qualifier) as temporal=null', () => {
    const text =
      'Saturn MD was a period of disciplined effort and professional consolidation for the native.'
    const claims = extractDashaClaims(text)
    const saturnClaim = claims.find(c => c.lord === 'Saturn')
    expect(saturnClaim).toBeDefined()
    expect(saturnClaim!.temporal).toBeNull()
    expect(saturnClaim!.has_citation).toBe(false)
  })

  it('extracts level MD from "Mahadasha" token', () => {
    const text = 'The current Mahadasha lord Mercury is strong in Gemini.'
    const claims = extractDashaClaims(text)
    const mercuryClaim = claims.find(c => c.lord === 'Mercury')
    expect(mercuryClaim).toBeDefined()
    expect(mercuryClaim!.level).toBe('MD')
  })

  it('extracts fact_id from citation "(→ DSH.V.001, ...)"', () => {
    const text =
      'The current Mercury MD (→ DSH.V.001, 2023-07-10 to 2040-07-10) is an intellectual peak.'
    const claims = extractDashaClaims(text)
    const mercuryClaim = claims.find(c => c.lord === 'Mercury')
    expect(mercuryClaim?.cited_fact_id).toBe('DSH.V.001')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// validateClaimsAgainstChartFacts
// ─────────────────────────────────────────────────────────────────────────────

describe('validateClaimsAgainstChartFacts', () => {
  it('returns halt for temporal claim without citation', async () => {
    const claims: DashaClaim[] = [
      {
        span: 'Saturn MD next',
        start: 0,
        end: 14,
        temporal: 'next',
        lord: 'Saturn',
        level: 'MD',
        has_citation: false,
        cited_fact_id: null,
        cited_date_range: null,
      },
    ]
    const results = await validateClaimsAgainstChartFacts(claims)
    expect(results[0].verdict).toBe('halt')
    expect(results[0].violation).toMatch(/no_citation/)
  })

  it('returns warn (not halt) for generic mention without temporal qualifier', async () => {
    const claims: DashaClaim[] = [
      {
        span: 'Saturn MD was challenging',
        start: 0,
        end: 25,
        temporal: null,
        lord: 'Saturn',
        level: 'MD',
        has_citation: false,
        cited_fact_id: null,
        cited_date_range: null,
      },
    ]
    const results = await validateClaimsAgainstChartFacts(claims)
    expect(results[0].verdict).toBe('warn')
  })

  it('returns pass when citation matches chart_facts lord (Mercury MD)', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          fact_id: 'DSH.V.001',
          md_lord: 'Mercury',
          ad_lord: 'Mercury',
          start_date: '2023-07-10',
          end_date: '2040-07-10',
        },
      ],
    })
    const claims: DashaClaim[] = [
      {
        span: 'current Mercury MD',
        start: 0,
        end: 18,
        temporal: 'current',
        lord: 'Mercury',
        level: 'MD',
        has_citation: true,
        cited_fact_id: 'DSH.V.001',
        cited_date_range: '2023-07-10 to 2040-07-10',
      },
    ]
    const results = await validateClaimsAgainstChartFacts(claims)
    expect(results[0].verdict).toBe('pass')
  })

  it('returns halt when DSH.V.001 (Jupiter) is cited but synthesis claims Saturn MD', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        {
          fact_id: 'DSH.V.001',
          md_lord: 'Jupiter',
          ad_lord: 'Jupiter',
          start_date: '2000-01-01',
          end_date: '2016-01-01',
        },
      ],
    })
    const claims: DashaClaim[] = [
      {
        span: 'current Saturn MD',
        start: 0,
        end: 17,
        temporal: 'current',
        lord: 'Saturn',
        level: 'MD',
        has_citation: true,
        cited_fact_id: 'DSH.V.001',
        cited_date_range: null,
      },
    ]
    const results = await validateClaimsAgainstChartFacts(claims)
    expect(results[0].verdict).toBe('halt')
    expect(results[0].violation).toMatch(/lord_mismatch/)
  })

  it('returns halt for unknown fact_id not found in chart_facts', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const claims: DashaClaim[] = [
      {
        span: 'next Jupiter MD',
        start: 0,
        end: 15,
        temporal: 'next',
        lord: 'Jupiter',
        level: 'MD',
        has_citation: true,
        cited_fact_id: 'DSH.V.999',
        cited_date_range: null,
      },
    ]
    const results = await validateClaimsAgainstChartFacts(claims)
    expect(results[0].verdict).toBe('halt')
    expect(results[0].violation).toMatch(/unknown_fact_id/)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// runCheckpointDasha — flag/skip behaviour
// ─────────────────────────────────────────────────────────────────────────────

describe('runCheckpointDasha — flag OFF', () => {
  it('returns skipped=true and skipped_reason=flag_off when CHECKPOINT_DASHA_ENABLED=false', async () => {
    mockGetFlag.mockReturnValue(false)
    const result = await runCheckpointDasha(makeInput())
    expect(result.skipped).toBe(true)
    expect(result.skipped_reason).toBe('flag_off')
    expect(result.verdict).toBe('pass')
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

describe('runCheckpointDasha — non-dasha query', () => {
  it('returns skipped=true and skipped_reason=non_dasha_query for a lagna query', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_DASHA_ENABLED')
    const result = await runCheckpointDasha(
      makeInput({
        query: "what's my ascendant?",
        query_plan: makeQueryPlan(['msr_sql']),
      }),
    )
    expect(result.skipped).toBe(true)
    expect(result.skipped_reason).toBe('non_dasha_query')
    expect(result.verdict).toBe('pass')
    expect(mockQuery).not.toHaveBeenCalled()
  })
})

describe('runCheckpointDasha — halt + FAIL_HARD', () => {
  it('throws CheckpointHaltError when synthesis has temporal claim without citation and FAIL_HARD=true', async () => {
    mockGetFlag.mockImplementation((flag: string) =>
      flag === 'CHECKPOINT_DASHA_ENABLED' || flag === 'CHECKPOINT_DASHA_FAIL_HARD',
    )
    const input = makeInput({
      synthesized_text: 'The next MD is Saturn. This will be a difficult period.',
    })
    await expect(runCheckpointDasha(input)).rejects.toBeInstanceOf(CheckpointHaltError)
  })

  it('returns result (no throw) when FAIL_HARD=false even with violations', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_DASHA_ENABLED')
    const input = makeInput({
      synthesized_text: 'The next MD is Saturn. This will be a difficult period.',
    })
    const result = await runCheckpointDasha(input)
    expect(result.verdict).toBe('halt')
    expect(result.violations_count).toBeGreaterThan(0)
  })
})

describe('runCheckpointDasha — pass verdict', () => {
  it('returns pass verdict when synthesis has properly cited temporal claim', async () => {
    mockGetFlag.mockImplementation((flag: string) => flag === 'CHECKPOINT_DASHA_ENABLED')
    // Use mockResolvedValue (not Once) so both potential DB calls from passA + passAReverse
    // claims get the correct Ketu row.
    mockQuery.mockResolvedValue({
      rows: [
        {
          fact_id: 'DSH.V.024',
          md_lord: 'Ketu',
          ad_lord: 'Ketu',
          start_date: '2027-08-21',
          end_date: '2034-08-18',
        },
      ],
    })
    const input = makeInput({
      synthesized_text:
        'Your next Ketu MD (→ DSH.V.024, 2027-08-21 to 2034-08-18) will be a period of dissolution.',
    })
    const result = await runCheckpointDasha(input)
    expect(result.verdict).toBe('pass')
    expect(result.violations_count).toBe(0)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Yogini + Chara (Jaimini) extension — §5C follow-up
// ─────────────────────────────────────────────────────────────────────────────

describe('extractDashaClaims — Yogini system', () => {
  it('extracts "Siddha Yogini" as a claim with lord=Siddha and level=MD', () => {
    const text = 'Your next Siddha Yogini dasha (→ DSH.Y.003, 2026-09-14 to 2029-09-14) will challenge boundaries.'
    const claims = extractDashaClaims(text)
    const siddha = claims.find(c => c.lord === 'Siddha')
    expect(siddha).toBeDefined()
    expect(siddha!.level).toBe('MD')
    expect(siddha!.has_citation).toBe(true)
    expect(siddha!.cited_fact_id).toBe('DSH.Y.003')
  })

  it('extracts Yogini claim without citation as has_citation=false', () => {
    const text = 'Currently running Mangala Yogini — a period of intense activity.'
    const claims = extractDashaClaims(text)
    const mangala = claims.find(c => c.lord === 'Mangala')
    expect(mangala).toBeDefined()
    expect(mangala!.has_citation).toBe(false)
  })
})

describe('extractDashaClaims — Chara (Jaimini) system', () => {
  it('extracts "Aries Chara" as a claim with lord=Aries and level=MD', () => {
    const text = 'The next Aries Chara dasha (→ DSH.C.005, 2028-01-01 to 2034-01-01) brings strong ambition.'
    const claims = extractDashaClaims(text)
    const aries = claims.find(c => c.lord === 'Aries')
    expect(aries).toBeDefined()
    expect(aries!.level).toBe('MD')
    expect(aries!.has_citation).toBe(true)
    expect(aries!.cited_fact_id).toBe('DSH.C.005')
  })
})

describe('validateClaimsAgainstChartFacts — Yogini citation cross-check', () => {
  it('returns pass when DSH.Y.003 lord matches synthesis claim (Siddha)', async () => {
    mockQuery.mockResolvedValue({
      rows: [
        {
          fact_id: 'DSH.Y.003',
          md_lord: 'Siddha',
          ad_lord: 'Siddha',
          start_date: '2026-09-14',
          end_date: '2029-09-14',
        },
      ],
    })
    const claims: DashaClaim[] = [
      {
        span: 'next Siddha Yogini',
        start: 0,
        end: 18,
        temporal: 'next',
        lord: 'Siddha',
        level: 'MD',
        has_citation: true,
        cited_fact_id: 'DSH.Y.003',
        cited_date_range: '2026-09-14 to 2029-09-14',
      },
    ]
    const results = await validateClaimsAgainstChartFacts(claims)
    expect(results[0].verdict).toBe('pass')
  })

  it('returns halt when DSH.Y.003 has Siddha but synthesis claims Bhramari', async () => {
    mockQuery.mockResolvedValue({
      rows: [
        {
          fact_id: 'DSH.Y.003',
          md_lord: 'Siddha',
          ad_lord: 'Siddha',
          start_date: '2026-09-14',
          end_date: '2029-09-14',
        },
      ],
    })
    const claims: DashaClaim[] = [
      {
        span: 'next Bhramari Yogini',
        start: 0,
        end: 20,
        temporal: 'next',
        lord: 'Bhramari',
        level: 'MD',
        has_citation: true,
        cited_fact_id: 'DSH.Y.003',
        cited_date_range: null,
      },
    ]
    const results = await validateClaimsAgainstChartFacts(claims)
    expect(results[0].verdict).toBe('halt')
    expect(results[0].violation).toMatch(/lord_mismatch/)
  })
})

describe('validateClaimsAgainstChartFacts — Chara citation cross-check', () => {
  it('returns halt for unknown DSH.C fact_id', async () => {
    mockQuery.mockResolvedValue({ rows: [] })
    const claims: DashaClaim[] = [
      {
        span: 'next Aries Chara',
        start: 0,
        end: 16,
        temporal: 'next',
        lord: 'Aries',
        level: 'MD',
        has_citation: true,
        cited_fact_id: 'DSH.C.999',
        cited_date_range: null,
      },
    ]
    const results = await validateClaimsAgainstChartFacts(claims)
    expect(results[0].verdict).toBe('halt')
    expect(results[0].violation).toMatch(/unknown_fact_id/)
  })
})
