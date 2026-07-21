/**
 * w5_l8_listcapabilities_filters.test.ts — W5 Lane L8 ("listCapabilities filters" / W-13)
 * ==========================================================================================
 * Proves the new filter dimensions added to the DB-backed asset_registry catalog surface
 * (marsys://resource/asset-registry/all + marsys://resource/asset-registry/L0 — the ONLY
 * listCapabilities-shaped surface actually exposed to end users today, served by
 * list_assets / catalog_assets_list / catalog_assets_all / catalog_assets_l0 /
 * asset_registry_l0) actually narrow the query — not just accepted-and-silently-ignored.
 *
 * DB is mocked (same convention as r6_3a_param_echo.test.ts): each case asserts the SQL
 * WHERE clause and bound params actually built for a given filter combination, since a
 * mocked query() cannot itself narrow rows — the narrowing happens in Postgres in
 * production. [verify-against: prod] for live row-count behavior.
 *
 * Cases:
 *   1-5. Each new filter dimension (asset_type, catalog_status, scope, is_active,
 *        has_writer) narrows the WHERE clause + bound params on its own.
 *   6.   Combined multi-filter case — all dimensions AND-combined in one call.
 *   7.   No-filter case — identical to pre-W5-L8 behavior (no WHERE clause at all),
 *        proving backward compatibility.
 *   8-9. Same coverage for the L0-scoped sibling (asset_registry_l0.ts), which always
 *        carries the fixed `layer = 'brahmagyan'` clause AND-combined with the new filters.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => queryMock(...args),
}))

import { assetRegistryAllCapability } from '../layers/L0_brahmagyan/asset_registry_all'
import { assetRegistryL0Capability } from '../layers/L0_brahmagyan/asset_registry_l0'

beforeEach(() => {
  queryMock.mockReset()
  queryMock.mockResolvedValue({ rows: [] })
})

describe('W5 L8 — asset_registry_all new filter dimensions', () => {
  it('asset_type narrows the WHERE clause + bound params', async () => {
    await assetRegistryAllCapability.handler({ asset_type: 'service' }, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).toMatch(/asset_type = \$1/)
    expect(countParams).toContain('service')
    const [selectSql, selectParams] = queryMock.mock.calls[1] as [string, unknown[]]
    expect(selectSql).toMatch(/asset_type = \$1/)
    expect(selectParams).toContain('service')
  })

  it('catalog_status narrows the WHERE clause + bound params (case-insensitive input)', async () => {
    await assetRegistryAllCapability.handler({ catalog_status: 'draft' }, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).toMatch(/catalog_status = \$1/)
    expect(countParams).toContain('DRAFT')
  })

  it('scope narrows the WHERE clause + bound params', async () => {
    await assetRegistryAllCapability.handler({ scope: 'per_chart' }, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).toMatch(/scope = \$1/)
    expect(countParams).toContain('per_chart')
  })

  it('is_active narrows the WHERE clause + bound params, including explicit false', async () => {
    await assetRegistryAllCapability.handler({ is_active: false }, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).toMatch(/is_active = \$1/)
    expect(countParams).toContain(false)
  })

  it('has_writer narrows the WHERE clause + bound params', async () => {
    await assetRegistryAllCapability.handler({ has_writer: true }, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).toMatch(/has_writer = \$1/)
    expect(countParams).toContain(true)
  })

  it('combined multi-filter case: layer + asset_type + catalog_status + scope + is_active + has_writer all AND-combined', async () => {
    await assetRegistryAllCapability.handler({
      layer: 'L2', asset_type: 'data', catalog_status: 'CURRENT',
      scope: 'per_chart', is_active: true, has_writer: true, limit: 10,
    }, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    // All six conditions present, AND-joined, in the order the handler builds them.
    expect(countSql).toMatch(
      /layer = \$1 AND asset_type = \$2 AND catalog_status = \$3 AND scope = \$4 AND is_active = \$5 AND has_writer = \$6/
    )
    expect(countParams).toEqual(['bodha', 'data', 'CURRENT', 'per_chart', true, true])

    const [selectSql, selectParams] = queryMock.mock.calls[1] as [string, unknown[]]
    expect(selectSql).toMatch(/LIMIT/)
    // select params = the 6 filter binds + limit + offset(0)
    expect(selectParams).toEqual(['bodha', 'data', 'CURRENT', 'per_chart', true, true, 10, 0])
  })

  it('no-filter case returns the full unfiltered set unchanged (backward compatible: no WHERE clause at all)', async () => {
    await assetRegistryAllCapability.handler({}, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).not.toMatch(/WHERE/)
    expect(countParams).toEqual([])
    const [selectSql] = queryMock.mock.calls[1] as [string, unknown[]]
    expect(selectSql).not.toMatch(/WHERE/)
    // Full column set now includes the previously-unselected asset_type/catalog_status/has_writer.
    expect(selectSql).toMatch(/asset_type, catalog_status, has_writer/)
  })
})

describe('W5 L8 — asset_registry_l0 new filter dimensions (AND-combined with the fixed L0 layer clause)', () => {
  it('asset_type narrows the WHERE clause alongside the fixed brahmagyan layer clause', async () => {
    await assetRegistryL0Capability.handler({ asset_type: 'service' }, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).toMatch(/ar\.layer = 'brahmagyan' AND ar\.asset_type = \$1/)
    expect(countParams).toContain('service')
  })

  it('combined multi-filter case on the L0 slice', async () => {
    await assetRegistryL0Capability.handler({
      catalog_status: 'CURRENT', scope: 'global', is_active: true, has_writer: true,
    }, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).toMatch(
      /ar\.layer = 'brahmagyan' AND ar\.catalog_status = \$1 AND ar\.scope = \$2 AND ar\.is_active = \$3 AND ar\.has_writer = \$4/
    )
    expect(countParams).toEqual(['CURRENT', 'global', true, true])
  })

  it('no-filter case on the L0 slice returns the unfiltered L0 set unchanged (backward compatible)', async () => {
    await assetRegistryL0Capability.handler({}, undefined)
    const [countSql, countParams] = queryMock.mock.calls[0] as [string, unknown[]]
    expect(countSql).toMatch(/WHERE ar\.layer = 'brahmagyan'$/)
    expect(countParams).toEqual([])
  })
})
