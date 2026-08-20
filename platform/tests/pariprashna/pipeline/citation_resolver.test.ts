/**
 * G2-B "Citations at first paint" (PPR-08, FD-2/FD-6) —
 * `pipeline/citation_resolver.ts`.
 *
 * Proves the resolver's epistemic scope claim directly: a ref that WAS part
 * of this turn's retrieved evidence resolves (grade `primary`); a ref that
 * was NOT — even if it is a perfectly real id elsewhere — resolves to null
 * (the honest "not grounded for this answer" outcome the rewriter turns into
 * `unverified` + a hallucination-counter increment).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const { queryMock } = vi.hoisted(() => ({ queryMock: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('server-only', () => ({}))

import {
  extractCandidateSignalIds,
  fetchCandidateSignalLabels,
  buildTurnCitationResolver,
} from '@/lib/pariprashna/pipeline/citation_resolver'
import type { ToolBundle } from '@/lib/retrieval/shared_types'

function toolBundle(toolName: string, contents: string[]): ToolBundle {
  return {
    tool_name: toolName,
    results: contents.map((content) => ({ content })),
  } as unknown as ToolBundle
}

describe('extractCandidateSignalIds', () => {
  it('scans every tool result for SIG.MSR.NNN-shaped ids, deduplicated', () => {
    const ids = extractCandidateSignalIds({
      validToolResults: [
        toolBundle('msr_sql', ['signal_id=SIG.MSR.001 fired', 'also SIG.MSR.002 and SIG.MSR.001 again']),
        toolBundle('cgm_graph_walk', ['no signal ids in this one']),
      ],
    })
    expect(ids.sort()).toEqual(['SIG.MSR.001', 'SIG.MSR.002'])
  })

  it('returns [] when nothing matches', () => {
    expect(extractCandidateSignalIds({ validToolResults: [] })).toEqual([])
  })
})

describe('fetchCandidateSignalLabels', () => {
  beforeEach(() => queryMock.mockReset())

  it('resolves grade primary for every row the query returns', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [{ signal_id: 'SIG.MSR.413', name: 'Mercury convergence', description: 'a deep dive' }],
    })
    const labels = await fetchCandidateSignalLabels(['SIG.MSR.413'])
    expect(labels.get('SIG.MSR.413')).toEqual({
      reader_label: 'Mercury convergence — a deep dive',
      grade: 'primary',
    })
  })

  it('returns an empty map (never throws) when the query fails', async () => {
    queryMock.mockRejectedValueOnce(new Error('db unavailable'))
    const labels = await fetchCandidateSignalLabels(['SIG.MSR.413'])
    expect(labels.size).toBe(0)
  })

  it('short-circuits to an empty map with zero candidate ids (no query call)', async () => {
    const labels = await fetchCandidateSignalLabels([])
    expect(labels.size).toBe(0)
    expect(queryMock).not.toHaveBeenCalled()
  })
})

describe('buildTurnCitationResolver — epistemic scope', () => {
  it('a ref that WAS part of this turn evidence resolves, grade primary', () => {
    const labels = new Map([['SIG.MSR.413', { reader_label: 'Mercury convergence', grade: 'primary' as const }]])
    const resolver = buildTurnCitationResolver(labels)
    const resolved = resolver.resolve('SIG.MSR.413')
    expect(resolved).not.toBeNull()
    expect(resolved?.grade).toBe('primary')
    expect(resolved?.reader_label).toBe('Mercury convergence')
    expect(resolved?.audit_detail).toContain('SIG.MSR.413')
  })

  it('a ref that was NOT part of this turn evidence resolves to null (never borrows a grade)', () => {
    const labels = new Map([['SIG.MSR.413', { reader_label: 'Mercury convergence', grade: 'primary' as const }]])
    const resolver = buildTurnCitationResolver(labels)
    // A real-looking id, but absent from THIS turn's prefetched map.
    expect(resolver.resolve('SIG.MSR.999')).toBeNull()
  })

  it('readerLabel mirrors the same map for the register-leak lint REWRITE path', () => {
    const labels = new Map([['SIG.MSR.413', { reader_label: 'Mercury convergence', grade: 'primary' as const }]])
    const resolver = buildTurnCitationResolver(labels)
    expect(resolver.readerLabel('SIG.MSR.413')).toBe('Mercury convergence')
    expect(resolver.readerLabel('SIG.MSR.999')).toBeNull()
  })
})
