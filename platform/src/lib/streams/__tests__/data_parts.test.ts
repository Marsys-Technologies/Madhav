/**
 * Unit tests for data_parts.ts — Zod schema validation + helper constructors.
 *
 * Verifies every schema accepts valid payloads and rejects invalid ones, and
 * that helper functions produce correctly-typed output.
 */
import { describe, it, expect } from 'vitest'
import {
  StagePartSchema,
  ToolPartSchema,
  CostPartSchema,
  ObservabilityPartSchema,
  CitationGatePartSchema,
  PersistencePartSchema,
  JudgmentFlagsPartSchema,
  DataPartSchema,
  stagePart,
  toolPart,
  costPart,
  observabilityPart,
  citationGatePart,
  persistencePart,
  judgmentFlagsPart,
  TIME_TO_FIRST_VERDICT_SLO_MS,
  type StagePart,
  type ToolPart,
} from '../data_parts'

// ── StagePart ─────────────────────────────────────────────────────────────

describe('StagePartSchema', () => {
  it('accepts a valid running stage part', () => {
    const result = StagePartSchema.safeParse({
      type: 'stage',
      stage: 'classify',
      status: 'running',
    })
    expect(result.success).toBe(true)
  })

  it('accepts a valid done stage part with ms', () => {
    const result = StagePartSchema.safeParse({
      type: 'stage',
      stage: 'synthesis',
      status: 'done',
      ms: 4213,
    })
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.ms).toBe(4213)
  })

  it('rejects unknown stage names', () => {
    const result = StagePartSchema.safeParse({
      type: 'stage',
      stage: 'unknown_stage',
      status: 'done',
    })
    expect(result.success).toBe(false)
  })

  it('rejects negative ms', () => {
    const result = StagePartSchema.safeParse({
      type: 'stage',
      stage: 'classify',
      status: 'done',
      ms: -1,
    })
    expect(result.success).toBe(false)
  })

  it('accepts all valid stage names', () => {
    const stages: StagePart['stage'][] = [
      'classify', 'compose_bundle', 'plan_per_tool', 'tool_fetch',
      'first_verdict', 'synthesis', 'audit', 'panel:member:1', 'panel:member:2',
      'panel:member:3', 'panel:adjudicator',
    ]
    for (const stage of stages) {
      const result = StagePartSchema.safeParse({ type: 'stage', stage, status: 'done' })
      expect(result.success, `stage ${stage} should be valid`).toBe(true)
    }
  })
})

// ── first_verdict stage (W5 L9 — verdict-first streaming) ─────────────────

describe('first_verdict stage + TIME_TO_FIRST_VERDICT_SLO_MS', () => {
  it('stagePart builds a valid first_verdict done part with an ms sample', () => {
    const part = stagePart('first_verdict', 'done', 10_750)
    expect(StagePartSchema.safeParse(part).success).toBe(true)
    expect(part.stage).toBe('first_verdict')
    expect(part.ms).toBe(10_750)
  })

  it('SLO target is a real, ordered numeric target (p50 < p95), not a placeholder', () => {
    expect(typeof TIME_TO_FIRST_VERDICT_SLO_MS.p50).toBe('number')
    expect(typeof TIME_TO_FIRST_VERDICT_SLO_MS.p95).toBe('number')
    expect(TIME_TO_FIRST_VERDICT_SLO_MS.p50).toBeLessThan(TIME_TO_FIRST_VERDICT_SLO_MS.p95)
    // Both sit well under the measured 38.7s synthesis stage / ~51s total wall-clock (W4 close) —
    // the whole point of streaming the verdict layer before synthesis completes.
    expect(TIME_TO_FIRST_VERDICT_SLO_MS.p95).toBeLessThan(38_700)
  })
})

// ── ToolPart ─────────────────────────────────────────────────────────────

describe('ToolPartSchema', () => {
  it('accepts a running tool part', () => {
    const result = ToolPartSchema.safeParse({ type: 'tool', name: 'msr_sql', status: 'running' })
    expect(result.success).toBe(true)
  })

  it('accepts a done tool part with optional counts', () => {
    const result = ToolPartSchema.safeParse({
      type: 'tool',
      name: 'vector_search',
      status: 'done',
      ms: 312,
      ok_count: 8,
      err_count: 0,
    })
    expect(result.success).toBe(true)
  })

  it('rejects empty tool name', () => {
    const result = ToolPartSchema.safeParse({ type: 'tool', name: '', status: 'done' })
    expect(result.success).toBe(false)
  })

  it('rejects negative ok_count', () => {
    const result = ToolPartSchema.safeParse({
      type: 'tool',
      name: 'msr_sql',
      status: 'done',
      ok_count: -1,
    })
    expect(result.success).toBe(false)
  })
})

