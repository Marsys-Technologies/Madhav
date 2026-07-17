/**
 * scan_fetch.test.ts — D-2 Lane V-3, two-pass channel (ledger row 20).
 */
import { describe, it, expect } from 'vitest'
import { scan, fetchByIds, scanLine, parseScanLine, type ScanFetchConfig } from './scan_fetch.js'

type Row = { id: string; cls: string; sal: number; subj: string }
const cfg: ScanFetchConfig<Row> = {
  id: (r) => r.id,
  columns: [
    { key: 'cls', get: (r) => r.cls },
    { key: 'sal', get: (r) => r.sal },
    { key: 'subj', get: (r) => r.subj },
  ],
}
const rows: Row[] = Array.from({ length: 500 }, (_, i) => ({
  id: `s${i}`, cls: 'yoga', sal: Math.round((i / 500) * 1000) / 1000, subj: `graha_${i % 9}`,
}))

describe('scanLine', () => {
  it('builds a dense id-prefixed line', () => {
    const line = scanLine(rows[0], cfg)
    expect(line.startsWith('s0')).toBe(true)
    const parsed = parseScanLine(line, ['id', 'cls', 'sal', 'subj'])
    expect(parsed.id).toBe('s0')
    expect(parsed.cls).toBe('yoga')
    expect(parsed.subj).toBe('graha_0')
  })
  it('keeps lines dense (~60B target)', () => {
    const avg = rows.slice(0, 100).reduce((a, r) => a + Buffer.byteLength(scanLine(r, cfg), 'utf8'), 0) / 100
    expect(avg).toBeLessThan(60)
  })
})

describe('scan (Pass 1)', () => {
  it('reports the TRUE total even when truncated (truncation honesty)', () => {
    const res = scan(rows, cfg, 2000) // tiny cap forces truncation
    expect(res.total).toBe(500)
    expect(res.returned).toBeLessThan(500)
    expect(res.truncated).toBe(true)
    expect(res.next_step).toContain('total=500')
  })
  it('scans everything when the cap is generous', () => {
    const res = scan(rows, cfg, 100_000)
    expect(res.returned).toBe(500)
    expect(res.truncated).toBe(false)
  })
})

describe('fetchByIds (Pass 2)', () => {
  it('resolves ids picked from a scan to full rows', () => {
    const res = fetchByIds(rows, ['s3', 's7', 's99'], cfg)
    expect(res.resolved).toBe(3)
    expect(res.rows.map((r) => r.id).sort()).toEqual(['s3', 's7', 's99'])
    expect(res.missing_ids).toEqual([])
  })
  it('reports missing ids honestly (never silently drops)', () => {
    const res = fetchByIds(rows, ['s1', 'nope'], cfg)
    expect(res.resolved).toBe(1)
    expect(res.missing_ids).toEqual(['nope'])
  })
})
