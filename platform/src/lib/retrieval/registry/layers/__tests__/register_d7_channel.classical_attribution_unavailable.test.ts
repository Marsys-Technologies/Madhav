import { describe, expect, it, vi } from 'vitest'
import { getCatalog } from '../../catalog'

vi.mock('server-only', () => ({}))

const CLASSICAL_ATTRIBUTION_URI = 'marsys://tool/L2/classical_attribution_lookup'

describe('classical_attribution_lookup source closure', () => {
  it('fails closed instead of presenting the retired attribution store as an empty successful lookup', async () => {
    const capability = getCatalog().find((candidate) =>
      candidate.uri === CLASSICAL_ATTRIBUTION_URI,
    )
    expect(capability).toBeDefined()

    const response = await capability!.handler({
      chart_id: '11111111-1111-4111-8111-111111111111',
      signal_ids: ['SIG.MSR.042'],
    })

    expect(response.is_error).toBe(true)
    expect(response.content).toMatchObject({
      code: 'CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE',
    })
    expect(response.content).not.toHaveProperty('attributions')
  })

  it('describes itself as unavailable and names the classical corpus surface instead of promising attributions', () => {
    const capability = getCatalog().find((candidate) => candidate.uri === CLASSICAL_ATTRIBUTION_URI)!
    expect(capability.description).toMatch(/^UNAVAILABLE — fails closed\./)
    expect(capability.description).toContain('CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE')
    expect(capability.description).toContain('query_classical_texts')
    expect(capability.description).not.toMatch(/Provides the classical grounding/)
  })

  it('throws the typed source-unavailable error from the underlying lookup (never signal_ids_silent)', async () => {
    const {
      classical_attribution_lookup,
      ClassicalAttributionSourceUnavailableError,
      CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE,
    } = await import('@/lib/tools/classical_attribution_lookup')

    const pending = classical_attribution_lookup({ signal_ids: ['SIG.MSR.042'] })
    await expect(pending).rejects.toBeInstanceOf(ClassicalAttributionSourceUnavailableError)
    await expect(pending).rejects.toMatchObject({ code: CLASSICAL_ATTRIBUTION_SOURCE_UNAVAILABLE })
  })

  it('no registered capability advertises a drill edge into the unavailable attribution route', () => {
    const pointing = getCatalog()
      .filter((candidate) => (candidate.drill_children ?? []).includes(CLASSICAL_ATTRIBUTION_URI))
      .map((candidate) => candidate.name)
    expect(pointing).toEqual([])
  })
})
