/**
 * RC-17 — web-door dasha-anchoring hallucination regression test.
 *
 * Live-reproduced 2026-07-22 (RC-02_TWO_DOOR_PARITY_v1_0.md §5a, chart 1c826d5a):
 * `/api/chat/consult`'s synthesis text stated "Mercury MD / Saturn AD" while its own
 * `data-orientation` block (and the MCP `prashna_ask` door, for the same chart) both
 * correctly said "Saturn MD / Rahu AD". Root cause: `run_adapter_dispatch.ts`'s
 * `systemContent` assembly never included the resolved `current_maha_antar` or
 * today's date at all — the synthesis model was handed a raw table of dasha periods
 * (via the B.11 dasha-context floor tool) with no anchor telling it which one is
 * CURRENT, so it fell back to training-data recency. Same defect class fixed for the
 * MCP `prashna_ask` synthesis path in commit 2df42b61 (W6.3 fix-cycle,
 * `prashna_ask_synthesis.ts`'s `formatTemporalAnchor`) — this is the equivalent fix
 * for the web path, `formatConsultTemporalAnchor`.
 *
 * fix-cycle 2 (2026-07-23): fix-cycle 1's anchor wording ("treat this as the CURRENT
 * period") reached `main` and deployed, but the defect RESURFACED in production in a
 * new, worse form — live-reproduced three independent times against the deployed
 * `amjis-web` `/api/chat/consult` route (chart 1c826d5a) THIS session, before any
 * fix-cycle-2 code was written:
 *   (a) synthesis opened "**TEMPORAL ANCHOR:** As instructed, this analysis is based
 *       on your current period being Saturn Mahadasha (MD) / Rahu Antardasha (AD)..."
 *       — the model treated the anchor as a user INSTRUCTION it was reluctantly
 *       complying with (and echoed the internal "TEMPORAL ANCHOR:" section header
 *       back into user-facing text), rather than absorbing it as fact;
 *   (b) a separate run fabricated "Mercury Mahadasha / Saturn Antardasha" as the
 *       "CURRENT PERIOD" outright — the correct "Saturn MD / Rahu AD" never once
 *       appeared in the visible synthesis text, only in the client-only
 *       data-orientation JSON alongside it.
 * Root cause: "treat this as X" is a conditional/imperative frame that invites an
 * "as instructed"/hedge/second-guess completion — the model was never told the fact
 * simply IS true. `formatConsultTemporalAnchor` and `buildConsultSystemContent` were
 * rewritten to (1) state the fact as unconditional declarative ground truth sourced
 * from the deterministic chart-facts database, (2) explicitly forbid the exact hedge
 * phrasings observed live ("as instructed", "as per your request", etc.), (3)
 * explicitly forbid naming any OTHER Mahadasha/Antardasha combination as the
 * "actual"/"real"/"true" current period, and (4) rename the internal section label
 * away from "TEMPORAL ANCHOR:" (which the model echoed) to a label that explicitly
 * instructs the model not to cite it. The tests below cover both fix-cycle 1's
 * original defect AND fix-cycle 2's regression pattern.
 */

import { describe, it, expect } from 'vitest'
import { formatConsultTemporalAnchor, buildConsultSystemContent } from '../run_adapter_dispatch'

describe('formatConsultTemporalAnchor — RC-17', () => {
  it('tells the model today\'s date and the current maha/antar dasha explicitly', () => {
    const anchor = formatConsultTemporalAnchor('2026-07-22', 'Saturn MD / Rahu AD')
    expect(anchor).toContain('2026-07-22')
    expect(anchor).toContain('Saturn MD / Rahu AD')
    expect(anchor).toMatch(/CURRENT period, not upcoming or past/i)
  })

  it('degrades honestly instead of fabricating a period when current_maha_antar is unresolved', () => {
    const anchor = formatConsultTemporalAnchor('2026-07-22', null)
    expect(anchor).toContain('could not be resolved')
    expect(anchor).not.toMatch(/MD \/ .* AD/)
  })

  it('never asserts a dasha lord/period other than the one it was given (no silent substitution)', () => {
    // Regression guard for the exact live symptom: the model substituted a DIFFERENT
    // chart's/period's dasha lord ("Mercury MD / Saturn AD") for the correct resolved
    // one ("Saturn MD / Rahu AD"). The anchor line must be unambiguous and must not
    // contain any other MD/AD combination alongside the correct one.
    const anchor = formatConsultTemporalAnchor('2026-07-22', 'Saturn MD / Rahu AD')
    expect(anchor).toContain('Saturn MD / Rahu AD')
    expect(anchor).not.toContain('Mercury MD')
  })

  it('instructs the model to reason about "current"/"now"/"upcoming"/"past" relative to the given date only', () => {
    const anchor = formatConsultTemporalAnchor('2026-07-22', 'Saturn MD / Rahu AD')
    expect(anchor).toMatch(/relative to THIS date and period only/i)
    expect(anchor).toMatch(/do not rely on any other date/i)
  })

  it('is pure — identical inputs produce identical output (no hidden Date.now() dependency)', () => {
    const a = formatConsultTemporalAnchor('2026-07-22', 'Saturn MD / Rahu AD')
    const b = formatConsultTemporalAnchor('2026-07-22', 'Saturn MD / Rahu AD')
    expect(a).toBe(b)
  })
})

