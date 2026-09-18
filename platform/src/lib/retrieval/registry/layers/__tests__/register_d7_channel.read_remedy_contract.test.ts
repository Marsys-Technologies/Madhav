import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))

import { query } from '@/lib/db/client'
import { clearRegistry, getCapability } from '../../index'
import { registerD7ChannelCapabilities } from '../register_d7_channel'

const mockQuery = vi.mocked(query)

const EXPECTED_PROJECTION = [
  'id',
  'remedy_id',
  'planet',
  'domain',
  'remedy_type',
  'prescription_text',
  'mantra_text',
  'gemstone',
  'charity_action',
  'day_of_week',
  'color_associated',
  'confidence',
  'source_canonical_id',
  'source_citation',
  'classical_ref',
  'created_at',
  'category',
  'deity',
  'mantra_sanskrit',
  'mantra_transliteration',
  'ingredients_jsonb',
  'timing_rules_jsonb',
  'cost_tier',
  'contraindications',
  'classical_attestation_text',
  'scaffold_status',
] as const

describe('read_remedy handler contract', () => {
  beforeEach(() => {
    clearRegistry()
    registerD7ChannelCapabilities()
    mockQuery.mockReset()
  })

  it('queries the complete governed remedy projection by stable slug without changing filter semantics', async () => {
    const remedy = { remedy_id: 'sat_career_mantra_01', scaffold_status: 'review' }
    mockQuery.mockResolvedValue({ rows: [remedy] } as never)
    const cap = getCapability('marsys://tool/L0/read_remedy')!

    const result = await cap.handler({ remedy_id: remedy.remedy_id })

    expect(mockQuery).toHaveBeenCalledTimes(1)
    const [sql, params] = mockQuery.mock.calls[0]!
    const normalizedSql = String(sql).replace(/\s+/g, ' ').trim()
    expect(normalizedSql).toBe(
      `SELECT ${EXPECTED_PROJECTION.join(', ')} FROM brahma_remedy_corpus WHERE remedy_id = $1`,
    )
    expect(normalizedSql).not.toContain('SELECT *')
    expect(normalizedSql).not.toContain('scaffold_status =')
    expect(params).toEqual([remedy.remedy_id])
    expect(result).toEqual({
      content: { remedy_id: remedy.remedy_id, remedy, found: true },
      is_error: false,
    })
  })

  it('describes remedy_id as the stable TEXT slug defined by the authoritative DDL', () => {
    const cap = getCapability('marsys://tool/L0/read_remedy')!
    const remedyIdSchema = (cap.input_schema?.['remedy_id'] ?? {}) as { description?: string }

    expect(cap.description).toContain('stable TEXT remedy slug')
    expect(remedyIdSchema.description).toContain('Stable TEXT remedy slug')
    expect(`${cap.description} ${remedyIdSchema.description}`).not.toMatch(/\bUUID\b/)
  })
})
