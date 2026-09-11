import { describe, expect, it } from 'vitest'

import { readSqlScalarMetric } from '../scalarMetric'

describe('readSqlScalarMetric', () => {
  it('reads a conventionally aliased count', () => {
    expect(readSqlScalarMetric({ count: '42' }, 'count')).toBe(42)
  })

  it('reads an unaliased single-column compound count', () => {
    expect(readSqlScalarMetric({ '?column?': '440' }, 'count')).toBe(440)
  })

  it('keeps nullable size results nullable', () => {
    expect(readSqlScalarMetric({ size: null }, 'size', { nullable: true })).toBeNull()
  })

  it('rejects a missing result instead of silently reporting zero', () => {
    expect(() => readSqlScalarMetric(undefined, 'count')).toThrow(/returned no row/i)
  })

  it('rejects an ambiguous unaliased result', () => {
    expect(() => readSqlScalarMetric({ first: '1', second: '2' }, 'count')).toThrow(/expected alias/i)
  })

  it.each(['12 rows', '-1', '1.5', Number.NaN, Number.POSITIVE_INFINITY])(
    'rejects an invalid metric value %p',
    (value) => {
      expect(() => readSqlScalarMetric({ count: value }, 'count')).toThrow(/non-negative safe integer/i)
    },
  )
})
