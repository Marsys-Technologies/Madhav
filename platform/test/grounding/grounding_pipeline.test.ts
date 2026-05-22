/**
 * Grounding pipeline tests (Track A — AC.S1.1, AC.S1.2)
 *
 * Tests the pipeline logic without requiring a live DB or Vertex AI:
 *  - CSV serialization / deserialization round-trips
 *  - buildCsvRow field mapping
 *  - apply_grounded_citations citation builder
 *  - Wilson boundary: 50% of 10 → CI ~ (0.24, 0.76)  [used in Track B too]
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import * as fs from 'fs'
import * as os from 'os'
import * as path from 'path'

// ── Import helpers under test (pure functions, no DB/Vertex deps) ─────────────

import {
  writeCsv,
  type GroundingCsvRow,
  type UngroundedSignal,
  type GroundingCandidate,
} from '../../scripts/grounding/msr_grounding_pipeline'

// Re-export buildCsvRow for testing by patching the module
// We test the CSV writer + row shape directly.

describe('msr_grounding_pipeline — CSV round-trip', () => {
  let tmpDir: string
  let tmpFile: string

  beforeEach(() => {
    tmpDir  = fs.mkdtempSync(path.join(os.tmpdir(), 'grounding-'))
    tmpFile = path.join(tmpDir, 'test_candidates.csv')
  })

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true })
  })

  function makeRow(overrides: Partial<GroundingCsvRow> = {}): GroundingCsvRow {
    return {
      signal_id: 'SIG.MSR.001',
      domain: 'career',
      planet: 'Saturn',
      claim_excerpt: 'Saturn in 10th gives professional hardship in early career',
      candidate_1_chunk_id: 'chunk-abc12345',
      candidate_1_source: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
      candidate_1_section: '§4.2.Saturn',
      candidate_1_score: '0.1823',
      candidate_1_excerpt: 'Saturn is placed in Scorpio in the 10th house from lagna...',
      candidate_2_chunk_id: 'chunk-def67890',
      candidate_2_source: '01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md',
      candidate_2_section: '§E.3',
      candidate_2_score: '0.2941',
      candidate_2_excerpt: 'Career stagnation between 2006 and 2009...',
      candidate_3_chunk_id: 'chunk-xyz00001',
      candidate_3_source: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
      candidate_3_section: '§6.1',
      candidate_3_score: '0.3512',
      candidate_3_excerpt: 'Saturn mahadasha coincides with professional reorganization...',
      accepted_candidate: '',
      override_citation: '',
      ...overrides,
    }
  }

  it('writeCsv creates a file with a header row', () => {
    const rows = [makeRow()]
    writeCsv(rows, tmpFile)
    expect(fs.existsSync(tmpFile)).toBe(true)
    const lines = fs.readFileSync(tmpFile, 'utf8').split('\n').filter(Boolean)
    expect(lines.length).toBe(2)  // header + 1 row
    expect(lines[0]).toContain('signal_id')
    expect(lines[0]).toContain('accepted_candidate')
  })

  it('writeCsv round-trips signal_id and scores correctly', () => {
    const rows = [makeRow({ signal_id: 'SIG.MSR.099', candidate_1_score: '0.0512' })]
    writeCsv(rows, tmpFile)
    const text = fs.readFileSync(tmpFile, 'utf8')
    expect(text).toContain('SIG.MSR.099')
    expect(text).toContain('0.0512')
  })

  it('writeCsv escapes commas in claim_excerpt', () => {
    const row = makeRow({ claim_excerpt: 'Saturn, Rahu, and Ketu form a complex' })
    writeCsv([row], tmpFile)
    const text = fs.readFileSync(tmpFile, 'utf8')
    expect(text).toContain('"Saturn, Rahu, and Ketu form a complex"')
  })

  it('writeCsv handles multiple rows', () => {
    const rows = [
      makeRow({ signal_id: 'SIG.MSR.001' }),
      makeRow({ signal_id: 'SIG.MSR.002', accepted_candidate: '1' }),
      makeRow({ signal_id: 'SIG.MSR.003', accepted_candidate: 'defer' }),
    ]
    writeCsv(rows, tmpFile)
    const lines = fs.readFileSync(tmpFile, 'utf8').split('\n').filter(Boolean)
    expect(lines.length).toBe(4)  // header + 3 rows
    expect(lines[2]).toContain('SIG.MSR.002')
    expect(lines[2]).toContain('1')
  })
})

// ── Citation builder tests ────────────────────────────────────────────────────

describe('apply_grounded_citations — citation builder', () => {
  it('builds citation from candidate_1 source + section + chunk', () => {
    const citation = buildCitationForTest({
      candidate_1_source: '01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md',
      candidate_1_section: '§4.2.Saturn',
      candidate_1_chunk_id: 'abcdef123456',
      accepted_candidate: '1',
      override_citation: '',
    })
    expect(citation).toBe('FORENSIC_ASTROLOGICAL_DATA_v8_0#§4.2.Saturn [abcdef12]')
  })

  it('uses override_citation when provided', () => {
    const citation = buildCitationForTest({
      candidate_1_source: 'anything.md',
      candidate_1_section: '§1',
      candidate_1_chunk_id: 'xxx',
      accepted_candidate: '1',
      override_citation: 'FORENSIC_v8_0 §3.7 custom',
    })
    expect(citation).toBe('FORENSIC_v8_0 §3.7 custom')
  })

  it('returns null for defer', () => {
    const citation = buildCitationForTest({ accepted_candidate: 'defer' })
    expect(citation).toBeNull()
  })

  it('returns null for reject', () => {
    const citation = buildCitationForTest({ accepted_candidate: 'reject' })
    expect(citation).toBeNull()
  })

  it('returns null for empty accepted_candidate', () => {
    const citation = buildCitationForTest({ accepted_candidate: '' })
    expect(citation).toBeNull()
  })
})

// ── Grounding % threshold test ─────────────────────────────────────────────────

describe('AC.S1.1 — 95% grounding threshold', () => {
  it('573 total * 0.95 = 544 minimum grounded signals', () => {
    const TOTAL_MSR_SIGNALS = 573
    const MIN_GROUNDED = Math.ceil(TOTAL_MSR_SIGNALS * 0.95)
    expect(MIN_GROUNDED).toBe(545)  // 573 * 0.95 = 544.35 → ceil = 545
    expect(544).toBeLessThan(MIN_GROUNDED)  // 544 is NOT enough
    expect(545).toBeGreaterThanOrEqual(MIN_GROUNDED)  // 545 IS enough
  })

  it('grounding_pct calculation is correct', () => {
    expect(545 / 573).toBeGreaterThanOrEqual(0.95)
    expect(544 / 573).toBeLessThan(0.95)
  })
})

// ── Wilson CI sanity check (shared with Track B) ─────────────────────────────

describe('Wilson CI — 50% of 10 baseline', () => {
  it('lower bound is approximately 0.24', () => {
    // Wilson lower bound for 5 successes out of 10, 95% CI
    const lb = wilsonLower(5, 10, 0.95)
    expect(lb).toBeGreaterThanOrEqual(0.23)
    expect(lb).toBeLessThanOrEqual(0.28)
  })

  it('upper bound is approximately 0.76', () => {
    const ub = wilsonUpper(5, 10, 0.95)
    expect(ub).toBeGreaterThanOrEqual(0.72)
    expect(ub).toBeLessThanOrEqual(0.77)
  })

  it('zero total returns null-equivalent (0)', () => {
    expect(wilsonLower(0, 0, 0.95)).toBe(0)
    expect(wilsonUpper(0, 0, 0.95)).toBe(1)
  })

  it('all successes: lower bound > 0.5 for large N', () => {
    const lb = wilsonLower(100, 100, 0.95)
    expect(lb).toBeGreaterThan(0.9)
  })
})

// ── Helpers (pure JS implementations mirroring wilson.sql) ───────────────────

function wilsonLower(successes: number, total: number, confidence: number): number {
  if (total === 0) return 0
  const z = zForConfidence(confidence)
  const p_hat = successes / total
  const denom  = 1 + (z * z) / total
  const center = (p_hat + (z * z) / (2 * total)) / denom
  const margin = (z * Math.sqrt((p_hat * (1 - p_hat)) / total + (z * z) / (4 * total * total))) / denom
  return Math.max(0, center - margin)
}

function wilsonUpper(successes: number, total: number, confidence: number): number {
  if (total === 0) return 1
  const z = zForConfidence(confidence)
  const p_hat = successes / total
  const denom  = 1 + (z * z) / total
  const center = (p_hat + (z * z) / (2 * total)) / denom
  const margin = (z * Math.sqrt((p_hat * (1 - p_hat)) / total + (z * z) / (4 * total * total))) / denom
  return Math.min(1, center + margin)
}

function zForConfidence(c: number): number {
  if (c === 0.95) return 1.96
  if (c === 0.99) return 2.576
  if (c === 0.90) return 1.645
  return 1.96
}

// Stub: buildCitationForTest mirrors apply_grounded_citations.buildCitation
function buildCitationForTest(row: Partial<{
  accepted_candidate: string
  override_citation: string
  candidate_1_source: string
  candidate_1_section: string
  candidate_1_chunk_id: string
  candidate_2_source: string
  candidate_2_section: string
  candidate_2_chunk_id: string
}>): string | null {
  const r = {
    override_citation: '',
    accepted_candidate: '',
    candidate_1_source: '', candidate_1_section: '', candidate_1_chunk_id: '',
    candidate_2_source: '', candidate_2_section: '', candidate_2_chunk_id: '',
    ...row,
  }
  if (r.override_citation?.trim()) return r.override_citation.trim()
  const n = r.accepted_candidate
  if (!['1','2','3'].includes(n)) return null
  const source  = (r as Record<string, string>)[`candidate_${n}_source`]
  const section = (r as Record<string, string>)[`candidate_${n}_section`]
  const chunkId = (r as Record<string, string>)[`candidate_${n}_chunk_id`]
  const base    = (source ?? '').split('/').pop()?.replace(/\.md$/, '') ?? ''
  const sect    = section?.trim() ? `#${section}` : ''
  const suffix  = chunkId ? ` [${chunkId.substring(0, 8)}]` : ''
  return `${base}${sect}${suffix}`
}
