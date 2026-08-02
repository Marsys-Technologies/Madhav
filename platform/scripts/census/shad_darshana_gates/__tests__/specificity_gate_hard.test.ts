/**
 * specificity_gate_hard.test.ts — ṢAḌ-DARŚANA W2 (lane w2-specificity-hard).
 *
 * Proves the HARD specificity criterion (brief §3 W2 "specificity gate HARD-green";
 * KALA_W2_FIELD_DESIGN §10 "composer templates must vary") has real teeth (§N.8
 * Earned-Signal: a gate that cannot fail is null, not green):
 *
 *   - NON-VACUITY: a deliberately-generic pair of readings (same template, only the
 *     chart name/numbers swapped) must FAIL the criterion — S2_MASKED_IDENTICAL.
 *   - Byte-identical readings must FAIL — S1_BYTE_IDENTICAL.
 *   - Two different charts' readings grounded in literally the same evidence
 *     fact-id set must FAIL — S3_IDENTICAL_EVIDENCE.
 *   - A genuinely chart-specific pair must PASS (no false-positive tripwire).
 *   - The gate's own embedded fixture self-checks (which run on EVERY invocation,
 *     PLAN and LIVE) agree with the above.
 *   - Script-level (execFileSync, PLAN mode): exit 0 on the real tree; exit 1 when
 *     the registration census is pointed at an empty tools root — proving PLAN mode
 *     no longer "exits 0 always" and the census FAIL path is live end-to-end.
 */
import { describe, it, expect } from 'vitest'
import { execFileSync } from 'node:child_process'
import { mkdtempSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  compareReadingPair,
  maskChartSpecificTokens,
  sentenceTemplateOverlap,
  runFixtureSelfChecks,
  NON_VACUITY_FIXTURES,
  type ReadingSample,
} from '../specificity_gate_v0'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const PLATFORM_ROOT = path.resolve(HERE, '..', '..', '..', '..')
const GATE = path.join('scripts', 'census', 'shad_darshana_gates', 'specificity_gate_v0.ts')
const TSX_BIN = path.join(PLATFORM_ROOT, 'node_modules', '.bin', 'tsx')

function sample(partial: Partial<ReadingSample> & { chart_id: string; text: string }): ReadingSample {
  return { fact_ids: [], aliases: [], ...partial }
}

describe('compareReadingPair — the HARD criterion', () => {
  it('S1: byte-identical reading text across two different charts FAILS', () => {
    const a = sample({ chart_id: 'aaaa1111', text: 'Saturn dasha demands discipline in career.' })
    const b = sample({ chart_id: 'bbbb2222', text: 'Saturn dasha demands discipline in career.' })
    const v = compareReadingPair(a, b)
    expect(v.pass).toBe(false)
    expect(v.criterion).toBe('S1_BYTE_IDENTICAL')
  })

  it('S2 (non-vacuity core): a generic template that differs ONLY by chart-name/number substitution FAILS', () => {
    const a = sample({
      chart_id: 'aaaa1111-0000-0000-0000-000000000000',
      text: 'For Abhisek, the current Saturn dasha (7.2 years remaining) demands discipline; Abhisek should expect career consolidation.',
      aliases: ['Abhisek'],
    })
    const b = sample({
      chart_id: 'bbbb2222-0000-0000-0000-000000000000',
      text: 'For Abhinandan, the current Saturn dasha (3.4 years remaining) demands discipline; Abhinandan should expect career consolidation.',
      aliases: ['Abhinandan'],
    })
    const v = compareReadingPair(a, b)
    expect(v.pass).toBe(false)
    expect(v.criterion).toBe('S2_MASKED_IDENTICAL')
  })

  it('S3: identical non-empty evidence fact-id sets across two different charts FAILS', () => {
    const a = sample({
      chart_id: 'aaaa1111',
      text: 'Jupiter return in the 10th brings visibility; the yoga fires from the lagna lord.',
      fact_ids: ['fact:1', 'fact:2'],
    })
    const b = sample({
      chart_id: 'bbbb2222',
      text: 'Venus period softens the 7th house; partnership themes dominate the window.',
      fact_ids: ['fact:2', 'fact:1'],
    })
    const v = compareReadingPair(a, b)
    expect(v.pass).toBe(false)
    expect(v.criterion).toBe('S3_IDENTICAL_EVIDENCE')
  })

  it('a genuinely chart-specific pair PASSES', () => {
    const a = sample({
      chart_id: 'aaaa1111',
      text: 'Aries lagna with Saturn in the 10th: the current Sade Sati third phase compresses career risk into Q3; the Capricorn stellium answers with structure.',
      fact_ids: ['a:1', 'a:2'],
      aliases: ['Abhisek'],
    })
    const b = sample({
      chart_id: 'bbbb2222',
      text: 'Cancer lagna, Moon-Jupiter gajakesari from the 4th: home and mother themes dominate; the Venus antardasha opens a property window before December.',
      fact_ids: ['b:9', 'b:10'],
      aliases: ['Abhinandan'],
    })
    const v = compareReadingPair(a, b)
    expect(v.pass).toBe(true)
    expect(v.criterion).toBeNull()
  })

  it('empty fact-id sets on both sides do NOT trigger S3 (an honest absence is not evidence of sharing)', () => {
    const a = sample({ chart_id: 'aaaa1111', text: 'Reading one, structurally distinct thesis.' })
    const b = sample({ chart_id: 'bbbb2222', text: 'A different verdict entirely, other grounds.' })
    expect(compareReadingPair(a, b).pass).toBe(true)
  })
})

