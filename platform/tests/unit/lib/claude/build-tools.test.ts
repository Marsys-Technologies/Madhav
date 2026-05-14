import { describe, it, expect, vi, beforeEach } from 'vitest'

// build-tools.ts uses @/lib/db/client (query) and @/lib/storage/client (gcs ops)
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(),
}))

vi.mock('@/lib/storage/client', () => ({
  chartDocsBucket: vi.fn().mockReturnValue({}),
  gcsDownloadText: vi.fn(),
  gcsUpload: vi.fn(),
  gcsDelete: vi.fn(),
}))

import { query } from '@/lib/db/client'

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
    expect(names).toContain('list_documents')
    expect(names).toContain('read_document')
    expect(names).toContain('create_document')
    expect(names).toContain('update_document')
    expect(names).toContain('run_ephemeris')
    expect(names).toContain('get_pyramid_status')
    expect(names).toContain('append_to_document')
    expect(names).toContain('update_layer_status')
    expect(names).toContain('run_computation')
    expect(names).toContain('search_in_document')
  })

  describe('list_documents', () => {
    it('returns documents array for a chart', async () => {
      const mockDocs = [
        { id: 'doc-1', name: 'forensic_data', layer: 'L1', version: '8.0', updated_at: '2026-01-01' },
        { id: 'doc-2', name: 'holistic_synthesis', layer: 'L2.5', version: '1.0', updated_at: '2026-01-02' },
      ]
      ;(query as ReturnType<typeof vi.fn>).mockResolvedValue({ rows: mockDocs })

      const { buildTools } = await import('@/lib/claude/build-tools')
      const result = await buildTools.list_documents.execute!({ chart_id: 'chart-1' }, {} as never)
      expect(result).toEqual(mockDocs)
    })

    it('returns documents filtered by layer', async () => {
      const mockDocs = [
        { id: 'doc-1', name: 'forensic_data', layer: 'L1', version: '8.0', updated_at: '2026-01-01' },
      ]
      ;(query as ReturnType<typeof vi.fn>).mockResolvedValue({ rows: mockDocs })

      const { buildTools } = await import('@/lib/claude/build-tools')
      const result = await buildTools.list_documents.execute!({ chart_id: 'chart-1', layer: 'L1' }, {} as never)
      expect(result).toEqual(mockDocs)
    })

    it('returns error object on DB failure', async () => {
      ;(query as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('DB error'))

      const { buildTools } = await import('@/lib/claude/build-tools')
      const result = await buildTools.list_documents.execute!({ chart_id: 'chart-1' }, {} as never)
      expect(result).toEqual({ error: 'DB error' })
    })
  })

  describe('read_document', () => {
    it('returns document content', async () => {
      const mockRow = {
        id: 'doc-1',
        name: 'forensic_data',
        layer: 'L1',
        version: '8.0',
        storage_path: 'charts/chart-1/L1/forensic_data_v8.0.md',
      }
      const mockContent = '# Forensic Astrological Data\n\nContent here.'

      ;(query as ReturnType<typeof vi.fn>).mockResolvedValue({ rows: [mockRow] })
      const { gcsDownloadText } = await import('@/lib/storage/client')
      ;(gcsDownloadText as ReturnType<typeof vi.fn>).mockResolvedValue(mockContent)

      const { buildTools } = await import('@/lib/claude/build-tools')
      const result = await buildTools.read_document.execute!({ chart_id: 'chart-1', name: 'forensic_data' }, {} as never)
      expect(result).toEqual({
        name: 'forensic_data',
        layer: 'L1',
        version: '8.0',
        content: mockContent,
      })
    })

    it('returns error when document not found', async () => {
      ;(query as ReturnType<typeof vi.fn>).mockResolvedValue({ rows: [] })

      const { buildTools } = await import('@/lib/claude/build-tools')
      const result = await buildTools.read_document.execute!({ chart_id: 'chart-1', name: 'missing' }, {} as never)
      expect(result).toEqual({ error: 'Document not found' })
    })
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
