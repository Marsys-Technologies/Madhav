import { FixtureBuilder } from './builder'
import type { Fixture } from './types'

/**
 * A shallow, single-pass turn (no seams) — the honest-when-appropriate
 * counterpart to the adaptive fixture (P5: a smaller grounding count is
 * legitimate when the question is narrow; it must still be visible, never
 * hidden). Used to exercise the "one working band, one prose run, no seam"
 * path and to prove seam absence doesn't regress the settle choreography.
 */
export function buildSinglePassFixture(turnId = 't-single'): Fixture {
  const userText = 'And within that, when specifically should I not initiate anything new?'
  const b = new FixtureBuilder(turnId)

  b.turnOpen(userText)
  b.phase('Reading the question')
  b.activity({ id: 's1', passIndex: 0, label: 'Reading the question', detail: 'timing · narrow window', kind: 'reasoning', durationMs: 500, ms: '0.5s' })
  b.activity({ id: 's2', passIndex: 0, label: 'Retrieved — transit windows', detail: '6 windows', kind: 'tool', durationMs: 500, ms: '0.5s' })
  b.activity({ id: 's3', passIndex: 0, label: 'Composing the reading', detail: 'narrow scope', kind: 'reasoning', durationMs: 600, ms: '0.6s' })

  b.citation(
    { n: 1, title: 'Retrograde Mars over the tenth', sourceClass: 'computed_window', relevance: 'Transit anchor.', ref: 'ga_transit_anchors · Mars(R) → H10 2027-01', grade: 'confirmed' },
    b.cursor(),
  )

  b.advance(200)
  b.streamedBlock({
    blockId: 'sb1',
    role: 'verdict',
    text: 'One narrow window asks caution: avoid initiating new commitments in January 2027, while Mars sits retrograde over the tenth house.⟦1⟧',
  })
  b.advance(200)
  b.streamedBlock({
    blockId: 'sb2',
    role: 'caveat',
    text: 'Outside that month, the period otherwise stated stands — this is a pause within it, not a reversal of it.',
  })

  b.advance(200)
  b.turnCommit({
    factorCount: 1,
    classicalCount: 0,
    elapsedLabel: `0:0${Math.round(b.cursor() / 1000)}`,
    gradeSummaryLabel: 'Core claim: WELL-GROUNDED',
    source: 'client_estimate',
  })
  b.advance(50)
  b.turnClose()

  return { id: 'single_pass', label: 'Single pass', userText, events: b.build() }
}
