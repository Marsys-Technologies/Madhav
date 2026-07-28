/**
 * PB-2 (SMṚTI) lane M-3 — render.ts: tool-part human-readable rendering.
 *
 * Proves the two hard rules from the brief:
 *   1. tool_call/tool_result parts NEVER render as a raw internal tool name or
 *      a '[multipart content]'-style placeholder — always
 *      "consulted <reader label> -> <result summary>".
 *   2. The rendered label is drawn from S-2's closed lexicon (reused, not
 *      reinvented) — leak-checked with the SAME `isLeakFree` /
 *      `INTERNAL_LEAK_PATTERNS` PB-1's own lexicon tests use as their model.
 */
import { describe, it, expect } from 'vitest'
import { isLeakFree, FALLBACK_READER_LABEL } from '@/lib/pariprashna/lexicon'
import { renderTurnsForSummary, resolveToolReaderLabel } from '../render'
import type { CanonicalTurn } from '../types'
import type { PersistedMessagePart } from '../../store/schema'

function part(p: Partial<PersistedMessagePart> & Pick<PersistedMessagePart, 'kind' | 'body' | 'seq'>): PersistedMessagePart {
  return {
    id: `part-${p.seq}`,
    message_id: 'm1',
    model_visible: true,
    created_at: new Date().toISOString(),
    ...p,
  }
}

describe('resolveToolReaderLabel', () => {
  it('resolves a REGISTERED + mapped tool name to its closed-lexicon label, never the raw name', () => {
    const label = resolveToolReaderLabel('query_dasha_periods')
    expect(label).not.toBe('query_dasha_periods')
    expect(label).not.toContain('query_dasha_periods')
    expect(isLeakFree(label)).toBe(true)
  })

  it('resolves an UNMAPPED/unknown tool name to the fallback label, never the raw name', () => {
    const label = resolveToolReaderLabel('some_totally_unmapped_tool_xyz')
    expect(label).toBe(FALLBACK_READER_LABEL)
    expect(label).not.toContain('some_totally_unmapped_tool_xyz')
  })
})

describe('renderTurnsForSummary — tool_call/tool_result rendering', () => {
  it('renders a tool_call+tool_result pair as "consulted <label> -> <result>", never a raw name or placeholder', () => {
    const turn: CanonicalTurn = {
      message_id: 'm1',
      role: 'assistant',
      parts: [
        part({
          seq: 0,
          kind: 'tool_call',
          body: { call_id: 'c1', tool_name: 'query_dasha_periods', args: {} },
        }),
        part({
          seq: 1,
          kind: 'tool_result',
          body: { call_id: 'c1', status: 'done', count: 3, ms: 120 },
        }),
      ],
    }

    const { text } = renderTurnsForSummary([turn])

    expect(text).toMatch(/^consulted .+ → 3 results in 120ms$/)
    expect(text).not.toContain('query_dasha_periods')
    expect(text).not.toContain('[multipart content]')
    expect(isLeakFree(text)).toBe(true)
  })

  it('an unmapped tool_call still renders a safe line (fallback label), never leaking the raw name', () => {
    const turn: CanonicalTurn = {
      message_id: 'm1',
      role: 'assistant',
      parts: [
        part({ seq: 0, kind: 'tool_call', body: { call_id: 'c1', tool_name: 'ga_some_internal_asset_query', args: {} } }),
        part({ seq: 1, kind: 'tool_result', body: { call_id: 'c1', status: 'done', count: 1 } }),
      ],
    }
    const { text } = renderTurnsForSummary([turn])
    expect(text).toContain(`consulted ${FALLBACK_READER_LABEL} →`)
    expect(text).not.toContain('ga_some_internal_asset_query')
    expect(isLeakFree(text)).toBe(true)
  })

  it('renders an error tool_result honestly, never fabricating a success summary', () => {
    const turn: CanonicalTurn = {
      message_id: 'm1',
      role: 'assistant',
      parts: [
        part({ seq: 0, kind: 'tool_call', body: { call_id: 'c1', tool_name: 'query_dasha_periods', args: {} } }),
        part({ seq: 1, kind: 'tool_result', body: { call_id: 'c1', status: 'error', detail: 'timeout' } }),
      ],
    }
    const { text } = renderTurnsForSummary([turn])
    expect(text).toContain('→ error — timeout')
  })

  it('renders text parts verbatim as prose lines', () => {
    const turn: CanonicalTurn = {
      message_id: 'm1',
      role: 'assistant',
      parts: [part({ seq: 0, kind: 'text', body: { text: 'Moon in Purva Bhadrapada.' } })],
    }
    const { text } = renderTurnsForSummary([turn])
    expect(text).toBe('Moon in Purva Bhadrapada.')
  })

  it('extracts citation parts separately from the rendered prose text', () => {
    const turn: CanonicalTurn = {
      message_id: 'm1',
      role: 'assistant',
      parts: [
        part({
          seq: 0,
          kind: 'citation',
          body: { index: 1, signal_id: 'SIG.MSR.042', layer: 'L2', snippet: 'Moon dignity note' },
        }),
      ],
    }
    const { text, citations } = renderTurnsForSummary([turn])
    expect(citations).toEqual([{ index: 1, signal_id: 'SIG.MSR.042', layer: 'L2', snippet: 'Moon dignity note' }])
    // Citations are not inlined into the prose text itself (they are appended
    // deterministically later, in appendCitationBlock) — the rendered TEXT for
    // an all-citation turn is empty.
    expect(text).toBe('')
  })

  it('prepends a prior summary seed as an "[Earlier context]" block', () => {
    const turn: CanonicalTurn = {
      message_id: 'm1',
      role: 'assistant',
      parts: [part({ seq: 0, kind: 'text', body: { text: 'New turn.' } })],
    }
    const { text } = renderTurnsForSummary([turn], 'Prior summary prose.')
    expect(text).toBe('[Earlier context]\nPrior summary prose.\nNew turn.')
  })
})
