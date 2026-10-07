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
    expect(savedReadingTimestamp({ createdAt: '2024-02-29T00:00:00Z' }))
      .toBe('2024-02-29T00:00:00.000Z')
    expect(savedReadingTimestamp({ createdAt: '2026-08-01 01:33:13.123456+05:30' }))
      .toBe('2026-07-31T20:03:13.123456Z')
  })

  it('does not invent an export time when saved metadata is missing or invalid', () => {
    for (const metadata of [undefined, null, {}, { createdAt: 'yesterday' },
      { createdAt: '2026-13-40T20:03:13Z' }, { createdAt: new Date(NaN) }, { createdAt: 0 },
      ...['2026-02-29', '2026-02-30', '2026-02-31', '2026-04-31'].map(date => ({ createdAt: `${date}T10:00:00Z` })),
      { createdAt: '2026-01-01T24:00:00Z' }, { createdAt: '2026-01-01T00:60:00Z' },
      { createdAt: '2026-01-01T00:00:60Z' }, { createdAt: '2026-01-01T00:00:00+24:00' }]) {
      expect(savedReadingTimestamp(metadata)).toBeNull()
    }
  })
})
