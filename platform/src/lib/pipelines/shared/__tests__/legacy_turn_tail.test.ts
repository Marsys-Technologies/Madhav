/**
 * Legacy consult terminal sequence (Jātaka Phase-A2). The dispatch inspects the
 * shared write-through result: when the final archive/readiness recheck refused
 * persistence, the client receives the stable refusal code in a stream error
 * part and never a successful finish; otherwise the existing tail is unchanged.
 */
import { describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

import { writeLegacyTurnTail } from '../run_adapter_dispatch'

function collect() {
  const chunks: Array<Record<string, any>> = []
  const events: Array<Record<string, any>> = []
  return {
    chunks,
    events,
    writer: { write: (c: Record<string, any>) => chunks.push(c) },
    emit: (e: Record<string, any>) => events.push(e),
  }
}

const BASE = { completenessReceipt: null, judgmentFlags: [], adapterStartMs: 0, queryId: 'q-1' }

describe('writeLegacyTurnTail', () => {
  it('a refused write reaches the client as a stable error code, with no successful finish', () => {
    const c = collect()
    writeLegacyTurnTail({
      ...BASE,
      writer: c.writer as never,
      emit: c.emit as never,
      writeThrough: {
        persisted: false,
        refusal: { code: 'CONVERSATION_ARCHIVED_READ_ONLY', message: 'This reading was not saved.' },
      },
    })
    const error = c.chunks.find((k) => k.type === 'error')
    expect(error).toBeDefined()
    expect(JSON.parse(error!.errorText)).toEqual({
      code: 'CONVERSATION_ARCHIVED_READ_ONLY',
      message: 'This reading was not saved.',
      retry: false,
    })
    expect(c.chunks.some((k) => k.type === 'finish')).toBe(false)
    expect(c.chunks.some((k) => k.type === 'data-judgment-flags')).toBe(false)
    expect(c.chunks.at(-1)?.type).toBe('error')
    // The observability trace still closes (it is not a client success signal).
    expect(c.events).toContainEqual({ event: 'done', query_id: 'q-1' })
  })

  it.each([
    ['a persisted turn', { persisted: true as const }],
    ['a turn with nothing to persist', undefined],
  ])('%s keeps the successful tail', (_label, writeThrough) => {
    const c = collect()
    writeLegacyTurnTail({ ...BASE, writer: c.writer as never, emit: c.emit as never, writeThrough })
    expect(c.chunks.some((k) => k.type === 'error')).toBe(false)
    expect(c.chunks).toContainEqual(expect.objectContaining({ type: 'finish', finishReason: 'stop' }))
    expect(c.chunks.some((k) => k.type === 'data-judgment-flags')).toBe(true)
    expect(c.events).toContainEqual({ event: 'done', query_id: 'q-1' })
  })
})
