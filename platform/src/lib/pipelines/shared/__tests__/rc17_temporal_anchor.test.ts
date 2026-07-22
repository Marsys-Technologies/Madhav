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
    expect(systemContent).toContain('TEMPORAL ANCHOR')
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
