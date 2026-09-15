import { beforeEach, describe, expect, it, vi } from 'vitest'
import { queryPlanetTransitCapability } from '../query_planet_transit'
import { CANONICAL_TRANSIT_PLANETS, queryCurrentTransitSnapshotCapability } from '../query_current_transit_snapshot'
import { getToolByName } from '../../../tool_name_bridge'
import { getCatalog } from '../../../catalog'

describe('query_current_transit_snapshot aggregate capability', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('declares the exact nine-unit fan-out weight for atomic broker admission', () => {
    getCatalog()
    expect(queryCurrentTransitSnapshotCapability.dispatch_units).toBe(9)
    expect(getToolByName('query_current_transit_snapshot')?.dispatch_units).toBe(9)
  })

  it('executes the strict scalar binding once per canonical graha and receipts every component', async () => {
    const handler = vi.spyOn(queryPlanetTransitCapability, 'handler').mockImplementation(async (args) => ({
      ok: true,
      planet: args['planet'],
      window: { start: args['start_date'], end: args['end_date'] },
      count: 1,
      rows: [{ body: args['planet'], date: args['start_date'] }],
    }))

    const result = await queryCurrentTransitSnapshotCapability.handler!({ as_of_date: '2026-09-15' }) as Record<string, unknown>
    const components = result['components'] as Array<Record<string, unknown>>

    expect(handler).toHaveBeenCalledTimes(9)
    expect(handler.mock.calls.map(([args]) => args)).toEqual(CANONICAL_TRANSIT_PLANETS.map((planet) => ({
      planet,
      start_date: '2026-09-15',
      end_date: '2026-09-15',
    })))
    expect(result).toMatchObject({ ok: true, complete: true, expected_components: 9, accounted_components: 9, missing_planets: [] })
    expect(components).toHaveLength(9)
    expect(components.every((component) => component['status'] === 'served'
      && typeof component['args_hash'] === 'string'
      && typeof component['result_hash'] === 'string')).toBe(true)
  })

  it('fails the aggregate honestly when one scalar component fails', async () => {
    vi.spyOn(queryPlanetTransitCapability, 'handler').mockImplementation(async (args) => args['planet'] === 'Ketu'
      ? { ok: false, error: 'sidecar failure', count: 0, rows: [] }
      : {
          ok: true,
          planet: args['planet'],
          window: { start: args['start_date'], end: args['end_date'] },
          count: 1,
          rows: [{ body: args['planet'], date: args['start_date'] }],
        })

    const result = await queryCurrentTransitSnapshotCapability.handler!({ as_of_date: '2026-09-15' }) as Record<string, unknown>

    expect(result).toMatchObject({
      ok: false,
      complete: false,
      expected_components: 9,
      accounted_components: 8,
      missing_planets: ['Ketu'],
      error: 'CURRENT_TRANSIT_SNAPSHOT_INCOMPLETE',
    })
  })

  it('fails closed when every scalar call dishonestly returns the Sun component', async () => {
    vi.spyOn(queryPlanetTransitCapability, 'handler').mockResolvedValue({
      ok: true,
      planet: 'Sun',
      window: { start: '2026-09-15', end: '2026-09-15' },
      count: 1,
      rows: [{ body: 'Sun', date: '2026-09-15' }],
    })

    const result = await queryCurrentTransitSnapshotCapability.handler!({ as_of_date: '2026-09-15' }) as Record<string, unknown>
    const components = result['components'] as Array<Record<string, unknown>>

    expect(result).toMatchObject({
      ok: false,
      complete: false,
      accounted_components: 1,
      missing_planets: CANONICAL_TRANSIT_PLANETS.slice(1),
      error: 'CURRENT_TRANSIT_SNAPSHOT_INCOMPLETE',
    })
    expect(components[0]).toMatchObject({ planet: 'Sun', status: 'served' })
    expect(components.slice(1).every((component) => component['status'] === 'failed'
      && component['error'] === 'SCALAR_TRANSIT_IDENTITY_MISMATCH')).toBe(true)
  })

  it.each(['', '2026-02-30', '2026/09/15', '1899-12-31', '2151-01-01'])(
    'rejects an invalid or unsupported anchor %j before dispatch',
    async (asOfDate) => {
      const handler = vi.spyOn(queryPlanetTransitCapability, 'handler')
      const result = await queryCurrentTransitSnapshotCapability.handler!({ as_of_date: asOfDate }) as Record<string, unknown>
      expect(result).toMatchObject({ ok: false, complete: false, error: 'INVALID_TEMPORAL_ANCHOR_DATE' })
      expect(handler).not.toHaveBeenCalled()
    },
  )
})
