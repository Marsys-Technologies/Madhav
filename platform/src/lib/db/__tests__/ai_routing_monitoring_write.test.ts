import { beforeEach, describe, expect, it, vi } from 'vitest'

const { dbQuery } = vi.hoisted(() => ({ dbQuery: vi.fn() }))
vi.unmock('@/lib/db/monitoring-write')
vi.mock('@/lib/storage', () => ({ getStorageClient: () => ({ query: dbQuery }) }))
vi.mock('@/lib/models/registry', () => ({ getModelMeta: vi.fn() }))

import { writeAiRoutingUsageEvent, writeMcpExternalSynthesisEvent } from '../monitoring-write'
import type { SafeAiRoutingParameters, SafeMcpExternalSynthesis } from '@/lib/ai-console/observability'

const base: SafeAiRoutingParameters = {
  schema_version: 'madhav.ai-routing.v1',
  snapshot_id: '10000000-0000-4000-8000-000000000001',
  invocation_id: '10000000-0000-4000-8000-000000000002',
  correlation_id: 'turn-1', conversation_id: null, user_id: 'user-1', source: 'backend',
  role: 'worker', selection_mode: 'default', resolved_choice_kind: 'provider_model',
  configuration_id: null, configuration_version: null, target_kind: 'provider_model',
  connection_id: '10000000-0000-4000-8000-000000000003', provider: 'openai', model_id: 'gpt-test',
  cli_id: null, built_in_default: false, terminal_status: 'success',
  started_at: '2026-09-27T00:00:00.000Z', finished_at: '2026-09-27T00:00:00.010Z',
  latency_ms: 10, input_tokens: 100, output_tokens: 20, total_tokens: 120,
  retry_count: 0, error_code: null, fallback_used: false,
}

describe('strict AI routing monitoring writers', () => {
  beforeEach(() => dbQuery.mockReset().mockResolvedValue({ rows: [] }))

  it('writes null prompts/responses and null cost when authoritative pricing is incomplete', async () => {
    dbQuery.mockResolvedValueOnce({ rows: [{ pricing_version_id: '10000000-0000-4000-8000-000000000004',
      token_class: 'input', price_per_million_usd: 1 }] }).mockResolvedValueOnce({ rows: [] })
    await writeAiRoutingUsageEvent(base)

    const [, insert] = dbQuery.mock.calls
    expect(insert[0]).toContain('prompt_text,response_text,system_prompt')
    expect(insert[0]).toContain('NULL,NULL,NULL')
    expect(insert[1][9]).toBeNull()
    expect(insert[1][10]).toBeNull()
    expect(insert[1][0]).toBeNull()
    expect(insert[1][1]).toBe(base.invocation_id)
  })

  it('never performs a pricing lookup for CLI usage and preserves missing tokens as null', async () => {
    const cli: SafeAiRoutingParameters = { ...base, target_kind: 'local_cli', connection_id: null,
      provider: 'cli', model_id: null, cli_id: 'claude_code', built_in_default: true,
      input_tokens: null, output_tokens: null, total_tokens: null }
    await writeAiRoutingUsageEvent(cli)

    expect(dbQuery).toHaveBeenCalledTimes(1)
    const params = dbQuery.mock.calls[0][1]
    expect(params[4]).toBe('built-in-default')
    expect(params[7]).toBeNull()
    expect(params[8]).toBeNull()
    expect(params[9]).toBeNull()
  })

  it('writes external synthesis only to the non-usage relation with null model/provider/cost', async () => {
    const marker: SafeMcpExternalSynthesis = {
      schema_version: 'madhav.external-synthesis.v1',
      correlation_id: '10000000-0000-4000-8000-000000000006', conversation_id: null,
      user_id: 'user-1', call_stage: 'external_synthesis_handoff', external_synthesis: true,
      performed_by_madhav: false, status: 'not_observed', fallback_used: null,
    }
    await writeMcpExternalSynthesisEvent(marker)

    expect(dbQuery).toHaveBeenCalledTimes(1)
    expect(dbQuery.mock.calls[0][0]).toContain('INSERT INTO llm_call_log')
    expect(dbQuery.mock.calls[0][0]).not.toContain('llm_usage_events')
    expect(dbQuery.mock.calls[0][0]).toContain('NULL,NULL,NULL,NULL,NULL,NULL,NULL')
    expect(dbQuery.mock.calls[0][0]).toContain("call_stage='external_synthesis_handoff'")
    expect(JSON.stringify(dbQuery.mock.calls[0][1])).not.toContain('prompt')
  })

  it('revalidates the closed schema at the writer boundary', async () => {
    const warn = vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    await writeAiRoutingUsageEvent({ ...base, prompt: 'forbidden' } as unknown as SafeAiRoutingParameters)
    expect(dbQuery).not.toHaveBeenCalled()
    expect(warn).toHaveBeenCalledWith('[ai-console] Observatory role write failed')
    expect(JSON.stringify(warn.mock.calls)).not.toContain('forbidden')
  })

})
