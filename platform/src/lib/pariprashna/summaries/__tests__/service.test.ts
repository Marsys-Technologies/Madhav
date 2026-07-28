/**
 * PB-2 (SMṚTI) lane M-3 — service.ts: threshold + reuse-on-restart.
 *
 * The brief's requirement, verbatim: "the summarizer writes the row once per
 * threshold crossing and reuses it across process restarts — test that
 * calling your 'should we summarize?' check twice for the same conversation
 * state doesn't re-summarize (zero re-summarize call to the LLM on a cache
 * hit)."
 *
 * A process restart has no in-memory state to lose here by construction:
 * `getOrCreateSummary` takes its ENTIRE state from the injected `store`
 * (`findLatest`/`insert`) and the caller-supplied `turns` array — there is no
 * module-level cache to reset. So "two independent calls against the same
 * store state" IS the restart scenario: a fresh process would call
 * `getOrCreateSummary` exactly the same way, with `deps.store` reading
 * whatever a prior process already persisted.
 */
import { describe, it, expect, vi } from 'vitest'
import { getOrCreateSummary } from '../service'
import { DEFAULT_SUMMARIZE_EVERY_N_MESSAGES, DEFAULT_VERBATIM_TAIL_MESSAGES, shouldSummarize } from '../threshold'
import type { CanonicalTurn, ConversationSummaryRow, SummarizerWorker, SummaryStore } from '../types'
import type { PersistedMessagePart } from '../../store/schema'

function textTurn(messageId: string, text: string): CanonicalTurn {
  const part: PersistedMessagePart = {
    id: `${messageId}-p0`,
    message_id: messageId,
    seq: 0,
    kind: 'text',
    body: { text },
    model_visible: true,
    created_at: new Date().toISOString(),
  }
  return { message_id: messageId, role: 'assistant', parts: [part] }
}

class FakeSummaryStore implements SummaryStore {
  rows: ConversationSummaryRow[] = []
  async findLatest(conversationId: string): Promise<ConversationSummaryRow | null> {
    const matches = this.rows.filter((r) => r.conversation_id === conversationId)
    return matches.at(-1) ?? null
  }
  async insert(row: Parameters<SummaryStore['insert']>[0]): Promise<ConversationSummaryRow> {
    const inserted: ConversationSummaryRow = {
      id: `row-${this.rows.length}`,
      created_at: new Date(Date.now() + this.rows.length).toISOString(),
      ...row,
    }
    this.rows.push(inserted)
    return inserted
  }
}

class CountingWorker implements SummarizerWorker {
  callCount = 0
  async summarize(input: Parameters<SummarizerWorker['summarize']>[0]): Promise<string> {
    void input
    this.callCount += 1
    return `summary produced by call #${this.callCount}`
  }
  lastModelId(): string {
    return 'test-worker-model'
  }
}

describe('threshold.shouldSummarize — pure decision', () => {
  it('false below the default threshold, true at/above it', () => {
    expect(shouldSummarize({ eligibleNewMessageCount: DEFAULT_SUMMARIZE_EVERY_N_MESSAGES - 1 })).toBe(false)
    expect(shouldSummarize({ eligibleNewMessageCount: DEFAULT_SUMMARIZE_EVERY_N_MESSAGES })).toBe(true)
    expect(shouldSummarize({ eligibleNewMessageCount: DEFAULT_SUMMARIZE_EVERY_N_MESSAGES + 5 })).toBe(true)
  })

  it('honors a custom everyN', () => {
    expect(shouldSummarize({ eligibleNewMessageCount: 2 }, 3)).toBe(false)
    expect(shouldSummarize({ eligibleNewMessageCount: 3 }, 3)).toBe(true)
  })
})

