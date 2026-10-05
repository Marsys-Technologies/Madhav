import { describe, expect, it } from 'vitest'
import { orderVargaConfirmationRows } from '../register_d9_judgment'

/**
 * F-A2 reader fix: ashtakavarga bindus rows (12 per graha-varga after the key widening) must not sort ahead of
 * the placement / dignity rows that confirm the varga, because the response-budget trim keeps the head.
 */
describe('orderVargaConfirmationRows', () => {
  const r = (fact_category: string, fact_key: string, fact_subject: string) => ({ fact_category, fact_key, fact_subject })

  it('puts every non-bindus row first, bindus last, each group in served order', () => {
    const served = [
      r('varga_ashtakavarga', 'bindus', 'D9.SUN.S1'),
      r('varga_ashtakavarga', 'bindus', 'D9.SUN.S2'),
      r('varga_dignity', 'dignity', 'D9.SUN'),
      r('varga_position', 'sign', 'D9.SUN'),
      r('varga_vargottama_flag', 'vargottama', 'D9.SUN'),
    ]
    expect(orderVargaConfirmationRows(served).map(x => `${x.fact_category}:${x.fact_subject}`)).toEqual([
      'varga_dignity:D9.SUN',
      'varga_position:D9.SUN',
      'varga_vargottama_flag:D9.SUN',
      'varga_ashtakavarga:D9.SUN.S1',
      'varga_ashtakavarga:D9.SUN.S2',
    ])
  })

  it('keeps all rows (nothing dropped) and does not mutate its input', () => {
    const served = [r('varga_ashtakavarga', 'bindus', 'a'), r('varga_position', 'sign', 'b')]
    const copy = [...served]
    expect(orderVargaConfirmationRows(served)).toHaveLength(2)
    expect(served).toEqual(copy)
  })

  it('a head-keeping trim of the first 2 rows keeps placement and dignity, not bindus', () => {
    const served = [
      r('varga_ashtakavarga', 'bindus', 's1'), r('varga_ashtakavarga', 'bindus', 's2'),
      r('varga_dignity', 'dignity', 'd'), r('varga_position', 'sign', 'p'),
    ]
    expect(orderVargaConfirmationRows(served).slice(0, 2).map(x => x.fact_category)).toEqual(['varga_dignity', 'varga_position'])
  })
})
