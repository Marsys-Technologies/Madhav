import { beforeEach, describe, expect, it, vi } from 'vitest'
import { query } from '@/lib/db/client'
import { queryFactCollection } from '../fact_collection'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

const base = "SELECT fact_id, fact_key, fact_value_num FROM chart_facts WHERE chart_id = $1 AND fact_category = 'strength'"

describe('queryFactCollection', () => {
  beforeEach(() => vi.clearAllMocks())

  it('passes the whole keyed page and its original parameters through', async () => {
    const result = {
      command: 'SELECT', rowCount: 2, oid: 0, fields: [],
      rows: [{ fact_id: 'a', fact_key: 'ratio' }, { fact_id: 'b', fact_key: 'rupa' }],
    }
    vi.mocked(query).mockResolvedValueOnce(result)
    const sql = base + ' ORDER BY fact_key LIMIT $2 OFFSET $3'
    const params = ['chart', 2, 0]
    await expect(queryFactCollection(sql, params)).resolves.toBe(result)
    expect(query).toHaveBeenCalledExactlyOnceWith(sql, params)
  })

  it.each([
    base + ' ORDER BY fact_value_num LIMIT 1',
    base + ' ORDER BY fact_value_num FETCH FIRST 1 ROW ONLY',
    base + ' ORDER BY fact_value_num LIMIT $2',
    base + ' ORDER BY fact_value_num LIMIT $2 OFFSET $3',
    base.replace('fact_id, fact_key, ', 'fact_id, '),
    base.replace('fact_id,', 'DISTINCT ON (fact_id) fact_id,'),
    base.replace('fact_value_num FROM', 'MAX(fact_value_num) OVER () FROM'),
    base + ' UNION ALL ' + base,
  ])('refuses a non-collection query before hitting the database', (sql) => {
    expect(() => queryFactCollection(sql, ['chart', 1, 0])).toThrow('Expected a chart-fact collection')
    expect(query).not.toHaveBeenCalled()
  })
})
