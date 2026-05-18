import { renderHook } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useDataParts } from '../useDataParts'
import type { NormalizedDataPart } from '../useDataParts'

type MinMsg = Parameters<typeof useDataParts>[0]

function msg(overrides: Partial<MinMsg> = {}): MinMsg {
  return { metadata: undefined, content: [], ...overrides }
}

describe('useDataParts', () => {
  it('empty case — both sources absent returns []', () => {
    const { result } = renderHook(() => useDataParts(msg()))
    expect(result.current).toEqual([])
  })

  it('metadata-only — unstable_data entry returns source:metadata', () => {
    const { result } = renderHook(() =>
      useDataParts(
        msg({
          metadata: {
            unstable_data: [{ type: 'data-stage', data: { name: 'planning', state: 'running' } }],
          },
        }),
      ),
    )
    expect(result.current).toHaveLength(1)
    expect(result.current[0]).toMatchObject<NormalizedDataPart>({
      type: 'data-stage',
      data: { name: 'planning', state: 'running' },
      source: 'metadata',
    })
  })

  it('content-only — DataMessagePart returns type data-<name>, source:content', () => {
    const { result } = renderHook(() =>
      useDataParts(
        msg({
          content: [{ type: 'data', name: 'citation', data: { signal_id: 'SIG.MSR.001' } }],
        }),
      ),
    )
    expect(result.current).toHaveLength(1)
    expect(result.current[0]).toMatchObject<NormalizedDataPart>({
      type: 'data-citation',
      data: { signal_id: 'SIG.MSR.001' },
      source: 'content',
    })
  })

  it('both sources — same logical part from each; no de-duplication (both entries present)', () => {
    const { result } = renderHook(() =>
      useDataParts(
        msg({
          metadata: {
            unstable_data: [{ type: 'data-stage', data: { stage: 'synthesis', status: 'running' } }],
          },
          content: [{ type: 'data', name: 'stage', data: { stage: 'synthesis', status: 'done' } }],
        }),
      ),
    )
    expect(result.current).toHaveLength(2)
    expect(result.current[0].source).toBe('metadata')
    expect(result.current[1].source).toBe('content')
  })

  it('filtering — non-data-* entries in unstable_data and non-data entries in content are ignored', () => {
    const { result } = renderHook(() =>
      useDataParts(
        msg({
          metadata: {
            unstable_data: [
              { type: 'data-stage', data: {} },    // valid — kept
              { type: 'other-thing', data: {} },    // no data- prefix — dropped
              'not-an-object',                       // not an object — dropped
            ],
          },
          content: [
            { type: 'data', name: 'citation', data: {} }, // valid — kept
            { type: 'text', text: 'hello' },               // not type:data — dropped
            { type: 'data' },                              // no name — dropped
          ],
        }),
      ),
    )
    expect(result.current).toHaveLength(2)
    expect(result.current[0].type).toBe('data-stage')
    expect(result.current[1].type).toBe('data-citation')
  })

  it('type narrowing — type field is inferred as data-${string} template literal', () => {
    const { result } = renderHook(() =>
      useDataParts(
        msg({
          metadata: { unstable_data: [{ type: 'data-custom-xyz', data: null }] },
        }),
      ),
    )
    const part = result.current[0]
    // Type assertion confirms compiler accepts template literal narrowing
    const t: `data-${string}` = part.type
    expect(t).toBe('data-custom-xyz')
  })
})
