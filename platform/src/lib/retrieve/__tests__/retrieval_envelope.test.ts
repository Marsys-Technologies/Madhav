/**
 * RIR-S1/S2/S3/S4: retrieval_envelope tests
 * [BUILD-ORCH-RIR-S1, RIR-S2]
 */

import { describe, it, expect } from 'vitest'
import {
  parseInput,
  makeOutput,
  makeCitation,
  makeChannelAdapter,
  tierAtLeast,
  filterByTier,
  CHANNELS,
  AUDIENCE_TIERS,
  isChannel,
  isAudienceTier,
  InputValidationError,
} from '../retrieval_envelope'

// ── Validators ────────────────────────────────────────────────────────────────

function validateStringParams(raw: unknown): { fact_category: string; limit?: number } {
  const obj = raw as Record<string, unknown>
  if (typeof obj?.['fact_category'] !== 'string') throw new Error('fact_category required')
  return { fact_category: obj['fact_category'], limit: typeof obj['limit'] === 'number' ? obj['limit'] : undefined }
}

function validateLimitParams(raw: unknown): { limit: number } {
  const obj = raw as Record<string, unknown>
  if (typeof obj?.['limit'] !== 'number') throw new Error('limit required')
  return { limit: obj['limit'] }
}

// ── Input envelope ────────────────────────────────────────────────────────────

describe('parseInput', () => {
  it('validates a valid input envelope', () => {
    const result = parseInput(validateStringParams, {
      params: { fact_category: 'planet', limit: 10 },
      chart_id: '00000000-0000-0000-0000-000000000001',
      audience_tier: 'super_admin',
      channel: 'portal',
    })
    expect(result.params.fact_category).toBe('planet')
    expect(result.ayanamsha_id).toBe('lahiri') // default
  })

  it('rejects invalid channel', () => {
    expect(() =>
      parseInput(validateStringParams, {
        params: { fact_category: 'planet' },
        audience_tier: 'super_admin',
        channel: 'unknown_channel',
      })
    ).toThrow(InputValidationError)
  })

  it('rejects invalid audience_tier', () => {
    expect(() =>
      parseInput(validateStringParams, {
        params: { fact_category: 'planet' },
        audience_tier: 'god_mode',
        channel: 'portal',
      })
    ).toThrow(InputValidationError)
  })

  it('defaults ayanamsha_id to lahiri', () => {
    const result = parseInput(validateStringParams, {
      params: { fact_category: 'planet' },
      audience_tier: 'client',
      channel: 'mcp',
    })
    expect(result.ayanamsha_id).toBe('lahiri')
  })

  it('preserves optional chart_id', () => {
    const result = parseInput(validateStringParams, {
      params: { fact_category: 'planet' },
      audience_tier: 'super_admin',
      channel: 'portal',
      chart_id: 'aaaaaaaa-0000-0000-0000-000000000001',
    })
    expect(result.chart_id).toBe('aaaaaaaa-0000-0000-0000-000000000001')
  })

  it('parses and returns typed input', () => {
    const result = parseInput(validateLimitParams, {
      params: { limit: 5 },
      audience_tier: 'client',
      channel: 'consume_hybrid',
    })
    expect(result.params.limit).toBe(5)
    expect(result.channel).toBe('consume_hybrid')
  })
})

// ── Citation envelope ─────────────────────────────────────────────────────────

describe('makeCitation', () => {
  it('creates citation with ref from canonical ID', () => {
    const c = makeCitation('FORENSIC', '8.0', 0.95, '§3.1')
    expect(c.ref).toBe('[FORENSIC §3.1]')
    expect(c.source_canonical_id).toBe('FORENSIC')
    expect(c.confidence).toBe(0.95)
    expect(c.section).toBe('§3.1')
  })

  it('creates citation without section', () => {
    const c = makeCitation('MSR', '5.0', 0.8)
    expect(c.ref).toBe('[MSR]')
    expect(c.section).toBeUndefined()
  })
})

// ── Output envelope ───────────────────────────────────────────────────────────

