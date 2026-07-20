/**
 * list_entities_cursor_w3.test.ts — W3 cursor filter/sort fingerprint, end-to-end through a
 * real capability handler (`query` mocked, no live DB required — matches the project's
 * established mocking pattern, e.g. get_vichara.test.ts).
 *
 * Covers the three required scenarios from the W3-L4 brief:
 *   1. same filters + cursor replay → same continuing page, no mismatch flag.
 *   2. different filters + old cursor → mismatch flag fires, does NOT silently return the
 *      wrong family's page.
 *   3. cursor round-trips correctly for a call with no filter at all (offset-only case,
 *      no regression).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { listEntitiesCapability } from '../list_entities'
import { decodeCursorFull } from '@/lib/retrieval/envelope'

type Content = Record<string, unknown>

function mockRowsThenCount(rows: Array<Record<string, unknown>>, total: number) {
  mockQuery.mockResolvedValueOnce({ rows }) // main SELECT
  mockQuery.mockResolvedValueOnce({ rows: [{ total }] }) // COUNT
}

const PLANET_ROWS_PAGE1 = Array.from({ length: 2 }, (_, i) => ({ canonical_id: `planet_${i}`, entity_class: 'planet' }))
const PLANET_ROWS_PAGE2 = Array.from({ length: 2 }, (_, i) => ({ canonical_id: `planet_${i + 2}`, entity_class: 'planet' }))
const SIGN_ROWS_PAGE1 = Array.from({ length: 2 }, (_, i) => ({ canonical_id: `sign_${i}`, entity_class: 'sign' }))

describe('list_entities — W3 cursor filter/sort fingerprint', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('1. same filters + cursor replay → same continuing page, no mismatch flag', async () => {
    // Page 1: entity_class=planet, no cursor.
    mockRowsThenCount(PLANET_ROWS_PAGE1, 4) // total 4 planets, 2 more beyond page 1
    const page1 = await listEntitiesCapability.handler({ entity_class: 'planet', limit: 2 }, undefined)
    const c1 = page1.content as Content
    expect(c1.judgment_flags).toEqual([])
    expect(c1.more_available).toBe(true)
    const cursor = c1.next_cursor as string
    expect(cursor).toBeTruthy()
    expect(decodeCursorFull(cursor)?.offset).toBe(2)

    // Page 2: SAME entity_class=planet, replay the cursor from page 1.
    mockRowsThenCount(PLANET_ROWS_PAGE2, 4)
    const page2 = await listEntitiesCapability.handler({ entity_class: 'planet', limit: 2, cursor }, undefined)
    const c2 = page2.content as Content
    expect(c2.judgment_flags).toEqual([]) // no mismatch — genuine continuation
    expect(c2.entities).toEqual(PLANET_ROWS_PAGE2)
    expect(c2.more_available).toBe(false) // offset(2) + served(2) === total(4)

    // Confirm the SELECT for page 2 actually used offset=2 (the decoded cursor offset),
    // not offset=0 — proves this is a real continuation, not a restart.
    const page2SelectParams = mockQuery.mock.calls[mockQuery.mock.calls.length - 2][1] as unknown[]
    expect(page2SelectParams).toEqual([2, 2, 'planet']) // [limit, offset, resolvedClass]
  })

  it("2. different filters + old cursor → mismatch flag fires, does NOT silently return the wrong family's page", async () => {
    // Mint a cursor under entity_class=planet.
    mockRowsThenCount(PLANET_ROWS_PAGE1, 4)
    const page1 = await listEntitiesCapability.handler({ entity_class: 'planet', limit: 2 }, undefined)
    const staleCursor = (page1.content as Content).next_cursor as string
    expect(decodeCursorFull(staleCursor)?.offset).toBe(2)

    // Replay it under a DIFFERENT filter: entity_class=sign.
    mockRowsThenCount(SIGN_ROWS_PAGE1, 12)
    const mismatchResult = await listEntitiesCapability.handler(
      { entity_class: 'sign', limit: 2, cursor: staleCursor },
      undefined,
    )
    const c = mismatchResult.content as Content
    expect(c.judgment_flags).toEqual(['cursor_filter_mismatch'])
    expect(c.cursor_filter_mismatch_note).toBeDefined()
    // Must NOT silently return "page 2" of the sign family at the stale offset=2 — it must
    // restart at offset 0 for the current (sign) filter.
    const selectParams = mockQuery.mock.calls[mockQuery.mock.calls.length - 2][1] as unknown[]
    expect(selectParams).toEqual([2, 0, 'sign']) // offset forced back to 0, never the stale 2
    expect(c.entities).toEqual(SIGN_ROWS_PAGE1)
  })

  it('3. cursor round-trips correctly for a call with no filter at all (offset-only case, no regression)', async () => {
    // Page 1: no entity_class filter at all.
    mockRowsThenCount([{ canonical_id: 'a' }, { canonical_id: 'b' }], 5)
    const page1 = await listEntitiesCapability.handler({ limit: 2 }, undefined)
    const c1 = page1.content as Content
    expect(c1.judgment_flags).toEqual([])
    const cursor = c1.next_cursor as string
    expect(decodeCursorFull(cursor)?.offset).toBe(2)

    // Replay with the SAME (absent) filter — must still be a clean continuation, no mismatch.
    mockRowsThenCount([{ canonical_id: 'c' }, { canonical_id: 'd' }], 5)
    const page2 = await listEntitiesCapability.handler({ limit: 2, cursor }, undefined)
    const c2 = page2.content as Content
    expect(c2.judgment_flags).toEqual([])
    const selectParams = mockQuery.mock.calls[mockQuery.mock.calls.length - 2][1] as unknown[]
    expect(selectParams).toEqual([2, 2]) // [limit, offset] — no resolvedClass param at all
  })

  it('no cursor supplied at all behaves exactly as before (offset 0, no flags)', async () => {
    mockRowsThenCount(PLANET_ROWS_PAGE1, 2)
    const res = await listEntitiesCapability.handler({ entity_class: 'planet', limit: 2 }, undefined)
    const c = res.content as Content
    expect(c.judgment_flags).toEqual([])
    expect(c.more_available).toBe(false)
    const selectParams = mockQuery.mock.calls[mockQuery.mock.calls.length - 2][1] as unknown[]
    expect(selectParams).toEqual([2, 0, 'planet'])
  })
})