// ── CostPart ──────────────────────────────────────────────────────────────

describe('CostPartSchema', () => {
  it('accepts a valid cost part', () => {
    const result = CostPartSchema.safeParse({
      type: 'cost',
      model: 'claude-3-7-sonnet-20250219',
      input_tokens: 4821,
      output_tokens: 1536,
      dollars: 0.0287,
      ms: 5647,
    })
    expect(result.success).toBe(true)
  })

  it('accepts cost part with reasoning_tokens', () => {
    const result = CostPartSchema.safeParse({
      type: 'cost',
      model: 'claude-3-7-sonnet-20250219',
      input_tokens: 4821,
      output_tokens: 1536,
      reasoning_tokens: 312,
      dollars: 0.0287,
      ms: 5647,
    })
    expect(result.success).toBe(true)
  })

  it('rejects negative dollars', () => {
    const result = CostPartSchema.safeParse({
      type: 'cost',
      model: 'claude-3-7-sonnet',
      input_tokens: 100,
      output_tokens: 50,
      dollars: -0.001,
      ms: 1000,
    })
    expect(result.success).toBe(false)
  })

  it('rejects non-integer token counts', () => {
    const result = CostPartSchema.safeParse({
      type: 'cost',
      model: 'claude-3-7-sonnet',
      input_tokens: 100.5,
      output_tokens: 50,
      dollars: 0.001,
      ms: 1000,
    })
    expect(result.success).toBe(false)
  })
})

// ── ObservabilityPart ─────────────────────────────────────────────────────

describe('ObservabilityPartSchema', () => {
  it('accepts a valid observability part', () => {
    const result = ObservabilityPartSchema.safeParse({
      type: 'observability',
      query_id: '550e8400-e29b-41d4-a716-446655440000',
      trace_url: 'https://app.marsys.internal/observatory/trace/550e8400-e29b-41d4-a716-446655440000',
    })
    expect(result.success).toBe(true)
  })

  it('rejects non-UUID query_id', () => {
    const result = ObservabilityPartSchema.safeParse({
      type: 'observability',
      query_id: 'not-a-uuid',
      trace_url: 'https://example.com/trace',
    })
    expect(result.success).toBe(false)
  })

  it('rejects non-URL trace_url', () => {
    const result = ObservabilityPartSchema.safeParse({
      type: 'observability',
      query_id: '550e8400-e29b-41d4-a716-446655440000',
      trace_url: 'not-a-url',
    })
    expect(result.success).toBe(false)
  })
})

// ── CitationGatePart ──────────────────────────────────────────────────────

describe('CitationGatePartSchema', () => {
  it('accepts pass with no issues', () => {
    const result = CitationGatePartSchema.safeParse({ type: 'citation_gate', status: 'pass' })
    expect(result.success).toBe(true)
  })

  it('accepts warn with issues array', () => {
    const result = CitationGatePartSchema.safeParse({
      type: 'citation_gate',
      status: 'warn',
      issues: ['SIG.MSR.123 not in assembled context'],
    })
    expect(result.success).toBe(true)
  })

  it('rejects unknown status', () => {
    const result = CitationGatePartSchema.safeParse({ type: 'citation_gate', status: 'unknown' })
    expect(result.success).toBe(false)
  })
})

// ── PersistencePart ───────────────────────────────────────────────────────

describe('PersistencePartSchema', () => {
  it('accepts a valid ok persistence part', () => {
    const result = PersistencePartSchema.safeParse({
      type: 'persistence',
      conversation_id: '550e8400-e29b-41d4-a716-446655440000',
      message_id: 'msg_abc123',
      status: 'ok',
    })
    expect(result.success).toBe(true)
  })

  it('rejects non-UUID conversation_id', () => {
    const result = PersistencePartSchema.safeParse({
      type: 'persistence',
      conversation_id: 'not-a-uuid',
      message_id: 'msg_abc123',
      status: 'ok',
    })
    expect(result.success).toBe(false)
  })
})

// ── JudgmentFlagsPart (RC-02 — web ↔ MCP gate-flag parity) ─────────────────

