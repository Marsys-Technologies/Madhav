import { describe, expect, it, vi } from 'vitest'
import type { LanguageModelV3 } from '@ai-sdk/provider'
import { meterModel } from '../model'
import type { MeteringContext } from '../types'
import type { RecoveryEnvelope, RecoveryStore } from '../recovery'

const context: MeteringContext = { userId: 'owner', conversationId: 'conversation', turnId: 'turn', operationId: 'operation',
  channel: 'mcp', purpose: 'customer', payer: 'user', provider: 'openai', model: 'model', role: 'planner', aggregation: 'transport' }
const usage = { inputTokens: { total: 100, noCache: 80, cacheRead: 20, cacheWrite: 0 }, outputTokens: { total: 20, text: 15, reasoning: 5 } }
function harness() {
  const envelopes: RecoveryEnvelope[] = []
  const recovery: RecoveryStore = { put: vi.fn(async e => { envelopes.push(e) }), list: async () => [],
    read: vi.fn(), remove: vi.fn() }
  const db = { query: vi.fn(async (sql: string) => {
    if (sql.includes('SELECT')) return { rows: [] }
    return { rows: [],rowCount: 1 }
  }) }
  return { db,recovery,envelopes }
}
function model(parts: unknown[], doStream = vi.fn()): LanguageModelV3 {
  doStream.mockImplementation(async () => ({ stream: new ReadableStream({ start(c) {
    for (const part of parts) c.enqueue(part); c.close()
  } }) }))
  return { specificationVersion: 'v3',provider: 'openai',modelId: 'model',supportedUrls: {},doStream,
    doGenerate: vi.fn(async () => ({ content: [],usage,finishReason: { unified: 'stop' as const,raw: 'stop' },warnings: [] })) }
}
const options = { prompt: [] }

describe('physical model attempts', () => {
  it('commits start before entering the model and writes a detailed receipt before finish', async () => {
    const h = harness(), delegate = model([{ type: 'finish', usage, finishReason: { unified: 'stop' } }])
    const stream = await meterModel(delegate,context,h).doStream(options)
    expect(h.db.query.mock.calls[0][0]).toContain('INSERT INTO ai_metering_attempts')
    const reader = stream.stream.getReader(); await reader.read()
    const receipt = h.db.query.mock.calls.find(([sql]) => sql.includes('INSERT INTO ai_metering_receipts'))
    expect(receipt).toBeDefined()
    expect(JSON.parse((receipt as unknown as [string,unknown[]])[1][3] as string)).toMatchObject({ cacheRead: 20,reasoning: 5 })
  })
  it('records one leaf attempt per SDK invocation, including repeated steps', async () => {
    const h = harness(), wrapped = meterModel(model([]),context,h)
    await wrapped.doGenerate(options); await wrapped.doGenerate(options)
    expect(h.db.query.mock.calls.filter(([sql]) => sql.includes('INSERT INTO ai_metering_attempts'))).toHaveLength(2)
  })
  it('does not call a provider if start persistence fails', async () => {
    const h = harness(), delegate = model([]); h.db.query.mockRejectedValue(new Error('DB down'))
    await expect(meterModel(delegate,context,h).doGenerate(options)).rejects.toThrow()
    expect(delegate.doGenerate).not.toHaveBeenCalled()
  })
  it('keeps usage unavailable when a stream ends without provider finish', async () => {
    const h = harness(), stream = await meterModel(model([{ type:'text-delta', id:'x',delta:'hello' }]),context,h).doStream(options)
    const reader = stream.stream.getReader(); await reader.read(); await reader.read()
    const receipt = h.db.query.mock.calls.find(([sql]) => sql.includes('INSERT INTO ai_metering_receipts')) as unknown as [string,unknown[]]
    expect(receipt[1][2]).toBe('incomplete')
    expect(JSON.parse(receipt[1][3] as string).input).toBeNull()
  })
  it('persists cancellation as unknown usage and retains first-token timing', async () => {
    const h = harness(), stream = await meterModel(model([{ type:'text-delta',id:'x',delta:'hello' }]),context,h).doStream(options)
    const reader = stream.stream.getReader(); await reader.read(); await reader.cancel()
    const receipt = h.db.query.mock.calls.find(([sql]) => sql.includes('INSERT INTO ai_metering_receipts')) as unknown as [string,unknown[]]
    expect(receipt[1][2]).toBe('cancelled'); expect(receipt[1][6]).not.toBeNull()
  })
  it('classifies deadline aborts as timeouts', async () => {
    const h = harness(), delegate = model([]), signal = AbortSignal.abort(new DOMException('deadline','TimeoutError'))
    delegate.doGenerate = vi.fn(async () => { throw new Error('upstream private') })
    await expect(meterModel(delegate,context,h).doGenerate({...options,abortSignal:signal})).rejects.toThrow('upstream private')
    const receipt = h.db.query.mock.calls.find(([sql]) => sql.includes('INSERT INTO ai_metering_receipts')) as unknown as [string,unknown[]]
    expect(receipt[1][2]).toBe('timeout');expect(receipt[1][3]).not.toContain('private')
  })
  it('writes a safe recovery envelope if receipt DB persistence fails', async () => {
    const h = harness()
    h.db.query.mockImplementation(async sql => { if (sql.includes('INSERT INTO ai_metering_receipts')) throw new Error('down')
      return { rows: [],rowCount: 1 } })
    await meterModel(model([]),context,h).doGenerate(options)
    expect(h.envelopes).toHaveLength(1); expect(h.envelopes[0].receipt.usage.input).toBe(100)
    expect(JSON.stringify(h.envelopes)).not.toContain('hello')
  })
})
