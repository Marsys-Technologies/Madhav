/**
 * Paripraśna PB-1 (DHĀRĀ) hardening — honest grounding-grade rollup.
 * =========================================================================
 * Regression guard for the fabricated-verdict bug the PB-1 Verifier flagged:
 * the live adapter (`s1LiveAdapter`) and the dev fixture-playback adapter
 * (`c2ProtocolAdapter`) used to emit "Core claim: WELL-GROUNDED" whenever
 * `citationsSeen > 0` — i.e. a SINGLE citation of ANY grade produced a
 * confident WELL-GROUNDED verdict. That is a fabricated confident claim
 * (CLAUDE.md B.1/B.10; §6.7 "grade chips … never fabricated").
 *
 * These tests pin the honest behaviour: the confident label is derived ONLY
 * from the ACTUAL distribution of per-citation grades, and a single
 * weak/unverified citation can NEVER default to WELL-GROUNDED.
 */
import { describe, it, expect } from 'vitest'
import {
  emptyGradeTally,
  rollUpGradeSummaryLabel,
  tallyGrade,
  GRADE_SUMMARY_WELL_GROUNDED,
  GRADE_SUMMARY_SUPPORTED,
  GRADE_SUMMARY_CATALOG_ONLY,
  GRADE_SUMMARY_HONEST_GAP,
} from '@/components/pariprashna/state/groundingRollup'
import type { Grade } from '@/components/pariprashna/state/types'
import { makeS1LiveAdapter } from '@/components/pariprashna/state/s1LiveAdapter'
import type { CitationDefineEvent, TurnCommitEvent } from '@/lib/pariprashna/protocol/events'

function tallyOf(...grades: Grade[]) {
  const t = emptyGradeTally()
  for (const g of grades) tallyGrade(t, g)
  return t
}

describe('rollUpGradeSummaryLabel — honest grade rollup (pure)', () => {
  it('no citations at all → HONEST GAP (silence verified), never a confident verdict', () => {
    expect(rollUpGradeSummaryLabel(emptyGradeTally())).toBe(GRADE_SUMMARY_HONEST_GAP)
  })

  it('a SINGLE unverified citation does NOT produce WELL-GROUNDED — it is CATALOG-ONLY', () => {
    const label = rollUpGradeSummaryLabel(tallyOf('honest_gap'))
    expect(label).not.toBe(GRADE_SUMMARY_WELL_GROUNDED)
    expect(label).toBe(GRADE_SUMMARY_CATALOG_ONLY)
  })

  it('a SINGLE catalog-only citation does NOT produce WELL-GROUNDED — it is CATALOG-ONLY', () => {
    const label = rollUpGradeSummaryLabel(tallyOf('catalog'))
    expect(label).not.toBe(GRADE_SUMMARY_WELL_GROUNDED)
    expect(label).toBe(GRADE_SUMMARY_CATALOG_ONLY)
  })

  it('one confirmed + one catalog (mixed) → SUPPORTED, not WELL-GROUNDED', () => {
    const label = rollUpGradeSummaryLabel(tallyOf('confirmed', 'catalog'))
    expect(label).not.toBe(GRADE_SUMMARY_WELL_GROUNDED)
    expect(label).toBe(GRADE_SUMMARY_SUPPORTED)
  })

  it('supported-only (no confirmed anchor) → SUPPORTED, not WELL-GROUNDED', () => {
    const label = rollUpGradeSummaryLabel(tallyOf('supported', 'supported'))
    expect(label).not.toBe(GRADE_SUMMARY_WELL_GROUNDED)
    expect(label).toBe(GRADE_SUMMARY_SUPPORTED)
  })

  it('WELL-GROUNDED only when there is a confirmed anchor AND zero weak rows', () => {
    expect(rollUpGradeSummaryLabel(tallyOf('confirmed'))).toBe(GRADE_SUMMARY_WELL_GROUNDED)
    expect(rollUpGradeSummaryLabel(tallyOf('confirmed', 'supported'))).toBe(GRADE_SUMMARY_WELL_GROUNDED)
  })
})

// ── End-to-end through the LIVE adapter (the real doctrine-risk path) ─────────

function citationEvent(seq: number, index: number, grade?: string): CitationDefineEvent {
  return {
    type: 'citation.define',
    seq,
    t: 1_000 + seq,
    index,
    signal_id: `SIG.MSR.${index}`,
    layer: 'L2',
    snippet: `snippet ${index}`,
    ...(grade ? { grade } : {}),
  }
}

function commitEvent(seq: number): TurnCommitEvent {
  return {
    type: 'turn.commit',
    seq,
    t: 1_000 + seq,
    turn_id: 'server-turn',
    conversation_id: 'conv-1',
    message_id: 'msg-1',
    status: 'ok',
    assistant_chars: 42,
  }
}

/** Drive events through the adapter and return the synthesized grounding summary. */
function groundingFor(citationGrades: (string | undefined)[]) {
  const adapter = makeS1LiveAdapter('client-turn', 'Will my career shift this year?', Date.now())
  let seq = 0
  citationGrades.forEach((g, i) => adapter.map(citationEvent(seq++, i + 1, g)))
  const out = adapter.map(commitEvent(seq))
  const commit = out.find((e) => e.type === 'turn.commit')
  expect(commit && commit.type === 'turn.commit').toBe(true)
  return (commit as Extract<typeof commit, { type: 'turn.commit' }>).grounding
}

describe('makeS1LiveAdapter — turn.commit grounding is honest, not fabricated', () => {
  it('THE BUG: a single unverified citation no longer yields "Core claim: WELL-GROUNDED"', () => {
    const g = groundingFor(['unverified'])
    expect(g.gradeSummaryLabel).not.toBe(GRADE_SUMMARY_WELL_GROUNDED)
    expect(g.gradeSummaryLabel).toBe(GRADE_SUMMARY_CATALOG_ONLY)
  })

  it('a stream that carries NO grade at all rolls up to CATALOG-ONLY (absent grade → catalog)', () => {
    const g = groundingFor([undefined])
    expect(g.gradeSummaryLabel).not.toBe(GRADE_SUMMARY_WELL_GROUNDED)
    expect(g.gradeSummaryLabel).toBe(GRADE_SUMMARY_CATALOG_ONLY)
  })

  it('zero citations → HONEST GAP', () => {
    const g = groundingFor([])
    expect(g.factorCount).toBe(0)
    expect(g.gradeSummaryLabel).toBe(GRADE_SUMMARY_HONEST_GAP)
  })

  it('all-primary citations (S-3 strong grade) legitimately roll up to WELL-GROUNDED', () => {
    const g = groundingFor(['primary', 'primary'])
    expect(g.gradeSummaryLabel).toBe(GRADE_SUMMARY_WELL_GROUNDED)
  })

  it('mixed primary + contextual (catalog) rolls up to SUPPORTED, not WELL-GROUNDED', () => {
    const g = groundingFor(['primary', 'contextual'])
    expect(g.gradeSummaryLabel).toBe(GRADE_SUMMARY_SUPPORTED)
  })
})
