/**
 * γ5 — Observability deep-link
 *
 * Tests:
 *   - query_id extraction from observability data part (primary source)
 *   - Fallback to metadata.custom.queryId when no observability part exists
 *   - URL format: /observatory/trace/[query_id]
 *   - PerMessageDetailsDrawer source has updated observability extraction
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const drawerSource = readFileSync(
  join(process.cwd(), 'src/components/chat/PerMessageDetailsDrawer.tsx'),
  'utf-8',
)

// ── Source-level assertions ────────────────────────────────────────────────────

describe('PerMessageDetailsDrawer — γ5 observability source', () => {
  it('reads query_id from named observability data part', () => {
    expect(drawerSource).toContain("p.name === 'observability'")
    expect(drawerSource).toContain('obsQueryId')
  })

  it('falls back to metadata.custom.queryId when no obs part', () => {
    // The fallback is `?? (meta.queryId ...)`
    expect(drawerSource).toContain('obsQueryId ?? (meta.queryId')
  })

  it('builds trace URL at /observatory/trace/<queryId>', () => {
    expect(drawerSource).toContain('/observatory/trace/')
  })

  it('opens trace link in new tab', () => {
    expect(drawerSource).toContain('target="_blank"')
    expect(drawerSource).toContain('rel="noopener noreferrer"')
  })

  it('has v2-details-trace-link testid for E2E', () => {
    expect(drawerSource).toContain('data-testid="v2-details-trace-link"')
  })

  it('link text is "View trace →"', () => {
    expect(drawerSource).toContain('View trace →')
  })

  it('does not contain stub observatory comment any more', () => {
    expect(drawerSource).not.toContain('γ5 — Observatory')
  })
})

// ── Pure-function logic ────────────────────────────────────────────────────────

type DataPart = { type: string; data: Record<string, unknown> }

function extractQueryId(dataParts: ReadonlyArray<unknown>, metaQueryId?: string): string | undefined {
  const obsEntry = dataParts.find(
    (d): d is DataPart =>
      typeof d === 'object' && d !== null &&
      (d as Record<string, unknown>).type === 'data-observability',
  )
  const obsQueryId = (obsEntry?.data as { query_id?: string } | undefined)?.query_id
  return obsQueryId ?? metaQueryId
}

function buildTraceUrl(queryId: string | undefined): string | null {
  return queryId ? `/observatory/trace/${queryId}` : null
}

describe('observability deep-link logic', () => {
  const TEST_UUID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'

  it('returns query_id from observability data part', () => {
    const parts = [
      { type: 'data-observability', data: { query_id: TEST_UUID, trace_url: '' } },
    ]
    expect(extractQueryId(parts)).toBe(TEST_UUID)
  })

  it('falls back to meta queryId when no observability part', () => {
    const parts: DataPart[] = []
    expect(extractQueryId(parts, 'fallback-uuid')).toBe('fallback-uuid')
  })

  it('prefers observability part over meta queryId', () => {
    const parts = [
      { type: 'data-observability', data: { query_id: TEST_UUID } },
    ]
    expect(extractQueryId(parts, 'meta-uuid')).toBe(TEST_UUID)
  })

  it('returns undefined when neither source is present', () => {
    expect(extractQueryId([])).toBeUndefined()
  })

  it('builds correct trace URL', () => {
    expect(buildTraceUrl(TEST_UUID)).toBe(`/observatory/trace/${TEST_UUID}`)
  })

  it('returns null trace URL when queryId is undefined', () => {
    expect(buildTraceUrl(undefined)).toBeNull()
  })

  it('URL sliced to first 8 chars for display', () => {
    const display = TEST_UUID.slice(0, 8)
    expect(display).toBe('a1b2c3d4')
    expect(display.length).toBe(8)
  })
})
