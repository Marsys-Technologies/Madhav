import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { ChatEvent } from '@/lib/providers/types'
import { meterCapabilityChat } from '../capability-chat'
import { getAdapter } from '@/lib/providers/dispatcher'
import { meteringRequest, setMeteringAttribution } from '../context'

const calls = vi.hoisted(() => ({ start: vi.fn(), finish: vi.fn() }))
vi.mock('../service', () => ({ startAttempt: calls.start, finishAttempt: calls.finish }))
const context = { userId: 'alice', conversationId: 'conversation', turnId: 'question', operationId: 'operation',
  channel: 'web' as const, purpose: 'customer' as const, payer: 'platform' as const,
  provider: 'openai', model: 'model', role: 'synthesis', aggregation: 'transport' as const }
const events: ChatEvent[] = [{ type: 'text_delta', text: 'answer' }, { type: 'message_stop', stopReason: 'stop' },
  { type: 'usage', inputTokens: 100, outputTokens: 10, cacheReadTokens: 20 }]
async function* stream(sequence: ChatEvent[]) { for (const event of sequence) yield event }
beforeEach(() => {
  vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED', 'true')
  calls.start.mockReset().mockImplementation(async input => ({ ...input, attemptId: '00000000-0000-4000-8000-000000000001', startedAt: '2026-09-29T10:00:00Z' }))
  calls.finish.mockReset().mockResolvedValue(undefined)
})
afterEach(() => vi.unstubAllEnvs())

describe('raw capability stream metering', () => {
  it('records reported usage once after a successful stream', async () => {
    const seen: ChatEvent[] = []
    for await (const event of meterCapabilityChat(stream(events), context)) seen.push(event)
    expect(seen).toEqual(events)
    expect(calls.start).toHaveBeenCalledTimes(1)
    expect(calls.finish).toHaveBeenCalledTimes(1)
    expect(calls.finish.mock.calls[0][1]).toMatchObject({ status: 'success', usage: { input: 100, output: 10, cacheRead: 20, source: 'provider_reported' } })
  })
  it('keeps provider errors as failed attempts with unknown usage', async () => {
    for await (const event of meterCapabilityChat(stream([{ type: 'error', error: 'provider failed' }]), context)) expect(event.type).toBe('error')
    expect(calls.finish.mock.calls[0][1]).toMatchObject({ status: 'error', usage: { input: null, output: null, source: 'unavailable' } })
  })
  it('records an early consumer stop as cancellation', async () => {
    for await (const event of meterCapabilityChat(stream(events), context)) { expect(event.type).toBe('text_delta'); break }
    expect(calls.finish.mock.calls[0][1].status).toBe('cancelled')
  })
  it('requires request attribution when the raw adapter is enabled', () => {
    const adapter = getAdapter('openai')
    expect(() => adapter.chat({ model: 'model', messages: [] })).toThrow('Metering attribution required')
  })
  it('routes one raw adapter invocation through the scoped ledger', async () => {
    const raw = getAdapter('openai')
    vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED', 'false')
    const original = getAdapter('openai').chat
    getAdapter('openai').chat = () => stream(events)
    vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED', 'true')
    try {
      await meteringRequest(async () => {
        setMeteringAttribution({ userId: 'alice', conversationId: 'conversation', turnId: 'question', channel: 'mcp', purpose: 'customer', payer: 'platform' })
        for await (const event of raw.chat({ model: 'model', messages: [] })) expect(event.type).toBeTruthy()
      })
      expect(calls.start.mock.calls[0][0]).toMatchObject({ userId: 'alice', channel: 'mcp', provider: 'openai', model: 'model', aggregation: 'transport' })
    } finally {
      vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED', 'false')
      getAdapter('openai').chat = original
    }
  })
})
