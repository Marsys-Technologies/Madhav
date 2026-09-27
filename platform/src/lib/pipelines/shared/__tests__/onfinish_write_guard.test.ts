/**
 * Shared onFinish write-through — final authoritative recheck at the
 * persistence boundary (Jātaka Phase-A hardening, item 5). Both reading doors
 * (legacy consult via run_adapter_dispatch, Paripraśna via persistence_stage)
 * persist through this function, so a refusing guard must stop every write:
 * messages, bookkeeping, title, prediction ledger and calibration stamp.
 */
import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
vi.mock('@/lib/db/client', () => ({ query: vi.fn(async () => ({ rows: [] })) }))
vi.mock('@/lib/charts/readingGate', () => ({ checkReadingReadiness: vi.fn(async () => ({ ok: true })) }))

import { runOnFinishWriteThrough, type OnFinishWriteThroughDeps, type OnFinishWriteThroughOpts } from '../onfinish_writethrough'
import { PersistenceRefusedError } from '@/lib/conversations/writeGuard'

function deps(guard: OnFinishWriteThroughDeps['writeGuard']) {
  return {
    writeGuard: guard,
    persistence: { writeMessages: vi.fn(async () => ({ verified: true, messageIds: ['m1'] })) },
    pricing: { getPricing: vi.fn(() => null), computeUsd: vi.fn(() => 0) },
    contextAssemblyLog: vi.fn(),
    fetchMsrSnippets: vi.fn(async () => new Map()),
    pendingStreamWriter: { clear: vi.fn() },
    title: { generate: vi.fn(async () => 'T'), update: vi.fn(async () => undefined) },
    predictionLedger: vi.fn(),
  } as unknown as OnFinishWriteThroughDeps
}

function opts(parts: Array<{ type: string; data: unknown }>): OnFinishWriteThroughOpts {
  return {
    pipelineKind: 'agentic',
    queryId: 'q1',
    conversationId: 'conv-1',
    chartId: 'c1',
    userUid: 'u1',
    isFirstTurn: true,
    lelContextEnabled: false,
    finalMessages: [],
    assistantText: 'The reading. SIG.MSR.001',
    lastUserQuery: 'Q',
    lastAssistantMetadata: {},
    modelId: 'm',
    modelMaxContext: null,
    synthUsage: null,
    synthesisElapsedMs: 1,
    citationGate: { gateResult: 'PASS', layer1Count: 1, layer2Verified: 1 },
    contextAssembly: {},
    writer: { write: (p: { type: string; data: unknown }) => parts.push(p) },
    emit: () => undefined,
  } as unknown as OnFinishWriteThroughOpts
}

describe('runOnFinishWriteThrough — write guard', () => {
  it('writes nothing when the guard refuses, and reports the refusal', async () => {
    const parts: Array<{ type: string; data: unknown }> = []
    const d = deps(async () => ({ ok: false, code: 'CONVERSATION_ARCHIVED_READ_ONLY', message: 'historical' }))
    const result = await runOnFinishWriteThrough(opts(parts), d)
    expect(result).toEqual({ persisted: false, refusal: { code: 'CONVERSATION_ARCHIVED_READ_ONLY', message: 'historical' } })
    expect(d.persistence.writeMessages).not.toHaveBeenCalled()
    expect(d.contextAssemblyLog).not.toHaveBeenCalled()
    expect(d.title.generate).not.toHaveBeenCalled()
    expect(d.title.update).not.toHaveBeenCalled()
    expect(d.predictionLedger).not.toHaveBeenCalled()
    expect(parts).toContainEqual(expect.objectContaining({ type: 'data-persistence', data: expect.objectContaining({ status: 'error' }) }))
    expect(parts.some((p) => p.type === 'data-title')).toBe(false)
  })

  it('fails closed when the guard itself throws', async () => {
    const d = deps(async () => {
      throw new Error('db down')
    })
    const result = await runOnFinishWriteThrough(opts([]), d)
    expect(result.persisted).toBe(false)
    expect(d.persistence.writeMessages).not.toHaveBeenCalled()
  })

  it('persists normally when the guard allows the write', async () => {
    const d = deps(async () => ({ ok: true }))
    const result = await runOnFinishWriteThrough(opts([]), d)
    expect(result).toEqual({ persisted: true })
    expect(d.persistence.writeMessages).toHaveBeenCalled()
  })

  it('checks the guard before the first write', async () => {
    const order: string[] = []
    const d = deps(async () => {
      order.push('guard')
      return { ok: true }
    })
    ;(d.persistence.writeMessages as ReturnType<typeof vi.fn>).mockImplementation(async () => {
      order.push('write')
      return { verified: true, messageIds: [] }
    })
    await runOnFinishWriteThrough(opts([]), d)
    expect(order).toEqual(['guard', 'write'])
  })

  it.each([
    ['a refusal raised by a later re-check inside persistence', () => new PersistenceRefusedError('CONVERSATION_ARCHIVED_READ_ONLY', 'historical')],
    ['the database write guard (migration 1121)', () => Object.assign(new Error('CONVERSATION_ARCHIVED_READ_ONLY: conversation x is correction-archived history'), { code: '23514' })],
  ])('treats %s as a refusal: no ledger, no calibration stamp, not persisted', async (_label, makeError) => {
    const d = deps(async () => ({ ok: true }))
    ;(d.persistence.writeMessages as ReturnType<typeof vi.fn>).mockRejectedValue(makeError())
    const parts: Array<{ type: string; data: unknown }> = []
    const result = await runOnFinishWriteThrough(opts(parts), d)
    expect(result).toMatchObject({ persisted: false, refusal: { code: 'CONVERSATION_ARCHIVED_READ_ONLY' } })
    expect(d.predictionLedger).not.toHaveBeenCalled()
    expect(d.title.generate).not.toHaveBeenCalled()
    expect(parts.some((p) => p.type === 'data-title')).toBe(false)
  })

  it('keeps the existing best-effort behaviour for an ordinary persistence error', async () => {
    const d = deps(async () => ({ ok: true }))
    ;(d.persistence.writeMessages as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('connection reset'))
    const result = await runOnFinishWriteThrough(opts([]), d)
    expect(result).toEqual({ persisted: true })
  })
})

