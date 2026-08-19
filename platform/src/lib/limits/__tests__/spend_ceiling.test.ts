/**
 * spend_ceiling.test.ts — NCD-8 ceiling logic (Paripraśna P1, lane G1-D).
 *
 * Covers the ruling's two numbers ($2/turn, $40/day — PARIPRASHNA_DECISION_
 * REGISTER_v1_0.md NCD-8, RULED 2026-08-18) and, critically, the negative cases:
 * a detector that can only ever say "allowed" is not a detector (CLAUDE.md §N.8),
 * so every ceiling here is tested from BOTH sides.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

import {
  DEFAULT_PROJECTION_INPUT_TOKENS,
  SPEND_CEILING_PER_DAY_USD,
  SPEND_CEILING_PER_TURN_USD,
  checkSpendCeilings,
  getDailySpendUsd,
  getSpendAttribution,
  projectTurnCostUsd,
  spendCeilingMessage,
} from '../spend_ceiling'

/** Today's spend, as the ledger query would return it. */
function spendRows(totalUsd: number) {
  return { rows: [{ total: String(totalUsd) }] }
}

beforeEach(() => {
  queryMock.mockReset()
})

describe('NCD-8 ruled ceiling values', () => {
  it('is $2 per turn and $40 per day', () => {
    expect(SPEND_CEILING_PER_TURN_USD).toBe(2)
    expect(SPEND_CEILING_PER_DAY_USD).toBe(40)
  })
})

describe('projectTurnCostUsd — the pre-dispatch worst-case bound', () => {
  it('projects from real registry pricing, not a placeholder', () => {
    // gemini-2.5-flash: $0.075/1M in, $0.30/1M out, 65_536 max output.
    // 128_000/1e6*0.075 + 65_536/1e6*0.30 = 0.0096 + 0.0196608 = 0.0292608
    const p = projectTurnCostUsd('gemini-2.5-flash')
    expect(p.input_tokens).toBe(DEFAULT_PROJECTION_INPUT_TOKENS)
    expect(p.output_tokens).toBe(65_536)
    expect(p.projected_max_usd).toBeCloseTo(0.029261, 5)
  })

  it('honours an explicit token budget', () => {
    // claude-sonnet-4-6: $3/1M in, $15/1M out.
    // 1_000_000/1e6*3 + 100_000/1e6*15 = 3 + 1.5 = 4.5
    const p = projectTurnCostUsd('claude-sonnet-4-6', {
      inputTokens: 1_000_000,
      outputTokens: 100_000,
    })
    expect(p.projected_max_usd).toBeCloseTo(4.5, 6)
  })

  it("caps assumed input at the model's own declared context window", () => {
    // gemini-2.5-flash declares maxInputTokens 1_000_000; asking for 5M must clamp.
    const p = projectTurnCostUsd('gemini-2.5-flash', { inputTokens: 5_000_000 })
    expect(p.input_tokens).toBe(1_000_000)
  })

  it('returns null — never 0 — for a model with no registry pricing', () => {
    const p = projectTurnCostUsd('some-model-that-does-not-exist')
    expect(p.projected_max_usd).toBeNull()
    expect(p.unpriced_reason).toBe('model_not_in_registry')
  })
})

