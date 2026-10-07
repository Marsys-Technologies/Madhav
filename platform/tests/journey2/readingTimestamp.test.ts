import { describe, expect, it } from 'vitest'
import { savedReadingTimestamp } from '@/lib/conversations/readingTimestamp'

describe('saved reading timestamp provenance', () => {
  it('preserves the original instant from PostgreSQL dates and saved ISO metadata', () => {
    expect(savedReadingTimestamp({ createdAt: new Date('2026-07-31T20:03:13.586Z') }))
      .toBe('2026-07-31T20:03:13.586Z')
    expect(savedReadingTimestamp({ createdAt: '2026-08-01T01:33:13.586+05:30' }))
      .toBe('2026-07-31T20:03:13.586Z')
    expect(savedReadingTimestamp({ createdAt: '2026-07-31 20:03:13.586+00' }))
      .toBe('2026-07-31T20:03:13.586Z')
  })

  it('does not invent an export time when saved metadata is missing or invalid', () => {
    for (const metadata of [undefined, null, {}, { createdAt: 'yesterday' },
      { createdAt: '2026-13-40T20:03:13Z' }, { createdAt: new Date(NaN) }, { createdAt: 0 }]) {
      expect(savedReadingTimestamp(metadata)).toBeNull()
    }
  })
})
