import { beforeEach, describe, expect, it, vi } from 'vitest'
import { queryPlanetTransitCapability } from '../query_planet_transit'
import { CANONICAL_TRANSIT_PLANETS, queryCurrentTransitSnapshotCapability } from '../query_current_transit_snapshot'

describe('query_current_transit_snapshot aggregate capability', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('executes the strict scalar binding once per canonical graha and receipts every component', async () => {
    const handler = vi.spyOn(queryPlanetTransitCapability, 'handler').mockImplementation(async (args) => ({
      ok: true,
      planet: args['planet'],
      count: 1,
      rows: [{ planet: args['planet'], date: args['start_date'] }],
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
      : { ok: true, planet: args['planet'], count: 1, rows: [{ planet: args['planet'] }] })

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