describe('JudgmentFlagsPartSchema', () => {
  it('accepts an empty flags array (unconditional emission, §N.6 — "checked, nothing to report")', () => {
    const result = JudgmentFlagsPartSchema.safeParse({ type: 'judgment_flags', flags: [] })
    expect(result.success).toBe(true)
  })

  it('accepts the same flag string prashna_ask surfaces for the NO-LEAKAGE strip', () => {
    const result = JudgmentFlagsPartSchema.safeParse({
      type: 'judgment_flags',
      flags: ['no_leakage_capabilities_stripped'],
    })
    expect(result.success).toBe(true)
  })

  it('rejects a non-array flags field', () => {
    const result = JudgmentFlagsPartSchema.safeParse({ type: 'judgment_flags', flags: 'not-an-array' })
    expect(result.success).toBe(false)
  })
})

// ── DataPartSchema (union discriminator) ──────────────────────────────────

describe('DataPartSchema (union)', () => {
  it('dispatches correctly to each variant', () => {
    const variants = [
      { type: 'stage', stage: 'classify', status: 'done' },
      { type: 'tool', name: 'msr_sql', status: 'running' },
      { type: 'cost', model: 'claude', input_tokens: 100, output_tokens: 50, dollars: 0.01, ms: 1000 },
      { type: 'observability', query_id: '550e8400-e29b-41d4-a716-446655440000', trace_url: 'https://a.com/t' },
      { type: 'citation_gate', status: 'pass' },
      { type: 'persistence', conversation_id: '550e8400-e29b-41d4-a716-446655440000', message_id: 'msg_1', status: 'ok' },
      { type: 'judgment_flags', flags: ['no_leakage_capabilities_stripped'] },
    ]
    for (const v of variants) {
      const result = DataPartSchema.safeParse(v)
      expect(result.success, `Union parse failed for type=${v.type}: ${JSON.stringify((result as { error?: unknown }).error)}`).toBe(true)
    }
  })

  it('rejects unknown type discriminator', () => {
    const result = DataPartSchema.safeParse({ type: 'unknown', data: {} })
    expect(result.success).toBe(false)
  })
})

// ── Helper constructors ───────────────────────────────────────────────────

describe('Helper constructors', () => {
  it('stagePart produces valid StagePart', () => {
    const part = stagePart('synthesis', 'done', 4200)
    expect(StagePartSchema.safeParse(part).success).toBe(true)
    expect(part.type).toBe('stage')
    expect(part.stage).toBe('synthesis')
    expect(part.ms).toBe(4200)
  })

  it('stagePart omits ms when not provided', () => {
    const part = stagePart('classify', 'running')
    expect(part.ms).toBeUndefined()
  })

  it('toolPart produces valid ToolPart', () => {
    const part = toolPart('vector_search', 'done', 312)
    expect(ToolPartSchema.safeParse(part).success).toBe(true)
  })

  it('costPart produces valid CostPart', () => {
    const part = costPart({
      model: 'claude-3-7-sonnet-20250219',
      input_tokens: 4821,
      output_tokens: 1536,
      dollars: 0.0287,
      ms: 5647,
    })
    expect(CostPartSchema.safeParse(part).success).toBe(true)
  })

  it('observabilityPart produces valid ObservabilityPart', () => {
    const part = observabilityPart({
      query_id: '550e8400-e29b-41d4-a716-446655440000',
      trace_url: 'https://a.com/trace/550e8400-e29b-41d4-a716-446655440000',
    })
    expect(ObservabilityPartSchema.safeParse(part).success).toBe(true)
  })

  it('citationGatePart produces valid CitationGatePart', () => {
    const part = citationGatePart({ status: 'warn', issues: ['issue1'] })
    expect(CitationGatePartSchema.safeParse(part).success).toBe(true)
  })

  it('persistencePart produces valid PersistencePart', () => {
    const part = persistencePart({
      conversation_id: '550e8400-e29b-41d4-a716-446655440000',
      message_id: 'msg_abc',
      status: 'ok',
    })
    expect(PersistencePartSchema.safeParse(part).success).toBe(true)
  })

  it('judgmentFlagsPart produces valid JudgmentFlagsPart', () => {
    const part = judgmentFlagsPart({ flags: ['no_leakage_capabilities_stripped'] })
    expect(JudgmentFlagsPartSchema.safeParse(part).success).toBe(true)
    expect(part.type).toBe('judgment_flags')
    expect(part.flags).toEqual(['no_leakage_capabilities_stripped'])
  })
})
