import { describe, expect, it, vi } from 'vitest'

const { usageWrite, externalWrite } = vi.hoisted(() => ({
  usageWrite: vi.fn().mockResolvedValue(undefined),
  externalWrite: vi.fn().mockResolvedValue(undefined),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeAiRoutingUsageEvent: usageWrite,
  writeMcpExternalSynthesisEvent: externalWrite,
}))

import {
  observeMcpExternalSynthesis,
  projectRoleInvocationObservation,
  SafeAiRoutingParametersSchema,
  SafeMcpExternalSynthesisSchema,
} from '../observability'
import type { SafeRoutingSnapshot } from '../execution/types'

const ids = {
  snapshot: '10000000-0000-4000-8000-000000000001',
  invocation: '10000000-0000-4000-8000-000000000002',
  connection: '10000000-0000-4000-8000-000000000003',
  configuration: '10000000-0000-4000-8000-000000000004',
  conversation: '10000000-0000-4000-8000-000000000005',
  correlation: '10000000-0000-4000-8000-000000000006',
}

function snapshot(overrides: Partial<SafeRoutingSnapshot> = {}): SafeRoutingSnapshot {
  const target = { kind: 'provider_model' as const, connectionId: ids.connection,
    providerId: 'google' as const, modelId: 'gemini-test' }
  return {
    source: 'pariprashna', userId: 'user-1', correlationId: ids.correlation,
    conversationId: ids.conversation, selection: { kind: 'default' },
    resolvedChoice: { kind: 'provider_model', connectionId: ids.connection, modelId: 'gemini-test' },
    configurationVersion: null,
    roles: { synthesizer: target, planner: target, deep_planner: target, worker: target },
    ...overrides,
  }
}

function terminal() {
  return {
    invocationId: ids.invocation,
    status: 'success' as const,
    startedAt: new Date('2026-09-27T00:00:00.000Z'),
    finishedAt: new Date('2026-09-27T00:00:00.125Z'),
    usage: { inputTokens: 10, outputTokens: 5, totalTokens: 15 },
    retryCount: 1,
    errorCode: null,
  }
}

describe('safe AI routing observations', () => {
  it('projects exact Default provider identity and normalizes only Google to gemini', () => {
    const projected = projectRoleInvocationObservation({ role: 'planner', providerId: 'google',
      connectionId: ids.connection, modelId: 'gemini-test' },
    { snapshotId: ids.snapshot, snapshot: snapshot() }, terminal())
    expect(projected).toMatchObject({ provider: 'gemini', connection_id: ids.connection,
      model_id: 'gemini-test', role: 'planner', selection_mode: 'default', retry_count: 1,
      latency_ms: 125, fallback_used: false })
    expect(projected).not.toHaveProperty('prompt')
  })

  it.each(['xai', 'kimi', 'openrouter'] as const)('preserves %s provider identity', providerId => {
    const target = { kind: 'provider_model' as const, connectionId: ids.connection, providerId, modelId: 'model' }
    const projected = projectRoleInvocationObservation({ role: 'worker', providerId,
      connectionId: ids.connection, modelId: 'model' }, { snapshotId: ids.snapshot,
      snapshot: snapshot({ resolvedChoice: { kind: 'provider_model', connectionId: ids.connection, modelId: 'model' },
        roles: { synthesizer: target, planner: target, deep_planner: target, worker: target } }) }, terminal())
    expect(projected.provider).toBe(providerId)
  })

  it('projects custom configuration version and explicit CLI built-in default honestly', () => {
    const cli = { kind: 'local_cli' as const, cliId: 'claude_code' as const, modelId: null }
    const choice = { kind: 'custom_configuration' as const, configurationId: ids.configuration }
    const projected = projectRoleInvocationObservation({ role: 'synthesizer', cliId: 'claude_code', modelId: null },
      { snapshotId: ids.snapshot, snapshot: snapshot({ selection: { kind: 'explicit', choice },
        resolvedChoice: choice, configurationVersion: 7,
        roles: { synthesizer: cli, planner: cli, deep_planner: cli, worker: cli } }) },
      { ...terminal(), usage: { inputTokens: null, outputTokens: null, totalTokens: null } })
    expect(projected).toMatchObject({ selection_mode: 'explicit', resolved_choice_kind: 'custom_configuration',
      configuration_id: ids.configuration, configuration_version: 7, provider: 'cli',
      cli_id: 'claude_code', model_id: null, built_in_default: true,
      input_tokens: null, output_tokens: null, total_tokens: null })
  })

  it('rejects an executor descriptor that differs from the immutable snapshot', () => {
    expect(() => projectRoleInvocationObservation({ role: 'planner', providerId: 'openai',
      connectionId: ids.connection, modelId: 'other' },
    { snapshotId: ids.snapshot, snapshot: snapshot() }, terminal())).toThrow(/does not match/)
  })

  it('records an explicitly linked default fallback without weakening exact snapshot matching', () => {
    const projected = projectRoleInvocationObservation({ role: 'planner', providerId: 'google',
      connectionId: ids.connection, modelId: 'gemini-test' },
    { snapshotId: ids.snapshot, snapshot: snapshot(),
      fallback: { fromCorrelationId: 'selected-turn-1' } }, terminal())
    expect(projected).toMatchObject({
      fallback_used: true,
      fallback_from_correlation_id: 'selected-turn-1',
    })
  })

  it('records one strict external-synthesis marker without usage identity', async () => {
    externalWrite.mockClear()
    observeMcpExternalSynthesis(snapshot({ source: 'mcp', conversationId: null }))
    expect(externalWrite).toHaveBeenCalledTimes(1)
    expect(externalWrite.mock.calls[0][0]).toEqual({
      schema_version: 'madhav.external-synthesis.v1', correlation_id: ids.correlation,
      conversation_id: null, user_id: 'user-1', call_stage: 'external_synthesis_handoff',
      external_synthesis: true, performed_by_madhav: false, status: 'not_observed', fallback_used: null,
    })
    expect(externalWrite.mock.calls[0][0]).not.toHaveProperty('model')
  })

  it('keeps external marker persistence non-fatal and non-blocking', async () => {
    externalWrite.mockClear()
    externalWrite.mockImplementationOnce(() => new Promise<void>(() => undefined))
    expect(() => observeMcpExternalSynthesis(snapshot({ source: 'mcp' }))).not.toThrow()
    expect(externalWrite).toHaveBeenCalledOnce()

    externalWrite.mockRejectedValueOnce(new Error('db unavailable'))
    vi.spyOn(console, 'warn').mockImplementation(() => undefined)
    observeMcpExternalSynthesis(snapshot({ source: 'mcp' }))
    await vi.waitFor(() => expect(console.warn).toHaveBeenCalledWith(
      '[ai-console] Observatory external-synthesis observation failed'))
  })

  it('exports closed schemas', () => {
    expect(SafeAiRoutingParametersSchema.safeParse({ unexpected: true }).success).toBe(false)
    expect(SafeMcpExternalSynthesisSchema.safeParse({ unexpected: true }).success).toBe(false)
  })
})
