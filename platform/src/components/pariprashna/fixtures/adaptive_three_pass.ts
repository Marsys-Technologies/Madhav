import { FixtureBuilder } from './builder'
import type { Fixture } from './types'

/**
 * The signature adaptive multi-pass demo turn: reads, answers, goes back
 * for more twice. Ported from the approved mockup's `PASSES` script
 * (`00_ARCHITECTURE/pariprashna_mockups/pariprashna_core_conversation.html`)
 * so the renderer is proven against the exact choreography the native
 * approved: one working band whose ledger groups rows under PASS 1/2/3, a
 * pass seam between prose segments that settles into a hairline divider,
 * and grounding that accrues in the (now-docked) right panel across passes.
 */
export function buildAdaptiveThreePassFixture(turnId = 't-adaptive'): Fixture {
  const userText = 'Is a career change on the cards over the next two years?'
  const b = new FixtureBuilder(turnId)

  b.turnOpen(userText)
  b.phase('Reading the question')

  // ── Pass 1 ──────────────────────────────────────────────────────────
  b.activity({ id: 'a1', passIndex: 0, label: 'Reading the question', detail: 'career · timing · 24 months', kind: 'reasoning', durationMs: 600, ms: '0.6s' })
  b.activity({ id: 'a2', passIndex: 0, label: 'Reading the whole chart', detail: 'six domains, cross-linked', kind: 'reasoning', durationMs: 900, ms: '2.8s' })
  b.activity({ id: 't1', passIndex: 0, label: 'Retrieved — timing cycles', detail: '536 periods', kind: 'tool', durationMs: 360, ms: '0.6s' })
  b.activity({ id: 't2', passIndex: 0, label: 'Retrieved — house lords & career factors', detail: '23 facts', kind: 'tool', durationMs: 360, ms: '0.4s' })
  b.activity({ id: 'a3', passIndex: 0, label: 'Composing the reading', detail: 'first view', kind: 'reasoning', durationMs: 500, ms: '1.2s' })

  b.citation(
    { n: 1, title: "Saturn–Moon angle in the tenth", sourceClass: 'chart_factor', relevance: 'Whole-chart synthesis, verified.', ref: 'SIG.MSR.413 · verified', grade: 'confirmed' },
    b.cursor(),
  )
  b.citation(
    { n: 2, title: 'Śani daśā running since Nov 2022', sourceClass: 'computed_window', relevance: 'Vimśottarī cycle.', ref: 'ka_dasha_periods · MD 2022-11 → 2041-11', grade: 'confirmed' },
    b.cursor(),
  )

  b.streamedBlock({
    blockId: 'b1',
    role: 'verdict',
    text: 'Yes — the two years ahead carry a genuine occupational shift, and it is initiated by you rather than forced from outside.⟦1⟧',
  })
  b.advance(240)
  b.streamedBlock({
    blockId: 'b2',
    role: 'elaboration',
    text:
      "Saturn's period — Śani daśā (the disciplinarian's cycle) — has run since late 2022 and has been the engine behind the pressure you have felt.⟦2⟧ Saturn rewards the long, deliberate move, not the sudden leap.",
  })
  b.advance(400)

  // ── Pass 2 — "looking further" ───────────────────────────────────────
  b.seamOpen(1, 'Looking further — the divisional charts…', 'seam1')
  b.activity({ id: 't3', passIndex: 1, label: 'Retrieved — the career chart (daśāṁśa)', detail: 'D-10 · 14 facts', kind: 'tool', durationMs: 700, ms: '0.7s' })
  b.activity({ id: 't4', passIndex: 1, label: 'Retrieved — yoga combinations, cross-checked', detail: '12 firings', kind: 'tool', durationMs: 700, ms: '0.7s' })
  b.activity({ id: 'a4', passIndex: 1, label: 'Weighing what the deeper look adds', detail: 'convergence check', kind: 'reasoning', durationMs: 400, ms: '0.4s' })
  b.seamSettle('seam1', 'LOOKED FURTHER · 2 RETRIEVALS · 1.8s')

  b.citation(
    { n: 3, title: 'Daśāṁśa lord strengthened at the window', sourceClass: 'chart_factor', relevance: 'Divisional chart, verified.', ref: 'ga_divisionals · D-10 lagneśa dignity', grade: 'confirmed' },
    b.cursor(),
  )
  b.citation(
    { n: 4, title: 'Rāja-yoga activation in window', sourceClass: 'chart_factor', relevance: 'Awaiting cross-verification.', ref: 'ganita_yoga_firings · requires_pass', grade: 'catalog' },
    b.cursor(),
  )

  b.advance(250)
  b.streamedBlock({
    blockId: 'b3',
    role: 'elaboration',
    text:
      'The deeper look sharpens the picture. Your daśāṁśa (the career chart) carries the same signature — its lord gains strength precisely where the birth chart promised it⟦3⟧ — and a Rāja-yoga (a combination for rise in station) stands ready to activate in the same window.⟦4⟧',
  })
  b.advance(400)

  // ── Pass 3 — "cross-checking" ────────────────────────────────────────
  b.seamOpen(2, 'Cross-checking before concluding…', 'seam2')
  b.activity({ id: 't5', passIndex: 2, label: 'Retrieved — transit windows', detail: '14 windows', kind: 'tool', durationMs: 500, ms: '0.5s' })
  b.activity({ id: 'a5', passIndex: 2, label: 'Consulting the classics', detail: 'BPHS · Phaladīpikā', kind: 'reasoning', durationMs: 900, ms: '0.9s' })
  b.activity({ id: 'a6', passIndex: 2, label: 'Verifying every claim', detail: 'grounding gate · 6/6', kind: 'reasoning', durationMs: 800, ms: '0.8s' })
  b.seamSettle('seam2', 'CROSS-CHECKED · TIMING CONFIRMED · 1.1s')

  b.citation(
    { n: 5, title: 'Tenth-lord sub-period opens mid-2027', sourceClass: 'computed_window', relevance: 'Daśā timing.', ref: 'ka_windows · AD 10L 2027-05 → 2028-01', grade: 'confirmed' },
    b.cursor(),
  )
  b.citation(
    { n: 6, title: 'Jupiter transits the career house · 2027', sourceClass: 'classical_source', relevance: 'Transit anchor.', ref: 'ga_transit_anchors · BPHS 34.12', grade: 'confirmed' },
    b.cursor(),
  )

  b.advance(250)
  b.streamedBlock({
    blockId: 'b4',
    role: 'elaboration',
    text:
      'Timing, then. Three independent indications converge on the middle of 2027⟦5⟧ — the tenth-lord’s sub-period opening, Jupiter’s transit to your career house, and the yoga above. Read it not as an escape but as an arrival: the chart favours a change that consolidates what you have built.⟦6⟧',
  })

  b.advance(200)
  b.commitOnlyBlock({
    blockId: 'b-pred',
    kind: 'prediction_card',
    prediction: {
      id: 'pred-1',
      claim: 'An occupational shift, self-initiated, most likely around mid-2027.',
      // PB-6 (SAMĀPTI): real ISO kāla-rekhā anchors — the geometry is computed
      // live from these (computeKalaRekha), never a pre-baked fraction. The
      // "today" dot is NOT fixed here; it is read from the real clock at
      // render time, so this fixture still shows real, live-advancing
      // geometry rather than a frozen demo position.
      readingDate: '2026-06-01',
      windowStart: '2027-01-01',
      windowEnd: '2027-12-31',
      windowStartLabel: '2026',
      windowEndLabel: '2028',
      confidencePhrase: 'more likely than not',
      ref: 'PRED.CAREER.2027-06',
      lifecycle: 'window_open',
    },
  })

  b.advance(150)
  b.turnCommit({
    factorCount: 6,
    classicalCount: 2,
    elapsedLabel: `0:${String(Math.round(b.cursor() / 1000)).padStart(2, '0')}`,
    compositionNote: undefined,
    gradeSummaryLabel: 'Core claim: WELL-GROUNDED',
  })
  b.advance(50)
  b.turnClose()

  return { id: 'adaptive_three_pass', label: 'Adaptive · 3 passes', userText, events: b.build() }
}
