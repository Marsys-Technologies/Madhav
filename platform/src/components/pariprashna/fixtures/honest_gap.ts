import { FixtureBuilder } from './builder'
import type { Fixture } from './types'

/**
 * J7 — an honest-gap answer (two-option gap). Exercises the gap ribbon as a
 * distinct, commit-only block type, and a grounding summary whose grade
 * reads "Honest gap" rather than "well-grounded" — the gap is still a
 * grounded answer (P2/P5): the grounding is how we know it's silent.
 */
export function buildHonestGapFixture(turnId = 't-gap'): Fixture {
  const userText = 'Should I take the Dubai offer or the Singapore one?'
  const b = new FixtureBuilder(turnId)

  b.turnOpen(userText)
  b.phase('Reading the question')
  b.activity({ id: 'g1', passIndex: 0, label: 'Reading the whole chart', detail: 'relocation, timing', kind: 'reasoning', durationMs: 800, ms: '0.8s' })
  b.activity({ id: 'g2', passIndex: 0, label: 'Retrieved — transit windows', detail: '9 windows', kind: 'tool', durationMs: 500, ms: '0.5s' })
  b.activity({ id: 'g3', passIndex: 0, label: 'Verifying every claim', detail: 'grounding gate · 4/4', kind: 'reasoning', durationMs: 600, ms: '0.6s' })

  b.citation(
    { n: 1, title: 'Favorable relocation window opens Q3 2026', sourceClass: 'computed_window', relevance: 'Transit anchor, verified.', ref: 'ga_transit_anchors · Jup→H4 2026-08', grade: 'confirmed' },
    b.cursor(),
  )

  b.advance(200)
  b.streamedBlock({
    blockId: 'gb1',
    role: 'verdict',
    text: 'The chart speaks clearly to the timing of a move, and much less clearly to its destination.',
  })
  b.advance(200)
  b.streamedBlock({
    blockId: 'gb2',
    role: 'elaboration',
    text: 'A window opens in the third quarter of 2026 that favors relocation generally⟦1⟧ — the character of the period is expansive, outward-facing, well-aspected for a cross-border move.',
  })
  b.advance(150)
  b.commitOnlyBlock({
    blockId: 'gb-ribbon',
    kind: 'gap_ribbon',
    gapText:
      'Between these two, the chart is silent — no factor consulted distinguishes them. The choice is yours on other grounds; the chart speaks to the timing either way.',
  })

  b.advance(150)
  b.turnCommit({
    factorCount: 4,
    classicalCount: 0,
    elapsedLabel: `0:0${Math.round(b.cursor() / 1000)}`,
    gradeSummaryLabel: 'Honest gap — silence verified across consulted factors.',
  })
  b.advance(50)
  b.turnClose()

  return { id: 'honest_gap', label: 'Honest gap', userText, events: b.build() }
}
