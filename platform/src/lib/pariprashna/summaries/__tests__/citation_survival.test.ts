/**
 * PB-2 (SMṚTI) lane M-3 — citation-preservation fixture.
 *
 * The brief's requirement, verbatim: "any citation-kind message_parts within
 * the summarized range must have their signal_id/fact-id references survive
 * VERBATIM into the summary text ... a later grounding-gate check must be
 * able to resolve them; don't let the LLM-generated summary silently drop or
 * paraphrase-away a citation reference."
 *
 * `appendCitationBlock` is the mechanism that GUARANTEES this independently of
 * what any LLM worker produces: it deterministically appends every citation's
 * signal_id/layer/snippet verbatim after the LLM's prose, always. These tests
 * exercise that guarantee directly, plus prove it holds end-to-end through
 * `getOrCreateSummary` with a worker stub that (adversarially) drops every
 * citation from its own prose — the persisted summary_text must still resolve
 * every original signal_id.
 */
import { describe, it, expect } from 'vitest'
import { appendCitationBlock, renderTurnsForSummary, type CitationLine } from '../render'
import { getOrCreateSummary } from '../service'
import type { CanonicalTurn, SummarizerWorker, SummaryStore, ConversationSummaryRow } from '../types'
import type { PersistedMessagePart } from '../../store/schema'

const FIXTURE_CITATIONS: CitationLine[] = [
  { index: 1, signal_id: 'SIG.MSR.042', layer: 'L2', snippet: 'Moon dignity note.' },
  { index: 2, signal_id: 'SIG.CGM.017', layer: 'L2', snippet: 'Cross-domain link.' },
  { index: 3, signal_id: 'FACT.CHART.9981', layer: 'L1', snippet: 'Lagna degree.' },
]

describe('appendCitationBlock — deterministic verbatim survival', () => {
  it('every fixture signal_id survives verbatim in the appended block', () => {
    const out = appendCitationBlock('A short LLM-produced summary that mentions nothing specific.', FIXTURE_CITATIONS)
    for (const c of FIXTURE_CITATIONS) {
      expect(out).toContain(c.signal_id)
      expect(out).toContain(c.snippet)
    }
  })

  it('survives even when the LLM prose ITSELF never mentions any citation', () => {
    const adversarialProse = 'The native shows strength in career matters this period.'
    const out = appendCitationBlock(adversarialProse, FIXTURE_CITATIONS)
    expect(out).toContain(adversarialProse)
    for (const c of FIXTURE_CITATIONS) expect(out).toContain(c.signal_id)
  })

  it('no citations -> prose returned unchanged (trimmed), no empty block appended', () => {
    const out = appendCitationBlock('  plain prose  ', [])
    expect(out).toBe('plain prose')
  })

  it('citations are ordered by their original index, not insertion order', () => {
    const shuffled = [FIXTURE_CITATIONS[2], FIXTURE_CITATIONS[0], FIXTURE_CITATIONS[1]]
    const out = appendCitationBlock('prose', shuffled)
    const idx1 = out.indexOf('SIG.MSR.042')
    const idx2 = out.indexOf('SIG.CGM.017')
    const idx3 = out.indexOf('FACT.CHART.9981')
    expect(idx1).toBeLessThan(idx2)
    expect(idx2).toBeLessThan(idx3)
  })
})

function part(p: Partial<PersistedMessagePart> & Pick<PersistedMessagePart, 'kind' | 'body' | 'seq'>): PersistedMessagePart {
  return { id: `part-${p.seq}`, message_id: 'm', model_visible: true, created_at: new Date().toISOString(), ...p }
}

/** An in-memory fake store — see service.test.ts for the fuller reuse-on-restart suite. */
class FakeSummaryStore implements SummaryStore {
  rows: ConversationSummaryRow[] = []
  async findLatest(conversationId: string): Promise<ConversationSummaryRow | null> {
    const matches = this.rows.filter((r) => r.conversation_id === conversationId)
    return matches.at(-1) ?? null
  }
  async insert(row: Parameters<SummaryStore['insert']>[0]): Promise<ConversationSummaryRow> {
    const inserted: ConversationSummaryRow = { id: `row-${this.rows.length}`, created_at: new Date().toISOString(), ...row }
    this.rows.push(inserted)
    return inserted
  }
}

/** An adversarial worker: always drops citations from its own prose. */
class AdversarialCitationDroppingWorker implements SummarizerWorker {
  async summarize(): Promise<string> {
    return 'A generic summary with zero citation mentions whatsoever.'
  }
  lastModelId(): string {
    return 'adversarial-test-worker'
  }
}

describe('getOrCreateSummary — end-to-end citation survival through persistence', () => {
  it('persisted summary_text resolves every citation even when the worker drops them all', async () => {
    // 8 turns: with the default verbatim-tail of 2, this leaves 6 eligible
    // turns (indices 0-5) — exactly DEFAULT_SUMMARIZE_EVERY_N_MESSAGES, so the
    // threshold crosses on this single call. Citations sit at index 3, safely
    // inside the eligible (summarized) range, not the reserved tail.
    const turns: CanonicalTurn[] = Array.from({ length: 8 }, (_, i) => ({
      message_id: `msg-${i}`,
      role: (i % 2 === 0 ? 'user' : 'assistant') as CanonicalTurn['role'],
      parts:
        i === 3
          ? [
              part({ seq: 0, kind: 'citation', body: { index: 1, signal_id: 'SIG.MSR.042', layer: 'L2', snippet: 'Moon note' } }),
              part({ seq: 1, kind: 'citation', body: { index: 2, signal_id: 'FACT.CHART.9981', layer: 'L1', snippet: 'Lagna degree' } }),
            ]
          : [part({ seq: 0, kind: 'text', body: { text: `turn ${i} text` } })],
    }))

    const store = new FakeSummaryStore()
    const worker = new AdversarialCitationDroppingWorker()

    const result = await getOrCreateSummary({ store, worker }, { conversationId: 'conv-1', turns })

    expect(result.created).toBe(true)
    expect(result.summary).not.toBeNull()
    expect(result.summary!.summary_text).toContain('SIG.MSR.042')
    expect(result.summary!.summary_text).toContain('FACT.CHART.9981')
  })
})

describe('renderTurnsForSummary + appendCitationBlock composition', () => {
  it('a fixture with mixed text + citation parts preserves citations verbatim after summarization', () => {
    const turn: CanonicalTurn = {
      message_id: 'm1',
      role: 'assistant',
      parts: [
        part({ seq: 0, kind: 'text', body: { text: 'Discussing career timing.' } }),
        part({ seq: 1, kind: 'citation', body: { index: 1, signal_id: 'SIG.MSR.042', layer: 'L2', snippet: 'Moon dignity note.' } }),
      ],
    }
    const rendered = renderTurnsForSummary([turn])
    const finalText = appendCitationBlock('Summarized prose without the citation id.', rendered.citations)
    expect(finalText).toContain('SIG.MSR.042')
    expect(finalText).toContain('Moon dignity note.')
  })
})