describe('buildConsultSystemContent — RC-17 wiring (proves the anchor reaches the synthesis prompt)', () => {
  it('includes the temporal anchor alongside the B.11 floor bundle content', () => {
    const systemContent = buildConsultSystemContent({
      bundleSystemContent: 'MSR SIGNAL: Saturn strong in 10th house.',
      synthesisGuidance: null,
      dataReadinessNote: undefined,
      nowContextDate: '2026-07-22',
      currentMahaAntar: 'Saturn MD / Rahu AD',
    })
    expect(systemContent).toBeDefined()
    // fix-cycle 2: label renamed from "TEMPORAL ANCHOR:" (echoed verbatim by the
    // model in the live regression) to a label that instructs against citing it.
    expect(systemContent).toContain('VERIFIED CHART FACT')
    expect(systemContent).toContain('Saturn MD / Rahu AD')
    expect(systemContent).toContain('MSR SIGNAL: Saturn strong in 10th house.')
  })

  it('the temporal anchor is present even when the bundle/guidance/readiness-note are all empty (never silently omitted)', () => {
    const systemContent = buildConsultSystemContent({
      bundleSystemContent: '',
      synthesisGuidance: null,
      dataReadinessNote: undefined,
      nowContextDate: '2026-07-22',
      currentMahaAntar: 'Saturn MD / Rahu AD',
    })
    // Prior behavior: an all-empty systemContent collapsed to `undefined` (no system
    // prompt at all). The temporal anchor must survive that collapse — it is never
    // conditional on other system-content sections being present.
    expect(systemContent).toBeDefined()
    expect(systemContent).toContain('Saturn MD / Rahu AD')
  })

  it('never fabricates a different dasha lord than the one resolved (regression guard for the live symptom)', () => {
    const systemContent = buildConsultSystemContent({
      bundleSystemContent: 'raw dasha period rows: Mercury AD 2010-2013, Saturn MD 2010-2029, Rahu AD 2023-2026...',
      synthesisGuidance: null,
      dataReadinessNote: undefined,
      nowContextDate: '2026-07-22',
      currentMahaAntar: 'Saturn MD / Rahu AD',
    })
    // The bundle (raw tool results) may legitimately mention "Mercury AD" as one row
    // among many historical periods — but the ANCHOR line itself must unambiguously
    // name the correct current period, giving the model the disambiguating signal
    // that was missing in the live-reproduced defect.
    expect(systemContent).toMatch(/current Vimshottari dasha period, as of this date, is Saturn MD \/ Rahu AD/)
  })
})