describe('makeOutput', () => {
  it('creates output with defaults', () => {
    const out = makeOutput({ rows: 10 })
    expect(out.schema_version).toBe('1.0')
    expect(out.channel).toBe('portal')
    expect(out.ayanamsha_id).toBe('lahiri')
    expect(out.cache_hit).toBe(false)
    expect(out.tier_filtered).toBe(false)
    expect(out.citations).toEqual([])
  })

  it('overrides defaults', () => {
    const cite = makeCitation('LEL', '1.7', 0.9)
    const out = makeOutput({ signal: 'S001' }, {
      channel: 'mcp',
      ayanamsha_id: 'kp',
      latency_ms: 42,
      citations: [cite],
      cache_hit: true,
      tier_filtered: true,
      rows_returned: 1,
    })
    expect(out.channel).toBe('mcp')
    expect(out.ayanamsha_id).toBe('kp')
    expect(out.latency_ms).toBe(42)
    expect(out.citations).toHaveLength(1)
    expect(out.cache_hit).toBe(true)
    expect(out.tier_filtered).toBe(true)
  })
})

// ── Channel adapter ───────────────────────────────────────────────────────────

describe('makeChannelAdapter', () => {
  it('wraps an async function in an adapter', async () => {
    const adapter = makeChannelAdapter(
      'portal',
      async (params: { limit: number }) => ({ results: Array(params.limit).fill('x') }),
      { rowsFn: (o) => o.results.length },
    )

    const result = await adapter.execute({
      params: { limit: 3 },
      audience_tier: 'client',
      channel: 'portal',
      ayanamsha_id: 'lahiri',
    })

    expect(result.data.results).toHaveLength(3)
    expect(result.rows_returned).toBe(3)
    expect(result.channel).toBe('portal')
    expect(result.latency_ms).toBeGreaterThanOrEqual(0)
    expect(result.schema_version).toBe('1.0')
  })
})

// ── Tier filtering ────────────────────────────────────────────────────────────

describe('tierAtLeast', () => {
  it('super_admin >= all', () => {
    expect(tierAtLeast('super_admin', 'client')).toBe(true)
    expect(tierAtLeast('super_admin', 'acharya_reviewer')).toBe(true)
    expect(tierAtLeast('super_admin', 'super_admin')).toBe(true)
  })

  it('public_redacted < all others', () => {
    expect(tierAtLeast('public_redacted', 'client')).toBe(false)
    expect(tierAtLeast('public_redacted', 'acharya_reviewer')).toBe(false)
  })

  it('client >= public_redacted, < acharya', () => {
    expect(tierAtLeast('client', 'public_redacted')).toBe(true)
    expect(tierAtLeast('client', 'acharya_reviewer')).toBe(false)
  })
})

describe('filterByTier', () => {
  it('returns all items when no min_tier set', () => {
    const items = [{ name: 'a' }, { name: 'b' }]
    const { filtered, was_filtered } = filterByTier(items, 'client')
    expect(filtered).toHaveLength(2)
    expect(was_filtered).toBe(false)
  })

  it('filters items by min_tier', () => {
    const items = [
      { name: 'public', min_tier: 'public_redacted' as const },
      { name: 'admin_only', min_tier: 'super_admin' as const },
    ]
    const { filtered, was_filtered } = filterByTier(items, 'client')
    expect(filtered).toHaveLength(1)
    expect(filtered[0]!.name).toBe('public')
    expect(was_filtered).toBe(true)
  })
})

// ── Enum validation ───────────────────────────────────────────────────────────

describe('isChannel', () => {
  it('accepts all 5 channels', () => {
    for (const c of CHANNELS) {
      expect(isChannel(c)).toBe(true)
    }
  })
  it('rejects unknown channel', () => {
    expect(isChannel('unknown')).toBe(false)
  })
})

describe('isAudienceTier', () => {
  it('accepts all 4 tiers', () => {
    for (const t of AUDIENCE_TIERS) {
      expect(isAudienceTier(t)).toBe(true)
    }
  })
  it('rejects unknown tier', () => {
    expect(isAudienceTier('god_mode')).toBe(false)
  })
})
