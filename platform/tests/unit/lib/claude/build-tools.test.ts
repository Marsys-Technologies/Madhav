import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

import { query } from '@/lib/db/client'

// list_documents, read_document, create_document, update_document,
// append_to_document, search_in_document and their GCS-storage tests
// removed in WS-0C Sub-E (documents table dropped in WS-0).

describe('buildTools', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('every tool has description and inputSchema', async () => {
    const { buildTools } = await import('@/lib/claude/build-tools')
    for (const t of Object.values(buildTools)) {
      expect(t).toHaveProperty('description')
      expect(t).toHaveProperty('inputSchema')
    }
  })

  it('includes required tool names', async () => {
    const { buildTools } = await import('@/lib/claude/build-tools')
    const names = Object.keys(buildTools)
    expect(names).toContain('run_ephemeris')
    expect(names).toContain('run_computation')
    expect(names).toContain('get_pyramid_status')
    expect(names).toContain('update_layer_status')
  })

  describe('get_pyramid_status', () => {
    it('returns pyramid layer statuses', async () => {
      const mockLayers = [
        { layer: 'L1', sublayer: 'facts', status: 'complete', version: '8.0', updated_at: '2026-01-01' },
        { layer: 'L2', sublayer: 'analysis_mode_a', status: 'in_progress', version: null, updated_at: '2026-01-02' },
        { layer: 'L2.5', sublayer: 'synthesis', status: 'not_started', version: null, updated_at: '2026-01-01' },
      ]
      ;(query as ReturnType<typeof vi.fn>).mockResolvedValue({ rows: mockLayers })

      const { buildTools } = await import('@/lib/claude/build-tools')
      const result = await buildTools.get_pyramid_status.execute!({ chart_id: 'chart-1' }, {} as never)
      expect(result).toEqual(mockLayers)
    })

    it('returns error on DB failure', async () => {
      ;(query as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Connection timeout'))

      const { buildTools } = await import('@/lib/claude/build-tools')
      const result = await buildTools.get_pyramid_status.execute!({ chart_id: 'chart-1' }, {} as never)
      expect(result).toEqual({ error: 'Connection timeout' })
    })
  })

  describe('update_layer_status', () => {
    it('upserts layer status and returns result', async () => {
      ;(query as ReturnType<typeof vi.fn>).mockResolvedValue({ rows: [] })

      const { buildTools } = await import('@/lib/claude/build-tools')
      const result = await buildTools.update_layer_status.execute!(
        { chart_id: 'chart-1', layer: 'L1', sublayer: 'facts', status: 'complete' },
        {} as never
      )
      expect(result).toEqual({ layer: 'L1', sublayer: 'facts', status: 'complete' })
      expect(query).toHaveBeenCalledWith(
        expect.stringContaining('pyramid_layers'),
        expect.arrayContaining(['chart-1', 'L1', 'facts', 'complete'])
      )
    })

    it('returns error on upsert failure', async () => {
      ;(query as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Upsert failed'))

      const { buildTools } = await import('@/lib/claude/build-tools')
      const result = await buildTools.update_layer_status.execute!(
        { chart_id: 'chart-1', layer: 'L1', sublayer: 'facts', status: 'in_progress' },
        {} as never
      )
      expect(result).toEqual({ error: 'Upsert failed' })
    })
  })
})