describe('formatConsultTemporalAnchor — RC-17 fix-cycle 2 (production regression, "as instructed" hedge + wrong-"actual"-period second-guess)', () => {
  // Live production evidence (this session, chart 1c826d5a, deployed amjis-web,
  // AFTER fix-cycle 1 had already merged and deployed):
  //   (a) "As instructed, this analysis is based on your current period being
  //        Saturn Mahadasha (MD) / Rahu Antardasha (AD)..."
  //   (b) "Confidence Note: This analysis is based on the explicit instruction to
  //        treat Saturn MD / Rahu AD as your current dasha. Your chart's actual
  //        current period is Mercury MD / Saturn AD..."
  // Both hedge shapes stem from the anchor being framed as something the model was
  // "asked"/"instructed" to accept rather than as fact. The anchor text itself is the
  // only lever this module controls — these tests assert the wording no longer gives
  // the model instruction-shaped language to hedge against, and explicitly forbids the
  // specific hedge/substitution phrasings observed live.

  it('never frames the anchor as something the model was instructed/asked/requested to accept', () => {
    const anchor = formatConsultTemporalAnchor('2026-07-23', 'Saturn MD / Rahu AD')
    // The old wording ("treat this as the CURRENT period") is an imperative "pretend
    // X" frame — this is exactly what invited the live "As instructed..." hedge.
    expect(anchor).not.toMatch(/treat this as/i)
    // Explicit prohibition against the exact hedge phrasings seen live.
    expect(anchor).toMatch(/not.*(a user instruction|an instruction)/i)
    expect(anchor).toMatch(/as instructed/i) // present only inside the prohibition sentence
    expect(anchor).toMatch(/as per your request/i)
  })

  it('explicitly forbids naming any other Mahadasha/Antardasha combination as the "actual"/"real"/"true" current period', () => {
    // Regression guard for the live "Confidence Note: ... Your chart's actual current
    // period is Mercury MD / Saturn AD" symptom — a hallucinated correction that
    // substituted a DIFFERENT chart's dasha for the correctly-resolved one.
    const anchor = formatConsultTemporalAnchor('2026-07-23', 'Saturn MD / Rahu AD')
    expect(anchor).toMatch(/"actual"/i)
    expect(anchor).toMatch(/never (name|preface|qualify)/i)
    expect(anchor).toMatch(/exactly one current Mahadasha\/Antardasha combination/i)
  })

  it('instructs the model to state the fact as a plain, unconditional fact rather than a complied-with directive', () => {
    const anchor = formatConsultTemporalAnchor('2026-07-23', 'Saturn MD / Rahu AD')
    expect(anchor).toMatch(/verified fact/i)
    expect(anchor).toMatch(/deterministic chart-facts database/i)
    expect(anchor).toMatch(/not a request you are complying with/i)
  })

  it('instructs the model never to cite or quote the internal grounding label/section in its response', () => {
    const anchor = formatConsultTemporalAnchor('2026-07-23', 'Saturn MD / Rahu AD')
    // Regression guard for the live symptom where the model echoed the literal
    // "TEMPORAL ANCHOR:" section header back into user-facing text.
    expect(anchor).toMatch(/do not quote, mention, or refer to this paragraph/i)
  })

  it('the assembled systemContent label is not the old "TEMPORAL ANCHOR:" string the model echoed live', () => {
    const systemContent = buildConsultSystemContent({
      bundleSystemContent: 'MSR SIGNAL: Saturn strong in 10th house.',
      synthesisGuidance: null,
      dataReadinessNote: undefined,
      nowContextDate: '2026-07-23',
      currentMahaAntar: 'Saturn MD / Rahu AD',
    })
    expect(systemContent).toBeDefined()
    expect(systemContent).not.toContain('TEMPORAL ANCHOR:')
  })
})

// ---------------------------------------------------------------------------
// Output-side guard: a small helper + tests asserting that IF a hedge phrase
// like the ones observed live were to appear in a synthesis response, a
// caller could detect it. This does not replace the prompt-level fix above
// (the model cannot be perfectly constrained by a system prompt alone) but
// gives the pipeline a mechanical tripwire for the exact failure mode this
// fix-cycle targets, independent of prompt wording.
// ---------------------------------------------------------------------------

/**
 * Detects the RC-17 fix-cycle-2 hedge pattern in a synthesis response: either
 * (a) framing the temporal anchor as an instruction the model complied with
 * ("as instructed", "as per your request", "per your instruction", ...), or
 * (b) naming a second, different dasha combination as the "actual"/"real"/
 * "true" current period (the wrong-"actual"-period second-guess). Exported
 * only for this test file's use — not part of the module's public surface
 * consumed elsewhere; a lightweight local detector, not a production gate.
 */
function containsRc17HedgePattern(text: string): boolean {
  const instructionHedge = /\b(as instructed|as per your (request|instruction)|as requested|per (the|your) instruction)\b/i
  const actualPeriodHedge = /\b(actual|real|true)\b[^.]{0,40}\bcurrent\b[^.]{0,20}\b(period|dasha|mahadasha|antardasha)\b/i
  return instructionHedge.test(text) || actualPeriodHedge.test(text)
}

describe('containsRc17HedgePattern — local detector for the live symptom text', () => {
  it('flags the live "as instructed" hedge', () => {
    expect(containsRc17HedgePattern(
      '**TEMPORAL ANCHOR:** As instructed, this analysis is based on your current period being Saturn Mahadasha (MD) / Rahu Antardasha (AD)...',
    )).toBe(true)
  })

  it('flags the live "actual current period" second-guess', () => {
    expect(containsRc17HedgePattern(
      'Confidence Note: This analysis is based on the explicit instruction to treat Saturn MD / Rahu AD as your current dasha. Your chart\'s actual current period is Mercury MD / Saturn AD.',
    )).toBe(true)
  })

  it('does not flag a clean, unhedged answer', () => {
    expect(containsRc17HedgePattern(
      'Your current dasha period is Saturn Mahadasha / Rahu Antardasha. This period favors career consolidation...',
    )).toBe(false)
  })
})