describe('$2/turn ceiling', () => {
  it('REFUSES a turn whose own budget could breach $2', async () => {
    // claude-opus-4-7: $15/1M in, $75/1M out, 64_000 max output.
    // 128_000/1e6*15 + 64_000/1e6*75 = 1.92 + 4.80 = $6.72 > $2.
    const decision = await checkSpendCeilings({
      userId: 'u1',
      channel: 'web',
      modelId: 'claude-opus-4-7',
    })
    expect(decision.allowed).toBe(false)
    expect(decision.reason).toBe('turn_ceiling_exceeded')
    expect(decision.ceiling_usd).toBe(2)
    expect(decision.projected_turn_usd).toBeCloseTo(6.72, 6)
    // PRE-DISPATCH: refused before the DB is even consulted.
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('ALLOWS a turn that cannot breach $2', async () => {
    queryMock.mockResolvedValue(spendRows(0))
    const decision = await checkSpendCeilings({
      userId: 'u1',
      channel: 'web',
      modelId: 'gemini-2.5-flash',
    })
    expect(decision.allowed).toBe(true)
    expect(decision.reason).toBeUndefined()
  })

  it('applies the same $2 ceiling on the MCP door', async () => {
    const decision = await checkSpendCeilings({
      userId: 'u1',
      channel: 'mcp',
      modelId: 'claude-opus-4-7',
    })
    expect(decision.allowed).toBe(false)
    expect(decision.reason).toBe('turn_ceiling_exceeded')
    expect(decision.channel).toBe('mcp')
  })
})

describe('$40/day ceiling', () => {
  it('REFUSES when today’s spend plus this turn would pass $40', async () => {
    queryMock.mockResolvedValue(spendRows(39.999))
    const decision = await checkSpendCeilings({
      userId: 'u1',
      channel: 'web',
      modelId: 'gemini-2.5-flash', // ~$0.029 projected — enough to cross
    })
    expect(decision.allowed).toBe(false)
    expect(decision.reason).toBe('daily_ceiling_exceeded')
    expect(decision.ceiling_usd).toBe(40)
    expect(decision.spent_today_usd).toBeCloseTo(39.999, 6)
    expect(decision.daily_spend_known).toBe(true)
  })

  it('ALLOWS when the day still has room', async () => {
    queryMock.mockResolvedValue(spendRows(10))
    const decision = await checkSpendCeilings({
      userId: 'u1',
      channel: 'web',
      modelId: 'gemini-2.5-flash',
    })
    expect(decision.allowed).toBe(true)
    expect(decision.spent_today_usd).toBe(10)
  })

  it('applies the same $40 ceiling on the MCP door', async () => {
    queryMock.mockResolvedValue(spendRows(40.5))
    const decision = await checkSpendCeilings({
      userId: 'u1',
      channel: 'mcp',
      modelId: 'gemini-2.5-flash',
    })
    expect(decision.allowed).toBe(false)
    expect(decision.reason).toBe('daily_ceiling_exceeded')
    expect(decision.channel).toBe('mcp')
  })

  it('scopes the ledger read to the user and to the current UTC day', async () => {
    queryMock.mockResolvedValue(spendRows(1))
    await checkSpendCeilings({ userId: 'u-42', channel: 'web', modelId: 'gemini-2.5-flash' })
    const [sql, params] = queryMock.mock.calls[0]
    expect(sql).toContain('llm_usage_events')
    expect(sql).toContain('computed_cost_usd')
    expect(sql).toContain("date_trunc('day', now() AT TIME ZONE 'utc')")
    expect(params).toEqual(['u-42'])
  })
})

describe('fail-open is reported honestly, never as "under ceiling"', () => {
  it('allows the turn but marks the day-spend unknown when the query fails', async () => {
    queryMock.mockRejectedValue(new Error('connection refused'))
    const decision = await checkSpendCeilings({
      userId: 'u1',
      channel: 'web',
      modelId: 'gemini-2.5-flash',
    })
    expect(decision.allowed).toBe(true)
    expect(decision.daily_spend_known).toBe(false)
  })

  it('getDailySpendUsd reports known:false rather than a fabricated 0', async () => {
    queryMock.mockRejectedValue(new Error('boom'))
    await expect(getDailySpendUsd('u1')).resolves.toEqual({ usd: 0, known: false })
  })
})

describe('an unpriced model does not silently bypass the gate', () => {
  it('still evaluates the daily ceiling against known spend', async () => {
    queryMock.mockResolvedValue(spendRows(41))
    const decision = await checkSpendCeilings({
      userId: 'u1',
      channel: 'web',
      modelId: 'not-a-real-model',
    })
    expect(decision.projected_turn_usd).toBeNull()
    expect(decision.allowed).toBe(false)
    expect(decision.reason).toBe('daily_ceiling_exceeded')
  })
})

describe('per-(user, channel, model) attribution', () => {
  it('groups the existing ledger by exactly those three dimensions', async () => {
    queryMock.mockResolvedValue({
      rows: [
        { user_id: 'u1', channel: 'web', model: 'gemini-2.5-flash', calls: '3', cost_usd: '0.42' },
        { user_id: 'u1', channel: 'mcp', model: 'gemini-2.5-pro', calls: '1', cost_usd: '0.10' },
        { user_id: 'u1', channel: null, model: 'gpt-4.1', calls: '2', cost_usd: '0.05' },
      ],
    })
    const rows = await getSpendAttribution('u1')
    const [sql] = queryMock.mock.calls[0]
    expect(sql).toContain('GROUP BY user_id, channel, model')
    expect(rows).toHaveLength(3)
    expect(rows[0]).toEqual({
      user_id: 'u1',
      channel: 'web',
      model: 'gemini-2.5-flash',
      calls: 3,
      cost_usd: 0.42,
    })
    // A legacy row with no declared door stays null — not coerced to a channel.
    expect(rows[2].channel).toBeNull()
  })
})

describe('refusal messages state the real ceiling', () => {
  it('names the per-turn ceiling and the model', () => {
    const msg = spendCeilingMessage({
      allowed: false,
      reason: 'turn_ceiling_exceeded',
      ceiling_usd: 2,
      projected_turn_usd: 6.72,
      spent_today_usd: 0,
      daily_spend_known: false,
      channel: 'web',
      model_id: 'claude-opus-4-7',
    })
    expect(msg).toContain('$2.00')
    expect(msg).toContain('$6.72')
    expect(msg).toContain('claude-opus-4-7')
  })

  it('names the daily ceiling and the reset', () => {
    const msg = spendCeilingMessage({
      allowed: false,
      reason: 'daily_ceiling_exceeded',
      ceiling_usd: 40,
      projected_turn_usd: 0.03,
      spent_today_usd: 39.999,
      daily_spend_known: true,
      channel: 'mcp',
      model_id: 'gemini-2.5-flash',
    })
    expect(msg).toContain('$40.00')
    expect(msg).toContain('00:00 UTC')
  })
})