describe('masking + template overlap arithmetic', () => {
  it('masks chart ids, aliases (case-insensitive) and digit runs', () => {
    const masked = maskChartSpecificTokens(
      'For Abhisek (chart 482012f1) Saturn has 7.2 years left; ABHISEK holds.',
      ['Abhisek', '482012f1'],
    )
    expect(masked).not.toMatch(/Abhisek/i)
    expect(masked).not.toContain('482012f1')
    expect(masked).not.toMatch(/\d/)
  })

  it('sentenceTemplateOverlap is 1.0 for same-template texts and low for disjoint texts', () => {
    const same = sentenceTemplateOverlap(
      'Saturn rules. Jupiter protects Abhisek.',
      'Saturn rules. Jupiter protects Abhinandan.',
      ['Abhisek', 'Abhinandan'],
    )
    expect(same).toBe(1)
    const disjoint = sentenceTemplateOverlap('Mars afflicts the seventh house.', 'Mercury blesses commerce and speech.', [])
    expect(disjoint).toBe(0)
  })
})

describe('embedded fixture self-checks (run on every gate invocation)', () => {
  it('all fixture self-checks PASS with the shipped comparator (no FAIL rows)', () => {
    const results = runFixtureSelfChecks()
    const fails = results.filter((r) => r.status === 'FAIL')
    expect(fails, JSON.stringify(fails, null, 2)).toEqual([])
    // and the battery is not vacuous itself: it must actually contain the generic-pair probe
    expect(results.map((r) => r.id)).toContain('specificity-selftest:generic_name_swap_pair')
  })

  it('the generic fixture pair is genuinely rejected by the comparator (non-vacuity witnessed directly)', () => {
    const { a, b } = NON_VACUITY_FIXTURES.generic_name_swap_pair
    expect(compareReadingPair(a, b).pass).toBe(false)
  })
})

describe('script-level PLAN mode (execFileSync)', () => {
  it('exits 0 on the real tree (all 8 tools registered, fixtures behave)', () => {
    const out = execFileSync(TSX_BIN, [GATE], {
      cwd: PLATFORM_ROOT,
      env: { ...process.env, MCP_SERVER_URL: '', MCP_BEARER: '' },
      encoding: 'utf-8',
    })
    expect(out).toContain('"FAIL": 0')
  }, 120_000)

  it('exits 1 when the registration census sees an empty tools root — PLAN mode CAN fail', () => {
    const emptyRoot = mkdtempSync(path.join(tmpdir(), 'shad-darshana-empty-tools-'))
    try {
      let code = 0
      try {
        execFileSync(TSX_BIN, [GATE], {
          cwd: PLATFORM_ROOT,
          env: { ...process.env, MCP_SERVER_URL: '', MCP_BEARER: '', SHAD_DARSHANA_MCP_TOOLS_ROOT: emptyRoot },
          encoding: 'utf-8',
        })
      } catch (err) {
        code = (err as { status?: number }).status ?? -1
      }
      expect(code).toBe(1)
    } finally {
      rmSync(emptyRoot, { recursive: true, force: true })
    }
  }, 120_000)
})