describe('getOrCreateSummary — threshold + reuse-on-restart', () => {
  it('below threshold: no summary yet, ZERO worker calls', async () => {
    const store = new FakeSummaryStore()
    const worker = new CountingWorker()
    // Fewer turns than DEFAULT_SUMMARIZE_EVERY_N_MESSAGES + verbatim tail.
    const turns = [textTurn('m0', 't0'), textTurn('m1', 't1')]

    const result = await getOrCreateSummary({ store, worker }, { conversationId: 'conv-below', turns })

    expect(result.summary).toBeNull()
    expect(result.created).toBe(false)
    expect(worker.callCount).toBe(0)
  })

  it('at threshold: writes exactly ONE new row, ONE worker call', async () => {
    const store = new FakeSummaryStore()
    const worker = new CountingWorker()
    const turnCount = DEFAULT_SUMMARIZE_EVERY_N_MESSAGES + DEFAULT_VERBATIM_TAIL_MESSAGES
    const turns = Array.from({ length: turnCount }, (_, i) => textTurn(`m${i}`, `t${i}`))

    const result = await getOrCreateSummary({ store, worker }, { conversationId: 'conv-cross', turns })

    expect(result.created).toBe(true)
    expect(result.summary).not.toBeNull()
    expect(worker.callCount).toBe(1)
    expect(store.rows.length).toBe(1)
  })

  it('REUSE-ON-RESTART: calling getOrCreateSummary a SECOND time with the SAME store state ' +
    '(no new turns since the summary that was just written) makes ZERO additional worker calls', async () => {
    const store = new FakeSummaryStore()
    const worker = new CountingWorker()
    const turnCount = DEFAULT_SUMMARIZE_EVERY_N_MESSAGES + DEFAULT_VERBATIM_TAIL_MESSAGES
    const turns = Array.from({ length: turnCount }, (_, i) => textTurn(`m${i}`, `t${i}`))

    // First call — a real process crosses the threshold and writes the row.
    const first = await getOrCreateSummary({ store, worker }, { conversationId: 'conv-restart', turns })
    expect(first.created).toBe(true)
    expect(worker.callCount).toBe(1)

    // "Restart": a FRESH call, same store/turns (as a fresh process would see
    // after reading the same persisted state back). This is the cache-hit path.
    const second = await getOrCreateSummary({ store, worker }, { conversationId: 'conv-restart', turns })

    expect(second.created).toBe(false)
    expect(second.summary).toEqual(first.summary)
    // The load-bearing assertion: the LLM was NOT called again.
    expect(worker.callCount).toBe(1)
    expect(store.rows.length).toBe(1)
  })

  it('a THIRD call after enough NEW turns accrue crosses the threshold again — exactly one more ' +
    'worker call, and the new summary folds the prior one in as its seed', async () => {
    const store = new FakeSummaryStore()
    const worker = new CountingWorker()
    const summarizeSpy = vi.spyOn(worker, 'summarize')

    const firstBatchCount = DEFAULT_SUMMARIZE_EVERY_N_MESSAGES + DEFAULT_VERBATIM_TAIL_MESSAGES
    const firstBatch = Array.from({ length: firstBatchCount }, (_, i) => textTurn(`m${i}`, `t${i}`))
    await getOrCreateSummary({ store, worker }, { conversationId: 'conv-again', turns: firstBatch })
    expect(worker.callCount).toBe(1)

    // Same conversation state — cache hit, still 1 call.
    await getOrCreateSummary({ store, worker }, { conversationId: 'conv-again', turns: firstBatch })
    expect(worker.callCount).toBe(1)

    // Now enough NEW turns accrue past the verbatim tail to cross again.
    const moreTurns = [
      ...firstBatch,
      ...Array.from({ length: DEFAULT_SUMMARIZE_EVERY_N_MESSAGES + DEFAULT_VERBATIM_TAIL_MESSAGES }, (_, i) =>
        textTurn(`m${firstBatchCount + i}`, `t${firstBatchCount + i}`),
      ),
    ]
    const third = await getOrCreateSummary({ store, worker }, { conversationId: 'conv-again', turns: moreTurns })

    expect(third.created).toBe(true)
    expect(worker.callCount).toBe(2)
    expect(store.rows.length).toBe(2)
    // The seed (prior summary) was passed to renderTurnsForSummary via
    // summarize()'s renderedText — check the second call's input carried it.
    const secondCallInput = summarizeSpy.mock.calls[1][0]
    expect(secondCallInput.renderedText).toContain('[Earlier context]')
  })
})
