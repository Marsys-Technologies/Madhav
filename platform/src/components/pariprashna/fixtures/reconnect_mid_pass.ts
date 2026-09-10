import { FixtureBuilder } from './builder'
import type { Fixture } from './types'

/**
 * J6 — reconnect after a network drop, mid pass-transition. Injects
 * `reconnecting` right as pass 2 begins, then `reconnected` ~1.3s later —
 * the committed prose from pass 1 must not move, gray out, or shake; only
 * the band and the caret (hollow while reconnecting) may change.
 */
export function buildReconnectMidPassFixture(turnId = 't-reconnect'): Fixture {
  const userText = 'Is a career change on the cards over the next two years?'
  const b = new FixtureBuilder(turnId)

  b.turnOpen(userText)
  b.phase('Reading the question')
  b.activity({ id: 'r1', passIndex: 0, label: 'Reading the question', detail: 'career · timing', kind: 'reasoning', durationMs: 500, ms: '0.5s' })
  b.activity({ id: 'r2', passIndex: 0, label: 'Retrieved — timing cycles', detail: '536 periods', kind: 'tool', durationMs: 400, ms: '0.4s' })

  b.citation(
    { n: 1, title: "Saturn's daśā, third pāda", sourceClass: 'computed_window', relevance: 'Active through 2027.', ref: 'ka_dasha_periods · MD 2022-11 → 2041-11', grade: 'confirmed' },
    b.cursor(),
  )

  b.advance(200)
  b.streamedBlock({ blockId: 'rb1', role: 'verdict', text: 'Yes — a genuine occupational shift is indicated, self-initiated.⟦1⟧' })

  b.advance(300)
  b.seamOpen(1, 'Looking further — the divisional charts…', 'rseam1')
  b.reconnecting()
  b.advance(1300)
  b.reconnected()
  b.activity({ id: 'r3', passIndex: 1, label: 'Retrieved — the career chart (daśāṁśa)', detail: 'D-10 · 14 facts', kind: 'tool', durationMs: 600, ms: '0.6s' })
  b.seamSettle('rseam1', 'LOOKED FURTHER · 1 RETRIEVAL · 0.6s (resumed)')

  b.citation(
    { n: 2, title: 'Daśāṁśa lord strengthened at the window', sourceClass: 'chart_factor', relevance: 'Divisional chart, verified.', ref: 'ga_divisionals · D-10 lagneśa dignity', grade: 'confirmed' },
    b.cursor(),
  )

  b.advance(200)
  b.streamedBlock({
    blockId: 'rb2',
    role: 'elaboration',
    text: 'The deeper look sharpens the picture — nothing above has moved; the connection dropped and resumed without loss.⟦2⟧',
  })

  b.advance(200)
  b.turnCommit({
    factorCount: 2,
    classicalCount: 0,
    elapsedLabel: `0:0${Math.round(b.cursor() / 1000)}`,
    gradeSummaryLabel: 'Core claim: WELL-GROUNDED',
    source: 'client_estimate',
  })
  b.advance(50)
  b.turnClose()

  return { id: 'reconnect_mid_pass', label: 'Reconnect mid-pass', userText, events: b.build() }
}
