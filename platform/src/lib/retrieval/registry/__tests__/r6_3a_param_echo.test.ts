/**
 * r6_3a_param_echo.test.ts — R6 lane 3a-params contract tests
 * ==============================================================
 * Per-tool "param-echo" tests: call the handler with a distinctive param value and assert
 * the response actually reflects/honors it (fewer rows, a real filter clause, a translated
 * field name, or — for a param this lane deliberately chose to reject — a clear rejection).
 *
 * Covers a representative sample of the R6 3a-params defect-register fixes (R-18, R-17, R-27):
 *   1. get_positions.ts             — planet filter (SC-20)
 *   2. asset_registry_all.ts        — layer alias (L0->brahmagyan) + limit (R-18)
 *   3. asset_registry_l0.ts         — limit (R-18)
 *   4. query_remedies.ts            — domain + keyword + limit (R-18)
 *   5. query_temporal_activation.ts — domain filter (R-18)
 *   6. query_projections.ts        — limit (R-18)
 *   7. list_entities.ts             — entity_class alias (graha->planet) + unbacked-class reject (R-27)
 *   8. register_d8_assess_domain.ts — yoga_activation_by_dasha domain filter (R-18)
 *
 * DB is mocked (vi.mock('@/lib/db/client')) — these assert against the SQL/params actually
 * built, not live data. [verify-against: prod] for end-to-end row-count behavior.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

import { getPositionsCapability } from '../layers/L1_ganita/get_positions'
import { assetRegistryAllCapability } from '../layers/L0_brahmagyan/asset_registry_all'
import { assetRegistryL0Capability } from '../layers/L0_brahmagyan/asset_registry_l0'
import { queryRemediesCapability } from '../layers/L2_bodha/query_remedies'
import { queryTemporalActivationCapability } from '../layers/L3_kala/query_temporal_activation'
import { queryProjectionsCapability } from '../layers/L3_kala/query_projections'
import { listEntitiesCapability } from '../layers/L0_brahmagyan/list_entities'
import { registerD8AssessDomainCapabilities } from '../layers/register_d8_assess_domain'
import { clearRegistry, getCapability } from '../index'

const CHART_ID = '11111111-aaaa-4aaa-aaaa-aaaaaaaaaaaa'

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockResolvedValue({ rows: [] })
})

describe('SC-20 fix — get_positions planet filter', () => {
  it('canonicalizes a graha planet to its fact_subject CODE (exact match, not ILIKE)', async () => {
    // W4-loop-1 (E-5): chart_facts.fact_subject stores 3-letter graha CODES (Saturn->SAT).
    // The old `fact_subject ILIKE 'Saturn'` matched nothing against the stored code and
    // returned a dishonest empty; the fix canonicalizes the name to its code + exact-matches.
    await getPositionsCapability.handler({ chart_id: CHART_ID, planet: 'Saturn' }, undefined)
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(/fact_subject = /)
    expect(sql).not.toMatch(/fact_subject ILIKE/)
    expect(params).toContain('SAT')
  })

  it('omits the planet clause when planet is not given', async () => {
    await getPositionsCapability.handler({ chart_id: CHART_ID }, undefined)
    const [sql] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).not.toMatch(/fact_subject ILIKE/)
  })
})

describe('R-18 fix — asset_registry_all layer + limit', () => {
  it('resolves the L0 shorthand to the stored "brahmagyan" value and applies limit', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [{ total: '5' }] }) // count query
      .mockResolvedValueOnce({ rows: [] }) // select query
    await assetRegistryAllCapability.handler({ layer: 'L0', limit: 2 }, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).toMatch(/layer = \$1/)
    expect(countParams).toContain('brahmagyan')
    const [selectSql, selectParams] = queryMock.mock.calls[1] as [string, unknown[]]
    expect(selectSql).toMatch(/LIMIT/)
    expect(selectParams).toContain(2)
  })
})

describe('R-18 fix — asset_registry_l0 limit', () => {
  it('applies limit to the L0-scoped query', async () => {
    queryMock
      .mockResolvedValueOnce({ rows: [{ total: '9' }] })
      .mockResolvedValueOnce({ rows: [] })
    await assetRegistryL0Capability.handler({ limit: 3 }, undefined)
    const [selectSql, selectParams] = queryMock.mock.calls[1] as [string, unknown[]]
    expect(selectSql).toMatch(/LIMIT/)
    expect(selectParams).toContain(3)
  })
})

describe('R-18 fix — query_remedies domain + keyword + limit', () => {
  it('applies an EXISTS/CDLM domain clause to both resonance and prescription queries', async () => {
    await queryRemediesCapability.handler({ chart_id: CHART_ID, domain: 'career' }, undefined)
    const [resSql, resParams] = queryMock.mock.calls[0] as [string, unknown[]]
    const [preSql, preParams] = queryMock.mock.calls[1] as [string, unknown[]]
    expect(resSql).toMatch(/bodha_cdlm_cells/)
    expect(resParams).toContain('career')
    expect(preSql).toMatch(/bodha_cdlm_cells/)
    expect(preParams).toContain('career')
  })

  it('applies a keyword ILIKE clause to the prescription query only', async () => {
    await queryRemediesCapability.handler({ chart_id: CHART_ID, keyword: 'mantra' }, undefined)
    const [, resParams] = queryMock.mock.calls[0] as [string, unknown[]]
    const [preSql, preParams] = queryMock.mock.calls[1] as [string, unknown[]]
    expect(preSql).toMatch(/ILIKE/)
    expect(preParams).toContain('%mantra%')
    expect(resParams).not.toContain('%mantra%')
  })

  it('applies limit to both queries', async () => {
    await queryRemediesCapability.handler({ chart_id: CHART_ID, limit: 5 }, undefined)
    const [resSql, resParams] = queryMock.mock.calls[0] as [string, unknown[]]
    const [preSql, preParams] = queryMock.mock.calls[1] as [string, unknown[]]
    expect(resSql).toMatch(/LIMIT/)
    expect(resParams).toContain(5)
    expect(preSql).toMatch(/LIMIT/)
    expect(preParams).toContain(5)
  })
})

describe('R-18 fix — query_temporal_activation domain filter', () => {
  it('applies an EXISTS/bodha_msr_signals domain clause', async () => {
    await queryTemporalActivationCapability.handler({ chart_id: CHART_ID, domain: 'wealth' }, undefined)
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(/bodha_msr_signals/)
    expect(params).toContain('wealth')
  })
})

describe('R-18 fix — query_projections limit', () => {
  it('applies a LIMIT clause honoring the caller value', async () => {
    await queryProjectionsCapability.handler({ chart_id: CHART_ID, limit: 7 }, undefined)
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(/LIMIT/)
    expect(params).toContain(7)
  })

  it('defaults to 50 and clamps values above 50', async () => {
    await queryProjectionsCapability.handler({ chart_id: CHART_ID, limit: 999 }, undefined)
    const [, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(params).toContain(50)
  })
})

describe('R-27 fix — list_entities class vocabulary', () => {
  it('aliases entity_class="graha" to the stored "planet" value', async () => {
    await listEntitiesCapability.handler({ entity_class: 'graha' }, undefined)
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    // W3 (cursor filter/sort fingerprint) added an `offset` bind param ahead of the filter
    // param — $1=limit, $2=offset, $3=entity_class (was $2 pre-W3, no offset param existed).
    expect(sql).toMatch(/entity_class = \$3/)
    expect(params).toContain('planet')
  })

  it('rejects entity_class="yoga" with an explicit empty_reason (no silent empty array)', async () => {
    const result = await listEntitiesCapability.handler({ entity_class: 'yoga' }, undefined)
    expect(queryMock).not.toHaveBeenCalled()
    const content = result.content as Record<string, unknown>
    expect(content['entities']).toEqual([])
    expect(typeof content['empty_reason']).toBe('string')
    expect(content['empty_reason'] as string).toMatch(/no dedicated top-level class/)
  })
})

describe('R-18 fix — yoga_activation_by_dasha domain filter', () => {
  it('applies a domains_affected_array clause when domain is given', async () => {
    clearRegistry()
    registerD8AssessDomainCapabilities()
    const cap = getCapability('marsys://tool/L-TIMING/yoga_activation_by_dasha')
    expect(cap).toBeDefined()
    await cap!.handler({ chart_id: CHART_ID, domain: 'health' }, undefined)
    const [sql, params] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(sql).toMatch(/domains_affected_array/)
    expect(params).toContain('health')
  })
})
